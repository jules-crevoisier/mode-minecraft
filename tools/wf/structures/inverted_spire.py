"""Inverted Spire (La Flèche renversée): a gothic tower built downward into a sinkhole, its crown level with the ground
and its point hanging over an underground lake 106 blocks below, where the boss waits on an island. Colossal tier
(tools/BUILDING.md §1, §12 concept 14, §15).

Silhouette (one noun phrase, §15.1): a crowned ring of pinnacles round a black hole in a meadow, four giant chains
reaching from the rim to a copper lantern spire in its middle, and below it a tower that tapers down into the dark.

Layout, ground y = 0, x east, z south, the shaft centred on 0, 0 (compass bearings from north, clockwise):
  * the rim: a paved walk round the hole (r 25.5-32.5) on a masonry collar that corbels out over the void, with a
    balustrade and eighteen pinnacles of four heights: the twin gate pinnacles in the south (22), four chain posts on
    the diagonals (20) whose arms hold the giant chains down to the crown, and lower ones between. The approach road
    comes up from a pilgrims' camp 75 blocks south, past a ruined wayside arch that frames the lantern spire, to the
    gate; the hole is hidden by the lie of the land until the gate (denial, reveal);
  * the crown court (feet 1): the tower's top, a round terrace 29 across over the void, reached by the south bridge
    (main) and the north bridge (from the shortcut kiosk). The lantern cupola over the open core rises 38 blocks (the
    dominant); the waystone stands by the bridge. A chain hung with glowing beads drops from the cupola down the
    core through every level, the lantern shaft seen from the court;
  * the descent: a helical ramp three wide winds clockwise round the outside of the tower, six turns, 14 blocks a turn
    (gentle slab steps, a railing hung with lanterns and inverted pinnacles under it). At each level it lands at the
    south face (a pier blocks it): the way on goes in through the east door, round the ring room past the core and
    out through the west door (each level is crossed, not skipped). Each level has a door north onto a bridge across
    the void to the shaft wall;
  * the levels get stranger going down: L1 (feet -13) the chapter library; L2 (-27) the refectory, bridge to the
    quarry gallery and its rock stair up to the rim (iron door, lever below: shortcut 1); L3 (-41) the inverted
    chapel (pews on the ceiling, an altar hanging upside down), bridge to the ossuary gallery: the hub site of grace,
    where the shore lift arrives; L4 (-55) the root crypt, its bridge broken; L5 (-69) the unmaking: amethyst in the
    walls, the outer wall coming apart into masonry floating in the void, a crystal bridge to the reliquary (secret
    best loot before the boss); L6 (-83) the tip sanctum where the bead chain ends;
  * the depths: from L6 a bridge and a long narrow corridor (compression) lead to a rock stair down to the north
    shore of the lake cavern (site of grace before the boss), a causeway, the mist and the arena: an island 35 across
    under the hanging point of the spire (release: the shaft opens to the sky 110 blocks up). Across the island the
    south causeway leads to the vault behind sealed bars;
  * the fast ways back up (§10.4): two bubble-column lifts in glass tubes set in slots of the shaft wall, glowing
    lines seen from the rim: the north lift from the shore to the ossuary gallery (shortcut 2, back to the hub
    grace), the south lift from the south shore to the rim beside the gate (after the boss, back to the entrance).
    The quarry stair (shortcut 1) and the north bridge make the surface loop; anyone can leap from a bridge into the
    lake (the fast way down).
Loot gradient (§15.6): camp, chapter, refectory, quarry and hermit tier 1; chapel, ossuary, crypt tier 2; unmaking,
sanctum tier 2-3; the reliquary and the vault tier 3.
Depth budget: the lake bed is 113 below the ground layer, so the site must stand above y ~50 (the land fit keeps the
wonder on dry ground; Overworld land is at 62+ almost everywhere); the spire tip stands 38 above the ground.
"""
import functools
import math

from ..arch import slab, stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..megakit import fbm, hash01, hash3
from ..parts import LOOT, MOD
from .chained_bastion import giant_chain

# placeholder until the spire gets its own boss: the Sculk Spawn rises from the lake
BOSS = "brasshaven:sculk_spawn"
MOB_KNIGHT = "brasshaven:skeleton_knight"
MOB_SKELETON = "minecraft:skeleton"
MOB_BANSHEE = "brasshaven:banshee"
MOB_CRAWLER = "brasshaven:crypt_crawler"
MOB_WISP = "brasshaven:lantern_wisp"
MOB_LADY = "brasshaven:weeping_lady"
MOB_GARGOYLE = "brasshaven:gargoyle"

# ------------------------------------------------------------------ dimensions
LV = [1, -13, -27, -41, -55, -69, -83]   # feet of the crown court and of levels 1..6
ROOM_H = 10                              # ring room air: feet .. feet + 9
B0 = 180                                 # bearing of the landings (doors, piers)
R_SHAFT = 25.0
CAV_TOP = -86                            # the lake cavern flares out below this
LAKE_TOP = -106                          # top water block (flush with the shores: swim out anywhere)
FA = -105                                # feet on the island, the shores and the causeways
LAKE_BED = -112
AR = 17.5                                # arena floor radius
TUBE_R = 30.5
LIFT_N = (10, -29)                       # bearing ~20
LIFT_S = (-10, 29)                       # bearing ~200
LIFT_N_TOP = -42                         # top water block (ossuary gallery floor)
LIFT_S_TOP = 0
RIM0, RIM1 = 25.5, 32.5
SPIRE_TOP = 38
DOOR_D = 18                              # helix doors at B0 -/+ DOOR_D

LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
FROG = "pearlescent_froglight[axis=y]"
AIR = "air"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ geometry
def bearing(x, z):
    return math.degrees(math.atan2(x, -z)) % 360


def polar(b, r):
    t = math.radians(b)
    return r * math.sin(t), -r * math.cos(t)


def pt(b, r):
    x, z = polar(b, r)
    return int(round(x)), int(round(z))


def angdiff(a, b):
    return (a - b + 180) % 360 - 180


def facing_of(dx, dz):
    if abs(dz) >= abs(dx):
        return "north" if dz < 0 else "south"
    return "west" if dx < 0 else "east"


def out_dir(x, z):
    """Horizontal direction pointing away from the shaft axis."""
    return facing_of(x, z)


def in_dir(x, z):
    return facing_of(-x, -z)


def Rt(y):
    """Outer radius of the tower at height y (crown 14 -> 5.9 at the foot of the body, then the tip cone)."""
    if y >= 0:
        return 14.0
    if y >= -85:
        return 14.0 + 8.0 * y / 84.0
    t = max(0.0, (y + 92.6) / 7.0)
    return 5.9 * t ** 1.25


def shaft_r(b, y):
    if y >= -6:
        return R_SHAFT
    n = fbm(b * 0.33, y * 0.45, 5.0, 17) - 0.5
    amp = min(1.0, (-6 - y) / 10.0) * 4.0
    return R_SHAFT + n * amp


def void_r(b, y):
    """Radius of the open void at height y: the shaft, then the bell of the lake cavern."""
    return _void_r(round(b * 2) / 2, y)


@functools.lru_cache(maxsize=None)
def _void_r(b, y):
    r = shaft_r(b, y)
    if y < CAV_TOP:
        t = min(1.0, (CAV_TOP - y) / 14.0)
        r += 13.0 * math.sin(t * math.pi / 2) + (fbm(b * 0.5, y * 0.6, 4.0, 23) - 0.5) * 3.0 * t
    if y <= LAKE_TOP:
        r -= (LAKE_TOP - y) * 0.6
    return r


def H(psi):
    """Feet height (in half blocks) of the helix at helix angle psi (degrees from the first landing bearing)."""
    n = int(psi // 360)
    d = psi - 360 * n
    if n >= 6:
        return float(LV[6])
    if d <= 25:
        return float(LV[n])
    if d >= 335:
        return float(LV[n + 1])
    v = LV[n] + (LV[n + 1] - LV[n]) * (d - 25) / 310.0
    return round(v * 2) / 2.0


def band(y):
    j = y
    if j > -22:
        return 0
    if j > -46:
        return 1
    if j > -66:
        return 2
    return 3


def pick(choices, x, y, z, seed):
    tot = sum(w for _, w in choices)
    h = hash3(x, y, z, seed) * tot
    for s, w in choices:
        h -= w
        if h <= 0:
            return s
    return choices[-1][0]


MASONRY = [
    [("stone_bricks", 6), ("polished_andesite", 1.5), ("cracked_stone_bricks", 1.2), ("andesite", 0.6)],
    [("stone_bricks", 4), ("tuff_bricks", 4), ("polished_tuff", 1), ("cracked_stone_bricks", 1)],
    [("tuff_bricks", 3), ("deepslate_bricks", 5), ("cracked_deepslate_bricks", 1.5), ("polished_tuff", 0.6)],
    [("deepslate_tiles", 4.5), ("polished_blackstone_bricks", 3), ("cracked_deepslate_tiles", 1.5),
     ("crying_obsidian", 0.35), ("amethyst_block", 0.3)],
]
TRIM = ["polished_andesite", "polished_tuff", "polished_deepslate", "polished_blackstone"]
CHISEL = ["chiseled_stone_bricks", "chiseled_tuff_bricks", "chiseled_deepslate", "chiseled_polished_blackstone"]
SLAB = ["polished_andesite_slab", "tuff_brick_slab", "deepslate_brick_slab", "deepslate_tile_slab"]
DECK = ["polished_andesite", "tuff_bricks", "deepslate_bricks", "deepslate_tiles"]
WALLB = ["stone_brick_wall", "tuff_brick_wall", "deepslate_brick_wall", "polished_blackstone_brick_wall"]
STAIRB = ["stone_brick_stairs", "tuff_brick_stairs", "deepslate_brick_stairs", "polished_blackstone_brick_stairs"]


def masonry(x, y, z):
    j = (hash3(x // 3, y // 2, z // 3, 5) - 0.5) * 5
    return pick(MASONRY[band(int(y + j))], x, y, z, 11)


def rock(x, y, z):
    j = (fbm(x * 0.7 + z * 0.3, y * 1.4, 6.0, 41) - 0.5) * 6
    yy = y + j
    if yy > -30:
        seq = ("stone", "andesite", "stone", "tuff", "stone", "diorite")
    elif yy > -62:
        seq = ("stone", "tuff", "andesite", "deepslate", "stone", "tuff")
    else:
        seq = ("deepslate", "cobbled_deepslate", "tuff", "deepslate", "calcite", "deepslate")
    s = seq[int(yy // 4) % len(seq)]
    h = hash3(x, y, z, 7)
    if h < 0.07:
        return "cobblestone" if yy > -50 else "cobbled_deepslate"
    if h < 0.1 and yy > -60:
        return "mossy_cobblestone"
    return s


# ------------------------------------------------------------------ site state
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.void = set()       # open cells of the shaft, the cavern and the lift slots
        self.skin = set()       # rock lining cells (may be replaced by masonry rooms)
        self.walk = set()       # cells kept clear for walking (helix, bridges)

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def soft(self, x, y, z):
        """True when the cell is free to carve or line (unset terrain or rock lining)."""
        b = self.bp.get(x, y, z)
        return b is None or ((x, y, z) in self.skin and b != "minecraft:air")


# ------------------------------------------------------------------ the hole
def slots():
    """(x, z, y0, y1) cells of the two slots cut in the shaft wall for the lift tubes."""
    out = []
    for (tx, tz), y0, y1 in ((LIFT_N, FA - 1, LIFT_N_TOP + 2), (LIFT_S, FA - 1, LIFT_S_TOP)):
        r0 = math.hypot(tx, tz)
        ux, uz = tx / r0, tz / r0
        for x in range(tx - 9, tx + 10):
            for z in range(tz - 9, tz + 10):
                along = x * ux + z * uz
                across = abs(-x * uz + z * ux)
                if across <= 1.6 and 20 <= along <= r0 - 1.2:
                    out.append((x, z, y0, y1))
    return out


def hole(S):
    """Air of the shaft and the cavern, the lake, then a two-block rock lining round every open cell."""
    bp = S.bp
    void = S.void
    for y in range(0, LAKE_BED - 1, -1):
        for x in range(-46, 47):
            for z in range(-46, 47):
                r = math.hypot(x, z)
                if r > 46:
                    continue
                b = bearing(x, z)
                R = void_r(b, y)
                if r < R:
                    if y == LAKE_BED:
                        bp.set(x, y, z, "mud" if hash3(x, y, z, 3) < 0.4 else ("clay" if hash3(x, y, z, 4) < 0.5
                                                                                else "gravel"))
                        S.skin.add((x, y, z))
                        continue
                    void.add((x, y, z))
                    bp.set(x, y, z, "water" if y <= LAKE_TOP else AIR)
    for x, z, y0, y1 in slots():
        for y in range(y0, y1 + 1):
            if (x, y, z) not in void:
                void.add((x, y, z))
                bp.set(x, y, z, AIR)
    # lining: two layers of rock round the void (below the masonry collar)
    front = list(void)
    for layer in range(2):
        nxt = []
        for (x, y, z) in front:
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
                q = (x + dx, y + dy, z + dz)
                if q[1] > -7 or q in void or q in S.skin:
                    continue
                if bp.get(*q) is None:
                    bp.set(*q, rock(*q))
                    S.skin.add(q)
                    nxt.append(q)
        front = nxt
    # the bed under the lake
    for x in range(-40, 41):
        for z in range(-40, 41):
            if bp.get(x, LAKE_BED, z) is not None and bp.get(x, LAKE_BED - 1, z) is None:
                bp.set(x, LAKE_BED - 1, z, "deepslate")


def collar(S):
    """The masonry rim of the hole: a 7-deep collar, a corbelled lip over the void and the balustrade."""
    bp = S.bp
    for x in range(-29, 30):
        for z in range(-29, 30):
            r = math.hypot(x, z)
            if r < 23.9 or r > 28.6:
                continue
            for y in range(-7, 1):
                if r >= R_SHAFT:
                    if r < 27.6 or y == 0:
                        bp.set(x, y, z, "stone_bricks" if hash3(x, y, z, 31) < 0.7 else
                               ("andesite" if y < -3 else "cracked_stone_bricks"))
                        S.skin.discard((x, y, z))
                elif y >= -1:
                    # the lip: corbel course (upside-down stairs) under a coping
                    if y == -1 and r >= 24.4:
                        bp.set(x, y, z, stair("stone_brick_stairs", in_dir(x, z), "top"))
                    elif y == 0:
                        bp.set(x, y, z, "polished_andesite")
            if 24.0 <= r < 25.2:
                bp.set(x, 1, z, "stone_brick_wall")
    # bands of chiseled brick and string course on the collar face
    for x in range(-27, 28):
        for z in range(-27, 28):
            r = math.hypot(x, z)
            if R_SHAFT <= r < 26.2:
                bp.set(x, -4, z, "chiseled_stone_bricks" if int(bearing(x, z)) % 15 < 3 else "polished_andesite")


# ------------------------------------------------------------------ the tower
def tower(S):
    bp = S.bp
    for y in range(0, -93, -1):
        rt = Rt(y)
        if rt <= 0.05:
            continue
        ri = int(math.ceil(rt)) + 1
        lvl = None
        for n in range(1, 7):
            if LV[n] <= y < LV[n] + ROOM_H:
                lvl = n
        for x in range(-ri, ri + 1):
            for z in range(-ri, ri + 1):
                r = math.hypot(x, z)
                if r > rt + 0.3:
                    continue
                if y >= -1:
                    # the crown court: two-block floor, the open core in the middle
                    if r <= 2.2:
                        bp.set(x, y, z, AIR)
                    elif y == 0:
                        bp.set(x, y, z, court_floor(x, z, r))
                    else:
                        bp.set(x, y, z, masonry(x, y, z))
                    continue
                if y < -85:
                    # the tip cone: ribs of gilded blackstone between dark tiles
                    b = bearing(x, z)
                    rib = (b % 45) < 360 / (2 * math.pi * max(r, 1)) * 1.1
                    bp.set(x, y, z, "gilded_blackstone" if rib and r > rt - 1.2 else
                           ("polished_blackstone_bricks" if hash3(x, y, z, 9) < 0.6 else "deepslate_tiles"))
                    continue
                core = y >= LV[6] + ROOM_H
                if lvl is not None and lvl < 6:
                    if r <= 2.2:
                        bp.set(x, y, z, AIR)
                    elif r <= 3.3:
                        bp.set(x, y, z, "iron_bars")
                    elif r < rt - 1.5:
                        bp.set(x, y, z, AIR)
                    else:
                        bp.set(x, y, z, wall_block(x, y, z, rt, r))
                elif lvl == 6:
                    bp.set(x, y, z, AIR if r < rt - 1.5 else wall_block(x, y, z, rt, r))
                else:
                    if core and r <= 2.2:
                        bp.set(x, y, z, AIR)
                    elif core and r <= 3.3 and is_bead_level(y):
                        bp.set(x, y, z, "sea_lantern")
                    else:
                        bp.set(x, y, z, floor_block(x, y, z, rt, r))


def is_bead_level(y):
    return any(y == LV[n] - 2 for n in range(1, 7))


def court_floor(x, z, r):
    b = bearing(x, z)
    if r > 13.5:
        return "polished_andesite"
    if 6.5 <= r < 7.5 or 11.5 <= r < 12.5:
        return "chiseled_stone_bricks" if int(b) % 30 < 6 else "polished_andesite"
    if r < 6.5 and int(b + 11.25) % 45 < 4:
        return "polished_diorite"
    return "stone_bricks" if hash01(x, z, 12) < 0.75 else "polished_andesite"


def wall_block(x, y, z, rt, r):
    """Outer wall of a ring room: string courses at the floor and at the springing of the vault."""
    for n in range(1, 7):
        if y == LV[n] + 7 and r > rt - 0.8:
            return TRIM[band(y)]
    return masonry(x, y, z)


def floor_block(x, y, z, rt, r):
    """The solid band between two rooms: floor, vault and the cornice ring round the outside."""
    b = band(y)
    for n in range(0, 7):
        if y == LV[n] - 1 and r > rt - 0.8:
            return TRIM[b]
        if y == LV[n] - 3 and r > rt - 0.8 and n > 0:
            return CHISEL[b] if int(bearing(x, z)) % 20 < 4 else TRIM[b]
    return masonry(x, y, z)


def tip(S):
    """Under the sanctum floor: the point of the spire, soul lanterns round its root and one at the very tip."""
    bp = S.bp
    for k in range(8):
        b = 22.5 + 45 * k
        x, z = pt(b, 5.2)
        bp.set(x, -86, z, "polished_blackstone_bricks")
        bp.set(x, -87, z, "polished_blackstone_wall")
        bp.set(x, -88, z, SOUL_H)
    bp.set(0, -93, 0, SOUL_H)


# ------------------------------------------------------------------ the helix
def helix(S):
    """The ramp round the outside of the tower: six turns from the crown court to the sanctum."""
    bp = S.bp
    piers = []
    lamps = []
    pendants = []
    for x in range(-21, 22):
        for z in range(-21, 22):
            r = math.hypot(x, z)
            if r < 6.0 or r > 20.5:
                continue
            b = bearing(x, z)
            delta = (b - B0) % 360
            for t in range(7):
                psi = delta + 360 * t
                if psi < 12 or psi > 2160 - 6:
                    continue
                d = psi % 360
                landing = t >= 1 and (d <= 25 or d >= 335) or psi >= 2135
                hf = H(psi)
                rt = Rt(hf - 1)
                rr = r - rt
                w_deck = 4.8 if landing else 3.8
                if rr < 0.8 or rr >= w_deck + 1.0:
                    continue
                pier = t >= 1 and (d <= 12 or d >= 348) and min(d, 360 - d) * math.pi / 180 * r <= 0.9
                k = int(math.floor(hf))
                half = hf - k > 0.25
                bnd = band(k)
                top = k + 1 if half else k        # first walking cell
                if pier:
                    piers.append((x, z, k, half, bnd, rr))
                    continue
                if rr < w_deck:
                    if half:
                        bp.set(x, k, z, slab(SLAB[bnd]))
                        bp.set(x, k - 1, z, DECK[bnd])
                        bp.set(x, k - 2, z, masonry(x, k - 2, z))
                    else:
                        bp.set(x, k - 1, z, DECK[bnd] if hash3(x, k, z, 2) < 0.8 else TRIM[bnd])
                        bp.set(x, k - 2, z, masonry(x, k - 2, z))
                    for y in range(top, top + 4):
                        bp.set(x, y, z, AIR)
                        S.walk.add((x, y, z))
                else:
                    # railing: solid up to the deck, a wall block on it
                    if half:
                        bp.set(x, k, z, TRIM[bnd])
                        bp.set(x, k - 1, z, TRIM[bnd])
                    else:
                        bp.set(x, k - 1, z, TRIM[bnd])
                    bp.set(x, k - 2, z, masonry(x, k - 2, z))
                    bp.set(x, top, z, WALLB[bnd])
                    for y in range(top + 1, top + 4):
                        bp.set(x, y, z, AIR)
                    a = psi % 30
                    if a < 360 / (2 * math.pi * r) * 0.9:
                        lamps.append((x, top + 1, z, bnd))
                    a2 = (psi + 15) % 30
                    if a2 < 360 / (2 * math.pi * r) * 0.9 and not (140 <= d <= 220) and not landing:
                        pendants.append((x, k - 3, z, bnd))
    for x, z, k, half, bnd, rr in piers:
        y0 = k - 1
        h = 4 if rr < 4.0 else 3
        for y in range(y0 - 1, k + h):
            bp.set(x, y, z, CHISEL[bnd] if y in (k, k + h - 1) else masonry(x, y, z))
        if rr >= 4.0:
            bp.set(x, k + h, z, WALLB[bnd])
        elif 2.3 <= rr < 3.3:
            bp.set(x, k + h, z, WALLB[bnd])
            bp.set(x, k + h + 1, z, SOUL if bnd >= 2 else LANT)
    for (x, y, z, bnd) in lamps:
        if bp.get(x, y, z) in (None, "minecraft:air"):
            bp.set(x, y, z, SOUL if bnd >= 2 else LANT)
    for (x, y, z, bnd) in pendants:
        if any((x, yy, z) in S.walk for yy in range(y - 5, y + 1)):
            continue
        bp.set(x, y, z, TRIM[bnd])
        bp.set(x, y - 1, z, WALLB[bnd])
        bp.set(x, y - 2, z, WALLB[bnd])
        bp.set(x, y - 3, z, SOUL_H if bnd >= 2 else LANT_H)


def doors(S):
    """The two helix doors of every level (east in, west out; the sanctum has only the east one), the north
    bridge door, and the partition that sends the way round the ring."""
    bp = S.bp
    for n in range(1, 7):
        f = LV[n]
        rt = Rt(f)
        ri = int(rt) + 2
        for x in range(-ri, ri + 1):
            for z in range(-ri, ri + 1):
                r = math.hypot(x, z)
                if r > rt + 0.6 or r < 3.4:
                    continue
                b = bearing(x, z)
                for db in ((-DOOR_D, DOOR_D) if n < 6 else (-DOOR_D,)):
                    arc = abs(angdiff(b, B0 + db)) * math.pi / 180 * r
                    if arc <= 1.15 and r >= rt - 2.4:
                        for y in range(f, f + 4):
                            bp.set(x, y, z, AIR)
                        bp.set(x, f - 1, z, TRIM[band(f)])
                arc0 = abs(angdiff(b, 0)) * math.pi / 180 * r
                if arc0 <= 1.15 and r >= rt - 2.4:
                    for y in range(f, f + 4):
                        bp.set(x, y, z, AIR)
                    bp.set(x, f - 1, z, TRIM[band(f)])
                # partition across the ring between the two doors
                arcp = abs(angdiff(b, B0)) * math.pi / 180 * r
                if n < 6 and arcp <= 0.9 and r < rt - 1.4:
                    for y in range(f, f + ROOM_H):
                        bp.set(x, y, z, TRIM[band(f)] if y in (f, f + 7) else masonry(x, y, z))


def windows(S):
    """Tall windows in the ring rooms wherever the outside is open (the helix passes everywhere at some height)."""
    bp = S.bp
    for n in range(1, 6):
        f = LV[n]
        for k in range(12):
            b = 15 + 30 * k
            if abs(angdiff(b, B0)) < 35 or abs(angdiff(b, 0)) < 12:
                continue
            rt = Rt(f + 3)
            cells = []
            for y in range(f + 2, f + 7):
                for rr in (rt - 1.0, rt):
                    x, z = pt(b, rr)
                    cells.append((x, y, z))
            ox, oz = pt(b, rt + 1.3)
            if not all(bp.get(ox, y, oz) in (None, "minecraft:air") and (ox, y, oz) not in S.walk
                       for y in range(f + 1, f + 8)):
                continue
            pane = "iron_bars" if n >= 4 else ("tinted_glass" if n == 5 else "glass_pane")
            for (x, y, z) in cells:
                if math.hypot(x, z) > rt - 0.6:
                    bp.set(x, y, z, pane)
                else:
                    bp.set(x, y, z, AIR)
            x, z = pt(b, rt)
            bp.set(x, f + 1, z, TRIM[band(f)])
            bp.set(x, f + 7, z, CHISEL[band(f)])


# ------------------------------------------------------------------ the crown
def crown(S):
    bp = S.bp
    # parapet round the court, with gaps for the two bridges and the start of the helix
    for x in range(-15, 16):
        for z in range(-15, 16):
            r = math.hypot(x, z)
            if not 13.6 <= r < 14.8:
                continue
            b = bearing(x, z)
            if abs(angdiff(b, 180)) < 9 or abs(angdiff(b, 0)) < 9 or 190 <= b <= 218:
                continue
            bp.set(x, 1, z, "stone_brick_wall")
    # oculus railing
    for x in range(-4, 5):
        for z in range(-4, 5):
            if 2.2 < math.hypot(x, z) <= 3.3:
                bp.set(x, 1, z, "andesite_wall" if (x + z) % 2 else "stone_brick_wall")
    # small pinnacles on the parapet
    for b, h in ((90, 8), (270, 8), (150, 6), (330, 6), (20, 5), (240, 6), (115, 5), (295, 5)):
        x, z = pt(b, 14.2)
        bp.set(x, 1, z, "chiseled_stone_bricks")
        for y in range(2, h):
            bp.set(x, y, z, "stone_bricks" if y < h - 2 else "stone_brick_wall")
        bp.set(x, h, z, LANT)
    # the gate over the start of the descent
    for b in (192, 217):
        x, z = pt(b, 15.6)
        for y in range(1, 8):
            bp.set(x, y, z, "chiseled_stone_bricks" if y in (1, 7) else "stone_bricks")
        bp.set(x, 8, z, "stone_brick_wall")
        bp.set(x, 9, z, LANT)
    # chain anchors on the diagonals
    for b in (45, 135, 225, 315):
        cx, cz = pt(b, 12.3)
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                for y in range(1, 4):
                    bp.set(x, y, z, "gold_block" if y == 3 and x == cx and z == cz else
                           ("polished_blackstone_bricks" if y < 3 else "chiseled_polished_blackstone"))
    # the waystone by the south bridge
    bp.set(4, 1, 11, MOD["waystone"])
    bp.set(5, 1, 10, "candle[candles=3,lit=true,waterlogged=false]")
    cupola(S)


def cupola(S):
    """Four piers round the oculus, a drum with lit windows, a dome and an octagonal copper needle: the dominant."""
    bp = S.bp
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in range(1, 9):
                bp.set(sx * 4, y, sz * 4, "chiseled_stone_bricks" if y in (1, 8) else "polished_andesite")
                bp.set(sx * 4 - sx, y, sz * 4, "stone_bricks" if y > 5 else AIR)
                bp.set(sx * 4, y, sz * 4 - sz, "stone_bricks" if y > 5 else AIR)
    # arches between the piers (open 2-6)
    for y in (6, 7, 8):
        for u in range(-4, 5):
            if y == 6 and abs(u) <= 1:
                continue
            for (x, z) in ((u, -4), (u, 4), (-4, u), (4, u)):
                bp.set(x, y, z, "stone_bricks" if y < 8 else "polished_andesite")
    for y in (6,):
        for u in (-2, 2):
            for (x, z, f) in ((u, -4, "south"), (u, 4, "north"), (-4, u, "east"), (4, u, "west")):
                pass
    # drum
    for x in range(-5, 6):
        for z in range(-5, 6):
            r = math.hypot(x, z)
            if r <= 5.2:
                bp.set(x, 9, z, "polished_andesite" if r > 2.3 else AIR)
            if 3.6 <= r <= 4.9:
                for y in range(10, 14):
                    b = bearing(x, z)
                    win = int(b + 22.5) % 45 < 12 and y in (11, 12)
                    bp.set(x, y, z, "glass" if win else "stone_bricks")
            elif r < 3.6:
                for y in range(10, 14):
                    bp.set(x, y, z, AIR)
    for x in range(-3, 4):
        for z in range(-3, 4):
            r = math.hypot(x, z)
            if 2.6 <= r < 3.6:
                bp.set(x, 10, z, "sea_lantern")
    # dome
    for y, rr in ((14, 4.6), (15, 3.9), (16, 3.0)):
        for x in range(-5, 6):
            for z in range(-5, 6):
                r = math.hypot(x, z)
                if r <= rr:
                    bp.set(x, y, z, "waxed_oxidized_cut_copper" if r > rr - 1.2 else AIR)
    # needle: octagonal, copper with dark ribs
    h0 = 17
    for y in range(h0, SPIRE_TOP + 1):
        t = (y - h0) / (SPIRE_TOP - h0)
        rr = 2.7 * (1 - t) ** 1.1
        for x in range(-3, 4):
            for z in range(-3, 4):
                r = math.hypot(x, z)
                if r <= rr + 0.45:
                    rib = x == 0 or z == 0
                    bp.set(x, y, z, ("waxed_copper_block" if rib and y in (h0 + 5, h0 + 12) else
                                     "waxed_oxidized_copper" if rib else "waxed_oxidized_cut_copper"))
    bp.set(0, SPIRE_TOP + 1, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # four lucarne pinnacles on the shoulders of the drum
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 4, sz * 4
            for y in range(14, 20):
                bp.set(x, y, z, "polished_andesite" if y < 17 else "stone_brick_wall")
            bp.set(x, 20, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the bead chain down the core
    for y in range(16, -77, -1):
        if y in (-77,):
            continue
        bead = (y - 1) % 7 == 0 and y < 0
        bp.set(0, y, 0, FROG if bead else "iron_chain[axis=y,waterlogged=false]")
    for y in (-77, -78):
        bp.set(0, y, 0, FROG)
    for (x, z) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x, -77, z, "pearlescent_froglight[axis=x]" if x else "pearlescent_froglight[axis=z]")
        bp.set(x, -78, z, SOUL_H)


# ------------------------------------------------------------------ rim, chains, gate
PINNACLES = [(171, 22), (189, 22), (352, 14), (8, 14), (45, 20), (135, 20), (225, 20), (315, 20), (90, 16),
             (270, 16), (68, 11), (112, 11), (248, 11), (292, 11), (154, 9), (338, 12), (30, 10), (215, 13)]


def rim(S):
    bp = S.bp
    for x in range(-34, 35):
        for z in range(-34, 35):
            r = math.hypot(x, z)
            if not RIM0 <= r <= RIM1 + 0.4:
                continue
            h = hash01(x, z, 51)
            if r > RIM1 - 0.8:
                spec = "mossy_cobblestone" if h < 0.5 else "cobblestone"
            elif 27.5 <= r < 28.5:
                spec = "polished_andesite"
            else:
                spec = "stone_bricks" if h < 0.6 else ("cracked_stone_bricks" if h < 0.75 else "andesite")
            bp.set(x, 0, z, spec)
            if bp.get(x, -1, z) is None:
                bp.set(x, -1, z, "cobblestone")
    for b, h in PINNACLES:
        pinnacle(S, b, h)
    # the gate: an arch between the twin pinnacles over the mouth of the south bridge
    for x in range(-3, 4):
        top = 7 if abs(x) == 3 else (8 if abs(x) == 2 else 9)
        for y in range(top, 11):
            bp.set(x, y, 25, "stone_bricks" if y < 10 else "polished_andesite")
        bp.set(x, 11, 25, "stone_brick_wall" if x % 2 == 0 else AIR)
    bp.set(0, 9, 25, "chiseled_stone_bricks")
    bp.set(0, 8, 25, LANT_H)
    for x in (-2, 2):
        bp.set(x, 7, 25, stair("stone_brick_stairs", "east" if x < 0 else "west", "top"))


def pinnacle(S, b, h):
    """A rim pinnacle on the balustrade: a 3x3 shaft with chiseled bands, a gabled needle and a lantern; the
    chain posts carry an iron arm reaching over the void."""
    bp = S.bp
    cx, cz = pt(b, 26.0)
    shaft = int(h * 0.58) if h != 20 else 16
    for y in range(-7, shaft + 1):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                edge = abs(x - cx) == 1 and abs(z - cz) == 1
                if y <= 0:
                    bp.set(x, y, z, "stone_bricks")
                elif y == 1 or y == shaft or (y % 5 == 0):
                    bp.set(x, y, z, "chiseled_stone_bricks" if edge else "polished_andesite")
                else:
                    bp.set(x, y, z, "stone_bricks" if hash3(x, y, z, 77) < 0.8 else "cracked_stone_bricks")
    for x, z, f in ((cx - 1, cz, "west"), (cx + 1, cz, "east"), (cx, cz - 1, "north"), (cx, cz + 1, "south")):
        bp.set(x, shaft + 1, z, stair("stone_brick_stairs", OPP[f]))
    top = h if h != 20 else 24
    for y in range(shaft + 1, top):
        bp.set(cx, y, cz, "stone_bricks" if y < shaft + 3 else "stone_brick_wall")
    bp.set(cx, top, cz, LANT)
    if h == 20:
        # chain post: an iron arm toward the axis; the giant chain hangs from its end
        ux, uz = -cx / 26.0, -cz / 26.0
        for k in range(1, 4):
            x, z = int(round(cx + ux * k)), int(round(cz + uz * k))
            bp.set(x, shaft, z, "polished_blackstone_bricks")
            bp.set(x, shaft - 1, z, stair("polished_blackstone_brick_stairs", out_dir(ux, uz), "top") if k < 3
                   else "polished_blackstone_bricks")


def chains(S):
    """Four giant chains from the arms of the chain posts down to the anchors on the crown court."""
    bp = S.bp
    for b in (45, 135, 225, 315):
        x0, z0 = polar(b, 23.0)
        x1, z1 = polar(b, 12.3)
        p0 = (x0, 15.0, z0)
        p1 = (x1, 4.0, z1)
        giant_chain(bp, p0, p1, link=5, mat="polished_blackstone_bricks", mat2="polished_basalt[axis=y]",
                    trim="gilded_blackstone", step=4)
    # iron chains hanging from the corbels with lanterns and cages
    for b, ln in ((60, 18), (105, 30), (150, 12), (240, 24), (285, 15), (330, 34), (15, 9), (165, 22)):
        x, z = pt(b, 22.6)
        if any((x, y, z) in S.walk for y in range(-ln - 2, 1)):
            continue
        for y in range(-1, -ln, -1):
            bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")
        if ln > 20:
            # a gibbet cage
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for y in range(-ln - 3, -ln + 1):
                        if (dx, dz) != (0, 0) and abs(dx) + abs(dz) == 1:
                            bp.set(x + dx, y, z + dz, "iron_bars")
                    bp.set(x + dx, -ln - 4, z + dz, "dark_oak_slab[type=bottom,waterlogged=false]")
                    bp.set(x + dx, -ln + 1, z + dz, "dark_oak_slab[type=top,waterlogged=false]")
            bp.set(x, -ln, z, "iron_chain[axis=y,waterlogged=false]")
            bp.set(x, -ln - 1, z, SOUL_H if b > 200 else LANT_H)
        else:
            bp.set(x, -ln, z, LANT_H)


def bridge(S, f, z0, z1, rails=True, broken=None, deck="polished_andesite", crystal=False):
    """A bridge along x = -1..1 (rails at |x| = 2) from z0 to z1 (z0 > z1, going north) at feet f."""
    bp = S.bp
    bnd = band(f)
    for z in range(z1, z0 + 1):
        if broken and broken[0] < z < broken[1]:
            continue
        for x in range(-2, 3):
            if crystal:
                spec = ("amethyst_block" if hash3(x, f, z, 3) < 0.5 else "tinted_glass") if abs(x) < 2 else \
                    "amethyst_block"
            else:
                spec = (DECK[bnd] if hash3(x, f, z, 4) < 0.7 else TRIM[bnd]) if abs(x) < 2 else TRIM[bnd]
            bp.set(x, f - 1, z, spec)
            bp.set(x, f - 2, z, masonry(x, f - 2, z) if not crystal else "amethyst_block")
            if abs(x) < 2:
                for y in range(f, f + 4):
                    bp.set(x, y, z, AIR)
                    S.walk.add((x, y, z))
            else:
                if rails:
                    bp.set(x, f, z, WALLB[bnd] if not crystal else "amethyst_cluster[facing=up,waterlogged=false]")
                for y in range(f + 1, f + 4):
                    bp.set(x, y, z, AIR)
        if (z - z1) % 4 == 2 and not crystal:
            for x in (-2, 2):
                bp.set(x, f - 3, z, stair(STAIRB[bnd], "east" if x < 0 else "west", "top"))
            if rails:
                bp.set(-2, f + 1, z, SOUL if bnd >= 2 else LANT)
    if broken:
        # rubble edges and a rail across each broken end
        for zz in (broken[0], broken[1]):
            for x in range(-1, 2):
                bp.set(x, f, zz, WALLB[bnd])


def rock_room(S, x0, z0, x1, z1, f, h, wall=None, floor=None, lining=True):
    """Carve air x0..x1, z0..z1, feet f, h high; masonry shell on every soft cell round it."""
    bp = S.bp
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 1, f + h + 1):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and f <= y < f + h
                if inside:
                    bp.set(x, y, z, AIR)
                    S.skin.discard((x, y, z))
                elif S.soft(x, y, z) and lining:
                    if y == f - 1 and x0 <= x <= x1 and z0 <= z <= z1:
                        spec = floor(x, z) if callable(floor) else (floor or masonry(x, y, z))
                    else:
                        spec = wall(x, y, z) if callable(wall) else (wall or masonry(x, y, z))
                    bp.set(x, y, z, spec)
                    S.skin.discard((x, y, z))


def flight(S, lane, z_from, step, f, n, spec, wall=None):
    """n stairs climbing along z (step = -1 north, +1 south) in the x lane (x0, x1), starting next to the landing
    edge z_from at feet f; air above each tread, a shell round it. Returns the feet at the top."""
    bp = S.bp
    face = "north" if step < 0 else "south"
    x0, x1 = lane
    for k in range(1, n + 1):
        z = z_from + step * k
        y = f - 1 + k
        for x in range(x0, x1 + 1):
            bp.set(x, y, z, stair(spec, face))
            S.skin.discard((x, y, z))
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, AIR)
                S.skin.discard((x, yy, z))
            for yy in (y - 1, y - 2):
                if S.soft(x, yy, z):
                    bp.set(x, yy, z, masonry(x, yy, z))
        for x in (x0 - 1, x1 + 1):
            for yy in range(y - 1, y + 6):
                if S.soft(x, yy, z):
                    bp.set(x, yy, z, wall(x, yy, z) if wall else masonry(x, yy, z))
        for yy in (y + 5,):
            for x in range(x0, x1 + 1):
                if S.soft(x, yy, z):
                    bp.set(x, yy, z, masonry(x, yy, z))
    return f + n


# ------------------------------------------------------------------ the levels
def P(b, r):
    return pt(b, r)


def ring_cells(f, r0, r1, b0=0, b1=360):
    rt = Rt(f)
    out = []
    ri = int(rt) + 1
    for x in range(-ri, ri + 1):
        for z in range(-ri, ri + 1):
            r = math.hypot(x, z)
            if r0 <= r < r1:
                b = bearing(x, z)
                if b0 <= b <= b1 or (b0 > b1 and (b >= b0 or b <= b1)):
                    out.append((x, z, r, b))
    return out


def free(S, x, y, z):
    return S.bp.get(x, y, z) in ("minecraft:air",)


def level_lights(S, f, soul=False, count=4, r=None):
    rt = Rt(f)
    rr = r or (3.3 + (rt - 1.5)) / 2
    for k in range(count):
        b = 45 + 360 / count * k
        x, z = P(b, rr)
        if free(S, x, f + ROOM_H - 1, z):
            S.bp.set(x, f + ROOM_H - 1, z, "iron_chain[axis=y,waterlogged=false]")
            S.bp.set(x, f + ROOM_H - 2, z, SOUL_H if soul else LANT_H)


def chapter(S):
    """L1: the chapter library. Shelves along the outer wall, desks and lecterns, chandeliers."""
    bp = S.bp
    f = LV[1]
    rin = Rt(f) - 1.5
    for (x, z, r, b) in ring_cells(f, rin - 1.0, rin):
        if abs(angdiff(b, B0)) < 30 or abs(angdiff(b, 0)) < 14:
            continue
        if int(b) % 30 in (13, 14, 15, 16, 17):
            continue
        for y in range(f, f + 4):
            if free(S, x, y, z):
                bp.set(x, y, z, "bookshelf" if y < f + 3 else "oak_slab[type=bottom,waterlogged=false]")
    for b in (65, 115, 245, 295):
        x, z = P(b, 7.0)
        bp.table(x, f, z)
        bp.set(x, f + 1, z, "candle[candles=2,lit=true,waterlogged=false]")
    for b in (90, 270):
        x, z = P(b, 6.6)
        bp.set(x, f, z, f"lectern[facing={in_dir(x, z)},has_book=false,powered=false]")
    x, z = P(30, 9.2)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_chapter")
    x, z = P(330, 9.2)
    bp.barrel(x, f, z, "up")
    x, z = P(120, 5.2)
    bp.spawner(x, f, z, MOB_KNIGHT)
    level_lights(S, f)
    # the partition: a hearth on its east face, a banner wall on the west
    x, z = P(B0 - 6, 7.0)
    bp.set(x, f, z, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")


def refectory(S):
    """L2: the refectory and dormitory of the builders."""
    bp = S.bp
    f = LV[2]
    rin = Rt(f) - 1.5
    for b0, b1 in ((60, 120), (240, 300)):
        for (x, z, r, b) in ring_cells(f, 5.8, 6.8, b0, b1):
            if free(S, x, f, z):
                bp.table(x, f, z, top="spruce_pressure_plate", leg="spruce_fence")
        for (x, z, r, b) in ring_cells(f, 4.6, 5.6, b0 + 4, b1 - 4):
            if free(S, x, f, z):
                bp.set(x, f, z, stair("spruce_stairs", in_dir(x, z)))
    for b, kind in ((140, "smoker[facing=north,lit=false]"), (146, "barrel"), (152, "barrel"),
                    (215, "cauldron"), (222, "crafting_table")):
        x, z = P(b, rin - 0.5)
        if free(S, x, f, z):
            if kind == "barrel":
                bp.barrel(x, f, z, "up")
            elif kind.startswith("smoker"):
                bp.set(x, f, z, f"smoker[facing={in_dir(x, z)},lit=false]")
            else:
                bp.set(x, f, z, kind)
    for b in (320, 335, 25, 40):
        x, z = P(b, rin - 0.5)
        x2, z2 = P(b, rin - 1.5)
        fc = facing_of(x - x2, z - z2)
        x, z = x2 + DIRS[fc][0], z2 + DIRS[fc][1]
        if free(S, x, f, z) and free(S, x2, f, z2):
            bp.set(x2, f, z2, with_props("white_bed", facing=fc, part="foot", occupied=False))
            bp.set(x, f, z, with_props("white_bed", facing=fc, part="head", occupied=False))
    x, z = P(200 + 30, 8.0)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_refectory")
    x, z = P(270, 4.4)
    bp.spawner(x, f, z, MOB_SKELETON)
    level_lights(S, f)


def chapel(S):
    """L3: the inverted chapel. Pews hang from the ceiling, lanterns stand on chains rising from the floor, the
    altar hangs upside down over the north door."""
    bp = S.bp
    f = LV[3]
    rin = Rt(f) - 1.5
    ceil = f + ROOM_H - 1
    for b0, b1 in ((40, 150), (210, 320)):
        for (x, z, r, b) in ring_cells(f, 5.0, 7.6, b0, b1):
            if int(b) % 12 < 6 and free(S, x, ceil, z):
                fc = facing_of(math.cos(math.radians(b)), math.sin(math.radians(b)))
                bp.set(x, ceil, z, stair("dark_oak_stairs", fc, "top"))
    # red runner round the ring
    for (x, z, r, b) in ring_cells(f, 4.4, 5.4):
        if free(S, x, f, z):
            bp.set(x, f, z, "red_carpet")
    # rising lanterns
    for b in (70, 110, 250, 290):
        x, z = P(b, rin - 0.6)
        if free(S, x, f, z):
            bp.set(x, f, z, "polished_tuff")
            bp.set(x, f + 1, z, "iron_chain[axis=y,waterlogged=false]")
            bp.set(x, f + 2, z, "iron_chain[axis=y,waterlogged=false]")
            bp.set(x, f + 3, z, LANT)
    # the hanging altar over the north door
    for (x, z, r, b) in ring_cells(f, rin - 1.2, rin, 350, 10):
        bp.set(x, ceil, z, "chiseled_quartz_block")
        bp.set(x, ceil - 1, z, "quartz_pillar[axis=y]")
        bp.set(x, ceil - 2, z, stair("quartz_stairs", out_dir(x, z), "top"))
    x, z = P(0, rin - 0.6)
    bp.set(x, ceil - 3, z, "end_rod[facing=down]")
    for b in (340, 20):
        x, z = P(b, rin - 0.6)
        if free(S, x, ceil, z):
            bp.set(x, ceil, z, "iron_chain[axis=y,waterlogged=false]")
            bp.set(x, ceil - 1, z, SOUL_H)
    x, z = P(300, rin - 0.6)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_chapel")
    x, z = P(90, 6.2)
    bp.spawner(x, f, z, MOB_BANSHEE)
    level_lights(S, f, count=2)


def crypt(S):
    """L4: the root crypt. Roots through the vault, moss on the floor, sarcophagi against the wall."""
    bp = S.bp
    f = LV[4]
    rin = Rt(f) - 1.5
    ceil = f + ROOM_H - 1
    for (x, z, r, b) in ring_cells(f, 3.4, rin):
        if not free(S, x, f, z):
            continue
        h = hash01(x, z, 61)
        if h < 0.35:
            bp.set(x, f - 1, z, "moss_block")
            if h < 0.15:
                bp.set(x, f, z, "moss_carpet")
        hc = hash01(x, z, 62)
        if free(S, x, ceil, z):
            if hc < 0.3:
                bp.set(x, ceil + 1, z, "rooted_dirt")
                bp.set(x, ceil, z, "hanging_roots[waterlogged=false]")
            elif hc < 0.4:
                bp.set(x, ceil, z, "pointed_dripstone[thickness=frustum,vertical_direction=down,waterlogged=false]")
                bp.set(x, ceil - 1, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    for b in (60, 110, 250, 300):
        x, z = P(b, rin - 0.5)
        if free(S, x, f, z):
            bp.set(x, f, z, "polished_deepslate")
            bp.set(x, f + 1, z, "deepslate_tile_slab[type=bottom,waterlogged=false]")
            x2, z2 = P(b + 9, rin - 0.5)
            if free(S, x2, f, z2):
                bp.set(x2, f, z2, "polished_deepslate")
                bp.set(x2, f + 1, z2, "candle[candles=1,lit=true,waterlogged=false]")
    for b in (30, 330):
        x, z = P(b, rin - 0.5)
        if free(S, x, f + 2, z):
            bp.set(x, f + 2, z, "cobweb")
    x, z = P(225, rin - 0.6)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_crypt")
    x, z = P(90, 5.0)
    bp.spawner(x, f, z, MOB_CRAWLER)
    level_lights(S, f, soul=True, count=3)


def unmaking(S):
    """L5: the unmaking. Amethyst grows through the walls, the outer wall comes apart into the void."""
    bp = S.bp
    f = LV[5]
    rt = Rt(f)
    rin = rt - 1.5
    for (x, z, r, b) in ring_cells(f, rin, rt + 0.3):
        for y in range(f, f + ROOM_H):
            h = hash3(x, y, z, 81)
            if bp.get(x, y, z) in ("minecraft:air", "minecraft:iron_bars", "minecraft:glass_pane"):
                continue
            if h < 0.12:
                bp.set(x, y, z, "crying_obsidian")
            elif h < 0.2:
                bp.set(x, y, z, "amethyst_block")
    # breaches in the outer wall where the void is open, masonry floating outside
    for b in (60, 300, 120):
        cells = []
        for y in range(f + 1, f + 6):
            for db in (-5, 0, 5):
                for rr in (rt - 1.0, rt):
                    x, z = P(b + db, rr)
                    cells.append((x, y, z))
        ox, oz = P(b, rt + 1.4)
        if all(bp.get(ox, y, oz) in ("minecraft:air", None) and (ox, y, oz) not in S.walk for y in range(f, f + 7)):
            for (x, y, z) in cells:
                bp.set(x, y, z, AIR)
            x, z = P(b, rt - 0.5)
            bp.set(x, f + 1, z, "polished_blackstone_wall")
    for (x, z, r, b) in ring_cells(f, rin - 1.0, rin):
        y = f + int(hash01(x, z, 83) * 6)
        if free(S, x, y, z) and hash01(x, z, 84) < 0.45:
            ox, oz = DIRS[in_dir(x, z)]
            behind = bp.get(x - ox, y, z - oz) or "minecraft:air"
            if behind != "minecraft:air" and not any(k in behind for k in ("cluster", "bars", "pane", "lantern")):
                bp.set(x, y, z, f"amethyst_cluster[facing={in_dir(x, z)},waterlogged=false]")
        if free(S, x, f, z) and hash01(x, z, 85) < 0.3:
            bp.set(x, f - 1, z, "sculk")
    # fragments of the wall drifting in the void: chunks of masonry 3-4 wide (a support pass drops anything
    # smaller than 13 blocks)
    n = 0
    for k in range(300):
        h1, h2, h3 = hash01(k, 1, 91), hash01(k, 2, 91), hash01(k, 3, 91)
        b = h1 * 360
        r = rt + 5 + h2 * 9
        y = int(f - 8 + h3 * 22)
        cx, cz = P(b, r)
        if math.hypot(cx, cz) > shaft_r(b, y) - 3.5:
            continue
        w = 2 if hash01(k, 4, 91) < 0.5 else 1
        cells = [(cx + dx, y + dy, cz + dz) for dx in range(-w, w + 1) for dz in range(-1, 2) for dy in (0, 1)]
        cells += [(cx, y + 2, cz), (cx, y - 1, cz)]
        if any((x + dx, yy, z + dz) in S.walk for (x, _, z) in cells for dx in (-1, 0, 1) for dz in (-1, 0, 1)
               for yy in range(y - 6, y + 4)):
            continue
        if any(bp.get(*c) not in ("minecraft:air", None) for c in cells):
            continue
        for c in cells:
            hc = hash3(*c, 93)
            bp.set(*c, masonry(*c) if hc < 0.75 else ("crying_obsidian" if hc < 0.87 else "amethyst_block"))
        if hash01(k, 5, 91) < 0.5:
            bp.set(cx, y - 2, cz, SOUL_H)
        n += 1
        if n >= 9:
            break
    x, z = P(250, rin - 0.6)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_unmaking")
    x, z = P(95, 4.4)
    bp.spawner(x, f, z, MOB_WISP)
    level_lights(S, f, soul=True, count=2, r=4.4)


def sanctum(S):
    """L6: the tip sanctum, where the bead chain ends over a ring of gilded blackstone."""
    bp = S.bp
    f = LV[6]
    rin = Rt(f) - 1.5
    for (x, z, r, b) in ring_cells(f, 0, rin):
        if free(S, x, f, z):
            bp.set(x, f - 1, z, "gilded_blackstone" if 2.5 <= r < 3.4 else
                   ("polished_blackstone" if r < 2.5 else "polished_blackstone_bricks"))
    for b in (90, 270):
        x, z = P(b, rin - 0.6)
        if free(S, x, f, z):
            bp.set(x, f, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    x, z = P(225, rin - 0.6)
    bp.chest(x, f, z, in_dir(x, z), loot=LOOT + "is_sanctum")
    x, z = P(130, rin - 0.6)
    bp.set(x, f, z, f"lectern[facing={in_dir(x, z)},has_book=false,powered=false]")
    x, z = P(300, rin - 0.6)
    bp.spawner(x, f, z, MOB_LADY)


# ------------------------------------------------------------------ bridges and galleries (north)
def gallery_floor(x, z):
    return "polished_andesite" if hash01(x, z, 71) < 0.5 else "stone_bricks"


def galleries(S):
    bp = S.bp
    # L0: the main bridge from the gate (south) and the north bridge from the kiosk (the surface loop)
    bridge(S, LV[0], 27, 14)
    bridge(S, LV[0], -14, -27)
    # L1: hermit's cell
    f = LV[1]
    bridge(S, f, -int(Rt(f)) - 1, -26)
    rock_room(S, -1, -28, 1, -26, f, 4, floor=gallery_floor)
    rock_room(S, -3, -33, 3, -29, f, 5, floor=gallery_floor)
    bp.bed(-3, f, -33, "south", color="brown")
    bp.set(3, f, -33, f"lectern[facing=west,has_book=false,powered=false]")
    bp.chest(2, f, -33, "south", loot=LOOT + "is_hermit")
    bp.set(0, f + 4, -31, "iron_chain[axis=y,waterlogged=false]")
    bp.set(0, f + 3, -31, LANT_H)
    # L2: the quarry gallery, the rock stair up to the rim (shortcut 1)
    f = LV[2]
    bridge(S, f, -int(Rt(f)) - 1, -26)
    rock_room(S, -1, -28, 1, -26, f, 4, floor=gallery_floor)
    rock_room(S, -7, -34, 8, -29, f, 6, floor=gallery_floor)
    quarry_stair(S)
    for (x, z) in ((-7, -34), (-6, -34), (-7, -33)):
        bp.barrel(x, f, z, "up")
    bp.set(-5, f, -34, "stonecutter[facing=south]")
    bp.set(-4, f, -34, "grindstone[face=floor,facing=south]")
    for x in range(-2, 5):
        bp.set(x, f, -34, "rail[shape=east_west,waterlogged=false]")
    bp.set(5, f, -34, "chest[facing=south,type=single,waterlogged=false]")
    bp.chest(5, f, -34, "south", loot=LOOT + "is_quarry")
    for (x, z) in ((-6, -30), (6, -30)):
        bp.set(x, f + 5, z, "iron_chain[axis=y,waterlogged=false]")
        bp.set(x, f + 4, z, LANT_H)
    for y in range(f, f + 3):
        bp.set(-7, y, -29, "cobblestone" if y < f + 2 else "cobblestone_slab[type=bottom,waterlogged=false]")
    # L3: the ossuary gallery, hub site of grace, top of the shore lift
    f = LV[3]
    bridge(S, f, -int(Rt(f)) - 1, -26)
    rock_room(S, -1, -28, 1, -26, f, 4, floor=gallery_floor)
    rock_room(S, -9, -36, 13, -29, f, 7, wall=lambda x, y, z: "tuff_bricks" if hash3(x, y, z, 5) < 0.7
              else "polished_tuff", floor=lambda x, z: "polished_tuff" if (x + z) % 3 else "tuff_bricks")
    for x in range(-8, 13, 2):
        for y in (f + 2, f + 4):
            if bp.get(x, y, -37) not in (None,):
                bp.set(x, y, -37, "bone_block[axis=y]" if (x + y) % 4 else "skeleton_skull[rotation=0]")
    for x in range(-8, 13, 3):
        bp.set(x, f + 5, -37, "polished_tuff")
    bp.set(-6, f, -34, MOD["waystone"])
    bp.set(-4, f, -35, "candle[candles=4,lit=true,waterlogged=false]")
    bp.chest(4, f, -36, "south", loot=LOOT + "is_ossuary")
    for (x, z) in ((-5, -32), (6, -32)):
        bp.set(x, f + 6, z, "iron_chain[axis=y,waterlogged=false]")
        bp.set(x, f + 5, z, SOUL_H)
    # L4: the broken bridge
    f = LV[4]
    bridge(S, f, -int(Rt(f)) - 1, -26, broken=(-24, -16))
    rock_room(S, -1, -28, 1, -26, f, 4, floor=gallery_floor)
    bp.set(0, f + 3, -28, LANT_H)
    # L5: the crystal bridge to the reliquary
    f = LV[5]
    bridge(S, f, -int(Rt(f)) - 1, -26, crystal=True)
    rock_room(S, -1, -28, 1, -26, f, 4, wall=lambda x, y, z: "amethyst_block", floor=lambda x, z: "calcite")
    rock_room(S, -4, -33, 4, -29, f, 6, wall=lambda x, y, z: "amethyst_block" if hash3(x, y, z, 7) < 0.6
              else "calcite", floor=lambda x, z: "calcite")
    for (x, z, fc) in ((-4, -31, "east"), (4, -31, "west"), (-2, -33, "south"), (2, -33, "south")):
        bp.set(x, f + 3, z, f"amethyst_cluster[facing={fc},waterlogged=false]")
    bp.chest(0, f, -33, "south", loot=LOOT + "is_reliquary")
    bp.set(-3, f, -33, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(3, f, -33, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(0, f + 5, -31, "iron_chain[axis=y,waterlogged=false]")
    bp.set(0, f + 4, -31, SOUL_H)
    # L6: bridge, the long corridor north and the rock stair down to the lake (main path)
    f = LV[6]
    bridge(S, f, -int(Rt(f)) - 1, -26)
    cavern_stair(S)


def quarry_stair(S):
    """Switchback rock stair from the quarry gallery (feet -27) to a kiosk on the north rim (feet 1): an iron door
    that opens only from inside."""
    bp = S.bp
    A, B = (9, 11), (13, 15)
    sb = "stone_brick_stairs"
    # bottom landing joined to the gallery
    rock_room(S, 9, -30, 11, -28, -27, 5, floor=gallery_floor)
    f = flight(S, A, -30, -1, -27, 7, sb)           # -> -20 north
    rock_room(S, 9, -40, 15, -38, f, 5, floor=gallery_floor)
    f = flight(S, B, -38, 1, f, 7, sb)              # -> -13 south
    rock_room(S, 9, -30, 15, -28, f, 5, floor=gallery_floor)
    f = flight(S, A, -30, -1, f, 7, sb)             # -> -6 north
    rock_room(S, 9, -40, 15, -38, f, 5, floor=gallery_floor)
    bp.set(12, f + 4, -39, LANT_H)
    f = flight(S, B, -38, 1, f, 7, sb)              # -> 1 south: the surface
    # the kiosk over the top flight
    for x in range(12, 17):
        for z in range(-38, -26):
            for y in range(1, 6):
                edge = x in (12, 16) or z in (-38, -27)
                if y == 5:
                    bp.set(x, y, z, "stone_bricks" if edge else "polished_andesite")
                elif edge:
                    if bp.get(x, y, z) not in ("minecraft:air",) or z == -27 or x in (12, 16):
                        bp.set(x, y, z, "stone_bricks" if (x + y + z) % 5 else "chiseled_stone_bricks")
    for x in range(13, 16):
        for z in range(-30, -27):
            bp.set(x, 0, z, "polished_andesite")
            for y in range(1, 5):
                bp.set(x, y, z, AIR)
    for z in range(-37, -30):
        for x in range(13, 16):
            for y in range(1, 5):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
    bp.set(12, 6, -38, "stone_brick_wall")
    bp.set(16, 6, -38, "stone_brick_wall")
    bp.set(14, 6, -27, LANT)
    bp.door(14, 1, -27, "south", wood="iron")
    bp.set(15, 2, -28, "lever[face=wall,facing=north,powered=false]")
    bp.set(13, 3, -28, "wall_torch[facing=north]")
    for x in range(13, 16):
        bp.set(x, 0, -26, "polished_andesite")


def cavern_stair(S):
    """From the sanctum bridge: a corridor north (compression), three flights down to the north shore."""
    bp = S.bp
    A, B = (1, 3), (-3, -1)
    sb = "deepslate_brick_stairs"
    dk = lambda x, y, z: "deepslate_bricks" if hash3(x, y, z, 3) < 0.75 else "cracked_deepslate_bricks"
    fl = lambda x, z: "polished_deepslate" if (x + z) % 2 else "deepslate_tiles"
    # antechamber at the bridge end, then the corridor at feet -84
    rock_room(S, -3, -28, 1, -26, -83, 4, wall=dk, floor=fl)
    for x in range(-3, 2):
        bp.set(x, -84, -28, slab("polished_deepslate_slab"))
    rock_room(S, -3, -50, -1, -29, -84, 4, wall=dk, floor=fl)
    for z in range(-48, -29, 6):
        bp.set(-2, -81, z, SOUL_H)
    # the stairwell: bottom landing (feet -105) south, flights north/south/north
    rock_room(S, -3, -43, 3, -41, FA, 5, wall=dk, floor=fl)
    f = flight(S, A, -43, -1, FA, 7, sb, wall=dk)        # -> -98 north
    rock_room(S, -3, -53, 3, -51, f, 5, wall=dk, floor=fl)
    bp.set(0, f + 4, -53, SOUL_H)
    f = flight(S, B, -51, 1, f, 7, sb, wall=dk)          # -> -91 south
    rock_room(S, -3, -43, 3, -41, f, 5, wall=dk, floor=fl)
    bp.set(0, f + 4, -43, SOUL_H)
    f = flight(S, A, -43, -1, f, 7, sb, wall=dk)         # -> -84 north
    rock_room(S, -3, -53, 3, -51, f, 5, wall=dk, floor=fl)
    bp.set(0, f + 4, -53, SOUL_H)
    # the bottom corridor out to the shore
    rock_room(S, -1, -40, 1, -35, FA, 4, wall=dk, floor=fl)
    bp.set(0, FA + 3, -40, SOUL_H)


# ------------------------------------------------------------------ the depths
def depths(S):
    bp = S.bp
    # shores: crescents north and south
    for x in range(-42, 43):
        for z in range(-42, 43):
            r = math.hypot(x, z)
            if r < 27.6:
                continue
            b = bearing(x, z)
            if not (abs(angdiff(b, 0)) <= 58 or abs(angdiff(b, 180)) <= 58):
                continue
            if r > min(void_r(b, y) for y in range(FA, FA + 4)) - 0.5:
                continue
            for y in range(LAKE_BED, FA):
                if bp.get(x, y, z) in ("minecraft:water", "minecraft:air", None) or (x, y, z) in S.skin:
                    if y == FA - 1:
                        h = hash01(x, z, 101)
                        spec = ("moss_block" if h < 0.25 else "cobbled_deepslate" if h < 0.5 else
                                "deepslate" if h < 0.8 else "tuff")
                    else:
                        spec = rock(x, y, z)
                    bp.set(x, y, z, spec)
            h = hash01(x, z, 102)
            if bp.get(x, FA, z) == "minecraft:air":
                if h < 0.06:
                    bp.set(x, FA, z, "glow_lichen[down=true,east=false,north=false,south=false,up=false,west=false,"
                                     "waterlogged=false]")
                elif h < 0.09:
                    bp.set(x, FA, z, "brown_mushroom")
    # the island
    for x in range(-24, 25):
        for z in range(-24, 25):
            r = math.hypot(x, z)
            for y in range(LAKE_BED, FA):
                rr = 20.5 + (FA - 1 - y) * 0.45
                if r <= rr:
                    if y == FA - 1:
                        bp.set(x, y, z, arena_floor(x, z, r))
                    else:
                        bp.set(x, y, z, rock(x, y, z) if r > 18 else "deepslate")
            if 19.6 <= r < 20.6:
                b = bearing(x, z)
                if abs(x) <= 1:
                    continue
                bp.set(x, FA, z, "polished_blackstone_brick_wall")
    for k in range(8):
        b = 22.5 + 45 * k
        x, z = pt(b, 18.6)
        for y in range(FA, FA + 3):
            bp.set(x, y, z, "polished_blackstone_bricks" if y < FA + 2 else "chiseled_polished_blackstone")
        bp.set(x, FA + 3, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.boss_seal(0, FA - 1, 0, BOSS, 15)
    # causeways
    for sz in (-1, 1):
        for z in range(21 * sz, 28 * sz + sz, sz):
            for x in range(-2, 3):
                for y in range(LAKE_BED, FA):
                    bp.set(x, y, z, rock(x, y, z) if y < FA - 1 else
                           ("polished_deepslate" if abs(x) < 2 else "polished_blackstone_bricks"))
                if abs(x) == 2:
                    bp.set(x, FA, z, "polished_blackstone_brick_wall")
                else:
                    for y in range(FA, FA + 4):
                        bp.set(x, y, z, AIR)
            if z % 3 == 0:
                bp.set(2, FA + 1, z, SOUL)
        bp.mist(-1, FA, 20 * sz, 1, FA + 3, 20 * sz)
    # north shore: waystone before the boss, lanterns
    bp.set(-4, FA, -32, MOD["waystone"])
    bp.set(-5, FA, -31, "candle[candles=3,lit=true,waterlogged=false]")
    for (x, z) in ((3, -31), (-3, -36), (6, 30), (-5, 33)):
        bp.set(x, FA, z, "polished_deepslate_wall")
        bp.set(x, FA + 1, z, SOUL)
    # the vault behind sealed bars (south)
    dk = lambda x, y, z: "polished_blackstone_bricks" if hash3(x, y, z, 3) < 0.8 else "gilded_blackstone"
    rock_room(S, -1, 35, 1, 40, FA, 4, wall=dk, floor=lambda x, z: "polished_blackstone")
    for x in range(-1, 2):
        for z in range(31, 41):
            if bp.get(x, FA - 1, z) in ("minecraft:water", "minecraft:air", None) or (x, FA - 1, z) in S.skin:
                bp.set(x, FA - 1, z, "polished_blackstone")
    rock_room(S, -6, 41, 6, 48, FA, 6, wall=dk, floor=lambda x, z: "polished_blackstone" if (x + z) % 2 else
              "polished_blackstone_bricks")
    for x in range(-1, 2):
        for y in range(FA, FA + 3):
            bp.set(x, y, 40, MOD["vault_bars"])
    for x in range(-5, 6, 2):
        bp.set(x, FA - 1, 45, "gold_block" if x == -1 or x == 1 else "chiseled_polished_blackstone")
    bp.chest(-6, FA, 45, "east", loot=LOOT + "is_vault")
    bp.chest(6, FA, 45, "west", loot=LOOT + "is_vault")
    bp.chest(0, FA, 48, "north", loot=LOOT + "is_vault")
    for (x, z) in ((-5, 42), (5, 42), (-5, 47), (5, 47)):
        bp.set(x, FA + 5, z, SOUL_H)
    bp.set(3, FA, 48, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(-3, FA, 48, "smithing_table")
    # dripstone from the cavern ceiling
    for k in range(260):
        x = int(hash01(k, 1, 111) * 80) - 40
        z = int(hash01(k, 2, 111) * 80) - 40
        r = math.hypot(x, z)
        if r < 26 or r > 40:
            continue
        for y in range(CAV_TOP - 1, FA + 4, -1):
            if bp.get(x, y, z) == "minecraft:air" and (x, y + 1, z) in S.skin:
                ln = 1 + int(hash01(k, 3, 111) * 3)
                if all(bp.get(x, y - i, z) == "minecraft:air" for i in range(ln + 3)):
                    for i in range(ln):
                        th = "tip" if i == ln - 1 else ("base" if i == 0 and ln > 2 else "frustum")
                        bp.set(x, y - i, z, f"pointed_dripstone[thickness={th},vertical_direction=down,"
                                            f"waterlogged=false]")
                break


def arena_floor(x, z, r):
    if r > AR:
        return "polished_blackstone_bricks"
    if 5.5 <= r < 6.5 or 11.5 <= r < 12.5:
        return "gilded_blackstone" if int(bearing(x, z)) % 30 < 4 else "chiseled_polished_blackstone"
    return "polished_deepslate" if int(r) % 2 else "deepslate_tiles"


def lifts(S):
    """The two bubble-column lifts in glass tubes: north from the shore to the ossuary gallery, south from the
    south shore to the rim beside the gate."""
    for (tx, tz), top in ((LIFT_N, LIFT_N_TOP), (LIFT_S, LIFT_S_TOP)):
        lift(S, tx, tz, FA, top)


def lift(S, tx, tz, y0, y1):
    bp = S.bp
    r0 = math.hypot(tx, tz)
    ux, uz = -tx / r0, -tz / r0             # toward the axis (the glass face)
    fx, fz = DIRS[facing_of(ux, uz)]
    bp.set(tx, y0 - 1, tz, "soul_sand")
    for y in range(y0, y1 + 1):
        bp.set(tx, y, tz, "bubble_column[drag=false]")
    for y in range(y0 - 1, y1 + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                x, z = tx + dx, tz + dz
                front = (dx, dz) == (fx, fz)
                corner = dx != 0 and dz != 0
                free_side = bp.get(x, y, z) in ("minecraft:air", None) and (x, y, z) in S.void
                if y == y1 and y1 == LIFT_S_TOP or y == y1 and y1 == LIFT_N_TOP:
                    continue
                if front or (free_side and not corner):
                    spec = "glass"
                elif corner:
                    spec = "dark_prismarine" if (y % 8) else "sea_lantern"
                else:
                    spec = "sea_lantern" if y % 4 == 0 else "prismarine_bricks"
                bp.set(x, y, z, spec)
                S.skin.discard((x, y, z))
    # the door at the bottom on the axis side, a landing in front of it
    dx_, dz_ = tx + fx, tz + fz
    rot = {"south": 0, "west": 4, "north": 8, "east": 12}[facing_of(fx, fz)]
    side = facing_of(fz, -fx)     # tangential: the wall sign hangs on the casing corner beside the opening
    bp.set(dx_, y0, dz_, f"spruce_sign[rotation={rot},waterlogged=false]")
    bp.set(dx_, y0 + 1, dz_, f"spruce_wall_sign[facing={side},waterlogged=false]")
    bp.set(dx_ - DIRS[side][0], y0 + 1, dz_ - DIRS[side][1], "dark_prismarine")
    bp.set(dx_, y0 - 1, dz_, "dark_prismarine")
    bp.set(dx_, y0 + 2, dz_, "dark_prismarine")
    for k in (1, 2):
        x, z = tx + fx * (1 + k), tz + fz * (1 + k)
        bp.set(x, y0 - 1, z, "polished_deepslate")
        for y in range(y0, y0 + 3):
            if bp.get(x, y, z) in ("minecraft:water",):
                bp.set(x, y, z, AIR)
    # the top: floor round the water, a ring of chains and lanterns
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                bp.set(tx + dx, y1, tz + dz, "dark_prismarine" if dx and dz else "prismarine_bricks")
                for y in range(y1 + 1, y1 + 4):
                    if bp.get(tx + dx, y, tz + dz) is None or (tx + dx, y, tz + dz) in S.skin:
                        bp.set(tx + dx, y, tz + dz, AIR)
    for y in range(y1 + 1, y1 + 4):
        bp.set(tx, y, tz, AIR)


def lift_house(S):
    """Pavilion over the top of the south lift on the rim."""
    bp = S.bp
    tx, tz = LIFT_S
    for dx in (-2, 2):
        for dz in (-2, 2):
            for y in range(1, 5):
                bp.set(tx + dx, y, tz + dz, "polished_andesite" if y < 4 else "chiseled_stone_bricks")
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            m = max(abs(dx), abs(dz))
            if m == 3:
                bp.set(tx + dx, 5, tz + dz, stair("brasshaven:slate_roof_tile_stairs",
                                                  facing_of(-dx, -dz) if abs(dx) != abs(dz) else
                                                  facing_of(0, -dz), "bottom"))
            elif m == 2:
                bp.set(tx + dx, 5, tz + dz, "brasshaven:slate_roof_tiles")
                bp.set(tx + dx, 6, tz + dz, stair("brasshaven:slate_roof_tile_stairs",
                                                  facing_of(-dx, -dz) if abs(dx) != abs(dz) else
                                                  facing_of(0, -dz), "bottom"))
            else:
                bp.set(tx + dx, 5, tz + dz, "brasshaven:slate_roof_tiles")
                bp.set(tx + dx, 6, tz + dz, "brasshaven:slate_roof_tiles")
    bp.set(tx, 7, tz, "brasshaven:slate_roof_tile_slab[type=bottom,waterlogged=false]")
    bp.set(tx, 4, tz, LANT_H)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if (dx or dz) and bp.get(tx + dx, 0, tz + dz) is None:
                bp.set(tx + dx, 0, tz + dz, "polished_andesite")


# ------------------------------------------------------------------ approach and camp
ROAD = [(30, 112), (26, 102), (14, 94), (0, 88), (-9, 78), (-8, 66), (2, 56), (3, 46), (0, 38), (0, 33)]


def road_points():
    pts = []
    for i in range(len(ROAD) - 1):
        p0 = ROAD[max(0, i - 1)]
        p1, p2 = ROAD[i], ROAD[i + 1]
        p3 = ROAD[min(len(ROAD) - 1, i + 2)]
        for k in range(12):
            t = k / 12
            t2, t3 = t * t, t * t * t
            pts.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j])
                                    * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    pts.append(ROAD[-1])
    return pts


def approach(S):
    bp = S.bp
    cells = set()
    for (px, pz) in road_points():
        for x in range(int(px) - 3, int(px) + 4):
            for z in range(int(pz) - 3, int(pz) + 4):
                if math.hypot(x - px, z - pz) <= 1.7 + (fbm(x, z, 5.0, 3) - 0.5) * 0.8:
                    cells.add((x, z))
    for (x, z) in cells:
        if math.hypot(x, z) < RIM1 + 0.5:
            continue
        h = hash01(x, z, 121)
        bp.set(x, 0, z, "dirt_path" if h < 0.6 else ("coarse_dirt" if h < 0.8 else "cobblestone"))
        for y in range(1, 5):
            if bp.get(x, y, z) is None:
                bp.set(x, y, z, AIR)
    # lantern posts along the road
    pts = road_points()
    for i in range(6, len(pts) - 4, 16):
        px, pz = pts[i]
        qx, qz = pts[i + 1]
        nx, nz = -(qz - pz), (qx - px)
        n = math.hypot(nx, nz) or 1
        x, z = int(round(px + nx / n * 3)), int(round(pz + nz / n * 3))
        if (x, z) in cells:
            continue
        bp.set(x, 0, z, "cobblestone")
        bp.set(x, 1, z, "cobblestone_wall")
        bp.set(x, 2, z, "spruce_fence")
        bp.set(x, 3, z, LANT)
    # the ruined wayside arch framing the spire
    ax, az = -9, 72
    for sx in (-3, 3):
        for y in range(1, 9 if sx < 0 else 6):
            for dz in (0, 1):
                bp.set(ax + sx, y, az + dz, "stone_bricks" if hash3(sx, y, dz, 5) < 0.7 else "mossy_stone_bricks")
        bp.set(ax + sx, 0, az, "cobblestone")
        bp.set(ax + sx, 0, az + 1, "cobblestone")
    for x in range(ax - 3, ax + 2):
        for dz in (0, 1):
            bp.set(x, 9, az + dz, "stone_bricks" if x < ax else "mossy_stone_bricks")
    bp.set(ax - 2, 8, az, stair("stone_brick_stairs", "west", "top"))
    bp.set(ax + 1, 0, az + 3, "mossy_cobblestone")
    bp.set(ax + 2, 1, az + 3, "mossy_stone_brick_slab[type=bottom,waterlogged=false]")
    camp(S)


def camp(S):
    """The pilgrims' camp at the start of the road: two tents, a fire, a signpost to the hole."""
    bp = S.bp
    cx, cz = 32, 116
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if math.hypot(x - cx, (z - cz) * 1.1) <= 6.8:
                h = hash01(x, z, 131)
                bp.set(x, 0, z, "coarse_dirt" if h < 0.35 else ("dirt_path" if h < 0.6 else "grass_block[snowy=false]"))
                for y in range(1, 5):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, AIR)
    smoke = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
    bp.set(cx, 0, cz, "cobblestone")
    bp.set(cx, 1, cz, smoke)
    for (x, z) in ((cx - 1, cz - 1), (cx + 1, cz + 1), (cx + 1, cz - 1)):
        bp.set(x, 1, z, stair("spruce_stairs", facing_of(cx - x, 0) if x != cx else "north"))
    for (tx, tz, col) in ((cx - 5, cz - 3, "white_wool"), (cx + 3, cz + 3, "brown_wool")):
        for dz in range(0, 4):
            bp.set(tx - 1, 1, tz + dz, col)
            bp.set(tx + 1, 1, tz + dz, col)
            bp.set(tx, 2, tz + dz, col)
            bp.set(tx, 1, tz + dz, AIR)
        bp.set(tx, 0, tz + 3, "spruce_planks")
    bp.barrel(cx - 4, 1, cz + 3, "up")
    bp.barrel(cx - 5, 1, cz + 3, "up")
    bp.chest(cx + 4, 1, cz - 3, "west", loot=LOOT + "is_camp")
    bp.set(cx + 4, 1, cz - 2, "crafting_table")
    bp.set(cx - 2, 1, cz - 5, "spruce_fence")
    bp.set(cx - 2, 2, cz - 5, "spruce_fence")
    bp.set(cx - 2, 3, cz - 5, LANT)


# ------------------------------------------------------------------ finishing
def lids(S):
    """Keep the hole open above the ground layer: air 1..4 over every open column round the crown and an
    invisible light block at 5, so the template carves any terrain that stands higher than the ground layer
    (carve_limit drops sky air in columns with nothing built above the ground)."""
    bp = S.bp
    built = {}
    for (x, y, z), v in bp.blocks.items():
        if y >= 1 and v[0] not in ("minecraft:air",):
            built[(x, z)] = True
    for x in range(-34, 35):
        for z in range(-34, 35):
            r = math.hypot(x, z)
            if r > RIM1 + 0.5:
                continue
            for y in range(1, 5):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
            if (x, z) not in built and bp.get(x, 5, z) is None:
                bp.set(x, 5, z, "light[level=0,waterlogged=false]")


def footings(S, depth=4):
    """Shallow footings under the ground-layer blocks outside the hole (foundation=False: the pipeline's global
    foundation under the whole disc would cost far more entries)."""
    bp = S.bp
    cols = [(x, z, v[0]) for (x, y, z), v in bp.blocks.items() if y == 0 and v[0] != "minecraft:air"
            and math.hypot(x, z) > R_SHAFT + 0.5]
    for x, z, name in cols:
        short = name.split(":")[1]
        soil = short in ("grass_block", "dirt", "coarse_dirt", "dirt_path", "spruce_planks")
        for d in range(1, depth + 1):
            if bp.get(x, -d, z) is not None:
                break
            bp.set(x, -d, z, "dirt" if soil and d <= 2 else "stone")


def inverted_spire(bp):
    S = Site(bp)
    hole(S)
    collar(S)
    tower(S)
    tip(S)
    helix(S)
    doors(S)
    windows(S)
    crown(S)
    rim(S)
    galleries(S)
    depths(S)
    lifts(S)
    lift_house(S)
    chapter(S)
    refectory(S)
    chapel(S)
    crypt(S)
    unmaking(S)
    sanctum(S)
    chains(S)
    approach(S)
    lids(S)
    footings(S)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("crown_court", (2, 1, 20), (0, 20, -6)),
    ("descent", (*pt(250, 15.8), -10), (*pt(330, 12.0), -30)),
    ("chapter_library", (*pt(150, 7.4), LV[1]), (*pt(60, 7.0), LV[1] + 3)),
    ("inverted_chapel", (*pt(250, 6.2), LV[3]), (*pt(330, 6.0), LV[3] + 6)),
    ("root_crypt", (*pt(140, 5.2), LV[4]), (*pt(60, 5.2), LV[4] + 4)),
    ("ossuary_gallery", (8, LV[3], -31), (-6, LV[3] + 2, -34)),
    ("arena", (0, FA, -30), (0, FA + 10, 0)),
]


register(StructureDef(
    "inverted_spire", "overworld",
    ["plains", "sunflower_plains", "meadow", "forest", "birch_forest", "taiga", "savanna", "old_growth_birch_forest"],
    [Piece("spire", inverted_spire, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_SKELETON, 6, 1, 2), (MOB_CRAWLER, 3, 1, 1)],
    title_fr="La Flèche renversée", title_en="Inverted Spire"))
