"""Lair of the Sand Pharaoh, under the Desert Oasis.

The oasis already hides a tomb (the burial chamber at y -16..-7 under the domed hall, see ``oasis`` in
overworld_b.py). This module digs two levels deeper:

* **Level 2 (floor y -28)**: a grand stair leaves the burial chamber through its south wall and dives into a
  painted **hypostyle hall** (papyrus columns under a night sky of gold stars). West of it, the **gallery of the
  embalmed** (burial niches, canopic jars, a skeleton spawner) ends at the **Well of Souls**, a round shaft with a
  spiral stair. East of it, a **collapsed gallery** half buried in sand (husk spawner) hides the top of a shortcut
  shaft that comes up from the reward vault.
* **Level 3 (floor y -48)**: at the bottom of the well, a corridor leads to the **site of grace** (waystone,
  benches, candles), then through the mist into the **great burial hall** (33 x 33, 17 high): a peristyle of
  lotus columns, two seated colossi flanking the dais where the Pharaoh's open sarcophagus lies, a starry ceiling.
  Past the east mist, the **treasure vault** and the ladder back up to level 2.
"""
import math
import random

from ..arch import Palette, stair
from ..parts import LOOT, MOD

AIR = "air"
WALL = Palette({"sandstone": 4, "smooth_sandstone": 2, "cut_sandstone": 2}, seed=81, scale=2.5)
FLOOR = Palette({"smooth_sandstone": 3, "cut_sandstone": 2, "sandstone": 1}, seed=82, scale=2.0)
CUT, CHI, SMOOTH = "cut_sandstone", "chiseled_sandstone", "smooth_sandstone"
GOLD, LAPIS = "gold_block", "lapis_block"
GLYPHS = ("orange_glazed_terracotta[facing=north]", "blue_glazed_terracotta[facing=east]",
          "light_blue_glazed_terracotta[facing=south]", "yellow_glazed_terracotta[facing=west]")
STAR = "ochre_froglight[axis=y]"

L2 = -27          # walking level of the hypostyle and the galleries (floor blocks at y -28)
L3 = -47          # walking level of the arena and the grace (floor blocks at y -48)
AX, AZ, AR = 0, -12, 16   # arena centre and half size (interior x -16..16, z -28..4)
AH = 17           # arena interior height (y -47..-31)


def build(bp):
    rng = random.Random(41)
    _grand_stair(bp)
    _hypostyle(bp, rng)
    _west_gallery(bp, rng)
    _well(bp)
    _east_gallery(bp, rng)
    _grace(bp)
    _arena(bp, rng)
    _vault(bp, rng)
    _mists(bp)


# ------------------------------------------------------------------ helpers
def _box(bp, x0, y0, z0, x1, y1, z1, wall=WALL, floor=None, ceiling=None):
    """Hollow room: walls from the palette, interior cleared to air (x0..x1 etc. are the wall planes)."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(y0, y1 + 1):
                if y == y0:
                    bp.set(x, y, z, floor.pick(x, y, z) if isinstance(floor, Palette) else (floor or wall.pick(x, y, z)))
                elif y == y1:
                    bp.set(x, y, z, ceiling or CUT)
                elif edge:
                    bp.set(x, y, z, wall.pick(x, y, z))
                else:
                    bp.set(x, y, z, AIR)


def _frieze(bp, x0, z0, x1, z1, y, seed=0):
    """A painted register along the inner face of a room's walls (x0..x1, z0..z1 are the wall planes)."""
    k = seed
    for x in range(x0 + 1, x1):
        for z in (z0, z1):
            bp.set(x, y, z, GLYPHS[(x + k) % 4] if x % 3 else CHI)
    for z in range(z0 + 1, z1):
        for x in (x0, x1):
            bp.set(x, y, z, GLYPHS[(z + k) % 4] if z % 3 else CHI)


def _band(bp, x0, z0, x1, z1, y, block):
    for x in range(x0 + 1, x1):
        for z in (z0, z1):
            bp.set(x, y, z, block)
    for z in range(z0 + 1, z1):
        for x in (x0, x1):
            bp.set(x, y, z, block)


def _star_ceiling(bp, x0, z0, x1, z1, y, seed=0):
    """The sky goddess's ceiling: deep blue with gold stars; some stars glow (they light the room)."""
    rng = random.Random(seed)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            r = rng.random()
            bp.set(x, y, z, STAR if r < 0.035 else "yellow_terracotta" if r < 0.09 else
                   LAPIS if (x * 3 + z) % 11 == 0 else "blue_terracotta")


def _column(bp, x, z, y0, y1, seed=0):
    """A papyrus column (plus-shaped shaft, painted rings) with a flaring lotus capital and an abacus."""
    for y in range(y0, y1 + 1):
        top = y1 - y
        if top == 0:
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    bp.set(x + dx, y, z + dz, CUT)
        elif top <= 2:
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) <= 3:
                        edge = max(abs(dx), abs(dz)) == 2
                        bp.set(x + dx, y, z + dz, ("lime_terracotta" if (dx + dz) % 2 else "blue_terracotta")
                               if edge and top == 1 else CHI if edge else SMOOTH)
        else:
            ring = (y - y0) % 5 == 0 or y == y0
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if abs(dx) + abs(dz) <= 1 or y == y0:
                        if ring:
                            b = CUT if y == y0 else ("blue_terracotta" if (y + seed) % 2 else "orange_terracotta")
                        else:
                            b = SMOOTH if abs(dx) + abs(dz) == 0 else ("smooth_sandstone" if (y + dx + dz) % 7 else CHI)
                        bp.set(x + dx, y, z + dz, b)


def _stair_down(bp, x0, x1, z_start, y_top, n, direction, block="sandstone_stairs"):
    """A stair of n steps descending one block per step toward ``direction`` (south/east/...), cleared above,
    walled at both sides. y_top is the y of the first stair block."""
    dx, dz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[direction]
    up = {"south": "north", "north": "south", "east": "west", "west": "east"}[direction]
    for i in range(n):
        y = y_top - i
        for w in range(x0, x1 + 1):
            if dz:
                x, z = w, z_start + dz * i
            else:
                x, z = z_start + dx * i, w
            bp.set(x, y, z, stair(block, up))
            bp.set(x, y - 1, z, "sandstone")
            for c in range(1, 5):
                bp.set(x, y + c, z, AIR)
            bp.set(x, y + 5, z, CUT)
        for side in (x0 - 1, x1 + 1):
            x, z = (side, z_start + dz * i) if dz else (z_start + dx * i, side)
            for yy in range(y - 1, y + 6):
                bp.set(x, yy, z, CHI if (yy - y) == 3 and i % 3 == 1 else CUT)


# ------------------------------------------------------------------ level 1 -> 2: the grand stair
def _grand_stair(bp):
    # the burial chamber's south wall (z -16) opens under a lintel guarded by two jackal statues
    bp.clear(-1, -15, -16, 1, -12, -16)
    for x in (-2, 2):
        bp.fill(x, -15, -16, x, -11, -16, CHI)
    for x in range(-2, 3):
        bp.set(x, -11, -16, GOLD if x == 0 else CUT)
    for sx in (-4, 4):                         # recumbent jackals (Anubis) on plinths in the chamber
        bp.fill(sx, -15, -17, sx, -15, -19, CUT)
        bp.set(sx, -14, -19, "black_terracotta")
        bp.set(sx, -14, -18, "black_terracotta")
        bp.set(sx, -13, -18, "black_terracotta")
        bp.set(sx, -12, -18, stair("blackstone_stairs", "north"))
        bp.set(sx, -13, -17, "gold_block")
        bp.set(sx, -14, -17, stair("blackstone_stairs", "north"))
    _stair_down(bp, -1, 1, -15, -16, 12, "south")
    for i in (2, 6, 10):
        bp.lantern(0, -16 - i + 4, -15 + i, hanging=True)


# ------------------------------------------------------------------ level 2: hypostyle hall
def _hypostyle(bp, rng):
    x0, x1, z0, z1 = -14, 14, -3, 19
    y0, y1 = L2 - 1, L2 + 9
    _box(bp, x0, y0, z0, x1, y1, z1, floor=FLOOR)
    bp.clear(-1, L2, z0, 1, L2 + 3, z0)                                   # from the grand stair
    _star_ceiling(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, y1, seed=5)
    _band(bp, x0, z0, x1, z1, L2 + 1, "orange_terracotta")
    _frieze(bp, x0, z0, x1, z1, L2 + 3, seed=1)
    _band(bp, x0, z0, x1, z1, L2 + 5, "blue_terracotta")
    _frieze(bp, x0, z0, x1, z1, L2 + 6, seed=2)
    _band(bp, x0, z0, x1, z1, L2 + 8, "yellow_terracotta")
    # processional way: lapis and gold inlay down the central aisle
    for z in range(z0 + 1, z1):
        bp.set(0, y0, z, GOLD if z % 4 == 0 else LAPIS)
        for x in (-1, 1):
            bp.set(x, y0, z, CHI)
    for x in (-10, -5, 5, 10):
        for z in (2, 8, 14):
            _column(bp, x, z, L2, y1 - 1, seed=x + z)
    # wall torches between the columns, braziers on pedestals along the aisle
    for z in (5, 11, 17):
        for x, f in ((x0 + 1, "east"), (x1 - 1, "west")):
            bp.wall_torch(x, L2 + 4, z, f)
    for z in (5, 11):
        for x in (-3, 3):
            bp.set(x, L2, z, CHI)
            bp.set(x, L2 + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the shrine at the south end: a golden statue of the jackal god over an offering table
    bp.fill(-4, L2, z1 - 3, 4, L2, z1 - 1, CUT)
    bp.fill(-3, L2 + 1, z1 - 2, 3, L2 + 1, z1 - 1, SMOOTH)
    bp.fill(-1, L2 + 2, z1 - 1, 1, L2 + 2, z1 - 1, "black_terracotta")
    bp.set(0, L2 + 3, z1 - 1, "black_terracotta")
    bp.set(0, L2 + 4, z1 - 1, "black_terracotta")
    bp.set(-1, L2 + 5, z1 - 1, stair("blackstone_stairs", "south"))
    bp.set(1, L2 + 5, z1 - 1, stair("blackstone_stairs", "south"))
    bp.set(0, L2 + 4, z1 - 2, stair("blackstone_stairs", "south"))
    bp.set(0, L2 + 3, z1 - 2, GOLD)
    bp.chest(0, L2 + 1, z1 - 3, "north", LOOT + "desert_tomb")
    for x in (-3, 3):
        bp.set(x, L2 + 2, z1 - 2, "candle[candles=4,lit=true,waterlogged=false]")
        bp.set(x, L2 + 1, z1 - 3, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    bp.spawner(0, L2, 9, "minecraft:husk")
    # doors to the two galleries
    for x in (x0, x1):
        bp.clear(x, L2, 7, x, L2 + 3, 9)
        for z in (6, 10):
            bp.fill(x, L2, z, x, L2 + 4, z, CHI)
        bp.fill(x, L2 + 4, 6, x, L2 + 4, 10, CUT)
    # sand drifted in through the cracks, a few broken pots
    for _ in range(26):
        x, z = rng.randint(x0 + 1, x1 - 1), rng.randint(z0 + 1, z1 - 1)
        if bp.get(x, L2, z) == "minecraft:air" and abs(x) > 1:
            bp.set(x, L2, z, "sand" if rng.random() < 0.7 else "decorated_pot[facing=south,waterlogged=false,cracked=true]")


# ------------------------------------------------------------------ level 2 west: the gallery of the embalmed
def _west_gallery(bp, rng):
    x0, x1, z0, z1 = -34, -14, 3, 13
    _box(bp, x0, L2 - 1, z0, x1, L2 + 6, z1, floor=FLOOR)
    bp.clear(x1, L2, 7, x1, L2 + 3, 9)
    _frieze(bp, x0, z0, x1, z1, L2 + 4, seed=3)
    _star_ceiling(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L2 + 6, seed=12)
    # burial niches in both long walls: each holds a wrapped body on a bier
    for x in range(x0 + 3, x1 - 1, 3):
        for z, out in ((z0, -1), (z1, 1)):
            bp.set(x, L2, z, CUT)
            bp.clear(x, L2 + 1, z, x, L2 + 2, z)
            for xx in (x - 1, x + 1):
                bp.set(xx, L2 + 1, z, CHI)
            bp.set(x, L2 + 3, z, CUT)
            bp.set(x, L2 + 1, z + out, "white_wool" if rng.random() < 0.6 else "bone_block[axis=x]")
            bp.set(x, L2 + 2, z + out, CUT)
            bp.set(x, L2 + 1, z, "skeleton_skull[powered=false,rotation=%d]" % (8 if out < 0 else 0)
                   if rng.random() < 0.35 else "air")
    # canopic jars and embalming tables down the middle
    for x in (-30, -24, -18):
        bp.set(x, L2, 8, SMOOTH)
        bp.set(x, L2 + 1, 8, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
        for dz in (-2, 2):
            bp.set(x, L2, 8 + dz, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    for x in (-28, -21):
        bp.lantern(x, L2 + 5, 8, hanging=True, soul=True)
        bp.chain(x, L2 + 5, 8, L2 + 5)
        bp.lantern(x, L2 + 4, 8, hanging=True, soul=True)
    bp.set(-27, L2, 5, "cobweb")
    bp.set(-17, L2 + 3, 12, "cobweb")
    bp.spawner(-24, L2, 11, "minecraft:skeleton")
    bp.barrel(-32, L2, 12, "up", LOOT + "desert_tomb")
    # the way on: an arch in the west wall to the Well of Souls
    bp.clear(x0, L2, 7, x0, L2 + 3, 9)
    bp.fill(x0, L2 + 4, 6, x0, L2 + 4, 10, GOLD)


# ------------------------------------------------------------------ the Well of Souls: spiral stair to level 3
def _well(bp):
    cx, cz, R = -40, 8, 5
    for y in range(L3 - 1, L2 + 9):
        for x in range(cx - R - 1, cx + R + 2):
            for z in range(cz - R - 1, cz + R + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= R + 0.5:
                    if y in (L3 - 1, L2 + 8):
                        bp.set(x, y, z, CHI if d < 1.5 else "blue_terracotta" if d < R - 1.5 else CUT)
                    elif d > R - 0.5:
                        bp.set(x, y, z, "orange_terracotta" if y % 6 == 0 else WALL.pick(x, y, z))
                    else:
                        bp.set(x, y, z, AIR)
    # floor ring at level 2 joins the gallery door, the stair winds down around a carved pillar
    bp.clear(cx + R, L2, 7, cx + R + 1, L2 + 3, 9)
    for x in range(cx + 2, cx + R):
        for z in range(7, 10):
            bp.set(x, L2 - 1, z, CUT)
    # a helix of slabs (half a block per step) that starts right at the landing and winds down clockwise
    ring = sorted(((x, z) for x in range(cx - 3, cx + 4) for z in range(cz - 3, cz + 4)
                   if max(abs(x - cx), abs(z - cz)) == 3), key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    i = ring.index((cx + 3, cz - 2))
    half = 2 * L2                       # walking surface in half blocks
    while half > 2 * L3:
        x, z = ring[i % len(ring)]
        y = (half - 1) // 2
        bp.slab(x, y, z, "smooth_sandstone_slab", "top" if half % 2 == 0 else "bottom")
        half -= 1
        i -= 1
    for y in range(L3, L2 + 8):
        bp.set(cx, y, cz, CHI if y % 4 == 0 else "sandstone")
        if y % 5 == 0:
            for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
                bp.wall_torch(cx + dx, y + 1, cz + dz, f, soul=True)
    for y in range(L3 + 2, L2 + 6, 6):
        for dx, dz in ((R - 1, 0), (-R + 1, 0), (0, R - 1), (0, -R + 1)):
            bp.set(cx + dx, y - 1, cz + dz, CHI)                  # corbel under each lantern
            bp.lantern(cx + dx, y, cz + dz, soul=False)
    # the bottom opens north toward the grace
    _box(bp, -42, L3 - 1, -6, -38, L3 + 4, cz - R)
    bp.clear(-41, L3, -6, -39, L3 + 3, cz - R)
    for z in range(-5, cz - R, 3):
        bp.lantern(-40, L3 + 3, z, hanging=True)


# ------------------------------------------------------------------ level 2 east: the collapsed gallery
def _east_gallery(bp, rng):
    x0, x1, z0, z1 = 14, 33, 3, 13
    _box(bp, x0, L2 - 1, z0, x1, L2 + 6, z1, floor=FLOOR)
    bp.clear(x0, L2, 7, x0, L2 + 3, 9)
    _frieze(bp, x0, z0, x1, z1, L2 + 3, seed=4)
    # the ceiling gave way at the far end: a dune of sand and fallen blocks fills it
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            h = int((x - 20) * 0.45 + 1.4 * math.sin(z * 0.9) - 1)
            for y in range(L2, L2 + max(0, min(5, h))):
                bp.set(x, y, z, "sand" if rng.random() < 0.85 else "sandstone")
            if x > 24 and rng.random() < 0.25:
                bp.set(x, L2 + 6, z, "sand")
    for (x, z) in ((25, 5), (29, 11), (22, 10)):
        bp.set(x, L2 + 5, z, "suspicious_sand", {"LootTable": "minecraft:archaeology/desert_pyramid"})
    for x in range(x0 + 2, 22, 3):
        bp.set(x, L2, z0 + 1, "decorated_pot[facing=south,waterlogged=false,cracked=true]")
    bp.spawner(19, L2, 8, "minecraft:husk")
    bp.lantern(18, L2 + 5, 8, hanging=True)
    # dug through the dune: the shortcut tunnel from the vault ladder (north wall, x 26..28)
    for x in range(26, 29):
        for z in range(z0 + 1, 8):
            for y in range(L2, L2 + 3):
                bp.set(x, y, z, AIR)
    bp.clear(26, L2, z0, 28, L2 + 2, z0)
    bp.set(27, L2 + 3, z0, CHI)
    for (x, z) in ((25, 5), (29, 5)):
        bp.fill(x, L2, z, x, L2 + 2, z, "stripped_jungle_log[axis=y]")        # timbering of the tunnel
    bp.fill(25, L2 + 3, 5, 29, L2 + 3, 5, "stripped_jungle_log[axis=x]")


# ------------------------------------------------------------------ level 3: site of grace
def _grace(bp):
    x0, x1, z0, z1 = -37, -24, -18, -6
    _box(bp, x0, L3 - 1, z0, x1, L3 + 6, z1, floor=FLOOR)
    _star_ceiling(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L3 + 6, seed=9)
    _frieze(bp, x0, z0, x1, z1, L3 + 3, seed=5)
    _band(bp, x0, z0, x1, z1, L3 + 1, "orange_terracotta")
    # joined to the well corridor (x -41..-39 at z -6) through the south-west corner
    for x in range(-39, x0 + 1):
        for z in range(-8, -5):
            for y in range(L3, L3 + 4):
                bp.set(x, y, z, AIR)
            bp.set(x, L3 - 1, z, CUT)
            bp.set(x, L3 + 4, z, CUT)
    bp.set(x0, L3 + 4, -7, GOLD)
    # the waystone on a dais, benches and candles: rest before the mist
    cx, cz = -31, -12
    bp.fill(cx - 2, L3 - 1, cz - 2, cx + 2, L3 - 1, cz + 2, CHI)
    bp.set(cx, L3 - 1, cz, GOLD)
    bp.set(cx, L3, cz, MOD["waystone"])
    for (x, z) in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
        bp.set(x, L3, z, "sandstone_wall")
        bp.set(x, L3 + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    for z in range(cz - 2, cz + 3):
        bp.stairs(x0 + 1, L3, z, "smooth_sandstone_stairs", "east")
    for x in range(cx - 2, cx + 3):
        bp.stairs(x, L3, z0 + 1, "smooth_sandstone_stairs", "south")
    bp.lantern(cx, L3 + 5, cz, hanging=True)
    bp.chain(cx, L3 + 5, cz, L3 + 5)
    bp.lantern(cx, L3 + 4, cz, hanging=True)
    for (x, z) in ((x0 + 1, z0 + 1), (x1 - 1, z1 - 1)):
        bp.set(x, L3, z, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    bp.wall_torch(x1 - 1, L3 + 2, -15, "west")
    bp.wall_torch(x1 - 1, L3 + 2, -9, "west")
    # the processional corridor to the burial hall (east), ending at the mist
    for x in range(x1, AX - AR - 1):
        for z in range(AZ - 1, AZ + 2):
            bp.set(x, L3 - 1, z, LAPIS if z == AZ and x % 2 == 0 else CUT)
            for y in range(L3, L3 + 5):
                bp.set(x, y, z, AIR)
            bp.set(x, L3 + 5, z, CUT)
        for z in (AZ - 2, AZ + 2):
            for y in range(L3 - 1, L3 + 6):
                bp.set(x, y, z, CHI if y == L3 + 2 else CUT)
    for x in (x1 + 1, AX - AR - 3):
        bp.wall_torch(x, L3 + 3, AZ - 1, "south")
        bp.wall_torch(x, L3 + 3, AZ + 1, "north")


# ------------------------------------------------------------------ level 3: the great burial hall (arena)
def _arena(bp, rng):
    x0, x1, z0, z1 = AX - AR - 2, AX + AR + 2, AZ - AR - 2, AZ + AR + 2
    yb, yt = L3 - 1, L3 + AH
    # thick walls (2 blocks), floor, ceiling
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            inner = AX - AR <= x <= AX + AR and AZ - AR <= z <= AZ + AR
            for y in range(yb - 1, yt + 2):
                if y <= yb:
                    bp.set(x, y, z, FLOOR.pick(x, y, z) if y == yb else "sandstone")
                elif y >= yt:
                    bp.set(x, y, z, CUT if y == yt + 1 else "blue_terracotta")
                elif inner:
                    bp.set(x, y, z, AIR)
                else:
                    bp.set(x, y, z, WALL.pick(x, y, z))
    # floor: a great sun disc of gold and lapis rays around the seal, framed by glyph tiles
    for x in range(AX - AR, AX + AR + 1):
        for z in range(AZ - AR, AZ + AR + 1):
            d = math.hypot(x - AX, z - AZ)
            a = math.degrees(math.atan2(z - AZ, x - AX)) % 360
            if d < 1.5:
                b = CHI
            elif d < 3.5:
                b = GOLD if d < 2.5 else "orange_terracotta"
            elif d < 9.5:
                b = ("yellow_terracotta" if int(a // 15) % 2 else "smooth_sandstone") if d > 4.5 else LAPIS
            elif 9.5 <= d < 10.5:
                b = GOLD if int(a // 10) % 3 == 0 else CUT
            elif max(abs(x - AX), abs(z - AZ)) >= AR - 1:
                b = GLYPHS[(x + z) % 4]
            else:
                b = FLOOR.pick(x, yb, z)
            bp.set(x, yb, z, b)
    _star_ceiling(bp, AX - AR, AZ - AR, AX + AR, AZ + AR, yt, seed=17)
    # wall paintings: registers of glyphs, lapis and orange bands, pilasters between them
    ix0, ix1, iz0, iz1 = AX - AR - 1, AX + AR + 1, AZ - AR - 1, AZ + AR + 1
    _band(bp, ix0, iz0, ix1, iz1, L3, CUT)
    _band(bp, ix0, iz0, ix1, iz1, L3 + 1, "orange_terracotta")
    _frieze(bp, ix0, iz0, ix1, iz1, L3 + 3, seed=6)
    _frieze(bp, ix0, iz0, ix1, iz1, L3 + 4, seed=7)
    _band(bp, ix0, iz0, ix1, iz1, L3 + 6, "blue_terracotta")
    _band(bp, ix0, iz0, ix1, iz1, L3 + 7, GOLD)
    _frieze(bp, ix0, iz0, ix1, iz1, L3 + 10, seed=8)
    _band(bp, ix0, iz0, ix1, iz1, L3 + 12, "blue_terracotta")
    _band(bp, ix0, iz0, ix1, iz1, AH + L3 - 1, "yellow_terracotta")
    # peristyle: lotus columns ringing the floor, the entrance axis (z = AZ) and the dais left clear
    for c in (-7, 7, 13):                         # (the colossi stand where the first pair would be)
        for side in (-1, 1):
            _column(bp, AX + side * 13, AZ + c, L3, yt - 1, seed=c)
    for c in (-7, 7):
        _column(bp, AX + c, AZ + 13, L3, yt - 1, seed=c + 3)
    # the dais (north): three steps up to the open sarcophagus, its lid thrown aside
    for k, (hw, zz) in enumerate(((7, AZ - 11), (6, AZ - 12), (5, AZ - 13))):
        for x in range(AX - hw, AX + hw + 1):
            for z in range(AZ - AR, zz + 1):
                bp.set(x, L3 + k, z, CHI if z == zz and x % 2 == 0 else CUT if k < 2 else SMOOTH)
            bp.set(x, L3 + k, zz, stair("smooth_sandstone_stairs", "south") if abs(x) < hw else CUT)
    sz = AZ - 15                                   # the empty sarcophagus lies across the dais top
    for x in range(AX - 3, AX + 4):
        for z in range(sz, sz + 3):
            edge = abs(x - AX) == 3 or z in (sz, sz + 2)
            bp.set(x, L3 + 3, z, GOLD if edge else "black_concrete")
            bp.set(x, L3 + 4, z, (LAPIS if abs(x - AX) == 3 else GOLD) if edge else AIR)
    for x in range(AX - 3, AX + 4):                # its lid, thrown down onto the step below
        bp.set(x, L3 + 2, sz + 3, stair("smooth_sandstone_stairs", "north", "top") if abs(x) == 3 else
               (GOLD if abs(x) == 2 else LAPIS if x % 2 else "orange_glazed_terracotta[facing=south]"))
    for x in (AX - 6, AX + 6):
        bp.set(x, L3 + 2, AZ - 13, CHI)
        bp.set(x, L3 + 3, AZ - 13, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    # two seated colossi flank the dais, their backs to the north wall
    for side in (-1, 1):
        _colossus(bp, AX + side * 10, AZ - AR, side)
    # light: lanterns hung on chains from the ceiling between the columns, braziers at the corners
    for (x, z) in ((-7, AZ - 7), (7, AZ - 7), (-7, AZ + 7), (7, AZ + 7)):
        bp.chain(x, yt - 5, z, yt - 1)
        bp.lantern(x, yt - 6, z, hanging=True)
    for (x, z) in ((AX - AR + 1, AZ + AR - 1), (AX + AR - 1, AZ + AR - 1)):
        bp.set(x, L3, z, CHI)
        bp.set(x, L3 + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for side in (-1, 1):
        for z in (AZ - 9, AZ - 3, AZ + 3, AZ + 9):
            x = AX + side * (AR + 1)
            bp.set(x, L3 + 5, z, STAR)
            bp.set(x, L3 + 9, z, STAR)
    # entrances (west from the grace, east to the vault): tall gold-framed portals
    for side in (-1, 1):
        xw = AX + side * (AR + 1)
        xo = AX + side * (AR + 2)
        for x in (xw, xo):
            bp.clear(x, L3, AZ - 1, x, L3 + 4, AZ + 1)
        for z in (AZ - 2, AZ + 2):
            bp.fill(xw, L3, z, xw, L3 + 5, z, GOLD)
        bp.fill(xw, L3 + 5, AZ - 2, xw, L3 + 5, AZ + 2, GOLD)
        bp.set(xw, L3 + 6, AZ, "orange_glazed_terracotta[facing=north]")
    bp.boss_seal(AX, L3 - 1, AZ, "brasshaven:sand_pharaoh", AR)


def _colossus(bp, cx, zb, side):
    """A seated pharaoh 15 blocks tall carved against the wall: throne, shins, crook and flail crossed on the chest,
    a broad collar, a striped nemes whose lappets fall on the shoulders, a gold mask with lapis eyes, a uraeus."""
    nemes = lambda y: "lapis_block" if y % 3 == 0 else "yellow_terracotta"
    # throne and shins (front face at zb + 6), the feet on a gold-banded plinth
    for x in range(cx - 4, cx + 5):
        for z in range(zb, zb + 7):
            for y in range(L3, L3 + 5):
                if abs(x - cx) == 4 and z > zb + 2:
                    continue
                if z >= zb + 4 and x == cx:
                    continue                                    # the gap between the shins
                bp.set(x, y, z, GOLD if y == L3 and z == zb + 6 else CHI if z == zb + 6 and y == L3 + 4 else
                       SMOOTH if z >= zb + 4 else CUT)
    # torso, shoulders and folded arms
    for x in range(cx - 4, cx + 5):
        for z in range(zb, zb + 4):
            for y in range(L3 + 5, L3 + 10):
                if abs(x - cx) == 4 and y < L3 + 8:
                    continue
                bp.set(x, y, z, SMOOTH)
    for k in range(5):                                          # crook and flail crossed on the chest
        bp.set(cx - 2 + k, L3 + 5 + k, zb + 4, GOLD if k != 2 else LAPIS)
        bp.set(cx + 2 - k, L3 + 5 + k, zb + 4, "blue_terracotta" if k % 2 else GOLD)
    bp.set(cx + 3, L3 + 9, zb + 4, GOLD)                        # the crook's hook over the shoulder
    bp.set(cx + 3, L3 + 10, zb + 4, GOLD)
    for x in range(cx - 4, cx + 5):                             # broad collar
        bp.set(x, L3 + 9, zb + 4, ("blue_terracotta" if (x + side) % 2 else "orange_terracotta")
               if abs(x - cx) < 3 else "light_blue_terracotta")
        bp.set(x, L3 + 8, zb + 4, GOLD if abs(x - cx) >= 3 else bp.get(x, L3 + 8, zb + 4) or GOLD)
    # head: nemes with lappets, a gold mask with lapis eyes
    for x in range(cx - 4, cx + 5):
        for z in range(zb, zb + 4):
            for y in range(L3 + 10, L3 + 16):
                if abs(x - cx) == 4 and y > L3 + 12:
                    continue
                if abs(x - cx) == 3 and y > L3 + 14:
                    continue
                bp.set(x, y, z, nemes(y))
    for x in range(cx - 2, cx + 3):
        for y in range(L3 + 10, L3 + 15):
            bp.set(x, y, zb + 4, GOLD)
    for dx in (-1, 1):
        bp.set(cx + dx, L3 + 13, zb + 4, LAPIS)
    bp.set(cx, L3 + 12, zb + 5, stair("smooth_sandstone_stairs", "south"))
    bp.set(cx, L3 + 11, zb + 4, "orange_terracotta")
    for y in (L3 + 9, L3 + 10):                                  # the braided beard
        bp.set(cx, y, zb + 5, "blue_terracotta")
    bp.set(cx, L3 + 15, zb + 4, GOLD)
    bp.set(cx, L3 + 16, zb + 4, LAPIS)                           # uraeus


# ------------------------------------------------------------------ level 3 east: the treasure vault and the way up
def _vault(bp, rng):
    x0, x1, z0, z1 = AX + AR + 2, AX + AR + 13, AZ - 5, AZ + 5
    _box(bp, x0, L3 - 1, z0, x1, L3 + 6, z1, floor=FLOOR)
    _star_ceiling(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L3 + 6, seed=23)
    _frieze(bp, x0, z0, x1, z1, L3 + 3, seed=9)
    bp.clear(x0, L3, AZ - 1, x0, L3 + 4, AZ + 1)
    # heaps of gold around the reward
    for (x, z) in ((x1 - 2, z0 + 1), (x1 - 1, z0 + 1), (x1 - 1, z0 + 2), (x0 + 2, z1 - 1), (x0 + 3, z1 - 1), (x1 - 1, z1 - 2)):
        bp.set(x, L3, z, rng.choice(["gold_block", "raw_gold_block", "gold_block"]))
    bp.fill(x1 - 3, L3, AZ - 1, x1 - 1, L3, AZ + 1, CHI)
    bp.chest(x1 - 2, L3 + 1, AZ, "west", LOOT + "desert_tomb_secret")
    bp.chest(x1 - 2, L3 + 1, AZ - 1, "west", LOOT + "desert_tomb")
    bp.set(x1 - 2, L3 + 1, AZ + 1, GOLD)
    for z in (z0 + 1, z1 - 1):
        bp.set(x0 + 5, L3, z, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    bp.lantern(x0 + 5, L3 + 5, AZ, hanging=True)
    # the ladder shaft in the north-east corner climbs back to the collapsed gallery (shortcut)
    lx, lz = 27, -8                                # ladder against the vault's south wall, open on the vault side
    for y in range(L3 + 6, L2 - 1):
        for x in range(lx - 1, lx + 2):
            for z in range(lz - 1, lz + 2):
                if (x, z) != (lx, lz):
                    bp.set(x, y, z, CUT)
        bp.set(lx, y, lz, AIR)
    bp.ladder(lx, L3, lz, L2 - 2, "north")
    bp.set(lx, L3 + 5, lz - 1, CHI)                # mark the ladder's head in the vault
    # corridor at level 2 from the shaft top to the gallery tunnel
    for x in range(25, 30):
        for z in range(lz - 1, 4):
            for y in range(L2 - 1, L2 + 4):
                edge = x in (25, 29) or z == lz - 1
                bp.set(x, y, z, CUT if edge or y in (L2 - 1, L2 + 3) else AIR)
    bp.set(lx, L2 - 1, lz, "jungle_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.lantern(27, L2 + 2, -2, hanging=True)


# ------------------------------------------------------------------ the mist (after every doorway is carved)
def _mists(bp):
    for side in (-1, 1):
        x = AX + side * (AR + 1)
        bp.mist(x, L3, AZ - 1, x, L3 + 4, AZ + 1)
