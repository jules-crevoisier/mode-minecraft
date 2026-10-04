"""Decoration, mobs and music for the world-overhaul biomes (wf/biomes.py).

Every biome's feature list is cut from one global order per generation step (MASTER), merged from vanilla's own
biome lists (vanilla_biome_templates.json, extracted from the 26.2 sources). This keeps the relative order of
features the same in every biome, which the game requires ("Feature order cycle found" otherwise).
"""
import json
import os

HERE = os.path.dirname(__file__)
TEMPLATES = json.load(open(os.path.join(HERE, "vanilla_biome_templates.json")))
STEPS = 11


def _mc(ids):
    return [i if ":" in i else f"minecraft:{i}" for i in ids]


# decoration groups: our design names -> placed features (vanilla for now; ours are added to the same groups)
DECOR = {k: _mc(v) for k, v in {
    "icebergs": ["iceberg_packed", "iceberg_blue", "blue_ice"],
    "ocean_floor_cold": ["seagrass_cold"],
    "kelp_cold": ["kelp_cold"],
    "seagrass_deep": ["seagrass_deep"],
    "ocean_floor": ["seagrass_normal"],
    "kelp": ["kelp_cold"],
    "warm_ocean_vegetation": ["warm_ocean_vegetation"],
    "seagrass_warm": ["seagrass_warm"],
    "sea_pickles": ["sea_pickle"],
    "giant_glowcaps": ["mushroom_island_vegetation"],
    "mushrooms_dense": ["brown_mushroom_old_growth", "red_mushroom_old_growth"],
    "glow_lichen": ["glow_lichen"],
    "palms": ["jungle_bush"],
    "beach_grass": ["patch_grass_badlands"],
    "frost_rocks": ["forest_rock"],
    "basalt_columns": ["wayfarers:basalt_columns"],
    "sea_stacks": ["forest_rock"],
    "river_reeds": ["patch_sugar_cane"],
    "river_crystals": ["wayfarers:river_crystals"],
    "seagrass": ["seagrass_river"],
    "snowy_spruces_sparse": ["trees_snowy"],
    "ice_spires": ["ice_spike", "ice_patch"],
    "blue_ice_chunks": ["blue_ice"],
    "frost_pines": ["trees_grove"],
    "berry_bushes": ["patch_berry_common"],
    "frost_pines_sparse": ["wayfarers:frost_pines_sparse"],
    "ice_spires_small": ["ice_patch"],
    "calcite_veins": ["wayfarers:calcite_veins"],
    "meadow_flowers": ["flower_meadow", "wildflowers_meadow"],
    "lone_oaks": ["trees_plains"],
    "tall_grass": ["patch_tall_grass_2", "patch_grass_plain"],
    "wildflowers": ["flower_flower_forest", "patch_sunflower", "wildflowers_birch_forest"],
    "bee_trees": ["trees_plains"],
    "boulders": ["forest_rock"],
    "glowwood_trees": ["wayfarers:glowwood", "trees_flower_forest"],
    "glowwood_sparse": ["wayfarers:glowwood_sparse"],
    "glow_flowers": ["flower_flower_forest"],
    "great_oaks": ["trees_birch_and_oak_leaf_litter", "fallen_oak_tree"],
    "forest_floor": ["forest_flowers", "patch_grass_forest", "patch_leaf_litter"],
    "tall_birches": ["birch_tall", "fallen_super_birch_tree"],
    "surface_crystals": ["wayfarers:surface_crystals"],
    "shadow_oaks": ["dark_forest_vegetation"],
    "pines": ["trees_taiga", "fallen_spruce_tree"],
    "giant_trees": ["wayfarers:giant_spruce", "trees_old_growth_spruce_taiga"],
    "ferns": ["patch_large_fern", "patch_grass_taiga"],
    "mossy_boulders": ["forest_rock"],
    "great_cherries": ["trees_cherry"],
    "pink_petals": ["flower_cherry"],
    "windswept_spruces": ["trees_windswept_hills"],
    "marsh_trees": ["trees_swamp"],
    "lily_pads": ["patch_waterlily"],
    "reeds": ["patch_sugar_cane_swamp", "seagrass_swamp"],
    "acacias": ["trees_savanna"],
    "dry_grass": ["patch_grass_savanna"],
    "steam_vents": ["wayfarers:steam_vents"],
    "rustwood_trees": ["wayfarers:rustwood"],
    "rustwood_sparse": ["wayfarers:rustwood_sparse"],
    "rusted_wrecks": ["wayfarers:rusted_wrecks"],
    "jungle_giants": ["trees_jungle", "bamboo_light"],
    "jungle_floor": ["patch_grass_jungle", "vines", "flower_warm"],
    "melons": ["patch_melon"],
    "dune_cacti": ["patch_cactus_desert", "patch_dry_grass_desert"],
    "dead_bushes": ["patch_dead_bush_2"],
    "fossil_bones": ["fossil_upper", "fossil_lower"],
    "canyon_cacti": ["patch_cactus_decorated", "patch_dead_bush_badlands", "patch_dry_grass_badlands"],
    "cave_crystals": ["large_dripstone", "dripstone_cluster", "pointed_dripstone"],
    "amethyst_geodes": [],
    "lush_cave_vegetation": ["lush_caves_ceiling_vegetation", "cave_vines", "lush_caves_clay", "lush_caves_vegetation",
                             "rooted_azalea_tree", "spore_blossom", "classic_vines_cave_feature"],
    "sculk_growth": ["sculk_vein", "sculk_patch_deep_dark"],
    "cave_magma_pools": ["wayfarers:cave_magma"],
    "basalt_columns_cave": ["wayfarers:basalt_columns_cave"],
    "mithril_veins": ["wayfarers:mithril_veins"],
    # our stones (wf/decor.py WORLD_STONES), as big veins that show in cliffs and cave walls
    "marble_strata": ["wayfarers:marble_strata"],
    "rust_rock_veins": ["wayfarers:rust_rock_veins"],
    "blue_slate_veins": ["wayfarers:blue_slate_veins"],
    # natural objects (structure templates from wf/worldobjects.py) and scenery
    "thorn_spikes": ["wayfarers:thorn_spikes"],
    "stone_arches": ["wayfarers:stone_arches"],
    "crystal_shards": ["wayfarers:crystal_shards"],
    "hoodoos": ["wayfarers:hoodoos"],
    "hoodoos_sparse": ["wayfarers:hoodoos_sparse"],
    "hot_springs": ["wayfarers:hot_springs"],
    "flat_mushrooms": ["wayfarers:flat_mushrooms"],
    "ash_columns": ["wayfarers:ash_columns"],
    "lava_streams": ["wayfarers:lava_streams"],
    "lava_pools": ["wayfarers:lava_pools"],
    "mossy_boulders_many": ["forest_rock", "wayfarers:tuff_boulders"],
    "marble_boulders": ["wayfarers:marble_boulders"],
    "slate_boulders": ["wayfarers:slate_boulders"],
    "rust_boulders": ["wayfarers:rust_boulders"],
    "basalt_boulders": ["wayfarers:basalt_boulders"],
    "fallen_spruce_logs": ["wayfarers:fallen_spruce_logs"],
    "fallen_oak_logs": ["wayfarers:fallen_oak_logs"],
    "fallen_glowwood_logs": ["wayfarers:fallen_glowwood_logs"],
    "fallen_rustwood_logs": ["wayfarers:fallen_rustwood_logs"],
    "autumn_spruces": ["wayfarers:autumn_spruces"],
    "tall_spruces": ["wayfarers:giant_spruce_sparse", "trees_old_growth_spruce_taiga"],
    "autumn_oaks": ["wayfarers:autumn_oaks"],
    "sparse_autumn_oaks": ["wayfarers:autumn_oaks_sparse"],
    "crimson_reeds": ["patch_sugar_cane_swamp", "patch_tall_grass_2", "patch_grass_jungle"],
    "ripple_grass": ["patch_dry_grass_desert"],
}.items()}

# generation step of features that no vanilla template places (the rest come from the templates)
EXTRA_STEPS = {
    "minecraft:iceberg_packed": 2, "minecraft:iceberg_blue": 2, "minecraft:forest_rock": 2,
    "minecraft:fossil_upper": 3, "minecraft:fossil_lower": 3,
    "minecraft:blue_ice": 4, "minecraft:ice_spike": 4, "minecraft:ice_patch": 4,
    "minecraft:ore_emerald": 6,
    "wayfarers:basalt_columns": 4, "wayfarers:basalt_columns_cave": 7,
    "wayfarers:calcite_veins": 6, "wayfarers:cave_magma": 6, "wayfarers:mithril_veins": 6,
    "wayfarers:giant_spruce": 9, "wayfarers:glowwood": 9, "wayfarers:rusted_wrecks": 4,
    "wayfarers:glowwood_sparse": 9, "wayfarers:rustwood": 9, "wayfarers:rustwood_sparse": 9,
    "wayfarers:marble_strata": 6, "wayfarers:rust_rock_veins": 6, "wayfarers:blue_slate_veins": 6,
    "wayfarers:surface_crystals": 9, "wayfarers:river_crystals": 9, "wayfarers:steam_vents": 9,
    "wayfarers:thorn_spikes": 4, "wayfarers:stone_arches": 4, "wayfarers:crystal_shards": 4, "wayfarers:hoodoos": 4,
    "wayfarers:hoodoos_sparse": 4, "wayfarers:hot_springs": 4, "wayfarers:flat_mushrooms": 4,
    "wayfarers:ash_columns": 4, "wayfarers:lava_pools": 1, "wayfarers:lava_streams": 8,
    "wayfarers:tuff_boulders": 2, "wayfarers:marble_boulders": 2, "wayfarers:slate_boulders": 2,
    "wayfarers:rust_boulders": 2, "wayfarers:basalt_boulders": 2,
    "wayfarers:fallen_spruce_logs": 9, "wayfarers:fallen_oak_logs": 9, "wayfarers:fallen_glowwood_logs": 9,
    "wayfarers:fallen_rustwood_logs": 9, "wayfarers:autumn_spruces": 9, "wayfarers:giant_spruce_sparse": 9,
    "wayfarers:autumn_oaks": 9, "wayfarers:autumn_oaks_sparse": 9, "wayfarers:frost_pines_sparse": 9,
}

# mobs: our key -> vanilla template whose spawners we copy
SPAWN_TEMPLATES = {
    "plains": "plains", "meadow": "meadow", "forest": "forest", "enchanted": "forest", "dark_forest": "dark_forest",
    "taiga": "taiga", "snowy": "snowy_plains", "peaks": "jagged_peaks", "swamp": "swamp", "savanna": "plains",
    "jungle": "jungle", "desert": "desert", "badlands": "badlands", "beach": "beach", "river": "river",
    "ocean": "ocean", "cold_ocean": "ocean", "frozen_ocean": "ocean", "warm_ocean": "ocean",
    "cave": "dripstone_caves", "lush": "lush_caves", "none": "deep_dark", "mushroom": None,
}


def _step_of():
    steps = {}
    for t in TEMPLATES.values():
        for i, s in enumerate(t["features"]):
            for fid in s:
                steps.setdefault(fid, i)
    steps.update(EXTRA_STEPS)
    return steps


STEP_OF = _step_of()


def _master():
    """One global order per step: vanilla's lists merged (an unseen id goes right after the previous seen one)."""
    master = [[] for _ in range(STEPS)]
    for name in sorted(TEMPLATES):
        for i, s in enumerate(TEMPLATES[name]["features"]):
            prev = -1
            for fid in s:
                if fid in master[i]:
                    prev = master[i].index(fid)
                else:
                    master[i].insert(prev + 1, fid)
                    prev += 1
    for group in DECOR.values():
        for fid in group:
            step = STEP_OF.get(fid, 9)
            if fid not in master[step]:
                master[step].append(fid)
    return master


MASTER = _master()

MOUNTAIN_EXTRAS = _mc(["ore_emerald", "ore_infested"])
MOUNTAINS = {"majestic_peaks", "stone_spires", "snowcap_slopes", "windswept_crags", "highland_meadow"}


def features(b):
    """The 11 step lists of a biome, from its base template and its decoration groups."""
    if b["cave"]:
        base_name = {"lush": "lush_caves", "none": "deep_dark"}.get(b["mobs"], "dripstone_caves")
    elif b["mobs"] in ("ocean", "cold_ocean", "frozen_ocean", "warm_ocean"):
        base_name = "ocean"
    else:
        base_name = "plains"
    base = TEMPLATES[base_name]["features"]
    wanted = set()
    for i in range(STEPS):
        if i != 9:  # vegetation comes only from our groups
            wanted |= set(base[i])
    wanted.add("minecraft:glow_lichen")
    for group in b["decor"]:
        wanted |= set(DECOR[group])
    if b.get("id") in MOUNTAINS:
        wanted |= set(MOUNTAIN_EXTRAS)
    return [[fid for fid in MASTER[i] if fid in wanted] for i in range(STEPS)]


def carvers(b):
    return _mc(["cave", "cave_extra_underground", "canyon"])


def spawners(key):
    template = SPAWN_TEMPLATES[key]
    if template is None:  # glowcap isles: only mooshrooms and bats, never monsters
        return {"creature": [{"type": "minecraft:mooshroom", "weight": 8, "minCount": 4, "maxCount": 8}],
                "ambient": [{"type": "minecraft:bat", "weight": 10, "minCount": 8, "maxCount": 8}]}
    return TEMPLATES[template]["spawners"]


def attribute_extras(b):
    out = {}
    music = None
    if b["music"]:
        music = {"default": {"sound": b["music"], "min_delay": 12000, "max_delay": 24000}}
    elif SPAWN_TEMPLATES.get(b["mobs"]):
        music = TEMPLATES[SPAWN_TEMPLATES[b["mobs"]]]["music"]
    if music:
        out["minecraft:audio/background_music"] = music
    if b["particles"]:
        out["minecraft:visual/ambient_particles"] = [{"particle": {"type": b["particles"]},
                                                      "probability": b.get("particle_rate", 0.004)}]
    if b.get("fog_end"):
        # thick fog (mires, ash wastes): a plain value overrides the dimension's distance, blended between biomes
        out["minecraft:visual/fog_end_distance"] = float(b["fog_end"])
    return out


def _state(name, **props):
    st = {"Name": name if ":" in name else f"minecraft:{name}"}
    if props:
        st["Properties"] = {k: str(v).lower() for k, v in props.items()}
    return st


def _simple(state):
    return {"type": "minecraft:simple_block",
            "config": {"to_place": {"type": "minecraft:simple_state_provider", "state": state}}}


def _ore(state, tag, size):
    return {"type": "minecraft:ore", "config": {"size": size, "discard_chance_on_air_exposure": 0.0, "targets": [
        {"target": {"predicate_type": "minecraft:tag_match", "tag": tag}, "state": state}]}}


def _uniform(lo, hi):
    return {"type": "minecraft:uniform", "min_inclusive": lo, "max_inclusive": hi}


def _height(lo, hi):
    return {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo},
                                                          "max_inclusive": {"absolute": hi}}}


SURFACE = [{"type": "minecraft:in_square"}, {"type": "minecraft:heightmap", "heightmap": "MOTION_BLOCKING_NO_LEAVES"}]
FLOOR_SCAN = {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
              "target_condition": {"type": "minecraft:solid"},
              "allowed_search_condition": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}
ABOVE = {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": 1}
ON_AIR = {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}}
BIOME = {"type": "minecraft:biome"}

BELOW_TRUNK = {"type": "minecraft:rule_based_state_provider", "rules": [{
    "if_true": {"type": "minecraft:not", "predicate": {"type": "minecraft:matching_block_tag",
                                                         "tag": "minecraft:cannot_replace_below_tree_trunk"}},
    "then": {"type": "minecraft:simple_state_provider", "state": {"Name": "minecraft:dirt"}}}]}


def _tree(trunk, trunk_placer, foliage, foliage_placer, size):
    return {"type": "minecraft:tree", "config": {
        "trunk_provider": trunk, "trunk_placer": trunk_placer, "foliage_provider": foliage,
        "foliage_placer": foliage_placer, "minimum_size": size, "decorators": [], "ignore_vines": True,
        "below_trunk_provider": BELOW_TRUNK}}


def _tree_placement(count, sapling, rarity=None):
    """Trees on dry ground where `sapling` (an id; vanilla's without namespace) could grow."""
    sapling = sapling if ":" in sapling else f"minecraft:{sapling}"
    head = [{"type": "minecraft:rarity_filter", "chance": rarity}] if rarity else [{"type": "minecraft:count", "count": count}]
    return head + [{"type": "minecraft:in_square"},
                   {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
                   {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
                   {"type": "minecraft:block_predicate_filter",
                    "predicate": {"type": "minecraft:would_survive", "state": {"Name": sapling, "Properties": {"stage": "0"}}}},
                   BIOME]


# dry, rusty ground a Rustwood takes root in (the sapling itself needs dirt; the wild trees are less picky)
RUST_GROUND = {"type": "minecraft:any_of", "predicates": [
    {"type": "minecraft:matching_block_tag", "offset": [0, -1, 0], "tag": "minecraft:dirt"},
    {"type": "minecraft:matching_blocks", "offset": [0, -1, 0],
     "blocks": ["minecraft:red_sand", "minecraft:terracotta", "minecraft:red_terracotta", "minecraft:smooth_sandstone",
                "wayfarers:rust_rock"]}]}


def _rust_tree_placement(count=None, rarity=None):
    head = [{"type": "minecraft:rarity_filter", "chance": rarity}] if rarity else [{"type": "minecraft:count", "count": count}]
    return head + [{"type": "minecraft:in_square"},
                   {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
                   {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
                   {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
                       {"type": "minecraft:matching_blocks", "blocks": "minecraft:air"}, RUST_GROUND]}},
                   BIOME]


def _provider(name):
    return {"type": "minecraft:simple_state_provider", "state": {"Name": f"minecraft:{name}"}}


# id -> (configured feature, placement modifiers)
OURS = {
    # half-buried steampunk wrecks (templates from wf/wrecks.py)
    "rusted_wrecks": ({"type": "minecraft:template", "config": {"templates": [
        {"data": {"id": f"wayfarers:wrecks/{n}"}, "weight": w}
        for n, w in (("cog", 3), ("pipe", 3), ("boiler", 2), ("stump", 2), ("automaton", 2))]}},
        [{"type": "minecraft:rarity_filter", "chance": 6}, {"type": "minecraft:in_square"},
         {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
         {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -1}, BIOME]),
    # Giant Sylvan Forest: spruces 28 to 40 blocks tall
    "giant_spruce": (_tree(_provider("spruce_log"),
                           {"type": "minecraft:giant_trunk_placer", "base_height": 28, "height_rand_a": 4, "height_rand_b": 8},
                           _provider("spruce_leaves"),
                           {"type": "minecraft:mega_pine_foliage_placer", "radius": 0, "offset": 0,
                            "crown_height": _uniform(15, 20)},
                           {"type": "minecraft:two_layers_feature_size", "limit": 1, "lower_size": 1, "upper_size": 2}),
                     _tree_placement(4, "spruce_sapling")),
    # Glowwoods (wf/worldblocks.py): pale trunks under glowing teal crowns. The tree itself is
    # data/wayfarers/worldgen/configured_feature/glowwood_tree.json (always loaded: its sapling grows it too)
    "glowwood": ("wayfarers:glowwood_tree", _tree_placement(5, "wayfarers:glowwood_sapling")),
    "glowwood_sparse": ("wayfarers:glowwood_tree", _tree_placement(0, "wayfarers:glowwood_sapling", rarity=3)),
    # Rustwoods: dark red forking trunks with rust-orange crowns, on dry and rusty ground
    "rustwood": ("wayfarers:rustwood_tree", _rust_tree_placement(count=1)),
    "rustwood_sparse": ("wayfarers:rustwood_tree", _rust_tree_placement(rarity=5)),
    # stone veins, large like vanilla's granite/diorite blobs, high up where cliffs and peaks expose them
    "marble_strata": (_ore(_state("wayfarers:marble"), "minecraft:base_stone_overworld", 64),
                      [{"type": "minecraft:count", "count": 5}, {"type": "minecraft:in_square"}, _height(70, 300), BIOME]),
    "rust_rock_veins": (_ore(_state("wayfarers:rust_rock"), "minecraft:base_stone_overworld", 56),
                        [{"type": "minecraft:count", "count": 4}, {"type": "minecraft:in_square"}, _height(30, 200), BIOME]),
    "blue_slate_veins": (_ore(_state("wayfarers:blue_slate"), "minecraft:base_stone_overworld", 56),
                         [{"type": "minecraft:count", "count": 4}, {"type": "minecraft:in_square"}, _height(-10, 160), BIOME]),
    "basalt_columns": ({"type": "minecraft:basalt_columns", "config": {"reach": 1, "height": _uniform(2, 6)}},
                       [{"type": "minecraft:count", "count": 3}] + SURFACE + [BIOME]),
    "basalt_columns_cave": ({"type": "minecraft:basalt_columns", "config": {"reach": 2, "height": _uniform(3, 9)}},
                            [{"type": "minecraft:count", "count": 24}, {"type": "minecraft:in_square"}, _height(-56, 40),
                             FLOOR_SCAN, ABOVE, BIOME]),
    "calcite_veins": (_ore(_state("calcite"), "minecraft:base_stone_overworld", 33),
                      [{"type": "minecraft:count", "count": 6}, {"type": "minecraft:in_square"}, _height(60, 300), BIOME]),
    "cave_magma": (_ore(_state("magma_block"), "minecraft:base_stone_overworld", 24),
                   [{"type": "minecraft:count", "count": 10}, {"type": "minecraft:in_square"}, _height(-56, 30), BIOME]),
    "mithril_veins": (_ore(_state("wayfarers:deepslate_mithril_ore"), "minecraft:deepslate_ore_replaceables", 7),
                      [{"type": "minecraft:count", "count": 10}, {"type": "minecraft:in_square"}, _height(-64, 0), BIOME]),
    "surface_crystals": (_simple(_state("amethyst_cluster", facing="up", waterlogged=False)),
                         [{"type": "minecraft:count", "count": 4}] + SURFACE + [ON_AIR, BIOME]),
    "river_crystals": (_simple(_state("amethyst_cluster", facing="up", waterlogged=True)),
                       [{"type": "minecraft:count", "count": 3}, {"type": "minecraft:in_square"},
                        {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
                        {"type": "minecraft:block_predicate_filter",
                         "predicate": {"type": "minecraft:matching_blocks", "blocks": "minecraft:water"}}, BIOME]),
    "steam_vents": (_simple(_state("campfire", facing="north", lit=True, signal_fire=False, waterlogged=False)),
                    [{"type": "minecraft:rarity_filter", "chance": 2}] + SURFACE + [ON_AIR, BIOME]),
}


# ------------------------------------------------------------------ natural objects and scenery
def _objects(kind):
    """A template feature picking one of the variants of `kind` (wf/worldobjects.py), rotated at random."""
    from . import worldobjects
    return {"type": "minecraft:template", "config": {"templates": [
        {"data": {"id": t}, "weight": 1} for t in worldobjects.template_ids(kind)]}}


def _object_placement(count=None, rarity=None, sink=2):
    head = [{"type": "minecraft:rarity_filter", "chance": rarity}] if rarity else [{"type": "minecraft:count", "count": count}]
    return head + [{"type": "minecraft:in_square"}, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
                   {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
                   {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -sink}, BIOME]


GROUND = {"type": "minecraft:any_of", "predicates": [
    {"type": "minecraft:matching_block_tag", "tag": t} for t in
    ("minecraft:dirt", "minecraft:sand", "minecraft:terracotta", "minecraft:base_stone_overworld", "minecraft:nylium")]
    + [{"type": "minecraft:matching_blocks", "blocks": ["minecraft:snow_block", "minecraft:gravel", "minecraft:calcite",
                                                        "minecraft:coarse_dirt", "minecraft:mud", "minecraft:blackstone",
                                                        "wayfarers:marble", "wayfarers:rust_rock", "wayfarers:blue_slate"]}]}


def _boulder(block, count):
    return ({"type": "minecraft:block_blob", "config": {"state": _state(block), "can_place_on": GROUND}},
            [{"type": "minecraft:count", "count": count}] + SURFACE + [BIOME])


def _fallen(log, sapling, rarity):
    return ({"type": "minecraft:fallen_tree", "config": {
        "trunk_provider": {"type": "minecraft:simple_state_provider", "state": _state(log, axis="y")},
        "log_length": _uniform(5, 9), "stump_decorators": [], "log_decorators": []}},
        _tree_placement(0, sapling, rarity=rarity))


SPRING_ROCK = ["minecraft:" + b for b in (
    "stone", "granite", "andesite", "tuff", "deepslate", "blackstone", "basalt", "coarse_dirt", "dirt", "grass_block",
    "terracotta", "brown_terracotta", "orange_terracotta", "red_terracotta", "yellow_terracotta",
    "light_gray_terracotta", "gray_terracotta", "magma_block", "smooth_basalt", "calcite", "red_sand")] + [
    "wayfarers:rust_rock"]


def _leaves(name):
    return {"type": "minecraft:simple_state_provider",
            "state": _state(name, distance=7, persistent=False, waterlogged=False)}


def _spruce_like(leaves, base, rand_a, rand_b):
    return _tree(_provider("spruce_log"),
                 {"type": "minecraft:straight_trunk_placer", "base_height": base, "height_rand_a": rand_a,
                  "height_rand_b": rand_b},
                 _leaves(leaves),
                 {"type": "minecraft:spruce_foliage_placer", "radius": _uniform(2, 3), "offset": _uniform(0, 2),
                  "trunk_height": _uniform(1, 2)},
                 {"type": "minecraft:two_layers_feature_size", "limit": 2, "lower_size": 0, "upper_size": 2})


def _oak_like(base, rand_a):
    return _tree(_provider("oak_log"),
                 {"type": "minecraft:straight_trunk_placer", "base_height": base, "height_rand_a": rand_a,
                  "height_rand_b": 0},
                 _leaves("minecraft:oak_leaves"),
                 {"type": "minecraft:blob_foliage_placer", "radius": 2, "offset": 0, "height": 3},
                 {"type": "minecraft:two_layers_feature_size", "limit": 1, "lower_size": 0, "upper_size": 1})


OURS.update({
    # slim curved blackstone horns of the Crimson Mire, 15-30 blocks tall (one per chunk: a field of thorns)
    "thorn_spikes": (_objects("thorn"), _object_placement(count=1, sink=2)),
    # natural arches of banded grey rock (Ashen Wastes)
    "stone_arches": (_objects("arch"), _object_placement(rarity=5, sink=3)),
    # leaning aether crystal shards
    "crystal_shards": (_objects("crystal"), _object_placement(rarity=3, sink=1)),
    # banded terracotta hoodoos (Pale Dunes, Painted Canyon)
    "hoodoos": (_objects("hoodoo"), _object_placement(rarity=2, sink=2)),
    "hoodoos_sparse": (_objects("hoodoo"), _object_placement(rarity=4, sink=2)),
    # hot-spring terraces with coloured rims (Geyser Basin)
    "hot_springs": (_objects("hot_spring"), _object_placement(rarity=3, sink=3)),
    # giant flat-capped red mushrooms with weeping vines (Crimson Mire): one chunk in two, caps 10-18 wide
    "flat_mushrooms": (_objects("flat_mushroom"), _object_placement(rarity=2, sink=1)),
    "ash_columns": (_objects("ash_column"), _object_placement(rarity=3, sink=2)),
    # lava springs just under the surface of slopes: lava streams run down the mountainsides
    "lava_streams": ({"type": "minecraft:spring_feature", "config": {
        "state": {"Name": "minecraft:lava", "Properties": {"falling": "false"}}, "requires_block_below": True,
        "rock_count": 4, "hole_count": 1, "valid_blocks": SPRING_ROCK}},
        [{"type": "minecraft:count", "count": 12}, {"type": "minecraft:in_square"},
         {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
         {"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -2}, BIOME]),
    "lava_pools": ({"type": "minecraft:lake", "config": {
        "fluid": {"type": "minecraft:simple_state_provider", "state": {"Name": "minecraft:lava", "Properties": {"level": "0"}}},
        "barrier": {"type": "minecraft:simple_state_provider", "state": {"Name": "minecraft:blackstone"}},
        "can_place_feature": {"type": "minecraft:true"},
        "can_replace_with_air_or_fluid": {"type": "minecraft:not", "predicate": {
            "type": "minecraft:matching_block_tag", "tag": "minecraft:features_cannot_replace"}},
        "can_replace_with_barrier": {"type": "minecraft:not", "predicate": {
            "type": "minecraft:matching_block_tag", "tag": "minecraft:lava_pool_stone_cannot_replace"}}}},
        [{"type": "minecraft:rarity_filter", "chance": 9}, {"type": "minecraft:in_square"},
         {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, BIOME]),
    # boulders of our stones and vanilla rock
    "tuff_boulders": _boulder("tuff", 1),
    "marble_boulders": _boulder("wayfarers:marble", 2),
    "slate_boulders": _boulder("wayfarers:blue_slate", 2),
    "rust_boulders": _boulder("wayfarers:rust_rock", 2),
    "basalt_boulders": _boulder("blackstone", 2),
    # fallen logs
    "fallen_spruce_logs": _fallen("spruce_log", "spruce_sapling", 3),
    "fallen_oak_logs": _fallen("oak_log", "oak_sapling", 3),
    "fallen_glowwood_logs": _fallen("wayfarers:glowwood_log", "oak_sapling", 4),
    "fallen_rustwood_logs": _fallen("wayfarers:rustwood_log", "oak_sapling", 5),
    # autumn trees: oak leaves take the biome's (orange) foliage colour, spruce leaves stay green
    "autumn_spruces": (_spruce_like("oak_leaves", 6, 3, 2), _tree_placement(7, "spruce_sapling")),
    "giant_spruce_sparse": ("wayfarers:giant_spruce", _tree_placement(0, "spruce_sapling", rarity=3)),
    # a lone spruce or two per chunk on the fjord tops and snowy slopes (vanilla's spruce; the snow comes from
    # freeze_top_layer)
    "frost_pines_sparse": ("minecraft:spruce", _tree_placement(1, "spruce_sapling")),
    "autumn_oaks": (_oak_like(5, 3), _tree_placement(3, "oak_sapling")),
    "autumn_oaks_sparse": (_oak_like(4, 2), _tree_placement(0, "oak_sapling", rarity=4)),
})


# A surface feature (thorn, giant mushroom, hoodoo, boulder, tree...) generates after the structures: without this
# filter (com.wayfarers.world.ClearOfStructuresFilter) it can grow through a building. Skipped in a chunk that a
# surface structure (tag wayfarers:clears_decoration) reaches.
CLEAR = {"type": "wayfarers:clear_of_structures"}


def _on_surface(placement):
    return any(m.get("type") in ("minecraft:heightmap", "minecraft:surface_relative_threshold_filter")
               or m is FLOOR_SCAN for m in placement)


def write_features(write):
    """Our configured and placed features (data/wayfarers/worldgen/... inside the overhaul pack)."""
    for fid, (configured, placement) in OURS.items():
        if _on_surface(placement):
            placement = [m for m in placement if m is not BIOME] + [CLEAR, BIOME]
        if isinstance(configured, str):  # a configured feature of the mod's own data (always loaded)
            write(f"wayfarers/worldgen/placed_feature/{fid}.json", {"feature": configured, "placement": placement})
            continue
        write(f"wayfarers/worldgen/configured_feature/{fid}.json", configured)
        write(f"wayfarers/worldgen/placed_feature/{fid}.json", {"feature": f"wayfarers:{fid}", "placement": placement})
    return len(OURS)
