"""Nether structures. The Nether has a roof, so placement uses absolute heights (lava sea at y=31).

Every builder works around blueprint y=0 = main floor; foundations dip below it into the lava, and
each StructureDef's start height is chosen so that floor lands at a sensible absolute altitude
(the template's lowest block is placed at the start height).
"""
import math
import random

from .. import arch
from ..arch import FACE_VEC, OPPOSITE, Palette, _pos, fill_pal, slab, stair
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD
from .lair_ash_lord import ash_lord_lair
from .lair_piglin_king import piglin_king_lair

NETHER = ["#minecraft:is_nether"]

# ------------------------------------------------------------------ materials
EB = "wayfarers:ember_bricks"
EBS = "wayfarers:ember_brick_stairs"
EBSL = "wayfarers:ember_brick_slab"
EBW = "wayfarers:ember_brick_wall"
LAMP = "wayfarers:ember_lamp"
GILD = "wayfarers:gilded_trim"
PBB = "polished_blackstone_bricks"
CPBB = "cracked_polished_blackstone_bricks"
PBBS = "polished_blackstone_brick_stairs"
PBBSL = "polished_blackstone_brick_slab"
PBBW = "polished_blackstone_brick_wall"
PB = "polished_blackstone"
PBS = "polished_blackstone_stairs"
PBSL = "polished_blackstone_slab"
PBW = "polished_blackstone_wall"
CHIS = "chiseled_polished_blackstone"
BS = "blackstone_stairs"
PBAS = "polished_basalt[axis=y]"
GBS = "gilded_blackstone"

EMBER = Palette({EB: 6, PBB: 3, CPBB: 1}, seed=11, scale=2.5)
BLACK = Palette({PBB: 5, CPBB: 1, "blackstone": 2, PB: 1}, seed=12, scale=2.5)
BASALT = Palette({PBAS: 3, "smooth_basalt": 1}, seed=13, scale=2.0)
ROCK = Palette({"basalt[axis=y]": 4, "blackstone": 4, "magma_block": 1, "smooth_basalt": 1}, seed=14, scale=3.5)
FLOOR = Palette({PB: 4, PBB: 3, GBS: 0.15}, seed=15, scale=1.5)


# ------------------------------------------------------------------ geometry helpers
def ring_cells(cx, cz, R, inner=0.6):
    """Cells of the outermost ring of a disk of radius R (gap-free: disk(R) = disk(R-1) + ring(R))."""
    out = []
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x - cx, z - cz)
            if R - inner < d <= R + 0.4:
                out.append((x, z))
    return out


def toward(cx, cz, x, z):
    """Horizontal direction from (x, z) toward the centre."""
    dx, dz = cx - x, cz - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


_NOISE = {}


def noise2(x, z, scale=6.0, seed=0):
    """Smooth 2D value noise in 0..1."""
    if (scale, seed) not in _NOISE:
        _NOISE[(scale, seed)] = Palette({"stone": 1}, seed=seed, scale=scale)
    return _NOISE[(scale, seed)]._noise(x, 0, z)


def rock_island(bp, rx, rz, edge_r, *, depth=14, slope=1.3, spread=12, seed=0, pillars=24, pal=None,
                cx=0, cz=0, top_y=-1):
    """Rugged rock base around a rounded-rectangle core (half sizes rx, rz): flat top at y=-1 inside,
    slopes down and tapers outside, with basalt columns jutting from the flanks."""
    pal = pal or ROCK
    rng = random.Random(seed)
    tops = {}
    for x in range(cx - rx - spread, cx + rx + spread + 1):
        for z in range(cz - rz - spread, cz + rz + spread + 1):
            ex = max(0, abs(x - cx) - (rx - edge_r))
            ez = max(0, abs(z - cz) - (rz - edge_r))
            d = math.hypot(ex, ez) - edge_r  # <= 0 inside the core
            n = noise2(x, z, 5.0, seed)
            if d <= 0:
                top, bottom = top_y, -depth
            else:
                top = top_y - int(d * slope + n * 3.5)
                bottom = -depth + int(d * 0.7)
                if top < bottom or d > spread:
                    continue
            for y in range(bottom, top + 1):
                bp.set(x, y, z, pal.pick(x, y, z), keep=True)
            tops[(x, z)] = top
    flank = [p for p, t in tops.items() if t < -2]
    rng.shuffle(flank)
    for (x, z) in flank[:pillars]:
        h = rng.randint(2, 8)
        for y in range(tops[(x, z)] + 1, tops[(x, z)] + 1 + h):
            bp.set(x, y, z, "basalt[axis=y]" if rng.random() < 0.7 else PBAS, keep=True)
        if rng.random() < 0.3:
            bp.set(x, tops[(x, z)] + 1 + h, z, "magma_block", keep=True)
    return tops


def lavafall(bp, x, z, y_top, y_pool):
    """Source at y_top (keep its sides enclosed), falling lava down to a source at y_pool."""
    bp.set(x, y_top, z, "lava[level=0]")
    for y in range(y_pool + 1, y_top):
        bp.set(x, y, z, "lava[level=8]")
    bp.set(x, y_pool, z, "lava[level=0]")


def pinnacle(bp, x, y, z, h=3, tip="lightning_rod[facing=up,powered=false,waterlogged=false]"):
    bp.set(x, y, z, CHIS)
    for k in range(1, h):
        bp.set(x, y + k, z, PBBW)
    bp.set(x, y + h, z, tip)


def brazier(bp, x, y, z, soul=False, big=False):
    """Standing brazier whose base sits at y."""
    fire = "soul_campfire" if soul else "campfire"
    fire += "[facing=north,lit=true,signal_fire=false,waterlogged=false]"
    if big:
        bp.set(x, y, z, CHIS)
        bp.set(x, y + 1, z, PBBW)
        bp.set(x, y + 2, z, GBS)
        for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
            bp.set(x + dx, y + 2, z + dz, stair(PBBS, d, "top"))
            bp.set(x + dx, y + 3, z + dz, fire)
        bp.set(x, y + 3, z, "magma_block")
        bp.set(x, y + 4, z, fire)
        return
    bp.set(x, y, z, PBBW)
    bp.set(x, y + 1, z, GBS)
    bp.set(x, y + 2, z, fire)


def chandelier(bp, x, y, z, soul=False, drop=2):
    """Black iron chandelier hanging from the ceiling block above y."""
    bp.chain(x, y - drop + 1, z, y)
    c = y - drop
    bp.set(x, c, z, GILD)
    bp.set(x, c - 1, z, LAMP)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + dx, c, z + dz, PBBW)
        bp.set(x + 2 * dx, c, z + 2 * dz, PBBW)
        bp.lantern(x + 2 * dx, c - 1, z + 2 * dz, hanging=True, soul=soul)
        bp.set(x + 2 * dx, c + 1, z + 2 * dz, "candle[candles=3,lit=true,waterlogged=false]")


def spike(bp, cx, cz, y, r, block="blackstone", stairs=BS, steep=3, round_=True, band=GILD,
          tip=True, lamps=True, lamp=LAMP):
    """Sharp cone/pyramid roof: each ring is `steep` tall, gilded band on the first ring."""
    yy, rr, i = y, r, 0
    while rr >= 1:
        for k in range(steep):
            for x in range(cx - rr - 1, cx + rr + 2):
                for z in range(cz - rr - 1, cz + rr + 2):
                    d = math.hypot(x - cx, z - cz) if round_ else max(abs(x - cx), abs(z - cz))
                    if d > rr + 0.35:
                        continue
                    edge = d > rr - 0.75
                    if edge and k == steep - 1:
                        bp.set(x, yy, z, stair(stairs, toward(cx, cz, x, z)))
                    elif edge and lamps and i == 1 and k == 0 and (x == cx or z == cz):
                        bp.set(x, yy, z, lamp)
                    elif edge:
                        bp.set(x, yy, z, band if (band and i == 0 and k == 0) else block)
                    elif k == 0:
                        bp.set(x, yy, z, block)
            yy += 1
        rr -= 1
        i += 1
    bp.set(cx, yy, cz, block)
    bp.set(cx, yy + 1, cz, lamp)
    if tip:
        bp.set(cx, yy + 2, cz, PBBW)
        bp.set(cx, yy + 3, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        return yy + 3
    return yy + 1


def round_tower(bp, cx, cz, y0, h, r, wall=EMBER, *, base=-8, roof="spike", steep=3, solid=False,
                band=GILD, rib=PBAS, floor=PB, floors_every=8, slit_seed=0, roof_block="blackstone",
                roof_stairs=BS, ladder=True, crown_lamps=True, ribs=8):
    """Monumental round tower: battered base, basalt ribs, gilded bands, glowing slits, corbelled
    machicolated crown with crenels and an optional spike roof. Returns the top y."""
    top = y0 + h
    for y in range(y0 + base, top + 1):
        rr = r + 1 if y < y0 + 3 else r
        for x in range(cx - rr - 1, cx + rr + 2):
            for z in range(cz - rr - 1, cz + rr + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.4:
                    if solid or d > rr - 0.8 or y <= y0:
                        bp.set(x, y, z, wall.pick(x, y, z))
                    else:
                        bp.set(x, y, z, "air")
    for (x, z) in ring_cells(cx, cz, r + 1):
        bp.set(x, y0 + 3, z, stair(PBBS, toward(cx, cz, x, z)))
    # ribs (protruding basalt pilasters) running up into the crown corbels
    for k in range(ribs):
        a = math.radians(360 / ribs * k + 180 / ribs)
        x, z = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
        for y in range(y0 + 3, top):
            bp.set(x, y, z, rib)
        bp.set(x, y0 + 3, z, CHIS)
    # gilded bands and glowing slits
    for by in range(y0 + 8, top - 3, 8):
        for (x, z) in ring_cells(cx, cz, r):
            bp.set(x, by, z, band)
    rng = random.Random(slit_seed)
    for i, sy in enumerate(range(y0 + 4, top - 4, 8)):
        off = rng.uniform(0, 90)
        for q in range(4):
            a = math.radians(off + 90 * q + i * 25)
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            for dy in range(3):
                bp.set(x, sy + dy, z, LAMP if solid else "orange_stained_glass_pane")
            if not solid:
                ix, iz = cx + round(math.cos(a) * (r - 1)), cz + round(math.sin(a) * (r - 1))
                bp.set(ix, sy, iz, "air")
    if not solid:
        bp.disk(cx, y0, cz, r - 1, floor)
        for fy in range(y0 + floors_every, top - 1, floors_every):
            bp.disk(cx, fy, cz, r - 1, floor)
            bp.lantern(cx, fy - 1, cz, hanging=True)
        if ladder:
            bp.ladder(cx, y0 + 1, cz - r + 1, top + 1, "south")
    # crown: two corbel courses, platform, parapet with merlons
    for (x, z) in ring_cells(cx, cz, r + 1):
        bp.set(x, top - 1, z, stair(PBBS, toward(cx, cz, x, z), "top"))
        bp.set(x, top, z, BLACK.pick(x, top, z))
    for (x, z) in ring_cells(cx, cz, r + 2):
        bp.set(x, top, z, stair(PBBS, toward(cx, cz, x, z), "top"))
    bp.disk(cx, top + 1, cz, r + 2, PBB)
    if not solid:
        bp.disk(cx, top + 1, cz, r - 1, floor)
        if ladder:
            bp.set(cx, top + 1, cz - r + 1, "ladder[facing=south,waterlogged=false]")
    cells = sorted(ring_cells(cx, cz, r + 2), key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    for i, (x, z) in enumerate(cells):
        bp.set(x, top + 2, z, EMBER.pick(x, top + 2, z))
        if i % 3 != 2:
            bp.set(x, top + 3, z, PBB)
            bp.set(x, top + 4, z, slab(PBBSL))
        elif crown_lamps and i % 6 == 2:
            bp.set(x, top + 2, z, LAMP)
    if roof == "spike":
        bp.disk(cx, top + 2, cz, r, roof_block)
        return spike(bp, cx, cz, top + 3, r, roof_block, roof_stairs, steep=steep)
    return top + 4


def sq_tower(bp, x0, z0, x1, z1, y0, h, wall=EMBER, *, base=-8, roof="spike", steep=3, solid=False,
             band=GILD, quoin=BASALT, floor=PB, floors_every=8, roof_block="blackstone", roof_stairs=BS,
             slits=True):
    """Square tower with 2x2 corner piers, gilded bands, glowing slits, corbelled crown, spike roof."""
    top = y0 + h
    for y in range(y0 + base, top + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                if solid or edge or y <= y0:
                    bp.set(x, y, z, wall.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
    # battered plinth
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                for y in range(y0 + base, y0 + 2):
                    bp.set(x, y, z, BLACK.pick(x, y, z))
                f = "south" if z == z0 - 1 else "north" if z == z1 + 1 else "east" if x == x0 - 1 else "west"
                bp.set(x, y0 + 2, z, stair(PBBS, f))
    # corner piers
    for (cx, sx) in ((x0, -1), (x1, 1)):
        for (cz, sz) in ((z0, -1), (z1, 1)):
            for y in range(y0 + base, top - 1):
                for (px, pz) in ((cx, cz), (cx + sx, cz), (cx, cz + sz), (cx + sx, cz + sz)):
                    bp.set(px, y, pz, quoin.pick(px, y, pz))
    # bands + slits
    for by in range(y0 + 8, top - 3, 8):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, by, z, band)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                bp.set(x, by, z, band)
    mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
    if slits:
        for sy in range(y0 + 4, top - 4, 8):
            for (x, z) in ((mx, z0), (mx, z1), (x0, mz), (x1, mz)):
                for dy in range(3):
                    bp.set(x, sy + dy, z, LAMP if solid else "orange_stained_glass_pane")
    if not solid:
        for fy in range(y0 + floors_every, top - 1, floors_every):
            bp.fill(x0 + 1, fy, z0 + 1, x1 - 1, fy, z1 - 1, floor)
            bp.lantern(mx, fy - 1, mz, hanging=True)
        bp.ladder(x0 + 1, y0 + 1, z0 + 1, top + 1, "south")
    # crown
    for k, (o, half) in enumerate(((1, "top"), (2, "top"))):
        yy = top - 2 + k
        for x in range(x0 - o, x1 + o + 1):
            for z in range(z0 - o, z1 + o + 1):
                if x in (x0 - o, x1 + o) or z in (z0 - o, z1 + o):
                    f = "south" if z == z0 - o else "north" if z == z1 + o else "east" if x == x0 - o else "west"
                    bp.set(x, yy, z, stair(PBBS, f, half))
        for x in range(x0 - o + 1, x1 + o):
            for z in range(z0 - o + 1, z1 + o):
                if x in (x0 - o + 1, x1 + o - 1) or z in (z0 - o + 1, z1 + o - 1):
                    bp.set(x, yy, z, BLACK.pick(x, yy, z))
    bp.fill(x0 - 2, top + 1, z0 - 2, x1 + 2, top + 1, z1 + 2, PBB)
    for x in range(x0 - 2, x1 + 3):
        for z in range(z0 - 2, z1 + 3):
            if x in (x0 - 2, x1 + 2) or z in (z0 - 2, z1 + 2):
                bp.set(x, top + 2, z, EMBER.pick(x, top + 2, z))
                corner = x in (x0 - 2, x1 + 2) and z in (z0 - 2, z1 + 2)
                if corner:
                    pinnacle(bp, x, top + 3, z, 3)
                elif (x + z) % 3 != 0:
                    bp.set(x, top + 3, z, PBB)
                    bp.set(x, top + 4, z, slab(PBBSL))
                elif (x + z) % 6 == 0:
                    bp.set(x, top + 2, z, LAMP)
    if roof == "spike":
        r = (x1 - x0) // 2
        bp.fill(x0, top + 2, z0, x1, top + 2, z1, roof_block)
        return spike(bp, mx, mz, top + 3, r, roof_block, roof_stairs, steep=steep, round_=False)
    return top + 4


def curtain(bp, face, line, u0, u1, h, *, thick=3, wall=EMBER, base=-8, bay=7, falls=(), skip=None):
    """Curtain wall whose outer face is the plane `line`, facing `face`; thickness extends inward.
    Battered plinth, basalt buttresses, gilded string course, glowing slits, corbelled parapet with
    merlons, wall-walk. `falls` = u positions of lavafalls pouring out of the wall into the moat."""
    inward = OPPOSITE[face]
    for u in range(u0, u1 + 1):
        if skip and skip(u):
            continue
        for t in range(thick):
            x, z = _pos(face, line, u, -t)
            for y in range(base, h + 1):
                bp.set(x, y, z, wall.pick(x, y, z))
        x, z = _pos(face, line, u, 1)
        for y in range(base, 3):
            bp.set(x, y, z, BLACK.pick(x, y, z))
        bp.set(x, 3, z, stair(PBBS, inward))
        bp.set(x, h - 1, z, stair(PBBS, inward, "top"))
        bp.set(x, h, z, BLACK.pick(x, h, z))
        bp.set(x, h + 1, z, EMBER.pick(x, h + 1, z))
        if (u - u0) % 3 != 2:
            bp.set(x, h + 2, z, PBB)
            bp.set(x, h + 3, z, slab(PBBSL))
        elif (u - u0) % 6 == 2:
            bp.set(x, h + 1, z, LAMP)
        fx, fz = _pos(face, line, u, 0)
        bp.set(fx, h - 4, fz, GILD)
                # wall-walk + inner rail
        ix, iz = _pos(face, line, u, -(thick - 1) - 1)
        bp.set(ix, h + 1, iz, PBBW)
        for t in range(thick):
            wx, wz = _pos(face, line, u, -t)
            bp.set(wx, h, wz, PB)
    # buttresses + slits
    for u in range(u0 + 3, u1 - 2, bay):
        if skip and skip(u):
            continue
        for y in range(base, h - 1):
            x, z = _pos(face, line, u, 1)
            bp.set(x, y, z, BASALT.pick(x, y, z))
        for y in range(base, 8):
            x, z = _pos(face, line, u, 2)
            bp.set(x, y, z, BASALT.pick(x, y, z))
        x, z = _pos(face, line, u, 2)
        bp.set(x, 8, z, stair(PBBS, inward))
        x, z = _pos(face, line, u, 1)
        bp.set(x, h - 7, z, LAMP)
        # slit in the middle of the next bay
        su = u + bay // 2 + 1
        if su < u1 - 1 and not (skip and skip(su)):
            sx, sz = _pos(face, line, su, 0)
            for y in range(h - 11, h - 8):
                bp.set(sx, y, sz, LAMP)
    for u in falls:
        fx, fz = _pos(face, line, u, 0)
        lavafall(bp, fx, fz, h - 3, -1)
        ox, oz = _pos(face, line, u, 1)
        for y in range(0, 4):
            bp.set(ox, y, oz, "air")
        bp.set(ox, -1, oz, "lava[level=0]")
        # gargoyle spout above the fall
        bp.set(ox, h - 3, oz, stair(PBBS, inward, "top"))
        bp.set(ox, h - 2, oz, GBS)


# ============================================================ Basalt fortress
# Black citadel on a rock island: lava moat, curtain walls with lavafalls, four great corner towers
# (the north-west one taller), mid-wall towers, a twin-towered gatehouse with portcullis and
# drawbridge, courtyard with lava basins, barracks and blaze forge, and a three-storey keep with
# corner turrets and a central spire tower. Floor (y=0) sits ~y38-40 absolute.
F_WALL = 28      # outer face of the curtain walls
F_H = 20         # curtain wall height (wall-walk level)
MOAT = (30, 35)  # lava moat ring (Chebyshev distance)


def _fortress_ground(bp):
    for x in range(-MOAT[1] - 2, MOAT[1] + 3):
        for z in range(-MOAT[1] - 2, MOAT[1] + 3):
            e = max(abs(x), abs(z))
            for y in range(-12, 0):
                bp.set(x, y, z, ROCK.pick(x, y, z))
            if MOAT[0] <= e <= MOAT[1]:
                bp.set(x, -1, z, "lava[level=0]")
                for y in range(0, 4):
                    bp.set(x, y, z, "air")
            elif e < MOAT[0]:
                bp.set(x, 0, z, FLOOR.pick(x, 0, z))
            else:
                bp.set(x, 0, z, BLACK.pick(x, 0, z))
                if e == MOAT[1] + 1:
                    bp.set(x, 1, z, PBBW if (x + z) % 8 else GBS)
    rock_island(bp, MOAT[1] + 2, MOAT[1] + 2, 8, depth=14, slope=1.2, spread=12, seed=3, pillars=40)
    # braziers along the outer bank
    for k in range(-30, 31, 10):
        for (x, z) in ((k, MOAT[1] + 2), (k, -MOAT[1] - 2), (MOAT[1] + 2, k), (-MOAT[1] - 2, k)):
            if abs(k) > 4 or z <= 0:
                brazier(bp, x, 1, z)


def _keep(bp):
    x0, x1, z0, z1 = -12, 12, -20, 0
    # raised plinth
    for x in range(x0 - 2, x1 + 3):
        for z in range(z0 - 2, z1 + 3):
            bp.set(x, 0, z, BLACK.pick(x, 0, z))
            if x in (x0 - 2, x1 + 2) or z in (z0 - 2, z1 + 2):
                f = "south" if z == z0 - 2 else "north" if z == z1 + 2 else "east" if x == x0 - 2 else "west"
                bp.set(x, 1, z, stair(PBBS, OPPOSITE[f]))
            else:
                bp.set(x, 1, z, PBB)
    floors = [1, 10, 19]
    top = 28
    bp.clear(x0 + 1, 2, z0 + 1, x1 - 1, top - 1, z1 - 1)
    for face, line, u0, u1 in (("south", z1, x0, x1), ("north", z0, x0, x1), ("east", x1, z0, z1),
                               ("west", x0, z0, z1)):
        arch.facade(bp, face, line, u0, u1, 1, top, EMBER, PBAS, pilaster_every=4, window_h=5, window_y=2,
                    plinth=PBB, plinth_stairs=PBBS, cornice_stairs=PBBS, glass="orange_stained_glass_pane",
                    sill=PBBS, floors=floors, floor_band=GILD)
    for fy in floors:
        fill_pal(bp, x0 + 1, fy, z0 + 1, x1 - 1, fy, z1 - 1, FLOOR)
    bp.fill(x0 + 1, top, z0 + 1, x1 - 1, top, z1 - 1, PBB)
    # entrance
    arch.arch_door(bp, "south", z1, 0, 1, width=5, height=6, trim=CHIS, stairs=PBBS)
    bp.fill(-2, 6, z1, 2, 7, z1, "iron_bars")
    bp.fill(-2, 6, z1, 2, 6, z1, "air")
    bp.set(0, 9, z1 + 1, LAMP)
    for dx in (-4, 4):
        bp.set(dx, 6, z1 + 1, "red_wall_banner[facing=south]")
    # corner turrets
    for (tx, tz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        round_tower(bp, tx, tz, 0, 34, 3, base=-2, solid=True, steep=3, ribs=4, slit_seed=tx * 3 + tz)
    # roof + central spire tower
    arch.steep_roof(bp, x0, z0, x1, z1, top + 1, PBBS, axis="x", overhang=1, steep=1, fill=PBB, under=PBBS,
                    ridge=GILD, dormers=3, dormer_stairs=PBBS, dormer_wall=EB)
    round_tower(bp, 0, -10, top, 24, 5, base=0, steep=3, slit_seed=99)
    # lavafalls from the front turrets into basins
    for sx in (-1, 1):
        tx = sx * 12
        lavafall(bp, tx, 3, 30, 0)
        bp.set(tx, 31, 4, stair(PBBS, "north", "top"))
        bp.set(tx, 32, 4, GBS)
        for x in range(min(sx * 6, sx * 14), max(sx * 6, sx * 14) + 1):
            for z in range(3, 15):
                rim = x in (sx * 6, sx * 14) or z in (3, 14)
                if (x, z) == (tx, 3):
                    continue
                for y in range(1, 4):
                    bp.set(x, y, z, "air")
                if rim:
                    bp.set(x, 0, z, PBB)
                    bp.set(x, 1, z, PBBW if (x + z) % 4 else GILD)
                else:
                    bp.set(x, 0, z, "lava[level=0]")
                    bp.set(x, -1, z, "magma_block")
        # obelisk rising from the basin
        ox = sx * 10
        for y in range(0, 7):
            bp.set(ox, y, 9, BASALT.pick(ox, y, 9))
        bp.set(ox, 3, 9, GILD)
        bp.set(ox, 7, 9, GILD)
        bp.set(ox, 8, 9, LAMP)
        pinnacle(bp, ox, 9, 9, 2)
    # ---------------- interiors
    # great hall (y=1..9): columns, lava troughs, throne, chandeliers
    for z in (-16, -12, -8, -4):
        for x in (-6, 6):
            bp.fill(x, 2, z, x, 9, z, PBAS)
            bp.set(x, 2, z, CHIS)
            bp.set(x, 9, z, GILD)
            for d, (dx, dz) in (("west", (1, 0)), ("east", (-1, 0)), ("north", (0, 1)), ("south", (0, -1))):
                bp.set(x + dx, 9, z + dz, stair(PBBS, d, "top"))
    for x in (-9, 9):
        for z in range(-17, -2):
            bp.set(x, 1, z, "lava[level=0]")
            bp.set(x, 0, z, "magma_block")
            bp.set(x, 2, z, "iron_bars")
    for z in range(-17, -1):
        bp.set(0, 1, z, "red_nether_bricks")
        bp.set(-1, 1, z, GBS if z % 3 == 0 else PB)
        bp.set(1, 1, z, GBS if z % 3 == 0 else PB)
    bp.fill(-3, 2, -19, 3, 2, -17, GBS)
    bp.fill(-2, 3, -19, 2, 3, -18, PB)
    bp.set(0, 4, -18, stair(PBBS, "south"))
    bp.fill(0, 4, -19, 0, 7, -19, "gold_block")
    bp.set(0, 8, -19, LAMP)
    bp.set(-1, 4, -18, stair(PBBS, "east", "top"))
    bp.set(1, 4, -18, stair(PBBS, "west", "top"))
    for dx in (-3, 3):
        brazier(bp, dx, 3, -18)
        bp.set(dx, 7, -19, "red_wall_banner[facing=south]")
    for z in (-14, -7):
        chandelier(bp, 0, 9, z, drop=2)
    bp.chest(-10, 2, -1, "north", LOOT + "basalt_fortress")
    bp.spawner(0, 2, -10, MOB["basalt_guard"])
    # stairs to the upper floors
    arch.stair_run(bp, 10, 2, -2, "north", 9, 1, PBBS, fill=PBB, clear=3)
    arch.stair_run(bp, -10, 11, -17, "south", 9, 1, PBBS, fill=PBB, clear=3)
    # armory / barracks floor (y=10)
    for x in range(-8, 9, 2):
        bp.entity(x, 11, -19, {"id": "minecraft:armor_stand", "Rotation": [0.0, 0.0]})
    for x in (-7, -4, 4, 7):
        bp.bed(x, 11, -4, "north", "red")
        bp.barrel(x + 1, 11, -3, "up")
    bp.set(-3, 11, -12, "anvil[facing=east]")
    bp.set(-3, 11, -11, "grindstone[face=floor,facing=east]")
    bp.set(3, 11, -12, "smithing_table")
    bp.chest(11, 11, -19, "west", LOOT + "basalt_fortress")
    for z in (-15, -6):
        chandelier(bp, 0, 18, z, drop=2)
    # treasury / war room (y=19)
    bp.fill(-3, 20, -12, 3, 20, -8, "crimson_planks")
    bp.set(0, 21, -10, "cartography_table")
    for x, z in ((-8, -18), (8, -18), (-8, -3), (8, -3)):
        bp.set(x, 20, z, "gold_block")
        bp.set(x, 21, z, "candle[candles=4,lit=true,waterlogged=false]")
    bp.fill(-2, 20, -19, 2, 20, -19, GBS)
    bp.chest(0, 21, -19, "south", LOOT + "basalt_fortress_keep")
    bp.set(-2, 21, -19, "gold_block")
    bp.set(2, 21, -19, "gold_block")
    bp.spawner(0, 20, -15, MOB["basalt_guard"])
    for z in (-15, -6):
        chandelier(bp, 0, 27, z, drop=3, soul=True)
    # secret vault under the hall: a cracked slab in the north-west corner hides a ladder
    bp.set(-11, 1, -19, CPBB)
    bp.clear(-11, -6, -19, -11, 0, -19)
    bp.ladder(-11, -6, -18, 0, "south")
    bp.room(-11, -7, -19, -3, -2, -13, PBB, floor=PB, ceiling=PBB)
    bp.set(-11, -2, -19, "air")
    bp.chest(-7, -6, -18, "south", LOOT + "basalt_fortress_keep")
    bp.fill(-5, -6, -18, -4, -6, -18, "gold_block")
    bp.set(-9, -6, -14, "soul_lantern[hanging=false,waterlogged=false]")
    bp.spawner(-7, -6, -15, "minecraft:blaze")


def _gatehouse(bp):
    zf = 31
    # flanking towers
    for tx0 in (-15, 7):
        sq_tower(bp, tx0, 22, tx0 + 8, zf, 0, 32, base=-6, steep=3)
    # gate block, one step proud of the towers
    fill_pal(bp, -6, -6, 22, 6, 25, zf + 1, EMBER)
    for x in range(-6, 7):
        bp.set(x, 24, zf + 2, stair(PBBS, "north", "top"))
        bp.set(x, 25, zf + 2, BLACK.pick(x, 25, zf + 2))
        bp.set(x, 26, zf + 2, PBB if x % 2 else LAMP)
        bp.set(x, 27, zf + 2, slab(PBBSL) if x % 2 else "air")
        bp.set(x, 1, zf + 2, stair(PBBS, "north"))
    for x in (-6, 6):
        for y in range(0, 25):
            bp.set(x, y, zf + 2, BASALT.pick(x, y, zf + 2))
        pinnacle(bp, x, 26, zf + 2, 3)
    # pointed arch passage (7 wide, 11 tall) with stepped archivolt
    rows = [(y, 3) for y in range(1, 9)] + [(9, 2), (10, 1), (11, 0)]
    for (y, hw) in rows:
        bp.clear(-hw, y, 21, hw, y, zf + 2)
    for z in (zf + 2, 22):
        for (y, hw) in rows:
            if y >= 9:
                bp.set(-hw - 1, y, z, stair(PBBS, "east", "top"))
                bp.set(hw + 1, y, z, stair(PBBS, "west", "top"))
    for (y, hw) in rows:
        if y < 9:
            bp.set(-hw - 1, y, zf + 2, CHIS)
            bp.set(hw + 1, y, zf + 2, CHIS)
        bp.set(-hw - 2, y, zf + 2, GILD)
        bp.set(hw + 2, y, zf + 2, GILD)
    bp.set(0, 12, zf + 2, GILD)
    bp.set(-1, 12, zf + 2, GILD)
    bp.set(1, 12, zf + 2, GILD)
    bp.set(0, 13, zf + 2, LAMP)
    # portcullis (half raised) and its chains
    for (y, hw) in rows:
        if y >= 6:
            bp.fill(-hw, y, 29, hw, y, 29, "iron_bars")
    for x in (-2, 2):
        bp.chain(x, 9, 26, 10)
    bp.lantern(0, 10, 25, hanging=True)
    for z in range(21, zf + 3):
        for x in range(-3, 4):
            bp.set(x, 0, z, GBS if x == 0 else PBB)
    # crest above the gate
    bp.fill(-3, 15, zf + 2, 3, 22, zf + 2, GILD)
    bp.fill(-2, 16, zf + 2, 2, 21, zf + 2, CHIS)
    for y in (17, 19, 20):
        bp.set(0, y, zf + 2, GBS)
    for (x, y) in ((0, 16), (0, 21), (-2, 18), (0, 18), (2, 18)):
        bp.set(x, y, zf + 2, LAMP)
    for x in range(-3, 4):
        bp.set(x, 14, zf + 3, stair(PBBS, "north", "top"))
    for x in (-11, 11):
        bp.set(x, 17, zf + 1, "red_wall_banner[facing=south]")
    # drawbridge over the moat with its chains
    for z in range(zf + 3, MOAT[1] + 2):
        for x in range(-3, 4):
            bp.set(x, 0, z, "dark_oak_planks" if abs(x) < 3 else PBAS)
            bp.set(x, 1, z, "air")
        bp.set(-4, 0, z, stair(PBBS, "east", "top"))
        bp.set(4, 0, z, stair(PBBS, "west", "top"))
    for x in (-3, 3):
        bp.line((x, 1, MOAT[1] + 1), (x, 13, zf + 3), "iron_chain[axis=y,waterlogged=false]")
    brazier(bp, -5, 1, MOAT[1] + 2, big=True)
    brazier(bp, 5, 1, MOAT[1] + 2, big=True)
    # guard rooms in the gate towers
    bp.chest(14, 1, 23, "west", LOOT + "basalt_fortress")
    bp.set(8, 1, 30, "barrel[facing=up,open=false]")
    bp.set(-14, 1, 30, "barrel[facing=up,open=false]")
    for tx in (7, -7):
        bp.clear(tx, 1, 25, tx, 3, 26)


def _lean_hall(bp, x0, x1, z0, z1, door_face, kind):
    """Courtyard building (barracks / forge) with a steep blackstone roof."""
    bp.clear(x0 + 1, 1, z0 + 1, x1 - 1, 8, z1 - 1)
    face = door_face
    line = x1 if face == "east" else x0
    arch.facade(bp, face, line, z0, z1, 0, 8, EMBER, PBAS, pilaster_every=4, window_h=3, window_y=2,
                plinth=PBB, plinth_stairs=PBBS, cornice_stairs=PBBS, glass="orange_stained_glass_pane", sill=PBBS)
    for z in (z0, z1):
        fill_pal(bp, x0, 0, z, x1, 8, z, EMBER)
    fill_pal(bp, x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, FLOOR)
    arch.steep_roof(bp, x0, z0, x1, z1, 9, BS, axis="z", overhang=1, steep=2, fill=PBB, under=PBBS, ridge=GILD)
    mid = (z0 + z1) // 2
    arch.arch_door(bp, face, line, mid, 0, width=3, height=4, trim=CHIS, stairs=PBBS)
    inner_x = x1 - 1 if face == "west" else x0 + 1
    if kind == "barracks":
        for z in range(z0 + 2, z1 - 1, 3):
            if abs(z - mid) > 1:
                bp.bed(x0 + 1 if face == "east" else x1 - 2, 1, z, "east", "red")
        bp.chest(x0 + 1 if face == "east" else x1 - 1, 1, z0 + 1, "south", LOOT + "basalt_fortress")
        for z in (z0 + 4, z1 - 4):
            bp.lantern((x0 + x1) // 2, 8, z, hanging=True)
    else:
        for z in range(z0 + 2, z1 - 1, 2):
            if abs(z - mid) > 1:
                bp.set(inner_x, 1, z, "blast_furnace[facing=%s,lit=true]" % face)
        bp.set((x0 + x1) // 2, 1, z0 + 2, "anvil[facing=north]")
        bp.set((x0 + x1) // 2, 1, z1 - 2, "lava_cauldron")
        bp.spawner((x0 + x1) // 2, 1, mid - 3, "minecraft:blaze")
        # chimney
        cxh = x0 + 1 if face == "east" else x1 - 2
        fill_pal(bp, cxh, 1, z1 - 3, cxh + 1, 22, z1 - 2, EMBER)
        bp.fill(cxh, 23, z1 - 3, cxh + 1, 23, z1 - 2, GILD)
        bp.set(cxh, 23, z1 - 3, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        bp.set(cxh + 1, 23, z1 - 2, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        for z in (z0 + 4, z1 - 6):
            bp.lantern((x0 + x1) // 2, 8, z, hanging=True)


def basalt_fortress(bp):
    _fortress_ground(bp)
    # courtyard causeway from the gate to the keep
    for z in range(2, 22):
        for x in range(-3, 4):
            bp.set(x, 0, z, GBS if (x == 0 and z % 2 == 0) else PBB if abs(x) < 3 else CHIS)
    # curtain walls (south one is interrupted by the gatehouse)
    curtain(bp, "south", F_WALL, -F_WALL, F_WALL, F_H, falls=(-20, 20), skip=lambda u: abs(u) <= 15)
    curtain(bp, "north", -F_WALL, -F_WALL, F_WALL, F_H, falls=(-12, 12))
    curtain(bp, "east", F_WALL, -F_WALL, F_WALL, F_H, falls=(-14, 14))
    curtain(bp, "west", -F_WALL, -F_WALL, F_WALL, F_H, falls=(-14, 14))
    # mid-wall towers on east and west
    for sx in (-1, 1):
        round_tower(bp, sx * F_WALL, 0, 0, 26, 4, base=-8, roof="crenels", slit_seed=sx)
        brazier(bp, sx * F_WALL, 28, 0, big=True)
    # corner towers (north-west is the great donjon)
    for (sx, sz, h, st) in ((-1, -1, 48, 4), (1, -1, 40, 3), (-1, 1, 36, 3), (1, 1, 42, 3)):
        round_tower(bp, sx * F_WALL, sz * F_WALL, 0, h, 6, base=-12, steep=st, slit_seed=sx * 7 + sz)
    _gatehouse(bp)
    # stair up to the west wall-walk
    arch.stair_run(bp, -20, 1, -25, "east", 20, 1, PBBS, fill=PBB, clear=3)
    _keep(bp)
    _lean_hall(bp, -25, -17, 4, 22, "east", "barracks")
    _lean_hall(bp, 17, 25, 4, 22, "west", "forge")
    # courtyard braziers
    for z in (6, 12, 18):
        for x in (-4, 4):
            brazier(bp, x, 1, z)
    ash_lord_lair(bp)


register(StructureDef(
    "basalt_fortress", "nether", ["basalt_deltas", "nether_wastes", "soul_sand_valley"],
    [Piece("fortress", basalt_fortress)], spacing=26, separation=9, step="surface_structures",
    adaptation="beard_box", height=("uniform", 22, 24),
    spawns=[("wayfarers:basalt_guard", 10, 1, 2), ("minecraft:wither_skeleton", 6, 1, 2)],
    title_fr="Forteresse de basalte", title_en="Basalt Fortress"))




# ============================================================ Chain bridge over the lava sea
# Two colossal gate towers (twin piers joined by a pointed gate arch and a high crenellated gallery)
# stand on rock islands in the lava sea; a 60-block suspension span hangs between them on doubled
# iron-chain cables with hangers every two blocks, back-stayed to massive anchor blocks.
# Blueprint y=0 is the deck; the lava sea surface is y=-13 and the template bottom y=-24, so the
# absolute start height 20 puts the deck at y44.
CB_L = 68        # distance between the two gate towers' centres
CB_SEA = -13     # lava sea level relative to the deck


def giant_chain(bp, x, pts, link=6, mat="polished_basalt[axis=z]", trim=GILD):
    """Chain of giant interlocking links following a curve given as one (z, y) per z. Links alternate
    between the vertical plane (rails above/below the curve) and the horizontal plane (rails beside it)."""
    zs = [p[0] for p in pts]
    cy = dict(pts)
    lo, hi = min(zs), max(zs)

    def put(xx, yy, zz, spec):
        bp.set(xx, yy, zz, spec)

    s0, k = lo, 0
    while s0 < hi:
        s1 = min(hi, s0 + link - 1)
        vertical = k % 2 == 0
        for z in range(s0, s1 + 1):
            y = cy[z]
            end = z in (s0, s1)
            if vertical:
                offs = [(0, -1), (0, 0), (0, 1)] if end else [(0, -1), (0, 1)]
            else:
                offs = [(-1, 0), (0, 0), (1, 0)] if end else [(-1, 0), (1, 0)]
            for dx, dy in offs:
                put(x + dx, y + dy, z, trim if (end and dx == 0 and dy == 0) else mat)
            if z < s1:
                y2 = cy[z + 1]
                for (dx, dy) in ((0, -1), (0, 1)) if vertical else ((-1, 0), (1, 0)):
                    a_, b_ = sorted((y + dy, y2 + dy))
                    for yy in range(a_ + 1, b_):
                        put(x + dx, yy, z, mat.replace("axis=z", "axis=y"))
        s0 += link - 2
        k += 1


def _gate_tower(bp, zc, back, h=47, steep=3):
    """Twin piers at x=+-5..13 around the deck with a gate arch and high gallery. back = -1/+1:
    the side facing away from the span (approach stairs + backstay anchors)."""
    for sx in (-1, 1):
        x0, x1 = (5, 13) if sx > 0 else (-13, -5)
        sq_tower(bp, x0, zc - 4, x1, zc + 4, CB_SEA + 1, h, base=-12, solid=True, steep=steep)
        # cutwaters: pointed buttresses in the lava, up- and down-stream
        for d in (-1, 1):
            for k in range(1, 5):
                for y in range(-24, CB_SEA + 6 - k):
                    for xx in range(x0 + k - 1, x1 - k + 2):
                        bp.set(xx, y, zc + d * (4 + k), BLACK.pick(xx, y, zc + d * (4 + k)))
                for xx in range(x0 + k - 1, x1 - k + 2):
                    bp.set(xx, CB_SEA + 6 - k, zc + d * (4 + k), stair(PBBS, "north" if d > 0 else "south"))
        # lavafall from the outer face into a basin on the island
        fx = sx * 13
        lavafall(bp, fx, zc, 22, CB_SEA + 1)
        bp.set(fx + sx, 23, zc, GBS)
        bp.set(fx + sx, 22, zc, stair(PBBS, "west" if sx > 0 else "east", "top"))
        for xx in (fx + sx, fx + 2 * sx):
            for zz in (zc - 1, zc, zc + 1):
                bp.set(xx, CB_SEA + 1, zz, "lava[level=0]")
                bp.set(xx, CB_SEA + 2, zz, "air")
    # gate passage between the piers
    bp.clear(-4, 1, zc - 4, 4, 9, zc + 4)
    # pointed gate arch with gilded archivolt
    for z in range(zc - 3, zc + 4):
        fill_pal(bp, -4, 10, z, 4, 16, z, EMBER)
        for (y, hw) in ((9, 2), (10, 1)):
            for x in range(-hw, hw + 1):
                bp.set(x, y + 1, z, "air")
            bp.set(-hw - 1, y + 1, z, stair(PBBS, "east", "top"))
            bp.set(hw + 1, y + 1, z, stair(PBBS, "west", "top"))
        bp.set(0, 12, z, stair(PBBS, "north", "top") if z == zc - 3 else GILD if z in (zc - 3, zc + 3) else PBB)
    for z in (zc - 4, zc + 4):
        for x in range(-4, 5):
            bp.set(x, 16, z, stair(PBBS, "north" if z > zc else "south", "top"))
            bp.set(x, 17, z, EMBER.pick(x, 17, z))
            bp.set(x, 18, z, PBB if x % 2 else LAMP)
        for (y, hw) in ((9, 3), (10, 2), (11, 1), (12, 0)):
            bp.set(-hw - 1, y, z, GILD)
            bp.set(hw + 1, y, z, GILD)
        bp.set(0, 14, z, LAMP)
        bp.set(0, 13, z, GBS)
        bp.set(0, 15, z, GBS)
    fill_pal(bp, -4, 17, zc - 3, 4, 17, zc + 3, BLACK)
    # high gallery joining the piers (open arcade with crenels)
    fill_pal(bp, -4, 27, zc - 3, 4, 28, zc + 3, EMBER)
    for x in range(-4, 5):
        bp.set(x, 26, zc - 3, stair(PBBS, "north", "top"))
        bp.set(x, 26, zc + 3, stair(PBBS, "south", "top"))
        for z in (zc - 3, zc + 3):
            bp.set(x, 29, z, EMBER.pick(x, 29, z))
            if x % 2 == 0:
                bp.set(x, 30, z, PBB)
                bp.set(x, 31, z, slab(PBBSL))
            else:
                bp.set(x, 29, z, LAMP if x in (-1, 1) else PBB)
    for z in range(zc - 2, zc + 3):
        bp.set(-4, 29, z, PBBW)
        bp.set(4, 29, z, PBBW)
    bp.set(0, 25, zc, "iron_chain[axis=y,waterlogged=false]")
    bp.set(0, 26, zc, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(0, 24, zc, hanging=True)
    bp.chain(0, 15, zc, 16)
    chandelier(bp, 0, 16, zc, drop=3)
    # deck through the gate
    for z in range(zc - 4, zc + 5):
        for x in range(-4, 5):
            bp.set(x, 0, z, GBS if (x == 0 and z % 2 == 0) else PBB)
    # guard room inside the east pier (door from the passage)
    bp.clear(7, 1, zc - 2, 11, 5, zc + 2)
    fill_pal(bp, 7, 0, zc - 2, 11, 0, zc + 2, FLOOR)
    bp.clear(5, 1, zc, 6, 3, zc)
    bp.lantern(9, 5, zc, hanging=True)
    bp.chest(11, 1, zc + (2 if back < 0 else -2), "west", LOOT + "chain_bridge")
    bp.barrel(11, 1, zc, "west")
    bp.set(7, 1, zc - 2 * back, "barrel[facing=up,open=false]")
    bp.set(10, 1, zc - 2 * back, "anvil[facing=north]")
    # approach: stairs down to the island behind the tower, flanked by braziers
    zs = zc + back * 5
    for i in range(12):
        z = zs + back * i
        for x in range(-3, 4):
            bp.set(x, -i, z, stair(PBBS, "north" if back < 0 else "south"))
            for y in range(CB_SEA - 2, -i):
                bp.set(x, y, z, BLACK.pick(x, y, z))
        for x in (-4, 4):
            for y in range(CB_SEA - 2, -i + 1):
                bp.set(x, y, z, BLACK.pick(x, y, z))
            bp.set(x, -i + 1, z, PBBW)
            if i % 4 == 0:
                bp.set(x, -i + 1, z, LAMP)
    for x in (-5, 5):
        brazier(bp, x, 1, zs, big=True)
    # backstay anchors on the island
    za = zc + back * 15
    for sx in (-1, 1):
        ax = sx * 6
        fill_pal(bp, ax - 1, CB_SEA - 4, za - 1, ax + 1, CB_SEA + 3, za + 1, BLACK)
        bp.fill(ax - 1, CB_SEA + 3, za - 1, ax + 1, CB_SEA + 3, za + 1, GILD)
        bp.set(ax, CB_SEA + 4, za, CHIS)
        bp.set(ax, CB_SEA + 5, za, LAMP)
    return zs


def chain_bridge(bp):
    zm = CB_L // 2
    # rock islands carrying the towers
    for zc, seed in ((0, 5), (CB_L, 6)):
        rock_island(bp, 15, 13, 7, depth=24, slope=1.2, spread=3, seed=seed, pillars=14, cz=zc,
                    top_y=CB_SEA + 1)
    for zc, back, h, st in ((0, -1, 47, 3), (CB_L, 1, 53, 4)):
        _gate_tower(bp, zc, back, h, st)
    # the deck: blackstone curbs, crimson planking, ember lamps in the railing, girders below
    for z in range(5, CB_L - 4):
        for x in range(-4, 5):
            bp.set(x, 0, z, PBB if abs(x) == 4 else "dark_oak_planks" if z % 4 == 0 else "spruce_planks")
        bp.set(-5, 0, z, stair(PBBS, "east", "top"))
        bp.set(5, 0, z, stair(PBBS, "west", "top"))
        for x in (-4, 4):
            bp.set(x, 1, z, LAMP if z % 6 == 0 else PBBW)
        if z % 4 == 0:
            for x in range(-4, 5):
                bp.set(x, -1, z, stair(PBBS, "north", "top") if abs(x) < 4 else PBBW)
            bp.set(-4, -2, z, PBBW)
            bp.set(4, -2, z, PBBW)
        if z % 8 == 4:
            bp.set(0, -1, z, LAMP)
            for x in (-4, 4):
                drop = 2 + (z // 8) % 3
                bp.chain(x, -1 - drop, z, -3)
                bp.lantern(x, -2 - drop, z, hanging=True)
    # main cables: giant chains from the gallery of one tower, sagging to mid-span, up to the other
    half = (CB_L - 10) / 2
    top_y, low_y = 29, 4
    for x in (-4, 4):
        pts = []
        for z in range(5, CB_L - 4):
            t = (z - zm) / half
            pts.append((z, round(low_y + (top_y - low_y) * t * t)))
        giant_chain(bp, x, pts)
        for (z, y) in pts:
            if z % 2 == 1 and y > 5:
                for yy in range(2, y - 1):
                    bp.set(x, yy, z, "iron_chain[axis=y,waterlogged=false]")
            if z % 6 == 3 and 8 < y:
                bp.lantern(x, y - 2, z, hanging=True)
        # backstays: giant chains from the galleries down to the anchors on the islands
        for zc, back in ((0, -1), (CB_L, 1)):
            za = zc + back * 15
            z_from = zc + back * 5
            bpts = []
            for z in range(min(z_from, za), max(z_from, za) + 1):
                t = abs(z - z_from) / abs(za - z_from)
                bpts.append((z, round(29 + (CB_SEA + 6 - 29) * t)))
            giant_chain(bp, x + (2 if x > 0 else -2), bpts, link=5)
        # saddles where the cables cross the towers
        for zc in (0, CB_L):
            for z in range(zc - 4, zc + 5):
                bp.set(x, 29, z, GILD)
                bp.set(x, 30, z, PBAS.replace("axis=y", "axis=z"))
    # mid-span: a gibbet cage hangs under the deck with a forgotten chest
    for y in (-1, -2, -3):
        bp.set(0, y, zm, "iron_chain[axis=y,waterlogged=false]")
    bp.fill(-1, -7, zm - 1, 1, -4, zm + 1, "iron_bars")
    bp.fill(-1, -8, zm - 1, 1, -8, zm + 1, PBB)
    bp.fill(-1, -4, zm - 1, 1, -4, zm + 1, PBB)
    bp.clear(0, -7, zm, 0, -5, zm)
    bp.chest(0, -7, zm, "north", LOOT + "chain_bridge")
    bp.set(0, -9, zm, LAMP)
    # mid-span lookout with braziers
    for sx in (-1, 1):
        bp.set(sx * 6, 0, zm, stair(PBBS, "west" if sx > 0 else "east", "top"))
        brazier(bp, sx * 5, 1, zm, big=False)


register(StructureDef(
    "chain_bridge", "nether", ["nether_wastes", "basalt_deltas", "crimson_forest", "soul_sand_valley"],
    [Piece("bridge", chain_bridge)], spacing=22, separation=7, adaptation="none",
    height=("absolute", 20), processors="none",
    title_fr="Pont de chaînes suspendu", title_en="Chain Bridge"))


# ============================================================ Piglin sanctuary (crimson forest)
# A four-tier golden ziggurat of blackstone: gilded cornices, gold-capped corner piers with braziers,
# lava cascading from tier to tier, a grand staircase to the summit where a 22-block golden piglin
# idol raises its sword. Inside: a pillared treasure sanctum; under the summit, a hidden vault.
# Giant crimson fungi with weeping vines frame the temple.
ZIG = [(22, 0, 6), (17, 6, 6), (12, 12, 6), (8, 18, 4)]   # (half size, base y, height)
GOLD = Palette({"gold_block": 3, "raw_gold_block": 2}, seed=21, scale=2.0)
TEMPLE = Palette({PBB: 4, "blackstone": 2, CPBB: 1, GBS: 1}, seed=22, scale=2.5)
NETHER_GROUND = Palette({"netherrack": 5, "blackstone": 2, "nether_wart_block": 0.5}, seed=23, scale=3.0)


def giant_fungus(bp, x, y, z, h, cap_r, seed=0, kind="crimson"):
    """Huge nether fungus: thick leaning stem with buttress roots, a domed cap with a drooping lip,
    shroomlights under the cap and vines (weeping for crimson) hanging from the rim."""
    rng = random.Random(seed)
    stem = f"{kind}_stem[axis=y]"
    hyph = f"{kind}_hyphae[axis=y]"
    wart = "nether_wart_block" if kind == "crimson" else "warped_wart_block"
    lean_a = rng.uniform(0, 2 * math.pi)
    lean = rng.uniform(1.0, 2.5)
    cx, cz = x, z
    for i in range(-3, h):
        t = max(0, i) / h
        cx = x + round(math.cos(lean_a) * lean * t * t)
        cz = z + round(math.sin(lean_a) * lean * t * t)
        r = 1.6 if i < h * 0.3 else 1.2
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if math.hypot(dx, dz) <= r:
                    bp.set(cx + dx, y + i, cz + dz, stem if abs(dx) + abs(dz) < 2 else hyph)
    for k in range(5):
        a = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
        for j in range(1, 5):
            rx, rz = x + round(math.cos(a) * (1 + j)), z + round(math.sin(a) * (1 + j))
            bp.set(rx, y + 1 - j, rz, hyph)
            bp.set(rx, y - j, rz, hyph)
    top = y + h
    H = max(3.0, cap_r * 0.5)
    for dx in range(-cap_r - 2, cap_r + 3):
        for dz in range(-cap_r - 2, cap_r + 3):
            d = math.hypot(dx, dz)
            R = cap_r + (noise2(cx + dx, cz + dz, 3.0, seed) - 0.5) * 2.4
            if d > R:
                continue
            t = H * math.sqrt(max(0.0, 1 - (d / R) ** 2))
            ytop = top + round(t)
            lip = 3 if d > R - 1.6 else 1
            for yy in range(ytop - lip, ytop + 1):
                bp.set(cx + dx, yy, cz + dz, wart)
            if lip == 1 and rng.random() < 0.08:
                bp.set(cx + dx, ytop - 1, cz + dz, "shroomlight")
            if d > R - 1.6 and rng.random() < 0.35:
                ln = rng.randint(1, 6)
                for k in range(ln):
                    yy = ytop - 4 - k
                    if kind == "crimson":
                        bp.set(cx + dx, yy, cz + dz, "weeping_vines_plant" if k < ln - 1 else "weeping_vines[age=25]",
                               keep=True)
                    elif k < 2:
                        bp.set(cx + dx, yy, cz + dz, "shroomlight" if k == 1 else wart, keep=True)
    for _ in range(cap_r):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(2, cap_r - 1.5)
        bp.set(cx + round(math.cos(a) * r), top - 1, cz + round(math.sin(a) * r), "shroomlight")


def mini_piglin(bp, x, y, z, rot):
    """Small gilded piglin statue (4 tall) on a corner pier."""
    bp.set(x, y, z, GBS)
    bp.set(x, y + 1, z, "raw_gold_block")
    bp.set(x, y + 2, z, "gold_block")
    bp.set(x, y + 3, z, f"piglin_head[rotation={rot}]")


def zig_tier(bp, half, y0, h, seed=0, niches=False, corner="brazier"):
    """One ziggurat tier: solid core, battered plinth, pilasters with gold capitals, gilded cornice,
    gold-capped corner piers carrying braziers or small piglin statues; optional lamp-lit niches."""
    fill_pal(bp, -half, y0, -half, half, y0 + h - 1, half, TEMPLE)
    top = y0 + h - 1
    for face in ("north", "south", "east", "west"):
        line = half if face in ("south", "east") else -half
        inward = OPPOSITE[face]
        for u in range(-half, half + 1):
            x, z = _pos(face, line, u, 1)
            bp.set(x, y0, z, stair(PBBS, inward))
            bp.set(x, top, z, stair(PBBS, inward, "top"))
            ex, ez = _pos(face, line, u, 0)
            bp.set(ex, top, ez, GILD)
            if u % 4 == 0 and abs(u) < half - 1:
                for y in range(y0, top):
                    bp.set(x, y, z, PBAS)
                bp.set(x, top - 1, z, "gold_block")
                bp.set(x, y0, z, CHIS)
            elif u % 4 == 2 and abs(u) < half - 1 and niches and abs(u) > 3:
                # recessed niche across the bay: ember lamp in the back, gilded jambs, lintel and sill
                for du in (-1, 0, 1):
                    fx, fz = _pos(face, line, u + du, 0)
                    bx, bz = _pos(face, line, u + du, -1)
                    for y in (y0 + 2, y0 + 3):
                        bp.set(fx, y, fz, "air")
                        bp.set(bx, y, bz, LAMP if du == 0 else GBS)
                    bp.set(fx, y0 + 4, fz, GILD)
                    bp.set(fx, y0 + 1, fz, GBS)
                    sx_, sz_ = _pos(face, line, u + du, 1)
                    bp.set(sx_, y0 + 1, sz_, stair(PBBS, inward, "top"))
                cx_, cz_ = _pos(face, line, u, 0)
                bp.set(cx_, y0 + 2, cz_, "candle[candles=3,lit=true,waterlogged=false]")
            elif u % 4 == 2 and abs(u) < half - 1 and h >= 5:
                bp.set(ex, y0 + h // 2, ez, CHIS)
                bp.set(ex, y0 + h // 2 - 1, ez, GBS)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (half + 1), sz * (half + 1)
            for y in range(y0, top + 2):
                for dx in (0, -sx):
                    for dz in (0, -sz):
                        bp.set(cx + dx, y, cz + dz, GOLD.pick(cx + dx, y, cz + dz) if y > top - 1 else PBAS)
            if corner == "statue":
                rot = {(1, 1): 14, (-1, 1): 2, (-1, -1): 6, (1, -1): 10}[(sx, sz)]
                mini_piglin(bp, cx, top + 2, cz, rot)
            else:
                brazier(bp, cx, top + 2, cz, big=True)


def _idol_gold(x, y, z, B, H=34):
    """Gold shading: raw (darker) gold dominates low on the statue, bright gold high up."""
    t = (y - B) / H
    n = noise2(x + y * 0.3, z, 4.0, 51)
    return "raw_gold_block" if n < 1.05 - 1.6 * t else "gold_block"


def _section(bp, y, cz, hx, hz, B, fn=None, n=2.6, cx=0):
    """Fill a rounded horizontal cross-section (superellipse) of the statue."""
    cells = []
    for x in range(cx - math.ceil(hx), cx + math.ceil(hx) + 1):
        for z in range(cz - math.ceil(hz), cz + math.ceil(hz) + 1):
            if (abs(x - cx) / hx) ** n + (abs(z - cz) / hz) ** n <= 1.0:
                cells.append((x, z))
    for (x, z) in cells:
        bp.set(x, y, z, fn(x, y, z) if fn else _idol_gold(x, y, z, B))
    return cells


def _limb(bp, a, b, B, r=0.9):
    """Rounded limb between two points."""
    (x0, y0, z0), (x1, y1, z1) = a, b
    n = max(1, int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 2))
    for i in range(n + 1):
        t = i / n
        px, py, pz = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
        for x in range(math.floor(px - r), math.ceil(px + r) + 1):
            for y in range(math.floor(py - r), math.ceil(py + r) + 1):
                for z in range(math.floor(pz - r), math.ceil(pz + r) + 1):
                    if (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= r * r + 0.35:
                        bp.set(x, y, z, _idol_gold(x, y, z, B))


def piglin_idol(bp, B, zc=-3):
    """Sculpted golden piglin (~34 tall incl. crown) facing south, feet at y=B: robed body narrowing
    to a gilded belt, broad shoulders with pauldrons, free-standing arms whose hands rest on the
    pommel of a great sword planted before its feet, wide head with snout, tusks and floppy ears,
    a tall spiked crown, and a red cape flowing off the shoulders."""
    # robe skirt flaring to the ground, gilded hem, boots peeking out
    for dy in range(0, 9):
        cells = _section(bp, B + dy, zc, 4.7 - 0.14 * dy, 3.3 - 0.08 * dy, B)
        if dy == 0:
            for (x, z) in cells:
                if (abs(x) / 4.7) ** 2.6 + (abs(z - zc) / 3.3) ** 2.6 > 0.55:
                    bp.set(x, B, z, GILD)
    for x in (-2, -1, 1, 2):
        bp.set(x, B, zc + 4, "blackstone")
    for x in (-3, 3):
        for dy in range(1, 8, 2):
            bp.set(x, B + dy, zc + 3, "raw_gold_block")
    # belt with an ember buckle
    _section(bp, B + 9, zc, 3.7, 2.7, B, fn=lambda *_: GILD)
    bp.set(0, B + 9, zc + 3, LAMP)
    bp.set(-1, B + 9, zc + 3, GBS)
    bp.set(1, B + 9, zc + 3, GBS)
    # torso widening from the waist to broad shoulders, with a gilded strap
    for dy in range(10, 18):
        _section(bp, B + dy, zc, 3.7 + (dy - 10) * 0.22, 2.7 + (dy - 10) * 0.06, B)
    for i in range(7):
        bp.set(-3 + i, B + 10 + i, zc + 3, GBS)
    # neck with a blackstone gorget
    _section(bp, B + 18, zc, 2.6, 2.0, B, fn=lambda *_: "blackstone")
    _section(bp, B + 19, zc, 2.3, 1.8, B)
    # pauldrons
    for sx in (-1, 1):
        for dy, (hx, hz) in ((15, (1.6, 2.2)), (16, (2.1, 2.6)), (17, (2.1, 2.6)), (18, (1.5, 2.0))):
            _section(bp, B + dy, zc, hx, hz, B, cx=sx * 6)
        for z in range(zc - 2, zc + 3):
            bp.set(sx * 6, B + 15, z, GILD)
            bp.set(sx * 5, B + 15, z, "blackstone")
    # arms: upper arms hang free of the torso, forearms reach forward to the pommel
    sz = zc + 6
    for sx in (-1, 1):
        _limb(bp, (sx * 7, B + 15, zc), (sx * 7, B + 12, zc + 1), B, r=1.0)
        bp.set(sx * 7, B + 12, zc + 1, "blackstone")
        _limb(bp, (sx * 7, B + 12, zc + 1), (sx * 2, B + 11, sz - 1), B, r=0.9)
        bp.set(sx * 2, B + 11, sz - 1, "blackstone")
        bp.fill(sx * 1, B + 10, sz, sx * 1, B + 11, sz, "raw_gold_block")
    # the great sword, point-down before the feet
    for y in range(B - 1, B + 9):
        bp.set(0, y, sz, "obsidian" if (y - B) % 3 else LAMP)
        if y > B:
            bp.set(-1, y, sz, PBAS)
            bp.set(1, y, sz, PBAS)
    bp.fill(-4, B + 9, sz, 4, B + 9, sz, GBS)
    bp.set(-4, B + 10, sz, "gold_block")
    bp.set(4, B + 10, sz, "gold_block")
    bp.set(0, B + 10, sz, GBS)
    bp.set(0, B + 11, sz, GBS)
    bp.set(0, B + 12, sz, "gold_block")
    bp.set(0, B + 13, sz, LAMP)
    # head: wider than the neck, rounded, with brow, glowing eyes, snout, nostrils, tusks
    hz0 = zc - 0.5
    for dy in range(20, 28):
        w = 5.3 if 21 <= dy <= 26 else 4.6
        _section(bp, B + dy, round(hz0), w, 3.6 if 21 <= dy <= 26 else 3.0, B, n=3.0)
    front = round(hz0) + 3
    for x in range(-2, 3):
        for dy in (20, 21, 22):
            for dz in (1, 2):
                if not (abs(x) == 2 and dz == 2):
                    bp.set(x, B + dy, front + dz, "raw_gold_block")
    for x in (-1, 1):
        bp.set(x, B + 21, front + 3, "nether_wart_block")
    bp.set(0, B + 21, front + 3, "raw_gold_block")
    for x in (-3, 3):
        bp.set(x, B + 20, front + 1, "bone_block[axis=y]")
        bp.set(x, B + 21, front + 1, "bone_block[axis=y]")
        bp.set(x, B + 22, front + 1, "bone_block[axis=y]")
    for x in (-3, -2, 2, 3):
        bp.set(x, B + 24, front, "blackstone" if abs(x) == 3 else LAMP)
    for x in (-4, -3, -2, -1, 1, 2, 3, 4):
        bp.set(x, B + 25 + (1 if abs(x) == 4 else 0), front + 1, GBS)
    # floppy ears angled out and down
    for sx in (-1, 1):
        for i, (dx, ys_) in enumerate(((6, (25, 27)), (7, (24, 26)), (8, (23, 25)), (9, (22, 23)), (10, (21, 21)))):
            for z in range(round(hz0) - 1, round(hz0) + 2 - (1 if i >= 3 else 0)):
                for dy in range(ys_[0], ys_[1] + 1):
                    bp.set(sx * dx, B + dy, z, "raw_gold_block" if i < 3 else "gold_block")
        bp.set(sx * 6, B + 27, round(hz0) + 1, "blackstone")
    # tall spiked crown of gold with gilded trim and ember jewels
    hz_c = round(hz0)
    ring = []
    for x in range(-5, 6):
        for z in range(hz_c - 4, hz_c + 5):
            inside = (abs(x) / 4.7) ** 3 + (abs(z - hz_c) / 3.1) ** 3 <= 1.0
            if inside:
                bp.set(x, B + 28, z, GBS)
                edge = any((abs(x + dx) / 4.7) ** 3 + (abs(z + dz - hz_c) / 3.1) ** 3 > 1.0
                           for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    ring.append((x, z))
    ring.sort(key=lambda p: math.atan2(p[1] - hz_c, p[0]))
    for i, (x, z) in enumerate(ring):
        bp.set(x, B + 28, z, GILD)
        bp.set(x, B + 29, z, "gold_block")
        if i % 2 == 0:
            tall = 4 if (x == 0 and z > hz_c) else 3 if abs(x) >= 4 else 2
            for k in range(tall):
                bp.set(x, B + 30 + k, z, "gold_block" if k < tall - 1 else GILD)
            bp.set(x, B + 30 + tall, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(0, B + 31, hz_c + 3, LAMP)
    for x in (-2, 2):
        bp.set(x, B + 29, hz_c + 3, LAMP)
    # red cape flowing from the shoulders: billows out behind (deeper in the middle), widens and
    # wraps forward at the sides, gilded hem, darker folds
    back = zc - 3
    for y in range(B + 1, B + 19):
        drop = B + 18 - y
        w = 5 + drop // 5
        for x in range(-w, w + 1):
            billow = 1 if abs(x) < w - 1 and drop > 3 else 0
            zz = back - 1 - drop // 7 - billow
            hem = abs(x) == w or y == B + 1
            fold = (x + drop // 3) % 4 == 0
            bp.set(x, y, zz, GILD if hem else "red_terracotta" if fold else "red_wool")
            if abs(x) == w and drop > 5:
                bp.set(x, y, zz + 1, "red_wool")
    for sx in (-1, 1):
        for z in range(back - 1, zc + 1):
            bp.set(sx * 6, B + 19, z, "red_wool")
            bp.set(sx * 5, B + 19, z, "red_wool")
        bp.set(sx * 4, B + 19, back, GBS)
    # braided mane down the back of the head
    hb = round(hz0) - 4
    for y in range(B + 20, B + 28):
        bp.set(0, y, hb, GBS if y % 2 else "blackstone")
        for sx in (-2, 2):
            if y > B + 22:
                bp.set(sx, y, hb + 1, "raw_gold_block")


def piglin_sanctuary(bp):
    # ground: netherrack apron with crimson nylium, rooted into the terrain
    rock_island(bp, 30, 30, 10, depth=8, slope=1.2, spread=6, seed=9, pillars=0, pal=NETHER_GROUND)
    for x in range(-34, 35):
        for z in range(-34, 35):
            if bp.get(x, -1, z) and not bp.get(x, 0, z):
                bp.set(x, -1, z, "crimson_nylium")
    rng = random.Random(4)
    for x in range(-33, 34):
        for z in range(-33, 34):
            if max(abs(x), abs(z)) > 25 and bp.get(x, -1, z) == "minecraft:crimson_nylium":
                r = rng.random()
                if r < 0.10:
                    bp.set(x, 0, z, "crimson_roots")
                elif r < 0.13:
                    bp.set(x, 0, z, "crimson_fungus")
                elif r < 0.15:
                    bp.set(x, 0, z, "nether_sprouts")
    # paved court around the base
    for x in range(-26, 27):
        for z in range(-26, 27):
            if max(abs(x), abs(z)) <= 26:
                bp.set(x, -1, z, GBS if (x + z) % 9 == 0 else FLOOR.pick(x, -1, z))
                for y in range(0, 3):
                    bp.set(x, y, z, "air")
    # lava channel around the base, bridged at the doors and the stairs
    for x in range(-25, 26):
        for z in range(-25, 26):
            if 24 <= max(abs(x), abs(z)) <= 25 and not (abs(x) <= 5 and z > 0) and not abs(z) <= 2:
                bp.set(x, -1, z, "lava[level=0]")
                bp.set(x, -2, z, "magma_block")
    # the tiers
    for i, (half, y0, h) in enumerate(ZIG):
        zig_tier(bp, half, y0, h, seed=i, niches=i in (1, 2), corner="statue" if i == 1 else "brazier")
    summit = ZIG[-1][1] + ZIG[-1][2]   # walking level on the summit
    # lava cascades down the east and west faces of the upper tiers into gilded basins
    for sx in (-1, 1):
        for i in (1, 2):
            half, y0, h = ZIG[i]
            lhalf = ZIG[i - 1][0]
            xf = sx * half
            src_y = y0 + h - 2
            for z in (-1, 0, 1):
                lavafall(bp, xf, z, src_y, y0 - 1)
            bp.fill(xf + sx, src_y, -1, xf + sx, src_y, 1, stair(PBBS, "west" if sx > 0 else "east", "top"))
            bp.fill(xf + sx, src_y + 1, -1, xf + sx, src_y + 1, 1, GBS)
            for x in range(min(xf + sx, sx * (lhalf - 1)), max(xf + sx, sx * (lhalf - 1)) + 1):
                for z in range(-3, 4):
                    rim = abs(z) == 3 or x == sx * (lhalf - 1)
                    bp.set(x, y0 - 1, z, GBS if rim else "lava[level=0]")
                    if rim:
                        bp.set(x, y0, z, PBBW if (x + z) % 2 else GILD)
    # grand staircase on the south face, with balustrades, gold posts and braziers
    arch.stair_run(bp, -4, 0, 29, "north", summit, 9, PBBS, clear=5)
    for i in range(summit):
        z = 29 - i
        for x in range(-4, 5):
            for y in range(-1, i):
                bp.set(x, y, z, TEMPLE.pick(x, y, z), keep=True)
            if x == 0 and i % 3 == 0:
                bp.set(x, i, z, stair("polished_blackstone_stairs", "north"))
        for x in (-5, 5):
            for y in range(-1, i + 1):
                bp.set(x, y, z, TEMPLE.pick(x, y, z))
            bp.set(x, i + 1, z, "gold_block" if i % 4 == 0 else PBBW)
            if i % 8 == 0:
                brazier(bp, x, i + 2, z)
    # summit: pedestal, idol, altar, obelisks
    ys = summit
    for (hx, z0_, z1_, ya, yb) in ((8, -8, 3, ys, ys + 1), (7, -8, 2, ys + 2, ys + 3), (6, -7, 0, ys + 4, ys + 4)):
        fill_pal(bp, -hx, ya, z0_, hx, yb, z1_, TEMPLE)
        for x in range(-hx, hx + 1):
            bp.set(x, yb, z1_, GILD)
            bp.set(x, ya, z1_ + 1, stair(PBBS, "north"))
        for z in range(z0_, z1_ + 1):
            bp.set(-hx, yb, z, GILD)
            bp.set(hx, yb, z, GILD)
    for x in (-6, 6):
        bp.set(x, ys + 3, 3, LAMP)
    piglin_idol(bp, ys + 5, zc=-3)
    bp.fill(-3, ys, 5, 3, ys, 6, GBS)
    bp.fill(-2, ys + 1, 5, 2, ys + 1, 5, "gold_block")
    bp.chest(0, ys + 1, 6, "south", LOOT + "piglin_sanctuary")
    bp.set(-2, ys + 2, 5, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(2, ys + 2, 5, "candle[candles=4,lit=true,waterlogged=false]")
    for sx in (-1, 1):
        ox = sx * 7
        for y in range(ys, ys + 9):
            bp.set(ox, y, 7, GOLD.pick(ox, y, 7) if y % 3 == 0 else PBAS)
        bp.set(ox, ys + 9, 7, LAMP)
        pinnacle(bp, ox, ys + 10, 7, 2)
    # ---------------- sanctum inside the lowest tier (doors east and west)
    bp.clear(-11, 0, -11, 11, 9, 11)
    fill_pal(bp, -11, -1, -11, 11, -1, 11, FLOOR)
    bp.fill(-11, 10, -11, 11, 10, 11, PBB)
    for x in (-7, -2, 2, 7):
        for z in (-7, -2, 2, 7):
            if abs(x) == 7 or abs(z) == 7:
                bp.fill(x, 0, z, x, 9, z, PBAS)
                bp.set(x, 9, z, "gold_block")
                bp.set(x, 0, z, CHIS)
    for sx in (-1, 1):
        bp.clear(sx * 12, 0, -1, sx * 26, 3, 1)
        for x in range(12, 24):
            bp.set(sx * x, -1, 0, GBS)
            bp.set(sx * x, -1, -1, PB)
            bp.set(sx * x, -1, 1, PB)
        for z in (-2, 2):
            bp.fill(sx * 23, 0, z, sx * 23, 4, z, "gold_block")
        bp.fill(sx * 23, 4, -1, sx * 23, 4, 1, GILD)
        bp.set(sx * 23, 4, 0, LAMP)
        bp.lantern(sx * 17, 3, 0, hanging=True)
    # gold hoard and offerings
    bp.fill(-3, 0, -3, 3, 0, 3, "gold_block")
    bp.fill(-2, 1, -2, 2, 1, 2, GBS)
    bp.fill(-1, 2, -1, 1, 2, 1, "gold_block")
    bp.set(0, 3, 0, LAMP)
    for (x, z) in ((-9, -9), (9, -9), (-9, 9), (9, 9)):
        bp.set(x, 0, z, "gold_block")
        bp.set(x, 1, z, "raw_gold_block")
        bp.set(x, 2, z, "candle[candles=4,lit=true,waterlogged=false]")
    bp.chest(-10, 0, 0, "east", LOOT + "piglin_sanctuary")
    bp.chest(10, 0, -9, "west", LOOT + "piglin_sanctuary")
    bp.spawner(0, 0, -6, "minecraft:piglin")
    for (x, z) in ((-5, 5), (5, 5), (-5, -5), (5, -5)):
        chandelier(bp, x, 9, z, drop=2)
    # hidden vault inside the third tier, reached by a ladder under a cracked slab on the summit
    bp.room(2, 13, 2, 8, 17, 8, PBB, floor=GBS, ceiling=PBB)
    bp.set(6, ys - 1, 5, CPBB)
    bp.clear(6, 14, 5, 6, ys - 2, 5)
    bp.ladder(6, 17, 5, ys - 2, "south")
    bp.chest(3, 14, 7, "east", LOOT + "piglin_sanctuary")
    bp.fill(4, 14, 7, 5, 14, 7, "gold_block")
    bp.set(3, 14, 3, "soul_lantern[hanging=false,waterlogged=false]")
    # giant crimson fungi framing the temple
    for (fx, fz, h, r, sd) in ((-30, -24, 24, 9, 1), (29, -28, 20, 8, 2), (-29, 27, 18, 7, 3),
                               (31, 24, 26, 9, 4), (14, -32, 12, 5, 5), (-16, 33, 11, 5, 6)):
        giant_fungus(bp, fx, 0, fz, h, r, seed=sd)
    # braziers around the court
    for k in (-18, -9, 9, 18):
        for (x, z) in ((k, 26), (k, -26), (26, k), (-26, k)):
            brazier(bp, x, 0, z)
    piglin_king_lair(bp)


register(StructureDef(
    "piglin_sanctuary", "nether", ["crimson_forest", "nether_wastes"],
    [Piece("sanctuary", piglin_sanctuary)], spacing=24, separation=8, adaptation="beard_box",
    height=("uniform", 30, 46), processors="aging",
    title_fr="Sanctuaire piglin", title_en="Piglin Sanctuary"))


# ============================================================ Lava foundry
# An industrial foundry on a stilted deck above the lava sea: a long brick casting hall under a
# green-copper sawtooth roof, a smelting line of blast furnaces, hanging crucibles (one pouring
# into the casting channel), a round blast-furnace tower, three tall brick chimneys, copper pipes
# with glowing bulbs, a cargo dock with a jib crane and a smugglers' cache under the pier.
# Blueprint y=0 is the deck (absolute y40): stilts reach down to y=-16 into the lava sea (y=-9).
LF_SEA = -9
NBRICK = Palette({"nether_bricks": 5, "red_nether_bricks": 2, "cracked_nether_bricks": 1}, seed=31, scale=2.5)
CLAY = Palette({"bricks": 5, "nether_bricks": 1}, seed=32, scale=2.0)
CU = "waxed_weathered_cut_copper"
CUS = "waxed_weathered_cut_copper_stairs"
CUSL = "waxed_weathered_cut_copper_slab"
PIPE = "waxed_exposed_copper"
BULB = "waxed_copper_bulb[lit=true,powered=false]"


def pipe(bp, pts, bulbs=6):
    """Copper pipe through axis-aligned waypoints, with glowing bulbs at intervals and at joints."""
    n = 0
    for (a, b) in zip(pts, pts[1:]):
        (x0, y0, z0), (x1, y1, z1) = a, b
        steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // max(1, steps)
            y = y0 + (y1 - y0) * i // max(1, steps)
            z = z0 + (z1 - z0) * i // max(1, steps)
            bp.set(x, y, z, BULB if (n % bulbs == 0 and n) else PIPE)
            n += 1
        bp.set(*b, "waxed_copper_grate[waterlogged=false]")


def chimney(bp, cx, cz, h, seed=0):
    """Tall round brick chimney tapering from r=3 to r=2: plinth, banded shaft with copper ties
    and glowing bulbs, corbelled crown, smoke."""
    fill_pal(bp, cx - 4, -1, cz - 4, cx + 4, 3, cz + 4, NBRICK)
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if max(abs(x - cx), abs(z - cz)) == 4:
                bp.set(x, 4, z, stair("nether_brick_stairs", toward(cx, cz, x, z)))
    step = int(h * 0.55)
    for y in range(4, h + 1):
        r = 3 if y < step else 2
        bp.disk(cx, y, cz, r - 1, "air")
        for (x, z) in ring_cells(cx, cz, r, inner=0.8):
            bp.set(x, y, z, "nether_bricks" if y % 7 == 0 else CLAY.pick(x, y, z))
        if y % 7 == 3:
            for (x, z) in ring_cells(cx, cz, r + 1):
                if x == cx or z == cz:
                    bp.set(x, y, z, BULB if y % 14 == 3 else CU)
    for (x, z) in ring_cells(cx, cz, 3):
        bp.set(x, step, z, stair("brick_stairs", toward(cx, cz, x, z)))
    for (x, z) in ring_cells(cx, cz, 3):
        bp.set(x, h - 1, z, stair("brick_stairs", toward(cx, cz, x, z), "top"))
        bp.set(x, h, z, "nether_bricks")
        bp.set(x, h + 1, z, "nether_brick_fence" if (x + z) % 2 else "nether_bricks")
    bp.set(cx, h - 1, cz, "magma_block")
    for dx, dz in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
        bp.set(cx + dx, h, cz + dz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


def crucible(bp, cx, y, cz, pour=None):
    """Hanging 5x5 crucible full of lava, chained to the gantry above. pour = side direction of a
    spout that empties into the channel below."""
    bp.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, PBB)
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if max(abs(x - cx), abs(z - cz)) == 2:
                bp.set(x, y + 1, z, "iron_block" if (x + z) % 2 else PBB)
                bp.set(x, y + 2, z, PBB)
            else:
                bp.set(x, y + 1, z, "lava[level=0]")
                bp.set(x, y + 2, z, "lava[level=0]")
    for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
        bp.chain(x, y + 3, z, 12)
    bp.set(cx, y - 1, cz, LAMP)
    if pour:
        dx, dz = FACE_VEC[pour]
        bp.set(cx + 2 * dx, y + 2, cz + 2 * dz, "lava[level=0]")
        lavafall(bp, cx + 3 * dx, cz + 3 * dz, y + 2, 0)


def lava_foundry(bp):
    # ---------------- stilted deck over the lava sea
    deck = set()
    for x in range(-30, 25):
        for z in range(-22, 15):
            deck.add((x, z))
    for x in range(-6, 7):
        for z in range(15, 36):
            deck.add((x, z))
    for x in range(25, 30):
        for z in range(-14, 2):
            deck.add((x, z))
    for (x, z) in deck:
        bp.set(x, 0, z, "spruce_planks" if (x // 3 + z) % 5 else "dark_oak_planks")
        if x % 3 == 0 or z % 3 == 0:
            bp.set(x, -1, z, "nether_bricks")
    for (x, z) in deck:
        edge = any((x + dx, z + dz) not in deck for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            bp.set(x, 0, z, "nether_bricks")
            bp.set(x, 1, z, "nether_brick_fence")
            if (x + z) % 8 == 0:
                bp.set(x, 1, z, "nether_bricks")
                bp.set(x, 2, z, "lantern[hanging=false,waterlogged=false]")
        if x % 6 == 0 and z % 6 == 0 or edge and (x + z) % 6 == 0:
            for y in range(-16, 0):
                bp.set(x, y, z, NBRICK.pick(x, y, z))
            bp.set(x, LF_SEA + 1, z, "nether_bricks")
            for d, (ddx, ddz) in (("east", (1, 0)), ("west", (-1, 0)), ("south", (0, 1)), ("north", (0, -1))):
                if (x + ddx, z + ddz) in deck:
                    bp.set(x + ddx, -2, z + ddz, stair("nether_brick_stairs", OPPOSITE[d], "top"))
            # cross bracing towards the next stilt
            if (x + 6, z) in deck and x % 6 == 0 and z % 6 == 0:
                for i in range(1, 6):
                    bp.set(x + i, -2 - abs(3 - i), z, "nether_brick_fence")
            if (x, z + 6) in deck and x % 6 == 0 and z % 6 == 0:
                for i in range(1, 6):
                    bp.set(x, -2 - abs(3 - i), z + i, "nether_brick_fence")
    # ---------------- main casting hall
    x0, x1, z0, z1 = -26, 6, -12, 12
    H = 14
    bp.clear(x0 + 1, 1, z0 + 1, x1 - 1, H + 8, z1 - 1)
    for face, line, u0, u1 in (("south", z1, x0, x1), ("north", z0, x0, x1), ("east", x1, z0, z1),
                               ("west", x0, z0, z1)):
        arch.facade(bp, face, line, u0, u1, 0, H, NBRICK, PBAS, pilaster_every=4, window_h=6, window_y=3,
                    plinth=PBB, plinth_stairs=PBBS, cornice_stairs="nether_brick_stairs",
                    glass="orange_stained_glass_pane", sill="nether_brick_stairs")
    fill_pal(bp, x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, FLOOR)
    # sawtooth copper roof: glazed vertical faces look west, copper slopes fall towards +x
    for a in range(x0, x1, 8):
        for i in range(8):
            x = a + i
            if x > x1:
                break
            for z in range(z0 - 1, z1 + 2):
                if i == 0:
                    for yy in range(H + 1, H + 8):
                        bp.set(x, yy, z, "orange_stained_glass" if z0 < z < z1 else CU)
                    bp.set(x, H + 8, z, slab(CUSL))
                else:
                    bp.set(x, H + 8 - i, z, stair(CUS, "west"))
            for z in (z0, z1):
                for yy in range(H + 1, H + 8 - i):
                    bp.set(x, yy, z, NBRICK.pick(x, yy, z))
    # gantry beam + crucibles over the casting channel
    for x in range(x0 + 1, x1):
        bp.set(x, 13, -3, PBB)
        bp.set(x, 13, -4, stair(PBBS, "south", "top"))
        bp.set(x, 13, -2, stair(PBBS, "north", "top"))
    for x in range(x0 + 1, x1):
        bp.set(x, 0, 0, "lava[level=0]")
        bp.set(x, -1, 0, "magma_block")
        bp.set(x, 1, -1, PBBW if x % 4 else LAMP)
        bp.set(x, 1, 1, PBBW if x % 4 else LAMP)
        if x % 3 == 0:
            bp.set(x, 0, 2, "iron_block" if x % 6 else "gold_block")
    # slag chute: the channel leaves the hall and pours off the deck into the lava sea
    for x in range(-31, x0 + 1):
        bp.set(x, 0, 0, "lava[level=0]")
        bp.set(x, -1, 0, "magma_block")
        for y in (1, 2):
            bp.set(x, y, 0, "air")
        if x < x0:
            bp.set(x, 1, -1, PBBW if x % 3 else LAMP)
            bp.set(x, 1, 1, PBBW if x % 3 else LAMP)
            bp.set(x, 0, -1, "nether_bricks")
            bp.set(x, 0, 1, "nether_bricks")
    bp.set(-31, -1, 0, "nether_bricks")
    bp.set(-31, 0, -1, "nether_bricks")
    bp.set(-31, 0, 1, "nether_bricks")
    bp.set(-31, 1, 0, "air")
    lavafall(bp, -32, 0, 0, LF_SEA)
    bp.set(-32, 0, -1, "nether_bricks")
    bp.set(-32, 0, 1, "nether_bricks")
    bp.set(-32, -1, -1, stair(PBBS, "south", "top"))
    bp.set(-32, -1, 1, stair(PBBS, "north", "top"))
    crucible(bp, -16, 6, -3, pour="south")
    crucible(bp, -4, 7, -3)
    # smelting line along the north wall
    for x in range(x0 + 2, x1 - 1, 2):
        bp.set(x, 1, z0 + 1, "blast_furnace[facing=south,lit=true]")
        bp.set(x, 2, z0 + 1, "hopper[enabled=true,facing=down]")
        bp.set(x + 1, 1, z0 + 1, "magma_block" if x % 4 else "smoker[facing=south,lit=true]")
    pipe(bp, [(x0 + 2, 4, z0 + 1), (x1 - 2, 4, z0 + 1)], bulbs=4)
    # anvils and work tables along the south wall
    for x in range(x0 + 3, x1 - 2, 5):
        bp.set(x, 1, z1 - 2, "anvil[facing=east]")
        bp.set(x + 1, 1, z1 - 2, "smithing_table")
        bp.set(x + 2, 1, z1 - 2, "grindstone[face=floor,facing=north]")
    bp.chest(x1 - 2, 1, z1 - 1, "north", LOOT + "lava_foundry")
    bp.barrel(x0 + 1, 1, z1 - 1, "up", LOOT + "lava_foundry")
    bp.spawner(-10, 1, 6, "minecraft:magma_cube")
    for x in (-20, -10, 0):
        bp.lantern(x, 12, 6, hanging=True)
        bp.chain(x, 13, 6, 14)
    # big doors
    arch.arch_door(bp, "south", z1, -2, 0, width=5, height=7, trim=PBAS, stairs=PBBS)
    # ore-cart rails from the dock into the hall
    for z in range(3, 35):
        bp.set(-2, 1, z, "rail[shape=north_south,waterlogged=false]")
        bp.set(-2, 0, z, "nether_bricks")
    bp.entity(-2, 1, 24, {"id": "minecraft:chest_minecart", "LootTable": LOOT + "lava_foundry"})
    bp.entity(-2, 1, 9, {"id": "minecraft:minecart"})
    arch.arch_door(bp, "east", x1, 0, 0, width=3, height=5, trim=PBAS, stairs=PBBS)
    # ---------------- blast-furnace tower
    tx, tz = 16, -8
    round_tower(bp, tx, tz, 0, 22, 5, wall=CLAY, base=-16, roof="crenels", band="nether_bricks",
                rib="nether_bricks", slit_seed=3, floors_every=7)
    bp.disk(tx, 23, tz, 4, "lava[level=0]")
    bp.disk(tx, 22, tz, 4, PBB)
    for y in range(1, 6):
        bp.set(tx - 5, y, tz, "air")
    for (dy, dz) in ((2, -1), (2, 1)):
        bp.set(tx - 5, 1 + dy, tz + dz, LAMP)
    # spout pouring from the tower crown down to a basin by the hall
    bp.set(tx - 7, 24, tz, GBS)
    bp.set(tx - 7, 23, tz, stair(PBBS, "east", "top"))
    lavafall(bp, tx - 7, tz, 22, 0)
    bp.set(tx - 7, 22, tz, "lava[level=0]")
    for z in (tz - 1, tz + 1):
        bp.set(tx - 7, 1, z, PBBW)
    bp.set(tx - 7, -1, tz, "magma_block")
    pipe(bp, [(tx - 5, 10, tz + 3), (x1 + 1, 10, tz + 3), (x1 + 1, 10, -2)], bulbs=3)
    pipe(bp, [(tx + 3, 4, tz + 5), (tx + 3, 4, 10), (x1 + 2, 4, 10)], bulbs=3)
    # ---------------- chimneys behind the hall
    for (cx, h, sd) in ((-20, 38, 1), (-8, 46, 2), (4, 34, 3)):
        chimney(bp, cx, -17, h, seed=sd)
        pipe(bp, [(cx, 8, -14), (cx, 8, -13)], bulbs=9)
    # ---------------- cargo dock with a jib crane
    for z in range(15, 36, 4):
        for x in (-6, 6):
            bp.set(x, 1, z, "nether_bricks")
            bp.set(x, 2, z, "iron_chain[axis=y,waterlogged=false]")
    for (x, z) in ((-3, 18), (-2, 18), (-3, 19), (3, 20), (2, 21), (3, 22)):
        bp.barrel(x, 1, z, "up")
    bp.barrel(-3, 2, 18, "up", LOOT + "lava_foundry")
    bp.set(2, 1, 17, "coal_block")
    bp.set(2, 2, 17, "coal_block")
    bp.set(-2, 1, 22, "magma_block")
    mx, mz = 3, 31
    fill_pal(bp, mx - 1, 0, mz - 1, mx + 1, 26, mz + 1, NBRICK)
    for y in range(2, 26, 4):
        for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bp.set(mx + dx, y, mz + dz, PBAS)
    bp.fill(mx - 2, 26, mz - 1, mx + 6, 27, mz + 1, PBB)
    fill_pal(bp, mx + 4, 23, mz - 1, mx + 6, 25, mz + 1, BLACK)
    bp.fill(mx + 4, 24, mz - 1, mx + 6, 24, mz + 1, GILD)
    for x in range(mx - 2, mx - 25, -1):
        bp.set(x, 27, mz, PBB)
        bp.set(x, 26, mz, PBBW if x % 3 else "nether_bricks")
        if (mx - x) % 3 == 0:
            bp.line((x, 27, mz), (mx, 31, mz), "iron_chain[axis=y,waterlogged=false]")
    bp.set(mx, 31, mz, LAMP)
    bp.set(mx, 32, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    hx = mx - 22
    bp.chain(hx, 10, mz, 25)
    bp.fill(hx - 1, 8, mz - 1, hx + 1, 9, mz + 1, "barrel[facing=up,open=false]")
    bp.fill(hx - 1, 7, mz - 1, hx + 1, 7, mz + 1, PBB)
    bp.lantern(hx, 6, mz, hanging=True)
    # smugglers' cache hanging under the pier, reached through a hatch
    bp.set(0, 0, 27, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(0, -4, 26, -1, "south")
    bp.room(-3, -6, 24, 3, -1, 30, "nether_bricks", floor=PBB)
    bp.set(0, -1, 26, "ladder[facing=south,waterlogged=false]")
    bp.set(0, -1, 27, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(0, 0, 27, "air")
    bp.chest(-2, -5, 29, "east", LOOT + "lava_foundry")
    bp.set(2, -5, 29, "gold_block")
    bp.lantern(0, -2, 28, hanging=True)
    bp.set(0, -7, 27, LAMP)
    # foreman's office / ingot store on the east deck, under a copper gable
    ox0, ox1, oz0, oz1 = 12, 22, 3, 12
    bp.clear(ox0 + 1, 1, oz0 + 1, ox1 - 1, 9, oz1 - 1)
    for face, line, u0, u1 in (("south", oz1, ox0, ox1), ("north", oz0, ox0, ox1), ("east", ox1, oz0, oz1),
                               ("west", ox0, oz0, oz1)):
        arch.facade(bp, face, line, u0, u1, 0, 9, NBRICK, PBAS, pilaster_every=5, window_h=2, window_y=2,
                    floors=[0, 5], floor_band="nether_bricks", plinth=PBB, plinth_stairs=PBBS,
                    cornice_stairs="nether_brick_stairs", glass="orange_stained_glass_pane",
                    sill="nether_brick_stairs")
    fill_pal(bp, ox0 + 1, 0, oz0 + 1, ox1 - 1, 0, oz1 - 1, FLOOR)
    bp.fill(ox0 + 1, 5, oz0 + 1, ox1 - 1, 5, oz1 - 1, "spruce_planks")
    arch.steep_roof(bp, ox0, oz0, ox1, oz1, 10, CUS, axis="x", overhang=1, steep=1, fill="nether_bricks",
                    under="nether_brick_stairs", ridge=slab(CUSL))
    arch.arch_door(bp, "south", oz1, 17, 0, width=1, height=3, trim=PBAS, stairs=PBBS)
    bp.door(17, 1, oz1, "south", "crimson")
    arch.stair_run(bp, ox1 - 1, 1, oz1 - 1, "north", 4, 1, "spruce_stairs", clear=3)
    for x in range(ox0 + 1, ox1 - 1, 2):
        bp.set(x, 1, oz0 + 1, "iron_block" if x % 4 == 1 else "gold_block")
        bp.barrel(x + 1, 1, oz0 + 1, "up")
    bp.set(ox0 + 2, 6, oz0 + 2, "cartography_table")
    bp.set(ox0 + 3, 6, oz0 + 2, "lectern[facing=south,has_book=false,powered=false]")
    bp.bed(ox0 + 2, 6, oz1 - 3, "south", "red")
    bp.chest(ox0 + 4, 6, oz1 - 1, "north", LOOT + "lava_foundry")
    bp.lantern(17, 4, 7, hanging=True)
    bp.lantern(17, 9, 7, hanging=True)
    # ore yard on the east platform
    for (x, z) in ((27, -12), (28, -10), (26, -6), (28, -3)):
        bp.set(x, 1, z, "nether_gold_ore")
        bp.set(x, 2, z, "nether_gold_ore" if (x + z) % 2 else "magma_block")
    brazier(bp, 27, 1, 0)
    brazier(bp, 27, 1, -14)


register(StructureDef(
    "lava_foundry", "nether", ["nether_wastes", "basalt_deltas", "crimson_forest", "warped_forest"],
    [Piece("foundry", lava_foundry)], spacing=24, separation=8, adaptation="none",
    height=("absolute", 24), processors="aging",
    title_fr="Fonderie de lave", title_en="Lava Foundry"))


# ============================================================ Soul tower (soul sand valley)
# A 52-block black tower tapering in three stages, clasped by six twisting bone buttresses that
# spiral up its flanks with rib-like struts. Cyan lancet windows glow with soul lanterns, three
# ghostly balconies hang off different sides, and the top bristles with a crown of outward-leaning
# blackstone spikes around a needle spire. Inside, a spiral stair climbs past six floors; under
# the tower lies a hidden ossuary.
ST_TOP = 52
SOUL = Palette({PBB: 4, "blackstone": 2, CPBB: 1, "smooth_basalt": 1}, seed=41, scale=2.5)
SOUL_GROUND = Palette({"soul_soil": 4, "soul_sand": 3, "basalt[axis=y]": 1, "blackstone": 1}, seed=42, scale=3.0)
BONE = "bone_block[axis=y]"
SOULGLASS = "cyan_stained_glass_pane"


def st_r(y):
    return 8 if y < 16 else 7 if y < 34 else 6


def bone_buttresses(bp, cx, cz, n, y0, y1, twist, flare, seed=0):
    """Helical bone buttresses: thick and flared at the foot, thinning as they wind up the tower,
    tied back to the wall by rib struts."""
    for k in range(n):
        prev = None
        for y in range(y0, y1):
            t = (y - y0) / (y1 - y0)
            ang = 2 * math.pi * k / n + math.radians(twist * (y - y0))
            rad = st_r(max(y, 0)) + 1.2 + flare * (1 - t) ** 2.2
            x = cx + round(math.cos(ang) * rad)
            z = cz + round(math.sin(ang) * rad)
            th = 1.0 if t < 0.12 else 0.5
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if math.hypot(dx, dz) <= th:
                        bp.set(x + dx, y, z + dz, BONE)
            if prev and max(abs(prev[0] - x), abs(prev[1] - z)) > 1:
                bp.line((prev[0], y - 1, prev[1]), (x, y, z), BONE)
            prev = (x, z)
            if y % 6 == 3 and t > 0.05:
                wx = cx + round(math.cos(ang) * (st_r(y) + 0.5))
                wz = cz + round(math.sin(ang) * (st_r(y) + 0.5))
                bp.line((x, y, z), (wx, y, wz), "bone_block[axis=x]" if abs(x - wx) >= abs(z - wz)
                        else "bone_block[axis=z]")
        # skull finial where the buttress dies into the wall
        bp.set(prev[0], y1, prev[1], "wither_skeleton_skull[rotation=%d]" % ((k * 3) % 16))


def ghost_balcony(bp, cx, cz, y, ang_deg, depth=3, spread=40, loot=None):
    """Half-moon balcony on corbels: slab floor, wall rail, soul lantern posts, hanging lanterns."""
    r = st_r(y)
    a0 = math.radians(ang_deg)
    cells = []
    for x in range(cx - r - depth - 1, cx + r + depth + 2):
        for z in range(cz - r - depth - 1, cz + r + depth + 2):
            d = math.hypot(x - cx, z - cz)
            da = abs((math.atan2(z - cz, x - cx) - a0 + math.pi) % (2 * math.pi) - math.pi)
            if r + 0.4 < d <= r + depth + 0.4 and da <= math.radians(spread):
                cells.append((x, z, d, da))
    for (x, z, d, da) in cells:
        bp.set(x, y, z, PBB)
        bp.set(x, y - 1, z, stair(PBBS, toward(cx, cz, x, z), "top"))
        outer = d > r + depth - 0.6 or da > math.radians(spread - 9)
        if outer:
            bp.set(x, y + 1, z, PBBW)
            if (x + z) % 4 == 0:
                bp.set(x, y + 2, z, "soul_lantern[hanging=false,waterlogged=false]")
            if (x * 3 + z) % 5 == 0:
                bp.chain(x, y - 3, z, y - 2)
                bp.lantern(x, y - 4, z, hanging=True, soul=True)
    # doorway into the tower
    dx, dz = math.cos(a0), math.sin(a0)
    for k in (r - 1, r, r + 1):
        x, z = cx + round(dx * k), cz + round(dz * k)
        for yy in (y + 1, y + 2):
            bp.set(x, yy, z, "air")
    x, z = cx + round(dx * (r + 2)), cz + round(dz * (r + 2))
    if loot:
        bp.chest(x, y + 1, z, toward(cx, cz, x, z), loot)
    else:
        bp.set(x, y + 1, z, "skeleton_skull[rotation=0]")


def soul_tower(bp):
    cx = cz = 0
    # soul sand mound with fossils, basalt columns and soul fire
    rock_island(bp, 18, 18, 18, depth=6, slope=0.9, spread=7, seed=13, pillars=18, pal=SOUL_GROUND)
    rng = random.Random(8)
    for x in range(-25, 26):
        for z in range(-25, 26):
            top = None
            for y in range(-1, -12, -1):
                if bp.get(x, y, z):
                    top = y
                    break
            if top is not None and rng.random() < 0.025 and math.hypot(x, z) > 11:
                bp.set(x, top + 1, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for a in (35, 155, 275):
        fx, fz = round(math.cos(math.radians(a)) * 15), round(math.sin(math.radians(a)) * 15)
        for k in range(-4, 5, 2):
            px, pz = fx + round(math.cos(math.radians(a + 90)) * k), fz + round(math.sin(math.radians(a + 90)) * k)
            hh = 5 - abs(k) // 2
            bp.line((px - round(math.cos(math.radians(a)) * 3), -1, pz - round(math.sin(math.radians(a)) * 3)),
                    (px, hh, pz), BONE)
            bp.line((px, hh, pz), (px + round(math.cos(math.radians(a)) * 3), -1,
                                   pz + round(math.sin(math.radians(a)) * 3)), BONE)
        bp.line((fx - round(math.cos(math.radians(a + 90)) * 5), 4, fz - round(math.sin(math.radians(a + 90)) * 5)),
                (fx + round(math.cos(math.radians(a + 90)) * 5), 4, fz + round(math.sin(math.radians(a + 90)) * 5)),
                BONE)
    # ---------------- the tower shell (three tapering stages)
    for y in range(-6, ST_TOP + 1):
        r = st_r(max(y, 0))
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.4:
                    if d > r - 0.8 or y <= 0:
                        bp.set(x, y, z, SOUL.pick(x, y, z))
                    else:
                        bp.set(x, y, z, "air")
    for (y, r) in ((15, 8), (33, 7)):
        for (x, z) in ring_cells(cx, cz, r + 1):
            bp.set(x, y, z, stair(PBBS, toward(cx, cz, x, z), "top"))
        for (x, z) in ring_cells(cx, cz, r):
            bp.set(x, y + 1, z, stair(PBBS, toward(cx, cz, x, z)))
            bp.set(x, y, z, CHIS)
    for (x, z) in ring_cells(cx, cz, 9):
        bp.set(x, 0, z, PBB)
        bp.set(x, 1, z, stair(PBBS, toward(cx, cz, x, z)))
    # rings of soul lanterns dripping from the corbel courses
    for (y, r) in ((15, 8), (33, 7)):
        for i, (x, z) in enumerate(sorted(ring_cells(cx, cz, r + 1), key=lambda p: math.atan2(p[1], p[0]))):
            if i % 3 == 0:
                bp.chain(x, y - 1, z, y - 1)
                bp.lantern(x, y - 2, z, hanging=True, soul=True)
    # floors around the open stair well, spiral stair round a bone column
    floors = list(range(8, ST_TOP, 8))
    for fy in floors:
        r = st_r(fy)
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if max(abs(x - cx), abs(z - cz)) >= 3 and math.hypot(x - cx, z - cz) <= r - 0.6:
                    bp.set(x, fy, z, PB if (x + z) % 2 else PBB)
    fill_pal(bp, -7, 0, -7, 7, 0, 7, FLOOR)
    bp.disk(cx, 0, cz, 7, PB)
    for (x, z) in ring_cells(cx, cz, 5):
        bp.set(x, 0, z, CHIS)
    bp.spiral_stairs(cx, cz, 1, ST_TOP, 2, PBBSL, center=BONE)
    # lancet windows with soul light, rotating floor by floor
    for i, fy in enumerate([0] + floors):
        r = st_r(fy + 3)
        for q in range(4):
            a = math.radians(45 + 90 * q + i * 22)
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            for dy in range(2, 6):
                bp.set(x, fy + dy, z, SOULGLASS)
            bp.set(x, fy + 6, z, CHIS)
            ix, iz = cx + round(math.cos(a) * (r - 1)), cz + round(math.sin(a) * (r - 1))
            if fy and bp.get(ix, fy, iz):
                bp.set(ix, fy + 1, iz, "soul_lantern[hanging=false,waterlogged=false]")
            ox, oz = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
            bp.set(ox, fy + 1, oz, stair(PBBS, toward(cx, cz, ox, oz), "top"))
        bp.lantern(cx + 4, fy + 7, cz, hanging=True, soul=True)
        bp.lantern(cx - 4, fy + 7, cz, hanging=True, soul=True)
    # entrance with a bone arch
    for z in range(cz + 6, cz + 10):
        for x in (-1, 0, 1):
            for y in (1, 2, 3):
                bp.set(x, y, z, "air")
            bp.set(x, 0, z, PBB)
    for z in (cz + 9, cz + 10):
        for (x, y) in ((-2, 1), (-2, 2), (-2, 3), (2, 1), (2, 2), (2, 3), (-2, 4), (2, 4), (-1, 5), (0, 5), (1, 5)):
            bp.set(x, y, z, BONE)
        bp.set(-1, 4, z, stair(PBBS, "east", "top"))
        bp.set(1, 4, z, stair(PBBS, "west", "top"))
        bp.set(0, 6, z, "wither_skeleton_skull[rotation=0]" if z == cz + 10 else BONE)
    bp.door(-1, 1, cz + 8, "south", "crimson", hinge="left")
    bp.door(1, 1, cz + 8, "south", "crimson", hinge="right")
    bp.set(0, 1, cz + 8, "polished_blackstone_brick_wall")   # mullion between the two leaves
    bp.set(0, 2, cz + 8, "polished_blackstone_brick_wall")
    for x in (-3, 3):
        brazier(bp, x, 0, cz + 11, soul=True, big=True)
    # ---------------- twisted bone buttresses
    bone_buttresses(bp, cx, cz, 6, -3, ST_TOP - 6, twist=4.0, flare=5.0)
    # ---------------- ghostly balconies
    ghost_balcony(bp, cx, cz, 24, 40, depth=4, spread=45)
    ghost_balcony(bp, cx, cz, 40, 200, depth=4, spread=45, loot=LOOT + "soul_tower")
    ghost_balcony(bp, cx, cz, 48, 310, depth=3)
    # ---------------- crown of spikes around a needle spire
    top = ST_TOP
    r = st_r(top)
    for (x, z) in ring_cells(cx, cz, r + 1):
        bp.set(x, top - 1, z, stair(PBBS, toward(cx, cz, x, z), "top"))
        bp.set(x, top, z, SOUL.pick(x, top, z))
    for (x, z) in ring_cells(cx, cz, r + 2):
        bp.set(x, top, z, stair(PBBS, toward(cx, cz, x, z), "top"))
    bp.disk(cx, top + 1, cz, r + 2, PBB)
    bp.disk(cx, top + 1, cz, r - 1, PB)
    # stair well opening onto the roof, railed, around the bone needle
    for x in range(-2, 3):
        for z in range(-2, 3):
            if (x, z) != (0, 0):
                bp.set(cx + x, top + 1, cz + z, "air")
    for x in range(-3, 4):
        for z in range(-3, 4):
            if max(abs(x), abs(z)) == 3 and not (z == 3 and abs(x) <= 1):
                bp.set(cx + x, top + 2, cz + z, PBBW)
    cells = sorted(ring_cells(cx, cz, r + 2), key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    for i, (x, z) in enumerate(cells):
        bp.set(x, top + 2, z, SOUL.pick(x, top + 2, z))
    for k in range(14):
        a = 2 * math.pi * k / 14
        h = 9 if k % 2 == 0 else 5
        x0_, z0_ = cx + math.cos(a) * (r + 2), cz + math.sin(a) * (r + 2)
        x1_, z1_ = cx + math.cos(a) * (r + 4.5), cz + math.sin(a) * (r + 4.5)
        pts = []
        for j in range(h + 1):
            t = j / h
            pts.append((round(x0_ + (x1_ - x0_) * t * t), top + 2 + j, round(z0_ + (z1_ - z0_) * t * t)))
        for j, (x, y, z) in enumerate(pts):
            bp.set(x, y, z, "blackstone" if j < h * 0.5 else PBW)
        x, y, z = pts[-1]
        bp.set(x, y + 1, z, "end_rod[facing=up]")
    # soul braziers on the roof and the bone needle with its lantern crossbar
    for (x, z) in ((cx + 5, cz), (cx - 5, cz), (cx, cz + 5), (cx, cz - 5)):
        brazier(bp, x, top + 2, z, soul=True)
    for y in range(top + 1, top + 13):
        bp.set(cx, y, cz, BONE if y % 4 else CHIS)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, top + 10, cz + dz, PBBW)
        bp.set(cx + 2 * dx, top + 10, cz + 2 * dz, PBBW)
        bp.lantern(cx + 2 * dx, top + 9, cz + 2 * dz, hanging=True, soul=True)
    spike(bp, cx, cz, top + 13, 1, "blackstone", BS, steep=4, band=None, lamps=False,
          lamp="soul_lantern[hanging=false,waterlogged=false]")
    # ---------------- floor contents
    rooms = {8: "library", 16: "guard", 24: "crypt", 32: "alchemy", 40: "blaze", 48: "reliquary"}
    for fy, kind in rooms.items():
        r = st_r(fy) - 1
        if kind == "library":
            for a in range(0, 360, 30):
                x, z = cx + round(math.cos(math.radians(a)) * r), cz + round(math.sin(math.radians(a)) * r)
                for yy in (fy + 1, fy + 2):
                    if not bp.get(x, yy, z) or bp.get(x, yy, z) == "minecraft:air":
                        bp.set(x, yy, z, "bookshelf")
            bp.set(cx + 4, fy + 1, cz + 1, "lectern[facing=west,has_book=false,powered=false]")
            bp.set(cx - 4, fy + 1, cz - 2, "skeleton_skull[rotation=4]")
        elif kind == "guard":
            bp.spawner(cx + 4, fy + 1, cz - 3, MOB["basalt_guard"])
            for (x, z) in ((cx - 4, cz + 3), (cx + 3, cz + 4)):
                bp.set(x, fy + 1, z, "cobweb")
        elif kind == "crypt":
            for (x, z) in ((cx + 4, cz), (cx - 4, cz), (cx, cz + 4), (cx, cz - 4)):
                bp.set(x, fy + 1, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
                bp.set(x, fy + 2, z, "candle[candles=3,lit=true,waterlogged=false]")
            bp.set(cx + 3, fy + 1, cz + 3, "wither_skeleton_skull[rotation=6]")
        elif kind == "alchemy":
            bp.set(cx + 4, fy + 1, cz + 2, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
            bp.set(cx + 4, fy + 1, cz - 2, "cauldron")
            bp.set(cx - 4, fy + 1, cz + 2, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        elif kind == "blaze":
            bp.spawner(cx - 3, fy + 1, cz + 3, "minecraft:blaze")
            bp.set(cx + 3, fy + 1, cz - 3, "magma_block")
        elif kind == "reliquary":
            bp.chest(cx, fy + 1, cz - 4, "south", LOOT + "soul_tower")
            bp.set(cx - 1, fy + 1, cz - 4, "gold_block")
            bp.set(cx + 1, fy + 1, cz - 4, "candle[candles=4,lit=true,waterlogged=false]")
    # ---------------- hidden ossuary under the tower
    bp.disk(cx, -6, cz, 6, PBB)
    for y in range(-5, -1):
        for (x, z) in ring_cells(cx, cz, 6, inner=0.8):
            bp.set(x, y, z, BONE if (x + y + z) % 4 else CHIS)
        bp.disk(cx, y, cz, 5, "air")
    bp.disk(cx, -1, cz, 6, PBB)
    bp.set(cx, -5, cz, BONE)
    bp.set(cx + 4, 0, cz - 4, CPBB)
    bp.clear(cx + 4, -4, cz - 4, cx + 4, -1, cz - 4)
    bp.ladder(cx + 4, -5, cz - 3, -1, "south")
    bp.set(cx + 4, -5, cz - 4, "air")
    bp.chest(cx - 3, -5, cz + 3, "north", LOOT + "soul_tower")
    for (x, z) in ((cx - 4, cz), (cx + 4, cz + 2), (cx, cz - 4)):
        bp.set(x, -5, z, "soul_lantern[hanging=false,waterlogged=false]")
    # ---------------- the summit arena of the Soul Reaper (grace floor, turret, reliquary)
    from . import lair_soul_reaper
    lair_soul_reaper.build(bp, cx, cz)


register(StructureDef(
    "soul_tower", "nether", ["soul_sand_valley"], [Piece("tower", soul_tower)],
    spacing=22, separation=7, adaptation="beard_box", height=("uniform", 28, 34), processors="aging",
    title_fr="Tour des âmes", title_en="Soul Tower"))


# ============================================================ Piglin market
# A walled bazaar square: four arcaded market ranges full of stalls, red-roofed corner pavilions,
# four gilded gate arches with banners, striped crimson and warped awnings, festoons of lanterns
# strung from a central fountain-tower whose gargoyles pour lava into a gold-rimmed ring basin.
PM_H = 28        # half size of the square (outer wall line)
PM_IN = 23       # colonnade line
RNB = "red_nether_bricks"
RNBS = "red_nether_brick_stairs"
GOODS = ["gold_block", "raw_gold_block", "crying_obsidian", "magma_block", "quartz_block", "shroomlight",
         "decorated_pot[facing=north,waterlogged=false,cracked=false]", "lantern[hanging=false,waterlogged=false]",
         "gilded_blackstone", "nether_wart_block", "warped_wart_block", "soul_lantern[hanging=false,waterlogged=false]"]


def _frame(cx, cz, facing):
    fx, fz = FACE_VEC[facing]
    rx, rz = -fz, fx

    def w(u, v):
        return cx + rx * u + fx * v, cz + rz * u + fz * v
    return w


def market_stall(bp, cx, cz, facing, wood, seed=0, loot=None):
    """5x3 stall facing `facing` (towards the shoppers): fence posts, counter with goods, barrels,
    striped wool awning with a drooping front."""
    rng = random.Random(seed)
    w = _frame(cx, cz, facing)
    stripes = ("red_wool", "yellow_wool") if wood == "crimson" else ("cyan_wool", "light_blue_wool")
    for u in range(-2, 3):
        for v in range(-1, 2):
            x, z = w(u, v)
            bp.set(x, 0, z, f"{wood}_planks" if v == -1 else f"stripped_{wood}_hyphae[axis=y]")
    for u in (-2, 2):
        for v in (-1, 1):
            x, z = w(u, v)
            for y in range(1, 4):
                bp.set(x, y, z, f"{wood}_fence")
    for u in (-1, 0, 1):
        x, z = w(u, 1)
        bp.set(x, 1, z, f"{wood}_planks")
        bp.set(x, 2, z, rng.choice(GOODS))
        x, z = w(u, -1)
        bp.barrel(x, 1, z, "up", loot if (loot and u == 0) else None)
        bp.set(x, 2, z, "barrel[facing=north,open=false]" if u else rng.choice(GOODS))
    for u in range(-2, 3):
        for v in range(-2, 3):
            x, z = w(u, v)
            bp.set(x, {-2: 3, -1: 4, 0: 5, 1: 4, 2: 3}[v], z, stripes[(u + 2) % 2])
        x, z = w(u, 0)
        if abs(u) == 2:
            bp.set(x, 4, z, f"{wood}_fence")
    x, z = w(0, 0)
    bp.lantern(x, 3, z, hanging=True)


def festoon(bp, axis, sign, r0, r1, y0, y1, sag=4):
    """Chain strung along an axis from (r0, y0) to (r1, y1), sagging, with lanterns every 3."""
    pts = []
    n = r1 - r0
    for i in range(n + 1):
        t = i / n
        y = round(y0 + (y1 - y0) * t - sag * 4 * t * (1 - t))
        pts.append((r0 + i, y))
    for (r, y), (_, y2) in zip(pts, pts[1:]):
        x, z = (sign * r, 0) if axis == "x" else (0, sign * r)
        lo, hi = sorted((y, y2))
        if hi > lo:
            for yy in range(lo, hi + 1):
                bp.set(x, yy, z, "iron_chain[axis=y,waterlogged=false]")
        else:
            bp.set(x, y, z, f"iron_chain[axis={axis},waterlogged=false]")
        if r % 3 == 0:
            bp.lantern(x, lo - 1, z, hanging=True)


def piglin_market(bp):
    H, I = PM_H, PM_IN
    # ground: blackstone/netherrack base, plaza paving with gilded radial lines
    rock_island(bp, H + 2, H + 2, 6, depth=8, slope=1.3, spread=6, seed=17, pillars=0, pal=NETHER_GROUND)
    for x in range(-H, H + 1):
        for z in range(-H, H + 1):
            d = math.hypot(x, z)
            a = math.degrees(math.atan2(z, x)) % 45
            line = (a < 3 or a > 42) and d > 11
            bp.set(x, 0, z, GBS if line else "gold_block" if (round(d) == 13 and (x + z) % 3 == 0)
                   else FLOOR.pick(x, 0, z))
            for y in range(1, 4):
                bp.set(x, y, z, "air")
    # ---------------- open double arcades on the four sides under striped tent canopies
    for face in ("north", "south", "east", "west"):
        line = H if face in ("south", "east") else -H
        along = arch._along_dir(face)
        for (u0, u1) in ((-H + 1, -5), (5, H - 1)):
            for u in range(u0, u1 + 1):
                k = (u - u0) % 4
                bay = (u - u0) // 4
                warm = (bay + len(face)) % 2 == 0
                stripes = ("red_wool", "yellow_wool") if warm else ("cyan_wool", "light_blue_wool")
                for t in range(0, H - I + 1):
                    x, z = _pos(face, line, u, -t)
                    bp.set(x, 0, z, PB if 0 < t < H - I else PBB)
                    for y in range(1, 11):
                        bp.set(x, y, z, "air")
                    cy = 8 + min(t, H - I - t, 2)
                    bp.set(x, cy, z, stripes[u % 2])
                # the two colonnades (outer line and inner line)
                for t in (0, H - I):
                    x, z = _pos(face, line, u, -t)
                    if k == 0 or u == u1:
                        for y in range(1, 8):
                            bp.set(x, y, z, PBAS)
                        bp.set(x, 1, z, CHIS)
                        bp.set(x, 8, z, "gold_block")
                        if t:
                            bp.set(x, 9, z, "lantern[hanging=false,waterlogged=false]")
                        else:
                            ox, oz = _pos(face, line, u, 1)
                            bp.set(ox, 0, oz, stair(PBBS, OPPOSITE[face]))
                            bp.set(ox, 1, oz, PBAS)
                            bp.set(ox, 2, oz, stair(PBBS, OPPOSITE[face]))
                    else:
                        bp.set(x, 7, z, PBB)
                        if k == 1:
                            bp.set(x, 6, z, stair(PBBS, OPPOSITE[along], "top"))
                        elif k == 3:
                            bp.set(x, 6, z, stair(PBBS, along, "top"))
                        if t == 0:
                            bp.set(x, 1, z, PBBW)
                    gx, gz = _pos(face, line, u, -t + (1 if t == 0 else -1))
                    bp.set(gx, 7, gz, stair(PBBS, OPPOSITE[face] if t == 0 else face, "top"))
            # goods, counters and lanterns under the arcade
            for k, u in enumerate(range(u0 + 2, u1 - 1, 4)):
                x, z = _pos(face, line, u, -1)
                bp.set(x, 1, z, "barrel[facing=up,open=false]")
                bp.set(x, 2, z, GOODS[(k + len(face)) % len(GOODS)])
                x2, z2 = _pos(face, line, u + 1, -1)
                bp.set(x2, 1, z2, "gold_block" if k % 2 else "raw_gold_block")
                x3, z3 = _pos(face, line, u, -3)
                bp.chain(x3, 8, z3, 9)
                bp.lantern(x3, 7, z3, hanging=True)
                if k % 3 == 1:
                    bx, bz = _pos(face, line, u + 1, -4)
                    bp.set(bx, 1, bz, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    # ---------------- corner pavilions
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, z0 = (I if sx > 0 else -H), (I if sz > 0 else -H)
            sq_tower(bp, x0, z0, x0 + H - I, z0 + H - I, 0, 15, TEMPLE, base=-4, steep=2, roof_block=RNB,
                     roof_stairs=RNBS, floors_every=5)
    # ---------------- gate towers with pointed arch passages and red spires
    for face in ("north", "south", "east", "west"):
        line = H if face in ("south", "east") else -H
        along = arch._along_dir(face)
        xa, za = _pos(face, line, -4, 1)
        xb, zb = _pos(face, line, 4, -(H - I) - 2)
        sq_tower(bp, min(xa, xb), min(za, zb), max(xa, xb), max(za, zb), 0, 13, TEMPLE, base=-4, steep=2,
                 roof_block=RNB, roof_stairs=RNBS, floors_every=20)
        rows = [(y, 2) for y in range(1, 8)] + [(8, 1), (9, 0)]
        for (y, hw) in rows:
            for u in range(-hw, hw + 1):
                for t in range(-3, H - I + 4):
                    x, z = _pos(face, line, u, -t)
                    bp.set(x, y, z, "air")
        for t in range(-3, H - I + 4):
            for u in (-2, -1, 0, 1, 2):
                x, z = _pos(face, line, u, -t)
                bp.set(x, 0, z, GBS if u == 0 else PBB)
        for t in (-1, H - I + 2):
            for (y, hw) in rows[7:]:
                x, z = _pos(face, line, -hw - 1, -t)
                bp.set(x, y, z, stair(PBBS, OPPOSITE[along], "top"))
                x, z = _pos(face, line, hw + 1, -t)
                bp.set(x, y, z, stair(PBBS, along, "top"))
            for (y, hw) in rows:
                for uu in (-hw - 2, hw + 2) if y >= 8 else (-3, 3):
                    x, z = _pos(face, line, uu, -t)
                    bp.set(x, y, z, GILD)
        x, z = _pos(face, line, 0, 2)
        bp.set(x, 11, z, "gold_block")
        bp.set(x, 12, z, "piglin_head[rotation=%d]" % {"south": 0, "west": 4, "north": 8, "east": 12}[face])
        x, z = _pos(face, line, 0, 1)
        bp.set(x, 10, z, LAMP)
        for uu in (-3, 3):
            x, z = _pos(face, line, uu, 2)
            bp.set(x, 11, z, f"orange_wall_banner[facing={face}]")
        x, z = _pos(face, line, 0, -3)
        bp.chain(x, 9, z, 9)
        bp.lantern(x, 8, z, hanging=True)
    # ---------------- central fountain-tower
    bp.disk(0, -1, 0, 10, "magma_block")
    for (x, z) in [(x, z) for x in range(-10, 11) for z in range(-10, 11)]:
        d = math.hypot(x, z)
        if 5.4 < d <= 9.4:
            bp.set(x, 0, z, "lava[level=0]")
        elif 9.4 < d <= 10.4:
            bp.set(x, 0, z, PBB)
            bp.set(x, 1, z, "gold_block" if (x + z) % 4 == 0 else PBBW)
    round_tower(bp, 0, 0, 0, 38, 4, wall=TEMPLE, base=-6, steep=4, roof_block=RNB, roof_stairs=RNBS,
                rib=PBAS, slit_seed=5, floors_every=7)
    for (x, z) in ring_cells(0, 0, 5):
        bp.set(x, 0, z, PBB)
    # open lantern loggia near the top with a golden bell
    for y in range(30, 35):
        for (x, z) in ring_cells(0, 0, 4, inner=0.8):
            if not (abs(x) == abs(z) or x == 0 or z == 0):
                bp.set(x, y, z, "air")
    bp.set(0, 35, 0, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.disk(0, 29, 0, 3, PB)
    bp.set(0, 29, -3, "ladder[facing=south,waterlogged=false]")
    for (x, z) in ((2, 0), (-2, 0), (0, 2)):
        bp.lantern(x, 35, z, hanging=True)
    # lava-spewing gargoyles into the ring basin
    for q in range(4):
        a = math.radians(45 + 90 * q)
        ca, sa = math.cos(a), math.sin(a)
        gx, gz = round(ca * 5), round(sa * 5)
        bp.set(gx, 9, gz, stair(PBBS, toward(0, 0, gx, gz), "top"))
        bp.set(gx, 10, gz, GBS)
        lx, lz = round(ca * 6.5), round(sa * 6.5)
        lavafall(bp, lx, lz, 9, 0)
    # tower door and interior
    for z in range(3, 6):
        bp.set(0, 1, z, "air")
        bp.set(0, 2, z, "air")
    for z in range(5, 11):
        bp.set(0, 0, z, GBS)
        bp.set(-1, 0, z, PBB)
        bp.set(1, 0, z, PBB)
        for x in (-1, 0, 1):
            bp.set(x, 1, z, "air")
        for x in (-2, 2):
            if z > 5:
                bp.set(x, 1, z, PBBW if z % 2 else "gold_block")
    bp.chest(-2, 1, -2, "south", LOOT + "piglin_market")
    bp.spawner(2, 1, -1, "minecraft:piglin")
    # hidden treasury under the tower
    bp.set(2, 0, 2, CPBB)
    bp.clear(2, -4, 2, 2, -1, 2)
    bp.ladder(2, -5, 1, -1, "south")
    bp.room(-4, -6, -4, 4, -1, 4, PBB, floor=GBS, ceiling=PBB)
    bp.set(2, -1, 2, "air")
    bp.set(2, -1, 1, "ladder[facing=south,waterlogged=false]")
    bp.chest(-3, -5, -3, "south", LOOT + "piglin_market")
    bp.fill(-3, -5, 3, 3, -5, 3, "gold_block")
    bp.fill(-2, -4, 3, 2, -4, 3, "raw_gold_block")
    bp.set(0, -5, 0, "soul_lantern[hanging=false,waterlogged=false]")
    # ---------------- stalls in the square (crimson and warped awnings)
    stalls = [((-11, 16), "north", "crimson"), ((11, 16), "north", "warped"),
              ((-11, -16), "south", "warped"), ((11, -16), "south", "crimson"),
              ((16, -11), "west", "crimson"), ((16, 11), "west", "warped"),
              ((-16, -11), "east", "crimson"), ((-16, 11), "east", "warped")]
    for i, ((x, z), f, wood) in enumerate(stalls):
        market_stall(bp, x, z, f, wood, seed=i, loot=LOOT + "piglin_market" if i in (0, 5) else None)
    # festoons of lanterns from the tower to the gates
    for axis in ("x", "z"):
        for sign in (-1, 1):
            festoon(bp, axis, sign, 5, H - 6, 22, 12, sag=3)
    # braziers, planted fungi, waystone
    for (x, z) in ((7, 18), (-7, 18), (7, -18), (-7, -18), (18, 7), (18, -7), (-18, 7), (-18, -7)):
        brazier(bp, x, 1, z, big=True)
    for (x, z, kind, sd) in ((-19, -19, "crimson", 1), (19, 19, "warped", 2), (19, -19, "crimson", 3),
                             (-19, 19, "warped", 4)):
        bp.disk(x, 0, z, 2, f"{kind}_nylium")
        for (px, pz) in ring_cells(x, z, 3):
            bp.set(px, 1, pz, PBBW if (px + pz) % 2 else GBS)
        giant_fungus(bp, x, 1, z, 8, 4, seed=sd, kind=kind)
    # piglin merchants minding the stalls
    for (x, z) in ((-11, 13), (13, -11), (-13, 11), (11, -13), (0, 12)):
        bp.entity(x, 1, z, {"id": "minecraft:piglin", "PersistenceRequired": True})
    bp.set(0, 1, 21, MOD["waystone"])
    bp.fill(-1, 0, 20, 1, 0, 22, GBS)
    for x in (-2, 2):
        bp.set(x, 1, 21, "soul_lantern[hanging=false,waterlogged=false]")


register(StructureDef(
    "piglin_market", "nether", ["crimson_forest", "warped_forest", "nether_wastes"],
    [Piece("market", piglin_market)], spacing=24, separation=8, adaptation="beard_box",
    height=("uniform", 30, 42), processors="aging",
    title_fr="Marché piglin", title_en="Piglin Market"))
