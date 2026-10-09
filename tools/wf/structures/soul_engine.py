"""The Soul Engine (Le Moteur des âmes): a monstrous machine-ossuary on the floor of a Nether soul sand valley, a
cathedral-sized engine block of blackstone, soul soil and tarnished brass, fed by bone conveyors, with six colossal
pistons frozen at different heights on its crankcase, ribbed chimneys venting blue flame, soul-fire furnace mouths,
an ossuary of bone vaults under it and warped-fungus overgrowth eating its outer walls. Colossal tier
(tools/BUILDING.md §1, §12 concept 24, §10 legacy-dungeon template, §15; tools/STYLE_STEAMPUNK.md).

Silhouette (one noun phrase, §15.1): a black engine block like a windowless cathedral, crowned by a row of six giant
brass pistons at different heights and four ribbed chimneys burning blue, two bone conveyors climbing to its flanks.

Placement: the Nether has no sky, so the engine stands on the valley floor at a fixed height (cavern FIT, like
titan_forge / chained_bastion): blueprint y = world y - 30 (template bottom = the charnel pit floor, y -15 = world
15), the soul-soil apron at y 5 (world 35, feet 6), the highest piston crown at y 88 (world 118, under the bedrock
roof). Every open interior volume is explicit air (the rooms of the mass grid, then ``carve_open`` for the approach,
the forecourt and the camp), so the natural netherrack cannot fill them. x east, z south.

The engine block (x -52..52, z -42..42, top y 40) on a battered plinth, buttresses every 13 blocks, brass bands; the
crankcase on top (x -42..42, z -40..24, top y 60) carries the six pistons in a row over the crank trench (z -32);
the piston-sleeve tower (the shaft) stands at its north-west corner.

The route (main path ~500 path blocks):
  * the lost pilgrims' camp (waystone) south-west on the soul sand, the bone road east and north through the
    ribcage arch (it frames the gate: the reveal) to the forecourt and the bone gate (a wicket in its iron leaves);
  * the gate tunnel (compression) into the pressure hall (hub, waystone, 37 x 35 x 25): the pressure vessel, its
    pipes, the balcony of the governor's room above;
  * north: the bone hopper hall (bones pouring from the conveyors into hoppers, the bone grinder), east through
    the soul-soil bunker into the soul furnace hall (three furnaces burning soul fire, their mouths open on the east
    facade, the boiler drum over them); the grand stair up its west wall to the stokers' balcony (feet 20);
  * the stokers' mess, the governor's control room (the flyball governor, the gauge wall, the balcony over the hub),
    the valve room, then up the piston shaft (a newel stair in a disused cylinder sleeve) to the site of grace
    (waystone) on the crankcase, a narrow corridor (the mist), and the boss arena on the crankshaft deck: 39 x 39
    under the crankcase roof, the crank trench and its six connecting rods on the north side, the flywheel bay east.
  * behind sealed bars in the arena's west wall, the soul reliquary (treasury).
Shortcuts (§10.4): the piston lift (a ladder shaft from the site of grace down to the ossuary stair hall, its iron
door opens from the lift side only); the bone chute (a 16-block drop from the reliquary onto hay in the piston
gallery, back to the hub); the one-way furnace door (an iron door from the soul furnace into the pressure hall, its
lever only on the furnace side).
Optional: the piston gallery (spare pistons on cradles, the gantry, the catwalk), the ossuary vaults under the
engine (bone nave, the charnel pit with its bone throne, the builders' crypt and its stair back up into the piston
gallery: a loop).
Loot gradient (§15.6): camp, hall 1; hopper, bunker, mess 1-2; furnace, gallery, ossuary 2; governor, crypt 2;
charnel pit 2-3; reliquary 3+.
"""
import math

import numpy as np

from ..arch import Palette, stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, COPPER, GAUGE, GEAR, IRON, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_STAIRS,
                       PIPES, SMOKE, SMOKE_STAIRS, TABLE, TREAD, VERD, W, fbm, hash01, hash3, vnoise)
from ..parts import LOOT, MOD
from .caldera_ringwall import newel_laps
from .nether import CHIS, CPBB, GBS, GILD, PB, PBB, PBBS, PBBW, brazier, chandelier, giant_fungus

# the champion of the crankshaft deck: the Soul Stoker (entity/boss/SoulStoker.java, tools/BOSSES.md)
BOSS = "brasshaven:soul_stoker"
MOB_WSKEL = "minecraft:wither_skeleton"
MOB_SKEL = "minecraft:skeleton"
MOB_GRAVE = W + "grave_knight"
MOB_CRAWLER = W + "crypt_crawler"
MOB_KNIGHT = W + "skeleton_knight"
MOB_HOUND = W + "cinder_hound"
MOB_IMP = W + "ember_imp"
MOB_GUARD = W + "basalt_guard"
MOB_WISP = W + "lantern_wisp"

# ------------------------------------------------------------------ levels
G = 6              # feet on the ground floor (floor y 5, the soul-soil apron)
L2 = 20            # feet on the upper floor of the engine block
CW = 26            # feet on the piston gallery catwalk
AF = 42            # feet in the crankcase (site of grace, arena, reliquary)
OF = -10           # feet in the ossuary
PF = -14           # feet in the charnel pit
BX0, BX1, BZ0, BZ1, BTOP = -52, 52, -42, 42, 40       # the engine block
UX0, UX1, UZ0, UZ1, UTOP = -42, 42, -40, 24, 60       # the crankcase
PZ = -32           # the pistons' row (and the crankshaft)
PISTONS = ((-30, 79), (-18, 85), (-6, 75), (6, 88), (18, 82), (30, 76))   # (x, crown top)
RIDGE = 64         # top of the cylinder block (the ridge along the pistons' row)
AC = (0, -7)       # arena centre
SHAFT_C = (-45, -35)

AIR = "minecraft:air"
BONE = "bone_block[axis=y]"
BONE_X = "bone_block[axis=x]"
BONE_Z = "bone_block[axis=z]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
HANG_SOUL = "soul_lantern[hanging=true,waterlogged=false]"
SOUL_LANT = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_FIRE = "soul_fire"
SOUL_CAMP = "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
GLASS = "light_blue_stained_glass"
HAY = "hay_block[axis=y]"
LADDER = "ladder[facing={},waterlogged=false]"
SKULL = "skeleton_skull[rotation={}]"
WSKULL = "skeleton_wall_skull[facing={}]"
WITHER = "wither_skeleton_skull[rotation={}]"
CANDLE = "candle[candles={},lit=true,waterlogged=false]"

FLOOR_HALL = Palette({PB: 4, PBB: 3, CHIS: 0.4}, seed=701, scale=1.8)
WALL_DARK = Palette({PBB: 6, CPBB: 1.5, "blackstone": 1.5, PB: 1}, seed=702, scale=2.4)
BONEP = Palette({BONE: 5, PBB: 2, CPBB: 1}, seed=703, scale=2.0)
OSS_FLOOR = Palette({PB: 3, "smooth_basalt": 2, BONE: 1, CPBB: 1}, seed=704, scale=1.6)
SOOT = Palette({SMOKE: 5, PBB: 2, "blackstone": 1}, seed=705, scale=2.2)
DECK = Palette({TREAD: 5, IRON: 2}, seed=706, scale=1.6)
IRONW = Palette({IRON: 5, PBB: 2, "polished_basalt[axis=y]": 1}, seed=707, scale=2.0)
GROUND = Palette({"soul_soil": 4, "soul_sand": 3, "blackstone": 0.6, "basalt[axis=y]": 0.4}, seed=708, scale=4.0)
PATH = Palette({PBB: 5, PB: 2, CHIS: 0.5}, seed=709, scale=1.4)
FACADE = Palette({PBB: 6, "blackstone": 1.5, CPBB: 1.5, PB: 1}, seed=710, scale=2.6)
BASE = Palette({"blackstone": 4, CPBB: 2, PBB: 2, "basalt[axis=y]": 1, "soul_soil": 1}, seed=711, scale=3.0)
TARN = Palette({BRASS: 4, VERD: 2, COPPER: 1}, seed=712, scale=2.0)          # tarnished brass
CRANK = Palette({IRON: 5, PBB: 2, PB: 1}, seed=713, scale=2.5)
ROOF = Palette({PB: 3, PBB: 2, "soul_soil": 1}, seed=714, scale=2.5)
SLEEVE = Palette({COPPER: 3, VERD: 2, BRASS: 1}, seed=715, scale=2.0)

STYLES = {   # (floor, wall, ceiling)
    "hall": (FLOOR_HALL, WALL_DARK, IRONW),
    "gate": (PATH, WALL_DARK, WALL_DARK),
    "bone": (OSS_FLOOR, BONEP, Palette({BONE: 3, PBB: 1}, seed=716)),
    "soot": (Palette({PBB: 3, "soul_soil": 1, "blackstone": 2}, seed=717), SOOT, SOOT),
    "iron": (DECK, IRONW, IRONW),
    "wood": (Palette({"crimson_planks": 1}), Palette({MAHOGANY: 3, PBB: 1}, seed=718), IRONW),
    "gov": (Palette({"dark_oak_planks": 1}), Palette({MAHOGANY: 4, BRASS: 0.4}, seed=719), IRONW),
    "copper": (DECK, Palette({COPPER: 3, VERD: 2, IRON: 2}, seed=720), IRONW),
    "brass": (Palette({CHIS: 2, PBB: 3, GILD: 0.3}, seed=721), TARN, IRONW),
    "arena": (DECK, CRANK, IRONW),
    "relic": (Palette({GBS: 1, PBB: 2}, seed=722), Palette({BONE: 3, GBS: 1, PBB: 2}, seed=723), BONEP),
}

# ------------------------------------------------------------------ the rooms (air boxes of the mass grid)
ROOMS = [
    # ground floor (feet 6)
    ("gate", "gate", -2, 2, G, G + 4, 29, 42),
    ("hall", "hall", -18, 18, G, 30, -6, 28),
    ("hopper", "bone", -18, 18, G, 15, -39, -10),
    ("nw", "bone", -49, -24, G, 15, -39, -12),
    ("ne", "soot", 24, 49, G, 15, -39, -12),
    ("gallery", "iron", -49, -24, G, 32, -8, 39),
    ("furnace", "soot", 24, 49, G, 30, -8, 39),
    ("d_hall_hop", "gate", -2, 2, G, G + 4, -9, -7),
    ("d_hop_ne", "gate", 19, 23, G, G + 4, -26, -24),
    ("d_hop_nw", "gate", -23, -19, G, G + 4, -26, -24),
    ("d_ne_fur", "gate", 30, 34, G, G + 4, -11, -9),
    ("d_hall_pg", "gate", -23, -19, G, G + 6, 8, 12),
    ("d_oneway", "gate", 19, 22, G, G + 2, 2, 2),
    ("d_oneway2", "gate", 23, 23, G, G + 1, 2, 2),
    # upper floor (feet 20)
    ("gov", "gov", -18, 18, L2, 30, -39, -12),
    ("mess", "wood", 24, 49, L2, 28, -39, -12),
    ("valve", "copper", -49, -24, L2, 30, -39, -12),
    ("d_gov_hall", "gate", -2, 2, L2, L2 + 3, -11, -7),
    ("d_fur_mess", "gate", 24, 26, L2, L2 + 3, -11, -9),
    ("d_mess_gov", "gate", 19, 23, L2, L2 + 3, -20, -18),
    ("d_gov_valve", "gate", -23, -19, L2, L2 + 3, -20, -18),
    # the piston shaft, the site of grace, the lift
    ("shaft", "brass", -49, -41, L2, AF + 4, -39, -31),
    ("d_shaft_grace", "brass", -49, -47, AF, AF + 3, -30, -30),
    ("grace", "brass", -49, -39, AF, AF + 5, -29, -21),
    ("lift", "iron", -40, -38, G, AF + 3, -19, -17),
    ("d_lift_grace", "brass", -39, -39, AF, AF + 2, -20, -20),
    ("corr", "brass", -38, -20, AF, AF + 3, -24, -22),
    # the crankcase
    ("arena", "arena", -19, 19, AF, 58, -26, 12),
    ("trench", "arena", -35, 35, 34, 58, -37, -27),
    ("fly", "arena", 20, 25, AF, 58, -18, 4),
    ("reliq", "relic", -38, -24, AF, AF + 6, 0, 12),
    ("d_bars", "relic", -23, -20, AF, AF + 3, 5, 7),
    ("chute", "relic", -36, -35, 33, AF - 1, 8, 9),
    # the ossuary (feet -10)
    ("oss_stair", "bone", -48, -27, OF, 15, -39, -37),
    ("nave", "bone", -49, -16, OF, -1, -39, -12),
    ("d_nave_pit", "bone", -15, -13, OF, OF + 5, -27, -23),
    ("pit", "bone", -12, 18, PF, -1, -39, -12),
    ("d_nave_crypt", "bone", -40, -36, OF, OF + 4, -11, -7),
    ("crypt", "bone", -46, -30, OF, -3, -6, 20),
    ("crypt_stair", "bone", -48, -46, OF, 15, 2, 21),
]
ROOM_INDEX = {r[0]: i for i, r in enumerate(ROOMS)}

# ------------------------------------------------------------------ the numpy grid of the masses
GX0, GX1 = -60, 60
GY0, GY1 = -17, 70
GZ0, GZ1 = -50, 50
SHAPE = (GX1 - GX0 + 1, GY1 - GY0 + 1, GZ1 - GZ0 + 1)
BODY, PLINTH, BUTT, UPPER, SHAFT, ANNEX = 1, 2, 3, 4, 5, 6


class _M:
    full = air = lab = None


M = _M()


def _sl(x0, x1, y0, y1, z0, z1):
    return (slice(x0 - GX0, x1 - GX0 + 1), slice(y0 - GY0, y1 - GY0 + 1), slice(z0 - GZ0, z1 - GZ0 + 1))


def _shift_or(out, a, dx, dy, dz):
    n = a.shape
    out[max(dx, 0):n[0] + min(dx, 0), max(dy, 0):n[1] + min(dy, 0), max(dz, 0):n[2] + min(dz, 0)] |= \
        a[max(-dx, 0):n[0] + min(-dx, 0), max(-dy, 0):n[1] + min(-dy, 0), max(-dz, 0):n[2] + min(-dz, 0)]


def dilate(a, six=False):
    out = a.copy()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dy, dz) == (0, 0, 0) or (six and abs(dx) + abs(dy) + abs(dz) != 1):
                    continue
                _shift_or(out, a, dx, dy, dz)
    return out


def buttress_sites():
    """(x0, x1, z0, z1) footprints of the buttresses (3 wide, 4 deep) round the engine block."""
    out = []
    for x in (-45, -32, -19, 19, 32, 45):
        out.append((x - 1, x + 1, BZ1 + 1, BZ1 + 4))               # south
    for x in (-45, -32, -19, 10, 19, 32, 45):
        out.append((x - 1, x + 1, BZ0 - 4, BZ0 - 1))               # north (the conveyor intake at x -4)
    for z in (-32, -19, -6, 20, 33):
        out.append((BX0 - 4, BX0 - 1, z - 1, z + 1))               # west (the conveyor intake at z 4)
    for z in (-32, -19, -6, 7, 20, 33):
        out.append((BX1 + 1, BX1 + 4, z - 1, z + 1))               # east
    return out


def build_masses():
    lab = np.zeros(SHAPE, np.uint8)
    for y in range(0, 10):                                          # battered plinth
        d = int(round((10 - y) * 0.4))
        lab[_sl(BX0 - d, BX1 + d, y, y, BZ0 - d, BZ1 + d)] = PLINTH
    lab[_sl(BX0, BX1, 10, BTOP, BZ0, BZ1)] = BODY
    for (x0, x1, z0, z1) in buttress_sites():
        lab[_sl(x0, x1, 0, 30, z0, z1)] = BUTT
        # the upper step: 2 deep, to the cornice
        if z0 > BZ1:
            lab[_sl(x0, x1, 31, 36, z0, z0 + 1)] = BUTT
        elif z1 < BZ0:
            lab[_sl(x0, x1, 31, 36, z1 - 1, z1)] = BUTT
        elif x0 > BX1:
            lab[_sl(x0, x0 + 1, 31, 36, z0, z1)] = BUTT
        else:
            lab[_sl(x1 - 1, x1, 31, 36, z0, z1)] = BUTT
    lab[_sl(UX0 - 1, UX1 + 1, BTOP + 1, BTOP + 3, UZ0 - 1, UZ1 + 1)] = UPPER     # the crankcase's foot
    lab[_sl(UX0, UX1, BTOP + 1, UTOP, UZ0, UZ1)] = UPPER
    lab[_sl(-38, 38, UTOP + 1, RIDGE, UZ0 + 1, PZ + 7)] = UPPER                   # the cylinder block
    # the piston-sleeve tower (the shaft): a cylinder with a stepped cap
    cx, cz = SHAFT_C
    X = np.arange(GX0, GX1 + 1)[:, None]
    Z = np.arange(GZ0, GZ1 + 1)[None, :]
    d = np.hypot(X - cx, Z - cz)
    for y in range(30, 57):
        r = 7.5 if y <= 50 else 7.5 - (y - 50) * 1.1
        lab[:, y - GY0, :][d <= r] = SHAFT
    lab[_sl(-51, -37, BTOP, 49, -32, -19)] = ANNEX
    return lab


def build_air():
    air = np.zeros(SHAPE, bool)
    rid = np.full(SHAPE, -1, np.int16)
    for i, (name, style, x0, x1, y0, y1, z0, z1) in enumerate(ROOMS):
        sl = _sl(x0, x1, y0, y1, z0, z1)
        air[sl] = True
        rid[sl] = i
    return air, rid


def outer_spec(L, x, y, z, top):
    if L in (BODY, PLINTH, BUTT, ANNEX):
        if top:
            return CHIS if L == BUTT else ROOF.pick(x, y, z)
        n = overgrowth(x, y, z)
        if n > 0.62:
            return "shroomlight" if hash3(x, y, z, 731) < 0.05 else "warped_wart_block"
        if n > 0.56:
            return "warped_hyphae[axis=y]"
        if L == BUTT:
            if y < 10:
                return BASE.pick(x, y, z)
            return GILD if y in (30, 36) else (PB if hash3(x, y, z, 732) > 0.25 else CHIS)
        if y < 10:
            return BASE.pick(x, y, z)
        if y in (10, 11):
            return TARN.pick(x, y, z)
        if y in (18, 19):
            return IRON
        if y >= 37:
            if y == 37:
                return CHIS
            if y == 38:
                return GILD if (x + z) % 4 == 0 else PBB
            return PB
        u = x if abs(z) >= BZ1 - 1 else z
        if u % 13 == 0:
            return IRON
        if 22 <= y <= 33 and u % 13 in (5, 6, 7, 8) and L == BODY:
            return "soul_soil" if hash3(x, y, z, 733) > 0.3 else "soul_sand"      # the soot-dark panels
        return FACADE.pick(x, y, z)
    if L == UPPER:
        if top:
            return DECK.pick(x, y, z)
        if y <= BTOP + 3:
            return CHIS
        if y in (50, 51):
            return TARN.pick(x, y, z)
        if y >= UTOP - 1:
            return GILD if (x + z) % 5 == 0 else IRON
        u = x if abs(z - (UZ0 + UZ1) / 2) >= (UZ1 - UZ0) / 2 - 1 else z
        if u % 7 == 0:
            return PIPES
        return CRANK.pick(x, y, z)
    if L == SHAFT:
        if top:
            return COPPER
        return BRASS if y % 4 == 0 else SLEEVE.pick(x, y, z)
    return "blackstone"


def overgrowth(x, y, z):
    """Warped fungus eating the outer walls: stronger low down and on the west and north faces."""
    bonus = 0.18 if (x < BX0 + 6 or z < BZ0 + 6) else 0.0
    return fbm(x * 0.8 + z * 0.6, y * 1.3, 9.0, 734) + bonus - max(0, y - 6) / 90.0


def write_masses(bp, lab, air, rid):
    full = ((lab > 0) | dilate(air)) & ~air
    occ = full | air
    outside = ~occ
    outside[:, :-GY0, :] = False          # below y 0: the ground, not an outside face
    outer = full & dilate(dilate(outside, six=True), six=True)
    lining = full & dilate(air, six=True)
    M.full, M.air, M.lab = full, air, lab
    NX, NY, NZ = SHAPE
    styles = [r[1] for r in ROOMS]
    for ix, iy, iz in np.argwhere(outer | lining).tolist():
        x, y, z = ix + GX0, iy + GY0, iz + GZ0
        spec = None
        if lining[ix, iy, iz]:
            if iy + 1 < NY and air[ix, iy + 1, iz]:
                spec = STYLES[styles[rid[ix, iy + 1, iz]]][0].pick(x, y, z)
            elif iy > 0 and air[ix, iy - 1, iz]:
                spec = STYLES[styles[rid[ix, iy - 1, iz]]][2].pick(x, y, z)
            else:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    jx, jz = ix + dx, iz + dz
                    if 0 <= jx < NX and 0 <= jz < NZ and air[jx, iy, jz]:
                        spec = STYLES[styles[rid[jx, iy, jz]]][1].pick(x, y, z)
                        break
        if spec is None:
            L = int(lab[ix, iy, iz])
            if L == 0:
                L = BODY if y >= 0 else 0
            top = iy + 1 < NY and outside[ix, iy + 1, iz]
            spec = outer_spec(L, x, y, z, top)
        bp.set(x, y, z, spec)
    for ix, iy, iz in np.argwhere(air).tolist():
        bp.set(ix + GX0, iy + GY0, iz + GZ0, AIR)


def solid(x, y, z):
    ix, iy, iz = x - GX0, y - GY0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= iz < SHAPE[2]:
        return bool(M.full[ix, iy, iz])
    return False


# ------------------------------------------------------------------ small parts
def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def hang(bp, x, y, z, spec=HANG_SOUL, drop=1):
    """A lamp hanging under the ceiling: a chain of ``drop`` above y."""
    for k in range(1, drop + 1):
        bp.set(x, y + k, z, CHAIN)
    bp.set(x, y, z, spec)


def floor_box(bp, x0, x1, z0, z1, y, pal):
    """Pave the floor cells (y) under open air (y + 1) inside a box."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if bp.get(x, y + 1, z) == AIR and bp.get(x, y, z) not in (None, AIR):
                bp.set(x, y, z, pal(x, z) if callable(pal) else pal.pick(x, y, z))


def box(bp, x0, x1, y0, y1, z0, z1, spec):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, y, z, spec.pick(x, y, z) if isinstance(spec, Palette) else spec)


def rail(bp, x, y, z):
    bp.set(x, y, z, IRON_WALL)


def wall_skull(bp, x, y, z, facing):
    if bp.get(x, y, z) == AIR:
        bp.set(x, y, z, WSKULL.format(facing))


def deck_cells(bp, x0, x1, z0, z1, y, pal=DECK, clear=4):
    """A deck (catwalk, landing) at block y with air above it."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, pal.pick(x, y, z) if isinstance(pal, Palette) else pal)
            for yy in range(y + 1, y + 1 + clear):
                if bp.get(x, yy, z) in (None, AIR):
                    bp.set(x, yy, z, AIR)


def flight_z(bp, x0, x1, z_start, n, f0, dz, spec=PBBS, fill=PBB, low=None, wall=None):
    """n steps along z (dz = +-1), the first step at z_start with feet f0 + 1, each one block higher; solid fill
    under the treads down to ``low``; ``wall``: x of a parapet along the open side. Returns (z after the last step,
    feet of the last step)."""
    facing = "south" if dz > 0 else "north"
    f = f0
    z = z_start
    for i in range(n):
        f += 1
        if wall is not None:
            parapet(bp, wall, z, f, low)
        for x in range(x0, x1 + 1):
            bp.set(x, f - 1, z, stair(spec, facing))
            for y in range(low if low is not None else f - 2, f - 1):
                bp.set(x, y, z, fill)
            for y in range(f, f + 4):
                if bp.get(x, y, z) in (None, AIR):
                    bp.set(x, y, z, AIR)
        z += dz
    return z, f


def flight_x(bp, z0, z1, x_start, n, f0, dx, spec=PBBS, fill=PBB, low=None):
    facing = "east" if dx > 0 else "west"
    f = f0
    x = x_start
    for i in range(n):
        f += 1
        for z in range(z0, z1 + 1):
            bp.set(x, f - 1, z, stair(spec, facing))
            for y in range(low if low is not None else f - 2, f - 1):
                bp.set(x, y, z, fill)
            for y in range(f, f + 4):
                if bp.get(x, y, z) in (None, AIR):
                    bp.set(x, y, z, AIR)
        x += dx
    return x, f


def parapet(bp, x, z, f, low):
    for y in range(low if low is not None else f - 2, f):
        bp.set(x, y, z, PBB)
    bp.set(x, f, z, PBBW)


def landing(bp, x0, x1, z0, z1, f, pal=PATH, low=None, fill=PBB, wall=None):
    if wall is not None:
        for z in range(z0, z1 + 1):
            parapet(bp, wall, z, f, low)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, f - 1, z, pal.pick(x, f - 1, z) if isinstance(pal, Palette) else pal)
            for y in range(low if low is not None else f - 2, f - 1):
                bp.set(x, y, z, fill)


def vessel(bp, cx, cz, y0, y1, r, shell=IRON, band=BRASS, cap=True, core="blackstone"):
    """A vertical riveted tank: a solid cylinder with brass bands and a domed cap."""
    for y in range(y0, y1 + 1):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.3:
                    if d > r - 0.8:
                        bp.set(x, y, z, band if (y - y0) % 5 == 4 else shell)
                    else:
                        bp.set(x, y, z, core)
    if cap:
        rr, y = r, y1 + 1
        while rr > 0.5:
            rr -= 1.3
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    if math.hypot(x - cx, z - cz) <= rr + 0.3:
                        bp.set(x, y, z, COPPER if rr > 1 else GILD)
            y += 1
        return y
    return y1 + 1


def chest(bp, x, y, z, facing, table):
    bp.chest(x, y, z, facing, loot=LOOT + table)


# ------------------------------------------------------------------ the ground, the camp, the approach
OPEN = []          # (x0, x1, y0, y1, z0, z1) boxes kept open (air where nothing is set) by carve_open


def ground(bp):
    """The soul-soil apron round the engine: one layer at y 5 over the valley floor, bone fossils, basalt."""
    for x in range(-98, 66):
        for z in range(-100, 86):
            e = ((x + 16) / 82.0) ** 2 + ((z + 7) / 93.0) ** 2 + 0.25 * (vnoise(x, z, 11.0, 741) - 0.5)
            if e > 1.0:
                continue
            if BX0 <= x <= BX1 and BZ0 <= z <= BZ1:
                continue
            if bp.get(x, 5, z) is None:
                spec = GROUND.pick(x, 5, z)
                near_wall = BX0 - 9 <= x <= BX1 + 9 and BZ0 - 9 <= z <= BZ1 + 9
                if near_wall and overgrowth(x, 6, z) > 0.62:
                    spec = "warped_nylium"
                bp.set(x, 5, z, spec)
                if spec == "warped_nylium" and bp.get(x, 6, z) is None:
                    h = hash01(x, z, 742)
                    if h < 0.25:
                        bp.set(x, 6, z, "warped_roots")
                    elif h < 0.4:
                        bp.set(x, 6, z, "nether_sprouts")
                    elif h < 0.44:
                        bp.set(x, 6, z, "warped_fungus")
                    elif h < 0.5:
                        for k in range(1 + int(hash01(x, z, 743) * 4)):
                            bp.set(x, 6 + k, z, "twisting_vines_plant")
                        bp.set(x, 7 + int(hash01(x, z, 743) * 4), z, "twisting_vines[age=20]")
    # fossils: giant ribs arching out of the soul sand (the valley's own bones)
    for (cx, cz, ang, span, h) in ((60, -70, 0.3, 9, 13), (-80, -40, 1.2, 7, 10), (44, 66, 2.0, 8, 11),
                                   (-84, 34, 0.7, 6, 9)):
        ux, uz = math.cos(ang), math.sin(ang)
        for k in range(4):
            ox, oz = cx + round(-uz * k * 4), cz + round(ux * k * 4)
            for t in range(0, 41):
                a = math.pi * t / 40
                px = ox + round(ux * span * math.cos(a))
                pz = oz + round(uz * span * math.cos(a))
                py = 5 + round(h * math.sin(a) * (1 - 0.12 * k))
                bp.set(px, py, pz, BONE)
                if t % 10 == 0 and py > 6:
                    bp.set(px, py - 1, pz, BONE)


def path_cells(bp, x0, x1, z0, z1, pal=PATH):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, 5, z, pal.pick(x, 5, z))
    OPEN.append((x0, x1, G, G + 3, z0, z1))


def approach(bp):
    """The bone road from the camp: east along z 72, then north to the forecourt, bone posts with soul lanterns;
    the ribcage arch over the road frames the gate (the reveal)."""
    path_cells(bp, -60, 2, 70, 74)
    path_cells(bp, -2, 2, 44, 69)
    for x in range(-58, 2, 6):
        for z in (69, 75):
            post(bp, x, z)
    for z in range(48, 68, 6):
        for x in (-3, 3):
            post(bp, x, z)
    # the ribcage: five pairs of giant ribs leaning over the road, the spine above them
    for k, z in enumerate(range(52, 69, 4)):
        span = 9 - abs(k - 2)
        top = 18 - abs(k - 2) * 2
        for t in range(0, 31):
            a = math.pi * t / 30
            x = round(span * math.cos(a))
            y = 5 + round(top * math.sin(a))
            if abs(x) <= 2 and y < 10:
                continue
            bp.set(x, y, z, BONE)
            if t % 6 == 0:
                bp.set(x, y, z + 1, BONE)
    # the spine along the ribs' crowns
    for z in range(52, 70):
        k = min(4, max(0, (z - 52) // 4))
        bp.set(0, 5 + 18 - abs(k - 2) * 2 + 1, z, BONE_Z)


def post(bp, x, z):
    bp.set(x, 5, z, CHIS)
    bp.set(x, 6, z, BONE)
    bp.set(x, 7, z, BONE)
    bp.set(x, 8, z, PBBW)
    bp.set(x, 9, z, SOUL_LANT)


def camp(bp):
    """The lost pilgrims' camp at the start of the approach: two tents of hide, the soul fire, packs, the
    entrance waystone, the bones of those who did not leave."""
    x0, x1, z0, z1 = -74, -52, 60, 82
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if math.hypot((x + 63) / 11.5, (z - 71) / 11.5) <= 1.0:
                bp.set(x, 5, z, "soul_soil" if hash01(x, z, 751) < 0.6 else "coarse_dirt")
    OPEN.append((x0, x1, G, G + 4, z0, z1))
    # the fire ring
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.set(-63 + dx, 6, 71 + dz, "blackstone_slab[type=bottom,waterlogged=false]")
    bp.set(-63, 5, 71, "soul_soil")
    bp.set(-63, 6, 71, SOUL_CAMP)
    # two A-frame tents of brown wool on spruce poles
    for (tx, tz) in ((-70, 64), (-58, 78)):
        for dz in range(0, 5):
            for k, dx in enumerate((-2, -1, 0, 1, 2)):
                y = 6 + (2 - abs(dx))
                bp.set(tx + dx, y, tz + dz, "brown_wool" if abs(dx) < 2 or dz in (0, 4) else "brown_wool")
            bp.set(tx, 9, tz + dz, "spruce_fence")
        for dz in (0, 4):
            bp.set(tx, 6, tz + dz, "spruce_fence")
            bp.set(tx, 7, tz + dz, "spruce_fence")
            bp.set(tx, 8, tz + dz, "spruce_fence")
        for dz in range(1, 4):
            bp.set(tx, 6, tz + dz, AIR)
            bp.set(tx, 7, tz + dz, AIR)
            bp.set(tx - 1, 6, tz + dz, "brown_carpet")
            bp.set(tx + 1, 6, tz + dz, "red_carpet")
        bp.set(tx, 6, tz + 4, AIR)
        bp.set(tx, 7, tz + 4, AIR)
    bp.set(-70, 6, 68, "barrel[facing=up,open=false]")
    chest(bp, -58, 6, 77, "south", "se_camp")
    bp.set(-66, 6, 74, MOD["waystone"])
    # packs, a cart, a fallen pilgrim
    bp.set(-60, 6, 66, "barrel[facing=up,open=false]")
    bp.set(-59, 6, 66, "brown_wool")
    bp.set(-61, 6, 66, "spruce_trapdoor[facing=north,half=bottom,open=false,waterlogged=false]")
    for (x, z) in ((-67, 66), (-67, 67), (-67, 68)):
        bp.set(x, 6, z, "spruce_slab[type=bottom,waterlogged=false]")
    bp.set(-68, 6, 66, "dark_oak_fence")
    bp.set(-68, 6, 68, "dark_oak_fence")
    bp.set(-55, 6, 68, SKULL.format(6))
    bp.set(-55, 6, 67, BONE_X)
    bp.set(-54, 6, 69, "bone_block[axis=z]")
    for (x, z) in ((-72, 72), (-54, 74)):
        post(bp, x, z)
    bp.set(-62, 6, 64, "lectern[facing=south,has_book=false,powered=false]")


def forecourt(bp):
    """The paved terrace before the bone gate: bone obelisks, braziers of soul fire, steps."""
    for x in range(-16, 17):
        for z in range(43, 57):
            bp.set(x, 5, z, PATH.pick(x, 5, z) if (x + z) % 9 else CHIS)
    OPEN.append((-16, 16, G, G + 5, 43, 56))
    for (x, z) in ((-14, 47), (14, 47), (-14, 55), (14, 55)):
        for y in range(6, 13):
            bp.set(x, y, z, BONE if y < 12 else GILD)
        bp.set(x, 13, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        bp.set(x, 12, z, "soul_soil")
    for (x, z) in ((-8, 52), (8, 52)):
        brazier(bp, x, 6, z, soul=True, big=True)


def bone_gate(bp):
    """The colossal portal on the south face: two giant rib-bone jambs meeting in a pointed arch (12 wide, 22
    high), the iron leaves with bone studs and the wicket (3 x 4) in their middle, a wither-skull keystone."""
    zf = BZ1 + 1
    for t in range(0, 61):
        a = t / 60.0
        for side in (-1, 1):
            # each jamb: up to y 18, then curving in to the apex at y 29
            if a < 0.55:
                x, y = side * 9, 5 + round(a / 0.55 * 13)
            else:
                b = (a - 0.55) / 0.45
                x, y = side * round(9 * math.cos(b * math.pi / 2)), 18 + round(11 * math.sin(b * math.pi / 2))
            for dx in (0, side):
                for dz in (0, 1, 2):
                    bp.set(x + dx, y, zf + dz, BONE)
    # the leaves: iron with bone studs, inside the arch
    for x in range(-8, 9):
        for y in range(6, 29):
            inside = (abs(x) <= 8 and y <= 18) or (abs(x) <= round(8 * math.cos(math.asin(min(1.0, (y - 18) / 11.0)))))
            if not inside:
                continue
            if abs(x) <= 1 and y <= 9:
                bp.set(x, y, zf, AIR)                       # the wicket
                continue
            if x == 0:
                spec = BRASS
            elif (x + y) % 5 == 0:
                spec = BONE
            elif y in (10, 17, 24):
                spec = BRASS
            else:
                spec = IRON
            bp.set(x, y, zf, spec)
    for y in range(6, 10):
        for x in (-2, 2):
            bp.set(x, y, zf, BRASS)
    for x in range(-2, 3):
        bp.set(x, 10, zf, GILD)
    for x in range(-1, 2):
        bp.set(x, 5, zf, CHIS)
        bp.set(x, 5, zf + 1, CHIS)
    bp.set(0, 29, zf + 3, WITHER.format(8))
    bp.set(0, 28, zf + 3, BONE)
    bp.set(0, 27, zf + 3, BONE)
    # the gate tunnel: path, slits, lamps, a raised portcullis
    floor_box(bp, -2, 2, 29, 42, G - 1, PATH)
    for x in range(-2, 3):
        bp.set(x, G + 4, 40, "iron_bars")
    for z in (32, 37):
        hang(bp, 0, G + 3, z, HANG_SOUL)
    for z in (31, 35, 39):
        bp.set(-3, G + 1, z, "iron_bars")
        bp.set(3, G + 1, z, "iron_bars")


# ------------------------------------------------------------------ the pressure hall (hub)
def pressure_hall(bp):
    f = G
    cx, cz = 0, 10
    floor_box(bp, -18, 18, -6, 28, f - 1, lambda x, z: (
        BRASS if 8.5 <= math.hypot(x - cx, z - cz) < 9.5 else
        GILD if 12.5 <= math.hypot(x - cx, z - cz) < 13.4 and (x + z) % 3 == 0 else
        TREAD if math.hypot(x - cx, z - cz) < 8.5 else FLOOR_HALL.pick(x, f - 1, z)))
    # the plinth and the pressure vessel, its gauges and valve wheels
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d <= 7.3:
                bp.set(x, f, z, CHIS if d > 6.3 else PBB)
                if d <= 6.3:
                    bp.set(x, f + 1, z, PBB)
    top = vessel(bp, cx, cz, f + 2, 24, 5.4, shell=IRON, band=BRASS)
    for (dx, dz, fc) in ((6, 0, "east"), (-6, 0, "west"), (0, 6, "south"), (0, -6, "north")):
        bp.set(cx + dx, 13, cz + dz, GAUGE)
        bp.set(cx + dx, 10, cz + dz, GEAR)
        bp.set(cx + dx, 17, cz + dz, GAUGE)
    # the steam pipes: from the vessel to the four walls at y 20, on hangers
    for x in list(range(-18, -5)) + list(range(6, 19)):
        bp.set(x, 20, cz, PIPES)
    for z in list(range(-6, cz - 5)) + list(range(cz + 6, 29)):
        bp.set(cx, 20, z, PIPES)
    for y in range(21, 31):
        bp.set(cx, y, cz, PIPES)                             # the riser to the roof
    # four great columns (3 x 3, brass bands, capitals)
    for (px, pz) in ((-12, -1), (12, -1), (-12, 21), (12, 21)):
        for y in range(f, 31):
            for x in range(px - 1, px + 2):
                for z in range(pz - 1, pz + 2):
                    if y in (f, f + 1) or y >= 29:
                        bp.set(x, y, z, CHIS)
                    elif y % 6 == 0:
                        bp.set(x, y, z, BRASS)
                    else:
                        bp.set(x, y, z, PBB if (x == px or z == pz) else PB)
        for (dx, dz, fc) in ((2, 0, "west"), (-2, 0, "east"), (0, 2, "north"), (0, -2, "south")):
            bp.set(px + dx, 28, pz + dz, stair(PBBS, fc, "top"))
    # ceiling girders and chandeliers
    for z in (-3, 4, 16, 25):
        for x in range(-18, 19):
            bp.set(x, 30, z, IRON)
    for (x, z) in ((-7, 0), (7, 0), (-7, 22), (7, 22), (-14, 10), (14, 10)):
        chandelier(bp, x, 30, z, soul=True, drop=3)
    # the governor's balcony on the north wall (feet 20), on corbels
    for x in range(-18, 19):
        for z in range(-6, -3):
            bp.set(x, L2 - 1, z, DECK.pick(x, L2 - 1, z))
        rail(bp, x, L2, -3)
        if x % 4 == 0:
            bp.set(x, L2 - 2, -4, stair(IRON_STAIRS, "north", "top"))
            bp.set(x, L2 - 2, -5, IRON)
    # the hub waystone by the entrance, benches, a map table, stores
    bp.set(5, f, 25, MOD["waystone"])
    for x in (-6, -5, -4):
        bp.set(x, f, 26, stair(PBBS, "north"))
    bp.set(-8, f, 24, "cartography_table")
    bp.set(-9, f, 24, "lectern[facing=east,has_book=false,powered=false]")
    chest(bp, -17, f, 27, "east", "se_hall")
    for (x, z) in ((-17, 25), (-17, 26), (17, 27), (16, 27)):
        bp.set(x, f, z, "barrel[facing=up,open=false]")
    # the doorways: north (to the hoppers), west arch (to the piston gallery), the one-way iron door (east)
    for y in range(G, G + 5):
        for x in (-3, 3):
            bp.set(x, y, -7, BRASS if y == G + 4 else CHIS)
    for x in range(-3, 4):
        bp.set(x, G + 5, -7, GILD)
    for z in (7, 13):
        for y in range(G, G + 7):
            bp.set(-19, y, z, CHIS)
    for z in range(7, 14):
        bp.set(-19, G + 7, z, GILD)
    bp.set(18, G + 2, 1, GAUGE)


# ------------------------------------------------------------------ the bone hopper hall
def hopper_hall(bp):
    f = G
    floor_box(bp, -18, 18, -39, -10, f - 1, lambda x, z: BONE_Z if abs(x) <= 1 else STYLES["bone"][0].pick(x, f - 1, z))
    # three chutes from the conveyor intake pour bones into funnel hoppers
    for cx in (-10, 0, 10):
        cz = -34
        for y in range(f + 8, 16):
            bp.set(cx, y, cz, BONE if y % 3 else IRON)
        for k, y in enumerate((f + 7, f + 6, f + 5)):
            r = 2 - k
            for x in range(cx - r - 1, cx + r + 2):
                for z in range(cz - r - 1, cz + r + 2):
                    edge = abs(x - cx) == r + 1 or abs(z - cz) == r + 1
                    bp.set(x, y, z, IRON if edge else BONE)
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            for y in range(f, f + 7):
                bp.set(cx + dx, y, cz + dz, IRON_WALL if y < f + 6 else IRON)
        # bone heaps under the funnel
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 2, cz + 5):
                h = int(2.6 - math.hypot(x - cx, z - cz) * 0.7 + hash01(x, z, 761))
                for y in range(f, f + max(0, h)):
                    if bp.get(x, y, z) == AIR:
                        bp.set(x, y, z, BONE if hash3(x, y, z, 762) > 0.2 else "bone_block[axis=x]")
        bp.set(cx + 2, f, cz + 4, SKULL.format(int(hash01(cx, cz, 763) * 16)))
    # the bone grinder: two great gear wheels between iron cheeks, the grindstones
    for gx in (-4, 4):
        for y in range(f, f + 8):
            for z in range(-28, -21):
                d = math.hypot(z + 25, y - (f + 4))
                if d <= 3.6:
                    bp.set(gx, y, z, GEAR if d > 2.4 or d < 0.8 else IRON)
        bp.set(gx, f + 4, -25, BRASS)
    for x in (-6, 6):
        for y in range(f, f + 9):
            bp.set(x, y, -25, IRON if y < f + 8 else BRASS)
    for x in range(-3, 4):
        bp.set(x, f, -25, "grindstone[face=floor,facing=north]")
    for x in range(-6, 7):
        bp.set(x, f + 9, -25, IRON)
    # sorting tables, skull racks along the walls
    for z in range(-20, -11, 3):
        bp.table(-16, f, z, top="polished_blackstone_pressure_plate", leg=PBBW)
        bp.table(16, f, z, top="polished_blackstone_pressure_plate", leg=PBBW)
    for x in range(-17, 18, 2):
        wall_skull(bp, x, f + 3, -39, "south")
    for z in range(-38, -10, 2):
        wall_skull(bp, -18, f + 3, z, "east")
        wall_skull(bp, 18, f + 3, z, "west")
    for (x, z) in ((-10, -16), (10, -16), (0, -14)):
        hang(bp, x, 14, z, HANG_SOUL, drop=1)
    for (x, z) in ((-10, -28), (10, -28)):
        hang(bp, x, 13, z, HANG_SOUL, drop=2)
    chest(bp, 17, f, -38, "west", "se_hopper")
    bp.spawner(13, f, -30, MOB_SKEL)
    for (x, z) in ((-17, -38), (-16, -38)):
        bp.set(x, f, z, "barrel[facing=up,open=false]")
    # doorframes east and west (to the bunker and the ossuary stair hall)
    for (x, s) in ((19, 1), (-19, -1)):
        for z in (-27, -23):
            for y in range(f, f + 5):
                bp.set(x, y, z, CHIS)
        for z in range(-27, -22):
            bp.set(x, f + 5, z, BRASS)


# ------------------------------------------------------------------ the ossuary stair hall (north-west)
def nw_hall(bp):
    f = G
    # the stairwell down to the ossuary along the north wall (x -27 .. -48, z -39 .. -37)
    landing(bp, -27, -27, -39, -37, f, PATH, low=OF - 1)
    # flight 1 down to the west: step k at x -28-k, feet f-1-k
    for k in range(8):
        xx = -28 - k
        fk = f - 1 - k
        for z in range(-39, -36):
            for y in range(OF - 1, fk - 1):
                bp.set(xx, y, z, PBB)
            bp.set(xx, fk - 1, z, stair(PBBS, "east"))
            for y in range(fk, f + 4):
                bp.set(xx, y, z, AIR)
    landing(bp, -38, -36, -39, -37, f - 8, PATH, low=OF - 1)
    for y in range(f - 8, f + 4):
        for xx in range(-38, -35):
            for z in range(-39, -36):
                bp.set(xx, y, z, AIR)
    for k in range(8):
        xx = -39 - k
        fk = f - 9 - k
        for z in range(-39, -36):
            for y in range(OF - 1, fk - 1):
                bp.set(xx, y, z, PBB)
            bp.set(xx, fk - 1, z, stair(PBBS, "east"))
            for y in range(fk, fk + 4):
                bp.set(xx, y, z, AIR)
    # the railing round the stairwell in the hall floor
    for xx in range(-48, -26):
        rail(bp, xx, f, -36)
    for z in range(-39, -36):
        rail(bp, -49, f, z)
    # the lift cage round the piston lift (x -40 .. -38, z -19 .. -17), its iron door south
    lift_cage(bp, G, 15, door=True)
    # mortuary carts, skull niches, candles, a bone wheel
    for xx in range(-48, -25, 2):
        if not -41 <= xx <= -36:
            wall_skull(bp, xx, f + 2, -12, "north")
    for z in range(-34, -12, 2):
        wall_skull(bp, -49, f + 2, z, "east")
        wall_skull(bp, -49, f + 4, z + 1, "east")
    for (xx, z) in ((-30, -20), (-30, -25), (-45, -24)):
        bp.set(xx, f, z, PBB)
        bp.set(xx, f + 1, z, CANDLE.format(3))
    # a mortuary cart: a slab bed on wheels, laid with bones
    for xx in range(-34, -30):
        bp.set(xx, f, -14, "spruce_slab[type=top,waterlogged=false]")
        bp.set(xx, f + 1, -14, BONE_X if xx % 2 else "bone_block[axis=x]")
    bp.set(-35, f, -14, GEAR)
    bp.set(-29, f, -14, GEAR)
    for (xx, z) in ((-30, -30), (-30, -18), (-45, -26)):
        hang(bp, xx, 14, z, HANG_SOUL)
    bp.spawner(-30, f, -32, MOB_GRAVE)
    for (xx, z) in ((-25, -13), (-26, -13)):
        bp.set(xx, f, z, "barrel[facing=up,open=false]")


def lift_cage(bp, y0, y1, door=False):
    """The cage of the piston lift where it crosses a room: dark iron frame, glass, a brass band; at the bottom
    the iron door south, its lever inside only."""
    for y in range(y0, y1 + 1):
        for x in range(-41, -36):
            for z in range(-20, -15):
                if x in (-41, -37) or z in (-20, -16):
                    corner = x in (-41, -37) and z in (-20, -16)
                    bp.set(x, y, z, IRON if corner or y in (y0, y1) or (y - y0) % 4 == 3 else GLASS)
    for y in range(y0, y1 + 1):
        bp.set(-39, y, -19, LADDER.format("south"))
    if door:
        bp.door(-39, y0, -16, "south", wood="iron")
        lever(bp, -38, y0 + 1, -17, "north")
        bp.set(-39, y0 + 2, -16, BRASS)
        for y in (y0, y0 + 1):
            bp.set(-40, y, -16, IRON)
            bp.set(-38, y, -16, IRON)


# ------------------------------------------------------------------ the soul-soil bunker (north-east)
def bunker(bp):
    f = G
    floor_box(bp, 24, 49, -39, -12, f - 1, STYLES["soot"][0])
    # heaps of soul soil and coal under the chutes, a rail track, shovels and barrows
    for (cx, cz, r) in ((32, -32, 4.5), (43, -30, 5.0), (40, -18, 3.5)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                h = int((r - math.hypot(x - cx, z - cz)) * 0.9 + hash01(x, z, 771) * 0.8)
                for y in range(f, f + max(0, h)):
                    bp.set(x, y, z, "coal_block" if hash3(x, y, z, 772) < 0.25 else "soul_soil")
        for y in range(f + 6, 16):
            bp.set(int(cx), y, int(cz), IRON if y == 15 else "soul_soil")
        bp.set(int(cx), f + 5, int(cz), "hopper[enabled=true,facing=down]")
    for x in range(25, 49):
        bp.set(x, f, -14, "rail[shape=east_west,waterlogged=false]")
    for (x, z) in ((26, -38), (27, -38), (48, -13)):
        bp.set(x, f, z, "barrel[facing=up,open=false]")
    chest(bp, 48, f, -38, "west", "se_bunker")
    for (x, z) in ((30, -22), (44, -22)):
        hang(bp, x, 14, z, HANG_SOUL)
    bp.spawner(36, f, -26, MOB_IMP)


# ------------------------------------------------------------------ the soul furnace
FURNACES = (0, 13, 26)     # z centres of the three fireboxes


def soul_furnace(bp):
    f = G
    floor_box(bp, 24, 49, -8, 39, f - 1, lambda x, z: "soul_soil" if x >= 38 and hash01(x, z, 781) < 0.3
              else STYLES["soot"][0].pick(x, f - 1, z))
    for cz in FURNACES:
        # the firebox: x 41 .. 52 (through the east wall), its mouths barred at both ends
        for x in range(40, 53):
            for z in range(cz - 4, cz + 5):
                for y in range(f, 19):
                    edge = x in (40, 52) or z in (cz - 4, cz + 4) or y >= 12
                    inner = 41 <= x <= 51 and cz - 3 <= z <= cz + 3 and f <= y <= f + 4
                    if inner:
                        if y == f:
                            bp.set(x, y, z, SOUL_FIRE if (x + z) % 3 else SOUL_CAMP)
                        else:
                            bp.set(x, y, z, AIR)
                    elif edge or not inner:
                        if x in (40, 52) and abs(z - cz) <= 2 and f <= y <= f + 3:
                            bp.set(x, y, z, "iron_bars")
                        elif y in (12, 18):
                            bp.set(x, y, z, BRASS)
                        else:
                            bp.set(x, y, z, SMOKE if hash3(x, y, z, 782) > 0.15 else PBB)
                bp.set(x, f - 1, z, "soul_soil") if 41 <= x <= 51 and abs(z - cz) <= 3 else None
        # the arch over the inner mouth, its lintel, the gauge
        for z in range(cz - 3, cz + 4):
            bp.set(39, f + 5, z, stair(SMOKE_STAIRS, "east", "top"))
        bp.set(39, f + 7, cz, GAUGE)
        bp.set(39, f + 7, cz - 2, GEAR)
        bp.set(39, f + 7, cz + 2, GEAR)
        # outside: a hood over the outer mouth
        for z in range(cz - 3, cz + 4):
            bp.set(53, f + 5, z, stair(SMOKE_STAIRS, "west", "top"))
            bp.set(53, f + 6, z, BRASS)
        # stoking: soul soil heap and a coal barrow in front
        for (x, z) in ((36, cz - 3), (36, cz + 3)):
            bp.set(x, f, z, "soul_soil")
            bp.set(x - 1, f, z, "soul_soil")
            bp.set(x, f + 1, z, "soul_soil") if hash01(x, z, 783) < 0.5 else None
    # the boiler drum over the furnaces (a horizontal cylinder along z, y 20 .. 28) with steam domes
    for z in range(-6, 31):
        for x in range(40, 50):
            for y in range(19, 30):
                d = math.hypot(x - 45, y - 23)
                if d <= 4.6:
                    if d > 3.8:
                        bp.set(x, y, z, BRASS if z % 6 == 0 else IRON)
                    else:
                        bp.set(x, y, z, "blackstone")
    for z in (2, 16):
        for y in range(28, 30):
            for x in range(44, 47):
                bp.set(x, y, z, COPPER)
    # the stair up the west wall: flight 1 north from z 38 (feet 7..13), landing, flight 2 (feet 14..20)
    zz, ff = flight_z(bp, 24, 26, 38, 7, f, -1, low=f - 1, wall=27)
    landing(bp, 24, 26, 28, 31, ff, PATH, low=f - 1, wall=27)
    zz, ff = flight_z(bp, 24, 26, 27, 7, ff, -1, low=f - 1, wall=27)
    # the stokers' balcony at feet 20 (z 20 .. -8), corbels under its edge
    for z in range(-8, 21):
        for x in range(24, 27):
            bp.set(x, L2 - 1, z, DECK.pick(x, L2 - 1, z))
        rail(bp, 27, L2, z)
        if z % 4 == 0:
            bp.set(27, L2 - 2, z, stair(IRON_STAIRS, "west", "top"))
            bp.set(26, L2 - 2, z, IRON)
    # the one-way door into the pressure hall: an iron door with its lever on this side only
    bp.door(23, f, 2, "east", wood="iron")
    lever(bp, 24, f + 1, 3, "east")
    bp.set(23, f + 2, 2, BRASS)
    # soul-sand chutes from the ceiling, lamps, stores
    for (x, z) in ((33, 6), (33, 20)):
        for y in range(24, 31):
            bp.set(x, y, z, "soul_sand" if y % 3 else IRON)
    for (x, z) in ((32, -4), (32, 14), (32, 30)):
        chandelier(bp, x, 30, z, soul=True, drop=4)
    chest(bp, 48, f, 37, "west", "se_furnace")
    for (x, z) in ((48, 38), (47, 38), (48, -7)):
        bp.set(x, f, z, "barrel[facing=up,open=false]")
    for (x, z) in ((34, 34), (36, -2)):
        bp.set(x, f, z, LEATHER)
        bp.set(x, f + 1, z, LEATHER)
    bp.spawner(31, f, 8, MOB_HOUND)
    bp.spawner(37, f, 24, MOB_IMP)


# ------------------------------------------------------------------ the stokers' mess (north-east, upper)
def mess(bp):
    f = L2
    # bunks: crimson frames with wool mattresses (no beds in the Nether)
    for x in range(26, 48, 4):
        for (z0, fc) in ((-38, "south"), (-15, "north")):
            for dz in range(0, 3):
                z = z0 + dz if z0 < -20 else z0 - dz
                bp.set(x, f, z, "crimson_planks")
                bp.set(x, f + 1, z, "gray_wool")
                bp.set(x, f + 2, z, "crimson_fence")
                bp.set(x, f + 3, z, "crimson_planks")
                bp.set(x, f + 4, z, "brown_wool")
            bp.set(x + 1, f, z0, "crimson_trapdoor[facing=north,half=bottom,open=false,waterlogged=false]")
    # the long tables and benches
    for z in (-28, -23):
        for x in range(28, 46):
            bp.set(x, f, z, TABLE if x % 6 else "crimson_planks")
            bp.set(x, f, z - 1, stair(MAHOGANY_STAIRS, "south"))
            bp.set(x, f, z + 1, stair(MAHOGANY_STAIRS, "north"))
        for x in range(30, 46, 5):
            bp.set(x, f + 1, z, CANDLE.format(2))
    # the hearth: a soul fire under a cauldron, the chimney hood
    for z in range(-27, -23):
        bp.set(48, f, z, PBB)
    bp.set(48, f, -26, SOUL_CAMP)
    bp.set(48, f, -25, "cauldron")
    for z in range(-27, -23):
        bp.set(48, f + 3, z, stair(SMOKE_STAIRS, "west", "top"))
    for (x, z) in ((30, -20), (40, -20), (36, -32)):
        hang(bp, x, 27, z, HANG_SOUL)
    chest(bp, 48, f, -37, "west", "se_mess")
    for (x, z) in ((48, -38), (48, -13), (47, -13)):
        bp.set(x, f, z, "barrel[facing=up,open=false]")
    bp.spawner(44, f, -20, MOB_GUARD)
    # windows east
    for z in (-36, -26, -14):
        pierce(bp, 49, f + 1, z, 1, 0, h=3, fill=GLASS)


def pierce(bp, x, y, z, dx, dz, h=3, w=1, fill=GLASS, max_steps=6, sill=True):
    """A window from a room outwards: walks through solid cells to the outside and opens h x w; the outermost
    cell gets ``fill`` and a sill under it."""
    px, pz = (1, 0) if dx == 0 else (0, 1)
    xx, zz = x + dx, z + dz
    steps = 0
    while steps < max_steps and any(solid(xx + px * s, y + k, zz + pz * s) for s in range(w) for k in range(h)):
        for s in range(w):
            for k in range(h):
                bp.set(xx + px * s, y + k, zz + pz * s, AIR)
        # line the tunnel where it crosses the unset core of a wall
        for s in range(-1, w + 1):
            for k in range(-1, h + 1):
                if (0 <= s < w) and (0 <= k < h):
                    continue
                q = (xx + px * s, y + k, zz + pz * s)
                if bp.get(*q) is None:
                    bp.set(*q, PBB)
        xx, zz = xx + dx, zz + dz
        steps += 1
    xx, zz = xx - dx, zz - dz
    fc = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
    for s in range(w):
        for k in range(h):
            bp.set(xx + px * s, y + k, zz + pz * s, fill)
        if not sill:
            continue
        bp.set(xx + dx + px * s, y - 1, zz + dz + pz * s, stair(IRON_STAIRS, fc, "top"))
        bp.set(xx + dx + px * s, y + h, zz + dz + pz * s, stair(IRON_STAIRS, fc, "bottom")) \
            if bp.get(xx + dx + px * s, y + h, zz + dz + pz * s) is None else None


# ------------------------------------------------------------------ the governor's control room
def governor(bp):
    f = L2
    cx, cz = 0, -27
    floor_box(bp, -18, 18, -39, -12, f - 1, lambda x, z: "red_carpet" if False else
              (BRASS if 5.5 <= math.hypot(x - cx, z - cz) < 6.5 else "dark_oak_planks"))
    # the flyball governor: the spindle, the collars, two arms and the brass balls, the bevel gears below
    for y in range(f, 31):
        bp.set(cx, y, cz, IRON_WALL if 0 < y - f < 9 else IRON)
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.3:
                bp.set(x, f, z, GEAR if d > 2.6 else (IRON if d > 1.2 else BRASS))
    for (yy, r) in ((f + 8, 1), (f + 4, 1)):
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(cx + dx, yy, cz + dz, BRASS)
    for side in (-1, 1):
        for k in range(1, 5):
            bp.set(cx + side * k, f + 8 - k, cz, IRON_WALL if k < 4 else IRON)
        bx, by = cx + side * 5, f + 3
        for x in range(bx - 1, bx + 2):
            for y in range(by - 1, by + 2):
                for z in range(cz - 1, cz + 2):
                    if abs(x - bx) + abs(y - by) + abs(z - cz) <= 2:
                        bp.set(x, y, z, GILD if (x, y, z) == (bx, by + 1, cz) else BRASS)
        for k in range(1, 3):
            bp.set(cx + side * k, f + 4 + (k - 1), cz, IRON_WALL)
    # the gauge wall (north) and the control desks round the governor
    for x in range(-16, 17):
        for y in range(f + 1, f + 8):
            spec = GAUGE if (x % 3 == 0 and y % 2 == 1) else (BRASS if y == f + 7 else
                                                                     PIPES if x % 3 == 0 else MAHOGANY)
            bp.set(x, y, -39, spec)
    for x in range(-14, 15):
        if abs(x) <= 5:
            continue
        bp.set(x, f, -35, MAHOGANY)
        bp.set(x, f + 1, -35, "lever[face=floor,facing=north,powered=false]" if x % 2 else
               "polished_blackstone_button[face=floor,facing=north,powered=false]")
        bp.set(x, f, -34, stair(MAHOGANY_STAIRS, "north"))
    for (x0, x1, z) in ((-14, -9, -18), (9, 14, -18)):
        for x in range(x0, x1 + 1):
            bp.set(x, f, z, MAHOGANY)
            bp.set(x, f + 1, z, GAUGE if x % 2 else "lever[face=floor,facing=south,powered=false]")
    bp.set(-10, f, -14, "cartography_table")
    bp.set(-11, f, -14, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(10, f, -14, TABLE)
    bp.set(10, f, -13, stair(MAHOGANY_STAIRS, "north"))
    # windows onto the pressure hall (the balcony door in the middle)
    for x in (-12, -7, 7, 12):
        pierce(bp, x, f + 2, -12, 0, 1, h=3, fill="iron_bars", sill=False)
    for y in range(L2, L2 + 4):
        for x in (-3, 3):
            bp.set(x, y, -12, BRASS if y == L2 + 3 else CHIS)
    # lamps, carpet runner, stores
    for x in range(-2, 3):
        for z in range(-17, -12):
            bp.set(x, f, z, "red_carpet")
    for (x, z) in ((-10, -26), (10, -26), (0, -16), (-10, -34), (10, -34)):
        hang(bp, x, 29, z, "lantern[hanging=true,waterlogged=false]" if x == 0 else HANG_SOUL)
    chest(bp, 17, f, -38, "west", "se_governor")
    bp.set(16, f, -38, "barrel[facing=up,open=false]")
    bp.spawner(-15, f, -30, MOB_KNIGHT)


# ------------------------------------------------------------------ the valve room and the piston shaft
def valve_room(bp):
    f = L2
    # manifolds: pipe runs on the walls, valve wheels, pressure tanks along the south wall
    for x in range(-40, -24):
        bp.set(x, f + 6, -39, PIPES)
        bp.set(x, f + 3, -39, PIPES)
        if x % 3 == 0:
            bp.set(x, f + 4, -39, GEAR)
            bp.set(x, f + 5, -39, GAUGE)
    for (tx, tz) in ((-33, -14), (-28, -14), (-46, -15)):
        vessel(bp, tx, tz, f, f + 5, 1.6, shell=COPPER, band=BRASS)
    for z in range(-38, -12):
        bp.set(-24, f + 7, z, PIPES)
    lift_cage(bp, L2, 30, door=False)
    for (x, z) in ((-32, -24), (-28, -32)):
        hang(bp, x, 29, z, HANG_SOUL)
    chest(bp, -25, f, -38, "west", "se_gallery")
    bp.spawner(-30, f, -20, MOB_WISP)
    for z in range(-30, -26):
        wall_skull(bp, -24, f + 2, z, "west")
    for z in (-36, -27, -15):
        pierce(bp, -49, f + 2, z, -1, 0, h=3, fill=GLASS)


def piston_shaft(bp):
    """The newel stair in the disused cylinder sleeve: feet 20 (valve room) -> 42 (site of grace), 3 wide."""
    newel_laps(bp, -49, -39, 3, L2, [3, 3, 3, 3, 3, 3, 2, 2], 3, cw=True, tread="polished_blackstone_brick",
               fill=PBB, clear=4, core_spec=BRASS, lamps=False)
    for x in range(-49, -40):
        for z in range(-39, -30):
            for y in range(L2 - 1, AF + 5):
                if bp.get(x, y, z) == "minecraft:polished_andesite":
                    bp.set(x, y, z, CHIS)
    # lamps set in the core
    for y in range(L2 + 2, AF + 3, 4):
        for (x, z) in ((-46, -36), (-44, -34), (-46, -34), (-44, -36)):
            bp.set(x, y, z, "shroomlight" if (y // 4) % 2 else GILD)


def grace(bp):
    f = AF
    floor_box(bp, -49, -39, -30, -20, f - 1, lambda x, z: GILD if (x, z) == (-44, -25) else
              CHIS if (x + z) % 4 == 0 else PBB)
    bp.set(-44, f, -26, MOD["waystone"])
    brazier(bp, -48, f, -22, soul=True)
    brazier(bp, -48, f, -28, soul=True)
    for x in (-46, -45, -44):
        bp.set(x, f, -21, stair(PBBS, "north"))
    bp.set(-40, f, -28, "barrel[facing=up,open=false]")
    hang(bp, -44, AF + 4, -24, HANG_SOUL)
    # the doorway to the lift (south), framed
    for y in range(f, f + 4):
        bp.set(-40, y, -20, BRASS if y == f + 3 else IRON)
        bp.set(-38, y, -20, BRASS if y == f + 3 else IRON)
    # the top of the lift: ladder ends at the floor, railing
    # the corridor east to the arena: compression, lamps, the mist at its end
    floor_box(bp, -38, -20, -24, -22, f - 1, PATH)
    for x in (-34, -27):
        hang(bp, x, f + 3, -23, HANG_SOUL, drop=0)
    bp.mist(-20, f, -24, -20, f + 3, -22)


def lift(bp):
    """The piston lift: a ladder from the site of grace down to the ossuary stair hall (36 rungs), the brass
    piston head at its foot."""
    for y in range(16, 20):
        bp.set(-39, y, -19, LADDER.format("south"))
    for y in range(31, AF):
        bp.set(-39, y, -19, LADDER.format("south"))
    for y in range(G, AF):
        bp.set(-39, y, -19, LADDER.format("south"))
    for (x, z) in ((-40, -18), (-38, -18), (-40, -17), (-38, -17), (-39, -17)):
        bp.set(x, G - 1, z, BRASS)
    for y in range(AF + 2, AF + 4):
        bp.set(-39, y, -18, CHAIN)
    bp.set(-39, AF + 1, -18, GEAR) if False else None


# ------------------------------------------------------------------ the crankcase: arena, trench, flywheel
def arena(bp):
    f = AF
    ax, az = AC
    for x in range(-19, 20):
        for z in range(-26, 13):
            d = math.hypot(x - ax, z - az)
            if d <= 2.4:
                spec = GILD
            elif d <= 4.4:
                spec = GEAR
            elif 9.5 <= d < 10.5 or 16.5 <= d < 17.5:
                spec = BRASS
            elif d < 17.5:
                spec = TREAD if int(d) % 2 else IRON
            else:
                spec = IRON if (x + z) % 3 else PB
            bp.set(x, f - 1, z, spec)
    bp.boss_seal(ax, f - 1, az, BOSS, 18)
    # railing over the crank trench (north), two ladders out of the trench
    for x in range(-19, 20):
        if x in (-10, 10):
            continue
        rail(bp, x, f, -26)
    for x in (-10, 10):
        for y in range(34, f):
            bp.set(x, y, -27, LADDER.format("north"))
    # corner braziers, the ceiling girders and lamps
    for (x, z) in ((-16, 9), (16, 9), (-16, -23), (16, -23)):
        brazier(bp, x, f, z, soul=True, big=True)
    for z in (-20, -7, 6):
        for x in range(-19, 20):
            bp.set(x, 58, z, IRON)
    for (x, z) in ((-10, -14), (10, -14), (-10, 2), (10, 2)):
        chandelier(bp, x, 58, z, soul=True, drop=3)
    # sealed bars to the reliquary (west wall)
    for z in range(5, 8):
        for y in range(f, f + 3):
            bp.set(-20, y, z, MOD["vault_bars"])
        bp.set(-20, f + 3, z, GILD)
    for y in range(f, f + 4):
        bp.set(-20, y, 4, IRON)
        bp.set(-20, y, 8, IRON)
    floor_box(bp, -23, -20, 5, 7, f - 1, PATH)


def trench(bp):
    """The crank trench (z -37 .. -27, floor y 33): the crankshaft along x, main bearings, the crank webs and the six
    connecting rods rising to the pistons through the crankcase roof."""
    floor_box(bp, -35, 35, -37, -27, 33, Palette({IRON: 3, "polished_basalt[axis=y]": 2}, seed=791))
    for x in range(-35, 36):
        for y in range(37, 40):
            for z in range(PZ - 1, PZ + 2):
                edge = y in (37, 39) and z in (PZ - 1, PZ + 1)
                bp.set(x, y, z, IRON if not edge else "polished_basalt[axis=x]")
        if x % 6 == 3:
            for z in range(PZ - 1, PZ + 2):
                bp.set(x, 38, z, BRASS)
    for bx in (-34, -24, -12, 0, 12, 24, 34):
        for x in range(bx - 1, bx + 2):
            for z in range(PZ - 2, PZ + 3):
                for y in range(34, 37):
                    bp.set(x, y, z, PBB if y < 36 else BRASS)
    for i, (px, top) in enumerate(PISTONS):
        up = top >= 78
        pin = 42 if up else 34
        # the webs: two plates on either side of the rod, from the shaft to the pin
        for x in (px - 2, px + 2):
            for y in range(min(pin, 38), max(pin, 38) + 1):
                for z in range(PZ - 1, PZ + 2):
                    bp.set(x, y, z, IRON if y != pin else BRASS)
        # the rod: 3 x 3, from the pin to the ceiling and through the roof into the sleeve
        for y in range(pin, RIDGE + 2):
            for x in range(px - 1, px + 2):
                for z in range(PZ - 1, PZ + 2):
                    if x == px - 1 and y < 37 and not up:
                        pass
                    band = y in (pin, pin + 1, 56, 57)
                    bp.set(x, y, z, BRASS if band else ("iron_block" if (x == px and z == PZ) else IRON))
    # lamps set in the trench walls
    for x in range(-33, 34, 6):
        bp.set(x, 39, -26, "shroomlight")
        bp.set(x, 45, -38, "shroomlight")


def flywheel(bp):
    """The flywheel in its bay east of the arena: a wheel 17 across in the y-z plane, six spokes, the hub on its
    axle into the wall."""
    cz, cy = -7, 50
    for x in (22, 23):
        for z in range(cz - 9, cz + 10):
            for y in range(cy - 9, cy + 10):
                d = math.hypot(z - cz, y - cy)
                a = math.degrees(math.atan2(y - cy, z - cz)) % 60
                if 6.6 < d <= 8.3:
                    bp.set(x, y, z, BRASS if int(math.degrees(math.atan2(y - cy, z - cz)) + 360) % 30 < 6 else IRON)
                elif d <= 1.7:
                    bp.set(x, y, z, GEAR)
                elif d <= 6.6 and (a < 7 or a > 53):
                    bp.set(x, y, z, IRON)
    for x in (24, 25):
        for z in range(cz - 1, cz + 2):
            for y in range(cy - 1, cy + 2):
                bp.set(x, y, z, BRASS if (z, y) == (cz, cy) else IRON)
    floor_box(bp, 20, 25, -18, 4, AF - 1, DECK)


def reliquary(bp):
    """The soul reliquary: gilded caskets, the engine's hoard, the skulls of its makers on pedestals, a soul in a
    lantern on the altar; the bone chute in the floor (the way back)."""
    f = AF
    floor_box(bp, -38, -24, 0, 12, f - 1, lambda x, z: GBS if (x + z) % 5 == 0 else PBB)
    chest(bp, -37, f, 2, "east", "se_reliquary")
    chest(bp, -37, f, 6, "east", "se_reliquary")
    chest(bp, -31, f, 0, "south", "se_reliquary")
    for x in range(-34, -27):
        bp.set(x, f, 12, "gold_block" if x % 2 else GBS)
        bp.set(x, f + 1, 12, WITHER.format(0) if x % 3 == 0 else (CANDLE.format(4) if x % 2 else AIR))
    for (x, z) in ((-26, 1), (-26, 11)):
        bp.set(x, f, z, CHIS)
        bp.set(x, f + 1, z, GILD)
        bp.set(x, f + 2, z, SKULL.format(4))
    # the altar: a soul lantern on gilded blackstone
    bp.set(-31, f, 6, GBS)
    bp.set(-31, f + 1, 6, SOUL_LANT)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(-31 + dx, f, 6 + dz, stair(PBBS, {(1, 0): "west", (-1, 0): "east", (0, 1): "north",
                                                 (0, -1): "south"}[(dx, dz)]))
    hang(bp, -31, f + 5, 3, HANG_SOUL)
    hang(bp, -31, f + 5, 10, HANG_SOUL)
    for x in range(-38, -23, 3):
        for y in range(f + 1, f + 5, 2):
            wall_skull(bp, x, y, 0, "south")
    # the bone chute: a 2 x 2 hole with a bone rim, onto hay in the piston gallery 16 below
    for (x, z) in ((-37, 7), (-37, 8), (-37, 9), (-37, 10), (-34, 7), (-34, 8), (-34, 9), (-34, 10),
                   (-36, 7), (-35, 7), (-36, 10), (-35, 10)):
        bp.set(x, f - 1, z, BONE)
    for y in range(34, AF):
        for x in (-37, -34):
            for z in (8, 9):
                bp.set(x, y, z, BONEP.pick(x, y, z)) if bp.get(x, y, z) not in (None, AIR) else None


# ------------------------------------------------------------------ the piston gallery (west)
def piston_gallery(bp):
    f = G
    floor_box(bp, -49, -24, -8, 39, f - 1, DECK)
    # two spare pistons lying on cradles: rods along z with their heads
    for cx in (-42, -32):
        cy = f + 5
        for z in range(-4, 25):
            for x in range(cx - 3, cx + 4):
                for y in range(cy - 3, cy + 4):
                    d = math.hypot(x - cx, y - cy)
                    if d <= 2.4:
                        bp.set(x, y, z, "iron_block" if d < 1.5 else (BRASS if z % 7 == 0 else IRON))
        for z in range(25, 30):
            for x in range(cx - 5, cx + 6):
                for y in range(cy - 5, cy + 6):
                    d = math.hypot(x - cx, y - cy)
                    if d <= 4.2 and y >= f:
                        bp.set(x, y, z, BRASS if z in (26, 28) and d > 3.3 else IRON)
        for z in (0, 8, 16, 22):
            for x in range(cx - 2, cx + 3):
                for y in range(f, f + 3):
                    bp.set(x, y, z, PBB if y < f + 2 else (BRASS if abs(x - cx) == 2 else IRON))
    # piston rings stacked on the floor, a gantry crane on the walls
    for (rx, rz) in ((-45, 34), (-27, -5)):
        for y in range(f, f + 3):
            for x in range(rx - 2, rx + 3):
                for z in range(rz - 2, rz + 3):
                    if 1.5 < math.hypot(x - rx, z - rz) <= 2.5:
                        bp.set(x, y, z, BRASS if y % 2 else COPPER)
    for z in range(-8, 40):
        bp.set(-49, 30, z, IRON)
        bp.set(-24, 30, z, IRON)
    for x in range(-48, -24):
        bp.set(x, 30, 18, IRON)
        bp.set(x, 30, 19, IRON)
    for y in range(17, 30):
        bp.set(-36, y, 18, CHAIN)
    bp.set(-36, 16, 18, IRON)
    for (dx, dz) in ((1, 0), (-1, 0)):
        bp.set(-36 + dx, 15, 18, IRON_WALL)
    # the catwalk (feet 26): along the west wall and across at z 7 .. 10; hay where the chute lands
    for z in range(-8, 40):
        for x in range(-49, -46):
            bp.set(x, CW - 1, z, DECK.pick(x, CW - 1, z))
        rail(bp, -46, CW, z) if not (7 <= z <= 10) else None
        if z % 4 == 0:
            bp.set(-46, CW - 2, z, stair(IRON_STAIRS, "east", "top"))
    for x in range(-46, -26):
        for z in range(7, 11):
            bp.set(x, CW - 1, z, HAY if (x in (-36, -35) and z in (8, 9)) else DECK.pick(x, CW - 1, z))
        rail(bp, x, CW, 6)
        rail(bp, x, CW, 11)
        if x % 4 == 0:
            bp.set(x, CW - 2, 7, stair(IRON_STAIRS, "south", "top"))
            bp.set(x, CW - 2, 10, stair(IRON_STAIRS, "north", "top"))
    for x in (-36, -35):
        for z in (8, 9):
            bp.set(x, CW - 2, z, IRON)
    # the stair up the east wall: flight 1 north from z 36 (feet 7..16), landing, flight 2 (feet 17..26)
    zz, ff = flight_z(bp, -26, -24, 36, 10, f, -1, low=f - 1, wall=-27)
    landing(bp, -26, -24, 23, 26, ff, PATH, low=f - 1, wall=-27)
    zz, ff = flight_z(bp, -26, -24, 22, 10, ff, -1, low=f - 1, wall=-27)
    landing(bp, -26, -24, 7, 12, ff, DECK, low=ff - 2)
    # loot on the far end of the catwalk (risk/reward), lamps
    chest(bp, -48, CW, -7, "south", "se_gallery")
    for (x, z) in ((-37, 0), (-37, 28), (-30, 14)):
        hang(bp, x, 30, z, HANG_SOUL, drop=2)
    bp.spawner(-36, f, 12, MOB_HOUND)
    bp.spawner(-48, CW, 30, MOB_SKEL)
    # the crypt stair's hole: railing in the floor
    for z in range(2, 22):
        rail(bp, -45, f, z)
    for x in range(-48, -44):
        rail(bp, x, f, 1)
    for z in (0, 12, 24, 36):
        pierce(bp, -49, f + 8, z, -1, 0, h=6, fill=GLASS)


# ------------------------------------------------------------------ the ossuary
def ossuary(bp):
    # ---- the stair hall's foot and the nave: bone piers and ribs, walls of skulls
    f = OF
    floor_box(bp, -49, -16, -39, -12, f - 1, OSS_FLOOR)
    piers_x, piers_z = (-38, -27), (-30, -21)
    for px in piers_x:
        for pz in piers_z:
            for y in range(f, 0):
                for x in range(px - 1, px + 2):
                    for z in range(pz - 1, pz + 2):
                        bp.set(x, y, z, BONE if (x == px or z == pz) else "bone_block[axis=x]")
    lines_x = (-49,) + piers_x + (-16,)
    lines_z = (-39,) + piers_z + (-12,)
    for x in range(-49, -15):
        for z in range(-39, -11):
            d = min(min(abs(x - lx) for lx in lines_x), min(abs(z - lz) for lz in lines_z))
            for y in range(-1, -1 - max(0, 3 - d), -1):
                if bp.get(x, y, z) == AIR and not (-39 <= z <= -37 and -48 <= x <= -27):
                    bp.set(x, y, z, BONE)
    for x in range(-48, -16, 2):
        if -41 <= x <= -35:
            continue
        for y in (f + 2, f + 4):
            wall_skull(bp, x, y, -12, "north")
    for z in range(-35, -12, 2):
        for y in (f + 2, f + 4):
            wall_skull(bp, -49, y, z, "east")
    # ossuary stacks: bone and skull walls between the piers, candles
    for (x0, x1, z) in ((-46, -41, -26), (-23, -19, -26)):
        for x in range(x0, x1 + 1):
            bp.set(x, f, z, BONE_X)
            bp.set(x, f + 1, z, SKULL.format(0) if x % 2 else WITHER.format(8))
    for (x, z) in ((-44, -16), (-33, -16), (-22, -34), (-44, -33)):
        bp.set(x, f, z, PBB)
        bp.set(x, f + 1, z, CANDLE.format(4))
    for (x, z) in ((-43, -25), (-32, -17), (-21, -25)):
        hang(bp, x, -2, z, HANG_SOUL, drop=1)
    chest(bp, -17, f, -13, "west", "se_ossuary")
    bp.spawner(-21, f, -18, MOB_SKEL)
    bp.spawner(-44, f, -36, MOB_CRAWLER)
    # the arch to the charnel pit
    for y in range(f, f + 6):
        bp.set(-14, y, -28, BONE)
        bp.set(-14, y, -22, BONE)
    for z in range(-28, -21):
        bp.set(-14, f + 6, z, BONE_Z)
    charnel_pit(bp)
    crypt(bp)


def charnel_pit(bp):
    """The charnel pit (floor y -15): a ledge from the nave, steps down, heaps of bones, two bone columns, the bone
    throne at the east end with its guardians."""
    f = PF
    floor_box(bp, -12, 18, -39, -12, f - 1, OSS_FLOOR)
    landing(bp, -12, -9, -27, -23, OF, PATH, low=f - 1)
    for k, x in enumerate(range(-8, -4)):
        fk = OF - 1 - k
        for z in range(-27, -22):
            bp.set(x, fk - 1, z, stair(PBBS, "west"))
            for y in range(f - 1, fk - 1):
                bp.set(x, y, z, PBB)
    for x in range(-12, -8):
        rail(bp, x, OF, -27)
        rail(bp, x, OF, -23)
    # bone heaps (noise mounds) away from the walkway and the throne
    for x in range(-4, 18):
        for z in range(-38, -12):
            if abs(z + 25) <= 3:
                continue
            h = int(fbm(x, z, 5.0, 795) * 5 - 1.5)
            for y in range(f, f + max(0, h)):
                bp.set(x, y, z, BONE if hash3(x, y, z, 796) > 0.3 else "bone_block[axis=z]")
            if h >= 1 and hash01(x, z, 797) < 0.12:
                bp.set(x, f + h, z, SKULL.format(int(hash01(x, z, 798) * 16)))
    for (cx, cz) in ((3, -32), (3, -18)):
        for y in range(f, 0):
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    bp.set(x, y, z, BONE if y % 4 else GILD)
    # the bone throne
    tx, tz = 16, -25
    for z in range(tz - 2, tz + 3):
        for x in range(tx - 1, tx + 2):
            bp.set(x, f, z, BONE)
    bp.set(tx - 1, f + 1, tz, stair("polished_blackstone_brick_stairs", "west"))
    for z in range(tz - 2, tz + 3):
        for y in range(f + 1, f + 5):
            bp.set(tx + 1, y, z, BONE if abs(z - tz) < 2 else BONE_X)
    bp.set(tx + 1, f + 5, tz, WITHER.format(12))
    bp.set(tx - 1, f + 1, tz - 2, BONE)
    bp.set(tx - 1, f + 1, tz + 2, BONE)
    chest(bp, 16, f, -22, "west", "se_pit")
    bp.spawner(11, f, -22, MOB_GRAVE)
    bp.spawner(11, f, -28, MOB_WSKEL)
    for (x, z) in ((3, -25), (10, -25)):
        hang(bp, x, -2, z, HANG_SOUL, drop=1)
    for (x, z) in ((-2, -36), (-2, -14), (15, -37), (15, -13)):
        bp.set(x, f, z, "soul_soil")
        bp.set(x, f + 1, z, SOUL_CAMP)


def crypt(bp):
    """The builders' crypt (feet -10): two rows of sarcophagi with effigies, the lore lectern, the stair up into the
    piston gallery (the loop)."""
    f = OF
    floor_box(bp, -46, -30, -6, 20, f - 1, OSS_FLOOR)
    floor_box(bp, -40, -36, -11, -7, f - 1, PATH)
    for z in range(-4, 19, 4):
        for (x0, fc) in ((-45, "east"), (-33, "west")):
            for x in range(x0, x0 + 3):
                for dz in range(0, 2):
                    bp.set(x, f, z + dz, PBB)
                    bp.set(x, f + 1, z + dz, "polished_blackstone_slab[type=bottom,waterlogged=false]"
                           if x != x0 + 1 else CHIS)
            bp.set(x0 + 1, f + 2, z, SKULL.format(0 if fc == "east" else 8))
            bp.set(x0 + (2 if fc == "east" else 0), f, z + 2, CANDLE.format(2)) if z + 2 <= 20 else None
    bp.set(-38, f, 18, "lectern[facing=north,has_book=false,powered=false]")
    chest(bp, -36, f, 20, "north", "se_crypt")
    for z in (-2, 8, 16):
        hang(bp, -38, -4, z, HANG_SOUL, drop=1)
    bp.spawner(-38, f, 4, MOB_CRAWLER)
    # the stair up (x -48 .. -46): from z 3 north to south, feet -9 .. -2, landing, feet -1 .. 6
    zz, ff = flight_z(bp, -48, -46, 3, 8, f, 1, low=f - 1)
    landing(bp, -48, -46, 11, 13, ff, PATH, low=f - 1)
    zz, ff = flight_z(bp, -48, -46, 14, 8, ff, 1, low=f - 1)
    landing(bp, -48, -46, 2, 2, f, PATH, low=f - 1)


# ------------------------------------------------------------------ the outside: pistons, chimneys, conveyors
def pistons(bp):
    """Six pistons in a row on the crankcase (z -32): copper sleeves with brass flanges, polished rods, the crowns
    frozen at different heights (rising and falling)."""
    for (px, top) in PISTONS:
        hb = top - 4
        s0 = RIDGE + 1
        for y in range(s0, s0 + 5):
            for x in range(px - 6, px + 7):
                for z in range(PZ - 6, PZ + 7):
                    d = math.hypot(x - px, z - PZ)
                    if y in (s0, s0 + 4) and d <= 6.3:
                        bp.set(x, y, z, BRASS if d > 5.3 else IRON)
                    elif d <= 5.3:
                        bp.set(x, y, z, SLEEVE.pick(x, y, z) if d > 4.3 else "blackstone")
        for y in range(s0 + 5, hb):
            for x in range(px - 2, px + 3):
                for z in range(PZ - 2, PZ + 3):
                    if math.hypot(x - px, z - PZ) <= 2.3:
                        bp.set(x, y, z, "iron_block" if (y - hb) % 6 else BRASS)
        for y in range(hb, top + 1):
            for x in range(px - 6, px + 7):
                for z in range(PZ - 6, PZ + 7):
                    d = math.hypot(x - px, z - PZ)
                    if d > 5.4:
                        continue
                    if y == top:
                        spec = GILD if d > 4.6 else (GEAR if d < 1.5 else IRON)
                    elif y in (hb + 1, hb + 3) and d > 4.4:
                        spec = BRASS
                    else:
                        spec = IRON if d > 4.4 or y == hb else "blackstone"
                    bp.set(x, y, z, spec)
        # a steam pipe down the sleeve to the roof, a valve chest on the crankcase roof beside it
        for y in range(UTOP + 1, s0 + 5):
            bp.set(px, y, PZ + 8, PIPES)
        for x in range(px - 1, px + 2):
            for y in range(UTOP + 1, UTOP + 3):
                bp.set(x, y, PZ + 9, IRON if y == UTOP + 1 else BRASS)
        bp.set(px, UTOP + 2, PZ + 10, GAUGE)


def chimney(bp, cx, cz, y0, top, r=4):
    """A ribbed chimney venting blue flame: smokestack bricks with eight iron ribs, brass bands, a flared crown
    and a ring of soul fire burning in its mouth."""
    for y in range(y0, top + 1):
        for x in range(cx - r - 2, cx + r + 3):
            for z in range(cz - r - 2, cz + r + 3):
                d = math.hypot(x - cx, z - cz)
                if r - 0.8 < d <= r + 0.3:
                    bp.set(x, y, z, BRASS if (top - y) % 9 == 3 else (SMOKE if hash3(x, y, z, 801) > 0.2 else PBB))
                elif r + 0.3 < d <= r + 1.3 and y < top - 2:
                    a = math.degrees(math.atan2(z - cz, x - cx)) % 45
                    if a < 9 or (top - y) % 9 == 3:
                        bp.set(x, y, z, IRON if (top - y) % 9 != 3 else BRASS)
    for x in range(cx - r - 2, cx + r + 3):
        for z in range(cz - r - 2, cz + r + 3):
            d = math.hypot(x - cx, z - cz)
            if r + 0.3 < d <= r + 1.6:
                fc = "south" if abs(z - cz) >= abs(x - cx) and z < cz else "north" if abs(z - cz) >= abs(x - cx) \
                    else ("east" if x < cx else "west")
                bp.set(x, top - 1, z, stair(SMOKE_STAIRS, fc, "top"))
                bp.set(x, top, z, IRON)
            elif d <= r - 0.8:
                bp.set(x, top - 1, z, "soul_soil")
                bp.set(x, top, z, SOUL_FIRE if hash01(x, z, 802) < 0.8 else SOUL_CAMP)
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            for y in (y0, y0 + 1):
                bp.set(x, y, z, PBB if y == y0 else CHIS)


def conveyor(bp, axis, fixed, a0, a1, y0, y1):
    """A bone conveyor on trestles: a belt of bone blocks 3 wide between iron rails, rollers, the legs down to the
    soul soil; from (a0, y0) to (a1, y1) along ``axis``."""
    n = abs(a1 - a0)
    s = 1 if a1 > a0 else -1
    for i in range(n + 1):
        a = a0 + s * i
        y = round(y0 + (y1 - y0) * i / n)
        for w in (-1, 0, 1):
            x, z = (a, fixed + w) if axis == "x" else (fixed + w, a)
            bp.set(x, y, z, BONE_X if axis == "x" else BONE_Z)
            bp.set(x, y - 1, z, IRON if i % 4 else "polished_basalt[axis=" + ("z" if axis == "x" else "x") + "]")
        for w in (-2, 2):
            x, z = (a, fixed + w) if axis == "x" else (fixed + w, a)
            bp.set(x, y, z, IRON)
            bp.set(x, y + 1, z, IRON_WALL)
        if i % 9 == 4 and y > 8:
            for w in (-2, 2):
                x, z = (a, fixed + w) if axis == "x" else (fixed + w, a)
                for yy in range(5, y - 1):
                    bp.set(x, yy, z, PBBW if yy % 5 else BRASS)
                bp.set(x, 5, z, CHIS)
            for w in (-1, 0, 1):
                x, z = (a, fixed + w) if axis == "x" else (fixed + w, a)
                bp.set(x, y - 2, z, IRON)
        if i % 5 == 2 and hash01(a, fixed, 811) < 0.6:
            x, z = (a, fixed) if axis == "x" else (fixed, a)
            bp.set(x, y + 1, z, SKULL.format(int(hash01(a, fixed, 812) * 16)))


def conveyors(bp):
    # north: from the bone heap at z -96 up to the intake hood on the north face at y 30
    conveyor(bp, "z", -4, -96, BZ0 - 1, 7, 30)
    hood(bp, "north")
    bone_heap(bp, -4, -100, 7)
    # west: from the heap at x -96 to the intake hood on the west face at y 28
    conveyor(bp, "x", 4, -96, BX0 - 1, 7, 28)
    hood(bp, "west")
    bone_heap(bp, -100, 4, 6)


def hood(bp, face):
    """The intake hood where a conveyor enters the engine: an iron box with a barred mouth and a brass lip."""
    if face == "north":
        for x in range(-8, 1):
            for y in range(28, 36):
                for z in range(BZ0 - 4, BZ0):
                    edge = x in (-8, 0) or y in (28, 35) or z == BZ0 - 4
                    if edge:
                        bp.set(x, y, z, BRASS if y == 35 else IRON)
                    else:
                        bp.set(x, y, z, "black_concrete" if y > 31 else IRON)
        for x in range(-6, -1):
            for y in range(31, 35):
                bp.set(x, y, BZ0 - 4, "iron_bars")
    else:
        for z in range(0, 9):
            for y in range(26, 34):
                for x in range(BX0 - 4, BX0):
                    edge = z in (0, 8) or y in (26, 33) or x == BX0 - 4
                    if edge:
                        bp.set(x, y, z, BRASS if y == 33 else IRON)
                    else:
                        bp.set(x, y, z, "black_concrete" if y > 29 else IRON)
        for z in range(2, 7):
            for y in range(29, 33):
                bp.set(BX0 - 4, y, z, "iron_bars")


def bone_heap(bp, cx, cz, h):
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            d = math.hypot(x - cx, z - cz)
            top = int(h - d * 0.8 + vnoise(x, z, 3.0, 821) * 2)
            for y in range(5, 5 + max(0, top)):
                bp.set(x, y, z, BONE if hash3(x, y, z, 822) > 0.35 else ("soul_sand" if y < 7 else BONE_X))
            if top > 0 and hash01(x, z, 823) < 0.07:
                bp.set(x, 5 + top, z, SKULL.format(int(hash01(x, z, 824) * 16)))


def overgrowth_outside(bp):
    """Giant warped fungi against the west and north walls, roots and vines climbing the overgrown patches."""
    for (x, z, h, r, seed) in ((-62, -24, 20, 8, 1), (-60, 26, 15, 6, 2), (-30, -54, 17, 7, 3),
                               (26, -54, 13, 5, 4), (-64, 52, 11, 5, 5)):
        giant_fungus(bp, x, 6, z, h, r, seed=seed + 830, kind="warped")


def roof_details(bp):
    """The engine block's roof: soul-fire vents and parapet pinnacles on the cornice."""
    for x in range(BX0, BX1 + 1, 8):
        for z in (BZ0, BZ1):
            if bp.get(x, BTOP + 1, z) is None:
                bp.set(x, BTOP + 1, z, PBBW)
                bp.set(x, BTOP + 2, z, PBBW)
                bp.set(x, BTOP + 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in range(BZ0 + 8, BZ1, 8):
        for x in (BX0, BX1):
            if bp.get(x, BTOP + 1, z) is None:
                bp.set(x, BTOP + 1, z, PBBW)
                bp.set(x, BTOP + 2, z, PBBW)
                bp.set(x, BTOP + 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the crankcase roof: transverse iron ribs, gilded crenels on the south parapet, two skylight lanterns
    for x in range(UX0 + 2, UX1 - 1, 7):
        for z in range(PZ + 8, UZ1 + 1):
            if bp.get(x, UTOP + 1, z) is None:
                bp.set(x, UTOP + 1, z, IRON if z % 6 else BRASS)
    for x in range(UX0, UX1 + 1):
        if bp.get(x, UTOP + 1, UZ1) is None:
            bp.set(x, UTOP + 1, UZ1, GILD if x % 4 == 0 else PBBW)
    for z in range(PZ + 8, UZ1):
        for x in (UX0, UX1):
            if bp.get(x, UTOP + 1, z) is None:
                bp.set(x, UTOP + 1, z, GILD if z % 4 == 0 else PBBW)
    for cx in (-21, 21):
        for x in range(cx - 3, cx + 4):
            for z in range(4, 11):
                edge = x in (cx - 3, cx + 3) or z in (4, 10)
                bp.set(x, UTOP + 1, z, BRASS if edge else GLASS)
                if edge:
                    bp.set(x, UTOP + 2, z, IRON_WALL if (x + z) % 2 else BRASS)
        bp.set(cx, UTOP + 2, 7, GILD)
        bp.set(cx, UTOP + 3, 7, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # soul-fire vents along the crankcase's south side
    for x in range(-36, 37, 12):
        z = UZ1 + 4
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            bp.set(x + dx, BTOP + 1, z + dz, "soul_soil")
            bp.set(x + dx, BTOP + 2, z + dz, SOUL_FIRE)
        for (dx, dz) in ((-1, -1), (2, -1), (-1, 2), (2, 2)):
            bp.set(x + dx, BTOP + 1, z + dz, IRON)
            bp.set(x + dx, BTOP + 2, z + dz, IRON_WALL)


# ------------------------------------------------------------------ open space and the whole site
def carve_open(bp):
    """Explicit air in the open volumes where nothing is built (the last step: only unset cells), so the natural
    netherrack of the valley cannot fill the approach, the forecourt or the camp."""
    for (x0, x1, y0, y1, z0, z1) in OPEN:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, AIR)


def soul_engine(bp):
    OPEN.clear()
    lab = build_masses()
    air, rid = build_air()
    write_masses(bp, lab, air, rid)
    bone_gate(bp)
    pressure_hall(bp)
    hopper_hall(bp)
    nw_hall(bp)
    bunker(bp)
    soul_furnace(bp)
    mess(bp)
    governor(bp)
    valve_room(bp)
    piston_shaft(bp)
    grace(bp)
    lift(bp)
    arena(bp)
    trench(bp)
    flywheel(bp)
    reliquary(bp)
    piston_gallery(bp)
    ossuary(bp)
    pistons(bp)
    for (cx, cz, top) in ((48, -37, 84), (48, 37, 78), (-48, 37, 74), (0, 34, 86)):
        chimney(bp, cx, cz, BTOP + 1, top)
    roof_details(bp)
    conveyors(bp)
    ground(bp)
    approach(bp)
    camp(bp)
    forecourt(bp)
    overgrowth_outside(bp)
    carve_open(bp)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("pressure_hall", (9, G, 26), (0, 18, 10)),
    ("soul_furnace", (31, G, 36), (42, G + 4, 12)),
    ("piston_gallery", (-37, G, 37), (-37, G + 12, -6)),
    ("governor", (11, L2, -14), (0, L2 + 4, -27)),
    ("ossuary", (-32, OF, -13), (-32, OF + 3, -38)),
    ("charnel_pit", (-10, OF, -25), (15, PF + 3, -25)),
    ("piston_shaft", (-30, L2, -21), (-45, L2 + 9, -35)),
    ("arena", (0, AF, 9), (0, AF + 8, -32)),
]

register(StructureDef(
    "soul_engine", "nether", ["soul_sand_valley", "warped_forest"],
    [Piece("engine", soul_engine, views=VIEWS)],
    spacing=36, separation=12, adaptation="none", height=("absolute", 15), processors="none", max_distance=128,
    ground=G - 1, foundation=False,
    spawns=[(MOB_WSKEL, 6, 1, 2), (MOB_SKEL, 6, 1, 3), (MOB_GRAVE, 3, 1, 1), (MOB_CRAWLER, 3, 1, 2),
            (MOB_HOUND, 2, 1, 1)],
    title_fr="Le Moteur des âmes", title_en="The Soul Engine"))
