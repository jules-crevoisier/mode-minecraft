#!/usr/bin/env python3
"""Regenerate tools/wf/world_points.json (vanilla's Overworld climate layout) from a decompiled game.

    python3 tools/biome_harness/make_points.py <path to decompiled net/minecraft/world/level/biome/OverworldBiomeBuilder.java>

The Mojang file is copied to a temp dir with biome keys turned into strings, compiled with the small
Climate/Pair stand-ins next to this script, run, and its points stored as [biome, t, h, c, e, d, w, offset] rows.
Nothing from the game is kept in the repository.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "wf", "world_points.json")


def transform(src):
    s = re.sub(r"^import .*?;\n", "", src, flags=re.M)
    s = re.sub(r"^package .*?;", "package harness;\nimport java.util.function.Consumer;\nimport java.util.List;", s, flags=re.M)
    s = s.replace("ResourceKey<Biome>", "String").replace("new ResourceKey[][]", "new String[][]")
    s = re.sub(r"Biomes\.([A-Z_]+)", lambda m: '"' + m.group(1).lower() + '"', s)
    s = re.sub(r"if \(SharedConstants\.debugGenerateSquareTerrainWithoutNoise\) \{\s*this\.addDebugBiomes\(biomes\);\s*\} else \{(.*?)\}\n\t\}",
               r"\1}", s, flags=re.S)
    s = s[:s.index("\tprivate void addDebugBiomes")] + s[s.index("\tprivate void addOffCoastBiomes"):]
    s = s[:s.index("\tpublic static boolean isDeepDarkRegion")] + "}\n"
    return s.replace("@VisibleForDebug", "")


def main():
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "harness"))
        with open(os.path.join(tmp, "harness", "OverworldBiomeBuilder.java"), "w") as f:
            f.write(transform(open(sys.argv[1]).read()))
        for name in ("Climate.java", "Pair.java", "Dump.java"):
            shutil.copy(os.path.join(HERE, name), os.path.join(tmp, "harness", name))
        subprocess.run(["javac", "-nowarn", "-d", os.path.join(tmp, "out")] +
                       [os.path.join(tmp, "harness", n) for n in os.listdir(os.path.join(tmp, "harness"))], check=True)
        raw = subprocess.run(["java", "-cp", os.path.join(tmp, "out"), "harness.Dump"], check=True,
                             capture_output=True, text=True).stdout
        rows = [[x["b"], x["t"], x["h"], x["c"], x["e"], x["d"], x["w"], x["o"]] for x in json.loads(raw)]
        with open(OUT, "w") as f:
            json.dump(rows, f, separators=(",", ":"))
        print(f"{len(rows)} points written to {os.path.relpath(OUT)}")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
