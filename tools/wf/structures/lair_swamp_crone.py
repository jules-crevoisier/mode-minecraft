"""Lair of the Swamp Crone, in the drowned grotto under the bog.

Descent: the hermit's mud cellar (y -7) -> a gap behind a curtain of roots in its east wall -> the ritual
passage sloping down (cages with bones on one side, shelves of jars and candles on the other) -> the
brewing rooms (floor y -15: cauldrons, brewing stands, hanging herbs, a witch's nest) -> a long stair down
-> a site of grace (waystone, bench) -> mist -> the flooded grotto arena (floor y -30, radius ~16, up to 14
high): shallow pools with lily pads, mud and moss banks, mangrove roots hanging from the ceiling, froglights
and spore blossoms for light, giant mushrooms, and a giant cauldron bubbling against the far wall. Past the
arena, behind a second mist, the crone's hoard.
"""
import math
import random

from ..arch import Palette, stair
from ..parts import LOOT, MOD

FLOOR = -30                  # arena floor block (players stand on y = -29)
AX, AZ = -6, -8              # arena centre
BREW_Y = -15                 # brewing rooms floor block
STEM = "mushroom_stem[down=true,east=true,north=true,south=true,up=true,west=true]"
BROWN_CAP = "brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"


def _radius(a):
    return 15.8 + 1.2 * math.sin(3 * a + 1.1) + 0.9 * math.sin(5 * a + 0.3)


def _ceiling(r, a):
    R = _radius(a) + 4
    return FLOOR + max(5, min(14, round(14 * math.sqrt(max(0.0, 1 - (r / R) ** 2)))))


def _ball_line(bp, p0, p1, r0, r1, block):
    n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * 2.5) + 2
    for i in range(n + 1):
        t = i / n
        c = [p0[k] + (p1[k] - p0[k]) * t for k in range(3)]
        r = r0 + (r1 - r0) * t
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r + 0.3:
                        bp.set(round(c[0] + dx), round(c[1] + dy), round(c[2] + dz), block)


def build_lair(bp):
    rng = random.Random(77)
    earth = Palette({"mud": 5, "packed_mud": 2, "muddy_mangrove_roots[axis=y]": 1, "tuff": 1}, seed=41, scale=3.5)
    bank = Palette({"mud": 4, "moss_block": 3, "packed_mud": 2, "clay": 1, "muddy_mangrove_roots[axis=y]": 1},
                   seed=42, scale=2.0)
    brick = Palette({"mud_bricks": 5, "packed_mud": 1, "tuff_bricks": 1}, seed=43, scale=1.7)
    carve = set()

    # ------------------------------------------------------------------ 1. ritual passage from the cellar
    passage = []
    for i, x in enumerate(range(-11, 3)):
        fy = -7 - round(8 * max(0, i - 1) / 12)       # floor block: -7 at the cellar wall, -15 at the brewing rooms
        passage.append((x, fy))
        for z in ((11, 12) if x == -11 else (10, 11, 12)):
            top = fy + (2 if x == -11 else 4)
            for y in range(fy + 1, top + 1):
                carve.add((x, y, z))
    # alcoves: cages on the south side, shelves on the north side
    cages = [(-7, 13), (-3, 13), (1, 13)]
    for (x, z) in cages:
        fy = dict(passage)[x]
        for dx in (-1, 0, 1):
            for y in range(fy + 1, fy + 4):
                carve.add((x + dx, y, z))
                carve.add((x + dx, y, z + 1))

    # ------------------------------------------------------------------ 2. brewing rooms
    BX0, BX1, BZ0, BZ1 = 3, 13, 6, 17
    for x in range(BX0, BX1 + 1):
        for z in range(BZ0, BZ1 + 1):
            for y in range(BREW_Y + 1, BREW_Y + 6):
                carve.add((x, y, z))
    # ------------------------------------------------------------------ 3. long stair down to the grace
    SX = (15, 16, 17)
    stair_cells = []
    for z in (14, 15, 16):                      # opening from the brewing rooms' east wall
        for x in (BX1 + 1,):
            for y in range(BREW_Y + 1, BREW_Y + 4):
                carve.add((x, y, z))
    for i, z in enumerate(range(16, 0, -1)):
        fy = BREW_Y - i
        for x in SX:
            for y in range(fy + 1, fy + 5):
                carve.add((x, y, z))
        stair_cells.append((z, fy))
    GX0, GX1, GZ0, GZ1 = 13, 20, -6, 0
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            for y in range(FLOOR + 1, FLOOR + 6):
                carve.add((x, y, z))

    # ------------------------------------------------------------------ 4. the flooded grotto
    arena = {}
    for x in range(AX - 21, AX + 22):
        for z in range(AZ - 21, AZ + 22):
            r = math.hypot(x - AX, z - AZ)
            a = math.atan2(z - AZ, x - AX)
            if r <= _radius(a):
                top = _ceiling(r, a)
                arena[(x, z)] = top
                for y in range(FLOOR + 1, top + 1):
                    carve.add((x, y, z))
    gate = []
    gx, gz = GX0, (GZ0 + GZ1) / 2
    dx, dz = AX - gx, AZ - gz
    L = math.hypot(dx, dz)
    s = 0.0
    while s < L:
        px, pz = round(gx + dx / L * s), round(gz + dz / L * s)
        if (px, pz) in arena:
            break
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                for y in range(FLOOR + 1, FLOOR + 5):
                    carve.add((px + ox, y, pz + oz))
        gate.append((px, pz))
        s += 0.5
    # ------------------------------------------------------------------ 5. the hoard, past the far side
    z_edge = min(z for (x, z) in arena if x == AX)
    hoard_path = list(range(z_edge - 1, z_edge - 4, -1))
    for z in hoard_path:
        for x in (AX - 1, AX, AX + 1):
            for y in range(FLOOR + 1, FLOOR + 5):
                carve.add((x, y, z))
    HX0, HX1, HZ0, HZ1 = AX - 4, AX + 4, z_edge - 10, z_edge - 4
    for x in range(HX0, HX1 + 1):
        for z in range(HZ0, HZ1 + 1):
            for y in range(FLOOR + 1, FLOOR + 6):
                carve.add((x, y, z))

    # ------------------------------------------------------------------ shell, then carve
    for (x, y, z) in list(carve):
        for ddx in (-2, -1, 0, 1, 2):
            for ddy in (-2, -1, 0, 1, 2):
                for ddz in (-2, -1, 0, 1, 2):
                    n = (x + ddx, y + ddy, z + ddz)
                    if n not in carve and bp.get(*n) is None:
                        bp.set(*n, earth.pick(*n))
    for c in carve:
        bp.set(*c, "air")

    # ------------------------------------------------------------------ dress the ritual passage
    bp.fill(-11, -6, 11, -11, -5, 12, "mud_bricks")
    bp.set(-11, -6, 11, "air")
    bp.set(-11, -5, 11, "hanging_roots[waterlogged=false]")
    pd = dict(passage)
    for x, fy in passage:
        for z in (9, 10, 11, 12, 13):
            if (x, fy + 1, z) in carve:
                bp.set(x, fy, z, brick.pick(x, fy, z))
            else:
                for y in range(fy, fy + 6):
                    if (x, y, z) not in carve:
                        bp.set(x, y, z, brick.pick(x, y, z))
        for z in (10, 11, 12):
            if (x, fy + 5, z) not in carve:
                bp.set(x, fy + 5, z, "dark_oak_planks" if x % 4 else "stripped_dark_oak_log[axis=z]")
        if x > -11 and pd.get(x - 1, fy) > fy:        # a step down
            for z in (10, 11, 12):
                bp.set(x, fy + 1, z, stair("mud_brick_stairs", "west"))
                bp.set(x, fy, z, "mud_bricks")
    for (x, z) in cages:
        fy = pd[x]
        for dx in (-1, 0, 1):
            for y in range(fy + 1, fy + 4):
                bp.set(x + dx, y, z, "iron_bars[east=true,north=false,south=false,waterlogged=false,west=true]")
        bp.set(x, fy + 1, z + 1, "skeleton_skull[powered=false,rotation=8]" if x != -3 else "bone_block[axis=y]")
        bp.set(x - 1, fy + 1, z + 1, "cobweb")
        bp.chain(x + 1, fy + 3, z + 1, fy + 3)
        bp.set(x + 1, fy + 2, z + 1, "soul_lantern[hanging=true,waterlogged=false]")
    jars = ["potted_brown_mushroom", "potted_red_mushroom", "potted_fern", "potted_dead_bush",
            "decorated_pot[facing=south,waterlogged=false,cracked=false]", "candle[candles=3,lit=true,waterlogged=false]",
            "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", "potted_crimson_fungus"]
    for x, fy in passage[2:]:
        bp.set(x, fy + 2, 9, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x, fy + 3, 9, rng.choice(jars))
        if x % 3 == 0:
            bp.set(x, fy + 1, 9, "barrel[facing=up,open=false]")
    bp.spawner(-3, pd[-3] + 1, 10, "minecraft:bogged")
    for x in (-8, -1):
        bp.chain(x, pd[x] + 4, 11, pd[x] + 4)
        bp.lantern(x, pd[x] + 3, 11, hanging=True, soul=True)

    # ------------------------------------------------------------------ dress the brewing rooms
    for x in range(BX0 - 1, BX1 + 2):
        for z in range(BZ0 - 1, BZ1 + 2):
            for y in range(BREW_Y, BREW_Y + 7):
                if (x, y, z) not in carve:
                    bp.set(x, y, z, brick.pick(x, y, z))
    for x in range(BX0, BX1 + 1):
        for z in range(BZ0, BZ1 + 1):
            bp.set(x, BREW_Y, z, "dark_oak_planks" if (x + z // 2) % 2 else "spruce_planks")
    # the passage door
    for z in (10, 11, 12):
        for y in range(BREW_Y + 1, BREW_Y + 4):
            bp.set(BX0 - 1, y, z, "air")
    # dark oak beams and a partition making two rooms (a doorway in the middle)
    for x in range(BX0, BX1 + 1):
        bp.set(x, BREW_Y + 5, 11, "stripped_dark_oak_log[axis=x]")
    for x in (BX0, BX1):
        for z in (BZ0, BZ1):
            bp.fill(x, BREW_Y + 1, z, x, BREW_Y + 5, z, "stripped_dark_oak_log[axis=y]")
    for z in range(BZ0, BZ1 + 1):
        if z not in (11, 12):
            bp.fill(8, BREW_Y + 1, z, 8, BREW_Y + 4, z, "dark_oak_planks" if z % 3 else "stripped_dark_oak_log[axis=y]")
    # west room: the brewery
    for (x, z) in ((BX0, BZ0 + 2), (BX0, BZ0 + 4), (BX0 + 2, BZ0)):
        bp.set(x, BREW_Y + 1, z, "water_cauldron[level=3]")
        bp.set(x, BREW_Y + 0, z, "magma_block")
    for (x, z) in ((BX0, BZ0 + 3), (BX0 + 3, BZ0), (BX0, BZ1 - 1)):
        bp.set(x, BREW_Y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    for z in range(BZ0 + 6, BZ1 + 1):                # shelves of jars along the west wall
        for y in (BREW_Y + 2, BREW_Y + 4):
            bp.set(BX0, y, z, "spruce_slab[type=top,waterlogged=false]")
            bp.set(BX0, y + 1, z, rng.choice(jars))
    bp.set(5, BREW_Y + 1, 13, "dark_oak_fence")
    bp.set(5, BREW_Y + 2, 13, "dark_oak_pressure_plate[powered=false]")
    bp.set(6, BREW_Y + 1, 13, "dark_oak_fence")
    bp.set(6, BREW_Y + 2, 13, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=true]")
    bp.chest(BX0, BREW_Y + 1, BZ1 - 2, "east", LOOT + "witch_hut")
    # east room: drying herbs, a straw nest, the witch spawner
    for x in range(9, BX1):
        for z in (BZ0 + 1, BZ0 + 3, BZ1 - 1):
            if rng.random() < 0.6:
                bp.set(x, BREW_Y + 4, z, rng.choice(["hanging_roots[waterlogged=false]", "spore_blossom",
                                                      "hanging_roots[waterlogged=false]"]))
    bp.fill(10, BREW_Y + 1, BZ1 - 2, 12, BREW_Y + 1, BZ1 - 1, "hay_block[axis=y]")
    bp.set(11, BREW_Y + 2, BZ1 - 1, "purple_carpet")
    bp.spawner(11, BREW_Y + 1, 9, "minecraft:witch")
    bp.barrel(BX1, BREW_Y + 1, BZ0 + 1, "up", LOOT + "witch_hut")
    bp.set(BX1, BREW_Y + 1, BZ0 + 2, "composter[level=7]")
    for (x, z) in ((5, 8), (5, 15), (11, 8), (11, 15)):
        bp.chain(x, BREW_Y + 5, z, BREW_Y + 5)
        bp.lantern(x, BREW_Y + 4, z, hanging=True, soul=(x == 11))
    for z in (14, 15, 16):
        bp.set(BX1 + 1, BREW_Y, z, "mud_bricks")

    # ------------------------------------------------------------------ dress the stair and the site of grace
    for (z, fy) in stair_cells:
        for x in SX:
            bp.set(x, fy, z, stair("mud_brick_stairs", "north"))
            bp.set(x, fy - 1, z, "mud_bricks")
        if z % 4 == 0:
            bp.set(SX[-1] + 1, fy + 2, z, "verdant_froglight[axis=y]")
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            bp.set(x, FLOOR, z, "mud_bricks" if (x + z) % 4 else "moss_block")
    WX, WZ = 17, -3
    bp.set(WX, FLOOR + 1, WZ, MOD["waystone"])
    for (x, z) in ((WX - 2, WZ - 2), (WX + 2, WZ - 2), (WX - 2, WZ + 2), (WX + 2, WZ + 2)):
        bp.set(x, FLOOR + 1, z, "mud_brick_wall")
        bp.set(x, FLOOR + 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    for z in (WZ - 1, WZ, WZ + 1):
        bp.set(GX1, FLOOR + 1, z, stair("spruce_stairs", "east"))
    bp.set(GX1, FLOOR + 1, GZ0, "potted_red_mushroom")
    bp.set(GX1, FLOOR + 1, GZ1, "firefly_bush")
    bp.chain(WX, FLOOR + 5, WZ, FLOOR + 5)
    bp.lantern(WX, FLOOR + 4, WZ, hanging=True, soul=True)

    # ------------------------------------------------------------------ dress the grotto
    pools = []
    for (x, z), top in arena.items():
        r = math.hypot(x - AX, z - AZ)
        n = math.sin(x * 0.42 + 1.3) * math.cos(z * 0.37) + 0.55 * math.sin(x * 0.13 - z * 0.19)
        if 4.5 < r < _radius(math.atan2(z - AZ, x - AX)) - 1.5 and n > 0.55:
            bp.set(x, FLOOR, z, "water[level=0]")      # a shallow pool, knee-deep
            bp.set(x, FLOOR - 1, z, "mud")
            pools.append((x, z))
            if rng.random() < 0.18:
                bp.set(x, FLOOR + 1, z, "lily_pad")
            elif rng.random() < 0.05:
                bp.set(x, FLOOR - 1, z, rng.choice(["verdant_froglight[axis=y]", "ochre_froglight[axis=y]",
                                                     "pearlescent_froglight[axis=y]"]))
        else:
            bp.set(x, FLOOR, z, bank.pick(x, FLOOR, z))
            if r > 5 and rng.random() < 0.07:
                bp.set(x, FLOOR + 1, z, rng.choice(["brown_mushroom", "red_mushroom", "moss_carpet", "short_grass",
                                                     "firefly_bush"]))
        # the ceiling: hanging mangrove roots, spore blossoms, embedded froglights
        if top > FLOOR + 6:
            q = rng.random()
            if q < 0.035:
                bp.set(x, top + 1, z, rng.choice(["verdant_froglight[axis=y]", "ochre_froglight[axis=y]",
                                                   "pearlescent_froglight[axis=y]"]))
            elif q < 0.05:
                bp.set(x, top, z, "spore_blossom")
            elif q < 0.12:
                ln = rng.randint(1, 3)
                for k in range(ln):
                    bp.set(x, top - k, z, "mangrove_roots[waterlogged=false]")
                bp.set(x, top - ln, z, "hanging_roots[waterlogged=false]")
    # the cavern walls: a damp band of moss at the waterline, patches of glow lichen higher up
    dirs = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
    for (x, z), top in arena.items():
        for (ddx, ddz), face in dirs.items():
            n = (x + ddx, z + ddz)
            if n in arena or (x + ddx, FLOOR + 1, z + ddz) in carve:
                continue
            for y in (FLOOR + 1, FLOOR + 2):
                if rng.random() < 0.6:
                    bp.set(n[0], y, n[1], "moss_block")
            if rng.random() < 0.18:
                y = FLOOR + rng.randint(3, 6)
                if (x, y, z) in carve and bp.get(x, y, z) == "minecraft:air":
                    props = {k: "false" for k in ("down", "east", "north", "south", "up", "west")}
                    props[face] = "true"
                    bp.set(x, y, z, "glow_lichen[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) +
                           ",waterlogged=false]")
    # mangrove pillars at the edge, roots flaring at their feet and spreading over the ceiling
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.4
        R = _radius(a) - 1.5
        px, pz = round(AX + math.cos(a) * R), round(AZ + math.sin(a) * R)
        top = arena.get((px, pz), FLOOR + 6)
        bp.fill(px, FLOOR + 1, pz, px, top + 1, pz, "mangrove_log[axis=y]")
        for (ddx, ddz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(px + ddx, FLOOR + 1, pz + ddz, "muddy_mangrove_roots[axis=y]")
            bp.set(px + ddx * 2, FLOOR + 1, pz + ddz * 2, "mangrove_roots[waterlogged=false]", keep=False) \
                if rng.random() < 0.6 else None
            bp.set(px + ddx, top, pz + ddz, "mangrove_roots[waterlogged=false]")
        bp.set(px, FLOOR + 4, pz, "ochre_froglight[axis=y]" if k % 2 else "verdant_froglight[axis=y]")
        _ball_line(bp, (px, top + 1, pz), (AX + math.cos(a) * 6, arena[(AX, AZ)] + 1, AZ + math.sin(a) * 6),
                   0.6, 0.4, "mangrove_roots[waterlogged=false]")
    # giant mushrooms along the wall
    for k, (ang, hgt) in enumerate(((1.0, 6), (2.6, 5), (4.3, 7), (5.4, 5))):
        R = _radius(ang) - 2.5
        mx, mz = round(AX + math.cos(ang) * R), round(AZ + math.sin(ang) * R)
        bp.fill(mx, FLOOR, mz, mx, FLOOR + hgt, mz, STEM)
        for ddx in range(-3, 4):
            for ddz in range(-3, 4):
                d = math.hypot(ddx, ddz)
                if d <= 3.2:
                    bp.set(mx + ddx, FLOOR + hgt + 1, mz + ddz, BROWN_CAP)
                if d <= 1.5:
                    bp.set(mx + ddx, FLOOR + hgt, mz + ddz, "shroomlight" if d > 0.5 else STEM)
        bp.set(mx + 1, FLOOR + 1, mz + 1, "red_mushroom")
    # the giant cauldron, bubbling against the far wall
    ca = math.pi * 0.85
    CR = _radius(ca) - 6
    cx, cz = round(AX + math.cos(ca) * CR), round(AZ + math.sin(ca) * CR)
    pot = Palette({"polished_deepslate": 3, "deepslate_tiles": 2, "polished_blackstone": 1}, seed=44)
    for (ddx, ddz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        bp.set(cx + ddx, FLOOR + 1, cz + ddz, "polished_deepslate_wall")
    for ddx in (-1, 0, 1):
        for ddz in (-1, 0, 1):
            bp.set(cx + ddx, FLOOR + 1, cz + ddz, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for y, r in ((2, 2.6), (3, 3.5), (4, 4.0), (5, 4.1), (6, 3.7), (7, 3.3)):
        for ddx in range(-5, 6):
            for ddz in range(-5, 6):
                d = math.hypot(ddx, ddz)
                p = (cx + ddx, FLOOR + y, cz + ddz)
                if y == 2 and d <= r:
                    bp.set(*p, pot.pick(*p))
                elif r - 1.1 < d <= r:
                    bp.set(*p, pot.pick(*p))
                elif d <= r - 1.1:
                    bp.set(*p, "water[level=0]")
    bp.set(cx, FLOOR + 2, cz, "verdant_froglight[axis=y]")
    bp.set(cx + 1, FLOOR + 3, cz, "verdant_froglight[axis=y]")
    bp.set(cx, FLOOR + 8, cz + 1, "lily_pad")
    for a_ in range(0, 360, 8):
        ddx, ddz = round(math.cos(math.radians(a_)) * 3.6), round(math.sin(math.radians(a_)) * 3.6)
        f = "north" if abs(ddz) >= abs(ddx) and ddz < 0 else "south" if abs(ddz) >= abs(ddx) else \
            "west" if ddx < 0 else "east"
        opp = {"north": "south", "south": "north", "west": "east", "east": "west"}[f]
        bp.set(cx + ddx, FLOOR + 8, cz + ddz, stair("polished_deepslate_stairs", opp))
    _ball_line(bp, (cx + 2, FLOOR + 7, cz), (cx + 5, FLOOR + 12, cz + 2), 0.4, 0.4, "stripped_mangrove_log[axis=y]")
    # the ritual circle around the seal: mud bricks ringed with candles
    for x in range(AX - 4, AX + 5):
        for z in range(AZ - 4, AZ + 5):
            d = math.hypot(x - AX, z - AZ)
            if d <= 3.6:
                bp.set(x, FLOOR, z, "mud_bricks" if int(d * 1.4) % 2 else "packed_mud")
                bp.clear(x, FLOOR + 1, z, x, FLOOR + 1, z)
            elif d <= 4.6:
                bp.set(x, FLOOR, z, "chiseled_tuff_bricks" if (x + z) % 3 == 0 else "tuff_bricks")
                bp.clear(x, FLOOR + 1, z, x, FLOOR + 1, z)
    for k in range(8):
        a = 2 * math.pi * k / 8
        bp.set(round(AX + math.cos(a) * 5.4), FLOOR + 1, round(AZ + math.sin(a) * 5.4),
               "candle[candles=4,lit=true,waterlogged=false]")
    bp.boss_seal(AX, FLOOR, AZ, "brasshaven:swamp_crone", 16)

    # ------------------------------------------------------------------ dress the hoard
    for x in range(HX0, HX1 + 1):
        for z in range(HZ0, HZ1 + 1):
            bp.set(x, FLOOR, z, "mud_bricks" if (x + z) % 2 else "packed_mud")
    for z in hoard_path:
        for x in (AX - 1, AX, AX + 1):
            bp.set(x, FLOOR, z, "mud_bricks")
    bp.chest(AX, FLOOR + 1, HZ0 + 1, "south", LOOT + "witch_hut")
    bp.barrel(AX - 2, FLOOR + 1, HZ0 + 1, "up", LOOT + "witch_hut")
    bp.set(AX + 2, FLOOR + 1, HZ0 + 1, "water_cauldron[level=3]")
    bp.set(AX + 3, FLOOR + 1, HZ0 + 1, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]")
    bp.set(HX0, FLOOR + 1, HZ0 + 3, "skeleton_skull[powered=false,rotation=12]")
    bp.set(HX1, FLOOR + 1, HZ0 + 3, "pearlescent_froglight[axis=y]")
    bp.set(HX0, FLOOR + 1, HZ1, "verdant_froglight[axis=y]")
    for x in (HX0 + 1, HX1 - 1):
        bp.set(x, FLOOR + 5, HZ0 + 3, "spore_blossom")
    bp.chain(AX, FLOOR + 5, HZ0 + 3, FLOOR + 5)
    bp.lantern(AX, FLOOR + 4, HZ0 + 3, hanging=True, soul=True)

    # ------------------------------------------------------------------ mist across both arena entrances
    for (px, pz) in gate[-2:]:
        bp.mist(px - 1, FLOOR + 1, pz - 1, px + 1, FLOOR + 4, pz + 1)
    bp.mist(AX - 1, FLOOR + 1, hoard_path[0], AX + 1, FLOOR + 4, hoard_path[0])
