"""Standalone dungeons: a small surface entrance over several procedurally planned underground levels,
ending in a boss arena (see wf/dungeon.py). Each dungeon has three layouts."""
import math
import random

from .. import arch
from ..arch import stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..dungeon import Dungeon, Theme, build
from ..parts import LOOT, MOB

CATACOMBS = Theme(
    "catacombs",
    wall=["wayfarers:guild_bricks"] * 4 + ["wayfarers:mossy_guild_bricks"] * 2 + ["wayfarers:cracked_guild_bricks",
                                                                                 "tuff_bricks"],
    floor=["polished_tuff", "tuff_bricks", "wayfarers:polished_guild_stone"],
    trim="wayfarers:guild_brick", pillar="wayfarers:polished_guild_stone", ceiling=["tuff_bricks", "stone_bricks"],
    cracked="wayfarers:cracked_guild_bricks", accent="wayfarers:carved_guild_stone", light="lantern",
    candle="candle", spawners=("wayfarers:skeleton_knight", "wayfarers:crypt_crawler", "minecraft:zombie"),
)
HYPOGEUM = Theme(
    "hypogeum",
    wall=["sandstone"] * 3 + ["cut_sandstone", "smooth_sandstone", "sandstone"],
    floor=["smooth_sandstone", "cut_sandstone"], trim="sandstone", pillar="cut_sandstone",
    ceiling=["sandstone", "smooth_sandstone"], cracked="chiseled_sandstone", accent="chiseled_red_sandstone",
    light="lantern", candle="orange_candle", skull="skeleton_skull",
    spawners=("wayfarers:crypt_crawler", "minecraft:husk"),
)
LITHITE = Theme(
    "lithite",
    wall=["deepslate_bricks"] * 3 + ["cracked_deepslate_bricks", "deepslate_tiles", "wayfarers:lithite_bricks"],
    floor=["polished_deepslate", "deepslate_tiles"], trim="deepslate_brick", pillar="wayfarers:lithite_bricks",
    ceiling=["deepslate_tiles", "cobbled_deepslate"], cracked="cracked_deepslate_tiles", accent="wayfarers:lithite_block",
    light="soul_lantern", candle="cyan_candle",
    spawners=("minecraft:cave_spider", MOB["map_wraith"], "minecraft:skeleton"),
)
VOID = Theme(
    "void",
    wall=["wayfarers:void_bricks"] * 4 + ["end_stone_bricks", "purpur_block"],
    floor=["purpur_block", "wayfarers:void_bricks"], trim="wayfarers:void_brick", pillar="purpur_pillar",
    ceiling=["end_stone_bricks", "wayfarers:void_bricks"], cracked="end_stone", accent="wayfarers:starlight_block",
    light="end_rod", candle="purple_candle", bones="purpur_pillar",
    spawners=("minecraft:endermite", MOB["void_stalker"]),
)


# ------------------------------------------------------------------ surface entrances
def mausoleum(bp, t, x, z):
    """Catacombs: a gothic crypt chapel in a walled graveyard; the stairwell opens in its nave."""
    rng = random.Random(x * 31 + z)
    hw, hd = 7, 9                      # half width (x) and half depth (z) of the chapel
    W, B, M, C = ("wayfarers:guild_bricks", "wayfarers:polished_guild_stone", "wayfarers:mossy_guild_bricks",
                  "wayfarers:carved_guild_stone")
    # ground: grass, a gravel path from the south gate to the door
    for xx in range(x - hw - 8, x + hw + 9):
        for zz in range(z - hd - 7, z + hd + 10):
            if (xx, -1, zz) not in bp.blocks:
                bp.set(xx, -1, zz, "grass_block[snowy=false]")
    for zz in range(z + hd + 1, z + hd + 10):
        for dx in (-1, 0, 1):
            bp.set(x + dx, -1, zz, "gravel" if (zz + dx) % 3 else "coarse_dirt")
    # plinth and front steps
    for xx in range(x - hw - 1, x + hw + 2):
        for zz in range(z - hd - 1, z + hd + 2):
            if math.hypot(xx - x, zz - z) > 4.4:
                bp.set(xx, 0, zz, B)
    for dx in range(-2, 3):
        bp.set(x + dx, 0, z + hd + 2, stair("wayfarers:polished_guild_stone_stairs", "north"))
    # walls: brick with a moss tide line, quoins of polished stone
    for xx in range(x - hw, x + hw + 1):
        for zz in range(z - hd, z + hd + 1):
            if abs(xx - x) != hw and abs(zz - z) != hd:
                continue
            for y in range(1, 9):
                corner = abs(xx - x) == hw and abs(zz - z) == hd
                bp.set(xx, y, zz, B if corner or y == 8 else (M if y <= 2 and rng.random() < 0.5 else W))
    # buttresses with stepped tops along the long sides
    for zz in range(z - hd + 3, z + hd - 1, 4):
        for side in (-1, 1):
            bx = x + side * (hw + 1)
            for y in range(1, 7):
                bp.set(bx, y, zz, B)
            bp.set(bx, 7, zz, stair("wayfarers:guild_brick_stairs", "east" if side < 0 else "west"))
            bp.set(bx + side, 1, zz, B)
            bp.set(bx + side, 2, zz, stair("wayfarers:guild_brick_stairs", "east" if side < 0 else "west"))
            # lancet windows between buttresses
            for y in range(3, 7):
                bp.set(x + side * hw, y, zz - 2, "purple_stained_glass_pane" if y > 3 else
                       "black_stained_glass_pane")
    # pointed doorway in the south gable, carved stone surround
    for y in range(1, 6):
        w = 1 if y < 5 else 0
        for dx in range(-w, w + 1):
            bp.set(x + dx, y, z + hd, "air")
    for y in range(1, 7):
        for dx in (-2, 2):
            bp.set(x + dx, y, z + hd, C if y in (1, 6) else B)
    bp.set(x - 1, 6, z + hd, stair("wayfarers:polished_guild_stone_stairs", "east", "top"))
    bp.set(x + 1, 6, z + hd, stair("wayfarers:polished_guild_stone_stairs", "west", "top"))
    bp.set(x, 7, z + hd, C)
    # gables and a steep slate roof, ridge cross and corner pinnacles
    arch.steep_roof(bp, x - hw - 1, z - hd - 1, x + hw + 1, z + hd + 1, 9, "wayfarers:slate_roof_tile_stairs",
                    axis="z", overhang=1, steep=1, fill="wayfarers:slate_roof_tiles")
    top = 9 + hw + 1
    for y in range(top - 1, top + 3):
        bp.set(x, y, z + hd, B)
    bp.set(x - 1, top + 1, z + hd, B)
    bp.set(x + 1, top + 1, z + hd, B)
    for cx, cz in ((x - hw, z - hd), (x + hw, z - hd), (x - hw, z + hd), (x + hw, z + hd)):
        for y in range(9, 12):
            bp.set(cx, y, cz, B)
        bp.set(cx, 12, cz, "wayfarers:guild_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
        bp.set(cx, 13, cz, "lantern[hanging=false,waterlogged=false]")
    # interior: a balustrade around the stairwell, candles, two sarcophagi, hanging lanterns
    for a in range(0, 360, 15):
        bx = int(round(x + math.cos(math.radians(a)) * 5))
        bz = int(round(z + math.sin(math.radians(a)) * 5))
        if bz < z + 4 or abs(bx - x) > 1:
            bp.set(bx, 1, bz, "wayfarers:guild_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
    for side in (-1, 1):
        for dz in (-6, -5):
            bp.set(x + side * 5, 1, z + dz, B)
            bp.set(x + side * 5, 2, z + dz, "wayfarers:guild_brick_slab[type=bottom,waterlogged=false]")
        bp.set(x + side * 5, 1, z + 6, "candle[candles=3,lit=true,waterlogged=false]")
        bp.set(x + side * 3, 7, z, "iron_chain[axis=y,waterlogged=false]")
        bp.set(x + side * 3, 6, z, "lantern[hanging=true,waterlogged=false]")
    # angel statues flanking the steps
    for side in (-1, 1):
        sx = x + side * 4
        sz = z + hd + 3
        bp.set(sx, 0, sz, B)
        bp.set(sx, 1, sz, "calcite")
        bp.set(sx, 2, sz, "calcite")
        bp.set(sx, 3, sz, "skeleton_skull[rotation=0,powered=false]")
        bp.set(sx - 1, 2, sz, "end_rod[facing=west]")
        bp.set(sx + 1, 2, sz, "end_rod[facing=east]")
    # graveyard: rows of tombstones, a low wall with an iron gate, dead trees, lantern posts
    for row in range(3):
        for i in range(-3, 4):
            gx = x + i * 3 + (row % 2)
            gz = z - hd - 3 - row * 2 if row < 2 else z + hd + 5
            if abs(gx - x) <= 2 and gz > z:
                continue
            if rng.random() < 0.8:
                bp.set(gx, 0, gz, rng.choice(("mossy_stone_bricks", "stone_bricks", "cracked_stone_bricks")))
                bp.set(gx, 1, gz, rng.choice(("stone_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]",
                                              "mossy_stone_brick_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")))
                bp.set(gx, -1, gz + 1, "podzol")
    for xx in range(x - hw - 7, x + hw + 8):
        for zz in (z - hd - 7, z + hd + 9):
            if not (zz > z and abs(xx - x) <= 1):
                bp.set(xx, 0, zz, "mossy_cobblestone_wall[east=low,north=none,south=none,west=low,up=false,waterlogged=false]"
                       if rng.random() < 0.85 else "air")
    for zz in range(z - hd - 7, z + hd + 10):
        for xx in (x - hw - 7, x + hw + 7):
            bp.set(xx, 0, zz, "mossy_cobblestone_wall[east=none,north=low,south=low,west=none,up=false,waterlogged=false]"
                   if rng.random() < 0.85 else "air")
    for side in (-1, 1):
        for y in range(0, 4):
            bp.set(x + side * 2, y, z + hd + 9, B)
        bp.set(x + side * 2, 4, z + hd + 9, "lantern[hanging=false,waterlogged=false]")
    arch.dark_tree(bp, x - hw - 5, 0, z + hd + 5, h=9, seed=3)
    arch.dark_tree(bp, x + hw + 4, 0, z - hd - 4, h=7, seed=8)


def sand_gate(bp, t, x, z):
    """Hypogeum: a half-buried temple gate between two leaning obelisks; steps lead down."""
    r = 6
    for xx in range(x - r - 3, x + r + 4):
        for zz in range(z - r - 3, z + r + 4):
            d = math.hypot(xx - x, zz - z)
            if d <= 4.4:
                continue
            h = max(0, int(2 - d / 4)) if d < r + 3 else 0
            for y in range(-1, h):
                bp.set(xx, y, zz, "sand")
    for xx in range(x - r, x + r + 1):
        for zz in range(z - r, z + r + 1):
            if math.hypot(xx - x, zz - z) <= 4.4:
                continue
            bp.set(xx, 0, zz, "smooth_sandstone")
            if abs(xx - x) == r or abs(zz - z) == r:
                for y in range(1, 6):
                    bp.set(xx, y, zz, "cut_sandstone" if y in (1, 5) else "sandstone")
    for y in range(1, 5):
        for dx in (-1, 0, 1):
            bp.set(x + dx, y, z + r, "air")
    for xx in range(x - r - 1, x + r + 2):
        for zz in range(z - r - 1, z + r + 2):
            if abs(xx - x) == r + 1 or abs(zz - z) == r + 1:
                bp.set(xx, 6, zz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
            elif math.hypot(xx - x, zz - z) > 2:
                bp.set(xx, 6, zz, "chiseled_sandstone" if (xx + zz) % 4 == 0 else "smooth_sandstone")
    for dx in (-1, 0, 1):
        bp.set(x + dx, 5, z + r, "chiseled_red_sandstone")
    for side in (-1, 1):
        ox = x + side * (r + 3)
        for y in range(0, 10):
            bp.set(ox, y, z + r, "smooth_sandstone" if y < 9 else "gold_block")
        bp.set(ox, 4, z + r + 1, "chiseled_red_sandstone")
    bp.set(x, 4, z + r - 1, "lantern[hanging=true,waterlogged=false]")


def well_head(bp, t, x, z):
    """Lithite well: a mine head of deepslate with a timber winch over the shaft."""
    for xx in range(x - 6, x + 7):
        for zz in range(z - 6, z + 7):
            d = math.hypot(xx - x, zz - z)
            if d <= 4.4:
                continue
            if d <= 6.2:
                bp.set(xx, 0, zz, "polished_deepslate")
                if d > 5.2:
                    bp.set(xx, 1, zz, "deepslate_brick_wall[east=low,north=low,south=low,west=low,up=true,waterlogged=false]"
                           if (xx + zz) % 2 else "wayfarers:lithite_bricks")
    for sx, sz in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        for y in range(0, 9):
            bp.set(x + sx, y, z + sz, "dark_oak_log[axis=y]")
    for xx in range(x - 5, x + 6):
        bp.set(xx, 9, z - 5, "dark_oak_log[axis=x]")
        bp.set(xx, 9, z + 5, "dark_oak_log[axis=x]")
    for zz in range(z - 5, z + 6):
        bp.set(x, 10, zz, "dark_oak_log[axis=z]")
        bp.set(x - 5, 9, zz, "dark_oak_log[axis=z]")
        bp.set(x + 5, 9, zz, "dark_oak_log[axis=z]")
    for y in range(1, 10):
        bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")
    bp.set(x, 1, z, "wayfarers:lithite_block")
    for sx in (-5, 5):
        bp.set(x + sx, 8, z, "soul_lantern[hanging=true,waterlogged=false]")
    for zz in range(z - 4, z + 5):
        bp.set(x + 7, 0, zz, "rail[shape=north_south,waterlogged=false]")


def void_obelisk(bp, t, x, z):
    """Void crypt: a ring of void-brick obelisks with starlight caps around the stair."""
    for xx in range(x - 6, x + 7):
        for zz in range(z - 6, z + 7):
            d = math.hypot(xx - x, zz - z)
            if 4.4 < d <= 6.4:
                bp.set(xx, 0, zz, "purpur_block" if (xx + zz) % 3 else "wayfarers:void_bricks")
    for i in range(6):
        a = math.pi * 2 * i / 6
        ox, oz = int(round(x + math.cos(a) * 8)), int(round(z + math.sin(a) * 8))
        h = 7 + (i % 3) * 2
        for y in range(0, h):
            bp.set(ox, y, oz, "wayfarers:void_bricks")
        bp.set(ox, h, oz, "wayfarers:starlight_block")
        bp.set(ox, h + 1, oz, "end_rod[facing=up]")


def _register(sid, theme, entrance, biomes, title_fr, title_en, boss, loot, levels=3, spacing=34, **kw):
    pieces = []
    for i in range(3):
        def builder(bp, i=i):
            build(bp, theme, f"{sid}-{i}", boss, Dungeon(LOOT + loot, LOOT + loot + "_treasure", LOOT + loot + "_reward"),
                  levels=levels, entrance_fn=entrance)
        pieces.append(Piece(f"layout_{i}", builder))
    register(StructureDef(sid, kw.pop("dimension", "overworld"), biomes, pieces, spacing=spacing, separation=12,
                          processors="none", title_fr=title_fr, title_en=title_en, **kw))


_register("forgotten_catacombs", CATACOMBS, mausoleum,
          ["plains", "forest", "birch_forest", "dark_forest", "old_growth_birch_forest", "meadow", "taiga",
           "flower_forest", "cherry_grove"],
          "Catacombes oubliées", "Forgotten Catacombs", "wayfarers:grave_knight", "catacombs",
          spawns=[("wayfarers:skeleton_knight", 10, 1, 2), ("wayfarers:crypt_crawler", 8, 1, 2), ("minecraft:zombie", 8, 1, 2)])
_register("sand_hypogeum", HYPOGEUM, sand_gate, ["desert", "badlands", "wooded_badlands", "eroded_badlands"],
          "Hypogée des sables", "Sand Hypogeum", "wayfarers:bone_matriarch", "hypogeum",
          spawns=[("wayfarers:crypt_crawler", 10, 1, 2), ("minecraft:husk", 10, 1, 2)])
_register("lithite_well", LITHITE, well_head,
          ["windswept_hills", "windswept_forest", "windswept_gravelly_hills", "grove", "snowy_slopes", "jagged_peaks",
           "stony_peaks", "old_growth_spruce_taiga"],
          "Puits de lithite", "Lithite Well", "wayfarers:weeping_lady", "lithite_well",
          spawns=[("minecraft:cave_spider", 8, 1, 2), (MOB["map_wraith"], 8, 1, 1), ("minecraft:skeleton", 8, 1, 2)])
_register("void_crypt", VOID, void_obelisk, ["end_highlands", "end_midlands"],
          "Crypte du vide", "Void Crypt", "wayfarers:larva_mother", "void_crypt", levels=2, spacing=30,
          dimension="end", spawns=[("minecraft:endermite", 8, 1, 2), (MOB["void_stalker"], 8, 1, 1)])
