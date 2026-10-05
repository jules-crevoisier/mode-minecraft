#!/usr/bin/env python3
"""Generate the Wayfarers biomes and terrain touches (tools/wf/worldbiomes.py, objects in tools/wf/worldobjects.py).

Minecraft's terrain stays as it is. Written here:
  * mod data (always loaded): the three biomes (data/wayfarers/worldgen/biome), their features and the terrain
    touches' features (worldgen/{configured,placed}_feature/world/), the Forge biome modifiers of the touches
    (forge/biome_modifier/terrain_*.json, type wayfarers:toggled_features, config world.terrain.*), the object
    templates (structure/worldobjects), the biome tags (our biomes join the vanilla and Wayfarers tags of the
    vanilla biome they come from: structures, mob variants, ores) and the structure tag wayfarers:clears_decoration;
  * the built-in data pack custom_biomes_pack (Java: CustomBiomesPack, config world.customBiomes): the Overworld
    dimension with vanilla's biome parameter list, our slices carved in, and the noise settings wayfarers:overworld
    = vanilla's minecraft:overworld word for word plus our surface rules.

Run after gen_structures.py and gen_data.py (it adds our biomes to the biome tags they write); generate_all.py does.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wf import worldbiomes as WB  # noqa: E402
from wf import worldobjects  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
DATA = os.path.join(RES, "data")
PACK = os.path.join(RES, "custom_biomes_pack")
NS = "wayfarers"

# vanilla surface structures whose chunks keep the big decorations (thorns, hoodoos, spires, boulders) away
VANILLA_CLEARS = ["#minecraft:village", "minecraft:pillager_outpost", "minecraft:desert_pyramid",
                  "minecraft:jungle_pyramid", "minecraft:swamp_hut", "minecraft:igloo", "minecraft:mansion",
                  "minecraft:trail_ruins"]


def write(path, obj, compact=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
        else:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def reset_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)


def write_pack():
    """custom_biomes_pack: the Overworld dimension and its noise settings (nothing else)."""
    reset_dir(PACK)
    write(os.path.join(PACK, "pack.mcmeta"), {"pack": {
        "description": "Wayfarers: Crimson Mire, Volcanic Highlands and Pale Dunes in the Overworld",
        "min_format": 88, "max_format": 107}})
    icon = os.path.join(RES, "pack.png")
    if os.path.exists(icon):
        shutil.copy(icon, os.path.join(PACK, "pack.png"))
    points, counts = WB.climate_points()
    write(os.path.join(PACK, "data", "minecraft", "dimension", "overworld.json"), {
        "type": "minecraft:overworld",
        "generator": {"type": "minecraft:noise", "settings": f"{NS}:overworld",
                      "biome_source": {"type": "minecraft:multi_noise", "biomes": points}}}, compact=True)
    write(os.path.join(PACK, "data", NS, "worldgen", "noise_settings", "overworld.json"), WB.noise_settings())
    return points, counts


def write_mod_data():
    for bid in WB.BIOMES:
        write(os.path.join(DATA, NS, "worldgen", "biome", f"{bid}.json"), WB.biome_json(bid))
    biome_dir = os.path.join(DATA, NS, "worldgen", "biome")
    for f in os.listdir(biome_dir):
        if f[:-5] not in WB.BIOMES:
            os.remove(os.path.join(biome_dir, f))
    for kind in ("configured_feature", "placed_feature"):
        reset_dir(os.path.join(DATA, NS, "worldgen", kind, "world"))
    for rel, obj in WB.feature_files().items():
        kind, fid = rel.split("/", 1)
        write(os.path.join(DATA, NS, "worldgen", kind, "world", f"{fid}.json"), obj)
    mods = os.path.join(DATA, NS, "forge", "biome_modifier")
    for f in os.listdir(mods):
        if f.startswith("terrain_"):
            os.remove(os.path.join(mods, f))
    for name, obj in WB.touch_modifiers().items():
        write(os.path.join(mods, f"{name}.json"), obj)
    return len(WB.FEATURES)


def write_tags():
    """Our biomes join every tag that lists their parent biome by name: vanilla's (copied into
    data/minecraft/tags/worldgen/biome, replace false) and the mod's (the files gen_structures/gen_data wrote)."""
    vanilla = json.load(open(os.path.join(ROOT, "tools", "wf", "vanilla_biome_tags.json")))
    parents = {bid: set(b["parent"][0]) for bid, b in WB.BIOMES.items()}

    def ours_for(listed):
        names = {v.split(":")[-1] for v in listed if not v.startswith("#")}
        return [f"{NS}:{bid}" for bid, ps in parents.items() if ps & names]

    out = os.path.join(DATA, "minecraft", "tags", "worldgen", "biome")
    reset_dir(out)
    count = 0
    for tag, entry in sorted(vanilla.items()):
        values = ours_for(entry["biomes"])
        if values:
            write(os.path.join(out, f"{tag}.json"), {"replace": False, "values": values})
            count += 1
    mine = os.path.join(DATA, NS, "tags", "worldgen", "biome")
    for dirpath, _dirs, files in os.walk(mine):
        for f in sorted(files):
            path = os.path.join(dirpath, f)
            tag = json.load(open(path))
            listed = [v["id"] if isinstance(v, dict) else v for v in tag["values"]]
            add = [v for v in ours_for(listed) if v not in listed]
            if add:
                tag["values"] = tag["values"] + add
                write(path, tag)
                count += 1
    # surface structures that keep the big decorations out of their chunks (ClearOfStructuresFilter)
    from wf import defs, placement
    import wf.structures  # noqa: F401  (fills defs.STRUCTURES)
    ours = sorted(f"{NS}:{s.id}" for s in defs.STRUCTURES if s.dimension == "overworld"
                  and placement.fit_params(s.id)["mode"] in ("land", "wetland", "coast"))
    write(os.path.join(DATA, NS, "tags", "worldgen", "structure", "clears_decoration.json"),
          {"replace": False, "values": ours + [{"id": v, "required": False} for v in VANILLA_CLEARS]})
    return count


def main():
    names = worldobjects.write(ROOT)
    points, counts = write_pack()
    features = write_mod_data()
    tags = write_tags()
    vanilla_count = len(WB.vanilla_points())
    ours = {b: n for b, n in counts.items() if b.startswith(NS + ":")}
    print(f"world written: {len(WB.BIOMES)} biomes ({', '.join(f'{b} {n} points' for b, n in sorted(ours.items()))}), "
          f"{len(points)} climate points (vanilla {vanilla_count}), {features} features, {len(names)} object "
          f"templates, {tags} biome tags")


if __name__ == "__main__":
    main()
