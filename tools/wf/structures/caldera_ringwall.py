"""Caldera Ringwall (Le Rempart de la caldeira): a ring of curtain walls and towers on the rim of a crater lake, with
the keep perched on a rock needle in the middle of the lake, joined to the rim by one long bridge. Colossal tier
(tools/BUILDING.md §1, §12 concept 1, §10 Stormveil template, §15), mountain biomes.

Silhouette (one noun phrase, §15.1): a dark volcanic crater crowned by a pale sixteen-sided ring of walls with red
roofed towers, and in its middle a black needle carrying an overhanging castle and one tall keep with a green
copper spire.

Layout, ground y = 0, x east, z south; the massif is centred on 0, 0, the lake and the needle on (LCX, LCZ):
  * the massif: an outer slope (rock faces at the top, grass and talus lower down) from the foot (r ~113) up to the
    flat rim (y 44, feet 45); inside, a sheer crater wall drops to a gravel strand and the lake (water top y 12);
  * the curtain: a 16-sided wall 5 thick on the rim (walk feet 59) with towers at every vertex: four stair towers
    on the diagonals where cross walls split the bailey into four wards, the great tower of the hub (north), the
    east bastion projecting down the slope, the west tower, round open turrets between them, and on the south the
    gatehouse built into the outer slope;
  * the approach: a camp and a waystone at the foot (south-east), a road along the foot of the slope to the
    barbican, the gatehouse portal (9 x 14 with a wicket), the gate hall where the guardians wait, and the grand
    stair: three flights round a 45-high stair hall and a flying bridge across it to the gate court on the rim
    (site of grace, the reveal of the needle through the north door);
  * the side route (§10.1): from the barbican a path cut into the outer slope climbs round the west flank to the
    berm under the west wall and a breach into the west ward;
  * the main route: gate court -> south-east tower -> the wall-walk past the open turrets and the east bastion's gun
    deck -> north-east tower -> the hub (north ward: great tower, great hall, kitchen, site of grace, an overlook
    over the crater). Optional: the east ward (barracks, the bastion armoury), the west ward (ruined chapel, the
    broken west bridge);
  * the undercroft cut into the crater wall under the hub (feet 33): the cistern hall, the prison and its hidden
    ossuary, the bridge gallery whose arches look at the needle, and the dock stair down to the strand;
  * the bridge (feet 33, 41 long, two piers in the lake and a gate tower) to the needle's gate; inside the needle a
    newel stair climbs 45 blocks (guard room, windows over the lake) to the keep's lower room;
  * the summit (feet 84): the keep hall (site of grace), a covered passage (compression) and the mist, the arena:
    an open court 33 across under the sky on corbels over the void; the vault turret behind sealed bars on the far
    side and its balcony, the way down: a leap into the lake;
  * shortcuts (§10.4): the south-east tower's iron door (lever on the east ward side) and the south-west tower's
    (lever inside, from the west ward) back to the gate court; the undercroft ladder up through a hatch in the
    great tower; the water gate (iron door, lever on the strand side) from the strand up to the gate court; after
    the boss, the leap into the lake, the strand and the water gate.
Loot gradient (§15.6): camp, ramparts, barracks tier 1; armoury, great hall, undercroft, needle, keep tier 2; the
hidden ossuary tier 2-3; the vault tier 3.
Height budget: the keep's finial stands ~148 above the ground layer, so it stays under the build limit wherever the
ground is below y ~170 (meadows, groves, slopes, stony peaks, windswept hills).
"""
import math

import numpy as np

from ..arch import boulder, spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3, is_air, pointed_arch
from ..parts import LOOT, MOD

# the ringwall's own lord: the Castellan of the Caldera (entity/boss/CalderaCastellan.java, tools/BOSSES.md)
BOSS = "brasshaven:caldera_castellan"
MOB_KNIGHT = "brasshaven:skeleton_knight"
MOB_GARGOYLE = "brasshaven:gargoyle"
MOB_CRAWLER = "brasshaven:crypt_crawler"
MOB_SKELETON = "minecraft:skeleton"

# ------------------------------------------------------------------ dimensions
RIM = 44                   # rim top block (bailey feet 45)
FR = RIM + 1
FW = 59                    # wall-walk feet (walk floor block y 58)
LAKE = 12                  # water surface block = strand top block
FS = LAKE + 1              # strand feet
LCX, LCZ = 0, 6            # crater lake and needle centre
R_LAKE = 54.0
R_EDGE = 59.0              # crater edge (top of the inner cliff)
R_WALL = 82.0              # curtain centreline
R_TOP = 87.0               # outer edge of the flat rim
R_FOOT = 113.0             # foot of the outer slope (mean)
FB = 33                    # undercroft, bridge and needle gate feet
FL = 78                    # keep lower room feet
FT = 84                    # summit feet (keep hall, passage, arena)
NEEDLE_TOP = 77            # last rock layer of the needle
AC = (0, 19)               # arena centre
AR = 16                    # arena floor radius
KX0, KZ0, KX1, KZ1 = -8, -20, 8, -4      # keep outer walls
K_FLOORS = (FT, 94, 104, 114, 124)       # keep feet levels (124 = the roof walk)
GH = (-16, 82, 16, 105)                  # gatehouse outer box x0, z0, x1, z1
GF = 9                                   # gate hall feet

AX0, AX1 = -124, 124
AZ0, AZ1 = -124, 124
AY = 92

# materials
SB, CR, MO, CH = "stone_bricks", "cracked_stone_bricks", "mossy_stone_bricks", "chiseled_stone_bricks"
SB_ST, SB_SL, SB_W = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
PA, PA_ST, PA_SL = "polished_andesite", "polished_andesite_stairs", "polished_andesite_slab"
DB, CDB, CD = "deepslate_bricks", "cracked_deepslate_bricks", "cobbled_deepslate"
DT = "deepslate_tiles"
ROOF, ROOF_ST, ROOF_SL = ("brasshaven:crimson_roof_tiles", "brasshaven:crimson_roof_tile_stairs",
                          "brasshaven:crimson_roof_tile_slab")
SLATE, SLATE_ST, SLATE_SL = ("brasshaven:slate_roof_tiles", "brasshaven:slate_roof_tile_stairs",
                             "brasshaven:slate_roof_tile_slab")
COP, COP_ST = "waxed_oxidized_cut_copper", "waxed_oxidized_cut_copper_stairs"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ vector noise (numpy)
def _hash(ix, iz, seed):
    n = ((ix * 73856093) ^ (iz * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def nvnoise(x, z, scale, seed):
    fx, fz = np.asarray(x, float) / scale, np.asarray(z, float) / scale
    ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _hash(ix, iz, seed), _hash(ix + 1, iz, seed)
    c, d = _hash(ix, iz + 1, seed), _hash(ix + 1, iz + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def nfbm(x, z, scale, seed):
    return 0.6 * nvnoise(x, z, scale, seed) + 0.3 * nvnoise(x, z, scale / 2.3, seed + 7) + \
        0.1 * nvnoise(x, z, scale / 5.1, seed + 13)


# ------------------------------------------------------------------ geometry
def polar(theta, r):
    """Point at compass bearing theta (degrees, clockwise from north) and radius r round 0, 0."""
    t = math.radians(theta)
    return r * math.sin(t), -r * math.cos(t)


def bearing(x, z):
    return math.degrees(math.atan2(x, -z)) % 360


def seg_dist(px, pz, a, b):
    """(distance, t in 0..1, closest x, closest z) of point p to segment ab."""
    vx, vz = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vz * vz or 1e-9
    t = max(0.0, min(1.0, ((px - a[0]) * vx + (pz - a[1]) * vz) / L2))
    cx, cz = a[0] + vx * t, a[1] + vz * t
    return math.hypot(px - cx, pz - cz), t, cx, cz


def capsule_cells(a, b, hw):
    """Cells within hw of segment ab: (x, z, distance, outward (away from 0, 0) sign, u along)."""
    L = math.dist(a, b)
    for x in range(int(math.floor(min(a[0], b[0]) - hw)) - 1, int(math.ceil(max(a[0], b[0]) + hw)) + 2):
        for z in range(int(math.floor(min(a[1], b[1]) - hw)) - 1, int(math.ceil(max(a[1], b[1]) + hw)) + 2):
            d, t, cx, cz = seg_dist(x, z, a, b)
            if d <= hw:
                out = 1 if math.hypot(x, z) >= math.hypot(cx, cz) else -1
                yield x, z, d, out, t * L


def disc(cx, cz, r):
    ir = int(r) + 1
    for x in range(int(cx) - ir, int(cx) + ir + 1):
        for z in range(int(cz) - ir, int(cz) + ir + 1):
            d = math.hypot(x - cx, z - cz)
            if d <= r:
                yield x, z, d


def inward(dx, dz):
    """Facing of a roof stair at offset (dx, dz) from a centre: its high side towards the centre."""
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def outward(dx, dz):
    return OPP[inward(dx, dz)]


# ------------------------------------------------------------------ the grid
XS = np.arange(AX0, AX1 + 1)
ZS = np.arange(AZ0, AZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")
JIT = nfbm(GX, GZ, 9.0, 31)


def ai(x, y, z):
    return x - AX0, y, z - AZ0


def inside(x, z):
    return AX0 <= x <= AX1 and AZ0 <= z <= AZ1


def massif_heights():
    """Top block y of every column of the massif (< 0: none), the radius from 0, 0 and from the lake centre."""
    d = np.hypot(GX, GZ)
    dd = np.maximum(d, 1e-6)
    ux, uz = GX / dd, GZ / dd
    rf = R_FOOT + 9.0 * (nfbm(ux * 60, uz * 60, 22.0, 11) - 0.5) + 3.0 * (nvnoise(ux * 160, uz * 160, 7.0, 12) - 0.5)
    t = np.clip((d - R_TOP) / (rf - R_TOP), 0.0, 1.0)
    h = RIM * (1 - t) ** 1.5
    bump = np.sin(np.pi * t)
    h = h + bump * (6.0 * (nvnoise(ux * 260, uz * 260, 5.0, 13) - 0.5) + 4.0 * (nfbm(GX, GZ, 13.0, 14) - 0.5))
    h = np.where(d <= R_TOP, RIM, h)
    tt = np.clip((d - rf) / 8.0, 0, 1)
    talus = 2.2 * (1 - tt) + 2.4 * (nfbm(GX, GZ, 6.0, 15) - 0.5) - 0.6
    h = np.where(d > rf, talus, h)
    dl = np.hypot(GX - LCX, GZ - LCZ)
    edge = R_EDGE + 2.4 * (nfbm(GX, GZ, 8.0, 16) - 0.5)
    h = np.where(dl < edge, LAKE, h)
    bed = np.where(dl < R_LAKE - 6, LAKE - 4, LAKE - 3)
    h = np.where(dl < R_LAKE, bed, h)
    return np.floor(h + 0.5).astype(int), d, dl, edge


HMAP, DIST, DLAKE, EDGE = massif_heights()
SLOPE = np.hypot(*np.gradient(HMAP.astype(float)))


def hmap(x, z):
    if not inside(x, z):
        return -1
    i, _, k = ai(x, 0, z)
    return int(HMAP[i, k])


NEEDLE = ((0, 25.0, 1.0, 6.0), (12, 23.0, 1.0, 6.0), (22, 19.0, 1.05, 6.5), (34, 16.5, 1.1, 7.0),
          (50, 12.8, 1.2, 8.0), (64, 13.6, 1.3, 9.0), (NEEDLE_TOP, 15.2, 1.4, 10.0))


def needle_shape(y):
    ys = [n[0] for n in NEEDLE]
    return (float(np.interp(y, ys, [n[1] for n in NEEDLE])), float(np.interp(y, ys, [n[2] for n in NEEDLE])),
            float(np.interp(y, ys, [n[3] for n in NEEDLE])))


# ------------------------------------------------------------------ paths cut in the slope (half-block ramps)
class Path:
    """A walkway along a polyline of (x, z, feet) nodes, ``width`` wide. Its floor rises in half blocks (full block /
    bottom slab), so it climbs without steps whatever its direction: ``cells`` maps (x, z) -> floor height in half
    blocks (s even: full block at s/2 - 1; odd: slab at s // 2); ``edge`` is the parapet ring around it."""

    def __init__(self, nodes, width):
        self.nodes = nodes
        hw = width / 2.0
        lens = [0.0]
        for i in range(1, len(nodes)):
            lens.append(lens[-1] + math.dist(nodes[i - 1][:2], nodes[i][:2]))
        self.length = lens[-1]
        self.cells, self.edge = {}, {}
        x0 = int(min(n[0] for n in nodes) - hw - 3)
        x1 = int(max(n[0] for n in nodes) + hw + 3)
        z0 = int(min(n[1] for n in nodes) - hw - 3)
        z1 = int(max(n[1] for n in nodes) + hw + 3)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                best = None
                for i in range(len(nodes) - 1):
                    a, b = nodes[i], nodes[i + 1]
                    d, t, _, _ = seg_dist(x, z, a, b)
                    if best is None or d < best[0] - 1e-9:
                        best = (d, i, t)
                d, i, t = best
                f = nodes[i][2] + (nodes[i + 1][2] - nodes[i][2]) * t
                s = int(math.floor(2 * f + 0.5))
                if d <= hw:
                    self.cells[(x, z)] = s
                elif d <= hw + 1.05:
                    self.edge[(x, z)] = s
        for c in self.cells:
            self.edge.pop(c, None)

    @staticmethod
    def top_y(s):
        """y of the floor block (full block or slab) of a floor height s."""
        return s // 2 - 1 if s % 2 == 0 else s // 2

    @staticmethod
    def feet(s):
        return (s + 1) // 2


def approach_path():
    nodes = []
    for th, r, f in ((141, 113.5, 1.0), (147, 114.0, 1.0), (153, 114.0, 2.0), (159, 113.5, 3.5),
                     (165, 113.5, 5.0), (170, 113.0, 6.5)):
        x, z = polar(th, r)
        nodes.append((x, z, f))
    nodes += [(16.0, 111.0, 8.0), (13.0, 110.0, 9.0)]
    return Path(nodes, 4)


def side_path():
    """The side route: from the barbican's west side round the west flank to the berm and the breach."""
    def r_of(f):
        return R_TOP + 27.0 * (1 - ((f + 2.5) / 44.0) ** (2 / 3)) - 0.5

    nodes = [(-13.0, 110.0, 9.0), (-18.0, 109.5, 9.5)]
    for th, f in ((193, 11.0), (201, 14.0), (210, 17.5), (219, 21.0), (228, 25.0), (237, 29.0), (246, 33.0),
                  (255, 37.0), (263, 41.0), (270, 44.0)):
        x, z = polar(th, r_of(f))
        nodes.append((x, z, f))
    for th in (274, 279, 282):
        x, z = polar(th, 86.6)
        nodes.append((x, z, 45.0))
    return Path(nodes, 3)


APPROACH = approach_path()
SIDE = side_path()
BREACH_TH = 282.0


# ------------------------------------------------------------------ newel stairs
def newel(x0, z0, k, f0, flights, start, cw=True):
    """Square newel stair (outer side 6 + k): 3 x 3 corner landings, flights of <= k steps 3 wide along the sides,
    round a solid k x k core. ``start``: corner index (0 NW, 1 NE, 2 SE, 3 SW) of the bottom landing at feet f0.
    Returns (cells {(x, z): (feet, facing or None, flight index)}, core box, top corner index, top feet)."""
    corner = {0: (x0, z0), 1: (x0 + 3 + k, z0), 2: (x0 + 3 + k, z0 + 3 + k), 3: (x0, z0 + 3 + k)}
    # side from corner c to the next one clockwise: (origin of u, u direction, across direction, facing)
    cells = {}

    def put_corner(c, f, idx):
        cx, cz = corner[c]
        for dx in range(3):
            for dz in range(3):
                cells[(cx + dx, cz + dz)] = (f, None, idx)

    c, f = start, f0
    put_corner(c, f, -1)
    for i, n in enumerate(flights):
        nxt = (c + 1) % 4 if cw else (c - 1) % 4
        ax, az = corner[c]
        bx, bz = corner[nxt]
        if az == bz:                       # along x
            sx = 1 if bx > ax else -1
            facing = "east" if sx > 0 else "west"
            for u in range(k):
                x = (ax + 3 + u) if sx > 0 else (ax - 1 - u)
                ff = f + min(u + 1, n)
                for dz in range(3):
                    cells[(x, az + dz)] = (ff, facing if u < n else None, i)
        else:                              # along z
            sz = 1 if bz > az else -1
            facing = "south" if sz > 0 else "north"
            for u in range(k):
                z = (az + 3 + u) if sz > 0 else (az - 1 - u)
                ff = f + min(u + 1, n)
                for dx in range(3):
                    cells[(ax + dx, z)] = (ff, facing if u < n else None, i)
        f += n
        c = nxt
        put_corner(c, f, i)
    return cells, (x0 + 3, z0 + 3, x0 + 2 + k, z0 + 2 + k), c, f


def newel_laps(bp, x0, z0, k, f0, flights, start, cw=True, **kw):
    """A newel stair of any number of flights, written three flights at a time (a fourth would land on the corner it
    started from in the same cell map): each part reuses the columns of the one below, higher up.
    Returns (cells of the last part, core, top corner, top feet)."""
    c, f = start, f0
    for i in range(0, len(flights), 3):
        cells, core, c, f1 = newel(x0, z0, k, f, flights[i:i + 3], c, cw)
        write_newel(bp, cells, core, f, **kw)
        f = f1
    return cells, core, c, f


def write_newel(bp, cells, core, f0, tread="stone_brick", fill="stone_bricks", clear=4, core_spec=None,
                lamps=True):
    """Blocks of a newel stair: air above every cell first, then treads (stairs or landing floors) 2 thick, and solid
    masonry under the low cells so no crawl gap is left under them; the core pillar."""
    top = max(f for f, _, _ in cells.values())
    for (x, z), (f, fc, _) in cells.items():
        for y in range(f, f + clear):
            bp.set(x, y, z, "air")
    for (x, z), (f, fc, _) in cells.items():
        if fc:
            bp.set(x, f - 1, z, stair(tread + "_stairs", fc))
        else:
            bp.set(x, f - 1, z, fill if hash01(x, z, 7) < 0.8 else PA)
        if f - 2 - f0 < 3:
            for y in range(f0 - 1, f - 1):
                bp.set(x, y, z, fill)
        else:
            bp.set(x, f - 2, z, fill)
    cx0, cz0, cx1, cz1 = core
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(f0 - 1, top + clear):
                edge = x in (cx0, cx1) or z in (cz0, cz1)
                bp.set(x, y, z, (core_spec or SB) if edge or y < f0 + 1 else (core_spec or SB))
    if lamps:
        # a lantern on the core at every corner landing (on a bracket slab)
        seen = set()
        for (x, z), (f, fc, i) in cells.items():
            if fc is None and (f, i) not in seen and (x in (cx0 - 1, cx1 + 1) and z in (cz0 - 1, cz1 + 1)):
                seen.add((f, i))
                bp.set(x, f + 3, z, "air")
                hx = cx0 if x < cx0 else cx1
                hz = cz0 if z < cz0 else cz1
                bp.set(hx, f + 2, hz, "chiseled_stone_bricks")


# ------------------------------------------------------------------ rock plan
class Plan:
    """Rock mask (S), carved air (K), masonry supports (M), floors and the columns under them (SUP: never carved)."""

    def __init__(self):
        shape = (len(XS), AY, len(ZS))
        self.S = np.zeros(shape, bool)
        self.K = np.zeros(shape, bool)
        self.M = np.zeros(shape, bool)
        self.SUP = np.zeros(shape, bool)
        self.NEEDLE = np.zeros(shape, bool)

    def rock(self):
        Y = np.arange(AY)[None, :, None]
        self.S |= Y <= HMAP[:, None, :]
        for y in range(0, NEEDLE_TOP + 1):
            rx, kz, cz = needle_shape(y)
            rz = rx * kz
            th = np.arctan2(GX, GZ - cz)
            n = nfbm(GX * 1.0, GZ * 1.0 + y * 0.45, 5.0, 21)
            rib = 1.4 * (0.5 + 0.5 * np.cos(th * 7 + y * 0.06)) ** 4
            ledge = (((y + 5 * nvnoise(GX, GZ, 11.0, 23)) % 9) < 1.4) * 0.9
            e = np.hypot(GX / rx, (GZ - cz) / rz)
            m = e < 1 + (2.4 * (n - 0.5) + rib + ledge) / rx
            self.S[:, y, :] |= m
            self.NEEDLE[:, y, :] |= m

    def carve(self, x0, y0, z0, x1, y1, z1):
        a = ai(min(x0, x1), max(0, min(y0, y1)), min(z0, z1))
        b = ai(max(x0, x1), min(AY - 1, max(y0, y1)), max(z0, z1))
        self.K[a[0]:b[0] + 1, a[1]:b[1] + 1, a[2]:b[2] + 1] = True

    def fill(self, x0, y0, z0, x1, y1, z1, sup=True):
        a = ai(min(x0, x1), max(0, min(y0, y1)), min(z0, z1))
        b = ai(max(x0, x1), min(AY - 1, max(y0, y1)), max(z0, z1))
        self.S[a[0]:b[0] + 1, a[1]:b[1] + 1, a[2]:b[2] + 1] = True
        if sup:
            self.SUP[a[0]:b[0] + 1, a[1]:b[1] + 1, a[2]:b[2] + 1] = True

    def support(self, x, z, ytop, mason):
        """Solid from ytop down to the rock (or the ground); masonry in the 3 blocks under the top on outer edges."""
        if not inside(x, z):
            return
        i, _, k = ai(x, 0, z)
        y, j = ytop, 0
        while y >= 0:
            if self.S[i, y, k] and j:
                break
            self.S[i, y, k] = True
            self.SUP[i, y, k] = True
            if mason and 0 < j <= 3:
                self.M[i, y, k] = True
            j += 1
            y -= 1

    def column_top(self, x, z):
        if not inside(x, z):
            return -1
        i, _, k = ai(x, 0, z)
        col = np.flatnonzero(self.S[i, :, k])
        return int(col[-1]) if len(col) else -1

    def path(self, p):
        for (x, z), s in p.cells.items():
            yt = Path.top_y(s)
            self.support(x, z, yt, False)
            self.carve(x, yt + 1, z, x, yt + 4, z)
        for (x, z), s in p.edge.items():
            f = Path.feet(s)
            top = self.column_top(x, z)
            if top >= f + 2:
                continue                       # the uphill side: the cut rock face stays
            self.support(x, z, f - 1, True)
            self.carve(x, f + 1, z, x, f + 4, z)

    def carves(self):
        x0, z0, x1, z1 = GH
        self.carve(x0, GF, z0, x1, AY - 1, z1)                     # the gatehouse box
        self.carve(-13, GF, 106, 13, 30, 116)                      # over the barbican
        self.carve(18, 0, 92, 24, 0, 92)                           # (no-op anchor)
        # water gate: newel shaft under the gate court and its passage out to the strand
        self.carve(6, FS - 1, 66, 14, FR + 3, 74)
        self.carve(12, FS, 58, 14, FS + 3, 65)
        # the undercroft (feet FB): bridge gallery, cistern hall, prison, ossuary, the stair from the hub
        self.carve(-15, FB, -60, 12, FB + 5, -49)
        self.carve(-11, FB, -74, 11, FB + 6, -61)
        self.carve(-25, FB, -73, -12, FB + 4, -61)
        self.carve(-25, FB - 7, -80, -17, FB - 3, -74)
        self.carve(-24, FB - 7, -73, -22, FB - 3, -71)
        self.carve(12, FB, -73, 24, FB + 4, -70)
        self.carve(3, FB, -78, 5, FB + 3, -74)
        self.carve(4, FB, -78, 4, RIM, -78)
        for i in range(13):                                        # the stair down from the hub
            f = FR - i
            self.carve(22, f, -57 - i, 24, f + 4, -57 - i)
        # the dock stair: newel shaft in the crater wall and the passage to the strand
        self.carve(-24, FS - 1, -62, -16, FB + 4, -54)
        self.carve(-18, FS, -54, -16, FS + 3, -43)
        # the needle: gate vestibule, the newel shaft, the guard room, the passage to the keep
        self.carve(-5, FB, -16, 2, FB + 4, -2)
        self.carve(-5, FB - 1, -1, 5, FL + 4, 9)
        self.carve(7, 43, 3, 12, 47, 10)
        self.carve(3, FL, -6, 5, FL + 4, -2)

    def finish(self):
        self.K &= ~self.SUP
        S2 = self.S & ~self.K
        air = ~S2
        near = air.copy()
        for _ in range(2):
            n = near.copy()
            n[1:, :, :] |= near[:-1, :, :]
            n[:-1, :, :] |= near[1:, :, :]
            n[:, 1:, :] |= near[:, :-1, :]
            n[:, :-1, :] |= near[:, 1:, :]
            n[:, :, 1:] |= near[:, :, :-1]
            n[:, :, :-1] |= near[:, :, 1:]
            near = n
        shell = S2 & near
        shell[0, :, :] |= S2[0, :, :]
        shell[-1, :, :] |= S2[-1, :, :]
        shell[:, :, 0] |= S2[:, :, 0]
        shell[:, :, -1] |= S2[:, :, -1]
        top = S2.copy()
        top[:, :-1, :] &= ~S2[:, 1:, :]
        self.S2, self.shell, self.top = S2, shell, top


# ------------------------------------------------------------------ rock blocks
OUTER = ("stone", "andesite", "stone", "tuff", "andesite", "stone", "cobblestone", "andesite", "stone", "tuff")
INNER = ("tuff", "deepslate[axis=y]", "tuff", "basalt[axis=y]", "smooth_basalt", "tuff", "deepslate[axis=y]",
         "blackstone", "tuff", "smooth_basalt")
NEEDLE_R = ("deepslate[axis=y]", "tuff", "basalt[axis=y]", "smooth_basalt", "deepslate[axis=y]", "blackstone",
            "tuff", "calcite", "deepslate[axis=y]", "smooth_basalt")


def rock_block(x, y, z, top, mason, needle, jit, dl, d, sl, edge):
    h = hash3(x, y, z, 7)
    if mason:
        return MO if h < 0.3 else (CR if h < 0.45 else SB)
    s = y + int(5 * jit)
    if needle:
        if top and y < NEEDLE_TOP:
            return "moss_block" if h < 0.35 else ("tuff" if h < 0.7 else "smooth_basalt")
        return NEEDLE_R[(s // 3) % len(NEEDLE_R)]
    if dl < R_LAKE:                                       # the lake bed
        return "gravel" if h < 0.5 else ("clay" if h < 0.75 else "tuff")
    if dl < edge and y <= LAKE:                           # the strand
        if top:
            return "gravel" if h < 0.55 else ("tuff" if h < 0.8 else "coarse_dirt")
        return INNER[(s // 3) % len(INNER)]
    if dl < edge + 3 and y < RIM:                         # the crater wall
        return INNER[(s // 3) % len(INNER)]
    if top:
        if y >= RIM and d <= R_TOP:                       # the bailey
            n = jit
            if n > 0.66 and h < 0.5:
                return "coarse_dirt"
            if n < 0.28 and h < 0.4:
                return "gravel" if h < 0.15 else "podzol[snowy=false]"
            return "grass_block[snowy=false]" if h < 0.92 else "moss_block"
        if y <= 3:
            return "grass_block[snowy=false]" if h < 0.75 else ("gravel" if h < 0.85 else "mossy_cobblestone")
        if sl > 1.45:
            return OUTER[(s // 3) % len(OUTER)]
        if sl > 0.95:
            return "grass_block[snowy=false]" if h < 0.45 else OUTER[(s // 3) % len(OUTER)]
        return "grass_block[snowy=false]" if h < 0.8 else ("moss_block" if h < 0.9 else "coarse_dirt")
    if y < 8 and h < 0.25:
        return "mossy_cobblestone"
    return OUTER[(s // 3) % len(OUTER)]


def write_rock(bp, P):
    idx = np.argwhere(P.shell)
    for i, y, k in idx.tolist():
        x, z = int(XS[i]), int(ZS[k])
        bp.set(x, y, z, rock_block(x, y, z, bool(P.top[i, y, k]), bool(P.M[i, y, k]), bool(P.NEEDLE[i, y, k]),
                                   float(JIT[i, k]), float(DLAKE[i, k]), float(DIST[i, k]), float(SLOPE[i, k]),
                                   float(EDGE[i, k])))
    idx = np.argwhere(P.K & P.S)
    for i, y, k in idx.tolist():
        bp.set(int(XS[i]), y, int(ZS[k]), "air")


def write_lake(bp, P):
    """Water from the bed to y LAKE inside R_LAKE (the needle and the piers stay dry)."""
    for i, k in np.argwhere(DLAKE < R_LAKE).tolist():
        x, z = int(XS[i]), int(ZS[k])
        for y in range(int(HMAP[i, k]) + 1, LAKE + 1):
            if not P.S2[i, y, k]:
                bp.set(x, y, z, "water")


# ------------------------------------------------------------------ masonry helpers
def wall_block(x, y, z, y0=RIM, y1=FW - 1):
    """Stone of a wall face: deepslate base course, mossy and cracked low down, clean higher (BUILDING §5)."""
    h = hash3(x, y, z, 5)
    if y <= y0 + 1:
        return DB if h < 0.6 else (CDB if h < 0.8 else CD)
    fr = (y - y0) / max(1, y1 - y0) + 0.12 * (hash01(x, z, 9) - 0.5)
    if fr < 0.3:
        return MO if h < 0.28 else (CR if h < 0.42 else SB)
    if fr < 0.6:
        return MO if h < 0.08 else (CR if h < 0.2 else SB)
    return CR if h < 0.1 else SB


def merlon(bp, x, y, z, u):
    if int(u) % 4 < 2:
        bp.set(x, y, z, SB)
        bp.set(x, y + 1, z, SB_SL + "[type=bottom,waterlogged=false]")
    else:
        bp.set(x, y, z, SB_W)


def steep_pyramid(bp, x0, z0, x1, z1, y, spec, stairs_spec, steep=2, overhang=1, finial=None):
    """Hipped roof steeper than 45 degrees: the outline shrinks by 1 every ``steep`` layers (stairs on the first layer
    of each step, full blocks above). Returns the apex y."""
    lx, hx, lz, hz = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
    yy, i = y, 0
    while lx <= hx and lz <= hz:
        for x in range(lx, hx + 1):
            for z in range(lz, hz + 1):
                if x in (lx, hx) or z in (lz, hz):
                    if i % steep == 0:
                        if x in (lx, hx) and z in (lz, hz):
                            bp.set(x, yy, z, spec)
                        elif x == lx:
                            bp.set(x, yy, z, stair(stairs_spec, "east"))
                        elif x == hx:
                            bp.set(x, yy, z, stair(stairs_spec, "west"))
                        elif z == lz:
                            bp.set(x, yy, z, stair(stairs_spec, "south"))
                        else:
                            bp.set(x, yy, z, stair(stairs_spec, "north"))
                    else:
                        bp.set(x, yy, z, spec)
        if i % steep == steep - 1:
            lx, hx, lz, hz = lx + 1, hx - 1, lz + 1, hz - 1
        yy += 1
        i += 1
    if finial:
        bp.set((x0 + x1) // 2, yy, (z0 + z1) // 2, finial)
    return yy


def cone(bp, cx, cz, y, r, spec, stairs_spec, steep=2, finial="lightning_rod"):
    """Round roof steeper than 45 degrees (a shell: stairs facing in on the first layer of each step)."""
    yy, rr, i = y, r, 0
    while rr >= 0.6:
        for x, z, d in disc(cx, cz, rr + 0.35):
            if d > rr - 1.0:
                if i % steep == 0 and d > 0.6:
                    bp.set(x, yy, z, stair(stairs_spec, inward(x - cx, z - cz)))
                else:
                    bp.set(x, yy, z, spec)
        if i % steep == steep - 1:
            rr -= 1
        yy += 1
        i += 1
    bp.set(cx, yy, cz, spec)
    if finial:
        bp.set(cx, yy + 1, cz, finial)
    return yy


def stone_lantern(bp, x, y, z):
    bp.set(x, y, z, "andesite_wall")
    bp.set(x, y + 1, z, PA)
    bp.set(x, y + 2, z, LANT)


def lamp_post(bp, x, y, z):
    bp.set(x, y, z, SB_W)
    bp.set(x, y + 1, z, SB_W)
    bp.set(x, y + 2, z, LANT)


def banner(bp, x, y, z, facing, color="red"):
    bp.set(x, y, z, f"{color}_wall_banner[facing={facing}]")


# ------------------------------------------------------------------ the curtain
VERT = [polar(22.5 * k, R_WALL) for k in range(16)]
GATE_E, GATE_W = (GH[2], GH[1] + 1.0), (GH[0], GH[1] + 1.0)


def wall_segments():
    segs = []
    for k in range(16):
        a, b = VERT[k], VERT[(k + 1) % 16]
        if k == 7:
            b = GATE_E
        if k == 8:
            a = GATE_W
        segs.append((k, a, b))
    return segs


SEGS = wall_segments()


def breach_hit(x, z):
    return abs(((bearing(x, z) - BREACH_TH + 180) % 360) - 180) * R_WALL * math.pi / 180 < 3.2


def curtain(bp):
    for k, a, b in SEGS:
        nx, nz = b[1] - a[1], -(b[0] - a[0])
        L = math.hypot(nx, nz)
        nx, nz = nx / L, nz / L
        if nx * (a[0] + b[0]) + nz * (a[1] + b[1]) < 0:
            nx, nz = -nx, -nz                  # outward normal
        to_wall = inward(nx * 5, nz * 5)       # stairs leaning on the wall from outside
        for x, z, d, out, u in capsule_cells(a, b, 3.6):
            if d <= 2.5:
                for y in range(RIM, FW - 1):
                    bp.set(x, y, z, wall_block(x, y, z))
                if d < 1.5:
                    bp.set(x, FW - 1, z, PA if d < 0.5 and int(u) % 6 else SB)
                else:
                    bp.set(x, FW - 1, z, SB)
                    if out > 0:
                        merlon(bp, x, FW, z, u)
                    else:
                        bp.set(x, FW, z, SB_W)
                if out > 0 and d >= 1.5 and 3 <= int(u) % 9 <= 4:
                    bp.set(x, 50, z, "air")    # arrow slit (a recess in the outer face)
                    bp.set(x, 51, z, "air")
            elif out > 0 and d <= 3.6:
                bp.set(x, FW - 3, z, stair(SB_ST, to_wall, "top"))      # machicolation corbels
                bp.set(x, RIM + 1, z, DB)
                bp.set(x, RIM + 2, z, stair("deepslate_brick_stairs", to_wall))
                bp.set(x, RIM, z, DB)
                for y in range(max(0, hmap(x, z)), RIM):
                    bp.set(x, y, z, DB if hash3(x, y, z, 2) < 0.7 else CD)


def breach(bp):
    """The collapsed stretch of the west curtain where the side route gets in: a ragged V, rubble on both sides."""
    k = 12
    _, a, b = SEGS[k]
    for x, z, d, out, u in capsule_cells(a, b, 4.0):
        da = abs(((bearing(x, z) - BREACH_TH + 180) % 360) - 180) * R_WALL * math.pi / 180
        if da > 6.5:
            continue
        cut = FW + 2 - int(max(0.0, 6.5 - da) * 2.4 + 2 * hash01(x, z, 41))
        if da < 2.6:
            cut = FR
        for y in range(max(FR, cut), FW + 3):
            if bp.get(x, y, z) is not None:
                bp.set(x, y, z, "air")
        if da < 2.6:
            bp.set(x, RIM, z, "mossy_cobblestone" if hash01(x, z, 4) < 0.5 else "cobblestone")
    # rubble heaps beside the gap (not on the way through)
    for (th, r) in ((276.5, 78.5), (287.5, 78.0), (276.0, 86.0), (288.0, 86.2)):
        x, z = polar(th, r)
        x, z = round(x), round(z)
        for dx, dz, h in ((0, 0, 2), (1, 0, 1), (0, 1, 1), (-1, 0, 1), (0, -1, 1)):
            for y in range(FR, FR + h):
                bp.set(x + dx, y, z + dz, "mossy_cobblestone" if hash3(x + dx, y, z + dz, 8) < 0.5 else CR)


# ------------------------------------------------------------------ towers
def tower_doors_walk(bp, cx, cz, half, k):
    """Openings in a tower's walls at walk level where the two neighbouring wall segments meet it."""
    for kk in (k - 1, k):
        _, a, b = SEGS[kk % 16]
        for x in range(cx - half, cx + half + 1):
            for z in range(cz - half, cz + half + 1):
                if max(abs(x - cx), abs(z - cz)) < half - 2:
                    continue
                d, t, _, _ = seg_dist(x, z, a, b)
                if d <= 1.5 and 0.0 < t < 1.0:
                    bp.set(x, FW - 1, z, SB)
                    for y in range(FW, FW + 4):
                        bp.set(x, y, z, "air")


STAIR_TOWERS = {
    # k: (start corner, ground doors [(face, iron?, lever side)], roof?)
    0: (3, [("south", None)], True),
    2: (3, [("west", None), ("south", None)], True),
    6: (0, [("west", None), ("north", "out")], False),
    10: (1, [("north", None), ("east", "in")], False),
    14: (2, [("east", None), ("south", None)], True),
}


def stair_tower(bp, k):
    start, doors, roofed = STAIR_TOWERS[k]
    vx, vz = VERT[k]
    cx, cz = int(round(vx)), int(round(vz))
    half = 7
    x0, z0 = cx - 5, cz - 5                     # interior 11 x 11
    top = 65
    # body: foundations down to the rock, walls, floors
    for x in range(cx - half, cx + half + 1):
        for z in range(cz - half, cz + half + 1):
            wall = max(abs(x - cx), abs(z - cz)) > 5
            base = min(RIM, hmap(x, z))
            if wall:
                for y in range(max(0, base - 1), top + 1):
                    bp.set(x, y, z, wall_block(x, y, z, y1=top) if y < top - 1 else SB)
            else:
                for y in range(max(0, base - 1), RIM):
                    bp.set(x, y, z, SB)
                bp.set(x, RIM, z, SB if hash01(x, z, 3) < 0.7 else PA)
                for y in range(FR, top):
                    bp.set(x, y, z, "air")
    cells, core, top_c, top_f = newel(x0, z0, 5, FR, [5, 5, 4], start)
    write_newel(bp, cells, core, FR)
    last = {c for c, v in cells.items() if v[2] == 2 and v[1] is not None}
    corner_top = {c for c, v in cells.items() if v[0] == top_f}
    # the top room floor (y FW - 1) over everything but the last flight
    for x in range(x0, x0 + 11):
        for z in range(z0, z0 + 11):
            if (x, z) in last or (x, z) in corner_top:
                continue
            bp.set(x, FW - 1, z, "spruce_planks" if (x + z) % 5 else "stripped_spruce_log[axis=x]")
            for y in range(FW, top):
                bp.set(x, y, z, "air")
    for (x, z) in last:
        for dx, dz in DIRS.values():
            q = (x + dx, z + dz)
            if x0 <= q[0] < x0 + 11 and z0 <= q[1] < z0 + 11 and q not in last and q not in corner_top:
                bp.set(q[0], FW, q[1], "spruce_fence")
    for x in range(x0, x0 + 11):
        for z in range(z0, z0 + 11):
            bp.set(x, top, z, "spruce_planks")
    # ground doors next to the bottom landing
    sx, sz = {0: (x0, z0), 1: (x0 + 8, z0), 2: (x0 + 8, z0 + 8), 3: (x0, z0 + 8)}[start]
    for face, iron in doors:
        dxs = range(sx, sx + 3) if face in ("north", "south") else None
        if face == "north":
            ring = [(x, z0 - 1) for x in dxs] + [(x, z0 - 2) for x in dxs]
            outside = (sx + 1, z0 - 3)
        elif face == "south":
            ring = [(x, z0 + 11) for x in dxs] + [(x, z0 + 12) for x in dxs]
            outside = (sx + 1, z0 + 13)
        elif face == "west":
            ring = [(x0 - 1, z) for z in range(sz, sz + 3)] + [(x0 - 2, z) for z in range(sz, sz + 3)]
            outside = (x0 - 3, sz + 1)
        else:
            ring = [(x0 + 11, z) for z in range(sz, sz + 3)] + [(x0 + 12, z) for z in range(sz, sz + 3)]
            outside = (x0 + 13, sz + 1)
        for (x, z) in ring:
            bp.set(x, RIM, z, PA)
            for y in range(FR, FR + 4):
                bp.set(x, y, z, "air")
        if iron:
            # a one-way door: iron, its lever on one side only, the rest of the opening walled
            mx, mz = ring[1]
            for (x, z) in ring:
                for y in range(FR, FR + 4):
                    bp.set(x, y, z, SB if (x, z) != (mx, mz) or y >= FR + 2 else "air")
            bp.door(mx, FR, mz, face if iron == "out" else OPP[face], wood="iron")
            ox, oz = DIRS[face]
            if iron == "out":
                lx, lz = mx + ox * 2 + (1 if face in ("north", "south") else 0), mz + oz * 2 + (
                    1 if face in ("east", "west") else 0)
                bp.set(mx + ox * 2, FR + 1, mz + oz * 2, "air")
                wx, wz = mx + ox + (1 if face in ("north", "south") else 0), mz + oz + (1 if face in ("east", "west") else 0)
                bp.set(wx + ox, FR + 1, wz + oz, f"lever[face=wall,facing={face},powered=false]")
            else:
                ix, iz = mx - ox + (1 if face in ("north", "south") else 0), mz - oz + (1 if face in ("east", "west") else 0)
                bp.set(ix, FR + 1, iz, f"lever[face=floor,facing={OPP[face]},powered=false]")
        else:
            x, z = ring[1]
            bp.set(x + DIRS[face][0] * 0, FR + 4, z, CH)
    tower_doors_walk(bp, cx, cz, half, k)
    # windows in the top room, slits below
    for face, (fx, fz) in DIRS.items():
        for y in (FW + 1, FW + 2):
            px, pz = cx + fx * half, cz + fz * half
            if bp.get(px, y, pz) not in ("minecraft:air",):
                bp.set(px, y, pz, "glass_pane")
    # cornice and roof
    for x in range(cx - half - 1, cx + half + 2):
        for z in range(cz - half - 1, cz + half + 2):
            if max(abs(x - cx), abs(z - cz)) == half + 1:
                bp.set(x, top, z, stair(SB_ST, inward(x - cx, z - cz), "top"))
    if roofed:
        steep_pyramid(bp, cx - half, cz - half, cx + half, cz + half, top + 1, ROOF, ROOF_ST, steep=1,
                      overhang=1, finial="lightning_rod")
    else:
        for x in range(cx - half - 1, cx + half + 2):
            for z in range(cz - half - 1, cz + half + 2):
                if max(abs(x - cx), abs(z - cz)) == half + 1:
                    bp.set(x, top + 1, z, SB if (x + z) % 3 else SB_W)
                elif max(abs(x - cx), abs(z - cz)) <= half:
                    bp.set(x, top, z, SB)
        # a watch cabin on the platform
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                e = max(abs(x - cx), abs(z - cz)) == 2
                for y in range(top + 1, top + 4):
                    if e and abs(x - cx) == 2 and abs(z - cz) == 2:
                        bp.set(x, y, z, "spruce_log[axis=y]")
        steep_pyramid(bp, cx - 2, cz - 2, cx + 2, cz + 2, top + 4, ROOF, ROOF_ST, steep=1, overhang=1)
    # light
    return cells


def turret(bp, k):
    """An open round turret on an odd vertex: solid, its top flush with the walk, taller merlons."""
    vx, vz = VERT[k]
    cx, cz = int(round(vx)), int(round(vz))
    r = 4.6
    for x, z, d in disc(cx, cz, r + 1.2):
        if d <= r:
            for y in range(max(0, min(RIM, hmap(x, z)) - 1), FW - 1):
                bp.set(x, y, z, wall_block(x, y, z))
            bp.set(x, FW - 1, z, PA if d < 1.5 else SB)
            for y in range(FW, FW + 4):
                bp.set(x, y, z, "air")
            if d > r - 1.0:
                ang = math.atan2(x - cx, z - cz)
                if (int((ang + math.pi) * 3) % 2) == 0:
                    bp.set(x, FW, z, SB)
                    bp.set(x, FW + 1, z, SB)
                    bp.set(x, FW + 2, z, SB_SL + "[type=bottom,waterlogged=false]")
                else:
                    bp.set(x, FW, z, SB_W)
        elif d <= r + 1.2 and math.hypot(x, z) > R_WALL + 1.5:
            bp.set(x, FW - 3, z, stair(SB_ST, inward(x - cx, z - cz), "top"))
    # re-open the walk through the turret
    for kk in (k - 1, k):
        _, a, b = SEGS[kk % 16]
        for x, z, d in disc(cx, cz, r):
            dd, t, _, _ = seg_dist(x, z, a, b)
            if dd < 1.5:
                bp.set(x, FW, z, "air")
                bp.set(x, FW + 1, z, "air")
                bp.set(x, FW + 2, z, "air")
    bp.set(cx, FW, cz, "andesite_wall")
    bp.set(cx, FW + 1, cz, LANT)


def west_tower(bp):
    """The tall round west tower (k 12): a guard room at walk level, a red cone roof."""
    vx, vz = VERT[12]
    cx, cz = int(round(vx)), int(round(vz))
    r = 7.5
    top = 70
    for x, z, d in disc(cx, cz, r + 1.3):
        if d <= r:
            wall = d > r - 2.0
            for y in range(max(0, min(RIM, hmap(x, z)) - 1), FW - 1):
                bp.set(x, y, z, wall_block(x, y, z, y1=top) if wall else SB)
            bp.set(x, FW - 1, z, SB if wall else ("spruce_planks" if (x + z) % 4 else "spruce_log[axis=x]"))
            for y in range(FW, top + 1):
                bp.set(x, y, z, wall_block(x, y, z, y1=top) if wall else "air")
            bp.set(x, top, z, SB if wall else "spruce_planks")
        elif d <= r + 1.3:
            bp.set(x, top, z, stair(SB_ST, inward(x - cx, z - cz), "top"))
    tower_doors_walk(bp, cx, cz, 8, 12)
    for i in range(8):
        a = i * math.tau / 8 + 0.2
        x, z = round(cx + (r - 0.5) * math.sin(a)), round(cz + (r - 0.5) * math.cos(a))
        if bp.get(x, FW + 1, z) != "minecraft:air":
            bp.set(x, FW + 1, z, "glass_pane")
            bp.set(x, FW + 2, z, "glass_pane")
    bp.set(cx, top - 1, cz, LANT_H)
    bp.set(cx - 3, FW, cz - 2, "barrel[facing=up,open=false]")
    bp.chest(cx - 3, FW, cz + 2, "east", loot=LOOT + "caldera_ramparts")
    cone(bp, cx, cz, top + 1, r + 1, ROOF, ROOF_ST, steep=2)


# ------------------------------------------------------------------ the gatehouse and the barbican
def gatehouse(bp):
    x0, z0, x1, z1 = GH
    ix0, iz0, ix1, iz1 = x0 + 3, z0 + 3, x1 - 3, z1 - 3       # interior -13, 85, 13, 102
    ceil = 55
    deck = FW - 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            inner = ix0 <= x <= ix1 and iz0 <= z <= iz1
            if inner:
                bp.set(x, GF - 1, z, PA if abs(x) <= 1 or (z == iz1 and x > 0) else (SB if hash01(x, z, 2) < 0.8
                                                                                     else CR))
                for y in range(GF, ceil):
                    bp.set(x, y, z, "air")
                for y in range(ceil, deck + 1):
                    bp.set(x, y, z, SB)
            else:
                for y in range(min(GF - 1, max(0, hmap(x, z) - 1)), deck + 1):
                    if y < 12:
                        spec = DB if hash3(x, y, z, 1) < 0.7 else CDB
                    elif y in (30, 52):
                        spec = PA
                    else:
                        spec = wall_block(x, y, z, y0=10, y1=deck)
                    bp.set(x, y, z, spec)
            # crenellated deck
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                merlon(bp, x, FW, z, x + z)
    # machicolations along the south face: a corbelled gallery front under the merlons, and arrow slits
    for x in range(x0, x1 + 1):
        bp.set(x, deck - 2, z1 + 1, stair(SB_ST, "north", "top"))
        bp.set(x, deck - 1, z1 + 1, SB)
        bp.set(x, deck, z1 + 1, SB)
        merlon(bp, x, FW, z1 + 1, x + 1)
        bp.set(x, FW, z1, "air")
    for sx in (-12, -4, 4, 12):
        for y0 in (19, 34, 46):
            if abs(sx) <= 5 and y0 == 19:
                continue
            for y in range(y0, y0 + 3):
                bp.set(sx, y, z1, "air" if y < y0 + 2 else SB)
            bp.set(sx, y0, z1, "air")
    # the walk joins the deck on its north corners
    for (x, z) in ((x0, z0 + 1), (x0, z0 + 2), (x1, z0 + 1), (x1, z0 + 2), (x0, z0), (x1, z0)):
        for y in range(FW, FW + 3):
            bp.set(x, y, z, "air")
    # buttresses on the south face
    for bx in (-11, -7, 7, 11):
        for z in range(z1 + 1, z1 + 3):
            for y in range(max(0, hmap(bx, z) - 1), 40 - (z - z1) * 6):
                bp.set(bx, y, z, wall_block(bx, y, z, y0=10, y1=40))
            bp.set(bx, 40 - (z - z1) * 6, z, stair(SB_ST, "north"))
    # the portal: a pointed arch 9 x 14, its ring of polished andesite, gate leaves with a wicket
    prof = pointed_arch(4.6, 14)
    for u in range(-5, 6):
        hgt = int(prof(u))
        for z in range(z1 - 2, z1 + 1):
            for y in range(GF, GF + hgt):
                bp.set(u, y, z, "air")
            bp.set(u, GF - 1, z, PA)
        if hgt > 0:
            bp.set(u, GF + hgt, z1, PA)
            bp.set(u, GF + hgt + 1, z1, CH if u == 0 else PA)
        for y in range(GF, GF + hgt):
            if abs(u) <= 1 and y < GF + 4:
                continue
            if abs(u) == 2 and y < GF + 4:
                bp.set(u, y, z1 - 1, "dark_oak_log[axis=y]")
                continue
            if y == GF + 4 and abs(u) <= 1:
                bp.set(u, y, z1 - 1, "dark_oak_log[axis=x]")
                continue
            bp.set(u, y, z1 - 1, "dark_oak_log[axis=x]" if (y - GF) % 5 == 4 else "spruce_planks")
    for u in (-6, 6):
        for y in range(GF - 1, GF + 12):
            bp.set(u, y, z1 + 1, PA if y % 4 else CH)
    banner(bp, -7, GF + 9, z1 + 1, "south")
    banner(bp, 7, GF + 9, z1 + 1, "south")
    # windows high on the south face (light into the stair hall)
    for wx in (-9, 9):
        for y in range(36, 46):
            bp.set(wx, y, z1, "glass_pane" if y < 45 else PA)
            bp.set(wx, y, z1 - 1, "air")
            bp.set(wx, y, z1 - 2, "air")
    # the north door to the gate court (feet FR)
    for x in range(-1, 2):
        for z in range(z0, z0 + 3):
            bp.set(x, RIM, z, PA)
            for y in range(FR, FR + 4):
                bp.set(x, y, z, "air")
    for x in range(-2, 3):
        bp.set(x, FR + 4, z0, CH if x == 0 else PA)
    # the grand stair: three flights of 12 round the hall, a gallery and a flying bridge at feet FR
    cells = {}
    for i in range(1, 13):                       # F1: east wall, north
        for x in range(ix1 - 2, ix1 + 1):
            cells[(x, iz1 - i)] = (GF + i, "north")
    for z in range(iz0, iz0 + 5):                # NE landing
        for x in range(ix1 - 2, ix1 + 1):
            cells[(x, z)] = (GF + 12, None)
    for i in range(1, 13):                       # F2: north wall, west
        for z in range(iz0, iz0 + 3):
            cells[(ix1 - 2 - i, z)] = (GF + 12 + i, "west")
    for x in range(ix0, ix1 - 14):               # NW landing
        for z in range(iz0, iz0 + 3):
            cells[(x, z)] = (GF + 24, None)
    for i in range(1, 13):                       # F3: west wall, south
        for x in range(ix0, ix0 + 3):
            cells[(x, iz0 + 2 + i)] = (GF + 24 + i, "south")
    for x in range(ix0, 2):                      # SW landing and the gallery along the south wall
        for z in range(iz1 - 2, iz1 + 1):
            cells[(x, z)] = (FR, None)
    over = []                                    # the flying bridge where it spans the second flight
    for z in range(iz0, iz1 - 2):                # the flying bridge to the north door
        for x in range(-1, 2):
            if (x, z) not in cells:
                cells[(x, z)] = (FR, None)
            elif cells[(x, z)][0] < FR - 4:
                over.append((x, z))
    for (x, z) in over:
        bp.set(x, FR - 1, z, PA if hash01(x, z, 4) < 0.5 else SB)
        bp.set(x, FR - 2, z, stair(SB_ST, "south" if z == iz0 + 2 else "north", "top") if z in (iz0, iz0 + 2)
               else SB)
        for sx in (-2, 2):
            bp.set(sx, FR, z, SB_W)
    for (x, z), (f, fc) in cells.items():
        massive = f < FR or (x < -1 and z > iz1 - 3) or x <= ix0 + 2
        if f == FR and ix0 + 3 <= x and not (x <= 1 and z >= iz1 - 2 and x >= ix0):
            pass
        if fc:
            bp.set(x, f - 1, z, stair(SB_ST, fc))
        else:
            bp.set(x, f - 1, z, PA if hash01(x, z, 4) < 0.5 else SB)
        bridge = f == FR and -1 <= x <= 1 and z < iz1 - 2
        gallery = f == FR and z >= iz1 - 2 and x > ix0 + 2
        if bridge or gallery:
            bp.set(x, f - 2, z, SB)
        else:
            for y in range(GF - 1, f - 1):
                bp.set(x, y, z, SB if hash3(x, y, z, 3) < 0.85 else CR)
        for y in range(f, f + 4):
            if (x, y, z) and bp.get(x, y, z) in (None, "minecraft:air"):
                pass
    # balustrades on the open sides
    for (x, z), (f, fc) in cells.items():
        for dx, dz in DIRS.values():
            q = (x + dx, z + dz)
            if q in cells or not (ix0 <= q[0] <= ix1 and iz0 <= q[1] <= iz1):
                continue
            cur = bp.get(q[0], f, q[1])
            if cur in (None, "minecraft:air"):
                bp.set(q[0], f, q[1], SB_W)
    # the portal approach and the foot of F1 stay open: no balustrade across the walking line
    for x in range(-1, ix1 + 1):
        for z in range(iz1 - 1, iz1 + 1):
            if (x, z) not in cells:
                for y in range(GF, GF + 3):
                    bp.set(x, y, z, "air")
    # chandeliers on chains, lamps on the walls
    for (lx, lz) in ((-5, 93), (5, 93), (0, 96)):
        bp.chain(lx, 46, lz, ceil - 1)
        bp.set(lx, 45, lz, LANT_H)
    for (lx, lz) in ((-6, 89), (6, 89)):
        bp.chain(lx, 30, lz, ceil - 1)
        bp.set(lx, 29, lz, LANT_H)
    # the guardians: skeleton knights in the hall
    bp.spawner(-6, GF, 95, MOB_KNIGHT)
    bp.spawner(4, GF, 92, "brasshaven:magma_sentry")
    # banners and a statue plinth in the hall
    for (sx, sz) in ((-8, 99), (8, 99)):
        bp.set(sx, GF, sz, CH)
        bp.set(sx, GF + 1, sz, PA)
        bp.set(sx, GF + 2, sz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the two great towers flanking the portal
    for sx in (-1, 1):
        tcx, tcz, r = sx * 21, 102, 6.5
        for x, z, d in disc(tcx, tcz, r + 1.2):
            if d <= r:
                wall = d > r - 2.0
                for y in range(max(0, hmap(x, z) - 1), 84):
                    if wall or y in (FW - 1,):
                        if y < 12:
                            spec = DB if hash3(x, y, z, 1) < 0.7 else CDB
                        elif y in (30, 52, 72):
                            spec = PA
                        else:
                            spec = wall_block(x, y, z, y0=10, y1=84)
                        bp.set(x, y, z, spec)
                bp.set(x, 83, z, SB)
            elif d <= r + 1.2:
                bp.set(x, 82, z, stair(SB_ST, inward(x - tcx, z - tcz), "top"))
                bp.set(x, 83, z, SB)
                bp.set(x, 84, z, SB if (x + z) % 2 else SB_W)
        for i in range(6):
            a = i * math.tau / 6 + 0.5
            for y in (60, 61, 70, 71):
                x, z = round(tcx + r * math.sin(a)), round(tcz + r * math.cos(a))
                bp.set(x, y, z, "glass_pane" if y in (70, 71) else "air")
        cone(bp, tcx, tcz, 84, 5, ROOF, ROOF_ST, steep=2)


def barbican(bp):
    """The walled forecourt before the portal (feet GF): the road comes in on the east, the side route leaves west."""
    for x in range(-12, 13):
        for z in range(106, 115):
            base = max(0, hmap(x, z))
            for y in range(min(base, GF - 1), GF - 1):
                bp.set(x, y, z, SB if hash3(x, y, z, 6) < 0.8 else MO)
            bp.set(x, GF - 1, z, PA if abs(x) <= 1 else (SB if hash01(x, z, 8) < 0.75 else "andesite"))
            for y in range(GF, GF + 5):
                bp.set(x, y, z, "air")
            edge_s = z == 114
            edge_e = x == 12 and not 107 <= z <= 112
            edge_w = x == -12 and not 107 <= z <= 112
            if edge_s or edge_e or edge_w:
                bp.set(x, GF, z, SB)
                bp.set(x, GF + 1, z, SB if (x + z) % 2 else SB_W)
    # retaining walls down to the talus
    for x in range(-13, 14):
        for z in (115,):
            for y in range(max(0, hmap(x, z)), GF + 1):
                bp.set(x, y, z, stair(SB_ST, "north") if y == GF else DB if y < 3 else SB)
    for sx in (-1, 1):
        tx, tz = sx * 12, 114
        for x, z, d in disc(tx, tz, 2.4):
            for y in range(max(0, hmap(x, z)), 17):
                bp.set(x, y, z, SB if d > 1.2 or y < GF or y > 15 else "air")
        bp.set(tx, 17, tz, SB)
        bp.set(tx, 18, tz, LANT)
    for x in (-5, 5):
        stone_lantern(bp, x, GF, 108)


# ------------------------------------------------------------------ the east bastion and the wards
def east_bastion(bp):
    """A D-shaped bastion on the east vertex: armoury inside (feet FR), gun deck on top (feet FW), base down the slope."""
    x0, x1, z0, z1 = 82, 96, -9, 9
    rc = 9.5
    cx = x1

    def inside_(x, z):
        return (x0 <= x <= x1 and z0 <= z <= z1) or math.hypot(x - cx, z) <= rc

    def inner(x, z):
        return (x0 + 3 <= x <= x1 and z0 + 3 <= z <= z1 - 3) or math.hypot(x - cx, z) <= rc - 3

    for x in range(x0, int(cx + rc) + 2):
        for z in range(z0 - 1, z1 + 2):
            if not inside_(x, z):
                continue
            base = max(0, hmap(x, z) - 1)
            wall = not inner(x, z)
            for y in range(base, FW - 1):
                if wall or y < RIM or y >= FR + 7:
                    if y < RIM - 6:
                        spec = DB if hash3(x, y, z, 1) < 0.6 else CD
                    elif y == RIM - 6:
                        spec = PA
                    else:
                        spec = wall_block(x, y, z, y0=RIM - 5)
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, "air")
            if not wall:
                bp.set(x, RIM, z, SB if hash01(x, z, 5) < 0.6 else PA)
            bp.set(x, FW - 1, z, PA if abs(z) <= 1 else SB)
            for y in range(FW, FW + 4):
                bp.set(x, y, z, "air")
            # parapet on the outer edge
            if not inside_(x + 1, z) or not inside_(x, z + 1) or not inside_(x, z - 1):
                if x > R_WALL + 2:
                    merlon(bp, x, FW, z, x + z)
    # the door from the east ward through the curtain into the armoury
    for x in range(78, x0 + 4):
        for z in range(-1, 2):
            bp.set(x, RIM, z, PA)
            for y in range(FR, FR + 4):
                bp.set(x, y, z, "air")
    for z in (-2, 2):
        bp.set(79, FR + 4, z, CH)
    # the armoury: racks, anvil, chests, the knight
    for z in (-5, 5):
        for x in range(86, 95, 2):
            bp.set(x, FR, z, "barrel[facing=up,open=false]" if x % 4 else "smithing_table")
            bp.set(x, FR + 1, z, "iron_bars" if x % 4 else "air")
    bp.set(91, FR, 0, "anvil[facing=north]")
    bp.set(99, FR, -2, "grindstone[face=floor,facing=north]")
    bp.chest(100, FR, 0, "west", loot=LOOT + "caldera_armory")
    bp.chest(99, FR, 2, "west", loot=LOOT + "caldera_armory")
    bp.spawner(95, FR, -3, "brasshaven:magma_sentry")
    for (lx, lz) in ((88, 0), (96, 0)):
        bp.chain(lx, FR + 5, lz, FR + 6)
        bp.set(lx, FR + 4, lz, LANT_H)
    # gun deck: two cannons pointing out over the slope
    for cz in (-4, 4):
        for x in range(100, 104):
            bp.set(x, FW, cz, "polished_blackstone" if x < 103 else "polished_blackstone_wall")
        bp.set(99, FW, cz, "anvil[facing=east]")
        bp.set(101, FW, cz + 1, "polished_blackstone_slab[type=bottom,waterlogged=false]")
    bp.set(97, FW, 0, "andesite_wall")
    bp.set(97, FW + 1, 0, LANT)


def barracks(bp):
    """The barracks along the east curtain: bunks, tables, the sergeant's chest."""
    x0, x1, z0, z1 = 62, 76, -12, 12
    top = FR + 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            bp.set(x, RIM, z, "spruce_planks" if not wall else SB)
            for y in range(FR, top):
                if wall:
                    corner = x in (x0, x1) and z in (z0, z1)
                    post = corner or (z - z0) % 6 == 0 and x in (x0, x1)
                    if y < FR + 2:
                        spec = SB if hash3(x, y, z, 3) < 0.8 else MO
                    elif post:
                        spec = "dark_oak_log[axis=y]"
                    elif y == top - 1:
                        spec = "dark_oak_log[axis=z]" if x in (x0, x1) else "dark_oak_log[axis=x]"
                    else:
                        spec = "white_terracotta" if hash3(x, y, z, 4) < 0.85 else "spruce_planks"
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, top, z, "spruce_planks")
    # windows
    for z in range(z0 + 3, z1 - 1, 6):
        for x in (x0, x1):
            bp.set(x, FR + 2, z, "glass_pane")
            bp.set(x, FR + 3, z, "glass_pane")
    # doors: west to the ward, east to the bastion
    for z in (-1, 0, 1):
        bp.set(x0, FR, z, "air")
        bp.set(x0, FR + 1, z, "air")
        bp.set(x0, FR + 2, z, "air")
        bp.set(x1, FR, z, "air")
        bp.set(x1, FR + 1, z, "air")
        bp.set(x1, FR + 2, z, "air")
    for x in range(x1 + 1, 79):
        for z in range(-1, 2):
            bp.set(x, RIM, z, PA)
    # roof (ridge along z)
    for z in range(z0 - 1, z1 + 2):
        for i in range(9):
            y = top + 1 + i
            xa, xb = x0 - 1 + i, x1 + 1 - i
            if xa > xb:
                break
            if xa == xb:
                bp.set(xa, y, z, SLATE_SL + "[type=bottom,waterlogged=false]")
                break
            bp.set(xa, y, z, stair(SLATE_ST, "east"))
            bp.set(xb, y, z, stair(SLATE_ST, "west"))
            if z in (z0 - 1, z1 + 1):
                continue
            if z in (z0, z1):
                for x in range(xa + 1, xb):
                    bp.set(x, y, z, "spruce_planks")
    # bunks along the walls, tables down the middle
    for z in range(z0 + 2, z1 - 1, 3):
        bp.bed(x0 + 1, FR, z, "east", color="red")
        bp.bed(x1 - 2, FR, z, "west", color="red")
    for z in range(-9, 10, 4):
        if abs(z) <= 1:
            continue
        bp.set(69, FR, z, "spruce_fence")
        bp.set(69, FR + 1, z, "spruce_pressure_plate")
        bp.set(68, FR, z, stair("spruce_stairs", "east"))
        bp.set(70, FR, z, stair("spruce_stairs", "west"))
    bp.chest(69, FR, z1 - 1, "north", loot=LOOT + "caldera_barracks")
    bp.set(70, FR, z1 - 1, "barrel[facing=up,open=false]")
    bp.set(68, FR, z1 - 1, "barrel[facing=up,open=false]")
    bp.spawner(73, FR, -9, MOB_SKELETON)
    for z in (-6, 6):
        bp.chain(69, top - 1, z, top - 1)
        bp.set(69, top - 2, z, LANT_H)


def cross_wall(bp, k):
    """The radial wall from a diagonal tower's inner corner to the crater edge: it splits two wards."""
    vx, vz = VERT[k]
    ux, uz = -vx / R_WALL, -vz / R_WALL
    a = (vx + ux * 7.5, vz + uz * 7.5)
    t = 0.0
    b = None
    while t < 40:
        px, pz = a[0] + ux * t, a[1] + uz * t
        if math.hypot(px - LCX, pz - LCZ) < R_EDGE - 1.5:
            b = (px, pz)
            break
        t += 0.5
    for x, z, d, out, u in capsule_cells(a, b, 1.6):
        if math.hypot(x - LCX, z - LCZ) < R_EDGE - 3:
            continue
        for y in range(max(0, min(RIM, hmap(x, z)) - 1), FR + 9):
            bp.set(x, y, z, wall_block(x, y, z, y1=FR + 9))
        bp.set(x, FR + 9, z, SB if int(u) % 4 < 2 else SB_W)
        # down the crater wall a little (no gap to slip through at the edge)
        for y in range(max(LAKE, RIM - 6), RIM):
            bp.set(x, y, z, SB)


def inner_parapet(bp):
    """A low wall along the crater edge all round the bailey (1.5 high: nobody falls into the crater by mistake)."""
    done = set()
    for i, k in np.argwhere((DLAKE >= EDGE) & (DLAKE < EDGE + 1.6) & (DIST <= R_TOP)).tolist():
        x, z = int(XS[i]), int(ZS[k])
        if (x, z) in done:
            continue
        done.add((x, z))
        if bp.get(x, FR, z) not in (None, "minecraft:air"):
            continue
        bp.set(x, RIM, z, SB if hash01(x, z, 3) < 0.7 else MO)
        bp.set(x, FR, z, SB_W if hash01(x, z, 9) < 0.85 else "mossy_stone_brick_wall")


# ------------------------------------------------------------------ gate court (south ward)
def gate_court(bp):
    # paving from the gatehouse north door to the tower doors
    for x in range(-12, 13):
        for z in range(72, 82):
            if bp.get(x, RIM, z) in ("minecraft:grass_block", "minecraft:moss_block", "minecraft:coarse_dirt",
                                     "minecraft:podzol", "minecraft:gravel"):
                bp.set(x, RIM, z, PA if abs(x) <= 1 else ("stone_bricks" if hash01(x, z, 6) < 0.6 else "andesite"))
    # the site of grace
    bp.set(-5, FR, 75, MOD["waystone"])
    stone_lantern(bp, -7, FR, 73)
    stone_lantern(bp, 7, FR, 73)
    # stables against the curtain (west)
    for x in range(-30, -16):
        for z in range(68, 78):
            if math.hypot(x, z) > R_WALL - 2.4:
                continue
            bp.set(x, FR + 4, z, "spruce_slab[type=bottom,waterlogged=false]")
            if (x in (-30, -17)) and z in (68, 72, 76):
                for y in range(FR, FR + 4):
                    bp.set(x, y, z, "spruce_log[axis=y]")
    for z in range(69, 77, 3):
        bp.set(-27, FR, z, "hay_block[axis=y]")
        bp.set(-25, FR, z, "spruce_fence")
    bp.set(-22, FR, 70, "hay_block[axis=x]")
    bp.set(-22, FR + 1, 70, "hay_block[axis=x]")
    bp.set(-20, FR, 74, "water_cauldron[level=3]")
    bp.set(-18, FR, 70, "barrel[facing=up,open=false]")
    # a cart by the gate
    for (x, z) in ((10, 77), (11, 77)):
        bp.set(x, FR, z, "spruce_slab[type=top,waterlogged=false]")
    bp.set(9, FR, 77, "spruce_fence")
    bp.set(17, FR, 76, "barrel[facing=up,open=false]")
    # the water-gate stair house over its shaft (x 6..14, z 66..74)
    for x in range(5, 16):
        for z in range(65, 76):
            wall = x in (5, 15) or z in (65, 75)
            if not wall:
                continue
            for y in range(FR, FR + 5):
                bp.set(x, y, z, wall_block(x, y, z, y1=FR + 5))
    for x in range(5, 16):
        for z in range(65, 76):
            bp.set(x, FR + 5, z, SB)
    steep_pyramid(bp, 5, 65, 15, 75, FR + 6, SLATE, SLATE_ST, steep=1, overhang=1)


def water_gate(bp):
    """The newel shaft from the strand (feet FS) up to the gate court (feet FR); an iron door with its lever on the
    strand side: a shortcut back to the gate."""
    x0, z0 = 6, 66
    flights = [3] * 10 + [2]
    cells, core, top_c, top_f = newel_laps(bp, x0, z0, 3, FS, flights, 1, cw=False)
    assert top_f == FR, top_f
    # floors of the house at the top: the top landing is the house floor
    for x in range(6, 15):
        for z in range(66, 75):
            if (x, z) not in cells or cells[(x, z)][0] < FR - 4:
                pass
    # the door of the house into the court (north face, next to the top corner)
    tx, tz = {0: (6, 66), 1: (12, 66), 2: (12, 72), 3: (6, 72)}[top_c]
    door_face = "north" if tz == 66 else "south"
    dz = 65 if door_face == "north" else 75
    for x in range(tx, tx + 3):
        bp.set(x, RIM, dz, PA)
        for y in range(FR, FR + 4):
            bp.set(x, y, dz, "air")
    # bottom: the passage out to the strand (south of the shaft is the court... the strand is north)
    for z in range(58, 66):
        for x in range(12, 15):
            bp.set(x, FS - 1, z, SB if hash01(x, z, 1) < 0.7 else MO)
            for y in range(FS, FS + 4):
                bp.set(x, y, z, "air")
    # the iron door near the strand end, its lever outside
    for x in (12, 14):
        for y in range(FS, FS + 4):
            bp.set(x, y, 61, SB)
    for y in (FS + 2, FS + 3):
        bp.set(13, y, 61, SB)
    bp.door(13, FS, 61, "north", wood="iron")
    bp.set(12, FS + 1, 60, "lever[face=wall,facing=north,powered=false]")
    bp.set(12, FS + 1, 61, SB)


# ------------------------------------------------------------------ the hub (north ward)
def great_tower_extras(bp, cells):
    """The hatch of the undercroft ladder in the great tower's ground room."""
    bp.set(4, RIM, -78, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")


def hub(bp):
    # paving across the court
    for x in range(-12, 22):
        for z in range(-70, -52):
            b = bp.get(x, RIM, z)
            if b in ("minecraft:grass_block", "minecraft:moss_block", "minecraft:coarse_dirt", "minecraft:podzol",
                     "minecraft:gravel"):
                c = math.hypot(x - 2, z + 62)
                bp.set(x, RIM, z, CH if c < 1 else (PA if c < 4 or abs(x) <= 1 else
                                                    ("stone_bricks" if hash01(x, z, 6) < 0.6 else "andesite")))
    # fountain
    cx, cz = 2, -62
    for x, z, d in disc(cx, cz, 3.6):
        if d > 2.6:
            bp.set(x, FR, z, SB)
        elif d > 0.8:
            bp.set(x, RIM, z, "water")
        else:
            bp.set(x, RIM, z, SB)
            bp.set(x, FR, z, SB_W)
            bp.set(x, FR + 1, z, SB_W)
            bp.set(x, FR + 2, z, CH)
    for x, z, d in disc(cx, cz, 2.6):
        if 0.8 < d:
            bp.set(x, RIM - 1, z, SB)
    # the site of grace
    bp.set(-6, FR, -60, MOD["waystone"])
    stone_lantern(bp, -8, FR, -58)
    # the overlook over the crater (a balcony over the undercroft gallery)
    for x in range(-6, 7):
        for z in range(-56, -50):
            if math.hypot(x - LCX, z - LCZ) >= EDGE_AT(x, z) - 0.5:
                continue
            bp.set(x, RIM, z, SB if hash01(x, z, 2) < 0.7 else PA)
            bp.set(x, RIM - 1, z, stair(SB_ST, "north", "top") if z == -50 else SB)
            for y in range(FR, FR + 3):
                bp.set(x, y, z, "air")
    for x in range(-7, 8):
        for z in range(-57, -49):
            if bp.get(x, RIM, z) is None:
                continue
            open_ = any(bp.get(x + dx, RIM, z + dz) is None for dx, dz in DIRS.values())
            if open_ and (abs(x) >= 6 or z >= -51):
                bp.set(x, FR, z, SB_W)
    # the undercroft stair house: an open pavilion over the first steps
    for (x, z) in ((21, -57), (25, -57), (21, -63), (25, -63)):
        for y in range(FR, FR + 5):
            bp.set(x, y, z, "spruce_log[axis=y]")
    for x in range(20, 27):
        for z in range(-64, -55):
            bp.set(x, FR + 5, z, "spruce_slab[type=bottom,waterlogged=false]" if x in (20, 26) or z in (-64, -56)
                   else "spruce_planks")
    for z in range(-63, -56):
        for x in (21, 25):
            if bp.get(x, FR, z) in (None, "minecraft:air", "minecraft:grass_block"):
                bp.set(x, FR, z, SB_W)
    great_hall(bp)
    kitchen(bp)


def EDGE_AT(x, z):
    if not inside(x, z):
        return R_EDGE
    i, _, k = ai(x, 0, z)
    return float(EDGE[i, k])


def great_hall(bp):
    """The great hall west of the great tower: a hall 21 x 13, timber roof trusses, the lord's table, a hearth."""
    x0, x1, z0, z1 = -32, -10, -72, -60
    top = FR + 10
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(RIM - 1, RIM + 1):
                bp.set(x, y, z, SB if wall else ("spruce_planks" if (x + z) % 7 else "dark_oak_planks"))
            for y in range(FR, top + 1):
                if wall:
                    pier = x in (x0, x1) and z in (z0, z1) or (x - x0) % 5 == 0 and z in (z0, z1)
                    if y == top:
                        spec = PA
                    elif pier:
                        spec = PA if y % 4 == 0 else SB
                    else:
                        spec = wall_block(x, y, z, y1=top)
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, "air")
    # tall windows on the south side, a rose on the west gable
    for x in range(x0 + 2, x1 - 1, 5):
        for y in range(FR + 3, FR + 8):
            bp.set(x, y, z1, "glass_pane")
            bp.set(x + 1, y, z1, "glass_pane")
    # the door from the court (east end of the south wall), 3 wide
    for x in range(-14, -11):
        for y in range(FR, FR + 4):
            bp.set(x, y, z1, "air")
    bp.set(-13, FR + 4, z1, CH)
    # roof: slate gable, ridge along x, trusses below
    for x in range(x0 - 1, x1 + 2):
        for i in range(8):
            y = top + 1 + i
            za, zb = z0 - 1 + i, z1 + 1 - i
            if za >= zb:
                bp.set(x, y, za, SLATE_SL + "[type=bottom,waterlogged=false]")
                break
            bp.set(x, y, za, stair(SLATE_ST, "south"))
            bp.set(x, y, zb, stair(SLATE_ST, "north"))
            if x in (x0, x1):
                for z in range(za + 1, zb):
                    bp.set(x, y, z, SB)
    for x in range(x0 + 4, x1 - 2, 4):
        for z in range(z0 + 1, z1):
            bp.set(x, top, z, "dark_oak_log[axis=z]")
        bp.chain(x, top - 3, (z0 + z1) // 2, top - 1)
        bp.set(x, top - 4, (z0 + z1) // 2, LANT_H)
    # the lord's table on a dais (west end), benches, the hearth on the north wall
    for x in range(x0 + 1, x0 + 5):
        for z in range(z0 + 1, z1):
            bp.set(x, RIM, z, "dark_oak_planks")
            bp.set(x, FR, z, "red_carpet" if x != x0 + 1 else "air")
    for z in range(z0 + 3, z1 - 2):
        bp.set(x0 + 3, FR, z, "dark_oak_fence")
        bp.set(x0 + 3, FR + 1, z, "dark_oak_pressure_plate")
    bp.set(x0 + 1, FR, (z0 + z1) // 2, stair("dark_oak_stairs", "east"))
    for x in range(x0 + 7, x1 - 2):
        if x % 3 == 0:
            continue
        bp.set(x, FR, -67, "spruce_fence")
        bp.set(x, FR + 1, -67, "spruce_pressure_plate")
        bp.set(x, FR, -65, "spruce_fence")
        bp.set(x, FR + 1, -65, "spruce_pressure_plate")
    hx = -20
    for x in range(hx - 2, hx + 3):
        for y in range(FR, FR + 5):
            bp.set(x, y, z0 + 1, SB if abs(x - hx) == 2 or y == FR + 4 else "air")
    bp.set(hx, FR, z0 + 1, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    bp.set(hx - 1, FR, z0 + 1, "air")
    bp.set(hx + 1, FR, z0 + 1, "air")
    for x in range(hx - 1, hx + 2):
        bp.set(x, FR + 3, z0 + 1, SB)
    bp.chest(x0 + 2, FR, z0 + 1, "south", loot=LOOT + "caldera_hall")
    bp.chest(x0 + 2, FR, z1 - 1, "north", loot=LOOT + "caldera_hall")
    bp.spawner(x0 + 6, FR, z0 + 2, MOB_KNIGHT)
    for z in (z0 + 3, z1 - 3):
        banner(bp, x0 + 1, FR + 6, z, "east")


def kitchen(bp):
    x0, x1, z0, z1 = 26, 34, -70, -61
    top = FR + 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            bp.set(x, RIM, z, SB if wall else "bricks")
            for y in range(FR, top):
                bp.set(x, y, z, wall_block(x, y, z, y1=top) if wall else "air")
            bp.set(x, top, z, "spruce_planks")
    for x in range(x0 + 2, x0 + 5):
        for y in range(FR, FR + 4):
            bp.set(x, y, z1, "air")
    steep_pyramid(bp, x0, z0, x1, z1, top + 1, SLATE, SLATE_ST, steep=1, overhang=1)
    bp.set(x1 - 1, FR, z0 + 1, "smoker[facing=south,lit=false]")
    bp.set(x1 - 2, FR, z0 + 1, "furnace[facing=south,lit=false]")
    bp.set(x1 - 3, FR, z0 + 1, "crafting_table")
    bp.set(x0 + 1, FR, z0 + 1, "barrel[facing=up,open=false]")
    bp.set(x0 + 1, FR, z0 + 2, "barrel[facing=up,open=false]")
    bp.set(x0 + 1, FR + 1, z0 + 1, "barrel[facing=up,open=false]")
    bp.set(x1 - 1, FR, z1 - 2, "water_cauldron[level=3]")
    bp.chain(30, top - 1, -66, top - 1)
    bp.set(30, top - 2, -66, LANT_H)
    # chimney
    for y in range(FR, top + 8):
        bp.set(x1 - 1, y, z0 - 1, "bricks")
    bp.set(x1 - 1, top + 8, z0 - 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


# ------------------------------------------------------------------ the undercroft
def undercroft(bp):
    # the stair down from the hub (feet FR -> FB), x 22..24
    for i in range(13):
        f = FR - i
        z = -57 - i
        for x in range(22, 25):
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
            if i == 0:
                bp.set(x, f - 1, z, PA)
            else:
                bp.set(x, f - 1, z, stair(SB_ST, "south"))
            bp.set(x, f - 2, z, SB)
    for z in range(-73, -69):
        for x in range(12, 25):
            bp.set(x, FB - 1, z, SB if hash01(x, z, 3) < 0.8 else CR)
            for y in range(FB, FB + 4):
                bp.set(x, y, z, "air")
    # the cistern hall: 23 x 13, 7 high, piers on a grid, water channels in the floor
    for x in range(-11, 12):
        for z in range(-73, -60):
            ch = z in (-67,) and abs(x) > 2
            bp.set(x, FB - 1, z, "water" if ch else (PA if abs(x) <= 1 else (SB if hash01(x, z, 5) < 0.75
                                                                               else CR)))
            if ch:
                bp.set(x, FB - 2, z, SB)
            for y in range(FB, FB + 7):
                bp.set(x, y, z, "air")
    for px in (-8, -4, 4, 8):
        for pz in (-70, -64):
            for y in range(FB, FB + 7):
                for dx in (0, 1):
                    for dz in (0, 1):
                        bp.set(px + dx - (1 if px < 0 else 0), y, pz + dz, PA if y in (FB, FB + 6) else SB)
    for (lx, lz) in ((-6, -67), (6, -67), (0, -71), (0, -63)):
        bp.chain(lx, FB + 5, lz, FB + 6)
        bp.set(lx, FB + 4, lz, LANT_H)
    bp.spawner(-6, FB, -71, MOB_CRAWLER)
    bp.chest(10, FB, -72, "west", loot=LOOT + "caldera_undercroft")
    bp.set(10, FB, -61, "barrel[facing=up,open=false]")
    bp.set(9, FB, -61, "barrel[facing=up,open=false]")
    # the passage north to the ladder (shortcut up into the great tower)
    for z in range(-78, -73):
        for x in range(3, 6):
            bp.set(x, FB - 1, z, SB)
            for y in range(FB, FB + 4):
                bp.set(x, y, z, "air")
    bp.ladder(4, FB, -78, RIM - 1, "south")
    bp.set(4, FB - 1, -78, SB)
    # the bridge gallery along the crater face: arches on the lake, the bridge in the middle
    for x in range(-15, 13):
        for z in range(-60, -52):
            bp.set(x, FB - 1, z, PA if abs(x) <= 2 else (SB if hash01(x, z, 7) < 0.8 else MO))
            for y in range(FB, FB + 6):
                bp.set(x, y, z, "air")
            bp.set(x, FB + 6, z, SB)
    for x in range(-15, 13):
        for z in range(-52, -48):
            if math.hypot(x - LCX, z - LCZ) < R_LAKE + 1:
                continue
            for y in range(FB - 1, FB + 7):
                bp.set(x, y, z, "air")
    zf = -52                                    # the arcade front
    for x in range(-16, 14):
        for y in range(FB - 2, FB + 8):
            bp.set(x, y, zf, wall_block(x, y, zf, y0=FB - 2, y1=FB + 8))
        bp.set(x, FB + 8, zf, SB_W if x % 2 else SB)
    prof = pointed_arch(2.2, 5)
    for c in (-12, -6, 0, 6, 11):
        hw = 2 if c == 0 else 1
        for u in range(-hw, hw + 1):
            hgt = int(prof(u * (2 / max(hw, 1)))) if c else int(pointed_arch(3.0, 5)(u))
            for y in range(FB, FB + max(3, hgt)):
                bp.set(c + u, y, zf, "air")
            if c != 0:
                bp.set(c + u, FB, zf, SB_W)
    for x in range(-15, 13):
        bp.set(x, FB - 1, zf, SB)
    bp.set(-9, FB, -59, "lectern[facing=south,has_book=false,powered=false]")
    for (lx, lz) in ((-9, -56), (9, -56)):
        bp.set(lx, FB + 5, lz, "iron_chain[axis=y,waterlogged=false]")
        bp.set(lx, FB + 4, lz, LANT_H)
    # the prison: a corridor west of the hall, cells with bars, the hidden ossuary under the last one
    for x in range(-25, -11):
        for z in range(-73, -60):
            bp.set(x, FB - 1, z, SB if hash01(x, z, 8) < 0.7 else ("cobblestone" if hash01(x, z, 9) < 0.5 else MO))
            for y in range(FB, FB + 5):
                corridor = -68 <= z <= -66
                cellwall = (x - -25) % 4 == 0 or z in (-73, -61, -60) or (not corridor and z in (-69, -65))
                if corridor:
                    bp.set(x, y, z, "air")
                elif cellwall:
                    bp.set(x, y, z, SB if y < FB + 4 else SB)
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, FB + 5, z, SB)
    for x in range(-25, -11):
        for z in (-69, -65):
            if (x - -25) % 4 != 0:
                for y in range(FB, FB + 4):
                    bp.set(x, y, z, "iron_bars")
                if (x - -25) % 4 == 2:
                    bp.set(x, FB, z, "air")
                    bp.set(x, FB + 1, z, "air")
    for x in range(-12, -10):
        for z in range(-68, -65):
            for y in range(FB, FB + 4):
                bp.set(x, y, z, "air")
    for x in range(-24, -11, 4):
        bp.set(x + 1, FB, -72, "bone_block[axis=y]") if x != -24 else None
        bp.set(x + 2, FB, -62, "cobweb") if x != -24 else None
    bp.spawner(-18, FB, -67, MOB_SKELETON)
    bp.chain(-18, FB + 4, -66, FB + 4)
    bp.set(-18, FB + 3, -66, LANT_H)
    # the secret: a hatch in the far west cell, a ladder down to the ossuary (feet FB - 7)
    bp.set(-23, FB - 1, -71, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(FB - 7, FB - 1):
        bp.set(-23, y, -71, "ladder[facing=north,waterlogged=false]")
    bp.set(-23, FB - 8, -71, SB)
    for x in range(-25, -16):
        for z in range(-80, -73):
            bp.set(x, FB - 8, z, "bone_block[axis=y]" if hash01(x, z, 3) < 0.25 else "cobblestone")
            for y in range(FB - 7, FB - 3):
                bp.set(x, y, z, "air")
            bp.set(x, FB - 3, z, SB)
    for x in range(-24, -21):
        for z in range(-73, -70):
            bp.set(x, FB - 8, z, "cobblestone")
            for y in range(FB - 7, FB - 3):
                bp.set(x, y, z, "air")
            if (x, z) != (-23, -71):
                bp.set(x, FB - 3, z, SB)
    for y in range(FB - 7, FB - 1):
        bp.set(-23, y, -71, "ladder[facing=north,waterlogged=false]")
    for x in range(-25, -16):
        bp.set(x, FB - 7, -80, "bone_block[axis=x]")
        bp.set(x, FB - 6, -80, "skeleton_skull[rotation=0]" if x % 3 == 0 else "bone_block[axis=x]")
    bp.chest(-21, FB - 7, -78, "south", loot=LOOT + "caldera_hoard")
    bp.set(-19, FB - 7, -78, "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(-24, FB - 7, -76, "candle[candles=2,lit=true,waterlogged=false]")


def dock_stair(bp):
    """The newel stair from the bridge gallery's west end down to the strand, and the jetty."""
    x0, z0 = -24, -62
    flights = [3, 3, 3, 3, 3, 3, 2]
    cells, core, top_c, top_f = newel_laps(bp, x0, z0, 3, FS, flights, 2)
    assert top_f == FB and top_c == 1, (top_f, top_c)
    tx, tz = {0: (x0, z0), 1: (x0 + 6, z0), 2: (x0 + 6, z0 + 6), 3: (x0, z0 + 6)}[top_c]
    # the top landing joins the gallery (x -15) on the east
    for x in range(x0 + 9, -14):
        for z in range(tz, tz + 3):
            bp.set(x, FB - 1, z, SB)
            for y in range(FB, FB + 4):
                bp.set(x, y, z, "air")
    for x in range(x0 + 9, -14):
        for z in range(z0 + 4, z0 + 9):
            pass
    # bottom: the passage south to the strand
    for z in range(z0 + 9, -42):
        for x in range(-18, -15):
            bp.set(x, FS - 1, z, SB if hash01(x, z, 2) < 0.7 else MO)
            for y in range(FS, FS + 4):
                bp.set(x, y, z, "air")
    # the jetty into the lake
    for z in range(-46, -37):
        for x in range(-18, -15):
            if math.hypot(x - LCX, z - LCZ) < R_LAKE + 0.5:
                bp.set(x, LAKE, z, "spruce_planks")
        for x in (-19, -15):
            if math.hypot(x - LCX, z - LCZ) < R_LAKE + 0.5 and z % 3 == 0:
                for y in range(LAKE - 3, LAKE + 2):
                    bp.set(x, y, z, "spruce_log[axis=y]")
    bp.set(-19, LAKE + 2, -39, LANT)


# ------------------------------------------------------------------ the bridge
BR_Z0, BR_Z1 = -53, -13           # deck from the gallery front to the needle gate
PIERS = (-42, -27)


def bridge(bp):
    deck = FB - 1
    for z in range(BR_Z0, BR_Z1 + 1):
        for x in range(-3, 4):
            edge = abs(x) == 3
            bp.set(x, deck, z, SB if edge else (PA if x == 0 else (SB if hash01(x, z, 5) < 0.8 else CR)))
            bp.set(x, deck - 1, z, SB)
            for y in range(FB, FB + 4):
                bp.set(x, y, z, "air")
            if edge:
                bp.set(x, FB, z, SB_W)
                if (z - BR_Z0) % 6 == 3:
                    bp.set(x, FB, z, SB)
                    bp.set(x, FB + 1, z, LANT)
        # corbels under the parapets
        for x in (-4, 4):
            bp.set(x, deck - 1, z, stair(SB_ST, "east" if x < 0 else "west", "top"))
    # arches between the supports (the gallery front, two piers, the needle)
    supports = [(BR_Z0 - 2, BR_Z0)] + [(p - 2, p + 2) for p in PIERS] + [(BR_Z1, BR_Z1 + 3)]
    for (a0, a1), (b0, b1) in zip(supports, supports[1:]):
        za, zb = a1, b0
        zc, w = (za + zb) / 2, (zb - za) / 2
        for z in range(za, zb + 1):
            u = (z - zc) / max(w, 1)
            y_in = int(22 + 7.5 * math.sqrt(max(0.0, 1 - u * u)))
            for x in range(-3, 4):
                for y in range(y_in, deck - 1):
                    bp.set(x, y, z, SB if hash3(x, y, z, 4) < 0.85 else MO)
    for p in PIERS:
        for x in range(-4, 5):
            for z in range(p - 2, p + 3):
                for y in range(max(0, hmap(x, z) - 1), deck - 1):
                    if y < 22 and (abs(x) == 4 or z in (p - 2, p + 2)) and y > LAKE - 1:
                        spec = DB if y < 16 else SB
                    elif y <= LAKE:
                        spec = DB if hash3(x, y, z, 2) < 0.7 else CD
                    else:
                        spec = SB
                    bp.set(x, y, z, spec)
        # cutwaters
        for s in (-1, 1):
            for y in range(LAKE - 3, LAKE + 4):
                bp.set(0, y, p + s * 3, DB)
                bp.set(0, LAKE + 4, p + s * 3, stair("deepslate_brick_stairs", "north" if s > 0 else "south"))
    # the bridge tower on the first pier: a gate 3 wide (compression), a red roof
    p = PIERS[0]
    for x in range(-4, 5):
        for z in range(p - 3, p + 4):
            wall = abs(x) >= 2
            for y in range(FB, FB + 12):
                if wall:
                    bp.set(x, y, z, wall_block(x, y, z, y0=FB, y1=FB + 12))
                elif y >= FB + 4:
                    bp.set(x, y, z, SB)
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, FB + 12, z, SB)
            if abs(x) == 4 or z in (p - 3, p + 3):
                bp.set(x, FB + 13, z, SB if (x + z) % 2 else SB_W)
    for z in (p - 3, p + 3):
        for x in range(-1, 2):
            bp.set(x, FB + 4, z, CH if x == 0 else PA)
    steep_pyramid(bp, -3, p - 2, 3, p + 2, FB + 13, ROOF, ROOF_ST, steep=2, overhang=0, finial="lightning_rod")
    bp.set(0, FB + 3, p, LANT_H)


def broken_bridge(bp):
    """The west bridge that never reached the needle: one pier, a deck ending in a collapse (a rail at the edge)."""
    deck = RIM
    xa, xb = -59, -45
    for x in range(xa - 3, xb + 1):
        if math.hypot(x - LCX, 6 - LCZ) > EDGE_AT(x, 6) + 1:
            continue
        ragged = x > xb - 3
        for z in range(3, 10):
            edge = z in (3, 9)
            if ragged and hash01(x, z, 4) < (x - (xb - 3)) / 3.5:
                continue
            bp.set(x, deck, z, SB if edge else (PA if z == 6 else SB))
            bp.set(x, deck - 1, z, SB)
            for y in range(FR, FR + 3):
                bp.set(x, y, z, "air")
            if edge:
                bp.set(x, FR, z, SB_W)
        if not ragged:
            pass
    for z in range(4, 9):
        bp.set(xb - 3, FR, z, SB_W)                # the rail where the deck ends
    for z in range(3, 10):
        for x in range(xa, xb - 3):
            u = (x - (xa + xb - 3) / 2) / ((xb - 3 - xa) / 2)
            y_in = int(28 + 12 * math.sqrt(max(0.0, 1 - u * u)))
            if abs(x - -52) > 2:
                for y in range(y_in, deck - 1):
                    bp.set(x, y, z, SB if hash3(x, y, z, 6) < 0.8 else MO)
    for x in range(-54, -49):
        for z in range(3, 10):
            for y in range(max(0, hmap(x, z) - 1), deck - 1):
                bp.set(x, y, z, DB if y <= LAKE + 2 else (SB if hash3(x, y, z, 7) < 0.8 else MO))
    # fallen blocks in the lake under the break
    for (x, z) in ((-43, 5), (-42, 8), (-44, 7)):
        for y in range(LAKE - 2, LAKE + 1):
            bp.set(x, y, z, SB if hash3(x, y, z, 9) < 0.5 else MO)


# ------------------------------------------------------------------ the needle and the summit
def needle_inside(bp):
    # the gate vestibule (feet FB) from the bridge to the newel shaft
    for x in range(-5, 3):
        for z in range(-16, -1):
            bp.set(x, FB - 1, z, PA if -2 <= x <= 2 and z < -8 or x <= -3 else SB)
            for y in range(FB, FB + 5):
                bp.set(x, y, z, "air")
    # the gate in the needle's face: an arch, the gate leaves open
    for x in range(-3, 4):
        for z in range(-14, -11):
            if abs(x) == 3:
                for y in range(FB, FB + 6):
                    bp.set(x, y, z, PA if z == -14 else SB)
    for x in range(-2, 3):
        bp.set(x, FB + 5, -14, CH if x == 0 else PA)
        bp.set(x, FB + 4, -13, "air")
    for (lx, lz) in ((-4, -9), (1, -5)):
        bp.chain(lx, FB + 4, lz, FB + 4)
        bp.set(lx, FB + 3, lz, LANT_H)
    bp.set(-5, FB, -15, "barrel[facing=up,open=false]")
    # the newel stair: 9 flights of 5 from feet FB to FL
    # one lap (four flights) per call: a lap reuses the same columns 20 blocks higher
    cells, core, c, f = newel_laps(bp, -5, -1, 5, FB, [5] * 9, 0, core_spec="tuff_bricks")
    assert f == FL and c == 1, (f, c)
    # the guard room off the SE landing (feet 43)
    for x in range(6, 13):
        for z in range(3, 11):
            room = 7 <= x <= 12 and 4 <= z <= 10
            if room:
                bp.set(x, 42, z, SB if hash01(x, z, 4) < 0.8 else CR)
                for y in range(43, 47):
                    bp.set(x, y, z, "air")
                bp.set(x, 47, z, SB)
    for z in range(7, 10):
        for y in range(43, 47):
            bp.set(6, y, z, "air")
    bp.chest(12, 43, 4, "west", loot=LOOT + "caldera_needle")
    bp.set(12, 43, 10, "barrel[facing=up,open=false]")
    bp.spawner(10, 43, 5, MOB_KNIGHT)
    bp.chain(9, 46, 7, 46)
    bp.set(9, 45, 7, LANT_H)
    # loopholes: windows from the landings over the lake
    for (x, y, z, dx, dz) in ((-6, 54, 0, -1, 0), (6, 59, 0, 1, 0), (0, 66, 10, 0, 1), (-6, 69, 9, -1, 0)):
        for k in range(1, 9):
            px, pz = x + dx * k, z + dz * k
            for yy in (y, y + 1):
                bp.set(px, yy, pz, "air")
    # the passage at the top (feet FL) north to the keep's lower room
    for z in range(-6, -1):
        for x in range(3, 6):
            bp.set(x, FL - 1, z, SB)
            for y in range(FL, FL + 4):
                bp.set(x, y, z, "air")


def platform_cells():
    """(x, z) of the summit platform: the keep, the passage, the arena with its parapet, the vault turret."""
    cells = set()
    for x in range(KX0, KX1 + 1):
        for z in range(KZ0, KZ1 + 1):
            cells.add((x, z))
    for x in range(-2, 3):
        for z in range(KZ1, 4):
            cells.add((x, z))
    for x, z, d in disc(AC[0], AC[1], AR + 2.6):
        cells.add((x, z))
    for x in range(-5, 6):
        for z in range(AC[1] + AR + 1, AC[1] + AR + 12):
            cells.add((x, z))
    return cells


def needle_rock_top(x, z):
    rx, kz, cz = needle_shape(NEEDLE_TOP)
    return ((x / rx) ** 2 + ((z - cz) / (rx * kz)) ** 2) <= 0.92


def summit_platform(bp):
    """The podium over the rock top (y NEEDLE_TOP+1 .. FT-1) and the corbels under the overhangs."""
    cells = platform_cells()
    rx, kz, cz = needle_shape(NEEDLE_TOP)
    rz = rx * kz
    for (x, z) in cells:
        e = math.sqrt((x / rx) ** 2 + ((z - cz) / rz) ** 2)
        over = max(0.0, (e - 0.92) * rx)            # distance beyond the rock edge (approx.)
        edge = any((x + dx, z + dz) not in cells for dx, dz in DIRS.values())
        y_bot = int(NEEDLE_TOP - over * 2.2) if over > 0 else NEEDLE_TOP - 2
        rib = (int(math.degrees(math.atan2(x, z - 12)) // 15) % 2 == 0) and over > 1
        if rib:
            y_bot -= 4
        y_bot = max(30, y_bot)
        for y in range(y_bot, FT - 1):
            under = y < y_bot + 2
            if edge or under or y >= FT - 3 or y == NEEDLE_TOP:
                if y == FT - 4:
                    spec = PA
                elif under and over > 0:
                    spec = DB if hash3(x, y, z, 3) < 0.6 else DT
                else:
                    spec = wall_block(x, y, z, y0=y_bot, y1=FT)
                bp.set(x, y, z, spec)


def keep(bp):
    """The keep: lower room (feet FL), the hall of grace (feet FT), three upper floors, the roof walk, the copper spire."""
    x0, z0, x1, z1 = KX0, KZ0, KX1, KZ1
    ix0, iz0, ix1, iz1 = x0 + 2, z0 + 2, x1 - 2, z1 - 2      # -6..6, -18..-6
    wall_top = 123
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = not (ix0 <= x <= ix1 and iz0 <= z <= iz1)
            if wall:
                for y in range(FL - 1, wall_top + 1):
                    if y in (FT - 1, 103, wall_top):
                        spec = PA
                    elif x in (x0, x1) and z in (z0, z1):
                        spec = SB if (y // 2) % 2 else PA          # quoins
                    else:
                        spec = wall_block(x, y, z, y0=FL, y1=wall_top)
                    bp.set(x, y, z, spec)
            else:
                bp.set(x, FL - 1, z, SB)
                for y in range(FL, FL + 5):
                    bp.set(x, y, z, "air")
                bp.set(x, FT - 1, z, "spruce_planks" if (x + z) % 4 else "dark_oak_planks")
                for f in K_FLOORS[1:]:
                    bp.set(x, f - 1, z, "spruce_planks" if (x * 3 + z) % 5 else "stripped_dark_oak_log[axis=x]")
                for i, f in enumerate(K_FLOORS[:-1]):
                    for y in range(f, K_FLOORS[i + 1] - 1):
                        bp.set(x, y, z, "air")
                for y in range(K_FLOORS[-1], K_FLOORS[-1] + 4):
                    bp.set(x, y, z, "air")
    # stairs: lower room -> hall (west, north), then alternate east / west, 10 steps each
    def flight(xs, zs_from, f0, n, facing, landing_rows):
        cells = []
        dz = -1 if facing == "north" else 1
        for i in range(1, n + 1):
            z = zs_from + dz * (i - 1)
            for x in xs:
                bp.set(x, f0 + i - 1, z, stair(SB_ST, facing))
                for y in range(f0 + i, f0 + i + 4):
                    bp.set(x, y, z, "air")
                cells.append((x, z))
        return cells

    holes = []
    holes.append(flight(range(ix0, ix0 + 3), -8, FL, 6, "north", None))
    for x in range(ix0, ix0 + 3):
        for z in range(-8, -14, -1):
            for y in range(FL, (FL + 6) - (z + 8) - 1 + 1):
                pass
    # fill under the lower flight
    for i, z in enumerate(range(-8, -14, -1)):
        for x in range(ix0, ix0 + 3):
            for y in range(FL, FL + i):
                bp.set(x, y, z, SB)
    holes.append(flight(range(ix1 - 2, ix1 + 1), -7, FT, 10, "north", None))
    holes.append(flight(range(ix0, ix0 + 3), -16, 94, 10, "south", None))
    holes.append(flight(range(ix1 - 2, ix1 + 1), -7, 104, 10, "north", None))
    holes.append(flight(range(ix0, ix0 + 3), -16, 114, 10, "south", None))
    # open the floor above each flight, and rail the opening
    above = {0: FT - 1, 1: 93, 2: 103, 3: 113, 4: 123}
    for j, cells in enumerate(holes):
        y = above[j]
        for (x, z) in cells:
            if not (bp.get(x, y, z) or "").endswith("_stairs"):      # the last step stays: it is the landing edge
                bp.set(x, y, z, "air")
        for (x, z) in cells:
            for dx, dz in DIRS.values():
                q = (x + dx, z + dz)
                if q in cells or not (ix0 <= q[0] <= ix1 and iz0 <= q[1] <= iz1):
                    continue
                if bp.get(q[0], y, q[1]) not in (None, "minecraft:air"):
                    bp.set(q[0], y + 1, q[1], "spruce_fence")
    # the landings at the top of each flight stay free of rails
    for (xs, zz, y) in ((range(ix0, ix0 + 3), -14, FT), (range(ix1 - 2, ix1 + 1), -17, 94),
                        (range(ix0, ix0 + 3), -6, 104), (range(ix1 - 2, ix1 + 1), -17, 114),
                        (range(ix0, ix0 + 3), -6, 124)):
        for x in xs:
            for z in (zz, zz - 1 if zz < -10 else zz + 1):
                if iz0 <= z <= iz1 and bp.get(x, y, z) == "minecraft:spruce_fence":
                    bp.set(x, y, z, "air")
    # roof walk: parapet with merlons, corner bartizans, the copper spire
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            ring = max(abs(x - (x0 + x1) / 2), abs(z - (z0 + z1) / 2))
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, wall_top - 1, z, stair(SB_ST, inward(x - (x0 + x1) / 2, z - (z0 + z1) / 2), "top"))
                bp.set(x, wall_top, z, SB)
                merlon(bp, x, wall_top + 1, z, x + z)
            elif x in (x0, x1) or z in (z0, z1):
                bp.set(x, wall_top, z, SB)
    for (bx, bz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for x, z, d in disc(bx, bz, 2.6):
            for y in range(wall_top - 6, wall_top + 8):
                if y < wall_top - 3:
                    if d < 2.6 - (wall_top - 3 - y):
                        bp.set(x, y, z, SB)
                elif d > 1.5 or y >= wall_top + 6:
                    bp.set(x, y, z, SB if y != wall_top + 6 else PA)
            if d > 1.5:
                for y in (wall_top + 3, wall_top + 4):
                    if (x + z) % 2 == 0:
                        bp.set(x, y, z, "air")
        cone(bp, bx, bz, wall_top + 8, 3, ROOF, ROOF_ST, steep=2)
    # the spire over the inner bay (green copper), its gold finial
    yy = steep_pyramid(bp, ix0 + 3, iz0 + 2, ix1 - 3, iz1 - 2, wall_top + 1, COP, COP_ST, steep=3, overhang=0)
    cxk, czk = (x0 + x1) // 2, (z0 + z1) // 2
    for y in range(yy, yy + 6):
        bp.set(cxk, y, czk, COP if y < yy + 3 else "gold_block")
    bp.set(cxk, yy + 6, czk, "lightning_rod")
    # the roof walk must stay walkable round the spire: clear its first ring at the edge
    for x in range(ix0, ix1 + 1):
        for z in range(iz0, iz1 + 1):
            if x in (ix0, ix1) or z in (iz0, iz1):
                for y in range(K_FLOORS[-1], K_FLOORS[-1] + 4):
                    bp.set(x, y, z, "air")
    # windows: tall slits on every floor, a balcony on the hall's west side
    for f in K_FLOORS[:-1]:
        for (wx, wz, ax) in ((0, z0, "z"), (0, z1, "z"), (x0, -12, "x"), (x1, -12, "x")):
            for y in range(f + 1, f + 4):
                for dd in (0, 1):
                    if ax == "z":
                        bp.set(wx, y, wz + (dd if wz == z0 else -dd), "glass_pane" if dd == 0 else "air")
                    else:
                        bp.set(wx + (dd if wx == x0 else -dd), y, wz, "glass_pane" if dd == 0 else "air")
    # the hall of grace (feet FT): the south door to the passage, the waystone, banners, chandelier
    for x in range(-1, 2):
        for z in range(z1 - 1, z1 + 1):
            for y in range(FT, FT + 4):
                bp.set(x, y, z, "air")
            bp.set(x, FT - 1, z, PA)
    bp.set(-4, FT, -9, MOD["waystone"])
    stone_lantern(bp, -4, FT, -16)
    for z in (-15, -9):
        banner(bp, ix1, FT + 4, z, "west")
    bp.chain(0, FT + 7, -12, 92)
    bp.set(0, FT + 6, -12, LANT_H)
    # the lower room opens south onto the passage from the needle stair (x 3..5, feet FL)
    for x in range(3, 6):
        for z in range(z1 - 1, z1 + 2):
            bp.set(x, FL - 1, z, SB)
            for y in range(FL, FL + 4):
                bp.set(x, y, z, "air")
        bp.set(x, FL + 4, z1, PA)
    # the lower room: guards' room, barrels
    bp.set(ix1, FL, iz0, "barrel[facing=up,open=false]")
    bp.set(ix1, FL, iz0 + 1, "barrel[facing=up,open=false]")
    bp.chain(0, FL + 4, -12, FL + 4)
    bp.set(0, FL + 3, -12, LANT_H)
    # floor 2 (feet 94): the castellan's chamber
    bp.bed(-3, 94, -8, "north", color="blue")
    bp.chest(2, 94, -8, "south", loot=LOOT + "caldera_keep")
    bp.set(-1, 94, -8, "barrel[facing=up,open=false]")
    bp.set(0, 94, -16, "crafting_table")
    bp.chain(0, 102, -12, 102)
    bp.set(0, 101, -12, LANT_H)
    # floor 3 (feet 104): map room
    bp.set(0, 104, -12, "cartography_table")
    bp.set(1, 104, -12, "lectern[facing=west,has_book=false,powered=false]")
    for x in range(-2, 3):
        bp.set(x, 104, -17, "bookshelf")
        bp.set(x, 105, -17, "bookshelf")
    bp.chain(0, 112, -10, 112)
    bp.set(0, 111, -10, LANT_H)
    # floor 4 (feet 114): the watch, gargoyles roost here
    bp.spawner(0, 114, -12, MOB_GARGOYLE)
    bp.chain(-3, 122, -12, 122)
    bp.set(-3, 121, -12, LANT_H)
    bp.set(3, 114, -9, "barrel[facing=up,open=false]")


def arena(bp):
    """The arena: an open court r 16 on the platform, a crenellated parapet, four red turrets; the passage and the
    mist from the keep; the vault turret behind sealed bars and its leap balcony."""
    cx, cz = AC
    for x, z, d in disc(cx, cz, AR + 2.6):
        if d <= AR + 0.5:
            ring = int(d)
            if d < 1.2:
                spec = CH
            elif ring in (5, 11):
                spec = "calcite"
            elif ring % 2 == 0:
                spec = PA
            else:
                spec = SB if hash01(x, z, 3) < 0.85 else CR
            bp.set(x, FT - 1, z, spec)
            for y in range(FT, FT + 6):
                bp.set(x, y, z, "air")
        else:
            bp.set(x, FT - 1, z, SB)
            if d <= AR + 1.6:
                ang = math.atan2(x - cx, z - cz)
                if int((ang + math.pi) * 8) % 3 == 0:
                    bp.set(x, FT, z, SB)
                    bp.set(x, FT + 1, z, SB)
                    bp.set(x, FT + 2, z, SB_SL + "[type=bottom,waterlogged=false]")
                else:
                    bp.set(x, FT, z, SB_W)
            else:
                bp.set(x, FT, z, SB)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        tx, tz = round(cx + 18.0 * math.sin(a)), round(cz + 18.0 * math.cos(a))
        for x, z, d in disc(tx, tz, 2.6):
            for y in range(FT - 4, FT + 8):
                bp.set(x, y, z, SB if d > 1.4 or y < FT or y == FT + 7 else ("air" if y < FT + 7 else SB))
            if d <= 1.4:
                bp.set(x, FT - 1, z, SB)
        for y in range(FT - 8, FT - 4):
            for x, z, d in disc(tx, tz, 2.6 - (FT - 4 - y) * 0.6):
                bp.set(x, y, z, SB)
        cone(bp, tx, tz, FT + 8, 3, ROOF, ROOF_ST, steep=2)
    bp.boss_seal(cx, FT - 1, cz, BOSS, AR - 1)
    # braziers round the arena edge
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        x, z = round(cx + 14.5 * math.sin(a)), round(cz + 14.5 * math.cos(a))
        bp.set(x, FT, z, PA)
        bp.set(x, FT + 1, z, LANT)
    # the passage from the keep: 3 wide, 4 high, 6 long, roofed (compression before the arena)
    for z in range(KZ1 + 1, cz - AR + 1):
        for x in range(-2, 3):
            if abs(x) == 2:
                for y in range(FT, FT + 5):
                    bp.set(x, y, z, wall_block(x, y, z, y0=FT, y1=FT + 5))
            else:
                bp.set(x, FT - 1, z, PA)
                for y in range(FT, FT + 4):
                    bp.set(x, y, z, "air")
            bp.set(x, FT + 4, z, SB)
            bp.set(x, FT + 5, z, SB_SL + "[type=bottom,waterlogged=false]")
    bp.set(0, FT + 3, KZ1 + 3, LANT_H)
    zm = cz - AR + 1
    bp.mist(-1, FT, zm, 1, FT + 3, zm)
    # the vault turret south of the arena, behind sealed bars
    zv0, zv1 = cz + AR + 2, cz + AR + 10           # inner box z (37 .. 45)
    for x in range(-5, 6):
        for z in range(zv0 - 2, zv1 + 2):
            wall = abs(x) >= 4 or z < zv0 or z > zv1
            for y in range(FT, FT + 8):
                if wall:
                    bp.set(x, y, z, wall_block(x, y, z, y0=FT, y1=FT + 8))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, FT - 1, z, SB if wall else ("red_carpet" if False else PA))
            bp.set(x, FT + 8, z, SB)
    steep_pyramid(bp, -5, zv0 - 2, 5, zv1 + 1, FT + 9, ROOF, ROOF_ST, steep=2, overhang=1, finial="lightning_rod")
    for x in range(-1, 2):
        for z in range(cz + AR, zv0):
            bp.set(x, FT - 1, z, PA)
            for y in range(FT, FT + 3):
                bp.set(x, y, z, "air")
            bp.set(x, FT + 3, z, SB)
        bp.set(x, FT, zv0 - 1, MOD["vault_bars"])
        bp.set(x, FT + 1, zv0 - 1, MOD["vault_bars"])
        bp.set(x, FT + 2, zv0 - 1, MOD["vault_bars"])
    bp.chest(-3, FT, zv0 + 2, "east", loot=LOOT + "caldera_vault")
    bp.chest(3, FT, zv0 + 2, "west", loot=LOOT + "caldera_vault")
    bp.set(0, FT, zv0 + 4, CH)
    bp.set(0, FT + 1, zv0 + 4, "candle[candles=4,lit=true,waterlogged=false]")
    bp.chain(0, FT + 6, zv0 + 2, FT + 7)
    bp.set(0, FT + 5, zv0 + 2, LANT_H)
    # the leap: a door in the south wall onto a balcony with a gap in its rail (the lake is below)
    for x in range(-1, 2):
        for z in (zv1 + 1,):
            for y in range(FT, FT + 3):
                bp.set(x, y, z, "air")
            bp.set(x, FT - 1, z, PA)
    for x in range(-2, 3):
        for z in range(zv1 + 2, zv1 + 4):
            bp.set(x, FT - 1, z, "spruce_planks")
            bp.set(x, FT - 2, z, stair("spruce_stairs", "north", "top"))
            for y in range(FT, FT + 4):
                bp.set(x, y, z, "air")
    for z in range(zv1 + 2, zv1 + 4):
        bp.set(-3, FT, z, "dark_oak_fence")
        bp.set(3, FT, z, "dark_oak_fence")
    for x in (-2, -1, 1, 2):
        bp.set(x, FT, zv1 + 4, "dark_oak_fence")
    bp.set(-3, FT + 1, zv1 + 3, LANT)
    bp.set(3, FT + 1, zv1 + 3, LANT)


# ------------------------------------------------------------------ the west ward: the ruined chapel
def chapel(bp):
    x0, x1, z0, z1 = -77, -67, 12, 30
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if math.hypot(x, z) > R_WALL - 2.6:
                continue
            wall = x in (x0, x1) or z in (z0, z1)
            bp.set(x, RIM, z, SB if wall else ("mossy_cobblestone" if hash01(x, z, 4) < 0.3 else SB))
            # ruin: walls lose height towards the north-east corner
            hgt = int(9 - 6 * hash01(x // 2, z // 2, 5) * (z - z0) / (z1 - z0))
            if wall:
                for y in range(FR, FR + max(2, hgt)):
                    bp.set(x, y, z, wall_block(x, y, z, y1=FR + 9))
            else:
                for y in range(FR, FR + 4):
                    bp.set(x, y, z, "air")
    for z in range(z0 + 3, z1 - 1, 4):
        for y in range(FR + 2, FR + 6):
            if bp.get(x1, y, z) not in (None, "minecraft:air"):
                bp.set(x1, y, z, "air")
    for x in range(-73, -70):
        for y in range(FR, FR + 4):
            bp.set(x, y, z0, "air")
    bp.set(-72, FR, z1 - 2, CH)
    bp.set(-72, FR + 1, z1 - 2, "candle[candles=3,lit=true,waterlogged=false]")
    bp.chest(-74, FR, z1 - 2, "north", loot=LOOT + "caldera_ramparts")
    bp.spawner(-70, FR, z1 - 4, MOB_GARGOYLE)
    for z in range(z0 + 3, z1 - 3, 3):
        bp.set(-75, FR, z, stair("spruce_stairs", "south"))
        bp.set(-69, FR, z, stair("spruce_stairs", "south"))
    for (x, z) in ((-71, 18), (-73, 22), (-70, 25)):
        bp.set(x, FR, z, "mossy_cobblestone")
    bp.set(-72, FR + 3, 14, "cobweb")


# ------------------------------------------------------------------ the camp at the foot
def camp(bp):
    cx, cz = polar(140, 113)
    cx, cz = int(round(cx)), int(round(cz)) + 6
    base = max(0, hmap(cx, cz))

    def ground(x, z):
        g = max(0, hmap(x, z))
        return g + 1

    # a tent (wool on fence frame), campfire, waystone, supplies
    tx, tz = cx + 5, cz + 2
    for dz in range(-2, 3):
        for dx in range(-3, 4):
            y0 = ground(tx + dx, tz + dz)
            h = 3 - abs(dz)
            bp.set(tx + dx, y0 - 1, tz + dz, "coarse_dirt")
            if abs(dz) == 2 or dx in (-3,):
                bp.set(tx + dx, y0 + h - 1, tz + dz, "white_wool") if h > 0 else None
            bp.set(tx + dx, y0 + 2, tz, "brown_wool") if abs(dz) == 0 else None
            if abs(dz) == 1:
                bp.set(tx + dx, y0 + 1, tz + dz, "white_wool")
    y0 = ground(cx, cz)
    bp.set(cx, y0 - 1, cz, "cobblestone")
    bp.set(cx, y0, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz) in ((2, 0), (-2, 0), (0, -2)):
        bp.set(cx + dx, ground(cx + dx, cz + dz), cz + dz, stair("spruce_stairs", outward(dx, dz)))
    wx, wz = cx - 4, cz - 3
    bp.set(wx, ground(wx, wz) - 1, wz, "stone_bricks")
    bp.set(wx, ground(wx, wz), wz, MOD["waystone"])
    sx, sz = cx + 1, cz + 5
    bp.chest(sx, ground(sx, sz), sz, "north", loot=LOOT + "caldera_camp")
    bp.set(sx + 1, ground(sx + 1, sz), sz, "barrel[facing=up,open=false]")
    bp.set(sx - 1, ground(sx - 1, sz), sz, "barrel[facing=up,open=false]")
    # the start marker: a stone post with a lantern
    mx, mz = cx - 6, cz + 3
    g = ground(mx, mz)
    for y in range(g, g + 3):
        bp.set(mx, y, mz, MO if y == g else SB)
    bp.set(mx, g + 3, mz, LANT)
    _ = base


# ------------------------------------------------------------------ paths: blocks
def write_path(bp, p, edge_spec=SB_W, centre=PA):
    for (x, z), s in p.cells.items():
        yt = Path.top_y(s)
        for y in range(yt + 1, yt + 5):
            if bp.get(x, y, z) is None or bp.get(x, y, z) != "minecraft:water":
                bp.set(x, y, z, "air")
        if s % 2 == 0:
            bp.set(x, yt, z, centre if hash01(x, z, 3) < 0.5 else ("stone_bricks" if hash01(x, z, 4) < 0.6
                                                                    else "andesite"))
        else:
            bp.set(x, yt, z, (PA_SL if hash01(x, z, 3) < 0.5 else SB_SL) + "[type=bottom,waterlogged=false]")
            if bp.get(x, yt - 1, z) in (None, "minecraft:air"):
                bp.set(x, yt - 1, z, SB)
    for (x, z), s in p.edge.items():
        f = Path.feet(s)
        cur = bp.get(x, f, z)
        if cur not in (None, "minecraft:air"):
            continue
        below = bp.get(x, f - 1, z)
        if below in (None, "minecraft:air"):
            continue
        bp.set(x, f, z, edge_spec)


# ------------------------------------------------------------------ life
def plants(bp, P):
    tops = np.argwhere(P.top & P.shell)
    placed = []
    busy = set(APPROACH.cells) | set(SIDE.cells) | set(APPROACH.edge) | set(SIDE.edge)
    order = sorted(tops.tolist(), key=lambda t: hash3(int(XS[t[0]]), t[1], int(ZS[t[2]]), 55))
    n = 0
    for i, y, k in order:
        x, z = int(XS[i]), int(ZS[k])
        d = math.hypot(x, z)
        if d < R_TOP + 4 or y > 30 or SLOPE[i, k] > 0.9:
            continue
        if any((x + dx, z + dz) in busy for dx in (-3, 0, 3) for dz in (-3, 0, 3)):
            continue
        if abs(x) < 30 and z > 80:
            continue                                   # keep the gate's foreground open
        if any(abs(x - a) < 6 and abs(z - b) < 6 for a, b in placed):
            continue
        if not is_air(bp, x, y + 1, z) or not is_air(bp, x, y + 6, z):
            continue
        h = hash01(x, z, 9)
        if h < 0.7:
            spruce(bp, x, y + 1, z, h=7 + int(h * 7), seed=x * 3 + z)
            bp.set(x, y, z, "podzol[snowy=false]")
        else:
            boulder(bp, x, y + 1, z, r=2, blocks=("andesite", "tuff", "stone", "mossy_cobblestone"), seed=x + z)
        placed.append((x, z))
        n += 1
        if n >= 70:
            break
    # grass tufts and flowers on the bailey and the foot
    for i, y, k in tops.tolist():
        x, z = int(XS[i]), int(ZS[k])
        if bp.get(x, y, z) != "minecraft:grass_block" or not is_air(bp, x, y + 1, z):
            continue
        h = hash3(x, y, z, 61)
        if h < 0.1:
            bp.set(x, y + 1, z, "short_grass")
        elif h < 0.12:
            bp.set(x, y + 1, z, ("cornflower", "oxeye_daisy", "dandelion", "allium")[int(h * 1000) % 4])


# ------------------------------------------------------------------ builder
def caldera_ringwall(bp):
    P = Plan()
    P.rock()
    P.carves()
    P.path(APPROACH)
    P.path(SIDE)
    P.finish()
    write_rock(bp, P)
    write_lake(bp, P)
    write_path(bp, APPROACH)
    write_path(bp, SIDE)
    curtain(bp)
    for k in (1, 3, 5, 7, 9, 11, 13, 15):
        turret(bp, k)
    gt = None
    for k in STAIR_TOWERS:
        c = stair_tower(bp, k)
        if k == 0:
            gt = c
    great_tower_extras(bp, gt)
    west_tower(bp)
    breach(bp)
    east_bastion(bp)
    for k in (2, 6, 10, 14):
        cross_wall(bp, k)
    inner_parapet(bp)
    gatehouse(bp)
    barbican(bp)
    gate_court(bp)
    water_gate(bp)
    barracks(bp)
    hub(bp)
    undercroft(bp)
    dock_stair(bp)
    bridge(bp)
    broken_bridge(bp)
    summit_platform(bp)
    needle_inside(bp)
    keep(bp)
    arena(bp)
    chapel(bp)
    camp(bp)
    plants(bp, P)
    toe(bp)


def toe(bp):
    """A shallow footing under the outer talus only (the global foundation would sink 12 blocks under the whole
    250-block disc): the outer slopes never float over a dip, the interior columns already stand on rock."""
    feet = [(x, z) for (x, y, z), v in list(bp.blocks.items()) if y == 0 and v[0] != "minecraft:air"
            and math.hypot(x, z) > R_FOOT - 10]
    for x, z in feet:
        for d in range(1, 3):
            if bp.get(x, -d, z) is None:
                bp.set(x, -d, z, "dirt" if d == 1 else "stone")


_cx, _cz = polar(140, 113)
VIEWS = [
    ("approach", (int(_cx) - 6, 2, int(_cz) + 2), (0, 70, 20)),
    ("gate_hall", (0, GF, 101), (0, GF + 22, 88)),
    ("gate_court", (0, FR, 80), (0, FT + 20, 0)),
    ("rampart", (int(polar(130, R_WALL)[0]), FW, int(polar(130, R_WALL)[1])),
     (int(polar(70, R_WALL)[0]), FW + 2, int(polar(70, R_WALL)[1]))),
    ("hub", (2, FR, -66), (0, FT + 10, -4)),
    ("undercroft", (0, FB, -72), (0, FB + 2, -55)),
    ("arena", (0, FT, 6), (0, FT + 8, 30)),
]


register(StructureDef(
    "caldera_ringwall", "overworld",
    ["meadow", "grove", "snowy_slopes", "stony_peaks", "windswept_hills", "windswept_gravelly_hills",
     "windswept_forest"],
    [Piece("ringwall", caldera_ringwall, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128,
    foundation=False, spawns=[(MOB_SKELETON, 8, 1, 2), (MOB_KNIGHT, 4, 1, 1), ("brasshaven:magma_sentry", 5, 1, 1)],
    title_fr="Le Rempart de la caldeira", title_en="Caldera Ringwall"))
