"""Sky Harbour: an iron mooring tower with a steam airship docked at its top (Lot 6, mega-structures).

Ground y = 0. The tower (7x7 lattice, 44 high) carries a landing deck and a docking arm; the airship floats
east of it, its deck level with the arm: a mahogany hull with portholes, a cabin, stern propeller and side
engines, held under a striped envelope by chains.
"""
import math

from .. import interior as INT
from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..parts import LOOT

W = "wayfarers:"
BRASS, IRON, TREAD = W + "brass_plating", W + "dark_iron_plating", W + "diamond_plate"
MAHOGANY, GEAR, PIPES, EDISON = W + "mahogany_panelling", W + "gear_panel", W + "copper_pipes", W + "edison_lamp"
SMOKE, COPPER = W + "smokestack_bricks", W + "copper_plating"
OXI_SLAB = "oxidized_cut_copper_slab[type=bottom,waterlogged=false]"

DECK = 44          # tower deck and ship deck
SHIP_X = 24        # ship centre line (x)
HALF_LEN = 16      # ship half length along z


def railing(bp, x, y, z, facing):
    bp.set(x, y, z, f"{W}brass_railing[facing={facing}]")


# ------------------------------------------------------------------ tower
def tower(bp):
    r = 3
    # footing
    for x in range(-r - 2, r + 3):
        for z in range(-r - 2, r + 3):
            bp.set(x, 0, z, IRON if max(abs(x), abs(z)) > r else TREAD)
    for y in range(1, DECK):
        for x in range(-r, r + 1):
            for z in range(-r, r + 1):
                corner = abs(x) == r and abs(z) == r
                face = max(abs(x), abs(z)) == r
                if corner:
                    bp.set(x, y, z, IRON if y % 6 else BRASS)
                elif face and y % 6 == 0:
                    bp.set(x, y, z, IRON)
                elif face:
                    # diagonal bracing on each face
                    u = x if abs(z) == r else z
                    k = (y % 6)
                    bp.set(x, y, z, "iron_bars[east=true,west=true,north=true,south=true,waterlogged=false]"
                           if abs(u) == abs(k - 3) else "air")
                else:
                    bp.set(x, y, z, "air")
    # ladder up the inside of the west face
    for y in range(1, DECK):
        bp.set(-r + 1, y, 0, "ladder[facing=east,waterlogged=false]")
    for y in range(1, DECK):
        bp.set(-r, y, 0, IRON)
    # landings every 12 blocks
    for y in (12, 24, 36):
        for x in range(-r + 1, r):
            for z in range(-r + 1, r):
                if (x, z) != (-r + 1, 0):
                    bp.set(x, y, z, TREAD)
        bp.set(0, y - 1, 0, W + "hanging_edison_lamp")
    # top deck with railings and a beacon lamp
    R = 6
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            bp.set(x, DECK, z, TREAD if max(abs(x), abs(z)) < R else IRON)
            if max(abs(x), abs(z)) == R and not (x == R and abs(z) <= 1):
                facing = ("north" if z < 0 else "south") if abs(z) >= abs(x) else ("west" if x < 0 else "east")
                railing(bp, x, DECK + 1, z, facing)
    bp.set(-r + 1, DECK, 0, "air")  # ladder hatch
    for (x, z) in ((-R, -R), (R, -R), (-R, R), (R, R)):
        bp.set(x, DECK + 1, z, BRASS)
        bp.set(x, DECK + 2, z, EDISON)
    # mast with signal lamp
    for y in range(DECK + 1, DECK + 10):
        bp.set(0, y, 0, IRON)
    bp.set(0, DECK + 10, 0, GEAR)
    bp.set(0, DECK + 11, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # docking arm towards the ship
    for x in range(R + 1, SHIP_X - 6):
        for z in (-1, 0, 1):
            bp.set(x, DECK, z, TREAD)
        railing(bp, x, DECK + 1, -2, "north")
        railing(bp, x, DECK + 1, 2, "south")
        bp.set(x, DECK, -2, IRON)
        bp.set(x, DECK, 2, IRON)
        if (x - R) % 4 == 0:
            bp.set(x, DECK - 1, 0, stair(W + "brass_plating_stairs", "west", "top"))
    # cargo at the foot of the tower
    for (x, z) in ((5, 4), (6, 4), (5, 5), (-5, -4), (-6, -5)):
        bp.set(x, 1, z, W + "compacting_crate[facing=north]")
    bp.barrel(-5, 1, 4, "up", loot=LOOT + "sky_harbour")
    bp.chest(4, DECK + 1, -4, "south", loot=LOOT + "sky_harbour")
    for (x, z) in ((-6, 6), (6, -6)):
        bp.set(x, 1, z, IRON)
        bp.set(x, 2, z, W + "smokestack_brick_wall")
        bp.set(x, 3, z, EDISON)


# ------------------------------------------------------------------ airship
def _half_width(z):
    t = z / (HALF_LEN + 0.5)
    return 5.2 * math.sqrt(max(0.0, 1 - t ** 4))


def hull(bp):
    for z in range(-HALF_LEN, HALF_LEN + 1):
        hw = _half_width(z)
        for y in range(DECK - 8, DECK + 1):
            depth = DECK - y
            w = hw * (1 - (depth / 9.0) ** 2)
            wi = int(round(w))
            if wi < 1 and depth > 0:
                continue
            for x in range(SHIP_X - wi, SHIP_X + wi + 1):
                edge = abs(x - SHIP_X) == wi or y == DECK - 8 or abs(z) >= HALF_LEN - 1
                if y == DECK:
                    bp.set(x, y, z, "spruce_planks" if abs(x - SHIP_X) < wi else BRASS)
                elif edge:
                    porthole = y == DECK - 3 and abs(x - SHIP_X) == wi and z % 4 == 0 and abs(z) < HALF_LEN - 3
                    band = y == DECK - 1
                    bp.set(x, y, z, "glass" if porthole else (BRASS if band else MAHOGANY))
                else:
                    bp.set(x, y, z, "air")
    # keel
    for z in range(-HALF_LEN + 2, HALF_LEN - 1):
        bp.set(SHIP_X, DECK - 9, z, IRON)
    # lower hold: floor, cargo, lamp
    for z in range(-HALF_LEN + 4, HALF_LEN - 3):
        for x in range(SHIP_X - 2, SHIP_X + 3):
            bp.set(x, DECK - 5, z, "spruce_planks")
    bp.chest(SHIP_X - 2, DECK - 4, 6, "east", loot=LOOT + "sky_harbour")
    bp.set(SHIP_X + 2, DECK - 4, 6, W + "compacting_crate[facing=west]")
    bp.set(SHIP_X, DECK - 1, 0, W + "hanging_edison_lamp")
    bp.set(SHIP_X, DECK - 4, -10, "ladder[facing=south,waterlogged=false]")
    for y in range(DECK - 4, DECK):
        bp.set(SHIP_X, y, -10, "ladder[facing=south,waterlogged=false]")
        bp.set(SHIP_X, y, -11, MAHOGANY)
    bp.set(SHIP_X, DECK, -10, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    # deck railings
    for z in range(-HALF_LEN + 1, HALF_LEN):
        wi = int(round(_half_width(z)))
        for side, facing in ((-1, "west"), (1, "east")):
            x = SHIP_X + side * wi
            if side < 0 and abs(z) <= 1:
                continue  # gangway opening towards the tower
            railing(bp, x, DECK + 1, z, facing)
    # gangway from the docking arm
    for x in range(SHIP_X - 6, SHIP_X - int(round(_half_width(0))) + 1):
        for z in (-1, 0, 1):
            bp.set(x, DECK, z, TREAD)


def cabin(bp):
    x0, x1, z0, z1, h = SHIP_X - 3, SHIP_X + 3, -6, 4, 4
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(DECK + 1, DECK + h + 1):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    window = y in (DECK + 2, DECK + 3) and not corner and (x in (x0, x1) and z % 2 == 0)
                    bp.set(x, y, z, BRASS if corner else ("glass_pane" if window else COPPER))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, DECK + h + 1, z, OXI_SLAB)
    for y in (DECK + 1, DECK + 2):
        bp.set(SHIP_X, y, z1, "air")
    bp.door(SHIP_X, DECK + 1, z1, "south", "dark_oak")
    # inside: chart table, chairs, helm, lamp
    bp.set(SHIP_X, DECK + 1, -2, W + "mahogany_table")
    bp.set(SHIP_X - 1, DECK + 1, -2, f"{W}mahogany_chair[facing=east]")
    bp.set(SHIP_X + 1, DECK + 1, -2, f"{W}mahogany_chair[facing=west]")
    bp.set(SHIP_X, DECK + 2, z0 + 1, f"{W}valve_wheel[facing=south]")
    bp.set(SHIP_X, DECK + 1, z0 + 1, GEAR)
    bp.set(SHIP_X, DECK + h, 0, W + "brass_chandelier")
    bp.chest(x1 - 1, DECK + 1, 2, "west", loot=LOOT + "sky_harbour")


def engines(bp):
    # stern propeller: a cross of gear panels on a shaft
    zs = HALF_LEN + 1
    bp.set(SHIP_X, DECK - 2, HALF_LEN, IRON)
    bp.set(SHIP_X, DECK - 2, zs, BRASS)
    for d in range(1, 4):
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            bp.set(SHIP_X + dx, DECK - 2 + dy, zs + 1, GEAR)
    # side engines with smoking stacks
    for side in (-1, 1):
        ex = SHIP_X + side * 7
        for z in range(-3, 4):
            for y in (DECK - 2, DECK - 1):
                bp.set(ex, y, z, COPPER if abs(z) < 3 else BRASS)
        for x in range(SHIP_X + side * 5, ex, side):
            bp.set(x, DECK - 1, 0, W + "copper_pipe[axis=x]")
        for d in range(1, 3):
            for dz, dy in ((0, d), (0, -d), (d, 0), (-d, 0)):
                bp.set(ex, DECK - 1 + dy, 4 + 1 + max(0, dz), GEAR if dz == 0 else GEAR)
        for y in range(DECK, DECK + 3):
            bp.set(ex, y, -1, SMOKE)
        bp.set(ex, DECK + 2, -1, "hay_block[axis=y]")
        bp.set(ex, DECK + 3, -1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def envelope(bp):
    cy, rx, ry, rz = DECK + 15, 8, 7, HALF_LEN + 5
    for x in range(SHIP_X - rx - 1, SHIP_X + rx + 2):
        for y in range(cy - ry - 1, cy + ry + 2):
            for z in range(-rz - 1, rz + 2):
                d = ((x - SHIP_X) / rx) ** 2 + ((y - cy) / ry) ** 2 + (z / rz) ** 2
                if d <= 1.0:
                    shell = ((abs(x - SHIP_X) + 1) / rx) ** 2 + ((abs(y - cy) + 1) / ry) ** 2 + ((abs(z) + 1) / rz) ** 2 > 1.0
                    if shell:
                        band = z in (-12, 0, 12)
                        stripe = z % 6 in (0, 1)
                        bp.set(x, y, z, BRASS if band else ("red_wool" if stripe and y > cy - 3 else "white_wool"))
                    else:
                        bp.set(x, y, z, "air")
    # tail fins
    for d in range(1, 6):
        bp.set(SHIP_X, cy + ry - 2 + d // 2, rz - 1 + d, "red_wool")
        bp.set(SHIP_X - 2 - d // 2, cy, rz - 1 + d, "white_wool")
        bp.set(SHIP_X + 2 + d // 2, cy, rz - 1 + d, "white_wool")
    # chains from the envelope down to the deck rails
    bottom = cy - ry
    for z in (-10, 0, 10):
        for side in (-1, 1):
            x = SHIP_X + side * 4
            for y in range(DECK + 1, bottom + 1):
                if bp.get(x, y, z) is None or bp.get(x, y, z) == "minecraft:air":
                    bp.chain(x, y, z, y)


def harbour(bp):
    tower(bp)
    hull(bp)
    cabin(bp)
    engines(bp)
    envelope(bp)
    # the crew: a navigator at the chart table, an engineer in the hold, a quartermaster; a trader at the
    # foot of the tower waiting for the next flight
    INT.populate(bp, [("cartographer", 3), ("toolsmith", 2), "armorer", "fisherman"], seed=1, bell=(-6, 1, 0))
    INT.decorate(bp, dict(INT.THEMES["steampunk"], density=0.35), seed=1)
    INT.wandering_trader(bp, *INT.open_spot(bp, (8, 1, 2), height=2), facing="west")
    INT.yard(bp, (-14, -14, 14, 14), 1, "harbour", count=5, seed=1)


register(StructureDef(
    "sky_harbour", "overworld",
    ["plains", "meadow", "savanna", "sunflower_plains", "#minecraft:is_hill", "windswept_savanna"],
    [Piece("harbour", harbour)],
    spacing=56, separation=20, adaptation="beard_thin", processors="none", max_distance=100,
    peaceful=True,
    title_fr="Port céleste", title_en="Sky Harbour"))
