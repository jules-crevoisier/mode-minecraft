"""Supplies in the barrels (and the odd plain chest or shulker box) of every structure.

The rooms of the structures are full of barrels and crate stacks (wf/interior.py, the builders' own props). They used
to be empty; now most of them hold a few modest, themed supplies, like the barrels of vanilla villages. The good loot
stays in the main chests (tools/gen_loot.py): a barrel never holds diamonds, enchanted gear, boss gear or anything
that skips a step of the progression ladder (wf/progression.py, checked by validate.py).

How a barrel picks its table, most specific first:
  1. the room it stands in: decorate() / yard() of wf/interior.py set ``bp.barrel_kind`` while they furnish, so the
     barrels of a kitchen hold food and those of a forge hold nuggets and coal (Blueprint.set records the hint);
     a builder can do the same around its own props;
  2. the structure: STRUCTURE_KIND below (a harbour keeps fish and string, a Nether fort gold nuggets and quartz);
  3. the dimension (Nether, End), else food.

About two barrels in three are stocked (a little fewer in inhabited places: those barrels are the residents'
stores); the others stay empty so it feels natural. The choice is deterministic (seeded by the piece name).
A container that already has a ``LootTable`` (a structure's chest table placed in a barrel) is left alone.
"""
import random

from . import nbt

PREFIX = "brasshaven:chests/barrel_"

# ------------------------------------------------------------------------------------------- tables
# kind -> (main pool [(item, weight, (min, max))], extra pool [(item, weight, (min, max))]).
# The main pool always rolls 2-3 times (a stocked barrel is never empty); the extra pool sometimes adds one more,
# slightly nicer thing. Counts stay small: a barrel is a larder, not a treasure.
B = "brasshaven:"
TABLES = {
    # storerooms, kitchens, homes, farms
    "food": (
        [("bread", 14, (1, 3)), ("potato", 12, (2, 5)), ("carrot", 12, (2, 5)), ("wheat", 12, (3, 8)),
         ("wheat_seeds", 10, (3, 8)), ("beetroot", 8, (2, 4)), ("beetroot_seeds", 6, (2, 6)), ("apple", 10, (1, 3)),
         ("baked_potato", 6, (1, 3)), ("pumpkin_seeds", 5, (1, 4)), ("melon_seeds", 4, (1, 4)), ("sugar", 6, (1, 4)),
         ("egg", 5, (1, 3)), ("sweet_berries", 5, (2, 6)), ("dried_kelp", 4, (2, 6))],
        [("cookie", 4, (2, 6)), ("pumpkin_pie", 3, (1, 1)), ("honey_bottle", 2, (1, 1)), ("cocoa_beans", 3, (1, 3)),
         ("bowl", 3, (1, 2))]),
    # workshops, forges, foundries
    "workshop": (
        [("iron_nugget", 15, (2, 9)), ("coal", 14, (2, 6)), (B + "brass_nugget", 12, (2, 8)), ("copper_ingot", 10, (1, 3)),
         ("charcoal", 8, (2, 5)), (B + "zinc_nugget", 8, (2, 6)), (B + "rivet", 8, (2, 6)), ("flint", 6, (1, 3)),
         ("leather", 6, (1, 3)), ("string", 6, (1, 4)), ("stick", 6, (2, 6))],
        [("iron_ingot", 4, (1, 2)), (B + "brass_ingot", 4, (1, 2)), (B + "brass_gear", 3, (1, 1)), ("bucket", 1, (1, 1))]),
    # libraries, studies, archives
    "library": (
        [("paper", 18, (2, 8)), ("book", 10, (1, 2)), ("ink_sac", 10, (1, 3)), ("feather", 10, (1, 4)),
         ("candle", 6, (1, 2)), ("leather", 4, (1, 2)), ("string", 4, (1, 3))],
        [("glow_ink_sac", 3, (1, 2)), ("writable_book", 3, (1, 1)), ("map", 2, (1, 1)), (B + "map_fragment", 3, (1, 1))]),
    # barracks, watchtowers, camps, outposts
    "military": (
        [("arrow", 18, (4, 12)), ("iron_nugget", 12, (2, 8)), ("bread", 10, (1, 3)), ("leather", 8, (1, 3)),
         ("string", 8, (1, 4)), ("cooked_beef", 6, (1, 3)), ("flint", 6, (1, 3)), ("feather", 6, (1, 4)),
         ("torch", 6, (2, 6))],
        [("potion", 3, (1, 1)), ("iron_ingot", 3, (1, 2)), ("gunpowder", 2, (1, 2)), ("shield", 1, (1, 1))]),
    # docks, lighthouses, ships, wrecks
    "harbour": (
        [("string", 14, (2, 6)), ("cod", 12, (1, 4)), ("salmon", 10, (1, 4)), ("dried_kelp", 10, (2, 8)),
         ("kelp", 8, (2, 6)), ("cooked_cod", 6, (1, 3)), ("ink_sac", 6, (1, 3)), ("tropical_fish", 3, (1, 2)),
         ("paper", 4, (1, 4))],
        [("lead", 3, (1, 1)), ("fishing_rod", 2, (1, 1)), ("gunpowder", 2, (1, 2)), (B + "pearl", 1, (1, 1))]),
    # mines, dwarven halls, deep wells
    "mine": (
        [("coal", 16, (3, 8)), ("raw_iron", 12, (1, 4)), ("raw_copper", 12, (2, 6)), (B + "raw_zinc", 10, (1, 4)),
         ("torch", 12, (3, 10)), ("iron_nugget", 8, (2, 6)), ("rail", 6, (2, 6)), ("flint", 4, (1, 3)),
         ("bread", 6, (1, 2))],
        [("gold_nugget", 4, (1, 5)), ("redstone", 4, (1, 4)), ("lapis_lazuli", 3, (1, 3))]),
    # sylvan halls, giant trees, witches' gardens
    "sylvan": (
        [("glow_berries", 10, (2, 6)), ("sweet_berries", 10, (2, 6)), ("bone_meal", 10, (2, 6)), ("apple", 6, (1, 3)),
         ("oak_sapling", 6, (1, 2)), ("birch_sapling", 6, (1, 2)), ("wheat_seeds", 6, (2, 6)),
         ("brown_mushroom", 5, (1, 3)), ("red_mushroom", 5, (1, 3)), ("dandelion", 4, (1, 3)), ("poppy", 4, (1, 3)),
         ("lily_of_the_valley", 3, (1, 2)), ("cornflower", 3, (1, 2))],
        [("honeycomb", 4, (1, 3)), ("cherry_sapling", 3, (1, 1)), (B + "glowwood_sapling", 2, (1, 1))]),
    # clockwork towns, labs, inventors
    "clockwork": (
        [(B + "brass_nugget", 14, (2, 8)), ("redstone", 14, (2, 6)), ("copper_ingot", 12, (1, 4)),
         (B + "rivet", 10, (2, 6)), (B + "brass_gear", 8, (1, 2)), (B + "zinc_nugget", 8, (2, 6)),
         ("iron_nugget", 8, (2, 6)), ("copper_nugget", 8, (2, 8))],
        [("repeater", 3, (1, 1)), ("lever", 3, (1, 2)), ("clock", 1, (1, 1)), (B + "brass_ingot", 3, (1, 2))]),
    "nether": (
        [("gold_nugget", 16, (2, 9)), ("quartz", 12, (1, 5)), ("bone", 8, (1, 4)), ("nether_wart", 8, (1, 4)),
         ("glowstone_dust", 8, (1, 4)), ("cooked_porkchop", 6, (1, 3)), ("soul_torch", 6, (2, 6)),
         ("crimson_fungus", 5, (1, 2)), ("warped_fungus", 5, (1, 2)), ("coal", 6, (1, 4))],
        [("magma_cream", 4, (1, 2)), ("blaze_powder", 3, (1, 1)), ("gold_ingot", 2, (1, 2))]),
    "end": (
        [("chorus_fruit", 16, (2, 6)), ("popped_chorus_fruit", 10, (1, 4)), ("glass_bottle", 6, (1, 3)),
         ("paper", 6, (2, 6)), ("end_rod", 6, (1, 2)), ("purpur_block", 6, (2, 6)), ("string", 4, (1, 3))],
        [("ender_pearl", 2, (1, 1)), ("experience_bottle", 3, (1, 2)), ("phantom_membrane", 2, (1, 1))]),
}
KINDS = list(TABLES)

# never in a barrel (validate.py): the good loot stays in the chests, progression items are earned
FORBIDDEN = ("structure_compass", "diamond", "netherite", "emerald_block", "enchanted_golden_apple", "golden_apple",
             "totem_of_undying", "elytra", "trident", "heart_of_the_sea", "smithing_template", "music_disc",
             "spawn_egg", "remembrance_", "lithite_shard", "ancient_ember", "void_shard", "mithril", "orichalcum",
             "aether_crystal", "arcane_", "_staff", "_wand", "_ring", "_amulet")
# a barrel's potion is a plain Potion of Healing
POTION = "minecraft:healing"


def table_json(kind):
    main, extra = TABLES[kind]

    def entry(name, weight, count):
        e = {"type": "minecraft:item", "name": name if ":" in name else f"minecraft:{name}", "weight": weight}
        fns = []
        if count != (1, 1):
            fns.append({"function": "minecraft:set_count",
                        "count": {"type": "minecraft:uniform", "min": count[0], "max": count[1]}, "add": False})
        if name == "potion":
            fns.append({"function": "minecraft:set_potion", "id": POTION})
        if fns:
            e["functions"] = fns
        return e
    extra_total = sum(w for _n, w, _c in extra)
    return {"type": "minecraft:chest", "pools": [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 3}, "bonus_rolls": 0.0,
         "entries": [entry(*e) for e in main]},
        # the extra pool adds something about one barrel in three
        {"rolls": 1, "bonus_rolls": 0.0,
         "entries": [entry(*e) for e in extra] + [{"type": "minecraft:empty", "weight": extra_total * 2}]},
    ], "random_sequence": f"{PREFIX}{kind}"}


# ------------------------------------------------------------------------------------------- choice
# interior.py room themes -> barrel kind (None: the structure's kind)
ROOM_KIND = {"home": "food", "hall": None, "barracks": "military", "kitchen": "food", "library": "library",
             "chapel": None, "workshop": "workshop", "forge": "workshop", "storage": "food", "lab": None,
             "steampunk": "clockwork", "nether": "nether", "end": "end", "camp": "military", "mine": "mine",
             "ruin": None, "crypt": None, "wreck": "harbour"}
# interior.py yard themes
YARD_KIND = {"farm": "food", "village": "food", "camp": "military", "harbour": "harbour", "ruin": None}

STRUCTURE_KIND = {
    "guild_outpost": "food", "mountain_monastery": "food", "forgotten_library": "library",
    "coastal_lighthouse": "harbour", "giant_tree": "sylvan", "desert_oasis": "food", "witch_huts": "sylvan",
    "sky_island": "food", "jungle_ziggurat": "sylvan", "ruined_watchtower": "military", "bandit_camp": "military",
    "rune_circle": "library", "ice_observatory": "library", "galleon_wreck": "harbour", "sunken_temple": "harbour",
    "dwarven_mine": "mine", "dwarven_forge": "mine", "crystal_grotto": "mine", "sealed_lab": "clockwork",
    "sunken_citadel": "harbour", "forgotten_catacombs": "food", "sand_hypogeum": "food", "lithite_well": "mine",
    "clockwork_citadel": "clockwork", "sky_harbour": "clockwork", "undercity": "clockwork", "dwarven_city": "mine",
    "sylvan_palace": "sylvan", "inventor_manor": "clockwork", "sky_isles": "sylvan", "geothermal_foundry": "workshop",
    "tesla_observatory": "clockwork", "crystal_cathedral": "library", "sunken_submarine": "harbour",
    "diving_bell": "harbour", "coral_shrine": "harbour", "shipwreck_debris": "harbour",
    # vanilla villages and outposts extended by wf/village.py, the sea-floor props of wf/ocean.py
    "village": "food", "pillager_outpost": "military", "ocean": "harbour",
}
# peaceful places where people live: their barrels are the residents' stores (still lootable, a bit fewer)
INHABITED = {"village", "guild_outpost", "mountain_monastery", "dwarven_city", "sylvan_palace", "clockwork_citadel",
             "sky_harbour", "inventor_manor", "sunken_citadel", "piglin_market", "undercity", "coastal_lighthouse"}

FILL = 0.70
FILL_INHABITED = 0.62

CONTAINERS = ("minecraft:barrel",)


def _is_container(name, data):
    if data is not None and "LootTable" in data:
        return False
    if name in CONTAINERS or name.endswith("_shulker_box") or name == "minecraft:shulker_box":
        return True
    return name in ("minecraft:chest", "minecraft:trapped_chest") and not data


def default_kind(sid, dimension="overworld"):
    if sid in STRUCTURE_KIND:
        return STRUCTURE_KIND[sid]
    return {"the_nether": "nether", "nether": "nether", "the_end": "end", "end": "end"}.get(dimension, "food")


def stock(bp, sid, dimension="overworld"):
    """Give the empty containers of ``bp`` their supplies. Returns {table: count, None: left empty}."""
    base = default_kind(sid, dimension)
    hints = getattr(bp, "barrel_hints", {})
    fill = FILL_INHABITED if sid in INHABITED else FILL
    rng = random.Random(f"barrels:{bp.name}")
    counts = {}
    for pos in sorted(bp.blocks):
        name, props, data = bp.blocks[pos]
        if not _is_container(name, data):
            continue
        # a plain chest is never left empty (an empty chest looks like a bug); barrels may be
        if not name.endswith("chest") and rng.random() >= fill:
            counts[None] = counts.get(None, 0) + 1
            continue
        kind = hints.get(pos) or base
        if dimension in ("nether", "the_nether") and kind in ("food", "harbour", "sylvan"):
            kind = "nether"  # a Nether storeroom keeps Nether food
        if dimension in ("end", "the_end") and kind in ("food", "harbour", "sylvan"):
            kind = "end"
        table = PREFIX + kind
        new = dict(data) if data else {}
        new["LootTable"] = nbt.String(table)
        bp.blocks[pos] = (name, props, new)
        counts[table] = counts.get(table, 0) + 1
    return counts


def merge(total, counts):
    for k, v in counts.items():
        total[k] = total.get(k, 0) + v
    return total


def summary(total):
    stocked = sum(v for k, v in total.items() if k)
    empty = total.get(None, 0)
    parts = ", ".join(f"{k[len(PREFIX):]} {v}" for k, v in sorted(((k, v) for k, v in total.items() if k),
                                                                     key=lambda kv: -kv[1]))
    return f"barrel supplies: {stocked} containers stocked ({parts}), {empty} barrels left empty"
