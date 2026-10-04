"""Wayfarers biomes for the world overhaul (tools/gen_world.py).

Placement: vanilla's climate layout (world_points.json), with every vanilla biome swapped for one of ours through
VANILLA_TO_OURS, and extra cave biomes. Each biome sets its colours, weather, top blocks (surface rules), mobs and
decoration (vanilla placed features plus our own, see worldfeatures.py).
"""
import json
import os

from . import worldfeatures as WF
from .terrain import GLOWCAP_W, MUSHROOM_C

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

# sub-biomes: some vanilla climate cells are split between two of ours (by weirdness or temperature), so the land
# changes more often while staying coherent. Each rule: vanilla -> (test on the point's parameters, our biome);
# the points that fail the test keep VANILLA_TO_OURS. Parameters are [min, max] ranges.
def _lo(r):
    return r if isinstance(r, (int, float)) else r[0]


SPLITS = {
    "mangrove_swamp": (lambda p: True, "crimson_mire"),
    "wooded_badlands": (lambda p: True, "volcanic_highlands"),
    "badlands": (lambda p: _lo(p["weirdness"]) >= 0.0, "ashen_wastes"),
    "desert": (lambda p: _lo(p["weirdness"]) >= 0.05, "pale_dunes"),
    "jagged_peaks": (lambda p: _lo(p["temperature"]) >= -0.15, "alpine_peaks"),
    "windswept_savanna": (lambda p: True, "geyser_basin"),
    "birch_forest": (lambda p: _lo(p["weirdness"]) >= 0.0, "starlight_grove"),
    "pale_garden": (lambda p: True, "aetherblight_grove"),
    "taiga": (lambda p: _lo(p["weirdness"]) >= 0.0, "emberleaf_taiga"),
    "snowy_beach": (lambda p: _lo(p["weirdness"]) < 0.0, "rimefrost_fjords"),
    "warm_ocean": (lambda p: _lo(p["continentalness"]) >= -0.455, "tidebrass_archipelago"),
}


def ours_for(vanilla, params):
    rule = SPLITS.get(vanilla)
    if rule and rule[0](params):
        return rule[1]
    return VANILLA_TO_OURS[vanilla]


def sources():
    """Our biome -> the vanilla biomes whose cells it takes (wiki grouping, biome tags)."""
    out = {}
    for v, o in VANILLA_TO_OURS.items():
        out.setdefault(o, []).append(v)
    for v, (_, o) in SPLITS.items():
        out.setdefault(o, []).append(v)
    return out


# extra cave biomes: (biome, temperature, humidity, continentalness, erosion, weirdness) with depth 0.2..0.9
EXTRA_CAVES = [
    ("fungal_grotto", [-1.0, 1.0], [0.3, 0.7], [-1.0, 1.0], [-1.0, 1.0], [-1.0, -0.6]),
    ("thermal_caves", [0.55, 1.0], [-1.0, 1.0], [0.8, 1.0], [-1.0, 1.0], [-1.0, 1.0]),
    ("mithril_hollows", [-1.0, -0.45], [-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0], [0.6, 1.0]),
]


def B(en, fr, temp, downfall, sky, fog, water, water_fog, grass=None, foliage=None, rain=True, surface="grass",
      decor=(), mobs="plains", music=None, particles=None, cave=False, fog_end=None, particle_rate=0.004):
    """fog_end: a fog distance in blocks (thick fog in mires and wastes), None for the default."""
    return dict(en=en, fr=fr, temp=temp, downfall=downfall, sky=sky, fog=fog, water=water, water_fog=water_fog,
                grass=grass, foliage=foliage, rain=rain, surface=surface, decor=list(decor), mobs=mobs, music=music,
                particles=particles, cave=cave, fog_end=fog_end, particle_rate=particle_rate)


# id -> design. decor: keys of worldfeatures.DECOR (vanilla placed features + ours), mobs: worldfeatures.SPAWNS key
BIOMES = {
    # ---------------------------------------------------------------- oceans and coasts
    "glacial_sea": B("Glacial Sea", "Mer glaciaire", 0.0, 0.5, "#7fa1ff", "#c0d8ff", "#3938c9", "#050533",
                     surface="ocean_cold", decor=["icebergs", "ocean_floor_cold", "kelp_cold"], mobs="frozen_ocean"),
    "slate_sea": B("Slate Sea", "Mer d'ardoise", 0.5, 0.5, "#7ba4ff", "#b6c8e8", "#3d57d6", "#050533",
                   surface="slate_ocean", decor=["ocean_floor_cold", "kelp_cold", "seagrass_deep", "blue_slate_veins"],
                   mobs="cold_ocean"),
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
                        surface="peaks", decor=["ice_spires_small", "marble_strata"], mobs="peaks",
                        particles="minecraft:white_ash"),
    "stone_spires": B("Stone Spires", "Aiguilles de pierre", 1.0, 0.3, "#76a8ff", "#d6d6d6", "#3f76e4", "#050533",
                      surface="spires", decor=["calcite_veins", "marble_strata"], mobs="peaks"),
    # ---------------------------------------------------------------- temperate
    "verdant_meadows": B("Verdant Meadows", "Prairies verdoyantes", 0.8, 0.4, "#78a7ff", "#c0d8ff", "#3f76e4", "#050533",
                         grass="#79c05a", foliage="#59ae30", decor=["meadow_flowers", "lone_oaks", "tall_grass"], mobs="plains"),
    "wildflower_fields": B("Wildflower Fields", "Champs de fleurs sauvages", 0.8, 0.5, "#78a7ff", "#c0d8ff", "#3f76e4", "#050533",
                           grass="#86cc5e", foliage="#59ae30", decor=["wildflowers", "tall_grass", "bee_trees"], mobs="plains"),
    "highland_meadow": B("Highland Meadow", "Alpage", 0.5, 0.8, "#7ba4ff", "#c0d8ff", "#0e4ecf", "#050533",
                         grass="#83bb6d", foliage="#63a948", surface="alpine",
                         decor=["meadow_flowers", "tall_grass", "boulders", "marble_strata"], mobs="meadow"),
    "enchanted_forest": B("Enchanted Forest", "Forêt enchantée", 0.7, 0.8, "#8f9bff", "#c9b8ff", "#7a63e8", "#1d1452",
                          grass="#4fd1a1", foliage="#3fc4c0", decor=["glowwood_trees", "glow_flowers", "glow_lichen"],
                          mobs="enchanted", particles="minecraft:firefly"),
    "elderwood": B("Elderwood", "Bois des anciens", 0.7, 0.8, "#79a6ff", "#c0d8ff", "#3f76e4", "#050533",
                   grass="#5fae45", foliage="#4c9a2a", decor=["great_oaks", "forest_floor"], mobs="forest"),
    "silver_birch_wood": B("Silver Birch Wood", "Bois de bouleaux d'argent", 0.6, 0.6, "#7aa5ff", "#d0e0ff", "#3f76e4", "#050533",
                           grass="#88bb67", foliage="#6ba941", decor=["tall_birches", "forest_floor"], mobs="forest"),
    "crystal_woods": B("Crystal Woods", "Bois de cristal", 0.6, 0.6, "#8fb0ff", "#cdeeff", "#3ad2ff", "#06375a",
                       grass="#6fcfb0", foliage="#7fe0d8",
                       decor=["tall_birches", "glowwood_sparse", "surface_crystals", "glow_flowers"],
                       mobs="forest", particles="minecraft:end_rod"),
    "shadow_woods": B("Shadow Woods", "Bois des ombres", 0.6, 0.8, "#6f7aa8", "#7d8496", "#3a4f6b", "#050533",
                      grass="#4e7a3a", foliage="#3b6a2a", decor=["shadow_oaks", "mushrooms_dense"], mobs="dark_forest",
                      particles="minecraft:ash"),
    "pine_highlands": B("Pine Highlands", "Hautes terres de pins", 0.25, 0.8, "#7fa1ff", "#c8d8ff", "#287082", "#050533",
                        grass="#86b783", foliage="#68a464", surface="pine_slate",
                        decor=["pines", "berry_bushes", "blue_slate_veins"], mobs="taiga"),
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
                       grass="#b0a456", foliage="#a69a46", rain=False, surface="savanna",
                       decor=["acacias", "rustwood_sparse", "dry_grass", "rust_rock_veins"], mobs="savanna"),
    "rustlands": B("Rustlands", "Terres rouillées", 1.2, 0.0, "#8aa8d8", "#d8a07a", "#4f8f8a", "#1b2f2c",
                   grass="#a08646", foliage="#8f7436", rain=False, surface="rust",
                   decor=["steam_vents", "rusted_wrecks", "rustwood_trees", "dry_grass", "rust_rock_veins"],
                   mobs="savanna", particles="minecraft:ash"),
    "emerald_jungle": B("Emerald Jungle", "Jungle d'émeraude", 0.95, 0.9, "#77a8ff", "#c6e8c0", "#14a2c5", "#0a4a55",
                        grass="#59c93c", foliage="#30bb0b", decor=["jungle_giants", "jungle_floor", "melons"], mobs="jungle"),
    "dune_sea": B("Dune Sea", "Mer de dunes", 2.0, 0.0, "#6eb1ff", "#f2dfb4", "#32a598", "#050533", rain=False,
                  surface="desert", decor=["dune_cacti", "dead_bushes", "fossil_bones"], mobs="desert"),
    "painted_canyon": B("Painted Canyon", "Canyon peint", 2.0, 0.0, "#6eb1ff", "#f0c89a", "#3f76e4", "#050533", rain=False,
                        grass="#90814d", foliage="#9e814d", surface="badlands", decor=["dead_bushes", "canyon_cacti"], mobs="badlands"),
    "cogwork_valley": B("Cogwork Valley", "Vallée des engrenages", 1.6, 0.1, "#80a9e0", "#e4c9a0", "#4f8f8a", "#1b2f2c", rain=False,
                        grass="#9e8f4d", foliage="#9e814d", surface="cogwork",
                        decor=["rusted_wrecks", "steam_vents", "acacias", "rustwood_sparse", "rust_rock_veins"],
                        mobs="badlands"),
    # ---------------------------------------------------------------- sub-biomes (SPLITS): Dregora-like moods
    "crimson_mire": B("Crimson Mire", "Marais pourpre", 0.8, 0.9, "#b49494", "#dcc6c2", "#6b2b33", "#2a0c10",
                      grass="#8e4038", foliage="#7a2c2c", surface="crimson_mire",
                      decor=["thorn_spikes", "flat_mushrooms", "crimson_reeds", "lily_pads", "mushrooms_dense"],
                      mobs="swamp", particles="minecraft:crimson_spore", fog_end=96, particle_rate=0.02),
    "volcanic_highlands": B("Volcanic Highlands", "Hautes terres volcaniques", 1.6, 0.0, "#c09878", "#a8826a",
                            "#b0603a", "#3a1a0a", grass="#bba86a", foliage="#d4782a", rain=False, surface="volcanic",
                            decor=["lava_streams", "lava_pools", "sparse_autumn_oaks", "rustwood_sparse", "dry_grass",
                                   "basalt_boulders"],
                            mobs="badlands", particles="minecraft:ash", fog_end=240, particle_rate=0.01),
    "ashen_wastes": B("Ashen Wastes", "Désolation cendrée", 2.0, 0.0, "#a8977e", "#8c7a62", "#5a5a4a", "#1e1c16",
                      grass="#8f8a70", foliage="#7f7a60", rain=False, surface="ashen",
                      decor=["stone_arches", "crystal_shards", "ash_columns", "lava_pools", "lava_streams", "dead_bushes"],
                      mobs="badlands", particles="minecraft:white_ash", fog_end=170, particle_rate=0.03),
    "alpine_peaks": B("Alpine Peaks", "Pics alpins", 0.1, 0.6, "#7fa6ff", "#d8e4f0", "#3d6fd6", "#050533",
                      grass="#76a85c", foliage="#d89a30", surface="alpine_peak",
                      decor=["tall_spruces", "autumn_spruces", "mossy_boulders_many", "fallen_spruce_logs", "ferns"],
                      mobs="peaks"),
    "pale_dunes": B("Pale Dunes", "Dunes pâles", 2.0, 0.0, "#9cc0ff", "#f0e6d4", "#3fa0a8", "#0a3a3e", rain=False,
                    surface="pale_dunes", decor=["hoodoos", "ripple_grass", "dead_bushes"], mobs="desert",
                    fog_end=260),
    "geyser_basin": B("Geyser Basin", "Bassin des geysers", 1.2, 0.4, "#8fb0d8", "#e0dcd0", "#3fd0c8", "#0a4a48",
                      grass="#aaa862", foliage="#9a9a50", surface="geyser",
                      decor=["hot_springs", "steam_vents", "dry_grass", "rust_boulders"], mobs="savanna",
                      particles="minecraft:white_smoke", particle_rate=0.006),
    "starlight_grove": B("Starlight Grove", "Bosquet astral", 0.6, 0.8, "#9a90ff", "#d0c4f0", "#7a6ae0", "#1d1452",
                         grass="#9a86d8", foliage="#b48ae8", surface="starlight",
                         decor=["tall_birches", "glowwood_sparse", "glow_flowers", "surface_crystals",
                                "fallen_glowwood_logs", "crystal_shards"],
                         mobs="enchanted", particles="minecraft:end_rod"),
    "aetherblight_grove": B("Aetherblight Grove", "Bosquet de l'éther corrompu", 0.6, 0.8, "#5a4a7a", "#3e3450",
                            "#3a2a5a", "#120a1e", grass="#4c3a5c", foliage="#5c2c6c", surface="blight",
                            decor=["shadow_oaks", "crystal_shards", "mushrooms_dense", "fallen_glowwood_logs",
                                   "glow_lichen"],
                            mobs="dark_forest", particles="minecraft:portal", fog_end=110, particle_rate=0.02),
    "emberleaf_taiga": B("Emberleaf Taiga", "Taïga aux feuilles de braise", 0.25, 0.8, "#7fa1ff", "#e0d0b8",
                         "#287082", "#050533", grass="#a2a85a", foliage="#e08a28", surface="podzol_patches",
                         decor=["autumn_spruces", "fallen_spruce_logs", "mossy_boulders_many", "berry_bushes", "ferns"],
                         mobs="taiga", particles="minecraft:pale_oak_leaves"),
    "rimefrost_fjords": B("Rimefrost Fjords", "Fjords de givre", -0.3, 0.6, "#7d9bff", "#d6e2f0", "#2f4fa8", "#050533",
                          grass="#80a890", foliage="#60a17b", surface="fjord",
                          decor=["frost_pines_sparse", "slate_boulders", "frost_rocks"], mobs="snowy"),
    "tidebrass_archipelago": B("Tidebrass Archipelago", "Archipel d'airain", 0.9, 0.6, "#7fd0ff", "#d6f6ff",
                               "#20d8c8", "#0a5c63", grass="#5cd04a", foliage="#40c030", surface="archipelago",
                               decor=["warm_ocean_vegetation", "seagrass_warm", "sea_pickles", "palms", "beach_grass"],
                               mobs="warm_ocean"),
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


# scenery added to the original biomes: boulders, fallen logs, rock objects
for _bid, _extra in {
    "elderwood": ["fallen_oak_logs", "mossy_boulders_many"], "giant_sylvan": ["fallen_spruce_logs"],
    "pine_highlands": ["slate_boulders", "fallen_spruce_logs"], "highland_meadow": ["marble_boulders"],
    "painted_canyon": ["hoodoos_sparse"], "rustlands": ["rust_boulders"], "majestic_peaks": ["marble_boulders"],
    "stone_spires": ["marble_boulders"], "shadow_woods": ["fallen_oak_logs"],
    "enchanted_forest": ["fallen_glowwood_logs"], "crystal_woods": ["crystal_shards"],
    "windswept_crags": ["mossy_boulders_many"], "frostpine_forest": ["fallen_spruce_logs"],
    "cogwork_valley": ["rust_boulders"], "silver_birch_wood": ["fallen_oak_logs"],
}.items():
    BIOMES[_bid]["decor"] += [d for d in _extra if d not in BIOMES[_bid]["decor"]]


# ------------------------------------------------------------------ placement
# VANILLA_TO_OURS and SPLITS above say which vanilla biomes each of ours stands for (its tags, the structures it
# hosts, the wiki groups). Where each biome goes is decided here: vanilla's climate layout (world_points.json) keeps
# the terrain roles (oceans, coasts, rivers in the valleys, peaks, slopes, plateaus, windswept hills, swamps), every
# box is cut at our climate bands, and each piece takes the biome of LAYOUT[role][temperature][humidity].
# The temperature and humidity bands get chosen shares of the world (wf/terrain.py remaps the noises: TEMP_CDF,
# VEG_CDF), so each cell of the tables covers a known area; tools/world_preview.py --stats measures the result.
T_EDGES = [-0.45, -0.15, 0.2, 0.55]     # frozen | cold | temperate | warm | hot
H_EDGES = [-0.35, -0.1, 0.1, 0.3]       # arid | dry | medium | humid | wet
# terrain roles of the land boxes, from wf/terrain.py's erosion splines (inland, continentalness >= -0.11):
# summit (the range cores, erosion < -0.55), mountain (< -0.31), plateau (< -0.11, the canyon plateaus, from
# mid-inland: continentalness >= 0.03), wetland (>= 0.62, the swamp spline), low (everything else)
E_EDGES = [-0.55, -0.31, -0.11, 0.62]
C_EDGES = [-0.11, 0.03]
W_SPLIT = 0.0                           # a cell may hold two biomes: (weirdness < 0, weirdness >= 0)

ROLE_OF_VANILLA = {
    "river": "river", "frozen_river": "river",
    "beach": "beach", "snowy_beach": "beach", "stony_shore": "beach",
    "windswept_hills": "shattered", "windswept_gravelly_hills": "shattered", "windswept_forest": "shattered",
    "windswept_savanna": "shattered",
}


def _mid(r):
    return (r[0] + r[1]) / 2.0


def _role(vanilla, p):
    """The terrain role of a (cut) vanilla box: rivers, beaches and windswept hills keep vanilla's places; the rest
    of the land is classed by erosion and continentalness (E_EDGES)."""
    if vanilla in ROLE_OF_VANILLA:
        return ROLE_OF_VANILLA[vanilla]
    if "ocean" in vanilla or vanilla == "mushroom_fields" or "caves" in vanilla or vanilla == "deep_dark":
        return None
    e, c = _mid(p["erosion"]), _mid(p["continentalness"])
    if c < -0.11:
        return "low"                        # the coast band (beaches take most of it)
    if e < -0.55:
        return "summit"
    if e < -0.31:
        return "mountain"
    if e < -0.11 and c >= 0.03:
        return "plateau"
    if e >= 0.62:
        return "wetland"
    return "low"


def _cuts(r, edges):
    a, b = r
    cuts = [a] + [x for x in edges if a < x < b] + [b]
    return list(zip(cuts[:-1], cuts[1:]))


def _band(r, edges):
    return sum(1 for x in edges if _mid(r) >= x)


def _pick(role, ti, hi, p):
    """LAYOUT[role] is a biome, or 5 temperature rows, each a biome or 5 humidity cells; a cell is a biome, a pair
    (weirdness < 0, >= 0) or a function of the box's parameters."""
    cell = LAYOUT[role]
    if isinstance(cell, list):
        cell = cell[ti]
        if isinstance(cell, list):
            cell = cell[hi]
    if callable(cell):
        cell = cell(p)
    if isinstance(cell, tuple):
        cell = cell[0] if _mid(p["weirdness"]) < W_SPLIT else cell[1]
    return cell


def layout_points():
    """(vanilla biome, role, temperature band, humidity band, parameters) for every (cut) box of the layout."""
    rows = json.load(open(os.path.join(os.path.dirname(__file__), "world_points.json")))
    for b, t, h, c, e, d, w, o in rows:
        p = {"temperature": t, "humidity": h, "continentalness": c, "erosion": e, "weirdness": w, "depth": d,
             "offset": o}
        if _role(b, p) is None:
            if c[1] == -1.05 or c[0] == -1.05:      # the mushroom isles reach further out (wf/terrain.py)
                p = dict(p, continentalness=[x if x != -1.05 else MUSHROOM_C for x in c])
            if b == "ocean":                        # and have archipelagos in the temperate seas
                for ww in _cuts(w, [GLOWCAP_W]):
                    yield ("mushroom_fields" if ww[0] >= GLOWCAP_W else b), None, None, None, dict(
                        p, weirdness=list(ww))
                continue
            yield b, None, None, None, p
            continue
        land = b not in ROLE_OF_VANILLA
        river = b in ("river", "frozen_river")
        for tt in _cuts(t, T_EDGES):
            for hh in _cuts(h, H_EDGES):
                for ee in _cuts(e, E_EDGES if land else []):
                    for cc in _cuts(c, C_EDGES if land else []):
                        for ww in _cuts(w, [] if river else [W_SPLIT]):
                            q = dict(p, temperature=list(tt), humidity=list(hh), erosion=list(ee),
                                     continentalness=list(cc), weirdness=list(ww))
                            yield b, _role(b, q), _band(tt, T_EDGES), _band(hh, H_EDGES), q


def _fjord_coast(other):
    """Rimefrost Fjords on the frozen coasts (continentalness < 0.03, weirdness < 0: wf/terrain.py cuts the fjords
    there), `other` inland."""
    return lambda p: "rimefrost_fjords" if _mid(p["continentalness"]) < 0.03 and _mid(p["weirdness"]) < 0 else other


# rows: frozen, cold, temperate, warm, hot; columns: arid, dry, medium, humid, wet; (a, b): weirdness < 0 / >= 0.
# Each cell of `low` is ~2.6% of the land, of `plateau` ~0.4%, of `mountain` ~0.35% (measured, 3 seeds).
LAYOUT = {
    "low": [
        [_fjord_coast("shattered_glacier"), _fjord_coast(("snowcap_slopes", "aurora_tundra")), _fjord_coast("aurora_tundra"),
         _fjord_coast("frostpine_forest"), _fjord_coast("frostpine_forest")],
        [_fjord_coast(("windswept_crags", "highland_meadow")), _fjord_coast(("pine_highlands", "silver_birch_wood")),
         _fjord_coast(("emberleaf_taiga", "pine_highlands")), _fjord_coast(("starlight_grove", "emberleaf_taiga")),
         ("giant_sylvan", "silver_birch_wood")],
        ["verdant_meadows", "wildflower_fields", ("elderwood", "crystal_woods"), ("shadow_woods", "enchanted_forest"),
         "aetherblight_grove"],
        [("dune_sea", "rustlands"), ("ashen_savanna", "geyser_basin"), "geyser_basin", "emerald_jungle", ("glowing_marsh", "crimson_mire")],
        ["pale_dunes", ("painted_canyon", "pale_dunes"), "ashen_wastes", ("volcanic_highlands", "cogwork_valley"),
         "crimson_mire"],
    ],
    "plateau": [
        "snowcap_slopes",
        ["highland_meadow", "highland_meadow", "sakura_valley", "pine_highlands", "giant_sylvan"],
        ["sakura_valley", "sakura_valley", "starlight_grove", "enchanted_forest", "aetherblight_grove"],
        ["painted_canyon", "rustlands", "geyser_basin", "emerald_jungle", "emerald_jungle"],
        ["ashen_wastes", "ashen_wastes", "ashen_wastes", "ashen_wastes", "volcanic_highlands"],
    ],
    "mountain": ["majestic_peaks", "alpine_peaks", ("alpine_peaks", "windswept_crags"), "stone_spires",
                 "volcanic_highlands"],
    "summit": ["majestic_peaks", "alpine_peaks", "alpine_peaks", "stone_spires", "volcanic_highlands"],
    # the swamp flats (erosion > 0.62): marshes where it is wet, dunes and dry savanna where it is not
    "wetland": [
        "aurora_tundra",
        ["pine_highlands", "pine_highlands", "glowing_marsh", "glowing_marsh", "glowing_marsh"],
        ["verdant_meadows", "glowing_marsh", "glowing_marsh", "glowing_marsh", "glowing_marsh"],
        ["dune_sea", "ashen_savanna", "glowing_marsh", "crimson_mire", "crimson_mire"],
        ["pale_dunes", "pale_dunes", "crimson_mire", "crimson_mire", "crimson_mire"],
    ],
    "shattered": ["windswept_crags", "windswept_crags", "windswept_crags", "geyser_basin", "volcanic_highlands"],
}


AXES = ("temperature", "humidity", "continentalness", "erosion", "weirdness")


def merge_boxes(points):
    """Merge boxes of the same biome that touch along one axis and match on the others (fewer points to search)."""
    def key(p, skip):
        q = p["parameters"]
        return (p["biome"], json.dumps(q["depth"]), q["offset"]) + tuple(tuple(q[a]) for a in AXES if a != skip)
    changed = True
    while changed:
        changed = False
        for axis in AXES:
            groups = {}
            for p in points:
                groups.setdefault(key(p, axis), []).append(p)
            out = []
            for g in groups.values():
                g.sort(key=lambda p: p["parameters"][axis][0])
                cur = g[0]
                for p in g[1:]:
                    if abs(p["parameters"][axis][0] - cur["parameters"][axis][1]) < 1e-6:
                        cur = {"biome": cur["biome"], "parameters": dict(
                            cur["parameters"], **{axis: [cur["parameters"][axis][0], p["parameters"][axis][1]]})}
                        changed = True
                    else:
                        out.append(cur)
                        cur = p
                out.append(cur)
            points = out
    return points


def climate_points():
    out = []
    for b, role, ti, hi, p in layout_points():
        # oceans, rivers and beaches keep the plain swap (their vanilla boxes already follow our temperature bands)
        ours = ours_for(b, p) if role in (None, "river", "beach") else _pick(role, ti, hi, p)
        if role == "beach" and ti <= 1 and _mid(p["weirdness"]) < 0:
            ours = "rimefrost_fjords"           # the fjord cliffs replace the cold beaches (wf/terrain.py)
        out.append({"biome": f"{NS}:{ours}", "parameters": {
            k: p[k] for k in ("temperature", "humidity", "continentalness", "erosion", "depth", "weirdness", "offset")}})
    out = merge_boxes(out)
    for biome, t, h, c, e, w in EXTRA_CAVES:
        out.append({"biome": f"{NS}:{biome}", "parameters": {
            "temperature": t, "humidity": h, "continentalness": c, "erosion": e, "depth": [0.2, 0.9], "weirdness": w,
            "offset": 0.0}})
    return out


# ------------------------------------------------------------------ surface rules
def _block(name, props=None):
    if "[" in name:                 # 'basalt[axis=y]': the properties go to Properties, not into the id
        name, rest = name.rstrip("]").split("[", 1)
        props = dict(dict(kv.split("=") for kv in rest.split(",") if kv), **(props or {}))
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


def _wnoise(nid, lo, hi):
    """A threshold on one of our surface noises (wf/terrain.py NOISES). Surface noises are 2D (sampled at y 0),
    so on a cliff they draw vertical stripes."""
    return {"type": "minecraft:noise_threshold", "noise": f"{NS}:{nid}", "min_threshold": lo, "max_threshold": hi}


def _ybands(blocks, y0, y1, step, base):
    """Horizontal rock bands cycling through `blocks` from y0 to y1, `step` blocks each (wavering with the surface
    depth), `base` elsewhere: stratified cliffs."""
    bands = []
    y, i = y0, 0
    while y < y1:
        bands.append((y, blocks[i % len(blocks)]))
        y += step
        i += 1

    def tree(lo, hi):          # bands[lo:hi], the y is known to be inside them: one check per level
        if hi - lo == 1:
            return _block(bands[lo][1])
        mid = (lo + hi) // 2
        return _seq(_if(_above(bands[mid][0], 1), tree(mid, hi)), tree(lo, mid))
    return _seq(_if(_above(y0, 1), _if(_not(_above(y, 1)), tree(0, len(bands)))), _block(base))


STEEP = {"type": "minecraft:steep"}
ON_FLOOR = _depth("floor")
UNDER_FLOOR = _depth("floor", add=True)
DEEP_UNDER_FLOOR = _depth("floor", add=True, secondary=6)
ON_CEILING = _depth("ceiling")
ABOVE_WATER = _water(-1, 0)
GRASS = _block("grass_block", {"snowy": "false"})
DIRT = _block("dirt")


def _strata(stone, bands, base="stone"):
    """Horizontal bands of `stone` in a cliff face (the rest `base`): a mountain's rock strata. Each band is shifted
    by the local surface depth, so it wavers a little along the slope."""
    rules = [_if(_above(lo, 1), _if(_not(_above(hi, 1)), _block(stone))) for lo, hi in bands]
    return _seq(*rules, _block(base))


MARBLE = "wayfarers:marble"
MARBLE_BANDS = [(92, 96), (109, 112), (127, 132), (146, 149), (165, 170), (186, 189), (207, 212), (231, 234),
                (254, 259), (279, 283)]


# ochre mountains: orange, yellow and plain terracotta, brown and red streaks, a dark basalt seam now and then
VOLCANIC_BANDS = ["orange_terracotta", "terracotta", "brown_terracotta", "orange_terracotta", "yellow_terracotta",
                  "terracotta", "red_terracotta", "orange_terracotta", "brown_terracotta", "terracotta",
                  "basalt[axis=y]", "orange_terracotta", "yellow_terracotta", "brown_terracotta"]
ASH_BANDS = ["tuff", "deepslate[axis=y]", "andesite", "smooth_basalt", "tuff", "cobbled_deepslate", "stone",
             "deepslate[axis=y]", "polished_andesite", "basalt[axis=y]", "tuff", "light_gray_terracotta"]
CLIFF_BANDS = ["stone", "andesite", "stone", "tuff", "stone", "stone", "andesite", "wayfarers:marble", "stone",
               "cobblestone", "stone", "tuff"]

# land biomes that get the generic highland look: bare banded rock on cliffs above y ~100, snow above y ~205
HIGHLAND_SURFACES = {"grass", "alpine", "pine_slate", "podzol_patches", "crags", "snowy_grass", "snowy_podzol",
                     "starlight", "blight", "marsh", "crimson_mire", "mycelium", "river", "fjord", "savanna"}


def _striated():
    """Alpine rock: vertical stripes (2D noise, constant down a face) of tuff, gravel, andesite and diorite in
    stone, moss in the gullies."""
    return _seq(_if(_wnoise("moss_streak", 0.42, 1.0), _block("moss_block")),
                _if(_wnoise("striation", -1.0, -0.35), _block("tuff")),
                _if(_wnoise("striation", -0.35, -0.2), _block("gravel")),
                _if(_wnoise("striation", 0.2, 0.4), _block("andesite")),
                _if(_wnoise("striation", 0.55, 1.0), _block("diorite")),
                _block("stone"))


def highland():
    snow = _seq(_if(_noise("powder_snow", 0.45, 0.58), _block("powder_snow")), _block("snow_block"))
    return _seq(
        _if(STEEP, _if(_above(96, 2), _if(UNDER_FLOOR, _ybands(CLIFF_BANDS, 96, 340, 5, "stone")))),
        _if(ON_FLOOR, _if(_above(205, 3), snow)),
        _if(UNDER_FLOOR, _if(_above(215, 3), _block("snow_block"))))


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
    "peaks": lambda: _seq(_if(STEEP, _if(UNDER_FLOOR, _strata(MARBLE, MARBLE_BANDS))),
                          _if(ON_FLOOR, _seq(_if(_noise("packed_ice", 0.0, 0.2), _block("packed_ice")),
                                             _if(_noise("ice", 0.0, 0.025), _block("ice")), _block("snow_block"))),
                          _if(UNDER_FLOOR, _block("snow_block"))),
    "spires": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("calcite", -0.0125, 0.0125), _block("calcite")),
                                              _if(_noise("surface", 0.3, 1.0), _block("andesite")),
                                              _strata(MARBLE, MARBLE_BANDS))),
                           _if(UNDER_FLOOR, _strata(MARBLE, MARBLE_BANDS))),
    # alpine meadow: grass, with marble bands in the steep banks and a few bare marble outcrops
    "alpine": lambda: _seq(_if(STEEP, _if(UNDER_FLOOR, _strata(MARBLE, MARBLE_BANDS))),
                           _if(ON_FLOOR, _if(_noise("surface", 0.62, 1.0), _block(MARBLE))),
                           _land(GRASS, DIRT, _block("dirt"))),
    # pine highlands: podzol and grass over blue slate, which shows in every steep bank and in a few outcrops
    "pine_slate": lambda: _seq(_if(STEEP, _if(UNDER_FLOOR, _block("wayfarers:blue_slate"))),
                               _if(ON_FLOOR, _if(_noise("surface", -0.7, -0.52), _block("wayfarers:blue_slate"))),
                               _land(_seq(_if(_noise("surface", 0.21, 1.0), _block("podzol", {"snowy": "false"})),
                                          _if(_noise("surface", -0.95, -0.7), _block("coarse_dirt")), GRASS), DIRT)),
    # slate sea: a floor of gravel and blue slate (clay in places), blue slate shores
    "slate_ocean": lambda: _land(_seq(_if(_noise("surface", -0.3, 0.25), _block("wayfarers:blue_slate")), _block("gravel")),
                                 _block("wayfarers:blue_slate"),
                                 _seq(_if(_noise("surface", 0.1, 0.4), _block("clay")),
                                      _if(_noise("gravel", -0.35, 0.3), _block("wayfarers:blue_slate")), _block("gravel"))),
    "podzol_patches": lambda: _land(_seq(_if(_noise("surface", 0.21, 1.0), _block("podzol", {"snowy": "false"})),
                                         _if(_noise("surface", -0.95, -0.4), _block("coarse_dirt")), GRASS), DIRT),
    "crags": lambda: _land(_seq(_if(_noise("gravel", 0.2, 1.0), _block("gravel")),
                                _if(_noise("surface", 0.4, 1.0), _block("stone")), GRASS), DIRT, _block("gravel")),
    "marsh": lambda: _land(_seq(_if(_noise("surface_swamp", 0.0, 1.0), _block("mud")), GRASS), DIRT, _block("mud")),
    "savanna": lambda: _land(_seq(_if(_noise("surface", 0.25, 1.0), _block("coarse_dirt")), GRASS), DIRT),
    "rust": lambda: _seq(_if(STEEP, _if(UNDER_FLOOR, _block("wayfarers:rust_rock"))),
                         _land(_seq(_if(_noise("surface", 0.3, 1.0), _block("wayfarers:rust_rock")),
                                    _if(_noise("surface", 0.15, 0.3), _block("red_terracotta")),
                                    _if(_noise("surface", -1.0, -0.4), _block("gravel")), _block("coarse_dirt")),
                               _seq(_if(_noise("surface", -0.2, 0.2), _block("terracotta")), _block("wayfarers:rust_rock")))),
    "desert": lambda: _land(_block("sand"), _seq(_if(DEEP_UNDER_FLOOR, _block("sandstone")), _block("sand")), _block("sand")),
    "badlands": lambda: _seq(_if(STEEP, {"type": "minecraft:bandlands"}),
                             _if(ON_FLOOR, _seq(_if(_above(74, 1), _block("orange_terracotta")), _block("red_sand"))),
                             {"type": "minecraft:bandlands"}),       # banded cliffs at any depth
    # Crimson Mire: mud and blood-red nylium patches, podzol, mud under shallow water
    "crimson_mire": lambda: _land(_seq(_if(_noise("surface", 0.05, 1.0), _block("crimson_nylium")),
                                       _if(_noise("surface_swamp", 0.0, 1.0), _block("mud")),
                                       _if(_noise("surface", -1.0, -0.55), _block("podzol", {"snowy": "false"})), GRASS),
                                  _block("mud"), _block("mud")),
    # Volcanic Highlands: ochre terracotta cliffs banded with brown, red and basalt (at any depth, so whole faces
    # show them, like the badlands and the ashen plateaus); tan grass, coarse dirt,
    # blackstone and magma on the slopes
    "volcanic": lambda: _seq(
        _if(STEEP, _ybands(VOLCANIC_BANDS, 60, 330, 4, "brown_terracotta")),
        _if(ON_FLOOR, _seq(_if(_noise("surface", -1.0, -0.62), _block("blackstone")),
                           _if(_noise("surface", -0.62, -0.57), _block("magma_block")),
                           _if(_noise("surface", 0.35, 1.0), _block("coarse_dirt")),
                           _if(_above(150, 2), _block("brown_terracotta")),
                           _if(ABOVE_WATER, GRASS), _block("blackstone"))),
        _ybands(VOLCANIC_BANDS, 60, 330, 4, "brown_terracotta")),
    # Ashen Wastes: stratified dark grey plateaus, white ash streaks on the tops, gravel and tuff
    "ashen": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(STEEP, _ybands(ASH_BANDS, 40, 330, 3, "tuff")),
                           _if(_wnoise("striation", 0.25, 1.0), _block("calcite")),
                           _if(_noise("surface", 0.3, 1.0), _block("light_gray_concrete_powder")),
                           _if(_noise("surface", -1.0, -0.4), _block("gravel")),
                           _ybands(ASH_BANDS, 40, 330, 3, "tuff"))),
        _ybands(ASH_BANDS, 40, 330, 3, "tuff")),
    # Alpine Peaks: bare rock above y ~170 and on every steep face (at any depth), striated: the 2D striation noise
    # draws vertical stripes of stone, tuff, gravel, andesite and diorite down the faces, moss in the gullies;
    # meadow grass and podzol below, snow from y ~200
    "alpine_peak": lambda: _seq(
        _if(STEEP, _if(_above(80), _striated())),
        _if(ON_FLOOR, _seq(_if(_above(200, 3), _seq(_if(_noise("powder_snow", 0.45, 0.58), _block("powder_snow")),
                                                     _block("snow_block"))),
                           _if(_wnoise("moss_streak", 0.5, 1.0), _block("moss_block")),
                           _if(_above(170, 2), _striated()),
                           _if(_noise("surface", 0.3, 1.0), _block("podzol", {"snowy": "false"})),
                           _if(ABOVE_WATER, GRASS), _block("gravel"))),
        _if(_above(170, 2), _striated()),
        _if(UNDER_FLOOR, DIRT)),
    # Pale Dunes: pale white sand rippled with ordinary sand, sandstone underneath
    "pale_dunes": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(_wnoise("striation", -0.2, 0.25), _block("sand")),
                           _block("white_concrete_powder"))),
        _if(UNDER_FLOOR, _seq(_if(DEEP_UNDER_FLOOR, _block("smooth_sandstone")), _block("white_concrete_powder")))),
    # Geyser Basin: travertine (calcite) crusts ringed with yellow and orange, tan grass between the springs
    "geyser": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(_noise("surface", -0.12, -0.04), _block("orange_terracotta")),
                           _if(_noise("surface", -0.04, 0.04), _block("yellow_terracotta")),
                           _if(_noise("surface", 0.04, 0.3), _block("calcite")),
                           _if(_noise("surface", 0.3, 0.36), _block("white_terracotta")),
                           _if(ABOVE_WATER, GRASS), _block("calcite"))),
        _if(UNDER_FLOOR, _block("calcite"))),
    # Starlight Grove: lavender grass, moss and amethyst-flecked ground
    "starlight": lambda: _land(_seq(_if(_noise("surface", 0.4, 1.0), _block("moss_block")),
                                    _if(_noise("surface", -0.05, 0.0), _block("amethyst_block")), GRASS), DIRT),
    # Aetherblight Grove: corrupted ground: mycelium and podzol, blackstone in the banks
    "blight": lambda: _seq(_if(STEEP, _if(UNDER_FLOOR, _block("blackstone"))),
                           _land(_seq(_if(_noise("surface", 0.15, 1.0), _block("mycelium", {"snowy": "false"})),
                                      _if(_noise("surface", -1.0, -0.4), _block("podzol", {"snowy": "false"})),
                                      _if(_noise("surface", -0.05, 0.0), _block("crying_obsidian")), GRASS),
                                 DIRT)),
    # Rimefrost Fjords: blue slate and stone cliffs, snowy tops, gravel shores
    "fjord": lambda: _seq(
        _if(STEEP, _if(_above(40), _ybands(["wayfarers:blue_slate", "stone", "wayfarers:blue_slate", "andesite"],
                                            30, 200, 5, "stone"))),
        _if(ON_FLOOR, _seq(_if(_not(_above(66, 1)), _block("gravel")),
                           _if(_noise("powder_snow", 0.35, 0.6), _block("snow_block")),
                           _block("grass_block", {"snowy": "true"}))),
        _if(UNDER_FLOOR, _seq(_if(_not(_above(66, 1)), _block("gravel")), DIRT))),
    # Tidebrass Archipelago: grassy island tops with sand beaches, sand sea floor
    "archipelago": lambda: _seq(
        _if(ON_FLOOR, _seq(_if(_above(67, 2), _if(ABOVE_WATER, GRASS)), _block("sand"))),
        _if(UNDER_FLOOR, _seq(_if(_above(67, 2), DIRT), _block("sandstone")))),
    "cogwork": lambda: _seq(_if(ON_FLOOR, _seq(_if(_noise("surface", 0.2, 1.0), _block("smooth_sandstone")),
                                               _if(_noise("surface", -1.0, -0.6), _block("wayfarers:rust_rock")),
                                               _block("red_sand"))),
                            {"type": "minecraft:bandlands"}),
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
    high = sorted(bid for s, ids in by_surface.items() if s in HIGHLAND_SURFACES for bid in ids)
    surface_rules = [_if(_biomes(*high), highland())]
    surface_rules += [_if(_biomes(*ids), SURFACES[s]()) for s, ids in by_surface.items() if s != "grass"]
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
        short = v.split(":")[-1]
        targets = [VANILLA_TO_OURS.get(short)] + ([SPLITS[short][1]] if short in SPLITS else [])
        for o in targets:
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
