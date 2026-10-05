#!/usr/bin/env python3
"""Boot a real Forge server with the mod and exercise its content, then fail on any error in the log.

Used by CI (.github/workflows/build.yml) after `./gradlew build`:
    python3 tools/ci_smoke.py <server_dir>                    # flat world: every structure, mob, item, loot table
    python3 tools/ci_smoke.py <server_dir> --fit              # normal world: how every structure sits on the terrain
    python3 tools/ci_smoke.py <server_dir> --fit --shard 0/2  # ...every second structure from the first
    python3 tools/ci_smoke.py <server_dir> --world            # Wayfarers biomes + generation speed gate

The server directory must already contain an installed Forge server and the mod jar in mods/.
The script accepts the EULA, starts the server, waits for "Done", then from the console:
  * places every structure (in its own dimension), then our village and outpost pieces and vanilla villages and
    outposts that use them (after checking the vanilla jigsaw names they rely on in the server jar),
  * summons every entity and every item,
  * measures the server's time per tick with a crowded base of machines and automatons (fails above 25 ms),
  * breaks mod blocks (loot tables + Forge loot modifiers),
  * spawns every loot table,
  * reloads data packs,
and stops the server. Any ERROR line, exception, crash report or failed command fails the run.
With --fit the server makes a fresh world with Minecraft's own terrain instead (and the Wayfarers biomes, on by
default) and /wayfarers fitcheck locates, generates and measures every Overworld structure there.

With --world the server runs twice on the same seed, each time in a fresh normal world: once WITH the Wayfarers biomes
and terrain touches (config world.customBiomes and world.terrain.* on), once WITHOUT (all off: Minecraft's own
generation). Each run generates the same fresh areas for real (/wayfarers genbench area: a warm-up area first, then
a fixed 12 x 12 chunk area at 20000 20000 and a 6 x 6 chunk area on each Wayfarers biome) and the summary gives the
full-generation ms/chunk of both and their ratio. The job fails when WITH is more than 5 % slower than WITHOUT
(GATE); a pair over the gate is measured once more, in the other order, on fresh worlds, and the verdict uses both
pairs together. The WITH run also checks that the pack is on, finds each biome with /locate biome and draws it
(/wayfarers biomeshots: wayfarers-biome-<id>.png, published with the previews).

Every run writes a short diagnostic summary, wayfarers-ci-<job>.txt, into the server folder: phase durations, FAIL
lines, suspicious log lines, slow commands. CI publishes it with the previews, so the next diagnosis needs no log
download.

Time: the server runs one command at a time, so a command the script stopped waiting for still blocks the ones after
it. /wayfarers fitcheck keeps to its own budget (in the Java command) and the script waits that budget plus a margin;
anything skipped for time is listed in the summary, never counted as a pass.
"""
import glob
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
DATA = os.path.join(RES, "data", "wayfarers")

NETHER = {"nether_wastes", "soul_sand_valley", "crimson_forest", "warped_forest", "basalt_deltas"}
END = {"the_end", "end_highlands", "end_midlands", "small_end_islands", "end_barrens"}

# Log lines that are expected on a headless CI server and say nothing about the mod.
BENIGN = [
    re.compile(p) for p in (
        r"Failed to (load|fetch) .*(profile|session|skin|realms)",
        r"Ambiguity between arguments",
        r"Can't keep up!",
        r"kqueue|OSX/BSD|Appender DebugFile",  # netty probing a macOS-only transport on the Linux runner
        # vanilla's own deep dark sculk patch spreads 2 chunks out; 26.2's unsafe-read detector flags it (not our feature)
        r"unsafe terrain read.*minecraft:sculk_patch_deep_dark",
    )
]
BAD = [re.compile(p) for p in (
    r"/ERROR\]",
    r"/FATAL\]",
    r"Exception",
    r"Missing metadata",
    r"Couldn't (load|parse|read)",
    r"Failed to (load|parse|place|decode|read)",
    r"Unknown (registry|structure|item|entity|block)",
    r"Errors in currently selected datapacks",
)]

FEEDBACK_TIMEOUT = 180
BUDGET = 36 * 60  # seconds per test; past it the remaining phases are skipped and the run fails with a clear message
# Java-side budget (keep in step): FitCheckCommand.BUDGET_MS 22 min (+ LOCATE_BUDGET_MS 5 min for the structure in
# progress). The script waits the budget plus a margin for the item in progress, so the server answers first.
FIT_BUDGET = 22 * 60
FIT_WAIT = FIT_BUDGET + 5 * 60 + 180
# --world: the generation speed gate (WITH / WITHOUT full-generation ms per chunk) and its areas
GATE = 1.05
BENCH_X, BENCH_Z, BENCH_SIZE = 20000, 20000, 12
WARMUP_X, WARMUP_Z, WARMUP_SIZE = -20000, 20000, 8
BIOME_BENCH_SIZE = 6
GENBENCH_WAIT = 900
BIOMESHOTS_WAIT = 6 * 60 + 300  # BiomeShotsCommand.BUDGET_MS plus a margin
OUR_BIOMES = sorted(os.path.splitext(n)[0] for n in os.listdir(os.path.join(DATA, "worldgen", "biome"))) \
    if os.path.isdir(os.path.join(DATA, "worldgen", "biome")) else []
TERRAIN_TOGGLES = ["boulders", "fallenLogs", "rockSpires", "wildflowers", "mossCarpets", "hotSprings"]


class Summary:
    """What wayfarers-ci-<job>.txt says (see the module docstring)."""
    job = "smoke"
    phases = []      # (name, seconds, note)
    notes = []       # skips, partial results, anything a reader must know
    slow = []        # "[smoke] slow: ..." lines
    perf = []        # the server performance check (see server_performance)

    @classmethod
    def write(cls, server_dir, failures, bad, extra=()):
        lines = [f"wayfarers CI summary: job {cls.job}, commit {os.environ.get('GITHUB_SHA', '?')[:12]}, "
                 f"run {os.environ.get('GITHUB_RUN_ID', '?')} attempt {os.environ.get('GITHUB_RUN_ATTEMPT', '?')}",
                 f"result: {'FAILED' if failures else 'OK'}", "", "phases (seconds):"]
        lines += [f"  {name:34s} {sec:6.0f}  {note}".rstrip() for name, sec, note in cls.phases]
        if cls.perf:
            lines += ["", "server performance (MSPT = mean milliseconds per server tick):"] + ["  " + p for p in cls.perf]
        lines += list(extra)
        if cls.notes:
            lines += ["", "notes (skipped or partial items, never counted as passed):"] + ["  " + n for n in cls.notes]
        if cls.slow:
            lines += ["", "slow commands:"] + ["  " + n for n in cls.slow[:40]]
        lines += ["", f"FAIL lines ({len(failures)}):"] + ["  FAIL: " + f for f in failures]
        lines += ["", f"suspicious log lines ({len(set(bad))}):"] + ["  " + b[:400] for b in sorted(set(bad))[:40]]
        path = os.path.join(server_dir, f"wayfarers-ci-{cls.job}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[smoke] summary written to {path}", flush=True)


def structure_dims():
    tags = os.path.join(DATA, "tags", "worldgen", "biome", "has_structure")
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA, "worldgen", "structure", "*.json"))):
        sid = os.path.splitext(os.path.basename(path))[0]
        dim = "minecraft:overworld"
        tag = os.path.join(tags, sid + ".json")
        if os.path.exists(tag):
            names = {v["id"].split(":")[-1] if isinstance(v, dict) else v.split(":")[-1]
                     for v in json.load(open(tag))["values"]}
            if names & NETHER:
                dim = "minecraft:the_nether"
            elif names & END:
                dim = "minecraft:the_end"
        out[sid] = dim
    return out


def lang_ids(prefix):
    lang = json.load(open(os.path.join(RES, "assets", "wayfarers", "lang", "en_us.json")))
    return sorted({k[len(prefix):] for k in lang if k.startswith(prefix) and "." not in k[len(prefix):]})


def loot_tables():
    root = os.path.join(DATA, "loot_table")
    return sorted(os.path.relpath(p, root)[:-5].replace(os.sep, "/")
                  for p in glob.glob(os.path.join(root, "**", "*.json"), recursive=True))


class Server:
    def __init__(self, cwd, cmd, log_name="smoke-console.log"):
        self.cwd = cwd
        self.lines = []
        self.q = queue.Queue()
        self.log = open(os.path.join(cwd, log_name), "w", encoding="utf-8")
        self.proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8",
                                     errors="replace")
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            self.log.write(line + "\n")
            self.log.flush()
            print(line, flush=True)
            self.q.put(line)
        self.q.put(None)

    def wait_for(self, pattern, timeout):
        rx = re.compile(pattern)
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=1)
            except queue.Empty:
                continue
            if line is None:
                return None
            if rx.search(line):
                return line
        return None

    def run(self, command, expect=None, timeout=FEEDBACK_TIMEOUT):
        while not self.q.empty():
            self.q.get_nowait()
        print(f">>> {command}", flush=True)
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()
        if expect:
            t = time.time()
            res = self.wait_for(expect, timeout)
            if time.time() - t > 15:
                msg = f"{command} took {time.time() - t:.0f}s -> {res}"
                print(f"[smoke] slow: {msg}", flush=True)
                Summary.slow.append(msg[:300])
            return res
        time.sleep(0.2)
        return None


def server_command(server_dir):
    if os.path.exists(os.path.join(server_dir, "run.sh")):
        return ["bash", "run.sh", "nogui"]
    jars = [j for j in glob.glob(os.path.join(server_dir, "*.jar")) if "installer" not in j]
    if not jars:
        sys.exit("no server jar or run.sh in " + server_dir)
    return ["java", "-Xmx4G", "-jar", os.path.basename(jars[0]), "nogui"]


def prepare(server_dir, fit, level_name=None, custom=True):
    with open(os.path.join(server_dir, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    props = ("online-mode=false\nspawn-protection=0\nlevel-seed=wayfarers-ci\nmax-tick-time=-1\n"
             "view-distance=4\nsimulation-distance=4\nsync-chunk-writes=false\n")
    # the Wayfarers biomes and terrain touches: on (the defaults) unless this run measures vanilla generation
    os.makedirs(os.path.join(server_dir, "config"), exist_ok=True)
    flag = "true" if custom else "false"
    with open(os.path.join(server_dir, "config", "wayfarers-common.toml"), "w") as f:
        f.write(f"[world]\ncustomBiomes = {flag}\n\n[world.terrain]\n"
                + "".join(f"{t} = {flag}\n" for t in TERRAIN_TOGGLES))
    if level_name:
        # a fresh normal world (the --world speed runs)
        props += f"level-name={level_name}\n"
    elif fit:
        # a fresh Default world: the structures are measured on Minecraft's own terrain
        props += "level-name=world_fit\n"
    else:
        # a flat Overworld generates in a blink; /place structure ignores biomes, so every structure
        # still assembles (full noise terrain made the run take over an hour on CI runners)
        props += "level-name=world\nlevel-type=minecraft\\:flat\ngenerate-structures=false\n"
        props += ('generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},'
                  '{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],'
                  '"biome":"minecraft:plains"}\n')
    with open(os.path.join(server_dir, "server.properties"), "w") as f:
        f.write(props)
    jvm = os.path.join(server_dir, "user_jvm_args.txt")
    if os.path.exists(jvm) and "-Xmx4G" not in open(jvm).read():
        with open(jvm, "a") as f:
            f.write("\n-Xmx4G\n")


def check_budget(where):
    if time.time() - Phase.start > BUDGET:
        raise TimeoutError(f"time budget used up at {where}")


class Phase:
    """Prints how long each part of the test took (the CI log is the only window into a slow run)."""
    start = time.time()

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        if time.time() - Phase.start > BUDGET:
            raise TimeoutError(f"time budget used up before '{self.name}'")
        self.t = time.time()
        print(f"[smoke] {self.name}: start (t={time.time() - Phase.start:.0f}s)", flush=True)

    def __exit__(self, *exc):
        sec = time.time() - self.t
        print(f"[smoke] {self.name}: {sec:.0f}s", flush=True)
        Summary.phases.append((self.name, sec, "interrupted" if exc and exc[0] else ""))


def exercise_mod(srv, failures):
    with Phase("structures"):
        place_structures(srv, failures)
    with Phase("vanilla villages and outposts"):
        vanilla_villages(srv, failures)
    with Phase("entities and items"):
        summon_all(srv, failures)
    with Phase("creatures fighting"):
        creatures_fight(srv, failures)
    with Phase("server performance"):
        server_performance(srv, failures)
    with Phase("blocks and loot"):
        blocks_and_loot(srv, failures)
    with Phase("reload"):
        srv.run("reload", r"Reloading|Failed", 120)
        time.sleep(20)
    srv.run("say smoke test finished")
    time.sleep(2)


def place_structures(srv, failures):
    dims = structure_dims()
    for i, (sid, dim) in enumerate(dims.items()):
        check_budget(f"structure {sid}")
        x = 2000 + 500 * i
        r = 160  # the biggest wonders reach 120+ blocks from their origin
        # /forceload takes at most 256 chunks per call: load the square in 128-block tiles
        for x0 in range(x - r, x + r, 128):
            for z0 in range(-r, r, 128):
                res = srv.run(f"execute in {dim} run forceload add {x0} {z0} {min(x0 + 127, x + r)} {min(z0 + 127, r)}",
                              r"Marked|forceload|No chunks|too many|Too many", 60)
                if res and "oo many" in res:
                    failures.append(f"forceload for {sid}: {res}")
        res = None
        for attempt in range(12):
            res = srv.run(f"execute in {dim} run place structure wayfarers:{sid} {x} 100 0",
                          r"Generated structure|Failed to place|not loaded|commands\.place|Unknown|Invalid|Incorrect", 120)
            if not res or "not loaded" not in res:
                break
            time.sleep(5)
        if not res or "Generated structure" not in res:
            failures.append(f"place structure {sid} in {dim}: {res}")
        srv.run(f"execute in {dim} run forceload remove all", r"Unmarked|forceload|No chunks", 30)


VILLAGES = ["plains", "desert", "savanna", "snowy", "taiga"]


def our_templates(sub):
    """Template ids of ours under data/wayfarers/structure/<sub>."""
    root = os.path.join(DATA, "structure")
    return sorted("wayfarers:" + os.path.relpath(p, root)[:-4].replace(os.sep, "/")
                  for p in glob.glob(os.path.join(root, sub, "**", "*.nbt"), recursive=True))


def vanilla_villages(srv, failures):
    """Our village and outpost pieces (tools/wf/village.py): every template loads and places, then vanilla villages
    of the five types and pillager outposts assemble with our pieces in their pools (bad jigsaws or missing
    templates show up as log errors)."""
    x = -3000
    srv.run(f"execute in minecraft:overworld run forceload add {x} 0 {x + 399} 127",
            r"Marked|forceload|No chunks|too many|Too many", 120)
    for i, tid in enumerate(our_templates("village") + our_templates("pillager_outpost")):
        check_budget(f"template {tid}")
        res = srv.run(f"execute in minecraft:overworld run place template {tid} {x + (i % 20) * 20} 100 {(i // 20) * 32}",
                      r"Loaded template|Failed to place|no template|not loaded|Not all chunks|Unknown|Invalid|Incorrect", 60)
        if not res or "Loaded template" not in res:
            failures.append(f"place template {tid}: {res}")
    srv.run("execute in minecraft:overworld run forceload remove all", r"Unmarked|forceload|No chunks", 30)
    spots = [(vt, k) for vt in VILLAGES for k in range(3)] + [("outpost", k) for k in range(3)]
    for i, (vt, k) in enumerate(spots):
        check_budget(f"village {vt}")
        cx, cz = -6000 - 400 * i, 0
        r = 112
        res = srv.run(f"execute in minecraft:overworld run forceload add {cx - r} {cz - r} {cx + r - 1} {cz + r - 1}",
                      r"Marked|forceload|No chunks|too many|Too many", 120)
        sid = "minecraft:pillager_outpost" if vt == "outpost" else f"minecraft:village_{vt}"
        for attempt in range(12):
            res = srv.run(f"execute in minecraft:overworld run place structure {sid} {cx} 100 {cz}",
                          r"Generated structure|Failed to place|not loaded|commands\.place|Unknown|Invalid|Incorrect", 120)
            if not res or "not loaded" not in res:
                break
            time.sleep(5)
        if not res or "Generated structure" not in res:
            failures.append(f"place structure {sid}: {res}")
        srv.run("execute in minecraft:overworld run forceload remove all", r"Unmarked|forceload|No chunks", 30)


def _jigsaws(raw):
    """(name, target, pool) of every jigsaw in a template (old 1.14 data upgraded like JigsawPropertiesFix)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import nbt
    t = nbt.loads(raw)
    pal = t["palette"]
    out = []
    for b in t["blocks"]:
        if pal[b["state"]]["Name"] == "minecraft:jigsaw" and b.get("nbt"):
            d = b["nbt"]
            if "attachement_type" in d:
                name = target = d["attachement_type"]
                pool = d.get("target_pool", "minecraft:empty")
            else:
                name, target, pool = d.get("name"), d.get("target"), d.get("pool")
            out.append((name, target, pool))
    return out


def check_vanilla_jigsaws(server_dir, failures):
    """Our village pieces copy the vanilla jigsaw conventions (tools/wf/village.py): read the vanilla street and
    outpost templates from the server jar and check they still connect the way our pieces expect."""
    probe = "data/minecraft/structure/village/plains/streets/straight_01.nbt"
    jar = None
    for path in glob.glob(os.path.join(server_dir, "**", "*.jar"), recursive=True):
        try:
            with zipfile.ZipFile(path) as z:
                if probe in z.namelist():
                    jar = path
                    break
        except (zipfile.BadZipFile, OSError):
            continue
    if not jar:
        print("[smoke] vanilla jigsaw check skipped: no jar with the vanilla village templates", flush=True)
        return
    with zipfile.ZipFile(jar) as z:
        names = z.namelist()
        for vt in VILLAGES:
            js = []
            for n in names:
                if n.startswith(f"data/minecraft/structure/village/{vt}/streets/") and n.endswith(".nbt"):
                    js += _jigsaws(z.read(n))
            houses = {t for _, t, p in js if p == f"minecraft:village/{vt}/houses"}
            streets = {(nm, t) for nm, t, p in js if p == f"minecraft:village/{vt}/streets"}
            decor = {t for _, t, p in js if p == f"minecraft:village/{vt}/decor"}
            if "minecraft:building_entrance" not in houses:
                failures.append(f"vanilla {vt} streets reach houses through {houses}, our houses answer to "
                                f"minecraft:building_entrance")
            if not any(nm == "minecraft:street" for nm, _ in streets) or \
                    not any(t == "minecraft:street" for _, t in streets):
                failures.append(f"vanilla {vt} streets join through {streets}, our plaza and avenue use minecraft:street")
            if decor and "minecraft:bottom" not in decor:
                failures.append(f"vanilla {vt} street decorations hang on {decor}, ours on minecraft:bottom")
        plate = "data/minecraft/structure/pillager_outpost/feature_plate.nbt"
        if plate in names:
            feats = {t for _, t, p in _jigsaws(z.read(plate)) if p == "minecraft:pillager_outpost/features"}
            if "minecraft:feature" not in feats:
                failures.append(f"vanilla outpost feature plates hold features by {feats}, ours hang on minecraft:feature")
    print(f"[smoke] vanilla jigsaw conventions checked in {os.path.basename(jar)}", flush=True)


def load_origin(srv):
    """Keep the chunks around 0,0 loaded (place_structures ends with 'forceload remove all'), or every command
    there answers 'That position is not loaded'."""
    srv.run("execute in minecraft:overworld run forceload add -16 -16 16 16", r"Marked|forceload|No chunks|already", 120)


def summon_all(srv, failures):
    load_origin(srv)
    for eid in lang_ids("entity.wayfarers."):
        res = srv.run(f"execute in minecraft:overworld run summon wayfarers:{eid} 0 200 0",
                      r"Summoned|Unable|Unknown|Invalid|Incorrect", 60)
        if not res or "Summoned" not in res:
            failures.append(f"summon {eid}: {res}")
    srv.run("execute in minecraft:overworld run kill @e[type=!minecraft:player]", r"Killed|No entity", 60)
    items = lang_ids("item.wayfarers.") + lang_ids("block.wayfarers.")
    for iid in items:
        check_budget(f"item {iid}")
        res = srv.run(f'execute in minecraft:overworld run summon minecraft:item 0 200 0 '
                      f'{{Item:{{id:"wayfarers:{iid}",count:1}}}}',
                      r"Summoned|Unable|Unknown|Invalid|Incorrect|Expected", 60)
        if not res or "Summoned" not in res:
            failures.append(f"item {iid}: {res}")


def creatures_fight(srv, failures):
    """Every creature of the mod on the ground next to a villager, then 600 ticks at full speed: AI goals, attacks,
    projectiles, summons and boss phases all run, and any exception in them lands in the log."""
    srv.run("execute in minecraft:overworld run forceload add -64 -64 64 64", r"Marked|forceload|No chunks|already", 300)
    ground = -60  # the flat test world: bedrock, 2 dirt, grass on top at y -61
    for i, eid in enumerate(lang_ids("entity.wayfarers.")):
        x, z = (i % 8) * 14 - 49, (i // 8) * 14 - 49
        res = srv.run(f"execute in minecraft:overworld run summon wayfarers:{eid} {x} {ground} {z}",
                      r"Summoned|Unable|Unknown|Invalid|Incorrect|not loaded", 60)
        if not res or "Summoned" not in res:
            failures.append(f"summon {eid} on the ground: {res}")
        srv.run(f"execute in minecraft:overworld run summon minecraft:villager {x + 3} {ground} {z}",
                r"Summoned|Unable|Invalid|not loaded", 30)
    srv.run("execute in minecraft:overworld run summon minecraft:zombie 0 -60 0", r"Summoned|Unable|Invalid", 30)
    res = srv.run("tick sprint 600", r"Sprint completed|Unknown|Incorrect", 600)
    if not res or "Sprint completed" not in res:
        failures.append(f"tick sprint: {res}")
    srv.run("execute in minecraft:overworld run kill @e[type=!minecraft:player]", r"Killed|No entity", 60)


# Server performance check: a crowded base (PERF_MACHINES machines working a wheat field) and PERF_AUTOMATONS
# automatons fighting each other, then the mean time per tick over PERF_TICKS ticks (/tick sprint measures the real
# work of each tick, without the sleep between ticks). Above PERF_MAX_MSPT the run fails. The numbers go to the
# summary (wayfarers-ci-smoke.txt) with a baseline of the same world before anything was added.
PERF_MACHINES = {"auto_harvester": 24, "sprinkler": 16, "vacuum_hopper": 16, "entity_detector": 16,
                 "redstone_timer": 8, "wireless_transmitter": 8, "wireless_receiver": 8}
PERF_AUTOMATONS = {"brass_golem": 20, "clockwork_spider": 20, "steam_drone": 20}
PERF_TICKS = 600
PERF_MAX_MSPT = 25.0
SPRINT_RX = r"Sprint completed with (\d+) ticks per second, or ([\d.]+) ms per tick"


def sprint_mspt(srv, ticks, failures, what):
    res = srv.run(f"tick sprint {ticks}", SPRINT_RX + r"|Unknown|Incorrect", 900)
    m = re.search(SPRINT_RX, res or "")
    if not m:
        failures.append(f"performance: no sprint report for {what}: {res}")
        return None
    return float(m.group(2))


def tick_query(srv):
    """(average ms, p50, p95, p99) of the last 100 real-time ticks, from /tick query."""
    start = len(srv.lines)
    res = srv.run("tick query", r"Percentiles: P50", 60)
    avg = None
    for line in srv.lines[start:]:
        m = re.search(r"Average time per tick: ([\d.]+) ?ms", line)
        if m:
            avg = float(m.group(1))
    m = re.search(r"P50: ([\d.]+) ?ms P95: ([\d.]+) ?ms P99: ([\d.]+) ?ms", res or "")
    return (avg,) + (tuple(float(g) for g in m.groups()) if m else (None, None, None))


def server_performance(srv, failures):
    x0, z0 = -1200, -1200            # an area of its own, far from the other phases
    ground = -61                     # the flat test world: grass on top at y -61
    srv.run(f"execute in minecraft:overworld run forceload add {x0 - 16} {z0 - 16} {x0 + 112} {z0 + 112}",
            r"Marked|forceload|No chunks|already|too many|Too many", 300)
    srv.run("execute in minecraft:overworld run kill @e[type=!minecraft:player]", r"Killed|No entity", 60)
    base = sprint_mspt(srv, 200, failures, "the baseline")
    # a 96 x 96 wheat field, ripe, on farmland: harvesters and sprinklers have work, vacuum hoppers collect the rest
    for dz in range(0, 96, 32):
        srv.run(f"execute in minecraft:overworld run fill {x0} {ground} {z0 + dz} {x0 + 95} {ground} {z0 + dz + 31} "
                f"minecraft:farmland[moisture=7]", r"Successfully filled|No blocks|too big|Unknown|Invalid|not loaded", 60)
        srv.run(f"execute in minecraft:overworld run fill {x0} {ground + 1} {z0 + dz} {x0 + 95} {ground + 1} {z0 + dz + 31} "
                f"minecraft:wheat[age=7]", r"Successfully filled|No blocks|too big|Unknown|Invalid|not loaded", 60)
    placed = 0
    i = 0
    for bid, n in PERF_MACHINES.items():
        for _ in range(n):
            x, z = x0 + 3 + (i % 16) * 6, z0 + 3 + (i // 16) * 6
            res = srv.run(f"execute in minecraft:overworld run setblock {x} {ground + 1} {z} wayfarers:{bid}",
                          r"Changed|Could not|Unknown|Invalid|not loaded", 30)
            placed += 1 if res and "Changed" in res else 0
            i += 1
    if placed < sum(PERF_MACHINES.values()):
        failures.append(f"performance: only {placed} of {sum(PERF_MACHINES.values())} machines placed")
    summoned = 0
    i = 0
    for eid, n in PERF_AUTOMATONS.items():
        for _ in range(n):
            x, z = x0 + 8 + (i % 10) * 9, z0 + 8 + (i // 10) * 13
            res = srv.run(f"execute in minecraft:overworld run summon wayfarers:{eid} {x} {ground + 2} {z}",
                          r"Summoned|Unable|Unknown|Invalid|not loaded", 30)
            summoned += 1 if res and "Summoned" in res else 0
            i += 1
    if summoned < sum(PERF_AUTOMATONS.values()):
        failures.append(f"performance: only {summoned} of {sum(PERF_AUTOMATONS.values())} automatons summoned")
    loaded = sprint_mspt(srv, PERF_TICKS, failures, f"{placed} machines + {summoned} automatons")
    # then 30 s at the normal rate, for the tick-time percentiles a player would feel
    time.sleep(32)
    avg, p50, p95, p99 = tick_query(srv)
    Summary.perf.append(f"baseline (same world, nothing added), /tick sprint 200: {base} ms")
    Summary.perf.append(f"{placed} machines + {summoned} automatons, /tick sprint {PERF_TICKS}: {loaded} ms "
                        f"(limit {PERF_MAX_MSPT} ms)")
    Summary.perf.append(f"then at 20 TPS, /tick query (last 100 ticks): average {avg} ms, P50 {p50} ms, P95 {p95} ms, "
                        f"P99 {p99} ms")
    Summary.perf.append("machines: " + ", ".join(f"{n} {b}" for b, n in PERF_MACHINES.items()))
    Summary.perf.append("automatons: " + ", ".join(f"{n} {e}" for e, n in PERF_AUTOMATONS.items()))
    print("[smoke] performance: " + " | ".join(Summary.perf[:3]), flush=True)
    if loaded is not None and loaded > PERF_MAX_MSPT:
        failures.append(f"performance: {loaded} ms per tick with {placed} machines and {summoned} automatons "
                        f"(limit {PERF_MAX_MSPT} ms, baseline {base} ms)")
    srv.run("execute in minecraft:overworld run kill @e[type=!minecraft:player]", r"Killed|No entity", 60)
    srv.run("execute in minecraft:overworld run forceload remove all", r"Unmarked|forceload|No chunks", 30)


def blocks_and_loot(srv, failures):
    load_origin(srv)
    for bid in lang_ids("block.wayfarers."):
        check_budget(f"block {bid}")
        res = srv.run(f"execute in minecraft:overworld run setblock 0 150 0 wayfarers:{bid}",
                      r"Changed|Could not|Unknown|Invalid|not loaded", 30)
        if not res or re.search(r"Unknown|Invalid|not loaded", res):
            failures.append(f"setblock {bid}: {res}")
        srv.run("execute in minecraft:overworld run setblock 0 150 0 minecraft:air destroy", r"Changed|Could not|not loaded", 30)
    for table in loot_tables():
        res = srv.run(f"execute in minecraft:overworld run loot spawn 0 200 0 loot wayfarers:{table}",
                      r"Dropped|Unknown|Invalid|Incorrect|No loot", 30)
        if not res or "Dropped" not in res and "No loot" not in res:
            failures.append(f"loot {table}: {res}")
    srv.run("execute in minecraft:overworld run kill @e[type=minecraft:item]", r"Killed|No entity", 60)


def exercise_fit(srv, failures, shard=None):
    """Every Overworld structure of the mod (or every n-th with --shard i/n), located in a fresh normal world
    (Minecraft's terrain) and really generated: /wayfarers fitcheck measures floating edges, buried edges and flooding at each, draws it in
    place (wayfarers-fit-<id>.png) and writes wayfarers-fit.txt (wayfarers-fit-shard<i>.txt). A MISFIT or ERROR line
    fails the run, so every structure is checked on real terrain. A structure skipped for time is listed in the
    summary; the run fails for that only when more than half of the structures were skipped."""
    command = "wayfarers fitcheck" + (f" shard {shard[0]} {shard[1]}" if shard else "")
    name = f"wayfarers-fit-shard{shard[0]}.txt" if shard else "wayfarers-fit.txt"
    with Phase("structure fit" + (f" (shard {shard[0] + 1} of {shard[1]})" if shard else "")):
        # the command keeps to FIT_BUDGET (plus the structure in progress) and reports what it skipped past that
        res = srv.run(command, r"Fit check (written|failed)|Unknown|Incorrect", FIT_WAIT)
    if not res or "Fit check written" not in res:
        failures.append(f"fit check: no answer in {FIT_WAIT} s" if not res else f"fit check: {res}")
    report = os.path.join(srv.cwd, name)
    if not os.path.exists(report):
        failures.append(f"fit check: no {name}")
        return []
    lines = open(report, encoding="utf-8").read().splitlines()[1:]
    print("\n".join(["structure fit report:"] + lines), flush=True)
    verdicts = {}
    time_skips = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            verdicts[parts[0]] = parts[2]
            if parts[2] in ("MISFIT", "ERROR"):
                failures.append(f"structure {parts[2].lower()}: {line.strip()}")
            if parts[2] == "SKIPPED" and ("time budget" in line or "gave up" in line):
                time_skips.append(parts[0])
                Summary.notes.append("structure fit SKIPPED (time): " + re.sub(r"\s+", " ", line.strip()))
    checked = [v for v in verdicts.values() if v in ("OK", "MISFIT", "NOT_FOUND", "ERROR")]
    missing = [k for k, v in verdicts.items() if v == "NOT_FOUND"]
    if len(missing) > max(2, len(checked) // 3):
        failures.append(f"{len(missing)} of {len(checked)} structures not found near spawn (does the site check reject "
                        f"them everywhere on this terrain?): {missing}")
    if time_skips and len(time_skips) * 2 > len(checked) + len(time_skips):
        failures.append(f"structure fit: {len(time_skips)} of {len(checked) + len(time_skips)} structures skipped for "
                        f"time: {time_skips}")
    if res:
        srv.run("say fit test finished")
        time.sleep(2)
    return ["", f"structure fit ({name}):"] + ["  " + ln for ln in lines]


# ================================================================================ --world: biomes and speed gate
GENBENCH_RX = re.compile(r"Genbench area: (\d+) x \d+ chunks at block (-?\d+) (-?\d+) \((\d+) already loaded\) "
                         r"in (\d+) ms: ([\d.]+) ms/chunk")


def genbench_area(srv, x, z, size, failures, label):
    """/wayfarers genbench area: {"ms", "chunks", "already", "per_chunk"} or None."""
    res = srv.run(f"wayfarers genbench area {x} {z} {size}", r"Genbench area|Unknown|Incorrect", GENBENCH_WAIT)
    m = GENBENCH_RX.search(res or "")
    if not m:
        failures.append(f"genbench {label} at {x} {z}: {res}")
        return None
    side = int(m.group(1))
    return {"ms": float(m.group(5)), "chunks": side * side, "already": int(m.group(4)),
            "per_chunk": float(m.group(6)), "label": label, "x": x, "z": z, "size": side}


def locate_biome(srv, biome, x=4000, z=4000):
    """Nearest (x, z) of a biome from x z (away from spawn, so its area is fresh), or None."""
    res = srv.run(f"execute in minecraft:overworld positioned {x} 64 {z} run locate biome {biome}",
                  r"nearest|Could not find|Unknown|Invalid|not found|Incorrect", 300)
    m = re.search(r"\[(-?\d+), (-?[\d~]+), (-?\d+)\]", res or "")
    if not res or "nearest" not in res or not m:
        return None
    return int(m.group(1)), int(m.group(3))


def world_run(server_dir, custom, level_name, biome_spots, failures, bad):
    """One server start in a fresh normal world: WITH (custom) or WITHOUT the Wayfarers biomes and terrain touches.
    The same areas are generated in both, in the same order: a warm-up area (not counted), the fixed area, then the
    biome areas (biome_spots, found by the WITH run). Returns the genbench results."""
    import shutil
    shutil.rmtree(os.path.join(server_dir, level_name), ignore_errors=True)
    prepare(server_dir, False, level_name=level_name, custom=custom)
    tag = "with" if custom else "without"
    srv = Server(server_dir, server_command(server_dir), f"smoke-console-world-{tag}-{level_name}.log")
    boot = time.time()
    started = srv.wait_for(r"Done \(|Failed to load datapacks|Crashing|Encountered an unexpected exception", 1200)
    Summary.phases.append((f"server start ({tag}, {level_name})", time.time() - boot, ""))
    results = []
    if not started or "Done (" not in started:
        failures.append(f"server did not finish starting ({tag})")
    else:
        Phase.start = time.time()
        try:
            res = srv.run("datapack list enabled", r"data pack", 60)
            on = bool(res) and "wayfarers:custom_biomes" in res
            if on != custom:
                failures.append(f"pack wayfarers:custom_biomes {'not ' if custom else ''}enabled in the {tag} world: {res}")
            with Phase(f"generation benchmark ({tag})"):
                genbench_area(srv, WARMUP_X, WARMUP_Z, WARMUP_SIZE, failures, "warm-up")
                r = genbench_area(srv, BENCH_X, BENCH_Z, BENCH_SIZE, failures, "fixed area")
                if r:
                    results.append(r)
            if custom:
                with Phase("locate biomes"):
                    first = not biome_spots
                    for b in OUR_BIOMES:
                        spot = locate_biome(srv, f"wayfarers:{b}")
                        if spot is None:
                            failures.append(f"/locate biome wayfarers:{b}: not found within 6400 blocks of 4000 4000")
                        elif first:
                            biome_spots[b] = spot
            else:
                # the same lookups as the WITH run (their parents' climate), so both JVMs warm up alike
                for b in ("minecraft:swamp", "minecraft:badlands", "minecraft:desert"):
                    locate_biome(srv, b)
            with Phase(f"biome area benchmark ({tag})"):
                for b, (x, z) in sorted(biome_spots.items()):
                    r = genbench_area(srv, x, z, BIOME_BENCH_SIZE, failures, b)
                    if r:
                        results.append(r)
            res = srv.run("wayfarers genbench noise", r"Genbench world|Unknown|Incorrect", GENBENCH_WAIT)
            for line in list(srv.lines):
                m = re.search(r"(Genbench (vanilla|world).*)$", line)
                if m and ">>>" not in line:
                    Summary.notes.append(f"{tag}: {m.group(1)}")
            if custom:
                with Phase("biome shots"):
                    res = srv.run("wayfarers biomeshots", r"Biome shots (written|failed)|Unknown|Incorrect", BIOMESHOTS_WAIT)
                    m = re.search(r"written: (\d+) of (\d+)", res or "")
                    if not res or not m:
                        failures.append(f"biome shots: {res}")
                    elif int(m.group(1)) < int(m.group(2)):
                        failures.append(f"biome shots: only {m.group(1)} of {m.group(2)} drawn (see wayfarers-biomes.txt)")
        except TimeoutError as e:
            failures.append(str(e))
            Summary.notes.append(str(e))
    srv.run("stop")
    try:
        srv.proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        srv.proc.kill()
        failures.append(f"server did not stop ({tag})")
    bad += scan_log(server_dir, srv.lines)
    return results


def scan_log(server_dir, lines):
    """Suspicious lines of a run: its console and logs/latest.log (BAD minus BENIGN)."""
    text = list(lines)
    latest = os.path.join(server_dir, "logs", "latest.log")
    if os.path.exists(latest):
        text += open(latest, encoding="utf-8", errors="replace").read().splitlines()
    return [ln for ln in text if not any(b.search(ln) for b in BENIGN) and any(rx.search(ln) for rx in BAD)]


def exercise_world(server_dir, failures, bad):
    """The WITH / WITHOUT pair (twice, the second in the other order, when the first is over the gate). Returns the
    summary lines."""
    spots = {}
    pairs = []
    for attempt in range(2):
        order = [True, False] if attempt == 0 else [False, True]
        got = {}
        for custom in order:
            got[custom] = world_run(server_dir, custom, f"world_{'with' if custom else 'without'}_{attempt + 1}",
                                    spots, failures, bad)
        pairs.append(got)
        ratio = pair_ratio(pairs)
        if ratio is None or ratio <= GATE:
            break
        Summary.notes.append(f"generation speed: pair 1 over the gate ({ratio:.3f}), measured again in the other order")
    return speed_report(pairs, spots, failures)


def _match(with_, without):
    """The areas measured in both runs of a pair, by label."""
    w = {r["label"]: r for r in with_}
    o = {r["label"]: r for r in without}
    return [(w[k], o[k]) for k in w if k in o]


def pair_ratio(pairs):
    """WITH / WITHOUT full-generation time over every area measured in both runs of every pair."""
    tw = to = 0.0
    for got in pairs:
        for a, b in _match(got.get(True, []), got.get(False, [])):
            tw += a["ms"]
            to += b["ms"]
    return tw / to if to > 0 else None


def speed_report(pairs, spots, failures):
    lines = ["", "world generation speed (same seed, same fresh areas, full generation on the server's worker threads;",
             "  WITH = Wayfarers biomes + terrain touches, WITHOUT = vanilla generation; warm-up area not counted):"]
    for i, got in enumerate(pairs):
        lines.append(f"  pair {i + 1}:")
        for a, b in _match(got.get(True, []), got.get(False, [])):
            r = a["ms"] / b["ms"] if b["ms"] else float("nan")
            lines.append(f"    {a['label']:20s} {a['size']}x{a['size']} at {a['x']} {a['z']}: with {a['per_chunk']:.1f} "
                         f"ms/chunk, without {b['per_chunk']:.1f} ms/chunk, ratio {r:.3f}"
                         + (f" ({a['already']}/{b['already']} chunks already loaded)" if a["already"] or b["already"] else ""))
    ratio = pair_ratio(pairs)
    fixed = [(a, b) for got in pairs for a, b in _match(got.get(True, []), got.get(False, [])) if a["label"] == "fixed area"]
    if fixed:
        fr = sum(a["ms"] for a, _ in fixed) / max(1e-9, sum(b["ms"] for _, b in fixed))
        lines.append(f"  fixed area {BENCH_SIZE}x{BENCH_SIZE} at {BENCH_X} {BENCH_Z}: ratio {fr:.3f}")
    if spots:
        lines.append("  biome areas: " + ", ".join(f"{b} at {x} {z}" for b, (x, z) in sorted(spots.items())))
    if ratio is None:
        failures.append("generation speed: no area measured in both runs")
        lines.append("  ratio: not measured")
    else:
        verdict = "PASS" if ratio <= GATE else "FAIL"
        lines.append(f"  RATIO with / without (all areas, all pairs): {ratio:.3f} (gate <= {GATE}) {verdict}")
        if ratio > GATE:
            failures.append(f"generation speed: with the Wayfarers biomes and terrain touches {ratio:.3f}x vanilla "
                            f"(gate {GATE})")
    print("\n".join(lines), flush=True)
    return lines


def main():
    server_dir = os.path.abspath(sys.argv[1])
    args = sys.argv[2:]
    if "--world" in args:
        Summary.job = "world"
        failures, bad = [], []
        extra = exercise_world(server_dir, failures, bad)
        crashes = glob.glob(os.path.join(server_dir, "crash-reports", "*"))
        if crashes:
            failures.append(f"crash reports: {crashes}")
        if bad:
            failures.append(f"{len(set(bad))} suspicious log lines")
            for line in sorted(set(bad))[:200]:
                print("BAD:", line)
        for f in failures:
            print("FAIL:", f)
        try:
            Summary.write(server_dir, failures, bad, extra)
        except OSError as e:
            print(f"[smoke] could not write the summary: {e}", flush=True)
        print("world test:", "FAILED" if failures else "OK")
        sys.exit(1 if failures else 0)
    fit = "--fit" in args
    shard = None
    if "--shard" in args:
        i, n = args[args.index("--shard") + 1].split("/")
        shard = (int(i), int(n))
    Summary.job = (f"fit-{shard[0] + 1}of{shard[1]}" if shard else "fit") if fit else "smoke"
    prepare(server_dir, fit)
    failures = []
    extra = []
    if not fit:
        check_vanilla_jigsaws(server_dir, failures)
    log_name = "smoke-console-fit.log" if fit else "smoke-console.log"
    srv = Server(server_dir, server_command(server_dir), log_name)
    boot = time.time()
    # stop waiting as soon as the server gives up (a broken data pack used to cost the whole 15 minutes)
    started = srv.wait_for(r"Done \(|Failed to load datapacks|Crashing|Encountered an unexpected exception",
                           1200 if fit else 900)
    Summary.phases.append(("server start (spawn area included)", time.time() - boot, ""))
    if not started or "Done (" not in started:
        failures.append("server did not finish starting")
    else:
        Phase.start = time.time()
        try:
            if fit:
                extra = exercise_fit(srv, failures, shard)
            else:
                exercise_mod(srv, failures)
        except TimeoutError as e:
            failures.append(str(e))
            Summary.notes.append(str(e))
    srv.run("stop")
    try:
        srv.proc.wait(timeout=300 if fit else 180)  # the fit test saves the areas it generated
    except subprocess.TimeoutExpired:
        srv.proc.kill()
        failures.append("server did not stop")

    bad = scan_log(server_dir, srv.lines)
    crashes = glob.glob(os.path.join(server_dir, "crash-reports", "*"))
    if crashes:
        failures.append(f"crash reports: {crashes}")
    if bad:
        failures.append(f"{len(set(bad))} suspicious log lines")
        for line in sorted(set(bad))[:200]:
            print("BAD:", line)
    for f in failures:
        print("FAIL:", f)
    try:
        Summary.write(server_dir, failures, bad, extra)
    except OSError as e:
        print(f"[smoke] could not write the summary: {e}", flush=True)
    print("smoke test:", "FAILED" if failures else "OK")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
