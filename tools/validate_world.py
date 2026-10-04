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
BLOCK_ID = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")

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


# density function types (DensityFunctions.bootstrap, 26.2) -> their fields, and which of those are functions
_ONE = {"argument"}
DF_FIELDS = {
    **{t: ({"argument1", "argument2"}, {"argument1", "argument2"}) for t in ("add", "mul", "min", "max")},
    **{t: (_ONE, _ONE) for t in ("abs", "square", "cube", "half_negative", "quarter_negative", "invert", "squeeze",
                                  "interpolated", "flat_cache", "cache_2d", "cache_once", "cache_all_in_cell",
                                  "blend_density")},
    "clamp": ({"input", "min", "max"}, {"input"}),
    "noise": ({"noise", "xz_scale", "y_scale"}, set()),
    "shifted_noise": ({"noise", "xz_scale", "y_scale", "shift_x", "shift_y", "shift_z"}, {"shift_x", "shift_y", "shift_z"}),
    "range_choice": ({"input", "min_inclusive", "max_exclusive", "when_in_range", "when_out_of_range"},
                     {"input", "when_in_range", "when_out_of_range"}),
    "interval_select": ({"input", "thresholds", "functions"}, {"input"}),
    "shift_a": (_ONE, set()), "shift_b": (_ONE, set()), "shift": (_ONE, set()),
    "spline": ({"spline"}, set()),
    "constant": (_ONE, set()),
    "y_clamped_gradient": ({"from_y", "to_y", "from_value", "to_value"}, set()),
    "find_top_surface": ({"density", "upper_bound", "lower_bound", "cell_height"}, {"density", "upper_bound"}),
    "old_blended_noise": ({"xz_scale", "y_scale", "xz_factor", "y_factor", "smear_scale_multiplier"}, set()),
    "blend_alpha": (set(), set()), "blend_offset": (set(), set()), "beardifier": (set(), set()),
}


def check_df(node, where):
    """A density function: a number, a registered id, or an object whose type and fields match the 26.2 codecs."""
    if isinstance(node, (int, float)) or isinstance(node, str):
        return
    if not isinstance(node, dict) or "type" not in node:
        err(f"{where}: not a density function: {str(node)[:80]}")
        return
    t = node["type"].split(":")[-1]
    if t not in DF_FIELDS:
        err(f"{where}: unknown density function type {node['type']}")
        return
    fields, fns = DF_FIELDS[t]
    keys = set(node) - {"type"}
    if keys != fields:
        err(f"{where}: {t} has fields {sorted(keys)}, expected {sorted(fields)}")
        return
    for k in fns:
        check_df(node[k], f"{where}.{k}")
    if t == "interval_select":
        th = node["thresholds"]
        if th != sorted(th) or len(th) != len(node["functions"]) - 1:
            err(f"{where}: interval_select thresholds unsorted or wrong count")
        for i, f in enumerate(node["functions"]):
            check_df(f, f"{where}.functions[{i}]")
    if t == "spline":
        check_spline(node["spline"], f"{where}.spline")
    if t == "range_choice" and node["min_inclusive"] >= node["max_exclusive"]:
        err(f"{where}: empty range_choice range")
    if t == "y_clamped_gradient":
        for k in ("from_y", "to_y"):
            if not -4064 <= node[k] <= 4062:
                err(f"{where}: {k} out of range")


def check_spline(sp, where):
    if isinstance(sp, (int, float)):
        return
    if set(sp) != {"coordinate", "points"} or not sp["points"]:
        err(f"{where}: a spline needs a coordinate and points")
        return
    check_df(sp["coordinate"], f"{where}.coordinate")
    locs = [p["location"] for p in sp["points"]]
    if any(b <= a for a, b in zip(locs, locs[1:])):
        err(f"{where}: spline locations not strictly ascending: {locs}")
    for i, p in enumerate(sp["points"]):
        if set(p) != {"location", "value", "derivative"}:
            err(f"{where}.points[{i}]: fields {sorted(p)}")
        check_spline(p["value"], f"{where}.points[{i}]")


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

    # block states: the id must be a plain resource location ('minecraft:basalt[axis=y]' fails to parse)
    def check_states(obj, where):
        def fn(o):
            if isinstance(o, dict) and isinstance(o.get("Name"), str) and not BLOCK_ID.match(o["Name"]):
                err(f"{where}: bad block id {o['Name']}")
        walk(obj, fn)
    check_states(settings, "noise_settings")
    for path in glob.glob(os.path.join(PACK, "*", "worldgen", "configured_feature", "*.json")):
        check_states(json.load(open(path)), os.path.relpath(path, PACK))
    for router_key, v in settings["noise_router"].items():
        if isinstance(v, str) and v not in VANILLA_DENSITY | ours_df:
            err(f"noise_router.{router_key}: unknown density function {v}")
    for d in ours_df:
        check_refs(json.load(open(os.path.join(PACK, "wayfarers", "worldgen", "density_function", d.split(":")[1] + ".json"))), d)

    for name, d in [("noise_settings.noise_router." + k, v) for k, v in settings["noise_router"].items()] + \
            [(d, json.load(open(os.path.join(PACK, "wayfarers", "worldgen", "density_function", d.split(":")[1] + ".json"))))
             for d in sorted(ours_df)]:
        check_df(d, name)

    # world height: noise settings and dimension type agree, and fit the codecs (DimensionType, NoiseSettings)
    noise = settings["noise"]
    dt_path = os.path.join(PACK, "minecraft", "dimension_type", "overworld.json")
    if dim.get("type") == "minecraft:overworld" and os.path.exists(dt_path):
        dt = json.load(open(dt_path))
        if (dt["min_y"], dt["height"]) != (noise["min_y"], noise["height"]):
            err(f"dimension_type min_y/height {dt['min_y']}/{dt['height']} != noise settings {noise['min_y']}/{noise['height']}")
        if dt["logical_height"] > dt["height"]:
            err("dimension_type: logical_height > height")
    elif (noise["min_y"], noise["height"]) != (-64, 384):
        err("noise settings change the world height but the pack has no minecraft:dimension_type/overworld")
    if noise["min_y"] % 16 or noise["height"] % 16:
        err("noise min_y and height must be multiples of 16")
    if noise["min_y"] + noise["height"] > 2032 or noise["height"] > 4064 or noise["min_y"] < -2032:
        err("world height out of range (min_y >= -2032, min_y + height <= 2032)")
    cell = 4 * noise["size_vertical"]
    if noise["height"] % cell:
        err(f"noise height must be a multiple of the cell height {cell}")

    # template features: every template exists (mod data or the pack)
    res = os.path.join(HERE, "..", "src", "main", "resources")
    for path in glob.glob(os.path.join(PACK, "*", "worldgen", "configured_feature", "*.json")):
        cf = json.load(open(path))
        if cf.get("type") == "minecraft:template":
            for t in cf["config"]["templates"]:
                ns, p = t["data"]["id"].split(":")
                if not any(os.path.exists(os.path.join(r, ns, "structure", p + ".nbt"))
                           for r in (os.path.join(res, "data"), PACK)):
                    err(f"{path}: missing structure template {t['data']['id']}")

    for e in errors[:100]:
        print("ERROR:", e)
    print(f"world pack: {len(ours_biomes)} biomes, {len(dim['generator']['biome_source']['biomes'])} climate points, "
          f"{len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    sys.exit(main())
