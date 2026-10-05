"""Living oceans: sea creatures, sea-floor scenery, diving gear (one table for names, recipes, loot, worldgen,
textures and manual pages, like gadgets.py).

Java: registry/ModOcean.java (blocks, items, spawn eggs, the bubble_vent feature), entity/ocean/* and
ModEntities (creatures), event/OceanEvents.java (the Sea Serpent rises near boats at night; Glow Jelly brewing).

Everything placed in the world is in the mod's own data: Forge biome modifiers add the spawns and the features to
biome tags (data/brasshaven/tags/worldgen/biome/ocean/*) that list the vanilla oceans.
"""
import math
import random

from .png import Canvas
from .texgen import mix, mul

NS = "brasshaven"

# ------------------------------------------------------------------ names
# id -> (english, french, tooltip en, tooltip fr)
ITEMS = {
    "glow_jelly": ("Glow Jelly", "Gelée lumineuse",
                   "Dropped by Glow Jellyfish. Brews Night Vision; four around glass make a Jelly Lamp.",
                   "Lâchée par les méduses lumineuses. Infusée : vision nocturne ; quatre autour d'un verre : une lampe."),
    "pearl": ("Pearl", "Perle", "From a Pearl Oyster. Four pearls trade for an emerald at the crafting table.",
              "Tirée d'une huître perlière. Quatre perles valent une émeraude à l'établi."),
    "serpent_scale": ("Sea Serpent Scale", "Écaille de serpent de mer",
                      "Trophy of the Sea Serpent. Four make a Diving Helmet.",
                      "Trophée du serpent de mer. Quatre font un casque de scaphandre."),
    "diving_helmet": ("Diving Helmet", "Casque de scaphandre",
                      "Head under water: Conduit Power (breathing, clear sight, full mining speed).",
                      "Tête sous l'eau : force de conduit (respiration, vue dégagée, minage à pleine vitesse)."),
    "flippers": ("Flippers", "Palmes", "Swim much faster (like Depth Strider II).",
                 "Nage bien plus vite (comme Agilité aquatique II)."),
    "reef_fish_bucket": ("Bucket of Reef Fish", "Seau de poisson de récif", "", ""),
}
# block id -> (english, french, tooltip en, tooltip fr)
BLOCKS = {
    "glow_anemone": ("Glow Anemone", "Anémone lumineuse", "Glows under water. Three colours.",
                     "Brille sous l'eau. Trois couleurs."),
    "pearl_oyster": ("Pearl Oyster", "Huître perlière",
                     "Right-click an open shell to take its pearl. Under water it grows a new one.",
                     "Clic droit sur une coquille entrouverte pour prendre sa perle. Sous l'eau, elle en refait une."),
    "jelly_lamp": ("Jelly Lamp", "Lampe de gelée", "A wobbly block of glowing jelly (light 15).",
                   "Un bloc de gelée lumineuse tremblotant (lumière 15)."),
}
ENTITIES = {
    "glow_jellyfish": ("Glow Jellyfish", "Méduse lumineuse"),
    "reef_fish": ("Reef Fish", "Poisson de récif"),
    "manta_ray": ("Manta Ray", "Raie manta"),
    "sea_serpent": ("Sea Serpent", "Serpent de mer"),
    "whale": ("Humpback Whale", "Baleine à bosse"),
}
# spawn egg colours (base, spots), merged into gen_textures.EGGS
EGGS = {
    "glow_jellyfish": ((232, 110, 186), (140, 236, 255)),
    "reef_fish": ((255, 214, 40), (40, 96, 230)),
    "manta_ray": ((44, 52, 70), (232, 234, 238)),
    "sea_serpent": ((26, 92, 102), (186, 40, 52)),
    "whale": ((46, 58, 76), (226, 230, 232)),
}
MESSAGES = {
    "message.brasshaven.sea_serpent.rises": ("Something huge stirs beneath the waves...",
                                            "Quelque chose d'énorme remue sous les vagues..."),
}
# block-state properties of our blocks, for validate.py (structure templates)
MOD_STATES = {
    "glow_anemone": {"color": ["0", "1", "2"], "waterlogged": ["false", "true"]},
    "pearl_oyster": {"facing": ["north", "south", "east", "west"], "pearl": ["false", "true"],
                     "waterlogged": ["false", "true"]},
    "jelly_lamp": {},
}
MOD_ITEMS = set(ITEMS) | set(BLOCKS) | {"brass_ingot"}


def register_content(items, entities, spawn_eggs):
    """content.py: item names/tooltips, creature names and spawn eggs."""
    items.update(ITEMS)
    entities.update(ENTITIES)
    for mob in ENTITIES:
        if mob not in spawn_eggs:
            spawn_eggs.append(mob)


def lang():
    en, fr = {}, {}
    for bid, (e, f, te, tf) in BLOCKS.items():
        en[f"block.{NS}.{bid}"], fr[f"block.{NS}.{bid}"] = e, f
        if te:
            en[f"block.{NS}.{bid}.desc"], fr[f"block.{NS}.{bid}.desc"] = te, tf
    for key, (e, f) in MESSAGES.items():
        en[key], fr[key] = e, f
    return en, fr


# ------------------------------------------------------------------ recipes and tags (gen_data.py)
def recipes(shaped, shapeless, write):
    shaped("diving_helmet", ["SBS", "SGS"], {"S": "serpent_scale", "B": "brass_ingot", "G": "glass"},
           category="equipment")
    write(f"{NS}/recipe/diving_helmet_from_copper.json", {
        "type": "minecraft:crafting_shaped", "category": "equipment", "pattern": ["BCB", "CGC"],
        "key": {"B": f"{NS}:brass_ingot", "C": "minecraft:copper_block", "G": "minecraft:glass"},
        "result": {"id": f"{NS}:diving_helmet", "count": 1}})
    shaped("flippers", ["L L", "K K"], {"L": "leather", "K": "dried_kelp_block"}, category="equipment")
    shaped("jelly_lamp", [" J ", "JGJ", " J "], {"J": "glow_jelly", "G": "glass"}, category="building")
    write(f"{NS}/recipe/emerald_from_pearls.json", {
        "type": "minecraft:crafting_shaped", "category": "misc", "pattern": ["PP", "PP"],
        "key": {"P": f"{NS}:pearl"}, "result": {"id": "minecraft:emerald", "count": 1}})


def tags(write):
    """Writes our own tag files; returns the values to merge into shared vanilla tag files (gen_data merges them)."""
    write(f"{NS}/tags/item/diving_repair_materials.json", {"values": [f"{NS}:serpent_scale", f"{NS}:brass_ingot"]})
    return {"minecraft/tags/item/head_armor.json": [f"{NS}:diving_helmet"],
            "minecraft/tags/item/foot_armor.json": [f"{NS}:flippers"],
            "minecraft/tags/block/mineable/pickaxe.json": [f"{NS}:pearl_oyster"]}


# ------------------------------------------------------------------ loot (gen_data.py)
def _pool(name, lo=1, hi=1, chance=None, looting=False):
    e = {"type": "minecraft:item", "name": name if ":" in name else f"minecraft:{name}"}
    fns = []
    if (lo, hi) != (1, 1):
        fns.append({"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi},
                    "add": False})
    if looting:
        fns.append({"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
                    "count": {"type": "minecraft:uniform", "min": 0, "max": 1}})
    if fns:
        e["functions"] = fns
    pool = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [e]}
    if chance is not None:
        pool["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance}]
    return pool


def loot(write):
    entities = {
        "glow_jellyfish": [_pool(f"{NS}:glow_jelly", 1, 2, looting=True)],
        "reef_fish": [_pool("tropical_fish"), _pool("bone_meal", chance=0.05)],
        "manta_ray": [_pool("leather", 1, 3, looting=True), _pool("prismarine_crystals", 0, 2)],
        "whale": [_pool("bone", 4, 8), _pool("nautilus_shell", chance=0.3), _pool("prismarine_crystals", 2, 6)],
        "sea_serpent": [_pool(f"{NS}:serpent_scale", 3, 6, looting=True), _pool("prismarine_crystals", 2, 5),
                        _pool("heart_of_the_sea", chance=0.2), _pool("nautilus_shell", 1, 2)],
    }
    for name, pools in entities.items():
        write(f"{NS}/loot_table/entities/{name}.json", {"type": "minecraft:entity", "pools": pools,
                                                        "random_sequence": f"{NS}:entities/{name}"})

    def drop_self(bid, extra=None):
        pools = [{"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                  "entries": [{"type": "minecraft:item", "name": f"{NS}:{bid}"}]}]
        if extra:
            pools.append(extra)
        write(f"{NS}/loot_table/blocks/{bid}.json", {"type": "minecraft:block", "pools": pools,
                                                     "random_sequence": f"{NS}:blocks/{bid}"})
    drop_self("glow_anemone")
    drop_self("jelly_lamp")
    drop_self("pearl_oyster", {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{"type": "minecraft:item", "name": f"{NS}:pearl"}],
                               "conditions": [{"condition": "minecraft:block_state_property", "block": f"{NS}:pearl_oyster",
                                               "properties": {"pearl": "true"}}]})


# ------------------------------------------------------------------ worldgen (gen_data.py)
# biome tags of vanilla oceans
OCEAN_TAGS = {
    "all": ["ocean", "deep_ocean", "cold_ocean", "deep_cold_ocean", "lukewarm_ocean", "deep_lukewarm_ocean",
            "warm_ocean"],
    "cold": ["cold_ocean", "deep_cold_ocean", "frozen_ocean", "deep_frozen_ocean"],
    "temperate": ["ocean", "deep_ocean"],
    "warm": ["warm_ocean", "lukewarm_ocean", "deep_lukewarm_ocean"],
    "coral": ["warm_ocean"],
    "manta": ["ocean", "deep_ocean", "warm_ocean", "lukewarm_ocean", "deep_lukewarm_ocean"],
    "deep": ["deep_ocean", "deep_cold_ocean", "deep_lukewarm_ocean", "deep_frozen_ocean"],
}

# spawns per biome tag: (tag, entity, weight, min, max). Balance: vanilla oceans have cod 10-15 and squid 1-10
# (water_ambient / water_creature caps 20 / 5 per player), so these add life without crowding the caps.
SPAWNS = [
    ("all", "glow_jellyfish", 8, 2, 4),
    ("warm", "reef_fish", 22, 5, 9),
    ("manta", "manta_ray", 2, 1, 1),
    ("whales", "whale", 1, 1, 1),
]

FLOOR = [{"type": "minecraft:in_square"}, {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR_WG"}]
BIOME = {"type": "minecraft:biome"}


def _water_at(dy):
    return {"type": "minecraft:matching_fluids", "fluids": "minecraft:water", "offset": [0, dy, 0]}


def _patch(per_chunk, size, spread, state_ok):
    """Clusters: ``per_chunk`` centres, ``size`` copies each scattered within ``spread`` blocks, every copy snapped
    to the sea floor and kept only where ``state_ok`` would survive in water."""
    return [{"type": "minecraft:count", "count": per_chunk}, {"type": "minecraft:in_square"},
            {"type": "minecraft:count", "count": size},
            {"type": "minecraft:random_offset",
             "xz_spread": {"type": "minecraft:uniform", "min_inclusive": -spread, "max_inclusive": spread},
             "y_spread": 0},
            {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR_WG"},
            {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
                {"type": "minecraft:matching_blocks", "blocks": "minecraft:water"},
                {"type": "minecraft:would_survive", "state": state_ok}]}},
            BIOME]


def _templates(names, weight=None):
    return {"type": "minecraft:template", "config": {"templates": [
        {"data": {"id": f"{NS}:ocean/{n}"}, "weight": (weight or {}).get(n, 1)} for n in names]}}


# id -> (configured feature, placement, generation step, biome tag)
def features():
    anemone = [{"data": {"Name": f"{NS}:glow_anemone", "Properties": {"color": str(c), "waterlogged": "true"}},
                "weight": w} for c, w in ((0, 3), (1, 3), (2, 2))]
    oyster = [{"data": {"Name": f"{NS}:pearl_oyster", "Properties": {"facing": f, "pearl": p, "waterlogged": "true"}},
               "weight": 3 if p == "true" else 1}
              for f in ("north", "south", "east", "west") for p in ("true", "false")]
    return {
        # dense, patchy kelp forests in cold and temperate seas (vanilla's own kelp, more of it, in clumps)
        "ocean_kelp_forest": ({"type": "minecraft:kelp", "config": {}},
                              [{"type": "minecraft:noise_threshold_count", "noise_level": 0.2, "below_noise": 0,
                                "above_noise": 90}] + FLOOR + [BIOME], "vegetal_decoration", "kelp"),
        # sea-grass meadows: thick tufts in wide patches
        "ocean_seagrass_meadow": ({"type": "minecraft:seagrass", "config": {"probability": 0.6}},
                                  [{"type": "minecraft:noise_threshold_count", "noise_level": -0.3, "below_noise": 4,
                                    "above_noise": 48}] + FLOOR + [BIOME], "vegetal_decoration", "meadow"),
        # coral gardens: vanilla's coral trees, claws and mushrooms, many more of them in the warmest seas
        "ocean_coral_garden": ("minecraft:warm_ocean_vegetation",
                               [{"type": "minecraft:noise_based_count", "noise_to_count_ratio": 30,
                                 "noise_factor": 160.0, "noise_offset": 0.3}] + FLOOR + [BIOME],
                               "vegetal_decoration", "coral"),
        # giant corals: towers, fans and arches of coral blocks (templates below)
        "ocean_giant_coral": (_templates(["coral_tower", "coral_fan", "coral_arch", "coral_brain"]),
                              [{"type": "minecraft:rarity_filter", "chance": 4}] + FLOOR
                              + [{"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -4},
                                 {"type": "minecraft:block_predicate_filter", "predicate": _water_at(15)}, BIOME],
                              "local_modifications", "coral"),
        # glowing anemone patches on every sea floor
        "ocean_anemones": ({"type": "minecraft:simple_block", "config": {"to_place": {
            "type": "minecraft:weighted_state_provider", "entries": anemone}}},
            _patch({"type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 2}, 6, 3,
                   {"Name": f"{NS}:glow_anemone", "Properties": {"color": "0", "waterlogged": "true"}}),
            "vegetal_decoration", "all"),
        # pearl oyster beds
        "ocean_oyster_beds": ({"type": "minecraft:simple_block", "config": {"to_place": {
            "type": "minecraft:weighted_state_provider", "entries": oyster}}},
            [{"type": "minecraft:rarity_filter", "chance": 3}] + _patch(1, 5, 2, {
                "Name": f"{NS}:pearl_oyster", "Properties": {"facing": "north", "pearl": "true", "waterlogged": "true"}}),
            "vegetal_decoration", "oysters"),
        # hydrothermal vents: basalt chimneys over magma, upward bubble columns to the surface (Java feature)
        "ocean_bubble_vents": ({"type": f"{NS}:bubble_vent", "config": {}},
                               [{"type": "minecraft:rarity_filter", "chance": 20}] + FLOOR + [BIOME],
                               "local_modifications", "all"),
        # rock arches, sea stacks and pillars standing on the sea floor (templates below)
        "ocean_rock_formations": (_templates(["rock_arch", "rock_pillars", "rock_stack", "rock_ring"]),
                                  [{"type": "minecraft:rarity_filter", "chance": 9}] + FLOOR
                                  + [{"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -4},
                                     {"type": "minecraft:block_predicate_filter", "predicate": _water_at(15)}, BIOME],
                                  "local_modifications", "all"),
        # small sunken ruins: broken colonnades, a fallen statue, a sunken stair, an amphora heap
        "ocean_sunken_ruins": (_templates(["ruin_colonnade", "ruin_statue", "ruin_stair", "ruin_amphorae"]),
                               [{"type": "minecraft:rarity_filter", "chance": 14}] + FLOOR
                               + [{"type": "minecraft:random_offset", "xz_spread": 0, "y_spread": -4},
                                  {"type": "minecraft:block_predicate_filter", "predicate": _water_at(10)}, BIOME],
                               "surface_structures", "all"),
    }


# biome-modifier tags of the features (a feature may need a tag of its own)
FEATURE_TAGS = {
    # whales stay out of frozen seas: there squid are the only other big swimmer, so whales would be half of all spawns
    "whales": [b for b in OCEAN_TAGS["deep"] if "frozen" not in b],
    "kelp": OCEAN_TAGS["cold"] + OCEAN_TAGS["temperate"],
    "meadow": OCEAN_TAGS["temperate"] + OCEAN_TAGS["warm"],
    "oysters": OCEAN_TAGS["temperate"] + OCEAN_TAGS["warm"],
}


def _tag_values(ids):
    return {"replace": False, "values": [b if ":" in b else f"minecraft:{b}" for b in ids]}


def worldgen(write):
    """Biome tags, features and the Forge biome modifiers that add creatures and scenery to every ocean."""
    tags = dict(OCEAN_TAGS)
    tags.update(FEATURE_TAGS)
    for name, ids in tags.items():
        write(f"{NS}/tags/worldgen/biome/ocean/{name}.json", _tag_values(ids))
    for tag, mob, weight, lo, hi in SPAWNS:
        write(f"{NS}/forge/biome_modifier/ocean_spawn_{mob}.json", {
            "type": "forge:add_spawns", "biomes": f"#{NS}:ocean/{tag}",
            "spawners": [{"type": f"{NS}:{mob}", "weight": weight, "minCount": lo, "maxCount": hi}]})
    # one modifier per (tag, step): features keep one global order in every biome (no feature order cycle)
    groups = {}
    for fid, (configured, placement, step, tag) in features().items():
        if isinstance(configured, dict):
            write(f"{NS}/worldgen/configured_feature/{fid}.json", configured)
            feature = f"{NS}:{fid}"
        else:
            feature = configured
        write(f"{NS}/worldgen/placed_feature/{fid}.json", {"feature": feature, "placement": placement})
        groups.setdefault((tag, step), []).append(f"{NS}:{fid}")
    for (tag, step), fids in groups.items():
        write(f"{NS}/forge/biome_modifier/ocean_{tag}_{step}.json", {
            "type": "forge:add_features", "biomes": f"#{NS}:ocean/{tag}", "features": fids, "step": step})


# ------------------------------------------------------------------ manual (guide.py)
CATEGORY = ("oceans", "brasshaven:diving_helmet", ("Living oceans", "Océans vivants"))
PAGES = [
    ("oceans", "brasshaven:glow_jelly", ("Living oceans", "Océans vivants"), [
        ("The seas are full of life now: schools of reef fish, glowing jellyfish, manta rays, and far out in the "
         "deep, humpback whales. Dive and look around: the floor hides kelp forests, coral gardens, glowing "
         "anemones, pearl oysters, bubble vents, rock arches and sunken ruins.",
         "Les mers grouillent de vie : bancs de poissons de récif, méduses lumineuses, raies manta et, au large, "
         "baleines à bosse. Plonge et regarde : le fond cache des forêts de varech, des jardins de corail, des "
         "anémones lumineuses, des huîtres perlières, des cheminées à bulles, des arches rocheuses et des ruines."),
        ("Small wrecks wait on the sea floor too: a sunken steampunk submarine, a diving bell with air inside, coral "
         "shrines in warm seas and fields of shipwreck debris. Each has loot.",
         "De petites épaves attendent aussi au fond : un sous-marin steampunk englouti, une cloche de plongée "
         "pleine d'air, des sanctuaires de corail dans les mers chaudes et des champs de débris de naufrage. "
         "Chacun a son butin."),
    ], []),
    ("ocean_creatures", "brasshaven:reef_fish_bucket", ("Sea creatures", "Créatures marines"), [
        ("Glow Jellyfish drift in every sea, in four colours. Bumping into one stings (a little poison). They drop "
         "Glow Jelly: brew it into an Awkward Potion for Night Vision, or put four around glass for a Jelly Lamp.",
         "Les méduses lumineuses dérivent dans toutes les mers, en quatre couleurs. Les toucher pique (un peu de "
         "poison). Elles lâchent de la gelée lumineuse : dans une potion étrange, elle donne la vision nocturne ; "
         "quatre autour d'un verre font une lampe de gelée."),
        ("Reef Fish swim in schools in warm seas: sunburst, clown or azure. Catch one with a water bucket.",
         "Les poissons de récif nagent en bancs dans les mers chaudes : soleil, clown ou azur. Attrape-les avec "
         "un seau d'eau."),
        ("Manta Rays glide near the surface and sometimes leap out of the water. Humpback Whales live in the deep: "
         "they rise to blow and sing from far away. Both are peaceful.",
         "Les raies manta planent près de la surface et sautent parfois hors de l'eau. Les baleines à bosse vivent "
         "au large : elles remontent souffler et chantent de loin. Toutes deux sont paisibles."),
    ], ["brasshaven:glow_jelly", "brasshaven:jelly_lamp", "brasshaven:reef_fish_bucket"]),
    ("sea_serpent", "brasshaven:serpent_scale", ("Sea Serpent", "Serpent de mer"), [
        ("At night, over deep water, a boat or a swimmer may draw the Sea Serpent: a long crested beast with a boss "
         "bar. It bites, lunges from afar (boats in its way break) and roars up a whirlpool that drags you in and "
         "tips riders into the sea.",
         "La nuit, au-dessus des eaux profondes, un bateau ou un nageur peut attirer le serpent de mer : une longue "
         "bête à crête, avec sa barre de vie. Il mord, charge de loin (les bateaux sur sa route se brisent) et "
         "rugit pour lever un tourbillon qui t'aspire et renverse les passagers."),
        ("Fight it from a solid spot or under water with a Diving Helmet. It drops Sea Serpent Scales, prismarine "
         "and sometimes a Heart of the Sea. Unfought, it sinks away at dawn.",
         "Affronte-le depuis un appui solide ou sous l'eau avec un casque de scaphandre. Il lâche des écailles, de "
         "la prismarine et parfois un cœur de la mer. S'il n'est pas combattu, il replonge à l'aube."),
    ], ["brasshaven:serpent_scale", "brasshaven:sea_serpent_spawn_egg"]),
    ("diving_gear", "brasshaven:diving_helmet", ("Diving gear", "Équipement de plongée"), [
        ("Diving Helmet: a brass dome with a porthole. With your head under water it gives Conduit Power: you "
         "breathe, see clearly and mine at full speed. Craft it from four Sea Serpent Scales, a brass ingot and "
         "glass, or from two brass ingots, three copper blocks and glass.",
         "Casque de scaphandre : un dôme de laiton à hublot. La tête sous l'eau, il donne la force de conduit : tu "
         "respires, vois clair et mines à pleine vitesse. Fabrication : quatre écailles de serpent de mer, un "
         "lingot de laiton et du verre, ou deux lingots de laiton, trois blocs de cuivre et du verre."),
        ("Flippers: swim much faster. Two leather and two dried kelp blocks.",
         "Palmes : nage bien plus vite. Deux cuirs et deux blocs d'algues séchées."),
    ], ["brasshaven:diving_helmet", "brasshaven:flippers"]),
    ("sea_floor", "brasshaven:pearl_oyster", ("The sea floor", "Les fonds marins"), [
        ("Pearl Oysters lie in beds in temperate and warm seas. Right-click an open shell to take its pearl; it grows "
         "a new one in time. Four pearls trade for an emerald at the crafting table.",
         "Les huîtres perlières forment des bancs dans les mers tempérées et chaudes. Clic droit sur une coquille "
         "entrouverte pour prendre sa perle ; elle en refait une avec le temps. Quatre perles valent une émeraude "
         "à l'établi."),
        ("Bubble vents rise from basalt chimneys: swim into the column to shoot up to the surface and breathe. Glow "
         "Anemones light the floor at night; pick them up to decorate an aquarium.",
         "Les cheminées de basalte soufflent des colonnes de bulles : entre dedans pour remonter d'un coup et "
         "respirer. Les anémones lumineuses éclairent le fond la nuit ; ramasse-les pour décorer un aquarium."),
    ], ["brasshaven:pearl_oyster", "brasshaven:pearl", "brasshaven:glow_anemone"]),
]


def guide_pages():
    return [(pid, CATEGORY[0], icon, title, paras, items) for pid, icon, title, paras, items in PAGES]


# ------------------------------------------------------------------ textures (gen_textures.py)
# material -> (light, mid, dark), shaded like the gadget sprites (light top-left, dark bottom-right, outline)
MATS = {
    "J": ((200, 255, 250), (110, 226, 240), (52, 150, 196)),     # glow jelly
    "j": ((255, 214, 246), (240, 140, 214), (178, 80, 160)),     # jelly, rose heart
    "P": ((255, 255, 252), (236, 230, 236), (190, 178, 196)),    # pearl
    "S": ((92, 196, 190), (34, 120, 128), (16, 64, 76)),         # serpent scale
    "R": ((240, 110, 96), (186, 40, 52), (112, 20, 34)),         # crimson fin
    "B": ((250, 222, 130), (204, 162, 72), (140, 100, 40)),      # brass
    "C": ((240, 166, 104), (186, 112, 52), (122, 64, 30)),       # copper
    "G": ((206, 244, 255), (120, 196, 220), (60, 118, 150)),     # glass
    "K": ((70, 84, 110), (38, 48, 70), (20, 26, 40)),            # rubber
    "I": ((228, 228, 236), (164, 164, 176), (98, 98, 112)),      # iron (bucket)
    "W": ((96, 160, 255), (52, 108, 230), (34, 70, 170)),        # water
    "O": ((255, 186, 90), (255, 120, 30), (196, 74, 16)),        # orange fish
    "w": ((255, 255, 255), (240, 240, 236), (200, 200, 196)),    # white
}


class Grid:
    """16x16 grid of material letters, shaded and outlined like the gadget sprites."""

    def __init__(self, n=16):
        self.n = n
        self.m = [[None] * n for _ in range(n)]
        self.force = {}

    def paint(self, mat, test):
        for y in range(self.n):
            for x in range(self.n):
                if test(x + 0.5, y + 0.5):
                    self.m[y][x] = mat

    def px(self, x, y, mat, tone=None):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.m[y][x] = mat
            if tone:
                self.force[(x, y)] = tone

    def disc(self, mat, cx, cy, r):
        self.paint(mat, lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r)

    def ellipse(self, mat, cx, cy, rx, ry):
        self.paint(mat, lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0)

    def render(self, alpha=None):
        n = self.n
        cv = Canvas(n, n)

        def filled(x, y):
            return 0 <= x < n and 0 <= y < n and self.m[y][x] is not None
        for y in range(n):
            for x in range(n):
                mat = self.m[y][x]
                if mat is None:
                    continue
                light, mid, dark = MATS[mat]
                tone = self.force.get((x, y))
                if isinstance(tone, tuple):
                    cv.set(x, y, tone)
                    continue
                if tone is None:
                    up = filled(x, y - 1) and self.m[y - 1][x] == mat
                    left = filled(x - 1, y) and self.m[y][x - 1] == mat
                    down = filled(x, y + 1) and self.m[y + 1][x] == mat
                    right = filled(x + 1, y) and self.m[y][x + 1] == mat
                    if not up or not left:
                        tone = "light" if (down and right) or not (up or left) else "mid"
                    elif not down or not right:
                        tone = "dark"
                    else:
                        tone = "mid"
                c = {"light": light, "mid": mid, "dark": dark}[tone]
                a = (alpha or {}).get(mat, 255)
                cv.set(x, y, (*c, a))
        for y in range(n):
            for x in range(n):
                if self.m[y][x] is not None:
                    continue
                near = [self.m[yy][xx] for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if filled(xx, yy)]
                if near:
                    cv.set(x, y, tuple(int(c * 0.38) for c in MATS[near[0]][2]))
        return cv


def _glow_jelly():
    g = Grid()
    # a wobbly dome of jelly with a rose heart and a bright highlight
    g.paint("J", lambda x, y: ((x - 8) / 6.0) ** 2 + ((y - 9.5) / 5.0) ** 2 <= 1.0 and y < 14 - 0.8 * math.sin(x * 1.7))
    g.ellipse("j", 8.5, 10.5, 2.6, 1.8)
    for x, y in ((5, 6), (6, 6), (5, 7), (4, 8)):
        g.px(x, y, "J", (255, 255, 255))
    g.px(11, 12, "J", (40, 120, 170))
    return g.render(alpha={"J": 220})


def _pearl():
    g = Grid()
    g.disc("P", 8, 8.5, 4.6)
    g.px(6, 6, "P", (255, 255, 255))
    g.px(7, 6, "P", (255, 255, 255))
    g.px(6, 7, "P", (255, 250, 255))
    for x, y in ((10, 11), (11, 10)):
        g.px(x, y, "P", (204, 186, 214))  # a faint rose sheen
    return g.render()


def _serpent_scale():
    g = Grid()

    # a pointed teal scale: rounded top, tapering to a point at the bottom, crimson rim, light ridge
    def inside(x, y, shrink=0.0):
        t = (y - 1.5) / 13.0
        if t < 0 or t > 1:
            return False
        half = 6.0 * (1 - t) ** 0.75 * min(1.0, t * 3.5) ** 0.5 - shrink
        return abs(x - 8) <= half
    g.paint("R", lambda x, y: inside(x, y))
    g.paint("S", lambda x, y: inside(x, y, 1.2) and y < 13)
    for y in range(4, 12):
        g.px(8, y, "S", MATS["S"][0])
    for x, y in ((5, 6), (11, 6), (6, 9), (10, 9)):
        g.px(x, y, "S", MATS["S"][2])
    return g.render()


def _diving_helmet():
    g = Grid()
    g.disc("B", 8, 7.5, 6.3)                                  # brass dome
    for x in range(2, 14):                                     # copper collar
        for y in (13, 14):
            g.px(x, y, "C")
    g.disc("C", 8, 8, 3.6)                                    # porthole frame
    g.disc("G", 8, 8, 2.5)                                    # glass
    g.px(7, 7, "G", (236, 252, 255))
    g.px(8, 7, "G", (236, 252, 255))
    for x, y in ((3, 7), (13, 7), (8, 2), (5, 3), (11, 3)):   # rivets
        g.px(x, y, "B", (255, 240, 180))
    for x, y in ((1, 9), (14, 9)):                            # side portholes
        g.px(x, y, "G")
    return g.render()


def _flippers():
    g = Grid()
    # two splayed flippers: a foot pocket at the heel (bottom) and a wide ribbed blade toward the toes (top)
    for ox, lean in ((5, -1), (11, 1)):
        def blade(x, y, ox=ox, lean=lean):
            if not 1.5 <= y <= 14:
                return False
            cx = ox + lean * (14 - y) * 0.18
            half = 0.9 + (14 - y) * 0.2 if y < 11 else 1.4
            return abs(x - cx) <= half
        g.paint("K", blade)
        for y in range(3, 10, 2):
            g.px(round(ox + lean * (14 - y) * 0.18), y, "K", MATS["K"][0])
        for x in range(ox - 1, ox + 2):                       # yellow heel strap
            g.px(x, 12, "O")
    return g.render()


def _reef_fish_bucket():
    g = Grid()
    g.paint("I", lambda x, y: 4 <= y <= 14 and abs(x - 8) <= 5.6 - (y - 4) * 0.18)
    g.paint("W", lambda x, y: 5 <= y <= 7 and abs(x - 8) <= 4.4)
    g.paint("I", lambda x, y: 1.2 <= y <= 4 and ((x - 8) ** 2 / 36 + (y - 4.5) ** 2 / 12) >= 0.75 and abs(x - 8) <= 6)
    g.ellipse("O", 8.5, 6, 2.6, 1.6)                          # the fish peeking out
    g.px(11, 5, "O")
    g.px(11, 7, "O")
    g.px(8, 6, "w")
    g.px(7, 5, "w", (20, 20, 30))
    return g.render()


def _anemone(color):
    """Cross-plant texture: a short striped stalk and a crown of glowing tentacles."""
    stalk, tent, tip = {
        0: ((150, 60, 120), (236, 110, 200), (255, 210, 245)),
        1: ((40, 110, 130), (80, 220, 230), (220, 255, 255)),
        2: ((150, 100, 30), (255, 196, 60), (255, 245, 190)),
    }[color]
    cv = Canvas(16, 16)
    for y in range(11, 16):
        for x in range(6, 10):
            cv.set(x, y, mix(stalk, (255, 255, 255), 0.15) if (x + y) % 3 == 0 else stalk)
    rng = random.Random(color * 7 + 1)
    for i in range(9):
        a = math.pi * (0.08 + 0.84 * i / 8)
        length = 7 + rng.random() * 3.5
        for s in range(int(length * 2)):
            t = s / 2.0
            x = 8 + math.cos(a) * t * 0.8 + math.sin(t * 0.9 + i) * 0.6
            y = 11 - math.sin(a) * t
            if 0 <= int(x) < 16 and 0 <= int(y) < 16:
                cv.set(int(x), int(y), tip if t > length - 1.5 else mix(tent, stalk, 0.3 * (1 - t / length)))
    return cv


def _oyster(face):
    cv = Canvas(16, 16)
    rng = random.Random({"top": 3, "side": 4, "inside": 5}[face])
    for y in range(16):
        for x in range(16):
            if face == "top":
                # concentric growth ridges on a rough grey-brown shell
                r = math.hypot(x - 8, y - 15)
                c = (120, 110, 100) if int(r * 1.2) % 2 else (150, 140, 126)
                c = mul(c, 1 + rng.uniform(-0.08, 0.08))
                if rng.random() < 0.05:
                    c = (90, 120, 96)          # a bit of weed
            elif face == "side":
                c = [(160, 150, 136), (120, 110, 100), (186, 176, 160), (110, 100, 92)][(y // 2) % 4]
                c = mul(c, 1 + rng.uniform(-0.06, 0.06))
            else:
                # mother-of-pearl: pale with rose and teal sheen
                t = (x + y) / 30.0
                c = mix(mix((240, 232, 240), (214, 196, 230), t), (196, 232, 230),
                        0.25 * math.sin(x * 0.7 + y * 0.4) ** 2)
            cv.set(x, y, c)
    return cv


def _pearl_block():
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            cv.set(x, y, mix((255, 255, 255), (214, 204, 222), min(1.0, d / 3.0)))
    return cv


def _jelly_lamp():
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            d = math.hypot(x - 7.5, y - 7.5)
            if edge:
                c, a = (90, 200, 230), 235
            elif d < 3.2:
                c, a = mix((255, 255, 230), (255, 190, 236), d / 3.2), 255     # the glowing core
            else:
                wob = math.sin(x * 0.9) * math.cos(y * 0.7)
                c, a = mix((120, 226, 244), (226, 150, 230), 0.3 + 0.3 * wob), 170
            cv.set(x, y, (*c, a))
    for x, y in ((3, 3), (4, 3), (3, 4), (12, 11)):
        cv.set(x, y, (240, 255, 255, 240))
    return cv


def _diving_armor():
    """Humanoid equipment layer (64x32): the helmet (head + a slightly larger outer shell with a porthole frame and
    rivets, so the dome stands out in 3D) and the flippers (feet of the leg box)."""
    cv = Canvas(64, 32)
    B, Bl, Bd = MATS["B"][1], MATS["B"][0], MATS["B"][2]
    C, Cd = MATS["C"][1], MATS["C"][2]
    G, Gl = MATS["G"][1], MATS["G"][0]

    def faces(u, v, w, h, d):
        return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
                "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + d + w + d, v + d, w, h)}

    # head (inner): brass dome, darker toward the collar, a round glass port on the front and on each side
    for name, (x0, y0, w, h) in faces(0, 0, 8, 8, 8).items():
        for y in range(h):
            for x in range(w):
                c = mix(Bl, B, y / 7.0) if name != "bottom" else Bd
                if name in ("front", "right", "left", "back") and y == h - 1:
                    c = C                                           # copper collar
                port = 6.5 if name == "front" else 2.5
                if name in ("front", "left", "right") and (x - 3.5) ** 2 + (y - 3.5) ** 2 <= port:
                    c = Gl if (x, y) in ((2, 2), (3, 2)) else G
                cv.set(x0 + x, y0 + y, c)
    # hat (outer shell): only the porthole frames, bolts and the crest are drawn, the rest stays clear
    for name, (x0, y0, w, h) in faces(32, 0, 8, 8, 8).items():
        for y in range(h):
            for x in range(w):
                r2 = (x - 3.5) ** 2 + (y - 3.5) ** 2
                c = None
                if name == "front" and 6.5 < r2 <= 12.5:
                    c = C if (x + y) % 3 else Cd                    # bolted porthole frame
                elif name in ("left", "right") and 2.5 < r2 <= 6.5:
                    c = C
                elif name in ("front", "back", "left", "right") and y == h - 1 and x % 2 == 0:
                    c = Bd                                          # bolts of the collar
                elif name == "top" and x in (3, 4):
                    c = Bl if y % 2 else B                          # crest strip over the dome
                if c is not None:
                    cv.set(x0 + x, y0 + y, c)
    # flippers: the lower part of each leg box (boots use the 4x12x4 leg at 0,16)
    K, Kl, Kd = MATS["K"][1], MATS["K"][0], MATS["K"][2]
    for name, (x0, y0, w, h) in faces(0, 16, 4, 12, 4).items():
        if name == "top":
            continue
        for y in range(h):
            for x in range(w):
                if name == "bottom" or y >= 8:
                    c = Kl if (x + y) % 4 == 0 else K
                    if y == 8 and name != "bottom":
                        c = Cd                                      # strap
                    cv.set(x0 + x, y0 + y, c)
    return cv


def textures():
    """rel path (under textures/) -> Canvas."""
    out = {
        "item/glow_jelly": _glow_jelly(),
        "item/pearl": _pearl(),
        "item/serpent_scale": _serpent_scale(),
        "item/diving_helmet": _diving_helmet(),
        "item/flippers": _flippers(),
        "item/reef_fish_bucket": _reef_fish_bucket(),
        "block/oyster_top": _oyster("top"),
        "block/oyster_side": _oyster("side"),
        "block/oyster_inside": _oyster("inside"),
        "block/oyster_pearl": _pearl_block(),
        "block/jelly_lamp": _jelly_lamp(),
        "entity/equipment/humanoid/diving": _diving_armor(),
    }
    for c in range(3):
        out[f"block/glow_anemone_{c}"] = _anemone(c)
    return out


# ------------------------------------------------------------------ block models (gen_assets.py)
def _cross(texture, emission):
    planes = []
    for angle in (45, -45):
        planes.append({"from": [0.8, 0, 8], "to": [15.2, 16, 8], "shade": False, "light_emission": emission,
                       "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": angle, "rescale": True},
                       "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#cross"},
                                 "south": {"uv": [0, 0, 16, 16], "texture": "#cross"}}})
    return {"parent": "minecraft:block/block", "render_type": "minecraft:cutout", "ambient_occlusion": False,
            "textures": {"particle": texture, "cross": texture}, "elements": planes}


def _oyster_model(open_):
    t = f"{NS}:block/"
    tex = {"particle": t + "oyster_top", "top": t + "oyster_top", "side": t + "oyster_side",
           "inside": t + "oyster_inside", "pearl": t + "oyster_pearl"}

    def cube(frm, to, up, down, side, rot=None):
        e = {"from": frm, "to": to, "faces": {
            "up": {"texture": up}, "down": {"texture": down},
            **{f: {"texture": side} for f in ("north", "south", "east", "west")}}}
        if rot:
            e["rotation"] = rot
        return e
    els = [cube([2, 0, 2], [14, 2, 14], "#inside", "#top", "#side")]
    if open_:
        # the lid hinged at the back, propped open, and the pearl inside
        els.append(cube([2, 2, 2], [14, 4, 14], "#top", "#inside", "#side",
                        {"origin": [8, 2, 14], "axis": "x", "angle": 22.5}))
        els.append(cube([7, 2, 6], [9, 4, 8], "#pearl", "#pearl", "#pearl"))
    else:
        els.append(cube([2, 2, 2], [14, 4, 14], "#top", "#inside", "#side"))
        els.append(cube([4, 4, 4], [12, 5, 12], "#top", "#top", "#side"))
    return {"parent": "minecraft:block/block", "textures": tex, "elements": els}


def assets(write):
    """Block models, blockstates, item definitions of the ocean blocks, and the diving equipment asset."""
    for c in range(3):
        write(f"models/block/glow_anemone_{c}.json", _cross(f"{NS}:block/glow_anemone_{c}", 12))
    write("blockstates/glow_anemone.json", {"variants": {
        f"color={c}": {"model": f"{NS}:block/glow_anemone_{c}"} for c in range(3)}})
    write("items/glow_anemone.json", {"model": {"type": "minecraft:model", "model": f"{NS}:item/glow_anemone"}})
    write("models/item/glow_anemone.json", {"parent": "minecraft:item/generated",
                                            "textures": {"layer0": f"{NS}:block/glow_anemone_0"}})
    write("models/block/pearl_oyster.json", _oyster_model(False))
    write("models/block/pearl_oyster_open.json", _oyster_model(True))
    rot = {"north": 0, "east": 90, "south": 180, "west": 270}
    write("blockstates/pearl_oyster.json", {"variants": {
        f"facing={f},pearl={p}": {"model": f"{NS}:block/pearl_oyster{'_open' if p == 'true' else ''}",
                                  **({"y": r} if r else {})}
        for f, r in rot.items() for p in ("false", "true")}})
    write("items/pearl_oyster.json", {"model": {"type": "minecraft:model", "model": f"{NS}:block/pearl_oyster_open"}})
    write("models/block/jelly_lamp.json", {"parent": "minecraft:block/cube_all", "render_type": "minecraft:translucent",
                                           "textures": {"all": f"{NS}:block/jelly_lamp"}})
    write("blockstates/jelly_lamp.json", {"variants": {"": {"model": f"{NS}:block/jelly_lamp"}}})
    write("items/jelly_lamp.json", {"model": {"type": "minecraft:model", "model": f"{NS}:block/jelly_lamp"}})
    write("equipment/diving.json", {"layers": {"humanoid": [{"texture": f"{NS}:diving"}]}})


# ------------------------------------------------------------------ sea-floor templates (gen_data.py)
# Placed by the template features above: blueprint y = 0 is the top block of the sea floor (the placement snaps to
# the floor, then moves 4 down, so every template must reach down to y = -3: a foundation that fills dips and keeps
# nothing floating on a slope). Unset cells keep the sea. Footprints stay within 15 x 15 (a feature may only write
# one chunk around its own).
CORALS = ["brain", "tube", "bubble", "fire", "horn"]


def is_solid(name):
    return name not in ("minecraft:air", "minecraft:water") and not any(
        h in name for h in ("coral", "pickle", "kelp", "seagrass", "pot", "chest", "button", "stairs", "slab", "wall"))


def _foundation(bp, rock=("stone", "andesite", "gravel")):
    """Fill every column under the lowest block down to y = -3 (and mark the template's bottom at -3)."""
    rng = random.Random(len(bp.blocks))
    cols = {}
    for (x, y, z) in bp.blocks:
        cols[(x, z)] = min(y, cols.get((x, z), y))
    for (x, z), low in cols.items():
        for y in range(-3, min(low, 0)):
            if (x, y, z) not in bp.blocks:
                bp.set(x, y, z, rng.choice(rock))
    if not any(y == -3 for (_x, y, _z) in bp.blocks):
        bp.set(0, -3, 0, rock[0])


def _coral_dressing(bp, rng, chance=0.6):
    """Corals, fans and sea pickles on the free tops of coral blocks."""
    tops = [(x, y, z) for (x, y, z), (name, _p, _d) in list(bp.blocks.items())
            if name.endswith("_coral_block") and (x, y + 1, z) not in bp.blocks]
    for x, y, z in tops:
        if rng.random() < chance:
            kind = rng.choice(CORALS)
            r = rng.random()
            if r < 0.45:
                bp.set(x, y + 1, z, f"{kind}_coral[waterlogged=true]")
            elif r < 0.85:
                bp.set(x, y + 1, z, f"{kind}_coral_fan[waterlogged=true]")
            else:
                bp.set(x, y + 1, z, f"sea_pickle[pickles={rng.randint(1, 4)},waterlogged=true]")


def coral_tower(bp):
    rng = random.Random(11)
    # three lumpy stacks leaning together, each a different coral
    for (cx, cz, h, kind) in ((0, 0, 10, "brain"), (2, 1, 7, "tube"), (-1, 2, 5, "fire")):
        for y in range(0, h):
            r = 1.8 - 0.9 * (y / h) + (0.6 if y % 3 == 0 else 0.0)
            ox = round(math.sin(y * 0.7 + cx) * 0.6)
            for x in range(-2, 3):
                for z in range(-2, 3):
                    if (x - 0.0) ** 2 + (z - 0.0) ** 2 <= r * r:
                        bp.set(cx + x + ox, y, cz + z, f"{kind}_coral_block")
    _coral_dressing(bp, rng, 0.7)
    _foundation(bp, ("sand", "sandstone", "sand"))


def coral_fan(bp):
    rng = random.Random(12)
    # a great flat fan of horn and fire coral, rooted in a brain-coral base, veined with tube coral
    for x in range(-6, 7):
        for y in range(0, 10):
            d = math.hypot(x * 0.9, (y - 0.5) * 1.0)
            if d <= 6.5 and y >= 0 and (y >= 1 or abs(x) <= 2):
                vein = abs(math.atan2(y, x) * 3) % 1.0 < 0.12
                kind = "tube" if vein else ("horn" if (x + y) % 5 else "fire")
                if d > 6.0 and rng.random() < 0.35:
                    continue
                bp.set(x, y, 0, f"{kind}_coral_block")
    for x in range(-2, 3):
        for z in (-1, 1):
            bp.set(x, 0, z, "brain_coral_block")
    for x in range(-6, 7):
        for y in range(1, 10):
            if bp.get(x, y, 0) and rng.random() < 0.25:
                for z in (-1, 1):
                    if not bp.get(x, y, z):
                        bp.set(x, y, z, f"{rng.choice(CORALS)}_coral_wall_fan[facing={'north' if z < 0 else 'south'},waterlogged=true]")
    _coral_dressing(bp, rng, 0.8)
    _foundation(bp, ("sand", "sandstone"))


def coral_arch(bp):
    rng = random.Random(13)
    # a twisted arch of bubble and tube coral over a swim-through
    for i in range(0, 41):
        t = i / 40.0
        x = -6 + 12 * t
        y = 7.5 * math.sin(math.pi * t)
        z = math.sin(t * 6.0) * 0.8
        r = 1.6 - 0.5 * math.sin(math.pi * t)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dz in range(-2, 3):
                    if dx * dx + dy * dy + dz * dz <= r * r:
                        kind = "bubble" if (round(x + dx) + round(y + dy)) % 4 else "tube"
                        bp.set(round(x + dx), max(0, round(y + dy)), round(z + dz), f"{kind}_coral_block")
    _coral_dressing(bp, rng, 0.75)
    _foundation(bp, ("sand", "sandstone"))


def coral_brain(bp):
    rng = random.Random(14)
    # a big brain-coral dome ringed with fans, a few sea pickles glowing in its folds
    for x in range(-5, 6):
        for z in range(-5, 6):
            for y in range(0, 5):
                if x * x + z * z + (y * 1.3) ** 2 <= 22:
                    bp.set(x, y, z, "brain_coral_block" if (x * 3 + z * 5 + y) % 7 else "fire_coral_block")
    _coral_dressing(bp, rng, 0.55)
    for a in range(16):
        ang = a / 16 * math.tau
        x, z = round(math.cos(ang) * 5.6), round(math.sin(ang) * 5.6)
        if not bp.get(x, 0, z):
            bp.set(x, 0, z, "sand")
            bp.set(x, 1, z, f"{rng.choice(CORALS)}_coral_fan[waterlogged=true]")
    _foundation(bp, ("sand", "sandstone"))


ROCK = ["stone", "stone", "andesite", "tuff", "cobblestone", "diorite"]


def _rock(rng):
    return rng.choice(ROCK)


def _weed(bp, rng, chance=0.4):
    """Moss and gravel on the tops of rocks, kelp and sea grass growing from them."""
    tops = [(x, y, z) for (x, y, z), (name, _p, _d) in list(bp.blocks.items())
            if (x, y + 1, z) not in bp.blocks and y >= 0 and is_solid(name)]
    for x, y, z in tops:
        r = rng.random()
        if r < chance * 0.4:
            bp.set(x, y, z, "moss_block")
        elif r < chance * 0.6:
            bp.set(x, y, z, "gravel" if y == 0 else "mossy_cobblestone")
        elif r < chance * 0.8 and y < 6:
            h = rng.randint(2, 5)
            for k in range(1, h + 1):
                bp.set(x, y + k, z, "kelp_plant" if k < h else "kelp[age=20]")
        elif r < chance:
            bp.set(x, y + 1, z, "seagrass")


def rock_arch(bp):
    rng = random.Random(21)
    for i in range(0, 61):
        t = i / 60.0
        x = -5 + 10 * t
        y = 9 * math.sin(math.pi * t) ** 0.8
        r = 2.4 - 1.0 * math.sin(math.pi * t)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                for dz in range(-2, 3):
                    if dx * dx + (dy * 1.2) ** 2 + dz * dz * 1.6 <= r * r:
                        bp.set(round(x + dx), max(0, round(y + dy)), dz, _rock(rng))
    _weed(bp, rng)
    _foundation(bp)


def rock_pillars(bp):
    rng = random.Random(22)
    for cx, cz, h in ((-4, -2, 11), (1, -4, 7), (4, 2, 9), (-1, 4, 5), (-5, 4, 3)):
        for y in range(0, h):
            r = 1.4 if y < h - 2 else 0.9
            for x in range(-2, 3):
                for z in range(-2, 3):
                    if x * x + z * z <= r * r + (0.6 if y == 0 else 0):
                        bp.set(cx + x, y, cz + z, "tuff" if (y + x) % 4 else "polished_tuff")
    _weed(bp, rng, 0.5)
    _foundation(bp, ("tuff", "stone", "gravel"))


def rock_stack(bp):
    rng = random.Random(23)
    for y in range(0, 13):
        r = 3.2 - y * 0.16 + (0.5 if y % 4 == 1 else 0)
        sx = math.sin(y * 0.5) * 0.7
        for x in range(-4, 5):
            for z in range(-4, 5):
                if (x - sx) ** 2 + z * z <= r * r:
                    bp.set(x, y, z, _rock(rng) if y % 3 else "andesite")
    _weed(bp, rng, 0.45)
    _foundation(bp)


def rock_ring(bp):
    rng = random.Random(24)
    # a ring of tilted standing stones around a sandy hollow, like a drowned henge
    for i in range(7):
        a = i / 7 * math.tau
        cx, cz = round(math.cos(a) * 5), round(math.sin(a) * 5)
        h = rng.randint(3, 6)
        lean = rng.choice((-1, 0, 1))
        for y in range(0, h):
            off = lean if y >= h - 2 else 0
            for dx in (0, 1):
                bp.set(cx + dx + off, y, cz, "stone" if y % 2 else "cobblestone")
    for x in range(-3, 4):
        for z in range(-3, 4):
            if x * x + z * z <= 9:
                bp.set(x, 0, z, "sand")
    bp.set(0, 1, 0, "sea_pickle[pickles=4,waterlogged=true]")
    _weed(bp, rng, 0.35)
    _foundation(bp)


RUIN = ["stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "stone_bricks"]


def _ruin(rng):
    return rng.choice(RUIN)


def ruin_colonnade(bp):
    rng = random.Random(31)
    for x in range(-5, 6):
        for z in range(-3, 4):
            if rng.random() < 0.85:
                bp.set(x, 0, z, "smooth_sandstone" if (x + z) % 2 else "cut_sandstone")
    for i, x in enumerate((-4, -1, 2, 5)):
        h = (6, 3, 5, 2)[i]
        for z in (-3, 3):
            hh = h if z < 0 else max(1, h - 2)
            for y in range(1, hh + 1):
                bp.set(x, y, z, "chiseled_sandstone" if y == 1 else "cut_sandstone")
            if hh >= 5:
                bp.set(x, hh + 1, z, "smooth_sandstone_slab[type=bottom]")
    # an architrave still resting on the two tallest columns, and a fallen drum
    for x in range(-4, 0):
        bp.set(x, 7, -3, "smooth_sandstone")
    for x in (1, 2, 3):
        bp.set(x, 1, 1, "cut_sandstone")
    bp.set(0, 1, 0, "decorated_pot[facing=south,cracked=true,waterlogged=true]")
    _weed(bp, rng, 0.3)
    _foundation(bp, ("sandstone", "sand"))


def ruin_statue(bp):
    rng = random.Random(32)
    # the great head of a fallen statue, half sunk, with its crown, and the broken shoulder beside it
    for x in range(-2, 3):
        for y in range(0, 5):
            for z in range(-2, 3):
                bp.set(x, y, z, "stone" if (x + y + z) % 5 else "andesite")
    for x in (-1, 1):
        bp.set(x, 3, -3, "polished_blackstone_button[face=wall,facing=north,powered=false]")   # eyes
    bp.set(0, 2, -3, "stone_brick_stairs[facing=south,half=top]")                               # nose
    for x in range(-1, 2):
        bp.set(x, 1, -3, "stone_slab[type=top]")                                                 # lips
    for x in range(-2, 3):
        bp.set(x, 5, 0, "gold_block" if x == 0 else "stone_brick_wall")                          # its crown
    for x in range(3, 7):
        for z in range(0, 3):
            bp.set(x, 0, z, _ruin(rng))
            if x < 5:
                bp.set(x, 1, z, _ruin(rng))
    _weed(bp, rng, 0.3)
    _foundation(bp)


def ruin_stair(bp):
    rng = random.Random(33)
    # a stairway sinking into the sea floor between two walls, down to a landing before a collapsed doorway, where
    # a small chest waits
    for i in range(4):
        z = -2 + i
        for x in (-1, 0, 1):
            bp.set(x, -i, z, "stone_brick_stairs[facing=north,half=bottom]")
            for y in range(-i + 1, 1):
                bp.set(x, y, z, "air")                    # carved out (water once placed)
        for x in (-2, 2):
            for y in range(-i, 2 if i < 2 else 1):
                bp.set(x, y, z, _ruin(rng))
    for x in range(-2, 3):
        bp.set(x, -3, 2, _ruin(rng))
        for y in range(-2, 1):
            bp.set(x, y, 2, "air" if abs(x) < 2 else _ruin(rng))
        for y in range(-3, 2):
            bp.set(x, y, 3, "chiseled_stone_bricks" if (x, y) == (0, 1) else _ruin(rng))
    bp.set(0, -2, 3, "cracked_stone_bricks")
    bp.set(0, -1, 3, "mossy_cobblestone")
    bp.chest(0, -2, 2, "north", "minecraft:chests/underwater_ruin_small")
    bp.set(-1, -2, 2, "sea_pickle[pickles=2,waterlogged=true]")
    _weed(bp, rng, 0.25)
    _foundation(bp)


def ruin_amphorae(bp):
    rng = random.Random(34)
    # a merchant's cargo of amphorae spilled from a lost boat, half buried in sand
    for x in range(-4, 5):
        for z in range(-3, 4):
            if x * x / 20 + z * z / 12 <= 1.0:
                bp.set(x, 0, z, "sand")
                if rng.random() < 0.35:
                    bp.set(x, 1, z, f"decorated_pot[facing={rng.choice(['north', 'south', 'east', 'west'])},"
                                    f"cracked={'true' if rng.random() < 0.4 else 'false'},waterlogged=true]")
    for x in range(-3, 3):
        bp.set(x, 1, -3, "dark_oak_planks" if x % 2 else "stripped_dark_oak_log[axis=x]")
    bp.set(3, 1, 2, "barrel[facing=up,open=false]")
    _foundation(bp, ("sand", "sandstone"))


TEMPLATES = {
    "coral_tower": coral_tower, "coral_fan": coral_fan, "coral_arch": coral_arch, "coral_brain": coral_brain,
    "rock_arch": rock_arch, "rock_pillars": rock_pillars, "rock_stack": rock_stack, "rock_ring": rock_ring,
    "ruin_colonnade": ruin_colonnade, "ruin_statue": ruin_statue, "ruin_stair": ruin_stair,
    "ruin_amphorae": ruin_amphorae,
}


def build_template(name):
    from .blueprint import Blueprint
    bp = Blueprint(f"ocean/{name}")
    bp.underwater = True
    TEMPLATES[name](bp)
    (x0, y0, z0), (x1, y1, z1) = bp.bounds()
    if x1 - x0 > 14 or z1 - z0 > 14 or y0 != -3:
        raise ValueError(f"ocean template {name}: {x1 - x0 + 1}x{z1 - z0 + 1} footprint, bottom {y0} (max 15x15, -3)")
    return bp


def write_templates(root):
    import os
    out = os.path.join(root, "src", "main", "resources", "data", NS, "structure", "ocean")
    os.makedirs(out, exist_ok=True)
    for name in TEMPLATES:
        build_template(name).save(os.path.join(out, f"{name}.nbt"))
    return list(TEMPLATES)
