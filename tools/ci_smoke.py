#!/usr/bin/env python3
"""Boot a real Forge server with the mod and exercise its content, then fail on any error in the log.

Used by CI (.github/workflows/build.yml) after `./gradlew build`:
    python3 tools/ci_smoke.py <server_dir>                    # flat world: every structure, mob, item, loot table
    python3 tools/ci_smoke.py <server_dir> --overhaul         # overhaul world: biomes, world map, biome renders
    python3 tools/ci_smoke.py <server_dir> --overhaul --fit   # overhaul world: how every structure sits on the terrain
    python3 tools/ci_smoke.py <server_dir> --overhaul --fit --shard 0/2   # ...every second structure from the first

The server directory must already contain an installed Forge server and the mod jar in mods/.
The script accepts the EULA, starts the server, waits for "Done", then from the console:
  * places every structure (in its own dimension), then our village and outpost pieces and vanilla villages and
    outposts that use them (after checking the vanilla jigsaw names they rely on in the server jar),
  * summons every entity and every item,
  * breaks mod blocks (loot tables + Forge loot modifiers),
  * spawns every loot table,
  * reloads data packs,
  * measures how fast chunks generate (/wayfarers genbench: vanilla's noise settings, and the overhaul's when on),
and stops the server. Any ERROR line, exception, crash report or failed command fails the run.

Every run writes a short diagnostic summary, wayfarers-ci-<job>.txt, into the server folder: phase durations, chunk
generation speed, FAIL lines, suspicious log lines, slow commands. CI publishes it with the world previews, so the
next diagnosis needs no log download.

Time: the server runs one command at a time, so a command the script stopped waiting for still blocks the ones after
it. The long commands (/wayfarers worldmap, biomeshots, fitcheck) keep to their own budgets (in the Java commands)
and the script waits that budget plus a margin; if one still does not answer, the remaining phases are skipped and
reported, not run behind it. Anything skipped for time is listed in the summary, never counted as a pass.
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
# Java-side budgets (keep in step): WorldMapCommand.BUDGET_MS 10 min, BiomeShotsCommand.BUDGET_MS 9 min,
# FitCheckCommand.BUDGET_MS 22 min (+ LOCATE_BUDGET_MS 5 min for the structure in progress). The script waits each
# budget plus a margin for the item in progress, so the server answers before the script gives up.
WORLDMAP_WAIT = 10 * 60 + 300
BIOMESHOTS_WAIT = 9 * 60 + 300
FIT_BUDGET = 22 * 60
FIT_WAIT = FIT_BUDGET + 5 * 60 + 180
GENBENCH_WAIT = 600
# a fresh area far from spawn and from everything else the tests generate
BENCH_X, BENCH_Z, BENCH_SIZE = 20000, 20000, 12


class Summary:
    """What wayfarers-ci-<job>.txt says (see the module docstring)."""
    job = "smoke"
    phases = []      # (name, seconds, note)
    bench = []       # "Genbench ..." lines
    notes = []       # skips, partial results, anything a reader must know
    slow = []        # "[smoke] slow: ..." lines

    @classmethod
    def write(cls, server_dir, failures, bad, extra=()):
        lines = [f"wayfarers CI summary: job {cls.job}, commit {os.environ.get('GITHUB_SHA', '?')[:12]}, "
                 f"run {os.environ.get('GITHUB_RUN_ID', '?')} attempt {os.environ.get('GITHUB_RUN_ATTEMPT', '?')}",
                 f"result: {'FAILED' if failures else 'OK'}", "", "phases (seconds):"]
        lines += [f"  {name:34s} {sec:6.0f}  {note}".rstrip() for name, sec, note in cls.phases]
        if cls.bench:
            lines += ["", "chunk generation:"] + ["  " + b for b in cls.bench]
            ratio = bench_ratio(cls.bench)
            if ratio:
                lines.append(f"  overhaul / vanilla (noise, ms per chunk): {ratio:.2f}x (target <= 1.5x)")
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


def bench_ratio(bench):
    """overhaul ms/chunk over vanilla ms/chunk from the genbench noise lines (None when one is missing)."""
    per = {}
    for b in bench:
        m = re.match(r"Genbench (vanilla|world \S+): ([\d.]+) ms/chunk", b)
        if m:
            per["vanilla" if m.group(1) == "vanilla" else "world"] = float(m.group(2))
    if "vanilla" in per and "world" in per and per["vanilla"] > 0:
        return per["world"] / per["vanilla"]
    return None


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


def prepare(server_dir, overhaul):
    with open(os.path.join(server_dir, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    props = ("online-mode=false\nspawn-protection=0\nlevel-seed=wayfarers-ci\nmax-tick-time=-1\n"
             "view-distance=4\nsimulation-distance=4\nsync-chunk-writes=false\n")
    if overhaul:
        # a fresh world with the default generator, so the overhaul pack replaces the Overworld
        props += "level-name=world_overhaul\n"
    else:
        # a flat Overworld generates in a blink; /place structure ignores biomes, so every structure
        # still assembles (full noise terrain made the run take over an hour on CI runners)
        props += "level-name=world\nlevel-type=minecraft\\:flat\ngenerate-structures=false\n"
        props += ('generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},'
                  '{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],'
                  '"biome":"minecraft:plains"}\n')
    with open(os.path.join(server_dir, "server.properties"), "w") as f:
        f.write(props)
    os.makedirs(os.path.join(server_dir, "config"), exist_ok=True)
    with open(os.path.join(server_dir, "config", "wayfarers-common.toml"), "w") as f:
        f.write(f"[world]\noverhaul = {'true' if overhaul else 'false'}\n")
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


def skip_phase(name, why):
    """A phase not run: printed and listed in the summary (never a silent pass)."""
    print(f"[smoke] {name}: SKIPPED ({why})", flush=True)
    Summary.phases.append((name, 0, f"SKIPPED: {why}"))
    Summary.notes.append(f"phase '{name}' skipped: {why}")


def genbench(srv, failures, area=True):
    """/wayfarers genbench: chunk generation speed (noise settings side by side, and a fresh area for real)."""
    with Phase("chunk generation benchmark"):
        if area:
            res = srv.run(f"wayfarers genbench area {BENCH_X} {BENCH_Z} {BENCH_SIZE}", r"Genbench area|Unknown|Incorrect",
                          GENBENCH_WAIT)
            if not res or "Genbench area" not in res:
                failures.append(f"genbench area: {res}")
        res = srv.run("wayfarers genbench noise", r"Genbench world|Unknown|Incorrect", GENBENCH_WAIT)
        if not res or "Genbench world" not in res:
            failures.append(f"genbench noise: {res}")
        time.sleep(0.5)
        for line in list(srv.lines):
            m = re.search(r"(Genbench .*)$", line)
            if m and "/wayfarers" not in line and ">>>" not in line and m.group(1) not in Summary.bench:
                Summary.bench.append(m.group(1))


def exercise_mod(srv, failures):
    with Phase("structures"):
        place_structures(srv, failures)
    with Phase("vanilla villages and outposts"):
        vanilla_villages(srv, failures)
    with Phase("entities and items"):
        summon_all(srv, failures)
    with Phase("creatures fighting"):
        creatures_fight(srv, failures)
    with Phase("blocks and loot"):
        blocks_and_loot(srv, failures)
    with Phase("reload"):
        srv.run("reload", r"Reloading|Failed", 120)
        time.sleep(20)
    # the flat test world has no noise terrain: the area is flat chunks, the noise line is vanilla's generator
    genbench(srv, failures)
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


def exercise_overhaul(srv, failures):
    """The overhaul pack is on, every biome of ours can be found, the world map and the biome renders are drawn,
    and nothing logs an error."""
    res = srv.run("datapack list enabled", r"data pack", 60)
    if not res or "wayfarers:world_overhaul" not in res:
        failures.append(f"world overhaul pack not enabled: {res}")
    biomes = sorted(os.path.splitext(n)[0] for n in os.listdir(
        os.path.join(RES, "worldgen_pack", "data", "wayfarers", "worldgen", "biome")))
    missing = []
    with Phase("locate biomes"):
        found = locate_all(srv, biomes, missing)
    print(f"biomes found: {found}", flush=True)
    print(f"biomes not found nearby: {missing}", flush=True)
    if len(missing) > len(biomes) // 3:
        failures.append(f"{len(missing)} of {len(biomes)} biomes not found: {missing}")
    genbench(srv, failures)
    with Phase("world map"):
        res = srv.run("wayfarers worldmap", r"World map written|worldmap:|Unknown|Incorrect", WORLDMAP_WAIT)
        if not res or "World map written" not in res:
            failures.append(f"world map: no answer in {WORLDMAP_WAIT} s ({res})")
        elif "partial" in res:
            Summary.notes.append("world map partial: " + res.split("World map written", 1)[1].strip()[:200])
    if not res:
        # the server is still drawing the map: everything sent now would wait behind it
        skip_phase("biome shots", "the world map did not answer, the server is still busy with it")
        skip_phase("generate terrain around spawn", "the server is busy")
        return
    with Phase("biome shots"):
        # really generates 5 x 5 chunks per biome and draws them (wayfarers-biome-<id>.png, published with the map);
        # the command keeps to about 9 minutes and skips what is left past that (listed in wayfarers-biomes.txt)
        res = srv.run("wayfarers biomeshots", r"Biome shots (written|failed)|Unknown|Incorrect", BIOMESHOTS_WAIT)
        m = re.search(r"written: (\d+) of (\d+)", res or "")
        if not res or "Biome shots written" not in res or not m:
            failures.append(f"biome shots: {res}")
        else:
            done, total = int(m.group(1)), int(m.group(2))
            legend = os.path.join(srv.cwd, "wayfarers-biomes.txt")
            skipped = [ln.strip() for ln in open(legend, encoding="utf-8")] if os.path.exists(legend) else []
            skipped = [ln for ln in skipped if "skipped:" in ln]
            for ln in skipped:
                Summary.notes.append("biome shot " + re.sub(r"\s+", " ", ln))
            if done * 2 < total:
                failures.append(f"biome shots: only {done} of {total} drawn ({len(skipped)} skipped, see wayfarers-biomes.txt)")
    if not res:
        skip_phase("generate terrain around spawn", "the biome shots did not answer, the server is still busy")
        return
    with Phase("generate terrain around spawn"):
        srv.run("execute in minecraft:overworld run forceload add -64 -64 64 64", r"Marked|forceload|No chunks", 600)
    srv.run("say overhaul test finished")
    time.sleep(2)


def exercise_fit(srv, failures, shard=None):
    """Every Overworld structure of the mod (or every n-th with --shard i/n), located in the overhaul world and really
    generated: /wayfarers fitcheck measures floating edges, buried edges and flooding at each, draws it in place
    (wayfarers-fit-<id>.png) and writes wayfarers-fit.txt (wayfarers-fit-shard<i>.txt). A MISFIT or ERROR line fails
    the run, so any change of the terrain is checked against every structure. A structure skipped for time is listed
    in the summary; the run fails for that only when more than half of the structures were skipped."""
    res = srv.run("datapack list enabled", r"data pack", 60)
    if not res or "wayfarers:world_overhaul" not in res:
        failures.append(f"world overhaul pack not enabled: {res}")
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


def locate_all(srv, biomes, missing):
    found = {}
    for b in biomes:
        check_budget(f"biome {b}")
        res = srv.run(f"execute in minecraft:overworld run locate biome wayfarers:{b}",
                      r"nearest|Could not find|Unknown|Invalid|not found|Incorrect", 300)
        if not res or "nearest" not in res:
            missing.append(b)
        else:
            m = re.search(r"\((\d+) blocks away\)", res)
            found[b] = int(m.group(1)) if m else -1
    return found


def main():
    server_dir = os.path.abspath(sys.argv[1])
    args = sys.argv[2:]
    overhaul = "--overhaul" in args
    fit = "--fit" in args
    overhaul = overhaul or fit
    shard = None
    if "--shard" in args:
        i, n = args[args.index("--shard") + 1].split("/")
        shard = (int(i), int(n))
    Summary.job = (f"fit-{shard[0] + 1}of{shard[1]}" if shard else "fit") if fit else "world" if overhaul else "smoke"
    prepare(server_dir, overhaul)
    failures = []
    extra = []
    if not overhaul:
        check_vanilla_jigsaws(server_dir, failures)
    log_name = "smoke-console-fit.log" if fit else "smoke-console-overhaul.log" if overhaul else "smoke-console.log"
    srv = Server(server_dir, server_command(server_dir), log_name)
    boot = time.time()
    # stop waiting as soon as the server gives up (a broken data pack used to cost the whole 15 minutes)
    started = srv.wait_for(r"Done \(|Failed to load datapacks|Crashing|Encountered an unexpected exception",
                           1800 if overhaul else 900)
    Summary.phases.append(("server start (spawn area included)", time.time() - boot, ""))
    if not started or "Done (" not in started:
        failures.append("server did not finish starting")
    else:
        Phase.start = time.time()
        try:
            if fit:
                extra = exercise_fit(srv, failures, shard)
            else:
                (exercise_overhaul if overhaul else exercise_mod)(srv, failures)
        except TimeoutError as e:
            failures.append(str(e))
            Summary.notes.append(str(e))
    srv.run("stop")
    try:
        srv.proc.wait(timeout=300 if overhaul else 180)  # the overhaul test saves the biome render areas
    except subprocess.TimeoutExpired:
        srv.proc.kill()
        failures.append("server did not stop")

    text = list(srv.lines)
    latest = os.path.join(server_dir, "logs", "latest.log")
    if os.path.exists(latest):
        text += open(latest, encoding="utf-8", errors="replace").read().splitlines()
    bad = []
    for line in text:
        if any(b.search(line) for b in BENIGN):
            continue
        if any(rx.search(line) for rx in BAD):
            bad.append(line)
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
