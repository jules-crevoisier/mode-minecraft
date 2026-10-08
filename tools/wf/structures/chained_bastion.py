"""Chained Bastion (Bastion enchaîné / Chained Bastion): a blackstone and gilded fortress hanging under the Nether
ceiling from eight colossal chains, over a lava lake. Colossal tier (tools/BUILDING.md §1, §12 concept 7, §15).

Silhouette: an inverted ziggurat. The fortress hangs at y ~74-110 (world), its stepped keel tapering downwards into
a forest of inverted spires and buttress pinnacles, the deepest one (under the east block) reaching down to a few
blocks above the lava. Six splayed giant chains (links 3 x 5, made of blocks) rise from gilded outriggers to rock
anchors in the ceiling, two more hold the boss drum; broken chains dangle below.

Layout, blueprint y = world y - 30 (template bottom = the lava lake floor, lava surface at y 1 = world 31):
  * approach: the landing on a rock outcrop at the west edge (waystone, guard post, braziers), reached from the lava
    shore by a stair down the outcrop's flank; a chain bridge to a pier standing in the lava; beyond the pier the
    bridge goes on toward the bastion and breaks off (a vista over the lava);
  * the climb: from the pier, a stair runs up the back of the anchor chain, a giant inclined chain whose links carry
    the treads, 18 up with a landing halfway, to the porch of the gatehouse;
  * L0 (feet 46): the gatehouse hall (a stair to L1), the prison of hanging cages (a 30-high hall over a pit that
    opens through the keel onto the lava, cages on chains, the warden's cage holds a chest), the barracks (bunks,
    basalt guard spawner, a hatch under the floor to a secret cell in the keel), the forge hall (16 high, a hearth
    of lava under a hood, blaze spawner), the east armoury with the main stair up;
  * L1 (feet 56): the gallery over the prison, the chapel (nave, altar of soul fire), the hall of the site of grace;
    from it a narrow covered bridge (compression) to the mist and the boss drum;
  * the boss drum (r 14 floor, 16 high): a ring of blackstone round a grate that looks down to the lava, pilasters
    and curtains of chain, two giant chains on its crown; past the south mist and the sealed bars, the reward vault.
Loot gradient (§15.6): landing / barracks tier 1, forge / warden's cage / secret cell tier 2, chapel tier 2-3,
vault tier 3.
"""
import math
import random

import numpy as np

from ..arch import Palette, slab, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3
from ..parts import LOOT, MOB, MOD
from .nether import (BASALT, BLACK, BS, CHIS, CPBB, GBS, GILD, LAMP, PB, PBAS, PBB, PBBS, PBBSL,
                     PBBW, PBS, PBSL, brazier, chandelier, round_tower, spike)

# the bastion's own warden: the Chained Jailer (entity/boss/ChainedJailer.java, tools/BOSSES.md section 9)
BOSS = "brasshaven:chained_jailer"

# ------------------------------------------------------------------ levels
LAVA_Y = 1                  # lava surface layer (lake floor y 0)
DECK = 28                   # feet on the landing, the bridge and the pier
L0 = 46                     # feet on the lower floor of the bastion (floor blocks y 44-45)
L1 = 56                     # feet on the upper floor (floor blocks y 54-55)
ARENA = (66, 0)             # centre of the boss drum
ARENA_R = 14                # floor radius (air r <= 14.4, wall to 16.4)
ARENA_TOP = 71              # last air layer of the drum
CEIL = 86                   # where the chains enter the ceiling anchors (template top y 89 = world 119)
HULL_C = (7, 0)             # centre of the main block (chains splay away from it)

# ------------------------------------------------------------------ materials
GOLD = "gold_block"
NB = "nether_bricks"
NBS = "nether_brick_stairs"
RNB = "red_nether_bricks"
RNBS = "red_nether_brick_stairs"
SB = "smooth_basalt"
MAG = "magma_block"
BARS = "iron_bars"
SOUL_FIRE = "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
WALLP = Palette({PBB: 6, CPBB: 2, PB: 1, "blackstone": 1}, seed=301, scale=2.6)
INNER = Palette({PB: 5, PBB: 4, CPBB: 1}, seed=302, scale=2.2)
KEEL = Palette({"blackstone": 5, "basalt[axis=y]": 3, PBB: 2, SB: 1}, seed=303, scale=3.0)
ROCK = Palette({"netherrack": 5, "blackstone": 3, "basalt[axis=y]": 2, MAG: 0.4}, seed=304, scale=3.5)
CEIL_ROCK = Palette({"blackstone": 4, "basalt[axis=y]": 3, "netherrack": 2, SB: 1}, seed=308, scale=3.0)
FLOOR = Palette({PB: 5, PBB: 3, GBS: 0.2}, seed=305, scale=1.6)
LINK = Palette({PB: 3, "blackstone": 1, PBB: 1}, seed=306, scale=2.0)
LINK2 = Palette({"polished_basalt[axis=y]": 4, SB: 1}, seed=307, scale=2.0)

# ------------------------------------------------------------------ the hull: solid volumes and carved rooms
# solid boxes (x0, x1, z0, z1, y0, y1) of the bastion's walls; every room is carved out of them, and only the
# shell of the solid plus two layers round every room is set (the rest of a thick mass stays hollow)
HULL = [
    (-30, -16, -10, 10, 44, 62),     # gatehouse
    (-16, 23, -28, 9, 44, 68),       # core: barracks + chapel (north), prison (middle)
    (-16, 23, 9, 30, 44, 63),        # forge hall (south)
    (22, 45, -14, 14, 44, 67),       # east block: armoury + hall of grace
    (46, 50, -2, 2, 55, 60),         # the covered bridge to the drum
    (-4, 11, -4, 5, 67, 74),         # the lantern over the prison
    (55, 75, 18, 32, 54, 64),        # the reward vault
    (63, 69, 14, 19, 54, 61),        # the passage from the drum to the vault
]
# rooms (name, x0, x1, z0, z1, y0, y1): air from y0 to y1, floor at y0 - 1
ROOMS = [
    ("gate", -27, -17, -9, 9, L0, 60),
    ("prison", -13, 20, -7, 7, L0, 66),
    ("lantern", -3, 10, -3, 4, 67, 74),
    ("barracks", -13, 20, -26, -10, L0, 53),
    ("chapel", -13, 20, -26, -10, L1, 68),
    ("forge", -13, 20, 10, 28, L0, 61),
    ("armoury", 25, 43, -12, 12, L0, 53),
    ("grace", 25, 43, -12, 12, L1, 65),
    ("passage", 44, 51, -1, 1, L1, 59),
    ("south", 65, 67, 14, 19, L1, 59),
    ("vault", 59, 73, 20, 30, L1, 62),
]
# doorways (x0, x1, z0, z1, y0, y1), carved through the walls
DOORS = [
    (-30, -28, -1, 1, L0, L0 + 4),        # the gate
    (-16, -14, -1, 1, L0, L0 + 3),        # gatehouse -> prison
    (-16, -14, -7, -5, L1, L1 + 3),       # gatehouse mezzanine -> prison gallery
    (0, 2, -9, -8, L0, L0 + 3),           # prison -> barracks
    (12, 14, -9, -8, L0, L0 + 3),
    (2, 4, 8, 9, L0, L0 + 3),             # prison -> forge
    (14, 16, 8, 9, L0, L0 + 3),
    (21, 24, -1, 1, L0, L0 + 3),          # prison -> armoury
    (3, 5, -9, -8, L1, L1 + 3),           # gallery -> chapel
    (15, 17, -9, -8, L1, L1 + 3),
    (21, 24, -7, -5, L1, L1 + 3),         # gallery -> hall of grace
    (27, 36, 9, 11, 54, 55),              # stairwell armoury -> hall of grace
]
PIT = (-6, 13, -2, 3)        # x0, x1, z0, z1 of the prison pit (open through the floor and the keel)
SECRET = (14, 19, -24, -20, 40, 43)       # the hidden cell in the keel under the barracks

# ------------------------------------------------------------------ the numpy grid of the hull
GX0, GX1 = -40, 92
GY0, GY1 = 24, 80
GZ0, GZ1 = -36, 36
SHAPE = (GX1 - GX0 + 1, GY1 - GY0 + 1, GZ1 - GZ0 + 1)


def _box(mask, x0, x1, z0, z1, y0, y1, val=True):
    mask[x0 - GX0:x1 - GX0 + 1, y0 - GY0:y1 - GY0 + 1, z0 - GZ0:z1 - GZ0 + 1] = val


def _cyl(mask, cx, cz, r, y0, y1, val=True, r_in=-1.0):
    xs = np.arange(GX0, GX1 + 1)[:, None]
    zs = np.arange(GZ0, GZ1 + 1)[None, :]
    d = np.hypot(xs - cx, zs - cz)
    m2 = (d <= r) & (d > r_in)
    sl = mask[:, y0 - GY0:y1 - GY0 + 1, :]
    sl[np.broadcast_to(m2[:, None, :], sl.shape)] = val


def _dilate(a):
    out = a.copy()
    n = a.shape
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                out[max(dx, 0):n[0] + min(dx, 0), max(dy, 0):n[1] + min(dy, 0), max(dz, 0):n[2] + min(dz, 0)] |= \
                    a[max(-dx, 0):n[0] + min(-dx, 0), max(-dy, 0):n[1] + min(-dy, 0), max(-dz, 0):n[2] + min(-dz, 0)]
    return out


def _shell(a):
    """Cells of `a` with at least one of their 6 neighbours outside `a`."""
    e = a.copy()
    e[1:, :, :] &= a[:-1, :, :]
    e[:-1, :, :] &= a[1:, :, :]
    e[:, 1:, :] &= a[:, :-1, :]
    e[:, :-1, :] &= a[:, 1:, :]
    e[:, :, 1:] &= a[:, :, :-1]
    e[:, :, :-1] &= a[:, :, 1:]
    e[0], e[-1] = False, False
    e[:, 0], e[:, -1] = False, False
    e[:, :, 0], e[:, :, -1] = False, False
    return a & ~e


def hull_masks():
    sol = np.zeros(SHAPE, bool)
    air = np.zeros(SHAPE, bool)
    for b in HULL:
        _box(sol, *b)
    ax, az = ARENA
    _cyl(sol, ax, az, 16.4, 54, 73)
    for (_, x0, x1, z0, z1, y0, y1) in ROOMS:
        _box(air, x0, x1, z0, z1, y0, y1)
    _cyl(air, ax, az, ARENA_R + 0.4, L1, ARENA_TOP)
    for d in DOORS:
        _box(air, *d)
    # the stairs need their headroom where they climb through the floors
    _box(air, -27, -18, -7, -5, L0, 60)
    _box(air, 27, 36, 9, 11, L0, 55)
    # the prison pit: down through the floor
    x0, x1, z0, z1 = PIT
    _box(air, x0, x1, z0, z1, 44, 45)
    return sol, air


def facade_spec(x, y, z):
    """Outer skin of the hull: a gilded string course on each floor line, darker and rougher low down."""
    if y == 45:
        return GILD
    if y == 55:
        return CHIS if (x + z) % 4 else GILD
    h = hash3(x, y, z, 311)
    if y < 50:
        return "blackstone" if h < 0.35 else (CPBB if h < 0.55 else PBB)
    return WALLP.pick(x, y, z)


def build_hull(bp):
    sol, air = hull_masks()
    near = _dilate(_dilate(air))
    walls = sol & ~air & (_shell(sol) | near)
    outer = _shell(sol) & ~near
    pts = np.argwhere(walls)
    for ix, iy, iz in pts.tolist():
        x, y, z = ix + GX0, iy + GY0, iz + GZ0
        if outer[ix, iy, iz] or not near[ix, iy, iz]:
            bp.set(x, y, z, facade_spec(x, y, z))
        else:
            bp.set(x, y, z, INNER.pick(x, y, z))
    for ix, iy, iz in np.argwhere(air).tolist():
        bp.set(ix + GX0, iy + GY0, iz + GZ0, "air")
    return sol, air


def in_sol(sol, x, y, z):
    ix, iy, iz = x - GX0, y - GY0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= iz < SHAPE[2]:
        return bool(sol[ix, iy, iz])
    return False


# ------------------------------------------------------------------ small parts
def lamp(bp, x, y, z, chain=1, soul=False):
    """A lantern hung from the ceiling block above (y + chain)."""
    for k in range(1, chain + 1):
        bp.set(x, y + k, z, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(x, y, z, hanging=True, soul=soul)


def wall_torch(bp, x, y, z, facing, soul=True):
    bp.wall_torch(x, y, z, facing, soul=soul)


def candles(bp, x, y, z, n=3):
    bp.set(x, y, z, f"candle[candles={n},lit=true,waterlogged=false]")


def flight(bp, x0, z0, direction, y0, n, width=3, spec=PBBS, fill=None, under=True):
    """Straight stair: step i at (x0 + i*dx, y0 + i, z0 + i*dz), `width` wide to the right of the climb; solid
    under each step down to y0 - 1 (or, with under=False, one block only)."""
    dx, dz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[direction]
    px, pz = -dz, dx
    for i in range(n):
        for w in range(width):
            x, z = x0 + dx * i + px * w, z0 + dz * i + pz * w
            bp.set(x, y0 + i, z, stair(spec, direction))
            lo = y0 - 1 if under else y0 + i - 1
            for y in range(lo, y0 + i):
                bp.set(x, y, z, fill.pick(x, y, z) if fill else PBB)
            for y in range(y0 + i + 1, y0 + i + 5):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, "air")


# ------------------------------------------------------------------ giant chains
def _norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n else (0.0, 0.0, 0.0)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def giant_chain(bp, p0, p1, link=6, mat=LINK, trim=GILD, broken_end=False, step=4, skip=None, mat2=None):
    """Chain of interlocking links 3 wide and `link` long from p0 to p1: each link is a ring of blocks (two rails
    and two end caps), alternately in the two planes along the chain and in two materials (dark blackstone, grey
    basalt) so each link reads. broken_end: the last link is torn open."""
    mat2 = mat2 or LINK2
    d = tuple(b - a for a, b in zip(p0, p1))
    L = math.sqrt(sum(c * c for c in d))
    u = _norm(d)
    up = (0.0, 1.0, 0.0)
    a = _cross(u, up)
    if math.sqrt(sum(c * c for c in a)) < 0.2:
        a = (1.0, 0.0, 0.0)
    a = _norm(a)
    b = _norm(_cross(a, u))
    placed = []
    k = 0
    s0 = 0.0
    while s0 < L - 1:
        s1 = min(L, s0 + link - 1)
        v = a if k % 2 == 0 else b
        last = s0 + step >= L - 1
        cells = set()
        s = s0
        while s <= s1 + 1e-6:
            for w in (-1, 1):
                if broken_end and last and w == 1 and s > (s0 + s1) / 2:
                    continue
                cells.add(tuple(int(round(p0[i] + u[i] * s + v[i] * w)) for i in range(3)))
            s += 0.5
        for se in (s0, s1):
            if broken_end and last and se == s1:
                continue
            for w in (-1, 0, 1):
                cells.add(tuple(int(round(p0[i] + u[i] * se + v[i] * w)) for i in range(3)))
        for c in cells:
            if skip and skip(*c):
                continue
            end = abs(c[0] - round(p0[0] + u[0] * s0)) + abs(c[1] - round(p0[1] + u[1] * s0)) + \
                abs(c[2] - round(p0[2] + u[2] * s0)) <= 1
            m = mat if k % 2 == 0 else mat2
            bp.set(*c, trim if (end and k % 4 == 0) else (m.pick(*c) if isinstance(m, Palette) else m))
            placed.append(c)
        s0 += step
        k += 1
    return placed


def stalactite(bp, cx, cz, y_top=89, r=4.5, depth=12, seed=0):
    """Rock hanging from the ceiling where a chain is anchored: a rough inverted cone with smaller drips round it
    and a gilded anchor plate where the chain goes in."""
    rng = random.Random(400 + seed)
    cones = [(cx, cz, r, depth)]
    for _ in range(3):
        a = rng.uniform(0, 2 * math.pi)
        cones.append((cx + math.cos(a) * (r + 0.5), cz + math.sin(a) * (r + 0.5), 1.8, rng.randint(4, 7)))
    for (px, pz, rr0, dep) in cones:
        for y in range(y_top - dep, y_top + 1):
            t = (y_top - y) / dep
            rr = rr0 * (1 - t) ** 1.3 + 0.5
            for x in range(int(px - rr0 - 2), int(px + rr0 + 3)):
                for z in range(int(pz - rr0 - 2), int(pz + rr0 + 3)):
                    n = hash3(x, y // 2, z, 320 + seed)
                    if math.hypot(x - px, z - pz) <= rr + (n - 0.5) * 1.2:
                        bp.set(x, y, z, CEIL_ROCK.pick(x, y, z))
    for x in range(int(cx) - 2, int(cx) + 3):
        for z in range(int(cz) - 2, int(cz) + 3):
            if math.hypot(x - cx, z - cz) <= 2.3 and bp.get(x, y_top - 6, z) is not None:
                bp.set(x, y_top - 6, z, GILD)


def outrigger(bp, x, y, z, ox, oz, n=4):
    """A cantilevered gilded beam out of the wall (direction ox, oz), corbelled, ending in the chain shackle."""
    for i in range(n + 1):
        xx, zz = x + ox * i, z + oz * i
        bp.set(xx, y, zz, PBB if i < n else GILD)
        bp.set(xx, y + 1, zz, CHIS if i == n else PBB)
        f = "south" if oz < 0 else "north" if oz > 0 else ("east" if ox < 0 else "west")
        if i < n:
            bp.set(xx, y - 1, zz, stair(PBBS, f, "top"))
    bp.set(x + ox * n, y + 2, z + oz * n, GILD)


# ------------------------------------------------------------------ spires and the keel
def inv_spire(bp, cx, cz, y_top, r, depth, band=GILD, seed=0):
    """Inverted spire: a solid cone hanging point-down from y_top, gilded rings every 5, a lantern at the tip."""
    for j in range(depth + 1):
        y = y_top - j
        rr = r * (1 - j / (depth + 1)) ** 0.85
        ring = (j % 5 == 4) and rr > 1.2
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.3:
                    if ring and d > rr - 0.8:
                        bp.set(x, y, z, band)
                    elif d > rr - 0.8 and hash3(x, y, z, 330 + seed) < 0.08:
                        bp.set(x, y, z, MAG)
                    else:
                        bp.set(x, y, z, KEEL.pick(x, y, z))
    tip = y_top - depth - 1
    bp.set(cx, tip, cz, GILD)
    bp.set(cx, tip - 1, cz, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(cx, tip - 2, cz, hanging=True, soul=True)


def plan_mask():
    """2D footprint of the main block (gatehouse, core, forge, east block) -> (mask, chebyshev depth)."""
    xs = np.arange(GX0, GX1 + 1)
    zs = np.arange(GZ0, GZ1 + 1)
    m = np.zeros((len(xs), len(zs)), bool)
    for (x0, x1, z0, z1, y0, y1) in HULL[:4]:
        m[x0 - GX0:x1 - GX0 + 1, z0 - GZ0:z1 - GZ0 + 1] = True
    depth = np.zeros(m.shape, int)
    cur = m.copy()
    while cur.any():
        depth += cur
        e = cur.copy()
        e[1:, :] &= cur[:-1, :]
        e[:-1, :] &= cur[1:, :]
        e[:, 1:] &= cur[:, :-1]
        e[:, :-1] &= cur[:, 1:]
        e[0, :] = e[-1, :] = False
        e[:, 0] = e[:, -1] = False
        cur = e
    return m, depth


def keel(bp):
    """The stepped keel under the main block: every 3 blocks down the footprint shrinks by 2 (an inverted
    ziggurat), solid, gilded on the lip of each step, with magma seams; the prison pit runs through it."""
    m, depth = plan_mask()
    px0, px1, pz0, pz1 = PIT
    sx0, sx1, sz0, sz1, sy0, sy1 = SECRET
    bottoms = {}
    for ix, iz in np.argwhere(m).tolist():
        x, z = ix + GX0, iz + GZ0
        d = int(depth[ix, iz])
        nsteps = min((d - 1) // 2 + 1, 5)
        bottom = 43 - 3 * nsteps + 1
        bottoms[(x, z)] = bottom
        for y in range(bottom, 44):
            if px0 <= x <= px1 and pz0 <= z <= pz1:
                continue
            if sx0 <= x <= sx1 and sz0 <= z <= sz1 and sy0 <= y <= sy1:
                continue
            j = 43 - y
            lip = (y == bottom) and d % 2 == 1
            if lip and d < 11:
                spec = GILD if hash01(x, z, 340) < 0.85 else LAMP
            elif hash3(x, y, z, 341) < 0.04:
                spec = MAG
            elif j < 2:
                spec = PBB
            else:
                spec = KEEL.pick(x, y, z)
            bp.set(x, y, z, spec)
    # the secret cell's floor and the pit lining stay keel; the pit gets a gilded collar at its mouth below
    for x in range(px0 - 1, px1 + 2):
        for z in range(pz0 - 1, pz1 + 2):
            if (x, z) in bottoms and not (px0 <= x <= px1 and pz0 <= z <= pz1):
                bp.set(x, bottoms[(x, z)], z, GILD)
    return bottoms


def drum_keel(bp):
    """Under the boss drum: a ring bowl (deep at the rim, shallow by the grate), four hanging spires."""
    ax, az = ARENA
    for x in range(ax - 17, ax + 18):
        for z in range(az - 17, az + 18):
            r = math.hypot(x - ax, z - az)
            if 7.5 <= r <= 16.4:
                dep = 2 + int((r - 7.5) * 0.8)
                for y in range(53 - dep, 54):
                    if y == 53 - dep:
                        spec = GILD if int(r) % 3 == 0 else KEEL.pick(x, y, z)
                    else:
                        spec = KEEL.pick(x, y, z)
                    bp.set(x, y, z, spec)
    for k, (a, dep) in enumerate(((45, 9), (135, 7), (225, 8), (315, 6))):
        t = math.radians(a)
        cx, cz = ax + round(math.cos(t) * 13), az + round(math.sin(t) * 13)
        inv_spire(bp, cx, cz, 44, 2.6, dep, seed=k + 10)
    # under the reward vault: a short keel and one spire
    for x in range(56, 75):
        for z in range(19, 32):
            dep = 1 + min(x - 55, 75 - x, z - 18, 32 - z) // 2
            for y in range(53 - min(dep, 5), 54):
                bp.set(x, y, z, KEEL.pick(x, y, z))
    inv_spire(bp, 66, 25, 47, 4.2, 12, seed=20)


def spires(bp, bottoms):
    """The forest of inverted spires under the keel; the dominant one under the east block."""
    def bot(x, z):
        return bottoms.get((x, z), 43)
    inv_spire(bp, 34, 0, bot(34, 0) - 1, 8.5, 22, seed=1)       # dominant: tip a few blocks above the lava
    inv_spire(bp, 4, -19, bot(4, -19) - 1, 5.5, 17, seed=2)
    inv_spire(bp, 4, 20, bot(4, 20) - 1, 5.5, 14, seed=3)
    inv_spire(bp, -23, 0, bot(-23, 0) - 1, 4.5, 11, seed=4)
    inv_spire(bp, 18, -20, bot(18, -20) - 1, 3.2, 8, seed=5)
    inv_spire(bp, -10, 21, bot(-10, 21) - 1, 3.2, 9, seed=6)
    inv_spire(bp, 40, -9, bot(40, -9) - 1, 3.0, 7, seed=7)


# ------------------------------------------------------------------ exterior: buttresses, crenels, roofs, towers
def buttress(bp, x, z, ox, oz, top, low=40, tip=8, w=3):
    """Hanging buttress against a wall face (outward ox, oz): a 3-wide pier 2 deep from the crenels down past the
    hull, ending in an inverted pinnacle; gilded at the floor lines, a pinnacle above the parapet."""
    px, pz = (1, 0) if ox == 0 else (0, 1)
    for s in range(-(w // 2), w // 2 + 1):
        for o in (1, 2):
            xx, zz = x + px * s + ox * o, z + pz * s + oz * o
            for y in range(low, top + 1):
                if y in (45, 55):
                    spec = GILD
                elif o == 2 and y == top:
                    spec = stair(PBBS, "south" if oz < 0 else "north" if oz > 0 else ("east" if ox < 0 else "west"))
                else:
                    spec = BASALT.pick(xx, y, zz) if s == 0 and o == 2 else WALLP.pick(xx, y, zz)
                bp.set(xx, y, zz, spec)
    # the inverted pinnacle under it
    cx, cz = x + ox * 1, z + oz * 1
    for j in range(1, tip + 1):
        y = low - j
        rr = 1.6 * (1 - j / (tip + 1))
        for s in range(-1, 2):
            for o in range(0, 3):
                xx, zz = x + px * s + ox * o, z + pz * s + oz * o
                if math.hypot(xx - cx - ox * 0.5, zz - cz - oz * 0.5) <= rr + 0.6:
                    bp.set(xx, y, zz, GILD if j == 3 else KEEL.pick(xx, y, zz))
    bp.set(cx + ox, low - tip - 1, cz + oz, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(cx + ox, low - tip - 2, cz + oz, hanging=True, soul=True)
    # pinnacle on top
    bp.set(x + ox, top + 1, z + oz, CHIS)
    bp.set(x + ox, top + 2, z + oz, PBBW)
    bp.set(x + ox, top + 3, z + oz, GILD)


def crenels(bp, sol, x0, x1, z0, z1, top):
    """Merlons and slabs along the edge of a box roof, skipped where a higher mass rises."""
    ring = [(x, z0) for x in range(x0, x1 + 1)] + [(x, z1) for x in range(x0, x1 + 1)] + \
           [(x0, z) for z in range(z0 + 1, z1)] + [(x1, z) for z in range(z0 + 1, z1)]
    for (x, z) in ring:
        if in_sol(sol, x, top + 1, z) or not in_sol(sol, x, top, z):
            continue
        # machicolation: a corbelled course one block out under the parapet (a shadow line round every roof)
        for (ox, oz, f) in ((0, -1, "south"), (0, 1, "north"), (-1, 0, "east"), (1, 0, "west")):
            xx, zz = x + ox, z + oz
            if (z == z0 and oz < 0) or (z == z1 and oz > 0) or (x == x0 and ox < 0) or (x == x1 and ox > 0):
                if not in_sol(sol, xx, top, zz) and bp.get(xx, top, zz) is None:
                    bp.set(xx, top - 1, zz, stair(PBBS, f, "top"))
                    bp.set(xx, top, zz, PBB if (x + z) % 4 else GILD)
        if (x + z) % 3 == 0:
            bp.set(x, top + 1, z, PBB)
            bp.set(x, top + 2, z, slab(PBBSL))
        else:
            bp.set(x, top + 1, z, PBBW)


def roofs(bp, sol):
    # the chapel: a steep roof of red nether brick over the north range, gilded ridge
    bp.gable_roof(-16, -28, 23, -9, 69, RNBS, ridge_axis="x", overhang=1, fill=RNB, ridge=GILD)
    # the chapel is open into its roof: clear the attic, tie beams and king posts carry the chandeliers
    for k in range(11):
        for x in range(-15, 23):
            for z in range(-28 + k, -8 - k):
                if bp.get(x, 69 + k, z) is None:
                    bp.set(x, 69 + k, z, "air")
    for x in (-13, -8, -3, 2, 7, 12, 17):
        for z in range(-27, -9):
            bp.set(x, 69, z, "polished_basalt[axis=z]")
        for y in range(70, 79):
            bp.set(x, y, -18, PBAS)
        bp.set(x, 68, -27, stair(PBBS, "south", "top"))
        bp.set(x, 68, -10, stair(PBBS, "north", "top"))
    # the prison terrace: crenels round the flat roof, the lantern with its spire
    crenels(bp, sol, -16, 23, -8, 9, 68)
    lx0, lx1, lz0, lz1 = -4, 11, -4, 5
    for x in range(lx0, lx1 + 1):
        for z in range(lz0, lz1 + 1):
            if x in (lx0, lx1) or z in (lz0, lz1):
                bp.set(x, 74, z, GILD if (x + z) % 2 else PBB)
    # wind openings in the lantern (high above any walkway: light and a view of the cages from outside)
    for y in range(69, 74):
        for x in (0, 1, 6, 7):
            for z in (lz0, lz1):
                bp.set(x, y, z, BARS if y < 73 else stair(PBBS, "north" if z == lz0 else "south", "top"))
        for z in (-1, 0, 2, 3):
            for x in (lx0, lx1):
                bp.set(x, y, z, BARS if y < 73 else stair(PBBS, "east" if x == lx1 else "west", "top"))
    # a steep hipped spire of nether brick (two blocks per step), open inside above the cages
    for k in range(5):
        x0, x1, z0, z1 = lx0 - 1 + k, lx1 + 1 - k, lz0 - 1 + k, lz1 + 1 - k
        y = 75 + 2 * k
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                if edge:
                    bp.set(x, y, z, GILD if k == 0 else NB)
                    f = "south" if z == z0 else "north" if z == z1 else ("east" if x == x0 else "west")
                    bp.set(x, y + 1, z, stair(NBS, f))
                elif bp.get(x, y, z) is None:
                    bp.set(x, y, z, "air")
                    bp.set(x, y + 1, z, "air")
    for x in range(lx0 + 4, lx1 - 3):
        for z in range(lz0 + 4, lz1 - 3):
            bp.set(x, 85, z, NB)
            bp.set(x, 86, z, GILD if (x + z) % 2 else PBBW)
    for y in range(86, 89):
        bp.set(3, y, 0, GILD if y == 88 else PBBW)
        bp.set(4, y, 1, GILD if y == 88 else PBBW)
    for (x, z) in ((lx0 - 1, lz0 - 1), (lx1 + 1, lz0 - 1), (lx0 - 1, lz1 + 1), (lx1 + 1, lz1 + 1)):
        for y in range(68, 77):
            bp.set(x, y, z, PBAS)
        bp.set(x, 77, z, GILD)
        bp.set(x, 78, z, LAMP)
    # the chapel's fleche on the ridge, cresting along it
    for x in range(-15, 23):
        if x % 2 == 0:
            for z in (-19, -18):
                bp.set(x, 80, z, PBBW if x % 4 else GILD)
    for x in range(3, 6):
        for z in range(-20, -16):
            edge = x in (3, 5) or z in (-20, -17)
            for y in range(79, 83):
                bp.set(x, y, z, (BARS if (y in (80, 81) and (x == 4 or z in (-19, -18))) else PBB) if edge else "air")
            bp.set(x, 83, z, slab(PBBSL))
    bp.set(4, 84, -19, GILD)
    bp.set(4, 84, -18, GILD)
    bp.set(4, 85, -18, PBBW)
    bp.set(4, 86, -18, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the gatehouse, the east block, the forge: crenellated roofs
    crenels(bp, sol, -30, -16, -10, 10, 62)
    crenels(bp, sol, 22, 45, -14, 14, 67)
    crenels(bp, sol, -16, 23, 10, 30, 63)
    crenels(bp, sol, 55, 75, 18, 32, 64)
    # forge chimneys, smoking
    for cx in (-7, 4, 15):
        cz = 27
        for y in range(64, 76):
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    if x == cx and z == cz:
                        bp.set(x, y, z, "air" if y > 64 else NB)
                    else:
                        bp.set(x, y, z, GILD if y in (70, 75) else (NB if (x + y + z) % 5 else RNB))
        bp.set(cx, 64, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if max(abs(x - cx), abs(z - cz)) == 2:
                    bp.set(x, 76, z, stair(PBBS, "south" if z < cz else "north" if z > cz else
                                           ("east" if x < cx else "west"), "top"))
    # east block corner turrets
    for (cx, cz) in ((44, -13), (44, 13)):
        for y in range(60, 72):
            for x in range(cx - 2, cx + 3):
                for z in range(cz - 2, cz + 3):
                    if math.hypot(x - cx, z - cz) <= 2.4:
                        bp.set(x, y, z, GILD if y in (66,) else WALLP.pick(x, y, z))
        spike(bp, cx, cz, 72, 2, block="blackstone", stairs=BS, steep=2, lamps=False)
    # the gatehouse towers (round, hanging below the hull into inverted spires)
    for (cx, cz) in ((-27, -13), (-27, 14)):
        round_tower(bp, cx, cz, L0, 22, 3, wall=WALLP, base=-6, solid=True, steep=2, crown_lamps=True)
        inv_spire(bp, cx, cz, 39, 4.0, 9, seed=cz)


def buttresses(bp):
    for x in (-12, -2, 9, 19):
        buttress(bp, x, -28, 0, -1, 66, low=41, tip=7 + (x % 3))
        buttress(bp, x, 30, 0, 1, 61, low=41, tip=6 + (x % 4))
    for x in (28, 38):
        buttress(bp, x, -14, 0, -1, 65, low=42, tip=6)
        buttress(bp, x, 14, 0, 1, 65, low=42, tip=7)
    for z in (-7, 7):
        buttress(bp, 45, z, 1, 0, 65, low=42, tip=8)
    for x in (58, 74):
        buttress(bp, x, 32, 0, 1, 63, low=51, tip=5)
    # the west faces of the north range and of the forge, either side of the gatehouse
    for z in (-24, -16):
        buttress(bp, -16, z, -1, 0, 66, low=41, tip=6 + (z % 3))
    for z in (16, 25):
        buttress(bp, -16, z, -1, 0, 61, low=41, tip=7 + (z % 2))


def pierce(bp, sol, x, y, z, ox, oz, h=3, w=1, fill=BARS, sill=True):
    """A window from a room outwards: walks out while inside the hull solid and opens h x w, bars on the outer
    face, a sill under it."""
    px, pz = (1, 0) if ox == 0 else (0, 1)
    xx, zz = x, z
    steps = 0
    while in_sol(sol, xx, y, zz) and steps < 6:
        for s in range(w):
            for dy in range(h):
                bp.set(xx + px * s, y + dy, zz + pz * s, "air")
        xx, zz = xx + ox, zz + oz
        steps += 1
    xx, zz = xx - ox, zz - oz
    for s in range(w):
        for dy in range(h):
            bp.set(xx + px * s, y + dy, zz + pz * s, fill)
        if sill:
            f = "south" if oz < 0 else "north" if oz > 0 else ("east" if ox < 0 else "west")
            bp.set(xx + ox + px * s, y - 1, zz + oz + pz * s, stair(PBBS, f, "top"))
        bp.set(xx + px * s, y + h, zz + pz * s, CHIS)


def windows(bp, sol):
    # barracks (north face, L0): small barred windows in pairs
    for x in (-10, -6, 1, 5, 12, 16):
        pierce(bp, sol, x, L0 + 2, -26, 0, -1, h=2)
    # chapel (north face, L1): tall lancets with red glass
    for x in (-8, -4, 4, 8, 15):
        pierce(bp, sol, x, L1 + 2, -26, 0, -1, h=6, fill="red_stained_glass_pane")
    # west faces: the barracks, the chapel and the forge look out over the landing
    for z in (-20, -12):
        pierce(bp, sol, -13, L0 + 2, z, -1, 0, h=2)
        pierce(bp, sol, -13, L1 + 2, z, -1, 0, h=6, fill="red_stained_glass_pane")
    for z in (12, 20):
        pierce(bp, sol, -13, L0 + 3, z, -1, 0, h=5, w=2)
    # forge (south face): wide openings onto the lava
    for x in (-9, -2, 10, 17):
        pierce(bp, sol, x, L0 + 3, 28, 0, 1, h=5, w=2)
    # prison: slits on the west and east of the gallery level
    for z in (-6, 5):
        pierce(bp, sol, 20, L0 + 2, z, 1, 0, h=3)
    # hall of grace (east, north, south faces): views of the drum
    for z in (-8, -4, 4, 8):
        pierce(bp, sol, 43, L1 + 2, z, 1, 0, h=4)
    for x in (31, 37):
        pierce(bp, sol, x, L1 + 2, -12, 0, -1, h=4)
        pierce(bp, sol, x, L1 + 2, 12, 0, 1, h=4)
    # armoury
    for x in (29, 33, 37, 41):
        pierce(bp, sol, x, L0 + 2, -12, 0, -1, h=2)
    for x in (39, 42):
        pierce(bp, sol, x, L0 + 2, 12, 0, 1, h=2)
    # gatehouse: slits above the gate, on north and south
    for x in (-25, -19):
        pierce(bp, sol, x, L0 + 6, -9, 0, -1, h=4)
        pierce(bp, sol, x, L0 + 6, 9, 0, 1, h=4)
    # the vault: narrow windows
    for x in (62, 70):
        pierce(bp, sol, x, L1 + 2, 30, 0, 1, h=3)


# ------------------------------------------------------------------ the chains
def chains(bp):
    """Six chains hang the main block from the ceiling (from gilded outriggers on the hull), two the drum; one torn
    chain hangs from the ceiling, three broken ones dangle under the hull."""
    anchors = [
        ((-20, 50, -10), (0, -1)), ((-20, 50, 10), (0, 1)),
        ((-6, 52, -28), (0, -1)), ((-6, 52, 30), (0, 1)),
        ((34, 52, -14), (0, -1)), ((34, 52, 14), (0, 1)),
    ]
    for k, ((x, y, z), (ox, oz)) in enumerate(anchors):
        n = 5
        outrigger(bp, x, y, z + oz, ox, oz, n=n)
        sx, sz = x + ox * (n + 1), z + oz * (n + 1)
        giant_chain(bp, (sx, y + 2, sz), (sx, CEIL + 1, sz))
        stalactite(bp, sx, sz, seed=k)
    ax, az = ARENA
    for s in (-1, 1):
        a = math.radians(60 * s)
        bx, bz = round(ax + math.cos(a) * 18), round(az + math.sin(a) * 18)
        giant_chain(bp, (bx, 76, bz), (bx, CEIL + 1, bz))
        stalactite(bp, bx, bz, seed=7 + s)
        # the shackle: a gilded beam out of the crown
        for d in range(14, 19):
            ix, iz = round(ax + math.cos(a) * d), round(az + math.sin(a) * d)
            bp.set(ix, 75, iz, GILD if d == 18 else PBB)
            bp.set(ix, 74, iz, PBB)
        bp.set(bx, 73, bz, stair(PBBS, _toward(ax, az, bx, bz), "top"))
    # broken chains: one torn from the ceiling, three hanging under the hull and the bridge
    giant_chain(bp, (-2, CEIL + 1, -46), (-2, 62, -46), broken_end=True)
    stalactite(bp, -2, -46, seed=31)
    giant_chain(bp, (20, 40, -24), (20, 22, -24), broken_end=True)
    giant_chain(bp, (12, 40, 26), (12, 27, 26), broken_end=True)
    giant_chain(bp, (52, 53, 7), (52, 36, 7), broken_end=True)


# ------------------------------------------------------------------ the lake, the outcrop, the landing, the bridge
def lake(bp):
    for x in range(-96, 86):
        for z in range(-58, 59):
            e = ((x + 5) / 87.5) ** 2 + (z / 56.0) ** 2
            e += 0.10 * (hash01(x // 6, z // 6, 350) - 0.5)
            if e > 1:
                continue
            bp.set(x, 0, z, "basalt[axis=y]" if hash01(x, z, 351) < 0.4 else "blackstone")
            bp.set(x, LAVA_Y, z, "lava[level=0]")
            if e > 0.93:
                bp.set(x, 1, z, ROCK.pick(x, 1, z))
                bp.set(x, 2, z, ROCK.pick(x, 2, z) if hash01(x, z, 352) < 0.6 else "air")
    # debris that fell from the bastion: rubble islets with a broken spire tip
    rng = random.Random(353)
    for (cx, cz, r) in ((10, 36, 3), (-24, -42, 2), (46, 22, 3), (28, -34, 2), (60, -30, 2)):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + rng.random() * 0.8:
                    for y in range(1, 2 + int((r - d) * 0.9)):
                        bp.set(x, y, z, KEEL.pick(x, y, z) if hash3(x, y, z, 354) > 0.15 else GILD)


def outcrop(bp):
    """The rock outcrop of the landing at the west edge: a craggy mesa from the lake floor to the deck."""
    cx, cz = -80, 2
    top = DECK - 1
    for x in range(cx - 16, cx + 17):
        for z in range(cz - 16, cz + 17):
            n = hash01(x // 3, z // 3, 360)
            for y in range(0, top + 1):
                r = 10.0 + (top - y) * 0.1 + (n - 0.5) * 2.4 + 1.0 * math.sin(y / 4.0 + x * 0.3)
                if math.hypot((x - cx) * 0.95, z - cz) <= r:
                    bp.set(x, y, z, ROCK.pick(x, y, z) if y < top else "blackstone")


def landing(bp):
    """The paved landing on the outcrop: guard post, waystone, braziers, the gate of the bridge, and a stair down
    the outcrop's west flank to a jetty at the lava shore."""
    f = DECK - 1
    for x in range(-88, -71):
        for z in range(-8, 12):
            if math.hypot((x + 80) / 9.0, (z - 2) / 10.5) <= 1.05:
                bp.set(x, f, z, FLOOR.pick(x, f, z) if abs(z) > 2 else (CHIS if x % 4 == 0 else PBB))
                for y in range(DECK, DECK + 4):
                    bp.set(x, y, z, "air")
    # parapet round the landing (gaps for the bridge and the west stair)
    for x in range(-89, -70):
        for z in range(-9, 13):
            r = math.hypot((x + 80) / 9.0, (z - 2) / 10.5)
            if 1.05 < r <= 1.2 and bp.get(x, f, z) is None:
                bp.set(x, f, z, PBB)
                if not (abs(z) <= 2 and x > -80) and not (-1 <= z <= 1 and x < -80):
                    bp.set(x, DECK, z, PBBW)
    # the gate of the bridge: two gilded pylons carrying the suspension chains
    for z in (-4, 4):
        for y in range(DECK, DECK + 12):
            for x in (-73, -72):
                for zz in (z, z + (1 if z > 0 else -1)):
                    bp.set(x, y, zz, GILD if y in (DECK + 5, DECK + 11) else WALLP.pick(x, y, zz))
        bp.set(-72, DECK + 12, z, CHIS)
        brazier(bp, -74, DECK, z, soul=True)
    for x in (-73, -72):
        for z in range(-3, 4):
            bp.set(x, DECK + 9, z, PBB if abs(z) < 3 else GILD)
            bp.set(x, DECK + 10, z, slab(PBBSL))
        bp.set(x, DECK + 8, 0, stair(PBBS, "north", "top"))
    lamp(bp, -72, DECK + 7, 0, chain=1, soul=True)
    # guard post: a little square tower on the north side
    gx0, gx1, gz0, gz1 = -87, -82, -7, -3
    for x in range(gx0, gx1 + 1):
        for z in range(gz0, gz1 + 1):
            for y in range(DECK, DECK + 7):
                edge = x in (gx0, gx1) or z in (gz0, gz1)
                bp.set(x, y, z, (WALLP.pick(x, y, z) if edge else "air") if y < DECK + 6 else PBB)
    bp.set(gx1 - 2, DECK, gz1, "air")
    bp.set(gx1 - 2, DECK + 1, gz1, "air")
    bp.set(gx1 - 2, DECK + 2, gz1, CHIS)
    for x in range(gx0 - 1, gx1 + 2):
        for z in range(gz0 - 1, gz1 + 2):
            if x in (gx0 - 1, gx1 + 1) or z in (gz0 - 1, gz1 + 1):
                bp.set(x, DECK + 6, z, stair(PBBS, "south" if z < gz0 else "north" if z > gz1 else
                                             ("east" if x < gx0 else "west"), "top"))
                if (x + z) % 2 == 0:
                    bp.set(x, DECK + 7, z, PBBW)
    bp.barrel(gx0 + 1, DECK, gz0 + 1, "up", loot=LOOT + "chained_barracks")
    bp.set(gx0 + 2, DECK, gz0 + 1, "smithing_table")
    lamp(bp, gx0 + 2, DECK + 4, gz0 + 2, chain=1, soul=True)
    # the waystone on its gilded dais, facing the bastion
    wx, wz = -79, 6
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            bp.set(x, f, z, GILD if (x + z) % 2 else CHIS)
    bp.set(wx, DECK, wz, MOD["waystone"])
    brazier(bp, -84, DECK, 8, soul=False, big=True)
    brazier(bp, -76, DECK, -6, soul=True)
    # the stair down the west flank to the jetty (two flights with a landing; the jetty at the lava's edge)
    sx = -90
    _west_stair(bp)


def _west_stair(bp):
    """Switchback down the outcrop's west flank: from the landing (feet DECK) to the jetty (feet 3)."""
    # flight A: from the landing west edge (x -89) descending south along x -92..-90
    top = DECK - 1                                          # landing floor y 27
    # landing gap at x -89..-88, z -1..1 (west) -> platform x -92..-90, z -1..1 at floor 27
    for x in range(-92, -87):
        for z in range(-1, 2):
            bp.set(x, top, z, PBB)
            for y in range(top - 3, top):
                bp.set(x, y, z, ROCK.pick(x, y, z))
            for y in range(DECK, DECK + 4):
                bp.set(x, y, z, "air")
    for z in (-2, 2):
        for x in range(-92, -88):
            bp.set(x, DECK, z, PBBW)
    for z in range(-1, 2):
        bp.set(-93, DECK, z, PBBW)
    # flight A descends south: steps at z = 2 + i, y = 26 - i  (climbing north)
    yA = top
    for i in range(12):
        z = 2 + i
        y = top - 1 - i
        for x in range(-92, -89):
            bp.set(x, y, z, stair(PBBS, "north"))
            for yy in range(y - 3, y):
                bp.set(x, yy, z, ROCK.pick(x, yy, z))
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
        bp.set(-93, y + 1, z, PBBW)
    yA = top - 12                                           # last step y 15 at z 13
    # landing B at z 14..16, floor y 14
    yb = yA - 1
    for x in range(-92, -86):
        for z in range(14, 17):
            bp.set(x, yb, z, PBB)
            for yy in range(yb - 3, yb):
                bp.set(x, yy, z, ROCK.pick(x, yy, z))
            for yy in range(yb + 1, yb + 5):
                bp.set(x, yy, z, "air")
    for x in range(-93, -85):
        bp.set(x, yb + 1, 17, PBBW)
    bp.set(-93, yb + 1, 14, PBBW)
    bp.set(-93, yb + 1, 15, PBBW)
    bp.set(-93, yb + 1, 16, PBBW)
    bp.lantern(-93, yb + 2, 16)
    # flight C descends east along z 14..16: steps at x = -86 + i, y = yb - 1 - i (climbing west)
    for i in range(11):
        x = -86 + i
        y = yb - 1 - i
        for z in range(14, 17):
            bp.set(x, y, z, stair(PBBS, "west"))
            for yy in range(max(0, y - 3), y):
                bp.set(x, yy, z, ROCK.pick(x, yy, z))
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
        bp.set(x, y + 1, 17, PBBW)
    # the jetty at the lava's edge, floor y 2 (feet 3): a basalt landing stage
    yj = yb - 12
    for x in range(-75, -69):
        for z in range(13, 19):
            bp.set(x, yj, z, PB if (x + z) % 3 else GBS)
            for yy in range(0, yj):
                bp.set(x, yy, z, BASALT.pick(x, yy, z))
            for yy in range(yj + 1, yj + 5):
                bp.set(x, yy, z, "air")
    for x in range(-75, -69):
        bp.set(x, yj + 1, 19, PBBW)
    brazier(bp, -70, yj + 1, 18, soul=True)


def bridge(bp):
    """The chain bridge from the landing to the pier, and beyond the pier the broken span."""
    f = DECK - 1
    # the pier: a blackstone pier standing in the lava, its tower carrying the cables
    for x in range(-60, -54):
        for z in range(-4, 11):
            for y in range(0, f):
                if 0 <= z <= 6 and y < 13 + 7 * math.sqrt(max(0.0, 1 - ((z - 3) / 3.6) ** 2)):
                    continue                                    # the pier stands on two legs over an arch
                edge = x in (-60, -55) or z in (-4, 10)
                if edge and y % 6 == 5:
                    spec = GILD
                elif edge and (z - 3) % 4 == 0 and 4 <= y < f - 3 and x in (-60, -55):
                    spec = BASALT.pick(x, y, z)
                else:
                    spec = KEEL.pick(x, y, z) if y < f - 1 else PBB
                bp.set(x, y, z, spec)
            bp.set(x, f, z, FLOOR.pick(x, f, z))
            for y in range(DECK, DECK + 4):
                bp.set(x, y, z, "air")
    # cutwaters
    for z in (-5, -6, 11, 12):
        k = abs(z) - (4 if z < 0 else 10)
        for x in range(-59 + k, -55 - k + 1):
            for y in range(0, f - 1 - k):
                bp.set(x, y, z, KEEL.pick(x, y, z))
    # pier tower on the north part: the cable saddles, a lamp
    for x in range(-60, -54):
        for z in (-4, -3):
            for y in range(DECK, DECK + 12):
                if -59 <= x <= -56 and y < DECK + 4 and z == -3:
                    continue
                bp.set(x, y, z, GILD if y in (DECK + 5, DECK + 11) else WALLP.pick(x, y, z))
    for x in range(-60, -54):
        bp.set(x, DECK + 12, -4, PBBW if x % 2 else CHIS)
    # pier parapets (gaps: bridge west and east at z -2..2, the chain stair east at z 6..8)
    for z in range(-2, 11):
        if not (-2 <= z <= 2):
            bp.set(-60, DECK, z, PBBW)
        if not (-2 <= z <= 2 or 6 <= z <= 8):
            bp.set(-55, DECK, z, PBBW)
    for x in range(-60, -54):
        bp.set(x, DECK, 10, PBBW)
    brazier(bp, -59, DECK, 9, soul=True)
    lamp(bp, -57, DECK + 3, -2, chain=1, soul=True)
    # the span landing -> pier: crimson planks between blackstone curbs, walls with lamps
    for x in range(-71, -60):
        for z in range(-2, 3):
            bp.set(x, f, z, PBB if abs(z) == 2 else ("crimson_planks" if x % 3 else "dark_oak_planks"))
            for y in range(DECK, DECK + 4):
                bp.set(x, y, z, "air")
        bp.set(x, DECK, -3, LAMP if x % 5 == 0 else PBBW)
        bp.set(x, DECK, 3, LAMP if x % 5 == 0 else PBBW)
        bp.set(x, f, -3, PBB)
        bp.set(x, f, 3, PBB)
        if x % 2 == 0:
            for z in range(-3, 4):
                bp.set(x, f - 1, z, stair(PBBS, "north", "top") if abs(z) < 3 else PBBW)
    # suspension cables: giant chains from the pylons sagging to the deck and up to the pier tower
    for z in (-4, 4):
        zz = z if z < 0 else z
        pts = [(-72, DECK + 11, zz), (-66, DECK + 3, zz), (-57, DECK + 11, -4 if z < 0 else 4)]
        giant_chain(bp, pts[0], pts[1], step=3)
        if z < 0:
            giant_chain(bp, pts[1], (-58, DECK + 10, -4), step=3)
        else:
            giant_chain(bp, pts[1], (-60, DECK + 6, 5), step=3)
    # the broken span beyond the pier: it once reached a gate under the bastion; the deck ends in a jagged edge,
    # a railing closes it (a vista over the lava, BUILDING §15.5)
    for x in range(-54, -40):
        brk = x > -45
        for z in range(-2, 3):
            if brk and hash01(x, z, 370) < (x + 45) / 5.0:
                continue
            bp.set(x, f, z, PBB if abs(z) == 2 else ("crimson_planks" if x % 3 else "dark_oak_planks"))
            for y in range(DECK, DECK + 4):
                bp.set(x, y, z, "air")
        if not brk:
            bp.set(x, DECK, -3, LAMP if x % 5 == 0 else PBBW)
            bp.set(x, DECK, 3, LAMP if x % 5 == 0 else PBBW)
            bp.set(x, f, -3, PBB)
            bp.set(x, f, 3, PBB)
            if x % 2 == 0:
                for z in range(-3, 4):
                    bp.set(x, f - 1, z, stair(PBBS, "north", "top") if abs(z) < 3 else PBBW)
    # the railing that closes the broken end
    for z in range(-3, 4):
        bp.set(-45, DECK, z, PBBW)
        bp.set(-45, f, z, PBB)
    for x in range(-49, -45):
        for z in range(-2, 3):
            bp.set(x, f, z, PBB if abs(z) == 2 else "crimson_planks")
    for x in range(-48, -45):
        for z in (-3, 3):
            bp.set(x, DECK, z, PBBW)
            bp.set(x, f, z, PBB)
    brazier(bp, -46, DECK, 0, soul=True)
    # torn deck pieces and a dangling cable beyond the edge
    for (x, z) in ((-43, -2), (-43, 1), (-42, 2), (-41, -1)):
        bp.set(x, f, z, "crimson_planks")
    giant_chain(bp, (-44, DECK - 1, 3), (-43, 10, 4), broken_end=True)
    giant_chain(bp, (-57, DECK + 11, -4), (-44, DECK + 1, -4), broken_end=True)


def chain_climb(bp):
    """From the pier up the anchor chain to the porch of the gatehouse: two flights of nine (3 wide) on the back
    of a giant inclined chain, a landing halfway, walls with lanterns, the porch on gilded corbels."""
    z0 = 6                                                  # treads z 6..8
    # flight 1: x -54..-46, treads y 28..36 ; landing x -45..-43 floor 36 ; flight 2: x -42..-34, treads 37..45
    for i in range(9):
        x = -54 + i
        y = DECK + i
        for z in range(z0, z0 + 3):
            bp.set(x, y, z, stair(PBBS, "east"))
            bp.set(x, y - 1, z, PBB)
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
        bp.set(x, y + 1, z0 - 1, PBBW if i % 4 else LAMP)
        bp.set(x, y + 1, z0 + 3, PBBW if i % 4 else LAMP)
        bp.set(x, y, z0 - 1, PBB)
        bp.set(x, y, z0 + 3, PBB)
    yl = DECK + 8
    for x in range(-45, -42):
        for z in range(z0 - 1, z0 + 4):
            bp.set(x, yl, z, GILD if z in (z0 - 1, z0 + 3) else CHIS)
            bp.set(x, yl - 1, z, PBB)
            if z0 <= z <= z0 + 2:
                for yy in range(yl + 1, yl + 5):
                    bp.set(x, yy, z, "air")
        bp.set(x, yl + 1, z0 - 1, PBBW)
        bp.set(x, yl + 1, z0 + 3, PBBW)
    bp.set(-44, yl + 2, z0 - 1, "soul_lantern[hanging=false,waterlogged=false]")
    bp.set(-44, yl + 2, z0 + 3, "soul_lantern[hanging=false,waterlogged=false]")
    for i in range(9):
        x = -42 + i
        y = yl + 1 + i
        for z in range(z0, z0 + 3):
            bp.set(x, y, z, stair(PBBS, "east"))
            bp.set(x, y - 1, z, PBB)
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
        bp.set(x, y + 1, z0 - 1, PBBW if i % 4 else LAMP)
        bp.set(x, y + 1, z0 + 3, PBBW if i % 4 else LAMP)
        bp.set(x, y, z0 - 1, PBB)
        bp.set(x, y, z0 + 3, PBB)
    # the giant chain under the treads: from the pier's anchor block to the gatehouse's gilded shackle
    def skip(x, y, z):
        return z0 <= z <= z0 + 2 and y >= _tread(x)
    giant_chain(bp, (-55, DECK - 4, 7), (-31, L0 - 5, 7), link=5, step=3, skip=skip)
    for y in range(DECK - 6, DECK - 1):
        for z in range(6, 9):
            bp.set(-56, y, z, GILD if y == DECK - 4 else PBB)
    # the porch of the gatehouse: x -33..-31, z -3..9 at floor 45, on gilded corbels, walls round it
    for x in range(-33, -30):
        for z in range(-3, 10):
            bp.set(x, L0 - 1, z, CHIS if (x + z) % 2 else PBB)
            bp.set(x, L0 - 2, z, stair(PBBS, "east", "top") if x == -33 else PBB)
            for yy in range(L0, L0 + 5):
                if bp.get(x, yy, z) not in (None, "minecraft:air") and x >= -30:
                    continue
                bp.set(x, yy, z, "air")
    for z in range(-4, 11):
        if not (6 <= z <= 8):
            bp.set(-34, L0, z, PBBW if z % 3 else LAMP)
            bp.set(-34, L0 - 1, z, PBB)
    for x in range(-34, -30):
        bp.set(x, L0, -4, PBBW)
        bp.set(x, L0, 10, PBBW)
        bp.set(x, L0 - 1, -4, PBB)
        bp.set(x, L0 - 1, 10, PBB)
    for z in (-3, 3, 9):
        bp.set(-31, L0 - 3, z, PBB)
        bp.set(-31, L0 - 4, z, stair(PBBS, "east", "top"))
        bp.set(-32, L0 - 3, z, stair(PBBS, "east", "top"))


def _tread(x):
    """Tread height of the chain stair at x (used to keep the chain under the treads)."""
    if x < -54:
        return DECK - 1
    if x <= -46:
        return DECK + (x + 54)
    if x <= -43:
        return DECK + 8
    if x <= -34:
        return DECK + 9 + (x + 42)
    return L0 - 1


# ------------------------------------------------------------------ interiors
def floors(bp):
    """Floors of the rooms (layer y0 - 1): darker field, a lighter processional strip along the main path."""
    for name, x0, x1, z0, z1, y0, y1 in ROOMS:
        if name == "lantern":
            continue
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                spec = FLOOR.pick(x, y0 - 1, z)
                if name in ("prison", "armoury", "grace", "passage", "gate") and abs(z) <= 1:
                    spec = CHIS if x % 4 == 0 else PB
                if name == "chapel" and z in (-18, -17, -19):
                    spec = RNB if x % 3 else GILD
                if name == "forge" and (x + z) % 5 == 0:
                    spec = SB
                if name == "grace" and 27 <= x <= 36 and 9 <= z <= 11:
                    continue                                # the stairwell
                bp.set(x, y0 - 1, z, spec)
    # doors' sills
    for (x0, x1, z0, z1, y0, y1) in DOORS[:-1]:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, y0 - 1, z, CHIS)
                bp.set(x, y1 + 1, z, GILD if y0 == L0 and (x0 == -30) else CHIS)


def gatehouse(bp):
    # the colossal portal on the west face (BUILDING §3: the gate is the wicket inside it): a pointed arch 9 wide
    # and 15 high recessed one block, gilded voussoirs, a tympanum with the chained sun
    for z in range(-5, 6):
        top = 54 + int(round(6.5 * max(0.0, 1 - (abs(z) / 5.2) ** 1.5)))
        for y in range(L0, top + 2):
            if abs(z) <= 4 and y < top:
                if bp.get(-30, y, z) != "minecraft:air":
                    bp.set(-30, y, z, "air")
                if y > L0 + 4 or abs(z) > 1:
                    bp.set(-29, y, z, CHIS if (y + z) % 3 else PBB)
            elif y == top or (abs(z) == 5 and y < top):
                bp.set(-30, y, z, GILD if (y + z) % 2 else CHIS)
            else:
                bp.set(-30, y, z, PBB)
                if y == top + 1:
                    bp.set(-31, y, z, stair(PBBS, "east", "top"))
    for (y, z) in ((56, 0), (55, -1), (55, 1), (57, 0), (56, -1), (56, 1), (55, 0)):
        bp.set(-29, y, z, GOLD)
    for (y, z) in ((58, 0), (56, -2), (56, 2), (54, 0), (57, -2), (57, 2), (55, -2), (55, 2)):
        bp.set(-29, y, z, GILD)
    for z in (-3, 3):
        for y in range(L0 + 6, 53):
            bp.set(-29, y, z, "iron_chain[axis=y,waterlogged=false]" if y < 52 else GILD)
    # the gate (the wicket): a gilded frame, a raised portcullis of bars above the opening
    for z in range(-2, 3):
        for y in range(L0, L0 + 6):
            if abs(z) == 2 or y == L0 + 5:
                bp.set(-31, y, z, GILD if y == L0 + 5 or y % 2 == 0 else CHIS)
    for z in range(-1, 2):
        bp.set(-31, L0 + 5, z, GOLD if z == 0 else GILD)
        bp.set(-29, L0 + 5, z, BARS)
    # the stair up to the mezzanine, along the north wall
    for i in range(10):
        x = -27 + i
        for z in range(-7, -4):
            bp.set(x, L0 + i, z, stair(PBBS, "east"))
            for y in range(L0 - 1, L0 + i):
                bp.set(x, y, z, BLACK.pick(x, y, z))
        bp.set(x, L0 + i + 1, -4, PBBW)
        bp.set(x, L0 + i, -4, PBB)
    for z in range(-7, -4):
        bp.set(-17, L1 - 1, z, CHIS)
        for y in range(L0, L1 - 1):
            bp.set(-17, y, z, BLACK.pick(-17, y, z))
    bp.set(-17, L1, -4, PBBW)
    # braziers and banners by the gate, a chandelier
    brazier(bp, -26, L0, -2, soul=True, big=True)
    brazier(bp, -26, L0, 3, soul=True, big=True)
    chandelier(bp, -22, 60, 2, soul=True, drop=4)
    for z in (5, 8):
        bp.set(-27, L0 + 4, z, "black_wall_banner[facing=east]")
        bp.set(-17, L0 + 4, z, "red_wall_banner[facing=west]")
    # guard table
    bp.set(-20, L0, 6, PBB)
    bp.set(-20, L0 + 1, 6, slab(PBSL, "bottom"))
    bp.set(-21, L0, 6, stair(PBS, "east"))
    bp.set(-19, L0, 6, stair(PBS, "west"))
    bp.set(-20, L0 + 2, 6, "soul_lantern[hanging=false,waterlogged=false]")
    for z in (-8, 8):
        wall_torch(bp, -18, L0 + 3, z, "west")


def prison(bp):
    """The prison of hanging cages: walkways round a pit open to the lava, the gallery above on corbels, the
    lantern's beams carrying the cages on chains."""
    px0, px1, pz0, pz1 = PIT
    # railing round the pit (a gap at the warden's cage)
    for x in range(px0 - 1, px1 + 2):
        for z in (pz0 - 1, pz1 + 1):
            if (x, z) == (6, pz1 + 1):
                continue
            bp.set(x, L0, z, PBBW if (x + z) % 5 else LAMP)
    for z in range(pz0, pz1 + 1):
        for x in (px0 - 1, px1 + 1):
            bp.set(x, L0, z, PBBW)
    # gallery at L1 along the north wall (z -7..-5), its railing and corbels
    for x in range(-13, 21):
        for z in range(-7, -4):
            bp.set(x, L1 - 1, z, FLOOR.pick(x, L1 - 1, z))
        bp.set(x, L1, -4, PBBW if x % 6 else LAMP)
        bp.set(x, L1 - 1, -4, PBB)
        if x % 4 == 0:
            bp.set(x, L1 - 2, -4, stair(PBBS, "south", "top"))
    # beams across the lantern carrying the cages
    for x in (-2, 3, 6, 9):
        for z in range(-4, 6):
            bp.set(x, 75, z, "polished_basalt[axis=z]")
    cages = [(-2, 0, 50, 75), (3, 2, 38, 75), (9, 0, 46, 75), (3, -1, 58, 75), (-2, 2, 31, 75), (9, 2, 33, 75)]
    for (cx, cz, yb, yt) in cages:
        cage(bp, cx, cz, yb)
        for y in range(yb + 4, yt):
            bp.set(cx, y, cz, "iron_chain[axis=y,waterlogged=false]")
    # the warden's cage at the south edge of the pit, level with the walkway: a chest behind the open bars
    for x in range(5, 8):
        for z in range(1, 4):
            bp.set(x, L0 - 1, z, PBB)
            bp.set(x, L0 + 3, z, PBB)
            for y in range(L0, L0 + 3):
                if (x, z) == (6, 2):
                    continue
                if (x, z) == (6, 3) and y < L0 + 2:
                    bp.set(x, y, z, "air")
                    continue
                bp.set(x, y, z, BARS)
        bp.set(x, L0 - 2, 2, stair(PBBS, "north", "top"))
    bp.chest(6, L0, 2, "south", loot=LOOT + "chained_forge")
    for y in range(L0 + 4, 75):
        bp.set(6, y, 2, "iron_chain[axis=y,waterlogged=false]")
    # spawner on the east walkway, skulls and soul braziers at the corners
    bp.spawner(18, L0, 6, "minecraft:wither_skeleton")
    for (x, z) in ((-12, -6), (-12, 6), (19, -6)):
        bp.set(x, L0, z, PBBW)
        bp.set(x, L0 + 1, z, SOUL_FIRE)
    for (x, z) in ((-10, 6), (16, -6)):
        bp.set(x, L0, z, "wither_skeleton_skull[rotation=4]")
    # chandeliers from the gallery ceiling, soul lanterns over the walkways
    for x in (-9, 16):
        chandelier(bp, x, 66, 4, soul=True, drop=6)
    for x in (-10, 0, 10, 18):
        lamp(bp, x, 52, -6, chain=2, soul=True)
    for z in (-6, 6):
        wall_torch(bp, -13, L0 + 3, z, "east")


def cage(bp, cx, cz, yb):
    """Gibbet cage 3 x 3, 4 high: blackstone floor and lid, bars round an empty cell (a skull inside)."""
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            bp.set(x, yb, z, PBB if (x + z) % 2 else PB)
            bp.set(x, yb + 4, z, PBB)
            for y in range(yb + 1, yb + 4):
                if x == cx and z == cz:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, BARS)
    bp.set(cx, yb + 1, cz, "skeleton_skull[rotation=%d]" % ((cx + cz) % 16))
    bp.set(cx, yb - 1, cz, GILD)
    if yb > 32:
        bp.lantern(cx, yb - 2, cz, hanging=True, soul=True)


def barracks(bp):
    """Bunks along the north wall, a long table with benches, weapon racks, the guard captain's chest; a hatch
    under the floor to the secret cell in the keel."""
    for x in range(-12, 17, 3):
        if x != -3:
            bp.bed(x, L0, -25, "north", color="black")
    for x in range(-12, 17, 3):
        if x == -3:
            continue
        if x + 1 <= 20:
            bp.set(x + 1, L0, -26, "barrel[facing=up,open=false]")
    # the long table
    for x in range(-8, 13):
        bp.set(x, L0, -17, PBB if x in (-8, 12) else "dark_oak_planks")
        if x % 3 == 0:
            bp.set(x, L0 + 1, -17, "candle[candles=2,lit=true,waterlogged=false]")
        if x not in (-8, 12):
            bp.set(x, L0, -18, stair("dark_oak_stairs", "south"))
        if x not in (-8, 12):
            bp.set(x, L0, -16, stair("dark_oak_stairs", "north"))
    # weapon racks on the south wall: grindstones, fences with lanterns
    for x in (-11, -7, 9, 18):
        bp.set(x, L0, -11, "grindstone[face=floor,facing=north]")
    bp.set(19, L0, -11, "smithing_table")
    bp.chest(-12, L0, -12, "east", loot=LOOT + "chained_barracks")
    bp.spawner(4, L0, -13, MOB["basalt_guard"])
    for x in (-6, 4, 14):
        chandelier(bp, x, 53, -19, soul=False, drop=3)
    for z in (-22, -14):
        wall_torch(bp, -13, L0 + 3, z, "east", soul=False)
        wall_torch(bp, 20, L0 + 3, z, "west", soul=False)
    # the hatch to the secret cell (a trapdoor in the floor) and the ladder down into the keel
    sx0, sx1, sz0, sz1, sy0, sy1 = SECRET
    bp.set(19, L0 - 1, -24, "dark_oak_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(19, L0 - 2, -24, "ladder[facing=south,waterlogged=false]")
    bp.ladder(19, sy0, -24, sy1, "south")
    bp.set(19, L0 - 2, -25, PBB)
    for y in range(sy0, sy1 + 1):
        bp.set(19, y, -25, PBB)


def secret_cell(bp):
    sx0, sx1, sz0, sz1, sy0, sy1 = SECRET
    for x in range(sx0, sx1 + 1):
        for z in range(sz0, sz1 + 1):
            bp.set(x, sy0 - 1, z, PB)
            for y in range(sy0, sy1 + 1):
                if bp.get(x, y, z) is None or "ladder" not in bp.get(x, y, z):
                    bp.set(x, y, z, "air")
    bp.chest(14, sy0, -22, "east", loot=LOOT + "chained_forge")
    bp.set(15, sy0, -24, "barrel[facing=up,open=false]")
    bp.set(14, sy0, -24, GOLD)
    bp.lantern(16, sy0, -21, soul=True)
    bp.set(17, sy0, -20, "skeleton_skull[rotation=8]")


def chapel(bp):
    """The chapel of the chained god: a nave of pews facing the east altar of soul fire, gilded reredos, red
    lancets on the north side, chandeliers."""
    for x in range(-10, 14, 2):
        for z in list(range(-25, -19)) + list(range(-16, -11)):
            bp.set(x, L1, z, stair("blackstone_stairs", "west"))
    # the altar on a dais at the east end
    for x in range(16, 21):
        for z in range(-24, -11):
            bp.set(x, L1 - 1, z, GILD if (x + z) % 2 else CHIS)
    for z in range(-23, -13):
        if z not in (-19, -18, -17):
            bp.set(16, L1, z, stair(PBBS, "west"))
    for z in range(-20, -15):
        bp.set(18, L1, z, GILD if z in (-20, -16) else CHIS)
        bp.set(18, L1 + 1, z, slab(PBBSL, "bottom") if z not in (-18,) else SOUL_FIRE)
    bp.chest(19, L1, -18, "west", loot=LOOT + "chained_chapel")
    # reredos: a gilded wall with a chained figure of gold
    for z in range(-24, -11):
        for y in range(L1, 69):
            bp.set(20, y, z, GILD if (y + z) % 4 == 0 else (CHIS if abs(z + 18) <= 2 else PBB))
    for y in range(L1 + 2, L1 + 9):
        bp.set(20, y, -18, GOLD)
    for y in (L1 + 6,):
        for z in (-20, -19, -17, -16):
            bp.set(20, y, z, GOLD)
    for z in (-21, -15):
        for y in range(L1 + 5, 67):
            bp.set(19, y, z, "iron_chain[axis=y,waterlogged=false]")
        bp.set(19, 67, z, stair(PBBS, "east", "top"))
    for z in (-22, -14):
        bp.set(19, L1, z, PBBW)
        bp.set(19, L1 + 1, z, SOUL_FIRE)
    for x in (-8, 2, 12):
        chandelier(bp, x, 68, -18, soul=True, drop=6)
    for x in (-12, -2, 8):
        wall_torch(bp, x, L1 + 3, -11, "north")
    bp.set(-13, L1 + 4, -18, "black_wall_banner[facing=east]")


def forge(bp):
    """The forge hall: the great hearth of lava in a railed basin under a gilded hood and the central chimney,
    anvils, blast furnaces, the quenching trough, racks of iron, a blaze spawner on its plinth."""
    hx0, hx1, hz0, hz1 = 1, 7, 17, 21
    for x in range(hx0 - 1, hx1 + 2):
        for z in range(hz0 - 1, hz1 + 2):
            edge = x in (hx0 - 1, hx1 + 1) or z in (hz0 - 1, hz1 + 1)
            bp.set(x, L0 - 1, z, MAG if not edge else CHIS)
            if edge:
                bp.set(x, L0, z, PBB)
                bp.set(x, L0 + 1, z, PBBW)
            else:
                bp.set(x, L0, z, "lava[level=0]")
                bp.set(x, L0 - 1, z, PBB)
    # the hood: a stepped gilded funnel from y 56 up to the roof, open into the middle chimney (x 4, z 27 is the
    # chimney; the hood vents through a flue along the ceiling)
    for k, y in enumerate(range(55, 62)):
        r = 5 - k // 2
        for x in range(4 - r, 4 + r + 1):
            for z in range(19 - r, 19 + r + 1):
                if max(abs(x - 4), abs(z - 19)) == r:
                    bp.set(x, y, z, GILD if k == 0 else (NB if k % 2 else RNB))
    for y in range(51, 55):
        for (x, z) in ((hx0 - 1, hz0 - 1), (hx1 + 1, hz0 - 1), (hx0 - 1, hz1 + 1), (hx1 + 1, hz1 + 1)):
            bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")
    for (x, z) in ((hx0 - 1, hz0 - 1), (hx1 + 1, hz0 - 1), (hx0 - 1, hz1 + 1), (hx1 + 1, hz1 + 1)):
        for y in range(L0 + 2, 51):
            bp.set(x, y, z, PBBW)
    # anvils, blast furnaces, smithing tables round the hearth; the trough of lava in cauldrons
    bf_on, bf_off = "blast_furnace[facing=south,lit=true]", "blast_furnace[facing=south,lit=false]"
    for (x, z, b) in ((-2, 16, "anvil[facing=east]"), (-2, 22, "chipped_anvil[facing=east]"),
                      (10, 16, "anvil[facing=west]"), (10, 22, "smithing_table"),
                      (-11, 12, bf_on), (-10, 12, bf_on), (-9, 12, bf_off), (18, 12, bf_on),
                      (17, 12, "furnace[facing=south,lit=true]"), (-12, 20, "lava_cauldron"),
                      (-12, 21, "lava_cauldron"), (-12, 22, "lava_cauldron"),
                      (19, 25, "grindstone[face=floor,facing=west]"),
                      (12, 27, "iron_block"), (13, 27, "iron_block"), (12, 26, "iron_block")):
        bp.set(x, L0, z, b)
    for x in range(-11, -7):
        bp.set(x, L0, 27, "iron_block" if x % 2 else "raw_iron_block")
    bp.chest(19, L0, 27, "west", loot=LOOT + "chained_forge")
    # the overhead crane: a basalt beam across the hall carrying a ladle (a lava cauldron) on its chains
    for x in range(-13, 21):
        bp.set(x, 59, 14, "polished_basalt[axis=x]")
        if x % 6 == 0:
            bp.set(x, 58, 14, stair(PBBS, "south", "top"))
    for y in range(53, 59):
        bp.set(-5, y, 14, "iron_chain[axis=y,waterlogged=false]")
    bp.set(-5, 52, 14, "lava_cauldron")
    # racks of chains and bars along the north wall, coal (blackstone) heaps, barrels of ore
    for x in range(-12, 0, 2):
        for y in range(L0, L0 + 3):
            bp.set(x, y, 10, BARS)
        bp.set(x, L0 + 3, 10, PBB)
    for (x, z) in ((-11, 26), (-10, 26), (-11, 25), (-11, 27), (-10, 27)):
        bp.set(x, L0, z, "coal_block" if (x + z) % 2 else "blackstone")
    for z in (16, 18):
        bp.set(-12, L0, z, "barrel[facing=east,open=false]")
        bp.set(-12, L0 + 1, z, "barrel[facing=up,open=false]")
    # the blaze on a plinth in the south-east corner (fed by the hearth's heat)
    for x in range(14, 17):
        for z in range(22, 25):
            bp.set(x, L0, z, CHIS if (x, z) != (15, 23) else PBB)
    bp.spawner(15, L0 + 1, 23, "minecraft:blaze")
    for x in (-8, 14):
        chandelier(bp, x, 61, 15, soul=False, drop=5)
    for z in (14, 24):
        wall_torch(bp, -13, L0 + 3, z, "east", soul=False)
        wall_torch(bp, 20, L0 + 3, z, "west", soul=False)


def armoury(bp):
    """The east armoury and its stair up to the hall of grace."""
    for i in range(10):
        x = 27 + i
        for z in range(9, 12):
            bp.set(x, L0 + i, z, stair(PBBS, "east"))
            for y in range(L0 - 1, L0 + i):
                bp.set(x, y, z, BLACK.pick(x, y, z))
        if i < 7:
            bp.set(x, L0 + i + 1, 8, PBBW)
        if i < 7:
            bp.set(x, L0 + i, 8, PBB)
    # the stairwell's railing on the upper floor
    for x in range(26, 37):
        bp.set(x, L1, 8, PBBW if x % 4 else LAMP)
        bp.set(x, L1 - 1, 8, PBB)
    for z in range(9, 12):
        bp.set(26, L1, z, PBBW)
        bp.set(26, L1 - 1, z, PBB)
    for z in range(-12, 7, 3):
        bp.set(43, L0, z, "barrel[facing=west,open=false]")
        if z % 2 == 0:
            bp.set(43, L0 + 1, z, "barrel[facing=west,open=false]")
    for x in (28, 32, 36, 40):
        bp.set(x, L0, -12, "grindstone[face=floor,facing=south]" if x % 8 else "anvil[facing=east]")
    for x in (30, 38):
        lamp(bp, x, 51, 0, chain=2, soul=False)
    for z in (-6, 4):
        wall_torch(bp, 25, L0 + 3, z, "east", soul=False)


def grace(bp):
    """The hall of the site of grace: the waystone on a gilded dais with soul braziers, benches, the east windows
    looking onto the drum; the covered bridge beyond."""
    cx, cz = 35, -3
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            bp.set(x, L1 - 1, z, GILD if (x + z) % 2 else CHIS)
    bp.set(cx, L1 - 1, cz, GOLD)
    bp.set(cx, L1, cz, MOD["waystone"])
    for (x, z) in ((cx - 3, cz - 3), (cx + 3, cz - 3), (cx - 3, cz + 3), (cx + 3, cz + 3)):
        bp.set(x, L1, z, PBBW)
        bp.set(x, L1 + 1, z, SOUL_FIRE)
    for z in range(-10, -6):
        bp.set(27, L1, z, stair("blackstone_stairs", "west"))
        bp.set(42, L1, z, stair("blackstone_stairs", "east"))
    chandelier(bp, cx, 65, cz, soul=True, drop=4)
    for x in (28, 40):
        lamp(bp, x, 62, 3, chain=3, soul=True)
    # the covered bridge to the drum: bars on its sides, lanterns
    for x in range(46, 51):
        if x % 2 == 0:
            for y in (L1 + 1, L1 + 2):
                bp.set(x, y, -2, BARS)
                bp.set(x, y, 2, BARS)
    for x in (46, 49):
        bp.set(x, L1 + 3, 0, "soul_lantern[hanging=true,waterlogged=false]")
    for x in range(46, 51):
        for z in (-3, 3):
            bp.set(x, L1 - 1, z, stair(PBBS, "north" if z > 0 else "south", "top"))
        bp.set(x, 61, 0, GILD if x % 3 == 0 else PBB)


def arena(bp, sol):
    """The boss drum: floor rings round the grate over the lava, pilasters and chain curtains, the crown."""
    ax, az = ARENA
    fy = L1 - 1
    for x in range(ax - ARENA_R - 1, ax + ARENA_R + 2):
        for z in range(az - ARENA_R - 1, az + ARENA_R + 2):
            d = math.hypot(x - ax, z - az)
            if d > ARENA_R + 0.4:
                continue
            if d <= 1.5:
                spec = CHIS
            elif d <= 6.4:
                spec = BARS
            elif d <= 7.4:
                spec = GILD
            elif 11.5 <= d < 12.4:
                spec = GILD if (x + z) % 2 else GBS
            elif abs(z - az) <= 1 and x < ax:
                spec = CHIS if x % 3 else PB
            else:
                spec = PBB if int(d) % 2 else PB
            bp.set(x, fy, z, spec)
            if d <= 6.4:
                bp.set(x, fy - 1, z, "air")
    # nothing under the grate: the void to the lava (the drum keel is a ring)
    # pilasters: eight basalt columns with gilded capitals against the wall
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = ax + round(math.cos(a) * 14), az + round(math.sin(a) * 14)
        for y in range(L1, ARENA_TOP + 1):
            bp.set(x, y, z, GILD if y in (L1, ARENA_TOP - 2) else PBAS)
        bp.set(x, ARENA_TOP - 1, z, CHIS)
        bp.set(x, ARENA_TOP, z, CHIS)
    # chain curtains hanging from the ceiling between the pilasters, soul lanterns at their ends
    for k in range(8):
        a = math.radians(k * 45)
        for rr in (12, 13):
            x, z = ax + round(math.cos(a) * rr), az + round(math.sin(a) * rr)
            n = 5 + (k * 3 + rr) % 4
            for y in range(ARENA_TOP - n + 1, ARENA_TOP + 1):
                bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")
            bp.lantern(x, ARENA_TOP - n, z, hanging=True, soul=True)
    # the ceiling: a gilded ring and spokes; a great chandelier over the grate
    for x in range(ax - 15, ax + 16):
        for z in range(az - 15, az + 16):
            d = math.hypot(x - ax, z - az)
            if d <= 14.4:
                spoke = abs(x - ax) <= 0 or abs(z - az) <= 0
                bp.set(x, ARENA_TOP + 1, z, GILD if (spoke or 9.5 <= d < 10.4) else PBB)
    chandelier(bp, ax, ARENA_TOP, az, soul=True, drop=5)
    # slit windows round the wall
    for k in range(12):
        a = math.radians(k * 30 + 15)
        if abs(math.degrees(a) % 360 - 180) < 20 or abs(math.degrees(a) % 360 - 90) < 20:
            continue
        x, z = ax + round(math.cos(a) * 16), az + round(math.sin(a) * 16)
        xi, zi = ax + round(math.cos(a) * 15), az + round(math.sin(a) * 15)
        for y in range(L1 + 4, L1 + 9):
            bp.set(xi, y, zi, "air")
            bp.set(x, y, z, BARS)
    # outside: the crown: corbels, a shallow cone of nether brick, gilded ribs, the spire
    for x in range(ax - 18, ax + 19):
        for z in range(az - 18, az + 19):
            d = math.hypot(x - ax, z - az)
            if 16.4 < d <= 17.4:
                bp.set(x, 72, z, stair(PBBS, _toward(ax, az, x, z), "top"))
                bp.set(x, 73, z, PBB)
                if int(math.degrees(math.atan2(z - az, x - ax)) + 360) % 12 < 5:
                    bp.set(x, 74, z, PBBW)
    for x in range(ax - 17, ax + 18):
        for z in range(az - 17, az + 18):
            d = math.hypot(x - ax, z - az)
            if d <= 16.4:
                y = 74 + int((16.4 - d) * 0.45)
                ang = math.degrees(math.atan2(z - az, x - ax)) % 45
                rib = ang < 4 or ang > 41
                bp.set(x, y, z, GILD if rib else (NB if hash01(x, z, 380) < 0.7 else RNB))
                for yy in range(74, y):
                    bp.set(x, yy, z, NB)
    for y in range(81, 85):
        bp.set(ax, y, az, GILD if y == 84 else PBBW)
    # ribs round the drum, hanging below it into gilded pinnacles
    for k in range(12):
        deg = k * 30 + 15
        if min(abs(deg - 180), abs(deg - 90)) < 20:
            continue
        a = math.radians(deg)
        for rr in (17, 18):
            x, z = ax + round(math.cos(a) * rr), az + round(math.sin(a) * rr)
            lo = 48 if rr == 17 else 50
            for y in range(lo, 72):
                bp.set(x, y, z, GILD if y in (55, 64) else (BASALT.pick(x, y, z) if rr == 18 else PBB))
            bp.set(x, 72, z, stair(PBBS, _toward(ax, az, x, z), "top") if rr == 18 else PBB)
        x, z = ax + round(math.cos(a) * 17), az + round(math.sin(a) * 17)
        bp.set(x, 47, z, GILD)
        bp.set(x, 46, z, "iron_chain[axis=y,waterlogged=false]")
        bp.lantern(x, 45, z, hanging=True, soul=True)
    bp.boss_seal(ax, fy, az, BOSS, ARENA_R - 1)
    # mist on both doors; the vault behind sealed bars that open when the boss falls
    bp.mist(51, L1, -1, 51, L1 + 3, 1)
    bp.mist(65, L1, 15, 67, L1 + 3, 15)
    for x in (65, 66, 67):
        for y in range(L1, L1 + 4):
            bp.set(x, y, 19, MOD["vault_bars"])
    for x in (64, 68):
        for y in range(L1, L1 + 4):
            bp.set(x, y, 15, GILD if y == L1 + 3 else CHIS)
    for z in (-2, 2):
        for y in range(L1, L1 + 4):
            bp.set(51, y, z, GILD if y == L1 + 3 else CHIS)


def _toward(cx, cz, x, z):
    dx, dz = cx - x, cz - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def vault(bp):
    """The reward vault: the chained god's hoard, two chests, gold, a throne of gilded blackstone."""
    for x in range(59, 74):
        for z in range(20, 31):
            if hash01(x, z, 390) < 0.12 and abs(x - 66) > 2 and z > 22:
                bp.set(x, L1, z, GOLD if hash01(x, z, 391) < 0.6 else "raw_gold_block")
    for x in range(64, 69):
        for z in range(27, 31):
            bp.set(x, L1, z, GBS if z < 29 else GILD)
    bp.set(66, L1 + 1, 29, stair(PBBS, "north"))
    bp.set(65, L1 + 1, 29, GILD)
    bp.set(67, L1 + 1, 29, GILD)
    for y in range(L1 + 2, L1 + 5):
        bp.set(66, y, 30, GOLD if y == L1 + 4 else GBS)
    bp.chest(61, L1, 28, "east", loot=LOOT + "chained_vault")
    bp.chest(71, L1, 28, "west", loot=LOOT + "chained_vault")
    for (x, z) in ((60, 21), (72, 21)):
        bp.set(x, L1, z, PBBW)
        bp.set(x, L1 + 1, z, SOUL_FIRE)
    chandelier(bp, 66, 62, 24, soul=False, drop=3)
    # heaps of the hoard along the side walls, candles on them; chains of the god hang over the throne
    for (x0, x1) in ((59, 61), (71, 73)):
        for x in range(x0, x1 + 1):
            for z in range(21, 27):
                h = 1 + int(hash01(x, z, 392) * 2.2)
                if (x in (61, 71)) and h > 1:
                    h = 1
                for y in range(L1, L1 + h):
                    bp.set(x, y, z, (GOLD, "raw_gold_block", GBS, GILD)[int(hash3(x, y, z, 393) * 4)])
                if hash01(x, z, 394) < 0.3:
                    candles(bp, x, L1 + h, z, 1 + int(hash01(x, z, 395) * 3))
    for z in (28, 30):
        for y in range(L1 + 2, 63):
            bp.set(64 if z == 28 else 68, y, z, "iron_chain[axis=y,waterlogged=false]")
    for x in range(63, 70):
        bp.set(x, L1 - 1, 24 + (x % 2), GILD)
    for x in (59, 73):
        wall_torch(bp, x, L1 + 3, 26, "east" if x == 59 else "west", soul=False)


# ------------------------------------------------------------------ the whole site
def chained_bastion(bp):
    lake(bp)
    outcrop(bp)
    landing(bp)
    bridge(bp)
    sol, air = build_hull(bp)
    bottoms = keel(bp)
    spires(bp, bottoms)
    drum_keel(bp)
    floors(bp)
    buttresses(bp)
    roofs(bp, sol)
    windows(bp, sol)
    gatehouse(bp)
    prison(bp)
    barracks(bp)
    secret_cell(bp)
    chapel(bp)
    forge(bp)
    armoury(bp)
    grace(bp)
    arena(bp, sol)
    vault(bp)
    chain_climb(bp)
    chains(bp)


# interior and approach shots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("landing", (-82, DECK, -1), (-31, L0 + 3, 0)),
    ("chain_climb", (-44, DECK + 9, 7), (-31, L0 + 4, 4)),
    ("prison", (-10, L0, -6), (9, 49, 0)),
    ("forge", (-8, L0, 24), (19, L0 + 4, 13)),
    ("chapel", (-11, L1, -18), (19, L1 + 4, -18)),
    ("grace", (27, L1, 6), (40, L1 + 3, -6)),
    ("arena", (54, L1, 0), (78, L1 + 6, 0)),
]


register(StructureDef(
    "chained_bastion", "nether", ["nether_wastes", "basalt_deltas", "crimson_forest", "soul_sand_valley"],
    [Piece("bastion", chained_bastion, views=VIEWS)],
    spacing=36, separation=12, adaptation="none", height=("absolute", 30), processors="none", max_distance=116,
    ground=L0 - 1,
    spawns=[("minecraft:wither_skeleton", 8, 1, 2), (MOB["basalt_guard"], 6, 1, 2), ("minecraft:blaze", 3, 1, 1)],
    title_fr="Bastion enchaîné", title_en="Chained Bastion"))
