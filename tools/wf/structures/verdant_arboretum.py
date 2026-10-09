"""The Sunken Arboretum (L'Arboretum englouti): a botanical research complex built inside a vast lush cavern under the
lush caves, round a colossal brass-and-glass palm house dome whose ribs hold up the cavern roof. Colossal tier
(tools/BUILDING.md §1, §12 concept 27, §10, §15).

Silhouette (one noun phrase, §15.1): a glowing glass dome under a stone sky, its brass ribs running up into the rock,
a waterfall pouring off an aqueduct into a lily lake at its feet, glasshouses stepping up the terraces either side.
Theme: life underground. Glow berries, spore blossoms, moss, azalea, dripleaf, lily pads and hanging roots over
brass, copper, verdigris and dark iron; the cavern is bright and green, not dark: every walkable floor keeps light 8
or more (glow berries on the roof, froglights in the paths, lanterns on the brass).

Layout, blueprint y = world y - start height - LOW (template bottom = the lake bed): the cavern floor is the block
layer y 0 (feet 1), the terraces' y 7 (feet 8); x east, z south; the dome on (0, -20). Placed at a fixed height
(start y -16..-12: cavern floor near world y -10..-4) in lush caves, found with the structure compass.
  * the approach: the botanists' camp (waystone) in a side cave south-east of the cavern; its tunnel (compression,
    3 x 4, ~40 long, one bend) comes out through the back door of the lake shore station;
  * the lake shore station (hub, waystone): a brass-and-glass pavilion on the south shore; through its arcade the
    whole cavern opens (release, the reveal): the lily lake, the waterfall, the dome rising 50 blocks into the rock;
    an observation deck upstairs; the causeway runs north across the lake to the dome's great south doors (barred:
    they open from inside only, the way back after the boss);
  * west: along the shore past the waterfall pool (a grotto behind the fall), the terrace stair, the propagation
    greenhouses (double glasshouse, benches, misting pipes; its south door opens from inside only: shortcut 1), the
    seed vault cut into the west wall (round brass door, drawers), the overgrown specimen laboratory in the north-west
    (specimen tanks: glass jars of plants, the dissection bench, the archive);
  * north: the irrigation passage under the herbarium (aqueduct on arches overhead) to the pump house (north-east):
    the engine hall with its beam pump, the boiler gallery, and the lift tower on the dome band whose bubble column
    rises from the lake level to the cornice (shortcut 2: its top door opens from the cornice only);
  * east: the azalea maze on the east terrace (flowering hedges, a fountain court in the middle), from whose court
    the east rib catwalk climbs a great brass rib to the dome's cornice (feet 21): the site of grace in the lamp
    kiosk; the dripleaf drop off the cornice into the lake (shortcut 3); the west rib catwalk's gate opens from the
    cornice only, down to the greenhouses (shortcut 4);
  * the boss: through the mist in the cornice door, the inner rib bridge to the arena, a giant lily-pad platform
    (32 across, an upturned rim) on a brass pedestal in the dome's pool, under the sun-lamp: a giant brass lamp of
    shroomlight, sea lanterns and lenses hanging from the dome's crown. North over the second rib bridge, behind
    sealed bars, the herbarium vault (best loot), and its stair down to the irrigation passage. After the fight, a
    jump into the pool and the south doors lead back to the station;
  * optional: the station's deck, the waterfall grotto, the aqueduct walk, dripleaf islands, the boiler gallery.
Loot gradient (§15.6): camp, station tier 1; greenhouse, maze tier 1-2; seed vault, laboratory, pump house tier 2;
lift top, cornice tier 2-3; the herbarium vault tier 3.
Budget: the cavern is the bulk of the entries (every cell of it is written as air); its roof hugs the dome and the
buildings (low by the walls, high over the lake) to stay under ~450k entries.
"""
import math

from ..arch import slab, stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, MAHOGANY, MAHOGANY_SLAB, MAHOGANY_STAIRS, PIPES, TABLE,
                       TREAD, VERD, W, fbm, hash01, hash3)
from ..parts import LOOT, MOD

# the champion of the lily-pad arena: the Head Gardener (entity/boss/ThornGardener.java, tools/BOSSES.md)
BOSS = "brasshaven:thorn_gardener"
MOB_FROG = "brasshaven:dart_frog_assassin"
MOB_SPIDER = "brasshaven:clockwork_spider"
MOB_DRONE = "brasshaven:steam_drone"

# ------------------------------------------------------------------ dimensions
F = 1                    # cavern floor feet (floor block y 0)
TF = 8                   # terrace feet (floor block y 7)
COR = 21                 # cornice deck feet (deck block y 20)
DCX, DCZ = 0, -20        # dome centre
DR = 27.0                # drum outer radius (shell 26.5 <= d < 27.5)
DRUM_TOP = 20            # entablature ring; the dome springs above it
DOME_H = 30.0            # dome rise above DRUM_TOP (crown ~50)
PAD_R = 16.0             # the lily-pad platform
POOL_R = 21.0            # the pool inside the dome
TER_X = 37               # the terraces start at |x| >= TER_X
LAKE = (0, 26, 28.0, 15.0)   # lake ellipse centre x, z, radii
LIFT = (31, -34)         # the pump-house lift (bubble column)

AIR = "minecraft:air"
SB, MSB, CSB, CHSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "chiseled_stone_bricks"
SB_ST, MSB_ST, SB_SL, MSB_SL, SB_W, MSB_W = ("stone_brick_stairs", "mossy_stone_brick_stairs", "stone_brick_slab",
                                             "mossy_stone_brick_slab", "stone_brick_wall", "mossy_stone_brick_wall")
PA, PA_ST, PA_SL = "polished_andesite", "polished_andesite_stairs", "polished_andesite_slab"
TB, TB_ST, TB_SL = "tuff_bricks", "tuff_brick_stairs", "tuff_brick_slab"
MOSS, MOSS_C, CLAY, ROOTED = "moss_block", "moss_carpet", "clay", "rooted_dirt"
GLASS = "glass"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
WATER = "water[level=0]"
FALL = "water[level=8]"
SHROOM, SEA = "shroomlight", "sea_lantern"
FROG_O, FROG_P, FROG_V = "ochre_froglight[axis=y]", "pearlescent_froglight[axis=y]", "verdant_froglight[axis=y]"
AZ_LEAVES = "azalea_leaves[distance=7,persistent=true,waterlogged=false]"
FAZ_LEAVES = "flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]"
JUNGLE_LEAVES = "jungle_leaves[distance=7,persistent=true,waterlogged=false]"
SPORE = "spore_blossom"
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


def mas(x, y, z, base=0):
    """Stone-brick masonry with a vertical gradient (§5): mossy and cracked at the damp base, plain bricks in the
    body, polished andesite toward the top; the band edges jitter."""
    yy = y - base + (hash3(x // 2, y // 3, z // 2, 5) - 0.5) * 4
    if yy < 3:
        return pick([(MSB, 4), (SB, 2), (CSB, 1), ("mossy_cobblestone", 1)], x, y, z, 11)
    if yy < 14:
        return pick([(SB, 7), (MSB, 1.5), (CSB, 1)], x, y, z, 12)
    return pick([(SB, 5), (PA, 2), (TB, 1)], x, y, z, 13)


def patina(x, y, z):
    """Brass gone green where the water runs: verdigris low and in patches."""
    v = fbm(x * 0.9 + z * 0.4, y * 0.8 + z * 0.3, 4.0, 77)
    return VERD if v + max(0, (12 - y)) * 0.02 > 0.62 else BRASS


def rock(x, y, z):
    """Cave rock: strata of stone, andesite, tuff and diorite with moss and clay patches (two-octave jitter, §11)."""
    yy = y + (fbm(x * 0.6 + z * 0.4, y * 0.9, 7.0, 41) - 0.5) * 7
    seq = ("stone", "andesite", "stone", "tuff", "stone", "diorite", "andesite", "stone", "tuff", "deepslate")
    s = seq[int(yy // 3) % len(seq)]
    n = fbm(x, z + y * 0.5, 9.0, 43)
    if n > 0.64:
        s = MOSS
    elif n < 0.26 and y < 8:
        s = CLAY
    if hash3(x, y, z, 7) < 0.05:
        s = "cobblestone" if y > 4 else "mossy_cobblestone"
    return s


def ddist(x, z):
    return math.hypot(x - DCX, z - DCZ)


def in_lake(x, z):
    cx, cz, rx, rz = LAKE
    if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 < 1.0 + (fbm(x, z, 5.0, 81) - 0.5) * 0.25:
        return True
    # the moat round the dome's south half, under the cornice
    d = ddist(x, z)
    return 27.5 <= d < 33.5 and z > DCZ + 12


# ------------------------------------------------------------------ site state
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.cmap = {}          # (x, z) -> (floor y, top air y)
        self.lining = set()     # cave rock written round the cavern (free to carve or replace)

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def soft(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or (x, y, z) in self.lining

    def free(self, x, y, z):
        return self.bp.get(x, y, z) == AIR

    def floor(self, x, z):
        c = self.cmap.get((x, z))
        return c[0] if c else None


def _lerp(pts, z):
    if z >= pts[0][0]:
        return pts[0][1]
    for (z0, v0), (z1, v1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            t = (z0 - z) / (z0 - z1)
            return v0 + (v1 - v0) * t
    return pts[-1][1]


# half width of the cavern by z (south to north)
HALF_W = [(64, 4), (61, 12), (58, 24), (52, 38), (44, 52), (36, 62), (20, 66), (-30, 66), (-48, 64), (-58, 58),
          (-66, 48), (-72, 36), (-76, 18), (-78, 6)]


def cave_w(z, side):
    return _lerp(HALF_W, z) + (fbm(z * 1.0, side * 37.0, 6.0, 31) - 0.5) * 5.0


def floor_y(x, z):
    """Floor block y of the column: 7 on the terraces, 0 on the cavern floor; the lake and the dome pool lower."""
    d = ddist(x, z)
    if d < 26.5:
        return 0
    if abs(x) >= TER_X + (fbm(x * 0.3, z * 0.9, 4.0, 85) - 0.5) * 1.5 and z < 44:
        return 7
    if z < -40 and d >= 28.5:
        return 7
    return 0


# the masses the cavern roof must clear: (plan x0, x1, z0, z1, top, margin)
RECTS = [
    (-17, 17, 39, 58, 19, 4),            # the lake shore station
    (-61, -43, -6, 30, 21, 4),           # the propagation greenhouses
    (-37, -7, -75, -51, 20, 4),          # the laboratory
    (34, 60, -58, -34, 31, 3),           # the pump house and its chimney
    (27, 36, -38, -29, 28, 3),           # the lift tower
    (-10, 16, -64, -46, 33, 3),          # the herbarium
    (-70, -18, 30, 36, 25, 3),           # the aqueduct
    (24, 44, -6, 1, 25, 3),              # the east rib catwalk
    (-44, -24, -12, -6, 25, 3),          # the west rib catwalk
    (36, 64, -30, 32, 13, 3),            # the maze hedges
]
SLOPE = 2.0


def _dome_top(d):
    """Top of the dome's outer surface (or the cornice) at distance d from its axis."""
    if d < 27.5:
        return DRUM_TOP + DOME_H * math.sqrt(max(0.0, 1 - (d / 27.5) ** 2))
    if d < 32:
        return 22
    return 0


DOME_KEEP = []
for _i in range(0, 140):
    _d = _i * 0.5
    _k = 0.0
    for _j in range(0, 64):
        _r = _j * 0.5
        _k = max(_k, _dome_top(_r) + 3 - SLOPE * max(0.0, _d - _r))
    DOME_KEEP.append(_k)


def keep_clear(x, z):
    d = ddist(x, z)
    k = DOME_KEEP[min(len(DOME_KEEP) - 1, int(d * 2))]
    for x0, x1, z0, z1, top, margin in RECTS:
        dx = max(x0 - x, 0, x - x1)
        dz = max(z0 - z, 0, z - z1)
        k = max(k, top + margin - SLOPE * math.hypot(dx, dz))
    return k


def roof_y(x, z, w, fy):
    u = min(1.0, abs(x) / max(w, 1.0))
    # the vault rises toward the lake and the dome: high over the water (the view), low by the walls
    zc = 1.0 - min(1.0, abs(z - 8) / 70.0) ** 2
    c = fy + 6 + (28 - fy) * (1 - u ** 1.8) * (0.5 + 0.5 * zc)
    c = max(c, keep_clear(x, z), fy + 6)
    c += (fbm(x * 0.8, z * 0.8, 7.0, 35) - 0.5) * 4.0
    return int(round(c))


def floor_block(x, z, fy):
    """The cavern floor: moss and rooted dirt, clay by the water, grass-like moss on the terraces."""
    h = hash01(x, z, 21)
    n = fbm(x, z, 8.0, 22)
    if fy == 0 and in_lake(x, z + 3) or in_lake(x + 3, z) or in_lake(x - 3, z):
        return CLAY if h < 0.5 else ("mud" if h < 0.7 else MOSS)
    if n < 0.3:
        return ROOTED if h < 0.5 else "coarse_dirt"
    if n > 0.7:
        return "stone" if h < 0.5 else "andesite"
    return MOSS if h < 0.8 else "grass_block[snowy=false]"


def cavern(S):
    """Air of the cavern over its floors, a one-block lining of strata round it (walls and roof), the terrace
    retaining walls."""
    bp = S.bp
    cols = {}
    for z in range(-80, 66):
        for x in range(-70, 71):
            side = 1 if x >= 0 else -1
            w0 = cave_w(z, side)
            if abs(x) >= w0:
                continue
            fy = floor_y(x, z)
            top = roof_y(x, z, w0, fy)
            # the walls lean in a little as they rise
            ytop = fy
            for y in range(fy + 1, top + 1):
                ww = w0 - max(0, y - fy - 6) * 0.18 + (fbm(z * 0.7, y * 0.9 + side * 50, 5.0, 33) - 0.5) * 2.0
                if abs(x) >= ww and y > fy + 3:
                    break
                ytop = y
            if ytop >= fy + 3:
                cols[(x, z)] = (fy, ytop)
    S.cmap = cols
    for (x, z), (fy, top) in cols.items():
        for y in range(fy + 1, top + 1):
            bp.set(x, y, z, AIR)
        bp.set(x, fy, z, floor_block(x, z, fy))
    # terrace retaining walls: battered masonry where a terrace column meets a lower one
    for (x, z), (fy, top) in cols.items():
        if fy == 0:
            continue
        low = [n for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)) if n in cols and cols[n][0] < fy]
        if not low:
            continue
        for y in range(0, fy):
            bp.set(x, y, z, mas(x, y, z))
        bp.set(x, fy, z, PA if hash01(x, z, 4) < 0.6 else SB)
    # lining: the roof and the walls
    for (x, z), (fy, top) in cols.items():
        if bp.get(x, top + 1, z) is None:
            bp.set(x, top + 1, z, rock(x, top + 1, z))
            S.lining.add((x, top + 1, z))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            nfy, ntop = cols.get(n, (None, None))
            lo = fy if nfy is None else max(fy, ntop + 1)
            for y in range(lo, top + 1):
                if bp.get(n[0], y, n[1]) is None:
                    bp.set(n[0], y, n[1], rock(n[0], y, n[1]))
                    S.lining.add((n[0], y, n[1]))
            if nfy is None and bp.get(n[0], fy, n[1]) is None:
                bp.set(n[0], fy, n[1], rock(n[0], fy, n[1]))
                S.lining.add((n[0], fy, n[1]))


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


def hang(S, x, y, z, spec, top=70):
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


def berries(S, x, z, y_top, low, seed=0):
    """A glow-berry vine hanging from the solid block above y_top down to y `low` (berries on most links)."""
    bp = S.bp
    if bp.get(x, y_top + 1, z) in (None, AIR) or bp.get(x, y_top, z) != AIR:
        return False
    if low > y_top:
        return False
    for y in range(y_top, low - 1, -1):
        if bp.get(x, y, z) != AIR:
            return False
    for y in range(y_top, low - 1, -1):
        lit = "true" if hash3(x, y, z, 91 + seed) < 0.7 else "false"
        if y == low:
            bp.set(x, y, z, "cave_vines[age=25,berries=%s]" % ("true" if lit == "true" or True else "false"))
        else:
            bp.set(x, y, z, "cave_vines_plant[berries=%s]" % lit)
    return True


def lamp_post(S, x, f, z, h=3, top=LANT):
    S.set(x, f - 1, z, S.get(x, f - 1, z) or SB)
    for y in range(f, f + h):
        S.set(x, y, z, IRON_WALL)
    S.set(x, f + h, z, top)


# ------------------------------------------------------------------ the side cave, the tunnel and the camp
CAMP = (24, 92)


def side_cave(S):
    """The botanists' camp in a mossy side cave south-east of the cavern, and the tunnel to the station."""
    bp = S.bp
    cx, cz = CAMP
    cells = []
    for x in range(cx - 15, cx + 16):
        for z in range(cz - 13, cz + 14):
            n = fbm(x * 1.1, z * 1.1, 5.0, 61)
            rx, rz = 12.5 + (n - 0.5) * 6, 10.5 + (n - 0.5) * 5
            d = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
            if d >= 1.0:
                continue
            top = int(round(4 + 7 * math.sqrt(1 - d) + (fbm(x, z, 4.0, 62) - 0.5) * 3))
            cells.append((x, z, top))
    have = {(x, z) for x, z, _ in cells}
    for x, z, top in cells:
        bp.set(x, 0, z, MOSS if hash01(x, z, 63) < 0.6 else (ROOTED if hash01(x, z, 64) < 0.5 else CLAY))
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
    # the tunnel: 3 wide, 4 high: north from the station's back door, then a bend east to the cave
    path = [(x, z) for z in range(58, 84) for x in range(-1, 2)]
    path += [(x, z) for x in range(2, cx - 1) for z in range(81, 84)]
    path += [(x, z) for x in range(cx - 4, cx - 1) for z in range(84, 87)]
    pset = set(path)
    for (x, z) in path:
        for y in range(1, 5):
            bp.set(x, y, z, AIR)
            S.lining.discard((x, y, z))
        bp.set(x, 0, z, PA if (x + z) % 3 else SB)
        S.lining.discard((x, 0, z))
    for (x, z) in path:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                n = (x + dx, z + dz)
                if n in pset:
                    continue
                for y in range(0, 6):
                    if S.soft(n[0], y, n[1]):
                        bp.set(n[0], y, n[1], mas(n[0], y, n[1]) if y < 4 else rock(n[0], y, n[1]))
                        S.lining.discard((n[0], y, n[1]))
        if S.soft(x, 5, z):
            bp.set(x, 5, z, rock(x, 5, z))
    # timber frames and lamps along the tunnel, roots through the ceiling
    for z in (63, 69, 75):
        for x in (-2, 2):
            for y in range(1, 5):
                bp.set(x, y, z, "stripped_jungle_log[axis=y]")
        for x in range(-1, 2):
            bp.set(x, 5, z, "stripped_jungle_log[axis=x]")
        bp.set(0, 4, z, LANT_H)
    for x in (6, 12):
        for z in (80, 84):
            for y in range(1, 5):
                bp.set(x, y, z, "stripped_jungle_log[axis=y]")
        for z in range(81, 84):
            bp.set(x, 5, z, "stripped_jungle_log[axis=z]")
        bp.set(x, 4, 82, LANT_H)
    for (x, z) in ((-1, 66), (1, 72), (0, 78), (9, 82)):
        if bp.get(x, 5, z) not in (None, AIR):
            bp.set(x, 4, z, "hanging_roots[waterlogged=false]")
    camp(S)


def camp(S):
    """Tents, a fire, the waystone, a chest, potted cuttings and the botanists' notes."""
    bp = S.bp
    cx, cz = CAMP
    bp.set(cx, 0, cz, "cobblestone")
    bp.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, fc) in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz + 2, "north")):
        bp.set(x, 1, z, stair("jungle_stairs", OPP[fc]))
    for (tx, tz, col) in ((cx - 7, cz - 2, "lime_wool"), (cx + 5, cz + 3, "green_wool")):
        for dz in range(0, 4):
            bp.set(tx - 1, 1, tz + dz, col)
            bp.set(tx + 1, 1, tz + dz, col)
            bp.set(tx, 2, tz + dz, col)
            bp.set(tx, 1, tz + dz, AIR)
        bp.set(tx, 0, tz + 3, "jungle_planks")
        bp.set(tx, 1, tz + 3, "white_carpet")
    bp.set(cx - 4, 1, cz + 4, MOD["waystone"])
    bp.set(cx - 3, 1, cz + 5, "candle[candles=3,lit=true,waterlogged=false]")
    bp.chest(cx + 6, 1, cz - 4, "west", loot=LOOT + "va_camp")
    bp.barrel(cx + 6, 1, cz - 3, "up")
    bp.set(cx + 7, 1, cz - 3, "composter[level=4]")
    bp.set(cx + 6, 1, cz - 2, "crafting_table")
    bp.set(cx + 4, 1, cz - 5, "lectern[facing=south,has_book=false,powered=false]")
    for (x, z, p) in ((cx + 3, cz - 5, "potted_azalea_bush"), (cx + 2, cz - 5, "potted_fern"),
                      (cx + 1, cz - 5, "potted_flowering_azalea_bush")):
        bp.set(x, 1, z, "jungle_slab[type=bottom,waterlogged=false]")
        bp.set(x, 2, z, p)
    for (x, z) in ((cx - 6, cz + 3), (cx + 2, cz - 7), (cx + 8, cz + 1), (cx - 9, cz - 4)):
        lamp_post(S, x, 1, z, 2)
    # moss, azalea and dripleaf round the walls of the cave
    for x, z, top in S.side_cells:
        h = hash01(x, z, 65)
        if bp.get(x, 1, z) != AIR or abs(x - cx) + abs(z - cz) < 7:
            continue
        if h < 0.12:
            bp.set(x, 1, z, MOSS_C)
        elif h < 0.16:
            bp.set(x, 1, z, "azalea")
        elif h < 0.18:
            bp.set(x, 1, z, "small_dripleaf[facing=north,half=lower,waterlogged=false]")
            bp.set(x, 2, z, "small_dripleaf[facing=north,half=upper,waterlogged=false]")
        if 0.5 < h < 0.56 and bp.get(x, top + 1, z) not in (None, AIR):
            berries(S, x, z, top, max(3, top - 3), 1)


# ------------------------------------------------------------------ the lake and the station
def lake(S):
    """The lily lake: clay and moss bed, deep by the dome, shallow by the shore; lily pads, dripleaf islands."""
    bp = S.bp
    cells = [(x, z) for (x, z), (fy, top) in S.cmap.items() if fy == 0 and in_lake(x, z) and ddist(x, z) >= 27.5]
    cs = set(cells)
    S.lake = cs
    for (x, z) in cells:
        # depth: 2 at the shore, 4 toward the dome and under the cornice
        edge = min(abs(x - a) + abs(z - b) for (a, b) in ((x + 3, z), (x - 3, z), (x, z + 3), (x, z - 3))
                   if (a, b) not in cs) if any(n not in cs for n in ((x + 3, z), (x - 3, z), (x, z + 3),
                                                                     (x, z - 3))) else 4
        depth = 2 if edge <= 1 else (3 if edge <= 2 else 4)
        if ddist(x, z) < 34:
            depth = 4
        bed = -depth - 1
        for y in range(bed + 1, 1):
            bp.set(x, y, z, WATER)
        bp.set(x, bed, z, CLAY if hash01(x, z, 31) < 0.5 else (MOSS if hash01(x, z, 32) < 0.5 else "gravel"))
        S.lining.discard((x, 0, z))
        if depth >= 3 and hash01(x, z, 33) < 0.08:
            bp.set(x, bed + 1, z, "seagrass")
    # seal the sides of the basin
    for (x, z) in cells:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in cs:
                continue
            for y in range(-5, 0):
                b = bp.get(n[0], y, n[1])
                if b is None or b == AIR:
                    bp.set(n[0], y, n[1], CLAY if y > -2 else rock(n[0], y, n[1]))
            if bp.get(n[0], 0, n[1]) in (None, AIR) and n not in S.cmap:
                bp.set(n[0], 0, n[1], rock(n[0], 0, n[1]))
        for y in range(-6, -4):
            if bp.get(x, y, z) is None:
                bp.set(x, y, z, "stone")
    # lily pads
    for (x, z) in cells:
        if hash01(x, z, 34) < 0.16 and bp.get(x, 1, z) == AIR:
            bp.set(x, 1, z, "lily_pad")
    # dripleaf islands: clay humps with big dripleaf, moss and a froglight under moss
    for (ix, iz, r) in ((-16, 26, 2.6), (15, 30, 2.2), (-8, 34, 1.8), (20, 18, 2.0), (-21, 17, 1.8)):
        for x in range(ix - 3, ix + 4):
            for z in range(iz - 3, iz + 4):
                d = math.hypot(x - ix, z - iz)
                if d > r or (x, z) not in cs:
                    continue
                for y in range(-4, 1):
                    bp.set(x, y, z, CLAY if y < 0 else MOSS)
                bp.set(x, 1, z, AIR)
                h = hash01(x, z, 35)
                if d < 0.6:
                    bp.set(x, 0, z, FROG_V)
                elif h < 0.45:
                    tall = 1 + int(h * 6) % 3
                    for y in range(1, 1 + tall):
                        bp.set(x, y, z, "big_dripleaf_stem[facing=%s,waterlogged=false]" % ("north", "east",
                                                                                            "south", "west")[int(h * 40) % 4])
                    bp.set(x, 1 + tall, z, "big_dripleaf[facing=%s,tilt=none,waterlogged=false]" % ("north", "east",
                                                                                                "south", "west")[int(h * 40) % 4])
                elif h < 0.7:
                    bp.set(x, 1, z, MOSS_C)
                elif h < 0.8:
                    bp.set(x, 1, z, "small_dripleaf[facing=south,half=lower,waterlogged=false]")
                    bp.set(x, 2, z, "small_dripleaf[facing=south,half=upper,waterlogged=false]")


def station(S):
    """The lake shore station (hub): a brass-and-glass pavilion on a stone plinth, an arcade toward the lake, a
    waystone in the hall, the observation deck upstairs, a pier and the causeway to the dome's south doors."""
    bp = S.bp
    x0, x1, z0, z1 = -14, 14, 44, 56
    # plinth and floor
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            bp.set(x, 0, z, PA if (x + z) % 2 else SB)
            for y in range(-3, 0):
                if bp.get(x, y, z) in (None, AIR, WATER):
                    bp.set(x, y, z, SB)
    # walls: masonry base 3 high, brass frame and glass to the cornice at y 9; the north face is an arcade
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(1, 15):
                bp.set(x, y, z, AIR)
            if not edge:
                continue
            post = (x - x0) % 4 == 0 if z in (z0, z1) else (z - z0) % 4 == 0
            corner = x in (x0, x1) and z in (z0, z1)
            for y in range(1, 10):
                if corner:
                    spec = IRON if y < 9 else BRASS
                elif z == z0:
                    # the arcade: piers every 4, round-headed openings 3 wide and 6 high
                    if post:
                        spec = mas(x, y, z) if y < 3 else (BRASS if y in (3, 8) else IRON)
                    else:
                        spec = AIR if y <= 6 else (BRASS_STAIRS + "[facing=%s,half=top,shape=straight,"
                                                   "waterlogged=false]" % ("east" if (x - x0) % 4 == 1 else "west")
                                                   if y == 7 and (x - x0) % 4 != 2 else
                                                   (GLASS if y == 7 else IRON))
                elif post:
                    spec = mas(x, y, z) if y < 3 else (BRASS if y in (3, 8) else IRON)
                elif y < 3:
                    spec = mas(x, y, z)
                elif y in (3, 8):
                    spec = BRASS
                else:
                    spec = GLASS
                bp.set(x, y, z, spec)
            bp.set(x, 9, z, IRON)
    # the upper floor (feet 10): a glass gallery over the hall, open deck on the lake side
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if z0 + 1 <= z <= z1 - 1 and x0 + 1 <= x <= x1 - 1:
                bp.set(x, 9, z, "jungle_planks" if (x + z) % 5 else MAHOGANY)
            if z >= z0 + 5:
                edge = x in (x0, x1) or z == z1
                for y in range(10, 15):
                    if edge:
                        bp.set(x, y, z, GLASS if 11 <= y <= 13 and (x - x0) % 4 and (z - z0) % 4 else
                               (BRASS if y == 14 else IRON))
                # glass roof: a low pitch
                ry = 15 + min(z - (z0 + 5), z1 - z) // 3
                bp.set(x, min(ry, 16), z, GLASS if (x - x0) % 4 else BRASS)
            else:
                if x in (x0, x1) or z == z0:
                    bp.set(x, 10, z, IRON_WALL)
    # the inner wall of the upper gallery toward the deck, with a door
    for x in range(x0 + 1, x1):
        for y in range(10, 15):
            bp.set(x, y, z0 + 5, GLASS if y in (11, 12, 13) else IRON)
    for x in (-1, 0, 1):
        for y in range(10, 13):
            bp.set(x, y, z0 + 5, AIR)
    # stairs up (west side of the hall): south to north, feet 1 -> 10
    for k in range(9):
        z = z1 - 2 - k
        for x in (x0 + 1, x0 + 2):
            bp.set(x, k, z, stair("jungle_stairs", "north"))
            for y in range(k + 1, k + 5):
                if y < 10 or z < z0 + 5 or True:
                    bp.set(x, y, z, AIR)
    for x in (x0 + 1, x0 + 2):
        for z in range(z1 - 10, z1 - 1):
            if bp.get(x, 9, z) not in (None, AIR) and z > z1 - 11:
                bp.set(x, 9, z, AIR)
        bp.set(x, 9, z1 - 11, "jungle_planks")
    for z in range(z1 - 10, z1 - 1):
        bp.set(x0 + 3, 10, z, IRON_WALL)
    # doors: south (the tunnel), west and east (the shores)
    for (x, z) in ((-1, z1), (0, z1), (1, z1)):
        for y in range(1, 5):
            bp.set(x, y, z, AIR)
    for (x, z) in ((x0, 49), (x0, 50), (x0, 51), (x1, 49), (x1, 50), (x1, 51)):
        for y in range(1, 5):
            bp.set(x, y, z, AIR)
    # the hall: waystone, map table, specimen crates, benches facing the view
    bp.set(0, 1, 52, MOD["waystone"])
    bp.set(-1, 1, 52, "candle[candles=2,lit=true,waterlogged=false]")
    for x in (4, 5, 6):
        bp.set(x, 1, 50, TABLE)
    bp.set(5, 2, 50, "cartography_table") if False else None
    bp.set(4, 1, 51, stair("jungle_stairs", "north"))
    bp.set(6, 1, 51, stair("jungle_stairs", "north"))
    bp.chest(12, 1, 54, "west", loot=LOOT + "va_station")
    bp.barrel(12, 1, 53, "up")
    bp.barrel(12, 2, 53, "up")
    bp.set(11, 1, 55, "composter[level=6]")
    for x in (-8, -5, 5, 8):
        bp.set(x, 1, 46, stair("jungle_stairs", "south"))
    for (x, z, p) in ((-12, 46, "potted_fern"), (12, 46, "potted_azalea_bush"), (-12, 54, "potted_red_mushroom"),
                      (9, 55, "potted_flowering_azalea_bush")):
        bp.set(x, 1, z, p)
    bp.set(2, 1, 54, "lectern[facing=north,has_book=false,powered=false]")
    # the deck upstairs: a telescope on a tripod looking at the dome
    bp.set(0, 10, 46, IRON_WALL)
    bp.set(0, 11, 46, BRASS)
    bp.set(0, 11, 45, "lightning_rod[facing=north,powered=false,waterlogged=false]")
    bp.chest(-12, 10, 55, "east", loot=LOOT + "va_deck")
    for x in (-10, -6, 6, 10):
        bp.set(x, 10, 54, stair("jungle_stairs", "north"))
    # chandeliers in the hall
    for (x, z) in ((-6, 50), (6, 50)):
        bp.set(x, 8, z, CHANDELIER)
    for (x, z) in ((-6, 53), (6, 53), (0, 48)):
        bp.set(x, 8, z, HANG_LAMP)
    # the pier and the causeway north across the lake to the dome's doors
    for z in range(9, z0):
        for x in range(-2, 3):
            edge = abs(x) == 2
            bp.set(x, 0, z, (SB if edge else (PA if z % 2 else TB)))
            for y in range(-4, 0):
                if bp.get(x, y, z) in (None, WATER, AIR) and (abs(x) == 2 or z % 8 == 0):
                    bp.set(x, y, z, SB if y > -3 else "stone")
            bp.set(x, 1, z, AIR)
            if edge and z % 4 == 0:
                bp.set(x, 1, z, IRON_WALL)
                bp.set(x, 2, z, IRON_WALL)
                bp.set(x, 3, z, LANT)
            elif edge:
                bp.set(x, 1, z, IRON_WALL)
    S.causeway = (9, z0)


# ------------------------------------------------------------------ the dome
def shell_kind(x, y, z):
    """Material of a shell cell of the palm house: brass ribs every 22.5 degrees, dark iron rings, glass between."""
    a = math.degrees(math.atan2(z - DCZ, x - DCX)) % 360
    da = min(a % 22.5, 22.5 - a % 22.5)
    d = max(1.0, ddist(x, z))
    arc = math.radians(da) * d
    major = min(a % 90, 90 - a % 90) * math.radians(1) * d < 1.6
    if arc < 0.75 or major:
        return patina(x, y, z)
    if y <= DRUM_TOP:
        if y % 5 == 0:
            return IRON
        return GLASS
    ring = (y - DRUM_TOP) % 6 == 0
    if ring:
        return IRON
    return GLASS


def dome(S):
    """The palm house: a masonry plinth (y 0..6), a glass drum between brass ribs to the entablature at y 20, the
    cornice deck outside it, the dome (crown ~50) and the oculus collar running up into the rock."""
    bp = S.bp
    R = 32
    for x in range(DCX - R, DCX + R + 1):
        for z in range(DCZ - R, DCZ + R + 1):
            d = ddist(x, z)
            if d >= 32:
                continue
            # interior: floor ring and pool
            if d < 26.5:
                for y in range(1, 60):
                    if (d / 26.5) ** 2 + (max(0, y - DRUM_TOP) / (DOME_H - 1.0)) ** 2 < 1:
                        bp.set(x, y, z, AIR)
                if d < POOL_R:
                    for y in range(-3, 1):
                        bp.set(x, y, z, WATER)
                    bp.set(x, -4, z, CLAY if hash01(x, z, 41) < 0.6 else MOSS)
                    bp.set(x, -5, z, "stone")
                    if d > POOL_R - 1.2:
                        for y in range(-4, 1):
                            bp.set(x, y, z, PA if y == 0 else SB)
                else:
                    bp.set(x, 0, z, (MOSS if hash01(x, z, 42) < 0.5 else ROOTED) if d < 25.5 else PA)
                    for y in range(-3, 0):
                        bp.set(x, y, z, "stone")
                continue
            if d < 27.5:
                # the shell: plinth, drum, entablature
                for y in range(0, DRUM_TOP + 1):
                    if y <= 6:
                        spec = mas(x, y, z) if y not in (6,) else PA
                    elif y == DRUM_TOP or y == DRUM_TOP - 1:
                        spec = BRASS if y == DRUM_TOP else IRON
                    else:
                        spec = shell_kind(x, y, z)
                    bp.set(x, y, z, spec)
                bp.set(x, -1, z, SB)
            elif d < 31.5:
                # the cornice deck: tread plate with a brass edge, brackets under it at the ribs
                bp.set(x, DRUM_TOP, z, TREAD if d < 30.5 else BRASS)
                bp.set(x, DRUM_TOP - 1, z, IRON if d < 28.5 else AIR)
                if d >= 30.5:
                    bp.set(x, DRUM_TOP + 1, z, IRON_WALL)
    # the dome above the entablature
    for x in range(DCX - 28, DCX + 29):
        for z in range(DCZ - 28, DCZ + 29):
            d = ddist(x, z)
            for y in range(DRUM_TOP + 1, DRUM_TOP + int(DOME_H) + 2):
                t = (y - DRUM_TOP) / DOME_H
                outer = (d / 27.5) ** 2 + t ** 2 <= 1.0
                inner = (d / 26.5) ** 2 + ((y - DRUM_TOP) / (DOME_H - 1.0)) ** 2 < 1.0
                if outer and not inner:
                    if d < 5.5:
                        continue             # the oculus (the collar is written below)
                    bp.set(x, y, z, shell_kind(x, y, z))
    # major ribs stand proud of the shell (E, S, W, N), from the plinth to the crown
    for ang in (0, 90, 180, 270):
        t = math.radians(ang)
        ux, uz = math.cos(t), math.sin(t)
        for y in range(1, DRUM_TOP + int(DOME_H)):
            tt = (y - DRUM_TOP) / DOME_H if y > DRUM_TOP else 0.0
            if tt >= 1:
                break
            r = 27.5 * math.sqrt(max(0.0, 1 - tt ** 2)) if y > DRUM_TOP else 27.5
            if r < 6:
                break
            for w in (-1, 0, 1):
                px = int(round(DCX + ux * (r + 0.5) - uz * w))
                pz = int(round(DCZ + uz * (r + 0.5) + ux * w))
                if y in (DRUM_TOP, DRUM_TOP + 1) and r >= 27:
                    continue
                if bp.get(px, y, pz) in (None, AIR):
                    bp.set(px, y, pz, patina(px, y, pz) if w else IRON)
    # the collar: a brass drum round the oculus, rising into the roof rock
    for x in range(-7, 8):
        for z in range(DCZ - 7, DCZ + 8):
            d = ddist(x, z)
            if d > 6.5 or (x, z) not in S.cmap:
                continue
            top = S.cmap[(x, z)][1] + 1
            y0 = DRUM_TOP + int(DOME_H * math.sqrt(max(0.0, 1 - (d / 27.5) ** 2))) - 1
            for y in range(y0, top + 1):
                if d >= 4.5:
                    bp.set(x, y, z, BRASS if y % 4 else IRON)
                    S.lining.discard((x, y, z))
    # ribs into the rock: fins on the 16 ribs, from the shoulder up to the roof
    for k in range(16):
        t = math.radians(k * 22.5)
        ux, uz = math.cos(t), math.sin(t)
        for y in range(DRUM_TOP + 8, DRUM_TOP + int(DOME_H)):
            tt = (y - DRUM_TOP) / DOME_H
            r = 27.5 * math.sqrt(max(0.0, 1 - tt ** 2))
            if r < 7:
                break
            for o in range(1, 12):
                px = int(round(DCX + ux * (r + o)))
                pz = int(round(DCZ + uz * (r + o)))
                b = bp.get(px, y, pz)
                if b == AIR:
                    if bp.get(px, y + 1, pz) not in (None, AIR) and (px, y + 1, pz) in S.lining or o > 1:
                        pass
                    # a fin only where the roof is close above (it carries it)
                    top = S.cmap.get((px, pz), (0, 0))[1]
                    if top - y <= 6:
                        for yy in range(y, top + 1):
                            if bp.get(px, yy, pz) == AIR:
                                bp.set(px, yy, pz, IRON if yy == y else patina(px, yy, pz))
                    break
                elif b is None:
                    break


def dome_doors(S):
    """The great south doors (iron, lever inside only) onto the causeway; the cornice door (mist) and the north door
    (sealed bars) at feet 21."""
    bp = S.bp
    # south doors at z = DCZ + 27 (the shell), x -1..1, feet 1: a portal 3 wide, 5 high in a brass frame
    zs = DCZ + 27
    for x in range(-3, 4):
        for z in range(zs - 1, zs + 2):
            for y in range(1, 8):
                if abs(x) <= 1 and y <= 5:
                    bp.set(x, y, z, AIR)
                elif abs(x) == 2 or y in (6, 7):
                    bp.set(x, y, z, BRASS if y != 7 else IRON)
    for x in (-1, 0, 1):
        bp.set(x, 0, zs, PA)
        bp.set(x, 0, zs - 1, PA)
        bp.set(x, 0, zs + 1, PA)
    bp.set(-1, 1, zs, "iron_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
    bp.set(-1, 2, zs, "iron_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
    bp.set(1, 1, zs, "iron_door[facing=north,half=lower,hinge=right,open=false,powered=false]")
    bp.set(1, 2, zs, "iron_door[facing=north,half=upper,hinge=right,open=false,powered=false]")
    bp.set(0, 1, zs, "iron_bars")
    bp.set(0, 2, zs, "iron_bars")
    for y in (3, 4, 5):
        for x in (-1, 0, 1):
            bp.set(x, y, zs, "iron_bars")
    # the lever inside only (on the brass jamb, two blocks in)
    bp.set(-2, 2, zs - 1, "lever[face=wall,facing=north,powered=false]")
    bp.set(2, 2, zs - 1, "lever[face=wall,facing=north,powered=false]")
    # the inner steps from the pool ring to the doors
    for x in range(-2, 3):
        for z in range(zs - 5, zs - 1):
            bp.set(x, 0, z, PA)
            for y in range(-3, 0):
                bp.set(x, y, z, SB)
            bp.set(x, 1, z, AIR)


# ------------------------------------------------------------------ the arena: the lily pad and the sun-lamp
def pad_kind(x, z):
    d = ddist(x, z)
    a = math.degrees(math.atan2(z - DCZ, x - DCX)) % 360
    vein = min(a % 30, 30 - a % 30) * math.radians(1) * d < 0.6 and d > 3
    ring = abs(d - 7) < 0.5 or abs(d - 12) < 0.5
    if d < 1.5:
        return BRASS
    if (vein and ring) or (d > 2.5 and abs(d - 4) < 0.5 and hash01(x, z, 51) < 0.25):
        return FROG_V if hash01(x, z, 52) < 0.5 else FROG_P
    if vein:
        return "lime_terracotta"
    if ring:
        return "green_terracotta"
    return MOSS if hash01(x, z, 53) < 0.85 else "green_concrete"


def arena(S):
    """The giant lily pad (r 16) on its brass pedestal over the pool, the upturned rim, the inner rib bridges."""
    bp = S.bp
    deck = COR - 1
    for x in range(DCX - 17, DCX + 18):
        for z in range(DCZ - 17, DCZ + 18):
            d = ddist(x, z)
            if d > PAD_R + 0.5:
                continue
            notch = abs(z - DCZ) <= 1 and x > DCX + 13       # the notch where the east bridge lands
            if d > PAD_R - 0.5 and not notch:
                bp.set(x, deck, z, "red_terracotta")
                bp.set(x, deck + 1, z, "red_terracotta")
                bp.set(x, deck + 2, z, "mangrove_slab[type=bottom,waterlogged=false]")
            else:
                bp.set(x, deck, z, pad_kind(x, z))
            # the underside: radial ribs of the leaf, red, and brass spokes
            a = math.degrees(math.atan2(z - DCZ, x - DCX)) % 360
            rib = min(a % 30, 30 - a % 30) * math.radians(1) * d < 0.8
            if rib and d > 5:
                depth = 1 + int(max(0.0, (PAD_R - d)) / 5)
                for y in range(deck - depth, deck):
                    bp.set(x, y, z, "mangrove_planks" if (int(a) // 30) % 3 else BRASS)
    # the north notch for the herbarium bridge too
    for x in range(DCX - 1, DCX + 2):
        for z in range(DCZ - 17, DCZ - 14):
            if ddist(x, z) <= PAD_R + 0.5:
                bp.set(x, deck, z, pad_kind(x, z))
                bp.set(x, deck + 1, z, AIR)
                bp.set(x, deck + 2, z, AIR)
    # the pedestal: a fluted brass column from the pool bed, flaring under the leaf
    for x in range(DCX - 5, DCX + 6):
        for z in range(DCZ - 5, DCZ + 6):
            d = ddist(x, z)
            for y in range(-4, deck):
                r = 2.5 + max(0, y - (deck - 6)) * 0.55
                if d <= r:
                    a = math.degrees(math.atan2(z - DCZ, x - DCX)) % 360
                    flute = (int(a) // 30) % 2 == 0
                    spec = (VERD if y < 3 else (BRASS if flute else COPPER)) if d > r - 1.2 else IRON
                    if y % 8 == 3 and d > r - 1.2:
                        spec = IRON
                    bp.set(x, y, z, spec)
    # four slender stays from the pool floor to the rim, like the stems of the pad
    for ang in (45, 135, 225, 315):
        t = math.radians(ang)
        for y in range(-4, deck):
            r = 4 + (y + 4) * (PAD_R - 5) / (deck + 4)
            px = int(round(DCX + math.cos(t) * r))
            pz = int(round(DCZ + math.sin(t) * r))
            bp.set(px, y, pz, IRON if y % 6 else BRASS)
    # the inner bridges: east (from the cornice door) and north (to the herbarium)
    for x in range(DCX + 14, DCX + 27):
        for z in range(DCZ - 1, DCZ + 2):
            bp.set(x, deck, z, TREAD if abs(z - DCZ) < 1 else BRASS)
            bp.set(x, deck - 1, z, IRON if abs(z - DCZ) == 1 else AIR)
            for y in range(deck + 1, deck + 5):
                bp.set(x, y, z, AIR)
        for z in (DCZ - 2, DCZ + 2):
            bp.set(x, deck, z, IRON)
            bp.set(x, deck + 1, z, IRON_WALL)
    for z in range(DCZ - 26, DCZ - 13):
        for x in range(DCX - 1, DCX + 2):
            bp.set(x, deck, z, TREAD if abs(x - DCX) < 1 else BRASS)
            bp.set(x, deck - 1, z, IRON if abs(x - DCX) == 1 else AIR)
            for y in range(deck + 1, deck + 5):
                bp.set(x, y, z, AIR)
        for x in (DCX - 2, DCX + 2):
            bp.set(x, deck, z, IRON)
            bp.set(x, deck + 1, z, IRON_WALL)
    # the cornice door (east): a portal through the shell, the mist across it
    for x in range(DCX + 25, DCX + 29):
        for z in range(DCZ - 2, DCZ + 3):
            for y in range(deck + 1, deck + 7):
                if abs(z - DCZ) <= 1 and y <= deck + 4:
                    bp.set(x, y, z, AIR)
                elif x >= DCX + 26:
                    bp.set(x, y, z, BRASS if abs(z - DCZ) == 2 or y == deck + 6 else IRON)
        for z in range(DCZ - 1, DCZ + 2):
            bp.set(x, deck, z, TREAD)
    bp.mist(DCX + 26, deck + 1, DCZ - 1, DCX + 26, deck + 4, DCZ + 1)
    # the north door: sealed bars to the herbarium
    for z in range(DCZ - 29, DCZ - 25):
        for x in range(DCX - 2, DCX + 3):
            for y in range(deck + 1, deck + 7):
                if abs(x - DCX) <= 1 and y <= deck + 4:
                    bp.set(x, y, z, AIR)
                else:
                    bp.set(x, y, z, BRASS if abs(x - DCX) == 2 or y == deck + 6 else IRON)
        for x in range(DCX - 1, DCX + 2):
            bp.set(x, deck, z, TREAD)
    for x in range(DCX - 1, DCX + 2):
        for y in range(deck + 1, deck + 4):
            bp.set(x, y, DCZ - 27, MOD["vault_bars"])
    # rim lanterns and froglights; flowers on the pad
    for k in range(12):
        t = math.radians(k * 30 + 15)
        x = int(round(DCX + math.cos(t) * (PAD_R - 0.2)))
        z = int(round(DCZ + math.sin(t) * (PAD_R - 0.2)))
        if bp.get(x, deck + 2, z) and bp.get(x, deck + 2, z).endswith("slab"):
            bp.set(x, deck + 2, z, "red_terracotta")
            bp.set(x, deck + 3, z, LANT)
    for k in range(10):
        t = math.radians(k * 36 + 7)
        r = 9.5 + (k % 3)
        x = int(round(DCX + math.cos(t) * r))
        z = int(round(DCZ + math.sin(t) * r))
        if bp.get(x, deck, z) == MOSS and bp.get(x, deck + 1, z) == AIR:
            bp.set(x, deck + 1, z, ("blue_orchid", "lily_of_the_valley", "pink_petals[facing=north,flower_amount=4]",
                                    "allium")[k % 4])
    bp.boss_seal(DCX, deck, DCZ, BOSS, 17)
    sun_lamp(S)


def sun_lamp(S):
    """The sun-lamp: a giant brass lamp hanging on chains from the dome's crown: a cage of brass hoops round a core of
    shroomlight and sea lanterns, a ring of glass lenses, a reflector dish open below."""
    bp = S.bp
    top = DRUM_TOP + int(DOME_H) - 1
    cy = 39
    # chains from the oculus collar
    for (dx, dz) in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        for y in range(cy + 5, top + 6):
            if bp.get(DCX + dx, y, DCZ + dz) in (AIR,):
                bp.set(DCX + dx, y, DCZ + dz, CHAIN)
    for y in range(cy + 4, top + 6):
        if bp.get(DCX, y, DCZ) == AIR:
            bp.set(DCX, y, DCZ, CHAIN)
    for x in range(DCX - 6, DCX + 7):
        for z in range(DCZ - 6, DCZ + 7):
            for y in range(cy - 4, cy + 5):
                dx, dy, dz = x - DCX, y - cy, z - DCZ
                r = math.sqrt(dx * dx + dy * dy * 1.3 + dz * dz)
                h = math.hypot(dx, dz)
                if r < 2.6:
                    bp.set(x, y, z, SHROOM if (dx + dy + dz) % 2 else SEA)
                elif r < 3.6 and dy >= -1:
                    bp.set(x, y, z, "yellow_stained_glass" if (dx + dz) % 2 else GLASS)
                elif 4.5 <= r < 5.4 and (dy in (-1, 2) or abs(dx) == 0 or abs(dz) == 0):
                    bp.set(x, y, z, BRASS if dy != 2 else COPPER)
                elif dy == -3 and 3.0 <= h < 6.5:
                    bp.set(x, y, z, IRON if h > 5.6 else ("orange_stained_glass" if (dx + dz) % 2 else GLASS))
                elif dy == 4 and h < 3.5:
                    bp.set(x, y, z, BRASS if h < 2.5 else IRON)
    # the lens arms: four brass arms carrying round lenses outward
    for (ux, uz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for o in range(5, 9):
            bp.set(DCX + ux * o, cy, DCZ + uz * o, BRASS)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                px = DCX + ux * 9 + (uz * a)
                pz = DCZ + uz * 9 + (ux * a)
                bp.set(px, cy + b, pz, SEA if a == 0 and b == 0 else "light_blue_stained_glass")
    # a ring of hanging lamps lower down, over the pad
    for k in range(8):
        t = math.radians(k * 45 + 22.5)
        x = int(round(DCX + math.cos(t) * 7))
        z = int(round(DCZ + math.sin(t) * 7))
        for y in range(cy - 7, cy - 3):
            bp.set(x, y, z, CHAIN)
        bp.set(x, cy - 8, z, SHROOM)
        bp.set(x, cy - 3, z, BRASS)


# ------------------------------------------------------------------ the dome interior: palms, planters, berries
def palm(S, x, f, z, h, lean):
    """A palm: a curved trunk of jungle wood, a crown of jungle-leaf fronds drooping outward, a cluster of cocoa."""
    bp = S.bp
    lx, lz = lean
    px, pz = x, z
    for k in range(h):
        t = k / max(1, h - 1)
        px = x + int(round(lx * t * t * 3))
        pz = z + int(round(lz * t * t * 3))
        bp.set(px, f + k, pz, "jungle_wood[axis=y]" if k % 3 else "stripped_jungle_wood[axis=y]")
    cy = f + h
    bp.set(px, cy, pz, JUNGLE_LEAVES)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
        for o in range(1, 5):
            y = cy + (1 if o == 1 else 0) - max(0, o - 2)
            fx, fz = px + dx * o, pz + dz * o
            if bp.get(fx, y, fz) == AIR:
                bp.set(fx, y, fz, JUNGLE_LEAVES)
    bp.set(px, cy + 1, pz, JUNGLE_LEAVES)
    for (dx, dz, fc) in ((1, 0, "west"), (-1, 0, "east")):
        if bp.get(px + dx, cy - 1, pz + dz) == AIR:
            bp.set(px + dx, cy - 1, pz + dz, "cocoa[age=2,facing=%s]" % fc)


def dome_garden(S):
    """The palm ring round the pool: planters of moss and rooted dirt, palms, ferns, glow berries hanging from the
    shell's ribs, spore blossoms under the dome, froglights in the walk."""
    bp = S.bp
    for x in range(DCX - 27, DCX + 28):
        for z in range(DCZ - 27, DCZ + 28):
            d = ddist(x, z)
            if not POOL_R <= d < 26.5 or bp.get(x, 1, z) != AIR:
                continue
            a = math.degrees(math.atan2(z - DCZ, x - DCX)) % 360
            walk = 22.5 <= d < 24.0
            if walk:
                bp.set(x, 0, z, PA if hash01(x, z, 61) < 0.7 else TB)
                if hash01(x, z, 62) < 0.04:
                    bp.set(x, 0, z, FROG_O)
            elif d >= 24.0:
                h = hash01(x, z, 63)
                bp.set(x, 0, z, MOSS)
                if h < 0.25:
                    bp.set(x, 1, z, "fern")
                elif h < 0.32:
                    bp.set(x, 1, z, "large_fern[half=lower]")
                    bp.set(x, 2, z, "large_fern[half=upper]")
                elif h < 0.4:
                    bp.set(x, 1, z, MOSS_C)
                elif h < 0.43:
                    bp.set(x, 1, z, "azalea")
    for k in range(10):
        a = math.radians(k * 36 + 10)
        x = int(round(DCX + math.cos(a) * 25))
        z = int(round(DCZ + math.sin(a) * 25))
        if abs(x - DCX) < 4 and z > DCZ:
            continue
        palm(S, x, 1, z, 12 + (k * 7) % 5, (-math.cos(a) * 0.8, -math.sin(a) * 0.8))
    # spore blossoms and glow berries under the dome's iron rings
    for x in range(DCX - 26, DCX + 27):
        for z in range(DCZ - 26, DCZ + 27):
            d = ddist(x, z)
            if d > 26 or d < 7:
                continue
            h = hash01(x, z, 64)
            # first solid above the walk
            y = 2
            while y < 60 and bp.get(x, y, z) == AIR:
                y += 1
            if y >= 60 or y < 24:
                continue
            under = y - 1
            if h < 0.035:
                bp.set(x, under, z, SPORE)
            elif h < 0.085 and d > 17:
                berries(S, x, z, under, max(COR + 5 if d < 17.5 else 6, under - 6 - int(h * 100) % 6), 2)


# ------------------------------------------------------------------ the waterfall and the aqueduct
def aqueduct(S):
    """The irrigation aqueduct: a stone channel on arches from a brass sluice in the west wall, across the terrace
    and the shore, to a spillway that pours the waterfall into the lake."""
    bp = S.bp
    zc = 33
    xw, xe = -70, -22
    y0 = 19                                   # channel floor; water at y 20
    for x in range(xw, xe + 1):
        for z in range(zc - 2, zc + 3):
            side = abs(z - zc) == 2
            bp.set(x, y0, z, SB if not side else mas(x, y0, z, 10))
            bp.set(x, y0 - 1, z, SB)
            if side:
                bp.set(x, y0 + 1, z, PA)
                bp.set(x, y0 + 2, z, SB_W if x % 3 else LANT)
            else:
                bp.set(x, y0 + 1, z, WATER)
                for y in range(y0 + 2, y0 + 5):
                    if bp.get(x, y, z) in (None,) or (x, y, z) in S.lining:
                        bp.set(x, y, z, AIR)
                        S.lining.discard((x, y, z))
        # arches: piers every 9, round arches between
        fy = S.floor(x, zc)
        if fy is None:
            fy = 7
        ph = (x - xe) % 9
        for z in range(zc - 2, zc + 3):
            if ph in (0, 1):
                y_lo = -4 if (x, z) in S.lake else fy + 1
                for y in range(y_lo, y0 - 1):
                    bp.set(x, y, z, mas(x, y, z, fy))
            else:
                u = min(ph - 1, 8 - ph) if ph < 8 else 0
                arch_top = y0 - 2 - max(0, 3 - u)
                for y in range(arch_top, y0 - 1):
                    bp.set(x, y, z, mas(x, y, z, fy) if y < y0 - 2 else SB)
    # the sluice: a brass outlet in the cavern wall with a valve wheel
    for z in range(zc - 2, zc + 3):
        for y in range(y0, y0 + 5):
            if bp.get(xw - 1, y, z) is None or (xw - 1, y, z) in S.lining:
                bp.set(xw - 1, y, z, BRASS if y in (y0, y0 + 4) or abs(z - zc) == 2 else IRON)
    bp.set(xw, y0 + 3, zc, W + "valve_wheel") if False else None
    # the spillway: a brass lip, the fall to the lake
    for z in range(zc - 1, zc + 2):
        bp.set(xe + 1, y0, z, BRASS)
        bp.set(xe + 1, y0 + 1, z, WATER)
        bp.set(xe + 2, y0, z, BRASS_SLAB + "[type=top,waterlogged=false]")
        for y in range(1, y0):
            if bp.get(xe + 2, y, z) == AIR:
                bp.set(xe + 2, y, z, FALL)
    # the grotto behind the fall: a niche in the terrace face under the aqueduct's end pier
    S.aq = (xw, xe, zc, y0)


def grotto(S):
    """A mossy grotto in the terrace face by the waterfall pool, a forgotten chest of cuttings."""
    bp = S.bp
    rock_room(S, -43, 17, -38, 23, F, 4, wall=lambda x, y, z: rock(x, y, z), floor=lambda x, z: MOSS,
              ceil=lambda x, z: MOSS)
    for z in (19, 20):
        for y in range(1, 4):
            bp.set(-37, y, z, AIR)
        bp.set(-37, 0, z, MOSS)
    bp.chest(-42, 1, 20, "east", loot=LOOT + "va_grotto")
    bp.set(-42, 1, 18, "glow_lichen[down=true,east=false,north=false,south=false,up=false,west=false,"
                       "waterlogged=false]")
    bp.set(-41, 4, 22, SHROOM)
    bp.set(-40, 4, 18, SHROOM)
    bp.set(-39, 1, 23, "small_dripleaf[facing=east,half=lower,waterlogged=false]")
    bp.set(-39, 2, 23, "small_dripleaf[facing=east,half=upper,waterlogged=false]")
    bp.set(-43, 1, 22, MOSS_C)
    bp.set(-40, 3, 23, "hanging_roots[waterlogged=false]") if False else None


# ------------------------------------------------------------------ the west terrace: stairs, greenhouses, vault
GH = (-60, -44, -4, 28)


def west_terrace(S):
    """The terrace stair from the shore (cut in the face, rising north), the hedge that closes the south strip, and
    the south stair from the greenhouses' one-way door down to the station."""
    bp = S.bp
    # bottom landing (feet 1) open east to the shore, then seven treads north to the strip (feet 8)
    for x in range(-41, -36):
        for z in range(4, 7):
            for y in range(1, 8):
                bp.set(x, y, z, AIR)
            bp.set(x, 0, z, PA)
    for k in range(1, 8):
        z = 4 - k
        for x in range(-41, -38):
            bp.set(x, k, z, stair(SB_ST, "north"))
            for y in range(0, k):
                bp.set(x, y, z, SB)
            for y in range(k + 1, 8):
                bp.set(x, y, z, AIR)
    for z in range(-4, 8):
        for x in (-42, -38):
            for y in range(0, 8):
                if bp.get(x, y, z) is None or (z in (-4, 7) and bp.get(x, y, z) != AIR):
                    bp.set(x, y, z, mas(x, y, z))
            if bp.get(x, 8, z) == AIR and z < 7:
                bp.set(x, 8, z, IRON_WALL)
        for x in range(-41, -38):
            if bp.get(x, 0, z) is None:
                bp.set(x, 0, z, SB)
    for z in (-1, 3):
        bp.set(-42, 5 if z < 2 else 2, z, SHROOM)
        bp.set(-38, 5 if z < 2 else 2, z, SHROOM)
    bp.set(-38, 9, -3, LANT)
    bp.set(-42, 9, -3, LANT)
    for x in range(-43, -36):
        if bp.get(x, 7, 7) not in (None, AIR):
            bp.set(x, 7, 7, MOSS)
            for y in (8, 9, 10):
                bp.set(x, y, 7, FAZ_LEAVES if (x + y) % 3 == 0 else AZ_LEAVES)
    for z in (4, 6):
        lamp_post(S, -37, 1, z, 2)
    # the south stair: from the terrace's south tip (feet 8) east down to the shore (feet 1)
    for j in range(0, 7):
        x = -37 + j
        y = 6 - j
        for z in range(38, 41):
            for yy in range(0, y):
                bp.set(x, yy, z, mas(x, yy, z))
            bp.set(x, y, z, stair(SB_ST, "west"))
            for yy in range(y + 1, y + 5):
                if bp.get(x, yy, z) not in (None,) and yy >= 7 or yy < 8:
                    bp.set(x, yy, z, AIR)
        for z in (37, 41):
            for yy in range(0, y + 1):
                bp.set(x, yy, z, mas(x, yy, z))
            bp.set(x, y + 1, z, MSB_W)
    bp.set(-37, 7, 37, PA)
    bp.set(-37, 7, 41, PA)
    bp.set(-35, 5, 37, LANT)
    bp.set(-35, 5, 41, LANT)
    lamp_post(S, -29, 1, 37, 3)


def greenhouse(S):
    """The propagation greenhouses: two glass spans on a mossy plinth, brass posts every four, glass ridge roofs;
    planting beds in the west span, benches of cuttings in the east span, misting pipes under the ridges."""
    bp = S.bp
    x0, x1, z0, z1 = GH
    spans = ((x0, -52), (-52, x1))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, 7, z, MSB if x in (x0, x1) or z in (z0, z1) else (PA if hash01(x, z, 71) < 0.6 else TB))
            for y in range(8, 20):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
    for (a, b) in spans:
        xm = (a + b) // 2
        for z in range(z0, z1 + 1):
            gable = z in (z0, z1)
            post_z = (z - z0) % 4 == 0
            for x in range(a, b + 1):
                wall = x in (a, b)
                ridge_y = 14 + (4 - abs(x - xm))
                if wall or gable:
                    for y in range(8, 14):
                        if x == -52 and not gable:
                            # the gutter wall between the spans: iron columns, open between
                            spec = (IRON if post_z else AIR) if y < 13 else BRASS
                        elif y == 8:
                            spec = MSB if hash01(x, z, 72) < 0.6 else SB
                        elif y == 13:
                            spec = BRASS
                        elif (wall and post_z) or (gable and (x - a) % 4 == 0):
                            spec = BRASS if y != 11 else IRON
                        else:
                            spec = GLASS
                        bp.set(x, y, z, spec)
                    if gable:
                        for y in range(14, ridge_y):
                            bp.set(x, y, z, GLASS if (x - a) % 4 else BRASS)
                # the roof
                spec = IRON if x == xm else (BRASS if post_z else GLASS)
                if x == a or x == b:
                    spec = BRASS
                bp.set(x, ridge_y, z, spec)
                if x == xm and 1 <= z - z0 < z1 - z0:
                    bp.set(x, ridge_y - 2, z, PIPES if z % 2 else AIR)
            # misting pipes on brass hangers under the ridge
            if post_z and z0 < z < z1:
                bp.set(xm, 17, z, CHAIN)
    # doors: two in the north gable (from the lawn), south (iron, opens from inside only)
    for x in list(range(-49, -46)) + list(range(-57, -54)):
        for y in (8, 9, 10):
            bp.set(x, y, z0, AIR)
    bp.set(-48, 8, z1, "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    bp.set(-48, 9, z1, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    bp.set(-47, 9, z1 - 1, "lever[face=floor,facing=south,powered=false]") if False else None
    bp.set(-46, 8, z1 - 1, SB)
    bp.set(-46, 9, z1 - 1, "lever[face=floor,facing=west,powered=false]")
    # the east span: three-wide aisle, benches of potted cuttings both sides
    pots = ["potted_fern", "potted_azalea_bush", "potted_flowering_azalea_bush", "potted_red_tulip",
            "potted_blue_orchid", "potted_allium", "potted_jungle_sapling", "potted_cornflower", "potted_oxeye_daisy",
            "potted_mangrove_propagule", "potted_lily_of_the_valley", "potted_brown_mushroom", "potted_dandelion"]
    for z in range(z0 + 2, z1 - 1):
        if z in (-5, -4) or z1 - 2 <= z:
            continue
        for x in (-51, -50, -46, -45):
            if (z - z0) % 9 == 0:
                continue
            bp.set(x, 8, z, "jungle_slab[type=top,waterlogged=false]")
            h = hash01(x, z, 73)
            if h < 0.7:
                bp.set(x, 9, z, pots[int(h * 97) % len(pots)])
    for z in range(z0 + 1, z1):
        bp.set(-48, 7, z, PA if z % 5 else FROG_P)
    # the west span: planting beds of rooted dirt and moss, a gravel walk down the middle
    flora = [("azalea",), ("flowering_azalea",), ("fern",), ("torchflower",), ("pink_petals[facing=east,flower_amount=4]",),
             ("large_fern[half=lower]", "large_fern[half=upper]"), ("pitcher_plant[half=lower]", "pitcher_plant[half=upper]"),
             ("small_dripleaf[facing=east,half=lower,waterlogged=false]",
              "small_dripleaf[facing=east,half=upper,waterlogged=false]"), ("lily_of_the_valley",), ("blue_orchid",)]
    for z in range(z0 + 1, z1):
        for x in range(x0 + 1, -52):
            if x == -56:
                bp.set(x, 7, z, "gravel" if z % 6 else FROG_O)
                continue
            if (z - z0) % 10 == 0:
                bp.set(x, 7, z, "gravel")
                continue
            bp.set(x, 7, z, ROOTED if (x + z) % 3 else MOSS)
            h = hash01(x, z, 74)
            if h < 0.62:
                f = flora[int(h * 131) % len(flora)]
                bp.set(x, 8, z, f[0])
                if len(f) > 1:
                    bp.set(x, 9, z, f[1])
    # hanging lamps on chains from the ridges, a chest at the north end, a spawner among the beds
    for (a, b) in spans:
        xm = (a + b) // 2
        for z in range(z0 + 4, z1 - 1, 8):
            bp.set(xm, 16, z, CHAIN)
            bp.set(xm, 15, z, LANT_H)
    bp.chest(-58, 8, z0 + 1, "south", loot=LOOT + "va_greenhouse")
    bp.chest(-46, 8, z1 - 3, "west", loot=LOOT + "va_greenhouse")
    bp.set(-57, 8, 8, AIR)
    bp.spawner(-57, 8, 8, MOB_FROG)
    bp.set(-57, 9, 8, AIR)


def seed_vault(S):
    """The seed vault cut into the west wall: a passage behind a round brass door, a cold room of drawers (barrels),
    seed jars and a sorting table."""
    bp = S.bp
    fl = lambda x, z: PA if (x + z) % 2 else TB
    rock_room(S, -72, -33, -58, -31, TF, 4, floor=fl, wall=lambda x, y, z: mas(x, y, z, TF))
    rock_room(S, -85, -40, -73, -24, TF, 6, floor=fl, wall=lambda x, y, z: TB if y % 4 else PA,
              ceil=lambda x, z: PA)
    # the round door: a brass ring round the passage mouth, the door disc swung open against the wall
    xm = -60
    for z in range(-36, -27):
        for y in range(TF - 1, TF + 7):
            dz, dy = z + 32, y - (TF + 1.5)
            r = math.hypot(dz, dy)
            if 2.6 <= r < 3.8:
                bp.set(xm, y, z, BRASS if r < 3.2 else IRON)
    for z in range(-30, -26):
        pass
    for y in range(TF, TF + 4):
        for z in range(-29, -26):
            if math.hypot(z + 27.5, y - TF - 1.5) < 2.2:
                bp.set(xm + 1, y, z, IRON if (y + z) % 3 else BRASS)
    for z in (-33, -31):
        bp.set(-58, TF + 3, z, LANT_H) if False else None
    # drawers: barrels in the walls, two rows
    for z in range(-39, -24):
        for y in (TF, TF + 1, TF + 2):
            if z in (-33, -32, -31):
                continue
            bp.barrel(-85, y, z, "east")
    for x in range(-84, -73):
        for y in (TF, TF + 1, TF + 2):
            bp.barrel(x, y, -40, "south")
            bp.barrel(x, y, -24, "north")
    # the sorting table, seed jars, two chests
    for x in range(-81, -77):
        bp.set(x, TF, -32, TABLE)
    for (x, z) in ((-81, -33), (-78, -31), (-80, -31)):
        bp.set(x, TF, z, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    bp.chest(-84, TF, -32, "east", loot=LOOT + "va_seedvault")
    bp.chest(-74, TF, -38, "north", loot=LOOT + "va_seedvault")
    bp.set(-76, TF, -27, "potted_cherry_sapling")
    bp.set(-77, TF, -27, "potted_dark_oak_sapling")
    bp.set(-78, TF, -27, "potted_azalea_bush")
    bp.spawner(-75, TF, -28, MOB_SPIDER)
    for (x, z) in ((-82, -36), (-82, -28), (-76, -36), (-76, -30)):
        bp.set(x, TF + 5, z, CHAIN)
        bp.set(x, TF + 4, z, LANT_H)
    for x in (-70, -64):
        bp.set(x, TF + 3, -32, LANT_H)


# ------------------------------------------------------------------ the specimen laboratory
LAB = (-34, -10, -70, -52)


def tank(S, x, z, kind):
    """A specimen jar: a brass base, three blocks of glass, a brass lid with a pipe; inside a plant."""
    bp = S.bp
    f = TF
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(x + dx, f, z + dz, BRASS if dx or dz else IRON)
            for y in range(f + 1, f + 4):
                bp.set(x + dx, y, z + dz, GLASS if dx or dz else AIR)
            bp.set(x + dx, f + 4, z + dz, BRASS_SLAB + "[type=bottom,waterlogged=false]" if dx or dz else BRASS)
    if kind == "kelp":
        bp.set(x, f, z, "sand")
        bp.set(x, f + 1, z, "kelp_plant")
        bp.set(x, f + 2, z, "kelp_plant")
        bp.set(x, f + 3, z, "kelp[age=20]")
    elif kind == "berries":
        bp.set(x, f, z, MOSS)
        bp.set(x, f + 3, z, "cave_vines_plant[berries=true]")
        bp.set(x, f + 2, z, "cave_vines[age=25,berries=true]")
        bp.set(x, f + 1, z, "moss_carpet")
    elif kind == "dripleaf":
        bp.set(x, f, z, CLAY)
        bp.set(x, f + 1, z, "small_dripleaf[facing=north,half=lower,waterlogged=false]")
        bp.set(x, f + 2, z, "small_dripleaf[facing=north,half=upper,waterlogged=false]")
    elif kind == "spore":
        bp.set(x, f, z, MOSS)
        bp.set(x, f + 3, z, SPORE)
        bp.set(x, f + 1, z, "azalea")
    else:
        bp.set(x, f, z, MOSS)
        bp.set(x, f + 1, z, "flowering_azalea")
    bp.set(x, f + 5, z, PIPES)


def lab(S):
    """The specimen laboratory: brick base, iron-framed glass upper walls under a glass roof broken by a tree; the
    specimen hall (jars in two rows), the dissection room and the archive; overgrown with moss, roots and azalea."""
    bp = S.bp
    x0, x1, z0, z1 = LAB
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, 7, z, (SB if edge else ("dark_oak_planks" if x > -21 else (PA if (x + z) % 2 else TB))))
            for y in range(8, 16):
                if edge:
                    post = (x - x0) % 4 == 0 if z in (z0, z1) else (z - z0) % 4 == 0
                    if y < 10:
                        spec = mas(x, y, z, 8)
                    elif y == 15:
                        spec = SB
                    elif post or y == 14:
                        spec = IRON
                    else:
                        spec = GLASS if hash01(x * 3, z + y, 75) > 0.08 else AIR
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, AIR)
            if not edge:
                # the glass roof on iron trusses, a few panes gone
                truss = (x - x0) % 4 == 0
                bp.set(x, 16, z, IRON if truss else (GLASS if hash01(x, z, 76) > 0.1 else AIR))
            else:
                bp.set(x, 16, z, SB)
    # the partition: brick wall with a wide arch between the hall and the east rooms
    for z in range(z0 + 1, z1):
        for y in range(8, 16):
            arch = -63 <= z <= -59 and y <= 11
            bp.set(-21, y, z, AIR if arch else (SB if y < 14 else IRON))
    # the east rooms: a cross wall between the dissection room (south) and the archive (north)
    for x in range(-20, x1):
        for y in range(8, 16):
            door = x in (-16, -15) and y <= 10
            bp.set(x, y, -61, AIR if door else MAHOGANY)
    # doors: west (from the lawn), east (to the irrigation passage)
    for z in (-61, -60):
        for y in (8, 9, 10):
            bp.set(x0, y, z, AIR)
    for z in (-58, -57):
        for y in (8, 9, 10):
            bp.set(x1, y, z, AIR)
    # the specimen hall: two rows of jars
    kinds = ["kelp", "berries", "dripleaf", "spore", "azalea", "kelp", "berries", "spore"]
    k = 0
    for x in (-30, -25):
        for z in (-67, -55):
            tank(S, x, z, kinds[k % len(kinds)])
            k += 1
    tank(S, -27, -64, "berries")
    tank(S, -27, -58, "kelp")
    # benches along the walls with small jars (potted plants under glass) and brewing stands
    for x in range(-33, -22):
        if x in (-31, -30, -29, -26, -25, -24):
            continue
        bp.set(x, 8, z0 + 1, MAHOGANY_SLAB + "[type=top,waterlogged=false]")
        bp.set(x, 9, z0 + 1, ("brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                              "potted_fern", "water_cauldron[level=2]", "potted_crimson_fungus")[x % 4])
    # the dissection room (south-east): a long table, a lectern, the cartography table and a sink
    for x in range(-18, -13):
        bp.set(x, 8, -56, TABLE)
    bp.set(-19, 8, -56, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(-12, 8, -54, "cartography_table")
    bp.set(-12, 8, -55, "water_cauldron[level=3]")
    bp.set(-12, 8, -59, "smithing_table")
    bp.chest(-19, 8, -53, "east", loot=LOOT + "va_lab")
    bp.spawner(-14, 8, -58, MOB_DRONE)
    # the archive (north-east): bookshelves, a reading desk, a ladder to nowhere
    for x in range(-20, x1):
        for y in (8, 9, 10, 11):
            if x not in (-16, -15):
                bp.set(x, y, z0 + 1, "bookshelf" if (x + y) % 5 else "chiseled_bookshelf[facing=south,"
                                                                       "slot_0_occupied=true,slot_1_occupied=false,"
                                                                       "slot_2_occupied=true,slot_3_occupied=true,"
                                                                       "slot_4_occupied=false,slot_5_occupied=true]")
    for z in range(-67, -62):
        bp.set(-20, 8, z, "bookshelf")
        bp.set(-20, 9, z, "bookshelf")
    bp.set(-14, 8, -65, TABLE)
    bp.set(-14, 8, -66, stair(MAHOGANY_STAIRS, "north"))
    bp.chest(-11, 8, -68, "west", loot=LOOT + "va_lab")
    # the overgrowth: an azalea tree breaking the roof, moss, roots
    tree(S, -27, 8, -61, 9)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if bp.get(x, 8, z) == AIR and hash01(x, z, 77) < 0.12:
                bp.set(x, 8, z, MOSS_C)
            if bp.get(x, 15, z) == AIR and bp.get(x, 16, z) not in (None, AIR) and hash01(x, z, 78) < 0.06:
                bp.set(x, 15, z, "hanging_roots[waterlogged=false]")
    for (x, z) in ((-31, -61), (-23, -61), (-17, -66), (-17, -54)):
        bp.set(x, 13, z, CHAIN)
        bp.set(x, 12, z, HANG_LAMP)


def tree(S, x, f, z, h):
    """An azalea tree: a twisting oak trunk, a round canopy of azalea and flowering azalea leaves."""
    bp = S.bp
    px, pz = x, z
    for k in range(h):
        if k > 3 and k % 3 == 0:
            px += (1 if hash01(x, k, 79) < 0.5 else -1) if k < h - 2 else 0
        bp.set(px, f + k, pz, "oak_log[axis=y]")
    cy = f + h
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            for dy in range(-2, 2):
                d = math.sqrt(dx * dx + dz * dz + dy * dy * 2.2)
                if d <= 3.2 and bp.get(px + dx, cy + dy, pz + dz) in (AIR, None, GLASS):
                    if bp.get(px + dx, cy + dy, pz + dz) is None and not (px + dx, cy + dy, pz + dz) in S.lining:
                        pass
                    bp.set(px + dx, cy + dy, pz + dz, FAZ_LEAVES if hash3(dx, dy, dz, 80) < 0.35 else AZ_LEAVES)
    bp.set(px, cy - 1, pz, "oak_log[axis=y]")


# ------------------------------------------------------------------ the north: irrigation passage and herbarium
HERB = (-8, 8, -64, -50)


def passage(S):
    """The irrigation passage along the north terrace: a brick path, a copper pipe line on brass stands, lamps."""
    bp = S.bp
    pts = [(-9, -58), (12, -58), (24, -54), (37, -52)]
    cells = set()
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        n = max(abs(bx - ax), abs(bz - az))
        for i in range(n + 1):
            x = int(round(ax + (bx - ax) * i / n))
            z = int(round(az + (bz - az) * i / n))
            for dz in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    cells.add((x + dx, z + dz))
    for (x, z) in cells:
        if S.floor(x, z) == 7 and bp.get(x, 8, z) == AIR:
            bp.set(x, 7, z, SB if hash01(x, z, 81) < 0.7 else MSB)
    # the pipe line on the north side
    for x in range(-8, 12):
        bp.set(x, 9, -61, PIPES)
        if x % 5 == 0:
            bp.set(x, 8, -61, BRASS)
    bp.spawner(18, 8, -60, MOB_DRONE)


def herbarium(S):
    """The herbarium vault (treasury) on brick piers behind the dome: walls of cabinets, pressing tables, the
    rarest specimens under glass; its stair turret drops to the passage (iron door: opens from inside only)."""
    bp = S.bp
    x0, x1, z0, z1 = HERB
    f = COR
    # piers and arches over the passage
    for (px, pz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), (x0, -57), (x1, -57), (0, z0)):
        for x in (px - 1, px, px + 1) if px == 0 else (px,):
            for dz in (0, 1) if pz != z1 else (-1, 0):
                for y in range(8, f - 1):
                    bp.set(x, y, pz + dz if pz != z1 else pz + dz, mas(x, y, pz, 8))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, f - 1, z, SB if x in (x0, x1) or z in (z0, z1) else (MAHOGANY if (x + z) % 3 else
                                                                         "dark_oak_planks"))
            bp.set(x, f - 2, z, SB if (x in (x0, x1) or z in (z0, z1) or z % 7 == 0) else AIR)
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(f, f + 8):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    win = not corner and 2 <= y - f <= 4 and ((x - x0) % 4 == 2 if z in (z0, z1) else
                                                            (z - z0) % 4 == 2)
                    bp.set(x, y, z, GLASS if win else (BRASS if y == f + 7 or corner else mas(x, y, z, 0)))
                else:
                    bp.set(x, y, z, AIR)
            # a stepped roof with a glass lantern
            d = min(x - x0, x1 - x, z - z0, z1 - z)
            ry = f + 8 + min(d, 3)
            for y in range(f + 8, ry + 1):
                bp.set(x, y, z, BRASS if y == ry and d >= 3 else SB)
            if d >= 4:
                bp.set(x, ry, z, GLASS)
    # the door from the dome's north bridge
    for x in (-1, 0, 1):
        for y in range(f, f + 4):
            bp.set(x, y, z1, AIR)
        bp.set(x, f - 1, z1, TREAD)
    # cabinets: barrels and bookshelves round the walls, pressing tables, the specimen cases
    for z in range(z0 + 1, z1):
        for y in (f, f + 1, f + 2):
            bp.set(x0 + 1, y, z, "bookshelf" if (z + y) % 3 else "chiseled_bookshelf[facing=east,"
                                                                     "slot_0_occupied=true,slot_1_occupied=true,"
                                                                     "slot_2_occupied=false,slot_3_occupied=true,"
                                                                     "slot_4_occupied=true,slot_5_occupied=false]")
    for x in range(x0 + 2, x1 - 1):
        for y in (f, f + 1):
            bp.barrel(x, y, z0 + 1, "south")
    for z in (-60, -55):
        for x in (-3, -2, -1):
            bp.set(x, f, z, TABLE)
    for (x, z, p) in ((3, -60, "potted_torchflower"), (3, -55, "potted_wither_rose"), (5, -58, "potted_azure_bluet"),
                      (-5, -58, "potted_blue_orchid")):
        bp.set(x, f, z, "chiseled_quartz_block")
        bp.set(x, f + 1, z, p)
        bp.set(x, f + 2, z, GLASS)
    bp.chest(0, f, z0 + 2, "south", loot=LOOT + "va_herbarium")
    bp.chest(-6, f, -57, "east", loot=LOOT + "va_herbarium")
    bp.chest(6, f, -62, "west", loot=LOOT + "va_herbarium")
    bp.set(1, f, z0 + 2, "gold_block")
    bp.set(-1, f, z0 + 2, "gold_block")
    bp.set(0, f + 1, z0 + 2, "potted_flowering_azalea_bush") if False else None
    for (x, z) in ((0, -57), (-4, -61), (4, -53)):
        bp.set(x, f + 6, z, CHAIN)
        bp.set(x, f + 5, z, CHANDELIER)
    # the stair turret (east): two flights down to the passage, an iron door at the foot
    tx0, tx1, tz0, tz1 = 9, 15, -63, -50
    for x in range(tx0, tx1 + 1):
        for z in range(tz0, tz1 + 1):
            edge = x in (tx0, tx1) or z in (tz0, tz1)
            for y in range(7, f + 6):
                bp.set(x, y, z, mas(x, y, z, 8) if edge else AIR)
            bp.set(x, f + 6, z, SB)
            bp.set(x, 7, z, PA)
    for z in range(-62, -50):
        for y in range(7, f + 6):
            bp.set(12, y, z, mas(12, y, z, 8))
    # top landing (feet 21) z -52..-51 across both lanes, the door from the herbarium
    for x in range(10, 15):
        for z in (-52, -51):
            bp.set(x, f - 1, z, PA)
            for y in range(7, f - 1):
                bp.set(x, y, z, SB if x <= 11 or y >= 13 else AIR)
    for z in (-52, -51):
        for y in range(f, f + 4):
            bp.set(x1, y, z, AIR)
            bp.set(tx0, y, z, AIR)
            bp.set(12, y, z, AIR)
    # flight 1: lane x 10..11, north from z -53 (feet 20) to z -58 (feet 15)
    for k in range(6):
        z = -53 - k
        for x in (10, 11):
            bp.set(x, f - 1 - k, z, stair(SB_ST, "south"))
            for y in range(7, f - 1 - k):
                bp.set(x, y, z, SB)
            for y in range(f - k, f + 4 - k):
                bp.set(x, y, z, AIR)
    # landing (feet 14) z -59..-62
    for x in range(10, 15):
        for z in range(-62, -58):
            bp.set(x, 13, z, PA)
            for y in range(7, 13):
                bp.set(x, y, z, SB)
            for y in range(14, 18):
                bp.set(x, y, z, AIR)
    # flight 2: lane x 13..14, south from z -58 (feet 13) to z -53 (feet 8)
    for k in range(7):
        z = -58 + k
        for x in (13, 14):
            bp.set(x, 14 - k, z, stair(SB_ST, "north"))
            for y in range(7, 14 - k):
                bp.set(x, y, z, SB)
            for y in range(15 - k, 19 - k):
                bp.set(x, y, z, AIR)
    bp.set(12, 12, -56, SHROOM)
    bp.set(12, 18, -55, SHROOM)
    for x in (13, 14):
        bp.set(x, 7, -51, PA)
        for y in range(8, 12):
            bp.set(x, y, -51, AIR)
    # the iron door at the foot (south wall), lever inside
    for y in (8, 9):
        bp.set(14, y, tz1, AIR)
    bp.set(14, 8, tz1, "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    bp.set(14, 9, tz1, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    bp.set(13, 9, -51, "lever[face=wall,facing=north,powered=false]")
    bp.set(13, 9, -52, AIR) if False else None
    bp.set(11, f + 2, -52, LANT) if False else None
    for (x, y, z) in ((12, 17, -60), (12, 23, -52)):
        bp.set(x, y, z, "lantern[hanging=false,waterlogged=false]") if False else None


# ------------------------------------------------------------------ the pump house and the lift tower
PUMP = (38, 58, -56, -36)


def pump_house(S):
    """The pump house: brick engine hall with tall arched windows, a beam engine (cylinder, A-frame, rocking beam,
    pump rod into the well), a flywheel, the boiler gallery round the north side, a smokestack into the roof."""
    bp = S.bp
    x0, x1, z0, z1 = PUMP
    f = TF
    top = 22
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, 7, z, SB if edge else (TREAD if (x + z) % 4 else IRON))
            for y in range(f, top + 1):
                if edge:
                    along = (z - z0) if x in (x0, x1) else (x - x0)
                    pil = along % 5 == 0
                    win = not pil and 11 <= y <= 18 and (along % 5) in (2, 3)
                    if win and y == 18 and (along % 5) == 3:
                        spec = SB
                    elif win:
                        spec = GLASS
                    elif y == top:
                        spec = BRASS
                    elif pil:
                        spec = SB if y < 12 else ("bricks" if y % 6 else BRASS)
                    else:
                        spec = mas(x, y, z, 8) if y < 11 else "bricks"
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, AIR)
            # the roof: a dark iron pitch along z
            d = min(x - x0, x1 - x)
            ry = top + 1 + d // 2
            for y in range(top + 1, ry + 1):
                bp.set(x, y, z, IRON if y == ry else "bricks")
            if d >= 9:
                bp.set(x, ry + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
    # doors: west (from the passage), south (to the maze)
    for z in range(-53, -50):
        for y in range(f, f + 3):
            bp.set(x0, y, z, AIR)
    for x in range(47, 50):
        for y in range(f, f + 3):
            bp.set(x, y, z1, AIR)
    # the well: a pit with water at the pump rod
    for x in range(51, 56):
        for z in range(-48, -43):
            rim = x in (51, 55) or z in (-48, -44)
            for y in range(2, 8):
                bp.set(x, y, z, (SB if rim else (WATER if y < 6 else AIR)) if y < 7 else (PA if rim else AIR))
            bp.set(x, 1, z, SB)
    for x in range(51, 56):
        for z in (-48, -44):
            bp.set(x, 8, z, IRON_WALL)
    for z in range(-47, -44):
        bp.set(51, 8, z, IRON_WALL)
        bp.set(55, 8, z, IRON_WALL)
    # the beam engine: copper cylinder, iron A-frame, brass rocking beam, the pump rod
    for x in range(41, 46):
        for z in range(-49, -44):
            d = math.hypot(x - 43, z - 46.5)
            if d <= 2.4:
                for y in range(f, f + 8):
                    bp.set(x, y, z, COPPER if y % 3 else BRASS)
                bp.set(x, f + 8, z, IRON)
    for y in range(f + 9, 19):
        bp.set(43, y, -46, IRON)
    for z in (-50, -43):
        for y in range(f, 19):
            bp.set(48, y, z, IRON)
    for z in range(-50, -42):
        bp.set(48, 19, z, IRON)
    for x in range(42, 55):
        tilt = int(round((x - 48) * 0.18))
        bp.set(x, 20 + tilt, -46, BRASS)
        bp.set(x, 20 + tilt, -47, BRASS if x in (42, 48, 54) else AIR)
    bp.set(48, 20, -47, GEAR)
    for y in range(9, 20):
        bp.set(53, y, -46, CHAIN if y > 6 else IRON)
    # the flywheel: an iron rim and brass spokes in the x-y plane by the south wall
    cxw, cyw, zw = 44, 14, -39
    for x in range(cxw - 5, cxw + 6):
        for y in range(cyw - 5, cyw + 6):
            r = math.hypot(x - cxw, y - cyw)
            if 4.4 <= r < 5.4:
                bp.set(x, y, zw, IRON)
            elif r < 4.4 and (x == cxw or y == cyw or abs(x - cxw) == abs(y - cyw)):
                bp.set(x, y, zw, BRASS if r > 1 else GEAR)
    for y in range(f, cyw):
        bp.set(cxw, y, zw, IRON if y < cyw - 5 else bp.get(cxw, y, zw))
    # the stair to the boiler gallery (west wall, rising north) and the gallery (feet 15) round the north side
    for k in range(1, 8):
        z = -38 - k
        for x in range(39, 42):
            bp.set(x, 7 + k, z, stair(SB_ST, "north"))
            for y in range(8, 7 + k):
                bp.set(x, y, z, SB)
            for y in range(8 + k, 12 + k):
                bp.set(x, y, z, AIR)
    for x in range(39, 58):
        for z in range(-55, -45):
            gallery = (z <= -52) or (x <= 41)
            if not gallery:
                continue
            bp.set(x, 14, z, TREAD)
            bp.set(x, 13, z, IRON if (x + z) % 3 == 0 or z <= -54 else AIR)
            for y in range(15, 19):
                bp.set(x, y, z, AIR)
    for x in range(42, 58):
        bp.set(x, 15, -51, IRON_WALL)
    for z in range(-51, -45):
        bp.set(42, 15, z, IRON_WALL)
    # the boilers on the gallery: two drums along the north wall
    for bx in (46, 53):
        for x in range(bx - 2, bx + 3):
            for y in range(15, 19):
                for z in (-55, -54):
                    if math.hypot(x - bx, y - 16.5) <= 2.3:
                        bp.set(x, y, z, IRON if abs(x - bx) == 2 else (COPPER if y % 2 else BRASS))
        bp.set(bx, 15, -53, "blast_furnace[facing=south,lit=true]")
        bp.set(bx + 1, 15, -53, GAUGE)
    bp.chest(57, 15, -53, "west", loot=LOOT + "va_pump")
    bp.chest(39, 15, -55, "east", loot=LOOT + "va_pump")
    bp.spawner(46, f, -41, MOB_SPIDER)
    # the smokestack (north-east corner) into the cavern roof
    for x in range(54, 59):
        for z in range(-56, -51):
            d = math.hypot(x - 56, z - 53.5)
            if d > 2.6:
                continue
            ytop = S.cmap.get((x, z), (7, 40))[1] + 1
            for y in range(top + 1, ytop + 1):
                bp.set(x, y, z, ("smooth_stone" if y % 7 == 0 else "bricks") if d > 1.4 else AIR)
    # hanging lamps in the hall
    for (x, z) in ((45, -42), (50, -40), (45, -50)):
        bp.set(x, 21, z, CHAIN)
        bp.set(x, 20, z, CHANDELIER)
    for (x, z) in ((52, -54), (40, -48)):
        bp.set(x, 18, z, LANT_H)


def lift_tower(S):
    """The water elevator: a brass-and-glass tower on the dome band; a bubble column rises from the lake level to
    the cornice; its top door (iron) opens from the cornice side only."""
    bp = S.bp
    tx, tz = LIFT
    x0, x1, z0, z1 = tx - 2, tx + 2, tz - 2, tz + 2
    top = COR - 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            bp.set(x, 0, z, PA)
            for y in range(1, top + 6):
                if edge:
                    spec = IRON if corner else (BRASS if y % 6 == 0 else (GLASS if y > 3 else SB))
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, AIR)
            bp.set(x, top + 6, z, BRASS)
            if not corner:
                bp.set(x, top + 7, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    bp.set(tx, top + 7, tz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the column: soul sand, bubbles up to the top floor, a glass casing (open south at the foot)
    bp.set(tx, 0, tz, "soul_sand")
    for y in range(1, top + 1):
        bp.set(tx, y, tz, "bubble_column[drag=false]")
    for y in range(1, top):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                if (dx, dz) == (0, 1) and y in (1, 2):
                    continue
                bp.set(tx + dx, y, tz + dz, IRON if dx and dz else (GLASS if y % 4 else BRASS))
    bp.set(tx, 1, tz + 1, "spruce_sign[rotation=0,waterlogged=false]")
    bp.set(tx, 2, tz + 1, "spruce_wall_sign[facing=south,waterlogged=false]")
    bp.set(tx, 3, tz + 1, IRON)
    # the ground door (south) and the top floor
    for y in (1, 2, 3):
        bp.set(tx, y, z1, AIR)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if (x, z) != (tx, tz):
                bp.set(x, top, z, TREAD)
            for y in range(top + 1, top + 5):
                bp.set(x, y, z, AIR)
    # the top door west onto a short bridge to the cornice; the lever on the cornice side only
    bp.set(x0, top + 1, tz, "iron_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
    bp.set(x0, top + 2, tz, "iron_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
    for z in range(tz - 1, tz + 2):
        bp.set(x0 - 1, top, z, TREAD)
        bp.set(x0 - 1, top - 1, z, IRON)
        for y in range(top + 1, top + 4):
            bp.set(x0 - 1, y, z, AIR)
    bp.set(x0 - 1, top + 1, tz - 1, IRON_WALL)
    bp.set(x0 - 1, top + 2, tz + 1, "lever[face=wall,facing=west,powered=false]")
    bp.chest(x1 - 1, top + 1, z1 - 1, "west", loot=LOOT + "va_lift")
    bp.set(x1 - 1, top + 4, z0 + 1, LANT_H)
    # the pipe from the tower to the pump house
    for x in range(x1 + 1, PUMP[0]):
        bp.set(x, 14, PUMP[3], PIPES)
    bp.set(x0 + 1, 3, z1 - 1, LANT) if False else None


# ------------------------------------------------------------------ the azalea maze and the court
MZ_X0, MZ_Z0, MZ_NI, MZ_NJ = 38, -28, 6, 14     # hedge lines every 4 from (MZ_X0, MZ_Z0)
COURT = {(i, j) for i in range(0, 3) for j in range(4, 8)}


def maze(S):
    """The azalea maze: flowering hedges four high on moss, paths three wide, a dead end with a chest, the fountain
    court in the middle where the east rib catwalk starts."""
    bp = S.bp
    f = TF
    x1 = MZ_X0 + 4 * MZ_NI
    z1 = MZ_Z0 + 4 * MZ_NJ
    cells = [(i, j) for i in range(MZ_NI) for j in range(MZ_NJ) if (i, j) not in COURT]
    # depth-first spanning tree from the entrance cell (north edge)
    import random
    rng = random.Random(4242)
    start = (4, 0)
    seen = {start}
    stack = [start]
    open_walls = set()
    while stack:
        c = stack[-1]
        nb = [(c[0] + di, c[1] + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        nb = [n for n in nb if 0 <= n[0] < MZ_NI and 0 <= n[1] < MZ_NJ and n not in COURT and n not in seen]
        if not nb:
            stack.pop()
            continue
        n = rng.choice(nb)
        open_walls.add(frozenset((c, n)))
        seen.add(n)
        stack.append(n)
    # a few loops
    extra = [((1, 2), (2, 2)), ((4, 9), (5, 9)), ((3, 11), (3, 12)), ((0, 10), (1, 10)), ((5, 3), (5, 4))]
    for a, b in extra:
        open_walls.add(frozenset((a, b)))
    # hedge mass over the whole maze, then carve the cells and the opened walls
    for x in range(MZ_X0, x1 + 1):
        for z in range(MZ_Z0, z1 + 1):
            if S.floor(x, z) != 7:
                continue
            bp.set(x, 7, z, MOSS)
            for y in range(f, f + 4):
                bp.set(x, y, z, FAZ_LEAVES if hash3(x, y, z, 82) < 0.3 else AZ_LEAVES)

    def cell_box(i, j):
        return MZ_X0 + 4 * i + 1, MZ_Z0 + 4 * j + 1, MZ_X0 + 4 * i + 3, MZ_Z0 + 4 * j + 3

    def clear(xa, za, xb, zb):
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if S.floor(x, z) != 7:
                    continue
                bp.set(x, 7, z, MOSS if hash01(x, z, 83) < 0.5 else (ROOTED if hash01(x, z, 84) < 0.5 else
                                                                    "mossy_cobblestone"))
                for y in range(f, f + 4):
                    bp.set(x, y, z, AIR)
                if hash01(x, z, 85) < 0.1:
                    bp.set(x, f, z, MOSS_C)

    for (i, j) in cells:
        xa, za, xb, zb = cell_box(i, j)
        clear(xa, za, xb, zb)
    for w in open_walls:
        (a, b) = tuple(w)
        xa, za, xb, zb = cell_box(*a)
        xc, zc, xd, zd = cell_box(*b)
        clear(min(xa, xc), min(za, zc), max(xb, xd), max(zb, zd))
    # the court: one opening east into the maze
    cx0, cz0, _, _ = cell_box(0, 4)
    _, _, cx1, cz1 = cell_box(2, 7)
    clear(cx0, cz0, cx1, cz1)
    clear(cx1, MZ_Z0 + 4 * 5 + 1, cx1 + 2, MZ_Z0 + 4 * 5 + 3)
    # the entrance (north) from the pump house
    xa, za, xb, zb = cell_box(*start)
    clear(xa, MZ_Z0, xb, MZ_Z0)
    # the fountain in the court
    fx, fz = 45, -6
    for x in range(fx - 2, fx + 3):
        for z in range(fz - 2, fz + 3):
            rim = max(abs(x - fx), abs(z - fz)) == 2
            bp.set(x, f, z, MSB_SL if False else (SB if rim else WATER))
            bp.set(x, 7, z, SB)
    bp.set(fx, f, fz, PA)
    bp.set(fx, f + 1, fz, PA)
    bp.set(fx, f + 2, fz, BRASS)
    bp.set(fx, f + 3, fz, FROG_V)
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        bp.set(fx + dx, f + 1, fz + dz, LANT)
    # a far dead end with a chest, another with a spawner, benches in the court
    bp.chest(MZ_X0 + 4 * 5 + 2, f, MZ_Z0 + 4 * 13 + 3, "north", loot=LOOT + "va_maze")
    bp.spawner(MZ_X0 + 4 * 1 + 2, f, MZ_Z0 + 4 * 11 + 2, MOB_FROG)
    bp.spawner(MZ_X0 + 4 * 4 + 2, f, MZ_Z0 + 4 * 6 + 2, MOB_FROG)
    for (x, z, fc) in ((40, -11, "south"), (49, -11, "south"), (40, 3, "north"), (49, 3, "north")):
        bp.set(x, f, z, stair("jungle_stairs", fc))
    S.maze_box = (MZ_X0, MZ_Z0, x1, z1)


# ------------------------------------------------------------------ the rib catwalks and the cornice
def catwalks(S):
    """The east rib catwalk (main route) from the maze court up to the cornice, two flights on a brass girder with a
    leg on the band; the west rib catwalk from the cornice down to the greenhouses (one-way gate at the top)."""
    bp = S.bp
    # east: top landing x 26..27 (feet 21), flight x 28..33 down to feet 15, landing x 34..35, flight x 36..41
    zs = (-4, -3, -2)
    rows = [(26, 21, None), (27, 21, None)]
    for k in range(6):
        rows.append((28 + k, 21 - k, "west"))
    rows += [(34, 15, None), (35, 15, None)]
    for k in range(7):
        rows.append((36 + k, 15 - k, "west"))
    for (x, ft, fc) in rows:
        for z in zs:
            bp.set(x, ft - 1, z, stair(TREAD_STAIRS_SAFE, fc) if fc else TREAD)
            for y in range(ft, ft + 4):
                if bp.get(x, y, z) != AIR:
                    bp.set(x, y, z, AIR)
            # the girder: two deep under the treads, solid down to the terrace where it stands on it
            fl = S.floor(x, z)
            if fl == 7 and x >= 38:
                for y in range(7, ft - 1):
                    bp.set(x, y, z, IRON if z != -3 else BRASS)
            else:
                bp.set(x, ft - 2, z, IRON if z != -3 else BRASS)
                bp.set(x, ft - 3, z, patina(x, ft - 3, z) if z == -3 else AIR)
        for z in (-5, -1):
            bp.set(x, ft, z, IRON_WALL)
            bp.set(x, ft - 1, z, IRON)
    # the leg under the landing (on the band)
    for x in (34, 35):
        for z in zs:
            for y in range(1, 14):
                bp.set(x, y, z, patina(x, y, z) if z == -3 else IRON)
            bp.set(x, 0, z, PA)
    for (x, z) in ((34, -5), (35, -1)):
        bp.set(x, 16, z, LANT)
    # west: gate on the deck at x -30, treads x -31..-42 (feet 20..9), the strip at x -43 (feet 8)
    zw = (-10, -9, -8)
    for k in range(13):
        x = -31 - k
        ft = 21 - k
        for z in zw:
            bp.set(x, ft - 1, z, TREAD if (k == 0 and z != -9) else stair(TREAD_STAIRS_SAFE, "east"))
            for y in range(ft, ft + 4):
                if bp.get(x, y, z) != AIR:
                    bp.set(x, y, z, AIR)
            if S.floor(x, z) == 7 and x <= -38:
                for y in range(7, ft - 1):
                    bp.set(x, y, z, IRON if z != -9 else BRASS)
            else:
                bp.set(x, ft - 2, z, IRON if z != -9 else BRASS)
                bp.set(x, ft - 3, z, patina(x, ft - 3, z) if z == -9 else AIR)
        for z in (-11, -7):
            bp.set(x, ft, z, IRON_WALL)
            bp.set(x, ft - 1, z, IRON)
    for z in zw:
        bp.set(-30, 20, z, TREAD)
        bp.set(-29, 20, z, TREAD)
        for y in range(21, 25):
            bp.set(-30, y, z, AIR)
            bp.set(-29, y, z, AIR)
    for z in (-10, -8):
        bp.set(-30, 21, z, "iron_bars")
        bp.set(-30, 22, z, BRASS)
        bp.set(-30, 23, z, BRASS)
    bp.set(-30, 23, -9, BRASS)
    bp.set(-30, 21, -9, "iron_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
    bp.set(-30, 22, -9, "iron_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
    bp.set(-29, 22, -10, "lever[face=wall,facing=east,powered=false]")
    for x in (-32, -39):
        bp.set(x, 20 - (-31 - x) + 1, -11, LANT) if False else None


TREAD_STAIRS_SAFE = W + "diamond_plate_stairs"


def cornice(S):
    """The cornice walk round the dome: lanterns on the parapet, gaps for the catwalks and the lift bridge, the lamp
    kiosk with the site of grace, the dripleaf drop over the moat."""
    bp = S.bp
    y = COR - 1
    # gaps in the parapet
    for x in range(DCX - 33, DCX + 34):
        for z in range(DCZ - 33, DCZ + 34):
            if bp.get(x, y + 1, z) != IRON_WALL:
                continue
            if (24 <= x <= 29 and -5 <= z <= -1) or (-31 <= x <= -27 and -11 <= z <= -7) or \
                    (27 <= x <= 29 and -36 <= z <= -32):
                bp.set(x, y + 1, z, AIR)
    # lanterns on the parapet
    for k in range(24):
        t = math.radians(k * 15 + 7.5)
        x = int(round(DCX + math.cos(t) * 31))
        z = int(round(DCZ + math.sin(t) * 31))
        if bp.get(x, y + 1, z) == IRON_WALL and bp.get(x, y + 2, z) == AIR:
            bp.set(x, y + 2, z, LANT)
    # the lamp kiosk: four posts and a brass canopy over the waystone
    for (x, z) in ((27, -14), (29, -14), (27, -12), (29, -12)):
        for yy in range(y + 1, y + 5):
            bp.set(x, yy, z, IRON_WALL)
    for x in range(26, 31):
        for z in range(-15, -10):
            if bp.get(x, y + 5, z) in (AIR, None):
                bp.set(x, y + 5, z, BRASS_SLAB + "[type=bottom,waterlogged=false]" if x in (26, 30) or z in (-15, -11)
                       else BRASS)
    bp.set(28, y + 6, -13, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(28, y + 4, -13, LANT_H)
    bp.set(28, y + 1, -13, MOD["waystone"])
    bp.set(28, y + 1, -12, "candle[candles=3,lit=true,waterlogged=false]") if False else None
    bp.set(27, y + 1, -13, stair("jungle_stairs", "east")) if False else None
    bp.chest(27, y + 1, -9, "east", loot=LOOT + "va_cornice") if bp.get(27, y, -9) == TREAD else None
    # the dripleaf drop: a gap in the parapet, a brass board one block out over the moat, a sign
    t = math.radians(110)
    ux, uz = math.cos(t), math.sin(t)
    for w in (-1, 0, 1):
        for o in (30.8, 31.8):
            x = int(round(DCX + ux * o - uz * w))
            z = int(round(DCZ + uz * o + ux * w))
            if bp.get(x, y + 1, z) == IRON_WALL:
                bp.set(x, y + 1, z, AIR)
    bx = int(round(DCX + ux * 32.3))
    bz = int(round(DCZ + uz * 32.3))
    bp.set(bx, y, bz, BRASS_SLAB + "[type=top,waterlogged=false]")
    bp.set(bx + 1, y + 1, bz, IRON_WALL)
    bp.set(bx - 1, y + 1, bz, IRON_WALL)
    bp.set(bx + 1, y, bz, IRON)
    bp.set(bx - 1, y, bz, IRON)
    S.drop = (bx, bz)
    # big dripleaf rising from the moat round the landing water
    for (dx, dz, h) in ((-3, 2, 5), (3, 3, 4), (-2, 5, 3), (4, 0, 6)):
        x, z = bx + dx, bz + dz
        if (x, z) not in S.lake:
            continue
        bp.set(x, -5, z, CLAY)
        for yy in range(-4, h - 3):
            bp.set(x, yy, z, "big_dripleaf_stem[facing=south,waterlogged=%s]" % ("true" if yy <= 0 else "false"))
        bp.set(x, h - 3, z, "big_dripleaf[facing=south,tilt=none,waterlogged=%s]" % ("true" if h - 3 <= 0 else "false"))


# ------------------------------------------------------------------ the living cave
def cave_dressing(S):
    """Moss, glow lichen, hanging roots and spore blossoms on the cave, azalea trees and bushes on the terraces,
    dripleaf and sugar cane by the water, glow berries hanging from the roof."""
    bp = S.bp
    for (x, z), (fy, top) in S.cmap.items():
        h = hash01(x, z, 101)
        roof = bp.get(x, top + 1, z)
        if roof is not None and roof != AIR and (x, top + 1, z) in S.lining and bp.get(x, top, z) == AIR:
            if h < 0.03:
                bp.set(x, top, z, SPORE)
            elif h < 0.09:
                bp.set(x, top, z, "hanging_roots[waterlogged=false]")
            elif h < 0.115 and top - fy > 10:
                berries(S, x, z, top, top - 2 - int(hash01(x, z, 102) * 5), 3)
            if roof in ("minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:diorite"):
                if hash01(x, z, 103) < 0.35:
                    bp.set(x, top + 1, z, MOSS)
        # the floor
        if bp.get(x, fy + 1, z) != AIR or bp.get(x, fy, z) not in ("minecraft:moss_block", "minecraft:rooted_dirt",
                                                                     "minecraft:grass_block", "minecraft:coarse_dirt",
                                                                     "minecraft:clay", "minecraft:mud"):
            continue
        if ddist(x, z) < 34 and fy == 0:
            continue
        g = hash01(x, z, 104)
        near_water = (x + 1, z) in S.lake or (x - 1, z) in S.lake or (x, z + 1) in S.lake or (x, z - 1) in S.lake
        if near_water and g < 0.25:
            if g < 0.08:
                for yy in (fy + 1, fy + 2):
                    bp.set(x, yy, z, "sugar_cane[age=0]")
            else:
                bp.set(x, fy + 1, z, "small_dripleaf[facing=north,half=lower,waterlogged=false]")
                bp.set(x, fy + 2, z, "small_dripleaf[facing=north,half=upper,waterlogged=false]")
        elif g < 0.18:
            bp.set(x, fy + 1, z, MOSS_C)
        elif g < 0.22:
            bp.set(x, fy + 1, z, "short_grass")
        elif g < 0.24:
            bp.set(x, fy + 1, z, "azalea" if g < 0.23 else "flowering_azalea")
        elif g < 0.25:
            bp.set(x, fy + 1, z, "fern")
    # glow lichen on the cave walls near the floor
    for p in list(S.lining):
        x, y, z = p
        if hash3(x, y, z, 105) > 0.05:
            continue
        for (dx, dz, side) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
            if bp.get(x + dx, y, z + dz) == AIR:
                props = {s: "false" for s in ("down", "east", "north", "south", "up", "west")}
                props[side] = "true"
                bp.set(x + dx, y, z + dz, "glow_lichen[%s,waterlogged=false]" % ",".join("%s=%s" % kv for kv in
                                                                                         sorted(props.items())))
                break
    # azalea trees on the terraces, away from the buildings
    spots = [(-62, -20), (-40, -46), (-60, 2), (-58, 38), (-50, -42), (-64, -46), (24, -62), (-22, -46),
             (60, -26), (62, 30), (40, 32), (-28, -76) if False else (-44, -62)]
    for (x, z) in spots:
        if S.floor(x, z) == 7 and bp.get(x, 8, z) == AIR and bp.get(x, 11, z) == AIR:
            tree(S, x, 8, z, 6 + int(hash01(x, z, 106) * 3))


def stone_paths(S):
    """The main route's floors, lighter and cleaner (§10.10): shore paths round the lake, the band round the dome."""
    bp = S.bp
    for (x, z), (fy, top) in S.cmap.items():
        if fy != 0 or (x, z) in S.lake or bp.get(x, 1, z) != AIR:
            continue
        d = ddist(x, z)
        if 32 <= d < 35 and z < 10:
            bp.set(x, 0, z, PA if hash01(x, z, 111) < 0.75 else MSB)
        cx, cz, rx, rz = LAKE
        e = ((x - cx) / (rx + 3)) ** 2 + ((z - cz) / (rz + 3)) ** 2
        if 0.92 < e < 1.12 and z > 0:
            bp.set(x, 0, z, PA if hash01(x, z, 112) < 0.75 else SB)


# ------------------------------------------------------------------ lighting
EMIT = (("sea_lantern", 15), ("shroomlight", 15), ("froglight", 15), ("glowstone", 15), ("soul_lantern", 10),
        ("lantern", 15), ("campfire", 15), ("edison_lamp", 15), ("chandelier", 15), ("end_rod", 14),
        ("glow_lichen", 7), ("candle", 6), ("blast_furnace", 13))


def emission(name, props):
    s = name.split(":")[1]
    if s in ("cave_vines", "cave_vines_plant"):
        return 14 if props.get("berries") == "true" else 0
    for k, v in EMIT:
        if k in s:
            if k == "campfire" and props.get("lit") == "false":
                return 0
            if k == "blast_furnace" and props.get("lit") != "true":
                return 0
            return v
    return 0


def _opaque(name):
    from ..blueprint import is_solid
    s = name.split(":")[1]
    if s in ("air", "water", "bubble_column") or "glass" in s or "leaves" in s or "slab" in s or "stairs" in s:
        return False
    if "lantern" in s or "froglight" in s or s in ("shroomlight", "glowstone"):
        return True
    return is_solid(name)


def light_map(bp):
    """Block light over the blueprint's box (numpy flood, 15 steps); unknown cells (the world's rock) are opaque."""
    import numpy as np
    xs = [p[0] for p in bp.blocks]
    ys = [p[1] for p in bp.blocks]
    zs = [p[2] for p in bp.blocks]
    ox, oy, oz = min(xs) - 1, min(ys) - 1, min(zs) - 1
    shape = (max(xs) - ox + 2, max(ys) - oy + 2, max(zs) - oz + 2)
    trans = np.zeros(shape, dtype=bool)
    cost = np.ones(shape, dtype=np.int8)
    emit = np.zeros(shape, dtype=np.int8)
    cache = {}
    for (x, y, z), (name, props, _) in bp.blocks.items():
        key = (name, tuple(sorted(props.items())))
        if key not in cache:
            s = name.split(":")[1]
            cache[key] = (not _opaque(name), 2 if (s == "water" or "leaves" in s) else 1, emission(name, props))
        t, c, e = cache[key]
        i, j, k = x - ox, y - oy, z - oz
        trans[i, j, k] = t
        cost[i, j, k] = c
        emit[i, j, k] = e
    L = emit.copy()
    for _ in range(15):
        n = L.copy()
        for ax in range(3):
            for sh in (1, -1):
                r = np.roll(L, sh, axis=ax)
                if sh == 1:
                    idx = [slice(None)] * 3
                    idx[ax] = slice(0, 1)
                else:
                    idx = [slice(None)] * 3
                    idx[ax] = slice(-1, None)
                r[tuple(idx)] = 0
                cand = r - cost
                n = np.where(trans & (cand > n), cand, n)
        L = n
    return L, (ox, oy, oz), trans


SKIP_BELOW = ("glass", "cocoa", "leaves", "_log", "_wood", "pipes", "chain", "lantern", "lightning_rod", "sugar_cane",
              "pitcher", "iron_bars", "dark_iron_plating_slab", "dripleaf", "lily_pad", "mushroom", "fence", "_wall")


def dark_floors(bp, L, origin, trans, minimum=8):
    """Standable cells (solid below, two passable cells) whose light is under `minimum`."""
    from ..blueprint import is_solid
    ox, oy, oz = origin
    out = []
    B = bp.blocks
    for (x, y, z), (name, props, _) in B.items():
        if name != AIR:
            continue
        below = B.get((x, y - 1, z))
        if below is None:
            continue
        bn = below[0]
        sb = bn.split(":")[1]
        if not (is_solid(bn) or sb.endswith("_slab") or sb.endswith("_stairs") or "leaves" in sb) or sb in (
                "water", "bubble_column") or "leaves" in sb:
            continue
        if any(k in sb for k in SKIP_BELOW) or (ddist(x, z) < 28 and y > COR + 2):
            continue
        head = B.get((x, y + 1, z))
        if head is None or (head[0] != AIR and _opaque(head[0])):
            continue
        if L[x - ox, y - oy, z - oz] < minimum:
            out.append((x, y, z))
    return out


NATURAL = {"minecraft:" + n for n in (MOSS, ROOTED, "coarse_dirt", "grass_block", "stone", "andesite", CLAY, "mud",
                                     "gravel", "mossy_cobblestone", "tuff", "diorite")}
PLAIN_FLOORS = {"minecraft:" + n for n in (MOSS, ROOTED, "coarse_dirt", "grass_block", "stone", "andesite", CLAY,
                                          "mud", PA, SB, MSB, TB, "gravel", "mossy_cobblestone", "cobblestone",
                                          "dark_oak_planks", "jungle_planks", CSB, "tuff", "diorite", "deepslate")} | {
    TREAD, IRON, MAHOGANY}


def lighting(S, rounds=7):
    """Keep every walkable floor at light 8 or more (the cavern is alive, not dark): glow berries hanging from the
    cave roof over open ground, froglights set into floors under low ceilings, lanterns hung in rooms."""
    bp = S.bp
    for r in range(rounds):
        L, origin, trans = light_map(bp)
        dark = dark_floors(bp, L, origin, trans)
        if not dark:
            break
        dark.sort(key=lambda p: (L[p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]], p))
        placed = []
        for (x, y, z) in dark:
            if any(abs(x - a) + abs(y - b) + abs(z - c) < 5 for (a, b, c) in placed):
                continue
            ok = False
            # the ceiling above
            t = y + 2
            while t < y + 40 and bp.get(x, t, z) == AIR:
                t += 1
            ceil = bp.get(x, t, z)
            if ceil is not None and ceil != AIR and 7 <= t - y <= 15 and ((x, t, z) in S.lining or ceil in (
                    "minecraft:moss_block", "minecraft:stone", "minecraft:andesite")):
                ok = berries(S, x, z, t - 1, y + 3 + (r % 2), 4 + r)
            if not ok and ceil is not None and ceil != AIR and 4 <= t - y <= 12 and _opaque(ceil) and \
                    (x, t, z) not in S.lining:
                for yy in range(y + 4, t):
                    bp.set(x, yy, z, CHAIN)
                bp.set(x, y + 3, z, LANT_H)
                ok = True
            if not ok and bp.get(x, y - 1, z) in NATURAL:
                # a glowing fungus patch in the moss
                bp.set(x, y - 1, z, SHROOM if hash01(x, z, 121) < 0.6 else FROG_V)
                if bp.get(x + 1, y, z) == AIR and bp.get(x + 1, y - 1, z) in NATURAL and hash01(x, z, 122) < 0.5:
                    bp.set(x + 1, y, z, "red_mushroom" if hash01(x, z, 123) < 0.5 else "brown_mushroom")
                ok = True
            if not ok:
                fb = bp.get(x, y - 1, z)
                if fb in PLAIN_FLOORS:
                    bp.set(x, y - 1, z, FROG_O if hash01(x, z, 120) < 0.5 else FROG_P)
                    ok = True
            if not ok:
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if bp.get(x + dx, y - 1, z + dz) in PLAIN_FLOORS and bp.get(x + dx, y, z + dz) == AIR:
                        bp.set(x + dx, y - 1, z + dz, FROG_O)
                        ok = True
                        break
            if ok:
                placed.append((x, y, z))
        S.light_log = getattr(S, "light_log", []) + [(len(dark), len(placed))]


SOLID = {"minecraft:" + n for n in (SB, MSB, CSB, PA, TB, "stone", "andesite", "tuff", "diorite", "deepslate",
                                     "cobblestone", "mossy_cobblestone", "bricks", "clay", "moss_block", "gravel")} | {
    BRASS, VERD, IRON, MAHOGANY, COPPER}


def hollow_cores(S):
    """Leave the hidden cores of walls, piers and fills to the rock they are built in: a plain block with plain
    blocks on all six sides is dropped from the template."""
    B = S.bp.blocks

    def plain(p):
        v = B.get(p)
        return v is not None and v[0] in SOLID and not v[1] and v[2] is None

    drop = [p for p in B if plain(p) and all(plain((p[0] + dx, p[1] + dy, p[2] + dz)) for dx, dy, dz in
                                             ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))]
    for p in drop:
        del B[p]


def verdant_arboretum(bp):
    S = Site(bp)
    cavern(S)
    side_cave(S)
    lake(S)
    station(S)
    dome(S)
    dome_doors(S)
    arena(S)
    dome_garden(S)
    aqueduct(S)
    grotto(S)
    west_terrace(S)
    greenhouse(S)
    seed_vault(S)
    lab(S)
    passage(S)
    herbarium(S)
    pump_house(S)
    lift_tower(S)
    maze(S)
    catwalks(S)
    cornice(S)
    stone_paths(S)
    cave_dressing(S)
    for p in ((-40, 12, -7), (37, 14, -5)):   # the open rib catwalks' lowest treads: a glowing rail block
        S.bp.set(*p, "minecraft:shroomlight")
    lighting(S)
    hollow_cores(S)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("lake_shore_station", (0, F, 46), (0, 30, -20)),
    ("greenhouse", (-48, TF, 22), (-48, 11, -8)),
    ("seed_vault", (-74, TF, -32), (-83, TF + 2, -30)),
    ("specimen_lab", (-32, TF, -60), (-16, TF + 3, -61)),
    ("pump_house", (40, TF, -38), (50, 16, -48)),
    ("azalea_maze_court", (47, TF, -9), (27, 22, -3)),
    ("arena", (24, COR, -20), (0, 34, -20)),
    ("herbarium", (0, COR, -51), (0, COR + 2, -62)),
]

register(StructureDef(
    "verdant_arboretum", "overworld", ["lush_caves"],
    [Piece("arboretum", verdant_arboretum, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", height=("uniform", -16, -12), processors="none",
    step="underground_structures", max_distance=116, foundation=False,
    spawns=[(MOB_FROG, 6, 1, 2), (MOB_SPIDER, 4, 1, 2), (MOB_DRONE, 2, 1, 1)],
    title_fr="L'Arboretum englouti", title_en="The Sunken Arboretum"))
