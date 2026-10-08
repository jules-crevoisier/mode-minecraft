"""Mire Stilt-City (La Cité des pilotis): a wetland town of timber on piles over a mangrove swamp, 200 blocks across.
Colossal tier (tools/BUILDING.md §1, §12 concept 11, §15).

Silhouette (one noun phrase, §15.1): a witch's hat on stilts, a round hall with a crooked cone roof raised 34 blocks on
a forest of piles, over a crooked town of huts and boardwalks, a smoking chimney on one side and a drowned bell tower
on the other.

Placement: fit mode ``wetland`` (wf/placement.py): the ground layer (blueprint y = 0) is the swamp's water surface.
The template lays its own bog (water channels, mud islets, mangroves) two blocks deep and clears two layers of air
over it, so a hummock of the real swamp never pokes through the low boardwalks.

Levels: water y = 0; boardwalk feet L1 = 3 (the Sumps), L2 = 12 (the market and the smokehouse), L3 = 22 (the High
Walk), the witch-queen's hall floor at feet 34; the drowned undercroft at feet -9 under the water.

Layout (x east, z south; compass from north). The main path (~560 path blocks):
  * the landing (south): a mud islet with the first waystone, the causeway north over the water to the palisade;
  * the gate: a log palisade with two gate towers (guards in the court); outside it fishers' huts; the palisade is
    broken at its west end (the side route: wade round and climb onto the west street);
  * the Sumps (L1): the Eel Market platform, streets of huts on short piles, the Ladderhouse (a timber stair house)
    up to L2;
  * the hub (L2): the market platform round the market tree, stalls, the second waystone; the queen's hall in view.
    Spokes: a rope bridge west to the drowned bell tower (stair down to the undercroft, up to the belfry), a rope
    bridge east to the smokehouse, a ladder north to the High Walk landing;
  * the smokehouse (L2 to L3): the hearth hall under hanging fish, its stair up to the gallery and out on the High
    Walk (L3) round the east and north, a rope bridge, the landing (third waystone, the site of grace before the
    boss), the grand stair (two flights, a covered porch: compression) and the mist into the witch-queen's hall: a
    round hall 35 across under a crooked cone, eight posts (cover in the fight), the throne, the vault behind sealed
    bars, and a chute from the vault down into the queen's pool, 33 blocks below (the way back after the boss).
  * under it all (L1): the spine walk runs under the market from the Eel Market to the queen's pool and the root walk
    under the hall; the west walk joins the bell tower.
  * the drowned undercroft (optional, under the west): a vaulted nave with flooded channels and sunken tombs, a hoard
    room behind a narrow passage, and a tunnel that climbs into a hut on the west street whose iron door opens from
    inside only (shortcut back to the Sumps).
Shortcuts: the undercroft tunnel (one-way iron door), the hoist (scaffolding shaft from L1 to the smokehouse platform),
the ladder from the hub to the landing, the vault chute (a 33-block drop into the queen's pool), the bell tower stair
(L1 <-> L2).
Loot gradient (§15.6): huts, gate and market tier 1, smokehouse, High Walk huts, belfry and undercroft tier 2, the
queen's chest 2-3, the undercroft hoard and the vault behind the boss tier 3.
"""
import math

from ..arch import Palette, stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..megakit import fbm, hash01, hash3
from ..parts import LOOT, MOD

# placeholder boss until the stilt-city gets its own: the Swamp Crone holds court in the witch-queen's hall
BOSS = "brasshaven:swamp_crone"
MOB_DROWNED = "minecraft:drowned"
MOB_BOGGED = "minecraft:bogged"
MOB_WITCH = "minecraft:witch"
MOB_SLIME = "minecraft:slime"

# ------------------------------------------------------------------ dimensions
L1, L2, L3, HALL_F = 3, 12, 22, 34
HALL_C = (0, -74)
HALL_R = 17.5               # interior floor radius (diameter 35)
HALL_W = 19.5               # outer wall radius
HALL_TOP = 47               # last wall course
ROOF_TIP = 100
TOWER_C = (-60, -10)        # drowned bell tower centre (9 x 9)
UND_F = -9                  # undercroft feet
BOG_R = 101

AIR = "minecraft:air"
WATER = "water[level=0]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
FENCE = "mangrove_fence"
PILE = "mangrove_log[axis=y]"
CHAIN_Y = "iron_chain[axis=y,waterlogged=false]"

DECK_MAIN = Palette({"mangrove_planks": 4, "spruce_planks": 3, "stripped_mangrove_wood[axis=y]": 1, "dark_oak_planks": 1},
                    seed=811, scale=1.3)
DECK_SIDE = Palette({"spruce_planks": 4, "mangrove_planks": 3, "dark_oak_planks": 2}, seed=812, scale=2.0)
DECK_HIGH = Palette({"dark_oak_planks": 4, "mangrove_planks": 3, "stripped_dark_oak_wood[axis=y]": 1}, seed=813,
                    scale=2.0)
INFILL = Palette({"spruce_planks": 3, "mangrove_planks": 2, "packed_mud": 2, "mud_bricks": 2, "dark_oak_planks": 1},
                 seed=814, scale=2.4)
MUDWALL = Palette({"mud_bricks": 5, "packed_mud": 3, "bricks": 1}, seed=815, scale=2.0)
STONE = Palette({"mossy_stone_bricks": 4, "tuff_bricks": 4, "mossy_cobblestone": 2, "cracked_stone_bricks": 1,
                 "cobbled_deepslate": 1, "mud_bricks": 1}, seed=816, scale=2.5)
DEEP = Palette({"mossy_cobblestone": 3, "mossy_stone_bricks": 3, "tuff_bricks": 2, "cobbled_deepslate": 1}, seed=817,
               scale=2.0)
ROOF = Palette({"deepslate_tiles": 5, "cobbled_deepslate": 1, "mossy_cobblestone": 1, "deepslate_bricks": 2}, seed=818,
               scale=3.0)
HALLWALL = Palette({"packed_mud": 3, "mud_bricks": 3, "mangrove_planks": 2}, seed=819, scale=2.6)

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def empty(b):
    return b is None or b in ("minecraft:air", "minecraft:cave_air")


def soft(b):
    """Cells a pile or a tree may take: open air, the bog's water and mud, plants."""
    if b is None:
        return True
    s = b.split(":")[1]
    return s in ("air", "water", "mud", "seagrass", "lily_pad", "short_grass", "fern", "firefly_bush", "moss_block",
                 "grass_block", "moss_carpet", "brown_mushroom", "mangrove_roots", "muddy_mangrove_roots", "clay",
                 "sugar_cane", "mangrove_leaves", "azalea_leaves")


def rect(x0, z0, x1, z1):
    return [(x, z) for x in range(min(x0, x1), max(x0, x1) + 1) for z in range(min(z0, z1), max(z0, z1) + 1)]


def card(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


# ------------------------------------------------------------------ the site
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.walk = {}       # (x, z) -> [feet]
        self.nopile = set()  # (x, z, feet) walk cells carried by something else (rope bridges, rooms)
        self.keep = set()    # cells that must stay clear (walk headroom, rooms)
        self.cols = set()    # built columns (no trees)
        self.lamps = 0
        self.warn = []

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)

    def clear(self, x, y, z):
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def add_walk(self, x, z, f, pile=True):
        lst = self.walk.setdefault((x, z), [])
        if f not in lst:
            lst.append(f)
        if not pile:
            self.nopile.add((x, z, f))

    def levels(self, x, z):
        return self.walk.get((x, z), ())

    def claim(self, x0, z0, x1, z1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                self.cols.add((x, z))

    def check_box(self, name, x0, y0, z0, x1, y1, z1, allow=()):
        bad = [(x, y, z) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) for z in range(z0, z1 + 1)
               if (x, y, z) in self.keep and (x, z) not in allow]
        if bad:
            self.warn.append(f"{name}: {len(bad)} cells over walk headroom, e.g. {bad[0]}")


# ------------------------------------------------------------------ walkways
def deck(S, cells, f, pal=DECK_MAIN, head=3, pile=True, skip=()):
    """Plank deck under feet f over the cells, `head` blocks of clear headroom over it."""
    for (x, z) in cells:
        if (x, z) in skip:
            continue
        S.set(x, f - 1, z, pal.pick(x, f - 1, z))
        for h in range(head):
            S.clear(x, f + h, z)
        S.add_walk(x, z, f, pile)


def flight(S, a0, c0, c1, facing, f0, n, mat="mangrove", fill_to=None, head=4):
    """n steps climbing toward `facing` from feet f0: step k (1..n) one block further along, stair block at
    y = f0 + k - 1 (feet f0 + k), the cross range c0..c1 (x for north/south flights, z for east/west ones).
    The underside is filled down to `fill_to` (default: three blocks of stringer)."""
    dx, dz = DIRS[facing]
    for k in range(1, n + 1):
        a = a0 + (dz if dz else dx) * (k - 1)
        y = f0 + k - 1
        for c in range(min(c0, c1), max(c0, c1) + 1):
            x, z = (c, a) if dz else (a, c)
            S.set(x, y, z, stair(f"{mat}_stairs", facing))
            lo = fill_to if fill_to is not None else max(f0 - 1, y - 3)
            for yy in range(lo, y):
                if fill_to is not None:
                    S.keep.discard((x, yy, z))
                if (x, yy, z) not in S.keep:
                    S.set(x, yy, z, f"{mat}_planks")
            for h in range(head):
                S.clear(x, y + 1 + h, z)
            S.add_walk(x, z, f0 + k)


def rope_bridge(S, a0, a1, c0, c1, axis, f, sag, pal=DECK_SIDE):
    """Sagging plank bridge from a0 to a1 along `axis` (cross range c0..c1 walkable, rails on c0-1 and c1+1), level f
    at both ends: thin slabs at half-block steps, fences and rope posts, nothing underneath."""
    lo, hi = min(a0, a1), max(a0, a1)
    L = hi - lo
    for a in range(lo, hi + 1):
        t = (a - lo) / L if L else 0
        h = f - sag * math.sin(math.pi * t)
        hh = round(h * 2) / 2
        n = math.floor(hh)
        half = hh - n > 0.25
        for c in range(min(c0, c1) - 1, max(c0, c1) + 2):
            x, z = (a, c) if axis == "x" else (c, a)
            wood = "mangrove" if pal.pick(x, 0, z).startswith("minecraft:mangrove") else "spruce"
            edge = c < min(c0, c1) or c > max(c0, c1)
            if half:
                S.set(x, n, z, f"{wood}_slab[type=bottom,waterlogged=false]")
                fy = n + 1
            else:
                S.set(x, n - 1, z, f"{wood}_slab[type=top,waterlogged=false]")
                fy = n
            if edge:
                S.set(x, fy, z, FENCE)
                if (a - lo) % 6 == 0 and 0 < a - lo < L:
                    S.set(x, fy + 1, z, FENCE)
                    if (a - lo) % 12 == 0:
                        S.set(x, fy + 2, z, LANT)
            else:
                for k in range(3):
                    S.clear(x, fy + k, z)
                S.add_walk(x, z, hh, pile=False)
    # rope posts at both ends
    for a in (lo - 1, hi + 1):
        for c in (min(c0, c1) - 1, max(c0, c1) + 1):
            x, z = (a, c) if axis == "x" else (c, a)
            if (x, f, z) in S.keep:
                continue
            for y in range(f - 1, f + 3):
                if (x, y, z) not in S.keep:
                    S.set(x, y, z, "stripped_mangrove_log[axis=y]")
            S.set(x, f + 3, z, LANT)


def rails(S):
    """Fences on the cells beside every walkway where the next cell is not walkway at about the same height."""
    n = 0
    for (x, z), lv in sorted(S.walk.items()):
        for f in lv:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, z + dz)
                if any(abs(g - f) <= 1.01 for g in S.levels(*q)):
                    continue
                fy = int(f) if f == int(f) else math.floor(f) + 1
                c1, c0 = (q[0], fy, q[1]), (q[0], fy - 1, q[1])
                if c1 in S.keep or c0 in S.keep or not empty(S.bp.get(*c1)):
                    continue
                b0 = S.bp.get(*c0)
                if not empty(b0) and not b0.endswith("water"):
                    continue
                S.set(*c0, "stripped_dark_oak_wood[axis=y]" if (q[0] + q[1]) % 5 else "dark_oak_planks")
                S.set(*c1, FENCE)
                n += 1
                if n % 9 == 0 and (q[0], fy + 1, q[1]) not in S.keep and empty(S.bp.get(q[0], fy + 1, q[1])):
                    S.set(q[0], fy + 1, q[1], LANT)
    return n


def pile_ok(S, x, z, y_top, y_bot=-2):
    for y in range(y_bot, y_top + 1):
        if (x, y, z) in S.keep or not soft(S.bp.get(x, y, z)):
            return False
    return True


def pile(S, x, z, y_top, y_bot=-2, spec=PILE, roots=True):
    for y in range(y_bot, y_top + 1):
        S.set(x, y, z, spec)
    if roots:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if hash01(x + dx, z + dz, 77) < 0.35 and S.bp.get(x + dx, 0, z + dz) == "minecraft:water" \
                    and (x + dx, z + dz) not in S.walk and (x + dx, 1, z + dz) not in S.keep:
                S.set(x + dx, 0, z + dz, "mangrove_roots[waterlogged=true]")


def piles(S):
    """Piles under the walkways: under the edges every four blocks and on a five-block grid under wide decks; never
    through a lower walkway or room."""
    for (x, z), lv in sorted(S.walk.items()):
        for f in lv:
            if (x, z, f) in S.nopile or f != int(f):
                continue
            f = int(f)
            edge = any(not any(abs(g - f) <= 1.01 for g in S.levels(x + dx, z + dz))
                       for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge and (x + z) % 4 != 0:
                continue
            if not edge and (x % 5 or z % 5):
                continue
            if any(g < f - 1 for g in lv):
                continue
            top = f - 2
            if S.bp.get(x, top, z) is not None and S.bp.get(x, top, z).endswith("_stairs"):
                top -= 1
            while top > -2 and not empty(S.bp.get(x, top, z)) and not soft(S.bp.get(x, top, z)):
                top -= 1
            if top < 0 or not pile_ok(S, x, z, top):
                continue
            pile(S, x, z, top)


# ------------------------------------------------------------------ the bog
def bog(S):
    bp = S.bp
    for x in range(-BOG_R - 4, BOG_R + 5):
        for z in range(-106, 119):
            # a rounded blob: 101 round the centre, stretched south to the landing islet
            zz = z if z < 0 else z * 0.86
            r = math.hypot(x, zz)
            edge = BOG_R + (fbm(x * 0.7, z * 0.7, 9.0, 3) - 0.5) * 10
            if r > edge:
                continue
            n = fbm(x, z, 11.0, 5) + (fbm(x, z, 4.0, 6) - 0.5) * 0.35
            land = n > 0.62
            deep = n < 0.36
            h = hash01(x, z, 9)
            if land:
                top = "grass_block[snowy=false]" if h < 0.45 else "moss_block" if h < 0.7 else "mud"
                bp.set(x, 0, z, top)
                bp.set(x, -1, z, "mud")
                hp = hash01(z, x, 10)
                if hp < 0.08:
                    bp.set(x, 1, z, "firefly_bush")
                elif hp < 0.2:
                    bp.set(x, 1, z, "short_grass" if hp < 0.15 else "fern")
                elif hp < 0.23 and top == "mud":
                    bp.set(x, 1, z, "brown_mushroom")
                else:
                    bp.set(x, 1, z, AIR)
            else:
                bp.set(x, 0, z, WATER)
                if deep:
                    bp.set(x, -1, z, "seagrass" if h < 0.25 else WATER)
                    bp.set(x, -2, z, "mud" if h < 0.7 else "clay")
                else:
                    bp.set(x, -1, z, "mud")
                bp.set(x, 1, z, "lily_pad" if hash01(z, x, 11) < 0.07 else AIR)
            bp.set(x, 2, z, AIR)


def bog_after(S):
    """Once everything stands: lily pads and plants off the walkways, sugar cane on mud beside water."""
    bp = S.bp
    for (x, y, z), b in list(bp.blocks.items()):
        if y != 1 or b[0] not in ("minecraft:lily_pad", "minecraft:short_grass", "minecraft:fern",
                                  "minecraft:firefly_bush", "minecraft:brown_mushroom"):
            continue
        under = bp.get(x, 0, z)
        if b[0] == "minecraft:lily_pad" and under != "minecraft:water":
            bp.set(x, 1, z, AIR)
        elif b[0] != "minecraft:lily_pad" and (under is None or under.endswith("water")):
            bp.set(x, 1, z, AIR)


def mangrove(S, x, z, h, seed, crown=4):
    """A mangrove on prop roots, leaning a little, with two or three flat crowns; placed only where all its cells
    are free (water, air, bog)."""
    cells = {}
    lx = (hash01(x, z, seed + 1) - 0.5) * 4
    lz = (hash01(z, x, seed + 2) - 0.5) * 4
    trunk = []
    for y in range(1, h + 1):
        t = (y / h) ** 1.5
        px, pz = x + round(lx * t), z + round(lz * t)
        trunk.append((px, y, pz))
        cells[(px, y, pz)] = "mangrove_log[axis=y]"
    nroots = 5 + int(hash01(x, z, seed + 3) * 3)
    for k in range(nroots):
        a = 2 * math.pi * (k / nroots + hash01(x, z + k, seed) * 0.12)
        rr = 2.6 + hash01(x + k, z, seed + 4) * 1.6
        ex, ez = x + math.cos(a) * rr, z + math.sin(a) * rr
        y0 = 3 + int(hash01(k, x, seed) * 2)
        n = 6
        for i in range(n + 1):
            t = i / n
            px, pz = round(x + (ex - x) * t), round(z + (ez - z) * t)
            py = round(y0 - (y0 + 1) * t ** 0.8)
            if (px, py, pz) not in cells:
                cells[(px, py, pz)] = "mangrove_roots[waterlogged=false]" if py >= 1 else "muddy_mangrove_roots[axis=y]"
    top = trunk[-1]
    ncrown = 2 + int(hash01(x, z, seed + 6) * 2)
    for c in range(ncrown):
        a = 2 * math.pi * (c / ncrown + hash01(c, z, seed) * 0.3)
        off = 0 if c == 0 else crown * 0.8
        ccx, ccz = top[0] + round(math.cos(a) * off), top[2] + round(math.sin(a) * off)
        ccy = top[1] + (1 if c == 0 else -1 - int(hash01(c, x, seed) * 2))
        cr = crown if c == 0 else max(2, crown - 1)
        if c:
            for i in range(1, round(off) + 1):
                bx = top[0] + round(math.cos(a) * i)
                bz = top[2] + round(math.sin(a) * i)
                cells[(bx, ccy - 1, bz)] = "mangrove_wood[axis=y]"
        for dx in range(-cr - 1, cr + 2):
            for dy in range(-2, 3):
                for dz in range(-cr - 1, cr + 2):
                    d = (dx / cr) ** 2 + (dy / (1.8 if dy >= 0 else 1.2)) ** 2 + (dz / cr) ** 2
                    lump = 0.25 * math.sin(dx * 0.9 + seed + c) * math.cos(dz * 0.8 - dy * 0.6)
                    p = (ccx + dx, ccy + dy, ccz + dz)
                    if d <= 1 + lump and p not in cells:
                        leaf = "azalea_leaves" if hash3(*p, seed) < 0.1 else "mangrove_leaves"
                        cells[p] = f"{leaf}[distance=1,persistent=true,waterlogged=false]"
    for p in cells:
        if p in S.keep or (p[0], p[2]) in S.cols:
            return False
        b = S.bp.get(*p)
        if not soft(b) and not (p[1] <= 0):
            return False
        if p[1] > 2 and not empty(b) and not b.endswith("leaves"):
            return False
    for p, spec in cells.items():
        if p[1] <= 0 and not soft(S.bp.get(*p)):
            continue
        if p[1] == 0 and spec.startswith("mangrove_roots"):
            spec = "mangrove_roots[waterlogged=true]" if S.bp.get(*p) == "minecraft:water" else spec
        S.set(*p, spec)
    # hanging roots under the crowns
    for (px, py, pz), spec in list(cells.items()):
        if spec.startswith("mangrove_leaves") and hash01(px, pz, seed + 5) < 0.1:
            if empty(S.bp.get(px, py - 1, pz)) and (px, py - 1, pz) not in S.keep and py - 1 > 2:
                S.set(px, py - 1, pz, "hanging_roots[waterlogged=false]")
    return True


def trees(S):
    n = 0
    pts = []
    for i in range(1400):
        x = round((hash01(i, 3, 61) - 0.5) * 194)
        z = round((hash01(i, 7, 62) - 0.5) * 206) + 5
        if math.hypot(x, z if z < 0 else z * 0.86) > BOG_R - 6:
            continue
        if any(math.hypot(x - a, z - b) < 11 for a, b in pts):
            continue
        big = hash01(i, 13, 65) < 0.25
        h = (11 + int(hash01(i, 9, 63) * 6)) if big else (6 + int(hash01(i, 9, 63) * 5))
        crown = (5 if big else 3) + int(hash01(i, 11, 64) * 2)
        if mangrove(S, x, z, h, i, crown=crown):
            pts.append((x, z))
            n += 1
    return n


# ------------------------------------------------------------------ houses
def hut(S, x0, z0, x1, z1, f, door, kind="fisher", loot=None, roof="gable", seed=0, spawner=None):
    """A timber hut on piles, floor at feet f, door = (side, u). Walls 4 high under a ceiling, a pitched roof."""
    bp = S.bp
    S.check_box(f"hut {x0},{z0}", x0, f - 1, z0, x1, f + 9, z1)
    S.claim(x0 - 1, z0 - 1, x1 + 1, z1 + 1)
    side, u = door
    top = f + 4
    dark = hash01(x0, z0, seed) < 0.4
    axis = "x" if x1 - x0 >= z1 - z0 else "z"
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            S.set(x, f - 1, z, "dark_oak_planks" if edge else "spruce_planks")
            for y in range(f, top + 1):
                if not edge:
                    # tie beams across the short side every other block, the room open to the rafters
                    if y == top and ((x - x0) % 2 == 0 if axis == "x" else (z - z0) % 2 == 0):
                        S.set(x, y, z, "stripped_dark_oak_log[axis=%s]" % ("z" if axis == "x" else "x"))
                    else:
                        S.clear(x, y, z)
                    continue
                if corner:
                    spec = "stripped_mangrove_log[axis=y]" if not dark else "dark_oak_log[axis=y]"
                elif y == top:
                    spec = "stripped_dark_oak_wood[axis=y]"
                elif y == f:
                    spec = "mud_bricks"
                else:
                    spec = INFILL.pick(x, y, z)
                S.set(x, y, z, spec)
            if not edge:
                S.add_walk(x, z, f, pile=False)
    # windows where the outside is open
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)) or (x in (x0, x1) and z in (z0, z1)):
                continue
            if (x + z + seed) % 3:
                continue
            ox = x + (-1 if x == x0 else 1 if x == x1 else 0)
            oz = z + (-1 if z == z0 else 1 if z == z1 else 0)
            if empty(bp.get(ox, f + 1, oz)) and empty(bp.get(ox, f + 2, oz)) and (ox, f + 1, oz) not in S.keep:
                S.set(x, f + 1, z, "glass_pane")
                S.set(x, f + 2, z, "glass_pane" if hash01(x, z, 5) < 0.5 else INFILL.pick(x, f + 2, z))
    # the door
    if side in ("north", "south"):
        dx_, dz_ = u, (z0 if side == "north" else z1)
    else:
        dx_, dz_ = (x0 if side == "west" else x1), u
    S.clear(dx_, f, dz_)
    S.clear(dx_, f + 1, dz_)
    S.set(dx_, f - 1, dz_, "dark_oak_planks")
    bp.door(dx_, f, dz_, side, wood="mangrove" if hash01(x0, z1, 3) < 0.5 else "spruce")
    S.add_walk(dx_, dz_, f, pile=False)
    # roof
    if roof == "thatch":
        lo, hi = (z0 - 1, z1 + 1) if axis == "x" else (x0 - 1, x1 + 1)
        layer = 0
        while lo + layer <= hi - layer:
            for a in range((x0 if axis == "x" else z0) - 1, (x1 if axis == "x" else z1) + 2):
                for b in (lo + layer, hi - layer):
                    p = (a, top + 1 + layer, b) if axis == "x" else (b, top + 1 + layer, a)
                    S.set(*p, "dried_kelp_block")
            layer += 1
    else:
        mat = "dark_oak_stairs" if dark else "mangrove_stairs"
        bp.gable_roof(x0, z0, x1, z1, top + 1, mat, ridge_axis=axis, overhang=1,
                      fill="stripped_mangrove_log[axis=y]" if not dark else "dark_oak_planks")
    # piles under the corners and the middles of the edges
    for (px, pz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), ((x0 + x1) // 2, z0), ((x0 + x1) // 2, z1)):
        if pile_ok(S, px, pz, f - 2):
            pile(S, px, pz, f - 2)
    # furnishing
    inner = [(x, z) for x in range(x0 + 1, x1) for z in range(z0 + 1, z1)
             if abs(x - dx_) + abs(z - dz_) > 1]
    if not inner:
        return dx_, dz_
    far = sorted(inner, key=lambda c: -(abs(c[0] - dx_) + abs(c[1] - dz_)))
    used = set()

    def put(c, spec):
        used.add(c)
        S.set(c[0], f, c[1], spec)

    if loot:
        c = far[0]
        used.add(c)
        bp.chest(c[0], f, c[1], card(dx_ - c[0], dz_ - c[1]), loot=LOOT + loot)
    rest = [c for c in far if c not in used]
    wall_cells = [c for c in rest if c[0] in (x0 + 1, x1 - 1) or c[1] in (z0 + 1, z1 - 1)]
    if kind == "fisher":
        specs = ["barrel", "cauldron", "crafting_table", "barrel", "composter"]
    elif kind == "witch":
        specs = ["brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", "cauldron", "barrel",
                 "potted_brown_mushroom", "bookshelf"]
    elif kind == "smoke":
        specs = ["smoker[facing=north,lit=false]", "barrel", "barrel", "hay_block[axis=y]", "dried_kelp_block"]
    elif kind == "guard":
        specs = ["barrel", "grindstone[face=floor,facing=north]", "barrel", "smithing_table"]
    else:
        specs = ["barrel", "crafting_table", "barrel"]
    for spec, c in zip(specs, wall_cells[1:]):
        if spec == "barrel":
            bp.barrel(c[0], f, c[1], "up")
            used.add(c)
        else:
            put(c, spec)
    free = [c for c in rest if c not in used]
    beamed = [c for c in free if (S.bp.get(c[0], top, c[1]) or "").endswith("_log")]
    if beamed:
        mid = beamed[len(beamed) // 2]
        S.set(mid[0], top - 1, mid[1], LANT_H)
    if spawner and free:
        c = free[-1]
        bp.spawner(c[0], f, c[1], spawner)
    return dx_, dz_


def stall(S, x, z, f, axis, color, goods="barrel"):
    """A market stall: a counter of barrels and slabs under a striped awning on four posts."""
    bp = S.bp
    w, d = (3, 2) if axis == "x" else (2, 3)
    for i in range(w):
        for j in range(d):
            cx, cz = x + i, z + j
            if j == 0 if axis == "x" else i == 0:
                if (i + j) % 2 == 0:
                    bp.barrel(cx, f, cz, "up")
                else:
                    S.set(cx, f, cz, "spruce_slab[type=top,waterlogged=false]")
                    S.set(cx, f + 1, cz, goods)
    for (cx, cz) in ((x - 1, z - 1), (x + w, z - 1), (x - 1, z + d), (x + w, z + d)):
        for y in range(f, f + 3):
            S.set(cx, y, cz, "spruce_fence")
    for cx in range(x - 1, x + w + 1):
        for cz in range(z - 1, z + d + 1):
            S.set(cx, f + 3, cz, f"{color}_carpet" if (cx + cz) % 2 else "white_carpet")
    for cx in range(x - 1, x + w + 1):
        for cz in range(z - 1, z + d + 1):
            if (cx, f + 3, cz) in S.keep:
                S.keep.discard((cx, f + 3, cz))


# ------------------------------------------------------------------ the route skeleton
def walkways(S):
    # --- L1, the Sumps
    # the landing islet and its steps up onto the causeway
    for (x, z) in rect(-7, 105, 7, 114):
        if math.hypot(x / 7.5, (z - 109.5) / 5.5) <= 1.05:
            S.set(x, 0, z, "mud" if hash01(x, z, 2) < 0.5 else "grass_block[snowy=false]")
            S.set(x, -1, z, "mud")
            S.clear(x, 1, z)
            S.clear(x, 2, z)
            S.clear(x, 3, z)
            S.add_walk(x, z, 1, pile=False)
    flight(S, 105, -1, 1, "north", 1, 2, mat="spruce", fill_to=0)
    deck(S, rect(-1, 84, 1, 103), L1)
    deck(S, rect(-2, 76, 2, 83), L1, head=5)                     # the gate passage
    deck(S, rect(-8, 66, 8, 77), L1)                             # gate court
    deck(S, rect(-16, 50, 12, 65), L1)                           # the Eel Market
    deck(S, rect(-29, 55, -17, 57), L1, DECK_SIDE)               # west street
    deck(S, rect(-32, 31, -30, 57), L1, DECK_SIDE)
    deck(S, rect(-51, 43, -33, 45), L1, DECK_SIDE)               # to the Eelwife's hut
    deck(S, rect(13, 56, 41, 58), L1, DECK_SIDE)                 # east branch
    deck(S, rect(42, 15, 44, 58), L1, DECK_SIDE)
    deck(S, rect(-1, -47, 1, 49), L1)                            # the spine under the market
    deck(S, rect(-6, -54, 6, -48), L1)                           # the queen's pool platform
    deck(S, rect(-1, -99, 1, -55), L1, DECK_SIDE)                # the root walk under the hall
    deck(S, rect(-5, -99, -2, -95), L1, DECK_SIDE)               # the pool landing
    deck(S, rect(-55, -9, -2, -7), L1, DECK_SIDE)                # the west walk to the bell tower
    # --- L2, the market and the smokehouse
    hub = rect(-22, -4, 22, 22) + rect(-10, -14, 12, -5) + rect(-22, 23, -12, 29)
    hub = [c for c in hub if not (c[0] > 18 and c[1] > 19) and not (c[0] < -19 and c[1] < -1)]
    S.hub_tree = set(rect(15, 14, 16, 15))
    deck(S, hub, L2, skip=S.hub_tree)
    deck(S, rect(-27, 27, -23, 29), L2)                          # from the Ladderhouse
    deck(S, rect(-22, -13, -11, -11), L2, DECK_SIDE)             # to the bell tower bridge
    rope_bridge(S, -55, -23, -13, -11, "x", L2, 3.0)
    rope_bridge(S, 23, 39, 5, 7, "x", L2, 2.0)
    deck(S, rect(40, -14, 68, 14), L2, DECK_SIDE)                # the smokehouse platform
    deck(S, rect(4, -22, 6, -15), L2, DECK_SIDE)                 # to the landing ladder
    # --- L3, the High Walk
    deck(S, rect(56, -30, 58, -11), L3, DECK_HIGH)
    deck(S, rect(52, -33, 62, -30), L3, DECK_HIGH)
    deck(S, rect(34, -33, 51, -31), L3, DECK_HIGH)
    rope_bridge(S, 9, 33, -33, -31, "x", L3, 2.5)
    deck(S, rect(-8, -36, 8, -24), L3, DECK_HIGH)                # the landing
    # the grand stair: two flights and the porch landing
    flight(S, -37, -1, 1, "north", L3, 6, mat="dark_oak")
    deck(S, rect(-2, -45, 2, -43), L3 + 6, DECK_HIGH, head=4)
    flight(S, -46, -1, 1, "north", L3 + 6, 6, mat="dark_oak")
    deck(S, rect(-2, -54, 2, -52), HALL_F, DECK_HIGH, head=4)


# ------------------------------------------------------------------ the landing, the causeway, the gate
def landing(S):
    bp = S.bp
    S.set(-4, 1, 110, MOD["waystone"])
    S.set(-5, 1, 108, "spruce_fence")
    S.set(-5, 2, 108, "spruce_fence")
    S.set(-5, 3, 108, LANT)
    # a wayside post with a hanging lamp and a sunk rowboat of planks
    for y in range(1, 6):
        S.set(5, y, 110, "stripped_mangrove_log[axis=y]")
    S.set(4, 5, 110, FENCE)
    S.set(4, 4, 110, LANT_H)
    for (x, z) in ((9, 104), (10, 104), (11, 105), (9, 105), (10, 105)):
        S.set(x, 0, z, "spruce_slab[type=top,waterlogged=true]" if (x + z) % 2 else "spruce_planks")
    bp.barrel(-3, 1, 112, "up")


def gate(S):
    bp = S.bp
    # palisade along z = 80, broken at its west end (the side route)
    for x in range(-50, 51):
        if -8 <= x <= 8:
            continue
        top = 8 + (1 if hash01(x, 80, 3) < 0.4 else 0)
        if x < -38:
            if hash01(x, 81, 4) < 0.45:
                continue
            top = 1 + int(hash01(x, 82, 5) * 6)
        S.claim(x, 80, x, 80)
        for y in range(-2, top + 1):
            S.set(x, y, 80, "mangrove_log[axis=y]" if (x + y) % 7 else "stripped_mangrove_log[axis=y]")
        if top >= 8:
            S.set(x, top + 1, 80, "pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
        if abs(x) % 6 == 0 and x > -38:
            for y in range(2, 5):
                S.set(x, y, 81, "mangrove_log[axis=y]")
            S.set(x, 5, 81, stair("mangrove_stairs", "north"))
    # two gate towers
    for sx in (-1, 1):
        x0, x1 = (3, 7) if sx > 0 else (-7, -3)
        S.check_box("gate tower", x0, L1 - 1, 78, x1, 20, 82)
        S.claim(x0, 78, x1, 82)
        for x in range(x0, x1 + 1):
            for z in range(78, 83):
                edge = x in (x0, x1) or z in (78, 82)
                for y in range(-2, 17):
                    if edge:
                        corner = x in (x0, x1) and z in (78, 82)
                        S.set(x, y, z, "dark_oak_log[axis=y]" if corner else
                              ("mud_bricks" if y <= L1 else INFILL.pick(x, y, z)))
                    elif y in (L1 - 1, L2 - 1):
                        S.set(x, y, z, "spruce_planks")
                    elif y < L1 - 1:
                        S.set(x, y, z, "mud_bricks")
                    else:
                        S.clear(x, y, z)
                if not edge:
                    S.add_walk(x, z, L1, pile=False)
                    S.add_walk(x, z, L2, pile=False)
        # crenels on the top floor walls, arrow slits
        for x in range(x0, x1 + 1):
            for z in range(78, 83):
                if (x in (x0, x1) or z in (78, 82)) and (x + z) % 2:
                    S.set(x, 15, z, AIR)
                    S.set(x, 16, z, AIR)
        for (x, z) in (((x0 + x1) // 2, 82), (x1 if sx > 0 else x0, 80)):
            S.set(x, L1 + 1, z, AIR)
            S.set(x, L1 + 2, z, "iron_bars")
        bp.pyramid_roof(x0, 78, x1, 82, 17, "dark_oak_stairs", overhang=1, cap="dark_oak_planks")
        S.set((x0 + x1) // 2, 20, 80, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        # door to the court (north face) and a ladder up
        dx = (x0 + x1) // 2
        S.clear(dx, L1, 78)
        S.clear(dx, L1 + 1, 78)
        bp.door(dx, L1, 78, "north", wood="spruce")
        S.add_walk(dx, 78, L1, pile=False)
        lx = x1 - 1 if sx < 0 else x0 + 1
        bp.ladder(lx, L1, 81, L2 - 1, "north")
        S.set(lx, L2 - 1, 81, with_props("ladder", facing="north", waterlogged=False))
        for y in range(L1, L2 + 2):
            S.keep.add((lx, y, 81))
        S.set(lx - sx, L2, 79, LANT)
        S.set(dx, L1 + 3, 80, LANT_H)
        bp.barrel(x0 + 1 if sx > 0 else x1 - 1, L1, 79, "up")
        if sx < 0:
            bp.chest(x0 + 1, L2, 79, "south", loot=LOOT + "mire_gate")
    # the lintel over the gate and its banner
    for x in range(-2, 3):
        for z in range(78, 83):
            for y in range(L1 + 5, 17):
                S.set(x, y, z, "dark_oak_planks" if y in (L1 + 5, 16) else INFILL.pick(x, y, z))
        S.set(x, L1 + 4, 78, "iron_bars" if abs(x) < 2 else "dark_oak_planks")
        S.set(x, L1 + 4, 82, "iron_bars" if abs(x) < 2 else "dark_oak_planks")
    for x in (-1, 1):
        S.set(x, 12, 83, with_props("green_wall_banner", facing="south"))
    S.set(0, 12, 83, LANT_H.replace("true", "false"))
    # guards in the court
    bp.spawner(-7, L1, 67, MOB_BOGGED)
    bp.spawner(7, L1, 74, MOB_DROWNED)
    for (x, z) in ((-8, 75), (8, 66)):
        S.set(x, L1, z, "spruce_fence")
        S.set(x, L1 + 1, z, LANT)
    # sunken stepping logs round the broken west end of the palisade (side route)
    for i, (x, z) in enumerate(((-44, 86), (-46, 83), (-47, 78), (-46, 73), (-44, 68), (-42, 63))):
        S.set(x, 0, z, "mangrove_log[axis=x]" if i % 2 else "mangrove_log[axis=z]")
        S.set(x, 1, z, AIR)
    flight(S, 62, -40, -40, "north", 1, 2, mat="spruce", fill_to=0)
    deck(S, rect(-41, 58, -39, 60), L1, DECK_SIDE)
    deck(S, rect(-38, 58, -33, 58), L1, DECK_SIDE)
    deck(S, rect(-33, 49, -33, 57), L1, DECK_SIDE)


# ------------------------------------------------------------------ the Sumps: huts and the Eel Market
def sumps(S):
    bp = S.bp
    hut(S, 2, 86, 8, 92, L1, ("west", 89), "fisher", seed=1)
    hut(S, -9, 94, -2, 100, L1, ("east", 97), "fisher", loot="mire_sumps", seed=2)
    hut(S, -16, 67, -9, 73, L1, ("east", 70), "guard", seed=3)
    hut(S, 14, 48, 21, 55, L1, ("south", 17), "smoke", seed=4, roof="thatch")
    hut(S, 24, 59, 30, 66, L1, ("north", 27), "fisher", loot="mire_sumps", seed=5)
    hut(S, 32, 48, 39, 55, L1, ("south", 35), "witch", seed=6)
    hut(S, 45, 40, 51, 47, L1, ("west", 43), "fisher", seed=7, roof="thatch")
    hut(S, 45, 26, 52, 33, L1, ("west", 29), "store", seed=8)
    hut(S, 34, 32, 41, 39, L1, ("east", 35), "witch", loot="mire_sumps", seed=9, spawner=MOB_WITCH)
    hut(S, -27, 47, -20, 54, L1, ("south", -24), "fisher", seed=10)
    hut(S, -29, 58, -22, 64, L1, ("north", -25), "fisher", loot="mire_sumps", seed=11, roof="thatch")
    hut(S, -40, 46, -34, 53, L1, ("east", 50), "store", seed=12)
    hut(S, -29, 33, -24, 40, L1, ("west", 36), "fisher", seed=13)
    hut(S, 2, 30, 8, 37, L1, ("west", 33), "smoke", seed=14)
    hut(S, -9, 38, -2, 45, L1, ("east", 41), "fisher", seed=15, roof="thatch")
    hut(S, -40, -6, -33, 0, L1, ("north", -37), "witch", seed=16)
    hut(S, 7, -54, 13, -48, L1, ("west", -51), "fisher", seed=17)
    # the Eel Market: stalls, a drying rack, the eel pool (a hatch onto the water)
    stall(S, -13, 52, L1, "x", "lime", "dried_kelp_block")
    stall(S, -13, 60, L1, "x", "brown", "pumpkin")
    stall(S, 7, 52, L1, "x", "green", "melon")
    stall(S, 7, 60, L1, "x", "cyan", "dried_kelp_block")
    for (x, z) in rect(-5, 57, -4, 58):
        S.set(x, L1 - 1, z, AIR)
        S.set(x, 1, z, AIR)
        S.walk[(x, z)].remove(L1)
    for (x, z) in rect(-6, 56, -3, 59):
        if (x, z) not in ((-5, 57), (-4, 57), (-5, 58), (-4, 58)):
            S.set(x, L1, z, "spruce_fence" if (x, z) not in ((-6, 57),) else "spruce_fence_gate[facing=east,in_wall=false,open=false,powered=false]")
            S.keep.discard((x, L1, z))
    for x in range(2, 6):
        S.set(x, L1, 64, "spruce_fence")
        S.set(x, L1 + 1, 64, "spruce_fence")
        S.set(x, L1 + 2, 64, "spruce_slab[type=bottom,waterlogged=false]")
        S.keep.discard((x, L1, 64))
        S.keep.discard((x, L1 + 1, 64))
        S.keep.discard((x, L1 + 2, 64))
    bp.chest(-15, L1, 64, "east", loot=LOOT + "mire_sumps")
    bp.spawner(10, L1, 51, MOB_WITCH)
    for (x, z) in ((-16, 50), (12, 65), (12, 50), (-16, 65)):
        S.set(x, L1, z, "spruce_fence")
        S.set(x, L1 + 1, z, LANT)


# ------------------------------------------------------------------ the Ladderhouse (L1 -> L2)
def ladderhouse(S):
    bp = S.bp
    x0, z0, x1, z1 = -40, 18, -28, 30
    S.claim(x0, z0, x1, z1)
    top = 21
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            if edge:
                for y in range(-2, top + 1):
                    if y < L1 - 1:
                        if corner or (x + z) % 3 == 0:
                            S.set(x, y, z, "mangrove_log[axis=y]")
                        continue
                    S.set(x, y, z, "dark_oak_log[axis=y]" if corner or (x - x0) % 6 == 0 and z in (z0, z1)
                          or (z - z0) % 6 == 0 and x in (x0, x1) else
                          "stripped_dark_oak_wood[axis=y]" if y in (L1 - 1, L2 - 1, top) else
                          "mud_bricks" if y <= L1 + 1 else INFILL.pick(x, y, z))
            else:
                S.set(x, L1 - 1, z, "spruce_planks")
                if (x, L1 - 1, z) in S.keep:
                    pass
                for y in range(-2, L1 - 1):
                    if (x + z) % 4 == 0:
                        S.set(x, y, z, PILE)
                S.add_walk(x, z, L1, pile=False)
                for y in range(L1, top):
                    if (x, y, z) not in S.keep:
                        S.clear(x, y, z)
    # flight A along the west wall up to the mid landing, flight B back south to the top landing
    flight(S, 28, -38, -36, "north", L1, 5, mat="spruce", fill_to=L1)
    deck(S, rect(-38, 21, -30, 23), L1 + 5, DECK_SIDE, head=4, pile=False)
    flight(S, 24, -32, -30, "south", L1 + 5, 4, mat="spruce", fill_to=None)
    deck(S, rect(-32, 28, -30, 29), L2, DECK_SIDE, head=4, pile=False)
    # the floor under the flights is no longer floor
    for z in range(24, 29):
        for x in (-38, -37, -36):
            if L1 in S.walk.get((x, z), []):
                S.walk[(x, z)].remove(L1)
    for z in range(21, 24):
        for x in range(-38, -29):
            S.nopile.add((x, z, L1 + 5))
    # doors: south onto the west street (L1), east onto the hub walk (L2)
    for x in range(-32, -29):
        for y in range(L1, L1 + 4):
            S.clear(x, y, z1)
        S.set(x, L1 - 1, z1, "spruce_planks")
        S.add_walk(x, z1, L1, pile=False)
    for z in (28, 29):
        for y in range(L2, L2 + 3):
            S.clear(x1, y, z)
        S.set(x1, L2 - 1, z, "spruce_planks")
        S.add_walk(x1, z, L2, pile=False)
    for x in range(-33, -28):
        S.set(x, L1 + 4, z1, "dark_oak_planks")
    # windows, lamps, a roof with a lookout lantern
    for y in (L1 + 6, L1 + 7, L2 + 4, L2 + 5):
        for (x, z) in ((x0, 21), (x0, 27), (-34, z0), (x1, 21)):
            S.set(x, y, z, "glass_pane")
    for (x, y, z) in ((-34, L1 + 4, 26), (-37, L1 + 9, 22), (-31, L2 + 4, 25)):
        S.set(x, y + 1, z, CHAIN_Y)
        S.set(x, y, z, LANT_H)
    bp.pyramid_roof(x0, z0, x1, z1, top + 1, "dark_oak_stairs", overhang=1, cap="dark_oak_planks")
    S.set(-34, top + 8, 24, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.barrel(-29, L1, 19, "up")
    bp.barrel(-29, L1, 20, "up")
    bp.barrel(-29, L1 + 1, 19, "up")


# ------------------------------------------------------------------ the hub (L2)
def hub(S):
    bp = S.bp
    # the market tree grows from the water through the deck
    tx, tz = 15, 14
    for y in range(-2, 25):
        for (x, z) in S.hub_tree:
            S.set(x, y, z, "mangrove_log[axis=y]")
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        ex, ez = tx + 0.5 + math.cos(a) * 4.5, tz + 0.5 + math.sin(a) * 4.5
        for i in range(7):
            t = i / 6
            px = round(tx + 0.5 + (ex - tx - 0.5) * t)
            pz = round(tz + 0.5 + (ez - tz - 0.5) * t)
            py = round(6 - 7 * t)
            if (px, py, pz) not in S.keep and soft(bp.get(px, py, pz)):
                S.set(px, py, pz, "mangrove_roots[waterlogged=true]" if py <= 0 else "mangrove_roots[waterlogged=false]")
    for dx in range(-8, 9):
        for dy in range(-2, 5):
            for dz in range(-8, 9):
                d = (dx / 7.5) ** 2 + (dy / (3.2 if dy >= 0 else 2.0)) ** 2 + (dz / 7.5) ** 2
                if d <= 1 + 0.18 * math.sin(dx + dz * 0.7):
                    p = (tx + dx, 25 + dy, tz + dz)
                    if empty(bp.get(*p)):
                        S.set(*p, "mangrove_leaves[distance=1,persistent=true,waterlogged=false]"
                              if hash3(*p, 4) > 0.1 else "shroomlight")
    for (dx, dz) in ((-1, 0), (2, 0), (0, -1), (0, 2), (-1, 2), (2, -1)):
        S.set(tx + dx, 24 - abs(dx + dz) % 2, tz + dz, "mangrove_log[axis=y]")
    for (x, z) in ((12, 12), (19, 17), (13, 19)):
        S.set(x, 22, z, CHAIN_Y)
        S.set(x, 21, z, LANT_H)
    # stalls, the waystone, lamp posts, a weighing beam
    stall(S, -18, 2, L2, "x", "red", "pumpkin")
    stall(S, -18, 12, L2, "x", "orange", "honeycomb_block")
    stall(S, -7, 18, L2, "x", "purple", "dried_kelp_block")
    stall(S, 3, 18, L2, "x", "yellow", "hay_block[axis=y]")
    stall(S, 7, -10, L2, "x", "blue", "melon")
    stall(S, -19, 25, L2, "z", "magenta", "barrel[facing=up,open=false]")
    S.set(-4, L2, 6, MOD["waystone"])
    for (x, z) in ((-5, 4), (-3, 4)):
        S.set(x, L2, z, "spruce_fence")
        S.set(x, L2 + 1, z, LANT)
    for y in range(L2, L2 + 4):
        S.set(4, y, 6, "spruce_fence")
    S.set(4, L2 + 4, 6, "spruce_planks")
    S.set(3, L2 + 4, 6, "spruce_slab[type=bottom,waterlogged=false]")
    S.set(5, L2 + 4, 6, "spruce_slab[type=bottom,waterlogged=false]")
    S.set(3, L2 + 3, 6, CHAIN_Y)
    S.set(5, L2 + 3, 6, CHAIN_Y)
    S.set(3, L2 + 2, 6, "cauldron")
    S.set(5, L2 + 2, 6, LANT_H)
    for y in range(L2, L2 + 5):
        S.keep.discard((4, y, 6))
        S.keep.discard((3, y, 6))
        S.keep.discard((5, y, 6))
    bp.chest(-19, L2, 7, "east", loot=LOOT + "mire_market")
    # houses round the market
    hut(S, 8, 23, 15, 30, L2, ("north", 11), "store", seed=21)
    hut(S, 23, 10, 30, 18, L2, ("west", 14), "witch", seed=22, roof="thatch")
    hut(S, -30, -3, -23, 4, L2, ("east", 0), "fisher", seed=23)
    hut(S, 13, -13, 20, -6, L2, ("west", -10), "smoke", loot="mire_market", seed=24)
    hut(S, -21, -21, -14, -15, L2, ("south", -18), "store", seed=25)
    # the ladder from the hub to the landing (L3)
    for y in range(L2, L3 - 1):
        S.set(5, y, -24, "dark_oak_planks")
        S.set(4, y, -24, "stripped_dark_oak_log[axis=y]")
        S.set(6, y, -24, "stripped_dark_oak_log[axis=y]")
    bp.ladder(5, L2, -23, L3 - 1, "south")
    for y in range(L2, L3 + 2):
        S.keep.add((5, y, -23))
    S.set(5, L3 + 2, -23, AIR)


# ------------------------------------------------------------------ the smokehouse (L2 -> L3) and the hoist
def smokehouse(S):
    bp = S.bp
    x0, z0, x1, z1 = 46, -10, 68, 10
    S.claim(x0, z0, x1 + 5, z1)
    wtop = 27
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            if not edge:
                S.set(x, L2 - 1, z, "spruce_planks" if (x + z) % 5 else "packed_mud")
                for y in range(L2, wtop + 1):
                    if (x, y, z) not in S.keep:
                        S.clear(x, y, z)
                continue
            for y in range(L2 - 1, wtop + 1):
                post = corner or (x - x0) % 5 == 0 and z in (z0, z1) or (z - z0) % 5 == 0 and x in (x0, x1)
                spec = ("dark_oak_log[axis=y]" if post else
                        "stripped_dark_oak_wood[axis=y]" if y in (L3 - 1, wtop) else
                        MUDWALL.pick(x, y, z) if y <= L2 + 3 else INFILL.pick(x, y, z))
                S.set(x, y, z, spec)
    # soot: blackened upper courses
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if hash01(x, z, 8) < 0.4:
                S.set(x, wtop - 1, z, "blackstone")
    # roof: a steep gable along x, soot-dark
    bp.gable_roof(x0, z0, x1, z1, wtop + 1, "dark_oak_stairs", ridge_axis="x", overhang=1, fill="dark_oak_planks")
    for x in range(x0, x1 + 1):
        for z in range(z0 + 1, z1):
            pass
    # rafters under the roof (no bare roof stairs inside)
    for x in range(x0 + 2, x1, 4):
        for z in range(z0 + 1, z1):
            S.set(x, wtop, z, "dark_oak_log[axis=z]")
    # floor of the smokehouse is walkable
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            S.add_walk(x, z, L2, pile=False)
    # the inner stair up the west wall and the gallery round the north wall (L3)
    flight(S, 7, 47, 49, "north", L2, 10, mat="spruce", fill_to=L2)
    deck(S, rect(47, -9, 67, -6) + rect(47, -5, 49, -3), L3, DECK_SIDE, head=4, pile=False)
    for x in range(50, 68, 4):
        for y in range(L2, L3 - 1):
            S.set(x, y, -5, "dark_oak_log[axis=y]")
            S.keep.discard((x, y, -5))
        if x <= 66:
            S.set(x, L3 - 2, -4, stair("dark_oak_stairs", "south", "top"))
    for z in range(-5, 8):
        for x in (47, 48, 49):
            if L2 in S.walk.get((x, z), []):
                S.walk[(x, z)].remove(L2)
    # doors: south (L2, onto the platform) and north (L3, onto the High Walk)
    for x in range(56, 59):
        for y in range(L2, L2 + 4):
            S.clear(x, y, z1)
        S.add_walk(x, z1, L2, pile=False)
    for x in range(56, 59):
        for y in range(L3, L3 + 3):
            S.clear(x, y, z0)
        S.set(x, L3 - 1, z0, "dark_oak_planks")
        S.add_walk(x, z0, L3, pile=False)
    for x in range(55, 60):
        S.set(x, L2 + 4, z1, "dark_oak_planks")
    # the hearth: a long stone trough of fires under racks of hanging fish
    for x in range(52, 63):
        for z in (-1, 0, 1):
            S.set(x, L2 - 1, z, "mud_bricks")
            if z == 0:
                S.set(x, L2, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
                S.keep.discard((x, L2, z))
            else:
                S.set(x, L2, z, "mud_brick_slab[type=bottom,waterlogged=false]")
                S.keep.discard((x, L2, z))
        if L2 in S.walk.get((x, 0), []):
            S.walk[(x, 0)].remove(L2)
    for x in range(52, 63, 2):
        for z in (-2, 2):
            S.set(x, wtop - 1, z, "dark_oak_fence")
            for y in range(L2 + 6, wtop - 1):
                S.set(x, y, z, CHAIN_Y)
            S.set(x, L2 + 5, z, "dried_kelp_block" if (x // 2) % 2 else "brown_mushroom_block[down=true,east=true,"
                  "north=true,south=true,up=true,west=true]")
    for (x, z) in ((52, 6), (62, 6), (52, -3), (62, -3)):
        S.set(x, wtop - 1, z, CHAIN_Y)
        S.set(x, wtop - 2, z, LANT_H)
    # stores: barrels against the walls, the smokehouse chest on the gallery
    for x in range(51, 68, 2):
        bp.barrel(x, L2, 9, "up")
    for z in range(1, 9, 2):
        bp.barrel(67, L2, z, "up")
    bp.barrel(67, L2 + 1, 3, "up")
    bp.chest(66, L3, -9, "south", loot=LOOT + "mire_smokehouse")
    S.set(64, L3, -9, "smoker[facing=south,lit=false]")
    bp.spawner(60, L2, -7, MOB_SLIME)
    # the chimney on the east gable
    cx0, cz0 = 69, -2
    for x in range(cx0, cx0 + 5):
        for z in range(cz0, cz0 + 5):
            ring = x in (cx0, cx0 + 4) or z in (cz0, cz0 + 4)
            for y in range(-2, 51):
                if ring or y < 47:
                    S.set(x, y, z, "bricks" if hash3(x, y, z, 2) < 0.7 or y > 44 else "mud_bricks")
                else:
                    S.set(x, y, z, AIR)
            if ring and (x + z) % 2:
                S.set(x, 51, z, "brick_wall")
    for y in (20, 48):
        for x in range(cx0 - 1, cx0 + 6):
            for z in (cz0 - 1, cz0 + 5):
                S.set(x, y, z, stair("brick_stairs", "south" if z < cz0 else "north", "top"))
        for z in range(cz0, cz0 + 5):
            S.set(cx0 - 1, y, z, stair("brick_stairs", "east", "top"))
            S.set(cx0 + 5, y, z, stair("brick_stairs", "west", "top"))
    S.set(cx0 + 2, 47, cz0 + 2, "hay_block[axis=y]")
    S.set(cx0 + 2, 48, cz0 + 2, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # the hoist: a scaffolding shaft from the east branch (L1) to the platform (L2)
    for y in range(L1, L2):
        S.set(45, y, 15, "scaffolding[bottom=false,distance=0,waterlogged=false]")
        S.keep.add((45, y, 15))
    S.set(45, L1 - 1, 15, "spruce_planks")
    S.keep.add((45, L2, 15))
    S.keep.add((45, L2 + 1, 15))
    for y in range(-2, L2 + 4):
        if (46, y, 16) not in S.keep:
            S.set(46, y, 16, "stripped_mangrove_log[axis=y]")
    S.set(45, L2 + 3, 16, "dark_oak_planks")
    S.set(46, L2 + 4, 16, "dark_oak_planks")
    S.set(45, L2 + 2, 16, CHAIN_Y)
    S.set(45, L2 + 1, 16, "barrel[facing=up,open=false]")


# ------------------------------------------------------------------ the High Walk huts and the landing
def high_walk(S):
    bp = S.bp
    hut(S, 59, -26, 65, -19, L3, ("west", -23), "witch", loot="mire_highwalk", seed=31)
    hut(S, 49, -24, 55, -17, L3, ("east", -21), "store", seed=32, roof="thatch")
    hut(S, 54, -40, 60, -34, L3, ("south", 57), "guard", loot="mire_highwalk", seed=33, spawner=MOB_BOGGED)
    hut(S, 38, -40, 45, -34, L3, ("south", 41), "witch", seed=34)
    # the landing: the site of grace before the hall, a shrine of candles, lamps
    S.set(6, L3, -26, MOD["waystone"])
    for (x, z) in ((-8, -36), (8, -36), (-8, -24), (8, -24)):
        S.set(x, L3, z, "dark_oak_fence")
        S.set(x, L3 + 1, z, "dark_oak_fence")
        S.set(x, L3 + 2, z, SOUL)
        for y in range(L3, L3 + 3):
            S.keep.discard((x, y, z))
    for x in (-7, -6, -5):
        S.set(x, L3, -25, "mud_bricks")
        S.set(x, L3 + 1, -25, "white_candle[candles=3,lit=true,waterlogged=false]" if x != -6 else
              "skeleton_skull[rotation=8]")
        S.keep.discard((x, L3, -25))
        S.keep.discard((x, L3 + 1, -25))


# ------------------------------------------------------------------ the witch-queen's hall
def hall(S):
    bp = S.bp
    cx, cz = HALL_C
    f = HALL_F
    # stilts: 2 x 2 piles on a grid that leaves the root walk (|x| <= 2) free, ring beams and braces
    grid = (-16, -10, -5, 4, 9, 15)
    posts = []
    for gx in grid:
        for gz in (-16, -10, -5, 4, 9, 15):
            if math.hypot(gx + 0.5, gz + 0.5) <= HALL_W - 1.0:
                posts.append((cx + gx, cz + gz))
    for (px, pz) in posts:
        for x in (px, px + 1):
            for z in (pz, pz + 1):
                for y in range(-2, f - 1):
                    S.set(x, y, z, "mangrove_log[axis=y]" if y % 9 else "stripped_mangrove_log[axis=y]")
        for dx, dz in ((-1, 0), (2, 0), (0, -1), (0, 2), (-1, 1), (2, 1), (1, -1), (1, 2)):
            if S.bp.get(px + dx, 0, pz + dz) == "minecraft:water":
                S.set(px + dx, 0, pz + dz, "mangrove_roots[waterlogged=true]")
            if S.bp.get(px + dx, 1, pz + dz) in (None, AIR) and hash01(px + dx, pz + dz, 4) < 0.5:
                S.set(px + dx, 1, pz + dz, "mangrove_roots[waterlogged=false]")
        S.claim(px, pz, px + 1, pz + 1)
    pset = set(posts)
    for (px, pz) in posts:
        for (qx, qz, axis) in ((px + 9, pz, "x"), (px + 5, pz, "x"), (px + 6, pz, "x"), (px, pz + 9, "z"),
                               (px, pz + 5, "z"), (px, pz + 6, "z")):
            if (qx, qz) not in pset:
                continue
            for y in (13, 24):
                if axis == "x":
                    for x in range(px + 2, qx):
                        if (x, y, pz) not in S.keep:
                            S.set(x, y, pz, "stripped_mangrove_log[axis=x]")
                else:
                    for z in range(pz + 2, qz):
                        if (px, y, z) not in S.keep:
                            S.set(px, y, z, "stripped_mangrove_log[axis=z]")
            # an X of fences between the two beams
            if axis == "x":
                n = qx - px - 2
                for i in range(n):
                    for y in (14 + round(i * 9 / max(1, n - 1)), 23 - round(i * 9 / max(1, n - 1))):
                        if empty(bp.get(px + 2 + i, y, pz)):
                            S.set(px + 2 + i, y, pz, FENCE)
            break
    # the floor: two layers over the full disk, a rim of corbels
    for x in range(cx - 21, cx + 22):
        for z in range(cz - 21, cz + 22):
            d = math.hypot(x - cx, z - cz)
            if d <= HALL_W:
                S.set(x, f - 2, z, "dark_oak_planks")
                ring = int(d) % 4 == 0
                S.set(x, f - 1, z, "stripped_dark_oak_wood[axis=y]" if ring else
                      ("dark_oak_planks" if (x + z) % 3 else "mangrove_planks"))
                S.claim(x, z, x, z)
            elif d <= HALL_W + 1.0:
                S.set(x, f - 2, z, stair("dark_oak_stairs", card(cx - x, cz - z), "top"))
    # walls: timber posts, mud infill, a band of dark planks at the top; six windows onto the swamp
    windows = (30, 60, 90, 120, 150, 210, 240, 270, 300, 330)
    for x in range(cx - 21, cx + 22):
        for z in range(cz - 21, cz + 22):
            d = math.hypot(x - cx, z - cz)
            if not HALL_R < d <= HALL_W:
                if d <= HALL_R:
                    S.add_walk(x, z, f, pile=False)
                    for y in range(f, f + 4):
                        S.keep.add((x, y, z))
                continue
            phi = math.degrees(math.atan2(x - cx, -(z - cz))) % 360
            post = (phi % 15) < 2.6
            dw = min(min(abs(phi - w), 360 - abs(phi - w)) for w in windows)
            win = dw < 3.4
            wtop = f + 10 if dw < 1.6 else f + 9
            for y in range(f, HALL_TOP + 1):
                if win and f + 3 <= y <= wtop and d > HALL_W - 1.2:
                    spec = "glass_pane" if y < wtop else "dark_oak_planks"
                elif win and f + 3 <= y < wtop:
                    spec = AIR
                elif post:
                    spec = "dark_oak_log[axis=y]"
                elif y in (HALL_TOP, HALL_TOP - 1) or y == f + 9:
                    spec = "dark_oak_planks"
                elif y <= f + 1:
                    spec = "mud_bricks"
                else:
                    spec = HALLWALL.pick(x, y, z)
                S.set(x, y, z, spec)
            if win:
                S.set(x, f + 2, z, "dark_oak_slab[type=top,waterlogged=false]" if d <= HALL_W - 1.2 else
                      HALLWALL.pick(x, f + 2, z))
    # the roof: a crooked witch's hat with an overhang, rafters inside
    def roof_c(y):
        t = (y - HALL_TOP - 1) / (ROOF_TIP - HALL_TOP - 1)
        return cx + 9.0 * t ** 2.6, cz + 6.0 * t ** 2.6, 23.0 * (1 - t) ** 1.55 + 0.45

    for y in range(HALL_TOP + 1, ROOF_TIP + 1):
        ox, oz, r = roof_c(y)
        t = (y - HALL_TOP - 1) / (ROOF_TIP - HALL_TOP - 1)
        band = 0.10 <= t <= 0.14
        rr = int(math.ceil(r)) + 2
        for x in range(int(ox) - rr, int(ox) + rr + 2):
            for z in range(int(oz) - rr, int(oz) + rr + 2):
                d = math.hypot(x - ox, z - oz)
                if r - 1.5 < d <= r:
                    h = hash3(x, y, z, 6)
                    spec = ("polished_blackstone_bricks" if band else
                            "moss_block" if h < 0.16 * (1 - t) ** 3 else
                            "mossy_cobblestone" if h < 0.3 * (1 - t) ** 2 else ROOF.pick(x, y, z))
                    S.set(x, y, z, spec)
                elif y == HALL_TOP + 1 and d <= r - 1.5 and d > HALL_R:
                    S.set(x, y, z, "dark_oak_planks")
    # the brim: a drip course of stairs round the eave
    ox, oz, r = roof_c(HALL_TOP + 1)
    for x in range(cx - 26, cx + 27):
        for z in range(cz - 26, cz + 27):
            d = math.hypot(x - ox, z - oz)
            if r < d <= r + 1.0 and empty(bp.get(x, HALL_TOP + 1, z)):
                S.set(x, HALL_TOP + 1, z, stair("deepslate_tile_stairs", card(ox - x, oz - z)))
            if r - 1.6 < d <= r and empty(bp.get(x, HALL_TOP, z)):
                S.set(x, HALL_TOP, z, stair("deepslate_tile_stairs", card(x - ox, z - oz), "top"))
    tx_, _, _ = roof_c(ROOF_TIP)
    tip = (round(roof_c(ROOF_TIP)[0]), round(roof_c(ROOF_TIP)[1]))
    S.set(tip[0], ROOF_TIP + 1, tip[1], "polished_blackstone_wall")
    S.set(tip[0], ROOF_TIP + 2, tip[1], "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # dormers with green glass at three heights
    for (phi, yy) in ((90, 55), (210, 58), (330, 61), (150, 64), (30, 57), (270, 62)):
        ox, oz, r = roof_c(yy)
        a = math.radians(phi)
        x, z = round(ox + math.sin(a) * (r - 0.7)), round(oz - math.cos(a) * (r - 0.7))
        for y in (yy, yy + 1):
            S.set(x, y, z, "green_stained_glass")
        S.set(x, yy + 2, z, ROOF.pick(x, yy + 2, z))
    # eight posts round the floor (cover in the fight), knee braces to the wall top
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        px, pz = round(cx + 12.5 * math.sin(a)), round(cz - 12.5 * math.cos(a))
        for x in (px, px + 1):
            for z in (pz, pz + 1):
                for y in range(f, HALL_TOP + 1):
                    S.set(x, y, z, "dark_oak_log[axis=y]" if y not in (f, f + 6) else "stripped_dark_oak_wood[axis=y]")
                    S.keep.discard((x, y, z))
                if (x, z) in S.walk and f in S.walk[(x, z)]:
                    S.walk[(x, z)].remove(f)
        out = card(px - cx, pz - cz)
        dx, dz = DIRS[out]
        for i in range(1, 5):
            for (x, z) in ((px + dx * i, pz + dz * i), (px + 1 + dx * i, pz + 1 + dz * i)):
                if math.hypot(x - cx, z - cz) <= HALL_R:
                    S.set(x, HALL_TOP, z, "dark_oak_planks")
        # rafters climbing into the cone to the king post, a lantern hanging from each
        for i in range(0, 15):
            y = HALL_TOP + 1 + i
            t = i / 14
            x = round(px + (cx - px) * t)
            z = round(pz + (cz - pz) * t)
            S.set(x, y, z, "dark_oak_log[axis=y]")
            if i == 11:
                for yy in range(f + 10, y):
                    S.set(x, yy, z, CHAIN_Y)
                S.set(x, f + 9, z, SOUL_H)
    for y in range(HALL_TOP + 14, HALL_TOP + 22):
        S.set(cx, y, cz, "dark_oak_log[axis=y]")
    # the throne on its dais (north), cauldrons and candles, the queen's chest
    for x in range(-4, 5):
        for z in range(-90, -86):
            if math.hypot(x, z - cz) <= HALL_R - 0.5:
                S.set(x, f, z, "dark_oak_slab[type=bottom,waterlogged=false]" if z == -86 else "dark_oak_planks")
                S.keep.discard((x, f, z))
                S.walk[(x, z)] = [f + 0.5 if z == -86 else f + 1]
    S.set(0, f + 1, -89, stair("dark_oak_stairs", "south"))
    for y in range(f + 2, f + 6):
        S.set(0, y, -90, "dark_oak_planks" if y < f + 5 else "chiseled_polished_blackstone")
        S.keep.discard((0, y, -90))
    S.set(-1, f + 1, -89, "mangrove_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    S.set(1, f + 1, -89, "mangrove_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    for x in (-3, 3):
        S.set(x, f + 1, -88, "cauldron")
        S.set(x, f + 1, -87, "white_candle[candles=4,lit=true,waterlogged=false]")
    bp.chest(-4, f + 1, -87, "south", loot=LOOT + "mire_queen")
    for (x, z) in ((-10, -64), (10, -64), (-12, -80), (12, -80)):
        S.set(x, f, z, "cauldron")
        S.set(x, f - 1, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the chandelier on a long chain from the king post
    for y in range(f + 9, HALL_TOP + 14):
        S.set(cx, y, cz, CHAIN_Y)
    S.set(cx, f + 8, cz, SOUL_H)
    for k in range(8):
        a = math.radians(k * 45)
        x, z = round(cx + 16.5 * math.sin(a)), round(cz - 16.5 * math.cos(a))
        if k != 4:
            S.set(x, f + 5, z, "soul_wall_torch[facing=%s]" % card(cx - x, cz - z))
    # the boss
    bp.boss_seal(cx, f - 1, cz, BOSS, 16)
    # the door (south): a gap in the wall, the mist across it
    for x in range(-1, 2):
        for z in (-57, -56, -55):
            for y in range(f, f + 4):
                S.clear(x, y, z)
            S.set(x, f - 1, z, "dark_oak_planks")
            S.add_walk(x, z, f, pile=False)
        S.set(x, f + 4, -55, "dark_oak_planks")

    # the porch over the top of the grand stair (compression before the hall)
    for z in range(-54, -47):
        for x in (-3, 3):
            for y in range(L3 + 6, f + 5):
                if (x, y, z) not in S.keep and (z <= -52 or y >= f - 2):
                    S.set(x, y, z, "dark_oak_log[axis=y]" if z in (-54, -48) else INFILL.pick(x, y, z))
        for x in range(-3, 4):
            S.set(x, f + 5, z, "dark_oak_planks")
            S.set(x, f + 6, z, stair("deepslate_tile_stairs", "west" if x < 0 else "east") if x else
                  "deepslate_tile_slab[type=bottom,waterlogged=false]")
    for z in (-53, -50):
        S.set(-3, f + 2, z, "glass_pane") if z <= -52 else None
    S.set(0, f + 4, -53, SOUL_H)
    S.set(0, f + 4, -49, SOUL_H)


def vault(S):
    """The vault behind the throne: a bay on the north side, sealed bars, two chests, the chute to the pool."""
    bp = S.bp
    f = HALL_F
    x0, z0, x1, z1 = -4, -100, 4, -92
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z == z0
            S.set(x, f - 2, z, "dark_oak_planks")
            S.set(x, f - 1, z, "dark_oak_planks")
            for y in range(f, f + 7):
                if edge or y == f + 6:
                    if math.hypot(x - HALL_C[0], z - HALL_C[1]) > HALL_R:
                        S.set(x, y, z, "dark_oak_log[axis=y]" if x in (x0, x1) and z == z0 else HALLWALL.pick(x, y, z))
                elif z <= -94:
                    S.clear(x, y, z)
            if not edge and z <= -94:
                S.add_walk(x, z, f, pile=False)
    for z in range(z0, z1 + 1):
        for x in range(x0 - 1, x1 + 2):
            S.set(x, f + 7, z, stair("deepslate_tile_stairs", "east" if x < 0 else "west") if x else
                  "deepslate_tiles")
    for (px, pz) in ((x0, z0), (x1, z0), (x0, -93), (x1, -93)):
        for y in range(-2, f - 2):
            S.set(px, y, pz, "mangrove_log[axis=y]")
    # the opening through the hall wall, the sealed bars
    for x in range(-1, 2):
        for z in (-93, -92):
            for y in range(f, f + 3):
                S.clear(x, y, z)
            S.set(x, f + 3, z, "dark_oak_planks")
            S.set(x, f - 1, z, "dark_oak_planks")
            S.add_walk(x, z, f, pile=False)
        for y in range(f, f + 3):
            S.set(x, y, -92, MOD["vault_bars"])
            S.keep.discard((x, y, -92))
        S.walk[(x, -92)] = []
    bp.chest(-2, f, -99, "south", loot=LOOT + "mire_vault")
    bp.chest(1, f, -99, "south", loot=LOOT + "mire_vault")
    for x in (-3, 0):
        S.set(x, f, -99, "gold_block" if x == 0 else "white_candle[candles=4,lit=true,waterlogged=false]")
        S.keep.discard((x, f, -99))
    S.set(-3, f, -95, "emerald_block")
    S.keep.discard((-3, f, -95))
    S.set(0, f + 5, -96, SOUL_H)
    # the chute: a hole in the floor over the queen's pool, 33 blocks down
    hx, hz = 3, -97
    for y in range(1, f):
        S.clear(hx, y, hz)
    S.walk[(hx, hz)] = []
    S.set(hx, f, hz + 1, "mangrove_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    S.keep.discard((hx, f, hz + 1))
    # the pool under it, lined, 4 deep; a ladder up onto the root walk
    for x in range(1, 5):
        for z in range(-99, -94):
            inner = 2 <= x <= 4 and -98 <= z <= -96
            for y in range(-5, 1):
                if inner and y >= -4:
                    S.set(x, y, z, WATER)
                elif y >= -5:
                    S.set(x, y, z, DEEP.pick(x, y, z) if not (x == 1 and y >= -1) else "mangrove_log[axis=y]")
    for y in range(0, 3):
        S.set(1, y, -97, "mangrove_log[axis=y]")
    S.set(2, 0, -97, "ladder[facing=east,waterlogged=true]")
    S.set(2, 1, -97, "ladder[facing=east,waterlogged=false]")
    S.set(2, 2, -97, "ladder[facing=east,waterlogged=false]")
    for y in (1, 2, 3):
        S.keep.add((2, y, -97))
    S.set(-4, L1, -99, "spruce_fence")
    S.set(-4, L1 + 1, -99, LANT)


# ------------------------------------------------------------------ the drowned bell tower and the undercroft
def tower_path():
    """The square newel stair of the bell tower: [(local x, local z, feet, kind, facing)], from the undercroft
    (feet UND_F, south-east corner) up to the belfry (feet 30, south-west corner). Each corner landing is 2 x 2, each
    side three steps up."""
    corners = [((2, 3), (2, 3)), ((-3, -2), (2, 3)), ((-3, -2), (-3, -2)), ((2, 3), (-3, -2))]   # SE, SW, NW, NE
    sides = [  # cells in climbing order, facing
        ([((1, 0, -1)[i], (2, 3)) for i in range(3)], "west", "x"),
        ([((-3, -2), (1, 0, -1)[i]) for i in range(3)], "north", "z"),
        ([((-1, 0, 1)[i], (-3, -2)) for i in range(3)], "east", "x"),
        ([((2, 3), (-1, 0, 1)[i]) for i in range(3)], "south", "z"),
    ]
    out = []
    f = UND_F
    k = 0
    while True:
        cxs, czs = corners[k % 4]
        for x in cxs:
            for z in czs:
                out.append((x, z, f, "land", None))
        if f >= 30:
            break
        cells, facing, axis = sides[k % 4]
        for i, cell in enumerate(cells):
            if axis == "x":
                for z in cell[1]:
                    out.append((cell[0], z, f + i + 1, "step", facing))
            else:
                for x in cell[0]:
                    out.append((x, cell[1], f + i + 1, "step", facing))
        f += 3
        k += 1
    return out


def bell_tower(S):
    bp = S.bp
    tx, tz = TOWER_C
    top = 37
    path = tower_path()
    visits = {}
    for (x, z, f, kind, fc) in path:
        visits.setdefault((x, z), []).append((f, kind, fc))
    S.claim(tx - 5, tz - 5, tx + 5, tz + 5)
    for lx in range(-4, 5):
        for lz in range(-4, 5):
            x, z = tx + lx, tz + lz
            wall = max(abs(lx), abs(lz)) == 4
            core = max(abs(lx), abs(lz)) <= 1
            for y in range(UND_F - 2, top + 1):
                if wall:
                    S.set(x, y, z, STONE.pick(x, y, z) if y > -1 else DEEP.pick(x, y, z))
                    continue
                if core:
                    S.set(x, y, z, STONE.pick(x, y, z) if y < 30 else AIR)
                    continue
                spec = DEEP.pick(x, y, z)
                vs = sorted(visits.get((lx, lz), []))
                for (f, kind, fc) in vs:
                    if y == f - 1:
                        spec = "tuff_bricks" if kind == "land" else stair("tuff_brick_stairs", fc)
                    elif f <= y <= f + 3:
                        spec = AIR
                last = vs[-1][0] if vs else UND_F
                if y >= last and y != last - 1:
                    spec = AIR
                if y == 29 and last <= 26:
                    spec = "spruce_planks"
                    S.add_walk(x, z, 30, pile=False)
                if spec == AIR:
                    S.clear(x, y, z)
                else:
                    S.set(x, y, z, spec)
            if core:
                S.add_walk(x, z, 30, pile=False)
    for (x, z, f, kind, fc) in path:
        S.add_walk(tx + x, tz + z, f, pile=False)
    # a battered plinth at the waterline, string courses, corner buttresses stepping back as they rise
    for lx in range(-8, 9):
        for lz in range(-8, 9):
            m = max(abs(lx), abs(lz))
            x, z = tx + lx, tz + lz
            if m == 5 and (x, z) not in S.walk:
                for y in range(-3, 2):
                    if (x, y, z) not in S.keep:
                        S.set(x, y, z, DEEP.pick(x, y, z))
                if (x, 2, z) not in S.keep:
                    S.set(x, 2, z, stair("mossy_stone_brick_stairs", card(-lx, -lz)))
                for y in (13, 25):
                    if empty(bp.get(x, y, z)) and (x, y, z) not in S.keep:
                        S.set(x, y, z, stair("stone_brick_stairs", card(-lx, -lz), "top"))
            elif 6 <= m <= 8 and bp.get(x, 0, z) == "minecraft:water" and (x, z) not in S.walk:
                S.set(x, -1, z, WATER)
                S.set(x, -2, z, "mud")
    for (sx, sz) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        for dep, ytop in ((1, 30), (2, 18), (3, 8)):
            for (ox, oz) in ((4 + dep, 4), (4, 4 + dep)):
                x, z = tx + sx * ox, tz + sz * oz
                if (x, z) in S.walk:
                    continue
                for y in range(-3, ytop + 1):
                    if (x, y, z) not in S.keep:
                        S.set(x, y, z, STONE.pick(x, y, z) if y > 1 else DEEP.pick(x, y, z))
                if (x, ytop + 1, z) not in S.keep:
                    S.set(x, ytop + 1, z, stair("mossy_stone_brick_stairs", card(-sx * (ox - 4), -sz * (oz - 4))))
    # doors: the undercroft (south, feet -9), L1 (east, feet 3), L2 (east, feet 12)
    for (cells, f) in (([(2, 4), (3, 4)], UND_F), ([(4, 2), (4, 3)], L1), ([(4, -3), (4, -2)], L2)):
        for (lx, lz) in cells:
            x, z = tx + lx, tz + lz
            for y in range(f, f + 3):
                S.clear(x, y, z)
            S.set(x, f - 1, z, "tuff_bricks")
            S.add_walk(x, z, f, pile=False)
    # the belfry: arches on four sides, the bell over the core, a pyramid roof; a ruined corner
    for lx in range(-4, 5):
        for lz in range(-4, 5):
            if max(abs(lx), abs(lz)) != 4:
                continue
            u = lz if abs(lx) == 4 else lx
            if abs(u) <= 2:
                for y in range(31, 35):
                    S.set(tx + lx, y, tz + lz, AIR if abs(u) <= 1 else "stone_brick_wall")
    for x in range(tx - 3, tx + 4):
        S.set(x, 36, tz, "stripped_dark_oak_log[axis=x]")
    S.set(tx, 35, tz, "bell[attachment=ceiling,facing=north,powered=false]")
    for lx in range(-4, 5):
        for lz in range(-4, 5):
            S.set(tx + lx, top, tz + lz, STONE.pick(tx + lx, top, tz + lz))
    bp.pyramid_roof(tx - 4, tz - 4, tx + 4, tz + 4, top + 1, "deepslate_tile_stairs", overhang=1,
                    cap="deepslate_tiles")
    S.set(tx, top + 6, tz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for (x, y, z) in ((tx + 4, top, tz + 4), (tx + 4, top - 1, tz + 4), (tx + 3, top, tz + 4), (tx + 4, top, tz + 3)):
        S.set(x, y, z, AIR)
    for (x, z) in ((tx + 7, tz + 6), (tx + 6, tz + 8), (tx + 8, tz + 7)):
        S.set(x, 0, z, "mossy_stone_bricks")
    bp.chest(tx - 1, 30, tz - 1, "south", loot=LOOT + "mire_belfry")
    S.set(tx + 1, 30, tz - 1, LANT)
    S.keep.discard((tx + 1, 30, tz - 1))
    # lamps on the stair
    for (lx, lz, y) in ((-3, 3, -5), (3, -3, 7), (-3, -3, 16), (3, 3, 24)):
        S.set(tx + lx, y + 3, tz + lz, SOUL_H if y < 0 else LANT_H)
    # moss and vines down the outer walls from the waterline
    for lx in range(-5, 6):
        for lz in range(-5, 6):
            if max(abs(lx), abs(lz)) != 5:
                continue
            x, z = tx + lx, tz + lz
            if hash01(x, z, 21) < 0.35 and empty(bp.get(x, 1, z)) and (x, 1, z) not in S.keep \
                    and (x, z) not in S.walk:
                S.set(x, 1, z, "moss_carpet")


def carve(S, x0, y0, z0, x1, y1, z1, pal=DEEP, floor=None):
    """An undercroft room: air inside, a lining shell round it (watertight under the bog)."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, y1 + 2):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and y0 <= y <= y1
                if inside:
                    S.clear(x, y, z)
                elif (x, y, z) in S.keep:
                    continue
                elif y == y0 - 1 and x0 <= x <= x1 and z0 <= z <= z1:
                    S.set(x, y, z, floor or pal.pick(x, y, z))
                else:
                    b = S.bp.get(x, y, z)
                    if b is None or soft(b) or y <= 0:
                        S.set(x, y, z, pal.pick(x, y, z))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            S.add_walk(x, z, y0, pile=False)


def undercroft(S):
    bp = S.bp
    f = UND_F
    tx, tz = TOWER_C
    # vestibule from the tower's south door, the nave, the ossuary, the hoard passage and room, the exit tunnel
    carve(S, tx + 2, f, tz + 5, tx + 3, f + 3, tz + 9)                       # x -58..-57, z -5..-1
    carve(S, -66, f, 0, -48, f + 5, 21)
    carve(S, -47, f, 6, -44, f + 3, 13)
    carve(S, -72, f, 10, -67, f + 2, 11)
    carve(S, -79, f, 6, -73, f + 4, 15)
    carve(S, -58, f, 22, -56, f + 3, 32)
    # the nave: pillars, a groined look, flooded channels down both sides, sunken tombs
    for px in (-61, -53):
        for pz in (4, 9, 14, 19):
            for y in range(f, f + 6):
                S.set(px, y, pz, "tuff_bricks" if y not in (f, f + 4) else "chiseled_tuff_bricks")
                S.keep.discard((px, y, pz))
            for (dx, dz, fc) in ((-1, 0, "east"), (1, 0, "west"), (0, -1, "south"), (0, 1, "north")):
                S.set(px + dx, f + 5, pz + dz, stair("tuff_brick_stairs", fc, "top"))
                S.keep.discard((px + dx, f + 5, pz + dz))
            S.walk[(px, pz)] = []
    for z in range(1, 21):
        for x in (-65, -64, -50, -49):
            S.set(x, f - 1, z, WATER)
            S.set(x, f - 2, z, "mud")
            S.walk[(x, z)] = []
            if hash01(x, z, 31) < 0.3:
                S.set(x, f - 1, z, "seagrass")
    for z in (6, 11, 16):
        for x in range(-58, -55):
            S.set(x, f, z, "mossy_stone_brick_slab[type=bottom,waterlogged=false]" if x != -57 else
                  "chiseled_stone_bricks")
            S.keep.discard((x, f, z))
            S.walk[(x, z)] = [f + 0.5 if x != -57 else f + 1]
    for (x, z) in ((-57, 2), (-57, 19), (-62, 12), (-52, 12), (-62, 3), (-52, 20)):
        S.set(x, f + 5, z, SOUL_H)
    for (x, z) in ((-66, 21), (-48, 0), (-66, 0)):
        S.set(x, f, z, "bone_block[axis=y]")
        S.set(x, f + 1, z, "skeleton_skull[rotation=6]")
        S.keep.discard((x, f, z))
        S.keep.discard((x, f + 1, z))
        S.walk[(x, z)] = []
    bp.spawner(-57, f, 9, MOB_DROWNED)
    bp.spawner(-62, f, 17, MOB_BOGGED)
    # the ossuary niche (east): the undercroft chest
    for z in range(6, 14):
        S.set(-44, f + 1, z, "bone_block[axis=y]" if z % 2 else "skeleton_skull[rotation=4]")
        S.keep.discard((-44, f + 1, z))
    for y in (f, f + 1, f + 2):
        for z in range(6, 14):
            pass
    for x in (-48,):
        for z in range(6, 14):
            if z not in (9, 10):
                for y in range(f, f + 4):
                    S.set(x, y, z, "tuff_bricks")
                    S.keep.discard((x, y, z))
                S.walk[(x, z)] = []
    bp.chest(-45, f, 13, "west", loot=LOOT + "mire_undercroft")
    S.set(-46, f + 3, 9, SOUL_H)
    # the hoard (west, through the narrow passage): the best of the undercroft, guarded
    bp.chest(-78, f, 10, "east", loot=LOOT + "mire_hoard")
    for (x, z) in ((-78, 7), (-78, 14), (-74, 6), (-74, 15)):
        S.set(x, f, z, "white_candle[candles=3,lit=true,waterlogged=false]")
        S.keep.discard((x, f, z))
    for z in range(6, 16):
        S.set(-79, f + 1, z, "bone_block[axis=y]" if z % 3 else "skeleton_skull[rotation=12]")
        S.keep.discard((-79, f + 1, z))
    bp.spawner(-75, f, 12, MOB_BOGGED)
    S.set(-76, f + 4, 10, SOUL_H)
    S.set(-70, f + 2, 10, SOUL_H)
    # the exit: a stair up the tunnel into the Eelwife's hut (feet 3), whose iron door opens from inside only
    for k in range(1, 13):
        z = 32 + k
        y = f + k - 1
        for x in (-58, -57, -56):
            S.set(x, y, z, stair("tuff_brick_stairs", "south"))
            for yy in range(y - 2, y):
                S.set(x, yy, z, "tuff_bricks")
            for h in range(1, 5):
                if y + h <= L1 + 3:
                    S.clear(x, y + h, z)
            S.add_walk(x, z, f + k, pile=False)
            for yy in range(y + 5, L1 - 1):
                S.set(x, yy, z, DEEP.pick(x, yy, z))
        for x in (-59, -55):
            for yy in range(y - 2, min(y + 6, L1 - 1)):
                if (x, yy, z) not in S.keep:
                    S.set(x, yy, z, DEEP.pick(x, yy, z))
    for x in (-59, -58, -57, -56, -55):
        for yy in range(f - 1, L1 - 1):
            if (x, yy, 45) not in S.keep:
                S.set(x, yy, 45, DEEP.pick(x, yy, 45))
    for (x, z) in ((-57, 26), (-57, 31)):
        S.set(x, f + 3, z, SOUL_H)


def eelwife(S):
    """The hut over the undercroft stair on the west street: its floor opens onto the stair, its iron door opens from
    inside only (a lever beside it)."""
    bp = S.bp
    x0, z0, x1, z1 = -62, 40, -52, 48
    f = L1
    S.check_box("eelwife", x0, f - 1, z0, x1, f + 9, z1, allow=set(rect(-58, 40, -56, 44)))
    S.claim(x0 - 1, z0 - 1, x1 + 1, z1 + 1)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            stairwell = -58 <= x <= -56 and z <= 44
            if not stairwell:
                S.set(x, f - 1, z, "dark_oak_planks" if edge else "spruce_planks")
            for y in range(f, f + 5):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    S.set(x, y, z, "dark_oak_log[axis=y]" if corner else
                          "stripped_dark_oak_wood[axis=y]" if y == f + 4 else
                          "mud_bricks" if y == f else INFILL.pick(x, y, z))
                elif y == f + 4 and (x - x0) % 2 == 0 and not stairwell:
                    S.set(x, y, z, "stripped_dark_oak_log[axis=z]")
                elif (x, y, z) not in S.keep or stairwell:
                    S.clear(x, y, z)
            if not edge and not stairwell:
                S.add_walk(x, z, f, pile=False)
    for (px, pz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), (-57, z1)):
        if pile_ok(S, px, pz, f - 2):
            pile(S, px, pz, f - 2)
    bp.gable_roof(x0, z0, x1, z1, f + 5, "dark_oak_stairs", ridge_axis="x", overhang=1, fill="dark_oak_planks")
    # rails round the stairwell
    for z in range(40, 45):
        for x in (-59, -55):
            if not (x0 < x < x1 and z0 < z < z1):
                continue
            if z == 44 or True:
                pass
    for x in (-59, -55):
        for z in range(41, 45):
            S.set(x, f, z, "spruce_fence")
            S.keep.discard((x, f, z))
    # the iron door east onto the walk to the west street, a lever inside
    S.clear(x1, f, 44)
    S.clear(x1, f + 1, 44)
    S.set(x1, f - 1, 44, "dark_oak_planks")
    bp.door(x1, f, 44, "east", wood="iron")
    S.add_walk(x1, 44, f, pile=False)
    S.set(x1 - 1, f + 1, 45, with_props("lever", face="wall", facing="west", powered=False))
    S.set(x1, f + 1, 45, INFILL.pick(x1, f + 1, 45))
    S.keep.discard((x1 - 1, f + 1, 45))
    # glass, a lamp, nets and barrels
    for (x, z) in ((x0, 43), (x0, 46), (-60, z1), (-54, z1), (-60, z0)):
        S.set(x, f + 1, z, "glass_pane")
        S.set(x, f + 2, z, "glass_pane")
    S.set(-60, f + 3, 46, LANT_H)
    bp.barrel(x0 + 1, f, z1 - 1, "up")
    bp.barrel(x0 + 1, f, z1 - 2, "up")
    S.set(x1 - 1, f, z1 - 1, "cauldron")


# ------------------------------------------------------------------ builder
def mire_stilt_city(bp):
    S = Site(bp)
    bog(S)
    walkways(S)
    landing(S)
    gate(S)
    bell_tower(S)
    undercroft(S)
    eelwife(S)
    ladderhouse(S)
    hub(S)
    smokehouse(S)
    high_walk(S)
    hall(S)
    vault(S)
    sumps(S)
    piles(S)
    rails(S)
    bp.mist(-1, HALL_F, -56, 1, HALL_F + 3, -56)
    trees(S)
    bog_after(S)
    S.bp._mire_warn = S.warn


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("causeway", (0, L1, 98), (0, 50, -74)),
    ("eel_market", (-12, L1, 63), (6, L1 + 3, 52)),
    ("market_hub", (-14, L2, 16), (0, 45, -74)),
    ("smokehouse", (64, L2, 7), (54, L2 + 6, 0)),
    ("high_walk", (57, L3, -28), (0, 50, -74)),
    ("undercroft", (-57, UND_F, 3), (-57, UND_F + 3, 18)),
    ("queen_hall", (0, HALL_F, -60), (0, HALL_F + 6, -88)),
]


register(StructureDef(
    "mire_stilt_city", "overworld", ["swamp", "mangrove_swamp"],
    [Piece("city", mire_stilt_city, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[("minecraft:drowned", 5, 1, 2), ("minecraft:bogged", 3, 1, 2), ("minecraft:witch", 1, 1, 1)],
    title_fr="La Cité des pilotis", title_en="Mire Stilt-City"))
