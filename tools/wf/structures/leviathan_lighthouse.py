"""The Leviathan Lighthouse (Le Phare du Léviathan): a storm-lashed lighthouse fortress on a rocky headland. A 120-high
masonry lighthouse banded with an oxblood spiral stands on the headland's plateau, crowned by a corbelled lamp gallery,
a glass lantern room under a verdigris cupola and a great lamp; beside it the keeper's quarters. Below, in the cove,
a whaling station on its quay (rendering house, boathouse, harpoon battery, flensing crane) and the skeleton of a
beached leviathan, its skull on the shingle and its ribs vaulting over a covered dock. Colossal tier
(tools/BUILDING.md §1, §12 concept 35, §10 legacy-dungeon template, §15), steampunk accents
(tools/STYLE_STEAMPUNK.md: a clockwork lens drive, a steam fog-horn engine, harpoon cannons, rendering vats).

Silhouette (one noun phrase, §15.1): a tall white lighthouse wound with a red spiral, flaring to a wide glass lantern
under a green dome, on a cliff-bound headland, a whale's ribcage arching over the harbour below it.

Placement: fit mode ``coast`` (wf/placement.py): the template's south side is the sea; the ground layer (y = 0) lands
one block above the sea surface (sea water top = y -1). Layout, x east, z south; the tower's axis is (TX, TZ) = (0, 6):
  * the massif: the headland plateau (top 26) with cliffs on three sides; the ridge and its east crag to the north
    (tops 32-42, with the stump of the old light), the shoulder ledge (top 14) at the crag's south-east foot, the
    quay terrace of the whaling station (top 10) in the cove, the shingle spit (top 0) where the skull lies;
  * the approach (§7): the beachcombers' camp (waystone) on the land north of the ridge, a path east along the ridge's
    foot, the gorge cut through the east crag (compression, the lighthouse hidden), the natural arch at its mouth that
    frames the headland, the lighthouse and the harbour (the reveal), the shoulder ledge and the ramp down to the quay;
  * the whaling station (hub, waystone): the flensers' mess and bunkhouse, the cooperage, the rendering house (three
    try-works under two smokestacks, the stirring gallery), the harpoon battery on the quay's rim, the flensing crane,
    the boathouse (sail loft above, two slips and whaleboats below), the quay stair down to the skull; through the
    leviathan's jaws into its skull and out into the ribcage dock (two jetties, moored boats; optional: the lamp
    tower up to the spine catwalk and its cache at the tail);
  * the main route on: the tide stair from the quay's south-west corner down the cliff foot to the tideline ledge,
    the sea caves under the headland: the tide grotto (optional: the smugglers' hole north), the flooded hall round
    its sea pool (a loop round the pool), the rock stair (a spiral in a rock shaft) up to the cistern under the tower
    and its stair into the base hall; then the tower: base hall (oil store), chart room, log room, fog-horn engine
    room, clockwork room, watch room (balcony), the lens room with the giant rotating lens (site of grace); the
    enclosed stair in the gallery's corbel (compression) to the hatch house, the mist, the lantern room (the arena,
    33 wide under the cupola and its great lamp, the lamp gallery outside the glass);
  * optional: the keeper's quarters (kitchen, parlour, bedroom, study) beside the tower and the plateau yard (signal
    mast, fog bell, oil house, garden);
  * the treasury: the keeper's hoard in the gallery corbel under the arena, down a ladder under sealed bars;
  * shortcuts (§10.4): the hoard's drop well (85 blocks in the tower wall) into a pool lobby whose iron door opens
    onto the plateau from inside only; the stair tower down the cliff to the quay, whose iron door opens from inside
    only; the tower's north door and the keeper's front door (plateau <-> tower).
Loot gradient (§15.6): camp 1; station, cooperage, battery 1-2; mess, rendering house, boathouse, dock 2; grotto,
smugglers, flooded hall, cistern 2; keeper's quarters, base and chart rooms 2; log, engine, clockwork 2-3; watch room,
spine cache 3; lens room 3; the keeper's hoard 3-5.
Height budget: the vane stands ~150 above the ground layer, i.e. ~215 absolute on a sea-level coast.
"""
import math
import random

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, IRON_SLAB, PIPES,
                       TABLE, TREAD, TREAD_SLAB, VERD, W, fbm, hash01, hash3, out_facing, vnoise)
from ..parts import LOOT, MOD

# the champion of the lantern room: the Drowned Lightkeeper (entity/boss/DrownedKeeper.java)
BOSS = "brasshaven:drowned_keeper"
MOB_DROWNED = "minecraft:drowned"
MOB_WRAITH = W + "tide_wraith"
MOB_CRAB = W + "barnacle_crab"
MOB_WRECKER = W + "bandit_marksman"
MOB_DRONE = W + "steam_drone"
MOB_SPIDER = W + "clockwork_spider"
MOB_GARGOYLE = W + "gargoyle"
MOB_MARINE = W + "drowned_marine"
MOB_MITE = W + "rust_mite"
MOB_KNIGHT = W + "skeleton_knight"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
ENGR = W + "engraved_brass"
BTILE, BTILE_ST, BTILE_SL = W + "brass_tiles", W + "brass_tile_stairs", W + "brass_tile_slab"
GRILLE = W + "brass_grille"
GILD = W + "gilded_trim"
DIB = W + "dark_iron_bricks"
IRON_ST = W + "dark_iron_plating_stairs"
IRON_WALL = W + "dark_iron_plating_wall"
COPPER_SL = W + "copper_plating_slab"
MAHOG = W + "mahogany_panelling"
PARQ, PARQ_SL = W + "mahogany_parquet", W + "mahogany_parquet_slab"
SLATE, SLATE_ST, SLATE_SL = W + "slate_roof_tiles", W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"
SMOKE, SOOT = W + "smokestack_bricks", W + "sooty_smokestack_bricks"
VALVE, COG, SHELF, CHAIR = W + "valve_wheel", W + "wall_cog", W + "wall_shelf", W + "mahogany_chair"
RAIL = W + "brass_railing"
SB, MSB, CSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"
SB_ST, SB_SL, SB_WALL = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
DSB, DSB_ST, DSB_SL, DSB_WALL = "deepslate_bricks", "deepslate_brick_stairs", "deepslate_brick_slab", \
    "deepslate_brick_wall"
TUFB, PTUF = "tuff_bricks", "polished_tuff"
PAND, PAND_SL, PAND_ST = "polished_andesite", "polished_andesite_slab", "polished_andesite_stairs"
CALC = "calcite"
PDIO = "polished_diorite"
RED, RED2 = "red_terracotta", "brown_terracotta"
BRICK, BRICK_ST, BRICK_SL, BRICK_WALL = "bricks", "brick_stairs", "brick_slab", "brick_wall"
SPR, SPR_ST, SPR_SL = "spruce_planks", "spruce_stairs", "spruce_slab"
SPR_LOG, SPR_FENCE = "spruce_log", "spruce_fence"
DOAK, DOAK_ST, DOAK_SL = "dark_oak_planks", "dark_oak_stairs", "dark_oak_slab"
BONE = "bone_block"
CU_OX, CU_WE, CU_EX = "waxed_oxidized_copper", "waxed_weathered_copper", "waxed_exposed_copper"
CUT_OX, CUT_OX_ST, CUT_OX_SL = "waxed_oxidized_cut_copper", "waxed_oxidized_cut_copper_stairs", \
    "waxed_oxidized_cut_copper_slab"
CU_BLOCK = "waxed_copper_block"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CHAIN_X, CHAIN_Z = "iron_chain[axis=x,waterlogged=false]", "iron_chain[axis=z,waterlogged=false]"
BULB = "waxed_copper_bulb[lit=true,powered=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
ROD_D = "lightning_rod[facing=down,powered=false,waterlogged=false]"
GLASS, BLUE_GL, PANE = "glass", "light_blue_stained_glass", "glass_pane"
GOLD = "gold_block"
GRASS = "grass_block[snowy=false]"
PICKLE = "sea_pickle[pickles=4,waterlogged=true]"
LADDER = "ladder[facing={},waterlogged=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# ------------------------------------------------------------------ dimensions
TX, TZ = 0, 6                        # the lighthouse's axis
G = 26                               # plateau top block (feet 27)
TERR = 10                            # quay terrace top (feet 11)
SHOUL = 14                           # shoulder ledge top (feet 15)
R_IN = 9.6                           # tower rooms' radius (every storey)
FLOORS = (27, 39, 51, 63, 75, 87)    # storey feet: base hall, chart, log, engine, clockwork, watch
STAIR_A = (280, 140, 0, 220, 80, 300)   # start angle of each storey's wall stair (it climbs +190 degrees)
LF = 99                              # lens room feet (floor 98)
AY = 113                             # arena floor block (feet 114)
GL0, GL1 = 16.5, 17.5                # lantern glazing ring
RD = 20.5                            # gallery deck outer radius
CUP = 128                            # cupola spring
VAULT_F = 104                        # the hoard's feet (floor 103)
WELL = (TX, TZ + 11)                 # the drop well (in the tower wall)
PLAT_C, PLAT_R = (0, -4), (34.0, 40.0)
RID_C, RID_R = (-24, -74), (60.0, 14.0)
CRAG_C, CRAG_R = (26, -78), (16.0, 11.0)
SH_C, SH_R = (40, -62), (16.0, 7.0)
TERRACE = (30, -62, 98, -36)         # quay terrace x0, z0, x1, z1
SPIT_C, SPIT_R = (68, -20), (18.0, 16.0)
CAMP = (-30, -104)
SPINE_X = 68                         # the leviathan's axis
RIBS = (-2, 4, 10, 16, 22, 28, 34)
HOUSE = (-31, -4, -19, 14)           # keeper's quarters walls x0, z0, x1, z1
STAIRT = (26, -47, 38, -35)          # cliff stair tower walls
STC = (32, -41)
MESS = (56, -61, 69, -50)
RENDER = (72, -60, 96, -46)
COOP = (42, -53, 50, -46)
BOATH = (82, -35, 96, -19)
CAVE_A = (28, -12, 9.0, 7.0, 7)      # tide grotto (cx, cz, rx, rz, height)
CAVE_B = (20, -34, 6.0, 5.0, 5)      # smugglers' hole
CAVE_C = (-6, -2, 15.0, 13.0, 10)    # flooded hall
POOL_C = (-6, -1, 8.5, 5.5)
SHAFT_D = (16, 18)                   # rock stair shaft centre
CIST = (-8, -4, 8, 22)               # cistern room x0, z0, x1, z1 (feet 15)


# ------------------------------------------------------------------ small geometry
def ang(x, z):
    return math.degrees(math.atan2(z, x)) % 360.0


def polar(r, a, c=(TX, TZ)):
    return c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))


def dt(x, z):
    """Horizontal distance to the tower's axis."""
    return math.hypot(x - TX, z - TZ)


def at(x, z):
    return ang(x - TX, z - TZ)


def in_arc(a, a0, a1):
    return (a - a0) % 360.0 <= (a1 - a0) + 1e-9


def adelta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def q2(s):
    return round(s * 2) / 2.0


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def se(x, z, c, r, p=3.0):
    return (abs((x - c[0]) / r[0]) ** p + abs((z - c[1]) / r[1]) ** p) ** (1.0 / p)


def in_rect(x, z, r, m=0):
    return r[0] - m <= x <= r[2] + m and r[1] - m <= z <= r[3] + m


def disk_pts(cx, cz, r):
    R = int(math.ceil(r)) + 1
    return [(x, z) for x in range(int(cx) - R, int(cx) + R + 1) for z in range(int(cz) - R, int(cz) + R + 1)
            if math.hypot(x - cx, z - cz) <= r + 0.01]


class Ctx:
    """Blueprint wrapper: ``keep`` holds reserved air (walkways' headroom) that decoration (``put``) never fills;
    ``top`` the massif column tops; ``kind`` their kind."""

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
        self.bp.set(x, y, z, AIR)
        self.keep.discard((x, y, z))

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b and "bubble" not in b

    def free(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR

    def water(self, x, y, z, spec=WATER):
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))


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


def floor_ok(C, x, y, z):
    """A free furniture spot on feet y: air here and above, a solid block below, not reserved."""
    return C.free(x, y, z) and (x, y, z) not in C.keep and C.solid(x, y - 1, z) and C.free(x, y + 1, z)


def fput(C, x, y, z, spec):
    if floor_ok(C, x, y, z):
        C.set(x, y, z, spec)
        return True
    return False


def lamp_post(C, x, y, z, h=3, lamp=LANT):
    C.set(x, y, z, IRON)
    for yy in range(y + 1, y + h):
        C.set(x, yy, z, IRON_WALL)
    C.set(x, y + h, z, lamp)


def fill_down(C, x, y, z, spec, ymin=-14):
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
        elif C.free(*p) and p not in C.keep:
            C.put(*p, spec)
    return out


def surface(C, x, z, s, full, half, under=None):
    """Walking surface at feet s (a multiple of 0.5): a full block, or a bottom slab on ``under``; returns the top
    block y."""
    n = math.floor(s)
    if s - n > 0.25:
        C.set(x, n, z, slab(half))
        C.set(x, n - 1, z, under or full)
        return n
    C.set(x, n - 1, z, full)
    return n - 1


def rail_at(C, x, z, s, facing, under=BRASS_SLAB, post=None, spec=None):
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


def walkway(C, pts, width=3, full=SB, half=SB_SL, under=None, rails=True, head=4, lamp_every=8, rail_spec=None,
            support=None, post=(SPR_FENCE, LANT), support_min=-14):
    """A walkway along a polyline of (x, feet s, z), quantised to half blocks (slope <= 0.5 per block); ``full`` and
    ``half`` may be callables of (x, z). Returns {(x, z): s}."""
    hw = width // 2
    deck_c, rail_c = {}, {}
    total = sum(math.hypot(b[0] - a[0], b[2] - a[2]) for a, b in zip(pts, pts[1:])) or 1.0
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        if L < 1e-6:
            continue
        if abs(b[1] - a[1]) / L > 0.52:
            print(f"leviathan_lighthouse: walkway segment {a}->{b} too steep ({abs(b[1] - a[1]) / L:.2f})")
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
        f = full(X, Z) if callable(full) else full
        h = half(X, Z) if callable(half) else half
        y = surface(C, X, Z, s, f, h, under)
        for c in range(1, head + 1):
            C.clear(X, y + c, Z)
        if support:
            fill_down(C, X, y - 2, Z, support, support_min)
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
            if C.solid(X, top - 1, Z) and C.top.get((X, Z), -99) >= top - 1:
                continue
            if C.solid(X, top, Z):
                continue
            k += 1
            pst = post if lamp_every and k % lamp_every == 0 else None
            if support and C.free(X, top - 1, Z):
                fill_down(C, X, top - 1, Z, support, support_min)
            rail_at(C, X, Z, s, out_facing(X - nb[0], Z - nb[1]), post=pst, spec=rail_spec)
    return out


def spiral(C, segs, rc, w, full, half, fill, head=4, rails=True, rmax=12, cx=TX, cz=TZ, support=None,
           rail_spec=None, rail_rmin=0.0):
    """A stair winding round (cx, cz): segs [(a0, a1, s0, s1)] (each arc < 360), feet linear in the angle, on a band
    w wide round radius rc. ``support`` fills under the treads down to the next solid block. Returns {(x, z): s} of
    every cell (later segments win)."""
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
                    if n in cells or n in allc:
                        continue
                    if math.hypot(n[0] - cx, n[1] - cz) < rail_rmin:
                        continue
                    top = math.ceil(s - 0.01)
                    if C.solid(n[0], top - 1, n[1]) or C.solid(n[0], top, n[1]):
                        continue
                    rail_at(C, n[0], n[1], s, out_facing(dx, dz), spec=rail_spec)
        allc.update(cells)
    return allc


def stair_run(C, cells0, d, n, fy, spec=SB_ST, support=SB, head=4, support_min=None):
    """A straight flight climbing toward ``d``: ``cells0`` the first tread row; tread i sits at y fy + 1 + i (the
    last tread flush with a floor at fy + n). Headroom cleared; support under each tread down to fy + 1 (or
    ``support_min``)."""
    dx, dz = DV[d]
    rows = []
    for i in range(n):
        row = [(x + dx * i, z + dz * i) for (x, z) in cells0]
        t = fy + 1 + i
        for (x, z) in row:
            C.set(x, t, z, stair(spec, d))
            lo = fy + 1 if support_min is None else support_min
            for yy in range(lo, t):
                if support_min is not None and C.solid(x, yy, z):
                    continue
                C.set(x, yy, z, support)
            for yy in range(t + 1, t + head + 1):
                C.clear(x, yy, z)
            reg(x, z, t + 0.5)
        rows.append(row)
    return rows


def box(C, x0, y0, z0, x1, y1, z1, wall, floor=None, ceil=None, air=True):
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
    """Railings on floor y_floor round a set of open cells (a stairwell)."""
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


def gable(C, x0, z0, x1, z1, y, axis, st, full, over=1, gable_wall=None):
    """A pitched roof over the box x0..x1, z0..z1 (walls), eaves at y: ridge along ``axis``; rafters under it are
    full blocks of ``full``; gable ends filled with ``gable_wall``."""
    if axis == "x":
        span = (z1 - z0) / 2.0
        mid = (z0 + z1) / 2.0
        for x in range(x0 - over, x1 + over + 1):
            for z in range(z0 - over, z1 + over + 1):
                k = int(span + over - abs(z - mid) + 0.5)
                yy = y + k
                if abs(z - mid) < 0.6:
                    C.set(x, yy, z, slab(full.replace("_tiles", "_tile_slab") if "tiles" in full else full.replace("_planks", "_slab")))
                    C.set(x, yy - 1, z, full)
                else:
                    C.set(x, yy, z, stair(st, "south" if z < mid else "north"))
                if x in (x0, x1) and gable_wall:
                    for g in range(y, yy):
                        if x0 <= x <= x1 and z0 <= z <= z1:
                            C.set(x, g, z, gable_wall(x, g, z) if callable(gable_wall) else gable_wall)
    else:
        span = (x1 - x0) / 2.0
        mid = (x0 + x1) / 2.0
        for z in range(z0 - over, z1 + over + 1):
            for x in range(x0 - over, x1 + over + 1):
                k = int(span + over - abs(x - mid) + 0.5)
                yy = y + k
                if abs(x - mid) < 0.6:
                    C.set(x, yy, z, slab(full.replace("_tiles", "_tile_slab") if "tiles" in full else full.replace("_planks", "_slab")))
                    C.set(x, yy - 1, z, full)
                else:
                    C.set(x, yy, z, stair(st, "east" if x < mid else "west"))
                if z in (z0, z1) and gable_wall:
                    for g in range(y, yy):
                        if x0 <= x <= x1 and z0 <= z <= z1:
                            C.set(x, g, z, gable_wall(x, g, z) if callable(gable_wall) else gable_wall)


# ------------------------------------------------------------------ terrain: the headland massif
def gorge_floor(z):
    """Feet height of the gorge path at z (rising south)."""
    if z <= -94:
        return 1
    if z <= -78:
        return 1 + (z + 94) * 0.5
    if z <= -66:
        return 9 + (z + 78) * 0.5
    return 15


def natural(x, z):
    """(top block y, kind) of the massif column at (x, z), or (None, None)."""
    best, kind = None, None
    n1 = fbm(x, z, 12.0, 701) - 0.5
    # the headland plateau
    e = se(x, z, PLAT_C, PLAT_R, 3.5) * (1 + 0.07 * n1)
    if e <= 1.0:
        t = G
    else:
        t = G - (e - 1.0) * 36.0 * 3.0 - 2.5 * (vnoise(x, z, 4.0, 702) - 0.5)
    best, kind = t, "plat"
    # the ridge and its east crag (the gorge cuts the crag)
    for (c, r, top, amp, seed) in ((RID_C, RID_R, 32, 9, 711), (CRAG_C, CRAG_R, 33, 6, 712)):
        e = se(x, z, c, r, 2.2) * (1 + 0.1 * (fbm(x, z, 9.0, seed) - 0.5))
        if e <= 1.0:
            t = top + amp * fbm(x, z, 8.0, seed + 5)
        else:
            t = top - 2 - (e - 1.0) * r[1] * 2.6
        if t > best:
            best, kind = t, "ridge"
    # the shoulder ledge
    e = se(x, z, SH_C, SH_R, 2.5)
    t = SHOUL if e <= 1.0 else SHOUL - (e - 1.0) * SH_R[1] * 2.2
    if t > best:
        best, kind = t, "shoulder"
    # the quay terrace (masonry, vertical faces)
    if in_rect(x, z, TERRACE) and best < TERR:
        best, kind = TERR, "quay"
    # the shingle spit
    e = se(x, z, SPIT_C, SPIT_R, 2.5) * (1 + 0.08 * (fbm(x, z, 7.0, 721) - 0.5))
    t = 0 if e <= 1.0 else -(e - 1.0) * SPIT_R[0] * 1.0
    if t > best:
        best, kind = t, "spit"
    # the gorge through the crag
    if -100 <= z <= -63:
        w = 2.6 + 1.2 * (vnoise(x, z, 5.0, 731) - 0.5) + (1.0 if z < -96 else 0.0)
        if abs(x - 34 - 0.8 * math.sin(z * 0.17)) <= w:
            f = gorge_floor(z) - 1
            if best > f:
                best, kind = f, "gorge"
    if best < -13:
        return None, None
    return int(math.floor(best)), kind


def rock(x, y, z):
    """Headland rock: jittered strata of stone, andesite, tuff and deepslate; wet and mossy in the tide zone, gull
    streaks (calcite) high on the faces."""
    j = int((hash01(x // 5, z // 5, 741) - 0.5) * 4)
    band = (y + j) % 9
    h = hash3(x, y, z, 742)
    if y <= 2:
        if y < -2:
            return "stone" if h < 0.6 else ("andesite" if h < 0.85 else "gravel" if False else "tuff")
        return "mossy_cobblestone" if h < 0.4 else ("tuff" if h < 0.7 else "cobblestone")
    if y >= 20 and h < 0.05:
        return CALC
    if band in (0, 1):
        return "andesite" if h < 0.8 else "stone"
    if band == 4:
        return "tuff" if h < 0.75 else "andesite"
    if band == 7 and y < 10:
        return "deepslate" if h < 0.6 else "cobbled_deepslate"
    return "stone" if h < 0.85 else "cobblestone"


def quay_stone(x, y, z):
    h = hash3(x, y, z, 751)
    if y <= 1:
        return MSB if h < 0.6 else "mossy_cobblestone"
    if y <= 4:
        return MSB if h < 0.3 else SB
    return CSB if h < 0.1 else SB


def heightfield(C):
    for x in range(-100, 101):
        for z in range(-112, 97):
            t, k = natural(x, z)
            if t is None:
                continue
            C.top[(x, z)] = t
            C.kind[(x, z)] = k


def write_terrain(C):
    """A shell: the top crust 4 deep and every cell exposed within two columns (faces), down to the sea floor (or
    two below the ground on the land side); the inside stays the world's own rock."""
    def nb_low(x, z):
        m = 99
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) + abs(dz) > 2 or (dx == 0 and dz == 0):
                    continue
                t = C.top.get((x + dx, z + dz))
                if t is None:
                    t = -15 if z + dz > -64 else -3
                m = min(m, t)
        return m
    for (x, z), t in C.top.items():
        k = C.kind[(x, z)]
        m = nb_low(x, z)
        lo = max(-14, min(m + 1, t - 3) - 1)
        if z < -64 and C.top.get((x, z), 0) >= 0:
            lo = max(lo, -3)
        for y in range(lo, t + 1):
            if k == "quay":
                if y == t:
                    spec = quay_pave(x, z)
                else:
                    spec = quay_stone(x, y, z) if y > m - 1 or y >= t - 1 else "stone"
            elif k == "spit":
                h = hash01(x, z, 761)
                if y == t:
                    spec = "gravel" if h < 0.45 else ("sand" if h < 0.75 else ("cobblestone" if h < 0.9 else
                                                                               "mossy_cobblestone"))
                else:
                    spec = "sand" if y > t - 2 else rock(x, y, z)
            else:
                spec = rock(x, y, z)
                if y == t and k == "plat":
                    n = fbm(x, z, 6.0, 771)
                    spec = GRASS if n > 0.42 else ("coarse_dirt" if n > 0.34 else ("gravel" if n > 0.3 else
                                                                                  rock(x, y, z)))
                elif y == t and k in ("ridge", "shoulder") and t > 2:
                    n = fbm(x, z, 5.0, 772)
                    spec = GRASS if n > 0.58 else ("gravel" if n > 0.5 else rock(x, y, z))
                elif y in (t - 1, t - 2) and k == "plat" and fbm(x, z, 6.0, 771) > 0.34:
                    spec = "dirt"
            C.set(x, y, z, spec)


def quay_pave(x, z):
    """The quay: stone-brick flags in a grid with cobble joints, plank boardwalks near the water."""
    h = hash01(x, z, 781)
    if z >= -40:
        return SPR if (x % 4) else DOAK
    if x % 6 == 0 or z % 6 == 0:
        return "cobblestone" if h < 0.7 else "mossy_cobblestone"
    return SB if h < 0.75 else (PAND if h < 0.9 else CSB)


def seal_caves(C):
    """Wherever a built space (air, water, a partial block) touches the hollow inside of the massif's shell, the
    touching hollow cell becomes rock, so no room or stair leaks into the world under the headland."""
    FULL_W = ("stone", "brick", "andesite", "tuff", "plating", "dirt", "gravel", "cobble", "calcite", "diorite",
              "planks", "grass_block", "deepslate", "_block", "copper", "glass", "log", "terracotta", "granite",
              "clay", "parquet", "plate", "concrete", "wool", "sand", "bone")
    PART_W = ("slab", "stair", "wall", "fence", "pane", "bars", "chain", "door", "rail", "rod", "lantern", "lamp",
              "carpet", "button", "lever", "sign", "ladder", "torch", "candle", "water", "air", "bed", "head", "plant",
              "grass[", "pickle", "kelp", "seagrass", "trapdoor")
    for (x, y, z) in list(C.bp.blocks):
        b = C.get(x, y, z)
        if any(k in b for k in FULL_W) and not any(k in b for k in PART_W):
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0)):
            n = (x + dx, y + dy, z + dz)
            if n in C.bp.blocks:
                continue
            t = C.top.get((n[0], n[2]))
            if t is None or n[1] > t or n[1] < -14:
                continue
            C.bp.set(*n, rock(*n))


# ------------------------------------------------------------------ lighting check (fallback only)
LIGHT_EMIT = {"lantern": 15, "soul_lantern": 10, "campfire": 15, "sea_lantern": 15, "glowstone": 15, "edison_lamp": 15,
              "hanging_edison_lamp": 15, "brass_chandelier": 15, "end_rod": 14, "torch": 14, "wall_torch": 14,
              "copper_bulb": 15, "waxed_copper_bulb": 15, "shroomlight": 15, "ochre_froglight": 15,
              "pearlescent_froglight": 15, "verdant_froglight": 15, "redstone_lamp": 15, "blast_furnace": 13,
              "smoker": 13, "furnace": 13, "jack_o_lantern": 15}
NO_BULB = ("chest", "barrel", "spawner", "door", "lamp", "bulb", "glass", "waystone", "seal", "bars", "sign", "bed",
           "water", "ladder", "stairs", "slab", "lantern", "gold", "rod", "vault", "table", "shelf", "lectern", "gauge",
           "valve", "cog", "gear", "pipe", "furnace", "anvil", "redstone", "bone", "grass", "dirt", "sand", "gravel")
LIGHT_STATS = {}


def light_pass(C):
    """Every covered floor (a ceiling within 14 blocks over the head) should have block light 8 or more from the
    hand-placed lamps; the few floors that stay dark get a lit copper bulb set in their ceiling (low ceilings) or in
    the floor (tall halls). The count is reported so the hand placement can be tuned."""
    import numpy as np
    from ..blueprint import is_solid
    blocks = C.bp.blocks
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    X0, Y0, Z0 = min(xs) - 1, min(ys) - 1, min(zs) - 1
    SH = (max(xs) - X0 + 2, max(ys) - Y0 + 2, max(zs) - Z0 + 2)
    opaque = np.zeros(SH, bool)
    known = np.zeros(SH, bool)
    L = np.zeros(SH, np.int8)
    wet = np.zeros(SH, bool)
    full = np.zeros(SH, bool)
    for (x, y, z), v in blocks.items():
        n, pr = v[0], v[1] or {}
        sh = n.split(":")[1]
        i = (x - X0, y - Y0, z - Z0)
        known[i] = True
        e = LIGHT_EMIT.get(sh, 0)
        if ("bulb" in sh or "furnace" in sh or sh == "smoker" or sh == "redstone_lamp") and pr.get("lit") != "true":
            e = 0
        if sh == "campfire" and pr.get("lit") != "true":
            e = 0
        if sh.endswith("candle") and pr.get("lit") == "true":
            e = 3 * int(pr.get("candles", 1))
        if sh == "sea_pickle" and pr.get("waterlogged") == "true":
            e = 3 + 3 * int(pr.get("pickles", 1))
        if sh in ("water", "bubble_column") or pr.get("waterlogged") == "true":
            wet[i] = True
        if is_solid(n) and sh not in ("air", "cave_air"):
            full[i] = True
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
    stand[:, 1:-1, :] = air[:, 1:-1, :] & opaque[:, :-2, :] & air[:, 2:, :] & known[:, :-2, :] & known[:, 1:-1, :]
    cov = np.zeros(SH, bool)
    for k in range(2, 16):
        cov[:, :-k, :] |= opaque[:, k:, :]
    stand[:, 1:-1, :] &= ~full[:, 1:-1, :] & ~full[:, 2:, :]
    stand &= ~wet
    cells = np.argwhere(stand & cov & (L < 8))
    LIGHT_STATS["dark_before"] = int(len(cells))
    LIGHT_STATS["covered"] = int((stand & cov).sum())
    order = sorted(((int(a) + X0, int(b) + Y0, int(c) + Z0) for a, b, c in cells),
                   key=lambda p: (0 if (p[0] % 5 == 0 and p[2] % 5 == 0) else 1, p[1], p[0], p[2]))

    def ok_block(x, y, z):
        b = C.get(x, y, z) or ""
        return b and opaque[x - X0, y - Y0, z - Z0] and not any(k in b for k in NO_BULB) and (x, y, z) not in C.keep

    added = 0
    for (x, f, z) in order:
        if L[x - X0, f - Y0, z - Z0] >= 8:
            continue
        cy = f + 2
        while not opaque[x - X0, cy - Y0, z - Z0]:
            cy += 1
        if cy - f <= 5 and ok_block(x, cy, z):
            p = (x, cy, z)
        elif ok_block(x, f - 1, z):
            p = (x, f - 1, z)
        else:
            continue
        C.bp.set(*p, BULB)
        LIGHT_STATS.setdefault("where", []).append(p)
        opaque[p[0] - X0, p[1] - Y0, p[2] - Z0] = False
        spread(*p, 15)
        added += 1
    LIGHT_STATS["bulbs_added"] = added
    print(f"leviathan_lighthouse: light check: {LIGHT_STATS['covered']} covered floor cells, "
          f"{LIGHT_STATS['dark_before']} below 8 before the fallback, {added} fallback bulbs")


# ------------------------------------------------------------------ the approach: camp, path, gorge, arch, shoulder
def tent(C, cx, cz, length=5, color="white_wool", axis="z"):
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
    x, z = (cx, cz - hl) if axis == "z" else (cx - hl, cz)
    C.set(x, 1, z, LANT)


def ground_patch(C, x0, z0, x1, z1, seed=801):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) in C.top and C.top[(x, z)] > 0:
                continue
            h = hash01(x, z, seed)
            C.set(x, 0, z, GRASS if h < 0.6 else ("coarse_dirt" if h < 0.8 else ("gravel" if h < 0.92 else "sand")))
            C.set(x, -1, z, "dirt")
            C.set(x, -2, z, "dirt" if h < 0.7 else "stone")
            for y in range(1, 4):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)


def whaleboat(C, x, y, z, axis="z", n=7, wood="spruce"):
    """A small open whaleboat lying on its keel at hull level y: planked sides, thwarts, a harpoon at the bow."""
    hl = n // 2
    for i in range(-hl, hl + 1):
        w = 1 if abs(i) < hl else 0
        for o in range(-w - 1, w + 2):
            X, Z = (x + o, z + i) if axis == "z" else (x + i, z + o)
            if abs(o) == w + 1:
                if abs(i) < hl:
                    C.set(X, y, Z, f"{wood}_slab[type=top,waterlogged=false]" if abs(i) < hl - 1 else
                          f"{wood}_planks")
                continue
            if abs(i) == hl:
                f = ("south" if i > 0 else "north") if axis == "z" else ("east" if i > 0 else "west")
                C.set(X, y, Z, stair(f"{wood}_stairs", OPP[f]))
            else:
                C.set(X, y - 1, Z, f"{wood}_planks")
                C.set(X, y, Z, f"{wood}_slab[type=bottom,waterlogged=false]" if i % 2 else f"{wood}_trapdoor["
                      "facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    tip = (x, z + hl) if axis == "z" else (x + hl, z)
    C.set(tip[0], y + 1, tip[1], ROD_U)


def camp(C):
    """The beachcombers' camp north of the ridge: tents round a fire, the waystone, a beached boat, fish racks, a
    signpost toward the gorge."""
    cx, cz = CAMP
    ground_patch(C, cx - 12, cz - 7, cx + 12, cz + 7)
    tent(C, cx - 6, cz - 1, 5, "white_wool")
    tent(C, cx + 5, cz - 2, 5, "light_gray_wool", axis="x")
    C.set(cx, 1, cz + 2, "campfire[lit=true,facing=north,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((0, 4, "north"), (2, 2, "west"), (-2, 2, "east")):
        C.set(cx + dx, 1, cz + dz, stair(SPR_ST, f))
    waystone(C, cx + 2, 1, cz + 5)
    C.set(cx + 2, 0, cz + 5, PAND)
    chest(C, cx - 6, 1, cz + 1, "south", "lvl_camp")
    barrel(C, cx + 8, 1, cz + 3)
    barrel(C, cx + 8, 2, cz + 3)
    barrel(C, cx + 9, 1, cz + 4, "north")
    # fish drying racks
    for x in range(cx - 10, cx - 6):
        C.set(x, 1, cz + 5, SPR_FENCE)
        C.set(x, 2, cz + 5, SPR_FENCE)
        C.set(x, 3, cz + 5, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    whaleboat(C, cx - 3, 1, cz - 6, axis="x", n=7)
    # signpost
    C.set(cx + 11, 1, cz, SPR_FENCE)
    C.set(cx + 11, 2, cz, "spruce_wall_sign[facing=east,waterlogged=false]" if False else SPR_FENCE)
    C.set(cx + 11, 3, cz, LANT)


def approach(C):
    """Camp -> along the ridge foot -> the gorge -> the arch -> the shoulder ledge -> the ramp down to the quay."""
    def gpath(x, z):
        h = hash01(x, z, 811)
        return "dirt_path" if h < 0.55 else ("gravel" if h < 0.8 else "coarse_dirt")

    def gslab(x, z):
        return "cobblestone_slab"
    walkway(C, [(-20, 1, -103), (0, 1, -102), (20, 1, -101), (31, 1, -100)], width=3, full=gpath, half=gslab,
            under="dirt", rails=False, support="dirt", support_min=-2)
    pts = [(31, 1, -100), (34, 1, -95), (34, 9, -79), (34, 15, -66), (35, 15, -61)]
    walkway(C, pts, width=3, full=lambda x, z: "gravel" if hash01(x, z, 812) < 0.5 else "cobblestone",
            half=lambda x, z: "cobblestone_slab", under="cobblestone", rails=False, support="cobblestone")
    # the arch at the gorge's mouth: a rock lintel over the path
    for x in range(28, 41):
        for z in range(-69, -64):
            base = 22 + int(1.5 * math.cos((x - 34) / 6.0 * math.pi / 2)) - (1 if z in (-69, -65) else 0)
            for y in range(base, 31):
                if C.free(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, rock(x, y, z))
    # the shoulder ledge: a parapet path along its rim, then the ramp to the quay
    walkway(C, [(35, 15, -61), (44, 15, -60), (50, 15, -59), (58, 11, -57), (62, 11, -54)], width=3,
            full=lambda x, z: SB if hash01(x, z, 813) < 0.7 else "cobblestone", half=SB_SL, rails=True,
            support="cobblestone", lamp_every=6, post=(SB_WALL, LANT))
    # a viewing bench and a cairn at the reveal
    C.set(42, 15, -63, stair(SPR_ST, "north"))
    C.set(43, 15, -63, stair(SPR_ST, "north"))
    for y in range(15, 18):
        C.set(38, y, -63, "cobblestone" if y < 17 else "mossy_cobblestone")
    C.set(38, 18, -63, LANT)


# ------------------------------------------------------------------ the old light on the ridge (a ruined stump)
def old_light(C):
    cx, cz = -50, -74
    base = C.top.get((cx, cz), 34)
    top0 = base + 30
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d > 6.2:
                continue
            ytop = top0 - int(9 * fbm(x, z, 3.0, 821)) - (6 if x > cx + 2 else 0)
            gb = C.top.get((x, z), base)
            for y in range(min(gb, base) - 2, ytop + 1):
                if d > 5.0:
                    if (y - base) % 7 == 3 and abs((ang(x - cx, z - cz) % 90) - 45) < 8 and d > 5.5:
                        spec = "iron_bars" if hash01(x, y, 822) < 0.5 else AIR
                    else:
                        h = hash3(x, y, z, 823)
                        spec = MSB if y < base + 4 and h < 0.5 else (CSB if h < 0.3 else ("mossy_cobblestone" if h <
                                                                                          0.4 else SB))
                else:
                    spec = "cobblestone" if hash3(x, y, z, 824) < 0.6 else "gravel"
                if spec != AIR:
                    C.set(x, y, z, spec)
    # fallen blocks round its foot and a toppled lamp cage
    rng = random.Random(825)
    for _ in range(40):
        x, z = cx + rng.randint(-11, 11), cz + rng.randint(-9, 9)
        t = C.top.get((x, z))
        if t is None or math.hypot(x - cx, z - cz) < 6.5:
            continue
        if C.free(x, t + 1, z):
            C.set(x, t + 1, z, rng.choice((CSB, MSB, "cobblestone", "mossy_cobblestone", SB_SL + "[type=bottom,"
                                                                                               "waterlogged=false]")))
    x, z = cx + 8, cz + 3
    t = C.top.get((x, z), base)
    C.set(x, t + 1, z, "iron_bars")
    C.set(x + 1, t + 1, z, "iron_bars")
    C.set(x, t + 2, z, IRON_SLAB + "[type=bottom,waterlogged=false]")


# ------------------------------------------------------------------ the quay terrace and the whaling station
def station_yard(C):
    """The yard (hub): the waystone on a whalebone plinth, crates, a rope walk, lamp posts, drying racks."""
    wx, wz = 62, -44
    C.set(wx, TERR, wz, BONE)
    waystone(C, wx, TERR + 1, wz)
    for (dx, dz) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        C.set(wx + dx, TERR, wz + dz, PAND)
    # lamp posts round the yard
    for (x, z) in ((52, -42), (72, -42), (58, -48), (70, -48), (44, -40), (80, -44), (90, -40)):
        if floor_ok(C, x, TERR + 1, z):
            lamp_post(C, x, TERR + 1, z, 3, LANT)
    # crates, casks and a cart
    for (x, z, n) in ((47, -48, 2), (48, -48, 1), (75, -44, 2), (76, -44, 1), (86, -42, 2), (66, -47, 1)):
        for k in range(n):
            if C.free(x, TERR + 1 + k, z):
                barrel(C, x, TERR + 1 + k, z, "up" if k else "north")
    chest(C, 49, TERR + 1, -48, "south", "lvl_station")
    # baleen drying racks (iron bars on spruce frames)
    for x in range(76, 82):
        C.set(x, TERR + 1, -40, SPR_FENCE if x in (76, 81) else "iron_bars")
        C.set(x, TERR + 2, -40, SPR_FENCE if x in (76, 81) else "iron_bars")
        C.set(x, TERR + 3, -40, SPR_SL + "[type=bottom,waterlogged=false]")
    # rope coils and a capstan
    C.set(56, TERR + 1, -40, SPR_LOG + "[axis=y]")
    C.set(56, TERR + 2, -40, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(56 + dx, TERR + 1, -40 + dz, CHAIN_X if dx else CHAIN_Z)
    spawner(C, 74, TERR + 1, -38, MOB_WRECKER)
    spawner(C, 50, TERR + 1, -44, MOB_WRECKER)


def quay_edges(C):
    """Bollards and a rail on the quay's sea rim (except at stairs)."""
    x0, z0, x1, z1 = TERRACE
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if C.kind.get((x, z)) != "quay":
                continue
            edge = False
            for (dx, dz) in N4:
                tn = C.top.get((x + dx, z + dz), -15)
                if tn <= TERR - 3:
                    edge = True
            if not edge or (x, TERR + 1, z) in C.keep or not C.free(x, TERR + 1, z):
                continue
            if 62 <= x <= 74 and z >= -37:
                continue
            if (x * 3 + z) % 9 == 0:
                C.set(x, TERR + 1, z, IRON)
                C.set(x, TERR + 2, z, "iron_bars" if False else SPR_FENCE)
            elif (x + z) % 2 == 0 or True:
                C.set(x, TERR + 1, z, SPR_FENCE)


def mess_hall(C):
    """The flensers' mess and bunkhouse: long tables and benches, a hearth, the tally desk, bunks; a jawbone arch
    over its door."""
    x0, z0, x1, z1 = MESS
    F = TERR + 1
    def wall(x, y, z):
        if (x in (x0, x1)) and (z in (z0, z1)):
            return SPR_LOG + "[axis=y]"
        if y == F + 5:
            return "stripped_spruce_log[axis=x]" if z in (z0, z1) else "stripped_spruce_log[axis=z]"
        return "cobblestone" if y == F else (SPR if hash3(x, y, z, 841) < 0.8 else "stripped_spruce_wood[axis=y]")
    box(C, x0, F, z0, x1, F + 5, z1, wall, floor=lambda x, z: SPR if (x + z) % 5 else DOAK, ceil=None)
    gable(C, x0, z0, x1, z1, F + 6, "z", SLATE_ST, SLATE, over=1, gable_wall=lambda x, y, z: SPR)
    # rafters and a ceiling
    for z in range(z0 + 1, z1):
        if (z - z0) % 3 == 0:
            for x in range(x0 + 1, x1):
                C.set(x, F + 6, z, "stripped_spruce_log[axis=x]")
    # windows
    for z in range(z0 + 2, z1 - 1, 3):
        for x in (x0, x1):
            C.set(x, F + 2, z, PANE)
            C.set(x, F + 3, z, PANE)
    # door (south) and the jawbone arch over it
    xd = (x0 + x1) // 2
    for x in (xd, xd + 1):
        for y in (F, F + 1, F + 2):
            C.clear(x, y, z1)
    for k in range(9):
        a = math.pi * k / 8
        for s in (-1, 1):
            x = round(xd + 0.5 + s * (3.2 * math.cos(a) if s > 0 else -3.2 * math.cos(a)))
            y = F + round(6.5 * math.sin(a))
            C.set(round(xd + 0.5 + 3.2 * math.cos(a)), y, z1 + 2, BONE)
    for y in range(F, F + 2):
        C.set(xd - 3, y, z1 + 2, BONE)
        C.set(xd + 4, y, z1 + 2, BONE)
    # long tables with benches (two rows along z)
    for xt in (x0 + 4, x1 - 4):
        for z in range(z0 + 3, z1 - 2):
            C.set(xt, F, z, TABLE)
            C.set(xt - 1, F, z, stair(SPR_ST, "east"))
            C.set(xt + 1, F, z, stair(SPR_ST, "west"))
            if z % 3 == 0:
                C.set(xt, F + 1, z, "candle[candles=3,lit=true,waterlogged=false]")
    # the hearth on the north wall
    hx = (x0 + x1) // 2
    for x in range(hx - 2, hx + 3):
        for y in range(F, F + 6):
            C.set(x, y, z0 + 1, BRICK if abs(x - hx) == 2 or y >= F + 3 else BRICK)
    C.set(hx, F, z0 + 1, "campfire[lit=true,facing=south,signal_fire=false,waterlogged=false]")
    C.set(hx - 1, F, z0 + 1, BRICK)
    C.set(hx + 1, F, z0 + 1, BRICK)
    C.set(hx, F + 1, z0 + 1, AIR)
    C.set(hx, F, z0 + 2, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for y in range(F + 6, F + 14):
        C.set(hx, y, z0 + 1, BRICK if y < F + 13 else "campfire[lit=true,facing=north,signal_fire=false,"
                                                       "waterlogged=false]")
    # bunks along the west wall, the tally desk in the north-east corner
    for z in range(z0 + 2, z1 - 2, 3):
        C.bp.bed(x0 + 1, F, z, "east", "brown")
        C.set(x0 + 1, F + 2, z, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
    C.set(x1 - 1, F, z0 + 2, TABLE)
    C.set(x1 - 1, F + 1, z0 + 2, "lectern[facing=west,has_book=false,powered=false]" if False else
          "candle[candles=2,lit=true,waterlogged=false]")
    C.set(x1 - 2, F, z0 + 2, CHAIR + "[facing=east]")
    chest(C, x1 - 1, F, z0 + 3, "west", "lvl_mess")
    barrel(C, x1 - 1, F, z1 - 1)
    barrel(C, x1 - 1, F + 1, z1 - 1)
    for (x, z) in ((x0 + 4, z0 + 4), (x1 - 4, z0 + 4), (x0 + 4, z1 - 3), (x1 - 4, z1 - 3)):
        hang(C, x, F + 4, z, LANT_H)
    spawner(C, (x0 + x1) // 2, F, (z0 + z1) // 2, MOB_DROWNED)


def cooperage(C):
    x0, z0, x1, z1 = COOP
    F = TERR + 1
    def wall(x, y, z):
        if x in (x0, x1) and z in (z0, z1):
            return SPR_LOG + "[axis=y]"
        return DOAK if y > F else "cobblestone"
    box(C, x0, F, z0, x1, F + 3, z1, wall, ceil=None)
    gable(C, x0, z0, x1, z1, F + 4, "x", SPR_ST, SPR, over=1, gable_wall=DOAK)
    for x in (x0 + 3, x0 + 4):
        for y in (F, F + 1):
            C.clear(x, y, z1)
    C.set(x0 + 1, F, z0 + 1, "anvil[facing=east]")
    C.set(x0 + 2, F, z0 + 1, "grindstone[face=floor,facing=north]")
    C.set(x1 - 1, F, z0 + 1, "smithing_table")
    for (x, z) in ((x0 + 1, z1 - 1), (x0 + 1, z1 - 2), (x1 - 1, z1 - 1), (x1 - 2, z0 + 1)):
        barrel(C, x, F, z, "east")
    for x in range(x0 + 2, x1 - 1):
        C.set(x, F + 2, z0 + 1, SHELF + "[facing=south]")
    chest(C, x1 - 1, F, z1 - 2, "west", "lvl_station")
    hang(C, (x0 + x1) // 2, F + 3, (z0 + z1) // 2, LANT_H)
    # windows
    C.set(x0, F + 1, z0 + 3, PANE)
    C.set(x1, F + 1, z0 + 3, PANE)


def try_works(C, x, z, F):
    """One try-works: a brick furnace block with two copper try-pots on top and two fire mouths."""
    for dx in range(0, 6):
        for dz in range(0, 4):
            for y in range(F, F + 3):
                C.set(x + dx, y, z + dz, BRICK if hash3(x + dx, y, z + dz, 851) < 0.8 else "mud_bricks")
    for k in (0, 3):
        px = x + k
        for dx in (0, 1, 2):
            for dz in (0, 1, 2, 3):
                edge = dx in (0, 2) or dz in (0, 3)
                C.set(px + dx, F + 3, z + dz, CU_EX if edge else "water_cauldron[level=3]")
                if edge:
                    C.set(px + dx, F + 4, z + dz, COPPER_SL + "[type=bottom,waterlogged=false]")
        C.set(px + 1, F, z + 3, "campfire[lit=true,facing=south,signal_fire=false,waterlogged=false]")
        C.set(px + 1, F + 1, z + 3, IRON_SLAB + "[type=top,waterlogged=false]")


def rendering_house(C):
    """The rendering house: brick walls under a slate roof and two smokestacks; three try-works along the north wall,
    a copper cooling trough, casks, blubber hooks, the stirring gallery on the west wall."""
    x0, z0, x1, z1 = RENDER
    F = TERR + 1
    H = 9
    def wall(x, y, z):
        if (x - x0) % 8 == 0 or (x in (x0, x1) and z in (z0, z1)):
            return DSB if y < F + 1 else BRICK if (y - F) % 4 else "chiseled_stone_bricks"
        if y == F:
            return "cobblestone"
        return BRICK if hash3(x, y, z, 861) < 0.85 else ("mud_bricks" if hash3(x, y, z, 862) < 0.6 else
                                                        "cracked_stone_bricks")
    box(C, x0, F, z0, x1, F + H, z1, wall, floor=lambda x, z: "stone" if (x + z) % 3 else "cobblestone", ceil=None)
    gable(C, x0, z0, x1, z1, F + H + 1, "x", SLATE_ST, SLATE, over=1, gable_wall=BRICK)
    for x in range(x0 + 1, x1):
        if (x - x0) % 4 == 0:
            for z in range(z0 + 1, z1):
                C.set(x, F + H + 1, z, "stripped_spruce_log[axis=z]")
    # tall arched windows on the south wall, small ones north
    for x in range(x0 + 3, x1 - 2, 4):
        if abs(x - (x0 + x1) // 2) <= 1:
            continue
        for y in range(F + 2, F + 6):
            C.set(x, y, z1, PANE if y < F + 5 else "iron_bars")
        C.set(x, F + 7, z0, PANE)
    # the great door (south, 3 wide) and an iron door east
    xd = (x0 + x1) // 2
    for x in range(xd - 1, xd + 2):
        for y in range(F, F + 4):
            C.clear(x, y, z1)
    C.set(xd - 2, F + 4, z1, "chiseled_stone_bricks")
    C.set(xd + 2, F + 4, z1, "chiseled_stone_bricks")
    # three try-works along the north wall
    for k, tx in enumerate((x0 + 2, x0 + 9, x0 + 16)):
        try_works(C, tx, z0 + 1, F)
        # a hood and flue up into the roof
        for dx in range(1, 5):
            C.set(tx + dx, F + 6, z0 + 2, BRICK_SL + "[type=top,waterlogged=false]")
    # two smokestacks rising out of the roof
    for (sx, h) in ((x0 + 5, 46), (x0 + 19, 40)):
        for y in range(F + 6, h + 1):
            for dx in (-1, 0, 1):
                for dz in (0, 1, 2):
                    edge = dx != 0 or dz != 1
                    if edge:
                        C.set(sx + dx, y, z0 + dz, SOOT if y > h - 4 else (SMOKE if (y // 6) % 2 else BRICK))
                    else:
                        C.air(sx + dx, y, z0 + dz) if y > F + H + 3 else C.set(sx + dx, y, z0 + dz, SMOKE)
        for dx in (-2, 2):
            C.set(sx + dx, h - 6, z0 + 1, IRON)
        C.set(sx, h, z0 + 1, "campfire[lit=true,facing=north,signal_fire=true,waterlogged=false]")
    # the copper cooling trough along the south wall (west part), casks east
    for x in range(x0 + 2, xd - 3):
        C.set(x, F, z1 - 2, CU_WE)
        C.set(x, F, z1 - 3, "water_cauldron[level=3]" if x % 2 else CU_WE)
    for x in range(xd + 4, x1 - 3):
        for z in (z1 - 2, z1 - 3):
            for k in range(1 + (x % 2)):
                barrel(C, x, F + k, z, "east" if k == 0 else "up")
    # blubber hooks on chains from the tie beams
    for x in range(x0 + 4, x1 - 2, 4):
        hang(C, x, F + 4, (z0 + z1) // 2 + 1, "tripwire_hook[attached=false,facing=south,powered=false]", reach=8)
    # the stirring gallery: a catwalk along the west wall at F + 5, stair up from the floor
    gy = F + 5
    for z in range(z0 + 1, z1):
        for x in (x0 + 1, x0 + 2):
            C.set(x, gy - 1, z, TREAD)
            for y in range(gy, gy + 3):
                if C.free(x, y, z):
                    C.clear(x, y, z)
        railing(C, x0 + 3, gy, z, "east") if C.free(x0 + 3, gy, z) and z > z0 + 4 else None
    stair_run(C, [(x0 + 1, z1 - 1), (x0 + 2, z1 - 1)], "north", 5, F - 1, spec=BRICK_ST, support=BRICK)
    chest(C, x0 + 1, gy, z0 + 1, "south", "lvl_render")
    chest(C, xd + 6, F, z0 + 8, "south", "lvl_render")
    # the stirring deck in front of the try-works (feet F + 3, the pots in reach over their rims), stair up east
    for x in range(x0 + 3, x0 + 24):
        for z in (z0 + 5, z0 + 6):
            C.set(x, F + 3, z, SPR if x % 4 else DOAK)
            for y in range(F + 4, F + 7):
                C.clear(x, y, z)
        if x % 4 == 1:
            for y in (F, F + 1, F + 2):
                C.set(x, y, z0 + 6, SPR_FENCE)
        if x < x0 + 22:
            C.set(x, F + 4, z0 + 7, SPR_FENCE)
    stair_run(C, [(x0 + 22, z0 + 10), (x0 + 23, z0 + 10)], "north", 4, F - 1, spec=SPR_ST, support=SPR)
    # lamps
    for x in range(x0 + 3, x1 - 1, 5):
        hang(C, x, F + 6, z1 - 4, LANT_H)
    hang(C, x0 + 2, gy + 2, (z0 + z1) // 2, LANT_H)
    spawner(C, xd + 1, F, (z0 + z1) // 2 + 2, MOB_DROWNED)


def harpoon_cannon(C, x, z, facing):
    """A harpoon gun on the quay: a stepped iron plinth, a brass swivel, a long barrel with a barbed harpoon, a chain
    coil and a gunner's seat."""
    F = TERR + 1
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            C.set(x + dx, F - 1, z + dz, IRON if (dx or dz) else GEAR)
    C.set(x, F, z, IRON)
    C.set(x, F + 1, z, BRASS)
    fx, fz = DV[facing]
    for k in range(-1, 4):
        C.set(x + fx * k, F + 2, z + fz * k, COPPER if k in (-1, 0) else BRASS_SLAB + "[type=bottom,waterlogged=false]"
              if k == 3 else BRASS)
    C.set(x + fx * 4, F + 2, z + fz * 4, f"lightning_rod[facing={facing},powered=false,waterlogged=false]")
    C.set(x - fx * 2, F, z - fz * 2, stair(IRON_ST, facing))
    lx, lz = -fz, fx
    C.set(x + lx, F, z + lz, CHAIN_X if fz else CHAIN_Z)
    C.set(x - lx, F, z - lz, "barrel[facing=up,open=false]")


def harpoon_battery(C):
    for (x, z) in ((46, -38), (54, -38), (79, -38)):
        harpoon_cannon(C, x, z, "south")
    chest(C, 50, TERR + 1, -37, "north", "lvl_battery")


def flensing_crane(C):
    """A timber derrick on the quay rim with its boom out over the skull, a hook on chains and a winch."""
    bx, bz = 76, -40
    F = TERR + 1
    for dx in (0, 1):
        for dz in (0, 1):
            for y in range(F, F + 16):
                C.set(bx + dx, y, bz + dz, SPR_LOG + "[axis=y]" if (y - F) % 6 else "stripped_spruce_log[axis=y]")
    for y in (F + 5, F + 11):
        for dx in (-1, 2):
            C.set(bx + dx, y, bz, stair(SPR_ST, "west" if dx < 0 else "east", "top"))
    tip = (71, F + 19, -28)
    line3(C, (bx, F + 15, bz + 1), tip, SPR_LOG + "[axis=z]", force=True)
    line3(C, (bx + 1, F + 15, bz + 1), (tip[0] + 1, tip[1], tip[2]), SPR_LOG + "[axis=z]", force=True)
    for y in range(F + 6, tip[1]):
        C.put(tip[0], y, tip[2], CHAIN)
    C.set(tip[0], F + 5, tip[2], "iron_bars")
    C.set(tip[0], F + 4, tip[2], "tripwire_hook[attached=false,facing=north,powered=false]" if False else CHAIN)
    # the winch
    C.set(bx - 1, F, bz + 1, "barrel[facing=east,open=false]")
    C.set(bx - 2, F, bz + 1, VALVE + "[facing=west]")
    C.set(bx + 2, F, bz, LANT)


def quay_stair(C):
    """The grand quay stair from the terrace down to the shingle in front of the skull (9 wide)."""
    stair_run(C, [(x, -27) for x in range(63, 74)], "north", 10, 0, spec=SB_ST, support=MSB, support_min=-3)
    for z in range(-36, -26):
        for x in (62, 74):
            t = 10 - (z + 36) + (0 if z > -36 else 0)
            for y in range(-2, max(0, -27 - z + 11)):
                pass
    # side walls of the stair with lamps
    for i in range(10):
        z = -27 - i
        for x in (62, 74):
            for y in range(-2, i + 2):
                C.set(x, y, z, quay_stone(x, y, z))
            if i % 3 == 1:
                C.set(x, i + 2, z, LANT)


def tide_stair(C):
    """The tide stair: from the quay's south-west corner down along the cliff foot to the tideline ledge, then the
    ledge round to the sea cave's mouth."""
    stair_run(C, [(39, -26), (40, -26), (41, -26)], "north", 10, 0, spec="mossy_stone_brick_stairs",
              support=MSB, support_min=-8)
    for i in range(10):
        z = -26 - i
        C.set(42, i + 1, z, "mossy_stone_brick_wall" if i % 4 else "mossy_cobblestone")
        if i % 4 == 0:
            C.set(42, i + 2, z, LANT)
    # the tideline ledge round to the cave mouth (feet 1)
    walkway(C, [(40, 1, -25), (42, 1, -21), (44, 1, -16), (44, 1, -12), (40, 1, -12)], width=3,
            full=lambda x, z: "mossy_cobblestone" if hash01(x, z, 871) < 0.5 else MSB,
            half=lambda x, z: "mossy_stone_brick_slab", rails=True, support="mossy_cobblestone",
            rail_spec="mossy_cobblestone_wall", lamp_every=0, support_min=-8)
    # seaweed and wet stones along the cliff foot
    for (x, z) in ((45, -20), (46, -14), (46, -18)):
        if C.free(x, 1, z):
            C.set(x, 1, z, LANT)
            C.set(x, 0, z, "mossy_cobblestone")


def boathouse(C):
    """The boathouse on piles south of the quay: the sail loft at quay level, a gallery over the boat hall, two slips
    of sea water with whaleboats, a stair down to the deck, a wide opening to the sea."""
    x0, z0, x1, z1 = BOATH
    # piles and the slips' water
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(-8, 0):
                C.water(x, y, z)
            C.set(x, -9, z, "sand" if hash01(x, z, 881) < 0.6 else "gravel")
    def wall(x, y, z):
        if x in (x0, x1) and z in (z0, z1) or (z in (z0, z1) and (x - x0) % 7 == 0) or (x in (x0, x1) and
                                                                                         (z - z0) % 5 == 0):
            return SPR_LOG + "[axis=y]"
        return SPR if (y // 3) % 2 else "stripped_spruce_wood[axis=y]"
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(1, 17):
                if edge and not (z == z1 and 1 <= y <= 7 and x0 < x < x1):
                    C.set(x, y, z, wall(x, y, z))
                elif not edge:
                    C.air(x, y, z)
            # deck at y 0 except the slips
            slip = (84 <= x <= 87 or 90 <= x <= 92) and z >= z0 + 4
            if not slip:
                C.set(x, 0, z, SPR if (x + z) % 4 else DOAK)
                if (x - x0) % 4 == 0 and (z - z0) % 4 == 0:
                    for y in range(-8, 0):
                        C.set(x, y, z, SPR_LOG + "[axis=y]")
            else:
                C.air(x, 0, z)
                if (x in (84, 87, 90, 92)) and (z - z0) % 4 == 0:
                    for y in range(-8, -2):
                        C.set(x, y, z, SPR_LOG + "[axis=y]")
    # the loft at quay level over the north part, a gallery rail at its edge
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z0 + 8):
            C.set(x, TERR, z, SPR if (x + z) % 3 else DOAK)
            C.set(x, TERR - 1, z, "stripped_spruce_log[axis=x]" if z % 3 == 0 else SPR)
    for x in range(x0 + 1, x1):
        if C.free(x, TERR + 1, z0 + 8):
            railing(C, x, TERR + 1, z0 + 7, "south") if False else None
    gable(C, x0, z0, x1, z1, 17, "z", SLATE_ST, SLATE, over=1, gable_wall=lambda x, y, z: SPR)
    # door from the quay (north wall, at quay level)
    for x in (88, 89):
        for y in (TERR + 1, TERR + 2):
            C.clear(x, y, z0)
    # the stair from the loft down to the deck along the east wall
    stair_run(C, [(x1 - 3, z0 + 13), (x1 - 2, z0 + 13), (x1 - 1, z0 + 13)], "north", 10, 0, spec=SPR_ST,
              support=SPR)
    # the loft's edge: a rail along z0 + 8 (except over the stair)
    for x in range(x0 + 1, x1 - 3):
        if C.free(x, TERR + 1, z0 + 7):
            railing(C, x, TERR + 1, z0 + 7, "south")
    # sail loft furnishing
    for x in range(x0 + 1, x0 + 6):
        C.set(x, TERR + 1, z0 + 1, "white_wool" if x % 2 else "light_gray_wool")
        C.set(x, TERR + 2, z0 + 1, "white_carpet")
    C.set(x0 + 1, TERR + 1, z0 + 3, "loom[facing=east]")
    chest(C, x0 + 1, TERR + 1, z0 + 5, "east", "lvl_boathouse")
    for z in (z0 + 2, z0 + 4):
        C.set(x1 - 4, TERR + 3, z, SHELF + "[facing=west]") if False else None
    for x in range(x0 + 7, x1 - 4):
        C.set(x, TERR + 1, z0 + 1, "barrel[facing=south,open=false]") if x % 2 else None
    # whaleboats in the slips and on the deck
    whaleboat(C, 85, 0, z0 + 10, axis="z", n=9)
    whaleboat(C, 91, 0, z0 + 11, axis="z", n=7)
    whaleboat(C, 94, 1, z0 + 6, axis="z", n=5)
    # oars, harpoon racks on the walls
    for z in range(z0 + 9, z1 - 1, 2):
        C.set(x0 + 1, 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        C.set(x0 + 1, 3, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # lamps: hung in the boat hall and the loft
    for (x, z) in ((86, z0 + 10), (91, z0 + 14), (85, z0 + 3), (91, z0 + 3), (94, z0 + 10)):
        hang(C, x, TERR + 5 if z < z0 + 8 else 7, z, LANT_H)
    for (x, z) in ((83, z0 + 12), (88, z0 + 6), (95, z0 + 4)):
        if floor_ok(C, x, 1, z):
            C.set(x, 1, z, LANT)
    spawner(C, 88, 1, z0 + 10, MOB_CRAB)


# ------------------------------------------------------------------ the leviathan
def bone(axis="y"):
    return f"{BONE}[axis={axis}]"


def skull(C):
    """The skull on the shingle: a hollow cranium (a bony hall), the upper jaw arching north over the open lower
    jaws, teeth, eye sockets; the foramen opens south into the ribcage dock."""
    cx, cy, cz = SPINE_X, 1, -12
    # cranium: a hollow ellipsoid shell above the beach (rx 8, ry 9, rz 7)
    rx, ry, rz = 8.5, 9.5, 7.5
    for x in range(cx - 10, cx + 11):
        for z in range(cz - 9, cz + 9):
            for y in range(1, cy + 11):
                e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if e > 1.0:
                    continue
                if e > 0.72:
                    C.set(x, y, z, bone("z") if hash3(x, y, z, 891) < 0.85 else "calcite")
                else:
                    C.air(x, y, z)
    # eye sockets, the foramen (south) and the throat (north)
    for s in (-1, 1):
        for y in range(5, 8):
            for z in range(cz - 2, cz + 1):
                C.air(cx + s * 8, y, z)
                C.air(cx + s * 7, y, z)
    for x in range(cx - 2, cx + 3):
        for y in range(1, 6):
            for z in range(cz + 5, cz + 9):
                C.clear(x, y, z)
            for z in range(cz - 9, cz - 5):
                C.clear(x, y, z)
    # the upper jaw (rostrum): a narrowing vault north to z -32
    for z in range(cz - 20, cz - 5):
        t = (cz - 5 - z) / 15.0
        hw = 6.0 - 3.5 * t
        top = 9 - 4 * t
        for x in range(cx - 7, cx + 8):
            dx = abs(x - cx)
            if dx > hw + 0.5:
                continue
            y = round(top - (dx / max(hw, 1)) ** 2 * 3.5)
            C.set(x, y, z, bone("z"))
            if dx > hw - 0.6:
                C.set(x, y - 1, z, bone("z"))
                if (z % 2 == 0) and y - 2 >= 2:
                    C.set(x, y - 2, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    # the lower jaws: two mandibles on the shingle, open wide
    for s in (-1, 1):
        for z in range(cz - 22, cz - 4):
            t = (cz - 4 - z) / 18.0
            x = round(cx + s * (6.5 + 3.0 * t))
            for y in (1, 2):
                C.set(x, y, z, bone("z"))
                C.set(x + s, y, z, bone("z")) if y == 1 else None
            if z % 2 == 0:
                C.set(x, 3, z, "pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
    # inside the skull: a bony hall with lamps (whale-oil lamps on bone stands) and a chest
    for (x, z) in ((cx - 4, cz - 2), (cx + 4, cz - 2), (cx - 4, cz + 3), (cx + 4, cz + 3)):
        C.set(x, 1, z, bone("y"))
        C.set(x, 2, z, LANT)
    chest(C, cx + 5, 1, cz, "west", "lvl_dock")
    hang(C, cx, 6, cz, LANT_H, reach=6)
    hang(C, cx, 6, cz - 13, LANT_H, reach=6)


def rib(C, z0, side):
    """One rib: an arc from the vertebra (y 18) down to the waterline 12 out, swept back a little; 2 thick."""
    pts = []
    for k in range(0, 61):
        th = math.radians(k * 1.75)
        dx = 12.5 * math.sin(th)
        y = 1 + 17.5 * math.cos(th) - 1.5 * (1 - math.cos(th))
        z = z0 - 2.0 * math.sin(th)
        pts.append((SPINE_X + side * dx, y, z))
    for (x, y, z) in pts:
        X, Y, Z = round(x), round(y), round(z)
        if Y < -3:
            continue
        ax = "y" if abs(X - SPINE_X) > 8 else "x"
        for (ox, oz) in ((0, 0), (0, 1)):
            C.set(X + ox, Y, Z + oz, bone(ax))
    # anchor under water: a pile
    X, Z = round(SPINE_X + side * 12.5), round(z0 - 2.0)
    for y in range(-8, -2):
        C.set(X, y, Z, bone("y"))


def leviathan(C):
    """Spine (vertebrae with processes), seven rib pairs over the dock, the tail sinking south into the sea."""
    skull(C)
    # vertebrae from the skull back (z -4) to the tail tip (z 66)
    for z in range(-4, 67):
        if z <= 36:
            y0, r = 18, 1
        else:
            t = (z - 36) / 30.0
            y0, r = round(18 - 20 * t * t - 4 * t), (1 if t < 0.6 else 0)
        seg = (z % 3) != 2
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if seg or (dx == 0 and dy == 0):
                    if y0 + dy >= -3:
                        C.set(SPINE_X + dx, y0 + dy, z, bone("z"))
        if z % 3 == 0 and z <= 50:
            for k in range(1, 4 if z <= 36 else 2):
                if y0 + r + k >= -3:
                    C.set(SPINE_X, y0 + r + k, z, bone("y"))
            for s in (-1, 1):
                C.set(SPINE_X + s * (r + 1), y0, z, bone("x"))
                C.set(SPINE_X + s * (r + 2), y0, z, bone("x"))
    # the fluke at the tail tip, half sunk
    for x in range(SPINE_X - 7, SPINE_X + 8):
        for z in range(63, 70):
            if abs(x - SPINE_X) + abs(z - 66) * 1.6 <= 8:
                C.set(x, -2 if abs(x - SPINE_X) < 4 else -1, z, bone("x"))
    for z in RIBS:
        rib(C, z, -1)
        rib(C, z, 1)


def dock(C):
    """The ribcage dock: two plank jetties on piles inside the ribs, the basin between them, moored whaleboats,
    lamps on the ribs, the lamp-lighter's ladder tower up to the spine catwalk and its cache."""
    for x in range(SPINE_X - 9, SPINE_X + 10):
        for z in range(-5, 40):
            jet = abs(x - SPINE_X) in (6, 7, 8)
            if jet:
                C.set(x, 0, z, SPR if (z % 5) else DOAK)
                for y in range(1, 4):
                    if C.free(x, y, z):
                        C.clear(x, y, z)
                if z % 4 == 0 and abs(x - SPINE_X) in (6, 8):
                    for y in range(-8, 0):
                        C.set(x, y, z, SPR_LOG + "[axis=y]")
                    C.set(x, 1, z, SPR_FENCE) if abs(x - SPINE_X) == 8 and z % 8 == 0 else None
            elif abs(x - SPINE_X) <= 5:
                for y in range(-6, 0):
                    if C.get(x, y, z) is None:
                        C.water(x, y, z)
                if C.get(x, 0, z) is None:
                    C.air(x, 0, z)
                C.set(x, -7, z, "sand") if C.get(x, -7, z) is None else None
    # the landing from the skull's foramen onto the jetties (a plank deck z -5..-3)
    for x in range(SPINE_X - 8, SPINE_X + 9):
        for z in range(-5, -2):
            C.set(x, 0, z, SPR if (x + z) % 3 else DOAK)
            for y in range(-8, 0):
                if (x - SPINE_X) % 4 == 0 and z == -4:
                    C.set(x, y, z, SPR_LOG + "[axis=y]")
            for y in range(1, 4):
                if C.free(x, y, z):
                    C.clear(x, y, z)
    # swim-up ladders on the jetties' inner faces
    for z in (6, 16, 26, 36):
        for s, f in ((-1, "east"), (1, "west")):
            C.water(SPINE_X + s * 5, -1, z, f"ladder[facing={f},waterlogged=true]")
            C.set(SPINE_X + s * 5, 0, z, LADDER.format(f))
            C.set(SPINE_X + s * 6, 1, z, "air") if C.free(SPINE_X + s * 6, 1, z) else None
    # boats in the basin (hull at the waterline)
    whaleboat(C, SPINE_X - 2, 0, 8, axis="z", n=9)
    whaleboat(C, SPINE_X + 2, 0, 24, axis="z", n=7)
    # lamps hung under the ribs over the jetties
    for z in RIBS:
        for s in (-1, 1):
            hang(C, SPINE_X + s * 7, 5, round(z - 1.0), LANT_H, reach=14)
    # crates and nets on the jetties
    for (x, z) in ((SPINE_X - 7, 3), (SPINE_X + 7, 12), (SPINE_X + 7, 13), (SPINE_X - 7, 30)):
        barrel(C, x, 1, z)
    chest(C, SPINE_X + 7, 1, 30, "west", "lvl_dock")
    spawner(C, SPINE_X - 7, 1, 18, MOB_DROWNED)
    # the lamp-lighter's ladder tower on the east jetty up to the spine catwalk (feet 21)
    lx, lz = SPINE_X + 7, -1
    for y in range(1, 21):
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1)):
            C.set(lx + dx, y, lz + dz, SPR_LOG + "[axis=y]" if dx else SPR)
        C.set(lx, y, lz, LADDER.format("north"))
        C.set(lx, y, lz - 1, AIR) if y < 3 else None
    for y in (8, 14):
        C.set(lx, y, lz + 1, SPR)
    # a landing on top, a plank catwalk along the spine to the tail
    for x in range(SPINE_X - 1, lx + 2):
        for z in (lz - 1, lz, lz + 1):
            C.set(x, 20, z, SPR)
    C.set(lx, 20, lz, LADDER.format("north"))
    C.set(lx, 21, lz + 1, SPR_FENCE)
    for z in range(-3, 37):
        for x in (SPINE_X - 1, SPINE_X, SPINE_X + 1):
            if C.free(x, 20, z) or "bone" in (C.get(x, 20, z) or ""):
                C.set(x, 20, z, SPR_SL + "[type=top,waterlogged=false]")
            for y in (21, 22, 23):
                if not C.free(x, y, z) and "bone" in (C.get(x, y, z) or ""):
                    C.air(x, y, z)
                C.keep.add((x, y, z))
        for x in (SPINE_X - 2, SPINE_X + 2):
            if x == SPINE_X + 2 and lz - 1 <= z <= lz + 1:
                continue
            if C.free(x, 21, z):
                C.set(x, 21, z, SPR_FENCE)
    C.set(SPINE_X - 2, 22, 8, LANT)
    C.set(SPINE_X + 2, 22, 20, LANT)
    C.set(SPINE_X - 2, 22, 32, LANT)
    chest(C, SPINE_X, 21, 35, "north", "lvl_spine")
    C.set(SPINE_X, 21, 36, SPR_FENCE)


# ------------------------------------------------------------------ the stair tower (cliff stair, a shortcut)
def stair_tower(C):
    x0, z0, x1, z1 = STAIRT
    cx, cz = STC
    def wall(x, y, z):
        if x in (x0, x1) and z in (z0, z1):
            return DSB if y < 14 else PAND
        h = hash3(x, y, z, 901)
        return MSB if y < 14 and h < 0.4 else (CSB if h < 0.1 else SB)
    box(C, x0, TERR + 1, z0, x1, G + 4, z1, wall, floor=SB, ceil=None)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                C.set(x, G + 5, z, SB)
                if (x + z) % 2 == 0:
                    C.set(x, G + 6, z, SB_WALL)
            else:
                C.set(x, G + 5, z, SLATE)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if math.hypot(x - cx, z - cz) < 1.6:
                for y in range(TERR + 1, G + 5):
                    C.set(x, y, z, DSB if y % 4 else PAND)
    segs = [(-20, 0, TERR + 1, TERR + 1), (0, 270, TERR + 1, TERR + 1 + 8), (270, 540, TERR + 9, G + 1),
            (540, 560, G + 1, G + 1)]
    spiral(C, [(a0, a1, s0, s1) for (a0, a1, s0, s1) in segs], 3.6, 3.2, TREAD, TREAD_SLAB, IRON, cx=cx, cz=cz,
           rmax=6, rail_rmin=5.0)
    # bottom door (east, iron; the lever inside only: the stair opens back down, never up)
    iron_door(C, x1, TERR + 1, cz, "east")
    lever(C, x1 - 1, TERR + 2, cz - 1, "west")
    for y in (TERR + 1, TERR + 2, TERR + 3):
        C.clear(x1 - 1, y, cz)
        C.clear(x1 + 1, y, cz)
    C.set(x1 + 1, TERR, cz, SB)
    # top door (west) onto the bridge
    for z in range(cz - 1, cz + 2):
        for y in range(G + 1, G + 4):
            C.clear(x0, y, z)
            C.clear(x0 + 1, y, z)
        C.set(x0, G, z, SB)
        C.set(x0 + 1, G, z, SB)
    # slit windows and lamps
    for y in (TERR + 4, TERR + 10, G - 1):
        for (x, z) in ((cx, z0), (cx, z1), (x0, cz + 3), (x1, cz - 3)):
            if C.solid(x, y, z):
                C.set(x, y, z, PANE)
                C.set(x, y + 1, z, PANE)
    for y in (TERR + 4, TERR + 12, G + 2):
        for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            x, z = cx + dx, cz + dz
            if C.solid(x, y, z):
                C.set(x, y, z, EDISON)
    # the bridge to the plateau rim (an arch under it)
    for x in range(20, x0):
        for z in range(cz - 1, cz + 2):
            C.set(x, G, z, SB if (x + z) % 3 else PAND)
            for y in range(G + 1, G + 5):
                if C.free(x, y, z):
                    C.clear(x, y, z)
        for z in (cz - 2, cz + 2):
            C.set(x, G, z, SB)
            C.set(x, G + 1, z, SB_WALL)
        k = x0 - x
        under = G - 1 - (2 if 2 <= k <= 4 else 0)
        for z in range(cz - 2, cz + 3):
            for y in range(G - 6, under + 1):
                if C.free(x, y, z):
                    C.set(x, y, z, SB)
    C.set(x0 - 3, G + 2, cz - 2, LANT)
    C.set(x0 - 3, G + 2, cz + 2, LANT)


# ------------------------------------------------------------------ the sea caves
def blob_cells(cx, cz, rx, rz, seed, grow=0.0):
    out = []
    for x in range(int(cx - rx) - 3, int(cx + rx) + 4):
        for z in range(int(cz - rz) - 3, int(cz + rz) + 4):
            e = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 + 0.45 * (fbm(x, z, 6.0, seed) - 0.5) - grow
            if e <= 1.0:
                out.append((x, z, e))
    return out


def cave_room(C, spec, seed, floor=1):
    cx, cz, rx, rz, h = spec
    cells = blob_cells(cx, cz, rx, rz, seed)
    for (x, z, e) in cells:
        top = floor + max(3, int(h * math.sqrt(max(0.0, 1.0 - e)) + 2.0 * (fbm(x, z, 4.0, seed + 1) - 0.5))) - 1
        C.set(x, floor - 1, z, rock(x, floor - 1, z) if hash01(x, z, seed + 2) < 0.7 else "gravel")
        for y in range(floor, top + 1):
            C.air(x, y, z)
        # stalactites
        if hash01(x, z, seed + 3) < 0.06 and top - floor > 4:
            C.set(x, top, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    return {(x, z) for (x, z, e) in cells}


def tunnel(C, pts, w, h, floor_fn, seed):
    """A rock tunnel along a polyline [(x, z)] with feet floor_fn(t) (t 0..1 along the line), w wide, h high."""
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) or 1.0
    acc = 0.0
    done = set()
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L * 3) + 1
        for i in range(n + 1):
            t = i / n
            px, pz = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            f = floor_fn((acc + L * t) / total)
            for x in range(int(px - w), int(px + w) + 2):
                for z in range(int(pz - w), int(pz + w) + 2):
                    if math.hypot(x - px, z - pz) > w / 2.0 + 0.3 * (vnoise(x, z, 3.0, seed) - 0.3):
                        continue
                    if (x, z) in done:
                        continue
                    done.add((x, z))
                    ff = int(round(f))
                    C.set(x, ff - 1, z, rock(x, ff - 1, z))
                    for y in range(ff, ff + h):
                        C.clear(x, y, z) if y < ff + 3 else C.air(x, y, z)
        acc += L
    return done


def sea_caves(C):
    """The tide grotto, the smugglers' hole, the flooded hall round its sea pool, the rock stair, the cistern."""
    # the mouth on the east cliff and the tide grotto
    tunnel(C, [(45, -12), (39, -12), (35, -12)], 4, 5, lambda t: 1, 931)
    A = cave_room(C, CAVE_A, 932)
    # tide pools in the grotto with kelp and sea pickles
    for (x, z) in A:
        if ((x - 27) / 4.0) ** 2 + ((z + 8) / 2.5) ** 2 <= 1.0 + 0.4 * (fbm(x, z, 3.0, 933) - 0.5):
            C.water(x, 0, z)
            C.water(x, -1, z)
            C.set(x, -2, z, "sand")
            if hash01(x, z, 934) < 0.25:
                C.set(x, -1, z, "kelp_plant")
                C.set(x, 0, z, "kelp")
            elif hash01(x, z, 935) < 0.2:
                C.set(x, -1, z, PICKLE)
    for (x, z) in ((24, -15), (33, -14), (30, -6), (21, -9)):
        if floor_ok(C, x, 1, z):
            C.set(x, 1, z, SPR_FENCE)
            C.set(x, 2, z, LANT)
    spawner(C, 26, 1, -16, MOB_CRAB)
    chest(C, 34, 1, -8, "west", "lvl_grotto")
    # the smugglers' hole (optional, north)
    tunnel(C, [(25, -17), (23, -24), (21, -30)], 3, 4, lambda t: 1, 936)
    cave_room(C, CAVE_B, 937)
    whaleboat(C, 18, 1, -35, axis="x", n=7)
    for (x, z, n) in ((24, -36, 2), (24, -35, 1), (15, -32, 2), (16, -38, 1)):
        for k in range(n):
            if C.free(x, 1 + k, z):
                barrel(C, x, 1 + k, z)
    chest(C, 23, 1, -32, "west", "lvl_smugglers")
    chest(C, 16, 1, -31, "east", "lvl_smugglers")
    C.set(20, 1, -30, SPR_FENCE)
    C.set(20, 2, -30, LANT)
    hang(C, 19, 4, -35, LANT_H, reach=4)
    # the passage west to the flooded hall
    tunnel(C, [(20, -10), (14, -8), (9, -7)], 4, 5, lambda t: 1, 938)
    Cc = cave_room(C, CAVE_C, 939)
    # the sea pool: two deep, a channel of black water, the wreck of a ketch's ribs in it
    pool = set()
    for (x, z) in Cc:
        px, pz, prx, prz = POOL_C
        if ((x - px) / prx) ** 2 + ((z - pz) / prz) ** 2 + 0.5 * (fbm(x, z, 4.0, 940) - 0.5) <= 1.0:
            pool.add((x, z))
            C.water(x, 0, z)
            C.water(x, -1, z)
            C.set(x, -2, z, "gravel" if hash01(x, z, 941) < 0.5 else "sand")
            h = hash01(x, z, 942)
            if h < 0.07:
                C.set(x, -1, z, PICKLE)
            elif h < 0.2:
                C.set(x, -1, z, "seagrass")
    # pool rim: a low kerb of wet stone where it meets the walkable ledge
    for (x, z) in pool:
        for (dx, dz) in N4:
            q = (x + dx, z + dz)
            if q in pool or q not in Cc:
                continue
            C.set(q[0], 0, q[1], "mossy_cobblestone")
    # the wreck's ribs in the pool
    for k, z in enumerate((-4, -1, 2)):
        for i in range(-4, 5):
            y = round(0 + 4 * math.cos(i / 5.0 * math.pi / 2))
            x = -6 + i
            if (x, z) in pool:
                C.set(x, max(y, 0), z, "stripped_dark_oak_wood[axis=y]" if abs(i) > 2 else DOAK)
    # sea lanterns set in the pool bed and lamps on posts round the ledge
    for (x, z) in ((-8, -2), (-3, 1), (-6, 2)):
        if (x, z) in pool:
            C.set(x, -2, z, "sea_lantern")
    for (x, z) in ((5, -9), (-14, -8), (-17, 2), (-12, 8), (2, 8), (6, 3), (-4, -11), (-19, -4)):
        if (x, z) in Cc and (x, z) not in pool and floor_ok(C, x, 1, z):
            C.set(x, 1, z, SPR_FENCE)
            C.set(x, 2, z, LANT)
    for (x, z) in ((-10, -6), (0, 2), (-6, 6)):
        hang(C, x, 6, z, LANT_H, reach=6)
    spawner(C, -16, 1, -2, MOB_WRAITH)
    spawner(C, 2, 1, -10, MOB_DROWNED)
    chest(C, -18, 1, 4, "east", "lvl_caves")
    # a drowned keeper's grave by the pool
    C.set(-14, 1, 6, "cobblestone")
    C.set(-14, 2, 6, "stone_brick_wall")
    candle(C, -13, 1, 6, 3, "white")
    # the passage from the hall's south-east to the rock stair
    tunnel(C, [(4, 8), (9, 12), (13, 14)], 4, 5, lambda t: 1, 943)
    rock_stair(C)
    cistern(C)


def rock_stair(C):
    """A spiral stair round a stone newel in a rock shaft, from the caves (feet 1) up to the cistern (feet 15)."""
    cx, cz = SHAFT_D
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            if d < 1.6:
                for y in range(0, 20):
                    C.set(x, y, z, SB if y % 5 else "chiseled_stone_bricks")
            elif d <= 5.2:
                C.set(x, 0, z, rock(x, 0, z))
    segs = [(210, 240, 1, 1), (240, 540, 1, 8), (540, 830, 8, 15), (830, 860, 15, 15)]
    spiral(C, segs, 3.4, 3.2, "cobblestone", "cobblestone_slab", "cobblestone", cx=cx, cz=cz, rmax=6, rail_rmin=4.9)
    for y in (4, 9, 13, 17):
        for a in (45, 225):
            x, z = polar(5.4, a + y * 20, (cx, cz))
            x, z = round(x), round(z)
            if C.get(x, y, z) is None or C.solid(x, y, z):
                C.set(x, y, z, "sea_lantern" if y < 10 else EDISON)
    # the exit corridor west to the cistern (feet 15)
    for x in range(CIST[2] + 1, cx - 1):
        for z in range(19, 23):
            C.set(x, 14, z, SB)
            for y in range(15, 19):
                C.clear(x, y, z) if z < 22 else C.air(x, y, z)


def cistern(C):
    """The cistern under the tower: a vaulted rainwater tank in the rock, piers, a hand pump, the oil cellar's
    casks; its stair climbs into the base hall."""
    x0, z0, x1, z1 = CIST
    F = 15
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, F - 1, z, SB if (x + z) % 2 else PAND)
            top = F + 6 - (1 if x in (x0, x1) or z in (z0, z1) else 0)
            for y in range(F, top + 1):
                C.air(x, y, z)
            C.set(x, top + 1, z, SB)
    # piers
    for (px, pz) in ((x0 + 3, z0 + 5), (x1 - 3, z0 + 5), (x0 + 3, z0 + 13), (x1 - 3, z0 + 13)):
        for y in range(F, F + 7):
            C.set(px, y, pz, SB if y % 3 else "chiseled_stone_bricks")
    # the tank (west half)
    for x in range(x0 + 1, x0 + 7):
        for z in range(z0 + 7, z0 + 12):
            edge = x in (x0 + 1, x0 + 6) or z in (z0 + 7, z0 + 11)
            if edge:
                C.set(x, F, z, SB_WALL if False else "stone_bricks")
            else:
                C.water(x, F - 1, z)
                C.water(x, F, z)
                C.set(x, F - 2, z, "clay")
    C.set(x0 + 3, F + 1, z0 + 7, "iron_bars")
    C.set(x0 + 3, F + 2, z0 + 7, COPPER)
    C.set(x0 + 3, F + 3, z0 + 7, VALVE + "[facing=south]")
    for y in range(F + 1, F + 7):
        C.set(x0 + 4, y, z0 + 7, "copper_pipe[axis=y]" if False else PIPES)
    # the oil cellar: casks along the east wall
    for z in range(z0 + 1, z1, 2):
        for k in range(2):
            barrel(C, x1 - 1, F + k, z, "west")
    chest(C, x1 - 1, F, z0 + 2, "west", "lvl_cistern")
    spawner(C, x0 + 3, F, z0 + 2, MOB_MITE)
    for (x, z) in ((x0 + 5, z0 + 3), (x1 - 4, z0 + 9), (x0 + 5, z1 - 3), (x1 - 5, z1 - 3)):
        hang(C, x, F + 4, z, LANT_H, reach=4)
    # the stair up into the base hall (x -1..1, from z 18 north to z 7)
    stair_run(C, [(-1, 18), (0, 18), (1, 18)], "north", 12, F - 1, spec=SB_ST, support=SB)
    for i in range(12):
        z = 18 - i
        for x in (-2, 2):
            for y in range(F, F + 1 + i):
                if C.free(x, y, z) and y > G - 4:
                    C.set(x, y, z, SB)


# ------------------------------------------------------------------ the lighthouse
def r_out(y):
    """Outer radius of the lighthouse body at height y."""
    if y <= 26:
        return 18.5
    if y <= 33:
        return 18.5 - (y - 26) * 0.35
    if y <= 99:
        return 15.5 - (y - 34) * (3.5 / 65.0)
    if y <= 107:
        return 12.0 + (y - 99) * 1.06
    return RD


def body_spec(x, y, z, d, a):
    """The skin: a dark granite-and-tuff plinth, then white masonry wound with an oxblood spiral band; brass string
    courses at the storeys; the corbels dark iron with brass rivet rings."""
    h = hash3(x, y, z, 951)
    if y <= 33:
        if y <= 28:
            return MSB if h < 0.35 else (DSB if h < 0.7 else TUFB)
        return DSB if h < 0.5 else (TUFB if h < 0.8 else "polished_deepslate")
    if y >= 100:
        if y == 107 or (y - 100) % 3 == 0:
            return BRASS if d > r_out(y) - 0.6 else IRON
        return IRON if h < 0.8 else DIB
    if y in [f - 1 for f in FLOORS[1:]] + [LF - 1]:
        return BRASS if d > r_out(y) - 0.7 else CALC
    phase = (a / 360.0 * 30.0 + y * 1.0) % 30.0
    if phase < 9.5:
        return RED if h < 0.85 else RED2
    if y < 45 and h < 0.12:
        return "diorite"
    return CALC if h < 0.7 else (PDIO if h < 0.95 else "white_concrete")


def tower_shell(C):
    """Walls (rooms keep radius R_IN), the storey floors, the interior air, the corbel flare, the gallery deck."""
    R = 22
    for x in range(TX - R, TX + R + 1):
        for z in range(TZ - R, TZ + R + 1):
            d = dt(x, z)
            if d > RD + 0.5:
                continue
            a = at(x, z)
            for y in range(18, AY + 1):
                ro = r_out(y)
                if d > ro:
                    continue
                if y <= G and ((x, y, z) in C.keep or C.get(x, y, z) == AIR or "stairs" in (C.get(x, y, z) or "")):
                    continue      # the cistern stair climbing through the plinth
                if d <= R_IN:
                    # interior: floors, air
                    if y <= G:
                        C.set(x, y, z, SB if y > 20 else rock(x, y, z))
                    elif y in (38, 50, 62, 74, 86, 98):
                        C.set(x, y, z, PARQ if y != 98 else BTILE)
                    elif y in (37, 49, 61, 73, 85, 97):
                        C.set(x, y, z, SPR if (x - TX) % 3 else "stripped_spruce_log[axis=x]")
                    elif y >= AY - 1:
                        C.set(x, y, z, IRON if y == AY - 1 else deck_spec(x, z, d, a))
                    else:
                        C.air(x, y, z)
                else:
                    if y >= AY - 1:
                        C.set(x, y, z, IRON if y == AY - 1 else deck_spec(x, z, d, a))
                    else:
                        C.set(x, y, z, body_spec(x, y, z, d, a))
    # brass string courses projecting one block at the storeys (the outline at 5-10 m detail)
    for F in FLOORS[1:] + (LF,):
        y = F - 1
        ro = r_out(y)
        for (x, z) in disk_pts(TX, TZ, ro + 1.0):
            d = dt(x, z)
            if ro < d <= ro + 1.0 and C.free(x, y, z):
                C.set(x, y, z, BRASS_SLAB + "[type=top,waterlogged=false]")
    # corbel ribs under the gallery: every 15 degrees an inverted iron stair per course
    for k in range(24):
        a = 15 * k + 7.5
        for y in range(96, 108):
            ro = r_out(y)
            x, z = polar(ro + 0.6, a)
            x, z = round(x), round(z)
            if C.free(x, y, z) and dt(x, z) > ro:
                C.set(x, y, z, stair(IRON_ST, out_facing(TX - x, TZ - z), "top"))


def deck_spec(x, z, d, a):
    """The arena / gallery floor: rings of brass tile and tread plate, a compass rose of gilded trim."""
    if d <= 1.5:
        return GILD
    if d > GL1:
        return TREAD
    if abs(d - 8.0) < 0.6 or abs(d - 14.0) < 0.6:
        return BTILE
    if d < 8 and (adelta(a, 0) < 4 or adelta(a, 90) < 4 or adelta(a, 180) < 4 or adelta(a, 270) < 4):
        return GILD
    return IRON if (int(d) + int(a / 30)) % 2 else "polished_deepslate"


def windows(C):
    """Windows through the body: slits on the stair side, tall windows on the free side of each storey."""
    for k, F in enumerate(FLOORS):
        a0 = STAIR_A[k]
        free = (a0 + 230) % 360.0
        for j in range(6):
            a = (free + 60 * j) % 360.0
            tall = j == 0
            y0 = F + 3 if not tall else F + 2
            y1 = F + 6 if not tall else F + 7
            for rr10 in range(int(R_IN * 10), int(r_out(F + 4) * 10) + 1):
                x, z = polar(rr10 / 10.0, a)
                x, z = round(x), round(z)
                if dt(x, z) <= R_IN:
                    continue
                for y in range(y0, y1 + 1):
                    outer = dt(x, z) > r_out(y) - 1.0
                    if outer:
                        C.set(x, y, z, PANE if y < y1 else "iron_bars")
                    else:
                        C.set(x, y, z, GLASS)
    # the lens room: four tall windows
    for a in (20, 110, 200, 290):
        for rr10 in range(int(R_IN * 10), 130):
            x, z = polar(rr10 / 10.0, a)
            x, z = round(x), round(z)
            if dt(x, z) <= R_IN:
                continue
            for y in range(LF + 1, LF + 6):
                outer = dt(x, z) > r_out(y) - 1.0
                C.set(x, y, z, BLUE_GL if outer else AIR) if outer or C.solid(x, y, z) else None


def wall_stairs(C):
    """The stair round each storey's wall, then railings round the stairwell it opens in the floor above."""
    stairs = []
    for k, F in enumerate(FLOORS):
        a = STAIR_A[k]
        Ftop = FLOORS[k + 1] if k + 1 < len(FLOORS) else LF
        segs = [(a - 20, a, F, F), (a, a + 190, F, Ftop), (a + 190, a + 210, Ftop, Ftop)]
        cells = spiral(C, segs, 8.0, 3.0, PAND, PAND_SL, PAND, support=SB, rmax=11, rail_rmin=0.0)
        stairs.append((F, Ftop, cells))
    for (F, Ftop, cells) in stairs:
        hole = {(x, z) for (x, z), s in cells.items() if C.free(x, Ftop - 1, z)}
        rails_round(C, hole, Ftop - 1)
    return stairs


def portals(C):
    """The north door (double, onto the plateau), the keeper's passage (west), the pool lobby and its iron door
    (south: opens from inside only), the watch room's balcony door and balcony."""
    F = FLOORS[0]
    # north portal through the plinth (x -1..0), a stone porch
    for x in (-1, 0, 1):
        for z in range(TZ - 19, TZ - 9):
            C.set(x, F - 1, z, PAND)
            for y in range(F, F + 4):
                if x != 1 or y < F + 4:
                    C.clear(x, y, z)
    for z in range(TZ - 19, TZ - 9):
        for y in range(F, F + 5):
            for x in (-2, 2):
                if dt(x, z) <= r_out(y) + 0.5 and not C.free(x, y, z):
                    pass
    wood_door(C, -1, F, TZ - 13, "north", "dark_oak", "left")
    wood_door(C, 0, F, TZ - 13, "north", "dark_oak", "right")
    wood_door(C, 1, F, TZ - 13, "north", "dark_oak", "right") if False else C.set(1, F, TZ - 13, DSB) or \
        C.set(1, F + 1, TZ - 13, DSB)
    for y in range(F, F + 6):
        for x in (-3, 2):
            C.set(x, y, TZ - 19, DSB if y < F + 5 else DSB_SL + "[type=bottom,waterlogged=false]")
    for x in range(-3, 3):
        C.set(x, F + 5, TZ - 19, DSB_ST + "[facing=north,half=top,shape=straight,waterlogged=false]" if x in (-3, 2)
              else DSB)
    C.set(-2, F + 3, TZ - 20, LANT)
    C.set(1, F + 3, TZ - 20, LANT)
    # the keeper's passage west (z 5..7) through the plinth to the house
    for x in range(HOUSE[2], TX - 9):
        for z in (TZ - 1, TZ, TZ + 1):
            C.set(x, F - 1, z, PARQ)
            for y in range(F, F + 4):
                C.clear(x, y, z)
        for z in (TZ - 2, TZ + 2):
            for y in range(F, F + 4):
                if not C.solid(x, y, z):
                    C.set(x, y, z, "white_terracotta")
        C.set(x, F + 4, TZ - 1, SB)
        C.set(x, F + 4, TZ, SB)
        C.set(x, F + 4, TZ + 1, SB)
    for x in range(HOUSE[2] + 1, TX - 17):
        for z in range(TZ - 2, TZ + 3):
            C.set(x, F + 5, z, SLATE_SL + "[type=bottom,waterlogged=false]")
    hang(C, -15, F + 3, TZ, LANT_H, reach=3)
    # the pool lobby (the drop well's foot) and its iron door to the south terrace
    wx, wz = WELL
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 3):
            C.set(x, F - 1, z, PAND)
            for y in range(F, F + 3):
                C.clear(x, y, z)
    for y in range(F - 3, F):
        C.water(wx, y, wz)
    C.set(wx, F - 4, wz, "clay")
    for z in range(wz + 3, wz + 8):
        C.set(wx, F - 1, z, PAND)
        for y in range(F, F + 3):
            C.clear(wx, y, z)
    iron_door(C, wx, F, TZ + 18, "south")
    lever(C, wx + 1, F + 1, TZ + 17, "west") if False else lever(C, wx, F + 2, TZ + 17, "north", face="ceiling") \
        if False else None
    C.set(wx + 1, F, TZ + 17, SB)
    lever(C, wx - 1, F + 1, wz + 1, "east") if False else None
    # lever on the lobby's wall beside the door (inside)
    C.set(wx + 1, F + 1, TZ + 17, SB)
    lever(C, wx, F + 1, TZ + 16, "north") if False else None
    C.set(wx - 1, F + 1, TZ + 16, SB)
    lever(C, wx, F + 1, TZ + 15, "south") if False else None
    for (dx, dz) in ((1, 0),):
        pass
    C.set(wx, F + 2, TZ + 17, EDISON)
    C.set(wx + 1, F, wz + 2, "oak_sign[rotation=8,waterlogged=false]") if False else None
    # the shaft: open from the lobby up to the hoard's floor
    for y in range(F + 3, VAULT_F):
        C.clear(wx, y, wz)
    C.set(wx + 1, F + 2, wz, EDISON)
    # outside the iron door: a landing on the south terrace
    for x in range(wx - 2, wx + 3):
        for z in range(TZ + 19, TZ + 22):
            C.set(x, G, z, PAND)
            for y in range(F, F + 3):
                if C.free(x, y, z) or C.get(x, y, z) is None:
                    C.clear(x, y, z)


def lobby_lever(C):
    """The pool lobby's lever: on its west wall beside the iron door, so only someone inside can open it."""
    wx, wz = WELL
    F = FLOORS[0]
    C.set(wx - 1, F + 1, TZ + 17, SB)
    lever(C, wx, F + 1, TZ + 17, "east") if False else None
    # a lever on the wall block (wx - 1, F + 1, TZ + 17) facing east, sitting in the corridor cell
    C.set(wx, F + 1, TZ + 16, AIR)
    lever(C, wx, F + 1, TZ + 16, "east") if False else None


def watch_balcony(C):
    F = FLOORS[5]
    a = 170.0
    ro = r_out(F)
    # door through the wall
    for rr10 in range(int(R_IN * 10) - 5, int(ro * 10) + 6):
        for off in (-1, 0, 1):
            x, z = polar(rr10 / 10.0, a)
            px, pz = -math.sin(math.radians(a)), math.cos(math.radians(a))
            X, Z = round(x + px * off * 0.8), round(z + pz * off * 0.8)
            if dt(X, Z) <= R_IN:
                continue
            C.set(X, F - 1, Z, TREAD)
            for y in range(F, F + 3):
                C.clear(X, y, Z)
    # the balcony: a corbelled half-ring outside
    for x in range(TX - 18, TX + 19):
        for z in range(TZ - 18, TZ + 19):
            d = dt(x, z)
            if ro < d <= ro + 3.2 and adelta(at(x, z), a) <= 22:
                C.set(x, F - 1, z, TREAD)
                C.set(x, F - 2, z, stair(IRON_ST, out_facing(TX - x, TZ - z), "top"))
                for y in range(F, F + 3):
                    C.clear(x, y, z)
                if d > ro + 2.2 or adelta(at(x, z), a) > 19:
                    C.set(x, F, z, f"{RAIL}[facing={out_facing(x - TX, z - TZ)}]")
                    C.keep.discard((x, F, z))


# ------------------------------------------------------------------ the storeys' rooms
def room_cells(F, rmax=R_IN):
    return [(x, z) for (x, z) in disk_pts(TX, TZ, rmax) if floor_ok_cell(x, z)]


def floor_ok_cell(x, z):
    return dt(x, z) <= R_IN


def base_hall(C):
    """Base hall: the oil store and vestibule. A copper oil tank piped up into the ceiling, racks of casks, the
    lamp-trimming bench, a notice board, the cellar stairwell in the middle."""
    F = FLOORS[0]
    # floor: flagstones with a brass compass at the stairwell's head
    for (x, z) in disk_pts(TX, TZ, R_IN):
        if C.solid(x, F - 1, z) and "stairs" not in (C.get(x, F - 1, z) or "") and (x, F - 1, z) not in C.keep:
            C.set(x, F - 1, z, PAND if (x + z) % 2 else SB)
    rails_round(C, {(x, z) for x in (-1, 0, 1) for z in range(TZ, TZ + 6)}, F - 1, skip={(x, TZ - 1) for x in
                                                                                       (-1, 0, 1)})
    # the oil tank (west of centre)
    tx, tz = TX - 5, TZ - 1
    for (x, z) in disk_pts(tx, tz, 1.6):
        for y in range(F, F + 5):
            C.set(x, y, z, CU_WE if y % 2 else COPPER)
        C.set(x, F + 5, z, COPPER_SL + "[type=bottom,waterlogged=false]")
    for y in range(F + 6, F + 10):
        C.set(tx, y, tz, PIPES)
    C.set(tx + 2, F + 1, tz, VALVE + "[facing=east]")
    C.set(tx + 2, F + 2, tz, GAUGE)
    # cask racks on the free side (west/south-west band)
    for a in range(140, 255, 9):
        x, z = polar(8.6, a)
        x, z = round(x), round(z)
        if adelta(a, 180) < 14:
            continue
        for k in range(2):
            if floor_ok(C, x, F + k, z) or (k == 1 and C.free(x, F + 1, z) and "barrel" in (C.get(x, F, z) or "")):
                barrel(C, x, F + k, z, "east" if k == 0 else "up")
    # the lamp-trimming bench and shelves
    for (x, z) in ((TX + 3, TZ - 4), (TX + 4, TZ - 4)):
        fput(C, x, F, z, TABLE)
    fput(C, TX + 3, F + 1, TZ - 4, "candle[candles=3,lit=true,waterlogged=false]") if False else None
    C.put(TX + 4, F + 1, TZ - 4, LANT) if C.free(TX + 4, F + 1, TZ - 4) else None
    fput(C, TX + 3, F, TZ - 3, CHAIR + "[facing=north]")
    chest(C, TX - 3, F, TZ + 3, "east", "lvl_tower_low")
    # lamps: a chandelier over the stairwell, lanterns hung round
    hang(C, TX, F + 6, TZ - 2, CHANDELIER, reach=6)
    for a in (200, 120, 330, 30):
        x, z = polar(5.5, a)
        hang(C, round(x), F + 5, round(z), LANT_H, reach=6)
    spawner(C, TX + 4, F, TZ + 3, MOB_KNIGHT)


def chart_room(C):
    """Chart room: the great chart table, a globe, the telescope at the east window, signal flag lockers, the
    telegraph desk."""
    F = FLOORS[1]
    for (x, z) in disk_pts(TX, TZ, R_IN):
        if C.get(x, F - 1, z) == "brasshaven:mahogany_parquet" and (x + z) % 7 == 0:
            C.set(x, F - 1, z, "brasshaven:mahogany_parquet")
    # the chart table (3 x 5) with charts (cartography tables) and brass weights
    for x in range(TX - 2, TX + 1):
        for z in range(TZ - 2, TZ + 3):
            fput(C, x, F, z, "cartography_table" if (x + z) % 2 else TABLE)
    for (x, z) in ((TX - 3, TZ), (TX + 1, TZ), (TX - 1, TZ - 3), (TX - 1, TZ + 3)):
        fput(C, x, F, z, CHAIR + f"[facing={out_facing(TX - 1 - x, TZ - z)}]")
    C.put(TX - 1, F + 1, TZ, "candle[candles=4,lit=true,waterlogged=false]")
    # globe on a stand
    gx, gz = TX + 4, TZ + 2
    if floor_ok(C, gx, F, gz):
        C.set(gx, F, gz, "spruce_fence")
        C.set(gx, F + 1, gz, "light_blue_wool")
        C.set(gx, F + 2, gz, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    # telescope at the free window (east)
    a = (STAIR_A[1] + 230) % 360
    x, z = polar(7.6, a)
    x, z = round(x), round(z)
    fput(C, x, F, z, "spruce_fence")
    if C.free(x, F + 1, z):
        C.set(x, F + 1, z, f"lightning_rod[facing={out_facing(x - TX, z - TZ)},powered=false,waterlogged=false]")
    # flag lockers (barrels with coloured wool on top) and the telegraph desk
    for (x, z, col) in ((TX + 3, TZ - 4, "red"), (TX + 2, TZ - 5, "yellow"), (TX - 4, TZ - 4, "blue")):
        if fput(C, x, F, z, "barrel[facing=up,open=false]"):
            C.set(x, F + 1, z, f"{col}_carpet")
    if fput(C, TX - 4, F, TZ + 3, TABLE):
        C.set(TX - 4, F + 1, TZ + 3, W + "redstone_timer" if False else "daylight_detector[inverted=false,power=0]")
    chest(C, TX - 5, F, TZ + 2, "east", "lvl_tower_low")
    hang(C, TX - 1, F + 6, TZ, CHANDELIER, reach=6)
    for a in (60, 160, 260):
        x, z = polar(5.5, a)
        hang(C, round(x), F + 5, round(z), LANT_H, reach=6)


def log_room(C):
    """Log room: the keepers' library: a book column in the middle, reading desks, armchairs on a rug, the stove."""
    F = FLOORS[2]
    # the book column
    for (x, z) in ((TX, TZ), (TX - 1, TZ), (TX, TZ - 1), (TX - 1, TZ - 1)):
        for y in range(F, F + 10):
            C.set(x, y, z, "bookshelf" if y < F + 9 else MAHOG)
    for (x, z) in ((TX + 1, TZ), (TX - 2, TZ - 1), (TX, TZ - 2), (TX - 1, TZ + 1)):
        C.put(x, F + 4, z, "wall_torch" if False else None) if False else None
    # rug round it
    for (x, z) in disk_pts(TX - 0.5, TZ - 0.5, 4.2):
        if floor_ok(C, x, F, z):
            C.set(x, F, z, "red_carpet" if dt(x, z) > 3.5 else "brown_carpet")
    # armchairs and side tables
    for (x, z, f) in ((TX + 3, TZ + 2, "west"), (TX - 4, TZ - 3, "east"), (TX + 2, TZ - 4, "south")):
        C.put(x, F, z, CHAIR + f"[facing={f}]")
    for (x, z) in ((TX + 3, TZ + 3), (TX - 4, TZ - 4)):
        C.put(x, F, z, TABLE)
        C.put(x, F + 1, z, "candle[candles=2,lit=true,waterlogged=false]")
    # the writing desk with the lectern (the keeper's log) on the free side
    a = (STAIR_A[2] + 230) % 360
    x, z = polar(7.3, a)
    x, z = round(x), round(z)
    if floor_ok(C, x, F, z):
        C.set(x, F, z, "lectern[facing=" + out_facing(TX - x, TZ - z) + ",has_book=false,powered=false]")
    x2, z2 = polar(6.0, a + 20)
    fput(C, round(x2), F, round(z2), TABLE)
    chest(C, TX - 5, F, TZ + 3, "north", "lvl_library")
    # ship model on a stand
    if floor_ok(C, TX + 4, F, TZ - 1):
        C.set(TX + 4, F, TZ - 1, "spruce_fence")
        C.set(TX + 4, F + 1, TZ - 1, SPR_SL + "[type=bottom,waterlogged=false]")
        C.set(TX + 4, F + 2, TZ - 1, "white_banner[rotation=4]" if False else "white_carpet")
    # lamps
    for a in (30, 150, 270):
        x, z = polar(4.5, a)
        hang(C, round(x), F + 6, round(z), CHANDELIER if a == 30 else LANT_H, reach=6)
    for (x, z) in ((TX + 1, TZ - 1), (TX - 2, TZ)):
        C.set(x, F + 3, z, EDISON) if False else None


def engine_room(C):
    """Fog-horn engine room: a horizontal boiler with its firebox, gauges and valves, and two great brass horns
    through the south wall."""
    F = FLOORS[3]
    # boiler drum along x (y F+1..F+3), firebox under its west end
    for x in range(TX - 4, TX + 3):
        for dy in range(0, 4):
            for dz in (-1, 0, 1):
                if dy in (0, 3) and dz != 0:
                    continue
                C.set(x, F + dy, TZ - 2 + dz, COPPER if (x % 2) else CU_EX)
        C.set(x, F + 4, TZ - 2, BRASS_SLAB + "[type=bottom,waterlogged=false]" if x % 3 else GAUGE)
    C.set(TX - 5, F, TZ - 2, "blast_furnace[facing=west,lit=true]")
    C.set(TX - 5, F + 1, TZ - 2, IRON)
    for y in range(F + 2, F + 10):
        C.set(TX - 5, y, TZ - 2, SMOKE if y < F + 9 else SOOT)
    C.set(TX + 3, F + 1, TZ - 2, VALVE + "[facing=east]")
    C.set(TX + 3, F + 2, TZ - 2, GAUGE)
    # coal bunker
    for (x, z) in ((TX - 4, TZ + 1), (TX - 3, TZ + 1)):
        C.put(x, F, z, "coal_block")
    C.put(TX - 4, F + 1, TZ + 1, "coal_block" if False else "black_carpet")
    # the steam main to the horns (south)
    a = (STAIR_A[3] + 230) % 360          # ~90: south
    for k, off in enumerate((-12, 12)):
        ah = a + off
        hx, hz = polar(5.0, ah)
        hx, hz = round(hx), round(hz)
        for y in range(F, F + 4):
            C.put(hx, y, hz, PIPES)
        # the horn: a widening brass cone through the wall and out
        for rr10 in range(55, int(r_out(F + 4) * 10) + 30, 5):
            r = rr10 / 10.0
            cx, cz = polar(r, ah)
            w = 0 if r < R_IN + 0.5 else (1 if r < r_out(F + 4) + 1.0 else 2)
            for dy in range(-w, w + 1):
                for o in range(-w, w + 1):
                    px, pz = -math.sin(math.radians(ah)), math.cos(math.radians(ah))
                    X, Z = round(cx + px * o), round(cz + pz * o)
                    Y = F + 4 + dy
                    edge = abs(dy) == w or abs(o) == w
                    if r > r_out(Y) + 2.4 and not edge:
                        C.set(X, Y, Z, AIR)
                    elif w == 0 or edge:
                        C.set(X, Y, Z, BRASS if w < 2 else GILD)
    # workbench, tool rack
    fput(C, TX + 4, F, TZ + 2, TABLE)
    fput(C, TX + 4, F, TZ + 3, "anvil[facing=north]")
    chest(C, TX + 3, F, TZ + 4, "north", "lvl_engine")
    for a in (0, 120, 240):
        x, z = polar(5.2, a + 30)
        hang(C, round(x), F + 6, round(z), HANG_LAMP, reach=6)
    spawner(C, TX + 1, F, TZ + 2, MOB_DRONE)


def gear_disc(C, cx, cy, cz, r, plane, spec=GEAR, hub=BRASS):
    """A gear wheel standing in a vertical plane ('x' = in the x-y plane, 'z' = in the z-y plane): rim teeth, spokes,
    a brass hub."""
    R = int(r) + 1
    for u in range(-R, R + 1):
        for v in range(-R, R + 1):
            d = math.hypot(u, v)
            x, y, z = (cx + u, cy + v, cz) if plane == "x" else (cx, cy + v, cz + u)
            if d <= 0.9:
                C.set(x, y, z, hub)
            elif r - 0.9 < d <= r + 0.2:
                C.set(x, y, z, spec)
            elif r + 0.2 < d <= r + 1.0 and (int(math.degrees(math.atan2(v, u)) + 360) // 30) % 2 == 0:
                C.set(x, y, z, IRON)
            elif d < r - 0.9 and (abs(u) < 0.5 or abs(v) < 0.5):
                C.set(x, y, z, IRON)


def clockwork_room(C):
    """Clockwork room: the lens drive. A great vertical wheel, a smaller pinion, the escapement, a flyball governor,
    the weight drums with their chains running down through the floor, a bench of spare cogs."""
    F = FLOORS[4]
    gear_disc(C, TX - 1, F + 4, TZ, 3.6, "x")
    gear_disc(C, TX + 3, F + 6, TZ + 1, 1.6, "x", spec=BTILE)
    for y in range(F, F + 9):
        if y != F + 4:
            C.put(TX - 1, y, TZ - 1, IRON_WALL if y < F + 4 else IRON_WALL)
    # the governor (two gold balls on chains round a brass spindle)
    gx, gz = TX + 3, TZ - 3
    for y in range(F, F + 6):
        C.put(gx, y, gz, BRASS if y in (F, F + 5) else "iron_bars")
    for (dx, dz) in ((1, 0), (-1, 0)):
        C.put(gx + dx, F + 4, gz + dz, CHAIN)
        C.put(gx + dx, F + 3, gz + dz, GOLD)
    # weight drums (logs) and chains through the floor
    for (x, z) in ((TX - 4, TZ + 3), (TX - 2, TZ + 4)):
        C.put(x, F + 7, z, "stripped_dark_oak_log[axis=x]")
        for y in range(F, F + 7):
            C.put(x, y, z, CHAIN)
    # the escapement: an anchor of iron stairs over a brass wheel
    C.put(TX + 1, F + 8, TZ, stair(IRON_ST, "west", "top"))
    C.put(TX + 2, F + 8, TZ, stair(IRON_ST, "east", "top"))
    # bench of spare cogs
    a = (STAIR_A[4] + 230) % 360
    x, z = polar(6.8, a)
    x, z = round(x), round(z)
    for o in (0, 1):
        fput(C, x + o, F, z, TABLE)
    C.put(x, F + 1, z, COG + "[facing=north]" if False else "candle[candles=3,lit=true,waterlogged=false]")
    chest(C, TX - 5, F, TZ - 3, "east", "lvl_clockwork")
    for a in (90, 210, 330):
        x, z = polar(5.6, a)
        hang(C, round(x), F + 7, round(z), HANG_LAMP, reach=4)
    C.set(TX - 1, F + 4, TZ + 1, EDISON) if C.free(TX - 1, F + 4, TZ + 1) else None
    spawner(C, TX + 4, F, TZ + 3, MOB_SPIDER)


def watch_room(C):
    """Watch room: the keeper's watch desk under the barometers, a stove, a cot, a sea chest, the balcony door."""
    F = FLOORS[5]
    # the watch desk facing the balcony
    for (x, z) in ((TX - 3, TZ + 1), (TX - 3, TZ + 2)):
        fput(C, x, F, z, TABLE)
    fput(C, TX - 2, F, TZ + 1, CHAIR + "[facing=west]")
    C.put(TX - 3, F + 1, TZ + 1, "candle[candles=3,lit=true,waterlogged=false]")
    C.put(TX - 3, F + 1, TZ + 2, LANT)
    # stove with its pipe
    sx, sz = TX + 3, TZ - 3
    if floor_ok(C, sx, F, sz):
        C.set(sx, F, sz, "smoker[facing=south,lit=true]")
        for y in range(F + 1, F + 10):
            C.set(sx, y, sz, PIPES if y < F + 9 else IRON)
    # cot and sea chest
    C.bp.bed(TX + 2, F, TZ + 3, "east", "blue") if floor_ok(C, TX + 2, F, TZ + 3) and floor_ok(C, TX + 3, F, TZ + 3) \
        else None
    chest(C, TX + 1, F, TZ + 4, "north", "lvl_watch")
    # barometers and gauges on a brass panel in the middle
    for y in range(F, F + 3):
        C.put(TX, y, TZ - 1, BRASS if y == F else GAUGE)
    C.put(TX, F + 3, TZ - 1, EDISON)
    for a in (60, 300):
        x, z = polar(5.0, a)
        hang(C, round(x), F + 6, round(z), CHANDELIER if a == 60 else LANT_H, reach=6)
    spawner(C, TX - 4, F, TZ - 3, MOB_MARINE)


def lens(C):
    """The lens room: the giant Fresnel lens on its clockwork turntable at the centre, twisted bull's-eye panels that
    read as turning, the lamp inside, beams of end rods; the waystone (site of grace); the stair to the corbel."""
    F = LF
    # turntable: a brass disc with a gear rim, rollers under it
    for (x, z) in disk_pts(TX, TZ, 5.4):
        d = dt(x, z)
        if d <= 4.6:
            C.set(x, F - 1, z, BTILE if d > 1.5 else GILD)
        elif d <= 5.4:
            C.set(x, F - 1, z, GEAR)
            if (int(at(x, z)) // 20) % 2 == 0:
                C.set(x, F, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    # the lens barrel: rings of glass between brass hoops, twisted panel ribs
    for (x, z) in disk_pts(TX, TZ, 4.4):
        d = dt(x, z)
        a = at(x, z)
        for y in range(F + 1, F + 11):
            if d > 3.5:
                tw = (a + (y - F) * 7.0) % 45.0
                if (y - F) % 3 == 0:
                    spec = BRASS if (y - F) % 6 == 0 else BTILE
                elif tw < 6.0:
                    spec = GILD
                elif abs(tw - 22.5) < 6.0 and (y - F) % 3 == 2:
                    spec = "yellow_stained_glass"
                else:
                    spec = BLUE_GL if (y + int(a / 45)) % 2 else GLASS
                C.set(x, y, z, spec)
            elif d <= 1.5 and F + 4 <= y <= F + 6:
                C.set(x, y, z, "sea_lantern" if d < 0.6 else "ochre_froglight")
            elif d <= 3.5:
                C.set(x, y, z, AIR)
        C.set(x, F + 11, z, BRASS if d > 2.5 else GILD)
        if d <= 2.5:
            C.set(x, F + 12, z, BTILE_SL + "[type=bottom,waterlogged=false]")
    # the lamp's pedestal inside
    C.set(TX, F, TZ, GEAR)
    C.set(TX, F + 1, TZ, BRASS)
    C.set(TX, F + 2, TZ, IRON_WALL)
    C.set(TX, F + 3, TZ, BRASS)
    # beams: end rods out of the bull's-eyes at eight bearings
    for k in range(8):
        a = 45 * k + 22.5
        x, z = polar(5.0, a)
        x, z = round(x), round(z)
        f = out_facing(x - TX, z - TZ)
        if C.free(x, F + 5, z):
            C.set(x, F + 5, z, f"end_rod[facing={f}]")
    # the drive: a vertical gear meshing with the rim, chains from the ceiling (the weight cable)
    gear_disc(C, TX - 6, F + 2, TZ - 3, 1.6, "z", spec=BTILE)
    for y in range(F + 4, F + 13):
        C.put(TX + 6, y, TZ - 3, CHAIN)
    C.put(TX + 6, F + 3, TZ - 3, "stripped_dark_oak_log[axis=y]")
    # the grace: the waystone on the west side, a bench, the polishing lathe, spare prisms
    waystone(C, TX - 7, F, TZ + 2)
    C.set(TX - 7, F - 1, TZ + 2, GILD)
    fput(C, TX - 7, F, TZ + 4, stair(SPR_ST, "east"))
    fput(C, TX - 7, F, TZ + 5, stair(SPR_ST, "east"))
    for (x, z) in ((TX - 5, TZ - 6), (TX - 4, TZ - 6)):
        fput(C, x, F, z, TABLE)
    C.put(TX - 5, F + 1, TZ - 6, "amethyst_cluster[facing=up,waterlogged=false]")
    chest(C, TX - 6, F, TZ - 5, "east", "lvl_lens")
    # wall lamps
    for a in (160, 250, 340, 70):
        for rr10 in range(97, 112):
            x, z = polar(rr10 / 10.0, a)
            x, z = round(x), round(z)
            if C.solid(x, F + 6, z) and (x, F + 6, z) not in C.keep and dt(x, z) > R_IN:
                C.set(x, F + 6, z, EDISON)
                break
    for a in (200, 20):
        x, z = polar(7.0, a)
        hang(C, round(x), F + 8, round(z), HANG_LAMP, reach=6)
    # the inner stair along the east wall up to the corbel landing (feet 104) and the passage north into the corbel
    stair_run(C, [(TX + 5, TZ + 2), (TX + 6, TZ + 2), (TX + 7, TZ + 2)], "north", 5, F - 1, spec=PAND_ST,
              support=SB)
    for x in range(TX + 5, TX + 9):
        for z in range(TZ - 7, TZ - 2):
            if dt(x, z) <= R_IN + 2.6 or (x, z) in ((TX + 5, TZ - 3), (TX + 6, TZ - 3)):
                C.set(x, VAULT_F - 1, z, PAND)
                fill_down(C, x, VAULT_F - 2, z, SB, LF - 1)
                for y in range(VAULT_F, VAULT_F + 4):
                    C.clear(x, y, z)
    rails_round(C, {(x, z) for x in range(TX + 5, TX + 9) for z in range(TZ - 7, TZ - 2) if dt(x, z) <= R_IN + 2.6},
                VAULT_F - 1, skip={(x, TZ - 2) for x in range(TX + 5, TX + 8)} | {(x, TZ - 8) for x in range(5, 9)})


def corbel_stair(C):
    """The enclosed stair in the gallery's corbel (compression): a straight flight under the deck from the lens
    room's landing west to the hatch house on the arena floor."""
    # the corridor (z TZ - 13 .. TZ - 11), x from 9 down to -6, feet 104
    for x in range(TX - 5, TX + 10):
        for z in range(TZ - 13, TZ - 10):
            C.set(x, VAULT_F - 1, z, TREAD)
            for y in range(VAULT_F, AY - 1):
                C.clear(x, y, z)
        for z in (TZ - 14, TZ - 10):
            for y in range(VAULT_F - 1, AY - 1):
                if not C.solid(x, y, z) or dt(x, z) <= R_IN + 1.2:
                    C.set(x, y, z, DIB)
    # link from the landing (x 5..8, z TZ-7..TZ-3) to the corridor
    for x in range(TX + 6, TX + 9):
        for z in range(TZ - 10, TZ - 6):
            C.set(x, VAULT_F - 1, z, TREAD)
            for y in range(VAULT_F, VAULT_F + 4):
                C.clear(x, y, z)
    # the flight: 10 treads climbing west from x 4 to x -5 (tread i at y 104 + i), the last flush with the deck
    stair_run(C, [(TX + 4, z) for z in range(TZ - 13, TZ - 10)], "west", 10, VAULT_F - 1, spec=IRON_ST,
              support=DIB)
    for x in (TX - 6,):
        for z in range(TZ - 13, TZ - 10):
            C.set(x, AY, z, TREAD)
            C.set(x, AY - 1, z, IRON)
            for y in range(AY + 1, AY + 4):
                C.clear(x, y, z)
    # lamps in the corridor
    for x in (TX + 7, TX + 1):
        if C.solid(x, VAULT_F + 3, TZ - 14):
            C.set(x, VAULT_F + 3, TZ - 14, EDISON)
    C.set(TX - 3, AY - 2, TZ - 14, EDISON)


def hatch_house(C):
    """The hatch house on the arena's north rim round the stair's head: plated walls, a copper roof, the doorway
    south toward the lamp (the mist)."""
    x0, z0, x1, z1 = TX - 7, TZ - 14, TX + 2, TZ - 9
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(AY + 1, AY + 5):
                if edge:
                    C.set(x, y, z, IRON if (x + y) % 3 else BRASS)
                elif (x, y, z) not in C.keep:
                    C.air(x, y, z)
            C.set(x, AY + 5, z, CUT_OX if edge else CUT_OX_SL + "[type=bottom,waterlogged=false]")
    for x in (x0 + 1, x0 + 2):
        for y in range(AY + 1, AY + 4):
            C.clear(x, y, z1)
    C.set(x0 + 3, AY + 3, z1 - 1, EDISON) if C.free(x0 + 3, AY + 3, z1 - 1) else None
    hang(C, x0 + 2, AY + 3, z0 + 2, LANT_H, reach=2)
    C.bp.mist(x0 + 1, AY + 1, z1, x0 + 2, AY + 3, z1)


def hoard(C):
    """The keeper's hoard in the corbel's south side: chests, ambergris and whale ivory, the brass instruments of
    lost ships; the drop well's hatch in its floor; the ladder up to the sealed bars in the arena floor."""
    F = VAULT_F
    cells = []
    for x in range(TX - 16, TX + 17):
        for z in range(TZ, TZ + 18):
            d = dt(x, z)
            a = at(x, z)
            if R_IN + 1.0 < d <= 15.0 and in_arc(a, 40, 140):
                cells.append((x, z))
                C.set(x, F - 1, z, PARQ if (x + z) % 2 else BTILE)
                for y in range(F, AY - 1):
                    C.air(x, y, z)
    wx, wz = WELL
    C.set(wx, F - 1, wz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    lever(C, wx + 1, F, wz, "east", face="floor")
    # the ladder from the bars down (attached to the lens room's outer wall)
    lx, lz = TX + 3, TZ + 11
    for y in range(F, AY):
        C.set(lx, y, lz, LADDER.format("south"))
        if not C.solid(lx, y, lz - 1):
            C.set(lx, y, lz - 1, DIB)
    C.set(lx, AY, lz, MOD["vault_bars"])
    # treasure
    for (a, r) in ((55, 13.0), (90, 14.0), (125, 13.0)):
        x, z = polar(r, a)
        x, z = round(x), round(z)
        chest(C, x, F, z, out_facing(TX - x, TZ - z), "lvl_vault")
    rng = random.Random(961)
    for (x, z) in cells:
        if C.free(x, F, z) and (x, F, z) not in C.keep and dt(x, z) > 13.2 and rng.random() < 0.35:
            C.set(x, F, z, rng.choice((GOLD, "honeycomb_block", BONE, "raw_gold_block", GOLD)))
            if rng.random() < 0.3 and C.free(x, F + 1, z):
                C.set(x, F + 1, z, "candle[candles=3,lit=true,waterlogged=false]")
    for a in (70, 110):
        x, z = polar(12.5, a)
        hang(C, round(x), F + 4, round(z), CHANDELIER, reach=6)


def arena(C):
    """The lantern room (the arena): the glazing with diagonal brass astragals, two glazed doorways onto the lamp
    gallery, the cupola with its ribs, the ventilator ball and the vane; the great lamp hung from the apex; the seal."""
    for x in range(TX - 22, TX + 23):
        for z in range(TZ - 22, TZ + 23):
            d = dt(x, z)
            if d > RD + 0.5:
                continue
            a = at(x, z)
            if d <= GL0:
                for y in range(AY + 1, CUP):
                    if (x, y, z) not in C.keep:
                        C.air(x, y, z)
            elif d <= GL1:
                door = (adelta(a, 0) < 4.5 or adelta(a, 180) < 4.5) and y_ok(AY + 1)
                for y in range(AY + 1, CUP):
                    lat = (a * 0.36 + (y - AY)) % 6.0 < 1.0 or (a * 0.36 - (y - AY)) % 6.0 < 1.0
                    if door and y <= AY + 3 and (adelta(a, 0) < 4.5 or adelta(a, 180) < 4.5):
                        C.clear(x, y, z)
                    elif y in (AY + 1, CUP - 1) or lat:
                        C.set(x, y, z, BRASS if y in (AY + 1, CUP - 1) else GRILLE if False else BRASS)
                    else:
                        C.set(x, y, z, GLASS if (y // 4 + int(a / 20)) % 3 else BLUE_GL)
            else:
                # the lamp gallery outside the glass
                for y in range(AY + 1, AY + 4):
                    if (x, y, z) not in C.keep:
                        C.clear(x, y, z)
                if d > RD - 1.0:
                    C.set(x, AY + 1, z, f"{RAIL}[facing={out_facing(x - TX, z - TZ)}]")
                    C.keep.discard((x, AY + 1, z))
    # lamp posts on the gallery rail between the doors (the gallery is lit for the fight's run-outs)
    for k in range(12):
        x, z = polar(RD - 0.6, 30 * k + 15)
        x, z = round(x), round(z)
        C.set(x, AY + 1, z, IRON_WALL)
        C.set(x, AY + 2, z, LANT)
    # cupola: a ribbed verdigris dome, a cornice
    for x in range(TX - 20, TX + 21):
        for z in range(TZ - 20, TZ + 21):
            d = dt(x, z)
            if d > 18.6:
                continue
            a = at(x, z)
            if d > GL1 - 0.2:
                C.set(x, CUP, z, CUT_OX_SL + "[type=bottom,waterlogged=false]" if d > 18.0 else CUT_OX)
                C.set(x, CUP - 1, z, BRASS) if d <= GL1 + 0.6 else None
                continue
            yt = CUP + 13.0 * math.sqrt(max(0.0, 1.0 - (d / 17.6) ** 2))
            yb = CUP + 13.0 * math.sqrt(max(0.0, 1.0 - (min(17.6, d + 1.0) / 17.6) ** 2))
            rib = adelta(a % 30.0, 15.0) > 13.5
            for y in range(int(yb), int(yt) + 1):
                C.set(x, y, z, BRASS if rib else (CU_OX if hash3(x, y, z, 971) < 0.75 else CUT_OX))
            for y in range(AY + 1, int(yb)):
                if (x, y, z) not in C.keep and C.free(x, y, z):
                    C.air(x, y, z)
    # ventilator ball and vane
    top = CUP + 14
    for (x, z) in disk_pts(TX, TZ, 2.2):
        for y in range(top, top + 4):
            if math.hypot(x - TX, z - TZ, (y - top - 1.5) * 1.1) <= 2.2:
                C.set(x, y, z, GILD if (y - top) % 2 else BRASS)
    for y in range(top + 4, top + 9):
        C.set(TX, y, TZ, IRON_WALL if y < top + 8 else ROD_U)
    for (dx, dz, f) in ((1, 0, "east"), (2, 0, "east"), (-1, 0, "west")):
        C.set(TX + dx, top + 6, TZ + dz, f"{CHAIN_X}" if abs(dx) < 2 else f"lightning_rod[facing={f},powered=false,"
                                                                             "waterlogged=false]")
    # the great lamp: a cage of sea lanterns and froglights hung from the apex
    ly = CUP + 3
    for y in range(ly + 4, CUP + 13):
        C.set(TX, y, TZ, CHAIN)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (0, 1, 2):
                corner = abs(dx) + abs(dz) == 2
                if corner and dy == 1:
                    C.set(TX + dx, ly + dy, TZ + dz, "iron_bars")
                elif corner:
                    C.set(TX + dx, ly + dy, TZ + dz, BRASS)
                else:
                    C.set(TX + dx, ly + dy, TZ + dz, "sea_lantern" if (dx, dz) == (0, 0) or dy == 1 else
                          "ochre_froglight")
    C.set(TX, ly + 3, TZ, BRASS)
    for (dx, dz, f) in ((2, 0, "east"), (-2, 0, "west"), (0, 2, "south"), (0, -2, "north")):
        C.set(TX + dx, ly + 1, TZ + dz, f"end_rod[facing={f}]")
    # light at the floor: sea lanterns set in the deck ring under glass
    for k in range(16):
        a = 22.5 * k
        x, z = polar(11.0, a)
        x, z = round(x), round(z)
        if (x, AY, z) not in C.keep and "stairs" not in (C.get(x, AY, z) or "") and C.solid(x, AY, z):
            C.set(x, AY, z, "sea_lantern")
    C.bp.boss_seal(TX, AY, TZ, BOSS, 16)


def y_ok(y):
    return True


# ------------------------------------------------------------------ the keeper's quarters
def keepers_house(C):
    """A whitewashed two-storey cottage under a slate roof against the tower: kitchen and parlour below, bedroom and
    study above, a chimney on the north gable; front door onto the plateau yard."""
    x0, z0, x1, z1 = HOUSE
    F = G + 1
    UF = F + 6
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(G - 3, G + 1):
                if C.free(x, y, z) or y == G:
                    C.set(x, y, z, SB if (x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)) else "stone")
    def wall(x, y, z):
        corner = x in (x0, x1) and z in (z0, z1)
        if corner:
            return SB if (y % 2) else PAND
        if y == F:
            return SB
        if y == UF - 1:
            return "stripped_dark_oak_log[axis=x]" if z in (z0, z1) else "stripped_dark_oak_log[axis=z]"
        return "white_terracotta" if hash3(x, y, z, 981) < 0.85 else CALC
    box(C, x0, F, z0, x1, UF + 3, z1, wall, floor=lambda x, z: SPR if (x + z) % 4 else DOAK, ceil=None)
    # the upper floor
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            C.set(x, UF - 1, z, DOAK if (x % 3) else "stripped_dark_oak_log[axis=z]")
            C.set(x, UF - 2, z, "stripped_dark_oak_log[axis=x]" if (z - z0) % 3 == 0 else AIR)
    gable(C, x0, z0, x1, z1, UF + 4, "z", SLATE_ST, SLATE, over=1,
          gable_wall=lambda x, y, z: "white_terracotta" if hash3(x, y, z, 982) < 0.9 else CALC)
    # partitions at z 4 on both floors, doors in them
    pz = 4
    for x in range(x0 + 1, x1):
        for y in range(F, UF - 2):
            C.set(x, y, pz, SPR)
        for y in range(UF, UF + 4):
            C.set(x, y, pz, SPR)
    for y in (F, F + 1):
        C.clear(x0 + 6, y, pz)
    for y in (UF, UF + 1):
        C.clear(x0 + 6, y, pz)
    # the passage door (east wall, z 5..7) and the front door (north wall)
    for z in (TZ - 1, TZ, TZ + 1):
        for y in range(F, F + 3):
            C.clear(x1, y, z)
    wood_door(C, x0 + 6, F, z0, "north", "spruce")
    C.set(x0 + 6, F - 1, z0 - 1, PAND)
    C.set(x0 + 6, F - 1, z0 - 2, PAND)
    C.set(x0 + 5, F + 2, z0 - 1, LANT)
    # windows with shutters
    for (x, z, f) in ((x0, z0 + 2, "west"), (x0, z0 + 9, "west"), (x0, z1 - 2, "west"), (x0 + 3, z1, "south"),
                      (x1 - 3, z1, "south"), (x0 + 9, z0, "north")):
        for y in (F + 2, UF + 2):
            C.set(x, y, z, PANE)
            C.set(x, y + 1, z, PANE) if y == UF + 2 else None
    # the stair (kitchen, west wall) up to the upper floor
    stair_run(C, [(x0 + 1, z1 - 1), (x0 + 2, z1 - 1), (x0 + 3, z1 - 1)], "north", 6, F - 1, spec=SPR_ST,
              support=SPR)
    hole = [(x, z) for x in range(x0 + 1, x0 + 4) for z in range(z1 - 6, z1) if C.free(x, UF - 1, z)]
    rails_round(C, set(hole), UF - 1, spec=SPR_FENCE)
    # kitchen (south ground floor): range, table, pantry, sink
    C.set(x1 - 1, F, z1 - 1, "smoker[facing=west,lit=true]")
    C.set(x1 - 1, F, z1 - 2, "furnace[facing=west,lit=true]")
    C.set(x1 - 1, F, z1 - 3, "water_cauldron[level=3]")
    for z in (z1 - 4, z1 - 5):
        C.set(x1 - 1, F, z, "barrel[facing=west,open=false]")
    for x in (x0 + 6, x0 + 7):
        for z in (pz + 4, pz + 5):
            fput(C, x, F, z, TABLE)
    for (x, z, f) in ((x0 + 5, pz + 4, "east"), (x0 + 8, pz + 5, "west")):
        fput(C, x, F, z, CHAIR + f"[facing={f}]")
    C.put(x0 + 6, F + 1, pz + 4, "candle[candles=3,lit=true,waterlogged=false]")
    chest(C, x1 - 2, F, pz + 1, "south", "lvl_keeper")
    hang(C, x0 + 7, F + 3, pz + 6, LANT_H)
    hang(C, x1 - 3, F + 3, z1 - 3, LANT_H)
    # parlour (north): a fireplace on the west wall, armchairs on a rug, a clock, a bookcase
    fx, fz = x0 + 1, (z0 + pz) // 2
    for z in range(fz - 1, fz + 2):
        for y in range(F, F + 4):
            C.set(fx, y, z, BRICK)
    C.set(fx, F, fz, "campfire[lit=true,facing=east,signal_fire=false,waterlogged=false]")
    C.set(fx, F + 1, fz, AIR)
    for y in range(F + 4, UF + 10):
        C.set(fx - 1 if False else x0, y, fz, BRICK) if y >= UF + 4 else None
    for y in range(UF + 4, UF + 11):
        C.set(x0, y, fz, BRICK)
    C.set(x0, UF + 11, fz, "campfire[lit=false,facing=north,signal_fire=false,waterlogged=false]")
    for (x, z) in disk_pts(x0 + 5, fz, 2.2):
        if floor_ok(C, x, F, z):
            C.set(x, F, z, "red_carpet")
    for (x, z, f) in ((x0 + 4, fz - 2, "south"), (x0 + 4, fz + 2, "north"), (x0 + 7, fz, "west")):
        C.put(x, F, z, CHAIR + f"[facing={f}]")
    for z in range(z0 + 1, z0 + 4):
        for y in (F, F + 1):
            C.set(x1 - 1, y, z, "bookshelf")
    C.set(x0 + 9, F, z0 + 1, DOAK)
    C.set(x0 + 9, F + 1, z0 + 1, DOAK)
    C.set(x0 + 9, F + 2, z0 + 1, "clock" if False else GAUGE)
    hang(C, x0 + 5, F + 3, fz, LANT_H)
    C.set(x1 - 1, F + 2, z0 + 1, "candle[candles=2,lit=true,waterlogged=false]")
    # bedroom (south upper floor)
    C.bp.bed(x1 - 2, UF, z1 - 2, "south", "red")
    C.set(x1 - 1, UF, z1 - 1, DOAK if False else "barrel[facing=west,open=false]")
    C.set(x1 - 3, UF, z1 - 1, TABLE)
    C.set(x1 - 3, UF + 1, z1 - 1, LANT)
    chest(C, x1 - 1, UF, pz + 2, "west", "lvl_keeper")
    for z in (pz + 2, pz + 3):
        C.set(x0 + 5, UF, z, "dark_oak_planks")
        C.set(x0 + 5, UF + 1, z, "dark_oak_planks")
    hang(C, x0 + 8, UF + 2, z1 - 3, LANT_H)
    # study (north upper floor): desk, maps, shelves, a telescope at the window
    for x in (x0 + 7, x0 + 8):
        C.set(x, UF, z0 + 2, TABLE)
    C.set(x0 + 8, UF, z0 + 3, CHAIR + "[facing=north]")
    C.set(x0 + 7, UF + 1, z0 + 2, "candle[candles=3,lit=true,waterlogged=false]")
    for z in range(z0 + 1, pz):
        C.set(x1 - 1, UF, z, "bookshelf")
        C.set(x1 - 1, UF + 1, z, "bookshelf")
    C.set(x0 + 1, UF, z0 + 2, SPR_FENCE)
    C.set(x0 + 1, UF + 1, z0 + 2, "lightning_rod[facing=west,powered=false,waterlogged=false]")
    hang(C, x0 + 4, UF + 2, z0 + 2, LANT_H)
    chest(C, x0 + 4, UF, z0 + 1, "south", "lvl_keeper")


def plateau_yard(C):
    """The plateau: a cliff-edge parapet, the signal mast with its flags, the fog bell, the oil house, the keeper's
    garden, paths of flags from the bridge to the doors."""
    # paths
    def flag(x, z):
        return PAND if hash01(x, z, 991) < 0.6 else ("cobblestone" if hash01(x, z, 992) < 0.6 else SB)
    walkway(C, [(21, G + 1, -40), (12, G + 1, -30), (2, G + 1, -22), (0, G + 1, -14)], width=3, full=flag,
            half=PAND_SL, rails=False)
    walkway(C, [(0, G + 1, -22), (-12, G + 1, -14), (-25, G + 1, -7)], width=3, full=flag, half=PAND_SL,
            rails=False)
    walkway(C, [(0, G + 1, 26), (8, G + 1, 30)], width=3, full=flag, half=PAND_SL, rails=False)
    # signal mast
    mx, mz = -14, -28
    for y in range(G + 1, G + 20):
        C.set(mx, y, mz, SPR_LOG + "[axis=y]")
    for dx in range(-4, 5):
        C.set(mx + dx, G + 16, mz, SPR_FENCE if abs(dx) < 4 else "spruce_fence")
    for (dx, col) in ((-4, "red"), (-2, "yellow"), (2, "blue"), (4, "white")):
        C.set(mx + dx, G + 15, mz, f"{col}_wool")
        C.set(mx + dx, G + 14, mz, f"{col}_wool" if col != "white" else "red_wool")
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        line3(C, (mx, G + 18, mz), (mx + dx, G + 1, mz + dz), CHAIN)
    C.set(mx, G + 20, mz, LANT)
    # fog bell in its frame
    bx, bz = 16, -26
    for y in range(G + 1, G + 6):
        C.set(bx - 1, y, bz, SPR_LOG + "[axis=y]")
        C.set(bx + 1, y, bz, SPR_LOG + "[axis=y]")
    C.set(bx - 1, G + 6, bz, SPR_SL + "[type=bottom,waterlogged=false]")
    C.set(bx, G + 6, bz, SPR_LOG + "[axis=x]")
    C.set(bx + 1, G + 6, bz, SPR_SL + "[type=bottom,waterlogged=false]")
    C.set(bx, G + 5, bz, "bell[attachment=ceiling,facing=north,powered=false]")
    C.set(bx, G + 1, bz + 1, LANT)
    # oil house
    ox0, oz0, ox1, oz1 = 4, -40, 12, -34
    box(C, ox0, G + 1, oz0, ox1, G + 4, oz1, lambda x, y, z: SB if (x in (ox0, ox1) and z in (oz0, oz1)) else
        "white_terracotta", floor=SB, ceil=None)
    gable(C, ox0, oz0, ox1, oz1, G + 5, "x", SLATE_ST, SLATE, over=1, gable_wall="white_terracotta")
    for y in (G + 1, G + 2):
        C.clear(ox0 + 4, y, oz1)
    for x in range(ox0 + 1, ox1):
        barrel(C, x, G + 1, oz0 + 1, "south")
        if x % 2:
            barrel(C, x, G + 2, oz0 + 1, "up")
    chest(C, ox1 - 1, G + 1, oz1 - 1, "west", "lvl_keeper")
    hang(C, ox0 + 4, G + 3, oz0 + 3, LANT_H, reach=3)
    # garden: furrows of potatoes and carrots round a water channel, a scarecrow
    gx0, gz0 = -26, -24
    for x in range(gx0, gx0 + 9):
        for z in range(gz0, gz0 + 7):
            if C.kind.get((x, z)) != "plat":
                continue
            if z == gz0 + 3:
                C.water(x, G, z)
                continue
            C.set(x, G, z, "farmland[moisture=7]")
            C.set(x, G + 1, z, "potatoes[age=7]" if x % 2 else "carrots[age=7]")
    for x in range(gx0 - 1, gx0 + 10):
        for z in (gz0 - 1, gz0 + 7):
            if C.free(x, G + 1, z) and (x, G + 1, z) not in C.keep:
                C.set(x, G + 1, z, SPR_FENCE)
    C.set(gx0 + 4, G + 2, gz0 + 1, "hay_block") if False else None
    # the cliff-edge parapet where the plateau drops
    for (x, z), t in C.top.items():
        if t != G or C.kind[(x, z)] != "plat":
            continue
        drop = any(C.top.get((x + dx, z + dz), -15) <= G - 4 for (dx, dz) in N4)
        if not drop or (x, G + 1, z) in C.keep or not C.free(x, G + 1, z):
            continue
        if 18 <= x <= 26 and -44 <= z <= -36:
            continue
        if dt(x, z) < RD + 1:
            continue
        C.set(x, G + 1, z, SB if hash3(x, G, z, 993) < 0.75 else MSB)
        if (x * 5 + z * 3) % 3 and C.free(x, G + 2, z):
            C.set(x, G + 2, z, SB_WALL)
        if (x * 7 + z * 13) % 29 == 0:
            C.set(x, G + 2, z, LANT)
    spawner(C, -4, G + 1, -30, MOB_WRECKER)


# ------------------------------------------------------------------ the whole site
def leviathan_lighthouse(bp):
    WALK.clear()
    C = Ctx(bp)
    heightfield(C)
    write_terrain(C)
    camp(C)
    approach(C)
    old_light(C)
    # harbour and station
    leviathan(C)
    dock(C)
    quay_stair(C)
    station_yard(C)
    mess_hall(C)
    cooperage(C)
    rendering_house(C)
    harpoon_battery(C)
    flensing_crane(C)
    boathouse(C)
    tide_stair(C)
    stair_tower(C)
    quay_edges(C)
    # under the headland
    sea_caves(C)
    # the lighthouse
    tower_shell(C)
    windows(C)
    stairs = wall_stairs(C)
    portals(C)
    watch_balcony(C)
    base_hall(C)
    chart_room(C)
    log_room(C)
    engine_room(C)
    clockwork_room(C)
    watch_room(C)
    lens(C)
    corbel_stair(C)
    hoard(C)
    arena(C)
    hatch_house(C)
    lobby_lever_final(C)
    keepers_house(C)
    plateau_yard(C)
    seal_caves(C)
    extra_lamps(C)
    light_pass(C)


def wall_lamp(C, x, y, z):
    b = C.get(x, y, z) or ""
    if C.solid(x, y, z) and (x, y, z) not in C.keep and not any(k in b for k in NO_BULB):
        C.set(x, y, z, EDISON)
        return True
    return False


def extra_lamps(C):
    """Hand-placed fixtures for the long dark runs: lanterns hung along the cave tunnels, sconces in the cistern,
    the stair tower and round each lighthouse storey, lanterns in the keeper's cottage."""
    for pts in ([(45, -12), (39, -12), (35, -12)], [(25, -17), (23, -24), (21, -30)], [(20, -10), (14, -8), (9, -7)],
                [(4, 8), (9, 12), (13, 14)]):
        for a, b in zip(pts, pts[1:]):
            n = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / 5.0))
            for i in range(n):
                t = (i + 0.5) / n
                x, z = round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t)
                if C.free(x, 4, z) and (x, 4, z) not in C.keep:
                    hang(C, x, 4, z, LANT_H, reach=4)
    # cistern: sconces down both long walls and on the end walls
    x0, z0, x1, z1 = CIST
    for z in range(z0 + 2, z1 - 1, 5):
        wall_lamp(C, x0 - 1, 18, z)
        wall_lamp(C, x1 + 1, 18, z)
    for x in (x0 + 4, x1 - 4):
        wall_lamp(C, x, 18, z0 - 1)
        wall_lamp(C, x, 18, z1 + 1)
    # stair tower: a sconce on alternating walls every four blocks of height
    sx0, sz0, sx1, sz1 = STAIRT
    cx, cz = STC
    walls = [(sx0, cz), (cx, sz0), (sx1, cz), (cx, sz1)]
    for i, y in enumerate(range(TERR + 3, G + 4, 3)):
        x, z = walls[i % 4]
        wall_lamp(C, x, y, z)
    # lighthouse storeys: sconces at two heights round the wall (in the masonry behind the spiral)
    for k, F in enumerate(FLOORS):
        for j in range(8):
            a = 45 * j + (22.5 if k % 2 else 0)
            y = F + (3 if j % 2 else 8)
            for rr10 in range(int(R_IN * 10) + 2, int(R_IN * 10) + 20):
                x, z = polar(rr10 / 10.0, a)
                x, z = round(x), round(z)
                if dt(x, z) <= R_IN:
                    continue
                if C.solid(x, y, z):
                    wall_lamp(C, x, y, z)
                    break
    # keeper's cottage: lanterns hung in each room
    hx0, hz0, hx1, hz1 = HOUSE
    for (x, y, z) in ((hx0 + 3, G + 4, hz0 + 6), (hx1 - 2, G + 4, hz0 + 2), (hx0 + 4, G + 10, hz1 - 3),
                      (hx1 - 3, G + 10, hz0 + 6), (hx0 + 2, G + 10, hz0 + 1)):
        if C.free(x, y, z):
            hang(C, x, y, z, LANT_H, reach=4)


def lobby_lever_final(C):
    """The pool lobby's iron door opens from inside only: its lever sits on the corridor wall just inside."""
    wx, wz = WELL
    F = FLOORS[0]
    C.set(wx + 1, F + 1, TZ + 17, SB)
    lever(C, wx, F + 1, TZ + 17, "west") if False else None
    # the lever is placed on the east wall of the corridor cell next to the door, facing west
    C.set(wx, F + 1, TZ + 16, AIR)
    C.set(wx + 1, F + 1, TZ + 16, SB)
    lever(C, wx, F + 1, TZ + 16, "west")


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("whaling_station", (60, 11, -40), (76, 16, -52)),
    ("rendering_house", (84, 11, -48), (80, 14, -57)),
    ("ribcage_dock", (61, 1, -2), (68, 10, 20)),
    ("flooded_hall", (6, 1, -6), (-8, 3, 0)),
    ("chart_room", (6, 39, 9), (-1, 40, 5)),
    ("engine_room", (-4, 63, 10), (2, 66, 14)),
    ("lens_room", (-6, 99, 8), (0, 104, 6)),
    ("lantern_arena", (0, 114, 18), (0, 126, 0)),
]

register(StructureDef(
    "leviathan_lighthouse", "overworld", ["stony_shore", "beach", "snowy_beach"],
    [Piece("lighthouse", leviathan_lighthouse, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_DROWNED, 6, 1, 2), (MOB_WRAITH, 3, 1, 1), (MOB_WRECKER, 3, 1, 1)],
    title_fr="Le Phare du Léviathan", title_en="The Leviathan Lighthouse"))
