"""Chisel families: blocks the Engraver's Chisel (and the Chisel Table) turn into each other, for free.

Each family is an ordered loop: right-click a block with the chisel to get the next member, sneak-right-click for
the previous one. Stairs, slabs and walls get their own families so the shape (facing, half, type...) is kept.
gen_data writes one data/brasshaven/chisel/<family>.json per family ({"blocks": [...]}); the game loads them
(ChiselFamilies, reloadable with /reload) and datapacks may add their own files in data/<ns>/chisel/.

Rules: a block belongs to one family only; no family turns something cheap into something that drops loot
(no gilded blackstone, no ores, no infested blocks); no family mixes blocks of different worth (the stonecutter's
1 -> 4 recipes must not run backwards: no copper block with cut copper); blocks with a block entity are refused by
the game anyway.
"""
from . import decor

W = "brasshaven:"


def _mc(*ids):
    return [f"minecraft:{i}" for i in ids]


def _mod(*ids):
    return [W + i for i in ids]


def _shapes(name, full, stairs=(), slabs=(), walls=()):
    """A full-block family plus its stairs / slab / wall families (only those with at least two members)."""
    out = {name: full}
    for suffix, ids in (("stairs", stairs), ("slabs", slabs), ("walls", walls)):
        if len(ids) >= 2:
            out[f"{name}_{suffix}"] = list(ids)
    return out


FAMILIES = {}
# ---------------------------------------------------------------- vanilla stone
FAMILIES.update(_shapes(
    "stone", _mc("stone", "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "chiseled_stone_bricks",
                 "smooth_stone"),
    stairs=_mc("stone_stairs", "stone_brick_stairs", "mossy_stone_brick_stairs"),
    slabs=_mc("stone_slab", "smooth_stone_slab", "stone_brick_slab", "mossy_stone_brick_slab"),
    walls=_mc("stone_brick_wall", "mossy_stone_brick_wall")))
FAMILIES.update(_shapes(
    "cobblestone", _mc("cobblestone", "mossy_cobblestone"),
    stairs=_mc("cobblestone_stairs", "mossy_cobblestone_stairs"),
    slabs=_mc("cobblestone_slab", "mossy_cobblestone_slab"),
    walls=_mc("cobblestone_wall", "mossy_cobblestone_wall")))
for _rock in ("granite", "diorite", "andesite"):
    FAMILIES.update(_shapes(
        _rock, _mc(_rock, f"polished_{_rock}"),
        stairs=_mc(f"{_rock}_stairs", f"polished_{_rock}_stairs"),
        slabs=_mc(f"{_rock}_slab", f"polished_{_rock}_slab")))
FAMILIES.update(_shapes(
    "deepslate", _mc("cobbled_deepslate", "deepslate", "polished_deepslate", "deepslate_bricks",
                     "cracked_deepslate_bricks", "deepslate_tiles", "cracked_deepslate_tiles", "chiseled_deepslate"),
    stairs=_mc("cobbled_deepslate_stairs", "polished_deepslate_stairs", "deepslate_brick_stairs", "deepslate_tile_stairs"),
    slabs=_mc("cobbled_deepslate_slab", "polished_deepslate_slab", "deepslate_brick_slab", "deepslate_tile_slab"),
    walls=_mc("cobbled_deepslate_wall", "polished_deepslate_wall", "deepslate_brick_wall", "deepslate_tile_wall")))
FAMILIES.update(_shapes(
    "tuff", _mc("tuff", "polished_tuff", "tuff_bricks", "chiseled_tuff", "chiseled_tuff_bricks"),
    stairs=_mc("tuff_stairs", "polished_tuff_stairs", "tuff_brick_stairs"),
    slabs=_mc("tuff_slab", "polished_tuff_slab", "tuff_brick_slab"),
    walls=_mc("tuff_wall", "polished_tuff_wall", "tuff_brick_wall")))
for _sand in ("sandstone", "red_sandstone"):
    FAMILIES.update(_shapes(
        _sand, _mc(_sand, f"chiseled_{_sand}", f"cut_{_sand}", f"smooth_{_sand}"),
        stairs=_mc(f"{_sand}_stairs", f"smooth_{_sand}_stairs"),
        slabs=_mc(f"{_sand}_slab", f"cut_{_sand}_slab", f"smooth_{_sand}_slab")))
FAMILIES.update(_shapes(
    "mud", _mc("packed_mud", "mud_bricks")))
FAMILIES.update(_shapes(
    "resin", _mc("resin_bricks", "chiseled_resin_bricks")))
# ---------------------------------------------------------------- nether & end
FAMILIES.update(_shapes(
    "quartz", _mc("quartz_block", "quartz_bricks", "chiseled_quartz_block", "quartz_pillar", "smooth_quartz"),
    stairs=_mc("quartz_stairs", "smooth_quartz_stairs"),
    slabs=_mc("quartz_slab", "smooth_quartz_slab")))
FAMILIES.update(_shapes(
    "blackstone", _mc("blackstone", "polished_blackstone", "polished_blackstone_bricks",
                      "cracked_polished_blackstone_bricks", "chiseled_polished_blackstone"),
    stairs=_mc("blackstone_stairs", "polished_blackstone_stairs", "polished_blackstone_brick_stairs"),
    slabs=_mc("blackstone_slab", "polished_blackstone_slab", "polished_blackstone_brick_slab"),
    walls=_mc("blackstone_wall", "polished_blackstone_wall", "polished_blackstone_brick_wall")))
FAMILIES["basalt"] = _mc("basalt", "polished_basalt", "smooth_basalt")
FAMILIES.update(_shapes(
    "nether_bricks", _mc("nether_bricks", "cracked_nether_bricks", "chiseled_nether_bricks", "red_nether_bricks"),
    stairs=_mc("nether_brick_stairs", "red_nether_brick_stairs"),
    slabs=_mc("nether_brick_slab", "red_nether_brick_slab"),
    walls=_mc("nether_brick_wall", "red_nether_brick_wall")))
FAMILIES["end_stone"] = _mc("end_stone", "end_stone_bricks")
FAMILIES["purpur"] = _mc("purpur_block", "purpur_pillar")
# ---------------------------------------------------------------- ocean
FAMILIES.update(_shapes(
    "prismarine", _mc("prismarine", "prismarine_bricks", "dark_prismarine"),
    stairs=_mc("prismarine_stairs", "prismarine_brick_stairs", "dark_prismarine_stairs"),
    slabs=_mc("prismarine_slab", "prismarine_brick_slab", "dark_prismarine_slab")))
# ---------------------------------------------------------------- terracotta: plain <-> glazed, per colour
COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan",
          "purple", "blue", "brown", "green", "red", "black"]
for _c in COLORS:
    FAMILIES[f"{_c}_terracotta"] = _mc(f"{_c}_terracotta", f"{_c}_glazed_terracotta")
# ---------------------------------------------------------------- copper: one family per oxidation level and wax,
# so chiselling never cleans, ages or unwaxes a block. The full copper block stays out: the stonecutter makes four
# cut copper, chiseled copper or grates from one block, so turning them back into blocks (9 ingots each) would
# multiply copper.
for _wax in ("", "waxed_"):
    for _age in ("", "exposed_", "weathered_", "oxidized_"):
        FAMILIES[f"{_wax}{_age}copper"] = _mc(f"{_wax}{_age}cut_copper", f"{_wax}{_age}chiseled_copper",
                                              f"{_wax}{_age}copper_grate")

# ---------------------------------------------------------------- Brasshaven decor (tools/wf/decor.py)
def _v(bid, v):
    return W + decor.variant_id(bid, v)


FAMILIES.update(_shapes(
    "guild_stone", _mod("guild_bricks", "mossy_guild_bricks", "cracked_guild_bricks", "polished_guild_stone",
                        "carved_guild_stone", "guild_tiles"),
    stairs=[_v("guild_bricks", "stairs"), _v("mossy_guild_bricks", "stairs"), _v("polished_guild_stone", "stairs")],
    slabs=[_v("guild_bricks", "slab"), _v("mossy_guild_bricks", "slab"), _v("polished_guild_stone", "slab")],
    walls=[_v("guild_bricks", "wall"), _v("mossy_guild_bricks", "wall")]))
FAMILIES["lithite_stone"] = _mod("lithite_bricks", "chiseled_lithite_bricks")
FAMILIES["ember_stone"] = _mod("ember_bricks", "chiseled_ember_bricks")
FAMILIES["void_stone"] = _mod("void_bricks", "chiseled_void_bricks")
FAMILIES.update(_shapes(
    "brass", _mod("brass_plating", "brass_tiles", "engraved_brass", "brass_grille"),
    stairs=[_v("brass_plating", "stairs"), _v("brass_tiles", "stairs")],
    slabs=[_v("brass_plating", "slab"), _v("brass_tiles", "slab")]))
FAMILIES.update(_shapes(
    "copper_plating", _mod("copper_plating", "verdigris_plating", "copper_pipes", "copper_tiles"),
    stairs=[_v("copper_plating", "stairs"), _v("verdigris_plating", "stairs"), _v("copper_tiles", "stairs")],
    slabs=[_v("copper_plating", "slab"), _v("verdigris_plating", "slab"), _v("copper_tiles", "slab")]))
FAMILIES.update(_shapes(
    "dark_iron", _mod("dark_iron_plating", "diamond_plate", "dark_iron_bricks", "gear_panel", "pressure_gauge"),
    stairs=[_v("dark_iron_plating", "stairs"), _v("diamond_plate", "stairs"), _v("dark_iron_bricks", "stairs")],
    slabs=[_v("dark_iron_plating", "slab"), _v("diamond_plate", "slab"), _v("dark_iron_bricks", "slab")],
    walls=[_v("dark_iron_plating", "wall"), _v("dark_iron_bricks", "wall")]))
FAMILIES.update(_shapes(
    "smokestack", _mod("smokestack_bricks", "sooty_smokestack_bricks"),
    stairs=[_v("smokestack_bricks", "stairs"), _v("sooty_smokestack_bricks", "stairs")],
    slabs=[_v("smokestack_bricks", "slab"), _v("sooty_smokestack_bricks", "slab")],
    walls=[_v("smokestack_bricks", "wall"), _v("sooty_smokestack_bricks", "wall")]))
FAMILIES.update(_shapes(
    "mahogany", _mod("mahogany_panelling", "mahogany_parquet"),
    stairs=[_v("mahogany_panelling", "stairs"), _v("mahogany_parquet", "stairs")],
    slabs=[_v("mahogany_panelling", "slab"), _v("mahogany_parquet", "slab")]))
# ---------------------------------------------------------------- world stones (decor.py WORLD_STONES)
FAMILIES.update(_shapes(
    "marble", _mod("marble", "polished_marble", "marble_bricks", "marble_pillar", "chiseled_marble"),
    stairs=[_v("marble", "stairs"), _v("polished_marble", "stairs"), _v("marble_bricks", "stairs")],
    slabs=[_v("marble", "slab"), _v("polished_marble", "slab"), _v("marble_bricks", "slab")],
    walls=[_v("marble", "wall"), _v("marble_bricks", "wall")]))
FAMILIES.update(_shapes(
    "rust_rock", _mod("rust_rock", "polished_rust_rock", "rust_rock_bricks"),
    stairs=[_v("rust_rock", "stairs"), _v("polished_rust_rock", "stairs"), _v("rust_rock_bricks", "stairs")],
    slabs=[_v("rust_rock", "slab"), _v("polished_rust_rock", "slab"), _v("rust_rock_bricks", "slab")],
    walls=[_v("rust_rock", "wall"), _v("rust_rock_bricks", "wall")]))
FAMILIES.update(_shapes(
    "blue_slate", _mod("blue_slate", "polished_blue_slate", "blue_slate_bricks", "blue_slate_tiles"),
    stairs=[_v("blue_slate", "stairs"), _v("polished_blue_slate", "stairs"), _v("blue_slate_bricks", "stairs"),
            _v("blue_slate_tiles", "stairs")],
    slabs=[_v("blue_slate", "slab"), _v("polished_blue_slate", "slab"), _v("blue_slate_bricks", "slab"),
           _v("blue_slate_tiles", "slab")],
    walls=[_v("blue_slate", "wall"), _v("blue_slate_bricks", "wall"), _v("blue_slate_tiles", "wall")]))


def all_ids():
    return [b for fam in FAMILIES.values() for b in fam]


def check(vanilla_blocks, mod_blocks):
    """Problems with the table: unknown ids, duplicates, one-member families. Returns a list of messages."""
    problems, seen = [], {}
    for name, fam in FAMILIES.items():
        if len(fam) < 2:
            problems.append(f"chisel family {name}: needs at least two blocks")
        for b in fam:
            ns, path = b.split(":")
            if (ns == "minecraft" and path not in vanilla_blocks) or (ns == "brasshaven" and path not in mod_blocks):
                problems.append(f"chisel family {name}: unknown block {b}")
            if b in seen:
                problems.append(f"chisel family {name}: {b} is already in family {seen[b]}")
            seen[b] = name
    return problems


def data_files():
    """{relative path under data/: json object} for gen_data."""
    return {f"brasshaven/chisel/{name}.json": {"blocks": fam} for name, fam in FAMILIES.items()}
