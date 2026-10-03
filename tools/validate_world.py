#!/usr/bin/env python3
"""Static checks for the world-overhaul pack (src/main/resources/worldgen_pack), run by validate.py.

Catches what would stop a world from loading: unknown biome, feature, density function or noise ids, features
listed in a different relative order in two biomes ("Feature order cycle found"), and malformed biome files.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "src", "main", "resources", "worldgen_pack", "data")
TEMPLATES = json.load(open(os.path.join(HERE, "wf", "vanilla_biome_templates.json")))

VANILLA_DENSITY = {f"minecraft:{n}" for n in (
    "zero", "y", "shift_x", "shift_z", "overworld/base_3d_noise", "overworld/continents", "overworld/erosion",
    "overworld/ridges", "overworld/ridges_folded", "overworld/offset", "overworld/factor", "overworld/jaggedness",
    "overworld/depth", "overworld/sloped_cheese", "overworld/caves/spaghetti_roughness_function",
    "overworld/caves/entrances", "overworld/caves/noodle", "overworld/caves/pillars",
    "overworld/caves/spaghetti_2d_thickness_modulator", "overworld/caves/spaghetti_2d")}
VANILLA_NOISES = {f"minecraft:{n}" for n in (
    "temperature", "vegetation", "continentalness", "erosion", "ridge", "offset", "aquifer_barrier",
    "aquifer_fluid_level_floodedness", "aquifer_lava", "aquifer_fluid_level_spread", "pillar", "pillar_rareness",
    "pillar_thickness", "spaghetti_roughness", "spaghetti_roughness_modulator", "cave_entrance", "cave_layer",
    "cave_cheese", "ore_veininess", "ore_vein_a", "ore_vein_b", "ore_gap", "noodle", "noodle_thickness",
    "noodle_ridge_a", "noodle_ridge_b", "jagged", "surface", "surface_secondary", "clay_bands_offset",
    "badlands_pillar", "badlands_pillar_roof", "badlands_surface", "iceberg_pillar", "iceberg_pillar_roof",
    "iceberg_surface", "surface_swamp", "calcite", "gravel", "powder_snow", "packed_ice", "ice")}
ALLOWED_TOP = {"has_precipitation", "temperature", "temperature_modifier", "downfall", "attributes", "effects",
               "spawners", "spawn_costs", "creature_spawn_probability", "carvers", "features"}
ALLOWED_EFFECTS = {"water_color", "foliage_color", "dry_foliage_color", "grass_color", "grass_color_modifier"}
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

errors = []


def err(msg):
    errors.append(msg)


def ids_in(path):
    return {os.path.splitext(os.path.relpath(p, path))[0].replace(os.sep, "/") for p in glob.glob(os.path.join(path, "**", "*.json"), recursive=True)}


def walk(obj, fn):
    fn(obj)
    if isinstance(obj, dict):
        for v in obj.values():
            walk(v, fn)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, fn)


def main():
    if not os.path.isdir(PACK):
        print("world overhaul pack not generated (run tools/gen_world.py)")
        return 1
    vanilla_features = set()
    for t in TEMPLATES.values():
        for step in t["features"]:
            vanilla_features |= set(step)
    from wf import worldfeatures
    for group in worldfeatures.DECOR.values():
        vanilla_features |= set(group)  # every id here was taken from the 26.2 Placements classes
    ours_biomes = {f"wayfarers:{b}" for b in ids_in(os.path.join(PACK, "wayfarers", "worldgen", "biome"))}
    ours_df = {f"wayfarers:{d}" for d in ids_in(os.path.join(PACK, "wayfarers", "worldgen", "density_function"))}
    ours_noise = {f"wayfarers:{n}" for n in ids_in(os.path.join(PACK, "wayfarers", "worldgen", "noise"))}
    ours_placed = {f"wayfarers:{n}" for n in ids_in(os.path.join(PACK, "wayfarers", "worldgen", "placed_feature"))}

    # biomes
    order = {}
    for bid in sorted(ours_biomes):
        path = os.path.join(PACK, "wayfarers", "worldgen", "biome", bid.split(":")[1] + ".json")
        b = json.load(open(path))
        for k in b:
            if k not in ALLOWED_TOP:
                err(f"{bid}: unknown key {k}")
        for k in ("has_precipitation", "temperature", "downfall", "effects", "carvers", "features", "spawners", "spawn_costs"):
            if k not in b:
                err(f"{bid}: missing {k}")
        for k, v in b["effects"].items():
            if k not in ALLOWED_EFFECTS:
                err(f"{bid}: effects.{k} not allowed")
            elif k.endswith("color") and not COLOR.match(v):
                err(f"{bid}: bad colour {k}={v}")
        for k in b.get("attributes", {}):
            if k in ("minecraft:gameplay/sky_light_level", "minecraft:gameplay/fast_lava"):
                err(f"{bid}: attribute {k} not allowed in a biome")
        if len(b["features"]) > 11:
            err(f"{bid}: more than 11 feature steps")
        for i, step in enumerate(b["features"]):
            for fid in step:
                if fid not in vanilla_features and fid not in ours_placed:
                    err(f"{bid}: unknown placed feature {fid}")
            for a in range(len(step)):
                for c in range(a + 1, len(step)):
                    key = (i, step[a], step[c])
                    rev = (i, step[c], step[a])
                    if rev in order:
                        err(f"feature order cycle: {step[a]} / {step[c]} (step {i}) in {bid} and {order[rev]}")
                    order.setdefault(key, bid)
        for cat, entries in b["spawners"].items():
            for e in entries:
                if set(e) != {"type", "weight", "minCount", "maxCount"}:
                    err(f"{bid}: bad spawner entry {e}")

    # dimension
    dim = json.load(open(os.path.join(PACK, "minecraft", "dimension", "overworld.json")))
    used = set()
    for entry in dim["generator"]["biome_source"]["biomes"]:
        used.add(entry["biome"])
        if entry["biome"] not in ours_biomes:
            err(f"dimension: unknown biome {entry['biome']}")
    for b in ours_biomes - used:
        err(f"biome {b} is never placed")

    # noise settings and density functions: every referenced id must exist
    def check_refs(obj, where):
        def fn(o):
            if isinstance(o, dict):
                if o.get("type") in ("minecraft:noise", "minecraft:shifted_noise") and \
                        o["noise"] not in VANILLA_NOISES | ours_noise:
                    err(f"{where}: unknown noise {o['noise']}")
                if o.get("type") == "minecraft:noise_threshold" and o["noise"] not in VANILLA_NOISES | ours_noise:
                    err(f"{where}: unknown surface noise {o['noise']}")
                if o.get("type") == "minecraft:biome":
                    for bb in o["biome_is"]:
                        if bb not in ours_biomes:
                            err(f"{where}: surface rule names unknown biome {bb}")
                for k, v in o.items():
                    if isinstance(v, str) and k in ("argument", "argument1", "argument2", "input", "when_in_range",
                                                    "when_out_of_range", "density", "upper_bound", "shift_x", "shift_z") \
                            and v not in VANILLA_DENSITY | ours_df:
                        err(f"{where}: unknown density function {v}")
        walk(obj, fn)
    settings = json.load(open(os.path.join(PACK, "wayfarers", "worldgen", "noise_settings", "overworld.json")))
    check_refs(settings, "noise_settings")
    for router_key, v in settings["noise_router"].items():
        if isinstance(v, str) and v not in VANILLA_DENSITY | ours_df:
            err(f"noise_router.{router_key}: unknown density function {v}")
    for d in ours_df:
        check_refs(json.load(open(os.path.join(PACK, "wayfarers", "worldgen", "density_function", d.split(":")[1] + ".json"))), d)

    for e in errors[:100]:
        print("ERROR:", e)
    print(f"world pack: {len(ours_biomes)} biomes, {len(dim['generator']['biome_source']['biomes'])} climate points, "
          f"{len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    sys.exit(main())
