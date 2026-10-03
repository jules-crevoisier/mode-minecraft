"""Lair of the Root Mother, under the Hollow Giant Tree.

Descent: the secret root cellar (y -7) -> a curtain of hanging roots in its south wall -> a winding root
tunnel sloping down to the buried druid crypt (floor y -13) -> a stair down beside the crypt -> a site of
grace (waystone, bench, candles) -> mist -> the root cavern arena (floor y -27, radius ~16, up to 17 high):
great roots arch down from the ceiling as pillars around the edge, the tree's taproot hangs over a dais of
heartwood rings, shroomlights and glow berries light the soil. Past the arena, behind a second mist, the
heartwood vault holds the reward.
"""
import math
import random

from ..arch import Palette, stair
from ..parts import LOOT, MOB, MOD

FLOOR = -27                 # arena floor block (players stand on y = -26)
AX, AZ = 0, -3              # arena centre
CRYPT_Y = -13               # crypt floor block


def _radius(a):
    """Irregular cavern outline (blocks) at angle a."""
    return 15.5 + 1.3 * math.sin(3 * a + 0.5) + 0.8 * math.sin(5 * a + 1.7)


def _ceiling(r, a):
    """Top carved y of the cavern at distance r from the centre: a low dome, 17 high in the middle."""
    R = _radius(a) + 3.5
    return FLOOR + max(5, min(17, round(17 * math.sqrt(max(0.0, 1 - (r / R) ** 2)))))


def _root_line(bp, p0, p1, r0, r1, block, bend=(0, 0, 0)):
    """A tapering root from p0 to p1 along a quadratic curve bent by ``bend`` at its middle."""
    mx = (p0[0] + p1[0]) / 2 + bend[0]
    my = (p0[1] + p1[1]) / 2 + bend[1]
    mz = (p0[2] + p1[2]) / 2 + bend[2]
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), abs(p1[2] - p0[2])) * 2.5) + 2
    cells = set()
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t * t * p1[1]
        z = (1 - t) ** 2 * p0[2] + 2 * (1 - t) * t * mz + t * t * p1[2]
        r = r0 + (r1 - r0) * t
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r + 0.3:
                        c = (round(x + dx), round(y + dy), round(z + dz))
                        cells.add(c)
    for c in cells:
        bp.set(*c, block)
    return cells


def build_lair(bp, v):
    """Carve the descent, the arena and the vault under the giant tree (variant dict ``v``)."""
    rng = random.Random(v["seed"] * 7 + 3)
    LOG = f"{v['log']}[axis=y]"
    WOOD = f"{v['wood']}[axis=y]"
    STRIP = f"stripped_{v['log']}[axis=y]"
    deck = v["deck"]
    earth = Palette({"rooted_dirt": 5, "dirt": 3, "coarse_dirt": 1}, seed=v["seed"] + 1, scale=3.5)
    soil = Palette({"rooted_dirt": 4, "moss_block": 3, "podzol[snowy=false]": 2, "coarse_dirt": 2,
                    "mud": 1}, seed=v["seed"] + 2, scale=2.0)
    stone = Palette({"mossy_stone_bricks": 4, "stone_bricks": 2, "cracked_stone_bricks": 1, "tuff_bricks": 2},
                    seed=v["seed"] + 3, scale=1.6)

    carve = set()

    # ------------------------------------------------------------------ 1. the cellar's root curtain + tunnel
    # a two-high gap in the cellar's south wall, hidden behind a curtain of hanging roots
    tunnel = []
    for z in range(4, 18):
        t = (z - 4) / 13
        fy = -7 - round(6 * t)                       # floor block: -7 at the cellar, -13 at the crypt door
        cx = round(2.2 * math.sin(t * math.pi * 1.2))  # the tunnel wanders
        tunnel.append((cx, fy, z))
        w = 1 if z > 4 else 0
        for x in range(cx - w, cx + w + 1):
            top = fy + (2 if z == 4 else 4)
            for y in range(fy + 1, top + 1):
                carve.add((x, y, z))
    # a side nook with a cave spider nest
    for x in range(3, 6):
        for z in range(9, 12):
            for y in (-9, -8, -7):
                carve.add((x, y, z))

    # ------------------------------------------------------------------ 2. druid crypt
    CX0, CX1, CZ0, CZ1 = -7, 7, 18, 30
    for x in range(CX0 + 1, CX1):
        for z in range(CZ0 + 1, CZ1):
            for y in range(CRYPT_Y + 1, CRYPT_Y + 6):
                carve.add((x, y, z))
    for x in (-1, 0, 1):                              # doorway from the tunnel
        for y in range(CRYPT_Y + 1, CRYPT_Y + 4):
            carve.add((x, y, CZ0))
    # ------------------------------------------------------------------ 3. stair down to the site of grace
    stair_cells = []
    SX = (14, 15, 16)
    for i, z in enumerate(range(29, 14, -1)):
        fy = CRYPT_Y - i                              # one step down per block northward
        for x in SX:
            for y in range(fy + 1, fy + 5):
                carve.add((x, y, z))
        stair_cells.append((z, fy))
    for z in (27, 28, 29):                            # door and passage from the crypt's east wall
        for x in range(CX1, SX[0]):
            for y in range(CRYPT_Y + 1, CRYPT_Y + 4):
                carve.add((x, y, z))
    # grace landing at the foot of the stair, floor at the arena level
    GX0, GX1, GZ0, GZ1 = 14, 21, 10, 16
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            for y in range(FLOOR + 1, FLOOR + 6):
                carve.add((x, y, z))

    # ------------------------------------------------------------------ 4. arena: the root cavern
    arena = {}
    for x in range(AX - 20, AX + 21):
        for z in range(AZ - 20, AZ + 21):
            r = math.hypot(x - AX, z - AZ)
            a = math.atan2(z - AZ, x - AX)
            if r <= _radius(a):
                top = _ceiling(r, a)
                arena[(x, z)] = top
                for y in range(FLOOR + 1, top + 1):
                    carve.add((x, y, z))
    # passage from the grace landing into the cavern (towards the centre)
    gate = []
    gx, gz = (GX0 + GX1) / 2, GZ0
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
    # ------------------------------------------------------------------ 5. the heartwood vault (reward)
    z_edge = min(z for (x, z) in arena if x == AX)
    vault_path = list(range(z_edge - 1, z_edge - 4, -1))
    for z in vault_path:
        for x in (-1, 0, 1):
            for y in range(FLOOR + 1, FLOOR + 5):
                carve.add((x, y, z))
    VX0, VX1, VZ0, VZ1b = -4, 4, z_edge - 10, z_edge - 4
    for x in range(VX0, VX1 + 1):
        for z in range(VZ0, VZ1b + 1):
            for y in range(FLOOR + 1, FLOOR + 7):
                carve.add((x, y, z))

    # ------------------------------------------------------------------ shell: solid earth around every void
    for (x, y, z) in list(carve):
        for ddx in (-2, -1, 0, 1, 2):
            for ddy in (-2, -1, 0, 1, 2):
                for ddz in (-2, -1, 0, 1, 2):
                    n = (x + ddx, y + ddy, z + ddz)
                    if n not in carve and bp.get(*n) is None:
                        bp.set(*n, earth.pick(*n))
    for c in carve:
        bp.set(*c, "air")

    # ------------------------------------------------------------------ dress the tunnel
    bp.fill(-1, -6, 4, 1, -5, 4, "rooted_dirt")      # wall either side of the gap
    bp.set(0, -6, 4, "air")
    bp.set(0, -5, 4, "hanging_roots[waterlogged=false]")
    bp.set(0, -4, 4, "rooted_dirt")
    for i, (cx, fy, z) in enumerate(tunnel):
        for x in range(cx - 1, cx + 2):
            if bp.get(x, fy, z) not in (None,) and (x, fy + 1, z) in carve:
                bp.set(x, fy, z, soil.pick(x, fy, z))
        # steps where the floor drops
        if i + 1 < len(tunnel) and tunnel[i + 1][1] < fy:
            for x in range(cx - 1, cx + 2):
                if (x, fy + 1, z) in carve:
                    pass
        if z % 3 == 0:                                # roots across the ceiling
            for x in range(cx - 2, cx + 3):
                bp.set(x, fy + 5, z, WOOD)
            bp.set(cx, fy + 4, z, "hanging_roots[waterlogged=false]")
        if z in (8, 14):
            bp.chain(cx + 1, fy + 4, z, fy + 4)
            bp.lantern(cx + 1, fy + 3, z, hanging=True)
        if rng.random() < 0.4:
            bp.set(cx - 1, fy + 1, z, rng.choice(["brown_mushroom", "red_mushroom", "moss_carpet"]))
    # slope: turn each drop into a stair step
    for i in range(len(tunnel) - 1):
        cx, fy, z = tunnel[i]
        ncx, nfy, nz = tunnel[i + 1]
        if nfy < fy:
            for x in range(ncx - 1, ncx + 2):
                if (x, nfy + 1, nz) in carve and (x, fy, nz) in carve:
                    bp.set(x, fy, nz, stair("mud_brick_stairs", "north"))
    for x in range(3, 6):
        for z in range(9, 12):
            bp.set(x, -10, z, soil.pick(x, -10, z))
    bp.spawner(5, -9, 11, "minecraft:cave_spider")
    bp.set(4, -9, 9, "cobweb")
    bp.set(5, -8, 10, "cobweb")
    bp.set(3, -9, 11, "skeleton_skull[powered=false,rotation=3]")

    # ------------------------------------------------------------------ dress the druid crypt
    for x in range(CX0, CX1 + 1):
        for z in range(CZ0, CZ1 + 1):
            edge = x in (CX0, CX1) or z in (CZ0, CZ1)
            for y in range(CRYPT_Y, CRYPT_Y + 7):
                if (x, y, z) in carve:
                    continue
                if edge or y in (CRYPT_Y, CRYPT_Y + 6):
                    bp.set(x, y, z, stone.pick(x, y, z))
    for x in range(CX0 + 1, CX1):
        for z in range(CZ0 + 1, CZ1):
            bp.set(x, CRYPT_Y, z, "mossy_cobblestone" if (x * 3 + z) % 7 == 0 else
                   "polished_tuff" if (x + z) % 2 else "tuff_bricks")
    # pillars down both sides, with arches of roots between them
    for z in (21, 24, 27):
        for x in (CX0 + 2, CX1 - 2):
            bp.fill(x, CRYPT_Y + 1, z, x, CRYPT_Y + 5, z, "chiseled_tuff_bricks" if z == 24 else "tuff_brick_wall")
            bp.set(x, CRYPT_Y + 5, z, "chiseled_tuff")
    for z in (21, 24, 27):
        _root_line(bp, (CX0 + 2, CRYPT_Y + 5, z), (CX1 - 2, CRYPT_Y + 5, z), 0.6, 0.6, WOOD, bend=(0, 1, 0))
    # roots breaking in through the walls
    _root_line(bp, (CX0, CRYPT_Y + 6, 20), (CX0 + 2, CRYPT_Y + 1, 23), 1.0, 0.5, WOOD, bend=(1, 0, 0))
    _root_line(bp, (CX1, CRYPT_Y + 5, 28), (CX1 - 3, CRYPT_Y + 1, 29), 0.9, 0.4, WOOD)
    # sarcophagi of the druids, with candles
    for (x0, z0) in ((-4, 20), (2, 20), (-4, 25), (2, 25)):
        bp.fill(x0, CRYPT_Y + 1, z0, x0 + 2, CRYPT_Y + 1, z0 + 1, "mossy_stone_bricks")
        for x in range(x0, x0 + 3):
            for z in (z0, z0 + 1):
                bp.set(x, CRYPT_Y + 2, z, "stone_brick_slab[type=bottom,waterlogged=false]")
        bp.set(x0 + 1, CRYPT_Y + 2, z0, "chiseled_stone_bricks")
        bp.set(x0 + 1, CRYPT_Y + 3, z0, "candle[candles=3,lit=true,waterlogged=false]")
        bp.set(x0 + 2, CRYPT_Y + 3, z0 + 1, "moss_carpet")
    # the altar at the south end: a carved stone under a living sapling
    bp.fill(-2, CRYPT_Y + 1, CZ1 - 2, 2, CRYPT_Y + 1, CZ1 - 1, "chiseled_stone_bricks")
    bp.set(0, CRYPT_Y + 2, CZ1 - 1, "moss_block")
    bp.set(0, CRYPT_Y + 3, CZ1 - 1, "flowering_azalea")
    bp.set(-2, CRYPT_Y + 2, CZ1 - 2, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(2, CRYPT_Y + 2, CZ1 - 2, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(-1, CRYPT_Y + 2, CZ1 - 2, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    bp.barrel(1, CRYPT_Y + 2, CZ1 - 2, "up", LOOT + "giant_tree")
    bp.spawner(0, CRYPT_Y + 1, 23, MOB["ruin_walker"])
    for (x, z) in ((-5, 19), (5, 19), (-5, 29), (5, 29), (0, 22), (0, 27)):
        bp.chain(x, CRYPT_Y + 5, z, CRYPT_Y + 5)
        bp.lantern(x, CRYPT_Y + 4, z, hanging=True, soul=x == 0)
    for x in range(CX0 + 1, CX1):
        for z in range(CZ0 + 1, CZ1):
            if (x, CRYPT_Y + 5, z) in carve and rng.random() < 0.12 and bp.get(x, CRYPT_Y + 6, z) != "minecraft:air":
                bp.set(x, CRYPT_Y + 5, z, "hanging_roots[waterlogged=false]")
            elif bp.get(x, CRYPT_Y + 1, z) == "minecraft:air" and rng.random() < 0.05:
                bp.set(x, CRYPT_Y + 1, z, "moss_carpet")

    # ------------------------------------------------------------------ dress the stair and the site of grace
    for x in range(CX1, SX[-1] + 1):
        for z in (27, 28, 29):
            bp.set(x, CRYPT_Y, z, "tuff_bricks")
    bp.chain(11, CRYPT_Y + 3, 28, CRYPT_Y + 3)
    bp.lantern(11, CRYPT_Y + 2, 28, hanging=True)
    for (z, fy) in stair_cells:
        for x in SX:
            bp.set(x, fy, z, stair("mossy_stone_brick_stairs", "south"))
            bp.set(x, fy - 1, z, "stone_bricks")
        if z % 4 == 0:
            bp.set(SX[-1] + 1, fy + 1, z, "rooted_dirt")
            bp.set(SX[-1] + 1, fy + 2, z, "lantern[hanging=false,waterlogged=false]")
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            bp.set(x, FLOOR, z, "moss_block" if (x + z) % 3 else "mossy_stone_bricks")
    WX, WZ = 18, 13
    bp.set(WX, FLOOR + 1, WZ, MOD["waystone"])
    for (x, z) in ((WX - 2, WZ - 2), (WX + 2, WZ - 2), (WX - 2, WZ + 2), (WX + 2, WZ + 2)):
        bp.set(x, FLOOR + 1, z, "mossy_stone_brick_wall")
        bp.set(x, FLOOR + 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    for z in (WZ - 1, WZ, WZ + 1):                                 # a bench to rest on
        bp.set(GX1, FLOOR + 1, z, stair(f"{deck}_stairs", "east"))
    bp.set(GX1, FLOOR + 1, GZ1, "flowering_azalea")
    bp.set(GX1, FLOOR + 1, GZ0, "azalea")
    bp.chain(WX, FLOOR + 5, WZ, FLOOR + 5)
    bp.lantern(WX, FLOOR + 4, WZ, hanging=True)

    # ------------------------------------------------------------------ dress the arena
    for (x, z), top in arena.items():
        bp.set(x, FLOOR, z, soil.pick(x, FLOOR, z))
        r = math.hypot(x - AX, z - AZ)
        if r > 6 and rng.random() < 0.08:
            bp.set(x, FLOOR + 1, z, rng.choice(["moss_carpet", "moss_carpet", "brown_mushroom", "red_mushroom",
                                                 "fern", f"leaf_litter[facing=north,segment_amount=3]"]))
        if rng.random() < 0.035 and top > FLOOR + 6:
            bp.set(x, top + 1, z, "shroomlight")
        elif rng.random() < 0.06 and top > FLOOR + 5:
            bp.set(x, top, z, "hanging_roots[waterlogged=false]")
        elif rng.random() < 0.03 and top > FLOOR + 7:
            ln = rng.randint(1, 4)
            for k in range(ln):
                bp.set(x, top - k, z, "cave_vines_plant[berries=true]" if k < ln - 1 else
                       "cave_vines[age=20,berries=true]")
    # the great roots: arching from the ceiling down to the floor at the edge, framing the fight
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        R = _radius(a)
        top_r = R - 6
        p0 = (AX + math.cos(a) * top_r, _ceiling(top_r, a) + 1, AZ + math.sin(a) * top_r)
        p1 = (AX + math.cos(a + 0.12) * (R - 1.2), FLOOR, AZ + math.sin(a + 0.12) * (R - 1.2))
        cells = _root_line(bp, p0, p1, 1.7, 1.2, WOOD, bend=(math.cos(a) * 2.5, 1, math.sin(a) * 2.5))
        lit = sorted(cells, key=lambda c: -c[1])
        for c in lit[::23][:3]:
            bp.set(*c, "shroomlight")
        # a druid lantern hung from each great root
        hx, hz = round(AX + math.cos(a) * (R - 4.5)), round(AZ + math.sin(a) * (R - 4.5))
        for y in range(FLOOR + 13, FLOOR + 3, -1):
            if bp.get(hx, y, hz) not in (None, "minecraft:air", "minecraft:hanging_roots") and \
                    bp.get(hx, y - 1, hz) == "minecraft:air":
                bp.chain(hx, y - 1, hz, y - 1)
                bp.lantern(hx, y - 2, hz, hanging=True)
                break
    # root veins across the ceiling, from the taproot out to the tops of the great roots
    tap_top = arena[(AX, AZ)] + 1
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        top_r = _radius(a) - 6
        p0 = (AX + math.cos(a) * top_r, _ceiling(top_r, a) + 1, AZ + math.sin(a) * top_r)
        _root_line(bp, (AX + math.cos(a) * 2, tap_top, AZ + math.sin(a) * 2), p0, 1.1, 0.9, WOOD, bend=(0, 3, 0))
    # giant glowing mushrooms between the great roots, against the cavern wall
    for k in (1, 4, 6):
        a = 2 * math.pi * k / 8 + 0.2 + math.pi / 8
        R = _radius(a) - 1.5
        mx, mz = round(AX + math.cos(a) * R), round(AZ + math.sin(a) * R)
        hgt = 5 + k % 3
        bp.fill(mx, FLOOR + 1, mz, mx, FLOOR + hgt, mz, "mushroom_stem[down=true,east=true,north=true,south=true,up=true,west=true]")
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                d = math.hypot(dx, dz)
                if d <= 2.6:
                    bp.set(mx + dx, FLOOR + hgt + 1, mz + dz,
                           "red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
                    if d <= 1.6:
                        bp.set(mx + dx, FLOOR + hgt, mz + dz, "shroomlight" if d > 0.5 else
                               "mushroom_stem[down=true,east=true,north=true,south=true,up=true,west=true]")
                if 1.6 < d <= 2.6 and (dx + dz) % 2 == 0:
                    bp.set(mx + dx, FLOOR + hgt, mz + dz,
                           "red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                bp.set(mx + dx, FLOOR + hgt + 2, mz + dz,
                       "red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
        bp.set(mx + 1, FLOOR + 1, mz, "brown_mushroom")
        bp.set(mx, FLOOR + 1, mz - 1, "red_mushroom")
    # thinner roots dangling from the ceiling
    for k in range(14):
        a = rng.random() * 2 * math.pi
        r = rng.uniform(5, 12)
        x, z = round(AX + math.cos(a) * r), round(AZ + math.sin(a) * r)
        top = arena.get((x, z))
        if top is None:
            continue
        ln = rng.randint(2, 5)
        _root_line(bp, (x, top + 1, z), (x + rng.randint(-1, 1), top - ln, z + rng.randint(-1, 1)), 0.6, 0.3, WOOD)
        bp.set(x, top - ln - 1, z, "hanging_roots[waterlogged=false]")
    # the taproot of the tree, hanging over the dais, its tip glowing
    tap_top = arena[(AX, AZ)] + 2
    _root_line(bp, (AX, tap_top, AZ), (AX + 1, FLOOR + 10, AZ), 2.6, 1.0, LOG, bend=(1, 0, -1))
    for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        bp.set(AX + dx, FLOOR + 9, AZ + dz, "shroomlight")
    for (dx, dz) in ((-1, 0), (2, 0), (0, -1), (1, 2), (2, 1)):
        bp.set(AX + dx, FLOOR + 9, AZ + dz, "hanging_roots[waterlogged=false]")
    # heartwood dais: tree rings around the seal, a rim of mossy stone stairs
    for x in range(AX - 5, AX + 6):
        for z in range(AZ - 5, AZ + 6):
            d = math.hypot(x - AX, z - AZ)
            if d <= 4.6:
                bp.set(x, FLOOR + 1, z, STRIP if int(d) % 2 == 0 else LOG)
                bp.clear(x, FLOOR + 2, z, x, FLOOR + 3, z)
            elif d <= 5.6:
                f = "north" if abs(z - AZ) >= abs(x - AX) and z < AZ else \
                    "south" if abs(z - AZ) >= abs(x - AX) else "west" if x < AX else "east"
                opp = {"north": "south", "south": "north", "west": "east", "east": "west"}[f]
                bp.set(x, FLOOR + 1, z, stair("mossy_stone_brick_stairs", opp))
    bp.boss_seal(AX, FLOOR + 1, AZ, "wayfarers:root_mother", 16)

    # ------------------------------------------------------------------ dress the vault (reward)
    for x in range(VX0, VX1 + 1):
        for z in range(VZ0, VZ1b + 1):
            bp.set(x, FLOOR, z, STRIP if (x + z) % 2 else LOG)
    for z in vault_path:
        for x in (-1, 0, 1):
            bp.set(x, FLOOR, z, soil.pick(x, FLOOR, z))
    for (x, z) in ((VX0, VZ0), (VX1, VZ0), (VX0, VZ1b), (VX1, VZ1b)):
        bp.fill(x, FLOOR + 1, z, x, FLOOR + 6, z, LOG)
    for x in range(VX0, VX1 + 1):
        bp.set(x, FLOOR + 6, VZ0, WOOD)
        bp.set(x, FLOOR + 6, VZ1b, WOOD)
    bp.set(0, FLOOR + 1, VZ0 + 1, "moss_block")
    bp.chest(0, FLOOR + 2, VZ0 + 1, "south", LOOT + "giant_tree_top")
    bp.set(-1, FLOOR + 1, VZ0 + 1, "flowering_azalea")
    bp.set(1, FLOOR + 1, VZ0 + 1, "flowering_azalea")
    bp.barrel(VX0 + 1, FLOOR + 1, VZ0 + 2, "up", LOOT + "giant_tree")
    bp.set(VX1 - 1, FLOOR + 1, VZ0 + 2, "decorated_pot[facing=south,waterlogged=false,cracked=false]")
    for (x, z) in ((VX0 + 1, VZ1b - 1), (VX1 - 1, VZ1b - 1)):
        bp.set(x, FLOOR + 1, z, "shroomlight")
        bp.set(x, FLOOR + 2, z, "moss_carpet")
    bp.chain(0, FLOOR + 6, VZ0 + 3, FLOOR + 6)
    bp.lantern(0, FLOOR + 5, VZ0 + 3, hanging=True)

    # ------------------------------------------------------------------ mist across both arena entrances
    for (px, pz) in gate[-2:]:
        bp.mist(px - 1, FLOOR + 1, pz - 1, px + 1, FLOOR + 4, pz + 1)
    vz = vault_path[0] if vault_path else AZ - 14
    bp.mist(-1, FLOOR + 1, vz, 1, FLOOR + 4, vz)
