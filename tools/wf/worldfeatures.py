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
    "frost_pines_sparse": ["trees_snowy"],
    "ice_spires_small": ["ice_patch"],
    "calcite_veins": ["wayfarers:calcite_veins"],
    "meadow_flowers": ["flower_meadow", "wildflowers_meadow"],
    "lone_oaks": ["trees_plains"],
    "tall_grass": ["patch_tall_grass_2", "patch_grass_plain"],
    "wildflowers": ["flower_flower_forest", "patch_sunflower", "wildflowers_birch_forest"],
    "bee_trees": ["trees_plains"],
    "boulders": ["forest_rock"],
    "glowwood_trees": ["wayfarers:glowwood", "trees_flower_forest"],
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
    "wayfarers:surface_crystals": 9, "wayfarers:river_crystals": 9, "wayfarers:steam_vents": 9,
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
        out["minecraft:visual/ambient_particles"] = [{"particle": {"type": b["particles"]}, "probability": 0.004}]
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


def _tree_placement(count, sapling):
    return [{"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
            {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
            {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
            {"type": "minecraft:block_predicate_filter",
             "predicate": {"type": "minecraft:would_survive", "state": {"Name": f"minecraft:{sapling}", "Properties": {"stage": "0"}}}},
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
    # Enchanted Forest: round azalea crowns dotted with glowing shroomlights
    "glowwood": (_tree(_provider("oak_log"),
                       {"type": "minecraft:fancy_trunk_placer", "base_height": 8, "height_rand_a": 6, "height_rand_b": 0},
                       {"type": "minecraft:weighted_state_provider", "entries": [
                           {"data": {"Name": "minecraft:azalea_leaves"}, "weight": 6},
                           {"data": {"Name": "minecraft:flowering_azalea_leaves"}, "weight": 4},
                           {"data": {"Name": "minecraft:shroomlight"}, "weight": 1}]},
                       {"type": "minecraft:fancy_foliage_placer", "radius": 2, "offset": 4, "height": 4},
                       {"type": "minecraft:two_layers_feature_size", "limit": 0, "lower_size": 0, "upper_size": 0,
                        "min_clipped_height": 4}),
                 _tree_placement(5, "oak_sapling")),
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


def write_features(write):
    """Our configured and placed features (data/wayfarers/worldgen/... inside the overhaul pack)."""
    for fid, (configured, placement) in OURS.items():
        write(f"wayfarers/worldgen/configured_feature/{fid}.json", configured)
        write(f"wayfarers/worldgen/placed_feature/{fid}.json", {"feature": f"wayfarers:{fid}", "placement": placement})
    return len(OURS)
