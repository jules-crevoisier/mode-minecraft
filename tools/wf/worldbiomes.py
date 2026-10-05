"""The Wayfarers biomes and terrain touches (tools/gen_world.py writes them, tools/validate_world.py checks them).

Cheap by design: Minecraft's own terrain is kept as it is (vanilla noise router, density functions, dimension
type). Three biomes take a slice of the climate cells of a vanilla biome (BIOMES[...]["slice"]): the Overworld of the
Default world preset uses vanilla's own parameter list (world_points.json, dumped from OverworldBiomeBuilder 26.2)
with those cells split, so the biome lookup costs the same. Their ground comes from a few surface rules put in front of vanilla's,
behind one biome test (a chunk without our biomes skips them: SurfaceRules prunes biome tests against the chunk's
possible biomes). Their decoration is the parent biome's own list (same relative order, so no feature order cycle)
minus a few plants, plus a handful of our features with rarity filters.

The terrain touches (TOUCHES) add cheap features to vanilla biomes through Forge biome modifiers
(wayfarers:toggled_features, one config option world.terrain.<toggle> each): boulders, fallen logs, rock spires,
wildflower patches, moss carpets, hot springs.
"""
import json
import os

from . import worldobjects

NS = "wayfarers"
HERE = os.path.dirname(os.path.abspath(__file__))
VANILLA = json.load(open(os.path.join(HERE, "..", "data", "vanilla_worldgen_26.2.json")))
POINTS_FILE = os.path.join(HERE, "world_points.json")

STEPS = ["raw_generation", "lakes", "local_modifications", "underground_structures", "surface_structures",
         "strongholds", "underground_ores", "underground_decoration", "fluid_springs", "vegetal_decoration",
         "top_layer_modification"]
AXES = ("temperature", "humidity", "continentalness", "erosion", "depth", "weirdness")


# ===================================================================================================== biomes
def B(en, fr, parent, slice_, sky, fog, water, water_fog, grass=None, foliage=None, music=None, particles=None,
      particle_rate=0.0, fog_end=None, drop=(), add=(), where_en="", where_fr="", text_en="", text_fr=""):
    return dict(en=en, fr=fr, parent=parent, slice=slice_, sky=sky, fog=fog, water=water, water_fog=water_fog,
                grass=grass, foliage=foliage, music=music, particles=particles, particle_rate=particle_rate,
                fog_end=fog_end, drop=list(drop), add=list(add), where_en=where_en, where_fr=where_fr,
                text_en=text_en, text_fr=text_fr)


# id -> design. parent: (vanilla biomes whose cells are sliced, template biome for decoration, mobs and music);
# slice: {axis: (lo, hi)}, the part of each parent cell that becomes ours; drop: parent features left out;
# add: our features (FEATURES keys)
BIOMES = {
    "crimson_mire": B(
        "Crimson Mire", "Marais pourpre", (["swamp"], "swamp"), {"humidity": (0.1, 1.0)},
        sky="#b49494", fog="#d2b8b2", water="#6b2b33", water_fog="#2a0c10", grass="#8e4038", foliage="#7a2c2c",
        music="minecraft:music.overworld.swamp", particles="minecraft:crimson_spore", particle_rate=0.008,
        fog_end=112.0,
        drop=["minecraft:trees_swamp", "minecraft:flower_swamp", "minecraft:patch_pumpkin"],
        add=["mire_thorns", "mire_giant_mushrooms", "mire_crimson_roots", "mire_red_mushrooms"],
        where_en="the wettest swamps (about two swamps in five).",
        where_fr="les marais les plus humides (environ deux marais sur cinq).",
        text_en="A blood-red marsh under a rosy haze: crimson nylium, mud and podzol, dark red water and drifting "
                "spores. Curved horns of blackstone rise from the mud, and giant red mushrooms with weeping vines "
                "shade the pools. Witches, slimes and the Bogged live here like in any swamp.",
        text_fr="Un marais rouge sang sous une brume rosée : nylium pourpre, boue et podzol, eau rouge sombre et "
                "spores qui flottent. Des cornes recourbées de pierre noire sortent de la boue, et des champignons "
                "rouges géants aux lianes pleureuses ombragent les mares. Sorcières, slimes et Embourbés y vivent "
                "comme dans tout marais."),
    "volcanic_highlands": B(
        "Volcanic Highlands", "Hautes terres volcaniques", (["badlands", "wooded_badlands"], "badlands"),
        {"erosion": (-1.0, -0.375), "weirdness": (0.0, 1.0)},
        sky="#c09878", fog="#a8826a", water="#b0603a", water_fog="#3a1a0a", grass="#bba86a", foliage="#d4782a",
        music="minecraft:music.overworld.badlands", particles="minecraft:ash", particle_rate=0.006,
        fog_end=192.0,
        drop=["minecraft:patch_cactus_decorated", "minecraft:patch_sugar_cane_badlands", "minecraft:patch_pumpkin",
              "minecraft:trees_badlands"],
        add=["volcanic_lava_pools", "volcanic_boulders", "volcanic_lava_springs", "volcanic_rustwoods",
             "volcanic_smoke_vents"],
        where_en="half of the mountain ranges of the badlands.",
        where_fr="la moitié des massifs montagneux des badlands.",
        text_en="Ochre mountains banded with terracotta under an ashen sky. Black rock and glowing magma break "
                "through the tan grass, lava pools steam in the hollows and lava trickles down the slopes. Smoke "
                "rises from vents, and a few Rustwoods cling to the ground. Watch your step.",
        text_fr="Des montagnes ocre striées de terre cuite sous un ciel de cendre. La roche noire et le magma "
                "percent l'herbe fauve, des mares de lave fument dans les creux et la lave ruisselle sur les "
                "pentes. Des évents crachent de la fumée, et quelques bois rouillés s'accrochent au sol. Regarde "
                "où tu marches."),
    "pale_dunes": B(
        "Pale Dunes", "Dunes pâles", (["desert"], "desert"), {"humidity": (-1.0, -0.35)},
        sky="#9cc0ff", fog="#f0e6d4", water="#3fa0a8", water_fog="#0a3a3e",
        music="minecraft:music.overworld.desert", fog_end=None,
        add=["pale_hoodoos"],
        where_en="the driest deserts (about one desert in four).",
        where_fr="les déserts les plus arides (environ un désert sur quatre).",
        text_en="A white desert of pale sand rippled with gold, smooth sandstone underneath. Banded terracotta "
                "hoodoos stand like chimneys between the dunes, some with a sandstone cap. Husks, camels and "
                "desert villages are at home here too.",
        text_fr="Un désert blanc de sable pâle strié d'or, du grès lisse en dessous. Des cheminées de fée de terre "
                "cuite rayée se dressent entre les dunes, certaines coiffées de grès. Zombies momifiés, dromadaires "
                "et villages du désert y sont chez eux aussi."),
}


# ===================================================================================================== climate
def _q(v):
    """A climate value as the game stores it (Climate.quantizeCoord: 1/10000 steps)."""
    return int(round(v * 10000))


def _enc(q):
    """A quantized value written so that the game reads back exactly q: (long) (float * 10000F) truncates toward
    zero, so the value is nudged half a step away from zero (q / 10000 itself can land a hair short, on q - 1)."""
    if q == 0:
        return 0.0
    return (q + (0.5 if q > 0 else -0.5)) / 10000.0


def vanilla_points():
    """[(biome, {axis: (lo, hi)} in quantized steps, offset)] in OverworldBiomeBuilder's order."""
    out = []
    for row in json.load(open(POINTS_FILE)):
        b, rest, offset = row[0], row[1:7], row[7]
        out.append((b, {a: (_q(r[0]), _q(r[1])) for a, r in zip(AXES, rest)}, _q(offset)))
    return out


def _carve(box, cut):
    """Splits `box` by the slice `cut` (both {axis: (lo, hi)}): (inside or None, [outside boxes])."""
    inside = dict(box)
    for a, (lo, hi) in cut.items():
        blo, bhi = box[a]
        if bhi <= lo or blo >= hi:
            return None, [box]
        inside[a] = (max(blo, lo), min(bhi, hi))
    outside = []
    rest = dict(box)
    for a, (lo, hi) in cut.items():        # peel the parts below and above the slice, axis by axis
        blo, bhi = rest[a]
        if blo < lo:
            outside.append(dict(rest, **{a: (blo, lo)}))
        if bhi > hi:
            outside.append(dict(rest, **{a: (hi, bhi)}))
        rest[a] = (max(blo, lo), min(bhi, hi))
    return inside, outside


def climate_points():
    """The overworld's multi_noise list: vanilla's points, the parent cells of our biomes carved by their slices.
    Returns ([{"biome", "parameters"}], {biome: number of points})."""
    rules = []
    for bid, b in BIOMES.items():
        cut = {a: (_q(lo), _q(hi)) for a, (lo, hi) in b["slice"].items()}
        rules.append((set(b["parent"][0]), cut, bid))
    out, counts = [], {}

    def emit(biome, box, offset):
        params = {a: [_enc(box[a][0]), _enc(box[a][1])] for a in AXES}
        params["offset"] = _enc(offset)
        out.append({"biome": biome if ":" in biome else f"minecraft:{biome}", "parameters": params})
        counts[biome] = counts.get(biome, 0) + 1

    for b, box, offset in vanilla_points():
        pieces = [(b, box)]
        for parents, cut, ours in rules:
            if b in parents:
                inside, outside = _carve(box, cut)
                if inside is not None:
                    pieces = [(b, o) for o in outside] + [(f"{NS}:{ours}", inside)]
                break
        for biome, bx in pieces:
            emit(biome, bx, offset)
    return out, counts


# ===================================================================================================== surface
def _block(name, props=None):
    state = {"Name": name if ":" in name else f"minecraft:{name}"}
    if props:
        state["Properties"] = props
    return {"type": "minecraft:block", "result_state": state}


def _if(cond, then):
    return {"type": "minecraft:condition", "if_true": cond, "then_run": then}


def _seq(*rules):
    return {"type": "minecraft:sequence", "sequence": list(rules)}


def _noise(nid, lo, hi):
    return {"type": "minecraft:noise_threshold", "noise": f"minecraft:{nid}", "min_threshold": lo, "max_threshold": hi}


def _depth(add=False, secondary=0):
    return {"type": "minecraft:stone_depth", "offset": 0, "add_surface_depth": add, "secondary_depth_range": secondary,
            "surface_type": "floor"}


def _biome(*ids):
    return {"type": "minecraft:biome", "biome_is": [f"{NS}:{i}" for i in ids]}


ON_FLOOR = _depth()
UNDER_FLOOR = _depth(add=True)
DEEP_UNDER_FLOOR = _depth(add=True, secondary=6)
ABOVE_WATER = {"type": "minecraft:water", "offset": -1, "surface_depth_multiplier": 0, "add_stone_depth": False}
STEEP = {"type": "minecraft:steep"}
GRASS = _block("grass_block", {"snowy": "false"})
BANDLANDS = {"type": "minecraft:bandlands"}

# each biome's ground: a few conditions, no y-band chains (the volcanic bands come from vanilla's bandlands rule,
# a table lookup)
SURFACES = {
    # nylium and mud patches over mud, podzol here and there, mud under the water
    "crimson_mire": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(ABOVE_WATER, _seq(_if(_noise("surface", 0.05, 1.0), _block("crimson_nylium")),
                                                 _if(_noise("surface_swamp", 0.0, 1.0), _block("mud")),
                                                 _if(_noise("surface", -1.0, -0.45), _block("podzol", {"snowy": "false"})),
                                                 GRASS)),
                           _block("mud"))),
        _if(UNDER_FLOOR, _block("mud"))),
    # terracotta bands on the slopes and below the ground, blackstone, magma, coarse dirt and tan grass on top
    "volcanic_highlands": lambda: _seq(
        _if(STEEP, BANDLANDS),
        _if(ON_FLOOR, _seq(_if(_noise("surface", -1.0, -0.38), _block("blackstone")),
                           _if(_noise("surface", -0.38, -0.33), _block("magma_block")),
                           _if(_noise("surface", 0.3, 1.0), _block("coarse_dirt")),
                           _if(ABOVE_WATER, GRASS),
                           _block("blackstone"))),
        BANDLANDS),
    # pale sand (white concrete powder) rippled with ordinary sand, smooth sandstone underneath
    "pale_dunes": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(_noise("surface", -0.08, 0.08), _block("sand")),
                           _block("white_concrete_powder"))),
        _if(UNDER_FLOOR, _seq(_if(DEEP_UNDER_FLOOR, _block("smooth_sandstone")), _block("white_concrete_powder")))),
}


def surface_rule(vanilla_rule):
    """Vanilla's overworld rule with ours in front, inside its above_preliminary_surface branch: one biome test,
    then one per biome. Nothing changes for the vanilla biomes."""
    ours = _if(_biome(*BIOMES), _seq(*[_if(_biome(bid), SURFACES[bid]()) for bid in BIOMES]))
    rule = json.loads(json.dumps(vanilla_rule))
    for entry in rule["sequence"]:
        if entry.get("type") == "minecraft:condition" and entry["if_true"].get("type") == "minecraft:above_preliminary_surface":
            inner = entry["then_run"]
            if inner.get("type") != "minecraft:sequence":
                raise ValueError("vanilla surface rule: above_preliminary_surface branch is not a sequence")
            inner["sequence"].insert(0, ours)
            return rule
    raise ValueError("vanilla surface rule: no above_preliminary_surface branch")


def world_preset(points):
    """minecraft:normal, the "Default" world type: vanilla's, but for the Overworld's biome list and settings."""
    preset = json.loads(json.dumps(VANILLA["world_preset_normal"]))
    preset["dimensions"]["minecraft:overworld"]["generator"] = {
        "type": "minecraft:noise", "settings": f"{NS}:overworld",
        "biome_source": {"type": "minecraft:multi_noise", "biomes": points}}
    return preset


def noise_settings():
    """vanilla's minecraft:overworld noise settings, word for word, with our surface rules: wayfarers:overworld."""
    ns = json.loads(json.dumps(VANILLA["noise_settings_overworld"]))
    ns["surface_rule"] = surface_rule(ns["surface_rule"])
    return ns


# ===================================================================================================== features
BIOME_FILTER = {"type": "minecraft:biome"}
# keeps big surface decorations out of the chunks a surface structure reaches (com.wayfarers.world
# .ClearOfStructuresFilter, tag wayfarers:clears_decoration); placed right after the rarity filter, so it runs once
# per lucky chunk
CLEAR = {"type": "wayfarers:clear_of_structures"}


def _state(name, **props):
    st = {"Name": name if ":" in name else f"minecraft:{name}"}
    if props:
        st["Properties"] = {k: str(v).lower() for k, v in props.items()}
    return st


def _simple(state):
    return {"type": "minecraft:simple_block",
            "config": {"to_place": {"type": "minecraft:simple_state_provider", "state": state}}}


def _uniform(lo, hi):
    return {"type": "minecraft:uniform", "min_inclusive": lo, "max_inclusive": hi}


def _trapezoid(m):
    return {"type": "minecraft:trapezoid", "min": -m, "max": m, "plateau": 0}


def _objects(kind):
    """A template feature picking one of the variants of `kind` (wf/worldobjects.py), rotated at random."""
    return {"type": "minecraft:template", "config": {"templates": [
        {"data": {"id": t}, "weight": 1} for t in worldobjects.template_ids(kind)]}}


def _object_placement(rarity, sink):
    return [{"type": "minecraft:rarity_filter", "chance": rarity}, CLEAR, {"type": "minecraft:in_square"},
            {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
            {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
            {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -sink}, BIOME_FILTER]


def _patch(rarity, tries, spread, heightmap="MOTION_BLOCKING"):
    """A patch of plants like vanilla's (26.2 has no random_patch: count + random_offset), one chunk in `rarity`."""
    return [{"type": "minecraft:rarity_filter", "chance": rarity}, {"type": "minecraft:in_square"},
            {"type": "minecraft:heightmap", "heightmap": heightmap}, BIOME_FILTER,
            {"type": "minecraft:count", "count": tries},
            {"type": "minecraft:random_offset", "xz_spread": _trapezoid(spread), "y_spread": _trapezoid(2)},
            {"type": "minecraft:block_predicate_filter",
             "predicate": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}}]


def _on_ground(rarity, heightmap="MOTION_BLOCKING", clear=True):
    return ([{"type": "minecraft:rarity_filter", "chance": rarity}] + ([CLEAR] if clear else [])
            + [{"type": "minecraft:in_square"}, {"type": "minecraft:heightmap", "heightmap": heightmap}, BIOME_FILTER])


def _sapling_ground(rarity, sapling):
    """Dry ground where `sapling` could grow (trees and fallen logs)."""
    return [{"type": "minecraft:rarity_filter", "chance": rarity}, CLEAR, {"type": "minecraft:in_square"},
            {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
            {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
            {"type": "minecraft:block_predicate_filter",
             "predicate": {"type": "minecraft:would_survive", "state": _state(sapling, stage=0)}}, BIOME_FILTER]


def _fallen(log):
    return {"type": "minecraft:fallen_tree", "config": {
        "trunk_provider": {"type": "minecraft:simple_state_provider", "state": _state(log, axis="y")},
        "log_length": _uniform(4, 7), "stump_decorators": [],
        "log_decorators": [{"type": "minecraft:attached_to_logs", "probability": 0.1, "directions": ["up"],
                            "block_provider": {"type": "minecraft:weighted_state_provider", "entries": [
                                {"data": _state("red_mushroom"), "weight": 2},
                                {"data": _state("brown_mushroom"), "weight": 1}]}}]}}


ROCKY = {"type": "minecraft:any_of", "predicates": [
    {"type": "minecraft:matching_block_tag", "tag": t} for t in
    ("minecraft:dirt", "minecraft:terracotta", "minecraft:base_stone_overworld")]
    + [{"type": "minecraft:matching_blocks", "blocks": ["minecraft:coarse_dirt", "minecraft:blackstone",
                                                         "minecraft:magma_block", "minecraft:red_sand"]}]}

# blocks the volcanic lava springs may sit in (the vanilla spring's rock plus the volcanic ground)
SPRING_ROCK = ["minecraft:" + b for b in (
    "stone", "granite", "andesite", "tuff", "blackstone", "coarse_dirt", "dirt", "grass_block", "terracotta",
    "white_terracotta", "brown_terracotta", "orange_terracotta", "red_terracotta", "yellow_terracotta",
    "light_gray_terracotta", "magma_block", "red_sand")]

# id -> (step, configured feature (dict, or the id of an existing one), placement)
FEATURES = {
    # ---- Crimson Mire
    # slim curved blackstone horns, 14-26 blocks tall: one chunk in three
    "mire_thorns": ("surface_structures", _objects("thorn"), _object_placement(3, 2)),
    # giant flat-capped red mushrooms with weeping vines: one chunk in four
    "mire_giant_mushrooms": ("surface_structures", _objects("flat_mushroom"), _object_placement(4, 1)),
    "mire_crimson_roots": ("vegetal_decoration", _simple(_state("crimson_roots")), _patch(2, 16, 5)),
    # red mushrooms on the nylium and the podzol (they grow there in full light)
    "mire_red_mushrooms": ("vegetal_decoration", _simple(_state("red_mushroom")), _patch(3, 12, 5)),
    # ---- Volcanic Highlands
    "volcanic_lava_pools": ("lakes", {"type": "minecraft:lake", "config": {
        "fluid": {"type": "minecraft:simple_state_provider", "state": _state("lava", level=0)},
        "barrier": {"type": "minecraft:simple_state_provider", "state": _state("blackstone")},
        "can_place_feature": {"type": "minecraft:true"},
        "can_replace_with_air_or_fluid": {"type": "minecraft:not", "predicate": {
            "type": "minecraft:matching_block_tag", "tag": "minecraft:features_cannot_replace"}},
        "can_replace_with_barrier": {"type": "minecraft:not", "predicate": {
            "type": "minecraft:matching_block_tag", "tag": "minecraft:lava_pool_stone_cannot_replace"}}}},
        [{"type": "minecraft:rarity_filter", "chance": 14}, CLEAR, {"type": "minecraft:in_square"},
         {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, BIOME_FILTER]),
    "volcanic_boulders": ("local_modifications", {"type": "minecraft:block_blob", "config": {
        "state": _state("blackstone"), "can_place_on": ROCKY}}, _on_ground(3)),
    # a lava spring just under the surface of a slope: a lava trickle runs down the mountainside
    "volcanic_lava_springs": ("fluid_springs", {"type": "minecraft:spring_feature", "config": {
        "state": _state("lava", falling="false"), "requires_block_below": True, "rock_count": 4, "hole_count": 1,
        "valid_blocks": SPRING_ROCK}},
        [{"type": "minecraft:rarity_filter", "chance": 3}, CLEAR, {"type": "minecraft:in_square"},
         {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
         {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -2}, BIOME_FILTER]),
    "volcanic_rustwoods": ("vegetal_decoration", f"{NS}:rustwood_tree", _sapling_ground(5, "acacia_sapling")),
    # smouldering vents: a lit campfire hidden in the ground, smoke rising from the slope
    "volcanic_smoke_vents": ("vegetal_decoration",
                             _simple(_state("campfire", facing="north", lit=True, signal_fire=False, waterlogged=False)),
                             [{"type": "minecraft:rarity_filter", "chance": 4}, CLEAR, {"type": "minecraft:in_square"},
                              {"type": "minecraft:heightmap", "heightmap": "MOTION_BLOCKING"}, BIOME_FILTER,
                              {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
                                  {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"},
                                  {"type": "minecraft:solid", "offset": [0, -1, 0]}]}}]),
    # ---- Pale Dunes
    # banded terracotta hoodoos: one chunk in three
    "pale_hoodoos": ("surface_structures", _objects("hoodoo"), _object_placement(3, 2)),
    # ---- terrain touches in vanilla biomes (TOUCHES)
    "boulders": ("local_modifications", {"type": "minecraft:block_blob", "config": {
        "state": _state("mossy_cobblestone"),
        "can_place_on": {"type": "minecraft:matching_block_tag", "tag": "minecraft:forest_rock_can_place_on"}}},
        _on_ground(8)),
    "fallen_dark_oak_logs": ("vegetal_decoration", _fallen("dark_oak_log"), _sapling_ground(4, "dark_oak_sapling")),
    "fallen_acacia_logs": ("vegetal_decoration", _fallen("acacia_log"), _sapling_ground(6, "acacia_sapling")),
    "fallen_cherry_logs": ("vegetal_decoration", _fallen("cherry_log"), _sapling_ground(5, "cherry_sapling")),
    "rock_spires": ("surface_structures", _objects("rock_spire"), _object_placement(6, 2)),
    "wildflower_patches": ("vegetal_decoration", "minecraft:wildflower", _patch(4, 10, 5)),
    "moss_carpets": ("vegetal_decoration", {"type": "minecraft:vegetation_patch", "config": {
        "replaceable": "#minecraft:moss_replaceable", "ground_state": {"type": "minecraft:simple_state_provider",
                                                                       "state": _state("moss_block")},
        "vegetation_feature": {"feature": _simple(_state("moss_carpet")), "placement": []},
        "surface": "floor", "depth": 1, "vertical_range": 3, "extra_bottom_block_chance": 0.0,
        "extra_edge_column_chance": 0.3, "vegetation_chance": 0.5, "xz_radius": _uniform(2, 4)}},
        _on_ground(5, "MOTION_BLOCKING_NO_LEAVES")),
    "hot_springs": ("surface_structures", _objects("hot_spring"), _object_placement(10, 3)),
}
# terrain touches: toggle (config world.terrain.<toggle>) -> [(feature, vanilla biomes)]
TOUCHES = {
    "boulders": [("boulders", ["plains", "sunflower_plains", "meadow", "forest", "birch_forest", "taiga",
                               "windswept_hills", "windswept_forest"])],
    "fallenLogs": [("fallen_dark_oak_logs", ["dark_forest"]),
                   ("fallen_acacia_logs", ["savanna", "savanna_plateau"]),
                   ("fallen_cherry_logs", ["cherry_grove"])],
    "rockSpires": [("rock_spires", ["stony_peaks", "windswept_hills", "windswept_gravelly_hills", "windswept_forest"])],
    "wildflowers": [("wildflower_patches", ["plains", "sunflower_plains", "forest"])],
    "mossCarpets": [("moss_carpets", ["dark_forest", "old_growth_pine_taiga", "old_growth_spruce_taiga"])],
    "hotSprings": [("hot_springs", ["windswept_savanna", "savanna_plateau"])],
}
TOUCH_TEXT = {
    "boulders": ("Mossy boulders in plains, meadows, forests, taigas and windswept hills.",
                 "Rochers moussus dans les plaines, prairies, forêts, taïgas et collines venteuses."),
    "fallenLogs": ("Fallen logs in dark forests (dark oak), savannas (acacia) and cherry groves.",
                   "Troncs tombés dans les forêts noires (chêne noir), les savanes (acacia) et les cerisaies."),
    "rockSpires": ("Small rock spires in stony peaks and windswept hills.",
                   "Petites aiguilles rocheuses sur les pics pierreux et les collines venteuses."),
    "wildflowers": ("Wildflower patches in plains and forests.",
                    "Tapis de fleurs sauvages dans les plaines et les forêts."),
    "mossCarpets": ("Moss carpets in dark forests and old-growth taigas.",
                    "Tapis de mousse dans les forêts noires et les taïgas anciennes."),
    "hotSprings": ("Hot-spring terraces in windswept savannas and savanna plateaus.",
                   "Sources chaudes en terrasses dans les savanes venteuses et les plateaux de savane."),
}


def fid(name):
    """The id of one of our features (they live under worldgen/*_feature/world/)."""
    return f"{NS}:world/{name}"


def touch_modifiers():
    """{file name: Forge biome modifier}: one wayfarers:toggled_features per feature group."""
    out = {}
    for toggle, groups in TOUCHES.items():
        for name, biomes in groups:
            out[f"terrain_{name}"] = {"type": f"{NS}:toggled_features", "toggle": toggle,
                                     "biomes": [f"minecraft:{b}" for b in biomes], "features": fid(name),
                                     "step": FEATURES[name][0]}
    return out


def biome_json(bid):
    b = BIOMES[bid]
    parent = VANILLA["biomes"][b["parent"][1]]
    attributes = dict(parent["attributes"])
    attributes["minecraft:visual/sky_color"] = b["sky"]
    attributes["minecraft:visual/fog_color"] = b["fog"]
    attributes["minecraft:visual/water_fog_color"] = b["water_fog"]
    if b["music"]:
        attributes["minecraft:audio/background_music"] = {
            "default": {"sound": b["music"], "min_delay": 12000, "max_delay": 24000}}
    if b["particles"]:
        attributes["minecraft:visual/ambient_particles"] = [{"particle": {"type": b["particles"]},
                                                             "probability": b["particle_rate"]}]
    if b["fog_end"]:
        attributes["minecraft:visual/fog_end_distance"] = b["fog_end"]
    effects = {k: v for k, v in parent["effects"].items() if k not in ("grass_color_modifier",)}
    effects["water_color"] = b["water"]
    if b["grass"]:
        effects["grass_color"] = b["grass"]
    if b["foliage"]:
        effects["foliage_color"] = b["foliage"]
    features = [[f for f in step if f not in b["drop"]] for step in parent["features"]]
    for name in b["add"]:
        features[STEPS.index(FEATURES[name][0])].append(fid(name))
    return {
        "has_precipitation": parent["has_precipitation"],
        "temperature": parent["temperature"],
        "downfall": parent["downfall"],
        "attributes": dict(sorted(attributes.items())),
        "effects": dict(sorted(effects.items())),
        "carvers": parent["carvers"],
        "features": features,
        "spawners": parent["spawners"],
        "spawn_costs": parent.get("spawn_costs", {}),
    }


def feature_files():
    """{"configured_feature/<id>": json, "placed_feature/<id>": json} for FEATURES."""
    out = {}
    for name, (_step, configured, placement) in FEATURES.items():
        if isinstance(configured, str):
            out[f"placed_feature/{name}"] = {"feature": configured, "placement": placement}
        else:
            out[f"configured_feature/{name}"] = configured
            out[f"placed_feature/{name}"] = {"feature": fid(name), "placement": placement}
    return out


def lang():
    en, fr = {}, {}
    for bid, b in BIOMES.items():
        en[f"biome.{NS}.{bid}"], fr[f"biome.{NS}.{bid}"] = b["en"], b["fr"]
    en["pack.wayfarers.custom_biomes"] = "Wayfarers: Crimson Mire, Volcanic Highlands and Pale Dunes"
    fr["pack.wayfarers.custom_biomes"] = "Wayfarers : Marais pourpre, Hautes terres volcaniques et Dunes pâles"
    return en, fr
