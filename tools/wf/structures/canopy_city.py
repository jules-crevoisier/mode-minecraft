"""Canopy Temple-City (La Cité-temple de la canopée): a lost city in the jungle, 210 blocks across. A stepped stone
temple 67 high stands in the middle, wrapped by roots and crowned by a broken brass sun-disc; five colossal hollow
trunks (16 wide, 56-74 high, built block by block, not vanilla trees) ring it and carry platform districts at three
heights joined by rope bridges and brass zip-line pulleys. Colossal tier (tools/BUILDING.md §1, §12 concept 17, §10,
§15).

Silhouette (one noun phrase, §15.1): a green stepped pyramid with a giant's stair up its south face and a cracked
brass sun-wheel standing on its summit, in a ring of five branching tree-towers.

Layout, ground y = 0 (feet 1), x east, z south. The temple (TC = 0, 0) has six tiers 11 high (half-widths 40 to 20,
chamfered corners, recessed panels between pilasters, jade masks); its terraces have feet 12, 23, 34, 45, 56 and the
summit feet 67. The trunks: A (-50, 66) the Gate Trunk, B (-84, 0) the Market Trunk, C (-50, -66) the Watch Trunk,
D (84, 0) the Lift Trunk, E (50, 66) the Orchid Trunk. Platform levels (feet): L1 25, L2 40, L3 55.

The route (main path, ~900 path blocks):
  * the approach: a jungle track from the south edge past the explorers' camp (waystone, a satellite §15.9) to the
    ruined gate, two stone towers joined by a corbel arch that frames the temple and its giant stair (the reveal);
  * the gate: the west tower's newel stair (25 up) to the gate deck, a rope bridge west to the Root Ward (A-L1,
    huts), the Gate Trunk's newel stair (dwelling in a burl) up to A-L2, a rope bridge north-west to the Market
    (B-L2: stalls, the totem, the second waystone, the hub with the temple in view);
  * the canopy: the Market Trunk's newel up to the High Ward (B-L3), a rope bridge to the Watch (C-L3) and the long
    bridge to the west half of the temple's upper terrace (feet 56); the west door;
  * the temple: the glyph library (feet 56), a stair down to the trap corridor (feet 45, dart traps round three sides
    of the cenote, windows onto it), a stair down into the jade-and-gold sanctum (feet 23, the third waystone), a
    stair down into the hall of offerings (feet 12) and on into the root-choked crypt (feet 1), a passage to the foot
    of the flooded cenote: a ledge spirals 55 blocks up round its walls, round the waterfall falling from the summit
    grate into the pool, to the site of grace (feet 56, the fourth waystone); a narrow stair (compression) climbs to
    the stair-house on the summit and the mist;
  * the boss: the summit arena (39 x 32, open sky) under the broken brass sun-disc; the vault behind sealed bars in
    the disc's dais; the east gate (iron door, lever on the arena side) down to the east terrace, the bridge to the
    Lift Trunk (D-L3) and the brass elevator: a drop shaft into a pool down to the ground and a bubble-column lift up,
    the ground door opening from inside only (the shortcut back, §10.4).
Side routes and loops: the Gate Trunk and the Market Trunk have ground doors (the side route that skips the gate);
the gate deck, A-L1 and E-L1 form a ring over the approach; B-L2 to C-L2 (the seed shrine) and C's stair to C-L3
close a loop in the canopy; the library and the grace room share an iron door that opens from the grace side.
Optional: the Orchid Loft (E-L2), the seed shrine (C-L2), the gate shrine, the secret grotto under the cenote pool,
the burl dwellings.
Loot gradient (§15.6): camp, Root Ward, gate shrine, dwellings tier 1; market 1-2; High Ward, Watch, shrine, library,
trap victims, offerings 2; sanctum, crypt, Orchid Loft 2-3; the cenote grotto and the vault 3.
Height budget: the sun-disc tops out ~103 above the ground layer; the pool and the grotto reach 6 below it.
"""
import math

from .. import nbt
from ..arch import Palette, stair
from ..defs import Piece, StructureDef, register
from ..megakit import BRASS, BRASS_STAIRS, COPPER, GAUGE, GEAR, IRON, PIPES, VERD, W, fbm, hash01, hash3, vnoise
from ..parts import LOOT, MOD

# the temple-city's own boss: the Strangler Fig Queen holds the summit terrace and climbs into the sun-disc
# (StranglerQueen.java finds the disc by its froglight eyes, so keep VERDANT_FROGLIGHT in the disc face)
BOSS = "brasshaven:strangler_queen"
MOB_SPIDER = "minecraft:spider"
MOB_CAVE = "minecraft:cave_spider"
MOB_SKEL = "minecraft:skeleton"
MOB_ZOMBIE = "minecraft:zombie"
MOB_CRAWLER = "brasshaven:crypt_crawler"
MOB_CLOCK = W + "clockwork_spider"

# ------------------------------------------------------------------ dimensions
HW = (40, 36, 32, 28, 24, 20)      # tier half-widths (tier k spans y 11k+1 .. 11k+11)
TH = 11
CH = 5.0                            # corner chamfer
SUMMIT = 66                         # summit top block (feet 67)
SF = SUMMIT + 1
TF = 56                             # feet on the tier-4 terrace (the upper terrace)
L1, L2, L3 = 25, 40, 55             # platform feet
CE = (7, 1)                         # cenote centre
CR = 8.4                            # cenote shaft radius
LEDGE_IN = 4.5                      # ledge inner radius (pool inside)
SP_TOTAL = math.pi / 2 + 4 * 2 * math.pi   # spiral angle: from the west, 4.25 laps, ends north
SP_RISE = 55.0
AC = (0, 4)                         # arena centre
GATE_Z = (71, 81)
R0 = 7.8                            # trunk radius

AIR = "minecraft:air"
WATER = "water[level=0]"
FALL = "water[level=8]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN_Y = "iron_chain[axis=y,waterlogged=false]"
FENCE = "jungle_fence"
LEAVES = "jungle_leaves[distance=1,persistent=true,waterlogged=false]"
JADE, JADE_C, JADE_S = "oxidized_cut_copper", "oxidized_copper", "oxidized_cut_copper_stairs"
EYE = "verdant_froglight[axis=y]"
GOLD = "gold_block"
CORN = ((1, -1), (-1, -1), (-1, 1), (1, 1))      # NE, NW, SW, SE
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}

LADDER = ("stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "mossy_cobblestone", "cobblestone",
          "cobbled_deepslate")
DECK = Palette({"jungle_planks": 6, "bamboo_planks": 2, "stripped_jungle_wood[axis=y]": 1, "spruce_planks": 1},
               seed=1701, scale=1.6)
HUTWALL = Palette({"bamboo_planks": 4, "jungle_planks": 3, "bamboo_mosaic": 1, "stripped_bamboo_block[axis=y]": 1},
                  seed=1702, scale=1.8)
INNER = Palette({"tuff_bricks": 4, "mossy_stone_bricks": 3, "stone_bricks": 3, "polished_tuff": 1,
                 "cracked_stone_bricks": 1}, seed=1703, scale=2.4)
CRYPT = Palette({"mossy_cobblestone": 4, "cobbled_deepslate": 3, "tuff": 2, "mossy_stone_bricks": 2, "rooted_dirt": 1},
                seed=1704, scale=2.0)
ROCK = Palette({"stone": 4, "tuff": 3, "andesite": 2, "mossy_cobblestone": 2, "cobbled_deepslate": 1}, seed=1705,
               scale=2.6)


def empty(b):
    return b is None or b in (AIR, "minecraft:cave_air")


def card(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def mm(x, z):
    ax, az = abs(x), abs(z)
    return max(ax, az, (ax + az + CH) / 2.0)


def tier_k(y):
    return min(5, max(0, (y - 1) // TH))


def hw_at(y):
    return HW[tier_k(y)]


def col_top(m):
    for k in range(5, -1, -1):
        if HW[k] >= m:
            return TH * (k + 1), k
    return None, None


def tstone(x, y, z):
    """The temple's value ladder: dark and mossy at the foot, light at the crown, smooth noise, ±1 step jitter."""
    n = vnoise(x + z * 0.7 + y * 0.25, y * 0.9 - (x - z) * 0.15, 6.0, 71)
    j = hash3(x, y, z, 72)
    base = 2.7 - 2.1 * min(1.0, max(0.0, y / 66.0))
    i = int(base + (n - 0.5) * 2.4 + (j - 0.5) * 0.9 + 0.5)
    return LADDER[max(0, min(len(LADDER) - 1, i))]


def tstair(x, y, z):
    s = tstone(x, y, z)
    return "mossy_stone_brick_stairs" if s.startswith("mossy") else "stone_brick_stairs"


# ------------------------------------------------------------------ the site
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.walk = {}       # (x, z) -> [feet]  (outdoor decks, bridges, terraces: for the rails)
        self.keep = set()    # air cells that must stay clear
        self.inner = set()   # carved interior air: sealed against the unset void at the end
        self.deck = set()    # (x, z, feet) of decks and terraces (bridges do not overwrite them)
        self.paths = set()   # ground path columns
        self.busy = set()    # columns where no tree may grow

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)

    def put(self, x, y, z, spec):
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def clear(self, x, y, z, inner=False):
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))
        if inner:
            self.inner.add((x, y, z))

    def solid(self, x, y, z, spec):
        """A block that belongs where air was reserved (a tread, a doorframe): set it and release the cell."""
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))
        self.inner.discard((x, y, z))

    def add_walk(self, x, z, f):
        lst = self.walk.setdefault((x, z), [])
        if f not in lst:
            lst.append(f)

    def levels(self, x, z):
        return self.walk.get((x, z), ())


def carve(S, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                S.clear(x, y, z, inner=True)


def room(S, x0, z0, x1, z1, f, h, wall, floor, ceil=None):
    """Air box x0..x1, z0..z1, feet f, h high; floor at f - 1, ceiling at f + h, walls one block round it (cells
    already reserved as air, doorways for instance, stay open)."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(f - 1, f + h + 1):
                if edge:
                    S.put(x, y, z, wall(x, y, z))
                elif y == f - 1:
                    S.put(x, y, z, floor(x, z))
                elif y == f + h:
                    S.put(x, y, z, (ceil or wall)(x, y, z))
                else:
                    S.clear(x, y, z, inner=True)


def flight(S, x0, z0, facing, n, f0, width, wdir, mat="stone_brick", fill="stone_bricks", head=4, inner=True):
    """n steps climbing toward `facing`: step k (1..n) at distance k - 1 from (x0, z0), its stair block at y = f0 + k - 1
    (feet f0 + k), `width` cells toward `wdir`, `head` blocks of air over each tread, a stringer under it."""
    dx, dz = DIRS[facing]
    px, pz = DIRS[wdir]
    for k in range(1, n + 1):
        for w in range(width):
            x, z = x0 + dx * (k - 1) + px * w, z0 + dz * (k - 1) + pz * w
            y = f0 + k - 1
            S.solid(x, y, z, stair(mat + "_stairs", facing))
            for yy in range(y - 2, y):
                S.put(x, yy, z, fill)
            for hh in range(1, head + 1):
                S.clear(x, y + hh, z, inner=inner)


def landing(S, x0, z0, x1, z1, f, spec="stone_bricks", head=4):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            S.solid(x, f - 1, z, spec)
            for hh in range(head):
                S.clear(x, f + hh, z, inner=True)


def dart_trap(S, x, f, z, facing, wall_dx, wall_dz):
    """A pressure plate at (x, f, z) beside a dispenser hidden in the wall (one step along wall_dx/dz) that fires
    across the corridor (toward `facing`)."""
    items = nbt.List([nbt.Compound({"Slot": nbt.Byte(0), "id": nbt.String("minecraft:arrow"), "count": nbt.Int(24)})])
    S.bp.set(x + wall_dx, f, z + wall_dz, f"dispenser[facing={facing},triggered=false]", {"Items": items})
    S.solid(x, f, z, "polished_blackstone_pressure_plate[powered=false]")
    S.keep.add((x, f, z))


# ------------------------------------------------------------------ the jungle floor
def ground(S):
    bp = S.bp
    for x in range(-110, 111):
        for z in range(-96, 116):
            r = math.hypot(x, z * 1.02 - 8)
            edge = 104 + (fbm(x * 0.8, z * 0.8, 14.0, 3) - 0.5) * 14
            if r > edge or mm(x, z) <= 41.5:
                continue
            n = fbm(x, z, 9.0, 5)
            h = hash01(x, z, 9)
            top = ("podzol[snowy=false]" if n > 0.62 else "moss_block" if n < 0.34 else
                   "coarse_dirt" if h < 0.08 else "rooted_dirt" if h < 0.12 else "grass_block[snowy=false]")
            bp.set(x, 0, z, top)
            bp.set(x, -1, z, "dirt")
            if r < edge - 8:
                bp.set(x, -2, z, "dirt" if h < 0.7 else "coarse_dirt")


def path_line(S, pts, half=1.6, mat="jungle"):
    """A ground track through the jungle: mossy cobble, gravel, packed mud and dirt path, slightly wandering."""
    bp = S.bp
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 2))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            w = half + (vnoise(px, pz, 5.0, 61) - 0.5) * 1.2
            for x in range(int(px) - 3, int(px) + 4):
                for z in range(int(pz) - 3, int(pz) + 4):
                    if math.hypot(x - px, z - pz) > w or mm(x, z) <= 41.5:
                        continue
                    if (x, z) in S.paths:
                        continue
                    S.paths.add((x, z))
                    h = hash01(x, z, 62)
                    spec = ("mossy_cobblestone" if h < 0.3 else "dirt_path" if h < 0.55 else
                            "gravel" if h < 0.68 else "packed_mud" if h < 0.85 else "coarse_dirt")
                    if mat == "court":
                        spec = ("mossy_stone_bricks" if h < 0.35 else "stone_bricks" if h < 0.6 else
                                "cracked_stone_bricks" if h < 0.75 else "mossy_cobblestone" if h < 0.9 else "moss_block")
                    bp.set(x, 0, z, spec)
                    bp.set(x, -1, z, "dirt")
                    bp.set(x, -2, z, "dirt")
                    if bp.get(x, 1, z) is not None and bp.get(x, 1, z) in ("minecraft:short_grass", "minecraft:fern"):
                        bp.set(x, 1, z, AIR)


# ------------------------------------------------------------------ the temple
def temple_shell(S):
    """Six chamfered tiers, each a 3-block shell with a 3-block terrace slab; recessed panels between pilasters in
    the body of each face, a cornice of upside-down stairs, a battered base; the upper terrace (feet 56) railed by a
    parapet and walkable."""
    bp = S.bp
    for x in range(-43, 44):
        for z in range(-43, 44):
            m = mm(x, z)
            if m > 43.0:
                continue
            top, kc = col_top(m)
            ax, az = abs(x), abs(z)
            chamf = (ax + az + CH) / 2.0 > max(ax, az)
            u = z if ax >= az else x
            if top is None:
                # the battered base round tier 0 (three courses)
                for y in range(-3, 3):
                    if m <= 40 + (3 - y) * 0.75:
                        bp.set(x, y, z, tstone(x, y - 2, z))
                if m <= 41.0:
                    bp.set(x, 3, z, stair(tstair(x, 3, z), card(x if ax >= az else 0, z if az > ax else 0)))
                continue
            for y in range(-4, top + 1):
                hw = hw_at(y)
                face = hw - m
                roof = top - y
                if face < 0:
                    continue
                if not (face < 3 or roof < 3):
                    continue
                k = tier_k(y)
                yb = TH * k + 1
                body = yb + 3 <= y <= yb + 7
                if face < 1 and body and not chamf and k < 5:
                    b = round(u / 9.0)
                    if abs(u - 9 * b) <= 3:
                        continue            # recessed panel: the outer layer stays open
                spec = tstone(x, y, z)
                if face < 1 and y == yb + TH - 1 and roof >= 3:
                    spec = "chiseled_stone_bricks" if (u % 3 == 0) else "stone_bricks"   # string course
                if face < 1 and not chamf and k < 5 and (yb + 3 <= y <= yb + 7) and abs(u - 9 * round(u / 9.0)) >= 4:
                    spec = "mossy_stone_bricks" if hash3(x, y, z, 73) < 0.4 else "stone_bricks"  # pilaster
                bp.set(x, y, z, spec)
    # cornices: upside-down stairs one block out at the top of every tier
    for k in range(6):
        hw, y = HW[k], TH * (k + 1)
        for x in range(-hw - 1, hw + 2):
            for z in range(-hw - 1, hw + 2):
                m = mm(x, z)
                if hw < m <= hw + 1.0 and (abs(x) + abs(z) + CH) / 2.0 <= max(abs(x), abs(z)) + 0.01:
                    fc = card(x if abs(x) >= abs(z) else 0, z if abs(z) > abs(x) else 0)
                    bp.set(x, y, z, stair(tstair(x, y, z), OPP[fc], "top"))
    # the upper terrace (tier-4 roof, feet 56): parapet on its rim, walkway inside
    for x in range(-25, 26):
        for z in range(-25, 26):
            m = mm(x, z)
            if not (20 < m <= 24):
                continue
            if abs(x) <= 7 and z > 0:
                continue                     # the giant stair crosses here
            if abs(x) <= 2 and z < 0:
                continue                     # the north stele
            if m > 23:
                bp.set(x, TF, z, "mossy_stone_brick_wall" if hash01(x, z, 74) < 0.4 else "stone_brick_wall")
                continue
            for h in range(3):
                S.clear(x, TF + h, z)
            S.add_walk(x, z, TF)
            S.deck.add((x, z, TF))
    # the north stele across the terrace (the two halves of the terrace stay apart)
    for x in range(-2, 3):
        for z in range(-24, -20):
            for y in range(TF, TF + 6):
                S.solid(x, y, z, tstone(x, y + 20, z) if y < TF + 5 else "chiseled_stone_bricks")
    S.solid(0, TF + 3, -25, EYE)
    S.solid(0, TF + 4, -25, JADE)


def masks(S):
    """Jade masks in the panels flanking the axes of each face: brow, two glowing eyes, a nose and a fanged mouth."""
    for k in (1, 2, 3, 4):
        hw = HW[k]
        y = TH * k + 6
        for side in ("south", "north", "east", "west"):
            nx, nz = DIRS[side]
            for b in ((-1, 1) if side in ("south", "north") else (0,)):
                if side == "south" and b == 0:
                    continue
                u = 9 * b

                def at(du, v, layer, spec):
                    if nz:
                        x, z = u + du, nz * (hw - layer)
                    else:
                        x, z = nx * (hw - layer), u + du
                    S.solid(x, y + v, z, spec)
                for du in (-1, 0, 1):
                    at(du, 1, 0, JADE)
                    at(du, -1, 0, stair(JADE_S, OPP[side], "top") if du else JADE_C)
                at(-1, 0, 0, EYE)
                at(1, 0, 0, EYE)
                at(0, 0, 0, JADE_C)
                at(0, 2, 0, "chiseled_tuff_bricks")
                for du in (-2, 2):
                    at(du, 0, 0, "chiseled_tuff_bricks")


def giant_stair(S):
    """The giants' stair up the south face: 2-high steps (no player climbs it), balustrades a step higher, jade
    serpent heads at its foot, a sealed jade door on the summit edge at its head."""
    bp = S.bp
    for z in range(21, 55):
        top = SUMMIT - 2 * (z - 20)
        if top < -1:
            break
        m_top, _ = col_top(z) if z <= 40 else (None, None)
        base = (m_top + 1) if m_top is not None else -3
        for x in range(-7, 8):
            t = top + (1 if abs(x) >= 6 else 0)
            for y in range(base, t + 1):
                if abs(x) >= 6:
                    spec = tstone(x, y, z) if y < t else ("chiseled_stone_bricks" if z % 4 == 0 else "stone_bricks")
                elif y == t:
                    spec = "stone_bricks" if hash01(x, z, 75) < 0.7 else "mossy_stone_bricks"
                elif y == t - 1:
                    spec = "chiseled_stone_bricks" if x % 2 == 0 else "stone_bricks"
                else:
                    spec = tstone(x, y, z)
                bp.set(x, y, z, spec)
        S.busy.update((x, z) for x in range(-8, 9))
    # serpent heads at the foot of the balustrades (jaws open toward the court)
    for sx in (-1, 1):
        x0 = sx * 7
        for dx in (-1, 0, 1):
            for dz in range(0, 4):
                for y in range(0, 4):
                    x, z = x0 + dx, 53 + dz
                    if y == 3 and dz == 3:
                        continue
                    spec = JADE if (y + dz) % 3 else JADE_C
                    if dz == 3 and y == 1:
                        spec = stair(JADE_S, "north", "top")
                    S.solid(x, y, z, spec)
        S.solid(x0 - 1, 3, 55, EYE)
        S.solid(x0 + 1, 3, 55, EYE)
        S.solid(x0, 0, 57, "polished_andesite")
    # the sealed jade door at the head of the stair
    for x in range(-3, 4):
        for y in range(SF, SF + 6):
            z = 20
            if abs(x) == 3 or y >= SF + 4:
                S.solid(x, y, z, "chiseled_stone_bricks" if y < SF + 5 else "stone_bricks")
            else:
                S.solid(x, y, z, JADE if (x + y) % 2 else JADE_C)
    S.solid(0, SF + 2, 20, EYE)
    S.solid(0, SF + 5, 20, GOLD)


# ------------------------------------------------------------------ temple interior
def wall_in(x, y, z):
    return INNER.pick(x, y, z)


def floor_tile(x, z):
    return "polished_tuff" if (x + z) % 2 else "tuff_bricks"


def library(S):
    """The glyph library under the summit (feet 56): the west door from the terrace, stacks of shelves, glyph walls
    of chiseled tuff and jade, lecterns, a stele at the north end; the stair well down to the trap corridor."""
    bp = S.bp
    f = TF
    room(S, -17, -17, -5, 17, f, 8, wall_in, floor_tile)
    # the west door: a passage through the shell, a jade lintel and glowing eyes over it
    for x in range(-21, -16):
        for z in range(-1, 2):
            S.solid(x, f - 1, z, "chiseled_tuff_bricks" if x == -19 else "polished_tuff")
            for y in range(f, f + 4):
                S.clear(x, y, z, inner=x >= -18)
    for z in range(-2, 3):
        S.solid(-21, f + 4, z, JADE if abs(z) < 2 else "chiseled_stone_bricks")
        S.solid(-21, f + 5, z, "chiseled_stone_bricks")
    S.solid(-21, f + 6, -1, EYE)
    S.solid(-21, f + 6, 1, EYE)
    for y in range(f, f + 4):
        S.solid(-21, y, -2, "chiseled_tuff_bricks")
        S.solid(-21, y, 2, "chiseled_tuff_bricks")
    # glyph walls on the shell (west) and the partition (east)
    for z in range(-17, 18):
        for y in range(f + 1, f + 7):
            for x in (-18, -4):
                if bp.get(x, y, z) is None or (x, y, z) in S.keep:
                    continue
                g = hash3(x, y, z, 76)
                if (y - f) % 3 == 1:
                    spec = "chiseled_tuff_bricks" if g < 0.6 else JADE
                else:
                    spec = "chiseled_stone_bricks" if g < 0.3 else "tuff_bricks" if g < 0.8 else "chiseled_tuff"
                bp.set(x, y, z, spec)
    # shelf stacks (the aisle runs down the middle), reading tables, lecterns
    for z in list(range(-15, -1)) + list(range(5, 16)):
        if z in (-8, -7, 10, 11):
            continue
        for y in range(f, f + 3):
            S.solid(-8, y, z, "bookshelf" if (y + z) % 5 else "chiseled_bookshelf[facing=west,"
                    "slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=true,"
                    "slot_4_occupied=false,slot_5_occupied=true]")
        if z < 0:
            for y in range(f, f + 3):
                S.solid(-13, y, z, "bookshelf")
        S.solid(-8, f + 3, z, "jungle_slab[type=bottom,waterlogged=false]")
        if z < 0:
            S.solid(-13, f + 3, z, "jungle_slab[type=bottom,waterlogged=false]")
    for (x, z) in ((-11, -11), (-11, 0), (-6, -4), (-11, 14)):
        S.solid(x, f, z, "lectern[facing=west,has_book=false,powered=false]")
    for (x, z) in ((-6, 2), (-6, 12)):
        S.solid(x, f, z, "jungle_slab[type=top,waterlogged=false]")
        S.solid(x, f + 1, z, "candle[candles=3,lit=true,waterlogged=false]")
    # the stele at the north end
    for x in range(-12, -9):
        for y in range(f, f + 5):
            S.solid(x, y, -17, "chiseled_tuff" if (x + y) % 2 else "chiseled_tuff_bricks")
    S.solid(-11, f + 3, -17, EYE)
    S.solid(-11, f + 5, -17, GOLD)
    bp.chest(-15, f, -16, "south", loot=LOOT + "cc_library")
    S.keep.discard((-15, f, -16))
    for (x, z) in ((-10, -12), (-10, -2), (-10, 8), (-10, 15), (-15, -6), (-6, -13)):
        S.solid(x, f + 6, z, CHAIN_Y)
        S.solid(x, f + 5, z, LANT_H)
    bp.spawner(-6, f, 7, MOB_SKEL)
    S.keep.discard((-6, f, 7))
    # the stair well down to the trap corridor (west side, 11 steps down to the south), railed
    flight(S, -17, 13, "north", 11, 45, 3, "east", mat="tuff_brick", fill="tuff_bricks")
    for z in range(4, 14):
        S.solid(-14, f, z, "jungle_fence")
    S.solid(-14, f + 1, 8, LANT)


def grace_room(S):
    """The site of grace (feet 56) north of the cenote: the waystone, the iron door to the library (lever on this
    side), the narrow stair to the summit (compression), the doorway from the cenote ledge."""
    bp = S.bp
    f = TF
    room(S, -3, -17, 17, -10, f, 8, wall_in, floor_tile)
    # the doorway from the cenote's spiral ledge (north rim)
    for x in range(6, 9):
        for z in (-9, -8):
            S.solid(x, f - 1, z, "polished_tuff")
            for y in range(f, f + 4):
                S.clear(x, y, z, inner=True)
    for x in (5, 9):
        for y in range(f, f + 4):
            S.solid(x, y, -9, "chiseled_tuff_bricks")
    # the iron door to the library: opens from this side only
    S.solid(-4, f - 1, -12, "polished_tuff")
    bp.door(-4, f, -12, "west", wood="iron")
    S.solid(-4, f + 2, -12, "chiseled_tuff_bricks")
    S.solid(-4, f + 1, -11, "chiseled_tuff_bricks")
    S.solid(-3, f + 1, -11, "lever[face=wall,facing=east,powered=false]")
    S.keep.discard((-4, f, -12))
    S.keep.discard((-4, f + 1, -12))
    S.clear(-5, f, -12, inner=True)
    S.clear(-5, f + 1, -12, inner=True)
    # the waystone, a bench, candles, a jade brazier
    S.solid(1, f, -11, MOD["waystone"])
    for x in (3, 4):
        S.solid(x, f, -10, stair("jungle_stairs", "north"))
    S.solid(16, f, -11, "polished_tuff")
    S.solid(16, f + 1, -11, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    S.solid(-2, f, -14, "candle[candles=4,lit=true,waterlogged=false]")
    for x in (2, 10, 15):
        S.solid(x, f + 7, -12, CHAIN_Y)
        S.solid(x, f + 6, -12, LANT_H)
    # the narrow stair to the summit (3 wide, along the north wall, 11 up to the east)
    flight(S, 2, -17, "east", 11, f, 3, "south", mat="tuff_brick", fill="tuff_bricks", head=4)
    for x in range(13, 16):
        for z in range(-17, -14):
            S.solid(x, SUMMIT, z, "polished_tuff")
            for y in range(SF, SF + 4):
                S.clear(x, y, z, inner=True)
    for x in range(2, 13):
        S.solid(x, f + 4 + max(0, x - 6), -14, "tuff_brick_wall") if x < 6 else None


def trap_corridor(S):
    """The corridor of darts (feet 45) round the south, east and north of the cenote: dart traps, spike pits behind
    low walls, the bones of those who came before, windows onto the cenote."""
    bp = S.bp
    f = 45
    wall = wall_in

    def fl(x, z):
        return "mossy_stone_bricks" if hash01(x, z, 77) < 0.3 else "stone_bricks"
    room(S, -17, 14, 20, 16, f, 4, wall, fl)
    room(S, 18, -19, 20, 16, f, 4, wall, fl)
    room(S, -8, -19, 20, -17, f, 4, wall, fl)
    # dart traps: plates in the walk, dispensers in the outer walls
    for x in (-10, -2, 6, 13):
        dart_trap(S, x, f, 16, "north", 0, 1)
    for z in (9, 0, -9):
        dart_trap(S, 20, f, z, "west", 1, 0)
    for x in (12, 4):
        dart_trap(S, x, f, -19, "south", 0, -1)
    # spike pits behind low walls (south wall alcoves)
    for x0 in (-14, 2):
        for x in range(x0, x0 + 4):
            for z in (17, 18):
                S.clear(x, f - 1, z, inner=True)
                S.clear(x, f, z, inner=True)
                S.clear(x, f + 1, z, inner=True)
                S.clear(x, f + 2, z, inner=True)
                S.solid(x, f - 2, z, "pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]"
                        if (x + z) % 2 else "bone_block[axis=y]")
            S.solid(x, f, 17, "mossy_stone_brick_wall")
    # windows onto the cenote (south and east walls of the shaft side)
    for x in range(5, 10):
        for z in (11, 12, 13):
            for y in (f + 1, f + 2):
                if z == 11:
                    S.solid(x, y, z, "iron_bars")
                else:
                    S.clear(x, y, z, inner=True)
    for z in range(-1, 4):
        for x in (16, 17):
            for y in (f + 1, f + 2):
                if x == 16:
                    S.solid(x, y, z, "iron_bars")
                else:
                    S.clear(x, y, z, inner=True)
    # victims and their chest in a niche on the east side
    for (x, z) in ((-5, 15), (19, 5), (19, -14), (0, -18)):
        S.solid(x, f, z, "skeleton_skull[rotation=%d]" % (int(hash01(x, z, 78) * 16)))
    S.solid(1, f, 15, "bone_block[axis=x]")
    for x in range(21, 24):
        for z in (-4, -3, -2):
            for y in range(f, f + 3):
                S.clear(x, y, z, inner=True)
            S.solid(x, f - 1, z, "mossy_stone_bricks")
    bp.chest(23, f, -3, "west", loot=LOOT + "cc_traps")
    S.keep.discard((23, f, -3))
    S.solid(22, f, -4, "skeleton_skull[rotation=4]")
    S.solid(22, f + 2, -2, SOUL)
    for (x, z) in ((-12, 15), (0, 15), (11, 15), (19, 12), (19, -4), (19, -16), (8, -18), (-4, -18)):
        S.solid(x, f + 3, z, SOUL_H)
    bp.spawner(19, f, -10, MOB_ZOMBIE)
    S.keep.discard((19, f, -10))
    # the stair down toward the sanctum: west from the corridor's north end, then south
    flight(S, -19, -19, "east", 11, 34, 3, "south")
    landing(S, -22, -19, -20, -17, 34)
    flight(S, -22, -6, "north", 11, 23, 3, "east")
    landing(S, -22, -5, -20, -4, 23)
    S.solid(-21, 37, -19, SOUL_H)


def sanctum(S):
    """The jade-and-gold sanctum (feet 23): dark prismarine pillars with gold capitals, a jade idol on a gold dais,
    soul braziers, a window onto the cenote, the third waystone."""
    bp = S.bp
    f = 23

    def fl(x, z):
        if z == 5 and x > -22:
            return GOLD if x % 4 == 0 else "chiseled_tuff_bricks"
        return JADE if (x + z) % 2 else "polished_tuff"

    def wl(x, y, z):
        if y in (f + 4, f + 8):
            return "chiseled_tuff_bricks"
        return "prismarine_bricks" if (x + z) % 6 in (0, 1) and f < y < f + 8 else "tuff_bricks"
    room(S, -25, -4, -5, 14, f, 11, wl, fl, ceil=lambda x, y, z: "chiseled_tuff" if (x + z) % 3 else "tuff_bricks")
    for px in (-20, -11):
        for pz in (0, 9):
            for x in (px, px + 1):
                for z in (pz, pz + 1):
                    for y in range(f, f + 11):
                        S.solid(x, y, z, GOLD if y in (f, f + 10) else "dark_prismarine")
    # the idol on its dais (west end)
    for x in range(-25, -22):
        for z in range(2, 9):
            S.solid(x, f, z, GOLD if x == -23 else "chiseled_tuff_bricks")
    for z in range(3, 8):
        S.solid(-24, f + 1, z, "prismarine_bricks")
    for y in range(f + 2, f + 7):
        for z in range(4, 7):
            S.solid(-24, y, z, JADE if y % 2 else "prismarine_bricks")
    S.solid(-23, f + 5, 4, EYE)
    S.solid(-23, f + 5, 6, EYE)
    S.solid(-23, f + 4, 5, stair(JADE_S, "west", "top"))
    for z in range(3, 8):
        S.solid(-24, f + 7, z, GOLD if z % 2 else "raw_gold_block")
    bp.chest(-22, f, 2, "east", loot=LOOT + "cc_sanctum")
    bp.chest(-22, f, 8, "east", loot=LOOT + "cc_sanctum")
    S.keep.discard((-22, f, 2))
    S.keep.discard((-22, f, 8))
    for (x, z) in ((-15, -3), (-15, 13)):
        S.solid(x, f, z, GOLD)
        S.solid(x, f + 1, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((-15, 5), (-8, 0), (-8, 10), (-22, 5)):
        for y in range(f + 8, f + 11):
            S.solid(x, y, z, CHAIN_Y)
        S.solid(x, f + 7, z, SOUL_H)
    S.solid(-7, f, 12, MOD["waystone"])
    S.solid(-6, f, 9, "candle[candles=3,lit=true,waterlogged=false]")
    # the window onto the cenote (east wall)
    for z in range(0, 3):
        for y in range(f + 3, f + 6):
            S.clear(-4, y, z, inner=True)
            S.clear(-3, y, z, inner=True)
            S.solid(-2, y, z, "iron_bars")
    # down to the hall of offerings: a stair out of the south wall
    flight(S, -12, 25, "north", 11, 12, 3, "east")


def offering_hall(S):
    """The hall of offerings (feet 12): an altar heaped with pots and candles, jaguar heads in the wall niches."""
    bp = S.bp
    f = 12
    room(S, -27, 18, -9, 30, f, 8, wall_in, lambda x, z: "mossy_stone_bricks" if hash01(x, z, 79) < 0.35
         else "stone_bricks")
    for x in range(-20, -15):
        for z in range(22, 27):
            S.solid(x, f, z, "chiseled_stone_bricks" if (x + z) % 2 else "polished_andesite")
    for (x, z) in ((-19, 23), (-17, 25), (-19, 25), (-17, 23)):
        S.solid(x, f + 1, z, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    S.solid(-18, f + 1, 24, GOLD)
    S.solid(-18, f + 2, 24, "candle[candles=4,lit=true,waterlogged=false]")
    for z in (20, 24, 28):
        for x in (-27, -9):
            if x == -27 and z == 20:
                continue
            S.solid(x, f + 2, z, EYE)
            S.solid(x, f + 3, z, JADE)
    bp.chest(-26, f, 30, "north", loot=LOOT + "cc_offering")
    S.keep.discard((-26, f, 30))
    bp.spawner(-14, f, 20, MOB_SKEL)
    S.keep.discard((-14, f, 20))
    for (x, z) in ((-22, 21), (-14, 28), (-22, 28)):
        S.solid(x, f + 7, z, CHAIN_Y)
        S.solid(x, f + 6, z, LANT_H)
    # down to the crypt: from the west end, north
    flight(S, -27, 7, "south", 11, 1, 3, "east")


def crypt(S):
    """The root-choked crypt (feet 1): tombs in rows, roots of the trunks breaking through the vault, hanging roots,
    rooted earth, the passage east to the foot of the cenote."""
    bp = S.bp
    f = 1
    room(S, -30, -12, -8, 10, f, 7, lambda x, y, z: CRYPT.pick(x, y, z),
         lambda x, z: "rooted_dirt" if fbm(x, z, 4.0, 81) > 0.6 else "mossy_cobblestone" if hash01(x, z, 82) < 0.5
         else "cobbled_deepslate")
    # tombs
    for tx in (-27, -21, -15):
        for tz in (-10, -4):
            for x in range(tx, tx + 3):
                for z in range(tz, tz + 2):
                    S.solid(x, f, z, "polished_andesite")
                    S.solid(x, f + 1, z, "andesite_slab[type=bottom,waterlogged=false]")
            S.solid(tx + 1, f + 2, tz, "skeleton_skull[rotation=8]")
    # roots through the vault: thick tubes from the ceiling to the floor
    for (x0, z0, x1, z1) in ((-24, -12, -18, 2), (-12, -9, -16, 9), (-30, 4, -22, 9)):
        n = 14
        for i in range(n + 1):
            t = i / n
            x = round(x0 + (x1 - x0) * t)
            z = round(z0 + (z1 - z0) * t)
            y = round(f + 7 - 7 * t)
            for dx in (0, 1):
                for dy in (0, 1):
                    if (x + dx, y + dy, z) not in S.keep or True:
                        S.solid(x + dx, min(f + 6, y + dy), z, "jungle_wood[axis=y]" if dy else "mangrove_roots[waterlogged=false]")
    for x in range(-30, -7):
        for z in range(-12, 11):
            h = hash01(x, z, 83)
            if h < 0.12 and bp.get(x, f + 6, z) == AIR:
                S.solid(x, f + 6, z, "hanging_roots[waterlogged=false]")
            elif h > 0.94 and bp.get(x, f, z) == AIR:
                S.solid(x, f, z, "moss_carpet")
            elif 0.9 < h <= 0.92 and bp.get(x, f + 6, z) == AIR:
                S.solid(x, f + 6, z, "cobweb")
    # the chest behind a curtain of roots (north-west niche)
    for x in range(-30, -27):
        for y in range(f, f + 3):
            S.clear(x, y, -13, inner=True)
        S.solid(x, f - 1, -13, "mossy_cobblestone")
    bp.chest(-29, f, -13, "south", loot=LOOT + "cc_crypt")
    S.keep.discard((-29, f, -13))
    S.solid(-28, f + 2, -13, "hanging_roots[waterlogged=false]")
    bp.spawner(-24, f, 6, MOB_CRAWLER)
    S.keep.discard((-24, f, 6))
    bp.spawner(-12, f, -10, MOB_CAVE)
    S.keep.discard((-12, f, -10))
    for (x, z) in ((-19, 0), (-27, -7), (-11, 4)):
        S.solid(x, f + 5, z, SOUL_H)
    for (x, z) in ((-9, -1), (-9, 3)):
        S.solid(x, f, z, "candle[candles=2,lit=true,waterlogged=false]")
    # the passage to the cenote
    for x in range(-7, -1):
        for z in range(0, 3):
            S.solid(x, f - 1, z, "mossy_stone_bricks")
            for y in range(f, f + 4):
                S.clear(x, y, z, inner=True)
    S.solid(-4, f + 3, 1, SOUL_H)


def ledge_feet(theta_u):
    return 1.0 + SP_RISE * theta_u / SP_TOTAL


def cenote(S):
    """The flooded cenote: a round shaft (r 8) from the pool to the roof, a ledge spiralling 4.25 laps (55 up) from the
    crypt passage (west, feet 1) to the grace doorway (north, feet 56), railed on its inner edge with lamps on the
    rail, the waterfall falling through the summit grate into the pool, a secret grotto through an underwater
    tunnel."""
    bp = S.bp
    cx, cz = CE
    ri = int(CR) + 1
    # the shaft
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            r = math.hypot(x - cx, z - cz)
            if r > CR:
                continue
            for y in range(1, SUMMIT - 2):
                S.clear(x, y, z, inner=True)
            if r < LEDGE_IN:
                for y in range(-5, 1):
                    S.solid(x, y, z, WATER)
                    S.inner.add((x, y, z))
                h = hash01(x, z, 84)
                S.solid(x, -6, z, "sea_lantern" if h < 0.08 else "clay" if h < 0.4 else "gravel" if h < 0.6 else "sand")
            else:
                for y in range(-6, 0):
                    S.solid(x, y, z, ROCK.pick(x, y, z))
    # the ledge
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            r = math.hypot(x - cx, z - cz)
            if not (LEDGE_IN <= r <= CR):
                continue
            phi = math.atan2(z - cz, x - cx)
            base = (phi - math.pi) % (2 * math.pi)
            feet_list = []
            for n in range(5):
                tu = base + 2 * math.pi * n
                if tu <= SP_TOTAL + 0.02:
                    feet_list.append(ledge_feet(tu))
            if base > 2 * math.pi - 0.75:
                feet_list.append(1.0)           # the landing at the foot, before the first step
            rail = r < LEDGE_IN + 0.85
            for fe in feet_list:
                hh = math.floor(fe * 2) / 2
                n = math.floor(hh)
                half = hh - n > 0.25
                if rail:
                    top = n if half else n - 1
                    S.solid(x, top, z, "mossy_stone_bricks")
                    S.solid(x, top - 1, z, "stone_bricks")
                    S.solid(x, top + 1, z, "mossy_cobblestone_wall" if hash01(x, z, 85) < 0.5 else "cobblestone_wall")
                    continue
                if half:
                    S.solid(x, n, z, "mossy_stone_brick_slab[type=bottom,waterlogged=false]" if hash01(x, z, n) < 0.4
                            else "stone_brick_slab[type=bottom,waterlogged=false]")
                    S.solid(x, n - 1, z, "stone_bricks")
                    S.solid(x, n - 2, z, ROCK.pick(x, n - 2, z))
                    fy = n + 1
                else:
                    S.solid(x, n - 1, z, "mossy_stone_bricks" if hash01(x, z, n) < 0.35 else "stone_bricks")
                    S.solid(x, n - 2, z, ROCK.pick(x, n - 2, z))
                    fy = n
                if r > CR - 1.2 and hash01(x, z, n + 9) < 0.5:
                    S.solid(x, n - 3, z, ROCK.pick(x, n - 3, z))    # corbels under the outer edge
                for hy in range(fy, fy + 3):
                    if bp.get(x, hy, z) == AIR:
                        S.keep.add((x, hy, z))
    # lamps on the rail every so often
    for k in range(34):
        tu = 0.35 + k * SP_TOTAL / 34
        if tu > SP_TOTAL:
            break
        a = math.pi + tu
        x, z = round(cx + (LEDGE_IN + 0.3) * math.cos(a)), round(cz + (LEDGE_IN + 0.3) * math.sin(a))
        fe = ledge_feet(tu)
        y = math.floor(math.floor(fe * 2) / 2) + 1
        if bp.get(x, y, z) is not None and bp.get(x, y, z).endswith("_wall") and bp.get(x, y + 1, z) == AIR:
            S.solid(x, y + 1, z, LANT if k % 3 else SOUL)
    # the waterfall: a source under the summit grate, falling to the pool
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            for y in (SUMMIT - 2, SUMMIT - 1):
                S.clear(x, y, z, inner=True)
            S.solid(x, SUMMIT, z, "iron_bars")
    S.solid(cx, SUMMIT - 3, cz, WATER)
    for y in range(1, SUMMIT - 3):
        S.solid(cx, y, cz, FALL)
    # glowing lichen and moss on the shaft wall (applied after sealing, see seal())
    # the secret grotto: an underwater tunnel north from the pool, up through a hole into a dry chamber
    for z in range(-10, cz - 2):
        for y in (-5, -4):
            S.solid(cx, y, z, WATER)
            S.inner.add((cx, y, z))
    for x in range(cx - 3, cx + 4):
        for z in range(-15, -9):
            S.solid(x, -4, z, "mossy_cobblestone")
            S.solid(x, -3, z, "mossy_stone_bricks")
            for y in range(-2, 2):
                S.clear(x, y, z, inner=True)
    S.solid(cx, -3, -10, WATER)
    S.inner.add((cx, -3, -10))
    S.solid(cx, -4, -10, WATER)
    bp.chest(cx + 2, -2, -14, "south", loot=LOOT + "cc_cenote")
    S.keep.discard((cx + 2, -2, -14))
    S.solid(cx - 2, -2, -14, "skeleton_skull[rotation=6]")
    S.solid(cx - 3, -2, -12, SOUL)
    S.solid(cx + 3, -2, -11, "candle[candles=2,lit=true,waterlogged=false]")


SEE_THROUGH = ("hanging_roots", "vine", "lantern", "lichen", "carpet", "torch", "candle", "cobweb", "chain", "lever",
               "pressure_plate", "sign", "skull", "fence", "_wall", "pane", "bars", "door", "slab", "stairs",
               "dripstone", "fern", "grass", "spore", "water", "bubble", "campfire", "pot", "rail", "button")


def seal(S):
    """Every carved interior cell facing the unset void inside the temple (or the earth) gets a lining block."""
    bp = S.bp
    nb = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    cells = set(S.inner)
    for x in range(-HW[0], HW[0] + 1):
        for z in range(-HW[0], HW[0] + 1):
            m = mm(x, z)
            for y in range(1, SF):
                if m <= hw_at(y):
                    b = bp.get(x, y, z)
                    if b is not None and (b == AIR or any(k in b for k in SEE_THROUGH)):
                        cells.add((x, y, z))
    for (x, y, z) in cells:
        for dx, dy, dz in nb:
            q = (x + dx, y + dy, z + dz)
            if bp.get(*q) is None:
                if q[1] >= SF or (q[1] > 0 and mm(q[0], q[2]) > hw_at(q[1])):
                    continue                 # open air outside the temple (arena, terraces): leave it open
                if q[1] <= 0 and (x, y, z) not in S.inner:
                    continue
                cen = math.hypot(q[0] - CE[0], q[2] - CE[1]) <= CR + 1.5 and q[1] < SUMMIT
                bp.set(*q, ROCK.pick(*q) if (cen or q[1] <= 0) else INNER.pick(*q))
    # moss, lichen and vines on the cenote wall
    cx, cz = CE
    for x in range(cx - 10, cx + 11):
        for z in range(cz - 10, cz + 11):
            r = math.hypot(x - cx, z - cz)
            if not (CR - 0.6 < r <= CR):
                continue
            for y in range(2, SUMMIT - 3):
                if bp.get(x, y, z) != AIR or (x, y, z) in S.keep:
                    continue
                dx, dz = x - cx, z - cz
                side = card(dx, dz)
                wx, wz = DIRS[side]
                if empty(bp.get(x + wx, y, z + wz)):
                    continue
                h = hash3(x, y, z, 86)
                if h < 0.07:
                    props = {k: "false" for k in ("down", "east", "north", "south", "up", "west", "waterlogged")}
                    props[side] = "true"
                    S.set(x, y, z, ("minecraft:glow_lichen", props))
                elif h < 0.11 and y > 8:
                    for yy in range(y, max(1, y - 1 - int(h * 60)), -1):
                        if bp.get(x, yy, z) != AIR or (x, yy, z) in S.keep:
                            break
                        S.set(x, yy, z, f"vine[{side}=true]")


# ------------------------------------------------------------------ the summit
def summit(S):
    """The arena on the summit: an inlaid floor round the boss seal, the parapet, four braziers, the dais of the
    sun-disc (the vault in its west half, the stair-house in its east half, the mist at the stair-house door), the
    east gate (iron door, lever on the arena side) and its flight down to the east terrace."""
    bp = S.bp
    ax, az = AC
    for x in range(-20, 21):
        for z in range(-20, 21):
            m = mm(x, z)
            if m > 20:
                continue
            if bp.get(x, SUMMIT, z) in ("minecraft:iron_bars", "minecraft:tuff_brick_stairs") or (x, SUMMIT, z) in S.keep:
                continue                     # the cenote grate, the stairwell up from the site of grace
            r = math.hypot(x - ax, z - az)
            a = math.atan2(z - az, x - ax)
            if m > 19:
                S.solid(x, SF, z, "mossy_stone_brick_wall" if hash01(x, z, 87) < 0.35 else "stone_brick_wall")
                spec = tstone(x, SUMMIT, z)
            elif 5.5 <= r < 6.5:
                spec = GOLD if int((a + math.pi) * 12 / math.pi) % 2 == 0 else "chiseled_stone_bricks"
            elif 11.5 <= r < 12.5:
                spec = JADE
            elif r < 5.5 and (abs(x - ax) == 0 or abs(z - az) == 0):
                spec = "chiseled_tuff_bricks"
            elif r < 12 and abs(math.sin(a * 6)) < 0.18:
                spec = "polished_tuff"
            else:
                spec = "stone_bricks" if hash01(x, z, 88) < 0.6 else "mossy_stone_bricks"
            S.solid(x, SUMMIT, z, spec)
    bp.boss_seal(ax, SUMMIT, az, BOSS, 18)
    # braziers
    for (x, z) in ((-13, -7), (13, -7), (-13, 15), (13, 15)):
        S.solid(x, SF, z, "chiseled_stone_bricks")
        S.solid(x, SF + 1, z, GOLD)
        S.solid(x, SF + 2, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the dais: x -14..17, z -19..-13, y 67..71
    for x in range(-14, 18):
        for z in range(-19, -12):
            for y in range(SF, SF + 5):
                edge = x in (-14, 17) or z in (-19, -13) or y == SF + 4 or x in (4, 5)
                if edge:
                    if (x, y, z) not in S.keep:
                        S.solid(x, y, z, "chiseled_stone_bricks" if (y == SF + 4 and (x + z) % 3 == 0) else
                                tstone(x, y + 6, z))
                else:
                    S.clear(x, y, z, inner=True)
    for x in range(-15, 19):
        for z in (-20, -12):
            if mm(x, z) < 20:
                S.solid(x, SF + 4, z, stair(tstair(x, SF + 4, z), "north" if z < -15 else "south", "top")) \
                    if (x, SF + 4, z) not in S.keep else None
    # the vault (west half) behind sealed bars
    for x in range(-13, 4):
        for z in range(-18, -13):
            S.solid(x, SUMMIT, z, GOLD if (x + z) % 5 == 0 else "polished_tuff")
    for x in (-1, 0, 1):
        for y in range(SF, SF + 3):
            S.solid(x, y, -13, MOD["vault_bars"])
    bp.chest(-11, SF, -17, "south", loot=LOOT + "cc_vault")
    bp.chest(-5, SF, -18, "south", loot=LOOT + "cc_vault")
    bp.chest(1, SF, -18, "south", loot=LOOT + "cc_vault")
    for (x, z) in ((-11, -17), (-5, -18), (1, -18)):
        S.keep.discard((x, SF, z))
    for (x, z) in ((-8, -18), (-2, -18), (3, -17), (-13, -14)):
        S.solid(x, SF, z, GOLD if (x + z) % 2 else "raw_gold_block")
    S.solid(-8, SF + 1, -18, "candle[candles=4,lit=true,waterlogged=false]")
    for (x, z) in ((-9, -16), (-1, -16)):
        S.solid(x, SF + 3, z, SOUL_H)
    # the stair-house door (south wall) and the mist
    for x in range(13, 16):
        for y in range(SF, SF + 4):
            S.clear(x, y, -13, inner=True)
        S.solid(x, SUMMIT, -13, "polished_tuff")
    S.solid(14, SF + 3, -15, LANT_H)
    bp.mist(13, SF, -13, 15, SF + 3, -13)
    # the east gate: a doorframe in the parapet, an iron door whose lever is on the arena side
    for y in range(SF, SF + 4):
        S.solid(20, y, -1, "chiseled_stone_bricks")
        S.solid(20, y, 1, "chiseled_stone_bricks")
    S.solid(20, SF + 2, 0, "chiseled_stone_bricks")
    S.solid(20, SF + 3, 0, GOLD)
    S.solid(20, SUMMIT, 0, "polished_tuff")
    bp.door(20, SF, 0, "east", wood="iron")
    S.solid(19, SF + 1, -1, "lever[face=wall,facing=west,powered=false]")
    # the landing and the flight down the east terrace (south), solid underneath
    for x in range(21, 24):
        for z in range(-1, 2):
            for y in range(TF - 1, SUMMIT + 1):
                S.solid(x, y, z, tstone(x, y, z))
            for y in range(SF, SF + 3):
                S.clear(x, y, z)
            S.add_walk(x, z, SF)
    for x in range(21, 24):
        for k in range(1, 12):
            z = 13 - k
            y = TF + k - 1
            for yy in range(TF - 1, y):
                S.solid(x, yy, z, tstone(x, yy, z))
            S.solid(x, y, z, stair(tstair(x, y, z), "north"))
            for hh in range(1, 4):
                S.clear(x, y + hh, z)
            S.add_walk(x, z, TF + k)
            S.walk.pop((x, z), None) if False else None
    for z in range(2, 13):
        for x in range(21, 24):
            S.deck.discard((x, z, TF))
            lv = S.walk.get((x, z), [])
            if TF in lv:
                lv.remove(TF)
    # fallen pieces of the disc lying on the summit and the east terrace
    for (x, y, z, spec) in ((9, SF, -9, BRASS), (10, SF, -9, BRASS), (10, SF, -8, GEAR), (11, SF, -10, VERD),
                            (9, SF + 1, -9, stair(BRASS_STAIRS, "west")), (12, SF, -7, BRASS),
                            (16, SF, -9, GEAR), (15, SF, -10, BRASS), (22, TF, -14, BRASS), (23, TF, -13, VERD),
                            (22, TF + 1, -14, GEAR)):
        S.solid(x, y, z, spec)


def sun_disc(S):
    """The broken brass sun-disc on the dais: a ring of brass (r 9..15) with geared teeth and gold rays, a jade-and-gold
    face on spokes at its heart, two pylons; the upper right sector torn away (its pieces lie on the summit)."""
    cx, cy = 0, SF + 5 + 15
    for x in range(-17, 18):
        for y in range(SF + 5, cy + 18):
            r = math.hypot(x - cx, y - cy)
            a = math.degrees(math.atan2(y - cy, x - cx))
            broken = 22 <= a <= 78 or (78 < a <= 90 and r > 13)
            for z in (-17, -16):
                if 9 <= r <= 15 and not broken:
                    spec = COPPER if r < 10 else (VERD if hash3(x, y, z, 89) < 0.22 else BRASS)
                    S.solid(x, y, z, spec)
                elif 15 < r <= 16.6 and not broken and z == -16:
                    t = (a % 15)
                    if t < 6:
                        S.solid(x, y, z, GEAR if int(a // 15) % 2 else GOLD)
                elif r < 3.6:
                    S.solid(x, y, z, EYE if (abs(x) == 1 and y == cy + 1) else GOLD if r < 2.6 else JADE)
            # spokes
            if 3.6 <= r < 9 and not broken:
                for k in range(8):
                    sa = k * 45 + 22.5
                    if k in (1, 2):
                        continue
                    ra = math.radians(sa)
                    along = (x - cx) * math.cos(ra) + (y - cy) * math.sin(ra)
                    perp = abs(-(x - cx) * math.sin(ra) + (y - cy) * math.cos(ra))
                    if along > 0 and perp <= 0.75:
                        S.solid(x, y, -17, IRON)
                        S.solid(x, y, -16, "iron_bars" if r > 5 else IRON)
    # pylons
    for sx in (-1, 1):
        x = sx * 11
        for y in range(SF + 5, SF + 11):
            for z in (-17, -16):
                S.solid(x, y, z, IRON if y % 3 else BRASS)
        S.solid(x, SF + 5, -18, stair(BRASS_STAIRS, "south"))
        S.solid(x, SF + 5, -15, stair(BRASS_STAIRS, "north"))
    for x in range(-2, 3):
        S.solid(x, SF + 5, -15, stair(BRASS_STAIRS, "north"))
        S.solid(x, SF + 5, -18, stair(BRASS_STAIRS, "south"))


# ------------------------------------------------------------------ the trunks
TRUNKS = {
    # name: centre, top, newel (f0, k_end, c0) or None, doors {k: axis}, burls {k: (axis, kind)}, rings, seed
    "A": dict(c=(-50, 66), top=62, newel=(1, 13, 0), doors={0: "x", 8: "x", 13: "z"}, burls={10: ("x", "home")},
              seed=11),
    "B": dict(c=(-84, 0), top=70, newel=(1, 18, 0), doors={0: "x", 13: "z", 18: "x"},
              burls={4: ("z", "store"), 15: ("x", "weaver")}, seed=23),
    "C": dict(c=(-50, -66), top=66, newel=(40, 5, 2), doors={0: "z", 5: "x"}, burls={2: ("z", "home")}, seed=37),
    "D": dict(c=(84, 0), top=74, newel=None, seed=41),
    "E": dict(c=(50, 66), top=56, newel=(25, 5, 1), doors={0: "x", 5: "z"}, burls={2: ("x", "home")}, seed=53),
}
RINGS = [
    ("A", L1, 12, "ward"), ("A", L2, 8, "perch"),
    ("B", L2, 12, "market"), ("B", L3, 10, "high"),
    ("C", L2, 9, "shrine"), ("C", L3, 9, "watch"),
    ("D", L3, 9, "lift"),
    ("E", L1, 9, "ward_e"), ("E", L2, 10, "loft"),
]


def fins(T):
    """Angles of the buttress roots: between them the ground door (if any) passes."""
    s = T["seed"]
    door = T.get("door_ang", 0.0)
    return [door + math.radians(32 + 60 * i + 8 * (hash01(i, s, 3) - 0.5)) for i in range(6)]


def r_out(T, y, ang):
    s = T["seed"]
    rid = max(0.0, max(math.cos(ang - a) for a in T["_fins"])) ** 8
    flare = math.exp(-max(y, 0) / 6.5) * (4.5 + 9.5 * rid) if y < 30 else 0.0
    bark = (vnoise(ang * 5.0 + s, y * 0.22, 1.0, s) - 0.5) * 1.4
    taper = -0.5 * max(0, y) / T["top"]
    return max(7.35, R0 + flare + bark + taper)


def ring_r(T, L, ang, width):
    s = T["seed"] + L
    return R0 + width + (vnoise(ang * 3.0 + s, L * 0.1, 1.0, s) - 0.5) * 2.4


def newel_cells(cx, cz, f0, k_end, c0):
    """Square newel round a 3 x 3 core (as in great_aqueduct): 3 x 3 corner landings, flights of three steps (3 wide)
    on the sides, +3 per side. Returns [(x, z, feet, facing or None)] and {k: (sx, sz, feet)}."""
    cells, land = [], {}
    f = f0
    for k in range(k_end + 1):
        sx, sz = CORN[(c0 + k) % 4]
        for d1 in (2, 3, 4):
            for d2 in (2, 3, 4):
                cells.append((cx + sx * d1, cz + sz * d2, f, None))
        land[k] = (sx, sz, f)
        if k == k_end:
            break
        nx, nz = CORN[(c0 + k + 1) % 4]
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


def bark(T, x, y, z, d, ro, inner_face):
    h = hash3(x, y, z, T["seed"])
    if inner_face:
        return "stripped_jungle_log[axis=y]"
    if d > ro - 1.3:
        if y < 3 and h < 0.35:
            return "moss_block" if h < 0.15 else "rooted_dirt"
        if (z - T["c"][1]) < -2 and h < 0.22:
            return "moss_block"
        if h > 0.93:
            return "jungle_wood[axis=y]"
        return "jungle_log[axis=y]"
    return "jungle_wood[axis=y]"


def trunk(S, name):
    """One colossal hollow trunk: a flared base with buttress fins, a 2-3 block bark wall round a square 9 x 9 well,
    a ragged broken top open to the sky; its newel stair (or the elevator) inside; doors at the landings; burl
    dwellings bulging out of the bark; branches and leafy crowns near the top."""
    T = TRUNKS[name]
    bp = S.bp
    cx, cz = T["c"]
    T["door_ang"] = 0.0
    if name == "D":
        T["door_ang"] = math.pi / 2
    elif name == "B":
        T["door_ang"] = 0.0
    T["_fins"] = fins(T)
    top = T["top"]
    nw = T["newel"]
    floor_y = (nw[0] - 1) if nw else 0
    for y in range(-4, top + 5):
        rr = 26 if y < 14 else 11
        for x in range(cx - rr, cx + rr + 1):
            for z in range(cz - rr, cz + rr + 1):
                dx, dz = x - cx, z - cz
                d = math.hypot(dx, dz)
                if d > rr:
                    continue
                ang = math.atan2(dz, dx)
                ro = r_out(T, y, ang)
                if d > ro:
                    continue
                rag = top + round(4 * vnoise(ang * 4.0, 0.5, 1.0, T["seed"] + 7))
                if y > rag:
                    continue
                well = abs(dx) <= 4 and abs(dz) <= 4
                if well and y >= floor_y:
                    if y == floor_y:
                        S.set(x, y, z, "stripped_jungle_wood[axis=y]" if nw else "jungle_planks")
                    else:
                        S.clear(x, y, z)
                    continue
                if well:
                    S.set(x, y, z, "stripped_jungle_wood[axis=y]")
                    continue
                inner_face = max(abs(dx), abs(dz)) == 5 and d < 6.5
                S.set(x, y, z, bark(T, x, y, z, d, ro, inner_face))
        S.busy.update((x, z) for x in range(cx - 24, cx + 25) for z in range(cz - 24, cz + 25)
                      if math.hypot(x - cx, z - cz) <= 24)
    if nw:
        f0, k_end, c0 = nw
        cells, land = newel_cells(cx, cz, f0, k_end, c0)
        for (x, z, f, fc) in cells:
            S.solid(x, f - 1, z, stair("jungle_stairs", fc) if fc else
                    ("jungle_planks" if (x + z) % 2 else "stripped_jungle_wood[axis=y]"))
            if f - f0 <= 6:
                for y in range(f0 - 1, f - 1):
                    S.solid(x, y, z, "jungle_planks")
        for (x, z, f, fc) in cells:
            for y in range(f, f + 3):
                if bp.get(x, y, z) == AIR:
                    S.keep.add((x, y, z))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(f0 - 1, top + 1):
                    S.solid(cx + dx, y, cz + dz, "stripped_jungle_log[axis=y]" if (dx or dz) else
                            ("jungle_log[axis=y]" if y % 7 else "chiseled_tuff_bricks"))
        for k, (sx, sz, f) in land.items():
            if k % 2 == 1 and k not in T["doors"] and k not in T["burls"]:
                S.solid(cx + sx * 4, f, cz + sz * 4, LANT)
        T["_land"] = land
        for k, axis in T["doors"].items():
            sx, sz, f = land[k]
            trunk_door(S, T, sx, sz, f, axis)
        for k, (axis, kind) in T["burls"].items():
            sx, sz, f = land[k]
            burl(S, T, sx, sz, f, axis, kind)
    crown(S, T)
    roots(S, T)
    cocoa(S, T)


def trunk_door(S, T, sx, sz, f, axis, width=3):
    """A doorway from a newel landing out through the bark (3 wide, 4 high), floored with planks."""
    cx, cz = T["c"]
    for i in range(5, 30):
        for j in (2, 3, 4):
            x, z = (cx + sx * i, cz + sz * j) if axis == "x" else (cx + sx * j, cz + sz * i)
            d = math.hypot(x - cx, z - cz)
            ang = math.atan2(z - cz, x - cx)
            if d > r_out(T, f, ang) + 0.5 and d > r_out(T, f + 3, ang) + 0.5:
                if bp_is_free(S, x, f - 1, z):
                    break
            S.solid(x, f - 1, z, "jungle_planks" if i % 3 else "stripped_jungle_log[axis=%s]" % axis)
            for y in range(f, f + 4):
                S.clear(x, y, z)
        else:
            continue
    # a lintel of stripped wood over the outer mouth
    return


def bp_is_free(S, x, y, z):
    return S.get(x, y, z) is None or (x, y + 1, z) in S.keep


def burl(S, T, sx, sz, f, axis, kind):
    """A dwelling in a burl of the bark beside a landing: a rounded swelling of wood with a room 5 wide inside."""
    bp = S.bp
    cx, cz = T["c"]

    def loc(i, j):
        return (cx + sx * i, cz + sz * j) if axis == "x" else (cx + sx * j, cz + sz * i)
    # the swelling
    ccx, ccz = loc(9, 3)
    for x in range(ccx - 8, ccx + 9):
        for z in range(ccz - 8, ccz + 9):
            for y in range(f - 4, f + 8):
                e = ((x - ccx) / 6.0) ** 2 + ((z - ccz) / 6.0) ** 2 + ((y - f - 1.5) / 5.0) ** 2
                if e > 1.0 or (x, y, z) in S.keep:
                    continue
                if empty(bp.get(x, y, z)):
                    h = hash3(x, y, z, 91)
                    S.set(x, y, z, "jungle_wood[axis=y]" if h < 0.8 else "moss_block" if y > f + 4 else
                          "jungle_log[axis=y]")
    # the room
    cells = [loc(i, j) for i in range(5, 12) for j in range(1, 6)]
    for (x, z) in cells:
        S.solid(x, f - 1, z, "jungle_planks" if (x + z) % 2 else "stripped_jungle_wood[axis=y]")
        for y in range(f, f + 4):
            S.clear(x, y, z)
    # a window out, a lantern
    wx, wz = loc(12, 3)
    for y in (f + 1, f + 2):
        S.solid(wx, y, wz, "glass_pane")
        ox, oz = loc(13, 3)
        if empty(bp.get(ox, y, oz)) and (ox, y, oz) not in S.keep:
            pass
    lx, lz = loc(8, 3)
    S.solid(lx, f + 3, lz, LANT_H)
    # furnishing
    a, b = loc(11, 1), loc(11, 5)
    if kind == "home":
        bx, bz = loc(10, 1)
        hx, hz = loc(11, 1)
        bfc = card(hx - bx, hz - bz)
        S.solid(bx, f, bz, f"red_bed[facing={bfc},part=foot,occupied=false]")
        S.solid(hx, f, hz, f"red_bed[facing={bfc},part=head,occupied=false]")
        c = loc(11, 5)
        S.bp.chest(c[0], f, c[1], card(-(c[0] - cx), -(c[1] - cz)), loot=LOOT + "cc_dwelling")
        S.keep.discard((c[0], f, c[1]))
        t = loc(9, 5)
        S.solid(t[0], f, t[1], "crafting_table")
        p = loc(7, 5)
        S.solid(p[0], f, p[1], "potted_fern")
    elif kind == "store":
        for (i, j) in ((10, 1), (11, 1), (11, 2), (10, 5), (11, 5), (11, 4)):
            q = loc(i, j)
            S.bp.barrel(q[0], f, q[1], "up")
            S.keep.discard((q[0], f, q[1]))
        q = loc(11, 1)
        S.bp.barrel(q[0], f + 1, q[1], "up")
        S.keep.discard((q[0], f + 1, q[1]))
    else:
        q = loc(11, 1)
        S.solid(q[0], f, q[1], "loom[facing=%s]" % card(cx - q[0], cz - q[1]))
        for (i, j) in ((11, 4), (11, 5)):
            q = loc(i, j)
            S.solid(q[0], f, q[1], "white_wool" if j == 5 else "lime_wool")
        q = loc(9, 1)
        S.bp.chest(q[0], f, q[1], card(cx - q[0], cz - q[1]), loot=LOOT + "cc_dwelling")
        S.keep.discard((q[0], f, q[1]))


def crown(S, T):
    """Three to five branches out of the upper trunk (child radius ~0.7), leaf clusters at their tips, vines."""
    bp = S.bp
    cx, cz = T["c"]
    s = T["seed"]
    top = T["top"]
    nb = 4 + int(hash01(s, 1, 5) * 2)
    for i in range(nb):
        a = 2 * math.pi * (i / nb + 0.13 * hash01(i, s, 6))
        y0 = top - 10 + int(6 * hash01(i, s, 7))
        L = 14 + 6 * hash01(i, s, 8)
        rise = 6 + 5 * hash01(i, s, 9)
        pts = []
        for k in range(int(L) + 1):
            t = k / L
            d = R0 - 1 + t * L
            pts.append((cx + d * math.cos(a), y0 + rise * t * (2 - t), cz + d * math.sin(a), 2.0 - 1.3 * t))
        for (px, py, pz, pr) in pts:
            ri = int(math.ceil(pr))
            for x in range(int(px) - ri, int(px) + ri + 2):
                for y in range(int(py) - ri, int(py) + ri + 2):
                    for z in range(int(pz) - ri, int(pz) + ri + 2):
                        if (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= pr * pr + 0.3:
                            if empty(bp.get(x, y, z)) and (x, y, z) not in S.keep:
                                S.set(x, y, z, "jungle_wood[axis=y]")
        ex, ey, ez, _ = pts[-1]
        leaf_blob(S, ex, ey + 1, ez, 5.5 + 2 * hash01(i, s, 10), 2.8, s + i)


def leaf_blob(S, cx, cy, cz, rx, ry, seed, vines=True):
    bp = S.bp
    for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
        for z in range(int(cz - rx) - 1, int(cz + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                e = ((x - cx) / rx) ** 2 + ((z - cz) / rx) ** 2 + ((y - cy) / ry) ** 2
                lump = 0.22 * math.sin(x * 0.9 + seed) * math.cos(z * 0.7 - y * 0.5)
                if e <= 1.0 + lump and empty(bp.get(x, y, z)) and (x, y, z) not in S.keep:
                    if hash3(x, y, z, seed) < 0.92:
                        S.set(x, y, z, LEAVES)
    if not vines:
        return
    for x in range(int(cx - rx), int(cx + rx) + 1):
        for z in range(int(cz - rx), int(cz + rx) + 1):
            if hash01(x, z, seed + 3) > 0.12:
                continue
            ybot = None
            for y in range(int(cy + ry) + 1, int(cy - ry) - 2, -1):
                if bp.get(x, y, z) == "minecraft:jungle_leaves":
                    ybot = y
            if ybot is None:
                continue
            for side, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
                vx, vz = x - dx, z - dz
                if bp.get(vx, ybot, vz) == "minecraft:jungle_leaves":
                    continue
                n = 2 + int(hash01(x, z, seed + 4) * 6)
                for k in range(n):
                    y = ybot - k
                    if not empty(bp.get(vx, y, vz)) or (vx, y, vz) in S.keep:
                        break
                    S.set(vx, y, vz, f"vine[{side}=true]")
                break


def roots(S, T):
    """Surface roots radiating from the fins, diving into the ground (radius 2.2 to 0.7)."""
    bp = S.bp
    cx, cz = T["c"]
    for i, a in enumerate(T["_fins"]):
        L = 15 + 7 * hash01(i, T["seed"], 11)
        n = int(L * 1.5)
        for k in range(n + 1):
            t = k / n
            d = 14 + t * L
            wob = 1.6 * math.sin(t * 5 + i)
            px = cx + d * math.cos(a) + wob * -math.sin(a)
            pz = cz + d * math.sin(a) + wob * math.cos(a)
            py = 3.0 - 5.0 * t
            pr = 2.2 - 1.5 * t
            ri = int(math.ceil(pr))
            for x in range(int(px) - ri, int(px) + ri + 2):
                for z in range(int(pz) - ri, int(pz) + ri + 2):
                    for y in range(int(py) - ri, int(py) + ri + 2):
                        if (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= pr * pr + 0.2:
                            if (x, y, z) in S.keep or (x, z) in S.paths and y >= 0:
                                continue
                            if y >= 0 or empty(bp.get(x, y, z)) or bp.get(x, y, z) in (
                                    "minecraft:dirt", "minecraft:grass_block", "minecraft:podzol",
                                    "minecraft:moss_block", "minecraft:coarse_dirt", "minecraft:rooted_dirt"):
                                S.set(x, y, z, "jungle_wood[axis=y]" if hash3(x, y, z, 12) < 0.85 else
                                      "moss_block")


def cocoa(S, T):
    bp = S.bp
    cx, cz = T["c"]
    for k in range(30):
        a = 2 * math.pi * hash01(k, T["seed"], 13)
        y = 4 + int(hash01(k, T["seed"], 14) * (T["top"] - 10))
        fc = card(math.cos(a), math.sin(a))
        dx, dz = DIRS[fc]
        for d in range(6, 16):
            x, z = cx + dx * d, cz + dz * d
            if empty(bp.get(x, y, z)) and bp.get(x - dx, y, z - dz) == "minecraft:jungle_log" \
                    and (x, y, z) not in S.keep:
                S.set(x, y, z, f"cocoa[age=2,facing={OPP[fc]}]")
                break


# ------------------------------------------------------------------ the brass elevator (trunk D)
def elevator(S):
    """The Lift Trunk: a bubble-column lift in a brass and glass casing from the ground to the landing (feet 55), a
    drop shaft from the landing into a pool on the ground floor; the ground door (iron) opens from inside only."""
    bp = S.bp
    T = TRUNKS["D"]
    cx, cz = T["c"]
    top = L3 - 1
    # the landing floor (y 54) across the well, with the shaft openings
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            S.solid(x, top, z, BRASS if (x + z) % 4 == 0 else "jungle_planks")
    # the lift: column at (cx - 3, cz - 3), casing round it, open toward +x at the foot (signs hold the water)
    lx, lz = cx - 3, cz - 3
    S.solid(lx, -1, lz, "soul_sand")
    for y in range(0, top + 1):
        S.solid(lx, y, lz, "bubble_column[drag=false]")
    for y in range(0, top):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                x, z = lx + dx, lz + dz
                if (dx, dz) == (1, 0) and y in (1, 2):
                    continue
                front = dx == 1 or dz == 1
                corner = dx != 0 and dz != 0
                if corner:
                    spec = BRASS if y % 6 else GEAR
                elif front:
                    spec = "glass" if y % 6 else BRASS
                else:
                    spec = COPPER if y % 6 else BRASS
                S.solid(x, y, z, spec)
    S.solid(lx + 1, 1, lz, "spruce_sign[rotation=12,waterlogged=false]")
    S.solid(lx + 1, 2, lz, "spruce_wall_sign[facing=east,waterlogged=false]")
    S.solid(lx + 1, 0, lz, BRASS)
    # the drop shaft: 2 x 2 at the opposite corner, a pool below the floor
    for x in (cx + 3, cx + 4):
        for z in (cz + 3, cz + 4):
            S.clear(x, top, z)
            for y in range(-4, 1):
                S.solid(x, y, z, WATER)
            S.solid(x, -5, z, "clay")
    for x in range(cx + 2, cx + 6):
        for z in range(cz + 2, cz + 6):
            for y in range(-5, 1):
                if (x, z) not in ((cx + 3, cz + 3), (cx + 3, cz + 4), (cx + 4, cz + 3), (cx + 4, cz + 4)):
                    if y < 0 or x > cx + 4 or z > cz + 4:
                        S.solid(x, y, z, "smooth_stone" if y > -2 else "stone")
    for x in range(cx + 2, cx + 5):
        if x != cx + 2:
            S.solid(x, L3, cz + 2, IRON + "_wall" if False else "jungle_fence")
    for z in range(cz + 3, cz + 5):
        S.solid(cx + 2, L3, z, "jungle_fence")
    # brass furniture of the winch room at the top and the hall at the foot
    for (x, z) in ((cx - 4, cz + 4), (cx + 4, cz - 4)):
        S.solid(x, L3, z, GEAR)
        S.solid(x, L3 + 1, z, GAUGE)
    for y in range(1, top):
        S.solid(cx + 4, y, cz - 4, PIPES if y % 5 else BRASS)
    S.solid(cx, L3 + 3, cz, "chain_command_block" if False else LANT_H)
    S.solid(cx, L3 + 4, cz, CHAIN_Y)
    for y in range(L3 + 5, L3 + 8):
        S.solid(cx, y, cz, IRON if y == L3 + 7 else CHAIN_Y)
    for x in range(cx - 4, cx + 5):
        S.solid(x, L3 + 7, cz, IRON)
    for (x, z) in ((cx + 1, cz - 4), (cx - 4, cz + 1)):
        S.solid(x, 4, z, "lantern[hanging=false,waterlogged=false]") if empty(bp.get(x, 4, z)) else None
    S.solid(cx, 1, cz + 4, "lantern[hanging=false,waterlogged=false]")
    S.solid(cx - 4, 1, cz + 4, GEAR)
    bp.spawner(cx - 1, 1, cz + 1, MOB_CLOCK)
    S.keep.discard((cx - 1, 1, cz + 1))
    for y in (12, 24, 36, 48):
        S.solid(cx + 4, y, cz + 1, "lantern[hanging=false,waterlogged=false]") if False else None
    # the landing door (west, onto the D-L3 ring) and the ground door (south, iron, lever inside)
    for i in range(5, 14):
        for j in (-1, 0, 1):
            x, z = cx - i, cz + j
            ang = math.atan2(z - cz, x - cx)
            if math.hypot(x - cx, z - cz) > r_out(T, L3, ang) + 0.6:
                break
            S.solid(x, top, z, "jungle_planks")
            for y in range(L3, L3 + 4):
                S.clear(x, y, z)
    for i in range(5, 30):
        x, z = cx, cz + i
        ang = math.atan2(z - cz, x - cx)
        if math.hypot(x - cx, z - cz) > r_out(T, 0, ang) + 0.6 and math.hypot(x - cx, z - cz) > r_out(T, 3, ang) + .6:
            break
        for j in (-1, 0, 1):
            S.solid(cx + j, 0, z, "jungle_planks" if i > 5 else BRASS)
            for y in range(1, 5):
                S.clear(cx + j, y, z)
    for j in (-1, 1):
        for y in range(1, 4):
            S.solid(cx + j, y, cz + 5, BRASS)
    for j in (-1, 0, 1):
        S.solid(cx + j, 4, cz + 5, BRASS)
        S.solid(cx + j, 3, cz + 5, BRASS) if j else None
    bp.door(cx, 1, cz + 5, "south", wood="iron")
    S.keep.discard((cx, 1, cz + 5))
    S.keep.discard((cx, 2, cz + 5))
    S.solid(cx - 1, 2, cz + 4, "lever[face=wall,facing=north,powered=false]")
    S.solid(cx - 1, 2, cz + 5, BRASS)


# ------------------------------------------------------------------ platforms, huts, stalls
def ring_platform(S, name, L, width, kind):
    """A ring deck round a trunk at feet L, its edge wandering, radial joists and knee braces underneath."""
    T = TRUNKS[name]
    bp = S.bp
    cx, cz = T["c"]
    cells = []
    rmax = int(R0 + width + 3)
    for x in range(cx - rmax, cx + rmax + 1):
        for z in range(cz - rmax, cz + rmax + 1):
            dx, dz = x - cx, z - cz
            d = math.hypot(dx, dz)
            ang = math.atan2(dz, dx)
            if d > ring_r(T, L, ang, width) or d <= r_out(T, L - 1, ang):
                continue
            if any(d <= r_out(T, y, ang) for y in range(L, L + 3)):
                continue
            if not empty(bp.get(x, L - 1, z)) and (x, L - 1, z) not in S.keep:
                b = bp.get(x, L - 1, z)
                if not b.startswith("minecraft:jungle_planks") and "stripped" not in b:
                    pass
            cells.append((x, z))
    for (x, z) in cells:
        S.solid(x, L - 1, z, DECK.pick(x, L - 1, z))
        for h in range(3):
            if empty(bp.get(x, L + h, z)) or (x, L + h, z) in S.keep:
                S.clear(x, L + h, z)
        S.add_walk(x, z, L)
        S.deck.add((x, z, L))
    # joists and knee braces
    for i in range(12):
        a = 2 * math.pi * i / 12 + 0.1 * T["seed"]
        rr = ring_r(T, L, a, width) - 0.6
        for k in range(int(R0), int(rr) + 1):
            x, z = round(cx + k * math.cos(a)), round(cz + k * math.sin(a))
            if empty(bp.get(x, L - 2, z)):
                S.set(x, L - 2, z, "stripped_jungle_log[axis=%s]" % ("x" if abs(math.cos(a)) > 0.7 else
                                                                  "z" if abs(math.sin(a)) > 0.7 else "y"))
        if i % 2 == 0:
            n = 12
            for k in range(n + 1):
                t = k / n
                d = R0 + 0.5 + t * (rr - R0 - 1.5)
                y = round(L - 11 + 9 * t)
                x, z = round(cx + d * math.cos(a)), round(cz + d * math.sin(a))
                if empty(bp.get(x, y, z)) and (x, y, z) not in S.keep:
                    S.set(x, y, z, "jungle_wood[axis=y]")
    T.setdefault("_rings", {})[L] = (width, set(cells))
    return cells


def hut(S, cx, cz, f, w, d, door, kind, seed, loot=None):
    """A bamboo hut on a deck: log corners, plank-and-bamboo walls, a steep thatch-like roof, a door toward the
    trunk, windows, furniture by kind."""
    bp = S.bp
    x0, x1 = cx - w // 2, cx + w // 2
    z0, z1 = cz - d // 2, cz + d // 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            S.solid(x, f - 1, z, "bamboo_mosaic" if not edge else "stripped_jungle_log[axis=y]")
            for y in range(f, f + 4):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    S.solid(x, y, z, "jungle_log[axis=y]" if corner else
                            "stripped_jungle_wood[axis=y]" if y == f + 3 else HUTWALL.pick(x, y, z))
                else:
                    S.clear(x, y, z)
            S.walk.pop((x, z), None)
    dx, dz = DIRS[door]
    if dz:
        px, pz = cx, (z1 if dz > 0 else z0)
    else:
        px, pz = (x1 if dx > 0 else x0), cz
    bp.door(px, f, pz, door, wood="jungle")
    S.keep.discard((px, f, pz))
    S.keep.discard((px, f + 1, pz))
    S.clear(px + dx, f, pz + dz)
    S.clear(px + dx, f + 1, pz + dz)
    # windows on the sides
    for (wx, wz) in ((x0, cz), (x1, cz), (cx, z0), (cx, z1)):
        if (wx, wz) != (px, pz):
            S.solid(wx, f + 1, wz, "bamboo_fence" if hash01(wx, wz, seed) < 0.5 else "glass_pane")
    bp.pyramid_roof(x0 - 1, z0 - 1, x1 + 1, z1 + 1, f + 4, "bamboo_mosaic_stairs", overhang=0,
                    cap="bamboo_block[axis=y]")
    S.solid(cx, f + 3, cz, LANT_H)
    # furniture
    inside = [(x, z) for x in range(x0 + 1, x1) for z in range(z0 + 1, z1) if (x, z) != (px - dx, pz - dz)]
    back = [(x, z) for (x, z) in inside if (x - cx) * dx + (z - cz) * dz <= -(min(w, d) // 2 - 1)]
    if not back:
        back = inside
    if kind == "home":
        pair = next(((p, q) for p in back for q in back if abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1), None)
        if pair:
            (ax, az), (bx, bz) = pair
            fc = card(bx - ax, bz - az)
            S.solid(ax, f, az, f"lime_bed[facing={fc},part=foot,occupied=false]")
            S.solid(bx, f, bz, f"lime_bed[facing={fc},part=head,occupied=false]")
        if len(back) >= 3 and (not pair or back[-1] not in pair):
            bp.barrel(back[-1][0], f, back[-1][1], "up")
            S.keep.discard((back[-1][0], f, back[-1][1]))
    elif kind == "store":
        for (x, z) in back:
            bp.barrel(x, f, z, "up")
            S.keep.discard((x, f, z))
    elif kind == "shrine":
        for (x, z) in back:
            S.solid(x, f, z, "potted_red_tulip" if hash01(x, z, seed) < 0.3 else "candle[candles=3,lit=true,"
                    "waterlogged=false]" if hash01(x, z, seed) < 0.6 else "potted_fern")
    elif kind == "loom":
        S.solid(back[0][0], f, back[0][1], f"loom[facing={door}]")
        if len(back) > 1:
            S.solid(back[1][0], f, back[1][1], "lime_wool")
    if loot:
        free = [c for c in back if bp.get(c[0], f, c[1]) == AIR] or [c for c in inside if bp.get(c[0], f, c[1]) == AIR]
        q = free[len(free) // 2] if free else (back[len(back) // 2] if back else inside[0])
        bp.chest(q[0], f, q[1], door, loot=LOOT + loot)
        S.keep.discard((q[0], f, q[1]))
    for (x, z) in inside:
        S.keep.discard((x, f, z)) if bp.get(x, f, z) != AIR else None


def stall(S, x0, z0, f, color, goods):
    """A market stall: four posts, a wool awning, a counter of barrels and slabs with goods on it."""
    bp = S.bp
    for (x, z) in ((x0, z0), (x0 + 2, z0), (x0, z0 + 2), (x0 + 2, z0 + 2)):
        for y in range(f, f + 3):
            S.solid(x, y, z, "bamboo_fence")
    for x in range(x0, x0 + 3):
        for z in range(z0, z0 + 3):
            S.solid(x, f + 3, z, f"{color}_wool" if (x + z) % 2 else "white_wool")
    S.solid(x0 + 1, f, z0, "barrel[facing=up,open=false]")
    S.solid(x0 + 1, f, z0 + 2, "jungle_slab[type=top,waterlogged=false]")
    S.solid(x0 + 1, f + 1, z0 + 2, goods)


def ring_angles(T, L, avoid, n, width):
    """Hut slots round a ring: n angles evenly spread, skipping those within 26 degrees of `avoid`."""
    out = []
    s = T["seed"] + L
    for i in range(n * 3):
        a = 2 * math.pi * (i / (n * 3)) + 0.3 * hash01(s, i, 15)
        if any(abs((a - b + math.pi) % (2 * math.pi) - math.pi) < math.radians(28) for b in avoid):
            continue
        if any(abs((a - b + math.pi) % (2 * math.pi) - math.pi) < 2 * math.pi / n * 0.9 for b in out):
            continue
        out.append(a)
        if len(out) >= n:
            break
    return out


def districts(S, avoid):
    """The huts, stalls and fixtures of each ring platform. `avoid`: {(name, L): [angles of bridges]}."""
    bp = S.bp
    for (name, L, width, kind) in RINGS:
        T = TRUNKS[name]
        cx, cz = T["c"]
        cells = set(T["_rings"][L][1])
        av = list(avoid.get((name, L), []))
        land = T.get("_land", {})
        for k, axis in T.get("doors", {}).items():
            sx, sz, f = land[k]
            if f == L:
                av.append(math.atan2(sz * 3 if axis == "x" else sz, sx if axis == "x" else sx * 3))
        rad = R0 + width - 3.5
        if kind in ("ward", "ward_e", "high", "loft", "shrine", "watch", "perch", "lift"):
            n = {"ward": 4, "ward_e": 2, "high": 3, "loft": 1, "shrine": 1, "watch": 1, "perch": 1, "lift": 1}[kind]
            angs = ring_angles(T, L, av, n, width)
            for i, a in enumerate(angs):
                hx, hz = round(cx + rad * math.cos(a)), round(cz + rad * math.sin(a))
                w, d = (5, 5) if kind != "loft" else (7, 7)
                hk = "home"
                loot = None
                if kind == "ward":
                    hk = ("home", "store", "home", "loom")[i % 4]
                    loot = "cc_ward" if i in (0, 2) else None
                elif kind == "ward_e":
                    hk = "home"
                    loot = "cc_ward" if i == 0 else None
                elif kind == "high":
                    hk = ("home", "store", "home")[i]
                    loot = "cc_highward" if i == 0 else None
                    if i == 0:
                        w, d = 7, 5
                elif kind == "loft":
                    hk, loot = "shrine", "cc_loft"
                elif kind == "shrine":
                    hk, loot = "shrine", "cc_shrine"
                elif kind == "watch":
                    hk, loot = "store", "cc_highward"
                elif kind == "perch":
                    hk = "home"
                elif kind == "lift":
                    hk = "store"
                foot = [(x, z) for x in range(hx - w // 2 - 1, hx + w // 2 + 2)
                        for z in range(hz - d // 2 - 1, hz + d // 2 + 2)]
                if not all(c in cells for c in foot):
                    continue
                door = card(cx - hx, cz - hz)
                hut(S, hx, hz, L, w, d, door, hk, T["seed"] + i, loot=loot)
        if kind == "market":
            angs = ring_angles(T, L, av, 7, width)
            colors = ("orange", "lime", "yellow", "red", "cyan", "magenta", "brown")
            goods = ("melon", "pumpkin", "hay_block[axis=y]", "jungle_log[axis=y]", "bamboo_block[axis=y]",
                     "cocoa[age=2,facing=north]" if False else "dried_kelp_block", "moss_block")
            for i, a in enumerate(angs):
                hx, hz = round(cx + rad * math.cos(a)), round(cz + rad * math.sin(a))
                foot = [(x, z) for x in range(hx - 2, hx + 3) for z in range(hz - 2, hz + 3)]
                if not all(c in cells for c in foot):
                    continue
                if i in (2, 5):
                    hut(S, hx, hz, L, 5, 5, card(cx - hx, cz - hz), "store" if i == 2 else "loom", T["seed"] + i,
                        loot="cc_market" if i == 2 else None)
                else:
                    stall(S, hx - 1, hz - 1, L, colors[i], goods[i])
            # the waystone and the totem on the inner walk
            a = angs[0] + math.radians(18) if angs else 0.0
            wx, wz = round(cx + (R0 + 2.5) * math.cos(a)), round(cz + (R0 + 2.5) * math.sin(a))
            if (wx, wz) in cells:
                S.solid(wx, L, wz, MOD["waystone"])
        # lamp posts on the deck edge
        for i in range(10):
            a = 2 * math.pi * (i + 0.5) / 10
            if any(abs((a - b + math.pi) % (2 * math.pi) - math.pi) < math.radians(16) for b in av):
                continue
            rr = ring_r(T, L, a, width) - 1.2
            x, z = round(cx + rr * math.cos(a)), round(cz + rr * math.sin(a))
            if (x, z) in cells and bp.get(x, L, z) == AIR and bp.get(x, L + 1, z) == AIR:
                S.solid(x, L, z, "bamboo_fence")
                S.solid(x, L + 1, z, LANT)
                S.walk.pop((x, z), None)
    # spawners on the canopy
    for (name, L, a, mob) in (("A", L1, 3.6, MOB_SPIDER), ("B", L3, 0.9, MOB_SKEL), ("C", L2, 4.4, MOB_SPIDER),
                              ("E", L2, 2.2, MOB_CAVE)):
        T = TRUNKS[name]
        cx, cz = T["c"]
        cells = T["_rings"][L][1]
        for dd in (R0 + 3.5, R0 + 4.5, R0 + 2.5):
            x, z = round(cx + dd * math.cos(a)), round(cz + dd * math.sin(a))
            if (x, z) in cells and bp.get(x, L, z) == AIR and bp.get(x, L + 1, z) == AIR:
                bp.spawner(x, L, z, mob)
                S.keep.discard((x, L, z))
                S.walk.pop((x, z), None)
                break


# ------------------------------------------------------------------ the gate
def gate(S):
    """The ruined gate: two stone towers 11 x 11 joined by a corbel arch 13 wide, a deck on top (feet 25) where the
    rope bridges of A-L1 and E-L1 land; the west tower holds a newel stair up to the deck, the east tower a tall
    jaguar shrine."""
    bp = S.bp
    z0, z1 = GATE_Z
    zc = (z0 + z1) // 2
    for x in range(-17, 18):
        for z in range(z0, z1 + 1):
            tower = abs(x) >= 7
            for y in range(-3, 24):
                if tower:
                    lx = x - (-12 if x < 0 else 12)
                    lz = z - zc
                    if max(abs(lx), abs(lz)) <= 4 and y >= 0:
                        continue
                    S.solid(x, y, z, tstone(x, y, z))
                else:
                    open_h = 15 if abs(x) <= 6 - max(0, 0) else 0
                    cor = 11 + (6 - abs(x))
                    if y < 1:
                        S.solid(x, y, z, "mossy_stone_bricks" if hash01(x, z, 92) < 0.4 else "stone_bricks")
                    elif y <= min(cor, 15):
                        S.clear(x, y, z)
                    else:
                        S.solid(x, y, z, tstone(x, y, z))
            S.solid(x, 23, z, "mossy_stone_bricks" if hash01(x, z, 93) < 0.3 else "stone_bricks")
            for h in range(3):
                S.clear(x, 24 + h, z) if empty(bp.get(x, 24 + h, z)) else None
            if not (x < -6 and max(abs(x + 12), abs(z - zc)) <= 4):
                S.add_walk(x, z, L1)
                S.deck.add((x, z, L1))
    # corbel string courses on the arch faces, masks over the arch
    for x in range(-7, 8):
        for z in (z0, z1):
            S.solid(x, 16, z, stair(tstair(x, 16, z), "north" if z == z0 else "south", "top")) if abs(x) <= 6 else None
    for z in (z0, z1):
        nz = -1 if z == z0 else 1
        for dx in (-1, 0, 1):
            S.solid(dx, 19, z, JADE)
            S.solid(dx, 17, z, stair(JADE_S, "north" if nz < 0 else "south", "top") if dx else JADE_C)
        S.solid(-1, 18, z, EYE)
        S.solid(1, 18, z, EYE)
        S.solid(0, 18, z, JADE_C)
    # the west tower: newel stair from the passage (feet 1) to the deck (feet 25), a stair house over it
    cells, land = newel_cells(-12, zc, 1, 8, 0)
    for x in range(-16, -7):
        for z in range(zc - 4, zc + 5):
            S.solid(x, 0, z, "stone_bricks")
            for y in range(1, 29):
                S.clear(x, y, z)
    for (x, z, f, fc) in cells:
        S.solid(x, f - 1, z, stair("stone_brick_stairs", fc) if fc else "polished_andesite")
        if f - 1 <= 6:
            for y in range(0, f - 1):
                S.solid(x, y, z, "stone_bricks")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for y in range(0, 28):
                S.solid(-12 + dx, y, zc + dz, "chiseled_stone_bricks" if y % 6 == 0 else "stone_bricks")
    for x in range(-17, -6):
        for z in range(zc - 5, zc + 6):
            if max(abs(x + 12), abs(z - zc)) == 5:
                for y in range(24, 29):
                    S.solid(x, y, z, tstone(x, y, z))
                S.walk.pop((x, z), None)
    bp.pyramid_roof(-18, zc - 6, -6, zc + 6, 29, "mossy_stone_brick_stairs", overhang=0, cap="chiseled_stone_bricks")
    for k, (sx, sz, f) in land.items():
        if k in (2, 5):
            S.solid(-12 + sx * 4, f, zc + sz * 4, LANT)
    # doors: k0 (NE corner) east into the arch passage; k8 (NE) east onto the deck
    for (k, y0) in ((0, 1), (8, 25)):
        sx, sz, f = land[k]
        for x in (-7, -6) if k == 0 else (-7,):
            for z in range(zc + sz * 2 - 0, zc + sz * 4 + (1 if sz > 0 else 0), 1 if sz > 0 else 1):
                pass
        zs = sorted((zc + sz * 2, zc + sz * 4))
        for z in range(zs[0], zs[1] + 1):
            for x in ((-7,) if k == 8 else (-7, -6)):
                S.solid(x, f - 1, z, "polished_andesite")
                for y in range(f, f + 4):
                    S.clear(x, y, z)
    # the east tower: the jaguar shrine (feet 1, 22 high), door into the arch passage
    for x in range(8, 17):
        for z in range(zc - 4, zc + 5):
            S.solid(x, 0, z, "chiseled_stone_bricks" if (x + z) % 4 == 0 else "polished_andesite")
            for y in range(1, 23):
                S.clear(x, y, z, inner=False)
    for z in range(zc - 1, zc + 2):
        for y in range(1, 5):
            S.clear(7, y, z)
            S.clear(6, y, z)
        S.solid(7, 0, z, "polished_andesite")
    # the statue: a seated jaguar of jade
    for x in range(13, 16):
        for z in range(zc - 1, zc + 2):
            for y in range(1, 4):
                S.solid(x, y, z, JADE if y < 3 else JADE_C)
    for z in range(zc - 1, zc + 2):
        for y in range(4, 7):
            S.solid(14, y, z, JADE)
    S.solid(13, 6, zc - 1, EYE)
    S.solid(13, 6, zc + 1, EYE)
    S.solid(13, 5, zc, stair(JADE_S, "west", "top"))
    S.solid(15, 7, zc - 1, JADE_C)
    S.solid(15, 7, zc + 1, JADE_C)
    bp.chest(10, 1, zc + 4, "north", loot=LOOT + "cc_gate")
    S.keep.discard((10, 1, zc + 4))
    for (x, z) in ((9, zc - 3), (9, zc + 3)):
        S.solid(x, 1, z, "candle[candles=3,lit=true,waterlogged=false]")
    for y in range(13, 23):
        S.solid(12, y, zc, CHAIN_Y)
    S.solid(12, 12, zc, LANT_H)
    bp.spawner(10, 1, zc - 3, MOB_SKEL)
    S.keep.discard((10, 1, zc - 3))
    # the deck: a little shrine and the zip-line pulley; lamps
    for (x, z) in ((-4, z0 + 1), (4, z0 + 1), (-4, z1 - 1), (4, z1 - 1)):
        S.solid(x, 24, z, "bamboo_fence")
        S.solid(x, 25, z, LANT)
        S.walk.pop((x, z), None)
    S.busy.update((x, z) for x in range(-20, 21) for z in range(z0 - 3, z1 + 4))


# ------------------------------------------------------------------ bridges and zip-lines
def ring_edge(name, L, toward, inset=1.6):
    T = TRUNKS[name]
    cx, cz = T["c"]
    a = math.atan2(toward[1] - cz, toward[0] - cx)
    width = T["_rings"][L][0]
    r = ring_r(T, L, a, width) - inset
    return (cx + r * math.cos(a), cz + r * math.sin(a)), a


def bridge(S, p0, p1, f0, f1, sag, half=1.15):
    """A sagging rope bridge from p0 (feet f0) to p1 (feet f1): plank slabs at half-block steps, fence rails with rope
    posts every six blocks, lanterns every twelve; it never overwrites a deck it starts or ends on."""
    bp = S.bp
    (ax, az), (bx, bz) = p0, p1
    L = math.hypot(bx - ax, bz - az)
    ux, uz = (bx - ax) / L, (bz - az) / L
    cells = {}
    for x in range(int(min(ax, bx)) - 4, int(max(ax, bx)) + 5):
        for z in range(int(min(az, bz)) - 4, int(max(az, bz)) + 5):
            t = ((x - ax) * ux + (z - az) * uz) / L
            if t < -0.02 or t > 1.02:
                continue
            d = abs(-(x - ax) * uz + (z - az) * ux)
            if d <= half:
                cells[(x, z)] = ("deck", min(1, max(0, t)))
            elif d <= half + 1.05:
                cells[(x, z)] = ("rail", min(1, max(0, t)))
    for (x, z), (kind, t) in sorted(cells.items()):
        h = f0 + (f1 - f0) * t - sag * math.sin(math.pi * t)
        if any(abs(h - lv) < 1.01 and (x, z, lv) in S.deck for lv in S.levels(x, z)):
            continue
        hh = math.floor(h * 2) / 2
        n = math.floor(hh)
        half_step = hh - n > 0.25
        wood = "jungle" if hash01(x, z, 94) < 0.6 else "bamboo"
        if half_step:
            S.solid(x, n, z, f"{wood}_slab[type=bottom,waterlogged=false]")
            fy = n + 1
        else:
            S.solid(x, n - 1, z, f"{wood}_slab[type=top,waterlogged=false]")
            fy = n
        if kind == "rail":
            if (x, fy, z) in S.keep:
                continue
            S.solid(x, fy, z, FENCE)
            step = round(t * L)
            if step % 6 == 0 and 0 < step < L - 2:
                if empty(bp.get(x, fy + 1, z)) and (x, fy + 1, z) not in S.keep:
                    S.set(x, fy + 1, z, FENCE)
                    if step % 12 == 0 and empty(bp.get(x, fy + 2, z)):
                        S.set(x, fy + 2, z, LANT)
        else:
            for k in range(3):
                S.clear(x, fy + k, z)
            S.add_walk(x, z, hh)
            S.busy.add((x, z))
    # rope posts at both ends
    nx, nz = -uz, ux
    for (px, pz, f) in ((ax + ux * 0.5, az + uz * 0.5, f0), (bx - ux * 0.5, bz - uz * 0.5, f1)):
        for s in (-1, 1):
            x, z = round(px + s * nx * (half + 0.9)), round(pz + s * nz * (half + 0.9))
            fl = math.floor(f)
            if (x, fl, z) in S.keep or (x, fl + 1, z) in S.keep:
                continue
            for y in range(fl, fl + 3):
                S.solid(x, y, z, "stripped_jungle_log[axis=y]")
            S.solid(x, fl + 3, z, LANT)


def zipline(S, p0, p1):
    """A brass zip-line: a pulley frame at each end (brass posts, a grindstone wheel, gear plates) and the cable of
    chain between them, high over the jungle."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(z1 - z0), abs(y1 - y0)))
    axis = "x" if abs(x1 - x0) >= abs(z1 - z0) else "z"
    for i in range(1, n):
        t = i / n
        sag = 3.0 * math.sin(math.pi * t)
        x, y, z = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t - sag), round(z0 + (z1 - z0) * t)
        if empty(S.get(x, y, z)) and (x, y, z) not in S.keep:
            S.set(x, y, z, f"iron_chain[axis={axis},waterlogged=false]")
    for (x, y, z) in (p0, p1):
        S.solid(x, y, z, f"grindstone[face=floor,facing={'north' if axis == 'x' else 'east'}]")
        S.solid(x, y + 1, z, BRASS)
        ox, oz = (0, 1) if axis == "x" else (1, 0)
        for s in (-1, 1):
            px, pz = x + s * ox, z + s * oz
            for yy in range(y - 4, y + 2):
                if (px, yy, pz) not in S.keep:
                    S.solid(px, yy, pz, BRASS if yy == y + 1 else IRON)
            S.solid(px, y, pz, GEAR)
        S.solid(x, y - 1, z, IRON)
        for yy in range(y - 4, y - 1):
            if (x, yy, z) not in S.keep and empty(S.get(x, yy, z)):
                S.solid(x, yy, z, CHAIN_Y)


def links(S):
    """All the rope bridges and zip-lines; returns the bridge angles per ring (no huts there)."""
    avoid = {}

    def note(name, L, a):
        avoid.setdefault((name, L), []).append(a)
    # gate deck <-> A-L1 and E-L1
    for name, sx in (("A", -1), ("E", 1)):
        g = (sx * 17.5, 75.5)
        p, a = ring_edge(name, L1, g)
        note(name, L1, a)
        bridge(S, (sx * 16.5, 75.5), p, L1, L1, 1.0)
    # A-L2 <-> B-L2, B-L3 <-> C-L3, B-L2 <-> C-L2
    for (n0, n1, L, sag) in (("A", "B", L2, 3.0), ("B", "C", L3, 3.0), ("B", "C", L2, 2.5)):
        c1 = TRUNKS[n1]["c"]
        c0 = TRUNKS[n0]["c"]
        p0, a0 = ring_edge(n0, L, c1)
        p1, a1 = ring_edge(n1, L, c0)
        note(n0, L, a0)
        note(n1, L, a1)
        if (n0, n1, L) == ("B", "C", L2):
            # offset sideways so the two B-C bridges do not hang one over the other
            off = 9
            dx, dz = c1[0] - c0[0], c1[1] - c0[1]
            ln = math.hypot(dx, dz)
            ox, oz = -dz / ln * off, dx / ln * off
            p0, a0 = ring_edge(n0, L, (c1[0] + ox * 2, c1[1] + oz * 2))
            p1, a1 = ring_edge(n1, L, (c0[0] + ox * 2, c0[1] + oz * 2))
            note(n0, L, a0)
            note(n1, L, a1)
        bridge(S, p0, p1, L, L, sag)
    # C-L3 -> the temple's west terrace (NW corner), D-L3 -> the east terrace (south of the gate flight)
    for (name, tgt) in (("C", (-22.0, -14.0)), ("D", (22.0, 17.0))):
        p, a = ring_edge(name, L3, tgt)
        note(name, L3, a)
        bridge(S, p, tgt, L3, TF, 3.5)
    # zip-lines (decorative pulleys): B-L3 -> gate deck, D-L3 -> E-L2, C-L3 -> B-L2 market
    B, C, D, E = (TRUNKS[k]["c"] for k in "BCDE")
    zl = []
    for (name, L, tgt, endp) in (("B", L3, (0, 76), (-2, L1 + 3, 73)),
                                 ("D", L3, E, None), ("C", L3, (B[0], B[1] - 30), None)):
        p, a = ring_edge(name, L, tgt, inset=3.2)
        zl.append((name, L, p, a, tgt, endp))
    for (name, L, p, a, tgt, endp) in zl:
        start = (round(p[0]), L + 3, round(p[1]))
        if endp is None:
            if name == "D":
                q, b = ring_edge("E", L2, TRUNKS["D"]["c"], inset=3.2)
                endp = (round(q[0]), L2 + 3, round(q[1]))
                note("E", L2, b)
            else:
                q, b = ring_edge("B", L2, TRUNKS["C"]["c"], inset=3.0)
                q = (q[0] + 4, q[1])
                endp = (round(q[0]), L2 + 3, round(q[1]))
        note(name, L, a)
        zl_cells = (start, endp)
        zipline(S, *zl_cells)
    return avoid


def rails(S):
    """Fences on the cells beside every outdoor walkway where the next cell is not walkway at about the same height."""
    n = 0
    for (x, z), lv in sorted(S.walk.items()):
        for f in lv:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, z + dz)
                if any(abs(g - f) <= 1.01 for g in S.levels(*q)):
                    continue
                fy = int(f) if f == int(f) else math.floor(f) + 1
                c1, c0 = (q[0], fy, q[1]), (q[0], fy - 1, q[1])
                if c1 in S.keep or c0 in S.keep or not empty(S.get(*c1)):
                    continue
                if not empty(S.get(*c0)):
                    b0 = S.get(*c0)
                    if not (b0.endswith("_slab") or b0.endswith("planks") or "jungle_wood" in b0 or "log" in b0
                            or b0.endswith("bricks") or b0.endswith("mosaic")):
                        continue
                else:
                    S.set(*c0, "stripped_jungle_wood[axis=y]")
                S.set(*c1, FENCE)
                n += 1
                if n % 11 == 0 and empty(S.get(q[0], fy + 1, q[1])) and (q[0], fy + 1, q[1]) not in S.keep:
                    S.set(q[0], fy + 1, q[1], LANT)
    return n


# ------------------------------------------------------------------ roots over the temple
def temple_roots(S):
    """Strangler roots from the west and east trunks crawl across the court and up over the lower tiers of the temple
    (they end tapered on the terraces), and curtains of roots and vines hang down the faces from the ledges."""
    bp = S.bp
    paths = [
        [(-72, 1, -10), (-46, 1, -14), (-41, 6, -16), (-38, 12, -18), (-35, 14, -22), (-34, 23, -24), (-31, 25, -27)],
        [(-62, 1, 30), (-44, 1, 22), (-40, 8, 20), (-37, 13, 16), (-34, 18, 14), (-33, 24, 10)],
        [(-66, 1, -50), (-46, 1, -42), (-41, 7, -39), (-37, 13, -36), (-34, 17, -33)],
        [(64, 1, 14), (44, 1, 10), (40, 7, 8), (37, 13, 4), (34, 20, 2), (33, 24, -2), (30, 27, -6)],
        [(30, 1, -60), (22, 1, -44), (18, 7, -41), (15, 13, -37), (12, 19, -34), (8, 24, -32)],
        # from the south-west and south-east trunks over the front corners (they stop below the second ledge)
        [(-40, 1, 58), (-34, 1, 44), (-30, 6, 41), (-27, 12, 37), (-24, 18, 34), (-21, 23, 33), (-17, 27, 32)],
        [(40, 1, 56), (33, 1, 44), (30, 7, 40), (28, 13, 36), (26, 19, 33), (22, 24, 31), (18, 27, 30)],
        [(44, 1, -20), (41, 7, -22), (38, 13, -24), (35, 19, -25), (33, 24, -27)],
    ]
    for i, pts in enumerate(paths):
        tot = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        acc = 0.0
        for a, b in zip(pts, pts[1:]):
            seg = math.dist(a, b)
            m = max(1, int(seg * 2))
            for j in range(m + 1):
                t = j / m
                p = [a[c] + (b[c] - a[c]) * t for c in range(3)]
                s = (acc + seg * t) / tot
                pr = 2.4 - 1.8 * s
                p[0] += 1.2 * math.sin(s * 9 + i)
                p[2] += 1.2 * math.cos(s * 7 + i)
                ri = int(math.ceil(pr))
                for x in range(int(p[0]) - ri, int(p[0]) + ri + 2):
                    for y in range(int(p[1]) - ri, int(p[1]) + ri + 2):
                        for z in range(int(p[2]) - ri, int(p[2]) + ri + 2):
                            if (x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 > pr * pr + 0.2:
                                continue
                            if (x, y, z) in S.keep or (y >= 1 and (x, z) in S.paths):
                                continue
                            S.set(x, y, z, "jungle_wood[axis=y]" if hash3(x, y, z, 95) < 0.8 else "mangrove_roots"
                                  "[waterlogged=false]" if y > 0 else "rooted_dirt")
            acc += seg
    # curtains of roots and vines hanging from the terrace edges down the faces
    for k in range(1, 5):
        hw = HW[k]
        ytop = TH * k
        for side in ("north", "east", "west", "south"):
            nx, nz = DIRS[side]
            for u in range(-hw + 4, hw - 3):
                if side == "south" and abs(u) <= 9:
                    continue
                h = hash01(u, k * 7 + len(side), 96)
                if h > 0.5 - 0.25 * vnoise(u, k * 13 + len(side), 7.0, 99):
                    continue
                x, z = (u, nz * (hw + 1)) if nz else (nx * (hw + 1), u)
                if mm(x, z) > HW[k - 1]:
                    continue
                n = 4 + int(hash01(u, k, 97) * 7)
                for j in range(n):
                    y = ytop + TH - 1 - j
                    wx, wz = x - nx, z - nz
                    if not empty(bp.get(x, y, z)) or (x, y, z) in S.keep or empty(bp.get(wx, y, wz)):
                        break
                    if h < 0.13:
                        S.set(x, y, z, "jungle_wood[axis=y]" if j < n - 1 else "hanging_roots[waterlogged=false]")
                    else:
                        S.set(x, y, z, f"vine[{OPP[side]}=true]")
    # the lower ledges (outside, unwalked): moss and rooted earth in the joints, ferns, leaf tufts on the corners
    for k in range(0, 4):
        y = TH * (k + 1)
        for x in range(-HW[k], HW[k] + 1):
            for z in range(-HW[k], HW[k] + 1):
                m = mm(x, z)
                if not (HW[k + 1] < m <= HW[k] - 1) or (abs(x) <= 9 and z > 0):
                    continue
                if not empty(bp.get(x, y + 1, z)) or (x, y + 1, z) in S.keep or empty(bp.get(x, y, z)):
                    continue
                g = fbm(x + k * 17, z, 5.0, 101 + k)
                if g < 0.45:
                    continue
                S.set(x, y, z, "moss_block" if g < 0.62 else "rooted_dirt")
                h = hash3(x, y, z, 102)
                if g > 0.62 and h < 0.18 and m < HW[k] - 1.5:
                    S.set(x, y + 1, z, LEAVES)
                    if h < 0.07 and empty(bp.get(x, y + 2, z)):
                        S.set(x, y + 2, z, LEAVES)
                elif h < 0.35:
                    S.set(x, y + 1, z, "moss_carpet" if h < 0.2 else "fern")


# ------------------------------------------------------------------ approach, camp, jungle
def jungle_tree(S, x, z, h, seed):
    """A big jungle tree: 2 x 2 trunk, a few side boughs, a broad crown, vines and cocoa."""
    bp = S.bp
    for y in range(1, h + 1):
        for dx in (0, 1):
            for dz in (0, 1):
                S.set(x + dx, y, z + dz, "jungle_log[axis=y]")
    for dx, dz in ((-1, 0), (2, 1), (0, -1), (1, 2)):
        if hash01(x + dx, z + dz, seed) < 0.6:
            S.set(x + dx, 1, z + dz, "jungle_wood[axis=y]")
    for i in range(3):
        a = 2 * math.pi * (i / 3 + hash01(i, seed, 1) * 0.2)
        by = h - 6 + i * 2
        for k in range(1, 6):
            S.set(round(x + 0.5 + k * math.cos(a)), by + k // 2, round(z + 0.5 + k * math.sin(a)), "jungle_wood[axis=y]")
        leaf_blob(S, x + 0.5 + 6 * math.cos(a), by + 4, z + 0.5 + 6 * math.sin(a), 3.6, 2.0, seed + i, vines=True)
    leaf_blob(S, x + 0.5, h + 1, z + 0.5, 6.5, 2.8, seed, vines=True)
    for k in range(5):
        fc = ("north", "south", "east", "west")[k % 4]
        dx, dz = DIRS[fc]
        y = 3 + int(hash01(k, seed, 3) * (h - 6))
        px = x + (1 if dx > 0 else 0) + dx
        pz = z + (1 if dz > 0 else 0) + dz
        if dx == 0:
            px = x + (k % 2)
        if dz == 0:
            pz = z + (k % 2)
        if empty(bp.get(px, y, pz)):
            S.set(px, y, pz, f"cocoa[age=2,facing={OPP[fc]}]")


def bush(S, x, z, seed):
    S.set(x, 1, z, "jungle_log[axis=y]")
    leaf_blob(S, x, 2, z, 2.2, 1.4, seed, vines=False)


def camp(S):
    """The explorers' camp east of the track before the gate: the first waystone, a tent, a theodolite of brass,
    crates and a fire."""
    bp = S.bp
    cx, cz = 15, 97
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            if math.hypot(x - cx, z - cz) < 6.5:
                bp.set(x, 0, z, "coarse_dirt" if hash01(x, z, 98) < 0.5 else "packed_mud")
                for y in range(1, 4):
                    if not empty(bp.get(x, y, z)):
                        bp.set(x, y, z, AIR)
                S.busy.add((x, z))
    S.solid(cx - 3, 1, cz - 2, MOD["waystone"])
    # the tent
    for z in range(cz, cz + 5):
        for (x, y) in ((cx + 1, 1), (cx + 2, 2), (cx + 3, 3), (cx + 4, 2), (cx + 5, 1)):
            S.solid(x, y, z, "green_wool" if (x + z) % 3 else "lime_wool")
        S.solid(cx + 3, 1, z, AIR)
        S.solid(cx + 3, 2, z, AIR)
    for y in range(1, 4):
        S.solid(cx + 3, y, cz + 5, "jungle_fence")
    bp.chest(cx + 3, 1, cz + 4, "north", loot=LOOT + "cc_camp")
    S.solid(cx + 2, 1, cz + 3, "brown_bed[facing=south,part=foot,occupied=false]")
    S.solid(cx + 2, 1, cz + 4, "brown_bed[facing=south,part=head,occupied=false]")
    # fire, crates, theodolite
    S.solid(cx - 1, 1, cz + 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((cx - 5, cz + 2), (cx - 5, cz + 3), (cx - 4, cz + 3)):
        bp.barrel(x, 1, z, "up")
    S.solid(cx - 5, 2, cz + 3, "barrel[facing=up,open=false]")
    for y in (1, 2):
        S.solid(cx - 2, y, cz - 4, IRON + "_wall" if False else "iron_bars")
    S.solid(cx - 2, 3, cz - 4, BRASS)
    S.solid(cx - 2, 4, cz - 4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    S.solid(cx - 1, 1, cz - 3, stair("jungle_stairs", "west"))


def jungle(S):
    """Big jungle trees along the approach (they hide the temple until the gate) and round the edges, bushes, ferns,
    bamboo and flowers on the jungle floor."""
    bp = S.bp
    placed = []
    spots = []
    for i in range(900):
        x = int(-104 + 208 * hash01(i, 1, 99))
        z = int(-92 + 204 * hash01(i, 2, 99))
        spots.append((x, z, i))
    for (x, z, i) in spots:
        if len(placed) >= 34:
            break
        if mm(x, z) <= 52 or abs(x) < 6 and z > 40:
            continue
        if any((x + dx, z + dz) in S.busy or (x + dx, z + dz) in S.paths for dx in range(-7, 9, 2)
               for dz in range(-7, 9, 2)):
            continue
        if any(abs(x - a) < 14 and abs(z - b) < 14 for a, b in placed):
            continue
        if bp.get(x, 0, z) is None or bp.get(x, 1, z) is not None:
            continue
        near_app = z > 82 and abs(x) < 40
        if not near_app and math.hypot(x, z) < 70:
            continue
        jungle_tree(S, x, z, 15 + int(hash01(i, 3, 99) * 8), 300 + i)
        placed.append((x, z))
    for i in range(1400):
        x = int(-104 + 208 * hash01(i, 4, 99))
        z = int(-92 + 204 * hash01(i, 5, 99))
        if bp.get(x, 0, z) is None or bp.get(x, 1, z) is not None or (x, z) in S.paths:
            continue
        g = bp.get(x, 0, z)
        if g not in ("minecraft:grass_block", "minecraft:podzol", "minecraft:moss_block", "minecraft:coarse_dirt",
                     "minecraft:rooted_dirt"):
            continue
        if any((x + dx, z + dz) in S.busy for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            continue
        h = hash01(i, 6, 99)
        if h < 0.06:
            bush(S, x, z, 500 + i)
        elif h < 0.42:
            S.set(x, 1, z, "fern")
        elif h < 0.5:
            S.set(x, 1, z, "large_fern[half=lower]")
            S.set(x, 2, z, "large_fern[half=upper]")
        elif h < 0.72:
            S.set(x, 1, z, "short_grass")
        elif h < 0.76 and g != "minecraft:moss_block":
            for y in range(1, 5 + int(hash01(i, 7, 99) * 6)):
                S.set(x, y, z, "bamboo[age=1,leaves=%s,stage=0]" % ("large" if y > 4 else "small" if y > 2 else "none"))
        elif h < 0.8:
            S.set(x, 1, z, "melon" if hash01(i, 8, 99) < 0.3 else "azalea")
        elif h < 0.86:
            S.set(x, 1, z, ("blue_orchid", "poppy", "allium", "oxeye_daisy")[i % 4])


def approach(S):
    path_line(S, [(1, 114), (3, 104), (-1, 94), (1, 86), (0, 82), (0, 70)], half=2.0)
    path_line(S, [(0, 70), (0, 58)], half=6.5, mat="court")
    path_line(S, [(-8, 62), (-24, 64), (-36, 62)], half=1.8)          # to the Gate Trunk's door
    path_line(S, [(-24, 64), (-50, 40), (-64, 20), (-67, -3)], half=1.5)  # the side route to the Market Trunk
    path_line(S, [(8, 62), (30, 46), (62, 34), (82, 24)], half=1.5)     # from the Lift Trunk's door
    path_line(S, [(12, 95), (3, 96)], half=1.2)
    # the court: stelae and broken braziers before the giant stair
    for (x, z) in ((-12, 60), (12, 60), (-12, 68), (12, 68)):
        for y in range(1, 6):
            S.solid(x, y, z, "chiseled_stone_bricks" if y in (1, 5) else tstone(x, y + 20, z))
        S.solid(x, 4, z + (1 if z > 64 else -1) * 0, "chiseled_stone_bricks")
        S.solid(x, 6, z, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
        S.busy.add((x, z))
    S.solid(-12, 3, 61, EYE)
    S.solid(12, 3, 61, EYE)
    # the marker where the track enters the site
    for y in range(1, 4):
        S.solid(4, y, 112, "mossy_stone_bricks" if y < 3 else "chiseled_stone_bricks")
    S.solid(4, 4, 112, JADE)


# ------------------------------------------------------------------ the temple core
CORE_BUDGET = 76000          # entries spent on the core between the rooms (the piece stays under ~440k)


def core_fill(S):
    """The masonry core between the rooms: the unset void inside the stepped mass would keep whatever the terrain
    left there (a dark sealed cavity that spawns mobs). Small pockets are filled whole, the core is filled solid from
    the ground up as far as the entry budget allows, and every floor left in the rest of the void (the top of the
    fill, the backs of vaults and stairs) gets a bottom slab, on which nothing spawns."""
    bp = S.bp
    void = set()
    for x in range(-HW[0], HW[0] + 1):
        for z in range(-HW[0], HW[0] + 1):
            m = mm(x, z)
            for y in range(1, SF):
                if m <= hw_at(y) and (x, y, z) not in bp.blocks:
                    void.add((x, y, z))
    nb = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    # pockets of fewer than 400 cells: filled whole
    small, seen = set(), set()
    for c in void:
        if c in seen:
            continue
        comp, todo = [c], [c]
        seen.add(c)
        while todo:
            x, y, z = todo.pop()
            for dx, dy, dz in nb:
                q = (x + dx, y + dy, z + dz)
                if q in void and q not in seen:
                    seen.add(q)
                    comp.append(q)
                    todo.append(q)
        if len(comp) < 400:
            small.update(comp)

    def plan(yb):
        solid = small | {c for c in void if c[1] <= yb}
        rest = void - solid
        slabs = {c for c in rest if (c[0], c[1] - 1, c[2]) not in rest}
        return solid, slabs

    yb = 1
    solid, slabs = plan(yb)
    while yb < SF:
        s2, l2 = plan(yb + 1)
        if len(s2) + len(l2) > CORE_BUDGET:
            break
        yb, solid, slabs = yb + 1, s2, l2
    for (x, y, z) in solid:
        h = hash3(x, y, z, 91)
        bp.set(x, y, z, "stone" if h < 0.6 else ("tuff" if h < 0.8 else ("andesite" if h < 0.92 else "cobblestone")))
    for (x, y, z) in slabs:
        bp.set(x, y, z, "cobblestone_slab[type=bottom,waterlogged=false]" if hash3(x, y, z, 92) < 0.5
               else "stone_slab[type=bottom,waterlogged=false]")


# ------------------------------------------------------------------ builder
def canopy_city(bp):
    S = Site(bp)
    ground(S)
    approach(S)
    temple_shell(S)
    masks(S)
    giant_stair(S)
    library(S)
    grace_room(S)
    trap_corridor(S)
    sanctum(S)
    offering_hall(S)
    crypt(S)
    cenote(S)
    summit(S)
    sun_disc(S)
    seal(S)
    for name in "ABCDE":
        trunk(S, name)
    elevator(S)
    for (name, L, width, kind) in RINGS:
        ring_platform(S, name, L, width, kind)
    gate(S)
    avoid = links(S)
    districts(S, avoid)
    temple_roots(S)
    camp(S)
    rails(S)
    jungle(S)
    core_fill(S)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("market", (-84 + 10, L2, 6), (0, 60, 0)),
    ("glyph_library", (-10, TF, 15), (-10, TF + 3, -14)),
    ("trap_corridor", (-12, 45, 15), (19, 46, 15)),
    ("jade_sanctum", (-7, 23, 6), (-24, 28, 5)),
    ("crypt", (-10, 1, 1), (-27, 3, -8)),
    ("cenote", (1, 1, 1), (7, 40, 1)),
    ("summit_arena", (0, SF, 17), (0, SF + 18, -16)),
]


register(StructureDef(
    "canopy_city", "overworld", ["jungle", "sparse_jungle", "bamboo_jungle"],
    [Piece("city", canopy_city, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_SPIDER, 5, 1, 2), (MOB_SKEL, 4, 1, 2), (MOB_ZOMBIE, 3, 1, 2)],
    title_fr="La Cité-temple de la canopée", title_en="Canopy Temple-City"))
