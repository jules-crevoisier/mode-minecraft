"""The Icebound Fleet (La Flotte prise dans les glaces): a polar expedition frozen into the pack ice, ~215 blocks across
in frozen oceans, ice spikes, snowy plains and snowy beaches. Colossal tier (tools/BUILDING.md §1, §12 concept 26,
§10 legacy-dungeon template, §15), steampunk (tools/STYLE_STEAMPUNK.md: dark iron hull, copper funnels, brass trim,
timber supply ships, amber lamps against blue ice).

Silhouette (one noun phrase, §15.1): a colossal dark-iron paddle icebreaker locked in the ice with a list to
starboard, its two fat copper funnels leaning, its raked ram bow ridden up on a pressure ridge, beside two small
timber supply ships, a brass drilling derrick and blue ice spires.

Placement: fit mode ``wetland`` (the frozen sea surface counts as ground): blueprint y = 0 is the sea surface, which
the template turns into pack ice (snow, packed ice, blue ice) one layer deep over the water, two where it matters.
Everything below y = 0 that is walked in is a sealed pocket (``seal``: every air cell under the ice gets solid
neighbours), so the hulls and the trench stay dry while the sea fills the rest of the hulls (flooded holds).

Layout (x east, z south, y up; ice surface y 0, feet 1):
  * the approach (south-east): the sledge camp and its waystone, a trodden track over the ice under the spine of a
    frozen-over whale skeleton (a broken rib leaves the gap), through a gap in a pressure ridge (the reveal of the
    icebreaker beyond) to the drilling camp (the hub, waystone): the brass ice-drill derrick over its borehole, the
    engine house, the lab hut, the mess tent, the bunk hut, the sledge depot;
  * the supply ship Fulmar (south): gangway, companion, the 'tween deck stores, the frozen hold (below the ice), the
    chart room under the poop, the poop deck and a sagging rope bridge to the supply ship Petrel: the kennels in its
    forecastle, the galley (waystone) and berths on its 'tween deck, the ice door (opens from inside only);
  * the snow trench from the Petrel to the icebreaker's starboard flank, sinking under the ice to a breach the
    pressure crushed into the aft coal bunker;
  * the icebreaker (120 long, keel 13 under the ice): the boiler room (a 27-high hall: four boilers, the paddle
    shaft, galleries), the crew mess (waystone; the one-way hatch to the starboard side deck and its gangway), the
    officers' mess, the captain's cabin; out on the boat deck, up the newel stair inside the forward funnel, over the
    gantry to the wheelhouse roof and down its hatch into the wheelhouse (site of grace); the enclosed bridge stair
    (compression, the mist at its foot) to the boss arena on the forecastle deck under the bridge front;
  * behind the sealed hatch on the bow, the expedition strongroom, and the ice slide out of the ram's breach back
    down to the ice by the drilling camp.
Optional: the derrick's crown platform, the whale's ribcage, the Fulmar's bosun's locker, the Petrel's
quartermaster's store and crow's nest, the icebreaker's port coal bunker, boiler-room floor, crew cabins, aft deck
(mainmast crow's nest, engineers' quarters) and the cargo crane, whose jib drops into a fishing hole by the trench.
Loot gradient (§15.6): camp, whale, hub tier 1; supply ships 1-2; bunkers, crew 2; officers, captain, crow's nests 2-3;
strongroom 3+.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_STAIRS, PIPES, SMOKE, TABLE,
                       TREAD, TREAD_SLAB, TREAD_STAIRS, VERD, W, fbm, hash01, hash3, vnoise)
from ..parts import LOOT, MOD
from .airship_graveyard import Ctx, newel_laps, write_steps

# no boss of its own yet: the Gryphon Knight (a flier) holds the open forecastle under the bridge
BOSS = "brasshaven:gryphon_knight"
MOB_STRAY = "minecraft:stray"
MOB_DRONE = W + "steam_drone"
MOB_GUNNER = W + "boiler_gunner"
MOB_MITE = W + "rust_mite"
MOB_SPIDER = W + "clockwork_spider"

AIR = "minecraft:air"
WATER = "water[level=0]"
SNOW = "snow_block"
PICE = "packed_ice"
BICE = "blue_ice"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
IRON_BR = W + "dark_iron_bricks"
RUST = W + "rust_rock"
SOOT = W + "sooty_smokestack_bricks"
PARQUET = W + "mahogany_parquet"
GRILLE = W + "brass_grille"
RAIL = W + "brass_railing"
VALVE = W + "valve_wheel"
COG = W + "wall_cog"
SHELF = W + "wall_shelf"
CHAIR = W + "mahogany_chair"
COPPER_ST = W + "copper_plating_stairs"
SPRUCE = "spruce_planks"
DOAK = "dark_oak_planks"
DIRV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def log(spec, axis):
    return f"{spec}[axis={axis}]"


# ------------------------------------------------------------------ small helpers
def lamp(C, x, y, z, drop=1, spec=HANG_LAMP):
    """A lamp hanging ``drop`` chain links under the ceiling block above y + drop."""
    for k in range(drop):
        C.set(x, y + 1 + k, z, CHAIN)
    C.set(x, y, z, spec)


def door(C, x, y, z, facing, wood="spruce", hinge="left"):
    C.bp.door(x, y, z, facing, wood=wood, hinge=hinge)


def rail(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def clear(C, x0, x1, y0, y1, z0, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(y0, y1 + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                C.air(x, y, z)


def box(C, x0, x1, y0, y1, z0, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(y0, y1 + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def steps(cells, x, z, d, n, f0, w=3, side=None):
    """n steps climbing toward ``d`` from (x, z): step i stands at feet f0 + 1 + i (bottom landing at feet f0
    before it, top landing at f0 + n after it); ``w`` wide toward ``side`` (default +z / +x)."""
    dx, dz = DIRV[d]
    sx, sz = DIRV[side] if side else ((0, 1) if dx else (1, 0))
    for i in range(n):
        for k in range(w):
            cells[(x + dx * i + sx * k, z + dz * i + sz * k)] = (f0 + 1 + i, d)


def land(cells, x0, x1, z0, z1, f):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            cells[(x, z)] = (f, None)


def box_room(C, x0, x1, z0, z1, yf, yc, wall, floor=None, ceil=None):
    """A world-aligned room: walls on the box edges from yf to yc, floor at yf, ceiling at yc, air inside."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(yf, yc + 1):
                if y == yf:
                    if floor:
                        C.set(x, y, z, floor(x, y, z) if callable(floor) else floor)
                elif y == yc:
                    if ceil:
                        C.set(x, y, z, ceil(x, y, z) if callable(ceil) else ceil)
                elif edge:
                    C.set(x, y, z, wall(x, y, z) if callable(wall) else wall)
                else:
                    C.air(x, y, z)


def gable(C, x0, x1, z0, z1, y, stairs, ridge="x", fill=SPRUCE, cap=SNOW):
    """A pitched roof (stairs, the gable ends filled), overhang 1, a snow ridge."""
    if ridge == "x":
        w = z1 - z0 + 3
        for k in range((w + 1) // 2):
            for x in range(x0 - 1, x1 + 2):
                for z, fc in ((z0 - 1 + k, "south"), (z1 + 1 - k, "north")):
                    if z0 - 1 + k > z1 + 1 - k:
                        continue
                    if z0 - 1 + k == z1 + 1 - k:
                        C.set(x, y + k, z, cap)
                    else:
                        C.set(x, y + k, z, stair(stairs, fc))
            for x in (x0, x1):
                for z in range(z0 + k, z1 - k + 1):
                    if C.empty(x, y + k, z):
                        C.set(x, y + k, z, fill)
    else:
        w = x1 - x0 + 3
        for k in range((w + 1) // 2):
            for z in range(z0 - 1, z1 + 2):
                for x, fc in ((x0 - 1 + k, "east"), (x1 + 1 - k, "west")):
                    if x0 - 1 + k > x1 + 1 - k:
                        continue
                    if x0 - 1 + k == x1 + 1 - k:
                        C.set(x, y + k, z, cap)
                    else:
                        C.set(x, y + k, z, stair(stairs, fc))
            for z in (z0, z1):
                for x in range(x0 + k, x1 - k + 1):
                    if C.empty(x, y + k, z):
                        C.set(x, y + k, z, fill)


# ------------------------------------------------------------------ hulls
class Hull:
    """A ship's hull in a rolled frame: u along the ship from the stern tip, v across (+ starboard = +z), h up
    (h 0 = the ice surface before the roll). ``tops``: [(u_from, deck surface h)] (the last matching entry wins)."""

    def __init__(self, xs, length, zc, hb, keel, tops, roll=0.0, stem_rake=0.75, stern_rake=0.35, taper=0.73,
                 stern_round=12.0, hmax=5.0, bottom=0.5, bluff=1.8):
        self.xs, self.L, self.zc, self.hb, self.keel = xs, length, zc, hb, keel
        self.tops = tops
        self.tmax = max(t for _, t in tops)
        r = math.radians(roll)
        self.sr, self.cr = math.sin(r), math.cos(r)
        self.stem_rake, self.stern_rake = stem_rake, stern_rake
        self.ut = length * taper
        self.stern_round, self.hmax, self.bottom, self.bluff = stern_round, hmax, bottom, bluff
        self.deckn = {}

    def top(self, u):
        t = self.tops[0][1]
        for u0, h in self.tops:
            if u >= u0:
                t = h
        return t

    def local(self, x, y, z):
        dz = z - self.zc
        return x - self.xs, dz * self.cr - y * self.sr, dz * self.sr + y * self.cr

    def hw(self, u, h):
        if h < self.keel - 0.5:
            return 0.0
        sec = 1.0 if h >= self.hmax else 1 - self.bottom * ((self.hmax - h) / (self.hmax - self.keel)) ** 2
        a = max(0.0, self.tmax - h) * self.stern_rake
        b = self.L - max(0.0, self.tmax - h) * self.stem_rake
        if u < a or u > b:
            return 0.0
        f = 1.0
        ua = u - a
        if ua < self.stern_round:
            f = math.sqrt(max(0.0, 1 - ((self.stern_round - ua) / self.stern_round) ** 2))
        if u > self.ut and b > self.ut:
            t = min(1.0, (u - self.ut) / (b - self.ut))
            f *= max(0.0, 1 - t ** self.bluff) ** 0.55
        return self.hb * sec * f

    def inside(self, x, y, z, margin=1.0):
        u, v, h = self.local(x, y, z)
        return self.keel + 1.0 < h < self.top(u) - 1.5 and abs(v) < self.hw(u, h) - margin

    def plan(self, x, z, h=2.0):
        """Within the hull's outline at local height h (no roll correction: for the seal and keep-outs)."""
        return abs(z - self.zc) <= self.hw(x - self.xs, h) + 0.5

    def feet(self, x, z):
        """Deck feet (float, half steps) of a deck column, or None."""
        return self.deckn.get((x, z))


def build_hull(C, S, plate, deck_block, deck_slab, under=IRON, cap=BRASS, bul_h=2):
    """Shell plating (``plate(u, v, h, x, y, z)``), the bulwark band ``bul_h`` above the deck, and the deck surface of
    each column: full blocks, with a bottom slab where the rolled deck plane sits half way (walkable half steps)."""
    x0, x1 = S.xs - 1, S.xs + S.L + 1
    z0, z1 = int(math.floor(S.zc - S.hb - 3)), int(math.ceil(S.zc + S.hb + 3))
    ytop = int(S.tmax + bul_h + 3)
    for x in range(x0, x1 + 1):
        u = x - S.xs
        T = S.top(u)
        for z in range(z0, z1 + 1):
            for y in range(S.keel - 3, ytop):
                _, v, h = S.local(x, y, z)
                if h < S.keel - 0.5 or h > T + bul_h + 0.5:
                    continue
                w = S.hw(u, min(h, T - 0.5))
                if w <= 0:
                    continue
                a = abs(v)
                if a > w + 0.4:
                    continue
                if h >= T - 0.5:
                    if a > w - 1.0:
                        C.set(x, y, z, cap if h >= T + bul_h - 0.5 else plate(u, v, h, x, y, z))
                    continue
                if a > w - 1.2 or h < S.keel + 0.5:
                    C.set(x, y, z, plate(u, v, h, x, y, z))
            yt = (T - (z - S.zc) * S.sr) / S.cr
            _, v, _ = S.local(x, yt - 0.5, z)
            w = S.hw(u, T - 0.5)
            if w <= 0 or abs(v) > w - 1.0:
                continue
            n = math.floor(yt * 2 + 0.5) / 2.0
            fy = int(math.floor(n))
            if n == fy:
                C.set(x, fy - 1, z, deck_block(x, z))
                C.set(x, fy - 2, z, under)
            else:
                C.set(x, fy, z, deck_slab(x, z))
                C.set(x, fy - 1, z, deck_block(x, z))
                C.set(x, fy - 2, z, under)
            S.deckn[(x, z)] = n


def hroom(C, S, x0, x1, z0, z1, f, hgt, wall, floor, ceil=None, line=None, margin=1.2):
    """A room inside a hull: box edges are walls, floor at f - 1, air f .. f + hgt - 1, ceiling at f + hgt; cells
    near the curved shell get the lining (``line``), cells beyond the shell are left to the hull."""
    sp = lambda s, x, y, z: s(x, y, z) if callable(s) else s  # noqa: E731
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(f - 1, f + hgt + 1):
                if y == f + hgt and ceil is None:
                    continue
                if not S.inside(x, y, z, 0.0):
                    continue
                if y == f - 1:
                    C.set(x, y, z, sp(floor, x, y, z))
                elif y == f + hgt:
                    C.set(x, y, z, sp(ceil, x, y, z))
                elif edge:
                    C.set(x, y, z, sp(wall, x, y, z))
                elif S.inside(x, y, z, margin):
                    C.air(x, y, z)
                else:
                    C.set(x, y, z, sp(line or wall, x, y, z))


def bulkhead(C, S, x, y0, y1, spec, zr=None):
    """A transverse wall across a hull at x (the breaks of forecastles and poops)."""
    z0, z1 = zr or (int(S.zc - S.hb - 1), int(S.zc + S.hb + 1))
    for z in range(z0, z1 + 1):
        for y in range(y0, y1 + 1):
            if S.inside(x, y, z, 0.0):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def portholes(C, S, x0, x1, y, every=4, glass="glass"):
    """Portholes in both flanks at height y: the shell cells outward of the room air become glass."""
    for x in range(x0, x1 + 1, every):
        for sgn in (-1, 1):
            z = int(round(S.zc))
            found = False
            for k in range(int(S.hb) + 4):
                zz = z + sgn * k
                b = C.get(x, y, zz)
                if b == AIR:
                    found = True
                    continue
                if found and b is not None:
                    u, v, h = S.local(x, y, zz)
                    if abs(v) > S.hw(u, h) - 2.6:
                        C.set(x, y, zz, glass)
                        z2 = zz + sgn
                        if C.get(x, y, z2) is not None and C.get(x, y, z2) != AIR and \
                                abs(S.local(x, y, z2)[1]) <= S.hw(u, h) + 0.4:
                            C.set(x, y, z2, glass)
                    break


def mast(C, S, x, z0, y0, y1, spec=log("spruce_log", "y"), yards=(), sail=True, top=None):
    """A mast leaning with the hull's roll, yards across with furled frozen sails."""
    tan = S.sr / S.cr
    for y in range(y0, y1 + 1):
        z = int(round(z0 + (y - y0) * tan))
        C.set(x, y, z, spec)
    for (y, half) in yards:
        z = int(round(z0 + (y - y0) * tan))
        for k in range(-half, half + 1):
            C.set(x, y, z + k, log("stripped_spruce_log", "z"))
            if sail and abs(k) < half and abs(k) > 0:
                C.set(x, y - 1, z + k, "white_wool" if hash01(x + k, y, 11) < 0.7 else "light_gray_wool")
                if hash01(x + k, y, 12) < 0.4:
                    C.set(x, y - 2, z + k, SNOW if hash01(k, y, 13) < 0.3 else "white_wool")
        C.set(x, y + 1, z - half, SNOW)
    if top:
        z = int(round(z0 + (y1 + 1 - y0) * tan))
        C.set(x, y1 + 1, z, top)


# ------------------------------------------------------------------ palettes
def ib_plate(u, v, h, x, y, z):
    """The icebreaker's shell: dark iron strakes with seams, a copper-and-verdigris ice belt round the ice line,
    rust streaks under the hawse and the portholes, a brass knife on the stem."""
    if u > IB.L - (IB.tmax - h) * IB.stem_rake - 2.2 and abs(v) < 3:
        return BRASS if h > -3 else IRON
    if h < -3.5:
        return IRON if hash3(x, y, z, 1) < 0.75 else RUST
    if h < 2.5:
        n = vnoise(u * 0.6, h * 0.8 + v * 0.1, 3.0, 7)
        return VERD if n < 0.38 else COPPER if n < 0.8 else RUST
    T = IB.top(u)
    if T - 3.4 <= h < T - 2.6:
        return BRASS
    k = int(math.floor(h)) // 3
    if (int(u) + 4 * k) % 9 == 0:
        return IRON_BR
    if hash3(x // 2, y, z, 3) < 0.05 + 0.1 * max(0.0, 1 - abs(h - 5) / 5):
        return RUST
    return IRON


def wood_plate(band):
    def fn(u, v, h, x, y, z):
        if h < 2.0:
            if h < -2.5:
                return DOAK
            return COPPER if hash3(x, y, z, 21) < 0.7 else VERD
        if 3.0 <= h < 4.0:
            return log("stripped_dark_oak_log", "x")
        if 5.0 <= h < 6.0:
            return band
        return SPRUCE if int(math.floor(h)) % 2 else DOAK
    return fn


def ib_deck(x, z):
    u = x - XS
    if u >= FC_U:
        d = math.hypot(u - AC[0], z - ZC)
        if 9.5 <= d < 10.5:
            return BRASS
        if d < 2.5:
            return GEAR
        return TREAD
    return SPRUCE if (x % 7) else DOAK


def ib_deck_slab(x, z):
    u = x - XS
    if u >= FC_U:
        d = math.hypot(u - AC[0], z - ZC)
        return slab(BRASS_SLAB) if 9.5 <= d < 10.5 else slab(TREAD_SLAB)
    return slab("spruce_slab")


# ------------------------------------------------------------------ dimensions
XS, LEN, ZC, HB = -80, 120, -40, 16      # the icebreaker: stern tip x, length, centre line z, half beam
KEEL = -13
MAIN_T, FC_T = 11.5, 14.5                # deck surfaces (local h): main deck, forecastle deck
FC_U = 74                                # the forecastle starts here
ROLL = 4.0                               # list to starboard
AC = (89, 0)                             # arena centre (u, v)
IB = Hull(XS, LEN, ZC, HB, KEEL, [(0, MAIN_T), (FC_U, FC_T)], roll=ROLL, stem_rake=0.75, stern_rake=0.35,
          taper=0.73, stern_round=12, hmax=5, bottom=0.5, bluff=1.8)
F1U, F2U, FR = 33, 50, 8                 # funnels (u), radius
FTOP = 58
PADU, PADR = 41.5, 10                    # paddle wheels: centre u, radius (axle at local h PADH)
PADH = 2.0
BD = 17                                  # boat deck plating y (feet 18)

# supply ships (timber hulls)
SB = Hull(-24, 54, 32, 9, -7, [(0, 13.5), (13, 7.5), (44, 13.5)], roll=-4.0, stem_rake=0.6, stern_rake=0.25,
          taper=0.67, stern_round=8, hmax=3, bottom=0.5, bluff=1.6)
SA = Hull(-96, 56, 36, 9, -7, [(0, 13.5), (13, 7.5), (44, 13.5)], roll=5.0, stem_rake=0.6, stern_rake=0.25,
          taper=0.67, stern_round=8, hmax=3, bottom=0.5, bluff=1.6)

HUB = (40, 14)
DER = (56, 0)
CAMP = (86, 80)
WHALE_C = (64, 49)


def X(u):
    return XS + int(math.floor(u))


def Z(v):
    return ZC + int(math.floor(v))


# ------------------------------------------------------------------ the pack ice
def field_e(x, z):
    return (x / 108.0) ** 2 + (z / 100.0) ** 2


def in_field(x, z):
    t = max(0.0, min(1.0, ((x - CAMP[0]) * -14 + (z - CAMP[1]) * -16) / 452.0))
    if math.hypot(x - CAMP[0] + 14 * t, z - CAMP[1] + 16 * t) < 12 + (hash01(x, z, 7) - 0.5) * 2:
        return True               # the camp's tongue of ice
    return field_e(x, z) <= 1.0 + (fbm(x, z, 14.0, 3) - 0.5) * 0.16


def ice_field(C):
    for x in range(-112, 113):
        for z in range(-104, 105):
            if not in_field(x, z):
                continue
            n = fbm(x, z, 9.0, 5)
            h = hash01(x, z, 6)
            if n > 0.66:
                top = PICE
            elif n < 0.24:
                top = PICE if h < 0.6 else BICE
            elif h < 0.03:
                top = BICE
            else:
                top = SNOW
            C.set(x, 0, z, top)
            C.set(x, -1, z, PICE if h < 0.5 else "ice")


def lead(C, pts, half=1.2, seed=0):
    """An open lead: a crack of black water through the ice, wandering, two blocks deep at least."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 2))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            w = half * (0.6 + 0.9 * vnoise(px, pz, 4.0, seed))
            for x in range(int(px - w) - 1, int(px + w) + 2):
                for z in range(int(pz - w) - 1, int(pz + w) + 2):
                    if math.hypot(x - px, z - pz) > w or not in_field(x, z) or keep_out(x, z, 0):
                        continue
                    C.set(x, 0, z, WATER)
                    C.set(x, -1, z, WATER)
                    if hash01(x, z, seed + 1) < 0.08:
                        C.set(x, 0, z, PICE)      # a floe


def keep_out(x, z, m=3):
    """Ships, camps and the paths: no ridge, spire or lead here."""
    for S in (IB, SB, SA):
        if S.xs - m - 2 <= x <= S.xs + S.L + m + 2 and abs(z - S.zc) <= S.hb + m + (7 if S is IB else 2):
            return True
    for (cx, cz, r) in KEEP:
        if math.hypot(x - cx, z - cz) <= r + m:
            return True
    for pts, half in PATHS:
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            dx, dz = bx - ax, bz - az
            L2 = dx * dx + dz * dz
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L2))
            if math.hypot(x - ax - t * dx, z - az - t * dz) <= half + m:
                return True
    return False


KEEP = [(HUB[0], HUB[1], 22), (DER[0], DER[1], 14), (CAMP[0], CAMP[1], 12), (WHALE_C[0], WHALE_C[1], 18),
        (30, -20, 12), (-62, 0, 12), (-12, -14, 9), (-58, -10, 6)]
PATHS = [
    ([CAMP, (78, 70), (70, 58), (64, 49), (57, 41), (52, 36), (46, 27), (41, 18)], 1.8),
    ([(34, 18), (20, 20), (3, 20)], 1.7),
    ([(28, -8), (34, 0), (40, 8)], 1.6),
    ([(-11, -21), (6, -12), (22, -2), (34, 8)], 1.6),
    ([(-66, 25), (-66, 2), (-65, -10), (-62, -18), (-61, -24)], 1.8),
]


def path_line(C, pts, half=1.7, seed=31):
    """A trodden track over the ice: packed snow and sledge-worn packed ice, cleared three high."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 2))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            w = half + (vnoise(px, pz, 5.0, seed) - 0.5) * 0.8
            for x in range(int(px) - 3, int(px) + 4):
                for z in range(int(pz) - 3, int(pz) + 4):
                    if math.hypot(x - px, z - pz) > w:
                        continue
                    b = C.get(x, 0, z)
                    if b in ("minecraft:" + SNOW, "minecraft:" + PICE, "minecraft:" + BICE):
                        hh = hash01(x, z, seed + 1)
                        C.set(x, 0, z, "white_concrete_powder" if hh < 0.45 else PICE if hh < 0.8 else
                              "light_gray_concrete_powder")
                        for y in (1, 2, 3):
                            if C.get(x, y, z) is None:
                                C.air(x, y, z)


def ridge(C, pts, hmax, seed, gaps=()):
    """A pressure ridge: a jagged wall of tilted ice slabs heaped where two floes met (packed ice, blue ice at the
    sheared cores, snow on the windward crest)."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 1.5))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            if any(math.hypot(px - gx, pz - gz) < gr for gx, gz, gr in gaps):
                continue
            H = hmax * (0.45 + 0.55 * fbm(px, pz, 7.0, seed))
            w = 2.0 + H * 0.45
            for x in range(int(px - w) - 1, int(px + w) + 2):
                for z in range(int(pz - w) - 1, int(pz + w) + 2):
                    d = math.hypot(x - px, z - pz)
                    if d > w or keep_out(x, z, 1) or not in_field(x, z):
                        continue
                    hh = H * (1 - (d / w) ** 1.4) + (hash01(x, z, seed + 3) - 0.5) * 2.6
                    top = int(hh)
                    for y in range(1, top + 1):
                        if C.get(x, y, z) is not None:
                            continue
                        k = hash3(x, y, z, seed + 4)
                        C.set(x, y, z, BICE if (d < 1.2 and k < 0.6) else SNOW if (y == top and k < 0.35)
                              else PICE)


def spire(C, cx, cz, r, h, lean, seed):
    """A blue packed-ice spire (a serac): faceted, banded, leaning a little, its foot buried in a drift."""
    lx, lz = lean
    for y in range(1, h + 1):
        t = y / h
        rr = r * (1 - t) ** 0.85 + 0.4
        ox, oz = cx + lx * t * h / 10.0, cz + lz * t * h / 10.0
        for x in range(int(ox - rr) - 2, int(ox + rr) + 3):
            for z in range(int(oz - rr) - 2, int(oz + rr) + 3):
                a = math.atan2(z - oz, x - ox)
                facet = 1 + 0.18 * math.cos(5 * a + seed) + 0.12 * (hash01(int(a * 3), y // 3, seed) - 0.5)
                d = math.hypot(x - ox, z - oz) / facet
                if d > rr:
                    continue
                band = (y + int(3 * vnoise(x, z, 4.0, seed))) % 7
                C.set(x, y, z, BICE if band in (0, 1) or d < rr * 0.45 else PICE)
    for x in range(cx - r - 3, cx + r + 4):
        for z in range(cz - r - 3, cz + r + 4):
            d = math.hypot(x - cx, z - cz)
            if r < d < r + 3 and C.get(x, 1, z) is None and hash01(x, z, seed + 9) < 0.7:
                C.set(x, 1, z, SNOW)
                if d < r + 1.5 and C.get(x, 2, z) is None:
                    C.set(x, 2, z, PICE if hash01(x, z, seed + 10) < 0.5 else SNOW)


def drifts(C):
    """Snow drifts against the windward (north-west) faces of everything standing on the ice."""
    for x in range(-110, 111):
        for z in range(-102, 103):
            if C.get(x, 0, z) not in ("minecraft:" + SNOW, "minecraft:" + PICE) or C.get(x, 1, z) is not None:
                continue
            for dx, dz in ((1, 1), (1, 0), (0, 1)):
                b = C.get(x + dx, 1, z + dz)
                if b is not None and b != AIR and "snow" not in b and "ice" not in b and \
                        hash01(x, z, 61) < 0.55:
                    C.set(x, 1, z, SNOW)
                    break


# ------------------------------------------------------------------ the icebreaker: hull and decks
def icebreaker_hull(C):
    build_hull(C, IB, ib_plate, ib_deck, ib_deck_slab, under=IRON, cap=BRASS, bul_h=2)
    # the boot-top stripe: brass hawse pipes and anchors on the bow, a rudder at the stern
    for sgn in (-1, 1):
        for u in range(108, 112):
            for y in (10, 11):
                for z in range(int(ZC + sgn * 6), int(ZC + sgn * 13), sgn):
                    _, v, h = IB.local(X(u), y, z)
                    if abs(abs(v) - IB.hw(u, h)) < 0.8:
                        C.set(X(u), y, z, IRON_BR if (u, y) != (110, 10) else "iron_block")
                        break
    for y in range(-8, 6):
        C.set(X(-1), y, ZC, IRON)
        C.set(X(-2), y, ZC, IRON)
        C.set(X(-3), y, ZC, IRON_BR)
    C.set(X(-2), 6, ZC, BRASS)


def boiler_room(C):
    """The boiler room: 27 high from the hold floor to the boat deck. Four Scotch boilers (axis across) fire into a
    central stokehold aisle; their uptakes rise to the funnels; the paddle shaft crosses over the stokehold; side
    galleries at the lower-deck level, the starboard one carrying the main stair up to the crew mess."""
    x0, x1 = X(26), X(58)
    hroom(C, IB, x0, x1, Z(-11), Z(11), -10, 20, IRON_BR, TREAD, None, line=IRON)
    # the casing above the main deck (y 10..16) up to the boat deck
    for x in range(x0, x1 + 1):
        for z in range(Z(-11), Z(11) + 1):
            edge = x in (x0, x1) or z in (Z(-11), Z(11))
            for y in range(9, BD):
                if edge:
                    C.set(x, y, z, IRON_BR if (x - x0) % 8 else BRASS)
                else:
                    C.air(x, y, z)
            C.set(x, BD, z, IRON)
    # boilers: centres (u, side), radius 3.5, axis across from |v| 2 to 6
    for uc in (F1U, F2U):
        for sgn in (-1, 1):
            for v in range(2, 7):
                for du in range(-4, 5):
                    for y in range(-10, -2):
                        d = math.hypot(du, y + 6.5)
                        if d <= 3.6:
                            C.set(X(uc + du), y, Z(sgn * v), BRASS if v in (2, 6) and d > 2.6 else
                                  (COPPER if d > 2.8 else IRON))
            # the furnace front facing the aisle: two firedoors, gauges, a valve
            vf = sgn * 2
            C.set(X(uc - 1), -9, Z(vf), "furnace[facing=%s,lit=true]" % ("south" if sgn < 0 else "north"))
            C.set(X(uc + 1), -9, Z(vf), "blast_furnace[facing=%s,lit=true]" % ("south" if sgn < 0 else "north"))
            C.set(X(uc), -7, Z(vf), GAUGE)
            C.set(X(uc), -5, Z(vf), GAUGE)
            # short ducts from the boiler tops into the uptake
            for y in range(-3, 1):
                for v in range(3, 6):
                    C.set(X(uc), y, Z(sgn * v), SOOT)
        # the uptake trunk to the funnel, above head height over the aisle
        for x in range(X(uc - 2), X(uc + 2) + 1):
            for z in range(Z(-5), Z(5) + 1):
                for y in range(1, BD):
                    C.set(x, y, z, BRASS if y in (6, 12) else SOOT)
    # coal on the stokehold floor, shovels' heaps, the gratings
    for x in range(X(38), X(46) + 1):
        for z in range(Z(-1), Z(1) + 1):
            C.set(x, -11, z, GRILLE if (x + z) % 3 == 0 else TREAD)
    for (u, v) in ((39, -1), (45, 1), (44, -1)):
        C.set(X(u), -10, Z(v), "coal_block" if hash01(u, v, 3) < 0.5 else slab(W + "smokestack_brick_slab"))
    # the paddle shaft (rolled with the hull) and its crank over the aisle
    for x in range(X(40), X(44) + 1):
        for z in range(Z(-23), Z(23) + 1):
            for y in range(-1, 7):
                u, v, h = IB.local(x, y, z)
                if abs(v) > 22.5:
                    continue
                dd = math.hypot(u - PADU, h - (PADH + 1.0))
                if dd <= 1.1 or (abs(v) < 1.6 and dd <= 3.2 and abs(u - PADU) < 2.6):
                    C.set(x, y, z, IRON if dd <= 1.1 else GEAR)
    # galleries at the lower-deck level (feet -2): starboard (main), port, the forward cross catwalk
    for x in range(X(27), X(57) + 1):
        for v in list(range(6, 10)) + list(range(-9, -5)):
            C.set(x, -3, Z(v), TREAD)
            C.set(x, -4, Z(v), IRON)
        if X(54) <= x <= X(56):
            continue          # the cross catwalk joins here
        rail(C, x, -2, Z(6), "north")
        rail(C, x, -2, Z(-6), "south")
    for x in range(X(54), X(56) + 1):
        for v in range(-6, 7):
            C.set(x, -3, Z(v), TREAD)
            C.set(x, -4, Z(v), IRON)
    # the central stair from the cross catwalk down the aisle to the stokehold
    cells = {}
    # climbing east from the aisle (feet -10 at u 45) to the catwalk (feet -2 at u 54)
    land(cells, X(44), X(45), Z(-1), Z(1), -10)
    steps(cells, X(46), Z(-1), "east", 8, -10)
    wsteps(C, cells, solid_to=-11)
    # the main stair: starboard gallery up to the crew mess door (feet 5)
    cells = {}
    steps(cells, X(47), Z(8), "east", 7, -2, w=2)      # the gallery walk (v 7) passes beside it
    land(cells, X(54), X(57), Z(7), Z(9), 5)
    wsteps(C, cells)
    # lamps down from the boat deck, lanterns on the gallery rails
    for u in (30, 38, 46, 54):
        lamp(C, X(u), 9, Z(0) if u not in (F1U, F2U) else Z(8), drop=7)
    for u in (28, 36, 44, 52):
        C.set(X(u), -2, Z(-9), LANT)
        C.set(X(u), -2, Z(9), LANT) if u != 52 else None
    # pipes and gauges on the bulkheads
    for v in range(-8, 9, 4):
        for y in range(-9, 8):
            if C.get(X(27), y, Z(v)) == AIR:
                C.set(X(27), y, Z(v), PIPES)
    for v in (-4, 4):
        C.set(X(57), 1, Z(v), GAUGE)
        C.set(X(57), 2, Z(v), f"{VALVE}[facing=west]")
    # spawners: the stokers' ghosts in the aisle
    C.bp.spawner(X(41), -10, Z(-1), MOB_GUNNER)
    C.bp.spawner(X(43), -10, Z(1), MOB_GUNNER)
    C.bp.chest(X(28), -10, Z(-1), "east", loot=LOOT + "if_boiler")
    # door from the aft bunker (u 26) onto the starboard gallery; door from the landing into the crew mess (u 58)
    clear(C, X(26), X(26), -2, 0, Z(7), Z(9))
    clear(C, X(58), X(58), 5, 7, Z(7), Z(9))
    # the port wing bunker (optional): off the port gallery
    hroom(C, IB, X(36), X(46), Z(-15), Z(-10), -2, 5, IRON_BR, TREAD, IRON, line=IRON)
    clear(C, X(40), X(41), -2, 0, Z(-10), Z(-10))
    for x in range(X(37), X(46)):
        for z in range(Z(-14), Z(-10)):
            if C.get(x, -2, z) == AIR and hash01(x, z, 71) < 0.5:
                C.set(x, -2, z, "coal_block")
    C.bp.chest(X(44), -2, Z(-12), "north", loot=LOOT + "if_bunker")
    C.bp.spawner(X(38), -2, Z(-12), MOB_MITE)
    C.set(X(42), 2, Z(-12), HANG_LAMP)


def aft_bunker(C):
    """The aft coal bunker (lower deck, feet -2): heaps of coal, barrows, the chute from the deck; the breach the
    ice crushed into the starboard flank opens onto the snow trench."""
    hroom(C, IB, X(14), X(26), Z(-14), Z(14), -2, 6, IRON_BR, TREAD, IRON, line=IRON)
    for x in range(X(15), X(26)):
        for z in range(Z(-13), Z(14)):
            if C.get(x, -2, z) != AIR:
                continue
            n = fbm(x, z, 4.0, 81)
            if n > 0.55 and abs(z - Z(8)) > 2 and abs(x - X(19)) > 2:
                hh = 1 + int((n - 0.55) * 8)
                for y in range(-2, -2 + min(hh, 3)):
                    C.set(x, y, z, "coal_block" if hash3(x, y, z, 82) < 0.7 else slab(W + "smokestack_brick_slab"))
    # the breach: torn plates, ice shards poking in
    for x in range(X(18), X(20) + 1):
        for z in range(Z(10), Z(19)):
            for y in range(-2, 2):
                C.air(x, y, z)
            C.set(x, -3, z, TREAD if z < Z(15) else PICE)
    for (x, y, z) in ((X(17), 1, Z(13)), (X(21), 0, Z(13)), (X(17), -2, Z(14)), (X(21), 1, Z(14))):
        C.set(x, y, z, RUST)
    C.set(X(18), 1, Z(12), BICE)
    C.set(X(20), 1, Z(11), PICE)
    # the chute (blocked), a barrow, a lamp, the waystone of the miners? no: a chest and a spawner
    for y in range(-2, 4):
        C.set(X(15), y, Z(-2), IRON_BR)
    C.set(X(16), 2, Z(0), HANG_LAMP)
    C.set(X(22), 2, Z(-6), HANG_LAMP)
    C.set(X(22), 2, Z(8), HANG_LAMP)
    C.set(X(16), -2, Z(-12), "barrel[facing=up,open=false]")
    C.bp.chest(X(16), -2, Z(-10), "east", loot=LOOT + "if_bunker")
    C.bp.spawner(X(23), -2, Z(-9), MOB_MITE)


def crew_deck(C):
    """The crew deck (feet 5): the crew mess (waystone; the hatch ladder to the starboard side deck; the stair up to
    the officers' mess) and the corridor of cabins under the forecastle."""
    hroom(C, IB, X(58), X(72), Z(-15), Z(15), 5, 5, MAHOGANY, PARQUET, IRON, line=MAHOGANY)
    clear(C, X(58), X(58), 5, 7, Z(7), Z(9))      # from the boiler room's stair landing
    # mess tables and benches (two long tables along u)
    for v in (-5, 3):
        for u in range(61, 68):
            C.set(X(u), 5, Z(v), TABLE)
            C.set(X(u), 5, Z(v - 1), f"{CHAIR}[facing=south]") if u % 2 else None
            C.set(X(u), 5, Z(v + 1), f"{CHAIR}[facing=north]") if u % 2 == 0 else None
        lamp(C, X(64), 8, Z(v), drop=1, spec=CHANDELIER)
    # the galley hatch, the stove, plates
    C.set(X(70), 5, Z(-1), "smoker[facing=west,lit=true]")
    C.set(X(70), 5, Z(0), "furnace[facing=west,lit=true]")
    C.set(X(70), 5, Z(1), "barrel[facing=up,open=false]")
    C.set(X(70), 6, Z(1), "barrel[facing=up,open=false]")
    for v in (-3, 3, 9):
        C.set(X(71), 7, Z(v), f"{SHELF}[facing=west]")
    C.set(X(59), 5, Z(-3), MOD["waystone"])
    C.set(X(59), 7, Z(-5), LANT)
    C.set(X(59), 8, Z(-1), f"{COG}[facing=east]")
    # the hatch ladder (starboard aft corner) up to the side deck, its lever below the hatch
    lx, lz = X(59), Z(13)
    for y in range(5, 10):
        C.set(X(58), y, lz, IRON_BR)
        C.set(lx, y, lz, "ladder[facing=east,waterlogged=false]")
    C.set(lx, 10, lz, "iron_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
    C.set(X(58), 8, Z(12), IRON_BR)
    C.set(lx, 8, Z(12), "lever[face=wall,facing=east,powered=false]")
    for y in (10, 11, 12):
        C.set(lx, y, Z(12), IRON_BR) if C.get(lx, y, Z(12)) in (None, AIR) else None
    # the stair up to the officers' mess (port side, climbing east: feet 5 -> 12)
    cells = {}
    land(cells, X(61), X(62), Z(-12), Z(-10), 5)
    steps(cells, X(63), Z(-12), "east", 7, 5)
    land(cells, X(70), X(71), Z(-12), Z(-10), 12)
    wsteps(C, cells, tread=MAHOGANY_STAIRS, floor=PARQUET, fill=MAHOGANY)
    # portholes
    portholes(C, IB, X(60), X(71), 7, every=3)
    # the corridor and the cabins (forward of the mess)
    hroom(C, IB, X(72), X(96), Z(-2), Z(2), 5, 4, MAHOGANY, PARQUET, IRON)
    clear(C, X(72), X(72), 5, 7, Z(-1), Z(1))
    cabins = [(72, 79), (79, 87), (87, 96)]
    for i, (a, b) in enumerate(cabins):
        for sgn in (-1, 1):
            z0, z1 = (Z(2), Z(15)) if sgn > 0 else (Z(-15), Z(-2))
            hroom(C, IB, X(a), X(b), z0, z1, 5, 4, MAHOGANY, PARQUET, IRON, line=MAHOGANY)
            dx = X((a + b) // 2)
            zd = Z(2 * sgn)
            clear(C, dx, dx, 5, 6, zd, zd)
            door(C, dx, 5, zd, "south" if sgn > 0 else "north", hinge="left")
            # bunks along the hull, a locker, a lamp
            zz = Z(sgn * 10)
            for k, u in enumerate(range(a + 2, b - 1, 3)):
                if C.get(X(u), 5, zz) == AIR and C.get(X(u + 1), 5, zz) == AIR:
                    C.bp.bed(X(u), 5, zz, "east", color=("blue", "gray", "brown")[(i + k) % 3])
            C.set(X(a + 1), 5, Z(sgn * 4), "barrel[facing=up,open=false]")
            C.set(X((a + b) // 2), 8, Z(sgn * 7), HANG_LAMP)
            if (i + (sgn > 0)) % 2 == 0:
                C.bp.chest(X(b - 1), 5, Z(sgn * 4), "west", loot=LOOT + "if_crew")
    C.bp.spawner(X(83), 5, Z(-8), MOB_STRAY)
    for u in (76, 84, 92):
        C.set(X(u), 8, Z(0), HANG_LAMP)
    portholes(C, IB, X(74), X(95), 7, every=4)


def engineers(C):
    """The engineers' quarters under the aft deck (optional, from the aft deck's companion): bunks, the workbench,
    spare parts, the chief engineer's chest."""
    hroom(C, IB, X(8), X(23), Z(-14), Z(14), 5, 5, IRON_BR, TREAD, IRON, line=MAHOGANY)
    for u in (10, 13, 16):
        if C.get(X(u), 5, Z(-9)) == AIR and C.get(X(u + 1), 5, Z(-9)) == AIR:
            C.bp.bed(X(u), 5, Z(-9), "east", color="gray")
    C.set(X(20), 5, Z(-10), "smithing_table")
    C.set(X(21), 5, Z(-10), "grindstone[face=floor,facing=north]")
    C.set(X(19), 5, Z(-10), "crafting_table")
    for v in (-6, -4):
        C.set(X(9), 6, Z(v), GEAR)
    C.bp.chest(X(12), 5, Z(8), "north", loot=LOOT + "if_engineers")
    C.bp.spawner(X(16), 5, Z(3), MOB_SPIDER)
    for u in (11, 18):
        C.set(X(u), 9, Z(0), HANG_LAMP)
    portholes(C, IB, X(9), X(22), 7, every=3)


def strongroom(C):
    """The expedition strongroom in the bow under the forecastle (feet 7): pay chests, the sledge-party's sealed
    instruments, gold bars on brass racks; the breach in the bow opens onto the ice slide."""
    hroom(C, IB, X(97), X(114), Z(-9), Z(9), 7, 6, IRON_BR, TREAD, None, line=BRASS)
    for x in range(X(98), X(114)):
        for z in range(Z(-8), Z(9)):
            if C.get(x, 6, z) == W + "diamond_plate" and (x + z) % 4 == 0:
                C.set(x, 6, z, BRASS)
    # the ladder pillar under the hood
    for y in range(7, 13):
        C.set(X(104) + 1, y, Z(0), IRON)
    C.bp.chest(X(100), 7, Z(-3), "east", loot=LOOT + "if_strongroom")
    C.bp.chest(X(100), 7, Z(3), "east", loot=LOOT + "if_strongroom")
    C.bp.chest(X(108), 7, Z(-2), "west", loot=LOOT + "if_strongroom")
    for (u, v) in ((102, -5), (102, 5), (106, -4)):
        C.set(X(u), 7, Z(v), "gold_block" if v < 0 else "raw_gold_block")
        C.set(X(u), 8, Z(v), slab(BRASS_SLAB))
    C.set(X(98), 9, Z(0), f"{COG}[facing=east]")
    for u in (99, 106):
        C.set(X(u), 12, Z(0), HANG_LAMP)
    # the breach out of the starboard bow (onto the slide)
    for x in range(X(106), X(109)):
        for z in range(Z(5), Z(14)):
            for y in range(7, 10):
                if y >= 7:
                    C.air(x, y, z)
            C.set(x, 6, z, TREAD if z < Z(10) else BICE)


# ------------------------------------------------------------------ the icebreaker: superstructure
def bridge_house(C):
    """The bridge house (u 60..73): officers' mess (feet 12, full width), captain's deck (feet 18), wheelhouse
    (feet 24, its wings); the enclosed stair from the wheelhouse to the forecastle (the compression before the arena)."""
    xa, xf = X(60), X(73)
    # L1 walls from the deck to the boat-deck level, full width (it closes the side decks off the forecastle)
    for x in range(xa, xf + 1):
        for z in range(Z(-16), Z(16) + 1):
            _, v, h = IB.local(x, 11, z)
            w = IB.hw(x - XS, 9)
            if abs(z - ZC) > w + 0.3:
                continue
            edge = x in (xa, xf) or abs(z - ZC) > w - 1.2
            for y in range(9, BD + 1):
                if y == BD:
                    C.set(x, y, z, IRON)
                elif y == 10:
                    C.set(x, y, z, IRON if edge else IRON)
                elif y == 11:
                    C.set(x, y, z, IRON_BR if edge else PARQUET)
                elif edge:
                    C.set(x, y, z, MAHOGANY if y in (12, 16) else ("glass" if y == 14 and (x % 3 == 0 or
                          x in (xa, xf) and z % 3 == 0) else "white_terracotta"))
                else:
                    C.air(x, y, z)
    # L2 (captain's deck) v -10..10, L3 wheelhouse v -9..9
    box_room(C, xa, xf, Z(-10), Z(10), BD, 23, lambda x, y, z: "glass_pane" if y == 20 and (x + z) % 3 == 0
             else ("white_terracotta" if y > BD + 1 else MAHOGANY), floor=PARQUET, ceil=IRON)
    box_room(C, X(61), xf, Z(-9), Z(9), 23, 29, lambda x, y, z: "glass_pane" if 25 <= y <= 27 and
             (x == xf or (z in (Z(-9), Z(9)) and x > X(63))) else ("white_terracotta" if y < 28 else BRASS),
             floor=PARQUET, ceil=IRON)
    # the wings: platforms off the L2 roof, parapets of dark iron (nobody steps off onto the arena)
    for x in range(X(64), xf + 1):
        for v in list(range(10, 16)) + list(range(-15, -9)):
            C.set(x, 23, Z(v), TREAD)
            C.set(x, 22, Z(v), IRON) if abs(v) > 10 else None
    for x in range(X(64), xf + 1):
        for v in (15, -15):
            C.set(x, 24, Z(v), IRON_WALL)
    for v in list(range(10, 16)) + list(range(-15, -9)):
        C.set(xf, 24, Z(v), IRON_WALL)
        C.set(X(64), 24, Z(v), IRON_WALL)
    for sgn in (-1, 1):
        door(C, X(70), 24, Z(9 * sgn), "south" if sgn > 0 else "north")
        C.set(X(68), 26, Z(10 * sgn), EDISON)
    # the L1 roof outside L2 (v 11..15) and the boat-deck level round it: parapets on the forecastle side
    for v in list(range(11, 16)) + list(range(-15, -10)):
        C.set(xf, BD + 1, Z(v), IRON_WALL)
    for x in range(xa, xf + 1):
        for v in (15, -15):
            if C.get(x, BD, Z(v)) is not None:
                C.set(x, BD + 1, Z(v), IRON_WALL)
    # the monkey island: parapet, binnacle, searchlight; the roof hatch down into the wheelhouse
    # (two high on the front and the sides: nobody drops from the roof onto the arena past the mist)
    for x in range(X(61), xf + 1):
        for z in (Z(-9), Z(9)):
            C.set(x, 30, z, IRON_WALL)
            C.set(x, 31, z, IRON_WALL)
    for z in range(Z(-9), Z(10)):
        C.set(xf, 30, z, IRON_WALL)
        C.set(xf, 31, z, IRON_WALL)
        if not (Z(-4) <= z <= Z(-2)):
            C.set(X(61), 30, z, IRON_WALL)
    C.set(X(70), 30, Z(0), BRASS)
    C.set(X(70), 31, Z(0), "lantern[hanging=false,waterlogged=false]")
    # the wheelhouse (feet 24, site of grace): the wheel on its brass pedestal, the engine telegraphs, the chart
    # table, the speaking tubes, the waystone by the roof hatch
    C.set(X(71), 24, Z(0), BRASS)
    C.set(X(71), 25, Z(0), BRASS)
    C.set(X(70), 25, Z(0), f"{VALVE}[facing=west]")
    for v in (-3, 3):
        C.set(X(72), 24, Z(v), BRASS)
        C.set(X(72), 25, Z(v), GAUGE)
    for u in (66, 67):
        C.set(X(u), 24, Z(-5), TABLE)
    C.set(X(66), 25, Z(-5), "lantern[hanging=false,waterlogged=false]")
    C.set(X(68), 24, Z(-6), f"{CHAIR}[facing=north]")
    for v in (-8, -4, 4):
        C.set(X(61), 26, Z(v), PIPES)
    C.set(X(63), 24, Z(-3), MOD["waystone"])
    C.set(X(66), 28, Z(0), HANG_LAMP)
    C.set(X(70), 28, Z(-5), HANG_LAMP)
    hx, hz = X(62), Z(-2)
    for y in range(24, 29):
        C.set(hx, y, hz, "ladder[facing=east,waterlogged=false]")
    C.set(hx, 29, hz, "spruce_trapdoor[facing=east,half=top,open=false,powered=false,waterlogged=false]")
    # the bridge stair: top landing u 62..63 (feet 24), steps u 64..71 (feet 23..16), landing u 72 (feet 15)
    cells = {}
    land(cells, X(62), X(62), Z(6), Z(8), 24)
    for i, u in enumerate(range(63, 72)):
        for v in (6, 7, 8):
            cells[(X(u), Z(v))] = (24 - i, "west")
    land(cells, X(72), X(72), Z(6), Z(8), 15)
    for (x, z), (f, fc) in cells.items():
        for y in range(f, f + 4):
            C.air(x, y, z)
    for (x, z), (f, fc) in cells.items():
        C.set(x, f - 1, z, stair(TREAD_STAIRS, fc) if fc else TREAD)
        lo = 11 if fc or f == 15 else f - 2
        for y in range(lo, f - 1):
            C.set(x, y, z, IRON_BR)
    # the stairwell's walls (v 5 and v 9) through L1, L2 and the wheelhouse floor
    for x in range(X(61), xf + 1):
        for y in range(11, 23):
            for v in (5, 9):
                C.set(x, y, Z(v), IRON_BR if v == 9 or y < 18 else MAHOGANY)
        for y in range(11, 14):
            for v in (6, 7, 8):
                if x >= X(64):
                    C.set(x, y, Z(v), IRON_BR)
    for y in range(11, 23):
        for v in (6, 7, 8):
            if C.get(X(61), y, Z(v)) == AIR or C.get(X(61), y, Z(v)) is None:
                C.set(X(61), y, Z(v), IRON_BR)
    # starboard strip of L1 (v 10..14) beside the stairwell: the pantry, reached round the aft end of the stair
    for x in range(X(61), X(64)):
        for y in range(12, 15):
            for v in range(5, 10):
                C.air(x, y, Z(v))
        C.set(x, 11, Z(7), PARQUET)
    for x in range(X(61), X(64)):
        for v in range(5, 10):
            C.set(x, 11, Z(v), PARQUET)
            C.set(x, 15, Z(v), MAHOGANY)
            C.set(x, 16, Z(v), MAHOGANY)
    # railings round the stair hole in the wheelhouse floor
    for x in range(X(64), xf):
        rail(C, x, 24, Z(5), "north")
    # the arena door at the stair foot (front wall u 73, v 6..8) and its mist
    clear(C, xf, xf, 15, 17, Z(6), Z(8))
    for v in (6, 7, 8):
        C.set(xf, 14, Z(v), TREAD)
        C.set(xf + 1, 14, Z(v), TREAD) if C.get(xf + 1, 14, Z(v)) is None else None
    C.bp.mist(xf, 15, Z(6), xf, 17, Z(8))


def officers_mess(C):
    """The officers' mess (L1, feet 12): one long mahogany table under two chandeliers, the sideboard, the
    bookcases, the portrait wall, the hearth, the pantry beyond the stairwell."""
    for u in range(63, 71):
        for v in (-6, -5):
            C.set(X(u), 12, Z(v), TABLE)
        C.set(X(u), 12, Z(-7), f"{CHAIR}[facing=south]")
        C.set(X(u), 12, Z(-4), f"{CHAIR}[facing=north]")
    C.set(X(62), 12, Z(-6), f"{CHAIR}[facing=east]")
    for u in (65, 69):
        lamp(C, X(u), 15, Z(-5), drop=1, spec=CHANDELIER)
    for u in range(62, 72):
        C.set(X(u), 12, Z(-14), "bookshelf") if u % 3 else C.set(X(u), 12, Z(-14), "chiseled_bookshelf")
        C.set(X(u), 13, Z(-14), "bookshelf")
    C.set(X(72), 12, Z(-2), "smoker[facing=west,lit=true]")
    C.set(X(72), 13, Z(-2), SOOT)
    C.set(X(72), 12, Z(0), "barrel[facing=up,open=false]")
    for v in (-10, -8, -2, 0, 2):
        C.set(X(61), 14, Z(v), f"{COG}[facing=east]") if v % 4 == 0 else C.set(X(61), 14, Z(v), GAUGE)
    C.bp.chest(X(62), 12, Z(2), "east", loot=LOOT + "if_officers")
    # the pantry strip (v 10..14)
    for u in range(63, 72, 2):
        C.set(X(u), 12, Z(13), "barrel[facing=up,open=false]")
        C.set(X(u), 14, Z(14), f"{SHELF}[facing=north]")
    C.set(X(66), 15, Z(12), HANG_LAMP)
    C.bp.spawner(X(68), 12, Z(-11), MOB_DRONE)
    # the stair on to the captain's deck (v 1..3, climbing west: feet 12 -> 18)
    cells = {}
    land(cells, X(71), X(71), Z(1), Z(3), 12)
    steps(cells, X(70), Z(1), "west", 6, 12)
    land(cells, X(63), X(64), Z(1), Z(3), 18)
    wsteps(C, cells, tread=MAHOGANY_STAIRS, floor=PARQUET, fill=MAHOGANY)
    for u in range(65, 71):
        rail(C, X(u), BD + 1, Z(0), "north") if C.get(X(u), BD, Z(0)) is not None else None
    for u in range(65, 70):
        C.set(X(u), 12, Z(-9), f"{RAIL}[facing=north]")


def captains_deck(C):
    """L2 (feet 18): the captain's cabin aft (bed, desk, sea chest), the day room forward (chart table, the
    chronometers, the telegraph), the iced-over stair to the wheelhouse; the door aft onto the boat deck."""
    # partition between sleeping cabin and day room
    for v in range(-9, 5):
        if v not in (-2, -1):
            for y in range(18, 22):
                C.set(X(66), y, Z(v), MAHOGANY)
    C.bp.bed(X(61), 18, Z(-8), "east", color="red")
    C.set(X(61), 18, Z(-6), "barrel[facing=up,open=false]")
    C.bp.chest(X(64), 18, Z(-9), "south", loot=LOOT + "if_captain")
    C.set(X(62), 18, Z(-3), TABLE)
    C.set(X(62), 18, Z(-2), f"{CHAIR}[facing=west]")
    C.set(X(62), 19, Z(-3), "lantern[hanging=false,waterlogged=false]")
    C.set(X(64), 21, Z(-5), HANG_LAMP)
    for v in (-9, -8, -7):
        C.set(X(72), 18, Z(v), "bookshelf")
    C.set(X(69), 18, Z(-5), "cartography_table")
    C.set(X(70), 18, Z(-5), "cartography_table")
    C.set(X(69), 18, Z(-6), f"{CHAIR}[facing=north]")
    C.set(X(72), 18, Z(0), "lectern[facing=west,has_book=false,powered=false]")
    C.set(X(72), 19, Z(3), GAUGE)
    C.set(X(72), 19, Z(-2), f"{COG}[facing=west]")
    lamp(C, X(69), 21, Z(-2), drop=1, spec=CHANDELIER)
    # the stair to the wheelhouse, frozen solid: three steps into a block of blue ice
    for i, u in enumerate((70, 71, 72)):
        C.set(X(u), 18 + i, Z(-8), stair(MAHOGANY_STAIRS, "east"))
        for y in range(19 + i, 23):
            C.set(X(u), y, Z(-8), BICE)
    # the door aft onto the boat deck (port strip)
    door(C, X(60), 18, Z(-9), "west")


def boat_deck(C):
    """The boat deck over the casing (feet 18): the two funnels, lifeboats in chocks, ventilator cowls, the stair
    down to the aft deck, the catwalk to the cargo crane."""
    for x in range(X(24), X(60)):
        for z in range(Z(-13), Z(14)):
            if C.get(x, BD, z) is None or abs(z - ZC) > 10:
                C.set(x, BD, z, SPRUCE if (x % 6) else DOAK)
            for y in range(BD + 1, BD + 4):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
        for v in (-13, 13):
            rail(C, x, BD + 1, Z(v), "north" if v < 0 else "south")
        # stanchions under the overhang
        if (x - XS) % 6 == 0:
            for v in (-12, 12):
                for y in range(int(MAIN_T) + 1, BD):
                    if C.get(x, y, Z(v)) is None or C.get(x, y, Z(v)) == AIR:
                        C.set(x, y, Z(v), IRON_WALL)
    for z in range(Z(-13), Z(14)):
        if not (Z(-4) <= z <= Z(-2)) and not (Z(10) <= z <= Z(12)):
            rail(C, X(24), BD + 1, z, "west")
    # lifeboats (starboard aft pair, port aft one): hulls of spruce under canvas
    for (u0, sgn) in ((26, 1), (36, 1), (26, -1)):
        for du in range(0, 8):
            w = 1 if du in (0, 7) else 2
            for k in range(-w, w + 1):
                z = Z(sgn * 11) + k
                C.set(X(u0 + du), BD + 1, z, SPRUCE if abs(k) == w else "white_wool")
                C.set(X(u0 + du), BD + 2, z, "white_wool" if abs(k) < w else SPRUCE)
                C.set(X(u0 + du), BD + 3, z, "white_wool" if k == 0 else
                      ("light_gray_wool" if abs(k) < w else slab("spruce_slab", "top")))
    # ventilator cowls
    for (u, v) in ((44, 11), (44, -11), (58, 11)):
        C.set(X(u), BD + 1, Z(v), COPPER)
        C.set(X(u), BD + 2, Z(v), COPPER)
        C.set(X(u), BD + 3, Z(v), stair(COPPER_ST, "south" if v < 0 else "north"))
    # the stair down to the aft deck (v -4..-2, climbing east from the deck)
    fd = IB.feet(X(17), Z(-3))
    fb = int(math.floor(fd + 0.5)) if fd is not None else 12
    cells = {}
    land(cells, X(16), X(17), Z(-4), Z(-2), fb)
    steps(cells, X(18), Z(-4), "east", BD + 1 - fb, fb)
    wsteps(C, cells, tread=SPRUCE.replace("_planks", "_stairs"), floor=SPRUCE, fill=IRON, solid_to=int(MAIN_T))


def funnels(C):
    """The two funnels (radius 8), leaning with the list: copper bodies, brass bands, sooty crowns, a steam pipe up
    the aft face; inside the forward one the maintenance newel stair to the gantry door at feet 38."""
    tan = IB.sr / IB.cr
    for uc in (F1U, F2U):
        cx = X(uc)
        for y in range(BD, FTOP + 1):
            zc = ZC + y * tan
            for x in range(cx - FR - 2, cx + FR + 3):
                for z in range(int(zc) - FR - 3, int(zc) + FR + 4):
                    d = math.hypot(x - cx, z - zc)
                    r = FR + (1 if y >= FTOP - 1 else 0)
                    if r - 0.75 < d <= r + 0.45:
                        if y >= FTOP - 6:
                            spec = SOOT
                        elif y in (FTOP - 8, FTOP - 9, BD + 3) or y == FTOP - 20:
                            spec = BRASS
                        else:
                            spec = COPPER if hash3(x, y, z, 91) < 0.92 else VERD
                        C.set(x, y, z, spec)
                    elif d <= r - 0.75 and y == BD:
                        C.set(x, y, z, IRON)
            # the steam pipe on the aft face
            if y < FTOP - 2:
                C.set(cx - FR - 1, y, int(round(zc)), PIPES)
        C.set(cx - FR - 1, FTOP - 2, int(round(ZC + (FTOP - 2) * tan)), GAUGE)
    # the newel inside the forward funnel: NW corner at feet 18 (door north), 10 flights of 2 to the SE corner at 38
    cx = X(F2U)
    zc = int(round(ZC + 18 * tan))
    x0, z0 = cx - 4, zc - 4
    for x in range(x0 - 3, x0 + 12):
        for z in range(z0 - 4, z0 + 12):
            d = math.hypot(x - cx, z - (ZC + 18 * tan))
            if d <= FR - 0.75:
                for y in range(BD + 1, BD + 4):
                    C.air(x, y, z)
    _, core, c, ftop = newel_laps(C, x0, z0, 2, 18, [2] * 10, 0)
    cx0, cz0, cx1, cz1 = core
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(BD, ftop + 3):
                C.set(x, y, z, IRON_BR if y % 6 else BRASS)
    for y in (21, 27, 33):
        C.set(cx0, y, cz0, "ochre_froglight")
        C.set(cx1, y + 3, cz1, "ochre_froglight")
    # entry door through the north wall
    zn = int(math.floor(ZC + 18 * tan - FR))
    for z in range(zn - 1, z0):
        for y in (18, 19, 20):
            C.air(x0 + 1, y, z)
        C.set(x0 + 1, BD, z, IRON)
    # top platform from the SE corner to the east wall, the door, the gantry
    ztop = ZC + 38 * tan
    xe = int(math.floor(cx + math.sqrt(max(0.0, FR ** 2 - (z0 + 6 - ztop) ** 2))))
    for x in range(x0 + 5, xe + 3):
        for z in range(z0 + 5, z0 + 8):
            C.set(x, 37, z, TREAD)
            for y in (38, 39, 40):
                C.air(x, y, z)
    gz = z0 + 5
    cells = {}
    land(cells, xe + 1, xe + 2, gz, gz + 2, 38)
    steps(cells, X(67), gz, "west", 8, 30)
    land(cells, X(68), X(69), gz, gz + 2, 30)
    for i in range(8):
        for k in range(3):
            cells[(X(67) - i, gz + k)] = (31 + i, "west")
    gx0 = X(67) - 7
    for x in range(gx0, xe + 3):
        for k in range(3):
            if (x, gz + k) not in cells:
                cells[(x, gz + k)] = (38, None)
    wsteps(C, cells)
    for x in range(min(gx0, xe) - 1, X(68)):
        for zz in (gz - 1, gz + 3):
            f = max(cells.get((x, gz), (30, None))[0], 30)
            if C.get(x, f, zz) in (None, AIR):
                C.set(x, f, zz, IRON_WALL)
    for x in (gx0, gx0 + 3, xe + 1):
        f = cells.get((x, gz), (30, None))[0]
        for y in range(24, f - 2):
            if C.get(x, y, gz + 1) in (None, AIR):
                C.set(x, y, gz + 1, IRON_WALL)


def paddle_wheels(C):
    """The paddle wheels, half sunk in the ice in holes of black water, under their semicircular boxes (a brass
    sunburst of vent slats on the outer face)."""
    for sgn in (-1, 1):
        for x in range(X(PADU - 13), X(PADU + 13) + 1):
            for z in range(Z(sgn * 15), Z(sgn * 24) + sgn, sgn):
                for y in range(-9, 16):
                    u, v, h = IB.local(x, y, z)
                    av = abs(v)
                    if not (16.0 <= av <= 22.6):
                        continue
                    du, dh = u - PADU, h - PADH
                    d = math.hypot(du, dh)
                    a = math.atan2(dh, du)
                    if dh >= -0.5:
                        # the box: an outer semicircle plate, a curved top, open below the axle
                        if d <= PADR + 1.5:
                            if av >= 21.6:
                                slat = int((a + math.pi) / (math.pi / 9)) % 2
                                spec = BRASS if (d < 3 or (slat and d > 4)) else IRON
                                C.set(x, y, z, spec)
                            elif d > PADR + 0.5:
                                C.set(x, y, z, IRON if d < PADR + 1.0 else BRASS)
                        continue
                    if 17.0 <= av <= 21.0:
                        rim = PADR - 0.8 <= d <= PADR + 0.2
                        spoke = d <= PADR and min(abs(((a * 6 / math.pi) % 1) - 0.5), 0.5) > 0.42
                        paddle = PADR - 2.5 <= d <= PADR and abs(math.sin(6 * a)) < 0.13
                        hubc = d <= 1.5
                        if rim or spoke or paddle or hubc:
                            C.set(x, y, z, BRASS if rim and av in (17.0, 21.0) else
                                  ("dark_oak_planks" if paddle else IRON))
        # the hole in the ice round the lower half
        for x in range(X(PADU - 12), X(PADU + 12) + 1):
            for z in range(Z(sgn * 16), Z(sgn * 24) + sgn, sgn):
                u, v, h = IB.local(x, 0, z)
                if math.hypot(u - PADU, (abs(v) - 19) * 1.6) > 12.5 + (hash01(x, z, 95) - 0.5) * 2:
                    continue
                for y in (0, -1):
                    if C.get(x, y, z) in ("minecraft:" + SNOW, "minecraft:" + PICE, "minecraft:ice",
                                          "minecraft:" + BICE, None):
                        C.set(x, y, z, WATER if hash01(x, z, 96 + y) > 0.06 else PICE)


def deck_fittings(C):
    """The weather decks: bulwark gaps, the starboard side deck's gate and gangway (the hatch shortcut), the aft
    deck's mainmast and crow's nest, the companion to the engineers', the cargo crane and its jib over the ice; the
    forecastle (the arena): capstans, hatches, the foremast, the sealed hood over the strongroom ladder."""
    # -- the starboard side deck cul-de-sac (u 53..59, v 12..15): gate aft, gangway down the flank
    for v in range(12, 16):
        for y in range(10, 15):
            if C.get(X(52), y, Z(v)) in (None, AIR):
                C.set(X(52), y, Z(v), "iron_bars")
    for u in range(56, 59):
        for y in range(10, 15):
            for v in (15, 16):
                b = C.get(X(u), y, Z(v))
                if b is not None and b != AIR and y >= 11:
                    C.air(X(u), y, Z(v))
        for v in range(15, 20):
            C.set(X(u), 10, Z(v), TREAD)
            for y in (11, 12, 13):
                C.air(X(u), y, Z(v))
    cells = {}
    land(cells, X(69), X(70), Z(17), Z(19), 1)
    steps(cells, X(68), Z(17), "west", 10, 1)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE, solid_to=0)
    for u in range(59, 70):
        f = cells.get((X(u), Z(17)), (11, None))[0]
        C.set(X(u), f, Z(20), "spruce_fence")
    # -- the aft deck: mainmast and crow's nest (ladder), companion to the engineers', capstan, hatch
    mast(C, IB, X(12), ZC, 11, 50, spec=IRON_WALL, yards=((38, 9), (28, 11)), sail=False, top=EDISON)
    tan = IB.sr / IB.cr
    nz = int(round(ZC + 40 * tan))
    for x in range(X(10), X(15)):
        for z in range(nz - 2, nz + 3):
            C.set(x, 39, z, SPRUCE)
            if x in (X(10), X(14)) or z in (nz - 2, nz + 2):
                C.set(x, 40, z, IRON_WALL)
            else:
                for y in (40, 41, 42):
                    if C.get(x, y, z) is None:
                        C.air(x, y, z)
    C.bp.chest(X(13), 40, nz + 1, "west", loot=LOOT + "if_crowsnest")
    for y in range(12, 39):
        z = int(round(ZC + y * tan))
    lz = nz
    for y in range(12, 40):
        C.set(X(12), y, lz, IRON_BR)
        C.set(X(11), y, lz, "ladder[facing=west,waterlogged=false]")
    C.set(X(11), 39, lz, "spruce_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]")
    # the companion down to the engineers' (climbing east from feet 5 to the deck)
    fd = IB.feet(X(22), Z(-7))
    fb = int(math.floor(fd + 0.5)) if fd is not None else 12
    cells = {}
    land(cells, X(13), X(13), Z(-8), Z(-6), 5)
    steps(cells, X(14), Z(-8), "east", fb - 5, 5)
    wsteps(C, cells, tread=TREAD_STAIRS, floor=TREAD, fill=IRON)
    hx1 = X(14) + fb - 5
    for x in range(X(13), hx1 + 2):
        for z in (Z(-9), Z(-5)):
            for y in range(fb - 1, fb + 3):
                C.set(x, y, z, MAHOGANY if y < fb + 2 else IRON)
        for z in range(Z(-9), Z(-4)):
            C.set(x, fb + 3, z, IRON)
    for z in range(Z(-9), Z(-4)):
        for y in range(fb - 1, fb + 3):
            C.set(X(13) - 1, y, z, MAHOGANY)
    for (u, v) in ((18, 4), (8, 0)):
        f = IB.feet(X(u), Z(v)) or 12
        C.set(X(u), int(f), Z(v), "brasshaven:gear_panel")
        C.set(X(u), int(f) + 1, Z(v), log("stripped_dark_oak_log", "y"))
    # -- the cargo crane on the aft deck (starboard) and its jib out over the ice, the catwalk from the boat deck
    px, pz = X(20), Z(9)
    for y in range(9, 25):
        for dx in (0, 1):
            for dz in (0, 1):
                C.set(px + dx, y, pz + dz, BRASS if y % 6 == 0 else IRON_BR)
    for x in range(px - 1, px + 3):
        for z in range(pz - 1, pz + 3):
            for y in range(13, 17):
                edge = x in (px - 1, px + 2) or z in (pz - 1, pz + 2)
                if edge:
                    C.set(x, y, z, "glass_pane" if y == 15 else IRON)
            C.set(x, 17, z, IRON)
    jx = (px, px + 1)
    for z in range(pz + 2, Z(31) + 1):
        for x in jx:
            C.set(x, BD, z, TREAD)
            C.set(x, BD - 1, z, IRON_WALL if z % 3 else BRASS)
            for y in range(BD + 1, BD + 4):
                C.air(x, y, z)
        C.set(px - 1, BD + 1, z, IRON_WALL) if z < Z(29) else None
        C.set(px + 2, BD + 1, z, IRON_WALL) if z < Z(29) and z > Z(13) else None
    # tie chains from the crane head to the jib
    for z in range(pz + 2, Z(31) + 1):
        y = int(round(24 - (z - pz) * 6.0 / 22.0))
        if y > BD + 3:
            C.set(px - 1, y, z, CHAIN.replace("axis=y", "axis=z"))
    C.set(px, BD - 1, Z(31), GEAR)
    for y in range(BD - 6, BD - 1):
        C.set(px + 1, y, Z(31), CHAIN)
    C.set(px + 1, BD - 7, Z(31), "iron_block")
    # the catwalk from the boat deck's aft starboard corner to the jib
    for x in range(px + 2, X(25)):
        for z in range(Z(10), Z(13)):
            C.set(x, BD, z, TREAD)
            for y in range(BD + 1, BD + 4):
                C.air(x, y, z)
        C.set(x, BD + 1, Z(13), IRON_WALL)
    # -- the forecastle: capstans, hatches, ventilators, the foremast, the sealed hood
    for (u, v) in ((80, -9), (80, 9)):
        f = int(IB.feet(X(u), Z(v)) or 15)
        C.set(X(u), f, Z(v), GEAR)
        C.set(X(u), f + 1, Z(v), log("stripped_dark_oak_log", "y"))
        C.set(X(u), f + 2, Z(v), slab(BRASS_SLAB))
    for (u0, v0) in ((84, -12), (84, 10), (95, -12), (95, 10)):
        for du in range(3):
            for dv in range(2):
                f = int(IB.feet(X(u0 + du), Z(v0 + dv)) or 15)
                C.set(X(u0 + du), f, Z(v0 + dv), "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,"
                                                 "waterlogged=false]")
    mast(C, IB, X(112), ZC, 13, 46, spec=IRON_WALL, yards=((40, 7),), sail=False, top=EDISON)
    # the hood (u 102..106, v -2..2): sealed bars aft, the ladder hole down to the strongroom
    for x in range(X(102), X(107)):
        for v in range(-2, 3):
            edge = x in (X(102), X(106)) or v in (-2, 2)
            for y in range(13, 19):
                if y == 13:
                    C.set(x, y, Z(v), IRON)
                elif y == 14:
                    C.set(x, y, Z(v), IRON if edge else TREAD)
                elif y == 18:
                    C.set(x, y, Z(v), BRASS)
                elif edge:
                    C.set(x, y, Z(v), IRON_BR if y < 17 else BRASS)
                else:
                    C.air(x, y, Z(v))
    for v in (-1, 0, 1):
        for y in (15, 16, 17):
            C.set(X(102), y, Z(v), MOD["vault_bars"])
    for y in range(7, 15):
        C.set(X(104), y, Z(0), "ladder[facing=west,waterlogged=false]")
        C.set(X(105), y, Z(0), IRON) if y >= 13 else None
    # the seal
    f = int(math.floor(IB.feet(X(AC[0]), Z(AC[1])) or 15))
    C.bp.boss_seal(X(AC[0]), f - 1, Z(AC[1]), BOSS, 18)
    # lamps on the forecastle bulwarks
    for u in (78, 86, 94, 100):
        for sgn in (-1, 1):
            z = int(round(ZC + sgn * (IB.hw(u, 14) - 1.5)))
            f = IB.feet(X(u), z)
            if f is not None:
                C.set(X(u), int(math.ceil(f)), z, LANT)


# ------------------------------------------------------------------ the supply ships
def fulmar(C):
    """The Fulmar (south): gangway, companion, the 'tween deck stores, the frozen hold, the chart room under the
    poop and its stair to the poop deck, the bosun's locker in the forecastle."""
    S = SB
    build_hull(C, S, wood_plate("green_terracotta"), lambda x, z: SPRUCE, lambda x, z: slab("spruce_slab"),
               under=DOAK, cap="stripped_dark_oak_log[axis=x]", bul_h=2)
    xs = S.xs
    # rooms
    hroom(C, S, xs + 3, xs + 44, 23, 41, 2, 4, SPRUCE, SPRUCE, None, line="barrel[facing=up,open=false]")
    hroom(C, S, xs + 3, xs + 38, 23, 41, -5, 6, PICE, SPRUCE, None, line=PICE)
    hroom(C, S, xs + 1, xs + 13, 23, 41, 8, 4, SPRUCE, PARQUET, None, line="bookshelf")
    hroom(C, S, xs + 44, xs + 53, 23, 41, 8, 4, SPRUCE, SPRUCE, None, line=SPRUCE)
    bulkhead(C, S, xs + 13, 7, 12, DOAK)
    bulkhead(C, S, xs + 44, 7, 12, DOAK)
    # gangway (north flank, climbing east from the ice to the main deck)
    cells = {}
    land(cells, 2, 3, 19, 21, 1)
    steps(cells, 4, 19, "east", 6, 1)
    land(cells, 10, 12, 19, 22, 7)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE, solid_to=0)
    for x in range(10, 13):
        for z in (23, 24):
            for y in range(7, 11):
                C.air(x, y, z)
            C.set(x, 6, z, SPRUCE)
    for x in range(4, 10):
        C.set(x, cells[(x, 19)][0], 18, "spruce_fence")
    # companion hood (x 2..11, z 30..34), stair from the 'tween deck (feet 2) up to the hood (feet 8)
    cells = {}
    land(cells, 1, 2, 31, 33, 2)
    steps(cells, 3, 31, "east", 6, 2)
    land(cells, 9, 10, 31, 33, 8)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    for x in range(2, 12):
        for z in range(30, 35):
            edge = x in (2, 11) or z in (30, 34)
            for y in range(7, 12):
                if y == 11:
                    C.set(x, y, z, "spruce_slab[type=bottom,waterlogged=false]" if not edge else DOAK)
                elif edge and y > 7:
                    C.set(x, y, z, DOAK if x in (2, 11) and z in (30, 34) else SPRUCE)
                elif edge and y == 7 and C.get(x, y, z) is None:
                    C.set(x, y, z, SPRUCE)
    for z in (31, 32, 33):
        for y in (8, 9):
            C.air(11, y, z)
    C.set(6, 10, 32, LANT_H)
    # stair from the 'tween deck down to the frozen hold (z 35..37, climbing west from feet -5 to 2)
    cells = {}
    land(cells, 12, 13, 35, 37, -5)
    steps(cells, 11, 35, "west", 7, -5)
    land(cells, 3, 4, 35, 37, 2)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    # stair from the hold up to the aft 'tween deck (z 31..33, climbing west from feet -5 to 2)
    cells = {}
    land(cells, -11, -10, 31, 33, -5)
    steps(cells, -12, 31, "west", 7, -5)
    land(cells, -20, -19, 31, 33, 2)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    # stair from the aft 'tween deck up to the chart room (z 35..37, climbing west from feet 2 to 8)
    cells = {}
    land(cells, -13, -13, 35, 37, 2)
    steps(cells, -14, 35, "west", 6, 2)
    land(cells, -21, -20, 35, 37, 8)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    for x in range(-19, -15):
        rail(C, x, 8, 34, "north")
    # stair from the chart room to the poop deck (z 26..28, climbing west)
    fp = S.feet(-20, 27)
    fp = int(math.floor(fp + 0.5)) if fp is not None else 13
    cells = {}
    land(cells, -13, -13, 26, 28, 8)
    steps(cells, -14, 26, "west", fp - 8, 8)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    for x in range(-14 - (fp - 8) + 1, -13):
        C.set(x, fp, 29, "spruce_fence") if C.get(x, fp, 29) is None else None
    # door from the main deck into the bosun's locker (forecastle bulkhead, x 20)
    clear(C, xs + 44, xs + 44, 8, 9, 32, 32)
    door(C, xs + 44, 8, 32, "west")
    C.set(xs + 43, 7, 32, SPRUCE) if C.get(xs + 43, 7, 32) is None else None
    # furnishing: the 'tween deck stores
    for (x, z) in ((-6, 26), (-4, 26), (-2, 38), (5, 27), (8, 38), (14, 27), (16, 37), (-9, 38)):
        if C.get(x, 2, z) == AIR:
            C.set(x, 2, z, "barrel[facing=up,open=false]")
            if hash01(x, z, 5) < 0.5 and C.get(x, 3, z) == AIR:
                C.set(x, 3, z, "barrel[facing=up,open=false]")
    for x in range(-8, 0):
        if C.get(x, 2, 28) == AIR:
            C.set(x, 2, 28, "brown_wool" if x % 2 else "hay_block")
    for x in range(12, 18, 2):
        C.set(x, 2, 29, "spruce_slab[type=bottom,waterlogged=false]")
    for x in (-5, 6, 15):
        C.set(x, 5, 32, HANG_LAMP)
    # the frozen hold: crates rimed with ice, carcasses on chains, blue crystals, soul lanterns (no melting)
    for (x, z) in ((-8, 29), (-6, 35), (-2, 29), (2, 35), (6, 29), (-4, 36), (0, 28)):
        if C.get(x, -5, z) == AIR:
            C.set(x, -5, z, "barrel[facing=up,open=false]" if (x + z) % 3 else PICE)
            if C.get(x, -4, z) == AIR and hash01(x, z, 7) < 0.6:
                C.set(x, -4, z, PICE if hash01(x, z, 8) < 0.5 else "barrel[facing=up,open=false]")
    for (x, z) in ((-7, 32), (-3, 33), (1, 31), (5, 33)):
        for y in (0, -1):
            C.set(x, y, z, CHAIN)
        C.set(x, -2, z, "brown_terracotta")
        C.set(x, -3, z, "red_terracotta")
    for (x, z) in ((-9, 30), (3, 36), (7, 31)):
        if C.get(x, 0, z) == AIR:
            C.set(x, 0, z, BICE)
    for x in (-6, 2):
        C.set(x, 0, 30, SOUL_H)
        C.set(x, 0, 34, SOUL_H)
    C.bp.chest(-9, -5, 34, "east", loot=LOOT + "if_hold")
    C.bp.spawner(-4, -5, 30, MOB_STRAY)
    C.bp.spawner(4, -5, 34, MOB_STRAY)
    # the chart room: the great chart table, chronometers, the barometer, the log on its lectern
    for x in range(-19, -15):
        C.set(x, 8, 31, "cartography_table")
        C.set(x, 8, 30, f"{CHAIR}[facing=south]") if x % 2 else None
    C.set(-15, 8, 31, TABLE)
    C.set(-15, 9, 31, "lantern[hanging=false,waterlogged=false]")
    C.set(-22, 8, 32, "lectern[facing=east,has_book=false,powered=false]")
    C.set(-12, 9, 30, GAUGE)
    C.set(-12, 9, 34, f"{COG}[facing=west]")
    C.set(-18, 10, 32, HANG_LAMP)
    C.bp.chest(-21, 8, 29, "east", loot=LOOT + "if_chart")
    # the poop deck: wheel, binnacle, the rope bridge head (stern, z 33..35)
    fp2 = S.feet(-21, 32)
    if fp2 is not None:
        f2 = int(math.ceil(fp2))
        C.set(-21, f2, 32, IRON_WALL)
        C.set(-21, f2 + 1, 32, f"{VALVE}[facing=east]")
    # the bosun's locker
    for (x, z) in ((23, 30), (23, 34), (26, 32)):
        if C.get(x, 8, z) == AIR:
            C.set(x, 8, z, "barrel[facing=up,open=false]")
    if C.get(24, 8, 36) == AIR:
        C.bp.chest(24, 8, 36, "west", loot=LOOT + "if_berths")
    C.set(23, 11, 32, HANG_LAMP)
    portholes(C, S, xs + 5, xs + 42, 3, every=4)
    # masts, a little funnel
    mast(C, S, -2, 32, 8, 38, yards=((34, 7), (26, 9), (18, 8)), top="lightning_rod")
    mast(C, S, 17, 32, 8, 34, yards=((30, 6), (22, 8)), top="lightning_rod")
    tan = S.sr / S.cr
    for y in range(8, 21):
        z = int(round(32 + y * tan))
        for x in (13, 14):
            C.set(x, y, z, COPPER if y < 19 else SOOT)


def petrel(C):
    """The Petrel (south-west): the kennels in the forecastle (the rope bridge lands on it), the galley (waystone),
    the mess and the berths on the 'tween deck, the ice door (iron, its button inside), the quartermaster's store
    under the poop, the crow's nest."""
    S = SA
    build_hull(C, S, wood_plate("white_terracotta"), lambda x, z: SPRUCE, lambda x, z: slab("spruce_slab"),
               under=DOAK, cap="stripped_dark_oak_log[axis=x]", bul_h=2)
    xs = S.xs
    hroom(C, S, xs + 44, xs + 55, 27, 45, 8, 4, SPRUCE, SPRUCE, None, line=SPRUCE)
    hroom(C, S, xs + 13, xs + 43, 27, 45, 2, 4, SPRUCE, SPRUCE, None, line=SPRUCE)
    hroom(C, S, xs + 1, xs + 13, 27, 45, 8, 4, SPRUCE, SPRUCE, None, line=SPRUCE)
    bulkhead(C, S, xs + 13, 7, 12, DOAK)
    bulkhead(C, S, xs + 44, 7, 12, DOAK)
    # the hatch stair from the forecastle deck down into the kennels (z 37..39, climbing east)
    fk = S.feet(xs + 52, 38)
    fk = int(math.floor(fk + 0.5)) if fk is not None else 13
    cells = {}
    land(cells, xs + 46, xs + 46, 37, 39, 8)
    steps(cells, xs + 47, 37, "east", fk - 8, 8)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    for x in range(xs + 47, xs + 47 + fk - 8):
        C.set(x, fk, 36, "spruce_fence") if C.get(x, fk, 36) is None else None
    # kennels: pens along both flanks, straw, water bowls, the musher's bunk
    for x in range(xs + 45, xs + 54, 3):
        for zr, face in ((range(29, 31), "south"), (range(42, 44), "north")):
            for z in zr:
                if C.get(x, 8, z) == AIR:
                    C.set(x, 8, z, "hay_block" if (x + z) % 2 else "yellow_carpet")
            zf = 31 if face == "south" else 41
            if C.get(x, 8, zf) == AIR:
                C.set(x, 8, zf, "spruce_fence")
            if C.get(x + 1, 8, zf) == AIR:
                C.set(x + 1, 8, zf, "spruce_fence_gate[facing=%s,in_wall=false,open=false,powered=false]" % face)
    C.set(xs + 53, 8, 36, "cauldron")
    C.set(xs + 45, 8, 34, "bone_block[axis=x]")
    C.bp.chest(xs + 50, 8, 34, "west", loot=LOOT + "if_kennels")
    C.bp.spawner(xs + 49, 8, 36, MOB_STRAY)
    C.set(xs + 48, 11, 36, HANG_LAMP)
    C.set(xs + 52, 11, 34, HANG_LAMP)
    clear(C, xs + 44, xs + 44, 8, 9, 35, 35)
    door(C, xs + 44, 8, 35, "west")
    # companion from the main deck down to the 'tween deck (z 35..37, climbing east from feet 2 to 8)
    cells = {}
    land(cells, xs + 29, xs + 30, 35, 37, 2)
    steps(cells, xs + 31, 35, "east", 6, 2)
    land(cells, xs + 37, xs + 38, 35, 37, 8)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE)
    for x in range(xs + 30, xs + 40):
        for z in range(34, 39):
            edge = x in (xs + 30, xs + 39) or z in (34, 38)
            for y in range(7, 12):
                if y == 11:
                    C.set(x, y, z, DOAK if edge else "spruce_slab[type=bottom,waterlogged=false]")
                elif edge and y > 7:
                    C.set(x, y, z, SPRUCE)
    for z in (35, 36, 37):
        for y in (8, 9):
            C.air(xs + 39, y, z)
    C.set(xs + 35, 10, 36, LANT_H)
    # the galley (x -70..-60): range, pots, hams, shelves; the mess forward; the berths aft behind a partition
    for z in range(29, 44):
        if z not in (35, 36, 37):
            for y in range(2, 6):
                if C.get(xs + 24, y, z) == AIR:
                    C.set(xs + 24, y, z, SPRUCE)
    clear(C, xs + 24, xs + 24, 2, 3, 35, 37)
    for x in range(xs + 26, xs + 30):
        C.set(x, 2, 44, "smoker[facing=north,lit=true]" if x % 2 else "furnace[facing=north,lit=true]")
        C.set(x, 3, 44, SOOT)
        C.set(x, 4, 44, SOOT)
    for x in range(xs + 26, xs + 30, 2):
        C.set(x, 2, 42, "water_cauldron[level=3]")
        C.set(x + 1, 2, 42, "crafting_table")
    for (x, z) in ((xs + 27, 32), (xs + 31, 32), (xs + 27, 40)):
        for y in (5, 4):
            C.set(x, y, z, CHAIN) if y == 5 else C.set(x, y, z, "brown_terracotta")
    for x in range(xs + 26, xs + 35, 2):
        C.set(x, 4, 28 if C.get(x, 4, 28) == AIR else 29, f"{SHELF}[facing=south]")
    for x in range(xs + 32, xs + 36):
        C.set(x, 2, 40, "barrel[facing=up,open=false]")
    for x in range(xs + 37, xs + 43):
        C.set(x, 2, 31, TABLE)
        C.set(x, 2, 30, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]") if x % 2 else None
    C.set(xs + 29, 2, 33, MOD["waystone"])
    C.set(xs + 33, 5, 33, HANG_LAMP)
    C.set(xs + 40, 5, 35, HANG_LAMP)
    C.set(xs + 18, 5, 36, HANG_LAMP)
    # the berths aft
    for x in range(xs + 15, xs + 23, 3):
        for z in (30, 42):
            if C.get(x, 2, z) == AIR and C.get(x + 1, 2, z) == AIR:
                C.bp.bed(x, 2, z, "east", color="light_gray")
    C.bp.chest(xs + 14, 2, 36, "east", loot=LOOT + "if_berths")
    # the ice door: an iron door in the north flank (feet 2), its button inside
    dx = xs + 32
    for z in range(25, 30):
        for y in (2, 3):
            if z < 29:
                C.air(dx, y, z)
        C.set(dx, 1, z, SPRUCE)
    C.bp.door(dx, 2, 28, "north", wood="iron")
    C.set(dx + 1, 3, 29, "stone_button[face=wall,facing=south,powered=false]")
    C.set(dx + 1, 3, 28, SPRUCE)
    C.set(dx - 1, 2, 28, SPRUCE)
    C.set(dx - 1, 3, 28, SPRUCE)
    C.set(dx + 1, 2, 28, SPRUCE)
    C.set(dx, 4, 28, SPRUCE)
    # the quartermaster's store under the poop
    clear(C, xs + 13, xs + 13, 8, 9, 36, 36)
    C.set(xs + 13, 7, 36, SPRUCE)
    door(C, xs + 13, 8, 36, "east")
    C.set(xs + 14, 7, 36, SPRUCE) if C.get(xs + 14, 7, 36) is None else None
    C.bp.bed(xs + 4, 8, 33, "east", color="brown") if C.get(xs + 5, 8, 33) == AIR else None
    C.bp.chest(xs + 9, 8, 41, "north", loot=LOOT + "if_berths")
    C.set(xs + 10, 8, 31, "barrel[facing=up,open=false]")
    C.set(xs + 7, 11, 36, HANG_LAMP)
    portholes(C, S, xs + 15, xs + 42, 3, every=4)
    # masts, the crow's nest on the mainmast, a little funnel
    mast(C, S, xs + 24, 36, 8, 34, yards=((30, 7), (22, 9), (15, 8)), top="lightning_rod")
    mast(C, S, xs + 42, 36, 8, 30, yards=((26, 6), (19, 8)), top="lightning_rod")
    tan = S.sr / S.cr
    nz = int(round(36 + 31 * tan))
    for x in range(xs + 22, xs + 27):
        for z in range(nz - 2, nz + 3):
            C.set(x, 31, z, SPRUCE)
            if x in (xs + 22, xs + 26) or z in (nz - 2, nz + 2):
                C.set(x, 32, z, "spruce_fence")
            else:
                for y in (32, 33, 34):
                    if C.get(x, y, z) is None or (x, z) != (xs + 24, int(round(36 + (y - 8) * tan))):
                        C.air(x, y, z)
    C.bp.chest(xs + 25, 32, nz + 1, "west", loot=LOOT + "if_crowsnest")
    for y in range(8, 31):
        C.set(xs + 24, y, nz, SPRUCE) if C.get(xs + 24, y, nz) in (None, AIR) else None
    for y in range(8, 31):
        C.set(xs + 23, y, nz, "ladder[facing=west,waterlogged=false]")
    C.set(xs + 23, 31, nz, "spruce_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(8, 20):
        z = int(round(36 + y * tan))
        for x in (xs + 19, xs + 20):
            C.set(x, y, z, COPPER if y < 18 else SOOT)


def rope_bridge(C):
    """The rope bridge from the Fulmar's poop (stern) to the Petrel's forecastle: spruce slabs sagging between
    fence rails, chains for hand lines."""
    prof = {}
    xa, xb = -40, -24
    for x in range(xa, xb + 1):
        t = (x - xa) / float(xb - xa)
        prof[x] = 13.5 - round(2 * 1.0 * math.sin(math.pi * t)) / 2.0
    for x, f in prof.items():
        for z in (33, 34, 35):
            fy = int(math.floor(f))
            for y in range(fy - 1, fy + 4):
                if C.get(x, y, z) is not None or y >= fy:
                    C.air(x, y, z)
            if f == fy:
                C.set(x, fy - 1, z, slab("spruce_slab", "top"))
            else:
                C.set(x, fy, z, slab("spruce_slab"))
        for z in (32, 36):
            fy = int(math.ceil(f))
            C.set(x, fy, z, "spruce_fence")
            if x % 4 == 0:
                C.set(x, fy + 1, z, "spruce_fence")
    # cut the bulwarks at both ends
    for x in range(xa - 6, xa + 1):
        for z in (33, 34, 35):
            f = SA.feet(x, z)
            if f is not None:
                for y in range(int(math.floor(f)), int(math.floor(f)) + 4):
                    C.air(x, y, z)
    for x in range(xb, xb + 4):
        for z in (33, 34, 35):
            for y in range(13, 17):
                b = C.get(x, y, z)
                if b is not None and b != AIR:
                    C.air(x, y, z)
            if SB.feet(x, z) is None:
                C.set(x, 12, z, slab("spruce_slab", "top")) if x > xb else None


# ------------------------------------------------------------------ the camps
def hut(C, x0, z0, w, d, door_side, kind, loot=None, spawner=None):
    """A prefab expedition hut on the ice: timber frame, insulated plank walls, a pitched roof under snow, a
    stove pipe; furnished by ``kind`` (lab, mess, bunk, depot)."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            C.set(x, 0, z, SPRUCE)
            for y in range(1, 5):
                if corner:
                    C.set(x, y, z, log("dark_oak_log", "y"))
                elif edge:
                    C.set(x, y, z, "glass_pane" if y == 2 and (x + z) % 3 == 0 and not (x in (x0, x1) and
                          z in (z0, z1)) else (DOAK if y == 4 else SPRUCE))
                else:
                    C.air(x, y, z)
            C.set(x, 4, z, DOAK) if not edge else None
    gable(C, x0, x1, z0, z1, 5, "spruce_stairs", ridge="x" if w >= d else "z")
    for x in range(x0, x1 + 1):          # the loft under the roof: stacked stores (no sealed air pocket)
        for z in range(z0, z1 + 1):
            top = next((y for y in range(12, 4, -1) if C.get(x, y, z) is not None), 4)
            for y in range(5, top):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, "spruce_planks" if (x + y + z) % 4 else "hay_block")
    # door
    if door_side == "south":
        dx, dz = (x0 + x1) // 2, z1
    elif door_side == "north":
        dx, dz = (x0 + x1) // 2, z0
    elif door_side == "east":
        dx, dz = x1, (z0 + z1) // 2
    else:
        dx, dz = x0, (z0 + z1) // 2
    door(C, dx, 1, dz, door_side)
    ox, oz = DIRV[door_side]
    C.set(dx + ox, 0, dz + oz, SPRUCE)
    C.air(dx + ox, 1, dz + oz)
    C.air(dx + ox, 2, dz + oz)
    # stove pipe
    sx, sz = x0 + 1, z0 + 1
    C.set(sx, 1, sz, "furnace[facing=south,lit=true]")
    for y in range(2, 9):
        C.set(sx, y, sz, IRON_WALL if y > 1 else SOOT)
    C.set((x0 + x1) // 2, 3, (z0 + z1) // 2, HANG_LAMP)
    ix, iz = x1 - 1, z1 - 1 if door_side != "south" else z0 + 1
    if kind == "lab":
        C.set(x1 - 1, 1, z0 + 1, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
        C.set(x1 - 2, 1, z0 + 1, "cartography_table")
        C.set(x1 - 3, 1, z0 + 1, TABLE)
        C.set(x0 + 1, 2, z1 - 1, GAUGE) if C.get(x0 + 1, 2, z1 - 1) == AIR else None
        C.set(x0 + 2, 1, z1 - 1, "lectern[facing=north,has_book=false,powered=false]")
    elif kind == "mess":
        for x in range(x0 + 2, x1 - 1):
            C.set(x, 1, (z0 + z1) // 2, TABLE)
        C.set(x1 - 1, 1, z1 - 1, "barrel[facing=up,open=false]")
        C.set(x1 - 1, 1, z0 + 1, "smoker[facing=west,lit=true]")
    elif kind == "bunk":
        for x in range(x0 + 2, x1 - 1, 2):
            if door_side == "north":
                C.bp.bed(x, 1, z1 - 2, "south", color="blue")
            else:
                C.bp.bed(x, 1, z0 + 1, "south", color="blue")
    elif kind == "depot":
        C.set(x1 - 1, 1, z1 - 1, "barrel[facing=up,open=false]")
        C.set(x1 - 1, 2, z1 - 1, "barrel[facing=up,open=false]")
    if loot:
        lx, lz = (x1 - 1, z1 - 1) if kind != "bunk" else (x1 - 1, (z0 + z1) // 2)
        if C.get(lx, 1, lz) == AIR:
            C.bp.chest(lx, 1, lz, "west", loot=LOOT + loot)
        else:
            C.bp.chest(x0 + 1, 1, z1 - 1, "east", loot=LOOT + loot)
    if spawner:
        C.bp.spawner((x0 + x1) // 2, 1, (z0 + z1) // 2 + 1, spawner)


def sledge(C, x, z, axis="x"):
    """A dog sledge: runners of dark oak, a slab bed, a lashed load."""
    for k in range(5):
        xx, zz = (x + k, z) if axis == "x" else (x, z + k)
        C.set(xx, 1, zz, slab("spruce_slab"))
        if k in (1, 2, 3):
            C.set(xx, 2, zz, "brown_wool" if k != 2 else "barrel[facing=up,open=false]") if k != 3 else None
    xx, zz = (x + 5, z) if axis == "x" else (x, z + 5)
    C.set(xx, 1, zz, "spruce_fence")


def tent(C, x0, z0, ln, axis="x"):
    """A canvas ridge tent."""
    for k in range(ln):
        for j in range(3):
            for s in (-1, 1):
                xx, zz = (x0 + k, z0 + s * (2 - j)) if axis == "x" else (x0 + s * (2 - j), z0 + k)
                C.set(xx, 1 + j, zz, "white_wool" if (k + j) % 3 else "light_gray_wool")
        xx, zz = (x0 + k, z0) if axis == "x" else (x0, z0 + k)
        C.set(xx, 4, zz, "white_wool")
        for y in (1, 2, 3):
            if C.get(xx, y, zz) is None:
                C.air(xx, y, zz)


def sledge_camp(C):
    """The sledge camp where the approach starts: two tents, sledges, the fire, crates, a flag, the waystone."""
    cx, cz = CAMP
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if math.hypot(x - cx, (z - cz) * 1.2) < 7 and C.get(x, 0, z) is not None:
                C.set(x, 0, z, "white_concrete_powder" if hash01(x, z, 101) < 0.5 else PICE)
    tent(C, cx + 1, cz - 3, 6)
    tent(C, cx - 6, cz + 4, 5, axis="z")
    C.bp.bed(cx + 3, 1, cz - 3, "east", color="brown")
    sledge(C, cx - 5, cz - 4)
    sledge(C, cx + 2, cz + 3)
    C.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((cx - 2, cz - 1), (cx - 2, cz + 1), (cx + 2, cz + 1)):
        C.set(x, 1, z, "spruce_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]" %
              ("east" if x < cx else "west"))
    C.bp.chest(cx + 5, 1, cz + 1, "west", loot=LOOT + "if_camp")
    C.set(cx - 3, 1, cz + 3, MOD["waystone"])
    for y in range(1, 7):
        C.set(cx + 6, y, cz - 6, "spruce_fence")
    C.set(cx + 6, 7, cz - 6, "red_banner[rotation=4]")
    C.set(cx - 1, 1, cz - 5, IRON_WALL)
    C.set(cx - 1, 2, cz - 5, LANT)


def drilling_camp(C):
    """The hub: the brass ice-drill derrick over its borehole, the drill floor, the draw-works and the engine house
    (its boiler smoking), the pipe rack and the ice-core racks, the huts round the waystone."""
    dx, dz = DER
    # the drill floor (feet 4) on posts, the stair from the ice (west)
    for x in range(dx - 7, dx + 8):
        for z in range(dz - 7, dz + 8):
            C.set(x, 3, z, TREAD if (x + z) % 5 else BRASS)
            for y in (4, 5, 6):
                C.air(x, y, z)
            if (x - dx) % 4 == 3 and (z - dz) % 4 == 3 or (abs(x - dx) == 7 and abs(z - dz) == 7):
                for y in (1, 2):
                    C.set(x, y, z, log("spruce_log", "y"))
    for x in range(dx - 7, dx + 8):
        for z in (dz - 7, dz + 7):
            C.set(x, 4, z, IRON_WALL)
    for z in range(dz - 7, dz + 8):
        if abs(z - dz) > 1:
            C.set(dx - 7, 4, z, IRON_WALL)
        C.set(dx + 7, 4, z, IRON_WALL)
    cells = {}
    land(cells, dx - 11, dx - 11, dz - 1, dz + 1, 1)
    steps(cells, dx - 10, dz - 1, "east", 3, 1)
    wsteps(C, cells, tread="spruce_stairs", floor=SPRUCE, fill=SPRUCE, solid_to=0)
    # the borehole: water down through the ice, a brass casing collar, the drill string
    for x in range(dx - 1, dx + 2):
        for z in range(dz - 1, dz + 2):
            for y in range(-5, 1):
                C.set(x, y, z, WATER)
            C.air(x, 1, z)
            C.air(x, 2, z)
            C.air(x, 3, z)
    for x in range(dx - 2, dx + 3):
        for z in range(dz - 2, dz + 3):
            if max(abs(x - dx), abs(z - dz)) == 2:
                C.set(x, 4, z, IRON_WALL)
    for y in range(-5, 44):
        C.set(dx, y, dz, BRASS if y % 5 else GEAR)
    # the derrick: four brass legs tapering to the crown, girders every 8, the monkey board and crown platform
    for y in range(4, 45):
        a = 6 - 4.5 * (y - 4) / 40.0
        for sx in (-1, 1):
            for sz in (-1, 1):
                C.set(int(round(dx + sx * a)), y, int(round(dz + sz * a)), BRASS)
        if y % 8 == 4 and y > 4:
            ai = int(round(a))
            for k in range(-ai, ai + 1):
                for (x, z) in ((dx + k, dz - ai), (dx + k, dz + ai), (dx - ai, dz + k), (dx + ai, dz + k)):
                    if C.get(x, y, z) is None:
                        C.set(x, y, z, COPPER if k % 2 else IRON_WALL)
    # the ladder up the west face (spine of dark iron), rest decks at 14 and 26, the crown deck at 37
    lx, lz = dx - 3, dz
    for y in range(4, 38):
        C.set(lx + 1, y, lz, IRON_BR) if C.get(lx + 1, y, lz) in (None, AIR) else None
        C.set(lx, y, lz, "ladder[facing=west,waterlogged=false]")
    for (yy, r) in ((14, 4), (26, 3), (37, 2)):
        for x in range(lx - 2, lx):
            for z in range(lz - 1, lz + 2):
                C.set(x, yy - 1, z, TREAD)
                for y in (yy, yy + 1, yy + 2):
                    if C.get(x, y, z) is None:
                        C.air(x, y, z)
        for z in range(lz - 2, lz + 3):
            C.set(lx - 3, yy, z, IRON_WALL)
        for x in range(lx - 3, lx):
            C.set(x, yy, lz - 2, IRON_WALL)
            C.set(x, yy, lz + 2, IRON_WALL)
    C.bp.chest(lx - 2, 37, lz + 1, "east", loot=LOOT + "if_derrick")
    # the crown block, a lamp and a pennant
    for x in range(dx - 1, dx + 2):
        for z in range(dz - 1, dz + 2):
            C.set(x, 45, z, IRON if (x, z) != (dx, dz) else GEAR)
    C.set(dx, 46, dz, BRASS)
    C.set(dx, 47, dz, EDISON)
    C.set(dx, 48, dz, "lightning_rod")
    # the draw-works drum on the floor, the engine house east
    for z in range(dz + 3, dz + 6):
        C.set(dx + 4, 4, z, log("stripped_dark_oak_log", "z"))
        C.set(dx + 4, 5, z, log("stripped_dark_oak_log", "z"))
    C.set(dx + 5, 4, dz + 3, GEAR)
    ex0, ez0 = dx + 9, dz - 4
    for x in range(ex0, ex0 + 8):
        for z in range(ez0, ez0 + 9):
            edge = x in (ex0, ex0 + 7) or z in (ez0, ez0 + 8)
            C.set(x, 0, z, IRON)
            for y in range(1, 6):
                if edge:
                    C.set(x, y, z, "glass_pane" if y == 3 and (x + z) % 3 == 0 else (IRON if y < 5 else BRASS))
                else:
                    C.air(x, y, z)
            C.set(x, 6, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
    for y in (1, 2, 3):
        C.air(ex0, y, dz)
    C.set(ex0, 1, dz, AIR)
    door(C, ex0, 1, dz, "west")
    for x in range(ex0 + 3, ex0 + 7):
        for z in range(ez0 + 5, ez0 + 8):
            for y in range(1, 4):
                if (x - ex0 - 4.5) ** 2 + (y - 2) ** 2 <= 2.4:
                    C.set(x, y, z, COPPER if z != ez0 + 6 else BRASS)
    C.set(ex0 + 2, 1, ez0 + 6, "blast_furnace[facing=east,lit=true]")
    C.set(ex0 + 3, 1, ez0 + 2, GEAR)
    C.set(ex0 + 4, 1, ez0 + 2, PIPES)
    C.set(ex0 + 5, 2, ez0 + 1, GAUGE)
    C.set(ex0 + 2, 1, ez0 + 1, "barrel[facing=up,open=false]")
    C.set(ex0 + 4, 4, dz, HANG_LAMP)
    for y in range(6, 18):
        for (x, z) in ((ex0 + 5, ez0 + 6),):
            C.set(x, y, z, SOOT if y < 16 else BRASS)
    C.set(ex0 + 5, 18, ez0 + 6, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # the pipe rack and the ice-core racks
    for x in range(dx - 10, dx - 2):
        C.set(x, 1, dz + 10, log("spruce_log", "x") if x % 3 == 0 else "air")
        for k, z in enumerate((dz + 9, dz + 11)):
            C.set(x, 1, z, "spruce_fence") if x % 3 == 0 else None
            C.set(x, 2, z, BRASS if (x + k) % 2 else COPPER)
    for x in range(28, 37, 2):
        for y in (1, 2, 3):
            C.set(x, y, -8, BICE if (x + y) % 3 else PICE)
        C.set(x, 1, -9, "spruce_fence")
        C.set(x + 1, 1, -8, "spruce_fence") if x < 36 else None
    # huts and the waystone
    hut(C, 24, 0, 9, 7, "south", "lab", loot="if_hub")
    hut(C, 27, 22, 9, 7, "north", "mess", loot="if_hub")
    hut(C, 44, 22, 7, 7, "north", "bunk")
    hut(C, 16, 9, 6, 7, "east", "depot", spawner=None)
    hx, hz = HUB
    for x in range(hx - 3, hx + 4):
        for z in range(hz - 3, hz + 4):
            if math.hypot(x - hx, z - hz) < 3.5:
                C.set(x, 0, z, BRASS if math.hypot(x - hx, z - hz) < 1.5 else TREAD)
                for y in (1, 2, 3):
                    if C.get(x, y, z) is None:
                        C.air(x, y, z)
    C.set(hx, 1, hz, MOD["waystone"])
    for (x, z) in ((hx - 3, hz - 3), (hx + 3, hz + 3), (hx - 3, hz + 3), (hx + 3, hz - 3)):
        for y in (1, 2):
            C.set(x, y, z, IRON_WALL)
        C.set(x, 3, z, LANT)
    sledge(C, 20, 18, axis="x")
    sledge(C, 18, 4, axis="z")
    for y in range(1, 9):
        C.set(hx + 6, y, hz - 6, "spruce_fence")
    C.set(hx + 6, 9, hz - 6, "blue_banner[rotation=8]")


def whale(C):
    """A whale skeleton frozen into the ice across the track: spine arched 9 high, ribs down both sides, a broken
    rib where the track passes under the spine, the skull and its jawbones, ice crusted over the feet of the ribs."""
    ax, az = 0.73, -0.68                     # the spine's direction (tail -> snout)
    nx, nz = -az, ax                         # across
    cx, cz = WHALE_C
    u_cross = 14

    def W_(u, s):
        return cx + (u - u_cross) * ax + s * nx, cz + (u - u_cross) * az + s * nz

    def put(px, py, pz, spec="bone_block[axis=y]"):
        C.set(int(round(px)), int(round(py)), int(round(pz)), spec)

    def spine_h(u):
        if u < 8:
            return 1 + u
        if u < 22:
            return 9
        return max(2, 9 - (u - 22) * 0.6)

    for i in range(0, 340):
        u = i / 10.0
        px, pz = W_(u, 0)
        put(px, spine_h(u), pz)
        if i % 20 == 0 and u < 24:
            put(px, spine_h(u) + 1, pz)
    for u in range(9, 22, 2):
        if u in (13, 15):
            continue                        # the broken rib (the track goes through here)
        for side in (-1, 1):
            half = 7.5
            for k in range(0, 41):
                a = math.pi * k / 80.0
                s = side * half * math.sin(a)
                y = spine_h(u) * math.cos(a)
                px, pz = W_(u, s)
                if y >= 0.5:
                    put(px, y, pz)
            fx, fz = W_(u, side * half)
            for y in (1, 2):
                for dd in (-1, 0, 1):
                    q = (int(round(fx + dd * ax)), y, int(round(fz + dd * az)))
                    if C.get(*q) is None and hash01(q[0], q[2], 111) < 0.8:
                        C.set(*q, PICE if y == 1 else SNOW)
    # the broken rib's stump and its fallen half
    for side in (-1, 1):
        for k in range(0, 8):
            a = math.pi * k / 80.0
            px, pz = W_(13, side * 7.5 * math.sin(a))
            put(px, 9 * math.cos(a), pz)
    for k in range(5):
        px, pz = W_(16 + k * 0.3, 9 + k)
        put(px, 1, pz, "bone_block[axis=x]")
    # the skull (u 24..34): cranium raised on the jawbones, eye sockets
    for u10 in range(240, 345, 5):
        u = u10 / 10.0
        w = 4.5 - (u - 24) * 0.3
        for s10 in range(int(-w * 10), int(w * 10) + 1, 5):
            s = s10 / 10.0
            px, pz = W_(u, s)
            top = 6 - (u - 24) * 0.35 - (s / max(w, 1)) ** 2 * 2
            put(px, max(2, top), pz)
        for side in (-1, 1):
            px, pz = W_(u, side * (5.5 - (u - 24) * 0.35))
            put(px, 1, pz, "bone_block[axis=x]")
    for side in (-1, 1):
        px, pz = W_(26, side * 3)
        C.set(int(round(px)), 5, int(round(pz)), AIR)
    # tail flukes and a flipper on the ice
    for k in range(-4, 5):
        px, pz = W_(0, k)
        put(px, 1, pz, "bone_block[axis=x]")
    for k in range(6):
        px, pz = W_(11 + k * 0.5, -9 - k)
        put(px, 1, pz, "bone_block[axis=x]")
    # the frozen-over crust along the spine's foot, a lost explorer's pack inside the ribcage
    px, pz = W_(19, 3)
    C.bp.chest(int(round(px)), 1, int(round(pz)), "west", loot=LOOT + "if_whale")
    px, pz = W_(18, -3)
    C.set(int(round(px)), 1, int(round(pz)), "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,"
                                            "waterlogged=false]")
    C.bp.spawner(int(round(W_(10, 2)[0])), 1, int(round(W_(10, 2)[1])), MOB_STRAY)


# ------------------------------------------------------------------ links: the trench, the slide, the crane pool
def trench(C):
    """The snow trench from the Petrel's ice door to the icebreaker's breach: snow banks, plank-and-canvas roofs
    over half of it, sinking under the ice for its last stretch (packed-ice walls, a plank roof under snow)."""
    pts = PATHS[4][0]
    half = 1.6
    cells = {}
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 3))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            for x in range(int(px) - 3, int(px) + 4):
                for z in range(int(pz) - 3, int(pz) + 4):
                    d = math.hypot(x - px, z - pz)
                    if d <= half:
                        cells[(x, z)] = min(cells.get((x, z), 9), 0)
                    elif d <= half + 1.3 and (x, z) not in cells:
                        cells.setdefault((x, z), 1)

    def floor_at(z):
        if z >= -12:
            return 1
        if z <= -18:
            return -2
        return 1 - int((-12 - z) / 2.0 + 0.5)

    for (x, z), k in cells.items():
        f = floor_at(z)
        if k == 0:
            for y in range(f, 4 if f < 1 else 4):
                C.air(x, y, z)
            C.set(x, f - 1, z, PICE if f < 1 else ("white_concrete_powder" if hash01(x, z, 121) < 0.6 else PICE))
            roofed = (z < -13) or (-2 < z < 10)
            if roofed:
                C.set(x, 4, z, slab("spruce_slab", "top") if f >= 1 else SPRUCE)
                C.set(x, 5, z, SNOW)
        else:
            if (x, z) in cells and cells[(x, z)] == 0:
                continue
            top = 3 + (1 if hash01(x, z, 122) < 0.4 else 0)
            for y in range(min(f, 1) - 1, top + 1):
                if C.get(x, y, z) in (None, AIR, "minecraft:" + SNOW, "minecraft:" + PICE, "minecraft:ice",
                                      "minecraft:" + BICE):
                    if (x, y, z) in C.inner:
                        continue
                    C.set(x, y, z, PICE if y <= 1 else SNOW)
    # the descent steps (packed ice stairs) where the floor drops
    for (x, z), k in cells.items():
        if k:
            continue
        f = floor_at(z)
        if f < 1 and floor_at(z - 1) < f:
            C.set(x, f - 1, z, "spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for z in (-6, 4, 14):
        x = int(round(-66 + (0 if z > 2 else 0)))
        C.set(x - 2, 3, z, LANT) if C.get(x - 2, 3, z) not in (None, AIR) else None
    for z in (-15, -21):
        C.set(-63, 3, z, SOUL_H) if C.get(-63, 4, z) not in (None, AIR) else None


def ice_slide(C):
    """The ice slide from the strongroom's bow breach: four blue-ice runs, each dropping two blocks (no way back
    up), walled in packed ice, down to the ice by the drilling camp."""
    segs = [(range(-28, -24), 7), (range(-24, -19), 5), (range(-19, -14), 3), (range(-14, -9), 1)]
    for zr, f in segs:
        for z in zr:
            for x in range(25, 30):
                wall = x in (25, 29)
                for y in range(0, f - 1):
                    C.set(x, y, z, PICE)
                if wall:
                    for y in range(f - 1, f + 2):
                        C.set(x, y, z, PICE if y < f + 1 else SNOW)
                else:
                    C.set(x, f - 1, z, BICE)
                    for y in range(f, f + 3):
                        C.air(x, y, z)
    # the platform under the breach joins the first run
    for x in range(26, 29):
        for z in range(-31, -27):
            if C.get(x, 6, z) is None or C.get(x, 6, z) in ("minecraft:" + SNOW, "minecraft:" + PICE):
                C.set(x, 6, z, BICE)
            for y in range(1, 6):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, PICE)
            for y in range(7, 10):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
    for z in range(-31, -27):
        for x in (25, 29):
            for y in range(1, 9):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, PICE if y < 8 else SNOW)


def crane_pool(C):
    """The fishing hole under the crane jib: four deep, the trench a step away."""
    for x in range(-63, -55):
        for z in range(-12, -5):
            if math.hypot(x + 59, z + 9) > 3.9:
                continue
            for y in range(-4, 1):
                C.set(x, y, z, WATER)
            for y in (1, 2, 3):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
    for x in range(-64, -62):
        for z in range(-10, -7):
            C.set(x, 0, z, PICE)
            for y in (1, 2, 3):
                C.air(x, y, z)


def bow_rail(C):
    """A dark-iron rail along the forecastle bulwark caps: nobody walks the cap round the arena and drops overboard
    into the ram's breach (the strongroom stays behind its sealed bars)."""
    for x in range(X(74), X(LEN) + 2):
        u = x - XS
        for z in range(Z(-19), Z(20)):
            for y in range(20, 11, -1):
                _, v, h = IB.local(x, y, z)
                w = IB.hw(u, min(h, IB.top(u) - 0.5))
                if w <= 0 or abs(v) < w - 1.6 or abs(v) > w + 0.6:
                    continue
                b = C.get(x, y, z)
                if b not in (None, AIR):
                    if C.get(x, y + 1, z) in (None, AIR) and C.get(x, y + 2, z) in (None, AIR):
                        C.set(x, y + 1, z, IRON_WALL)
                    break


STAIRS = []


def wsteps(C, cells, **kw):
    """write_steps, remembered: every flight is written again at the end so later rooms cannot block it."""
    STAIRS.append((dict(cells), kw))
    write_steps(C, cells, **kw)


def restairs(C):
    for cells, kw in STAIRS:
        write_steps(C, cells, **kw)
    STAIRS.clear()


def fill_holds(C):
    """Unwritten cells inside a hull above the ice (between the rooms and under the decks) would keep the world's
    air: pack them with ballast (iron in the icebreaker, timber in the supply ships)."""
    for S, spec in ((IB, IRON), (SB, DOAK), (SA, DOAK)):
        z0, z1 = int(math.floor(S.zc - S.hb - 2)), int(math.ceil(S.zc + S.hb + 2))
        for x in range(S.xs, S.xs + S.L + 1):
            for z in range(z0, z1 + 1):
                for y in range(1, int(S.tmax) + 2):
                    if C.get(x, y, z) is None and S.inside(x, y, z, 0.0):
                        C.set(x, y, z, spec)


def seal(C):
    """Every air or water cell under the ice gets solid neighbours (dark iron in the hulls, timber in the supply
    ships, packed ice outside) so the sea never floods a room, the trench or the hold."""
    todo = [p for p in C.inner if p[1] <= 0 and C.get(*p) == AIR]
    for (x, y, z) in todo:
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
            q = (x + dx, y + dy, z + dz)
            if C.get(*q) is None:
                if IB.plan(q[0], q[2], q[1]):
                    C.set(*q, IRON_BR)
                elif SB.plan(q[0], q[2], q[1]) or SA.plan(q[0], q[2], q[1]):
                    C.set(*q, DOAK)
                else:
                    C.set(*q, PICE)


# ------------------------------------------------------------------ the whole site
def icebound_fleet(bp):
    C = Ctx(bp)
    ice_field(C)
    lead(C, [(42, -40), (52, -35), (66, -42), (84, -33), (104, -38)], half=1.6, seed=131)
    lead(C, [(-82, -40), (-96, -50), (-108, -45)], half=1.3, seed=132)
    lead(C, [(-30, 60), (-12, 72), (6, 66), (22, 80)], half=1.0, seed=133)
    ridge(C, [(104, 24), (82, 27), (64, 33), (52, 37), (40, 40), (22, 48), (4, 58)], 8, 141, gaps=((52, 36, 4.5),))
    ridge(C, [(46, -48), (60, -54), (80, -48), (100, -56)], 7, 142)
    ridge(C, [(-104, -14), (-92, 2), (-102, 22)], 6, 143)
    ridge(C, [(-64, 72), (-34, 82), (-4, 78), (28, 92)], 6, 144)
    ridge(C, [(-36, 2), (-18, -6), (2, -2)], 4, 145)
    for (x, z, r, h, lean, s) in ((78, -72, 5, 32, (0.6, 0.3), 1), (98, -20, 4, 24, (-0.4, 0.5), 2),
                                  (-104, -40, 5, 28, (0.5, 0.2), 3), (-22, -84, 4, 22, (0.2, 0.6), 4),
                                  (12, 88, 4, 20, (-0.5, -0.2), 5), (-74, 84, 3, 18, (0.3, -0.4), 6),
                                  (-44, -80, 6, 36, (0.4, 0.4), 7), (22, -64, 4, 26, (-0.3, 0.5), 8),
                                  (100, 4, 3, 16, (0.2, 0.2), 9)):
        spire(C, x, z, r, h, lean, s)
    # the bow ridden up on a heap of broken floes (kept clear of the slide)
    for x in range(30, 50):
        for z in range(-54, -26):
            u, v, h = IB.local(x, 2, z)
            d = math.hypot((x - 40) / 1.2, z - ZC)
            if d > 14 or (24 <= x <= 31 and z > -33):
                continue
            if abs(v) < IB.hw(u, 2) + 0.3:
                continue
            top = int(5 * (1 - d / 14.0) + 2 * hash01(x, z, 151))
            for y in range(1, top + 1):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, BICE if hash3(x, y, z, 152) < 0.25 else PICE)
    # the icebreaker
    icebreaker_hull(C)
    paddle_wheels(C)
    aft_bunker(C)
    boiler_room(C)
    crew_deck(C)
    engineers(C)
    strongroom(C)
    bridge_house(C)
    officers_mess(C)
    captains_deck(C)
    boat_deck(C)
    funnels(C)
    deck_fittings(C)
    # the supply ships and the bridge between them
    fulmar(C)
    petrel(C)
    rope_bridge(C)
    # the camps and the whale
    for pts, half in PATHS[:4]:
        path_line(C, pts, half=half)
    whale(C)
    drilling_camp(C)
    sledge_camp(C)
    trench(C)
    ice_slide(C)
    crane_pool(C)
    drifts(C)
    restairs(C)
    bow_rail(C)
    fill_holds(C)
    seal(C)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("boiler_room", (X(55), -2, Z(0)), (X(28), -8, Z(0))),
    ("crew_mess", (X(70), 5, Z(-12)), (X(60), 6, Z(4))),
    ("officers_mess", (X(71), 12, Z(-12)), (X(62), 13, Z(-4))),
    ("captain_cabin", (X(71), 18, Z(3)), (X(62), 19, Z(-6))),
    ("wheelhouse", (X(63), 24, Z(-7)), (X(70), 25, Z(0))),
    ("galley", (SA.xs + 40, 2, 38), (SA.xs + 27, 3, 42)),
    ("frozen_hold", (10, -5, 32), (-8, -4, 32)),
    ("chart_room", (-13, 8, 33), (-21, 9, 31)),
]

register(StructureDef(
    "icebound_fleet", "overworld", ["frozen_ocean", "deep_frozen_ocean", "ice_spikes", "snowy_plains", "snowy_beach"],
    [Piece("fleet", icebound_fleet, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_STRAY, 8, 1, 2), (MOB_MITE, 3, 1, 2), (MOB_DRONE, 2, 1, 1)],
    title_fr="La Flotte prise dans les glaces", title_en="The Icebound Fleet"))
