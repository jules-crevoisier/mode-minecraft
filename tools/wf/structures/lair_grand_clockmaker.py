"""Lair of the Grand Clockmaker, under the clock tower of the Clockwork Citadel (tools/wf/structures/clockwork.py).

A stair opens in the floor of the tower's entrance hall (east side) and goes down two levels:

* level 1, the Gearworks (floor y = L1): the machine room that drives the clock above, with wall cogs, pipe
  bundles, gauges, a Clockwork Spider spawner among the machines and two workshop chests;
* from its south wall a second stair falls to level 2 (floor y = L2): the site of grace, a little brass waiting
  room with a waystone, benches and Edison lamps, before the mist;
* the Clock Vault, the arena (radius AR): a round hall whose floor is a giant cream clock face stopped at midnight,
  twelve brass pilasters (one per hour) with Edison lamps, wall cogs, a dark iron dome hung with lamps and a great
  brass pendulum swinging high over the seal;
* past the arena to the west, the Clockmaker's study holds the reward.

Rooms are solid shells carved hollow (they are underground), so shells come first, interiors next, then doors,
furniture, lights and the mist. Everything stays below the plaza floor (y = 0) except the stair mouth.
"""
import math

from .. import arch as A
from ..arch import Palette
from ..parts import LOOT, MOD
from .lair_bell_keeper import cove, hang, hollow, opening, solid

W = "brasshaven:"
BRASS, COPPER, IRON = W + "brass_plating", W + "copper_plating", W + "dark_iron_plating"
TREAD, GEAR, PIPES, GAUGE = W + "diamond_plate", W + "gear_panel", W + "copper_pipes", W + "pressure_gauge"
EDISON, AETHER, MAHOGANY, LEATHER, SMOKE = (W + "edison_lamp", W + "aether_conduit", W + "mahogany_panelling",
                                           W + "leather_padding", W + "smokestack_bricks")
BRASS_ST, SMOKE_ST, TREAD_SLAB = W + "brass_plating_stairs", W + "smokestack_brick_stairs", W + "diamond_plate_slab"
HANGING = W + "hanging_edison_lamp"
CHANDELIER = W + "brass_chandelier"
CREAM = "white_terracotta"

L1 = -10                 # Gearworks floor
L2 = -21                 # vault floor (feet at L2 + 1)
ARENA = (-12, 30)        # Clock Vault centre (x, z)
AR = 13                  # clear floor radius
WALL_TOP = L2 + 12       # the drum wall springs the dome here
DOME = 6                 # dome rise above the drum (stays under the plaza)
GEARWORKS = (1, 4, 13, 15)        # x0, z0, x1, z1 (shell)
GRACE = (4, 26, 16, 34)           # site of grace shell
STUDY = (-40, 25, -29, 35)        # reward room shell

SHELL = Palette({SMOKE: 6, IRON: 3, "deepslate_bricks": 1}, seed=611, scale=2.5)
DEEP = Palette({"deepslate_bricks": 4, "polished_deepslate": 2, "cracked_deepslate_bricks": 1}, seed=612, scale=2.0)
FLOOR_PAL = Palette({TREAD: 4, IRON: 1}, seed=613, scale=2.0)


def build(bp):
    """Called at the end of the citadel builder."""
    stair_down(bp)
    gearworks(bp)
    second_stair(bp)
    vault(bp)
    grace(bp)
    study(bp)
    doors(bp)
    furnish(bp)
    mists(bp)


# ------------------------------------------------------------------------ stairs
def _stairs(bp, x0, x1, z0, z1, y0, head=4):
    """A straight 3-wide stair falling one block per block of +z from (z0, y0); solid fill under each step, air
    above it, a ceiling only where it stays underground (the top steps open into the room above)."""
    for z in range(z0, z1 + 1):
        y = y0 - (z - z0)
        top = min(y + head + 1, -1)                         # never build into the rooms above ground
        for x in range(x0 - 1, x1 + 2):
            solid(bp, x, y - 3, z, x, top, z, SHELL)
        for x in range(x0, x1 + 1):
            bp.stairs(x, y, z, SMOKE_ST, "north")
            bp.clear(x, y + 1, z, x, min(y + head, 0), z)   # head room; near the top it opens the hall floor
            if y + head + 1 <= -1:
                bp.set(x, y + head + 1, z, IRON if (z % 4) else BRASS)
        for x in (x0 - 1, x1 + 1):                          # brass handrail band in the side walls
            if y + 2 < 0:
                bp.set(x, y + 2, z, BRASS if z % 3 else EDISON)


def stair_down(bp):
    """From the tower's entrance hall (east side, x 4..6) down to the Gearworks: z -5 .. 3, y -1 .. -9."""
    _stairs(bp, 4, 6, -5, 3, -1)
    # the mouth in the hall floor, entered from the north: a brass railing along its open west side, the two
    # chairs that stood there moved aside, a lamp post at the corner
    for x in (4, 5, 6):
        bp.set(x, 1, -5, "air")                             # the hall chairs that stood over the stairwell
        bp.set(x, 1, -1, f"{W}brass_railing[facing=south]")  # keeps whoever comes in by the east door from falling
    for z in range(-5, -1):
        bp.set(3, 1, z, f"{W}brass_railing[facing=west]")
    bp.set(3, 1, -1, IRON)
    bp.set(3, 2, -1, EDISON)
    # the top steps end a block below the hall floor against the north wall: a landing sunk in the floor at their
    # head (z -6, under the foot of the corner pier) and a last step up to the west
    for x in (4, 5, 6):
        bp.set(x, -1, -6, TREAD)
        bp.set(x, 0, -6, "air")
    bp.set(6, 1, -6, "air")
    bp.stairs(3, 0, -6, SMOKE_ST, "west")


def second_stair(bp):
    """From the Gearworks' south wall down to the site of grace: x 9..11, z 16..25, y -11 .. -20."""
    _stairs(bp, 9, 11, 16, 25, L1 - 1)


# ------------------------------------------------------------------------ level 1: the Gearworks
def gearworks(bp):
    x0, z0, x1, z1 = GEARWORKS
    hollow(bp, x0, L1, z0, x1, L1 + 7, z1, SHELL, FLOOR_PAL)
    cove(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L1 + 6, BRASS_ST)
    for x in range(x0 + 2, x1, 4):                        # iron ribs across the ceiling
        for z in range(z0 + 1, z1):
            bp.set(x, L1 + 7, z, IRON)
    # the drive shaft: a copper pipe column from the floor to the ceiling, going up to the clock
    for y in range(L1 + 1, L1 + 7):
        bp.set(7, y, 10, W + "copper_pipe[axis=y]")
    bp.set(7, L1 + 1, 10, GEAR)


# ------------------------------------------------------------------------ level 2: the Clock Vault
def dome_y(r):
    """Highest air block of the dome at distance r from the vault axis."""
    return math.floor(WALL_TOP + DOME * math.sqrt(max(0.0, 1 - (r / (AR + 1.5)) ** 2)))


def _face_out(cx, cz, x, z):
    dx, dz = x - cx, z - cz
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _floor(dx, dz, d):
    """The floor is a clock face stopped at midnight: dark tread rim, brass ring, cream dial with brass hour marks,
    two iron hands pointing to twelve (north), a gear-panel boss in the middle."""
    if d >= AR - 0.5:
        return TREAD
    if d >= AR - 1.6:
        return BRASS
    ang = (math.degrees(math.atan2(dx, -dz)) + 360) % 360       # 0 = north (twelve o'clock)
    hour = min(ang % 30, 30 - ang % 30)
    if AR - 4.2 <= d < AR - 1.6 and hour * math.pi / 180 * d < 0.7:
        return BRASS if round(ang / 30) % 3 else W + "gear_panel"   # quarter hours are clockwork panels
    if d < 1.6:
        return GEAR
    if dz < 0 and abs(dx) < 0.6 and d < AR - 3.0:
        return IRON                                                  # the minute hand
    if dz < 0 and abs(dx) < 1.1 and d < AR - 6.0:
        return IRON                                                  # the hour hand (wider, shorter)
    if 5.5 <= d < 6.4:
        return "smooth_sandstone"                                    # inner ring line
    return CREAM


def vault(bp):
    cx, cz = ARENA
    R = AR
    for x in range(cx - R - 5, cx + R + 6):
        for z in range(cz - R - 5, cz + R + 6):
            d = math.hypot(x - cx, z - cz)
            if d > R + 3.5:
                continue
            for y in range(L2 - 2, L2):
                bp.set(x, y, z, DEEP.pick(x, y, z))
            inner = dome_y(min(d, R + 1))
            if d <= R + 0.5:
                bp.set(x, L2, z, _floor(x - cx, z - cz, d))
                bp.clear(x, L2 + 1, z, x, inner, z)
                solid(bp, x, inner + 1, z, x, min(inner + 2, -1), z, Palette({IRON: 3, SMOKE: 1}, seed=614))
            else:
                solid(bp, x, L2, z, x, min(inner + 2, -1), z, SHELL)
    # twelve brass pilasters, one per hour, with Edison lamps; between them recessed wall cogs
    for k in range(12):
        a = math.radians(k * 30 - 90)
        px, pz = cx + round(math.cos(a) * (R + 0.6)), cz + round(math.sin(a) * (R + 0.6))
        for y in range(L2 + 1, WALL_TOP + 1):
            bp.set(px, y, pz, BRASS if y not in (L2 + 6,) else EDISON)
        bp.set(px, WALL_TOP + 1, pz, GEAR)
    # ribs of the dome: twelve bands of dark iron toward the centre
    for k in range(12):
        a = math.radians(k * 30 - 90)
        for r10 in range(30, (R + 1) * 10, 5):
            r = r10 / 10
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            bp.set(x, dome_y(r) + 1, z, IRON)
    # cornice where the dome springs
    for x in range(cx - R - 2, cx + R + 3):
        for z in range(cz - R - 2, cz + R + 3):
            d = math.hypot(x - cx, z - cz)
            if R - 0.5 < d <= R + 0.5 and bp.get(x, WALL_TOP, z) == "minecraft:air":
                bp.set(x, WALL_TOP, z, A.stair(SMOKE_ST, _face_out(cx, cz, x, z), "top"))
    _pendulum(bp, cx, cz)


def _pendulum(bp, cx, cz):
    """The great pendulum hanging from the dome over the seal (high enough to fight under: the bob is 9 blocks up)."""
    top = dome_y(0)
    bp.set(cx, top + 1, cz, GEAR)
    bp.chain(cx, L2 + 11, cz, top)
    bob_y = L2 + 10
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(cx + dx, bob_y, cz + dz, BRASS if (dx == 0 or dz == 0) else W + "brass_plating_slab[type=top,waterlogged=false]")
    bp.set(cx, bob_y - 1, cz, W + "brass_plating_slab[type=top,waterlogged=false]")
    bp.set(cx, bob_y, cz, AETHER)


def grace(bp):
    x0, z0, x1, z1 = GRACE
    hollow(bp, x0, L2, z0, x1, L2 + 7, z1, SHELL, Palette({MAHOGANY: 3, TREAD: 1}, seed=615))
    cove(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L2 + 6, BRASS_ST)


def study(bp):
    """The Clockmaker's study (reward): mahogany panels, a workbench of half-built automatons, the chests."""
    x0, z0, x1, z1 = STUDY
    hollow(bp, x0, L2, z0, x1, L2 + 7, z1, Palette({MAHOGANY: 3, SMOKE: 1}, seed=616), Palette({TREAD: 1}, seed=617))
    cove(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, L2 + 6, BRASS_ST)


# ------------------------------------------------------------------------ connections
def doors(bp):
    cx, cz = ARENA
    gx0, gz0, gx1, gz1 = GEARWORKS
    # stair 1 -> Gearworks (north wall), Gearworks -> stair 2 (south wall)
    opening(bp, 4, L1 + 1, gz0, 6, L1 + 4, gz0)
    opening(bp, 9, L1 + 1, gz1, 11, L1 + 3, gz1)
    for x in (9, 10, 11):                               # the stair's last step, in the doorway
        bp.stairs(x, L1, gz1, SMOKE_ST, "north")
    # stair 2 -> site of grace (north wall)
    opening(bp, 9, L2 + 1, GRACE[1], 11, L2 + 4, GRACE[1])
    # grace -> vault (east side of the drum) and vault -> study (west side): 3 wide, 4 tall
    opening(bp, cx + AR + 1, L2 + 1, cz - 1, GRACE[0], L2 + 4, cz + 1, BRASS, BRASS_ST, axis="z")
    opening(bp, STUDY[2], L2 + 1, cz - 1, cx - AR - 1, L2 + 4, cz + 1, BRASS, BRASS_ST, axis="z")
    for x in list(range(cx + AR + 1, GRACE[0] + 1)) + list(range(STUDY[2], cx - AR)):
        for z in (cz - 1, cz, cz + 1):
            bp.set(x, L2, z, TREAD)


def mists(bp):
    cx, cz = ARENA
    bp.mist(cx + AR + 2, L2 + 1, cz - 1, cx + AR + 2, L2 + 4, cz + 1)    # from the site of grace
    bp.mist(cx - AR - 2, L2 + 1, cz - 1, cx - AR - 2, L2 + 4, cz + 1)    # to the study


# ------------------------------------------------------------------------ furniture, lights, encounters
def furnish(bp):
    _furnish_gearworks(bp)
    _furnish_grace(bp)
    _furnish_vault(bp)
    _furnish_study(bp)


def _furnish_gearworks(bp):
    x0, z0, x1, z1 = GEARWORKS
    # wall cogs and pipe bundles along the east and west walls, gauges between them
    for z in range(z0 + 2, z1 - 1, 2):
        bp.set(x0 + 1, L1 + 3, z, f"{W}wall_cog[facing=east]" if z % 4 else GAUGE)
        bp.set(x1 - 1, L1 + 3, z, f"{W}wall_cog[facing=west]" if z % 4 == 0 else GAUGE)
        bp.set(x0 + 1, L1 + 1, z, PIPES)
        bp.set(x1 - 1, L1 + 1, z, PIPES)
    # two rows of humming machines (decor) around the drive shaft
    for x, z in ((4, 8), (4, 12), (10, 8), (10, 12)):
        bp.set(x, L1 + 1, z, W + "block_breaker[facing=up,powered=false]")
        bp.set(x, L1 + 2, z, GEAR)
    for x in (5, 6, 8, 9):
        bp.set(x, L1 + 1, 10, W + "copper_pipe[axis=x]")
    bp.set(7, L1 + 2, 9, W + "valve_wheel[facing=north]")
    # the spider nest among the machines
    bp.spawner(7, L1 + 1, 7, "brasshaven:clockwork_spider")
    bp.set(7, L1 + 2, 7, W + "brass_plating_slab[type=bottom,waterlogged=false]")
    bp.chest(x0 + 1, L1 + 1, z1 - 1, "east", loot=LOOT + "clockwork_workshop")
    bp.chest(x1 - 1, L1 + 1, z0 + 1, "west", loot=LOOT + "clockwork_workshop")
    bp.set(x0 + 2, L1 + 1, z1 - 1, W + "mahogany_table")
    for x, z in ((4, 7), (10, 13), (4, 13)):
        bp.set(x, L1 + 6, z, HANGING)
    bp.set(10, L1 + 6, 6, HANGING)


def _furnish_grace(bp):
    """Waystone on a brass dais, leather benches, Edison lamps, a gauge panel; the arena door to the west."""
    x0, z0, x1, z1 = GRACE
    cz = ARENA[1]
    gx, gz = 13, cz
    solid(bp, gx - 1, L2 + 1, gz - 1, gx + 1, L2 + 1, gz + 1, BRASS)
    bp.set(gx, L2 + 2, gz, MOD["waystone"])
    for x in range(x0 + 2, x1 - 1):
        if x not in (9, 10, 11):
            bp.stairs(x, L2 + 1, z1 - 1, "dark_oak_stairs", "south")
    for x in (x0 + 2, x1 - 2):
        bp.set(x, L2 + 1, z0 + 1, LEATHER)
    for (x, z) in ((x0 + 1, z0 + 1), (x1 - 1, z0 + 1), (x1 - 1, z1 - 1), (x0 + 1, z1 - 1)):
        for y in range(L2 + 1, L2 + 6):
            bp.set(x, y, z, BRASS if y != L2 + 4 else EDISON)
    bp.set(x1 - 1, L2 + 3, cz, GAUGE)
    bp.set(x1 - 1, L2 + 2, cz, W + "valve_wheel[facing=west]")
    bp.set(gx, L2 + 6, gz, CHANDELIER)
    for x in range(x0 + 1, gx - 1):                         # a red runner to the arena door
        bp.set(x, L2 + 1, cz, "red_carpet")


def _furnish_vault(bp):
    cx, cz = ARENA
    # wall cogs between the pilasters (keeping the two doorways clear), copper pipes under the cornice
    for k in range(12):
        a = math.radians(k * 30 - 75)
        x, z = cx + round(math.cos(a) * (AR + 1)), cz + round(math.sin(a) * (AR + 1))
        if abs(z - cz) <= 2:
            continue
        face = {"east": "west", "west": "east", "north": "south", "south": "north"}[_face_out(cx, cz, x, z)]
        bp.set(x, L2 + 4, z, f"{W}wall_cog[facing={face}]")
        bp.set(x, L2 + 2, z, f"{W}wall_cog[facing={face}]")
    for k in range(24):
        a = math.radians(k * 15)
        x, z = cx + round(math.cos(a) * (AR + 1)), cz + round(math.sin(a) * (AR + 1))
        bp.set(x, WALL_TOP - 1, z, PIPES)
    # lamps hanging from the dome on a ring
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = cx + round(math.cos(a) * 8), cz + round(math.sin(a) * 8)
        top = dome_y(8)
        bp.chain(x, top - 2, z, top)
        bp.set(x, top - 3, z, HANGING)
    bp.boss_seal(cx, L2, cz, "brasshaven:grand_clockmaker", AR)


def _furnish_study(bp):
    x0, z0, x1, z1 = STUDY
    cz = ARENA[1]
    # workbench with a half-built automaton (brass block body, gear panel head) and drafting tables
    for x in range(x0 + 2, x0 + 6):
        bp.set(x, L2 + 1, z0 + 1, W + "mahogany_table")
    bp.set(x0 + 3, L2 + 2, z0 + 1, W + "pressure_gauge")
    bp.set(x0 + 8, L2 + 1, z0 + 2, "brasshaven:brass_block")
    bp.set(x0 + 8, L2 + 2, z0 + 2, GEAR)
    bp.set(x0 + 9, L2 + 1, z0 + 2, W + "copper_pipe[axis=y]")
    for z in range(z0 + 3, z1 - 2):
        bp.set(x0 + 1, L2 + 2, z, "bookshelf")
        bp.set(x0 + 1, L2 + 3, z, "bookshelf")
    bp.set(x0 + 1, L2 + 1, cz, "lectern[facing=east,has_book=false,powered=false]")
    bp.chest(x0 + 2, L2 + 1, z1 - 1, "north", loot=LOOT + "clockwork_vault")
    bp.chest(x0 + 4, L2 + 1, z1 - 1, "north", loot=LOOT + "clockwork_vault")
    bp.chest(x0 + 6, L2 + 1, z1 - 1, "north", loot=LOOT + "clockwork_workshop")
    bp.set(x0 + 3, L2 + 1, z1 - 2, W + "mahogany_chair[facing=south]")
    bp.set((x0 + x1) // 2, L2 + 6, cz, CHANDELIER)
    for (x, z) in ((x0 + 1, z0 + 1), (x1 - 1, z1 - 1), (x1 - 1, z0 + 1), (x0 + 1, z1 - 1)):
        bp.set(x, L2 + 4, z, EDISON)
