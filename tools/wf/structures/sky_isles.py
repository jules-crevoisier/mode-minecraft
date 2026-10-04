"""Sky Isles (Îles célestes): an archipelago of floating islands high above the oceans and plains (mega-structure).

The template is placed at a fixed height (bottom at y 168-174, island tops around y 195-230), no terrain.
Template y = 0 is the lowest point of the lowest underside.
  * the Crown Isle (A, 40 blocks): meadows, oaks and birches, a pond spilling into a waterfall, and the Sky
    Shrine: a ruined round temple of white stone with a half-fallen verdigris dome and the treasure altar,
  * the Cherry Isle (B, highest): a great cherry tree and a broken watchtower haunted by a gargoyle,
  * the Pool Isle (C, lowest): the waterfall's basin, wildflowers, a ruined arch and a stair tower climbing back
    up to the Crown Isle,
  * the Crystal Isle (D): an amethyst outcrop and aether ore,
  * the Bell Isle (E): a spruce grove and a bell pavilion,
  * four small rocks drifting around,
  * rope bridges on chains between the isles. Every isle hangs on an inverted cone of dirt and stone with ores,
    hanging roots, vines and spore blossoms.
"""
import math

from .. import arch
from ..arch import Palette, stair, slab
from ..defs import Piece, StructureDef, register
from ..parts import LOOT

W = "wayfarers:"
ROCK = Palette({"stone": 6, "andesite": 2, "tuff": 1, "granite": 1}, seed=3, scale=3.0)
WHITE = Palette({"calcite": 3, "smooth_quartz": 2, "polished_diorite": 2}, seed=8, scale=2.0)
ORES = ["coal_ore", "iron_ore", "copper_ore", "gold_ore", W + "aether_ore", W + "zinc_ore", "lapis_ore",
        "emerald_ore", "diamond_ore"]

# name: (cx, top, cz, radius, depth)
ISLES = {
    "A": (0, 40, 0, 19, 30),
    "B": (-30, 50, -18, 11, 22),
    "C": (25, 26, 17, 13, 18),
    "D": (-27, 31, 24, 8, 15),
    "E": (29, 44, -25, 9, 17),
    "r1": (8, 54, -31, 4, 8),
    "r2": (-8, 21, 33, 4, 7),
    "r3": (42, 35, -3, 3, 6),
    "r4": (-43, 41, 3, 4, 8),
}
SURFACE = {}   # (x, z) -> top block y of every isle column


def _hash(x, y, z, s=0):
    n = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (s * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


def outline(name, x, z):
    """Radius of isle `name` in the direction of (x, z): a lumpy, irregular shoreline."""
    cx, top, cz, R, depth = ISLES[name]
    a = math.atan2(z - cz, x - cx)
    s = sum(ord(c) for c in name)
    return R * (0.86 + 0.09 * math.sin(a * 3 + s) + 0.06 * math.sin(a * 7 + s * 2) + 0.04 * math.cos(a * 11 + s))


def isle(bp, name):
    cx, top, cz, R, depth = ISLES[name]
    s = sum(ord(c) for c in name)
    for x in range(cx - R - 2, cx + R + 3):
        for z in range(cz - R - 2, cz + R + 3):
            d = math.hypot(x - cx, z - cz)
            r = outline(name, x, z)
            if d > r:
                continue
            k = 1 - d / r
            ytop = top + round(1.5 * (1 - (d / r) ** 2) + (_hash(x, 0, z, s) - 0.5) * 0.8)
            spike = depth * 0.45 * k if _hash(x, 11, z, s) > 0.82 else 0
            ybot = top - 2 - round(depth * k ** 1.3 * (0.75 + 0.5 * _hash(x, 1, z, s)) + spike)
            SURFACE[(x, z)] = ytop
            for y in range(ybot, ytop + 1):
                dd = ytop - y
                if dd == 0:
                    b = "grass_block[snowy=false]"
                elif dd <= 2 + int(_hash(x, 2, z, s) * 2):
                    b = "dirt" if _hash(x, y, z, 5) > 0.2 else "coarse_dirt"
                elif y <= ybot + 1 and _hash(x, y, z, 6) < 0.5:
                    b = "rooted_dirt" if dd < 6 else ROCK.pick(x, y, z)
                else:
                    h = _hash(x, y, z, 7)
                    b = ORES[int(_hash(x, y, z, 9) * len(ORES)) % len(ORES)] if h < 0.035 else ROCK.pick(x, y, z)
                bp.set(x, y, z, b)
            # under the isle: hanging roots and spore blossoms
            h = _hash(x, 3, z, s)
            if h < 0.16:
                bp.set(x, ybot - 1, z, "hanging_roots[waterlogged=false]")
            elif h < 0.18 and depth > 8:
                bp.set(x, ybot - 1, z, "spore_blossom")


def flora(bp, name, density=0.3, flowers=("poppy", "dandelion", "azure_bluet", "oxeye_daisy", "cornflower",
                                            "allium", "lily_of_the_valley")):
    cx, top, cz, R, depth = ISLES[name]
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            y = SURFACE.get((x, z))
            if y is None or bp.get(x, y, z) != "minecraft:grass_block" or bp.get(x, y + 1, z) is not None:
                continue
            h = _hash(x, 4, z, 1)
            if h < density * 0.55:
                bp.set(x, y + 1, z, "short_grass")
            elif h < density * 0.8:
                bp.set(x, y + 1, z, flowers[int(h * 997) % len(flowers)])
            elif h < density * 0.85:
                bp.set(x, y + 1, z, "tall_grass[half=lower]")
                bp.set(x, y + 2, z, "tall_grass[half=upper]")


def top_at(x, z):
    return SURFACE.get((x, z))


# ------------------------------------------------------------------ the Sky Shrine (Crown Isle)
def shrine(bp):
    cx, cz = -4, -3
    y0 = max(top_at(cx + dx, cz + dz) or 0 for dx in range(-7, 8) for dz in range(-7, 8)) + 1
    R = 7
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x - cx, z - cz)
            if d <= R + 0.4:
                # stepped platform, filled down to the island
                for y in range(y0 - 3, y0):
                    if bp.get(x, y, z) is None or bp.get(x, y, z) in ("minecraft:air",):
                        bp.set(x, y, z, ROCK.pick(x, y, z))
                ring = "quartz_bricks" if int(d) % 2 else "calcite"
                bp.set(x, y0, z, "chiseled_quartz_block" if d < 1.5 else (WHITE.pick(x, y0, z) if d > R - 0.6 else ring))
                for y in range(y0 + 1, y0 + 12):
                    bp.set(x, y, z, "air")
            elif d <= R + 1.4:
                bp.set(x, y0 - 1, z, stair("quartz_stairs", _toward(cx - x, cz - z)))
                for y in range(y0 - 4, y0 - 1):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, ROCK.pick(x, y, z))
    # eight columns, two of them fallen, an architrave ring partly intact
    broken = {2, 5}
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = cx + round(math.cos(a) * (R - 1)), cz + round(math.sin(a) * (R - 1))
        hcol = 3 if k in broken else 6
        bp.set(x, y0 + 1, z, "chiseled_quartz_block")
        for y in range(y0 + 2, y0 + 1 + hcol):
            bp.set(x, y, z, "quartz_pillar[axis=y]")
        if k not in broken:
            bp.set(x, y0 + 7, z, "chiseled_quartz_block")
        else:
            # the fallen drum lying on the floor outside
            ox, oz = round(math.cos(a) * 3), round(math.sin(a) * 3)
            axis = "x" if abs(ox) >= abs(oz) else "z"
            for i in range(1, 4):
                px, pz = x + round(math.cos(a) * (i + 1)), z + round(math.sin(a) * (i + 1))
                ty = top_at(px, pz)
                if ty is not None:
                    bp.set(px, ty + 1, pz, f"quartz_pillar[axis={axis}]")
    for a in range(0, 360, 4):
        if 100 < a < 250:
            continue                                  # the fallen part of the ring
        x, z = cx + round(math.cos(math.radians(a)) * (R - 1)), cz + round(math.sin(math.radians(a)) * (R - 1))
        bp.set(x, y0 + 8, z, WHITE.pick(x, y0 + 8, z))
        xo, zo = cx + round(math.cos(math.radians(a)) * R), cz + round(math.sin(math.radians(a)) * R)
        if math.hypot(xo - cx, zo - cz) > R - 0.5:
            bp.set(xo, y0 + 8, zo, stair("quartz_stairs", _toward(cx - xo, cz - zo), "top"))
    # half of a verdigris dome still standing on the ring
    Rd = R - 1
    for x in range(cx - Rd - 1, cx + Rd + 2):
        for z in range(cz - Rd - 1, cz + Rd + 2):
            for y in range(y0 + 9, y0 + 9 + Rd):
                d = math.sqrt((x - cx) ** 2 + ((y - y0 - 8) * 1.2) ** 2 + (z - cz) ** 2)
                a = math.degrees(math.atan2(z - cz, x - cx)) % 360
                if Rd - 0.7 < d <= Rd + 0.3 and (a < 80 or a > 290):
                    bp.set(x, y, z, "oxidized_copper" if (x + y + z) % 5 else "oxidized_cut_copper")
    # rubble of the fallen dome on the floor
    for (dx, dz) in ((-3, 2), (-2, 3), (-4, 0), (-1, 4), (-5, 1)):
        bp.set(cx + dx, y0 + 1, cz + dz, "oxidized_cut_copper_slab[type=bottom,waterlogged=false]" if dx % 2
               else "oxidized_copper")
    # the altar and its treasure
    for dx in (-1, 0, 1):
        bp.set(cx + dx, y0 + 1, cz - 2, "quartz_bricks")
        bp.set(cx + dx, y0 + 2, cz - 2, "quartz_slab[type=bottom,waterlogged=false]")
    bp.set(cx, y0 + 2, cz - 2, W + "aether_block")
    bp.chest(cx, y0 + 1, cz - 3, "south", loot=LOOT + "sky_isles_shrine")
    for (dx, dz) in ((-2, -1), (2, -1)):
        bp.set(cx + dx, y0 + 1, cz + dz, "quartz_pillar[axis=y]")
        bp.set(cx + dx, y0 + 2, cz + dz, "lantern[hanging=false,waterlogged=false]")
    # moss and vines on the old stone
    arch.vines_on(bp, ((cx - R, y0 + 2, cz - R), (cx + R, y0 + 9, cz + R)), chance=0.08, seed=4, max_len=4)
    return y0


def _toward(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


# ------------------------------------------------------------------ trees
def cherry(bp, x, y, z, h=8, seed=0):
    for i in range(h):
        bp.set(x, y + i, z, "cherry_log[axis=y]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for i in range(1, 4):
            bp.set(x + dx * i, y + h - 3 + i // 2, z + dz * i, f"cherry_log[axis={'x' if dx else 'z'}]")
    lv = "cherry_leaves[distance=1,persistent=true,waterlogged=false]"
    for dx in range(-6, 7):
        for dz in range(-6, 7):
            for dy in range(-1, 4):
                d = (dx * dx + dz * dz) / 36 + ((dy - 1) / 2.5) ** 2
                if d <= 1 + (_hash(x + dx, dy, z + dz, seed) - 0.5) * 0.3:
                    bp.set(x + dx, y + h + dy - 1, z + dz, lv, keep=True)
    # blossoms drooping from the rim of the crown
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            col = [yy for yy in range(y + h - 3, y + h + 4) if (bp.get(x + dx, yy, z + dz) or "").endswith("leaves")]
            if not col or _hash(x + dx, 5, z + dz, seed) > 0.35 or dx * dx + dz * dz < 16:
                continue
            for i in range(1, 2 + int(_hash(x + dx, 6, z + dz, seed) * 3)):
                if bp.get(x + dx, col[0] - i, z + dz) is None:
                    bp.set(x + dx, col[0] - i, z + dz, lv)


def trees(bp):
    for (x, z, kind, h) in ((8, -8, "oak", 7), (12, 2, "birch", 8), (-12, 9, "oak", 6), (4, 12, "birch", 7),
                            (-14, -9, "oak", 8)):
        y = top_at(x, z)
        if y is None:
            continue
        if kind == "oak":
            arch.oak(bp, x, y + 1, z, h=h, seed=x * 7 + z)
        else:
            arch.birch(bp, x, y + 1, z, h=h, seed=x * 5 + z)
    bx, bz = ISLES["B"][0] + 2, ISLES["B"][2] + 1
    cherry(bp, bx, top_at(bx, bz) + 1, bz, h=9, seed=2)
    for (x, z, h) in ((27, -27, 11), (32, -22, 9), (25, -21, 8)):
        y = top_at(x, z)
        if y is not None:
            arch.spruce(bp, x, y + 1, z, h=h, seed=x + z)


# ------------------------------------------------------------------ waterfall, pool, stair tower
def waterfall(bp):
    """A pond on the Crown Isle spills over the east edge into a basin on the Pool Isle below."""
    px, pz = 8, 5
    pond = []
    for x in range(px - 3, px + 4):
        for z in range(pz - 3, pz + 4):
            if math.hypot(x - px, z - pz) <= 3.2 and top_at(x, z) is not None:
                pond.append((x, z))
    ylvl = min(top_at(x, z) for x, z in pond)
    for (x, z) in pond:
        for y in range(ylvl - 1, top_at(x, z) + 1):
            bp.set(x, y, z, "water[level=0]")
        bp.set(x, ylvl - 2, z, "clay" if (x + z) % 2 else "sand")
        for y in range(ylvl + 1, top_at(x, z) + 3):
            bp.set(x, y, z, "air")
    for (x, z) in pond:
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, z + dz)
            if q not in pond and top_at(*q) is not None and top_at(*q) < ylvl:
                bp.set(q[0], ylvl, q[1], "mossy_cobblestone")
    # the stream: from the pond towards the Pool Isle, until it leaves the island
    ux, uz = 0.83, 0.55
    x, z = px, pz
    t = 0
    last = None
    while True:
        t += 1
        x, z = round(px + ux * t), round(pz + uz * t)
        if top_at(x, z) is None:
            break
        for y in range(ylvl - 1, ylvl + 1):
            bp.set(x, y, z, "water[level=0]")
        bp.set(x, ylvl - 2, z, "mossy_cobblestone")
        for (dx, dz) in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            q = (x + dx, z + dz)
            if top_at(*q) is not None and abs(q[0] - px - ux * t) + abs(q[1] - pz - uz * t) > 0.9:
                if bp.get(q[0], ylvl, q[1]) != "minecraft:water":
                    bp.set(q[0], ylvl, q[1], "mossy_cobblestone" if (q[0] + q[1]) % 2 else "moss_block")
                    bp.set(q[0], ylvl - 1, q[1], "stone")
        for y in range(ylvl + 1, top_at(x, z) + 3):
            bp.set(x, y, z, "air")
        last = (x, z)
    # the falling column, and a lip so the last water cell has a floor
    fx, fz = x, z
    bp.set(fx, ylvl - 1, fz, "mossy_cobblestone")
    bp.set(fx, ylvl - 2, fz, "mossy_cobblestone")
    # the basin on the Pool Isle right under it
    cyt = top_at(fx + 1, fz + 1) or ISLES["C"][1]
    basin = []
    for x in range(fx - 3, fx + 4):
        for z in range(fz - 3, fz + 4):
            t = top_at(x, z)
            if math.hypot(x - fx, z - fz) <= 3.4 and t is not None and abs(t - ISLES["C"][1]) <= 3:
                basin.append((x, z))
    by = min(top_at(x, z) for x, z in basin) if basin else ISLES["C"][1]
    for (x, z) in basin:
        for y in range(by - 1, top_at(x, z) + 1):
            bp.set(x, y, z, "water[level=0]")
        bp.set(x, by - 2, z, "sand")
        bp.set(x, by - 3, z, "sandstone")
        for y in range(by + 1, top_at(x, z) + 3):
            bp.set(x, y, z, "air")
    for y in range(by + 1, ylvl):
        bp.set(fx, y, fz, "water[level=8]")
    for (x, z) in basin:
        if (x + z) % 5 == 0:
            bp.set(x, by + 1, z, "lily_pad")
    bp.set(fx, by + 1, fz, "water[level=8]")
    return (fx, fz, by)


def pool_isle(bp):
    """The ruined arch and the stair tower back up to the Crown Isle."""
    cx, top, cz, R, depth = ISLES["C"]
    # ruined arch
    ax, az = cx + 6, cz + 4
    y = top_at(ax, az) or top
    for side in (-2, 2):
        for k in range(1, 6 if side < 0 else 4):
            bp.set(ax + side, y + k, az, "mossy_stone_bricks" if (k + side) % 3 == 0 else "stone_bricks")
    for dx in (-2, -1, 0):
        bp.set(ax + dx, y + 6, az, "stone_bricks" if dx != -1 else "chiseled_stone_bricks")
    bp.set(ax - 1, y + 5, az, stair("stone_brick_stairs", "east", "top"))
    bp.set(ax + 1, y + 1, az + 1, "mossy_cobblestone")
    bp.set(ax + 2, y + 1, az + 2, "stone_brick_slab[type=bottom,waterlogged=false]")
    # stair tower: a round tower with a ladder up to a short bridge onto the Crown Isle
    tx, tz = cx - 12, cz - 1
    base = top_at(tx, tz) or top
    ytop = ISLES["A"][1] + 1
    for y in range(base, ytop + 1):
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                d = math.hypot(x - tx, z - tz)
                if d <= 2.4:
                    if d > 1.4:
                        bp.set(x, y, z, "mossy_stone_bricks" if _hash(x, y, z, 2) < 0.3 else "stone_bricks")
                    else:
                        bp.set(x, y, z, "air" if y > base else "stone_bricks")
    for y in range(base + 1, ytop + 1):
        bp.ladder(tx, y, tz + 1, y, "north")
    bp.set(tx + 2, base + 1, tz, "air")
    bp.set(tx + 2, base + 2, tz, "air")
    for y in (base + 6, base + 10):
        bp.set(tx - 2, y, tz, "glass_pane")
    for x in range(tx - 2, tx + 3):
        for z in range(tz - 2, tz + 3):
            if math.hypot(x - tx, z - tz) <= 2.4:
                bp.set(x, ytop, z, "stone_bricks" if (x, z) != (tx, tz + 1) else "air")
                if math.hypot(x - tx, z - tz) > 1.4 and (x + z) % 2:
                    bp.set(x, ytop + 1, z, "stone_brick_wall")
    bp.set(tx, ytop + 1, tz + 1, "air")
    bp.set(tx, ytop, tz + 1, "ladder[facing=north,waterlogged=false]")
    # a short bridge from the tower top to the nearest shore of the Crown Isle
    d = math.hypot(tx, tz)
    ux, uz = -tx / d, -tz / d
    shore = None
    for t in range(2, 20):
        x, z = round(tx + ux * t), round(tz + uz * t)
        if top_at(x, z) is not None and abs(top_at(x, z) - ytop) <= 3:
            shore = (x, top_at(x, z) + 1, z)
            break
    if shore:
        start = (round(tx + ux * 2), ytop, round(tz + uz * 2))
        rope_bridge(bp, start, shore, sag=0.6)
        for w in (-1, 0, 1):
            x, z = round(tx + ux * 2 - uz * w), round(tz + uz * 2 + ux * w)
            bp.set(x, ytop + 1, z, "air")


def crystal_isle(bp):
    cx, top, cz, R, depth = ISLES["D"]
    for (dx, dz, h) in ((0, 0, 4), (2, 1, 3), (-1, 2, 2), (1, -2, 3), (-2, -1, 2)):
        x, z = cx + dx, cz + dz
        y = top_at(x, z)
        if y is None:
            continue
        for k in range(1, h + 1):
            bp.set(x, y + k, z, "amethyst_block" if k < h else "budding_amethyst")
        bp.set(x, y + h + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
    for (dx, dz) in ((3, 0), (-3, 1), (0, 3), (2, -3)):
        x, z = cx + dx, cz + dz
        y = top_at(x, z)
        if y is not None and bp.get(x, y + 1, z) is None:
            bp.set(x, y, z, "calcite")
            bp.set(x, y + 1, z, "large_amethyst_bud[facing=up,waterlogged=false]")
    y = top_at(cx - 3, cz - 2)
    if y is not None:
        bp.barrel(cx - 3, y + 1, cz - 2, "up", loot=LOOT + "sky_isles")


def bell_isle(bp):
    cx, top, cz, R, depth = ISLES["E"]
    x0, z0 = cx - 2, cz + 1
    y = max(top_at(x0 + dx, z0 + dz) or 0 for dx in range(-2, 3) for dz in range(-2, 3)) + 1
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for yy in range(y - 2, y):
                bp.set(x0 + dx, yy, z0 + dz, "spruce_planks" if yy == y - 1 else "cobblestone")
            for yy in range(y, y + 6):
                bp.set(x0 + dx, yy, z0 + dz, "air")
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        for yy in range(y, y + 4):
            bp.set(x0 + dx, yy, z0 + dz, "stripped_spruce_log[axis=y]")
    bp.pyramid_roof(x0 - 2, z0 - 2, x0 + 2, z0 + 2, y + 4, "spruce_stairs", overhang=1)
    bp.set(x0, y + 3, z0, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.set(x0, y + 4, z0, "spruce_planks")
    bp.barrel(x0 + 1, y, z0 + 1, "up", loot=LOOT + "sky_isles")


def watchtower(bp):
    cx, top, cz, R, depth = ISLES["B"]
    tx, tz = cx - 4, cz - 3
    y0 = top_at(tx, tz) or top
    for y in range(y0 - 2, y0 + 12):
        for x in range(tx - 3, tx + 4):
            for z in range(tz - 3, tz + 4):
                d = math.hypot(x - tx, z - tz)
                if d <= 3.4:
                    broken = y > y0 + 6 + round(4 * math.sin(math.atan2(z - tz, x - tx) + 1)) and d > 2.4
                    if d > 2.4 and not broken:
                        bp.set(x, y, z, "mossy_stone_bricks" if _hash(x, y, z, 4) < 0.35 else
                               ("cracked_stone_bricks" if _hash(x, y, z, 5) < 0.2 else "stone_bricks"))
                    elif d <= 2.4:
                        bp.set(x, y, z, "stone_bricks" if y < y0 + 1 else ("air" if y > y0 else "stone_bricks"))
    for y in (y0 + 1, y0 + 2):
        bp.set(tx + 3, y, tz, "air")
    bp.set(tx, y0 + 6, tz, "stone_bricks")
    for x in range(tx - 2, tx + 3):
        for z in range(tz - 2, tz + 3):
            if math.hypot(x - tx, z - tz) <= 2.4:
                bp.set(x, y0 + 6, z, "spruce_planks" if (x + z) % 3 else "air")
    bp.set(tx - 2, y0 + 1, tz, "ladder[facing=east,waterlogged=false]")
    for y in range(y0 + 1, y0 + 7):
        bp.set(tx - 2, y, tz, "ladder[facing=east,waterlogged=false]")
    bp.set(tx - 3, y0 + 6, tz, "stone_bricks")
    bp.spawner(tx, y0 + 1, tz, "wayfarers:gargoyle")
    bp.chest(tx + 1, y0 + 7, tz + 1, "west", loot=LOOT + "sky_isles")
    arch.vines_on(bp, ((tx - 4, y0, tz - 4), (tx + 4, y0 + 12, tz + 4)), chance=0.1, seed=7, max_len=5)


# ------------------------------------------------------------------ rope bridges
def rope_bridge(bp, p0, p1, sag=2.0):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    length = math.hypot(x1 - x0, z1 - z0)
    n = int(length * 1.5) + 1
    ux, uz = (x1 - x0) / length, (z1 - z0) / length
    px, pz = -uz, ux
    for i in range(n + 1):
        t = i / n
        yf = y0 + (y1 - y0) * t - sag * 4 * t * (1 - t)
        yb = math.floor(yf)
        kind = "top" if yf - yb >= 0.5 else "bottom"
        bx, bz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
        for w in (-1, 0, 1):
            x, z = round(bx + px * w), round(bz + pz * w)
            if bp.get(x, yb, z) is None:
                bp.set(x, yb, z, slab("spruce_slab", kind))
        for w in (-2, 2):
            x, z = round(bx + px * w), round(bz + pz * w)
            if bp.get(x, yb + 1, z) is None and bp.get(x, yb, z) is None:
                bp.set(x, yb, z, slab("spruce_slab", kind))
                bp.set(x, yb + 1, z, "spruce_fence")
    for (x, y, z) in (p0, p1):
        for w in (-2, 2):
            xx, zz = round(x + px * w), round(z + pz * w)
            for yy in range(y + 1, y + 4):
                bp.set(xx, yy, zz, "stripped_spruce_log[axis=y]")
            bp.set(xx, y + 4, zz, "lantern[hanging=false,waterlogged=false]")


def edge_point(name, toward):
    """The last surface cell of isle `name` on the way to the centre of isle `toward`."""
    cx, top, cz, R, depth = ISLES[name]
    tx, tz = ISLES[toward][0], ISLES[toward][2]
    d = math.hypot(tx - cx, tz - cz)
    ux, uz = (tx - cx) / d, (tz - cz) / d
    last = (cx, top, cz)
    for t in range(0, R + 3):
        x, z = round(cx + ux * t), round(cz + uz * t)
        if top_at(x, z) is None:
            break
        last = (x, top_at(x, z), z)
    return last


def bridges(bp):
    for a, b in (("A", "B"), ("A", "E"), ("A", "D")):
        p0 = edge_point(a, b)
        p1 = edge_point(b, a)
        rope_bridge(bp, (p0[0], p0[1] + 1, p0[2]), (p1[0], p1[1] + 1, p1[2]))


def sky_isles(bp):
    SURFACE.clear()
    for name in ISLES:
        isle(bp, name)
    for name in ("A", "B", "C", "E"):
        flora(bp, name)
    waterfall(bp)
    shrine(bp)
    trees(bp)
    pool_isle(bp)
    crystal_isle(bp)
    bell_isle(bp)
    watchtower(bp)
    bridges(bp)
    flora(bp, "C", density=0.5, flowers=("poppy", "cornflower", "allium", "pink_tulip", "orange_tulip", "oxeye_daisy"))
    for name in ISLES:
        cx, top, cz, R, depth = ISLES[name]
        arch.vines_on(bp, ((cx - R - 2, top - depth, cz - R - 2), (cx + R + 2, top, cz + R + 2)), chance=0.025,
                      seed=len(name) + cx, max_len=6)


register(StructureDef(
    "sky_isles", "overworld",
    # low biomes only (a meadow can sit at y 160+ on a mountain flank, under the isles' undersides)
    ["ocean", "deep_ocean", "lukewarm_ocean", "deep_lukewarm_ocean", "warm_ocean", "plains", "sunflower_plains"],
    [Piece("isles", sky_isles)],
    # absolute height, never projected on the terrain: the lowest underside lands at y 168-174
    spacing=64, separation=24, adaptation="none", height=("uniform", 169, 175), processors="none",
    max_distance=100, foundation=False,
    title_fr="Îles célestes", title_en="Sky Isles"))
