"""Leviathan Dreadnought Wreck (Épave du cuirassé Léviathan): a brass-and-iron steam ironclad 188 blocks long, run
aground on an ocean reef and broken in two. Colossal tier (tools/BUILDING.md §1, §12 concept 16, §10 legacy-dungeon
template, §15), steampunk (tools/STYLE_STEAMPUNK.md: dark iron 60 %, brass and copper 25 %, glass, amber light).

Silhouette (one noun phrase, §15.1): a long dark warship broken amidships, the stern upright on the reef under a
bridge tower and its tripod mast, two oval funnels standing and the third fallen across the deck, the bow torn off,
pitched nose-down into the sea with its two turrets lifting their barrels.

Placement: fit mode ``seabed`` (wf/placement.py): blueprint y = 0 is the sea floor. The sea is 12 to ~30 deep where it
generates; the nominal sea surface is y SEA (top water block). Everything built works at any depth: the hull decks
are sealed air pockets (dry inside, a still wall of water at an opening under the surface), the bow's flooded
compartments are filled with water by the template, and no air is written outside the hull (the final pass drops
it), so nothing digs a hole in the sea.

Layout (x along the ship, stern at x = -96, the break at x = 0, bow towards +x; z across, port at -z; y up):
  * the reef: a sand floor, coral heads and rock pinnacles; a mound under the stern (keel at y KEEL) and the islet in
    the gap of the break (top y SEA), where the castaways' camp and the waystone stand;
  * the stern section (96 long, upright): hull decks hold / lower / middle / main (feet 15 / 23 / 29 / 35), the bridge
    tower and its tripod mast at the break, funnels at x -26 and -50, the stump of the second at x -38 with the
    funnel itself fallen across the starboard deck, the aft deckhouse, the superfiring X turret and the Y turret;
  * the bow section (80 long): tilted 22 degrees nose-down, rolled and swung, its broken end raised on the islet, its
    nose buried in the sand; turrets A and B (superfiring); inside, the forward mess deck, the forecastle tween deck
    and, under the water, the flooded torpedo deck;
  * the route: camp (waystone) -> the breach -> crew quarters (lower deck) -> stair -> officers' mess (middle deck)
    -> companion hood -> the main deck, aft along the port side under the funnels -> the aft deckhouse -> the
    middle-deck corridor, officers' cabins and the wardroom (site of grace, the hub) -> down into the engine room
    (two triple-expansion engines: spine catwalk, aft cross catwalk, side catwalks, side stairs) -> the hold landing
    (site of grace) -> the stokehold passage and the mist -> the boiler hall (boss arena: four giant boilers, the
    funnel uptakes open to the sky) -> the vault behind sealed bars -> the magazine -> the ammunition hoist (ladder
    shaft through every deck, iron door with its lever inside) back to the main deck at the bridge;
  * optional: the captain's cabin (stern windows, the stern walk), the steering flat under it, the turrets, the
    bridge and the spotting top of the mast (a long ladder), the bow (a plank bridge from the main deck, a debris
    stair from the islet) and its flooded torpedo deck.
Loot gradient (§15.6): camp, crew quarters, turrets, bow tier 1; mess, cabins, bridge, engine room, torpedo deck,
captain tier 2; the spotting top, the magazine and the vault tier 3.
"""
import math

from ..arch import stair
from ..blueprint import is_solid, with_props
from ..defs import Piece, StructureDef, register
from ..megakit import (AIR, BARS, BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP,
                       IRON, IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_SLAB, MAHOGANY_STAIRS, PIPES,
                       SMOKE, TABLE, TREAD, TREAD_SLAB, VERD, W, fbm, hash01, hash3)
from ..parts import LOOT, MOD

# the wreck's own boss: the Drowned Admiral holds the boiler hall (moveset in entity/boss/DrownedAdmiral.java: his
# steam lanes vent from the four boilers' fireboxes, his scuttle floods the hall knee-deep for a while)
BOSS = "brasshaven:drowned_admiral"
MOB_DROWNED = "minecraft:drowned"
MOB_KNIGHT = W + "skeleton_knight"
MOB_WRAITH = W + "tide_wraith"
MOB_CRAB = W + "barnacle_crab"
MOB_SPIDER = W + "clockwork_spider"

# ------------------------------------------------------------------ dimensions
SEA = 22                 # nominal top water block (sea 22 deep); the build works from 12 to ~32
KEEL = 12                # stern keel (bottom plate) y
XS = -96                 # stern tip: ship coordinate s = x - XS
L = 188                  # full length (stern tip to stem)
HB = 18                  # half beam
S_BOW0 = 108             # s of the bow section's broken end (s 96..108 is gone)
FC_S = 130               # forecastle break (bow)
HOLD_H, LOW_H, MID_H, MAIN_H, FC_H = 2, 10, 16, 22, 27   # top block of each deck in h = y - KEEL
WL = SEA - KEEL          # waterline (h)
BELT_TOP = 16
HF, LF, MF, DF = KEEL + 3, KEEL + 11, KEEL + 17, KEEL + 23   # feet: hold 15, lower 23, middle 29, main 35
DECK = DF - 1            # main deck top block (34)

# stern compartments (x of the transverse bulkheads)
X_FWD, X_ARF, X_ARA, X_ENF, X_ENA = -1, -16, -57, -63, -85
AC = (-36, 0)            # arena centre (boss seal)

# bridge tower: floors (feet) of its three levels and the roof
BT = (-15, -6, -3, 6)    # x0, z0, x1, z1 (outer)
B1, B2, BROOF = DF + 6, DF + 11, DF + 16      # 41, 46, 51
MAST_X, MAST_TOP, TOP_F = -9, DF + 61, DF + 46  # main leg, mast top y, spotting-top feet
FUNNELS = (-26, -50)     # standing funnels
F2 = -38                 # the fallen one's stump

# the bow: local (u along the bow from its broken end, h above its keel, v across) -> world
B_O = (14.0, KEEL - 1.0, 1.0)
PITCH, ROLL, YAW = math.radians(22), math.radians(5), math.radians(-7)
BOW_WL = SEA + 3          # the bow's flooded compartments: water up to the sill of their doors (y 25)
CP, SP = math.cos(PITCH), math.sin(PITCH)
CR, SR = math.cos(ROLL), math.sin(ROLL)
CY, SY = math.cos(YAW), math.sin(YAW)

IRON_BR = W + "dark_iron_bricks"
IRON_BR_ST, IRON_BR_SL = W + "dark_iron_brick_stairs", W + "dark_iron_brick_slab"
RUST, RUST_BR, RUST_P = W + "rust_rock", W + "rust_rock_bricks", W + "polished_rust_rock"
SOOT = W + "sooty_smokestack_bricks"
PARQUET = W + "mahogany_parquet"
GRILLE = W + "brass_grille"
RAIL = W + "brass_railing"
VALVE = W + "valve_wheel"
COG = W + "wall_cog"
SHELF = W + "wall_shelf"
CHAIR = W + "mahogany_chair"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}

# turrets: name, s of the centre, deck h under it, barbette top h, aim (+1 forward / -1 aft), elevation, barrel length,
# section
TURRETS = (
    ("Y", 10, MAIN_H, MAIN_H + 1, -1, 3, 14, "stern"),
    ("X", 24, MAIN_H, MAIN_H + 6, -1, 6, 15, "stern"),
    ("B", 150, FC_H, FC_H + 5, 1, 13, 15, "bow"),
    ("A", 167, FC_H, FC_H + 1, 1, 7, 12, "bow"),
)


# ------------------------------------------------------------------ the hull as a solid model (ship coordinates)
def plan(s):
    if s < 16:
        return 0.42 + 0.58 * math.sqrt(max(0.0, 1 - ((16 - s) / 16) ** 2))
    if s > 138:
        return max(0.0, (L - s) / (L - 138)) ** 0.75
    return 1.0


def hw(s, h):
    """Half width of the hull at s, h (the outer face of the plating)."""
    if h < 6:
        sec = HB - 6 + math.sqrt(max(0.0, 36 - (6 - h) ** 2))
    else:
        sec = HB
    if s > 140:                              # a finer, V-shaped forefoot and a flared bow
        t = min(1.0, (s - 140) / 40)
        sec *= 1 - t * 0.45 * max(0.0, 1 - h / 16)
        if h > 14:
            sec += t * (h - 14) * 0.18
    return plan(s) * sec


def kb(s):
    """Keel height: the cut-up of the cruiser stern, the rounded forefoot."""
    if s < 20:
        return (20 - s) * 0.5
    if s > 178:
        return (s - 178) * 1.2
    return 0.0


def deck_h(s):
    return FC_H if s >= FC_S else MAIN_H


def hull_plate(s, h, av):
    """Armoured hull plates with rivet lines (BUILDING §5: dark at the waterline, rust below, brass on the sheer)."""
    si, hi = int(math.floor(s + 0.5)), int(math.floor(h + 0.5))
    n = hash01(si * 7 + hi * 131, int(av * 2), 501)
    if hi < WL - 1:                          # anti-fouling: rust-red plates, barnacled
        if hi % 4 == 0 or si % 9 == 0:
            return RUST_P
        return RUST if n < 0.35 else RUST_BR
    if hi <= WL:                             # the black boot-topping
        return IRON_BR
    if hi <= BELT_TOP:                       # the armour belt: plates 10 long, riveted seams
        if hi == BELT_TOP or si % 10 == 0:
            return IRON_BR
        return RUST if n < 0.05 else IRON
    if hi >= deck_h(s):                      # the sheer strake
        return VERD if n < 0.25 else BRASS
    if hi == 19 and si % 5 == 2 and 4 < si < L - 6:
        return "glass"                       # portholes of the middle deck
    if (hi - 17) % 3 == 0 or si % 6 == 0:
        return IRON_BR
    if hi < 19 and si % 5 == 2 and n < 0.4:
        return RUST                          # rust weeping from the portholes
    return VERD if n < 0.03 else IRON


def deck_plank(s, v, w):
    si = int(math.floor(s + 0.5))
    if abs(v) > w - 2.6:
        return IRON                          # waterways
    if si % 11 == 0:
        return "dark_oak_planks"
    return "spruce_planks"


def turret_cell(s, v, h, sec):
    for (_, sc, dh, top, aim, elev, blen, tsec) in TURRETS:
        if tsec != sec:
            continue
        ds = s - sc
        if abs(ds) > 24 or abs(v) > 8.5 or h < dh + 0.5 or h > top + 11:
            continue
        lu, lh = ds * aim, h - top
        e = math.radians(elev)
        ce, se = math.cos(e), math.sin(e)
        du, dz = lu - 4.0, lh - 3.0
        t = du * ce + dz * se
        if -0.5 <= t <= blen:
            perp = -du * se + dz * ce
            for bv in (-2.5, 2.5):
                r = math.hypot(perp, v - bv)
                rad = 1.75 if t > blen - 1.0 else (1.55 if t < blen * 0.45 else 1.3)
                if r <= rad:
                    if t > blen - 1.0:
                        return "coal_block" if r < 0.6 else BRASS
                    if t < 1.0:
                        return BRASS
                    return IRON_BR if int(t) % 6 == 3 else IRON
        # rangefinder across the roof, periscope hoods
        if 6.5 <= lh < 7.5:
            if -5.5 <= lu < -3.5 and abs(v) <= 7.6:
                return "glass" if abs(v) > 7.0 else BRASS
            if 0 <= lu < 1.6 and 3.4 <= abs(v) < 4.6:
                return IRON_BR
            continue
        if 0.5 <= lh < 6.5:
            lc = min(max(lh, 0.0), 6.0)
            front = 6.0 - 0.55 * lc
            side = 6.5 - 0.35 * max(0.0, lh - 3)
            if -6.5 <= lu <= front and abs(v) <= side:
                inner = (-5.5 <= lu <= front - 1.0 and abs(v) <= side - 1.0 and lh < 5.5)
                if inner:
                    return AIR if sec == "stern" else IRON
                if lh >= 5.5:
                    return IRON_BR
                return IRON_BR if int(math.floor(lh + 0.5)) == 3 else IRON
            continue
        if -0.5 <= lh < 0.5:
            if math.hypot(ds, v) <= 6.2 or (-6.5 <= lu <= 6.0 and abs(v) <= 6.5):
                return IRON
            continue
        if lh < -0.5:
            r = math.hypot(ds, v)
            if r <= 6.2:
                if lh >= -1.5:
                    return BRASS
                return IRON_BR if r > 5.0 else IRON
    return None


def ship_cell(s, v, h, sec):
    """The block of the ship at ship coordinates (floats or integers): a block spec, AIR inside, None outside."""
    t = turret_cell(s, v, h, sec)
    if t:
        return t
    if s < 0 or s > L:
        return None
    k = kb(s)
    if h < k - 0.5:
        return None
    top = deck_h(s)
    if h >= top + 1.5:
        return None
    w = hw(s, h)
    av = abs(v)
    if av > w:
        return casemate(s, av, h, w)
    shell = av > w - 1.25 or h < k + 1.25
    if h >= top + 0.5:                       # the bulwark
        return hull_plate(s, h, av) if av > w - 1.25 else None
    if shell:
        return hull_plate(s, h, av)
    if sec == "bow" and s < S_BOW0 + 2.5:
        return None                          # the torn end: only the plating hangs there
    if h >= top - 0.5:
        return deck_plank(s, v, w)
    if h >= top - 1.5:
        return IRON
    if sec == "bow":
        b = bow_inside(s, v, h, w)
        if b is not None:
            return b
    for f in (LOW_H, MID_H) + ((MAIN_H,) if s >= FC_S else ()):
        if f - 1.5 <= h < f + 0.5:
            return TREAD if h >= f - 0.5 else IRON
    if h < HOLD_H + 0.5:
        return IRON
    return AIR


CASEMATES = (32, 44, 56, 68, 80, 92, 118, 132)


def casemate(s, av, h, w):
    """The secondary battery: armoured sponsons on both sides at the middle deck, a gun in each."""
    if not 16.5 <= h < 21.5:
        return None
    for sc in CASEMATES:
        ds = abs(s - sc)
        if ds > 2.6:
            continue
        out = av - w
        lh = h - 16.5
        if out <= 2.2 - max(0.0, ds - 1.5) and lh < 5 - max(0.0, out - 1.2) * 0.8:
            if lh >= 4:
                return IRON_BR
            return BRASS if ds > 2.0 and lh < 1 else IRON
        if ds < 0.5 and 2.5 <= lh < 3.5 and out <= 6.5:
            return BRASS if out > 5.5 else IRON_BR
    return None


def bow_inside(s, v, h, w):
    """Bulkheads, hatches and the torpedo deck of the bow section (None: the ordinary decks and air)."""
    av = abs(v)
    # hatches: middle deck to the lower deck, lower deck to the hold
    if 124 <= s < 127 and av < 1.6 and MID_H - 1.5 <= h < MID_H + 0.5:
        return AIR
    if 142 <= s < 145 and av < 1.6 and LOW_H - 1.5 <= h < LOW_H + 0.5:
        return AIR
    # the broken end's watertight bulkhead (door on the middle deck), the forecastle break (door on the main deck)
    if S_BOW0 + 2.5 <= s < S_BOW0 + 4.0:
        if av < 1.6 and MID_H + 0.5 <= h < MID_H + 3.5:
            return AIR
        return IRON_BR if int(h) % 4 == 0 else IRON
    if FC_S - 0.75 <= s < FC_S + 0.75 and MAIN_H + 0.5 <= h:
        if av < 1.6 and h < MAIN_H + 3.5:
            return AIR
        return IRON_BR if av > w - 3 else IRON
    for bs in (150, 170):
        if bs <= s < bs + 1 and h < MAIN_H - 1.5:
            if av < 1.6 and any(f + 0.5 <= h < f + 3.5 for f in (HOLD_H, LOW_H, MID_H)):
                return AIR
            if h > HOLD_H + 0.5:
                return IRON
    # the torpedo deck (lower deck, s 152..168): tubes through the sides, torpedoes on racks
    if 152 <= s < 169 and LOW_H + 0.5 <= h < MID_H - 1.5:
        row = int(math.floor(h + 0.5)) - LOW_H
        if 156 <= s < 160 and av > w - 3.3 and row == 2:
            return PIPES
        if row in (1, 3) and (3.5 <= av < 4.5 or 6.5 <= av < 7.5) and s < 167:
            return COPPER if s >= 165 else BRASS
        if row == 4 and 158 <= s < 160 and av < 2.5:
            return "sea_lantern"
    return None


# ------------------------------------------------------------------ bow transform
def bow_world(u, h, v):
    """Bow-local (u, h, v) to world (x, y, z) floats."""
    hp = h * CR - v * SR
    vp = h * SR + v * CR
    x = u * CP + hp * SP
    y = -u * SP + hp * CP
    return (B_O[0] + x * CY - vp * SY, B_O[1] + y, B_O[2] + x * SY + vp * CY)


def bow_local(x, y, z):
    dx, dy, dz = x - B_O[0], y - B_O[1], z - B_O[2]
    xx = dx * CY + dz * SY
    vp = -dx * SY + dz * CY
    u = xx * CP - dy * SP
    hp = xx * SP + dy * CP
    return u, hp * CR + vp * SR, -hp * SR + vp * CR


def ri(p):
    return tuple(int(round(c)) for c in p)


# ------------------------------------------------------------------ the site
class Wreck:
    def __init__(self, bp):
        self.bp = bp
        self.inner = set()      # air written on purpose (inside the hull and the superstructures)
        self.bow = set()        # cells of the bow section
        self.reef = {}          # (x, z) -> reef top y

    def set(self, x, y, z, spec, data=None):
        self.bp.set(x, y, z, spec, data)

    def air(self, x, y, z):
        self.bp.set(x, y, z, AIR)
        self.inner.add((x, y, z))

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def empty(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b in ("minecraft:air", "minecraft:water")


def zr(x, y):
    """Last interior z (|z| <= zr) of the stern at x, y."""
    s, h = x - XS, y - KEEL
    return int(math.floor(hw(s, h) - 1.25))


def cut_stern(h, z):
    return 96 + int(3.4 * fbm(h * 1.9, z * 1.4, 3.0, 77)) - 1


# ------------------------------------------------------------------ generic carving helpers
def box_air(S, x0, x1, y0, y1, z0, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(y0, y1 + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                S.air(x, y, z)


def box(S, x0, x1, y0, y1, z0, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(y0, y1 + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                S.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def inside_fill(S, x0, x1, y0, y1, spec):
    """Fill the hull interior (cells that are air) between x0..x1, y0..y1."""
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            r = zr(x, y)
            for z in range(-r, r + 1):
                if S.get(x, y, z) == AIR:
                    S.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def inside_air(S, x0, x1, y0, y1, zlim=None):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            r = zr(x, y) if zlim is None else min(zr(x, y), zlim)
            for z in range(-r, r + 1):
                S.air(x, y, z)


def bulkhead(S, x, y0, y1, spec=IRON):
    for y in range(y0, y1 + 1):
        r = zr(x, y)
        for z in range(-r, r + 1):
            S.set(x, y, z, IRON_BR if (y - KEEL) % 6 == 0 or abs(z) == r else spec)


def flight(S, x0, z0, z1, feet, n, dx, axis="x", spec=IRON_STAIRS, support=True, clear=4):
    """A straight stair going UP by n steps from a landing at feet `feet`: step i at (x0 + i*dx), block y feet - 1 + i,
    feet on it feet + i; headroom cleared above every tread. For axis z the steps advance along z (x0 is the z start
    and z0..z1 the x span)."""
    face = ("east" if dx > 0 else "west") if axis == "x" else ("south" if dx > 0 else "north")
    for i in range(n):
        a = x0 + i * dx
        y = feet - 1 + i
        for b in range(min(z0, z1), max(z0, z1) + 1):
            x, z = (a, b) if axis == "x" else (b, a)
            S.set(x, y, z, stair(spec, face))
            for yy in range(y + 1, y + 1 + clear):
                S.air(x, yy, z)
            if support:
                yy = y - 1
                while yy >= feet - 1 and S.empty(x, yy, z):
                    S.set(x, yy, z, IRON)
                    yy -= 1


def lamp(S, x, y, z, length=1):
    """A hanging Edison lamp under the ceiling block at y + length + 1."""
    for k in range(1, length + 1):
        S.set(x, y + k, z, CHAIN)
    S.set(x, y, z, HANG_LAMP)


def chest(S, x, y, z, facing, table):
    S.bp.chest(x, y, z, facing, loot=LOOT + table)


def wet_chest(S, x, y, z, facing, table):
    """A chest under water (a waterlogged chest)."""
    S.bp.chest(x, y, z, facing, loot=LOOT + table)
    name, props, data = S.bp.blocks[(x, y, z)]
    props = dict(props, waterlogged="true")
    S.bp.blocks[(x, y, z)] = (name, props, data)


# ------------------------------------------------------------------ the reef and the islet
ISLET = (-3, 17, -27, 16)     # x0, x1, z0, z1 of the islet in the break (top y SEA)
PINNACLES = ((-72, -32, 26, 6), (-30, 34, 29, 7), (34, -34, 20, 5), (62, 30, 24, 6), (-110, 14, 15, 5))


def reef_top(x, z):
    """Height of the reef (top block y) at a column, or None where the sea floor stays bare."""
    n = fbm(x, z, 11.0, 31) - 0.5
    m = fbm(x, z, 4.0, 32) - 0.5
    best = None
    # the mound under the stern
    if -110 <= x <= 6:
        s = x - XS
        w = hw(max(0, min(95, s)), 4) if s >= 0 else 0
        d = max(0.0, abs(z) - w) + (max(0, -s) * 1.2 if s < 0 else 0)
        top = KEEL - 1 - d * 0.5 + n * 5 + m * 2
        if s >= 0 and abs(z) < w:
            top = KEEL - 1 + (max(0.0, kb(s) - 5) if s < 20 else 0)
        best = top
    # the islet in the break
    x0, x1, z0, z1 = ISLET
    dx = max(x0 - x, 0, x - x1)
    dz = max(z0 - z, 0, z - z1)
    d = math.hypot(dx, dz) + n * 6
    if d < 14:
        top = SEA if d <= 0 else SEA - d * 0.9 + m * 2
        best = top if best is None else max(best, top)
    # the berm the bow ploughed into the sand
    u, h, v = bow_local(x, 2.0, z)
    if 20 <= u <= 84:
        w = hw(S_BOW0 + u, 4) + 3
        if abs(v) < w + 8:
            top = 3.0 - max(0.0, abs(v) - w) * 0.45 + n * 2
            best = top if best is None else max(best, top)
    # rock pinnacles
    for (px, pz, ph, pr) in PINNACLES:
        r = max(0.0, math.hypot(x - px, z - pz) + n * 3)
        if r < pr * 2.2:
            top = ph * (1 - (r / (pr * 2.2)) ** 1.6) + m * 2
            best = top if best is None else max(best, top)
    if best is None or best < 0.5:
        return None
    return int(round(best))


def reef_block(x, y, z, top, side):
    h = hash3(x, y, z, 33)
    if y == top and not side:
        if y >= SEA:
            return "gravel" if h < 0.3 else ("stone" if h < 0.6 else "andesite")
        if y <= 6:
            return "sand" if h < 0.6 else ("gravel" if h < 0.8 else "calcite")
        return "calcite" if h < 0.25 else ("tuff" if h < 0.55 else ("sand" if h < 0.8 else "andesite"))
    band = int((y + fbm(x, z, 7.0, 34) * 4) // 3) % 4
    return ("tuff", "andesite", "calcite", "stone")[band] if h > 0.12 else "dripstone_block"


def reef(S):
    bp = S.bp
    for x in range(-122, 104):
        for z in range(-66, 67):
            t = reef_top(x, z)
            if t is not None:
                S.reef[(x, z)] = t
    for (x, z), t in S.reef.items():
        lo = min(S.reef.get((x + dx, z + dz), 0) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        for y in range(max(1, lo - 1), t + 1):
            if bp.get(x, y, z) is None:
                bp.set(x, y, z, reef_block(x, y, z, t, y < t))
    # coral heads, fans and kelp: only where every sea it generates in covers them (y <= 11)
    for (x, z), t in S.reef.items():
        if t > 10 or bp.get(x, t + 1, z) is not None:
            continue
        h = hash01(x, z, 35)
        if h < 0.012 and t <= 8:
            c = ("brain", "tube", "fire", "horn", "bubble")[int(hash01(x, z, 36) * 5)]
            for dy in range(1, 3):
                bp.set(x, t + dy, z, f"{c}_coral_block")
            bp.set(x, t + 3, z, f"{c}_coral_fan[waterlogged=true]")
        elif h < 0.04 and fbm(x, z, 9.0, 39) > 0.5:
            c = ("brain", "tube", "fire", "horn", "bubble")[int(hash01(x, z, 37) * 5)]
            bp.set(x, t + 1, z, f"{c}_coral{'_fan' if h < 0.025 else ''}[waterlogged=true]")
        elif h < 0.12:
            bp.set(x, t + 1, z, "seagrass")
        elif h < 0.14 and t <= 5:
            top = min(11, t + 3 + int(hash01(x, z, 38) * 5))
            for y in range(t + 1, top + 1):
                bp.set(x, y, z, "kelp_plant" if y < top else "kelp[age=20]")


# ------------------------------------------------------------------ the stern section
def stern_hull(S):
    for x in range(XS - 10, 4):
        s = x - XS
        for y in range(KEEL - 1, KEEL + 42):
            h = y - KEEL
            for z in range(-26, 27):
                if s > cut_stern(h, z):
                    continue
                spec = ship_cell(s, z, h, "stern")
                if spec is None:
                    continue
                if spec == AIR:
                    S.air(x, y, z)
                else:
                    S.set(x, y, z, spec)
    # propellers and rudder under the counter, resting on the reef
    for zc in (-7, 7):
        for x in range(XS + 6, XS + 22):
            S.set(x, KEEL + 3, zc, IRON)            # shaft
        S.set(XS + 21, KEEL + 3, zc, BRASS)
        cx = XS + 5
        for a in range(3):
            ang = a * 2.094 + (0.4 if zc > 0 else 1.1)
            for r in range(1, 5):
                S.set(cx, KEEL + 3 + int(round(math.sin(ang) * r)), zc + int(round(math.cos(ang) * r)), BRASS)
        S.set(cx, KEEL + 3, zc, BRASS)
        S.set(cx + 1, KEEL + 3, zc, BRASS)
    for y in range(KEEL + 2, KEEL + 10):
        for x in (XS + 1, XS + 2, XS + 3):
            S.set(x, y, 0, IRON_BR if y > KEEL + 7 else IRON)


def stern_layout(S):
    """Bulkheads, the compartments that are filled (bunkers, bilges) and the open halls."""
    # watertight bulkheads
    bulkhead(S, X_FWD, HF, HF + 5)                      # forward hold (the breach)
    for x in (X_ARF, X_ARA):
        bulkhead(S, x, HF, DF - 3)
    bulkhead(S, X_ENF, HF, MF - 3)
    bulkhead(S, X_ENA, HF, DF - 3)
    bulkhead(S, -10, HF, HF + 5)                        # vault | magazine
    # the hold forward of the breach bulkhead is open to the sea: nothing kept there
    for x in range(X_FWD + 1, 4):
        for y in range(HF, HF + 6):
            for z in range(-20, 21):
                if S.get(x, y, z) == AIR:
                    S.bp.remove(x, y, z)
                    S.inner.discard((x, y, z))
    # the boiler hall: hold to the main deck, the engine room: hold and lower deck
    inside_air(S, X_ARA + 1, X_ARF - 1, HF, DECK - 2)
    inside_air(S, X_ENA + 1, X_ENF - 1, HF, MF - 3)
    # coal bunkers between the engine room and the boiler hall, the bilge under the captain's quarters
    coal = lambda x, y, z: "coal_block" if hash3(x, y, z, 51) < 0.35 else IRON
    inside_fill(S, X_ENF, X_ARA - 1, HF, DECK - 2, coal)
    inside_fill(S, XS, X_ENA - 1, KEEL, HF + 5, IRON)


# ------------------------------------------------------------------ forward compartment: crew, mess, magazine, vault
def crew_quarters(S):
    """Lower deck forward, open to the breach: bunks along the sides, mess tables, sea chests and lockers."""
    bp = S.bp
    f = LF
    for x in range(X_ARF + 1, 3):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f - 1, z) is not None and S.get(x, f, z) == AIR:
                S.set(x, f - 1, z, "spruce_planks" if (z + 40) % 4 else "dark_oak_planks")
    # bunks against both sides, two tiers, lockers between
    for side in (-1, 1):
        face = "north" if side > 0 else "south"
        for x0 in (-14, -10, -6):
            r = zr(x0, f) - 0
            zb = side * (r - 1)
            bp.bed(x0, f, zb, "east", "white")
            for x in (x0, x0 + 1):
                S.set(x, f + 2, zb, MAHOGANY_SLAB + "[type=top,waterlogged=false]")
            bp.bed(x0, f + 3, zb, "east", "light_gray")
            S.set(x0 + 2, f, zb, IRON_WALL)
            S.set(x0 + 2, f + 1, zb, IRON_WALL)
            S.set(x0 + 2, f + 2, zb, IRON_WALL)
            bp.barrel(x0 + 2, f, zb + (-side), "up")
            if x0 == -10:
                chest(S, x0 - 1, f, zb, "east" if side > 0 else "east", "dw_crew")
    # mess tables with benches, a stove
    for x0 in (-13, -7):
        for x in range(x0, x0 + 4):
            S.set(x, f, 0, TABLE)
            S.set(x, f, -1, stair("spruce_stairs", "north"))
            S.set(x, f, 1, stair("spruce_stairs", "south"))
    S.set(-12, f + 1, 0, "candle[candles=2,lit=true,waterlogged=false]")
    S.set(-5, f + 1, 0, "lantern[hanging=false,waterlogged=false]")
    # an overturned table and debris washed in through the breach
    S.set(-2, f, 4, stair("spruce_stairs", "east", "top"))
    S.set(-1, f, -3, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    S.set(0, f, 6, IRON_SLAB + "[type=bottom,waterlogged=false]")
    S.set(-3, f, -12, "barrel[facing=east,open=false]")
    for x, z in ((-12, -6), (-6, -6), (-12, 6), (-6, 6), (-3, 0)):
        S.set(x, f + 3, z, HANG_LAMP)
    bp.spawner(-13, f, -4, MOB_DROWNED)
    # the stair up to the officers' mess (starboard), rising aft
    flight(S, -4, 9, 11, f, 6, -1)
    for x in range(-9, -3):
        S.set(x, MF, 8, f"{RAIL}[facing=north]")
    for z in (9, 10, 11):
        S.set(-3, MF, z, f"{RAIL}[facing=east]")


def officers_mess(S):
    bp = S.bp
    f = MF
    for x in range(X_ARF + 1, X_FWD):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f, z) == AIR and S.get(x, f - 1, z) == TREAD:
                S.set(x, f - 1, z, PARQUET)
    # the torn forward bulkhead: a few holes look out over the islet
    bulkhead(S, X_FWD, f, DECK - 2, MAHOGANY)
    for z, y in ((-4, f + 1), (3, f + 1), (4, f + 2), (-12, f + 2)):
        S.air(X_FWD, y, z)
    # the long table, chairs, a runner, chandeliers
    for x in range(-13, -4):
        S.set(x, f - 1, 0, "red_wool")
        S.set(x, f, 0, TABLE)
        S.set(x, f, -1, f"{CHAIR}[facing=south]")
        S.set(x, f, 1, f"{CHAIR}[facing=north]")
    S.set(-14, f, 0, f"{CHAIR}[facing=east]")
    for x in (-12, -9, -6):
        S.set(x, f + 1, 0, "candle[candles=3,lit=true,waterlogged=false]" if x != -9 else
              "lantern[hanging=false,waterlogged=false]")
        S.set(x, f + 3, 0, CHANDELIER)
    # sideboards and the steward's pantry against the sides
    for x in range(-14, -10):
        S.set(x, f, -14, MAHOGANY)
        S.set(x, f + 1, -14, f"{SHELF}[facing=south]")
    for x in range(-14, -10):
        S.set(x, f, 14, MAHOGANY)
    S.set(-12, f + 1, 14, "flower_pot")
    chest(S, -13, f, 13, "north", "dw_mess")
    bp.barrel(-11, f, 13, "up")
    S.set(-3, f, -3, "brasshaven:mahogany_table")
    S.set(-3, f + 1, -3, "brewing_stand")
    S.set(-2, f + 2, 4, f"{GAUGE}")
    for z in (-6, 6):
        S.set(-2, f + 1, z, EDISON)
    bp.spawner(-4, f, 12, MOB_KNIGHT)
    # the companion stair to the main deck (port), rising forward, under a hood on deck
    flight(S, -14, -11, -9, f, 6, 1)
    for x in range(-14, -9):
        S.set(x, f, -8, f"{RAIL}[facing=south]") if S.get(x, f, -8) == AIR else None
    hood(S)


def hood(S):
    """The companion hood over the mess stair: a little iron house open forward."""
    x0, x1, z0, z1 = -15, -8, -12, -8
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0,) or z in (z0, z1)
            for y in range(DF, DF + 4):
                if edge:
                    S.set(x, y, z, IRON if y < DF + 3 else IRON_BR)
                elif S.empty(x, y, z):
                    S.air(x, y, z)
            S.set(x, DF + 4, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
    S.set(-13, DF + 2, -12, "glass")
    S.set(-11, DF + 2, -12, "glass")
    S.set(-9, DF + 3, -10, HANG_LAMP)


def magazine(S):
    """The forward magazine in the hold: shell racks, powder cases, the hoist; behind the vault (after the boss)."""
    bp = S.bp
    f = HF
    for x in range(-9, X_FWD):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f - 1, z) is not None:
                S.set(x, f - 1, z, TREAD if (x + z) % 5 else IRON)
    # shell racks: brass shells standing in rows along both sides
    for side in (-1, 1):
        for x in range(-9, -1):
            r = zr(x, f)
            for k in (r, r - 1):
                z = side * k
                if (x, z) in ((-4, -9), (-3, -9)):
                    continue
                S.set(x, f, z, COPPER)
                S.set(x, f + 1, z, BRASS_STAIRS.replace("_stairs", "_slab") + "[type=bottom,waterlogged=false]")
            S.set(x, f + 2, side * r, IRON_SLAB + "[type=top,waterlogged=false]")
    # powder cases and loose charges
    for (x, z) in ((-8, -3), (-8, 3), (-7, -3), (-7, 3), (-6, 3)):
        S.set(x, f, z, "tnt")
    S.set(-8, f + 1, 3, "tnt")
    for (x, z) in ((-6, -3), (-2, 4), (-2, 5)):
        bp.barrel(x, f, z, "up")
    chest(S, -2, f, -3, "west", "dw_magazine")
    chest(S, -2, f, 2, "west", "dw_magazine")
    # safety lamps behind glass
    for z in (-6, 6):
        S.set(-9, f + 3, z, "soul_lantern[hanging=true,waterlogged=false]")
    S.set(-5, f + 4, 0, "soul_lantern[hanging=true,waterlogged=false]")
    # the doorway from the vault
    for z in (-1, 0, 1):
        for y in (f, f + 1, f + 2):
            S.air(-10, y, z)
    hoist(S)


def hoist(S):
    """The ammunition hoist: a ladder shaft from the magazine up through the crew quarters and the mess to the main
    deck beside the bridge tower; an iron door at the top with its lever inside (the shortcut back)."""
    x0, x1, z0, z1 = -5, -2, -9, -7
    top = DF + 3
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(HF, top + 1):
                wall = x in (x0, x1) or z in (z0, z1)
                if wall:
                    S.set(x, y, z, IRON if y % 4 else IRON_BR)
                else:
                    S.air(x, y, z)
            S.set(x, top + 1, z, IRON_BR)
    for y in range(HF, DF):
        S.set(-4, y, -8, "ladder[facing=south,waterlogged=false]")
    S.set(-3, DECK, -8, TREAD)
    # open at the bottom into the magazine
    for x in (-4, -3):
        S.air(x, HF, -7)
        S.air(x, HF + 1, -7)
    # the door out onto the deck (east face), the lever inside
    S.air(-2, DF, -8)
    S.air(-2, DF + 1, -8)
    S.bp.door(-2, DF, -8, "east", wood="iron")
    S.set(-3, DF + 1, -8, "lever[face=wall,facing=south,powered=false]")
    S.set(-1, DF + 2, -8, EDISON)


def vault(S):
    """The paymaster's strongroom behind sealed bars in the boiler hall's forward bulkhead (tier 3)."""
    f = HF
    for x in range(X_ARF + 1, -10):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f - 1, z) is not None:
                S.set(x, f - 1, z, BRASS if (x + z) % 2 else IRON_BR)
    for z in (-1, 0, 1):
        for y in (f, f + 1, f + 2):
            S.set(X_ARF, y, z, MOD["vault_bars"])
    chest(S, -12, f, -5, "north", "dw_vault")
    chest(S, -12, f, 5, "south", "dw_vault")
    for z in (-6, 6):
        S.set(-14, f, z, "gold_block")
        S.set(-14, f + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    S.set(-11, f, -7, "gold_block")
    S.set(-12, f + 3, 0, LANT_H)
    S.set(-12, f + 4, 0, CHAIN)
    S.set(-12, f + 5, 0, CHAIN)


# ------------------------------------------------------------------ the boiler hall (boss arena)
def boiler(S, cx, cz, face):
    """A giant vertical boiler: riveted drum, brass bands, a domed top, a lit firebox facing the hall."""
    y0, y1 = HF, HF + 11
    r = 4.4
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            for y in range(y0, y1 + 3):
                rr = r if y <= y1 else r * math.sqrt(max(0.0, 1 - ((y - y1) / 3.2) ** 2))
                if d <= rr:
                    if d > rr - 1.2 or y >= y1:
                        spec = BRASS if (y - y0) % 5 == 4 else (IRON_BR if int(math.degrees(math.atan2(z - cz, x - cx)) // 30) % 3 == 0 else IRON)
                    else:
                        spec = IRON
                    S.set(x, y, z, spec)
    dx, dz = DIRS[face]
    fx, fz = cx + dx * 5, cz + dz * 5
    S.set(fx - dx, y0, fz - dz, f"blast_furnace[facing={face},lit=true]")
    S.set(fx - dx, y0 + 1, fz - dz, f"blast_furnace[facing={face},lit=true]")
    S.set(fx - dx, y0 + 3, fz - dz, GAUGE)
    S.set(fx - dx + (1 if dz else 0), y0 + 4, fz - dz + (1 if dx else 0), f"{VALVE}[facing={face}]")
    # steam pipes up to the deckhead
    for y in range(y1 + 3, DECK - 1):
        S.set(cx, y, cz, PIPES)
    S.set(cx, y1 + 3, cz, BRASS)


def arena(S):
    bp = S.bp
    f = HF
    x0, x1 = X_ARA + 1, X_ARF - 1
    for x in range(x0, x1 + 1):
        r = zr(x, f)
        for z in range(-r, r + 1):
            d = math.hypot(x - AC[0], z - AC[1])
            if 9.5 <= d < 10.5 or 16.5 <= d < 17.5:
                spec = BRASS
            elif (x - x0) % 6 == 0 or z == 0:
                spec = IRON_BR
            else:
                spec = TREAD if hash3(x, f, z, 61) > 0.08 else "coal_block"
            S.set(x, f - 1, z, spec)
    # hull frames up the sides and deck beams across the deckhead (every 6)
    for x in range(x0 + 2, x1, 6):
        for y in range(f, DECK - 1):
            r = zr(x, y)
            for z in (-r, r):
                S.set(x, y, z, IRON_BR)
        r = zr(x, DECK - 2)
        for z in range(-r, r + 1):
            S.set(x, DECK - 2, z, IRON_BR)
    # side galleries at the lower-deck level, ladders up at their ends
    for side in (-1, 1):
        for x in range(x0, x1 + 1):
            r = zr(x, LF - 1)
            for k in (r, r - 1):
                S.set(x, LF - 1, side * k, TREAD)
            if S.get(x, LF, side * (r - 2)) == AIR:
                S.set(x, LF, side * (r - 2), f"{RAIL}[facing={'south' if side > 0 else 'north'}]")
        for x in (x0 + 1, x1 - 1):
            r = zr(x, LF - 1)
            z = side * (r - 1)
            for y in range(f, LF):
                S.set(x, y, z, f"ladder[facing={'north' if side > 0 else 'south'},waterlogged=false]")
            S.set(x, LF - 1, z, f"ladder[facing={'north' if side > 0 else 'south'},waterlogged=false]")
    # four giant boilers in the corners, their fireboxes facing the centre
    for bx in (x0 + 6, x1 - 6):
        for side in (-1, 1):
            boiler(S, bx, side * 10, "north" if side > 0 else "south")
    # the funnel uptakes: ducts in the deckhead; the fallen funnel's hole lets the sky in
    for fx in FUNNELS + (F2,):
        for x in range(fx - 4, fx + 5):
            for z in range(-3, 4):
                if ((x - fx) / 4.5) ** 2 + (z / 3.2) ** 2 <= 1.0:
                    S.air(x, DECK - 2, z)
                    S.air(x, DECK - 1, z)
                    S.set(x, DECK, z, BARS)
    # lamps on chains from the beams, the boss seal at the centre
    for x in range(x0 + 2, x1, 6):
        for z in (-8, 0, 8):
            if abs(x - AC[0]) < 4 and z == 0:
                continue
            S.set(x, DECK - 3, z, CHAIN)
            S.set(x, DECK - 4, z, HANG_LAMP)
    bp.boss_seal(AC[0], f - 1, AC[1], BOSS, 18)
    # the stokehold passage: compression before the hall (3 wide, 4 high, 7 long), the mist at its end
    for x in range(X_ENF, X_ARA + 1):
        for z in (-1, 0, 1):
            S.set(x, f - 1, z, TREAD)
            for y in range(f, f + 4):
                S.air(x, y, z)
            S.set(x, f + 4, z, IRON_BR)
        for z in (-2, 2):
            for y in range(f, f + 4):
                S.set(x, y, z, IRON_BR if x % 3 else PIPES)
    S.set(-60, f + 3, 0, HANG_LAMP)
    bp.mist(X_ARA, f, -1, X_ARA, f + 3, 1)


# ------------------------------------------------------------------ the engine room
def engine_room(S):
    bp = S.bp
    f = HF
    x0, x1 = X_ENA + 1, X_ENF - 1          # -84 .. -64
    for x in range(x0, x1 + 1):
        r = zr(x, f)
        for z in range(-r, r + 1):
            S.set(x, f - 1, z, TREAD if (x + z) % 7 else IRON_BR)
    for side in (-1, 1):
        zc = side * 9
        # crankcase
        for x in range(-82, -65):
            for z in range(zc - 2, zc + 3):
                for y in range(f, f + 4):
                    S.set(x, y, z, BRASS if y == f + 3 and abs(z - zc) == 2 else IRON_BR)
        # three cylinders on columns, piston rods, valve chests
        for cx in (-80, -74, -68):
            for x in range(cx - 3, cx + 4):
                for z in range(zc - 3, zc + 4):
                    d = math.hypot(x - cx, z - zc)
                    for y in range(f + 5, MF - 2):
                        if d <= 2.6:
                            S.set(x, y, z, BRASS if y in (f + 5, MF - 3) else
                                  (IRON_BR if (y - f) % 3 == 0 else IRON) if d > 1.6 else IRON)
            for (ax, az) in ((cx - 2, zc - 2), (cx + 2, zc - 2), (cx - 2, zc + 2), (cx + 2, zc + 2)):
                S.set(ax, f + 4, az, IRON_WALL)
            S.set(cx, f + 4, zc, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            S.set(cx, MF - 2, zc, GEAR)
        # the shafts aft to the screws
        for x in range(x0, -82):
            S.set(x, f, zc, IRON)
    # catwalks at the lower-deck level: the spine (centre), the aft cross catwalk, the side catwalks
    cw = LF - 1

    def walk(x, z):
        S.set(x, cw, z, TREAD)

    for x in range(-84, -70):
        for z in (-1, 0, 1):
            walk(x, z)
    for x in (-84, -83):
        r = zr(x, cw)
        for z in range(-min(r, 15), min(r, 15) + 1):
            walk(x, z)
    for side in (-1, 1):
        for x in range(-82, -74):
            for k in (13, 14, 15):
                walk(x, side * k)
    # railings along the open edges of the catwalks
    for side in (-1, 1):
        for x in range(-82, -74):
            if S.get(x, cw, side * 12) == AIR:
                S.set(x, cw + 1, side * 13, f"{RAIL}[facing={'north' if side > 0 else 'south'}]")
    # the stair down from the middle-deck corridor to the spine (descending aft)
    for i in range(6):
        x = -65 - i
        y = MF - 2 - i
        for z in (-1, 0, 1):
            S.set(x, y, z, stair(IRON_STAIRS, "east"))
            for yy in range(y + 1, y + 5):
                S.air(x, yy, z)
    # the side stairs down to the hold (descending forward), port and starboard
    for side in (-1, 1):
        for i in range(8):
            x = -74 + i
            y = cw - 1 - i
            for k in (13, 14, 15):
                z = side * k
                S.set(x, y, z, stair(IRON_STAIRS, "west"))
                for yy in range(y + 1, y + 5):
                    if S.get(x, yy, z) not in (None,) and yy <= cw + 4:
                        S.air(x, yy, z)
                for yy in range(f, y):
                    S.set(x, yy, z, IRON_BR if yy == f else IRON)
    # lamps, gauges, the engine-room telegraph, the grace on the hold landing before the passage
    for x in (-82, -76, -70):
        for z in (-5, 5):
            S.set(x, MF - 3, z, CHAIN)
            S.set(x, MF - 4, z, HANG_LAMP)
    S.set(-64, f, -5, MOD["waystone"])
    S.set(-64, f, 5, "brasshaven:mahogany_table")
    S.set(-64, f + 1, 5, "lantern[hanging=false,waterlogged=false]")
    for z in (-1, 0, 1):
        S.air(X_ENF, f, z)
        S.air(X_ENF, f + 1, z)
        S.air(X_ENF, f + 2, z)
    chest(S, -84, f, -12, "east", "dw_engine")
    bp.barrel(-84, f, 12, "up")
    bp.barrel(-84, f + 1, 12, "up")
    S.set(-84, cw + 2, -6, GAUGE)
    S.set(-84, cw + 2, 6, GAUGE)
    S.set(-84, cw + 1, 3, f"{VALVE}[facing=east]")
    bp.spawner(-78, f, 0, MOB_SPIDER)
    bp.spawner(-70, cw + 1, 14, MOB_SPIDER)


# ------------------------------------------------------------------ middle deck aft: corridor, cabins, wardroom
def middle_aft(S):
    bp = S.bp
    f = MF
    x0, x1 = X_ENA + 1, X_ENF - 1              # -84 .. -64 (above the engine room)
    # the corridor floor and its panelled walls
    for x in range(x0, x1 + 2):
        for z in range(-3, 4):
            if S.get(x, f - 1, z) not in (None, AIR) and S.get(x, f, z) == AIR:
                S.set(x, f - 1, z, PARQUET if abs(z) < 3 else MAHOGANY)
    for x in range(x0, x1 + 1):
        for z in (-4, 4):
            for y in range(f, f + 4):
                S.set(x, y, z, MAHOGANY if y < f + 3 else IRON)
    # cabins (port: four; starboard: two and the wardroom)
    parts = (-80, -75, -70)
    for side in (-1, 1):
        for xp in parts:
            if side > 0 and xp == -70:
                continue
            for z in range(5, 18):
                zz = side * z
                if abs(zz) > zr(xp, f):
                    break
                for y in range(f, f + 4):
                    S.set(xp, y, zz, MAHOGANY)
    rooms = [(-84, -81), (-79, -76), (-74, -71), (-69, -65)]
    for side in (-1, 1):
        for i, (a, b) in enumerate(rooms):
            if side > 0 and i >= 2:
                continue
            dx = (a + b) // 2
            S.air(dx, f, side * 4)
            S.air(dx, f + 1, side * 4)
            bp.door(dx, f, side * 4, "north" if side > 0 else "south", wood="spruce")
            r = zr(a, f)
            zb = side * (r - 1)
            bp.bed(a, f, zb, "east", ("blue", "cyan", "gray", "brown")[i])
            S.set(b, f, side * (r - 1), MAHOGANY)
            S.set(b, f + 1, side * (r - 1), "candle[candles=1,lit=true,waterlogged=false]")
            S.set(b, f, side * 6, stair(MAHOGANY_STAIRS, "west"))
            if (i + side) % 2 == 0:
                chest(S, b, f, side * (r - 3), "west", "dw_cabins")
            else:
                bp.barrel(b, f, side * (r - 3), "up")
            S.set(a + 1, f + 3, side * 9, HANG_LAMP)
            for x in range(a, b + 1):
                for z in (6, 7, 8):
                    if S.get(x, f, side * z) == AIR:
                        S.set(x, f, side * z, ("blue_carpet", "cyan_carpet", "gray_carpet", "brown_carpet")[i])
            S.set(a + 1, f + 1, side * 5, f"{SHELF}[facing={'south' if side > 0 else 'north'}]")
            S.set(b, f, side * 10, MAHOGANY_STAIRS.replace("_stairs", "_slab") + "[type=top,waterlogged=false]")
    # the wardroom (starboard, forward): the hub's site of grace, armchairs, a bookcase, the gun-room table
    a, b = -74, -65
    for x in range(a, b + 1):
        for z in range(5, zr(x, f) + 1):
            S.set(x, f - 1, z, PARQUET if (x + z) % 2 else MAHOGANY)
    S.air(-68, f, 4)
    S.air(-68, f + 1, 4)
    S.air(-69, f, 4)
    S.air(-69, f + 1, 4)
    S.set(-70, f, 10, MOD["waystone"])
    for x in range(-73, -69):
        S.set(x, f, 14, "bookshelf")
        S.set(x, f + 1, 14, "bookshelf")
    for x in (-67, -66):
        S.set(x, f, 8, TABLE)
    S.set(-67, f, 7, f"{CHAIR}[facing=south]")
    S.set(-66, f, 9, f"{CHAIR}[facing=north]")
    S.set(-72, f, 7, "red_wool")
    S.set(-66, f + 3, 11, CHANDELIER)
    S.set(-65, f + 1, 12, f"{GAUGE}")
    bp.spawner(-82, f, 2, MOB_WRAITH)
    for x in (-82, -76, -70):
        S.set(x, f + 3, 0, HANG_LAMP)
    # the doorway aft into the captain's quarters
    for z in (-1, 0, 1):
        for y in range(f, f + 3):
            S.air(X_ENA, y, z)
    # railings round the stairwell to the engine room
    for x in range(-71, -64):
        for z in (-2, 2):
            S.set(x, f, z, f"{RAIL}[facing={'north' if z < 0 else 'south'}]")
    for z in (-1, 0, 1):
        S.set(-72, f, z, f"{RAIL}[facing=west]")


def captain(S):
    """The captain's quarters at the stern: day cabin with the stern windows and the stern walk, a sleeping cabin, a
    hatch down to the steering flat."""
    bp = S.bp
    f = MF
    for x in range(XS + 1, X_ENA):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f - 1, z) not in (None, AIR) and S.get(x, f, z) == AIR:
                S.set(x, f - 1, z, PARQUET if abs(z) < 5 else MAHOGANY)
                if abs(z) < 3 and XS + 4 < x < X_ENA - 2:
                    S.set(x, f, z, "red_carpet")
    # the stern windows
    for y in (f + 1, f + 2):
        for z in range(-12, 13, 2):
            for x in range(XS - 1, XS + 8):
                if S.get(x, y, z) is not None and S.get(x, y, z) not in (AIR,) and \
                        any(S.get(x + dx, y, z) == AIR for dx in (1,)) and \
                        any(S.get(x - k, y, z) is None for k in (1, 2)):
                    S.set(x, y, z, "glass")
    # the great table, the desk, the chart table, bookcases, the captain's bed
    for x in (-91, -90, -89):
        S.set(x, f, 0, TABLE)
        S.set(x, f, -1, f"{CHAIR}[facing=south]")
        S.set(x, f, 1, f"{CHAIR}[facing=north]")
    S.set(-92, f, 0, f"{CHAIR}[facing=east]")
    S.set(-90, f + 1, 0, "candle[candles=3,lit=true,waterlogged=false]")
    S.set(-90, f + 3, 0, CHANDELIER)
    S.set(-87, f, 9, "cartography_table")
    S.set(-87, f, 10, "lectern[facing=west,has_book=false,powered=false]")
    for x in range(-91, -86):
        S.set(x, f, -11, "bookshelf")
        S.set(x, f + 1, -11, "bookshelf")
    bp.bed(-88, f, -8, "west", "red")
    chest(S, -86, f, -9, "west", "dw_captain")
    S.set(-86, f, 5, "brasshaven:mahogany_table")
    S.set(-86, f + 1, 5, "brasshaven:pressure_gauge")
    for z in (-6, 6):
        S.set(-87, f + 3, z, HANG_LAMP)
    # the stern walk: a door through the stern plating and a railed balcony round the stern
    xs = None
    for x in range(XS - 2, XS + 6):
        if S.get(x, f, 0) not in (None, AIR):
            xs = x
            break
    if xs is not None:
        S.air(xs, f, 0)
        S.air(xs, f + 1, 0)
        bp.door(xs, f, 0, "west", wood="spruce")
        for z in range(-9, 10):
            for x in range(XS - 4, XS + 8):
                if S.get(x, f - 1, z) is None and S.get(x + 1, f - 1, z) not in (None, AIR) and \
                        S.get(x + 1, f, z) not in (None, AIR):
                    for k in range(0, 3):
                        if S.get(x - k, f - 1, z) is None:
                            S.set(x - k, f - 1, z, TREAD if k < 2 else IRON)
                    if S.get(x - 2, f, z) is None:
                        S.set(x - 2, f, z, f"{RAIL}[facing=west]")
                    break
    # the hatch to the steering flat (ladder down)
    S.air(-92, f - 1, 6)
    S.air(-92, f - 2, 6)
    for y in range(LF, f):
        S.set(-92, y, 6, "ladder[facing=north,waterlogged=false]")
    S.set(-92, f - 1, 5, MAHOGANY)
    S.set(-92, f - 2, 5, IRON)


def steering_flat(S):
    """Under the captain: the steering engine, the rudder head, the captain's private store (tier 2)."""
    bp = S.bp
    f = LF
    for x in range(XS + 2, X_ENA):
        r = zr(x, f)
        for z in range(-r, r + 1):
            if S.get(x, f - 1, z) is not None:
                S.set(x, f - 1, z, TREAD)
    for x in (-91, -90):
        for z in (-1, 0, 1):
            S.set(x, f, z, IRON_BR)
            S.set(x, f + 1, z, GEAR if z == 0 else IRON)
    S.set(-89, f + 1, 0, f"{VALVE}[facing=east]")
    S.set(-90, f + 2, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in (-4, 4):
        S.set(-88, f, z, GEAR)
    chest(S, -87, f, -6, "east", "dw_captain")
    bp.barrel(-87, f, -7, "up")
    S.set(-89, f + 3, 3, HANG_LAMP)
    bp.spawner(-88, f, 4, MOB_CRAB)


# ------------------------------------------------------------------ main deck: deckhouse, funnels, bridge tower
def deckhouse(S):
    """The aft deckhouse: the companionway from the main deck down to the middle-deck corridor."""
    x0, x1, z0, z1 = -63, -57, -5, 5
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(DF, DF + 5):
                if edge:
                    S.set(x, y, z, IRON_BR if y == DF + 4 or (x in (x0, x1) and z in (z0, z1)) else IRON)
                else:
                    S.air(x, y, z)
            S.set(x, DF + 5, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if edge else IRON)
    for z in (-1, 0, 1):
        for y in range(DF, DF + 3):
            S.air(x1, y, z)
    for z in (-3, 3):
        S.set(x1, DF + 2, z, "glass")
    S.set(x1 + 1, DF + 3, -2, EDISON)
    S.set(x1 + 1, DF + 3, 2, EDISON)
    # the companionway: down 6 to the middle deck, descending aft
    for i in range(6):
        x = -59 - i
        y = DF - 2 - i
        for z in (-1, 0, 1):
            S.set(x, y, z, stair(IRON_STAIRS, "east"))
            for yy in range(y + 1, y + 5):
                S.air(x, yy, z)
    for x in range(-63, -58):
        for z in (-2, 2):
            for y in range(MF - 1, DF):
                if S.get(x, y, z) in (AIR, None, "coal_block") or True:
                    S.set(x, y, z, IRON)
    S.set(-62, DF + 3, 0, HANG_LAMP)
    for z in (-4, 4):
        S.bp.barrel(-62, DF, z, "up")


def funnel(S, fx, top, standing=True):
    """An oval funnel (long fore and aft): a casing on deck, the iron stack with brass bands and a sooty crown, two
    steam pipes up its aft face."""
    rx, rz = 4.6, 3.3
    for x in range(fx - 7, fx + 8):
        for z in range(-6, 7):
            e = ((x - fx) / (rx + 1.5)) ** 2 + (z / (rz + 1.5)) ** 2
            if e <= 1.0:
                for y in range(DF, DF + 3):
                    inner = ((x - fx) / rx) ** 2 + (z / rz) ** 2 <= 1.0
                    if not inner:
                        S.set(x, y, z, IRON_BR if y == DF + 2 else IRON)
    yt = top if standing else DF + 3
    for x in range(fx - 6, fx + 7):
        for z in range(-5, 6):
            e = ((x - fx) / rx) ** 2 + (z / rz) ** 2
            ei = ((x - fx) / (rx - 1.1)) ** 2 + (z / (rz - 1.1)) ** 2
            if e > 1.0:
                continue
            for y in range(DF, yt + 1):
                if not standing:
                    jag = DF + 1 + int(hash01(x, z, 71) * 4)
                    if y > jag:
                        break
                if ei > 1.0:
                    if y >= yt - 3:
                        spec = SOOT
                    elif (y - DF) % 9 == 8:
                        spec = BRASS
                    else:
                        spec = IRON if hash3(x, y, z, 72) > 0.06 else RUST
                    S.set(x, y, z, spec)
                elif S.get(x, y, z) is None or S.get(x, y, z) == AIR:
                    S.air(x, y, z)
    if standing:
        for z in (-1, 1):
            for y in range(DF + 2, top + 2):
                S.set(fx - 5, y, z, PIPES)
            S.set(fx - 5, top + 2, z, BRASS)
        # the cap grating
        S.set(fx, top - 1, 0, IRON_BR)


def fallen_funnel(S):
    """Funnel 2 broke at its foot and fell across the starboard deck, its crown hanging over the side."""
    A = (F2 + 1.0, DF + 3.6, 3.0)
    B = (F2 + 9.0, DF + 1.5, 31.0)
    vx, vy, vz = B[0] - A[0], B[1] - A[1], B[2] - A[2]
    Lf = math.sqrt(vx * vx + vy * vy + vz * vz)
    ux, uy, uz = vx / Lf, vy / Lf, vz / Lf
    R = 4.0
    for x in range(int(min(A[0], B[0])) - 6, int(max(A[0], B[0])) + 7):
        for y in range(int(B[1]) - 6, int(A[1]) + 6):
            for z in range(int(A[2]) - 6, int(B[2]) + 6):
                px, py, pz = x - A[0], y - A[1], z - A[2]
                t = px * ux + py * uy + pz * uz
                if t < 0 or t > Lf:
                    continue
                qx, qy, qz = px - t * ux, py - t * uy, pz - t * uz
                d = math.sqrt(qx * qx + qy * qy + qz * qz)
                if d > R or d < R - 1.15:
                    continue
                if y <= DECK and abs(z) <= zr(x, DECK) + 2:
                    continue
                if S.get(x, y, z) not in (None, AIR):
                    continue
                if t > Lf - 3:
                    spec = SOOT
                elif int(t) % 9 == 8:
                    spec = BRASS
                elif t < 1.5:
                    spec = RUST
                else:
                    spec = IRON if hash3(x, y, z, 73) > 0.07 else RUST
                S.set(x, y, z, spec)
    # the crushed bulwark under it
    for x in range(F2 + 4, F2 + 9):
        z = zr(x, DECK) + 1
        if S.get(x, DF, z) is not None:
            S.set(x, DF, z, IRON_SLAB + "[type=bottom,waterlogged=false]")


def bridge_tower(S):
    bp = S.bp
    x0, z0, x1, z1 = BT
    # level 0 (feet DF), level 1 (B1, the conning tower and chart room), level 2 (B2, wheelhouse with wings), roof
    levels = ((DF, x0, z0, x1, z1), (B1, x0 + 1, z0 + 1, x1 - 1, z1 - 1), (B2, x0 + 2, z0, x1, z1))
    for (f, a0, c0, a1, c1) in levels:
        for x in range(a0, a1 + 1):
            for z in range(c0, c1 + 1):
                edge = x in (a0, a1) or z in (c0, c1)
                S.set(x, f - 1, z, TREAD if not edge else IRON_BR) if f != DF else None
                for y in range(f, f + 5):
                    if y == f + 4:
                        continue
                    if edge:
                        if f == B2 and y in (f + 1, f + 2) and not (x in (a0, a1) and z in (c0, c1)):
                            S.set(x, y, z, "glass")
                        elif f == B1 and y == f + 1 and (x - a0) % 3 == 1:
                            S.set(x, y, z, "glass")
                        else:
                            S.set(x, y, z, IRON if f != B1 else IRON_BR)
                    else:
                        S.air(x, y, z)
    # the conning-tower step: fill the level-1 margin as a ledge with railings
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                S.set(x, B1 - 1, z, IRON_BR)
    # bridge wings at level 2 and the roof
    for x in range(x0 + 2, x1 + 1):
        for z in range(z0 - 4, z1 + 5):
            S.set(x, B2 - 1, z, TREAD if abs(z) < 9 else IRON_BR)
            if abs(z) > z1:
                if abs(z) == z1 + 4 or x in (x0 + 2, x1):
                    S.set(x, B2, z, f"{RAIL}[facing={'south' if z > 0 else 'north'}]" if abs(z) == z1 + 4 else
                          f"{RAIL}[facing={'west' if x == x0 + 2 else 'east'}]")
                elif S.get(x, B2, z) is None:
                    S.air(x, B2, z)
                if (x - x0) % 4 == 0:
                    S.set(x, B2 - 2, z, stair(IRON_STAIRS, "south" if z < 0 else "north", "top")) if abs(z) == z1 + 1 \
                        else None
    for x in range(x0 + 2, x1 + 1):
        for z in range(z0, z1 + 1):
            S.set(x, BROOF - 1, z, IRON_BR if x in (x0 + 2, x1) or z in (z0, z1) else IRON)
    for x in range(x0 + 2, x1 + 1):
        for z in (z0, z1):
            S.set(x, BROOF, z, f"{RAIL}[facing={'north' if z == z0 else 'south'}]")
    for z in range(z0 + 1, z1):
        S.set(x1, BROOF, z, f"{RAIL}[facing=east]")
        S.set(x0 + 2, BROOF, z, f"{RAIL}[facing=west]")
    # doors and stairs: the deck door (aft face), level 0 -> 1 (starboard, rising forward), 1 -> 2 (port, rising aft)
    for z in (-1, 0, 1):
        for y in range(DF, DF + 3):
            S.air(x0, y, z)
    flight(S, -13, 3, 4, DF, 6, 1)
    flight(S, -5, -4, -3, B1, 5, -1)
    for x in range(x0 + 2, x1 - 1, 3):
        for z in (z0, z1):
            S.set(x, DF + 2, z, "glass")
    # level 0: the hoist's neighbour, a signal locker
    S.set(-4, DF, -4, "barrel[facing=up,open=false]")
    S.set(-4, DF + 3, 0, HANG_LAMP)
    S.set(-14, DF + 3, -4, HANG_LAMP)
    # level 1: chart table, voice pipes
    S.set(-10, B1, -3, "cartography_table")
    chest(S, -11, B1, -3, "east", "dw_bridge")
    for y in range(B1, B1 + 4):
        S.set(-5, y, 3, PIPES)
    S.set(-8, B1 + 3, 0, HANG_LAMP)
    # level 2: the helm, telegraphs, binnacle
    S.set(-5, B2, 0, MAHOGANY)
    S.set(-6, B2 + 1, 0, f"{VALVE}[facing=west]")
    S.set(-5, B2, -3, IRON_WALL)
    S.set(-5, B2 + 1, -3, GAUGE)
    S.set(-5, B2, 3, IRON_WALL)
    S.set(-5, B2 + 1, 3, GAUGE)
    S.set(-7, B2, 2, BRASS)
    S.set(-7, B2 + 1, 2, "lantern[hanging=false,waterlogged=false]")
    chest(S, -12, B2, 4, "east", "dw_bridge")
    S.set(-9, B2 + 3, 0, HANG_LAMP)
    # searchlights on the wings
    for z in (z0 - 3, z1 + 3):
        S.set(x1 - 1, B2, z, IRON_WALL)
        S.set(x1 - 1, B2 + 1, z, EDISON)
    # the ladder from level 2 to the roof
    for y in range(B2, BROOF):
        S.set(-12, y, -5, "ladder[facing=south,waterlogged=false]")
    tripod(S)


def tripod(S):
    """The tripod foremast on the bridge roof: a main leg, two raking legs, the spotting top, the topmast."""
    mx = MAST_X
    for y in range(BROOF, TOP_F + 9):
        S.set(mx, y, 0, IRON_BR if y % 6 else BRASS)
        S.set(mx - 1, y, 0, IRON_BR if y % 6 else BRASS)
    for side in (-1, 1):
        a = (BT[0] + 3, BROOF, side * 5)
        b = (mx - 1, TOP_F - 2, side * 1)
        n = 40
        for i in range(n + 1):
            t = i / n
            S.set(int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t)),
                  int(round(a[2] + (b[2] - a[2]) * t)), IRON)
    # ladder up the main leg, with rest platforms
    for y in range(BROOF, TOP_F):
        S.set(mx + 1, y, 0, "ladder[facing=east,waterlogged=false]")
    for yp in (BROOF + 10, BROOF + 20):
        for z in (-1, 1):
            S.set(mx + 1, yp - 1, z, GRILLE)
            S.set(mx + 2, yp - 1, z, GRILLE)
        S.set(mx + 2, yp - 1, 0, GRILLE)
    # the spotting top: a round platform with a low armoured wall and a roof
    tf = TOP_F
    for x in range(mx - 6, mx + 6):
        for z in range(-6, 7):
            d = math.hypot(x - (mx - 0.5), z)
            if d <= 5.4:
                S.set(x, tf - 1, z, TREAD if d < 4.4 else IRON_BR)
                if 4.4 <= d:
                    S.set(x, tf, z, IRON)
                    S.set(x, tf + 1, z, IRON if (x + z) % 3 else "glass")
                    S.set(x, tf + 4, z, IRON_BR)
                elif d < 4.4 and S.get(x, tf, z) is None:
                    for y in range(tf, tf + 4):
                        if S.get(x, y, z) is None:
                            S.air(x, y, z)
                    S.set(x, tf + 4, z, IRON if d > 1.2 else IRON_BR)
    S.air(mx + 1, tf - 1, 0)
    S.set(mx + 1, tf - 1, 0, "ladder[facing=east,waterlogged=false]")
    S.set(mx - 3, tf + 3, -2, HANG_LAMP)
    chest(S, mx - 3, tf, 2, "east", "dw_top")
    S.set(mx - 4, tf, -2, BRASS)
    # rangefinder arms and the topmast
    for z in range(-8, 9):
        S.set(mx - 1, tf + 5, z, BRASS if abs(z) < 8 else "glass")
    for y in range(tf + 5, MAST_TOP + 1):
        S.set(mx - 1, y, 0, IRON_BR if y < MAST_TOP - 6 else IRON_WALL)
    for z in range(-4, 5):
        S.set(mx - 1, MAST_TOP - 6, z, IRON_WALL if abs(z) < 4 else EDISON)


def turret_access(S):
    """Doors into the stern turrets' gunhouses (rear walls): X by a stair up its barbette, Y by a step; a chest in
    each."""
    bp = S.bp
    for (name, sc, dh, top, aim, _, _, sec) in TURRETS:
        if sec != "stern":
            continue
        fy = KEEL + top                    # gunhouse floor block
        rx = int(math.floor(XS + sc + 6.5))      # the rear wall (aim -1: the rear faces forward)
        while S.get(rx, fy + 1, 0) in (None, AIR):
            rx -= 1
        for y in (fy + 1, fy + 2):
            S.air(rx, y, 0)
        if fy > DECK:
            n = fy - DECK                  # steps rising towards -z up to a landing in front of the door
            for i in range(n):
                z = n - i
                for x in (rx + 1, rx + 2):
                    S.set(x, DF + i, z, stair(IRON_STAIRS, "north"))
                    for yy in range(DF, DF + i):
                        S.set(x, yy, z, IRON)
                    for yy in range(DF + i + 1, DF + i + 4):
                        if S.get(x, yy, z) is None:
                            S.air(x, yy, z)
            for x in (rx + 1, rx + 2):
                for yy in range(DF, fy + 1):
                    S.set(x, yy, 0, IRON_BR if yy == fy else IRON)
                for yy in range(fy + 1, fy + 4):
                    S.air(x, yy, 0)
                S.set(x, fy + 1, -1, f"{RAIL}[facing=north]")
        else:
            S.set(rx + 1, DF, 0, stair(IRON_STAIRS, "west"))
        inner_x = rx - 2
        chest(S, inner_x, fy + 1, 3, "east", "dw_turret")
        S.set(inner_x - 2, fy + 1, -2, IRON_WALL)
        S.set(inner_x - 2, fy + 2, -2, GAUGE)
        S.set(inner_x, fy + 4, 0, HANG_LAMP)


def deck_details(S):
    """Ventilator cowls, capstans, a wrecked launch on its davits, deck lamps; the main-deck route is lit."""
    bp = S.bp
    for (x, z) in ((-31, -7), (-44, -7), (-31, 8), (-56, 6)):
        for y in (DF, DF + 1, DF + 2):
            S.set(x, y, z, COPPER if y < DF + 2 else VERD)
        S.set(x, DF + 3, z, stair("brasshaven:copper_plating_stairs", "east", "top"))
    for (x, z) in ((-20, -12), (-33, -13), (-46, -13), (-56, -12), (-78, -12), (-92, -6)):
        if S.get(x, DF, z) is None or S.get(x, DF, z) == AIR:
            S.set(x, DF, z, IRON_WALL)
            S.set(x, DF + 1, z, IRON_WALL)
            S.set(x, DF + 2, z, EDISON)
    # bollards and a capstan on the quarterdeck
    for (x, z) in ((-93, -8), (-93, 8)):
        S.set(x, DF, z, IRON_BR)
    S.set(-78, DF, 9, GEAR)
    S.set(-78, DF + 1, 9, IRON_WALL)
    # the ship's boats on their chocks (port, between the funnels), one cutter hanging off the quarter by one fall
    boat(S, -48, -41, -13, DF + 1)
    boat(S, -35, -29, -13, DF + 1)
    for x in (-82, -74):
        z = -zr(x, DECK)
        for y in range(DF, DF + 6):
            S.set(x, y, z, IRON_WALL)
        for k in range(0, 4):
            S.set(x, DF + 6, z - k, IRON)
    for y in range(DF + 1, DF + 6):
        S.set(-82, y, -zr(-82, DECK) - 3, CHAIN)
    for x in range(-81, -74):
        t = (x + 81) / 7
        y = DF - int(t * 4)
        z = -zr(-78, DECK) - 3
        S.set(x, y, z, "spruce_planks")
        S.set(x, y + 1, z - 1, stair("spruce_stairs", "south"))
        S.set(x, y + 1, z + 1, stair("spruce_stairs", "north"))
    # skylights over the captain's cabin and the wardroom (light wells through the deck)
    skylight(S, -92, -88, 7, 10)
    skylight(S, -73, -68, 7, 10)
    # the searchlight platform round the forward funnel
    fx = FUNNELS[0]
    yp = DF + 16
    for x in range(fx - 8, fx + 9):
        for z in range(-6, 7):
            e = ((x - fx) / 6.6) ** 2 + (z / 5.3) ** 2
            ei = ((x - fx) / 4.6) ** 2 + (z / 3.3) ** 2
            if ei > 1.0 and e <= 1.0 and S.get(x, yp, z) is None:
                S.set(x, yp, z, GRILLE)
                if e > 0.7:
                    S.set(x, yp + 1, z, f"{RAIL}[facing={'north' if z < 0 else 'south'}]")
    for z in (-5, 5):
        S.set(fx + 4, yp + 1, z, IRON_WALL)
        S.set(fx + 4, yp + 2, z, EDISON)
    mainmast(S)


def boat(S, x0, x1, zc, y):
    """A ship's boat upright on two chocks: planked hull, gunwales, thwarts, a canvas over the bow."""
    for x in range(x0, x1 + 1):
        end = x in (x0, x1)
        if x in (x0 + 1, x1 - 1):
            for z in (zc - 1, zc, zc + 1):
                S.set(x, y - 1, z, IRON_SLAB + "[type=top,waterlogged=false]")
        S.set(x, y, zc, "spruce_planks")
        if end:
            S.set(x, y + 1, zc, "spruce_planks")
            continue
        S.set(x, y + 1, zc - 1, stair("spruce_stairs", "south"))
        S.set(x, y + 1, zc + 1, stair("spruce_stairs", "north"))
        S.set(x, y, zc - 1, stair("spruce_stairs", "south", "top"))
        S.set(x, y, zc + 1, stair("spruce_stairs", "north", "top"))
        if (x - x0) % 3 == 0:
            S.set(x, y + 1, zc, "spruce_slab[type=bottom,waterlogged=false]")
    for z in (zc - 1, zc, zc + 1):
        S.set(x1 - 1, y + 2, z, "white_carpet") if z == zc else None


def skylight(S, x0, x1, z0, z1):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if edge:
                S.set(x, DF, z, IRON_BR)
            else:
                S.air(x, DECK - 1, z)
                S.set(x, DECK, z, "glass")
                S.set(x, DF, z, BRASS_SLAB + "[type=bottom,waterlogged=false]" if (x + z) % 2 else "glass")


def mainmast(S):
    """A pole mainmast on the aft deckhouse: a crow's nest, a yard, the boat derrick."""
    mx, mz = -60, 0
    y0 = DF + 6
    for y in range(y0, DF + 40):
        S.set(mx, y, mz, IRON_BR if y % 7 else BRASS)
    yn = DF + 30
    for x in range(mx - 2, mx + 3):
        for z in range(mz - 2, mz + 3):
            if abs(x - mx) + abs(z - mz) <= 3 and (x, z) != (mx, mz):
                S.set(x, yn - 1, z, GRILLE)
                if abs(x - mx) == 2 or abs(z - mz) == 2:
                    S.set(x, yn, z, f"{RAIL}[facing={'west' if x < mx else 'east' if x > mx else 'north' if z < mz else 'south'}]")
    for z in range(-7, 8):
        S.set(mx, DF + 35, z, IRON_WALL if abs(z) < 7 else EDISON)
    # the derrick: a boom from the mast foot out over the boats
    for i in range(14):
        t = i / 13
        S.set(int(round(mx + 2 + t * 10)), int(round(y0 + 3 + t * 6)), int(round(-1 - t * 9)), IRON_WALL)
    for y in range(DF + 2, y0 + 9):
        pass


# ------------------------------------------------------------------ the bow section
def bow(S):
    bp = S.bp
    pts = [bow_world(u, h, v) for u in (-2, 84) for h in (-2, 42) for v in (-20, 20)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
        for z in range(int(min(zs)) - 1, int(max(zs)) + 2):
            for y in range(max(-3, int(min(ys)) - 1), int(max(ys)) + 2):
                u, h, v = bow_local(x, y, z)
                if u < -1 or u > L - S_BOW0 + 1 or abs(v) > 21 or h < -1.5 or h > 41:
                    continue
                s = S_BOW0 + u
                jag = min(2, int(3.2 * fbm(h * 1.7, v * 1.5, 3.0, 78)))   # the watertight bulkhead stays whole
                if u < jag:
                    continue
                spec = ship_cell(s, v, h, "bow")
                if spec is None:
                    continue
                if (x, y, z) in S.bp.blocks and S.bp.get(x, y, z) not in (AIR,) and spec == AIR:
                    continue
                if spec == AIR and y <= 1:
                    spec = "sand"
                if spec == AIR:
                    # flooded: everything under the middle deck (hold, lower deck, torpedo deck) and the rest up to
                    # the door sills; only the top of the forward mess deck keeps a pocket of trapped air
                    if y <= max(SEA, BOW_WL) or h < MID_H - 1.5:
                        S.set(x, y, z, "water")
                    else:
                        S.air(x, y, z)
                else:
                    if y <= SEA and spec.startswith("minecraft:") is False and "[" not in spec:
                        pass
                    S.set(x, y, z, spec)
                S.bow.add((x, y, z))
    smooth_bow(S)
    bow_doors(S)
    flood_bow(S)
    bow_rooms(S)


def smooth_bow(S):
    """Half steps on the tilted decks above the water: a bottom slab wherever a deck rises one block."""
    bp = S.bp
    slabs = {"minecraft:spruce_planks": "spruce_slab", "minecraft:dark_oak_planks": "dark_oak_slab",
             TREAD: TREAD_SLAB, IRON: IRON_SLAB, IRON_BR: IRON_BR_SL}
    adds = []
    for (x, y, z) in S.bow:
        if y <= SEA:
            continue
        b = bp.get(x, y, z)
        if b not in slabs:
            continue
        if bp.get(x, y + 1, z) not in (AIR,) or bp.get(x, y + 2, z) not in (AIR,):
            continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = bp.get(x + dx, y + 1, z + dz)
            if n in slabs and bp.get(x + dx, y + 2, z + dz) == AIR and bp.get(x + dx, y + 3, z + dz) == AIR:
                adds.append((x, y + 1, z, slabs[b]))
                break
    for (x, y, z, sl) in adds:
        if bp.get(x, y + 1, z) == AIR:
            name = sl if ":" in sl else "minecraft:" + sl
            S.set(x, y, z, f"{name}[type=bottom,waterlogged=false]")


def bow_doors(S):
    """Doors in the bow's two openings (the watertight bulkhead at the broken end, on the middle deck, and the
    forecastle break, on the main deck): a door holds water back, so the flooded compartments stay full above a
    shallow sea and the trapped air stays dry under a deep one; the rest of each opening is plated over."""
    bp = S.bp
    for (u0, u1, f) in ((2.5, 4.0, MID_H), (FC_S - S_BOW0 - 0.75, FC_S - S_BOW0 + 0.75, MAIN_H)):
        cells = {}
        for p in S.bow:
            if bp.get(*p) not in (AIR, "minecraft:water"):
                continue
            u, h, v = bow_local(*p)
            if u0 <= u < u1 and abs(v) < 1.6 and f + 0.5 <= h < f + 3.5:
                cells[p] = u
        if not cells:
            continue
        # the door: the column nearest the centre line with two open cells over a solid sill
        best = None
        for (x, y, z), u in cells.items():
            if (x, y + 1, z) not in cells or (x, y - 1, z) in cells:
                continue
            below = bp.get(x, y - 1, z)
            if below in (None, AIR, "minecraft:water") or not is_solid(below):
                continue
            key = (abs(z - round(bow_world(u, f + 1.0, 0.0)[2])), y)
            if best is None or key < best[0]:
                best = (key, (x, y, z), u)
        if best is None:
            continue
        _, (dx, dy, dz), du = best
        keep = set()
        for (x, y, z), u in cells.items():
            if z == dz and y in (dy, dy + 1) and x != dx:
                keep.add((x, y, z))
                if u < du:                                   # the outer side of the door is the sea's
                    bp.remove(x, y, z)
                    S.inner.discard((x, y, z))
                    S.bow.discard((x, y, z))
                else:
                    S.set(x, y, z, AIR if y > BOW_WL else "water")
        for p in cells:
            if p not in keep and p not in ((dx, dy, dz), (dx, dy + 1, dz)):
                S.set(*p, IRON_BR)
        face = "west"
        bp.door(dx, dy, dz, face, wood="spruce")
        S.inner.add((dx, dy, dz))
        S.inner.add((dx, dy + 1, dz))


def flood_bow(S):
    """Settle the bow's water: open cells level with or under water fill too (no still wall of water inside the
    hull), every hole in the plating above the sea is plugged, and whatever can be waterlogged in the water is."""
    bp = S.bp
    water = "minecraft:water"
    todo = [p for p in S.bow if bp.get(*p) == water]
    seen = set(todo)
    while todo:
        x, y, z = todo.pop()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
            q = (x + dx, y + dy, z + dz)
            b = bp.get(*q)
            if b == AIR and q in S.bow:
                bp.set(*q, "water")
                S.inner.discard(q)
            elif b is None and q[1] > SEA:
                bp.set(*q, IRON)
                S.bow.add(q)
                continue
            else:
                continue
            if q not in seen:
                seen.add(q)
                todo.append(q)
    # waterlog what stands in the water (never a block that touches the trapped air: it would spill into it)
    for q in list(S.bow):
        b = bp.blocks.get(q)
        if not b or b[1].get("waterlogged") != "false":
            continue
        x, y, z = q
        nbs = [bp.get(x + dx, y + dy, z + dz) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
                                                                  (0, 1, 0))]
        if any(n == water for n in nbs) and not any(n in (None, AIR) for n in nbs[:4]) and nbs[4] != AIR:
            bp.blocks[q] = (b[0], dict(b[1], waterlogged="true"), b[2])


def bow_spot(S, u, v, h_feet, need_dry=False):
    """A standable cell near bow-local (u, v) on the deck whose feet are at h_feet: (x, y, z) or None."""
    x, y, z = ri(bow_world(u, h_feet + 0.5, v))
    for dy in (0, 1, -1, 2, -2):
        yy = y + dy
        here = S.bp.get(x, yy, z)
        below = S.bp.get(x, yy - 1, z)
        if here in (AIR, "minecraft:water") and below is not None and is_solid(below):
            if need_dry and here != AIR:
                return None
            return (x, yy, z)
    return None


def bow_rooms(S):
    bp = S.bp
    # the forward mess deck (dry part of the middle deck behind the broken end)
    for (u, v, what) in ((7, -9, "chest"), (9, 9, "barrel"), (12, -10, "table"), (6, 8, "lamp")):
        p = bow_spot(S, u, v, MID_H + 1)
        if not p:
            continue
        x, y, z = p
        if what == "chest":
            (chest if bp.get(x, y, z) == AIR else wet_chest)(S, x, y, z, "east", "dw_bow")
        elif what == "barrel":
            bp.barrel(x, y, z, "up")
        elif what == "table":
            S.set(x, y, z, stair("spruce_stairs", "east", "top"))
        elif what == "lamp" and bp.get(x, y, z) == AIR:
            S.set(x, y, z, LANT)
    p = bow_spot(S, 10, 0, MID_H + 1)
    if p and bp.get(*p) == AIR:
        x, y, z = p
        S.set(x, y + 3, z, HANG_LAMP) if S.bp.get(x, y + 3, z) == AIR else None
    # the forecastle tween deck: the bosun's store
    for (u, v, what) in ((26, -7, "chest"), (28, 7, "barrel"), (30, 0, "spawner"), (25, 6, "lamp")):
        p = bow_spot(S, u, v, MAIN_H + 1)
        if not p:
            continue
        x, y, z = p
        if what == "chest":
            (chest if bp.get(x, y, z) == AIR else wet_chest)(S, x, y, z, "east", "dw_bow")
        elif what == "barrel":
            bp.barrel(x, y, z, "up")
        elif what == "spawner":
            bp.spawner(x, y, z, MOB_DROWNED)
        elif what == "lamp" and bp.get(x, y, z) == AIR:
            S.set(x, y, z, LANT)
    # the flooded torpedo deck: the torpedo store chests, a crab den
    for (u, v) in ((53, -1), (55, 1)):
        p = bow_spot(S, u, v, LOW_H + 1)
        if p:
            x, y, z = p
            (chest if bp.get(x, y, z) == AIR else wet_chest)(S, x, y, z, "east", "dw_torpedo")
    p = bow_spot(S, 47, 0, LOW_H + 1)
    if p:
        bp.spawner(*p, MOB_CRAB)
    # the flooded lower deck: seagrass in the silt on the deck, sea pickles glowing between the torpedo racks
    for (x, y, z) in sorted(S.bow):
        if bp.get(x, y, z) != "minecraft:water" or not is_solid(bp.get(x, y - 1, z) or "minecraft:air"):
            continue
        u, h, v = bow_local(x, y, z)
        if not LOW_H < h < MID_H - 1.5 or bp.get(x, y - 1, z) == "minecraft:sand":
            continue
        hv = hash3(x, y, z, 141)
        if hv < 0.035 and 40 <= u < 62:
            bp.set(x, y, z, f"sea_pickle[pickles={1 + int(hash3(x, y, z, 143) * 4)},waterlogged=true]")
        elif hv < 0.13:
            bp.set(x, y, z, "seagrass")
    # anchor chains from the hawse pipes down to the sand
    for v in (-4.5, 4.5):
        x, y, z = ri(bow_world(L - S_BOW0 - 9, FC_H - 2, v * 1.0 + (1.6 if v > 0 else -1.6)))
        yy = y
        while yy > 0 and S.bp.get(x, yy, z) in (None, AIR, "minecraft:water"):
            S.set(x, yy, z, "iron_chain[axis=y,waterlogged=true]" if yy <= SEA else CHAIN)
            yy -= 1


def gap(S):
    """The break: the islet's camp and waystone, debris from both broken ends, a plank bridge from the stern's main
    deck to the bow's, a debris stair from the islet up to the bow's door."""
    bp = S.bp
    top = SEA
    # the islet top: a flat landing in front of the breach
    for x in range(-2, 15):
        for z in range(-13, 14):
            if (x, z) in S.reef and S.reef[(x, z)] >= top - 1 and bp.get(x, top + 1, z) is None:
                bp.set(x, top, z, "gravel" if hash01(x, z, 81) < 0.4 else "andesite")
    # the castaways' camp on the port side of the islet
    cx, cz = 6, -19
    for x in range(cx - 6, cx + 6):
        for z in range(cz - 6, cz + 6):
            if (x, z) in S.reef and S.reef[(x, z)] >= top - 2:
                for y in range(S.reef[(x, z)], top + 1):
                    bp.set(x, y, z, "andesite" if y < top else ("gravel" if hash01(x, z, 82) < 0.5 else "stone"))
                S.reef[(x, z)] = top
    bp.set(cx - 2, top + 1, cz, MOD["waystone"])
    bp.set(cx + 1, top + 1, cz + 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # a lean-to of sailcloth on oars
    for x in range(cx + 2, cx + 6):
        bp.set(x, top + 1, cz - 3, "spruce_fence")
        bp.set(x, top + 2, cz - 3, "spruce_fence")
        bp.set(x, top + 3, cz - 2, "white_wool")
        bp.set(x, top + 3, cz - 3, "white_wool")
    bp.bed(cx + 3, top + 1, cz - 2, "east", "white")
    chest(S, cx + 5, top + 1, cz - 1, "west", "dw_camp")
    bp.barrel(cx - 3, top + 1, cz + 2, "up")
    bp.barrel(cx - 3, top + 2, cz + 2, "up")
    for y in (top + 1, top + 2):
        bp.set(cx + 4, y, cz + 3, "spruce_fence")
    bp.set(cx + 4, top + 3, cz + 3, LANT)
    # the beached launch
    for x in range(cx - 5, cx + 1):
        z = cz + 5
        bp.set(x, top + 1, z, "spruce_slab[type=bottom,waterlogged=false]")
        if cx - 5 < x < cx:
            bp.set(x, top + 1, z - 1, stair("spruce_stairs", "south"))
            bp.set(x, top + 1, z + 1, stair("spruce_stairs", "north"))
    # debris on the islet: torn plates, a fallen boiler drum, pipes
    for (x, z, sp) in ((3, 6, IRON_SLAB), (5, -6, IRON_BR_SL), (9, 3, IRON_SLAB), (11, -9, IRON_BR_SL),
                       (1, -10, IRON_SLAB), (12, 9, IRON_SLAB)):
        if bp.get(x, top + 1, z) is None:
            bp.set(x, top + 1, z, sp + "[type=bottom,waterlogged=false]")
    for z in range(6, 12):
        for x in range(7, 12):
            d = math.hypot(x - 9, (top + 2.5) - (top + 2.5))
        for (dx, dy) in ((-2, 0), (-2, 1), (-2, 2), (2, 0), (2, 1), (2, 2), (-1, 3), (0, 3), (1, 3), (-1, -0), (1, 0)):
            if dy >= 0:
                bp.set(9 + dx, top + 1 + dy, z, IRON if (z + dy) % 4 else BRASS)
    for x in range(-1, 5):
        bp.set(x, top + 1, 11, "brasshaven:copper_pipe[axis=x]")
    # the plank bridge from the stern's main deck to the bow's main deck
    land = None
    for x in range(10, 26):
        for y in range(DECK + 2, DECK - 8, -1):
            b = bp.get(x, y, -1)
            if (x, y, -1) in S.bow and b not in (None, AIR, "minecraft:water") and bp.get(x, y + 1, -1) in (AIR, None):
                land = (x, y)
                break
        if land:
            break
    if land:
        lx, ly = land
        x0 = 1
        for x in range(x0, lx):
            t = (x - x0) / max(1, lx - x0)
            yf = DECK + (ly - DECK) * t
            yb = int(math.floor(yf))
            half = yf - yb >= 0.5
            for z in (-2, -1, 0):
                if bp.get(x, yb, z) in (None, AIR):
                    S.set(x, yb, z, IRON if not half else IRON)
                if half and bp.get(x, yb + 1, z) in (None, AIR):
                    S.set(x, yb + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
                for yy in range(yb + 1 + (1 if half else 0), yb + 4):
                    if bp.get(x, yy, z) is None:
                        S.air(x, yy, z)
            if x in (x0 + 3, lx - 3):
                for y in range(top + 1, yb):
                    if bp.get(x, y, -3) is None:
                        S.set(x, y, -3, IRON_WALL)
                    if bp.get(x, y, 1) is None:
                        S.set(x, y, 1, IRON_WALL)
            if (x - x0) % 2 == 0 and bp.get(x, yb + 1, -3) is None:
                S.set(x, yb + 1, -3, f"{RAIL}[facing=north]")
    # the debris stair from the islet up to the bow's broken-end door
    door = ri(bow_world(S_BOW0 - S_BOW0 + 3.0, MID_H + 1.0, 0.0))
    dx_, dy_, dz_ = door
    fy = None
    for y in range(dy_ + 2, dy_ - 4, -1):
        if bp.get(dx_, y, dz_) in (AIR, "minecraft:water") and bp.get(dx_, y - 1, dz_) not in (None, AIR,
                                                                                                "minecraft:water"):
            fy = y
            break
    if fy is not None:
        x = dx_ - 1
        y = fy
        while y > top + 1 and x > 0:
            y -= 1
            for z in (dz_ - 1, dz_, dz_ + 1):
                S.set(x, y, z, stair(IRON_BR_ST, "east"))
                for yy in range(y + 1 - 0, y + 4):
                    if bp.get(x, yy, z) in (None,):
                        S.air(x, yy, z)
                for yy in range(top + 1, y):
                    if bp.get(x, yy, z) is None:
                        S.set(x, yy, z, "andesite" if hash3(x, yy, z, 83) < 0.5 else IRON)
            x -= 1
        # the landing in front of the door
        for z in (dz_ - 1, dz_, dz_ + 1):
            for xx in range(x + 1, dx_):
                if bp.get(xx, fy - 1, z) in (None, AIR, "minecraft:water"):
                    pass


def breach(S):
    """The way in from the sea. The lower deck's broken end is closed by a patched bulkhead with an airlock in it: a
    short iron vestibule with a pair of doors at each end (a door holds the sea back, so the crew quarters stay dry
    at any depth and nothing is a still wall of water), its brass collar lit by sea lanterns so it reads from afar
    and from under the surface. A ladder hung with chains runs down the broken hull from the main deck to the
    vestibule's sill: a diver coming from the surface (deep water drowns the islet) follows it down to the door. The
    torn mess bulkhead gets glass in its holes."""
    bp = S.bp
    water = "minecraft:water"
    xb, y0, y1 = 1, LF - 1, MF - 2                       # bulkhead x, y 22 (sill) .. 27 (under the middle deck)
    # the air left forward of the bulkheads would be a dry pocket open to the sea: it goes
    for p in list(S.inner):
        x, y, z = p
        if (x > xb and LF <= y <= MF - 2) or (x > X_FWD and MF - 1 <= y <= DECK - 2):
            if bp.get(*p) == AIR:
                bp.remove(*p)
                S.inner.discard(p)
    for z, y in ((-4, MF + 1), (3, MF + 1), (4, MF + 2), (-12, MF + 2)):
        S.set(X_FWD, y, z, "glass")
    # the patched bulkhead
    for y in range(y0, y1 + 1):
        rr = max(zr(0, y), zr(xb, y)) + 1
        for z in range(-rr, rr + 1):
            h = hash3(xb, y, z, 151)
            spec = IRON_BR if (y - KEEL) % 6 == 0 or abs(z) >= rr - 1 or z % 7 == 3 else (RUST if h < 0.18 else IRON)
            S.set(xb, y, z, spec)
            S.inner.discard((xb, y, z))
        for z in (-rr, rr):                              # the hull plating's torn edge meets it
            if bp.get(xb - 1, y, z) in (None, AIR):
                S.set(xb - 1, y, z, IRON_BR)
    # the vestibule: x 2..4, z -2..1, floor y 22, air y 23..25, roof y 26; doors at x 1 and x 4 (z -1, 0)
    for x in range(xb + 1, xb + 4):
        for z in range(-2, 2):
            S.set(x, y0, z, TREAD)
            S.set(x, y0 + 4, z, IRON_BR if (x + z) % 3 else BRASS)
            for y in range(y0 + 1, y0 + 4):
                if z in (-2, 1):
                    S.set(x, y, z, BRASS if x == xb + 3 else (IRON_BR if y == y0 + 1 else IRON))
                else:
                    S.air(x, y, z)
            yy = y0 - 1
            while yy >= y0 - 4 and bp.get(x, yy, z) in (None, AIR, water):
                S.set(x, yy, z, IRON)                    # the vestibule stands on the islet's rock
                yy -= 1
    for x in (xb, xb + 3):
        for z, hinge in ((-1, "left"), (0, "right")):
            bp.door(x, LF, z, "east", wood="spruce", hinge=hinge)
            S.inner.update({(x, LF, z), (x, LF + 1, z)})
        for z in (-1, 0):
            S.set(x, LF + 2, z, BRASS)                   # the lintel
    S.set(xb + 3, y0 + 4, -2, "sea_lantern")
    S.set(xb + 3, y0 + 4, 1, "sea_lantern")
    S.set(xb + 1, y0 + 4, -1, "sea_lantern")
    S.set(xb + 4, y0 + 4, -2, BRASS_STAIRS + "[facing=west,half=top,shape=straight,waterlogged=false]")
    S.set(xb + 4, y0 + 4, 1, BRASS_STAIRS + "[facing=west,half=top,shape=straight,waterlogged=false]")
    # the landing in front of the outer doors and under the ladder: the islet's rock, raised where it dips
    for x in range(xb + 1, xb + 7):
        for z in range(-6, 3):
            if xb + 1 <= x <= xb + 3 and -2 <= z <= 1:
                continue
            if bp.get(x, y0, z) in (None, AIR, water):
                S.set(x, y0, z, "andesite" if hash3(x, y0, z, 153) < 0.5 else "cobblestone")
                for yy in range(y0 - 1, y0 - 4, -1):
                    if bp.get(x, yy, z) in (None, AIR, water):
                        S.set(x, yy, z, "andesite")
            for y in range(y0 + 1, y0 + 4):
                if x > xb + 3 and -1 <= z <= 0 and bp.get(x, y, z) not in (None, AIR, water):
                    bp.remove(x, y, z)                   # nothing in front of the outer doors
    # the ladder down the broken hull: an iron stile at x 1, the ladder on its east face, chains beside it
    lz = -5
    for y in range(y1 + 1, DECK + 1):
        S.set(xb, y, lz, IRON_BR if y % 3 == 0 else IRON)
    for y in range(LF, DECK + 1):
        wet = "true" if y <= SEA else "false"
        S.set(xb + 1, y, lz, f"ladder[facing=east,waterlogged={wet}]")
        for cz in (lz - 1, lz + 1):
            if bp.get(xb + 1, y, cz) in (None, AIR, water):
                S.set(xb + 1, y, cz, f"iron_chain[axis=y,waterlogged={wet}]")
    for cz in (lz - 1, lz + 1):
        if bp.get(xb, DECK, cz) in (None, AIR, water):
            S.set(xb, DECK, cz, IRON)
        S.set(xb + 1, DECK + 1, cz, IRON_WALL)           # the davit posts the chains hang from
    S.set(xb + 1, DECK + 2, lz - 1, LANT)
    S.set(xb + 1, DECK + 2, lz + 1, IRON_WALL)
    S.set(xb + 1, DECK + 3, lz + 1, LANT)


def bed_bow(S):
    """The bow, driven nose-first into the reef, sits bedded in the sand it ploughed up: no pocket of open sea is
    left trapped between its keel and the sea floor."""
    high = {}
    for (x, y, z) in S.bow:
        if S.bp.get(x, y, z) not in (None, AIR, "minecraft:water") and y > high.get((x, z), -99):
            high[(x, z)] = y
    for (x, z), yh in high.items():
        for y in range(1, min(yh, 6)):
            if S.bp.get(x, y, z) is None:
                S.set(x, y, z, "sand" if hash01(x * 3 + y, z, 161) < 0.8 else "gravel")


# ------------------------------------------------------------------ final passes
def drop_outside_air(S):
    """Air written outside the hull and the superstructures would dig a dry hole in the sea: drop it."""
    for p, b in list(S.bp.blocks.items()):
        if b[0] == AIR and p not in S.inner:
            S.bp.remove(*p)


def lights_main_path(S):
    """Edison lamps on the bulwarks along the port side of the main deck (the route at night)."""
    for x in range(-90, -6, 8):
        z = -zr(x, DECK)
        if S.get(x, DF, z) not in (None, AIR):
            S.set(x, DF + 1, z, EDISON) if S.get(x, DF + 1, z) is None else None


def dreadnought_wreck(bp):
    S = Wreck(bp)
    stern_hull(S)
    stern_layout(S)
    crew_quarters(S)
    officers_mess(S)
    magazine(S)
    vault(S)
    arena(S)
    engine_room(S)
    middle_aft(S)
    captain(S)
    steering_flat(S)
    deckhouse(S)
    for fx, top in zip(FUNNELS, (DF + 28, DF + 25)):
        funnel(S, fx, top)
    funnel(S, F2, DF + 4, standing=False)
    fallen_funnel(S)
    bridge_tower(S)
    turret_access(S)
    deck_details(S)
    lights_main_path(S)
    bow(S)
    reef(S)
    bed_bow(S)
    gap(S)
    breach(S)
    drop_outside_air(S)


# camera spots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("crew_quarters", (-1, LF, 5), (-14, LF + 1, -5)),
    ("officers_mess", (-3, MF, 6), (-15, MF + 1, -2)),
    ("bridge", (-7, B2, 0), (40, DF - 4, 4)),
    ("captain_cabin", (-87, MF, 3), (-95, MF + 1, -1)),
    ("engine_room", (-71, LF, 0), (-82, LF - 2, 9)),
    ("boiler_hall", (-55, HF, 0), (-20, HF + 6, 0)),
    ("magazine", (-8, HF, 0), (-2, HF + 1, -10)),
]


register(StructureDef(
    "dreadnought_wreck", "overworld", ["warm_ocean", "lukewarm_ocean", "deep_lukewarm_ocean", "deep_ocean"],
    [Piece("wreck", dreadnought_wreck, views=VIEWS)],
    spacing=80, separation=32, heightmap="OCEAN_FLOOR_WG", adaptation="none", processors="none", max_distance=116,
    foundation=False, spawns=[(MOB_DROWNED, 6, 1, 2), (MOB_KNIGHT, 2, 1, 1), (MOB_WRAITH, 3, 1, 2)],
    title_fr="Épave du cuirassé Léviathan", title_en="Leviathan Dreadnought Wreck"))
