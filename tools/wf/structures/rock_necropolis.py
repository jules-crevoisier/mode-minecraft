"""Rock-cut Necropolis (Nécropole des rois / Necropolis of Kings): a Petra / Abu Simbel monument carved into an
artificial canyon massif. Colossal tier (tools/BUILDING.md §1, §12 concept 6, §15), desert and badlands.

Silhouette: a rose-red sandstone massif 170 across with beehive domes up to y ~100, a sheer cliff on its south
side cut by a 60-block slot canyon; behind the canyon a hidden plaza, and on the plaza's north wall the façade of
the kings: four seated colossi 42 high flanking a portal 18 high, a gorge cornice with a frieze of baboons, and above
it a Petra-style upper storey (round tholos between two broken half-pediments) up to y 88.

Layout, ground y = 0 (plaza feet y 1), façade plane z = FZ facing south (+z):
  * approach: the caravan camp, a waystone and two djinn blocks at the canyon mouth (z ~ 80); the slot canyon
    (4-6 wide, walls 30-60 high, a chockstone and a rock arch overhead) winds north to the plaza: compression ->
    release, with the façade revealed slice by slice at the canyon's last bend;
  * the plaza (90 x 40): the terrace of the kings, the fallen head of the broken second king, a side tomb carved
    in the west cliff (tier 1, optional), a waystone (hub);
  * L0 (feet 3): the portal with its wicket, the hypostyle hall (31 x 43, 24 high, eight Osirid pillars, a grate
    in the floor looking down into the boss arena), the sanctuary of the four gods at the end of the axis; east,
    a switchback stair up to the Gallery of Crowns behind the kings' heads (windows and a balcony over the plaza);
  * L1 (feet -9): the antechamber of Anubis, the embalming hall (husk spawner, tier 1), the gallery of niches;
  * L2 (feet -21): the flooded gallery (collapsed ceiling, a causeway between pools, crypt crawlers), the trap
    corridor (visible pressure plates, dart dispensers), the treasury (tier 2, spawner) and its secret hoard
    behind an iron door opened by a button hidden among the glyphs;
  * L3 (feet -37): the site of grace, a narrow corridor and the mist, the boss arena (r 16, 18 high, a dais
    with two seated colossi and jackal statues), past the south mist the reward vault behind sealed bars (tier 3)
    and the King's Well: a spiral stair back up to the vestibule, opening one way (lever on the well side).
Loot gradient (§15.6): camp / side tomb / galleries tier 1, embalming tier 1-2, treasury tier 2, vault tier 3.

The massif is a hollow shell (BUILDING §1): rock 2 thick under every outer face, room walls wrapped around every
carved space; the deep core stays unset (in game it keeps whatever terrain was there).
"""
import math
import random

import numpy as np

from .. import nbt
from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3
from ..parts import LOOT, MOD
from .walking_fortress import light_fill

# the necropolis' own king: the Fourth King, the seated king whose face was chiselled off the façade, risen
BOSS = "brasshaven:fourth_king"
MOB_CRAWLER = "brasshaven:crypt_crawler"
DUNE_KING = "brasshaven:dune_king"   # the hall's guardian (his old home, the Mesa Mine-City, has the Mine Baron)

# ------------------------------------------------------------------ dimensions
MX0, MX1 = -88, 88          # massif array (x)
MZ0, MZ1 = -98, 74          # (z)
TOP = 112                   # array height (y 0..TOP-1)
FZ = -6                     # façade plane: solid at z <= FZ in front of the hall
FACADE_W = 44               # lower storey half width
UPPER_W = 30                # upper storey half width
CORNICE = 50                # top of the lower storey (gorge cornice)
FACADE_TOP = 88
SHELL = 2                   # rock thickness under every outer face

F0 = 3                      # feet on the terrace, in the hall and the gallery of crowns' stair foot
F1 = -9                     # L1 feet
F2 = -21                    # L2 feet
F3 = -37                    # L3 feet
FC = 39                     # gallery of crowns feet
KING_Y = 3                  # first block of a king (on the terrace)
KINGS = (-34, -15, 15, 34)  # king centres (x); the second one from the west is broken
BROKEN = -15

HALL = (-15, -58, 15, -16)  # interior x0, z0, x1, z1 of the hypostyle hall
HALL_TOP = 26               # last air layer of the hall
ARENA = (0, -34)
ARENA_R = 16
ARENA_TOP = F3 + 17         # last air layer of the arena
WELL = (-22, -20)           # the King's Well (shortcut spiral) centre

# canyon centreline (x, z), from the plaza to beyond the south edge
CANYON = [(9, 30), (6, 40), (-5, 47), (-12, 56), (-6, 64), (6, 70), (10, 78), (10, 96)]

# ------------------------------------------------------------------ materials
ROCK_LADDER = ("white_terracotta", "pink_terracotta", "red_sandstone", "orange_terracotta", "terracotta",
               "red_terracotta", "brown_terracotta")          # light -> dark
# strata sequence (ladder indices), repeated upwards with jittered boundaries
STRATA = (2, 3, 2, 1, 3, 4, 3, 2, 2, 1, 0, 1, 3, 4, 5, 4, 3, 2, 1, 2, 3, 3, 4, 3, 2, 1, 1, 2)
DRESS = ("smooth_red_sandstone", "cut_red_sandstone", "red_sandstone")
RS, CRS, SRS, CHRS = "red_sandstone", "cut_red_sandstone", "smooth_red_sandstone", "chiseled_red_sandstone"
SS, CSS, SMS, CHSS = "sandstone", "cut_sandstone", "smooth_sandstone", "chiseled_sandstone"
GOLD, LAPIS = "gold_block", "lapis_block"
GLYPHS = ("orange_glazed_terracotta", "blue_glazed_terracotta", "light_blue_glazed_terracotta",
          "yellow_glazed_terracotta")
STAR = "ochre_froglight[axis=y]"
AIR = "air"


# ------------------------------------------------------------------ vector noise (numpy, for the massif)
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
    """Scalar value noise in 0..1."""
    return float(vnoise(np.array([x]), np.array([z]), scale, seed)[0])


# ------------------------------------------------------------------ the massif: 2D fields
XS = np.arange(MX0, MX1 + 1)
ZS = np.arange(MZ0, MZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")          # [ix, iz]


def _domes():
    rng = random.Random(7)
    out = [(0, -30, 10, 20), (-34, -40, 14, 15), (36, -44, 16, 16), (-62, -10, 13, 14), (60, -6, 12, 14),
           (-20, -78, 12, 15), (28, -80, 14, 14), (-56, -60, 10, 14), (62, -60, 12, 13), (-40, 54, 12, 13),
           (40, 50, 14, 12), (-28, 30, 9, 10), (30, 26, 8, 10), (0, 64, 6, 10)]
    for _ in range(8):
        out.append((rng.randint(-70, 70), rng.randint(-90, 60), rng.randint(5, 9), rng.randint(7, 10)))
    return out


DOMES = _domes()


def _fields():
    x, z = GX.astype(float), GZ.astype(float)
    # outline: a superellipse around (0, -12) with a noisy edge
    ax, az = 86.0, np.where(z < -12, 84.0, 84.0)
    p = 2.6
    r = (np.abs(x / ax) ** p + np.abs((z + 12) / az) ** p) ** (1 / p)
    r = r * (1 + 0.16 * (fbm(x, z, 22.0, 3) - 0.5) + 0.22 * (fbm(x, z, 48.0, 4) - 0.5))   # spurs and bays
    # plateau: tall behind the façade, falling to the back, the sides and the canyon side
    s = np.where(z < -40, np.exp(-((z + 40) / 30) ** 2), np.where(z > 0, np.exp(-(z / 30) ** 2), 1.0))
    hp = 40 + 58 * np.exp(-(x / 70) ** 2) * s + 8 * (fbm(x, z, 16.0, 5) - 0.5)
    for (dx, dz, amp, rad) in DOMES:
        d = np.hypot(x - dx, z - dz) / rad
        hp = hp + amp * np.clip(1 - d * d, 0, None) ** 1.5
    # the cliff slab above the façade
    d = np.hypot(x / 56.0, (z + 14) / 19.0)
    crest = 95 + 6 * (fbm(x, z, 9.0, 9) - 0.5) - 0.08 * np.abs(x) - np.clip(d - 0.82, 0, None) * 110
    hp = np.where(z <= FZ + 2, np.maximum(hp, crest), hp)
    # badlands terraces: flat benches with steep risers (raise-only, so no room under the surface gets exposed)
    step = 9.0 + 3.0 * (fbm(x, z, 40.0, 13) - 0.5)
    q = hp / step
    base = np.floor(q)
    hp = np.where(z <= FZ + 2, hp, np.maximum(hp, (base + np.minimum(1.0, (q - base) / 0.3)) * step))
    # the outer slopes climb in three cliff-and-bench steps (sheer risers, flat benches) up to the plateau
    rim = np.clip((1 - r) / 0.24, 0, 1) * 3.0
    tier = np.floor(rim)
    rim = np.minimum(1.0, (tier + np.minimum(1.0, (rim - tier) / 0.18)) / 3.0)
    h = np.where(r < 1, np.minimum(hp, np.maximum(28.0, hp * (0.45 + 0.55 * rim))), 0)
    h = np.minimum(h, TOP - 2)
    return r, h.astype(int)


R2, H2 = _fields()


def _canyon_fields():
    """Signed distance to the canyon centreline and the position along it (blocks from the plaza)."""
    best = np.full(GX.shape, 1e9)
    sd = np.zeros(GX.shape)
    along = np.zeros(GX.shape)
    acc = 0.0
    for (ax_, az_), (bx, bz) in zip(CANYON[:-1], CANYON[1:]):
        vx, vz = bx - ax_, bz - az_
        L = math.hypot(vx, vz)
        t = np.clip(((GX - ax_) * vx + (GZ - az_) * vz) / (L * L), 0, 1)
        cx, cz = ax_ + vx * t, az_ + vz * t
        d = np.hypot(GX - cx, GZ - cz)
        side = np.sign((GX - ax_) * vz - (GZ - az_) * vx)
        m = d < best
        best = np.where(m, d, best)
        sd = np.where(m, d * np.where(side == 0, 1, side), sd)
        along = np.where(m, acc + t * L, along)
        acc += L
    return sd, along


CAN_SD, CAN_A = _canyon_fields()


def canyon_cut(y):
    """2D mask of the canyon at height y: 4-6 wide on the floor, meandering and widening upwards."""
    yy = max(y, 1)
    shift = 1.1 * np.sin(yy / 8.0 + CAN_A / 11.0) * min(1.0, yy / 12.0)
    w = 2.6 + 0.045 * yy + 1.0 * (vnoise(CAN_A * 0.9, np.full(CAN_A.shape, yy * 0.8), 5.0, 31) - 0.5)
    w = w + np.where(CAN_A < 6, (6 - CAN_A) * 0.8, 0)          # flares into the plaza
    return np.abs(CAN_SD - shift) <= w


def plaza_cut(y):
    """2D mask of the plaza at height y: a D-shaped court, flat north side (the façade), cliffs leaning back."""
    x, z = GX.astype(float), GZ.astype(float)
    grow = 1 + 0.0035 * y
    wob = 3.2 * (fbm(x * 0.8 + y * 0.9, z * 0.8 - y * 0.6, 9.0, 41) - 0.5)
    sx, sz = 50 * grow + wob, 23 * grow + wob
    pz = 13.0
    south = (np.abs(x) / sx) ** 2.4 + (np.maximum(z - pz, 0) / sz) ** 2.4 <= 1
    # the north edge: the façade plane, its corners rounded into the side cliffs
    edge = FZ + np.clip(np.abs(x) - FACADE_W, 0, None) * 1.3
    if y > FACADE_TOP:
        edge = edge - (y - FACADE_TOP) * 0.9                    # the crown cliff steps back above the façade
    return south & (z > edge)


# ------------------------------------------------------------------ rock palette
def rock_specs(xs, ys, zs, top_mask):
    """Strata: ladder index from jittered horizontal bands, darker at the base, bleached on exposed tops."""
    jit = 2.2 * (vnoise(xs * 1.0, zs * 1.0, 9.0, 51) - 0.5) + 1.2 * (vnoise(xs + ys * 0.3, zs, 3.0, 52) - 0.5)
    band = np.floor((ys + jit) / 3.4).astype(int) % len(STRATA)
    idx = np.array(STRATA)[band].astype(float)
    idx += np.where(ys < 8, (8 - ys) / 4.0, 0)                                  # dark, rough base
    dmg = vnoise(xs * 1.0 + zs * 0.5, ys * 1.0, 4.0, 53)
    idx += np.where(dmg < 0.12, 1, 0)
    idx -= np.where(top_mask, 1.5, 0)                                          # sun-bleached tops
    idx = np.clip(np.round(idx), 0, len(ROCK_LADDER) - 1).astype(int)
    return idx


def massif(bp):
    nx, nz = len(XS), len(ZS)
    solid = np.zeros((nx, TOP, nz), bool)
    ys = np.arange(TOP)
    inside = R2 < 1
    for y in range(1, TOP):
        col = inside & (H2 >= y) & ~plaza_cut(y) & ~canyon_cut(y)
        solid[:, y, :] = col
    # erosion (6-neighbourhood, SHELL times): below y 1 counts as solid ground, outside the array as air
    er = solid.copy()
    for _ in range(SHELL):
        e = er.copy()
        e[1:, :, :] &= er[:-1, :, :]
        e[:-1, :, :] &= er[1:, :, :]
        e[0, :, :] = False
        e[-1, :, :] = False
        e[:, :, 1:] &= er[:, :, :-1]
        e[:, :, :-1] &= er[:, :, 1:]
        e[:, :, 0] = False
        e[:, :, -1] = False
        e[:, :-1, :] &= er[:, 1:, :]
        e[:, -1, :] = False
        e[:, 2:, :] &= er[:, 1:-1, :]
        er = e
    shell = solid & ~er
    top = np.zeros_like(solid)
    top[:, :-1, :] = solid[:, :-1, :] & ~solid[:, 1:, :]
    pts = np.argwhere(shell)
    xs, yv, zs = XS[pts[:, 0]], pts[:, 1], ZS[pts[:, 2]]
    idx = rock_specs(xs.astype(float), yv.astype(float), zs.astype(float), top[pts[:, 0], pts[:, 1], pts[:, 2]])
    names = ROCK_LADDER
    for (x, y, z, i) in zip(xs.tolist(), yv.tolist(), zs.tolist(), idx.tolist()):
        bp.set(x, y, z, names[i])
    # the base layer under the whole massif (sandy ground theme), one more layer to stop the foundations in the
    # core (the outer rim keeps them: it is where uneven ground shows)
    cut0 = plaza_cut(1) | canyon_cut(1)
    for ix, iz in np.argwhere(inside).tolist():
        x, z = int(XS[ix]), int(ZS[iz])
        if cut0[ix, iz]:
            continue
        bp.set(x, 0, z, RS if hash01(x, z, 61) < 0.65 else SS)
        if R2[ix, iz] < 0.95:
            bp.set(x, -1, z, SS)
    return solid


# ------------------------------------------------------------------ carving: every walkable space, then its walls
class Carver:
    """Collects the carved cells (explicit air, or virtual: left unset, decorative recesses high up), then wraps
    them in two layers of wall wherever the cell is unset and inside the rock (the massif or under the ground)."""

    def __init__(self, bp, solid):
        self.bp = bp
        self.solid = solid
        self.cells = set()

    def box(self, x0, x1, z0, z1, feet, h, floor=None, virtual=False):
        bp = self.bp
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                for y in range(feet, feet + h):
                    self.cells.add((x, y, z))
                    if not virtual:
                        bp.set(x, y, z, AIR)
                    elif bp.get(x, y, z) is not None:
                        bp.set(x, y, z, AIR)
                if floor is not None:
                    bp.set(x, feet - 1, z, floor(x, feet - 1, z) if callable(floor) else floor)

    def cell(self, x, y, z):
        self.cells.add((x, y, z))
        self.bp.set(x, y, z, AIR)

    def flight(self, x0, z0, direction, feet, n, width=3, head=4):
        """The carved prism of a straight stair climbing `direction` from feet level `feet`: step i at
        (x0 + i*dx, feet + i, z0 + i*dz), `width` wide to the right of the climbing direction."""
        dx, dz = DIRV[direction]
        px, pz = -dz, dx
        for i in range(n):
            for w in range(width):
                x, z = x0 + dx * i + px * w, z0 + dz * i + pz * w
                for y in range(feet + i, feet + i + head + 1):
                    self.cell(x, y, z)

    def inside_rock(self, x, y, z):
        if y <= 0:
            return True
        ix, iz = x - MX0, z - MZ0
        if 0 <= ix < self.solid.shape[0] and 0 <= iz < self.solid.shape[2] and y < TOP:
            return bool(self.solid[ix, y, iz])
        return False

    def wrap(self):
        bp = self.bp
        pts = np.array(sorted(self.cells))
        lo = pts.min(0) - 3
        hi = pts.max(0) + 3
        shape = tuple((hi - lo + 1).tolist())
        c = np.zeros(shape, bool)
        q = pts - lo
        c[q[:, 0], q[:, 1], q[:, 2]] = True

        def dil(a):
            out = a.copy()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == dy == dz == 0:
                            continue
                        out[max(dx, 0):shape[0] + min(dx, 0), max(dy, 0):shape[1] + min(dy, 0),
                            max(dz, 0):shape[2] + min(dz, 0)] |= a[max(-dx, 0):shape[0] + min(-dx, 0),
                                                                  max(-dy, 0):shape[1] + min(-dy, 0),
                                                                  max(-dz, 0):shape[2] + min(-dz, 0)]
            return out
        d1 = dil(c)
        d2 = dil(d1)
        for layer, mask in ((1, d1 & ~c), (2, d2 & ~d1)):
            for p in (np.argwhere(mask) + lo).tolist():
                x, y, z = p
                if bp.get(x, y, z) is not None or not self.inside_rock(x, y, z):
                    continue
                bp.set(x, y, z, wall_spec(x, y, z, layer))


DIRV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def wall_spec(x, y, z, layer):
    """Inner walls: dressed red sandstone above the ground, pale tomb sandstone below; rock behind."""
    h = hash3(x // 2, y // 2, z // 2, 71)
    if y >= 1:
        if layer == 1:
            return CRS if h < 0.55 else (SRS if h < 0.85 else RS)
        return RS
    if layer == 1:
        if y % 6 == 0 and h < 0.6:
            return CSS
        return SS if h < 0.5 else (SMS if h < 0.8 else CSS)
    return SS


def floor_tomb(x, y, z):
    h = hash3(x, y, z, 72)
    return SMS if (x + z) % 2 == 0 and h < 0.7 else (CSS if h < 0.85 else SS)


def floor_hall(x, y, z):
    if abs(x) <= 2:
        return SMS if (z % 4) else CHSS                                       # the processional axis
    return CSS if (x + z) % 2 else SS


def carve_all(C):
    """Every walkable space (see the module docstring for the plan)."""
    # ---- L0: portal, wicket, vestibule, hall, sanctuary
    C.box(-5, 5, -9, FZ, F0, 18, floor=CSS)                         # the portal recess (open to the plaza)
    C.box(-1, 1, -11, -10, F0, 5, floor=SMS)                        # the wicket through the sealing wall
    C.box(-4, 4, -14, -12, F0, 7, floor=floor_hall)                 # vestibule
    C.box(-3, 3, -15, -15, F0, 8, floor=floor_hall)
    x0, z0, x1, z1 = HALL
    C.box(x0, x1, z0, z1, F0, HALL_TOP - F0 + 1, floor=floor_hall)
    C.box(-2, 2, -60, -59, F0, 6, floor=SMS)
    C.box(-7, 7, -72, -61, F0, 10, floor=floor_tomb)               # sanctuary
    # oculus: a grated shaft from the hall floor down into the arena
    C.box(-1, 1, -35, -33, ARENA_TOP + 1, 1 - ARENA_TOP)
    # ---- east: the switchback stair to the Gallery of Crowns
    C.box(16, 18, -19, -17, F0, 5, floor=SMS)
    C.box(19, 21, -19, -16, F0, 5, floor=SMS)
    C.flight(19, -20, "north", F0, 12)          # x 19..21 (the width runs to the right of the climb)
    C.box(19, 25, -34, -32, F0 + 12, 5, floor=CSS)
    C.flight(25, -31, "south", F0 + 12, 12)     # x 25..23
    C.box(23, 29, -19, -17, F0 + 24, 5, floor=CSS)
    C.flight(27, -20, "north", F0 + 24, 12)     # x 27..29
    C.box(19, 29, -34, -32, FC, 5, floor=CSS)
    C.box(11, 18, -34, -32, FC, 5, floor=CSS)
    C.box(11, 13, -31, -16, FC, 5, floor=CSS)
    C.box(-38, 38, -15, -12, FC, 5, floor=floor_hall)              # the Gallery of Crowns
    for wx in (-24, 0, 24):
        C.box(wx - 2, wx + 2, -11, FZ, FC, 4, floor=SMS)          # windows onto the plaza
    C.box(-3, 3, -8, -7, 24, 12)                                    # the niche of Ra above the portal
    # from the gallery's west end up to the loggia of the upper storey (a second vista over the plaza)
    C.flight(-38, -16, "north", FC, 16)                            # x -38..-36
    C.box(-38, -31, -35, -32, FC + 16, 5, floor=CSS)
    C.box(-33, -31, -31, -12, FC + 16, 5, floor=CSS)
    # ---- west: the stair down to L1
    C.box(-17, -16, -31, -29, F0, 5, floor=SMS)
    C.box(-21, -18, -31, -29, F0, 5, floor=SMS)
    C.flight(-33, -31, "east", F1, 12)          # x -33..-22, z -31..-29
    # ---- L1
    C.box(-46, -34, -36, -24, F1, 7, floor=floor_tomb)             # antechamber of Anubis
    C.box(-42, -40, -41, -37, F1, 4, floor=floor_tomb)
    C.box(-60, -38, -62, -42, F1, 8, floor=floor_tomb)             # embalming hall
    C.box(-74, -47, -32, -28, F1, 6, floor=floor_tomb)             # gallery of niches (west arm)
    C.box(-74, -70, -80, -33, F1, 6, floor=floor_tomb)             # (north arm)
    C.flight(-71, -92, "south", F2, 12)         # x -71..-73
    # ---- L2
    C.box(-76, -68, -99, -93, F2, 6, floor=floor_tomb)             # landing
    C.box(-67, -10, -98, -92, F2, 7, floor=floor_tomb)             # flooded gallery
    C.box(-9, 13, -96, -94, F2, 4, floor=floor_tomb)               # trap corridor
    C.box(13, 29, -104, -86, F2, 9, floor=floor_tomb)              # treasury
    C.box(30, 31, -95, -95, F2, 2)                                 # secret door
    C.box(32, 38, -99, -91, F2, 5, floor=floor_tomb)               # secret hoard
    C.box(19, 21, -85, -85, F2, 5, floor=SMS)
    C.flight(19, -77, "north", F2 - 8, 8)       # x 19..21
    C.box(18, 22, -76, -72, F2 - 8, 5, floor=CSS)
    C.flight(19, -64, "north", F3, 8)           # x 19..21
    # ---- L3
    C.box(17, 22, -63, -60, F3, 5, floor=floor_tomb)
    C.box(7, 16, -63, -61, F3, 5, floor=floor_tomb)
    C.box(-6, 6, -67, -57, F3, 7, floor=floor_tomb)                # site of grace
    C.box(-1, 1, -56, -50, F3, 4, floor=SMS)                        # the narrow way to the mist
    ax, az = ARENA
    for x in range(ax - ARENA_R - 1, ax + ARENA_R + 2):
        for z in range(az - ARENA_R - 1, az + ARENA_R + 2):
            if math.hypot(x - ax, z - az) <= ARENA_R + 0.4:
                C.box(x, x, z, z, F3, ARENA_TOP - F3 + 1, floor=CSS)
    C.box(-1, 1, -17, -16, F3, 4, floor=SMS)                        # south door (mist + sealed bars)
    C.box(-6, 6, -15, -7, F3, 6, floor=floor_tomb)                 # reward vault
    C.box(-17, -7, -12, -10, F3, 4, floor=floor_tomb)
    C.box(-19, -17, -15, -13, F3, 4, floor=floor_tomb)
    wx, wz = WELL
    C.box(wx - 4, wx + 4, wz - 4, wz + 4, F3, F0 + 4 - F3 + 1)     # the King's Well
    C.box(-17, -16, -20, -20, F0, 2)                                # its one-way door into the hall
    # ---- the side tomb in the plaza's west cliff
    C.box(-49, -46, 7, 19, 1, 18, virtual=True)
    C.box(-55, -50, 12, 14, 1, 4, floor=SS)
    C.box(-64, -56, 9, 17, 1, 6, floor=floor_tomb)
    # ---- the upper storey's recess (decorative, left unset behind the rock face)
    C.box(-UPPER_W, UPPER_W, -16, FZ, CORNICE + 5, 20, virtual=True)


# ------------------------------------------------------------------ small parts
def build_flight(bp, x0, z0, direction, feet, n, width=3, spec="smooth_sandstone_stairs", fill=SS):
    """The steps of a stair carved by Carver.flight (same arguments), with solid rock under each step."""
    dx, dz = DIRV[direction]
    px, pz = -dz, dx
    for i in range(n):
        for w in range(width):
            x, z = x0 + dx * i + px * w, z0 + dz * i + pz * w
            bp.set(x, feet + i, z, stair(spec, direction))
            for y in range(feet - 1, feet + i):
                bp.set(x, y, z, fill)


def lamp(bp, x, y, z, chain=1, soul=False):
    """A lantern hung from the ceiling block above (y + chain)."""
    for k in range(1, chain + 1):
        bp.set(x, y + k, z, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(x, y, z, hanging=True, soul=soul)


def torch(bp, x, y, z, facing, soul=False):
    bp.wall_torch(x, y, z, facing, soul=soul)


def candles(bp, x, y, z, n=3):
    bp.set(x, y, z, f"candle[candles={n},lit=true,waterlogged=false]")


def pot(bp, x, y, z, facing="north"):
    bp.set(x, y, z, f"decorated_pot[facing={facing},waterlogged=false,cracked=false]")


def glyph(x, y, z):
    return GLYPHS[(x * 3 + y * 5 + z * 7) % 4] + "[facing=" + ("north", "east", "south", "west")[(x + y + z) % 4] + "]"


# ------------------------------------------------------------------ the kings
def king_cells(scale=1.0):
    """Seated colossus in local coordinates (u across, y up from its base, v forward from the façade plane, v >= 1)
    -> block. Proportions of Abu Simbel: throne, shins and feet, lap, torso with belt and broad collar, arms with
    the hands on the knees, the nemes headcloth with its lappets, the false beard and the double crown."""
    cells = {}

    def put(u0, u1, y0, y1, v0, v1, spec):
        for u in range(u0, u1 + 1):
            for y in range(y0, y1 + 1):
                for v in range(v0, v1 + 1):
                    cells[(u, y, v)] = spec(u, y, v) if callable(spec) else spec

    def stone(u, y, v):
        h = hash3(u + 40, y, v, 81)
        if y < 6:
            return SS if h < 0.7 else CSS                           # weathered base
        return SMS if h < 0.72 else (SS if h < 0.92 else CSS)

    # throne: a block with carved sides (the sema-tawy relief on its flanks)
    put(-8, 8, 0, 12, 1, 11, stone)
    for u in (-8, 8):
        for y in range(3, 11):
            for v in range(3, 10):
                if (y + v) % 3 == 0:
                    cells[(u, y, v)] = CSS
                elif y in (3, 10) or v in (3, 9):
                    cells[(u, y, v)] = CHSS
        cells[(u, 7, 6)] = "blue_glazed_terracotta[facing=north]"
    put(-8, 8, 13, 13, 1, 11, CSS)                                  # seat cushion line
    # shins and feet, the panel between the legs set back
    put(-6, -2, 0, 13, 12, 15, stone)
    put(2, 6, 0, 13, 12, 15, stone)
    put(-1, 1, 0, 12, 12, 12, CSS)
    put(-6, -2, 0, 1, 16, 18, stone)
    put(2, 6, 0, 1, 16, 18, stone)
    # lap (thighs) and the pleated kilt
    put(-6, 6, 14, 16, 1, 15, stone)
    for u in range(-6, 7):
        cells[(u, 15, 15)] = CSS if u % 2 else SMS
    # torso: waist 4, chest 5, the belt with gold
    put(-4, 4, 17, 19, 1, 7, stone)
    put(-5, 5, 20, 27, 1, 7, stone)
    put(-4, 4, 23, 26, 8, 8, stone)                                 # chest
    for u in range(-5, 6):
        for v in range(1, 9):
            if (u, 17, v) in cells or v == 8:
                cells[(u, 17, v)] = GOLD if (u + v) % 3 == 0 else CSS
    # arms: upper arms down the sides, forearms on the thighs, fists on the knees
    put(-7, -6, 18, 26, 2, 6, stone)
    put(6, 7, 18, 26, 2, 6, stone)
    put(-6, -3, 17, 18, 7, 14, stone)
    put(3, 6, 17, 18, 7, 14, stone)
    # broad collar (wesekh): bands of lapis, gold and stone on the chest
    for u in range(-6, 7):
        for y, spec in ((26, LAPIS), (27, GOLD), (28, CSS)):
            if abs(u) <= 6 - (28 - y):
                cells[(u, y, 8)] = spec if abs(u) % 2 == 0 or spec == CSS else SMS
        for y in (26, 27, 28):
            for v in range(1, 8):
                if abs(u) <= 6:
                    cells.setdefault((u, y, v), SMS)
    # nemes lappets in front of the shoulders, striped
    for s in (-1, 1):
        for u in range(3, 6):
            for y in range(24, 33):
                for v in (6, 7):
                    cells[(s * u, y, v)] = (LAPIS if (y % 2 == 0 and hash3(u, y, v, 82) < 0.35) else CSS) \
                        if y % 2 == 0 else SMS
    # neck, head, face
    put(-2, 2, 29, 30, 2, 6, stone)
    put(-3, 3, 31, 37, 2, 8, SMS)
    put(-1, 1, 31, 31, 8, 8, CSS)                                   # mouth
    cells[(0, 33, 9)] = SMS                                         # nose
    cells[(0, 34, 9)] = SMS
    for u in (-2, 2):
        cells[(u, 34, 8)] = "black_terracotta"                      # painted eyes
        cells[(u, 35, 8)] = CSS                                     # brows
    put(0, 0, 27, 30, 7, 8, CSS)                                    # false beard
    cells[(0, 26, 8)] = CHSS
    # nemes headcloth around the head: striped wings at the temples, flat top
    for u in range(-5, 6):
        for y in range(31, 39):
            for v in range(1, 8):
                if abs(u) >= 4 or y == 38 or v <= 2:
                    if abs(u) == 5 and y > 36:
                        continue
                    cells[(u, y, v)] = CSS if y % 2 else SMS
    cells[(0, 37, 9)] = GOLD                                        # uraeus
    cells[(0, 36, 9)] = GOLD
    # double crown: the red deshret ring, the white hedjet bulb above it
    put(-4, 4, 39, 40, 1, 7, SRS)
    for k, rr in enumerate((3.2, 3.2, 2.8, 2.4, 2.0, 1.6, 1.0)):
        y = 41 + k
        for u in range(-4, 5):
            for v in range(1, 8):
                if math.hypot(u, (v - 4) * 1.1) <= rr:
                    cells[(u, y, v)] = "calcite"
    cells[(0, 48, 4)] = GOLD
    for v in (1, 2, 3):
        cells[(3, 41 + v, 1)] = SRS                                 # the deshret's back spike
    # the shoulders run up under the nemes wings and the crown's back rises into the cornice: no ledge pocket is
    # left on the statue where a player could get stuck under an overhang
    for u in range(-6, 7):
        for y in (29, 30):
            for v in range(1, 8):
                cells.setdefault((u, y, v), SMS)
    for u in range(-4, 5):
        for y in (41, 42, 43):
            for v in (1, 2):
                cells.setdefault((u, y, v), SRS)
    return cells


def king(bp, cx, broken=False, defaced=False):
    """One seated king. `defaced`: the fourth king, whose face was chiselled away (the boss of the arena below):
    the nose, mouth and eyes are gone and the face is left rough and pitted."""
    cells = king_cells()
    cut = {}
    for (u, y, v), spec in cells.items():
        x, z = cx + u, FZ + v
        if defaced and 31 <= y <= 36 and abs(u) <= 3 and v >= 8:
            if v == 9 or hash01(u * 7 + y, v, 85) < 0.4:
                continue                                    # chiselled out
            spec = SS
        if broken:
            top = 23 + int(hash01(u, v, 83) * 4)
            if y > top:
                cut[(u, y, v)] = spec
                continue
        bp.set(x, KING_Y + y, z, spec)
    if broken:
        fallen_head(bp, cx, cut)


def fallen_head(bp, cx, cut):
    """The head and crown of the broken king lie face up on the plaza, the crown pointing south (Abu Simbel's
    second colossus); a few torso blocks scattered around."""
    for (u, y, v), spec in cut.items():
        if y < 30:
            continue
        x = cx + u - 2
        yy = 1 + (v - 1)
        z = 17 + (y - 30)
        if yy <= 8:
            bp.set(x, yy, z, spec)
    rng = random.Random(84)
    for _ in range(26):
        x = cx + rng.randint(-9, 9)
        z = rng.randint(12, 30)
        if bp.get(x, 1, z) is None:
            bp.set(x, 1, z, rng.choice((SMS, SS, CSS, "smooth_sandstone_slab[type=bottom,waterlogged=false]")))


def baboon(bp, x, y, z):
    """One of the adoring baboons of the crown frieze: squatting, paws raised (2 x 2 x 3)."""
    for dx in (0, 1):
        bp.set(x + dx, y, z, SS)
        bp.set(x + dx, y, z - 1, SS)
        bp.set(x + dx, y + 1, z - 1, SMS)
    bp.set(x, y + 1, z, stair("sandstone_stairs", "south"))
    bp.set(x + 1, y + 1, z, stair("sandstone_stairs", "south"))
    bp.set(x, y + 2, z - 1, CHSS)
    bp.set(x + 1, y + 2, z - 1, CHSS)


# ------------------------------------------------------------------ the façade
def dressed(x, y, z):
    """Ashlar of the façade: courses 2 high, joints staggered, smooth faces with cut-stone joints."""
    course = y // 2
    joint = (x + (course % 2) * 3) % 6 == 0
    h = hash3(x, y, z, 91)
    if joint:
        return CRS
    if y < 6:
        return RS if h < 0.6 else CRS                                  # darker, rougher base courses
    return SRS if h < 0.7 else (CRS if h < 0.9 else RS)


def facade(bp, C):
    cells = C.cells
    W_ = FACADE_W
    # the dressed face (two layers), then the pylon frame: a torus roll up both edges
    for x in range(-W_, W_ + 1):
        for y in range(1, CORNICE + 1):
            for z in (FZ, FZ - 1):
                if (x, y, z) not in cells:
                    bp.set(x, y, z, dressed(x, y, z))
    for s in (-1, 1):
        for y in range(1, CORNICE - 3):
            for (x, z) in ((s * (W_ + 1), FZ), (s * (W_ + 1), FZ + 1), (s * W_, FZ + 1)):
                bp.set(x, y, z, SRS if y % 4 else CRS)
    # the gorge cornice (cavetto) and its fillet, across the whole lower storey
    for x in range(-W_ - 2, W_ + 3):
        bp.set(x, CORNICE - 4, FZ + 1, SRS)
        bp.set(x, CORNICE - 3, FZ + 1, CRS)
        bp.set(x, CORNICE - 3, FZ + 2, stair("red_sandstone_stairs", "north", "top"))
        bp.set(x, CORNICE - 2, FZ + 1, CRS)
        bp.set(x, CORNICE - 2, FZ + 2, CRS)
        bp.set(x, CORNICE - 2, FZ + 3, stair("red_sandstone_stairs", "north", "top"))
        for z in range(FZ + 1, FZ + 4):
            bp.set(x, CORNICE - 1, z, CHRS if x % 3 == 0 else CRS)
        for z in range(FZ, FZ + 5):
            bp.set(x, CORNICE, z, SRS)
    # the frieze of baboons on the cornice (22 of them, repetition with diminution)
    for x in range(-W_ + 2, W_ - 1, 4):
        baboon(bp, x, CORNICE + 1, FZ + 3)
    # the portal: jambs, a lintel with the winged sun, the reveal, the sealing wall with its wicket
    for s in (-1, 1):
        for y in range(F0, 22):
            bp.set(s * 6, y, FZ + 1, CHRS if y % 5 == 0 else CRS)
            bp.set(s * 6, y, FZ, CRS)
    for x in range(-6, 7):
        for y in range(21, 25):
            bp.set(x, y, FZ + 1, CRS if y in (21, 24) else SRS)
    for x in range(-5, 6):
        bp.set(x, 22, FZ + 2, "blue_glazed_terracotta[facing=south]" if abs(x) > 1 else GOLD)
        bp.set(x, 23, FZ + 2, stair("red_sandstone_stairs", "north", "top") if abs(x) > 1 else GOLD)
    bp.set(0, 24, FZ + 2, GOLD)
    for x in range(-5, 6):
        for y in range(F0, 21):
            # back of the recess (z -10): the great door panels, studded, the wicket left open in the middle
            if (x, y, -10) not in cells:
                bp.set(x, y, -10, CHSS if (x % 3 == 0 and y % 3 == 0) else (CSS if abs(x) == 5 or y == 20 else SMS))
        for z in (-9, -8, -7):
            bp.set(x, 21, z, CRS)                                      # recess ceiling
    for y in range(F0, F0 + 6):
        for x in (-2, 2):
            bp.set(x, y, -10, GOLD if y == F0 + 5 else CHSS)          # the wicket's frame
    for x in range(-2, 3):
        bp.set(x, F0 + 5, -10, CHSS)
    torch(bp, -3, F0 + 3, -9, "south")
    torch(bp, 3, F0 + 3, -9, "south")
    # the niche of Ra-Horakhty above the portal: falcon head, sun disk
    for y in range(24, 36):
        for x in range(-3, 4):
            bp.set(x, y, -9, "blue_terracotta" if y > 32 else CRS)
    for y in range(24, 30):
        bp.set(0, y, -8, SMS)
        bp.set(-1, y, -8, SMS if y < 28 else AIR)
        bp.set(1, y, -8, SMS if y < 28 else AIR)
    for y in range(30, 32):
        bp.set(0, y, -8, SS)
    bp.set(0, 32, -7, stair("sandstone_stairs", "south"))           # the falcon's beak
    for dx in (-1, 0, 1):
        for y in (33, 34, 35):
            if abs(dx) + abs(y - 34) <= 1:
                bp.set(dx, y, -8, GOLD)                                # sun disk
    # cartouche panels flanking the niche, glyph columns between the kings
    for s in (-1, 1):
        for y in range(25, 35):
            for x in (s * 4, s * 5):
                bp.set(x, y, FZ, glyph(x, y, FZ) if 26 <= y <= 33 else CHRS)
    for gx in (-25, -23, 23, 25):
        for y in range(4, 22):
            bp.set(gx, y, FZ, glyph(gx, y, FZ) if y % 2 else CHRS)
    # the balcony of appearances over the portal (the gallery of crowns opens onto it)
    for x in range(-3, 4):
        for z in range(FZ + 1, FZ + 4):
            bp.set(x, FC - 1, z, CRS)
        bp.set(x, FC - 2, FZ + 1, stair("red_sandstone_stairs", "south", "top"))
    for x in range(-3, 4):
        bp.set(x, FC, FZ + 3, "red_sandstone_wall")
    for z in range(FZ + 1, FZ + 3):
        bp.set(-3, FC, z, "red_sandstone_wall")
        bp.set(3, FC, z, "red_sandstone_wall")
    # window frames of the gallery of crowns
    for wx in (-24, 24):
        for x in range(wx - 3, wx + 4):
            bp.set(x, FC + 4, FZ, CRS)
            bp.set(x, FC - 1, FZ + 1, stair("red_sandstone_stairs", "south", "top") if abs(x - wx) <= 2 else CRS)
        for y in range(FC, FC + 4):
            bp.set(wx - 3, y, FZ, CHRS)
            bp.set(wx + 3, y, FZ, CHRS)


def upper_storey(bp, C):
    """Petra's Khazneh upper storey: a loggia cut 11 deep into the cliff (columns 16 high under a rock ceiling), the
    tholos standing half out of the cliff face with its cone and urn in relief, and the two broken half-pediments
    carved on the face above the side pavilions."""
    W_ = UPPER_W
    y0 = CORNICE + 4                       # loggia floor
    yc = y0 + 21                           # rock ceiling of the loggia
    for x in range(-W_, W_ + 1):
        for z in range(-16, FZ + 1):
            bp.set(x, y0, z, CRS if (x + z) % 2 else SRS)
        if abs(x) > 8:
            bp.set(x, y0 + 1, FZ, "red_sandstone_wall")                   # parapet of the loggia
    # the tholos, centred on the face plane: podium, a ring of 8 columns round a cella with a false door,
    # entablature, then the cone and the urn carved half out of the rock
    cx, cz = 0, FZ
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d <= 6.8:
                bp.set(x, y0, z, CRS)
                bp.set(x, y0 + 1, z, CRS if d > 5.8 else SRS)
            if d <= 4.3:
                for y in range(y0 + 2, yc - 2):
                    bp.set(x, y, z, SRS if (y - y0) % 4 else CRS)
            if d <= 7.0:
                for y in (yc - 2, yc - 1):
                    bp.set(x, y, z, CRS if y == yc - 2 else SRS)
            if 6.0 <= d <= 7.0 and z > FZ and (x + z) % 2 == 0:
                bp.set(x, yc, z, CHRS)                                    # frieze of the tholos
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = cx + round(math.cos(a) * 6), cz + round(math.sin(a) * 6)
        for y in range(y0 + 2, yc - 2):
            bp.set(x, y, z, CRS if y in (y0 + 2, yc - 3) else SRS)
    for y in range(y0 + 2, y0 + 8):
        for x in (-1, 0, 1):
            bp.set(x, y, cz + 4, "dark_oak_planks" if y < y0 + 7 else CHRS)  # false door of the cella
    bp.cone_roof(cx, yc + 1, cz, 6, "red_sandstone_stairs", cap=CRS, block=CRS)
    top = yc + 7
    for y, r in ((top, 1), (top + 1, 2), (top + 2, 1), (top + 3, 0)):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                bp.set(x, y, z, GOLD if y == top + 3 else CRS)          # the urn (the "treasury" of the legend)
    # side pavilions: two columns, an entablature closing the loggia, the half-pediment on the face above
    for s in (-1, 1):
        xa, xb = s * 15, s * 29
        lo, hi = min(xa, xb), max(xa, xb)
        for cxx in (s * 17, s * 27):
            for x in (cxx, cxx + s):
                for z in (-9, -8):
                    for y in range(y0 + 1, yc - 4):
                        bp.set(x, y, z, CRS if y in (y0 + 1, yc - 5) else SRS)
        for x in range(lo, hi + 1):
            for z in range(-16, FZ + 1):
                for y in range(yc - 4, yc):
                    bp.set(x, y, z, CRS if y != yc - 3 else (CHRS if x % 2 else SRS))
        for x in range(lo + 2, hi - 1):
            for y in range(y0 + 1, yc - 4):
                bp.set(x, y, -15, CRS if (x in (lo + 2, hi - 2) or y in (y0 + 1, yc - 5)) else
                       ("blue_terracotta" if abs(x - s * 22) <= 1 and y0 + 6 <= y <= y0 + 11 else SRS))
        for x in range(lo, hi + 1):
            k = abs(x - xb)                                              # 0 at the outer edge
            ptop = yc + k // 2
            for z in range(FZ, FZ + 3):
                for y in range(yc, ptop + 1):
                    bp.set(x, y, z, CRS if y < ptop else stair("red_sandstone_stairs", "west" if s > 0 else "east"))
        # an eagle (acroterion) on the outer corner
        bp.set(xb, yc + 1, FZ + 2, CHRS)
        bp.set(xb, yc + 2, FZ + 2, stair("red_sandstone_stairs", "south"))


# ------------------------------------------------------------------ L0: hypostyle hall, sanctuary, stairs, gallery
def osiris(bp, x, z, s):
    """Mummiform Osiris standing against a pillar's aisle face (x = the face cell, s = +1 facing east / -1 west):
    3 wide, 2 deep, crossed arms holding the crook and the flail, the white atef crown."""
    f, b = x + s, x                       # front and back columns of the figure
    for dz in (-1, 0, 1):
        bp.set(b, F0, z + dz, CSS)
        bp.set(f, F0, z + dz, CSS)
        for y in range(F0 + 1, F0 + 11):
            bp.set(b, y, z + dz, SMS)
            if abs(dz) < 1 or y < F0 + 9:
                bp.set(f, y, z + dz, SMS if (y - F0) % 3 else SS)    # linen bands
    bp.set(f, F0 + 8, z - 1, GOLD)                                    # crook
    bp.set(f, F0 + 8, z + 1, "orange_terracotta")                     # flail
    bp.set(f, F0 + 9, z, CSS)
    for dz in (-1, 0, 1):
        bp.set(b, F0 + 11, z + dz, CSS)                                # nemes wings
    bp.set(f, F0 + 11, z, SMS)                                         # face
    bp.set(f, F0 + 10, z, CSS)                                         # beard
    bp.set(b, F0 + 12, z, CSS)
    bp.set(f, F0 + 12, z, SMS)
    for y in range(F0 + 13, F0 + 16):
        bp.set(b, y, z, "calcite")
    bp.set(f, F0 + 13, z, "calcite")
    bp.set(b, F0 + 13, z - 1, GOLD)
    bp.set(b, F0 + 13, z + 1, GOLD)


def hall(bp, C):
    x0, z0, x1, z1 = HALL
    cells = C.cells
    # walls: dado, two painted friezes, battle reliefs in the middle bays
    for z in range(z0, z1 + 1):
        for x in (x0 - 1, x1 + 1):
            for y in range(F0, HALL_TOP + 1):
                if (x, y, z) in cells:
                    continue
                if y <= F0 + 1:
                    spec = CSS
                elif y in (F0 + 5, F0 + 13):
                    spec = CHRS
                elif F0 + 6 <= y <= F0 + 7 or F0 + 14 <= y <= F0 + 15:
                    spec = glyph(x, y, z)
                elif F0 + 8 <= y <= F0 + 12 and z0 + 8 < z < z1 - 8:
                    spec = ("orange_terracotta", "white_terracotta", "yellow_terracotta",
                            "light_blue_terracotta")[int(hash3(x, y // 2, z // 2, 93) * 4)]
                else:
                    spec = SRS if (y + z) % 7 else CRS
                bp.set(x, y, z, spec)
    for x in range(x0, x1 + 1):
        for z in (z0 - 1, z1 + 1):
            for y in range(F0, HALL_TOP + 1):
                if (x, y, z) not in cells:
                    bp.set(x, y, z, CSS if y <= F0 + 1 else (glyph(x, y, z) if y in (F0 + 6, F0 + 14) else SRS))
    # the star ceiling with a band of vultures down the axis
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if abs(x) <= 2:
                spec = "yellow_glazed_terracotta[facing=north]" if (z % 4 < 2) == (abs(x) != 1) else \
                    "orange_terracotta"
            elif hash01(x, z, 94) < 0.06:
                spec = STAR
            elif hash01(x, z, 95) < 0.05:
                spec = GOLD
            else:
                spec = "blue_terracotta"
            bp.set(x, HALL_TOP + 1, z, spec)
    # eight-plus-two Osirid pillars: 3 x 3 shafts, papyrus capitals, the god facing the aisle
    for cz in (-21, -29, -37, -45, -53):
        for s in (-1, 1):
            cx = s * 7
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    for y in range(F0, HALL_TOP - 3):
                        bp.set(x, y, z, CRS if (y - F0) % 5 == 0 else SRS)
            for x in range(cx - 2, cx + 3):
                for z in range(cz - 2, cz + 3):
                    if abs(x - cx) == 2 and abs(z - cz) == 2:
                        continue
                    bp.set(x, HALL_TOP - 3, z, CSS)
                    bp.set(x, HALL_TOP - 2, z, glyph(x, HALL_TOP - 2, z) if (x + z) % 2 else CSS)
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    bp.set(x, HALL_TOP - 1, z, CRS)
                    bp.set(x, HALL_TOP, z, CRS)
            osiris(bp, cx - s * 2, cz, -s)
            torch(bp, cx + s * 2, F0 + 4, cz, "east" if s > 0 else "west")
    # the grate over the arena, ringed with gold
    for x in range(-2, 3):
        for z in range(-36, -31):
            if abs(x) <= 1 and -35 <= z <= -33:
                bp.set(x, F0 - 1, z, "iron_bars")
            else:
                bp.set(x, F0 - 1, z, GOLD if (x + z) % 2 else CHSS)
    # light: lanterns on long chains down the aisles, torches on the walls
    for z in (-24, -42, -50):
        lamp(bp, 0, HALL_TOP - 8, z, chain=8)
    for z in (-25, -33, -41, -49):
        lamp(bp, -12, HALL_TOP - 6, z, chain=6)
        lamp(bp, 12, HALL_TOP - 6, z, chain=6)
    for z in range(z0 + 3, z1, 6):
        if (x0 - 1, F0 + 3, z) not in cells:
            torch(bp, x0, F0 + 3, z, "east")
        if (x1 + 1, F0 + 3, z) not in cells:
            torch(bp, x1, F0 + 3, z, "west")
    # the King's Well opens into the west aisle (iron door, lever on the well side only: a one-way shortcut)
    bp.door(-17, F0, -20, "west", wood="iron")
    bp.set(-18, F0 + 1, -21, "lever[face=wall,facing=west,powered=false]")
    bp.set(-16, F0 + 2, -20, CHRS)
    # the Dune King, the necropolis' old guardian, still holds the far end of the hall (no mist: the hall is the
    # way through, like the Sentinel of the Fallen Colossus); his seal sits in the floor of the south aisle
    bp.boss_seal(0, F0 - 1, -46, DUNE_KING, 12)


def sanctuary(bp):
    """Four seated gods against the back wall (Ptah, Amun-Ra, Ra-Horakhty, the deified king), an offering altar."""
    crowns = ("blue_terracotta", GOLD, "orange_terracotta", "calcite")
    for i, gx in enumerate((-5, -2, 2, 5)):
        for x in range(gx - 1, gx + 2):
            for z in range(-72, -69):
                for y in range(F0, F0 + 3):
                    bp.set(x, y, z, CSS if y == F0 + 2 else SS)
            bp.set(x, F0, -69, SMS)
            bp.set(x, F0 + 1, -69, SMS)
        for y in range(F0 + 3, F0 + 6):
            for z in (-72, -71):
                bp.set(gx, y, z, SMS)
                if y < F0 + 5:
                    bp.set(gx - 1, y, z, SMS)
                    bp.set(gx + 1, y, z, SMS)
        bp.set(gx, F0 + 6, -71, SMS)
        bp.set(gx, F0 + 6, -72, CSS)
        bp.set(gx, F0 + 7, -72, crowns[i])
        bp.set(gx, F0 + 7, -71, crowns[i] if i != 0 else SMS)
    bp.set(0, F0, -66, CHSS)
    bp.set(-1, F0, -66, stair("smooth_sandstone_stairs", "east"))
    bp.set(1, F0, -66, stair("smooth_sandstone_stairs", "west"))
    candles(bp, 0, F0 + 1, -66, 4)
    bp.set(0, F0, -63, "lectern[facing=south,has_book=false,powered=false]")
    for x in (-6, 6):
        lamp(bp, x, F0 + 7, -62, chain=2)
        pot(bp, x, F0, -69)


def east_stair(bp):
    build_flight(bp, 19, -20, "north", F0, 12, spec="smooth_red_sandstone_stairs", fill=RS)
    build_flight(bp, 25, -31, "south", F0 + 12, 12, spec="smooth_red_sandstone_stairs", fill=RS)
    build_flight(bp, 27, -20, "north", F0 + 24, 12, spec="smooth_red_sandstone_stairs", fill=RS)
    for (x, y, z, f) in ((19, F0 + 14, -34, "south"), (29, F0 + 26, -17, "north"), (24, FC + 2, -34, "south"),
                         (11, FC + 2, -24, "east")):
        torch(bp, x, y, z, f)


def gallery_of_crowns(bp):
    for x in range(-38, 39):
        for y in range(FC, FC + 5):
            if bp.get(x, y, -16) not in (None, "minecraft:air"):
                bp.set(x, y, -16, glyph(x, y, -16) if y == FC + 2 and x % 4 else (CHRS if y == FC + 4 else SRS))
    for x in range(-32, 37, 8):
        torch(bp, x, FC + 3, -15, "south")
    bp.chest(-38, FC, -13, "east", loot=LOOT + "necropolis_gallery")
    bp.set(-38, FC, -12, "lectern[facing=east,has_book=false,powered=false]")
    pot(bp, -35, FC, -12)
    build_flight(bp, -38, -16, "north", FC, 16, spec="smooth_red_sandstone_stairs", fill=RS)
    torch(bp, -36, FC + 18, -34, "south")
    pot(bp, 37, FC, -12)
    for x in (-12, 12):
        bp.set(x, FC, -15, SMS)
        bp.set(x, FC + 1, -15, "calcite")                              # statuettes of the king


# ------------------------------------------------------------------ L1: antechamber, embalming hall, gallery of niches
def level1(bp, C):
    build_flight(bp, -33, -31, "east", F1, 12)
    # antechamber of Anubis: the jackal recumbent on his shrine, soul light
    for x in range(-43, -37):
        for z in range(-27, -24):
            bp.set(x, F1, z, "black_terracotta" if x in (-43, -38) else GOLD if z == -26 and x % 2 else
                   "polished_blackstone")
    for x in range(-42, -38):
        bp.set(x, F1 + 1, -26, "polished_blackstone")                 # the jackal's body
    bp.set(-39, F1 + 2, -26, "polished_blackstone")
    bp.set(-38, F1 + 2, -26, stair("polished_blackstone_stairs", "east"))   # muzzle
    bp.set(-39, F1 + 3, -27, "polished_blackstone_wall")                  # ears
    bp.set(-39, F1 + 3, -25, "polished_blackstone_wall")
    bp.set(-42, F1 + 2, -26, stair("polished_blackstone_stairs", "west", "top"))
    for (x, z) in ((-45, -35), (-35, -35), (-45, -25), (-35, -25)):
        bp.set(x, F1, z, "sandstone_wall")
        candles(bp, x, F1 + 1, z, 4)
    lamp(bp, -40, F1 + 5, -31, chain=1, soul=True)
    # embalming hall: tables with wrapped bodies, natron basins, canopic jars on shelves, the priests' tools
    for tx in (-56, -52, -46, -42):
        for tz0 in (-57, -49):
            for dz in range(3):
                bp.set(tx, F1, tz0 + dz, "smooth_stone")
            bp.set(tx, F1 + 1, tz0, "white_wool")
            bp.set(tx, F1 + 1, tz0 + 1, "white_wool")
            bp.set(tx, F1 + 1, tz0 + 2, "skeleton_skull[rotation=0]")
    for (x, z) in ((-58, -44), (-40, -44), (-58, -60)):
        bp.set(x, F1, z, "cauldron")
    for x in range(-58, -39):
        if x % 2 == 0:
            bp.set(x, F1 + 2, -61, "cut_sandstone_slab[type=top,waterlogged=false]")
            pot(bp, x, F1 + 3, -61, "south")
    bp.set(-49, F1, -61, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(-47, F1, -61, "lectern[facing=south,has_book=false,powered=false]")
    bp.barrel(-59, F1, -47, "up")
    bp.barrel(-59, F1, -48, "up")
    bp.chest(-59, F1, -52, "east", loot=LOOT + "necropolis_embalmer")
    bp.spawner(-49, F1, -52, "minecraft:husk")
    for (x, z) in ((-54, -45), (-44, -45), (-54, -59), (-44, -59)):
        lamp(bp, x, F1 + 6, z, chain=1)
    # gallery of niches: loculi on two rows along both walls, with bones and shrouds; a few sarcophagi
    rng = random.Random(97)
    for x in range(-72, -48, 3):
        for wz, f in ((-33, "south"), (-27, "north")):
            for y in (F1 + 1, F1 + 3):
                for dx in (0, 1):
                    bp.set(x + dx, y, wz, rng.choice(("bone_block[axis=x]", "white_wool", "skeleton_skull[rotation=4]",
                                                      "white_wool")) if rng.random() < 0.7 else AIR)
            torch(bp, x + 2, F1 + 2, wz + (1 if f == "south" else -1), f, soul=True)
    for z in range(-78, -34, 3):
        for wx, f in ((-75, "east"), (-69, "west")):
            for y in (F1 + 1, F1 + 3):
                for dz in (0, 1):
                    bp.set(wx, y, z + dz, rng.choice(("bone_block[axis=z]", "white_wool", "skeleton_skull[rotation=0]",
                                                      "white_wool")) if rng.random() < 0.7 else AIR)
            torch(bp, wx + (1 if f == "east" else -1), F1 + 2, z + 2, f, soul=True)
    for z in (-70, -58, -46):
        for dz in range(3):
            bp.set(-74, F1, z + dz, SMS)
            bp.set(-74, F1 + 1, z + dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    bp.chest(-73, F1, -29, "west", loot=LOOT + "necropolis_gallery")
    build_flight(bp, -71, -92, "south", F2, 12)


# ------------------------------------------------------------------ L2: flooded gallery, trap corridor, treasury
def level2(bp, C):
    # landing: a lioness-headed Sekhmet guards the way down
    for y in range(F2, F2 + 4):
        bp.set(-76, y, -96, SMS if y < F2 + 3 else "orange_terracotta")
    torch(bp, -75, F2 + 2, -99, "south")
    torch(bp, -69, F2 + 3, -93, "north")
    # flooded gallery: a causeway between two pools, the ceiling fallen in two places
    x0, x1 = -67, -10
    for x in range(x0, x1 + 1):
        for z in (-98, -97, -93, -92):
            bp.set(x, F2 - 1, z, "water")
            bp.set(x, F2 - 2, z, SS)
        for z in (-96, -94):
            if x % 5 == 0:
                bp.set(x, F2 - 1, z, CHSS)                             # kerb stones of the causeway
    rng = random.Random(98)
    for cx in (-49, -26):
        # rubble mound across the causeway (slab, block, slab: walkable), blocks fallen into the pools
        for dx, spec in ((-2, "sandstone_slab[type=bottom,waterlogged=false]"), (-1, SS), (0, CSS), (1, SS),
                         (2, "sandstone_slab[type=bottom,waterlogged=false]")):
            for z in (-96, -95, -94):
                if abs(dx) < 2 or rng.random() < 0.8:
                    bp.set(cx + dx, F2, z, spec if abs(dx) < 2 else "sandstone_slab[type=bottom,waterlogged=false]")
        for dx in range(-3, 4):
            for z in (-98, -97, -93, -92):
                if rng.random() < 0.55:
                    bp.set(cx + dx, F2 - 1, z, rng.choice((SS, CSS, "smooth_sandstone")))
                    if rng.random() < 0.4:
                        bp.set(cx + dx, F2, z, rng.choice((SS, "sandstone_slab[type=bottom,waterlogged=false]")))
        # the hole in the ceiling: the vault has dropped, rough rock above
        for dx in range(-2, 3):
            for z in range(-97, -92):
                if abs(dx) + abs(z + 95) <= 3:
                    bp.set(cx + dx, F2 + 6, z, AIR)
                    bp.set(cx + dx, F2 + 7, z, SS if rng.random() < 0.7 else "smooth_sandstone")
    for x in (-60, -40, -18):
        lamp(bp, x, F2 + 5, -95, chain=1, soul=True)
    bp.set(-36, F2 - 1, -92, SS)
    bp.spawner(-36, F2, -92, MOB_CRAWLER)
    bp.set(-20, F2 - 1, -92, SS)
    bp.chest(-20, F2, -92, "north", loot=LOOT + "necropolis_embalmer")
    # trap corridor: five visible pressure plates along the north wall, each in front of a dart dispenser
    items = nbt.List([nbt.Compound({"Slot": nbt.Byte(0), "id": nbt.String("minecraft:arrow"), "count": nbt.Int(16)})])
    for x in (-5, -1, 3, 7, 11):
        bp.set(x, F2, -97, "dispenser[facing=south,triggered=false]", {"Items": items})
        bp.set(x, F2, -96, "stone_pressure_plate[powered=false]")
        bp.set(x, F2 + 2, -97, CHSS)
    for x in (-8, 4):
        bp.set(x, F2, -94, "skeleton_skull[rotation=6]")
    # treasury: gold heaped along the walls, four pillars, the chests on a dais, a falcon of gold
    for (px, pz) in ((17, -100), (25, -100), (17, -90), (25, -90)):
        for x in (px, px + 1):
            for z in (pz, pz + 1):
                for y in range(F2, F2 + 9):
                    bp.set(x, y, z, CRS if y in (F2, F2 + 8) else (glyph(x, y, z) if y == F2 + 5 else SRS))
    for x in range(14, 29):
        for z in (-104, -103, -87):
            h = int(hash01(x, z, 99) * 3)
            for y in range(F2, F2 + h):
                bp.set(x, y, z, GOLD if hash3(x, y, z, 100) < 0.6 else "raw_gold_block")
    for z in range(-102, -88):
        h = int(hash01(28, z, 101) * 2) + 1
        if z in (-97, -96, -95, -94):
            continue
        for y in range(F2, F2 + h):
            bp.set(28, y, z, GOLD if hash3(28, y, z, 102) < 0.6 else "raw_gold_block")
    for x in range(19, 24):
        for z in range(-102, -99):
            bp.set(x, F2, z, CHSS if (x + z) % 2 else GOLD)
    bp.chest(20, F2 + 1, -101, "south", loot=LOOT + "necropolis_treasury")
    bp.chest(22, F2 + 1, -101, "south", loot=LOOT + "necropolis_treasury")
    for x in (19, 23):
        bp.set(x, F2 + 1, -102, GOLD)
        bp.set(x, F2 + 2, -102, stair("sandstone_stairs", "south"))       # the falcons
    for (x, z) in ((15, -88), (27, -100), (15, -102)):
        pot(bp, x, F2, z)
    for (x, z) in ((21, -88), (21, -95)):
        lamp(bp, x, F2 + 7, z, chain=1)
    bp.spawner(15, F2, -95, MOB_CRAWLER)
    # the secret hoard: an iron door among the glyphs of the east wall, opened by a button hidden in the frieze
    for z in range(-100, -89):
        for y in range(F2, F2 + 5):
            if (30, y, z) not in C.cells:
                bp.set(30, y, z, glyph(30, y, z) if (y + z) % 2 else CHSS)
    bp.door(30, F2, -95, "east", wood="iron")
    bp.set(29, F2 + 1, -97, "stone_button[face=wall,facing=west,powered=false]")
    bp.set(32, F2 + 1, -94, "stone_button[face=wall,facing=east,powered=false]")
    for x in range(33, 38):
        for z in (-98, -97):
            bp.set(x, F2, z, GOLD if (x + z) % 2 else "raw_gold_block")
    for dx in range(3):
        bp.set(34 + dx, F2, -93, SMS)
        bp.set(34 + dx, F2 + 1, -93, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    bp.chest(37, F2, -95, "west", loot=LOOT + "necropolis_treasury")
    candles(bp, 33, F2, -92, 3)
    candles(bp, 37, F2, -92, 2)
    build_flight(bp, 19, -77, "north", F2 - 8, 8)
    build_flight(bp, 19, -64, "north", F3, 8)
    torch(bp, 18, F2 - 5, -74, "east")


# ------------------------------------------------------------------ L3: site of grace, arena, vault, the King's Well
def seated_statue(bp, cx, y0, zb, height=12, crown=GOLD):
    """A smaller seated king facing north (-z), its back at z = zb: for the arena's dais."""
    k = height / 12.0
    def rz(v):
        return zb - int(round(v * k))
    for x in range(cx - 2, cx + 3):
        for v in range(0, 5):
            for y in range(y0, y0 + int(4 * k)):
                bp.set(x, y, rz(v), SS if y < y0 + 2 else SMS)
    for x in (cx - 2, cx - 1, cx + 1, cx + 2):
        for y in range(y0, y0 + int(4 * k)):
            bp.set(x, y, rz(5), SMS)
    for x in range(cx - 2, cx + 3):
        for y in range(y0 + int(4 * k), y0 + int(9 * k)):
            for v in (0, 1, 2):
                bp.set(x, y, rz(v), SMS if abs(x - cx) < 2 or y < y0 + int(8 * k) else CSS)
    for x in range(cx - 1, cx + 2):
        for y in range(y0 + int(9 * k), y0 + int(11 * k)):
            for v in (0, 1, 2):
                bp.set(x, y, rz(v), CSS if abs(x - cx) == 1 else SMS)
    bp.set(cx, y0 + int(11 * k), rz(1), crown)
    bp.set(cx, y0 + int(11 * k) + 1, rz(1), crown)
    bp.set(cx, y0 + int(9 * k) - 1, rz(3), CSS)                        # beard


def jackal(bp, x, z, facing):
    """Anubis recumbent on a plinth, looking towards the arena's centre."""
    dx, dz = DIRV[facing]
    bp.set(x, F3, z, CRS)
    bp.set(x - dx, F3, z - dz, CRS)
    bp.set(x, F3 + 1, z, "polished_blackstone")
    bp.set(x - dx, F3 + 1, z - dz, "polished_blackstone")
    bp.set(x, F3 + 2, z, stair("polished_blackstone_stairs", facing))
    bp.set(x - dx, F3 + 2, z - dz, "polished_blackstone_wall")


def level3(bp, C):
    # the site of grace: waystone on a dais, benches and candles, murals of the weighing of the heart
    cx, cz = 0, -62
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            bp.set(x, F3 - 1, z, CHSS if (x + z) % 2 else SMS)
    bp.set(cx, F3 - 1, cz, GOLD)
    bp.set(cx, F3, cz, MOD["waystone"])
    for (x, z) in ((cx - 3, cz - 3), (cx + 3, cz - 3), (cx - 3, cz + 3), (cx + 3, cz + 3)):
        bp.set(x, F3, z, "sandstone_wall")
        candles(bp, x, F3 + 1, z, 4)
    for z in range(cz - 2, cz + 3):
        bp.stairs(-6, F3, z, "smooth_sandstone_stairs", "east")
        bp.stairs(6, F3, z, "smooth_sandstone_stairs", "west")
    for x in range(-6, 7):
        for y in (F3 + 2, F3 + 3):
            bp.set(x, y, -68, glyph(x, y, -68))
    lamp(bp, cx, F3 + 4, cz, chain=2)
    pot(bp, -5, F3, -66)
    pot(bp, 5, F3, -66)


def arena(bp, C):
    ax, az = ARENA
    fy = F3 - 1
    # floor: rings of gold and lapis round the seal, the processional strip from the north door to the dais
    for x in range(ax - ARENA_R, ax + ARENA_R + 1):
        for z in range(az - ARENA_R, az + ARENA_R + 1):
            d = math.hypot(x - ax, z - az)
            if d > ARENA_R + 0.4:
                continue
            if 5.5 <= d < 6.4 or 12.5 <= d < 13.3:
                spec = GOLD if (x + z) % 2 else LAPIS
            elif abs(x) <= 1:
                spec = SMS
            else:
                spec = CSS if int(d) % 2 else SS
            bp.set(x, fy, z, spec)
    # the star ceiling (the grate of the hall above is its oculus)
    for x in range(ax - ARENA_R, ax + ARENA_R + 1):
        for z in range(az - ARENA_R, az + ARENA_R + 1):
            if math.hypot(x - ax, z - az) <= ARENA_R + 0.4 and (x, ARENA_TOP + 1, z) not in C.cells:
                bp.set(x, ARENA_TOP + 1, z, STAR if hash01(x, z, 111) < 0.08 else "blue_terracotta")
    # engaged columns round the wall (not in the fight), jackals between them
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        x, z = ax + round(math.cos(a) * 15.6), az + round(math.sin(a) * 15.6)
        for y in range(F3, ARENA_TOP + 1):
            bp.set(x, y, z, CRS if (y - F3) % 6 == 0 else SRS)
        bp.set(x, ARENA_TOP - 2, z, CHRS)
        jx, jz = ax + round(math.cos(a + math.pi / 12) * 13.2), az + round(math.sin(a + math.pi / 12) * 13.2)
        if abs(jx) > 3 and k % 2 == 0:
            facing = "west" if jx > 0 else "east"
            jackal(bp, jx, jz, facing)
    # the dais of the king on the south side, two seated colossi, the throne before the vault door
    for x in range(-6, 7):
        bp.set(x, F3, -23, stair("smooth_sandstone_stairs", "north"))
        for z in range(-22, -18):
            bp.set(x, F3, z, CHSS if (x + z) % 2 else SMS)
    bp.set(0, F3 + 1, -20, stair("smooth_sandstone_stairs", "north"))
    bp.set(-1, F3 + 1, -20, GOLD)
    bp.set(1, F3 + 1, -20, GOLD)
    for s in (-1, 1):
        seated_statue(bp, s * 10, F3, -19, 12, crown=GOLD if s < 0 else "calcite")
    for (x, z) in ((-12, -40), (12, -40), (-12, -28), (12, -28), (0, -46), (-8, -24), (8, -24)):
        lamp(bp, x, ARENA_TOP - 1, z, chain=1)
    bp.boss_seal(ax, fy, az, BOSS, ARENA_R - 1)
    # mist on both doors; the vault behind sealed bars that open when the king falls
    bp.mist(-1, F3, -51, 1, F3 + 3, -51)
    bp.mist(-1, F3, -17, 1, F3 + 3, -17)
    for x in (-1, 0, 1):
        for y in range(F3, F3 + 4):
            bp.set(x, y, -16, MOD["vault_bars"])


def vault(bp, C):
    # the king's sarcophagus of gold and lapis, his treasure, the passage to the well
    for x in range(-1, 2):
        for z in range(-13, -9):
            bp.set(x, F3, z, LAPIS if x == 0 else GOLD)
            bp.set(x, F3 + 1, z, "smooth_sandstone_slab[type=bottom,waterlogged=false]" if x else GOLD)
    bp.chest(-4, F3, -8, "north", loot=LOOT + "necropolis_vault")
    bp.chest(4, F3, -8, "north", loot=LOOT + "necropolis_vault")
    for x in (-6, -5, 5, 6):
        for z in (-15, -14, -8, -7):
            if hash01(x, z, 112) < 0.7:
                bp.set(x, F3, z, GOLD if hash01(x, z, 113) < 0.6 else "raw_gold_block")
    pot(bp, -6, F3, -11)
    pot(bp, 6, F3, -11)
    lamp(bp, 0, F3 + 4, -11, chain=1)
    torch(bp, -12, F3 + 2, -10, "north")


def well(bp):
    """The King's Well: a spiral of half slabs (two per level) on the square ring 3 round a central column, from
    the vault level up to the hall; its last step lands in front of the door, a floor caps the shaft there."""
    wx, wz = WELL
    r = 3
    ring = [(x, z) for x in range(wx - r, wx + r + 1) for z in range(wz - r, wz + r + 1)
            if max(abs(x - wx), abs(z - wz)) == r]
    ring.sort(key=lambda p: math.atan2(p[1] - wz, p[0] - wx))
    y0, y1 = F3, F0 - 1
    n = 2 * (y1 - y0 + 1)
    top = (wx + r, wz)
    i0 = (ring.index(top) - (n - 1)) % len(ring)
    level = {}
    for y in range(y0 - 1, y1 + 6):
        bp.set(wx, y, wz, SMS if y % 8 else CHSS)
    i = i0
    for y in range(y0, y1 + 1):
        for k in range(2):
            x, z = ring[i % len(ring)]
            bp.slab(x, y, z, "smooth_sandstone_slab", "bottom" if k == 0 else "top")
            level[(x, z)] = y
            i += 1
    # the cap at the hall's level: everywhere except over the last turn of the stair
    for x in range(wx - 4, wx + 5):
        for z in range(wz - 4, wz + 5):
            if (x, z) == (wx, wz):
                continue
            if (x, z) in level and level[(x, z)] > y1 - 4:
                continue
            bp.set(x, y1, z, CSS)
    for k, y in enumerate(range(y0 + 3, y1, 7)):
        dx, dz = ((1, 0), (0, 1), (-1, 0), (0, -1))[k % 4]
        torch(bp, wx + dx, y, wz + dz, ("east", "south", "west", "north")[k % 4])


# ------------------------------------------------------------------ outside: plaza, side tomb, canyon, camp
def canyon_point(a):
    """(x, z) on the canyon centreline at distance a from the plaza."""
    acc = 0.0
    for (ax_, az_), (bx, bz) in zip(CANYON[:-1], CANYON[1:]):
        L = math.hypot(bx - ax_, bz - az_)
        if acc + L >= a:
            t = (a - acc) / L
            return int(round(ax_ + (bx - ax_) * t)), int(round(az_ + (bz - az_) * t))
        acc += L
    return CANYON[-1]


def plaza(bp):
    """The court floor (sand, a paved way from the canyon to the kings), the terrace, the hub waystone."""
    pz = plaza_cut(1)
    cz_ = canyon_cut(1)
    for ix, iz in np.argwhere(pz | cz_).tolist():
        x, z = int(XS[ix]), int(ZS[iz])
        h = hash01(x, z, 121)
        if pz[ix, iz]:
            spec = "sand" if h < 0.5 else ("red_sand" if h < 0.85 else SS)
        else:
            spec = "red_sand" if h < 0.6 else ("gravel" if h < 0.75 else RS)
        bp.set(x, 0, z, spec)
        bp.set(x, -1, z, SS)
    # the paved way: from the canyon mouth to the terrace stair
    a, b = (9, 34), (0, 17)
    for k in range(40):
        t = k / 39
        px, pz_ = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for dx in range(-3, 4):
            x, z = int(round(px + dx)), int(round(pz_))
            bp.set(x, 0, z, SMS if abs(dx) < 3 else CSS)
    # the terrace of the kings, two steps up, a stair in the axis
    for x in range(-FACADE_W - 1, FACADE_W + 2):
        for z in range(FZ + 1, 15):
            bp.set(x, 1, z, RS)
            bp.set(x, 2, z, CRS if (x + z) % 4 == 0 else SRS)
        bp.set(x, 2, 14, CRS)
    for x in range(-6, 7):
        bp.set(x, 2, 15, stair("smooth_sandstone_stairs", "north"))
        bp.set(x, 1, 15, SS)
        bp.set(x, 1, 16, stair("smooth_sandstone_stairs", "north"))
    for s in (-1, 1):
        for y in (1, 2):
            bp.set(s * 8, y, 16, CSS)
        bp.set(s * 8, 3, 16, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # hub waystone on a little dais in the west of the court
    wx, wz = -30, 24
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            bp.set(x, 0, z, CHSS if (x + z) % 2 else SMS)
    bp.set(wx, 1, wz, MOD["waystone"])


def side_tomb(bp):
    """A smaller rock-cut tomb in the west cliff of the plaza (Petra's 'palace tombs'): pilasters, an entablature, a
    crow-step crown; inside, loculi, a sarcophagus and a chest."""
    fx = -50
    for z in range(7, 20):
        for y in range(1, 19):
            for x in (fx, fx - 1, fx - 2):
                if bp.get(x, y, z) in (None, "minecraft:air") or x == fx:
                    if not (12 <= z <= 14 and y <= 4):
                        bp.set(x, y, z, dressed(x, y, z))
    for z in (8, 9, 17, 18):
        for y in range(1, 13):
            bp.set(fx + 1, y, z, SRS if y % 4 else CRS)
        bp.set(fx + 1, 13, z, CHRS)
    for z in range(7, 20):
        bp.set(fx + 1, 14, z, CRS)
        bp.set(fx + 2, 14, z, stair("red_sandstone_stairs", "east", "top"))
        bp.set(fx + 1, 15, z, SRS)
    for z in range(7, 20):
        step = min(z - 7, 19 - z) % 4
        for y in range(16, 16 + (1 if step < 2 else 2)):
            bp.set(fx + 1, y, z, CRS)
    for y in range(1, 6):
        for z in (11, 15):
            bp.set(fx + 1, y, z, CHRS)
    for z in range(11, 16):
        bp.set(fx + 1, 5, z, CHRS)
    # inside: loculi, a sarcophagus, the chest, a lantern
    for z in range(10, 17, 2):
        for y in (2, 4):
            bp.set(-65, y, z, "bone_block[axis=x]" if (y + z) % 4 else AIR)
    for dz in range(3):
        bp.set(-62, 1, 11 + dz, SMS)
        bp.set(-62, 2, 11 + dz, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    bp.chest(-63, 1, 16, "east", loot=LOOT + "necropolis_gallery")
    lamp(bp, -60, 5, 13, chain=1)
    torch(bp, -55, 3, 12, "south")


def canyon(bp):
    """The slot canyon: a chockstone wedged high up, a carved gate arch, votive niches with lamps."""
    # chockstone
    cx, cz = canyon_point(24)
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            for y in range(24, 33):
                if math.sqrt((x - cx) ** 2 + ((y - 28) * 1.2) ** 2 + (z - cz) ** 2) <= 4.3:
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, ROCK_LADDER[2 + int(hash3(x, y, z, 131) * 3)])
    # the gate arch near the mouth (Petra's Siq arch): a dressed beam with voussoirs
    for ix, iz in np.argwhere(np.abs(CAN_A - 56) <= 1.6).tolist():
        x, z = int(XS[ix]), int(ZS[iz])
        for y in range(15, 21):
            if _cut_at(y, ix, iz):
                bp.set(x, y, z, CRS if y > 15 else stair("red_sandstone_stairs", "north", "top"))
    # votive niches with lamps along the walls
    for a in (12, 30, 44, 62):
        px, pz = canyon_point(a)
        for s in (-1, 1):
            x = px
            while _cut_at(2, x - MX0, pz - MZ0) and abs(x - px) < 9:
                x += s
            if abs(x - px) >= 9:
                continue
            for y in (2, 3):
                bp.set(x, y, pz, AIR)
            bp.set(x, 1, pz, CRS)
            bp.set(x, 4, pz, CHRS)
            bp.lantern(x, 2, pz)
            break


_CUT_CACHE = {}


def _cut_at(y, ix, iz):
    if y not in _CUT_CACHE:
        _CUT_CACHE[y] = canyon_cut(y)
    m = _CUT_CACHE[y]
    return 0 <= ix < m.shape[0] and 0 <= iz < m.shape[1] and bool(m[ix, iz])


def camp(bp):
    """The caravan camp at the canyon mouth: the approach marker (BUILDING §7, §15.9): two djinn blocks, a waystone,
    a striped tent, a campfire, fodder and the traders' barrels."""
    # sandy apron and the path from the camp into the canyon
    for x in range(-14, 40):
        for z in range(70, 96):
            ix, iz = x - MX0, z - MZ0
            inside = 0 <= ix < len(XS) and 0 <= iz < len(ZS) and R2[ix, iz] < 1
            if inside or math.hypot((x - 12) / 26.0, (z - 84) / 12.0) > 1:
                continue
            h = hash01(x, z, 141)
            bp.set(x, 0, z, "sand" if h < 0.55 else ("red_sand" if h < 0.9 else SS))
    for z in range(66, 96):
        px = 10
        for dx in range(-2, 3):
            if bp.get(px + dx, 0, z) is not None:
                bp.set(px + dx, 0, z, SMS if abs(dx) < 2 else CSS)
    # djinn blocks: two monoliths framing the way
    for bx in (-1, 18):
        for x in range(bx, bx + 5):
            for z in range(80, 85):
                for y in range(1, 9):
                    bp.set(x, y, z, CRS if y == 8 else (RS if hash3(x, y, z, 142) < 0.6 else SRS))
                bp.set(x, 9, z, stair("red_sandstone_stairs", "north" if z == 80 else "south" if z == 84 else
                                      "west" if x == bx else "east") if (z in (80, 84) or x in (bx, bx + 4))
                       else CRS)
    # the waystone
    for x in range(3, 6):
        for z in range(88, 91):
            bp.set(x, 0, z, CHSS if (x + z) % 2 else SMS)
    bp.set(4, 1, 89, MOD["waystone"])
    # the tent: an A-frame of striped cloth over a rug
    tx, tz = 24, 88
    for dx in range(0, 7):
        for k, (dz, y) in enumerate(((-3, 1), (-2, 2), (-1, 3), (0, 4), (1, 3), (2, 2), (3, 1))):
            bp.set(tx + dx, y, tz + dz, "orange_wool" if (dx + k) % 2 else "white_wool")
        for dz in range(-2, 3):
            bp.set(tx + dx, 0, tz + dz, "red_sand")
            bp.set(tx + dx, 1, tz + dz, "orange_carpet" if dz else "red_carpet")
    for y in range(1, 6):
        bp.set(tx - 1, y, tz, "spruce_fence")
        bp.set(tx + 7, y, tz, "spruce_fence")
    bp.bed(tx + 5, 1, tz - 1, "west", color="orange")
    bp.barrel(tx + 1, 1, tz + 2, "up", loot=LOOT + "necropolis_gallery")
    bp.set(tx + 1, 1, tz - 2, "crafting_table")
    bp.set(16, 1, 90, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((14, 92), (15, 92), (14, 93)):
        bp.set(x, 1, z, "hay_block[axis=y]")
    bp.barrel(32, 1, 86, "up")
    bp.barrel(32, 1, 87, "up")
    bp.barrel(32, 2, 86, "up")


# ------------------------------------------------------------------ quality pass: fixtures
def furnish_tombs(bp):
    """Hand-placed light and furniture where the first pass left long bare runs: lantern posts round the arena wall
    (the hung lamps sat 17 over the floor), offering tables and statuettes down the Gallery of Crowns, braziers on
    the hall's dais, lamps on the stair landings."""
    def free(x, y, z):
        return bp.get(x, y, z) == "minecraft:air" and bp.get(x, y - 1, z) not in (None, "minecraft:air")

    ax, az = ARENA
    for k in range(12):
        a = k * math.pi / 6
        x, z = ax + round(math.cos(a) * 14.2), az + round(math.sin(a) * 14.2)
        if abs(x) <= 2 or not free(x, F3, z):
            continue
        bp.set(x, F3, z, CRS)
        bp.set(x, F3 + 1, z, "sandstone_wall")
        bp.set(x, F3 + 2, z, "lantern[hanging=false,waterlogged=false]")
    # Gallery of Crowns: offering tables with candles and canopic pots between the windows
    for x in range(-34, 35, 6):
        if abs(x) in (0, 24) or not free(x, FC, -13):
            continue
        bp.set(x, FC, -13, "cut_red_sandstone_slab[type=top,waterlogged=false]")
        if bp.get(x, FC + 1, -13) == "minecraft:air":
            candles(bp, x, FC + 1, -13, 3)
        if free(x + 1, FC, -13):
            pot(bp, x + 1, FC, -13, "south")
    # the stair landings of the east climb and the west descent
    for (x, y, z) in ((22, F0 + 12, -33), (26, F0 + 24, -18), (17, F0, -18), (-19, F0, -30), (20, F2 - 8, -74),
                      (19, F3, -62), (-35, FC + 16, -33)):
        if free(x, y, z):
            bp.set(x, y, z, "sandstone_wall")
            if bp.get(x, y + 1, z) == "minecraft:air":
                bp.set(x, y + 1, z, "lantern[hanging=false,waterlogged=false]")


# ------------------------------------------------------------------ the whole site
def rock_necropolis(bp):
    solid = massif(bp)
    C = Carver(bp, solid)
    carve_all(C)
    C.wrap()
    plaza(bp)
    facade(bp, C)
    for kx in KINGS:
        king(bp, kx, broken=kx == BROKEN, defaced=kx == KINGS[-1])
    upper_storey(bp, C)
    hall(bp, C)
    sanctuary(bp)
    east_stair(bp)
    gallery_of_crowns(bp)
    level1(bp, C)
    level2(bp, C)
    level3(bp, C)
    arena(bp, C)
    vault(bp, C)
    well(bp)
    side_tomb(bp)
    canyon(bp)
    camp(bp)
    # quality pass: every carved floor lit to 8+ (themed fixtures first, then lanterns on chains / star lamps set in
    # the ceilings for the leftovers)
    furnish_tombs(bp)
    light_fill(bp, ground=0, lamp=STAR, hang="lantern[hanging=true,waterlogged=false]",
               chain="iron_chain[axis=y,waterlogged=false]")


# interior shots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("canyon", (canyon_point(46)[0], 1, canyon_point(46)[1]), (canyon_point(8)[0], 14, canyon_point(8)[1])),
    ("facade", (9, 1, 32), (0, 62, FZ)),
    ("hall", (0, F0, -18), (0, F0 + 8, -56)),
    ("gallery", (-72, F1, -36), (-72, F1 + 2, -78)),
    ("treasury", (15, F2, -95), (24, F2 + 2, -101)),
    ("arena", (0, F3, -48), (0, F3 + 6, -21)),
]


register(StructureDef(
    "rock_necropolis", "overworld", ["desert", "#minecraft:is_badlands"],
    [Piece("necropolis", rock_necropolis, views=VIEWS)],
    spacing=80, separation=32, adaptation="beard_box", processors="none", max_distance=116,
    spawns=[("minecraft:husk", 10, 1, 3), (MOB_CRAWLER, 5, 1, 2)],
    title_fr="Nécropole des rois", title_en="Necropolis of Kings"))
