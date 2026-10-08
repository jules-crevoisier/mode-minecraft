"""Rust Mesa Mine-City (La Ville minière de la Mesa rouille): a boomtown carved into and stacked on a striped badlands
butte. Colossal tier (tools/BUILDING.md §1, §12 concept 20, §10 legacy-dungeon template, §15), western mining town
with steampunk machinery (brass winding gear, gauges, copper pipes in the hoist house and the stamp mill).

Silhouette (one noun phrase, §15.1): a red-and-cream striped flat-topped butte with a timber-and-iron headframe on its
summit carrying a giant spoked winding wheel, a false-front town at its foot and a railway on tall trestles wrapped
once round its flanks.

Layout, ground y = 0 (feet 1), x east, z south. The butte is a superellipse (exponent 2.8) centred on (0, -20), four
tiers with noisy faces (two-octave fbm, gullies, erosion grooves, battered toes, jittered terracotta strata): radii
46 / 40 / 34 / 28, tops 14 / 28 / 42 / 56, so the terraces T1, T2, T3 have feet 15, 29, 43 and the summit feet 57.
A cleft (box canyon) splits the south-east shoulder at x ~31.
  * the approach (south): the stagecoach camp and its waystone at z ~116, a timber gate arch framing the headframe
    (the reveal), Main Street with false-front buildings (Gilded Pick saloon, general store, livery; hotel, bank and
    assay office, sheriff and jail), the town square with the well, the water tower and the railway station;
  * the climb: the grand stair up the talus to T1 (Rusty Spur saloon, two storeys, its back room cut into the rock),
    cliff stairs T1 -> T2 (Copper Kettle saloon, bunkhouse) -> T3 (telegraph office) -> the summit; trestle bridges
    span the cleft at T1 and T2 to the east shoulder (smithy, lookout) and a ladder joins them (a loop); the mine-cart
    railway spirals from the station round the east, north and west faces on trestles and rock cuts to the summit;
  * the summit (hub): the headframe over the main shaft, its winding wheel (radius 9) facing the town, the hoist house
    (winding drum, boiler, site of grace), the railway terminus and the ore tipple;
  * inside, down: a stairwell under the hoist house to the stamp mill (three stepped floors 43 / 36 / 29, a battery
    of ten stamps on a camshaft, two giant gears and a flywheel, amalgamation tables), a stairwell under the mill to
    level 15 (the dynamite store, the drift to the Rusty Spur's back room, the mine-boss office and its vault), a
    stairwell to the haulage level (feet 1: rails, the shaft station with a site of grace, the east adit portal), the
    winze down to the flooded lower gallery (a catwalk over black water, a drowned stope), the collapsed shaft (a ramp
    spiralling 19 down round the wreck of the fallen cage), a drainage tunnel, the antechamber (site of grace), a
    narrow tunnel (compression) and the mist;
  * the boss (feet -30): a vast excavated cavern (42 across, 22 high) round a half-dug colossal gold-and-copper vein
    with scaffolds, ladders and a derrick; behind sealed bars, the company strongroom (vault) and the cart-lift;
  * shortcuts (§10.4): the cart-lift (a bubble column in an iron cage, strongroom -> haulage level, iron door opening
    from the lift side only); the main shaft (a 55-block drop from the summit into the sump, a ladderway back up); the
    drift's iron door into the Rusty Spur (opens from the mine side); the mill's iron door onto T3 (opens from the
    mill side); the east adit (side route at ground level into the haulage level).
Loot gradient (§15.6): camp, town and terrace shacks tier 1; saloons and haulage 1-2; hoist house, mill, dynamite
store, collapsed shaft 2; office and drowned stope 2-3; office vault 3; strongroom 3-4.
Height budget: the wheel tops out at 107 above the ground layer; the strongroom lift reaches 32 below it.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, IRON, IRON_WALL, PIPES, TABLE, W, fbm, hash01,
                       hash3, vnoise)
from ..parts import LOOT, MOD

# the mine's own boss: the Mine Baron, the greedy foreman in his steam exo-rig, in the cavern round the vein
BOSS = "brasshaven:mine_baron"
MOB_HUSK = "minecraft:husk"
MOB_BANDIT = W + "bandit_marksman"
MOB_MITE = W + "rust_mite"
MOB_GUNNER = W + "boiler_gunner"
MOB_CRAWLER = W + "crypt_crawler"
MOB_CAVE = "minecraft:cave_spider"

# ------------------------------------------------------------------ dimensions
P = 2.8                                   # superellipse exponent of the butte's plan
MX, MZ = 0, -20                           # butte centre
R = (46, 40, 34, 28)                      # tier radii
TOPS = (14, 28, 42, 56)                   # tier top blocks
BOT = (0, 15, 29, 43)
F1, F2, F3, FP = 15, 29, 43, 57           # terrace feet and summit feet
SHAFT = (0, -22, 3, -20)                  # main shaft x0, z0, x1, z1 (ladder at x 0, the drop x 1..3)
WHEEL = (10.5, 98, -21)                   # winding wheel centre; radius 9, plane z -22..-20
MILL = (-21, -30, -4, -10)                # stamp mill hall x0, z0, x1, z1
FM_TOP, FM_STAMP, FM_PLATE = 43, 36, 29
FL = 15                                   # level 15 feet
FH = 1                                    # haulage level feet
FG = -11                                  # flooded gallery catwalk feet
FA = -30                                  # arena feet
AC = (8, -27)                             # cavern centre
AR = 21.0                                 # cavern floor radius
AR_APEX = -9                              # top air cell of the dome
CLEFT_X = 31

AIR = "minecraft:air"
WATER = "water[level=0]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
FENCE = "spruce_fence[east=false,north=false,south=false,west=false,waterlogged=false]"
PLANK, DPLANK = "spruce_planks", "dark_oak_planks"
POST = "stripped_spruce_log[axis=y]"
DPOST = "stripped_dark_oak_log[axis=y]"
RSS, CRSS, SRSS = "red_sandstone", "cut_red_sandstone", "smooth_red_sandstone"
RSS_ST, SRSS_ST = "red_sandstone_stairs", "smooth_red_sandstone_stairs"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def card(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def sgn(v):
    return (v > 0) - (v < 0)


def log_axis(d):
    return "x" if d in ("east", "west") else "z"


# ------------------------------------------------------------------ the site context
class Ctx:
    def __init__(self, bp):
        self.bp = bp
        self.keep = set()      # air cells reserved (passages, headroom): fills and posts stop there
        self.inner = set()     # carved interior air inside the butte: checked against breaches at the end
        self.wet = set()       # water cells placed by the build (lined like air underground)

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))

    def put(self, x, y, z, spec):
        """Set unless the cell is reserved air."""
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def clear(self, x, y, z, inner=False):
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))
        if inner:
            self.inner.add((x, y, z))

    def water(self, x, y, z):
        self.bp.set(x, y, z, WATER)
        self.wet.add((x, y, z))
        self.keep.discard((x, y, z))

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b


def carve(C, x0, y0, z0, x1, y1, z1, inner=True):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.clear(x, y, z, inner)


def fill(C, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def column_down(C, x, y, z, spec, floor=-3, maxd=60):
    """Fill down from y until a set solid block, reserved air, or `floor` (a footing in the ground)."""
    for yy in range(y, max(floor, y - maxd) - 1, -1):
        if (x, yy, z) in C.keep:
            return
        if C.solid(x, yy, z):
            return
        C.set(x, yy, z, spec(x, yy, z) if callable(spec) else spec)


def mroom(C, x0, z0, x1, z1, f, h, floor, wall=None, ceil=None, inner=True):
    """Air box x0..x1, z0..z1, feet f, h high; the floor at f - 1 is always laid; walls (one ring round it) and the
    ceiling at f + h only when given (else the rock stays), never over reserved air."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            ins = x0 <= x <= x1 and z0 <= z <= z1
            for y in range(f - 1, f + h + 1):
                if ins and f <= y < f + h:
                    C.clear(x, y, z, inner)
                elif ins and y == f - 1:
                    C.put(x, y, z, floor(x, z) if callable(floor) else floor)
                elif ins and y == f + h:
                    if ceil is not None:
                        C.put(x, y, z, ceil(x, y, z) if callable(ceil) else ceil)
                elif not ins and wall is not None:
                    C.put(x, y, z, wall(x, y, z) if callable(wall) else wall)


def flight(C, x0, z0, facing, n, f0, width, wdir, mat, head=4, support=None, inner=True):
    """n steps climbing toward `facing`: step k (1..n) at distance k - 1 from (x0, z0), its stair block at
    y = f0 + k - 1 (feet f0 + k), `width` cells toward `wdir`, `head` air cells over each tread; `support` fills
    under each tread down to the first solid block."""
    dx, dz = DV[facing]
    px, pz = DV[wdir]
    cells = []
    for k in range(1, n + 1):
        for w in range(width):
            x, z = x0 + dx * (k - 1) + px * w, z0 + dz * (k - 1) + pz * w
            y = f0 + k - 1
            for hh in range(1, head + 1):
                C.clear(x, y + hh, z, inner)
            C.set(x, y, z, stair(mat, facing))
            cells.append((x, y, z))
    if support:
        for (x, y, z) in cells:
            column_down(C, x, y - 1, z, support)
    return cells


def landing(C, x0, z0, x1, z1, f, spec, head=4, support=None, inner=True):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            C.set(x, f - 1, z, spec(x, z) if callable(spec) else spec)
            for hh in range(head):
                C.clear(x, f + hh, z, inner)
            if support:
                column_down(C, x, f - 2, z, support)


def hang(C, x, y, z, lamp=LANT_H, reach=16):
    """A lamp on a chain from the first solid block above (x, y, z)."""
    top = y + 1
    while top < y + reach and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return
    for yy in range(y + 1, top):
        C.set(x, yy, z, CHAIN)
    C.set(x, y, z, lamp)


def lever(C, x, y, z, facing):
    C.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{W}brass_railing[facing={facing}]")


# ------------------------------------------------------------------ materials
def _bands():
    out = {}
    y, k = -45, 0
    while y < 90:
        t = 2 + int(hash01(k, 3, 701) * 4)
        h = hash01(k, 5, 702)
        if y < 6:
            pal = ("brown_terracotta", "red_terracotta", "terracotta", "brown_terracotta", "orange_terracotta")
        elif y < 30:
            pal = ("orange_terracotta", "terracotta", "red_terracotta", "yellow_terracotta", "orange_terracotta",
                   "white_terracotta", "light_gray_terracotta", "red_terracotta")
        else:
            pal = ("orange_terracotta", "yellow_terracotta", "white_terracotta", "terracotta", "red_terracotta",
                   "orange_terracotta", "light_gray_terracotta")
        c = pal[int(h * len(pal)) % len(pal)]
        if out.get(y - 1) == c:
            c = pal[(int(h * len(pal)) + 1) % len(pal)]
        for yy in range(y, y + t):
            out[yy] = c
        y += t
        k += 1
    return out


BANDS = _bands()


def rock(x, y, z):
    """The butte's strata: horizontal terracotta bands with a smooth +-2 jitter (§5 no sandwiching)."""
    j = int(round((vnoise(x * 0.9 + z * 0.4, z * 0.9 - x * 0.3, 11.0, 703) - 0.5) * 4.6))
    return "minecraft:" + BANDS.get(y + j, "terracotta")


def deep(x, y, z):
    """Rock under the ground layer: terracotta first, then stone, tuff and deepslate going down."""
    if y > -7 + int(hash01(x // 3, z // 3, 704) * 3):
        return rock(x, y, z)
    h = hash3(x, y, z, 705)
    if y < -22:
        return "deepslate" if h < 0.5 else ("cobbled_deepslate" if h < 0.7 else "tuff" if h < 0.92 else "stone")
    return "stone" if h < 0.45 else ("tuff" if h < 0.7 else "andesite" if h < 0.85 else "deepslate")


def cave_wall(x, y, z):
    """The excavated cavern's lining: deep rock with gold and copper flecks."""
    h = hash3(x, y, z, 706)
    if h < 0.035:
        return "deepslate_gold_ore" if y < -20 else "gold_ore"
    if h < 0.08:
        return "deepslate_copper_ore" if y < -20 else "copper_ore"
    return deep(x, y, z)


def dust(x, z):
    """Top dressing of every flat rock surface."""
    h = hash01(x, z, 707)
    return "red_sand" if h < 0.6 else ("coarse_dirt" if h < 0.82 else "terracotta" if h < 0.92 else "orange_terracotta")


def mine_floor(x, z):
    h = hash01(x, z, 708)
    return "coarse_dirt" if h < 0.35 else ("packed_mud" if h < 0.6 else "gravel" if h < 0.72 else "terracotta")


def boards(x, z):
    return DPLANK if (x * 3 + z) % 7 == 0 else PLANK


def masonry(x, y, z):
    h = hash3(x, y, z, 709)
    return CRSS if h < 0.5 else (RSS if h < 0.8 else SRSS)


# ------------------------------------------------------------------ the butte
def sd(x, z):
    return (abs(x - MX) ** P + abs(z - MZ) ** P) ** (1.0 / P)


def tier_y(y):
    for k in range(4):
        if y <= TOPS[k]:
            return k
    return 4


def south_w(ang):
    """1 on the south face (calm, terraced, built on), falling to 0 by 60 degrees off it."""
    d = abs(ang - math.pi / 2)
    return max(0.0, 1.0 - d / 1.05)


GULLIES = ((-160, 4.0, 5.0), (-118, 3.0, 4.0), (-72, 5.0, 6.0), (-34, 3.0, 4.0), (12, 4.0, 5.0), (150, 3.5, 5.0),
           (-8, 2.5, 3.0), (176, 3.0, 4.0))


def gully(ang, r):
    g = 0.0
    for deg, w, depth in GULLIES:
        da = (ang - math.radians(deg) + math.pi) % (2 * math.pi) - math.pi
        g = max(g, depth * max(0.0, 1.0 - abs(da) * r / w))
    return g


def tier_radii(x, z):
    ang = math.atan2(z - MZ, x - MX)
    ca, sa = math.cos(ang), math.sin(ang)
    sw = south_w(ang)
    out = []
    prev = 1e9
    for k in range(4):
        n1 = fbm(ca * R[k] + 40 * k, sa * R[k], 20.0, 710 + k) - 0.5
        n2 = vnoise(ca * R[k], sa * R[k] + 13 * k, 4.0, 720 + k) - 0.5
        r = R[k] + n1 * 6.0 * (1 - 0.8 * sw) + n2 * 2.2 * (1 - 0.6 * sw) - gully(ang, R[k]) * (1 - sw)
        r = min(r, prev - 4.0)
        out.append(r)
        prev = r
    return out, ca, sa, sw


def cleft_cut(x, y, z):
    """The box canyon splitting the south-east shoulder (open from the ground up, wider at the top)."""
    if z < -1 + (vnoise(x, y, 6.0, 731) - 0.5) * 3:
        return False
    cx = CLEFT_X + (vnoise(z, y * 0.5, 7.0, 732) - 0.5) * 2.4
    hw = 3.0 + y / 24.0
    return abs(x - cx) <= hw


def butte(C):
    bp = C.bp
    for x in range(-62, 63):
        for z in range(-84, 40):
            d = sd(x, z)
            if d > R[0] + 10:
                continue
            rk, ca, sa, sw = tier_radii(x, z)
            top = -1
            for y in range(0, TOPS[3] + 1):
                k = tier_y(y)
                g = (vnoise(ca * 30 + y * 2.3, sa * 30 - y * 1.7, 2.2, 730) - 0.5) * 1.5 * (1 - 0.5 * sw)
                toe = max(0, BOT[k] + 2 - y) * 0.6 if k > 0 else 0.0
                if d <= rk[k] + g + toe and not (y >= 1 and cleft_cut(x, y, z)):
                    bp.set(x, y, z, rock(x, y, z))
                    top = y
                else:
                    break
            if top >= 0:
                bp.set(x, top, z, dust(x, z))
                if hash01(x, z, 733) < 0.025 and top > 2:
                    bp.set(x, top + 1, z, "dead_bush" if hash01(x, z, 734) < 0.6 else "short_dry_grass")
            # footings under the butte's rim, talus round its foot (not where the town meets it)
            if d <= rk[0] and d > rk[0] - 4:
                for y in range(-8, 0):
                    bp.set(x, y, z, rock(x, y, z))
            elif rk[0] < d <= rk[0] + 7 and not (z > 14 and abs(x) < 36):
                t = int((rk[0] + 7 - d) / 7.0 * 4.5 + (hash01(x, z, 735) - 0.5) * 1.6)
                for y in range(-2, max(0, t) + 1):
                    bp.set(x, y, z, rock(x, y, z) if y < t else ("red_sand" if hash01(x, z, 736) < 0.7 else
                                                                 "coarse_dirt"))
                if t >= 1 and hash01(x, z, 737) < 0.03:
                    bp.set(x, t + 1, z, "dead_bush")
    # the cleft's floor: a dry wash of red sand and gravel with boulders
    for x in range(CLEFT_X - 8, CLEFT_X + 9):
        for z in range(-4, 30):
            if C.get(x, 1, z) is None and C.get(x, 0, z) is not None and sd(x, z) < R[0]:
                C.set(x, 0, z, "gravel" if hash01(x, z, 738) < 0.3 else "red_sand")
                if hash01(x, z, 739) < 0.03:
                    C.set(x, 1, z, "terracotta" if hash01(x, z, 740) < 0.5 else "brown_terracotta")


# ------------------------------------------------------------------ trestle decks: the railway and the bridges
def polyline(pts):
    cells, corners = [], [0]
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        dx, dz = sgn(bx - ax), sgn(bz - az)
        n = max(abs(bx - ax), abs(bz - az))
        for i in range(1 if cells else 0, n + 1):
            cells.append((ax + dx * i, az + dz * i))
        corners.append(len(cells) - 1)
    return cells, corners


def heights(cells, corners, ys, windows=None):
    """Rail heights: flat at every corner (two cells either side), rises spread evenly inside each leg; windows
    {segment: (lo, hi)} place a leg's rises at offsets lo..hi from its first corner instead."""
    y = [0] * len(cells)
    for s in range(len(corners) - 1):
        ia, ib = corners[s], corners[s + 1]
        ya, yb = ys[s], ys[s + 1]
        r = yb - ya
        if windows and s in windows:
            lo, hi = ia + windows[s][0], ia + windows[s][1]
        else:
            lo, hi = ia + 2, ib - 3
        span = hi - lo + 1
        assert r <= span, (s, r, span)
        rises = {lo + int((t + 0.5) * span / r) for t in range(r)} if r > 0 else set()
        assert len(rises) == r, (s, r, rises)
        cur = ya
        for j in range(ia, ib + 1):
            y[j] = cur
            if j in rises:
                cur += 1
        assert y[ib] == yb, (s, y[ib], yb)
    return y


def track(C, pts, ys, rail=True, windows=None, bent_every=4, deck=PLANK, keep_out=(), open_sides=(), no_bents=(),
          embank=0):
    """A deck 3 wide (a rail on the centre lane when ``rail``) with an edge beam and a fence each side, trestle bents
    (two posts, cross beams, X-bracing) down to the first solid block every ``bent_every`` cells, air 4 high over it
    (rock cuts where it meets the butte). Walk lanes take a stair where the rail climbs."""
    cells, corners = polyline(pts)
    n = len(cells)
    y = heights(cells, corners, ys, windows) if len(ys) == len(corners) else [ys[0]] * n
    roles = {}

    def want(x, z, prio, role, yy, d, rise):
        cur = roles.get((x, z))
        if cur is None or cur[0] < prio:
            roles[(x, z)] = (prio, role, yy, d, rise)

    dirs = []
    for j in range(n):
        if j < n - 1:
            dn = card(cells[j + 1][0] - cells[j][0], cells[j + 1][1] - cells[j][1])
        else:
            dn = card(cells[j][0] - cells[j - 1][0], cells[j][1] - cells[j - 1][1])
        dp = OPP[card(cells[j][0] - cells[j - 1][0], cells[j][1] - cells[j - 1][1])] if j > 0 else OPP[dn]
        dirs.append((dp, dn))
    corner_set = set(corners[1:-1])
    for j, (x, z) in enumerate(cells):
        dp, dn = dirs[j]
        rise = j < n - 1 and y[j + 1] > y[j]
        if j in corner_set:
            for a in range(-2, 3):
                for b in range(-2, 3):
                    vp, vn = DV[dp], DV[dn]
                    if a * vp[0] + b * vp[1] == 2 or a * vn[0] + b * vn[1] == 2:
                        continue
                    if a == 0 and b == 0:
                        want(x, z, 3, "rail" if rail else "lane", y[j], dn, False)
                    elif max(abs(a), abs(b)) <= 1:
                        want(x + a, z + b, 2, "lane", y[j], dn, False)
                    else:
                        want(x + a, z + b, 1, "edge", y[j], dn, False)
            continue
        px, pz = -DV[dn][1], DV[dn][0]
        for k in range(-2, 3):
            role = ("rail" if rail else "lane") if k == 0 else ("lane" if abs(k) == 1 else "edge")
            want(x + px * k, z + pz * k, (3 if k == 0 else 2 if abs(k) == 1 else 1), role, y[j], dn, rise)
    for (x, z), (prio, role, yy, d, rise) in roles.items():
        if (x, z) in keep_out:
            continue
        for h in range(0, 4 + (1 if rise else 0)):
            C.clear(x, yy + h, z)
        if role == "edge":
            C.set(x, yy - 1, z, f"stripped_dark_oak_log[axis={log_axis(d)}]")
            C.set(x, yy, z, FENCE)
            if rise:
                C.set(x, yy + 1, z, FENCE)
        elif role == "lane":
            C.set(x, yy - 1, z, deck(x, z) if callable(deck) else deck)
            if rise:
                C.set(x, yy, z, stair("spruce_stairs", d))
        else:
            C.set(x, yy - 1, z, f"stripped_spruce_log[axis={log_axis(d)}]")
        # a ballast embankment where the deck runs too low to walk under
        if embank and yy - 1 <= embank:
            column_down(C, x, yy - 2, z, lambda a, b, c: "gravel" if hash3(a, b, c, 790) < 0.4 else rock(a, b, c))
    if rail:
        for j, (x, z) in enumerate(cells):
            C.set(x, y[j], z, f"rail[shape={rail_shape(cells, y, j)},waterlogged=false]")
    # trestle bents
    for j, (x, z) in enumerate(cells):
        if j % bent_every and j not in corner_set and j != n - 1:
            continue
        if (x, z) in no_bents:
            continue
        dp, dn = dirs[j]
        if j in corner_set:
            feet = [(x + a, z + b) for a in (-2, 2) for b in (-2, 2) if roles.get((x + a, z + b), (0, ""))[1] == "edge"]
            px, pz = 1, 0
        else:
            px, pz = -DV[dn][1], DV[dn][0]
            feet = [(x - 2 * px, z - 2 * pz), (x + 2 * px, z + 2 * pz)]
        bent(C, feet, y[j] - 2, (px, pz), x, z)
    return cells, y


def bent(C, feet, ytop, perp, cx, cz):
    """Posts from ytop down to the first solid block (or a footing 3 under the ground), cross beams every 6 and
    X-bracing between them when there are two posts."""
    bottoms = []
    for (x, z) in feet:
        yb = ytop
        while yb > -3 and (x, yb, z) not in C.keep and not C.solid(x, yb, z):
            C.set(x, yb, z, POST)
            yb -= 1
        bottoms.append(yb)
    if len(feet) != 2 or ytop - max(bottoms) < 5:
        return
    lo = max(bottoms) + 1
    px, pz = perp
    for yy in range(ytop - 1, lo + 2, -1):   # keep 3 clear under the lowest beam (people walk under)
        k = (ytop - 1 - yy) % 6
        if k == 0:
            for t in (-1, 0, 1):
                x, z = cx + px * t, cz + pz * t
                if C.get(x, yy, z) is None:
                    C.set(x, yy, z, f"stripped_spruce_log[axis={'x' if px else 'z'}]")
        else:
            t = (-1, 0, 1, 0, -1)[k - 1] if (yy // 6) % 2 else (1, 0, -1, 0, 1)[k - 1]
            x, z = cx + px * t, cz + pz * t
            if C.get(x, yy, z) is None:
                C.set(x, yy, z, FENCE)


def rail_shape(cells, y, j):
    x, z = cells[j]
    n = len(cells)
    if j < n - 1 and y[j + 1] > y[j]:
        return "ascending_" + card(cells[j + 1][0] - x, cells[j + 1][1] - z)
    if j > 0 and y[j - 1] > y[j]:
        return "ascending_" + card(cells[j - 1][0] - x, cells[j - 1][1] - z)
    ds = []
    if j > 0:
        ds.append(card(cells[j - 1][0] - x, cells[j - 1][1] - z))
    if j < n - 1:
        ds.append(card(cells[j + 1][0] - x, cells[j + 1][1] - z))
    if len(ds) == 1:
        ds.append(OPP[ds[0]])
    s = set(ds)
    if s == {"east", "west"}:
        return "east_west"
    if s == {"north", "south"}:
        return "north_south"
    return ("north" if "north" in s else "south") + "_" + ("east" if "east" in s else "west")


# ------------------------------------------------------------------ cliff stairs between the terraces
def cliff_stair(C, x0, z0, f0, d, n1=7, n2=7, land=3):
    """A masonry stair 3 wide on a terrace against the cliff: n1 steps along d from (x0, z0..z0 + 2), a landing, n2
    steps, then a landing `land` long at the top; a fence balustrade on the outer (south) side, lamps on posts."""
    dx = DV[d][0]
    c1 = flight(C, x0, z0, d, n1, f0, 3, "south", SRSS_ST, support=rock, inner=False)
    xl = x0 + dx * n1
    f1 = f0 + n1
    landing(C, xl, z0, xl + dx * (land - 1), z0 + 2, f1, CRSS, support=rock, inner=False)
    xs = xl + dx * land
    c2 = flight(C, xs, z0, d, n2, f1, 3, "south", SRSS_ST, support=rock, inner=False)
    xt = xs + dx * n2
    f2 = f1 + n2
    landing(C, xt, z0, xt + dx * 2, z0 + 2, f2, CRSS, support=rock, inner=False)
    # balustrade on the outer side
    for (x, y, z) in c1 + c2:
        if z == z0 + 2:
            column_down(C, x, y, z + 1, rock)
            C.set(x, y + 1, z + 1, FENCE)
    for xx in list(range(min(xl, xl + dx * (land - 1)), max(xl, xl + dx * (land - 1)) + 1)) + \
            list(range(min(xt, xt + dx * 2), max(xt, xt + dx * 2) + 1)):
        yy = f1 - 1 if min(xl, xl + dx * (land - 1)) <= xx <= max(xl, xl + dx * (land - 1)) else f2 - 1
        column_down(C, xx, yy, z0 + 3, rock)
        C.set(xx, yy + 1, z0 + 3, FENCE)
    # lamp posts at the foot, on the landing and the top
    for (x, f) in ((x0 - dx, f0), (xl + dx, f1), (xt + dx, f2)):
        C.set(x, f - 1, z0 + 3, CRSS)
        C.set(x, f, z0 + 3, POST)
        C.set(x, f + 1, z0 + 3, LANT)
    return xt + dx * 2, f2


# ------------------------------------------------------------------ false-front buildings
FRONT_VEC = DV


def building(C, x0, z0, x1, z1, f, front, *, h=5, stories=1, kind="dwelling", ff=3, wall=PLANK, loot=None,
             porch=2, spawner=None, seed=0):
    """A western timber building, walls x0..x1, z0..z1, ground floor feet f, ``stories`` of ``h``; a false front on
    the ``front`` face rising ``ff`` above the roof with a sign band and lamps, a door in the middle of the front, a
    porch with posts and an awning, stilts under the walls down to the ground or the rock, a ladder between storeys.
    Cut into the cliff where it meets it (the walls line the cut)."""
    fx, fz = FRONT_VEC[front]
    top = f + stories * h - 1                 # roof deck block
    corners = {(x0, z0), (x0, z1), (x1, z0), (x1, z1)}

    def on_front(x, z):
        return (front == "south" and z == z1) or (front == "north" and z == z0) or \
               (front == "east" and x == x1) or (front == "west" and x == x0)

    # floors, walls, interior air
    for s in range(stories):
        fs = f + s * h
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                if not edge:
                    C.set(x, fs - 1, z, boards(x, z) if s == 0 else PLANK)
                    for y in range(fs, fs + h - 1):
                        C.clear(x, y, z)
                    continue
                C.set(x, fs - 1, z, DPOST.replace("[axis=y]", "[axis=x]") if z in (z0, z1) else
                      DPOST.replace("[axis=y]", "[axis=z]"))
                for y in range(fs, fs + h - 1):
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    span = (x1 - x0) if z in (z0, z1) else (z1 - z0)
                    win = 2 <= u <= span - 2 and u % 3 == 1 and y in (fs + 1, fs + 2)
                    if (x, z) in corners:
                        spec = DPOST
                    elif win:
                        spec = "glass_pane"
                    else:
                        spec = wall
                    C.set(x, y, z, spec)
    # roof deck and parapet-cornice
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, top, z, "spruce_planks" if (x in (x0, x1) or z in (z0, z1)) else "dark_oak_planks")
            C.set(x, top + 1, z, "spruce_slab[type=bottom,waterlogged=false]") if not (
                x in (x0, x1) or z in (z0, z1)) else None
    # eaves: upside-down stairs under the side cornices
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            if on_front(x - fx, z - fz) or (x - fx, z - fz) in corners and on_front(x - fx, z - fz):
                continue
            if C.get(x, top, z) is None:
                C.set(x, top, z, stair("spruce_stairs", card(x0 + x1 - 2 * x, z0 + z1 - 2 * z), "top"))
    # the false front: the front wall rises ff above the roof with a stepped crest and a sign band
    if ff:
        if front in ("south", "north"):
            fline = [(x, z1 if front == "south" else z0) for x in range(x0, x1 + 1)]
        else:
            fline = [(x1 if front == "east" else x0, z) for z in range(z0, z1 + 1)]
        mid = (len(fline) - 1) / 2.0
        for i, (x, z) in enumerate(fline):
            off = abs(i - mid)
            hh = ff + (1 if off <= 1.5 else 0) - (1 if off > mid - 1 else 0)
            for y in range(top + 1, top + 1 + hh):
                band = y == top + 2
                C.set(x, y, z, "dark_oak_planks" if band else wall)
            C.set(x, top + 1 + hh, z, "spruce_slab[type=bottom,waterlogged=false]")
        # sign lamps
        for i in (1, len(fline) - 2):
            x, z = fline[i]
            C.set(x + fx, top + 2, z + fz, "lantern[hanging=false,waterlogged=false]") if C.get(
                x + fx, top + 2, z + fz) is None else None
    # the door in the middle of the front
    if front in ("south", "north"):
        dx_, dz_ = (x0 + x1) // 2, (z1 if front == "south" else z0)
    else:
        dx_, dz_ = (x1 if front == "east" else x0), (z0 + z1) // 2
    C.bp.door(dx_, f, dz_, front, wood="spruce")
    C.keep.add((dx_, f, dz_))
    C.keep.add((dx_, f + 1, dz_))
    # the porch: boardwalk, posts, awning
    if porch:
        lo_u, hi_u = (x0, x1) if front in ("south", "north") else (z0, z1)
        for u in range(lo_u, hi_u + 1):
            for k in range(1, porch + 1):
                x, z = (u, dz_ + fz * k) if front in ("south", "north") else (dx_ + fx * k, u)
                C.set(x, f - 1, z, PLANK)
                for y in range(f, f + 3):
                    C.clear(x, y, z)
                column_down(C, x, f - 2, z, POST if k == porch and (u - lo_u) % 3 == 0 else PLANK, maxd=3)
                # awning posts on the outer row only when a walk row stays free behind them
                if porch >= 2 and k == porch and ((u - lo_u) % 4 == 0 or u == hi_u):
                    for y in range(f, f + 3):
                        C.set(x, y, z, POST)
                C.set(x, f + 3, z, "spruce_slab[type=bottom,waterlogged=false]")
        mx_, mz_ = (dx_ + fx * porch, dz_ + fz * porch)
        C.set(dx_ + fx, f + 2, dz_ + fz, LANT_H) if porch >= 1 else None
        C.set(dx_ + fx, f + 3, dz_ + fz, "spruce_planks")
        _ = (mx_, mz_)
    # stilts under the walls (to the ground or the rock below)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x in (x0, x1) or z in (z0, z1)) and ((x - x0) % 3 == 0 or (z - z0) % 3 == 0 or (x, z) in corners):
                column_down(C, x, f - 2, z, DPOST)
    # ladder between storeys
    for s in range(1, stories):
        fs = f + s * h
        lx, lz = (x0 + 1, z0 + 1) if front != "north" else (x0 + 1, z1 - 1)
        facing = "south" if front != "north" else "north"
        for y in range(fs - h, fs):
            C.set(lx, y, lz, f"ladder[facing={facing},waterlogged=false]")
        C.set(lx, fs - 1, lz, f"ladder[facing={facing},waterlogged=false]")
    furnish(C, kind, x0, z0, x1, z1, f, h, stories, front, loot, spawner, seed)
    return (dx_, dz_)


def furnish(C, kind, x0, z0, x1, z1, f, h, stories, front, loot, spawner, seed):
    """Purpose-based furniture (§8): the back wall carries the counter, shelves or beds; the aisle from the door
    stays clear."""
    bp = C.bp
    ix0, iz0, ix1, iz1 = x0 + 1, z0 + 1, x1 - 1, z1 - 1
    # "back" = the wall opposite the front
    if front == "south":
        back = [(x, iz0) for x in range(ix0 + 1, ix1 + 1)]
        side = [(ix1, z) for z in range(iz0 + 2, iz1)]
        bf = "south"
    elif front == "north":
        back = [(x, iz1) for x in range(ix0 + 1, ix1 + 1)]
        side = [(ix1, z) for z in range(iz0 + 1, iz1 - 1)]
        bf = "north"
    elif front == "east":
        back = [(ix0, z) for z in range(iz0 + 1, iz1 + 1)]
        side = [(x, iz1) for x in range(ix0 + 2, ix1)]
        bf = "east"
    else:
        back = [(ix1, z) for z in range(iz0 + 1, iz1 + 1)]
        side = [(x, iz1) for x in range(ix0 + 1, ix1 - 1)]
        bf = "west"
    cx, cz = (ix0 + ix1) // 2, (iz0 + iz1) // 2
    hang(C, cx, f + h - 2, cz, CHANDELIER if kind in ("saloon", "hotel", "bank") else LANT_H, reach=3)
    if kind == "saloon":
        # the bar: a counter one row in front of the back wall, bottles and pots on shelves behind
        fx, fz = DV[bf]
        for i, (x, z) in enumerate(back[1:-1]):
            bp.set(x + fx, f, z + fz, "spruce_planks" if i % 3 else "barrel[facing=up,open=false]")
            if i % 2 == 0:
                bp.set(x, f + 1, z, "flower_pot")
            bp.set(x, f, z, "barrel[facing=up,open=false]" if i % 3 == 1 else "spruce_planks")
            if i % 4 == 2:
                bp.set(x + fx, f + 1, z + fz, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
        # tables: a fence with a pressure plate, stools of stairs
        for (tx, tz) in side[1:-1:3]:
            ox, oz = (tx - 1, tz) if front in ("south", "north") else (tx, tz - 1)
            bp.set(ox, f, oz, FENCE)
            bp.set(ox, f + 1, oz, "spruce_pressure_plate[powered=false]")
        bp.set(ix0, f, (iz0 + iz1) // 2 if front in ("south", "north") else iz0, "jukebox[has_record=false]")
        bp.set(ix0, f, iz1 if front != "north" else iz0, "note_block[instrument=harp,note=0,powered=false]")
        if loot:
            x, z = back[0]
            bp.chest(x, f, z, bf, loot=LOOT + loot)
    elif kind == "store":
        for i, (x, z) in enumerate(back):
            bp.set(x, f, z, "barrel[facing=up,open=false]" if i % 2 else "chiseled_bookshelf[facing=" + bf +
                   ",slot_0_occupied=false,slot_1_occupied=false,slot_2_occupied=false,slot_3_occupied=false,"
                   "slot_4_occupied=false,slot_5_occupied=false]")
            bp.set(x, f + 1, z, "barrel[facing=up,open=false]" if i % 2 == 0 else "flower_pot")
        for (x, z) in side[::2]:
            bp.barrel(x, f, z)
        if loot:
            bp.chest(side[-1][0], f, side[-1][1], bf, loot=LOOT + loot)
    elif kind in ("dwelling", "bunk", "hotel"):
        beds = back[::2]
        for (x, z) in beds[:4]:
            bp.bed(x, f, z, bf, color="red" if kind != "bunk" else "brown")
        for (x, z) in side[:2]:
            bp.barrel(x, f, z)
        if loot:
            x, z = side[-1]
            bp.chest(x, f, z, bf, loot=LOOT + loot)
        if stories > 1:
            for (x, z) in back[::2][:4]:
                bp.bed(x, f + h, z, bf, color="white")
    elif kind == "smithy":
        bp.set(back[0][0], f, back[0][1], "anvil[facing=north]")
        bp.set(back[1][0], f, back[1][1], f"furnace[facing={OPP[bf]},lit=false]")
        bp.set(back[2][0], f, back[2][1], f"blast_furnace[facing={OPP[bf]},lit=false]")
        bp.set(back[3][0], f, back[3][1], "smithing_table")
        bp.set(side[0][0], f, side[0][1], "grindstone[face=floor,facing=north]")
        bp.set(side[1][0], f, side[1][1], "water_cauldron[level=3]")
        if loot:
            bp.chest(side[-1][0], f, side[-1][1], bf, loot=LOOT + loot)
    elif kind == "bank":
        for (x, z) in back:
            bp.set(x, f, z, "iron_bars")
            bp.set(x, f + 1, z, "iron_bars")
        x, z = back[0]
        bp.set(x, f + 2, z, GAUGE)
        bp.set(side[0][0], f, side[0][1], TABLE)
        bp.set(side[1][0], f, side[1][1], "cartography_table")
        bp.set(side[2][0], f, side[2][1], "lectern[facing=" + bf + ",has_book=false,powered=false]")
        if loot:
            bp.chest(side[-1][0], f, side[-1][1], bf, loot=LOOT + loot)
    elif kind == "jail":
        for (x, z) in back:
            bp.set(x, f, z, "iron_bars")
            bp.set(x, f + 1, z, "iron_bars")
        bp.set(side[0][0], f, side[0][1], TABLE)
        bp.set(side[1][0], f, side[1][1], "barrel[facing=up,open=false]")
        if loot:
            bp.chest(side[-1][0], f, side[-1][1], bf, loot=LOOT + loot)
    elif kind == "livery":
        for i, (x, z) in enumerate(back):
            bp.set(x, f, z, "hay_block[axis=y]" if i % 3 else FENCE)
        for (x, z) in side[::2]:
            bp.set(x, f, z, "hay_block[axis=y]")
        if loot:
            bp.barrel(side[-1][0], f, side[-1][1], loot=LOOT + loot)
    elif kind == "office":
        bp.set(back[1][0], f, back[1][1], TABLE)
        bp.set(back[2][0], f, back[2][1], "lectern[facing=" + OPP[bf] + ",has_book=false,powered=false]")
        bp.set(back[0][0], f, back[0][1], "cartography_table")
        if loot:
            bp.chest(side[-1][0], f, side[-1][1], bf, loot=LOOT + loot)
    if spawner:
        bp.spawner(cx, f + (h if stories > 1 else 0), cz, spawner)


# ------------------------------------------------------------------ the town at the foot
def street_mat(x, z):
    h = hash01(x, z, 741)
    return "coarse_dirt" if h < 0.35 else ("dirt_path" if h < 0.6 else "packed_mud" if h < 0.8 else "red_sand")


def ground(C, x0, z0, x1, z1, mat):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if C.get(x, 0, z) is not None and C.get(x, 1, z) is not None:
                continue
            C.set(x, 0, z, mat(x, z) if callable(mat) else mat)
            C.set(x, -1, z, "dirt" if hash01(x, z, 742) < 0.6 else "terracotta")


def town(C):
    # Main Street, boardwalks, the square in front of the butte
    ground(C, -24, 27, 26, 45, lambda x, z: "packed_mud" if (x + z) % 5 else "mud_bricks")
    ground(C, -4, 46, 4, 126, street_mat)
    for s in (-1, 1):
        for z in range(46, 98):
            for x in (s * 5, s * 6):
                C.set(x, 0, z, PLANK)
                C.set(x, -1, z, "dirt")
    # west side: saloon, store, livery; east side: hotel, bank and assay office, sheriff
    building(C, -17, 48, -7, 60, 1, "east", stories=2, kind="saloon", loot="mm_saloon", spawner=MOB_BANDIT, porch=1)
    building(C, -16, 64, -7, 73, 1, "east", kind="store", loot="mm_town", porch=1)
    building(C, -18, 77, -7, 88, 1, "east", h=6, kind="livery", loot="mm_town", porch=1, ff=2)
    building(C, 7, 48, 17, 59, 1, "west", stories=2, kind="hotel", loot="mm_town", porch=1)
    building(C, 7, 63, 15, 72, 1, "west", kind="bank", loot="mm_town", porch=1, wall="birch_planks")
    building(C, 7, 76, 15, 85, 1, "west", kind="jail", porch=1)
    # lamp posts along the street
    for z in range(50, 98, 8):
        for s in (-1, 1):
            C.set(s * 4, 1, z, POST)
            C.set(s * 4, 2, z, POST)
            C.set(s * 4, 3, z, LANT)
    # hitching rails and troughs
    for (x, z) in ((-4, 62), (4, 74), (-4, 90)):
        C.set(x, 1, z, FENCE)
        C.set(x, 1, z + 1, FENCE)
        C.set(x, 1, z + 2, "water_cauldron[level=3]")
    # the well in the square
    for x in range(-18, -13):
        for z in range(36, 41):
            edge = x in (-18, -14) or z in (36, 40)
            C.set(x, 0, z, "cobblestone")
            if edge:
                C.set(x, 1, z, "cobblestone_wall[east=none,north=none,south=none,up=true,west=none,waterlogged=false]")
            else:
                C.water(x, 0, z)
                C.water(x, -1, z)
                C.set(x, -2, z, "cobblestone")
    for (x, z) in ((-18, 36), (-14, 36), (-18, 40), (-14, 40)):
        for y in range(2, 5):
            C.set(x, y, z, POST)
    for x in range(-19, -12):
        for z in range(35, 42):
            if abs(x + 16) + abs(z - 38) <= 5:
                C.set(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
    C.set(-16, 4, 38, LANT_H)
    # the water tower
    for (x, z) in ((20, 39), (25, 39), (20, 44), (25, 44)):
        for y in range(1, 9):
            C.set(x, y, z, POST)
    for x in range(19, 27):
        for z in range(38, 46):
            d = math.hypot(x - 22.5, z - 41.5)
            for y in range(9, 15):
                if d <= 3.6:
                    if y == 9:
                        C.set(x, y, z, PLANK)
                    elif d > 2.7:
                        C.set(x, y, z, "stripped_spruce_log[axis=y]" if y not in (10, 13) else IRON)
                    elif y == 14:
                        C.set(x, y, z, PLANK)
                    else:
                        C.water(x, y, z)
            if d <= 3.0:
                C.set(x, 15, z, "spruce_slab[type=bottom,waterlogged=false]")
    C.set(22, 16, 41, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the gate arch at the street's south end (frames the headframe from the road)
    for s in (-1, 1):
        for x in (s * 6, s * 7):
            for z in (103, 104):
                for y in range(1, 11):
                    C.set(x, y, z, DPOST)
                C.set(x, 0, z, "cobblestone")
    for x in range(-8, 9):
        for z in (103, 104):
            C.set(x, 10, z, "stripped_dark_oak_log[axis=x]")
            C.set(x, 11, z, "spruce_slab[type=bottom,waterlogged=false]")
        if abs(x) <= 4:
            C.set(x, 9, 104, DPLANK)
            C.set(x, 8, 104, DPLANK if abs(x) < 4 else "air")
    for x in (-3, 3):
        C.set(x, 7, 104, LANT_H)
        C.set(x, 8, 104, CHAIN) if C.get(x, 8, 104) != "minecraft:dark_oak_planks" else None


def camp(C):
    """The stagecoach stop beside the road: a covered wagon, a tent, a fire and the entrance waystone."""
    ground(C, 6, 106, 22, 124, lambda x, z: "coarse_dirt" if hash01(x, z, 743) < 0.5 else "red_sand")
    # the wagon (x 12..15, z 110..116): bed, wheels, canvas hoops
    for z in range(110, 117):
        for x in range(12, 16):
            C.set(x, 2, z, PLANK)
        for x in (12, 15):
            C.set(x, 3, z, "spruce_fence[east=false,north=true,south=true,west=false,waterlogged=false]")
            C.set(x, 4, z, "white_wool")
        for x in (13, 14):
            C.set(x, 5, z, "white_wool")
    for (x, z) in ((11, 111), (16, 111), (11, 115), (16, 115)):
        C.set(x, 1, z, "stripped_dark_oak_log[axis=x]")
        C.set(x, 2, z, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for z in (110, 116):
        for x in range(12, 16):
            C.set(x, 1, z, AIR) if C.get(x, 1, z) is None else None
    C.set(13, 3, 113, "barrel[facing=up,open=false]")
    C.bp.chest(14, 3, 112, "west", loot=LOOT + "mm_camp")
    for x in (13, 14):                        # the tailboard step
        C.set(x, 1, 109, stair("spruce_stairs", "south"))
    # tent
    for z in range(118, 123):
        C.set(18, 1, z, FENCE)
        C.set(22, 1, z, FENCE)
        C.set(18, 2, z, "brown_wool")
        C.set(22, 2, z, "brown_wool")
        for x in (19, 20, 21):
            C.set(x, 3 if x != 20 else 4, z, "white_wool" if z % 2 else "brown_wool")
        C.set(19, 3, z, "brown_wool")
        C.set(21, 3, z, "brown_wool")
    C.bp.bed(20, 1, 119, "south", color="brown")
    C.set(10, 1, 120, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, fc) in ((9, 120, "east"), (11, 120, "west"), (10, 121, "north")):
        C.set(x, 1, z, stair("spruce_stairs", fc))
    C.bp.barrel(8, 1, 123)
    # the entrance waystone beside the road
    C.set(6, 0, 112, "cobblestone")
    C.set(6, 1, 112, MOD["waystone"])


def outskirts(C):
    """Tailings heap (west), Boot Hill (east), a wind pump and a corral: satellites on the approach (§15.9)."""
    cx, cz = -60, 44
    for x in range(cx - 16, cx + 17):
        for z in range(cz - 12, cz + 13):
            d = math.hypot((x - cx) / 1.3, z - cz)
            if d > 12:
                continue
            t = int(7 * (1 - (d / 12) ** 1.5) + (hash01(x, z, 744) - 0.5) * 1.5)
            for y in range(-1, t + 1):
                h = hash3(x, y, z, 745)
                C.set(x, y, z, "gravel" if h < 0.35 else "coarse_dirt" if h < 0.6 else "terracotta" if h < 0.8 else
                      "red_sand")
    # a chute from the heap's top (an old ore cart on a stub of rail)
    for x in range(cx + 10, cx + 19):
        C.set(x, 0, cz, "stripped_spruce_log[axis=x]")
        C.set(x, 1, cz, "rail[shape=east_west,waterlogged=false]")
    # Boot Hill
    bx, bz = 62, 40
    for x in range(bx - 7, bx + 8):
        for z in range(bz - 5, bz + 6):
            C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 746) < 0.5 else "red_sand")
            if x in (bx - 7, bx + 7) or z in (bz - 5, bz + 5):
                if not (z == bz + 5 and abs(x - bx) <= 1):
                    C.set(x, 1, z, FENCE)
    for i, (x, z) in enumerate((x, z) for x in range(bx - 5, bx + 6, 3) for z in (bz - 3, bz, bz + 3)):
        C.set(x, 0, z, "coarse_dirt")
        C.set(x, 1, z, "spruce_fence[east=false,north=false,south=false,west=false,waterlogged=false]")
        C.set(x, 2, z, "spruce_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    for y in range(1, 6):
        C.set(bx + 5, y, bz - 4, "stripped_dark_oak_log[axis=y]")
    C.set(bx + 6, 5, bz - 4, "stripped_dark_oak_log[axis=x]")
    C.set(bx + 4, 4, bz - 4, "stripped_dark_oak_log[axis=x]")
    # wind pump beside the livery
    px, pz = -28, 82
    for y in range(1, 13):
        for (x, z) in ((px - 1, pz - 1), (px + 1, pz - 1), (px - 1, pz + 1), (px + 1, pz + 1)):
            if y % 4 == 0 or (x == px - 1 and z == pz - 1):
                C.set(x, y, z, POST)
        if y % 4 == 0:
            for (x, z) in ((px, pz - 1), (px, pz + 1), (px - 1, pz), (px + 1, pz)):
                C.set(x, y, z, "stripped_spruce_log[axis=x]" if z == pz else "stripped_spruce_log[axis=z]")
    for (x, z) in ((px + 1, pz - 1), (px - 1, pz + 1), (px + 1, pz + 1)):
        for y in range(1, 13):
            C.set(x, y, z, POST)
    C.set(px, 13, pz, IRON)
    for k in range(-3, 4):
        C.set(px + k, 14, pz + 2, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
        C.set(px, 14 + k, pz + 2, "spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    C.set(px, 14, pz + 2, BRASS)
    C.set(px, 14, pz + 1, IRON)
    for x in range(px - 2, px + 3):
        for z in range(pz + 3, pz + 6):
            C.set(x, 0, z, "cobblestone")
            C.water(x, 1, z) if (abs(x - px) < 2 and z == pz + 4) else C.set(x, 1, z, "cobblestone")
    # corral
    for x in range(-36, -21):
        for z in range(90, 100):
            if x in (-36, -22) or z in (90, 99):
                if not (x == -22 and z in (94, 95)):
                    C.set(x, 1, z, FENCE)
            C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 747) < 0.6 else "dirt_path")
    C.set(-30, 1, 94, "hay_block[axis=y]")
    C.set(-29, 1, 94, "hay_block[axis=y]")
    C.set(-30, 2, 94, "hay_block[axis=y]")


def grand_stair(C):
    """From the square up the talus to T1: two flights of 7 with a landing, the last steps cut into the rim."""
    flight(C, -8, 40, "north", 7, 1, 3, "east", RSS_ST, support=masonry, inner=False)
    landing(C, -8, 31, -6, 33, 8, CRSS, support=masonry, inner=False)
    flight(C, -8, 30, "north", 7, 8, 3, "east", RSS_ST, support=masonry, inner=False)
    landing(C, -8, 22, -6, 23, F1, PLANK, inner=False)
    for z in range(24, 41):
        for x in (-9, -5):
            top = 1 + max(0, min(7, 41 - z)) if z >= 33 else (8 if z >= 31 else 8 + min(7, 31 - z))
            if z <= 26:
                continue
            column_down(C, x, top - 1, z, masonry)
            C.set(x, top, z, FENCE)
    for (x, z, f) in ((-9, 41, 1), (-5, 41, 1), (-9, 32, 8), (-5, 32, 8)):
        C.set(x, f, z, POST)
        C.set(x, f + 1, z, POST)
        C.set(x, f + 2, z, LANT)


def terrace_walks(C):
    """Boardwalks along the main path on the terraces (a lighter, cleaner floor marks the way, §10.10)."""
    for (x0, z0, x1, z1, y) in ((-12, 23, 1, 25, 14), (19, 17, 24, 19, 28), (0, 11, 4, 13, 42)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                above = C.get(x, y + 1, z)
                if C.get(x, y, z) is not None and above in (None, AIR, "minecraft:dead_bush",
                                                            "minecraft:short_dry_grass"):
                    C.set(x, y, z, boards(x, z))
                    C.clear(x, y + 1, z)


def ladder_up(C, x, z, y_lo, y_hi, facing):
    """A ladder on a cliff: cells (x, y_lo..y_hi, z) facing `facing` (it hangs on the block behind it, which is made
    solid where the cliff is ragged)."""
    bx, bz = x - DV[facing][0], z - DV[facing][1]
    for y in range(y_lo, y_hi + 1):
        if not C.solid(bx, y, bz):
            C.set(bx, y, bz, rock(bx, y, bz))
        C.set(x, y, z, f"ladder[facing={facing},waterlogged=false]")
        for k in (1, 2):
            if C.solid(x + DV[facing][0] * k, y, z + DV[facing][1] * k) and k == 1:
                C.clear(x + DV[facing][0], y, z + DV[facing][1])


def terraces(C):
    terrace_walks(C)
    # T1: the Rusty Spur (two storeys, back room cut into the rock) and, east of the cleft, the smithy
    building(C, -33, 11, -15, 22, F1, "south", stories=2, kind="saloon", loot="mm_saloon", spawner=MOB_BANDIT,
             porch=1)
    building(C, 36, 1, 44, 9, F1, "south", kind="smithy", loot="mm_dwelling", porch=1)
    # T2: the bunkhouse and the Copper Kettle; the lookout shack on the east shoulder
    building(C, -31, 4, -17, 15, F2, "south", kind="bunk", loot="mm_dwelling", porch=1, ff=2)
    building(C, -13, 9, -1, 18, F2, "south", kind="saloon", loot="mm_saloon", porch=1)
    building(C, 35, -7, 40, 0, F2, "south", kind="dwelling", loot="mm_terrace", porch=1, ff=0)
    # a boardwalk along the T2 lip from the cliff stair's landing west past the saloon to the bunkhouse
    for x in range(-32, 2):
        for z in (19, 20):
            if C.get(x, F2 - 1, z) is None or not C.solid(x, F2 - 1, z):
                C.set(x, F2 - 1, z, boards(x, z))
                if x % 3 == 0:
                    column_down(C, x, F2 - 2, z, POST, maxd=16)
            if z == 20 and not C.solid(x, F2 - 1, z + 1):
                C.set(x, F2, z, FENCE) if x % 5 == 0 else None
    # T3: the telegraph office
    building(C, -23, 3, -15, 11, F3, "south", kind="office", loot="mm_terrace", porch=1, ff=2)
    # the main stairs up the face
    cliff_stair(C, 2, 20, F1, "east")
    landing(C, 19, 17, 23, 19, F2, PLANK, support=rock, inner=False)
    cliff_stair(C, 21, 14, F2, "west")
    cliff_stair(C, 5, 8, F3, "east")
    track(C, [(23, 7), (23, -1)], [FP], rail=False, bent_every=3)
    # the cleft bridges (T1 and T2) and the ladders (east shoulder T1 <-> T2, west T2 <-> T3)
    track(C, [(24, 18), (33, 18), (33, 12), (39, 12)], [F1], rail=False, bent_every=3,
          keep_out={(x, 10) for x in range(34, 46)})
    track(C, [(22, 11), (33, 11), (33, 2), (37, 2)], [F2], rail=False, bent_every=3,
          keep_out={(x, z) for x in range(34, 42) for z in (0, 1)})
    for (x, zg, ylo, yhi, fc) in ((41, -12, F1, F2 - 1, "east"), (-15, 13, F2, F3 - 1, "south")):
        ladder_up(C, x, zg, ylo, yhi, fc)


# ------------------------------------------------------------------ the railway
RAIL_PTS = [(8, 31), (50, 31), (50, -63), (-37, -63), (-37, 10), (-14, 10), (-14, 0)]
RAIL_YS = [1, 6, 22, 36, 50, 55, 57]
ADIT_YARD = {(x, z) for x in range(44, 62) for z in range(-31, -22)}


def railway(C):
    cells, ys = track(C, RAIL_PTS, RAIL_YS, rail=True, windows={0: (15, 38), 5: (2, 4)}, keep_out=(),
                      bent_every=6, no_bents=ADIT_YARD, embank=3)
    # the station platform south of the line (open to the track), a shed roof on posts, the ticket window
    for x in range(6, 24):
        for z in range(33, 38):
            C.set(x, 0, z, PLANK if z > 33 else "stripped_dark_oak_log[axis=x]")
            C.clear(x, 1, z)
            if z == 33 and 9 <= x <= 21:
                C.clear(x, 1, z)
    for x in range(8, 22):
        for z in range(34, 38):
            C.set(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]")
        if x % 4 == 0:
            for y in range(1, 5):
                C.set(x, y, 37, POST)
    for x in range(8, 22, 4):
        C.set(x + 2, 4, 36, LANT_H)
    for y in range(1, 5):
        for x in (22, 23):
            C.set(x, y, 37, PLANK)
    C.bp.barrel(21, 1, 36)
    C.bp.barrel(20, 1, 36)
    C.set(7, 1, 31, IRON)                     # buffer stop behind the first rail
    C.set(7, 2, 31, "stripped_dark_oak_log[axis=x]")
    # the terminus on the summit: a buffer and the ore tipple over the mill roof
    C.set(-14, FP, -1, IRON)
    C.set(-14, FP + 1, -1, "stripped_dark_oak_log[axis=z]")
    for x in range(-21, -16):
        for z in range(-6, 1):
            edge = x in (-21, -17) or z in (-6, 0)
            C.set(x, FP - 1, z, PLANK)
            if edge and (x, z) in ((-21, -6), (-17, -6), (-21, 0), (-17, 0)):
                for y in range(FP, FP + 6):
                    C.set(x, y, z, POST)
            C.set(x, FP + 5, z, PLANK if not edge else "stripped_spruce_log[axis=x]")
    for (x, z) in ((-19, -4), (-19, -2)):
        C.set(x, FP + 4, z, "hopper[enabled=true,facing=down]")
        C.set(x, FP + 3, z, "hopper[enabled=true,facing=down]")
    for (x, z, b) in ((-20, -5, "raw_iron_block"), (-18, -1, "raw_copper_block"), (-20, -1, "raw_copper_block"),
                      (-18, -5, "coarse_dirt")):
        C.set(x, FP, z, b)
    return cells, ys


# ------------------------------------------------------------------ the headframe, the wheel, the hoist house
def line3(a, b, steps=None):
    (x0, y0, z0), (x1, y1, z1) = a, b
    n = steps or int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 2) + 1
    out = []
    for i in range(n + 1):
        t = i / n
        p = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if not out or out[-1] != p:
            out.append(p)
    return out


def headframe(C):
    base = [(5, -26), (16, -26), (5, -16), (16, -16)]
    top = [(8, -23), (13, -23), (8, -19), (13, -19)]
    y0, y1 = FP, 88
    for (bx, bz), (tx, tz) in zip(base, top):
        ox = 1 if bx < 10 else -1
        oz = 1 if bz < -21 else -1
        for (x, y, z) in line3((bx, y0, bz), (tx, y1, tz)):
            for (ax, az) in ((0, 0), (ox, 0), (0, oz), (ox, oz)):
                C.set(x + ax, y, z + az, IRON if (y - y0) % 8 == 0 else "dark_oak_log[axis=y]")
        for dx in range(-1, 3):
            for dz in range(-1, 3):
                C.set(bx + (dx if ox > 0 else -dx), y0 - 1, bz + (dz if oz > 0 else -dz), CRSS)
    # girts and X-bracing on the four faces
    levels = list(range(y0 + 7, y1, 7)) + [y1]

    def corner_at(i, y):
        (bx, bz), (tx, tz) = base[i], top[i]
        t = (y - y0) / (y1 - y0)
        return round(bx + (tx - bx) * t), round(bz + (tz - bz) * t)

    faces = ((0, 1), (2, 3), (0, 2), (1, 3))
    prev = y0
    for y in levels:
        for (i, j) in faces:
            a, b = corner_at(i, y), corner_at(j, y)
            ax = "x" if a[1] == b[1] else "z"
            for (x, yy, z) in line3((a[0], y, a[1]), (b[0], y, b[1])):
                C.set(x, yy, z, f"stripped_dark_oak_log[axis={ax}]")
            # X brace between this girt and the previous one
            a0, b0 = corner_at(i, prev), corner_at(j, prev)
            for (p, q) in (((a0[0], prev, a0[1]), (b[0], y, b[1])), ((b0[0], prev, b0[1]), (a[0], y, a[1]))):
                for (x, yy, z) in line3(p, q):
                    if C.get(x, yy, z) is None:
                        C.set(x, yy, z, IRON_WALL)
        prev = y
    # the sheave deck
    for x in range(6, 16):
        for z in range(-25, -16):
            edge = x in (6, 15) or z in (-25, -17)
            C.set(x, y1, z, IRON if edge else PLANK)
            if edge:
                railing(C, x, y1 + 1, z, card(x - 10.5, z + 21))
    # A-frame pedestals carrying the axle
    for z in (-24, -18):
        for (x, y, zz) in line3((7, y1 + 1, z), (10, 97, z)) + line3((14, y1 + 1, z), (11, 97, z)):
            C.set(x, y, zz, IRON)
    cx, cy, cz = WHEEL
    for z in range(-24, -17):
        C.set(10, cy, z, IRON)
        C.set(11, cy, z, IRON)
    # the wheel: two rims, a rope groove, ten spokes a side, a brass hub
    for x in range(int(cx - 10), int(cx + 11)):
        for y in range(cy - 10, cy + 11):
            d = math.hypot(x - cx, y - cy)
            if 8.2 <= d <= 9.4:
                C.set(x, y, -22, BRASS if int((math.atan2(y - cy, x - cx) + math.pi) * 6) % 5 else GEAR)
                C.set(x, y, -20, BRASS if int((math.atan2(y - cy, x - cx) + math.pi) * 6) % 5 else GEAR)
                if d >= 8.7:
                    C.set(x, y, -21, IRON)
            elif d <= 1.7:
                for z in (-23, -22, -21, -20, -19):
                    C.set(x, y, z, BRASS if z in (-22, -20) else COPPER)
    for k in range(10):
        a = k * math.pi / 5 + 0.15
        for i in range(4, 28):
            t = i * 0.3
            x, y = round(cx + t * math.cos(a)), round(cy + t * math.sin(a))
            for z in (-22, -20):
                if C.get(x, y, z) is None:
                    C.set(x, y, z, IRON)
    # the hoisting rope down into the collar, a cage hung above the drop, the drum rope to the hoist house
    for y in range(66, 98):
        C.set(1, y, -21, CHAIN)
    for y in range(62, 66):
        for x in range(0, 3):
            for z in range(-22, -19):
                edge = x in (0, 2) or z in (-22, -20)
                if y in (62, 65):
                    C.set(x, y, z, IRON)
                elif edge:
                    C.set(x, y, z, "iron_bars")
    for (x, y, z) in line3((19, 99, -21), (19, 62, -12)):
        C.set(x, y, z, CHAIN)
    # backstays from the tower top down to pads east of it
    for (zt, zb) in ((-23, -27), (-19, -15)):
        for (x, y, z) in line3((13, 86, zt), (24, FP, zb)):
            C.set(x, y, z, "dark_oak_log[axis=y]")
            C.set(x, y, z + (1 if zb > -21 else -1), "dark_oak_log[axis=y]")
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                C.set(24 + dx, FP - 1, zb + dz, CRSS)
    # the collar: a timber ring and a railing with a gap beside the ladder
    x0, z0, x1, z1 = SHAFT
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            C.set(x, FP - 1, z, f"stripped_dark_oak_log[axis={'x' if z in (z0 - 1, z1 + 1) else 'z'}]")
            if (x, z) != (x0 - 1, -21):
                C.set(x, FP, z, FENCE)
    # a hand bell on the headframe for the shift change
    C.set(5, FP + 7, -26, BRASS)


def hoist_house(C):
    x0, z0, x1, z1 = 12, -14, 22, -5
    f = FP
    building(C, x0, z0, x1, z1, f, "south", h=7, kind="none", ff=0, porch=2, wall="spruce_planks")
    # brick footing course and a clerestory monitor on the roof
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                C.set(x, f, z, "bricks") if C.get(x, f, z) not in ("minecraft:spruce_door",) and \
                    (x, f, z) not in C.keep else None
    for x in range(x0 + 2, x1 - 1):
        for z in range(z0 + 2, z1 - 1):
            edge = x in (x0 + 2, x1 - 2) or z in (z0 + 2, z1 - 2)
            for y in (f + 7, f + 8):
                if edge:
                    C.set(x, y, z, "glass_pane" if (y == f + 7 and (x + z) % 2) else PLANK)
            C.set(x, f + 9, z, "spruce_slab[type=bottom,waterlogged=false]")
    # chimney
    for y in range(f, f + 15):
        for (x, z) in ((x1 - 1, z1 - 2), (x1 - 2, z1 - 2), (x1 - 1, z1 - 3), (x1 - 2, z1 - 3)):
            if y >= f + 6 or (x, y, z) not in C.keep:
                C.set(x, y, z, "bricks" if y % 5 else BRASS)
    C.set(x1 - 1, f + 15, z1 - 2, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    C.set(x1 - 1, f + 14, z1 - 2, "hay_block[axis=y]")
    # the winding drum (axis x) on iron bearers, its brake and the drive from the engine
    for x in range(17, 22):
        for y in range(57, 62):
            for z in range(-13, -8):
                d = math.hypot(y - 59, z + 11)
                if d <= 1.6:
                    C.set(x, y, z, BRASS if x in (17, 21) else ("dark_oak_log[axis=x]" if d > 0.5 else IRON))
    for x in (17, 21):
        C.set(x, 57, -11, IRON)
    for x in range(17, 22):
        C.set(x, 61, -11, CHAIN.replace("axis=y", "axis=x"))
    # the vertical boiler, pipes, gauges, the driver's levers
    for y in range(57, 61):
        for x in range(19, 22):
            for z in range(-9, -6):
                if abs(x - 20) + abs(z + 8) <= 1:
                    C.set(x, y, z, COPPER if y < 60 else BRASS)
    for y in range(57, 62):
        C.set(21, y, -10, PIPES)
    C.set(19, 58, -10, GAUGE)
    C.set(13, 58, z0, EDISON)
    C.set(21, 59, z0, EDISON)
    C.set(16, 57, -12, TABLE)
    # the stair hole (SW1 lane A) with a railing round it
    for z in range(-10, -6):
        railing(C, 16, f, z, "east")
    for x in range(13, 16):
        railing(C, x, f, -6, "south")
    # the hub's site of grace, a chest, a barrel
    C.set(17, f, -13, MOD["waystone"])
    C.bp.chest(21, f, -6, "west", loot=LOOT + "mm_hoist")
    C.bp.barrel(20, f, -6)


def summit(C):
    """Shacks and props on the summit: the assay lab, a flagpole, a powder-keg pile, lamp posts on the walk."""
    building(C, -4, -6, 4, 0, FP, "south", kind="office", loot="mm_terrace", porch=1, ff=2, wall="birch_planks")
    for y in range(FP, FP + 14):
        C.set(-8, y, 2, IRON_WALL if y > FP else IRON)
    for y in range(FP + 10, FP + 14):
        C.set(-7, y, 2, "red_wool" if y % 2 else "white_wool")
    for (x, z) in ((20, -2), (8, 2), (-2, 4), (-12, 3), (6, -12)):
        C.set(x, FP, z, POST)
        C.set(x, FP + 1, z, POST)
        C.set(x, FP + 2, z, LANT)


# ------------------------------------------------------------------ inside the butte: the mine
def timber_sets(C, x0, z0, x1, z1, f, h, axis, every=4, lamp_every=8):
    """Mine supports in the wall planes: posts in both side walls and a cap beam in the ceiling every ``every`` along
    the gallery's axis; a lamp set into the wall every ``lamp_every``."""
    if axis == "x":
        for x in range(x0, x1 + 1):
            if (x - x0) % every:
                continue
            for y in range(f, f + h):
                C.put(x, y, z0 - 1, POST)
                C.put(x, y, z1 + 1, POST)
            for z in range(z0 - 1, z1 + 2):
                C.put(x, f + h, z, "stripped_spruce_log[axis=z]")
            if (x - x0) % lamp_every == 0:
                C.put(x + 1, f + 2, z0 - 1, EDISON)
    else:
        for z in range(z0, z1 + 1):
            if (z - z0) % every:
                continue
            for y in range(f, f + h):
                C.put(x0 - 1, y, z, POST)
                C.put(x1 + 1, y, z, POST)
            for x in range(x0 - 1, x1 + 2):
                C.put(x, f + h, z, "stripped_spruce_log[axis=x]")
            if (z - z0) % lamp_every == 0:
                C.put(x0 - 1, f + 2, z + 1, EDISON)


def gallery(C, x0, z0, x1, z1, f, h=4, floor=mine_floor, rails=None, every=4):
    mroom(C, x0, z0, x1, z1, f, h, floor)
    axis = "x" if (x1 - x0) >= (z1 - z0) else "z"
    timber_sets(C, x0, z0, x1, z1, f, h, axis, every)
    if rails is not None:
        if axis == "x":
            for x in range(x0, x1 + 1):
                C.set(x, f - 1, rails, "stripped_spruce_log[axis=x]")
                C.set(x, f, rails, "rail[shape=east_west,waterlogged=false]")
        else:
            for z in range(z0, z1 + 1):
                C.set(rails, f - 1, z, "stripped_spruce_log[axis=z]")
                C.set(rails, f, z, "rail[shape=north_south,waterlogged=false]")


def sw1(C):
    """Under the hoist house: a stairwell down 14 (two flights and a landing) and a corridor west to the mill."""
    flight(C, 13, -5, "north", 7, 50, 3, "east", "spruce_stairs")
    landing(C, 13, -4, 18, -2, 50, PLANK)
    flight(C, 16, -11, "south", 7, 43, 3, "east", "spruce_stairs")
    landing(C, 16, -14, 18, -12, FM_TOP, PLANK)
    for x in (12, 19):
        for z in range(-14, -1):
            for y in range(43, 56):
                C.put(x, y, z, PLANK if y % 4 else POST)
    C.set(19, 46, -8, EDISON)
    C.set(12, 53, -3, EDISON)
    # the corridor at feet 43 west to the mill's top floor (compression before the hall)
    gallery(C, -3, -14, 15, -12, FM_TOP, h=4, floor=boards)


def gear(C, plane, cx, cy, cz, r, teeth=None, rim=BRASS, web=GEAR, hub=COPPER, phase=0.0):
    """A vertical gear in the x-y plane (plane='z', at z = cz) or the z-y plane (plane='x', at x = cx)."""
    teeth = teeth or max(8, int(r * 1.6))
    ri = int(r) + 2
    for u in range(-ri, ri + 1):
        for v in range(-ri, ri + 1):
            d = math.hypot(u, v)
            a = math.atan2(v, u) + phase
            tooth = (int((a + math.pi) / (2 * math.pi) * teeth * 2) % 2) == 0
            spec = None
            if d <= 1.5:
                spec = hub
            elif d <= r - 1.2:
                spoke = abs(math.sin((a) * 3)) < 0.22
                spec = IRON if spoke else (web if d > r * 0.55 else None)
                if d <= 2.6:
                    spec = BRASS
            elif d <= r + 0.2:
                spec = rim
            elif d <= r + 1.2 and tooth:
                spec = IRON
            if spec is None:
                continue
            if plane == "z":
                C.set(cx + u, cy + v, cz, spec)
            else:
                C.set(cx, cy + v, cz + u, spec)


def mill(C):
    """The stamp mill: three stepped floors under a hall 24 high, the stamp battery on its camshaft, two giant gears
    on the west wall, the flywheel on the north wall, amalgamation tables on the lowest floor."""
    x0, z0, x1, z1 = MILL
    top_air = 52
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            if edge:
                continue
            if z >= -16:
                f = FM_TOP
            elif z >= -23:
                f = FM_STAMP
            else:
                f = FM_PLATE
            C.set(x, f - 1, z, boards(x, z) if f != FM_PLATE else ("cut_copper" if (x + z) % 5 == 0 else PLANK))
            for y in range(f, top_air + 1):
                C.clear(x, y, z, inner=True)
    # retaining walls of timber under the upper floors' edges, railings along them
    for x in range(x0, x1 + 1):
        for y in range(FM_STAMP, FM_TOP - 1):
            C.put(x, y, -16, PLANK if (x - x0) % 4 else POST)
        for y in range(FM_PLATE, FM_STAMP - 1):
            C.put(x, y, -23, PLANK if (x - x0) % 4 else POST)
        if x < x1 - 3:
            railing(C, x, FM_TOP, -16, "north")
        if x > x0 + 3:
            railing(C, x, FM_STAMP, -23, "north")
    # roof trusses across the hall, lamps on chains
    for z in range(z0, z1 + 1, 5):
        for x in range(x0, x1 + 1):
            C.set(x, top_air + 1, z, "stripped_dark_oak_log[axis=x]")
        for x in (x0, x1):
            for y in range(top_air - 3, top_air + 1):
                C.set(x, y, z, "stripped_dark_oak_log[axis=y]") if y == top_air else None
    for (x, z) in ((-17, -13), (-8, -13), (-13, -27), (-6, -27), (-17, -20)):
        hang(C, x, 47 if z > -24 else 44, z, CHANDELIER)
    # the flights between the floors
    for (fx0, fz0, ff0) in ((-6, -23, FM_STAMP), (-21, -30, FM_PLATE)):
        for (x, y, z) in flight(C, fx0, fz0, "south", 7, ff0, 3, "east", "spruce_stairs"):
            for yy in range(y - 1, ff0 - 1, -1):
                C.set(x, yy, z, PLANK if (x + yy) % 4 else DPLANK)
    for x in range(-6, -3):
        C.put(x, FM_TOP, -16, AIR) if C.get(x, FM_TOP, -16) and "railing" in C.get(x, FM_TOP, -16) else None
    for x in range(-21, -18):
        C.put(x, FM_STAMP, -23, AIR) if C.get(x, FM_STAMP, -23) and "railing" in C.get(x, FM_STAMP, -23) else None
    # the stamp battery: ten stamps in two mortar boxes, a camshaft (axis x) at y 47 on two timber frames
    sz = -20
    for x in range(-18, -6):
        C.set(x, FM_STAMP, sz, IRON)
        C.set(x, FM_STAMP, sz - 1, IRON if x in (-18, -7, -12) else "cauldron")
        C.set(x, FM_STAMP + 1, sz, IRON_WALL if x in (-18, -12, -7) else "iron_bars")
    for x in list(range(-17, -12)) + list(range(-11, -6)):
        for y in range(FM_STAMP + 2, 46):
            C.set(x, y, sz, CHAIN if y < 44 else "iron_block" if y == 44 else CHAIN)
        C.set(x, FM_STAMP + 1, sz, "anvil[facing=east]")
    for x in range(-19, -6):
        C.set(x, 47, sz, "stripped_dark_oak_log[axis=x]")
        if x % 2 == 0:
            C.set(x, 47, sz - 1, IRON)
    for x in (-19, -12, -7):
        for y in range(FM_STAMP, 51):
            C.set(x, y, sz + 1, "dark_oak_log[axis=y]")
        C.set(x, 50, sz, "dark_oak_log[axis=y]")
    for x in range(-19, -6):
        C.set(x, 51, sz + 1, "stripped_dark_oak_log[axis=x]")
    # ore bins on the top floor feeding the stamps (chutes over the mortars)
    for x in range(-19, -7):
        for z in (-15, -14):
            C.set(x, FM_TOP, z, "barrel[facing=up,open=false]" if (x + z) % 3 else "raw_iron_block")
    # giant gears: the drive gear on the west wall meshing the camshaft pinion, a second gear above it
    gear(C, "x", x0 - 1, 46, -20, 6.0, phase=0.1)
    gear(C, "x", x0 - 1, 44, -11, 4.0, phase=0.3, rim=COPPER)
    # the flywheel on the north wall, its belt to the camshaft
    gear(C, "z", -12, 42, z0 - 1, 7.0, teeth=1, rim=IRON, web=None, hub=BRASS)
    # copper amalgamation tables and troughs on the plates floor
    for x in range(-16, -6, 3):
        for z in (-29, -28, -27):
            C.set(x, FM_PLATE, z, "cut_copper_slab[type=bottom,waterlogged=false]")
            C.set(x + 1, FM_PLATE, z, "cut_copper_slab[type=bottom,waterlogged=false]")
        C.set(x, FM_PLATE, -26, "water_cauldron[level=3]")
    for y in range(FM_PLATE, FM_PLATE + 6):
        C.set(-14, y, z0, PIPES)
    C.set(-15, FM_PLATE + 2, z0, GAUGE)
    C.bp.chest(-20, FM_TOP, -11, "east", loot=LOOT + "mm_mill")
    C.bp.chest(-9, FM_PLATE, -30, "south", loot=LOOT + "mm_mill")
    C.bp.barrel(-20, FM_TOP, -13)
    C.bp.barrel(-11, FM_STAMP, -18)
    C.bp.spawner(-15, FM_STAMP, -18, MOB_GUNNER)
    # the vista tunnel south from the top floor to T3, an iron door that opens from the mill side only
    gallery(C, -12, -9, -10, 6, FM_TOP, h=4, floor=boards)
    x, z = -11, 7
    while C.solid(x, FM_TOP, z) and z < 16:
        for xx in (-12, -11, -10):
            C.set(xx, FM_TOP - 1, z, PLANK)
            for y in range(FM_TOP, FM_TOP + 4):
                C.clear(xx, y, z)
        z += 1
    zd = 6
    for xx in (-12, -10):
        for y in range(FM_TOP, FM_TOP + 3):
            C.set(xx, y, zd, POST)
    for y in range(FM_TOP + 2, FM_TOP + 4):
        C.set(-11, y, zd, PLANK)
    C.bp.door(-11, FM_TOP, zd, "south", wood="iron")
    C.keep.add((-11, FM_TOP, zd))
    C.keep.add((-11, FM_TOP + 1, zd))
    lever(C, -12, FM_TOP + 1, zd - 1, "north")


def sw2(C):
    """Under the mill's east side: plates floor (29) down to level 15."""
    flight(C, -6, -18, "north", 7, 22, 3, "east", "spruce_stairs")
    landing(C, -9, -17, -4, -15, 22, PLANK)
    flight(C, -9, -24, "south", 7, FL, 3, "east", "spruce_stairs")
    C.set(-10, 19, -20, EDISON)
    C.set(-3, 25, -21, EDISON)


def level15(C):
    """Level 15: the cross-cut from the stairwell, the dynamite store (west), the drift to the Rusty Spur (south-west),
    the mine-boss office and its vault (east), the stairwell down to the haulage level."""
    gallery(C, -9, -28, -7, -25, FL)                              # landing at the stairwell's foot
    gallery(C, -23, -28, 14, -26, FL, rails=-27)                  # the cross-cut
    # the dynamite store: crates of TNT behind a timber bulkhead, kegs, a blasting box
    mroom(C, -32, -31, -24, -23, FL, 4, "coarse_dirt", wall=lambda x, y, z: PLANK if (x + z) % 4 else POST,
          ceil="stripped_spruce_log[axis=x]")
    carve(C, -23, FL, -28, -23, FL + 2, -26)
    for (x, z) in ((-31, -30), (-30, -30), (-31, -29), (-29, -30), (-31, -27), (-31, -24), (-30, -24)):
        C.set(x, FL, z, "tnt[unstable=false]")
    C.set(-31, FL + 1, -30, "tnt[unstable=false]")
    for (x, z) in ((-25, -30), (-25, -24), (-28, -30)):
        C.bp.barrel(x, FL, z)
    C.set(-27, FL, -24, "barrel[facing=up,open=false]")
    C.set(-26, FL, -30, "lever[face=floor,facing=north,powered=false]")
    C.set(-29, FL, -24, "target[power=0]")
    C.bp.chest(-32, FL, -26, "east", loot=LOOT + "mm_dynamite")
    C.set(-28, FL + 3, -27, LANT_H)
    C.bp.spawner(-28, FL, -27, MOB_MITE)
    # the drift south to the Rusty Spur's back room (iron door, lever on the mine side)
    gallery(C, -22, -25, -20, 10, FL, rails=-21)
    zb = 11
    for xx in (-22, -20):
        for y in range(FL, FL + 3):
            C.set(xx, y, zb, POST)
    C.set(-21, FL + 2, zb, PLANK)
    C.set(-21, FL + 3, zb, PLANK)
    C.bp.door(-21, FL, zb, "south", wood="iron")
    C.keep.update({(-21, FL, zb), (-21, FL + 1, zb)})
    lever(C, -22, FL + 1, zb - 1, "north")
    # the office (x 15..27, z -34..-26): panelled, a desk, maps, a safe-room door
    mroom(C, 15, -34, 27, -26, FL, 5, boards, wall=lambda x, y, z: W + "mahogany_panelling" if y < FL + 4 else PLANK,
          ceil="dark_oak_planks")
    carve(C, 14, FL, -28, 14, FL + 3, -26)
    for (x, z) in ((18, -33), (24, -33)):
        hang(C, x, FL + 3, z + 4, CHANDELIER, reach=3)
    C.set(21, FL, -31, TABLE)
    C.set(22, FL, -31, TABLE)
    C.set(21, FL, -30, stair("dark_oak_stairs", "south"))
    C.set(20, FL, -33, "lectern[facing=south,has_book=false,powered=false]")
    C.set(23, FL, -34, "cartography_table")
    for x in range(16, 27, 2):
        C.set(x, FL + 2, -35, GAUGE if x % 4 == 0 else "bookshelf")
    for z in range(-33, -26, 2):
        C.set(28, FL + 1, z, "bookshelf")
        C.set(28, FL + 2, z, "bookshelf")
    C.set(16, FL, -34, "green_carpet")
    for x in range(18, 25):
        for z in range(-32, -28):
            if C.get(x, FL, z) in (None, AIR):
                C.set(x, FL, z, "red_carpet")
    C.bp.chest(26, FL, -27, "west", loot=LOOT + "mm_office")
    C.bp.barrel(16, FL, -27)
    # the vault behind the north wall: a heavy iron door with a button
    mroom(C, 22, -40, 27, -36, FL, 3, "polished_andesite", wall=IRON, ceil=IRON)
    carve(C, 24, FL, -35, 24, FL + 1, -35)
    C.bp.door(24, FL, -35, "south", wood="iron")
    C.keep.update({(24, FL, -35), (24, FL + 1, -35)})
    C.set(25, FL + 1, -34, "stone_button[face=wall,facing=south,powered=false]")
    C.set(23, FL + 1, -36, "stone_button[face=wall,facing=north,powered=false]")
    C.bp.chest(22, FL, -40, "south", loot=LOOT + "mm_safe")
    C.bp.chest(27, FL, -38, "west", loot=LOOT + "mm_safe")
    C.set(26, FL, -40, "gold_block")
    C.set(26, FL + 1, -40, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(23, FL + 2, -38, LANT_H)


def sw3(C):
    """From the office's south door down to the haulage level."""
    flight(C, 18, -18, "north", 7, 8, 3, "east", "spruce_stairs")
    landing(C, 15, -17, 20, -15, 8, PLANK)
    flight(C, 15, -24, "south", 7, FH, 3, "east", "spruce_stairs")
    carve(C, 18, FL, -25, 20, FL + 3, -25)
    C.set(14, 5, -20, EDISON)
    C.set(21, 11, -21, EDISON)


def haulage(C):
    """The haulage level (feet 1): the main gallery from the winze to the east adit, the shaft station (site of
    grace, the sump, the ladderway), the cart-lift landing, a worked-out stope."""
    gallery(C, -14, -28, 47, -26, FH, rails=-27)
    gallery(C, 15, -25, 17, -25, FH)
    # shaft station: cross-cut to the shaft, the sump pool, the ladderway up to the summit
    x0, z0, x1, z1 = SHAFT
    mroom(C, -2, -25, 6, -23, FH, 4, mine_floor)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(FH, FP):
                C.clear(x, y, z)
            for y in range(-3, 1):
                C.water(x, y, z)
    for y in range(FH, FP):
        C.set(x0, y, -21, "ladder[facing=east,waterlogged=false]")
        if not C.solid(x0 - 1, y, -21):
            C.set(x0 - 1, y, -21, rock(x0 - 1, y, -21))
        for z in (z0 - 1, z1 + 1):
            if (y - FH) % 6 == 0:
                for x in range(x0 - 1, x1 + 2):
                    C.put(x, y, z, POST if x in (x0 - 1, x1 + 1) else "stripped_spruce_log[axis=x]")
    C.set(x0, 0, -21, WATER)
    C.set(5, FH, -24, MOD["waystone"])
    C.set(6, FH + 2, -25, EDISON)
    C.set(-2, FH + 2, -23, EDISON)
    for x in range(x0, x1 + 1):
        C.set(x, FH, -23, AIR)
    # the east adit: a timber portal, the yard outside with a cart on its stub of rail
    for x in range(44, 49):
        for z in range(-29, -24):
            for y in range(FH - 1, FH + 6):
                if z in (-29, -25) or y in (FH - 1, FH + 4):
                    if x >= 45:
                        C.set(x, y, z, DPOST if z in (-29, -25) and y < FH + 4 else
                              "stripped_dark_oak_log[axis=z]")
                elif y < FH + 4:
                    C.clear(x, y, z)
    for x in range(48, 60):
        for z in range(-30, -23):
            C.set(x, 0, z, "gravel" if hash01(x, z, 748) < 0.4 else "coarse_dirt")
            C.set(x, -1, z, "dirt")
            for y in range(1, 5):
                C.clear(x, y, z)
    for x in range(44, 58):
        C.set(x, 0, -27, "stripped_spruce_log[axis=x]")
        C.set(x, 1, -27, "rail[shape=east_west,waterlogged=false]")
    C.set(58, 1, -27, "stripped_dark_oak_log[axis=x]")
    C.set(49, 1, -30, "barrel[facing=up,open=false]")
    C.bp.barrel(50, 1, -30)
    # a worked-out stope north of the gallery: ore pillars, a rust mite nest
    mroom(C, 26, -37, 34, -30, FH, 5, mine_floor)
    carve(C, 29, FH, -29, 31, FH + 3, -29)
    for (x, z) in ((28, -34), (32, -34)):
        for y in range(FH, FH + 5):
            C.set(x, y, z, "raw_iron_block" if y % 2 else rock(x, y, z))
    C.bp.spawner(30, FH, -35, MOB_MITE)
    C.bp.chest(26, FH, -37, "south", loot=LOOT + "mm_haulage")
    C.set(34, FH, -30, "barrel[facing=up,open=false]")
    hang(C, 30, FH + 3, -32)
    # the cart-lift landing (north of the gallery near the adit): an iron door that opens from inside only
    mroom(C, 38, -34, 43, -30, FH, 4, IRON, wall=None)
    C.bp.door(41, FH, -29, "south", wood="iron")
    C.keep.update({(41, FH, -29), (41, FH + 1, -29)})
    for x in (40, 42):
        for y in range(FH, FH + 3):
            C.set(x, y, -29, IRON)
    C.set(41, FH + 2, -29, IRON)
    lever(C, 40, FH + 1, -30, "north")
    C.set(39, FH + 2, -34, EDISON)


def winze(C):
    """From the haulage gallery's west end down 12 to the flooded gallery's catwalk."""
    flight(C, -26, -28, "east", 12, FG, 3, "south", "spruce_stairs")
    for x in range(-27, -14):
        for z in (-29, -25):
            for y in range(FG + max(0, x + 26), FG + max(0, x + 26) + 5):
                C.put(x, y, z, POST if x % 4 == 0 else rock(x, y, z) if y > 0 else deep(x, y, z))
    C.set(-20, -4, -29, EDISON)
    C.set(-24, -8, -25, EDISON)


# ------------------------------------------------------------------ the deep levels
def flooded_gallery(C):
    """A long working half full of black water (2 deep) with a plank catwalk on posts along it, a dead pump engine
    at its east end and a drowned stope to the south with a chest on its floor."""
    x0, z0, x1, z1 = -61, -31, -27, -23
    f = FG
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, f - 4, z, "mud" if hash01(x, z, 749) < 0.5 else "gravel")
            for y in range(f - 3, f - 1):
                C.water(x, y, z)
            C.water(x, f - 1, z)
            for y in range(f, f + 5):
                C.clear(x, y, z)
    # the catwalk (z -28..-26) on posts, a rope rail, lanterns
    for x in range(x0, x1 + 1):
        for z in range(-28, -25):
            C.set(x, f - 1, z, boards(x, z))
        if x % 4 == 0:
            for y in range(f - 3, f - 1):
                C.set(x, y, -29, POST)
                C.set(x, y, -25, POST)
            C.set(x, f - 1, -29, POST)
            C.set(x, f - 1, -25, POST)
            C.set(x, f, -29, FENCE)
            C.set(x, f, -25, FENCE)
            if x % 8 == 0:
                C.set(x, f + 1, -29, LANT)
    # the roof: timber sets every 4 along the walls
    timber_sets(C, x0, z0, x1, z1, f, 5, "x", every=5, lamp_every=10)
    # the dead pump at the east end: a copper cylinder, pipes into the water, gauges
    for y in range(f, f + 4):
        for (x, z) in ((-29, -31), (-28, -31), (-29, -30), (-28, -30)):
            C.set(x, y, z, COPPER if y < f + 3 else BRASS)
    for y in range(f - 3, f + 4):
        C.set(-30, y, -31, PIPES)
    C.set(-28, f + 1, -32, GAUGE)
    C.set(-27, f, -30, "lever[face=floor,facing=west,powered=false]")
    # the drowned stope (south): full of water up to its roof, the chest on the floor
    for x in range(-50, -41):
        for z in range(-22, -15):
            C.set(x, f - 4, z, "gravel")
            for y in range(f - 3, f):
                C.water(x, y, z)
            for y in range(f, f + 3):
                C.set(x, y, z, deep(x, y, z))
    C.bp.chest(-46, f - 3, -17, "north", loot=LOOT + "mm_flooded")
    C.wet.discard((-46, f - 3, -17))
    for (x, z) in ((-49, -16), (-43, -20)):
        for y in range(f - 3, f):
            C.set(x, y, z, POST)
            C.wet.discard((x, y, z))
    C.set(-45, f, -18, "sea_lantern")
    C.set(-48, f, -20, "sea_lantern")
    C.bp.spawner(-36, f, -27, MOB_CRAWLER)
    # the west end: a timber sill holds the water back where the gallery opens onto the collapsed shaft
    for z in range(z0, z1 + 1):
        for y in range(f - 4, f - 1):
            C.set(x0, y, z, "packed_mud" if y < f - 2 else DPLANK)
            C.wet.discard((x0, y, z))
        C.set(x0, f - 1, z, "stripped_dark_oak_log[axis=z]")
        C.wet.discard((x0, f - 1, z))


def pillar(C, x, ytop, z, ybot, spec):
    for y in range(ytop, ybot - 1, -1):
        C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


RAMP = "cobbled_deepslate"
RAMP_WALL = "cobbled_deepslate_wall[east=none,north=none,south=none,up=true,west=none,waterlogged=false]"


def ramp_side(C, x0, z0, facing, wdir, n, f0, yb, flat=0):
    """One side of the collapsed shaft's ramp: n steps 3 wide climbing toward `facing`, a rail cell (a block and a
    wall post) on the void side (offset 3 toward `wdir`), rock filled under it to the shaft floor."""
    cells = flight(C, x0, z0, facing, n, f0, 3, wdir, RAMP + "_stairs")
    dx, dz = DV[facing]
    px, pz = DV[wdir]
    for k in range(1, n + 1 + flat):
        y = f0 + min(k, n) - 1 if k <= n else f0 + n - 1
        for w in range(4):
            x, z = x0 + dx * (k - 1) + px * w, z0 + dz * (k - 1) + pz * w
            if k > n:                                   # flat cells after the last step
                C.set(x, y, z, RAMP)
            if w == 3:
                C.set(x, y, z, RAMP)
                C.set(x, y + 1, z, RAMP_WALL)
            pillar(C, x, y - 1, z, yb + 1, deep)
    return cells


def corner_floor(C, x0, z0, x1, z1, f, yb, spec=RAMP, fill=True, inner=None):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, f - 1, z, spec(x, z) if callable(spec) else spec)
            if fill:
                pillar(C, x, f - 2, z, yb + 1, deep)
    if inner:
        C.set(inner[0], f, inner[1], RAMP_WALL)


def collapsed_shaft(C):
    """A 13 x 13 shaft whose cage fell: a ramp 3 wide (with a parapet on the void side) spirals 19 down round its
    walls, landings at the corners, to the wreck of the cage and its broken sheave on a rubble cone."""
    x0, z0, x1, z1 = -74, -33, -62, -21
    yb, yt = FA - 1, -6                       # floor block, top air
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, yb, z, "cobbled_deepslate" if hash01(x, z, 750) < 0.5 else "tuff")
            for y in range(yb + 1, yt + 1):
                C.clear(x, y, z, inner=True)
    # climbing from the bottom (the exit, NE corner, feet -30) round to the top (NE corner, feet -11)
    corner_floor(C, -65, -33, -62, -30, FA, yb, fill=False)                       # bottom NE: the shaft floor
    ramp_side(C, -62, -29, "south", "west", 4, FA, yb, flat=1)                  # east side, feet -30 -> -26
    corner_floor(C, -65, -24, -62, -21, FA + 4, yb, inner=(-65, -24))           # SE corner
    ramp_side(C, -66, -21, "west", "north", 5, FA + 4, yb)                      # south side -> -21
    corner_floor(C, -74, -24, -71, -21, FA + 9, yb, inner=(-71, -24))           # SW corner
    ramp_side(C, -74, -25, "north", "east", 5, FA + 9, yb)                      # west side -> -16
    corner_floor(C, -74, -33, -71, -30, FA + 14, yb, inner=(-71, -30))          # NW corner
    ramp_side(C, -70, -33, "east", "south", 5, FA + 14, yb)                     # north side -> -11
    # the top: a timber deck over the NE corner and the east side (the lower route runs underneath)
    for x in range(-65, -61):
        for z in range(-33, -24):
            C.set(x, FG - 1, z, boards(x, z) if x > -65 else "stripped_spruce_log[axis=z]")
            for y in range(FG, FG + 4):
                C.clear(x, y, z, inner=True)
        if x == -65:
            for z in range(-30, -24):
                C.set(x, FG, z, FENCE)
    for z in range(-33, -24, 3):
        C.set(-62, FG - 2, z, stair("spruce_stairs", "west", "top"))
    # the void: a rubble cone, the fallen cage, the broken sheave, splintered timbers
    cx, cz = -68, -27
    for x in range(-70, -65):
        for z in range(-29, -24):
            d = math.hypot(x - cx, z - cz)
            t = int(4 - d + (hash01(x, z, 751) - 0.5) * 1.5)
            for y in range(yb + 1, yb + 1 + max(0, t)):
                h = hash3(x, y, z, 752)
                C.set(x, y, z, "cobblestone" if h < 0.3 else "tuff" if h < 0.55 else rock(x, y, z) if h < 0.8 else
                      "coarse_dirt")
    for y in range(yb + 3, yb + 7):
        for (x, z) in ((-69, -28), (-67, -28), (-69, -26), (-67, -26)):
            C.set(x, y, z, "iron_bars")
    for x in range(-69, -66):
        for z in range(-28, -25):
            C.set(x, yb + 7, z, IRON)
    for (a, b) in (((-70, yb + 2, -29), (-66, yb + 9, -25)), ((-70, yb + 1, -25), (-66, yb + 6, -29))):
        for (x, y, z) in line3(a, b):
            if not C.solid(x, y, z):
                C.set(x, y, z, "stripped_spruce_log[axis=y]")
    gear(C, "x", -70, yb + 5, -27, 2.0, rim=IRON, web=None, hub=IRON)
    for y in range(yt - 8, yt + 1):
        C.set(-68, y, -27, CHAIN)
    C.bp.spawner(-74, FA + 9, -21, MOB_CAVE)
    C.bp.chest(-64, FA, -33, "south", loot=LOOT + "mm_shaft")
    for (x, y, z) in ((-63, FG, -32), (-73, FA + 14, -32), (-72, FA + 9, -22), (-63, FA + 4, -22), (-63, FA, -31)):
        C.set(x, y, z, LANT)
    # broken timber sets on the shaft walls
    for y in range(yb + 4, yt, 6):
        for x in range(x0, x1 + 1):
            for z in (z0 - 1, z1 + 1):
                C.put(x, y, z, "stripped_spruce_log[axis=x]" if hash01(x, y, 753) < 0.8 else deep(x, y, z))
        for z in range(z0, z1 + 1):
            for xx in (x0 - 1, x1 + 1):
                C.put(xx, y, z, "stripped_spruce_log[axis=z]" if hash01(z, y, 754) < 0.8 else deep(xx, y, z))


def deep_route(C):
    """The drainage tunnel from the collapsed shaft to the antechamber (site of grace), the narrow tunnel and the
    mist into the cavern."""
    gallery(C, -61, -33, -39, -31, FA, h=4)
    mroom(C, -38, -33, -30, -23, FA, 5, lambda x, z: "polished_tuff" if (x + z) % 2 else "tuff_bricks",
          wall=lambda x, y, z: "tuff_bricks" if y % 4 else POST, ceil="stripped_spruce_log[axis=x]")
    C.set(-31, FA, -32, MOD["waystone"])
    C.set(-37, FA, -32, "barrel[facing=up,open=false]")
    C.bp.barrel(-37, FA, -31)
    C.set(-37, FA, -24, "lectern[facing=east,has_book=false,powered=false]")
    hang(C, -34, FA + 4, -28, LANT_H)
    # the narrow tunnel (compression): 3 wide, 4 high, 15 long, timbered
    gallery(C, -29, -29, -13, -27, FA, h=4, every=3)


def dome_top(d):
    if d >= AR:
        return FA + 3
    return int(FA + 4 + (AR_APEX - FA - 4) * math.sqrt(max(0.0, 1 - (d / AR) ** 2)))


def vein_axis(y):
    """Centre of the ore vein at height y: it leans from south-west at the floor to north-east at the roof."""
    t = (y - FA) / float(AR_APEX - FA)
    return AC[0] - 4 + 9 * t, AC[1] + 3 - 7 * t


def arena(C):
    """The excavated cavern round the half-dug vein, its lining, props, scaffolds and derrick; the boss seal."""
    cx, cz = AC
    n = int(AR) + 3
    for x in range(cx - n, cx + n + 1):
        for z in range(cz - n, cz + n + 1):
            d = math.hypot(x - cx, z - cz)
            dd = d + (vnoise(x, z, 5.0, 760) - 0.5) * 2.0
            if dd > AR + 2:
                continue
            top = dome_top(min(dd, AR))
            for y in range(FA - 2, AR_APEX + 3):
                if dd <= AR and FA <= y <= top:
                    C.clear(x, y, z, inner=True)
                elif dd <= AR and y == FA - 1:
                    h = hash01(x, z, 761)
                    C.set(x, y, z, "packed_mud" if h < 0.3 else "coarse_dirt" if h < 0.55 else "cobbled_deepslate"
                          if h < 0.8 else "tuff")
                elif dd <= AR and y > top and y <= top + 2:
                    C.put(x, y, z, cave_wall(x, y, z))
                elif dd > AR and FA - 1 <= y <= dome_top(AR) + 1:
                    C.put(x, y, z, cave_wall(x, y, z))
    # the vein: a leaning column of ore (gold and copper in twisted bands), the south-west half quarried in benches
    for y in range(FA, AR_APEX + 1):
        vx, vz = vein_axis(y)
        rr = 5.2 - 1.6 * (y - FA) / (AR_APEX - FA)
        for x in range(int(vx - rr) - 1, int(vx + rr) + 2):
            for z in range(int(vz - rr) - 1, int(vz + rr) + 2):
                d = math.hypot(x - vx, z - vz)
                if d > rr + (hash3(x, y, z, 762) - 0.5) * 0.8:
                    continue
                if y > dome_top(math.hypot(x - cx, z - cz)):
                    continue
                # quarried benches: the half facing the entrance (west / south-west) is cut back in steps of 3
                cut = (x - vx) * 0.8 + (z - vz) * -0.6
                bench = (y - FA) // 3
                if cut < -0.5 and y < FA + 15 and d > rr - 1.4 - (bench % 2) and y % 3 != 0:
                    continue
                a = math.atan2(z - vz, x - vx) + y * 0.35
                band = int((a + math.pi) / (math.pi / 3)) % 3
                h = hash3(x, y, z, 763)
                if band == 0:
                    spec = "raw_gold_block" if h < 0.18 else ("deepslate_gold_ore" if y < -20 else "gold_ore")
                elif band == 1:
                    spec = "raw_copper_block" if h < 0.2 else ("deepslate_copper_ore" if y < -20 else "copper_ore")
                else:
                    spec = "calcite" if h < 0.4 else ("tuff" if h < 0.7 else "smooth_basalt")
                if h > 0.97:
                    spec = "gold_block"
                C.set(x, y, z, spec)
    # scaffolding against the quarried face, ladders, a timber derrick with its boom over the vein
    for (sx, sz, hgt) in ((cx - 9, cz + 5, 9), (cx - 7, cz + 8, 12), (cx - 10, cz + 1, 6)):
        for y in range(FA, FA + hgt):
            C.set(sx, y, sz, "scaffolding[bottom=false,distance=0,waterlogged=false]")
    for (x, y, z) in line3((cx - 16, FA, cz - 12), (cx - 16, FA + 14, cz - 12)):
        C.set(x, y, z, "dark_oak_log[axis=y]")
    for (x, y, z) in line3((cx - 16, FA + 14, cz - 12), (cx - 3, FA + 10, cz - 4)):
        C.set(x, y, z, "stripped_dark_oak_log[axis=x]")
    for y in range(FA + 3, FA + 10):
        C.set(cx - 3, y, cz - 4, CHAIN)
    C.set(cx - 3, FA + 2, cz - 4, IRON)
    for (x, y, z) in line3((cx - 18, FA, cz - 14), (cx - 16, FA + 10, cz - 12)):
        C.set(x, y, z, "dark_oak_log[axis=y]")
    # timber props round the wall, lamps on chains from the dome
    for k in range(16):
        a = k * math.pi / 8 + 0.2
        x, z = round(cx + (AR - 0.6) * math.cos(a)), round(cz + (AR - 0.6) * math.sin(a))
        if abs(z - (-28)) <= 2 and x < cx:
            continue
        if x > cx + 18 and abs(z + 27) <= 2:
            continue
        for y in range(FA, FA + 4):
            C.set(x, y, z, POST)
        C.set(x, FA + 4, z, "stripped_spruce_log[axis=y]")
    for (x, z) in ((cx - 10, cz - 8), (cx + 10, cz - 8), (cx - 10, cz + 9), (cx + 11, cz + 7), (cx, cz - 15),
                   (cx - 14, cz), (cx + 15, cz - 1), (cx + 1, cz + 15)):
        hang(C, x, FA + 7, z, LANT_H, reach=20)
    # a cart track round part of the floor with a buffer
    for x in range(cx - 6, cx + 13):
        C.set(x, FA - 1, cz + 14, "stripped_spruce_log[axis=x]")
        C.set(x, FA, cz + 14, "rail[shape=east_west,waterlogged=false]")
    C.set(cx + 13, FA, cz + 14, IRON)
    C.bp.boss_seal(cx + 2, FA - 1, cz + 10, BOSS, 20)
    # the mist across the narrow tunnel's mouth
    C.bp.mist(-14, FA, -29, -13, FA + 3, -27)


def strongroom(C):
    """Behind sealed bars east of the cavern: the company strongroom (vault) and the cart-lift up to the haulage
    level (a bubble column in an iron cage)."""
    gallery(C, 28, -29, 31, -27, FA, h=3)
    for z in (-29, -28, -27):
        for y in range(FA, FA + 3):
            C.set(30, y, z, MOD["vault_bars"])
    mroom(C, 32, -33, 40, -22, FA, 4, lambda x, z: "gold_block" if (x + z) % 7 == 0 else "polished_deepslate",
          wall=lambda x, y, z: "deepslate_tiles" if y % 3 else IRON, ceil=IRON)
    for (x, z, fc) in ((34, -33, "south"), (38, -33, "south"), (32, -24, "east")):
        C.bp.chest(x, FA, z, fc, loot=LOOT + "mm_vault")
    for (x, z) in ((36, -33), (40, -23), (33, -22)):
        C.set(x, FA, z, "gold_block")
        C.set(x, FA + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    C.set(39, FA, -22, "raw_gold_block")
    hang(C, 36, FA + 3, -28, CHANDELIER, reach=3)
    # the cart-lift: a bubble column at (42, -32) from the strongroom up through the rock to the landing at feet 1;
    # a wooden door holds the water back at its foot (x 41), glass and iron casing where it shows
    lx, lz = 42, -32
    C.set(lx, FA - 2, lz, "soul_sand")
    for y in range(FA - 1, FH):
        C.set(lx, y, lz, "bubble_column[drag=false]")
        C.wet.add((lx, y, lz))
        C.keep.discard((lx, y, lz))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dz) == (0, 0):
                    continue
                x, z = lx + dx, lz + dz
                if y == FH - 1:
                    C.set(x, y, z, IRON)
                elif dx == -1 and dz == 0 and y in (FA, FA + 1):
                    continue
                elif y <= FA + 3:
                    C.set(x, y, z, IRON if (dx and dz) or y in (FA - 1, FA + 3) else "glass")
                else:
                    C.set(x, y, z, "deepslate_tiles" if y % 6 else IRON)
    # signs hold the water back in the doorway (a standing sign on the sill, a hanging sign under the lintel)
    C.set(lx - 1, FA, lz, "spruce_sign[rotation=4,waterlogged=false]")
    C.set(lx - 1, FA + 1, lz, "spruce_hanging_sign[attached=false,rotation=4,waterlogged=false]")
    C.set(lx - 1, FA + 2, lz, IRON)
    C.set(lx - 1, FA - 1, lz, IRON)
    C.set(lx, FA - 1, lz, "bubble_column[drag=false]")
    C.set(lx - 2, FA + 2, lz, EDISON) if C.get(lx - 2, FA + 2, lz) == AIR else None


# ------------------------------------------------------------------ sealing, the breach check, the builder
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def seal(C):
    """Line every unset neighbour of the build's underground air and water with rock, so no natural cave, aquifer or
    lava pocket leaks into the mine; report carved interior cells above the ground that touch open air."""
    bp = C.bp
    cells = [c for c in C.keep if c[1] <= 0 and bp.get(*c) == AIR] + [c for c in C.wet if c[1] <= 0]
    for (x, y, z) in cells:
        for (dx, dy, dz) in N6:
            nx, ny, nz = x + dx, y + dy, z + dz
            if ny <= 0 and bp.get(nx, ny, nz) is None:
                bp.set(nx, ny, nz, deep(nx, ny, nz))
    leaks = set()
    for (x, y, z) in C.wet:
        if "water" not in (bp.get(x, y, z) or "") and "bubble" not in (bp.get(x, y, z) or ""):
            continue
        for (dx, dy, dz) in N6:
            if dy == 1:
                continue
            n = bp.get(x + dx, y + dy, z + dz)
            if n == AIR or (n is None and y + dy > 0):
                leaks.add((x + dx, y + dy, z + dz))
    if leaks and BREACH_REPORT:
        print(f"mesa_minecity: {len(leaks)} cells water would flow into, e.g. {sorted(leaks)[:12]}")
    breaches = []
    for (x, y, z) in C.inner:
        if y < 1 or bp.get(x, y, z) != AIR:
            continue
        for (dx, dy, dz) in N6:
            if bp.get(x + dx, y + dy, z + dz) is None:
                breaches.append((x + dx, y + dy, z + dz))
    if breaches and BREACH_REPORT:
        print(f"mesa_minecity: {len(breaches)} interior cells open to the sky, e.g. {sorted(set(breaches))[:12]}")
    if BREACH_PATCH:
        for (x, y, z) in set(breaches):
            bp.set(x, y, z, rock(x, y, z))


BREACH_REPORT = True
BREACH_PATCH = True


def mesa_minecity(bp):
    C = Ctx(bp)
    butte(C)
    town(C)
    camp(C)
    outskirts(C)
    grand_stair(C)
    terraces(C)
    railway(C)
    headframe(C)
    hoist_house(C)
    summit(C)
    sw1(C)
    mill(C)
    sw2(C)
    level15(C)
    sw3(C)
    haulage(C)
    winze(C)
    flooded_gallery(C)
    collapsed_shaft(C)
    deep_route(C)
    arena(C)
    strongroom(C)
    seal(C)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("saloon", (-23, 15, 19), (-23, 17, 13)),
    ("stamp_mill", (-12, 43, -11), (-12, 40, -29)),
    ("boss_office", (17, 15, -27), (24, 16, -33)),
    ("dynamite_store", (-25, 15, -27), (-31, 16, -30)),
    ("flooded_gallery", (-30, -11, -27), (-58, -10, -27)),
    ("collapsed_shaft", (-63, -11, -29), (-68, -25, -27)),
    ("ore_vein_cavern", (-11, -30, -28), (8, -18, -27)),
]

register(StructureDef(
    "mesa_minecity", "overworld", ["badlands", "eroded_badlands", "wooded_badlands"],
    [Piece("city", mesa_minecity, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_HUSK, 6, 1, 2), (MOB_BANDIT, 4, 1, 1), (MOB_MITE, 4, 1, 2)],
    title_fr="La Ville minière de la Mesa rouille", title_en="Rust Mesa Mine-City"))
