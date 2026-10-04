#!/usr/bin/env python3
"""Generate the Wayfarers world overhaul: a built-in data pack (src/main/resources/worldgen_pack) that replaces the
Overworld's terrain, caves and biomes. Java adds it as a pack (WorldOverhaul.java), switched on by default and
turned off with the config option world.overhaul (or by unticking it in the "Data Packs" screen).

Terrain: wf/terrain.py (continents, rolling lowlands, escarpments, canyon plateaus, sharp mountain ranges up to
y ~320, terraced mesas, spires, fjords, archipelagos, skylands; caves with mega caverns and underground rivers).
The world is 448 blocks tall (y -64..383): the pack overrides minecraft:dimension_type/overworld.
tools/world_preview.py draws maps and cross-sections of it (build/world_preview/).
Biomes are placed by vanilla's own climate layout (tools/wf/world_points.json, dumped from OverworldBiomeBuilder),
with every vanilla biome swapped for one of ours (wf/biomes.py), plus extra cave biomes.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wf import terrain as T  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACK = os.path.join(ROOT, "src", "main", "resources", "worldgen_pack")
DATA = os.path.join(PACK, "data")
NS = "wayfarers"


def write(rel, obj):
    path = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_compact(rel, obj):
    path = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"))
        f.write("\n")


def noise_settings(surface_rule):
    return {
        "sea_level": 63,
        "disable_mob_generation": False,
        "aquifers_enabled": True,
        "ore_veins_enabled": True,
        "legacy_random_source": False,
        "default_block": {"Name": "minecraft:stone"},
        "default_fluid": {"Name": "minecraft:water", "Properties": {"level": "0"}},
        "noise": {"min_y": T.MIN_Y, "height": T.HEIGHT, "size_horizontal": 1, "size_vertical": 2},
        "noise_router": T.noise_router(),
        "spawn_target": [
            {"temperature": [-1.0, 1.0], "humidity": [-1.0, 1.0], "continentalness": [-0.11, 1.0],
             "erosion": [-1.0, 1.0], "depth": 0.0, "weirdness": [-1.0, -0.16], "offset": 0.0},
            {"temperature": [-1.0, 1.0], "humidity": [-1.0, 1.0], "continentalness": [-0.11, 1.0],
             "erosion": [-1.0, 1.0], "depth": 0.0, "weirdness": [0.16, 1.0], "offset": 0.0},
        ],
        "surface_rule": surface_rule,
    }


def main():
    from wf import biomes
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    os.makedirs(PACK)
    with open(os.path.join(PACK, "pack.mcmeta"), "w") as f:
        json.dump({"pack": {"description": "Wayfarers: world overhaul (terrain, caves and biomes)",
                            "min_format": 88, "max_format": 107}}, f, indent=1)
        f.write("\n")
    icon = os.path.join(ROOT, "src", "main", "resources", "pack.png")
    if os.path.exists(icon):
        shutil.copy(icon, os.path.join(PACK, "pack.png"))
    for name, params in T.noise_json().items():
        write(f"{NS}/worldgen/noise/{name}.json", params)
    for name, fn in T.density_functions().items():
        write(f"{NS}/worldgen/density_function/overworld/{name}.json", fn)
    write("minecraft/dimension_type/overworld.json", T.dimension_type())
    write(f"{NS}/worldgen/noise_settings/overworld.json", noise_settings(biomes.surface_rule()))
    write_compact("minecraft/dimension/overworld.json", {
        "type": "minecraft:overworld",
        "generator": {"type": "minecraft:noise", "settings": f"{NS}:overworld",
                      "biome_source": {"type": "minecraft:multi_noise", "biomes": biomes.climate_points()}}})
    from wf import wrecks, worldobjects
    wrecks.write(ROOT)
    worldobjects.write(ROOT)
    count = biomes.write_biomes(write)
    print(f"world overhaul written: {count} biomes")


if __name__ == "__main__":
    main()
