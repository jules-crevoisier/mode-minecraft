"""Glacier Hall of the Frost Jarls (Halle glaciaire des jarls): a longhouse-cathedral carved inside a glacier
tongue, under an ice-and-rock horn. Colossal tier (tools/BUILDING.md §1, §12 concept 10, §15), snowy biomes.

Silhouette (one noun phrase, §15.1): a glacier tongue ending in a 60-high blue ice cliff, a pointed gate carved in
the middle of the cliff between two frozen jarls 34 high, the prow of a buried longhouse roof breaking the ice crest
above the gate, and far behind, off the axis to the east, a dark rock horn rising to y ~126 out of the glacier head.

Layout, ground y = 0 (feet 1 on the outwash plain), x east, z south (+z = the snout, the approach):
  * approach: a jarls' camp and a cairn at the marker (south-west, z ~40), a path through a gap in the terminal
    moraine (two standing stones and a lintel frame the gate), an axis break, then the grand stair (7 wide, two
    flights) up a rock buttress to the gate terrace (feet 15) and its waystone. The snout cliff is carved flat there
    between two jambs of natural ice: the pointed portal 13 x 27 with its frame, a timber screen and a 3-wide
    wicket, the "Jarl's eye" rose of froglight and blue ice above it, a rune frieze, the statues on either side;
  * L0 (feet 15): the wicket passage (compression, 3 x 5, 8 long; guard room west, mead store east), then the
    Great Hall: a nave 23 wide and 38 high (pointed ice vault, blue ice ribs every bay on packed-ice columns 5 x 5),
    hearth pits on the axis, side aisles 7 wide with the feasting tables and frozen warriors in niches, side rooms
    off the aisles (armoury, kitchen, the hall of the frozen warriors, the huscarls' sleeping hall), the crossing
    (hub waystone, ring chandelier) with the transepts: west the Skald's stair (to L1) and the library, east the
    Seer's balcony out of the glacier's east cliff; the apse at the north end with the jarls' throne;
  * L1 (feet 28): galleries above the aisles over the nave (strays up there), joined round the apse by the
    ambulatory (it looks down the whole nave); from its north door a corridor to the crevasse bridge over the
    bergschrund between glacier and horn, open to the sky, the meltwater lake 28 below (a gap in the rail: the drop);
  * the horn: the gate hall, the Jarl's Stair (two 39-long runs through the ice west of the horn, 20 up), the site of grace (feet 48), a narrow way, the
    mist, the arena (r 16 under a dome, an oculus up the horn's throat), the vault behind it (tier 3), and the
    Jarl's Leap: a shaft 47 down into the spring pool of the meltwater river;
  * L-1 (feet 1): the river runs south under the glacier from the spring, through the crevasse (open sky) and
    under the hall's east side to the ice cave at the foot of the snout: the way out. On the way: the drowned hoard
    (stepping stones, tier 2-3) and a stair up into the huscarls' hall (iron door, lever on the river side);
  * L2 (optional): the loft stair from the east gallery comes out on the glacier crest in a turf hut; a dormer door
    leads into the longhouse loft under the roof ridge (bunks, a chest, a round window over the approach), whose
    north gable opens on a terrace over the crevasse (vista).
Shortcuts back (§10.4): the huscarl stair (L1 -> L0, iron door opened from the stair), the crevasse drop into the
lake, the river stair into the huscarls' hall (iron door, lever only below), the river cave out of the snout next to
the grand stair (after the boss).
Loot gradient (§15.6): camp / guard room / mead store / kitchen tier 1, armoury / galleries / sleeping hall tier 1-2,
skald library / frozen warriors / loft / balcony tier 2, drowned hoard tier 2-3, the vault tier 3.

The glacier is a hollow shell (BUILDING §1): ice 2 thick under every outer face and round every carved space; the
deep core stays unset. Ice never melts here: only packed and blue ice are used (no plain ice, no snow layers).
"""
import math

import numpy as np

from ..arch import boulder, spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3, pointed_arch
from ..parts import LOOT, MOD

# the hall's own jarl comes with the boss pass; until then the arena wakes the Grave Knight (a dead warrior king)
BOSS = "brasshaven:grave_knight"
MOB_STRAY = "minecraft:stray"
MOB_KNIGHT = "brasshaven:skeleton_knight"
MOB_DROWNED = "minecraft:drowned"

# ------------------------------------------------------------------ dimensions
X0, X1 = -84, 84
Z0, Z1 = -210, 44
AY = 130

F0 = 15                     # gate terrace, hall, side rooms
F1 = 28                     # galleries, ambulatory, crevasse bridge, horn gate hall
FG = 48                     # site of grace, arena, vault
FR = 1                      # river bank
LOFT_Y = 60                 # loft floor (feet 61)
ROOF_Z = (-12, -120)        # roof ridge span (gable walls on these rows)
NAVE_Z = (-14, -112)        # nave (the apse half-circle continues north of -112)
NAVE_W = 11                 # nave interior |x| <= 11
YS = 33                     # vault springing
VAULT = pointed_arch(12.0, 19.0)
AISLE = (17, 23)            # aisle interior |x|
AISLE_TOP = 25
GAL = (12, 18)              # gallery interior |x|
GAL_TOP = 33
RING = (12.0, 18.5)         # ambulatory ring radii round (0, APSE_Z)
APSE_Z = -112
RIBS = (-18, -28, -38, -48, -56, -68, -78, -88, -98, -108)
CROSS = (-59, -65)          # crossing bay (z); transepts z -58..-66
HC = (30, -172)             # horn centre (arena centre)
ARENA_R = 16
ARENA_WALL = FG + 12        # last air layer at the arena wall
ARENA_TOP = FG + 20         # dome apex
JARL_X = (-8, -46)          # the Jarl's Stair: two long runs west then back east through the ice by the horn
JARL_LANES = ((-157, -159), (-163, -165))
VAULT_BOX = (23, 35, -192, -200)
LEAP = (24, 26, -197, -199)  # the shaft (x0, x1, z0, z1)

# the meltwater river, from the spring pool under the leap to the pool on the outwash plain
RIVER = [(25, -198), (29, -180), (26, -160), (21, -146), (20, -136), (25, -120), (30, -100), (30, -62), (31, -22),
         (33, 1), (38, 12), (45, 24), (51, 33)]
PORTAL_Z = 2

# ------------------------------------------------------------------ materials
PI, BI, SNOW = "packed_ice", "blue_ice", "snow_block"
CAL, PDI = "calcite", "polished_diorite"
SP, SPL = "spruce_planks", "stripped_spruce_log"
DO = "dark_oak_planks"
ROOF_ST = "brasshaven:slate_roof_tile_stairs"
ROOF = "brasshaven:slate_roof_tiles"
ROOF_SL = "brasshaven:slate_roof_tile_slab"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
FROG = "pearlescent_froglight[axis=y]"
TOP_SLAB = "spruce_slab[type=top,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

# material classes of the solid mask, zones of the carved spaces
ICE, ROCK, MORAINE, MASON = 1, 2, 3, 4
Z_HALL, Z_TIMBER, Z_ROCK, Z_ROUGH, Z_OPEN = 1, 2, 3, 4, 5


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


def n1(x, z, scale, seed):
    return float(vnoise(np.array([x]), np.array([z]), scale, seed)[0])


XS = np.arange(X0, X1 + 1)
ZS = np.arange(Z0, Z1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")


def ai(x, y, z):
    return x - X0, y, z - Z0


# ------------------------------------------------------------------ 2D fields: outline, heights
def half_width(z):
    return np.interp(z, [-208, -206, -203, -198, -190, -170, -140, -100, -40, 0, 8],
                     [0, 14, 30, 40, 48, 58, 66, 66, 60, 52, 46])


def front_line(x):
    """z of the snout face at x: carved flat (z = 0) between the jambs, natural and bowed beyond."""
    ax = np.abs(np.asarray(x, float))
    nat = 4.5 - 13.0 * ((ax - 22) / 32.0) ** 2 + 3.0 * (vnoise(x, 0 * ax, 7.0, 5) - 0.5)
    return np.where(ax <= 22, 0.0, nat)


def vault_top(u):
    """Last air layer of the nave vault at distance u from the axis (or from the apse centre)."""
    return YS + VAULT(min(abs(u), 11.99))


def _fields():
    x, z = GX.astype(float), GZ.astype(float)
    W = half_width(z)
    edge = 3.2 * (fbm(z, np.sign(x) * 97.0, 9.0, 11) - 0.5) * 2
    tongue = (z <= front_line(x)) & (np.abs(x) <= W + edge) & (W > 0)
    lobe_e = ((x - 60) / 20.0) ** 2 + ((z + 100) / 26.0) ** 2
    lobe = lobe_e <= 1 + 0.25 * (vnoise(x, z, 5.0, 12) - 0.5)
    inside = tongue | lobe
    H0 = np.interp(z, [-210, -150, -136, -80, -30, 0, 8], [72, 72, 62, 60, 56, 51, 50])
    # a convex whaleback: the flanks round off to a low cliff (about 26) fluted by vertical ice ribs
    Hc = H0 - 34.0 * (np.minimum(np.abs(x) / np.maximum(W, 1), 1.0)) ** 2.2
    Hc += 3.0 * (vnoise(z * 1.0, np.sign(x) * 31.0, 3.0, 13) - 0.5) * (np.abs(x) > 0.8 * W)
    Hc += 2.4 * (fbm(x, z, 10.0, 3) - 0.5) * 2
    # the whaleback over the hall and its roof: the ice heaps up along the axis to bury the eaves
    span = (z <= 2) & (z >= -126)
    Hw = 60.0 - 0.55 * np.maximum(0, np.abs(x) - 8) + 1.2 * (fbm(x, z, 6.0, 4) - 0.5)
    H = np.where(span, np.maximum(Hc, Hw), Hc)
    roofz = (z <= ROOF_Z[0] + 2) & (z >= ROOF_Z[1] - 2) & (np.abs(x) <= 8)
    H = np.where(roofz, 60.0, H)
    # the head of the tongue breaks off in a stepped ice cliff behind the vault
    zb = -202.0 + 3.0 * (vnoise(x, 0 * x, 6.0, 17) - 0.5) * 2
    H = np.where(z < zb, np.minimum(H, 60.0 - (zb - z) * 8.0 - 4.0 * vnoise(x, z, 3.0, 18)), H)
    # the ice fall: a lobe of stepped seracs on the east side
    Hl = 4 * np.floor((44 - 16 * lobe_e + 7 * vnoise(x, z, 4.0, 14)) / 4)
    H = np.where(lobe & ~tongue, Hl, np.where(lobe & tongue, np.maximum(H, Hl), H))
    # the natural lip of the snout rounds off; the carved section stays crisp and tall
    d_face = front_line(x) - z
    carved = (np.abs(x) <= 24) & (z >= -14)
    H = np.where(tongue & (d_face < 3) & ~roofz & ~carved, H - (3 - d_face) * 1.3, H)
    H = np.where(tongue & carved & ~roofz, np.maximum(H, 58.5 - 0.15 * np.abs(x)), H)
    for i in range(26):
        sx = -50 + 100 * hash01(i, 3, 91)
        sz = front_line(np.array([sx]))[0] - 2 - 9 * hash01(i, 4, 91)
        if abs(sx) < 26:
            continue
        r = 1.6 + 1.6 * hash01(i, 5, 91)
        hh = 4 + 6 * hash01(i, 6, 91)
        m = np.hypot(x - sx, z - sz) <= r
        H = np.where(m & tongue, H + hh, H)
    # transverse crevasse grooves on the flanks (decorative)
    for zg in (-34, -50, -86, -98, -118):
        wav = zg + 2.0 * np.sin(x / 7.0)
        m = (np.abs(z - wav) < 1.1) & (np.abs(x) > 16)
        H = np.where(m & tongue, H - 7, H)
    return inside, tongue, lobe, np.maximum(H, 0)


INSIDE, TONGUE, LOBE, H2 = _fields()


def crevasse_z(x):
    return -140.0 + 2.0 * math.sin(x / 8.0) + 2.0 * (n1(x, 0, 6.0, 21) - 0.5)


def crevasse_hw(x, y):
    return 5.6 + max(0, y - 46) / 5.0 + 1.2 * (n1(x, y, 5.0, 22) - 0.5)


def horn_centre(y):
    return HC[0] + 0.02 * y, HC[1] - 0.05 * y


def horn_r(y):
    return 30.0 * max(0.0, 1 - y / 127.0) ** 0.8


def river_dist(x, z):
    """(signed distance to the river line, nearest segment, t); positive = west of the flow."""
    best = None
    for i in range(len(RIVER) - 1):
        (px, pz), (qx, qz) = RIVER[i], RIVER[i + 1]
        vx, vz = qx - px, qz - pz
        L2 = vx * vx + vz * vz
        t = min(1.0, max(0.0, ((x - px) * vx + (z - pz) * vz) / L2))
        cx, cz = px + vx * t, pz + vz * t
        d = math.hypot(x - cx, z - cz)
        if best is None or d < best[0]:
            side = vx * (z - cz) - vz * (x - cx)
            best = (d, 1 if side >= 0 else -1, i, t)
    d, sgn, i, t = best
    return d * sgn, i, t


# ------------------------------------------------------------------ the plan: solid mask, carved mask, zones
def dil6(a, n=1):
    out = a.copy()
    for _ in range(n):
        b = out.copy()
        b[1:, :, :] |= out[:-1, :, :]
        b[:-1, :, :] |= out[1:, :, :]
        b[:, 1:, :] |= out[:, :-1, :]
        b[:, :-1, :] |= out[:, 1:, :]
        b[:, :, 1:] |= out[:, :, :-1]
        b[:, :, :-1] |= out[:, :, 1:]
        out = b
    return out


class Plan:
    def __init__(self):
        shape = (len(XS), AY, len(ZS))
        self.S = np.zeros(shape, bool)
        self.MAT = np.zeros(shape, np.int8)
        self.K = np.zeros(shape, bool)
        self.ZONE = np.zeros(shape, np.int8)

    # ---- solids
    def glacier(self):
        S, MAT = self.S, self.MAT
        for y in range(1, AY):
            S[:, y, :] = INSIDE & (H2 > y)
        MAT[S] = ICE
        # the horn: a four-sided rock peak with arêtes, leaning a little north
        for y in range(1, 127):
            cx, cz = horn_centre(y)
            r = horn_r(y)
            if r <= 0.3:
                continue
            dx, dz = GX - cx, GZ - cz
            th = np.arctan2(dz, dx)
            rr = r * (1 + 0.17 * np.cos(4 * (th - 0.4))) + 1.7 * (fbm(th * r, y * 1.0, 8.0, 41) - 0.5) * 2
            m = np.hypot(dx, dz) < rr
            if FG - 2 <= y <= ARENA_TOP + 3:
                m |= np.hypot(GX - HC[0], GZ - HC[1]) <= ARENA_R + 3.5
            S[:, y, :] |= m
            MAT[:, y, :][m] = ROCK
        # the crevasse (bergschrund) between the glacier and the horn, from the river up to the sky
        for ix, x in enumerate(XS.tolist()):
            zc = crevasse_z(x)
            for y in range(1, AY):
                hw = crevasse_hw(x, y)
                k0 = max(0, int(math.ceil(zc - hw)) - Z0)
                k1 = min(len(ZS) - 1, int(math.floor(zc + hw)) - Z0)
                if k0 <= k1:
                    S[ix, y, k0:k1 + 1] = False
        # the terminal moraine (a crescent with gaps for the path and the river) and the lateral moraines
        x, z = GX.astype(float), GZ.astype(float)
        zm = 34.0 - 0.011 * x * x
        hm = 9.0 * np.exp(-((z - zm) / 5.0) ** 2) * np.clip((58 - np.abs(x)) / 10.0, 0, 1)
        hm *= 0.75 + 0.5 * fbm(x, z, 7.0, 31)
        hm = np.where(np.abs(x + 8) < 6.5, np.minimum(hm, np.clip(np.abs(x + 8) - 4.0, 0, 9) * 1.5), hm)
        W = half_width(z)
        lat = np.exp(-((np.abs(x) - (W + 6)) / 3.0) ** 2) * 5.0 * ((z < -6) & (z > -190)) * \
            (0.6 + 0.8 * fbm(x, z, 9.0, 33))
        lat = np.where(LOBE | (x > 34) & (z < -60) & (z > -140), 0, lat)
        hm = np.maximum(hm, lat)
        for xx in range(28, 62):
            for zz in range(-2, 44):
                if abs(river_dist(xx, zz)[0]) < 6.5:
                    hm[xx - X0, zz - Z0] = 0
        for y in range(1, 11):
            m = (hm > y) & ~INSIDE & ~S[:, y, :]
            S[:, y, :] |= m
            MAT[:, y, :][m] = MORAINE
        # the gate buttress: battered rock under the terrace and the grand stair
        for y in range(1, F0):
            k = (F0 - y) * 0.45
            jx = 21 + k + 1.5 * (vnoise(z, y, 4.0, 35) - 0.5) * 2
            m1 = (np.abs(x) <= jx) & (z >= 0) & (z <= 7 + k)
            m2 = (np.abs(x) <= 5 + k * 0.8) & (z >= 0) & (z <= 24 - (y - 1) * 1.23 + k * 0.5)
            m = (m1 | m2) & ~INSIDE
            S[:, y, :] |= m
            MAT[:, y, :][m] = MASON

    def cover(self, lift=3, slope=0.9, reach=9):
        """Swell the ice over every room that would break the surface of the convex profile: the column must
        stand ``lift`` above the highest carved cell under y 50, with a cone of ``slope`` per block around it."""
        S, K, MAT = self.S, self.K, self.MAT
        ys = np.arange(AY)[None, :, None]
        low = K & (ys < 50) & (self.ZONE != Z_OPEN)
        need = np.where(low.any(axis=1), (np.where(low, ys, -1)).max(axis=1) + lift + 1, 0).astype(float)
        cone = need.copy()
        for dx in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                d = math.hypot(dx, dz)
                if d == 0 or d > reach:
                    continue
                sh = np.roll(np.roll(need, dx, axis=0), dz, axis=1) - slope * d
                cone = np.maximum(cone, sh)
        top = np.where(S.any(axis=1), AY - 1 - np.argmax(S[:, ::-1, :], axis=1), 0)
        for i, k in np.argwhere((cone > top + 0.5) & INSIDE).tolist():
            x = int(XS[i])
            zc = crevasse_z(x)
            for y in range(int(top[i, k]) + 1, int(cone[i, k])):
                if abs(int(ZS[k]) - zc) <= crevasse_hw(x, y) + 0.5 or K[i, y, k]:
                    continue
                if MAT[i, y, k] == 0:
                    MAT[i, y, k] = ICE
                S[i, y, k] = True

    # ---- carving
    def box(self, x0, x1, z0, z1, feet, h, zone=Z_HALL):
        xa, xb = sorted((x0, x1))
        za, zb = sorted((z0, z1))
        sl = (slice(max(0, xa - X0), xb - X0 + 1), slice(max(0, feet), min(AY, feet + h)),
              slice(max(0, za - Z0), zb - Z0 + 1))
        self.K[sl] = True
        self.ZONE[sl] = zone

    def cell(self, x, y0, y1, z, zone):
        i, k = x - X0, z - Z0
        if 0 <= i < self.K.shape[0] and 0 <= k < self.K.shape[2] and y1 >= y0:
            self.K[i, max(0, y0):min(AY, y1 + 1), k] = True
            self.ZONE[i, max(0, y0):min(AY, y1 + 1), k] = zone

    def stairs(self, cells, zone):
        for (x, z, f, st) in cells:
            self.cell(x, f, f + 3, z, zone)


# ------------------------------------------------------------------ stairs
def dogleg(axis, lanes, a_lo, a_hi, f0, rise, up=1):
    """A stair well whose flights run along ``axis`` ('x' or 'z') between landings at both ends (3 deep, spanning
    both lanes). ``lanes``: two cross ranges (c0, c1), used alternately starting with the first; ``up`` = +1 when
    the first flight climbs towards a_hi. Returns (cells [(x, z, feet, stair facing or None)], end side, feet)."""
    n = a_hi - a_lo - 5
    cells = []
    allc = (min(l[0] for l in lanes), max(l[1] for l in lanes))
    fac = {1: "south", -1: "north"} if axis == "z" else {1: "east", -1: "west"}

    def add(a, c, f, st):
        cells.append((c, a, f, st) if axis == "z" else (a, c, f, st))

    def landing(at, f):
        rng = range(a_lo, a_lo + 3) if at == a_lo else range(a_hi - 2, a_hi + 1)
        for a in rng:
            for c in range(allc[0], allc[1] + 1):
                add(a, c, f, None)

    f = f0
    side = a_lo if up > 0 else a_hi
    landing(side, f)
    d = up
    li = 0
    while f < f0 + rise:
        k = min(n, f0 + rise - f)
        lane = lanes[li % 2]
        start = a_lo + 3 if d > 0 else a_hi - 3
        for i in range(n):
            a = start + d * i
            for c in range(lane[0], lane[1] + 1):
                add(a, c, f + i + 1 if i < k else f + k, fac[d] if i < k else None)
        f += k
        side = a_hi if d > 0 else a_lo
        landing(side, f)
        d = -d
        li += 1
    return cells, side, f


def jarl_cells():
    """The Jarl's Stair, L1 -> FG: from the horn gate hall west along the south lane (10 up, a step every 3 to
    4 blocks), a landing at the far end spanning both lanes, then back east along the north lane (10 up) to the
    landing by the site of grace."""
    cells = []
    xe, xw = JARL_X
    n = xe - xw + 1
    steps = {int(round(1.5 + i * (n - 3) / 9.0)) for i in range(10)}
    f = F1
    for x in range(-3, xe, -1):                                     # off the gate hall's north-west corner
        for z in range(JARL_LANES[0][1], -155):
            cells.append((x, z, f, None))
    for lane, d in ((JARL_LANES[0], -1), (JARL_LANES[1], 1)):
        for i in range(n):
            x = xe - i if d < 0 else xw + i
            st = None
            if i in steps:
                f += 1
                st = "west" if d < 0 else "east"
            for z in range(lane[1], lane[0] + 1):
                cells.append((x, z, f, st))
        if d < 0:
            for x in range(xw - 4, xw):
                for z in range(JARL_LANES[1][1], JARL_LANES[0][0] + 1):
                    cells.append((x, z, f, None))
    for x in range(xe + 1, -3):                                     # the landing by the grace
        for z in range(-168, JARL_LANES[1][0] + 1):
            cells.append((x, z, f, None))
    for z in range(-168, JARL_LANES[1][0] + 1):
        cells.append((xe, z, f, None))
    return cells, "east", f


def huscarl_cells():
    """Down from the east gallery passage (feet F1 at x 26) eastwards: 7 steps, a landing, 6 steps, to feet F0."""
    cells = []
    f = F1
    x = 27
    for i in range(13 + 3):
        if i == 7 or i == 8 or i == 9:
            st = None
        else:
            f -= 1
            st = "west"
        for z in (-102, -103, -104):
            cells.append((x, z, f, st))
        x += 1
    return cells


def loft_rise():
    """Feet on the glacier crest where the loft stair comes out."""
    return int(H2[30 - X0, -62 - Z0])


def _stairs():
    out = {}
    # the Skald's stair: west transept, L0 -> L1, flights along x, lanes south then north
    out["skald"] = dogleg("x", [(-66, -64), (-60, -58)], -39, -27, F0, F1 - F0, up=-1)
    # the Jarl's Stair: horn, L1 -> FG, flights along z, lanes east then west
    out["jarl"] = jarl_cells()
    # the river stair: bank -> the huscarls' hall
    out["river"] = dogleg("z", [(54, 56), (50, 52)], -93, -79, FR, F0 - FR, up=-1)
    # the loft stair: east gallery -> the glacier crest
    out["loft"] = dogleg("x", [(-60, -58), (-66, -64)], 24, 36, F1, loft_rise() - F1, up=1)
    out["huscarl"] = (huscarl_cells(), None, F0)
    return out


STAIRS = _stairs()


def portal_top(x):
    """Last air layer of the portal at x (straight jambs to y 32, pointed arch to y 41)."""
    return 32 + int(round(pointed_arch(6.6, 9.0)(min(abs(x), 6.5))))


def arcade_top(z):
    """Last air layer of the arcade opening at z (pointed over each 5-wide opening between two columns)."""
    above = [r for r in RIBS if r > z]
    below = [r for r in RIBS if r < z]
    lo = (above[-1] - 3) if above else NAVE_Z[0]
    hi = (below[0] + 3) if below else -110
    zc = (lo + hi) / 2.0
    half = (lo - hi) / 2.0 + 0.6
    return AISLE_TOP - 3 + int(round(3 * pointed_arch(half, 1.0)(min(abs(z - zc), half))))


def balcony_x():
    """Last solid x of the glacier's east face at z = -62 (counting from the axis)."""
    i, k = -X0, -62 - Z0
    while i + 1 < len(XS) and INSIDE[i + 1, k] and H2[i + 1, k] > F0 + 6:
        i += 1
    return int(XS[i])


def bridge_span():
    """(zs, zn): the first solid row south and north of the crevasse at x = 0 around F1."""
    zc = crevasse_z(0)
    hw = max(crevasse_hw(x, y) for x in (-2, 0, 2) for y in range(F1 - 1, F1 + 6))
    return int(math.floor(zc + hw)) + 1, int(math.ceil(zc - hw)) - 1


RIVER_CELLS = {}


def river_carve(P):
    """The tunnel along the river: water 4 wide (y -2..0), the bank 4 wide on its east side (feet 1), 7 high."""
    RIVER_CELLS.clear()
    x0 = min(p[0] for p in RIVER) - 8
    x1 = max(p[0] for p in RIVER) + 8
    z0 = min(p[1] for p in RIVER) - 6
    z1 = max(p[1] for p in RIVER) + 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            d, i, t = river_dist(x, z)
            if -5.5 <= d < 2.5:
                if i == 0 and t == 0.0:
                    continue
                kind = "water" if d >= -1.5 else "bank"
                RIVER_CELLS[(x, z)] = kind
                P.cell(x, FR, 7 if z < PORTAL_Z else 2, z, Z_ROUGH)
    # the ice cave at the foot of the snout: a rounded mouth wider and higher than the tunnel
    for x in range(24, 44):
        fl = front_line(np.array([x]))[0]
        for y in range(1, 11):
            for z in range(-4, 7):
                if ((x - 33) / 6.5) ** 2 + ((y - 1) / 9.0) ** 2 <= 1 and z >= fl - 4:
                    P.cell(x, y, y, z, Z_ROUGH)


# ------------------------------------------------------------------ carving every space
def carve_all(P):
    # ---- outside: terrace, portal recess
    P.box(-21, 21, 1, 6, F0, 6, Z_OPEN)
    for x in range(-6, 7):
        for z in range(-4, 1):
            P.cell(x, F0, portal_top(x), z, Z_HALL)
    # ---- L0: the wicket passage and its two side rooms
    P.box(-1, 1, -5, -13, F0, 5, Z_HALL)
    P.box(-16, -5, -6, -12, F0, 6, Z_TIMBER)          # guard room
    P.box(-4, -2, -9, -10, F0, 3, Z_TIMBER)
    P.box(5, 16, -6, -12, F0, 6, Z_TIMBER)            # mead store
    P.box(2, 4, -9, -10, F0, 3, Z_TIMBER)
    # ---- the nave and the apse
    for x in range(-NAVE_W, NAVE_W + 1):
        P.box(x, x, NAVE_Z[0], NAVE_Z[1], F0, int(vault_top(x)) - F0 + 1, Z_HALL)
    for x in range(-12, 13):
        for z in range(APSE_Z - 12, APSE_Z):
            d = math.hypot(x, z - APSE_Z)
            if d <= 11.5:
                P.cell(x, F0, int(vault_top(d)), z, Z_HALL)
    # ---- aisles, arcades, galleries, the ambulatory ring
    for s in (-1, 1):
        a0, a1 = sorted((s * AISLE[0], s * AISLE[1]))
        P.box(a0, a1, NAVE_Z[0], -110, F0, AISLE_TOP - F0 + 1, Z_HALL)
        c0, c1 = sorted((s * 12, s * 16))
        for z in range(-110, NAVE_Z[0] + 1):
            if any(abs(z - r) <= 2 for r in RIBS):
                continue
            P.box(c0, c1, z, z, F0, arcade_top(z) - F0 + 1, Z_HALL)
        g0, g1 = sorted((s * GAL[0], s * GAL[1]))
        P.box(g0, g1, NAVE_Z[0], APSE_Z, F1, GAL_TOP - F1 + 1, Z_HALL)
    for x in range(-19, 20):
        for z in range(APSE_Z - 19, APSE_Z):
            if RING[0] <= math.hypot(x, z - APSE_Z) <= RING[1]:
                P.cell(x, F1, GAL_TOP, z, Z_HALL)
    # ---- the west transept: the Skald's stair, a passage north of its well to the library
    P.box(-24, -28, -58, -66, F0, 6, Z_HALL)
    P.stairs(STAIRS["skald"][0], Z_HALL)
    P.box(-19, -26, -57, -59, F1, 5, Z_HALL)                        # skald stair top -> west gallery
    P.box(-24, -40, -55, -57, F0, 4, Z_HALL)
    P.box(-41, -52, -54, -70, F0, 7, Z_TIMBER)                      # skald library
    # ---- the east transept, the tunnel to the Seer's balcony, the loft stair above
    P.box(24, 46, -58, -66, F0, 10, Z_HALL)
    bx = balcony_x()
    P.box(47, bx, -61, -63, F0, 5, Z_ROUGH)
    P.box(bx + 1, bx + 4, -60, -64, F0, 4, Z_OPEN)
    P.box(19, 23, -61, -63, F1, 5, Z_HALL)
    P.stairs(STAIRS["loft"][0], Z_HALL)
    # ---- side rooms (doors through the aisle walls at |x| = 24)
    P.box(-25, -40, -26, -38, F0, 7, Z_TIMBER)                      # armoury
    P.box(-24, -24, -31, -33, F0, 4, Z_TIMBER)
    P.box(25, 40, -26, -38, F0, 7, Z_TIMBER)                        # kitchen
    P.box(24, 24, -31, -33, F0, 4, Z_TIMBER)
    P.box(-25, -46, -76, -104, F0, 9, Z_HALL)                       # hall of the frozen warriors
    P.box(-24, -24, -81, -83, F0, 4, Z_HALL)
    P.box(25, 48, -76, -100, F0, 7, Z_TIMBER)                       # the huscarls' sleeping hall
    P.box(24, 24, -86, -88, F0, 4, Z_TIMBER)
    # ---- the huscarl stair: east gallery -> sleeping hall
    P.box(19, 26, -102, -104, F1, 5, Z_HALL)
    P.stairs(STAIRS["huscarl"][0], Z_HALL)
    P.box(43, 48, -102, -104, F0, 5, Z_TIMBER)
    P.box(47, 47, -101, -101, F0, 2, Z_TIMBER)
    # ---- L1 north: corridor, the bridge clearance, the horn gate hall, the Jarl's Stair, grace, arena, vault
    zs, zn = bridge_span()
    P.box(-1, 1, -131, zs, F1, 5, Z_HALL)
    P.box(-2, 2, zs - 1, zn + 1, F1, 5, Z_OPEN)
    P.box(-7, 7, zn, -155, F1, 8, Z_ROCK)
    P.stairs(STAIRS["jarl"][0], Z_ROCK)
    P.box(-6, 6, -169, -176, FG, 6, Z_ROCK)                         # site of grace
    P.box(7, 14, -171, -173, FG, 5, Z_ROCK)                         # the narrow way to the mist
    for x in range(HC[0] - ARENA_R - 1, HC[0] + ARENA_R + 2):
        for z in range(HC[1] - ARENA_R - 1, HC[1] + ARENA_R + 2):
            d = math.hypot(x - HC[0], z - HC[1])
            if d <= ARENA_R + 0.4:
                P.cell(x, FG, dome_top(d), z, Z_ROCK)
    for y in range(ARENA_TOP, 127):                                  # the oculus up the horn's throat
        cx, cz = horn_centre(y)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                P.cell(int(round(cx)) + dx, y, y, int(round(cz)) + dz, Z_OPEN)
    P.box(29, 31, HC[1] - ARENA_R - 1, VAULT_BOX[2] + 1, FG, 4, Z_ROCK)  # north door -> vault
    P.box(VAULT_BOX[0], VAULT_BOX[1], VAULT_BOX[2], VAULT_BOX[3], FG, 6, Z_ROCK)
    P.box(LEAP[0], LEAP[1], LEAP[2], LEAP[3], FR, FG - FR, Z_ROUGH)  # the Jarl's Leap shaft
    P.box(LEAP[0] - 2, LEAP[1] + 2, LEAP[2] + 2, LEAP[3] - 2, FR, 5, Z_ROUGH)  # the spring pool cave
    # ---- the river tunnel (bank + water), the hoard, the river stair
    river_carve(P)
    P.box(36, 46, -58, -66, FR, 6, Z_ROUGH)                         # the drowned hoard
    P.stairs(STAIRS["river"][0], Z_ROUGH)
    P.box(35, 49, -79, -81, FR, 5, Z_ROUGH)                         # bank -> river stair well
    P.box(49, 49, -80, -80, F0, 2, Z_TIMBER)                        # its iron door into the sleeping hall
    # ---- L2: the loft under the roof ridge
    for z in range(ROOF_Z[0] - 1, ROOF_Z[1], -1):
        for x in range(-5, 6):
            P.cell(x, LOFT_Y + 1, LOFT_Y + 6 - abs(x), z, Z_OPEN)


def dome_top(d):
    return int(ARENA_WALL + 8 * math.sqrt(max(0.0, 1 - (d / (ARENA_R + 0.4)) ** 2)))


# ------------------------------------------------------------------ writing the massif
LOW = ("tuff", "andesite", "cobblestone", "packed_ice", "andesite", "packed_ice", "tuff")
ROCKS = ("stone", "andesite", "stone", "tuff", "deepslate", "stone", "andesite", "cobbled_deepslate", "stone",
         "tuff", "andesite", "stone")


def ice_ext(x, y, z, top, hcol, jit):
    h = hash3(x, y, z, 5)
    if top:
        return SNOW if h < 0.9 else PI
    if y >= hcol - 2 - jit * 2:
        return SNOW if h < 0.8 else PI
    if y < 4 + 4 * jit:
        return LOW[int(h * len(LOW))] if h < 0.6 else (PI if h < 0.93 else BI)
    s = y + 3 * jit
    if s % 10.5 < 0.9:
        return "tuff" if h < 0.5 else "andesite"
    if n1(x + z * 0.7, y * 0.12, 2.6, 9) > 0.7:
        return BI
    return PI if h < 0.94 else BI


def rock_ext(x, y, z, top, jit):
    h = hash3(x, y, z, 6)
    cx, cz = horn_centre(y)
    th = math.atan2(z - cz, x - cx)
    if top and (y > 112 or h < 0.45):
        return SNOW
    if math.cos(5 * th + y * 0.07) > 0.93 and y > 30:
        return BI if h < 0.4 else PI
    if h < 0.12:
        return "cobblestone"
    return ROCKS[int((y + 4 * jit) // 4) % len(ROCKS)]


def moraine_ext(x, y, z, top):
    h = hash3(x, y, z, 7)
    if top:
        return SNOW if h < 0.55 else ("stone" if h < 0.7 else ("andesite" if h < 0.82 else
                                                                ("cobblestone" if h < 0.92 else "tuff")))
    return ("stone", "andesite", "cobblestone", "tuff", "stone", "andesite")[min(5, int(h * 6))]


def mason_ext(x, y, z, top):
    h = hash3(x, y, z, 8)
    if y >= F0 - 3 and (abs(x) >= 19 or z >= 5):
        return "cracked_stone_bricks" if h < 0.18 else "stone_bricks"
    if top:
        return SNOW if h < 0.6 else "stone"
    return ("stone", "andesite", "cobblestone", "tuff", "stone")[min(4, int(h * 5))]


def hall_wall(x, y, z, layer):
    h = hash3(x, y, z, 9)
    if layer == 1:
        if y % 6 == 0:
            return BI
        return PI if h < 0.86 else (CAL if h < 0.92 else BI)
    return PI


def timber_wall(x, y, z, layer):
    if layer == 2:
        return PI
    if x % 4 == 0 and z % 4 == 0:
        return SPL + "[axis=y]"
    return SP


def rock_wall(x, y, z, layer):
    h = hash3(x, y, z, 10)
    if layer == 1:
        if y % 7 == 0:
            return "polished_deepslate"
        return "stone_bricks" if h < 0.6 else ("polished_andesite" if h < 0.85 else "cracked_stone_bricks")
    return "stone"


def rough_wall(x, y, z, layer):
    h = hash3(x, y, z, 11)
    if y <= 2:
        return ("tuff", PI, "cobblestone", "andesite", PI)[min(4, int(h * 5))]
    return PI if h < 0.62 else (BI if h < 0.85 else (SNOW if h < 0.93 else "tuff"))


WALLS = {Z_HALL: hall_wall, Z_TIMBER: timber_wall, Z_ROCK: rock_wall, Z_ROUGH: rough_wall, Z_OPEN: rough_wall}


def write_massif(bp, P):
    S, K = P.S, P.K
    S2 = S & ~K
    air_ext = ~S
    air_ext[:, 0, :] = False                      # the ground counts as solid
    # one exterior layer is watertight (6-connected); two near the ground, where the terrain meets the ice
    near_ext = dil6(air_ext, 1)
    near_ext[:, :10, :] |= dil6(air_ext, 2)[:, :10, :]
    kin = K & S
    near1 = dil6(kin, 1)
    near2 = dil6(near1, 1)
    shell = S2 & (near_ext | near2)
    shell |= S2 & ((P.MAT == MORAINE) | (P.MAT == MASON))     # the moraines and the buttress are solid through
    for sl in ((0, slice(None), slice(None)), (-1, slice(None), slice(None)),
               (slice(None), slice(None), 0), (slice(None), slice(None), -1)):
        shell[sl] |= S2[sl]
    top = S2.copy()
    top[:, :-1, :] &= ~S2[:, 1:, :]
    # zone of the interior walls: spread the carved cells' zones two steps into the solid
    Z = np.where(kin, P.ZONE, 0).astype(np.int8)
    for _ in range(2):
        Zn = Z.copy()
        for ax in range(3):
            for sh in (1, -1):
                r = np.roll(Z, sh, axis=ax)
                Zn = np.where((Zn == 0) & (r > 0) & S2, r, Zn)
        Z = Zn
    jitf = fbm(GX, GZ, 9.0, 51)
    # the snow cap follows the real top of each column (the cover pass and the cliff steps move it off H2)
    colh = np.where(S2.any(axis=1), AY - np.argmax(S2[:, ::-1, :], axis=1), 0)
    for i, y, k in np.argwhere(shell).tolist():
        x, z = int(XS[i]), int(ZS[k])
        zone = int(Z[i, y, k])
        if near2[i, y, k] and zone > 0 and zone != Z_OPEN and (near1[i, y, k] or not near_ext[i, y, k]):
            spec = WALLS[zone](x, y, z, 1 if near1[i, y, k] else 2)
        else:
            m = int(P.MAT[i, y, k])
            t = bool(top[i, y, k])
            if m == ICE:
                spec = ice_ext(x, y, z, t, float(colh[i, k]), float(jitf[i, k]))
            elif m == ROCK:
                spec = rock_ext(x, y, z, t, float(jitf[i, k]))
            elif m == MORAINE:
                spec = moraine_ext(x, y, z, t)
            else:
                spec = mason_ext(x, y, z, t)
        bp.set(x, y, z, spec)
    for i, y, k in np.argwhere(K).tolist():
        bp.set(int(XS[i]), y, int(ZS[k]), "air")
    # the ground layer under the rim of every mass (the core keeps its terrain; own_foundations carries the rim)
    s1 = S[:, 1, :]
    inner = s1.copy()
    for _ in range(3):
        e = inner.copy()
        e[1:, :] &= inner[:-1, :]
        e[:-1, :] &= inner[1:, :]
        e[:, 1:] &= inner[:, :-1]
        e[:, :-1] &= inner[:, 1:]
        inner = e
    P.CORE = inner
    for i, k in np.argwhere(s1 & ~inner).tolist():
        x, z = int(XS[i]), int(ZS[k])
        if bp.get(x, 0, z) is not None:
            continue
        h = hash01(x, z, 61)
        bp.set(x, 0, z, SNOW if h < 0.6 else ("stone" if h < 0.8 else "andesite"))


# ------------------------------------------------------------------ small parts
def lamp_post(bp, x, y, z, soul=False):
    bp.set(x, y, z, "spruce_fence")
    bp.set(x, y + 1, z, SOUL if soul else LANT)


def brazier(bp, x, y, z):
    """A stone bowl with a fire: polished blackstone base, a campfire on top (y + 1)."""
    bp.set(x, y, z, "polished_blackstone")
    bp.set(x, y + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def hang(bp, x, z, y_lamp, y_ceil, spec=LANT_H):
    """A lamp at y_lamp on a chain up to the ceiling block at y_ceil (the chain fills y_lamp+1..y_ceil-1)."""
    for y in range(y_lamp + 1, y_ceil):
        bp.set(x, y, z, CHAIN)
    bp.set(x, y_lamp, z, spec)


def niche_lamp(bp, x, y, z):
    """A lantern standing in a niche cut into a wall (the block below carries it)."""
    bp.set(x, y, z, LANT)


def wall_lamp(bp, x, y, z):
    """A lantern on a slab bracket against a column or a wall: the slab at (x, y, z), the lantern on it."""
    bp.set(x, y, z, "stone_brick_slab[type=top,waterlogged=false]")
    bp.set(x, y + 1, z, LANT)


def warrior(bp, x, y, z, facing, seed=0):
    """A frozen warrior on a plinth at y: ice legs, blue ice chest, a skull for a head, a spear of bars beside him
    (when there is room), a round shield (a trapdoor) on his front."""
    dx, dz = DIRS[facing]
    rot = {"south": 0, "west": 4, "north": 8, "east": 12}[facing]
    bp.set(x, y, z, PDI)
    bp.set(x, y + 1, z, PI)
    bp.set(x, y + 2, z, BI)
    bp.set(x, y + 3, z, f"skeleton_skull[rotation={rot}]")
    px, pz = (-dz, dx) if hash01(x, z, seed) < 0.5 else (dz, -dx)
    sx, sz = x + px, z + pz
    if all(bp.get(sx, yy, sz) in (None, "minecraft:air") for yy in range(y + 1, y + 4)):
        for yy in range(y + 1, y + 4):
            bp.set(sx, yy, sz, "iron_bars")
    bp.set(x + dx, y + 2, z + dz, f"spruce_trapdoor[facing={facing},half=top,open=true,powered=false,"
                                  f"waterlogged=false]")


def long_table(bp, x, z0, z1, y, benches=True):
    """A feasting table along z at x: spruce slab top on fence legs every 3, benches on both sides."""
    a0, a1 = sorted((z0, z1))
    for z in range(a0, a1 + 1):
        bp.set(x, y, z, "spruce_fence" if (z - a0) % 3 == 0 or z == a1 else TOP_SLAB)
        if benches:
            for sx, f in ((x - 1, "east"), (x + 1, "west")):
                bp.set(sx, y, z, stair("spruce_stairs", f))


def candles(bp, x, y, z, n=3):
    bp.set(x, y, z, f"candle[candles={n},lit=true,waterlogged=false]")


def room_floor(bp, x0, x1, z0, z1, y, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            bp.set(x, y, z, spec(x, z) if callable(spec) else spec)


def plank_floor(x, z):
    return SPL + "[axis=x]" if z % 4 == 0 else SP


def beams(bp, x0, x1, z0, z1, y, axis="x", every=4):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            if (z % every == 0) if axis == "x" else (x % every == 0):
                bp.set(x, y, z, f"dark_oak_log[axis={axis}]")


def build_stair_cells(bp, cells, stair_spec, floor_spec):
    for (x, z, f, st) in cells:
        bp.set(x, f - 1, z, stair(stair_spec, st) if st else floor_spec)


def out_dir(dx, dz):
    """The facing of a stair whose high side points towards the centre (dx, dz = offset from the centre)."""
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


# ------------------------------------------------------------------ outside: the gate, the terrace, the statues
def gate_face(bp):
    """The carved section of the snout cliff: the portal frame, the Jarl's eye, the frieze, the timber screen."""
    zf = 1
    # the frieze: a calcite string course with a cornice slab, rune glyphs under it
    for x in range(-22, 23):
        bp.set(x, 52, zf, CAL)
        bp.set(x, 53, zf, "polished_diorite_slab[type=bottom,waterlogged=false]")
        if x % 3 == 0 and abs(x) <= 21:
            bp.set(x, 50, zf, "chiseled_stone_bricks")
    # the portal frame: jambs of calcite and diorite, two bands of voussoirs over the arch
    for x in range(-8, 9):
        u = abs(x)
        if u >= 7:
            for y in range(F0, 34):
                bp.set(x, y, zf, CAL if u == 7 else PDI)
            for y in range(34, 36 + 8 - u):
                bp.set(x, y, zf, CAL)
        else:
            t = portal_top(x)
            bp.set(x, t + 1, zf, CAL)
            bp.set(x, t + 2, zf, PDI)
    bp.set(0, 44, zf, "chiseled_quartz_block")
    # the Jarl's eye: a rose of blue ice spokes round a froglight, framed in polished diorite (the focal light)
    cy = 47
    for x in range(-4, 5):
        for y in range(cy - 4, cy + 5):
            d = math.hypot(x, y - cy)
            if d > 4.4:
                continue
            if d > 3.5:
                spec = PDI
            elif d < 1.2:
                spec = FROG
            elif abs(x) == abs(y - cy) or x == 0 or y == cy:
                spec = BI
            else:
                spec = "light_blue_stained_glass"
            bp.set(x, y, zf, spec)
    # the timber screen in the portal (z = -5): the great door (dark oak, iron bands) with the 3-wide wicket
    for x in range(-6, 7):
        for y in range(F0, portal_top(x) + 1):
            if abs(x) <= 1 and y <= F0 + 3:
                continue
            if abs(x) <= 3 and y <= F0 + 11:
                spec = "polished_blackstone" if y in (F0 + 4, F0 + 9) else (DO if x % 2 else "dark_oak_log[axis=y]")
            elif abs(x) == 6 or y == F0 + 12 or abs(x) == 4:
                spec = "dark_oak_log[axis=y]"
            else:
                spec = SP if (x + y) % 2 else "spruce_log[axis=y]"
            bp.set(x, y, -5, spec)
    for x in (-2, 2):
        for y in range(F0, F0 + 4):
            bp.set(x, y, -5, "dark_oak_log[axis=y]")
    for x in range(-2, 3):
        bp.set(x, F0 + 4, -5, "dark_oak_log[axis=x]")
    for x in (-5, 5):
        lamp_post(bp, x, F0, -2)


def terrace(bp):
    """The gate terrace (floor y 14): flagstones, the processional axis, parapets, braziers, the waystone."""
    y = F0 - 1
    for x in range(-21, 22):
        for z in range(1, 7):
            if abs(x) <= 1:
                spec = PDI
            elif abs(x) <= 6:
                spec = "polished_andesite" if (x + z) % 2 else "stone_bricks"
            else:
                spec = "stone_bricks" if hash01(x, z, 21) < 0.7 else "cracked_stone_bricks"
            bp.set(x, y, z, spec)
    for x in range(-6, 7):
        for z in range(-4, 1):
            bp.set(x, y, z, PDI if abs(x) <= 1 else "polished_andesite")
    for x in range(-21, 22):
        if abs(x) > 3:
            bp.set(x, F0, 6, "stone_brick_wall")
    for x in (-21, 21):
        for z in range(1, 6):
            bp.set(x, F0, z, "stone_brick_wall")
    brazier(bp, -6, F0, 5)
    brazier(bp, 6, F0, 5)
    bp.set(-7, F0, 2, MOD["waystone"])
    lamp_post(bp, -8, F0, 5)
    lamp_post(bp, 8, F0, 5)


def grand_stair(bp):
    """Two flights of 7 (7 wide) from the outwash plain to the terrace, a landing between, parapets and fires."""
    def row(z, f, st):
        for x in range(-3, 4):
            spec = "polished_diorite_stairs" if abs(x) <= 1 else "stone_brick_stairs"
            bp.set(x, f - 1, z, stair(spec, "north") if st else (PDI if abs(x) <= 1 else "stone_bricks"))
            for yy in range(f, f + 4):
                bp.set(x, yy, z, "air")
            for yy in range(max(0, f - 6), f - 1):
                if bp.get(x, yy, z) in (None, "minecraft:air"):
                    bp.set(x, yy, z, "stone_bricks")
        for x in (-4, 4):
            bp.set(x, f - 1, z, "stone_bricks")
            bp.set(x, f, z, "stone_brick_wall")
            for yy in range(max(0, f - 6), f - 1):
                if bp.get(x, yy, z) in (None, "minecraft:air"):
                    bp.set(x, yy, z, "stone_bricks")
    row(25, 1, False)
    row(24, 1, False)
    for i in range(7):
        row(23 - i, 2 + i, True)
    for z in (16, 15, 14):
        row(z, 8, False)
    for i in range(7):
        row(13 - i, 9 + i, True)
    for x in (-4, 4):
        bp.set(x, 8, 15, "polished_blackstone")
        bp.set(x, 9, 15, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        bp.set(x, 1, 25, "stone_bricks")
        bp.set(x, 2, 25, LANT)


def statue(bp, cx):
    """A frozen jarl 34 high standing guard against the cliff, both hands on the pommel of a sword planted point
    down in front of him; a beard of calcite, a winged helm, snow on the shoulders."""
    y0 = F0 + 3
    cz = 3

    def ell(c, r, spec, cut=None):
        ex, ey, ez = c
        for x in range(int(ex - r[0]) - 1, int(ex + r[0]) + 2):
            for y in range(int(ey - r[1]) - 1, int(ey + r[1]) + 2):
                for z in range(int(ez - r[2]) - 1, int(ez + r[2]) + 2):
                    if z < 1 or (cut and not cut(x, y, z)):
                        continue
                    if ((x - ex) / r[0]) ** 2 + ((y - ey) / r[1]) ** 2 + ((z - ez) / r[2]) ** 2 <= 1:
                        bp.set(x, y, z, spec(x, y, z) if callable(spec) else spec)

    def body(x, y, z):
        return PI if hash3(x, y, z, 23) < 0.85 else BI
    for x in range(cx - 6, cx + 7):
        for z in range(1, 6):
            for y in range(F0, y0):
                edge = abs(x - cx) == 6 or z == 5
                bp.set(x, y, z, PDI if y == y0 - 1 else ("stone_bricks" if edge else "stone"))
    for s in (-1, 1):
        ell((cx + 2.3 * s, y0 + 1.2, cz + 0.6), (1.9, 1.6, 2.4), "polished_deepslate")
        ell((cx + 2.2 * s, y0 + 6.5, cz), (1.8, 5.0, 1.8), body)
    ell((cx, y0 + 12.5, cz), (4.6, 3.6, 2.6), body)
    ell((cx, y0 + 19.0, cz), (4.9, 6.2, 2.7), body)
    for x in range(cx - 5, cx + 6):
        for z in range(1, 6):
            if bp.get(x, y0 + 14, z) in ("minecraft:packed_ice", "minecraft:blue_ice"):
                bp.set(x, y0 + 14, z, "polished_deepslate")
    bp.set(cx, y0 + 14, cz + 3, "gold_block")
    for s in (-1, 1):
        ell((cx + 5.0 * s, y0 + 23.5, cz), (2.0, 2.0, 2.0), body)
        for t in np.linspace(0, 1, 12):
            ell((cx + s * (5.4 - 4.0 * t), y0 + 22.5 - 8.5 * t, cz + 0.2 + 2.2 * t), (1.3, 1.3, 1.3), body)
    ell((cx, y0 + 28.0, cz), (2.4, 2.8, 2.3), PI)
    ell((cx, y0 + 24.8, cz + 1.6), (2.2, 2.6, 1.2), CAL)
    ell((cx, y0 + 30.0, cz), (2.7, 1.8, 2.6), "polished_deepslate", cut=lambda x, y, z: y >= y0 + 29)
    bp.set(cx, y0 + 28, cz + 3, BI)
    for s in (-1, 1):
        for k in range(4):
            for zz in (cz, cz - 1):
                bp.set(cx + s * (3 + k // 2), y0 + 30 + k, zz, "bone_block[axis=y]")
    bp.set(cx, y0 + 32, cz, BI)
    sz = cz + 2
    for y in range(y0, y0 + 12):
        bp.set(cx, y, sz, BI)
    for x in range(cx - 2, cx + 3):
        bp.set(x, y0 + 12, sz, "polished_deepslate")
    bp.set(cx, y0 + 13, sz, "stripped_dark_oak_log[axis=y]")
    bp.set(cx, y0 + 14, sz, "gold_block")
    for x in range(cx - 7, cx + 8):
        for z in range(1, 7):
            for y in range(y0 + 34, y0 + 18, -1):
                b = bp.get(x, y, z)
                if b in ("minecraft:packed_ice", "minecraft:blue_ice", "minecraft:polished_deepslate"):
                    if bp.get(x, y + 1, z) in (None, "minecraft:air"):
                        bp.set(x, y, z, SNOW)
                    break


# ------------------------------------------------------------------ the hall
def hall_floor(x, z):
    if abs(x) <= 1:
        return "smooth_stone" if z % 6 else "chiseled_stone_bricks"
    if abs(x) in (4, 5):
        return PDI
    h = hash01(x, z, 31)
    return "polished_andesite" if h < 0.45 else ("stone_bricks" if h < 0.8 else "andesite")


HEARTHS = (-23, -33, -43, -73, -83, -93, -103)


def nave(bp):
    y = F0 - 1
    for x in range(-NAVE_W, NAVE_W + 1):
        for z in range(NAVE_Z[1], NAVE_Z[0] + 1):
            bp.set(x, y, z, hall_floor(x, z))
    for x in range(-12, 13):
        for z in range(APSE_Z - 12, APSE_Z):
            if math.hypot(x, z - APSE_Z) <= 11.5:
                bp.set(x, y, z, hall_floor(x, z))
    # hearth pits on the axis, one per bay (a rim of slabs round a bed of fires), none in the crossing
    for zc in HEARTHS:
        for x in range(-2, 3):
            for z in range(zc - 2, zc + 3):
                if abs(x) == 2 or abs(z - zc) == 2:
                    bp.set(x, F0, z, "stone_brick_slab[type=bottom,waterlogged=false]")
                else:
                    bp.set(x, y, z, "polished_blackstone")
                    if (x + z) % 2 == 0:
                        bp.set(x, F0, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the ribs: blue ice bands under the vault (2 thick), down the walls to the columns, a calcite boss
    for r in RIBS:
        for z in (r, r - 1):
            for x in range(-NAVE_W, NAVE_W + 1):
                t = int(vault_top(x))
                bp.set(x, t, z, BI)
                bp.set(x, t - 1, z, BI if abs(x) < 10 else PI)
            for s in (-1, 1):
                for yy in range(AISLE_TOP + 1, YS + 6):
                    if bp.get(s * NAVE_W, yy, z) == "minecraft:air":
                        bp.set(s * NAVE_W, yy, z, BI)
            bp.set(0, int(vault_top(0)) - 2, z, CAL)
    for z in range(NAVE_Z[1], NAVE_Z[0] + 1):
        bp.set(0, int(vault_top(0)), z, BI)
    for ang in range(-75, 76, 25):
        a = math.radians(ang)
        for k in range(0, 12):
            x, z = round(k * math.sin(a)), round(APSE_Z - k * math.cos(a))
            d = math.hypot(x, z - APSE_Z)
            if d <= 11.5:
                bp.set(x, int(vault_top(d)), z, BI)
    # columns: 5 x 5 packed ice shafts with blue ice arrises, a calcite base and capital
    for r in RIBS:
        for s in (-1, 1):
            for x in range(12, 17):
                for z in range(r - 2, r + 3):
                    corner = x in (12, 16) and z in (r - 2, r + 2)
                    for yy in range(F0, AISLE_TOP + 2):
                        bp.set(s * x, yy, z, CAL if yy == F0 or yy >= AISLE_TOP else (BI if corner else PI))
            wall_lamp(bp, s * 11, F0 + 4, r)
            wall_lamp(bp, s * 17, F0 + 4, r)
            ban = "blue_wall_banner" if (r // 10) % 2 else "light_gray_wall_banner"
            for dz in (-1, 1):
                bp.set(s * 11, F0 + 9, r + dz, f"{ban}[facing={'west' if s > 0 else 'east'}]")
    # lamps on long chains from the vault over the lanes beside the hearths
    for r in RIBS:
        for x in (-7, 7):
            hang(bp, x, r - 5 if r != -56 else r - 3, F0 + 12, int(vault_top(x)))


def aisles(bp):
    y = F0 - 1
    doors = set(range(-33, -30)) | set(range(-83, -80)) | set(range(-88, -85)) | set(range(-66, -54))
    for s in (-1, 1):
        for x in range(AISLE[0], AISLE[1] + 1):
            for z in range(-110, NAVE_Z[0] + 1):
                bp.set(s * x, y, z, SP if z % 5 else SPL + "[axis=x]")
                bp.set(s * x, AISLE_TOP + 1, z, "dark_oak_log[axis=x]" if z % 5 == 0 else SP)
        for x in range(12, 17):
            for z in range(-110, NAVE_Z[0] + 1):
                if bp.get(s * x, F0, z) == "minecraft:air":
                    bp.set(s * x, y, z, PDI)
        # feasting tables in each bay against the outer wall, frozen warriors in niches at the ribs
        for z0 in range(-21, -108, -10):
            zs = [z for z in range(z0, z0 - 6, -1) if z not in doors]
            if len(zs) >= 4:
                long_table(bp, s * 21, zs[0], zs[-1], F0)
        for r in RIBS:
            nx = s * (AISLE[1] + 1)
            if r in (-56, -68) or any(abs(r - d) <= 1 for d in doors):
                continue
            if bp.get(s * (AISLE[1] + 2), F0 + 1, r) not in (None, "minecraft:packed_ice", "minecraft:blue_ice",
                                                               "minecraft:calcite"):
                continue
            for yy in range(F0, F0 + 5):
                bp.set(nx, yy, r, "air")
            warrior(bp, nx, F0 - 1, r, "west" if s > 0 else "east", seed=r)
        for z in range(-26, -110, -10):
            hang(bp, s * 19, z, AISLE_TOP - 2, AISLE_TOP + 1)


def galleries(bp):
    y = F1 - 1
    for s in (-1, 1):
        for x in range(GAL[0], GAL[1] + 1):
            for z in range(APSE_Z, NAVE_Z[0] + 1):
                bp.set(s * x, y, z, SP)
        for z in range(APSE_Z, NAVE_Z[0] + 1):
            bp.set(s * GAL[0], F1, z, "spruce_fence")
        for r in RIBS:
            for z in (r, r - 1):
                for x in range(GAL[0] + 1, GAL[1] + 1):
                    bp.set(s * x, GAL_TOP, z, BI)
            hang(bp, s * 16, r - 5 if r != -56 else r - 3, GAL_TOP - 2, GAL_TOP + 1)
    for x in range(-19, 20):
        for z in range(APSE_Z - 19, APSE_Z):
            d = math.hypot(x, z - APSE_Z)
            if RING[0] <= d <= RING[1]:
                bp.set(x, y, z, SP)
                if d < RING[0] + 0.9:
                    bp.set(x, F1, z, "spruce_fence")
    for ang in range(-80, 81, 40):
        a = math.radians(ang)
        hang(bp, round(16 * math.sin(a)), round(APSE_Z - 16 * math.cos(a)), GAL_TOP - 2, GAL_TOP + 1)
    bp.spawner(-16, F1, -40, MOB_STRAY)
    bp.spawner(16, F1, -84, MOB_STRAY)
    bp.chest(-18, F1, -72, "east", loot=LOOT + "glacier_armory")
    bp.chest(18, F1, -46, "west", loot=LOOT + "glacier_armory")
    bp.barrel(-18, F1, -74, "up")
    bp.barrel(18, F1, -44, "up")


def crossing(bp):
    """The hub: a rune circle in the floor, a ring chandelier of eight lanterns, the hub waystone."""
    cz = -62
    for x in range(-6, 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x, z - cz)
            if 4.5 < d <= 5.5:
                bp.set(x, F0 - 1, z, BI)
            elif d <= 1.5:
                bp.set(x, F0 - 1, z, CAL)
            elif d <= 4.5 and (x == 0 or z == cz):
                bp.set(x, F0 - 1, z, PDI)
    y = 36
    for (x, z) in ((-3, cz), (3, cz), (0, cz - 3), (0, cz + 3)):
        for yy in range(y + 1, int(vault_top(x)) + 1):
            bp.set(x, yy, z, CHAIN)
    for x in range(-4, 5):
        for z in range(cz - 4, cz + 5):
            if 2.5 < math.hypot(x, z - cz) <= 4.3:
                bp.set(x, y, z, "dark_oak_slab[type=bottom,waterlogged=false]")
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        bp.set(round(3.6 * math.sin(a)), y - 1, round(cz + 3.6 * math.cos(a)), LANT_H)
    bp.set(0, int(vault_top(0)) - 1, cz, FROG)
    bp.set(6, F0, cz + 4, MOD["waystone"])
    lamp_post(bp, 7, F0, cz + 6)


def transepts(bp):
    # west: the Skald's stair (L0 -> L1), the passage to the library
    room_floor(bp, -24, -28, -58, -66, F0 - 1, lambda x, z: "polished_andesite" if (x + z) % 2 else "stone_bricks")
    room_floor(bp, -24, -40, -55, -57, F0 - 1, lambda x, z: "polished_andesite" if (x + z) % 2 else "stone_bricks")
    build_stair_cells(bp, STAIRS["skald"][0], "stone_brick_stairs", "polished_andesite")
    room_floor(bp, -19, -26, -57, -59, F1 - 1, SP)
    niche_lamp(bp, -24, F0 + 1, -54)
    niche_lamp(bp, -34, F0 + 1, -54)
    for (x, z) in ((-27, -67), (-39, -67), (-27, -57)):
        niche_lamp(bp, x, F0 + 7 if x == -39 else F0 + 1, z)
    niche_lamp(bp, -39, F0 + 8, -57)
    niche_lamp(bp, -27, F1 + 1, -67)
    # east: the Seer's balcony tunnel and the loft stair above
    room_floor(bp, 24, 46, -58, -66, F0 - 1, lambda x, z: "polished_andesite" if (x + z) % 2 else "stone_bricks")
    for x in range(30, 47, 8):
        hang(bp, x, -62, F0 + 6, F0 + 10)
    build_stair_cells(bp, STAIRS["loft"][0], "spruce_stairs", SP)
    room_floor(bp, 19, 23, -61, -63, F1 - 1, SP)


def apse(bp):
    """The jarls' throne on a three-step dais at the end of the axis: a seat of blue ice and dark oak, braziers."""
    cz = APSE_Z - 4
    for k, r in enumerate((9.5, 7.5, 5.5)):
        for x in range(-10, 11):
            for z in range(APSE_Z - 12, APSE_Z + 6):
                d = math.hypot(x, z - cz)
                if d <= r and (z > APSE_Z or math.hypot(x, z - APSE_Z) <= 11.5):
                    if d > r - 1:
                        bp.set(x, F0 + k, z, stair("polished_diorite_stairs", out_dir(x, z - cz)))
                    else:
                        bp.set(x, F0 + k, z, PDI if k < 2 else CAL)
    tz = cz - 2
    fy = F0 + 3
    for x in range(-2, 3):
        for z in range(tz - 1, tz + 1):
            bp.set(x, fy, z, BI)
    bp.set(0, fy, tz + 1, stair("dark_oak_stairs", "north"))
    for x in (-1, 1):
        bp.set(x, fy, tz + 1, "dark_oak_slab[type=bottom,waterlogged=false]")
    for x in range(-2, 3):
        for yy in range(fy + 1, fy + 7 - abs(x)):
            bp.set(x, yy, tz - 1, BI if abs(x) == 2 or yy == fy + 6 - abs(x) else DO)
    bp.set(0, fy + 7, tz - 1, "gold_block")
    for x in (-6, 6):
        brazier(bp, x, F0 + 2, cz)


# ------------------------------------------------------------------ rooms
def guard_room(bp):
    room_floor(bp, -16, -2, -6, -12, F0 - 1, plank_floor)
    beams(bp, -16, -5, -6, -12, F0 + 6, axis="z")
    for z in (-7, -11):
        bp.bed(-15, F0, z, "east", color="gray")
    bp.chest(-6, F0, -12, "north", loot=LOOT + "glacier_hall")
    bp.barrel(-7, F0, -12, "up")
    bp.set(-9, F0, -12, "grindstone[face=floor,facing=north]")
    bp.spawner(-12, F0, -9, MOB_STRAY)
    hang(bp, -9, -9, F0 + 3, F0 + 6)
    hang(bp, 0, -9, F0 + 3, F0 + 5)


def mead_store(bp):
    room_floor(bp, 2, 16, -6, -12, F0 - 1, plank_floor)
    beams(bp, 5, 16, -6, -12, F0 + 6, axis="z")
    for z in range(-6, -13, -1):
        for yy in (F0, F0 + 1):
            bp.barrel(16, yy, z, "west")
    for x in range(8, 15, 2):
        bp.barrel(x, F0, -6, "south")
    bp.set(9, F0, -12, TOP_SLAB)
    bp.set(10, F0, -12, TOP_SLAB)
    bp.chest(12, F0, -12, "north", loot=LOOT + "glacier_hall")
    hang(bp, 10, -9, F0 + 3, F0 + 6)


def armoury(bp):
    room_floor(bp, -25, -40, -26, -38, F0 - 1, lambda x, z: "stone_bricks" if (x + z) % 3 else "polished_andesite")
    room_floor(bp, -24, -24, -31, -33, F0 - 1, "polished_andesite")
    beams(bp, -25, -40, -26, -38, F0 + 7, axis="z", every=5)
    bp.set(-37, F0, -27, "anvil[facing=east]")
    bp.set(-39, F0, -27, "smithing_table")
    bp.set(-39, F0, -29, "grindstone[face=floor,facing=east]")
    bp.chest(-39, F0, -34, "east", loot=LOOT + "glacier_armory")
    bp.chest(-39, F0, -36, "east", loot=LOOT + "glacier_armory")
    for z in range(-27, -38, -2):
        bp.set(-40, F0 + 2, z, "spruce_trapdoor[facing=east,half=top,open=true,powered=false,waterlogged=false]")
    for x in range(-34, -27, 3):
        warrior(bp, x, F0 - 1, -37, "north", seed=x)
    bp.spawner(-31, F0, -30, MOB_KNIGHT)
    hang(bp, -32, -32, F0 + 4, F0 + 7)


def kitchen(bp):
    room_floor(bp, 25, 40, -26, -38, F0 - 1, lambda x, z: "stone_bricks" if (x + z) % 3 else "cobblestone")
    room_floor(bp, 24, 24, -31, -33, F0 - 1, "stone_bricks")
    beams(bp, 25, 40, -26, -38, F0 + 7, axis="z", every=5)
    for z in (-27, -28, -29):
        bp.set(40, F0, z, "smoker[facing=west,lit=false]")
    bp.set(40, F0, -30, "furnace[facing=west,lit=false]")
    bp.set(40, F0, -31, "water_cauldron[level=3]")
    for z in range(-34, -38, -1):
        bp.barrel(40, F0, z, "west")
    long_table(bp, 32, -29, -36, F0)
    bp.chest(26, F0, -38, "north", loot=LOOT + "glacier_hall")
    bp.set(28, F0, -38, "crafting_table")
    for z in (-28, -35):
        hang(bp, 36, z, F0 + 4, F0 + 7)
        hang(bp, 28, z, F0 + 4, F0 + 7)


def skald_library(bp):
    room_floor(bp, -41, -52, -54, -70, F0 - 1, plank_floor)
    beams(bp, -41, -52, -54, -70, F0 + 7, axis="x", every=4)
    for z in range(-56, -70, -1):
        for yy in range(F0, F0 + 4):
            bp.set(-52, yy, z, "bookshelf")
    for x in range(-50, -42):
        for yy in range(F0, F0 + 3):
            bp.set(x, yy, -70, "bookshelf")
    bp.set(-46, F0, -62, "lectern[facing=east,has_book=false,powered=false]")
    long_table(bp, -47, -57, -59, F0, benches=False)
    long_table(bp, -47, -65, -67, F0, benches=False)
    candles(bp, -47, F0 + 1, -58, 3)
    candles(bp, -47, F0 + 1, -66, 2)
    bp.chest(-51, F0, -62, "east", loot=LOOT + "glacier_skald")
    for z in (-57, -67):
        hang(bp, -44, z, F0 + 4, F0 + 7)
    hang(bp, -49, -62, F0 + 4, F0 + 7)


def frozen_warriors(bp):
    """The hall of the frozen warriors: two rows of six guards along a causeway of blue ice, a knight spawner, the
    reliquary chests at the far end."""
    room_floor(bp, -25, -46, -76, -104, F0 - 1,
               lambda x, z: BI if x in (-35, -36) else ("polished_andesite" if (x + z) % 2 else "stone_bricks"))
    room_floor(bp, -24, -24, -81, -83, F0 - 1, "polished_andesite")
    for i, z in enumerate(range(-80, -102, -4)):
        warrior(bp, -32, F0 - 1, z, "west", seed=i)
        warrior(bp, -39, F0 - 1, z, "east", seed=i + 7)
    for x in range(-44, -26, 6):
        for z in (-76, -104):
            wall_lamp(bp, x, F0 + 3, z)
    for z in range(-82, -100, -6):
        hang(bp, -36, z, F0 + 5, F0 + 9)
    bp.spawner(-36, F0, -90, MOB_KNIGHT)
    bp.chest(-36, F0, -103, "south", loot=LOOT + "glacier_crypt")
    bp.chest(-44, F0, -103, "south", loot=LOOT + "glacier_crypt")


def sleeping_hall(bp):
    room_floor(bp, 25, 48, -76, -100, F0 - 1, plank_floor)
    room_floor(bp, 24, 24, -86, -88, F0 - 1, SP)
    beams(bp, 25, 48, -76, -100, F0 + 7, axis="z", every=4)
    for i, x in enumerate(range(27, 46, 3)):
        for z, fac in ((-77, "south"), (-99, "north")):
            bp.bed(x, F0, z, fac, color=("blue", "light_gray", "cyan")[i % 3])
            bp.barrel(x + 1, F0, z, "up") if i % 2 else None
    long_table(bp, 36, -82, -94, F0)
    bp.chest(47, F0, -90, "west", loot=LOOT + "glacier_armory")
    bp.chest(26, F0, -92, "east", loot=LOOT + "glacier_hall")
    bp.barrel(26, F0, -84, "up")
    for z in (-81, -88, -95):
        hang(bp, 31, z, F0 + 4, F0 + 7)
        hang(bp, 42, z, F0 + 4, F0 + 7)
    # the huscarl stair comes down beside it; an iron door from its landing (button on the landing side)
    build_stair_cells(bp, STAIRS["huscarl"][0], "spruce_stairs", SP)
    room_floor(bp, 19, 26, -102, -104, F1 - 1, SP)
    room_floor(bp, 43, 48, -102, -104, F0 - 1, SP)
    bp.door(47, F0, -101, "north", wood="iron_door")
    bp.set(48, F0, -103, "stone_button[face=floor,facing=north,powered=false]")
    hang(bp, 45, -103, F0 + 3, F0 + 5)
    niche_lamp(bp, 33, F0 + 7, -105)
    niche_lamp(bp, 26, F1 + 1, -105)
    # the river stair's iron door: its lever is on the stair side only
    bp.door(49, F0, -80, "west", wood="iron_door")


# ------------------------------------------------------------------ the north: bridge, horn, arena, vault
def ambulatory_north(bp):
    zs, zn = bridge_span()
    for z in range(zs, -130):
        for x in range(-1, 2):
            bp.set(x, F1 - 1, z, PDI if x == 0 else "polished_andesite")
    niche_lamp(bp, -2, F1 + 1, -133)
    niche_lamp(bp, 2, F1 + 1, -133)


def bridge(bp):
    """The crevasse bridge: a stone arch 5 wide with walls for rails, lamps on the abutments, a gap in the east
    rail at mid-span (the drop into the lake)."""
    zs, zn = bridge_span()
    mid = (zs + zn) / 2.0
    half = (zs - zn) / 2.0 + 1
    for z in range(zn - 1, zs + 2):
        t = abs(z - mid) / half
        depth = int(1 + 5 * t * t)
        for x in range(-2, 3):
            bp.set(x, F1 - 1, z, "polished_andesite" if abs(x) <= 1 else "stone_bricks")
            for yy in range(F1 - 1 - depth, F1 - 1):
                if bp.get(x, yy, z) in (None, "minecraft:air"):
                    bp.set(x, yy, z, "stone_bricks" if abs(x) == 2 or yy == F1 - 1 - depth else "stone")
            if abs(x) <= 1:
                for yy in range(F1, F1 + 4):
                    bp.set(x, yy, z, "air")
        if zn < z < zs:
            for x in (-2, 2):
                gap = x == 2 and abs(z - mid) <= 0.6
                bp.set(x, F1, z, "air" if gap else "stone_brick_wall")
    bp.set(3, F1 - 1, int(round(mid)), "stone_brick_slab[type=top,waterlogged=false]")
    for (x, z) in ((-2, zs), (2, zs), (-2, zn), (2, zn)):
        bp.set(x, F1, z, "stone_bricks")
        bp.set(x, F1 + 1, z, LANT)


def horn_gate(bp):
    zs, zn = bridge_span()
    room_floor(bp, -7, 7, zn, -155, F1 - 1, lambda x, z: PDI if abs(x) <= 1 else "polished_andesite")
    for x in (-6, 6):
        brazier(bp, x, F1, -151)
    for x in (-7, 7):
        for z in (-148, -154):
            warrior(bp, x, F1 - 1, z, "east" if x < 0 else "west", seed=z)
    hang(bp, 0, -151, F1 + 5, F1 + 8)


def jarl_stair(bp):
    cells, side, f = STAIRS["jarl"]
    build_stair_cells(bp, cells, "stone_brick_stairs", "polished_andesite")
    feet = {(x, z): ff for (x, z, ff, st) in cells}
    xe, xw = JARL_X
    for x in range(xe - 4, xw, -8):                                 # lanterns in niches along both runs
        for z, inner in ((JARL_LANES[0][0] + 1, JARL_LANES[0][0]), (JARL_LANES[1][1] - 1, JARL_LANES[1][1])):
            ff = feet.get((x, inner))
            if ff is not None:
                bp.set(x, ff + 1, z, LANT)
    for z in (JARL_LANES[1][1], JARL_LANES[0][0]):
        bp.set(xw - 4, feet[(xw - 4, z)], z, LANT)
    bp.spawner(xw - 3, feet[(xw - 3, -161)], -161, MOB_STRAY)


def grace(bp):
    room_floor(bp, -6, 6, -169, -176, FG - 1, lambda x, z: CAL if abs(x) <= 1 and abs(z + 172) <= 1 else
               "polished_andesite")
    room_floor(bp, 7, 14, -171, -173, FG - 1, "polished_andesite")
    bp.set(-3, FG, -174, MOD["waystone"])
    brazier(bp, -5, FG, -176)
    brazier(bp, 5, FG, -176)
    hang(bp, 0, -172, FG + 3, FG + 6)
    for x in (9, 12):
        niche_lamp(bp, x, FG + 1, -174)


def arena(bp):
    """The jarl's hall in the horn: a round floor 33 across with rune rings, eight engaged ice pillars, a dome on
    chains of lanterns, the oculus; mist on the narrow way in and on the north door."""
    cx, cz = HC
    for x in range(cx - ARENA_R - 1, cx + ARENA_R + 2):
        for z in range(cz - ARENA_R - 1, cz + ARENA_R + 2):
            d = math.hypot(x - cx, z - cz)
            if d <= ARENA_R + 0.4:
                if 11.5 < d <= 12.5 or d <= 1.5:
                    spec = BI
                elif 5.5 < d <= 6.3:
                    spec = CAL
                else:
                    spec = "polished_andesite" if hash01(x, z, 41) < 0.6 else "stone_bricks"
                bp.set(x, FG - 1, z, spec)
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        px, pz = round(cx + 15.6 * math.cos(a)), round(cz + 15.6 * math.sin(a))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if math.hypot(px + dx - cx, pz + dz - cz) >= 15.2:
                    for yy in range(FG, ARENA_WALL + 2):
                        bp.set(px + dx, yy, pz + dz, BI if yy > FG else CAL)
        lx, lz = round(cx + 9.5 * math.cos(a)), round(cz + 9.5 * math.sin(a))
        hang(bp, lx, lz, FG + 9, dome_top(math.hypot(lx - cx, lz - cz)) + 1)
    for z in range(cz - 2, cz + 3):
        bp.set(cx + 13, FG, z, PDI)
        bp.set(cx + 14, FG, z, PDI)
        for yy in range(FG + 1, FG + 6):
            bp.set(cx + 15, yy, z, BI if abs(z - cz) == 2 or yy == FG + 5 else DO)
    bp.set(cx + 14, FG + 1, cz, stair("dark_oak_stairs", "west"))
    bp.boss_seal(cx, FG - 1, cz, BOSS, 15)
    bp.mist(14, FG, -173, 14, FG + 4, -171)
    bp.mist(29, FG, cz - ARENA_R - 1, 31, FG + 3, cz - ARENA_R - 1)


def vault(bp):
    x0, x1, z0, z1 = VAULT_BOX
    room_floor(bp, x0, x1, z0, z1, FG - 1, lambda x, z: "polished_andesite" if (x + z) % 2 else CAL)
    room_floor(bp, 29, 31, HC[1] - ARENA_R - 1, z0 + 1, FG - 1, "polished_andesite")
    for x in range(LEAP[0], LEAP[1] + 1):
        for z in range(LEAP[3], LEAP[2] + 1):
            bp.set(x, FG - 1, z, "air")
    for z in range(LEAP[3] - 1, LEAP[2] + 2):
        if z != (LEAP[2] + LEAP[3]) // 2:
            bp.set(LEAP[1] + 1, FG, z, "spruce_fence")
    for x in range(LEAP[0], LEAP[1] + 1):
        bp.set(x, FG, LEAP[2] + 1, "spruce_fence")
    bp.chest(34, FG, -199, "west", loot=LOOT + "glacier_vault")
    bp.chest(34, FG, -195, "west", loot=LOOT + "glacier_vault")
    bp.set(30, FG, -200, "gold_block")
    candles(bp, 30, FG + 1, -200, 4)
    for x in (28, 32):
        brazier(bp, x, FG, -200)
    hang(bp, 30, -195, FG + 3, FG + 6)


def river(bp):
    """Water 3 deep, the bank (ice, gravel, stones), lamps on the bank, the spring pool under the leap, the lake in
    the crevasse, the pool on the plain."""
    for (x, z), kind in RIVER_CELLS.items():
        if kind == "water":
            for yy in range(-2, 1):
                bp.set(x, yy, z, "water")
            bp.set(x, -3, z, "gravel")
        else:
            h = hash01(x, z, 51)
            bp.set(x, 0, z, "gravel" if h < 0.25 else ("cobblestone" if h < 0.45 else (PI if h < 0.85 else
                                                                                    "andesite")))
            bp.set(x, -1, z, "stone")
    # the spring pool under the leap shaft
    for x in range(LEAP[0] - 2, LEAP[1] + 3):
        for z in range(LEAP[3] - 2, LEAP[2] + 3):
            deep = LEAP[0] <= x <= LEAP[1] and LEAP[3] <= z <= LEAP[2]
            for yy in range(-4 if deep else -2, 1):
                bp.set(x, yy, z, "water")
            bp.set(x, -5 if deep else -3, z, "gravel")
    # the lake in the crevasse (catches the drop from the bridge)
    for x in range(-5, 24):
        zc = crevasse_z(x)
        for z in range(int(zc) - 5, int(zc) + 5):
            if abs(z - zc) <= 3.5:
                for yy in range(-3, 1):
                    bp.set(x, yy, z, "water")
                bp.set(x, -4, z, "gravel")
                for yy in range(1, 4):
                    bp.set(x, yy, z, "air")
    # soul lanterns on the bank every so often (the way back is a dark place)
    n = 0
    for (x, z), kind in sorted(RIVER_CELLS.items(), key=lambda t: (t[0][1], t[0][0])):
        if kind == "bank" and z < PORTAL_Z - 2 and river_dist(x, z)[0] < -4.5:
            if n % 41 == 0:
                lamp_post(bp, x, 1, z, soul=True)
            n += 1
    # the pool on the outwash plain where the river ends (closed, so the water stays put)
    for x in range(45, 58):
        for z in range(28, 41):
            if math.hypot(x - 51, z - 34) <= 5.5:
                for yy in range(-2, 1):
                    bp.set(x, yy, z, "water")
                bp.set(x, -3, z, "gravel")
                bp.set(x, 1, z, "air")


def drowned_hoard(bp):
    """A cave off the river under the crossing: a pool, stepping stones of packed ice (jumps), the hoard on a
    ledge at the far end, a drowned spawner in the water."""
    for x in range(36, 47):
        for z in range(-66, -57):
            for yy in range(-2, 1):
                bp.set(x, yy, z, "water")
            bp.set(x, -3, z, "gravel")
    for (x, z) in ((37, -62), (39, -61), (41, -63), (43, -62)):
        for yy in range(-2, 1):
            bp.set(x, yy, z, PI)
    for x in (45, 46):
        for z in range(-64, -59):
            for yy in range(-2, 1):
                bp.set(x, yy, z, PI)
    bp.chest(46, 1, -62, "west", loot=LOOT + "glacier_hoard")
    bp.set(46, 1, -60, "gold_block")
    bp.spawner(40, -1, -65, MOB_DROWNED)
    bp.set(45, 1, -64, SOUL)


def river_stair(bp):
    build_stair_cells(bp, STAIRS["river"][0], "cobblestone_stairs", "cobblestone")
    room_floor(bp, 35, 49, -79, -81, FR - 1, lambda x, z: "cobblestone" if (x + z) % 3 else PI)
    bp.set(50, F0 + 1, -81, "lever[face=wall,facing=east,powered=false]")
    niche_lamp(bp, 57, FR + 1, -80)
    niche_lamp(bp, 57, FR + 9, -92)
    niche_lamp(bp, 57, F0 + 1, -80)


def balcony(bp):
    bx = balcony_x()
    room_floor(bp, 47, bx, -61, -63, F0 - 1, lambda x, z: PI if (x + z) % 3 else "polished_andesite")
    for x in range(bx + 1, bx + 5):
        for z in range(-64, -59):
            bp.set(x, F0 - 1, z, SP)
            bp.set(x, F0 - 2, z, TOP_SLAB)
            if x == bx + 4 or z in (-60, -64):
                bp.set(x, F0, z, "spruce_fence")
    for z in (-60, -64):
        for k in range(1, 4):
            bp.set(bx + k, F0 - 2 - k, z, "spruce_log[axis=y]")
            bp.set(bx + k, F0 - 1 - k, z, "spruce_log[axis=y]")
    bp.chest(bx + 1, F0, -63, "north", loot=LOOT + "glacier_skald")
    lamp_post(bp, bx + 1, F0, -61)
    for x in range(52, bx + 1, 8):
        hang(bp, x, -62, F0 + 2, F0 + 5)


# ------------------------------------------------------------------ the roof, the loft, the crest
def roof(bp):
    """The longhouse roof breaking the ice crest: slate on dark oak, rafters, gables with crossed bargeboards and
    dragon heads, smoke louvres every 14 blocks along the ridge."""
    z0, z1 = ROOF_Z
    for z in range(z1, z0 + 1):
        for x in range(-8, 9):
            ax = abs(x)
            if ax == 0:
                bp.set(x, LOFT_Y + 7, z, ROOF_SL + "[type=bottom,waterlogged=false]")
                bp.set(x, LOFT_Y + 6, z, "dark_oak_log[axis=z]")
            else:
                bp.set(x, LOFT_Y + 7 - ax if ax <= 7 else LOFT_Y - 1, z, stair(ROOF_ST, "east" if x < 0 else "west"))
        if z % 4 == 0:
            for x in range(-5, 6):
                if abs(x) >= 4:
                    bp.set(x, LOFT_Y + 6 - abs(x), z, stair("dark_oak_stairs", "west" if x < 0 else "east", "top"))
    for z, out in ((z0, 1), (z1, -1)):
        for x in range(-6, 7):
            for yy in range(LOFT_Y, LOFT_Y + 7 - abs(x)):
                bp.set(x, yy, z, SP if (x + yy) % 3 else "dark_oak_log[axis=y]")
        for s in (-1, 1):
            for k in range(0, 4):
                bp.set(s * k, LOFT_Y + 7 + k, z, "dark_oak_log[axis=y]")
            bp.set(s * 4, LOFT_Y + 11, z, f"dragon_head[rotation={0 if out > 0 else 8}]")
            bp.set(s * 4, LOFT_Y + 10, z, "dark_oak_log[axis=y]")
    for (x, yy) in ((-1, 62), (0, 62), (1, 62), (-1, 63), (1, 63), (-1, 64), (0, 64), (1, 64)):
        bp.set(x, yy, z0, "glass_pane")
    bp.set(0, 63, z0, "glass")
    for x in range(-1, 2):
        for yy in range(LOFT_Y + 1, LOFT_Y + 4):
            bp.set(x, yy, z1, SP)
    bp.door(0, LOFT_Y + 1, z1, "north", wood="spruce")
    for z in range(z0 - 14, z1 + 7, -14):
        for x in range(-1, 2):
            for dz in (-1, 0, 1):
                for yy in range(LOFT_Y + 7, LOFT_Y + 10):
                    if abs(x) == 1 or abs(dz) == 1:
                        bp.set(x, yy, z + dz, "spruce_fence" if (x + dz) % 2 else "dark_oak_log[axis=y]")
                    else:
                        bp.set(x, yy, z + dz, "air")
        for x in range(-2, 3):
            for dz in range(-2, 3):
                if max(abs(x), abs(dz)) == 2:
                    f = (("east" if x < 0 else "west") if abs(x) >= abs(dz) else ("south" if dz < 0 else "north"))
                    bp.set(x, LOFT_Y + 10, z + dz, stair(ROOF_ST, f))
                else:
                    bp.set(x, LOFT_Y + 10, z + dz, ROOF)
        bp.set(0, LOFT_Y + 11, z, ROOF_SL + "[type=bottom,waterlogged=false]")


def loft(bp):
    z0, z1 = ROOF_Z
    for z in range(z1 + 1, z0):
        for x in range(-6, 7):
            bp.set(x, LOFT_Y, z, SP if z % 5 else SPL + "[axis=x]")
    for z in range(z0 - 6, z1 + 4, -9):
        for x in (-4, 4):
            bp.bed(x, LOFT_Y + 1, z, "south", color="brown")
        hang(bp, 0, z - 4, LOFT_Y + 4, LOFT_Y + 6)
    bp.chest(-3, LOFT_Y + 1, z1 + 2, "south", loot=LOOT + "glacier_skald")
    bp.barrel(3, LOFT_Y + 1, z1 + 2, "up")
    bp.spawner(0, LOFT_Y + 1, -70, MOB_KNIGHT)
    # the dormer door on the east side at z -62 (from the crest)
    for z in (-61, -62, -63):
        for x in (5, 6, 7):
            for yy in range(LOFT_Y + 1, LOFT_Y + 4):
                bp.set(x, yy, z, "air")
        for x in (5, 6, 7, 8):
            bp.set(x, LOFT_Y, z, SP)
    for yy in range(LOFT_Y + 1, LOFT_Y + 4):
        for z in (-60, -64):
            for x in (5, 6, 7, 8):
                bp.set(x, yy, z, SP)
    for z in range(-60, -65, -1):
        for x in (5, 6, 7, 8):
            bp.set(x, LOFT_Y + 4, z, stair(ROOF_ST, "west") if x == 8 else ROOF)
    for yy in (LOFT_Y + 1, LOFT_Y + 2, LOFT_Y + 3):
        for z in (-61, -63):
            bp.set(8, yy, z, SP)
    bp.set(8, LOFT_Y + 3, -62, SP)
    bp.door(8, LOFT_Y + 1, -62, "east", wood="spruce")
    # the north terrace on the crest (vista over the crevasse and the horn)
    for x in range(-4, 5):
        for z in range(z1 - 1, z1 - 7, -1):
            bp.set(x, LOFT_Y, z, SP if abs(x) < 4 and z > z1 - 6 else "stone_bricks")
            for yy in range(LOFT_Y + 1, LOFT_Y + 4):
                bp.set(x, yy, z, "air")
            if abs(x) == 4 or z == z1 - 6:
                bp.set(x, LOFT_Y + 1, z, "spruce_fence")
    lamp_post(bp, -3, LOFT_Y + 1, z1 - 5)


def crest_path(bp):
    """The loft stair comes out in a turf hut on the crest; a trodden path of stone steps leads to the dormer."""
    cells, side, f = STAIRS["loft"]
    # the hut stands on a plank floor over a snow footing (the crest falls away east of the stair)
    for x in range(22, 39):
        for z in range(-56, -68, -1):
            if bp.get(x, f - 1, z) != "minecraft:air":
                bp.set(x, f - 1, z, SP if 22 < x < 38 and -67 < z < -56 else "stone_bricks")
            for yy in range(f - 2, f - 12, -1):
                b = bp.get(x, yy, z)
                if b is not None and b != "minecraft:air":
                    break
                if b == "minecraft:air" and (x, z) in {(c[0], c[1]) for c in cells}:
                    break
                bp.set(x, yy, z, SNOW)
            if 22 < x < 38 and -67 < z < -56:
                for yy in range(f, f + 4):
                    bp.set(x, yy, z, "air")
    for x in range(22, 39):
        for z in range(-56, -68, -1):
            edge = x in (22, 38) or z in (-56, -67)
            if edge:
                for yy in range(f, f + 4):
                    bp.set(x, yy, z, "spruce_log[axis=y]" if x in (22, 38) and z in (-56, -67) else SP)
                bp.set(x, f + 4, z, stair(ROOF_ST, "north" if z == -67 else "south" if z == -56 else
                                          "east" if x == 22 else "west"))
            else:
                bp.set(x, f + 4, z, ROOF)
    for z in range(-61, -64, -1):
        for yy in range(f, f + 3):
            bp.set(22, yy, z, "air")
    hang(bp, 30, -62, f + 2, f + 4)
    xa, fa = 21, f
    span = float(xa - 9)
    prev = fa
    for x in range(xa, 8, -1):
        ff = int(round(fa + (LOFT_Y + 1 - fa) * (xa - x) / span))
        for z in (-61, -62, -63):
            bp.set(x, ff - 1, z, stair("stone_brick_stairs", "west") if ff > prev else
                   ("stone_bricks" if (x + z) % 2 else "cobblestone"))
            for yy in range(ff - 6, ff - 1):
                if bp.get(x, yy, z) in (None, "minecraft:air"):
                    bp.set(x, yy, z, SNOW)
            for yy in range(ff, ff + 4):
                bp.set(x, yy, z, "air")
        prev = ff


# ------------------------------------------------------------------ the approach
PATH = [(-36, 35), (-20, 34), (-8, 31), (-4, 27), (0, 26)]
BACK_PATH = [(38, 8), (30, 13), (20, 19), (10, 23), (4, 26)]


def path_cells(pts, w=1.6):
    out = set()
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        L = max(1, int(math.hypot(bx - ax, bz - az) * 2))
        for i in range(L + 1):
            t = i / L
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if math.hypot(dx, dz) <= w:
                        out.add((int(round(px + dx)), int(round(pz + dz))))
    return out


def approach(bp, P):
    cells = path_cells(PATH) | path_cells(BACK_PATH)
    for (x, z) in cells:
        if (x, z) in RIVER_CELLS:
            continue
        h = hash01(x, z, 71)
        bp.set(x, 0, z, "cobblestone" if h < 0.35 else ("stone_bricks" if h < 0.55 else
                                                        ("gravel" if h < 0.7 else SNOW)))
        bp.set(x, -1, z, "stone")
        for yy in range(1, 5):
            bp.set(x, yy, z, "air")
    # the footbridge over the river on the way back from the ice cave
    for (x, z), kind in RIVER_CELLS.items():
        if kind == "water" and (x, z) in cells:
            bp.set(x, 1, z, "spruce_slab[type=bottom,waterlogged=false]")
    # the standing stones framing the moraine gap, a lintel on top (the first framed view of the gate)
    for sx in (-14, -2):
        for yy in range(0, 8):
            for zz in (31, 32):
                bp.set(sx, yy, zz, "stone" if hash01(sx + zz, yy, 3) < 0.6 else "andesite")
        bp.set(sx, 5, 32, "chiseled_stone_bricks")
    for x in range(-15, 0):
        for zz in (31, 32):
            bp.set(x, 8, zz, "stone_bricks" if -13 <= x <= -3 else "stone_brick_slab[type=bottom,waterlogged=false]")
    # the jarls' camp at the marker: a lean-to, a fire ring, a chest, the cairn and its lantern
    mx, mz = -36, 35
    for yy in range(0, 5):
        bp.set(mx - 3, yy, mz + 1, "cobblestone" if yy < 3 else "stone")
    bp.set(mx - 3, 5, mz + 1, LANT)
    for x in range(mx + 1, mx + 6):
        for z in range(mz - 6, mz - 2):
            bp.set(x, 0, z, SP)
        for yy in range(1, 4):
            bp.set(x, yy, mz - 6, SP)
        bp.set(x, 4, mz - 6, stair("spruce_stairs", "south"))
        bp.set(x, 4, mz - 5, stair("spruce_stairs", "south"))
        bp.set(x, 3, mz - 4, stair("spruce_stairs", "south", "top"))
        bp.set(x, 4, mz - 4, "spruce_slab[type=bottom,waterlogged=false]")
    for x in (mx + 1, mx + 5):
        for yy in range(1, 3):
            bp.set(x, yy, mz - 4, "spruce_fence")
    bp.bed(mx + 2, 1, mz - 5, "east", color="brown")
    bp.chest(mx + 5, 1, mz - 5, "west", loot=LOOT + "glacier_camp")
    bp.barrel(mx + 4, 1, mz - 5, "up")
    for (x, z) in ((mx, mz - 1), (mx - 1, mz - 2), (mx + 1, mz - 2), (mx, mz - 3), (mx, mz - 2)):
        bp.set(x, 0, z, "cobblestone")
    bp.set(mx, 1, mz - 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # trees and boulders on the plain (off the paths, the river and the moraine)
    busy = set()
    for (x, z) in cells:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                busy.add((x + dx, z + dz))
    placed = []
    for i in range(80):
        x = int(-78 + 156 * hash01(i, 1, 81))
        z = int(4 + 31 * hash01(i, 2, 81))
        if (x, z) in busy or (x, z) in RIVER_CELLS or abs(x) < 28 and z < 27 or math.hypot(x - 51, z - 34) < 8:
            continue
        if any(abs(x - a) < 6 and abs(z - b) < 6 for a, b in placed) or abs(x - mx) < 8 and abs(z - mz) < 8:
            continue
        i0, k0 = x - X0, z - Z0
        if INSIDE[i0, k0] or P.S[i0, 1, k0] or not (X0 + 3 < x < X1 - 3 and z < Z1 - 3):
            continue
        h = hash01(i, 3, 81)
        bp.set(x, 0, z, "podzol[snowy=true]" if h < 0.62 else SNOW)
        if h < 0.62:
            spruce(bp, x, 1, z, h=7 + int(h * 10), seed=i)
        else:
            boulder(bp, x, 1, z, r=2, blocks=("stone", "andesite", "cobblestone", "tuff"), seed=i)
        placed.append((x, z))


# ------------------------------------------------------------------ builder
def glacier_hall(bp):
    P = Plan()
    P.glacier()
    carve_all(P)
    P.cover()
    write_massif(bp, P)
    gate_face(bp)
    terrace(bp)
    grand_stair(bp)
    statue(bp, -15)
    statue(bp, 15)
    nave(bp)
    aisles(bp)
    galleries(bp)
    crossing(bp)
    transepts(bp)
    apse(bp)
    guard_room(bp)
    mead_store(bp)
    armoury(bp)
    kitchen(bp)
    skald_library(bp)
    frozen_warriors(bp)
    sleeping_hall(bp)
    ambulatory_north(bp)
    bridge(bp)
    horn_gate(bp)
    jarl_stair(bp)
    grace(bp)
    arena(bp)
    vault(bp)
    river(bp)
    drowned_hoard(bp)
    river_stair(bp)
    balcony(bp)
    roof(bp)
    loft(bp)
    crest_path(bp)
    approach(bp, P)
    seal_voids(bp, P)
    own_foundations(bp, P)


def seal_voids(bp, P):
    """Air set by the details outside the planned carve (doors, niches, the hut, the paths) can open the unset
    core of the masses: give every such air cell a solid skin where its neighbours are unset inside the plan."""
    nx, ny, nz = P.S.shape
    fill = {ICE: PI, ROCK: "stone", MORAINE: "cobblestone", MASON: "stone"}
    air = [k for k, v in bp.blocks.items() if v[0] == "minecraft:air"]
    for (x, y, z) in air:
        i, k = x - X0, z - Z0
        if 0 <= i < nx and 0 <= y < ny and 0 <= k < nz and P.K[i, y, k]:
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            qx, qy, qz = x + dx, y + dy, z + dz
            qi, qk = qx - X0, qz - Z0
            if not (0 <= qi < nx and 1 <= qy < ny and 0 <= qk < nz) or not P.S[qi, qy, qk] or P.K[qi, qy, qk]:
                continue
            if (qx, qy, qz) not in bp.blocks:
                bp.set(qx, qy, qz, fill.get(int(P.MAT[qi, qy, qk]), "stone"))


def own_foundations(bp, P, depth=5):
    """The structure carries its own foundations (foundation=False: the pipeline's would also wrap the inner edge
    of the rim ring): every ground-layer column outside the core of the masses goes down ``depth`` blocks, earth
    first and stone below, stopping on anything built."""
    cols = [(x, z, v[0]) for (x, y, z), v in bp.blocks.items() if y == 0 and v[0] != "minecraft:air"]
    for x, z, name in cols:
        i, k = x - X0, z - Z0
        if 0 <= i < len(XS) and 0 <= k < len(ZS) and P.CORE[i, k]:
            continue
        short = name.split(":")[1]
        top = "dirt" if short in ("snow_block", "podzol", "dirt", "grass_block", "gravel") else "stone"
        for d in range(1, depth + 1):
            if bp.get(x, -d, z) is not None:
                break
            bp.set(x, -d, z, top if d <= 2 else "stone")

VIEWS = [
    ("gate", (-8, 1, 36), (0, 34, 0)),
    ("nave", (0, F0, -15), (0, F0 + 14, -100)),
    ("gallery", (-15, F1, -36), (8, F1 + 4, -60)),
    ("apse", (0, F1, -128), (0, F0 + 6, -50)),
    ("crevasse_bridge", (0, F1, bridge_span()[0] + 1), (-30, F1 + 12, -140)),
    ("arena", (16, FG, -172), (42, FG + 6, -172)),
    ("meltwater", (33, FR, -110), (30, FR + 2, -80)),
]


register(StructureDef(
    "glacier_hall", "overworld",
    ["snowy_plains", "ice_spikes", "snowy_taiga", "grove", "snowy_slopes"],
    [Piece("hall", glacier_hall, views=VIEWS)],
    spacing=80, separation=32, adaptation="beard_thin", processors="none", max_distance=128, foundation=False,
    spawns=[("minecraft:stray", 10, 1, 2), ("brasshaven:skeleton_knight", 4, 1, 1)],
    title_fr="Halle glaciaire des jarls", title_en="Glacier Hall of the Frost Jarls"))
