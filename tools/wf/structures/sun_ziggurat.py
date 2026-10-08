"""Sun-Engine Ziggurat (La Ziggourat du Moteur solaire): a seven-step pyramid of mud brick and sandstone 141 blocks
wide and 70 high on the open desert, crowned by a colossal brass orrery whose sun hangs over a glass lens; the lens
throws the daylight down a shaft into the sun chamber under the summit, where the guardian sleeps. Colossal tier
(tools/BUILDING.md §1, §12 concept 15, §10 legacy-dungeon template, §15), steampunk accents (tools/STYLE_STEAMPUNK.md:
brass cornices, sphinxes and gate leaves, copper engine, amber light).

Silhouette (one noun phrase, §15.1): a stepped sand-coloured pyramid with a brass tripod orrery on its flat top, a
twin-towered pylon gate half-way up its south face at the end of a sphinx-lined stair, and a domed lens-keepers' tower
on its south-west shoulder.

Layout, ground y = 0 (feet 1), x east, z south; the pyramid is centred on (0, 0). Terraces (half width, top block):
T0 (70, 9), T1 (60, 21), T2 (50, 32), T3 (40, 43), T4 (31, 53), T5 (23, 62), summit (15, 70); each riser is a shell
3 thick (pilasters, niches, a brass cornice, corner pinnacles), the core is unset (in game: whatever was there).
  * the approach (south): two obelisks frame the avenue at z 148 beside the caravan camp and its waystone; five
    pairs of brass sphinxes line the avenue to the processional stair (three flights, a sphinx pair on every
    landing), which runs straight up the south face over the T0 terrace (an underpass keeps the terrace walk) to the
    pylon gate on the T1 terrace (feet 22): colossal brass leaves 7 x 14 with a wicket;
  * the gate hall, the hall of offerings and a narrow passage (compression) into the hypostyle hall: 49 x 49, 17 high,
    5 x 5 columns with brass lotus capitals and architraves, the central column a glowing sun conduit, a starry
    ceiling, the sun-engine wheel at the end of the axis (site of grace: the hub);
  * the side route: a breach in the south-west foot of the plinth lets the desert into the sand-flooded lower halls
    (feet 1): the collapsed vestibule (a fallen sphinx head), the granary, the dry cistern, the shrine of the buried
    sun, the hall of sand under the hypostyle (columns half buried) and the old engine hall (copper boiler); a newel
    stair climbs from the hall of sand into the hypostyle hall;
  * from the hypostyle two stairs climb to balconies along its side walls (vistas over the columns): east, the
    astronomer-priests' quarter (refectory, dormitory, star-chart room, scriptorium, armillary study); west, a robbers'
    breach into the sealed tomb gallery (sarcophagi in niches) and the astronomer-king's inner tomb (secret, tier 2-3);
  * the star-chart room opens onto the T2 terrace: the climb goes outside, round the pyramid, by stairs set along the
    risers (T2 -> T3 east face, T3 -> T4 and T4 -> T5 south face), the orrery looming overhead, to the lens gate in
    the summit; the lens-calibration chamber rings the light shaft under the lens; a stair to the summit itself (the
    orrery, the lens, a chest: optional climb);
  * the lens-keepers' tower (south-west shoulder) holds a newel stair down 18 to the antechamber (site of grace), a
    corridor (compression) and the mist into the sun chamber: the boss arena (radius 16, a dome 17 high, the light
    shaft landing on the sun disc at its centre); north, the vault behind sealed bars and the sun lift;
  * shortcuts (§10.4): the sun lift (a 44-block drop well into a pool and a bubble-column tube back up) from the vault
    to the lift hall under the hypostyle, its iron door opening into the hall of sand from the lift side only; the
    lower halls' iron door to the foot of the processional stair (opens from inside); the tomb gallery's iron door
    onto the T2 terrace; the lens-keepers' tower door onto the T4 terrace; the side-route newel; terrace stairs on
    every face give each storey two links.
Loot gradient (§15.6): camp, lower halls, gate and offerings tier 1; priests' quarter 1-2; tomb gallery and
calibration chamber 2; inner tomb and summit 2-3 (secret, optional climb); the vault 3.
Height budget: the orrery's apex stands 101 above the ground layer.
"""
import math

import numpy as np

from ..arch import stair
from ..blueprint import is_solid
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, IRON, IRON_SLAB, IRON_STAIRS,
                       IRON_WALL, MAHOGANY, MAHOGANY_STAIRS, TABLE, VERD, W, hash01, hash3, is_air)
from ..parts import LOOT, MOD

# the ziggurat's own guardian: the Solar Hierarch keeps the lens chamber (SolarHierarch.java)
BOSS = "brasshaven:solar_hierarch"
MOB_HUSK = "minecraft:husk"
MOB_CRAWLER = W + "crypt_crawler"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"

# ------------------------------------------------------------------ dimensions
TIERS = ((70, 9), (60, 21), (50, 32), (40, 43), (31, 53), (23, 62), (15, 70))   # (half width, top block)
RMAX = 70
FH, FQ, FA, FL, FS = 22, 33, 45, 63, 71      # feet: hypostyle, quarter / tomb, arena, lens chamber, summit
SX0, SX1, SZ0, SZ1 = -92, 92, -92, 150       # site
HALL = 24                                    # hypostyle interior |x|, |z| <= 24, air y 22..38
HALL_TOP = 38
COLS = (-18, -9, 0, 9, 18)
AR_R, AR_W = 16.4, 18.6                      # arena floor radius, outer radius of its wall
AR_WALL, AR_TOP = 55, 61                     # arena wall top, dome apex (air)
NEWEL_A = (-20, 20)                          # lens-keepers' tower newel (feet 45 -> 63)
NEWEL_B = (30, -18)                          # hall of sand -> hypostyle newel (feet 1 -> 22)
ANNEX = (-25, 9, -11, 25)                    # lens-keepers' tower walls x0, z0, x1, z1
AVENUE = (106, 115, 124, 133, 142)           # avenue sphinx pairs (z)

SS, CUT, SMO, CHIS = "sandstone", "cut_sandstone", "smooth_sandstone", "chiseled_sandstone"
SS_ST, SMO_ST, CUT_SL, SMO_SL = "sandstone_stairs", "smooth_sandstone_stairs", "cut_sandstone_slab", \
    "smooth_sandstone_slab"
SS_W, MUD_W = "sandstone_wall", "mud_brick_wall"
MUD, PMUD, MUD_ST = "mud_bricks", "packed_mud", "mud_brick_stairs"
TERRA, OTERRA, BTERRA, YTERRA = "terracotta", "orange_terracotta", "brown_terracotta", "yellow_terracotta"
BLUE_T = "blue_terracotta"
SAND = "sand"
GOLD = "gold_block"
ENGR, GILD, BTILE = W + "engraved_brass", W + "gilded_trim", W + "brass_tiles"
GLASS_Y, GLASS_O = "yellow_stained_glass", "orange_stained_glass"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
AIR = "minecraft:air"
WATER = "water"
FACES = ("south", "north", "east", "west")
CORN_CCW = ((1, -1), (-1, -1), (-1, 1), (1, 1))   # NE, NW, SW, SE


# ------------------------------------------------------------------ geometry
def cheb(x, z):
    return max(abs(x), abs(z))


def tier_of(r):
    """Index of the tier whose terrace or riser column r belongs to (-1 outside the plinth)."""
    for k in range(len(TIERS) - 1, -1, -1):
        if r <= TIERS[k][0]:
            return k
    return -1


def ptop(x, z):
    k = tier_of(cheb(x, z))
    return TIERS[k][1] if k >= 0 else 0


def in_mass(x, y, z):
    r = cheb(x, z)
    return r <= RMAX and 0 <= y <= ptop(x, z)


def fxz(face, u, r):
    if face == "south":
        return u, r
    if face == "north":
        return u, -r
    if face == "east":
        return r, u
    return -r, u


def along(face, d):
    if face in ("south", "north"):
        return "east" if d > 0 else "west"
    return "south" if d > 0 else "north"


OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ materials
def body(x, y, z):
    """The pyramid's masonry: dark mud brick at the foot, warm sandstone in the body, sun-bleached smooth stone at the
    crown (the band boundaries jittered, §5)."""
    h = hash3(x, y, z, 11)
    f = y / 70.0 + (hash01(x // 3 + y * 5, z // 3 - y * 3, 12) - 0.5) * 0.08
    if f < 0.09:
        return PMUD if h < 0.4 else MUD
    if f < 0.2:
        return MUD if h < 0.6 else SS
    if f < 0.55:
        return SS if h < 0.55 else (CUT if h < 0.9 else SMO)
    return SMO if h < 0.45 else (CUT if h < 0.85 else SS)


def tread(x, z):
    h = hash01(x, z, 21)
    return SMO if h < 0.5 else (CUT if h < 0.85 else SS)


def pave(x, z):
    h = hash01(x, z, 23)
    return CUT if (x + z) % 2 == 0 else (SMO if h < 0.7 else SS)


def inner(x, y, z):
    """Walls of the carved rooms."""
    h = hash3(x, y, z, 31)
    return CUT if h < 0.55 else (SS if h < 0.85 else SMO)


def ensure(bp, x, y, z, spec):
    if bp.get(x, y, z) is None:
        bp.set(x, y, z, spec)


def carve(bp, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                bp.set(x, y, z, AIR)


def fill(bp, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                bp.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def room(bp, x0, y0, z0, x1, y1, z1, wall=inner, floor=pave, ceil=None):
    """Air x0..x1, y0..y1, z0..z1; the floor (y0 - 1) is always laid, walls and ceiling only fill unset cells (the
    pyramid's skin stays where the room touches it)."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, y1 + 2):
                ins = x0 <= x <= x1 and z0 <= z <= z1
                if ins and y0 <= y <= y1:
                    bp.set(x, y, z, AIR)
                elif ins and y == y0 - 1 and floor is not None:
                    bp.set(x, y, z, floor(x, z) if callable(floor) else floor)
                elif ins and y == y1 + 1 and ceil is not None:
                    bp.set(x, y, z, ceil(x, y, z) if callable(ceil) else ceil)
                else:
                    ensure(bp, x, y, z, wall(x, y, z) if callable(wall) else wall)


def hang(bp, x, y, z, lamp=LANT_H, reach=14):
    """A lamp on a chain from the first solid block above (x, y, z)."""
    top = y + 1
    while top < y + reach and is_air(bp, x, top, z):
        top += 1
    if is_air(bp, x, top, z):
        return
    for yy in range(y + 1, top):
        bp.set(x, yy, z, CHAIN)
    bp.set(x, y, z, lamp)


def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def pot(bp, x, y, z, facing="north", cracked=False):
    bp.set(x, y, z, f"decorated_pot[facing={facing},waterlogged=false,cracked={'true' if cracked else 'false'}]")


def candle(bp, x, y, z, n=3, color=""):
    name = f"{color}_candle" if color else "candle"
    bp.set(x, y, z, f"{name}[candles={n},lit=true,waterlogged=false]")


def railing(bp, x, y, z, facing):
    bp.set(x, y, z, f"{W}brass_railing[facing={facing}]")


# ------------------------------------------------------------------ the pyramid
def pyramid(bp):
    """The stepped mass: a shell 3 thick under every riser and terrace (BUILDING §1: hollow, carved interiors)."""
    n = RMAX + 4
    xs = np.arange(-n, n + 1)
    GX, GZ = np.meshgrid(xs, xs, indexing="ij")
    R = np.maximum(np.abs(GX), np.abs(GZ))
    H = np.zeros(R.shape, np.int32)
    for rr, top in TIERS:
        H = np.where(R <= rr, top, H)
    pad = np.pad(H, 3, mode="constant", constant_values=0)
    hmin = H.copy()
    m = H.shape[0]
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            hmin = np.minimum(hmin, pad[3 + dx:3 + dx + m, 3 + dz:3 + dz + m])
    for i in range(m):
        x = int(xs[i])
        for k in range(m):
            z = int(xs[k])
            h = int(H[i, k])
            if h <= 0:
                continue
            lo = max(1, min(int(hmin[i, k]) + 1, h - 2))
            for y in range(lo, h + 1):
                bp.set(x, y, z, tread(x, z) if y == h else body(x, y, z))
            if R[i, k] >= RMAX - 2:            # footings under the plinth's outer wall
                for y in range(-6, 1):
                    bp.set(x, y, z, body(x, max(y, 0), z) if y > -3 else "sandstone")


def riser_details(bp):
    """Pilasters every 12 (3 wide, +1), niches with brass sun discs between them, a terracotta base course, a brass
    cornice under every terrace edge with an eave of upside-down stairs, corner piers carrying pinnacles, parapets."""
    for k, (R, top) in enumerate(TIERS):
        ylo = TIERS[k - 1][1] + 1 if k > 0 else 1
        base = ylo - 1
        hgt = top - ylo + 1
        for face in FACES:
            out = face
            for u in range(-R, R + 1):
                x, z = fxz(face, u, R)
                au = abs(u)
                if au < R:
                    bp.set(x, ylo, z, BTERRA if k < 2 else TERRA)
                    bp.set(x, top, z, BRASS)
                    ex, ez = fxz(face, u, R + 1)
                    bp.set(ex, top, ez, stair(SMO_ST if k > 1 else MUD_ST, OPP[out], "top"))
                # pilasters at |u| = 0, 12, 24 ... (3 wide), niches half-way between
                if au < R - 2 and min(au % 12, 12 - au % 12) <= 1:
                    px, pz = fxz(face, u, R + 1)
                    for y in range(base - (3 if k == 0 else 0), top):
                        spec = CHIS if y == top - 1 else (CUT if k > 1 or y > base + 2 else MUD)
                        if au % 12 == 0 and y == ylo + 3 and (au // 12) % 2 == 0:
                            spec = EDISON
                        bp.set(px, y, pz, spec)
                elif hgt >= 9 and au < R - 3 and abs(au % 12 - 6) <= 1:
                    for y in range(ylo + 2, ylo + 6):
                        bp.set(x, y, z, AIR)
                        bx, bz = fxz(face, u, R - 1)
                        bp.set(bx, y, bz, ENGR if (au % 12 == 6 and y == ylo + 4) else CHIS)
                    bp.set(x, ylo + 6, z, CHIS)
                    bp.set(x, ylo + 1, z, CUT)
                    if au % 12 == 6:
                        sx, sz = fxz(face, u, R)
                        bp.set(sx, ylo + 2, sz, CUT_SL + "[type=bottom,waterlogged=false]")
            # parapet on the terrace edge
            for u in range(-R + 1, R):
                x, z = fxz(face, u, R)
                au = abs(u)
                if k == len(TIERS) - 1:
                    railing(bp, x, top + 1, z, out)
                elif au % 12 == 0:
                    bp.set(x, top + 1, z, CUT)
                    bp.set(x, top + 2, z, LANT)
                else:
                    bp.set(x, top + 1, z, MUD_W if k < 2 else SS_W)
        # corner piers and pinnacles
        for sx in (-1, 1):
            for sz in (-1, 1):
                for (cx, cz) in ((sx * (R + 1), sz * (R + 1)), (sx * R, sz * (R + 1)), (sx * (R + 1), sz * R)):
                    for y in range(base - (3 if k == 0 else 0), top + 1):
                        bp.set(cx, y, cz, CUT if (y - ylo) % 4 else CHIS)
                if k == len(TIERS) - 1:
                    continue
                px, pz = sx * R, sz * R
                bp.set(px, top + 1, pz, CHIS)
                bp.set(px, top + 2, pz, CUT)
                bp.set(px, top + 3, pz, CUT)
                bp.set(px, top + 4, pz, BRASS)
                bp.set(sx * (R + 1), top + 1, sz * (R + 1), stair(SMO_ST, "south" if sz < 0 else "north"))


def wind_sand(bp):
    """Wind-blown sand banked against the risers on the north and west faces (the wind comes from the south-east),
    and against the plinth's foot on those sides."""
    for k, (R, top) in enumerate(TIERS):
        if k == 0:
            continue
        lower = TIERS[k - 1][1]
        for face in ("north", "west"):
            for u in range(-R + 2, R - 1):
                h = hash01(u, k, 41 if face == "north" else 42)
                if h > 0.45:
                    continue
                x, z = fxz(face, u, R + 1)
                if not is_air(bp, x, lower + 1, z):
                    continue
                bp.set(x, lower + 1, z, SAND)
                if h < 0.12:
                    x2, z2 = fxz(face, u, R + 2)
                    if is_air(bp, x2, lower + 1, z2):
                        bp.set(x2, lower + 1, z2, SAND)


# ------------------------------------------------------------------ exterior stairs along the risers
def face_stair(bp, face, R, yl, u0, d, landing=3, rail=True):
    """A stair 3 wide set against the riser at R on the terrace below it (top block yl): treads at w = 1..3 out from
    the riser, climbing along the face from u0 in direction d, one block per tread, then a 3-long landing level with
    the upper terrace (top yu); a balustrade at w = 4. The upper terrace's parapet opens over the landing."""
    k = tier_of(R)
    yu = TIERS[k][1]
    n = yu - yl
    fc = along(face, d)
    cells = []
    for i in range(1, n + landing + 1):
        u = u0 + d * (i - 1)
        top = yl + min(i, n)
        cells.append((u, top, i <= n))
    for u, top, step in cells:
        for w in (1, 2, 3, 4):
            x, z = fxz(face, u, R + w)
            for y in range(yl - (3 if yl <= 0 else 0), top):
                bp.set(x, y, z, body(x, y, z) if w == 4 else (CUT if (y - yl) % 5 else MUD if yl < 20 else CHIS))
            if w == 4:
                bp.set(x, top, z, CUT)
                if rail:
                    bp.set(x, top + 1, z, MUD_W if yl < 20 else SS_W)
                for y in range(top + 2, top + 6):
                    bp.set(x, y, z, AIR)
                continue
            bp.set(x, top, z, stair(SS_ST, fc) if step else tread(x, z))
            for y in range(top + 1, top + 6):
                bp.set(x, y, z, AIR)
        # the riser's pilaster or eave over the treads would hit the head: clear it
        x, z = fxz(face, u, R + 1)
        for y in range(top + 1, top + 6):
            bp.set(x, y, z, AIR)
    for u, top, step in cells[-landing:]:
        x, z = fxz(face, u, R)
        for y in range(yu + 1, yu + 4):
            bp.set(x, y, z, AIR)
    # brass lamp posts at the foot of the balustrade and on its landing end
    for u in (cells[0][0], cells[-1][0]):
        top = [c[1] for c in cells if c[0] == u][0]
        x, z = fxz(face, u, R + 4)
        bp.set(x, top + 1, z, CUT)
        bp.set(x, top + 2, z, LANT)


def terrace_stairs(bp):
    # ground -> T0 (south face, both sides), T0 -> T1 (south face, both sides)
    for s in (-1, 1):
        face_stair(bp, "south", 70, 0, s * 20, s)
        face_stair(bp, "south", 60, 9, s * 24, s)
    face_stair(bp, "north", 50, 21, -5, 1)          # T1 -> T2 behind the pyramid
    face_stair(bp, "east", 40, 32, -3, -1)          # T2 -> T3 from the priests' door (main route)
    face_stair(bp, "west", 40, 32, -3, -1)          # T2 -> T3 from the tomb gallery's door
    face_stair(bp, "south", 31, 43, 14, -1)         # T3 -> T4 (main route)
    face_stair(bp, "north", 31, 43, -14, 1)         # T3 -> T4 behind
    face_stair(bp, "south", 23, 53, 2, 1)           # T4 -> T5 (main route)
    face_stair(bp, "south", 15, 62, 12, -1, landing=1)   # T5 -> summit beside the lens gate


# ------------------------------------------------------------------ the processional stair and its sphinxes
def ramp_profile():
    prof = {}
    top = 0
    z = 99
    for kind, n in (("s", 7), ("l", 4), ("s", 7), ("l", 4), ("s", 7), ("l", 10)):
        for _ in range(n):
            if kind == "s":
                top += 1
            prof[z] = (top, kind == "s")
            z -= 1
    return prof


RAMP = ramp_profile()          # z 99..61 -> (top, step)


def sphinx(bp, x0, y0, z0, facing):
    """A brass sphinx lying on (x0, y0 - 1, z0)'s plinth, its tail at (x0, z0) and its paws 8 blocks toward
    ``facing``: a lion body 3 wide, chest and head with a striped headdress, copper paws, lamp eyes."""
    fx, fz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[facing]
    lx, lz = -fz, fx                      # lateral (right of the head)

    def put(u, v, h, spec):
        bp.set(x0 + fx * u + lx * v, y0 + h, z0 + fz * u + lz * v, spec)

    for u in range(0, 6):
        for v in (-1, 0, 1):
            for h in range(0, 3 if u > 0 else 2):
                put(u, v, h, BRASS if (u + h) % 3 else ENGR)
    put(0, 1, 0, stair(BRASS_STAIRS, OPP[facing]))           # the tail curled at the haunch
    for v in (-1, 1):
        put(1, v * 2, 0, stair(BRASS_STAIRS, "south" if (lz * v > 0) else "north") if fx else
            stair(BRASS_STAIRS, "east" if (lx * v > 0) else "west"))    # haunches
    for v in (-1, 0, 1):
        put(6, v, 0, BRASS)
        put(6, v, 1, BRASS)
        put(6, v, 2, BRASS)
    for v in (-1, 1):
        put(7, v, 0, COPPER)
        put(8, v, 0, stair(W + "copper_plating_stairs", OPP[facing]))
    put(7, 0, 0, GOLD)                                        # the sun disc between the paws
    # head: u 5..7, h 3..5, face at u 7; headdress lappets at v +-2
    for u in (5, 6):
        for v in (-1, 0, 1):
            for h in (3, 4, 5):
                put(u, v, h, GILD if (h + v) % 2 == 0 else BRASS)
            put(u, v, 6, GILD)
        for v in (-2, 2):
            put(u, v, 3, BRASS)
            put(u, v, 4, GILD)
    put(7, -1, 3, BRASS)
    put(7, 0, 3, ENGR)
    put(7, 1, 3, BRASS)
    put(7, -1, 4, EDISON)
    put(7, 1, 4, EDISON)
    put(7, 0, 4, ENGR)
    put(7, -1, 5, GILD)
    put(7, 0, 5, GOLD)
    put(7, 1, 5, GILD)
    put(6, 0, 7, GOLD)                                        # the uraeus


def plinth(bp, x0, z0, x1, z1, y0, top):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(y0, top + 1):
                bp.set(x, y, z, CHIS if y == top and edge else (CUT if y == top else body(x, max(y, 0), z)))


def processional(bp):
    for z, (top, step) in RAMP.items():
        yb = -3 if z >= 71 else 10
        for x in range(-6, 7):
            ax = abs(x)
            for y in range(yb, top):
                bp.set(x, y, z, body(x, max(y, 0), z) if ax >= 5 or y < top - 3 else CUT)
            if ax <= 4:
                if step:
                    bp.set(x, top, z, stair(SS_ST, "north"))
                else:
                    bp.set(x, top, z, CUT if ax == 0 or (z % 4 == 0) else SMO)
                for y in range(top + 1, top + 6):
                    bp.set(x, y, z, AIR)
            else:
                bp.set(x, top, z, body(x, top, z))
                bp.set(x, top + 1, z, SMO if ax == 5 else CUT)
                for y in range(top + 2, top + 5):
                    bp.set(x, y, z, AIR)
        # lamp posts on the balustrade at the landings' ends and every 4 along the flights
        if (not step and (z % 5 == 0)) or z in (99, 71):
            for s in (-1, 1):
                bp.set(s * 6, top + 2, z, LANT)
        # pilasters down the ramp's sides
        if z >= 71 and z % 6 == 0:
            for s in (-1, 1):
                for y in range(-3, top + 1):
                    bp.set(s * 7, y, z, CUT if y < top else CHIS)
    # sphinx pairs on the landings (plinths bracketed off the ramp, heads toward the stair)
    for (za, zb, top, yb) in ((88, 92, 7, -3), (77, 81, 14, -3), (63, 67, 21, 10)):
        for s in (-1, 1):
            plinth(bp, s * 7, za, s * 16, zb, yb, top)
            sphinx(bp, s * 15, top + 1, (za + zb) // 2, "west" if s > 0 else "east")
            for y in range(top + 1, top + 9):
                for z in range(za, zb + 1):
                    if is_air(bp, s * 16, y, z) and y == top + 1:
                        bp.set(s * 16, y, z, SS_W)
    # the underpass (cut after the plinths: it passes under them) that keeps the T0 terrace walk round the south face
    for x in range(-17, 18):
        for z in range(64, 67):
            for y in range(10, 14):
                bp.set(x, y, z, AIR)
            bp.set(x, 9, z, tread(x, z))
        bp.set(x, 14, 63, CHIS)
        bp.set(x, 14, 67, CHIS)
    for z in range(64, 67):
        for s in (-1, 1):
            bp.set(s * 6, 13, z, stair(SMO_ST, "east" if s < 0 else "west", "top"))


def avenue(bp):
    """The paved avenue from the obelisks to the stair, five sphinx pairs, sand either side; air cleared over it so a
    dune never buries the way."""
    for z in range(79, SZ1 + 1):
        for x in range(-18, 19):
            if z <= 99 and abs(x) <= 16 and (abs(x) <= 6 or (z in range(77, 93))):
                continue
            ax = abs(x)
            if ax <= 4:
                spec = CUT if ax == 0 or z % 6 == 0 else SMO
            elif ax <= 6:
                spec = SS if (z + ax) % 3 else CUT
            else:
                h = hash01(x, z, 51)
                spec = SAND if h < 0.85 else SS
            bp.set(x, 0, z, spec)
            bp.set(x, -1, z, SS)
            bp.set(x, -2, z, SAND)
            for y in range(1, 6):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
    for z in AVENUE:
        for s in (-1, 1):
            plinth(bp, s * 8, z - 2, s * 16, z + 2, -2, 2)
            sphinx(bp, s * 16, 3, z, "west" if s > 0 else "east")
        # a lamp standard between the pairs
        for s in (-1, 1):
            zz = z + 4
            bp.set(s * 7, 1, zz, CUT)
            bp.set(s * 7, 2, zz, SS_W)
            bp.set(s * 7, 3, zz, SS_W)
            bp.set(s * 7, 4, zz, LANT)
    # the two obelisks framing the avenue's start
    for s in (-1, 1):
        obelisk(bp, s * 12, 148, 26)


def obelisk(bp, cx, cz, h):
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            for y in range(-2, 3):
                bp.set(x, y, z, CHIS if y == 2 and (abs(x - cx) == 2 or abs(z - cz) == 2) else CUT)
    for y in range(3, h):
        r = 1
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if y > h - 8 and (x, z) != (cx, cz) and abs(x - cx) + abs(z - cz) == 2:
                    continue
                bp.set(x, y, z, ENGR if (y % 7 == 0 and (x == cx or z == cz)) else SMO)
    bp.set(cx, h, cz, BRASS)
    bp.set(cx, h + 1, cz, GOLD)


# ------------------------------------------------------------------ the pylon gate on the T1 terrace
def front_z(y):
    return 60 - (y - 22) // 6


def pylon(bp):
    for s in (-1, 1):
        for y in range(22, 47):
            i = (y - 22) // 6
            for ax in range(5, 17 - i):
                for z in range(51, 61 - i):
                    x = s * ax
                    edge = ax == 16 - i or z == 60 - i
                    if y >= 44:
                        spec = BRASS if y == 45 else (CUT if y == 46 else SMO)
                    elif edge and (ax == 16 - i and z == 60 - i):
                        spec = CHIS                      # torus moulding on the outer corner
                    else:
                        spec = body(x, y + 20, z) if edge else SS
                    bp.set(x, y, z, spec)
            # the cavetto cornice
            if y == 43:
                for ax in range(5, 18 - i):
                    bp.set(s * ax, y, 61 - i, stair(SMO_ST, "north", "top"))
                for z in range(51, 61 - i):
                    bp.set(s * (17 - i), y, z, stair(SMO_ST, "west" if s > 0 else "east", "top"))
        # flagstaff masts in front of each tower
        for ax in (8, 13):
            for y in range(10, 52):
                bp.set(s * ax, y, 61, BRASS if y % 8 == 0 else IRON_WALL)
            bp.set(s * ax, 52, 61, GOLD)
        # brass wing feathers across the tower fronts (the winged sun)
        for ax in range(5, 13):
            for y in (38, 39):
                if ax <= 12 - (y - 38) * 2:
                    bp.set(s * ax, y, front_z(y), BRASS if (ax + y) % 2 else GILD)
        # the guard room in the tower (door from the gate hall)
        room(bp, s * 7 if s > 0 else -13, 22, 53, 13 if s > 0 else -7, 26, 58, wall=inner, floor=pave)
    # gate section: jambs, the lintel with the sun disc, the gate hall
    for z in range(51, 61):
        for y in range(22, 36):
            for s in (-1, 1):
                bp.set(s * 4, y, z, CUT if y % 4 else CHIS)
        for x in range(-4, 5):
            for y in range(36, 44):
                bp.set(x, y, z, CUT if y in (36, 43) else SS)
    for x in range(-4, 5):
        bp.set(x, 44, 60, stair(SMO_ST, "north", "top"))
        for z in range(51, 61):
            bp.set(x, 44, z, BRASS)
            bp.set(x, 45, z, CUT)
    for x in range(-2, 3):
        for y in range(37, 42):
            if (x * x + (y - 39) ** 2) <= 5:
                bp.set(x, y, 60, GOLD)
    for x in range(-3, 4):
        for z in range(51, 60):
            for y in range(22, 36):
                bp.set(x, y, z, AIR)
            bp.set(x, 21, z, pave(x, z))
    for s in (-1, 1):
        carve(bp, s * 4, 22, 55, s * 6, 24, 56)
        for ax in (4, 5, 6):
            bp.set(s * ax, 21, 55, pave(ax, 55))
            bp.set(s * ax, 21, 56, pave(ax, 56))
    # the brass leaves and their wicket
    for x in range(-3, 4):
        for y in range(22, 36):
            if abs(x) <= 1 and y <= 25:
                bp.set(x, y, 60, AIR)
                continue
            if x == 0:
                spec = IRON
            elif y in (26, 31) or abs(x) == 3:
                spec = GEAR if y in (26, 31) and abs(x) == 2 else IRON
            else:
                spec = BRASS if (x + y) % 2 else ENGR
            bp.set(x, y, 60, spec)
    for y in range(22, 26):
        for s in (-1, 1):
            bp.set(s * 2, y, 60, IRON)
    bp.set(-1, 26, 60, IRON)
    bp.set(1, 26, 60, IRON)
    # lamps inside the gate hall and the passage into the T2 riser
    for z in (52, 58):
        for s in (-1, 1):
            bp.set(s * 3, 27, z, EDISON)
    hang(bp, 0, 30, 55, CHANDELIER)
    room(bp, -1, 22, 47, 1, 25, 50, wall=inner, floor=pave)
    for y in range(22, 26):
        bp.set(-2, y, 50, CHIS)
        bp.set(2, y, 50, CHIS)
    for s in (-1, 1):
        x0, x1 = (7, 13) if s > 0 else (-13, -7)
        bp.chest(s * 12, 22, 57, "north", loot=LOOT + "sz_offering")
        bp.barrel(s * 12, 22, 54)
        bp.barrel(s * 11, 22, 54)
        bp.set(s * 8, 22, 54, "brasshaven:mahogany_table")
        hang(bp, s * 10, 25, 55)
        bp.set(s * 13, 22, 58, "barrel[facing=up,open=false]")


# ------------------------------------------------------------------ hypostyle hall, offerings, passages
def hall_floor(x, z):
    if abs(x) <= 1:
        return CHIS if z % 4 == 0 else SMO
    if (x // 3 + z // 3) % 2 == 0:
        return CUT
    return SMO if hash01(x, z, 61) < 0.8 else SS


def column(bp, cx, cz, y0, ytop, sun=False):
    """A hypostyle column from the floor (y0) to under the architrave (ytop): a 5 x 5 plinth, a torus of stairs, a
    3 x 3 shaft with chiselled bands, a flared papyrus capital (upside-down stairs, a brass lotus course) and an
    abacus."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            bp.set(cx + dx, y0, cz + dz, SMO if max(abs(dx), abs(dz)) == 2 else CUT)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            m = max(abs(dx), abs(dz))
            if m == 2:
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                fc = "east" if dx == -2 else "west" if dx == 2 else "south" if dz == -2 else "north"
                bp.set(cx + dx, y0 + 1, cz + dz, stair(SMO_ST, fc))
            else:
                bp.set(cx + dx, y0 + 1, cz + dz, CUT)
    for y in range(y0 + 2, ytop - 3):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if sun:
                    spec = "ochre_froglight" if dx == 0 and dz == 0 else (GLASS_Y if (dx and dz) == 0 else BRASS)
                    if (y - y0) % 5 == 0 and (dx or dz):
                        spec = BRASS
                else:
                    band = (y - y0) % 5 == 0
                    spec = CHIS if band else (SMO if dx and dz else SS)
                    if y == ytop - 4:
                        spec = BRASS
                bp.set(cx + dx, y, cz + dz, spec)
    yc = ytop - 3
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            m = max(abs(dx), abs(dz))
            if m <= 1:
                bp.set(cx + dx, yc, cz + dz, GILD if sun else CUT)
            elif not (abs(dx) == 2 and abs(dz) == 2):
                fc = "east" if dx == -2 else "west" if dx == 2 else "south" if dz == -2 else "north"
                bp.set(cx + dx, yc, cz + dz, stair(SMO_ST, fc, "top"))
            bp.set(cx + dx, yc + 1, cz + dz, GILD if m == 2 and (dx + dz) % 2 == 0 else BRASS)
            bp.set(cx + dx, yc + 2, cz + dz, SMO if m == 2 else CUT)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(cx + dx, ytop, cz + dz, CHIS)


def hypostyle(bp):
    H = HALL
    room(bp, -H, FH, -H, H, HALL_TOP, H, wall=inner, floor=hall_floor,
         ceil=lambda x, y, z: GOLD if hash01(x, z, 62) < 0.025 else BLUE_T)
    # architraves along x over every column row, and along the walls
    for cz in COLS:
        for x in range(-H, H + 1):
            for dz in (-1, 0, 1):
                bp.set(x, HALL_TOP, cz + dz, CHIS if x in COLS and dz == 0 else CUT)
    for cx in COLS:
        for cz in COLS:
            column(bp, cx, cz, FH, HALL_TOP - 1, sun=(cx == 0 and cz == 0))
    # wall pilasters facing every column row and line, a painted frieze, a dado
    for t in COLS:
        for y in range(FH, HALL_TOP):
            for d in (-1, 0, 1):
                for (x, z) in ((t + d, -H - 1), (t + d, H + 1), (-H - 1, t + d), (H + 1, t + d)):
                    bp.set(x, y, z, CHIS if y in (FH, HALL_TOP - 1) else CUT)
            for (x, z) in ((t, -H), (-H, t), (H, t)):
                if y == FH + 9:
                    bp.set(x, y, z, EDISON if t % 18 == 0 else CUT)
    for u in range(-H, H + 1):
        for (x, z) in ((u, -H - 1), (-H - 1, u), (H + 1, u), (u, H + 1)):
            if any(abs(u - t) <= 1 for t in COLS):
                continue
            for y in (FH + 11, FH + 12):
                bp.set(x, y, z, (OTERRA, YTERRA, BTERRA, TERRA)[(u // 2 + y) % 4] if hash01(u, y, 63) < 0.85
                       else BLUE_T)
            bp.set(x, FH + 10, z, BRASS)
            bp.set(x, FH, z, BTERRA)
    # the sun-engine wheel at the end of the axis (north wall)
    cy = 31
    for x in range(-8, 9):
        for y in range(cy - 8, cy + 9):
            d = math.hypot(x, y - cy)
            if d <= 7.4:
                a = math.atan2(y - cy, x)
                if d >= 6.4:
                    spec = BRASS
                elif d <= 1.6:
                    spec = GOLD
                elif int((a + math.pi) / (math.pi / 6) + 0.5) % 2 == 0 and d > 2:
                    spec = COPPER
                else:
                    spec = GEAR
                bp.set(x, y, -H - 1, spec)
            elif d <= 8.4 and int((math.atan2(y - cy, x) + math.pi) / (math.pi / 12)) % 2 == 0:
                bp.set(x, y, -H - 1, BRASS)
    for x in (-10, 10):
        for y in range(FH, HALL_TOP):
            bp.set(x, y, -H, COPPER if y % 4 else BRASS)
    # chandeliers between the columns
    for x in (-13, -4, 4, 13):
        for z in (-13, -4, 4, 13):
            hang(bp, x, FH + 9, z, CHANDELIER, reach=12)
    # braziers (lanterns on pedestals) along the axis
    for z in (-20, 15):
        for s in (-1, 1):
            bp.set(s * 3, FH, z, CHIS)
            bp.set(s * 3, FH + 1, z, LANT)
    # the hub's site of grace near the entrance, a bench
    bp.set(4, FH, 21, MOD["waystone"])
    bp.set(6, FH, 22, stair(SMO_ST, "north"))
    bp.set(7, FH, 22, stair(SMO_ST, "north"))
    # the compression passage into the hall from the offerings (south)
    room(bp, -1, FH, H + 1, 1, FH + 3, 33, wall=inner, floor=pave)
    hall_stairs(bp)


def hall_stairs(bp):
    """Grand stairs up both side walls to balconies at feet 33 (doors to the priests' quarter, east, and to the
    robbers' breach into the tomb gallery, west)."""
    for s in (-1, 1):
        for i in range(1, 12):
            z = 22 - i
            top = FH - 1 + i
            for ax in (21, 22, 23):
                x = s * ax
                for y in range(FH, top):
                    bp.set(x, y, z, CUT if y % 4 else CHIS)
                bp.set(x, top, z, stair(SMO_ST, "north"))
            bp.set(s * 20, top + 1, z, SS_W)
            bp.set(s * 20, top, z, CUT)
            for y in range(FH, top):
                bp.set(s * 20, y, z, CUT if y % 4 else CHIS)
        # the balcony: floor at y 32 (feet 33), x 21..24, z -10..10, a railing on its edge, corbels under it
        for z in range(-10, 11):
            for ax in (21, 22, 23, 24):
                bp.set(s * ax, FQ - 1, z, MAHOGANY if ax < 24 else CUT)
            railing(bp, s * 21, FQ, z, "west" if s > 0 else "east")
            if z % 5 == 0:
                for ax in (21, 22, 23, 24):
                    bp.set(s * ax, FQ - 2, z, BRASS)
                bp.set(s * 20, FQ - 2, z, stair(SMO_ST, "east" if s > 0 else "west", "top"))
        # the stair's top tread meets the balcony at z 11 -> 10; a lamp post at the corner
        bp.set(s * 20, FQ, 11, CUT)
        bp.set(s * 20, FQ + 1, 11, LANT)
        bp.set(s * 20, FQ, -11, CUT)
        bp.set(s * 20, FQ + 1, -11, LANT)
        for ax in (20, 21, 22, 23, 24):
            bp.set(s * ax, FQ, -11, SS_W if ax > 20 else CUT)
        for z in (-8, 0, 8):
            bp.set(s * 25, FQ + 3, z + 4, EDISON)


def offerings(bp):
    room(bp, -7, FH, 34, 7, FH + 9, 46, wall=inner, floor=pave, ceil=lambda x, y, z: BLUE_T if (x + z) % 3 else CUT)
    # side niches with offering tables, statues of priests (pillars with a brass head), pots
    for s in (-1, 1):
        for z in (36, 40, 44):
            x = s * 8
            for y in range(FH, FH + 5):
                bp.set(x, y, z, AIR)
            bp.set(x, FH + 5, z, CHIS)
            bp.set(x, FH - 1, z, CUT)
            bp.set(s * 9, FH + 2, z, ENGR)
            pot(bp, x, FH, z, "west" if s > 0 else "east", cracked=z == 40)
        for z in (35, 38, 42, 45):
            bp.set(s * 6, FH, z, CHIS)
            bp.set(s * 6, FH + 1, z, SS_W)
            bp.set(s * 6, FH + 2, z, BRASS)
        for z in (37, 43):
            bp.set(s * 5, FH, z, TABLE)
            candle(bp, s * 5, FH + 1, z, 3)
    for z in (37, 43):
        hang(bp, 0, FH + 6, z, CHANDELIER)
    bp.chest(-6, FH, 46, "north", loot=LOOT + "sz_offering")
    bp.barrel(6, FH, 46)
    bp.spawner(-5, FH, 40, MOB_SPIDER)
    # the passage into the T2 riser joins the hall at z 46/47
    carve(bp, -1, FH, 46, 1, FH + 3, 47)


# ------------------------------------------------------------------ the sand-flooded lower halls (feet 1)
def heap(bp, cx, cz, r, h, seed, keep=()):
    for x in range(int(cx - r) - 1, int(cx + r) + 2):
        for z in range(int(cz - r) - 1, int(cz + r) + 2):
            d = math.hypot(x - cx, z - cz)
            if d > r:
                continue
            if any(abs(x - kx) <= kr and abs(z - kz) <= kr for kx, kz, kr in keep):
                continue
            n = h * (1 - (d / r) ** 1.6) + (hash01(x, z, seed) - 0.5) * 1.2
            for y in range(1, 1 + int(round(n))):
                if is_air(bp, x, y, z) and not is_air(bp, x, y - 1, z):
                    bp.set(x, y, z, SAND)


def sand_floor(x, z):
    h = hash01(x, z, 71)
    return SS if h < 0.5 else (CUT if h < 0.75 else SAND)


def lower_halls(bp):
    # the hall of sand under the hypostyle: columns half buried
    room(bp, -22, 1, -22, 22, 13, 22, wall=inner, floor=sand_floor)
    for cx in COLS:
        for cz in COLS:
            if cx == 0 and cz == 0:
                for y in range(1, 14):
                    for dx in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            bp.set(dx, y, dz, "ochre_froglight" if dx == 0 and dz == 0 else
                                   (BRASS if y % 4 == 0 else GLASS_Y))
                continue
            for y in range(1, 14):
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        bp.set(cx + dx, y, cz + dz, CHIS if y in (6, 12) else (MUD if y < 3 else SS))
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) == 2:
                        bp.set(cx + dx, 13, cz + dz, stair(SMO_ST, "east" if dx == -2 else "west" if dx == 2 else
                                                           "south" if dz == -2 else "north", "top"))
    keep = ((-14, 18, 2), (-14, 8, 2), (-8, 0, 2), (0, -14, 2), (0, -20, 2), (-18, 16, 2), (16, -15, 2), (18, 2, 2),
            (8, 8, 1), (-4, 18, 2))
    for (cx, cz, r, h, sd) in ((-6, 8, 5.5, 3, 1), (10, -5, 6.5, 4, 2), (13, 14, 5.0, 3, 3), (-12, -10, 6.0, 4, 4),
                               (6, 19, 3.5, 2, 5), (-19, -2, 4.5, 3, 6), (5, -18, 4.0, 2, 7), (17, 7, 3.5, 2, 8)):
        heap(bp, cx, cz, r, h, 700 + sd, keep)
    for (x, z) in ((-13, -4), (13, 4), (-4, 13), (4, -13), (-13, 13), (13, -13)):
        hang(bp, x, 9, z, SOUL_H)
    bp.spawner(-15, 1, -5, MOB_HUSK)
    bp.spawner(14, 1, 9, MOB_HUSK)
    bp.chest(-21, 1, -21, "south", loot=LOOT + "sz_sand")
    pot(bp, -21, 1, -19, cracked=True)
    pot(bp, -20, 1, -21)
    pot(bp, 21, 1, 21, cracked=True)
    lift_hall(bp)
    west_wing(bp)
    south_wing(bp)
    engine_hall(bp)


def lift_hall(bp):
    room(bp, -6, 1, -33, 6, 6, -25, wall=inner, floor=pave)
    # the door to the hall of sand: iron, its lever on the lift side
    for x in range(-2, 3):
        for y in range(1, 5):
            bp.set(x, y, -24, CHIS if x in (-2, 2) or y == 4 else CUT)
    bp.door(0, 1, -24, "south", wood="iron")
    carve(bp, 0, 1, -23, 0, 2, -23)
    bp.set(0, 0, -23, CUT)
    lever(bp, 1, 2, -25, "north")
    hang(bp, 0, 4, -29, LANT_H)
    for x in (-6, 6):
        bp.set(x, 3, -31, EDISON)


def west_wing(bp):
    """The corridor from the hall of sand to the collapsed vestibule behind the breach, the granary and the dry
    cistern on either side of it."""
    room(bp, -44, 1, 15, -23, 4, 17, wall=inner, floor=sand_floor)
    carve(bp, -23, 1, 15, -23, 3, 17)
    room(bp, -46, 1, 15, -44, 4, 49, wall=inner, floor=sand_floor)
    for z in range(20, 49, 8):
        hang(bp, -45, 3, z, SOUL_H)
    # granary (west)
    room(bp, -60, 1, 24, -50, 6, 40, wall=inner, floor=pave)
    carve(bp, -49, 1, 31, -47, 3, 32)
    for z in range(25, 40, 2):
        for x in (-59, -51):
            pot(bp, x, 1, z, "east" if x < -55 else "west", cracked=hash01(x, z, 81) < 0.3)
    for z in (27, 33, 37):
        bp.set(-56, 1, z, "hay_block[axis=x]")
        bp.set(-55, 1, z, "hay_block[axis=x]")
        bp.set(-54, 1, z, "barrel[facing=up,open=false]")
    bp.chest(-59, 1, 40, "east", loot=LOOT + "sz_sand")
    heap(bp, -55, 26, 3.5, 3, 811, keep=((-55, 31, 2),))
    hang(bp, -55, 4, 32, SOUL_H)
    # dry cistern (east): a sunken basin with steps, pillars
    room(bp, -40, 1, 26, -28, 6, 44, wall=inner, floor=pave)
    carve(bp, -43, 1, 34, -41, 3, 35)
    for x in range(-37, -30):
        for z in range(29, 42):
            for y in range(-3, 1):
                bp.set(x, y, z, AIR)
            bp.set(x, -4, z, SAND if hash01(x, z, 83) < 0.6 else SS)
    for x in range(-38, -29):
        for z in range(28, 43):
            if x in (-38, -30) or z in (28, 42):
                for y in range(-4, 1):
                    ensure(bp, x, y, z, CUT)
    # steps down the north side of the basin (z 29 -> 32)
    for i in range(4):
        for x in range(-35, -32):
            bp.set(x, -i, 29 + i, stair(SS_ST, "north"))
            for y in range(-i - 1, -4, -1):
                bp.set(x, y, 29 + i, CUT)
    for (x, z) in ((-37, 29), (-31, 29), (-37, 41), (-31, 41)):
        for y in range(-3, 7):
            bp.set(x, y, z, CHIS if y % 3 == 0 else CUT)
    bp.chest(-31, -3, 38, "west", loot=LOOT + "sz_sand")
    bp.spawner(-34, -3, 39, MOB_CRAWLER)
    hang(bp, -34, 3, 35, SOUL_H)
    collapsed_vestibule(bp)


def collapsed_vestibule(bp):
    room(bp, -54, 1, 50, -36, 7, 66, wall=inner, floor=sand_floor)
    carve(bp, -46, 1, 49, -44, 4, 50)
    # the breach through the plinth's south wall: a ragged hole, rubble and the desert pouring in
    for x in range(-49, -40):
        hi = 6 - int(2 * abs(x + 45) / 4) + int(hash01(x, 0, 91) * 2)
        for z in range(67, 72):
            for y in range(1, hi + 1):
                bp.set(x, y, z, AIR)
            bp.set(x, 0, z, SAND)
        for y in range(hi + 1, hi + 3):
            for z in range(67, 71):
                if bp.get(x, y, z) is None or bp.get(x, y, z) == AIR:
                    bp.set(x, y, z, body(x, y, z))
    for (x, z) in ((-50, 71), (-40, 72), (-48, 73), (-39, 70)):
        bp.set(x, 1, z, MUD if hash01(x, z, 92) < 0.5 else SS)
    heap(bp, -44, 74, 6.0, 2, 921, keep=((-45, 70, 1),))
    heap(bp, -45, 60, 7.0, 4, 922, keep=((-45, 52, 2), (-45, 64, 1)))
    # the fallen head of a sphinx, lying on its side
    for y in range(1, 5):
        for z in range(54, 59):
            for x in range(-53, -50):
                bp.set(x, y, z, GILD if (y + z) % 2 else BRASS)
    bp.set(-50, 2, 55, EDISON)
    bp.set(-50, 2, 57, EDISON)
    bp.set(-50, 3, 56, ENGR)
    bp.set(-50, 1, 56, BRASS)
    # broken column drums
    for (x, z, h) in ((-39, 53, 5), (-39, 63, 2), (-52, 63, 3)):
        for y in range(1, h + 1):
            for dx in (0, 1):
                for dz in (0, 1):
                    bp.set(x + dx, y, z + dz, CHIS if y == h else SS)
    for (x, z) in ((-41, 55), (-37, 60), (-42, 52)):
        bp.set(x, 1, z, SS if hash01(x, z, 93) < 0.5 else CUT_SL + "[type=bottom,waterlogged=false]")
    bp.chest(-37, 1, 51, "west", loot=LOOT + "sz_sand")
    bp.spawner(-51, 1, 52, MOB_HUSK)
    hang(bp, -45, 5, 57, SOUL_H)


def south_wing(bp):
    """The corridor from the hall of sand to the iron door at the plinth's foot beside the processional stair (opens
    from inside), and the shrine of the buried sun off it."""
    room(bp, -15, 1, 23, -13, 4, 68, wall=inner, floor=sand_floor)
    carve(bp, -15, 1, 23, -13, 3, 23)
    for z in range(28, 68, 8):
        hang(bp, -14, 3, z, SOUL_H)
    # the exit: iron door in the outer wall, lever inside
    for x in range(-16, -11):
        for y in range(0, 5):
            bp.set(x, y, 69, CHIS if x in (-16, -12) or y == 4 else body(x, y, 69))
    bp.door(-14, 1, 69, "south", wood="iron")
    lever(bp, -13, 2, 68, "north")
    for y in range(1, 4):
        bp.set(-14, y, 70, AIR)
        bp.set(-15, y, 70, CHIS)
        bp.set(-13, y, 70, CHIS)
    bp.set(-14, 4, 70, CHIS)
    bp.set(-14, 0, 70, CUT)
    # the shrine of the buried sun
    room(bp, -10, 1, 30, 10, 10, 46, wall=inner, floor=pave)
    carve(bp, -12, 1, 37, -11, 3, 38)
    cy = 6
    for x in range(-5, 6):
        for y in range(cy - 5, cy + 6):
            d = math.hypot(x, y - cy)
            if d <= 3.2:
                bp.set(x, y, 29, GOLD if d < 1.5 else BRASS)
            elif d <= 4.6 and int((math.atan2(y - cy, x) + math.pi) / (math.pi / 8)) % 2 == 0:
                bp.set(x, y, 29, GILD)
    for x in range(-3, 4):
        bp.set(x, 1, 31, CHIS)
    bp.set(-2, 2, 31, CHIS)
    bp.set(2, 2, 31, CHIS)
    bp.chest(0, 1, 32, "south", loot=LOOT + "sz_offering")
    candle(bp, -2, 3, 31, 3)
    candle(bp, 2, 3, 31, 3)
    for (x, z) in ((-6, 35), (6, 35), (-6, 41), (6, 41)):
        for y in range(1, 11):
            bp.set(x, y, z, CHIS if y in (1, 10) else SS)
    heap(bp, 3, 42, 6.0, 4, 931, keep=((0, 33, 2), (-9, 37, 2)))
    hang(bp, 0, 6, 38, LANT_H)


def engine_hall(bp):
    """The old sun-engine's boiler room east of the hall of sand: a copper boiler, its firebox, pipes rising into the
    pyramid, gauges, a gear wall."""
    room(bp, 26, 1, -8, 44, 9, 12, wall=inner, floor=lambda x, z: "brasshaven:diamond_plate" if (x + z) % 5 else IRON)
    carve(bp, 23, 1, 1, 25, 3, 3)
    cz, cy = 2, 5
    for x in range(29, 42):
        for z in range(cz - 4, cz + 5):
            for y in range(cy - 4, cy + 5):
                d = math.hypot(z - cz, y - cy)
                if d <= 3.4:
                    if d > 2.4 or x in (29, 41):
                        spec = BRASS if x % 3 == 0 else COPPER
                        if d > 2.4 and y == cy + 3 and x % 4 == 1:
                            spec = GAUGE
                        bp.set(x, y, z, spec)
                    elif y < 1:
                        pass
    for x in range(30, 41, 3):
        for y in range(1, cy - 2):
            bp.set(x, y, cz - 2, IRON)
            bp.set(x, y, cz + 2, IRON)
    for z in (cz - 1, cz, cz + 1):
        for y in (1, 2, 3):
            bp.set(43, y, z, "blast_furnace[facing=west,lit=false]" if y == 1 and z == cz else IRON)
    for x in (32, 38):
        for y in range(cy + 3, 10):
            bp.set(x, y, cz, COPPER)
    for z in range(-7, 12):
        if z % 2 == 0:
            for y in range(2, 8):
                bp.set(44, y, z, GEAR if (y + z) % 4 else BRASS) if z < -2 or z > 6 else None
    bp.chest(27, 1, -7, "east", loot=LOOT + "sz_sand")
    bp.barrel(27, 1, 11)
    bp.barrel(28, 1, 11)
    bp.spawner(40, 1, -5, MOB_SPIDER)
    for (x, z) in ((30, -5), (40, 9)):
        hang(bp, x, 7, z, LANT_H)


# ------------------------------------------------------------------ newel stairs
def spiral(cx, cz, f0, k_end, c0):
    """Square newel stair round a 3 x 3 core: (x, z, feet, stair facing or None) per cell and the landings
    {k: (sx, sz, feet)}: 3 x 3 landings at the corners, flights of three steps (3 wide) on the sides, +3 per side."""
    cells, land = [], {}
    f = f0
    for k in range(k_end + 1):
        sx, sz = CORN_CCW[(c0 + k) % 4]
        for d1 in (2, 3, 4):
            for d2 in (2, 3, 4):
                cells.append((cx + sx * d1, cz + sz * d2, f, None))
        land[k] = (sx, sz, f)
        if k == k_end:
            break
        nx, nz = CORN_CCW[(c0 + k + 1) % 4]
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


def build_newel(bp, cx, cz, f0, k_end, c0, y_top, wall=inner, lamps=True):
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            edge = abs(x - cx) == 5 or abs(z - cz) == 5
            core = abs(x - cx) <= 1 and abs(z - cz) <= 1
            for y in range(f0 - 1, y_top + 1):
                if edge or y in (f0 - 1, y_top):
                    bp.set(x, y, z, wall(x, y, z))
                elif core:
                    bp.set(x, y, z, CHIS if y % 6 == 0 else SMO)
                else:
                    bp.set(x, y, z, AIR)
    cells, land = spiral(cx, cz, f0, k_end, c0)
    for (x, z, f, fc) in cells:
        bp.set(x, f - 1, z, stair(SS_ST, fc) if fc else (SMO if (x + z) % 2 else CUT))
        if f - f0 <= 6:
            for y in range(f0 - 1, f - 1):
                bp.set(x, y, z, wall(x, y, z))
    for k, (sx, sz, f) in land.items():
        if lamps and k % 2 == 1 and f + 1 < y_top:
            # a lamp on the core corner, out of the way of the landing
            bp.set(cx + sx * 1, f + 1, cz + sz * 1, EDISON)
    return land


def newel_door(bp, cx, cz, land, side, width=3):
    """Open the newel's wall beside landing ``land`` = (sx, sz, feet) toward ``side`` (x or z); 3 high."""
    sx, sz, f = land
    if side == "x":
        x = cx + sx * 5
        for z in range(cz + sz * 2, cz + sz * 5, sz)[:width]:
            for y in range(f, f + 3):
                bp.set(x, y, z, AIR)
    else:
        z = cz + sz * 5
        for x in range(cx + sx * 2, cx + sx * 5, sx)[:width]:
            for y in range(f, f + 3):
                bp.set(x, y, z, AIR)


def side_newel(bp):
    cx, cz = NEWEL_B
    land = build_newel(bp, cx, cz, 1, 7, 2, FH + 4)
    newel_door(bp, cx, cz, land[0], "x")
    carve(bp, 23, 1, -16, 24, 3, -14)
    newel_door(bp, cx, cz, land[7], "x")
    for z in (-22, -21, -20):
        for y in range(FH, FH + 3):
            bp.set(25, y, z, AIR)


# ------------------------------------------------------------------ priests' quarter and tomb gallery (feet 33)
def priests_quarter(bp):
    f = FQ
    room(bp, 29, f, -21, 31, f + 4, 21, wall=inner, floor=lambda x, z:
         "spruce_planks" if (z % 4) else MAHOGANY)
    rooms = ((15, 21, "refectory"), (8, 13, "dormitory"), (-3, 6, "stars"), (-12, -5, "scriptorium"),
             (-21, -14, "study"))
    for z0, z1, kind in rooms:
        room(bp, 33, f, z0, 38, f + 5, z1, wall=inner,
             floor=(lambda x, z: "black_concrete" if kind == "stars" and 34 <= x <= 37 and -2 <= z <= 5 else
                    ("spruce_planks" if (x + z) % 3 else MAHOGANY)))
        zd = (z0 + z1) // 2
        bp.set(32, f - 1, zd, "spruce_planks")
        bp.door(32, f, zd, "east", wood="spruce")
    # the balcony door from the hypostyle
    for z in (-1, 0, 1):
        for x in range(25, 29):
            for y in range(f, f + 3):
                bp.set(x, y, z, AIR)
            bp.set(x, f - 1, z, CUT)
        for y in range(f, f + 4):
            pass
    for z in (-2, 2):
        for y in range(f, f + 4):
            bp.set(25, y, z, CHIS)
    for x in range(25, 29):
        bp.set(x, f + 3, -1, CHIS)
        bp.set(x, f + 3, 0, CHIS)
        bp.set(x, f + 3, 1, CHIS)
    # windows through the east wall
    for z0, z1, kind in rooms:
        if kind == "stars":
            continue
        zc = (z0 + z1) // 2 + (1 if kind != "dormitory" else 0)
        for x in (39, 40):
            for y in (f + 1, f + 2):
                bp.set(x, y, zc, "iron_bars[waterlogged=false]")
    # the star-chart room's terrace door (an arch 2 x 3 through the riser)
    for x in (39, 40):
        for z in (0, 1):
            for y in range(f, f + 3):
                bp.set(x, y, z, AIR)
            bp.set(x, f - 1, z, CUT)
        bp.set(x, f + 3, -1, CHIS)
        bp.set(x, f + 3, 2, CHIS)
        bp.set(x, f + 3, 0, CHIS)
        bp.set(x, f + 3, 1, CHIS)
    carve(bp, 41, f, -1, 41, f + 2, 1)            # the riser's pilaster in front of the door
    for z in range(-20, 21, 6):
        hang(bp, 30, f + 3, z, LANT_H)
    bp.spawner(30, f, -20, MOB_DRONE)
    # refectory: a long table with benches, a hearth
    for z in range(16, 21):
        bp.set(35, f, z, TABLE)
        bp.set(34, f, z, stair(MAHOGANY_STAIRS, "west"))
        bp.set(36, f, z, stair(MAHOGANY_STAIRS, "east"))
    bp.set(38, f, 15, "smoker[facing=west,lit=false]")
    bp.set(38, f, 16, "cauldron")
    bp.barrel(38, f, 21)
    bp.barrel(37, f, 21)
    bp.set(38, f, 17, "barrel[facing=up,open=false]")
    hang(bp, 35, f + 4, 18, LANT_H)
    # dormitory: beds, a chest
    for z in (8, 10, 12):
        bp.bed(37, f, z, "east", color="orange")
    bp.chest(33, f, 13, "south", loot=LOOT + "sz_priest")
    hang(bp, 35, f + 4, 10, LANT_H)
    # the star-chart room: a black floor with glowing stars, an armillary model, lecterns, a cartography table
    for (x, z) in ((34, -2), (36, 0), (35, 3), (37, 4), (34, 5), (37, -1), (35, 1)):
        bp.set(x, f - 1, z, "sea_lantern" if (x + z) % 2 else "glowstone")
    bp.set(38, f, -3, "cartography_table")
    bp.set(38, f, 6, "lectern[facing=west,has_book=false,powered=false]")
    bp.set(33, f, 6, "lectern[facing=east,has_book=false,powered=false]")
    for y in range(f, f + 3):
        bp.set(33, y, -3, BRASS if y < f + 2 else GOLD)
    hang(bp, 35, f + 4, 1, CHANDELIER)
    # scriptorium: shelves, desks
    for z in range(-12, -4):
        for y in range(f, f + 3):
            bp.set(38, y, z, "bookshelf")
    for z in (-11, -8):
        bp.set(35, f, z, TABLE)
        bp.set(34, f, z, stair(MAHOGANY_STAIRS, "west"))
        candle(bp, 35, f + 1, z, 2)
    bp.chest(33, f, -12, "south", loot=LOOT + "sz_priest")
    hang(bp, 36, f + 4, -8, LANT_H)
    # the armillary study: a brass armillary on a stand, a telescope at the window
    for y in range(f, f + 2):
        bp.set(35, y, -18, BRASS)
    for (dx, dy) in ((-1, 2), (1, 2), (0, 3), (-1, 3), (1, 3), (0, 4)):
        bp.set(35 + dx, f + dy, -18, BRASS if dy != 3 or dx else GOLD)
    for x in range(36, 39):
        bp.set(x, f + 1, -16, COPPER if x < 38 else BRASS)
    bp.set(36, f, -16, IRON_WALL)
    bp.chest(33, f, -21, "south", loot=LOOT + "sz_priest")
    bp.barrel(38, f, -21)
    hang(bp, 34, f + 4, -15, LANT_H)


def tomb_gallery(bp):
    f = FQ
    room(bp, -37, f, -21, -30, f + 5, 21, wall=inner, floor=lambda x, z: CUT if abs(x + 33.5) < 2 else SS)
    # sarcophagi in arched niches along both sides
    for z in range(-18, 19, 6):
        for xw, xs in ((-38, -37), (-29, -30)):
            for dz in (-1, 0, 1):
                for y in range(f, f + 3):
                    bp.set(xw, y, z + dz, AIR)
                bp.set(xw, f - 1, z + dz, CUT)
                bp.set(xw, f + 3, z + dz, CHIS)
            # the lid and the coffin (a stone box with a brass face)
            for dz in (-1, 0, 1):
                bp.set(xs, f, z + dz, CHIS if dz else ENGR)
                bp.set(xs, f + 1, z + dz, SMO_SL + "[type=bottom,waterlogged=false]")
            bp.set(xw, f, z, GOLD if hash01(z, 1, 101) < 0.2 else CUT)
        for xx in (-36, -31):
            pot(bp, xx, f, z + 3, cracked=hash01(xx, z, 102) < 0.5)
    for z in range(-20, 21, 8):
        hang(bp, -33, f + 4, z, SOUL_H)
    # the robbers' breach from the west balcony: a hole through a bricked-up door, rubble
    for z in (0, 1):
        for x in range(-28, -24):
            for y in range(f, f + 3):
                bp.set(x, y, z, AIR)
            bp.set(x, f - 1, z, CUT)
    for (x, y, z) in ((-28, f + 3, 0), (-27, f + 3, 1), (-26, f + 3, 0), (-29, f, -1), (-29, f, 2)):
        bp.set(x, y, z, MUD)
    for z in (-1, 2):
        for x in range(-28, -24):
            for y in range(f, f + 3):
                bp.set(x, y, z, MUD if hash3(x, y, z, 103) < 0.5 else PMUD)
    bp.set(-31, f, 0, MUD_ST + "[facing=east,half=bottom,shape=straight,waterlogged=false]")
    bp.set(-31, f, 1, "cobblestone_slab[type=bottom,waterlogged=false]")
    bp.set(-30, f, 2, "skeleton_skull[rotation=4]")
    bp.set(-30, f, -2, "bone_block[axis=x]")
    # loot, guardians
    bp.chest(-36, f, -15, "east", loot=LOOT + "sz_tomb")
    bp.chest(-31, f, 15, "west", loot=LOOT + "sz_tomb")
    bp.spawner(-34, f, -9, MOB_HUSK)
    bp.spawner(-33, f, 10, MOB_CRAWLER)
    # the west door onto the T2 terrace: iron, lever inside
    for z in (-1, 0, 1):
        for y in range(f - 1, f + 4):
            bp.set(-39, y, z, CHIS if z or y in (f - 1, f + 3) else CUT)
            bp.set(-40, y, z, CHIS if z or y in (f - 1, f + 3) else CUT)
    for x in (-38, -40):
        for y in (f, f + 1):
            bp.set(x, y, 0, AIR)
        bp.set(x, f - 1, 0, CUT)
    bp.door(-39, f, 0, "west", wood="iron")
    lever(bp, -38, f + 1, 1, "east")
    carve(bp, -41, f, -1, -41, f + 2, 1)          # the riser's pilaster in front of the door
    # the astronomer-king's inner tomb (north), behind a broken seal
    room(bp, -37, f, -30, -30, f + 6, -23, wall=lambda x, y, z: CHIS if y == f + 6 else CUT,
         floor=lambda x, z: GOLD if (x, z) in ((-34, -27), (-33, -27), (-34, -26), (-33, -26)) else SMO)
    for x in range(-37, -29):
        for y in range(f, f + 6):
            bp.set(x, y, -22, CHIS if y == f + 5 else CUT)
    for x in (-34, -33):
        for y in range(f, f + 3):
            bp.set(x, y, -22, AIR)
    bp.set(-35, f, -22, MUD)
    bp.set(-32, f + 1, -22, MUD)
    for x in range(-35, -31):
        for z in (-28, -27, -26):
            bp.set(x, f, z, GILD if z == -27 else BRASS)
    for x in range(-35, -31):
        bp.set(x, f + 1, -27, GOLD if x in (-34, -33) else GILD)
    bp.chest(-36, f, -29, "south", loot=LOOT + "sz_crypt")
    pot(bp, -31, f, -29)
    pot(bp, -36, f, -24, cracked=True)
    candle(bp, -31, f, -24, 4)
    hang(bp, -33, f + 4, -25, SOUL_H)


# ------------------------------------------------------------------ the sun chamber (arena), vault, lift
def dome_top(d):
    return AR_WALL + (AR_TOP - AR_WALL) * max(0.0, 1 - (d / AR_R) ** 2)


def arena(bp):
    f = FA
    n = int(AR_W) + 2
    for x in range(-n, n + 1):
        for z in range(-n, n + 1):
            d = math.hypot(x, z)
            if d > AR_W:
                continue
            top = dome_top(min(d, AR_R))
            for y in range(f - 2, AR_TOP + 3):
                if d <= AR_R and f <= y < top:
                    bp.set(x, y, z, AIR)
                elif d <= AR_R and y == f - 1:
                    a = (math.degrees(math.atan2(z, x)) + 360) % 360
                    if d < 3.2:
                        spec = GOLD
                    elif d < 4.4:
                        spec = GILD
                    elif int(a / 15) % 2 == 0 and d < 14:
                        spec = SMO
                    elif int(a / 15) % 4 == 1 and d < 14:
                        spec = BTILE
                    else:
                        spec = CUT
                    if 14.4 <= d < 15.4:
                        spec = CHIS
                    bp.set(x, y, z, spec)
                elif d <= AR_R and y < f - 1:
                    bp.set(x, y, z, body(x, y, z))
                elif d <= AR_R and y >= top and y <= top + 2:
                    a = (math.degrees(math.atan2(z, x)) + 360) % 360
                    bp.set(x, y, z, BRASS if int(a) % 45 < 4 else (BTILE if y < top + 1 else SMO))
                elif d > AR_R and y <= AR_WALL + 1:
                    bp.set(x, y, z, inner(x, y, z) if d < AR_R + 1.2 else body(x, y, z))
                elif d > AR_R and y <= AR_WALL + 3:
                    ensure(bp, x, y, z, body(x, y, z))
    # the wall: eight brass sun-ray pilasters, lamps between
    for k in range(16):
        a = k * math.pi / 8
        x, z = round(AR_R * math.cos(a) + 0.6 * math.cos(a)), round(AR_R * math.sin(a) + 0.6 * math.sin(a))
        x2, z2 = round((AR_R - 0.3) * math.cos(a)), round((AR_R - 0.3) * math.sin(a))
        if k % 2 == 0:
            for y in range(f, AR_WALL + 1):
                bp.set(x, y, z, BRASS if y % 4 else GILD)
        else:
            bp.set(x, f + 4, z, EDISON)
            bp.set(x, f + 8, z, EDISON)
    # the light shaft from the lens down to the sun disc
    for x in range(-2, 3):
        for z in range(-2, 3):
            for y in range(f, FL):
                if bp.get(x, y, z) != AIR:
                    bp.set(x, y, z, AIR)
    for x in range(-3, 4):
        for z in range(-3, 4):
            if max(abs(x), abs(z)) == 3:
                for y in range(int(dome_top(3)), FL - 1):
                    bp.set(x, y, z, BRASS if y % 3 == 0 else SMO)
    bp.boss_seal(0, f - 1, 0, BOSS, 16)
    # entrance: from the antechamber corridor (west), the mist across it
    carve(bp, -26, f, 3, -15, f + 3, 5)
    for x in range(-26, -15):
        for z in (3, 4, 5):
            bp.set(x, f - 1, z, pave(x, z))
        for y in range(f - 1, f + 5):
            for z in (2, 6):
                if math.hypot(x, z) > AR_R:
                    bp.set(x, y, z, inner(x, y, z))
        if math.hypot(x, 4) > AR_R:
            bp.set(x, f + 4, 3, inner(x, f + 4, 3))
            bp.set(x, f + 4, 4, inner(x, f + 4, 4))
            bp.set(x, f + 4, 5, inner(x, f + 4, 5))
    bp.mist(-17, f, 3, -17, f + 3, 5)
    # exit north: the passage to the vault, sealed bars
    carve(bp, -1, f, -21, 1, f + 2, -16)
    for z in range(-21, -15):
        for x in (-2, 2):
            for y in range(f - 1, f + 4):
                if math.hypot(x, z) > AR_R:
                    bp.set(x, y, z, CHIS if y == f + 3 else CUT)
        for x in (-1, 0, 1):
            if math.hypot(x, z) > AR_R:
                bp.set(x, f + 3, z, CHIS)
                bp.set(x, f - 1, z, pave(x, z))
    for x in (-1, 0, 1):
        for y in range(f, f + 3):
            bp.set(x, y, -19, MOD["vault_bars"])
    antechamber(bp)
    vault(bp)
    lift(bp)


def antechamber(bp):
    f = FA
    cx, cz = NEWEL_A
    room(bp, -29, f, 17, -26, f + 4, 26, wall=inner, floor=pave)
    room(bp, -29, f, 3, -27, f + 3, 16, wall=inner, floor=pave)
    carve(bp, -29, f, 16, -27, f + 3, 17)
    bp.set(-28, f, 25, MOD["waystone"])
    bp.set(-26, f, 26, "lectern[facing=west,has_book=false,powered=false]")
    candle(bp, -29, f, 18, 4)
    hang(bp, -27, f + 3, 21, LANT_H)
    hang(bp, -28, f + 2, 9, LANT_H)


def vault(bp):
    f = FA
    room(bp, -6, f, -26, 6, f + 4, -22, wall=lambda x, y, z: CUT if (x + y) % 3 else CHIS,
         floor=lambda x, z: GILD if (x + z) % 2 else SMO)
    bp.chest(-6, f, -24, "east", loot=LOOT + "sz_vault")
    bp.chest(6, f, -24, "west", loot=LOOT + "sz_vault")
    bp.chest(-3, f, -26, "south", loot=LOOT + "sz_vault")
    for x in (-5, 5):
        bp.set(x, f, -26, GOLD)
        bp.set(x, f + 1, -26, LANT)
    bp.set(3, f, -26, GOLD)
    hang(bp, 0, f + 3, -24, CHANDELIER)
    carve(bp, -1, f, -27, 1, f + 2, -27)


def lift(bp):
    """The sun lift: from the room behind the vault, a drop well (x -4..-2) 44 blocks down into a pool in the lift hall,
    and beside it a bubble-column tube (x 3) back up. Signs hold the water at the tube's foot."""
    f = FA
    room(bp, -4, f, -30, 4, f + 3, -28, wall=inner, floor=pave)
    for x in range(-5, 6):
        for z in range(-31, -26):
            for y in range(7, f - 1):
                ensure(bp, x, y, z, inner(x, y, z))
    # the drop well
    for x in range(-4, -1):
        for z in range(-30, -27):
            for y in range(1, f):
                bp.set(x, y, z, AIR)
            for y in range(-2, 1):
                bp.set(x, y, z, WATER)
            bp.set(x, -3, z, CUT)
    for x in range(-5, 0):
        for z in range(-31, -26):
            if x in (-5, -1) or z in (-31, -27):
                for y in range(-3, 1):
                    ensure(bp, x, y, z, CUT)
                for y in range(7, f):
                    bp.set(x, y, z, inner(x, y, z))
    for z in (-31, -27):
        for x in range(-5, 0):
            for y in range(7, f):
                bp.set(x, y, z, inner(x, y, z))
    for z in range(-30, -27):
        railing(bp, -1, f, z, "west") if z != -29 else None
    # the bubble-column tube
    bp.set(3, 0, -29, "soul_sand")
    for y in range(1, f):
        bp.set(3, y, -29, "bubble_column[drag=false]")
        for (x, z) in ((2, -30), (3, -30), (4, -30), (2, -29), (4, -29), (2, -28), (3, -28), (4, -28)):
            if y <= 2 and (x, z) == (3, -28):
                continue
            bp.set(x, y, z, "glass" if (y % 6) else BRASS)
    bp.set(3, 1, -28, "spruce_sign[rotation=0,waterlogged=false]")
    bp.set(3, 2, -28, "spruce_wall_sign[facing=south,waterlogged=false]")
    bp.set(3, 2, -29, "bubble_column[drag=false]")
    bp.set(4, 2, -28, BRASS)
    bp.set(2, 2, -28, BRASS)
    bp.set(3, 3, -28, BRASS)
    for (x, z) in ((2, -30), (3, -30), (4, -30), (2, -29), (4, -29), (2, -28), (3, -28), (4, -28)):
        bp.set(x, f - 1, z, "glass")
    bp.set(3, f - 1, -29, "bubble_column[drag=false]")
    hang(bp, 0, f + 2, -29, LANT_H)


# ------------------------------------------------------------------ lens-keepers' tower, calibration chamber, summit
def annex(bp):
    x0, z0, x1, z1 = ANNEX
    top = 74
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            ybase = ptop(x, z) + 1
            for y in range(ybase, top + 1):
                if edge or y == top:
                    corner = x in (x0, x1) and z in (z0, z1)
                    spec = CHIS if corner and y % 4 == 0 else (BRASS if y == top - 1 else body(x, y, z))
                    bp.set(x, y, z, spec)
    # buttresses on the free faces, blind arches, a cornice, the copper dome and its finial
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            on_t = ptop(x, z)
            if on_t >= FS - 1:
                continue                                  # the summit platform side stays clear
            if x in (x0 - 1, x1 + 1) and (z - z0) % 4 == 0 or z in (z0 - 1, z1 + 1) and (x - x0) % 5 == 0:
                for y in range(on_t + 1, top - 1):
                    bp.set(x, y, z, CUT if y % 6 else CHIS)
            fc = "east" if x == x0 - 1 else "west" if x == x1 + 1 else "south" if z == z0 - 1 else "north"
            bp.set(x, top - 1, z, stair(SMO_ST, fc, "top"))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            d = math.hypot(x - cx, z - cz)
            for y in range(top + 1, top + 8):
                rr = 6.5 * math.sqrt(max(0.0, 1 - ((y - top) / 7.5) ** 2))
                if d <= rr:
                    bp.set(x, y, z, (VERD if (y + x) % 5 else BRASS) if d > rr - 1.2 else COPPER)
            if d <= 7.2 and (x in (x0, x1) or z in (z0, z1) or d > 6.5):
                bp.set(x, top + 1, z, CUT)
    for y in range(top + 7, top + 11):
        bp.set(round(cx), y, round(cz), BRASS if y < top + 10 else GOLD)
    # the roof is a lookout: a railing round it, a stair up from the summit platform (east)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x in (x0, x1) or z in (z0, z1)) and bp.get(x, top + 1, z) is None:
                if x == x1 and 10 <= z <= 12:
                    continue
                railing(bp, x, top + 1, z, "west" if x == x0 else "east" if x == x1 else
                        "north" if z == z0 else "south")
    for i, x in enumerate(range(x1 + 4, x1, -1)):
        for z in range(10, 13):
            for y in range(FS - 1, FS + i):
                bp.set(x, y, z, CUT)
            bp.set(x, FS + i, z, stair(SS_ST, "west"))
            for y in range(FS + i + 1, FS + i + 5):
                bp.set(x, y, z, AIR)
    # the newel inside: feet 45 (the antechamber) -> 63 (the vestibule to the calibration chamber)
    ncx, ncz = NEWEL_A
    land = build_newel(bp, ncx, ncz, FA, 6, 2, FL + 4)
    newel_door(bp, ncx, ncz, land[0], "x")        # SW landing -> west: the antechamber
    newel_door(bp, ncx, ncz, land[3], "x")        # NW landing -> west: the T4 terrace (iron door)
    newel_door(bp, ncx, ncz, land[6], "z")        # NE landing -> north: the vestibule
    # T4 door: iron, lever inside
    sx, sz, f4 = land[3]
    for z in range(ncz - 4, ncz - 1):
        for y in range(f4, f4 + 3):
            bp.set(ncx - 5, y, z, CHIS)
    bp.door(ncx - 5, f4, ncz - 3, "west", wood="iron")
    lever(bp, ncx - 4, f4 + 1, ncz - 4, "east")
    for z in range(ncz - 4, ncz - 1):
        bp.set(ncx - 6, f4 - 1, z, tread(ncx - 6, z))
        for y in range(f4, f4 + 4):
            bp.set(ncx - 6, y, z, AIR)
    # the vestibule (an L from the newel's top to the chamber)
    room(bp, -18, FL, 10, -16, FL + 3, 14, wall=inner, floor=pave)
    room(bp, -15, FL, 10, -13, FL + 3, 12, wall=inner, floor=pave)
    carve(bp, -16, FL, 10, -15, FL + 3, 12)
    hang(bp, -17, FL + 3, 12, LANT_H)


def calibration(bp):
    f = FL
    room(bp, -12, f, -12, 12, f + 5, 12, wall=inner,
         floor=lambda x, z: BRASS if max(abs(x), abs(z)) in (4, 9) else ("brasshaven:diamond_plate" if (x + z) % 2
                                                                     else CUT))
    # the light shaft through the middle in a glass drum
    for x in range(-3, 4):
        for z in range(-3, 4):
            m = max(abs(x), abs(z))
            for y in range(f - 1, f + 6):
                if m <= 2:
                    bp.set(x, y, z, AIR)
                elif m == 3:
                    bp.set(x, y, z, BRASS if (y == f - 1 or y == f + 5 or (abs(x) == 3 and abs(z) == 3)) else GLASS_Y)
    # four calibration arms: brass rails with mirrors (glass panes) on gimbals, pointing at the drum
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for i in range(5, 9):
            x, z = dx * i, dz * i
            bp.set(x, f, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if i < 8 else IRON)
        bp.set(dx * 8, f + 1, dz * 8, BRASS)
        bp.set(dx * 8, f + 2, dz * 8, GLASS_O)
    # pillars at the corners of the inner ring
    for sx in (-1, 1):
        for sz in (-1, 1):
            for x in range(sx * 9, sx * 9 + sx * 2, sx):
                for z in range(sz * 9, sz * 9 + sz * 2, sz):
                    for y in range(f, f + 6):
                        bp.set(x, y, z, CHIS if y in (f, f + 5) else (GEAR if y == f + 3 else SMO))
    # benches: grindstone, stonecutter, lecterns, a cartography table; pipes and gauges on the walls
    bp.set(11, f, -11, "grindstone[face=floor,facing=north]")
    bp.set(10, f, -11, "stonecutter[facing=north]")
    bp.set(-11, f, -11, "cartography_table")
    bp.set(-11, f, -6, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(11, f, 6, "lectern[facing=west,has_book=false,powered=false]")
    for z in range(-12, 13, 3):
        for y in range(f, f + 5):
            bp.set(13, y, z, COPPER if y < f + 4 else BRASS) if abs(z) > 3 else None
        bp.set(-13, f + 2, z, GAUGE) if abs(z) > 3 and z < 9 else None
    bp.chest(11, f, 11, "west", loot=LOOT + "sz_lens")
    bp.chest(-6, f, -12, "south", loot=LOOT + "sz_lens")
    bp.barrel(12, f, -8)
    bp.spawner(7, f, -7, MOB_SPIDER)
    for (x, z) in ((-6, 6), (6, 6), (-6, -6), (6, -6)):
        hang(bp, x, f + 4, z, CHANDELIER)
    # the lens gate (south) and its frame
    carve(bp, -1, f, 13, 1, f + 3, 15)
    for z in (13, 14, 15):
        for x in (-1, 0, 1):
            bp.set(x, f - 1, z, CUT)
    for y in range(f, f + 5):
        bp.set(-2, y, 16, CHIS if y % 2 else CUT)
        bp.set(2, y, 16, CHIS if y % 2 else CUT)
    for x in range(-2, 3):
        bp.set(x, f + 4, 16, CHIS)
        bp.set(x, f + 5, 16, BRASS)
    bp.set(0, f + 6, 16, GOLD)


def summit(bp):
    f = FS
    # the lens: a bulging disc of amber glass in a brass collar over the shaft
    for x in range(-6, 7):
        for z in range(-6, 7):
            d = math.hypot(x, z)
            if d <= 4.3:
                bp.set(x, f - 1, z, GLASS_O if d < 1.5 else GLASS_Y)
            elif d <= 5.4:
                bp.set(x, f - 1, z, BRASS)
                railing(bp, x, f, z, "north" if abs(z) >= abs(x) and z < 0 else "south" if abs(z) >= abs(x) else
                        ("west" if x < 0 else "east"))
            if d <= 2.6:
                bp.set(x, f, z, GLASS_Y)
    for x in range(-4, 5):
        for z in range(-4, 5):
            if max(abs(x), abs(z)) <= 2 and math.hypot(x, z) > 4.3:
                pass
    # the floor of the summit platform: brass-banded paving
    for x in range(-14, 15):
        for z in range(-14, 15):
            d = math.hypot(x, z)
            if d > 5.4:
                bp.set(x, f - 1, z, BTILE if 9.5 <= d < 10.5 else tread(x, z))
    # the chest and a spyglass stand beside the lens
    bp.chest(7, f, -7, "west", loot=LOOT + "sz_summit")
    bp.set(-7, f, 7, IRON_WALL)
    bp.set(-7, f + 1, 7, BRASS)
    orrery(bp)


def orrery(bp):
    """The tripod orrery: four brass legs (3 thick) from the summit's corners to an apex 30 above the lens, two orbit
    rings carried by the legs with their planets, and the sun hung from the apex on a chain over the lens."""
    f = FS
    apex = (0, 101, 0)
    legs = [(sx * 12, f, sz * 12) if (sx, sz) != (-1, 1) else (-14, 75, 14) for sx in (-1, 1) for sz in (-1, 1)]
    for (lx, ly, lz) in legs:
        n = 120
        r0 = math.hypot(lx, lz)
        for i in range(n + 1):
            t = i / n
            bow = 6.0 * math.sin(math.pi * t)             # the legs bow outward like a tripod's
            x = lx * (1 - t) + lx / r0 * bow
            z = lz * (1 - t) + lz / r0 * bow
            y = ly + (apex[1] - ly) * t
            spec = GILD if i % 12 == 0 else BRASS
            thick = 1 if t < 0.8 else 0
            for dx in range(-thick, thick + 1):
                for dz in range(-thick, thick + 1):
                    if abs(dx) + abs(dz) <= 1:
                        bp.set(round(x) + dx, round(y), round(z) + dz, spec)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                bp.set(lx + dx, ly, lz + dz, BRASS if max(abs(dx), abs(dz)) < 2 else GILD)
                if max(abs(dx), abs(dz)) < 2:
                    bp.set(lx + dx, ly + 1, lz + dz, BRASS)
    for (r, y, planets) in ((17.5, 80, ((25, COPPER, 3.0), (145, VERD, 2.4), (260, "brasshaven:zinc_block", 2.0))),
                            (12.0, 89, ((80, IRON, 2.2), (215, GOLD, 2.8)))):
        for k in range(int(2 * math.pi * r * 3)):
            a = k / (r * 3)
            for dr in (-0.5, 0.5):
                bp.set(round((r + dr) * math.cos(a)), y, round((r + dr) * math.sin(a)), BRASS)
        for deg, spec, pr in planets:
            a = math.radians(deg)
            px, pz = r * math.cos(a), r * math.sin(a)
            cy = y + pr + 1.5
            for x in range(int(px - pr) - 1, int(px + pr) + 2):
                for yy in range(int(cy - pr) - 1, int(cy + pr) + 2):
                    for z in range(int(pz - pr) - 1, int(pz + pr) + 2):
                        if math.sqrt((x - px) ** 2 + (yy - cy) ** 2 + (z - pz) ** 2) <= pr + 0.3:
                            bp.set(x, yy, z, spec)
            bp.set(round(px), y + 1, round(pz), BRASS)
    # the sun: a glowing sphere in a brass cage, hung from the apex
    sy = 93
    for x in range(-5, 6):
        for y in range(sy - 5, sy + 6):
            for z in range(-5, 6):
                d = math.sqrt(x * x + (y - sy) ** 2 + z * z)
                if d <= 3.6:
                    bp.set(x, y, z, "shroomlight" if d > 2.4 else "glowstone")
                elif d <= 4.5 and (x == 0 or z == 0 or y >= sy):
                    bp.set(x, y, z, BRASS)
    for y in range(sy + 3, apex[1] + 1):
        rr = 4.6 - (y - sy - 3) * 0.75
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if math.hypot(dx, dz) <= rr:
                    bp.set(dx, y, dz, GILD if (y + dx + dz) % 3 == 0 else BRASS)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 2:
                bp.set(dx, apex[1], dz, BRASS)
    bp.set(0, apex[1] + 1, 0, BRASS)
    bp.set(0, apex[1] + 2, 0, GOLD)


# ------------------------------------------------------------------ ground: apron, dunes, the camp
def apron(bp):
    """A ring of sand and paving round the plinth (air cleared above it so a dune never buries the walk), sand
    banked against the north and west feet, footings so it never floats over a dip."""
    for x in range(-78, 79):
        for z in range(-78, 79):
            r = cheb(x, z)
            if r <= RMAX + 1 or (abs(x) <= 18 and z >= 72):
                continue
            h = hash01(x, z, 111)
            spec = SAND if h < 0.8 else ("smooth_sandstone" if r <= 74 else "sandstone")
            if r <= 74 and z > 0 and abs(x) < 40:
                spec = CUT if (x + z) % 3 else SMO
            bp.set(x, 0, z, spec)
            bp.set(x, -1, z, SS)
            bp.set(x, -2, z, SAND)
            bank = 0
            if (z < -RMAX or x < -RMAX) and r <= 76:
                bank = max(0, 2 - (r - RMAX - 1)) if hash01(x // 3, z // 3, 112) < 0.6 else 0
            for y in range(1, 6):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, SAND if y <= bank else AIR)
    # paved strip in front of the plinth's south foot, between the side stairs
    for x in range(-40, 41):
        for z in range(71, 76):
            if bp.get(x, 0, z) is not None and abs(x) > 6:
                bp.set(x, 0, z, CUT if (x + z) % 3 else SMO)


def dunes(bp):
    for (cx, cz, r, h, sd) in ((46, 118, 15, 7, 1), (-48, 112, 17, 8, 2), (60, 92, 12, 5, 3), (-66, 92, 13, 6, 4),
                               (34, 140, 9, 4, 5), (-30, 138, 11, 5, 6), (86, -40, 10, 5, 7), (-86, 30, 9, 4, 8)):
        for x in range(cx - r - 2, cx + r + 3):
            for z in range(cz - r - 2, cz + r + 3):
                if not (SX0 <= x <= SX1 and SZ0 <= z <= SZ1):
                    continue
                if cheb(x, z) <= 79 or abs(x) <= 19 and z >= 70:
                    continue
                # crescent dunes: steeper on the lee (north-west) side
                dx, dz = x - cx, z - cz
                lee = (dx + dz) < 0
                d = math.hypot(dx * (1.4 if lee else 1.0), dz * (1.4 if lee else 1.0))
                if d > r:
                    continue
                n = h * (1 - (d / r) ** 1.8) + (hash01(x, z, 120 + sd) - 0.5) * 1.5
                top = int(round(n))
                if top < 1:
                    continue
                for y in range(-2, top + 1):
                    bp.set(x, y, z, SAND if y >= 0 else SS)
                if hash01(x, z, 130 + sd) < 0.012:
                    bp.set(x, top + 1, z, "dead_bush")


def camp(bp):
    """The caravan camp beside the avenue's start: two striped tents, a fire, crates and the entrance waystone."""
    cx, cz = 30, 138
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 7, cz + 8):
            if bp.get(x, 0, z) in (None, "minecraft:sand"):
                for y in range(1, 6):
                    if bp.get(x, y, z) not in (None, AIR):
                        bp.set(x, y, z, AIR)
                bp.set(x, 0, z, SAND if hash01(x, z, 141) < 0.7 else "coarse_dirt")
                bp.set(x, -1, z, SS)
    for (tx, tz, col) in ((cx - 5, cz - 3, "white"), (cx + 3, cz + 2, "orange")):
        for z in range(tz, tz + 5):
            bp.set(tx, 1, z, "spruce_fence")
            bp.set(tx + 4, 1, z, "spruce_fence")
            bp.set(tx, 2, z, f"{col}_wool")
            bp.set(tx + 4, 2, z, f"{col}_wool")
            for x in range(tx + 1, tx + 4):
                bp.set(x, 3 if x != tx + 2 else 4, z, f"{col if (z % 2) else 'brown'}_wool")
            bp.set(tx + 1, 3, z, f"{col}_wool")
            bp.set(tx + 3, 3, z, f"{col}_wool")
    bp.chest(cx - 4, 1, cz - 2, "east", loot=LOOT + "sz_camp")
    bp.barrel(cx + 4, 1, cz + 6)
    bp.set(cx + 5, 1, cz + 6, "barrel[facing=up,open=false]")
    bp.set(cx, 1, cz + 7, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    for (x, z) in ((cx - 1, cz + 6), (cx + 1, cz + 6)):
        bp.set(x, 1, z, stair("spruce_stairs", "south"))
    bp.set(cx - 7, 1, cz + 5, "hay_block[axis=y]")
    bp.set(cx - 7, 2, cz + 5, "hay_block[axis=y]")
    # the entrance waystone at the avenue's start
    bp.set(18, 1, 146, MOD["waystone"])
    bp.set(18, 0, 146, CUT)


# ------------------------------------------------------------------ closing the shells
def seal(bp):
    """Close every hole the rooms cut toward the hidden core: an unset cell inside the pyramid next to an open cell
    gets masonry, so no carved room opens into the void."""
    masonry = {"minecraft:" + m for m in (SS, CUT, SMO, CHIS, MUD, PMUD, TERRA, BTERRA, "sand")}
    opened = [p for p, v in bp.blocks.items() if not is_solid(v[0]) or v[0] not in masonry]
    for (x, y, z) in opened:
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            q = (x + dx, y + dy, z + dz)
            if q in bp.blocks:
                continue
            if in_mass(*q) or (ANNEX[0] <= q[0] <= ANNEX[2] and ANNEX[1] <= q[2] <= ANNEX[3] and q[1] <= 74):
                bp.set(*q, body(*q))


def footings(bp):
    """Two blocks of footing under every ground-level block that stands outside the plinth (stairs, plinths,
    camp), so nothing floats over a dip (foundation=False)."""
    feet = [(x, z) for (x, y, z), v in list(bp.blocks.items()) if y == 0 and v[0] not in (AIR, "minecraft:water")
            and cheb(x, z) > RMAX]
    for x, z in feet:
        for d in (1, 2):
            if bp.get(x, -d, z) is None:
                bp.set(x, -d, z, SS if d == 1 else SAND)


# ------------------------------------------------------------------ builder
def sun_ziggurat(bp):
    apron(bp)
    pyramid(bp)
    riser_details(bp)
    wind_sand(bp)
    processional(bp)
    avenue(bp)
    pylon(bp)
    annex(bp)
    lower_halls(bp)
    offerings(bp)
    hypostyle(bp)
    side_newel(bp)
    priests_quarter(bp)
    tomb_gallery(bp)
    arena(bp)
    calibration(bp)
    summit(bp)
    terrace_stairs(bp)
    dunes(bp)
    camp(bp)
    seal(bp)
    footings(bp)


VIEWS = [
    ("offerings", (0, FH, 45), (0, FH + 4, 34)),
    ("hypostyle", (3, FH, 23), (-4, FH + 9, -20)),
    ("hall_of_sand", (-14, 1, 21), (2, 6, -12)),
    ("priests_quarter", (34, FQ, 5), (38, FQ + 1, -3)),
    ("tomb_gallery", (-33, FQ, 19), (-34, FQ + 2, -21)),
    ("calibration", (-9, FL, 9), (0, FL + 3, 0)),
    ("sun_chamber", (-14, FA, 4), (8, FA + 7, -5)),
]

register(StructureDef(
    "sun_ziggurat", "overworld", ["desert"],
    [Piece("ziggurat", sun_ziggurat, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_HUSK, 8, 1, 2), (MOB_CRAWLER, 3, 1, 1)],
    title_fr="La Ziggourat du Moteur solaire", title_en="Sun-Engine Ziggurat"))
