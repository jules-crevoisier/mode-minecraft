#!/usr/bin/env python3
"""Boot a real Forge server with the mod and exercise its content, then fail on any error in the log.

Used by CI (.github/workflows/build.yml) after `./gradlew build`:
    python3 tools/ci_smoke.py <server_dir>

The server directory must already contain an installed Forge server and the mod jar in mods/.
The script accepts the EULA, starts the server, waits for "Done", then from the console:
  * places every structure (in its own dimension),
  * summons every entity and every item,
  * breaks mod blocks (loot tables + Forge loot modifiers),
  * spawns every loot table,
  * reloads data packs,
and stops the server. Any ERROR line, exception, crash report or failed command fails the run.
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
BUDGET = 25 * 60  # seconds per test; past it the remaining phases are skipped and the run fails with a clear message


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
                print(f"[smoke] slow: {command} took {time.time() - t:.0f}s -> {res}", flush=True)
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
        print(f"[smoke] {self.name}: {time.time() - self.t:.0f}s", flush=True)


def exercise_mod(srv, failures):
    with Phase("structures"):
        place_structures(srv, failures)
    with Phase("entities and items"):
        summon_all(srv, failures)
    with Phase("creatures fighting"):
        creatures_fight(srv, failures)
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
        srv.run(f"execute in {dim} run forceload add {x - r} {-r} {x + r} {r}", r"Marked|forceload|No chunks|too many", 30)
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
    with Phase("world map"):
        res = srv.run("wayfarers worldmap", r"World map written|worldmap:|Unknown|Incorrect", 900)
        if not res or "World map written" not in res:
            failures.append(f"world map: {res}")
    with Phase("biome shots"):
        # really generates 5 x 5 chunks per biome and draws them (wayfarers-biome-<id>.png, published with the map);
        # the command keeps to about 9 minutes and skips what is left past that
        res = srv.run("wayfarers biomeshots", r"Biome shots (written|failed)|Unknown|Incorrect", 1200)
        if not res or "Biome shots written" not in res or "written: 0 of" in res:
            failures.append(f"biome shots: {res}")
    with Phase("generate terrain around spawn"):
        srv.run("execute in minecraft:overworld run forceload add -64 -64 64 64", r"Marked|forceload|No chunks", 600)
    srv.run("say overhaul test finished")
    time.sleep(2)


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
    overhaul = "--overhaul" in sys.argv[2:]
    prepare(server_dir, overhaul)
    failures = []
    srv = Server(server_dir, server_command(server_dir), "smoke-console-overhaul.log" if overhaul else "smoke-console.log")
    # stop waiting as soon as the server gives up (a broken data pack used to cost the whole 15 minutes)
    started = srv.wait_for(r"Done \(|Failed to load datapacks|Crashing|Encountered an unexpected exception",
                           1800 if overhaul else 900)
    if not started or "Done (" not in started:
        failures.append("server did not finish starting")
    else:
        Phase.start = time.time()
        try:
            (exercise_overhaul if overhaul else exercise_mod)(srv, failures)
        except TimeoutError as e:
            failures.append(str(e))
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
    print("smoke test:", "FAILED" if failures else "OK")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
