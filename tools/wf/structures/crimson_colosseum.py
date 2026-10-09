"""The Crimson Colosseum (Le Colisée cramoisi): a piglin gladiatorial arena-city in a Nether crimson forest, a
three-tiered oval colosseum of blackstone, gilded blackstone, nether bricks and gold ringed by a lava moat, crimson
fungus eating its north-west flank. Colossal tier (tools/BUILDING.md §1, §12 concept 32, §10 legacy-dungeon
template, §15; tools/STYLE_STEAMPUNK.md for the brass of the beast lifts).

Silhouette (one noun phrase, §15.1): a black oval arena of three arcaded storeys and a gilded attic hung with
banners, a colossal golden piglin champion standing on its north tower over the royal box, two spiked gate towers
on the south and two on the east, a ring of lava round it crossed by a chain bridge.

Placement: the Nether has no sky, so the colosseum stands at a fixed height (cavern FIT, like soul_engine /
titan_forge): blueprint y = world y - 30 (template bottom = the hypogeum floor, y -9 = world 21), the apron at y 5
(world 35, feet 6), the champion's crown at y 87 (world 117, under the bedrock roof). Every open volume is explicit
air (the rooms of the mass grid, the arena bowl, the air over the seats, the niches, then ``carve_open`` for the
approach, the moat, the bridge and the camp), so the netherrack cannot fill them. x east, z south.

The ring is one family of ellipses round the sand floor (semi-axes 22 x 17, u = 0): the podium (u 0..5, walk at
feet 15), tier 1 (u 5..17), a walkway, tier 2 (u 19.5..31.5), a walkway, tier 3 (u 33.5..41), the portico (u 41..44)
and the outer wall (u 44..47, 3 arcaded storeys and the attic, top y 50); the lava moat at u 51..58. Every room of
the substructure is a box (or a sector of the ring) of air under the seats.

The route (main path ~550 path blocks):
  * the exiled gladiators' camp (waystone) south-west beyond the moat; the road east between giant crimson fungi,
    north under the broken triumphal arch (it frames the gate: the reveal), over the chain bridge across the lava;
  * the champions' gate (a wicket in its gilded leaves), the gate tunnel (compression) into the betting hall (hub,
    waystone): counters, tally boards, heaps of gold, the bookmakers' cage;
  * west: the gladiators' barracks (bunks, weapon racks, training dummies), its stair down into the hypogeum: the
    muster hall, the cage gallery under the arena (cells behind bars, lift shafts to trapdoors in the sand), the
    hoglin pens, the beast lift hall (capstans, chains, cages hanging at three heights); its stairs climb to the
    gallery (feet 6); the armoury forge beside it (forge of champion weapons, its one-way portcullis into the hub);
  * the grand stair up through the stands to the upper ambulatory (feet 24, arched windows over the moat), north
    round the ring to the royal box (site of grace, waystone) under its gilded canopy; the royal stair down inside
    the stands, a narrow passage (the mist) and the boss arena on the sand floor (44 x 34 oval).
  * behind sealed bars under the royal box, the champion's purse vault (treasury).
Shortcuts (§10.4): the beast lift (a ladder from the hypogeum up into a cage in the hub, its iron door opens from
the cage only); the forge's one-way portcullis into the hub (lever on the forge side); the drop from the stands (a
broken row of seats over the hub, onto the bookmakers' hay). After the boss, the Gate of Life: an iron door from the
sand back to the hub (lever on the arena side).
Optional: the forge, the box-to-podium stair and the stands, the cage cells, the hoglin pens' feed store.
Loot gradient (§15.6): camp, hub 1; barracks, cages 1-2; forge, pens, lifts 2; ambulatory 2; royal box 2-3;
purse vault 3+.
"""
import math

import numpy as np

from ..arch import Palette, stair
from ..blueprint import is_solid
from ..defs import Piece, StructureDef, register
from ..megakit import BRASS, COPPER, GEAR, IRON, IRON_WALL, TREAD, fbm, hash01, hash3, vnoise
from ..parts import LOOT, MOD
from .nether import (CHIS, CPBB, GBS, GILD, LAMP, PB, PBB, PBBS, PBBW, brazier, chandelier, giant_fungus,
                     piglin_idol, round_tower)
from .soul_engine import dilate

# the champion of the sand floor: the Gilded Champion (tools/wf/mobs/gilded_champion.py, entity/boss/GildedChampion.java)
BOSS = "brasshaven:gilded_champion"
MOB_BRUTE = "minecraft:piglin_brute"
MOB_PIGLIN = "minecraft:piglin"
MOB_HOGLIN = "minecraft:hoglin"
MOB_ZPIG = "minecraft:zombified_piglin"
MOB_CUBE = "minecraft:magma_cube"
MOB_WSKEL = "minecraft:wither_skeleton"
MOB_GUARD = "brasshaven:basalt_guard"
MOB_HOUND = "brasshaven:cinder_hound"
MOB_IMP = "brasshaven:ember_imp"
MOB_SENTRY = "brasshaven:magma_sentry"

# ------------------------------------------------------------------ levels and the ring
G = 6              # feet on the apron and the ground floor (floor y 5)
HF = -8            # feet in the hypogeum (floor y -9)
PF = 15            # feet on the podium walk
UF = 24            # feet in the upper ambulatory and the royal box
A0, B0 = 22.0, 17.0          # the sand floor's semi-axes (u = 0)
U_WALL0, U_WALL1 = 44.0, 47.0
U_MOAT0, U_MOAT1 = 51.0, 58.0
WALL_TOP = 50
LAVA = "lava[level=0]"

AIR = "minecraft:air"
NB = "nether_bricks"
RNB = "red_nether_bricks"
NBS = "nether_brick_stairs"
NBW = "nether_brick_wall"
NBF = "nether_brick_fence"
RNBS = "red_nether_brick_stairs"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CHAIN_Z = "iron_chain[axis=z,waterlogged=false]"
CHAIN_X = "iron_chain[axis=x,waterlogged=false]"
HANG = "lantern[hanging=true,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
CAMP = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
HAY = "hay_block[axis=y]"
LADDER = "ladder[facing={},waterlogged=false]"
BANNER = "{}_wall_banner[facing={}]"
CANDLE = "candle[candles={},lit=true,waterlogged=false]"
FENCE = "crimson_fence"
BASALT = "polished_basalt[axis=y]"

FLOOR_HALL = Palette({PB: 4, PBB: 3, CHIS: 0.4}, seed=901, scale=1.8)
WALL_DARK = Palette({PBB: 6, CPBB: 1.5, "blackstone": 1.5, PB: 1}, seed=902, scale=2.4)
NETHERW = Palette({NB: 5, RNB: 2, "cracked_nether_bricks": 1}, seed=903, scale=2.2)
GOLDW = Palette({PBB: 5, GBS: 2, CHIS: 0.5}, seed=904, scale=2.0)
HYPO_FLOOR = Palette({"blackstone": 3, PB: 2, "basalt[axis=y]": 1, CPBB: 1}, seed=905, scale=1.6)
HYPO_WALL = Palette({"blackstone": 4, CPBB: 2, PBB: 2, "basalt[axis=y]": 1}, seed=906, scale=2.5)
SANDY = Palette({"sand": 6, "red_sand": 2, "soul_sand": 0.4}, seed=907, scale=2.6)
SEAT1 = Palette({PBB: 5, PB: 2, GBS: 0.3}, seed=908, scale=2.0)
SEAT2 = Palette({NB: 5, RNB: 1.5, "cracked_nether_bricks": 0.6}, seed=909, scale=2.2)
SEAT3 = Palette({"blackstone": 4, PBB: 2, RNB: 1}, seed=910, scale=2.4)
FACADE1 = Palette({PBB: 5, "blackstone": 2, CPBB: 1.5}, seed=911, scale=2.6)
FACADE2 = Palette({NB: 4, PBB: 3, RNB: 1}, seed=912, scale=2.4)
FACADE3 = Palette({PB: 4, PBB: 3, GBS: 0.6}, seed=913, scale=2.4)
ATTIC = Palette({GBS: 3, PBB: 3, PB: 1}, seed=914, scale=2.0)
ROOFP = Palette({PB: 3, PBB: 2, "blackstone": 1}, seed=915, scale=2.5)
GROUND = Palette({"netherrack": 3, "crimson_nylium": 4, "blackstone": 1, "soul_soil": 0.3}, seed=916, scale=4.0)
PATH = Palette({PBB: 5, PB: 2, CHIS: 0.4}, seed=917, scale=1.4)
GOLDPILE = Palette({"gold_block": 3, "raw_gold_block": 2, GBS: 1}, seed=918, scale=1.5)
CRIMSON = Palette({"crimson_planks": 1}, seed=919)
DECKP = Palette({TREAD: 4, IRON: 2}, seed=920, scale=1.6)

STYLES = {   # (floor, wall, ceiling)
    "gate": (PATH, WALL_DARK, WALL_DARK),
    "hall": (Palette({PB: 3, PBB: 3, GBS: 0.5, CHIS: 0.4}, seed=921, scale=1.8), GOLDW, WALL_DARK),
    "barracks": (Palette({"crimson_planks": 3, PBB: 1}, seed=922, scale=2.0), NETHERW, WALL_DARK),
    "forge": (Palette({PBB: 3, "magma_block": 0.25, "blackstone": 2}, seed=923, scale=2.0), WALL_DARK, WALL_DARK),
    "hypo": (HYPO_FLOOR, HYPO_WALL, HYPO_WALL),
    "pens": (Palette({"crimson_nylium": 3, "netherrack": 2, "blackstone": 1}, seed=924, scale=2.0), HYPO_WALL,
             HYPO_WALL),
    "lift": (DECKP, Palette({PBB: 4, "blackstone": 2, IRON: 1}, seed=925, scale=2.2), WALL_DARK),
    "amb": (Palette({PBB: 4, PB: 2, CHIS: 0.4}, seed=926, scale=1.8), NETHERW, NETHERW),
    "royal": (Palette({GBS: 2, PB: 3, "gold_block": 0.15}, seed=927, scale=1.8), GOLDW, GOLDW),
    "purse": (Palette({GBS: 2, "gold_block": 1, PBB: 2}, seed=928, scale=1.6), GOLDW, GOLDW),
}

# ------------------------------------------------------------------ the rooms: boxes of air
#   (name, style, x0, x1, y0, y1, z0, z1)
ROOMS = [
    # ground floor (feet 6)
    ("gate", "gate", -2, 2, G, G + 5, 47, 63),
    ("hub", "hall", -17, 17, G, 17, 30, 46),
    ("d_hub_bar", "gate", -23, -18, G, G + 3, 37, 39),
    ("barracks", "barracks", -44, -24, G, 14, 18, 38),
    ("bar_stair", "hypo", -42, -26, HF, G + 3, 9, 13),
    ("d_hub_forge", "gate", 18, 23, G, G + 3, 37, 39),
    ("forge", "forge", 24, 44, G, 15, 18, 38),
    ("d_forge_gal", "gate", 45, 46, G, G + 3, 13, 21),
    ("gal_w", "lift", 45, 49, G, G + 4, 9, 12),
    ("d_arena_hub", "gate", -1, 1, G, G + 3, 17, 29),
    ("treasury", "purse", -8, 8, G, 12, -38, -26),
    ("d_treas", "purse", -1, 1, G, G + 3, -25, -17),
    ("rs_corr", "gate", -17, -15, G, G + 4, -23, -12),
    # the hypogeum (feet -8)
    ("hypo", "hypo", -26, 26, HF, 1, -13, 13),
    ("muster", "hypo", -48, -27, HF, 2, -12, 14),
    ("d_hypo_pens", "hypo", 27, 27, HF, HF + 4, -2, 2),
    ("pens", "pens", 28, 48, HF, 2, -14, 14),
    ("d_pens_lift", "hypo", 49, 49, HF, HF + 4, -2, 2),
    ("lifthall", "lift", 50, 62, HF, 20, -12, 12),
    ("s_corr", "hypo", -1, 1, HF, HF + 4, 14, 32),
    ("s_shaft", "hypo", 0, 0, HF, 5, 33, 33),
    # the royal box (feet 24)
    ("royal", "royal", -12, 12, UF, 33, -46, -24),
    ("d_royal_amb", "royal", -2, 2, UF, UF + 4, -55, -47),
    ("d_royal_rs", "royal", -14, -13, UF, UF + 3, -46, -44),
    ("rs_top", "royal", -17, -15, UF, UF + 3, -47, -44),
]
# the upper ambulatory: a sector of the ring (u0, u1, theta0, theta1, y0, y1); theta 0 = east, +90 = south
AMB = (37.0, 41.5, -97.0, 46.0, UF, UF + 5)
AMB_STYLE = "amb"

# ------------------------------------------------------------------ the grid
GX0, GX1 = -90, 90
GY0, GY1 = -12, 92
GZ0, GZ1 = -84, 98
SHAPE = (GX1 - GX0 + 1, GY1 - GY0 + 1, GZ1 - GZ0 + 1)
RING, ARENA, WALL, BOX, TOWER, PORT = 1, 2, 3, 4, 5, 6


class _M:
    full = air = lab = U = TH = None
    open_ = None


M = _M()


def _sl(x0, x1, y0, y1, z0, z1):
    return (slice(x0 - GX0, x1 - GX0 + 1), slice(y0 - GY0, y1 - GY0 + 1), slice(z0 - GZ0, z1 - GZ0 + 1))


def ring_u():
    """u for every column: (x / (A0 + u))^2 + (z / (B0 + u))^2 = 1 (bisection), and the angle theta (degrees)."""
    X = np.arange(GX0, GX1 + 1, dtype=float)[:, None] * np.ones((1, SHAPE[2]))
    Z = np.arange(GZ0, GZ1 + 1, dtype=float)[None, :] * np.ones((SHAPE[0], 1))
    lo = np.full(X.shape, -16.95)
    hi = np.full(X.shape, 160.0)
    for _ in range(40):
        mid = (lo + hi) / 2
        f = (X / (A0 + mid)) ** 2 + (Z / (B0 + mid)) ** 2
        big = f > 1
        lo = np.where(big, mid, lo)
        hi = np.where(big, hi, mid)
    U = (lo + hi) / 2
    TH = np.degrees(np.arctan2(Z / (B0 + U), X / (A0 + U)))
    return U, TH


def u_at(x, z):
    ix, iz = x - GX0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iz < SHAPE[2]:
        return float(M.U[ix, iz])
    return 999.0


def th_at(x, z):
    return float(M.TH[x - GX0, z - GZ0])


def seat_top(u):
    """Top solid y of the ring at radial offset u (the stepped section of the cavea)."""
    if u < 5:
        return 14
    if u < 17:
        return 15 + int((u - 5) // 2)
    if u < 19.5:
        return 21
    if u < 31.5:
        return 23 + int((u - 19.5) // 2)
    if u < 33.5:
        return 29
    if u < 41:
        return 31 + int((u - 33.5) // 2)
    return 35


def row_front(u):
    """True on the front (arena-side) cell of a seat row: there the seat is a stair."""
    for a, b in ((5, 17), (19.5, 31.5), (33.5, 41)):
        if a <= u < b:
            return (u - a) % 2 < 1.0
    return False


def outward(x, z):
    """The cardinal direction pointing away from the arena at (x, z)."""
    u = max(0.0, u_at(x, z))
    gx, gz = x / (A0 + u) ** 2, z / (B0 + u) ** 2
    if abs(gx) >= abs(gz):
        return "east" if gx > 0 else "west"
    return "south" if gz > 0 else "north"


OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


# ------------------------------------------------------------------ the facade's bays
N_BAYS = 36
_PER = None


def _arclen_table():
    a, b = A0 + U_WALL1, B0 + U_WALL1
    ts = np.linspace(-math.pi, math.pi, 3601)
    xs, zs = a * np.cos(ts), b * np.sin(ts)
    d = np.hypot(np.diff(xs), np.diff(zs))
    s = np.concatenate([[0.0], np.cumsum(d)])
    return ts, s


def bay_coords(th_deg):
    """(bay index, offset from the bay's centre in blocks, bay length) for a facade angle; a bay is centred on the
    south axis (theta 90, the champions' gate)."""
    global _PER
    if _PER is None:
        _PER = _arclen_table()
    ts, s = _PER
    total = s[-1]
    L = total / N_BAYS
    sv = np.interp(math.radians(th_deg), ts, s)
    s0 = np.interp(math.pi / 2, ts, s)
    q = (sv - s0) / L + 0.5
    k = int(math.floor(q)) % N_BAYS
    w = (q - math.floor(q) - 0.5) * L
    return k, w, L


STOREYS = ((6, 17), (19, 30), (32, 43))     # (bottom, top) of each arcade storey
ARCH_HW = 3.6                               # half-width of the arch openings
GATE_BAYS = (0,)                            # the champions' gate (south)
BEAST_BAY = 27                              # the beast gate (east: theta 0)
DEATH_BAY = 9                               # the gate of death (west)


def arch_open(w, y, storey):
    y0, y1 = STOREYS[storey]
    if abs(w) > ARCH_HW:
        return False
    spring = y1 - 4
    if y <= spring:
        return y >= y0
    return (y - spring) ** 2 + w ** 2 <= ARCH_HW ** 2 + 0.6


def amb_window_bay(th):
    return AMB[2] + 4 <= th <= AMB[3] - 6


# ------------------------------------------------------------------ the masses
def build_masses():
    lab = np.zeros(SHAPE, np.uint8)
    U, TH = M.U, M.TH
    NXs, NZs = SHAPE[0], SHAPE[2]
    for ix in range(NXs):
        x = ix + GX0
        for iz in range(NZs):
            z = iz + GZ0
            u = U[ix, iz]
            if u < 0:
                lab[ix, 2 - GY0:6 - GY0, iz] = ARENA          # the arena slab over the hypogeum (sand top y 5)
            elif u < U_WALL0:
                top = seat_top(u)
                if -13 <= x <= 13 and z <= -23 and 6 <= u < 41:
                    top = 23                                 # the royal box's base
                lab[ix, 0 - GY0:top + 1 - GY0, iz] = RING
                if u >= 41:
                    lab[ix, 43 - GY0:45 - GY0, iz] = PORT     # the portico's roof
            elif u < U_WALL1:
                lab[ix, 0 - GY0:WALL_TOP + 1 - GY0, iz] = WALL
            elif u < U_WALL1 + 2:
                lab[ix, 0 - GY0:6 - GY0, iz] = WALL           # the stylobate step (y 5)
    # the portico's columns (between the bays) hold the roof
    for ix in range(NXs):
        for iz in range(NZs):
            u = U[ix, iz]
            if 41.5 <= u < 42.6:
                k, w, L = bay_coords(TH[ix, iz])
                if abs(w) > L / 2 - 1.1:
                    lab[ix, 36 - GY0:43 - GY0, iz] = PORT
    # half-columns on the piers and the storeys' cornices project from the wall face
    for ix in range(NXs):
        for iz in range(NZs):
            u = U[ix, iz]
            if not (U_WALL1 <= u < U_WALL1 + 1.3):
                continue
            k, w, L = bay_coords(TH[ix, iz])
            if abs(w) > L / 2 - 1.6:
                lab[ix, 6 - GY0:45 - GY0, iz] = WALL
            for y in (18, 31, 44, WALL_TOP):
                lab[ix, y - GY0, iz] = WALL
    # the royal box (walls and roof) and the imperial tower behind it, with the champion on top
    lab[_sl(-13, 13, 24, 35, -57, -23)] = BOX
    lab[_sl(-14, 14, 0, 40, -73, -57)] = TOWER
    lab[_sl(-12, 12, 41, 52, -71, -57)] = TOWER
    lab[_sl(-11, 11, 53, 54, -70, -59)] = TOWER
    for (a0, a1) in ((-10, -6), (-2, 2), (6, 10)):           # tall blind arches on its north face
        for x in range(a0, a1 + 1):
            for y in range(8, 36):
                c = (a0 + a1) / 2
                if y <= 32 or (y - 32) ** 2 + (x - c) ** 2 <= 6.5:
                    lab[x - GX0, y - GY0, -73 - GZ0] = 0
    for sx in (-14, 14):
        for (a0, a1) in ((-70, -66), (-64, -60)):
            for z in range(a0, a1 + 1):
                for y in range(8, 30):
                    c = (a0 + a1) / 2
                    if y <= 26 or (y - 26) ** 2 + (z - c) ** 2 <= 6.5:
                        lab[sx - GX0, y - GY0, z - GZ0] = 0
    # the facade niches: arches recessed 1.5 deep; the windows of the upper ambulatory go through
    for ix in range(NXs):
        x = ix + GX0
        for iz in range(NZs):
            z = iz + GZ0
            u = U[ix, iz]
            if not (U_WALL0 - 4.5 <= u < U_WALL1):
                continue
            k, w, L = bay_coords(TH[ix, iz])
            if k in GATE_BAYS and abs(x) <= 14:
                continue
            for s in range(3):
                window = s == 1 and amb_window_bay(TH[ix, iz]) and abs(w) <= 1.6
                if u < 45.0 and not window:
                    continue
                for y in range(STOREYS[s][0], STOREYS[s][1] + 1):
                    if window:
                        if UF <= y <= UF + 4 and u >= AMB[1] - 0.5:
                            lab[ix, y - GY0, iz] = 0
                    elif arch_open(w, y, s):
                        if lab[ix, y - GY0, iz] in (WALL,):
                            lab[ix, y - GY0, iz] = 0
    return lab


def build_air():
    air = np.zeros(SHAPE, bool)
    rid = np.full(SHAPE, -1, np.int16)
    for i, (name, style, x0, x1, y0, y1, z0, z1) in enumerate(ROOMS):
        sl = _sl(x0, x1, y0, y1, z0, z1)
        air[sl] = True
        rid[sl] = i
    # the upper ambulatory sector
    u0, u1, t0, t1, y0, y1 = AMB
    m = (M.U >= u0) & (M.U < u1) & (M.TH >= t0) & (M.TH <= t1)
    k = len(ROOMS)
    for iy in range(y0 - GY0, y1 + 1 - GY0):
        air[:, iy, :] |= m
        rid[:, iy, :][m] = k
    # the royal stair: one air box per step (feet f at z)
    for (z, f) in royal_stair_steps():
        sl = _sl(-17, -15, f, f + 3, z, z)
        air[sl] = True
        rid[sl] = 0
    return air, rid


def royal_stair_steps():
    """(z, feet) of the royal stair: landing at feet 24 (z -47..-44), down south to feet 15, a landing, down to the
    corridor at feet 6 (z -23)."""
    out = []
    f = UF
    z = -43
    for i in range(9):
        f -= 1
        out.append((z, f))
        z += 1
    for _ in range(2):
        out.append((z, f))
        z += 1
    for i in range(9):
        f -= 1
        out.append((z, f))
        z += 1
    return out


def style_of(i):
    if i < 0:
        return "gate"
    if i >= len(ROOMS):
        return AMB_STYLE
    return ROOMS[i][1]


def outer_spec(L, x, y, z, top):
    u = u_at(x, z)
    if L == ARENA:
        if top:
            d = math.hypot(x / A0, z / B0)
            if d > 0.94:
                return "red_sand" if hash01(x, z, 931) < 0.5 else GBS
            return SANDY.pick(x, y, z)
        return HYPO_WALL.pick(x, y, z)
    if L == RING:
        if top:
            if u < 1.0:
                return GILD
            if u < 5:
                return PATH.pick(x, y, z)
            pal = SEAT1 if u < 19.5 else (SEAT2 if u < 33.5 else SEAT3)
            if row_front(u):
                spec = {SEAT1: PBBS, SEAT2: NBS, SEAT3: "blackstone_stairs"}[pal]
                return stair(spec, outward(x, z))
            return pal.pick(x, y, z)
        if u < 2.5:                                   # the podium's face over the sand
            if y == 13:
                return GILD
            if y in (6, 7):
                return "blackstone"
            return GOLDW.pick(x, y, z) if (y + int(u * 3)) % 9 else CHIS
        if u < 19.5:
            return SEAT1.pick(x, y, z)
        if u < 33.5:
            return SEAT2.pick(x, y, z)
        return SEAT3.pick(x, y, z)
    if L == PORT:
        if top:
            return ROOFP.pick(x, y, z)
        if y >= 43:
            return GILD if y == 43 else PB
        return BASALT if (y - 36) % 6 else GILD
    if L == WALL:
        if top:
            if u >= U_WALL1:
                return CHIS
            return ROOFP.pick(x, y, z)
        return facade_spec(x, y, z, u)
    if L == BOX:
        if top:
            return GILD if (x + z) % 3 == 0 else ROOFP.pick(x, y, z)
        if y in (24, 35):
            return GILD
        return GOLDW.pick(x, y, z)
    if L == TOWER:
        if top:
            return CHIS
        if y < 8:
            return FACADE1.pick(x, y, z)
        if y in (18, 31, 44, 52):
            return GILD
        if x in (-14, 14) or (x % 7 == 0):
            return BASALT
        return FACADE3.pick(x, y, z) if y > 31 else FACADE1.pick(x, y, z)
    return "blackstone"


def overgrowth(x, y, z):
    """Crimson fungus eating the outer wall: stronger low down and on the west and north-west faces."""
    th = math.atan2(z, x)
    bonus = 0.16 * max(0.0, -math.cos(th + 0.6))
    return fbm(x * 0.7 + z * 0.5, y * 1.2, 9.0, 941) + bonus - max(0, y - 6) / 70.0


def facade_spec(x, y, z, u):
    n = overgrowth(x, y, z)
    if n > 0.66:
        return "shroomlight" if hash3(x, y, z, 942) < 0.05 else "nether_wart_block"
    if n > 0.6:
        return "crimson_hyphae[axis=y]"
    if y <= 7:
        return FACADE1.pick(x, y, z) if y > 5 else CHIS
    if y in (18, 31, 44):
        return GILD                                    # the cornices of the storeys
    if y == WALL_TOP:
        return CHIS
    k, w, L = bay_coords(th_at(x, z))
    pier = abs(w) > ARCH_HW
    if u >= U_WALL1 - 0.3 and y < 45:
        if abs(w) > L / 2 - 1.6:
            return BASALT if y not in (6, 7) else CHIS      # the half-columns
        if y in (18, 31, 44):
            return GILD
    for (sy0, sy1) in STOREYS:
        if u >= 45.0 and sy0 <= y <= sy1 and abs(w) <= ARCH_HW + 1.2:
            spring = sy1 - 4
            if y > spring and (y - spring) ** 2 + w ** 2 <= (ARCH_HW + 1.2) ** 2:
                return GILD if abs(w) < 0.6 else CHIS      # voussoirs, the gilded keystone
            if y <= spring and abs(w) > ARCH_HW:
                return PB                                  # the jambs
    if y >= 45:
        if abs(w) > L / 2 - 1.1:
            return BASALT                              # attic pilasters
        if y in (47, 48) and abs(w) < 1.1 and k % 2 == 0:
            return LAMP                                # the attic's lit slits
        return ATTIC.pick(x, y, z)
    if pier and abs(w) > L / 2 - 1.1:
        return BASALT if y > 7 else CHIS               # the pilaster on the pier
    pal = FACADE1 if y < 18 else (FACADE2 if y < 31 else FACADE3)
    return pal.pick(x, y, z)


def write_masses(bp, lab, air, rid):
    bowl = np.zeros(SHAPE, bool)                      # the open bowl over the sand: never walled by a room's shell
    bowl[:, 6 - GY0:, :] = (M.U < 0)[:, None, :]
    full = ((lab > 0) | (dilate(air) & ~bowl)) & ~air
    occ = full | air
    outside = ~occ
    outside[:, :5 - GY0, :] = False       # below the apron: ground, not an outside face
    outer = full & dilate(dilate(outside, six=True), six=True)
    lining = full & dilate(air, six=True)
    M.full, M.air, M.lab = full, air, lab
    NX, NY, NZ = SHAPE
    for ix, iy, iz in np.argwhere(outer | lining).tolist():
        x, y, z = ix + GX0, iy + GY0, iz + GZ0
        spec = None
        if lining[ix, iy, iz]:
            if iy + 1 < NY and air[ix, iy + 1, iz]:
                spec = STYLES[style_of(rid[ix, iy + 1, iz])][0].pick(x, y, z)
            elif iy > 0 and air[ix, iy - 1, iz]:
                spec = STYLES[style_of(rid[ix, iy - 1, iz])][2].pick(x, y, z)
            else:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    jx, jz = ix + dx, iz + dz
                    if 0 <= jx < NX and 0 <= jz < NZ and air[jx, iy, jz]:
                        spec = STYLES[style_of(rid[jx, iy, jz])][1].pick(x, y, z)
                        break
        if spec is None:
            L = int(lab[ix, iy, iz])
            if L == 0:
                L = RING
            top = iy + 1 < NY and outside[ix, iy + 1, iz]
            spec = outer_spec(L, x, y, z, top)
        bp.set(x, y, z, spec)
    for ix, iy, iz in np.argwhere(air).tolist():
        bp.set(ix + GX0, iy + GY0, iz + GZ0, AIR)
    # explicit air in the open volumes of the grid: the arena bowl, over the seats, the niches and windows
    U = M.U
    op = np.zeros(SHAPE, bool)
    for ix in range(NX):
        for iz in range(NZ):
            u = U[ix, iz]
            if u < 0:
                op[ix, 6 - GY0:37 - GY0, iz] = True
            elif u < U_WALL0:
                t = seat_top(u)
                op[ix, t + 1 - GY0:t + 7 - GY0, iz] = True
            elif u < U_WALL1 + 0.5:
                op[ix, 6 - GY0:WALL_TOP + 1 - GY0, iz] = True
            elif u < U_WALL1 + 6:
                op[ix, 6 - GY0:18 - GY0, iz] = True
    op[_sl(-13, 13, 15, 33, -22, -14)] = True           # under the royal box's canopy
    op &= ~occ
    M.open_ = op
    for ix, iy, iz in np.argwhere(op).tolist():
        if bp.get(ix + GX0, iy + GY0, iz + GZ0) is None:
            bp.set(ix + GX0, iy + GY0, iz + GZ0, AIR)


def solid(x, y, z):
    ix, iy, iz = x - GX0, y - GY0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= iz < SHAPE[2]:
        return bool(M.full[ix, iy, iz])
    return False


# ------------------------------------------------------------------ small parts
def hang(bp, x, y, z, spec=HANG, drop=1):
    for k in range(1, drop + 1):
        bp.set(x, y + k, z, CHAIN)
    bp.set(x, y, z, spec)


def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def floor_box(bp, x0, x1, z0, z1, y, pal):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if bp.get(x, y + 1, z) == AIR and bp.get(x, y, z) not in (None, AIR):
                bp.set(x, y, z, pal(x, z) if callable(pal) else pal.pick(x, y, z))


def box(bp, x0, x1, y0, y1, z0, z1, spec):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, y, z, spec.pick(x, y, z) if isinstance(spec, Palette) else spec)


def chest(bp, x, y, z, facing, table):
    bp.chest(x, y, z, facing, loot=LOOT + table)


def banner(bp, x, y, z, facing, colour="red"):
    bp.set(x, y, z, BANNER.format(colour, facing))


def column(bp, x, z, y0, y1, r=1, band=GILD, body=PBB, cap=CHIS):
    """A square column (2r+1 wide) with a chiselled base and capital, gilded bands every 5."""
    for y in range(y0, y1 + 1):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if y in (y0, y1):
                    spec = cap
                elif (y - y0) % 5 == 0:
                    spec = band
                else:
                    spec = body if (dx == 0 or dz == 0) else PB
                bp.set(x + dx, y, z + dz, spec)


def flight(bp, cells, facing, fill=PBB, spec=PBBS, low=None, clear=4):
    """One stair flight: cells = [(x, z, feet)], the tread at feet - 1 facing the climb; solid under each tread
    down to ``low``; air above to feet + clear - 1."""
    for (x, z, f) in cells:
        bp.set(x, f - 1, z, stair(spec, facing))
        for y in range(low if low is not None else f - 3, f - 1):
            bp.set(x, y, z, fill)
        for y in range(f, f + clear):
            bp.set(x, y, z, AIR)


def rail_side(bp, cells, ox, oz, low, wall=PBBW, fill=PBB):
    """A parapet along the open side of a flight: solid from ``low`` up to each step's tread, a wall block at its
    feet (cells of the flight itself are skipped)."""
    own = {(x, z) for (x, z, f) in cells}
    for (x, z, f) in cells:
        q = (x + ox, z + oz)
        if q in own:
            continue
        for y in range(low, f):
            bp.set(q[0], y, q[1], fill)
        bp.set(q[0], f, q[1], wall)


def deck(bp, x0, x1, z0, z1, y, pal=DECKP, low=None, fill=PBB):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, pal.pick(x, y, z) if isinstance(pal, Palette) else pal)
            if low is not None:
                for yy in range(low, y):
                    bp.set(x, yy, z, fill)


def bunk(bp, x, y, z, facing, colour="red"):
    """A two-high bunk: a bed below, a slab shelf and a second bed above on a fence frame."""
    bp.bed(x, y, z, facing, colour)


def statue(bp, x, y, z, facing, s=1, body=PB, trim=GILD, flesh="gold_block"):
    """A piglin champion (9 * s tall) on a pedestal at (x, y, z), facing ``facing``: legs, a gilded belt and
    pauldrons, a round shield on the left arm, a gold sword raised in the right, a wide snouted head with tusks
    and a spiked crown."""
    fx, fz = DV[facing]
    rx, rz = -fz, fx                        # the statue's right (seen from the front: its left)

    def put(a, d, h, spec):
        for i in range(s):
            for j in range(s):
                for k in range(s):
                    bp.set(x + (a * s + i) * rx + (d * s + j) * fx, y + h * s + k,
                           z + (a * s + i) * rz + (d * s + j) * fz, spec)
    for a in (-1, 0, 1):
        for d in (-1, 0):
            put(a, d, 0, CHIS if a == 0 else GBS)
    for h in (1, 2):
        put(-1, 0, h, body)
        put(1, 0, h, body)
        put(0, 0, h, trim if h == 2 else "blackstone")
        put(-1, -1, h, body)
        put(1, -1, h, body)
    for h in (3, 4):
        for a in (-1, 0, 1):
            for d in (-1, 0):
                put(a, d, h, flesh if (a == 0 and d == 0 and h == 3) else body)
    for a in (-2, -1, 0, 1, 2):
        put(a, 0, 5, trim if abs(a) == 2 else body)
        put(a, -1, 5, trim if abs(a) == 2 else body)
    put(-2, 0, 4, body)
    put(-2, 1, 4, GBS)                      # the shield
    put(-2, 1, 3, trim)
    put(2, 0, 4, body)
    put(2, 0, 3, body)
    put(2, 1, 5, PBBW)                      # the sword's grip, guard and blade
    put(2, 1, 6, trim)
    for h in (7, 8, 9):
        put(2, 1, h, flesh)
    for h in (6, 7):
        for a in (-1, 0, 1):
            for d in (-1, 0):
                put(a, d, h, flesh if h == 6 else body)
    put(0, 1, 6, "raw_gold_block")          # the snout
    put(-1, 1, 6, trim)
    put(1, 1, 6, trim)
    put(-2, 0, 7, body)
    put(2, -1, 7, body)
    for a in (-1, 0, 1):
        put(a, 0, 8, trim if a else "gold_block")
        put(a, -1, 8, trim)


# ------------------------------------------------------------------ the arena
def arena(bp):
    """The sand floor: an oval of sand and red sand, a gilded ring, trapdoors of the beast lifts, the boss seal;
    braziers and banners on the podium; four champion statues on the stands at the axis ends."""
    for (cx, cz) in ((-14, 0), (14, 0), (0, -9), (0, 9)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(cx + dx, 5, cz + dz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,"
                                            "waterlogged=false]")
        for k in range(-2, 3):
            bp.set(cx + k, 5, cz - 2, GILD)
            bp.set(cx + k, 5, cz + 2, GILD)
            bp.set(cx - 2, 5, cz + k, GILD)
            bp.set(cx + 2, 5, cz + k, GILD)
    for x in range(-22, 23):
        for z in range(-17, 18):
            d = math.hypot(x / 11.0, z / 8.5)
            if 0.93 <= d < 1.07:
                bp.set(x, 5, z, LAMP if (x * 3 + z) % 7 == 0 else GBS if (x + z) % 2 else "gold_block")
            elif d < 0.2:
                bp.set(x, 5, z, GILD)
    bp.boss_seal(0, 5, 0, BOSS, 20)
    # the podium: braziers on the walk, banners down its face, the parapet
    for ix in range(SHAPE[0]):
        for iz in range(SHAPE[2]):
            u = M.U[ix, iz]
            x, z = ix + GX0, iz + GZ0
            if 0 <= u < 1.0 and bp.get(x, 14, z) not in (None, AIR):
                bp.set(x, 15, z, PBBW)
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        x, z = round((A0 + 3.5) * math.cos(a)), round((B0 + 3.5) * math.sin(a))
        if bp.get(x, 15, z) == AIR:
            brazier(bp, x, 15, z)
        # a banner on the podium's face below
        bx, bz = round((A0 + 0.2) * math.cos(a)), round((B0 + 0.2) * math.sin(a))
        f = OPP[outward(bx, bz)]
        ox, oz = DV[f]
        for _ in range(3):
            if bp.get(bx, 11, bz) == AIR:
                break
            bx, bz = bx + ox, bz + oz
        if bp.get(bx, 11, bz) == AIR:
            banner(bp, bx, 11, bz, f, "red" if k % 2 else "black")
    # champions on the stands, facing the sand
    for (x, z, f) in ((-30, 0, "east"), (30, 0, "west")):
        y = seat_top(u_at(x, z)) + 1
        statue(bp, x, y, z, f, s=2)
    for (x, z, f) in ((-9, 24, "north"), (9, 24, "north")):
        y = seat_top(u_at(x, z)) + 1
        statue(bp, x, y, z, f, s=1)


def gate_of_life(bp):
    """The arena's south gate back to the hub: an iron door, its lever on the arena side only (after the boss)."""
    floor_box(bp, -1, 1, 17, 29, G - 1, PATH)
    for y in range(G, G + 4):
        for x in (-2, 2):
            bp.set(x, y, 17, GILD if y == G + 3 else CHIS)
    for x in range(-2, 3):
        bp.set(x, G + 4, 17, GILD)
    bp.door(0, G, 27, "north", wood="iron")
    for y in (G, G + 1):
        bp.set(-1, y, 27, IRON)
        bp.set(1, y, 27, IRON)
    for x in (-1, 0, 1):
        bp.set(x, G + 2, 27, IRON)
        bp.set(x, G + 3, 27, IRON)
    lever(bp, 1, G + 1, 26, "north")
    hang(bp, 0, G + 3, 21, HANG, drop=0)


# ------------------------------------------------------------------ the champions' gate and the tunnel
def champions_gate(bp):
    """The colossal portal in the south facade: a round arch 11 wide and 20 high between two gate towers, gilded
    iron leaves with a wicket (3 x 4) in their middle, a champion's head keystone, banners."""
    zf = 64
    for x in range(-14, 15):
        for y in range(5, 30):
            r = math.hypot(x, max(0, y - 20))
            if r <= 5.4 and y >= 6:
                for z in (zf, zf - 1):
                    bp.set(x, y, z, AIR)
                # the leaves at z 62
                if abs(x) <= 1 and y <= G + 3:
                    bp.set(x, y, 62, AIR)
                elif x == 0:
                    bp.set(x, y, 62, "gold_block")
                elif y in (10, 17, 22):
                    bp.set(x, y, 62, GILD)
                elif (x + y) % 4 == 0:
                    bp.set(x, y, 62, GBS)
                else:
                    bp.set(x, y, 62, IRON)
            elif 5.4 < r <= 7.4 and y >= 6:
                for z in (zf, zf - 1, zf + 1):
                    bp.set(x, y, z, GILD if r > 6.6 else CHIS)
    for y in range(G, G + 4):
        bp.set(-2, y, 62, "gold_block")
        bp.set(2, y, 62, "gold_block")
    for x in range(-2, 3):
        bp.set(x, G + 4, 62, GILD)
    for x in range(-1, 2):
        for z in (62, 63, 64):
            bp.set(x, 5, z, CHIS)
    bp.set(0, 28, zf + 2, "piglin_head[rotation=0]")
    bp.set(0, 27, zf + 2, "gold_block")
    bp.set(0, 27, zf + 1, GILD)
    # the gate towers
    for sx in (-1, 1):
        round_tower(bp, sx * 12, 71, 5, 40, 4, wall=FACADE1, base=-3, steep=3, solid=True, rib=BASALT,
                    roof_block="blackstone")
        for y in (20, 32):
            banner(bp, sx * 12, y, 76, "south", "red")
    # the tunnel: path, lamps, the portcullis raised in its slot, arrow slits
    floor_box(bp, -2, 2, 47, 63, G - 1, PATH)
    for x in range(-2, 3):
        bp.set(x, G + 5, 50, "iron_bars")
        bp.set(x, G + 5, 58, "iron_bars")
    for z in (49, 54, 59):
        hang(bp, 0, G + 4, z, HANG, drop=0)
    for z in (52, 56):
        bp.set(-3, G + 2, z, "iron_bars")
        bp.set(3, G + 2, z, "iron_bars")


def towers_east(bp):
    """The beast gate on the east: two smaller towers, a blind portal of iron bars, a hoglin's skull trophy."""
    for sz in (-1, 1):
        round_tower(bp, 75, sz * 11, 5, 36, 4, wall=FACADE1, base=-3, steep=3, solid=True, rib=BASALT,
                    roof_block="blackstone")
    for z in range(-5, 6):
        for y in range(6, 22):
            r = math.hypot(z, max(0, y - 16))
            if r <= 5:
                bp.set(69, y, z, "iron_bars" if (z + y) % 3 else IRON)
            elif r <= 6.5:
                bp.set(69, y, z, GILD)
                bp.set(70, y, z, CHIS)
    for z in (-2, 2):
        bp.set(70, 22, z, "bone_block[axis=x]")
    bp.set(70, 23, 0, "piglin_head[rotation=12]")


def gate_of_death(bp):
    """The west portal (the dead are carried out): a black arch with gilded voussoirs and iron leaves, sealed."""
    for z in range(-6, 7):
        for y in range(6, 24):
            r = math.hypot(z, max(0, y - 17))
            x = -int(round(A0 + U_WALL1)) + 1
            if r <= 5:
                bp.set(x, y, z, "blackstone" if (z + y) % 5 else GBS)
            elif r <= 6.6:
                bp.set(x, y, z, GILD)
                bp.set(x - 1, y, z, CHIS)
    bp.set(-69, 24, 0, "wither_skeleton_skull[rotation=4]")


# ------------------------------------------------------------------ the betting hall (hub)
def betting_hall(bp):
    f = G
    floor_box(bp, -17, 17, 30, 46, f - 1, lambda x, z: (
        "gold_block" if (abs(x) <= 1 and 32 <= z <= 44 and (z % 3 == 0)) else
        GILD if abs(x) == 2 and 32 <= z <= 44 else STYLES["hall"][0].pick(x, f - 1, z)))
    # six great columns (3 x 3) carry the stands
    for (px, pz) in ((-11, 34), (11, 34), (-11, 42), (11, 42)):
        column(bp, px, pz, f, 17)
    # the bookmakers' counter along the north wall: dark oak counter, gold scales, ledgers
    for x in range(-14, 12):
        if abs(x) <= 2:
            continue
        bp.set(x, f, 32, "dark_oak_planks" if x % 4 else GBS)
        bp.set(x, f + 1, 32, "dark_oak_slab[type=bottom,waterlogged=false]" if x % 3 else
               "polished_blackstone_pressure_plate")
        if x % 4 == 0:
            bp.set(x, f + 2, 31, "iron_bars")
            bp.set(x, f + 3, 31, "iron_bars")
    for x in (-13, -7, 7, 13):
        bp.set(x, f + 1, 32, "lectern[facing=south,has_book=false,powered=false]")
    # the tally boards on the north wall: dark oak panels with gold and red "odds"
    for x in range(-11, 12):
        if abs(x) <= 2:
            continue
        for y in range(f + 4, f + 9):
            if bp.get(x, y, 30) == AIR:
                bp.set(x, y, 30, ("gold_block" if (x * 7 + y) % 5 == 0 else "red_terracotta" if (x + y) % 4 == 0
                                  else "dark_oak_planks"))
    # heaps of gold behind the counter, coin chests, the strongbox
    for (cx, cz, r) in ((-9, 31, 2.5), (9, 31, 2.5)):
        for x in range(int(cx - 3), int(cx + 4)):
            for z in range(30, 32):
                h = int(r - abs(x - cx) * 0.8 + hash01(x, z, 951) * 0.8)
                for y in range(f, f + max(0, h)):
                    if bp.get(x, y, z) == AIR:
                        bp.set(x, y, z, GOLDPILE.pick(x, y, z))
    chest(bp, -16, f, 31, "east", "crc_hall")
    bp.set(16, f, 31, "barrel[facing=up,open=false]")
    bp.set(15, f, 31, "barrel[facing=up,open=false]")
    # betting tables with gold piles and candles
    for (tx, tz) in ((-6, 38), (6, 38), (-6, 43), (6, 43)):
        for dx in (-1, 0, 1):
            bp.set(tx + dx, f, tz, "dark_oak_fence")
            bp.set(tx + dx, f + 1, tz, "red_carpet" if dx else "gold_block")
        bp.set(tx - 1, f + 2, tz, CANDLE.format(3))
        bp.set(tx, f, tz - 1, stair("dark_oak_stairs", "south"))
        bp.set(tx, f, tz + 1, stair("dark_oak_stairs", "north"))
    # the wager pit: a sunken model arena in the middle of the hall
    for x in range(-3, 4):
        for z in range(36, 41):
            if abs(x) == 3 or z in (36, 40):
                bp.set(x, f, z, PBBW)
            else:
                bp.set(x, f - 1, z, "sand")
    bp.set(0, f, 38, "piglin_head[rotation=8]")
    bp.set(-1, f, 37, "gold_block")
    # the hub waystone by the entrance, benches, banners
    bp.set(6, f, 45, MOD["waystone"])
    for x in (-8, -7, -6):
        bp.set(x, f, 46, stair(PBBS, "north"))
    for z in (35, 41):
        banner(bp, -16, f + 7, z, "east", "red")
        banner(bp, 16, f + 7, z, "west", "red")
    # chandeliers and wall lanterns
    for (x, z) in ((-5, 35), (5, 35), (-5, 42), (5, 42), (0, 33), (0, 45)):
        chandelier(bp, x, 17, z, soul=False, drop=3)
    for z in (33, 38, 44):
        bp.set(-17, f + 3, z, LAMP)
        bp.set(17, f + 3, z, LAMP)
    # the bookmakers' hay under the broken seats (the drop from the stands)
    for x in (12, 13, 14, 15):
        for z in (31, 32, 33):
            bp.set(x, f, z, HAY)
    bp.set(13, f + 1, 32, HAY)
    # door frames: west (barracks), east (the forge's portcullis)
    for (x, s) in ((-17, -1), (17, 1)):
        for z in (36, 40):
            for y in range(f, f + 5):
                bp.set(x, y, z, CHIS)
        for z in range(36, 41):
            bp.set(x, f + 5, z, GILD)
    # the beast lift's cage in the hub (the shortcut up from the hypogeum)
    lift_cage(bp)


def lift_cage(bp):
    """The cage over the beast lift's shaft (ladder at x 0, z 33; landing cell z 34): iron bars, a gilded roof, the
    iron door north... south at z 35 whose lever is inside the cage only."""
    f = G
    for x in (-1, 0, 1):
        for z in (32, 33, 34, 35):
            if (x, z) != (0, 33):
                bp.set(x, f - 1, z, IRON)
    for y in range(f, f + 3):
        for z in (32, 33, 34, 35):
            bp.set(-1, y, z, "iron_bars")
            bp.set(1, y, z, "iron_bars")
        bp.set(0, y, 32, "iron_bars")
    bp.set(-1, f + 1, 34, IRON)
    lever(bp, 0, f + 1, 34, "east")
    bp.door(0, f, 35, "south", wood="iron")
    bp.set(0, f + 2, 35, IRON)
    for x in (-1, 0, 1):
        for z in (32, 33, 34, 35):
            bp.set(x, f + 3, z, GILD)


# ------------------------------------------------------------------ the barracks
def barracks(bp):
    f = G
    floor_box(bp, -44, -24, 18, 38, f - 1, STYLES["barracks"][0])
    # bunks along the outer (west and south) walls, footlockers between them
    for z in range(20, 37, 3):
        bp.bed(-43, f, z, "east", "red" if z % 2 else "black")
        bp.set(-43, f, z + 1, "barrel[facing=up,open=false]")
        bp.set(-43, f + 2, z, "crimson_slab[type=bottom,waterlogged=false]")
        bp.set(-43, f + 2, z + 1, "crimson_slab[type=bottom,waterlogged=false]")
    for x in range(-40, -27, 3):
        bp.bed(x, f, 37, "north", "black" if x % 2 else "red")
        bp.set(x + 1, f, 37, "barrel[facing=up,open=false]")
    # weapon racks on the east wall: fences and gold "blades"
    for z in range(20, 33, 2):
        bp.set(-24, f, z, "crimson_fence")
        bp.set(-24, f + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]" if z % 4 else
               "gold_block")
        bp.set(-24, f + 3, z, BANNER.format("red", "west") if z % 4 == 0 else LAMP)
    # training dummies: hay bodies on fence posts, carved-pumpkin heads, a sparring ring of chains
    for (x, z) in ((-36, 25), (-31, 25), (-36, 30), (-31, 30)):
        bp.set(x, f, z, "crimson_fence")
        bp.set(x, f + 1, z, HAY)
        bp.set(x, f + 2, z, "carved_pumpkin[facing=south]")
        bp.set(x - 1, f + 1, z, "crimson_trapdoor[facing=west,half=top,open=true,waterlogged=false]")
    for x in range(-38, -28):
        for z in (22, 33):
            if x % 2 == 0:
                bp.set(x, f, z, NBF)
    # the long table, a grindstone, the lanista's chest
    for x in range(-40, -32):
        bp.table(x, f, 34, top="crimson_pressure_plate", leg=NBF) if x % 3 else None
    bp.set(-27, f, 20, "grindstone[face=floor,facing=north]")
    bp.set(-28, f, 20, "smithing_table")
    chest(bp, -27, f, 37, "north", "crc_barracks")
    chest(bp, -44, f, 19, "east", "crc_barracks")
    for (x, z) in ((-38, 21), (-30, 21), (-38, 35), (-30, 35), (-34, 28)):
        hang(bp, x, 13, z, HANG, drop=1)
    for z in (24, 32):
        bp.set(-44, f + 3, z, LAMP)
    bp.spawner(-33, f, 28, MOB_BRUTE)
    # the opening to the stair down (north side) and its rail
    for x in range(-42, -25):
        if bp.get(x, f, 17) not in (None, AIR):
            pass
    for x in range(-42, -25):
        bp.set(x, f - 1, 17, PATH.pick(x, f - 1, 17)) if bp.get(x, f, 17) == AIR else None


def barracks_stair(bp):
    """Down from the barracks (feet 6) to the hypogeum's muster hall (feet -8): a doorway in the barracks' north wall,
    a flight west along z 10..12, a landing, a second flight south -> north into the muster hall."""
    for x in range(-29, -25):
        for z in range(14, 18):
            for y in range(G, G + 4):
                bp.set(x, y, z, AIR)
            bp.set(x, G - 1, z, PATH.pick(x, G - 1, z))
    deck(bp, -29, -26, 9, 13, G - 1, PATH, low=HF - 1)
    cells = [(-30 - i, z, G - 1 - i) for i in range(7) for z in (10, 11, 12)]
    flight(bp, cells, "east", low=HF - 1)
    rail_side(bp, cells, 0, -1, HF - 1)
    rail_side(bp, cells, 0, 1, HF - 1)
    deck(bp, -39, -37, 9, 12, G - 8, PATH, low=HF - 1)
    for x in range(-39, -36):
        for z in range(9, 13):
            for y in range(G - 7, G - 3):
                bp.set(x, y, z, AIR)
    for (x, z) in [(-40, z) for z in range(9, 14)] + [(x, 13) for x in (-39, -38, -37)]:
        for y in range(HF - 1, G - 7):
            bp.set(x, y, z, PBB)
        bp.set(x, G - 7, z, PBBW)
    cells = [(x, 8 - i, G - 8 - i) for i in range(6) for x in (-39, -38, -37)]
    flight(bp, cells, "north", low=HF - 1)
    rail_side(bp, cells, -1, 0, HF - 1)
    rail_side(bp, cells, 1, 0, HF - 1)
    for x in range(-29, -25):
        bp.set(x, G, 9, PBBW)
    for (x, z, y) in ((-33, 11, G + 2), (-38, 11, G - 4)):
        hang(bp, x, y, z, HANG, drop=0)
    bp.set(-30, G + 1, 13, LAMP)


# ------------------------------------------------------------------ the hypogeum
def hypogeum(bp):
    """Under the sand: the cage gallery (x -26..26) between rows of piers, cells behind iron bars on both sides
    (iron doors opened by a lever on the gallery side), the four lift shafts up to the trapdoors in the sand, the
    north and south aisles, the south corridor and the beast lift's ladder up into the hub."""
    f = HF
    floor_box(bp, -26, 26, -13, 13, f - 1, lambda x, z: (
        PATH.pick(x, f - 1, z) if abs(z) <= 2 or abs(x) <= 1 else HYPO_FLOOR.pick(x, f - 1, z)))
    for x0 in range(-24, 24, 6):
        for sz in (-1, 1):
            zf = sz * 4
            # the piers of the gallery's arcade, the partition wall between cells
            for y in range(f, 2):
                bp.set(x0, y, sz * 3, PBB if y < 1 else CHIS)
                bp.set(x0 + 1, y, sz * 3, PBB if y < 1 else CHIS)
                for z in range(min(zf, sz * 13), max(zf, sz * 13) + 1):
                    bp.set(x0 + 1, y, z, HYPO_WALL.pick(x0 + 1, y, z))
            if x0 + 2 <= 0 <= x0 + 5:
                continue                                    # the aisle crosses this bay
            for x in range(x0 + 2, x0 + 6):
                for y in range(f, f + 4):
                    bp.set(x, y, zf, "iron_bars")
            for y in range(f + 4, 2):
                for x in range(x0 + 2, x0 + 6):
                    bp.set(x, y, zf, HYPO_WALL.pick(x, y, zf))
            fc = "north" if sz > 0 else "south"
            bp.door(x0 + 3, f, zf, fc, wood="iron")
            for y in (f, f + 1, f + 2):
                bp.set(x0 + 4, y, zf, CHIS)
            lever(bp, x0 + 4, f + 1, zf - sz, fc)
            cx, cz = x0 + 4, sz * 9
            h = hash01(x0, sz, 961)
            if h < 0.3:
                bp.set(cx, f, cz, HAY)
                bp.set(cx + 1, f, cz + sz, "bone_block[axis=x]")
            elif h < 0.55:
                bp.set(cx, f, cz, "cauldron")
                bp.set(cx - 1, f, cz + sz, "skeleton_skull[rotation=3]")
            elif h < 0.8:
                bp.set(cx, f, cz + 3 * sz, "chiseled_polished_blackstone")
                for y in range(f + 1, 2):
                    bp.set(cx, y, cz + 3 * sz, CHAIN)
            else:
                bp.set(cx, f, cz, "barrel[facing=up,open=false]")
            hang(bp, x0 + 3, 0, sz * 8, HANG, drop=1)
    # the beasts in two cells, loot in two others
    bp.spawner(-14, f, 9, MOB_ZPIG)
    bp.spawner(16, f, -9, MOB_HOGLIN)
    chest(bp, -10, f, -11, "south", "crc_cages")
    chest(bp, 22, f, 11, "north", "crc_cages")
    # the aisles north and south through the cell rows
    for z in list(range(4, 14)) + list(range(-13, -3)):
        for x in (-1, 0, 1):
            for y in range(f, f + 4):
                bp.set(x, y, z, AIR)
            bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))
        for x in (-2, 2):
            for y in range(f, 2):
                bp.set(x, y, z, HYPO_WALL.pick(x, y, z))
    # lamps along the gallery
    for x in range(-24, 25, 6):
        hang(bp, x + 3, 0, 0, HANG, drop=1)
    for x in (-26, 26):
        for z in (-8, 8):
            bp.set(x, f + 3, z, LAMP)
    # the lift shafts to the trapdoors in the sand: open through the slab, chains, a brass pulley
    for (cx, cz) in ((-14, 0), (14, 0), (0, -9), (0, 9)):
        for y in range(2, 5):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bp.set(cx + dx, y, cz + dz, AIR)
        for dx in (-1, 1):
            for y in range(f + 4, 5):
                if bp.get(cx + dx, y, cz - 1) == AIR:
                    bp.set(cx + dx, y, cz - 1, CHAIN)
    # the south corridor and the beast lift's ladder up into the hub's cage
    floor_box(bp, -1, 1, 14, 32, f - 1, PATH)
    for y in range(f, 6):
        bp.set(0, y, 33, LADDER.format("north"))
    for z in (18, 26):
        hang(bp, 0, f + 3, z, HANG, drop=0)
    bp.set(-2, f + 2, 30, LAMP)


def muster_hall(bp):
    """The gladiators' muster hall under the west stands: benches, a rack of shields, the gods' altar of gold."""
    f = HF
    floor_box(bp, -48, -27, -12, 14, f - 1, HYPO_FLOOR)
    for (px, pz) in ((-42, -6), (-33, -6), (-42, 7), (-33, 7)):
        column(bp, px, pz, f, 2, r=1)
    for z in range(-10, 12, 3):
        for x in (-47, -46):
            bp.set(x, f, z, stair("blackstone_stairs", "east"))
    for x in range(-45, -29, 4):
        bp.set(x, f + 2, -12 + 1, BANNER.format("black" if x % 8 else "red", "south"))
    # the altar of gold at the west end
    for z in range(-3, 4):
        bp.set(-47, f, z, GBS)
        bp.set(-47, f + 1, z, "gold_block" if z == 0 else GILD)
    bp.set(-47, f + 2, 0, "piglin_head[rotation=4]")
    bp.set(-47, f + 2, -2, CAMP)
    bp.set(-47, f + 2, 2, CAMP)
    for (x, z) in ((-38, 0), (-30, -9), (-30, 10), (-44, -10), (-44, 12)):
        hang(bp, x, 1, z, HANG, drop=1)
    chest(bp, -27, f, -11, "west", "crc_barracks")
    bp.spawner(-36, f, -9, MOB_BRUTE)


def hoglin_pens(bp):
    f = HF
    floor_box(bp, 28, 48, -14, 14, f - 1, lambda x, z: PATH.pick(x, f - 1, z) if abs(z) <= 2 else
              STYLES["pens"][0].pick(x, f - 1, z))
    # four pens of crimson fence, gates on the aisle, hay, troughs, crimson roots and a fungus
    for (x0, x1, z0, z1) in ((29, 37, -13, -4), (39, 47, -13, -4), (29, 37, 4, 13), (39, 47, 4, 13)):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, f, z, FENCE)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                bp.set(x, f, z, FENCE)
        gz = z1 if z0 < 0 else z0
        bp.set((x0 + x1) // 2, f, gz, f"crimson_fence_gate[facing={'north' if z0 < 0 else 'south'},in_wall=false,"
                                      f"open=false,powered=false]")
        for x in range(x0 + 1, x1):
            for z in range(z0 + 1, z1):
                h = hash01(x, z, 971)
                if h < 0.12:
                    bp.set(x, f, z, "crimson_roots")
                elif h < 0.17:
                    bp.set(x, f, z, HAY)
        bp.set(x0 + 1, f, z0 + 1 if z0 < 0 else z1 - 1, "composter[level=3]")
        bp.set(x0 + 2, f, z0 + 1 if z0 < 0 else z1 - 1, "cauldron")
        hang(bp, (x0 + x1) // 2, 2, (z0 + z1) // 2, HANG, drop=1)
    bp.spawner(33, f, -9, MOB_HOGLIN)
    bp.spawner(43, f, 9, MOB_HOGLIN)
    # the feed store: crimson fungus and warped fungus sacks, hay stacks
    for (x, z) in ((47, -1), (47, 1), (46, -1)):
        bp.set(x, f, z, HAY)
        bp.set(x, f + 1, z, HAY) if x == 47 else None
    chest(bp, 29, f, 1, "east", "crc_pens")
    for x in (30, 38, 46):
        hang(bp, x, 2, 0, HANG, drop=1)


def lift_hall(bp):
    """The beast lift hall: a void from the hypogeum (feet -8) up past the gallery (feet 6), three cages hanging on
    chains from a capstan wheel under the roof, gear wheels, the stair along the north and east walls."""
    f = HF
    floor_box(bp, 50, 62, -12, 12, f - 1, DECKP)
    # flight 1 along the north wall, rising east (feet -7 .. 1)
    cells = [(51 + i, z, f + 1 + i) for i in range(9) for z in (-11, -10, -9)]
    flight(bp, cells, "east", low=f - 1)
    rail_side(bp, cells, 0, 1, f - 1)
    # the landing (feet 1) in the north-east corner
    deck(bp, 60, 62, -12, -6, f + 8, PATH, low=f - 1)
    for x in range(60, 63):
        for z in range(-12, -5):
            for y in range(f + 9, f + 13):
                bp.set(x, y, z, AIR)
    for z in (-8, -7, -6):
        for y in range(f - 1, f + 9):
            bp.set(59, y, z, PBB)
        bp.set(59, f + 9, z, PBBW)
    # flight 2 along the east wall, rising south to the gallery (feet 2 .. 6)
    cells = [(x, -5 + i, f + 10 + i) for i in range(5) for x in (60, 61, 62)]
    flight(bp, cells, "south", low=f - 1)
    rail_side(bp, cells, -1, 0, f - 1)
    # the gallery at feet 6: along the east wall (z 0..12) and the south wall to the west door
    deck(bp, 59, 62, 0, 12, G - 1, DECKP)
    deck(bp, 45, 62, 9, 12, G - 1, DECKP)
    for (x, z) in ((59, 0), (59, 5), (53, 9), (47, 9), (59, 9)):
        for y in range(G - 3, G - 1):
            bp.set(x, y, z, IRON)
    for z in range(0, 9):
        bp.set(59, G, z, IRON_WALL)
    for x in range(50, 60):
        bp.set(x, G, 9, IRON_WALL)
    # the capstan wheel under the roof and three cages on chains at three heights
    for (cx, cz, yb) in ((54, -3, f + 2), (54, 3, f + 9), (55, 0, G + 6)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(cx + dx, yb, cz + dz, IRON)
                for y in range(yb + 1, yb + 4):
                    if dx or dz:
                        bp.set(cx + dx, y, cz + dz, "iron_bars")
                bp.set(cx + dx, yb + 4, cz + dz, BRASS)
        for y in range(yb + 5, 20):
            bp.set(cx, y, cz, CHAIN)
    for y in (18,):
        for x in range(51, 61):
            bp.set(x, y, 0, IRON if x % 3 else GEAR)
    for (gx, gz) in ((52, 0), (58, 0)):
        for dy in range(-3, 4):
            for dz in range(-3, 4):
                if 2.2 <= math.hypot(dy, dz) <= 3.4:
                    bp.set(gx, 15 + dy, gz + dz, GEAR)
        bp.set(gx, 15, gz, BRASS)
    # the floor of the pit: the capstan with crimson spokes
    for dx in range(-3, 4):
        bp.set(56 + dx, f, 6, "crimson_stem[axis=x]") if dx else bp.set(56, f, 6, IRON)
    for dz in range(-3, 4):
        bp.set(56, f, 6 + dz, "crimson_stem[axis=z]") if dz else None
    for y in range(f + 1, f + 4):
        bp.set(56, y, 6, IRON)
    bp.set(56, f + 4, 6, BRASS)
    chest(bp, 51, f, 11, "east", "crc_lifts")
    for (x, z, y) in ((52, -10, 4), (61, -9, 9), (56, 10, 14), (52, 4, 14), (61, 4, 14)):
        hang(bp, x, y, z, HANG, drop=1)
    for (x, z) in ((50, -6), (50, 6), (62, 6)):
        bp.set(x, f + 2, z, LAMP)
    bp.spawner(55, f, -5, MOB_HOUND)


def forge(bp):
    """The armoury forge: the champions' hearth (lava under bars, a hood and chimney), anvils, smithing tables,
    blast furnaces, quench troughs, racks of finished gold weapons, the master's chest."""
    f = G
    floor_box(bp, 24, 44, 18, 38, f - 1, STYLES["forge"][0])
    # the hearth on the south wall: lava under iron bars, a hood of blackstone
    for x in range(30, 39):
        for z in (36, 37, 38):
            bp.set(x, f - 1, z, LAVA if z > 36 and 31 <= x <= 37 else PBB)
            bp.set(x, f, z, "iron_bars" if z > 36 and 31 <= x <= 37 else CHIS)
        bp.set(x, f + 4, 37, stair(PBBS, "north", "top"))
        for y in range(f + 5, 16):
            bp.set(x, y, 38, PB)
    for x in range(31, 38):
        bp.set(x, f - 2, 37, PBB)
        bp.set(x, f - 2, 38, PBB)
        bp.set(x, f - 1, 38, PBB)
    for y in range(f + 1, f + 4):
        bp.set(30, y, 37, CHIS)
        bp.set(38, y, 37, CHIS)
    # anvils and smithing tables round the hearth
    for (x, z) in ((32, 34), (36, 34)):
        bp.set(x, f, z, "anvil[facing=east]")
    bp.set(34, f, 33, "smithing_table")
    for x in (26, 27, 28):
        bp.set(x, f, 37, "blast_furnace[facing=north,lit=true]")
    bp.set(29, f, 37, "furnace[facing=north,lit=true]")
    # the quench trough (lava? no: a cauldron row), the grindstones
    for x in range(40, 44):
        bp.set(x, f, 36, "cauldron")
    bp.set(42, f, 33, "grindstone[face=floor,facing=east]")
    # racks of champion weapons along the north wall: gold blades on crimson racks
    for x in range(26, 43, 2):
        bp.set(x, f, 19, FENCE)
        bp.set(x, f + 1, 19, "gold_block" if x % 4 else "lightning_rod[facing=up,powered=false,waterlogged=false]")
        bp.set(x, f + 2, 19, GILD if x % 4 else AIR)
    for x in range(27, 43, 4):
        banner(bp, x, f + 5, 19, "south", "yellow" if x % 8 == 3 else "red")
    # an iron ingot pile and gold ore crates
    for (x, z) in ((25, 25), (25, 26), (26, 25)):
        bp.set(x, f, z, "raw_gold_block" if (x + z) % 2 else "raw_iron_block")
    bp.set(25, f + 1, 25, "raw_gold_block")
    chest(bp, 43, f, 22, "west", "crc_forge")
    for (x, z) in ((29, 24), (39, 24), (29, 32), (39, 32), (34, 28)):
        hang(bp, x, 15, z, HANG, drop=2)
    bp.set(44, f + 3, 28, LAMP)
    bp.set(24, f + 3, 28, LAMP)
    bp.spawner(34, f, 26, MOB_SENTRY)
    # the one-way portcullis into the hub: an iron door at x 18, its lever on the forge side (east)
    floor_box(bp, 18, 23, 37, 39, f - 1, PATH)
    bp.door(18, f, 38, "east", wood="iron")
    for z in (37, 39):
        for y in range(f, f + 4):
            bp.set(18, y, z, "iron_bars")
    for z in (37, 38, 39):
        bp.set(18, f + 2, z, "iron_bars")
        bp.set(18, f + 3, z, "iron_bars")
    bp.set(18, f + 1, 37, IRON)
    lever(bp, 19, f + 1, 37, "east")
    # the passage from the gallery
    floor_box(bp, 45, 46, 13, 21, f - 1, PATH)
    for z in range(19, 22):
        for y in range(f, f + 4):
            bp.set(44, y, z, AIR) if z in (19, 20) else None
    bp.set(44, f - 1, 19, PATH.pick(44, f - 1, 19))
    bp.set(44, f - 1, 20, PATH.pick(44, f - 1, 20))


def grand_stair(bp):
    """Up through the stands from the gallery (feet 6, z 12) to the upper ambulatory (feet 24, z 30): 18 steps
    south, 3 wide, a landing halfway."""
    cells = []
    f = G
    z = 13
    for i in range(18):
        if i == 9:
            for x in (47, 48, 49):
                for zz in (z, z + 1):
                    bp.set(x, f - 1, zz, PATH.pick(x, f - 1, zz))
                    for y in range(f - 3, f - 1):
                        bp.set(x, y, zz, PBB)
                    for y in range(f, f + 4):
                        bp.set(x, y, zz, AIR)
            z += 2
        f += 1
        for x in (47, 48, 49):
            cells.append((x, z, f))
        z += 1
    flight(bp, cells, "south", low=None)
    for (x, z, f) in cells:
        for y in range(f + 4, f + 6):
            if not solid(x, y, z) and bp.get(x, y, z) in (None, AIR):
                bp.set(x, y, z, PBB)
    for (z, y) in ((16, 12), (24, 19), (31, 27)):
        if bp.get(48, y, z) == AIR:
            hang(bp, 48, y, z, HANG, drop=0)


# ------------------------------------------------------------------ the upper ambulatory
def ambulatory(bp):
    f = UF
    u0, u1, t0, t1, y0, y1 = AMB
    cells = np.argwhere((M.U >= u0) & (M.U < u1) & (M.TH >= t0) & (M.TH <= t1))
    for ix, iz in cells.tolist():
        x, z = ix + GX0, iz + GZ0
        if bp.get(x, f, z) == AIR and not (bp.get(x, f - 1, z) or "").endswith("_stairs"):
            u = M.U[ix, iz]
            th = M.TH[ix, iz]
            k, w, L = bay_coords(th)
            bp.set(x, f - 1, z, GILD if abs(u - 39.25) < 0.5 and k % 2 == 0 else STYLES["amb"][0].pick(x, f - 1, z))
    # cross arches every bay (a rib of chiselled blackstone under the ceiling) and lamps
    for ix, iz in cells.tolist():
        x, z = ix + GX0, iz + GZ0
        k, w, L = bay_coords(M.TH[ix, iz])
        if abs(w) < 0.55:
            bp.set(x, y1, z, CHIS)
            if abs(M.U[ix, iz] - 39.25) < 0.5:
                bp.set(x, y1, z, LAMP) if k % 2 else hang(bp, x, y1 - 1, z, HANG, drop=0)
    # window sills (wall blocks) in the arched windows
    for ix, iz in np.argwhere((M.U >= 43.5) & (M.U < 46.5)).tolist():
        x, z = ix + GX0, iz + GZ0
        th = M.TH[ix, iz]
        if not amb_window_bay(th):
            continue
        k, w, L = bay_coords(th)
        if abs(w) <= 1.6 and bp.get(x, f, z) == AIR:
            bp.set(x, f, z, NBW)
            bp.set(x, f - 1, z, GILD)
    # things along the way: benches, banners, braziers, spawners, a chest
    spots = [(-60.0, "bench"), (-30.0, "chest"), (-10.0, "spawner_guard"), (12.0, "banner"), (30.0, "spawner_piglin"),
             (-75.0, "brazier"), (-45.0, "banner"), (0.0, "brazier")]
    for th, kind in spots:
        a = math.radians(th)
        u = 41.0
        x, z = round((A0 + u) * math.cos(a)), round((B0 + u) * math.sin(a))
        fc = OPP[outward(x, z)]
        if bp.get(x, f, z) != AIR:
            continue
        if kind == "bench":
            bp.set(x, f, z, stair(NBS, OPP[fc]))
        elif kind == "chest":
            chest(bp, x, f, z, fc, "crc_ambulatory")
        elif kind == "spawner_guard":
            ui = 39.0
            bp.spawner(round((A0 + ui) * math.cos(a)), f, round((B0 + ui) * math.sin(a)), MOB_GUARD)
        elif kind == "spawner_piglin":
            ui = 39.0
            bp.spawner(round((A0 + ui) * math.cos(a)), f, round((B0 + ui) * math.sin(a)), MOB_PIGLIN)
        elif kind == "banner":
            ux, uz = round((A0 + 36.6) * math.cos(a)), round((B0 + 36.6) * math.sin(a))
            if bp.get(ux, f + 3, uz) not in (None, AIR):
                o = outward(ux, uz)
                ox, oz = DV[o]
                if bp.get(ux + ox, f + 3, uz + oz) == AIR:
                    banner(bp, ux + ox, f + 3, uz + oz, o, "red")
        elif kind == "brazier":
            brazier(bp, x, f, z)


# ------------------------------------------------------------------ the royal box, the purse vault, the royal stair
def royal_box(bp):
    f = UF
    floor_box(bp, -12, 12, -46, -24, f - 1, lambda x, z: (
        "gold_block" if abs(x) <= 1 and z % 4 == 0 else GILD if abs(x) == 2 else
        STYLES["royal"][0].pick(x, f - 1, z)))
    # the open front over the sand: a gilded parapet, the canopy on four columns over the podium
    for x in range(-10, 11):
        for y in range(f, f + 9):
            bp.set(x, y, -23, AIR)
        bp.set(x, f - 1, -23, GILD)
        bp.set(x, f, -23, PBBW)
    for x in range(-13, 14):
        for z in range(-23, -19):
            bp.set(x, 34, z, GILD if z == -20 or abs(x) == 13 else PB)
            bp.set(x, 35, z, "polished_blackstone_slab[type=bottom,waterlogged=false]" if z > -23 else PB)
    for x in (-10, -4, 4, 10):
        for y in range(15, 34):
            bp.set(x, y, -21, BASALT if y % 5 else GILD)
        bp.set(x, 14, -21, CHIS)
    for x in range(-12, 13, 3):
        banner(bp, x, 33, -19, "south", "red" if x % 2 else "yellow")
    # the thrones on a dais, the champion's standard, the site of grace
    for x in range(-4, 5):
        for z in range(-45, -40):
            bp.set(x, f, z, GBS if (x + z) % 3 else "gold_block")
    for x in (-2, 0, 2):
        bp.set(x, f + 1, -42, stair("blackstone_stairs", "north"))
        bp.set(x, f + 2, -43, GILD if x else "gold_block")
    bp.set(0, f + 3, -43, "piglin_head[rotation=8]")
    for x in range(-3, 4):
        bp.set(x, f + 1, -44, GBS)
        bp.set(x, f + 2, -44, GBS if abs(x) == 3 else "gold_block")
    bp.set(0, f, -30, MOD["waystone"])
    # benches of the court on both sides, carpets, braziers, gold heaps
    for z in range(-38, -26, 2):
        bp.set(-11, f, z, stair(PBBS, "west"))
        bp.set(11, f, z, stair(PBBS, "east"))
    for x in range(-1, 2):
        for z in range(-39, -24):
            if bp.get(x, f, z) == AIR:
                bp.set(x, f, z, "red_carpet")
    for (x, z) in ((-8, -26), (8, -26), (-8, -40), (8, -40)):
        brazier(bp, x, f, z, big=True)
    for (x, z) in ((-6, -33), (6, -33), (0, -36), (0, -27)):
        chandelier(bp, x, 33, z, drop=3)
    chest(bp, -12, f, -45, "east", "crc_royal")
    for (x, z) in ((11, -45), (10, -45), (11, -44)):
        bp.set(x, f, z, GOLDPILE.pick(x, f, z))
    for z in (-42, -35, -28):
        banner(bp, -12, f + 5, z, "east", "red")
        banner(bp, 12, f + 5, z, "west", "red")
    # the doorway to the ambulatory
    for y in range(f, f + 5):
        for x in (-3, 3):
            bp.set(x, y, -47, CHIS if y < f + 4 else GILD)
    floor_box(bp, -2, 2, -52, -47, f - 1, STYLES["royal"][0])
    # the east door to the stair down onto the podium
    for z in (-31, -30):
        for y in range(f, f + 4):
            bp.set(13, y, z, AIR)
        bp.set(13, f - 1, z, GILD)
    box_to_podium(bp)


def box_to_podium(bp):
    """Outside the box's east door, a stair down over the seats to the podium walk (feet 15)."""
    cells = []
    for i in range(9):
        z = -29 + i
        for x in (14, 15):
            cells.append((x, z, UF - 1 - i))
    for x in (14, 15):
        for z in (-32, -31, -30):
            bp.set(x, UF - 1, z, PATH.pick(x, UF - 1, z))
            for y in range(PF - 1, UF - 1):
                bp.set(x, y, z, PBB)
            for y in range(UF, UF + 4):
                bp.set(x, y, z, AIR)
        bp.set(16, UF, -32, PBBW)
        bp.set(16, UF, -31, PBBW)
        bp.set(16, UF, -30, PBBW)
    for x in (14, 15):
        for z in (-33,):
            bp.set(x, UF, z, PBBW)
    flight(bp, cells, "north", low=PF - 1)
    for (x, z, f) in cells:
        if x == 15:
            bp.set(16, f, z, PBBW) if bp.get(16, f, z) in (None, AIR) else None
    for x in (14, 15):
        for z in (-20, -19, -18):
            bp.set(x, PF - 1, z, PATH.pick(x, PF - 1, z))
            for y in range(PF, PF + 4):
                if bp.get(x, y, z) != PBBW:
                    bp.set(x, y, z, AIR)


def purse_vault(bp):
    """The champion's purse vault under the royal box: gold heaps, chests, the champion's belt on a stand; behind
    sealed bars in the podium's north face."""
    f = G
    floor_box(bp, -8, 8, -38, -26, f - 1, STYLES["purse"][0])
    for (cx, cz, r) in ((-5, -35, 3.0), (5, -35, 3.0), (-6, -29, 2.0), (6, -29, 2.0)):
        for x in range(int(cx - 3), int(cx + 4)):
            for z in range(int(cz - 3), int(cz + 4)):
                h = int(r - math.hypot(x - cx, z - cz) * 0.9 + hash01(x, z, 981) * 0.7)
                for y in range(f, f + max(0, h)):
                    if bp.get(x, y, z) == AIR:
                        bp.set(x, y, z, GOLDPILE.pick(x, y, z))
    for x in (-1, 0, 1):
        bp.set(x, f, -37, GBS)
    bp.set(0, f + 1, -37, "gold_block")
    bp.set(0, f + 2, -37, "piglin_head[rotation=0]")
    chest(bp, -2, f, -37, "south", "crc_purse")
    chest(bp, 2, f, -37, "south", "crc_purse")
    chest(bp, 0, f, -32, "south", "crc_purse")
    for (x, z) in ((-4, -31), (4, -31), (0, -35)):
        hang(bp, x, 12, z, HANG, drop=1)
    for z in (-34, -28):
        bp.set(-8, f + 2, z, LAMP)
        bp.set(8, f + 2, z, LAMP)
    # the bars at the podium face (z -17), gilded frame, the corridor
    floor_box(bp, -1, 1, -25, -17, f - 1, PATH)
    for x in (-1, 0, 1):
        for y in range(f, f + 3):
            bp.set(x, y, -17, MOD["vault_bars"])
        bp.set(x, f + 3, -17, GILD)
    for y in range(f, f + 4):
        bp.set(-2, y, -17, GILD)
        bp.set(2, y, -17, GILD)
    hang(bp, 0, f + 2, -21, HANG, drop=1)


def royal_stair(bp):
    """The royal stair: from the box's west door down inside the stands to the arena's narrow passage (the mist)."""
    floor_box(bp, -17, -14, -47, -44, UF - 1, STYLES["royal"][0])
    steps = royal_stair_steps()
    for i, (z, f) in enumerate(steps):
        flat = i in (9, 10)
        for x in (-17, -16, -15):
            if flat:
                bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))
            else:
                bp.set(x, f - 1, z, stair(PBBS, "north"))
            for y in range(f - 3, f - 1):
                bp.set(x, y, z, PBB)
    for (z, f) in steps[::5]:
        bp.set(-18, f + 2, z, LAMP)
        bp.set(-14, f + 2, z, LAMP)
    floor_box(bp, -17, -15, -23, -12, G - 1, PATH)
    for z in (-21, -15):
        hang(bp, -16, G + 4, z, HANG, drop=0)
    bp.mist(-17, G, -13, -15, G + 3, -13)


# ------------------------------------------------------------------ the dominant: the golden champion
def champion_tower(bp):
    """The imperial tower behind the royal box, the colossal gold piglin champion on it, facing the arena."""
    piglin_idol(bp, 55, zc=-65)
    # the blind arches: long banners, a champion at the foot of the middle one, braziers
    for (c, col) in ((-8, "red"), (0, "yellow"), (8, "red")):
        for y in (30, 27, 24):
            banner(bp, c, y, -73, "north", col)
        if c == 0:
            statue(bp, 0, 8, -73, "north", s=1)
        else:
            brazier(bp, c, 8, -73, big=False)
    for sx in (-14, 14):
        for c in (-68, -62):
            for y in (24, 21):
                banner(bp, sx, y, c, "east" if sx > 0 else "west", "red")
    # the hip roof of the royal box, gilded ridge
    bp.pyramid_roof(-13, -56, 13, -24, 36, "blackstone_stairs", overhang=0, cap=GILD)
    for x in range(-11, 12):
        for z in (-71, -59):
            bp.set(x, 55, z, PBBW if x % 3 else GILD)
    for z in range(-71, -58):
        bp.set(-11, 55, z, PBBW if z % 3 else GILD)
        bp.set(11, 55, z, PBBW if z % 3 else GILD)
    for (x, z) in ((-11, -71), (11, -71), (-11, -59), (11, -59)):
        brazier(bp, x, 55, z, big=True)
    for x in range(-12, 13, 4):
        banner(bp, x, 48, -74, "north", "red" if x % 8 else "yellow")


# ------------------------------------------------------------------ the facade's furniture
def facade_details(bp):
    """Statues of champions in the ground-storey niches, banners in the third storey, braziers at the piers; the
    velarium masts on the attic."""
    done = set()
    for ix, iz in np.argwhere((M.U >= 45.4) & (M.U < 46.4)).tolist():
        x, z = ix + GX0, iz + GZ0
        th = M.TH[ix, iz]
        k, w, L = bay_coords(th)
        if abs(w) > 0.5 or k in done:
            continue
        done.add(k)
        if k in GATE_BAYS or k in (BEAST_BAY, DEATH_BAY) or abs(x) <= 15 and z > 0:
            continue
        fc = outward(x, z)
        ox, oz = DV[fc]
        # the niche floor: the first air cell outward from the wall at y 6
        px, pz = x, z
        for _ in range(3):
            if bp.get(px, 6, pz) == AIR:
                break
            px, pz = px + ox, pz + oz
        if k % 2 == 0:
            statue(bp, px - ox, 6, pz - oz, fc) if bp.get(px - ox, 6, pz - oz) == AIR else statue(bp, px, 6, pz, fc)
        else:
            brazier(bp, px, 6, pz, big=False)
            for y in (10, 11):
                pass
        # the third storey: a banner hung at the back of the niche
        bx, bz = x, z
        for _ in range(3):
            if bp.get(bx, 40, bz) == AIR:
                break
            bx, bz = bx + ox, bz + oz
        if bp.get(bx, 40, bz) == AIR:
            banner(bp, bx, 40, bz, fc, "red" if k % 3 else "yellow")
        # second storey niches off the ambulatory: a statue too
        if not amb_window_bay(th):
            sx, sz = x, z
            for _ in range(3):
                if bp.get(sx, 19, sz) == AIR:
                    break
                sx, sz = sx + ox, sz + oz
            if bp.get(sx, 19, sz) == AIR and k % 2 == 1:
                statue(bp, sx, 19, sz, fc)
    # velarium masts on the attic, every other bay: a pole, a gold finial, a banner
    done = set()
    for ix, iz in np.argwhere((M.U >= 45.0) & (M.U < 46.0)).tolist():
        x, z = ix + GX0, iz + GZ0
        k, w, L = bay_coords(M.TH[ix, iz])
        if abs(abs(w) - L / 2) > 0.6 or k in done:
            continue
        done.add(k)
        for y in range(WALL_TOP + 1, WALL_TOP + 7):
            bp.set(x, y, z, PBBW)
        bp.set(x, WALL_TOP + 7, z, "gold_block")
        bp.set(x, WALL_TOP + 8, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        fc = outward(x, z)
        ox, oz = DV[fc]
        bp.set(x + ox, WALL_TOP + 5, z + oz, BANNER.format("red" if k % 2 else "black", fc))
    # the crenellated parapet round the top of the wall
    for ix, iz in np.argwhere((M.U >= 46.0) & (M.U < 47.0)).tolist():
        x, z = ix + GX0, iz + GZ0
        if bp.get(x, WALL_TOP + 1, z) is None and (abs(x) > 14 or z > -50):
            bp.set(x, WALL_TOP + 1, z, PBB if (x + z) % 3 else GILD)
            if (x * 3 + z) % 4 == 0:
                bp.set(x, WALL_TOP + 2, z, "polished_blackstone_brick_slab[type=bottom,waterlogged=false]")


# ------------------------------------------------------------------ the stands' details
def stands(bp):
    """The broken seats over the hub (the drop), crimson fungus overgrowing the north-west stands, aisles of
    stairs, lamps on the walkways."""
    # the drop: a hole through tier 1 over the betting hall's hay
    for x in (13, 14):
        for z in (31, 32):
            t = seat_top(u_at(x, z))
            for y in range(18, t + 1):
                bp.set(x, y, z, AIR)
    for (x, z) in ((12, 30), (15, 30), (12, 33), (15, 33)):
        t = seat_top(u_at(x, z))
        bp.set(x, t + 1, z, "blackstone_slab[type=bottom,waterlogged=false]")
    # overgrowth: crimson nylium, roots and fungi on the north-west seats, a giant fungus in the ruin
    for ix, iz in np.argwhere((M.U >= 5) & (M.U < 41)).tolist():
        x, z = ix + GX0, iz + GZ0
        if x > -8 or z > 8:
            continue
        n = fbm(x * 0.9, z * 0.9, 10.0, 991) + 0.12 * (-x / 60.0) + 0.1 * (-z / 50.0)
        if n < 0.62:
            continue
        t = seat_top(M.U[ix, iz])
        if bp.get(x, t, z) in (None, AIR) or bp.get(x, t + 1, z) != AIR:
            continue
        bp.set(x, t, z, "crimson_nylium" if n < 0.72 else "nether_wart_block")
        h = hash01(x, z, 992)
        if h < 0.3:
            bp.set(x, t + 1, z, "crimson_roots")
        elif h < 0.36:
            bp.set(x, t + 1, z, "crimson_fungus")
        elif h < 0.38:
            bp.set(x, t + 1, z, "shroomlight")
    giant_fungus(bp, -38, seat_top(u_at(-38, -30)) + 1, -30, 13, 6, seed=993)
    # lamps on the walkways (praecinctiones)
    for k in range(24):
        a = 2 * math.pi * (k + 0.25) / 24
        for (u, y) in ((18.2, 22), (32.5, 30)):
            x, z = round((A0 + u) * math.cos(a)), round((B0 + u) * math.sin(a))
            if -14 <= x <= 14 and z < 0:
                continue
            if bp.get(x, y, z) == AIR and bp.get(x, y - 1, z) not in (None, AIR):
                bp.set(x, y, z, LANT) if k % 2 else brazier(bp, x, y, z)


# ------------------------------------------------------------------ the crowd's stands: fixtures and furniture
SOUL_LANT = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_HANG = "soul_lantern[hanging=true,waterlogged=false]"
SHROOM = "shroomlight"
FIRE = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
SOUL_FIRE = "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
BRASS_SLAB_B = "brasshaven:brass_plating_slab[type=bottom,waterlogged=false]"
# radial aisles (theta, degrees; 0 east, 90 south) where the lamps climb the seat rows: by hand, kept off the
# royal box (north), the champion's box (south), the vendors' recesses and the giant fungus
AISLES = (-172, -141, -52, -27, -6, 14, 37, 63, 108, 126, 147, 166)
STALLS = ((24.0, "red"), (49.0, "black"), (118.0, "red"), (137.0, "black"), (-38.0, "red"), (-62.0, "black"),
          (176.0, "red"))
SEAT_ROWS = [(5 + 2 * i, 1) for i in range(6)] + [(19.5 + 2 * i, 2) for i in range(6)] + \
            [(33.5 + 2 * i, 3) for i in range(4)]       # (row start u, tier)


def ring_xz(u, th):
    a = math.radians(th)
    return round((A0 + u) * math.cos(a)), round((B0 + u) * math.sin(a))


def brass_brazier(bp, x, y, z, soul=False, tall=False):
    """A brass brazier: a dark iron stem (tall ones), a brass bowl with a rim of brass slabs, a fire in it."""
    if tall:
        bp.set(x, y, z, CHIS)
        bp.set(x, y + 1, z, IRON_WALL)
        y += 2
    bp.set(x, y, z, BRASS)
    bp.set(x, y + 1, z, SOUL_FIRE if soul else FIRE)


def arc_cells(th0, hw, u0, u1):
    """The ring's columns within ``hw`` blocks of arc of the radial line at theta ``th0``, u0 <= u < u1."""
    out = []
    cells = np.argwhere((M.U >= u0) & (M.U < u1))
    for ix, iz in cells.tolist():
        x, z = ix + GX0, iz + GZ0
        d = (float(M.TH[ix, iz]) - th0 + 180.0) % 360.0 - 180.0
        if abs(math.radians(d)) * math.hypot(x, z) <= hw:
            out.append((x, z, float(M.U[ix, iz])))
    return out


def vendor_stall(bp, th0, colour):
    """A vendor's recess cut into the first rows of tier 2 off the lower walkway (floor y 21): a counter of barrels
    and crimson slabs under a striped awning, a lantern on the counter and one under the awning, a lit smoker and
    stacked barrels at the back, banners on the awning."""
    cells = arc_cells(th0, 2.6, 19.5, 23.5)
    if not cells:
        return
    other = "black" if colour == "red" else "red"
    for (x, z, u) in cells:
        for y in range(22, 29):
            bp.set(x, y, z, AIR)
        bp.set(x, 21, z, "crimson_planks" if (x + z) % 3 else "nether_wart_block")
        bp.set(x, 20, z, PBB)
    front = sorted([c for c in cells if c[2] < 20.6], key=lambda c: math.atan2(c[1], c[0]))
    back = sorted([c for c in cells if c[2] >= 22.4], key=lambda c: math.atan2(c[1], c[0]))
    fc = OPP[outward(*front[len(front) // 2][:2])] if front else "north"
    for i, (x, z, u) in enumerate(front):
        if i == 0:
            continue                                    # the vendor's gap at one end
        bp.set(x, 22, z, "barrel[facing=up,open=false]" if i % 3 == 1 else
               "crimson_slab[type=top,waterlogged=false]")
    if len(front) > 2:
        x, z, _ = front[len(front) // 2]
        if "slab" in (bp.get(x, 22, z) or ""):
            bp.set(x, 23, z, LANT)
        else:
            bp.set(x, 23, z, "crimson_slab[type=bottom,waterlogged=false]")
    for i, (x, z, u) in enumerate(back):
        if i == len(back) // 2:
            bp.set(x, 22, z, f"smoker[facing={fc},lit=true]")
        elif i % 2 == 0:
            bp.set(x, 22, z, "barrel[facing=up,open=false]")
            bp.set(x, 23, z, "barrel[facing=up,open=false]")
        else:
            bp.set(x, 22, z, HAY)
    # the awning: wool stripes over the counter row, fence posts at its two ends
    for (x, z, u) in cells:
        if u < 21.6:
            stripe = int(math.floor(math.degrees(math.atan2(z, x)) * 0.6)) % 2
            bp.set(x, 26, z, f"{colour if stripe else other}_wool")
    if len(front) >= 2:
        for (x, z, u) in (front[0], front[-1]):
            for y in (22, 23, 24, 25):
                bp.set(x, y, z, FENCE)
            bp.set(x, 27, z, f"{colour}_banner[rotation={'8' if fc == 'north' else '0'}]")
    mids = [c for c in cells if 20.6 <= c[2] < 21.6]
    if mids:
        x, z, _ = mids[len(mids) // 2]
        bp.chain(x, 25, z, 25)
        bp.set(x, 24, z, HANG)


def champions_box(bp):
    """The champion's box on the south axis, across the sand from the royal box: a gilded balcony levelled out of
    tier 2 (floor y 27) under a canopy on basalt posts, banners on its beam, three champion's chairs, benches for the
    retinue, brass braziers at its front corners, soul lanterns hung from the canopy; the back rows step up to the
    upper walkway."""
    P = 27
    cols = []
    for ix, iz in np.argwhere((M.U >= 19.5) & (M.U < 29.5)).tolist():
        x, z = ix + GX0, iz + GZ0
        if z > 0 and abs(x) <= 7:
            cols.append((x, z, float(M.U[ix, iz])))
    zf = {}
    for (x, z, u) in cols:
        zf[x] = min(zf.get(x, 999), z)
    for (x, z, u) in cols:
        side = abs(x) == 7
        for y in range(21, P):
            bp.set(x, y, z, PBB)
        bp.set(x, P, z, GILD if side or z == zf[x] else
               ("gold_block" if x == 0 and z % 3 == 0 else GBS if (x + z) % 4 == 0 else PB))
        for y in range(P + 1, P + 7):
            bp.set(x, y, z, AIR)
        if side:
            bp.set(x, P + 1, z, PBBW)
        elif z == zf[x]:
            bp.set(x, P + 1, z, PBBW if abs(x) != 4 else GBS)
    zb = max(z for (x, z, u) in cols if abs(x) <= 1)
    zfr = max(zf[x] for x in range(-6, 7))
    # the canopy: posts at the four corners, a gilded beam along the front, a blackstone roof
    zc0, zc1 = zfr + 1, zb - 1
    for (x, z) in ((-6, zc0), (6, zc0), (-6, zc1), (6, zc1)):
        for y in range(P + 1, P + 6):
            bp.set(x, y, z, BASALT)
    for x in range(-7, 8):
        for z in range(zc0 - 1, zc1 + 1):
            bp.set(x, P + 6, z, GILD if z == zc0 - 1 or abs(x) == 7 else PB)
            bp.set(x, P + 7, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
        bp.set(x, P + 5, zc0 - 1, GILD)
    for x in (-5, -3, -1, 1, 3, 5):
        banner(bp, x, P + 5, zc0 - 2, "north", "red" if x in (-5, -1, 3) else "yellow")
    for (x, z) in ((-4, zc0 + 2), (4, zc0 + 2), (0, zc1 - 3)):
        bp.chain(x, P + 5, z, P + 5)
        bp.set(x, P + 4, z, SOUL_HANG)
    # the champion's chairs, the retinue's benches, a carpet down the middle
    zt = zc1 - 1
    for x in (-2, 0, 2):
        bp.set(x, P + 1, zt, stair("blackstone_stairs", "south"))
        bp.set(x, P + 1, zt + 1, GBS if x else "gold_block")
        bp.set(x, P + 2, zt + 1, GILD if x else "gold_block")
    bp.set(0, P + 3, zt + 1, "piglin_head[rotation=0]")
    for z in range(zc0 + 1, zt):
        bp.set(0, P + 1, z, "red_carpet")
    for x in (-5, -4, 4, 5):
        for z in (zc0 + 3, zc0 + 5):
            bp.set(x, P + 1, z, stair(NBS, "south"))
            bp.set(x, P + 1, z - 1, "black_carpet") if bp.get(x, P + 1, z - 1) == AIR else None
    for x in (-6, 6):
        brass_brazier(bp, x, P + 1, zc0 + 1)
    for x in (-3, 3):
        bp.set(x, P + 1, zt + 1, "barrel[facing=up,open=false]")
        bp.set(x, P + 2, zt + 1, LANT)


def seat_cell(u, th):
    """(x, top y, z) of the back (flat) cell of the seat row starting at ``u`` on the radial line ``th``, or None
    where the row is broken, built over or overgrown."""
    for du in (1.5, 1.2, 1.8):
        x, z = ring_xz(u + du, th)
        uu = u_at(x, z)
        if row_front(uu) or not (u + 1.0 <= uu < u + 2.0):
            continue
        t = seat_top(uu)
        b = bp_get(x, t, z)
        if b in (None, AIR) or "stairs" in b or "nylium" in b or "wart" in b or bp_get(x, t + 1, z) != AIR \
                or bp_get(x, t + 2, z) != AIR:
            continue
        return x, t, z
    return None


_BP = [None]


def bp_get(x, y, z):
    return _BP[0].get(x, y, z)


def stands_life(bp):
    """Make the cavea a place people sat in: vendors' recesses off the lower walkway, the champion's box, reserved
    seats with carpets by the boxes, crowd banners on the back wall, and the lamps of the aisles: on every other row
    of each aisle a lantern on the step (soul lanterns on the top tier, brass braziers on the walkway ends), and
    shroomlights grown into the seats beside them."""
    _BP[0] = bp
    for th, col in STALLS:
        vendor_stall(bp, th, col)
    champions_box(bp)
    # the aisles
    for j, th in enumerate(AISLES):
        for i, (u, tier) in enumerate(SEAT_ROWS):
            if (i + j) % 2:
                continue
            c = seat_cell(u, th)
            if c is None:
                continue
            x, t, z = c
            if tier == 3 and i % 4 == 0:
                bp.set(x, t + 1, z, SOUL_LANT)
            else:
                bp.set(x, t + 1, z, LANT)
            # a shroomlight grown into the next seat along the row (both sides of the aisle in turn)
            for dth in ((2.2, -2.2) if i % 4 else (-2.2, 2.2)):
                th2 = th + math.degrees(dth / max(1.0, math.hypot(x, z)))
                x2, z2 = ring_xz(u + 1.5, th2)
                if (x2, z2) == (x, z) or row_front(u_at(x2, z2)):
                    continue
                t2 = seat_top(u_at(x2, z2))
                b2 = bp.get(x2, t2, z2)
                if t2 == t and b2 not in (None, AIR) and "stairs" not in b2 and bp.get(x2, t2 + 1, z2) == AIR:
                    bp.set(x2, t2, z2, SHROOM)
                    break
        # brass braziers where the aisle meets the two walkways (at the back edge, out of the way)
        for (u, y) in ((19.0, 22), (33.1, 30)):
            x, z = ring_xz(u, th + 1.5)
            if bp.get(x, y, z) == AIR and bp.get(x, y + 1, z) == AIR and bp.get(x, y - 1, z) not in (None, AIR) \
                    and "stairs" not in (bp.get(x, y - 1, z) or ""):
                brass_brazier(bp, x, y, z, soul=bool(j % 3 == 2))
    # reserved seats: red carpet on the flat cells of the rows flanking the royal box and the champion's box
    for ix, iz in np.argwhere((M.U >= 5) & (M.U < 17)).tolist():
        x, z = ix + GX0, iz + GZ0
        if not (15 <= abs(x) <= 22 and z < 0) and not (abs(x) <= 6 and z > 0):
            continue
        u = float(M.U[ix, iz])
        t = seat_top(u)
        if row_front(u) or bp.get(x, t + 1, z) != AIR or bp.get(x, t, z) in (None, AIR) or \
                "stairs" in bp.get(x, t, z) or bp.get(x, t, z) == "minecraft:" + SHROOM:
            continue
        bp.set(x, t + 1, z, "red_carpet" if z < 0 else "black_carpet")
    # crowd banners on the inner face of the outer wall over the portico walk, and on the walkway risers
    for k in range(40):
        th = -180 + 9 * k + 4.5
        if -118 <= th <= -62:
            continue
        for (u, y, col) in ((43.6, 40, "red" if k % 3 else "black"), (19.3, 22, "black" if k % 2 else "red")):
            x, z = ring_xz(u, th)
            o = outward(x, z)
            ox, oz = DV[o]
            inw = OPP[o]
            # walk outward from the open cell to the first solid one: the banner hangs on its face
            for _ in range(3):
                if bp.get(x + ox, y, z + oz) not in (None, AIR):
                    break
                x, z = x + ox, z + oz
            wall = bp.get(x + ox, y, z + oz)
            if bp.get(x, y, z) == AIR and wall not in (None, AIR) and _opaque(wall) and (u > 40 or k % 2 == 0):
                banner(bp, x, y, z, inw, col)


def light_arena(bp):
    """The sand floor: brass braziers on plinths round the foot of the podium (a ring of fires the champion fights
    in), shroomlights set in the sand between the gilded ring and the lift trapdoors."""
    for k in range(18):
        th = 10 + 20 * k
        x, z = round(A0 * 0.84 * math.cos(math.radians(th))), round(B0 * 0.84 * math.sin(math.radians(th)))
        if abs(x) <= 2 and z > 0:
            continue                                    # keep the gate of life clear
        if bp.get(x, G, z) == AIR and bp.get(x, G - 1, z) not in (None, AIR):
            brass_brazier(bp, x, G, z, tall=False)
    for (x, z) in ((-7, -5), (7, -5), (-7, 5), (7, 5), (-17, -5), (17, -5), (-17, 5), (17, 5), (-5, 13), (5, 13),
                   (-5, -13), (5, -13), (0, -4), (0, 4), (-4, 0), (4, 0)):
        if bp.get(x, G, z) == AIR and "trapdoor" not in (bp.get(x, G - 1, z) or ""):
            bp.set(x, G - 1, z, SHROOM)


# ------------------------------------------------------------------ outside: apron, moat, bridge, approach, camp
OPEN = []


def outside_ground(bp):
    """The apron between the facade and the moat (paved), the moat (lava two deep between quays), the forest floor
    beyond it with crimson nylium, roots and fungi."""
    U = M.U
    for ix, iz in np.argwhere((U >= U_WALL1) & (U < 84)).tolist():
        x, z = ix + GX0, iz + GZ0
        u = U[ix, iz]
        if solid(x, 6, z):
            continue
        if u < U_MOAT0 - 1:
            if bp.get(x, 5, z) is None:
                bp.set(x, 5, z, PATH.pick(x, 5, z))
            for y in range(6, 13):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
        elif u < U_MOAT0:
            bp.set(x, 5, z, CHIS)
            bp.set(x, 6, z, PBBW)
            for y in (3, 4):
                bp.set(x, y, z, PBB)
        elif u < U_MOAT1:
            bp.set(x, 1, z, "blackstone")
            bp.set(x, 2, z, LAVA)
            bp.set(x, 3, z, LAVA)
            for y in range(4, 11):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
        elif u < U_MOAT1 + 1:
            bp.set(x, 5, z, CHIS)
            for y in (3, 4):
                bp.set(x, y, z, PBB)
            if hash01(x, z, 1001) < 0.85:
                bp.set(x, 6, z, PBBW)
        else:
            e = u - U_MOAT1
            if e > 9 + 6 * vnoise(x, z, 9.0, 1002):
                continue
            if bp.get(x, 5, z) is None:
                spec = GROUND.pick(x, 5, z)
                bp.set(x, 5, z, spec)
                if spec == "crimson_nylium" and bp.get(x, 6, z) is None:
                    h = hash01(x, z, 1003)
                    if h < 0.2:
                        bp.set(x, 6, z, "crimson_roots")
                    elif h < 0.24:
                        bp.set(x, 6, z, "crimson_fungus")
                    elif h < 0.32:
                        bp.set(x, 6, z, "nether_sprouts")
            for y in range(6, 8):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)


def chain_bridge(bp):
    """The chain bridge over the moat on the south axis: a crimson deck on iron beams hung from two catenaries of
    chain between pylons on the quays, gold-capped."""
    z0, z1 = 65, 78
    for z in range(z0, z1 + 1):
        for x in range(-2, 3):
            bp.set(x, 5, z, "crimson_planks" if x % 2 else "dark_oak_planks")
            bp.set(x, 4, z, IRON if z % 4 == 0 else AIR) if 67 <= z <= 76 else None
            for y in range(6, 10):
                if bp.get(x, y, z) in (None, PBBW):
                    bp.set(x, y, z, AIR)
        for x in (-3, 3):
            bp.set(x, 5, z, IRON)
            bp.set(x, 6, z, NBF if z % 3 else IRON_WALL)
    # the pylons
    for zp in (66, 77):
        for x in (-4, 4):
            for y in range(5, 19):
                bp.set(x, y, zp, BASALT if y % 6 else GILD)
            bp.set(x, 19, zp, "gold_block")
            bp.set(x, 20, zp, LAMP)
    # the catenaries and the hangers
    for x in (-4, 4):
        prev = None
        for z in range(66, 78):
            t = (z - 71.5) / 5.5
            y = round(7 + 11 * t * t)
            bp.set(x, y, z, CHAIN_Z)
            if prev is not None and abs(prev - y) > 1:
                for yy in range(min(prev, y) + 1, max(prev, y)):
                    bp.set(x, yy, z, CHAIN)
            prev = y
            if z % 2 == 0 and 67 <= z <= 76:
                for yy in range(7, y):
                    sx = x - (1 if x > 0 else -1)
                    bp.set(sx, yy, z, CHAIN) if yy > 6 else None
    # the broken chain bridge on the north axis: a pylon, a deck end hanging down into the lava
    for z in range(-78, -67):
        for x in range(-2, 3):
            if z < -73:
                bp.set(x, 5, z, "crimson_planks")
            else:
                bp.set(x, 5 - (z + 73), z, "crimson_planks") if hash01(x, z, 1004) < 0.7 else None
    for x in (-4, 4):
        for y in range(5, 17):
            bp.set(x, y, -79, BASALT if y % 6 else GILD)
        for z in range(-78, -72):
            bp.set(x, 16 - (z + 78) * 2, z, CHAIN)


def approach(bp):
    """The road from the camp: east along z 85..88 between giant crimson fungi, north under the broken triumphal
    arch to the bridge."""
    def path(x0, x1, z0, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, 5, z, PATH.pick(x, 5, z))
                for y in range(G, G + 5):
                    bp.set(x, y, z, AIR)
    path(-56, 2, 85, 88)
    path(-2, 2, 79, 84)
    for x in range(-54, 0, 6):
        for z in (84, 89):
            post(bp, x, z)
    # giant crimson fungi along the road (they hide the colosseum until the arch)
    for i, (x, z, h, r) in enumerate(((-48, 79, 15, 7), (-34, 94, 13, 6), (-22, 79, 17, 8), (-10, 95, 14, 6),
                                      (12, 92, 16, 7), (14, 78, 12, 5), (-60, 72, 14, 6), (32, 84, 15, 7),
                                      (-74, 50, 16, 7), (70, 64, 15, 7), (78, -40, 16, 7), (-80, -20, 14, 6),
                                      (40, -78, 15, 7), (-46, -76, 13, 6))):
        if bp.get(x, 5, z) is None:
            bp.set(x, 5, z, "crimson_nylium")
        giant_fungus(bp, x, 6, z, h, r, seed=1010 + i)
    # the broken triumphal arch over the road (z 81..83): two piers, a round arch, a gilded frieze, a half-fallen
    # attic; it frames the champions' gate
    for x in range(-11, 12):
        for y in range(6, 27):
            for z in (81, 82, 83):
                r = math.hypot(x, max(0, y - 14))
                if abs(x) <= 4 and r <= 4.6:
                    continue
                if abs(x) > 9:
                    continue
                if y > 22 and x > 3 + (y - 22) * 0:
                    if hash01(x, y, 1020) < 0.7:
                        continue
                if y in (19, 20) and z == 83:
                    spec = GILD
                elif y == 6:
                    spec = CHIS
                else:
                    spec = FACADE1.pick(x, y, z) if y < 19 else FACADE3.pick(x, y, z)
                bp.set(x, y, z, spec)
    for (x, z) in ((-7, 84), (7, 84)):
        statue(bp, x, 6, z + 1, "south")
    for (x, y, z) in ((6, 6, 80), (7, 6, 79), (8, 7, 80), (5, 6, 78)):
        bp.set(x, y, z, CPBB if (x + z) % 2 else FACADE3.pick(x, y, z))
    OPEN.append((-9, 9, G, 20, 80, 84))


def post(bp, x, z):
    bp.set(x, 5, z, CHIS)
    bp.set(x, 6, z, PBBW)
    bp.set(x, 7, z, PBBW)
    bp.set(x, 8, z, GBS)
    bp.set(x, 9, z, LANT)


def camp(bp):
    """The exiled gladiators' camp: tents of red and black wool, a fire, a sparring ring, broken weapons, the
    waystone, the camp chest."""
    cx, cz = -66, 86
    for x in range(cx - 12, cx + 13):
        for z in range(cz - 11, cz + 12):
            if math.hypot((x - cx) / 12.0, (z - cz) / 11.0) <= 1.0:
                bp.set(x, 5, z, "crimson_nylium" if hash01(x, z, 1031) < 0.4 else
                       ("netherrack" if hash01(x, z, 1032) < 0.6 else "coarse_dirt"))
                for y in range(G, G + 6):
                    bp.set(x, y, z, AIR)
    OPEN.append((cx - 12, cx + 12, G, G + 5, cz - 11, cz + 11))
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.set(cx + dx, 6, cz + dz, "blackstone_slab[type=bottom,waterlogged=false]")
    bp.set(cx, 6, cz, CAMP)
    for (tx, tz, col) in ((-73, 79, "red"), (-60, 92, "black"), (-74, 91, "red")):
        for dz in range(0, 5):
            for dx in (-2, -1, 0, 1, 2):
                y = 6 + (2 - abs(dx))
                bp.set(tx + dx, y, tz + dz, f"{col}_wool")
            bp.set(tx, 9, tz + dz, "crimson_fence")
        for dz in (0, 4):
            for y in (6, 7, 8):
                bp.set(tx, y, tz + dz, "crimson_fence")
        for dz in range(1, 4):
            bp.set(tx, 6, tz + dz, AIR)
            bp.set(tx, 7, tz + dz, AIR)
            bp.set(tx - 1, 6, tz + dz, "red_carpet")
            bp.set(tx + 1, 6, tz + dz, "black_carpet")
        bp.set(tx, 6, tz + 4, AIR)
        bp.set(tx, 7, tz + 4, AIR)
    chest(bp, -59, 6, 91, "south", "crc_camp")
    bp.set(-62, 6, 82, MOD["waystone"])
    # the sparring ring: fence posts and chains, a training dummy
    for k in range(10):
        a = 2 * math.pi * k / 10
        bp.set(round(-66 + 5 * math.cos(a)) + 9, 6, round(86 + 4 * math.sin(a)) - 6, NBF)
    bp.set(-57, 6, 80, "crimson_fence")
    bp.set(-57, 7, 80, HAY)
    bp.set(-57, 8, 80, "carved_pumpkin[facing=west]")
    # broken weapons, a cart of loot, a grindstone, the bones of a hoglin
    bp.set(-70, 6, 84, "grindstone[face=floor,facing=east]")
    bp.set(-70, 6, 85, "smithing_table")
    bp.set(-62, 6, 89, "barrel[facing=up,open=false]")
    bp.set(-63, 6, 89, "barrel[facing=up,open=false]")
    for (x, z) in ((-75, 85), (-75, 86), (-75, 87)):
        bp.set(x, 6, z, "bone_block[axis=z]")
    bp.set(-74, 6, 86, "piglin_head[rotation=4]")
    for (x, z) in ((-72, 84), (-58, 86)):
        post(bp, x, z)
    bp.set(-64, 6, 81, "lectern[facing=north,has_book=false,powered=false]")


def carve_open(bp):
    for (x0, x1, y0, y1, z0, z1) in OPEN:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, AIR)


# ------------------------------------------------------------------ lighting: no dark floor inside
EMIT = {"lantern": 15, "soul_lantern": 10, "campfire": 15, "soul_campfire": 10, "shroomlight": 15, "glowstone": 15,
        "ember_lamp": 15, "edison_lamp": 15, "lava": 15, "fire": 15, "soul_fire": 10, "magma_block": 3,
        "jack_o_lantern": 15, "furnace": 13, "blast_furnace": 13}
NO_LAMP = ("chest", "barrel", "spawner", "waystone", "boss_seal", "sealed_bars", "trapdoor", "door", "gold_block",
           "lamp", "lava", "magma", "anvil", "table", "furnace", "cauldron", "composter", "lectern", "hay")


def _emit(name, props):
    sh = name.split(":")[1]
    if sh == "candle":
        return 3 * int(props.get("candles", "1")) if props.get("lit") == "true" else 0
    if sh in ("furnace", "blast_furnace", "campfire", "soul_campfire") and props.get("lit") == "false":
        return 0
    return EMIT.get(sh, 0)


def _opaque(name):
    sh = name.split(":")[1]
    if sh in ("air", "cave_air") or sh.endswith(("_slab", "_stairs")):
        return False
    return is_solid(name)


def relight(bp, regions, lamp=LAMP, margin=15, max_lamps=400, cells=None, cover=1.0):
    """Flood the block light of every source; then, while a standable floor cell of ``regions`` (boxes of feet
    cells) is darker than 8, set a lamp flush into the floor under the darkest one (its neighbours if that floor is
    furniture) and flood again from it. ``cells`` (feet cells) replaces the boxes' cells as the floor to light;
    ``cover`` stops once that share of it is lit. ``lamp`` may be a function of the floor cell."""
    if cells is not None:
        regions = [(min(c[0] for c in cells), max(c[0] for c in cells), min(c[1] for c in cells),
                    max(c[1] for c in cells), min(c[2] for c in cells), max(c[2] for c in cells))]
    x0 = min(r[0] for r in regions) - margin
    x1 = max(r[1] for r in regions) + margin
    y0 = min(r[2] for r in regions) - margin
    y1 = max(r[3] for r in regions) + margin
    z0 = min(r[4] for r in regions) - margin
    z1 = max(r[5] for r in regions) + margin
    sh = (x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1)
    opq = np.zeros(sh, bool)
    known = np.zeros(sh, bool)
    L = np.zeros(sh, np.int8)
    for (x, y, z), (n, pr, d) in bp.blocks.items():
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
            i = (x - x0, y - y0, z - z0)
            known[i] = True
            e = _emit(n, pr)
            if e:
                L[i] = e
            elif _opaque(n):
                opq[i] = True
    for lvl in range(15, 1, -1):
        m = L == lvl
        if not m.any():
            continue
        for ax in range(3):
            for dd in (1, -1):
                sm = np.zeros_like(m)
                src = [slice(None)] * 3
                dst = [slice(None)] * 3
                if dd > 0:
                    src[ax], dst[ax] = slice(0, -1), slice(1, None)
                else:
                    src[ax], dst[ax] = slice(1, None), slice(0, -1)
                sm[tuple(dst)] = m[tuple(src)]
                upd = sm & ~opq & (L < lvl - 1)
                L[upd] = lvl - 1

    def flood(i, e):
        L[i] = max(L[i], e)
        frontier = [i]
        lvl = e
        while frontier and lvl > 1:
            lvl -= 1
            nxt = []
            for (a, b, c) in frontier:
                for (da, db, dc) in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    q = (a + da, b + db, c + dc)
                    if 0 <= q[0] < sh[0] and 0 <= q[1] < sh[1] and 0 <= q[2] < sh[2] and not opq[q] and L[q] < lvl:
                        L[q] = lvl
                        nxt.append(q)
            frontier = nxt

    targets = []
    for (rx0, rx1, ry0, ry1, rz0, rz1) in regions:
        for x in range(rx0, rx1 + 1):
            for z in range(rz0, rz1 + 1):
                for y in range(ry0, ry1 + 1):
                    if cells is not None and (x, y, z) not in cells:
                        continue
                    b0, b1, b2 = bp.get(x, y - 1, z), bp.get(x, y, z), bp.get(x, y + 1, z)
                    if b0 is None or b1 is None or b2 is None:
                        continue
                    if b1 != AIR and _opaque(b1) or b2 != AIR and _opaque(b2):
                        continue
                    if b0 == AIR or not (_opaque(b0) or b0.endswith(("_stairs", "_slab"))):
                        continue
                    targets.append((x, y, z))
    targets = sorted(set(targets))
    placed = 0
    skip = set()
    while placed < max_lamps:
        dark = [t for t in targets if t not in skip and L[t[0] - x0, t[1] - y0, t[2] - z0] < 8]
        if not dark or len(dark) <= (1.0 - cover) * len(targets):
            break
        dark.sort(key=lambda t: (L[t[0] - x0, t[1] - y0, t[2] - z0], hash01(t[0], t[2], t[1])))
        x, y, z = dark[0]
        done = False
        for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            fb = bp.get(x + dx, y - 1, z + dz)
            above = bp.get(x + dx, y, z + dz)
            if fb is None or not _opaque(fb) or any(k in fb for k in NO_LAMP) or above != AIR:
                continue
            bp.set(x + dx, y - 1, z + dz, lamp(x + dx, y - 1, z + dz) if callable(lamp) else lamp)
            i = (x + dx - x0, y - 1 - y0, z + dz - z0)
            opq[i] = False
            flood(i, 15)
            placed += 1
            done = True
            break
        if not done:
            skip.add((x, y, z))
    return placed


def light_interiors(bp):
    regions = [(x0, x1, y0, min(y1, y0 + 20), z0, z1) for (n, st, x0, x1, y0, y1, z0, z1) in ROOMS
               if n not in ("s_shaft",)]
    for r in regions:
        relight(bp, [r])
    # the ambulatory, in four arcs
    u0, u1, t0, t1, y0, y1 = AMB
    for (a, b) in ((-97, -60), (-60, -20), (-20, 15), (15, 46)):
        cells = np.argwhere((M.U >= u0) & (M.U < u1) & (M.TH >= a) & (M.TH <= b))
        xs = cells[:, 0] + GX0
        zs = cells[:, 1] + GZ0
        relight(bp, [(int(xs.min()), int(xs.max()), UF, UF, int(zs.min()), int(zs.max()))])
    # the royal stair, the box-to-podium stair, the grand stair, the lift hall's stairs
    relight(bp, [(-17, -15, G, UF, -47, -12)])
    relight(bp, [(47, 49, G, UF, 9, 33)])
    # the cavea: the podium walk, the seat rows, the walkways and the portico walk; where the aisle lamps leave a
    # dark patch a shroomlight grows into the seat (an ember lamp in the paving of the walks)
    cells = set()
    for ix, iz in np.argwhere((M.U >= 0) & (M.U < U_WALL0)).tolist():
        x, z = ix + GX0, iz + GZ0
        for y in range(PF, 38):
            b0, b1, b2 = bp.get(x, y - 1, z), bp.get(x, y, z), bp.get(x, y + 1, z)
            if b0 in (None, AIR) or b1 is None or b2 is None or _opaque(b1) or _opaque(b2):
                continue
            if y >= 36 and -13 <= x <= 13 and -56 <= z <= -24:
                continue                                # inside the royal box's roof (sealed)
            if _opaque(b0) or b0.endswith(("_stairs", "_slab")):
                cells.add((x, y, z))

    def stand_lamp(x, y, z):
        u = u_at(x, z)
        return SHROOM if 5 <= u < 41 and not (17 <= u < 19.5 or 31.5 <= u < 33.5) else LAMP
    relight(bp, None, lamp=stand_lamp, cells=cells, cover=0.93, max_lamps=160)


# ------------------------------------------------------------------ the whole site
def crimson_colosseum(bp):
    OPEN.clear()
    M.U, M.TH = ring_u()
    lab = build_masses()
    air, rid = build_air()
    write_masses(bp, lab, air, rid)
    outside_ground(bp)
    arena(bp)
    gate_of_life(bp)
    champions_gate(bp)
    towers_east(bp)
    gate_of_death(bp)
    betting_hall(bp)
    barracks(bp)
    barracks_stair(bp)
    hypogeum(bp)
    muster_hall(bp)
    hoglin_pens(bp)
    lift_hall(bp)
    forge(bp)
    grand_stair(bp)
    ambulatory(bp)
    royal_box(bp)
    purse_vault(bp)
    royal_stair(bp)
    champion_tower(bp)
    facade_details(bp)
    stands(bp)
    stands_life(bp)
    light_arena(bp)
    chain_bridge(bp)
    approach(bp)
    camp(bp)
    light_interiors(bp)
    carve_open(bp)
    ys = [p[1] for p in bp.blocks]
    assert min(ys) == HF - 1, min(ys)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("betting_hall", (8, G, 44), (-4, G + 5, 32)),
    ("barracks", (-26, G, 36), (-40, G + 3, 22)),
    ("cage_gallery", (-20, HF, 0), (20, HF + 3, 0)),
    ("hoglin_pens", (30, HF, 0), (46, HF + 2, -8)),
    ("beast_lifts", (61, G, 11), (53, G + 2, -6)),
    ("armoury_forge", (42, G, 25), (32, G + 3, 36)),
    ("ambulatory", (61, UF, -2), (59, UF + 2, -13)),
    ("royal_box", (3, UF, -26), (0, UF + 3, -44)),
]

register(StructureDef(
    "crimson_colosseum", "nether", ["crimson_forest", "nether_wastes"],
    [Piece("colosseum", crimson_colosseum, views=VIEWS)],
    spacing=36, separation=12, adaptation="none", height=("absolute", 21), processors="none", max_distance=128,
    ground=G - 1, foundation=False,
    spawns=[(MOB_PIGLIN, 6, 1, 2), (MOB_BRUTE, 4, 1, 1), (MOB_HOGLIN, 3, 1, 2), (MOB_ZPIG, 4, 1, 2),
            (MOB_GUARD, 2, 1, 1)],
    title_fr="Le Colisée cramoisi", title_en="The Crimson Colosseum"))
