"""The Storm Spire (La Flèche des tempêtes): a lightning-harvesting complex crowning a mountain summit. A 110-high
copper-and-iron tesla spire rises from a fortified plateau carved into the crags: five stacked coil rings, a flaring
crown bowl and, over the open crown platform, a corona of lightning rods and end rods on six legs. Six lattice
collector masts stand on the surrounding pinnacles, their iron-chain cables sagging to the spire's second coil ring.
Colossal tier (tools/BUILDING.md §1, §12 concept 32, §10 legacy-dungeon template, §15), steampunk accents
(tools/STYLE_STEAMPUNK.md: Leyden jars of glass and copper, giant dynamos, a funicular, a bubble-column lift cage).

Silhouette (one noun phrase, §15.1): a needle of dark iron banded with copper, five fat coil rings stacked up its
shaft and a wide crown bowl crackling with rods on top, standing on a walled crag, six thin masts round it tied to
it by sagging cables.

Layout, ground y = 0 (feet 1), x east, z south; the spire's axis is (SX, SZ) = (0, -8).
  * the massif: the upper plateau (top y 24) carries the dynamo court, the capacitor hall (west), the dynamo house
    and the coil workshop (east); the bastion terrace (top 14) to the south with the gate bastion and its forecourt;
    the barracks terrace (top 34, north-west); the observatory pinnacle (top 44, north-east); a north crag ridge to
    ~50 and six spur pinnacles under the masts; the mountaineers' camp on flat ground to the south (y 0);
  * the approach: from the camp (waystone) up the funicular incline (rails, a parked cable car, a maintenance
    stair) or the three-leg switchback stair on the west face, to the forecourt; the gate (a closed great gate with a
    wicket) and the vaulted gate passage (compression), the stair up into the dynamo court (release: the spire
    stands over the court);
  * the dynamo court (hub, waystone): paving, transformer kiosks, insulator posts, the cooling pond under the slide;
    branches: the capacitor hall (west: two rows of giant Leyden jars, busbars, the stair to its roof walk), the
    dynamo house (east: three giant generators with flywheels, a control gallery), the coil workshop (north-east:
    winding lathes, spools), the pinnacle stair up to the weather observatory (anemometers, wind vanes, barometers,
    the telescope dome), the ridge walk west to the engineers' barracks (bunks, lockers, mess, stove), the barracks
    stair down to the court (a loop), the battery vaults under the court (rows of cells, reached by a stair from the
    court and a tunnel from the gate's guard room: a loop);
  * the main route on: the capacitor hall's roof walk and the covered bridge into the spire's first coil ring, then
    up inside the spire: each coil ring is a gallery walked half round (1 insulator gallery, 2 condenser ring,
    3 spark-gap gallery, 4 resonance chamber), the helical stair in the core between them; ring 5 is the site of
    grace (switchboard, waystone, the lift's top); the grace turret's spiral stair (compression) and the mist at its
    door onto the crown platform: the arena (33 wide, railed, open sky, the corona overhead);
  * the treasury: the charged vault inside the crown bowl under the arena, down a ladder under sealed bars;
  * shortcuts (§10.4): the lift cage in the spire's newel (a drop well from the vault and the grace into a pool in
    the spire's base lobby, whose iron door opens from inside only, and a bubble column back up to the grace); the
    weather slide (a flowing-water channel on an aqueduct from the observatory and a waterfall into the court's
    cooling pond); the bastion postern (a stair from the court down to an iron door onto the forecourt, lever inside).
Loot gradient (§15.6): camp, forecourt 1; gate, court, hall, dynamo house 1-2; workshop, barracks, vaults 2;
observatory, rings 2-3; grace 3; the charged vault 3-5.
Height budget: the corona's needle stands ~140 above the ground layer: the spire is clipped where the ground lies
above y ~180 (the highest jagged peaks).
"""
import math
import random

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, IRON_SLAB, PIPES,
                       TABLE, TREAD, TREAD_SLAB, VERD, W, fbm, hash01, hash3, out_facing, vnoise)
from ..parts import LOOT, MOD

# the champion of the crown platform: the Tesla Archon (seal, remembrance and quest follow this constant)
BOSS = "brasshaven:tesla_archon"
MOB_DRONE = W + "steam_drone"
MOB_AUTO = W + "turbine_automaton"
MOB_GUNNER = W + "boiler_gunner"
MOB_SPIDER = W + "clockwork_spider"
MOB_MITE = W + "rust_mite"
MOB_RAIDER = W + "sky_raider"
MOB_GARGOYLE = W + "gargoyle"
MOB_STRAY = "minecraft:stray"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
ENGR = W + "engraved_brass"
BTILE = W + "brass_tiles"
GRILLE = W + "brass_grille"
GILD = W + "gilded_trim"
DIB = W + "dark_iron_bricks"
DIB_ST = W + "dark_iron_brick_stairs"
DIB_SL = W + "dark_iron_brick_slab"
COPPER_SL = W + "copper_plating_slab"
COPPER_ST = W + "copper_plating_stairs"
VERD_SL = W + "verdigris_plating_slab"
IRON_WALL = W + "dark_iron_plating_wall"
MAHOG = W + "mahogany_panelling"
PARQ = W + "mahogany_parquet"
SLATE, SLATE_ST, SLATE_SL = W + "slate_roof_tiles", W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"
VALVE = W + "valve_wheel"
COG = W + "wall_cog"
RAIL = W + "brass_railing"
SB, MSB, CSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"
SB_ST, SB_SL, SB_WALL = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
DSB, DSB_ST, DSB_SL, DSB_WALL = "deepslate_bricks", "deepslate_brick_stairs", "deepslate_brick_slab", \
    "deepslate_brick_wall"
PDS = "polished_deepslate"
PAND, PAND_SL, PAND_ST = "polished_andesite", "polished_andesite_slab", "polished_andesite_stairs"
CU_OX, CU_WE, CU_EX = "waxed_oxidized_copper", "waxed_weathered_copper", "waxed_exposed_copper"
CUT_CU, CUT_OX = "waxed_cut_copper", "waxed_oxidized_cut_copper"
CU_BLOCK = "waxed_copper_block"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CHAIN_X, CHAIN_Z = "iron_chain[axis=x,waterlogged=false]", "iron_chain[axis=z,waterlogged=false]"
BULB = "waxed_copper_bulb[lit=true,powered=false]"
BULB_OX = "waxed_oxidized_copper_bulb[lit=true,powered=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
ROD_D = "lightning_rod[facing=down,powered=false,waterlogged=false]"
GLASS = "glass"
GOLD = "gold_block"
PANE = "glass_pane"
AMBER = "orange_stained_glass_pane"
BLUE_GL = "light_blue_stained_glass"
GRASS = "grass_block[snowy=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# ------------------------------------------------------------------ dimensions
SX, SZ = 0, -8                       # the spire's axis
G = 24                               # upper plateau top block (feet 25)
BT = 14                              # bastion terrace top block (feet 15)
T34, T44 = 34, 44                    # barracks terrace, observatory pinnacle tops
RF = [39, 52, 65, 78, 91]            # coil ring gallery feet (ring 5 = the site of grace)
CORE_R = 6.15                        # core air radius (cells), the helix band 3.1 .. 6.1
RC, RW = 4.6, 3.0                    # helix centre radius and width
NEWEL_R = 3.1                        # solid newel round the lift tubes (cells with d < 3.1)
BUBBLE = (1, 1)                      # the lift's bubble column (relative to the axis)
WELL = (-1, 1)                       # the drop well
F_VAULT = 100                        # the charged vault's feet (floor y 99)
AY = 110                             # arena floor block y (feet 111)
AR = 16.4                            # arena floor radius
TUR = (0, 15)                        # the grace turret's centre (absolute x, z)
P24C, P24R = (0, -6), (64.0, 34.0)   # upper plateau superellipse
P14C, P14R = (0, 46), (34.0, 16.0)   # bastion terrace
T34C, T34R = (-40, -52), (18.0, 12.0)
T44C, T44RAD = (42, -50), 8.5
CAMP = (8, 94)
CAP = (-62, -30, -26, 10)            # capacitor hall walls x0, z0, x1, z1
DYN = (26, -22, 62, 8)               # dynamo house walls
WSHOP = (28, -36, 52, -24)           # coil workshop walls
BARR = (-54, -60, -28, -44)          # barracks walls
VAULT = (-18, 4, 2, 22)              # battery vaults walls (floor y 10)
BAS = (-22, 28, 22, 50)              # gate bastion block
POND = (13, -33, 19, -27)            # cooling pond (x0, z0, x1, z1)
MASTS = [(54, 20, 30), (0, 40, 34), (-54, 20, 30), (-64, -42, 40), (0, -62, 48), (62, -32, 36)]
MAST_H = 30


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ang(x, z):
    return math.degrees(math.atan2(z, x)) % 360.0


def polar(r, a, c=(SX, SZ)):
    return c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))


def dsp(x, z):
    """Horizontal distance to the spire's axis."""
    return math.hypot(x - SX, z - SZ)


def asp(x, z):
    return ang(x - SX, z - SZ)


def in_arc(a, a0, a1):
    return (a - a0) % 360.0 <= (a1 - a0) + 1e-9


def adelta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def q2(s):
    return round(s * 2) / 2.0


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def se(x, z, c, r, p=3.0):
    """Superellipse norm (<= 1 inside)."""
    return (abs((x - c[0]) / r[0]) ** p + abs((z - c[1]) / r[1]) ** p) ** (1.0 / p)


def in_rect(x, z, r, m=0):
    return r[0] - m <= x <= r[2] + m and r[1] - m <= z <= r[3] + m


class Ctx:
    """Blueprint wrapper: ``keep`` holds reserved air (walkways' headroom) that decoration (``put``) never fills;
    ``top`` the massif column tops; ``kind`` their terrace."""

    def __init__(self, bp):
        self.bp = bp
        self.keep = set()
        self.top = {}
        self.kind = {}

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))

    def put(self, x, y, z, spec):
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def clear(self, x, y, z):
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def air(self, x, y, z):
        """Explicit air, not reserved (decoration may still go there)."""
        self.bp.set(x, y, z, AIR)
        self.keep.discard((x, y, z))

    def clear_if(self, x, y, z):
        if self.bp.get(x, y, z) is not None:
            self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b and "bubble" not in b

    def free(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR


WALK = {}                                # (x, z) -> [feet s] of every walkway / stair cell


def reg(x, z, s):
    WALK.setdefault((x, z), []).append(s)


def rail_ok(x, z, s):
    return all(abs(t - s) >= 3.0 for t in WALK.get((x, z), ()))


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def lever(C, x, y, z, facing, face="wall"):
    C.set(x, y, z, f"lever[face={face},facing={facing},powered=false]")


def iron_door(C, x, y, z, facing, hinge="left"):
    for half, dy in (("lower", 0), ("upper", 1)):
        C.set(x, y + dy, z, f"iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def wood_door(C, x, y, z, facing, wood="spruce", hinge="left"):
    for half, dy in (("lower", 0), ("upper", 1)):
        C.set(x, y + dy, z, f"{wood}_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def candle(C, x, y, z, n=3, color="white"):
    C.put(x, y, z, f"{color}_candle[candles={n},lit=true,waterlogged=false]")


def hang(C, x, y, z, lamp=LANT_H, reach=16):
    """A lamp at (x, y, z) on a chain up to the first solid block above."""
    top = y + 1
    while top < y + reach and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return False
    for yy in range(y + 1, top):
        C.put(x, yy, z, CHAIN)
    C.put(x, y, z, lamp)
    return True


def chest(C, x, y, z, facing, table):
    C.keep.discard((x, y, z))
    C.bp.chest(x, y, z, facing, loot=LOOT + table)


def barrel(C, x, y, z, facing="up"):
    C.keep.discard((x, y, z))
    C.bp.barrel(x, y, z, facing)


def spawner(C, x, y, z, mob):
    C.keep.discard((x, y, z))
    C.bp.spawner(x, y, z, mob)


def waystone(C, x, y, z):
    C.keep.discard((x, y, z))
    C.set(x, y, z, MOD["waystone"])


def lamp_post(C, x, y, z, h=3, lamp=EDISON):
    """An iron lamp post on feet y: a plated base, a wall post, an Edison lamp on top."""
    C.set(x, y, z, IRON)
    for yy in range(y + 1, y + h):
        C.set(x, yy, z, IRON_WALL)
    C.set(x, y + h, z, lamp)


def fill_down(C, x, y, z, spec, ymin=-14):
    """Fill from y down to the first solid block (or ymin) with spec (a callable gets (x, y, z))."""
    for yy in range(y, ymin - 1, -1):
        if C.solid(x, yy, z):
            return
        C.set(x, yy, z, spec(x, yy, z) if callable(spec) else spec)


def line3(C, p0, p1, spec, force=False):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 1.3) + 1
    out = []
    for i in range(n + 1):
        t = i / n
        p = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if p in out:
            continue
        out.append(p)
        if force:
            C.set(*p, spec)
        elif C.free(*p):
            C.put(*p, spec)
    return out


def disk_pts(cx, cz, r):
    R = int(math.ceil(r)) + 1
    return [(x, z) for x in range(int(cx) - R, int(cx) + R + 1) for z in range(int(cz) - R, int(cz) + R + 1)
            if math.hypot(x - cx, z - cz) <= r + 0.01]


def surface(C, x, z, s, full, half, under=None):
    """Walking surface at feet s (a multiple of 0.5): a full block, or a bottom slab on ``under``. Returns the top
    block y."""
    n = math.floor(s)
    if s - n > 0.25:
        C.set(x, n, z, slab(half))
        C.set(x, n - 1, z, under or full)
        return n
    C.set(x, n - 1, z, full)
    return n - 1


def rail_at(C, x, z, s, facing, under=BRASS_SLAB, post=None, spec=None):
    """A railing on the edge of a walk at feet s (a top slab carries it where nothing is below)."""
    top = math.ceil(s - 0.01)
    if not rail_ok(x, z, s) or not C.free(x, top, z) or (x, top, z) in C.keep:
        return False
    if C.free(x, top - 1, z):
        C.set(x, top - 1, z, slab(under, "top"))
    if post:
        C.set(x, top, z, post[0])
        C.set(x, top + 1, z, post[1])
    elif spec:
        C.set(x, top, z, spec)
    else:
        railing(C, x, top, z, facing)
    return True


def walkway(C, pts, width=3, full=SB, half=SB_SL, under=None, edge=None, rails=True, head=4, lamp_every=8,
            rail_spec=None, support=None, post=(IRON, LANT)):
    """A walkway along a polyline of (x, feet s, z) points, quantised to half blocks (slope <= 0.5 per block).
    ``edge`` = (full, half) of the outer lanes; ``support`` fills under the deck down to the ground. Returns
    {(x, z): s}."""
    hw = width // 2
    deck_c, rail_c = {}, {}
    total = sum(math.hypot(b[0] - a[0], b[2] - a[2]) for a, b in zip(pts, pts[1:])) or 1.0
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        if L < 1e-6:
            continue
        if abs(b[1] - a[1]) / L > 0.52:
            print(f"storm_spire: walkway segment {a}->{b} too steep ({abs(b[1] - a[1]) / L:.2f})")
        ux, uz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
        px, pz = -uz, ux
        n = int(L * 3) + 1
        for i in range(n + 1):
            t = i / n
            cx, cz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            s = a[1] + (b[1] - a[1]) * t
            tt = (acc + L * t) / total
            for w in range(-hw - 1, hw + 2):
                X, Z = round(cx + px * w), round(cz + pz * w)
                (rail_c if abs(w) == hw + 1 else deck_c).setdefault((X, Z), []).append((abs(w), s, tt))
        acc += L
    out = {}
    for (X, Z), ss in deck_c.items():
        ss.sort()
        s = q2(ss[0][1])
        out[(X, Z)] = s
        reg(X, Z, s)
    for (X, Z), s in out.items():
        mid = deck_c[(X, Z)][0][0] < hw or hw == 0
        f, h = (full, half) if (mid or not edge) else edge
        y = surface(C, X, Z, s, f, h, under)
        for c in range(1, head + 1):
            C.clear(X, y + c, Z)
        if support:
            fill_down(C, X, y - 2, Z, support)
    if rails:
        k = 0
        for (X, Z), ss in sorted(rail_c.items(), key=lambda kv: min(v[2] for v in kv[1])):
            if (X, Z) in deck_c:
                continue
            ss.sort()
            s = q2(ss[0][1])
            nb = min(((x2, z2) for (x2, z2) in ((X + 1, Z), (X - 1, Z), (X, Z + 1), (X, Z - 1)) if (x2, z2) in out),
                     default=None)
            if nb is None:
                continue
            top = math.ceil(s - 0.01)
            if C.solid(X, top - 1, Z) and C.top.get((X, Z), -99) >= top - 1 and not support:
                continue                                   # ground at the same level: no railing
            if C.solid(X, top, Z):
                continue
            k += 1
            pst = post if lamp_every and k % lamp_every == 0 else None
            if support and C.free(X, top - 1, Z):
                fill_down(C, X, top - 1, Z, support)
            rail_at(C, X, Z, s, out_facing(X - nb[0], Z - nb[1]), post=pst, spec=rail_spec)
    return out


def spiral(C, segs, rc, w, full, half, fill, head=4, rails=True, rmax=14, cx=SX, cz=SZ, support=None,
           rail_spec=None):
    """A stair winding round (cx, cz): segs [(a0, a1, s0, s1)] (each arc < 360), feet s linear in the angle; the band
    is w wide round the centre-line radius rc. ``support`` fills under the treads down to the ground. Returns
    {(x, z): s} of the last segment's cells merged (later segments win)."""
    allc = {}
    R = int(rmax) + 2
    for (a0, a1, s0, s1) in segs:
        cells = {}
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                d = math.hypot(x - cx, z - cz)
                if abs(d - rc) > w / 2.0:
                    continue
                a = ang(x - cx, z - cz)
                if in_arc(a, a0 % 360.0, a0 % 360.0 + (a1 - a0)):
                    t = ((a - a0) % 360.0) / (a1 - a0)
                    cells[(x, z)] = q2(s0 + (s1 - s0) * t)
        for (x, z), s in cells.items():
            reg(x, z, s)
        for (x, z), s in cells.items():
            y = surface(C, x, z, s, full, half, under=fill)
            for c in range(1, head + 1):
                C.clear(x, y + c, z)
            if support:
                fill_down(C, x, y - 2, z, support)
            elif C.free(x, y - 1, z):
                C.set(x, y - 1, z, slab(half, "top"))
        if rails:
            for (x, z), s in cells.items():
                for (dx, dz) in N4:
                    n = (x + dx, z + dz)
                    if n in cells:
                        continue
                    top = math.ceil(s - 0.01)
                    if C.solid(n[0], top - 1, n[1]) or C.solid(n[0], top, n[1]):
                        continue
                    if support:
                        fill_down(C, n[0], top - 1, n[1], support)
                    rail_at(C, n[0], n[1], s, out_facing(dx, dz), spec=rail_spec)
        allc.update(cells)
    return allc


def stair_run(C, cells0, d, n, fy, spec=SB_ST, support=SB, head=4):
    """A straight flight climbing toward ``d``: ``cells0`` is the first tread row [(x, z)]; tread i sits at y
    fy + 1 + i (so the last tread is flush with a floor at fy + n). Headroom is cleared ``head`` above each tread,
    solid support under each tread down to fy + 1. Returns the rows."""
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
            reg(x, z, t + 0.5)
        rows.append(row)
    return rows


def box(C, x0, y0, z0, x1, y1, z1, wall, floor=None, ceil=None, air=True):
    """A room: walls on the perimeter from y0 to y1, a floor at y0 - 1, a ceiling at y1 + 1, air inside."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if floor is not None:
                C.set(x, y0 - 1, z, floor(x, z) if callable(floor) else floor)
            if ceil is not None:
                C.set(x, y1 + 1, z, ceil(x, z) if callable(ceil) else ceil)
            for y in range(y0, y1 + 1):
                if edge:
                    C.set(x, y, z, wall(x, y, z) if callable(wall) else wall)
                elif air:
                    C.air(x, y, z)


def carve(C, x0, y0, z0, x1, y1, z1, keep=False):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                (C.clear if keep else C.air)(x, y, z)


def fill(C, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def rails_round(C, cells, y_floor, spec=None, skip=()):
    """Railings on floor y_floor round a set of open cells (a stairwell): on floor cells next to the hole."""
    for (x, z) in cells:
        for (dx, dz) in N4:
            q = (x + dx, z + dz)
            if q in cells or q in skip:
                continue
            if C.solid(q[0], y_floor, q[1]) and C.free(q[0], y_floor + 1, q[1]) and \
                    (q[0], y_floor + 1, q[1]) not in C.keep:
                if spec:
                    C.set(q[0], y_floor + 1, q[1], spec)
                else:
                    railing(C, q[0], y_floor + 1, q[1], out_facing(-dx, -dz))


# ------------------------------------------------------------------ the massif
def terrace_at(x, z):
    """(top, kind) of a carved terrace at (x, z), or None. Edges get a little two-octave noise (crag lips)."""
    n = 0.035 * (fbm(x, z, 14.0, 11) - 0.5) + 0.012 * (vnoise(x, z, 4.0, 12) - 0.5)
    if math.hypot(x - T44C[0], z - T44C[1]) <= T44RAD:
        return T44, "obs"
    if se(x, z, T34C, T34R, 2.5) <= 1.0 + n:
        return T34, "barr"
    if se(x, z, P24C, P24R, 3.0) <= 1.0 + n:
        return G, "plateau"
    if se(x, z, P14C, P14R, 4.0) <= 1.0 + n * 0.5:
        return BT, "bastion"
    if -46 <= x <= 48 and 80 <= z <= 108:
        return 0, "camp"
    return None


def natural_h(x, z):
    """Natural rock height round the terraces: steep falls from each terrace edge, a north ridge, spur pinnacles
    under the masts, crag noise. -99 outside the massif."""
    best = -99.0
    for (c, r, p, top, k) in ((P24C, P24R, 3.0, G, 1.25), (P14C, P14R, 4.0, BT, 0.62), (T34C, T34R, 2.5, T34, 1.4)):
        e = se(x, z, c, r, p)
        if e <= 1.0:
            best = max(best, top)
            continue
        dist = (e - 1.0) * min(r)
        best = max(best, top - k * dist)
    d44 = math.hypot(x - T44C[0], z - T44C[1])
    best = max(best, T44 - 4.0 * max(0.0, d44 - T44RAD) if d44 < 24 else -99)
    # the north ridge behind the plateau: peaks north of the spire, falls to the flanks
    if z < -30:
        ridge = 50 - 0.0065 * x * x - 0.9 * max(0.0, -z - 70) - 1.1 * max(0.0, z + 46)
        best = max(best, ridge)
    # spur pinnacles under the masts
    for (mx, mz, my) in MASTS:
        dm = math.hypot(x - mx, z - mz)
        if dm < 16:
            best = max(best, my - 1 - 2.4 * max(0.0, dm - 2.5))
    if best < -2:
        return -99
    # crag noise: strong on the high faces, calm near the ground
    n = 7.0 * (fbm(x, z, 16.0, 21) - 0.5) + 2.5 * (vnoise(x, z, 4.0, 22) - 0.5)
    amp = smooth(best / 12.0)
    return best + n * amp


def heightfield(C):
    top, kind = C.top, C.kind
    for x in range(-84, 85):
        for z in range(-86, 109):
            t = terrace_at(x, z)
            nat = natural_h(x, z)
            if t is not None:
                tt, k = t
                if k == "camp":
                    if nat > 0 and z < 84:
                        top[(x, z)], kind[(x, z)] = int(round(nat)), "rock"
                    else:
                        top[(x, z)], kind[(x, z)] = 0, "camp"
                    continue
                top[(x, z)], kind[(x, z)] = tt, k
                # crags rise behind a terrace (north ridge, pinnacles): keep them where they stand well above it
                if nat > tt + 6 and k in ("plateau", "barr") and z < -30:
                    top[(x, z)], kind[(x, z)] = int(round(nat)), "rock"
                continue
            if nat <= -2:
                continue
            # the slope down to the camp's flat ground blends in
            if z > 60:
                nat = max(nat, 0.0)
            top[(x, z)], kind[(x, z)] = int(round(max(nat, -1))), "rock"
    return top


def rock(x, y, z):
    """Natural rock: jittered strata of stone, andesite, tuff and calcite; cobble and moss low down."""
    j = int((hash01(x // 5, z // 5, 31) - 0.5) * 4)
    band = (y + j) % 9
    h = hash3(x, y, z, 32)
    if y <= 2 and h < 0.35:
        return "mossy_cobblestone" if h < 0.15 else "cobblestone"
    if band in (0, 1):
        return "andesite" if h < 0.85 else "stone"
    if band == 4:
        return "tuff" if h < 0.75 else "andesite"
    if band == 7 and y > 20:
        return "calcite" if h < 0.6 else "diorite"
    return "stone" if h < 0.88 else ("cobblestone" if h < 0.95 else "gravel")


def ground_top(x, z, t, steep, kind):
    """The surface block of a column."""
    h = hash01(x, z, 41)
    if kind == "camp":
        v = vnoise(x, z, 6.0, 42)
        if v > 0.6:
            return "gravel" if h < 0.6 else "coarse_dirt"
        return GRASS if h < 0.65 else ("coarse_dirt" if h < 0.85 else "stone")
    if kind in ("plateau", "bastion", "barr", "obs"):
        return rock(x, t, z)
    if steep >= 3:
        return rock(x, t, z)
    if t >= 46:
        v = vnoise(x, z, 7.0, 43)                   # snow lies in drifts, rock shows between them
        if v > 0.45 and h < 0.85:
            return "snow_block"
        return "calcite" if h < 0.15 else ("gravel" if h < 0.3 else rock(x, t, z))
    if t >= 30:
        return "stone" if h < 0.5 else ("gravel" if h < 0.7 else ("calcite" if h < 0.85 else "andesite"))
    return GRASS if h < 0.4 else ("stone" if h < 0.6 else ("gravel" if h < 0.8 else "coarse_dirt"))


def write_terrain(C):
    """A crust of rock: every column is filled from below its lowest neighbour (faces stay closed) up to its top;
    the rim reaches 12 below the ground layer. Two layers of explicit air over the ground."""
    top, kind = C.top, C.kind
    for (x, z), t in top.items():
        nb = [top.get((x + dx, z + dz)) for dx, dz in N4]
        edge = any(n is None for n in nb)
        lo = min([n for n in nb if n is not None] + [t])
        steep = t - lo
        y0 = -12 if edge else min(t - 4, lo - 2)
        if kind[(x, z)] == "camp":
            y0 = -3 if not edge else -8
        for y in range(y0, t):
            C.set(x, y, z, rock(x, y, z) if (y < t - 2 or steep >= 3) else ("dirt" if kind[(x, z)] in ("camp",)
                                                                           else rock(x, y, z)))
        C.set(x, t, z, ground_top(x, z, t, steep, kind[(x, z)]))
        for y in range(t + 1, t + 3):
            if C.get(x, y, z) is None:
                C.bp.set(x, y, z, AIR)


FULL_W = ("stone", "brick", "andesite", "tuff", "plating", "dirt", "gravel", "cobble", "calcite", "diorite", "planks",
          "grass_block", "deepslate", "_block", "copper", "glass", "log", "terracotta", "granite", "blackstone",
          "tiles", "bookshelf", "clay", "parquet", "plate", "concrete", "wool", "obsidian", "basalt", "bulb")
PART_W = ("slab", "stair", "wall", "fence", "pane", "bars", "chain", "door", "rail", "rod", "lantern", "lamp", "carpet",
          "button", "lever", "sign", "ladder", "torch", "candle", "water", "air", "bed", "head", "plant", "grass[")


LIGHT_EMIT = {"lantern": 15, "soul_lantern": 10, "campfire": 15, "sea_lantern": 15, "glowstone": 15, "edison_lamp": 15,
              "hanging_edison_lamp": 15, "brass_chandelier": 15, "end_rod": 14, "torch": 14, "wall_torch": 14,
              "copper_bulb": 15, "oxidized_copper_bulb": 4, "waxed_copper_bulb": 15, "waxed_oxidized_copper_bulb": 4,
              "shroomlight": 15}
NO_BULB = ("chest", "barrel", "spawner", "door", "lamp", "bulb", "glass", "waystone", "seal", "bars", "sign", "bed",
           "water", "ladder", "stairs", "slab", "lantern", "gold", "rod", "vault", "table", "shelf", "lectern", "gauge",
           "valve", "cog", "gear", "pipe", "furnace", "anvil", "redstone")


def light_pass(C):
    """Every covered floor (a ceiling within 14 blocks over the head) gets block light 8 or more: the light of all the
    lamps is flooded through the blueprint; where a floor stays dark, a lit copper bulb replaces its ceiling block (low
    ceilings) or an Edison lamp hangs on a chain four blocks over it (tall halls)."""
    import numpy as np
    from ..blueprint import is_solid
    blocks = C.bp.blocks
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    X0, Y0, Z0 = min(xs) - 1, min(ys) - 1, min(zs) - 1
    SH = (max(xs) - X0 + 2, max(ys) - Y0 + 2, max(zs) - Z0 + 2)
    opaque = np.zeros(SH, bool)
    known = np.zeros(SH, bool)
    L = np.zeros(SH, np.int8)
    for (x, y, z), v in blocks.items():
        n, pr = v[0], v[1] or {}
        sh = n.split(":")[1]
        i = (x - X0, y - Y0, z - Z0)
        known[i] = True
        e = LIGHT_EMIT.get(sh, 0)
        if "bulb" in sh and pr.get("lit") != "true":
            e = 0
        if sh == "candle" and pr.get("lit") == "true":
            e = 3 * int(pr.get("candles", 1))
        if e:
            L[i] = e
        elif is_solid(n) and sh not in ("air", "cave_air") and not sh.endswith("_slab") and "glass" not in sh:
            opaque[i] = True
    for lvl in range(15, 1, -1):
        m = (L == lvl)
        if not m.any():
            continue
        for ax in range(3):
            for d in (1, -1):
                upd = np.roll(m, d, axis=ax) & ~opaque & (L < lvl - 1)
                L[upd] = lvl - 1

    def spread(x, y, z, lvl):
        i0 = (x - X0, y - Y0, z - Z0)
        L[i0] = max(L[i0], lvl)
        q = [(i0, lvl)]
        while q:
            nq = []
            for (i, l) in q:
                for ax in range(3):
                    for d in (1, -1):
                        j = list(i)
                        j[ax] += d
                        j = tuple(j)
                        if not (0 <= j[ax] < SH[ax]) or opaque[j] or L[j] >= l - 1:
                            continue
                        L[j] = l - 1
                        if l - 1 > 1:
                            nq.append((j, l - 1))
            q = nq

    air = ~opaque
    stand = np.zeros(SH, bool)
    stand[:, 1:-1, :] = air[:, 1:-1, :] & opaque[:, :-2, :] & air[:, 2:, :] & known[:, :-2, :]
    cov = np.zeros(SH, bool)
    for k in range(2, 16):
        cov[:, :-k, :] |= opaque[:, k:, :]
    # only spaces a player can reach: flood the known open cells from the ones touching the open sky (unset cells
    # above the ground layer); sealed voids (generator casings, tower cores, roof spaces) stay dark
    openc = known & ~opaque
    sky = ~known
    sky[:, :1 - Y0, :] = False
    seed = np.zeros(SH, bool)
    for ax in range(3):
        for d in (1, -1):
            seed |= np.roll(sky, d, axis=ax)
    seed &= openc
    reach = seed.copy()
    q = [tuple(int(v) for v in i) for i in np.argwhere(seed)]
    while q:
        nq = []
        for i in q:
            for ax in range(3):
                for d in (1, -1):
                    j = list(i)
                    j[ax] += d
                    if not (0 <= j[ax] < SH[ax]):
                        continue
                    j = tuple(j)
                    if openc[j] and not reach[j]:
                        reach[j] = True
                        nq.append(j)
        q = nq
    reach |= sky
    cells = np.argwhere(stand & cov & (L < 8) & reach)
    # lattice points first (every 5 blocks), so the added lights fall in a regular pattern
    order = sorted(((int(a) + X0, int(b) + Y0, int(c) + Z0) for a, b, c in cells),
                   key=lambda p: (0 if (p[0] % 5 == 0 and p[2] % 5 == 0) else 1, p[1], p[0], p[2]))

    def ok_block(x, y, z):
        b = C.get(x, y, z) or ""
        return b and opaque[x - X0, y - Y0, z - Z0] and not any(k in b for k in NO_BULB) and (x, y, z) not in C.keep

    for (x, f, z) in order:
        if L[x - X0, f - Y0, z - Z0] >= 8:
            continue
        cy = f + 2
        while not opaque[x - X0, cy - Y0, z - Z0]:
            cy += 1
        if cy - f <= 5 and ok_block(x, cy, z):
            at = (x, cy, z)                          # low ceiling: a bulb set in it
        elif ok_block(x, f - 1, z):
            at = (x, f - 1, z)                       # tall hall: a bulb set in the floor
        else:
            continue
        C.bp.set(*at, BULB)
        opaque[at[0] - X0, at[1] - Y0, at[2] - Z0] = False
        spread(*at, 15)


def seal_caves(C):
    """The crust is hollow under the massif (unset cells, which the world's ground may or may not fill): wherever a
    built space (air, water, a partial block) touches that hollow from above the ground layer, the touching hollow cell
    becomes rock, so no room or stair leaks into a cave under the mountain."""
    bot = {}
    for (x, y, z) in C.bp.blocks:
        b = C.get(x, y, z)
        if b != AIR and not b.endswith(":air") and (x, z) in C.top:
            if y < bot.get((x, z), 999):
                bot[(x, z)] = y
    for (x, y, z) in list(C.bp.blocks):
        b = C.get(x, y, z)
        if any(k in b for k in FULL_W) and not any(k in b for k in PART_W):
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0)):
            n = (x + dx, y + dy, z + dz)
            if n[1] < 1 or n in C.bp.blocks or (n[0], n[2]) not in bot or n[1] >= bot[(n[0], n[2])]:
                continue
            C.bp.set(*n, rock(*n))


def scatter_rocks(C):
    """Boulders and snow patches on the natural slopes, scree at the feet of the cliffs."""
    rng = random.Random(51)
    for (x, z), t in sorted(C.top.items()):
        if C.kind[(x, z)] != "rock":
            continue
        h = hash01(x, z, 52)
        g = C.get(x, t, z)
        if not g or g == AIR or any(k in g for k in ("slab", "stairs", "wall", "fence", "chain", "bars", "water", "snow[",
                                                     "trapdoor", "rod", "lantern", "carpet", "leaves")):
            continue
        if h < 0.012 and C.free(x, t + 1, z):
            C.set(x, t + 1, z, rng.choice(("cobblestone", "andesite", "mossy_cobblestone", "stone")))
            if h < 0.005:
                C.set(x, t + 2, z, "cobblestone_slab[type=bottom,waterlogged=false]")
        elif h < 0.03 and C.free(x, t + 1, z) and t < 30:
            C.set(x, t + 1, z, "short_grass" if h < 0.024 else "fern")
        elif t >= 42 and h < 0.2 and C.free(x, t + 1, z):
            C.set(x, t + 1, z, "snow[layers=1]")


def parapet_walls(C, skip):
    """Crenellated walls along the plateau's and the terraces' rims (where the ground falls 3 or more), except in the
    ``skip`` predicates (gates, buildings, stairs)."""
    for (x, z), t in C.top.items():
        k = C.kind[(x, z)]
        if k not in ("plateau", "bastion", "barr", "obs"):
            continue
        drop = False
        for dx, dz in N4:
            tn = C.top.get((x + dx, z + dz))
            if tn is None or tn <= t - 3:
                drop = True
                break
        if not drop or any(f(x, z) for f in skip):
            continue
        if not C.free(x, t + 1, z) or (x, t + 1, z) in C.keep:
            continue
        C.set(x, t + 1, z, SB if hash3(x, t, z, 61) < 0.8 else CSB)
        if (x * 3 + z * 5) % 4 < 2 and C.free(x, t + 2, z) and (x, t + 2, z) not in C.keep:
            C.set(x, t + 2, z, SB_WALL)
        if (x * 7 + z * 11) % 23 == 0 and C.free(x, t + 2, z) and (x, t + 2, z) not in C.keep:
            C.set(x, t + 2, z, SB)
            C.set(x, t + 3, z, LANT)


# ------------------------------------------------------------------ the approach: camp, funicular, switchbacks
def tent(C, cx, cz, length=5, color="white_wool", axis="z"):
    """An A-frame canvas tent, open at its south (or east) end, a bedroll and a lantern inside."""
    hl = length // 2
    for i in range(-hl, hl + 1):
        for h in range(3):
            for sgn in (-1, 1):
                o = sgn * (2 - h)
                x, z = (cx + o, cz + i) if axis == "z" else (cx + i, cz + o)
                C.set(x, 1 + h, z, color)
        x, z = (cx, cz + i) if axis == "z" else (cx + i, cz)
        C.set(x, 3, z, color)
        for h in (1, 2):
            if i == hl:
                C.air(x, h, z)
    for i in range(-hl, hl):
        x, z = (cx, cz + i) if axis == "z" else (cx + i, cz)
        C.set(x, 1, z, "brown_carpet" if i % 2 else "light_gray_carpet")
        if axis == "z":
            C.set(cx - 1, 1, cz + i, "red_carpet")
            C.set(cx + 1, 1, cz + i, "red_carpet")
    x, z = (cx, cz - hl) if axis == "z" else (cx - hl, cz)
    C.set(x, 1, z, LANT)


def camp(C):
    """The mountaineers' camp on the flat ground south of the crag: tents round a fire, the waystone by the path,
    supply crates, a rack of ice axes and ropes, a wind sock, a signal mast, the funicular's lower station."""
    cx, cz = CAMP
    for (x, z) in disk_pts(cx, cz, 5.4):
        if C.kind.get((x, z)) == "camp":
            C.set(x, 0, z, "gravel" if hash01(x, z, 71) < 0.5 else "packed_mud")
    C.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((2, 0, "west"), (-2, 0, "east"), (0, 2, "north"), (0, -2, "south")):
        C.set(cx + dx, 1, cz + dz, stair("spruce_stairs", f))
    waystone(C, cx - 6, 1, cz - 8)
    C.set(cx - 6, 0, cz - 8, "polished_andesite")
    for (dx, dz) in N4:
        C.set(cx - 6 + dx, 0, cz - 8 + dz, PAND)
    tent(C, cx - 9, cz + 2, 5, "white_wool")
    tent(C, cx + 9, cz + 3, 5, "orange_wool")
    tent(C, cx - 1, cz + 10, 5, "light_gray_wool", axis="x")
    # supplies
    barrel(C, cx + 5, 1, cz - 4)
    barrel(C, cx + 5, 2, cz - 4)
    barrel(C, cx + 6, 1, cz - 4, "north")
    C.set(cx + 6, 1, cz - 5, "crafting_table")
    chest(C, cx - 4, 1, cz - 3, "east", "sts_camp")
    C.set(cx - 4, 1, cz - 2, "lectern[facing=east,has_book=false,powered=false]")
    C.set(cx + 4, 1, cz + 5, "smoker[facing=west,lit=true]")
    C.set(cx + 4, 1, cz + 6, "barrel[facing=up,open=false]")
    # the rack of ice axes and coiled ropes: a spruce frame with chains and lanterns
    for x in range(cx - 14, cx - 9):
        C.set(x, 1, cz - 6, "spruce_fence")
        C.set(x, 2, cz - 6, "spruce_slab[type=bottom,waterlogged=false]" if x % 2 else "spruce_fence")
    C.set(cx - 14, 3, cz - 6, LANT)
    C.set(cx - 10, 3, cz - 6, LANT)
    # the wind sock and the signal mast
    for y in range(1, 8):
        C.set(cx + 13, y, cz - 6, "spruce_fence" if y < 7 else "spruce_log[axis=y]")
    C.set(cx + 14, 7, cz - 6, "red_wool")
    C.set(cx + 15, 7, cz - 6, "white_wool")
    C.set(cx + 16, 6, cz - 6, "red_wool")
    C.set(cx + 13, 8, cz - 6, ROD_U)
    for (x, z) in ((cx - 4, cz - 9), (cx + 4, cz - 9), (cx - 12, cz + 8), (cx + 12, cz - 2)):
        lamp_post(C, x, 1, z, 2, LANT)


def funicular(C):
    """The funicular incline from the camp (feet 1, z 92) up to the forecourt (feet 15, z 64): a rail track on a
    stepped bed (rails on full blocks), a maintenance stair beside it, trestle piers to the slope, a cable car parked
    half way, the lower station shed and the upper station with its haul-cable drum."""
    z0, z1, f0, f1 = 92, 64, 1, 15
    n = z0 - z1
    # the track bed: two rails (x 23, 25) on dark iron, the cable groove between
    for i in range(n + 1):
        z = z0 - i
        h = f0 - 1 + i // 2                                  # bed top block (one up every two)
        nxt = f0 - 1 + (i + 1) // 2
        for x in range(21, 28):
            for y in range(h - 1, h + 1):
                C.set(x, y, z, IRON if x in (21, 27) else ("polished_blackstone" if y == h else DIB))
            fill_down(C, x, h - 2, z, DIB if (i % 6 == 0) else (lambda a, b, c: rock(a, b, c)))
            for y in range(h + 1, h + 5):
                if x not in (21, 27):
                    C.clear(x, y, z)
        for x in (23, 25):
            if i < n:
                shape = "ascending_north" if nxt > h else "north_south"
                C.set(x, h + 1, z, f"rail[shape={shape},waterlogged=false]")
        C.set(24, h + 1, z, CHAIN_Z if i % 2 == 0 else AIR)
        if i % 6 == 3:
            for x in (21, 27):
                C.set(x, h + 1, z, IRON_WALL)
                C.set(x, h + 2, z, LANT if i % 12 == 3 else IRON_WALL)
    # the maintenance stair east of the track
    walkway(C, [(29.5, f0, z0 + 0.0), (29.5, f1, z1 + 0.0)], width=3, full=SB, half=SB_SL, edge=(SB, SB_SL),
            support=lambda a, b, c: SB if hash3(a, b, c, 81) < 0.8 else MSB, lamp_every=6, rail_spec=SB_WALL,
            post=(SB, LANT))
    # the cable car parked half way: a brass-and-glass cabin on the rails
    zc = 78
    hc = f0 - 1 + (z0 - zc) // 2
    for x in range(22, 27):
        for z in range(zc - 2, zc + 3):
            for y in range(hc + 1, hc + 6):
                wall = x in (22, 26) or z in (zc - 2, zc + 2) or y in (hc + 1, hc + 5)
                if not wall:
                    C.air(x, y, z)
                    continue
                if y == hc + 1:
                    spec = TREAD
                elif y == hc + 5:
                    spec = COPPER if (x + z) % 2 else VERD
                elif y in (hc + 3, hc + 4) and not (x in (22, 26) and z in (zc - 2, zc + 2)):
                    spec = PANE
                else:
                    spec = BRASS
                C.set(x, y, z, spec)
    C.set(24, hc + 6, zc, GEAR)
    C.set(24, hc + 7, zc, CHAIN)
    C.set(24, hc + 2, zc, TABLE)
    C.set(23, hc + 2, zc + 1, stair("dark_oak_stairs", "north"))
    C.set(25, hc + 2, zc - 1, stair("dark_oak_stairs", "south"))
    C.set(24, hc + 4, zc, HANG_LAMP)
    # the cabin door toward the maintenance stair, a step up from the bed's edge
    C.set(26, hc + 2, zc, AIR)
    C.set(26, hc + 3, zc, AIR)
    C.set(27, hc + 1, zc, SB_SL + "[type=bottom,waterlogged=false]" if "[" not in SB_SL else SB_SL)
    for y in (hc + 2, hc + 3):
        C.clear(27, y, zc)
    # lower station: an open shed of iron columns and a copper roof over the track's foot
    for z in range(z0 + 1, z0 + 8):
        for x in range(20, 33):
            C.set(x, 0, z, TREAD if 22 <= x <= 26 else "polished_andesite")
            for y in range(1, 6):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
        for x in (20, 32):
            if z in (z0 + 1, z0 + 4, z0 + 7):
                for y in range(1, 6):
                    C.set(x, y, z, IRON if y < 5 else BRASS)
    for z in range(z0, z0 + 9):
        for x in range(19, 34):
            C.set(x, 6, z, CU_EX if (x + z) % 3 else CUT_CU)
    C.set(24, 5, z0 + 4, HANG_LAMP)
    C.set(30, 5, z0 + 4, HANG_LAMP)
    for x in (23, 25):
        for z in range(z0 + 1, z0 + 6):
            C.set(x, 1, z, "rail[shape=north_south,waterlogged=false]")
    C.set(24, 1, z0 + 6, IRON)
    C.set(30, 1, z0 + 6, "lectern[facing=north,has_book=false,powered=false]")
    barrel(C, 31, 1, z0 + 6)
    # upper station: the haul-cable drum (a gear wheel on an axle) in a brass frame on the forecourt
    for z in range(55, 64):
        for x in range(20, 33):
            if C.get(x, BT, z) is not None:
                C.set(x, BT, z, TREAD if 22 <= x <= 26 else PAND)
    for (x, z) in ((20, 55), (32, 55), (20, 62), (32, 62)):
        for y in range(BT + 1, BT + 7):
            C.set(x, y, z, IRON if y < BT + 6 else BRASS)
    for x in range(19, 34):
        for z in range(54, 64):
            C.set(x, BT + 7, z, CU_EX if (x + z) % 3 else CUT_CU)
    for dy in range(-3, 4):
        for dz in range(-3, 4):
            if 2.2 < math.hypot(dy, dz) <= 3.4:
                C.set(24, BT + 4 + dy, 58 + dz, GEAR)
            elif math.hypot(dy, dz) < 1:
                C.set(24, BT + 4 + dy, 58 + dz, BRASS)
    for x in range(21, 28):
        if x != 24:
            C.set(x, BT + 4, 58, IRON)
    C.set(30, BT + 1, 57, GAUGE)
    C.set(30, BT + 2, 57, VALVE)
    C.set(30, BT + 1, 58, "lever[face=floor,facing=north,powered=false]")
    C.set(26, BT + 6, 60, HANG_LAMP)


SWITCH = [[(-2.0, 1.0, 84.0), (-30.0, 7.5, 84.0), (-34.0, 7.5, 84.0)],
          [(-34.0, 7.5, 84.0), (-34.0, 7.5, 78.0), (-12.0, 12.5, 74.0), (-10.0, 12.5, 72.0)],
          [(-10.0, 12.5, 72.0), (-10.0, 15.0, 62.0)]]


def switchbacks(C):
    """The switchback stair on the crag's south-west face: three legs of stone-brick ramp on battered retaining walls,
    a stone parapet with lanterns, a landing at each turn."""
    def wall_stone(x, y, z):
        h = hash3(x, y, z, 91)
        return MSB if (y <= 2 and h < 0.6) else (CSB if h < 0.1 else SB)
    for leg in SWITCH:
        walkway(C, leg, width=3, full=SB, half=SB_SL, edge=(PAND, PAND_SL), support=wall_stone, lamp_every=7,
                rail_spec=SB_WALL, post=(SB, LANT))


# ------------------------------------------------------------------ the gate bastion
def bastion_stone(x, y, z):
    """Bastion masonry: dark deepslate bricks low down, stone bricks above, a few cracked and mossy."""
    h = hash3(x, y, z, 101)
    j = int((hash01(x // 3, z // 3, 102) - 0.5) * 3)
    if y + j < BT + 4:
        return DSB if h < 0.8 else ("cracked_deepslate_bricks" if h < 0.9 else PDS)
    return SB if h < 0.82 else (CSB if h < 0.92 else MSB)


def drum_tower(C, cx, cz, r, y0, y1):
    """A round flanking tower: battered base, arrow loops, a machicolated top, a copper cone with a lightning rod."""
    for (x, z) in disk_pts(cx, cz, r + 1.5):
        d = math.hypot(x - cx, z - cz)
        for y in range(y0, y1 + 1):
            rr = r + (1.0 if y < y0 + 6 else 0.0) + (0.8 if y >= y1 - 1 else 0.0)
            if d > rr + 0.01:
                continue
            if d > rr - 1.6:
                spec = bastion_stone(x, y, z)
                if y in (y1 - 2,):
                    spec = DIB
                a = math.degrees(math.atan2(z - cz, x - cx)) % 360
                if (y - y0) % 7 in (3, 4) and round(a) % 60 < 6 and y < y1 - 3:
                    spec = "iron_bars"
                C.set(x, y, z, spec)
            else:
                C.air(x, y, z)
    for (x, z) in disk_pts(cx, cz, r + 0.8):
        C.set(x, y1 - 3, z, SB if math.hypot(x - cx, z - cz) < r - 0.6 else C.get(x, y1 - 3, z) or SB)
    # crenels round the top
    for (x, z) in disk_pts(cx, cz, r + 0.8):
        d = math.hypot(x - cx, z - cz)
        if d > r - 0.2 and (x + z) % 2 == 0:
            C.set(x, y1 + 1, z, SB_WALL)
    # the cone
    for k in range(0, int(r) + 6):
        rr = r + 0.3 - k * 0.75
        if rr < 0.3:
            break
        for (x, z) in disk_pts(cx, cz, rr):
            if math.hypot(x - cx, z - cz) > rr - 1.2:
                C.set(x, y1 + 2 + k, z, CU_OX if (k % 3) else CUT_OX)
    yt = y1 + 2 + int((r + 0.3) / 0.75)
    C.set(cx, yt, cz, GILD)
    C.set(cx, yt + 1, cz, ROD_U)


def bastion(C):
    """The gate bastion: a masonry block on the bastion terrace between the forecourt and the court, two drum towers
    flanking the gate, the great gate (closed, a wicket open in it) and the vaulted passage (compression), the stair up
    to the court, the guard rooms, the postern stair and its one-way iron door, the rampart walk on top."""
    x0, z0, x1, z1 = BAS
    yr = 34                                             # roof block y (rampart walk feet 35)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(BT - 2, yr + 1):
                edge = x in (x0, x1) or z in (z0, z1) or (z >= z1 - 2)
                if y == yr or edge or y < BT + 1:
                    spec = bastion_stone(x, y, z)
                    if y == yr:
                        spec = SB if (x + z) % 5 else CSB
                    if y == BT + 10 and edge:
                        spec = DIB
                    C.set(x, y, z, spec)
                else:
                    C.set(x, y, z, bastion_stone(x, y, z))
    # crenellated rampart
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                C.set(x, yr + 1, z, SB)
                if (x + z) % 2 == 0:
                    C.set(x, yr + 2, z, SB_WALL)
    # buttresses on the front face (every 7, the gate bay wider)
    for x in (-21, -17, 17, 21):
        for y in range(BT - 2, yr - 2):
            for dz in (1, 2):
                C.set(x, y, z1 + dz, bastion_stone(x, y, z1 + dz) if y < yr - 6 + dz * 2 else AIR)
        C.set(x, yr - 6 + 4, z1 + 2, stair(SB_ST, "north"))
    for sx in (-10, 10):
        drum_tower(C, sx, z1 + 1, 4, BT - 2, yr + 6)
    # --- the gate: a great arch 7 wide, 10 high, the closed gate leaves set back in it, the wicket open
    for x in range(-3, 4):
        for y in range(BT + 1, BT + 11):
            arch_top = BT + 10 - (1 if abs(x) == 3 else 0)
            for z in (z1 - 2, z1 - 1, z1):
                if y <= arch_top:
                    C.air(x, y, z)
    for x in range(-4, 5):
        C.set(x, BT + 11, z1, ENGR if abs(x) < 4 else DIB)
        C.set(x, BT + 12, z1, DIB)
    for x in range(-3, 4):                              # the leaves (iron and spruce), set back at z1 - 1
        for y in range(BT + 1, BT + 10):
            if abs(x) <= 1 and y <= BT + 4:
                continue                                # the wicket
            C.set(x, y, z1 - 1, IRON if (y - BT) % 3 == 0 or abs(x) == 3 else "spruce_planks")
    for x in range(-1, 2):
        C.set(x, BT + 5, z1 - 1, BRASS)
    C.set(-4, BT + 7, z1 + 1, LANT)
    C.set(4, BT + 7, z1 + 1, LANT)
    # --- the passage north (x -1..1, z1-3 .. 38), then the stair to the court (treads z 37 .. 28)
    for z in range(38, z1 - 1):
        for x in range(-1, 2):
            C.set(x, BT, z, TREAD if x == 0 else PAND)
            for y in range(BT + 1, BT + 5):
                C.clear(x, y, z)
            reg(x, z, BT + 1)
        for x in (-2, 2):
            for y in range(BT + 1, BT + 5):
                C.set(x, y, z, DIB if y == BT + 1 else bastion_stone(x, y, z))
        if z % 3 == 0:
            for x in range(-1, 2):
                C.set(x, BT + 5, z, DIB)
            C.set(-1, BT + 4, z, stair(DIB_ST, "east", "top"))
            C.set(1, BT + 4, z, stair(DIB_ST, "west", "top"))
    for z in (40, 45):
        hang(C, 0, BT + 4, z, HANG_LAMP)
    stair_run(C, [(-1, 37), (0, 37), (1, 37)], "north", 10, BT, spec=SB_ST, support=SB)
    for z in range(27, 38):
        for x in (-2, 2):
            for y in range(BT + 1, G + 6):
                if C.get(x, y, z) is None or not C.solid(x, y, z):
                    C.set(x, y, z, bastion_stone(x, y, z))
    for z in range(28, 38):
        if z % 3 == 1:
            C.set(-2, BT + (38 - z) + 3, z, "lantern[hanging=false,waterlogged=false]")
    # the north mouth onto the court: an arch in the bastion's north wall
    for x in range(-1, 2):
        for y in range(G + 1, G + 5):
            C.clear(x, y, 28)
    for x in range(-2, 3):
        C.set(x, G + 5, 28, ENGR if x == 0 else DIB)
    # --- the west guard room (x -18 .. -6) and the tunnel to the battery vaults
    gx0, gx1, gz0, gz1 = -18, -6, 31, 45
    box(C, gx0 - 1, BT + 1, gz0 - 1, gx1 + 1, BT + 6, gz1 + 1, lambda a, b, c: bastion_stone(a, b, c),
        floor=lambda a, b: SB if (a + b) % 4 else PAND, ceil=DIB)
    for z in range(40, 43):
        for y in range(BT + 1, BT + 4):
            C.clear(-2, y, z)
            C.clear(-3, y, z)
            C.clear(-4, y, z)
            C.clear(-5, y, z)
        for x in (-5, -4, -3, -2):
            C.set(x, BT, z, PAND)
            reg(x, z, BT + 1)
    C.set(-14, BT + 1, 32, "smithing_table")
    C.set(-13, BT + 1, 32, "grindstone[face=floor,facing=north]")
    C.set(-12, BT + 1, 32, stair("spruce_stairs", "south"))
    C.set(-11, BT + 1, 32, TABLE)
    C.set(-10, BT + 1, 32, stair("spruce_stairs", "south"))
    for z in (36, 38, 40, 42, 44):
        C.set(gx0, BT + 1, z, "barrel[facing=east,open=false]")
        C.set(gx0, BT + 2, z, IRON)
    chest(C, gx0, BT + 1, 34, "east", "sts_gate")
    spawner(C, -12, BT + 1, 40, MOB_GUNNER)
    for (x, z) in ((-14, 36), (-9, 42)):
        hang(C, x, BT + 5, z, HANG_LAMP)
    # tunnel: from the guard room's north-west (x -15..-13, z 31) north down to the vaults (feet 11 at z 23)
    pts = [(-14.0, BT + 1.0, 31.0), (-14.0, BT + 1.0, 30.0), (-14.0, 11.0, 22.0)]
    walkway(C, pts, width=3, full=SB, half=SB_SL, rails=False, head=4)
    for z in range(21, 32):
        for x in (-16, -12):
            for y in range(10, BT + 6):
                if C.free(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, bastion_stone(x, y, z))
        for x in range(-16, -11):
            yt = 11 + max(0, min(4, (z - 22) // 2)) + 4
            for y in range(yt, yt + 2):
                if C.free(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, SB)
        if z % 4 == 0:
            C.set(-12, 11 + max(0, min(4, (z - 22) // 2)) + 2, z, "lantern[hanging=false,waterlogged=false]"
                  if C.free(-12, 13, z) else SB)
    # --- the postern: from the court (door at x 17, z 28) a stair down south to feet 15, a corridor to the iron door
    #     in the front wall at z1 (lever on the inside only: a shortcut from the court to the forecourt)
    for x in range(16, 19):
        for y in range(G + 1, G + 5):
            C.clear(x, y, 28)
    stair_run(C, [(16, 38), (17, 38), (18, 38)], "north", 10, BT, spec=SB_ST, support=SB)
    for z in range(38, z1):
        for x in range(16, 19):
            C.set(x, BT, z, PAND)
            for y in range(BT + 1, BT + 5):
                C.clear(x, y, z)
            reg(x, z, BT + 1)
    for z in range(27, z1):
        for x in (15, 19):
            for y in range(BT + 1, G + 6):
                if not C.solid(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, bastion_stone(x, y, z))
    C.keep.discard((17, BT + 1, z1))
    C.keep.discard((17, BT + 2, z1))
    iron_door(C, 17, BT + 1, z1, "south")
    for x in (16, 18):
        for y in (BT + 1, BT + 2, BT + 3):
            C.set(x, y, z1, DIB)
    C.set(17, BT + 3, z1, DIB)
    lever(C, 16, BT + 2, z1 - 1, "north")
    for x in range(16, 19):
        C.air(x, BT + 1, z1 + 1)
        C.air(x, BT + 2, z1 + 1)
    hang(C, 17, BT + 4, 44, HANG_LAMP)
    # the east guard room (x 4 .. 12): the armoury, its door off the passage
    box(C, 3, BT + 1, 30, 13, BT + 6, 45, lambda a, b, c: bastion_stone(a, b, c), floor=PAND, ceil=DIB)
    for y in range(BT + 1, BT + 4):
        for z in range(40, 43):
            C.clear(2, y, z)
            C.clear(3, y, z)
    for z in range(40, 43):
        C.set(2, BT, z, PAND)
        C.set(3, BT, z, PAND)
    for z in (32, 34, 36):
        C.set(12, BT + 1, z, "barrel[facing=west,open=false]")
        C.set(12, BT + 2, z, "iron_bars")
    C.set(6, BT + 1, 44, "anvil[facing=east]")
    C.set(7, BT + 1, 44, "grindstone[face=floor,facing=north]")
    C.set(9, BT + 1, 44, "smithing_table")
    chest(C, 12, BT + 1, 43, "west", "sts_gate")
    for x in range(5, 11, 2):
        C.set(x, BT + 1, 31, "barrel[facing=south,open=false]")
    hang(C, 8, BT + 5, 37, HANG_LAMP)
    spawner(C, 8, BT + 1, 38, MOB_AUTO)
    # rampart access from the court: a stair up the bastion's north face (x -12 .. -10)
    stair_run(C, [(-12, 27), (-11, 27), (-10, 27)], "south", 10, G, spec=SB_ST, support=SB)
    for z in range(27, 37):
        for x in (-13, -9):
            if not C.solid(x, G + 1 + (z - 27), z):
                C.set(x, G + 1 + (z - 27), z, SB)
                C.set(x, G + 2 + (z - 27), z, SB_WALL)


# ------------------------------------------------------------------ the dynamo court
def court(C):
    """The court's paving round the spire: concentric bands of polished andesite and stone brick, tread-plate lanes to
    the doors, the hub waystone on a brass plinth, transformer kiosks, insulator posts, lamp posts, the cooling
    pond under the slide's waterfall, a cart of coils."""
    for (x, z), t in C.top.items():
        if C.kind[(x, z)] != "plateau" or t != G:
            continue
        if not C.solid(x, G, z):
            continue
        d = math.hypot(x - 0, z - 2)
        ds = dsp(x, z)
        if d > 34 and abs(z + 9) > 1:
            continue
        if ds <= 13:
            spec = DSB if round(ds) % 3 else PDS
        elif round(ds) % 6 == 0:
            spec = SB
        elif abs(x) <= 1 or abs(z + 8) <= 1 or abs(z - 10) <= 1:
            spec = TREAD
        else:
            spec = PAND if hash01(x, z, 111) < 0.75 else "smooth_stone"
        C.set(x, G, z, spec)
    # the hub waystone on a plinth
    wx, wz = 8, 16
    for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        C.set(wx + dx, G, wz + dz, ENGR if (dx or dz) else BRASS)
    waystone(C, wx, G + 1, wz)
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        lamp_post(C, wx + dx, G + 1, wz + dz, 2, LANT)
    # transformer kiosks: copper boxes with insulator stacks and a gauge
    for (kx, kz) in ((-12, 20), (22, 20)):
        for x in range(kx - 1, kx + 2):
            for z in range(kz - 1, kz + 2):
                for y in range(G + 1, G + 4):
                    C.set(x, y, z, (COPPER if y < G + 3 else VERD) if (x, z) != (kx, kz + 1) or y > G + 2
                          else GAUGE)
        for y in range(G + 4, G + 7):
            for (dx, dz) in ((-1, 0), (1, 0)):
                C.set(kx + dx, y, kz + dz, "white_terracotta" if y % 2 else "calcite")
        C.set(kx - 1, G + 7, kz, ROD_U)
        C.set(kx + 1, G + 7, kz, ROD_U)
        C.set(kx, G + 4, kz, BULB)
    # insulator posts and lamp posts round the court
    for k in range(10):
        a = 18 + 36 * k
        x, z = polar(19, a)
        x, z = round(x), round(z)
        if C.kind.get((x, z)) != "plateau" or not C.free(x, G + 1, z) or (x, G + 1, z) in C.keep:
            continue
        if k % 2:
            lamp_post(C, x, G + 1, z, 3)
        else:
            C.set(x, G + 1, z, IRON)
            for y in range(G + 2, G + 5):
                C.set(x, y, z, "white_terracotta" if y % 2 else IRON_WALL)
            C.set(x, G + 5, z, BULB)
    # the cooling pond
    x0, z0, x1, z1 = POND
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            if edge:
                C.set(x, G, z, PAND)
                C.set(x, G + 1, z, SB_WALL if (x + z) % 3 else LANT)
            else:
                C.set(x, G - 3, z, "clay")
                for y in range(G - 2, G + 1):
                    C.set(x, y, z, WATER)
    # a cart of coil spools and crates by the dynamo house
    for (x, z) in ((20, 2), (21, 2), (20, 3)):
        C.set(x, G + 1, z, CU_BLOCK if (x + z) % 2 else CUT_CU)
    barrel(C, 21, G + 1, 3)
    C.set(19, G + 1, 4, "barrel[facing=up,open=false]")
    C.set(19, G + 2, 4, "barrel[facing=up,open=false]")
    spawner(C, -14, G + 1, 8, MOB_DRONE)


# ------------------------------------------------------------------ the dynamo house
def brick_wall(x, y, z, y0):
    h = hash3(x, y, z, 121)
    if y < y0 + 3:
        return SB if h < 0.85 else CSB
    return "bricks" if h < 0.92 else "mud_bricks"


def generator(C, gx, gz, gy=30, r=3, half=4):
    """A giant dynamo, axis along z: an iron cradle, copper windings in verdigris bands, brass end caps, the iron
    shaft and a flywheel (a toothed brass disc) at its north end, cable conduits to the floor."""
    for z in range(gz - half - 3, gz + half + 2):
        C.set(gx, gy, z, IRON)                                   # the shaft
    for dx in range(-r - 1, r + 2):
        for dy in range(-r - 1, r + 2):
            rr = math.hypot(dx, dy)
            if rr > r + 0.45:
                continue
            for z in range(gz - half, gz + half + 1):
                cap = z in (gz - half, gz + half)
                if cap:
                    spec = BRASS if rr > 1.2 else GEAR
                elif rr > r - 0.6:
                    spec = VERD if (z - gz) % 3 == 0 else COPPER
                else:
                    continue
                C.set(gx + dx, gy + dy, z, spec)
    # cradle
    for z in (gz - half + 1, gz + half - 1):
        for dx in range(-r, r + 1):
            for y in range(G + 1, gy - r + 1):
                if abs(dx) >= r - 1 or y == G + 1:
                    C.set(gx + dx, y, z, IRON)
    # flywheel at the north end
    fz = gz - half - 3
    R = r + 1.2
    for dx in range(-7, 8):
        for dy in range(-7, 8):
            rr = math.hypot(dx, dy)
            y = gy + dy
            if y <= G or rr > R + 0.5:
                continue
            th = math.degrees(math.atan2(dy, dx))
            if rr > R - 0.6:
                if int(th // 15) % 2 == 0:
                    C.set(gx + dx, y, fz, GEAR)
            elif rr > R - 1.6 or rr < 1.2:
                C.set(gx + dx, y, fz, BRASS)
            elif abs(math.sin(math.radians(th) * 3)) < 0.2:
                C.set(gx + dx, y, fz, IRON)
    # terminals on top, conduits
    for dz in (-2, 2):
        C.set(gx, gy + r + 1, gz + dz, ROD_U)
    C.set(gx, gy + r + 1, gz, BULB)


def dynamo_house(C):
    """The dynamo house: a red-brick engine hall with dark iron pilasters and tall arched windows, a copper barrel
    roof on brass ribs; three giant generators, a control gallery on the north wall, a door to the workshop."""
    x0, z0, x1, z1 = DYN
    yw = 40                                          # wall top
    zc = (z0 + z1) / 2.0
    hw = (z1 - z0) / 2.0
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, G, z, TREAD if (x - x0) % 9 in (4, 5) or abs(z + 9) <= 1 else PAND)
            for y in range(G + 1, yw + 1):
                if edge:
                    pil = (x - x0) % 6 == 0 if z in (z0, z1) else (z - z0) % 6 == 0
                    spec = IRON if pil else brick_wall(x, y, z, G + 1)
                    if y in (G + 12, yw):
                        spec = SB
                    win = not pil and (G + 4 <= y <= G + 12) and (
                        ((x - x0) % 6 in (2, 3, 4) and z in (z0, z1)) or ((z - z0) % 6 in (2, 3, 4) and x in (x0, x1)))
                    if win:
                        top = G + 12 - (0 if ((x - x0) % 6 == 3 or (z - z0) % 6 == 3) else 1)
                        spec = AMBER if y < top else spec
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            # the barrel roof
            dzr = (z - zc) / (hw + 0.5)
            if abs(dzr) <= 1:
                yr = yw + int(round(8 * math.sqrt(max(0.0, 1 - dzr * dzr))))
                rib = (x - x0) % 6 == 0
                for y in range(yw + 1, yr + 1):
                    if y == yr or edge:
                        C.set(x, y, z, BRASS if rib else (VERD if hash01(x, z, 122) < 0.6 else COPPER))
                    else:
                        C.air(x, y, z)
                if not rib and y == yr and abs(dzr) < 0.25 and (x - x0) % 6 == 3:
                    C.set(x, yr, z, GLASS)
    # doors: west to the court (5 x 6), north to the workshop (3 x 4)
    for z in range(-11, -6):
        for y in range(G + 1, G + 7):
            C.clear(x0, y, z)
    for z in range(-12, -5):
        C.set(x0, G + 7, z, ENGR if z == -9 else SB)
    for x in range(40, 43):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z0)
    # the three generators
    for gx in (35, 44, 53):
        generator(C, gx, -5)
    # control gallery on the north wall (feet 33): a catwalk on brackets, a stair up from the west
    for x in range(x0 + 1, x1):
        for z in (z0 + 1, z0 + 2):
            C.set(x, G + 8, z, TREAD)
            reg(x, z, G + 9)
        if C.free(x, G + 9, z0 + 3):
            railing(C, x, G + 9, z0 + 3, "south")
        if (x - x0) % 4 == 0:
            C.set(x, G + 7, z0 + 1, stair(IRON_SLAB.replace("_slab", "_stairs"), "south", "top"))
    for x in range(x0 + 1, x1):
        if x % 3 == 0:
            C.set(x, G + 9, z0 + 1, GAUGE if x % 2 else "lever[face=floor,facing=south,powered=false]")
    for x in range(x0 + 2, x1 - 1, 5):
        C.set(x, G + 10, z0, GAUGE)
        C.set(x + 1, G + 10, z0, BULB)
    stair_run(C, [(x0 + 1, -12), (x0 + 2, -12)], "north", 8, G, spec=IRON_SLAB.replace("_slab", "_stairs"),
              support=IRON)
    # lamps from the roof
    for x in range(x0 + 3, x1, 6):
        for z in (-15, -9, -1, 5):
            hang(C, x, G + 13 if abs(z + 9) > 3 else G + 15, z, HANG_LAMP, reach=24)
    for x in (39, 49):
        hang(C, x + 0, G + 16, -9, CHANDELIER, reach=24)
    chest(C, x1 - 1, G + 1, z1 - 1, "west", "sts_dynamo")
    chest(C, x0 + 2, G + 9, z0 + 1, "south", "sts_dynamo")
    spawner(C, 40, G + 1, 3, MOB_AUTO)
    spawner(C, 58, G + 1, -15, MOB_MITE)
    # workbenches and spares along the south wall
    for x in range(x0 + 2, x1 - 1, 3):
        C.put(x, G + 1, z1 - 1, ("crafting_table", "smithing_table", "barrel[facing=up,open=false]", PIPES,
                                 "anvil[facing=east]")[(x // 3) % 5])


def workshop(C):
    """The coil workshop: a slate-roofed brick shed; a winding lathe with a half-wound giant coil on its axle, spools
    of copper, wire racks, benches, a forge corner; doors west (court), south (dynamo house), north (pinnacle)."""
    x0, z0, x1, z1 = WSHOP
    yw = G + 9
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, G, z, PARQ if not edge else SB)
            for y in range(G + 1, yw + 1):
                if edge:
                    pil = (x - x0) % 6 == 0 if z in (z0, z1) else z in (z0, z1)
                    spec = DIB if pil else brick_wall(x, y, z, G + 1)
                    if y == yw:
                        spec = SB
                    if not pil and y in (G + 3, G + 4, G + 5) and z in (z0, z1) and (x - x0) % 6 in (2, 3, 4):
                        spec = PANE
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
    # gable roof (ridge along x)
    zc = (z0 + z1) / 2.0
    hw = (z1 - z0) // 2 + 1
    for k in range(hw + 1):
        y = yw + 1 + k
        for x in range(x0 - 1, x1 + 2):
            for z in (z0 - 1 + k, z1 + 1 - k):
                if z0 - 1 + k > z1 + 1 - k:
                    continue
                C.set(x, y, z, stair(SLATE_ST, "south" if z < zc else "north") if z0 - 1 + k != z1 + 1 - k
                      else SLATE)
            if x in (x0, x1):
                for z in range(z0 + k, z1 - k + 1):
                    C.set(x, y, z, brick_wall(x, y, z, 0))
            else:
                for z in range(z0 + k, z1 - k + 1):
                    C.air(x, y, z)
    for x in range(x0 + 2, x1 - 1, 4):
        C.set(x, yw, (z0 + z1) // 2, IRON)
    # doors
    for z in range(-31, -28):
        for y in range(G + 1, G + 5):
            C.clear(x0, y, z)
    for x in range(40, 43):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z1)
            C.clear(x, y, z1 + 1)
        C.set(x, G, z1 + 1, TREAD)
        C.set(x, G + 5, z1 + 1, SB)
        for y in range(G + 1, G + 5):
            C.set(39, y, z1 + 1, SB)
            C.set(43, y, z1 + 1, SB)
    for x in range(41, 44):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z0)
    # the winding lathe: two iron stands, a brass axle, a copper coil half wound
    lz = -30
    for x in (33, 45):
        for y in range(G + 1, G + 5):
            C.set(x, y, lz, IRON)
    for x in range(34, 45):
        C.set(x, G + 4, lz, BRASS)
    for x in range(36, 43):
        for dy in range(-2, 3):
            for dz in range(-2, 3):
                rr = math.hypot(dy, dz)
                if 1.0 < rr <= 2.5 and (x < 41 or rr < 1.8):
                    C.set(x, G + 4 + dy, lz + dz, COPPER if (x + dy) % 2 else CU_BLOCK)
    C.set(46, G + 1, lz, "lever[face=floor,facing=east,powered=false]")
    C.set(46, G + 2, lz, GAUGE)
    # spools and racks
    for (x, z) in ((31, -26), (31, -27), (32, -26), (50, -34), (49, -34), (50, -33)):
        C.set(x, G + 1, z, CU_BLOCK if (x + z) % 2 else CUT_CU)
    C.set(31, G + 2, -26, CUT_CU)
    for x in range(30, 37):
        C.set(x, G + 4, z0 + 1, CHAIN_X)
    for x in (30, 36):
        C.set(x, G + 3, z0 + 1, IRON_WALL)
        C.set(x, G + 2, z0 + 1, IRON_WALL)
        C.set(x, G + 1, z0 + 1, IRON)
    for x in range(31, 36):
        C.set(x, G + 3, z0 + 1, CHAIN)
    # benches and the forge corner
    for (x, spec) in ((44, "crafting_table"), (45, "smithing_table"), (46, "anvil[facing=north]"),
                      (47, "grindstone[face=floor,facing=north]"), (48, "fletching_table")):
        C.set(x, G + 1, z1 - 1, spec)
    C.set(51, G + 1, -26, "blast_furnace[facing=west,lit=true]")
    C.set(51, G + 1, -27, "smoker[facing=west,lit=true]")
    for y in range(G + 1, yw + 9):
        C.set(51, y, -28, "bricks" if y < yw + 1 else (SB if y < yw + 8 else "campfire[facing=north,lit=true,"
                                                                                "signal_fire=false,waterlogged=false]"))
    C.set(50, G + 1, -26, "cauldron")
    chest(C, 30, G + 1, -34, "east", "sts_workshop")
    for x in (34, 40, 46):
        hang(C, x, G + 7, -30 if x != 40 else -27, HANG_LAMP)
    hang(C, 37, G + 7, -26, HANG_LAMP)
    spawner(C, 38, G + 1, -26, MOB_SPIDER)


# ------------------------------------------------------------------ the capacitor hall
def hall_stone(x, y, z):
    h = hash3(x, y, z, 131)
    if y < G + 4:
        return DSB if h < 0.85 else "cracked_deepslate_bricks"
    return SB if h < 0.85 else (CSB if h < 0.93 else "andesite")


def leyden_jar(C, cx, cz, yf, r=2.5, h=9):
    """A giant Leyden jar: a glass cylinder coated with copper foil inside and out to two thirds of its height, a
    dark stopper, a brass rod through it with a copper ball, a chain inside down to a glowing bottom."""
    foil = yf + int(h * 0.6)
    for (x, z) in disk_pts(cx, cz, r + 0.3):
        d = math.hypot(x - cx, z - cz)
        for y in range(yf, yf + h):
            if d > r - 0.7:
                C.set(x, y, z, (CU_BLOCK if (y - yf) % 3 else CUT_CU) if y < foil else
                      (BLUE_GL if y < yf + h - 1 else GLASS))
            elif y == yf:
                C.set(x, y, z, "sea_lantern" if d < 1.2 else CU_EX)
            else:
                C.air(x, y, z)
        C.set(x, yf + h, z, IRON if d > r - 0.7 else DIB)
    C.set(cx, yf - 1, cz, IRON)
    for y in range(yf + 1, yf + h):
        C.set(cx, y, cz, CHAIN)
    C.set(cx, yf + h + 1, cz, BRASS)
    C.set(cx, yf + h + 2, cz, ROD_U)
    C.set(cx, yf + h + 3, cz, BULB)


def capacitor_hall(C):
    """The capacitor hall: a fortified hall (battered deepslate plinth, stone walls, buttresses, corner turrets with
    copper cones, a crenellated roof walk); inside two rows of giant Leyden jars on brass plinths, busbars over the
    aisle, the stair along the north wall up to the roof walk; the covered bridge from the roof into coil ring 1."""
    x0, z0, x1, z1 = CAP
    yr = G + 14                                   # roof block y 38 (walk feet 39)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            aisle = abs(x + 44) <= 2
            C.set(x, G, z, TREAD if aisle else (PDS if (x + z) % 2 else DSB))
            for y in range(G + 1, yr):
                if edge:
                    spec = hall_stone(x, y, z)
                    if y == G + 8:
                        spec = DIB
                    slit = y in (G + 9, G + 10, G + 11) and ((z - z0) % 8 == 4 if x in (x0, x1) else
                                                            (x - x0) % 8 == 4)
                    if slit:
                        spec = "iron_bars"
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            C.set(x, yr, z, SB if not edge else DIB)
            if edge:
                C.set(x, yr + 1, z, SB)
                if (x + z) % 2 == 0:
                    C.set(x, yr + 2, z, SB_WALL)
            else:
                reg(x, z, yr + 1)
    # battered plinth and buttresses
    for x in range(x0 - 1, x1 + 2):
        for z in (z0 - 1, z1 + 1):
            for y in range(G - 2, G + 3):
                C.set(x, y, z, hall_stone(x, y, z) if y < G + 2 else stair(DSB_ST, "north" if z == z1 + 1 else
                                                                           "south"))
    for z in range(z0 - 1, z1 + 2):
        for x in (x0 - 1,):
            for y in range(G - 2, G + 3):
                C.set(x, y, z, hall_stone(x, y, z) if y < G + 2 else stair(DSB_ST, "east"))
    for z in range(z0 + 4, z1 - 2, 8):
        for x in (x0 - 2, x0 - 1):
            for y in range(G - 2, yr - (2 if x == x0 - 2 else 0)):
                C.set(x, y, z, hall_stone(x, y, z))
    for x in range(x0 + 4, x1 - 2, 8):
        for z in (z0 - 2, z0 - 1, z1 + 1, z1 + 2):
            if z in (z1 + 1, z1 + 2) or abs(x + 40) > 2:
                for y in range(G - 2, yr - (2 if z in (z0 - 2, z1 + 2) else 0)):
                    C.set(x, y, z, hall_stone(x, y, z))
    # corner turrets
    for (tx, tz) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
        for (x, z) in disk_pts(tx, tz, 3.4):
            d = math.hypot(x - tx, z - tz)
            for y in range(G - 2, yr + 6):
                if d > 2.2:
                    C.set(x, y, z, hall_stone(x, y, z) if y != yr + 3 else DIB)
                elif y >= yr:
                    C.air(x, y, z) if y > yr else C.set(x, y, z, SB)
        for (x, z) in disk_pts(tx, tz, 3.6):
            if math.hypot(x - tx, z - tz) > 2.6 and (x + z) % 2 == 0:
                C.set(x, yr + 6, z, SB_WALL)
        for k in range(6):
            for (x, z) in disk_pts(tx, tz, 3.0 - k * 0.55):
                if math.hypot(x - tx, z - tz) > 2.0 - k * 0.55:
                    C.set(x, yr + 7 + k, z, CU_OX if k % 2 else CUT_OX)
        C.set(tx, yr + 13, tz, ROD_U)
        C.set(tx, yr + 1, tz, LANT)
    # doors: east to the court (5 x 6, a portal of dark iron), north to the barracks stair (3 x 4)
    for z in range(-12, -7):
        for y in range(G + 1, G + 7):
            C.clear(x1, y, z)
    for z in range(-13, -6):
        C.set(x1, G + 7, z, ENGR if z == -10 else DIB)
        C.set(x1 + 1, G + 7, z, DIB)
    for z in (-13, -7):
        for y in range(G + 1, G + 7):
            C.set(x1 + 1, y, z, DIB)
    for x in range(-41, -38):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z0)
    # the jars: two rows on brass plinths
    for jx in (-53, -35):
        for jz in (-21, -11, -1, 7):
            for (x, z) in disk_pts(jx, jz, 3.4):
                C.set(x, G + 1, z, BRASS if math.hypot(x - jx, z - jz) > 2.6 else ENGR)
            leyden_jar(C, jx, jz, G + 2)
            # busbar: from the jar's ball to the aisle at y 36
            yb = G + 12
            sx = 1 if jx < -44 else -1
            for x in range(jx, -44, sx):
                C.set(x, yb, jz, CHAIN_X)
            C.set(-44, yb, jz, CUT_CU)
    for z in range(z0 + 1, z1):
        if C.free(-44, G + 12, z):
            C.set(-44, G + 12, z, slab("waxed_cut_copper_slab", "top"))
    for z in range(z0 + 2, z1 - 1, 4):
        C.set(-44, G + 11, z, "end_rod[facing=down]")
    # small jars on racks along the west wall
    for z in range(z0 + 3, z1 - 2, 3):
        C.set(x0 + 1, G + 1, z, DIB)
        C.set(x0 + 1, G + 2, z, BLUE_GL if z % 2 else GLASS)
        C.set(x0 + 1, G + 3, z, CUT_CU)
        C.set(x0 + 1, G + 4, z, ROD_U)
    # the stair to the roof walk along the north wall (x -59 .. -43, z -29 .. -27)
    rows = stair_run(C, [(-59, -29), (-59, -28), (-59, -27)], "east", 7, G, spec=SB_ST, support=SB)
    for x in range(-52, -49):
        for z in range(-29, -26):
            for y in range(G + 1, G + 8):
                C.set(x, y, z, SB)
            for y in range(G + 8, G + 12):
                C.clear(x, y, z)
            reg(x, z, G + 8)
    rows2 = stair_run(C, [(-49, -29), (-49, -28), (-49, -27)], "east", 7, G + 7, spec=SB_ST, support=SB)
    hole = {(x, z) for row in rows2 for (x, z) in row if C.free(x, yr, z)}
    for x in range(-42, -40):
        for z in range(-29, -26):
            C.set(x, yr, z, SB)
            reg(x, z, yr + 1)
    rails_round(C, hole, yr, skip={(-42, -29), (-42, -28), (-42, -27)})
    for x in range(-58, -43, 3):
        hang(C, x, G + 12, -24, HANG_LAMP)
    for z in range(z0 + 4, z1, 8):
        hang(C, -44, G + 11, z + 2, CHANDELIER) if C.free(-44, G + 11, z + 2) else None
    for z in range(z0 + 3, z1 - 1, 6):
        for x in (-48, -40):
            hang(C, x, G + 10, z, HANG_LAMP)
    C.keep.discard((x0 + 2, G + 1, z1 - 1)); C.bp.barrel(x0 + 2, G + 1, z1 - 1, "north", loot=LOOT + "sts_hall")
    chest(C, x1 - 2, G + 1, z0 + 4, "west", "sts_hall")
    spawner(C, -44, G + 1, -16, MOB_DRONE)
    spawner(C, -44, G + 1, 4, MOB_SPIDER)
    C.set(x0 + 1, G + 1, z1 - 1, "lectern[facing=east,has_book=false,powered=false]")
    # roof walk: lamp posts and the door onto the bridge
    for (x, z) in ((-56, -24), (-56, 4), (-32, -24), (-32, 4), (-44, -10)):
        lamp_post(C, x, yr + 1, z, 2, LANT)


def bridge(C):
    """The covered bridge from the hall's roof walk east into coil ring 1 (feet 39): a tread deck on iron girders,
    iron arches every three blocks, lanterns, cables."""
    f = RF[0]
    x0, x1 = CAP[2], -13
    for x in range(x0, x1 + 1):
        for z in range(-9, -6):
            C.set(x, f - 1, z, TREAD if z == -8 else IRON)
            C.set(x, f - 2, z, IRON if z != -8 else "iron_bars")
            for y in range(f, f + 4):
                C.clear(x, y, z)
            reg(x, z, f)
        for z in (-10, -6):
            if (x - x0) % 3 == 0:
                for y in range(f - 2, f + 4):
                    C.set(x, y, z, IRON)
                C.set(x, f + 4, z, BRASS)
            else:
                C.set(x, f - 1, z, IRON)
                railing(C, x, f, z, "north" if z == -10 else "south")
        if (x - x0) % 3 == 0:
            for z in range(-9, -6):
                C.set(x, f + 4, z, stair(IRON_SLAB.replace("_slab", "_stairs"), "north" if z == -9 else "south",
                                         "top") if z != -8 else BRASS)
            C.set(x, f + 5, -8, IRON_SLAB + "[type=bottom,waterlogged=false]")
            if (x - x0) % 6 == 3:
                C.set(x, f + 3, -8, LANT_H)
    # the roof door through the parapet
    for z in range(-9, -6):
        for y in range(f, f + 4):
            C.clear(x0, y, z)


# ------------------------------------------------------------------ the engineers' barracks
def barracks(C):
    """The engineers' barracks on the north-west terrace: a timber-framed hall on a stone base under a slate roof;
    the bunk room (beds, lockers, a long mess table, the stove and its chimney, a wash corner) and the chief
    engineer's room (desk, maps, a bookcase); the stair down to the court in front, the ridge walk from its east door."""
    x0, z0, x1, z1 = BARR
    yf = T34                                       # floor block y (feet 35)
    yw = yf + 7
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, yf, z, "spruce_planks" if not edge else SB)
            for y in range(yf + 1, yw + 1):
                if edge:
                    post = (x - x0) % 5 == 0 if z in (z0, z1) else (z - z0) % 4 == 0
                    if y <= yf + 1:
                        spec = SB
                    elif post or y == yw:
                        spec = "dark_oak_log[axis=y]" if y < yw else "dark_oak_log[axis=x]"
                    elif y in (yf + 3, yf + 4) and not post:
                        spec = PANE if ((x - x0) % 5 in (2, 3) if z in (z0, z1) else (z - z0) % 4 == 2) else \
                            "spruce_planks"
                    else:
                        spec = "spruce_planks"
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
    # gable roof along x
    zc = (z0 + z1) / 2.0
    hw = (z1 - z0) // 2 + 1
    for k in range(hw + 1):
        y = yw + 1 + k
        for x in range(x0 - 1, x1 + 2):
            za, zb = z0 - 1 + k, z1 + 1 - k
            if za > zb:
                continue
            for z in (za, zb):
                C.set(x, y, z, stair(SLATE_ST, "south" if z < zc else "north") if za != zb else SLATE)
            for z in range(za + 1, zb):
                if x in (x0, x1):
                    C.set(x, y, z, "spruce_planks")
                elif k < hw - 1:
                    C.air(x, y, z)
    for x in range(x0 + 1, x1, 5):
        for z in range(z0 + 1, z1):
            C.set(x, yw, z, "dark_oak_log[axis=z]")
    # partition between the bunk room and the chief's room (x -37), a door in it
    for z in range(z0 + 1, z1):
        for y in range(yf + 1, yw):
            C.set(-37, y, z, "spruce_planks" if (z - z0) % 4 else "dark_oak_log[axis=y]")
    wood_door(C, -37, yf + 1, -50, "east")
    # doors: south (3 wide opening), east (to the ridge walk)
    for x in range(-42, -39):
        for y in range(yf + 1, yf + 4):
            C.clear(x, y, z1)
    for z in range(-53, -50):
        for y in range(yf + 1, yf + 4):
            C.clear(x1, y, z)
    # bunks: beds in pairs along the north and south walls, lockers between
    for x in range(-52, -38, 3):
        C.bp.bed(x, yf + 1, z0 + 1, "south", "light_blue" if x % 2 else "blue")
        C.bp.bed(x + 1, yf + 1, z0 + 1, "south", "blue" if x % 2 else "light_blue")
        C.set(x + 2, yf + 1, z0 + 1, "barrel[facing=south,open=false]")
        C.set(x + 2, yf + 2, z0 + 1, "barrel[facing=south,open=false]")
    for x in range(-49, -42, 3):
        C.bp.bed(x, yf + 1, z1 - 1, "north", "gray")
        C.set(x + 1, yf + 1, z1 - 1, "barrel[facing=north,open=false]")
    # the long mess table with benches
    for x in range(-50, -40):
        C.set(x, yf + 1, -52, TABLE)
        C.set(x, yf + 1, -51, stair("spruce_stairs", "north"))
        C.set(x, yf + 1, -53, stair("spruce_stairs", "south"))
    for x in (-48, -44):
        C.set(x, yf + 2, -52, "candle[candles=3,lit=true,waterlogged=false]")
    # the stove and its chimney on the west wall; the wash corner
    C.set(x0 + 1, yf + 1, -53, "furnace[facing=east,lit=true]")
    C.set(x0 + 1, yf + 1, -52, "smoker[facing=east,lit=true]")
    C.set(x0 + 1, yf + 1, -51, "barrel[facing=up,open=false]")
    for y in range(yf + 1, yw + 9):
        C.set(x0, y, -52, "bricks")
    C.set(x0, yw + 9, -52, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    C.set(x0 + 1, yf + 1, -47, "water_cauldron[level=3]")
    C.set(x0 + 1, yf + 1, -46, "water_cauldron[level=2]")
    C.set(x0 + 2, yf + 1, -46, "cauldron")
    # the chief engineer's room
    C.set(-34, yf + 1, z0 + 2, TABLE)
    C.set(-34, yf + 2, z0 + 2, "candle[candles=2,lit=true,waterlogged=false]")
    C.set(-34, yf + 1, z0 + 3, stair("dark_oak_stairs", "north"))
    C.set(-30, yf + 1, z0 + 1, "cartography_table")
    for z in range(z0 + 1, z0 + 5):
        C.set(x1 - 1, yf + 1, z, "bookshelf")
        C.set(x1 - 1, yf + 2, z, "bookshelf")
    C.bp.bed(-31, yf + 1, z1 - 2, "west", "red")
    C.set(-33, yf + 1, z1 - 1, "lectern[facing=north,has_book=false,powered=false]")
    C.keep.discard((-29, yf + 1, -56)); C.bp.barrel(-29, yf + 1, -56, "west", loot=LOOT + "sts_barracks")
    chest(C, -52, yf + 1, -47, "east", "sts_barracks")
    for x in (-50, -45, -40):
        hang(C, x, yf + 4, -52 if x != -45 else -48, HANG_LAMP)
    hang(C, -32, yf + 4, -52, LANT_H)
    hang(C, -32, yf + 4, -47, LANT_H)
    spawner(C, -46, yf + 1, -48, MOB_GUNNER)
    # the gable ends' eaves against the ridge: no pockets between the roof and the rock
    for x in (x0 - 1, x1 + 1):
        for z in range(z0 - 1, z1 + 2):
            for y in range(yw + 1, yw + 12):
                if C.get(x, y, z) == AIR and (x, y, z) not in C.keep:
                    C.set(x, y, z, rock(x, y, z))
    # the stair from the court (north door of the hall) up to the terrace, and a porch
    stair_run(C, [(-42, -32), (-41, -32), (-40, -32)], "north", 10, G, spec=SB_ST, support=SB)
    for z in range(-42, -32):
        for x in (-43, -39):
            y = G + 1 + (-32 - z)
            if not C.solid(x, y, z):
                C.set(x, y, z, SB)
            if C.free(x, y + 1, z):
                C.set(x, y + 1, z, SB_WALL)
    for z in (-42, -43):
        for x in range(-43, -38):
            C.set(x, T34, z, PAND)
            for y in range(T34 + 1, T34 + 5):
                C.clear(x, y, z)
            reg(x, z, T34 + 1)
    lamp_post(C, -44, T34 + 1, -43, 2, LANT)
    lamp_post(C, -38, T34 + 1, -43, 2, LANT)


# ------------------------------------------------------------------ the battery vaults
def battery_vaults(C):
    """The battery vaults under the court: a dark iron-brick hall (floor y 10) with three banks of battery cells
    (iron cases, glowing redstone cores, copper terminals, a busbar of chains), copper bulbs in the vault; the stair
    up to the court and the tunnel to the gate's guard room."""
    x0, z0, x1, z1 = VAULT
    yf = 10
    box(C, x0, yf + 1, z0, x1, yf + 6, z1, lambda a, b, c: DIB if (b - yf) % 3 else "deepslate_tiles",
        floor=lambda a, b: "polished_blackstone_bricks" if (a + b) % 3 else TREAD, ceil=DIB)
    for x in range(x0 + 2, x1 - 1, 4):
        for z in range(z0 + 2, z1 - 1, 4):
            C.set(x, yf + 7, z, EDISON)
    for z in (7, 11, 15):
        for x in range(x0 + 3, x1 - 2):
            C.set(x, yf + 1, z, IRON)
            C.set(x, yf + 2, z, "redstone_block" if x % 2 else IRON)
            C.set(x, yf + 3, z, CUT_CU if x % 2 else IRON_SLAB + "[type=bottom,waterlogged=false]")
            if x % 2:
                C.set(x, yf + 4, z, ROD_U)
            C.set(x, yf + 5, z, CHAIN_X)
        C.set(x0 + 2, yf + 5, z, CUT_CU)
        C.set(x1 - 2, yf + 5, z, CUT_CU)
    for (x, z) in ((x0 + 1, 9), (x1 - 1, 13), (x0 + 1, 17)):
        C.set(x, yf + 1, z, GAUGE)
        C.set(x, yf + 2, z, BULB)
    chest(C, x1 - 1, yf + 1, z0 + 1, "west", "sts_vaults")
    chest(C, x0 + 1, yf + 1, z1 - 4, "east", "sts_vaults")
    spawner(C, -4, yf + 1, 9, MOB_MITE)
    spawner(C, -10, yf + 1, 18, MOB_SPIDER)
    # the stair up to the court (x -23 .. -21): two flights north with a landing
    rows1 = stair_run(C, [(-23, 20), (-22, 20), (-21, 20)], "north", 7, yf, spec=SB_ST, support=SB)
    for z in range(11, 14):
        for x in range(-23, -20):
            C.set(x, yf + 7, z, SB)
            for y in range(yf + 8, yf + 12):
                C.clear(x, y, z)
            reg(x, z, yf + 8)
    rows2 = stair_run(C, [(-23, 10), (-22, 10), (-21, 10)], "north", 7, yf + 7, spec=SB_ST, support=SB)
    # walls round the stair (it runs in empty ground under the crust)
    for z in range(3, 23):
        for x in (-24, -20):
            for y in range(yf, G + 1):
                if not C.solid(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, DIB)
        for x in range(-23, -20):
            for y in range(yf, G + 1):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, DIB)
    hole = {(x, z) for row in rows2 for (x, z) in row if C.free(x, G, z)}
    rails_round(C, hole, G, skip={(-23, 3), (-22, 3), (-21, 3)})
    # the stair's foot: a corridor east into the vault
    for x in range(-23, x0 + 1):
        for z in range(20, 23):
            if z == 20 and x <= -21:
                continue                     # the flight's first tread
            C.set(x, yf, z, "polished_blackstone_bricks")
            for y in range(yf + 1, yf + 5):
                C.clear(x, y, z)
            reg(x, z, yf + 1)
    for x in range(-24, x0):
        for y in range(yf, yf + 6):
            for z in (19, 23):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, DIB)
        if C.get(x, yf + 5, 21) is None or not C.solid(x, yf + 5, 21):
            for z in range(20, 23):
                if (x, yf + 5, z) not in C.keep:
                    C.set(x, yf + 5, z, DIB)
    C.set(-22, yf + 4, 18, LANT_H) if C.free(-22, yf + 4, 18) else None
    hang(C, -22, yf + 10, 12, LANT_H)


# ------------------------------------------------------------------ the weather observatory
def observatory(C):
    """The weather observatory on the north-east pinnacle: a round stone tower with copper bands, a glass-and-copper
    dome, a wind vane, cup anemometers and a rain gauge on the deck; inside barometers, the log desk, charts, a ladder
    to the telescope room under the dome. The pinnacle stair winds up to it from the coil workshop."""
    cx, cz = T44C
    yf = T44
    for (x, z) in disk_pts(cx, cz, 5.4):
        d = math.hypot(x - cx, z - cz)
        for y in range(yf + 1, yf + 14):
            if d > 4.0:
                spec = SB if hash3(x, y, z, 141) < 0.85 else CSB
                if y in (yf + 6, yf + 13):
                    spec = COPPER
                a = math.degrees(math.atan2(z - cz, x - cx)) % 360
                if y in (yf + 3, yf + 4, yf + 9, yf + 10) and round(a) % 90 in range(35, 56):
                    spec = PANE
                C.set(x, y, z, spec)
            else:
                C.air(x, y, z)
        C.set(x, yf, z, PARQ if d <= 4 else SB)
        if d <= 4.0:
            C.set(x, yf + 7, z, "spruce_planks" if d > 1.2 else "dark_oak_planks")
    # the dome: a glass hemisphere on copper ribs
    for (x, z) in disk_pts(cx, cz, 5.4):
        for y in range(yf + 14, yf + 20):
            dd = math.sqrt((x - cx) ** 2 + (z - cz) ** 2 + ((y - yf - 13) * 1.0) ** 2)
            if 4.0 < dd <= 5.4:
                a = math.degrees(math.atan2(z - cz, x - cx)) % 360
                rib = round(a) % 45 < 9 or y == yf + 14
                C.set(x, y, z, COPPER if rib else "light_blue_stained_glass")
            elif dd <= 4.0:
                C.air(x, y, z)
    # wind vane on the top
    top = yf + 19
    C.set(cx, top, cz, GILD)
    for y in range(top + 1, top + 4):
        C.set(cx, y, cz, IRON_WALL)
    C.set(cx + 1, top + 3, cz, "iron_bars")
    C.set(cx + 2, top + 3, cz, GILD)
    C.set(cx - 1, top + 3, cz, "iron_bars")
    C.set(cx, top + 4, cz, ROD_U)
    # door (east), ladder (west) and the hole in the upper floor
    for y in range(yf + 1, yf + 4):
        for x in (cx + 4, cx + 5):
            C.clear(x, y, cz)
    C.set(cx + 5, yf + 4, cz, ENGR)
    for y in range(yf + 1, yf + 8):
        C.set(cx - 3, y, cz, "ladder[facing=east,waterlogged=false]")
    C.set(cx - 4, yf + 7, cz, SB)
    # ground floor: barometers, the log desk, charts, the chest
    C.set(cx - 3, yf + 1, cz - 2, "cartography_table")
    C.set(cx - 3, yf + 1, cz + 2, "lectern[facing=east,has_book=false,powered=false]")
    for (x, z) in ((cx, cz - 3), (cx + 2, cz - 3), (cx - 2, cz + 3)):
        C.set(x, yf + 2, z, GAUGE)
    C.set(cx + 2, yf + 1, cz + 2, TABLE)
    C.set(cx + 2, yf + 2, cz + 2, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(cx + 1, yf + 1, cz + 2, stair("dark_oak_stairs", "east"))
    C.keep.discard((cx, yf + 1, cz - 3)); C.bp.barrel(cx, yf + 1, cz - 3, "south", loot=LOOT + "sts_observatory")
    C.set(cx, yf + 6, cz, HANG_LAMP)
    # telescope room: the telescope aimed through the dome, charts, a bookcase
    C.set(cx, yf + 8, cz, BRASS)
    C.set(cx, yf + 9, cz, GEAR)
    for t in range(0, 6):
        p = (cx + round(t * 0.6), yf + 10 + round(t * 0.7), cz - round(t * 0.4))
        C.set(*p, GOLD if t == 5 else BRASS)
    for z in (cz - 1, cz, cz + 1):
        C.set(cx + 3, yf + 8, z, "bookshelf")
    C.set(cx - 2, yf + 8, cz - 2, "cartography_table")
    chest(C, cx - 1, yf + 8, cz + 3, "north", "sts_observatory")
    C.set(cx + 2, yf + 8, cz + 2, BULB)
    C.set(cx - 2, yf + 8, cz + 2, BULB)
    # anemometers: masts with four cups on cross arms; a rain gauge; a thermometer post
    for (ax, az) in ((45, -43), (36, -51)):
        for y in range(yf + 1, yf + 6):
            C.set(ax, y, az, IRON_WALL if y > yf + 1 else IRON)
        C.set(ax, yf + 6, az, GEAR)
        for (dx, dz) in N4:
            C.set(ax + dx, yf + 6, az + dz, "iron_bars")
            C.set(ax + 2 * dx, yf + 6, az + 2 * dz, "cauldron")
        C.set(ax, yf + 7, az, ROD_U)
    C.set(48, yf + 1, -52, "cauldron")
    C.set(48, yf + 1, -53, IRON)
    C.set(48, yf + 2, -53, GAUGE)
    lamp_post(C, 38, yf + 1, -45, 2, LANT)
    lamp_post(C, 47, yf + 1, -55, 2, LANT)
    spawner(C, 40, yf + 1, -44, MOB_RAIDER)


def pinnacle_stair(C):
    """The stair round the observatory pinnacle: from the coil workshop's north door, round the pinnacle (cut into
    the rock low down, on a masonry wall higher up), to the deck at feet 45."""
    walkway(C, [(42.0, G + 1.0, -36.0), (43.0, G + 1.0, -39.5)], width=3, full=SB, half=SB_SL, rails=False)
    cells = spiral(C, [(80, 215, G + 1, G + 11), (215, 240, G + 11, G + 11), (240, 375, G + 11, T44 + 1)], 10.0,
                   3.0, SB, SB_SL, SB, cx=T44C[0], cz=T44C[1], rmax=13,
                   support=lambda a, b, c: SB if hash3(a, b, c, 151) < 0.85 else MSB, rail_spec=SB_WALL)
    # lanterns: hung where the rock roofs the stair, on posts elsewhere
    k = 0
    for (x, z), s in sorted(cells.items(), key=lambda kv: kv[1]):
        if abs(math.hypot(x - T44C[0], z - T44C[1]) - 11.0) > 0.5:
            continue
        k += 1
        if k % 6:
            continue
        y = math.floor(s)
        if C.solid(x, y + 4, z):
            hang(C, x, y + 3, z, LANT_H, reach=2)
    return cells


def ridge_walk(C):
    """The ridge walk from the barracks' east door along (and through) the north crag to the observatory deck, a
    carved gallery lit with lanterns where the rock closes over it."""
    pts = [(-27.0, T34 + 1.0, -52.0), (-20.0, T34 + 1.0, -56.0), (0.0, T34 + 6.0, -57.5), (24.0, T44 + 1.0, -57.5),
           (36.0, T44 + 1.0, -55.5)]
    cells = walkway(C, pts, width=3, full=SB, half=SB_SL, edge=(PAND, PAND_SL), lamp_every=6, rail_spec=SB_WALL,
                    support=lambda a, b, c: rock(a, b, c), post=(SB, LANT))
    k = 0
    for (x, z), s in sorted(cells.items()):
        k += 1
        y = math.floor(s)
        if (x + z) % 7 == 0 and C.solid(x, y + 4, z) and C.free(x, y + 3, z):
            C.set(x, y + 3, z, LANT_H)
    return cells


def slide_anchors():
    pts = [(x, -47) for x in range(34, 15, -1)]
    pts += [(16, z) for z in range(-45, -32)]
    return pts


def slide(C):
    """The weather slide: a two-wide channel of flowing water (a new source every eight cells, one block lower) from
    the observatory deck west through the crag and south along an arched aqueduct of brick, ending in a waterfall into
    the court's cooling pond."""
    cells = {}
    for i, (ax, az) in enumerate(slide_anchors()):
        brush = ((ax, az), (ax, az + 1)) if az == -47 else ((ax, az), (ax + 1, az))
        for (bx, bz) in brush:
            if (bx, bz) not in cells:
                cells[(bx, bz)] = (T44 - i // 8, i % 8)
    for (x, z), (y, lv) in cells.items():
        C.set(x, y - 1, z, CU_EX if (x + z) % 2 else COPPER)
        C.set(x, y, z, WATER if lv == 0 else f"water[level={lv}]")
        for yy in range(y + 1, y + 4):
            C.clear(x, yy, z)
    for (x, z), (y, lv) in cells.items():
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            q = (x + dx, z + dz)
            if q in cells or math.hypot(q[0] - T44C[0], q[1] - T44C[1]) <= T44RAD + 0.5:
                continue
            if (q[0], y, q[1]) in C.keep:
                continue
            C.set(q[0], y - 1, q[1], SB)
            C.set(q[0], y, q[1], COPPER if (q[0] + q[1]) % 2 else BRASS)
            if C.free(q[0], y + 1, q[1]) and (q[0], y + 1, q[1]) not in C.keep:
                C.set(q[0], y + 1, q[1], IRON_SLAB + "[type=bottom,waterlogged=false]")
    # the aqueduct: brick piers every four, arches between, down to the ground
    for (x, z), (y, lv) in cells.items():
        g = C.top.get((x, z), -99)
        if g >= y - 3:
            continue
        pier = z % 4 == 0 if x in (16, 17) and z > -46 else x % 4 == 0
        for yy in range(max(g + 1, -12), y - 1):
            if pier or yy >= y - 3:
                if C.free(x, yy, z) and (x, yy, z) not in C.keep:
                    C.set(x, yy, z, "bricks" if not pier or yy % 6 else SB)
    # the waterfall into the pond
    ylast = min(y for (y, _) in cells.values())
    for x in (16, 17):
        for yy in range(G + 1, ylast + 1):
            C.set(x, yy, -32, "water[level=8]")
    return cells


# ------------------------------------------------------------------ the spire
def body_r(y):
    """Outer radius of the spire's shaft at y (the plinth below 34 is battered)."""
    if y < 34:
        return 12.5 - (y - G) * 0.3
    return 9.0 - (y - 34) * (2.0 / 64.0)


def bowl_r(y):
    return 7.0 + 10.0 * (max(0.0, y - 96) / 14.0) ** 0.75


def ring_r(F, y):
    return 13.0 + 2.0 * math.sin(math.pi * (y - (F - 2) + 0.5) / 10.0)


def ring_of(y):
    for k, F in enumerate(RF):
        if F - 2 <= y <= F + 7:
            return k, F
    return None, None


def shaft_spec(x, y, z, d, a):
    """The shaft's skin: dark iron plates (darker low, copper creeping in higher), brass rivet bands every seven,
    eight vertical ribs, small amber windows lighting the stair inside."""
    rib = adelta(a, round(a / 45.0) * 45.0) * math.pi / 180.0 * d < 0.6
    if y % 7 == 0:
        return ENGR if rib else BRASS
    if rib:
        return COPPER if (y // 7) % 2 else IRON
    f = (y - 34) / 64.0
    h = hash3(x, y, z, 161)
    if h < 0.15 + 0.45 * f:
        return VERD if h < 0.1 + 0.2 * f else COPPER
    return IRON if h < 0.85 else DIB


def tube_frame(dx, dz, y):
    """The newel: glass round the lift tubes, brass and iron bands, gear panels."""
    for (tx, tz) in (BUBBLE, WELL):
        if abs(dx - tx) + abs(dz - tz) == 1:
            return GLASS if y % 6 else BRASS
    return (GEAR if y % 12 == 0 else BRASS) if y % 6 == 0 else IRON


def spire_mass(C):
    """The plinth, the shaft, the coil rings, the newel and the core air, the crown bowl and the arena floor."""
    for x in range(SX - 18, SX + 19):
        for z in range(SZ - 18, SZ + 19):
            d = dsp(x, z)
            if d > 17.6:
                continue
            a = asp(x, z)
            dx, dz = x - SX, z - SZ
            for y in range(G - 3, AY + 1):
                k, F = ring_of(y)
                rb = body_r(y) if y < 99 else 0.0
                rr = ring_r(F, y) if k is not None else 0.0
                rbowl = bowl_r(y) if y >= 96 else 0.0
                R = max(rb, rr, rbowl if y >= 96 else 0.0)
                if y == AY:
                    R = 17.4
                if d > R + 0.01:
                    continue
                # --- the newel and the tubes
                if d < NEWEL_R and G <= y <= 98:
                    if (dx, dz) == BUBBLE:
                        spec = "soul_sand" if y == G - 1 else ("bubble_column[drag=false]" if y <= 90 else
                                                                (AIR if y <= 93 else IRON))
                        C.set(x, y, z, spec)
                        continue
                    if (dx, dz) == WELL:
                        C.set(x, y, z, WATER if y <= G else AIR)
                        continue
                    C.set(x, y, z, tube_frame(dx, dz, y))
                    continue
                if d < NEWEL_R and y < G:
                    if (dx, dz) == WELL:
                        C.set(x, y, z, WATER if y >= G - 2 else DIB)
                        continue
                    if (dx, dz) == BUBBLE:
                        C.set(x, y, z, "soul_sand" if y == G - 1 else DIB)
                        continue
                    C.set(x, y, z, DIB)
                    continue
                # --- the lobby (feet 25 .. 31, d <= 9)
                if G + 1 <= y <= G + 7 and d <= 9.0:
                    C.air(x, y, z)
                    continue
                if y == G and d <= 9.0:
                    C.set(x, y, z, TREAD if round(d) % 3 == 0 else PDS)
                    continue
                # --- the core (air from 39 to 98, floor at 38)
                if d <= CORE_R and 39 <= y <= 98:
                    C.air(x, y, z)
                    continue
                # --- the vault inside the bowl (feet 100 .. 108)
                if 100 <= y <= 108 and d <= bowl_r(y) - 1.8:
                    C.air(x, y, z)
                    continue
                # --- ring galleries
                if k is not None and F <= y <= F + 5 and 7.6 <= d <= rr - 1.6:
                    C.air(x, y, z)
                    continue
                # --- solid: pick the skin
                if y == AY:
                    if d <= 2.6:
                        spec = GOLD if d > 1.4 else GILD
                    elif 6.6 < d <= 7.4 or 11.6 < d <= 12.4:
                        spec = BRASS
                    elif adelta(a, round(a / 30.0) * 30.0) * math.pi / 180.0 * d < 0.55:
                        spec = COPPER
                    elif d > AR:
                        spec = ENGR
                    else:
                        spec = TREAD if (int(d) % 2) else IRON
                elif y >= 99 and rbowl >= max(rb, rr):
                    rib = adelta(a, round(a / 30.0) * 30.0) * math.pi / 180.0 * d < 0.7
                    if y == 109:
                        spec = GILD if d > rbowl - 1.2 else IRON
                    elif rib:
                        spec = BRASS
                    elif d > rbowl - 1.2:
                        h = hash3(x, y, z, 162)
                        spec = VERD if h < 0.35 + 0.03 * (y - 99) else (COPPER if h < 0.85 else CU_OX)
                    else:
                        spec = IRON
                    if y == 99:
                        spec = PARQ if d <= 9.4 else spec
                elif k is not None and d > max(rb, 7.6) - 0.01:
                    if y in (F - 2, F + 7):
                        spec = ENGR if round(a) % 20 < 3 else BRASS
                    elif d > rr - 1.2:
                        if F + 2 <= y <= F + 3 and round(a) % 30 < 5:
                            spec = AMBER
                        else:
                            spec = COPPER if (y % 2) else CU_OX
                    elif y == F - 1:
                        spec = PARQ if round(d) % 4 else TREAD
                    elif y == F + 6:
                        spec = IRON
                    else:
                        spec = IRON
                elif y < 34:
                    h = hash3(x, y, z, 163)
                    spec = (DSB if h < 0.75 else (PDS if h < 0.9 else "cracked_deepslate_bricks"))
                    if y in (G + 8, 33):
                        spec = BRASS if y == 33 else DIB
                else:
                    spec = shaft_spec(x, y, z, d, a)
                C.set(x, y, z, spec)


def lobby(C):
    """The lift lobby in the spire's foot: the glass tubes of the lift cage through its middle (the bubble column
    behind signs, the drop well's pool), the winding machinery, benches; its iron door onto the court opens only
    from inside (a lever by the door)."""
    y0 = G + 1
    # the bubble column's mouth (signs hold the water) and the well's mouth
    bx, bz = SX + BUBBLE[0], SZ + BUBBLE[1]
    wx, wz = SX + WELL[0], SZ + WELL[1]
    C.set(bx, y0, bz + 1, "spruce_sign[rotation=8,waterlogged=false]")
    C.set(bx, y0 + 1, bz + 1, "spruce_wall_sign[facing=south,waterlogged=false]")
    C.set(bx, y0 + 2, bz + 1, BRASS)
    C.clear(wx, y0, wz + 1)
    C.clear(wx, y0 + 1, wz + 1)
    C.set(wx, y0 - 1, wz + 1, TREAD)
    C.set(wx, y0 + 2, wz + 1, BRASS)
    reg(bx, bz + 1, y0)
    reg(wx, wz + 1, y0)
    # the door south (x -1 .. 1, z 2 .. 4), iron door at z 4, lever inside
    for x in range(SX - 1, SX + 2):
        for z in range(SZ + 9, SZ + 13):
            C.set(x, G, z, TREAD)
            for y in range(y0, y0 + 3):
                C.clear(x, y, z)
            reg(x, z, y0)
    zd = SZ + 12
    for x in (SX - 1, SX + 1):
        for y in range(y0, y0 + 3):
            C.set(x, y, zd, DIB)
    C.set(SX, y0 + 2, zd, DIB)
    iron_door(C, SX, y0, zd, "south")
    lever(C, SX + 1, y0 + 1, zd - 1, "north")
    C.set(SX + 1, y0 + 1, zd, DIB)
    for x in range(SX - 1, SX + 2):
        C.clear(x, y0, zd + 1)
        C.clear(x, y0 + 1, zd + 1)
    C.set(SX, y0 + 3, zd + 1, LANT_H.replace("hanging=true", "hanging=true")) if C.solid(SX, y0 + 4, zd + 1) else None
    # machinery: gear panels and valve wheels on the wall, a gauge board, benches, lamps
    for k in range(8):
        a = 22.5 + 45 * k
        if adelta(a, 90) < 30:
            continue
        x, z = polar(9.6, a)
        x, z = round(x), round(z)
        C.set(x, y0 + 2, z, GEAR if k % 2 else GAUGE)
        C.set(x, y0 + 4, z, EDISON)
        x2, z2 = polar(8.3, a)
        x2, z2 = round(x2), round(z2)
        C.put(x2, y0, z2, stair("dark_oak_stairs", out_facing(SX - x2, SZ - z2)) if k % 2 else
              ("barrel[facing=up,open=false]"))
    for (x, z) in ((SX - 6, SZ - 4), (SX + 6, SZ - 4), (SX, SZ - 7)):
        hang(C, x, y0 + 5, z, HANG_LAMP)
    C.set(SX - 5, y0, SZ + 5, VALVE)
    C.set(SX + 5, y0, SZ + 5, "lectern[facing=north,has_book=false,powered=false]")
    chest(C, SX - 7, y0, SZ, "east", "sts_court")


# the helices: S_k (departure angle at ring k), each climbs 13 over 504 degrees with a landing half way
HELIX_S = [24, 348, 312, 276]


def helices(C):
    """The helical stair in the spire's core between the rings, with flat landings at the ring doors; returns the
    door angles [(F, angle)]."""
    doors = []
    allcells = []
    for k, S in enumerate(HELIX_S):
        F = RF[k]
        E = S + 504
        segs = [(S - 25, S, F, F), (S, S + 232, F, F + 6.5), (S + 232, S + 272, F + 6.5, F + 6.5),
                (S + 272, E, F + 6.5, F + 13)]
        if k == 3:
            segs.append((E, E + 60, F + 13, F + 13))
        else:
            segs.append((E, E + 25, F + 13, F + 13))
        allcells.append(helix(C, segs))
        doors.append((F, (S - 12) % 360))
        if k < 3:
            doors.append((F + 13, (E + 12) % 360))
        else:
            doors.append((F + 13, 90.0))
    return doors


def helix(C, segs):
    """Treads (tread plate, brass slabs on half steps) for every segment, rails only on open ends."""
    cells = []
    for (a0, a1, s0, s1) in segs:
        for x in range(SX - 7, SX + 8):
            for z in range(SZ - 7, SZ + 8):
                d = dsp(x, z)
                if abs(d - RC) > RW / 2.0:
                    continue
                a = asp(x, z)
                if in_arc(a, a0 % 360.0, a0 % 360.0 + (a1 - a0)):
                    t = ((a - a0) % 360.0) / (a1 - a0)
                    cells.append((x, z, q2(s0 + (s1 - s0) * t)))
    best = {}
    for (x, z, s) in cells:
        best.setdefault((x, z), set()).add(s)
    for (x, z, s) in cells:
        reg(x, z, s)
    for (x, z, s) in sorted(cells, key=lambda c: c[2]):
        y = surface(C, x, z, s, TREAD, TREAD_SLAB, IRON)
        for c in range(1, 5):
            if any(abs(t - (y + c)) < 0.6 or abs(t - 1 - (y + c)) < 0.6 for t in best[(x, z)] if t > s + 1):
                break
            C.clear(x, y + c, z)
    for (x, z, s) in cells:
        for (dx, dz) in N4:
            n = (x + dx, z + dz)
            if any(abs(t - s) <= 1.0 for t in best.get(n, ())):
                continue
            top = math.ceil(s - 0.01)
            if C.solid(n[0], top - 1, n[1]) or C.solid(n[0], top, n[1]):
                continue
            if dsp(*n) >= CORE_R or dsp(*n) < NEWEL_R:
                continue
            rail_at(C, n[0], n[1], s, out_facing(dx, dz), under=TREAD_SLAB)
    return cells


def ring_doors(C, doors):
    """Doors (3 wide, 4 high) through the shaft's wall from the core into each gallery."""
    for (F, a) in doors:
        ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
        for x in range(SX - 9, SX + 10):
            for z in range(SZ - 9, SZ + 10):
                t = (x - SX) * ux + (z - SZ) * uz
                p = -(x - SX) * uz + (z - SZ) * ux
                if 5.6 <= t <= 8.4 and abs(p) <= 1.5:
                    C.set(x, F - 1, z, TREAD)
                    for y in range(F, F + 4):
                        C.clear(x, y, z)
                    reg(x, z, F)
                if 5.6 <= t <= 8.4 and 1.5 < abs(p) <= 2.5:
                    for y in range(F, F + 4):
                        if C.free(x, y, z) and dsp(x, z) > CORE_R:
                            C.set(x, y, z, ENGR)
        x, z = polar(7.0, a)
        C.set(round(x), F + 4, round(z), GILD)


def core_lights(C):
    """Edison lamps set in the core's wall every 45 degrees and four blocks of height; slit windows between rings."""
    for y in range(41, 98, 4):
        for k in range(8):
            a = 22.5 + 45 * k + (22.5 if (y // 4) % 2 else 0)
            for rr10 in range(62, 75):
                x, z = polar(rr10 / 10.0, a)
                x, z = round(x), round(z)
                if C.solid(x, y, z) and (x, y, z) not in C.keep and dsp(x, z) > CORE_R:
                    C.set(x, y, z, EDISON)
                    break


def galleries(C):
    """Each coil ring's gallery furnished for its use; lamps hung from every ring's ceiling."""
    for k, F in enumerate(RF):
        for j in range(12):
            a = 15 + 30 * j
            x, z = polar(10.3, a)
            x, z = round(x), round(z)
            if C.free(x, F + 4, z) and (x, F + 4, z) not in C.keep and C.solid(x, F + 6, z):
                hang(C, x, F + 4, z, HANG_LAMP if k < 4 else CHANDELIER if j % 3 == 0 else HANG_LAMP)
    rings_dress(C)


def ring_cells(F, r0, r1, a0=0, a1=360):
    out = []
    for x in range(SX - 15, SX + 16):
        for z in range(SZ - 15, SZ + 16):
            d = dsp(x, z)
            if r0 <= d <= r1 and in_arc(asp(x, z), a0, a1):
                out.append((x, z))
    return out


def free_floor(C, x, F, z):
    return C.free(x, F, z) and (x, F, z) not in C.keep and C.solid(x, F - 1, z) and C.free(x, F + 1, z)


def rings_dress(C):
    rng = random.Random(171)
    # ring 1, the insulator gallery: porcelain insulator stacks along the outer wall, cable drums, the bridge mouth
    F = RF[0]
    for j in range(18):
        a = 10 + 20 * j
        if adelta(a, 180) < 16 or adelta(a, HELIX_S[0] - 12) < 16:
            continue
        x, z = polar(11.6, a)
        x, z = round(x), round(z)
        if not free_floor(C, x, F, z):
            continue
        for y in range(F, F + 4):
            C.set(x, y, z, "white_terracotta" if y % 2 == F % 2 else "calcite")
        C.set(x, F + 4, z, BRASS)
        x2, z2 = polar(9.6, a + 10)
        x2, z2 = round(x2), round(z2)
        if j % 3 == 0 and free_floor(C, x2, F, z2):
            C.set(x2, F, z2, CU_BLOCK)
    x, z = polar(9.8, 120)
    chest(C, round(x), F, round(z), out_facing(SX - round(x), SZ - round(z)), "sts_rings")
    x, z = polar(9.6, 300)
    spawner(C, round(x), F, round(z), MOB_SPIDER)
    # ring 2, the condenser ring: banks of copper windings, small jars, gauges
    F = RF[1]
    for j in range(24):
        a = 7.5 + 15 * j
        if adelta(a, (HELIX_S[0] + 504 + 12) % 360) < 14 or adelta(a, HELIX_S[1] - 12) < 14:
            continue
        x, z = polar(11.7, a)
        x, z = round(x), round(z)
        if not free_floor(C, x, F, z):
            continue
        for y in range(F, F + 3):
            C.set(x, y, z, COPPER if (y + j) % 2 else CU_BLOCK)
        if j % 2:
            C.set(x, F + 3, z, BLUE_GL)
            C.set(x, F + 4, z, ROD_U)
        else:
            C.set(x, F + 3, z, GAUGE)
    x, z = polar(9.8, 60)
    chest(C, round(x), F, round(z), out_facing(SX - round(x), SZ - round(z)), "sts_rings")
    x, z = polar(9.6, 250)
    spawner(C, round(x), F, round(z), MOB_DRONE)
    # ring 3, the spark-gap gallery: electrode pairs across the gallery with sparks (end rods) between
    F = RF[2]
    for j in range(12):
        a = 15 + 30 * j
        if adelta(a, (HELIX_S[1] + 504 + 12) % 360) < 18 or adelta(a, HELIX_S[2] - 12) < 18:
            continue
        x, z = polar(11.8, a)
        x, z = round(x), round(z)
        if not free_floor(C, x, F, z):
            continue
        C.set(x, F, z, IRON)
        C.set(x, F + 1, z, IRON_WALL)
        C.set(x, F + 2, z, CU_BLOCK)
        fx = out_facing(SX - x, SZ - z)
        C.set(x, F + 3, z, f"lightning_rod[facing={fx},powered=false,waterlogged=false]")
        x2, z2 = polar(10.6, a)
        x2, z2 = round(x2), round(z2)
        if C.free(x2, F + 3, z2) and (x2, F + 3, z2) not in C.keep:
            C.set(x2, F + 3, z2, f"end_rod[facing={fx}]")
    x, z = polar(9.8, 200)
    chest(C, round(x), F, round(z), out_facing(SX - round(x), SZ - round(z)), "sts_rings")
    x, z = polar(9.6, 30)
    spawner(C, round(x), F, round(z), MOB_AUTO)
    # ring 4, the resonance chamber: tuning forks, bells, amethyst on the outer wall
    F = RF[3]
    for j in range(16):
        a = 11.25 + 22.5 * j
        if adelta(a, (HELIX_S[2] + 504 + 12) % 360) < 16 or adelta(a, HELIX_S[3] - 12) < 16:
            continue
        x, z = polar(11.8, a)
        x, z = round(x), round(z)
        if not free_floor(C, x, F, z):
            continue
        if j % 3 == 0:
            C.set(x, F, z, "bell[attachment=floor,facing=north,powered=false]")
        elif j % 3 == 1:
            C.set(x, F, z, "amethyst_block")
            C.set(x, F + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
        else:
            C.set(x, F, z, IRON)
            C.set(x, F + 1, z, IRON_WALL)
            C.set(x, F + 2, z, "iron_bars")
            C.set(x, F + 3, z, "iron_bars")
        C.set(x, F + 4, z, "note_block") if C.free(x, F + 4, z) else None
    x, z = polar(9.8, 340)
    chest(C, round(x), F, round(z), out_facing(SX - round(x), SZ - round(z)), "sts_rings")
    x, z = polar(9.6, 200)
    spawner(C, round(x), F, round(z), MOB_RAIDER)
    # ring 5, the switchboard ring (site of grace): the waystone, switchboards of levers and bulbs, benches
    F = RF[4]
    x, z = polar(10.2, 110)
    waystone(C, round(x), F, round(z))
    for j in range(24):
        a = 7.5 + 15 * j
        if adelta(a, 90) < 30:
            continue
        x, z = polar(12.0, a)
        x, z = round(x), round(z)
        if not free_floor(C, x, F, z):
            continue
        C.set(x, F, z, DIB)
        C.set(x, F + 1, z, BULB if j % 2 else GAUGE)
        C.set(x, F + 2, z, BULB_OX if j % 2 == 0 else GAUGE)
        if j % 4 == 1:
            x2, z2 = polar(10.0, a)
            x2, z2 = round(x2), round(z2)
            if free_floor(C, x2, F, z2):
                C.set(x2, F, z2, stair("dark_oak_stairs", out_facing(x - x2, z - z2)))
    x, z = polar(10.0, 140)
    chest(C, round(x), F, round(z), out_facing(SX - round(x), SZ - round(z)), "sts_grace")


def turret(C):
    """The grace turret: a square stair tower corbelled out of coil ring 5's south side, its spiral stair (the
    compression before the arena) up to a stair-house on the crown's rim; the mist in its door onto the arena."""
    tx, tz = TUR
    yb, yt = 84, AY + 6
    for x in range(tx - 6, tx + 7):
        for z in range(tz - 6, tz + 7):
            dd = math.hypot(x - tx, z - tz)
            edge = abs(x - tx) == 6 or abs(z - tz) == 6
            for y in range(yb, yt + 1):
                corbel = y < 90 and max(abs(x - tx), abs(z - tz)) > 6 - (90 - y)
                if corbel:
                    continue
                if y < 90 or y == yt:
                    spec = DIB if y < 90 else ENGR
                elif edge:
                    spec = IRON if (y % 7 and abs(x - tx) != abs(z - tz)) else BRASS
                    if y % 7 == 3 and (abs(x - tx) == 0 or abs(z - tz) == 0) and y < AY:
                        spec = AMBER
                elif dd <= 5.2:
                    if y == 90:
                        C.set(x, y, z, IRON)
                    else:
                        C.air(x, y, z)
                    continue
                else:
                    spec = IRON
                C.set(x, y, z, spec)
    # the copper pyramid roof with a lightning rod
    for k in range(8):
        for x in range(tx - 7 + k, tx + 8 - k):
            for z in range(tz - 7 + k, tz + 8 - k):
                if max(abs(x - tx), abs(z - tz)) == 7 - k:
                    C.set(x, yt + 1 + k, z, CU_OX if k % 2 else COPPER)
    C.set(tx, yt + 9, tz, GILD)
    C.set(tx, yt + 10, tz, ROD_U)
    C.set(tx, yt + 11, tz, ROD_U)
    # the spiral (rc 3.5): from the passage (north, feet 91) up two turns to the top landing (north, feet 111)
    cells = spiral(C, [(270, 610, RF[4], RF[4] + 10), (610, 650, RF[4] + 10, RF[4] + 10),
                       (650, 990, RF[4] + 10, AY + 1), (990, 1015, AY + 1, AY + 1)], 3.5, 3.0, TREAD, TREAD_SLAB,
                   IRON, cx=tx, cz=tz, rmax=6, rails=False)
    for (x, z) in disk_pts(tx, tz, 1.5):
        for y in range(RF[4] - 1, AY + 1):
            C.set(x, y, z, (BRASS if y % 4 else GEAR) if (x, z) == (tx, tz) else IRON)
    # the passage from the gallery (ring 5's south) to the turret's north wall
    for x in range(SX - 1, SX + 2):
        for z in range(SZ + 12, tz - 4):
            C.set(x, RF[4] - 1, z, TREAD)
            for y in range(RF[4], RF[4] + 4):
                C.clear(x, y, z)
            reg(x, z, RF[4])
    for z in range(SZ + 12, tz - 4):
        for x in (SX - 2, SX + 2):
            for y in range(RF[4] - 1, RF[4] + 5):
                if C.free(x, y, z):
                    C.set(x, y, z, IRON)
        for x in range(SX - 1, SX + 2):
            if C.free(x, RF[4] + 4, z) and (x, RF[4] + 4, z) not in C.keep:
                C.set(x, RF[4] + 4, z, IRON)
            if C.free(x, RF[4] - 2, z):
                C.set(x, RF[4] - 2, z, IRON)
    # lamps in the turret's walls
    for y in range(RF[4] + 2, AY + 4, 4):
        for (x, z) in ((tx - 6, tz), (tx + 6, tz), (tx, tz + 6), (tx - 4, tz - 4), (tx + 4, tz + 4), (tx - 4, tz + 4),
                       (tx + 4, tz - 4)):
            if C.solid(x, y, z) and (x, y, z) not in C.keep:
                C.set(x, y, z, EDISON)
    # the top door onto the arena (x -1 .. 1 through the north wall), the mist in it
    zw = tz - 6
    for x in range(tx - 1, tx + 2):
        C.set(x, AY, zw, TREAD)
        C.set(x, AY, zw + 1, TREAD)
        for y in range(AY + 1, AY + 4):
            C.clear(x, y, zw + 1)
            C.air(x, y, zw)
        reg(x, zw, AY + 1)
        reg(x, zw + 1, AY + 1)
    for x in range(tx - 2, tx + 3):
        C.set(x, AY + 4, zw, GILD if x == tx else ENGR)
    C.bp.mist(tx - 1, AY + 1, zw, tx + 1, AY + 3, zw)
    return cells


def arena(C):
    """The crown platform: the railing round the rim with copper posts and rods, the corona's six legs on pads, the
    corona ring with its rods and end rods, spokes to the hub and the needle; the boss seal; the vault hatch."""
    # railing (open at the turret door)
    k = 0
    for x in range(SX - 18, SX + 19):
        for z in range(SZ - 18, SZ + 19):
            d = dsp(x, z)
            if not (AR < d <= 17.4):
                continue
            if abs(x - TUR[0]) <= 6 and z >= TUR[1] - 6:
                continue
            k += 1
            if k % 7 == 0:
                C.set(x, AY + 1, z, COPPER)
                C.set(x, AY + 2, z, ROD_U)
            else:
                railing(C, x, AY + 1, z, out_facing(x - SX, z - SZ))
    # the corona's legs on pads past the rim
    for j in range(6):
        a = 60 * j
        lx, lz = polar(19.0, a)
        for (x, z) in disk_pts(lx, lz, 2.2):
            C.set(x, AY, z, ENGR)
            for y in range(AY - 3, AY):
                if C.free(x, y, z):
                    C.set(x, y, z, IRON)
        for (x, z) in disk_pts(lx, lz, 1.0):
            for y in range(AY + 1, 127):
                C.set(x, y, z, (BRASS if y % 6 == 0 else (COPPER if (y // 3) % 2 else IRON)))
        for y in range(AY - 6, AY - 2):
            x, z = polar(19.0 - (AY - 2 - y) * 0.6, a)
            C.set(round(x), y, round(z), IRON)
    # the corona ring (tube radius 1.3 round radius 18.5 at y 128)
    for x in range(SX - 21, SX + 22):
        for z in range(SZ - 21, SZ + 22):
            d = dsp(x, z)
            a = asp(x, z)
            for y in range(126, 131):
                if (d - 18.5) ** 2 + (y - 128) ** 2 <= 1.75:
                    C.set(x, y, z, BRASS if round(a) % 30 < 5 else (COPPER if y != 128 else CU_OX))
    for j in range(24):
        a = 15 * j + 7.5
        x, z = polar(18.5, a)
        C.set(round(x), 130, round(z), ROD_U)
        x, z = polar(20.4, a)
        C.set(round(x), 128, round(z), f"end_rod[facing={out_facing(math.cos(math.radians(a)), math.sin(math.radians(a)))}]")
    # spokes to the hub, the hub, the needle
    hub = (SX, 133, SZ)
    for j in range(6):
        a = 60 * j + 30
        x, z = polar(18.5, a)
        line3(C, (round(x), 129, round(z)), (hub[0], hub[1] - 1, hub[2]), IRON, force=True)
    for (x, z) in disk_pts(SX, SZ, 2.2):
        for y in range(131, 136):
            if math.sqrt((x - SX) ** 2 + (z - SZ) ** 2 + (y - 133) ** 2) <= 2.2:
                C.set(x, y, z, GILD if y == 133 else COPPER)
    for y in range(136, 141):
        C.set(SX, y, SZ, IRON_WALL if y < 139 else ROD_U)
    for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        C.set(SX + 3 * dx, 133, SZ + 3 * dz, f"end_rod[facing={f}]")
    C.set(SX, 137, SZ + 1, "end_rod[facing=south]")
    C.set(SX, 137, SZ - 1, "end_rod[facing=north]")
    # end rods crackling under the bowl's rim
    for j in range(36):
        a = 10 * j
        x, z = polar(17.0, a)
        x, z = round(x), round(z)
        if C.free(x, AY - 2, z):
            C.set(x, AY - 2, z, "end_rod[facing=down]")
    C.bp.boss_seal(SX, AY, SZ, BOSS, 15)


def charged_vault(C):
    """The charged vault inside the crown bowl: down a ladder under sealed bars in the arena floor; chests, gold, the
    storm heart (sea lanterns caged in copper and rods), charged cells; the drop well's iron trapdoor in its floor."""
    yf = F_VAULT
    hx, hz = SX, SZ - 6
    for y in range(yf, AY):
        C.set(hx, y, hz - 1, IRON if y % 3 else BRASS)
        C.set(hx, y, hz, "ladder[facing=south,waterlogged=false]")
    C.set(hx, AY, hz, MOD["vault_bars"])
    C.set(hx, AY - 1, hz, "ladder[facing=south,waterlogged=false]")
    # the storm heart in the middle (over the newel)
    for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(SX + dx, yf, SZ + dz + 3, GOLD if (dx or dz) else "sea_lantern")
    C.set(SX, yf + 1, SZ + 3, "sea_lantern")
    C.set(SX, yf + 2, SZ + 3, CU_BLOCK)
    C.set(SX, yf + 3, SZ + 3, ROD_U)
    for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south")):
        C.set(SX + dx, yf + 1, SZ + 3 + dz, f"end_rod[facing={f}]")
    # chests and treasure round the walls
    for (a, f) in ((200, None), (250, None), (330, None)):
        x, z = polar(7.6, a)
        x, z = round(x), round(z)
        chest(C, x, yf, z, out_facing(SX - x, SZ - z), "sts_vault")
    for a in range(20, 360, 40):
        x, z = polar(8.4, a)
        x, z = round(x), round(z)
        if C.free(x, yf, z) and (x, yf, z) not in C.keep and C.solid(x, yf - 1, z):
            C.set(x, yf, z, GOLD if a % 80 else "redstone_block")
            if C.free(x, yf + 1, z):
                C.set(x, yf + 1, z, BULB if a % 120 else ROD_U)
    for a in (40, 140):
        x, z = polar(5.0, a)
        hang(C, round(x), yf + 6, round(z), CHANDELIER)
    # the drop well's hatch
    wx, wz = SX + WELL[0], SZ + WELL[1]
    C.set(wx, yf - 1, wz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    lever(C, wx - 1, yf, wz, "west", face="floor")


def grace_tubes(C):
    """At the site of grace the lift cage opens south: the bubble column's top and the drop well's mouth."""
    F = RF[4]
    for (tx, tz) in (BUBBLE, WELL):
        x, z = SX + tx, SZ + tz + 1
        C.set(x, F - 1, z, TREAD)
        for y in range(F, F + 3):
            C.clear(x, y, z)
        reg(x, z, F)
        C.set(x, F + 3, z, BRASS)
    bx, bz = SX + BUBBLE[0], SZ + BUBBLE[1]
    for y in range(F, F + 3):
        C.clear(bx, y, bz)


def ring_rods(C):
    """Lightning rods on every coil ring's top rim, end rods sparking under the rims."""
    for F in RF:
        for j in range(18):
            a = 20 * j + (10 if F % 2 else 0)
            x, z = polar(13.6, a)
            x, z = round(x), round(z)
            if C.free(x, F + 8, z) and C.solid(x, F + 7, z):
                C.set(x, F + 8, z, ROD_U)
            x, z = polar(14.2, a + 10)
            x, z = round(x), round(z)
            if C.free(x, F - 3, z) and C.solid(x, F - 2, z):
                C.set(x, F - 3, z, "end_rod[facing=down]")


# ------------------------------------------------------------------ masts and cables
def mast(C, mx, mz, base):
    """A lattice collector mast on a spur: a 3 x 3 tower of copper and iron corners with X-braces, a platform, a
    copper coil ring and a cluster of lightning rods; returns its cable anchor."""
    y0, y1 = base + 1, base + MAST_H
    for (dx, dz) in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
        for y in range(base - 1, y0 + 1):
            for (ex, ez) in ((0, 0), (1 if dx < 0 else -1, 0), (0, 1 if dz < 0 else -1)):
                C.set(mx + dx + ex, y, mz + dz + ez, DSB)
    for y in range(y0, y1 + 1):
        for (dx, dz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            C.set(mx + dx, y, mz + dz, COPPER if (y // 4) % 2 else IRON)
        if (y - y0) % 4 == 0:
            for (dx, dz) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                C.set(mx + dx, y, mz + dz, IRON_SLAB + "[type=bottom,waterlogged=false]")
        elif (y - y0) % 4 == 3:
            for (dx, dz) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                C.set(mx + dx, y, mz + dz, "iron_bars")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            C.set(mx + dx, y1 + 1, mz + dz, BRASS if abs(dx) == 2 or abs(dz) == 2 else IRON)
    for y in range(y1 + 2, y1 + 6):
        C.set(mx, y, mz, "white_terracotta" if y % 2 else "calcite")
    for (x, z) in disk_pts(mx, mz, 2.6):
        if math.hypot(x - mx, z - mz) > 1.6:
            C.set(x, y1 + 6, z, COPPER if (x + z) % 2 else BRASS)
    for (dx, dz) in ((0, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        C.set(mx + dx, y1 + 7 if (dx or dz) else y1 + 6, mz + dz, ROD_U if (dx or dz) else CU_BLOCK)
    C.set(mx, y1 + 7, mz, ROD_U)
    C.set(mx, y1 + 8, mz, ROD_U)
    C.set(mx, y1, mz, BULB)
    return (mx, y1 + 3, mz)


def cable(C, p0, p1, sag=0.1):
    """A sagging iron chain from p0 to p1 (each link's axis follows the local slope)."""
    L = math.dist(p0, p1)
    n = int(L * 2.5) + 2
    prev = None
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        z = p0[2] + (p1[2] - p0[2]) * t
        y = p0[1] + (p1[1] - p0[1]) * t - sag * L * 4 * t * (1 - t)
        q = (round(x), round(y), round(z))
        if q == prev:
            continue
        prev = q
        dy = (p1[1] - p0[1]) - sag * L * 4 * (1 - 2 * t)
        hx, hz = abs(p1[0] - p0[0]), abs(p1[2] - p0[2])
        if abs(dy) > max(hx, hz):
            spec = CHAIN
        else:
            spec = CHAIN_X if hx >= hz else CHAIN_Z
        if C.free(*q) and q not in C.keep:
            C.set(*q, spec)


def masts_and_cables(C):
    for (mx, mz, my) in MASTS:
        base = C.top.get((mx, mz), my - 1)
        if mz == 40 and mx == 0:
            base = 34                                      # on the bastion's roof
        anchor = mast(C, mx, mz, base)
        a = asp(mx, mz)
        ex, ez = polar(15.6, a)
        F = RF[1]
        cable(C, anchor, (ex, F + 3, ez), sag=0.08)
        # an insulator where it meets the ring
        C.set(round(ex), F + 3, round(ez), "white_terracotta")


# ------------------------------------------------------------------ the whole site
def storm_spire(bp):
    WALK.clear()
    C = Ctx(bp)
    heightfield(C)
    write_terrain(C)
    court(C)
    spire_mass(C)
    lobby(C)
    doors = helices(C)
    ring_doors(C, doors)
    grace_tubes(C)
    core_lights(C)
    galleries(C)
    turret(C)
    arena(C)
    charged_vault(C)
    ring_rods(C)
    bastion(C)
    camp(C)
    funicular(C)
    switchbacks(C)
    capacitor_hall(C)
    bridge(C)
    dynamo_house(C)
    workshop(C)
    barracks(C)
    battery_vaults(C)
    observatory(C)
    pinnacle_stair(C)
    ridge_walk(C)
    slide(C)
    masts_and_cables(C)
    near_walk = set()
    for (x, z) in WALK:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                near_walk.add((x + dx, z + dz))
    parapet_walls(C, [lambda x, z: in_rect(x, z, CAP, 3), lambda x, z: in_rect(x, z, DYN, 2),
                      lambda x, z: in_rect(x, z, WSHOP, 2), lambda x, z: in_rect(x, z, BARR, 2),
                      lambda x, z: in_rect(x, z, BAS, 2), lambda x, z: (x, z) in near_walk,
                      lambda x, z: dsp(x, z) < 15, lambda x, z: in_rect(x, z, (12, -40, 20, -26)),
                      lambda x, z: 19 <= x <= 33 and 50 <= z <= 66])
    scatter_rocks(C)
    seal_caves(C)
    light_pass(C)


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("mountaineers_camp", (2, 1, 100), (1, 29, 50)),
    ("dynamo_court", (8, 25, 22), (3, 48, 4)),
    ("capacitor_hall", (-29, 25, -6), (-58, 30, -6)),
    ("dynamo_house", (29, 25, 4), (35, 28, -2)),
    ("battery_vaults", (-16, 11, 13), (0, 13, 13)),
    ("insulator_gallery", (-11, 39, -8), (-7, 41, 1)),
    ("site_of_grace", (-4, 91, 3), (2, 93, 0)),
    ("crown_arena", (0, 111, 6), (0, 128, -12)),
]

register(StructureDef(
    "storm_spire", "overworld", ["stony_peaks", "jagged_peaks", "windswept_hills", "windswept_gravelly_hills"],
    [Piece("spire", storm_spire, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_GUNNER, 5, 1, 2), (MOB_DRONE, 5, 1, 2), (MOB_STRAY, 6, 1, 2), (MOB_RAIDER, 3, 1, 1)],
    title_fr="La Flèche des tempêtes", title_en="The Storm Spire"))
