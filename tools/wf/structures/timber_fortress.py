"""The Timber Fortress (La Forteresse du bois): a steam-powered logging stronghold on a river bend in the taiga.
Colossal tier (tools/BUILDING.md §1, §12 concept 29, §10 legacy-dungeon template, §15), steampunk accents
(tools/STYLE_STEAMPUNK.md: a brass beam engine on the keep, a steam sawmill with giant saw blades and belts, a
logging locomotive on a stilted trestle, a pump tower feeding the log flume).

Silhouette (one noun phrase, §15.1): a top-heavy timber keep of five jettied floors, each skirted by a slate stave
roof, a brass beam engine and a smokestack on its crown, inside a palisade of whole spruce trunks on a river bend,
a long flume snaking on trestles down from a felled-forest hillside to a water-wheeled sawmill.

Layout, ground y = 0 (feet 1), x east, z south; the keep's axis is (KX, KZ) = (0, -48).
  * the terrain: flat yard ground inside the palisade; a bluff and hillside north of it (rising to ~30, a shelf cut
    at y 15 for the headworks, felled giant spruces, stumps and one standing giant on the crest); the river comes
    down the west side and bends east along the south, the fortress inside the bend;
  * the approach (south-east, outside): the trappers' camp and its waystone, a path west through the spruces along
    the river (the keep's crown shows above the trees, the rest hidden), the covered bridge over the river whose far
    portal frames the gatehouse and the keep (the reveal), the gatehouse (two towers, a closed great gate with a
    3-wide wicket gate, guard rooms);
  * the lumber yard (hub, waystone): log stacks, a gantry crane, sheds; the stilted rail trestle crosses its north;
  * the main route: the steam sawmill (giant saw blades, belts and a line shaft, the water wheel outside) -> its
    gallery -> the rail trestle over the yard (east) -> the charging platform over the charcoal kilns (the logging
    locomotive) -> down to the kiln yard -> the hill gate -> the skid path up the hill -> the headworks shelf
    (sluice house, pump tower, header tank, reservoir) -> the high trestle bridge over the palisade into the keep's
    first floor (the armoury) -> the great hall (antler chandeliers, the dais, the grand stair) -> the map room
    (site of grace) -> the boiler room under the crown -> the stair house -> the mist -> the boss arena on the keep's
    top platform round the beam engine (45 wide, open sky);
  * optional: the mess hall and its kitchen (north-west), the foreman's lodge (south-east, two storeys), the
    sawmill's boiler house, the kilns' insides, the collier's hut, the gatehouse guard rooms, the lift hall;
  * the treasury: the guild strongroom on the keep's top storey, down the north-east stair house behind sealed
    bars;
  * shortcuts (§10.4): ride the log flume (flowing water from the header tank down 140 blocks of trestles into the
    wheel pit), the sawmill's postern (an iron door that opens only from the wheel pit side), the counterweight lift
    (the strongroom's drop well through the keep into the lift hall's pool, whose iron door opens only from inside
    onto the yard); the lift hall's stair also joins the armoury (a loop).
Loot gradient (§15.6): camp and yard tier 1; gatehouse, sawmill, mess hall 1-2; kilns, lodge, headworks 2;
armoury 2; great hall 2-3; map room 3; the strongroom 3-5.
Height budget: the smokestack tops out 96 above the ground layer (taigas lie low enough).
"""
import math

from ..arch import stair
from ..blueprint import is_solid
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, MAHOGANY, PIPES, TABLE,
                       TREAD, VERD, W, fbm, hash01, hash3, vnoise)
from ..nbt import Float
from ..parts import LOOT, MOD
from .cloud_pagoda import Ctx, candle, carpet, hang, slab

# the champion of the keep's crown: the Lumber Jarl (tools/wf/mobs/lumber_jarl.py, entity/boss/LumberJarl.java)
BOSS = "brasshaven:lumber_jarl"
MOB_VINDI = "minecraft:vindicator"
MOB_PILL = "minecraft:pillager"
MOB_MARKS = W + "bandit_marksman"
MOB_MITE = W + "rust_mite"
MOB_DRONE = W + "steam_drone"
MOB_KNIGHT = W + "skeleton_knight"
MOB_AUTO = W + "turbine_automaton"
MOB_GUNNER = W + "boiler_gunner"
MOB_SPIDER = W + "clockwork_spider"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
GRASS = "grass_block[snowy=false]"
PODZOL = "podzol[snowy=false]"
LOG, LOGX, LOGZ = "spruce_log[axis=y]", "spruce_log[axis=x]", "spruce_log[axis=z]"
BARK = "spruce_wood[axis=y]"
STR, STRX, STRZ = "stripped_spruce_log[axis=y]", "stripped_spruce_log[axis=x]", "stripped_spruce_log[axis=z]"
DLOG, DLOGX, DLOGZ = "dark_oak_log[axis=y]", "dark_oak_log[axis=x]", "dark_oak_log[axis=z]"
SP, SP_ST, SP_SL, SP_FENCE = "spruce_planks", "spruce_stairs", "spruce_slab", "spruce_fence"
DO, DO_ST, DO_SL, DO_FENCE = "dark_oak_planks", "dark_oak_stairs", "dark_oak_slab", "dark_oak_fence"
SH, SH_ST, SH_SL = W + "slate_roof_tiles", W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"
COB, MCOB = "cobblestone", "mossy_cobblestone"
SB, MSB, CSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"
SB_ST, SB_SL, SB_WALL = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
PAND = "polished_andesite"
DIB = W + "dark_iron_bricks"
SMK, SSMK = W + "smokestack_bricks", W + "sooty_smokestack_bricks"
BRICK = "bricks"
GILD, BTILE = W + "gilded_trim", W + "brass_tiles"
PARQ = W + "mahogany_parquet"
LEAVES = "spruce_leaves[distance=1,persistent=true,waterlogged=false]"
GLASS = "glass_pane"
AMBER = "orange_stained_glass_pane"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CHAINX, CHAINZ = "iron_chain[axis=x,waterlogged=false]", "iron_chain[axis=z,waterlogged=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# ------------------------------------------------------------------ dimensions
KX, KZ = 0, -48                               # keep axis
# keep storeys: (floor block y, half width, clear height): lift hall, armoury, great hall, map room, boiler room
FLOORS = [(0, 14, 13), (15, 15, 8), (25, 17, 18), (45, 18, 8), (55, 20, 7)]
PLAT, PH = 64, 24                             # crown platform floor block y, half width (past every skirt)
HILL_Z = -78                                  # the hill's foot (it rises north of here)
SHELF = (-14, -112, 28, -86)                  # the headworks shelf (x0, z0, x1, z1), top block y 15
SHELF_Y = 15
ZMIN, ZMAX, XMIN, XMAX = -124, 108, -104, 112
# the palisade: an axis-aligned polygon (clockwise from the north-west corner)
PAL = [(-78, -76), (68, -76), (68, 28), (40, 28), (40, 46), (-56, 46), (-56, 22), (-78, 22)]
SAW = (-78, -40, -46, -10)                    # sawmill walls (x0, z0, x1, z1)
MESS = (-72, -70, -44, -52)
LODGE = (42, 0, 62, 22)
KILN_DECK = (37, -30, 63, -10)                # the charging platform (deck y 9)
TRESTLE_Z = (-16, -12)
DECK_Y = 9
PIT = (-87, -42, -79, -17)                    # the wheel pit (water y -3 .. -1)
RIVER = [(-104, -124), (-98, -90), (-95, -50), (-94, -10), (-90, 25), (-76, 52), (-52, 68), (-20, 74), (10, 72),
         (40, 74), (70, 80), (112, 84)]
RIVER_HW = 7
CAMP = (58, 98)
BUSY = []                                     # rectangles kept free of trees and clutter


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def face_of(dx, dz):
    if abs(dz) >= abs(dx):
        return "south" if dz > 0 else "north"
    return "east" if dx > 0 else "west"


def K(u, v):
    """Keep-local (u east, v south) to blueprint (x, z)."""
    return KX + u, KZ + v


def in_busy(x, z, m=0):
    for (x0, z0, x1, z1) in BUSY:
        if x0 - m <= x <= x1 + m and z0 - m <= z <= z1 + m:
            return True
    return False


def in_pal(x, z):
    """Inside the palisade polygon (ray casting on the axis-aligned outline, edges count as inside)."""
    inside = False
    n = len(PAL)
    for i in range(n):
        (x0, z0), (x1, z1) = PAL[i], PAL[(i + 1) % n]
        if x0 == x1 and min(z0, z1) <= z <= max(z0, z1) and x == x0:
            return True
        if z0 == z1 and min(x0, x1) <= x <= max(x0, x1) and z == z0:
            return True
        if (z0 > z) != (z1 > z):
            xi = x0 + (z - z0) * (x1 - x0) / float(z1 - z0)
            if x < xi:
                inside = not inside
    return inside


def seg_dist(px, pz, a, b):
    (ax, az), (bx, bz) = a, b
    vx, vz = bx - ax, bz - az
    L2 = vx * vx + vz * vz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / L2))
    return math.hypot(px - ax - vx * t, pz - az - vz * t)


def river_d(x, z):
    return min(seg_dist(x, z, RIVER[i], RIVER[i + 1]) for i in range(len(RIVER) - 1))


# ------------------------------------------------------------------ small furniture helpers
def fp(C, x, y, z, spec):
    """Furniture: never on reserved walkway air."""
    if (x, y, z) in C.keep:
        return False
    C.set(x, y, z, spec)
    return True


def hollow(C, x, y, z):
    """Room air: cleared but NOT reserved (furniture may go there later); ``C.clear`` reserves walkway air."""
    C.bp.set(x, y, z, AIR)
    C.keep.discard((x, y, z))


def reserve(C, x0, z0, x1, z1, y, h=3):
    """Keep an aisle free: the air cells of the box (feet y .. y + h - 1) are reserved against furniture."""
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for yy in range(y, y + h):
                if C.free(x, yy, z):
                    C.keep.add((x, yy, z))


# ------------------------------------------------------------------ furnishing and lighting helpers
def stand(C, x, y, z, facing, **gear):
    """An armour stand (arms shown) wearing / holding ``gear`` (slot=item id: head, chest, legs, feet, mainhand,
    offhand), turned to face ``facing``."""
    if not (C.free(x, y, z) and C.free(x, y + 1, z)) or (x, y, z) in C.keep or not backed(C, x, y - 1, z):
        return
    yaw = {"south": 0.0, "west": 90.0, "north": 180.0, "east": -90.0}[facing]
    eq = {slot: {"id": "minecraft:" + item, "count": 1} for slot, item in gear.items()}
    C.set(x, y, z, "dark_oak_pressure_plate[powered=false]")
    C.bp.entity(x, y, z, {"id": "minecraft:armor_stand", "Rotation": [Float(yaw), Float(0.0)], "ShowArms": True,
                          "equipment": eq})
    C.keep.add((x, y, z))       # nothing else in its cell (a lamp may still hang above it)


def backed(C, x, y, z):
    """A full block a banner or a bracket can hang on (not a pane, not a fence)."""
    b = C.get(x, y, z)
    return b is not None and b != AIR and is_solid(b)


def wall_lamp(C, x, y, z, wall):
    """A lantern hung under a dark-oak fence bracket at (x, y + 1, z) against the wall on the ``wall`` side (the
    lantern at y, kept out of the walkway by hanging at least 3 above the floor)."""
    dx, dz = DV[wall]
    if not backed(C, x + dx, y + 1, z + dz) or not C.free(x, y, z) or not C.free(x, y + 1, z):
        return False
    C.set(x, y + 1, z, DO_FENCE)
    C.set(x, y, z, LANT_H)
    return True


def table_candles(C, x, y, z, n=4, color=""):
    if C.free(x, y, z):
        candle(C, x, y, z, n, color)


_LIGHT_PASS = ("air", "water", "glass", "leaves", "spawner", "lantern", "candle", "chain", "chandelier", "lamp",
               "railing", "pipe", "rail", "carpet", "banner", "torch", "campfire")


def _clear_for_light(spec):
    if spec is None:
        return True
    s = spec.split(":")[1]
    if any(t in s for t in _LIGHT_PASS) and not s.endswith("_block") and s != "glass":
        return True
    if s == "glass":
        return True
    return not is_solid(spec)


def _emits(name, props):
    s = name.split(":")[1]
    if "candle" in s and "cake" not in s:
        return 3 * int(props.get("candles", 1)) if props.get("lit") == "true" else 0
    if s in ("furnace", "smoker", "blast_furnace"):
        return 13 if props.get("lit") == "true" else 0
    if s.endswith("campfire"):
        return (10 if s.startswith("soul") else 15) if props.get("lit") == "true" else 0
    if s.startswith("soul_"):
        return 10 if ("lantern" in s or "torch" in s) else 0
    if s in ("lantern", "torch", "wall_torch", "glowstone", "sea_lantern", "shroomlight", "jack_o_lantern", "lava",
             "fire", "beacon", "end_rod") or s.endswith("froglight"):
        return 14 if "torch" in s or s == "end_rod" else 15
    if name.startswith("brasshaven:") and ("lamp" in s or "lantern" in s or "chandelier" in s):
        return 15
    return 0


def light_field(C, box, pad=15):
    """Block light over ``box`` (x0, y0, z0, x1, y1, z1) grown by ``pad``: {pos: level} (MC rules: -1 per step,
    opaque blocks stop it)."""
    x0, y0, z0, x1, y1, z1 = box
    lo = (x0 - pad, y0 - pad, z0 - pad)
    hi = (x1 + pad, y1 + pad, z1 + pad)
    B = C.bp.blocks
    L = {}
    q = []
    for x in range(lo[0], hi[0] + 1):
        for z in range(lo[2], hi[2] + 1):
            for y in range(lo[1], hi[1] + 1):
                b = B.get((x, y, z))
                if b:
                    e = _emits(b[0], b[1])
                    if e:
                        L[(x, y, z)] = e
                        q.append((x, y, z))
    _spread(C, L, q, lo, hi)
    return L, lo, hi


def _spread(C, L, q, lo, hi):
    B = C.bp.blocks
    while q:
        nq = []
        for p in q:
            lv = L[p] - 1
            if lv <= 0:
                continue
            x, y, z = p
            for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)):
                if not (lo[0] <= n[0] <= hi[0] and lo[1] <= n[1] <= hi[1] and lo[2] <= n[2] <= hi[2]):
                    continue
                if L.get(n, 0) >= lv:
                    continue
                b = B.get(n)
                if b is not None and not _clear_for_light(b[0]):
                    continue
                L[n] = lv
                nq.append(n)
        q = nq


def floor_cells(C, box):
    """Standing spots of ``box`` (feet y0 .. y1): two free cells over a solid block."""
    x0, y0, z0, x1, y1, z1 = box
    out = []
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(y0, y1 + 1):
                below = C.get(x, y - 1, z)
                if C.free(x, y, z) and C.free(x, y + 1, z) and below is not None and below != AIR and is_solid(below):
                    out.append((x, y, z))
    return out


def light_fill(C, box, drop=3, target=8, cover=0.92, max_lamps=30, lamp=LANT_H, reach=16, lattice=True):
    """Hang lanterns on iron chains ``drop`` blocks over the floor of ``box`` until ``cover`` of its standing spots
    get block light >= ``target``: each lantern goes over the spot that lights the most dark ones (chained up to the
    first solid block above, within ``reach``), on a 3-block grid while one is left there (rows read as designed).
    Returns (lit share, lanterns hung)."""
    L, lo, hi = light_field(C, box)
    F = floor_cells(C, box)
    if not F:
        return 1.0, 0
    hung = 0
    tried = set()
    while True:
        dark = [p for p in F if L.get(p, 0) < target]
        if len(dark) <= (1 - cover) * len(F) or hung >= max_lamps:
            break
        r = 15 - drop - target          # horizontal reach of a lamp hung ``drop`` over the floor
        dset = {(a, c): b for (a, b, c) in dark}
        ring = [(a, c) for a in range(-r, r + 1) for c in range(-r, r + 1) if abs(a) + abs(c) <= r]
        best = None
        for (x, y, z) in dark:
            if (x, z) in tried or (lattice and ((x - box[0]) % 3 or (z - box[2]) % 3)):
                continue
            ly = y + drop
            if (x, ly, z) in C.keep or not all(C.free(x, yy, z) for yy in range(y, ly + 1)):
                continue
            top = ly + 1
            while top < ly + reach and C.free(x, top, z):
                top += 1
            if not C.solid(x, top, z) or any((x, yy, z) in C.keep for yy in range(ly, top)):
                continue
            gain = sum(1 for (a, c) in ring if dset.get((x + a, z + c), -99) == y)
            key = (gain, -abs(x) - abs(z), x, z)
            if best is None or key > best[0]:
                best = (key, x, ly, z, top)
        if best is None:
            if lattice:
                lattice = False         # nothing left on the 3-block grid: any spot will do
                continue
            break
        _, x, ly, z, top = best
        tried.add((x, z))
        for yy in range(ly + 1, top):
            C.set(x, yy, z, CHAIN)
        C.set(x, ly, z, lamp)
        hung += 1
        L[(x, ly, z)] = 15
        _spread(C, L, [(x, ly, z)], lo, hi)
    lit = sum(1 for p in F if L.get(p, 0) >= target) / len(F)
    return lit, hung


def spawner(C, x, y, z, mob):
    C.keep.discard((x, y, z))
    C.bp.spawner(x, y, z, mob)


def chest(C, x, y, z, facing, table):
    C.keep.discard((x, y, z))
    C.bp.chest(x, y, z, facing, loot=LOOT + table)


def barrel(C, x, y, z):
    C.keep.discard((x, y, z))
    C.bp.barrel(x, y, z)


def waystone(C, x, y, z):
    C.keep.discard((x, y, z))
    C.set(x, y, z, MOD["waystone"])


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{W}brass_railing[facing={facing}]")


def lever_on(C, x, y, z, facing):
    C.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def oneway_door(C, x, y, z, side, wall=DLOG):
    """An iron door at (x, y, z) in a wall; its lever sits on the wall beside the door on the ``side`` face only (the
    only side it opens from)."""
    dx, dz = DV[side]
    C.keep.discard((x, y, z))
    C.keep.discard((x, y + 1, z))
    C.bp.door(x, y, z, side, wood="iron")
    px, pz = (1, 0) if dx == 0 else (0, 1)
    wx, wz = x + px, z + pz
    for yy in (y, y + 1, y + 2):
        C.set(wx, yy, wz, wall)
    C.set(x, y + 2, z, wall)
    C.clear(wx + dx, y + 1, wz + dz)
    C.clear(wx + dx, y, wz + dz)
    lever_on(C, wx + dx, y + 1, wz + dz, side)
    # standing room on both sides
    for s in (1, -1):
        C.clear(x + dx * s, y, z + dz * s)
        C.clear(x + dx * s, y + 1, z + dz * s)


def lamp_post(C, x, y, z, h=3):
    """A spruce post with a lantern on a bracket; feet y."""
    for yy in range(y, y + h):
        C.set(x, yy, z, DO_FENCE)
    C.set(x, y + h, z, DLOG)
    C.set(x, y + h + 1, z, LANT)


def hanging_lamp(C, x, y, z, reach=10):
    hang(C, x, y, z, LANT_H, reach=reach)


def antler_chandelier(C, x, y, z, reach=12):
    """An antler chandelier: a chain from the beam, a stripped log boss, four dark-oak arms with tines, candles on
    the tines and lanterns hung under the arms; y is the arms' level."""
    top = y + 1
    while top < y + reach and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return
    for yy in range(y + 1, top):
        C.set(x, yy, z, CHAIN)
    C.set(x, y, z, STR)
    C.set(x, y - 1, z, LANT_H)
    for dx, dz in N4:
        for k in (1, 2):
            C.set(x + dx * k, y, z + dz * k, DO_FENCE)
        C.set(x + dx * 3, y + 1, z + dz * 3, SP_FENCE)
        C.set(x + dx * 3, y, z + dz * 3, DO_FENCE)
        candle(C, x + dx * 3, y + 2, z + dz * 3, 3, "white")
        C.set(x + dx * 2, y + 1, z + dz * 2, SP_FENCE)
        candle(C, x + dx * 2, y + 2, z + dz * 2, 2, "white")
        C.set(x + dx, y - 1, z + dz, LANT_H)
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        C.set(x + dx, y, z + dz, DO_FENCE)
        C.set(x + dx, y + 1, z + dz, "bone_block[axis=y]")


def stair_run(C, cells0, d, n, fy, spec=SP_ST, support=SP, head=4, rail=None):
    """A straight flight climbing toward ``d``: ``cells0`` is the first tread row (x, z); tread i sits at y fy + 1 + i
    (so the last tread is flush with a floor at fy + n). Headroom is cleared ``head`` above each tread; solid
    support under each tread down to fy + 1. ``rail`` = (dx, dz) side for a fence stringer. Returns the rows."""
    dx, dz = DV[d]
    rows = []
    for i in range(n):
        row = [(x + dx * i, z + dz * i) for (x, z) in cells0]
        t = fy + 1 + i
        for (x, z) in row:
            C.set(x, t, z, stair(spec, d))
            for yy in range(fy + 1, t):
                C.set(x, yy, z, support)
            for yy in range(t + 1, t + head + 1):
                C.clear(x, yy, z)
        if rail:
            rx, rz = rail
            for (x, z) in row:
                if (x + rx, z + rz) in row:
                    continue
                if not C.solid(x + rx, t + 1, z + rz):
                    C.set(x + rx, t, z + rz, support)
                    C.set(x + rx, t + 1, z + rz, SP_FENCE)
                    for yy in range(fy + 1, t):
                        C.set(x + rx, yy, z + rz, support)
        rows.append(row)
    return rows


def well_rail(C, rows, y, arrive, spec=SP_FENCE):
    """Fences round a stairwell opening at floor level y (cells over the rows that lost their floor), leaving the
    arrival side ``arrive`` (dx, dz from the last row) open."""
    hole = set()
    for row in rows:
        for (x, z) in row:
            if C.free(x, y, z):
                hole.add((x, z))
    last = set(rows[-1])
    for (x, z) in hole:
        for dx, dz in N4:
            q = (x + dx, z + dz)
            if q in hole or q in last:
                continue
            if (dx, dz) == arrive:
                continue
            if any(q in row for row in rows):
                continue
            if C.solid(q[0], y, q[1]) and C.free(q[0], y + 1, q[1]):
                C.set(q[0], y + 1, q[1], spec)


def gable(C, x0, z0, x1, z1, y, axis, over=1, st=SH_ST, full=SH, gable_spec=SP, inner=None, ridge=None):
    """A pitched roof: stairs stepping in one per block of rise from an eave ``over`` outside the walls; gable ends
    filled with ``gable_spec``; under the roof inside the walls ``inner`` (None = leave air: rafters show). ``axis``
    is the ridge direction. Returns the ridge y."""
    if axis == "z":
        lo, hi = x0 - over, x1 + over
        a0, a1 = z0 - over, z1 + over
    else:
        lo, hi = z0 - over, z1 + over
        a0, a1 = x0 - over, x1 + over
    top = y
    for b in range(lo, hi + 1):
        k = min(b - lo, hi - b)
        yy = y + k
        top = max(top, yy)
        for a in range(a0, a1 + 1):
            x, z = (b, a) if axis == "z" else (a, b)
            if b - lo == hi - b:
                spec = ridge or full
            elif b - lo < hi - b:
                spec = stair(st, "east" if axis == "z" else "south")
            else:
                spec = stair(st, "west" if axis == "z" else "north")
            C.set(x, yy, z, spec)
            if x0 <= x <= x1 and z0 <= z <= z1:
                end = (a in (z0, z1)) if axis == "z" else (a in (x0, x1))
                for yf in range(y, yy):
                    if end:
                        C.set(x, yf, z, gable_spec)
                    elif inner:
                        C.set(x, yf, z, inner)
            # the eave's underside: upside-down stairs one below the first course
            if k == 0:
                C.put(x, yy - 1, z, stair(DO_ST, "east" if (axis == "z" and b == lo) else
                                          "west" if axis == "z" else ("south" if b == lo else "north"), "top"))
    return top


def frame_wall_spec(u, y, y0, y1, period=4, base=DO):
    """Timber framing: dark oak posts every ``period``, a stripped-spruce mid rail, spruce plank infill, a dark plank
    sill course. ``u`` runs along the wall."""
    if u % period == 0:
        return DLOG
    if y == y0:
        return base
    if y == y1:
        return DO
    if y == (y0 + y1) // 2:
        return STR
    return SP


# ------------------------------------------------------------------ trees
def spruce_tree(C, x, z, y0, h, seed, r0=3.2):
    """A taiga spruce with persistent leaves: a trunk h high from feet y0, conical whorls of leaves."""
    for yy in range(y0, y0 + h):
        C.put(x, yy, z, LOG)
    C.put(x, y0 + h, z, LEAVES)
    C.put(x, y0 + h + 1, z, LEAVES)
    base = y0 + 3
    for yy in range(base, y0 + h + 1):
        t = (yy - base) / float(max(1, y0 + h - base))
        r = r0 * (1.0 - t) + 0.6
        if (yy - base) % 2 == 1:
            r *= 0.6
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if (dx, dz) == (0, 0):
                    continue
                d = math.hypot(dx, dz)
                if d > r + 0.2 or hash3(x + dx, yy, z + dz, seed) < 0.12 * d / max(r, 1):
                    continue
                if C.free(x + dx, yy, z + dz) or C.get(x + dx, yy, z + dz) is None:
                    C.put(x + dx, yy, z + dz, LEAVES)


def giant_spruce(C, x, z, y0, h, seed):
    """A standing giant on the crest: a 2 x 2 trunk with root flares, long drooping whorls."""
    for yy in range(y0 - 2, y0 + h):
        for dx in (0, 1):
            for dz in (0, 1):
                C.set(x + dx, yy, z + dz, LOG)
    for dx, dz in ((-1, 0), (-1, 1), (2, 0), (2, 1), (0, -1), (1, -1), (0, 2), (1, 2)):
        for yy in range(y0 - 2, y0):
            C.set(x + dx, yy, z + dz, BARK)
    for yy in range(y0 + 8, y0 + h + 3):
        t = (yy - y0 - 8) / float(h - 5)
        r = 7.0 * (1.0 - t) + 1.0
        ri = int(math.ceil(r)) + 1
        for dx in range(-ri, ri + 2):
            for dz in range(-ri, ri + 2):
                d = math.hypot(dx - 0.5, dz - 0.5)
                if d > r or (0 <= dx <= 1 and 0 <= dz <= 1 and yy < y0 + h):
                    continue
                C.put(x + dx, yy, z + dz, LEAVES)


def stump(C, x, z, y0, r, h, seed):
    """A felled giant's stump: bark ring, a stripped (ring-grained) cut top, roots spreading on the ground."""
    ri = int(math.ceil(r))
    for dx in range(-ri, ri + 1):
        for dz in range(-ri, ri + 1):
            d = math.hypot(dx, dz)
            if d > r:
                continue
            top = y0 + h - (1 if hash01(x + dx, z + dz, seed) < 0.25 and d > r - 1 else 0)
            for yy in range(y0 - 2, top):
                C.set(x + dx, yy, z + dz, BARK if d > r - 1.2 else STR)
            if d <= r - 1.2:
                C.set(x + dx, top - 1, z + dz, STR if (int(d) % 2 == 0) else "stripped_spruce_wood[axis=y]")
    for k in range(6):
        a = k * math.pi / 3 + hash01(x, z, seed + k) * 0.6
        for s in range(ri, ri + 3):
            px, pz = x + int(round(math.cos(a) * s)), z + int(round(math.sin(a) * s))
            C.set(px, y0 - 1, pz, "spruce_wood[axis=x]" if abs(math.cos(a)) > 0.7 else "spruce_wood[axis=z]")
            if s == ri:
                C.set(px, y0, pz, BARK)


def felled_trunk(C, x0, x1, z, r, ybot, seed):
    """A felled giant lying east-west on the hillside: bark shell, sawn west end showing rings, branch stubs."""
    yc = ybot + r
    ri = int(math.ceil(r))
    for x in range(x0, x1 + 1):
        taper = r * (1.0 - 0.25 * (x - x0) / float(max(1, x1 - x0)))
        for dy in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dy, dz)
                if d > taper:
                    continue
                if x == x0:
                    spec = "stripped_spruce_log[axis=x]" if int(d) % 2 == 0 else "spruce_log[axis=x]"
                elif d > taper - 1.1:
                    spec = LOGX
                else:
                    spec = STRX
                C.set(x, int(round(yc + dy)), z + dz, spec)
        if (x - x0) % 7 == 4 and x < x1 - 2:
            side = 1 if hash01(x, z, seed) < 0.5 else -1
            for k in range(1, 4):
                C.set(x + k // 2, int(yc + r * 0.5 + k * 0.6), z + side * (ri + k - 1), LOGZ)
    # a few chain dogs and a wedge on the cut end
    C.set(x0 - 1, int(yc), z, "iron_chain[axis=x,waterlogged=false]")


# ------------------------------------------------------------------ terrain
def hill_h(x, z):
    """The hillside north of the palisade: a steep bluff in the west (under the headworks), a gentle slope in the
    east (the skid path), rolling up to ~30 at the north edge, falling away toward the river in the west."""
    u = HILL_Z - z
    if u < 0:
        return 0.0
    wb = 9.0 + 17.0 * smooth((x - 26) / 26.0)
    h = 17.0 * smooth(u / wb) + 13.0 * smooth((u - wb) / 28.0)
    h *= smooth((x + 54) / 30.0)
    h += 3.0 * (fbm(x, z, 20.0, 401) - 0.5) * smooth(u / 8.0)
    h *= smooth((z - ZMIN) / 17.0) * smooth((XMAX - x) / 15.0)
    return max(0.0, h)


# the skid path up the hill: (start (x, z), direction, cells, y0, y1); width 5
HILL_PATH = [((46, -77), "north", 8, 0, 3), ((46, -84), "east", 15, 3, 5), ((60, -84), "north", 13, 5, 11),
             ((60, -96), "west", 33, 11, SHELF_Y)]


def hill_path_cells():
    """{(x, z): (y, stair facing or None)} for the skid path."""
    out = {}
    for (sx, sz), d, L, y0, y1 in HILL_PATH:
        dx, dz = DV[d]
        px, pz = (1, 0) if dx == 0 else (0, 1)
        hs = [y0 + int(round((y1 - y0) * max(0.0, min(1.0, (i - 2) / float(L - 5))))) for i in range(L)]
        for i in range(L):
            up = i > 0 and hs[i] > hs[i - 1]
            for o in range(-2, 3):
                c = (sx + dx * i + px * o, sz + dz * i + pz * o)
                if c in out and out[c][0] >= hs[i]:
                    continue
                out[c] = (hs[i], d if up else None)
    return out


def flume_anchors():
    """The flume's centre anchors from the header tank (east) to the wheel pit (south-west); each anchor paints a
    2 x 2 brush (its own cell and the cells one west and one north of it)."""
    pts = []
    for x in range(-3, -41, -1):
        pts.append((x, -99))
    for z in range(-98, -87):
        pts.append((-40, z))
    for x in range(-41, -84, -1):
        pts.append((x, -88))
    for z in range(-87, -41):
        pts.append((-83, z))
    return pts


FLUME_TOP = 27        # water y at the header tank (the deck is y 26)


def flume_cells():
    """{(x, z): (water y, flowing level)} along the flume."""
    out = {}
    for i, (ax, az) in enumerate(flume_anchors()):
        for (bx, bz) in ((ax, az), (ax - 1, az), (ax, az - 1), (ax - 1, az - 1)):
            if (bx, bz) not in out:
                out[(bx, bz)] = (FLUME_TOP - i // 8, i % 8)
    return out


def heightfield(C):
    """Column tops of everything the build lays itself: the yard (0) and a skirt round the palisade, the hill, the
    shelf and the skid path (cut and fill blended into the slope)."""
    top, kind = {}, {}
    for x in range(-86, 77):
        for z in range(-84, 55):
            if in_pal(x, z):
                top[(x, z)], kind[(x, z)] = 0, "yard"
            elif any(in_pal(x + dx, z + dz) for dx, dz in ((5, 0), (-5, 0), (0, 5), (0, -5), (3, 3), (-3, 3),
                                                            (3, -3), (-3, -3))):
                top[(x, z)], kind[(x, z)] = 0, "skirt"
    for x in range(-60, XMAX + 1):
        for z in range(ZMIN, HILL_Z + 1):
            h = hill_h(x, z)
            if h < 0.6:
                continue
            t = int(round(h))
            if (x, z) in top and top[(x, z)] >= t:
                continue
            top[(x, z)], kind[(x, z)] = t, "hill"
    # the shelf (cut and fill)
    x0, z0, x1, z1 = SHELF
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            top[(x, z)], kind[(x, z)] = SHELF_Y, "shelf"
    # the skid path and a blend band round it
    P = hill_path_cells()
    for (x, z), (y, _) in P.items():
        top[(x, z)], kind[(x, z)] = y, "path"
    for (x, z), (y, _) in list(P.items()):
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                q = (x + dx, z + dz)
                if q in P or kind.get(q) not in ("hill",):
                    continue
                d = max(abs(dx), abs(dz))
                t = top[q]
                want = int(round(y + (t - y) * (d - 1) / 4.0)) if d > 1 else y
                if kind.get(q) == "hill":
                    top[q] = want if abs(want - y) < abs(t - y) else t
    # slopes of at most one block between hill columns beyond the bluff (the upper hillside stays walkable)
    def bluff(x, z):
        return HILL_Z - z < 11 and x < 34

    free = [q for q in top if kind[q] == "hill" and not bluff(*q)]
    cone = {}
    for (x, z), (y, _) in P.items():
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                q = (x + dx, z + dz)
                if kind.get(q) == "hill" and not bluff(*q):
                    d = max(abs(dx), abs(dz))
                    lo, hi = cone.get(q, (-99, 99))
                    cone[q] = (max(lo, y - d), min(hi, y + d))
    for _ in range(6):
        for q, (lo, hi) in cone.items():
            top[q] = max(lo, min(hi, top[q]))
        for _ in range(30):
            changed = False
            for (x, z) in free:
                t = top[(x, z)]
                for dx, dz in N4:
                    n = (x + dx, z + dz)
                    if kind.get(n) in ("hill", "path") and not bluff(*n) and top[n] + 1 < t:
                        t = top[n] + 1
                if t < top[(x, z)]:
                    top[(x, z)] = t
                    changed = True
            if not changed:
                break
    for q, (lo, hi) in cone.items():
        top[q] = max(lo, min(hi, top[q]))
    # the flume never rests in the ground
    for (x, z), (y, _) in flume_cells().items():
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                q = (x + dx, z + dz)
                if q in top and kind[q] == "hill" and top[q] > y - 3:
                    top[q] = y - 3
    C.top, C.kind = top, kind
    return top


def rock(x, y, z):
    j = int((hash01(x // 4, z // 4, 411) - 0.5) * 3)
    band = (y + j) % 6
    h = hash3(x, y, z, 412)
    if band in (0, 1):
        return "andesite" if h < 0.8 else "stone"
    if band == 3:
        return "tuff" if h < 0.6 else "cobblestone"
    return "stone" if h < 0.8 else ("mossy_cobblestone" if h < 0.9 else "cobblestone")


def yard_floor(x, z):
    h = hash01(x, z, 421)
    v = vnoise(x, z, 7.0, 422)
    if v > 0.62:
        return "packed_mud" if h < 0.7 else "mud_bricks"
    if v < 0.3:
        return "gravel" if h < 0.7 else "dirt_path"
    return "dirt_path" if h < 0.6 else ("gravel" if h < 0.85 else "coarse_dirt")


def write_terrain(C):
    top, kind = C.top, C.kind
    P = hill_path_cells()
    sx0, sz0, sx1, sz1 = SHELF
    for (x, z), t in top.items():
        k = kind[(x, z)]
        nb = [top.get((x + dx, z + dz)) for dx, dz in N4]
        edge = any(n is None for n in nb)
        steep = max([abs(t - n) for n in nb if n is not None] or [0])
        y_lo = -5 if edge else -2
        for y in range(y_lo, t + 1):
            if k in ("yard", "skirt") or y < 0:
                spec = "dirt" if y >= -2 else "stone"
            elif y >= t - 2 and steep < 3:
                spec = "dirt"
            else:
                spec = rock(x, y, z)
            C.set(x, y, z, spec)
        # surface
        if k == "yard":
            spec = yard_floor(x, z)
        elif k == "skirt":
            h = hash01(x, z, 431)
            spec = GRASS if h < 0.6 else (PODZOL if h < 0.85 else "coarse_dirt")
        elif k == "shelf":
            spec = "gravel" if hash01(x, z, 432) < 0.5 else "packed_mud"
        elif k == "path":
            y, up = P[(x, z)]
            spec = stair(SP_ST, up) if up else ("dirt_path" if hash01(x, z, 433) < 0.7 else "gravel")
        else:
            if steep >= 3:
                spec = rock(x, t, z)
            else:
                h = hash01(x, z, 434)
                spec = GRASS if h < 0.55 else (PODZOL if h < 0.85 else ("coarse_dirt" if h < 0.95 else
                                                                            "mossy_cobblestone"))
        C.set(x, t, z, spec)
        # crib walls of logs where the hill stands above the shelf or the path
        if k == "hill":
            for dx, dz in N4:
                q = (x + dx, z + dz)
                if kind.get(q) in ("shelf", "path") and t > top[q]:
                    for y in range(top[q] + 1, t + 1):
                        C.set(x, y, z, LOGX if (y + x) % 2 else LOGZ)
        # clear a little air over our own ground (terrain bumps vanish)
        for y in range(t + 1, t + 3):
            if C.get(x, y, z) is None:
                C.bp.set(x, y, z, AIR)
    # the path's edges: log kerbs on the downhill side, lamp posts every 10
    for (sx, sz), d, L, y0, y1 in HILL_PATH:
        dx, dz = DV[d]
        px, pz = (1, 0) if dx == 0 else (0, 1)
        for i in range(0, L, 9):
            for o in (-3, 3):
                x, z = sx + dx * i + px * o, sz + dz * i + pz * o
                t = top.get((x, z))
                if t is not None and (x, z) not in P and abs(t - P[(sx + dx * i, sz + dz * i)][0]) <= 1:
                    lamp_post(C, x, t + 1, z, 2)


def river(C):
    """The river: a channel 3 deep (water y -3 .. -1), gravel and clay bed, sand and mud banks, air cut above."""
    for x in range(XMIN - 4, XMAX + 1):
        for z in range(ZMIN, ZMAX + 1):
            d = river_d(x, z)
            if d > RIVER_HW + 3.5:
                continue
            h = hash01(x, z, 441)
            if d <= RIVER_HW:
                C.set(x, -4, z, "gravel" if h < 0.5 else ("clay" if h < 0.8 else "sand"))
                for y in range(-3, 0):
                    C.water(x, y, z)
                for y in range(0, 3):
                    C.bp.set(x, y, z, AIR)
                if h < 0.03:
                    C.set(x, -3, z, "seagrass")
            else:
                for y in range(-5, -1):
                    C.set(x, y, z, "dirt" if y > -4 else "stone")
                if d <= RIVER_HW + 1.5:
                    C.set(x, -1, z, "sand" if h < 0.4 else ("mud" if h < 0.7 else "gravel"))
                    for y in range(0, 4):
                        C.bp.set(x, y, z, AIR)
                else:
                    C.set(x, -1, z, "dirt")
                    C.set(x, 0, z, GRASS if h < 0.7 else "coarse_dirt")
                    for y in range(1, 4):
                        if C.get(x, y, z) is None:
                            C.bp.set(x, y, z, AIR)


# ------------------------------------------------------------------ the palisade
TOWERS = [(-78, -76), (-40, -76), (10, -76), (30, -76), (68, -76), (68, -24), (68, 28), (40, 28), (40, 46),
          (-36, 46), (-56, 46), (-56, 22), (-78, 22), (-78, -58)]
HILL_GATE = (43, 49)                          # x range of the hill gate in the north wall


def palisade_skip(x, z):
    x0, z0, x1, z1 = SAW
    if x0 <= x <= x1 and z0 <= z <= z1:
        return True
    if -16 <= x <= 16 and 38 <= z <= 54:       # the gatehouse
        return True
    if HILL_GATE[0] <= x <= HILL_GATE[1] and -77 <= z <= -74:
        return True
    return False


def palisade(C):
    """Two rows of whole spruce trunks: the outer row 10-12 high, sharpened; the inner row 7 high; raking braces
    inside every 8; iron bands; timber towers at the corners and along the long walls."""
    n = len(PAL)
    for i in range(n):
        (x0, z0), (x1, z1) = PAL[i], PAL[(i + 1) % n]
        dx = (x1 > x0) - (x1 < x0)
        dz = (z1 > z0) - (z1 < z0)
        ix, iz = -dz, dx                        # inward (right of travel on the clockwise outline)
        L = max(abs(x1 - x0), abs(z1 - z0))
        for k in range(L + 1):
            x, z = x0 + dx * k, z0 + dz * k
            if palisade_skip(x, z):
                continue
            h = 10 + int(hash01(x, z, 501) * 3)
            for y in range(0, h + 1):
                C.set(x, y, z, LOG if not (y in (3, 8) and k % 2 == 0) else STR)
            C.set(x, h + 1, z, SP_FENCE)
            # iron bands on the outer face
            for y in (3, 8):
                C.put(x - ix, y, z - iz, "iron_chain[axis=x,waterlogged=false]" if dz == 0 else
                      "iron_chain[axis=z,waterlogged=false]") if hash01(x, z, 502) < 0.0 else None
            qx, qz = x + ix, z + iz
            if not palisade_skip(qx, qz) and in_pal(qx, qz):
                for y in range(0, 8):
                    C.set(qx, y, qz, LOG)
                C.set(qx, 8, qz, DLOGX if dz == 0 else DLOGZ)
            if k % 8 == 4 and 2 < k < L - 2:
                bx, bz = x + ix * 2, z + iz * 2
                if in_pal(bx, bz) and not in_busy(bx, bz) and not palisade_skip(bx, bz):
                    for y in range(1, 5):
                        C.set(bx, y, bz, STR)
                    C.set(bx, 5, bz, stair(SP_ST, face_of(-ix, -iz), "top"))
                    C.set(bx + ix, 1, bz + iz, stair(SP_ST, face_of(-ix, -iz)))
    for (tx, tz) in TOWERS:
        wall_tower(C, tx, tz)


def wall_tower(C, cx, cz):
    """A timber wall tower: a battered stone foot, a log-framed shaft, a jettied fighting top with arrow slits, a
    steep slate pyramid roof with a brass finial."""
    if -16 <= cx <= 16 and 38 <= cz <= 54:
        return
    r, top = 3, 15
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            edge = max(abs(x - cx), abs(z - cz)) == r
            for y in range(-2, top + 1):
                if y <= 2:
                    C.set(x, y, z, COB if hash3(x, y, z, 511) < 0.6 else (MCOB if y <= 0 else SB))
                elif edge:
                    corner = abs(x - cx) == r and abs(z - cz) == r
                    u = (x - cx) if abs(z - cz) == r else (z - cz)
                    C.set(x, y, z, DLOG if corner or u == 0 else (STR if y in (8, top) else SP))
                else:
                    C.set(x, y, z, SP)
            if abs(x - cx) < r and abs(z - cz) < r:
                C.set(x, top, z, SP)
    # jettied top storey
    R = r + 1
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            m = max(abs(x - cx), abs(z - cz))
            if m == R:
                C.set(x, top, z, DLOGX if abs(z - cz) == R else DLOGZ)
                C.set(x, top - 1, z, stair(DO_ST, face_of(x - cx, z - cz) if abs(x - cx) != abs(z - cz)
                                           else ("north" if z < cz else "south"), "top"))
                for y in range(top + 1, top + 5):
                    corner = abs(x - cx) == R and abs(z - cz) == R
                    C.set(x, y, z, DLOG if corner else (STR if y == top + 4 else SP))
            elif m < R:
                for y in range(top, top + 5):
                    C.set(x, y, z, SP)
    # pyramid roof
    for k in range(0, R + 3):
        rr = R + 1 - k
        y = top + 5 + k
        if rr < 0:
            break
        for x in range(cx - rr, cx + rr + 1):
            for z in range(cz - rr, cz + rr + 1):
                if max(abs(x - cx), abs(z - cz)) != rr:
                    continue
                if rr == 0:
                    C.set(x, y, z, SH)
                    continue
                if abs(x - cx) == abs(z - cz):
                    C.set(x, y, z, SH)
                else:
                    C.set(x, y, z, stair(SH_ST, OPP[face_of(x - cx, z - cz)]))
        if rr == 0:
            C.set(cx, y + 1, cz, GILD)
            C.set(cx, y + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            break
        # fill the roof underneath (no sealed void)
        for x in range(cx - rr + 1, cx + rr):
            for z in range(cz - rr + 1, cz + rr):
                C.set(x, y, z, SP)


# ------------------------------------------------------------------ the gatehouse
def gatehouse(C):
    """Two stone-footed timber towers astride a 13-wide passage; the great gate (outer face) stays shut, a 3-wide
    wicket gate in it; the portcullis hangs raised behind; a guard room in each tower."""
    z0, z1 = 40, 52
    for side in (-1, 1):
        xa, xb = (-15, -7) if side < 0 else (7, 15)
        for x in range(xa, xb + 1):
            for z in range(z0, z1 + 1):
                edge = x in (xa, xb) or z in (z0, z1)
                for y in range(-2, 25):
                    if y <= 0:
                        C.set(x, y, z, SB if not edge else COB)
                    elif y <= 4 and edge:
                        C.set(x, y, z, COB if hash3(x, y, z, 521) < 0.5 else (MCOB if y <= 2 else SB))
                    elif edge:
                        u = (z - z0) if x in (xa, xb) else (x - xa)
                        corner = x in (xa, xb) and z in (z0, z1)
                        spec = DLOG if corner or u % 4 == 0 else (STR if y in (12, 24) else SP)
                        if not corner and u % 4 == 2 and y in (9, 10, 17, 18):
                            spec = DO_FENCE                      # arrow slits
                        C.set(x, y, z, spec)
                    elif y <= 6:
                        C.clear(x, y, z)
                    elif y == 7:
                        C.set(x, y, z, DO)
                    else:
                        C.set(x, y, z, SP)
        # the jettied top and a stave roof
        cx, cz = (xa + xb) // 2, (z0 + z1) // 2
        for x in range(xa - 1, xb + 2):
            for z in range(z0 - 1, z1 + 2):
                if x in (xa - 1, xb + 1) or z in (z0 - 1, z1 + 1):
                    C.set(x, 24, z, DLOGX if z in (z0 - 1, z1 + 1) else DLOGZ)
                    C.set(x, 23, z, stair(DO_ST, face_of(x - cx, z - cz), "top"))
                    for y in range(25, 29):
                        corner = x in (xa - 1, xb + 1) and z in (z0 - 1, z1 + 1)
                        C.set(x, y, z, DLOG if corner else (DO_FENCE if y in (26, 27) and (x + z) % 3 == 0 else SP))
                else:
                    for y in range(24, 29):
                        C.set(x, y, z, SP)
        gable(C, xa - 1, z0 - 1, xb + 1, z1 + 1, 29, "z", over=1, inner=SP)
        # guard room door (into the passage) and furniture
        dxw = xb if side < 0 else xa
        for z in (45, 46):
            for y in (1, 2, 3):
                C.clear(dxw, y, z)
            C.set(dxw, 4, z, DLOGZ)
        ix0, ix1 = xa + 1, xb - 1
        hang(C, (ix0 + ix1) // 2, 5, 46, LANT_H, reach=3)
        for z in (42, 44):
            C.bp.bed(ix0 if side < 0 else ix1, 1, z, "west" if side > 0 else "east", "brown")
        fp(C, (ix0 + ix1) // 2, 1, 49, TABLE)
        fp(C, (ix0 + ix1) // 2 - 1, 1, 49, f"{W}mahogany_chair[facing=east]")
        barrel(C, ix0 if side > 0 else ix1, 1, 50)
        fp(C, ix0 if side > 0 else ix1, 1, 42, "grindstone[face=floor,facing=north]")
        chest(C, ix1 if side > 0 else ix0, 1, 50, "north", "tf_gate")
        spawner(C, (ix0 + ix1) // 2, 1, 42, MOB_PILL if side < 0 else MOB_VINDI)
    # the passage
    for x in range(-6, 7):
        for z in range(z0, z1 + 1):
            C.set(x, 0, z, SB if hash01(x, z, 531) < 0.7 else PAND)
            C.set(x, -1, z, "stone")
            for y in range(1, 11):
                C.clear(x, y, z)
            C.set(x, 11, z, DLOGZ if x % 3 == 0 else DO)
            for y in range(12, 19):
                C.set(x, y, z, SP if z in (z0, z1) else DO)
    gable(C, -6, z0, 6, z1, 19, "x", over=0, inner=SP)
    # great gate on the outer face, the wicket gate in it
    for x in range(-6, 7):
        for y in range(1, 11):
            wick = -1 <= x <= 1 and y <= 4
            if wick:
                continue
            spec = DLOG if x in (-6, -2, 2, 6) else (DLOGX if y in (3, 8) else SP)
            C.set(x, y, z1, spec)
    for x in (-1, 0, 1):
        C.set(x, 5, z1, GILD if x == 0 else DLOGX)
    # portcullis, raised, behind the inner arch
    for x in range(-6, 7):
        for y in (9, 10):
            C.set(x, y, z0 + 1, "iron_bars")
    for x in (-6, 6):
        for y in range(1, 9):
            C.set(x, y, z0 + 1, DLOG)
    for z in (43, 47):
        hang(C, -3, 9, z, LANT_H, reach=3)
        hang(C, 3, 9, z, LANT_H, reach=3)


# ------------------------------------------------------------------ the covered bridge over the river
def river_bridge(C):
    """A covered timber bridge (7-wide walkway) on two stone piers; its far portal frames the gatehouse and the keep."""
    za, zb = 57, 87
    for z in range(za - 1, zb + 2):
        for x in range(-4, 5):
            abut = z <= 61 or z >= 83
            if abut:
                for y in range(-5, 1):
                    C.set(x, y, z, SB if hash3(x, y, z, 541) < 0.7 else MSB)
            if z in (za - 1, zb + 1):
                if -3 <= x <= 3:
                    C.set(x, 1, z, slab(SP_SL))
                    for y in (2, 3, 4):
                        C.clear(x, y, z)
                continue
            C.set(x, 1, z, SP if -3 <= x <= 3 else DLOGZ)
            if not abut and z % 3 == 0:
                C.set(x, 0, z, DLOGX)
            if x in (-4, 4):
                post = z % 3 == 0 or z in (za, zb)
                for y in range(2, 6):
                    if post:
                        C.set(x, y, z, DLOG)
                    elif y == 2:
                        C.set(x, y, z, SP)
                    elif y in (3, 4):
                        C.set(x, y, z, SP_FENCE if z % 3 != 1 else SP)
                    else:
                        C.set(x, y, z, STRZ)
            else:
                for y in range(2, 6):
                    C.clear(x, y, z)
    for z in (66, 67, 68, 76, 77, 78):
        for x in range(-4, 5):
            for y in range(-6, 1):
                C.set(x, y, z, SB if hash3(x, y, z, 542) < 0.75 else MSB)
    gable(C, -4, za, 4, zb, 6, "z", over=1, inner=None, gable_spec=SP)
    for z in (za, zb):
        for x in range(-3, 4):
            C.set(x, 6, z, DLOGX)
        C.set(0, 6, z, GILD)
    for z in range(za + 3, zb, 6):
        hang(C, 0, 5, z, LANT_H, reach=6)
    # the portal openings: clear the gable ends over the walkway
    for z in (za, zb):
        for x in range(-3, 4):
            for y in range(2, 6):
                C.clear(x, y, z)


# ------------------------------------------------------------------ the approach and the trappers' camp
def path(C, pts, hw=2.0):
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    for x in range(int(min(xs) - hw - 1), int(max(xs) + hw + 2)):
        for z in range(int(min(zs) - hw - 1), int(max(zs) + hw + 2)):
            d = min(seg_dist(x, z, pts[i], pts[i + 1]) for i in range(len(pts) - 1))
            if d > hw:
                continue
            h = hash01(x, z, 551)
            spec = "dirt_path" if (d < hw - 0.7 and h < 0.8) else ("gravel" if h < 0.6 else "coarse_dirt")
            C.set(x, 0, z, spec)
            C.set(x, -1, z, "dirt")
            C.set(x, -2, z, "dirt")
            for y in (1, 2, 3):
                if C.free(x, y, z):
                    C.clear(x, y, z)


def approach(C):
    path(C, [(CAMP[0] - 6, 97), (10, 97), (2, 93), (0, 89)])
    path(C, [(0, 55), (0, 53)], 3.0)
    for (x, z) in ((40, 99), (24, 99), (12, 95), (-3, 91), (3, 91)):
        if C.get(x, 0, z) is not None:
            lamp_post(C, x, 1, z, 2)
    BUSY.append((-8, 86, 12, 100))


def tent(C, cx, cz, length=5, color="white_wool"):
    """An A-frame canvas tent along x: wool slopes on a spruce ridge pole, open at the east end."""
    for x in range(cx, cx + length):
        for dz in range(-2, 3):
            y = 3 - abs(dz)
            if abs(dz) == 2:
                C.set(x, 1, cz + dz, color)
            C.set(x, y, cz + dz, color if dz != 0 else STRX)
    for x in (cx, cx + length - 1):
        C.set(x, 4, cz, SP_FENCE)
    for dz in (-1, 0, 1):
        C.set(cx, 1, cz + dz, color)
        C.set(cx, 2, cz + dz, color if dz != 0 else STRX)
    for x in range(cx + 1, cx + length):
        for dz in (-1, 0, 1):
            C.clear(x, 1, cz + dz)
        C.clear(x, 2, cz)
    C.set(cx + 1, 1, cz - 1, "brown_carpet")
    C.set(cx + 1, 1, cz + 1, "brown_carpet")


def camp(C):
    """The trappers' camp: a clearing by the river with two tents, a fire ring, hide racks, a canoe, the waystone."""
    cx, cz = CAMP
    BUSY.append((cx - 11, cz - 9, cx + 11, cz + 9))
    for x in range(cx - 10, cx + 11):
        for z in range(cz - 8, cz + 9):
            if (x - cx) ** 2 / 110.0 + (z - cz) ** 2 / 70.0 > 1.0:
                continue
            h = hash01(x, z, 561)
            C.set(x, 0, z, "coarse_dirt" if h < 0.4 else (PODZOL if h < 0.7 else ("gravel" if h < 0.85 else
                                                                                  "dirt_path")))
            for y in (-1, -2):
                C.set(x, y, z, "dirt")
            for y in range(1, 6):
                if C.free(x, y, z):
                    C.clear(x, y, z)
    waystone(C, cx, 1, cz)
    C.set(cx, 0, cz, "polished_andesite")
    for dx, dz in N4:
        C.set(cx + dx, 0, cz + dz, SB)
    # fire ring with log benches
    fx, fz = cx - 5, cz + 1
    C.set(fx, 1, fz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        C.set(fx + dx, 0, fz + dz, COB)
    for x in range(fx - 1, fx + 2):
        C.set(x, 1, fz + 3, STRX)
        C.set(x, 1, fz - 3, STRX)
    tent(C, cx - 9, cz - 5)
    tent(C, cx + 3, cz - 5, 5, "brown_wool")
    # hide racks: fence frames with stretched pelts
    for (hx, hz) in ((cx + 5, cz + 4), (cx + 8, cz + 4)):
        for y in (1, 2, 3):
            C.set(hx, y, hz, SP_FENCE)
            C.set(hx + 2, y, hz, SP_FENCE)
        C.set(hx + 1, 3, hz, SP_FENCE)
        C.set(hx + 1, 2, hz, "brown_wool" if hx == cx + 5 else "white_wool")
    # stores, the canoe on the bank, a woodpile
    chest(C, cx - 7, 1, cz - 3, "south", "tf_camp")
    chest(C, cx + 6, 1, cz - 3, "south", "tf_camp")
    barrel(C, cx + 7, 1, cz - 2)
    barrel(C, cx - 8, 1, cz + 3)
    fp(C, cx - 9, 1, cz + 3, "smoker[facing=east,lit=false]")
    for x in range(cx + 1, cx + 5):
        for y in (1, 2):
            C.set(x, y, cz + 7, LOGX)
    C.set(cx + 2, 3, cz + 7, LOGX)
    C.set(cx + 3, 3, cz + 7, LOGX)
    for (lx, lz) in ((cx - 2, cz - 7), (cx + 9, cz)):
        lamp_post(C, lx, 1, lz, 2)
    canoe(C, 34, 87)


def canoe(C, x0, z):
    """A dugout canoe drawn up on the bank (east-west)."""
    for x in range(x0, x0 + 7):
        end = x in (x0, x0 + 6)
        C.set(x, 0, z, "dirt")
        C.set(x, 1, z, stair(SP_ST, "east" if x == x0 else "west") if end else SP_SL + "[type=bottom,waterlogged=false]")
        if not end:
            C.set(x, 1, z - 1, stair(SP_ST, "south"))
            C.set(x, 1, z + 1, stair(SP_ST, "north"))


def approach_trees(C):
    """Spruces along the river and round the camp: the fortress hides behind them until the bridge."""
    placed = []
    for i in range(400):
        x = int(XMIN + hash01(i, 1, 571) * (XMAX - XMIN))
        z = int(60 + hash01(i, 2, 572) * (ZMAX - 62))
        if river_d(x, z) < RIVER_HW + 4 or in_busy(x, z, 3):
            continue
        if in_pal(x, z) or any(math.hypot(x - px, z - pz) < 6 for (px, pz) in placed):
            continue
        if C.get(x, 1, z) not in (None, AIR) or C.get(x, 0, z) in ("minecraft:dirt_path", "minecraft:gravel"):
            continue
        if seg_dist(x, z, (CAMP[0] - 6, 97), (10, 97)) < 4 or seg_dist(x, z, (2, 93), (0, 89)) < 4:
            continue
        placed.append((x, z))
        for y in (-2, -1):
            C.set(x, y, z, "dirt")
        C.set(x, 0, z, PODZOL)
        spruce_tree(C, x, z, 1, 9 + int(hash01(x, z, 573) * 7), 574 + i)
        if len(placed) >= 30:
            break


# ------------------------------------------------------------------ the steam sawmill
def saw_blade(C, cx, cz, yc, r=5):
    """A giant circular saw in the x-y plane, half sunk in a slot in the floor: an iron disc with notched teeth, a
    dark-iron hub ring and a brass boss."""
    for dx in range(-r - 1, r + 2):
        for dy in range(-r - 1, r + 2):
            d = math.hypot(dx, dy)
            if d > r + 0.5:
                continue
            y = yc + dy
            if y < -3:
                continue
            if d > r - 0.5:
                a = math.atan2(dy, dx)
                if int((a + math.pi) / (2 * math.pi) * 28) % 2:
                    continue
                spec = "iron_block"
            elif d < 1.0:
                spec = GILD
            elif d < 2.0:
                spec = IRON
            else:
                spec = "iron_block"
            C.set(cx + dx, y, cz, spec)
    for dz in (-1, 1):
        C.set(cx, yc, cz + dz, IRON)
        for y in range(1, yc):
            C.set(cx, y, cz + dz, IRON)


def sawmill(C):
    """The steam sawmill: a 33 x 31 timber hall on a stone sill, a gallery round all four walls, two giant saws on
    the log line, belts from the line shaft, the water wheel outside the west wall, a boiler house with two
    smokestacks north."""
    x0, z0, x1, z1 = SAW
    H = 17
    BUSY.append((x0, z0 - 8, x1, z1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, (SP if hash01(x, z, 601) < 0.6 else "stripped_spruce_wood[axis=y]") if not edge else SB)
            C.set(x, -1, z, "stone")
            for y in range(1, H):
                if edge:
                    u = (z - z0) if x in (x0, x1) else (x - x0)
                    corner = x in (x0, x1) and z in (z0, z1)
                    if y <= 2:
                        spec = COB if hash3(x, y, z, 602) < 0.6 else SB
                    elif corner or u % 5 == 0:
                        spec = DLOG
                    elif y in (9, H - 1):
                        spec = DLOGX if z in (z0, z1) else DLOGZ
                    elif u % 5 in (2, 3) and y in (5, 6, 7, 12, 13, 14):
                        spec = AMBER
                    else:
                        spec = SP
                    C.set(x, y, z, spec)
                else:
                    hollow(C, x, y, z)
    # roof (ridge along x) with a monitor of glass at the ridge
    ridge = gable(C, x0, z0, x1, z1, H, "x", over=2, gable_spec=SP)
    for x in range(x0 + 3, x1 - 2):
        for z in (-26, -24):
            C.set(x, ridge - 2, z, AMBER) if x % 3 else None
    # tie beams across the hall (rafters show above)
    for x in range(x0 + 5, x1, 5):
        for z in range(z0 + 1, z1):
            C.set(x, H, z, DLOGZ)
    # the gallery round the walls (floor y 9, 3 wide) on posts and brackets
    G = DECK_Y
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            ring = min(x - x0, x1 - x, z - z0, z1 - z)
            if ring <= 3:
                C.set(x, G, z, SP)
                for y in range(G + 1, G + 4):
                    C.clear(x, y, z)
                hollow(C, x, G + 4, z)
                if ring == 3:
                    if (x + z) % 5 == 0:
                        for y in range(1, G):
                            C.set(x, y, z, DLOG)
                    C.set(x, G + 1, z, SP_FENCE)
                    C.set(x, G - 1, z, stair(DO_ST, face_of(x - (x0 + x1) // 2, z - (z0 + z1) // 2), "top")) \
                        if (x + z) % 5 != 0 else None
    # the stair up to the gallery (west side, north-going) and its landing to the west gallery
    rows = stair_run(C, [(-72, -14), (-71, -14), (-70, -14)], "north", G, 0)
    for x in range(-74, -69):
        for z in range(-26, -22):
            C.set(x, G, z, SP)
            for y in range(G + 1, G + 5):
                C.clear(x, y, z)
    for x in range(-74, -69):
        C.set(x, G + 1, -27, SP_FENCE)
    for z in range(-27, -22):
        C.set(-69, G + 1, z, SP_FENCE)
    for x in (-74, -73):
        C.set(x, G + 1, -22, SP_FENCE)
    # the log line (z -25): rollers, the haul-up from the pit through the west wall, two saws, aisles
    for x in range(x0 + 1, x1 - 2):
        if x in (-61, -60, -59, -48):
            continue
        C.set(x, 1, -26, "dark_oak_slab[type=bottom,waterlogged=false]")
        C.set(x, 1, -24, "dark_oak_slab[type=bottom,waterlogged=false]")
        C.set(x, 1, -25, "rail[shape=east_west,waterlogged=false]")
    for x in range(-76, -70):
        C.set(x, 2, -25, LOGX)
    for x in range(-56, -50):
        C.set(x, 2, -25, STRX)
    saw_blade(C, -66, -25, 1)
    saw_blade(C, -54, -25, 1)
    C.clear(-54, 1, -26)
    # line shaft at y 15 along x, pulleys over the saws, belts down to the arbors
    for x in range(x0 + 1, x1):
        C.set(x, 15, -25, STRX)
    for sx in (-66, -54):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dy or dz:
                    C.set(sx, 15 + dy, -25 + dz, IRON if abs(dy) + abs(dz) == 1 else BRASS)
        for y in range(2, 15):
            C.set(sx, y, -23, "black_wool")
        C.set(sx, 1, -23, GEAR)
    # the wheel's axle through the west wall into a gear
    for x in range(x0 - 2, x0 + 2):
        C.set(x, 6, -25, IRON)
    C.set(x0 + 2, 6, -25, GEAR)
    for y in (7, 8):
        C.set(x0 + 2, y, -25, STR)
    # aisles: the main doors -> the stair to the gallery and across the log line to the boiler house
    reserve(C, -64, -24, -60, -11, 1)
    reserve(C, -73, -13, -60, -11, 1)
    reserve(C, -60, -39, -60, -24, 1)
    reserve(C, -64, -39, -60, -27, 1)
    # the log carriage on the infeed: a plated bogie on the rail, the log dogged down with iron clamps
    for x in range(-77, -71):
        C.set(x, 1, -25, TREAD)
    for x in (-76, -73):
        for z in (-26, -24):
            C.set(x, 2, z, "iron_bars")
    C.set(-77, 2, -25, IRON)
    C.set(-77, 3, -25, "lever[face=floor,facing=east,powered=false]")
    # guard rails round the blades (brass railings on the rollers' outer side), the yellow-striped walk lines
    for (sx, d) in ((-66, 5), (-54, 5)):
        for x in range(sx - d, sx + d + 1):
            for z, fc in ((-27, "north"), (-23, "south")):
                if C.free(x, 1, z) and (x, 1, z) not in C.keep:
                    railing(C, x, 1, z, fc)
    for x in range(x0 + 1, x1):
        for z in (-28, -22):
            if C.free(x, 1, z) and (x, 1, z) not in C.keep:
                C.set(x, 1, z, "yellow_carpet" if x % 2 else "black_carpet")
    # lumber piles, sawdust heaps by the blades, the planer, the sharpening bench
    for (px, pz) in ((-66, -16), (-56, -16), (-56, -35), (-70, -35)):
        for x in range(px, px + 5):
            for z in range(pz, pz + 3):
                for y in range(1, 2 + int(hash01(x, z, 603) * 2)):
                    C.set(x, y, z, SP_SL + "[type=bottom,waterlogged=false]" if y == 3 else SP)
    for (cx, cz) in ((-66, -30), (-54, -30), (-69, -20), (-51, -20)):
        for dx in range(-2, 3):
            for dz in range(-1, 2):
                x, z = cx + dx, cz + dz
                if not C.free(x, 1, z) or (x, 1, z) in C.keep:
                    continue
                r = abs(dx) + abs(dz)
                if r <= 1:
                    C.set(x, 1, z, "brown_concrete_powder")
                    if r == 0:
                        C.set(x, 2, z, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
                elif r <= 2:
                    C.set(x, 1, z, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
                else:
                    C.set(x, 1, z, "brown_carpet")
    for x in (-52, -51):
        fp(C, x, 1, -31, IRON)
        fp(C, x, 2, -31, TREAD)
    fp(C, -53, 2, -31, GAUGE)
    fp(C, -50, 1, -31, "grindstone[face=floor,facing=east]")
    fp(C, -50, 1, -33, "smithing_table")
    for z in (-38, -37):
        fp(C, -76, 1, z, "barrel[facing=up,open=false]")
    # the saw doctor's bench: spare blades (iron trapdoors) on the wall, files, a lamp
    for z in range(-34, -29):
        fp(C, -47, 1, z, SP_SL + "[type=top,waterlogged=false]")
        fp(C, -47, 2, z, "iron_trapdoor[facing=west,half=top,open=true,powered=false,waterlogged=false]" if z % 2
           else "air")
    fp(C, -47, 2, -32, LANT)
    chest(C, -76, 1, -36, "east", "tf_sawmill")
    chest(C, -48, G + 1, -12, "north", "tf_sawmill")
    spawner(C, -52, 1, -36, MOB_VINDI)
    spawner(C, -64, 1, -20, MOB_MITE)
    # lanterns on brackets on the wall posts, for the floor (y 4) and the gallery (y 13)
    for u in range(5, 31, 5):
        for (x, z, wall) in ((x0 + 1, z0 + u, "west"), (x1 - 1, z0 + u, "east"), (x0 + u, z0 + 1, "north"),
                             (x0 + u, z1 - 1, "south")):
            if z0 < z < z1 and x0 < x < x1:
                wall_lamp(C, x, 4, z, wall)
                wall_lamp(C, x, G + 4, z, wall)
    # lamps low on chains from the tie beams, over the saws' working ends
    for (lx, lz) in ((-68, -31), (-58, -31), (-68, -19), (-58, -19), (-53, -27), (-73, -27)):
        hang(C, lx, 4, lz, LANT_H, reach=14)
    # doors: the main doors south (into the yard), the gallery door east (onto the trestle), the boiler house north
    for x in range(-64, -59):
        for y in range(1, 6):
            C.clear(x, y, z1)
        C.set(x, 6, z1, DLOGX)
        C.set(x, 0, z1, SB)
    for z in range(-15, -12):
        for y in range(G + 1, G + 5):
            C.clear(x1, y, z)
        C.set(x1, G, z, SP)
        C.set(x1, G + 5, z, DLOGZ)
    for x in (-63, -62):
        for y in (1, 2, 3):
            C.clear(x, y, z0)
    # the postern: an iron door in the west wall that opens only from the wheel pit side
    oneway_door(C, x0, 1, -14, "west", wall=DLOG)
    boiler_house(C)


def boiler_house(C):
    """North annex of the sawmill: a brick boiler house with a fire-tube boiler and two smokestacks."""
    x0, z0, x1, z1 = -70, -49, -55, -40
    for x in range(x0, x1 + 1):
        for z in range(z0, z1):
            edge = x in (x0, x1) or z == z0
            C.set(x, 0, z, BRICK if edge else "smooth_stone")
            for y in range(1, 9):
                if edge:
                    C.set(x, y, z, BRICK if hash3(x, y, z, 611) < 0.8 else SMK)
                else:
                    hollow(C, x, y, z)
            C.set(x, 9, z, BRICK if edge else SP)
    gable(C, x0, z0, x1, z1 - 1, 10, "x", over=1, gable_spec=BRICK, inner=SP)
    # the boiler: a horizontal copper drum along x
    for x in range(-67, -58):
        for dy in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dy) + abs(dz) == 2:
                    continue
                C.set(x, 3 + dy, -45 + dz, COPPER if x % 3 else BRASS)
        for dz in (-1, 0, 1):
            for y in (1, 2, 5, 6, 7, 8):
                C.set(x, y, -45 + dz, BRICK)
    for x in (-67, -59):
        for y in (1, 2):
            C.set(x, y, -45, IRON)
    C.set(-66, 1, -43, "furnace[facing=south,lit=true]")
    C.set(-64, 1, -43, "furnace[facing=south,lit=true]")
    C.set(-62, 5, -45, GAUGE)
    for x in (-57, -56):
        C.set(x, 1, -42, "coal_block")
        C.set(x, 2, -42, "coal_block") if x == -57 else None
    hang(C, -62, 7, -42, LANT_H, reach=3)
    for sx in (-67, -59):
        smokestack(C, sx, -47, 0, 40)


def smokestack(C, cx, cz, y0, y1, r=1):
    """A square brick smokestack (outer 3 x 3) with a sooty crown and a corbelled cap."""
    for y in range(y0, y1 + 1):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                crown = y > y1 - 4
                if abs(dx) < r and abs(dz) < r:
                    C.set(cx + dx, y, cz + dz, AIR if y > y1 - 2 else SMK)
                    continue
                C.set(cx + dx, y, cz + dz, SSMK if crown else (SMK if hash3(cx + dx, y, cz + dz, 621) < 0.8
                                                               else BRICK))
    for dx in range(-r - 1, r + 2):
        for dz in range(-r - 1, r + 2):
            if max(abs(dx), abs(dz)) == r + 1:
                C.set(cx + dx, y1 - 3, cz + dz, SSMK)
                C.set(cx + dx, y1 - 2, cz + dz, W + "sooty_smokestack_brick_slab[type=bottom,waterlogged=false]")
    C.set(cx, y1 - 1, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


def wheel_pit(C):
    """The wheel pit outside the sawmill's west wall: water 3 deep fed by the flume's fall and drained to the river,
    the overshot water wheel (r 7) on its axle, a boardwalk landing by the postern with steps out of the water."""
    x0, z0, x1, z1 = PIT
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1,) and river_d(x, z) <= RIVER_HW + 1:
                continue
            edge = x == x0 - 1 or z == z0 - 1 or z == z1 + 1 or x == x1 + 1
            C.set(x, -4, z, SB)
            if edge:
                for y in range(-3, 1):
                    C.set(x, y, z, SB if y < 0 else (MSB if hash01(x, z, 631) < 0.4 else SB))
            else:
                for y in range(-3, 0):
                    C.water(x, y, z)
                for y in range(0, 4):
                    C.clear(x, y, z)
    # tailrace into the river
    for z in range(-28, -22):
        for x in range(x0 - 4, x0):
            if river_d(x, z) <= RIVER_HW:
                continue
            C.set(x, -4, z, SB)
            for y in range(-3, 0):
                C.water(x, y, z)
            for y in range(0, 3):
                C.clear(x, y, z)
    # the landing (boardwalk at y 0) with steps out of the pit
    for x in range(x0, x1 + 1):
        for z in range(z1 + 1, z1 + 6):
            C.set(x, 0, z, SP)
            C.set(x, -1, z, "stone")
            for y in range(1, 5):
                C.clear(x, y, z)
        C.set(x, -1, z1, stair(SP_ST, "south"))
        C.clear(x, 0, z1)
    for x in (x0, x1 + 0):
        for z in range(z1 + 1, z1 + 6, 2):
            C.set(x, 1, z, SP_FENCE) if x == x0 else None
    lamp_post(C, x0, 1, z1 + 5, 2)
    # the water wheel: disc in the y-z plane, two rims, spokes, paddles; centre (y 6, z -25)
    yc, zc, R = 6, -25, 7
    for x in (-81, -80):
        for dy in range(-R - 1, R + 2):
            for dz in range(-R - 1, R + 2):
                d = math.hypot(dy, dz)
                y, z = yc + dy, zc + dz
                if R - 0.6 <= d <= R + 0.4:
                    C.set(x, y, z, DO)
                elif d < 1.2:
                    C.set(x, y, z, BRASS)
                elif d < R - 0.6:
                    a = math.atan2(dy, dz)
                    k = (a / (math.pi / 4)) % 1.0
                    if k < 0.18 or k > 0.82:
                        C.set(x, y, z, STRX if x == -81 else DLOGX)
    for k in range(16):
        a = k * math.pi / 8
        y, z = yc + int(round(math.sin(a) * (R + 1))), zc + int(round(math.cos(a) * (R + 1)))
        if y >= -3:
            C.set(-81, y, z, SP)
            C.set(-80, y, z, SP)
    for x in range(-82, -77):
        C.set(x, yc, zc, IRON)
    # bearing posts in the pit
    for z in (zc - 2, zc + 2):
        for y in range(-3, yc):
            C.set(-82, y, z, DLOG) if z == zc - 2 else None


# ------------------------------------------------------------------ the rail trestle and the logging locomotive
def trestle(C):
    """The stilted rail line: a 5-wide deck at y 9 from the sawmill gallery east across the yard to the kilns'
    charging platform; bents every 6 with cross braces, fenced walkways either side of the rails."""
    za, zb = TRESTLE_Z
    xa, xb = SAW[2] + 1, KILN_DECK[0] - 1
    for x in range(xa, xb + 1):
        for z in range(za, zb + 1):
            C.set(x, DECK_Y, z, SP if z in (za, zb) else (DO if z != -14 else SP))
            for y in range(DECK_Y + 1, DECK_Y + 5):
                C.clear(x, y, z)
            if z in (za, zb):
                C.set(x, DECK_Y + 1, z, SP_FENCE)
            if (x - xa) % 6 == 0 and z in (za, zb):
                for y in range(0, DECK_Y):
                    C.set(x, y, z, LOG)
                C.set(x, -1, z, COB)
        C.set(x, DECK_Y + 1, -14, "rail[shape=east_west,waterlogged=false]")
        if (x - xa) % 6 == 0:
            for z in range(za, zb + 1):
                C.set(x, DECK_Y - 1, z, DLOGZ)
                C.set(x, 4, z, STRZ)
        if (x - xa) % 6 == 3:
            for z in (za, zb):
                C.set(x, DECK_Y - 1, z, stair(DO_ST, "east", "top"))
    for x in range(xa + 3, xb, 12):
        C.set(x, DECK_Y + 1, za, DLOG)
        C.set(x, DECK_Y + 2, za, LANT)
    # gaps in the fence at the two ends
    for z in range(za + 1, zb):
        C.clear(xa, DECK_Y + 1, z) if z != -14 else None


def locomotive(C, x0, z):
    """A geared logging locomotive heading west on the rails: smokebox and balloon stack, a copper-banded boiler on
    a dark-iron frame, a timber cab, a tender stacked with cordwood; it stands on the charging platform."""
    y = DECK_Y + 1
    # frame and wheels
    for x in range(x0, x0 + 17):
        C.set(x, y, z, "rail[shape=east_west,waterlogged=false]")
        for dz in (-1, 1):
            C.set(x, y, z + dz, IRON if x % 3 else GEAR)
        C.set(x, y + 1, z, IRON)
    # boiler (x0 .. x0 + 7), smokebox, stack
    for x in range(x0, x0 + 8):
        for dy in range(0, 3):
            for dz in (-1, 0, 1):
                if dy in (0, 2) and dz != 0 and x != x0:
                    continue
                C.set(x, y + 2 + dy, z + dz, (DIB if x <= x0 + 1 else (BRASS if x % 3 == 0 else COPPER)))
    C.set(x0 - 1, y + 2, z, "iron_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    C.set(x0 - 1, y + 3, z, EDISON)
    for yy in range(y + 5, y + 8):
        C.set(x0 + 1, yy, z, DIB)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            C.set(x0 + 1 + dx, y + 8, z + dz, DIB if (dx or dz) else AIR)
    C.set(x0 + 4, y + 5, z, BRASS)
    C.set(x0 + 6, y + 5, z, "bell[attachment=floor,facing=east,powered=false]")
    # cab
    for x in range(x0 + 8, x0 + 12):
        for dz in (-1, 0, 1):
            for yy in range(y + 2, y + 6):
                side = dz != 0
                if yy == y + 5:
                    C.set(x, yy, z + dz, DO)
                elif side and x in (x0 + 8, x0 + 11):
                    C.set(x, yy, z + dz, DLOG)
                elif side and yy == y + 2:
                    C.set(x, yy, z + dz, SP)
                elif x == x0 + 8 and dz == 0:
                    C.set(x, yy, z + dz, DIB)
                else:
                    C.set(x, yy, z + dz, AIR if (not side or dz < 0) else GLASS)
    C.set(x0 + 9, y + 2, z, GAUGE)
    C.set(x0 + 10, y + 2, z, f"{W}valve_wheel[facing=west]")
    chest(C, x0 + 10, DECK_Y + 1, z - 3, "south", "tf_yard")
    for x in range(x0 + 8, x0 + 12):
        C.set(x, y + 6, z - 1, stair(DO_ST, "south"))
        C.set(x, y + 6, z + 1, stair(DO_ST, "north"))
        C.set(x, y + 6, z, DO_SL + "[type=bottom,waterlogged=false]")
    # tender with cordwood
    for x in range(x0 + 12, x0 + 17):
        for dz in (-1, 0, 1):
            C.set(x, y + 2, z + dz, SP)
            C.set(x, y + 3, z + dz, LOGX if dz == 0 or x % 2 else LOGX)
            if dz == 0:
                C.set(x, y + 4, z + dz, LOGX)


# ------------------------------------------------------------------ the charcoal kilns and their charging platform
def kiln(C, cx, cz, r=4.5):
    """A beehive charcoal kiln: a brick dome, an arched door south, a charging hole on top under a chute."""
    ri = int(math.ceil(r))
    for dx in range(-ri, ri + 1):
        for dz in range(-ri, ri + 1):
            for dy in range(0, ri + 2):
                d = math.sqrt(dx * dx + dz * dz + (dy * 0.85) ** 2)
                if d > r:
                    continue
                x, y, z = cx + dx, dy, cz + dz
                if dy == 0:
                    C.set(x, 0, z, BRICK)
                elif d > r - 1.1:
                    C.set(x, y, z, BRICK if hash3(x, y, z, 641) < 0.8 else SSMK)
                else:
                    C.clear(x, y, z)
    for dz in range(2, ri + 1):
        for y in (1, 2):
            C.clear(cx, y, cz + dz)
    C.set(cx, 0, cz + ri, BRICK)
    C.set(cx, 1, cz - 1, "coal_block")
    C.set(cx + 1, 1, cz - 1, "coal_block")
    C.set(cx - 1, 1, cz, "coal_block")
    # chute up to the deck
    for y in range(int(r / 0.85) + 1, DECK_Y):
        C.set(cx, y, cz, COPPER if y < DECK_Y - 1 else BRASS)


def kilns(C):
    """Three beehive kilns under the charging platform (deck y 9) where the trestle ends; the locomotive stands on
    it; a stair down north to the kiln yard; charcoal heaps and cordwood ricks; the collier's hut."""
    x0, z0, x1, z1 = KILN_DECK
    BUSY.append((x0, z0 - 12, x1, z1 + 2))
    for (kx, kz) in ((43, -21), (51, -21), (59, -21)):
        kiln(C, kx, kz)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, DECK_Y, z, SP if (x + z) % 7 else DO)
            for y in range(DECK_Y + 1, DECK_Y + 5):
                C.clear(x, y, z)
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                C.set(x, DECK_Y + 1, z, SP_FENCE)
            if x % 6 == 1 and z in (z0, z1):
                if not C.solid(x, 2, z):
                    for y in range(0, DECK_Y):
                        C.set(x, y, z, LOG)
        if x % 6 == 4:
            for z in range(z0, z1 + 1):
                C.put(x, DECK_Y - 1, z, DLOGZ)
    # the trestle arrives on the west edge
    for z in range(TRESTLE_Z[0] + 1, TRESTLE_Z[1]):
        C.clear(x0, DECK_Y + 1, z)
    for x in range(x0, x0 + 17):
        C.set(x, DECK_Y + 1, -14, "rail[shape=east_west,waterlogged=false]")
    locomotive(C, x0 + 4, -14)
    # charging chutes' hatches on the deck
    for (kx, kz) in ((43, -21), (51, -21), (59, -21)):
        C.set(kx, DECK_Y, kz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for (bx, bz) in ((40, -27), (47, -27), (56, -27)):
        for x in range(bx, bx + 4):
            C.set(x, DECK_Y + 1, bz, LOGX)
            C.set(x, DECK_Y + 2, bz, LOGX) if x < bx + 3 else None
    barrel(C, 61, DECK_Y + 1, -28)
    barrel(C, 62, DECK_Y + 1, -28)
    for (lx, lz) in ((x0, z0), (x1, z0), (x1, z1)):
        C.set(lx, DECK_Y + 1, lz, DLOG)
        C.set(lx, DECK_Y + 2, lz, LANT)
    # stair down north to the kiln yard (rows z -39 .. -31 climb south)
    rows = stair_run(C, [(52, -39), (53, -39), (54, -39)], "south", DECK_Y, 0)
    for (x, z) in [(51, z) for z in range(-39, -30)] + [(55, z) for z in range(-39, -30)]:
        t = DECK_Y - (-31 - z)
        if t >= 1:
            C.set(x, t + 1, z, SP_FENCE)
            for y in range(1, t + 1):
                C.set(x, y, z, SP)
    for x in (52, 53, 54):
        C.clear(x, DECK_Y + 1, z0)
    # the kiln yard: charcoal heaps, cordwood ricks, the collier's hut
    for (hx, hz, hr) in ((58, -50, 3.5), (49, -60, 3.0)):
        heap(C, hx, hz, hr)
    for (rx, rz, L) in ((38, -46, 8), (38, -52, 8), (38, -66, 5)):
        for x in range(rx, rx + L):
            for y in (1, 2):
                C.set(x, y, rz, LOGX if True else LOGZ)
            C.set(x, 3, rz, LOGX) if x % 2 else None
        C.set(rx - 1, 1, rz, SP_FENCE)
        C.set(rx + L, 1, rz, SP_FENCE)
    collier_hut(C, 54, -70)
    spawner(C, 63, 1, -56, MOB_PILL)
    lamp_post(C, 50, 1, -44, 3)
    lamp_post(C, 42, 1, -70, 3)


def heap(C, cx, cz, r):
    """A charcoal clamp: a turf-capped mound with a smoking vent."""
    ri = int(math.ceil(r))
    for dx in range(-ri, ri + 1):
        for dz in range(-ri, ri + 1):
            d = math.hypot(dx, dz)
            if d > r:
                continue
            h = int(round((r - d) * 0.8)) + 1
            for y in range(1, h + 1):
                C.set(cx + dx, y, cz + dz, "coal_block" if y < h else ("gravel" if hash01(cx + dx, cz + dz, 651) < 0.5
                                                                     else "mud"))
    hmax = int(round(r * 0.8)) + 1
    C.set(cx, hmax + 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def collier_hut(C, x0, z0):
    """A one-room log hut by the north wall: bunk, stove, a chest of the colliers' takings."""
    x1, z1 = x0 + 8, z0 + 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, SP)
            for y in range(1, 5):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    C.set(x, y, z, LOG if corner else (LOGX if z in (z0, z1) else LOGZ))
                else:
                    C.clear(x, y, z)
    gable(C, x0, z0, x1, z1, 5, "x", over=1, gable_spec=SP, inner=None)
    for y in (1, 2):
        C.clear(x0 + 4, y, z1)
    C.set(x0 + 2, 2, z1, GLASS)
    C.set(x0 + 6, 2, z1, GLASS)
    C.bp.bed(x0 + 1, 1, z0 + 1, "east", "brown")
    fp(C, x0 + 7, 1, z0 + 1, "furnace[facing=south,lit=true]")
    chest(C, x0 + 7, 1, z0 + 3, "west", "tf_kilns")
    barrel(C, x0 + 1, 1, z0 + 4)
    hang(C, x0 + 4, 4, z0 + 3, LANT_H, reach=3)


# ------------------------------------------------------------------ the mess hall
def mess_hall(C):
    """The loggers' mess hall: a long timber hall with a kitchen at its west end (ranges, smokers, the copper stew
    kettle, hams hung from the beams), three long tables with benches, a hearth on the north wall."""
    x0, z0, x1, z1 = MESS
    H = 8
    BUSY.append((x0, z0, x1, z1 + 2))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, (SP if x > -63 else "polished_andesite") if not edge else COB)
            for y in range(1, H + 1):
                if edge:
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    spec = frame_wall_spec(u, y, 1, H, 4)
                    if y in (3, 4, 5) and u % 4 == 2:
                        spec = AMBER
                    C.set(x, y, z, spec)
                else:
                    hollow(C, x, y, z)
    for x in range(x0 + 1, x1):
        if (x - x0) % 4 == 0:
            for z in range(z0 + 1, z1):
                C.set(x, H, z, DLOGZ)
    gable(C, x0, z0, x1, z1, H + 1, "x", over=2, gable_spec=SP, inner=None)
    # doors: south (to the yard) and east
    for x in (-59, -58, -57):
        for y in (1, 2, 3):
            C.clear(x, y, z1)
    for z in (-62, -61, -60):
        for y in (1, 2, 3):
            C.clear(x1, y, z)
    # aisles: the south door along the hall, the east door down the east end, the kitchen's edge
    reserve(C, x0 + 2, z1 - 2, x1 - 1, z1 - 1, 1)
    reserve(C, x1 - 2, z0 + 1, x1 - 1, z1 - 1, 1)
    reserve(C, -64, z0 + 2, -63, z1 - 1, 1)
    # kitchen (west end): ranges, smokers, kettle, counters
    for z in range(z0 + 1, z1):
        if z % 2:
            fp(C, x0 + 1, 1, z, "smoker[facing=east,lit=true]")
        else:
            fp(C, x0 + 1, 1, z, "furnace[facing=east,lit=true]")
    for x in range(x0 + 1, x0 + 7):
        fp(C, x, 1, z0 + 1, SP_SL + "[type=top,waterlogged=false]" if x % 2 else "barrel[facing=up,open=false]")
    for z in range(z0 + 4, z1 - 3):
        fp(C, x0 + 7, 1, z, SP_SL + "[type=top,waterlogged=false]")
    kx, kz = x0 + 4, (z0 + z1) // 2
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            fp(C, kx + dx, 1, kz + dz, COPPER if (dx or dz) else "water_cauldron[level=3]")
    for (hx, hz) in ((x0 + 3, z0 + 3), (x0 + 5, z0 + 3), (x0 + 3, z1 - 3)):
        for y in (H - 1, H - 2):
            C.set(hx, y, hz, CHAIN if y == H - 1 else "brown_terracotta")
    # three long tables with benches, bread, cake and candles
    for tz in (-66, -61, -56):
        for x in range(x0 + 10, x1 - 2):
            fp(C, x, 1, tz, DO_SL + "[type=top,waterlogged=false]")
            fp(C, x, 1, tz - 1, stair(SP_ST, "north")) if x % 4 else None
            fp(C, x, 1, tz + 1, stair(SP_ST, "south")) if x % 4 else None
            if x % 3 == 0:
                candle(C, x, 2, tz, 3)
            elif x % 7 == 1:
                C.set(x, 2, tz, "cake[bites=2]")
            elif x % 5 == 2:
                C.set(x, 2, tz, "flower_pot")
    # hearth on the north wall
    hx = -52
    for x in range(hx - 2, hx + 3):
        for y in range(1, 6):
            C.set(x, y, z0, COB if hash3(x, y, z0, 701) < 0.6 else SB)
        C.set(x, 1, z0 - 1, COB)
    C.set(hx, 1, z0 + 1, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    for dx in (-1, 1):
        C.set(hx + dx, 1, z0 + 1, SB)
        C.set(hx + dx, 2, z0 + 1, LANT)
    for y in range(1, H + 8):
        C.set(hx, y, z0 - 1, COB if y > 1 else COB)
    for y in range(H + 1, H + 9):
        for dx in (-1, 0, 1):
            C.set(hx + dx, y, z0 - 1, COB)
    # the pantry: casks and crates stacked in the north-east corner and along the south wall of the kitchen
    for (bx, bz, hgt) in ((-46, -69, 2), (-47, -69, 1), (-46, -68, 1), (-70, -53, 1), (-69, -53, 2),
                          (-68, -53, 1), (-67, -53, 2)):
        for y in range(1, hgt + 1):
            fp(C, bx, y, bz, "barrel[facing=up,open=false]" if (bx + y) % 2 else "barrel[facing=south,open=false]")
    for (x, z) in ((-66, -53), (-46, -67)):
        fp(C, x, 1, z, "hay_block[axis=y]")
    fp(C, -66, 2, -53, LANT)
    fp(C, -65, 1, -67, "water_cauldron[level=3]")
    fp(C, -65, 1, -55, "composter[level=4]")
    for x in range(x0 + 2, x0 + 7):
        if C.solid(x, 1, z0 + 1):
            fp(C, x, 2, z0 + 1, LANT if x % 3 == 0 else ("flower_pot" if x % 3 == 1 else "air"))
    # lamps: low over the tables (from the tie beams), over the counters, by the doors
    for lx in (-60, -56, -52, -48):
        for lz in (-66, -61, -56):
            hang(C, lx, 4, lz, LANT_H, reach=5)
    for (lx, lz) in ((-68, -65), (-68, -57)):
        hang(C, lx, 5, lz, LANT_H, reach=4)
    chest(C, x0 + 1, 1, z1 - 1, "east", "tf_mess")
    chest(C, x1 - 1, 1, z0 + 1, "west", "tf_mess")
    spawner(C, -50, 1, -64, MOB_VINDI)


# ------------------------------------------------------------------ the foreman's lodge
def lodge(C):
    """The foreman's lodge: a two-storey log house with a stone chimney and a porch on the yard side: the office
    and the trophy parlour below, the foreman's bedroom and the strong chest above."""
    x0, z0, x1, z1 = LODGE
    F1 = 6
    BUSY.append((x0 - 4, z0 - 1, x1 + 1, z1 + 1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, COB if edge else PARQ)
            for y in range(1, 12):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    if y == F1:
                        spec = DLOGX if z in (z0, z1) else DLOGZ
                    else:
                        spec = LOG if corner else (LOGX if z in (z0, z1) else LOGZ)
                    if not corner and y in (2, 3, 8, 9) and ((x - x0) % 5 == 2 if z in (z0, z1) else (z - z0) % 5 == 2):
                        spec = GLASS
                    C.set(x, y, z, spec)
                elif y == F1:
                    C.set(x, y, z, SP if (x - x0) % 4 else DLOGZ)
                else:
                    hollow(C, x, y, z)
    gable(C, x0, z0, x1, z1, 12, "x", over=2, gable_spec=SP, inner=None)
    # interior partition at x 52 (office west | parlour east) with a doorway
    for z in range(z0 + 1, z1):
        for y in range(1, F1):
            if z in (10, 11, 12) and y <= 3:
                continue
            C.set(52, y, z, SP)
    # the door onto the porch (west) and the porch
    for z in (10, 11, 12):
        for y in (1, 2, 3):
            C.clear(x0, y, z)
    for x in range(x0 - 4, x0):
        for z in range(z0 + 3, z1 - 2):
            C.set(x, 0, z, SP)
            for y in range(1, 5):
                C.clear(x, y, z)
            if x == x0 - 4 and z in (z0 + 3, z1 - 3):
                for y in range(1, 5):
                    C.set(x, y, z, DLOG)
        for z in range(z0 + 2, z1 - 1):
            C.set(x, 5, z, stair(SH_ST, "east")) if x == x0 - 4 else C.set(x, 5, z, SH_SL + "[type=bottom,waterlogged=false]")
    # the stone chimney on the east wall
    for y in range(-1, 16):
        for z in (10, 11, 12):
            C.set(x1 + 1, y, z, COB if hash3(x1 + 1, y, z, 711) < 0.6 else SB)
    C.set(x1, 1, 11, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    C.set(x1, 2, 11, COB)
    # aisles: porch door -> office -> parlour -> the stair foot; the stair's arrival upstairs
    reserve(C, x0 + 1, 10, 53, 12, 1)
    reserve(C, 53, 12, 57, z1 - 1, 1)
    reserve(C, 53, 12, 57, 14, F1 + 1)
    # office: the foreman's desk (ledgers, inkwell candle, the day book on a lectern), the map board, ledger
    # shelves, the dark-iron safe round the strong chest, a coat stand
    for x in (45, 46, 47):
        fp(C, x, 1, 4, TABLE)
    fp(C, 46, 1, 5, f"{W}mahogany_chair[facing=north]")
    fp(C, 45, 2, 4, "candle[candles=3,lit=true,waterlogged=false]")
    fp(C, 47, 2, 4, "chiseled_bookshelf[facing=south]")
    fp(C, 44, 1, 2, "lectern[facing=east,has_book=false,powered=false]")
    fp(C, 49, 1, 1, "cartography_table")
    fp(C, 50, 1, 1, "loom[facing=south]")
    for x in range(44, 49):
        fp(C, x, 1, 1, "chiseled_bookshelf[facing=south]" if x % 2 else "bookshelf")
        fp(C, x, 2, 1, "bookshelf" if x % 2 else "chiseled_bookshelf[facing=south]")
    for z in range(z0 + 1, z0 + 6):
        fp(C, 51, 1, z, "bookshelf")
        fp(C, 51, 2, z, "chiseled_bookshelf[facing=west]" if z % 2 else "bookshelf")
    chest(C, 43, 1, 20, "east", "tf_lodge")
    for (y, z) in ((1, 19), (1, 21), (2, 19), (2, 21), (3, 19), (3, 20), (3, 21)):
        C.set(43, y, z, IRON)
    C.set(43, 2, 20, "iron_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
    C.set(44, 2, 19, GAUGE)
    stand(C, 43, 1, 8, "east", head="leather_helmet", chest="leather_chestplate")
    for (x, z) in ((44, 15), (45, 15)):
        fp(C, x, 1, z, f"{W}mahogany_chair[facing=south]")
    fp(C, 44, 1, 16, TABLE)
    fp(C, 45, 1, 16, TABLE)
    fp(C, 44, 2, 16, LANT)
    fp(C, 51, 1, 18, "barrel[facing=up,open=false]")
    fp(C, 51, 1, 19, "barrel[facing=up,open=false]")
    fp(C, 51, 2, 19, "barrel[facing=up,open=false]")
    hang(C, 47, 4, 6, HANG_LAMP, reach=2)
    hang(C, 47, 4, 16, HANG_LAMP, reach=2)
    # parlour: the fireplace with its mantel, armchairs, the bear rug, antler trophies round the walls, the rifle
    # rack
    C.set(x1, 1, 11, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    C.set(x1, 2, 11, COB)
    for z in (10, 12):
        for y in (1, 2):
            C.set(x1 - 1, y, z, SB)
    for z in (10, 11, 12):
        C.set(x1 - 1, 3, z, stair(SB_ST, "west", "top"))
    for z in (10, 12):
        candle(C, x1 - 1, 4, z, 3)
    for (ax, az, fc) in ((58, 9, "east"), (58, 13, "east")):
        fp(C, ax, 1, az, f"{W}mahogany_chair[facing={fc}]")
    for x in (59, 60):
        for z in (10, 11, 12):
            C.set(x, 1, z, "brown_carpet")
    for z in (8, 14):
        fp(C, 58, 1, z, TABLE)
        fp(C, 58, 2, z, LANT)

    def antlers(x, y, z, axis_x):
        """A stag's antlers on a wall: a bone skull, two branching dark-oak tines."""
        C.set(x, y, z, "bone_block[axis=y]")
        for d in (-1, 1):
            X, Z = (x + d, z) if axis_x else (x, z + d)
            C.set(X, y + 1, Z, SP_FENCE)
            X2, Z2 = (x + 2 * d, z) if axis_x else (x, z + 2 * d)
            C.set(X2, y + 2, Z2, SP_FENCE)
            C.set(X, y + 2, Z, SP_FENCE)

    for z in (3, 18):
        antlers(x1 - 1, 3, z, False)
    antlers(57, 3, z0 + 1, True)
    for x in range(58, 62):
        fp(C, x, 1, z1 - 1, DO_FENCE if x % 2 else "barrel[facing=up,open=false]")
        fp(C, x, 2, z1 - 1, "iron_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]"
           if x % 2 == 0 else DO_FENCE)
    wall_lamp(C, 60, 4, 1, "north")
    wall_lamp(C, 60, 4, z1 - 1, "south")
    hang(C, 57, 4, 11, LANT_H, reach=2)
    spawner(C, 58, 1, 3, MOB_MARKS)
    # the stair to the upper floor (north-going along the east part, rows x 54 .. 56)
    rows = stair_run(C, [(54, 20), (55, 20), (56, 20)], "north", F1, 0, head=4)
    well_rail(C, rows, F1, (0, -1))
    # upstairs: the bedroom (bed, nightstand, wardrobe, rug, a second fireplace on the chimney), the foreman's
    # writing desk and the strong chest
    u = F1 + 1
    C.bp.bed(44, u, 2, "north", "red")
    fp(C, 45, u, 1, "barrel[facing=up,open=false]")
    fp(C, 45, u + 1, 1, "candle[candles=2,lit=true,waterlogged=false]")
    for x in (46, 47):
        fp(C, x, u, 1, "barrel[facing=south,open=false]")
        fp(C, x, u + 1, 1, "barrel[facing=south,open=false]")
    for x in range(44, 48):
        for z in range(4, 7):
            if C.free(x, u, z):
                C.set(x, u, z, "red_carpet" if (x + z) % 2 else "white_carpet")
    C.set(x1, u, 11, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    C.set(x1, u + 1, 11, COB)
    for z in (10, 12):
        C.set(x1 - 1, u, z, SB)
        C.set(x1 - 1, u + 1, z, SB)
    for z in (10, 11, 12):
        C.set(x1 - 1, u + 2, z, stair(SB_ST, "west", "top"))
    antlers(x1 - 1, u + 3, 7, False)
    chest(C, 61, u, 2, "west", "tf_lodge")
    for (x, z) in ((60, 2), (61, 3)):
        C.set(x, u, z, IRON)
    fp(C, 61, u, 6, TABLE)
    fp(C, 61, u, 5, TABLE)
    fp(C, 60, u, 6, f"{W}mahogany_chair[facing=east]")
    fp(C, 61, u + 1, 6, "candle[candles=3,lit=true,waterlogged=false]")
    for x in range(44, 51):
        fp(C, x, u, 20, "bookshelf" if x % 3 else "chiseled_bookshelf[facing=north]")
        fp(C, x, u + 1, 20, "bookshelf")
    fp(C, 47, u, 18, f"{W}mahogany_chair[facing=south]")
    for (x, z, wall) in ((48, 1, "north"), (56, 1, "north"), (48, z1 - 1, "south"), (x0 + 1, 6, "west"),
                         (x0 + 1, 16, "west")):
        wall_lamp(C, x, u + 3, z, wall)


# ------------------------------------------------------------------ the lumber yard (hub)
def log_stack(C, x0, z0, length, axis, layers, seed):
    """A pyramid stack of logs (axis x or z) on sleeper beams, with stakes at the ends."""
    for k in range(layers):
        w = layers - k + 1
        for a in range(length):
            for b in range(w):
                x, z = (x0 + a, z0 + b + k // 2) if axis == "x" else (x0 + b + k // 2, z0 + a)
                if hash3(x, k, z, seed) < 0.06 and k == layers - 1:
                    continue
                C.set(x, 1 + k, z, LOGX if axis == "x" else LOGZ)
    for b in range(layers + 1):
        for a in (-1, length):
            x, z = (x0 + a, z0 + b) if axis == "x" else (x0 + b, z0 + a)
            if b in (0, layers):
                for y in range(1, layers + 2):
                    C.set(x, y, z, SP_FENCE)


def gantry(C, x0, x1, z, h=12):
    """A timber gantry crane over the log stacks: two braced A-frames, a beam, a trolley with a chain and hook."""
    for x in (x0, x1):
        for dz in (-2, 2):
            for y in range(1, h):
                C.set(x, y, z + dz, LOG)
        for dz in range(-2, 3):
            C.set(x, 4, z + dz, STRZ)
            C.set(x, h, z + dz, DLOGZ)
    for x in range(x0, x1 + 1):
        C.set(x, h, z, DLOGX)
        C.set(x, h + 1, z, DLOGX if x in (x0, x1) else SP_SL + "[type=bottom,waterlogged=false]")
    tx = (x0 + x1) // 2 + 2
    C.set(tx, h - 1, z, IRON)
    for y in range(7, h - 1):
        C.set(tx, y, z, CHAIN)
    C.set(tx, 6, z, "anvil[facing=north]")


def shed(C, x0, z0, x1, z1, door_side, table):
    """A lean-to tool shed."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, SP)
            for y in range(1, 5):
                if edge:
                    C.set(x, y, z, DLOG if (x in (x0, x1) and z in (z0, z1)) else SP)
                else:
                    C.clear(x, y, z)
    gable(C, x0, z0, x1, z1, 5, "x", over=1, gable_spec=SP)
    dx, dz = DV[door_side]
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    px, pz = (cx, z1) if door_side == "south" else ((cx, z0) if door_side == "north" else
                                                    ((x1, cz) if door_side == "east" else (x0, cz)))
    for y in (1, 2, 3):
        C.clear(px, y, pz)
    chest(C, x0 + 1, 1, z0 + 1, "south", table)
    fp(C, x1 - 1, 1, z0 + 1, "grindstone[face=floor,facing=north]")
    hang(C, cx, 4, cz, LANT_H, reach=2)


def yard(C):
    """The lumber yard: the waystone on a log plinth by the crane, log stacks, sheds, a sawhorse row, lamps."""
    wx, wz = 0, 14
    waystone(C, wx, 1, wz)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            C.set(wx + dx, 0, wz + dz, SB if max(abs(dx), abs(dz)) == 2 else PAND)
    for (lx, lz) in ((-3, 11), (3, 11), (-3, 17), (3, 17)):
        lamp_post(C, lx, 1, lz, 3)
    BUSY.append((-4, 10, 4, 18))
    # log stacks
    log_stack(C, -36, 22, 14, "x", 4, 721)
    log_stack(C, -36, 32, 12, "x", 3, 722)
    log_stack(C, 14, 24, 16, "x", 4, 723)
    log_stack(C, 20, 34, 10, "x", 3, 724)
    log_stack(C, -40, -6, 10, "z", 4, 725)
    log_stack(C, 24, -6, 12, "z", 3, 726)
    gantry(C, -38, -18, 27, 12)
    gantry(C, 12, 32, 29, 11)
    shed(C, -30, 2, -22, 8, "east", "tf_yard")
    shed(C, 18, 4, 26, 10, "west", "tf_yard")
    # sawhorses and a log cart
    for (sx, sz) in ((-12, 2), (-8, 2), (8, 0)):
        for dz in (0, 2):
            C.set(sx, 1, sz + dz, SP_FENCE)
        C.set(sx, 2, sz, SP_FENCE)
        C.set(sx, 2, sz + 2, SP_FENCE)
        C.set(sx, 2, sz + 1, LOGZ)
    spawner(C, -24, 1, 28, MOB_VINDI) if C.free(-24, 1, 28) else None
    spawner(C, 12, 1, 18, MOB_VINDI)
    for (lx, lz) in ((-20, 0), (20, 0), (-30, 40), (30, 16), (-46, 30), (46, 30), (0, -24), (34, -36), (-34, -36)):
        if C.get(lx, 1, lz) in (None, AIR) and C.get(lx, 0, lz) is not None:
            lamp_post(C, lx, 1, lz, 3)


# ------------------------------------------------------------------ the headworks, the reservoir and the flume
HW = (-2, -108, 12, -92)                      # the sluice house walls; floor y 15, roof deck y 26


def headworks(C):
    """On the shelf: the reservoir behind a log dam, the sluice house (pump, valve gear, the stair to the roof),
    the header tank on the roof deck where the flume begins."""
    x0, z0, x1, z1 = HW
    f, deck = SHELF_Y, 26
    BUSY.append((x0 - 2, z0, 28, z1 + 2))
    # reservoir
    for x in range(16, 27):
        for z in range(-110, -99):
            edge = x in (16, 26) or z in (-110, -100)
            C.set(x, 12, z, "clay")
            for y in range(13, 16):
                if edge:
                    C.set(x, y, z, LOGX if z in (-110, -100) else LOGZ)
                else:
                    C.water(x, y, z)
            C.set(x, 16, z, SP_FENCE) if edge else None
    # the sluice house
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, f, z, SP if not edge else COB)
            for y in range(f + 1, deck):
                if edge:
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    spec = frame_wall_spec(u, y, f + 1, deck - 1, 4)
                    if y in (f + 3, f + 4, f + 5) and u % 4 == 2:
                        spec = GLASS
                    C.set(x, y, z, spec)
                elif y == deck - 1:
                    C.set(x, y, z, DLOGX if (z - z0) % 4 == 0 else SP)
                else:
                    C.clear(x, y, z)
            C.set(x, deck, z, SP if not edge else DLOG)
    # roof deck railing (left open at the flume's mouth on the west edge)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                if x == x0 and z in (-100, -99):
                    continue
                railing(C, x, deck + 1, z, face_of(x - (x0 + x1) / 2.0, z - (z0 + z1) / 2.0))
            else:
                C.clear(x, deck + 1, z)
                C.clear(x, deck + 2, z)
                C.clear(x, deck + 3, z)
    for z in (-100, -99):
        for y in (deck + 1, deck + 2, deck + 3):
            C.clear(x0, y, z)
    # the header tank: a riveted copper drum with brass bands on four posts
    tx, tz = 7, -99
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            d = math.hypot(dx, dz)
            if d > 3.3:
                continue
            for y in range(deck + 2, deck + 8):
                ring = d > 2.3
                if ring or y < deck + 6:
                    C.set(tx + dx, y, tz + dz, BRASS if y in (deck + 4, deck + 7) and ring else COPPER)
                elif y == deck + 6:
                    C.water(tx + dx, y, tz + dz)
            C.set(tx + dx, deck + 1, tz + dz, IRON if abs(dx) == 2 and abs(dz) == 2 else C.get(tx + dx, deck + 1, tz + dz) or AIR)
    for dx in (-2, 2):
        for dz in (-2, 2):
            C.set(tx + dx, deck + 1, tz + dz, IRON)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if not (abs(dx) == 2 and abs(dz) == 2):
                C.clear(tx + dx, deck + 1, tz + dz)
    # the feed pipe from the tank to the flume's mouth
    for x in range(x0 + 1, tx - 3):
        C.set(x, deck + 4, -101, f"{W}copper_pipe[axis=x]")
    C.set(x0, deck + 4, -101, f"{W}copper_pipe[axis=y]")
    # inside: the pump (from the reservoir), valve gear, a workbench
    for z in (-104, -103):
        for x in range(x1, 17):
            C.set(x, f + 2, z, f"{W}copper_pipe[axis=x]")
    for y in range(f + 1, deck - 1):
        C.set(9, y, -103, f"{W}copper_pipe[axis=y]")
    for dy in range(0, 3):
        for dz in (-1, 0, 1):
            C.set(10, f + 1 + dy, -98 + dz, COPPER if dy < 2 else BRASS)
    C.set(10, f + 1, -96, GEAR)
    C.set(10, f + 2, -96, GAUGE)
    fp(C, 1, f + 1, -95, "crafting_table")
    fp(C, 2, f + 1, -95, TABLE)
    chest(C, 0, f + 1, -95, "east", "tf_headworks")
    barrel(C, 0, f + 1, -97)
    spawner(C, 5, f + 1, -99, MOB_DRONE)
    for (lx, lz) in ((3, -96), (3, -102), (8, -96)):
        hang(C, lx, deck - 2, lz, LANT_H, reach=3)
    # doors: south (the shelf) and the stair to the roof (north wall, west-going)
    for x in (4, 5, 6):
        for y in (f + 1, f + 2, f + 3):
            C.clear(x, y, z1)
    rows = stair_run(C, [(11, -107), (11, -106), (11, -105)], "west", deck - f, f)
    well_rail(C, rows, deck, (-1, 0))
    for (x, z) in rows[-1]:
        C.clear(x, deck + 1, z)
    # lamp posts on the shelf
    for (lx, lz) in ((-12, -88), (-4, -88), (14, -90), (26, -92)):
        lamp_post(C, lx, f + 1, lz, 2)


def flume(C):
    """The log flume: a 2-wide trough of flowing water on trestle bents, falling one block every eight from the
    header tank (water y 27) to the wheel pit (the last cells at y 10 spill into the pit)."""
    cells = flume_cells()
    walls = {}
    for (x, z), (y, lv) in cells.items():
        C.set(x, y - 1, z, SP)
        C.water(x, y, z, WATER if lv == 0 else f"water[level={lv}]")
        for yy in range(y + 1, y + 3):
            if C.get(x, yy, z) is None:
                C.clear(x, yy, z)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                q = (x + dx, z + dz)
                if q in cells:
                    continue
                if q[0] >= HW[0] and -101 <= q[1] <= -98:
                    continue
                if q[0] in (-84, -83) and q[1] > -43:
                    continue
                walls[q] = max(walls.get(q, -99), y)
    for (x, z), y in walls.items():
        C.set(x, y - 1, z, SP)
        C.set(x, y, z, STRX if any((x + dx, z) in cells for dx in (-1, 1)) is False else STRZ)
        C.set(x, y + 1, z, SP_SL + "[type=bottom,waterlogged=false]")
    # the spill into the pit
    ylast = min(y for (y, _) in cells.values())
    for x in (-84, -83):
        for y in range(0, ylast + 1):
            C.water(x, y, -42 + 1, "water[level=8]")
    # trestle bents every 5 anchors
    for i, (ax, az) in enumerate(flume_anchors()):
        if i % 5 or az > -46 and ax < -80:
            continue
        nxt = flume_anchors()[min(i + 1, len(flume_anchors()) - 1)]
        dx, dz = nxt[0] - ax, nxt[1] - az
        y = cells[(ax, az)][0]
        if dz == 0:
            posts = [(ax, az - 2), (ax, az + 1)]
        else:
            posts = [(ax - 2, az), (ax + 1, az)]
        for (px, pz) in posts:
            g = C.top.get((px, pz), -2)
            for yy in range(g, y - 1):
                C.set(px, yy, pz, LOG)
            C.set(px, g - 1, pz, COB)
        g0 = max(C.top.get(p, -2) for p in posts)
        for yy in range(y - 2, g0, -6):
            (p0, p1) = posts
            if p0[0] == p1[0]:
                for zz in range(p0[1], p1[1] + 1):
                    C.put(p0[0], yy, zz, STRZ)
            else:
                for xx in range(p0[0], p1[0] + 1):
                    C.put(xx, yy, p0[1], STRX)


def high_bridge(C):
    """The trestle bridge from the headworks shelf over the palisade into the keep's armoury (deck y 15)."""
    za, zb = SHELF[3], KZ - FLOORS[1][1] - 1
    for z in range(za, zb + 1):
        for x in range(-10, -5):
            rail = x in (-10, -6)
            C.set(x, SHELF_Y, z, DLOGZ if rail else SP)
            for y in range(SHELF_Y + 1, SHELF_Y + 5):
                if not rail:
                    C.clear(x, y, z)
            if rail:
                C.set(x, SHELF_Y + 1, z, SP_FENCE)
        if z in (-84, -80, -70, -66):
            for x in (-10, -6):
                g = C.top.get((x, z), 0)
                for y in range(g, SHELF_Y):
                    C.set(x, y, z, LOG)
            for x in range(-10, -5):
                C.set(x, SHELF_Y - 1, z, DLOGX)
                if SHELF_Y - 6 > C.top.get((x, z), 0):
                    C.put(x, SHELF_Y - 6, z, STRX)
        if z % 6 == 0:
            C.set(-10, SHELF_Y + 2, z, LANT)
            C.set(-6, SHELF_Y + 2, z, LANT)


# ------------------------------------------------------------------ the keep
def skirt(C, half, fy, skip=None):
    """A stave roof ring round a storey's foot: three courses of slate stairs stepping down and out from just under
    the storey's sill, gilded tips and hanging lanterns at the corners."""
    for j in (1, 2, 3):
        R = half + j
        y = fy + 1 - j
        for u in range(-R, R + 1):
            for v in range(-R, R + 1):
                if max(abs(u), abs(v)) != R:
                    continue
                if skip and skip(u, v):
                    continue
                x, z = K(u, v)
                if abs(u) == abs(v):
                    C.set(x, y, z, SH)
                else:
                    C.set(x, y, z, stair(SH_ST, OPP[face_of(u, v)]))
    R = half + 3
    for su in (-1, 1):
        for sv in (-1, 1):
            x, z = K(su * (R + 1), sv * (R + 1))
            C.set(x, fy - 2, z, stair(SH_ST, OPP[face_of(su, 0)]))
            C.set(x, fy - 1, z, GILD)
            C.set(x, fy - 3, z, LANT_H)


def storey(C, k):
    """Storey k (1..4): floor slab, jetty joists and brackets under the overhang, timber-framed walls with the
    storey's window pattern, interior air, the ceiling beams."""
    fy, h, clear = FLOORS[k]
    ph = FLOORS[k - 1][1]
    top = fy + clear                 # last wall course; beams at top + 1, next floor at top + 2
    # joists and brackets under the jetty
    for u in range(-h, h + 1):
        for v in range(-h, h + 1):
            m = max(abs(u), abs(v))
            x, z = K(u, v)
            if m > ph:
                along = abs(u) >= abs(v)
                C.set(x, fy - 1, z, (DLOGX if along else DLOGZ) if (u + v) % 2 == 0 else SP)
            elif m <= ph:
                C.put(x, fy - 1, z, (DLOGZ if u % 4 == 0 else SP)) if k == 1 else None
            if m == ph + 1 and (u + v) % 3 == 0 and abs(u) != abs(v):
                C.set(x, fy - 2, z, stair(DO_ST, OPP[face_of(u, v)], "top"))
            # floor slab
            if m == h:
                C.set(x, fy, z, DLOGX if abs(v) == h else DLOGZ)
            else:
                C.set(x, fy, z, (DO if (u % 6 == 0 or v % 6 == 0) else SP) if k != 3 else
                      (PARQ if (u + v) % 2 else SP))
    # walls and air
    for u in range(-h, h + 1):
        for v in range(-h, h + 1):
            m = max(abs(u), abs(v))
            x, z = K(u, v)
            for y in range(fy + 1, top + 2):
                if m == h:
                    w = u if abs(v) == h else v
                    corner = abs(u) == h and abs(v) == h
                    if y == top + 1:
                        spec = DLOGX if abs(v) == h else DLOGZ
                    elif corner or (w + h) % 4 == 0:
                        spec = DLOG
                    elif y == fy + 1:
                        spec = DO
                    elif y == top:
                        spec = STRX if abs(v) == h else STRZ
                    else:
                        spec = SP
                    if not corner and (w + h) % 4 != 0 and window(k, w + h, y - fy):
                        spec = GLASS if k != 2 else AMBER
                    C.set(x, y, z, spec)
                elif y <= top:
                    hollow(C, x, y, z)
                else:
                    C.set(x, y, z, (DLOGX if abs(v) <= h else DLOGZ) if u % 4 == 0 else SP)
    # brass bands on the posts at the sill and the top plate
    for u in range(-h, h + 1, 4):
        for v in (-h, h):
            for (a, b) in ((u, v), (v, u)):
                x, z = K(a, b)
                C.set(x, top + 1, z, BRASS)


def window(k, w, dy):
    """Window cells of storey k (w = position along the wall from the corner, dy = height above the floor)."""
    if k == 1:
        return w % 4 == 2 and 3 <= dy <= 5
    if k == 2:
        return w % 8 in (1, 2, 3) and (4 <= dy <= 10 or 13 <= dy <= 16)
    if k == 3:
        return w % 4 in (1, 3) and 3 <= dy <= 6
    return w % 4 == 2 and 3 <= dy <= 5


def plinth(C):
    """The stone plinth (the lift hall): battered rubble walls 2 thick, arrow slits, the iron door south."""
    fy, h, clear = FLOORS[0]
    for u in range(-15, 16):
        for v in range(-15, 16):
            m = max(abs(u), abs(v))
            x, z = K(u, v)
            for y in range(-4, 1):
                C.set(x, y, z, "stone" if y < 0 else (SB if m >= 13 else (PAND if (u + v) % 2 else "smooth_stone")))
            if m == 15:
                for y in range(1, 3):
                    C.set(x, y, z, MCOB if hash3(x, y, z, 801) < 0.5 else COB)
                C.set(x, 3, z, stair(SB_ST, OPP[face_of(u, v)]) if abs(u) != abs(v) else SB)
            elif m >= 13:
                for y in range(1, clear + 1):
                    hh = hash3(x, y, z, 802)
                    spec = (MSB if hh < 0.4 else COB) if y <= 3 else (SB if hh < 0.7 else (CSB if hh < 0.85 else
                                                                                         "andesite"))
                    if m == 14 and y in (6, 7, 10, 11) and (u if abs(v) == 14 else v) % 6 == 3:
                        spec = "iron_bars"
                    C.set(x, y, z, spec)
            else:
                for y in range(1, clear + 1):
                    hollow(C, x, y, z)
            if m <= 14:
                C.set(x, clear + 1, z, DLOGZ if u % 4 == 0 else (SB if m >= 13 else SP))
    # quoins of dressed stone on the corners
    for su in (-1, 1):
        for sv in (-1, 1):
            for y in range(1, clear + 1):
                x, z = K(su * 14, sv * 14)
                C.set(x, y, z, PAND if y % 2 else SB)


def keep_shaft(C):
    """The counterweight lift's drop well: 3 x 3 air from the strongroom floor (y 55) to the lift hall's pool,
    boxed in by timber walls through the armoury, the great hall and the map room."""
    for y in range(1, PLAT - 8):
        for u in range(8, 13):
            for v in range(-13, -8):
                x, z = K(u, v)
                inner = 9 <= u <= 11 and -12 <= v <= -10
                if inner:
                    C.clear(x, y, z)
                elif y >= FLOORS[1][0]:
                    corner = u in (8, 12) and v in (-13, -9)
                    spec = DLOG if corner else (DO if y % 9 else BRASS)
                    if FLOORS[2][0] + 4 <= y <= FLOORS[2][0] + 14 and not corner and (u == 10 or v == -11) and y % 2:
                        spec = "iron_bars"
                    C.set(x, y, z, spec)
    # the pool
    for u in range(9, 12):
        for v in range(-12, -9):
            x, z = K(u, v)
            C.set(x, -3, z, SB)
            for y in range(-2, 1):
                C.water(x, y, z)
    for u in range(8, 13):
        for v in range(-13, -8):
            if 9 <= u <= 11 and -12 <= v <= -10:
                continue
            x, z = K(u, v)
            for y in range(-3, 1):
                C.set(x, y, z, SB if y < 0 else PAND)


def keep_stairs(C):
    """Every stair of the keep (rows returned for the views and rails)."""
    S = {}
    S["01a"] = stair_run(C, [K(-12, 11), K(-11, 11), K(-10, 11)], "north", 8, 0)
    for u in (-12, -11, -10):
        for v in (1, 2, 3):
            x, z = K(u, v)
            C.set(x, 8, z, SP)
            for y in range(1, 8):
                C.set(x, y, z, SP)
            for y in range(9, 13):
                C.clear(x, y, z)
    S["01b"] = stair_run(C, [K(-12, 0), K(-11, 0), K(-10, 0)], "north", 7, 8)
    well_rail(C, S["01b"], FLOORS[1][0], (0, -1))
    S["12"] = stair_run(C, [K(-6, 11), K(-6, 12), K(-6, 13)], "east", 10, FLOORS[1][0])
    well_rail(C, S["12"], FLOORS[2][0], (1, 0))
    S["23a"] = stair_run(C, [K(13, 13), K(14, 13), K(15, 13)], "north", 10, FLOORS[2][0], rail=(-1, 0))
    for u in (12, 13, 14, 15):
        for v in (1, 2, 3):
            x, z = K(u, v)
            if u == 12:
                C.set(x, 36, z, SP_FENCE)
                C.set(x, 35, z, SP)
                continue
            C.set(x, 35, z, SP)
            for y in range(26, 35):
                C.set(x, y, z, SP)
            for y in range(36, 40):
                C.clear(x, y, z)
    S["23b"] = stair_run(C, [K(13, 0), K(14, 0), K(15, 0)], "north", 10, 35, rail=(-1, 0))
    well_rail(C, S["23b"], FLOORS[3][0], (0, -1))
    S["34"] = stair_run(C, [K(-17, -8), K(-16, -8), K(-15, -8)], "south", 10, FLOORS[3][0], rail=(1, 0))
    well_rail(C, S["34"], FLOORS[4][0], (0, 1))
    S["4p"] = stair_run(C, [K(-19, 6), K(-18, 6), K(-17, 6)], "south", PLAT - FLOORS[4][0], FLOORS[4][0],
                        rail=(1, 0))
    S["sr"] = stair_run(C, [K(15, -6), K(16, -6), K(17, -6)], "north", PLAT - FLOORS[4][0], FLOORS[4][0],
                        rail=(-1, 0))
    return S


def lift_hall(C):
    """Storey 0: the lift hall in the plinth: the pool under the drop well, the winch drum, the guard post (table,
    chairs, a weapon rack, crates); the iron door south opens only from inside onto the yard."""
    fy, h, clear = FLOORS[0]
    f = fy + 1
    x, z = K(0, 14)
    oneway_door(C, x, 1, z, "north", wall=PAND)
    for y in (1, 2, 3):
        C.set(x - 1, y, z, PAND)
        C.set(x + 2, y, z, PAND)
    C.set(x, 4, z, GILD)
    C.set(x, 4, z + 1, stair(SB_ST, "north", "top"))
    # aisles: door -> stair foot, door -> pool
    for (u0, v0, u1, v1) in ((-12, 11, 1, 12), (-1, -9, 1, 12), (-1, -9, 8, -8)):
        X0, Z0 = K(u0, v0)
        X1, Z1 = K(u1, v1)
        reserve(C, X0, Z0, X1, Z1, f)
    # winch drum beside the pool
    for u in range(3, 8):
        X, Z = K(u, -11)
        fp(C, X, 2, Z, STRX)
        fp(C, X, 1, Z, DLOG if u in (3, 7) else "minecraft:air")
    X, Z = K(5, -11)
    fp(C, X, 3, Z, GEAR)
    X, Z = K(5, -12)
    for y in range(4, clear + 1):
        C.set(X, y, Z, CHAIN)
    # the guard post: a table, chairs, a lamp and cards
    for (u, v) in ((-6, -10), (-4, -10)):
        X, Z = K(u, v)
        fp(C, X, 1, Z, TABLE)
    X, Z = K(-5, -9)
    fp(C, X, 1, Z, f"{W}mahogany_chair[facing=north]")
    X, Z = K(-7, -10)
    fp(C, X, 1, Z, f"{W}mahogany_chair[facing=east]")
    X, Z = K(-4, -10)
    C.set(X, 2, Z, LANT)
    X, Z = K(-6, -10)
    table_candles(C, X, 2, Z, 2)
    for (u, v) in ((-11, -11), (-11, -10), (-10, -11), (-11, -9)):
        X, Z = K(u, v)
        barrel(C, X, 1, Z)
    X, Z = K(-11, -11)
    fp(C, X, 2, Z, "barrel[facing=up,open=false]")
    X, Z = K(-6, -11)
    chest(C, X, 1, Z, "south", "tf_armoury")
    # weapon rack on the south wall east of the door
    for u in range(3, 11):
        X, Z = K(u, 12)
        if u % 3 == 0:
            for y in (1, 2):
                fp(C, X, y, Z, DO_FENCE)
            fp(C, X, 3, Z, DO_SL + "[type=bottom,waterlogged=false]")
        else:
            fp(C, X, 1, Z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            fp(C, X, 2, Z, "iron_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    # crates and sacks round the winch, the guards' bench on the east wall
    for (u, v, spec) in ((2, -12, "barrel[facing=north,open=false]"), (8, -7, "barrel[facing=up,open=false]"),
                         (7, -7, "hay_block[axis=x]"), (3, -9, "barrel[facing=up,open=false]")):
        X, Z = K(u, v)
        fp(C, X, 1, Z, spec)
    for v in range(-3, 4):
        X, Z = K(11, v)
        fp(C, X, 1, Z, stair(SP_ST, "east")) if v % 3 else None
    for v in range(-6, 8, 3):
        X, Z = K(12, v)
        fp(C, X, 1, Z, "barrel[facing=up,open=false]")
    # lights: lanterns low on chains from the beams, brackets on the walls
    for (u, v) in ((-4, 4), (4, 4), (4, -4), (-4, -4), (8, 8), (0, -6)):
        X, Z = K(u, v)
        hang(C, X, f + 3, Z, LANT_H, reach=14)
    for u in (-6, 0, 6):
        X, Z = K(u, -12)
        wall_lamp(C, X, f + 3, Z, "north")
    for v in (-8, 0, 8):
        X, Z = K(12, v)
        wall_lamp(C, X, f + 3, Z, "east")


def armoury(C):
    """Storey 1: the armoury: weapon racks on the north and west walls, armour stands with axes and swords on the
    east wall, the smithy corner (anvils, grindstones, the blast furnace), practice dummies, the bridge door north;
    two knights' spawners."""
    fy = FLOORS[1][0]
    f = fy + 1
    # the bridge door (north wall)
    for u in (-9, -8, -7):
        x, z = K(u, -15)
        for y in range(f, f + 4):
            C.clear(x, y, z)
        C.set(x, f + 4, z, GILD if u == -8 else DLOGX)
    # aisles: bridge door -> stair up (south-west) and the stair down's arrival
    for (u0, v0, u1, v1) in ((-9, -14, -7, 13), (-12, -8, -7, -7), (-9, -2, 12, -1)):
        X0, Z0 = K(u0, v0)
        X1, Z1 = K(u1, v1)
        reserve(C, X0, Z0, X1, Z1, f)
    # racks: dark oak frames with chains and trapdoor shields on the north wall
    for u in range(-4, 7):
        x, z = K(u, -14)
        if u % 3 == 0:
            fp(C, x, f, z, DO_FENCE)
            fp(C, x, f + 1, z, DO_FENCE)
            fp(C, x, f + 2, z, "skeleton_skull[rotation=8]") if u == 0 else fp(C, x, f + 2, z, DO_FENCE)
        else:
            fp(C, x, f, z, "barrel[facing=up,open=false]" if u % 3 == 1 else "chiseled_bookshelf[facing=south]")
            fp(C, x, f + 1, z, f"dark_oak_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")
    # halberd racks on the west wall (rods with iron heads between posts)
    for v in range(2, 12):
        x, z = K(-14, v)
        if v % 3 == 2:
            for y in (f, f + 1, f + 2):
                fp(C, x, y, z, DO_FENCE)
        else:
            fp(C, x, f, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            fp(C, x, f + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            fp(C, x, f + 2, z, "iron_trapdoor[facing=east,half=top,open=true,powered=false,waterlogged=false]")
    # the smithy corner
    for (u, v, spec) in ((-2, -6, "anvil[facing=east]"), (2, -6, "grindstone[face=floor,facing=north]"),
                         (5, -6, "smithing_table"), (-5, -4, "blast_furnace[facing=east,lit=true]"),
                         (-5, -5, "blast_furnace[facing=east,lit=true]"), (6, 1, "anvil[facing=north]"),
                         (3, -6, "grindstone[face=floor,facing=north]"), (13, 8, "fletching_table")):
        x, z = K(u, v)
        fp(C, x, f, z, spec)
    x, z = K(-5, -6)
    fp(C, x, f, z, "water_cauldron[level=3]")
    for u in (-1, 0, 1):
        x, z = K(u, -6)
        fp(C, x, f, z, SP_SL + "[type=top,waterlogged=false]")
    x, z = K(0, -6)
    fp(C, x, f + 1, z, LANT)
    # practice dummies: fence, hay body, carved-pumpkin head
    for u in (-2, 1, 4):
        x, z = K(u, 4)
        fp(C, x, f, z, SP_FENCE)
        fp(C, x, f + 1, z, "hay_block[axis=y]")
        fp(C, x, f + 2, z, "carved_pumpkin[facing=south]")
    # the weapons bench (south) and the axe stands
    for u in range(0, 6):
        x, z = K(u, 10)
        fp(C, x, f, z, DO_SL + "[type=top,waterlogged=false]" if u not in (0, 5) else DO)
    x, z = K(2, 10)
    fp(C, x, f + 1, z, "grindstone[face=floor,facing=south]")
    x, z = K(4, 10)
    table_candles(C, x, f + 1, z, 3)
    for (v, gear) in ((-7, dict(head="iron_helmet", chest="iron_chestplate", legs="iron_leggings", feet="iron_boots",
                                mainhand="iron_axe", offhand="shield")),
                      (-1, dict(head="chainmail_helmet", chest="chainmail_chestplate", legs="chainmail_leggings",
                                mainhand="iron_sword")),
                      (1, dict(chest="leather_chestplate", legs="leather_leggings", feet="leather_boots",
                               mainhand="crossbow")),
                      (6, dict(head="iron_helmet", chest="iron_chestplate", mainhand="iron_axe", offhand="iron_axe")),
                      (11, dict(head="golden_helmet", chest="chainmail_chestplate", mainhand="stone_axe"))):
        x, z = K(13, v)
        stand(C, x, f, z, "west", **gear)
    for (u, gear) in ((4, dict(mainhand="iron_axe")), (7, dict(head="leather_helmet", mainhand="wooden_axe"))):
        x, z = K(u, 12)
        stand(C, x, f, z, "north", **gear)
    # spear and shield racks on the south wall, the archery butts by the bridge door, arrow casks
    for u in range(5, 14):
        x, z = K(u, 14)
        if u % 3 == 2:
            for y in (f, f + 1, f + 2):
                fp(C, x, y, z, DO_FENCE)
        else:
            fp(C, x, f, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            fp(C, x, f + 1, z, "iron_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]"
               if u % 3 == 0 else "lightning_rod[facing=up,powered=false,waterlogged=false]")
            fp(C, x, f + 2, z, "dark_oak_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]"
               if u % 3 == 1 else "air")
    for (u, v) in ((-13, -14), (-12, -14), (-11, -14)):
        x, z = K(u, v)
        fp(C, x, f, z, "hay_block[axis=y]")
        fp(C, x, f + 1, z, "target[power=0]")
        fp(C, x, f + 2, z, "hay_block[axis=x]") if u == -12 else None
    for (u, v) in ((12, 9), (12, 7), (11, 9)):
        x, z = K(u, v)
        fp(C, x, f, z, "barrel[facing=up,open=false]")
    # the officers' table: maps of the patrols, a lamp, a helmet on a stand
    for u in range(8, 12):
        x, z = K(u, -6)
        fp(C, x, f, z, TABLE)
    x, z = K(9, -6)
    fp(C, x, f + 1, z, LANT)
    x, z = K(11, -6)
    table_candles(C, x, f + 1, z, 2)
    for u in (8, 10):
        x, z = K(u, -5)
        fp(C, x, f, z, f"{W}mahogany_chair[facing=north]")
    for v in (-4, 4):
        x, z = K(13, v)
        chest(C, x, f, z, "west", "tf_armoury")
    for (u, v) in ((-3, 0), (6, 8)):
        x, z = K(u, v)
        spawner(C, x, f, z, MOB_KNIGHT)
    for v in range(-12, 13, 6):
        x, z = K(-13, v)
        if C.free(x, f + 3, z):
            C.set(x, f + 3, z, "red_wall_banner[facing=east]") if backed(C, x - 1, f + 3, z) else None
    # lights: lanterns low on chains, brackets on the walls
    for (u, v) in ((-4, -9), (4, -9), (-4, 7), (4, 7), (2, -2), (10, 4)):
        x, z = K(u, v)
        hang(C, x, f + 3, z, LANT_H, reach=8)
    for u in (-12, 10):
        x, z = K(u, -14)
        wall_lamp(C, x, f + 3, z, "north")
    for u in (-11, 11):
        x, z = K(u, 14)
        wall_lamp(C, x, f + 3, z, "south")


def great_hall(C):
    """Storey 2: the great hall, 33 wide and 18 high: two long tables with benches under four antler chandeliers,
    the guild-master's dais and throne north under banners, a stone hearth on the west wall with antlers, ale casks
    and a carpet runner down the middle, the grand stair on the east wall."""
    fy = FLOORS[2][0]
    f = fy + 1
    # aisles: the stair from the armoury (arrives east, v 11..13) -> the grand stair foot (east wall), the runner
    for (u0, v0, u1, v1) in ((4, 10, 16, 15), (-2, -11, 2, 15)):
        X0, Z0 = K(u0, v0)
        X1, Z1 = K(u1, v1)
        reserve(C, X0, Z0, X1, Z1, f)
    # dais
    for u in range(-7, 8):
        for v in range(-16, -12):
            x, z = K(u, v)
            C.set(x, f, z, DO_SL + "[type=bottom,waterlogged=false]" if v == -13 else DO)
            if v != -13:
                C.clear(x, f + 1, z)
    for u in range(-7, 8):
        x, z = K(u, -12)
        carpet(C, x, f, z, "red") if C.free(x, f, z) else None
    x, z = K(0, -15)
    C.set(x, f + 1, z, stair(DO_ST, "south"))
    C.set(x, f + 2, z, GILD)
    for du in (-1, 1):
        X, Z = K(du, -15)
        C.set(X, f + 1, Z, DO_FENCE)
        candle(C, X, f + 2, Z, 3, "red")
    for du in (-4, 4):
        X, Z = K(du, -15)
        chest(C, X, f + 1, Z, "south", "tf_hall")
    for du in (-6, 6):
        X, Z = K(du, -15)
        C.set(X, f + 1, Z, DO_FENCE)
        C.set(X, f + 2, Z, LANT)
    for u in range(-6, 7, 3):
        X, Z = K(u, -16)
        if C.free(X, f + 2, Z) and backed(C, X, f + 2, Z - 1):
            C.set(X, f + 2, Z, "red_wall_banner[facing=south]")
    # the carpet runner from the stair to the dais
    for v in range(-11, 10):
        for u in (-1, 0, 1):
            x, z = K(u, v)
            if C.free(x, f, z):
                C.set(x, f, z, "red_carpet" if u == 0 else "yellow_carpet")
                C.keep.discard((x, f, z))
    # two long tables and benches
    for tu in (-8, 4):
        for v in range(-8, 9):
            for du in (0, 1):
                x, z = K(tu + du, v)
                fp(C, x, f, z, DO_SL + "[type=top,waterlogged=false]")
                if v % 4 == 0 and du == 0:
                    candle(C, x, f + 1, z, 4)
                elif v % 4 == 2 and du == 1:
                    C.set(x, f + 1, z, "brown_candle[candles=3,lit=true,waterlogged=false]")
            x, z = K(tu - 1, v)
            fp(C, x, f, z, stair(SP_ST, "west")) if v % 5 else None
            x, z = K(tu + 2, v)
            fp(C, x, f, z, stair(SP_ST, "east")) if v % 5 else None
        for v in (-9, 9):
            x, z = K(tu, v)
            fp(C, x, f, z, f"{W}mahogany_chair[facing={'south' if v < 0 else 'north'}]")
    # hearth on the west wall: a stone chimney breast, a deep fire, the mantel with antlers and candles
    for v in range(-3, 4):
        for y in range(f, f + 7):
            x, z = K(-16, v)
            C.set(x, y, z, COB if hash3(x, y, z, 811) < 0.5 else SB)
        x, z = K(-15, v)
        if abs(v) <= 1:
            C.set(x, f, z, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]" if v == 0 else
                  "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
            C.set(x, f + 1, z, AIR)
            C.set(x, f + 2, z, AIR)
            C.set(x, f + 3, z, SB)
        else:
            for y in range(f, f + 4):
                C.set(x, y, z, SB)
    for v in range(-3, 4):
        x, z = K(-15, v)
        C.set(x, f + 4, z, stair(SB_ST, "east", "top"))
        if v in (-3, 3):
            candle(C, x, f + 5, z, 4)
    for y in range(f + 7, FLOORS[2][0] + FLOORS[2][2] + 1):
        for v in (-1, 0, 1):
            x, z = K(-16, v)
            C.set(x, y, z, SB if hash3(x, y, z, 812) < 0.7 else COB)
    # antler trophy over the mantel
    x, z = K(-15, 0)
    C.set(x, f + 6, z, "bone_block[axis=y]")
    for dv in (-1, 1):
        X, Z = K(-15, dv)
        C.set(X, f + 6, Z, SP_FENCE)
        X, Z = K(-15, 2 * dv)
        C.set(X, f + 7, Z, SP_FENCE)
        X, Z = K(-15, dv)
        C.set(X, f + 7, Z, SP_FENCE)
    for v in (-4, 4):
        x, z = K(-15, v)
        C.set(x, f + 6, z, "bone_block[axis=y]")
        C.set(x, f + 7, z, SP_FENCE)
    # fireside chairs and a bear rug
    for (u, v, fc) in ((-12, -2, "west"), (-12, 2, "west")):
        x, z = K(u, v)
        fp(C, x, f, z, f"{W}mahogany_chair[facing={fc}]")
    for u in range(-14, -12):
        for v in (-1, 0, 1):
            x, z = K(u, v)
            if C.free(x, f, z):
                C.set(x, f, z, "brown_carpet")
    # ale casks along the south wall and the east wall
    for u in range(-14, -6):
        x, z = K(u, 16)
        fp(C, x, f, z, "barrel[facing=north,open=false]")
        if u % 2 == 0:
            fp(C, x, f + 1, z, "barrel[facing=north,open=false]")
    for v in range(-10, -2):
        x, z = K(16, v)
        fp(C, x, f, z, "barrel[facing=west,open=false]")
    x, z = K(-10, 15)
    fp(C, x, f, z, SP_SL + "[type=top,waterlogged=false]")
    fp(C, x, f + 1, z, LANT)
    # banners round the walls under the windows
    for w in range(-14, 15, 4):
        for (u, v, fc) in ((16, w, "west"), (w, 16, "north")):
            x, z = K(u, v)
            dx, dz = DV[OPP[fc]]
            if C.free(x, f + 2, z) and backed(C, x + dx, f + 2, z + dz):
                C.set(x, f + 2, z, f"{'red' if w % 8 else 'yellow'}_wall_banner[facing={fc}]")
    # chandeliers low over the tables (arms 5 over the floor), lanterns on brackets along the walls
    for (u, v) in ((-7, -5), (-7, 5), (5, -5), (5, 5)):
        x, z = K(u, v)
        antler_chandelier(C, x, f + 5, z, reach=16)
    for (u, v, wall) in ((-16, -9, "west"), (-16, 9, "west"), (16, 0, "east"), (16, 9, "east"), (-9, -16, "north"),
                         (9, -16, "north"), (-6, 16, "south"), (6, 16, "south")):
        x, z = K(u, v)
        wall_lamp(C, x, f + 3, z, wall)
    x, z = K(-12, 10)
    spawner(C, x, f, z, MOB_VINDI)
    x, z = K(-12, -11)
    spawner(C, x, f, z, MOB_PILL)


def map_room(C):
    """Storey 3: the map room: the great map table (the valley in carpets with a model of the fortress on it),
    chart desks and cartography tables under charts on the walls, three globes, lodestone compasses and a brass
    orrery, lecterns, chart shelves, a telescope at the window; the waystone (site of grace) by the stair up."""
    fy = FLOORS[3][0]
    f = fy + 1
    # aisles: the grand stair's arrival (north-east) -> round the drop well -> the stair up (west)
    for (u0, v0, u1, v1) in ((13, -14, 15, -10), (-17, -15, 15, -14), (-17, -14, -14, -9), (-14, -9, 15, -8)):
        X0, Z0 = K(u0, v0)
        X1, Z1 = K(u1, v1)
        reserve(C, X0, Z0, X1, Z1, f)
    # the great map table: 15 x 9, cartography tables round the rim, the valley in carpets
    for u in range(-7, 8):
        for v in range(-4, 5):
            x, z = K(u, v)
            edge = abs(u) == 7 or abs(v) == 4
            fp(C, x, f, z, "cartography_table" if edge and (u + v) % 2 == 0 else (DO if edge else TABLE))
            if not edge:
                n = vnoise(u, v, 3.0, 821)
                col = "blue" if abs(v - round(math.sin(u * 0.5) * 1.5)) == 0 else (
                    "green" if n > 0.55 else ("lime" if n > 0.4 else "white"))
                carpet(C, x, f + 1, z, col)
    # the model fortress at the table's middle: palisade ring, keep tiers, a smokestack pin
    for (du, dv) in ((a, b) for a in range(-3, 4) for b in range(-2, 3) if max(abs(a), abs(b) * 1.5) >= 2.9):
        x, z = K(du, dv)
        C.set(x, f + 1, z, "spruce_fence")
    for du in (-1, 0, 1):
        for dv in (-1, 0, 1):
            x, z = K(du, dv)
            C.set(x, f + 1, z, DO)
            C.set(x, f + 2, z, SH_SL + "[type=bottom,waterlogged=false]")
    x, z = K(0, 0)
    C.set(x, f + 2, z, SP)
    C.set(x, f + 3, z, SH_SL + "[type=bottom,waterlogged=false]")
    x, z = K(1, 1)
    C.set(x, f + 2, z, "end_rod[facing=up]")
    for (du, dv, spec) in ((-5, -2, "lodestone"), (5, 2, "flower_pot"), (-5, 2, "candle[candles=4,lit=true,"
                                                                         "waterlogged=false]"),
                           (5, -2, "candle[candles=4,lit=true,waterlogged=false]"), (-4, 0, LANT), (4, 0, LANT)):
        x, z = K(du, dv)
        C.set(x, f + 1, z, spec)
    # chart shelves along the north wall, charts (banners) over them
    for u in range(-12, 7):
        x, z = K(u, -17)
        fp(C, x, f, z, "bookshelf")
        fp(C, x, f + 1, z, "chiseled_bookshelf[facing=south]" if u % 3 == 0 else "bookshelf")
        fp(C, x, f + 2, z, "bookshelf")
    # chart desks on the east and south walls: desk, chair, candles, an open chart (a white banner over it)
    for (u, v, wall) in ((17, 4, "east"), (17, 8, "east"), (17, 12, "east"), (-6, 17, "south"), (0, 17, "south"),
                         (6, 17, "south"), (-17, 4, "west"), (-17, 10, "west")):
        x, z = K(u, v)
        dx, dz = DV[wall]
        fp(C, x, f, z, "cartography_table" if (u + v) % 3 == 0 else TABLE)
        if (u + v) % 2:
            table_candles(C, x, f + 1, z, 3)
        else:
            fp(C, x, f + 1, z, "daylight_detector[inverted=false,power=0]")
        cx, cz = x - dx, z - dz
        fp(C, cx, f, cz, f"{W}mahogany_chair[facing={wall}]")
        if C.free(x, f + 3, z) and backed(C, x + dx, f + 3, z + dz):
            col = ("white", "light_blue", "brown", "lime")[(u * 3 + v) % 4]
            C.set(x, f + 3, z, f"{col}_wall_banner[facing={OPP[wall]}]")
    # lecterns round the table, the stair-side reading desk
    for (u, v, fc) in ((-10, 0, "east"), (10, 0, "west"), (0, 7, "north"), (0, -7, "south")):
        x, z = K(u, v)
        fp(C, x, f, z, f"lectern[facing={fc},has_book=false,powered=false]")
    # globes: the brass globe, a verdigris globe and a lapis desk globe; a brass orrery (the planets on rods)
    for (gu, gv, ring, core) in ((10, 10, BRASS, VERD), (-10, 10, COPPER, "lapis_block")):
        gx, gz = K(gu, gv)
        fp(C, gx, f, gz, DO)
        fp(C, gx, f + 1, gz, DO_FENCE)
        for (dx, dy, dz) in ((0, 2, 0), (1, 3, 0), (-1, 3, 0), (0, 3, 1), (0, 3, -1), (0, 4, 0)):
            fp(C, gx + dx, f + dy, gz + dz, ring)
        fp(C, gx, f + 3, gz, core)
    x, z = K(12, -4)
    fp(C, x, f, z, TABLE)
    fp(C, x, f + 1, z, "light_blue_stained_glass")
    ox, oz = K(-10, -4)
    fp(C, ox, f, oz, BRASS)
    fp(C, ox, f + 1, oz, DO_FENCE)
    fp(C, ox, f + 2, oz, "end_rod[facing=up]")
    fp(C, ox, f + 3, oz, GILD)
    for (dx, dz, spec) in ((1, 0, "end_rod[facing=east]"), (-1, 0, "end_rod[facing=west]"),
                           (0, 1, "end_rod[facing=south]"), (0, -1, "end_rod[facing=north]")):
        fp(C, ox + dx, f + 3, oz + dz, spec)
    # the telescope at the south-west window: a tripod and a copper rod
    tx, tz = K(-14, 14)
    fp(C, tx, f, tz, SP_FENCE)
    fp(C, tx, f + 1, tz, BRASS)
    fp(C, tx - 1, f + 1, tz + 1, "lightning_rod[facing=south,powered=false,waterlogged=false]")
    for v in (-4, 4):
        x, z = K(16, v)
        chest(C, x, f, z, "west", "tf_maproom")
    x, z = K(-12, -11)
    waystone(C, x, f, z)
    # lights: the chandelier over the table, lanterns low on chains, brackets
    x, z = K(0, 0)
    hang(C, x, f + 5, z, CHANDELIER, reach=4)
    for (u, v) in ((-5, -3), (5, -3), (-5, 3), (5, 3), (-12, -11), (12, -4)):
        x, z = K(u, v)
        hang(C, x, f + 3, z, LANT_H, reach=6)
    for u in (-13, -6, 0, 6, 13):
        for v in (-11, 6, 12):
            x, z = K(u, v)
            if C.free(x, f + 3, z) and C.free(x, f + 2, z):
                hang(C, x, f + 3, z, LANT_H, reach=6)
    for u in (-13, 13):
        for v in (-5, 1):
            x, z = K(u, v)
            if C.free(x, f + 3, z) and C.free(x, f + 2, z):
                hang(C, x, f + 3, z, LANT_H, reach=6)


def boiler_room(C):
    """Storey 4: the boiler room under the crown: two fire-tube boilers (fire doors, gauges, valve wheels, safety
    valves) feeding the beam engine above, steam mains under the ceiling, coal heaps and bunkers with shovels, the
    stokers' bench, the water tank; the strongroom walled off in the north-east."""
    fy = FLOORS[4][0]
    f = fy + 1
    top = fy + FLOORS[4][2]
    # strongroom walls (u 7, v 3)
    for y in range(f, f + 7):
        for v in range(-19, 4):
            x, z = K(7, v)
            C.set(x, y, z, DIB)
        for u in range(7, 20):
            x, z = K(u, 3)
            C.set(x, y, z, DIB)
    # aisles: stair up from the map room (arrives v -2) -> the stair to the crown (v 6), and the middle walk
    for (u0, v0, u1, v1) in ((-19, -2, -15, 5), (-15, -3, 6, -1)):
        X0, Z0 = K(u0, v0)
        X1, Z1 = K(u1, v1)
        reserve(C, X0, Z0, X1, Z1, f)
    # boilers along u
    for bv in (-12, 11):
        for u in range(-12, 3):
            for dy in (-1, 0, 1):
                for dv in (-1, 0, 1):
                    if abs(dy) + abs(dv) == 2:
                        continue
                    x, z = K(u, bv + dv)
                    C.set(x, f + 1 + dy, z, BRASS if u % 4 == 0 else COPPER)
        for u in (-13, 3):
            x, z = K(u, bv)
            C.set(x, f, z, "blast_furnace[facing=%s,lit=true]" % ("west" if u < 0 else "east"))
            C.set(x, f + 1, z, IRON)
        for y in range(f + 3, PLAT):
            x, z = K(-2, bv)
            C.set(x, y, z, f"{W}copper_pipe[axis=y]")
        side = 1 if bv < 0 else -1          # the side of the boiler facing the room's middle
        for u in (-10, -6, 1):
            x, z = K(u, bv + 2 * side)
            fp(C, x, f, z, "furnace[facing=%s,lit=true]" % ("south" if side > 0 else "north"))
        for u in (-8, -4, 0):
            x, z = K(u, bv + side)
            C.set(x, f + 1, z, GAUGE)
        x, z = K(-4, bv)
        C.set(x, f + 3, z, GAUGE)
        for u in (-11, -7, -3, 1):
            x, z = K(u, bv)
            C.set(x, f + 3, z, f"{W}copper_pipe[axis=y]")
            C.set(x, f + 4, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        # steam main under the ceiling along u, down to the engine pipe
        for u in range(-13, 4):
            x, z = K(u, bv + side)
            if C.free(x, top, z):
                C.set(x, top, z, f"{W}copper_pipe[axis=x]")
        # coal bunker behind each boiler: a stone-brick bin heaped with coal, a shovel (a lightning rod handle)
        for u in range(-9, -2):
            for dv in (2, 3):
                x, z = K(u, bv - dv * side)
                edge = u in (-9, -3) or dv == 3
                if edge:
                    fp(C, x, f, z, SB_WALL if dv == 2 else SB)
                else:
                    fp(C, x, f, z, "coal_block")
                    if hash3(x, f, z, 841) < 0.5:
                        fp(C, x, f + 1, z, "coal_block")
    for u in range(-1, 4):
        x, z = K(u, 0)
        fp(C, x, f, z, "coal_block")
        fp(C, x, f + 1, z, "coal_block") if u % 2 else None
    # coal heaps on the floor round the middle bin, black carpet dust
    for (u, v) in ((-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (-2, 0), (4, 0)):
        x, z = K(u, v)
        if C.free(x, f, z) and (x, f, z) not in C.keep:
            C.set(x, f, z, "black_carpet")
    x, z = K(4, 1)
    fp(C, x, f, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the water tank (cauldrons in a copper frame) and the stokers' bench by the south wall
    for u in range(-6, -1):
        x, z = K(u, 18)
        fp(C, x, f, z, "water_cauldron[level=3]" if u % 2 else COPPER)
        fp(C, x, f + 1, z, f"{W}copper_pipe[axis=x]" if u % 2 else COPPER)
    for u in range(1, 6):
        x, z = K(u, 18)
        fp(C, x, f, z, stair(SP_ST, "south"))
    x, z = K(0, 18)
    fp(C, x, f, z, "barrel[facing=up,open=false]")
    fp(C, x, f + 1, z, LANT)
    x, z = K(6, 18)
    fp(C, x, f, z, TABLE)
    table_candles(C, x, f + 1, z, 3)
    # the engineer's corner: a workbench with gauges and the valve board on the east part
    for v in range(6, 14):
        x, z = K(19, v)
        fp(C, x, f, z, "smithing_table" if v == 8 else (SP_SL + "[type=top,waterlogged=false]" if v % 2 else IRON))
        fp(C, x, f + 2, z, GAUGE if v % 3 == 0 else GEAR)
    x, z = K(-6, 0)
    spawner(C, x, f, z, MOB_AUTO)
    for u in (-16, -10, -4, 2):
        for v in (-17, -7, 0, 7, 16):
            x, z = K(u, v)
            if C.free(x, f + 3, z) and C.free(x, f + 2, z):
                hang(C, x, f + 3, z, LANT_H, reach=5)
    for (u, v) in ((10, 7), (16, 7), (10, 13), (16, 13), (13, 18), (-16, 12), (-16, -12)):
        x, z = K(u, v)
        if C.free(x, f + 3, z) and C.free(x, f + 2, z):
            hang(C, x, f + 3, z, LANT_H, reach=5)


def strongroom(C):
    """The guild strongroom: brass-tiled floor, strongbox chests, gold and ledgers behind bars, the drop well of the
    counterweight lift with its headframe and counterweight."""
    fy = FLOORS[4][0]
    f = fy + 1
    for u in range(8, 20):
        for v in range(-19, 3):
            x, z = K(u, v)
            if 9 <= u <= 11 and -12 <= v <= -10:
                continue
            if C.solid(x, fy, z):
                C.set(x, fy, z, BTILE if (u + v) % 2 else GILD)
    # railings round the drop well, open on the west
    for u in range(8, 13):
        for v in range(-13, -8):
            if 9 <= u <= 11 and -12 <= v <= -10:
                continue
            if u == 8 and -12 <= v <= -10:
                continue
            x, z = K(u, v)
            C.set(x, f, z, f"{W}brass_railing[facing={face_of(u - 10, v + 11)}]")
    # the headframe and the counterweight
    for (u, v) in ((8, -13), (12, -13), (8, -9), (12, -9)):
        x, z = K(u, v)
        for y in range(f + 1, f + 6):
            C.set(x, y, z, DLOG)
    for u in range(8, 13):
        x, z = K(u, -11)
        C.set(x, f + 6, z, DLOGX)
    x, z = K(13, -11)
    C.set(x, f + 6, z, DLOGX)
    x, z = K(10, -11)
    C.set(x, f + 5, z, GEAR)
    x, z = K(13, -11)
    for y in range(f + 2, f + 6):
        C.set(x, y, z, CHAIN)
    C.set(x, f + 1, z, IRON)
    C.set(x, f, z, BRASS)
    # strongboxes and the hoard
    for (u, v) in ((18, -18), (18, -2), (9, 1), (18, -10)):
        x, z = K(u, v)
        chest(C, x, f, z, "west" if u > 15 else "north", "tf_strongroom")
    for (u, v) in ((19, -16), (19, -15), (19, -4), (19, -3)):
        x, z = K(u, v)
        fp(C, x, f, z, "gold_block" if (u + v) % 2 else "raw_gold_block")
    for v in range(-19, -16):
        x, z = K(13, v)
        fp(C, x, f, z, "bookshelf")
    for (u, v) in ((12, -4), (14, -16)):
        x, z = K(u, v)
        hang(C, x, f + 5, z, CHANDELIER, reach=2)


def platform(C):
    """The crown: the platform floor (45 wide) on jetty joists and braces, the railing, the corner turrets (a stave
    spire north-west, the boiler smokestack south-east), the two stair houses and the beam engine."""
    h4 = FLOORS[4][1]
    for u in range(-PH, PH + 1):
        for v in range(-PH, PH + 1):
            m = max(abs(u), abs(v))
            x, z = K(u, v)
            if m > h4:
                C.set(x, PLAT - 1, z, (DLOGX if abs(u) >= abs(v) else DLOGZ) if (u + v) % 2 == 0 else SP)
            if m == h4 + 1 and (u + v) % 3 == 0 and abs(u) != abs(v):
                C.set(x, PLAT - 2, z, stair(DO_ST, OPP[face_of(u, v)], "top"))
                C.set(x, PLAT - 3, z, DO_FENCE)
            if m == PH:
                spec = DLOGX if abs(v) == PH else DLOGZ
            else:
                r = math.hypot(u, v)
                spec = GILD if 11.5 < r <= 12.5 else (DO if (u % 5 == 0 or v % 5 == 0) else SP)
            C.set(x, PLAT, z, spec)
    # railing and lamp posts on the edge
    for u in range(-PH, PH + 1):
        for v in range(-PH, PH + 1):
            if max(abs(u), abs(v)) != PH:
                continue
            x, z = K(u, v)
            if (u % 6 == 0 and abs(v) == PH) or (v % 6 == 0 and abs(u) == PH):
                C.set(x, PLAT + 1, z, DLOG)
                C.set(x, PLAT + 2, z, LANT)
            else:
                railing(C, x, PLAT + 1, z, face_of(u, v))
    stave_spire(C)
    x, z = K(18, 18)
    for u in range(16, 22):
        for v in range(16, 22):
            X, Z = K(u, v)
            for y in range(PLAT + 1, PLAT + 6):
                C.set(X, y, Z, BRICK if hash3(X, y, Z, 831) < 0.8 else SMK)
    smokestack(C, x, z, PLAT + 6, 96, r=2)
    stair_house(C, -21, 7, -15, 21, door=("east", (17, 19)))
    stair_house(C, 14, -21, 21, -5, door=("west", (-20, -18)))
    beam_engine(C)


def stair_house(C, u0, v0, u1, v1, door):
    """A timber stair house on the platform over a stairwell: framed walls 5 high, a slate gable roof along v, a
    3-wide door."""
    for u in range(u0, u1 + 1):
        for v in range(v0, v1 + 1):
            x, z = K(u, v)
            edge = u in (u0, u1) or v in (v0, v1)
            for y in range(PLAT + 1, PLAT + 6):
                if edge:
                    w = v - v0 if u in (u0, u1) else u - u0
                    corner = u in (u0, u1) and v in (v0, v1)
                    C.set(x, y, z, DLOG if corner or w % 4 == 0 else (STRZ if y == PLAT + 5 else SP))
                else:
                    if C.free(x, y, z):
                        C.clear(x, y, z)
    x0, z0 = K(u0, v0)
    x1, z1 = K(u1, v1)
    gable(C, x0, z0, x1, z1, PLAT + 6, "z", over=1, gable_spec=SP)
    side, (va, vb) = door
    uu = u1 if side == "east" else u0
    for v in range(va, vb + 1):
        x, z = K(uu, v)
        for y in range(PLAT + 1, PLAT + 4):
            C.clear(x, y, z)
        C.set(x, PLAT + 4, z, GILD if v == (va + vb) // 2 else DLOGZ)
    cx, cz = K((u0 + u1) // 2, (va + vb) // 2)
    hang(C, cx, PLAT + 4, cz, LANT_H, reach=3)


def stave_spire(C):
    """The north-west corner turret: a stave-church spire of three stacked roofs, dragon-head gables, a gilded
    finial."""
    cu, cv = -18, -18
    tiers = [(3, PLAT + 1, PLAT + 8), (2, PLAT + 10, PLAT + 15), (1, PLAT + 17, PLAT + 20)]
    for (r, y0, y1) in tiers:
        for u in range(cu - r, cu + r + 1):
            for v in range(cv - r, cv + r + 1):
                x, z = K(u, v)
                edge = max(abs(u - cu), abs(v - cv)) == r
                for y in range(y0, y1 + 1):
                    C.set(x, y, z, (DLOG if (abs(u - cu) == r and abs(v - cv) == r) else
                                    (DO_FENCE if y in (y1 - 2, y1 - 1) and (u + v) % 2 else SP)) if edge else SP)
        # its skirt roof
        R = r + 1
        for u in range(cu - R - 1, cu + R + 2):
            for v in range(cv - R - 1, cv + R + 2):
                m = max(abs(u - cu), abs(v - cv))
                x, z = K(u, v)
                if m == R:
                    C.set(x, y1 + 1, z, SH if abs(u - cu) == abs(v - cv) else stair(SH_ST, OPP[face_of(u - cu, v - cv)]))
                elif m == R + 1:
                    C.set(x, y1, z, SH if abs(u - cu) == abs(v - cv) else stair(SH_ST, OPP[face_of(u - cu, v - cv)]))
                elif m < R:
                    C.set(x, y1 + 1, z, SH)
        for su in (-1, 1):
            for sv in (-1, 1):
                x, z = K(cu + su * (R + 1), cv + sv * (R + 1))
                C.set(x, y1 + 1, z, GILD)
    # the spire
    y = PLAT + 22
    for k in range(7):
        x, z = K(cu, cv)
        if k < 5:
            for (du, dv) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if k < 2 else ((0, 0),):
                X, Z = K(cu + du, cv + dv)
                C.set(X, y + k, Z, SH)
        else:
            C.set(x, y + k, z, GILD if k == 5 else "lightning_rod[facing=up,powered=false,waterlogged=false]")


def beam_engine(C):
    """The brass beam engine at the centre of the crown: bed plate, the flywheel (r 7) on its pedestals, the
    cylinder, the twin columns and the walking beam (y 84), piston and connecting rods, the governor."""
    y0 = PLAT + 1
    for u in range(-2, 3):
        for v in range(-15, 9):
            x, z = K(u, v)
            C.set(x, y0, z, IRON if (abs(u) == 2 or v in (-15, 8)) else TREAD)
    # flywheel in the y-v plane at u 0, centre (v -8, y 73)
    yc, vc, R = 73, -8, 7
    for dv in range(-R - 1, R + 2):
        for dy in range(-R - 1, R + 2):
            d = math.hypot(dv, dy)
            x, z = K(0, vc + dv)
            y = yc + dy
            if y <= y0:
                continue
            if R - 0.7 <= d <= R + 0.4:
                C.set(x, y, z, DIB)
            elif d < 1.2:
                C.set(x, y, z, GILD)
            elif d < R - 0.7:
                a = math.atan2(dy, dv)
                kk = (a / (math.pi / 3)) % 1.0
                if kk < 0.14 or kk > 0.86:
                    C.set(x, y, z, IRON)
    for u in range(-2, 3):
        x, z = K(u, vc)
        C.set(x, yc, z, IRON if u else GILD)
    for u in (-2, 2):
        x, z = K(u, vc)
        for y in range(y0 + 1, yc):
            C.set(x, y, z, DIB)
    # cylinder
    cu, cv = 0, 5
    for du in range(-2, 3):
        for dv in range(-2, 3):
            if math.hypot(du, dv) > 2.3:
                continue
            x, z = K(cu + du, cv + dv)
            for y in range(y0 + 1, 77):
                C.set(x, y, z, BRASS if y in (68, 72, 76) else COPPER)
            C.set(x, 77, z, DIB)
    # twin columns and the entablature
    for u in (-1, 1):
        x, z = K(u, 0)
        for y in range(y0 + 1, 83):
            C.set(x, y, z, DIB if y % 6 else BRASS)
    for u in (-1, 0, 1):
        x, z = K(u, 0)
        C.set(x, 83, z, GEAR if u == 0 else IRON)
    # walking beam
    for v in range(-9, 8):
        x, z = K(0, v)
        C.set(x, 84, z, IRON if -8 < v < 7 else BRASS)
        if abs(v) <= 3:
            C.set(x, 85, z, IRON)
    # rods
    x, z = K(0, cv)
    for y in range(78, 84):
        C.set(x, y, z, CHAIN)
    x, z = K(1, vc)
    for y in range(yc + 1, 84):
        C.set(x, y, z, CHAIN)
    C.set(x, 84, z, IRON)
    # governor on the beam's pivot
    x, z = K(0, 0)
    C.set(x, 86, z, DO_FENCE)
    for du in (-1, 1):
        X, Z = K(du, 0)
        C.set(X, 87, Z, GILD)
    C.set(x, 87, z, BRASS)
    # steam pipes from the boilers below
    for (u, v) in ((-2, -12), (-2, 11)):
        x, z = K(u, v)
        for y in range(PLAT, PLAT + 3):
            C.set(x, y, z, f"{W}copper_pipe[axis=y]")
    x, z = K(3, 5)
    for y in range(y0 + 1, y0 + 6):
        C.set(x, y, z, f"{W}copper_pipe[axis=y]")
    C.set(x, y0 + 6, z, GAUGE)


def arena(C):
    """The seal, the mist in the south-west stair house door, the sealed bars in the north-east house door."""
    x, z = K(8, 10)
    C.bp.boss_seal(x, PLAT, z, BOSS, 30)
    for v in range(17, 20):
        X, Z = K(-15, v)
        C.bp.mist(X, PLAT + 1, Z, X, PLAT + 3, Z)
    for v in range(-20, -17):
        X, Z = K(14, v)
        for y in range(PLAT + 1, PLAT + 4):
            C.set(X, y, Z, MOD["vault_bars"])


def keep(C):
    BUSY.append((KX - 24, KZ - 24, KX + 24, KZ + 24))
    plinth(C)
    for k in (1, 2, 3, 4):
        storey(C, k)
    skirt(C, FLOORS[1][1], FLOORS[1][0], skip=lambda u, v: v < -14 and -12 <= u <= -4)
    for k in (2, 3, 4):
        skirt(C, FLOORS[k][1], FLOORS[k][0])
    platform(C)
    keep_shaft(C)
    keep_stairs(C)
    lift_hall(C)
    armoury(C)
    great_hall(C)
    map_room(C)
    boiler_room(C)
    strongroom(C)
    arena(C)


# ------------------------------------------------------------------ the felled-forest hillside
def hillside(C):
    """The logging slope above the bluff: two felled giants lying along the contours by their stumps, more stumps,
    one standing giant on the crest, a corduroy skid road, scattered spruces and boulders."""
    T = C.top

    def ground(x, z):
        return T.get((x, z), 0)

    for (sx, sz, r, h) in ((34, -108, 2.8, 3), (62, -115, 3.2, 4), (80, -100, 3.5, 4), (86, -90, 2.6, 5),
                           (46, -120, 2.2, 3)):
        stump(C, sx, sz, ground(sx, sz) + 1, r, h, 901 + sx)
    for (x0, x1, z, r) in ((38, 72, -108, 2.6), (66, 100, -115, 3.0)):
        ybot = max(ground(x, z + dz) for x in range(x0, x1 + 1) for dz in (-2, 0, 2)) + 1
        felled_trunk(C, x0, x1, z, r, ybot - 1, 911 + x0)
    gx, gz = 102, -101
    giant_spruce(C, gx, gz, ground(gx, gz) + 1, 36, 921)
    # the corduroy skid road from the felled giants down to the skid path
    for z in range(-106, -98):
        for x in (48, 49, 50, 51):
            t = ground(x, z)
            C.set(x, t, z, LOGX)
            for y in range(t + 1, t + 3):
                if C.get(x, y, z) is None:
                    C.clear(x, y, z)
    # spruces and boulders
    placed = [(gx, gz)]
    P = hill_path_cells()
    for i in range(300):
        x = int(-40 + hash01(i, 3, 931) * 150)
        z = int(ZMIN + 4 + hash01(i, 4, 932) * 40)
        k = C.kind.get((x, z))
        if k != "hill" or in_busy(x, z, 3) or (x, z) in P:
            continue
        if any((x + dx, z + dz) in P for dx in (-3, 0, 3) for dz in (-3, 0, 3)):
            continue
        if any(math.hypot(x - px, z - pz) < 7 for (px, pz) in placed):
            continue
        if C.get(x, T[(x, z)] + 1, z) not in (None, AIR):
            continue
        placed.append((x, z))
        t = T[(x, z)]
        if hash01(x, z, 933) < 0.2:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if hash01(x + dx, z + dz, 934) < 0.7:
                        C.set(x + dx, T.get((x + dx, z + dz), t) + 1, z + dz, MCOB if (dx + dz) % 2 else "andesite")
            C.set(x, t + 2, z, "mossy_cobblestone")
        else:
            C.set(x, t, z, PODZOL)
            spruce_tree(C, x, z, t + 1, 9 + int(hash01(x, z, 935) * 8), 936 + i)
        if len(placed) >= 26:
            break


# ------------------------------------------------------------------ lighting
# rooms (feet box x0, y0, z0, x1, y1, z1) lit to block light >= 8 by lanterns hung on chains over the dark spots
LIT_ROOMS = {
    "lift_hall": (-12, 1, -60, 12, 1, -36),
    "armoury": (-14, 16, -62, 14, 16, -34),
    "great_hall": (-16, 26, -64, 16, 27, -32),
    "map_room": (-17, 46, -65, 17, 46, -31),
    "boiler_room": (-19, 56, -67, 19, 56, -29),
    "sawmill": (-77, 1, -39, -47, 1, -11),
    "sawmill_gallery": (-77, 10, -39, -47, 10, -11),
    "boiler_house": (-69, 1, -45, -56, 1, -41),
    "mess_hall": (-71, 1, -69, -45, 1, -53),
    "lodge": (43, 1, 1, 61, 1, 21),
    "lodge_upstairs": (43, 7, 1, 61, 7, 21),
}
LIGHT_REPORT = {}


def light_rooms(C):
    for name, box in LIT_ROOMS.items():
        LIGHT_REPORT[name] = light_fill(C, box)


# ------------------------------------------------------------------ the builder
def timber_fortress(bp):
    C = Ctx(bp)
    BUSY.clear()
    for r in (SAW, MESS, LODGE, KILN_DECK, (-40, -8, 36, 40), (KX - 24, KZ - 24, KX + 24, KZ + 24),
              (HW[0] - 2, HW[1], 28, HW[3] + 2), (-16, 38, 16, 54), (36, -72, 66, -32), (-70, -50, -54, -40),
              (-12, -88, -4, -62)):
        BUSY.append(r)
    heightfield(C)
    write_terrain(C)
    river(C)
    wheel_pit(C)
    sawmill(C)
    mess_hall(C)
    lodge(C)
    kilns(C)
    trestle(C)
    yard(C)
    keep(C)
    headworks(C)
    flume(C)
    high_bridge(C)
    palisade(C)
    gatehouse(C)
    river_bridge(C)
    approach(C)
    camp(C)
    approach_trees(C)
    hillside(C)
    light_rooms(C)


VIEWS = [
    ("sawmill", (-50, 1, -14), (-66, 4, -25)),
    ("mess_hall", (-46, 1, -61), (-68, 3, -61)),
    ("foremans_lodge", (44, 1, 12), (47, 2, 3)),
    ("armoury", (10, 16, -38), (0, 18, -60)),
    ("great_hall", (0, 26, -40), (0, 30, -63)),
    ("map_room", (12, 46, -42), (0, 47, -48)),
    ("boiler_room", (-6, 56, -42), (-6, 58, -60)),
    ("boss_arena", (10, 65, -34), (0, 75, -48)),
]

register(StructureDef(
    "timber_fortress", "overworld", ["taiga", "snowy_taiga", "windswept_forest"],
    [Piece("fortress", timber_fortress, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_PILL, 6, 1, 2), (MOB_VINDI, 3, 1, 1), (MOB_MARKS, 3, 1, 2)],
    title_fr="La Forteresse du bois", title_en="The Timber Fortress"))
