"""The Great Aqueduct (Le Grand Aqueduc): a Roman bridge-aqueduct of golden limestone, three tiers of arches (12, 8 and
4 blocks wide) and 200 blocks long, striding across a river valley from one ridge to the other, the water channel
on top, a ruined breach in the middle and the castellum (the distribution tower) on the east ridge. Colossal tier
(tools/BUILDING.md §1, §12 concept 4, §15).

Silhouette (one noun phrase, §15.1): a long three-storey comb of arches bridging a valley, broken once in the
middle, ending against a tall square water tower with a red pyramid roof.

Layout, ground y = 0 (the valley floor), x east, z south. The valley runs north-south; its floor is flat for |x| < ~64
(a river meanders through it under the arch at x 3..14) and rock-faced slopes climb to the ridges (the east one a
plateau at y 48 under the castellum, the west one a crest over the spring house). The arcade follows z = 0: tier 1
(|z| <= 10, deck top y 21, walk feet 22), tier 2 (|z| <= 6, deck top y 40, the maintenance gallery in its spandrel
band, feet 34), tier 3 (|z| <= 5) carrying the channel (water at |z| 2..4 on the north side) and the towpath (feet 49).
Bays: 18 on tier 1, 12 on tier 2, 6 on tier 3 (they line up every 36 blocks); the arches stop where the ground rises
into them, so each tier meets the slopes further up, the way a real valley aqueduct does.

The route (main path, ~600 path blocks):
  * the approach: a road comes up the valley from the south past the builders' old quarry camp (a satellite, §15.9),
    crosses the river on a slab bridge and runs west along the foot of the arcade to the entrance waystone at the
    foot of the west ridge;
  * the ridge road: switchbacks up the west slope (the whole aqueduct and the castellum in view, §7 reveal) to the
    spring house terrace (site of grace) where the channel leaves the hill: the intake hall with its sluice, the
    nymph's niche and a waterfall with a grotto behind it (secret);
  * the towpath east along the full channel, 49 above the valley, to the west sluice gate and the breach (railed,
    vista); the west stair tower goes down to the tier-1 deck (its gallery door leads to the west tool room, its
    ground door is a one-way iron door to the entrance waystone: shortcut);
  * the breach: the tier-1 deck in the open, rubble and broken stumps, the sluice-keeper's house built of fallen
    stones (two storeys, garden, crane), a hatch under the rubble into a hollow pier (secret), and a rubble stair up
    to the broken mouth of the maintenance gallery;
  * the gallery inside tier 2: a corridor with rooms (store, bunks, workshop, the lamp room with the hub site of grace
    beside the east stair tower, the crawlers' room, the archive, the gauge room) to the valve hall inside the east
    ridge. The east stair tower links the valley (one-way iron door: shortcut), the deck, the gallery and the
    towpath; the towpath east and the gallery are two parallel ways to the castellum (loop);
  * the castellum: the distribution hall (the basin, copper pipes), the keepers' hall and the belfry loggia (vista,
    bell), climbed by a newel stair turret from the valve hall under it;
  * from the valve hall a corridor and a second newel stair go down to the cistern antechamber (site of grace), a
    narrow passage (compression) and the mist into the great cistern: the boss arena (radius 17, a dome on a ring of
    columns, water in its gutters, light from a grate in the valve hall). The vault behind sealed bars on the north
    side; the drain tunnel west ends at an iron door that opens from inside only, on the slope under the arcade
    (the last shortcut, back to the valley road).
Loot gradient (§15.6): camp, spring house, west tool room tier 1; keeper's house 1-2; gallery rooms, valve hall,
castellum 2; belfry 2-3 (optional climb); the grotto and the hollow pier 2-3 (secrets); the vault 3.
Height budget: the castellum finial stands ~100 above the valley floor; the ridges bring their own height, so it fits
in any plains or savanna valley.
"""
import math

import numpy as np

from ..arch import boulder, oak, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3, is_air
from ..parts import LOOT, MOD

# placeholder guardian until the aqueduct gets its own: the warden of the drowned citadel rises in the cistern
BOSS = "brasshaven:drowned_warden"
MOB_KNIGHT = "brasshaven:skeleton_knight"
MOB_CRAWLER = "brasshaven:crypt_crawler"
MOB_GARGOYLE = "brasshaven:gargoyle"
MOB_SKELETON = "minecraft:skeleton"

# ------------------------------------------------------------------ dimensions
AX0, AX1, AZ0, AZ1 = -124, 124, -64, 64
F_DECK, F_GAL, F_TOW = 22, 34, 49        # feet: tier-1 deck, maintenance gallery, towpath
TOP1, TOP2, TOW = 21, 40, 48             # top blocks: tier-1 deck, tier-2 deck, towpath floor
CH_Z = (-4, -2)                          # channel water (north side of tier 3)
TP_Z = (-1, 4)                           # towpath
COR_Z = (3, 5)                           # gallery corridor (rooms on z -5..1, partition z 2)
SLUICE_W, SLUICE_E = -47, 5              # sluice gates either side of the breach
T1C, T2C = (-55, 12), (35, 12)           # stair towers (centres): walls +-5
CAS = (93, -11, 115, 11)                 # castellum outer walls x0, z0, x1, z1
CAS_F = (49, 61, 73)                     # castellum storeys (feet)
TUR = (104, -17)                         # castellum stair turret centre
VALVE = (92, -9, 114, 9)                 # valve hall air box x0, z0, x1, z1 (feet F_GAL, 10 high)
AC, AF, AR = (102, 0), 13, 17.0          # cistern arena centre, feet, floor radius
BN = (108, 35)                           # boss newel stair centre (feet 13 -> 34)

TIERS = (
    dict(w=10, lo=-4, hi=TOP1, bay=18, off=3, span=12, ys=12.0, r=6.0, x0=-84, x1=84),
    dict(w=6, lo=22, hi=TOP2, bay=12, off=2, span=8, ys=28.0, r=4.0, x0=-96, x1=92),
    dict(w=5, lo=41, hi=TOW, bay=6, off=1, span=4, ys=42.5, r=2.0, x0=-100, x1=92),
)

SS, CUT, SMO, CHIS = "sandstone", "cut_sandstone", "smooth_sandstone", "chiseled_sandstone"
SS_ST, SMO_ST = "sandstone_stairs", "smooth_sandstone_stairs"
SMO_SL, CUT_SL = "smooth_sandstone_slab", "cut_sandstone_slab"
SS_W = "sandstone_wall"
MUD, PMUD, MUD_W = "mud_bricks", "packed_mud", "mud_brick_wall"
TILE_ST = "brick_stairs"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
WATER = "water"
CORN_CCW = ((1, -1), (-1, -1), (-1, 1), (1, 1))   # NE, NW, SW, SE (x sign, z sign)
DIRV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}


# ------------------------------------------------------------------ noise (vectorised, as in kneeling_gate)
def _vh(ix, iz, seed):
    n = ((ix * 73856093) ^ (iz * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, scale, seed):
    fx, fz = np.asarray(x, float) / scale, np.asarray(z, float) / scale
    ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _vh(ix, iz, seed), _vh(ix + 1, iz, seed)
    c, d = _vh(ix, iz + 1, seed), _vh(ix + 1, iz + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def fbm(x, z, scale, seed):
    return 0.6 * vnoise(x, z, scale, seed) + 0.3 * vnoise(x, z, scale / 2.3, seed + 7) + \
        0.1 * vnoise(x, z, scale / 5.1, seed + 13)


XS = np.arange(AX0, AX1 + 1)
ZS = np.arange(AZ0, AZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")


def river_x(z):
    return 9 + 7 * math.sin(z / 26.0)


# ------------------------------------------------------------------ paths (polylines with feet heights)
# the ridge road: from the entrance waystone up the west slope to the spring house terrace (feet 1 -> 49)
HILL = [(-60, 22), (-66, 34), (-76, 40), (-80, 28), (-86, 40), (-92, 30), (-94, 18)]
ROAD_MAIN = [(-60, 22), (-30, 21), (0, 21), (30, 21), (62, 22)]
ROAD_SOUTH = [(54, 64), (46, 50), (38, 36), (31, 22)]


def _poly_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def poly_cells(pts, half, f0=None, f1=None):
    """{(x, z): (feet, dx, dz)} for the cells within ``half`` of the polyline; feet interpolated f0 -> f1 along it."""
    L = _poly_len(pts)
    out = {}
    acc = 0.0
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 3))
        ux, uz = (bx - ax) / seg, (bz - az) / seg
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            s = acc + seg * t
            feet = None if f0 is None else f0 + (f1 - f0) * s / L
            r = int(math.ceil(half)) + 1
            for x in range(int(px) - r, int(px) + r + 2):
                for z in range(int(pz) - r, int(pz) + r + 2):
                    if math.hypot(x - px, z - pz) <= half:
                        old = out.get((x, z))
                        if old is None or (feet is not None and feet > old[0]):
                            out[(x, z)] = (feet, ux, uz)
        acc += seg
    return out


HILL_CELLS = poly_cells(HILL, 1.6, 1.0, 49.0)


# ------------------------------------------------------------------ terrain: the valley and its ridges
def heights():
    ax = np.abs(GX).astype(float)
    west = GX < 0
    n1 = fbm(GX, GZ, 23.0, 11)
    n2 = fbm(GX, GZ, 6.0, 12)
    nz = fbm(np.where(west, 0, 300) + 0 * GX, GZ, 21.0, 14)
    foot = 64 + 8 * nz
    t = np.clip((ax - foot) / (99 - foot), 0, 1)
    h = 48.0 * t * t * (3 - 2 * t)
    mid = (t > 0) & (t < 1)
    bell = np.sin(np.pi * t)
    h += mid * (n2 - 0.5) * 7 * bell
    h -= mid * 5 * np.clip(np.sin(GZ / 7.0 + 6 * n1) - 0.55, 0, None) * bell
    h += west * 12 * np.clip(1 - np.abs(ax - 109) / 11, 0, 1)        # the crest over the spring house
    h -= np.clip(ax - 116, 0, None) * 1.8                             # outer fall toward the site edge
    h *= 1 - 0.6 * np.clip((np.abs(GZ) - 34) / 30, 0, 1)              # lower toward north and south
    # the castellum's plateau (exactly 48 inside, blended over 10 blocks), the mound over the spring house
    d = np.hypot(np.clip(np.maximum(90 - GX, GX - 116), 0, None), np.clip(np.abs(GZ) - 22, 0, None))
    w = np.clip(1 - d / 10.0, 0, 1)
    w = w * w * (3 - 2 * w)
    h = h + (48.0 - h) * w
    d = np.hypot(np.clip(np.maximum(-115 - GX, GX + 101), 0, None), np.clip(np.abs(GZ) - 10, 0, None))
    h = np.maximum(h, np.where(GX <= -101, 60.0 - 1.1 * d - 3 * (n2 - 0.5) * (d > 0), -99.0))
    d = np.hypot(np.clip(np.maximum(-99 - GX, GX + 86), 0, None), np.clip(np.maximum(-8 - GZ, GZ - 17), 0, None))
    h = np.maximum(h, 42.0 - 1.4 * d)
    G = np.floor(h).astype(np.int32)
    # the ridge road: a terrace cut into the slope, blended into the ground round it
    tgt = np.full(G.shape, -999, np.int32)
    for (x, z), (feet, _, _) in HILL_CELLS.items():
        if AX0 <= x <= AX1 and AZ0 <= z <= AZ1:
            tgt[x - AX0, z - AZ0] = max(tgt[x - AX0, z - AZ0], int(round(feet)) - 1)
    on = tgt > -999
    Gf = G.astype(float)
    if on.any():
        idx = np.argwhere(on)
        near = np.full(G.shape, 99.0)
        val = np.zeros(G.shape)
        for i, k in idx.tolist():
            i0, i1, k0, k1 = max(0, i - 6), min(G.shape[0], i + 7), max(0, k - 6), min(G.shape[1], k + 7)
            d = np.hypot(GX[i0:i1, k0:k1] - GX[i, k], GZ[i0:i1, k0:k1] - GZ[i, k])
            better = d < near[i0:i1, k0:k1]
            near[i0:i1, k0:k1] = np.where(better, d, near[i0:i1, k0:k1])
            val[i0:i1, k0:k1] = np.where(better, tgt[i, k], val[i0:i1, k0:k1])
        w = np.clip(1 - (near - 1.0) / 5.0, 0, 1)
        Gf = Gf + (val - Gf) * w
        Gf = np.where(on, tgt, Gf)
    G = np.round(Gf).astype(np.int32)
    G = np.maximum(G, 0)
    return G


G_ = None


def gtop(x, z):
    """Top block height of the ground at (x, z) (0 on the valley floor)."""
    if AX0 <= x <= AX1 and AZ0 <= z <= AZ1:
        return int(G_[x - AX0, z - AZ0])
    return 0


def rock_block(x, y, z, jit):
    h = hash3(x, y, z, 7)
    s = y + int(4 * jit)
    band = ("stone", "andesite", "stone", "diorite", "stone", "tuff", "andesite", "stone")
    if h < 0.08:
        return "cobblestone"
    return band[(s // 4) % len(band)]


def terrain(bp):
    G = G_
    jit = fbm(GX, GZ, 9.0, 31)
    nx, nz = G.shape
    edge = np.zeros(G.shape, bool)
    edge[:2, :] = edge[-2:, :] = True
    edge[:, :2] = edge[:, -2:] = True
    pad = np.pad(G, 1, mode="edge")
    mn = np.minimum.reduce([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
    for i in range(nx):
        x = int(XS[i])
        for k in range(nz):
            z = int(ZS[k])
            g = int(G[i, k])
            low = int(mn[i, k])
            steep = g - low >= 2
            y0 = min(g, low) - 2
            if edge[i, k]:
                y0 = -3                      # close the ridges' sides at the edge of the site
            elif g <= 14:
                y0 = min(y0, -1)             # solid foothills: no hollow pockets where the slopes meet the floor
            j = float(jit[i, k])
            for y in range(max(-3, y0), g + 1):
                if y == g:
                    if steep:
                        spec = rock_block(x, y, z, j)
                    else:
                        h = hash01(x, z, 41)
                        spec = ("grass_block[snowy=false]" if h < 0.86 else
                                "coarse_dirt" if h < 0.95 else "rooted_dirt")
                elif y >= g - 2 and not steep and g > 0:
                    spec = "dirt"
                elif g == 0:
                    spec = "dirt"
                else:
                    spec = rock_block(x, y, z, j)
                bp.set(x, y, z, spec)


def valley(bp):
    """River, banks, the slab bridge, roads and their lamps on the valley floor."""
    for z in range(AZ0, AZ1 + 1):
        xr = river_x(z)
        for x in range(int(xr) - 7, int(xr) + 8):
            if gtop(x, z) != 0:
                continue
            d = abs(x - xr)
            if d <= 3.2:
                bp.set(x, 0, z, "air")
                bp.set(x, -1, z, WATER)
                bp.set(x, -2, z, WATER)
                bp.set(x, -3, z, "gravel" if hash01(x, z, 43) < 0.6 else "clay")
            elif d <= 4.6:
                h = hash01(x, z, 44)
                bp.set(x, 0, z, "coarse_dirt" if h < 0.4 else ("mud" if h < 0.55 else "grass_block[snowy=false]"))
                if h > 0.8:
                    bp.set(x, 1, z, "sugar_cane")
                    bp.set(x, 2, z, "sugar_cane")
    # roads
    for pts in (ROAD_MAIN, ROAD_SOUTH):
        for (x, z), _ in poly_cells(pts, 1.5).items():
            if not (AX0 <= x <= AX1 and AZ0 <= z <= AZ1) or gtop(x, z) != 0:
                continue
            if abs(x - river_x(z)) <= 4.6:
                continue
            h = hash01(x, z, 51)
            bp.set(x, 0, z, "dirt_path" if h < 0.6 else ("cobblestone" if h < 0.8 else "coarse_dirt"))
    # the slab bridge where the main road crosses the river
    zc = 21
    xr = river_x(zc)
    for x in range(int(xr) - 5, int(xr) + 6):
        for z in range(zc - 2, zc + 3):
            bp.set(x, 0, z, CUT if abs(z - zc) < 2 else SMO)
            if abs(z - zc) == 2:
                bp.set(x, 1, z, SS_W)
        if abs(x - xr) <= 3.2 and x % 3 == 0:
            for y in (-3, -2, -1):
                for z in (zc - 2, zc + 2):
                    bp.set(x, y, z, SS)
    for x in (int(xr) - 5, int(xr) + 5):
        for z in (zc - 2, zc + 2):
            bp.set(x, 1, z, SS)
            bp.set(x, 2, z, LANT)
    # lamp posts along the main road (south side), every ~16 blocks
    for x in range(-52, 64, 16):
        z = 24
        if gtop(x, z) or abs(x - river_x(z)) < 6:
            continue
        bp.set(x, 0, z, "cobblestone")
        bp.set(x, 1, z, MUD_W)
        bp.set(x, 2, z, "spruce_fence")
        bp.set(x, 3, z, LANT)


# ------------------------------------------------------------------ the arcade
def arch_top(T, x):
    """Intrados height (exclusive) of the arch over column x, or None over a pier."""
    xi = (x - T["off"]) % T["bay"]
    if xi >= T["span"]:
        return None
    xc = x - xi + (T["span"] - 1) / 2.0
    u = abs(x - xc)
    return T["ys"] + math.sqrt(max(0.0, T["r"] ** 2 - u * u))


def is_open(T, x, y):
    t = arch_top(T, x)
    return t is not None and y < t and y >= max(T["lo"], 1)


def ruin_top(x, z):
    """Highest masonry block left in column (x, z) by the breach (99 = intact)."""
    if x < -46 or x > 5:
        return 99
    j = int(hash01(x // 2, z // 4, 401) * 3) - 1
    if x <= -40:
        base = 49 - (x + 46) * 1.4                      # tier 3 broken down in steps
    elif x <= -34:
        base = 40 - (x + 40) * 3                        # tier 2 broken down to the deck
    elif x <= -10:
        base = TOP1
        if -14 <= x <= -11 and z <= 1:                  # the stump of a tier-2 pier
            base = TOP1 + 3 + int(5 * hash01(x, z, 402))
    elif x <= -5:
        base = TOP1 + 1 + (x + 9) * 4
    else:
        base = 41 + (x + 4)                             # tier 3 broken from the gallery's end
    if base <= TOP1 + 0.5:
        # the deck stays whole, its parapet broken here and there
        return TOP1 + (1 if hash01(x, z, 403) < 0.45 and abs(z) == 10 else 0)
    return int(base) + j


def ashlar(x, y, z):
    """Golden limestone with a gradient: dark mud-brick footings, warm sandstone body, paler crown; calcite drips
    on the north (channel) side where the specus leaks."""
    h = hash3(x, y, z, 21)
    f = y / 49.0 + (hash01(x // 3, z // 3 + y * 7, 22) - 0.5) * 0.10
    if f < 0.07:
        return PMUD if h < 0.45 else MUD
    if f < 0.15:
        return MUD if h < 0.3 else SS
    if f < 0.7:
        return SS if h < 0.62 else (CUT if h < 0.9 else SMO)
    return SS if h < 0.4 else (CUT if h < 0.75 else SMO)


def drip(x, y, z):
    """North faces under the channel: calcite streaks from the leaking specus."""
    if z >= 0:
        return False
    n = hash01(x, 0, 31)
    if n > 0.22:
        return False
    length = 4 + int(14 * hash01(x, 1, 31))
    return y >= TOW - length


def arcade(bp):
    for x in range(-100, 93):
        for z in range(-12, 13):
            g = gtop(x, z)
            for ti, T in enumerate(TIERS):
                w = T["w"]
                if abs(z) > w or not T["x0"] <= x <= T["x1"]:
                    continue
                top = arch_top(T, x)
                hi = T["hi"] + (1 if ti == 2 and z == -w else 0)
                for y in range(max(T["lo"], g - 3), hi + 1):
                    if y > ruin_top(x, z):
                        break
                    if top is not None and y < top and (ti == 0 and g == 0 or top - g >= 4):
                        continue                                     # the arch opening (or ground under it)
                    spec = ashlar(x, y, z)
                    # voussoirs round the intrados, the keystone at the crown
                    ys = T["ys"]
                    xi = (x - T["off"]) % T["bay"]
                    if y >= int(ys) and (is_open(T, x - 1, y) or is_open(T, x + 1, y) or is_open(T, x, y - 1)
                                         or is_open(T, x - 1, y - 1) or is_open(T, x + 1, y - 1)):
                        if top is not None and is_open(T, x, y - 1) and xi in (T["span"] // 2 - 1, T["span"] // 2):
                            spec = CHIS
                        else:
                            a = math.atan2(y - ys, 0.5 + xi - T["span"] / 2.0)
                            spec = CUT if int(a / (math.pi / 9)) % 2 == 0 else SMO
                    elif top is None and y == int(ys) - 1 and ti < 2:
                        spec = SMO                                   # impost course on the piers
                    elif abs(z) == w and ti == 1 and y == F_GAL - 1:
                        spec = CUT                                   # string course at the gallery floor
                    elif abs(z) == w and drip(x, y, z) and y > g:
                        spec = "calcite" if hash3(x, y, z, 32) < 0.7 else SMO
                    bp.set(x, y, z, spec)
            # cutwaters on the valley piers of tier 1, imposts proud of the piers
            T = TIERS[0]
            if abs(z) in (11, 12) and arch_top(T, x) is None and T["x0"] <= x <= T["x1"]:
                xi = (x - T["off"]) % T["bay"]
                pc = x - xi + T["span"] + 2.5
                d = abs(z) - 10
                if g == 0 and abs(x - pc) <= 2.5 - d:
                    for y in range(-3, 8):
                        bp.set(x, y, z, ashlar(x, min(y, 2), z))
                    bp.set(x, 8, z, stair(SS_ST, "south" if z < 0 else "north"))
    # imposts: a slab course proud of the pier faces at the springing of tiers 1 and 2
    for ti in (0, 1):
        T = TIERS[ti]
        y = int(T["ys"]) - 1
        for x in range(T["x0"], T["x1"] + 1):
            if arch_top(T, x) is not None:
                continue
            for s in (-1, 1):
                z = s * (T["w"] + 1)
                if y > gtop(x, z) and y <= ruin_top(x, s * T["w"]) and is_air(bp, x, y, z) and \
                        bp.get(x, y, s * T["w"]) is not None:
                    bp.set(x, y, z, SMO_SL + "[type=top,waterlogged=false]")
    # cornices at the decks of tiers 1 and 2; the deck parapet
    for x in range(-96, 93):
        for s in (-1, 1):
            if TIERS[0]["x0"] <= x <= TIERS[0]["x1"] and gtop(x, s * 11) < TOP1 and \
                    bp.get(x, TOP1, s * 10) is not None:
                bp.set(x, TOP1, s * 11, stair(SMO_ST, "south" if s < 0 else "north", "top"))
            if bp.get(x, TOP2, s * 6) is not None and gtop(x, s * 7) < TOP2 and ruin_top(x, s * 6) >= TOP2:
                bp.set(x, TOP2, s * 7, stair(SMO_ST, "south" if s < 0 else "north", "top"))
            if TIERS[0]["x0"] <= x <= TIERS[0]["x1"] and gtop(x, s * 10) < TOP1 and \
                    bp.get(x, TOP1, s * 10) is not None and ruin_top(x, s * 10) >= TOP1 + 1:
                bp.set(x, TOP1 + 1, s * 10, SS_W)


def channel(bp):
    """The specus and the towpath on tier 3: water west of the breach, a hand of water east of it."""
    for x in range(-100, 93):
        for z in range(CH_Z[0] - 1, TP_Z[1] + 2):
            if ruin_top(x, z) < TOW or bp.get(x, TOW, z) is None:
                continue
            if CH_Z[0] <= z <= CH_Z[1]:
                bp.set(x, TOW - 2, z, "terracotta")
                if x < SLUICE_W:
                    bp.set(x, TOW - 1, z, WATER)
                    bp.set(x, TOW, z, WATER)
                elif x > SLUICE_E:
                    bp.set(x, TOW - 1, z, WATER)
                    bp.set(x, TOW, z, "air")
                else:
                    bp.set(x, TOW - 1, z, "air")
                    bp.set(x, TOW, z, "air")
            elif TP_Z[0] <= z <= TP_Z[1]:
                h = hash01(x, z, 61)
                bp.set(x, TOW, z, CUT if (x + z) % 5 == 0 else (SMO if h < 0.6 else SS))
                for y in range(F_TOW, F_TOW + 4):
                    bp.set(x, y, z, "air")
            elif z == TP_Z[1] + 1:
                if gtop(x, z) < F_TOW:
                    bp.set(x, F_TOW, z, SS_W)
            elif z == CH_Z[0] - 1:
                bp.set(x, F_TOW, z, CUT)
        # bronze mile marks on the parapet every 36 blocks
        if x % 36 == 0 and ruin_top(x, 5) >= F_TOW and bp.get(x, F_TOW, 5) == "minecraft:sandstone_wall":
            bp.set(x, F_TOW, 5, SS)
            bp.set(x, F_TOW + 1, 5, LANT)
    # sluice gates and rails at the breach
    for xg, xr in ((SLUICE_W, SLUICE_W + 1), (SLUICE_E, SLUICE_E - 1)):
        for z in range(CH_Z[0], CH_Z[1] + 1):
            for y in (TOW - 1, TOW, TOW + 1):
                bp.set(xg, y, z, "spruce_planks")
            bp.set(xg, TOW + 2, z, "spruce_slab[type=bottom,waterlogged=false]")
        for y in range(TOW + 1, TOW + 4):
            bp.set(xg, y, CH_Z[0] - 1, "stripped_spruce_log[axis=y]")
            bp.set(xg, y, CH_Z[1] + 1, "stripped_spruce_log[axis=y]")
        for z in range(CH_Z[0] - 1, CH_Z[1] + 2):
            bp.set(xg, TOW + 4, z, "stripped_spruce_log[axis=z]")
        bp.set(xg, TOW + 3, CH_Z[0], CHAIN)
        bp.set(xg, TOW + 3, CH_Z[1], CHAIN)
        for z in range(TP_Z[0] + 1, TP_Z[1] + 1):
            bp.set(xr, F_TOW, z, SS_W)


# ------------------------------------------------------------------ helpers for rooms
def ensure(bp, x, y, z, spec):
    if bp.get(x, y, z) is None:
        bp.set(x, y, z, spec)


def shell_box(bp, x0, y0, z0, x1, y1, z1, wall=SS, floor=None):
    """Air x0..x1, y0..y1, z0..z1 inside a masonry shell that only fills unset cells (rooms in the ridges)."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, y1 + 2):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and y0 <= y <= y1
                if inside:
                    bp.set(x, y, z, "air")
                elif y == y0 - 1 and x0 <= x <= x1 and z0 <= z <= z1 and floor:
                    bp.set(x, y, z, floor(x, z) if callable(floor) else floor)
                else:
                    ensure(bp, x, y, z, wall(x, y, z) if callable(wall) else wall)


def floor_pave(x, z):
    h = hash01(x, z, 71)
    return SMO if h < 0.5 else (CUT if h < 0.85 else SS)


def solid_roof(bp, x0, z0, x1, z1, y, stairs=TILE_ST, fill="bricks"):
    """A pyramid roof of tile stairs over a solid core (no sealed void under it); returns the apex y."""
    yy = y
    while x0 <= x1 and z0 <= z1:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x0 == x1 or z0 == z1:
                    bp.set(x, yy, z, fill)
                elif x in (x0, x1) or z in (z0, z1):
                    fc = "east" if x == x0 else "west" if x == x1 else "south" if z == z0 else "north"
                    bp.set(x, yy, z, stair(stairs, fc))
                else:
                    bp.set(x, yy, z, fill)
        if x0 == x1 or z0 == z1:
            break
        x0, x1, z0, z1, yy = x0 + 1, x1 - 1, z0 + 1, z1 - 1, yy + 1
    return yy


def hang(bp, x, y, z, lamp=LANT_H, reach=10):
    """A lamp on a chain from the first solid block above (x, y, z)."""
    top = y + 1
    while top < y + reach and is_air(bp, x, top, z):
        top += 1
    if is_air(bp, x, top, z):
        return
    for yy in range(y + 1, top):
        bp.set(x, yy, z, CHAIN)
    bp.set(x, y, z, lamp)


# ------------------------------------------------------------------ the maintenance gallery
ROOMS = [(-58, -50, "tools"), (-4, 6, "store"), (8, 18, "bunks"), (20, 28, "workshop"), (30, 44, "lamp"),
         (46, 56, "crawlers"), (58, 70, "archive"), (72, 82, "gauges")]


def gallery(bp):
    f = F_GAL
    for xa, xb in ((-58, -39), (-6, 90)):
        for x in range(xa, xb + 1):
            for z in range(COR_Z[0], COR_Z[1] + 1):
                bp.set(x, f - 1, z, floor_pave(x, z) if (x + z) % 2 else CUT)
                for y in range(f, f + 4):
                    bp.set(x, y, z, "air")
                if ruin_top(x, z) >= f + 4:
                    ensure(bp, x, f + 4, z, SS)
            for y in range(f - 1, f + 5):
                if y <= ruin_top(x, 2):
                    ensure(bp, x, y, 2, SS)
                if y <= ruin_top(x, 6):
                    ensure(bp, x, y, 6, SS)
            # lamps along the corridor, slit windows over the arch crowns
            if x % 8 == 4 and ruin_top(x, 4) >= f + 4:
                hang(bp, x, f + 3, 4)
            if (x - 2) % 12 == 5 and ruin_top(x, 6) >= f + 2:
                bp.set(x, f + 1, 6, "iron_bars")
    # the broken west end: a 1-high stub of wall as a rail, a view into the breach
    for z in range(COR_Z[0], COR_Z[1] + 1):
        bp.set(-38, f, z, SS_W)
        bp.set(-38, f - 1, z, SS)
    for (x0, x1, kind) in ROOMS:
        for x in range(x0, x1 + 1):
            for z in range(-5, 2):
                bp.set(x, f - 1, z, floor_pave(x, z))
                for y in range(f, f + 4):
                    bp.set(x, y, z, "air")
                ensure(bp, x, f + 4, z, SS)
            for y in range(f - 1, f + 5):
                ensure(bp, x, y, -6, SS)
        for x in (x0 - 1, x1 + 1):
            for z in range(-6, 3):
                for y in range(f - 1, f + 5):
                    bp.set(x, y, z, CUT if y in (f - 1, f + 4) else SS)
        # doorway from the corridor (2 wide, 3 high), windows north
        dx = (x0 + x1) // 2
        for x in (dx, dx + 1):
            for y in range(f, f + 3):
                bp.set(x, y, 2, "air")
        for x in range(x0 + 2, x1 - 1, 4):
            bp.set(x, f + 1, -6, "iron_bars")
            bp.set(x, f + 2, -6, "iron_bars")
        furnish_room(bp, x0, x1, kind)


def furnish_room(bp, x0, x1, kind):
    f = F_GAL
    cx = (x0 + x1) // 2
    hang(bp, cx, f + 3, -2)
    if kind == "tools":
        bp.chest(x0, f, -5, "south", loot=LOOT + "ga_spring")
        bp.barrel(x0, f, -4)
        bp.barrel(x0, f + 1, -4)
        bp.set(x0 + 2, f, -5, "grindstone[face=floor,facing=south]")
        bp.set(x1, f, -5, "smithing_table")
        bp.spawner(x1 - 1, f, -3, MOB_CRAWLER)
    elif kind == "store":
        for x in range(x0, x1 + 1, 2):
            bp.barrel(x, f, -5)
            if x % 4 == 0:
                bp.barrel(x, f + 1, -5)
        bp.chest(x1, f, -1, "west", loot=LOOT + "ga_gallery")
        bp.set(x0, f, -1, "composter[level=0]")
    elif kind == "bunks":
        for x in range(x0, x1, 3):
            bp.bed(x, f, -5, "south", color="brown")
        bp.chest(x1, f, -5, "west", loot=LOOT + "ga_gallery")
        bp.set(x1, f, -1, "crafting_table")
        bp.set(cx, f, -1, "candle[candles=3,lit=true,waterlogged=false]")
    elif kind == "workshop":
        bp.set(x0, f, -5, "anvil[facing=east]")
        bp.set(x0 + 1, f, -5, "blast_furnace[facing=south,lit=false]")
        bp.set(x0 + 2, f, -5, "brasshaven:gear_panel")
        bp.set(x0 + 3, f, -5, "brasshaven:copper_pipes")
        bp.set(x1, f, -5, "stonecutter[facing=south]")
        bp.chest(x1, f, -3, "west", loot=LOOT + "ga_gallery")
        for x in range(x0 + 1, x1):
            bp.set(x, f, -2, "spruce_slab[type=top,waterlogged=false]") if x % 3 else None
    elif kind == "lamp":
        # the hub: site of grace among the keepers' lamps
        bp.set(x0 + 2, f, -3, MOD["waystone"])
        for x in range(x0 + 6, x1 - 1, 2):
            bp.set(x, f, -5, "spruce_slab[type=top,waterlogged=false]")
            bp.set(x, f + 1, -5, LANT)
        bp.chest(x1, f, -5, "west", loot=LOOT + "ga_gallery")
        bp.set(x0, f, -5, "lectern[facing=east,has_book=false,powered=false]")
    elif kind == "crawlers":
        bp.spawner(cx, f, -3, MOB_CRAWLER)
        bp.chest(x1, f, -5, "west", loot=LOOT + "ga_gallery")
        for x in range(x0, x1 + 1, 3):
            bp.set(x, f, -5, "cobweb")
    elif kind == "archive":
        for x in range(x0, x1 + 1):
            if x != cx:
                bp.set(x, f, -5, "bookshelf")
                bp.set(x, f + 1, -5, "bookshelf")
        bp.set(cx, f, -4, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(cx, f, -1, "cartography_table")
        bp.chest(x1, f, -1, "west", loot=LOOT + "ga_castellum")
    elif kind == "gauges":
        for x in range(x0, x1 + 1, 2):
            bp.set(x, f, -5, "brasshaven:pressure_gauge")
            bp.set(x, f + 1, -5, "brasshaven:copper_pipes")
            bp.set(x, f + 2, -5, "brasshaven:copper_pipes")
        bp.spawner(cx, f, -2, MOB_KNIGHT)
        bp.chest(x0, f, -1, "east", loot=LOOT + "ga_valve")


# ------------------------------------------------------------------ newel stairs and the stair towers
def spiral(cx, cz, f0, k_end, c0, corners=CORN_CCW):
    """Square newel stair round a 3 x 3 core: (x, z, feet, stair facing or None) per cell and the landings
    {k: (sx, sz, feet)}: 3 x 3 landings at the corners, flights of three steps (3 wide) on the sides, +3 per side."""
    cells, land = [], {}
    f = f0
    for k in range(k_end + 1):
        sx, sz = corners[(c0 + k) % 4]
        for d1 in (2, 3, 4):
            for d2 in (2, 3, 4):
                cells.append((cx + sx * d1, cz + sz * d2, f, None))
        land[k] = (sx, sz, f)
        if k == k_end:
            break
        nx, nz = corners[(c0 + k + 1) % 4]
        if sx != nx:
            d = 1 if nx > sx else -1
            for i, du in enumerate((-d, 0, d)):
                for dv in (2, 3, 4):
                    cells.append((cx + du, cz + sz * dv, f + i + 1, "east" if d > 0 else "west"))
        else:
            d = 1 if nz > sz else -1
            for i, dv in enumerate((-d, 0, d)):
                for du in (2, 3, 4):
                    cells.append((cx + sx * du, cz + dv, f + i + 1, "south" if d > 0 else "north"))
        f += 3
    return cells, land


def build_newel(bp, cx, cz, f0, k_end, c0, y_top, wall=None, lamps=True, doors=()):
    """Walls (+-5), air and the core of a newel stair well from f0 - 1 up to the ceiling y_top; ``doors`` are the
    landing indices whose corner gets no lamp."""
    wall = wall or (lambda x, y, z: ashlar(x, y, z))
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            edge = abs(x - cx) == 5 or abs(z - cz) == 5
            core = abs(x - cx) <= 1 and abs(z - cz) <= 1
            for y in range(f0 - 1, y_top + 1):
                if edge or y in (f0 - 1, y_top):
                    corner = abs(x - cx) == 5 and abs(z - cz) == 5
                    bp.set(x, y, z, CUT if corner and y % 2 else wall(x, y, z))
                elif core:
                    bp.set(x, y, z, CHIS if y % 6 == 0 else SMO)
                else:
                    bp.set(x, y, z, "air")
    cells, land = spiral(cx, cz, f0, k_end, c0)
    for (x, z, f, fc) in cells:
        bp.set(x, f - 1, z, stair(SS_ST, fc) if fc else (SMO if (x + z) % 2 else CUT))
        if f - f0 <= 6:
            for y in range(f0 - 1, f - 1):           # solid under the first flights: no low nook at the foot
                bp.set(x, y, z, wall(x, y, z))
    for k, (sx, sz, f) in land.items():
        if lamps and k % 2 == 1 and k not in doors and f + 1 < y_top:
            bp.set(cx + sx * 4, f, cz + sz * 4, LANT)
    return land


def stair_tower(bp, cx, cz, east_hub):
    """A stair tower on the south face of the arcade: newel from the valley (feet 1) to the towpath (feet 49).
    Doors: ground (k1, south; iron, opens from inside), deck (k7, east), gallery (k11, north), towpath (k16,
    north). A tile pyramid roof over a cornice; slit windows."""
    land = build_newel(bp, cx, cz, 1, 16, 1, F_TOW + 4, doors=(1, 7, 11, 16))
    # slit windows on the free faces
    for y in range(6, F_TOW, 6):
        for (x, z) in ((cx, cz + 5), (cx - 5, cz + 2), (cx + 5, cz + 2)):
            if y > TOP1 + 1 or z > 10:
                bp.set(x, y, z, "iron_bars")
                bp.set(x, y + 1, z, "iron_bars")
    # cornice and roof
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            if abs(x - cx) == 6 or abs(z - cz) == 6:
                if z >= 7:
                    fc = "east" if x < cx - 5 else "west" if x > cx + 5 else ("south" if z < cz else "north")
                    bp.set(x, F_TOW + 4, z, stair(SMO_ST, fc, "top"))
    apex = solid_roof(bp, cx - 6, cz - 6, cx + 6, cz + 6, F_TOW + 5)
    bp.set(cx, apex + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # base plinth (darker, proud)
    for x in range(cx - 6, cx + 7):
        for z in range(max(cz - 6, 11), cz + 7):
            if abs(x - cx) == 6 or abs(z - cz) == 6:
                for y in range(-3, 3):
                    bp.set(x, y, z, MUD if hash3(x, y, z, 81) < 0.6 else PMUD)
                bp.set(x, 3, z, stair(MUD.replace("bricks", "brick_stairs"),
                                      "east" if x < cx - 5 else "west" if x > cx + 5 else
                                      ("south" if z < cz else "north")))
    # ground door: iron, south wall at the first landing (south-west corner), lever inside (a shortcut out,
    # not a way in); a landing on the plinth and three steps down to the valley floor
    sx, sz, f = land[1]
    dx = cx - 3
    bp.set(dx, f + 2, cz + 5, CUT)
    bp.door(dx, f, cz + 5, "south", wood="iron")
    bp.set(dx + 1, f + 1, cz + 4, "lever[face=wall,facing=north,powered=false]")
    for x in range(dx - 1, dx + 2):
        bp.set(x, f - 1, cz + 6, CUT)
        for i, y in enumerate((f - 2, f - 3)):
            z = cz + 7 + i
            for yy in range(-2, y):
                bp.set(x, yy, z, SS)
            bp.set(x, y, z, stair(SS_ST, "north"))
            for yy in range(y + 1, y + 4):
                bp.set(x, yy, z, "air")
        for yy in range(f, f + 3):
            bp.set(x, yy, cz + 6, "air")
    # deck door: east wall, 2 wide
    sx, sz, f = land[7]
    for z in (cz - 4, cz - 3):
        for y in range(f, f + 3):
            bp.set(cx + 5, y, z, "air")
    # gallery door: north wall and the gallery face (3 wide)
    sx, sz, f = land[11]
    for x in range(cx + 2, cx + 5):
        for z in (cz - 5, cz - 6):
            for y in range(f, f + 3):
                bp.set(x, y, z, "air")
    # towpath door: north wall, a bridge over the cornice, a gap in the parapet
    sx, sz, f = land[16]
    for x in range(cx - 4, cx - 1):
        for y in range(f, f + 3):
            bp.set(x, y, cz - 5, "air")
            bp.set(x, y, cz - 6, "air")
            bp.set(x, y, 5, "air")
        bp.set(x, f - 1, cz - 6, CUT)
        bp.set(x, f - 1, 5, CUT)
    hang(bp, cx, f + 2, cz + 3)


# ------------------------------------------------------------------ the breach: rubble, the keeper's house, the stair
RUB = (SS, SS, CUT, SMO, SS, CUT, "mossy_cobblestone", SS)
HOUSE = (SS, SS, CUT, SS, SMO)


def rubble_heap(bp, cx, cz, r, h, y0, seed):
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = math.hypot(x - cx, z - cz) / max(r, 0.5)
            top = int(round(h * (1 - d * d) + (hash01(x, z, seed) - 0.5) * 1.5))
            for y in range(y0, y0 + top):
                bp.set(x, y, z, RUB[int(hash3(x, y, z, seed) * len(RUB))])
            if top >= 0 and d < 1.2 and hash01(x, z, seed + 1) < 0.25:
                yy = y0 + max(top, 0)
                if is_air(bp, x, yy, z):
                    bp.set(x, yy, z, "short_grass" if top > 0 or bp.get(x, yy - 1, z) else "air")


def breach(bp):
    y0 = TOP1 + 1
    # rubble on the deck, keeping the lane z 2..9 clear from the tower to the house and the stair
    for (cx, cz, r, h, s) in ((-44, -5, 3, 4, 501), (-39, -2, 2, 2, 503),
                              (-12, -7, 3, 3, 504), (-8, -4, 2, 3, 505), (-17, 8, 1, 1, 506)):
        rubble_heap(bp, cx, cz, r, h, y0, s)
    # fallen blocks in the valley under the breach, both sides
    for i in range(16):
        x = int(-44 + 48 * hash01(i, 1, 511))
        z = int((12 + 18 * hash01(i, 2, 511)) * (1 if i % 2 else -1))
        if abs(x - river_x(z)) < 6 or abs(z - 21) < 3:
            continue
        boulder(bp, x, 1, z, r=1 + i % 3, blocks=(SS, CUT, SMO, MUD), seed=i + 520)
    # the hatch into the hollow pier (secret): a ladder down into a room inside the pier at x -39..-34
    hx, hz = -36, -8
    bp.set(hx, TOP1, hz, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(15, TOP1):
        bp.set(hx, y, hz, "ladder[facing=south,waterlogged=false]")
    for x in range(-38, -34):
        for z in range(-7, -2):
            bp.set(x, 14, z, floor_pave(x, z))
            for y in range(15, 19):
                if (x, z) != (hx, hz):
                    bp.set(x, y, z, "air")
    for y in range(15, 19):
        bp.set(hx, y, hz + 1, "air")
    bp.chest(-37, 15, -3, "east", loot=LOOT + "ga_secret")
    bp.set(-35, 15, -3, "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(-37, 15, -6, "skeleton_skull[rotation=4]")
    keepers_house(bp)
    breach_stair(bp)
    # the deck in the breach has gone wild: moss, grass tufts, gravel and loose stones
    for x in range(-46, 6):
        for z in range(-9, 10):
            if not is_air(bp, x, F_DECK, z) or bp.get(x, TOP1, z) is None or is_air(bp, x, TOP1, z):
                continue
            h = hash01(x // 2, z // 2, 561) * 0.6 + hash01(x, z, 562) * 0.4
            if h < 0.22:
                bp.set(x, F_DECK, z, "moss_carpet")
            elif h < 0.30:
                bp.set(x, F_DECK, z, "short_grass")
            elif h < 0.34 and not is_air(bp, x, TOP1 - 1, z) and bp.get(x, TOP1 - 1, z) is not None:
                bp.set(x, TOP1, z, "gravel")
            elif h > 0.93:
                bp.set(x, F_DECK, z, "sandstone_slab[type=bottom,waterlogged=false]")
    # a skeleton guard among the stones, away from the waystones
    bp.spawner(-40, TOP1 + 1, -8, MOB_SKELETON)


def keepers_house(bp):
    """Two storeys of reused stone and timber on the deck in the breach, garden, the crane over the edge."""
    x0, z0, x1, z1 = -33, -8, -22, 0
    f = F_DECK
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            bp.set(x, f - 1, z, "spruce_planks" if not edge else "cobblestone")
            for y in range(f, f + 4):
                if corner:
                    spec = "stripped_spruce_log[axis=y]"
                elif edge:
                    spec = HOUSE[int(hash3(x, y, z, 531) * len(HOUSE))]
                else:
                    spec = "air"
                bp.set(x, y, z, spec)
            bp.set(x, f + 4, z, "spruce_planks" if not edge else "stripped_spruce_log[axis=x]" if z in (z0, z1)
                   else "stripped_spruce_log[axis=z]")
            for y in range(f + 5, f + 8):
                if corner or (edge and (x - x0) % 4 == 0 and z in (z0, z1)):
                    spec = "stripped_spruce_log[axis=y]"
                elif edge:
                    spec = "spruce_planks" if y != f + 6 else "white_terracotta"
                else:
                    spec = "air"
                bp.set(x, y, z, spec)
    bp.gable_roof(x0, z0, x1, z1, f + 8, TILE_ST, ridge_axis="x", overhang=1, fill="spruce_planks")
    # door south, windows
    bp.door(-27, f, z1, "south", wood="spruce")
    bp.set(-27, f + 2, z1, "spruce_planks")
    for x in (-31, -24):
        bp.set(x, f + 1, z1, "glass_pane")
        bp.set(x, f + 2, z1, "glass_pane")
        bp.set(x, f + 6, z1, "glass_pane")
        bp.set(x, f + 6, z0, "glass_pane")
    bp.set(x1, f + 6, -4, "glass_pane")
    bp.set(x0, f + 6, -4, "glass_pane")
    # ground floor: hearth, kitchen, the sluice ledger
    bp.set(x1 - 1, f, z0 + 1, "smoker[facing=west,lit=false]")
    bp.set(x1 - 1, f, z0 + 2, "barrel[facing=up,open=false]")
    bp.set(x1 - 1, f, z0 + 3, "water_cauldron[level=3]")
    bp.set(x0 + 3, f, z0 + 1, "crafting_table")
    bp.set(x0 + 4, f, z0 + 1, "spruce_slab[type=top,waterlogged=false]")
    bp.set(x0 + 4, f + 1, z0 + 1, "candle[candles=2,lit=true,waterlogged=false]")
    bp.chest(x0 + 1, f, z0 + 1, "south", loot=LOOT + "ga_keeper")
    bp.set(-27, f + 3, -4, LANT_H)
    # ladder to the upper floor (west wall)
    bp.ladder(x0 + 1, f, z1 - 2, f + 4, "east")
    # upper floor: bed, desk, lectern
    bp.bed(x1 - 1, f + 5, z0 + 1, "south", color="blue")
    bp.set(x1 - 3, f + 5, z0 + 1, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(x0 + 3, f + 5, z0 + 1, "bookshelf")
    bp.set(x0 + 4, f + 5, z0 + 1, "bookshelf")
    bp.chest(x1 - 1, f + 5, z1 - 1, "west", loot=LOOT + "ga_keeper")
    bp.set(-27, f + 5, -4, "barrel[facing=up,open=false]")
    bp.set(-27, f + 6, -4, LANT)
    # garden east of the house: beds of earth, flowers, a rain barrel, a washing line
    for x in range(-20, -16):
        for z in range(-7, -2):
            bp.set(x, TOP1, z, "grass_block[snowy=false]" if (x + z) % 3 else "rooted_dirt")
            h = hash01(x, z, 541)
            bp.set(x, F_DECK, z, "poppy" if h < 0.3 else "cornflower" if h < 0.5 else
                   "sweet_berry_bush[age=2]" if h < 0.7 else "short_grass")
    bp.set(-21, F_DECK, -8, "barrel[facing=up,open=false]")
    bp.set(-16, F_DECK, -8, "composter[level=4]")
    # the crane on the stump: post, jib out over the north parapet, chain and hook
    top = max(y for y in range(TOP1, 40) if bp.get(-12, y, -3) is not None)
    for y in range(top + 1, top + 5):
        bp.set(-12, y, -3, "stripped_spruce_log[axis=y]")
    for z in range(-12, -2):
        bp.set(-12, top + 5, z, "stripped_spruce_log[axis=z]")
    for y in range(top - 3, top + 5):
        bp.set(-12, y, -12, CHAIN)
    bp.set(-12, top - 4, -12, "brasshaven:dark_iron_plating")


def breach_stair(bp):
    """Rubble-built stair from the deck up to the gallery's broken mouth (feet 22 -> 34), a landing halfway."""
    steps = [(x, F_DECK + 1 + i) for i, x in enumerate(range(-18, -12))]
    steps += [(-12, 28), (-11, 28)]
    steps += [(x, 29 + i) for i, x in enumerate(range(-10, -4))]
    for x, feet in steps:
        flat = x in (-12, -11)
        for z in range(2, 7):
            for y in range(TOP1 + 1, feet - 1):
                if bp.get(x, y, z) is None or is_air(bp, x, y, z):
                    bp.set(x, y, z, RUB[int(hash3(x, y, z, 551) * len(RUB))])
            if z in (2, 6):
                if is_air(bp, x, feet, z) or bp.get(x, feet, z) is None:
                    bp.set(x, feet - 1, z, SS)
                    bp.set(x, feet, z, SS_W)
                continue
            bp.set(x, feet - 1, z, SMO if flat else stair(SS_ST, "east"))
            for y in range(feet, feet + 4):
                if y <= ruin_top(x, z) + 6:
                    bp.set(x, y, z, "air")


# ------------------------------------------------------------------ the west ridge: spring house and terrace
def spring_house(bp):
    f = F_TOW
    # the terrace south of the channel end: masonry platform, retaining wall battered to the slope
    for x in range(-99, -86):
        for z in range(6, 17):
            g = gtop(x, z)
            for y in range(min(g, TOW) - 1, TOW + 1):
                edge = x in (-99, -87) or z == 16
                bp.set(x, y, z, (MUD if y < TOW - 6 else ashlar(x, y, z)) if edge or y < TOW else floor_pave(x, z))
            for y in range(f, f + 4):
                if bp.get(x, y, z) is not None and not (z == 16 and y == f):
                    bp.set(x, y, z, "air")
            if z == 16 and not -96 <= x <= -92:
                bp.set(x, f, z, SS_W)
    for x in range(-99, -86):
        bp.set(x, f, 5, "air")
    bp.set(-90, f, 13, MOD["waystone"])
    for (x, z) in ((-98, 7), (-88, 7)):
        bp.set(x, f, z, SS)
        bp.set(x, f + 1, z, LANT)
    # the hall: x -111..-101, z -8..8, barrel vault over z, floor at TOW
    x0, x1 = -111, -101
    for x in range(x0 - 1, x1 + 1):
        for z in range(-10, 11):
            vt = f + 4 + int(math.sqrt(max(0.0, 64 - z * z)) * 0.5)    # vault top (exclusive) at z
            for y in range(TOW - 3, f + 10):
                inside = x0 <= x <= x1 and abs(z) <= 8 and TOW < y < vt
                if inside:
                    bp.set(x, y, z, "air")
                elif y <= vt + 1 and (abs(z) <= 9 or y <= TOW):
                    bp.set(x, y, z, ashlar(x, y + 10, z) if y > TOW else SMO)
            if x0 <= x <= x1 and abs(z) <= 8:
                bp.set(x, TOW, z, floor_pave(x, z) if not CH_Z[0] <= z <= CH_Z[1] else WATER)
                if CH_Z[0] <= z <= CH_Z[1]:
                    bp.set(x, TOW - 1, z, WATER)
                    bp.set(x, TOW - 2, z, "terracotta")
    # the facade on x = -100: pilasters, the great arch, inscription band, pediment
    xf = -100
    for z in range(-10, 11):
        for y in range(TOW - 2, f + 11):
            arch = abs(z) <= 5 and y < f + 5 + math.sqrt(max(0.0, 30.25 - z * z)) * 0.7
            if arch and y >= f:
                bp.set(xf, y, z, "air")
                continue
            if CH_Z[0] <= z <= CH_Z[1] and y in (TOW - 1, TOW):
                bp.set(xf, y, z, WATER)
                continue
            spec = CUT if abs(z) in (6, 10) else SS
            if y == f + 9:
                spec = CHIS
            elif y == f + 10:
                spec = stair(SMO_ST, "west", "top")
            bp.set(xf, y, z, spec)
            if abs(z) in (6, 10) and f <= y < f + 9:
                bp.set(xf + 1, y, z, CUT)
    # pediment: stepped triangle of stairs over the cornice
    for k in range(6):
        zz = 11 - 2 * k
        for z in range(-zz, zz + 1):
            bp.set(xf, f + 11 + k, z, SS if abs(z) < zz else stair(SS_ST, "south" if z < 0 else "north"))
    bp.set(xf, f + 17, 0, SMO_SL + "[type=bottom,waterlogged=false]")
    # sluice gate (raised), spring niche with a waterfall, the grotto behind it (secret)
    for y in range(f, f + 5):
        bp.set(-103, y, CH_Z[0] - 1, "stripped_spruce_log[axis=y]")
        bp.set(-103, y, CH_Z[1] + 1, "stripped_spruce_log[axis=y]")
    for z in range(CH_Z[0] - 1, CH_Z[1] + 2):
        bp.set(-103, f + 5, z, "stripped_spruce_log[axis=z]")
    for z in range(CH_Z[0], CH_Z[1] + 1):
        bp.set(-103, f + 3, z, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
        bp.set(-103, f + 4, z, CHAIN)
    bp.set(-111, f + 3, -3, WATER)
    bp.set(-112, f + 3, -3, CHIS)
    bp.set(-111, f + 4, -3, CHIS)
    for z in (-4, -2):
        bp.set(-111, f + 3, z, CHIS)
    for x in range(-116, -112):
        for z in range(-5, 0):
            bp.set(x, TOW, z, floor_pave(x, z))
            for y in range(f, f + 3):
                bp.set(x, y, z, "air")
            bp.set(x, f + 3, z, SS)
        for z in (-6, 0):
            for y in range(TOW, f + 4):
                bp.set(x, y, z, SS)
    for z in range(-6, 1):
        for y in range(TOW, f + 4):
            bp.set(-117, y, z, SS)
    for z in (-4, -3, -2):
        for y in range(f, f + 3):
            bp.set(-112, y, z, "air")
    bp.set(-112, TOW, -3, SMO)
    bp.chest(-116, f, -3, "east", loot=LOOT + "ga_secret")
    bp.set(-115, f, -5, "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(-115, f, -1, "amethyst_cluster[facing=up,waterlogged=false]")
    # the nymph in her niche (north wall), the offering chest, lamps
    for y in range(f, f + 4):
        bp.set(-106, y, -8, "air")
    bp.set(-106, f, -8, "quartz_pillar[axis=y]")
    bp.set(-106, f + 1, -8, "quartz_pillar[axis=y]")
    bp.set(-106, f + 2, -8, "quartz_block")
    bp.set(-106, f + 3, -8, "player_head[rotation=8]")
    bp.chest(-108, f, 7, "north", loot=LOOT + "ga_spring")
    bp.barrel(-104, f, 7)
    for x in (-109, -104):
        hang(bp, x, f + 4, 3)
    bp.set(-110, f, 6, "lectern[facing=north,has_book=false,powered=false]")


# ------------------------------------------------------------------ the ridge road
def ridge_road(bp):
    for (x, z), (feet, ux, uz) in HILL_CELLS.items():
        if not (AX0 <= x <= AX1 and AZ0 <= z <= AZ1):
            continue
        fi = int(round(feet))
        g = gtop(x, z)
        if fi - 1 != g:
            continue
        # a stair where the road climbs onto this cell from the one below along the way
        bx, bz = (x - (1 if ux > 0.5 else -1 if ux < -0.5 else 0), z - (1 if uz > 0.5 else -1 if uz < -0.5 else 0))
        prev = HILL_CELLS.get((bx, bz))
        h = hash01(x, z, 561)
        if prev is not None and int(round(prev[0])) == fi - 1 and (bx, bz) != (x, z):
            fc = "east" if ux > 0.5 else "west" if ux < -0.5 else ("south" if uz > 0 else "north")
            bp.set(x, fi - 1, z, stair("cobblestone_stairs", fc))
        else:
            bp.set(x, fi - 1, z, "dirt_path" if h < 0.55 else ("cobblestone" if h < 0.8 else "coarse_dirt"))
        bp.set(x, fi - 2, z, "dirt")
        for y in range(fi, fi + 3):
            if bp.get(x, y, z) is not None:
                bp.set(x, y, z, "air")
    # waymarks: little cairns with lanterns at the hairpins
    for (x, z) in HILL[1:-1]:
        for (dx, dz) in ((2, 2), (-2, -2)):
            px, pz = x + dx, z + dz
            if (px, pz) in HILL_CELLS:
                continue
            g = gtop(px, pz)
            bp.set(px, g + 1, pz, "cobblestone_wall")
            bp.set(px, g + 2, pz, LANT)
            break


# ------------------------------------------------------------------ the east ridge: castellum, valve hall, cistern
def cas_wall(x, y, z):
    h = hash3(x, y, z, 91)
    if y < 52:
        return MUD if h < 0.35 else SS
    if y > 78:
        return SMO if h < 0.4 else CUT
    return SS if h < 0.6 else (CUT if h < 0.88 else SMO)


def castellum(bp):
    x0, z0, x1, z1 = CAS
    top = 84
    # plinth (battered, dark), walls 2 thick, floors
    for x in range(x0 - 2, x1 + 3):
        for z in range(z0 - 2, z1 + 3):
            ring = max(abs(x - (x0 + x1) / 2) - (x1 - x0) / 2, abs(z - (z0 + z1) / 2) - (z1 - z0) / 2)
            if ring > 0:
                if x < x0 and -6 <= z <= 6:
                    continue
                hh = 50 if ring <= 1 else 48
                for y in range(44, hh + 1):
                    bp.set(x, y, z, MUD if hash3(x, y, z, 92) < 0.6 else PMUD)
                if ring <= 1:
                    bp.set(x, 51, z, stair(MUD.replace("bricks", "brick_stairs"),
                                           "east" if x < x0 else "west" if x > x1 else "south" if z < z0 else "north"))
                continue
            wall = x in (x0, x0 + 1, x1 - 1, x1) or z in (z0, z0 + 1, z1 - 1, z1)
            for y in range(44, top + 1):
                if wall:
                    bp.set(x, y, z, cas_wall(x, y, z))
                elif y in (48, 60, 72, 83):
                    bp.set(x, y, z, floor_pave(x, z) if y < 83 else SS)
                elif y > 48:
                    bp.set(x, y, z, "air")
    # string courses, corner buttresses with pinnacles, mid-face pilasters, cornice
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            fc = "east" if x < x0 else "west" if x > x1 else "south" if z < z0 else "north"
            for y in (60, 72):
                bp.set(x, y, z, stair(SMO_ST, fc, "top"))
            bp.set(x, top, z, stair(SMO_ST, fc, "top"))
    for (cx, cz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        sx = -1 if cx == x0 else 1
        sz = -1 if cz == z0 else 1
        for dx in range(0, 3):
            for dz in range(0, 3):
                x, z = cx + sx * dx, cz + sz * dz
                for y in range(44, top + 3):
                    bp.set(x, y, z, CUT if (y // 4) % 2 else SS)
        px, pz = cx + sx, cz + sz
        bp.set(px, top + 3, pz, CHIS)
        bp.set(px, top + 4, pz, SS_W)
        bp.set(px, top + 5, pz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for (x, z, ax) in ((104, z1 + 1, "x"), (x1 + 1, 0, "z")):
        for k in (-1, 0, 1):
            xx, zz = (x + k, z) if ax == "x" else (x, z + k)
            for y in range(52, top):
                bp.set(xx, y, zz, CUT if k == 0 or y % 3 == 0 else SS)
    # windows: ground hall tall, keepers' hall, belfry loggia arches
    for (wx, wz, ax) in ((x1, -6, "z"), (x1, 6, "z"), (98, z1, "x"), (110, z1, "x"), (96, z0, "x"),
                         (112, z0, "x")):
        for k in (0, 1):
            for y in range(53, 57):
                xx, zz = (wx, wz + k) if ax == "z" else (wx + k, wz)
                d = 1 if (wx == x1) else -1
                if ax == "z":
                    bp.set(xx, y, zz, "glass_pane")
                    bp.set(xx - d, y, zz, "air")
                else:
                    dd = 1 if wz == z1 else -1
                    bp.set(xx, y, zz, "glass_pane")
                    bp.set(xx, y, zz - dd, "air")
            for y in range(63, 66):
                xx, zz = (wx, wz + k) if ax == "z" else (wx + k, wz)
                if ax == "z":
                    bp.set(xx, y, zz, "glass_pane")
                    bp.set(xx - (1 if wx == x1 else -1), y, zz, "air")
                else:
                    bp.set(xx, y, zz, "glass_pane")
                    bp.set(xx, y, zz - (1 if wz == z1 else -1), "air")
    # belfry: three arched openings on each face, balustrade
    for side in ("n", "s", "e", "w"):
        for c in (-6, 0, 6):
            for k in (-1, 0, 1):
                for y in range(73, 80):
                    if y == 79 and k != 0:
                        continue
                    if side in ("n", "s"):
                        x, zz = 104 + c + k, (z0 if side == "n" else z1)
                        if side == "n" and 99 <= x <= 109:
                            continue
                        for z in (zz, zz + (1 if side == "n" else -1)):
                            bp.set(x, y, z, "air")
                        if y == 73:
                            bp.set(x, y, zz, SS_W)
                    else:
                        xx, z = (x1 if side == "e" else x0), c + k
                        for x in (xx, xx + (-1 if side == "e" else 1)):
                            bp.set(x, y, z, "air")
                        if y == 73:
                            bp.set(xx, y, z, SS_W)
    # roof and lantern
    apex = solid_roof(bp, x0 - 2, z0 - 2, x1 + 2, z1 + 2, top + 1)
    bp.set(104, apex + 1, 0, CHIS)
    bp.set(104, apex + 2, 0, "copper_block")
    bp.set(104, apex + 3, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the west door from the towpath, the inlet for the channel
    for z in range(0, 3):
        for y in range(F_TOW, F_TOW + 3):
            for x in (x0, x0 + 1):
                bp.set(x, y, z, "air")
    for z in range(CH_Z[0], CH_Z[1] + 1):
        for x in range(x0 - 1, 101):
            bp.set(x, TOW - 2, z, "terracotta")
            bp.set(x, TOW - 1, z, WATER)
            bp.set(x, TOW, z, "air" if x <= x0 + 1 or x >= 99 else "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        bp.set(x0, F_TOW, z, CUT)
    distribution_hall(bp)
    keepers_hall(bp)
    belfry(bp)


def distribution_hall(bp):
    f = CAS_F[0]
    cx, cz = AC
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.4:
                bp.set(x, TOW, z, WATER)
                bp.set(x, TOW - 1, z, WATER)
                bp.set(x, TOW - 2, z, "terracotta")
            elif d <= 5.4:
                bp.set(x, f, z, SS_W if (x + z) % 4 else SMO)
                bp.set(x, TOW, z, SMO)
    # outlet pipes in the floor to the three outer walls, down-pipes to the valve hall
    for (dx, dz) in ((1, 0), (0, 1), (0, -1)):
        for k in range(6, 11):
            bp.set(cx + dx * k, TOW, cz + dz * k, "brasshaven:copper_pipes")
    for (x, z) in ((96, -8), (112, -8), (96, 8), (112, 8)):
        for y in range(F_GAL + 1, TOW + 4):
            bp.set(x, y, z, "brasshaven:copper_pipes")
        bp.set(x, TOW + 4, z, "brasshaven:pressure_gauge")
    for (x, z) in ((97, -7), (111, 7)):
        hang(bp, x, f + 7, z)
    hang(bp, cx, f + 8, cz, "brasshaven:brass_chandelier")
    bp.chest(113, f, -9, "west", loot=LOOT + "ga_castellum")
    bp.barrel(113, f, 9)
    bp.barrel(112, f, 9)
    bp.set(95, f, 9, "brasshaven:gear_panel")
    bp.set(95, f + 1, 9, LANT)


def keepers_hall(bp):
    f = CAS_F[1]
    for x in range(100, 109):
        bp.set(x, f, 0, "spruce_planks" if x in (100, 108) else "spruce_slab[type=top,waterlogged=false]")
    for x in range(101, 108, 2):
        bp.set(x, f, -1, stair("spruce_stairs", "south"))
        bp.set(x, f, 1, stair("spruce_stairs", "north"))
    bp.set(104, f + 1, 0, "candle[candles=4,lit=true,waterlogged=false]")
    for z in range(-8, 9):
        if z % 3 and abs(z) > 1:
            bp.set(113, f, z, "bookshelf")
            bp.set(113, f + 1, z, "bookshelf")
    bp.set(95, f, -9, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(95, f, 9, "cartography_table")
    bp.chest(95, f, 0, "east", loot=LOOT + "ga_castellum")
    hang(bp, 104, f + 7, 0, "brasshaven:brass_chandelier")
    for (x, z) in ((97, -7), (111, 7), (97, 7), (111, -7)):
        hang(bp, x, f + 8, z)


def belfry(bp):
    f = CAS_F[2]
    bp.set(104, f + 6, 0, "bell[attachment=ceiling,facing=north,powered=false]")
    for y in range(f + 7, 83):
        bp.set(104, y, 0, CHAIN)
    bp.chest(96, f, 8, "east", loot=LOOT + "ga_belfry")
    bp.chest(112, f, -8, "west", loot=LOOT + "ga_belfry")
    bp.spawner(98, f, -6, MOB_GARGOYLE)
    for (x, z) in ((97, 0), (111, 0)):
        bp.set(x, f, z, SS)
        bp.set(x, f + 1, z, LANT)


def turret(bp):
    cx, cz = TUR
    land = build_newel(bp, cx, cz, F_GAL, 13, 2, 80, wall=cas_wall, doors=(0, 5, 9, 13))
    apex = solid_roof(bp, cx - 6, cz - 6, cx + 6, cz + 6, 81)
    bp.set(cx, apex + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for y in range(52, 80, 7):
        for (x, z) in ((cx, cz - 5), (cx - 5, cz), (cx + 5, cz)):
            bp.set(x, y, z, "iron_bars")
            bp.set(x, y + 1, z, "iron_bars")
    # doors south: k0 into the valve hall, k5/k9/k13 into the castellum storeys
    for k in (0, 5, 9, 13):
        sx, sz, f = land[k]
        for x in range(cx + sx * 2, cx + sx * 4 + sx, sx):
            for z in range(cz + 5, CAS[1] + 2 if k else VALVE[1]):
                for y in range(f, f + 3):
                    bp.set(x, y, z, "air")
            if k == 0:
                for z in range(cz + 5, VALVE[1]):
                    bp.set(x, f - 1, z, floor_pave(x, z))
                    ensure(bp, x, f + 3, z, SS)
                for y in range(f - 1, f + 4):
                    for z in range(cz + 5, VALVE[1]):
                        ensure(bp, cx + sx * 1, y, z, SS)
                        ensure(bp, cx + sx * 5, y, z, SS)


def valve_hall(bp):
    x0, z0, x1, z1 = VALVE
    f = F_GAL
    shell_box(bp, x0, f, z0, x1, f + 9, z1, wall=lambda x, y, z: SS if hash3(x, y, z, 95) < 0.7 else MUD,
              floor=floor_pave)
    # the west door from the gallery corridor
    for z in range(COR_Z[0], COR_Z[1] + 1):
        for y in range(f, f + 4):
            bp.set(x0 - 1, y, z, "air")
    # columns carrying the castellum floor
    for (x, z) in ((97, -5), (97, 5), (104, -5), (104, 5), (111, -5), (111, 5)):
        for y in range(f, f + 10):
            bp.set(x, y, z, CHIS if y in (f, f + 9) else SMO)
    # machinery: valve wheels (gear panels), gauges, pipes, the grate over the cistern
    for x in range(95, 114, 4):
        bp.set(x, f, z0, "brasshaven:gear_panel")
        bp.set(x, f + 1, z0, "brasshaven:pressure_gauge")
        bp.set(x, f + 2, z0, "lever[face=wall,facing=south,powered=false]")
    for x in range(101, 104):
        for z in range(-1, 2):
            bp.set(x, f - 1, z, "iron_bars")
    for x in range(100, 105):
        for z in (-2, 2):
            bp.set(x, f, z, SS_W)
    for z in range(-1, 2):
        bp.set(100, f, z, SS_W)
        bp.set(104, f, z, SS_W)
    for (x, z) in ((95, 0), (113, 0), (104, -8), (104, 8)):
        hang(bp, x, f + 7, z)
    bp.chest(x1, f, -8, "west", loot=LOOT + "ga_valve")
    bp.chest(x0, f, 8, "east", loot=LOOT + "ga_valve")
    bp.spawner(108, f, -2, MOB_KNIGHT)
    # the corridor south to the boss stair (x 110..112, z 10..29)
    for x in range(110, 113):
        for z in range(z1 + 1, BN[1] - 5):
            bp.set(x, f - 1, z, floor_pave(x, z))
            for y in range(f, f + 3):
                bp.set(x, y, z, "air")
            ensure(bp, x, f + 3, z, SS)
        for z in range(z1 + 1, BN[1] - 5):
            for y in range(f - 1, f + 4):
                ensure(bp, 109, y, z, SS)
                ensure(bp, 113, y, z, SS)
    for z in range(14, BN[1] - 5, 6):
        hang(bp, 111, f + 2, z)


def arena_top(r):
    return 30 - 8 * (r / 17.5) ** 2


def cistern(bp):
    cx, cz = AC
    f = AF
    for x in range(cx - 21, cx + 22):
        for z in range(cz - 21, cz + 22):
            r = math.hypot(x - cx, z - cz)
            if r > 20.4:
                continue
            top = arena_top(min(r, 17.5))
            for y in range(f - 2, int(top) + 3):
                if r <= 17.5 and f <= y < top:
                    bp.set(x, y, z, "air")
                elif r <= 17.5 and y == f - 1:
                    ring = int(r) % 4
                    bp.set(x, y, z, CHIS if 8.5 <= r < 9.5 else (CUT if ring == 0 else SMO))
                else:
                    bp.set(x, y, z, SS if hash3(x, y, z, 97) < 0.75 else (MUD if y < f + 4 else CUT))
    # columns: a ring of eight, 2 x 2, with bases and capitals
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        px, pz = cx + 12 * math.cos(a), cz + 12 * math.sin(a)
        for x in range(round(px) - 1, round(px) + 1):
            for z in range(round(pz) - 1, round(pz) + 1):
                tt = arena_top(math.hypot(x - cx, z - cz))
                for y in range(f, int(tt) + 1):
                    bp.set(x, y, z, CHIS if y in (f, int(tt)) else SMO)
        ix, iz = round(cx + 9.8 * math.cos(a)), round(cz + 9.8 * math.sin(a))
        bp.set(ix, f + 5, iz, SOUL_H)
        bp.set(ix, f + 6, iz, CHAIN)
        for y in range(f + 7, int(arena_top(math.hypot(ix - cx, iz - cz))) + 1):
            bp.set(ix, y, iz, CHAIN)
    # gutters (water a block down), the central basin round the seal, the oculus up to the valve hall grate
    for x in range(cx - 18, cx + 19):
        for z in range(cz - 18, cz + 19):
            r = math.hypot(x - cx, z - cz)
            if 15.0 <= r <= 16.2 and not (abs(x - 102) <= 2 and abs(z) > 10) and not (z >= 12 and x <= 95):
                bp.set(x, f - 1, z, WATER)
                bp.set(x, f - 2, z, "terracotta")
            elif 2.5 <= r <= 3.6:
                bp.set(x, f - 1, z, WATER)
                bp.set(x, f - 2, z, "terracotta")
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in range(int(arena_top(0)), F_GAL - 1):
                bp.set(x, y, z, "air")
    bp.boss_seal(cx, f - 1, cz, BOSS, 16)
    # the passage from the antechamber (north, compression) and its mist; the drain tunnel west and its mist
    for x in range(cx - 1, cx + 2):
        for z in range(16, 25):
            bp.set(x, f - 1, z, floor_pave(x, z))
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
            ensure(bp, x, f + 4, z, SS)
        for z in range(16, 25):
            for y in range(f - 1, f + 5):
                for xx in (cx - 2, cx + 2):
                    if math.hypot(xx - cx, z - cz) > 17.5:
                        ensure(bp, xx, y, z, SS)
    bp.mist(cx - 1, f, 18, cx + 1, f + 3, 18)
    for x in range(69, 93):
        for z in range(13, 16):
            if math.hypot(x - cx, z - cz) <= 17.0:
                continue
            bp.set(x, f - 1, z, floor_pave(x, z) if x > 70 else CUT)
            for y in range(f, f + 3):
                bp.set(x, y, z, "air")
            ensure(bp, x, f + 3, z, SS)
        for y in range(f - 1, f + 4):
            ensure(bp, x, y, 12, SS)
            ensure(bp, x, y, 16, SS)
    mx = max(x for x in range(69, 100) if math.hypot(x - cx, 14 - cz) > 17.5)
    bp.mist(mx, f, 13, mx, f + 2, 15)
    for x in range(72, 90, 6):
        bp.set(x, f + 2, 13, "soul_wall_torch[facing=south]")
    # the drain mouth: an iron door that opens from inside only
    for z in (13, 15):
        for y in range(f, f + 3):
            bp.set(69, y, z, SS)
    bp.set(69, f + 2, 14, SS)
    bp.door(69, f, 14, "west", wood="iron")
    bp.set(70, f + 1, 13, "lever[face=wall,facing=south,powered=false]")
    # the way down the slope under the arcade: a stair from the mouth to the valley floor
    for x in range(56, 69):
        feet = f - (68 - x)
        for z in range(13, 16):
            g = gtop(x, z)
            for y in range(max(-1, min(g, feet - 2)), feet - 1):
                bp.set(x, y, z, MUD if hash3(x, y, z, 99) < 0.5 else SS)
            if feet <= 1:
                bp.set(x, 0, z, "cobblestone")
                continue
            bp.set(x, feet - 1, z, stair("mud_brick_stairs", "east") if x < 68 else CUT)
            for y in range(feet, feet + 4):
                bp.set(x, y, z, "air")
    vault(bp)
    antechamber(bp)


def antechamber(bp):
    cx, cz = BN
    land = build_newel(bp, cx, cz, AF, 7, 1, F_GAL + 4, doors=(0, 7))
    # bottom door (k0, north-west landing) into the antechamber; top door (k7, north-east) to the corridor
    sx, sz, f = land[0]
    for x in range(cx - 4, cx - 1):
        for y in range(f, f + 3):
            bp.set(x, y, cz - 5, "air")
    sx, sz, f = land[7]
    for x in range(cx + 2, cx + 5):
        for y in range(f, f + 3):
            bp.set(x, y, cz - 5, "air")
    # the antechamber: x 99..106, z 25..29, the site of grace before the boss
    shell_box(bp, 99, AF, 25, 106, AF + 4, 29, wall=SS, floor=floor_pave)
    bp.set(100, AF, 28, MOD["waystone"])
    bp.set(105, AF, 26, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(99, AF, 25, "lectern[facing=south,has_book=false,powered=false]")
    hang(bp, 102, AF + 3, 27)
    for x in range(101, 104):
        for y in range(AF, AF + 4):
            bp.set(x, y, 24, "air")


def vault(bp):
    cx, cz = AC
    f = AF
    shell_box(bp, 96, f, -28, 108, f + 4, -21, wall=CUT, floor=lambda x, z: SMO if (x + z) % 2 else CHIS)
    for z in range(-21, -17):
        for y in range(f, f + 3):
            bp.set(cx, y, z, "air")
        bp.set(cx, f - 1, z, CUT)
    for y in range(f, f + 3):
        bp.set(cx, y, -18, MOD["vault_bars"])
    for z in range(-20, -17):
        for y in range(f - 1, f + 4):
            ensure(bp, cx - 1, y, z, CUT)
            ensure(bp, cx + 1, y, z, CUT)
        ensure(bp, cx, f + 3, z, CUT)
    bp.chest(97, f, -25, "east", loot=LOOT + "ga_vault")
    bp.chest(107, f, -25, "west", loot=LOOT + "ga_vault")
    bp.chest(102, f, -28, "south", loot=LOOT + "ga_vault")
    for x in (99, 105):
        bp.set(x, f, -28, "gold_block")
        bp.set(x, f + 1, -28, SOUL)
    hang(bp, 102, f + 3, -24, SOUL_H)


# ------------------------------------------------------------------ the approach, the quarry camp, plants
def acacia(bp, x, y, z, h, seed):
    # on a slope the crown clears the uphill ground by a full walking height
    hi = max(gtop(x + dx, z + dz) for dx in range(-4, 5) for dz in range(-4, 5))
    if hi + 4 - y > h + 3:
        return                                   # too steep for a tree here
    h = max(h, hi + 4 - y)
    lean = (1, 0) if seed % 2 else (0, 1)
    px, pz = x, z
    for i in range(h):
        if i == h // 2:
            px, pz = px + lean[0], pz + lean[1]
        bp.set(px, y + i, pz, "acacia_log[axis=y]")
    top = y + h
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if abs(dx) + abs(dz) <= 4 and hash01(dx + seed, dz, 601) < 0.9:
                bp.set(px + dx, top, pz + dz, "acacia_leaves[distance=1,persistent=true,waterlogged=false]",
                       keep=True)
            if abs(dx) + abs(dz) <= 2:
                bp.set(px + dx, top + 1, pz + dz, "acacia_leaves[distance=1,persistent=true,waterlogged=false]",
                       keep=True)


def approach(bp):
    # the marker where the road enters the site
    mx, mz = 52, 62
    bp.set(mx, 0, mz, SS)
    for y in range(1, 4):
        bp.set(mx, y, mz, CUT if y < 3 else SS)
    bp.set(mx, 4, mz, CHIS)
    bp.set(mx, 5, mz, LANT)
    # the builders' quarry camp: blocks cut and stacked, a broken crane, a tent, a fire
    cx, cz = 66, 46
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if gtop(x, z) == 0 and hash01(x, z, 611) < 0.5:
                bp.set(x, 0, z, "coarse_dirt")
    for (x, z, n) in ((cx - 4, cz - 3, 3), (cx - 2, cz - 4, 2), (cx + 3, cz + 2, 2)):
        for i in range(n):
            for dx in (0, 1):
                bp.set(x + dx, 1 + i // 2, z + (i % 2), CUT if (i + dx) % 2 else SS)
    for y in range(1, 9):
        bp.set(cx + 4, y, cz - 3, "stripped_spruce_log[axis=y]")
    for x in range(cx + 1, cx + 5):
        bp.set(x, 8, cz - 3, "stripped_spruce_log[axis=x]")
    for y in range(5, 8):
        bp.set(cx + 1, y, cz - 3, CHAIN)
    bp.set(cx + 1, 4, cz - 3, CHIS)
    for x in range(cx - 4, cx):
        for z in range(cz + 2, cz + 6):
            bp.set(x, 0, z, "spruce_planks" if x > cx - 4 and z < cz + 5 else "coarse_dirt")
    for z in range(cz + 2, cz + 6):
        bp.set(cx - 4, 1, z, "spruce_fence")
        bp.set(cx - 4, 2, z, "white_wool")
        bp.set(cx - 3, 3, z, "white_wool")
        bp.set(cx - 2, 3, z, "white_wool")
        bp.set(cx - 1, 2, z, "white_wool")
        bp.set(cx - 1, 1, z, "spruce_fence")
    bp.chest(cx - 3, 1, cz + 4, "east", loot=LOOT + "ga_camp")
    bp.set(cx + 1, 1, cz + 3, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    bp.set(cx + 2, 1, cz + 4, "barrel[facing=up,open=false]")
    # entrance waystone at the foot of the ridge road, a stone bench
    bp.set(-58, 1, 25, MOD["waystone"])
    for x in (-62, -61):
        bp.set(x, 1, 26, stair("smooth_sandstone_stairs", "north"))


def plants(bp):
    placed = []
    for i in range(400):
        if len(placed) >= 46:
            break
        x = int(AX0 + 4 + (AX1 - AX0 - 8) * hash01(i, 1, 621))
        z = int(AZ0 + 4 + (AZ1 - AZ0 - 8) * hash01(i, 2, 621))
        g = gtop(x, z)
        if abs(z) < 16 or abs(x - river_x(z)) < 7 or g > 30:
            continue
        if any(abs(x - a) < 7 and abs(z - b) < 7 for a, b in placed):
            continue
        if any((x + dx, z + dz) in HILL_CELLS for dx in range(-4, 5) for dz in range(-4, 5)):
            continue
        if abs(z - 21) < 5 and g == 0 or (40 < x < 75 and 36 < z < 56) or (x > 84 and abs(z) < 40):
            continue
        if bp.get(x, g, z) != "minecraft:grass_block" or bp.get(x, g + 1, z) is not None:
            continue
        if hash01(i, 3, 621) < 0.6:
            acacia(bp, x, g + 1, z, 5 + i % 3, i)
        else:
            oak(bp, x, g + 1, z, h=5 + i % 3, seed=i)
        placed.append((x, z))
    for i in range(500):
        x = int(AX0 + 2 + (AX1 - AX0 - 4) * hash01(i, 5, 631))
        z = int(AZ0 + 2 + (AZ1 - AZ0 - 4) * hash01(i, 6, 631))
        g = gtop(x, z)
        if abs(z) < 13 and abs(x) < 100:
            continue
        if bp.get(x, g, z) != "minecraft:grass_block" or bp.get(x, g + 1, z) is not None:
            continue
        h = hash01(i, 7, 631)
        bp.set(x, g + 1, z, "short_grass" if h < 0.55 else "tall_grass[half=lower]" if h < 0.6 else
               "dandelion" if h < 0.72 else "oxeye_daisy" if h < 0.84 else "short_dry_grass" if h < 0.94 else
               "poppy")
        if h >= 0.55 and h < 0.6:
            bp.set(x, g + 2, z, "tall_grass[half=upper]")


# ------------------------------------------------------------------ builder
def great_aqueduct(bp):
    global G_
    G_ = heights()
    terrain(bp)
    valley(bp)
    arcade(bp)
    channel(bp)
    gallery(bp)
    stair_tower(bp, T1C[0], T1C[1], False)
    stair_tower(bp, T2C[0], T2C[1], True)
    breach(bp)
    spring_house(bp)
    ridge_road(bp)
    valve_hall(bp)
    castellum(bp)
    turret(bp)
    cistern(bp)
    approach(bp)
    plants(bp)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("spring_house", (-102, F_TOW, 3), (-111, F_TOW + 2, -3)),
    ("keepers_house", (-24, F_DECK, -2), (-31, F_DECK + 1, -6)),
    ("breach", (-20, F_DECK, 7), (-42, 40, 0)),
    ("gallery", (0, F_GAL, 4), (28, F_GAL + 1, 4)),
    ("lamp_room", (42, F_GAL, -1), (31, F_GAL + 1, -4)),
    ("distribution_hall", (96, CAS_F[0], 7), (104, CAS_F[0] + 1, 0)),
    ("cistern_arena", (102, AF, 15), (102, AF + 6, -12)),
]

register(StructureDef(
    "great_aqueduct", "overworld",
    ["plains", "sunflower_plains", "meadow", "savanna", "savanna_plateau"],
    [Piece("aqueduct", great_aqueduct, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_SKELETON, 8, 1, 2), (MOB_KNIGHT, 3, 1, 1)],
    title_fr="Le Grand Aqueduc", title_en="The Great Aqueduct"))
