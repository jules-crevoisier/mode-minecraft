"""Lair of the Archivist, under the Forgotten Library.

The library had nothing underground. Its secret study (the south tower, reached by breaking two bookshelves)
now hides a stair in its floor:

* the stair winds down a square shaft in the tower's foundations to level 1 (floor y = LA1): a buried
  scriptorium of copying desks, then the collapsed stacks, a hall of toppled shelves and rubble;
* the grand stair falls from the stacks to level 2 (floor y = LA2): a reading-room vestibule with a waystone
  (the site of grace), then the Forbidden Archive: a tall cylindrical vault (radius AR) lined floor to ceiling
  with bookcases, ringed by three reading galleries, a great orrery of bronze rings hanging under a domed
  ceiling set with rune lamps, and a compass rose on the clear floor where the Archivist's seal lies;
* past the arena, the restricted vault keeps the reward.
"""
import math
import random

from .. import arch as A
from ..arch import Palette
from ..parts import LOOT, MOB, MOD
from .lair_bell_keeper import candles, cove, hang, hollow, opening, rib, solid, square_ring

LA1 = -12                 # scriptorium floor
LA2 = -33                 # archive floor
ARENA = (36, 18)          # archive centre (x, z)
AR = 15                   # clear floor radius
GALLERIES = (LA2 + 7, LA2 + 13, LA2 + 19)
TOP = LA2 + 24            # bookcase wall top, the dome springs here
DOME = 5

WALL = Palette({"tuff_bricks": 5, "polished_tuff": 1, "tuff": 1, "deepslate_bricks": 2, "cracked_deepslate_bricks": 1},
               seed=601, scale=2.0)
FLOOR = Palette({"polished_deepslate": 2, "polished_tuff": 2, "deepslate_tiles": 1}, seed=602, scale=1.5)
ROSE = Palette({"polished_tuff": 4, "tuff_bricks": 1, "polished_andesite": 1}, seed=603, scale=1.5)
PGS = "wayfarers:polished_guild_stone"
PGS_ST = "wayfarers:polished_guild_stone_stairs"
CGS = "wayfarers:carved_guild_stone"
RUNE = "wayfarers:rune_lamp"
TS = "tuff_brick_stairs"
SHELF = "bookshelf"
RUBBLE = ("tuff", "tuff_bricks", "cobblestone", "mossy_cobblestone", "gravel", "bookshelf", "dark_oak_planks")


def cshelf(face, seed=0):
    slots = ",".join(f"slot_{i}_occupied={'true' if (seed >> i) & 1 else 'false'}" for i in range(6))
    return f"chiseled_bookshelf[facing={face},{slots}]"


def build(bp):
    """Called at the end of the library builder."""
    stair_shaft(bp)
    scriptorium(bp)
    stacks(bp)
    grand_stair(bp)
    vestibule(bp)
    archive(bp)
    restricted_vault(bp)
    doors(bp)
    furnish(bp)
    mists(bp)


# ------------------------------------------------------------------------ the hidden stair
def stair_shaft(bp):
    """Square spiral stair under the secret study (tower interior x 65..71, z 27..33), from the study floor
    (y 0) down to LA1. The first flight is one block wide (x 71) so the study's furniture stays in place."""
    solid(bp, 64, LA1 - 1, 26, 72, -1, 34, WALL)
    bp.clear(65, LA1 + 1, 27, 71, -1, 33)
    solid(bp, 67, LA1, 29, 69, -1, 31, Palette({"chiseled_tuff_bricks": 1, "tuff_bricks": 2}, seed=3))
    # the ring path: flights (cells, facing) and landings, alternating
    path = [
        ("flight", [((71,), 29), ((71,), 30), ((71,), 31)], "north"),
        ("landing", [(70, 32), (71, 32), (70, 33), (71, 33)], None),
        ("flight", [((69,), (32, 33)), ((68,), (32, 33)), ((67,), (32, 33))], "east"),
        ("landing", [(65, 32), (66, 32), (65, 33), (66, 33)], None),
        ("flight", [((65, 66), 31), ((65, 66), 30), ((65, 66), 29)], "south"),
        ("landing", [(65, 27), (66, 27), (65, 28), (66, 28)], None),
        ("flight", [((67,), (27, 28)), ((68,), (27, 28)), ((69,), (27, 28))], "west"),
        ("landing", [(70, 27), (71, 27), (70, 28), (71, 28)], None),
    ]
    h = 0
    for kind, cells, facing in path:
        if kind == "landing":
            for (x, z) in cells:
                bp.set(x, h, z, PGS)
                solid(bp, x, LA1, z, x, h - 1, z, WALL)
            continue
        for xs, zs in cells:
            for x in xs:
                for z in (zs if isinstance(zs, tuple) else (zs,)):
                    bp.stairs(x, h, z, "dark_oak_stairs", facing)
                    solid(bp, x, LA1, z, x, h - 1, z, WALL)
            h -= 1
    # the study floor opens over the first flight
    for z in (30, 31):
        bp.set(71, 0, z, "air")
    bp.set(71, 1, 32, "dark_oak_trapdoor[facing=north,half=bottom,open=true,powered=false,waterlogged=false]")
    # rune lamps set in the core, one on each face along the way down
    for (x, y, z) in ((69, -2, 30), (68, -5, 31), (67, -8, 30), (68, -11, 29)):
        bp.set(x, y, z, RUNE)


# ------------------------------------------------------------------------ level 1
def scriptorium(bp):
    """Buried scriptorium (x 75..89, z 19..33): four piers, rows of copying desks."""
    hollow(bp, 74, LA1, 18, 90, LA1 + 8, 34, WALL, FLOOR)
    cove(bp, 75, 19, 89, 33, LA1 + 7, TS)
    for x in (79, 85):
        rib(bp, "z", x, 19, 33, LA1 + 7, PGS, PGS_ST)
    solid(bp, 72, LA1, 26, 74, LA1 + 5, 29, WALL)       # passage from the shaft


def stacks(bp):
    """The collapsed stacks (x 75..89, z 36..48)."""
    hollow(bp, 74, LA1, 35, 90, LA1 + 8, 49, WALL, FLOOR)
    cove(bp, 75, 36, 89, 48, LA1 + 7, TS)


def grand_stair(bp):
    """From the stacks' west door the stair falls 21 blocks westward (x 53..73, z 45..47)."""
    for x in range(53, 74):
        y = LA1 - (73 - x)
        solid(bp, x, y - 3, 44, x, y + 6, 48, WALL)
    for x in range(53, 74):
        y = LA1 - (73 - x)
        for z in (45, 46, 47):
            bp.stairs(x, y, z, "dark_oak_stairs", "east")
            bp.clear(x, y + 1, z, x, y + 4, z)
        if x % 4 == 1:
            bp.set(x, y + 2, 44, "candle[candles=3,lit=true,waterlogged=false]")
            bp.set(x, y + 2, 48, "candle[candles=2,lit=true,waterlogged=false]")
        if x % 6 == 3:
            hang(bp, x, y + 5, 46, 1, soul=True)
        if x % 3 == 0:                                   # shelves line the stair walls
            bp.set(x, y + 3, 44, SHELF)
            bp.set(x, y + 3, 48, SHELF)
    # landing and passage to the vestibule
    solid(bp, 44, LA2 - 1, 44, 52, LA2 + 5, 48, WALL)
    bp.clear(45, LA2 + 1, 45, 52, LA2 + 4, 47)
    for x in range(45, 53):
        for z in (45, 46, 47):
            bp.set(x, LA2, z, FLOOR.pick(x, LA2, z))


def vestibule(bp):
    """Reading-room vestibule (x 31..43, z 40..50): the site of grace before the archive."""
    hollow(bp, 30, LA2, 39, 44, LA2 + 9, 51, WALL, FLOOR)
    cove(bp, 31, 40, 43, 50, LA2 + 8, TS)
    for z in (43, 47):
        rib(bp, "x", z, 31, 43, LA2 + 8, PGS, PGS_ST)
    solid(bp, 32, LA2 - 1, 34, 40, LA2 + 6, 39, WALL)     # the passage to the arena (carved by doors())


# ------------------------------------------------------------------------ the Forbidden Archive
def vault_y(d):
    """Highest air block of the archive's dome at distance d from the axis."""
    return math.floor(TOP + DOME * math.sqrt(max(0.0, 1 - (d / (AR + 1)) ** 2)))


def archive(bp):
    cx, cz = ARENA
    R = AR
    rng = random.Random(611)
    for x in range(cx - R - 4, cx + R + 5):
        for z in range(cz - R - 4, cz + R + 5):
            d = math.hypot(x - cx, z - cz)
            if d > R + 3.5:
                continue
            solid(bp, x, LA2 - 1, z, x, LA2, z, WALL)
            top = vault_y(min(d, R + 1))
            if d <= R + 0.5:
                bp.set(x, LA2, z, _rose(x - cx, z - cz, d))
                bp.clear(x, LA2 + 1, z, x, top, z)
                solid(bp, x, top + 1, z, x, top + 2, z, WALL)
            elif d <= R + 1.5:                            # the bookcase wall
                ang = math.degrees(math.atan2(z - cz, x - cx)) % 22.5
                pilaster = min(ang, 22.5 - ang) * d * math.pi / 180 < 0.7
                face = _face_in(cx, cz, x, z)
                for y in range(LA2 + 1, TOP + 1):
                    if pilaster:
                        b = CGS if (y - LA2) % 6 == 0 else PGS
                    elif y in GALLERIES or y == TOP:
                        b = PGS
                    else:
                        b = SHELF if rng.random() < 0.8 else cshelf(face, rng.randint(0, 63))
                    bp.set(x, y, z, b)
                solid(bp, x, TOP + 1, z, x, top + 2, z, WALL)
            else:
                solid(bp, x, LA2 + 1, z, x, top + 2, z, WALL)
    # three reading galleries: plank floor 2 deep, fence railing, brackets under the pilasters
    for gy in GALLERIES:
        for x in range(cx - R - 1, cx + R + 2):
            for z in range(cz - R - 1, cz + R + 2):
                d = math.hypot(x - cx, z - cz)
                if R - 1.5 < d <= R + 0.5:
                    bp.set(x, gy, z, "dark_oak_planks")
                    if d <= R - 0.5:
                        bp.set(x, gy + 1, z, "dark_oak_fence")
                        bp.set(x, gy - 1, z, A.stair("dark_oak_stairs", _face_out(cx, cz, x, z), "top"))
    # dome ribs and a ring of rune lamps
    for k in range(16):
        a = math.radians(k * 22.5)
        for r10 in range(30, (R + 1) * 10, 5):
            r = r10 / 10
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            bp.set(x, vault_y(r) + 1, z, PGS)
    for k in range(12):
        a = math.radians(k * 30 + 15)
        x, z = cx + round(math.cos(a) * 9), cz + round(math.sin(a) * 9)
        bp.set(x, vault_y(9) + 1, z, RUNE)
    _orrery(bp, cx, cz)


def _rose(dx, dz, d):
    """Compass rose: a copper hub, an eight-pointed star of dark lines, a bronze ring, a tiled rim."""
    ang = math.degrees(math.atan2(dz, dx)) % 360
    if d < 1.6:
        return "waxed_chiseled_copper"
    if d < 3.2:
        return "chiseled_tuff_bricks"
    if 12.6 <= d < 13.5:
        return "waxed_oxidized_cut_copper" if (int(dx) + int(dz)) % 3 else "waxed_weathered_cut_copper"
    if d >= AR - 0.8:
        return "deepslate_tiles"
    a45 = ang % 45
    half_width = (1.0 - d / 12.5) * (2.6 if round(ang / 45) % 2 == 0 else 1.6)   # long and short points
    if d < 12.5 and min(a45, 45 - a45) * d * math.pi / 180 < half_width:
        return "polished_deepslate" if round(ang / 45) % 2 == 0 else "polished_blackstone"
    if 6.6 <= d < 7.4:
        return "chiseled_tuff"
    return ROSE.pick(int(dx) + 70, 0, int(dz) + 70)


def _face_in(cx, cz, x, z):
    dx, dz = x - cx, z - cz
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def _face_out(cx, cz, x, z):
    dx, dz = x - cx, z - cz
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _orrery(bp, cx, cz):
    """The great orrery: three bronze rings on chains under the dome, a rune-lamp sun at the hub."""
    apex = vault_y(0)
    hub_y = apex - 6
    bp.chain(cx, hub_y + 1, cz, apex)
    bp.set(cx, hub_y, cz, RUNE)
    bp.set(cx, hub_y - 1, cz, "waxed_copper_grate")
    for r, y, block in ((3, hub_y, "waxed_cut_copper"), (6, hub_y - 1, "waxed_exposed_cut_copper"),
                        (9, hub_y + 1, "waxed_weathered_cut_copper")):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                if abs(math.hypot(x - cx, z - cz) - r) < 0.5:
                    bp.set(x, y, z, block)
        for k in range(4):                                # each ring hangs from four chains
            a = math.radians(k * 90 + r * 15)
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            bp.chain(x, y + 1, z, vault_y(r))
    # planets: a lantern and a glowing ball on two of the rings
    bp.lantern(cx + 6, hub_y - 2, cz, hanging=True)
    bp.set(cx - 9, hub_y, cz, "waxed_copper_bulb[lit=true,powered=false]")
    bp.set(cx, hub_y - 2, cz + 3, "sea_lantern")


def restricted_vault(bp):
    """Reward room past the archive (x 6..16, z 12..24)."""
    hollow(bp, 5, LA2, 11, 17, LA2 + 8, 25, WALL, FLOOR)
    cove(bp, 6, 12, 16, 24, LA2 + 7, TS)
    for z in (15, 21):
        rib(bp, "x", z, 6, 16, LA2 + 7, PGS, PGS_ST)


# ------------------------------------------------------------------------ connections
def doors(bp):
    cx, cz = ARENA
    opening(bp, 72, LA1 + 1, 27, 74, LA1 + 3, 28, PGS, PGS_ST, axis="z")      # shaft -> scriptorium
    opening(bp, 80, LA1 + 1, 34, 82, LA1 + 4, 35, PGS, PGS_ST, axis="x")      # scriptorium -> stacks
    opening(bp, 74, LA1 + 1, 45, 74, LA1 + 4, 47, PGS, PGS_ST, axis="z")      # stacks -> grand stair
    opening(bp, 44, LA2 + 1, 45, 44, LA2 + 4, 47, PGS, PGS_ST, axis="z")      # stair landing -> vestibule
    # vestibule -> archive (south door), archive -> restricted vault (west door)
    opening(bp, cx - 1, LA2 + 1, cz + AR + 1, cx + 1, LA2 + 4, 39, PGS, PGS_ST, axis="x")
    opening(bp, 17, LA2 + 1, cz - 1, cx - AR - 1, LA2 + 4, cz + 1, PGS, PGS_ST, axis="z")
    for z in range(cz + AR + 1, 40):
        for x in (cx - 1, cx, cx + 1):
            bp.set(x, LA2, z, "deepslate_tiles")
    for x in range(17, cx - AR):
        for z in (cz - 1, cz, cz + 1):
            bp.set(x, LA2, z, "deepslate_tiles")


def mists(bp):
    cx, cz = ARENA
    bp.mist(cx - 1, LA2 + 1, cz + AR + 2, cx + 1, LA2 + 4, cz + AR + 2)   # from the vestibule
    bp.mist(cx - AR - 2, LA2 + 1, cz - 1, cx - AR - 2, LA2 + 4, cz + 1)   # to the restricted vault


# ------------------------------------------------------------------------ furniture, lights, encounters
def furnish(bp):
    _furnish_scriptorium(bp)
    _furnish_stacks(bp)
    _furnish_vestibule(bp)
    _furnish_archive(bp)
    _furnish_vault(bp)


def _furnish_scriptorium(bp):
    rng = random.Random(620)
    for (x, z) in ((79, 23), (85, 23), (79, 29), (85, 29)):            # piers with rune lamps
        for y in range(LA1 + 1, LA1 + 7):
            bp.set(x, y, z, PGS if y != LA1 + 4 else RUNE)
    for z0 in (21, 25, 31):                                            # rows of copying desks
        for x in range(76, 89):
            if x in (79, 85):
                continue
            bp.set(x, LA1 + 1, z0, "dark_oak_slab[type=top,waterlogged=false]" if x % 2 else "dark_oak_planks")
            bp.stairs(x, LA1 + 1, z0 + 1, "dark_oak_stairs", "north")
            if rng.random() < 0.3:
                bp.set(x, LA1 + 2, z0, "candle[candles=%d,lit=true,waterlogged=false]" % rng.randint(1, 3))
            elif rng.random() < 0.2:
                bp.set(x, LA1 + 2, z0, "lectern[facing=south,has_book=false,powered=false]")
    for x in range(75, 90):                                            # bookcases on the long walls
        for y in range(LA1 + 1, LA1 + 6):
            for z, f in ((19, "south"), (33, "north")):
                if x % 4 and not (y > LA1 + 3 and x % 4 == 2):
                    bp.set(x, y, z, SHELF if (x * y) % 5 else cshelf(f, x + y))
    bp.spawner(82, LA1 + 1, 27, MOB["map_wraith"])
    for x in (77, 87):
        hang(bp, x, LA1 + 8, 26, 2)
    A.chandelier(bp, 82, LA1 + 7, 23)
    for (x, z) in ((76, 32), (88, 20), (88, 32)):
        bp.set(x, LA1 + 1, z, "cobweb")


def _furnish_stacks(bp):
    """Toppled shelves lying across the floor, rubble heaps, a hidden chest under a fallen case."""
    rng = random.Random(630)
    for i in range(7):                                                 # fallen bookcases, 4-6 long
        x0, z0 = rng.randint(76, 84), rng.randint(37, 46)
        horiz = rng.random() < 0.5
        for k in range(rng.randint(4, 6)):
            x, z = (x0 + k, z0) if horiz else (x0, z0 + k)
            if 75 <= x <= 89 and 36 <= z <= 48:
                bp.set(x, LA1 + 1, z, SHELF)
    for (hx, hz) in ((86, 39), (78, 46)):
        for x in range(hx - 3, hx + 4):
            for z in range(hz - 3, hz + 4):
                d = math.hypot(x - hx, z - hz)
                if 75 <= x <= 89 and 36 <= z <= 48:
                    for y in range(LA1 + 1, LA1 + 1 + max(0, int(3.2 - d + rng.random()))):
                        bp.set(x, y, z, rng.choice(RUBBLE))
    for (x, z) in ((88, 47), (88, 46), (87, 47)):                       # the hidden chest's niche
        bp.set(x, LA1 + 1, z, "air")
    bp.chest(88, LA1 + 1, 47, "north", LOOT + "library_secret")
    bp.set(88, LA1 + 1, 46, SHELF)
    bp.set(87, LA1 + 1, 47, SHELF)
    bp.spawner(81, LA1 + 1, 41, MOB["ruin_walker"])
    for x in range(75, 90, 2):                                          # standing shelves along the walls
        for z, f in ((36, "south"), (48, "north")):
            if rng.random() < 0.7:
                for y in range(LA1 + 1, LA1 + 1 + rng.randint(2, 5)):
                    bp.set(x, y, z, SHELF)
    for (x, z) in ((77, 38), (83, 44), (88, 37), (76, 47), (85, 47)):
        bp.set(x, LA1 + 1 + (x % 2), z, "cobweb")
    hang(bp, 82, LA1 + 8, 42, 3, soul=True)
    for (x, z) in ((76, 40), (89, 43)):
        bp.set(x, LA1 + 1, z, "candle[candles=2,lit=true,waterlogged=false]")


def _furnish_vestibule(bp):
    """Site of grace: the waystone among reading tables, lamps and candles; the portal to the archive."""
    cx = ARENA[0]
    gx, gz = 37, 46
    solid(bp, gx - 1, LA2 + 1, gz - 1, gx + 1, LA2 + 1, gz + 1, PGS)
    for (x, z) in square_ring(gx, gz, 2):
        bp.stairs(x, LA2 + 1, z, PGS_ST, _face_out(gx, gz, x, z))
    bp.set(gx, LA2 + 2, gz, MOD["waystone"])
    candles(bp, [(gx - 1, LA2 + 2, gz - 1), (gx + 1, LA2 + 2, gz + 1), (gx - 2, LA2 + 1, gz + 2),
                 (gx + 2, LA2 + 1, gz - 2)], seed=8)
    for x in (32, 42):                                                 # reading tables with benches
        for z in (42, 48):
            bp.set(x, LA2 + 1, z, "dark_oak_fence")
            bp.set(x, LA2 + 2, z, "dark_oak_pressure_plate[powered=false]")
            bp.stairs(x, LA2 + 1, z + 1, "dark_oak_stairs", "north")
    for z in range(40, 51):                                            # shelves on the end walls
        for y in range(LA2 + 1, LA2 + 6):
            if z % 3:
                bp.set(31, y, z, SHELF)
    for (x, z) in ((33, 40), (41, 40), (33, 50), (41, 50)):
        for y in range(LA2 + 1, LA2 + 8):
            bp.set(x, y, z, PGS if y != LA2 + 5 else RUNE)
    hang(bp, gx, LA2 + 9, gz, 2)
    hang(bp, 34, LA2 + 9, 45, 3, soul=True)
    for z in (40, 41, 42, 43, 44):                                      # a runner from the waystone to the portal
        for x in (cx - 1, cx, cx + 1):
            if bp.get(x, LA2 + 1, z) in (None, "minecraft:air"):
                bp.set(x, LA2 + 1, z, "purple_carpet" if x == cx else "black_carpet")
    for x in (cx - 2, cx + 2):                                         # the portal: carved jambs, rune lamps
        for y in range(LA2 + 1, LA2 + 6):
            bp.set(x, y, 39, CGS if y in (LA2 + 1, LA2 + 5) else PGS)
        bp.set(x, LA2 + 6, 39, RUNE)


def _furnish_archive(bp):
    cx, cz = ARENA
    rng = random.Random(640)
    # candles along the gallery railings, lanterns under them
    for gy in GALLERIES:
        for k in range(24):
            a = math.radians(k * 15 + 7.5)
            x, z = cx + round(math.cos(a) * (AR - 1)), cz + round(math.sin(a) * (AR - 1))
            if bp.get(x, gy + 1, z) == "minecraft:dark_oak_fence" and k % 2 == 0:
                bp.set(x, gy + 2, z, "candle[candles=%d,lit=true,waterlogged=false]" % rng.randint(1, 4))
        for k in range(8):
            a = math.radians(k * 45 + 22.5)
            x, z = cx + round(math.cos(a) * AR), cz + round(math.sin(a) * AR)
            bp.lantern(x, gy - 2, z, hanging=True, soul=gy == GALLERIES[1])
    # lecterns and tables on the galleries, a few open books (chiseled shelves) facing the floor
    for gy in GALLERIES:
        for k in range(6):
            a = math.radians(k * 60 + gy * 7)
            x, z = cx + round(math.cos(a) * AR), cz + round(math.sin(a) * AR)
            if bp.get(x, gy, z) == "minecraft:dark_oak_planks":
                bp.set(x, gy + 1, z, "lectern[facing=%s,has_book=false,powered=false]" % _face_in(cx, cz, x, z))
    # reading lamps standing at the foot of the wall between the doors
    for k in range(8):
        a = math.radians(k * 45)
        x, z = cx + round(math.cos(a) * (AR - 0.6)), cz + round(math.sin(a) * (AR - 0.6))
        if abs(x - cx) <= 2 or abs(z - cz) <= 2:
            continue
        bp.set(x, LA2 + 1, z, PGS)
        bp.set(x, LA2 + 2, z, RUNE)
    bp.boss_seal(cx, LA2, cz, "wayfarers:archivist", AR)


def _furnish_vault(bp):
    """The restricted vault: chained books, a reading desk, the reward chests."""
    for z in range(12, 25):
        for y in range(LA2 + 1, LA2 + 6):
            if z % 4:
                bp.set(6, y, z, cshelf("east", z * 7 + y))
    for x in range(7, 16, 2):
        for z, f in ((12, "south"), (24, "north")):
            for y in range(LA2 + 1, LA2 + 5):
                bp.set(x, y, z, SHELF)
            bp.set(x + 1, LA2 + 3, z, "iron_chain[axis=y,waterlogged=false]")
    bp.chest(8, LA2 + 1, 16, "east", LOOT + "library_secret")
    bp.chest(8, LA2 + 1, 20, "east", LOOT + "library")
    bp.set(8, LA2 + 1, 18, "enchanting_table")
    for (x, z) in ((7, 15), (7, 21)):
        bp.set(x, LA2 + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(12, LA2 + 1, 18, "lectern[facing=west,has_book=false,powered=false]")
    hang(bp, 11, LA2 + 8, 18, 2)
    bp.set(16, LA2 + 1, 14, RUNE)
    bp.set(16, LA2 + 1, 22, RUNE)
