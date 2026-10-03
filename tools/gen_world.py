#!/usr/bin/env python3
"""Generate the Wayfarers world overhaul: a built-in data pack (src/main/resources/worldgen_pack) that replaces the
Overworld's terrain, caves and biomes. Java adds it as a pack (WorldOverhaul.java), switched on by default and
turned off with the config option world.overhaul (or by unticking it in the "Data Packs" screen).

Terrain is vanilla's noise router (ported from NoiseRouterData, 26.2) with three changes:
  * mountains rise about 65% higher above sea level and are 50% more jagged (peaks around y 300),
  * a regional "mega-cavern" noise opens huge caverns between y -40 and 10,
  * the top slide starts at y 304 instead of 240, so the peaks are not cut flat.
Biomes are placed by vanilla's own climate layout (tools/wf/world_points.json, dumped from OverworldBiomeBuilder),
with every vanilla biome swapped for one of ours (wf/biomes.py), plus extra cave biomes.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


# ------------------------------------------------------------------ density function helpers (JSON builders)
def add(a, b):
    return {"type": "minecraft:add", "argument1": a, "argument2": b}


def mul(a, b):
    return {"type": "minecraft:mul", "argument1": a, "argument2": b}


def dmin(a, b):
    return {"type": "minecraft:min", "argument1": a, "argument2": b}


def dmax(a, b):
    return {"type": "minecraft:max", "argument1": a, "argument2": b}


def unary(kind, a):
    return {"type": f"minecraft:{kind}", "argument": a}


def clamp(a, lo, hi):
    return {"type": "minecraft:clamp", "input": a, "min": lo, "max": hi}


def noise(nid, xz=1.0, y=1.0):
    return {"type": "minecraft:noise", "noise": nid, "xz_scale": xz, "y_scale": y}


def ygrad(y0, y1, v0, v1):
    return {"type": "minecraft:y_clamped_gradient", "from_y": y0, "to_y": y1, "from_value": v0, "to_value": v1}


def range_choice(inp, lo, hi, yes, no):
    return {"type": "minecraft:range_choice", "input": inp, "min_inclusive": lo, "max_exclusive": hi,
            "when_in_range": yes, "when_out_of_range": no}


def lerp_const(t, k, v):
    """DensityFunctions.lerp(t, k, v) with a constant k: k + t * (v - k)."""
    return add(mul(t, add(v, -k)), k)


def y_limited(fn, lo, hi, outside):
    return unary("interpolated", range_choice("minecraft:y", lo, hi + 1, fn, outside))


def slide(fn):
    # like NoiseRouterData.slideOverworld, but the top slide starts at y 304 (vanilla: 240) for taller peaks
    top = ygrad(320 - 16, 320, 1.0, 0.0)
    fn = lerp_const(top, -0.078125, fn)
    bottom = ygrad(-64, -64 + 24, 0.0, 1.0)
    return lerp_const(bottom, 0.1171875, fn)


DF = f"{NS}:overworld/"


def density_functions():
    """Our registered density functions (data/wayfarers/worldgen/density_function/overworld/*)."""
    out = {}
    vanilla_offset = "minecraft:overworld/offset"
    # higher land: above sea level the offset spline is stretched by 65%
    out["offset"] = add(vanilla_offset, mul(0.65, dmax(add(vanilla_offset, 0.50375), 0.0)))
    out["depth"] = add(ygrad(-64, 320, 1.5, -1.5), DF + "offset")
    jagged = unary("half_negative", noise("minecraft:jagged", 1500.0, 0.0))
    out["jaggedness"] = unary("flat_cache", mul(mul(1.5, "minecraft:overworld/jaggedness"), jagged))
    initial = mul(4.0, unary("quarter_negative", mul(add(DF + "depth", DF + "jaggedness"), "minecraft:overworld/factor")))
    out["sloped_cheese"] = add(initial, "minecraft:overworld/base_3d_noise")
    # mega caverns: a regional 2D noise lowers the cheese threshold in a band between y -40 and 10
    band = dmin(ygrad(-56, -40, 0.0, 1.0), ygrad(10, 26, 1.0, 0.0))
    region = unary("flat_cache", clamp(mul(noise(f"{NS}:mega_caverns", 1.0, 0.0), 1.6), 0.0, 1.0))
    out["mega_caverns"] = mul(mul(band, region), -0.26)
    return out


def underground(sloped):
    layer = mul(4.0, unary("square", noise("minecraft:cave_layer", 1.0, 8.0)))
    cheese = noise("minecraft:cave_cheese", 1.0, 0.6666666666666666)
    solid = add(clamp(add(add(0.27, DF + "mega_caverns"), cheese), -1.0, 1.0),
                clamp(add(1.5, mul(-0.64, sloped)), 0.0, 0.5))
    base = add(layer, solid)
    subtract = dmin(dmin(base, "minecraft:overworld/caves/entrances"),
                    add("minecraft:overworld/caves/spaghetti_2d", "minecraft:overworld/caves/spaghetti_roughness_function"))
    pillars = range_choice("minecraft:overworld/caves/pillars", -1000000.0, 0.03, -1000000.0, "minecraft:overworld/caves/pillars")
    return dmax(subtract, pillars)


def noise_router():
    sloped = unary("cache_once", DF + "sloped_cheese")
    entrances = dmin(sloped, mul(5.0, "minecraft:overworld/caves/entrances"))
    caves = range_choice(sloped, -1000000.0, 1.5625, entrances, underground(sloped))
    post = unary("squeeze", unary("interpolated", mul(unary("blend_density", slide(caves)), 0.64)))
    final = dmin(post, "minecraft:overworld/caves/noodle")

    factor = unary("cache_2d", "minecraft:overworld/factor")
    offset = unary("cache_2d", DF + "offset")
    upper = add(mul(add(mul(0.2734375, unary("invert", factor)), mul(-1.0, offset)), -128.0), 128.0)
    upper = clamp(upper, -40.0, 320.0)
    gradient = mul(4.0, unary("quarter_negative", mul(add(ygrad(-64, 320, 1.5, -1.5), offset), factor)))
    surface_density = add(slide(clamp(add(gradient, -0.703125), -64.0, 64.0)), -0.390625)
    preliminary = {"type": "minecraft:find_top_surface", "density": surface_density, "upper_bound": upper,
                   "lower_bound": -64, "cell_height": 8}

    vein = lambda n: y_limited(noise(n, 4.0, 4.0), -60, 50, 0.0)  # noqa: E731
    return {
        "barrier": noise("minecraft:aquifer_barrier", 1.0, 0.5),
        "fluid_level_floodedness": noise("minecraft:aquifer_fluid_level_floodedness", 1.0, 0.67),
        "fluid_level_spread": noise("minecraft:aquifer_fluid_level_spread", 1.0, 0.7142857142857143),
        "lava": noise("minecraft:aquifer_lava"),
        "temperature": {"type": "minecraft:shifted_noise", "noise": "minecraft:temperature", "xz_scale": 0.25,
                        "y_scale": 0.0, "shift_x": "minecraft:shift_x", "shift_y": 0.0, "shift_z": "minecraft:shift_z"},
        "vegetation": {"type": "minecraft:shifted_noise", "noise": "minecraft:vegetation", "xz_scale": 0.25,
                       "y_scale": 0.0, "shift_x": "minecraft:shift_x", "shift_y": 0.0, "shift_z": "minecraft:shift_z"},
        "continents": "minecraft:overworld/continents",
        "erosion": "minecraft:overworld/erosion",
        "depth": DF + "depth",
        "ridges": "minecraft:overworld/ridges",
        "preliminary_surface_level": preliminary,
        "final_density": final,
        "vein_toggle": y_limited(noise("minecraft:ore_veininess", 1.5, 1.5), -60, 50, 0.0),
        "vein_ridged": add(-0.07999999821186066, dmax(unary("abs", vein("minecraft:ore_vein_a")),
                                                      unary("abs", vein("minecraft:ore_vein_b")))),
        "vein_gap": noise("minecraft:ore_gap"),
    }


def noise_settings(surface_rule):
    return {
        "sea_level": 63,
        "disable_mob_generation": False,
        "aquifers_enabled": True,
        "ore_veins_enabled": True,
        "legacy_random_source": False,
        "default_block": {"Name": "minecraft:stone"},
        "default_fluid": {"Name": "minecraft:water", "Properties": {"level": "0"}},
        "noise": {"min_y": -64, "height": 384, "size_horizontal": 1, "size_vertical": 2},
        "noise_router": noise_router(),
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
    write(f"{NS}/worldgen/noise/mega_caverns.json", {"firstOctave": -8, "amplitudes": [1.0, 1.0, 0.5]})
    for name, fn in density_functions().items():
        write(f"{NS}/worldgen/density_function/overworld/{name}.json", fn)
    write(f"{NS}/worldgen/noise_settings/overworld.json", noise_settings(biomes.surface_rule()))
    write_compact("minecraft/dimension/overworld.json", {
        "type": "minecraft:overworld",
        "generator": {"type": "minecraft:noise", "settings": f"{NS}:overworld",
                      "biome_source": {"type": "minecraft:multi_noise", "biomes": biomes.climate_points()}}})
    count = biomes.write_biomes(write)
    print(f"world overhaul written: {count} biomes")


if __name__ == "__main__":
    main()
