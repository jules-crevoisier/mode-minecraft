"""Living oceans: small, frequent structures of the sea floor (tools/wf/ocean.py has the creatures and scenery).

  * Sunken Submarine: a riveted steampunk submarine lying on the sand, a breach in its flank, control room and
    engine room flooded, loot in the chart table and the engine room.
  * Diving Bell: a brass bell standing on four legs with a pocket of AIR inside (enter from below through the moon
    pool): a refuge to breathe, with the diver's barrels.
  * Coral Shrine (warm seas): a ring of prismarine columns under a broken dome, overgrown by coral, an altar and its
    offering chest.
  * Shipwreck Debris: what is left of a ship scattered on the sand: hull ribs, a fallen mast with its torn sail, a
    cannon, the anchor and spilled cargo, and the captain's chest half buried.

Blueprint y = 0 is the sea-floor layer (sand), structures are placed on OCEAN_FLOOR_WG. Interiors are cleared with
water (bp.underwater), except the diving bell's air pocket, which is sealed on every side but the moon pool, and
holds no waterloggable block (any of them would be filled with water when placed).
"""
import math
import random

from .. import arch
from .. import interior as INT
from ..arch import Palette
from ..defs import Piece, StructureDef, register
from ..parts import LOOT

W = "brasshaven:"
BRASS, COPPER, VERD, IRON = W + "brass_plating", W + "copper_plating", W + "verdigris_plating", W + "dark_iron_plating"
GEAR, GAUGE, LAMP, GRILLE = W + "gear_panel", W + "pressure_gauge", W + "edison_lamp", W + "brass_grille"
SAND = Palette({"sand": 7, "gravel": 1, "clay": 1}, seed=401, scale=3)
SEABED = ("sand", "sandstone", ("gravel", "clay", "sand"))


def seabed(bp, rx, rz, seed, cx=0, cz=0):
    """A sandy patch the structure rests on (y = 0), with a skirt down into the sea floor."""
    rng = random.Random(seed)
    for x in range(cx - rx - 1, cx + rx + 2):
        for z in range(cz - rz - 1, cz + rz + 2):
            a = math.atan2(z - cz, x - cx)
            wob = 1 + 0.15 * math.sin(a * 3 + seed) + 0.1 * math.cos(a * 5 + seed)
            if ((x - cx) / (rx * wob)) ** 2 + ((z - cz) / (rz * wob)) ** 2 <= 1 + rng.uniform(-0.05, 0.05):
                bp.set(x, 0, z, SAND.pick(x, 0, z), keep=True)


def skirt(bp, seed, depth=4, spread=2):
    top, soil, rubble = SEABED
    arch.terrain_skirt(bp, arch.footprint_of(bp, 0), 0, depth=depth, spread=spread, seed=seed, top="sand",
                       soil=top, rock=soil, rubble=rubble)


def kelp_and_grass(bp, rng, n, rx, rz, cx=0, cz=0, keep_out=None):
    """Kelp stalks and sea grass on free sand around the structure."""
    for _ in range(n):
        x, z = rng.randint(cx - rx, cx + rx), rng.randint(cz - rz, cz + rz)
        if keep_out and keep_out(x, z):
            continue
        if bp.get(x, 0, z) not in ("minecraft:sand", "minecraft:gravel", "minecraft:clay") or bp.get(x, 1, z):
            continue
        if rng.random() < 0.45:
            h = rng.randint(3, 9)
            for y in range(1, h + 1):
                if bp.get(x, y, z):
                    break
                bp.set(x, y, z, "kelp_plant" if y < h else "kelp[age=22]")
        else:
            bp.set(x, 1, z, "seagrass")


# ============================================================ 1. sunken submarine
def submarine(bp):
    bp.underwater = True
    rng = random.Random(411)
    seabed(bp, 15, 8, 412)
    L = 12                      # half length along x (bow at -x)
    CY = 3                      # hull axis height: the keel sinks into the sand

    def radius(x):
        t = x / L
        if t < -0.7:            # pointed bow
            return 3.4 * math.sqrt(max(0.0, 1 - ((t + 0.7) / 0.3) ** 2))
        if t > 0.6:             # tapering stern
            return 3.4 - 2.2 * (t - 0.6) / 0.4
        return 3.4

    hull = {}
    for x in range(-L, L + 1):
        r = radius(x)
        for y in range(CY - 4, CY + 5):
            for z in range(-4, 5):
                d = math.hypot(y - CY, z * 1.05)
                if d <= r + 0.35:
                    hull[(x, y, z)] = d > r - 1.0 or abs(x) == L
    for (x, y, z), shell in hull.items():
        if y < 0:
            bp.set(x, y, z, IRON if shell else "sand")
            continue
        if shell:
            if x % 4 == 0:
                mat = BRASS if y >= CY - 1 else IRON     # brass hoops over the riveted iron keel
            elif y >= CY + 3:
                mat = W + "diamond_plate"                # tread-plate deck
            elif y >= CY + 1:
                mat = IRON if rng.random() < 0.8 else W + "dark_iron_bricks"
            elif y >= CY - 1:
                mat = VERD if rng.random() < 0.7 else COPPER    # verdigris flanks
            else:
                mat = COPPER if rng.random() < 0.6 else IRON
            bp.set(x, y, z, mat)
        else:
            bp.set(x, y, z, "air")
    # portholes along both flanks (glass in the hull, brass frames above and below)
    for x in range(-8, 9, 3):
        for z in (-4, 4):
            if (x, CY, z) in hull and x % 4:
                bp.set(x, CY, z, "glass")
                bp.set(x, CY + 1, z, BRASS)                 # brass brow over each porthole
    # the breach: a torn hole in the starboard flank, plates bent outward on the sand
    for x in range(-2, 3):
        for y in range(CY - 1, CY + 2):
            if abs(x) + abs(y - CY) <= 2:
                bp.set(x, y, 4, "air")
                bp.set(x, y, 3, "air")
    for x, z in ((-1, 6), (1, 7), (3, 6), (0, 8)):
        bp.set(x, 1, z, rng.choice([VERD, COPPER, IRON]))
    bp.set(2, 1, 8, W + "copper_pipe[axis=z]")
    # inner deck and two rooms: control room (bow), engine room (stern), bulkhead between them
    for x in range(-L + 3, L - 2):
        for z in (-1, 0, 1):
            bp.set(x, CY - 2, z, W + "mahogany_parquet" if x < 3 else IRON)
    for z in (-2, -1, 1, 2):
        for y in range(CY - 1, CY + 3):
            if (3, y, z) in hull and not hull[(3, y, z)]:
                bp.set(3, y, z, IRON)
    bp.set(3, CY + 2, 0, IRON)
    bp.set(3, CY + 1, 0, IRON)
    bp.set(3, CY - 1, 0, "air")                          # the bulkhead hatch, blown open
    bp.set(3, CY, 0, "air")
    # control room: chart table with the captain's chest, gauges, a periscope column, a lamp
    bp.set(-6, CY - 1, -2, GAUGE)
    bp.set(-5, CY - 1, -2, W + "valve_wheel[facing=south]")
    bp.set(-7, CY - 1, 2, W + "mahogany_table")
    bp.chest(-6, CY - 1, 2, "north", LOOT + "sunken_submarine")
    bp.set(-3, CY - 1, 2, W + "mahogany_chair[facing=north]")
    for y in range(CY - 1, CY + 3):
        bp.set(-4, y, 0, W + "copper_pipe[axis=y]")
    bp.set(-8, CY + 2, 0, LAMP)
    # engine room: boiler, piston cylinders, pipes, a barrel of spares
    for y in range(CY - 1, CY + 2):
        bp.set(7, y, 0, COPPER if y < CY + 1 else BRASS)
    bp.set(6, CY - 1, -2, GEAR)
    bp.set(8, CY - 1, -2, GEAR)
    bp.set(6, CY - 1, 2, W + "valve_wheel[facing=north]")
    bp.barrel(8, CY - 1, 2, "up", LOOT + "sunken_submarine")
    for x in range(4, 8):
        bp.set(x, CY + 2, -1, W + "copper_pipe[axis=x]")
    bp.set(5, CY + 2, 0, LAMP)
    # conning tower with a glass dome, a hatch and a periscope
    for y in range(CY + 4, CY + 8):
        for x in range(-4, 0):
            for z in range(-1, 2):
                edge = x in (-4, -1) or z in (-1, 1)
                bp.set(x, y, z, (IRON if y < CY + 7 else BRASS) if edge else "air")
    for x in range(-4, 0):
        for z in range(-1, 2):
            bp.set(x, CY + 4, z, bp.get(x, CY + 4, z) or BRASS)
    for x in (-3, -2):
        bp.set(x, CY + 3, 0, "air")
        bp.set(x, CY + 4, 0, "air")
    bp.set(-3, CY + 8, 0, "glass")
    bp.set(-2, CY + 8, 0, "glass")
    bp.set(-3, CY + 7, 0, "air")
    bp.set(-2, CY + 7, 0, "air")
    bp.set(-4, CY + 5, 0, "glass")
    bp.set(-1, CY + 5, 0, "glass")
    bp.set(-2, CY + 8, -1, "iron_trapdoor[facing=south,half=bottom,open=true,powered=false]")
    for y in range(CY + 8, CY + 11):
        bp.set(-1, y, 1, "lightning_rod[facing=up,powered=false]")
    bp.set(-1, CY + 11, 1, "iron_bars")
    # bow: a ram and a searchlight; stern: rudder, diving planes and a three-bladed propeller
    bp.set(-L - 1, CY, 0, IRON)
    bp.set(-L - 2, CY, 0, "lightning_rod[facing=west,powered=false]")
    bp.set(-L + 1, CY + 1, 0, LAMP)
    for y in range(CY - 2, CY + 4):
        bp.set(L + 1, y, 0, IRON)
    for z in (-3, -2, 2, 3):
        bp.set(L - 1, CY, z, IRON)                       # diving planes
    bp.set(L + 2, CY, 0, IRON)
    for (dy, dz) in ((1, 0), (2, 0), (-1, -1), (-2, -1), (-1, 1), (-2, 2)):
        bp.set(L + 3, CY + dy, dz, BRASS)
    bp.set(L + 3, CY, 0, GEAR)
    kelp_and_grass(bp, rng, 70, 15, 8, keep_out=lambda x, z: abs(x) <= L + 3 and abs(z) <= 4)
    skirt(bp, 413)
    INT.decorate(bp, "wreck", seed=1, loot=LOOT + "sunken_submarine", min_area=6)


register(StructureDef(
    "sunken_submarine", "overworld", ["#minecraft:is_ocean"], [Piece("submarine", submarine)],
    spacing=26, separation=8, heightmap="OCEAN_FLOOR_WG", adaptation="none", processors="none",
    title_fr="Sous-marin englouti", title_en="Sunken Submarine"))


# ============================================================ 2. diving bell
def diving_bell(bp):
    bp.underwater = False   # the bell holds air: every other cell we clear must be set to water by hand
    rng = random.Random(421)
    seabed(bp, 8, 8, 422)
    FLOOR = 4                # platform level inside the bell
    TOP = FLOOR + 8

    def r_out(y):
        k = y - FLOOR
        if k <= 4:           # the skirt: almost straight walls
            return 4.6 - 0.1 * k
        t = (k - 4) / (TOP - FLOOR - 4)
        return 4.1 * math.sqrt(max(0.0, 1 - t * t)) + 0.45

    air = set()
    shell = set()
    for y in range(FLOOR, TOP + 1):
        ro = r_out(y)
        for x in range(-5, 6):
            for z in range(-5, 6):
                d = math.hypot(x, z)
                if d <= ro - 1.05 and y < TOP:
                    air.add((x, y, z))
                elif d <= ro + 0.3:
                    shell.add((x, y, z))
    # the platform: everything at FLOOR inside is the floor, except the 2 x 2 moon pool (water)
    pool = {(0, 0), (1, 0), (0, 1), (1, 1)}
    for (x, y, z) in list(air):
        if y == FLOOR:
            air.discard((x, y, z))
            if (x, z) not in pool:
                shell.add((x, y, z))
    # seal: every neighbour of an air cell is air, shell, or the moon-pool water below it
    for (x, y, z) in list(air):
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            p = (x + dx, y + dy, z + dz)
            if p not in air and not (p[1] == FLOOR and (p[0], p[2]) in pool):
                shell.add(p)
    for (x, y, z) in shell:
        k = y - FLOOR
        if k == 0 and math.hypot(x, z) <= r_out(FLOOR) - 1.05:
            bp.set(x, y, z, W + "mahogany_parquet")
        elif k <= 1:
            bp.set(x, y, z, IRON)                                  # heavy iron rim
        elif k == 4 or y == TOP:
            bp.set(x, y, z, BRASS)                                 # brass hoop and crown
        elif k > 4:
            bp.set(x, y, z, VERD if (x * 7 + z * 3 + y) % 4 else COPPER)   # weathered dome
        else:
            bp.set(x, y, z, COPPER if (x * 5 + z * 3 + y) % 6 else W + "copper_tiles")
    for p in air:
        bp.set(*p, "air")
    for (x, z) in pool:
        bp.set(x, FLOOR, z, "water[level=0]")
    # portholes: two-high glass set into the walls, framed in brass (glass is not waterloggable)
    for (x, z) in ((4, 0), (-4, 0), (0, 4), (0, -4)):
        bp.set(x, FLOOR + 2, z, "glass")
        bp.set(x, FLOOR + 3, z, "glass")
        for (fx, fz) in ((z != 0, x != 0), (-(z != 0), -(x != 0))):
            for y in (FLOOR + 2, FLOOR + 3):
                bp.set(x + int(fx), y, z + int(fz), BRASS)
    # inside: barrels of supplies, a lamp, a crafting table, a bench (no waterloggable block in the air!)
    bp.barrel(-2, FLOOR + 1, -2, "up", LOOT + "diving_bell")
    bp.barrel(-3, FLOOR + 1, 0, "up", LOOT + "diving_bell")
    bp.set(2, FLOOR + 1, -2, "crafting_table")
    bp.set(-2, FLOOR + 1, 2, W + "mahogany_table")
    bp.set(0, TOP - 2, 0, LAMP)
    bp.set(0, TOP - 1, 0, BRASS)
    bp.set(2, FLOOR + 1, 2, "cartography_table")
    # four legs down to the sand, cross-braced
    for (x, z) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for y in range(1, FLOOR):
            bp.set(x, y, z, IRON if y % 2 else W + "copper_pipe[axis=y]")
    # the moon pool shaft below the platform stays open (water)
    for y in range(1, FLOOR):
        for (x, z) in pool:
            bp.set(x, y, z, "water[level=0]")
    # winch chain going up, snapped; an air hose snaking over the sand to a broken pump
    for y in range(TOP + 1, TOP + 6):
        bp.set(0, y, 0, "iron_chain[axis=y,waterlogged=true]")
    bp.set(0, TOP + 1, 0, BRASS)
    pts = [(4, 2), (6, 4), (7, 7), (5, 8)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            if not bp.get(x, 1, z):
                bp.set(x, 1, z, W + ("copper_pipe[axis=x]" if abs(x1 - x0) >= abs(z1 - z0) else "copper_pipe[axis=z]"))
    bp.set(-6, 1, 5, IRON)                                     # the broken air pump
    bp.set(-6, 2, 5, COPPER)
    bp.set(-5, 2, 5, W + "valve_wheel[facing=east]")
    bp.set(-5, 1, 6, "barrel[facing=north,open=false]")
    bp.set(-4, 1, -6, "chest[facing=south,type=single,waterlogged=true]", {"LootTable": LOOT + "diving_bell"})
    kelp_and_grass(bp, rng, 40, 8, 8, keep_out=lambda x, z: math.hypot(x, z) <= 5.5)
    skirt(bp, 423)


register(StructureDef(
    "diving_bell", "overworld", ["#minecraft:is_ocean"], [Piece("bell", diving_bell)],
    spacing=24, separation=8, heightmap="OCEAN_FLOOR_WG", adaptation="none", processors="none",
    title_fr="Cloche de plongée", title_en="Diving Bell"))


# ============================================================ 3. coral shrine
SHRINE = Palette({"prismarine_bricks": 5, "prismarine": 3, "dark_prismarine": 1}, seed=431, scale=2.5)
CORALS = ["brain", "tube", "bubble", "fire", "horn"]


def coral_shrine(bp):
    bp.underwater = True
    rng = random.Random(432)
    seabed(bp, 9, 9, 433)
    # round, two-stepped platform
    for x in range(-7, 8):
        for z in range(-7, 8):
            d = math.hypot(x, z)
            if d <= 7.3:
                bp.set(x, 0, z, "dark_prismarine" if d > 6.5 else SHRINE.pick(x, 0, z))
            if d <= 5.3:
                bp.set(x, 1, z, "prismarine_bricks" if d > 4.5 else ("sea_lantern" if (x, z) in ((3, 0), (-3, 0), (0, 3), (0, -3)) else "smooth_sandstone"))
    # six columns, two of them broken
    cols = []
    for i in range(6):
        a = i / 6 * math.tau + 0.3
        cx, cz = round(math.cos(a) * 5), round(math.sin(a) * 5)
        h = 7 if i not in (2, 5) else rng.randint(2, 4)
        cols.append((cx, cz, h))
        for y in range(2, 2 + h):
            bp.set(cx, y, cz, "prismarine_bricks" if y % 3 else "chiseled_sandstone")
        if h == 7:
            bp.set(cx, 9, cz, "dark_prismarine")
        else:
            bp.set(cx + rng.choice((-1, 1)), 2, cz, "prismarine_bricks")       # the fallen drum
    # a ring beam on the standing columns and half a dome above it (the rest has fallen)
    for a in range(48):
        ang = a / 48 * math.tau
        x, z = round(math.cos(ang) * 5), round(math.sin(ang) * 5)
        if math.cos(ang - 2.4) < 0.55:
            bp.set(x, 9, z, "dark_prismarine")
    for y in range(10, 13):
        r = math.sqrt(max(0.0, 25 - ((y - 9) * 1.6) ** 2))
        for x in range(-5, 6):
            for z in range(-5, 6):
                d = math.hypot(x, z)
                if d <= r + 0.3 and math.cos(math.atan2(z, x) - 2.4) <= 0.2 and (d > r - 1.2 or y == 12):
                    # the shell of the dome, a capstone on top; the fallen half is open to the sea
                    bp.set(x, y, z, "prismarine" if (x + y) % 3 else "prismarine_bricks")
    # altar: a coral-crowned plinth with the offering chest and two sea lanterns
    for x in (-1, 0, 1):
        bp.set(x, 2, 0, "dark_prismarine")
    bp.set(0, 3, 0, "sea_lantern")
    bp.set(0, 4, 0, "brain_coral_block")
    bp.set(0, 5, 0, "fire_coral[waterlogged=true]")
    bp.chest(0, 2, -1, "north", LOOT + "coral_shrine")
    bp.set(-1, 3, 0, "tube_coral_fan[waterlogged=true]")
    bp.set(1, 3, 0, "horn_coral_fan[waterlogged=true]")
    # coral reclaims it: coral blocks, fans and pickles on the columns, the dome and the platform
    for (cx, cz, h) in cols:
        for y in range(2, 2 + h):
            if rng.random() < 0.35:
                for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
                    if not bp.get(cx + dx, y, cz + dz) and rng.random() < 0.4:
                        bp.set(cx + dx, y, cz + dz, f"{rng.choice(CORALS)}_coral_wall_fan[facing={f},waterlogged=true]")
    tops = [(x, y, z) for (x, y, z), b in list(bp.blocks.items())
            if y >= 1 and (x, y + 1, z) not in bp.blocks and b[0] in (
                "minecraft:prismarine", "minecraft:prismarine_bricks", "minecraft:dark_prismarine",
                "minecraft:smooth_sandstone")]
    for (x, y, z) in tops:
        r = rng.random()
        if r < 0.18:
            bp.set(x, y + 1, z, f"{rng.choice(CORALS)}_coral[waterlogged=true]")
        elif r < 0.32:
            bp.set(x, y + 1, z, f"{rng.choice(CORALS)}_coral_fan[waterlogged=true]")
        elif r < 0.38:
            bp.set(x, y + 1, z, f"sea_pickle[pickles={rng.randint(1, 4)},waterlogged=true]")
        elif r < 0.44 and y <= 2:
            bp.set(x, y + 1, z, f"{W}glow_anemone[color={rng.randint(0, 2)},waterlogged=true]")
    for _ in range(14):
        x, z = rng.randint(-9, 9), rng.randint(-9, 9)
        if 7.5 < math.hypot(x, z) and bp.get(x, 0, z) and not bp.get(x, 1, z):
            k = rng.choice(CORALS)
            bp.set(x, 1, z, f"{k}_coral_block")
            bp.set(x, 2, z, f"{rng.choice(CORALS)}_coral_fan[waterlogged=true]")
    kelp_and_grass(bp, rng, 30, 9, 9, keep_out=lambda x, z: math.hypot(x, z) <= 7.5)
    skirt(bp, 434)


register(StructureDef(
    "coral_shrine", "overworld", ["minecraft:warm_ocean", "minecraft:lukewarm_ocean", "minecraft:deep_lukewarm_ocean"],
    [Piece("shrine", coral_shrine)], spacing=22, separation=7, heightmap="OCEAN_FLOOR_WG", adaptation="none",
    processors="none", title_fr="Sanctuaire de corail", title_en="Coral Shrine"))


# ============================================================ 4. shipwreck debris
def shipwreck_debris(bp):
    bp.underwater = True
    rng = random.Random(441)
    seabed(bp, 14, 10, 442)
    # the broken keel and the ribs of the hull sticking out of the sand
    for x in range(-9, 4):
        bp.set(x, 1, 0, "stripped_dark_oak_log[axis=x]")
    for x in range(-8, 4, 2):
        h = rng.randint(2, 4) if x > -6 else rng.randint(4, 6)
        for side in (-1, 1):
            bp.set(x, 1, side, "dark_oak_fence")               # the rib leaves the keel...
            for k in range(1, h + 1):
                bp.set(x, k, side * 2, "dark_oak_fence")       # ...and curves up
            if h >= 4:
                bp.set(x, h, side * 3, "dark_oak_fence")
    # a section of hull planking lying on its side
    for x in range(-12, -8):
        for y in range(1, 4 if x > -12 else 3):
            bp.set(x, y, 3, "spruce_planks" if (x + y) % 3 else "dark_oak_planks")
    # the fallen mast with its yard and torn sail draped on the sand
    for z in range(-9, 2):
        bp.set(6, 1, z, "stripped_spruce_log[axis=z]")
    for x in range(3, 10):
        bp.set(x, 1, -6, "spruce_fence")
    for x in range(3, 10):
        for z in range(-5, -2):
            if rng.random() < 0.7 and not bp.get(x, 1, z):
                bp.set(x, 1, z, "white_carpet" if rng.random() < 0.8 else "light_gray_carpet")
    # a cannon on its broken carriage, and cannonballs
    bp.set(-3, 1, -5, "spruce_slab[type=bottom]")
    bp.set(-2, 1, -5, "spruce_slab[type=bottom]")
    bp.set(-3, 2, -5, "polished_blackstone")
    bp.set(-2, 2, -5, "polished_blackstone_wall")
    bp.set(-1, 2, -5, "polished_blackstone_wall")
    bp.set(-1, 1, -5, "spruce_slab[type=bottom]")
    for (x, z) in ((-4, -7), (-3, -7), (0, -6)):
        bp.set(x, 1, z, "coal_block" if (x + z) % 2 else "polished_blackstone_button[face=floor,facing=north,powered=false]")
    # the anchor and its chain
    for y in range(1, 4):
        bp.set(10, y, 4, "iron_block" if y < 3 else "iron_bars")
    bp.set(9, 1, 4, "iron_block")
    bp.set(11, 1, 4, "iron_block")
    for x in range(4, 10):
        bp.set(x, 1, 5, "iron_chain[axis=x]")
    # spilled cargo: barrels and crates; the captain's chest half buried
    for (x, z) in ((-6, 6), (-5, 7), (2, 7), (-10, -4), (8, 0)):
        bp.set(x, 1, z, "barrel[facing=up,open=false]" if rng.random() < 0.6 else "spruce_planks")
    bp.barrel(-6, 1, 7, "north", LOOT + "shipwreck_debris")
    bp.set(-1, 0, 4, "chest[facing=north,type=single,waterlogged=true]", {"LootTable": LOOT + "shipwreck_debris"})
    bp.set(1, 1, 6, "decorated_pot[facing=south,cracked=true,waterlogged=true]")
    kelp_and_grass(bp, rng, 60, 14, 10)
    skirt(bp, 443)


register(StructureDef(
    "shipwreck_debris", "overworld", ["#minecraft:is_ocean", "#minecraft:is_beach"],
    [Piece("debris", shipwreck_debris)], spacing=18, separation=6, heightmap="OCEAN_FLOOR_WG", adaptation="none",
    processors="none", title_fr="Débris de naufrage", title_en="Shipwreck Debris"))
