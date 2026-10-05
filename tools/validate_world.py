#!/usr/bin/env python3
"""Static checks for the Wayfarers biomes and terrain touches (tools/gen_world.py), run by validate.py and on its own.

Catches what would stop a world from loading or would quietly change vanilla terrain:
  * the pack (custom_biomes_pack): only the Default world preset, whose Overworld uses wayfarers:overworld (mod
    data), noise settings that are vanilla's
    minecraft:overworld word for word except the surface rule, which is vanilla's with one rule put in front; the
    biome list is vanilla's with only our slices carved out of the parent cells: every climate value reads back as
    the intended quantized value, and a brute-force nearest-biome test on random climates gives vanilla's answer
    everywhere outside our slices (and the parent biome's slice inside them);
  * our biomes: field names, colours, attributes, particles, music, spawners, every placed feature known, and no
    feature order cycle across all overworld biomes once the Forge biome modifiers are applied;
  * our features: field names against the 26.2 codecs of the feature and placement types used, block-state
    "Name"s (plain ids of known blocks), structure templates that exist, referenced configured features;
  * the terrain touches' biome modifiers: toggles that the Java config knows, vanilla biomes, known features;
  * the biome names in en_us / fr_fr.
"""
import glob
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wf import worldbiomes as WB  # noqa: E402
from wf import worldobjects  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
DATA = os.path.join(RES, "data")
PACK = os.path.join(RES, "custom_biomes_pack")
NS = "wayfarers"
V = WB.VANILLA
ID = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_/.-]+$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

ALLOWED_TOP = {"has_precipitation", "temperature", "temperature_modifier", "downfall", "attributes", "effects",
               "spawners", "spawn_costs", "creature_spawn_probability", "carvers", "features"}
ALLOWED_EFFECTS = {"water_color", "foliage_color", "dry_foliage_color", "grass_color", "grass_color_modifier"}
# 26.2 codec fields of the feature types our configured features use (FeatureConfiguration CODECs)
FEATURE_FIELDS = {
    "template": ({"templates"}, set()),
    "simple_block": ({"to_place"}, {"schedule_tick"}),
    "block_blob": ({"state", "can_place_on"}, set()),
    "lake": ({"fluid", "barrier", "can_place_feature", "can_replace_with_air_or_fluid", "can_replace_with_barrier"}, set()),
    "spring_feature": ({"state", "valid_blocks"}, {"requires_block_below", "rock_count", "hole_count"}),
    "fallen_tree": ({"trunk_provider", "log_length", "stump_decorators", "log_decorators"}, set()),
    "vegetation_patch": ({"replaceable", "ground_state", "vegetation_feature", "surface", "depth", "vertical_range",
                          "extra_bottom_block_chance", "extra_edge_column_chance", "vegetation_chance", "xz_radius"}, set()),
}
# placement modifier fields (PlacementModifier CODECs), ours included
PLACEMENT_FIELDS = {
    "minecraft:rarity_filter": {"chance"}, "minecraft:count": {"count"}, "minecraft:in_square": set(),
    "minecraft:heightmap": {"heightmap"}, "minecraft:biome": set(), "minecraft:random_offset": {"xz_spread", "y_spread"},
    "minecraft:surface_water_depth_filter": {"max_water_depth"}, "minecraft:block_predicate_filter": {"predicate"},
    "wayfarers:clear_of_structures": set(),
}
HEIGHTMAPS = {"WORLD_SURFACE_WG", "WORLD_SURFACE", "OCEAN_FLOOR_WG", "OCEAN_FLOOR", "MOTION_BLOCKING",
              "MOTION_BLOCKING_NO_LEAVES"}

errors = []


def err(msg):
    errors.append(msg)


def walk(obj, fn):
    fn(obj)
    if isinstance(obj, dict):
        for v in obj.values():
            walk(v, fn)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, fn)


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        err(f"{os.path.relpath(path, ROOT)}: unreadable ({e})")
        return None


def block_known(name):
    ns, path = name.split(":", 1)
    return path in V["blocks"] if ns == "minecraft" else True   # mod blocks: validate.py checks them


def check_states(obj, where):
    """Every block state "Name" is a plain id of a known block ('minecraft:basalt[axis=y]' does not parse)."""
    def fn(o):
        if isinstance(o, dict) and isinstance(o.get("Name"), str):
            if not ID.match(o["Name"]):
                err(f"{where}: block state Name {o['Name']!r} is not a valid id (properties go in Properties)")
            elif not block_known(o["Name"]):
                err(f"{where}: unknown block {o['Name']}")
    walk(obj, fn)


# ===================================================================================================== pack
def check_pack():
    if not os.path.isdir(PACK):
        err("custom_biomes_pack missing (run tools/gen_world.py)")
        return None
    meta = load(os.path.join(PACK, "pack.mcmeta")) or {}
    pack = meta.get("pack", {})
    if not isinstance(pack.get("description"), str) or not (pack.get("min_format", 999) <= 107 <= pack.get("max_format", 0)):
        err("custom_biomes_pack/pack.mcmeta: needs a plain description and a format range covering 107 (data 26.2)")
    data_files = sorted(os.path.relpath(p, PACK) for p in glob.glob(os.path.join(PACK, "data", "**", "*.*"), recursive=True))
    expected = [os.path.join("data", "minecraft", "worldgen", "world_preset", "normal.json")]
    if data_files != expected:
        err(f"custom_biomes_pack holds {data_files}, expected only {expected} (the Default world preset)")
    preset = load(os.path.join(PACK, *expected[0].split(os.sep)))
    settings = load(os.path.join(DATA, NS, "worldgen", "noise_settings", "overworld.json"))
    if preset is None or settings is None:
        return None
    vdims = V["world_preset_normal"]["dimensions"]
    dims = preset.get("dimensions", {})
    if set(preset) != {"dimensions"} or set(dims) != set(vdims):
        err("world preset: must hold vanilla's three dimensions and nothing else")
    for k in vdims:
        if k != "minecraft:overworld" and dims.get(k) != vdims[k]:
            err(f"world preset: {k} differs from vanilla's")
    over = dims.get("minecraft:overworld", {})
    if over.get("type") != "minecraft:overworld":
        err("world preset: the Overworld's type must stay minecraft:overworld (no dimension_type change)")
    gen = over.get("generator", {})
    if gen.get("type") != "minecraft:noise" or gen.get("settings") != f"{NS}:overworld" \
            or set(gen) != {"type", "settings", "biome_source"}:
        err(f"world preset: the Overworld generator must be minecraft:noise with settings {NS}:overworld")
    # noise settings: vanilla's, but for the surface rule
    vanilla = V["noise_settings_overworld"]
    for k in set(vanilla) | set(settings):
        if k != "surface_rule" and settings.get(k) != vanilla.get(k):
            err(f"noise settings: {k} differs from vanilla minecraft:overworld (only the surface rule may change)")
    check_surface(settings.get("surface_rule", {}), vanilla["surface_rule"])
    check_states(settings, "noise settings")
    src = gen.get("biome_source", {})
    if src.get("type") != "minecraft:multi_noise" or not isinstance(src.get("biomes"), list):
        err("world preset: the Overworld biome_source must be a minecraft:multi_noise list")
        return None
    return src["biomes"]


def check_surface(rule, vanilla):
    """Vanilla's rule with exactly one rule put first in its above_preliminary_surface branch: a test on our
    biomes."""
    try:
        seq, vseq = rule["sequence"], vanilla["sequence"]
        branch = next(i for i, e in enumerate(vseq) if e.get("if_true", {}).get("type") == "minecraft:above_preliminary_surface")
        ours = seq[branch]["then_run"]["sequence"]
        theirs = vseq[branch]["then_run"]["sequence"]
    except (KeyError, StopIteration, TypeError):
        err("noise settings: surface rule does not follow vanilla's layout")
        return
    if len(seq) != len(vseq) or any(seq[i] != vseq[i] for i in range(len(seq)) if i != branch):
        err("noise settings: surface rule changes vanilla outside the above_preliminary_surface branch")
    if ours[1:] != theirs:
        err("noise settings: the above_preliminary_surface branch must be vanilla's with one rule in front")
        return
    head = ours[0]
    test = head.get("if_true", {})
    want = sorted(f"{NS}:{b}" for b in WB.BIOMES)
    if head.get("type") != "minecraft:condition" or test.get("type") != "minecraft:biome" or sorted(test.get("biome_is", [])) != want:
        err(f"noise settings: the added surface rule must sit behind one biome test on {want}")
    noises = set(V["noises"])

    def fn(o):
        if isinstance(o, dict):
            if o.get("type") == "minecraft:noise_threshold" and o.get("noise", "").split(":")[-1] not in noises:
                err(f"surface rule: unknown noise {o.get('noise')}")
            if o.get("type") == "minecraft:biome":
                for b in o.get("biome_is", []):
                    if b.split(":")[1] not in WB.BIOMES:
                        err(f"surface rule: names unknown biome {b}")
    walk(head, fn)
    # cheap: a handful of conditions per biome, no long chains
    count = [0]
    walk(head, lambda o: count.__setitem__(0, count[0] + (isinstance(o, dict) and o.get("type") == "minecraft:condition")))
    if count[0] > 12 * len(WB.BIOMES):
        err(f"surface rule: {count[0]} conditions for {len(WB.BIOMES)} biomes (keep it cheap)")


def _quant(v):
    """Climate.quantizeCoord as the game does it: (long) (float * 10000F), in float32."""
    import struct
    f = struct.unpack("f", struct.pack("f", float(v)))[0]
    p = struct.unpack("f", struct.pack("f", f * 10000.0))[0]
    return int(p)          # truncation toward zero, like the Java cast


def check_climate(points):
    ours_ids = {f"{NS}:{b}" for b in WB.BIOMES}
    vanilla_biomes = set(V["overworld_biomes"])
    expected, _counts = WB.climate_points()
    if points != expected:
        err("dimension: biome list differs from tools/wf/worldbiomes.py climate_points() (run tools/gen_world.py)")
    used = set()
    boxes = []
    for i, p in enumerate(points):
        b = p.get("biome", "")
        used.add(b)
        if b not in ours_ids and b.split(":")[-1] not in vanilla_biomes:
            err(f"dimension point {i}: unknown biome {b}")
        par = p.get("parameters", {})
        if set(par) != set(WB.AXES) | {"offset"}:
            err(f"dimension point {i}: parameters {sorted(par)}")
            continue
        box = {}
        for a in WB.AXES:
            lo, hi = par[a]
            if not (-2.0 <= lo <= hi <= 2.0):
                err(f"dimension point {i}: {a} {par[a]} out of order or range")
            box[a] = (_quant(lo), _quant(hi))
        boxes.append((b, box, _quant(par["offset"])))
    for b in ours_ids - used:
        err(f"biome {b} is never placed")
    if len(points) > len(WB.vanilla_points()) * 1.02:
        err(f"dimension: {len(points)} climate points, more than 2 % over vanilla's {len(WB.vanilla_points())}")
    # every value reads back as intended: walking the list in order, the pieces of each vanilla cell (its own biome
    # or one of ours carved from it) sit inside it and fill it exactly
    vanilla = WB.vanilla_points()
    parent_of = {f"{NS}:{bid}": set(b["parent"][0]) for bid, b in WB.BIOMES.items()}

    def vol(box):
        out = 1
        for a in WB.AXES:
            out *= max(box[a][1] - box[a][0], 1) if box[a][1] > box[a][0] else 1
        return out
    k = 0
    for vb, vbox, voff in vanilla:
        filled = 0
        while filled < vol(vbox) and k < len(boxes):
            b, box, off = boxes[k]
            inside = all(vbox[a][0] <= box[a][0] <= box[a][1] <= vbox[a][1] for a in WB.AXES)
            if off != voff or not inside or (b.split(":")[-1] != vb and vb not in parent_of.get(b, set())):
                break
            filled += vol(box)
            k += 1
        if filled != vol(vbox):
            err(f"dimension: vanilla cell of {vb} {vbox} not rebuilt exactly (point {k}: values that do not read back "
                f"as intended, or a stray piece)")
            break
    if k != len(boxes) and not errors:
        err(f"dimension: {len(boxes) - k} climate points left over after vanilla's cells")
    # brute-force nearest biome on random climates: vanilla's answer outside our slices, the parent's inside

    def nearest(cands, t):
        best, bd = None, None
        for b, box, off in cands:
            d = off * off
            for a in WB.AXES:
                lo, hi = box[a]
                v = t[a]
                e = lo - v if v < lo else v - hi if v > hi else 0
                d += e * e
                if bd is not None and d >= bd:
                    break
            if bd is None or d < bd:
                best, bd = b, d
        return best

    rng = random.Random(7)
    van = [(b, box, off) for b, box, off in vanilla]
    parent_boxes = [box for b, box, _o in vanilla if any(b in ps for ps in parent_of.values()) and box["depth"][0] == 0]
    bad = 0
    for k in range(300):
        if k % 2:      # half anywhere, half inside a parent cell (around and inside our slices)
            t = {a: rng.randint(-10000, 10000) for a in WB.AXES}
        else:
            box = rng.choice(parent_boxes)
            t = {a: rng.randint(max(box[a][0], -10000), min(box[a][1], 10000)) for a in WB.AXES}
        t["depth"] = 0
        mine, theirs = nearest(boxes, t), nearest(van, t)
        if mine.split(":")[-1] != theirs and theirs not in parent_of.get(mine, set()):
            bad += 1
            if bad <= 3:
                err(f"climate {t}: our list gives {mine}, vanilla {theirs}")
    if bad:
        err(f"climate: {bad} of 300 random climates give another biome than vanilla's (or its slice)")


# ===================================================================================================== biomes
def placed_ids():
    out = {f"minecraft:{p}" for p in V["placed_features"]}
    root = os.path.join(DATA, NS, "worldgen", "placed_feature")
    for p in glob.glob(os.path.join(root, "**", "*.json"), recursive=True):
        out.add(f"{NS}:" + os.path.relpath(p, root)[:-5].replace(os.sep, "/"))
    return out


def configured_ids():
    out = {f"minecraft:{p}" for p in V["configured_features"]}
    root = os.path.join(DATA, NS, "worldgen", "configured_feature")
    for p in glob.glob(os.path.join(root, "**", "*.json"), recursive=True):
        out.add(f"{NS}:" + os.path.relpath(p, root)[:-5].replace(os.sep, "/"))
    return out


def check_biomes():
    placed = placed_ids()
    attrs = {f"minecraft:{a}" for a in V["environment_attributes"]}
    particles = {f"minecraft:{p}" for p in V["particle_types"]}
    sounds = {f"minecraft:{s}" for s in V["sound_events"]}
    entities = {f"minecraft:{e}" for e in V["entity_types"]}
    lists = {}
    root = os.path.join(DATA, NS, "worldgen", "biome")
    files = sorted(glob.glob(os.path.join(root, "*.json")))
    if sorted(os.path.basename(f)[:-5] for f in files) != sorted(WB.BIOMES):
        err(f"data/wayfarers/worldgen/biome holds {[os.path.basename(f) for f in files]}, expected {sorted(WB.BIOMES)}")
    for path in files:
        bid = f"{NS}:{os.path.basename(path)[:-5]}"
        b = load(path)
        if b is None:
            continue
        for k in b:
            if k not in ALLOWED_TOP:
                err(f"{bid}: unknown key {k}")
        for k in ("has_precipitation", "temperature", "downfall", "effects", "carvers", "features", "spawners"):
            if k not in b:
                err(f"{bid}: missing {k}")
        for k, v in b.get("effects", {}).items():
            if k not in ALLOWED_EFFECTS:
                err(f"{bid}: effects.{k} not allowed")
            elif k.endswith("color") and not COLOR.match(v):
                err(f"{bid}: bad colour {k}={v}")
        for k, v in b.get("attributes", {}).items():
            if k not in attrs:
                err(f"{bid}: unknown attribute {k}")
            if k.endswith("_color") and isinstance(v, str) and not COLOR.match(v):
                err(f"{bid}: bad colour {k}={v}")
            if k == "minecraft:visual/ambient_particles":
                for e in v:
                    if e["particle"]["type"] not in particles or not 0 < e["probability"] <= 0.05:
                        err(f"{bid}: ambient particle {e} unknown or too dense")
            if k == "minecraft:audio/background_music":
                for e in v.values():
                    if e.get("sound") not in sounds:
                        err(f"{bid}: unknown music {e.get('sound')}")
        if len(b.get("features", [])) != 11:
            err(f"{bid}: needs 11 feature steps")
        for step in b.get("features", []):
            for fid in step:
                if fid not in placed:
                    err(f"{bid}: unknown placed feature {fid}")
        for cat, entries in b.get("spawners", {}).items():
            for e in entries:
                if set(e) != {"type", "weight", "minCount", "maxCount"} or e["type"] not in entities:
                    err(f"{bid}: bad spawner entry {e}")
        lists[bid] = b.get("features", [])
    return lists


def check_feature_order(ours):
    """FeatureSorter: features run in one global order per step, so no two biomes of the dimension may list two
    features in opposite orders (directly or through a chain). Vanilla's overworld biomes and ours, after the Forge
    biome modifiers (applied in id order, each appending to its step)."""
    lists = {f"minecraft:{b}": [list(s) for s in f] for b, f in V["biome_features"].items()}
    lists.update({b: [list(s) for s in f] for b, f in ours.items()})
    tags = json.load(open(os.path.join(ROOT, "tools", "wf", "vanilla_biome_tags.json")))

    def resolve(spec, seen=()):
        specs = spec if isinstance(spec, list) else [spec]
        out = set()
        for s in specs:
            s = s["id"] if isinstance(s, dict) else s
            if s.startswith("#"):
                ns, path = s[1:].split(":")
                if s in seen:
                    continue
                f = os.path.join(DATA, ns, "tags", "worldgen", "biome", path + ".json")
                vals = []
                if ns == "minecraft" and path in tags:
                    vals += [f"minecraft:{b}" for b in tags[path]["biomes"]] + [f"#minecraft:{t}" for t in tags[path]["tags"]]
                if os.path.exists(f):
                    vals += json.load(open(f))["values"]
                out |= resolve(vals, seen + (s,))
            else:
                out.add(s if ":" in s else f"minecraft:{s}")
        return out

    mods = os.path.join(DATA, NS, "forge", "biome_modifier")
    for path in sorted(glob.glob(os.path.join(mods, "*.json"))):
        m = json.load(open(path))
        if m.get("type") not in ("forge:add_features", f"{NS}:toggled_features"):
            continue
        feats = m["features"] if isinstance(m["features"], list) else [m["features"]]
        step = WB.STEPS.index(m["step"])
        for b in resolve(m["biomes"]):
            if b in lists:
                lists[b][step] += [f for f in feats if f not in lists[b][step]]
    for b, steps in lists.items():
        for s in steps:
            if len(s) != len(set(s)):
                err(f"{b}: a feature listed twice in one step")
    # graph of "comes before" over (step, feature), cycle search
    edges = {}
    for b, steps in lists.items():
        flat = [(i, f) for i, s in enumerate(steps) for f in s]
        for a, c in zip(flat, flat[1:]):
            edges.setdefault(a, set()).add(c)
    state = {}

    def visit(n, stack):
        state[n] = 1
        for m in edges.get(n, ()):
            if state.get(m) == 1:
                err(f"feature order cycle: {' -> '.join(f for _s, f in stack[stack.index(m):] + [m]) if m in stack else m}")
                return True
            if state.get(m) is None and visit(m, stack + [m]):
                return True
        state[n] = 2
        return False
    sys.setrecursionlimit(10000)
    for n in list(edges):
        if state.get(n) is None and visit(n, [n]):
            break


# ===================================================================================================== features
def check_features():
    configured = configured_ids()
    pm_types = {f"minecraft:{t}" for t in V["placement_modifier_types"]} | {"wayfarers:clear_of_structures"}
    bp_types = {f"minecraft:{t}" for t in V["block_predicate_types"]}
    templates = set()
    root = os.path.join(DATA, NS, "structure")
    for p in glob.glob(os.path.join(root, "**", "*.nbt"), recursive=True):
        templates.add(f"{NS}:" + os.path.relpath(p, root)[:-4].replace(os.sep, "/"))
    for kind in ("configured_feature", "placed_feature"):
        for path in sorted(glob.glob(os.path.join(DATA, NS, "worldgen", kind, "world", "*.json"))):
            rel = os.path.relpath(path, DATA)
            obj = load(path)
            if obj is None:
                continue
            check_states(obj, rel)

            def fn(o, rel=rel):
                if not isinstance(o, dict):
                    return
                t = o.get("type")
                if t == "minecraft:random_offset":
                    for k in ("xz_spread", "y_spread"):
                        v = o.get(k)
                        if isinstance(v, int) and abs(v) > 16:
                            err(f"{rel}: random_offset {k} {v} outside -16..16")
                if isinstance(o.get("offset"), list) and any(abs(v) > 15 for v in o["offset"]):
                    err(f"{rel}: block predicate offset {o['offset']} outside -15..15")
                if isinstance(t, str) and "predicate" in o and isinstance(o["predicate"], dict):
                    pt = o["predicate"].get("type")
                    if pt not in bp_types:
                        err(f"{rel}: unknown block predicate {pt}")
            walk(obj, fn)
            if kind == "configured_feature":
                check_configured(rel, obj, templates)
            else:
                feat = obj.get("feature")
                if isinstance(feat, str) and feat not in configured:
                    err(f"{rel}: unknown configured feature {feat}")
                elif isinstance(feat, dict):
                    check_configured(rel, feat, templates)
                for m in obj.get("placement", []):
                    t = m.get("type")
                    if t not in pm_types:
                        err(f"{rel}: unknown placement modifier {t}")
                    elif t in PLACEMENT_FIELDS and set(m) - {"type"} != PLACEMENT_FIELDS[t]:
                        err(f"{rel}: {t} has fields {sorted(set(m) - {'type'})}, expected {sorted(PLACEMENT_FIELDS[t])}")
                    if t == "minecraft:heightmap" and m.get("heightmap") not in HEIGHTMAPS:
                        err(f"{rel}: unknown heightmap {m.get('heightmap')}")
                    if t == "minecraft:rarity_filter" and not (isinstance(m.get("chance"), int) and m["chance"] >= 1):
                        err(f"{rel}: rarity_filter chance must be a positive int")
                types = [m.get("type") for m in obj.get("placement", [])]
                if "wayfarers:clear_of_structures" in types and types.index("wayfarers:clear_of_structures") > 1:
                    err(f"{rel}: clear_of_structures belongs right after the rarity filter (it reads the chunk)")


def check_configured(rel, cf, templates):
    t = cf.get("type", "").split(":")[-1]
    if f"minecraft:{t}" != cf.get("type") or t not in V["features"]:
        err(f"{rel}: unknown feature type {cf.get('type')}")
        return
    if t in FEATURE_FIELDS:
        need, optional = FEATURE_FIELDS[t]
        keys = set(cf.get("config", {}))
        if not need <= keys or keys - need - optional:
            err(f"{rel}: {t} config has {sorted(keys)}, expected {sorted(need)} (+ optional {sorted(optional)})")
    else:
        err(f"{rel}: feature type {t} has no field table in validate_world.py FEATURE_FIELDS")
    if t == "template":
        for e in cf["config"]["templates"]:
            if set(e) != {"data", "weight"} or e["data"].get("id") not in templates:
                err(f"{rel}: template entry {e} unknown or malformed")
            elif e["data"]["id"].startswith(f"{NS}:worldobjects/"):
                kind = e["data"]["id"].split("/")[-1].rsplit("_", 1)[0]
                if kind not in worldobjects.VARIANTS:
                    err(f"{rel}: template {e['data']['id']} is not a world object")
    if t == "vegetation_patch":
        check_configured(rel + " vegetation_feature", cf["config"]["vegetation_feature"]["feature"], templates)


# ===================================================================================================== modifiers, lang
def java_toggles():
    text = open(os.path.join(ROOT, "src", "main", "java", "com", "wayfarers", "config", "WayfarersConfig.java"),
                encoding="utf-8").read()
    return set(re.findall(r'\.define\("world\.terrain\.(\w+)"', text)), set(re.findall(r'case "(\w+)" ->', text))


def check_modifiers():
    defined, switched = java_toggles()
    placed = placed_ids()
    found = set()
    for path in sorted(glob.glob(os.path.join(DATA, NS, "forge", "biome_modifier", "terrain_*.json"))):
        rel = os.path.relpath(path, DATA)
        m = load(path)
        if m is None:
            continue
        if m.get("type") != f"{NS}:toggled_features" or set(m) != {"type", "toggle", "biomes", "features", "step"}:
            err(f"{rel}: must be a {NS}:toggled_features with toggle, biomes, features, step")
            continue
        found.add(m["toggle"])
        if m["toggle"] not in defined or m["toggle"] not in switched:
            err(f"{rel}: toggle {m['toggle']} is not a world.terrain.* option of WayfarersConfig (terrainTouch)")
        for b in m["biomes"]:
            if b.split(":")[-1] not in V["overworld_biomes"] or not b.startswith("minecraft:"):
                err(f"{rel}: biome {b} is not a vanilla overworld biome (our biomes decorate themselves)")
        feats = m["features"] if isinstance(m["features"], list) else [m["features"]]
        for f in feats:
            if f not in placed:
                err(f"{rel}: unknown placed feature {f}")
        if m["step"] not in WB.STEPS:
            err(f"{rel}: unknown step {m['step']}")
    if found != set(WB.TOUCHES) or defined != set(WB.TOUCHES):
        err(f"terrain toggles: modifiers {sorted(found)}, config {sorted(defined)}, worldbiomes {sorted(WB.TOUCHES)} differ")


def check_lang():
    for lang in ("en_us", "fr_fr"):
        path = os.path.join(RES, "assets", NS, "lang", f"{lang}.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding="utf-8"))
        for bid in WB.BIOMES:
            if f"biome.{NS}.{bid}" not in d:
                err(f"{lang}: no name for biome {bid} (run tools/gen_assets.py)")
        if "pack.wayfarers.custom_biomes" not in d:
            err(f"{lang}: no name for the custom_biomes pack")


def check(report=None):
    """All checks; returns the error list (validate.py adds them to its own)."""
    del errors[:]
    points = check_pack()
    if points is not None:
        check_climate(points)
    ours = check_biomes()
    check_feature_order(ours)
    check_features()
    check_modifiers()
    check_lang()
    return list(errors)


def main():
    found = check()
    for e in found[:100]:
        print("ERROR:", e)
    print(f"world: {len(WB.BIOMES)} biomes, {len(WB.FEATURES)} features, {len(found)} errors")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
