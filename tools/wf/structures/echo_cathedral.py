"""The Echo Cathedral (La Cathédrale de l'Écho): a gothic cathedral of deepslate and tarnished brass built inside a vast
cavern a hundred blocks down, under deep dark or dripstone caves, with a giant pipe organ in its apse whose pipes rise
60 blocks into the cavern ceiling. Colossal tier (tools/BUILDING.md §1, §12 concept 22, §10, §15).

Silhouette (one noun phrase, §15.1): a black cathedral under a stone sky, its flying buttresses braced against the
cave walls, two square west towers, and behind the apse a fan of brass organ pipes rising into the dripstone.
Theme: sound and silence. Bells, amethyst, note blocks and muffled wool; sculk grows over the tombs (decoration only:
sculk sensors, veins and catalysts, never a shrieker, so no warden is ever summoned).

Layout, blueprint y = world y - start height - 12 (template bottom = the crypt bed at y -12): the nave floor is
the block layer y 0, feet 1; x east, z south, the main axis on x = 0 with the west front (south, +z) at z 52 and the
apse (north, -z) round z -60. Placed at a fixed height (start y -56..-53: nave feet near world y -42) in deep dark
and dripstone caves; found with the structure compass (like the other underground wonders, §15.8).
  * the approach: the pilgrims' camp (waystone) in a dripstone side cave south of the cavern, whose old stair to
    the surface has fallen in; a low tunnel (compression, 3 x 4, 15 long) opens onto the forecourt (release): the
    facade, its rose window and the twin towers under the cave roof, six hooded choristers in stone lining the way;
  * the west front: the great portal (9 x 15) is barred by its leaves; its wicket door opens only from inside
    (shortcut 1). Enter by the door at the foot of the south-west tower: its lodge, a wall passage to the narthex;
  * the nave (feet 1): 13 wide, its vault 36 high on 7 x 7 deepslate columns with brass bands, aisles under a
    triforium, three side chapels a side (the Hush, the Tuning Forks, the Drowned Hymn; the Bells, the Echoes,
    Saint Cecilia), the crossing (the hub, site of grace) with the transepts and the raised choir behind a grille;
  * up: the newel stairs in both west towers climb to the choir loft over the narthex (feet 16), which joins the
    triforium galleries above the aisles. The south-west tower goes on to the bell chamber (feet 31) and its
    cracked bronze bell, with a view up the nave roof to the organ; the south-east tower to the bellows loft;
  * the main route: the east triforium north to the transept balcony, out of its end door over a flying-buttress
    bridge into the cave wall: the choristers' dormitory (feet 16); its rock stair (four flights, landings) down
    past an iron door onto the cavern floor (shortcut 2, one-way) to a long corridor under the transept and the
    flooded crypt under the crossing and the choir: sculk-overgrown tombs in a black pool, raised causeways, the
    site of grace by the choir turret; the turret stair (compression) climbs to the mist and the arena;
  * the boss: the choir and the apse, raised over the crypt (feet 9), open to the cavern above the broken vault,
    ripples of brass in the floor, the organ console on its dais and the pipes rising behind it into the ceiling.
    Behind the organ, the sealed reliquary (best loot). After the fight, the choir grille opens from inside onto
    the choir stair and the crossing (shortcut 3);
  * the pipe-shaft lift: a bubble column in a brass organ pipe from the crypt annex up to the crossing floor (the
    hub grace), the fast way back from the depths (shortcut 4);
  * optional: the chapels, the west bridge to the cantors' library, the bell chamber, the bellows loft, the cave
    floor round the cathedral (buttress walk) with its piers, dripstone and sculk.
Loot gradient (§15.6): camp, chapels, sacristy tier 1; loft, dormitory tier 1-2; library, belfry, bellows tier 2;
crypt tier 2-3; the reliquary tier 3.
Budget: the cavern is the bulk of the entries (every cell of it must be written as air); its roof hugs the
cathedral (low by the walls, high over the nave and the apse) to stay under ~450k entries.
"""
import math

from ..arch import slab, stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, GAUGE, GEAR, HANG_LAMP, IRON, IRON_SLAB,
                       IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_SLAB, MAHOGANY_STAIRS, PIPES, VERD, W, fbm, hash01,
                       hash3, pointed_arch)
from ..parts import LOOT, MOD
from .caldera_ringwall import newel

# the cathedral's champion, the Hollow Cantor, at the organ console (entity/boss/HollowCantor.java, tools/BOSSES.md)
BOSS = "brasshaven:hollow_cantor"
MOB_MONK = "brasshaven:bell_monk"
MOB_CRAWLER = "brasshaven:crypt_crawler"
MOB_ABYSS = "brasshaven:abyss_crawler"
MOB_BANSHEE = "brasshaven:banshee"

# ------------------------------------------------------------------ dimensions
F = 1                    # nave feet (floor block y 0)
GAL = 16                 # choir loft, triforium galleries, transept balconies (floor y 14..15)
CHF = 9                  # choir and apse feet (floor y 7..8)
KF = -9                  # crypt feet (causeway blocks y -10; the pool: water y -10 over a bed at y -11)
BELL_F = 31              # bell chamber and bellows loft feet (floor y 30)
SPRING, CROWN = 28, 36   # nave and transept vault
RIDGE = 41
TOWER_TOP = 46
NHW = 6                  # nave clear half width (x -6..6)
COLS = [26, 13, 0, -13]  # nave column centres (z); x centres +-10, 7 x 7
CROSS_S, CROSS_N = -26, -46
BAYS = [(30, 40), (17, 22), (4, 9), (-9, -4), (-22, -17)]   # arcade openings between the columns (z ranges)
CHAPELS = [(16, 23), (3, 10), (-10, -3)]                     # side chapel interiors (z ranges)
TRZ0, TRZ1 = -42, -30    # transept interior (z)
TRX = 28                 # transept interior reaches |x| 28, end wall 29..30
AZ, AR = -60, 18         # apse centre (z) and inner radius
ZC0, ZC1 = -52, -60      # choir floor (z) between the screen and the apse
WALLH = 7                # cave walls rise this high before the roof curves in
ROOF_P = 2.0             # roof profile across the cavern: 1 - u**ROOF_P (u = 0 on the axis, 1 at the wall)
LIFT = (-4, -35)         # the pipe-shaft lift (crypt annex -> crossing)

AIR = "minecraft:air"
POL, BRK, TIL, CHI = "polished_deepslate", "deepslate_bricks", "deepslate_tiles", "chiseled_deepslate"
CBRK, CTIL, COB = "cracked_deepslate_bricks", "cracked_deepslate_tiles", "cobbled_deepslate"
PB, PBB = "polished_blackstone", "polished_blackstone_bricks"
BRK_ST, TIL_ST, POL_ST = "deepslate_brick_stairs", "deepslate_tile_stairs", "polished_deepslate_stairs"
BRK_SL, TIL_SL, POL_SL = "deepslate_brick_slab", "deepslate_tile_slab", "polished_deepslate_slab"
BRK_W, TIL_W, POL_W = "deepslate_brick_wall", "deepslate_tile_wall", "polished_deepslate_wall"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
WATER = "water[level=0]"
RAIL = W + "brass_railing"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def pick(choices, x, y, z, seed):
    tot = sum(w for _, w in choices)
    h = hash3(x, y, z, seed) * tot
    for s, w in choices:
        h -= w
        if h <= 0:
            return s
    return choices[-1][0]


def mas(x, y, z):
    """Deepslate masonry with a vertical gradient (§5): rough and dark at the base, bricks in the body, cleaner and
    lighter toward the crown; the band edges jitter so no straight line separates two steps."""
    yy = y + (hash3(x // 2, y // 3, z // 2, 5) - 0.5) * 5
    if yy < 4:
        return pick([(COB, 2), (CTIL, 2), (TIL, 3), (CBRK, 1.5)], x, y, z, 11)
    if yy < 30:
        return pick([(BRK, 6), (TIL, 2), (CBRK, 1.2), (POL, 0.4)], x, y, z, 12)
    return pick([(BRK, 4), (POL, 3), (TIL, 1.5)], x, y, z, 13)


def tarnish(x, y, z):
    """Tarnished brass: verdigris spreads from the damp base and in patches."""
    v = fbm(x * 0.9 + z * 0.4, y * 0.8 + z * 0.3, 4.0, 77)
    return VERD if v + max(0, (20 - y)) * 0.012 > 0.62 else BRASS


def rock(x, y, z):
    """Cave rock: strata of deepslate, tuff and calcite with dripstone patches (two-octave jitter, §11)."""
    yy = y + (fbm(x * 0.6 + z * 0.4, y * 0.9, 7.0, 41) - 0.5) * 7
    seq = ("deepslate", "deepslate", "tuff", "deepslate", "cobbled_deepslate", "deepslate", "calcite", "tuff",
           "deepslate", "smooth_basalt")
    s = seq[int(yy // 3) % len(seq)]
    if fbm(x, z + y * 0.5, 9.0, 43) > 0.66:
        s = "dripstone_block"
    h = hash3(x, y, z, 7)
    if h < 0.06:
        return "cobbled_deepslate"
    return s


# ------------------------------------------------------------------ site state
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.cmap = {}          # (x, z) -> top air y of the cavern column (floor y 0)
        self.lining = set()     # cave rock written round the cavern (free to carve or replace)
        self.walk = set()       # cells kept clear for walking

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def soft(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or (x, y, z) in self.lining

    def free(self, x, y, z):
        return self.bp.get(x, y, z) == AIR


# ------------------------------------------------------------------ the cavern
def _lerp(pts, z):
    if z >= pts[0][0]:
        return pts[0][1]
    for (z0, v0), (z1, v1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            t = (z0 - z) / (z0 - z1)
            return v0 + (v1 - v0) * t
    return pts[-1][1]


# half width at the floor (z -> W); north of AZ the cavern closes round the apse in a circle of radius CAVE_R
HALF_W = [(70, 7), (67, 16), (61, 24), (54, 30), (44, 30), (20, 30), (-24, 30), (-28, 36), (-44, 36), (-49, 30),
          (-60, 27)]
CAVE_R = 27.0
def cave_w(z, side):
    if z < AZ:
        d = CAVE_R ** 2 - (z - AZ) ** 2
        w = math.sqrt(max(0.0, d))
    else:
        w = _lerp(HALF_W, z)
    return w + (fbm(z * 1.0, side * 37.0, 6.0, 31) - 0.5) * 5.0


def _nave_top(x, z):
    return roof_top(min(abs(x), 9)) + 2


def _transept_top(x, z):
    return RIDGE + 1 - int(round(max(0.0, abs(z - (TRZ0 + TRZ1) / 2.0) - 0.5) * (RIDGE - 29) / 7.5))


# the masses the cavern roof must clear: (kind, plan, top, margin); the roof falls away from each at SLOPE
SHAPES = [
    ("rect", (-9, 9, -51, 48), _nave_top, 5),
    ("rect", (-11, 11, 41, 53), 47, 4),                    # the west front's gable
    ("rect", (-25, -11, 39, 54), 52, 3),                   # the towers and their pinnacles
    ("rect", (11, 25, 39, 54), 52, 3),
    ("rect", (-22, 22, -29, 40), 25, 4),                   # aisle terraces
    ("rect", (-29, 29, -15, 28), 32, 3),                   # piers and their pinnacles
    ("rect", (-31, 31, -45, -27), _transept_top, 4),
    ("circle", (0, AZ, 21), 40, 4),                        # the apse wall and its pinnacles
    ("rect", (-21, 21, -61, -49), 40, 4),
    ("circle", (0, AZ - 6, 15), 62, 3),                    # the organ: the tallest pipes rise into the roof
    ("circle", (0, AZ, 26), 35, 3),                        # radiating piers
    ("rect", (20, 28, -68, -50), 24, 3),                   # the choir turret
    ("circle", (0, -87, 8), 31, 3),                        # the reliquary
    ("rect", (-14, 14, 53, 67), 8, 3),                     # the forecourt and its statues
]
SLOPE = 2.0
BASE_ROOF = [(70, 10), (60, 22), (40, 26), (-40, 26), (-60, 28)]


def keep_clear(x, z):
    """Lowest roof over column (x, z): the highest mass nearby plus its margin, falling away with distance."""
    k = 0
    for kind, plan, top, margin in SHAPES:
        if kind == "rect":
            x0, x1, z0, z1 = plan
            dx = max(x0 - x, 0, x - x1)
            dz = max(z0 - z, 0, z - z1)
            d = math.hypot(dx, dz)
            px, pz = min(max(x, x0), x1), min(max(z, z0), z1)
        else:
            cx, cz, r = plan
            d = max(0.0, math.hypot(x - cx, z - cz) - r)
            px, pz = x, z
        t = top(px, pz) if callable(top) else top
        k = max(k, t + margin - SLOPE * d)
    return k


def roof_y(x, z, w):
    if z < AZ:
        u = math.hypot(x, z - AZ) / CAVE_R
    else:
        u = abs(x) / max(w, 1.0)
    u = min(1.0, u)
    h = _lerp(BASE_ROOF, z)
    c = WALLH + (h - WALLH) * (1 - u ** ROOF_P)
    c = max(c, keep_clear(x, z))
    c += (fbm(x * 0.8, z * 0.8, 7.0, 35) - 0.5) * 4.0
    return int(round(c))


def cavern(S):
    """Air of the cavern over a rock floor, a one-block lining of strata round it (walls and roof)."""
    bp = S.bp
    wy = {}
    for z in range(-95, 72):
        for side in (-1, 1):
            w0 = cave_w(z, side)
            for y in range(0, 80):
                # the walls wander a little with height
                wy[(z, side, y)] = w0 + (fbm(z * 0.7, y * 0.9 + side * 50, 5.0, 33) - 0.5) * 3.0
    cols = {}
    for z in range(-95, 72):
        for x in range(-45, 46):
            side = 1 if x >= 0 else -1
            w0 = wy[(z, side, 0)]
            if abs(x) >= w0:
                continue
            top = roof_y(x, z, w0)
            # the walls: below WALLH the floor-width test; above, the column ends where the wall leans in
            ytop = 0
            for y in range(1, top + 1):
                if abs(x) >= wy[(z, side, min(y, 79))] and y > 2:
                    break
                ytop = y
            if ytop >= 3:
                cols[(x, z)] = ytop
    S.cmap = cols
    for (x, z), top in cols.items():
        for y in range(1, top + 1):
            bp.set(x, y, z, AIR)
        bp.set(x, 0, z, floor_rock(x, z))
    # lining: the roof and the walls
    for (x, z), top in cols.items():
        if bp.get(x, top + 1, z) is None:
            bp.set(x, top + 1, z, rock(x, top + 1, z))
            S.lining.add((x, top + 1, z))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            ntop = cols.get(n, 0)
            for y in range(max(1, ntop + 1), top + 1):
                if bp.get(n[0], y, n[1]) is None:
                    bp.set(n[0], y, n[1], rock(n[0], y, n[1]))
                    S.lining.add((n[0], y, n[1]))
            if ntop == 0 and bp.get(n[0], 0, n[1]) is None:
                bp.set(n[0], 0, n[1], rock(n[0], 0, n[1]))
                S.lining.add((n[0], 0, n[1]))


def floor_rock(x, z):
    h = hash01(x, z, 21)
    n = fbm(x, z, 8.0, 22)
    if z < -20 and n > 0.6:
        return "sculk" if h < 0.7 else "sculk_catalyst" if h < 0.71 else "deepslate"
    if n < 0.3:
        return "tuff" if h < 0.5 else "deepslate"
    return "deepslate" if h < 0.55 else ("cobbled_deepslate" if h < 0.8 else "polished_deepslate")


def carve(S, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                S.bp.set(x, y, z, AIR)
                S.lining.discard((x, y, z))


def rock_room(S, x0, z0, x1, z1, f, h, wall=None, floor=None, ceil=None):
    """Carve air x0..x1, z0..z1, feet f, h high; dress every soft cell round it (walls, floor, ceiling)."""
    bp = S.bp
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 1, f + h + 1):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and f <= y < f + h
                if inside:
                    bp.set(x, y, z, AIR)
                    S.lining.discard((x, y, z))
                elif S.soft(x, y, z):
                    if y == f - 1 and x0 <= x <= x1 and z0 <= z <= z1:
                        spec = floor(x, z) if callable(floor) else (floor or mas(x, y, z))
                    elif y == f + h and ceil is not None:
                        spec = ceil(x, z) if callable(ceil) else ceil
                    else:
                        spec = wall(x, y, z) if callable(wall) else (wall or mas(x, y, z))
                    bp.set(x, y, z, spec)
                    S.lining.discard((x, y, z))


# ------------------------------------------------------------------ the side cave and the tunnel
def side_cave(S):
    """The pilgrims' camp in a dripstone side cave south of the cavern, and the low tunnel to the forecourt."""
    bp = S.bp
    cx, cz = 3, 95
    cells = []
    for x in range(cx - 16, cx + 17):
        for z in range(cz - 14, cz + 15):
            n = fbm(x * 1.1, z * 1.1, 5.0, 61)
            rx, rz = 12.5 + (n - 0.5) * 6, 11.0 + (n - 0.5) * 5
            d = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
            if d >= 1.0:
                continue
            top = int(round(3 + 8 * math.sqrt(1 - d) + (fbm(x, z, 4.0, 62) - 0.5) * 3))
            cells.append((x, z, top))
    have = {(x, z) for x, z, _ in cells}
    for x, z, top in cells:
        bp.set(x, 0, z, "dripstone_block" if hash01(x, z, 63) < 0.3 else ("tuff" if hash01(x, z, 64) < 0.5
                                                                            else "deepslate"))
        for y in range(1, top + 1):
            bp.set(x, y, z, AIR)
        if bp.get(x, top + 1, z) is None:
            bp.set(x, top + 1, z, rock(x, top + 1, z))
            S.lining.add((x, top + 1, z))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in have:
                continue
            for y in range(0, top + 2):
                if bp.get(n[0], y, n[1]) is None:
                    bp.set(n[0], y, n[1], rock(n[0], y, n[1]))
                    S.lining.add((n[0], y, n[1]))
    S.side_cells = cells
    # the tunnel: 3 wide, 4 high, from the cavern's throat to the side cave
    for z in range(64, 86):
        for x in range(-2, 3):
            for y in range(0, 6):
                inner = abs(x) <= 1 and 1 <= y <= 4
                if inner:
                    bp.set(x, y, z, AIR)
                    S.lining.discard((x, y, z))
                elif S.soft(x, y, z):
                    spec = ("polished_deepslate" if abs(x) <= 1 else BRK) if y == 0 else mas(x, y, z)
                    bp.set(x, y, z, spec)
                    S.lining.discard((x, y, z))
        if bp.get(0, 0, z) is not None and abs(z - 75) < 11:
            bp.set(0, 0, z, POL if z % 2 else TIL)
    for z in (70, 77, 83):
        bp.set(0, 5, z, CHI)
        bp.set(0, 4, z, LANT_H)
    camp(S)


def camp(S):
    """Tents, a fire, the waystone, a chest, and the fallen stair that once led to the surface."""
    bp = S.bp
    cx, cz = 3, 95
    bp.set(cx, 0, cz, COB)
    bp.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, fc) in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz + 2, "north")):
        bp.set(x, 1, z, stair("spruce_stairs", OPP[fc]))
    for (tx, tz, col) in ((cx - 7, cz - 4, "gray_wool"), (cx + 5, cz + 3, "brown_wool")):
        for dz in range(0, 4):
            bp.set(tx - 1, 1, tz + dz, col)
            bp.set(tx + 1, 1, tz + dz, col)
            bp.set(tx, 2, tz + dz, col)
            bp.set(tx, 1, tz + dz, AIR)
        bp.set(tx, 0, tz + 3, "spruce_planks")
        bp.set(tx, 1, tz + 3, "white_carpet")
    bp.set(cx - 4, 1, cz + 4, MOD["waystone"])
    bp.set(cx - 3, 1, cz + 5, "candle[candles=3,lit=true,waterlogged=false]")
    bp.chest(cx + 6, 1, cz - 3, "west", loot=LOOT + "ec_camp")
    bp.barrel(cx + 6, 1, cz - 2, "up")
    bp.barrel(cx + 7, 1, cz - 1, "up")
    bp.set(cx + 6, 1, cz - 1, "crafting_table")
    for (x, z) in ((cx - 6, cz + 2), (cx + 2, cz - 6)):
        bp.set(x, 1, z, "spruce_fence")
        bp.set(x, 2, z, "spruce_fence")
        bp.set(x, 3, z, LANT)
    # the fallen stair (south-west): six steps up into rubble, a sign on the last landing
    for k in range(6):
        z = 104 + k
        for x in range(-4, -1):
            bp.set(x, k, z, stair(BRK_ST, "south"))
            for y in range(k + 1, k + 5):
                bp.set(x, y, z, AIR)
                S.lining.discard((x, y, z))
            for y in range(0, k):
                bp.set(x, y, z, BRK)
        for x in (-5, -1):
            for y in range(0, k + 6):
                if S.soft(x, y, z):
                    bp.set(x, y, z, mas(x, y, z))
        for x in range(-4, -1):
            if S.soft(x, k + 5, z):
                bp.set(x, k + 5, z, mas(x, k + 5, z))
    for x in range(-5, 0):
        for y in range(5, 12):
            bp.set(x, y, 110, "gravel" if hash3(x, y, 110, 3) < 0.4 else COB)
        for y in range(0, 12):
            if S.soft(x, y, 111):
                bp.set(x, y, 111, COB)
    for x in range(-4, -1):
        bp.set(x, 6, 109, "gravel" if x != -3 else COB)
    bp.set(-2, 6, 109, AIR)
    bp.set(-3, 6, 108, "spruce_wall_sign[facing=north,waterlogged=false]")


# ------------------------------------------------------------------ forecourt
def forecourt(S):
    bp = S.bp
    for z in range(53, 68):
        hw = 15 - max(0, z - 60) * 1.4
        for x in range(-16, 17):
            if abs(x) + (fbm(x, z, 4.0, 71) - 0.5) * 3 > hw or (x, z) not in S.cmap:
                continue
            if abs(x) <= 1:
                spec = POL
            elif abs(x) <= 3:
                spec = TIL if (x + z) % 2 else POL
            else:
                spec = pick([(TIL, 3), (CTIL, 1), (COB, 1), ("deepslate", 1)], x, 0, z, 72)
            bp.set(x, 0, z, spec)
    # six hooded choristers in stone, a finger to the lips (sound and silence): repetition along the way in
    for z in (56, 60, 64):
        for sx in (-1, 1):
            chorister(S, sx * 6, z, "east" if sx < 0 else "west")
    for z in (58, 62):
        for sx in (-1, 1):
            x = sx * 9
            bp.set(x, 1, z, PBB)
            bp.set(x, 2, z, POL_W)
            bp.set(x, 3, z, POL_W)
            bp.set(x, 4, z, SOUL)


def chorister(S, x, z, face):
    bp = S.bp
    bp.set(x, 1, z, PBB)
    bp.set(x, 2, z, CHI)
    bp.set(x, 3, z, POL)
    bp.set(x, 4, z, POL)
    bp.set(x, 5, z, "skeleton_skull[rotation=%d]" % {"east": 12, "west": 4}[face])
    dx, dz = DIRS[face]
    bp.set(x + dx, 4, z, stair(POL_ST, OPP[face], "top"))      # the raised hand
    bp.set(x, 6, z, slab(POL_SL))                               # the hood


# ------------------------------------------------------------------ nave, aisles, crossing
def roof_top(ax):
    """Top block of the nave roof at |x| = ax (eaves at 9, ridge 41)."""
    return RIDGE - int(round(ax * (RIDGE - 29) / 9.0))


VAULT = pointed_arch(NHW + 0.5, CROWN - SPRING)


def vault_top(ax):
    """Top air y of the nave vault at |x| = ax."""
    return SPRING + int(VAULT(ax + 0.0))


def in_column(x, z):
    ax = abs(x)
    if not 7 <= ax <= 13:
        return False
    for c in COLS + [CROSS_S, CROSS_N]:
        if c - 3 <= z <= c + 3:
            return True
    return False


def bay_of(z):
    for z0, z1 in BAYS:
        if z0 <= z <= z1:
            return z0, z1
    return None


def arcade_top(z):
    b = bay_of(z)
    if not b:
        return 0
    z0, z1 = b
    hw = (z1 - z0 + 1) / 2.0
    mid = (z0 + z1) / 2.0
    arc = pointed_arch(hw, 3 + hw * 0.6)
    return 8 + int(arc(z - mid))


def nave_shell(S):
    """The solid envelope of nave, aisles and the crossing bay (z -51..40), then the carved volumes."""
    bp = S.bp
    for z in range(-51, 41):
        for x in range(-21, 22):
            ax = abs(x)
            if z < -29 and ax > 13:
                continue            # the transepts and the choir corner are built on their own
            top = roof_top(ax) if ax <= 9 else 23
            for y in range(0, top + 1):
                bp.set(x, y, z, mas(x, y, z))
            if ax <= 9:
                fc = "west" if x > 0 else "east"
                if x == 0:
                    bp.set(x, top, z, TIL)
                    bp.set(x, top + 1, z, TIL_SL if z % 6 else "lightning_rod[facing=up,powered=false,"
                                                                  "waterlogged=false]")
                else:
                    bp.set(x, top, z, stair(TIL_ST, fc))
            elif ax == 21:
                bp.set(x, 24, z, BRK_W)
    # string courses on the outer faces of the aisles: the gallery floor and the terrace
    for z in range(-29, 40):
        for x in (-21, 21):
            bp.set(x, 15, z, POL)
            bp.set(x, 23, z, POL)
            bp.set(x, 0, z, PBB)
            bp.set(x, 1, z, PBB)
    # the columns: 7 x 7 shafts with a base, brass bands and a capital; their outer half rises as the pier of the
    # flying buttress over the terrace
    for c in COLS + [CROSS_S, CROSS_N]:
        for sx in (-1, 1):
            column(S, sx * 10, c, sx)
    carve_nave(S)


def column(S, cx, cz, sx):
    bp = S.bp
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            dx, dz = abs(x - cx), abs(z - cz)
            m = max(dx, dz)
            for y in range(0, SPRING):
                if m == 4:
                    if y <= 2:
                        bp.set(x, y, z, PBB if y < 2 else stair("polished_blackstone_brick_stairs",
                                                                 face_out(x - cx, z - cz)))
                    continue
                if m <= 3:
                    corner = dx == 3 and dz == 3
                    if y <= 2:
                        spec = PBB
                    elif y in (12, 20) or y == SPRING - 2:
                        spec = tarnish(x, y, z) if not corner else IRON
                    elif y == SPRING - 1:
                        spec = CHI if (dx + dz) % 2 else POL
                    elif corner:
                        spec = POL
                    elif dx == 3 or dz == 3:
                        spec = "polished_basalt[axis=y]" if (dx + dz) % 2 == 0 and min(dx, dz) in (1,) else TIL
                    else:
                        spec = TIL
                    bp.set(x, y, z, spec)
    # the pier over the terrace (outer side), up to the flyer
    for x in range(cx, cx + 4 * sx, sx):
        if abs(x) < 9:
            continue
        for z in range(cz - 1, cz + 2):
            for y in range(24, 32):
                bp.set(x, y, z, CHI if y == 31 else mas(x, y, z))


def face_out(dx, dz):
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def carve_nave(S):
    bp = S.bp
    for z in range(-50, 49):
        for x in range(-NHW, NHW + 1):
            top = vault_top(abs(x))
            y0 = 1 if z <= 40 else 22         # over the loft the nave goes on to the west front
            for y in range(y0, top + 1):
                bp.set(x, y, z, AIR)
        # the ribs of the vault: a chiseled arch over each column line
    for c in COLS + [CROSS_S, CROSS_N]:
        for x in range(-NHW, NHW + 1):
            t = vault_top(abs(x))
            bp.set(x, t, c, CHI if x % 3 else POL)
            if abs(x) >= NHW - 1:
                bp.set(x, t - 1, c, POL)
    for x in range(-NHW, NHW + 1):
        for z in range(-50, 49, 1):
            if x == 0:
                bp.set(x, vault_top(0), z, POL if z % 13 else tarnish(x, 40, z))   # the ridge rib
    # arcades between the columns, the aisles, the triforium galleries
    for sx in (-1, 1):
        for z in range(-29, 41):
            for ax in range(7, 14):
                x = sx * ax
                if in_column(x, z):
                    continue
                t = arcade_top(z)
                for y in range(1, t + 1):
                    bp.set(x, y, z, AIR)
                if bay_of(z):
                    for y in range(GAL, GAL + 6):
                        bp.set(x, y, z, AIR)
            for ax in range(14, 20):
                x = sx * ax
                if z > 39:
                    continue
                at = 9 + int(pointed_arch(3.5, 4)(ax - 16.5))
                for y in range(1, at + 1):
                    bp.set(x, y, z, AIR)
                for y in range(GAL, GAL + 6):
                    bp.set(x, y, z, AIR)
            if 30 <= z <= 40:
                for ax in range(8, 12):
                    for y in range(GAL, GAL + 6):
                        bp.set(sx * ax, y, z, AIR)
        # the gallery parapet toward the nave (between the columns) and its posts
        for z in range(-29, 41):
            if in_column(sx * 7, z) or not bay_of(z):
                continue
            b = bay_of(z)
            if z in b:
                bp.set(sx * 7, GAL, z, POL)
                bp.set(sx * 7, GAL + 1, z, POL_W)
                if b[0] < 30:
                    bp.set(sx * 7, GAL + 2, z, LANT)
            else:
                bp.set(sx * 7, GAL, z, POL_W)
        # clerestory windows over every bay, aisle and gallery windows on the outer wall
        for z0, z1 in BAYS:
            mid = (z0 + z1) // 2
            for z in range(mid - 1, mid + 2):
                for y in range(23, 28):
                    for ax in (7, 8):
                        bp.set(sx * ax, y, z, AIR)
                    bp.set(sx * 9, y, z, "cyan_stained_glass_pane" if y < 27 or z == mid else POL)
                bp.set(sx * 9, 22, z, POL)
            if z0 >= 30:
                continue
            for z in range(mid - 1, mid + 2):
                for y in range(3, 10):
                    bp.set(sx * 20, y, z, AIR)
                    bp.set(sx * 21, y, z, "gray_stained_glass_pane" if (y < 9 or z == mid) else BRK)
                for y in range(17, 21):
                    bp.set(sx * 20, y, z, AIR)
                    bp.set(sx * 21, y, z, "light_gray_stained_glass_pane")
            bp.set(sx * 21, 2, mid, CHI)
    # narthex and loft (between the towers)
    carve(S, -11, 1, 41, 11, 13, 48)
    carve(S, -11, GAL, 41, 11, GAL + 5, 48)
    for x in range(-11, 12):
        for z in range(41, 49):
            bp.set(x, 14, z, BRK)
            bp.set(x, 15, z, POL if (x + z) % 2 else TIL)
    for x in range(-6, 7):
        bp.set(x, GAL, 41, POL_W if x % 3 else POL)
    # the loft's railing posts carry lanterns
    for x in (-6, -3, 3, 6):
        bp.set(x, GAL + 1, 41, LANT)
    # the floor: a runner of polished deepslate on the axis, tiles in the aisles
    for z in range(-50, 49):
        for x in range(-19, 20):
            if bp.get(x, 1, z) != AIR:
                continue
            ax = abs(x)
            if ax <= 1:
                spec = POL
            elif ax <= NHW:
                spec = TIL if (x // 2 + z // 2) % 2 else BRK
            else:
                spec = pick([(TIL, 4), (CTIL, 1), (BRK, 2)], x, 0, z, 81)
            bp.set(x, 0, z, spec)


# ------------------------------------------------------------------ transepts
TR_VAULT = pointed_arch((TRZ1 - TRZ0) / 2.0 + 0.5, CROWN - SPRING)


def transepts(S):
    bp = S.bp
    zm = (TRZ0 + TRZ1) / 2.0
    for sx in (-1, 1):
        for ax in range(14, 31):
            x = sx * ax
            for z in range(TRZ0 - 2, TRZ1 + 3):
                dz = abs(z - zm)
                top = RIDGE - int(round(max(0.0, dz - 0.5) * (RIDGE - 29) / 7.5))
                for y in range(0, top + 1):
                    bp.set(x, y, z, mas(x, y, z))
                if dz > 0.5:
                    bp.set(x, top, z, stair(TIL_ST, "north" if z > zm else "south"))
                else:
                    bp.set(x, top, z, TIL)
        # interior
        for ax in range(7, TRX + 1):
            x = sx * ax
            for z in range(TRZ0, TRZ1 + 1):
                if in_column(x, z):
                    continue
                top = SPRING + int(TR_VAULT(z - zm))
                for y in range(1, top + 1):
                    bp.set(x, y, z, AIR)
        # the aisles open into the transept
        for ax in range(14, 20):
            for z in range(TRZ1 + 1, -23):
                for y in range(1, 13):
                    if bp.get(sx * ax, y, z) != AIR:
                        bp.set(sx * ax, y, z, AIR)
        # the balcony along the south side (feet 16) and its parapet
        for ax in range(14, TRX + 1):
            x = sx * ax
            for z in range(TRZ1 - 2, TRZ1 + 1):
                bp.set(x, 14, z, BRK)
                bp.set(x, 15, z, POL if (ax + z) % 2 else TIL)
                for y in range(GAL, GAL + 5):
                    bp.set(x, y, z, AIR)
            bp.set(x, GAL, TRZ1 - 3, POL_W if ax % 4 else POL)
            if ax % 4 == 0:
                bp.set(x, GAL + 1, TRZ1 - 3, LANT)
            # corbels under the balcony
            if ax % 3 == 0:
                bp.set(x, 13, TRZ1 - 2, stair(BRK_ST, "south", "top"))
        for z in range(TRZ1 - 2, TRZ1 + 1):
            for ax in range(14, 20):
                for y in range(GAL, GAL + 6):
                    bp.set(sx * ax, y, z, AIR)
        # the end door at the balcony level and a rose window above it
        for z in range(TRZ1 - 2, TRZ1 + 1):
            for ax in (29, 30):
                for y in range(GAL, GAL + 4):
                    bp.set(sx * ax, y, z, AIR)
                bp.set(sx * ax, 15, z, POL)
        rose(S, sx * 30, 25, zm, axis="x", r=5.2, inner=sx * 29)
        # tall lancets in the outer side walls of the arm
        for zz, zo in ((TRZ0 - 1, TRZ0 - 2), (TRZ1 + 1, TRZ1 + 2)):
            for ax in (23, 26):
                for y in range(4, 12):
                    bp.set(sx * ax, y, zz, AIR)
                    bp.set(sx * ax, y, zo, "gray_stained_glass_pane")
        # floor
        for ax in range(7, TRX + 1):
            for z in range(TRZ0, TRZ1 + 1):
                x = sx * ax
                if bp.get(x, 1, z) == AIR:
                    bp.set(x, 0, z, TIL if (ax + z) % 3 else POL)


def rose(S, x, yc, zc, axis, r, inner):
    """A rose window: twelve spokes and a ring of tracery, cyan and violet glass, in a wall plane."""
    bp = S.bp
    ri = int(math.ceil(r)) + 1
    for du in range(-ri, ri + 1):
        for dy in range(-ri, ri + 1):
            d = math.hypot(du, dy)
            if d > r + 0.3:
                continue
            ang = math.degrees(math.atan2(dy, du)) % 30
            if d < 1.2:
                spec = tarnish(x, yc, zc)
            elif abs(d - r * 0.55) < 0.5 or ang < 360 / (2 * math.pi * max(d, 1)) * 0.9:
                spec = POL
            elif d > r - 0.7:
                spec = CHI
            else:
                spec = "purple_stained_glass_pane" if d < r * 0.55 else "cyan_stained_glass_pane"
            if axis == "x":
                p, q = (x, yc + dy, int(round(zc + du))), (inner, yc + dy, int(round(zc + du)))
            else:
                p, q = (int(round(x + du)), yc + dy, zc), (int(round(x + du)), yc + dy, inner)
            bp.set(*p, spec)
            if bp.get(*q) is not None and "glass" in spec:
                bp.set(*q, AIR)


# ------------------------------------------------------------------ west front and towers
def gable_top(ax):
    return 46 - int(round(ax * 1.15))


def west_front(S):
    bp = S.bp
    for x in range(-11, 12):
        for z in range(49, 53):
            top = gable_top(abs(x))
            for y in range(0, top + 1):
                bp.set(x, y, z, mas(x, y, z))
            bp.set(x, top, z, stair(TIL_ST, "west" if x > 0 else "east") if x else TIL)
        for y in range(0, 4):
            bp.set(x, y, 53, PBB if y < 3 else stair("polished_blackstone_brick_stairs", "north"))
    # the narthex/loft block roof (continues the nave roof to the front)
    for z in range(41, 49):
        for x in range(-11, 12):
            ax = abs(x)
            top = roof_top(ax) if ax <= 9 else 23
            for y in range(GAL + 6, top + 1):
                if bp.get(x, y, z) is None or (ax > NHW and bp.get(x, y, z) == AIR) or y > vault_top(min(ax, 6)):
                    if ax <= NHW and y <= vault_top(ax):
                        continue
                    bp.set(x, y, z, mas(x, y, z))
            if ax <= 9:
                bp.set(x, top, z, stair(TIL_ST, "west" if x > 0 else "east") if x else TIL)
    # the great portal: a pointed opening 9 x 15 through the wall, archivolts round it, barred by its leaves
    arc = pointed_arch(4.5, 7)
    for x in range(-6, 7):
        h = 8 + int(arc(x)) if abs(x) <= 4 else -1
        ho = 8 + int(pointed_arch(6.5, 9)(x))
        for z in range(49, 53):
            if abs(x) <= 4:
                for y in range(1, h + 1):
                    bp.set(x, y, z, AIR)
            if z >= 51 and abs(x) <= 6:
                bp.set(x, ho, z, CHI if (x + z) % 2 else POL)
                if abs(x) > 4:
                    for y in range(1, ho):
                        if y % 4 == 0:
                            bp.set(x, y, z, POL)
    for x in range(-4, 5):
        h = 8 + int(arc(x))
        for y in range(1, h + 1):
            if y >= 12:
                spec = CHI if (x + y) % 3 else tarnish(x, y, 50)     # tympanum: a bell in brass relief
            elif x == 0:
                spec = "dark_oak_planks"
            else:
                spec = IRON if y in (3, 8) else "dark_oak_planks"
            bp.set(x, y, 50, spec)
    for x in (-1, 1):
        bp.set(x, 13, 51, BRASS)
        bp.set(x, 14, 51, BRASS)
    bp.set(0, 15, 51, BRASS)
    bp.set(0, 12, 51, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.door(0, 1, 50, "south", wood="iron")                      # the wicket: opens from inside only
    bp.set(1, 2, 49, "lever[face=wall,facing=north,powered=false]")
    bp.set(-1, 3, 49, "wall_torch[facing=north]")
    # the rose window over the portal (into the nave)
    rose(S, 0, 29, 52, axis="z", r=6.3, inner=49)
    for z in (50, 51):
        for x in range(-5, 6):
            for y in range(23, 36):
                if math.hypot(x, y - 29) < 6.3 and bp.get(x, y, z) is not None and "glass" not in (bp.get(x, y, z)
                                                                                                   or ""):
                    if math.hypot(x, y - 29) < 5.5:
                        bp.set(x, y, z, AIR)
    # relief on the front: buttresses flanking the portal, a projecting archivolt, the gallery of the choristers
    # (a band of statues in niches) between two string courses, under the rose
    for sx in (-1, 1):
        for x in (sx * 7, sx * 8):
            for z in (53, 54):
                top = 17 if z == 53 else 11
                for y in range(0, top + 1):
                    bp.set(x, y, z, PBB if y < 3 else (POL if y % 5 == 0 else BRK))
                bp.set(x, top + 1, z, stair(POL_ST, "north" if z == 54 else ("east" if sx > 0 else "west")))
    ring = pointed_arch(6.5, 9)
    for x in range(-6, 7):
        ho = 8 + int(ring(x))
        bp.set(x, ho, 53, CHI if x % 2 else POL)
        bp.set(x, ho + 1, 53, stair(POL_ST, "south", "top") if abs(x) < 6 else POL)
    for x in range(-11, 12):
        if abs(x) <= 6:
            continue
        bp.set(x, 18, 53, stair(TIL_ST, "south", "top"))
    for x in range(-11, 12):
        bp.set(x, 22, 53, stair(TIL_ST, "south", "top"))
    for x in range(-10, 11, 2):
        y0 = 19
        if abs(x) <= 6 and 8 + int(ring(x)) >= y0 - 1:
            continue
        bp.set(x, y0, 53, "polished_deepslate_wall")
        bp.set(x, y0 + 1, 53, "polished_deepslate_wall")
        bp.set(x, y0 + 2, 53, "chiseled_polished_blackstone")
    for x in range(-5, 6):
        if 8 + int(ring(x)) < 18:
            bp.set(x, 18, 53, stair(TIL_ST, "south", "top"))
    # pinnacles on the gable
    for x in (-11, 11):
        pinnacle(S, x, gable_top(11) + 1, 52, 7)
    pinnacle(S, 0, gable_top(0) + 1, 51, 5)
    # wall passages to the two tower lodges
    for sx in (-1, 1):
        carve(S, sx * 9, 1, 49, sx * 12, 4, 51)
        carve(S, sx * 9, 1, 48, sx * 11, 4, 48)
        bp.set(sx * 10, 4, 50, LANT_H)


def pinnacle(S, x, y, z, h):
    bp = S.bp
    for k in range(h):
        if k < h - 3:
            bp.set(x, y + k, z, POL if k % 3 else CHI)
        else:
            bp.set(x, y + k, z, POL_W)
    bp.set(x, y + h, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def write_newel(S, cells, core, f0, cap=None, lamps=True):
    """Blocks of one newel part (caldera_ringwall.newel cells): air over every cell, treads, solid under."""
    bp = S.bp
    top = max(f for f, _, _ in cells.values())
    for (x, z), (f, fc, _) in cells.items():
        for y in range(f, f + 4):
            bp.set(x, y, z, AIR)
    for (x, z), (f, fc, _) in cells.items():
        if fc:
            bp.set(x, f - 1, z, stair(BRK_ST, fc))
        else:
            bp.set(x, f - 1, z, POL if hash01(x, z, 7) < 0.7 else TIL)
        bp.set(x, f - 2, z, BRK)
    cx0, cz0, cx1, cz1 = core
    ctop = cap if cap is not None else top + 3
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(f0 - 1, ctop + 1):
                edge = x in (cx0, cx1) and z in (cz0, cz1)
                bp.set(x, y, z, POL if edge else BRK)
    if lamps:
        seen = set()
        for (x, z), (f, fc, i) in cells.items():
            if fc is None and (f, i) not in seen and x in (cx0 - 1, cx1 + 1) and z in (cz0 - 1, cz1 + 1):
                seen.add((f, i))
                hx = cx0 if x < cx0 else cx1
                hz = cz0 if z < cz0 else cz1
                if f + 2 <= ctop:
                    bp.set(hx, f + 2, hz, CHI)
                    bp.set(x, f + 3, z, AIR)
                    dx, dz = x - hx, z - hz
                    bp.set(hx + dx, f + 2, hz + dz, AIR)


def tower(S, sx):
    """A west tower: 13 x 13, clasping buttresses, a newel stair (lodge -> loft -> top room), belfry crown."""
    bp = S.bp
    x0, x1 = (-24, -12) if sx < 0 else (12, 24)
    for x in range(x0 - 1, x1 + 2):
        for z in range(40, 54):
            edge_x = x in (x0 - 1, x1 + 1)
            edge_z = z == 53
            if edge_x or edge_z:
                # clasping buttresses at the corners only (§4), stepped back as they rise
                cx = x0 - 1 if x == x0 - 1 else x1 + 1
                near_corner = (z >= 50 or z <= 42) if edge_x else (x <= x0 + 2 or x >= x1 - 2)
                if not near_corner:
                    continue
                hb = 36 if (edge_x and edge_z) else 30
                for y in range(0, hb):
                    bp.set(x, y, z, PBB if y < 3 else mas(x, y, z))
                bp.set(x, hb, z, stair(BRK_ST, "north" if edge_z else ("east" if x == x0 - 1 else "west")))
                continue
            for y in range(0, TOWER_TOP + 1):
                spec = mas(x, y, z)
                if y in (15, 29, 43) and (x in (x0, x1) or z in (40, 52)):
                    spec = POL
                bp.set(x, y, z, spec)
    xi0, xi1 = x0 + 1, x1 - 1
    # the newel: SW tower clockwise from its SE corner, SE tower counter-clockwise from its SW corner
    if sx < 0:
        c1, f1, start1, cw = 2, F, 2, True
    else:
        c1, f1, start1, cw = 3, F, 3, False
    cells1, core, c, f = newel(xi0, 41, 5, F, [5, 5, 5], start1, cw)
    cells2, core2, c2, f2 = newel(xi0, 41, 5, GAL, [5, 5, 5], c, cw)
    write_newel(S, cells1, core, F, cap=BELL_F - 2)
    write_newel(S, cells2, core2, GAL, cap=BELL_F - 2)
    S.tower_cells = getattr(S, "tower_cells", {})
    S.tower_cells[sx] = (cells1, cells2)
    # the outer door of the SW tower (from the forecourt) and the passages to the narthex and the loft
    if sx < 0:
        bp.door(-14, 1, 52, "south", wood="dark_oak")
        bp.set(-14, 0, 53, POL)
        for x in (-15, -13):
            bp.set(x, 3, 53, "wall_torch[facing=south]")
    for z in range(49, 52):
        for y in range(1, 5):
            bp.set(sx * 12, y, z, AIR)
    for z in range(41, 44):
        for y in range(GAL, GAL + 4):
            bp.set(sx * 12, y, z, AIR)
        bp.set(sx * 12, GAL - 1, z, POL)
    # the top room (feet 31): floor over the stair except the hole of the last flight
    last = {k for k, v in cells2.items() if v[0] >= BELL_F - 4}
    for x in range(xi0, xi1 + 1):
        for z in range(41, 52):
            for y in range(BELL_F, 43):
                bp.set(x, y, z, AIR)
            if (x, z) in last:
                continue
            bp.set(x, BELL_F - 1, z, POL if (x + z) % 2 else TIL)
    for (x, z) in last:
        if cells2[(x, z)][0] < BELL_F:
            for dx, dz in DIRS.values():
                n = (x + dx, z + dz)
                if xi0 <= n[0] <= xi1 and 41 <= n[1] <= 51 and n not in last:
                    bp.set(n[0], BELL_F, n[1], POL_W)
    for x in range(xi0, xi1 + 1):
        for z in range(41, 52):
            bp.set(x, 43, z, BRK)
            bp.set(x, 44, z, TIL)
    # belfry openings on all four faces: tall pointed lancets with a low parapet (vistas, §7)
    arc = pointed_arch(2.5, 3)
    xm = (x0 + x1) // 2
    for u in range(-2, 3):
        h = 37 + int(arc(u))
        for y in range(BELL_F, h + 1):
            for (x, z) in ((xm + u, 40), (xm + u, 52), (x0, 46 + u), (x1, 46 + u)):
                bp.set(x, y, z, AIR if y > BELL_F else BRK_W)
    # the crown: parapet with crenels, corner pinnacles
    for x in range(x0, x1 + 1):
        for z in range(40, 53):
            if x in (x0, x1) or z in (40, 52):
                bp.set(x, 45, z, BRK)
                if (x + z) % 2 == 0:
                    bp.set(x, 46, z, BRK_W)
    for (x, z) in ((x0, 40), (x1, 40), (x0, 52), (x1, 52)):
        for y in range(45, 49):
            bp.set(x, y, z, POL if y < 48 else CHI)
        pinnacle(S, x, 49, z, 3)
    pinnacle(S, xm, 45, 46, 4)


def bell_chamber(S):
    """Top of the SW tower: the cracked bronze bell under a beam, a fallen shard, a view up the nave."""
    bp = S.bp
    cx, cz = -16, 46
    for x in range(-23, -12):
        bp.set(x, 42, cz, "dark_oak_log[axis=x]")
    bp.set(cx, 41, cz, CHAIN)
    ytop, ybot = 40, 34
    for y in range(ybot, ytop + 1):
        t = (ytop - y) / float(ytop - ybot)
        r = 1.5 + 2.0 * t ** 1.4 + (0.5 if y == ybot else 0.0)
        ri = int(math.ceil(r)) + 1
        for x in range(cx - ri, cx + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                d = math.hypot(x - cx, z - cz)
                if d > r + 0.35:
                    continue
                if d < r - 0.75 and y < ytop:
                    bp.set(x, y, z, AIR)
                    continue
                # the crack: a jagged gap up the south side
                crack = z - cz >= 2 and abs((x - cx) - int(round(math.sin(y * 1.7) * 0.8))) == 0 and y < ytop - 1
                if crack:
                    bp.set(x, y, z, AIR)
                    continue
                h = hash3(x, y, z, 91)
                spec = ("waxed_exposed_copper" if h < 0.55 else "waxed_copper_block" if h < 0.8 else
                        "waxed_weathered_copper")
                if y == ybot + 1:
                    spec = "waxed_cut_copper" if h < 0.7 else "waxed_exposed_cut_copper"
                bp.set(x, y, z, spec)
    for y in range(36, 40):
        bp.set(cx, y, cz, CHAIN)
    bp.set(cx, 35, cz, IRON)                                   # the clapper
    # a shard broken from the lip lies on the floor
    for (x, z) in ((-14, 50), (-13, 50), (-14, 51)):
        bp.set(x, BELL_F, z, "waxed_exposed_cut_copper_slab[type=bottom,waterlogged=false]")
    bp.chest(-22, BELL_F, 50, "east", loot=LOOT + "ec_belfry")
    bp.set(-13, BELL_F, 42, "bell[attachment=floor,facing=west,powered=false]")
    bp.spawner(-18, BELL_F, 50, MOB_BANSHEE)
    for (x, z) in ((-21, 51), (-13, 44)):
        bp.set(x, BELL_F, z, LANT)


def bellows_loft(S):
    """Top of the SE tower: the organ's giant bellows, a wind trunk, gauges."""
    bp = S.bp
    for x in range(15, 21):
        for z in range(44, 49):
            for y in range(BELL_F, BELL_F + 4):
                d = y - BELL_F
                if x - 15 <= 5 - d:
                    spec = LEATHER if 0 < d < 3 else MAHOGANY
                    bp.set(x, y, z, spec)
    for z in range(44, 49):
        if any("stairs" in (bp.get(21, y, z) or "") for y in range(BELL_F - 3, BELL_F)):
            continue                                    # keep the head-room over the newel stair
        bp.set(21, BELL_F, z, IRON)
        bp.set(21, BELL_F + 1, z, IRON)
    for y in range(BELL_F, 43):
        bp.set(22, y, 46, PIPES if y < 42 else COPPER)
    for (x, z) in ((14, 42), (22, 42)):
        bp.set(x, BELL_F, z, GEAR)
        bp.set(x, BELL_F + 1, z, GAUGE)
    bp.set(18, BELL_F, 42, "brasshaven:valve_wheel")
    bp.chest(22, BELL_F, 50, "west", loot=LOOT + "ec_bellows")
    bp.barrel(21, BELL_F, 51, "up")
    for (x, z) in ((14, 51), (21, 42)):
        bp.set(x, BELL_F, z, LANT)


# ------------------------------------------------------------------ flying buttresses
def flyer(S, xa, ya, xb, yb, z0, z1, top_spec=None):
    """A flying arch between two points in the x-y plane (z0..z1 thick): straight sloping top, segmental underside
    (thick at the haunches, 1.5 at mid-span). Cells are only written where nothing solid is built yet."""
    bp = S.bp
    n = abs(xb - xa)
    s = 1 if xb > xa else -1
    for k in range(n + 1):
        x = xa + s * k
        t = k / float(n)
        top = ya + (yb - ya) * t
        bot = top - 1.6 - 5.0 * (1 - 4 * t * (1 - t)) ** 2
        for y in range(int(math.floor(bot)), int(round(top)) + 1):
            for z in range(z0, z1 + 1):
                b = bp.get(x, y, z)
                if b is None or b == AIR or (x, y, z) in S.lining:
                    bp.set(x, y, z, top_spec if (y == int(round(top)) and top_spec) else mas(x, y, z))
                    S.lining.discard((x, y, z))


def buttresses(S):
    bp = S.bp
    for c in COLS:
        for sx in (-1, 1):
            # the outer pier
            for ax in range(24, 29):
                for z in range(c - 2, c + 3):
                    inner = 25 <= ax <= 27 and c - 1 <= z <= c + 1
                    hmax = 24 if inner else 3
                    for y in range(0, hmax + 1):
                        bp.set(sx * ax, y, z, PBB if y < 3 else mas(sx * ax, y, z))
                    if not inner:
                        bp.set(sx * ax, 3, z, stair("polished_blackstone_brick_stairs", "west" if
                                                     (ax == 28) == (sx > 0) else "east") if ax in (24, 28) else PBB)
            for y in range(25, 29):
                for ax in range(25, 28):
                    for z in range(c - 1, c + 2):
                        if y == 28 and (ax != 26 or z != c):
                            continue
                        bp.set(sx * ax, y, z, CHI if y == 25 else POL)
            for y in range(29, 32):
                bp.set(sx * 26, y, c, POL_W)
            bp.set(sx * 26, 32, c, "lightning_rod[facing=up,powered=false,waterlogged=false]")
            bp.set(sx * 28, 10, c, "soul_wall_torch[facing=%s]" % ("east" if sx > 0 else "west"))
            # flyer 1: clerestory pier -> outer pier; flyer 2: outer pier -> the cave wall
            flyer(S, sx * 13, 31, sx * 25, 24, c - 1, c + 1, top_spec=POL)
            flyer(S, sx * 27, 23, sx * 44, 27, c - 1, c + 1, top_spec=POL)


def apse_buttresses(S):
    """Radiating piers round the apse and the choir, each braced by a flyer into the cave wall behind."""
    bp = S.bp
    for b in (-90, -60, -30, 30, 60, 90):
        t = math.radians(b)
        ux, uz = math.sin(t), -math.cos(t)
        for r in range(21, 25):
            for w in (-1, 0, 1):
                x = int(round(ux * r - uz * w))
                z = int(round(AZ + uz * r + ux * w))
                for y in range(0, 31):
                    bp.set(x, y, z, PBB if y < 3 else mas(x, y, z))
        x = int(round(ux * 23))
        z = int(round(AZ + uz * 23))
        pinnacle(S, x, 31, z, 4)
        # the flyer runs outward along the bearing; built cell by cell in its own plane
        for k in range(0, 14):
            r = 24 + k
            t2 = k / 13.0
            top = 29 + 6 * t2
            bot = top - 1.6 - 5.0 * (1 - 4 * t2 * (1 - t2)) ** 2
            for w in (-1, 0, 1):
                x = int(round(ux * r - uz * w))
                z = int(round(AZ + uz * r + ux * w))
                for y in range(int(math.floor(bot)), int(round(top)) + 1):
                    cur = bp.get(x, y, z)
                    if cur is None or cur == AIR or (x, y, z) in S.lining:
                        bp.set(x, y, z, POL if y == int(round(top)) else mas(x, y, z))
                        S.lining.discard((x, y, z))


# ------------------------------------------------------------------ side chapels
def chapels(S):
    bp = S.bp
    for sx in (-1, 1):
        for i, (z0, z1) in enumerate(CHAPELS):
            for ax in range(22, 28):
                for z in range(z0 - 1, z1 + 2):
                    x = sx * ax
                    for y in range(0, 12):
                        bp.set(x, y, z, PBB if y < 2 and ax >= 26 else mas(x, y, z))
                    # a pent roof falling outward
                    rt = 12 - (ax - 22) // 2
                    for y in range(12, rt + 1):
                        bp.set(x, y, z, mas(x, y, z))
                    bp.set(x, rt + 1, z, stair(TIL_ST, "west" if sx > 0 else "east"))
            carve(S, sx * 22, 1, z0, sx * 25, 9, z1)
            for z in range(z0, z1 + 1):
                for ax in range(22, 26):
                    bp.set(sx * ax, 0, z, POL if (ax + z) % 2 else TIL)
                bp.set(sx * 25, 10, z, POL)
            # the opening from the aisle: pointed, 6 wide
            mid = (z0 + z1) / 2.0
            arc = pointed_arch(3.0, 3)
            for z in range(z0 + 1, z1):
                h = 5 + int(arc(z - mid))
                for y in range(1, h + 1):
                    for ax in (20, 21):
                        bp.set(sx * ax, y, z, AIR)
            chapel_furnish(S, sx, i, z0, z1)


def chapel_furnish(S, sx, i, z0, z1):
    bp = S.bp
    xa = sx * 25                       # the altar against the outer wall
    zm = (z0 + z1) // 2
    face = "west" if sx > 0 else "east"
    for z in range(zm - 1, zm + 2):
        bp.set(xa, 1, z, CHI if z == zm else POL)
        bp.set(xa, 2, z, slab(POL_SL) if z != zm else POL)      # a full block in the middle holds the candles
    bp.set(sx * 26, 5, zm, "cyan_stained_glass_pane")
    bp.set(sx * 26, 6, zm, "cyan_stained_glass_pane")
    bp.set(sx * 26, 7, zm, "cyan_stained_glass_pane")
    kind = (i, sx)
    if kind == (0, 1):        # the Hush: wool, unlit candles, a figure with a finger to its lips
        for z in range(z0, z1 + 1):
            for ax in range(22, 25):
                bp.set(sx * ax, 1, z, "gray_carpet")
        bp.set(xa, 3, zm, "candle[candles=4,lit=false,waterlogged=false]")
        chorister(S, sx * 22, z0, face)
        bp.barrel(sx * 22, 1, z1, "up")
    elif kind == (1, 1):      # the Tuning Forks: rows of rods, amethyst and note blocks
        for z in range(z0, z1 + 1, 2):
            bp.set(sx * 23, 1, z, "note_block[instrument=bell,note=%d,powered=false]" % (z % 24))
            bp.set(sx * 23, 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        bp.set(xa, 3, zm, "amethyst_cluster[facing=up,waterlogged=false]")
        bp.set(xa, 3, zm - 1, "small_amethyst_bud[facing=up,waterlogged=false]")
        bp.chest(sx * 22, 1, z1, face, loot=LOOT + "ec_chapel")
    elif kind == (2, 1):      # the Drowned Hymn: a font, sea lanterns under water
        bp.set(sx * 23, 1, zm, "water_cauldron[level=3]")
        bp.set(sx * 23, 1, zm - 1, POL_W)
        bp.set(sx * 23, 2, zm - 1, SOUL)
        bp.set(xa, 3, zm, "candle[candles=2,lit=true,waterlogged=false]")
        bp.spawner(sx * 22, 1, z0, MOB_MONK)
    elif kind == (0, -1):     # the Bells: a row of small bells hung from the vault
        for z in range(z0 + 1, z1, 2):
            bp.set(sx * 23, 9, z, CHAIN)
            bp.set(sx * 23, 8, z, CHAIN)
            bp.set(sx * 23, 7, z, "bell[attachment=ceiling,facing=north,powered=false]")
        bp.chest(sx * 22, 1, z1, face, loot=LOOT + "ec_chapel")
    elif kind == (1, -1):     # the Echoes: sculk sensors on plinths (decoration only)
        for z in (z0, zm, z1):
            bp.set(sx * 24, 1, z, CHI)
            bp.set(sx * 24, 2, z, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
        bp.set(xa, 3, zm, "calibrated_sculk_sensor[facing=%s,power=0,sculk_sensor_phase=inactive,"
                          "waterlogged=false]" % face)
        for z in range(z0, z1 + 1):
            if hash01(sx * 23, z, 5) < 0.5:
                bp.set(sx * 23, 0, z, "sculk")
        bp.spawner(sx * 22, 1, zm, MOB_MONK)
    else:                     # Saint Cecilia: a jukebox and the music stands of the choir
        bp.set(sx * 23, 1, zm, "jukebox[has_record=false]")
        for z in (z0, z1):
            bp.set(sx * 23, 1, z, "lectern[facing=%s,has_book=false,powered=false]" % face)
        bp.set(xa, 3, zm, "candle[candles=3,lit=true,waterlogged=false]")
        bp.chest(sx * 22, 1, z0, face, loot=LOOT + "ec_chapel")
    for y in range(6, 10):
        bp.set(sx * 24, y, zm, CHAIN)
    bp.set(sx * 24, 5, zm, LANT_H)


# ------------------------------------------------------------------ choir, apse, organ
def in_chevet(x, z, r_extra=0.0):
    """Inside the choir rectangle or the apse circle (inner faces)."""
    if ZC1 <= z <= ZC0 and abs(x) <= AR + r_extra:
        return True
    return z < ZC1 + 1 and math.hypot(x, z - AZ) <= AR + r_extra + 0.3


def chevet(S):
    """Choir walls and apse ring (y 0..34), the raised floor over the crypt, the screen with its grille."""
    bp = S.bp
    for x in range(-22, 23):
        for z in range(-83, -49):
            ins = in_chevet(x, z)
            wall = in_chevet(x, z, 2.2) and not ins
            if not (ins or wall):
                continue
            if wall:
                for y in range(0, 35):
                    bp.set(x, y, z, PBB if y < 3 else mas(x, y, z))
                bp.set(x, 35, z, BRK_W if (x + z) % 2 else BRK)
            else:
                for y in range(-11, 9):
                    bp.set(x, y, z, mas(x, y, z))
                for y in range(CHF, 43):
                    bp.set(x, y, z, AIR)
                bp.set(x, 8, z, arena_floor(x, z))
    # the south wall of the choir (z -50..-51) beside the stair, the screen across the stair
    for x in range(-20, 21):
        for z in (-50, -51):
            if abs(x) <= NHW:
                continue
            for y in range(0, 35 if abs(x) > 13 else 29):
                if bp.get(x, y, z) in (None, AIR) or abs(x) > 13 or True:
                    bp.set(x, y, z, mas(x, y, z))
    for x in range(-NHW, NHW + 1):
        for y in range(CHF, vault_top(abs(x)) + 1):
            if y <= CHF + 7:
                if abs(x) % 3 == 0:
                    spec = POL
                elif y == CHF + 7:
                    spec = CHI
                else:
                    spec = "iron_bars"
            else:
                vt = vault_top(abs(x))
                if y == CHF + 8 or y >= vt - 1:
                    spec = POL
                elif abs(x) % 3 == 0 or (y - CHF) % 7 == 1:
                    spec = CHI if (y - CHF) % 7 == 1 and abs(x) % 3 == 0 else POL
                else:
                    spec = "iron_bars"                      # open tracery: the pipes show from the nave
            bp.set(x, y, -51, spec)
        for y in range(0, CHF):
            bp.set(x, y, -51, mas(x, y, -51))
    for x in (-1, 1):
        for y in range(CHF, CHF + 3):
            bp.set(x, y, -51, POL)                      # solid jambs: the lever needs a wall to hang on
    bp.door(0, CHF, -51, "north", wood="iron")
    bp.set(1, CHF + 1, -52, "lever[face=wall,facing=north,powered=false]")
    bp.set(-1, CHF + 1, -52, AIR)
    # the choir stair: eight steps from the crossing (feet 2..9)
    for k in range(1, 9):
        z = -42 - k
        for x in range(-NHW, NHW + 1):
            bp.set(x, F + k - 1, z, stair(POL_ST if abs(x) <= 1 else BRK_ST, "north"))
            for y in range(0, F + k - 1):
                bp.set(x, y, z, BRK)
            for y in range(F + k, F + k + 4):
                if bp.get(x, y, z) != AIR:
                    bp.set(x, y, z, AIR)
    # the broken vault: three transverse ribs still span the choir, rubble in the corners
    for zr in (-54, -58):
        arc = pointed_arch(AR + 1.5, 12)
        for x in range(-AR - 1, AR + 2):
            y = 26 + int(arc(x))
            for dy in (0, 1):
                bp.set(x, y + dy, zr, POL if dy else (CHI if x % 4 == 0 else BRK))
            if abs(x) < 4:
                bp.set(x, y + 2, zr, tarnish(x, y, zr))
    for (x, z) in ((-17, -53), (16, -59), (-15, -59)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if hash3(x + dx, 0, z + dz, 5) < 0.7 and in_chevet(x + dx, z + dz):
                    bp.set(x + dx, CHF, z + dz, COB if hash3(x, dx, dz, 6) < 0.6 else slab(TIL_SL))
    # tall windows in the choir side walls
    for sx in (-1, 1):
        for z in (-55, -56, -57):
            for y in range(12, 27):
                bp.set(sx * 19, y, z, AIR)
                bp.set(sx * 20, y, z, "gray_stained_glass_pane" if z == -56 or y < 25 else POL)
    # crown of the apse wall: pinnacles every 30 degrees (the bays of the organ)
    for b in range(-90, 91, 30):
        t = math.radians(b)
        x = int(round(math.sin(t) * 19.5))
        z = int(round(AZ - math.cos(t) * 19.5))
        if z <= AZ:
            pinnacle(S, x, 36, z, 4)
    for (x, z) in ((-19, -51), (19, -51), (-19, -60), (19, -60)):
        pinnacle(S, x, 36, z, 4)


def arena_floor(x, z):
    """Ripples of sound round the organ console: rings of polished deepslate and tarnished brass."""
    r = math.hypot(x, z - AZ)
    if r > AR - 0.5:
        return PBB
    if abs(r - 6) < 0.5 or abs(r - 11) < 0.5:
        return BRASS if int(math.degrees(math.atan2(x, z - AZ))) % 20 < 12 else IRON
    return POL if int(r) % 3 == 0 else TIL


def organ(S):
    """The pipe organ: a wooden plinth round the back of the apse, two ranks of tarnished brass pipes rising behind
    the console; the tallest reach 60 blocks above the floor, into the cavern roof."""
    bp = S.bp
    # the plinth (feet of the pipes): r 12.5..18.5, bearings -95..95 (0 = north, the back of the apse)
    for x in range(-AR - 1, AR + 2):
        for z in range(AZ - AR - 1, AZ + 6):
            r = math.hypot(x, z - AZ)
            b = math.degrees(math.atan2(x, -(z - AZ)))
            if not (12.5 <= r <= AR + 0.4 and abs(b) <= 95):
                continue
            for y in range(CHF, 13):
                if y == 12:
                    spec = MAHOGANY_SLAB + "[type=bottom,waterlogged=false]" if r < 13.5 else MAHOGANY
                elif y == CHF and r < 13.5:
                    spec = tarnish(x, y, z)
                else:
                    spec = MAHOGANY if (int(b) // 6) % 3 else "dark_oak_planks"
                bp.set(x, y, z, spec)
    pipes = []
    for k in range(9):                                  # back rank: nine great pipes with daylight between them
        b = -72 + 18 * k
        h = 13 + 56 * math.cos(math.radians(b)) ** 1.25 - (4 if k % 2 else 0)
        pipes.append((b, 16.2, 1.8, int(round(h)), k % 2))
    for k in range(8):                                  # front rank: shorter, slimmer, in the gaps
        b = -63 + 18 * k
        h = 13 + 28 * math.cos(math.radians(b)) ** 1.1 - (2 if k % 2 else 0)
        pipes.append((b, 13.2, 1.15, int(round(h)), 1 - k % 2))
    for b, r, pr, top, alt in pipes:
        t = math.radians(b)
        px, pz = math.sin(t) * r, AZ - math.cos(t) * r
        ix, iz = -math.sin(t), math.cos(t)              # toward the arena
        pipe(S, px, pz, 13, top, pr, ix, iz, alt)
    # small flue pipes along the front edge of the plinth
    for b in range(-84, 85, 6):
        t = math.radians(b)
        x = int(round(math.sin(t) * 12.6))
        z = int(round(AZ - math.cos(t) * 12.6))
        hh = 2 + int(3 * math.cos(t) ** 2) + (b // 6) % 2
        for y in range(13, 13 + hh):
            bp.set(x, y, z, tarnish(x, y, z))
        bp.set(x, 13 + hh, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the console on its dais, the bench, two candelabra
    for x in range(-4, 5):
        for z in range(-72, -66):
            bp.set(x, 8, z, PBB if abs(x) == 4 or z in (-72, -67) else POL)
    for x in range(-3, 4):
        bp.set(x, CHF, -71, MAHOGANY)
        bp.set(x, CHF + 1, -71, MAHOGANY)
        bp.set(x, CHF + 2, -71, MAHOGANY_SLAB + "[type=bottom,waterlogged=false]")
        bp.set(x, CHF, -70, MAHOGANY)
        bp.set(x, CHF + 1, -70, "smooth_quartz_slab[type=bottom,waterlogged=false]" if x % 2 else
               "polished_blackstone_slab[type=bottom,waterlogged=false]")
    for x in (-3, -1, 1, 3):
        bp.set(x, CHF + 2, -70, "lever[face=floor,facing=south,powered=false]")
    bp.set(0, CHF + 3, -71, "lectern[facing=south,has_book=false,powered=false]")
    for x in range(-2, 3):
        bp.set(x, CHF, -68, stair("dark_oak_stairs", "north") if abs(x) < 2 else
               stair("dark_oak_stairs", "east" if x < 0 else "west"))
    for x in (-6, 6):
        bp.set(x, CHF, -69, PBB)
        bp.set(x, CHF + 1, -69, IRON_WALL)
        bp.set(x, CHF + 2, -69, IRON_WALL)
        bp.set(x, CHF + 3, -69, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # braziers round the arena edge
    for b in (-125, -150, 125, 150):
        t = math.radians(b)
        x = int(round(math.sin(t) * 15.5))
        z = int(round(AZ - math.cos(t) * 15.5))
        if in_chevet(x, z):
            bp.set(x, CHF, z, PBB)
            bp.set(x, CHF + 1, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.boss_seal(0, 8, AZ, BOSS, 15)


def pipe(S, px, pz, y0, top, pr, ix, iz, alt=0):
    bp = S.bp
    ri = int(math.ceil(pr)) + 1
    cx, cz = int(round(px)), int(round(pz))
    for y in range(y0, top + 1):
        r = pr - (1.0 if y < y0 + 2 else 0.0)
        for x in range(cx - ri, cx + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                dx, dz = x - px, z - pz
                d = math.hypot(dx, dz)
                if d > r + 0.4:
                    continue
                front = (dx * ix + dz * iz) > r - 0.9 and abs(dx * iz - dz * ix) < max(0.8, r * 0.45)
                if front and y == y0 + 4:
                    spec = "shroomlight"                        # a warm glow deep in the mouth
                elif front and y0 + 3 <= y <= y0 + 5:
                    spec = PB                                   # the mouth
                elif front and y == y0 + 6:
                    spec = IRON                                 # the upper lip
                elif (y - y0) % 14 == 13 or y == top:
                    spec = IRON
                elif y < y0 + 9:
                    spec = tarnish(x, y, z)                     # verdigris only round the damp feet
                elif (y - y0) % 14 in (6, 7):
                    spec = COPPER                               # a copper collar every fourteen blocks
                else:
                    spec = COPPER if alt and (x + z) % 5 == 0 else BRASS
                bp.set(x, y, z, spec)
                S.lining.discard((x, y, z))


def reliquary(S):
    """The axial chapel behind the apse: the sealed reliquary (feet 9) under a cone roof."""
    bp = S.bp
    cz = -87
    for x in range(-8, 9):
        for z in range(cz - 8, cz + 8):
            d = max(abs(x), abs(z - cz)) * 0.8 + min(abs(x), abs(z - cz)) * 0.45
            if d > 6.6:
                continue
            for y in range(0, 23):
                if d <= 5.4 and CHF <= y <= 18:
                    bp.set(x, y, z, AIR)
                elif d <= 5.4 and y == CHF - 1:
                    bp.set(x, y, z, PB if (x + z) % 2 else PBB)
                else:
                    bp.set(x, y, z, PBB if y < 3 else mas(x, y, z))
            rt = 23 + int(max(0, 6.6 - d) * 1.2)
            for y in range(23, rt + 1):
                bp.set(x, y, z, TIL)
    # passage from the arena under the central pipes, barred until the boss falls
    for z in range(-80, cz - 4, -1):
        for x in range(-1, 2):
            for y in range(CHF, CHF + 3):
                bp.set(x, y, z, AIR)
            bp.set(x, CHF - 1, z, PB)
        for x in (-2, 2):
            for y in range(CHF, CHF + 4):
                if bp.get(x, y, z) in (None, AIR):
                    bp.set(x, y, z, PBB)
        for x in range(-1, 2):
            if bp.get(x, CHF + 3, z) in (None, AIR):
                bp.set(x, CHF + 3, z, PBB)
    for z in range(-72, -81, -1):
        for x in range(-1, 2):
            for y in range(CHF, CHF + 3):
                bp.set(x, y, z, AIR)
    for x in range(-1, 2):
        for y in range(CHF, CHF + 3):
            bp.set(x, y, -73, MOD["vault_bars"])
    for z in range(-81, -74, -1):
        bp.set(0, CHF + 3, z, CHI)
    for (x, z, fc) in ((-4, cz, "east"), (4, cz, "west"), (0, cz - 4, "south")):
        bp.chest(x, CHF, z, fc, loot=LOOT + "ec_reliquary")
    for (x, z) in ((-3, cz - 3), (3, cz - 3)):
        bp.set(x, CHF, z, "gold_block")
        bp.set(x, CHF + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(0, CHF, cz - 2, "chiseled_quartz_block")
    bp.set(0, CHF + 1, cz - 2, "bell[attachment=floor,facing=south,powered=false]")
    for (x, z) in ((-3, cz + 2), (3, cz + 2)):
        bp.set(x, CHF, z, "candle[candles=4,lit=true,waterlogged=false]")
    for (x, z) in ((0, cz), (-3, cz - 1), (3, cz - 1)):
        bp.set(x, 18, z, CHAIN)
        bp.set(x, 17, z, SOUL_H)


# ------------------------------------------------------------------ crypt and pipe-shaft lift
def crypt_ceiling(x, z):
    """Top air y of the main crypt: groin vaults between 3 x 3 columns on a 6 x 8 grid."""
    fx = ((x + 3) % 6) / 6.0
    fz = ((z - AZ + 4) % 8) / 8.0
    px = math.sin(math.pi * fx)
    pz = math.sin(math.pi * fz)
    return -3 + int(round(5 * max(px, pz)))


def crypt_column(x, z):
    return (x + 3) % 6 in (5, 0, 1) and (z - AZ + 4) % 8 in (7, 0, 1) and not (abs(x) <= 2 and z > -70)


def crypt(S):
    """Under the choir and the apse: the flooded crypt; under the crossing: its annex and the lift."""
    bp = S.bp
    causeway = set()
    for z in range(-78, -51):
        for x in range(-1, 2):
            causeway.add((x, z))
    for x in range(-1, 18):
        for z in (-52, -53, -54):
            causeway.add((x, z))
    for x in range(-17, 18):
        for z in range(-79, -51):
            if not in_chevet(x, z, -0.5):
                continue
            col = crypt_column(x, z)
            top = crypt_ceiling(x, z)
            for y in range(-12, 7):
                if col and y <= top + 1:
                    bp.set(x, y, z, TIL if y in (-9, top) else (PBB if y < -8 else BRK))
                elif y == -12:
                    bp.set(x, y, z, "deepslate")
                elif y == -11:
                    bp.set(x, y, z, "mud" if hash01(x, z, 3) < 0.4 else "deepslate")
                elif y == -10:
                    if col:
                        continue
                    if (x, z) in causeway:
                        bp.set(x, y, z, POL if abs(x) == 0 or z in (-53,) else TIL)
                    else:
                        bp.set(x, y, z, WATER)
                elif KF <= y <= top:
                    bp.set(x, y, z, AIR)
                elif y == top + 1:
                    bp.set(x, y, z, CHI if (x + z) % 7 == 0 else BRK)
    # walls round the crypt below the choir floor
    for x in range(-21, 22):
        for z in range(-82, -50):
            if in_chevet(x, z, 1.8) and not in_chevet(x, z, -0.5):
                for y in range(-12, 7):
                    if S.soft(x, y, z) or bp.get(x, y, z) in (AIR, WATER):
                        bp.set(x, y, z, PBB if y < -8 else BRK)
    # tombs on islands in the pool, sculk overgrowing them
    for (tx, tz) in ((-9, -55), (9, -57), (-12, -63), (12, -65), (-7, -71), (7, -71), (-13, -58), (5, -63),
                     (-5, -63)):
        tomb(S, tx, tz)
    # the annex under the crossing: dry floor, a barrel vault along z
    arc = pointed_arch(6.5, 4)
    for z in range(-51, -31):
        for x in range(-7, 8):
            for y in range(-12, 0):
                if abs(x) == 7:
                    bp.set(x, y, z, BRK)
                    continue
                top = -6 + int(arc(x))
                if y <= -11:
                    bp.set(x, y, z, "deepslate")
                elif y == -10:
                    bp.set(x, y, z, POL if abs(x) <= 1 else TIL)
                elif y <= top:
                    bp.set(x, y, z, AIR)
                else:
                    bp.set(x, y, z, BRK)
    for z in range(-51, -31, 4):
        for x in (-6, 6):
            bp.set(x, -6, z, "soul_wall_torch[facing=%s]" % ("east" if x < 0 else "west"))
    # openings: annex -> crypt (z -51/-52 is inside the chevet test already), corridor door in the east wall
    for z in range(-37, -34):
        for y in range(KF, KF + 4):
            bp.set(7, y, z, AIR)
        bp.set(7, KF - 1, z, POL)
    lift(S)
    # the site of grace by the choir turret, sculk and candles, lights
    bp.set(14, KF, -55, MOD["waystone"])
    bp.set(15, KF, -55, "candle[candles=3,lit=true,waterlogged=false]")
    for (x, z) in ((-6, -56), (6, -56), (-6, -68), (6, -68), (0, -76), (12, -60), (-12, -60)):
        top = crypt_ceiling(x, z)
        if bp.get(x, top, z) == AIR:
            for y in range(KF + 4, top + 1):
                bp.set(x, y, z, CHAIN)
            bp.set(x, KF + 3, z, SOUL_H)
    bp.chest(-15, KF, -60, "east", loot=LOOT + "ec_crypt")
    bp.chest(2, KF, -77, "west", loot=LOOT + "ec_crypt")
    for (x, z) in ((-15, -59), (-15, -61), (1, -77)):
        if bp.get(x, KF - 1, z) == "minecraft:water":
            bp.set(x, KF - 1, z, TIL)
    bp.set(-15, KF - 1, -60, TIL)
    bp.set(2, KF - 1, -77, TIL)
    bp.spawner(-9, KF, -66, MOB_CRAWLER)
    bp.set(-9, KF - 1, -66, TIL)
    bp.spawner(9, KF, -73, MOB_ABYSS)
    bp.set(9, KF - 1, -73, TIL)


def tomb(S, tx, tz):
    """A sarcophagus on a little island: a base, a lid, sculk veins and sensors, candles."""
    bp = S.bp
    for x in range(tx - 2, tx + 3):
        for z in range(tz - 2, tz + 3):
            if crypt_column(x, z) or not in_chevet(x, z, -1.0):
                continue
            if bp.get(x, -10, z) == "minecraft:water":
                bp.set(x, -10, z, "sculk" if hash01(x, z, 9) < 0.5 else TIL)
    for x in range(tx - 1, tx + 1):
        for z in range(tz - 1, tz + 2):
            if crypt_column(x, z):
                continue
            bp.set(x, -9, z, CHI if z == tz else POL)
            bp.set(x, -8, z, slab(TIL_SL) if hash01(x, z, 11) < 0.6 else "sculk")
    bp.set(tx + 1, -9, tz, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]"
           if hash01(tx, tz, 12) < 0.5 else "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(tx - 2, -9, tz - 1, "sculk_vein[down=true,east=false,north=false,south=false,up=false,west=false,"
                               "waterlogged=false]")
    # lit candles on the lid's ends (on full blocks: a slab lid would not hold them)
    for z in (tz - 1, tz + 1):
        x = tx - 1
        if crypt_column(x, z):
            continue
        bp.set(x, -8, z, POL)
        bp.set(x, -7, z, CANDLES % (3 if z < tz else 4))


def lift(S):
    """The pipe-shaft lift: a bubble column in a brass organ pipe from the annex floor up to the crossing."""
    bp = S.bp
    tx, tz = LIFT
    y0, y1 = KF, 0
    bp.set(tx, y0 - 1, tz, "soul_sand")
    for y in range(y0, y1 + 1):
        bp.set(tx, y, tz, "bubble_column[drag=false]")
    for y in range(y0 - 1, y1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                corner = dx != 0 and dz != 0
                spec = IRON if corner else ("glass" if y % 3 else tarnish(tx + dx, y, tz + dz))
                bp.set(tx + dx, y, tz + dz, spec)
    # the door on the east side (signs keep the water in)
    bp.set(tx + 1, y0, tz, "spruce_sign[rotation=4,waterlogged=false]")
    bp.set(tx + 1, y0 + 1, tz, "spruce_wall_sign[facing=east,waterlogged=false]")
    bp.set(tx + 1, y0 + 2, tz, IRON)
    # the mouth in the crossing floor: a brass rim, rails on two sides
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                bp.set(tx + dx, y1, tz + dz, BRASS if not (dx and dz) else IRON)
    for dz in (-1, 0, 1):
        bp.set(tx - 2, 1, tz + dz, RAIL + "[facing=west]")
    for dx in (-1, 0, 1):
        bp.set(tx + dx, 1, tz - 2, RAIL + "[facing=north]")
    for y in range(1, 4):
        bp.set(tx, y, tz, AIR)


# ------------------------------------------------------------------ the choir turret (crypt -> arena)
def stair_flight(S, lane, z_start, dz, f_start, n, df, tread=BRK_ST, clear=4):
    """n treads along z in the x lane (x0, x1): tread k at z_start + dz*k with feet f_start + df*k."""
    bp = S.bp
    x0, x1 = lane
    up = ("south" if dz > 0 else "north") if df > 0 else ("north" if dz > 0 else "south")
    if df < 0:                                          # going down: the edge of the landing is the first tread
        for x in range(x0, x1 + 1):
            bp.set(x, f_start - 1, z_start, stair(tread, up))
    for k in range(1, n + 1):
        z = z_start + dz * k
        f = f_start + df * k
        for x in range(x0, x1 + 1):
            bp.set(x, f - 1, z, stair(tread, up))
            bp.set(x, f - 2, z, BRK)
            S.lining.discard((x, f - 1, z))
            for y in range(f, f + clear):
                bp.set(x, y, z, AIR)
                S.lining.discard((x, y, z))
    return f_start + df * n


def landing(S, x0, x1, z0, z1, f, clear=4, spec=None):
    bp = S.bp
    for x in range(x0, x1 + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            bp.set(x, f - 1, z, spec or (POL if (x + z) % 2 else TIL))
            bp.set(x, f - 2, z, BRK)
            for y in range(f, f + clear):
                bp.set(x, y, z, AIR)
                S.lining.discard((x, y, z))


def turret(S):
    bp = S.bp
    xa, xb = 21, 27
    za, zb = -67, -51
    for x in range(xa - 1, xb + 2):
        for z in range(za - 1, zb + 1):
            for y in range(-12, 19):
                bp.set(x, y, z, PBB if 0 <= y < 3 else mas(x, y, z))
            rt = 19 + min(x - xa + 1, xb + 1 - x, z - za + 1, zb - z) // 2
            for y in range(19, rt + 1):
                bp.set(x, y, z, TIL)
    landing(S, 21, 27, -52, -54, KF)
    stair_flight(S, (21, 23), -54, -1, KF, 9, +1)          # north to feet 0
    landing(S, 21, 27, -64, -66, 0)
    stair_flight(S, (25, 27), -64, +1, 0, 9, +1)           # south to feet 9
    landing(S, 21, 27, -52, -54, CHF)
    # crypt -> turret and turret -> choir openings
    carve(S, 19, KF, -54, 20, KF + 3, -52)
    for x in (19, 20):
        for z in range(-54, -51):
            bp.set(x, KF - 1, z, POL)
    carve(S, 19, CHF, -54, 20, CHF + 3, -52)
    for x in (19, 20):
        for z in range(-54, -51):
            bp.set(x, CHF - 1, z, POL)
    bp.mist(19, CHF, -54, 20, CHF + 3, -52)
    for (x, y, z) in ((24, KF + 3, -55), (24, 3, -65), (24, CHF + 3, -55)):
        if bp.get(x, y + 1, z) not in (None, AIR):
            bp.set(x, y, z, LANT_H)
    # arrow slits
    for y in (4, 12):
        bp.set(28, y, -59, "iron_bars")


# ------------------------------------------------------------------ the dormitory and its stair
def bridge(S, sx):
    """Over a flying arch from the transept end door (feet 16) to the cave wall."""
    bp = S.bp
    z0, z1 = TRZ1 - 2, TRZ1
    for ax in range(31, 41):
        x = sx * ax
        for z in range(z0 - 1, z1 + 2):
            edge = z in (z0 - 1, z1 + 1)
            bp.set(x, 14, z, BRK)
            bp.set(x, 15, z, POL if not edge else BRK)
            for y in range(GAL, GAL + 4):
                if not edge:
                    bp.set(x, y, z, AIR)
                    S.lining.discard((x, y, z))
            if edge:
                if S.free(x, GAL, z) or S.soft(x, GAL, z):
                    bp.set(x, GAL, z, BRK_W)
            S.lining.discard((x, 14, z))
            S.lining.discard((x, 15, z))
    flyer(S, sx * 30, 13, sx * 40, 13, z0 - 1, z1 + 1)
    bp.set(sx * 33, GAL + 1, z0 - 1, LANT)
    bp.set(sx * 33, GAL + 1, z1 + 1, LANT)


def dormitory(S):
    bp = S.bp
    bridge(S, 1)
    rock_room(S, 37, TRZ1 - 2, 39, TRZ1, GAL, 4)
    dk = lambda x, y, z: BRK if hash3(x, y, z, 3) < 0.75 else CBRK
    fl = lambda x, z: "spruce_planks" if (x + z) % 5 else "dark_oak_planks"
    rock_room(S, 40, -38, 54, -24, GAL, 6, wall=dk, floor=fl)
    # a rib vault over the hall
    for x in range(40, 55):
        for z in range(-38, -23):
            if (z + 38) % 5 == 0 or x in (40, 54):
                continue
            bp.set(x, GAL + 6, z, AIR)
    # bunks along the north and south walls, chests at their feet, the cantor's cell
    bp.barrel_kind = "food"
    for x in range(42, 54, 3):
        bp.bed(x, GAL, -24, "north", color="gray")
        bp.bed(x, GAL, -37, "south", color="gray")
        bp.barrel(x + 1, GAL, -24, "up")
    bp.barrel_kind = None
    for x in range(43, 53, 3):
        bp.table(x, GAL, -31, top="spruce_pressure_plate", leg="spruce_fence")
        bp.set(x - 1, GAL, -31, stair("spruce_stairs", "east"))
    for (x, z) in ((44, -31), (50, -31)):
        bp.set(x, GAL + 5, z, CHAIN)
        bp.set(x, GAL + 4, z, LANT_H)
    bp.set(54, GAL, -27, "cauldron")
    bp.set(54, GAL, -28, "water_cauldron[level=3]")
    bp.set(54, GAL, -33, "lectern[facing=west,has_book=false,powered=false]")
    bp.set(53, GAL, -34, "note_block[instrument=harp,note=12,powered=false]")
    bp.chest(54, GAL, -35, "west", loot=LOOT + "ec_dormitory")
    bp.spawner(47, GAL, -28, MOB_MONK)
    # the stair: four flights down to the crypt corridor, an iron door onto the cavern floor at feet 1
    stair_flight(S, (44, 46), -38, -1, GAL, 7, -1)          # A: north, 16 -> 9
    landing(S, 44, 50, -46, -48, 9)
    stair_flight(S, (48, 50), -46, +1, 9, 8, -1)            # B: south, 9 -> 1
    landing(S, 44, 50, -35, -37, 1)
    stair_flight(S, (44, 46), -35, -1, 1, 6, -1)            # C: north, 1 -> -5
    landing(S, 44, 50, -42, -44, -5)
    stair_flight(S, (48, 50), -42, +1, -5, 4, -1)           # D: south, -5 -> -9
    landing(S, 40, 50, -35, -38, KF)
    for (x0, x1, z0, z1, f) in ((44, 50, -46, -48, 9), (44, 50, -35, -37, 1), (44, 50, -42, -44, -5)):
        for x in range(x0 - 1, x1 + 2):
            for z in range(min(z0, z1) - 1, max(z0, z1) + 2):
                for y in range(f - 2, f + 5):
                    if S.soft(x, y, z):
                        bp.set(x, y, z, dk(x, y, z))
    shell_stair(S)
    for (x, y, z) in ((47, 12, -47), (47, 4, -36), (47, -2, -43), (45, KF + 3, -36)):
        bp.set(x, y, z, LANT_H)
    # the door at feet 1 west onto the cavern floor (opens from the stair side only)
    for x in range(36, 44):
        for z in (-36,):
            for y in range(1, 4):
                bp.set(x, y, z, AIR)
                S.lining.discard((x, y, z))
            bp.set(x, 0, z, POL)
        for z in (-37, -35):
            for y in range(0, 5):
                if S.soft(x, y, z):
                    bp.set(x, y, z, dk(x, y, z))
        if S.soft(x, 4, -36):
            bp.set(x, 4, -36, dk(x, 4, -36))
    bp.door(41, 1, -36, "east", wood="iron")
    bp.set(42, 2, -35, "lever[face=wall,facing=north,powered=false]")
    # the corridor west to the crypt annex (feet -9), under the transept
    dkk = lambda x, y, z: PBB if hash3(x, y, z, 4) < 0.7 else BRK
    for x in range(8, 41):
        for z in range(-38, -33):
            for y in range(KF - 1, KF + 5):
                inner = -37 <= z <= -35 and KF <= y <= KF + 3
                if inner:
                    bp.set(x, y, z, AIR)
                    S.lining.discard((x, y, z))
                elif y == KF - 1 and -37 <= z <= -35:
                    bp.set(x, y, z, POL if z == -36 else TIL)
                else:
                    cur = bp.get(x, y, z)
                    if cur is None or (x, y, z) in S.lining:
                        bp.set(x, y, z, dkk(x, y, z))
                        S.lining.discard((x, y, z))
        if x % 6 == 0:
            bp.set(x, KF + 3, -36, SOUL_H)


def shell_stair(S):
    """Dress the soft cells round the dormitory stair's flights."""
    bp = S.bp
    for x in range(43, 52):
        for z in range(-49, -33):
            for y in range(-11, 21):
                if not S.soft(x, y, z):
                    continue
                near = False
                for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    if bp.get(x + dx, y + dy, z + dz) == AIR:
                        near = True
                        break
                if near:
                    bp.set(x, y, z, BRK if hash3(x, y, z, 3) < 0.75 else CBRK)
                    S.lining.discard((x, y, z))


def library(S):
    """West bridge: the cantors' library in the cave wall (optional)."""
    bp = S.bp
    bridge(S, -1)
    rock_room(S, -39, TRZ1 - 2, -37, TRZ1, GAL, 4)
    rock_room(S, -52, -38, -40, -24, GAL, 7, floor=lambda x, z: "dark_oak_planks" if (x + z) % 3 else
              "spruce_planks")
    for z in range(-37, -24):
        if z in (-31, -30, -29):
            continue
        for y in range(GAL, GAL + 4):
            bp.set(-52, y, z, "bookshelf" if y < GAL + 3 else "dark_oak_slab[type=bottom,waterlogged=false]")
    for x in range(-51, -41):
        for z in (-38, -24):
            for y in range(GAL, GAL + 4):
                bp.set(x, y, z, "bookshelf" if (x % 4 and y < GAL + 3) else
                       ("dark_oak_planks" if y < GAL + 3 else "dark_oak_slab[type=bottom,waterlogged=false]"))
    for x in (-48, -44):
        for z in (-34, -28):
            bp.table(x, GAL, z, top="dark_oak_pressure_plate", leg="dark_oak_fence")
            bp.set(x, GAL + 1, z, "candle[candles=2,lit=true,waterlogged=false]")
    bp.set(-46, GAL, -31, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(-50, GAL, -31, "note_block[instrument=flute,note=7,powered=false]")
    bp.chest(-51, GAL, -36, "east", loot=LOOT + "ec_library")
    for (x, z) in ((-46, -35), (-46, -27)):
        bp.set(x, GAL + 6, z, CHAIN)
        bp.set(x, GAL + 5, z, CHANDELIER)


# ------------------------------------------------------------------ furnishing of the nave
def furnish(S):
    bp = S.bp
    # pews on both sides of the axis
    for z in range(34, -22, -2):
        if any(c - 4 <= z <= c + 4 for c in ()):
            continue
        for x in list(range(-6, -1)) + list(range(2, 7)):
            if bp.get(x, 1, z) == AIR and bp.get(x, 0, z) not in (None, AIR):
                bp.set(x, 1, z, stair("dark_oak_stairs", "south"))
    for z in range(-22, 37):
        for x in (-1, 0, 1):
            if bp.get(x, 1, z) == AIR:
                bp.set(x, 1, z, "black_carpet" if x == 0 else "gray_carpet")
    # chandeliers on long chains from the vault, low over the pews (lighting() adds the rest of the nave's lights)
    for z in (33, 19, 6, -7, -20, -36):
        top = vault_top(0)
        for y in range(7, top):
            bp.set(0, y, z, CHAIN)
        bp.set(0, 6, z, CHANDELIER)
    for c in COLS:
        for sx in (-1, 1):
            bp.set(sx * 6, 1, c, "candle[candles=3,lit=true,waterlogged=false]") if bp.get(sx * 6, 1, c) == AIR \
                else None
    # aisle lamps, hung low on chains under the aisle vault
    for z in range(-26, 40, 6):
        for sx in (-1, 1):
            x = sx * 17
            if bp.get(x, 5, z) == AIR:
                top = 6
                while bp.get(x, top, z) == AIR and top < 14:
                    top += 1
                if bp.get(x, top, z) not in (None, AIR):
                    for y in range(6, top):
                        bp.set(x, y, z, CHAIN)
                    bp.set(x, 5, z, HANG_LAMP)
            if bp.get(x, GAL + 4, z) == AIR and bp.get(x, GAL + 6, z) not in (None, AIR):
                bp.set(x, GAL + 5, z, CHAIN)
                bp.set(x, GAL + 4, z, LANT_H)
    # the narthex: stoups, a lectern, lamps; the loft: benches and music stands
    for x in (-8, 8):
        bp.set(x, 1, 46, POL_W)
        bp.set(x, 2, 46, "water_cauldron[level=3]")
    bp.set(-3, 1, 44, "lectern[facing=south,has_book=false,powered=false]")
    for x in (-6, 0, 6):
        bp.set(x, 13, 45, CHAIN)
        bp.set(x, 12, 45, HANG_LAMP)
    for x in range(-8, 9):
        if x in (-1, 0, 1):
            continue
        bp.set(x, GAL, 44, stair("spruce_stairs", "south"))
        if x % 3 == 0:
            bp.set(x, GAL, 42, "lectern[facing=south,has_book=false,powered=false]")
    bp.chest(10, GAL, 47, "west", loot=LOOT + "ec_loft")
    bp.set(-10, GAL, 47, "note_block[instrument=chime,note=5,powered=false]")
    bp.set(-9, GAL, 47, "jukebox[has_record=false]")
    for x in (-8, 8):
        bp.set(x, GAL + 5, 45, CHAIN)
        bp.set(x, GAL + 4, 45, LANT_H)
    # the triforium: a spawner in the east gallery (the main route)
    bp.spawner(17, GAL, 6, MOB_MONK)
    # the crossing (hub): the site of grace by the lift, a pulpit against the north-east pier
    bp.set(-4, 1, -31, MOD["waystone"])
    bp.set(-5, 1, -31, "candle[candles=4,lit=true,waterlogged=false]")
    for y in (1, 2):
        bp.set(6, y, -41, "dark_oak_planks")
    bp.set(6, 3, -41, stair("dark_oak_stairs", "west", "top"))
    bp.set(5, 1, -41, stair("dark_oak_stairs", "south"))
    # the transepts: the sacristy (east), the founder's tomb (west)
    for z in range(TRZ0, TRZ0 + 3):
        bp.set(27, 1, z, "dark_oak_planks")
        bp.set(27, 2, z, "dark_oak_trapdoor[facing=west,half=bottom,open=false,powered=false,waterlogged=false]")
    bp.chest(27, 1, TRZ0 + 4, "west", loot=LOOT + "ec_sacristy")
    bp.barrel(27, 1, TRZ0 + 5, "up")
    for x in range(-25, -20):
        for z in range(-37, -35):
            bp.set(x, 1, z, PBB if x in (-25, -21) else POL)
            bp.set(x, 2, z, slab(TIL_SL) if x not in (-24, -23) else POL)
    bp.set(-23, 3, -36, "skeleton_skull[rotation=0]")
    for (x, z) in ((-26, -38), (-20, -34)):
        bp.set(x, 1, z, "candle[candles=3,lit=true,waterlogged=false]")
    for sx in (-1, 1):
        x = sx * 21
        for y in range(9, 36):
            bp.set(x, y, -36, CHAIN)
        bp.set(x, 8, -36, CHANDELIER)


# ------------------------------------------------------------------ lighting
CANDLES = "candle[candles=%d,lit=true,waterlogged=false]"
SOUL_FIRE = "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"


def hang(S, x, y, z, spec, top=60):
    """Hang `spec` at (x, y, z) on an iron chain up to the first solid block above (within `top`)."""
    bp = S.bp
    if bp.get(x, y, z) != AIR:
        return False
    t = y + 1
    while t < top and bp.get(x, t, z) == AIR:
        t += 1
    if bp.get(x, t, z) in (None, AIR):
        return False
    for yy in range(y + 1, t):
        bp.set(x, yy, z, CHAIN)
    bp.set(x, y, z, spec)
    return True


def lighting(S):
    """Gloomy but readable (§15): every main room keeps its walkable floor at light 8 or more with lights that
    belong to the place: lanterns in niches of the columns and candles on their plinths, candelabra in the arcades,
    chandeliers low on chains, soul-fire braziers outside, glowing organ pipe mouths, ripples of ochre light in the
    arena floor, froglights in the crypt pool, sea lanterns behind the rose windows."""
    bp = S.bp
    # the columns: a lantern in a niche on each free face, candles on the plinth toward the nave
    for c in COLS + [CROSS_S, CROSS_N]:
        for sx in (-1, 1):
            cx = sx * 10
            for (x, z, ox, oz) in ((cx - 3 * sx, c, -sx, 0), (cx + 3 * sx, c, sx, 0), (cx, c - 3, 0, -1),
                                   (cx, c + 3, 0, 1)):
                if bp.get(x + ox, 3, z + oz) == AIR and bp.get(x + ox, 4, z + oz) == AIR:
                    bp.set(x, 3, z, LANT)
                    bp.set(x, 4, z, CHI)
            for z in (c - 2, c + 2):
                x = sx * 6
                if "polished_blackstone_brick_stairs" in (bp.get(x, 2, z) or "") and bp.get(x, 3, z) == AIR:
                    bp.set(x, 2, z, PBB)
                    bp.set(x, 3, z, CANDLES % 4)
    # lanterns on long chains over the pews, along the column lines between the chandeliers
    for c in COLS + [38]:
        for x in (-3, 3):
            hang(S, x, 6, c, LANT_H)
    # the triforium over the loft: lanterns on the parapet ends and hung in the gallery
    for sx in (-1, 1):
        for z in (30, 40):
            if bp.get(sx * 7, GAL + 1, z) == "minecraft:" + POL_W and bp.get(sx * 7, GAL + 2, z) == AIR:
                bp.set(sx * 7, GAL + 2, z, LANT)
        hang(S, sx * 11, GAL + 3, 35, LANT_H, top=GAL + 8)
    # candle posts at the inner ends of every other pew
    for z in range(32, -21, -4):
        for x in (-2, 2):
            if "dark_oak_stairs" in (bp.get(x, 1, z) or "") and bp.get(x, 2, z) == AIR:
                bp.set(x, 1, z, POL_W)
                bp.set(x, 2, z, CANDLES % 4)
    # candelabra in the arcades between nave and aisles
    for z0, z1 in BAYS:
        mid = (z0 + z1) // 2
        for sx in (-1, 1):
            x = sx * 10
            if bp.get(x, 1, mid) == AIR:
                bp.set(x, 1, mid, PBB)
                bp.set(x, 2, mid, IRON_WALL)
                bp.set(x, 3, mid, LANT)
    # aisles: votive candles on the chapel thresholds' sides, lanterns on the outer wall between the windows
    for z in range(-28, 40, 6):
        for sx in (-1, 1):
            x = sx * 19
            if bp.get(x, 1, z) == AIR and bp.get(sx * 20, 1, z) not in (None, AIR) and bp.get(x, 2, z) == AIR:
                bp.set(x, 1, z, POL_W)
                bp.set(x, 2, z, SOUL)
    # the crossing and the transepts: more chandeliers low on chains, lanterns at the transept walls
    for x in (-25, -12, 12, 25):
        hang(S, x, 8, -36, CHANDELIER)
    for x in (-4, 4):
        for z in (-30, -42):
            hang(S, x, 6, z, LANT_H)
    for x in (-7, 6):
        hang(S, x, 6, -36, LANT_H)
    for sx in (-1, 1):
        for z in (TRZ0, TRZ1):
            for ax in (16, 22, 27):
                x = sx * ax
                if bp.get(x, 1, z) == AIR and bp.get(x, 2, z) == AIR:
                    bp.set(x, 1, z, POL_W)
                    bp.set(x, 2, z, LANT)
    # the narthex: candle stands by the portal and the stoups
    for (x, z) in ((-5, 47), (5, 47), (-10, 42), (10, 42), (-10, 47), (10, 47)):
        if bp.get(x, 1, z) == AIR:
            bp.set(x, 1, z, POL_W)
            bp.set(x, 2, z, LANT)
    # the forecourt: the stone choristers hold up lanterns, soul-fire braziers along the way, lamp posts
    for z in (56, 60, 64):
        for sx in (-1, 1):
            x = sx * 6 - sx                     # on the raised hand (a top stair)
            if "stairs" in (bp.get(x, 4, z) or "") and bp.get(x, 5, z) == AIR:
                bp.set(x, 5, z, LANT)
    for z in (54, 58, 62, 66):
        for sx in (-1, 1):
            x = sx * 4
            if bp.get(x, 0, z) not in (None, AIR):
                bp.set(x, 1, z, PBB)
                bp.set(x, 2, z, SOUL_FIRE)
    for sx in (-1, 1):
        for z in (55, 60, 65):
            x = sx * 12
            if bp.get(x, 0, z) not in (None, AIR) and bp.get(x, 1, z) == AIR:
                bp.set(x, 1, z, PBB)
                bp.set(x, 2, z, POL_W)
                bp.set(x, 3, z, POL_W)
                bp.set(x, 4, z, LANT)
    # the rose windows: sea lanterns behind the tracery ring (lit from within, seen from the nave and outside)
    for du in range(-7, 8):
        for dy in range(-7, 8):
            d = math.hypot(du, dy)
            if abs(d - 6.3 * 0.55) < 0.5 and (du + dy) % 2 == 0 and bp.get(du, 29 + dy, 51) == AIR:
                bp.set(du, 29 + dy, 51, "sea_lantern")
    for sx in (-1, 1):
        zm = (TRZ0 + TRZ1) / 2.0
        for du in range(-6, 7):
            for dy in range(-6, 7):
                d = math.hypot(du, dy)
                z = int(round(zm + du))
                if abs(d - 5.2 * 0.55) < 0.5 and (du + dy) % 2 == 0 and \
                        bp.get(sx * 30, 25 + dy, z) == "minecraft:" + POL:
                    bp.set(sx * 29, 25 + dy, z, "sea_lantern")
    # the arena: ripples of ochre light in the brass rings, candles and lanterns on the organ console
    for rr, step, off in ((11, 30, 15), (6, 45, 22.5)):
        for k in range(int(360 / step)):
            a = math.radians(off + k * step)
            best = None
            for x in range(int(round(math.sin(a) * rr)) - 1, int(round(math.sin(a) * rr)) + 2):
                for z in range(int(round(AZ + math.cos(a) * rr)) - 1, int(round(AZ + math.cos(a) * rr)) + 2):
                    if bp.get(x, 8, z) in (BRASS, IRON) and bp.get(x, CHF, z) == AIR and in_chevet(x, z):
                        e = abs(math.hypot(x, z - AZ) - rr) + 0.3 * math.hypot(x - math.sin(a) * rr,
                                                                                z - AZ - math.cos(a) * rr)
                        if best is None or e < best[0]:
                            best = (e, x, z)
            if best:
                bp.set(best[1], 8, best[2], "ochre_froglight[axis=y]")
    for x in (-3, 3):
        bp.set(x, CHF + 2, -71, MAHOGANY)
        bp.set(x, CHF + 3, -71, CANDLES % 4)
    for x in (-2, 2):
        bp.set(x, CHF + 3, -71, CANDLES % 3) if bp.get(x, CHF + 2, -71) == MAHOGANY else None
    for (x, z) in ((-4, -72), (4, -72), (-4, -67), (4, -67)):
        if bp.get(x, CHF, z) == AIR:
            bp.set(x, CHF, z, IRON_WALL)
            bp.set(x, CHF + 1, z, LANT)
    # the choir by the screen: soul lanterns on the wall posts
    for x in (-9, 9):
        hang(S, x, CHF + 5, -54, SOUL_H, top=30)
    for x in (-17, 17):
        for z in (-53, -57):
            if bp.get(x, CHF, z) == AIR and bp.get(x, CHF + 1, z) == AIR:
                bp.set(x, CHF, z, IRON_WALL)
                bp.set(x, CHF + 1, z, LANT)
    hang(S, 0, CHF + 2, -77, LANT_H, top=CHF + 4)            # the reliquary passage
    # the flooded crypt: froglights in the bed of the pool, glimmering up through the black water
    for x in range(-17, 18):
        for z in range(-79, -51):
            if bp.get(x, -10, z) == "minecraft:water" and x % 4 == 0 and (z + (x // 4) * 2) % 4 == 0 and \
                    hash01(x, z, 171) < 0.9:
                bp.set(x, -11, z, "verdant_froglight[axis=y]" if hash01(x, z, 172) < 0.5
                       else "pearlescent_froglight[axis=y]")
    for x in (7, 13):
        hang(S, x, KF + 3, -53, LANT_H, top=8)
    # the annex: lanterns on the causeway posts
    for z in range(-49, -31, 6):
        for x in (-5, 5):
            if bp.get(x, KF, z) == AIR and bp.get(x, KF - 1, z) not in (None, AIR, WATER):
                bp.set(x, KF, z, POL_W)
                bp.set(x, KF + 1, z, LANT)
    # the dormitory: lanterns on the bunk barrels, candles on the tables, a lamp over the cantor's desk
    for x in range(42, 54, 3):
        if bp.get(x + 1, GAL + 1, -24) == AIR:
            bp.set(x + 1, GAL + 1, -24, LANT)
        if bp.get(x + 1, GAL, -37) == AIR:
            bp.set(x + 1, GAL, -37, PBB)
            bp.set(x + 1, GAL + 1, -37, CANDLES % 3)
    for x in range(43, 53, 3):
        if bp.get(x, GAL + 1, -31) == AIR:
            bp.set(x, GAL + 1, -31, CANDLES % 2)
    for x in (41, 47, 53):
        for z in (-33, -28):
            hang(S, x, GAL + 3, z, LANT_H, top=GAL + 8)        # from the ribs of the vault
    for x in (44, 50):
        if bp.get(x, GAL + 6, -31) == AIR:
            bp.set(x, GAL + 6, -31, CHAIN)                       # the old lamps' chains reach the rock
    # the bell chamber: a soul lantern hangs from the clapper inside the cracked bell, lanterns from the beam
    bp.set(-16, 34, 46, SOUL_H)
    for x in (-21, -11):
        if bp.get(x, 41, 46) == AIR and bp.get(x, 42, 46) not in (None, AIR):
            bp.set(x, 41, 46, CHAIN)
            bp.set(x, 40, 46, LANT_H)


def yards(S):
    """Ground doors in the transept end walls onto the cave yards under the bridges (the east yard is where the
    dormitory stair's iron door comes out: the way back to the crossing)."""
    bp = S.bp
    for sx in (-1, 1):
        for y in range(F, F + 3):
            bp.set(sx * 29, y, -36, AIR)
        bp.door(sx * 30, F, -36, "east" if sx > 0 else "west", wood="dark_oak")
        bp.set(sx * 29, F + 3, -36, CHI)
        for z in (-37, -35):
            bp.set(sx * 31, F + 2, z, "soul_wall_torch[facing=%s]" % ("east" if sx > 0 else "west"))


# ------------------------------------------------------------------ cave dressing
def cave_dressing(S):
    """Dripstone from the roof, stalagmites and sculk on the floor, glow lichen on the walls (where still open)."""
    bp = S.bp
    keys = list(S.cmap.items())
    for i, ((x, z), top) in enumerate(keys):
        h = hash01(x, z, 141)
        if h < 0.035 and bp.get(x, top, z) == AIR and bp.get(x, top + 1, z) not in (None, AIR):
            ln = 1 + int(hash01(x, z, 142) * 4)
            if all(bp.get(x, top - k, z) == AIR for k in range(ln + 3)):
                for k in range(ln):
                    th = "tip" if k == ln - 1 else ("base" if k == 0 and ln > 2 else "frustum")
                    bp.set(x, top - k, z, f"pointed_dripstone[thickness={th},vertical_direction=down,"
                                          f"waterlogged=false]")
        on_path = abs(x) <= 16 and z > 40
        if h > 0.975 and not on_path and bp.get(x, 1, z) == AIR and bp.get(x, 0, z) not in (None, AIR) and \
                bp.get(x, 0, z).split(":")[1] in ("deepslate", "tuff", "cobbled_deepslate", "polished_deepslate"):
            ln = 1 + int(hash01(x, z, 143) * 3)
            if all(bp.get(x, 1 + k, z) == AIR for k in range(ln + 2)):
                for k in range(ln):
                    th = "tip" if k == ln - 1 else ("base" if k == 0 and ln > 2 else "frustum")
                    bp.set(x, 1 + k, z, f"pointed_dripstone[thickness={th},vertical_direction=up,waterlogged=false]")
    # glow lichen on the walls at head height, sculk veins low down on the north side
    for (x, y, z) in list(S.lining):
        if not 2 <= y <= 30:
            continue
        h = hash3(x, y, z, 151)
        if h > 0.025 or bp.get(x, y, z) != "minecraft:" + rock(x, y, z):
            continue
        for face, (dx, dz) in DIRS.items():
            n = (x + dx, y, z + dz)
            if bp.get(*n) == AIR:
                props = {k: "false" for k in ("down", "east", "north", "south", "up", "west")}
                props[OPP[face]] = "true"
                kind = "sculk_vein" if z < -30 and h < 0.012 else "glow_lichen"
                bp.set(*n, with_props(kind, waterlogged=False, **props))
                break
    # a spawner out in the dark of the west yard
    bp.spawner(-33, 1, -40, MOB_ABYSS)


SOLID = {"minecraft:" + n for n in (POL, BRK, TIL, CHI, CBRK, CTIL, COB, PB, PBB, "deepslate", "tuff", "calcite",
                                     "smooth_basalt", "dripstone_block", "mud", "dark_oak_planks", "cobblestone")} | {
    BRASS, VERD, IRON, MAHOGANY}


def hollow_cores(S):
    """Leave the hidden cores of walls, piers and roofs to the rock they are built in: a plain masonry block with
    plain masonry on all six sides is dropped from the template (the deepslate around keeps it solid in the world)."""
    bp = S.bp
    B = bp.blocks

    def plain(p):
        v = B.get(p)
        return v is not None and v[0] in SOLID and not v[1] and v[2] is None

    drop = [p for p in B if plain(p) and all(plain((p[0] + dx, p[1] + dy, p[2] + dz)) for dx, dy, dz in
                                             ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))]
    for p in drop:
        del B[p]


def echo_cathedral(bp):
    S = Site(bp)
    cavern(S)
    side_cave(S)
    forecourt(S)
    nave_shell(S)
    transepts(S)
    west_front(S)
    tower(S, -1)
    tower(S, 1)
    bell_chamber(S)
    bellows_loft(S)
    chapels(S)
    buttresses(S)
    chevet(S)
    apse_buttresses(S)
    crypt(S)
    turret(S)
    organ(S)
    reliquary(S)
    dormitory(S)
    library(S)
    furnish(S)
    lighting(S)
    yards(S)
    cave_dressing(S)
    hollow_cores(S)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("forecourt", (0, F, 68), (0, 22, 52)),
    ("nave", (0, F, 37), (0, 16, -44)),
    ("triforium", (16, GAL, 30), (12, GAL + 3, -10)),
    ("bell_chamber", (-21, BELL_F, 41), (-16, 37, 46)),
    ("dormitory", (42, GAL, -30), (52, GAL + 2, -30)),
    ("flooded_crypt", (0, KF, -53), (-6, -6, -68)),
    ("arena", (0, CHF, -53), (0, 45, -76)),
]

register(StructureDef(
    "echo_cathedral", "overworld", ["deep_dark", "dripstone_caves"],
    [Piece("cathedral", echo_cathedral, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", height=("uniform", -56, -53), processors="none",
    step="underground_structures", max_distance=116, foundation=False,
    spawns=[(MOB_MONK, 8, 1, 2), (MOB_CRAWLER, 4, 1, 1), (MOB_ABYSS, 4, 1, 2), (MOB_BANSHEE, 2, 1, 1)],
    title_fr="La Cathédrale de l'Écho", title_en="The Echo Cathedral"))
