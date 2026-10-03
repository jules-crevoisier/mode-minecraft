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
    def __init__(self, cwd, cmd):
        self.lines = []
        self.q = queue.Queue()
        self.log = open(os.path.join(cwd, "smoke-console.log"), "w", encoding="utf-8")
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
            return self.wait_for(expect, timeout)
        time.sleep(0.2)
        return None


def server_command(server_dir):
    if os.path.exists(os.path.join(server_dir, "run.sh")):
        return ["bash", "run.sh", "nogui"]
    jars = [j for j in glob.glob(os.path.join(server_dir, "*.jar")) if "installer" not in j]
    if not jars:
        sys.exit("no server jar or run.sh in " + server_dir)
    return ["java", "-Xmx4G", "-jar", os.path.basename(jars[0]), "nogui"]


def main():
    server_dir = os.path.abspath(sys.argv[1])
    with open(os.path.join(server_dir, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    with open(os.path.join(server_dir, "server.properties"), "w") as f:
        f.write("online-mode=false\nspawn-protection=0\nlevel-seed=wayfarers-ci\nmax-tick-time=-1\n"
                "view-distance=4\nsimulation-distance=4\nsync-chunk-writes=false\n")
    jvm = os.path.join(server_dir, "user_jvm_args.txt")
    if os.path.exists(jvm):
        with open(jvm, "a") as f:
            f.write("\n-Xmx4G\n")

    failures = []
    srv = Server(server_dir, server_command(server_dir))
    if not srv.wait_for(r"Done \(", 900):
        failures.append("server did not finish starting")
    else:
        dims = structure_dims()
        for i, (sid, dim) in enumerate(dims.items()):
            x = 2000 + 400 * i
            r = 96
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
        for eid in lang_ids("entity.wayfarers."):
            res = srv.run(f"execute in minecraft:overworld run summon wayfarers:{eid} 0 200 0",
                          r"Summoned|Unable|Unknown|Invalid|Incorrect", 60)
            if not res or "Summoned" not in res:
                failures.append(f"summon {eid}: {res}")
        srv.run("execute in minecraft:overworld run kill @e[type=!minecraft:player]", r"Killed|No entity", 60)
        items = lang_ids("item.wayfarers.") + lang_ids("block.wayfarers.")
        for iid in items:
            res = srv.run(f'execute in minecraft:overworld run summon minecraft:item 0 200 0 '
                          f'{{Item:{{id:"wayfarers:{iid}",count:1}}}}',
                          r"Summoned|Unable|Unknown|Invalid|Incorrect|Expected", 60)
            if not res or "Summoned" not in res:
                failures.append(f"item {iid}: {res}")
        for bid in lang_ids("block.wayfarers."):
            srv.run(f"execute in minecraft:overworld run setblock 0 150 0 wayfarers:{bid}", r"Changed|Could not|Unknown|Invalid", 30)
            srv.run("execute in minecraft:overworld run setblock 0 150 0 minecraft:air destroy", r"Changed|Could not", 30)
        for table in loot_tables():
            res = srv.run(f"execute in minecraft:overworld run loot spawn 0 200 0 loot wayfarers:{table}",
                          r"Dropped|Unknown|Invalid|Incorrect|No loot", 30)
            if not res or "Dropped" not in res and "No loot" not in res:
                failures.append(f"loot {table}: {res}")
        srv.run("execute in minecraft:overworld run kill @e[type=minecraft:item]", r"Killed|No entity", 60)
        res = srv.run("reload", r"Reloading|Failed", 120)
        time.sleep(20)
        srv.run("say smoke test finished")
        time.sleep(2)
    srv.run("stop")
    try:
        srv.proc.wait(timeout=180)
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
