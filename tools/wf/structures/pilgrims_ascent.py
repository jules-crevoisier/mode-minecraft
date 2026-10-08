"""Pilgrim's Ascent (L'Ascension du pèlerin): a natural rock fang ~124 high crowned by a bell temple, climbed by a
switchback stairway carved into its south flank. The route IS the structure. Colossal tier (tools/BUILDING.md §1,
§12 concept 2, §15), mountain biomes.

Silhouette (one noun phrase, §15.1): a stone fang whose sheer north face drops into a plunge pool, its south flank
girdled by six terraces of red-gated stairs, a bell pavilion on the summit and a needle pinnacle tied to it by a
rope bridge.

Layout, ground y = 0, x east, z south. The rock is a stack of circular sections whose north edge stays on the plane
z = NZ (the vertical north cliff) while the radius shrinks upwards, so the centre drifts north and the south flank
leans back: wide talus at the foot (r 57), a 29-wide summit plateau at y 123.
  * the route: six legs, each an octagonal arc (west, south-west, south, south-east, east sides) carved 4 wide into
    the flank, the legs stacked 5 blocks inward and ~24 higher than the one below, reversing at the north-east and
    north-west shoulders (U-turn landings over the drop). Stair flights of 7-8 steps sit in the middle of the
    straight sides, each with a red gate at its foot (16 gates: the height reads by repetition); lanterns on the
    parapet every 6 blocks. Where the rock bulges above the stair it becomes a carved gallery; where it falls away
    the stair stands on a masonry retaining wall;
  * shrines (landings), bottom to top: 1. the foot: great torii, stone lanterns, purification basin, waystone;
    2. (y 17, NE) the prayer-wheel shrine on the shoulder; 3. (y 41, NW) the waterfall shrine: a spring falls from
    a spout into a basin; 4. (y 65, NE) the bell cave carved into the rock (gargoyles, waystone on the landing);
    5. (y 88, NW) the wind-bridge: a sagging rope bridge to the needle pinnacle, its top shrine guarded by skeleton
    knights (optional spur, tier 2); 6. (y 109, NE) the hermit's cell cut into the cliff, with a hatch to a hidden
    cellar (the secret);
  * the summit (feet 124): the last flight ends at a covered gate (compression, hung with a bell) opening on the
    terrace and its site of grace; the temple hall (radius 14, 18 high) is the boss arena, mist on its two doors,
    a stepped slate roof and the open belfry with the great bronze bell (visible from far); north of the hall the
    sanctum (reward, tier 3) hangs over the cliff on corbels, and its balcony is the way down: a 120-block leap
    into the plunge pool at the foot of the north face.
Loot gradient (§15.6): foot and prayer wheels tier 1, waterfall / bell cave tier 1-2, pinnacle / hermit tier 2,
the cellar 2-3, the sanctum tier 3.
Height budget: the template stands ~168 above its ground layer, so the bell finial stays under the build limit
(320) wherever the ground is below y ~150 (meadows, groves, snowy slopes, stony peaks, windswept hills). Frozen and
jagged peaks (ground often 170+) are left out for that reason.
"""
import math

import numpy as np

from ..arch import boulder, spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3
from ..parts import LOOT, MOD

# the ascent's own guardian comes with the boss pass; until then the temple wakes the Bell Keeper
BOSS = "brasshaven:bell_keeper"
MOB_STRAY = "minecraft:stray"
MOB_GARGOYLE = "brasshaven:gargoyle"
MOB_KNIGHT = "brasshaven:skeleton_knight"

# ------------------------------------------------------------------ dimensions
NZ = -44                                  # the vertical north cliff (plane z = NZ at x = 0)
F0 = 1                                    # feet at the foot
F_TOP = 124                               # feet on the summit plateau (rock top y 123)
LEG_R = (51, 46, 41, 36, 31, 26)          # apothem of each leg's octagon (5 inward per leg)
FLIGHTS = ((8, 8), (8, 8, 8), (8, 8, 8), (8, 7, 8), (7, 7, 7), (8, 7))
TZ = -24                                  # temple hall centre z (x = 0)
HALL_R = 14.4                             # arena floor radius (cells with r <= 14.4)
HALL_F = F_TOP + 3                        # arena feet: the hall stands on a 3-step podium
HALL_TOP = HALL_F + 17                    # last air layer of the hall
PX = -62                                  # needle pinnacle centre x (z = the bridge landing's)

# rock arrays
AX0, AX1 = -80, 80
AZ0, AZ1 = -66, 82
AY = 152                                  # y 0..AY-1

# materials
FLOOR_C = "polished_andesite"
FLOOR_E = ("stone_bricks", "stone_bricks", "andesite", "cobblestone")
ST_C = "polished_andesite_stairs"
ST_E = "stone_brick_stairs"
RED = "stripped_mangrove_log"
RED_P = "mangrove_planks"
TOP_W = "dark_oak_planks"
ROOF = "brasshaven:slate_roof_tiles"
ROOF_ST = "brasshaven:slate_roof_tile_stairs"
ROOF_SL = "brasshaven:slate_roof_tile_slab"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ vector noise (numpy)
def _hash(ix, iz, seed):
    n = ((ix * 73856093) ^ (iz * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, scale, seed):
    fx, fz = np.asarray(x, float) / scale, np.asarray(z, float) / scale
    ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _hash(ix, iz, seed), _hash(ix + 1, iz, seed)
    c, d = _hash(ix, iz + 1, seed), _hash(ix + 1, iz + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def fbm(x, z, scale, seed):
    return 0.6 * vnoise(x, z, scale, seed) + 0.3 * vnoise(x, z, scale / 2.3, seed + 7) + \
        0.1 * vnoise(x, z, scale / 5.1, seed + 13)


# ------------------------------------------------------------------ the route: legs, floors, cells
def leg_geom(k):
    r = LEG_R[k]
    cz = NZ + r + 3
    a = round(r * 0.4142)
    P = [(-r, cz - a), (-r, cz + a), (-a, cz + r), (a, cz + r), (r, cz + a), (r, cz - a)]
    M = (0, cz + r)
    if k == 0:
        pts = [M, P[3], P[4], P[5]]
    elif k == 5:
        pts = [P[5], P[4], P[3], M]
    elif k % 2 == 1:
        pts = P[::-1]
    else:
        pts = P
    return r, cz, a, pts


def _facing(p, q):
    dx, dz = q[0] - p[0], q[1] - p[1]
    if dz == 0:
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def build_legs():
    legs = []
    f = F0
    for k in range(6):
        r, cz, a, pts = leg_geom(k)
        fl = list(FLIGHTS[k])
        segs = []
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            axis = p[0] == q[0] or p[1] == q[1]
            if axis:
                L = abs(q[0] - p[0]) + abs(q[1] - p[1])
                n = fl.pop(0)
                u0 = max(2, (L - n) // 2 + 1)
                segs.append(dict(p=p, q=q, axis=True, L=L, f=f, n=n, u0=u0, facing=_facing(p, q)))
                f += n
            else:
                L = math.dist(p, q)
                segs.append(dict(p=p, q=q, axis=False, L=L, f=f, n=0, u0=0, facing=None))
        legs.append(dict(k=k, r=r, cz=cz, a=a, pts=pts, segs=segs, f_end=f, zc=cz - a,
                         side=1 if pts[-1][0] > 0 else -1))
    return legs


LEGS = build_legs()
assert LEGS[-1]["f_end"] == F_TOP, LEGS[-1]["f_end"]
TURN_F = [lg["f_end"] for lg in LEGS[:5]]          # feet on the five U-turn landings
PZ = (LEGS[4]["zc"] - 3 + LEGS[3]["zc"] + 2) // 2  # the bridge axis (z) at the north-west landing
YT = TURN_F[3]                                       # feet on the pinnacle top


def seg_floor(s, u):
    """(feet, stair?) at position u along segment s."""
    if not s["axis"] or s["n"] == 0:
        return s["f"], False
    u = int(round(u))
    i = u - s["u0"] + 1
    if 1 <= i <= s["n"]:
        return s["f"] + i, True
    return s["f"] + (s["n"] if i > s["n"] else 0), False


class Route:
    """Every walkway / parapet / clear cell of the route, and the landings."""

    def __init__(self):
        self.walk = {}       # (x, z) -> dict(f, stair facing or None, d, leg)
        self.para = {}       # (x, z) -> dict(f, leg)
        self.clear = {}      # (x, z) -> lowest f of the clears over it
        self.gates = []      # (row cells [(x, z, d)], f, facing)
        self.lamps = []      # (x, z, f)
        for lg in LEGS:
            self.raster(lg)
        for k in range(5):
            self.landing(k)
        self.forecourt()

    def raster(self, lg):
        segs = lg["segs"]
        cz = lg["cz"]
        x0 = min(p[0] for p in lg["pts"]) - 8
        x1 = max(p[0] for p in lg["pts"]) + 8
        z0 = min(p[1] for p in lg["pts"]) - 8
        z1 = max(p[1] for p in lg["pts"]) + 8
        last = len(segs) - 1
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                best = None
                for i, s in enumerate(segs):
                    (px, pz), (qx, qz) = s["p"], s["q"]
                    vx, vz = qx - px, qz - pz
                    L2 = vx * vx + vz * vz
                    t = ((x - px) * vx + (z - pz) * vz) / L2
                    if (i == 0 and t < 0) or (i == last and t > 1):
                        continue
                    tc = min(1.0, max(0.0, t))
                    cx, cc = px + vx * tc, pz + vz * tc
                    dist = math.hypot(x - cx, z - cc)
                    if best is None or dist < best[0] - 1e-9:
                        best = (dist, i, tc, cx, cc)
                if best is None:
                    continue
                dist, i, tc, cx, cc = best
                if dist > 6.6:
                    continue
                s = segs[i]
                # outward: away from the octagon centre
                ox, oz = cx - 0.0, cc - cz
                sgn = 1 if (x - cx) * ox + (z - cc) * oz >= 0 else -1
                d = sgn * dist
                u = tc * s["L"]
                f, is_stair = seg_floor(s, u)
                if -2.5 < d <= 1.5:
                    cell = dict(f=f, stair=s["facing"] if is_stair else None, d=round(d), leg=lg["k"])
                    old = self.walk.get((x, z))
                    if old is None or old["leg"] == lg["k"]:
                        self.walk[(x, z)] = cell
                elif 1.5 < d <= 2.5:
                    if (x, z) not in self.walk:
                        self.para[(x, z)] = dict(f=f, leg=lg["k"])
                elif d > 2.5:
                    self.clear[(x, z)] = min(self.clear.get((x, z), 999), f)
        # gates at the foot of every flight, lamps on the parapet every 6 blocks
        for s in segs:
            if not s["axis"]:
                continue
            ux, uz = DIRS[s["facing"]]
            nx, nz = self._outward(s, cz)
            u = s["u0"] - 1
            px, pz = s["p"][0] + ux * u, s["p"][1] + uz * u
            row = [(px + nx * d, pz + nz * d, d) for d in range(-4, 4)]
            self.gates.append((row, s["f"], s["facing"]))
            for u in range(3, s["L"] - 1, 6):
                if s["u0"] - 2 <= u <= s["u0"] + s["n"]:
                    continue
                f, _ = seg_floor(s, u)
                self.lamps.append((s["p"][0] + ux * u + nx * 2, s["p"][1] + uz * u + nz * 2, f))

    @staticmethod
    def _outward(s, cz):
        ux, uz = DIRS[s["facing"]]
        for nx, nz in ((uz, -ux), (-uz, ux)):
            mx, mz = (s["p"][0] + s["q"][0]) / 2, (s["p"][1] + s["q"][1]) / 2
            if nx * mx + nz * (mz - cz) > 0:
                return nx, nz
        return 0, 0

    def landing_box(self, k):
        a, b = LEGS[k], LEGS[k + 1]
        sg = a["side"]
        xs = sorted((sg * (b["r"] - 2), sg * (a["r"] + 1)))
        return xs[0], b["zc"] - 3, xs[1], a["zc"] + 2, TURN_F[k], sg

    def landing(self, k):
        x0, z0, x1, z1, f, sg = self.landing_box(k)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                self.walk[(x, z)] = dict(f=f, stair=None, d=0, leg=k, landing=k)
                self.para.pop((x, z), None)
        xo = x1 + 1 if sg > 0 else x0 - 1
        for z in range(z0 - 1, z1 + 1):
            if (xo, z) not in self.walk:
                self.para[(xo, z)] = dict(f=f, leg=k)
        for x in range(x0 - 1, x1 + 2):
            if (x, z0 - 1) not in self.walk:
                self.para[(x, z0 - 1)] = dict(f=f, leg=k)

    def forecourt(self):
        for x in range(-7, 8):
            for z in range(LEGS[0]["cz"] + LEGS[0]["r"] - 2, 80):
                if (x, z) in self.walk:
                    continue
                self.walk[(x, z)] = dict(f=F0, stair=None, d=0, leg=0, landing="foot")
                self.para.pop((x, z), None)


ROUTE = Route()


# ------------------------------------------------------------------ rock profile
def _rof_table():
    ys = [-1.0]
    rs = [57.0]
    for lg in LEGS:
        f_start = lg["segs"][0]["f"]
        ys.append((f_start + lg["f_end"]) / 2)
        rs.append(lg["r"] + 3.0)
    ys += [F_TOP - 1.0, 400.0]
    rs += [LEG_R[-1] + 3.0, LEG_R[-1] + 3.0]
    return ys, rs


_RY, _RR = _rof_table()


def rof(y):
    return float(np.interp(y, _RY, _RR))


XS = np.arange(AX0, AX1 + 1)
ZS = np.arange(AZ0, AZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")
JIT = fbm(GX, GZ, 9.0, 31)                                 # per-column strata jitter 0..1


def ai(x, y, z):
    return x - AX0, y, z - AZ0


class Plan:
    """Rock mask, carves, supports. Everything solid in ``S`` becomes rock (shell only), ``K`` is carved air."""

    def __init__(self):
        NX, NZ_ = len(XS), len(ZS)
        self.S = np.zeros((NX, AY, NZ_), bool)
        self.K = np.zeros((NX, AY, NZ_), bool)
        self.M = np.zeros((NX, AY, NZ_), bool)    # masonry supports (retaining walls)
        self.SUP = np.zeros((NX, AY, NZ_), bool)  # floors and the columns under them: never carved

    # ---- shapes
    def rock(self):
        S = self.S
        for y in range(0, F_TOP):
            R = rof(y)
            cz = NZ + R
            dx, dz = GX, GZ - cz
            dist = np.hypot(dx, dz)
            th = np.arctan2(dx, dz)
            arc = th * R
            n = fbm(arc, y * 1.0, 13.0, 3)
            n2 = vnoise(arc, y * 0.4, 6.0, 5)
            north = np.clip((-np.cos(th) - 0.35) / 0.45, 0, 1)
            amp = 3.4 * (1 - 0.8 * north)
            rib = 1.8 * (0.5 + 0.5 * np.cos(arc / 4.3 + y * 0.06)) ** 6 * (1 - north)
            ledge = (((y + 6 * vnoise(arc, 0 * arc, 22.0, 9)) % 11) < 1.7) * 1.3 * (1 - north)
            reff = R + amp * (2 * n - 1) + rib + ledge + 0.8 * (n2 - 0.5)
            S[:, y, :] |= dist < reff
            if y < 10:                                    # talus at the foot
                c0 = NZ + rof(0)
                d0 = np.hypot(GX, GZ - c0)
                rt = rof(0) + (10 - y) * 0.9 + 3.0 * (2 * fbm(GX, GZ, 11.0, 17) - 1)
                pool = (GZ < NZ + 9) & (np.abs(GX) < 14)
                S[:, y, :] |= (d0 < rt) & ~pool
        # the needle pinnacle (top flat at YT - 1)
        for y in range(0, YT):
            th = np.arctan2(GX - PX, GZ - PZ)
            rp = 10.5 - 4.5 * y / YT + 1.4 * (2 * fbm(th * 9, y * 1.0, 7.0, 41) - 1)
            if y >= YT - 2:
                rp = np.maximum(rp, 6.6)
            S[:, y, :] |= np.hypot(GX - PX, GZ - PZ) < rp
        # summit crags round the temple
        for (cx, cz, r0, top) in ((-22, -38, 6.0, 150), (18, -40, 4.0, 141), (-25, -12, 3.0, 133)):
            for y in range(F_TOP - 6, min(top, AY)):
                k = max(0.0, 1 - (y - (F_TOP - 6)) / (top - (F_TOP - 6))) ** 0.7
                th = np.arctan2(GX - cx, GZ - cz)
                rr = r0 * k + 0.9 * (vnoise(th * 3, y * 0.3, 2.0, 77) - 0.5)
                S[:, y, :] |= np.hypot(GX - cx, GZ - cz) < rr

    def carve_box(self, x0, y0, z0, x1, y1, z1):
        a = ai(min(x0, x1), max(0, min(y0, y1)), min(z0, z1))
        b = ai(max(x0, x1), min(AY - 1, max(y0, y1)), max(z0, z1))
        self.K[a[0]:b[0] + 1, a[1]:b[1] + 1, a[2]:b[2] + 1] = True

    def carve_ell(self, c, r, ymin=None):
        for x in range(int(c[0] - r[0]) - 1, int(c[0] + r[0]) + 2):
            for y in range(int(c[1] - r[1]) - 1, int(c[1] + r[1]) + 2):
                for z in range(int(c[2] - r[2]) - 1, int(c[2] + r[2]) + 2):
                    if ymin is not None and y < ymin:
                        continue
                    if ((x - c[0]) / r[0]) ** 2 + ((y - c[1]) / r[1]) ** 2 + ((z - c[2]) / r[2]) ** 2 <= 1:
                        self.K[ai(x, y, z)] = True

    def support(self, x, z, f, mason, out=None):
        """Solid from the floor (f - 1) down to the rock (or the ground): a masonry cap 3 high on the outer edge,
        then rock battered outwards (1 in 2.5) along ``out`` so the stair stands on a natural talus, not a wall."""
        i, _, k = ai(x, 0, z)
        NX, _, NK = self.S.shape
        if not (0 <= i < NX and 0 <= k < NK):
            return
        y = f - 1
        j = 0
        while y >= 0:
            if self.S[i, y, k] and j:
                break
            self.S[i, y, k] = True
            self.SUP[i, y, k] = True
            if mason and 0 < j <= 3:
                self.M[i, y, k] = True
            if out is not None and j > 3:
                for e in range(1, min(7, (j - 1) // 2) + 1):
                    ii, kk = i + round(out[0] * e), k + round(out[1] * e)
                    if 0 <= ii < NX and 0 <= kk < NK:
                        self.S[ii, y, kk] = True
            j += 1
            y -= 1

    def spurs(self):
        """A rock outcrop under every U-turn landing, widening downwards into the flank."""
        for kk in range(5):
            x0, z0, x1, z1, f, sg = ROUTE.landing_box(kk)
            cx, cz = (x0 + x1) / 2 + sg, (z0 + z1) / 2 - 1
            hx, hz = (x1 - x0) / 2 + 1.5, (z1 - z0) / 2 + 1.5
            for y in range(max(0, f - 50), f - 1):
                j = f - 1 - y
                ax, az = 0.0, NZ + rof(y)
                L = math.hypot(ax - cx, az - cz)
                mx, mz = cx + (ax - cx) / L * 0.4 * j, cz + (az - cz) / L * 0.4 * j
                th = np.arctan2(GX - mx, GZ - mz)
                n = fbm(th * 6, y * 1.0, 5.0, 90 + kk)
                rx, rz = hx + 0.22 * j, hz + 0.22 * j
                e = ((GX - mx) / rx) ** 2 + ((GZ - mz) / rz) ** 2
                self.S[:, y, :] |= e < (0.75 + 0.5 * n)

    def route(self):
        self.spurs()
        for (x, z), c in ROUTE.walk.items():
            self.support(x, z, c["f"], c["d"] >= 1 and "landing" not in c)
            self.carve_box(x, c["f"], z, x, c["f"] + 3, z)
        for (x, z), c in ROUTE.para.items():
            cz = LEGS[c["leg"]]["cz"]
            L = math.hypot(x, z - cz) or 1.0
            self.support(x, z, c["f"], True, out=(x / L, (z - cz) / L))
            self.carve_box(x, c["f"] + 1, z, x, c["f"] + 3, z)
        for (x, z), f in ROUTE.clear.items():
            if (x, z) not in ROUTE.walk and (x, z) not in ROUTE.para:
                self.carve_box(x, f, z, x, f + 24, z)
        for row, f, facing in ROUTE.gates:
            for (x, z, d) in row:
                if -4 <= d <= 3:
                    self.carve_box(x, f + 4, z, x, f + 6, z)

    def shrines(self):
        # the foot: a valley opening south through the talus, its sides sloping back (no straight cut)
        zf = LEGS[0]["cz"] + LEGS[0]["r"] - 2
        for z in range(zf, AZ1 + 1):
            for y in range(1, 22):
                hw = 8 + max(0, z - zf) * 0.45 + (y - 1) * 0.9 + 2.0 * (hash01(z, y, 71) - 0.5)
                self.carve_box(-int(hw), y, z, int(hw), y, z)
        # the chute down the north face (nothing sticks out under the leap)
        self.carve_box(-3, 1, AZ0, 3, F_TOP - 8, NZ + 2)
        self.carve_box(-14, 0, AZ0, 14, 30, NZ - 1)
        # prayer wheels landing: clear headroom for the shelter
        x0, z0, x1, z1, f, sg = ROUTE.landing_box(0)
        self.carve_box(x0, f, z0 - 1, x1 + 1, f + 9, z1)
        # stray pocket off leg 1's south side
        f1, zi = stray_pocket()
        self.carve_box(-14, f1, zi - 2, -10, f1 + 2, zi)
        # waterfall slot (north-west landing)
        x0, z0, x1, z1, f, sg = ROUTE.landing_box(1)
        wx = x1                                    # inner edge of the landing (x = -39)
        self.carve_box(wx - 1, f, z0 - 1, wx, f + 15, z0 + 1)
        # bell cave (north-east landing)
        x0, z0, x1, z1, f, sg = ROUTE.landing_box(2)
        self.carve_ell((x0 - 7, f + 3, z0 - 4), (6.5, 4.5, 5.5), ymin=f)
        self.carve_box(x0 - 4, f, z0, x0, f + 3, z0 + 2)
        # the wind bridge and the pinnacle top
        x0, z0, x1, z1, f, sg = ROUTE.landing_box(3)
        self.carve_box(PX + 6, YT - 1, PZ - 3, x0 - 1, YT + 7, PZ + 3)
        for x in range(PX - 9, PX + 10):
            for z in range(PZ - 9, PZ + 10):
                if math.hypot(x - PX, z - PZ) <= 9:
                    self.carve_box(x, YT, z, x, YT + 12, z)
        # hermit's cell, its door and the cellar under it
        x0, z0, x1, z1, f, sg = ROUTE.landing_box(4)
        self.carve_box(15, f, -30, 21, f + 4, -24)
        self.carve_box(22, f, -27, 23, f + 1, -27)
        self.carve_box(14, f - 6, -33, 19, f - 3, -29)
        self.carve_box(16, f - 6, -28, 16, f - 2, -28)

    def finish(self):
        self.K &= ~self.SUP
        S2 = self.S & ~self.K
        air = ~S2
        near = air.copy()
        for _ in range(3):
            n = near.copy()
            n[1:, :, :] |= near[:-1, :, :]
            n[:-1, :, :] |= near[1:, :, :]
            n[:, 1:, :] |= near[:, :-1, :]
            n[:, :-1, :] |= near[:, 1:, :]
            n[:, :, 1:] |= near[:, :, :-1]
            n[:, :, :-1] |= near[:, :, 1:]
            near = n
        # the array border counts as open air (except under the ground)
        shell = S2 & near
        shell[0, :, :] |= S2[0, :, :]
        shell[-1, :, :] |= S2[-1, :, :]
        shell[:, :, 0] |= S2[:, :, 0]
        shell[:, :, -1] |= S2[:, :, -1]
        top = S2.copy()
        top[:, :-1, :] &= ~S2[:, 1:, :]
        self.S2, self.shell, self.top = S2, shell, top


def stray_pocket():
    """(feet, inner z) of the stray ambush pocket on leg 1's south side, at x = -12."""
    lg = LEGS[1]
    z = lg["cz"] + lg["r"]
    c = ROUTE.walk.get((-12, z))
    return c["f"], z - 3


# ------------------------------------------------------------------ rock blocks
LOW = ("tuff", "andesite", "stone", "cobblestone", "andesite", "tuff", "stone", "andesite")
MID = ("stone", "andesite", "stone", "stone", "tuff", "stone", "andesite", "diorite", "stone")
HIGH = ("stone", "calcite", "stone", "andesite", "diorite", "stone", "calcite", "stone", "andesite")


def rock_block(x, y, z, top, mason, jit):
    h = hash3(x, y, z, 7)
    if mason:
        return "mossy_stone_bricks" if y < 30 and h < 0.3 else ("cracked_stone_bricks" if h < 0.15 else "stone_bricks")
    if top:
        if y >= F_TOP - 2:                       # the summit plateau: snow with rock showing through
            return "snow_block" if jit < 0.55 or h < 0.55 else ("calcite" if h < 0.8 else "stone")
        if y >= 96 - 34 * jit:
            return "snow_block"
        if y < 30 + 30 * jit:
            if h < 0.8:
                return "grass_block[snowy=false]"
            return "moss_block" if h < 0.9 else "coarse_dirt"
        if jit > 0.62:
            return "moss_block" if h < 0.6 else "grass_block[snowy=false]"
        return "stone" if h < 0.6 else ("andesite" if h < 0.85 else "tuff")
    s = y + int(5 * jit)
    if y < 12 and h < 0.3:
        return "mossy_cobblestone"
    if s < 34:
        return LOW[(s // 4) % len(LOW)]
    if s < 86:
        return MID[(s // 4) % len(MID)]
    return HIGH[(s // 3) % len(HIGH)]


def write_rock(bp, P):
    idx = np.argwhere(P.shell)
    for i, y, k in idx.tolist():
        x, z = int(XS[i]), int(ZS[k])
        bp.set(x, y, z, rock_block(x, y, z, bool(P.top[i, y, k]), bool(P.M[i, y, k]), float(JIT[i, k])))
    # carved rock -> air (the terrain around the foot gets cut the same way)
    idx = np.argwhere(P.K & P.S)
    for i, y, k in idx.tolist():
        bp.set(int(XS[i]), y, int(ZS[k]), "air")


# ------------------------------------------------------------------ the route's blocks
def edge_floor(x, z):
    return FLOOR_E[int(hash01(x, z, 11) * len(FLOOR_E))]


def build_route(bp):
    for (x, z), c in ROUTE.walk.items():
        f = c["f"]
        for y in range(f, f + 4):
            bp.set(x, y, z, "air")
        centre = c["d"] in (-1, 0) and "landing" not in c
        if c["stair"]:
            bp.set(x, f - 1, z, stair(ST_C if centre else ST_E, c["stair"]))
        elif c.get("landing") == "foot":
            bp.set(x, f - 1, z, "polished_andesite" if abs(x) <= 1 else edge_floor(x, z))
        else:
            bp.set(x, f - 1, z, FLOOR_C if centre or hash01(x, z, 3) < 0.35 else edge_floor(x, z))
    for (x, z), c in ROUTE.para.items():
        f = c["f"]
        bp.set(x, f - 1, z, "stone_bricks")
        bp.set(x, f, z, "andesite_wall" if hash01(x, z, 5) < 0.5 else "stone_brick_wall")
        for y in range(f + 1, f + 4):
            bp.set(x, y, z, "air")
    for (x, z, f) in ROUTE.lamps:
        if (x, z) in ROUTE.para:
            bp.set(x, f, z, "chiseled_stone_bricks")
            bp.set(x, f + 1, z, LANT)


def gate(bp, row, f, facing, stone=False):
    """A torii across the stair: posts at d = -3 and +2, a tie beam at f + 4, the top beam at f + 5..6."""
    post = "polished_andesite" if stone else RED + "[axis=y]"
    tie = "andesite_slab[type=top]" if stone else "mangrove_slab[type=top]"
    beam = "polished_andesite" if stone else RED_P
    cap = "dark_oak_slab[type=bottom]"
    side = facing in ("north", "south")
    for (x, z, d) in row:
        if d in (-3, 2):
            bp.set(x, f - 1, z, "stone_bricks")
            for y in range(f, f + 5):
                bp.set(x, y, z, post)
        elif -2 <= d <= 1:
            bp.set(x, f + 4, z, tie)
        if -4 <= d <= 3:
            bp.set(x, f + 5, z, beam)
            if d in (-4, 3):
                out = None
                dx, dz = x - row[4][0], z - row[4][1]
                if side:
                    out = "east" if dx > 0 else "west"
                else:
                    out = "south" if dz > 0 else "north"
                bp.set(x, f + 6, z, stair("dark_oak_stairs", OPP[out], "bottom"))
            else:
                bp.set(x, f + 6, z, cap)
    # a lantern hangs from the tie beam's middle on the outer side
    x, z, _ = row[6]
    bp.set(x, f + 3, z, "air")


def build_gates(bp):
    for i, (row, f, facing) in enumerate(ROUTE.gates):
        gate(bp, row, f, facing, stone=(i % 4 == 3))


# ------------------------------------------------------------------ shrines
def stone_lantern(bp, x, y, z):
    bp.set(x, y, z, "andesite_wall")
    bp.set(x, y + 1, z, "polished_andesite")
    bp.set(x, y + 2, z, LANT)
    bp.set(x, y + 3, z, "andesite_slab[type=bottom]")


def foot_shrine(bp):
    """Shrine 1: the great torii over the forecourt, stone lanterns, the basin, the waystone, a pilgrim's chest."""
    zg = 70
    for x in (-6, 6):
        bp.set(x, 0, zg, "polished_andesite")
        bp.set(x, 1, zg, "andesite_wall")
        for y in range(1, 12):
            bp.set(x, y, zg, RED + "[axis=y]")
    for x in range(-8, 9):
        bp.set(x, 9, zg, RED_P if abs(x) <= 6 else "air")
        bp.set(x, 12, zg, RED_P)
        bp.set(x, 13, zg, "dark_oak_slab[type=bottom]" if abs(x) < 9 else "air")
    for x in range(-7, 8):
        bp.set(x, 9, zg, "mangrove_slab[type=top]" if abs(x) != 6 else RED + "[axis=y]")
    for x in (-10, 10):
        bp.set(x, 12, zg, stair("dark_oak_stairs", "east" if x < 0 else "west", "top"))
        bp.set(x, 13, zg, stair("dark_oak_stairs", "east" if x < 0 else "west"))
    bp.set(-9, 13, zg, "dark_oak_slab[type=bottom]")
    bp.set(9, 13, zg, "dark_oak_slab[type=bottom]")
    bp.set(0, 10, zg, "dark_oak_planks")
    bp.set(0, 11, zg, "dark_oak_planks")
    # stone lanterns along the court
    for z in (64, 74, 78):
        for x in (-4, 4):
            stone_lantern(bp, x, 1, z)
    # the purification basin under a small roof, the waystone, the chest
    bp.set(5, 1, 66, "water_cauldron[level=3]")
    bp.set(6, 1, 66, "water_cauldron[level=3]")
    for (x, z) in ((4, 65), (7, 65), (4, 67), (7, 67)):
        for y in range(1, 4):
            bp.set(x, y, z, "spruce_fence")
    for x in range(3, 9):
        for z in range(64, 69):
            bp.set(x, 4, z, "spruce_slab[type=bottom]" if x in (3, 8) or z in (64, 68) else "spruce_planks")
    bp.set(-5, 1, 62, MOD["waystone"])
    bp.chest(-6, 1, 66, "east", loot=LOOT + "ascent_foot")
    bp.set(-6, 1, 67, "barrel[facing=up,open=false]")
    # the marker where the approach starts
    for y in range(1, 4):
        bp.set(-3, y, 80, "mossy_stone_bricks" if y == 1 else "stone_bricks")
    bp.set(-3, 4, 80, LANT)


def prayer_shrine(bp):
    """Shrine 2 (NE shoulder, y 17): prayer wheels under a pent roof along the parapet, prayer flags."""
    x0, z0, x1, z1, f, sg = ROUTE.landing_box(0)
    zr = z0
    for x in range(x0, x1 + 1):
        bp.set(x, f + 4, zr, "spruce_slab[type=top]")
        bp.set(x, f + 4, zr + 1, stair("spruce_stairs", "north", "bottom") if False else "spruce_slab[type=top]")
        bp.set(x, f + 5, zr, stair("spruce_stairs", "south"))
    for x in (x0, x1):
        for y in range(f, f + 4):
            bp.set(x, y, zr, RED + "[axis=y]")
    for x in range(x0 + 1, x1, 2):
        bp.set(x, f, zr, "waxed_cut_copper")
        bp.set(x, f + 1, zr, RED + "[axis=y]")
        bp.set(x, f + 2, zr, "waxed_chiseled_copper")
        bp.set(x, f + 3, zr, "iron_chain[axis=y,waterlogged=false]")
    bp.chest(x1, f, z1 - 1, "west", loot=LOOT + "ascent_foot")
    # prayer flags from a pole on the outer corner to the shelter
    px, pz = x1, z1
    for y in range(f, f + 7):
        bp.set(px + sg, y, pz, "spruce_fence" if y < f + 6 else LANT)
    colours = ("blue_wool", "white_wool", "red_wool", "green_wool", "yellow_wool")
    for i, z in enumerate(range(zr + 1, pz)):
        bp.set(px + sg, f + 5, z, colours[i % 5])


def waterfall_shrine(bp):
    """Shrine 3 (NW shoulder, y 41): a spring falls from a stone spout into a sunk basin; a little hokora."""
    x0, z0, x1, z1, f, sg = ROUTE.landing_box(1)
    wx, wz = x1, z0                    # the column (x -39, the landing's north row)
    for x in range(wx - 2, wx + 1):
        for z in range(wz, wz + 3):
            if (x, z) == (wx - 2, wz + 2):
                continue
            bp.set(x, f - 2, z, "stone_bricks")
            bp.set(x, f - 1, z, "water")
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
    for x in range(wx - 3, wx + 2):
        bp.set(x, f - 1, wz - 1, "mossy_stone_bricks")
        bp.set(x, f, wz - 1, "mossy_cobblestone_wall")
    top = f + 15
    for y in range(f, top):
        bp.set(wx, y, wz + 1, "water[level=8]")
    bp.set(wx, top, wz + 1, "water")
    for (x, y, z) in ((wx - 1, top, wz + 1), (wx, top, wz), (wx, top, wz + 2), (wx + 1, top, wz + 1),
                      (wx, top + 1, wz + 1), (wx - 1, top + 1, wz + 1), (wx + 1, top, wz), (wx + 1, top, wz + 2)):
        bp.set(x, y, z, "mossy_stone_bricks")
    bp.set(wx - 1, top - 1, wz, stair("stone_brick_stairs", "east", "top"))
    bp.set(wx - 1, top - 1, wz + 2, stair("stone_brick_stairs", "east", "top"))
    for y in range(f + 4, top):
        bp.set(wx + 1, y, wz + 1, "mossy_cobblestone")
    # the hokora: a tiny shrine house on the outer side of the landing
    hx, hz = x0 + 1, wz + 1
    bp.set(hx, f, hz, "polished_andesite_slab[type=bottom,waterlogged=false]")
    bp.set(hx + 1, f, hz, "candle[candles=3,lit=true,waterlogged=false]")
    for (x, z) in ((hx - 1, hz - 1), (hx - 1, hz + 1)):
        for y in range(f, f + 4):
            bp.set(x, y, z, RED + "[axis=y]")
    for x in range(hx - 2, hx + 3):
        for z in range(hz - 2, hz + 3):
            bp.set(x, f + 4, z, ROOF_SL + "[type=bottom]" if x in (hx - 2, hx + 2) or z in (hz - 2, hz + 2)
                   else ROOF)
    bp.chest(hx, f, hz + 2, "east", loot=LOOT + "ascent_shrine")
    bp.set(hx, f, hz + 2, "air")
    bp.chest(hx + 1, f, hz - 1, "south", loot=LOOT + "ascent_shrine")


def bell_cave(bp, P):
    """Shrine 4 (NE, y 65): a grotto in the rock with a hanging bell and candles; gargoyles; a waystone outside."""
    x0, z0, x1, z1, f, sg = ROUTE.landing_box(2)
    cx, cz = x0 - 7, z0 - 4
    # level the cave floor
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if P.K[ai(x, f, z)] and not ROUTE.walk.get((x, z)):
                bp.set(x, f - 1, z, "polished_andesite" if math.hypot(x - cx, z - cz) < 3 else
                       ("mossy_cobblestone" if hash01(x, z, 4) < 0.4 else "andesite"))
    for x in range(x0 - 4, x0 + 1):
        for z in range(z0, z0 + 3):
            bp.set(x, f - 1, z, "stone_bricks")
    # the bell hangs from the cave roof
    top = f + 7
    while top > f + 4 and not P.S2[ai(cx, top, cz)]:
        top += 1
        if top > f + 9:
            break
    bp.set(cx, f + 7, cz, "polished_andesite")
    bp.set(cx, f + 6, cz, "iron_chain[axis=y,waterlogged=false]")
    bp.set(cx, f + 5, cz, "bell[attachment=ceiling,facing=east,powered=false]")
    bp.set(cx, f - 1, cz, "chiseled_stone_bricks")
    for (x, z) in ((cx - 4, cz), (cx + 3, cz - 3), (cx, cz + 4), (cx - 3, cz - 3)):
        bp.set(x, f, z, "candle[candles=4,lit=true,waterlogged=false]")
    bp.spawner(cx - 5, f, cz - 1, MOB_GARGOYLE)
    bp.chest(cx - 4, f, cz + 2, "east", loot=LOOT + "ascent_shrine")
    bp.set(x1, f, z0 + 1, MOD["waystone"])
    bp.set(x1 - 1, f, z1, LANT)


def pinnacle(bp):
    """Shrine 5: the needle's top (feet YT), reached by the wind-bridge: an open pavilion with a wind bell."""
    f = YT
    for x in range(PX - 7, PX + 8):
        for z in range(PZ - 7, PZ + 8):
            r = math.hypot(x - PX, z - PZ)
            if r <= 6.6:
                bp.set(x, f - 1, z, "calcite" if r < 2 else ("polished_andesite" if hash01(x, z, 8) < 0.6
                                                                else "andesite"))
                for y in range(f, f + 4):
                    bp.set(x, y, z, "air")
            elif r <= 7.6 and not (x > PX and abs(z - PZ) <= 1):
                bp.set(x, f - 1, z, "stone_bricks")
                bp.set(x, f, z, "andesite_wall")
    for (dx, dz) in ((-3, -3), (-3, 3), (3, -3), (3, 3)):
        for y in range(f, f + 5):
            bp.set(PX + dx, y, PZ + dz, RED + "[axis=y]")
    for i in range(5):
        for x in range(PX - 5 + i, PX + 6 - i):
            for z in range(PZ - 5 + i, PZ + 6 - i):
                edge = x in (PX - 5 + i, PX + 5 - i) or z in (PZ - 5 + i, PZ + 5 - i)
                if i == 4:
                    bp.set(x, f + 5 + i, z, ROOF)
                elif edge:
                    if x == PX - 5 + i:
                        fc = "east"
                    elif x == PX + 5 - i:
                        fc = "west"
                    elif z == PZ - 5 + i:
                        fc = "south"
                    else:
                        fc = "north"
                    bp.set(x, f + 5 + i, z, stair(ROOF_ST, fc))
                else:
                    bp.set(x, f + 5 + i, z, TOP_W if i == 0 else ROOF)
    bp.set(PX, f + 10, PZ, "lightning_rod")
    bp.set(PX, f + 4, PZ, "bell[attachment=ceiling,facing=east,powered=false]")
    bp.spawner(PX - 1, f, PZ - 4, MOB_KNIGHT)
    bp.chest(PX - 5, f, PZ, "east", loot=LOOT + "ascent_pinnacle")
    stone_lantern(bp, PX - 4, f, PZ + 4)
    stone_lantern(bp, PX - 4, f, PZ - 4)


def wind_bridge(bp):
    """The sagging rope bridge from the north-west landing (feet YT) to the pinnacle."""
    x0, z0, x1, z1, f, sg = ROUTE.landing_box(3)
    xa, xb = PX + 7, x0 - 1                   # deck x range (pinnacle edge -> landing parapet)
    span = xb - xa
    for x in range(xa, xb + 1):
        t = (x - xa) / span
        sag = 4 * t * (1 - t)                 # 0 at the ends, 1 mid-span
        if sag < 0.45:
            deck, hb = "spruce_planks", f - 1
            rail_y = f
        elif sag < 0.85:
            deck, hb = "spruce_slab[type=bottom]", f - 1
            rail_y = f
        else:
            deck, hb = "spruce_slab[type=top]", f - 2
            rail_y = f - 1
        for z in range(PZ - 2, PZ + 3):
            for y in range(f - 2, f + 4):
                bp.set(x, y, z, "air")
            bp.set(x, hb, z, deck)
        for z in (PZ - 2, PZ + 2):
            bp.set(x, rail_y, z, "spruce_fence")
            cy = round(f + 4 - 3 * sag)
            bp.set(x, cy, z, "iron_chain[axis=x,waterlogged=false]")
            if x % 3 == 0 and cy - 1 > rail_y:
                for y in range(rail_y + 1, cy):
                    bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")
            elif x % 3 == 1 and cy - 1 > rail_y:
                bp.set(x, cy - 1, z, ("red_wool", "white_wool", "blue_wool", "yellow_wool")[(x // 3) % 4])
        bp.set(x, hb - 1, PZ, "iron_chain[axis=x,waterlogged=false]")
    # end posts with lanterns
    for x in (xa - 1, xb + 1):
        for z in (PZ - 2, PZ + 2):
            bp.set(x, f - 1, z, "stone_bricks")
            for y in range(f, f + 5):
                bp.set(x, y, z, "spruce_log[axis=y]")
            bp.set(x, f + 5, z, LANT)
    for z in range(PZ - 1, PZ + 2):
        bp.set(xb + 1, f - 1, z, FLOOR_C)
        bp.set(xb + 1, f, z, "air")
        bp.set(xa - 1, f - 1, z, "polished_andesite")
        bp.set(xa - 1, f, z, "air")


def hermit_cell(bp):
    """Shrine 6 (NE, y 109): a hermit's cell cut into the cliff; a hatch opens on a hidden cellar (the secret)."""
    x0, z0, x1, z1, f, sg = ROUTE.landing_box(4)
    for x in range(15, 22):
        for z in range(-30, -23):
            bp.set(x, f - 1, z, "spruce_planks" if (x + z) % 3 else "stripped_spruce_log[axis=x]")
            for y in range(f, f + 5):
                bp.set(x, y, z, "air")
            bp.set(x, f + 5, z, "spruce_planks")
    for x in (15, 21):
        bp.set(x, f + 4, -27, "spruce_log[axis=z]")
    bp.door(23, f, -27, "west", wood="spruce")
    bp.set(22, f, -27, "air")
    bp.set(22, f + 1, -27, "air")
    bp.set(22, f - 1, -27, "spruce_planks")
    bp.set(23, f - 1, -27, "spruce_planks")
    bp.bed(16, f, -25, "north", color="brown")
    bp.set(20, f, -30, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(21, f, -30, "bookshelf")
    bp.set(21, f + 1, -30, "bookshelf")
    bp.set(15, f, -30, "furnace[facing=south,lit=false]")
    bp.set(18, f, -30, "crafting_table")
    bp.barrel(21, f, -24, "up", loot=LOOT + "ascent_shrine")
    bp.set(19, f, -24, "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(18, f + 4, -27, LANT_H)
    bp.set(15, f, -27, "brown_carpet")
    bp.set(17, f, -28, "brown_carpet")
    # the hatch and the cellar
    bp.set(16, f - 1, -28, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(16, f - 6, -28, f - 2, "north")
    for x in range(14, 20):
        for z in range(-33, -28):
            bp.set(x, f - 7, z, "cobblestone")
            for y in range(f - 6, f - 2):
                bp.set(x, y, z, "air")
    bp.chest(18, f - 6, -33, "south", loot=LOOT + "ascent_hermit")
    bp.set(14, f - 6, -33, "candle[candles=1,lit=true,waterlogged=false]")
    bp.set(15, f - 6, -33, "barrel[facing=up,open=false]")
    # a window beside the door, a stone lantern on the landing
    bp.set(23, f + 1, -25, "glass_pane")
    stone_lantern(bp, x1 - 1, f, z0 + 1)


# ------------------------------------------------------------------ the summit
def disc_cells(cx, cz, r):
    ir = int(r) + 1
    for x in range(cx - ir, cx + ir + 1):
        for z in range(cz - ir, cz + ir + 1):
            d = math.hypot(x - cx, z - cz)
            if d <= r:
                yield x, z, d


def inward(dx, dz):
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def summit(bp):
    f = F_TOP
    # terrace paving round the temple and up to the gate
    for x, z, d in disc_cells(0, TZ, 21.5):
        if bp.get(x, f - 1, z) is not None or True:
            if (x, z) in ROUTE.walk:
                continue
            bp.set(x, f - 1, z, "polished_andesite" if d < 19 and hash01(x, z, 12) < 0.7 else
                   ("andesite" if hash01(x, z, 13) < 0.5 else "stone_bricks"))
            for y in range(f, f + 3):
                if bp.get(x, y, z) in ("minecraft:snow_block", None) or True:
                    pass
    for x in range(-12, 13):
        for z in range(-8, 8):
            if (x, z) in ROUTE.walk or ROUTE.para.get((x, z)):
                continue
            if abs(x) <= 1:
                spec = FLOOR_C
            elif abs(x) <= 3 or z >= 2:
                spec = "stone_bricks"
            else:
                spec = "polished_andesite" if hash01(x, z, 14) < 0.6 else "andesite"
            bp.set(x, f - 1, z, spec)
            for y in range(f, f + 4):
                if bp.get(x, y, z) in (None, "minecraft:snow_block", "minecraft:stone", "minecraft:calcite",
                                       "minecraft:andesite", "minecraft:diorite"):
                    bp.set(x, y, z, "air")
    # the summit gate (compression): 3 wide, 5 high, 7 long, hung with a bell
    for z in range(2, 9):
        for x in (-2, 2):
            for y in range(f, f + 5):
                bp.set(x, y, z, RED + "[axis=y]" if z in (2, 8) else "calcite")
        for x in range(-1, 2):
            for y in range(f, f + 5):
                bp.set(x, y, z, "air")
    for z in range(1, 10):
        for x in range(-3, 4):
            bp.set(x, f + 5, z, TOP_W)
        bp.set(-3, f + 6, z, stair(ROOF_ST, "east"))
        bp.set(3, f + 6, z, stair(ROOF_ST, "west"))
        for x in range(-2, 3):
            bp.set(x, f + 6, z, ROOF)
        bp.set(-2, f + 7, z, stair(ROOF_ST, "east"))
        bp.set(2, f + 7, z, stair(ROOF_ST, "west"))
        for x in range(-1, 2):
            bp.set(x, f + 7, z, ROOF)
        bp.set(0, f + 8, z, ROOF_SL + "[type=bottom]")
    bp.set(0, f + 4, 5, "bell[attachment=ceiling,facing=south,powered=false]")
    bp.set(0, f + 3, 3, "air")
    bp.set(-1, f + 4, 2, LANT_H)
    bp.set(1, f + 4, 8, LANT_H)
    # temenos wall either side of the gate
    for x in list(range(-12, -2)) + list(range(3, 13)):
        if (x, 8) not in ROUTE.walk:
            bp.set(x, f - 1, 8, "stone_bricks")
            bp.set(x, f, 8, "stone_bricks")
            bp.set(x, f + 1, 8, "stone_brick_wall")
    # the site of grace on the terrace
    bp.set(-5, f, -3, MOD["waystone"])
    stone_lantern(bp, -6, f, 0)
    stone_lantern(bp, 6, f, 0)
    temple(bp)
    sanctum(bp)


def temple(bp):
    f = HALL_F
    cz = TZ
    # the podium (3 high) and the hall floor
    for x, z, d in disc_cells(0, cz, 18.5):
        bp.set(x, f - 1, z, "calcite" if 6.5 < d < 7.5 else ("polished_andesite" if d <= HALL_R else
                                                              ("polished_andesite" if d > 17.6 else "stone_bricks")))
        for y in range(F_TOP - 4, f - 1):
            bp.set(x, y, z, ("chiseled_stone_bricks" if y == f - 2 and hash01(x, z, 15) < 0.2 else "stone_bricks")
                   if d > 17 else "stone")
    # the grand stair up the podium, 7 wide
    for k in range(3):
        z = cz + 21 - k
        for x in range(-3, 4):
            for y in range(F_TOP - 2, F_TOP + k):
                bp.set(x, y, z, "stone_bricks")
            bp.set(x, F_TOP + k, z, stair(ST_C if abs(x) <= 1 else ST_E, "north"))
            for y in range(F_TOP + k + 1, F_TOP + k + 5):
                bp.set(x, y, z, "air")
    for x in (-4, 4):
        for k in range(3):
            bp.set(x, F_TOP + k, cz + 21 - k, "stone_bricks")
        stone_lantern(bp, x, F_TOP, cz + 22)
    # walls: calcite between red posts, a stone base course, dark beam bands
    for x, z, d in disc_cells(0, cz, 17.5):
        if d <= HALL_R:
            for y in range(f, HALL_TOP + 1):
                bp.set(x, y, z, "air")
            continue
        ang = math.degrees(math.atan2(x, z - cz)) % 360
        post = min(ang % 22.5, 22.5 - ang % 22.5) < 2.2
        for y in range(f, HALL_TOP + 2):
            if d > 16.4:
                if post:
                    bp.set(x, y, z, RED + "[axis=y]")
                elif y <= f + 1:
                    bp.set(x, y, z, "polished_andesite")
                continue
            if y <= f + 2:
                spec = "polished_andesite" if d > 15.4 else "stone_bricks"
            elif y in (f + 9, HALL_TOP + 1):
                spec = TOP_W
            elif post and d > 15.4:
                spec = RED + "[axis=y]"
            else:
                spec = "calcite"
            bp.set(x, y, z, spec)
    # tall windows in 8 bays
    for i in range(8):
        a = math.radians(i * 45 + 11.25)
        for w in (-1, 0, 1):
            x = round(15.9 * math.sin(a) + w * math.cos(a))
            z = round(cz + 15.9 * math.cos(a) - w * math.sin(a))
            if abs(x) <= 2:
                continue
            for y in range(f + 10, f + 16):
                for rr in (15.0, 16.0):
                    xx = round(rr * math.sin(a) + w * math.cos(a))
                    zz = round(cz + rr * math.cos(a) - w * math.sin(a))
                    bp.set(xx, y, zz, "glass_pane" if rr == 16.0 else "air")
    # doors: south (the way in) and north (to the sanctum), mist on both
    for z in range(cz + 13, cz + 19):
        for x in range(-1, 2):
            for y in range(f, f + 5):
                bp.set(x, y, z, "air")
    for z in range(cz - 18, cz - 13):
        for x in range(-1, 2):
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
    for x in (-2, 2):
        for y in range(f, f + 6):
            bp.set(x, y, cz + 17, RED + "[axis=y]")
    for x in range(-2, 3):
        bp.set(x, f + 5, cz + 17, TOP_W)
    # porch roof over the south door
    for x in range(-5, 6):
        for z in range(cz + 16, cz + 20):
            bp.set(x, f + 6, z, ROOF_SL + "[type=bottom]" if z == cz + 19 or abs(x) == 5 else ROOF)
    for x in (-4, 4):
        for y in range(f, f + 6):
            bp.set(x, y, cz + 18, RED + "[axis=y]")
    # ceiling (coffered), lanterns on chains, the oculus up to the bell
    for x, z, d in disc_cells(0, cz, 16.4):
        if d <= 2.5:
            continue
        bp.set(x, HALL_TOP + 1, z, "dark_oak_planks" if (x + z) % 4 else "spruce_planks")
    for i in range(8):
        a = math.radians(i * 45)
        x, z = round(10 * math.sin(a)), round(cz + 10 * math.cos(a))
        bp.chain(x, HALL_TOP - 2, z, HALL_TOP)
        bp.set(x, HALL_TOP - 3, z, LANT_H)
    for i in range(16):
        a = math.radians(i * 22.5)
        x, z = round(13.6 * math.sin(a)), round(cz + 13.6 * math.cos(a))
        if abs(x) <= 2:
            continue
        bp.set(x, f + 3, z, "dark_oak_slab[type=top,waterlogged=false]")
        bp.set(x, f + 4, z, LANT)
    # the arena heart
    bp.boss_seal(0, f - 1, cz, BOSS, 13)
    bp.mist(-1, f, cz + 15, 1, f + 4, cz + 15)
    bp.mist(-1, f, cz - 15, 1, f + 3, cz - 15)
    roof(bp)


def roof(bp):
    f = F_TOP
    cz = TZ
    y0 = HALL_TOP + 2
    radii = [20.5 - 1.6 * i for i in range(8)]
    for i in range(6):
        y = y0 + i
        for x, z, d in disc_cells(0, cz, radii[i]):
            if d <= 2.5:
                continue
            if d > radii[i] - 1.2:
                bp.set(x, y, z, stair(ROOF_ST, inward(x, z - cz)))
            elif d > radii[i] - 2.4:
                bp.set(x, y, z, ROOF)
            else:
                bp.set(x, y, z, TOP_W)
    # upturned eaves at the 8 corners
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        x, z = round(20.0 * math.sin(a)), round(cz + 20.0 * math.cos(a))
        bp.set(x, y0 + 1, z, stair(ROOF_ST, inward(x, z - cz)))
    # the light shaft from the oculus to the belfry
    yb = y0 + 6                                  # belfry floor
    for x, z, d in disc_cells(0, cz, 3.5):
        for y in range(HALL_TOP + 1, yb + 1):
            if d > 2.5:
                bp.set(x, y, z, "dark_oak_planks")
            else:
                bp.set(x, y, z, "air")
    # drum and belfry floor
    for x, z, d in disc_cells(0, cz, 9.5):
        if d > 2.5:
            bp.set(x, yb, z, "dark_oak_planks" if d < 8.5 else "spruce_planks")
    belfry(bp, yb)


def belfry(bp, yb):
    cz = TZ
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        for dx in (0, 1):
            for dz in (0, 1):
                x, z = sx * (5 + dx), cz + sz * (5 + dz)
                for y in range(yb + 1, yb + 9):
                    bp.set(x, y, z, RED + "[axis=y]")
    for i in range(-7, 8):
        for (x, z) in ((i, cz - 7), (i, cz + 7), (-7, cz + i), (7, cz + i)):
            bp.set(x, yb + 9, z, TOP_W)
    for i in range(-6, 7):
        bp.set(i, yb + 9, cz, "dark_oak_log[axis=x]")
    for x in (-6, 6):
        for z in (cz - 6, cz + 6):
            bp.set(x, yb + 1, z, "dark_oak_fence")
    # railing round the belfry floor
    for x, z, d in disc_cells(0, cz, 9.5):
        if d > 8.6:
            bp.set(x, yb + 1, z, "dark_oak_fence")
    # pyramid roof
    for i in range(7):
        h = 9 - i
        y = yb + 10 + i
        for x in range(-h, h + 1):
            for z in range(cz - h, cz + h + 1):
                if max(abs(x), abs(z - cz)) == h:
                    bp.set(x, y, z, stair(ROOF_ST, inward(x, z - cz)))
                elif i >= 5 or max(abs(x), abs(z - cz)) >= h - 1:
                    bp.set(x, y, z, ROOF)
    bp.set(0, yb + 16, cz, "gold_block")
    bp.set(0, yb + 17, cz, "gold_block")
    bp.set(0, yb + 18, cz, "lightning_rod")
    # the great bronze bell
    bp.set(0, yb + 8, cz, "iron_chain[axis=y,waterlogged=false]")
    prof = [(yb + 7, 1.5, "gold_block"), (yb + 6, 2.2, "waxed_copper_block"), (yb + 5, 2.6, "waxed_copper_block"),
            (yb + 4, 2.9, "waxed_cut_copper"), (yb + 3, 3.1, "waxed_copper_block"), (yb + 2, 3.4, "waxed_copper_block"),
            (yb + 1, 3.8, "gold_block")]
    for y, r, spec in prof:
        for x, z, d in disc_cells(0, cz, r):
            if d > r - 1.3 or y >= yb + 6:
                bp.set(x, y, z, spec)
    bp.chain(0, yb + 2, cz, yb + 5)
    bp.set(0, yb + 1, cz, "gold_block")


def sanctum(bp):
    """The reward room north of the hall, hanging over the cliff on corbels; its balcony is the leap."""
    f = HALL_F
    zs0, zs1 = -51, -41                     # walls (z)
    for x in range(-5, 6):
        for z in range(zs0, zs1 + 1):
            wall = abs(x) == 5 or z in (zs0, zs1)
            bp.set(x, f - 1, z, "polished_andesite" if not wall else "stone_bricks")
            for y in range(f, f + 7):
                if wall:
                    corner = abs(x) == 5 and z in (zs0, zs1, -46)
                    bp.set(x, y, z, RED + "[axis=y]" if corner else ("stone_bricks" if y <= f + 1 else "calcite"))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, f + 7, z, TOP_W)
    # corbels under the overhang
    for j, (y, zz, xx) in enumerate(((f - 2, -51, 5), (f - 3, -50, 4), (f - 4, -48, 3), (f - 5, -47, 2))):
        for x in range(-xx, xx + 1):
            for z in range(zz, NZ + 2):
                bp.set(x, y, z, "stone_bricks" if hash01(x, z, 21 + j) < 0.8 else "cracked_stone_bricks")
    for x in (-5, 5):
        for k in range(8):
            bp.set(x, f - 2 - k, -51 + k, RED + "[axis=y]" if k else RED + "[axis=y]")
    # gable roof (axis z)
    for z in range(zs0 - 1, zs1 + 1):
        for i in range(4):
            y = f + 8 + i
            bp.set(-6 + i, y, z, stair(ROOF_ST, "east"))
            bp.set(6 - i, y, z, stair(ROOF_ST, "west"))
            for x in range(-5 + i, 6 - i):
                bp.set(x, y, z, ROOF if i == 3 or abs(x) >= 5 - i else TOP_W)
    # door from the hall, the reward, the altar
    for z in (zs1,):
        for x in range(-1, 2):
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
    bp.chest(-3, f, -49, "south", loot=LOOT + "ascent_vault")
    bp.chest(3, f, -49, "south", loot=LOOT + "ascent_vault")
    bp.set(0, f, -48, "chiseled_stone_bricks")
    bp.set(0, f + 1, -48, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(-1, f, -48, "polished_andesite_slab[type=bottom,waterlogged=false]")
    bp.set(1, f, -48, "polished_andesite_slab[type=bottom,waterlogged=false]")
    bp.set(0, f + 6, -45, LANT_H)
    # the leap: an opening in the north wall, a balcony with a gap in its rail
    for x in range(-1, 2):
        for y in range(f, f + 3):
            bp.set(x, y, zs0, "air")
    for x in range(-2, 3):
        for z in (zs0 - 1, zs0 - 2):
            bp.set(x, f - 1, z, "spruce_planks")
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
    for z in (zs0 - 1, zs0 - 2):
        bp.set(-3, f, z, "dark_oak_fence")
        bp.set(3, f, z, "dark_oak_fence")
    for x in (-2, -1, 1, 2):
        bp.set(x, f, zs0 - 3, "dark_oak_fence")
    bp.set(-3, f + 1, zs0 - 2, LANT)
    bp.set(3, f + 1, zs0 - 2, LANT)


def plunge_pool(bp):
    """The deep pool at the foot of the north face that catches the leap, with steps out to the north."""
    zc = -55
    for x in range(-6, 7):
        for z in range(zc - 6, zc + 6):
            edge = abs(x) == 6 or z in (zc - 6, zc + 5)
            for y in range(-6, 1):
                if edge:
                    bp.set(x, y, z, "mossy_cobblestone" if hash3(x, y, z, 3) < 0.4 else "stone")
                elif y == -6:
                    bp.set(x, y, z, "gravel")
                else:
                    bp.set(x, y, z, "water")
            for y in range(1, 5):
                bp.set(x, y, z, "air")
    for i, x in enumerate(range(-1, 2)):
        for k in range(4):
            bp.set(x, -3 + k, zc - 6 + 0, stair("stone_brick_stairs", "north") if k == 3 else "stone_bricks")
    for x in range(-1, 2):
        bp.set(x, 0, zc - 6, stair("stone_brick_stairs", "north"))
        bp.set(x, 0, zc - 5, "water")
    for (x, z) in ((-7, zc - 7), (7, zc - 7), (-7, zc + 5), (7, zc + 5)):
        stone_lantern(bp, x, 1, z)


# ------------------------------------------------------------------ life: trees and flowers
def bent_spruce(bp, x, y, z, h, seed):
    """A wind-bent spruce: the trunk leans east (the wind comes from the west), foliage combed to the lee."""
    lean = 1 + int(hash01(x, z, seed) * 2)
    tx, top = x, y
    for i in range(h):
        tx = x + int(lean * (i / h) ** 1.6 + 0.5)
        bp.set(tx, y + i, z, "spruce_log[axis=y]")
        top = y + i
    for i in range(2, h + 2):
        yy = y + i
        rr = max(0, int((h + 1 - i) / (h - 1) * 3 + 0.5)) if i % 2 == 0 else max(0, int((h + 1 - i) / (h - 1) * 2))
        cx = x + int(lean * (min(i, h - 1) / h) ** 1.6 + 0.5)
        for dx in range(-rr // 2, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr and bp.get(cx + dx, yy, z + dz) in (None, "minecraft:air"):
                    bp.set(cx + dx, yy, z + dz, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")
    bp.set(tx, top + 1, z, "spruce_leaves[distance=1,persistent=true,waterlogged=false]")


def plants(bp, P):
    """Bent spruces and shrubs on rock ledges away from the route; flowers in the meadow at the foot."""
    route_cols = set(ROUTE.walk) | set(ROUTE.para)
    busy = set()
    for (x, z) in route_cols:
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                busy.add((x + dx, z + dz))
    for x, z, d in disc_cells(PX, PZ, 11):
        busy.add((x, z))
    tops = np.argwhere(P.top & P.shell)
    rng_n = 0
    placed = []
    order = sorted(tops.tolist(), key=lambda t: hash3(int(XS[t[0]]), t[1], int(ZS[t[2]]), 55))
    for i, y, k in order:
        x, z = int(XS[i]), int(ZS[k])
        if y < 4 or y > 104 or (x, z) in busy:
            continue
        if any(bp.get(x + dx, y + dy, z + dz) not in (None, "minecraft:air")
               for dx in (-2, 0, 2) for dz in (-2, 0, 2) for dy in (1, 4, 8)):
            continue
        if any(abs(x - a) < 7 and abs(z - b) < 7 and abs(y - c) < 10 for a, c, b in placed):
            continue
        ok = True
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                ii, kk = i + dx, k + dz
                if not (0 <= ii < P.S2.shape[0] and 0 <= kk < P.S2.shape[2]) or not P.S2[ii, y, kk] or \
                        (x + dx, z + dz) in route_cols:
                    ok = False
        if not ok or P.S2[i, y + 1:min(AY, y + 12), k].any():
            continue
        if math.hypot(x, z - (NZ + rof(y))) < rof(y) - 4 and y > 20:
            continue                                  # only on the outer flank, not on top of the plateau
        bent_spruce(bp, x, y + 1, z, 5 + int(hash01(x, z, 9) * 4), seed=x * 3 + z)
        bp.set(x, y, z, "coarse_dirt")
        placed.append((x, y, z))
        rng_n += 1
        if rng_n >= 30:
            break
    # a ring of spruces and boulders on the talus at the foot
    for i in range(44):
        ang = i * math.tau / 44 + 0.3 * (hash01(i, 0, 81) - 0.5)
        rr = rof(0) + 1 + 7 * hash01(i, 1, 82)
        x, z = round(rr * math.sin(ang)), round(NZ + rof(0) + rr * math.cos(ang))
        if (x, z) in busy or abs(x) < 16 and z < NZ + 10 or not (AX0 < x < AX1 and AZ0 < z < AZ1):
            continue
        i0, _, k0 = ai(x, 0, z)
        col = np.flatnonzero(P.top[i0, :14, k0])
        if not len(col):
            continue
        y = int(col[-1])
        if bp.get(x, y + 1, z) not in (None, "minecraft:air") or any(
                bp.get(x + dx, y + dy, z + dz) not in (None, "minecraft:air")
                for dx in (-2, 2) for dz in (-2, 2) for dy in (2, 5)):
            continue
        h = hash01(i, 2, 83)
        if h < 0.55:
            bent_spruce(bp, x, y + 1, z, 6 + int(h * 8), seed=i)
        elif h < 0.8:
            spruce(bp, x, y + 1, z, h=9 + int(h * 6), seed=i)
        else:
            boulder(bp, x, y + 1, z, r=2, seed=i)
        if h < 0.8:
            bp.set(x, y, z, "podzol[snowy=false]")
    # flowers and grass tufts on the foot's meadow tops
    for i, y, k in tops.tolist():
        x, z = int(XS[i]), int(ZS[k])
        if y < 12 and (x, z) not in route_cols and bp.get(x, y + 1, z) in (None, "minecraft:air"):
            h = hash3(x, y, z, 61)
            if h < 0.12:
                bp.set(x, y + 1, z, "short_grass")
            elif h < 0.15:
                bp.set(x, y + 1, z, ("cornflower", "oxeye_daisy", "dandelion", "allium")[int(h * 1000) % 4])


# ------------------------------------------------------------------ builder
def pilgrims_ascent(bp):
    P = Plan()
    P.rock()
    P.route()
    P.shrines()
    P.finish()
    write_rock(bp, P)
    build_route(bp)
    build_gates(bp)
    foot_shrine(bp)
    prayer_shrine(bp)
    waterfall_shrine(bp)
    bell_cave(bp, P)
    wind_bridge(bp)
    pinnacle(bp)
    hermit_cell(bp)
    # the stray ambush pocket off leg 1
    f1, zi = stray_pocket()
    for x in range(-14, -9):
        for z in range(zi - 2, zi + 1):
            bp.set(x, f1 - 1, z, "andesite")
            for y in range(f1, f1 + 3):
                bp.set(x, y, z, "air")
    bp.spawner(-12, f1, zi - 2, MOB_STRAY)
    summit(bp)
    plunge_pool(bp)
    plants(bp, P)


def _view_on(leg, side_seg, u, d=0, up=1.7):
    s = LEGS[leg]["segs"][side_seg]
    ux, uz = DIRS[s["facing"]]
    f, _ = seg_floor(s, u)
    return (s["p"][0] + ux * u, f, s["p"][1] + uz * u)


_lb = ROUTE.landing_box
VIEWS = [
    ("foot_gate", (0, F0, 77), (0, 70, 10)),
    ("switchback", (LEGS[2]["segs"][2]["p"][0] + 4, LEGS[2]["segs"][2]["f"], LEGS[2]["cz"] + LEGS[2]["r"] + 1),
     (30, 10, 60)),
    ("prayer_wheels", (_lb(0)[0] + 2, TURN_F[0], _lb(0)[3] - 1), (_lb(0)[0] + 4, TURN_F[0] + 2, _lb(0)[1])),
    ("bell_cave", (_lb(2)[0], TURN_F[2], _lb(2)[1] + 1), (_lb(2)[0] - 9, TURN_F[2] + 3, _lb(2)[1] - 5)),
    ("wind_bridge", ((PX + 7 + _lb(3)[0]) // 2 + 5, YT, PZ), (PX, YT + 4, PZ)),
    ("summit_terrace", (0, F_TOP, 0), (0, F_TOP + 30, TZ)),
    ("arena", (0, HALL_F, TZ + 12), (0, HALL_F + 10, TZ - 10)),
]


register(StructureDef(
    "pilgrims_ascent", "overworld",
    ["meadow", "grove", "snowy_slopes", "stony_peaks", "windswept_hills", "windswept_gravelly_hills",
     "windswept_forest"],
    [Piece("ascent", pilgrims_ascent, views=VIEWS)],
    spacing=80, separation=32, adaptation="beard_thin", max_distance=116,
    spawns=[("minecraft:stray", 10, 1, 2), ("brasshaven:skeleton_knight", 4, 1, 1)],
    title_fr="L'Ascension du pèlerin", title_en="Pilgrim's Ascent"))
