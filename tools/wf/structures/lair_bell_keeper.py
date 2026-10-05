"""Lair of the Bell Keeper, under the Mountain Monastery.

The monks' crypt (inside the raised terrace) opens on a stair that goes down two levels:

* level 1, the catacombs (floor y = L1): an ossuary of bone niches, the gallery of monk tombs and a chapel
  whose vault has partly collapsed;
* from the chapel, the long stair falls to level 2 (floor y = L2): a candle-lit site of grace with a waystone,
  then the bell chamber, a domed rotunda (radius AR) under a giant cracked bronze bell hanging from a broken
  headstock beam; the Bell Keeper's seal lies in its centre;
* past the arena, the bell-founders' vault holds the reward.

Every room is a solid shell carved hollow (the rooms are underground: nothing may be left to the terrain), so
shells are laid first, interiors cleared next, then doors, furniture and lights. The generic helpers at the top
(shells, vaults, stairways, lights) are reused by the Archivist's lair.
"""
import math
import random

from .. import arch as A
from ..arch import Palette
from ..blueprint import OPPOSITE
from ..parts import LOOT, MOB, MOD

L1 = -11                  # catacombs floor (feet at L1 + 1)
L2 = -30                  # bell chamber floor
ARENA = (36, 49)          # bell chamber centre (x, z)
AR = 15                   # clear floor radius
WALL_TOP = L2 + 13        # the drum wall springs the dome here
DOME = 11                 # dome rise above the drum
STAIR_Z = 31              # the long stair: one step per block of z from the chapel door...
STAIR_END = STAIR_Z + (L1 - L2) - 1   # ...down to the last step above the site of grace floor
GRACE = (54, ARENA[1] - 4, 66, ARENA[1] + 10)   # site of grace shell x0, z0, x1, z1

WALL = Palette({"stone_bricks": 5, "cracked_stone_bricks": 2, "mossy_stone_bricks": 1, "tuff_bricks": 2,
                "andesite": 1}, seed=501, scale=2.0)
FLOOR = Palette({"polished_andesite": 3, "stone_bricks": 2, "cracked_stone_bricks": 1, "andesite": 1}, seed=502,
                scale=1.5)
DEEP = Palette({"deepslate_bricks": 5, "cracked_deepslate_bricks": 2, "deepslate_tiles": 2, "polished_deepslate": 1},
               seed=503, scale=2.0)
COLUMN = Palette({"calcite": 3, "polished_diorite": 1}, seed=504)
RUBBLE = ("cobblestone", "mossy_cobblestone", "stone_bricks", "cracked_stone_bricks", "andesite", "gravel", "tuff")
BRONZE = Palette({"waxed_cut_copper": 4, "waxed_exposed_cut_copper": 2, "waxed_weathered_cut_copper": 1},
                 seed=505, scale=1.5)
TRIM = "chiseled_stone_bricks"
TS = "stone_brick_stairs"
DS = "deepslate_brick_stairs"
CANDLE = "candle[candles=%d,lit=true,waterlogged=false]"
BULB = "waxed_copper_bulb[lit=true,powered=false]"


# ======================================================================== generic helpers (also used by
# lair_archivist)
def solid(bp, x0, y0, z0, x1, y1, z1, pal):
    A.fill_pal(bp, x0, y0, z0, x1, y1, z1, pal)


def hollow(bp, x0, y0, z0, x1, y1, z1, wall, floor=None):
    """A room as a solid shell carved hollow: walls/ceiling from ``wall``, the floor layer y0 from ``floor``."""
    solid(bp, x0, y0, z0, x1, y1, z1, wall)
    bp.clear(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1)
    if floor:
        solid(bp, x0 + 1, y0, z0 + 1, x1 - 1, y0, z1 - 1, floor)


def cove(bp, x0, z0, x1, z1, y, st):
    """Cornice of upside-down stairs along the inner edges of a room (x0..x1, z0..z1 = interior)."""
    for x in range(x0, x1 + 1):
        bp.set(x, y, z0, A.stair(st, "north", "top"))
        bp.set(x, y, z1, A.stair(st, "south", "top"))
    for z in range(z0 + 1, z1):
        bp.set(x0, y, z, A.stair(st, "west", "top"))
        bp.set(x1, y, z, A.stair(st, "east", "top"))


def rib(bp, axis, line, a0, a1, y, block, st):
    """Transverse arch across a room: a beam at y with stair haunches one row lower at both ends.
    axis='x': the rib spans x a0..a1 at z=line; axis='z': it spans z a0..a1 at x=line."""
    for a in range(a0, a1 + 1):
        p = (a, y, line) if axis == "x" else (line, y, a)
        bp.set(*p, block)
    lo, hi = ("west", "east") if axis == "x" else ("north", "south")
    for a, f in ((a0, lo), (a1, hi)):
        p = (a, y - 1, line) if axis == "x" else (line, y - 1, a)
        bp.set(*p, A.stair(st, f, "top"))


def opening(bp, x0, y0, z0, x1, y1, z1, frame=None, frame_st=None, axis="x"):
    """Doorway: clears the box; with ``frame`` adds a pointed head (stairs) over the top row.
    axis: the direction the doorway spans ('x' = wide along x, in a wall at constant z)."""
    bp.clear(x0, y0, z0, x1, y1, z1)
    if frame is None:
        return
    if axis == "x":
        for z in range(z0, z1 + 1):
            bp.set(x0, y1, z, A.stair(frame_st, "west", "top"))
            bp.set(x1, y1, z, A.stair(frame_st, "east", "top"))
            for x in range(x0, x1 + 1):
                bp.set(x, y1 + 1, z, frame)
    else:
        for x in range(x0, x1 + 1):
            bp.set(x, y1, z0, A.stair(frame_st, "north", "top"))
            bp.set(x, y1, z1, A.stair(frame_st, "south", "top"))
            for z in range(z0, z1 + 1):
                bp.set(x, y1 + 1, z, frame)


def stairway(bp, steps, facing, spec, shell, head=4, side=None):
    """A flight of stairs: ``steps`` = [(x, y, z), ...] stair blocks; each gets solid fill below (down to y-2),
    ``head`` air blocks above, a ceiling of ``shell`` above that, and ``side`` = (dx, dz) walls beside."""
    for (x, y, z) in steps:
        for yy in range(y - 2, y):
            bp.set(x, yy, z, shell.pick(x, yy, z))
        bp.stairs(x, y, z, spec, facing)
        bp.clear(x, y + 1, z, x, y + head, z)
        bp.set(x, y + head + 1, z, shell.pick(x, y + head + 1, z))


def candles(bp, pts, seed=0):
    rng = random.Random(seed)
    for (x, y, z) in pts:
        bp.set(x, y, z, CANDLE % rng.randint(2, 4))


def hang(bp, x, y_ceiling, z, length, soul=False):
    """Lantern hanging on a chain from the ceiling block at y_ceiling."""
    bp.chain(x, y_ceiling - length, z, y_ceiling - 1)
    bp.lantern(x, y_ceiling - length - 1, z, hanging=True, soul=soul)


# ======================================================================== the lair
def build(bp):
    """Called at the end of the monastery builder."""
    descent(bp)
    ossuary(bp)
    tombs(bp)
    chapel(bp)
    long_stair(bp)
    grace(bp)
    bell_chamber(bp)
    founders_vault(bp)
    doors(bp)
    furnish(bp)
    mists(bp)


# ------------------------------------------------------------------------ crypt -> catacombs
def descent(bp):
    """The crypt's east wall opens on a stair down to the catacombs (x 24..33, z 15..17)."""
    solid(bp, 23, L1 - 1, 13, 34, 4, 19, WALL)
    bp.clear(23, 0, 15, 23, 3, 17)                     # through the crypt wall
    for z in (15, 16, 17):
        bp.set(23, -1, z, FLOOR.pick(23, -1, z))
    steps = []
    for i, x in enumerate(range(24, 34)):
        for z in (15, 16, 17):
            steps.append((x, -1 - i, z))
    stairway(bp, steps, "west", TS, WALL, head=4)
    for i, x in enumerate(range(24, 34)):               # candles in little wall recesses every few steps
        if i % 3 == 1:
            for z in (14, 18):
                bp.set(x, -i + 1, z, CANDLE % 3)
    # a rib of chiseled stone at the crypt mouth
    for z in range(14, 19):
        bp.set(23, 4, z, TRIM)


# ------------------------------------------------------------------------ level 1: catacombs
def ossuary(bp):
    """Long hall of bones (x 35..47, z 6..26) with deep wall niches; two-thick walls for the niches."""
    hollow(bp, 33, L1, 5, 49, L1 + 8, 27, WALL, FLOOR)
    bp.clear(34, L1 + 1, 6, 34, L1 + 5, 26)            # inner wall layer replaced by niches below
    bp.clear(48, L1 + 1, 6, 48, L1 + 5, 26)
    for x in (34, 48):
        for z in range(6, 27):
            for y in range(L1 + 1, L1 + 6):
                niche = z % 3 != 0 and y in (L1 + 2, L1 + 4)
                if not niche:
                    bp.set(x, y, z, WALL.pick(x, y, z))
                elif y == L1 + 2:
                    bp.set(x, y, z, "bone_block[axis=x]" if (z + y) % 2 else "bone_block[axis=z]")
    cove(bp, 35, 6, 47, 26, L1 + 6, TS)
    for z in range(8, 26, 4):
        rib(bp, "x", z, 35, 47, L1 + 7, TRIM, TS)


def tombs(bp):
    """Gallery of monk tombs (x 51..65, z 6..14)."""
    hollow(bp, 50, L1, 5, 66, L1 + 7, 15, WALL, Palette({"deepslate_tiles": 3, "polished_deepslate": 1}, seed=7))
    cove(bp, 51, 6, 65, 14, L1 + 6, TS)
    for x in range(53, 65, 4):
        rib(bp, "z", x, 6, 14, L1 + 6, TRIM, TS)


def chapel(bp):
    """The collapsed chapel (x 51..65, z 17..29): tall vault, apse altar to the east."""
    hollow(bp, 50, L1, 16, 66, L1 + 10, 30, WALL, FLOOR)
    cove(bp, 51, 17, 65, 29, L1 + 8, TS)
    for x in range(53, 66, 4):
        rib(bp, "z", x, 17, 29, L1 + 9, TRIM, TS)


def _step_y(z):
    return L1 - (z - STAIR_Z)


def long_stair(bp):
    """From the chapel's south door the stair falls to the site of grace (x 57..59, z STAIR_Z..STAIR_END)."""
    for z in range(STAIR_Z, GRACE[1]):
        y = _step_y(z)
        solid(bp, 55, y - 3, z, 61, y + 6, z, WALL)      # two-thick side walls hold the candle recesses
    steps = [(x, _step_y(z), z) for z in range(STAIR_Z, GRACE[1]) for x in (57, 58, 59)]
    stairway(bp, steps, "north", TS, WALL, head=4)
    for z in range(STAIR_Z + 1, GRACE[1] - 1, 3):      # candle niches in both walls
        y = _step_y(z) + 2
        bp.set(56, y, z, CANDLE % 2)
        bp.set(60, y, z, CANDLE % 3)
    for z in range(STAIR_Z + 2, GRACE[1] - 1, 5):
        hang(bp, 58, _step_y(z) + 5, z, 1, soul=True)


def grace(bp):
    """Site of grace (the GRACE box): waystone, benches, candles, before the arena door."""
    x0, z0, x1, z1 = GRACE
    hollow(bp, x0, L2, z0, x1, L2 + 9, z1, WALL, FLOOR)
    cove(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L2 + 8, TS)
    # the stair comes in through the north wall and lands inside
    for z in range(z0, STAIR_END + 1):
        y = _step_y(z)
        for x in (57, 58, 59):
            bp.stairs(x, y, z, TS, "north")
            bp.clear(x, y + 1, z, x, min(y + 4, L2 + 8), z)
            for yy in range(L2 + 1, y):
                bp.set(x, yy, z, WALL.pick(x, yy, z))
        bp.set(56, y, z, WALL.pick(56, y, z))
        bp.set(56, y + 1, z, "stone_brick_wall")
        bp.set(60, y, z, WALL.pick(60, y, z))
        bp.set(60, y + 1, z, "stone_brick_wall")


def bell_chamber(bp):
    """The arena: drum wall of radius AR+1..AR+2, pointed dome, bronze-inlaid floor, the hanging bell."""
    cx, cz = ARENA
    R = AR
    for x in range(cx - R - 4, cx + R + 5):
        for z in range(cz - R - 4, cz + R + 5):
            d = math.hypot(x - cx, z - cz)
            if d > R + 3.5:
                continue
            for y in range(L2 - 1, L2 + 1):
                bp.set(x, y, z, DEEP.pick(x, y, z))
            inner = dome_y(min(d, R + 1))
            if d <= R + 0.5:
                bp.set(x, L2, z, _floor(x - cx, z - cz, d))
                bp.clear(x, L2 + 1, z, x, inner, z)
                solid(bp, x, inner + 1, z, x, inner + 2, z, DEEP)
            else:
                solid(bp, x, L2 + 1, z, x, inner + 2, z, DEEP)
    # sixteen calcite pilasters with bronze capitals, niches between them
    for k in range(16):
        a = math.radians(k * 22.5)
        px, pz = cx + round(math.cos(a) * (R + 0.4)), cz + round(math.sin(a) * (R + 0.4))
        for y in range(L2 + 1, WALL_TOP + 1):
            bp.set(px, y, pz, COLUMN.pick(px, y, pz) if y != L2 + 1 else "polished_deepslate")
        bp.set(px, WALL_TOP + 1, pz, "waxed_chiseled_copper")
        bp.set(px, L2 + 7, pz, BULB)
    # ribs of the dome: eight bands of polished deepslate from the drum to the oculus ring
    for k in range(8):
        a = math.radians(k * 45 + 11.25)
        for r10 in range(0, (R + 1) * 10, 5):
            r = r10 / 10
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            y = dome_y(r)
            if r > 3:
                bp.set(x, y + 1, z, "polished_deepslate")
    # cornice where the dome springs
    for x in range(cx - R - 2, cx + R + 3):
        for z in range(cz - R - 2, cz + R + 3):
            d = math.hypot(x - cx, z - cz)
            if R - 0.5 < d <= R + 0.5 and bp.get(x, WALL_TOP, z) == "minecraft:air":
                f = _face_out(cx, cz, x, z)
                bp.set(x, WALL_TOP, z, A.stair(DS, f, "top"))
    _hanging_bell(bp, cx, cz)


def dome_y(r):
    """Highest air block of the dome at distance r from the chamber axis."""
    return math.floor(WALL_TOP + DOME * math.sqrt(max(0.0, 1 - (r / (AR + 1)) ** 2)))


def _floor(dx, dz, d):
    """Concentric floor: seal disc, a bronze ring, eight dark sound-lines, a dark rim."""
    ang = math.degrees(math.atan2(dz, dx)) % 45
    if d < 1.6:
        return "waxed_chiseled_copper"
    if d < 3.2:
        return "chiseled_stone_bricks"
    if 5.6 <= d < 6.6:
        return "waxed_exposed_cut_copper" if (int(dx) + int(dz)) % 4 else "waxed_weathered_cut_copper"
    if d >= AR - 1.0:
        return "deepslate_tiles"
    if d > 6.6 and min(ang, 45 - ang) * d * math.pi / 180 < 0.6:
        return "polished_deepslate"
    if 10.6 <= d < 11.4:
        return "polished_blackstone_bricks"
    return FLOOR.pick(int(dx) + 50, 0, int(dz) + 50)


def _face_out(cx, cz, x, z):
    dx, dz = x - cx, z - cz
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _hanging_bell(bp, cx, cz):
    """The great bell, cracked down one side, hanging from a broken timber headstock under the dome."""
    beam_y = WALL_TOP + DOME - 3
    for x in range(cx - 13, cx + 14):
        for z in (cz - 1, cz, cz + 1):
            if abs(z - cz) == 1 and abs(x - cx) > 3:
                continue
            bp.set(x, beam_y, z, "stripped_dark_oak_log[axis=x]" if abs(z - cz) == 1 else "dark_oak_log[axis=x]")
    for x in (cx - 4, cx + 4):                           # iron straps
        bp.set(x, beam_y, cz, "waxed_copper_grate")
    # bell profile: (rows below the beam, radius); crown, rounded shoulder, long waist, flared sound bow, lip
    profile = [(1, 1.6), (2, 2.9), (3, 3.6), (4, 3.9), (5, 4.0), (6, 4.1), (7, 4.3), (8, 4.6), (9, 5.0), (10, 5.6),
               (11, 6.3), (12, 6.7)]
    for dy, r in profile:
        y = beam_y - dy
        for x in range(cx - 8, cx + 9):
            for z in range(cz - 8, cz + 9):
                d = math.hypot(x - cx, z - cz)
                if d > r + 0.35 or (d < r - 0.95 and dy > 2):
                    continue                             # outside, or the hollow inside
                if z - cz >= 2 and abs(x - cx - round(math.sin(dy * 1.1))) < 1 and 3 <= dy <= 11:
                    continue                             # the crack running down the south face
                bp.set(x, y, z, _bell_block(x - cx, z - cz, dy))
    bp.chain(cx, beam_y - 11, cz, beam_y - 2)           # clapper
    bp.set(cx, beam_y - 12, cz, "polished_blackstone")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        bp.set(cx + dx, beam_y - 12, cz + dz, "polished_blackstone_wall")
    # broken bell-wheel and dangling ropes / chains around the beam
    for x, length in ((cx - 9, 6), (cx - 6, 3), (cx + 7, 8), (cx + 11, 4)):
        bp.chain(x, beam_y - length, cz, beam_y - 1)


def _bell_block(dx, dz, dy):
    """Bronze by band: shoulder and sound-bow bands darker, an inscription band, verdigris dripping below."""
    if dy == 12:
        return "waxed_copper_block"                      # the lip
    if dy == 6:
        return "waxed_chiseled_copper"                   # inscription band
    if dy in (3, 10):
        return "waxed_exposed_cut_copper"
    if (dx * 3 + dz * 5) % 7 == 0 and dy in (7, 8, 11):
        return "waxed_weathered_cut_copper"              # verdigris streaks under the bands
    return "waxed_cut_copper"


def founders_vault(bp):
    """Reward room past the arena (x 7..17): the bell-founders' vault."""
    cz = ARENA[1]
    hollow(bp, 6, L2, cz - 6, 18, L2 + 8, cz + 6, WALL, Palette({"deepslate_tiles": 2, "polished_deepslate": 1},
                                                                  seed=9))
    cove(bp, 7, cz - 5, 17, cz + 5, L2 + 7, DS)
    for z in range(cz - 3, cz + 5, 4):
        rib(bp, "x", z, 7, 17, L2 + 7, "polished_deepslate", DS)


# ------------------------------------------------------------------------ connections
def doors(bp):
    cx, cz = ARENA
    # ossuary <-> tombs, ossuary <-> chapel, tombs <-> chapel, chapel -> long stair
    opening(bp, 48, L1 + 1, 9, 50, L1 + 3, 11, TRIM, TS, axis="z")
    opening(bp, 48, L1 + 1, 21, 50, L1 + 3, 23, TRIM, TS, axis="z")
    opening(bp, 57, L1 + 1, 15, 59, L1 + 3, 16, TRIM, TS, axis="x")
    opening(bp, 57, L1 + 1, 30, 59, L1 + 4, 30, TRIM, TS, axis="x")
    # catacomb stair -> ossuary
    opening(bp, 33, L1 + 1, 15, 34, L1 + 4, 17)
    # grace -> arena (east), arena -> vault (west): 3 wide, 4 tall, deep portals
    opening(bp, cx + AR + 1, L2 + 1, cz - 1, 54, L2 + 4, cz + 1, TRIM, TS, axis="z")
    opening(bp, 18, L2 + 1, cz - 1, cx - AR - 1, L2 + 4, cz + 1, TRIM, TS, axis="z")
    for x in range(cx + AR + 1, 55):
        for z in (cz - 1, cz, cz + 1):
            bp.set(x, L2, z, "deepslate_tiles")
    for x in range(18, cx - AR):
        for z in (cz - 1, cz, cz + 1):
            bp.set(x, L2, z, "deepslate_tiles")


def mists(bp):
    cx, cz = ARENA
    bp.mist(cx + AR + 2, L2 + 1, cz - 1, cx + AR + 2, L2 + 4, cz + 1)    # from the site of grace
    bp.mist(cx - AR - 2, L2 + 1, cz - 1, cx - AR - 2, L2 + 4, cz + 1)    # to the founders' vault


# ------------------------------------------------------------------------ furniture, lights, encounters
def furnish(bp):
    rng = random.Random(510)
    cx, cz = ARENA
    # ---- ossuary: bone piers, the mound with its spawner, skulls in the niches
    for z in range(9, 25, 5):
        for x in (38, 44):
            for y in range(L1 + 1, L1 + 6):
                bp.set(x, y, z, "bone_block[axis=y]" if y < L1 + 5 else TRIM)
            bp.set(x + (1 if x == 38 else -1), L1 + 1, z, CANDLE % 3)
    for x, rot in ((34, 12), (48, 4)):                    # skulls look out of the niches into the hall
        for z in range(6, 27):
            if z % 3 and rng.random() < 0.6:
                bp.set(x, L1 + 3, z, "skeleton_skull[rotation=%d]" % rot)
            if z % 3 and rng.random() < 0.35:
                bp.set(x, L1 + 5, z, CANDLE % rng.randint(1, 4))
    for (x, z) in ((40, 15), (41, 15), (42, 15), (40, 16), (42, 16), (40, 17), (41, 17), (42, 17), (41, 14),
                   (41, 18), (39, 16), (43, 16)):
        bp.set(x, L1 + 1, z, "bone_block[axis=y]")
    for (x, z) in ((40, 15), (42, 17), (41, 14), (39, 16)):
        bp.set(x, L1 + 2, z, "skeleton_skull[rotation=%d]" % rng.randint(0, 15))
    bp.spawner(41, L1 + 2, 16, "minecraft:skeleton")
    for z in (10, 21):
        hang(bp, 41, L1 + 7, z, 2, soul=True)
    for z in range(7, 26, 6):
        if rng.random() < 0.5:
            bp.set(36, L1 + 1, z, "cobweb")
    # ---- tombs: two rows of sarcophagi with effigies, candles, a loot barrel
    for x0 in range(52, 64, 4):
        for z0, f in ((7, "south"), (12, "north")):
            for x in range(x0, x0 + 3):
                bp.set(x, L1 + 1, z0, "polished_andesite")
                bp.set(x, L1 + 2, z0, "smooth_stone_slab[type=bottom,waterlogged=false]")
            bp.set(x0, L1 + 2, z0, "skeleton_skull[rotation=%d]" % (8 if f == "north" else 0))
            bp.set(x0 + 3, L1 + 1, z0, CANDLE % 2)
    bp.barrel(65, L1 + 1, 10, "west", LOOT + "monastery")
    for x in (55, 61):
        hang(bp, x, L1 + 7, 10, 2)
    # ---- chapel: broken pews, altar, the collapse, a fallen chandelier
    for z in range(19, 29, 2):
        for x in list(range(52, 57)) + list(range(60, 64)):
            if rng.random() < 0.75:
                bp.stairs(x, L1 + 1, z, "dark_oak_stairs", "west")     # seats facing the altar
    for z in range(19, 28):
        bp.set(64, L1 + 1, z, "polished_andesite")
    for z in range(21, 26):
        bp.set(65, L1 + 1, z, TRIM)
        bp.set(65, L1 + 2, z, "polished_andesite_slab[type=bottom,waterlogged=false]" if z != 23 else "gold_block")
    bp.set(65, L1 + 3, 23, "lectern[facing=west,has_book=false,powered=false]")
    candles(bp, [(65, L1 + 3, 21), (65, L1 + 3, 25), (64, L1 + 2, 20), (64, L1 + 2, 27)], seed=3)
    bp.chest(65, L1 + 2, 19, "west", LOOT + "monastery_library")
    for y in range(L1 + 3, L1 + 7):
        for z in (18, 28):
            bp.set(65, y, z, "purple_stained_glass" if y % 2 else "orange_stained_glass")
    for z in (20, 26):
        bp.set(66, L1 + 5, z, "shroomlight")              # light behind the glass "windows"
        bp.set(65, L1 + 5, z, "yellow_stained_glass")
    # the collapse: a cone of rubble under a hole in the vault (north-west quarter)
    hx, hz = 54, 20
    for x in range(hx - 4, hx + 5):
        for z in range(hz - 3, hz + 4):
            d = math.hypot(x - hx, z - hz)
            if 51 <= x <= 65 and 17 <= z <= 29:
                for y in range(L1 + 1, L1 + 1 + max(0, int(4 - d + rng.random()))):
                    bp.set(x, y, z, rng.choice(RUBBLE))
            if d < 2.5:
                for y in range(L1 + 8, L1 + 10):
                    bp.set(x, y, z, "air")
    for x, z in ((hx - 1, hz), (hx, hz + 1), (hx + 1, hz - 1)):
        bp.set(x, L1 + 10, z, "air")
    bp.set(60, L1 + 1, 24, "lantern[hanging=false,waterlogged=false]")   # the fallen chandelier
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(60 + dx, L1 + 1, 24 + dz, "dark_oak_fence")
    for x in range(62, 65):
        bp.set(x, L1 + 1, 24, "iron_chain[axis=x,waterlogged=false]")
    bp.spawner(59, L1 + 1, 21, MOB["ruin_walker"])
    hang(bp, 61, L1 + 10, 23, 3)
    for x in range(52, 65, 3):
        if rng.random() < 0.4:
            bp.set(x, L1 + 1, 29, "cobweb")
    _furnish_grace(bp)
    # ---- bell chamber: lights in the niches between pilasters, soul lanterns from the dome, shards
    for k in range(16):
        a = math.radians(k * 22.5 + 11.25)
        nx, nz = cx + round(math.cos(a) * (AR + 1)), cz + round(math.sin(a) * (AR + 1))
        if abs(nz - cz) <= 2 and abs(abs(nx - cx) - AR - 1) <= 1:
            continue                                      # keep the two doorways free
        for y in range(L2 + 2, L2 + 7):
            bp.set(nx, y, nz, "air")
        bp.set(nx, L2 + 1, nz, "polished_deepslate")
        bp.set(nx, L2 + 2, nz, CANDLE % 4)
        bp.set(nx, L2 + 4, nz, "iron_bars")
        bp.set(nx, L2 + 5, nz, "iron_bars")
        bp.set(nx, L2 + 6, nz, A.stair(DS, _face_out(cx, cz, nx, nz), "top"))
        ox, oz = cx + round(math.cos(a) * (AR + 2)), cz + round(math.sin(a) * (AR + 2))
        bp.set(ox, L2 + 4, oz, "soul_lantern[hanging=false,waterlogged=false]")
        bp.set(ox, L2 + 5, oz, "air")
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = cx + round(math.cos(a) * 10), cz + round(math.sin(a) * 10)
        hang(bp, x, dome_y(10) + 1, z, 3 + k % 3, soul=k % 2 == 0)
    for (x, z) in ((cx - 12, cz - 7), (cx + 11, cz + 8), (cx - 9, cz + 11)):
        bp.set(x, L2 + 1, z, "waxed_exposed_cut_copper_slab[type=bottom,waterlogged=false]")   # bronze shards
    bp.set(cx + 12, L2 + 1, cz - 6, "waxed_weathered_cut_copper_stairs[facing=north,half=bottom,shape=straight,"
                                    "waterlogged=false]")
    bp.boss_seal(cx, L2, cz, "brasshaven:bell_keeper", AR)
    _furnish_vault(bp)


def _furnish_grace(bp):
    """Waystone on a stepped dais, benches, candles, bronze bulbs; the portal flanked by kneeling monks."""
    cx, cz = ARENA
    x0, z0, x1, z1 = GRACE
    gx, gz = 61, cz + 5
    solid(bp, gx - 1, L2 + 1, gz - 1, gx + 1, L2 + 1, gz + 1, "polished_andesite")
    for (x, z) in square_ring(gx, gz, 2):
        bp.stairs(x, L2 + 1, z, "polished_andesite_stairs", _face_out(gx, gz, x, z))
    bp.set(gx, L2 + 2, gz, MOD["waystone"])
    candles(bp, [(gx - 1, L2 + 2, gz - 1), (gx + 1, L2 + 2, gz + 1), (gx + 1, L2 + 2, gz - 1),
                 (gx - 1, L2 + 2, gz + 1)], seed=5)
    for x in range(56, 60):                               # benches along the south wall and the east wall
        bp.stairs(x, L2 + 1, z1 - 1, "spruce_stairs", "south")
    for z in range(cz + 1, cz + 6):
        bp.stairs(x1 - 1, L2 + 1, z, "spruce_stairs", "east")
    for (x, z) in ((x1 - 2, z0 + 2), (x1 - 2, z1 - 2), (x0 + 2, z1 - 2)):
        for y in range(L2 + 1, L2 + 8):
            bp.set(x, y, z, COLUMN.pick(x, y, z))
        bp.set(x, L2 + 4, z, BULB)
    hang(bp, gx, L2 + 9, gz, 2)
    hang(bp, 58, L2 + 9, cz + 4, 3, soul=True)
    for (x, z) in ((x0 + 1, z1 - 1), (x1 - 1, z1 - 1), (x1 - 1, z0 + 1)):
        bp.set(x, L2 + 1, z, CANDLE % 4)
    for z in (cz - 2, cz + 2):                            # the portal toward the bell
        for y in range(L2 + 1, L2 + 6):
            bp.set(x0, y, z, "waxed_copper_block" if y in (L2 + 1, L2 + 5) else COLUMN.pick(x0, y, z))
    for z in (cz - 3, cz + 3):
        _statue(bp, x0 + 1, L2 + 1, z, "west")
    for x in range(x0 + 1, 60):                           # a worn runner from the stair foot to the portal
        for z in (cz - 1, cz, cz + 1):
            if bp.get(x, L2 + 1, z) in (None, "minecraft:air"):
                bp.set(x, L2 + 1, z, "red_carpet" if z == cz else "gray_carpet")
    for x in (x0 + 4, x0 + 8):                            # banners of the order on the south wall
        for y in (L2 + 5, L2 + 6):
            bp.set(x, y, z1 - 1, "purple_wall_banner[facing=north]" if y == L2 + 6 else "air")
    bp.set(x1 - 1, L2 + 1, z1 - 3, "lectern[facing=west,has_book=false,powered=false]")
    candles(bp, [(x1 - 1, L2 + 1, z1 - 4), (x1 - 1, L2 + 1, z1 - 2), (gx - 2, L2 + 1, gz + 2),
                 (gx + 2, L2 + 1, gz - 2)], seed=6)


def _furnish_vault(bp):
    """Founders' vault: a casting pit glowing under a grate, bronze bulbs, tools, the reward chests."""
    cz = ARENA[1]
    for x in range(10, 15):
        for z in range(cz - 2, cz + 3):
            bp.set(x, L2, z, "magma_block" if (x, z) == (12, cz) else "polished_blackstone")
    bp.set(12, L2 + 1, cz, "waxed_copper_grate")
    for (x, z) in ((8, cz - 4), (16, cz - 4), (8, cz + 4), (16, cz + 4)):
        bp.set(x, L2 + 1, z, "waxed_copper_block")
        bp.set(x, L2 + 2, z, BULB)
    for x, north, south in ((10, "anvil[facing=north]", "barrel[facing=up,open=false]"),
                            (12, "smithing_table", "blast_furnace[facing=north,lit=false]"),
                            (14, "barrel[facing=up,open=false]", "barrel[facing=up,open=false]")):
        bp.set(x, L2 + 1, cz - 5, north)
        bp.set(x, L2 + 1, cz + 5, south)
    bp.chest(7, L2 + 1, cz - 2, "east", LOOT + "monastery")
    bp.chest(7, L2 + 1, cz + 2, "east", LOOT + "monastery_library")
    bp.set(7, L2 + 1, cz, "waxed_copper_block")
    bp.set(7, L2 + 2, cz, "bell[attachment=floor,facing=east,powered=false]")
    hang(bp, 12, L2 + 8, cz, 2)


def _statue(bp, x, y, z, facing):
    """A hooded monk in stone, three blocks tall, facing ``facing``."""
    bp.set(x, y, z, "polished_andesite")
    bp.set(x, y + 1, z, "andesite_wall")
    bp.set(x, y + 2, z, "polished_andesite")
    bp.set(x, y + 3, z, A.stair("andesite_stairs", OPPOSITE[facing], "bottom"))
    bp.set(x, y + 4, z, "andesite_slab[type=bottom,waterlogged=false]")


def square_ring(cx, cz, r):
    return [(x, z) for x in range(cx - r, cx + r + 1) for z in range(cz - r, cz + r + 1)
            if max(abs(x - cx), abs(z - cz)) == r]
