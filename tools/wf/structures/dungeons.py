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
    """Hypogeum: a half-buried desert temple. From the dunes in the south a monumental stair guarded by two
    sphinxes descends into an excavated forecourt lined with jackal statues and obelisks; a battered pylon gate
    with a winged sun disk opens on a hypostyle hall whose roof is open over the stairwell, and the dunes pile up
    against its sides and back. The stairwell opening (radius 4.4 around (x, z), y <= 3) stays clear."""
    rng = random.Random(x * 17 + z * 5 + 3)
    S, CUT, SM, CH = "sandstone", "cut_sandstone", "smooth_sandstone", "chiseled_sandstone"
    RED, CRED = "chiseled_red_sandstone", "cut_red_sandstone"
    TOP = 5                              # dune / stair-head level (walking surface y = 6)
    HX0, HX1, HZ0, HZ1 = -9, 9, -11, 5   # hypostyle hall walls (relative)
    WALL_H = 8                           # roof at y = 8

    def opening(dx, y, dz):
        return y <= 3 and dx * dx + dz * dz <= 4.4 * 4.4

    def put(dx, y, dz, spec):
        if not opening(dx, y, dz):
            bp.set(x + dx, y, z + dz, spec)

    def sst(facing, half="bottom", block="sandstone_stairs"):
        return stair(block, facing, half)

    # ---------------------------------------------------------------- dunes (half-burying the temple)
    def in_hall(dx, dz, m=0):
        return HX0 - m <= dx <= HX1 + m and HZ0 - m <= dz <= HZ1 + m

    def in_court(dx, dz):          # the excavated forecourt and the stair corridor stay open
        return abs(dx) <= 8 and HZ1 < dz <= 23

    def dune_h(dx, dz):
        ox = max(HX0 - dx, 0, dx - HX1)
        oz = max(HZ0 - dz, 0, dz - HZ1)
        near = math.hypot(ox, oz)
        h = 6.6 - 0.42 * near + 1.4 * math.sin(dx * 0.31 + x * 0.1) * math.cos(dz * 0.27 - z * 0.1)
        if dz > HZ1:                # the south side was dug out: dunes stand level with the stair head
            h = max(h, TOP + 0.6 + 0.8 * math.sin(dx * 0.4)) if abs(dx) <= 14 and dz <= 26 else h
        r = math.hypot(dx, dz * 0.9)
        h *= max(0.0, min(1.0, (27 - r) / 7))
        if dz < HZ0 - 1 and abs(dx) < 6:
            h += 1.2              # drift heaped against the back wall
        return h

    for dx in range(-27, 28):
        for dz in range(-26, 31):
            if in_hall(dx, dz) or in_court(dx, dz) or dx * dx + dz * dz <= 4.6 * 4.6:
                continue
            hf = max(0.0, dune_h(dx, dz))
            h = int(hf)
            put(dx, -1, dz, "sandstone")
            for y in range(0, h):
                put(dx, y, dz, "sand" if y >= h - 2 else "sandstone")
            if hf - h >= 0.5:     # half steps soften the dune terraces
                put(dx, h, dz, "sandstone_slab[type=bottom,waterlogged=false]")
            elif h > 0 and rng.random() < 0.025:
                put(dx, h, dz, "dead_bush")

    # ---------------------------------------------------------------- forecourt floor and retaining walls
    for dx in range(-8, 9):
        for dz in range(HZ1 + 1, 17):
            put(dx, -1, dz, S)
            path = abs(dx) <= 2
            put(dx, 0, dz, CUT if path and (dz % 4) else RED if path else (SM if (dx + dz) % 5 else CH))
            for y in range(1, TOP + 3):
                put(dx, y, dz, "air")
    for side in (-1, 1):
        wx = 9 * side
        for dz in range(HZ1 + 3, 17):
            top = TOP
            for y in range(0, top + 1):
                put(wx, y, dz, CUT if y in (0, top) else (S if (y + dz) % 4 else CH))
            put(wx, top + 1, dz, sst("east" if side > 0 else "west", "bottom", "smooth_sandstone_stairs") if dz % 3 else CH)
    # drifted sand in the forecourt corners, a fallen column drum
    for dx, dz in ((-8, 15), (-7, 16), (-8, 16), (8, 14), (8, 15), (7, 16), (8, 16), (-8, 8)):
        put(dx, 1, dz, "sand")
    for dx, dz in ((-8, 16), (8, 16)):
        put(dx, 2, dz, "sand")
    for i in range(3):
        put(4 + i, 1, 15, CUT if i != 1 else CH)

    # ---------------------------------------------------------------- monumental stair up to the dunes
    for k in range(0, TOP + 1):
        dz = 17 + k
        for dx in range(-8, 9):
            put(dx, -1, dz, S)
            if abs(dx) <= 5:
                for y in range(0, k + 1):
                    put(dx, y, dz, S)
                if k < TOP:
                    put(dx, k + 1, dz, sst("south", block="smooth_sandstone_stairs" if abs(dx) <= 3 else "sandstone_stairs"))
                else:
                    put(dx, k + 1, dz, CUT if abs(dx) % 3 else RED)
                for y in range(k + 2, k + 6):
                    put(dx, y, dz, "air")
            else:   # terraces either side, level with the dunes, edged with a stepped coping
                for y in range(0, TOP + 1):
                    put(dx, y, dz, S if y < TOP else (CUT if abs(dx) == 6 else SM))
                if abs(dx) == 6:
                    put(dx, TOP + 1, dz, "cut_sandstone_slab[type=bottom,waterlogged=false]")
    for dz in range(23, 27):     # landing at the stair head
        for dx in range(-5, 6):
            put(dx, TOP, dz, SM)
            put(dx, TOP + 1, dz, CUT if (dx + dz) % 2 else SM)
            for y in range(TOP + 2, TOP + 6):
                put(dx, y, dz, "air")

    # ---------------------------------------------------------------- sphinxes flanking the stair head (facing south)
    def sphinx(sx, sz, y0):
        for dx in range(-2, 3):                     # plinth
            for dz in range(-6, 3):
                put(sx + dx, y0, sz + dz, CUT if dx in (-2, 2) or dz in (-6, 2) else SM)
        for dx in range(-1, 2):                     # lion body
            for dz in range(-5, 0):
                put(sx + dx, y0 + 1, sz + dz, S)
                put(sx + dx, y0 + 2, sz + dz, S if dz > -5 else sst("north", block="sandstone_stairs"))
        put(sx - 1, y0 + 1, sz + 1, sst("south", block="sandstone_stairs"))   # paws
        put(sx + 1, y0 + 1, sz + 1, sst("south", block="sandstone_stairs"))
        put(sx, y0 + 1, sz + 1, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
        for dx in range(-1, 2):                     # chest
            put(sx + dx, y0 + 1, sz, S)
            put(sx + dx, y0 + 2, sz, S)
        put(sx, y0 + 3, sz, CH)                     # face
        put(sx, y0 + 3, sz + 1, sst("north", "top", "sandstone_stairs"))      # chin / beard
        put(sx - 1, y0 + 3, sz, "lapis_block")      # nemes headdress lappets
        put(sx + 1, y0 + 3, sz, "lapis_block")
        put(sx - 1, y0 + 2, sz + 1, "gold_block")
        put(sx + 1, y0 + 2, sz + 1, "gold_block")
        put(sx, y0 + 4, sz, "gold_block")
        put(sx, y0 + 4, sz - 1, "lapis_block")
        put(sx, y0 + 3, sz - 1, "gold_block")
        put(sx, y0 + 5, sz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
        put(sx, y0 + 1, sz - 6, "sandstone_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")  # tail tuft
    for side in (-1, 1):
        sphinx(9 * side, 25, TOP + 1)

    # ---------------------------------------------------------------- obelisks before the pylon, jackal statues on the walls
    def obelisk(ox, oz, h, broken=False):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                put(ox + dx, 1, oz + dz, CUT if dx and dz else SM)
                put(ox + dx, 2, oz + dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]" if dx and dz else CUT)
        top = 3 + (h - 4 if broken else h)
        for y in range(3, top):
            put(ox, y, oz, CH if (y - 3) % 4 == 1 else ("orange_terracotta" if (y - 3) % 4 == 3 and y > 4 else SM))
            if y < 3 + h * 0.45:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(ox + dx, y, oz + dz, "smooth_sandstone_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]"
                        % {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
                        if y == int(3 + h * 0.45) - 1 else SM)
        if broken:   # the snapped pyramidion lies in the sand beside it
            put(ox + 2, 1, oz + 1, SM)
            put(ox + 3, 1, oz + 1, "orange_terracotta")
            put(ox + 4, 1, oz + 1, "gold_block")
        else:
            put(ox, top, oz, "gold_block")
            put(ox, top + 1, oz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    obelisk(-5, 10, 11)
    obelisk(5, 10, 11, broken=rng.random() < 0.5)

    def jackal(jx, jz, face):            # seated Anubis on a plinth, facing east or west
        fx = 1 if face == "east" else -1
        for dz in (-1, 0, 1):
            put(jx, 1, jz + dz, CUT)
            put(jx - fx, 1, jz + dz, CUT)
        put(jx + fx, 1, jz, "polished_blackstone_slab[type=bottom,waterlogged=false]")   # forepaws
        put(jx - fx, 2, jz, "polished_blackstone")                                       # haunches
        put(jx, 2, jz, "polished_blackstone")
        put(jx, 3, jz, "gold_block")                                                     # collar
        put(jx - fx, 3, jz, "polished_blackstone_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]" % face)
        put(jx, 4, jz, "polished_blackstone")                                            # head
        put(jx + fx, 4, jz, "polished_blackstone_slab[type=top,waterlogged=false]")      # snout
        put(jx, 5, jz, "polished_blackstone_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")  # ears
    for jz in (13, 16):
        jackal(-7, jz, "east")
        jackal(7, jz, "west")

    # ---------------------------------------------------------------- hypostyle hall
    for dx in range(HX0, HX1 + 1):
        for dz in range(HZ0, HZ1 + 1):
            put(dx, -1, dz, S)
            d = math.hypot(dx, dz)
            edge = dx in (HX0, HX1) or dz in (HZ0, HZ1)
            if not opening(dx, 0, dz):
                put(dx, 0, dz, CH if 4.4 < d <= 5.5 else (RED if 5.5 < d <= 6.3 and (dx + dz) % 2 else SM))
            for y in range(1, WALL_H):
                if edge:
                    band = y in (1, WALL_H - 1)
                    put(dx, y, dz, CUT if band else (S if y != 4 else "orange_terracotta" if (dx + dz) % 3 == 0 else CH))
                else:
                    put(dx, y, dz, "air")
            # roof, open above the stairwell
            if d > 5.6:
                put(dx, WALL_H, dz, SM if not edge else CUT)
            if edge:
                put(dx, WALL_H, dz, "cut_red_sandstone" if dz == HZ0 or dx in (HX0, HX1) else CUT)
                put(dx, WALL_H + 1, dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    # the surface ring of the stairwell shaft: open (no wall), one step down onto the shell rim at y = -1
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            d = math.hypot(dx, dz)
            if 3.6 < d <= 4.65:   # the drum wall left by the dungeon shell above ground is removed
                if d > 4.4:
                    bp.set(x + dx, 0, z + dz, CH if (dx + dz) % 2 else CUT)
                for y in range(0 if d <= 4.4 else 1, 5):
                    bp.set(x + dx, y, z + dz, "air")
    bp.set(x, 4, z, "lantern[hanging=false,waterlogged=false]")          # on the stair's central column
    # a lip of stairs around the roof opening
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            d = math.hypot(dx, dz)
            if 5.6 < d <= 6.6 and in_hall(dx, dz):
                ax, az = abs(dx), abs(dz)
                facing = ("east" if dx < 0 else "west") if ax >= az else ("south" if dz < 0 else "north")
                put(dx, WALL_H + 1, dz, sst(facing, "bottom", "smooth_sandstone_stairs"))
    # papyrus columns: banded shafts with flared capitals; lanterns hang between them
    cols = [(cx, cz) for cx in (-6, 6) for cz in (-8, -4, 0, 3)] + [(-2, -8), (2, -8)]
    for cx, cz in cols:
        for y in range(1, WALL_H - 1):
            put(cx, y, cz, CH if y in (1, 3) else ("orange_terracotta" if y == 5 else S))
        put(cx, WALL_H - 1, cz, CUT)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if in_hall(cx + dx, cz + dz, -1):
                put(cx + dx, WALL_H - 1, cz + dz, sst({(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)],
                                                      "top", "smooth_sandstone_stairs"))
    for cx, cz in ((-3, -6), (3, -6), (-6, -2), (6, -2), (-6, 2), (6, 2)):
        put(cx, WALL_H - 1, cz, "iron_chain[axis=y,waterlogged=false]")
        put(cx, WALL_H - 2, cz, "lantern[hanging=true,waterlogged=false]")
    # braziers at the four corners of the rim
    for cx, cz in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        put(cx, 1, cz, CUT)
        put(cx, 2, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # sanctuary at the back: a gilded altar with a lapis cat idol, candles and painted panels
    put(0, 1, HZ0 + 1, RED)
    put(-1, 1, HZ0 + 1, sst("east", "bottom", "smooth_red_sandstone_stairs"))
    put(1, 1, HZ0 + 1, sst("west", "bottom", "smooth_red_sandstone_stairs"))
    put(0, 2, HZ0 + 1, "gold_block")
    put(0, 3, HZ0 + 1, "lapis_block")
    put(0, 4, HZ0 + 1, "lapis_block")
    put(0, 5, HZ0 + 1, "polished_blackstone_wall[east=none,north=none,south=none,west=none,up=true,waterlogged=false]")
    for dx in (-3, 3):
        put(dx, 1, HZ0 + 1, "orange_candle[candles=4,lit=true,waterlogged=false]")
    for dx in range(HX0 + 1, HX1):
        if abs(dx) > 1 and dx % 2 == 0:
            for y in (3, 4, 5):
                put(dx, y, HZ0 + 1, "blue_terracotta" if y == 4 else "orange_terracotta")
    # sarcophagi along the side walls
    for side in (-1, 1):
        for dz in (-7, -6, -5):
            put(8 * side, 1, dz, CRED)
            put(8 * side, 2, dz, "cut_red_sandstone_slab[type=bottom,waterlogged=false]" if dz != -7 else "gold_block")

    # ---------------------------------------------------------------- pylon gate (battered towers) and the winged sun
    for side in (-1, 1):
        for dz in range(HZ1 - 1, HZ1 + 3):
            for y in range(0, 15):
                inset = y // 4                       # the towers lean back (batter)
                x_in, x_out = 3, 12 - inset
                for ax in range(x_in, x_out + 1):
                    dx = ax * side
                    if dz == HZ1 + 2 and y > 12:
                        continue
                    outer = ax == x_out or y in (0, 14) or dz in (HZ1 - 1, HZ1 + 2)
                    if not outer:
                        put(dx, y, dz, S)
                        continue
                    if y == 14:
                        put(dx, y, dz, SM)
                    elif y == 13:
                        put(dx, y, dz, "cut_red_sandstone")
                    elif y == 12:
                        put(dx, y, dz, "lapis_block" if ax % 2 else "gold_block") if dz == HZ1 + 2 else put(dx, y, dz, CUT)
                    elif ax == x_out:
                        put(dx, y, dz, CUT)
                    elif dz == HZ1 + 2 and 3 <= y <= 10 and 5 <= ax <= 9:
                        # relief panel: a striped frame with painted figures
                        put(dx, y, dz, CH if ax in (5, 9) or y in (3, 10) else
                            ("orange_terracotta" if (y + ax) % 3 == 0 else "blue_terracotta" if (y + ax) % 5 == 0 else S))
                    else:
                        put(dx, y, dz, S)
            # cavetto cornice: upside-down stairs flaring out under the top
            put(3 * side, 15, dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
        for ax in range(3, 10):
            put(ax * side, 13, HZ1 + 3, sst("north", "top", "smooth_sandstone_stairs"))
        # flagstaffs in the pylon's niches, with long blue and gold pennants
        for ax, colour in ((6, "blue"), (11, "yellow")):
            for y in range(1, 19):
                put(ax * side, y, HZ1 + 3, "spruce_fence[east=false,north=false,south=false,west=false,waterlogged=false]")
            put(ax * side, 17, HZ1 + 4, f"{colour}_wall_banner[facing=south]")
    # doorway (5 wide, 7 tall) with posts, lintel and the winged sun disk
    for dz in range(HZ1 - 1, HZ1 + 3):
        for dx in range(-2, 3):
            for y in range(1, 8):
                put(dx, y, dz, "air")
            put(dx, 0, dz, CUT)
            put(dx, 8, dz, CUT)
            put(dx, 9, dz, SM)
        put(-3, 8, dz, CUT)
        put(3, 8, dz, CUT)
    for dx, spec in ((0, "gold_block"), (-1, "lapis_block"), (1, "lapis_block"), (-2, "light_blue_terracotta"),
                     (2, "light_blue_terracotta"), (-3, "blue_terracotta"), (3, "blue_terracotta")):
        put(dx, 8, HZ1 + 3, spec)
    put(0, 9, HZ1 + 3, "orange_terracotta")
    put(0, 7, HZ1 + 3, "gold_block")
    for dx in (-4, 4):
        put(dx, 1, HZ1 + 3, CH)
        put(dx, 2, HZ1 + 3, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    put(0, 6, HZ1 - 2, "lantern[hanging=true,waterlogged=false]")
    put(0, 7, HZ1 - 2, "iron_chain[axis=y,waterlogged=false]")
    # sand spilled over the roof's back corners
    for dx, dz, hh in ((HX0, HZ0, 2), (HX0 + 1, HZ0, 1), (HX0, HZ0 + 1, 1), (HX1, HZ0, 2), (HX1 - 1, HZ0, 1),
                       (HX1, HZ0 + 1, 1), (HX0 + 2, HZ0, 1), (HX1 - 3, HZ0 + 1, 1)):
        for y in range(WALL_H + 2, WALL_H + 2 + hh):
            put(dx, y, dz, "sand")


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
