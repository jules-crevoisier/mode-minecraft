"""The Clockwork Asylum (L'Asile mécanique): a gothic hilltop sanatorium turned automaton workshop, rising out of the
dark oak canopy. Colossal tier (tools/BUILDING.md §1, §12 concept 24, §10 legacy-dungeon template, §15), steampunk
accents (tools/STYLE_STEAMPUNK.md: brass clockwork, copper pipes, boilers, dark iron and verdigris).

Silhouette (one noun phrase, §15.1): a black-and-grey gothic clock tower with a cracked four-faced brass clock and a
needle spire, standing over a long barred sanatorium on a wooded hill.

Layout, ground y = 0 (feet 1), x east, z south. The plateau (top block P = 24) is a superellipse round (0, -30)
padded under every building; the walled cemetery is a terrace at y 12 on the hill's south-west flank.
  * the approach (south, ground): the woodcutters' camp and its waystone, a path through the dark oaks to the
    gatehouse in the crooked iron perimeter fence, the yard with the funicular's lower station (east), the stair up
    the hill's flank to the cemetery (graves, mausoleum, gravedigger's shed, the dead tree), the grand stair against
    the retaining wall to the forecourt (dead fountain with an automaton statue) and the hall's portal;
  * the main hall (hub, waystone): a 45-high open-roofed hall with a gallery on three sides, the Iron Orderly
    statue; the west ward wing (main route): the patient cells on the raised ground floor, the stair pavilion, the
    operating theatre with its brass surgical arms and the conversion ward upstairs, back to the hall's gallery;
    the east ward wing (optional): the Nightingale ward, the records archive and the laundry upstairs, whose chute
    drops into the hydrotherapy baths in the basement. Optional branches on the plateau: the chapel (west) and the
    broken greenhouse (east);
  * the clock tower (x -14..14, z -58..-30): five mechanism floors linked by stairs on alternate walls round the
    pendulum shaft: the winding hall (shortcut only), the escapement room, the going train, the great wheel (a
    balcony looks out east), the winding room (site of grace); the mist at the head of the last stair; the boss
    arena in the clock stage (35 x 35, 18 high) behind the four dials, the south one cracked open;
  * the treasury: the director's office in an oriel on the tower's north face, behind sealed bars;
  * shortcuts (§10.4): the director's private drop shaft (into a pool, then a passage to the winding hall, whose
    iron door opens only from the tower side onto the hub); the laundry chute (into the baths; their iron door
    opens only from the basement side, a stair up into the hall); the chapel's south door (opens from inside, a
    stair down into the cemetery); the funicular (powered rails, a cart at each station) from the forecourt down to
    the yard, the lower station's door opening only from inside.
Loot gradient (§15.6): camp and yard tier 1; gate, cemetery, hall 1-2; cells, ward, chapel, greenhouse 2;
theatre, archive, baths, crypt 2-3; mechanism floors 2-3; the director's office 3-5.
Height budget: the finial stands ~145 above the ground layer (dark forests and pale gardens sit low).
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, PIPES, TABLE, VERD, W, fbm,
                       hash01, hash3, vnoise)
from ..parts import LOOT, MOD
from .cloud_pagoda import Ctx, candle, carpet, carve, climb, hang, lever, path, railing, slab

# the champion of the clock stage (tools/BOSSES.md §32)
BOSS = "brasshaven:asylum_director"
MOB_BANSHEE = W + "banshee"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_AUTO = W + "turbine_automaton"
MOB_CRAWLER = W + "crypt_crawler"
MOB_KNIGHT = W + "skeleton_knight"
MOB_GARGOYLE = W + "gargoyle"
MOB_WISP = W + "lantern_wisp"

# ------------------------------------------------------------------ dimensions
P = 24                                    # plateau top block (feet P + 1)
CY = 12                                   # cemetery terrace top block
ZC, RX, RZ = -30, 70, 44                  # plateau superellipse
FL = [P, P + 11, P + 22, P + 33, P + 44]  # tower mechanism floors (top block)
FC = P + 55                               # clock stage floor (arena feet FC + 1)
FB = FC + 20                              # clock stage roof
SH = 18                                   # clock stage half width (x -18..18, z -62..-26)
TZ = -44                                  # tower axis z
WG, W2, WT = P + 4, P + 11, P + 18        # wing ground floor, upper floor, wall top
RAIL0 = 15                                # funicular: first incline rail z (rail y P there)
PADS = [(-73, -9, -37, 10),               # chapel and its bell tower
        (42, -9, 72, 9),                  # greenhouse
        (-70, -30, 70, -6),               # wings and pavilions
        (-21, -75, 21, -24),              # tower, clock stage, north turret
        (-44, -6, 44, 13)]                # forecourt

# materials
AIR = "minecraft:air"
WATER = "water[level=0]"
TB, PT, TUFF = "tuff_bricks", "polished_tuff", "tuff"
CTB, CT = "chiseled_tuff_bricks", "chiseled_tuff"
TB_ST, TB_SL, TB_WALL = "tuff_brick_stairs", "tuff_brick_slab", "tuff_brick_wall"
PT_ST, PT_SL = "polished_tuff_stairs", "polished_tuff_slab"
DSB, CDSB, DST, CDS, PDS = ("deepslate_bricks", "cracked_deepslate_bricks", "deepslate_tiles", "cobbled_deepslate",
                            "polished_deepslate")
DSB_ST, DSB_WALL, PDS_SL, PDS_ST = ("deepslate_brick_stairs", "deepslate_brick_wall", "polished_deepslate_slab",
                                    "polished_deepslate_stairs")
DOP, DO_ST, DO_SL, DO_FENCE = "dark_oak_planks", "dark_oak_stairs", "dark_oak_slab", "dark_oak_fence"
DO_LOG, SDO = "dark_oak_log[axis=y]", "stripped_dark_oak_log[axis=y]"
ROOF, ROOF_ST, ROOF_SL = W + "slate_roof_tiles", W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"
GILD, ENGR, BTILE = W + "gilded_trim", W + "engraved_brass", W + "brass_tiles"
DIB = W + "dark_iron_bricks"
GRILLE = W + "brass_grille"
BARS = "iron_bars"
PANE = "gray_stained_glass_pane"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
ROD_D = "lightning_rod[facing=down,powered=false,waterlogged=false]"
DO_LEAF = "dark_oak_leaves[distance=1,persistent=true,waterlogged=false]"
PO_LEAF = "pale_oak_leaves[distance=1,persistent=true,waterlogged=false]"
COBWEB = "cobweb"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def face_of(dx, dz):
    if abs(dz) >= abs(dx):
        return "south" if dz > 0 else "north"
    return "east" if dx > 0 else "west"


def wmat(x, y, z, y0=P):
    """Asylum masonry: deepslate in the bottom courses, tuff bricks above with clusters of polished tuff and tuff."""
    h = hash3(x, y, z, 211)
    r = y - y0
    if r <= 1:
        return CDSB if h < 0.2 else DSB
    if r <= 3 and h < 0.3:
        return DSB
    v = vnoise(x + z * 0.7, y * 1.3, 3.0, 212)
    if v < 0.2:
        return PT
    if v > 0.82:
        return TUFF
    return TB


def fp(C, x, y, z, spec):
    """Furniture: never on reserved walkway air."""
    if (x, y, z) in C.keep:
        return False
    C.set(x, y, z, spec)
    return True


def spawner(C, x, y, z, mob):
    C.keep.discard((x, y, z))
    C.bp.spawner(x, y, z, mob)


def chest(C, x, y, z, facing, table):
    C.keep.discard((x, y, z))
    C.bp.chest(x, y, z, facing, loot=LOOT + table)


def barrel(C, x, y, z):
    C.keep.discard((x, y, z))
    C.bp.barrel(x, y, z)


def iron_door(C, x, y, z, facing, lever_at=None, lever_facing=None):
    C.bp.door(x, y, z, facing, wood="iron")
    C.keep.discard((x, y, z))
    C.keep.discard((x, y + 1, z))
    if lever_at:
        lever(C, *lever_at, lever_facing)


def gear_disk(C, cx, cy, cz, r, plane, rim=BRASS, body=GEAR, hub=ENGR, teeth=True, put=False):
    """A vertical gear in plane "x" (disk in x-y at z = cz) or "z" (disk in z-y at x = cx): a toothed brass rim, a
    gear-panel body with spokes and an engraved hub."""
    R = int(math.ceil(r)) + 1
    setf = C.put if put else C.set
    for du in range(-R, R + 1):
        for dv in range(-R, R + 1):
            d = math.hypot(du, dv)
            a = math.atan2(dv, du)
            tooth = teeth and (int((a + math.pi) / (2 * math.pi) * max(8, int(r * 3))) % 2 == 0)
            if d > r + (0.9 if tooth else 0.0) + 0.2:
                continue
            if d <= 1.2:
                spec = hub
            elif d > r - 0.8:
                spec = rim
            elif r > 3.5 and (abs(du) <= 0.5 or abs(dv) <= 0.5 or d < 2.2):
                spec = rim                                            # spokes
            elif r > 3.5 and d < r - 1.8:
                continue                                              # open between the spokes
            else:
                spec = body
            x, y, z = (cx + du, cy + dv, cz) if plane == "x" else (cx, cy + dv, cz + du)
            setf(x, y, z, spec)


# ------------------------------------------------------------------ the hill
def plateau_dist(x, z):
    rn = ((abs(x) / RX) ** 4 + (abs(z - ZC) / RZ) ** 4) ** 0.25
    d = max(0.0, rn - 1.0) * 46.0
    for (x0, z0, x1, z1) in PADS:
        dx = max(x0 - x, 0, x - x1)
        dz = max(z0 - z, 0, z - z1)
        d = min(d, math.hypot(dx, dz))
    return d


def cem_norm(x, z):
    return ((abs(x + 39) / 25.0) ** 6 + (abs(z - 30) / 16.0) ** 6) ** (1.0 / 6)


def rail_y(z):
    """The funicular rail's block y at z (flat at P + 1 north of the incline, at 1 in the lower station)."""
    if z < RAIL0:
        return P + 1
    return max(1, P - (z - RAIL0))


def hill_top(x, z):
    n = 2.6 * (fbm(x, z, 18.0, 7) - 0.5) + 1.3 * (vnoise(x, z, 4.0, 8) - 0.5)
    d = plateau_dist(x, z)
    slope = 1.25 + 1.1 * fbm(x, z, 26.0, 9)
    t = P if d <= 0.5 else min(P, int(P - (d + n) * slope))
    cn = cem_norm(x, z)
    if cn <= 1.0:
        t = max(t, CY)
    else:
        dc = (cn - 1.0) * 18.0
        t = max(t, int(CY - (dc + n * 0.6) * 1.6))
    if 26 <= x <= 30 and z >= RAIL0:
        t = min(t, rail_y(z) - 2)
    return t if t >= 1 else None


def rock(x, y, z):
    """Hill rock: clustered stone, andesite and tuff (two noise scales, gently inclined strata), deepslate low,
    moss near the ground and on the north faces."""
    h = hash3(x, y, z, 52)
    if y <= 2 and h < 0.45:
        return "mossy_cobblestone"
    if z < -70 and h < 0.2:
        return "mossy_cobblestone"
    v = vnoise(x * 0.8 + y * 1.7, z * 0.8 - y * 1.1, 5.0, 53) * 0.7 + vnoise(x, z + y * 2, 2.0, 54) * 0.3
    if y < 7 and v < 0.5:
        return "deepslate" if h < 0.75 else CDS
    if v < 0.3:
        return "andesite"
    if v > 0.72:
        return TUFF if h < 0.8 else "andesite"
    return "stone" if h < 0.88 else "cobblestone"


def soil(x, z, t):
    h = hash01(x, z, 61)
    if t == CY:
        return "podzol[snowy=false]" if h < 0.45 else ("coarse_dirt" if h < 0.7 else "grass_block[snowy=false]")
    if h < 0.5:
        return "grass_block[snowy=false]"
    if h < 0.72:
        return "podzol[snowy=false]"
    if h < 0.86:
        return "moss_block"
    return "coarse_dirt"


def hill(C):
    tops = {}
    for x in range(-94, 95):
        for z in range(-98, 64):
            t = hill_top(x, z)
            if t is not None:
                tops[(x, z)] = t
    C.top = dict(tops)
    for (x, z), t in tops.items():
        ns = [tops.get((x + dx, z + dz)) for (dx, dz) in N4]
        if any(n is None for n in ns):
            ylo = -3
        else:
            ylo = min(t - 3, min(ns) + 1)
        drop = t - min((n if n is not None else 0) for n in ns)
        steep = drop >= 2
        mason = CY < t < P and cem_norm(x, z) < 1.12
        for y in range(ylo, t + 1):
            if mason:
                spec = PDS if y == t else (DSB if hash3(x, y, z, 63) > 0.15 else CDSB)
            elif y == t and not steep:
                spec = soil(x, z, t)
            elif t - 2 <= y < t and not steep:
                spec = "dirt"
            else:
                spec = rock(x, y, z)
            C.set(x, y, z, spec)


def seal_voids(C):
    """Air and water the build carved into the hollow hill get a rock skin where they touch its empty core."""
    tops = C.top
    for (x, y, z), b in list(C.bp.blocks.items()):
        name = b[0]
        if y > P or (x, z) not in tops or name not in ("minecraft:air", "minecraft:water", "minecraft:bubble_column"):
            continue
        for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            q = (x + dx, y + dy, z + dz)
            if q in C.bp.blocks:
                continue
            t = tops.get((q[0], q[2]))
            if t is not None and q[1] <= t:
                C.bp.set(q[0], q[1], q[2], "stone")


# ------------------------------------------------------------------ the ground round the hill
GROUND = (-80, 18, 80, 104)


def ground(C):
    x0, z0, x1, z1 = GROUND
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) in C.top:
                continue
            h = hash01(x, z, 71)
            C.set(x, 0, z, "grass_block[snowy=false]" if h < 0.55 else (
                "podzol[snowy=false]" if h < 0.8 else ("moss_block" if h < 0.92 else "coarse_dirt")))
            C.set(x, -1, z, "dirt")
            C.set(x, -2, z, "dirt" if h < 0.6 else "stone")
            for y in range(1, 6):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)
    # a skirt of scree and moss round the rest of the hill's foot
    for (x, z), t in list(C.top.items()):
        for (dx, dz) in N4:
            q = (x + dx, z + dz)
            if q in C.top or C.get(q[0], 0, q[1]) is not None:
                continue
            h = hash01(*q, 72)
            C.set(q[0], 0, q[1], "mossy_cobblestone" if h < 0.3 else ("podzol[snowy=false]" if h < 0.6 else
                                                                       "grass_block[snowy=false]"))
            C.set(q[0], -1, q[1], "stone")


def gravel_path(x, z, d):
    h = hash01(x, z, 81)
    if d < 1.0 and (x * 3 + z) % 5 == 0:
        return PDS
    return "gravel" if h < 0.45 else ("coarse_dirt" if h < 0.75 else "dirt_path")


def flags(x, z, d):
    """The main way: cobbled and polished deepslate flags, rougher at the edges."""
    h = hash01(x, z, 82)
    if d > 1.3 and h < 0.35:
        return "gravel" if h < 0.18 else CDS
    return PDS if h < 0.55 else (CDS if h < 0.8 else DST)


def lamp_post(C, x, y, z, soul=False):
    """An iron lamp post: a deepslate base, a wall shaft, a crossbar with a hanging lantern."""
    C.set(x, y, z, PDS)
    for k in (1, 2, 3):
        C.set(x, y + k, z, DSB_WALL)
    C.set(x, y + 4, z, "iron_bars")
    C.set(x, y + 5, z, SOUL if soul else LANT)


# ------------------------------------------------------------------ trees
def dark_oak(C, x, y, z, h, seed, pale=False):
    """A dark (or pale) oak: a 2 x 2 trunk, short branches at the top, a wide flat canopy; pale oaks drip with moss."""
    log = "pale_oak_log[axis=y]" if pale else DO_LOG
    leaf = PO_LEAF if pale else DO_LEAF
    for i in range(h):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            C.put(x + dx, y + i, z + dz, log)
    cy = y + h
    crowns = [(x, cy, z, 4)]
    for k, (bx, bz) in enumerate(((1, 1), (-1, -1), (1, -1), (-1, 1))):
        if hash01(x + k, z - k, 300 + seed) < 0.7:
            px, pz = x + (2 if bx > 0 else -1) * 1, z + (2 if bz > 0 else -1) * 1
            for s in range(2):
                ax = "x" if s == 0 else "z"
                C.put(px + bx * s, cy - 2 + s, pz + bz * s, f"{'pale_oak' if pale else 'dark_oak'}_log[axis={ax}]")
            crowns.append((px + bx * 2, cy - 1, pz + bz * 2, 3))
    for (cx, ccy, cz, r) in crowns:
        for dx in range(-r - 1, r + 2):
            for dz in range(-r - 1, r + 2):
                for dy in (-1, 0, 1):
                    rr = r + 0.5 - (1.5 if dy == 1 else 0) - (0.8 if dy == -1 else 0)
                    d = math.hypot(dx + 0.5, dz + 0.5)
                    if d <= rr and hash3(cx + dx, ccy + dy, cz + dz, 310 + seed) < (0.95 if d < rr - 1 else 0.6):
                        q = (cx + dx, ccy + dy, cz + dz)
                        if C.free(*q) and q not in C.keep:
                            C.put(*q, leaf)
                            if pale and dy == -1 and hash3(*q, 320) < 0.22 and C.free(q[0], q[1] - 1, q[2]):
                                C.put(q[0], q[1] - 1, q[2], "pale_hanging_moss[tip=true]")


def trees(C):
    placed = []
    for x in range(-92, 93, 4):
        for z in range(-96, 104, 4):
            jx = x + int(hash01(x, z, 331) * 3) - 1
            jz = z + int(hash01(x, z, 332) * 3) - 1
            if hash01(jx, jz, 333) > 0.62:
                continue
            t = C.top.get((jx, jz))
            if t is None:
                if C.get(jx, 0, jz) is None:
                    continue
                t = 0
            if any(abs(jx - a) + abs(jz - b) < 7 for (a, b) in placed):
                continue
            ok = True
            for dx in range(-1, 3):
                for dz in range(-1, 3):
                    trunk = dx in (0, 1) and dz in (0, 1)
                    tc = C.top.get((jx + dx, jz + dz), 0 if t == 0 else None)
                    if tc is None or (trunk and tc != t) or tc > t + 3:
                        ok = False
                        break
                    b = C.get(jx + dx, tc, jz + dz) or ""
                    if trunk and not any(s in b for s in ("grass_block", "podzol", "moss_block", "coarse_dirt",
                                                            "stone", "andesite", "tuff", "deepslate", "dirt")):
                        ok = False
                    if trunk and (b.endswith("deepslate_bricks") or "polished" in b):
                        ok = False
                    for y in range(max(t, tc) + 1, t + 12):
                        if (jx + dx, y, jz + dz) in C.keep or not C.free(jx + dx, y, jz + dz):
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                continue
            placed.append((jx, jz))
            for dx in (0, 1):
                for dz in (0, 1):
                    b = C.get(jx + dx, t, jz + dz) or ""
                    if not any(s in b for s in ("grass_block", "podzol", "moss_block", "coarse_dirt")):
                        C.set(jx + dx, t, jz + dz, "rooted_dirt")
            pale = hash01(jx, jz, 334) < 0.28
            dark_oak(C, jx, t + 1, jz, 6 + int(hash01(jx, jz, 335) * 4), len(placed), pale=pale)


# ------------------------------------------------------------------ the approach
def camp(C):
    """The woodcutters' camp in a clearing: log piles, a saw pit, a canvas tent, a fire and the entrance waystone."""
    cx, cz = 36, 88
    for x in range(cx - 10, cx + 10):
        for z in range(cz - 8, cz + 10):
            if math.hypot((x - cx) / 10.0, (z - cz) / 9.0) <= 1.0 and (x, z) not in C.top:
                C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 91) < 0.45 else "grass_block[snowy=false]")
                for y in range(1, 9):
                    C.bp.set(x, y, z, AIR)
    # log piles (pyramids of dark oak logs lying along x)
    for (px, pz) in ((cx + 3, cz - 6), (cx + 3, cz - 3)):
        for k, y in ((0, 1), (0, 2), (1, 3)):
            for x in range(px + k, px + 6 - k):
                C.set(x, y, pz, "dark_oak_log[axis=x]")
                if y < 3:
                    C.set(x, y, pz + 1, "dark_oak_log[axis=x]")
    # stumps and a chopping block
    for (x, z) in ((cx - 7, cz - 5), (cx + 8, cz + 4), (cx - 4, cz + 7)):
        C.set(x, 1, z, "dark_oak_wood[axis=y]")
    C.set(cx - 1, 1, cz - 2, "stripped_dark_oak_wood[axis=y]")
    C.set(cx - 1, 2, cz - 2, "oak_pressure_plate[powered=false]")
    # a saw horse with a log on it
    for x in (cx - 6, cx - 3):
        C.set(x, 1, cz + 1, "spruce_fence")
    for x in range(cx - 7, cx - 1):
        C.set(x, 2, cz + 1, "dark_oak_log[axis=x]")
    # the tent: a canvas ridge on fence posts
    tx, tz = cx - 8, cz + 3
    for z in range(tz, tz + 5):
        C.set(tx, 1, z, "spruce_fence")
        C.set(tx + 4, 1, z, "spruce_fence")
        for y in (2, 3):
            C.set(tx, y, z, "brown_wool")
            C.set(tx + 4, y, z, "brown_wool")
        C.set(tx + 1, 4, z, "white_wool")
        C.set(tx + 3, 4, z, "white_wool")
        C.set(tx + 2, 5, z, "brown_wool")
    C.set(tx + 2, 1, tz + 3, "brown_bed[facing=south,part=foot,occupied=false]")
    C.set(tx + 2, 1, tz + 4, "brown_bed[facing=south,part=head,occupied=false]")
    chest(C, tx + 1, 1, tz + 4, "east", "asy_camp")
    C.set(cx + 1, 1, cz + 4, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, f) in ((cx, cz + 5, "south"), (cx + 2, cz + 5, "south"), (cx + 3, cz + 3, "east")):
        C.set(x, 1, z, stair("spruce_stairs", f))
    barrel(C, cx + 7, 1, cz - 1)
    C.set(cx + 7, 2, cz - 1, "barrel[facing=up,open=false]")
    C.set(cx + 6, 1, cz - 1, "grindstone[face=floor,facing=north]")
    lamp_post(C, cx - 3, 1, cz - 7)
    C.set(28, 0, 94, PDS)
    C.set(28, 1, 94, MOD["waystone"])
    lamp_post(C, 26, 1, 95)


def fence_run(C, a0, a1, fixed, axis, seed):
    """A crooked wrought-iron fence on a deepslate kerb: posts every 5, bays leaning off line, a few bays fallen."""
    for a in range(a0, a1 + 1):
        x, z = (a, fixed) if axis == "x" else (fixed, a)
        if (x, 1, z) in C.keep:
            continue
        bay = (a - a0) // 5
        post = (a - a0) % 5 == 0
        lean = hash01(bay, fixed, seed) < 0.35
        fallen = hash01(bay, fixed, seed + 1) < 0.1 and not post
        C.set(x, 0, z, DSB) if C.get(x, 0, z) is None else None
        C.set(x, 1, z, DSB_WALL if post else DSB)
        if post:
            C.set(x, 2, z, DSB_WALL)
            C.set(x, 3, z, ROD_U)
            continue
        if fallen:
            continue
        C.set(x, 2, z, BARS)
        if not lean or (a - a0) % 5 in (1, 2):
            C.set(x, 3, z, BARS)
        if not lean and (a - a0) % 5 == 2:
            C.set(x, 4, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def gatehouse(C):
    """The gatehouse in the perimeter fence: two square towers with steep slate roofs, a pointed archway with a
    half-raised portcullis, a clock in the gable foreshadowing the tower, guard rooms on the yard side."""
    zf, zb = 58, 66
    for s in (-1, 1):
        x0, x1 = (7, 13) if s > 0 else (-13, -7)
        for x in range(x0, x1 + 1):
            for z in range(zf, zb + 1):
                C.set(x, 0, z, DSB)
                edge = x in (x0, x1) or z in (zf, zb)
                for y in range(1, 19):
                    if edge or y >= 7:
                        C.set(x, y, z, wmat(x, y, z, 0) if not (edge and y in (7, 13)) else PT)
                    else:
                        C.clear(x, y, z)
                if not edge:
                    C.set(x, 0, z, DST)
        # stepped corner buttresses
        for (bx, bz) in ((x0, zf), (x1, zf), (x0, zb), (x1, zb)):
            ox = -1 if bx == x0 else 1
            oz = -1 if bz == zf else 1
            for y in range(1, 12):
                C.set(bx + ox, y, bz, DSB if y < 4 else TB)
                C.set(bx, y, bz + oz, DSB if y < 4 else TB)
            C.set(bx + ox, 12, bz, stair(TB_ST, OPP[face_of(ox, 0)]))
            C.set(bx, 12, bz + oz, stair(TB_ST, OPP[face_of(0, oz)]))
        # a steep slate roof (two blocks of rise per step) and a brass needle
        steep_roof(C, x0, zf, x1, zb, 19, rise=2)
        cxm = (x0 + x1) // 2
        # slit windows (barred) on the outer faces, the guard-room door on the yard side
        for y in (3, 4):
            C.set(cxm, y, zb, BARS)
            C.set(x0 if s < 0 else x1, y, (zf + zb) // 2, BARS)
        C.bp.door(cxm, 1, zf, "north", wood="dark_oak")
        C.clear(cxm, 1, zf - 1)
        C.clear(cxm, 2, zf - 1)
        hang(C, cxm, 5, (zf + zb) // 2, LANT_H)
        if s < 0:
            C.set(x0 + 1, 1, zf + 2, "red_bed[facing=south,part=foot,occupied=false]")
            C.set(x0 + 1, 1, zf + 3, "red_bed[facing=south,part=head,occupied=false]")
            chest(C, x0 + 1, 1, zb - 1, "east", "asy_gate")
            C.set(x1 - 1, 1, zb - 1, TABLE)
            spawner(C, x1 - 1, 1, zf + 3, MOB_KNIGHT)
        else:
            barrel(C, x1 - 1, 1, zb - 1)
            C.set(x0 + 1, 1, zb - 1, "smithing_table")
            C.set(x0 + 1, 1, zf + 2, W + "wall_shelf[facing=east]")
            C.set(x1 - 1, 1, zf + 2, "grindstone[face=floor,facing=north]")
    # the centre block with the archway
    for x in range(-6, 7):
        for z in range(zf, zb + 1):
            C.set(x, 0, z, DSB if abs(x) > 2 else PDS)
            for y in range(1, 16):
                if abs(x) <= 2:
                    top = 7 if abs(x) <= 1 else 6
                    if y <= top:
                        C.clear(x, y, z)
                        continue
                C.set(x, y, z, wmat(x, y, z, 0) if y != 15 else PT)
        for y in range(16, 18):
            if x % 2 == 0:
                C.set(x, y, zf, TB_WALL)
                C.set(x, y, zb, TB_WALL)
    for x in range(-6, 7):
        for z in range(zf + 1, zb):
            C.set(x, 16, z, ROOF_SL + "[type=bottom,waterlogged=false]")
    # arch voussoirs and the portcullis (raised: bars only in its top three rows)
    for z in (zf, zb):
        for x in (-3, 3):
            for y in range(1, 7):
                C.set(x, y, z, PDS)
        for x in range(-2, 3):
            C.set(x, 8 if abs(x) <= 1 else 7, z, CTB)
    for x in range(-2, 3):
        for y in range(5, 8):
            if C.free(x, y, 62):
                C.set(x, y, 62, BARS)
    for x in range(-2, 3):
        for y in range(1, 5):
            C.keep.add((x, y, 62))
    # the gable clock (a small brass dial) over the arch, both faces
    for z in (zf - 1, zb + 1):
        for du in range(-2, 3):
            for dv in range(-2, 3):
                if math.hypot(du, dv) <= 2.3:
                    C.set(du, 11 + dv, z, GILD if math.hypot(du, dv) > 1.4 else "white_concrete")
        C.set(0, 11, z, ENGR)
        C.set(0, 12, z, IRON)
    hang(C, 0, 6, 62 - 2, LANT_H)
    hang(C, 0, 6, 62 + 3, LANT_H)
    # the fence
    fence_run(C, -64, -14, 62, "x", 401)
    fence_run(C, 14, 64, 62, "x", 402)
    fence_run(C, 30, 61, -64, "z", 403)
    fence_run(C, 30, 61, 64, "z", 404)


def steep_roof(C, x0, z0, x1, z1, y, rise=2, over=1, finial=True):
    """A steep hipped roof over a solid core: rings stepping in one block per ``rise`` blocks, slate stairs on the
    first row of each step, full tiles under them; a brass needle on top."""
    i, yy = -over, y
    while True:
        ax0, az0, ax1, az1 = x0 + i, z0 + i, x1 - i, z1 - i
        if ax0 > ax1 or az0 > az1:
            break
        for k in range(rise):
            for x in range(ax0, ax1 + 1):
                for z in range(az0, az1 + 1):
                    ring = x in (ax0, ax1) or z in (az0, az1)
                    if ring and k == rise - 1 and ax0 < ax1 and az0 < az1:
                        f = "south" if z == az0 else "north" if z == az1 else "east" if x == ax0 else "west"
                        C.set(x, yy + k, z, stair(ROOF_ST, f))
                    else:
                        C.set(x, yy + k, z, ROOF)
        if i == -over:
            for x in range(ax0, ax1 + 1):
                for z in range(az0, az1 + 1):
                    if x in (ax0, ax1) or z in (az0, az1):
                        C.set(x, yy - 1, z, DOP)
        if ax0 == ax1 or az0 == az1:
            yy += rise
            break
        i += 1
        yy += rise
    if finial:
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        C.set(cx, yy, cz, BRASS)
        C.set(cx, yy + 1, cz, ROD_U)
    return yy


def yard(C):
    """Paths from the camp to the gate, the yard behind it, the stair up the hill's flank to the cemetery."""
    path(C, [(28, 92), (30, 86), (20, 79), (8, 73), (0, 70), (0, 67)], 0, 4, gravel_path)
    path(C, [(0, 57), (0, 52)], 0, 5, flags)
    path(C, [(0, 54), (-12, 58), (-26, 59), (-36, 59)], 0, 3, flags)
    path(C, [(0, 54), (12, 50), (20, 47)], 0, 3, gravel_path)
    climb(C, -36, 57, "north", 11, 1, 3, mat=DSB_ST, support=DSB, rails=DSB_WALL, landing=PDS)
    for (x, z) in ((-5, 55), (5, 55), (-20, 61), (-31, 61), (10, 47)):
        if C.free(x, 1, z) and (x, 1, z) not in C.keep:
            lamp_post(C, x, 1, z)
    # an overturned hearse in the yard: a black box on its side, a wheel, a broken shaft
    for x in range(-14, -9):
        for y in (1, 2):
            C.set(x, y, 46, "black_concrete" if y == 1 else "black_terracotta")
    C.set(-15, 1, 46, "dark_oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    for (x, y) in ((-13, 3), (-11, 3)):
        C.set(x, y, 46, "dark_oak_fence")
    C.set(-9, 1, 47, "dark_oak_fence")
    C.set(-8, 1, 48, "dark_oak_fence")


# ------------------------------------------------------------------ the cemetery
def headstone(C, x, z, kind):
    y = CY + 1
    if kind == 0:
        C.set(x, y, z, CTB)
        C.set(x, y + 1, z, TB_SL + "[type=bottom,waterlogged=false]")
    elif kind == 1:
        C.set(x, y, z, DSB_WALL)
        C.set(x, y + 1, z, "stone_button[face=floor,facing=north,powered=false]")
    elif kind == 2:
        C.set(x, y, z, "cobbled_deepslate_wall")
        C.set(x, y + 1, z, "cobbled_deepslate_wall")
        C.set(x - 1, y + 1, z, "iron_bars")
        C.set(x + 1, y + 1, z, "iron_bars")
    elif kind == 3:
        C.set(x, y, z, stair(DSB_ST, "south" if hash01(x, z, 501) < 0.5 else "east"))     # a fallen stone
    else:
        C.set(x, y, z, PDS)
        C.set(x, y + 1, z, PDS_SL + "[type=bottom,waterlogged=false]")


def cemetery(C):
    """The walled cemetery terrace: a deepslate kerb with crooked iron railings, rows of graves, the mausoleum, the
    gravedigger's shed and a dead tree; crypt crawlers in the graves."""
    # rim: a kerb and leaning railings where the terrace falls away
    rim = []
    for (x, z), t in C.top.items():
        if t != CY or cem_norm(x, z) > 1.05:
            continue
        for (dx, dz) in N4:
            tn = C.top.get((x + dx, z + dz))
            if tn is None or tn < CY:
                rim.append((x, z))
                break
    for (x, z) in rim:
        if (x, CY + 1, z) in C.keep:
            continue
        post = (x * 3 + z * 7) % 6 == 0
        C.set(x, CY + 1, z, DSB_WALL if post else DSB)
        if post:
            C.set(x, CY + 2, z, DSB_WALL)
            C.set(x, CY + 3, z, ROD_U)
        elif hash01(x, z, 511) > 0.12:
            C.set(x, CY + 2, z, BARS)
            if hash01(x // 3, z // 3, 512) < 0.6:
                C.set(x, CY + 3, z, BARS)
    # walks
    path(C, [(-36, 46), (-36, 36), (-30, 31), (-24, 28)], CY, 3, flags)
    path(C, [(-36, 37), (-48, 31), (-60, 23)], CY, 2, gravel_path)
    path(C, [(-36, 40), (-46, 37)], CY, 2, gravel_path)
    climb(C, -24, 26, "north", 11, CY + 1, 3, mat=DSB_ST, support=DSB, rails=DSB_WALL, landing=PDS)
    climb(C, -60, 21, "north", 11, CY + 1, 3, mat=DSB_ST, support=DSB, rails=DSB_WALL, landing=PDS, lamps=False)
    mausoleum(C)
    shed(C)
    dead_tree(C, -46, CY + 1, 23)
    # graves in rows: a headstone, a mound, now and then a candle or a wilted flower
    for z in range(18, 45, 4):
        for x in range(-60, -15, 3):
            jx = x + (1 if hash01(x, z, 521) < 0.3 else 0)
            if C.top.get((jx, z)) != CY or C.top.get((jx, z + 2)) != CY or cem_norm(jx, z + 2) > 0.93:
                continue
            cells = [(jx, CY + 1, z), (jx, CY + 1, z + 1), (jx, CY + 1, z + 2), (jx, CY + 2, z)]
            if any(c in C.keep or not C.free(*c) for c in cells):
                continue
            if any(not C.free(jx + dx, CY + 1, z + dz) for dx in (-1, 1) for dz in (0, 1, 2)):
                continue
            kind = int(hash01(jx, z, 522) * 5)
            headstone(C, jx, z, kind)
            for dz in (1, 2):
                C.set(jx, CY, z + dz, "coarse_dirt" if hash01(jx, z + dz, 523) < 0.5 else "rooted_dirt")
            h = hash01(jx, z, 524)
            if h < 0.15:
                candle(C, jx, CY + 1, z + 1, 1 + int(h * 20) % 3)
            elif h < 0.3:
                C.set(jx, CY + 1, z + 2, "wither_rose")
            elif h > 0.9:
                C.set(jx, CY + 1, z + 1, "pale_moss_carpet[bottom=true,east=none,north=none,south=none,west=none]")
    for (x, z) in ((-40, 44), (-32, 44), (-36, 30), (-27, 33), (-52, 28)):
        if C.top.get((x, z)) == CY and C.free(x, CY + 1, z) and (x, CY + 1, z) not in C.keep:
            lamp_post(C, x, CY + 1, z, soul=True)
    spawner(C, -42, CY + 1, 20, MOB_CRAWLER)
    spawner(C, -28, CY + 1, 38, MOB_CRAWLER)


def mausoleum(C):
    """A small gothic tomb: deepslate tiles, a pediment, an open bronze door; a sarcophagus inside."""
    x0, z0, x1, z1 = -57, 31, -49, 41
    f = CY
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(f - 2, f + 1):
                C.set(x, y, z, PDS if y == f else DSB)
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(f + 1, f + 7):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    C.set(x, y, z, PDS if corner else (CDSB if hash3(x, y, z, 531) < 0.15 else DST))
                else:
                    C.clear(x, y, z)
            C.set(x, f + 7, z, PDS)
    # pediment gable along x, the door in the east face
    for k in range(0, 4):
        for z in range(z0 + k, z1 - k + 1):
            for x in range(x0 - 1, x1 + 2):
                if z in (z0 + k, z1 - k):
                    C.set(x, f + 8 + k, z, stair(DSB_ST, "south" if z == z0 + k else "north"))
                else:
                    C.set(x, f + 8 + k, z, DST)
    for z in range(35, 38):
        for y in range(f + 1, f + 4):
            C.clear(x1, y, z)
        C.set(x1 + 1, f, z, PDS)
        C.set(x1 + 2, f, z, PDS) if C.top.get((x1 + 2, z)) == CY else None
    C.set(x1, f + 4, 36, CT)
    for z in (34, 38):
        for y in range(f + 1, f + 5):
            C.set(x1 + 1, y, z, PDS)
        C.set(x1 + 1, f + 5, z, "skeleton_skull[rotation=12]")
    # the sarcophagus
    for x in range(-55, -51):
        C.set(x, f + 1, 36, PDS)
        C.set(x, f + 2, 36, PDS_SL + "[type=bottom,waterlogged=false]")
    C.set(-56, f + 1, 36, "skeleton_skull[rotation=4]")
    candle(C, -54, f + 1, 33, 3)
    candle(C, -54, f + 1, 39, 2)
    chest(C, -56, f + 1, 33, "south", "asy_crypt")
    C.set(-56, f + 1, 39, COBWEB)
    hang(C, -53, f + 4, 36, SOUL_H)
    spawner(C, -51, f + 1, 33, MOB_CRAWLER)


def shed(C):
    """The gravedigger's lean-to: posts, a slab roof, tools, a barrel and his chest."""
    x0, z0, x1, z1 = -23, 38, -18, 43
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(CY + 1, CY + 4):
            C.set(x, y, z, SDO)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, CY + 4, z, DO_SL + "[type=bottom,waterlogged=false]")
    for z in range(z0 + 1, z1):
        C.set(x1, CY + 1, z, DOP)
        C.set(x1, CY + 2, z, DOP)
    chest(C, x1 - 1, CY + 1, z0 + 1, "west", "asy_cemetery")
    barrel(C, x1 - 1, CY + 1, z1 - 1)
    C.set(x0 + 1, CY + 1, z1 - 1, "composter[level=3]")
    C.set(x1 - 1, CY + 2, z0 + 2, W + "wall_shelf[facing=west]")
    hang(C, x0 + 2, CY + 3, z0 + 2, LANT_H)


def dead_tree(C, x, y, z):
    """A dead, gnarled oak: a leaning trunk, bare branches, a lantern and a noose of chain."""
    for i in range(8):
        ox = 1 if i > 4 else 0
        C.put(x + ox, y + i, z, "dark_oak_wood[axis=y]")
    for (dx, dy, dz, ax) in ((1, 5, 0, "x"), (2, 6, 0, "x"), (3, 7, 0, "x"), (-1, 4, 0, "x"), (-2, 5, 0, "x"),
                             (0, 6, 1, "z"), (0, 7, 2, "z"), (1, 8, -1, "z"), (1, 9, -2, "z")):
        C.put(x + dx, y + dy, z + dz, f"dark_oak_log[axis={ax}]")
    C.put(x + 3, y + 6, z, CHAIN)
    C.put(x + 3, y + 5, z, SOUL_H)
    C.put(x - 2, y + 4, z, CHAIN)


# ------------------------------------------------------------------ the forecourt and the funicular
def forecourt(C):
    path(C, [(-24, 13), (-18, 8), (-6, 2), (0, -2)], P, 4, flags)
    path(C, [(0, -2), (0, 9)], P, 5, flags)
    path(C, [(-6, 2), (-30, 1), (-45, 0)], P, 3, flags)
    path(C, [(6, 2), (30, 1), (43, 0)], P, 3, flags)
    path(C, [(6, 3), (21, 9)], P, 2, gravel_path)
    # the dead fountain with an automaton statue
    cx, cz = 0, 6
    for x in range(-5, 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x, z - cz)
            if d <= 4.6:
                C.set(x, P, z, "gravel" if d < 3.6 else PT)
                if 3.6 <= d <= 4.6:
                    C.set(x, P + 1, z, PT_SL + "[type=bottom,waterlogged=false]")
                    C.keep.discard((x, P + 1, z))
    C.set(0, P + 1, cz, PDS)
    C.set(0, P + 2, cz, PDS)
    C.set(0, P + 3, cz, IRON)
    C.set(0, P + 4, cz, BRASS)
    C.set(-1, P + 4, cz, "lightning_rod[facing=west,powered=false,waterlogged=false]")
    C.set(1, P + 4, cz, "lightning_rod[facing=east,powered=false,waterlogged=false]")
    C.set(0, P + 5, cz, GAUGE)
    C.set(0, P + 6, cz, "copper_bulb[lit=false,powered=false]")
    for (x, z) in ((-8, -2), (8, -2), (-14, 4), (14, 4), (-26, 4), (26, 4), (-36, 3), (36, 3), (-4, 11), (4, 11)):
        if C.free(x, P + 1, z) and (x, P + 1, z) not in C.keep and C.top.get((x, z)) == P:
            lamp_post(C, x, P + 1, z)
    # dead hedges and benches
    for x in list(range(-20, -8)) + list(range(9, 21)):
        for z in (-3,):
            if C.free(x, P + 1, z) and (x, P + 1, z) not in C.keep:
                C.set(x, P + 1, z, "dead_bush" if hash01(x, z, 601) < 0.4 else "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    for (x, z, f) in ((-7, 9, "east"), (7, 9, "west")):
        for dz in (0, 1):
            if C.free(x, P + 1, z + dz):
                C.set(x, P + 1, z + dz, stair(DO_ST, f))


def funicular(C):
    """The funicular: a single track of powered rails on redstone blocks, from the upper station on the forecourt down
    a trestle to the lower station in the yard; a cart waits at each end."""
    x = 28
    # upper station: an engine house with the winding wheel, an open platform under a canopy
    for xx in range(22, 35):
        for z in range(1, 15):
            C.set(xx, P, z, DST if xx in (22, 34) or z in (1, 14) else PDS)
            for y in range(P + 1, P + 6):
                C.clear(xx, y, z) if (xx, z) != (x, 1) else None
    for xx in range(22, 35):
        for z in range(1, 6):
            edge = xx in (22, 34) or z == 1
            for y in range(P + 1, P + 8):
                if edge:
                    C.set(xx, y, z, wmat(xx, y, z) if y < P + 7 else PT)
                elif y == P + 7:
                    C.set(xx, y, z, PT)
    steep_roof(C, 22, 1, 34, 5, P + 8, rise=1, finial=False)
    for xx in (24, 32):
        for y in range(P + 1, P + 4):
            C.set(xx, y, 1, PANE)
    gear_disk(C, 33, P + 4, 3, 2.4, "z")
    for y in range(P + 1, P + 4):
        C.set(31, y, 3, IRON)
    C.set(31, P + 4, 3, GAUGE)
    for (px, pz) in ((22, 9), (22, 14), (34, 9), (34, 14)):
        for y in range(P + 1, P + 6):
            C.set(px, y, pz, IRON)
    for xx in range(21, 36):
        for z in range(6, 16):
            C.set(xx, P + 6, z, ROOF_SL + "[type=bottom,waterlogged=false]")
    hang(C, 26, P + 4, 10, HANG_LAMP)
    hang(C, 30, P + 4, 10, HANG_LAMP)
    chest(C, 23, P + 1, 2, "south", "asy_station")
    C.set(33, P + 1, 13, stair(DO_ST, "west"))
    C.set(33, P + 1, 12, stair(DO_ST, "west"))
    # the track
    for z in range(2, 54):
        y = rail_y(z)
        if z == 2 or z == 53:
            C.set(x, y, z, PDS)
            continue
        if z < RAIL0 or z >= RAIL0 + P:
            shape = "north_south"
        else:
            shape = "ascending_north"
        C.set(x, y - 1, z, "redstone_block")
        C.set(x, y, z, f"powered_rail[powered=true,shape={shape},waterlogged=false]")
        for hh in (1, 2, 3):
            C.clear(x, y + hh, z)
        # the trestle: bents every fourth step, posts down to the hill or the ground
        if RAIL0 <= z < RAIL0 + P - 1:
            for xx in (x - 1, x + 1):
                C.set(xx, y - 1, z, DO_SL + "[type=top,waterlogged=false]")
            if z % 4 == 0:
                for xx in range(x - 2, x + 3):
                    C.set(xx, y - 2, z, "dark_oak_log[axis=x]")
                for xx in (x - 2, x + 2):
                    for yy in range(y - 3, -1, -1):
                        if C.solid(xx, yy, z):
                            break
                        C.set(xx, yy, z, DO_LOG)
            for yy in range(y - 2, -1, -1):
                if C.solid(x, yy, z):
                    break
                C.set(x, yy, z, DO_LOG if z % 4 == 0 else "dark_oak_fence")
    C.bp.entity(x, P + 1, 8, {"id": "minecraft:minecart"})
    C.bp.entity(x, 1, 50, {"id": "minecraft:minecart"})
    # lower station: a long shed over the track's foot; its door opens from inside only
    x0, z0, x1, z1 = 22, 32, 34, 54
    for xx in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(xx, 0, z, DST if xx in (x0, x1) or z in (z0, z1) else PDS)
            edge = xx in (x0, x1) or z in (z0, z1)
            for y in range(1, 8):
                if edge:
                    if z == z0 and abs(xx - x) <= 1 and y >= rail_y(z) - 1:
                        C.clear(xx, y, z)
                        continue
                    C.set(xx, y, z, wmat(xx, y, z, 0) if y < 7 else PT)
                elif not (xx == x and y <= rail_y(z)) and not (xx == x and y == rail_y(z) - 1):
                    if not (xx == x and z < 39 and y < rail_y(z)):
                        C.clear(xx, y, z)
    for z in range(z0, z1 + 1):
        if z0 < z < z1:
            for y in range(1, rail_y(z) - 1):
                C.set(x, y, z, PDS)
    for z in range(z0 + 2, z1, 4):
        for y in (3, 4):
            C.set(x0, y, z, BARS)
            C.set(x1, y, z, BARS)
    for z in range(z0 - 1, z1 + 2):
        for xx in range(x0 - 1, x1 + 2):
            dx = abs(xx - x)
            y = 8 + (6 - dx) if dx <= 6 else 8
            if dx == 0:
                C.set(xx, y, z, ROOF)
            else:
                C.set(xx, y, z, stair(ROOF_ST, "east" if xx < x else "west"))
            C.set(xx, y - 1, z, DOP) if dx <= 6 else None
    for z in (z0, z1):
        for xx in range(x0, x1 + 1):
            dx = abs(xx - x)
            for y in range(8, 8 + (6 - dx)):
                if not (z == z0 and abs(xx - x) <= 1 and y <= rail_y(z) + 3):
                    C.set(xx, y, z, wmat(xx, y, z, 0))
    for xx in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            dx = abs(xx - x)
            for y in range(8, 8 + (6 - dx) - 1):
                if C.get(xx, y, z) is None:
                    C.bp.set(xx, y, z, AIR)
    for (xx, z) in ((25, 40), (31, 40), (25, 48), (31, 48)):
        hang(C, xx, 5, z, HANG_LAMP)
    iron_door(C, x0, 1, 46, "west", (x0 + 1, 2, 45), "east")
    C.clear(x0 - 1, 1, 46)
    C.clear(x0 - 1, 2, 46)
    for z in (36, 38):
        C.set(x1 - 1, 1, z, stair(DO_ST, "west"))
    C.set(x1 - 1, 1, 44, TABLE)
    barrel(C, x1 - 1, 1, 52)


# ------------------------------------------------------------------ generic roofs and windows
def gable(C, a0, a1, c, half, y0, axis, over=1, rafter=DOP, end_mat=None, glass=None, wall_top=None, ends=(True, True)):
    """A gable roof whose ridge runs along ``axis`` over a0..a1, centred on c, the walls ``half`` from the ridge; the
    eave stair is ``over`` beyond the wall at y0 and the roof climbs one block per block. Rafter planks under every
    roof block (the space below stays open); gable-end walls up to the roof line."""
    H = half + over
    for a in range(a0 - over, a1 + over + 1):
        for d in range(-H, H + 1):
            y = y0 + (H - abs(d))
            x, z = (a, c + d) if axis == "x" else (c + d, a)
            if d == 0:
                spec = ROOF
            elif axis == "x":
                spec = stair(ROOF_ST, "north" if d > 0 else "south")
            else:
                spec = stair(ROOF_ST, "west" if d > 0 else "east")
            if glass and glass(x, z) and abs(d) < half - 1:
                spec = "gray_stained_glass"
            C.set(x, y, z, spec)
            C.set(x, y - 1, z, rafter if spec != "gray_stained_glass" else "gray_stained_glass")
    if end_mat:
        wt = wall_top if wall_top is not None else y0 - 1
        for a, on in ((a0, ends[0]), (a1, ends[1])):
            if not on:
                continue
            for d in range(-half, half + 1):
                ytop = y0 + (H - abs(d)) - 2
                x, z = (a, c + d) if axis == "x" else (c + d, a)
                for y in range(wt + 1, ytop + 1):
                    C.set(x, y, z, end_mat(x, y, z))


def lancet(C, plane, fixed, u0, w, y0, h, spec=PANE, depth=1, out=1):
    """A pointed window ``w`` wide and ``h`` high in a wall plane (plane "x": wall along x at z = fixed; "z": wall
    along z at x = fixed); ``depth`` cells deep inward from the face (out = +1 when the outside is the + side)."""
    cu = u0 + (w - 1) / 2.0
    for u in range(u0, u0 + w):
        du = abs(u - cu)
        top = y0 + h - 1 - (1 if w >= 2 and du >= w / 2.0 - 0.5 and h >= 4 else 0)
        for y in range(y0, top + 1):
            for k in range(depth):
                f = fixed - out * k
                x, z = (u, f) if plane == "x" else (f, u)
                C.set(x, y, z, spec)


# ------------------------------------------------------------------ the main hall (hub)
HX0, HX1, HZ0, HZ1 = -16, 16, -31, -4       # hall outer (the north wall is the tower's south wall)


def hall_roof_y(x):
    return P + 29 + (17 - abs(x))


def main_hall(C):
    """The hub: a 45-high hall open to its rafters, a gallery on three sides, the portal with a wicket, a rose
    window, corner turrets with needle spires; the Iron Orderly statue, the desk and the waystone."""
    for x in range(HX0, HX1 + 1):
        for z in range(HZ0 + 2, HZ1 + 1):
            wall = abs(x) >= 15 or z >= -5
            C.set(x, P, z, PDS if wall else (PDS if (x + z) % 2 else PT))
            ytop = hall_roof_y(x) - 2 if abs(x) < 17 else P + 28
            for y in range(P + 1, ytop + 1):
                if wall:
                    if abs(x) >= 15 and y > P + 28:
                        continue
                    C.set(x, y, z, wmat(x, y, z) if y not in (P + 11, P + 28) else PT)
                else:
                    C.clear(x, y, z)
    gable(C, HZ0 + 2, HZ1, 0, 16, P + 29, "z", over=1, end_mat=lambda x, y, z: wmat(x, y, z), wall_top=P + 28,
          ends=(False, True))
    for z in (HZ1, HZ1 - 1):          # the front gable carries on through both wall layers
        for x in range(-15, 16):
            for y in range(P + 29, hall_roof_y(x) - 1):
                C.set(x, y, z, wmat(x, y, z))
    # buttresses on the front between portal and turrets
    for bx in (-8, 8):
        for y in range(P + 1, P + 24):
            dep = 3 if y < P + 10 else (2 if y < P + 18 else 1)
            for k in range(1, dep + 1):
                for xx in (bx, bx + (1 if bx > 0 else -1)):
                    C.set(xx, y, HZ1 + k, DSB if y < P + 3 else TB)
        C.set(bx, P + 24, HZ1 + 1, stair(TB_ST, "north"))
    # the portal: a pointed arch 9 wide, 15 high, oak leaves with iron studs, a wicket door 3 x 4 open
    for x in range(-4, 5):
        top = P + 15 - (0 if abs(x) <= 1 else (1 if abs(x) <= 2 else (3 if abs(x) <= 3 else 6)))
        for y in range(P + 1, top + 1):
            C.set(x, y, HZ1, AIR if abs(x) <= 1 and y <= P + 4 else (IRON if (x + y) % 3 == 0 else DOP))
            C.set(x, y, HZ1 - 1, AIR if abs(x) <= 1 and y <= P + 4 else DOP)
        C.set(x, top + 1, HZ1, CTB)
    for x in range(-1, 2):
        for y in range(P + 1, P + 5):
            C.clear(x, y, HZ1)
            C.clear(x, y, HZ1 - 1)
        C.set(x, P, HZ1, PDS)
        C.set(x, P, HZ1 + 1, PDS)
    for x in (-5, 5):
        for y in range(P + 1, P + 12):
            C.set(x, y, HZ1 + 1, PDS)
        C.set(x, P + 12, HZ1 + 1, GILD)
    # the rose window (both wall layers): tracery spokes round a brass hub
    rc = P + 24
    for x in range(-6, 7):
        for y in range(rc - 6, rc + 7):
            d = math.hypot(x, y - rc)
            if d > 5.7:
                continue
            a = math.atan2(y - rc, x)
            spoke = abs(math.sin(a * 4)) < 0.22
            if d < 1.3:
                spec = ENGR
            elif d > 4.8:
                spec = CTB
            elif spoke or abs(d - 3.0) < 0.45:
                spec = PT
            else:
                spec = "red_stained_glass_pane" if d < 3 else ("purple_stained_glass_pane" if hash01(x, y, 701) < 0.5
                                                               else "black_stained_glass_pane")
            C.set(x, y, HZ1, spec)
            C.set(x, y, HZ1 - 1, spec if spec.endswith("pane") else AIR)
    # lancets beside the portal and high on the free stretches of the side walls
    for x0 in (-12, 11):
        lancet(C, "x", HZ1, x0, 2, P + 5, 9, BARS)
        lancet(C, "x", HZ1 - 1, x0, 2, P + 5, 9, PANE)
    for sx in (-1, 1):
        for z0 in (-9, -29):
            lancet(C, "z", sx * 16, z0, 2, P + 18, 8, BARS)
            lancet(C, "z", sx * 15, z0, 2, P + 18, 8, PANE)
    # corner turrets with needle spires
    for sx in (-1, 1):
        turret(C, sx * 17, HZ1 - 1, 3.6, P + 40, 16)
    # the gallery (mezzanine) on the west, north and east sides
    for x in range(-14, 15):
        for z in range(-29, -5):
            if not (abs(x) >= 11 or z <= -26):
                continue
            C.set(x, P + 10, z, DOP)
            C.set(x, P + 11, z, "dark_oak_planks" if (x + z) % 3 else W + "mahogany_parquet")
            edge = (abs(x) == 11 and z > -26) or (z == -26 and abs(x) <= 11)
            if edge:
                f = "east" if x == -11 and z > -26 else ("west" if x == 11 and z > -26 else "south")
                railing(C, x, P + 12, z, f)
    for x in range(-11, 12):
        C.set(x, P + 9, -26, stair(DO_ST, "north", "top"))
    for z in range(-25, -5):
        C.set(-11, P + 9, z, stair(DO_ST, "west", "top"))
        C.set(11, P + 9, z, stair(DO_ST, "east", "top"))
    # gallery columns (2 x 2) with brass capitals
    for sx in (-1, 1):
        for z in (-25, -18, -11):
            for dx in (0, 1):
                for dz in (0, 1):
                    xx = sx * (10 - dx) if sx > 0 else -(10 - dx)
                    for y in range(P + 1, P + 10):
                        C.set(xx, y, z + dz, PDS if y in (P + 1, P + 2) else (GILD if y == P + 9 else DSB))
    # floor: a red runner from the portal to the statue, a brass compass in the middle
    for z in range(-20, -5):
        for x in (-1, 0, 1):
            carpet(C, x, P + 1, z, "red")
            C.keep.discard((x, P + 1, z))
    for x in range(-3, 4):
        for z in range(-17, -10):
            if math.hypot(x, z + 14) <= 3.2 and abs(x) > 1:
                C.set(x, P, z, BTILE if math.hypot(x, z + 14) > 2.2 else GILD)
    # the Iron Orderly: a 12-high automaton in the north half, its hand raised toward the tower
    orderly(C, 0, P + 1, -22)
    # waystone (hub), the reception desk, benches, the director's portrait gallery upstairs
    C.set(6, P, -9, BTILE)
    C.set(6, P + 1, -9, MOD["waystone"])
    for x in range(-8, -3):
        C.set(x, P + 1, -10, TABLE if x != -8 else W + "mahogany_panelling")
    C.set(-8, P + 1, -9, W + "mahogany_panelling")
    C.set(-6, P + 2, -10, GAUGE)
    C.set(-5, P + 2, -10, "candle[candles=2,lit=true,waterlogged=false]")
    C.set(-6, P + 1, -11, W + "mahogany_chair[facing=south]")
    chest(C, -4, P + 1, -11, "south", "asy_hall")
    for z in range(-22, -6, 3):
        for sx in (-1, 1):
            if (sx * 14, P + 1, z) not in C.keep and abs(z + 18) > 2:
                C.set(sx * 14, P + 1, z, stair(DO_ST, "east" if sx < 0 else "west"))
    for (x, z) in ((0, -12), (0, -24)):
        hang(C, x, P + 22, z, CHANDELIER, reach=30)
    for (x, z) in ((-12, -8), (12, -8), (-12, -28), (12, -28)):
        hang(C, x, P + 15, z, HANG_LAMP, reach=20)
    for x in range(-9, 10, 3):
        if x != 0:
            C.set(x, P + 12, -28, W + "wall_shelf[facing=south]")
            C.set(x, P + 13, -29, "bookshelf")
    # the basement stair (from the baths, through a one-way door) comes up by the east wall
    for x in (8, 9, 10, 11, 12):
        railing(C, x, P + 1, -16, "south")
        railing(C, x, P + 1, -12, "north")
    for z in range(-15, -12):
        railing(C, 12, P + 1, z, "west")


def turret(C, cx, cz, r, ytop, spire_h):
    """A round corner turret, solid, with slit windows and a needle spire."""
    for x in range(int(cx - r) - 1, int(cx + r) + 2):
        for z in range(int(cz - r) - 1, int(cz + r) + 2):
            d = math.hypot(x - cx, z - cz)
            if d > r + 0.3:
                continue
            for y in range(P + 1, ytop + 1):
                ring = d > r - 0.9
                spec = wmat(x, y, z) if ring else "stone"
                if ring and (y - P) % 12 == 0:
                    spec = PT
                C.set(x, y, z, spec)
            if d > r - 0.9:
                C.set(x, ytop + 1, z, TB_WALL if (x + z) % 2 else TB)
    for k in range(spire_h):
        rr = (r + 0.6) * (1 - k / spire_h)
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for z in range(int(cz - r) - 1, int(cz + r) + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.2:
                    C.set(x, ytop + 1 + k, z, ROOF if d > rr - 1.0 or k % 4 else ROOF)
    C.set(int(cx), ytop + 1 + spire_h, int(cz), BRASS)
    C.set(int(cx), ytop + 2 + spire_h, int(cz), ROD_U)


def orderly(C, x, y, z):
    """The Iron Orderly, a hulking automaton nurse: a plinth, dark iron legs, a brass boiler torso with a gauge, a
    copper head with lit eyes, one arm raised with a lantern."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            C.set(x + dx, y, z + dz, PDS if max(abs(dx), abs(dz)) == 2 else GILD)
    for dx in (-1, 1):
        for k in range(1, 5):
            C.set(x + dx, y + k, z, IRON)
    for dx in range(-2, 3):
        for k in range(5, 9):
            if abs(dx) == 2 and k in (5, 8):
                continue
            C.set(x + dx, y + k, z, BRASS if abs(dx) < 2 else COPPER)
        C.set(x + dx, y + 5, z - 1, IRON) if abs(dx) < 2 else None
    C.set(x, y + 6, z + 1, GAUGE)
    C.set(x, y + 7, z + 1, "copper_grate")
    for k in (9, 10):
        for dx in (-1, 0, 1):
            C.set(x + dx, y + k, z, VERD)
    C.set(x, y + 11, z, ENGR)
    C.set(x, y + 12, z, ROD_U)
    C.set(x - 1, y + 9, z + 1, "redstone_lamp[lit=true]")
    C.set(x + 1, y + 9, z + 1, "redstone_lamp[lit=true]")
    for k in range(6, 12):
        C.set(x + 3, y + k, z, IRON if k < 11 else BRASS)
    C.set(x + 3, y + 12, z, CHAIN)
    for k in range(4, 8):
        C.set(x - 3, y + k, z, IRON)
    C.set(x - 3, y + 3, z, "tripwire_hook[attached=false,facing=south,powered=false]")


# ------------------------------------------------------------------ the ward wings
def wx(s, u):
    return s * u


def wing(C, s):
    """One ward wing, u = |x| from 17 (the hall) to 57, plus its stair pavilion u 58..68. s = -1 west, +1 east."""
    east = s > 0
    zN, zS = -26, -10
    for u in range(17, 58):
        x = wx(s, u)
        for z in range(zN, zS + 1):
            edge = z in (zN, zS)
            # plinth or basement wall below the ground floor
            for y in range(P - 6 if east else P + 1, WG):
                if y <= P and not edge:
                    continue
                if edge:
                    C.set(x, y, z, DSB if hash3(x, y, z, 721) > 0.12 else CDSB)
                elif not east or u < 21:
                    C.set(x, y, z, "stone")
            C.set(x, WG - 1, z, DST if not edge else DSB)
            C.set(x, WG, z, DOP if not edge else PT)
            for y in range(WG + 1, WT + 1):
                if edge:
                    spec = wmat(x, y, z, WG)
                    if y in (W2,):
                        spec = PT
                    C.set(x, y, z, spec)
                elif W2 - 1 <= y <= W2:
                    C.set(x, y, z, DST if y == W2 - 1 else DOP)
                else:
                    C.clear(x, y, z)
    # the roof: ridge along x at z -18, the upper floor open to the rafters
    glass = None
    if not east:
        def glass(x, z):
            return -55 <= x <= -41 and -21 <= z <= -15
    gable(C, wx(s, 17) if s > 0 else wx(s, 57), wx(s, 57) if s > 0 else wx(s, 17), -18, 8, WT + 1, "x", over=1,
          glass=glass)
    for u in range(17, 58):
        x = wx(s, u)
        for z in range(zN + 1, zS):
            ry = WT + 1 + (9 - abs(z + 18)) - 2
            for y in range(WT + 1, ry + 1):
                C.clear(x, y, z)
    # buttresses, string courses, barred windows (one per cell, aligned on both floors)
    for z, o in ((zN, -1), (zS, 1)):
        for u in (22, 32, 42, 52):
            for du in (0, 1):
                x = wx(s, u + du)
                for y in range(P + 1, WT - 1):
                    dep = 2 if y < W2 else 1
                    for k in range(1, dep + 1):
                        C.set(x, y, z + o * k, DSB if y < WG else TB)
                C.set(x, W2, z + o * 2, stair(TB_ST, OPP[face_of(0, o)]))
                C.set(x, WT - 1, z + o, stair(TB_ST, OPP[face_of(0, o)]))
        for k in range(8):
            u0 = 24 + 5 * k
            for du in (0, 1):
                x = wx(s, u0 + du)
                for y in range(WG + 2, WG + 5):
                    C.set(x, y, z, BARS)
                for y in range(W2 + 2, W2 + 6):
                    C.set(x, y, z, BARS)
                C.set(x, WG + 1, z + o, stair(TB_ST, OPP[face_of(0, o)], "top"))
                C.set(x, W2 + 1, z + o, stair(TB_ST, OPP[face_of(0, o)], "top"))
                C.set(x, WG + 5, z, CT)
                C.set(x, W2 + 6, z, CT)
                if east:
                    C.set(x, P + 1, z, BARS)
                    C.set(x, P + 2, z, BARS)
    # chimneys on the ridge
    for u in (27, 47):
        x0 = wx(s, u)
        for dx in (0, s):
            for dz in (0, 1):
                for y in range(WT + 8, WT + 14):
                    C.set(x0 + dx, y, -19 + dz, W + "sooty_smokestack_bricks" if y < WT + 13 else
                          W + "smokestack_bricks")
        C.set(x0, WT + 14, -19, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the junction with the hall: steps up from the hall floor to the ground floor, a door at gallery level
    for z in range(-19, -16):
        for k, y in enumerate(range(P + 1, P + 5)):
            x = wx(s, 17 + k)
            C.set(x, y, z, stair(DO_ST, "west" if s < 0 else "east"))
            for yy in range(y - 1, P, -1):
                C.set(x, yy, z, DOP)
            for hh in range(1, 4):
                C.clear(x, y + hh, z)
        for u in (15, 16):
            for y in range(P + 1, P + 5):
                C.clear(wx(s, u), y, z)
            for y in range(W2 + 1, W2 + 4):
                C.clear(wx(s, u), y, z)
            C.set(wx(s, u), W2, z, DOP)
            C.set(wx(s, u), P, z, PDS)
        C.set(wx(s, 17), W2, z, DOP)
    pavilion(C, s)


def pavilion(C, s):
    """The stair pavilion at the wing's end: taller than the wing, a steep hipped roof, a 3-wide stair from the ground
    floor to the upper floor along its outer wall."""
    u0, u1, zN, zS = 58, 68, -28, -8
    east = s > 0
    for u in range(u0, u1 + 1):
        x = wx(s, u)
        for z in range(zN, zS + 1):
            edge = u in (u0, u1) or z in (zN, zS)
            for y in range(P + 1, WG):
                C.set(x, y, z, DSB if edge else "stone")
            C.set(x, WG, z, PT if edge else DOP)
            for y in range(WG + 1, P + 23):
                if edge:
                    C.set(x, y, z, wmat(x, y, z, WG) if y not in (W2, P + 22) else PT)
                elif W2 - 1 <= y <= W2:
                    C.set(x, y, z, DST if y == W2 - 1 else DOP)
                elif y == P + 22:
                    C.set(x, y, z, DOP)
                else:
                    C.clear(x, y, z)
    xa, xb = sorted((wx(s, u0), wx(s, u1)))
    steep_roof(C, xa, zN, xb, zS, P + 23, rise=2)
    # gable wall closing the wing's roof against the pavilion
    for z in range(-27, -8):
        ry = WT + 1 + (9 - abs(z + 18))
        for y in range(P + 23, ry):
            C.set(wx(s, u0), y, z, wmat(wx(s, u0), y, z))
    # angle buttresses
    for (u, z) in ((u1, zN), (u1, zS)):
        for y in range(P + 1, P + 20):
            dep = 2 if y < P + 12 else 1
            for k in range(1, dep + 1):
                C.set(wx(s, u + k), y, z, DSB if y < WG else TB)
                C.set(wx(s, u), y, z + (k if z == zS else -k), DSB if y < WG else TB)
    # windows: tall lancets on the end face, barred
    for z0 in (-21, -15):
        lancet(C, "z", wx(s, u1), z0, 2, WG + 2, 4, BARS)
        lancet(C, "z", wx(s, u1), z0, 2, W2 + 2, 6, BARS)
    for x0 in (wx(s, 62), wx(s, 63)):
        for y in range(W2 + 2, W2 + 7):
            C.set(x0, y, zN, BARS)
            C.set(x0, y, zS, BARS)
    # openings to the wing on both floors
    for z in range(-19, -16):
        for y in range(WG + 1, WG + 4):
            C.clear(wx(s, u0), y, z)
        for y in range(W2 + 1, W2 + 4):
            C.clear(wx(s, u0), y, z)
    # the stair: three wide along the end wall (u 65..67), climbing north from z -11 to z -16, landing z -17..-19
    lats = [wx(s, 65), wx(s, 66), wx(s, 67)]
    for i in range(7):
        z = -11 - i
        y = WG + 1 + i
        for x in lats:
            C.set(x, y, z, stair(DO_ST, "north"))
            for yy in range(WG + 1, y):
                C.set(x, yy, z, DOP)
            for hh in range(1, 4):
                C.clear(x, y + hh, z)
    for x in lats:
        for hh in range(1, 4):
            C.clear(x, W2 + hh, -18)
    for i in range(6):
        z = -11 - i
        if WG + 1 + i + 3 >= W2 - 1:
            for x in lats:
                C.clear(x, W2, z)
                C.clear(x, W2 - 1, z)
    for i in range(6):
        z = -11 - i
        if C.free(lats[0], W2, z):
            railing(C, wx(s, 64), W2 + 1, z, "east" if s > 0 else "west")
    for x in lats:
        if C.free(x, W2, -10):
            pass
        railing(C, x, W2 + 1, -10, "north")
    for x in [wx(s, 64)]:
        railing(C, x, W2 + 1, -10, "north")
    for (u, z) in ((61, -22), (61, -14)):
        hang(C, wx(s, u), WG + 4, z, HANG_LAMP)
        hang(C, wx(s, u), P + 19, z, HANG_LAMP, reach=6)


def west_rooms(C):
    """Ground floor: the patient cells either side of a corridor. Upper floor: the operating theatre and the
    conversion ward."""
    s = -1
    # --- ground floor cells
    for u in range(22, 58, 5):
        x = wx(s, u)
        for z in list(range(-25, -19)) + list(range(-15, -10)):
            for y in range(WG + 1, W2 - 1):
                C.set(x, y, z, TB if u != 57 else wmat(x, y, z, WG))
    for k in range(7):
        ua, ub = 23 + 5 * k, 26 + 5 * k
        for (zf, zi, zo) in ((-20, -21, -25), (-16, -15, -11)):
            for u in range(ua, ub + 1):
                x = wx(s, u)
                for y in range(WG + 1, W2 - 1):
                    C.set(x, y, zf, BARS if y < W2 - 2 else TB)
            dx = wx(s, ua + 1)
            C.clear(dx, WG + 1, zf)
            C.clear(dx, WG + 2, zf)
            # furnish the cell
            padded = k in (2, 5)
            dz = 1 if zi > zf else -1
            xs = [wx(s, u) for u in range(ua, ub + 1)]
            if padded:
                for x in xs:
                    for z in range(min(zi, zo), max(zi, zo) + 1):
                        C.set(x, WG, z, "white_wool")
                for z in range(min(zi, zo), max(zi, zo) + 1):
                    for y in range(WG + 1, W2 - 1):
                        C.set(wx(s, ua - 1), y, z, "white_wool")
                        C.set(wx(s, ub + 1), y, z, "white_wool")
            bx = xs[-1]
            C.set(bx, WG + 1, zo - dz * 0, "white_bed[facing=%s,part=head,occupied=false]" % ("north" if zo < zi else "south"))
            C.set(bx, WG + 1, zo + (1 if zo < zi else -1),
                  "white_bed[facing=%s,part=foot,occupied=false]" % ("north" if zo < zi else "south"))
            if not padded:
                C.set(xs[0], WG + 3, zo, CHAIN.replace("axis=y", "axis=x"))
                C.set(xs[0], WG + 1, zo, "flower_pot" if k % 2 else "decorated_pot[facing=north,cracked=false,waterlogged=false]")
            if k == 4 and zf == -20:
                chest(C, xs[0], WG + 1, zo, "south", "asy_cells")
            if k == 1 and zf == -16:
                # a patient half-replaced by brass: a seated automaton
                C.set(xs[1], WG + 1, zo, W + "mahogany_chair[facing=north]")
                C.set(xs[1], WG + 2, zo, BRASS)
                C.set(xs[1], WG + 3, zo, GAUGE)
            if k in (0, 6):
                C.set(xs[1], WG + 4, zo, COBWEB)
    spawner(C, wx(s, 40), WG + 1, -23, MOB_BANSHEE)
    spawner(C, wx(s, 50), WG + 1, -13, MOB_BANSHEE)
    for u in range(24, 58, 6):
        hang(C, wx(s, u), WG + 4, -18, HANG_LAMP)
    C.set(wx(s, 21), WG + 1, -16, W + "mahogany_table")
    C.set(wx(s, 21), WG + 2, -16, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    # --- upper floor: the operating theatre (u 38..57) and the conversion ward (u 17..36)
    for z in range(-25, -10):
        for y in range(W2 + 1, WT + 9):
            x = wx(s, 37)
            ry = WT + 1 + (9 - abs(z + 18)) - 2
            if y <= ry:
                C.set(x, y, z, TB)
    for z in range(-19, -16):
        for y in range(W2 + 1, W2 + 4):
            C.clear(wx(s, 37), y, z)
    theatre(C)
    conversion_ward(C)


def theatre(C):
    """The operating theatre: tiered benches round three sides, the iron table under a ring lamp, four articulated
    brass surgical arms hanging from the rafters, instrument cabinets, a skylight."""
    s = -1
    cx, cz = -48, -20
    f = W2
    # tiers: three rising rows on the north and on the west (u 52..57), dark oak benches on stone risers
    for row in range(3):
        y = f + 1 + row
        z = -21 - row - 2
        for x in range(-56, -39):
            C.set(x, y, z - 0, stair(DO_ST, "south"))
            for yy in range(f + 1, y):
                C.set(x, yy, z, TB)
        x = -54 - row
        for z in range(-21, -12):
            if z in (-19, -18, -17):
                continue
            C.set(x, y, z, stair(DO_ST, "east"))
            for yy in range(f + 1, y):
                C.set(x, yy, z, TB)
    for x in range(-56, -39):
        for y in range(f + 1, f + 4):
            C.set(x, y, -25, TB) if C.get(x, y, -25) is None or C.free(x, y, -25) else None
    # the table
    for x in (cx - 1, cx, cx + 1):
        C.set(x, f + 1, cz, IRON if x != cx else "iron_block")
        C.set(x, f + 2, cz, W + "leather_padding_slab[type=bottom,waterlogged=false]")
    # ring lamp over it
    for (dx, dz) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        C.set(cx + dx, f + 8, cz + dz, BRASS)
    C.set(cx, f + 8, cz, "redstone_lamp[lit=true]")
    for y in range(f + 9, WT + 8):
        if C.free(cx, y, cz):
            C.set(cx, y, cz, CHAIN)
    # the surgical arms: a shoulder hung on a chain, an elbow, a forearm reaching down to the table, tool tips
    for (sx, sz) in ((-4, -3), (4, -3), (-4, 3), (4, 3)):
        ax, az = cx + sx, cz + sz
        ytop = WT + 4
        for y in range(f + 9, ytop + 1):
            if C.free(ax, y, az):
                C.set(ax, y, az, CHAIN)
        C.set(ax, f + 8, az, ENGR)
        ex, ez = cx + sx // 2 + (1 if sx > 0 else -1) * 0, cz + sz // 2
        C.set(ax - (1 if sx > 0 else -1), f + 7, az, BRASS)
        C.set(ex, f + 6, az - (1 if sz > 0 else -1), BRASS)
        tx, tz = cx + (1 if sx > 0 else -1), cz + (1 if sz > 0 else -1)
        C.set(tx, f + 5, tz, GEAR)
        C.set(tx, f + 4, tz, ROD_D)
    # cabinets and sinks on the south wall, a trolley
    for x in range(-53, -41):
        z = -11
        if x % 3 == 0:
            C.set(x, f + 1, z, "water_cauldron[level=2]")
        elif x % 3 == 1:
            C.set(x, f + 1, z, W + "mahogany_panelling")
            C.set(x, f + 2, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
        else:
            C.set(x, f + 1, z, W + "mahogany_panelling")
            C.set(x, f + 2, z, W + "wall_shelf[facing=north]")
    C.set(-44, f + 1, -14, TABLE)
    C.set(-44, f + 2, -14, "heavy_weighted_pressure_plate[power=0]")
    chest(C, -42, f + 1, -12, "west", "asy_theatre")
    spawner(C, -41, f + 1, -22, MOB_AUTO)
    for (x, z) in ((-52, -14), (-41, -15)):
        hang(C, x, f + 5, z, HANG_LAMP, reach=12)


def conversion_ward(C):
    """The conversion ward: brass-framed beds, half-built automata on stands, crates of parts, a workbench."""
    f = W2
    for k, x in enumerate(range(-35, -19, 4)):
        for (z, fac) in ((-24, "north"), (-12, "south")):
            hz = z
            fzz = z + (1 if fac == "north" else -1)
            C.set(x, f + 1, hz, f"red_bed[facing={fac},part=head,occupied=false]")
            C.set(x, f + 1, fzz, f"red_bed[facing={fac},part=foot,occupied=false]")
            C.set(x + 1, f + 1, hz, BRASS if k % 2 else IRON)
            C.set(x + 1, f + 2, hz, GAUGE if k % 2 else "copper_bulb[lit=true,powered=false]")
    # automata on stands down the middle
    for x in (-33, -27, -21):
        if x == -27:
            continue
        C.set(x, f + 1, -21, IRON)
        C.set(x, f + 2, -21, BRASS)
        C.set(x, f + 3, -21, VERD)
        C.set(x, f + 4, -21, "copper_grate")
        C.set(x - 1, f + 2, -21, "lightning_rod[facing=west,powered=false,waterlogged=false]")
        C.set(x + 1, f + 2, -21, "lightning_rod[facing=east,powered=false,waterlogged=false]")
    for x in (-34, -26):
        C.set(x, f + 1, -15, "crafting_table")
        C.set(x + 1, f + 1, -15, "smithing_table")
    barrel(C, -24, f + 1, -15)
    C.set(-23, f + 1, -15, "barrel[facing=up,open=false]")
    chest(C, -30, f + 1, -15, "north", "asy_ward")
    spawner(C, -27, f + 1, -21, MOB_SPIDER)
    for x in (-32, -24):
        hang(C, x, f + 5, -18, HANG_LAMP, reach=12)
    for y in range(f + 1, f + 4):
        C.set(-36, y, -25, PIPES)


def east_rooms(C):
    """Ground floor: the Nightingale ward. Upper floor: the records archive and the laundry with its chute. Below:
    the hydrotherapy baths."""
    s = 1
    f = WG
    # --- the Nightingale ward: beds against both long walls between the windows, screens, the nurses' station
    for u in range(21, 57, 5):
        for (z, fac) in ((-25, "north"), (-11, "south")):
            x = wx(s, u + 1)
            fz = z + (1 if fac == "north" else -1)
            C.set(x, f + 1, z, f"white_bed[facing={fac},part=head,occupied=false]")
            C.set(x, f + 1, fz, f"white_bed[facing={fac},part=foot,occupied=false]")
            for zz in (z, fz):
                C.set(wx(s, u - 1), f + 1, zz, "white_wool")
                C.set(wx(s, u - 1), f + 2, zz, "white_carpet")
    for x in range(38, 43):
        C.set(x, f + 1, -18, W + "mahogany_panelling")
    C.set(40, f + 2, -18, GAUGE)
    C.set(39, f + 2, -18, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
    C.set(41, f + 2, -18, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(40, f + 1, -17, W + "mahogany_chair[facing=north]")
    spawner(C, wx(s, 30), f + 1, -18, MOB_BANSHEE)
    for u in range(24, 58, 8):
        hang(C, wx(s, u), f + 4, -18, HANG_LAMP)
    # --- the laundry chute: a dark iron box through the ward, open from the upper floor to the basement pool
    cxs, czs = (52, 53), (-20, -19)
    for x in range(51, 55):
        for z in range(-21, -17):
            inner = x in cxs and z in czs
            for y in range(P - 5, W2 + 1):
                if inner:
                    C.clear(x, y, z)
                elif WG + 1 <= y <= W2 - 2:
                    C.set(x, y, z, IRON if (y + x) % 4 else GRILLE)
    for x in range(51, 55):
        for z in range(-21, -17):
            if not (x in cxs and z in czs):
                f2 = "north" if z == -21 else "south" if z == -18 else ("west" if x == 51 else "east")
                if not (z == -18 and x in cxs):
                    railing(C, x, W2 + 1, z, OPP[f2])
    C.set(52, W2 + 1, -17, "dark_oak_sign[rotation=8,waterlogged=false]")
    # --- the records archive (u 18..44)
    for x in range(20, 44, 3):
        for z in list(range(-25, -21)) + list(range(-15, -11)):
            for y in range(W2 + 1, W2 + 5):
                C.set(x, y, z, "bookshelf" if (x + y + z) % 4 else "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
    for x in range(26, 36, 4):
        C.set(x, W2 + 1, -18, TABLE)
        C.set(x, W2 + 2, -18, "candle[candles=1,lit=true,waterlogged=false]")
        C.set(x + 1, W2 + 1, -18, W + "mahogany_chair[facing=west]")
    C.set(38, W2 + 1, -19, "lectern[facing=west,has_book=false,powered=false]")
    chest(C, 43, W2 + 1, -20, "west", "asy_archive")
    spawner(C, 23, W2 + 1, -18, MOB_WISP)
    for x in (24, 32, 40):
        hang(C, x, W2 + 6, -18, HANG_LAMP, reach=12)
    for z in range(-25, -10):
        x = 45
        ry = WT + 1 + (9 - abs(z + 18)) - 2
        for y in range(W2 + 1, ry + 1):
            C.set(x, y, z, TB)
    for z in range(-19, -16):
        for y in range(W2 + 1, W2 + 4):
            C.clear(45, y, z)
    # --- the laundry (u 46..57): wash tubs, mangles, drying lines, baskets
    for x in range(47, 57, 2):
        if x in (51, 53):
            continue
        C.set(x, W2 + 1, -25, "water_cauldron[level=3]")
        C.set(x, W2 + 1, -11, "grindstone[face=floor,facing=north]" if x % 4 == 1 else "barrel[facing=up,open=false]")
    for x in range(47, 57):
        for z in (-14,):
            if C.free(x, W2 + 5, z):
                C.set(x, W2 + 5, z, CHAIN.replace("axis=y", "axis=x"))
    chest(C, 56, W2 + 1, -16, "west", "asy_laundry")
    for x in (48, 55):
        hang(C, x, W2 + 6, -18, HANG_LAMP, reach=12)
    baths(C)


def baths(C):
    """The hydrotherapy baths under the east wing: white-tiled, copper pipes along the vault, three restraint tubs, a
    plunge pool, the boilers and their gauges; the chute lands in a deep wash vat. Its west door opens from inside
    only, onto a stair up into the hall."""
    f = P - 6
    x0, x1, zN, zS = 21, 58, -26, -10
    for x in range(x0, x1 + 1):
        for z in range(zN, zS + 1):
            edge = x in (x0, x1) or z in (zN, zS)
            C.set(x, f - 1, z, "stone")
            C.set(x, f, z, ("white_concrete" if (x + z) % 2 else "light_gray_concrete") if not edge else DST)
            for y in range(f + 1, WG - 1):
                if edge:
                    C.set(x, y, z, DST if y < P else (DSB if hash3(x, y, z, 731) > 0.12 else CDSB))
                else:
                    C.clear(x, y, z)
    for x in range(x0 + 1, x1):
        for z in range(zN + 1, zS):
            C.set(x, WG - 1, z, DST)
    # basement windows in the plinth (bars in the outer wall) open into the vault
    # the restraint tubs on the north wall
    for k, xa in enumerate((23, 29, 35)):
        for x in range(xa, xa + 4):
            for z in (-25, -24, -23):
                rim = x in (xa, xa + 3) or z in (-25, -23)
                C.set(x, f + 1, z, "smooth_quartz" if rim else WATER)
                if not rim:
                    C.wet.add((x, f + 1, z))
        C.set(xa + 1, f + 2, -25, CHAIN.replace("axis=y", "axis=x"))
        C.set(xa + 2, f + 2, -25, W + "leather_padding")
        C.set(xa + 1, f + 4, -24, "copper_grate")
    # the plunge pool on the south side
    for x in range(24, 40):
        for z in range(-15, -11):
            C.water(x, f, z)
            C.set(x, f - 1, z, "white_concrete")
    for x in range(23, 41):
        for z in (-16,):
            C.set(x, f + 1, z, "smooth_quartz_slab[type=bottom,waterlogged=false]") if x % 4 else None
    # the deep wash vat under the chute
    for x in range(51, 55):
        for z in range(-21, -17):
            for y in (f - 2, f - 1, f):
                C.water(x, y, z)
            C.set(x, f - 3, z, "stone")
    # boilers, gauges, valves
    for (bx, bz) in ((45, -24), (45, -13)):
        for y in range(f + 1, f + 6):
            for dx in (0, 1):
                for dz in (0, 1):
                    C.set(bx + dx, y, bz + dz, IRON if y not in (f + 2, f + 5) else BRASS)
        C.set(bx - 1, f + 1, bz, "furnace[facing=west,lit=true]")
        C.set(bx - 1, f + 3, bz + 1, GAUGE)
        C.set(bx - 1, f + 2, bz + 1, W + "valve_wheel[facing=west]")
    for x in range(x0 + 1, x1):
        for z in (-25, -11):
            if C.free(x, WG - 2, z):
                C.set(x, WG - 2, z, W + "copper_pipe[axis=x]")
    for x in range(22, 58, 6):
        C.set(x, f + 3, zN + 1, EDISON)
        C.set(x, f + 3, zS - 1, EDISON)
    chest(C, 41, f + 1, -20, "west", "asy_baths")
    spawner(C, 47, f + 1, -18, MOB_DRONE)
    # the exit: one-way iron door in the west wall, a stair up to the hall's east side
    iron_door(C, x0, f + 1, -14, "west", (x0 + 1, f + 2, -13), "east")
    for z in range(-15, -12):
        for x in range(14, x0):
            C.set(x, f, z, DST)
            for hh in range(1, 4):
                C.clear(x, f + hh, z)
            C.set(x, f + 4, z, DST)
        for k, x in enumerate(range(13, 7, -1)):
            y = f + 1 + k
            C.set(x, y, z, stair(DSB_ST, "west"))
            for yy in range(f, y):
                C.set(x, yy, z, DSB)
            for hh in range(1, 4):
                C.clear(x, y + hh, z)
            C.set(x, f + 4 + k, z, DST) if f + 4 + k < y else None
    C.set(15, f + 3, -14, EDISON)


# ------------------------------------------------------------------ the clock tower
def tower_flight(C, k):
    """The stair from mechanism floor k to k + 1 (k = 4: into the clock stage): three wide on the west wall climbing
    north (k even) or on the east wall climbing south (k odd); the floor above opened over the top treads and railed.
    Returns the landing row's cells."""
    f0 = FL[k]
    f1 = FL[k + 1] if k < 4 else FC
    if k % 2 == 0:
        lats, r0, dr, d = (-12, -11, -10), -34, -1, "north"
    else:
        lats, r0, dr, d = (10, 11, 12), -54, 1, "south"
    n = f1 - f0
    for i in range(n):
        z = r0 + dr * i
        y = f0 + 1 + i
        for x in lats:
            C.set(x, y, z, stair(W + "diamond_plate_stairs", d))
            for yy in range(f0 + 1, y):
                C.set(x, yy, z, IRON if (i % 4 == 0 and x == lats[1]) else DIB)
            for hh in range(1, 4):
                C.clear(x, y + hh, z)
    hole = set()
    for i in range(n):
        z = r0 + dr * i
        for x in lats:
            if C.free(x, f1, z):
                hole.add((x, z))
    zl = r0 + dr * n
    land = []
    for x in lats:
        C.set(x, f1, zl, W + "diamond_plate")
        for hh in range(1, 4):
            C.clear(x, f1 + hh, zl)
        land.append((x, zl))
        for hh in range(1, 4):
            C.clear(x, f0 + hh, r0 - dr)
    for (x, z) in hole:
        for (dx, dz) in N4:
            q = (x + dx, z + dz)
            if q in hole or q in land or abs(q[0]) > 12 or not (-56 <= q[1] <= -32):
                continue
            if C.solid(q[0], f1, q[1]) and C.free(q[0], f1 + 1, q[1]):
                railing(C, q[0], f1 + 1, q[1], face_of(-dx, -dz))
    return land


SHAFT = (-3, 3, -47, -41)                   # pendulum shaft x0, x1, z0, z1


def tower(C):
    """The clock tower: the shaft with its buttresses and floors, the stairs, the pendulum, the mechanism rooms,
    the clock stage (arena) with its dials, the parapet, pinnacles, the lantern and the spire."""
    x0, x1, z0, z1 = -14, 14, -58, -30
    top = FC - 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x <= x0 + 1 or x >= x1 - 1 or z <= z0 + 1 or z >= z1 - 1
            C.set(x, P, z, PDS if wall else (DST if (x + z) % 2 else PDS))
            for y in range(P + 1, top + 1):
                if wall:
                    band = any(y == f for f in FL[1:]) or y == top
                    C.set(x, y, z, PT if band else wmat(x, y, z))
                else:
                    C.clear(x, y, z)
    # floors 2..5: a dark iron slab under plank or tread, the pendulum shaft left open
    sx0, sx1, sz0, sz1 = SHAFT
    for k in range(1, 5):
        f = FL[k]
        for x in range(x0 + 2, x1 - 1):
            for z in range(z0 + 2, z1 - 1):
                if sx0 <= x <= sx1 and sz0 <= z <= sz1:
                    continue
                C.set(x, f - 1, z, DIB)
                C.set(x, f, z, (DOP if (x // 3 + z // 3) % 2 else W + "diamond_plate") if k % 2 else
                      (W + "diamond_plate" if (x + z) % 5 else BTILE))
        for x in range(sx0 - 1, sx1 + 2):
            for z in range(sz0 - 1, sz1 + 2):
                if sx0 <= x <= sx1 and sz0 <= z <= sz1:
                    continue
                f2 = face_of(-x, TZ - z)
                railing(C, x, f + 1, z, f2)
    # angle buttresses, stepping in as they rise
    for (bx, bz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        ox = -1 if bx == x0 else 1
        oz = -1 if bz == z0 else 1
        for y in range(P + 1, top - 2):
            dep = 4 if y < P + 16 else (3 if y < P + 32 else (2 if y < P + 44 else 1))
            for k in range(1, dep + 1):
                for w in range(3):
                    C.set(bx + ox * k, y, bz - oz * w, DSB if y < P + 3 else TB)
                    C.set(bx - ox * w, y, bz + oz * k, DSB if y < P + 3 else TB)
        for yy, dep in ((P + 16, 4), (P + 32, 3), (P + 44, 2)):
            for w in range(3):
                C.set(bx + ox * dep, yy, bz - oz * w, stair(TB_ST, OPP[face_of(ox, 0)]))
                C.set(bx - ox * w, yy, bz + oz * dep, stair(TB_ST, OPP[face_of(0, oz)]))
    # lancets on the free faces (barred), lined with glass inside
    for k in range(5):
        f = FL[k]
        for (plane, fixed, inner, u0) in (("z", x0, x0 + 1, -45), ("z", x1, x1 - 1, -45), ("x", z0, z0 + 1, -1)):
            if k == 3 and fixed == x1:
                continue
            lancet(C, plane, fixed, u0, 2, f + 2, 6, BARS)
            lancet(C, plane, inner, u0, 2, f + 2, 6, PANE)
        if f + 2 > P + 46:
            lancet(C, "x", z1, -1, 2, f + 2, 6, BARS)
            lancet(C, "x", z1 - 1, -1, 2, f + 2, 6, PANE)
    # the doors: the winding hall's one-way iron door to the hall, the gallery doorway into the escapement room
    C.clear(0, P + 1, -30)
    C.clear(0, P + 2, -30)
    iron_door(C, 0, P + 1, -31, "south", (1, P + 2, -32), "north")
    for x in (-1, 0, 1):
        for y in range(W2 + 1, W2 + 4):
            C.clear(x, y, -30)
            C.clear(x, y, -31)
        C.set(x, W2, -30, DOP)
        C.set(x, W2, -31, DOP)
    clock_stage(C)
    # stairs
    for k in range(5):
        land = tower_flight(C, k)
    C.bp.mist(-12, FC + 1, -45, -10, FC + 3, -45)
    # the pendulum: a long chain from under the arena floor and a brass bob swinging through the escapement room
    for y in range(P + 17, FC - 1):
        C.set(0, y, TZ, CHAIN)
    for dx in range(-2, 3):
        for dy in range(-3, 4):
            d = math.hypot(dx, dy)
            if d <= 2.6:
                C.set(dx, P + 14 + dy, TZ, GILD if d > 1.8 else (ENGR if d < 0.9 else BRASS))
    mech_rooms(C)
    north_turret(C)


def mech_rooms(C):
    """The five mechanism floors, each a room of its own."""
    # M1: the winding hall (the shortcut's end): workbenches, crates, wall cogs, the drop-shaft passage
    f = FL[0]
    for x in range(-7, 8, 2):
        C.set(x, f + 1, -55, "crafting_table" if x % 4 == 1 else "smithing_table")
        C.set(x, f + 3, -56, W + "wall_cog[facing=south]")
    for (x, z) in ((-6, -36), (-6, -35), (6, -36), (5, -35)):
        barrel(C, x, f + 1, z) if (x, z) != (5, -35) else C.set(x, f + 1, z, "barrel[facing=up,open=false]")
    C.set(-5, f + 2, -36, "barrel[facing=up,open=false]")
    for z in range(-50, -37, 3):
        C.set(-8, f + 1, z, W + "mahogany_table") if z not in (-44,) else None
    chest(C, 7, f + 1, -54, "west", "asy_mechanism")
    spawner(C, 6, f + 1, -38, MOB_SPIDER)
    for (x, z) in ((-6, -50), (6, -50), (-6, -38), (6, -38)):
        hang(C, x, f + 7, z, HANG_LAMP, reach=6)
    # M2: the escapement room: the escapement wheel on the north wall, the anchor above it, gauges
    f = FL[1]
    gear_disk(C, 0, f + 5, -57, 4.2, "x")
    for dx, dy in ((-3, 9), (-2, 9), (-1, 9), (0, 9), (1, 9), (2, 9), (3, 9), (-3, 8), (3, 8)):
        C.set(dx, f + dy, -57, IRON)
    for x in range(-8, 9, 4):
        if abs(x) > 2:
            C.set(x, f + 2, -33, GAUGE)
            C.set(x, f + 3, -33, W + "copper_pipe[axis=y]")
            C.set(x, f + 4, -33, W + "copper_pipe[axis=y]")
    chest(C, -7, f + 1, -54, "east", "asy_mechanism")
    spawner(C, 6, f + 1, -52, MOB_SPIDER)
    for (x, z) in ((-6, -38), (6, -38), (-6, -50), (6, -50)):
        hang(C, x, f + 7, z, HANG_LAMP, reach=6)
    # M3: the going train: three meshing gears on the south wall, the great wheel's lower half on the north
    f = FL[2]
    gear_disk(C, -6, f + 5, -31, 3.0, "x")
    gear_disk(C, 1, f + 5, -31, 3.6, "x")
    gear_disk(C, 7, f + 4, -31, 1.8, "x")
    spawner(C, -6, f + 1, -51, MOB_AUTO)
    for (x, z) in ((-6, -38), (6, -38), (-6, -50), (6, -50)):
        hang(C, x, f + 7, z, HANG_LAMP, reach=6)
    # the great wheel (north wall plane) spanning M3 and M4
    gear_disk(C, 0, FL[3], -57, 9.2, "x")
    # M4: the great wheel's room: a balcony door east (a vista over the wing roofs), pinions, a chest
    f = FL[3]
    gear_disk(C, -11, f + 3, -57, 2.2, "x")
    gear_disk(C, 11, f + 3, -57, 2.2, "x")
    for z in range(-37, -34):
        for y in range(f + 1, f + 4):
            C.clear(13, y, z)
            C.clear(14, y, z)
        for xx in range(13, 19):
            C.set(xx, f, z, W + "diamond_plate" if xx < 15 else IRON_SLAB_TOP)
    for xx in range(15, 19):
        for z in (-38, -34):
            railing(C, xx, f + 1, z, "south" if z == -38 else "north")
    for z in range(-37, -34):
        railing(C, 18, f + 1, z, "west")
    for xx in range(15, 19):
        for z in range(-38, -33):
            C.set(xx, f - 1, z, stair(TB_ST, "west", "top") if xx == 18 else TB)
    chest(C, -7, f + 1, -36, "east", "asy_mechanism_high")
    spawner(C, 5, f + 1, -51, MOB_AUTO)
    for (x, z) in ((-6, -38), (6, -38), (-6, -50), (6, -50)):
        hang(C, x, f + 8, z, HANG_LAMP, reach=6)
    # M5: the winding room (site of grace): the winding drum and its weights, benches, the waystone
    f = FL[4]
    for x in range(-7, 8):
        for dy in range(-2, 3):
            for dz in range(-2, 3):
                if math.hypot(dy, dz) <= 2.2:
                    C.set(x, f + 6 + dy, -53 + dz, (BRASS if x % 4 == 0 else "stripped_dark_oak_wood[axis=x]")
                          if math.hypot(dy, dz) > 1.2 else IRON)
    for x in (-8, 8):
        for y in range(f + 1, f + 8):
            C.set(x, y, -53, IRON)
    for x in (-5, 5):
        for y in range(f + 1, f + 3):
            C.set(x, y, -50, CHAIN)
        C.set(x, f + 1, -50, IRON)
    C.set(4, f, -36, BTILE)
    C.set(4, f + 1, -36, MOD["waystone"])
    for x in (-6, -5, -4):
        C.set(x, f + 1, -34, stair(DO_ST, "north"))
    for (x, z) in ((-6, -38), (6, -38), (-6, -48), (6, -48)):
        hang(C, x, f + 7, z, HANG_LAMP, reach=6)


IRON_SLAB_TOP = W + "dark_iron_plating_slab[type=top,waterlogged=false]"


def dial(C, face):
    """A clock face in the stage wall: cream glass, a brass rim with twelve hour marks, dark iron hands. The south
    one is cracked open (a jagged split you can look out of)."""
    yc = FC + 9
    r = 9.0
    for u in range(-10, 11):
        for v in range(-10, 11):
            d = math.hypot(u, v)
            if d > r + 0.4:
                continue
            if face == "south":
                x, z = u, -26
            elif face == "north":
                x, z = -u, -62
            elif face == "east":
                x, z = SH, TZ + u
            else:
                x, z = -SH, TZ - u
            y = yc + v
            a = math.degrees(math.atan2(v, u)) % 360
            spec = "white_concrete" if not (3.2 < d < 5.4) else "white_stained_glass"
            if d > r - 0.7:
                spec = GILD
            elif d > r - 1.8 and abs(a - round(a / 30.0) * 30) < 7:
                spec = BRASS
            elif d < 1.2:
                spec = ENGR
            C.set(x, y, z, spec)
    # hands: hour hand toward 10, minute hand toward 2 (in u, v)
    for (ang, ln) in ((150, 5), (40, 7.5)):
        for t in range(2, int(ln * 2) + 1):
            tt = t / 2.0
            u = int(round(math.cos(math.radians(ang)) * tt))
            v = int(round(math.sin(math.radians(ang)) * tt))
            if face == "south":
                x, z = u, -26
            elif face == "north":
                x, z = -u, -62
            elif face == "east":
                x, z = SH, TZ + u
            else:
                x, z = -SH, TZ - u
            C.set(x, yc + v, z, IRON)
    if face == "south":
        pts = [(-7, 6), (-4, 3), (-5, 1), (-1, -1), (-2, -3), (2, -4), (1, -6)]
        for i in range(len(pts) - 1):
            (ua, va), (ub, vb) = pts[i], pts[i + 1]
            steps = max(abs(ub - ua), abs(vb - va))
            for t in range(steps + 1):
                u = int(round(ua + (ub - ua) * t / steps))
                v = int(round(va + (vb - va) * t / steps))
                if yc + v >= FC + 4:
                    C.set(u, yc + v, -26, AIR)
                    if hash01(u, v, 801) < 0.5:
                        C.set(u + 1, yc + v, -26, "black_stained_glass") if math.hypot(u + 1, v) < r - 1 else None


def clock_stage(C):
    """The clock stage: corbelled out to 37 x 37, the arena inside (35 x 35, 18 high) under a coffered ceiling, the
    four dials, gear wheels behind them, a floor laid out as a clock face; the parapet, the pinnacles, the lantern,
    the spire and its brass finial."""
    zs0, zs1 = TZ - SH, TZ + SH
    # corbel table under the overhang
    for x in range(-SH, SH + 1):
        for z in range(zs0, zs1 + 1):
            e = max(abs(x) - 14, (z - (-30)) if z > -30 else ((-58) - z) if z < -58 else 0, 0)
            if abs(x) <= 14 and -58 <= z <= -30:
                continue
            for k in range(1, 4):
                if e <= 4 - k:
                    spec = TB
                    if e == 4 - k:
                        spec = stair(TB_ST, face_of(-x if abs(x) > 14 else 0, (TZ - z) if abs(x) <= 14 else 0), "top")
                    C.set(x, FC - 1 - k, z, spec)
    # stage walls, floor, ceiling
    for x in range(-SH, SH + 1):
        for z in range(zs0, zs1 + 1):
            wall = abs(x) == SH or z in (zs0, zs1)
            corner = abs(x) == SH and z in (zs0, zs1)
            C.set(x, FC - 1, z, DIB)
            if not wall:
                r = math.hypot(x, z - TZ)
                if SHAFT[0] <= x <= SHAFT[1] and SHAFT[2] <= z <= SHAFT[3]:
                    spec = "glass"
                    C.set(x, FC - 1, z, "glass")
                elif abs(r - 15) < 0.6 or abs(r - 7.5) < 0.55:
                    spec = BTILE
                elif r > 13 and r < 15 and int(round(math.degrees(math.atan2(z - TZ, x)) / 30.0)) * 30 == round(
                        math.degrees(math.atan2(z - TZ, x))) // 1 // 1 and False:
                    spec = GILD
                else:
                    spec = PDS if (x + z) % 2 else DST
                C.set(x, FC, z, spec)
            else:
                C.set(x, FC, z, PT)
            for y in range(FC + 1, FB - 1):
                if wall:
                    u = x if z in (zs0, zs1) else z - TZ
                    pil = corner or abs(u) in (13, 14)
                    spec = PDS if pil else (PT if y in (FC + 1, FB - 2) else wmat(x, y, z, FC - 6))
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
            C.set(x, FB - 1, z, DIB if not wall else PT)
            C.set(x, FB, z, PDS if not wall else PT)
    # hour marks on the floor: twelve gilded bars round the 15-ring
    for hr in range(12):
        a = math.radians(hr * 30)
        for rr in (12, 13):
            x, z = int(round(math.cos(a) * rr)), TZ + int(round(math.sin(a) * rr))
            C.set(x, FC, z, GILD)
    C.bp.boss_seal(0, FC, TZ, BOSS, 17)
    # coffered ceiling beams
    for x in range(-SH + 1, SH):
        for z in range(zs0 + 1, zs1):
            if x % 7 == 0 or (z - TZ) % 7 == 0:
                C.set(x, FB - 2, z, "stripped_dark_oak_wood[axis=y]")
    for face in ("south", "north", "east", "west"):
        dial(C, face)
    # gear wheels behind the dials (inside, two blocks from the wall)
    for (plane, cx, cz) in (("x", 0, zs1 - 2), ("x", 0, zs0 + 2), ("z", SH - 2, TZ), ("z", -SH + 2, TZ)):
        gear_disk(C, cx, FC + 9, cz, 3.2, plane)
        if plane == "x":
            C.set(cx, FC + 9, cz + (1 if cz > TZ else -1), IRON)
        else:
            C.set(cx + (1 if cx > 0 else -1), FC + 9, cz, IRON)
    # lamps
    for (x, z) in ((-10, TZ - 10), (10, TZ - 10), (-10, TZ + 10), (10, TZ + 10)):
        hang(C, x, FC + 12, z, CHANDELIER, reach=8)
    for (x, z) in ((-17, TZ - 7), (-17, TZ + 7), (17, TZ - 7), (17, TZ + 7)):
        C.set(x, FC + 5, z, EDISON)
    for (x, z) in ((-7, -61), (7, -61), (-7, -27), (7, -27)):
        C.set(x, FC + 5, z, EDISON)
    # the parapet with pinnacles at the corners and the middles
    for x in range(-SH, SH + 1):
        for z in range(zs0, zs1 + 1):
            if abs(x) == SH or z in (zs0, zs1):
                C.set(x, FB + 1, z, TB_WALL if (x + z) % 2 else TB)
    for (px, pz) in ((-SH, zs0), (SH, zs0), (-SH, zs1), (SH, zs1)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(FB - 4, FB + 7):
                    C.set(px + dx, y, pz + dz, PDS if (dx or dz) else TB)
        for y in range(FB + 7, FB + 11):
            C.set(px, y, pz, ROOF)
        C.set(px, FB + 11, pz, BRASS)
        C.set(px, FB + 12, pz, ROD_U)
    # the lantern (solid core with blind arches) and the spire
    L = 6
    for x in range(-L, L + 1):
        for z in range(TZ - L, TZ + L + 1):
            for y in range(FB + 1, FB + 12):
                edge = abs(x) == L or abs(z - TZ) == L
                arch = edge and (abs(x) <= 2 or abs(z - TZ) <= 2) and FB + 3 <= y <= FB + 9 and not (
                    abs(x) == L and abs(z - TZ) == L)
                if arch:
                    spec = "black_concrete" if not (abs(x) <= 1 or abs(z - TZ) <= 1) or y > FB + 8 else BARS
                    if spec == BARS:
                        spec = "black_concrete"
                else:
                    spec = PDS if (abs(x) == L and abs(z - TZ) == L) else (PT if y in (FB + 1, FB + 11) else TB)
                C.set(x, y, z, spec)
    H = 40
    for k in range(H):
        rr = (L + 1.5) * (1 - k / H)
        y = FB + 12 + k
        for x in range(-L - 2, L + 3):
            for z in range(TZ - L - 2, TZ + L + 3):
                # octagon
                d = max(abs(x), abs(z - TZ), (abs(x) + abs(z - TZ)) / 1.414)
                if d <= rr + 0.3:
                    rib = abs(abs(x) - abs(z - TZ)) <= 0 and d > rr - 1.2
                    C.set(x, y, z, BTILE if rib else ROOF)
    C.set(0, FB + 12 + H, TZ, BRASS)
    C.set(0, FB + 13 + H, TZ, GILD)
    C.set(0, FB + 14 + H, TZ, ROD_U)


def north_turret(C):
    """The director's oriel on the tower's north face: a solid turret carrying a private drop shaft, an office
    corbelled out at the clock stage's level behind sealed bars, the pool at the shaft's foot and the passage to the
    winding hall."""
    x0, x1, z0, z1 = 9, 15, -68, -59
    shx, shz = (11, 12), (-66, -65)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(P + 1, FC - 1):
                if x in shx and z in shz:
                    C.clear(x, y, z)
                    continue
                edge = x in (x0, x1) or z in (z0, z1)
                C.set(x, y, z, (PT if (y - P) % 11 == 0 else wmat(x, y, z)) if edge else "stone")
    for y in range(P + 2, FC - 2):
        C.set(x0 - 1, y, z0 + 2, W + "copper_pipe[axis=y]")
        C.set(x1 + 1, y, z0 + 2, W + "copper_pipe[axis=y]")
        if y % 9 == 0:
            C.set(x0 - 1, y, z0 + 2, GAUGE)
    # the pool and the passage south into the winding hall
    for x in shx:
        for z in shz:
            for y in (P - 2, P - 1, P):
                C.water(x, y, z)
            C.set(x, P - 3, z, "stone")
        for z in range(-64, -56):
            for y in range(P + 1, P + 4):
                C.clear(x, y, z)
            C.set(x, P, z, PDS)
    hang(C, 11, P + 3, -60, LANT_H)
    # the office: x 10..18, z -71..-62 at the clock stage's floor
    ox0, ox1, oz0, oz1 = 10, 18, -71, -62
    for x in range(ox0, ox1 + 1):
        for z in range(oz0, oz1):
            edge = x in (ox0, ox1) or z == oz0
            C.set(x, FC - 1, z, DIB)
            C.set(x, FC, z, W + "mahogany_parquet" if not edge else PT)
            for y in range(FC + 1, FC + 8):
                if edge:
                    C.set(x, y, z, PT if y == FC + 7 else wmat(x, y, z, FC))
                else:
                    C.clear(x, y, z)
            C.set(x, FC + 8, z, PT)
    steep_roof(C, ox0, oz0, ox1, oz1 - 1, FC + 9, rise=2)
    # corbels under the office
    for x in range(ox0, ox1 + 1):
        for z in range(oz0, oz1):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            for k in range(1, 4):
                C.set(x, FC - 1 - k, z, TB if k < 3 else stair(TB_ST, "west", "top"))
    for x in shx:
        for z in shz:
            C.clear(x, FC, z)
            C.clear(x, FC - 1, z)
    for (x, z) in ((10, -67), (10, -66), (10, -65), (10, -64), (13, -67), (13, -66), (13, -65), (13, -64),
                   (11, -67), (12, -67), (11, -64)):
        if x in (ox0,):
            continue
        railing(C, x, FC + 1, z, face_of(11.5 - x, -65.5 - z))
    # sealed bars in the stage's north wall
    for x in (13, 14, 15):
        for y in range(FC + 1, FC + 4):
            C.set(x, y, -62, MOD["vault_bars"])
    # windows out to the north (vistas over the forest)
    for x in (13, 15):
        for y in (FC + 3, FC + 4, FC + 5):
            C.set(x, y, oz0, PANE)
    for z in (-68, -66):
        for y in (FC + 3, FC + 4, FC + 5):
            C.set(ox1, y, z, PANE)
    # the director's furniture
    for x in (15, 16):
        C.set(x, FC + 1, -68, TABLE)
    C.set(16, FC + 1, -67, W + "mahogany_chair[facing=north]")
    C.set(15, FC + 2, -68, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(16, FC + 2, -68, GAUGE)
    for z in range(-70, -63, 2):
        C.set(17, FC + 1, z, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        C.set(17, FC + 2, z, "bookshelf")
    chest(C, 14, FC + 1, -70, "south", "asy_office")
    chest(C, 17, FC + 1, -63, "west", "asy_office")
    C.set(11, FC + 1, -70, "iron_block")
    C.set(11, FC + 2, -70, ENGR)
    C.set(12, FC + 1, -70, W + "mahogany_panelling")
    C.set(12, FC + 2, -70, "copper_bulb[lit=true,powered=false]")
    hang(C, 15, FC + 6, -66, CHANDELIER, reach=4)


# ------------------------------------------------------------------ the chapel and the greenhouse
def chapel(C):
    """The chapel: a tall nave of tuff with stained lancets, pews, the altar of the clockwork saint under a gear
    halo, a bell tower with a slate needle; its south door opens from inside onto the stair to the cemetery."""
    x0, x1, z0, z1 = -72, -46, -7, 7
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, P, z, PDS if edge else (DST if (x + z) % 2 else PDS))
            for y in range(P + 1, P + 17):
                if edge:
                    C.set(x, y, z, wmat(x, y, z) if y not in (P + 16,) else PT)
                else:
                    C.clear(x, y, z)
    gable(C, x0, x1, 0, 7, P + 17, "x", over=1, end_mat=lambda x, y, z: wmat(x, y, z), wall_top=P + 16)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            ry = P + 17 + (8 - abs(z)) - 2
            for y in range(P + 17, ry + 1):
                C.clear(x, y, z)
    # buttresses
    for bx in (-66, -60, -54):
        for z, o in ((z0, -1), (z1, 1)):
            if bx == -60 and o > 0:
                continue
            for y in range(P + 1, P + 15):
                dep = 2 if y < P + 9 else 1
                for k in range(1, dep + 1):
                    C.set(bx, y, z + o * k, DSB if y < P + 3 else TB)
            C.set(bx, P + 15, z + o, stair(TB_ST, OPP[face_of(0, o)]))
    # lancets with stained glass
    for i, lx in enumerate((-70, -64, -57, -51)):
        for z in (z0, z1):
            col = ("purple", "red", "black", "blue")[i]
            lancet(C, "x", z, lx, 2, P + 4, 8, f"{col}_stained_glass_pane")
    # east portal and rose
    for z in range(-1, 2):
        for y in range(P + 1, P + 5):
            C.clear(x1, y, z)
        C.set(x1, P + 5, z, CTB)
        C.set(x1 + 1, P, z, PDS)
    for z in (-2, 2):
        for y in range(P + 1, P + 7):
            C.set(x1 + 1, y, z, PDS)
    for z in range(-4, 5):
        for y in range(P + 8, P + 17):
            d = math.hypot(z, y - (P + 12))
            if d <= 3.6:
                C.set(x1, y, z, ENGR if d < 1 else ("purple_stained_glass_pane" if d < 2.6 else PT))
    # the one-way south door to the cemetery stair
    iron_door(C, -60, P + 1, z1, "south", (-59, P + 2, z1 - 1), "north")
    for z in (z1 + 1, z1 + 2):
        C.clear(-60, P + 1, z)
        C.clear(-60, P + 2, z)
    # pews either side of the aisle, the altar on a dais at the west end
    for x in range(-66, -51, 2):
        for z in list(range(-5, -1)) + list(range(2, 6)):
            C.set(x, P + 1, z, stair(DO_ST, "east"))
    for x in range(-71, -67):
        for z in range(-5, 6):
            C.set(x, P + 1, z, PT if x < -68 else PT_SL + "[type=bottom,waterlogged=false]")
    for z in range(-2, 3):
        C.set(-69, P + 2, z, GILD if abs(z) == 2 else PDS)
    for z in (-2, 2):
        candle(C, -69, P + 3, z, 4)
    # the clockwork saint: a brass figure under a gear halo
    C.set(-71, P + 2, 0, IRON)
    C.set(-71, P + 3, 0, BRASS)
    C.set(-71, P + 4, 0, BRASS)
    C.set(-71, P + 5, 0, VERD)
    gear_disk(C, -72, P + 6, 0, 2.3, "z", rim=GILD)
    C.set(-71, P + 4, -1, "lightning_rod[facing=north,powered=false,waterlogged=false]")
    C.set(-71, P + 4, 1, "lightning_rod[facing=south,powered=false,waterlogged=false]")
    chest(C, -70, P + 2, 4, "east", "asy_chapel")
    # a confessional on the north wall
    for x in (-58, -55):
        for y in range(P + 1, P + 5):
            C.set(x, y, -6, DOP)
            C.set(x, y, -5, DOP)
    for x in (-57, -56):
        C.set(x, P + 5, -6, DOP)
        C.set(x, P + 5, -5, DOP)
        C.set(x, P + 1, -6, stair(DO_ST, "south"))
    spawner(C, -63, P + 1, 0, MOB_WISP)
    spawner(C, -49, P + 1, -5, MOB_GARGOYLE)
    for x in (-66, -56):
        hang(C, x, P + 12, 0, CHANDELIER, reach=12)
    # the bell tower beside the portal, solid, with a needle spire
    bx0, bx1, bz0, bz1 = -45, -39, 2, 8
    for x in range(bx0, bx1 + 1):
        for z in range(bz0, bz1 + 1):
            C.set(x, P, z, PDS)
            edge = x in (bx0, bx1) or z in (bz0, bz1)
            for y in range(P + 1, P + 29):
                C.set(x, y, z, (PDS if x in (bx0, bx1) and z in (bz0, bz1) else wmat(x, y, z)) if edge else "stone")
    for (plane, fixed, u0) in (("x", bz1, -43), ("z", bx1, 4), ("z", bx0, 4), ("x", bz0, -43)):
        for y in range(P + 20, P + 26):
            for u in (u0, u0 + 1):
                x, z = (u, fixed) if plane == "x" else (fixed, u)
                C.set(x, y, z, "black_concrete" if y < P + 25 else CTB)
    for k in range(14):
        rr = 4.2 * (1 - k / 14)
        for x in range(bx0 - 1, bx1 + 2):
            for z in range(bz0 - 1, bz1 + 2):
                d = max(abs(x + 42), abs(z - 5), (abs(x + 42) + abs(z - 5)) / 1.414)
                if d <= rr + 0.2:
                    C.set(x, P + 29 + k, z, ROOF)
    C.set(-42, P + 43, 5, BRASS)
    C.set(-42, P + 44, 5, ROD_U)


def greenhouse(C):
    """The broken greenhouse: an iron-ribbed glass barrel vault, a third of its panes gone, overgrown beds, a
    choked fountain and the gardener's potting bench."""
    x0, x1 = 44, 70
    R = 8.2

    def vy(z):
        return P + 3 + int(round(math.sqrt(max(0.0, R * R - z * z))))

    for x in range(x0, x1 + 1):
        for z in range(-7, 8):
            end = x in (x0, x1)
            rib = (x - x0) % 4 == 0
            C.set(x, P + 1, z, DSB) if abs(z) == 7 or end else None
            C.set(x, P + 2, z, DSB) if abs(z) == 7 or end else None
            top = vy(z)
            lo = max(vy(z - 1) if abs(z - 1) <= 7 else P + 3, vy(z + 1) if abs(z + 1) <= 7 else P + 3)
            lo = min(lo, top)
            ys = list(range(lo, top + 1)) if abs(z) < 7 else list(range(P + 3, top + 1))
            for y in ys:
                broken = vnoise(x * 1.0, z * 1.0 + y, 3.0, 811) < 0.32 and not rib and not end
                C.set(x, y, z, ("oxidized_copper" if rib else ("glass" if not broken else AIR)))
            if end:
                for y in range(P + 1, top):
                    if abs(z) < 7:
                        C.set(x, y, z, "glass_pane" if not rib else "oxidized_copper") if y > P + 2 else None
            if not end and abs(z) < 7:
                for y in range(P + 1, top if abs(z) < 7 else P + 3):
                    if y < lo or abs(z) < 7:
                        if C.get(x, y, z) not in ("minecraft:glass", "minecraft:oxidized_copper"):
                            C.clear(x, y, z)
    for x in range(x0 + 1, x1):
        for z in range(-6, 7):
            for y in range(P + 1, vy(z)):
                C.clear(x, y, z)
            C.set(x, P, z, "gravel" if abs(z) <= 1 else ("rooted_dirt" if hash01(x, z, 821) < 0.4 else "podzol[snowy=false]"))
    # door in the west end
    for z in range(-1, 2):
        for y in range(P + 1, P + 4):
            C.clear(x0, y, z)
        C.set(x0, P, z, PDS)
        C.set(x0 - 1, P, z, PDS)
    # overgrown beds
    for x in range(x0 + 1, x1):
        for z in list(range(-6, -1)) + list(range(2, 7)):
            h = hash01(x, z, 831)
            if (x, z) in ((57, -4), (57, 4)):
                continue
            if h < 0.18:
                C.set(x, P + 1, z, "fern")
            elif h < 0.28:
                C.set(x, P + 1, z, "large_fern[half=lower]")
                C.set(x, P + 2, z, "large_fern[half=upper]")
            elif h < 0.36:
                C.set(x, P + 1, z, "azalea")
            elif h < 0.44:
                C.set(x, P + 1, z, "dead_bush")
            elif h < 0.52:
                C.set(x, P + 1, z, "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
            elif h < 0.58:
                C.set(x, P + 1, z, "small_dripleaf[facing=north,half=lower,waterlogged=false]")
                C.set(x, P + 2, z, "small_dripleaf[facing=north,half=upper,waterlogged=false]")
            elif h < 0.66:
                C.set(x, P + 1, z, "pale_moss_carpet[bottom=true,east=none,north=none,south=none,west=none]")
    # the fountain
    for x in range(55, 60):
        for z in range(-2, 3):
            if abs(x - 57) == 2 or abs(z) == 2:
                C.set(x, P + 1, z, PT_SL + "[type=bottom,waterlogged=false]")
            else:
                C.water(x, P, z)
                C.set(x, P - 1, z, PT)
                if (x + z) % 2:
                    C.set(x, P + 1, z, "lily_pad")
    for z in range(-1, 2):
        for x in range(x0 + 1, x1):
            if not (55 <= x <= 59):
                C.keep.add((x, P + 1, z))
    # hanging vines from the ribs
    for x in range(x0 + 4, x1, 4):
        for z in (-3, 3):
            yt = vy(z) - 1
            for k in range(3):
                if C.free(x, yt - k, z):
                    C.set(x, yt - k, z, "cave_vines[age=10,berries=%s]" % ("true" if k == 2 else "false") if k < 2
                          else "cave_vines[age=10,berries=true]")
    # potting bench and chest
    for x in range(66, 70):
        C.set(x, P + 1, -6, TABLE if x != 69 else "composter[level=5]")
        C.set(x, P + 2, -6, "potted_fern" if x % 2 else "flower_pot")
    chest(C, 69, P + 1, 6, "west", "asy_greenhouse")
    spawner(C, 63, P + 1, 4, MOB_SPIDER)


# ------------------------------------------------------------------ the builder
def clockwork_asylum(bp):
    C = Ctx(bp)
    hill(C)
    ground(C)
    camp(C)
    yard(C)
    cemetery(C)
    forecourt(C)
    funicular(C)
    gatehouse(C)
    tower(C)
    main_hall(C)
    wing(C, -1)
    wing(C, 1)
    west_rooms(C)
    east_rooms(C)
    chapel(C)
    greenhouse(C)
    seal_voids(C)
    trees(C)


VIEWS = [
    ("main_hall", (0, P + 1, -8), (0, P + 14, -26)),
    ("patient_cells", (-22, WG + 1, -18), (-52, WG + 2, -18)),
    ("operating_theatre", (-40, W2 + 1, -15), (-48, W2 + 4, -20)),
    ("hydrotherapy_baths", (21, P - 5, -18), (44, P - 4, -18)),
    ("records_archive", (21, W2 + 1, -18), (40, W2 + 3, -20)),
    ("chapel", (-50, P + 1, 0), (-70, P + 5, 0)),
    ("great_wheel", (5, FL[3] + 1, -38), (0, FL[3] + 3, -56)),
    ("boss_arena", (0, FC + 1, -30), (0, FC + 8, -52)),
]

register(StructureDef(
    "clockwork_asylum", "overworld", ["dark_forest", "pale_garden"],
    [Piece("asylum", clockwork_asylum, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_BANSHEE, 6, 1, 1), (MOB_SPIDER, 4, 1, 2), (MOB_KNIGHT, 2, 1, 1)],
    title_fr="L'Asile mécanique", title_en="The Clockwork Asylum"))
