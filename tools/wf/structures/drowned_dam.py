"""Dam of the Drowned Valley (Le Barrage de la vallée engloutie): a curved arch dam of stone and brass 170 blocks
long and 66 high closing a horseshoe of rock, its reservoir drowning a village whose bell tower still breaks the
surface. Colossal tier (tools/BUILDING.md §1, §12 concept 12, §10 legacy-dungeon template, §15), steampunk
(tools/STYLE_STEAMPUNK.md: grey stone 60 %, brass and copper 25 %, red-brick powerhouse, amber light).

Silhouette (one noun phrase, §15.1): a pale curved wall between two rock shoulders, bowed toward a flat lake, with a
square control tower riding the middle of its crest, two sentinel towers standing free in front of its face, a lift
headframe and a red-brick powerhouse with a copper gable at its foot.

Layout, ground y = 0 (feet 1 in the valley below the dam), x east, z south; the reservoir lies north (z < 0):
  * the dam: an arc of radius 145 round (0, ZC) (upstream face; crest 10 thick, base 34) from x -80 to 80, crest
    road feet 67, a berm (feet 37) along its downstream face, buttress ribs, brass string courses;
  * the reservoir: water top y 60 inside a horseshoe ridge (rim ~68); on its bed (y 53) the drowned village: houses,
    a bridge over the old river bed and a church whose belfry stands out of the water (the hoard in it);
  * the approach (south): the surveyors' camp and its waystone (z ~106), a path up the valley behind a rock spur
    (denial) to the works yard at the foot of the west sentinel tower (reveal of the whole wall);
  * the route: works yard -> Generator Hall I (the lobby, west wing of the powerhouse) -> the west tower's newel
    stair (36 up) -> the gangway to the berm -> the valve house (penstock valves; a stair up to the drowned gallery
    whose windows look into the reservoir at the village) -> the control tower's newel stair -> the crest hall ->
    the control room (site of grace, the hub) -> the crest road east (vista both ways) -> the flying bridge to the
    east tower -> its newel stair down 66 -> Generator Hall II (site of grace) -> a narrow passage and the mist ->
    the main turbine chamber (boss arena, giant gears, generators in alcoves) -> the vault behind sealed bars;
  * loops: the berm joins the valve house and the control tower directly; both towers link the berm and the crest;
  * shortcuts (§10.4): the maintenance lift shaft from the crest headframe down to Generator Hall I (iron door, lever
    on the shaft side); the spillway shaft in the east gatehouse (a 66-block drop into the plunge pool, then the
    spillway tunnel out to the valley); after the boss, the arena's west passage (iron door, lever on the arena side)
    back to Hall I and the vault's door out to the tailrace quay; ladders down the upstream face to swim to the
    drowned village.
Loot gradient (§15.6): camp, yard, Hall I, towers tier 1; valve house, control room, drowned gallery, village tier
1-2; Hall II tier 2; the belfry hoard tier 2-3; the vault tier 3.
Height budget: the control tower's mast tops out ~104 above the ground layer.
"""
import math

import numpy as np

from ..arch import spruce, stair
from ..blueprint import is_solid
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, COPPER, COPPER_STAIRS, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, MAHOGANY, MAHOGANY_STAIRS, PIPES, TABLE, TREAD, VERD,
                       VERD_STAIRS, W, hash01, hash3, is_air, out_facing)
from ..parts import LOOT, MOD

# the dam's own boss: the Turbine Tyrant wakes in the turbine chamber (tools/BOSSES.md; its vents are the copper
# grates of tyrant_floor, its pressure blast is dodged behind the four pillars)
BOSS = "brasshaven:turbine_tyrant"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_DROWNED = "minecraft:drowned"

# ------------------------------------------------------------------ dimensions
ZC = 130.0                 # centre of the dam's arcs (downstream)
R_UP = 145.0               # upstream face radius
R_CR = 135.0               # crest downstream face radius (crest 10 thick)
CREST = 66                 # crest road top block (feet 67)
CF = CREST + 1
BERM = 36                  # berm floor top block (feet 37)
BF = BERM + 1
DAM_X = 81
WL = 60                    # reservoir water top block
BED = 53                   # reservoir bed (village floor top block)
VF = BED + 1               # village feet
RIDGE = 68                 # rim of the horseshoe
BZ, BA, BB = -40.0, 76.0, 52.0      # reservoir ellipse centre z and half axes

# powerhouse (PH): halls feet 1
PH_X = 44                  # outer walls |x| <= 44
PH_ZN, PH_ZS = 6, 60       # north (inside the dam) and south facade
H1 = (-42, -27)            # Generator Hall I interior x (west); Hall II mirrors it
AR_X = 18                  # arena interior |x| <= 18
AR_Z0, AR_Z1 = 12, 50      # arena interior z
AR_TOP = 24                # arena air up to y 24
HALL_TOP = 17              # side halls air up to y 17
AC = (0, 31)               # arena centre
# sentinel towers (west: s = -1, east: s = 1): outer x s*46..s*58, z 22..34
TW_Z0, TW_Z1 = 22, 34
TW_TOP = 72
# control tower
CT_X0, CT_X1, CT_Z0, CT_Z1 = -9, 8, -15, 2
CT_ROOM = 75               # control room feet
CT_LOFT = 83
CT_ROOF = 89
# lift shaft (outer box)
LS_X0, LS_X1, LS_Z0, LS_Z1 = -32, -28, -6, -2
# east gatehouse and the spillway shaft
SP_C = (68, 8)
SP_R = 3

SPUR = (-17.0, 87.0)      # the rock spur on the approach
CAMP = (-40, 104)         # the surveyors' camp

AX0, AX1 = -112, 112
AZ0, AZ1 = -124, 124
AY = 80

# materials
SB, CR, MO, CH = "stone_bricks", "cracked_stone_bricks", "mossy_stone_bricks", "chiseled_stone_bricks"
SB_ST, SB_SL, SB_W = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
PA, PA_ST, PA_SL = "polished_andesite", "polished_andesite_stairs", "polished_andesite_slab"
TB, PT = "tuff_bricks", "polished_tuff"
BR, BR_ST, BR_SL, BR_W = "bricks", "brick_stairs", "brick_slab", "brick_wall"
SLATE, SLATE_ST = W + "slate_roof_tiles", W + "slate_roof_tile_stairs"
BRASS_T = W + "brass_tiles"
IRON_BR = W + "dark_iron_bricks"
RAIL = W + "brass_railing"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
# the dam's stone ladder, light to dark (BUILDING §5)
LADDER = ("smooth_stone", PA, SB, "andesite", TB, CR, MO)


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


# ------------------------------------------------------------------ dam geometry
def r_dn(y):
    """Downstream face radius at height y: battered below the berm, a gentler batter above it."""
    if y >= BF:
        return R_CR - max(0, 58 - y) * 0.25
    return 125.0 - (BERM - y) * 0.4


def rad(x, z):
    return math.hypot(x, ZC - z)


def ang(x, z):
    return math.atan2(x, ZC - z)


def polar(r, th):
    return r * math.sin(th), ZC - r * math.cos(th)


def z_at(x, r):
    """z of the arc of radius r at x (north branch)."""
    return ZC - math.sqrt(max(0.0, r * r - x * x))


def toward_c(x, z):
    """Horizontal facing from (x, z) toward the arcs' centre (downstream)."""
    return out_facing(-x, ZC - z)


def away_c(x, z):
    return OPP[toward_c(x, z)]


def in_dam(x, y, z):
    r = rad(x, z)
    return 0 <= y <= CREST and abs(x) <= DAM_X and r_dn(y) <= r <= R_UP


def crest_cell(x, z):
    r = rad(x, z)
    return R_CR <= r <= R_UP


def vhw(z):
    """Half width of the valley floor below the dam (it widens downstream)."""
    return 46.0 + max(0.0, z - 20.0) * 0.5


# ------------------------------------------------------------------ the grid
XS = np.arange(AX0, AX1 + 1)
ZS = np.arange(AZ0, AZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")
GXF, GZF = GX.astype(float), GZ.astype(float)
GR = np.hypot(GXF, ZC - GZF)
JIT = nfbm(GXF, GZF, 9.0, 31)


def ai(x, y, z):
    return x - AX0, y, z - AZ0


def inside(x, z):
    return AX0 <= x <= AX1 and AZ0 <= z <= AZ1


def ellipse_dist():
    """Signed distance (negative inside) from every column to the reservoir ellipse, its outline wobbled by noise."""
    t = np.linspace(0, 2 * math.pi, 900, endpoint=False)
    ex, ez = BA * np.sin(t), BZ - BB * np.cos(t)
    d = np.full(GX.shape, 1e9)
    for i in range(0, len(t), 60):
        dx = GXF[..., None] - ex[None, None, i:i + 60]
        dz = GZF[..., None] - ez[None, None, i:i + 60]
        d = np.minimum(d, np.sqrt(dx * dx + dz * dz).min(axis=2))
    rho = np.hypot(GXF / BA, (GZF - BZ) / BB)
    d = np.where(rho < 1, -d, d)
    return d + (nfbm(GXF, GZF, 17.0, 3) - 0.5) * 7.0


def heights():
    """Column heights: the horseshoe ridge (rim, outer slopes), the abutment shoulders at the dam's ends, the banks
    and bed of the reservoir; the valley below the dam is cut out of all of it. Returns (H, DIST, BOWL)."""
    D = ellipse_dist()
    n = nfbm(GXF, GZF, 11.0, 5)
    big = nfbm(GXF, GZF, 34.0, 15)
    # ring: a rim 6 wide (its height wanders), an outer slope 34 wide falling to the ground, concave like a scree
    # fan, with spurs and gullies (low-frequency noise on the distance)
    Dg = D + (big - 0.5) * 16
    top = RIDGE + (big - 0.5) * 8 + (n - 0.5) * 3
    t = np.clip((Dg - 6.0) / 34.0, 0, 1)
    ring = np.where(Dg < 6, top, top * (1 - t) ** 1.7 + (n - 0.5) * 6 * (1 - t))
    ring = np.where(Dg >= 40, 0, ring)
    # abutment shoulders carrying the crest's ends (top 65, the crest road stands one above)
    abut = np.zeros(GX.shape)
    for sx in (-1, 1):
        dd = np.hypot(GXF - sx * 90, GZF - 6)
        abut = np.maximum(abut, 65 - np.maximum(0, dd - 20) * 1.6 + (n - 0.5) * 3)
    mass = np.maximum(ring, abut)
    # the reservoir: steep banks down to the bed; the old river bed winds through it, a basin deepens at the dam
    zup = ZC - np.sqrt(np.maximum(0, R_UP ** 2 - GXF ** 2))
    xc = 6 + 8 * np.sin((GZF + 40) / 14.0)
    bed = BED + (nfbm(GXF, GZF, 7.0, 9) - 0.5) * 1.6
    bed = bed - 6 * np.exp(-((GXF - xc) / 5.0) ** 2) * (GZF < -12)
    dd = np.clip(zup - GZF, 0, None)                   # distance north of the dam face
    bed = bed - np.clip(1 - dd / 14.0, 0, 1) * 9
    village = (GXF > -46) & (GXF < 26) & (GZF > -74) & (GZF < -28) & (np.abs(GXF - xc) > 6)
    bed = np.where(village, BED, bed)
    bank = RIDGE + D * 2.2
    H = np.where(D < 0, np.maximum(bed, np.minimum(mass, bank)), mass)
    # near the crest's ends the rock stays under the crest road
    near_crest = (GR > R_CR - 9) & (GR < R_UP + 9) & (np.abs(GXF) > 50)
    H = np.where(near_crest, np.minimum(H, CREST - 1), H)
    # the valley below the dam
    south = GZF > zup - 1
    valley = np.maximum(0, np.abs(GXF) - (46 + np.maximum(0, GZF - 20) * 0.5)) * 1.8
    H = np.where(south, np.minimum(H, valley), H)
    # the rock spur on the approach (the denial: the path winds behind it), a craggy knoll 15 high
    ds = np.maximum(0, np.hypot((GXF - SPUR[0]) / 1.3, GZF - SPUR[1]) + (n - 0.5) * 5)
    spur = np.where((ds < 10) & (GZF > 77) & (GZF < 98), 13 * (1 - (ds / 10) ** 1.6) + (big - 0.5) * 3, 0)
    H = np.maximum(H, spur)
    # the massif dies out before the edges of the plan (no cut faces at the template's box)
    ii, kk = np.meshgrid(np.arange(GX.shape[0]), np.arange(GX.shape[1]), indexing="ij")
    edge = np.minimum(np.minimum(ii, GX.shape[0] - 1 - ii), np.minimum(kk, GX.shape[1] - 1 - kk))
    H = np.minimum(H, edge * 2.0 + (n - 0.5) * 2)
    bowl = (D < 0) & (GR > R_UP) & ~south
    return np.floor(H).astype(np.int32), D, bowl, valley


HMAP, DIST, BOWL, VALLEY = heights()
SLOPE = np.zeros(GX.shape)
_dx = np.abs(np.diff(HMAP, axis=0))
_dz = np.abs(np.diff(HMAP, axis=1))
SLOPE[:-1, :] = np.maximum(SLOPE[:-1, :], _dx)
SLOPE[1:, :] = np.maximum(SLOPE[1:, :], _dx)
SLOPE[:, :-1] = np.maximum(SLOPE[:, :-1], _dz)
SLOPE[:, 1:] = np.maximum(SLOPE[:, 1:], _dz)


def hmap(x, z):
    if not inside(x, z):
        return 0
    i, _, k = ai(x, 0, z)
    return int(HMAP[i, k])


class Plan:
    """Rock (R) and dam (D) masks over the grid; the shell (2 blocks under every open face) is what gets written."""

    def __init__(self):
        Y = np.arange(AY)[None, :, None]
        self.R = (Y <= HMAP[:, None, :]) & (HMAP[:, None, :] >= 1)
        self.D = np.zeros_like(self.R)
        for y in range(0, CREST + 1):
            # the canyon walls bound the dam: lower down, it is shorter (embedded 6 into the rock)
            self.D[:, y, :] = (GR >= r_dn(y)) & (GR <= R_UP) & (np.abs(GXF) <= DAM_X) & (VALLEY < y + 6)
        S = self.R | self.D
        air = ~S
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
        self.S = S
        self.shell = S & near
        top = S.copy()
        top[:, :-1, :] &= ~S[:, 1:, :]
        self.top = top


# ------------------------------------------------------------------ block pickers
STRATA = ("stone", "andesite", "stone", "tuff", "andesite", "stone", "diorite", "stone", "tuff", "andesite")


# the outer slopes' cover (BUILDING §5 gradients, §7): a vegetation potential falling with height and steepness,
# raised on north faces and in damp hollows; scree gullies running straight down the slopes, fanning at their feet
MOSSN = nfbm(GXF, GZF, 7.0, 43)
NFACE = np.gradient(HMAP.astype(float), axis=1)          # dH/dz > 0: the slope falls toward the north
GULLY = (np.arctan2(GXF, GZF - BZ) * 34 / (2 * math.pi) + (nfbm(GXF, GZF, 9.0, 47) - 0.5) * 0.9) % 1.0


def rock_block(x, y, z, top, d, sl):
    h = hash3(x, y, z, 7)
    i, _, k = ai(x, 0, z)
    s = y + int(5 * JIT[i, k]) + (1 if h < 0.18 else 0)
    if d < 0:                                        # inside the bowl
        if y <= WL:
            if top:
                return "mud" if h < 0.35 else ("clay" if h < 0.6 else ("gravel" if h < 0.85 else "mossy_cobblestone"))
            return "tuff" if h < 0.5 else "mud"
        if y <= WL + 4:                              # the drawdown ring: bare mud and stones above the water
            if top:
                return "coarse_dirt" if h < 0.4 else ("gravel" if h < 0.65 else ("mud" if h < 0.8 else "cobblestone"))
            return "packed_mud" if h < 0.5 else "tuff"
    hf = y / float(RIDGE)
    north = NFACE[i, k] > 0.5
    veg = 1.3 - 1.0 * hf - max(0.0, sl - 2.0) * 0.16 + (float(MOSSN[i, k]) - 0.5) * 1.1 + (0.15 if north else 0.0)
    gully = y > 2 and sl >= 1 and float(GULLY[i, k]) < 0.05 + 0.09 * max(0.0, 1.0 - hf * 1.6)
    rock = STRATA[(s // 3) % len(STRATA)]
    if top:
        if y <= 2:
            return "grass_block[snowy=false]" if h < 0.7 else ("coarse_dirt" if h < 0.85 else "gravel")
        if gully:                                    # scree: gravel and broken stone washed down the slope
            return "gravel" if h < 0.5 else ("coarse_dirt" if h < 0.68 else ("cobblestone" if h < 0.85 else
                                                                             "andesite"))
        if sl <= 1:
            return "grass_block[snowy=false]" if h < 0.85 else ("podzol[snowy=false]" if h < 0.93 else "coarse_dirt")
        if veg > 0.55:
            return "grass_block[snowy=false]" if h < 0.75 else ("moss_block" if h < 0.83 else (
                "podzol[snowy=false]" if h < 0.9 else "coarse_dirt"))
        if veg > 0.3:
            return "grass_block[snowy=false]" if h < 0.4 else ("moss_block" if h < 0.58 else (
                "coarse_dirt" if h < 0.7 else ("mossy_cobblestone" if h < 0.82 else rock)))
        if veg > 0.08:
            return "mossy_cobblestone" if h < 0.2 else ("moss_block" if h < 0.28 else (
                "gravel" if h < 0.36 else ("cobblestone" if h < 0.46 else rock)))
        return "gravel" if h < 0.08 else ("cobblestone" if h < 0.15 else (
            "mossy_cobblestone" if h < (0.3 if north else 0.2) else rock))
    depth = int(HMAP[i, k]) - y
    if y > 2 and not gully and depth <= 1 and veg > 0.3:
        return "dirt" if h < 0.6 else ("coarse_dirt" if h < 0.85 else "rooted_dirt")
    if y > 2 and depth <= 3 and veg > 0.08 and h < 0.3:
        return "mossy_cobblestone" if h < 0.2 else "moss_block"
    if gully and depth <= 1:
        return "cobblestone" if h < 0.5 else "andesite"
    if y < 6 and h < 0.25:
        return "mossy_cobblestone"
    return rock


def dam_block(x, y, z):
    """Dam masonry: dark, mossy and stained at the foot, cleaner toward the crest; vertical seepage streaks under the
    berm drains; brass string courses at y 24 and 48; the upstream face dark below the waterline, a stain ring at it."""
    r = rad(x, z)
    h = hash3(x, y, z, 11)
    up = r > R_UP - 2.5
    if up:
        if y <= WL - 1:
            return MO if h < 0.45 else (TB if h < 0.7 else ("mud_bricks" if h < 0.85 else CR))
        if y <= WL + 1:
            return "polished_deepslate" if h < 0.6 else "deepslate_bricks"
        return SB if h < 0.5 else (PA if h < 0.85 else CR)
    if y in (24, 48) and r < r_dn(y) + 1.6:
        return BRASS
    if y == 12 and r < r_dn(y) + 1.6:
        return PT
    u = int(r * ang(x, z))
    streak = hash01(u // 2, 3, 17) < 0.22 and y < BERM
    frac = y / CREST
    idx = 1.0 + (1 - frac) * 3.2 + (h - 0.5) * 1.6 + (1.4 if streak else 0) + (0.8 if y < 4 else 0)
    if (y // 4) % 2 == 0 and h < 0.5:
        idx -= 0.6                                   # faint coursing
    return LADDER[max(0, min(len(LADDER) - 1, int(idx)))]


def write_mass(bp, P):
    idx = np.argwhere(P.shell)
    for i, y, k in idx.tolist():
        x, z = int(XS[i]), int(ZS[k])
        if P.D[i, y, k]:
            bp.set(x, y, z, dam_block(x, y, z))
        else:
            bp.set(x, y, z, rock_block(x, y, z, bool(P.top[i, y, k]), float(DIST[i, k]), float(SLOPE[i, k])))


def write_water(bp, P):
    for i, k in np.argwhere(BOWL).tolist():
        x, z = int(XS[i]), int(ZS[k])
        for y in range(int(HMAP[i, k]) + 1, WL + 1):
            if y < AY and not P.S[i, y, k]:
                bp.set(x, y, z, "water")




# ------------------------------------------------------------------ small helpers
def fillb(bp, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                bp.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def clear(bp, x0, y0, z0, x1, y1, z1):
    fillb(bp, x0, y0, z0, x1, y1, z1, "air")


def shell_room(bp, x0, y0, z0, x1, y1, z1, wall, floor=None, ceil=None, t=1):
    """A room with air inside the box (x0..x1, y0..y1, z0..z1 = interior) and walls / floor / ceiling t thick."""
    for x in range(x0 - t, x1 + t + 1):
        for z in range(z0 - t, z1 + t + 1):
            inner = x0 <= x <= x1 and z0 <= z <= z1
            for y in range(y0 - t, y1 + t + 1):
                if inner and y0 <= y <= y1:
                    bp.set(x, y, z, "air")
                elif inner and y < y0:
                    bp.set(x, y, z, (floor or wall)(x, y, z) if callable(floor or wall) else (floor or wall))
                elif inner and y > y1:
                    bp.set(x, y, z, (ceil or wall)(x, y, z) if callable(ceil or wall) else (ceil or wall))
                else:
                    bp.set(x, y, z, wall(x, y, z) if callable(wall) else wall)


def masonry(x, y, z):
    h = hash3(x, y, z, 23)
    return SB if h < 0.55 else (PA if h < 0.8 else (CR if h < 0.92 else "andesite"))


def dark_masonry(x, y, z):
    h = hash3(x, y, z, 29)
    return TB if h < 0.5 else (PT if h < 0.75 else ("deepslate_bricks" if h < 0.9 else CR))


def brick(x, y, z):
    h = hash3(x, y, z, 31)
    return BR if h < 0.82 else ("mud_bricks" if h < 0.92 else "granite")


def floor_tile(x, y, z):
    return TREAD if (x + z) % 2 == 0 else PA


def lamp_post(bp, x, y, z, h=3):
    bp.set(x, y, z, IRON)
    for k in range(1, h):
        bp.set(x, y + k, z, IRON_WALL)
    bp.set(x, y + h, z, EDISON)


def hang(bp, x, y_top, z, length=2, lamp=HANG_LAMP):
    """A lamp hanging from the ceiling block at y_top + 1 (chain of `length`)."""
    for k in range(length):
        bp.set(x, y_top - k, z, CHAIN)
    bp.set(x, y_top - length, z, lamp)


def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def gear_disc(bp, cx, cy, cz, r, axis, keep_air=False):
    """A big cog: a toothed gear-panel ring, iron spokes, a brass hub; axis = the normal of its plane."""
    for u in range(-r - 2, r + 3):
        for v in range(-r - 2, r + 3):
            d = math.hypot(u, v)
            a = math.atan2(v, u)
            tooth = r + 0.4 < d <= r + 1.4 and math.cos(a * max(8, 2 * r)) > 0.35
            if d <= 1.5:
                spec = BRASS
            elif r - 1.2 < d <= r + 0.4 or tooth:
                spec = GEAR
            elif (abs(u) <= 0.5 or abs(v) <= 0.5 or abs(abs(u) - abs(v)) <= 0.5) and d < r - 1.2:
                spec = IRON
            else:
                continue
            p = {"x": (cx, cy + v, cz + u), "z": (cx + u, cy + v, cz), "y": (cx + u, cy, cz + v)}[axis]
            if keep_air and not is_air(bp, *p):
                continue
            bp.set(*p, spec)


def steep_pyramid(bp, x0, z0, x1, z1, y, spec, stairs_spec, steep=2, overhang=1, finial=None):
    """Hipped roof steeper than 45 degrees: the outline shrinks by 1 every ``steep`` layers. Returns the apex y."""
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


def arc_cells(x0, x1, r0, r1, z_pad=2):
    """Columns (x, z, r, u) whose radius lies in [r0, r1), x0 <= x <= x1 (u = arc length along r 140)."""
    for x in range(x0, x1 + 1):
        za = int(math.floor(z_at(x, r1))) - z_pad
        zb = int(math.ceil(z_at(x, r0))) + z_pad
        for z in range(za, zb + 1):
            r = rad(x, z)
            if r0 <= r < r1:
                yield x, z, r, 140.0 * ang(x, z)


# ------------------------------------------------------------------ newel stairs (as in caldera_ringwall)
def newel(x0, z0, k, f0, flights, start, cw=True):
    """Square newel stair (outer side 6 + k): 3 x 3 corner landings, flights of <= k steps 3 wide along the sides,
    round a solid k x k core. ``start``: corner index (0 NW, 1 NE, 2 SE, 3 SW) of the bottom landing at feet f0.
    Returns (cells {(x, z): (feet, facing or None, flight index)}, core box, top corner index, top feet)."""
    corner = {0: (x0, z0), 1: (x0 + 3 + k, z0), 2: (x0 + 3 + k, z0 + 3 + k), 3: (x0, z0 + 3 + k)}
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
        if az == bz:
            sx = 1 if bx > ax else -1
            facing = "east" if sx > 0 else "west"
            for u in range(k):
                x = (ax + 3 + u) if sx > 0 else (ax - 1 - u)
                ff = f + min(u + 1, n)
                for dz in range(3):
                    cells[(x, az + dz)] = (ff, facing if u < n else None, i)
        else:
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


def write_newel(bp, cells, core, f0, tread=SB_ST, fill=SB, land=PA, clear=4, core_spec=masonry, lamps=True):
    top = max(f for f, _, _ in cells.values())
    for (x, z), (f, fc, _) in cells.items():
        for y in range(f, f + clear):
            bp.set(x, y, z, "air")
    for (x, z), (f, fc, _) in cells.items():
        if fc:
            bp.set(x, f - 1, z, stair(tread, fc))
        else:
            bp.set(x, f - 1, z, land if hash01(x, z, 7) < 0.7 else fill)
        if f - 2 - f0 < 3:
            for y in range(f0 - 1, f - 1):
                bp.set(x, y, z, fill)
        else:
            bp.set(x, f - 2, z, fill)
    cx0, cz0, cx1, cz1 = core
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            edge = x in (cx0, cx1) or z in (cz0, cz1)
            for y in range(f0 - 1, top + clear):
                if edge or y >= top + clear - 1:
                    bp.set(x, y, z, core_spec(x, y, z) if callable(core_spec) else core_spec)
    if lamps:
        seen = set()
        for (x, z), (f, fc, i) in cells.items():
            if fc is None and (f, i) not in seen and (x in (cx0 - 1, cx1 + 1) and z in (cz0 - 1, cz1 + 1)):
                seen.add((f, i))
                hx = cx0 if x < cx0 else cx1
                hz = cz0 if z < cz0 else cz1
                bp.set(hx, f + 2, hz, EDISON)


def newel_laps(bp, x0, z0, k, f0, flights, start, cw=True, **kw):
    c, f = start, f0
    allcells = {}
    for i in range(0, len(flights), 3):
        cells, core, c, f1 = newel(x0, z0, k, f, flights[i:i + 3], c, cw)
        write_newel(bp, cells, core, f, **kw)
        for key, v in cells.items():
            allcells.setdefault(key, []).append(v)
        f = f1
    return allcells, core, c, f


# ------------------------------------------------------------------ the dam: crest, berm, ribs
def reserved(x, z):
    """Crest columns taken by a building (the control tower, the east gatehouse, the west guard post)."""
    if CT_X0 <= x <= CT_X1 and CT_Z0 <= z <= CT_Z1:
        return True
    if 61 <= x <= 75 and 0 <= z <= 16:
        return True
    if -76 <= x <= -66 and 3 <= z <= 13:
        return True
    return False


SWIM_LADDERS = (-40, 24)


def crest(bp):
    """The crest road (feet 67): a paved deck 8 wide with a brass double line, parapets with brass railings, lamp
    posts on the downstream parapet, a corbel course under the downstream edge, two gaps with ladders down the
    upstream face to the water."""
    lamps = set()
    for x, z, r, u in arc_cells(-80, 80, R_CR - 0.01, R_UP + 0.01):
        if reserved(x, z):
            continue
        down = r < R_CR + 1
        up = r > R_UP - 1
        h = hash3(x, CREST, z, 41)
        if down or up:
            bp.set(x, CREST, z, PA)
            bp.set(x, CF, z, SB if h < 0.75 else CH)
            face = toward_c(x, z) if down else away_c(x, z)
            if down and int(u) % 12 == 0 and int(u) not in lamps:
                lamps.add(int(u))
                bp.set(x, CF + 1, z, IRON_WALL)
                bp.set(x, CF + 2, z, IRON_WALL)
                bp.set(x, CF + 3, z, EDISON)
            else:
                bp.set(x, CF + 1, z, f"{RAIL}[facing={face}]")
        else:
            line = 139.0 <= r < 141.0
            bp.set(x, CREST, z, BRASS_T if line else ("smooth_stone" if h < 0.35 else PA))
            for y in range(CF, CF + 4):
                bp.set(x, y, z, "air")
    # corbel course under the downstream parapet (a shadow line along the whole crest)
    for x, z, r, u in arc_cells(-80, 80, R_CR - 1.0, R_CR):
        if not reserved(x, z) and bp.get(x, CREST - 1, z) is None:
            bp.set(x, CREST - 1, z, stair(SB_ST, away_c(x, z), "top"))
    # ladders down the upstream face to the reservoir (a gap in the parapet)
    for lx in SWIM_LADDERS:
        zf = int(round(z_at(lx, R_UP)))
        while rad(lx, zf) > R_UP:
            zf += 1
        while rad(lx, zf - 1) <= R_UP:
            zf -= 1
        for y in (CF, CF + 1):
            bp.set(lx, y, zf, "air")
        for y in range(WL - 6, CREST + 1):
            bp.set(lx, y, zf, PA)
            bp.set(lx, y, zf - 1, f"ladder[facing=north,waterlogged={'true' if y <= WL else 'false'}]")


def berm(bp):
    """The berm walk (feet 37) along the downstream face: paved, a railing on its outer edge, lamps."""
    r_in = r_dn(BF)
    for x, z, r, u in arc_cells(-66, 66, 125.0, r_in):
        if bp.get(x, BERM, z) is None and not in_dam(x, BERM, z):
            continue
        if VALLEY[ai(x, 0, z)[0], ai(x, 0, z)[2]] >= BERM:
            continue
        edge = r < 126.0
        bp.set(x, BERM, z, PA if (int(u) % 7 and not edge) else (TB if edge else BRASS_T))
        for y in range(BF, BF + 4):
            if bp.get(x, y, z) is not None and not in_dam(x, y, z):
                continue
            bp.set(x, y, z, "air")
        if edge:
            if int(u) % 10 == 0:
                lamp_post(bp, x, BF, z, 3)
            else:
                bp.set(x, BF, z, f"{RAIL}[facing={toward_c(x, z)}]")
    # drain spouts under the berm: a dark slot and a stain below
    for k in range(-12, 13):
        th = k * 5.0 / 125.0
        x, z = polar(124.4, th)
        x, z = int(round(x)), int(round(z))
        if abs(x) > 60:
            continue
        if bp.get(x, BERM - 1, z) is None and in_dam(x, BERM - 1, z + 1):
            bp.set(x, BERM - 1, z, stair(IRON_STAIRS, away_c(x, z), "top"))


RIB_U = [k * 13.0 for k in range(-6, 7)]
RIB_LOW = {-65.0, -39.0, -26.0, -13.0, 13.0, 26.0, 39.0, 65.0}


def ribs(bp):
    """Buttress ribs on the downstream face (2 proud, 3 wide) every 13 blocks of arc, dark tuff with a brass cap,
    below and above the berm; they stop wherever a building already stands."""
    for uk in RIB_U:
        ys = (list(range(1, BERM)) if uk in RIB_LOW else []) + (list(range(BF, CREST - 1)) if uk else [])
        for y in ys:
            r0 = r_dn(y)
            th = uk / r0
            cx, cz = polar(r0, th)
            for x in range(int(cx) - 4, int(cx) + 5):
                for z in range(int(cz) - 4, int(cz) + 5):
                    r = rad(x, z)
                    if not (r0 - 2.5 <= r < r0):
                        continue
                    if abs(r * (ang(x, z) - th)) > 1.5:
                        continue
                    if bp.get(x, y, z) is not None or VALLEY[ai(x, 0, z)[0], ai(x, 0, z)[2]] >= y:
                        continue
                    top = y in (BERM - 1, CREST - 2)
                    if top:
                        bp.set(x, y, z, stair(BRASS_STAIRS, toward_c(x, z)))
                    else:
                        bp.set(x, y, z, dark_masonry(x, y, z) if (y % 12) else BRASS)


# ------------------------------------------------------------------ the powerhouse
PB_X0, PB_X1, PB_Y1, PB_Z0, PB_Z1 = -45, 45, 37, 2, 61
ALCOVES = (-12, 0, 12)


def roof_y(x):
    """Underside... the gable roof of the turbine chamber: eaves 27 at |x| 19, ridge 33."""
    return 27 + (19 - min(abs(x), 19)) // 3


def ph_volume(P):
    """Masses and carved spaces of the powerhouse in a local box (numpy): returns (solid, carved, written)."""
    xs = np.arange(PB_X0, PB_X1 + 1)
    zs = np.arange(PB_Z0, PB_Z1 + 1)
    X, Y, Z = np.meshgrid(xs, np.arange(PB_Y1 + 1), zs, indexing="ij")
    AXa = np.abs(X)
    sol = np.zeros(X.shape, bool)
    # side halls (outer walls |x| 43..44), wall zones (19..26), the chamber's north and south masses
    sol |= (AXa >= 27) & (AXa <= 44) & (Z >= 6) & (Z <= 60) & (Y <= 19)
    sol |= (AXa >= 19) & (AXa <= 26) & (Z >= 6) & (Z <= 60) & (Y <= 27)
    sol |= (AXa <= 18) & (Z >= 2) & (Z <= 11) & (Y <= 27)
    sol |= (AXa <= 18) & (Z >= 51) & (Z <= 60) & (Y <= 7)
    sol |= (AXa <= 18) & (Z >= 59) & (Z <= 60) & (Y <= 27 + (19 - np.minimum(AXa, 19)) // 3)
    sol |= (AXa <= 44) & (Z >= 6) & (Z <= 60) & (Y == 0)
    car = np.zeros(X.shape, bool)
    # Generator Halls I and II
    car |= (AXa >= 27) & (AXa <= 42) & (Z >= 10) & (Z <= 58) & (Y >= 1) & (Y <= HALL_TOP)
    # the turbine chamber up to its roof, over the vault at the back
    ry = 27 + (19 - np.minimum(AXa, 19)) // 3
    car |= (AXa <= AR_X) & (Z >= AR_Z0) & (Z <= AR_Z1) & (Y >= 1) & (Y < ry)
    car |= (AXa <= AR_X) & (Z > AR_Z1) & (Z <= 58) & (Y >= 8) & (Y < ry)
    # alcoves of the three generators in the north wall
    for c in ALCOVES:
        car |= (np.abs(X - c) <= 3) & (Z >= 4) & (Z <= 11) & (Y >= 1) & (Y <= 10)
    # passages: Hall II -> chamber (east, open), chamber -> Hall I (west, iron door); vault and its windows
    car |= (AXa >= 19) & (AXa <= 26) & (Z >= 34) & (Z <= 36) & (Y >= 1) & (Y <= 4)
    car |= (AXa <= 6) & (Z >= 54) & (Z <= 57) & (Y >= 1) & (Y <= 5)
    car |= (AXa <= 1) & ((Z == 51) | (Z == 53)) & (Y >= 1) & (Y <= 3)
    sol &= ~car
    # exposure: open air (not the powerhouse, not the dam / rock) within 2 blocks
    i0, k0 = PB_X0 - AX0, PB_Z0 - AZ0
    S = P.S[i0:i0 + len(xs), :PB_Y1 + 1, k0:k0 + len(zs)]
    open_ = (~sol & ~S) | car
    near = open_.copy()
    for _ in range(2):
        n = near.copy()
        n[1:, :, :] |= near[:-1, :, :]
        n[:-1, :, :] |= near[1:, :, :]
        n[:, 1:, :] |= near[:, :-1, :]
        n[:, :-1, :] |= near[:, 1:, :]
        n[:, :, 1:] |= near[:, :, :-1]
        n[:, :, :-1] |= near[:, :, 1:]
        near = n
    return xs, zs, sol, car, sol & near


def ph_block(x, y, z):
    ax = abs(x)
    h = hash3(x, y, z, 37)
    if y == 0:
        return floor_tile(x, y, z) if (ax <= 42 and 8 <= z <= 58) else dark_masonry(x, y, z)
    if y <= 2:
        return dark_masonry(x, y, z)
    if ax in (43, 44) and z in (59, 60) or (ax in (26, 27) and z in (59, 60)):
        return PA if h < 0.8 else SB                 # quoins
    if y in (10, 19) or (y == 27 and 19 <= ax <= 26):
        return PA
    if y in (18,) and 27 <= ax <= 42 and 10 <= z <= 58:
        return IRON
    return brick(x, y, z)


def powerhouse_mass(bp, P):
    xs, zs, sol, car, shell = ph_volume(P)
    for i, y, k in np.argwhere(car).tolist():
        bp.set(int(xs[i]), y, int(zs[k]), "air")
    for i, y, k in np.argwhere(shell).tolist():
        bp.set(int(xs[i]), y, int(zs[k]), ph_block(int(xs[i]), y, int(zs[k])))


def ph_roofs(bp):
    """The copper gable over the turbine chamber with a glazed monitor on the ridge; flat roofs with crenellated
    parapets over the halls; pinnacle buttresses framing the gable."""
    for x in range(-20, 21):
        y = roof_y(x)
        for z in range(5, 62):
            if in_dam(x, y, z) or in_dam(x, y + 3, z):
                continue
            mon = 8 <= z <= 58
            if abs(x) <= 1 and mon:
                for yy in (y, y + 1):
                    bp.set(x, yy, z, "air")
                bp.set(x, y + 2, z, COPPER if x == 0 else f"{W}copper_plating_slab[type=bottom,waterlogged=false]")
            elif abs(x) <= 1:
                for yy in (y, y + 1, y + 2):
                    bp.set(x, yy, z, COPPER)
            elif abs(x) == 2:
                bp.set(x, y, z, VERD)
                bp.set(x, y + 1, z, "glass_pane" if mon and z % 4 else COPPER)
                bp.set(x, y + 2, z, "glass_pane" if mon and z % 4 else COPPER)
                bp.set(x, y + 3, z, stair(COPPER_STAIRS, "east" if x < 0 else "west"))
            elif y == roof_y(x + (1 if x < 0 else -1)):
                bp.set(x, y, z, VERD)
            else:
                bp.set(x, y, z, stair(VERD_STAIRS, "east" if x < 0 else "west"))
    # crenellated parapets on the hall roofs and along the wall zones' tops
    for s in (-1, 1):
        for z in range(6, 61):
            for ax in (44,):
                x = s * ax
                if not in_dam(x, 20, z):
                    bp.set(x, 20, z, SB)
                    if z % 2 == 0:
                        bp.set(x, 21, z, SB_SL.replace("slab", "slab") + "[type=bottom,waterlogged=false]")
        for ax in range(27, 45):
            x = s * ax
            bp.set(x, 20, 60, SB)
            if ax % 2 == 0:
                bp.set(x, 21, 60, SB_SL + "[type=bottom,waterlogged=false]")
        for ax in range(19, 27):
            x = s * ax
            for z in range(6, 61):
                if not in_dam(x, 28, z) and bp.get(x, 28, z) is None:
                    bp.set(x, 28, z, PA if ax in (19, 26) else SB)
        # roof walks on the halls: tread and skylights
        for ax in range(27, 43):
            for z in range(10, 59):
                x = s * ax
                if not in_dam(x, 19, z):
                    bp.set(x, 19, z, "glass" if (ax in (33, 34, 35, 36) and z % 6 in (1, 2, 3)) else IRON)
    # pinnacle buttresses on the facade
    for s in (-1, 1):
        for cx, top in ((s * 23, 31), (s * 35, 21), (s * 44, 22)):
            for x in range(cx - 1, cx + 2):
                for z in (61, 62):
                    for y in range(0, top + 1):
                        bp.set(x, y, z, dark_masonry(x, y, z) if y <= 2 else (PA if y % 9 == 0 else masonry(x, y, z)))
                bp.set(x, top + 1, 62, stair(SB_ST, "north"))
                bp.set(x, top + 1, 61, SB)
            if top > 25:
                steep_pyramid(bp, cx - 1, 60, cx + 1, 62, top + 2, PA, PA_ST, steep=2, overhang=0,
                              finial="lightning_rod")
            else:
                bp.set(cx, top + 2, 61, "brasshaven:edison_lamp")


def ph_facade(bp):
    """South facade: tall arched windows in the halls, the gear rose over the chamber, the vault door, culverts."""
    for s in (-1, 1):
        for c in (s * 31, s * 39):
            for x in range(c - 1, c + 2):
                for y in range(4, 16):
                    if y == 15 and x != c:
                        continue
                    bp.set(x, y, 60, "glass_pane")
                    bp.set(x, y, 59, "air")
                bp.set(x, 3, 61, stair(SB_ST, "north", "top"))
            bp.set(c, 16, 60, PA)
        # windows in the long side walls (west and east), three bays
        for z in (18, 30, 42, 52):
            for zz in range(z - 1, z + 2):
                for y in range(6, 14):
                    bp.set(s * 44, y, zz, "glass_pane")
                    bp.set(s * 43, y, zz, "air")
    # the gear rose
    cx, cy = 0, 17
    for x in range(-7, 8):
        for y in range(cy - 7, cy + 8):
            d = math.hypot(x, y - cy)
            a = math.atan2(y - cy, x)
            if d <= 5.6:
                spoke = abs(math.sin(a * 4)) < 0.22 and d > 1.5
                ring = 2.6 < d <= 3.4
                bp.set(x, y, 60, BRASS if (spoke or ring or d <= 1.5) else "orange_stained_glass_pane")
                bp.set(x, y, 59, "air")
            elif d <= 7.2 and math.cos(a * 12) > 0.2:
                bp.set(x, y, 60, GEAR)
                bp.set(x, y, 61, GEAR) if d > 6.4 else None
            elif d <= 6.6:
                bp.set(x, y, 60, BRASS)
    # the vault door (iron, its lever inside) and its frame
    for y in (1, 2):
        bp.set(0, y, 59, "air")
        bp.set(0, y, 60, "air")
    bp.door(0, 1, 58, "south", wood="iron")
    lever(bp, 1, 2, 57, "north")
    for x in (-1, 1):
        for y in range(1, 4):
            bp.set(x, y, 61, PA)
    bp.set(0, 3, 61, stair(PA_ST, "south", "top"))
    bp.set(0, 4, 61, BRASS)
    for x in (-2, 2):
        bp.set(x, 3, 61, EDISON)
    # culverts of the tailrace under the halls (recesses with bars and water)
    for c in (-13, 13):
        for x in range(c - 2, c + 3):
            for y in range(-2, 3):
                top = y == 2 and abs(x - c) == 2
                if top:
                    continue
                bp.set(x, y, 60, BARS_W if y > 0 else "water")
                bp.set(x, y, 59, "water" if y <= 0 else "air")
            for z in (58, 59, 60):
                bp.set(x, -3, z, "mud_bricks")
            for y in range(-2, 1):
                bp.set(x, y, 58, "mud_bricks")
        for x in (c - 3, c + 3):
            for y in range(-3, 3):
                for z in (59, 60):
                    bp.set(x, y, z, dark_masonry(x, y, z))
        bp.set(c, 3, 61, stair(PA_ST, "south", "top"))


BARS_W = "iron_bars[waterlogged=false]"


def generator(bp, cx, z0, z1, broken=False):
    """A horizontal generator set along z: a copper drum r 3 with brass bands on an iron bed, gears at both ends,
    an exciter box on top and a cable duct to the ceiling."""
    cy = 4
    for z in range(z0, z1 + 1):
        for x in range(cx - 4, cx + 5):
            for y in range(1, 8):
                d = math.hypot(x - cx, y - cy)
                if y == 1 and abs(x - cx) <= 3:
                    bp.set(x, y, z, IRON)
                elif d <= 3.2:
                    if broken and (z - z0) % 5 in (2, 3) and d < 2.4:
                        bp.set(x, y, z, "air")
                    elif (z - z0) % 3 == 0:
                        bp.set(x, y, z, BRASS)
                    else:
                        bp.set(x, y, z, COPPER if d > 2.2 else IRON)
    for z in (z0 - 1, z1 + 1):
        gear_disc(bp, cx, cy, z, 3, "z")
    for x in range(cx - 1, cx + 2):
        for z in range(z0 + 2, z0 + 5):
            bp.set(x, 8, z, IRON_BR)
        bp.set(x, 9, z0 + 3, GAUGE if x == cx else IRON_SLAB + "[type=bottom,waterlogged=false]")
    for y in range(9, HALL_TOP + 1):
        bp.set(cx, y, z1 - 1, PIPES)


def hall_lamps(bp, xs, z0, z1, top, step=8):
    for x in xs:
        for z in range(z0, z1 + 1, step):
            if is_air(bp, x, top, z) and is_air(bp, x, top - 1, z) and is_air(bp, x, top - 2, z):
                hang(bp, x, top, z, 2)


def gantry(bp, x0, x1, z, y):
    """An overhead crane: rails along both side walls, a beam across, a hook on a chain."""
    for x in range(x0, x1 + 1):
        bp.set(x, y, z, IRON_BR if x in (x0, x1) else IRON)
        bp.set(x, y, z + 1, IRON_SLAB + "[type=top,waterlogged=false]")
    hx = (x0 + x1) // 2
    for y2 in range(y - 1, y - 5, -1):
        bp.set(hx, y2, z, CHAIN)
    bp.set(hx, y - 5, z, IRON)
    bp.set(hx, y - 6, z, "iron_bars[waterlogged=false]")


def hall_one(bp):
    """Generator Hall I (the lobby, west): the yard portal with its wicket, two generator sets, the crane, the
    workers' benches, a passage to the west tower and, at the north end, the lift's iron door."""
    generator(bp, -35, 18, 27)
    generator(bp, -35, 40, 49)
    gantry(bp, -42, -27, 33, 15)
    hall_lamps(bp, (-40, -30), 12, 56, HALL_TOP)
    # the yard portal: a 7 x 11 bay door of iron plates in the west wall, a wicket in the middle
    for z in range(43, 50):
        for y in range(1, 12):
            arch = y == 11 and z in (43, 49)
            bp.set(-44, y, z, PA if arch else (IRON if (z + y) % 4 else IRON_BR))
            bp.set(-43, y, z, "air")
        bp.set(-45, 12, z, stair(PA_ST, "west", "top"))
        bp.set(-45, 0, z, PA)
    for y in range(1, 12):
        bp.set(-45, y, 42, PA)
        bp.set(-45, y, 50, PA)
    bp.set(-44, 1, 46, "air")
    bp.set(-44, 2, 46, "air")
    bp.door(-44, 1, 46, "west", wood="spruce")
    bp.set(-45, 3, 45, EDISON)
    bp.set(-45, 3, 47, EDISON)
    # benches, lockers, supplies
    for z in range(12, 17):
        bp.set(-42, 1, z, TABLE if z % 2 else "crafting_table")
    bp.chest(-42, 1, 17, "east", loot=LOOT + "dd_works")
    for z in (52, 53, 55):
        bp.barrel(-42, 1, z, "up")
    bp.barrel(-28, 1, 56, "up")
    bp.barrel(-28, 2, 56, "up")
    bp.chest(-28, 1, 30, "west", loot=LOOT + "dd_works")
    for z in range(36, 40):
        bp.set(-27, 1, z, "spruce_planks")
        bp.set(-27, 2, z, "spruce_trapdoor[facing=west,half=bottom,open=false,waterlogged=false]")
    for z in (14, 26, 38, 50):
        bp.set(-42, 7, z, f"{W}wall_cog[facing=east]")
        bp.set(-27, 7, z, f"{W}wall_cog[facing=west]")
    bp.spawner(-35, 1, 33, MOB_SPIDER)
    bp.spawner(-35, 1, 55, MOB_DRONE)
    bp.spawner(-31, 1, 33, W + "turbine_automaton")
    # the passage to the west tower (3 wide)
    for x in range(-46, -42):
        for z in range(31, 34):
            bp.set(x, 0, z, PA)
            for y in range(1, 4):
                bp.set(x, y, z, "air")
        for z in (30, 34):
            for y in range(0, 5):
                bp.set(x, y, z, masonry(x, y, z))
        for z in range(30, 35):
            bp.set(x, 4, z, masonry(x, 4, z))


def hall_two(bp):
    """Generator Hall II (east): one generator still standing, the second stripped for parts, the fitters'
    workshop, the site of grace before the boss, the narrow passage to the turbine chamber."""
    generator(bp, 35, 18, 27)
    generator(bp, 35, 42, 49, broken=True)
    gantry(bp, 27, 42, 33, 15)
    hall_lamps(bp, (30, 40), 12, 56, HALL_TOP)
    # spare parts on the floor: gear panels, plates, an anvil, a grindstone
    for (x, z) in ((30, 38), (31, 38), (30, 39), (40, 36), (40, 37), (39, 36)):
        bp.set(x, 1, z, GEAR)
    bp.set(31, 2, 38, GEAR)
    bp.set(41, 1, 40, "anvil[facing=north]")
    bp.set(41, 1, 44, "smithing_table")
    bp.set(41, 1, 45, "grindstone[face=floor,facing=north]")
    bp.chest(42, 1, 12, "west", loot=LOOT + "dd_turbine")
    bp.chest(27, 1, 47, "east", loot=LOOT + "dd_turbine")
    for z in (14, 15, 16):
        bp.barrel(42, 1, z, "up")
    for z in (14, 26, 50):
        bp.set(42, 7, z, f"{W}wall_cog[facing=west]")
        bp.set(27, 7, z, f"{W}wall_cog[facing=east]")
    bp.spawner(35, 1, 33, MOB_SPIDER)
    bp.spawner(35, 1, 13, MOB_DRONE)
    bp.spawner(31, 1, 33, W + "turbine_automaton")
    # the site of grace in the south bay, benches round it
    bp.set(38, 1, 55, MOD["waystone"])
    for x in (36, 40):
        bp.set(x, 1, 57, stair(MAHOGANY_STAIRS, "north"))
    bp.set(38, 4, 57, EDISON)
    # the passage to the chamber: lamps, a gauge plaque
    bp.set(27, 4, 33, EDISON)
    bp.set(27, 4, 37, EDISON)


def tyrant_floor(bp):
    """The Turbine Tyrant's chamber floor: eight 3 x 3 copper grates over the steam mains on a ring 12 blocks round
    the seal (the boss finds them and blows them), and four cast-iron columns on the diagonals (2 x 2, 13 high) to
    hide behind from his pressure blast."""
    ax, az = AC
    for k in range(8):
        a = math.pi * 2 * k / 8
        gx, gz = round(ax + 12 * math.cos(a)), round(az + 12 * math.sin(a))
        for x in range(gx - 1, gx + 2):
            for z in range(gz - 1, gz + 2):
                bp.set(x, 0, z, "waxed_exposed_copper_grate")
    for sx in (-1, 1):
        for z0 in (20, 41):
            xs = (10, 11) if sx > 0 else (-11, -10)
            for x in xs:
                for z in (z0, z0 + 1):
                    bp.set(x, 0, z, IRON_BR)
                    for y in range(1, 14):
                        bp.set(x, y, z, BRASS if y in (4, 9) else (IRON_BR if y in (1, 12, 13) else PA))
            bp.set(xs[0] if sx > 0 else xs[1], 14, z0, LANT)


def arena(bp):
    """The main turbine chamber: three vertical generators in alcoves of the north wall under the Great Gear, gears
    on the side walls, a gantry crane, a brass gear inlaid in the floor round the boss seal; the vault behind sealed
    bars in the south wall; mists across both passages."""
    ax, az = AC
    # floor inlay
    for x in range(-AR_X, AR_X + 1):
        for z in range(AR_Z0, AR_Z1 + 1):
            d = math.hypot(x - ax, z - az)
            a = math.atan2(z - az, x - ax)
            if 8.5 <= d < 9.5 or (9.5 <= d < 10.5 and math.cos(a * 16) > 0.3) or 13.5 <= d < 14.2:
                bp.set(x, 0, z, BRASS)
            elif d < 8.5 and (abs(x - ax) <= 0 or abs(z - az) <= 0):
                bp.set(x, 0, z, IRON_BR)
            elif d < 2:
                bp.set(x, 0, z, BRASS_T)
    tyrant_floor(bp)
    # alcove generators
    for c in ALCOVES:
        for x in range(c - 3, c + 4):
            for z in range(4, 12):
                bp.set(x, 0, z, TREAD)
        for x in range(c - 3, c + 4):
            for z in range(4, 11):
                for y in range(1, 7):
                    d = math.hypot(x - c, z - 7)
                    if d <= 2.6:
                        bp.set(x, y, z, BRASS if y in (1, 4) else COPPER)
                    elif d <= 3.2 and y == 1:
                        bp.set(x, y, z, IRON)
        for y in range(7, 11):
            bp.set(c, y, 7, IRON)
        gear_disc(bp, c, 9, 7, 2, "y")
        for y in range(1, 11):
            bp.set(c, y, 4, PIPES if y % 3 else BRASS)
        bp.set(c - 3, 5, 11, EDISON)
        bp.set(c + 3, 5, 11, EDISON)
        for x in (c - 3, c + 3):
            bp.set(x, 11, 12, stair(PA_ST, "south", "top"))
    # the Great Gear on the north wall over the alcoves, the side gears
    gear_disc(bp, 0, 18, 12, 7, "z", keep_air=True)
    for s in (-1, 1):
        for zc in (22, 44):
            gear_disc(bp, s * AR_X, 13, zc, 5, "x", keep_air=True)
        for z in range(AR_Z0, 59):
            bp.set(s * AR_X, 20, z, IRON_SLAB + "[type=top,waterlogged=false]")
    gantry(bp, -AR_X, AR_X, 30, 21)
    # trusses under the roof
    for z in range(14, 59, 7):
        for x in range(-AR_X, AR_X + 1):
            y = roof_y(x) - 1
            if is_air(bp, x, y, z):
                bp.set(x, y, z, IRON)
        for x in (-12, -6, 6, 12):
            y = roof_y(x) - 2
            bp.set(x, y, z, HANG_LAMP)
    for (x, z) in ((-12, 20), (12, 20), (-12, 42), (12, 42), (0, 50)):
        for y in range(roof_y(x) - 1, 15, -1):
            if is_air(bp, x, y, z):
                bp.set(x, y, z, CHAIN)
        bp.set(x, 15, z, W + "brass_chandelier")
    # wall lamps low down so the floor is lit
    for s in (-1, 1):
        for z in (16, 28, 40, 48):
            bp.set(s * (AR_X + 1), 4, z, EDISON)
    # the balcony over the vault (railing) and the vault
    for x in range(-AR_X, AR_X + 1):
        bp.set(x, 8, 51, f"{RAIL}[facing=north]")
    for x in range(-1, 2):
        for y in range(1, 4):
            bp.set(x, y, 52, MOD["vault_bars"])
    for x in range(-6, 7):
        for z in range(54, 58):
            bp.set(x, 0, z, BRASS_T if (x + z) % 2 else IRON_BR)
    bp.chest(-5, 1, 55, "east", loot=LOOT + "dd_vault")
    bp.chest(5, 1, 55, "west", loot=LOOT + "dd_vault")
    bp.chest(-5, 1, 57, "east", loot=LOOT + "dd_vault")
    for x in (-3, 3):
        bp.set(x, 1, 54, GEAR)
        bp.set(x, 2, 54, LANT)
    hang(bp, 0, 5, 55, 1)
    # the passages: east open (mist), west closed by an iron door with its lever on the chamber side (mist)
    for z in range(34, 37):
        for x in range(19, 27):
            bp.set(x, 0, z, PA)
            bp.set(-x, 0, z, PA)
    for y in range(1, 5):
        for z in (34, 36):
            bp.set(-26, y, z, masonry(-26, y, z))
    for y in (3, 4):
        bp.set(-26, y, 35, masonry(-26, y, 35))
    bp.door(-26, 1, 35, "west", wood="iron")
    lever(bp, -25, 2, 34, "south")
    bp.set(-25, 2, 33, SB)
    bp.mist(19, 1, 34, 19, 4, 36)
    bp.mist(-19, 1, 34, -19, 4, 36)
    bp.boss_seal(ax, 0, az, BOSS, 17)


# ------------------------------------------------------------------ the sentinel towers
TW_FLIGHTS = [4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3]     # 36 to the berm, 30 more to the crest


def tower_block(x, y, z, x0, x1):
    h = hash3(x, y, z, 43)
    corner = x in (x0, x1) and z in (TW_Z0, TW_Z1)
    if y <= 3:
        return dark_masonry(x, y, z)
    if y % 12 == 0:
        return BRASS if not corner else PA
    if corner:
        return PA if (y // 2) % 2 else SB
    return LADDER[max(0, min(6, int(1.5 + (1 - y / TW_TOP) * 2.2 + (h - 0.5) * 1.4)))]


def sentinel_tower(bp, s):
    """A square tower 13 x 13 standing free in front of the dam face, 72 high, a newel stair inside from the ground
    to the crest; doors: the ground (the powerhouse side and the yard), the berm gangway (feet 37), the crest
    bridge (feet 67). West: s = -1 (the way up), east: s = 1 (the way down to Hall II)."""
    x0, x1 = (46, 58) if s > 0 else (-58, -46)
    z0, z1 = TW_Z0, TW_Z1
    # plinth one block wider, then the shaft
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            if edge:
                for y in range(-2, 3):
                    bp.set(x, y, z, dark_masonry(x, y, z))
                bp.set(x, 3, z, stair(SB_ST, out_facing(x - (x0 + x1) / 2, z - (z0 + z1) / 2)))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(0, TW_TOP + 1):
                if wall:
                    bp.set(x, y, z, tower_block(x, y, z, x0, x1))
                elif y == 0:
                    bp.set(x, y, z, PA)
                else:
                    bp.set(x, y, z, "air")
    # newel stair (k = 5), corner landings at the doors
    if s < 0:
        cells, core, c, f = newel_laps(bp, x0 + 1, z0 + 1, 5, 1, TW_FLIGHTS, 2, cw=True)
        north_door = (x0 + 1, x0 + 3)            # the NW landing
        ground = (x1 - 3, x1 - 1)                # the SE landing
    else:
        cells, core, c, f = newel_laps(bp, x0 + 1, z0 + 1, 5, 1, TW_FLIGHTS, 3, cw=False)
        north_door = (x1 - 3, x1 - 1)            # the NE landing
        ground = (x0 + 1, x0 + 3)                # the SW landing
    # ground doors: toward the powerhouse (side wall) and the outside (south wall)
    side_x = x1 if s < 0 else x0
    for z in range(z1 - 3, z1):
        for y in range(1, 4):
            bp.set(side_x, y, z, "air")
    for x in range(ground[0], ground[1] + 1):
        for y in range(1, 5):
            bp.set(x, y, z1, "air")
    gx = (ground[0] + ground[1]) // 2
    if s > 0:
        # the east tower's outer door is one way: iron, its lever inside
        for x in range(ground[0], ground[1] + 1):
            for y in range(1, 5):
                if x != gx or y > 2:
                    bp.set(x, y, z1, tower_block(x, y, z1, x0, x1))
        bp.door(gx, 1, z1, "south", wood="iron")
        lever(bp, gx + 1, 2, z1 - 1, "north")
    else:
        bp.set(gx, 5, z1, stair(PA_ST, "south", "top"))
    bp.set(gx - 2, 4, z1 + 1, EDISON)
    bp.set(gx + 2, 4, z1 + 1, EDISON)
    # north doors at the berm (37) and the crest (67)
    for fy in (BF, CF):
        for x in range(north_door[0], north_door[1] + 1):
            for y in range(fy, fy + 3):
                bp.set(x, y, z0, "air")
        bp.set((north_door[0] + north_door[1]) // 2, fy + 3, z0, BRASS)
    # slit windows in the outer walls (not in the wall against the dam below the berm)
    for y in range(8, TW_TOP - 6, 7):
        for (x, z) in ((x0, (z0 + z1) // 2), (x1, (z0 + z1) // 2), ((x0 + x1) // 2, z1), ((x0 + x1) // 2, z0)):
            if z == z0 and y < 40:
                continue
            for dy in (0, 1):
                if bp.get(x, y + dy, z) not in ("minecraft:air",):
                    bp.set(x, y + dy, z, "glass_pane")
    # crown: corbels, a parapet with merlons, the steep verdigris roof
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            if not edge:
                continue
            bp.set(x, TW_TOP - 1, z, stair(SB_ST, OPP[out_facing(x - (x0 + x1) / 2, z - (z0 + z1) / 2)], "top"))
            bp.set(x, TW_TOP, z, PA)
            bp.set(x, TW_TOP + 1, z, SB)
            if (x + z) % 2 == 0:
                bp.set(x, TW_TOP + 2, z, SB)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, TW_TOP, z, PA if (x + z) % 2 else SB)
    steep_pyramid(bp, x0 + 2, z0 + 2, x1 - 2, z1 - 2, TW_TOP + 1, VERD, VERD_STAIRS, steep=2, overhang=0,
                  finial="lightning_rod")
    # a little loot on the landings
    bp.barrel(gx - 1 if s < 0 else gx + 1, 1, z1 - 2 if s < 0 else z1 - 2, "up")
    return cells


def gangways(bp):
    """Bridges from the towers' north doors: to the berm (feet 37) and to the crest (feet 67, a flying bridge on an
    iron truss)."""
    for s in (-1, 1):
        xs = range(-57, -54) if s < 0 else range(55, 58)
        for fy, zstop in ((BF, None), (CF, None)):
            for x in xs:
                z = TW_Z0 - 1
                while z > -20:
                    r = rad(x, z)
                    if fy == BF and r >= 125.0:
                        break
                    if fy == CF and r >= R_CR:
                        break
                    edge = x in (xs[0], xs[-1])
                    bp.set(x, fy - 1, z, PA if not edge else TB)
                    for y in range(fy, fy + 4):
                        bp.set(x, y, z, "air")
                    if edge:
                        bp.set(x, fy, z, f"{RAIL}[facing={'west' if x == xs[0] else 'east'}]")
                    if fy == CF:
                        bp.set(x, fy - 2, z, IRON_SLAB + "[type=top,waterlogged=false]" if not edge else IRON)
                        if z % 4 == 0 and edge:
                            for y in range(fy - 5, fy - 2):
                                bp.set(x, y, z, IRON_WALL)
                    z -= 1
            # open the crest parapet where the bridge lands
            if fy == CF:
                for x in xs:
                    for z in range(-20, TW_Z0):
                        if R_CR <= rad(x, z) < R_CR + 1.0:
                            bp.set(x, CF, z, "air")
                            bp.set(x, CF + 1, z, "air")
                            bp.set(x, CREST, z, PA)
            else:
                for x in xs:
                    for z in range(-10, TW_Z0):
                        if 125.0 <= rad(x, z) < 126.0:
                            bp.set(x, BF, z, "air")


# ------------------------------------------------------------------ the control tower
CT_FLIGHTS = [8, 7, 8, 7]


def ct_block(x, y, z):
    h = hash3(x, y, z, 47)
    corner = x in (CT_X0, CT_X1) and z in (CT_Z0, CT_Z1)
    if y in (CF - 1, CT_ROOM - 1, CT_LOFT - 1) or y % 12 == 0:
        return BRASS if not corner else PA
    if corner or x in (CT_X0, CT_X1) and z in (CT_Z0 + 1, CT_Z1 - 1) or z in (CT_Z0, CT_Z1) and x in (CT_X0 + 1,
                                                                                                    CT_X1 - 1):
        return PA if (y // 2) % 2 else SB
    return "smooth_stone" if h < 0.35 else (PA if h < 0.7 else SB)


def control_tower(bp):
    """Square tower 18 x 18 riding the middle of the crest, from the berm (floor 36) to the roof walk (89): the
    newel stair from the berm and the valve house up to the crest hall (feet 67, the crest road passes through
    under two pointed arches), a straight stair to the control room (feet 75, the site of grace, windows on both
    sides), the gauge loft (83) with the dials, a roof walk, corner bartizans and a verdigris lantern spire."""
    x0, x1, z0, z1 = CT_X0, CT_X1, CT_Z0, CT_Z1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x <= x0 + 1 or x >= x1 - 1 or z <= z0 + 1 or z >= z1 - 1
            for y in range(BERM, CT_ROOF + 1):
                if wall:
                    bp.set(x, y, z, ct_block(x, y, z))
                elif y in (BERM, CREST, CT_ROOM - 1, CT_LOFT - 1, CT_ROOF):
                    bp.set(x, y, z, floor_tile(x, y, z) if y != CT_ROOF else PA)
                else:
                    bp.set(x, y, z, "air")
    # newel (k = 8) from the berm (feet 37, SW landing) to the crest hall (feet 67, SW landing)
    cells, core, c, f = newel_laps(bp, x0 + 2, z0 + 2, 8, BF, CT_FLIGHTS, 3, cw=True)
    # open the crest hall floor over the last flight's high steps, a railing round the opening
    for (x, z), vs in cells.items():
        for (ff, fc, i) in vs:
            if CREST - 3 <= ff <= CREST:
                bp.set(x, CREST, z, "air")
    for (x, z), vs in cells.items():
        for (ff, fc, i) in vs:
            if CREST - 3 <= ff <= CREST:
                for dx, dz in ((0, -1), (1, 0), (-1, 0), (0, 1)):
                    q = (x + dx, CREST, z + dz)
                    if not is_air(bp, *q) and bp.get(x + dx, CF, z + dz) == "minecraft:air" and \
                            (x + dx, z + dz) not in cells:
                        bp.set(x + dx, CF, z + dz, f"{RAIL}[facing={OPP[out_facing(dx, dz)]}]")
    # doors at the berm: south wall onto the berm, west wall into the valve house passage
    for x in range(x0 + 2, x0 + 5):
        for y in range(BF, BF + 3):
            bp.set(x, y, z1, "air")
            bp.set(x, y, z1 - 1, "air")
    bp.set(x0 + 3, BF + 3, z1, BRASS)
    for z in (z1 - 4, z1 - 3):
        for y in range(BF, BF + 3):
            for x in (x0, x0 + 1):
                bp.set(x, y, z, "air")
    # crest arches (west and east) for the road: 6 wide, pointed
    for x in (x0, x0 + 1, x1 - 1, x1):
        for z in range(-12, -6):
            top = CF + 5 - (1 if z in (-12, -7) else 0)
            for y in range(CF, top + 1):
                bp.set(x, y, z, "air")
            bp.set(x, CREST, z, PA)
        bp.set(x, CF + 6, -10, CH)
        bp.set(x, CF + 6, -9, CH)
    # crest hall: lamps, a bench, the stair up to the control room along the north wall (climbing east)
    for i in range(8):
        x = -4 + i
        for z in range(z0 + 2, z0 + 5):
            bp.set(x, CF + i, z, stair(SB_ST, "east"))
            for y in range(CF, CF + i):
                bp.set(x, y, z, SB)
            for y in range(CF + i + 1, CF + i + 5):
                bp.set(x, y, z, "air")
    for z in range(z0 + 2, z0 + 5):
        for y in range(CF, CT_ROOM):
            bp.set(4, y, z, SB if y < CT_ROOM - 1 else floor_tile(4, y, z))
    for x in range(-1, 4):
        bp.set(x, CT_ROOM, z0 + 5, f"{RAIL}[facing=south]")
    for z in range(z0 + 2, z0 + 6):
        bp.set(-2, CT_ROOM, z, f"{RAIL}[facing=west]")
    hang(bp, -1, CT_ROOM - 2, -9, 2)
    hang(bp, 2, CT_ROOM - 2, -5, 2)
    bp.spawner(4, CF, -4, MOB_DRONE)
    # control room (feet 75): windows over the reservoir (north) and the valley (south), the desk, the grace
    for x in range(x0 + 3, x1 - 2):
        for y in range(CT_ROOM + 2, CT_ROOM + 6):
            if (x - x0) % 4 == 2:
                continue
            for z, inner in ((z0, z0 + 1), (z1, z1 - 1)):
                bp.set(x, y, z, "glass_pane")
                bp.set(x, y, inner, "air")
    for z in range(z0 + 4, z1 - 3):
        for y in range(CT_ROOM + 2, CT_ROOM + 5):
            if (z - z0) % 4 == 2:
                continue
            for x, inner in ((x0, x0 + 1), (x1, x1 - 1)):
                bp.set(x, y, z, "glass_pane")
                bp.set(x, y, inner, "air")
    # the control desk along the south windows (the valley and the powerhouse below)
    for x in range(-4, 5):
        bp.set(x, CT_ROOM, z1 - 2, MAHOGANY if x % 3 else IRON)
        bp.set(x, CT_ROOM + 1, z1 - 2, "lever[face=floor,facing=south,powered=false]" if x % 2 else
               f"{W}brass_plating_slab[type=bottom,waterlogged=false]")
        if x % 3 == 0:
            bp.set(x, CT_ROOM, z1 - 3, f"{W}mahogany_chair[facing=south]")
    for x in (-6, 5):
        for y in range(CT_ROOM, CT_ROOM + 3):
            bp.set(x, y, z0 + 2, PIPES)
        bp.set(x, CT_ROOM + 3, z0 + 2, GAUGE)
    bp.set(-1, CT_ROOM, -6, "cartography_table")
    bp.set(0, CT_ROOM, -6, TABLE)
    bp.set(0, CT_ROOM + 1, -6, LANT)
    bp.set(-6, CT_ROOM, -3, MOD["waystone"])
    bp.chest(-6, CT_ROOM, -9, "east", loot=LOOT + "dd_control")
    bp.set(-6, CT_ROOM, -10, "lectern[facing=east,has_book=false,powered=false]")
    for y in range(CT_ROOM, CT_ROOM + 3):
        bp.set(x0 + 2, y, -6, GAUGE if y == CT_ROOM + 1 else IRON_BR)
    hang(bp, -2, CT_LOFT - 2, -7, 1)
    hang(bp, 2, CT_LOFT - 2, -7, 1, lamp=W + "brass_chandelier")
    # ladder up to the gauge loft and on to the roof walk (south-east corner)
    bp.ladder(x1 - 2, CT_ROOM, z1 - 2, CT_ROOF, "north")
    bp.set(x1 - 2, CT_LOFT - 1, z1 - 2, f"ladder[facing=north,waterlogged=false]")
    bp.set(x1 - 2, CT_ROOF, z1 - 2, f"ladder[facing=north,waterlogged=false]")
    # gauge loft: the dial works, a barrel
    gear_disc(bp, -1, CT_LOFT + 2, z0 + 3, 2, "z")
    gear_disc(bp, -1, CT_LOFT + 2, z1 - 3, 2, "z")
    bp.barrel(x0 + 2, CT_LOFT, z0 + 2, "up")
    hang(bp, -1, CT_ROOF - 1, -6, 1)
    # the dials on the north and south faces
    for z, out in ((z0 - 1, -1), (z1 + 1, 1)):
        cx, cy = -1, CT_LOFT + 2
        for x in range(cx - 4, cx + 5):
            for y in range(cy - 4, cy + 5):
                d = math.hypot(x - cx, y - cy)
                if d <= 3.2:
                    hand = (x == cx and cy <= y <= cy + 3) or (y == cy and cx <= x <= cx + 2)
                    bp.set(x, y, z, IRON if hand else "white_concrete")
                elif d <= 4.3:
                    bp.set(x, y, z, BRASS)
    # crown: corbels, crenellated parapet, bartizans, the lantern spire
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, CT_ROOF - 1, z, stair(SB_ST, OPP[out_facing(x - (x0 + x1) / 2, z - (z0 + z1) / 2)], "top"))
                bp.set(x, CT_ROOF, z, PA)
                bp.set(x, CT_ROOF + 1, z, SB)
                if (x + z) % 2 == 0:
                    bp.set(x, CT_ROOF + 2, z, SB)
    for (cx, cz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                for y in range(CT_ROOF - 4, CT_ROOF + 5):
                    bp.set(x, y, z, PA if y % 3 == 0 else SB)
                bp.set(x, CT_ROOF - 5, z, stair(SB_ST, OPP[out_facing(x - cx, z - cz)] if (x, z) != (cx, cz)
                                                else "north", "top"))
        steep_pyramid(bp, cx - 1, cz - 1, cx + 1, cz + 1, CT_ROOF + 5, VERD, VERD_STAIRS, steep=2, overhang=0,
                      finial="lightning_rod")
    lx0, lz0, lx1, lz1 = -4, -10, 3, -3
    for x in range(lx0, lx1 + 1):
        for z in range(lz0, lz1 + 1):
            edge = x in (lx0, lx1) or z in (lz0, lz1)
            for y in range(CT_ROOF + 1, CT_ROOF + 6):
                if edge:
                    arch = y < CT_ROOF + 4 and (x in (lx0 + 2, lx0 + 3, lx1 - 3, lx1 - 2) or
                                                z in (lz0 + 2, lz0 + 3, lz1 - 3, lz1 - 2))
                    bp.set(x, y, z, "air" if arch else (BRASS if y == CT_ROOF + 5 else PA))
                else:
                    bp.set(x, y, z, "air")
    bp.set(-1, CT_ROOF + 1, -7, GEAR)
    bp.set(-1, CT_ROOF + 2, -7, "bell[attachment=floor,facing=north,powered=false]")
    top = steep_pyramid(bp, lx0, lz0, lx1, lz1, CT_ROOF + 6, VERD, VERD_STAIRS, steep=2, overhang=1)
    for y in range(top, top + 4):
        bp.set(-1, y, -7, IRON_WALL if y < top + 3 else "lightning_rod")
    bp.set(-1, top, -6, IRON_WALL)


# ------------------------------------------------------------------ the valve house and the drowned gallery
VH_X0, VH_X1, VH_Z0, VH_Z1 = -23, -12, -10, -1      # interior, feet 37, air up to 48


def valve_house(bp):
    """The valve house: a pedimented front on the berm, inside the dam a hall of two penstocks with their valve
    wheels and gauges, the fitters' bench; a stair up the north wall to the drowned gallery; a passage east into
    the control tower."""
    shell_room(bp, VH_X0, BF, VH_Z0, VH_X1, BF + 11, VH_Z1, masonry, floor=floor_tile, ceil=SB)
    # the front on the berm (z = 0): pilasters, cornice, brass pediment, a double door and two windows
    for x in range(VH_X0 - 1, VH_X1 + 2):
        for y in range(BERM, BF + 13):
            bp.set(x, y, 0, PA if x in (VH_X0 - 1, VH_X1 + 1, -18, -17) and y < BF + 10 else masonry(x, y, 0))
        bp.set(x, BF + 10, 1, stair(SB_ST, "north", "top"))
    for x in (VH_X0 - 1, -20, -15, VH_X1 + 1):
        for y in range(BF, BF + 10):
            bp.set(x, y, 1, PA if y % 4 else SB)
    for i, y in enumerate(range(BF + 11, BF + 15)):
        for x in range(-23 + i * 2, -11 - i * 2):
            bp.set(x, y, 0, BRASS if x in (-23 + i * 2, -12 - i * 2) else W + "engraved_brass")
            for z in (-1, -2):
                if not in_dam(x, y, z):
                    bp.set(x, y, z, masonry(x, y, z))
    for x in (-18, -17):
        for y in range(BF, BF + 3):
            bp.set(x, y, 0, "air")
    bp.door(-18, BF, 0, "south", wood="spruce", hinge="left")
    bp.door(-17, BF, 0, "south", wood="spruce", hinge="right")
    bp.set(-18, BF + 3, 0, BRASS)
    bp.set(-17, BF + 3, 0, BRASS)
    for x in (-22, -21, -14, -13):
        for y in (BF + 2, BF + 3):
            bp.set(x, y, 0, "glass_pane")
        bp.set(x, BF + 1, 1, stair(SB_ST, "south", "top"))
    bp.set(-20, BF + 2, 2, EDISON)
    bp.set(-15, BF + 2, 2, EDISON)
    # penstocks and their valve wheels
    for px in (-21, -16):
        for y in range(BERM, BF + 12):
            for x in range(px - 1, px + 2):
                for z in range(-6, -3):
                    bp.set(x, y, z, BRASS if y % 4 == 0 else COPPER)
        bp.set(px, BF + 2, -3, f"{W}valve_wheel[facing=south]")
        bp.set(px, BF + 5, -4, GAUGE)
    # the bench and loot
    for z in range(-3, 0):
        bp.set(VH_X0, BF, z, TABLE if z != -2 else "crafting_table")
    bp.chest(VH_X0, BF, -4, "east", loot=LOOT + "dd_valves")
    bp.barrel(VH_X1, BF, -2, "up")
    bp.spawner(-13, BF, -6, MOB_DRONE)
    hang(bp, -18, BF + 10, -2, 2)
    hang(bp, -14, BF + 10, -7, 2)
    # stair up the north wall to the gallery landing (feet 45, west end)
    for i in range(8):
        x = -13 - i
        for z in range(VH_Z0, VH_Z0 + 3):
            bp.set(x, BF + i, z, stair(SB_ST, "west"))
            for y in range(BERM, BF + i):
                bp.set(x, y, z, SB)
        bp.set(x, BF + i + 1, VH_Z0 + 3, f"{RAIL}[facing=south]")
    for x in range(VH_X0, VH_X0 + 3):
        for z in range(VH_Z0, VH_Z0 + 3):
            for y in range(BERM, BF + 8):
                bp.set(x, y, z, SB if y < BF + 7 else floor_tile(x, y, z))
        bp.set(x, BF + 8, VH_Z0 + 3, f"{RAIL}[facing=south]")
    for z in range(VH_Z0, VH_Z0 + 3):
        for y in range(BF + 8, BF + 11):
            bp.set(VH_X0 - 1, y, z, "air")
    # the passage east into the control tower (2 wide)
    for x in range(VH_X1 + 1, CT_X0 + 2):
        for z in (-2, -1):
            bp.set(x, BERM, z, PA)
            for y in range(BF, BF + 3):
                bp.set(x, y, z, "air")
            bp.set(x, BF + 3, z, SB)
        for y in range(BERM, BF + 4):
            bp.set(x, y, -3, masonry(x, y, -3))
            bp.set(x, y, 0, masonry(x, y, 0))


GF = BF + 8          # gallery feet


def drowned_gallery(bp):
    """A curved gallery along the inside of the upstream face (feet 45), its windows looking into the reservoir at
    the drowned village; at the west end the chapel window, the village register and a memorial."""
    x_end = -48
    for x, z, r, u in arc_cells(x_end - 1, VH_X0 - 1, 139.0, R_UP + 0.01):
        inner = 140.0 <= r < 143.0
        if x == VH_X0 - 1 and not inner:
            continue
        for y in range(GF - 1, GF + 5):
            if inner and GF <= y <= GF + 3 and x >= x_end:
                bp.set(x, y, z, "air")
            elif inner and y == GF - 1:
                bp.set(x, y, z, TREAD if int(u) % 4 else BRASS_T)
            elif x < x_end and inner:
                bp.set(x, y, z, masonry(x, y, z))
            elif r < 140.0 or y in (GF - 1, GF + 4) or r >= 143.0:
                win = r >= 143.0 and GF + 1 <= y <= GF + 2 and int(u) % 5 in (1, 2) and x > x_end + 2
                if win:
                    bp.set(x, y, z, "glass" if r >= 144.0 else "air")
                else:
                    bp.set(x, y, z, dark_masonry(x, y, z) if r >= 143.0 else masonry(x, y, z))
    # lamps along the inner wall
    for x, z, r, u in arc_cells(x_end, VH_X0 - 2, 139.0, 140.0):
        if int(u) % 6 == 0:
            bp.set(x, GF + 2, z, EDISON)
    # the chapel window at the west end: a round window 5 across in the face
    ex = x_end + 1
    zc = int(round(z_at(ex, 144.5)))
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if math.hypot(dx, dy) <= 2.4:
                x, y = ex + dx, GF + 2 + dy
                for z in range(zc - 3, zc + 3):
                    r = rad(x, z)
                    if 142.5 <= r < 145.5:
                        bp.set(x, y, z, "glass" if r >= 144.0 else "air")
    bp.set(x_end + 1, GF, int(round(z_at(x_end + 1, 141.0))), "lectern[facing=north,has_book=false,powered=false]")
    zc2 = int(round(z_at(x_end + 3, 141.5)))
    bp.chest(x_end + 3, GF, zc2, "south", loot=LOOT + "dd_gallery")
    for (dx, rr) in ((5, 141.0), (6, 141.0)):
        bp.set(x_end + dx, GF, int(round(z_at(x_end + dx, rr))), "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(x_end + 7, GF, int(round(z_at(x_end + 7, 140.2))), "potted_blue_orchid")


# ------------------------------------------------------------------ shortcuts: the lift shaft and the spillway
def lift_shaft(bp):
    """The maintenance lift: a shaft 3 x 3 inside the dam from the crest (a hole under the headframe) down to a
    passage into Generator Hall I, closed by an iron door whose lever is on the shaft side (a shortcut from the hub
    back to the lobby). A ladder runs the whole height; the stalled cage hangs at the top."""
    x0, x1, z0, z1 = LS_X0, LS_X1, LS_Z0, LS_Z1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(-1, CREST + 1):
                if wall:
                    bp.set(x, y, z, IRON_BR if y % 8 == 0 else masonry(x, y, z))
                elif y <= 0:
                    bp.set(x, y, z, PA)
                else:
                    bp.set(x, y, z, "air")
    lx = (x0 + x1) // 2
    bp.ladder(lx, 1, z0 + 1, CREST, "south")
    # the cage stuck under the headframe (iron bars sides, a trapdoor floor folded open)
    for y in range(CREST - 9, CREST - 6):
        bp.set(x1 - 1, y, z1 - 1, "iron_bars[waterlogged=false]")
    bp.set(x1 - 1, CREST - 6, z1 - 1, CHAIN)
    for y in range(CREST - 5, CREST + 1):
        bp.set(x1 - 1, y, z1 - 1, CHAIN)
    # the passage south to Hall I and the one-way iron door
    for z in range(z1, 10):
        for x in range(x0 + 1, x1):
            bp.set(x, 0, z, PA)
            for y in range(1, 5):
                bp.set(x, y, z, "air")
        for y in range(0, 6):
            bp.set(x0, y, z, masonry(x0, y, z))
            bp.set(x1, y, z, masonry(x1, y, z))
        for x in range(x0, x1 + 1):
            bp.set(x, 5, z, masonry(x, 5, z))
    for y in range(1, 5):
        for x in (x0 + 1, x1 - 1):
            bp.set(x, y, 9, SB)
    for y in (3, 4):
        bp.set(lx, y, 9, SB)
    bp.door(lx, 1, 9, "south", wood="iron")
    lever(bp, x0 + 1, 2, 8, "north")
    bp.set(lx, 4, 4, EDISON)
    # railing round the hole on the crest (open on the ladder's side)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x in (x0, x1) or z == z1) and not (z == z0):
                bp.set(x, CF, z, f"{RAIL}[facing={out_facing(x - lx, z - (z0 + z1) / 2)}]")


def headframe(bp):
    """The lift's steel headframe over the shaft: four legs braced with bars, a platform and the sheave wheel, a
    back-leg strut to the winch on the crest."""
    x0, x1, z0, z1 = LS_X0 - 1, LS_X1 + 1, LS_Z0 - 1, LS_Z1 + 1
    top = CF + 14
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(CF, top + 1):
            bp.set(x, y, z, BRASS if (y - CF) % 7 == 0 else IRON)
    for y in range(CF + 3, top, 4):
        for x in range(x0 + 1, x1):
            bp.set(x, y, z0, IRON_SLAB + "[type=top,waterlogged=false]")
            bp.set(x, y, z1, IRON_SLAB + "[type=top,waterlogged=false]")
        for z in range(z0 + 1, z1):
            bp.set(x0, y, z, IRON_SLAB + "[type=top,waterlogged=false]")
            bp.set(x1, y, z, IRON_SLAB + "[type=top,waterlogged=false]")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, top + 1, z, IRON if x in (x0, x1) or z in (z0, z1) else TREAD)
    cx = (x0 + x1) // 2
    gear_disc(bp, cx, top + 6, (z0 + z1) // 2, 4, "x")
    for y in range(top + 2, top + 6):
        bp.set(cx, y, (z0 + z1) // 2, IRON)
    # back strut down to the winch (north-east, on the crest)
    for i in range(10):
        bp.set(cx + 1 + i // 2, top - i, z0 - 1 - i // 3, IRON)
    wx, wz = -22, -8
    for x in range(wx - 1, wx + 2):
        for y in range(CF, CF + 3):
            bp.set(x, y, wz, IRON if y != CF + 1 else BRASS)
    bp.set(wx, CF + 3, wz, GEAR)


def spillway(bp):
    """The spillway shaft under the east gatehouse: a round shaft from the crest (66) down to a plunge pool, and the
    spillway tunnel out to the valley floor east of the powerhouse (a one-way shortcut from the crest)."""
    cx, cz = SP_C
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            for y in range(6, CREST + 1):
                if d < SP_R + 0.5:
                    bp.set(x, y, z, "air")
                elif d < SP_R + 1.6:
                    bp.set(x, y, z, BRASS if y % 10 == 0 else dark_masonry(x, y, z))
    # the plunge pool chamber (water y -4..0, air 1..5)
    px0, px1, pz0, pz1 = cx - 5, cx + 5, cz - 5, cz + 5
    for x in range(px0 - 1, px1 + 2):
        for z in range(pz0 - 1, pz1 + 2):
            wall = x in (px0 - 1, px1 + 1) or z in (pz0 - 1, pz1 + 1)
            for y in range(-5, 7):
                if wall or y == -5 or y == 6:
                    if y == 6 and math.hypot(x - cx, z - cz) < SP_R + 0.5:
                        bp.set(x, y, z, "air")
                    else:
                        bp.set(x, y, z, dark_masonry(x, y, z))
                elif y <= 0:
                    bp.set(x, y, z, "water")
                else:
                    bp.set(x, y, z, "air")
    # the tunnel south from the pool to the valley
    z = pz1 + 1
    end = z
    while z < 110:
        if hmap(cx, z + 2) <= 2 and hmap(cx - 3, z + 2) <= 4 and hmap(cx + 3, z + 2) <= 4:
            end = z
            break
        z += 1
    for z in range(pz1 + 1, end + 1):
        for x in range(cx - 4, cx + 5):
            for y in range(-1, 8):
                dx = abs(x - cx)
                inside = dx <= 2 and 1 <= y <= 5 and not (dx == 2 and y == 5)
                lining = dx <= 3 and 0 <= y <= 6 and not inside
                if inside:
                    bp.set(x, y, z, "air")
                elif lining or (dx == 4 and 0 <= y <= 5) or (y in (-1, 7) and dx <= 3):
                    if y == 0 and dx <= 2:
                        bp.set(x, y, z, "gravel" if hash01(x, z, 5) < 0.3 else PA)
                    else:
                        bp.set(x, y, z, masonry(x, y, z))
        if (z - pz1) % 8 == 4:
            bp.set(cx - 2, 3, z, "air")
            bp.set(cx - 3, 3, z, EDISON)
    # the pool's south wall: a step up into the tunnel (the floor at y 0)
    for x in range(cx - 2, cx + 3):
        for y in range(1, 6):
            bp.set(x, y, pz1 + 1, "air")
        bp.set(x, 0, pz1 + 1, PA)
    # the portal: an arch of dressed stone, a stepped apron
    for x in range(cx - 4, cx + 5):
        for y in range(0, 9):
            dx = abs(x - cx)
            if dx <= 2 and 1 <= y <= 5 and not (dx == 2 and y == 5):
                continue
            bp.set(x, y, end + 1, PA if (dx >= 3 or y >= 6) else SB)
        bp.set(x, 9, end + 1, stair(PA_ST, "south"))
        for k in range(1, 4):
            bp.set(x, 0, end + 1 + k, PA if k < 3 else "gravel")
            for y in range(1, 5):
                bp.set(x, y, end + 1 + k, "air")
    for x in range(cx - 2, cx + 3):
        for y in range(1, 6):
            if not (abs(x - cx) == 2 and y == 5):
                bp.set(x, y, end + 1, "air")
    return end


def gatehouse(bp):
    """The east gatehouse at the crest's end, on the abutment: the spillway's gate winches round the open shaft
    (a railing with a gap: the leap), valve wheels, a balcony over the reservoir; a hipped slate roof."""
    x0, x1, z0, z1 = 62, 74, 1, 15
    cx, cz = SP_C
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(CREST - 1, CF + 9):
                if y <= CREST:
                    if math.hypot(x - cx, z - cz) < SP_R + 0.5:
                        bp.set(x, y, z, "air")
                    else:
                        bp.set(x, y, z, floor_tile(x, y, z) if y == CREST else masonry(x, y, z))
                elif wall:
                    corner = x in (x0, x1) and z in (z0, z1)
                    bp.set(x, y, z, PA if corner or y == CF + 8 else (BRASS if y == CF + 4 else masonry(x, y, z)))
                else:
                    bp.set(x, y, z, "air")
    # the road comes in through the west wall; a door north onto a balcony over the reservoir
    for z in range(3, 9):
        for y in range(CF, CF + 4):
            bp.set(x0, y, z, "air")
    for x in (x0 - 1,):
        for z in (2, 9):
            for y in range(CF, CF + 5):
                bp.set(x, y, z, PA)
    for x in range(66, 70):
        for y in range(CF, CF + 3):
            bp.set(x, y, z0, "air")
        for z in range(z0 - 3, z0):
            if True:
                bp.set(x, CREST, z, PA)
                for y in range(CF, CF + 3):
                    bp.set(x, y, z, "air")
                if z == z0 - 3 or x in (66, 69):
                    bp.set(x, CF, z, f"{RAIL}[facing={'north' if z == z0 - 3 else ('west' if x == 66 else 'east')}]")
    # railing round the shaft, open on the west side
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if SP_R + 0.5 <= d < SP_R + 1.5 and not (x < cx and abs(z - cz) <= 1):
                bp.set(x, CF, z, f"{RAIL}[facing={out_facing(x - cx, z - cz)}]")
    # gate winches and wheels
    for z in (z0 + 1, z1 - 1):
        for x in (x1 - 3, x1 - 1):
            bp.set(x, CF, z, IRON)
            bp.set(x, CF + 1, z, f"{W}valve_wheel[facing={'south' if z == z0 + 1 else 'north'}]")
    for z in range(cz - 2, cz + 3):
        bp.set(x1 - 1, CF, z, GEAR if z == cz else IRON)
    bp.set(x1 - 1, CF + 1, cz, GAUGE)
    bp.chest(x0 + 1, CF, z1 - 1, "north", loot=LOOT + "dd_control")
    hang(bp, cx, CF + 7, cz - 4, 2)
    hang(bp, cx, CF + 7, cz + 4, 2)
    for (x, z) in ((x0 + 3, z1), (x1 - 3, z1), (x1, cz - 3), (x1, cz + 3)):
        for y in (CF + 1, CF + 2):
            bp.set(x, y, z, "glass_pane")
    steep_pyramid(bp, x0, z0, x1, z1, CF + 9, SLATE, SLATE_ST, steep=1, overhang=1, finial=None)
    bp.set(cx, CF + 16, cz, IRON_WALL)
    bp.set(cx, CF + 17, cz, "lightning_rod")


def guard_post(bp):
    """The west guard post at the crest's end, on the abutment: a small tower over the road's end, a stair to a
    lookout room with windows over the valley and the reservoir."""
    x0, x1, z0, z1 = -75, -67, 4, 12
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(CREST - 1, CF + 14):
                if y <= CREST:
                    bp.set(x, y, z, floor_tile(x, y, z) if y == CREST else masonry(x, y, z))
                elif wall:
                    corner = x in (x0, x1) and z in (z0, z1)
                    bp.set(x, y, z, PA if corner or y in (CF + 5, CF + 13) else masonry(x, y, z))
                elif y == CF + 5:
                    bp.set(x, y, z, "spruce_planks")
                else:
                    bp.set(x, y, z, "air")
    for z in range(6, 11):
        for y in range(CF, CF + 4):
            bp.set(x1, y, z, "air")
    # stair along the south wall up to the lookout (feet 73)
    for i in range(6):
        x = x1 - 1 - i
        bp.set(x, CF + i, z1 - 1, stair(SB_ST, "west"))
        for y in range(CF, CF + i):
            bp.set(x, y, z1 - 1, SB)
        for y in range(CF + i + 1, CF + i + 5):
            bp.set(x, y, z1 - 1, "air")
    for z in (z1 - 2,):
        for x in range(x1 - 5, x1 - 1):
            bp.set(x, CF + 6, z, f"{RAIL}[facing=north]")
    for (x, z) in ((x0, 8), ((x0 + x1) // 2, z0), ((x0 + x1) // 2, z1)):
        for y in (CF + 7, CF + 8, CF + 9):
            for d in (-1, 0, 1):
                xx, zz = (x, z + d) if x == x0 else (x + d, z)
                bp.set(xx, y, zz, "glass_pane")
    bp.chest(x0 + 1, CF + 6, z0 + 1, "south", loot=LOOT + "dd_works")
    bp.set(x0 + 2, CF + 6, z0 + 1, "barrel[facing=up,open=false]")
    hang(bp, -71, CF + 12, 8, 2)
    bp.set(-71, CF + 3, 5, EDISON)
    steep_pyramid(bp, x0, z0, x1, z1, CF + 14, SLATE, SLATE_ST, steep=2, overhang=1, finial="lightning_rod")


# ------------------------------------------------------------------ the drowned village
WLOG = ("stairs", "slab", "fence", "wall", "pane", "bars", "chest", "lantern", "ladder", "trapdoor", "chain",
        "candle", "rail")


def ws(bp, x, y, z, spec):
    """Set a block of the drowned village: under the water line, every block that can hold water does."""
    if y <= WL and isinstance(spec, str) and any(k in spec for k in WLOG):
        if "waterlogged=" in spec:
            spec = spec.replace("waterlogged=false", "waterlogged=true")
        elif "[" in spec:
            spec = spec[:-1] + ",waterlogged=true]"
        else:
            spec = spec + "[waterlogged=true]"
    bp.set(x, y, z, spec)


def wet(bp, x, y, z):
    """Waterlog a block already set (chests placed with bp.chest under the water)."""
    name, props, data = bp.blocks[(x, y, z)]
    bp.blocks[(x, y, z)] = (name, dict(props, waterlogged="true"), data)


def wstair(spec, facing, half="bottom"):
    return f"{spec}[facing={facing},half={half},shape=straight,waterlogged=true]"


def drowned_house(bp, x0, z0, x1, z1, door, seed, loot=True):
    """A flooded cottage: mossy rubble base, rotten plank walls framed in logs, a sagging dark-oak roof with holes;
    inside, water, a table, a barrel or a chest."""
    f = VF
    w, d = x1 - x0 + 1, z1 - z0 + 1
    along_x = w > d
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            bp.set(x, BED, z, "mossy_cobblestone" if wall else ("spruce_planks" if hash01(x, z, seed) < 0.6 else "mud"))
            for y in range(f, f + 3):
                if wall:
                    h = hash3(x, y, z, seed)
                    if corner:
                        bp.set(x, y, z, "stripped_spruce_log[axis=y]")
                    elif y == f:
                        bp.set(x, y, z, "mossy_cobblestone" if h < 0.6 else "cobblestone")
                    elif h < 0.12:
                        bp.set(x, y, z, "water")          # rotted through
                    else:
                        bp.set(x, y, z, "dark_oak_planks" if h < 0.7 else "spruce_planks")
                else:
                    bp.set(x, y, z, "water")
    # windows and the door (open doorways: water flows through)
    for (x, z) in (((x0 + x1) // 2, z0), ((x0 + x1) // 2, z1), (x0, (z0 + z1) // 2), (x1, (z0 + z1) // 2)):
        bp.set(x, f + 1, z, "water")
    dx, dz = {"north": ((x0 + x1) // 2, z0), "south": ((x0 + x1) // 2, z1), "west": (x0, (z0 + z1) // 2),
              "east": (x1, (z0 + z1) // 2)}[door]
    bp.set(dx, f, dz, "water")
    bp.set(dx, f + 1, dz, "water")
    # roof: gable along the long side, a few holes
    if along_x:
        half = (d + 1) // 2
        for i in range(half + 1):
            y = f + 3 + i
            for x in range(x0 - 1, x1 + 2):
                for z, fc in ((z0 - 1 + i, "south"), (z1 + 1 - i, "north")):
                    if y > WL - 1 or hash3(x, y, z, seed + 3) < 0.1:
                        continue
                    if z0 - 1 + i == z1 + 1 - i:
                        ws(bp, x, y, z, "dark_oak_slab[type=bottom]")
                    else:
                        bp.set(x, y, z, wstair("dark_oak_stairs", fc))
            if i >= 1:
                for x in (x0, x1):
                    for z in range(z0 + i, z1 - i + 1):
                        if y <= WL - 1:
                            bp.set(x, y, z, "dark_oak_planks")
    else:
        half = (w + 1) // 2
        for i in range(half + 1):
            y = f + 3 + i
            for z in range(z0 - 1, z1 + 2):
                for x, fc in ((x0 - 1 + i, "east"), (x1 + 1 - i, "west")):
                    if y > WL - 1 or hash3(x, y, z, seed + 3) < 0.1:
                        continue
                    if x0 - 1 + i == x1 + 1 - i:
                        ws(bp, x, y, z, "dark_oak_slab[type=bottom]")
                    else:
                        bp.set(x, y, z, wstair("dark_oak_stairs", fc))
            if i >= 1:
                for z in (z0, z1):
                    for x in range(x0 + i, x1 - i + 1):
                        if y <= WL - 1:
                            bp.set(x, y, z, "dark_oak_planks")
    # inside
    ix, iz = x0 + 1, z0 + 1
    ws(bp, ix, f, iz, "oak_fence")
    ws(bp, ix, f + 1, iz, "dark_oak_slab[type=bottom]")
    if loot:
        if hash01(x0, z0, seed) < 0.5:
            bp.chest(x1 - 1, f, z1 - 1, OPP[door], loot=LOOT + "dd_drowned")
            wet(bp, x1 - 1, f, z1 - 1)
        else:
            bp.barrel(x1 - 1, f, z1 - 1, "up", loot=LOOT + "dd_drowned")
    ws(bp, x0 + 1, f, z1 - 1, "sea_pickle[pickles=3]")


def drowned_church(bp):
    """The church: a nave with lancet windows and a fallen roof (only rafters left), the apse toward the dam, and at
    the north end the bell tower that still stands out of the water: a ladder inside up to the belfry, the bell,
    the village's hoard."""
    f = VF
    nx0, nx1, nz0, nz1 = -24, -18, -61, -46
    for x in range(nx0, nx1 + 1):
        for z in range(nz0, nz1 + 1):
            wall = x in (nx0, nx1) or z == nz1
            bp.set(x, BED, z, "stone_bricks" if (x + z) % 3 else "mossy_stone_bricks")
            for y in range(f, f + 5):
                if wall:
                    h = hash3(x, y, z, 61)
                    lancet = (x in (nx0, nx1) and z % 4 == 0 and f + 1 <= y <= f + 3) or (z == nz1 and x == -21 and
                                                                                         y >= f + 1)
                    if lancet:
                        bp.set(x, y, z, "water")
                    elif y == f + 4 and h < 0.3:
                        bp.set(x, y, z, "water")
                    else:
                        bp.set(x, y, z, MO if h < 0.5 else (SB if h < 0.85 else CR))
                else:
                    bp.set(x, y, z, "water")
    # rafters left of the roof
    for z in range(nz0 + 2, nz1, 3):
        for x in range(nx0, nx1 + 1):
            bp.set(x, f + 5, z, "stripped_dark_oak_log[axis=x]")
    for z in range(nz0 + 2, nz1, 3):
        bp.set(-21, f + 6, z, "stripped_dark_oak_log[axis=y]")
    # pews and the altar
    for z in range(nz0 + 4, nz1 - 3, 2):
        for x in (nx0 + 1, nx0 + 2, nx1 - 2, nx1 - 1):
            bp.set(x, f, z, wstair("dark_oak_stairs", "north"))
    for x in range(-22, -19):
        bp.set(x, f, nz1 - 2, "chiseled_stone_bricks")
    ws(bp, -21, f + 1, nz1 - 2, "candle[candles=4,lit=false]")
    # the bell tower (5 x 5) at the north end
    tx0, tx1, tz0, tz1 = -23, -19, -66, -62
    top = 66
    for x in range(tx0, tx1 + 1):
        for z in range(tz0, tz1 + 1):
            wall = x in (tx0, tx1) or z in (tz0, tz1)
            bp.set(x, BED, z, SB)
            for y in range(f, top + 6):
                if y == top:
                    bp.set(x, y, z, SB if wall or (x, z) != (tx0 + 1, tz0 + 1) else
                           "ladder[facing=south,waterlogged=false]")
                elif wall:
                    corner = x in (tx0, tx1) and z in (tz0, tz1)
                    belfry = top < y <= top + 3 and not corner
                    if belfry:
                        bp.set(x, y, z, "air")
                    elif y == top + 4 or corner:
                        bp.set(x, y, z, SB if y > WL else MO)
                    else:
                        bp.set(x, y, z, (MO if hash3(x, y, z, 63) < 0.5 else SB) if y <= WL + 1 else
                               (SB if hash3(x, y, z, 63) < 0.8 else CR))
                elif y < top:
                    bp.set(x, y, z, "water" if y <= WL else "air")
                elif y <= top + 3:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, SB)
    # the doorway into the tower from the nave (under water) and a ladder up the inner north wall
    for y in (f, f + 1):
        bp.set(-21, y, tz1, "water")
    for y in range(f, top + 1):
        bp.set(tx0 + 1, y, tz0 + 1, f"ladder[facing=south,waterlogged={'true' if y <= WL else 'false'}]")
    bp.set(-21, top + 3, -64, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.chest(tx1 - 1, top + 1, tz1 - 1, "west", loot=LOOT + "dd_hoard")
    bp.set(tx0 + 1, top + 1, tz1 - 1, "lantern[hanging=false,waterlogged=false]")
    # the spire
    steep_pyramid(bp, tx0, tz0, tx1, tz1, top + 5, SLATE, SLATE_ST, steep=2, overhang=0, finial="lightning_rod")
    bp.spawner(-21, f, nz0 + 2, MOB_DROWNED)


def village(bp):
    houses = [(-42, -40, -38, -34, "east"), (-34, -38, -30, -32, "west"), (-14, -38, -8, -34, "south"),
              (-40, -54, -36, -46, "east"), (-34, -70, -30, -64, "south"), (12, -44, 16, -38, "west"),
              (14, -62, 20, -58, "north"), (-12, -66, -8, -60, "east")]
    for i, (x0, z0, x1, z1, door) in enumerate(houses):
        drowned_house(bp, x0, z0, x1, z1, door, 70 + i, loot=i % 2 == 0 or i == 5)
    drowned_church(bp)
    # the stone bridge over the old river bed
    for x in range(-9, 10):
        for z in range(-53, -50):
            deck = BED + 1 - (1 if abs(x) > 7 else 0)
            bp.set(x, deck, z, SB if z != -52 else "mossy_stone_bricks")
            if z in (-53, -50 + 0) and abs(x) <= 7:
                pass
            under = deck - 1
            while under > BED - 8 and abs(x) in (8, 9, 0) and (bp.get(x, under, z) in (None, "minecraft:water")):
                bp.set(x, under, z, SB)
                under -= 1
        for z in (-54, -50):
            ws(bp, x, BED + 2 - (1 if abs(x) > 7 else 0), z, "stone_brick_wall")
    # the well, fences, lamp posts with sea lanterns, dead trees
    for x in range(-28, -25):
        for z in range(-42, -39):
            bp.set(x, VF, z, "mossy_cobblestone" if (x, z) != (-27, -41) else "water")
    for (x, z) in ((-29, -45), (-6, -44), (4, -60), (-36, -60), (10, -36)):
        ws(bp, x, VF, z, "oak_fence")
        ws(bp, x, VF + 1, z, "oak_fence")
        bp.set(x, VF + 2, z, "sea_lantern")
    for z in range(-45, -38):
        ws(bp, -44, VF, z, "oak_fence")
    for x in range(-44, -36):
        ws(bp, x, VF, -45, "oak_fence")
    for i, (x, z) in enumerate(((-18, -38), (-44, -58), (2, -42), (-28, -66), (20, -48))):
        for y in range(VF, VF + 4 + i % 2):
            bp.set(x, y, z, "stripped_oak_log[axis=y]")
        bp.set(x + 1, VF + 3, z, "stripped_oak_log[axis=x]")
        bp.set(x, VF + 3, z - 1, "stripped_oak_log[axis=z]")


# ------------------------------------------------------------------ the east passage (Hall II <-> east tower)
def east_passage(bp):
    for x in range(43, 47):
        for z in range(31, 34):
            bp.set(x, 0, z, PA)
            for y in range(1, 4):
                bp.set(x, y, z, "air")
        for z in (30, 34):
            for y in range(0, 5):
                bp.set(x, y, z, masonry(x, y, z))
        for z in range(30, 35):
            bp.set(x, 4, z, masonry(x, 4, z))
    bp.set(42, 4, 30, EDISON)


# ------------------------------------------------------------------ the valley: approach, yard, tailrace, river
def river_x(z):
    return int(round(6 * math.sin((z - 75) / 12.0)))


def path_cells(pts, w=1.3):
    cells = set()
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(bz - az))) * 2 + 1
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if dx * dx + dz * dz <= w * w:
                        cells.add((int(round(px + dx)), int(round(pz + dz))))
    return cells


WEST_PATH = [(CAMP[0] + 2, CAMP[1] - 3), (-42, 92), (-45, 78), (-51, 66), (-54, 58)]
EAST_PATH = [(48, 36), (50, 58), (45, 78), (22, 94), (-8, 100), (CAMP[0] + 4, CAMP[1] - 1)]
PATHS = path_cells(WEST_PATH) | path_cells(EAST_PATH)


def in_river(x, z):
    return 75 <= z <= AZ1 - 4 and abs(x - river_x(z)) <= 4


def write_paths(bp):
    for (x, z) in sorted(PATHS):
        if not inside(x, z) or hmap(x, z) > 0 or bp.get(x, 0, z) is not None:
            continue
        if in_river(x, z):
            continue
        h = hash01(x, z, 81)
        bp.set(x, 0, z, "dirt_path" if h < 0.55 else ("coarse_dirt" if h < 0.8 else "gravel"))
    # a lamp post every so often along the west path
    for (x, z) in ((-43, 90), (-49, 71)):
        lamp_post(bp, x - 2, 1, z, 3)


def tailrace(bp):
    """The tailrace quay along the powerhouse's south facade, the walled pool fed by the culverts, the weir and the
    river winding away down the valley (a plank footbridge where the east path crosses it)."""
    # the quay (z 61..63)
    for x in range(-44, 45):
        for z in range(61, 64):
            if bp.get(x, 1, z) not in (None, "minecraft:air") and z == 61:
                pass
            bp.set(x, 0, z, PA if (x + z) % 5 else SB)
            bp.set(x, -1, z, dark_masonry(x, -1, z))
    for c in (-13, 13):
        for x in range(c - 2, c + 3):
            for z in range(61, 64):
                bp.set(x, 0, z, "iron_bars[waterlogged=true]")
                for y in range(-3, 0):
                    bp.set(x, y, z, "water")
                bp.set(x, -4, z, "mud_bricks")
        for x in (c - 3, c + 3):
            for z in range(61, 64):
                for y in range(-4, 0):
                    bp.set(x, y, z, dark_masonry(x, y, z))
    # the pool
    for x in range(-30, 31):
        for z in range(64, 75):
            wall = abs(x) == 30
            for y in range(-4, 1):
                if wall:
                    bp.set(x, y, z, PA if y == 0 else dark_masonry(x, y, z))
                elif y == -4:
                    bp.set(x, y, z, "gravel" if hash01(x, z, 83) < 0.5 else "mud")
                elif z == 74 and y <= -2:
                    bp.set(x, y, z, SB if abs(x) > 3 else MO)          # the weir
                else:
                    bp.set(x, y, z, "water")
    for x in (-30, 30):
        bp.set(x, 1, 74, IRON)
        bp.set(x, 2, 74, EDISON)
    # the railing along the quay's edge, bollards, lamps, steps down into the water
    for x in range(-29, 30):
        if x % 8 == 0:
            bp.set(x, 1, 63, IRON)
            if x % 16 == 0:
                bp.set(x, 2, 63, IRON_WALL)
                bp.set(x, 3, 63, EDISON)
        elif abs(x) not in (21, 22):
            bp.set(x, 1, 63, f"{RAIL}[facing=south]")
    for x in (21, 22, -21, -22):
        for k, y in enumerate((0, -1, -2)):
            bp.set(x, y, 64 + k, stair(PA_ST, "north") if y < 0 else PA)
    for z in range(64, 66):
        bp.set(-21, 0, z, stair(PA_ST, "north")) if z == 64 else None
    # crates and a coil of chain on the quay
    for (x, z) in ((-38, 62), (-37, 62), (-38, 61)):
        bp.barrel(x, 1, z, "up")
    bp.barrel(36, 1, 62, "up", loot=LOOT + "dd_works")
    bp.set(37, 1, 62, "cauldron")
    # the river down the valley
    for z in range(75, AZ1 - 3):
        xr = river_x(z)
        for dx in range(-4, 5):
            x = xr + dx
            a = abs(dx)
            if a <= 2:
                bp.set(x, 0, z, "water")
                bp.set(x, -1, z, "water")
                bp.set(x, -2, z, "gravel" if hash01(x, z, 85) < 0.6 else "sand")
            elif a == 3:
                bp.set(x, 0, z, "water")
                bp.set(x, -1, z, "sand" if hash01(x, z, 86) < 0.5 else "clay")
            else:
                bp.set(x, 0, z, "gravel" if hash01(x, z, 87) < 0.5 else "coarse_dirt")
            if a <= 3 and hash3(x, 0, z, 88) < 0.12:
                bp.set(x, -1 if a <= 2 else 0, z, "seagrass" if a <= 2 else "water")
    # the footbridge where the east path crosses
    for (x, z) in sorted(PATHS):
        if in_river(x, z) and abs(x - river_x(z)) <= 3:
            bp.set(x, 1, z, "spruce_slab[type=bottom,waterlogged=false]")


def works_yard(bp):
    """The works yard at the foot of the west sentinel tower, in front of Hall I's bay door: gravel, a rail track,
    a timber derrick, a boiler on skids, crates, a low wall with a gap for the path."""
    for z in range(36, 61):
        xa = int(-vhw(z)) + 2
        for x in range(xa, -45):
            if hmap(x, z) > 0 or bp.get(x, 0, z) is not None:
                continue
            h = hash01(x, z, 91)
            bp.set(x, 0, z, "gravel" if h < 0.4 else ("coarse_dirt" if h < 0.65 else
                                                       ("packed_mud" if h < 0.85 else "cobblestone")))
    for z in range(37, 61):
        bp.set(-52, 1, z, "rail[shape=north_south,waterlogged=false]")
    for x in range(-51, -45):
        bp.set(x, 1, 46, "rail[shape=east_west,waterlogged=false]")
    # the derrick: a mast, a boom to the east, a hook over the track
    mx, mz = -57, 52
    for y in range(1, 14):
        bp.set(mx, y, mz, "stripped_spruce_log[axis=y]")
    for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        bp.set(mx + dx, 1, mz + dz, "spruce_planks")
        bp.set(mx + dx // 2, 2, mz + dz // 2, "spruce_fence")
    for i in range(1, 8):
        bp.set(mx + i, 6 + i, mz, "spruce_fence")
    bp.set(mx, 14, mz, "spruce_fence")
    for i in range(1, 7):
        bp.set(mx + i, 14 - i // 2, mz, "iron_chain[axis=x,waterlogged=false]") if i % 2 else None
    for y in range(7, 13):
        bp.set(mx + 7, y, mz, CHAIN)
    bp.set(mx + 7, 6, mz, GEAR)
    bp.set(mx + 1, 2, mz, f"{W}valve_wheel[facing=east]")
    # the boiler on skids
    for z in range(41, 47):
        for (dx, dy) in ((0, 1), (-1, 2), (0, 2), (1, 2), (0, 3)):
            bp.set(-59 + dx, dy, z, COPPER if z not in (41, 46) else BRASS)
        bp.set(-60, 1, z, "spruce_slab[type=bottom,waterlogged=false]")
        bp.set(-58, 1, z, "spruce_slab[type=bottom,waterlogged=false]")
    for y in range(4, 8):
        bp.set(-59, y, 45, IRON_WALL)
    bp.set(-59, 8, 45, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    bp.set(-59, 3, 47, GAUGE)
    # crates, the clerk's chest, the yard's spawner, lamps
    for (x, y, z) in ((-48, 1, 56), (-48, 2, 56), (-49, 1, 57), (-48, 1, 57), (-60, 1, 56), (-61, 1, 56)):
        bp.barrel(x, y, z, "up")
    bp.chest(-47, 1, 38, "west", loot=LOOT + "dd_works")
    bp.set(-47, 1, 39, TABLE)
    bp.spawner(-56, 1, 58, MOB_SPIDER)
    for (x, z) in ((-47, 41), (-47, 52), (-62, 50)):
        lamp_post(bp, x, 1, z, 3)
    # the low wall closing the yard to the south
    for x in range(int(-vhw(61)) + 2, -45):
        if -57 <= x <= -51:
            continue
        bp.set(x, 1, 61, SB_W if hash01(x, 61, 93) < 0.8 else "mossy_stone_brick_wall")


def camp(bp):
    """The surveyors' camp at the head of the approach: a tent, a fire, the waystone, a plane table with the dam's
    drawings, a theodolite on its tripod pointed at the wall."""
    cx, cz = CAMP
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if math.hypot(x - cx, z - cz) < 6.5 and bp.get(x, 0, z) is None:
                bp.set(x, 0, z, "coarse_dirt" if hash01(x, z, 95) < 0.5 else "grass_block[snowy=false]")
    # the tent (canvas over a ridge pole along x)
    tx, tz = cx + 4, cz + 3
    for dx in range(-3, 4):
        for dz in (-2, -1, 0, 1, 2):
            h = 3 - abs(dz)
            if abs(dz) == 2:
                bp.set(tx + dx, 1, tz + dz, "white_wool")
            elif abs(dz) == 1:
                bp.set(tx + dx, 2, tz + dz, "white_wool")
                if dx in (-3, 3):
                    bp.set(tx + dx, 1, tz + dz, "white_wool")
            else:
                bp.set(tx + dx, 3, tz, "brown_wool")
                if dx == 3:
                    bp.set(tx + dx, 2, tz, "white_wool")
            _ = h
    bp.set(tx - 1, 1, tz, "red_bed[facing=east,occupied=false,part=foot]")
    bp.set(tx, 1, tz, "red_bed[facing=east,occupied=false,part=head]")
    bp.chest(tx + 2, 1, tz, "west", loot=LOOT + "dd_works")
    # the fire and its seats
    bp.set(cx, 0, cz, "cobblestone")
    bp.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((2, 0, "west"), (-2, 0, "east"), (0, -2, "south")):
        bp.set(cx + dx, 1, cz + dz, stair("spruce_stairs", f))
    # the waystone on a plinth
    bp.set(cx - 4, 0, cz - 2, SB)
    bp.set(cx - 4, 1, cz - 2, MOD["waystone"])
    # the plane table and the theodolite
    bp.set(cx - 3, 1, cz + 3, "cartography_table")
    bp.set(cx - 4, 1, cz + 3, "lectern[facing=north,has_book=false,powered=false]")
    for (dx, dz) in ((-1, 0), (1, 0), (0, 1)):
        bp.set(cx + 2 + dx, 1, cz - 4 + dz, "spruce_fence")
    bp.set(cx + 2, 2, cz - 4, "spruce_fence")
    bp.set(cx + 2, 3, cz - 4, f"{W}pressure_gauge")
    bp.barrel(cx - 5, 1, cz + 1, "up")
    bp.barrel(cx - 5, 2, cz + 1, "up")
    # the marker post with a lantern
    for y in range(1, 4):
        bp.set(cx - 1, y, cz - 6, MO if y == 1 else SB)
    bp.set(cx - 1, 4, cz - 6, LANT)


# ------------------------------------------------------------------ life
def busy(x, z):
    if (x, z) in PATHS or in_river(x, z):
        return True
    if abs(x) <= 48 and 0 <= z <= 76:
        return True
    if abs(x) <= 62 and 18 <= z <= 64:
        return True
    if math.hypot(x - CAMP[0], z - CAMP[1]) < 10:
        return True
    if 60 <= x <= 76 and 0 <= z <= 40:
        return True
    return False


def vegetation(bp, P):
    """Spruces on the ridge and in the valley, grass and ferns; seagrass, kelp and lily pads in the reservoir; dead
    snags on the drawdown ring."""
    tops = np.argwhere(P.top & P.shell & ~P.D)
    order = sorted(tops.tolist(), key=lambda t: hash3(int(XS[t[0]]), t[1], int(ZS[t[2]]), 97))
    placed = []
    n = 0
    for i, y, k in order:
        x, z = int(XS[i]), int(ZS[k])
        d = float(DIST[i, k])
        if y < 2 or SLOPE[i, k] > 1 or busy(x, z) or abs(x) > AX1 - 4 or abs(z) > AZ1 - 6:
            continue
        if d < 1.0 and y <= WL + 4:
            continue
        if abs(x) <= 92 and R_CR - 6 < GR[i, k] < R_UP + 12:
            continue                                   # keep the crest's ends clear
        if any(abs(x - a) < 6 and abs(z - b) < 6 for a, b in placed):
            continue
        if not is_air(bp, x, y + 1, z) or not is_air(bp, x, y + 7, z):
            continue
        spruce(bp, x, y + 1, z, h=7 + int(hash01(x, z, 9) * 6), seed=x * 3 + z)
        bp.set(x, y, z, "podzol[snowy=false]")
        placed.append((x, z))
        n += 1
        if n >= 70:
            break
    # the valley floor: scattered spruces and boulders on the natural ground (y 0)
    for x in range(AX0 + 4, AX1 - 3, 7):
        for z in range(14, AZ1 - 8, 7):
            jx = x + int(hash01(x, z, 101) * 5) - 2
            jz = z + int(hash01(x, z, 103) * 5) - 2
            if hmap(jx, jz) > 0 or busy(jx, jz) or bp.get(jx, 0, jz) is not None or hash01(jx, jz, 105) > 0.3:
                continue
            if any(abs(jx - a) < 5 and abs(jz - b) < 5 for a, b in placed):
                continue
            if abs(jx) < VALLEY.shape[0] and hmap(jx + 3, jz) > 2 or hmap(jx - 3, jz) > 2:
                continue
            if hash01(jx, jz, 107) < 0.8:
                bp.set(jx, 0, jz, "podzol[snowy=false]")
                spruce(bp, jx, 1, jz, h=8 + int(hash01(jx, jz, 9) * 6), seed=jx * 5 + jz)
            else:
                bp.set(jx, 0, jz, "mossy_cobblestone")
                bp.set(jx, 1, jz, "mossy_cobblestone")
                bp.set(jx + 1, 1, jz, "cobblestone")
                bp.set(jx, 2, jz, "mossy_cobblestone")
            placed.append((jx, jz))
    # grass tufts on the rock tops
    for i, y, k in tops.tolist():
        x, z = int(XS[i]), int(ZS[k])
        b = bp.get(x, y, z)
        if b not in ("minecraft:grass_block", "minecraft:moss_block", "minecraft:podzol") or \
                bp.get(x, y + 1, z) is not None:
            continue
        h = hash3(x, y, z, 109)
        if b == "minecraft:moss_block":
            if h < 0.35:
                bp.set(x, y + 1, z, "moss_carpet")
        elif b == "minecraft:podzol":
            if h < 0.25:
                bp.set(x, y + 1, z, "fern")
        elif h < 0.08:
            bp.set(x, y + 1, z, "short_grass")
        elif h < 0.11:
            bp.set(x, y + 1, z, "fern")
    # boulders fallen from the ridge, resting on the outer slopes (mossy on their north side)
    for i, y, k in tops.tolist():
        x, z = int(XS[i]), int(ZS[k])
        if DIST[i, k] < 4 or y < 4 or y > RIDGE - 6 or SLOPE[i, k] > 3 or hash3(x, y, z, 119) > 0.0035:
            continue
        if busy(x, z) or (abs(x) <= 92 and R_CR - 6 < GR[i, k] < R_UP + 12):
            continue
        cells = [(0, 1, 0), (1, 1, 0), (0, 1, 1), (0, 2, 0)] + ([(1, 1, 1), (-1, 1, 0)] if hash01(x, z, 121) < 0.5
                                                               else [])
        if any(bp.get(x + a, y + b, z + c) is not None for a, b, c in cells):
            continue
        if any(bp.get(x + a, y + b - 1, z + c) is None for a, b, c in cells if b == 1):
            continue
        for a, b, c in cells:
            bp.set(x + a, y + b, z + c, "mossy_cobblestone" if c <= 0 and hash3(x + a, y + b, z + c, 123) < 0.6
                   else ("cobblestone" if hash3(x + a, y + b, z + c, 125) < 0.5 else "andesite"))
    # the reservoir: seagrass and kelp on the bed, lily pads in the shallows, snags on the drawdown ring
    for i, k in np.argwhere(BOWL).tolist():
        x, z = int(XS[i]), int(ZS[k])
        hy = int(HMAP[i, k])
        if bp.get(x, hy + 1, z) != "minecraft:water":
            continue
        depth = WL - hy
        h = hash01(x, z, 111)
        if depth >= 4 and h < 0.025:
            ln = 2 + int(hash01(x, z, 113) * min(8, depth - 2))
            for y in range(hy + 1, hy + 1 + ln):
                bp.set(x, y, z, "kelp_plant")
            bp.set(x, hy + 1 + ln, z, "kelp[age=20]")
        elif depth >= 2 and h < 0.16:
            bp.set(x, hy + 1, z, "seagrass")
        elif depth == 1 and h < 0.3 and bp.get(x, WL + 1, z) is None:
            bp.set(x, WL + 1, z, "lily_pad")
    for i, y, k in tops.tolist():
        x, z = int(XS[i]), int(ZS[k])
        if DIST[i, k] < 0 and WL < y <= WL + 4 and hash3(x, y, z, 115) < 0.006 and is_air(bp, x, y + 1, z):
            for yy in range(y + 1, y + 4 + int(hash01(x, z, 117) * 3)):
                bp.set(x, yy, z, "stripped_spruce_log[axis=y]")
            bp.set(x + 1, y + 3, z, "stripped_spruce_log[axis=x]")


def footings(bp):
    """Two blocks of footing under the low rock at the edges of the valley and under the yard's machines, so the
    shoulders never float over a dip (foundation=False: the whole 225-block plan would sink otherwise)."""
    feet = [(x, z) for (x, y, z), v in list(bp.blocks.items()) if y == 0 and v[0] != "minecraft:air"
            and v[0] != "minecraft:water" and 1 <= hmap(x, z) <= 12]
    for x, z in feet:
        for d in (1, 2):
            if bp.get(x, -d, z) is None:
                bp.set(x, -d, z, "dirt" if d == 1 else "stone")


def seal(bp, P):
    """Close every hole the buildings cut into the rock and dam shells: an unset cell of the massif next to an open
    cell (air, water, any non-full block) gets its rock or masonry, so no carved room opens into the hollow core."""
    opened = [p for p, v in bp.blocks.items() if not is_solid(v[0])]
    for (x, y, z) in opened:
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            q = (x + dx, y + dy, z + dz)
            if q in bp.blocks or not inside(q[0], q[2]) or not (0 <= q[1] < AY):
                continue
            i, yy, k = ai(*q)
            if not P.S[i, yy, k]:
                continue
            if P.D[i, yy, k]:
                bp.set(*q, dam_block(*q))
            else:
                bp.set(*q, rock_block(q[0], yy, q[2], False, float(DIST[i, k]), float(SLOPE[i, k])))


# ------------------------------------------------------------------ builder
def drowned_dam(bp):
    P = Plan()
    write_mass(bp, P)
    write_water(bp, P)
    powerhouse_mass(bp, P)
    ph_roofs(bp)
    ph_facade(bp)
    hall_one(bp)
    hall_two(bp)
    east_passage(bp)
    arena(bp)
    for s in (-1, 1):
        sentinel_tower(bp, s)
    gangways(bp)
    control_tower(bp)
    valve_house(bp)
    drowned_gallery(bp)
    lift_shaft(bp)
    headframe(bp)
    spillway(bp)
    gatehouse(bp)
    guard_post(bp)
    crest(bp)
    berm(bp)
    ribs(bp)
    village(bp)
    tailrace(bp)
    works_yard(bp)
    camp(bp)
    write_paths(bp)
    seal(bp, P)
    vegetation(bp, P)
    footings(bp)


VIEWS = [
    ("approach", (CAMP[0] - 5, 1, CAMP[1] - 3), (0, 45, 15)),
    ("lobby", (-40, 1, 57), (-40, 8, 12)),
    ("berm", (-44, BF, 11), (0, BF + 3, 4)),
    ("valve_house", (-13, BF, -2), (-22, BF + 3, -6)),
    ("drowned_gallery", (-26, GF, -9), (-46, GF + 1, -3)),
    ("control_room", (5, CT_ROOM, -2), (-4, CT_ROOM + 2, -14)),
    ("east_tower", (48, 1, 32), (52, 30, 28)),
    ("arena", (14, 1, 48), (0, 12, 12)),
]


register(StructureDef(
    "drowned_dam", "overworld",
    ["meadow", "windswept_hills", "windswept_forest", "windswept_gravelly_hills", "taiga", "old_growth_spruce_taiga",
     "old_growth_pine_taiga", "forest", "birch_forest"],
    [Piece("dam", drowned_dam, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128,
    foundation=False, spawns=[(MOB_DROWNED, 4, 1, 2), ("minecraft:zombie", 4, 1, 2), (W + "turbine_automaton", 4, 1, 1)],
    title_fr="Barrage de la vallée engloutie", title_en="Dam of the Drowned Valley"))
