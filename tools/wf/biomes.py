"""Wayfarers biomes for the world overhaul (tools/gen_world.py).

Placement: vanilla's climate layout (world_points.json), with every vanilla biome swapped for one of ours through
VANILLA_TO_OURS, and extra cave biomes. Each biome sets its colours, weather, top blocks (surface rules), mobs and
decoration (vanilla placed features plus our own, see worldfeatures.py).
"""
import json
import os

from . import worldfeatures as WF

NS = "wayfarers"

# vanilla biome (as placed by OverworldBiomeBuilder) -> our biome
VANILLA_TO_OURS = {
    "deep_frozen_ocean": "glacial_sea", "frozen_ocean": "glacial_sea",
    "deep_cold_ocean": "slate_sea", "cold_ocean": "slate_sea",
    "deep_ocean": "azure_ocean", "ocean": "azure_ocean",
    "deep_lukewarm_ocean": "coral_lagoon", "lukewarm_ocean": "coral_lagoon", "warm_ocean": "coral_lagoon",
    "mushroom_fields": "glowcap_isles",
    "beach": "golden_beach", "snowy_beach": "frost_shore", "stony_shore": "basalt_cliffs",
    "river": "crystal_river", "frozen_river": "ice_river",
    "snowy_plains": "aurora_tundra", "ice_spikes": "shattered_glacier", "snowy_taiga": "frostpine_forest",
    "snowy_slopes": "snowcap_slopes", "grove": "frostpine_forest",
    "frozen_peaks": "majestic_peaks", "jagged_peaks": "majestic_peaks", "stony_peaks": "stone_spires",
    "plains": "verdant_meadows", "sunflower_plains": "wildflower_fields", "meadow": "highland_meadow",
    "flower_forest": "enchanted_forest", "forest": "elderwood", "birch_forest": "silver_birch_wood",
    "old_growth_birch_forest": "crystal_woods", "dark_forest": "shadow_woods", "pale_garden": "shadow_woods",
    "taiga": "pine_highlands", "old_growth_spruce_taiga": "giant_sylvan", "old_growth_pine_taiga": "giant_sylvan",
    "cherry_grove": "sakura_valley",
    "windswept_hills": "windswept_crags", "windswept_gravelly_hills": "windswept_crags", "windswept_forest": "windswept_crags",
    "swamp": "glowing_marsh", "mangrove_swamp": "glowing_marsh",
    "savanna": "ashen_savanna", "savanna_plateau": "rustlands", "windswept_savanna": "rustlands",
    "jungle": "emerald_jungle", "sparse_jungle": "emerald_jungle", "bamboo_jungle": "emerald_jungle",
    "desert": "dune_sea", "badlands": "painted_canyon", "eroded_badlands": "cogwork_valley",
    "wooded_badlands": "cogwork_valley",
    "dripstone_caves": "crystal_caverns", "lush_caves": "underground_jungle", "deep_dark": "deep_abyss",
    "sulfur_caves": "thermal_caves",
}

# extra cave biomes: (biome, temperature, humidity, continentalness, erosion, weirdness) with depth 0.2..0.9
EXTRA_CAVES = [
    ("fungal_grotto", [-1.0, 1.0], [0.3, 0.7], [-1.0, 1.0], [-1.0, 1.0], [-1.0, -0.6]),
    ("thermal_caves", [0.55, 1.0], [-1.0, 1.0], [0.8, 1.0], [-1.0, 1.0], [-1.0, 1.0]),
    ("mithril_hollows", [-1.0, -0.45], [-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0], [0.6, 1.0]),
]


def B(en, fr, temp, downfall, sky, fog, water, water_fog, grass=None, foliage=None, rain=True, surface="grass",
      decor=(), mobs="plains", music=None, particles=None, cave=False):
    return dict(en=en, fr=fr, temp=temp, downfall=downfall, sky=sky, fog=fog, water=water, water_fog=water_fog,
                grass=grass, foliage=foliage, rain=rain, surface=surface, decor=list(decor), mobs=mobs, music=music,
                particles=particles, cave=cave)


# id -> design. decor: keys of worldfeatures.DECOR (vanilla placed features + ours), mobs: worldfeatures.SPAWNS key
BIOMES = {
    # ---------------------------------------------------------------- oceans and coasts
    "glacial_sea": B("Glacial Sea", "Mer glaciaire", 0.0, 0.5, "#7fa1ff", "#c0d8ff", "#3938c9", "#050533",
                     surface="ocean_cold", decor=["icebergs", "ocean_floor_cold", "kelp_cold"], mobs="frozen_ocean"),
    "slate_sea": B("Slate Sea", "Mer d'ardoise", 0.5, 0.5, "#7ba4ff", "#b6c8e8", "#3d57d6", "#050533",
                   surface="ocean_cold", decor=["ocean_floor_cold", "kelp_cold", "seagrass_deep"], mobs="cold_ocean"),
    "azure_ocean": B("Azure Ocean", "Océan d'azur", 0.5, 0.5, "#78a7ff", "#c0d8ff", "#2b79e6", "#04294f",
                     surface="ocean", decor=["ocean_floor", "seagrass_deep", "kelp"], mobs="ocean"),
    "coral_lagoon": B("Coral Lagoon", "Lagon de corail", 0.8, 0.5, "#80cfff", "#d6f4ff", "#1fd6c8", "#0a5c63",
                      surface="ocean_warm", decor=["warm_ocean_vegetation", "seagrass_warm", "sea_pickles"], mobs="warm_ocean"),
    "glowcap_isles": B("Glowcap Isles", "Îles aux champignons luisants", 0.9, 1.0, "#9fb6ff", "#d9c8ff", "#8f6be0", "#2a1a52",
                       grass="#55c98d", surface="mycelium", decor=["giant_glowcaps", "mushrooms_dense", "glow_lichen"],
                       mobs="mushroom", particles="minecraft:spore_blossom_air"),
    "golden_beach": B("Golden Beach", "Plage dorée", 0.8, 0.4, "#78a7ff", "#ffe9c4", "#3fb8e6", "#06375a",
                      surface="beach", decor=["palms", "beach_grass"], mobs="beach"),
    "frost_shore": B("Frost Shore", "Rivage de givre", 0.05, 0.3, "#7fa1ff", "#d8e6ff", "#3d57d6", "#050533",
                     surface="snowy_beach", decor=["frost_rocks"], mobs="snowy"),
    "basalt_cliffs": B("Basalt Cliffs", "Falaises de basalte", 0.4, 0.6, "#7ba4ff", "#c6cdd8", "#2a6fb5", "#05264a",
                       surface="basalt", decor=["basalt_columns", "sea_stacks"], mobs="beach"),
    "crystal_river": B("Crystal River", "Rivière de cristal", 0.6, 0.6, "#78a7ff", "#cfe6ff", "#3ad2ff", "#06375a",
                       grass="#62c25a", surface="river", decor=["river_reeds", "river_crystals", "seagrass"], mobs="river"),
    "ice_river": B("Frozen River", "Rivière gelée", 0.0, 0.5, "#7fa1ff", "#d8e6ff", "#3938c9", "#050533",
                   surface="river_frozen", decor=["seagrass"], mobs="river"),
    # ---------------------------------------------------------------- cold
    "aurora_tundra": B("Aurora Tundra", "Toundra aurorale", 0.0, 0.5, "#6d7dff", "#c8d8ff", "#3d57d6", "#050533",
                       grass="#8ab689", foliage="#68a464", surface="snowy_grass", decor=["frost_rocks", "snowy_spruces_sparse"],
                       mobs="snowy", particles="minecraft:white_ash"),
    "shattered_glacier": B("Shattered Glacier", "Glacier brisé", -0.5, 0.5, "#7d9bff", "#e3eeff", "#3938c9", "#050533",
                           surface="glacier", decor=["ice_spires", "blue_ice_chunks"], mobs="snowy"),
    "frostpine_forest": B("Frostpine Forest", "Forêt de pins givrés", -0.3, 0.4, "#839dff", "#d4e2ff", "#3d57d6", "#050533",
                          grass="#80b497", foliage="#60a17b", surface="snowy_podzol", decor=["frost_pines", "berry_bushes"],
                          mobs="taiga"),
    "snowcap_slopes": B("Snowcap Slopes", "Pentes enneigées", -0.3, 0.9, "#839dff", "#dfe9ff", "#3d57d6", "#050533",
                        surface="snow_slopes", decor=["frost_pines_sparse"], mobs="snowy"),
    "majestic_peaks": B("Majestic Peaks", "Pics majestueux", -0.7, 0.9, "#8cb3ff", "#eef4ff", "#3d57d6", "#050533",
                        surface="peaks", decor=["ice_spires_small"], mobs="peaks", particles="minecraft:white_ash"),
    "stone_spires": B("Stone Spires", "Aiguilles de pierre", 1.0, 0.3, "#76a8ff", "#d6d6d6", "#3f76e4", "#050533",
                      surface="spires", decor=["calcite_veins"], mobs="peaks"),
    # ---------------------------------------------------------------- temperate
    "verdant_meadows": B("Verdant Meadows", "Prairies verdoyantes", 0.8, 0.4, "#78a7ff", "#c0d8ff", "#3f76e4", "#050533",
                         grass="#79c05a", foliage="#59ae30", decor=["meadow_flowers", "lone_oaks", "tall_grass"], mobs="plains"),
    "wildflower_fields": B("Wildflower Fields", "Champs de fleurs sauvages", 0.8, 0.5, "#78a7ff", "#c0d8ff", "#3f76e4", "#050533",
                           grass="#86cc5e", foliage="#59ae30", decor=["wildflowers", "tall_grass", "bee_trees"], mobs="plains"),
    "highland_meadow": B("Highland Meadow", "Alpage", 0.5, 0.8, "#7ba4ff", "#c0d8ff", "#0e4ecf", "#050533",
                         grass="#83bb6d", foliage="#63a948", decor=["meadow_flowers", "tall_grass", "boulders"], mobs="meadow"),
    "enchanted_forest": B("Enchanted Forest", "Forêt enchantée", 0.7, 0.8, "#8f9bff", "#c9b8ff", "#7a63e8", "#1d1452",
                          grass="#4fd1a1", foliage="#3fc4c0", decor=["glowwood_trees", "glow_flowers", "glow_lichen"],
                          mobs="enchanted", particles="minecraft:firefly"),
    "elderwood": B("Elderwood", "Bois des anciens", 0.7, 0.8, "#79a6ff", "#c0d8ff", "#3f76e4", "#050533",
                   grass="#5fae45", foliage="#4c9a2a", decor=["great_oaks", "forest_floor"], mobs="forest"),
    "silver_birch_wood": B("Silver Birch Wood", "Bois de bouleaux d'argent", 0.6, 0.6, "#7aa5ff", "#d0e0ff", "#3f76e4", "#050533",
                           grass="#88bb67", foliage="#6ba941", decor=["tall_birches", "forest_floor"], mobs="forest"),
    "crystal_woods": B("Crystal Woods", "Bois de cristal", 0.6, 0.6, "#8fb0ff", "#cdeeff", "#3ad2ff", "#06375a",
                       grass="#6fcfb0", foliage="#7fe0d8", decor=["tall_birches", "surface_crystals", "glow_flowers"],
                       mobs="forest", particles="minecraft:end_rod"),
    "shadow_woods": B("Shadow Woods", "Bois des ombres", 0.6, 0.8, "#6f7aa8", "#7d8496", "#3a4f6b", "#050533",
                      grass="#4e7a3a", foliage="#3b6a2a", decor=["shadow_oaks", "mushrooms_dense"], mobs="dark_forest",
                      particles="minecraft:ash"),
    "pine_highlands": B("Pine Highlands", "Hautes terres de pins", 0.25, 0.8, "#7fa1ff", "#c8d8ff", "#287082", "#050533",
                        grass="#86b783", foliage="#68a464", surface="podzol_patches", decor=["pines", "berry_bushes"], mobs="taiga"),
    "giant_sylvan": B("Giant Sylvan Forest", "Sylve géante", 0.3, 0.8, "#7fa1ff", "#bcd0e8", "#287082", "#050533",
                      grass="#6ea85b", foliage="#4f8f3a", surface="podzol_patches", decor=["giant_trees", "ferns", "mossy_boulders"],
                      mobs="taiga", particles="minecraft:spore_blossom_air"),
    "sakura_valley": B("Sakura Valley", "Vallée des cerisiers", 0.5, 0.8, "#8fb8ff", "#ffd6ea", "#5db7ef", "#5db7ef",
                       grass="#b6db61", foliage="#b6db61", decor=["great_cherries", "pink_petals"], mobs="meadow",
                       particles="minecraft:cherry_leaves"),
    "windswept_crags": B("Windswept Crags", "Escarpements venteux", 0.2, 0.3, "#7da3ff", "#c8d0dc", "#3f76e4", "#050533",
                         grass="#8ab689", foliage="#6da36b", surface="crags", decor=["windswept_spruces", "boulders"], mobs="peaks"),
    "glowing_marsh": B("Glowing Marsh", "Marais luminescent", 0.8, 0.9, "#6f8fd0", "#8db39a", "#2fb38a", "#0c3324",
                       grass="#5a8a3a", foliage="#4f7f2f", surface="marsh", decor=["marsh_trees", "glow_lichen", "lily_pads", "reeds"],
                       mobs="swamp", particles="minecraft:firefly"),
    # ---------------------------------------------------------------- warm
    "ashen_savanna": B("Ashen Savanna", "Savane cendrée", 1.4, 0.0, "#6eb1ff", "#e0d6c4", "#3f76e4", "#050533",
                       grass="#b0a456", foliage="#a69a46", rain=False, surface="savanna", decor=["acacias", "dry_grass"], mobs="savanna"),
    "rustlands": B("Rustlands", "Terres rouillées", 1.2, 0.0, "#8aa8d8", "#d8a07a", "#4f8f8a", "#1b2f2c",
                   grass="#a08646", foliage="#8f7436", rain=False, surface="rust", decor=["steam_vents", "rusted_wrecks", "dry_grass"],
                   mobs="savanna", particles="minecraft:ash"),
    "emerald_jungle": B("Emerald Jungle", "Jungle d'émeraude", 0.95, 0.9, "#77a8ff", "#c6e8c0", "#14a2c5", "#0a4a55",
                        grass="#59c93c", foliage="#30bb0b", decor=["jungle_giants", "jungle_floor", "melons"], mobs="jungle"),
    "dune_sea": B("Dune Sea", "Mer de dunes", 2.0, 0.0, "#6eb1ff", "#f2dfb4", "#32a598", "#050533", rain=False,
                  surface="desert", decor=["dune_cacti", "dead_bushes", "fossil_bones"], mobs="desert"),
    "painted_canyon": B("Painted Canyon", "Canyon peint", 2.0, 0.0, "#6eb1ff", "#f0c89a", "#3f76e4", "#050533", rain=False,
                        grass="#90814d", foliage="#9e814d", surface="badlands", decor=["dead_bushes", "canyon_cacti"], mobs="badlands"),
    "cogwork_valley": B("Cogwork Valley", "Vallée des engrenages", 1.6, 0.1, "#80a9e0", "#e4c9a0", "#4f8f8a", "#1b2f2c", rain=False,
                        grass="#9e8f4d", foliage="#9e814d", surface="cogwork", decor=["rusted_wrecks", "steam_vents", "acacias"],
                        mobs="badlands"),
    # ---------------------------------------------------------------- caves
    "crystal_caverns": B("Crystal Caverns", "Cavernes de cristal", 0.6, 0.4, "#78a7ff", "#3a2f5a", "#3ad2ff", "#06375a",
                         surface="cave_calcite", decor=["cave_crystals", "amethyst_geodes"], mobs="cave", cave=True,
                         music="minecraft:music.overworld.dripstone_caves", particles="minecraft:end_rod"),
    "underground_jungle": B("Underground Jungle", "Jungle souterraine", 0.8, 0.9, "#78a7ff", "#c0d8ff", "#3f76e4", "#050533",
                            surface="cave_moss", decor=["lush_cave_vegetation"], mobs="lush", cave=True,
                            music="minecraft:music.overworld.lush_caves"),
    "deep_abyss": B("Deep Abyss", "Abîme profond", 0.8, 0.4, "#78a7ff", "#0c0c14", "#3f76e4", "#050533",
                    surface="cave_sculk", decor=["sculk_growth"], mobs="none", cave=True,
                    music="minecraft:music.overworld.deep_dark", particles="minecraft:ash"),
    "thermal_caves": B("Thermal Caves", "Grottes thermales", 1.2, 0.0, "#78a7ff", "#4a2a1a", "#d06a2a", "#3a1a0a", rain=False,
                       surface="cave_magma", decor=["cave_magma_pools", "basalt_columns_cave"], mobs="cave", cave=True,
                       particles="minecraft:ash"),
    "fungal_grotto": B("Fungal Grotto", "Grotte fongique", 0.7, 0.9, "#78a7ff", "#3a5a4a", "#2fb38a", "#0c3324",
                       surface="cave_mycelium", decor=["giant_glowcaps", "mushrooms_dense", "glow_lichen"], mobs="cave",
                       cave=True, particles="minecraft:spore_blossom_air"),
    "mithril_hollows": B("Mithril Hollows", "Creux de mithril", 0.2, 0.3, "#78a7ff", "#2a3a5a", "#3f76e4", "#050533",
                         surface="cave_deepslate", decor=["mithril_veins", "cave_crystals"], mobs="cave", cave=True),
}


# ------------------------------------------------------------------ placement
def climate_points():
    rows = json.load(open(os.path.join(os.path.dirname(__file__), "world_points.json")))
    out = []
    for b, t, h, c, e, d, w, o in rows:
        ours = VANILLA_TO_OURS[b]
        out.append({"biome": f"{NS}:{ours}", "parameters": {
            "temperature": t, "humidity": h, "continentalness": c, "erosion": e, "depth": d, "weirdness": w, "offset": o}})
    for biome, t, h, c, e, w in EXTRA_CAVES:
        out.append({"biome": f"{NS}:{biome}", "parameters": {
            "temperature": t, "humidity": h, "continentalness": c, "erosion": e, "depth": [0.2, 0.9], "weirdness": w,
            "offset": 0.0}})
    return out


# ------------------------------------------------------------------ surface rules
def _block(name, props=None):
    state = {"Name": name if ":" in name else f"minecraft:{name}"}
    if props:
        state["Properties"] = props
    return {"type": "minecraft:block", "result_state": state}


def _if(cond, then):
    return {"type": "minecraft:condition", "if_true": cond, "then_run": then}


def _seq(*rules):
    return {"type": "minecraft:sequence", "sequence": list(rules)}


def _biomes(*ids):
    return {"type": "minecraft:biome", "biome_is": [f"{NS}:{i}" for i in ids]}


def _not(c):
    return {"type": "minecraft:not", "invert": c}


def _depth(kind="floor", add=False, offset=0, secondary=0):
    return {"type": "minecraft:stone_depth", "offset": offset, "add_surface_depth": add, "secondary_depth_range": secondary,
            "surface_type": kind}


def _water(offset=-1, mult=0, add=False):
    return {"type": "minecraft:water", "offset": offset, "surface_depth_multiplier": mult, "add_stone_depth": add}


def _noise(nid, lo, hi):
    return {"type": "minecraft:noise_threshold", "noise": f"minecraft:{nid}", "min_threshold": lo, "max_threshold": hi}


def _above(y, mult=0, add=False):
    return {"type": "minecraft:y_above", "anchor": {"absolute": y}, "surface_depth_multiplier": mult, "add_stone_depth": add}


ON_FLOOR = _depth("floor")
UNDER_FLOOR = _depth("floor", add=True)
DEEP_UNDER_FLOOR = _depth("floor", add=True, secondary=6)
ON_CEILING = _depth("ceiling")
ABOVE_WATER = _water(-1, 0)
GRASS = _block("grass_block", {"snowy": "false"})
DIRT = _block("dirt")


def _land(top, under, underwater=None):
    """Top block above water (else `underwater`), `under` below it."""
    return _seq(_if(ON_FLOOR, _seq(_if(ABOVE_WATER, top), underwater or under)), _if(UNDER_FLOOR, under))


SURFACES = {
    "grass": lambda: _land(GRASS, DIRT, _block("dirt")),
    "ocean": lambda: _land(_block("sand"), _block("sand"), _seq(_if(_noise("gravel", -0.2, 0.2), _block("gravel")), _block("sand"))),
    "ocean_cold": lambda: _land(_block("gravel"), _block("gravel"), _seq(_if(_noise("surface", 0.1, 0.4), _block("clay")), _block("gravel"))),
    "ocean_warm": lambda: _land(_block("sand"), _block("sandstone"), _block("sand")),
    "mycelium": lambda: _land(_block("mycelium", {"snowy": "false"}), DIRT),
    "beach": lambda: _land(_block("sand"), _block("sandstone")),
    "snowy_beach": lambda: _land(_block("snow_block"), _block("sand")),
    "basalt": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("surface", -0.15, 0.15), _block("blackstone")),
                                               _block("basalt", {"axis": "y"}))),
                           _if(UNDER_FLOOR, _block("smooth_basalt"))),
    "river": lambda: _land(GRASS, DIRT, _seq(_if(_noise("gravel", -0.1, 0.3), _block("clay")), _block("sand"))),
    "river_frozen": lambda: _land(_block("snow_block"), DIRT, _block("gravel")),
    "snowy_grass": lambda: _land(_seq(_if(_noise("powder_snow", 0.35, 0.6), _block("snow_block")),
                                      _block("grass_block", {"snowy": "true"})), DIRT),
    "glacier": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("packed_ice", -0.5, 0.2), _block("packed_ice")),
                                               _if(_noise("ice", -0.0625, 0.025), _block("blue_ice")), _block("snow_block"))),
                            _if(UNDER_FLOOR, _block("packed_ice"))),
    "snowy_podzol": lambda: _land(_seq(_if(_noise("surface", 0.2, 1.0), _block("podzol", {"snowy": "true"})),
                                       _block("grass_block", {"snowy": "true"})), DIRT),
    "snow_slopes": lambda: _land(_seq(_if(_noise("powder_snow", 0.45, 0.58), _block("powder_snow")), _block("snow_block")),
                                 _block("snow_block"), _block("stone")),
    "peaks": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("packed_ice", 0.0, 0.2), _block("packed_ice")),
                                             _if(_noise("ice", 0.0, 0.025), _block("ice")), _block("snow_block"))),
                          _if(UNDER_FLOOR, _block("snow_block"))),
    "spires": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("calcite", -0.0125, 0.0125), _block("calcite")),
                                              _if(_noise("surface", 0.3, 1.0), _block("andesite")), _block("stone"))),
                           _if(UNDER_FLOOR, _block("stone"))),
    "podzol_patches": lambda: _land(_seq(_if(_noise("surface", 0.21, 1.0), _block("podzol", {"snowy": "false"})),
                                         _if(_noise("surface", -0.95, -0.4), _block("coarse_dirt")), GRASS), DIRT),
    "crags": lambda: _land(_seq(_if(_noise("gravel", 0.2, 1.0), _block("gravel")),
                                _if(_noise("surface", 0.4, 1.0), _block("stone")), GRASS), DIRT, _block("gravel")),
    "marsh": lambda: _land(_seq(_if(_noise("surface_swamp", 0.0, 1.0), _block("mud")), GRASS), DIRT, _block("mud")),
    "savanna": lambda: _land(_seq(_if(_noise("surface", 0.25, 1.0), _block("coarse_dirt")), GRASS), DIRT),
    "rust": lambda: _land(_seq(_if(_noise("surface", 0.3, 1.0), _block("red_terracotta")),
                               _if(_noise("surface", -1.0, -0.4), _block("gravel")), _block("coarse_dirt")),
                          _block("terracotta")),
    "desert": lambda: _land(_block("sand"), _seq(_if(DEEP_UNDER_FLOOR, _block("sandstone")), _block("sand")), _block("sand")),
    "badlands": lambda: _seq(_if(ON_FLOOR, _seq(_if(_above(74, 1), _block("orange_terracotta")), _block("red_sand"))),
                             _if(UNDER_FLOOR, {"type": "minecraft:bandlands"})),
    "cogwork": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("surface", 0.2, 1.0), _block("smooth_sandstone")),
                                               _block("red_sand"))),
                            _if(UNDER_FLOOR, {"type": "minecraft:bandlands"})),
}

# cave floors (applied below the preliminary surface, on any floor in these biomes)
CAVE_SURFACES = {
    "cave_calcite": lambda: _if(ON_FLOOR, _seq(_if(_noise("calcite", -0.2, 0.2), _block("calcite")), _block("stone"))),
    "cave_moss": lambda: _if(ON_FLOOR, _block("moss_block")),
    "cave_sculk": lambda: _if(ON_FLOOR, _seq(_if(_noise("surface", -0.3, 0.3), _block("sculk")), _block("deepslate", {"axis": "y"}))),
    "cave_magma": lambda: _if(ON_FLOOR, _seq(_if(_noise("surface", 0.2, 1.0), _block("magma_block")), _block("basalt", {"axis": "y"}))),
    "cave_mycelium": lambda: _if(ON_FLOOR, _block("mycelium", {"snowy": "false"})),
    "cave_deepslate": lambda: _if(ON_FLOOR, _block("cobbled_deepslate")),
}


def surface_rule():
    by_surface = {}
    cave = {}
    for bid, b in BIOMES.items():
        (cave if b["surface"] in CAVE_SURFACES else by_surface).setdefault(b["surface"], []).append(bid)
    surface_rules = [_if(_biomes(*ids), SURFACES[s]()) for s, ids in by_surface.items() if s != "grass"]
    surface_rules.append(SURFACES["grass"]())
    cave_rules = [_if(_biomes(*ids), CAVE_SURFACES[s]()) for s, ids in cave.items()]
    return _seq(
        _if({"type": "minecraft:vertical_gradient", "random_name": "minecraft:bedrock_floor",
             "true_at_and_below": {"above_bottom": 0}, "false_at_and_above": {"above_bottom": 5}}, _block("bedrock")),
        _if({"type": "minecraft:above_preliminary_surface"}, _seq(*surface_rules)),
        *cave_rules,
        _if({"type": "minecraft:vertical_gradient", "random_name": "minecraft:deepslate",
             "true_at_and_below": {"absolute": 0}, "false_at_and_above": {"absolute": 8}},
            _block("deepslate", {"axis": "y"})),
    )


# ------------------------------------------------------------------ biome json
def biome_json(bid):
    b = dict(BIOMES[bid], id=bid)
    attributes = {
        "minecraft:visual/sky_color": b["sky"],
        "minecraft:visual/fog_color": b["fog"],
        "minecraft:visual/water_fog_color": b["water_fog"],
    }
    attributes.update(WF.attribute_extras(b))
    effects = {"water_color": b["water"]}
    if b["grass"]:
        effects["grass_color"] = b["grass"]
    if b["foliage"]:
        effects["foliage_color"] = b["foliage"]
    return {
        "has_precipitation": b["rain"],
        "temperature": b["temp"],
        "downfall": b["downfall"],
        "attributes": attributes,
        "effects": effects,
        "carvers": WF.carvers(b),
        "features": WF.features(b),
        "spawners": WF.spawners(b["mobs"]),
        "spawn_costs": {},
    }


def _ours(vanilla_ids):
    out = []
    for v in vanilla_ids:
        o = VANILLA_TO_OURS.get(v.split(":")[-1])
        if o and f"{NS}:{o}" not in out:
            out.append(f"{NS}:{o}")
    return out


def write_tags(write):
    """Our biomes join every tag of the vanilla biomes they replace (villages, strongholds, mineshafts, ruined
    portals, mob spawns...), and every Wayfarers structure tag that lists those vanilla biomes."""
    vanilla = json.load(open(os.path.join(os.path.dirname(__file__), "vanilla_biome_tags.json")))
    count = 0
    for tag, entry in vanilla.items():
        values = _ours(entry["biomes"])
        if values:
            write(f"minecraft/tags/worldgen/biome/{tag}.json", {"replace": False, "values": values})
            count += 1
    tags_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "resources", "data", NS, "tags",
                            "worldgen", "biome", "has_structure")
    for name in sorted(os.listdir(tags_dir)):
        listed = [v["id"] if isinstance(v, dict) else v for v in json.load(open(os.path.join(tags_dir, name)))["values"]]
        values = _ours([v for v in listed if not v.startswith("#")])
        if values:
            write(f"{NS}/tags/worldgen/biome/has_structure/{name}", {"replace": False, "values": values})
            count += 1
    return count


def write_biomes(write):
    for bid in BIOMES:
        write(f"{NS}/worldgen/biome/{bid}.json", biome_json(bid))
    WF.write_features(write)
    write_tags(write)
    return len(BIOMES)


def lang():
    en, fr = {}, {}
    for bid, b in BIOMES.items():
        en[f"biome.{NS}.{bid}"], fr[f"biome.{NS}.{bid}"] = b["en"], b["fr"]
    return en, fr
