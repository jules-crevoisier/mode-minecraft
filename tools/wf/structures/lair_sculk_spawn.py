"""Lair of the Sculk Spawn, under the Sealed Laboratory (called at the end of underground.sealed_lab).

The breached containment cell (north row, second from the west) has a torn-open service shaft in its floor.
The way down:

  B1 (floor y=-14)  collapsed service landing at the shaft's foot (crashed lift cage, a wraith spawner),
                    a service corridor south to the cold store: frozen specimen vats, a powder-snow trap,
                    a stray spawner and a supply barrel
  stairwell         a square maintenance stairwell spiralling down two full turns
  B2 (floor y=-30)  the decontamination antechamber: the site of grace (waystone, bench, lights), then a
                    hazard-striped bulkhead with the boss mist
  Containment Core  the arena: a 15-block-radius drum of reinforced deepslate with a low dome (17 blocks
                    clear at the centre), the ruptured catalyst column hanging from the dome over the
                    shattered tank base where the seal lies, broken glass tanks and sculk on the edges
  reward            east of the arena, behind sealed bars that fall with the boss: the catalyst vault
                    (reward chest) and a ladder shortcut up to the airlock (hidden trapdoor)
"""
import math
import random

from ..arch import Palette, slab, stair
from ..parts import LOOT, MOB, MOD

FY = -30          # arena / B2 floor
R = 15            # arena radius (clear floor)
DRUM = 11         # wall height above the floor before the dome springs
B1 = -14          # first basement floor

WALL = Palette({"deepslate_tiles": 5, "polished_deepslate": 3, "cracked_deepslate_tiles": 2}, seed=71, scale=1.6)
ROUGH = Palette({"cobbled_deepslate": 4, "deepslate": 3, "tuff": 1}, seed=72, scale=2.0)
CORE = Palette({"deepslate_tiles": 4, "polished_deepslate": 3, "cracked_deepslate_tiles": 1}, seed=73, scale=2.2)
METAL = "waxed_weathered_cut_copper"     # old lab metalwork, gone teal like the sculk
METAL_D = "waxed_oxidized_copper"
PANEL = Palette({"smooth_stone": 4, "polished_diorite": 1}, seed=74, scale=2)
AIR = "minecraft:air"
SLAB_TOP = "polished_deepslate_slab[type=top,waterlogged=false]"
CHAIN_Y = "iron_chain[axis=y,waterlogged=false]"


def _carve_room(bp, x0, y0, z0, x1, y1, z1, wall=WALL, floor=None, panel=False):
    """Room with walls/floor/ceiling (y0 = floor, y1 = ceiling) and a cleared inside."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, y0 - 1, z, "deepslate_tiles")
            bp.set(x, y1, z, wall.pick(x, y1, z))
            for y in range(y0, y1):
                if edge:
                    bp.set(x, y, z, wall.pick(x, y, z))
                elif y == y0:
                    bp.set(x, y, z, floor(x, z) if callable(floor) else (floor or ("polished_deepslate" if (x + z) % 2 else "deepslate_tiles")))
                else:
                    bp.set(x, y, z, "air")
    if panel:
        for x in range(x0 + 1, x1):
            for z in (z0, z1):
                for y in range(y0 + 2, y1 - 1):
                    bp.set(x, y, z, PANEL.pick(x, y, z) if (x - x0) % 4 else "polished_deepslate")
        for z in range(z0 + 1, z1):
            for x in (x0, x1):
                for y in range(y0 + 2, y1 - 1):
                    bp.set(x, y, z, PANEL.pick(x, y, z) if (z - z0) % 4 else "polished_deepslate")


def _open(bp, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                bp.set(x, y, z, "air")


def _hazard(bp, x, y, z, k):
    bp.set(x, y, z, "yellow_concrete" if k % 2 else "black_concrete")


# ============================================================ the shaft and B1
def shaft(bp, rng, vein):
    """The torn service shaft: from the breached cell's floor down to the B1 landing, a ladder on its
    north face, the floor around the hole buckled into hazard plates and sculk."""
    x0, x1, z0, z1 = -26, -24, -8, -6
    for y in range(B1 + 6, 1):
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                inner = x0 <= x <= x1 and z0 <= z <= z1
                if inner:
                    bp.set(x, y, z, "air")
                elif y < 0:
                    bp.set(x, y, z, ROUGH.pick(x, y, z) if (x + y + z) % 4 else METAL)
    # the ladder's support continues as a steel post through the landing
    for y in range(B1 + 1, B1 + 6):
        bp.set(-25, y, -9, METAL if y % 2 else "polished_deepslate")
    for y in range(B1 + 1, 1):
        bp.set(-25, y, -8, "ladder[facing=south,waterlogged=false]")
    # rim of the hole: bent hazard plates, a tilted grate, veins
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if not (x0 <= x <= x1 and z0 <= z <= z1) and bp.get(x, 0, z) not in (None, AIR):
                bp.set(x, 0, z, "yellow_concrete" if (x + z) % 2 else "black_concrete")
    bp.set(-27, 1, -5, "waxed_copper_grate")
    bp.set(-23, 1, -9, stair("cobbled_deepslate_stairs", "west"))
    bp.set(-27, 1, -7, vein(down=True))
    bp.set(-23, 1, -6, "iron_chain[axis=x,waterlogged=false]")


def landing(bp, rng, vein):
    """B1: the collapsed service landing at the foot of the shaft (x -31..-20, z -12..-2)."""
    x0, x1, z0, z1 = -31, -20, -12, -2
    _carve_room(bp, x0, B1, z0, x1, B1 + 6, z1, panel=True)
    # the shaft opens in the ceiling
    for x in range(-26, -23):
        for z in range(-8, -5):
            bp.set(x, B1 + 6, z, "air")
    # the crashed lift cage, slid away from the shaft: bent bars, its roof plate, its cable on the floor
    for (x, z) in ((-23, -7), (-20 - 1, -7), (-23, -4), (-21, -4)):
        bp.set(x, B1 + 1, z, "iron_block")
    for (x, z) in ((-22, -7), (-23, -6), (-23, -5), (-21, -5), (-22, -4)):
        if rng.random() < 0.75:
            bp.set(x, B1 + 1, z, "iron_bars")
            if rng.random() < 0.5:
                bp.set(x, B1 + 2, z, "iron_bars")
    bp.set(-22, B1 + 1, -6, "heavy_weighted_pressure_plate[power=0]")
    bp.set(-22, B1 + 2, -5, stair("polished_deepslate_stairs", "east", "top"))
    bp.set(-22, B1 + 1, -5, "iron_bars")
    for (x, z) in ((-24, -6), (-25, -6), (-24, -5), (-26, -5)):
        bp.set(x, B1 + 1, z, "iron_chain[axis=x,waterlogged=false]")
    # rubble that fell with it
    for (x, z) in ((-29, -10), (-28, -11), (-30, -9), (-22, -3), (-21, -4)):
        bp.set(x, B1 + 1, z, ROUGH.pick(x, B1 + 1, z))
    bp.set(-29, B1 + 2, -11, "cobbled_deepslate_slab[type=bottom,waterlogged=false]")
    bp.set(-30, B1 + 1, -11, "gravel")
    # pipes along the ceiling, copper lamps
    for x in range(x0 + 1, x1):
        bp.set(x, B1 + 5, -11, "waxed_copper_grate" if x % 3 else "waxed_cut_copper")
        bp.set(x, B1 + 5, -3, "waxed_copper_grate" if x % 3 else "waxed_cut_copper")
    for x in (-30, -21):
        bp.set(x, B1 + 4, -7, "waxed_copper_bulb[lit=true,powered=false]")
    bp.set(-22, B1 + 5, -7, "verdant_froglight[axis=y]")
    bp.set(-29, B1 + 5, -5, "verdant_froglight[axis=y]")
    # a guard's last stand: a toppled desk and a lantern
    bp.set(-21, B1 + 1, -11, SLAB_TOP)
    bp.set(-21, B1 + 2, -11, "lantern[hanging=false,waterlogged=false]")
    bp.set(-22, B1 + 1, -11, stair("dark_oak_stairs", "south"))
    bp.spawner(-30, B1 + 1, -3, MOB["map_wraith"])
    # sculk that rained down the shaft, cobwebs, abandoned crates
    from .underground import spread_sculk
    spread_sculk(bp, -25, -7, 6, 77, y_floor=B1, region=(x0 + 1, z0 + 1, x1 - 1, z1 - 1))
    for (x, z) in ((-30, -11), (-30, -10), (-29, -11)):
        bp.set(x, B1 + 1, z, "barrel[facing=up,open=false]")
    bp.set(-30, B1 + 2, -11, "barrel[facing=north,open=false]")
    bp.set(-21, B1 + 5, -3, "cobweb")
    bp.set(-30, B1 + 5, -6, "cobweb")
    # way south to the cold store
    _open(bp, -27, B1 + 1, z1, -25, B1 + 3, z1)
    for z in range(z1 + 1, 8):
        for x in range(-28, -23):
            bp.set(x, B1 - 1, z, "deepslate_tiles")
            bp.set(x, B1 + 4, z, WALL.pick(x, B1 + 4, z))
            for y in range(B1, B1 + 4):
                if x in (-28, -24):
                    bp.set(x, y, z, WALL.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air" if y > B1 else ("waxed_copper_grate" if x == -26 else "polished_deepslate"))
        if z % 3 == 0:
            bp.set(-26, B1 + 4, z, "ochre_froglight[axis=y]")


def cold_store(bp, rng, vein):
    """B1: the cold store (x -34..-20, z 8..20): two rows of frozen specimen vats on a snowy floor."""
    x0, x1, z0, z1 = -34, -20, 8, 20
    _carve_room(bp, x0, B1, z0, x1, B1 + 7, z1,
                floor=lambda x, z: "packed_ice" if (x + z) % 3 == 0 else ("polished_deepslate" if (x + z) % 2 else "deepslate_tiles"),
                panel=True)
    _open(bp, -27, B1 + 1, z0, -25, B1 + 3, z0)
    # vats: iron base and cap, glass shell, a frozen specimen in each; two are smashed
    vats = [(x, z) for x in (-31, -28, -24) for z in (11, 17)]
    for i, (vx, vz) in enumerate(vats):
        broken = i in (2, 3)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(vx + dx, B1 + 1, vz + dz, METAL if (dx and dz) else "polished_deepslate")
                bp.set(vx + dx, B1 + 5, vz + dz, METAL if (dx and dz) else SLAB_TOP)
                for y in range(B1 + 2, B1 + 5):
                    if dx == 0 and dz == 0:
                        bp.set(vx, y, vz, ["packed_ice", "blue_ice", "bone_block[axis=y]"][(i + y) % 3])
                    elif broken and rng.random() < 0.6:
                        bp.set(vx + dx, y, vz + dz, "air")
                    else:
                        bp.set(vx + dx, y, vz + dz, METAL_D if (dx and dz) else "light_blue_stained_glass")
        if broken:
            bp.set(vx, B1 + 4, vz, "skeleton_skull[rotation=4]")
            bp.set(vx + 2, B1 + 1, vz, "snow[layers=2]")
        bp.set(vx, B1 + 6, vz, "sea_lantern")
    # snow drifts, a powder-snow trap in front of the stairwell door, frost on the walls
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if bp.get(x, B1 + 1, z) == AIR and rng.random() < 0.07:
                bp.set(x, B1 + 1, z, f"snow[layers={rng.choice((1, 1, 2, 3))}]")
    for x in range(-29, -26):
        bp.set(x, B1, 19, "powder_snow")
    bp.spawner(-21, B1 + 1, 14, "minecraft:stray")
    bp.barrel(-33, B1 + 1, 19, "east", LOOT + "sealed_lab")
    bp.set(-33, B1 + 1, 18, "barrel[facing=up,open=false]")
    bp.set(-33, B1 + 2, 19, "candle[candles=2,lit=false,waterlogged=false]")
    for z in (10, 18):
        bp.set(-21, B1 + 4, z, "soul_lantern[hanging=false,waterlogged=false]")
        bp.set(-20, B1 + 4, z, "polished_deepslate")
    # door to the stairwell (south wall), framed in hazard stripes; the opening is cut in build()
    for k, (x, y) in enumerate([(-28, B1 + 1), (-28, B1 + 2), (-28, B1 + 3), (-28, B1 + 4), (-27, B1 + 4),
                                (-26, B1 + 4), (-26, B1 + 3), (-26, B1 + 2), (-26, B1 + 1)]):
        _hazard(bp, x, y, z1, k)
    for z in (21, 22):
        for x in (-28, -26):
            for y in range(B1, B1 + 4):
                bp.set(x, y, z, WALL.pick(x, y, z))
        bp.set(-27, B1, z, "polished_deepslate")
        bp.set(-27, B1 + 4, z, WALL.pick(-27, B1 + 4, z))
        bp.set(-27, B1 - 1, z, "deepslate_tiles")


def stairwell(bp, rng):
    """A square maintenance stairwell (centre -27, 26) spiralling two full turns from B1 down to B2."""
    cx, cz, r = -27, 26, 2
    top, bot = B1, FY + 1
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            for y in range(FY - 1, B1 + 7):
                edge = max(abs(x - cx), abs(z - cz)) == 3
                bp.set(x, y, z, WALL.pick(x, y, z) if edge or y in (FY - 1, FY, B1 + 6) else "air")
    for y in range(FY, B1 + 6):     # a 3x3 core: no well to fall into
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(cx + dx, y, cz + dz, METAL if (y % 6 == 0 and dx and dz) else "polished_deepslate")
        if y % 6 == 3:
            for (dx, dz) in ((3, 0), (-3, 0), (0, 3)):
                bp.set(cx + dx, y, cz + dz, "verdant_froglight[axis=y]")
            bp.set(cx + 1, y, cz, "sea_lantern")
    # ring of 16 cells, ordered so that the first and last steps sit on the north side
    ring = [(x, z) for x in range(cx - r, cx + r + 1) for z in range(cz - r, cz + r + 1)
            if max(abs(x - cx), abs(z - cz)) == r]
    ring.sort(key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    start = ring.index((cx, cz - r))
    ring = ring[start:] + ring[:start]
    # two half-steps per level, built from the bottom: the top step (B1, top slab) lands on ring[0]
    # (north middle, under the door from the cold store), the bottom one on ring[15] (its west neighbour)
    n = (top - bot + 1) * 2
    for i in range(n):
        y = bot + i // 2
        x, z = ring[(n - 1 - i) % len(ring)]
        bp.set(x, y, z, slab("polished_deepslate_slab", "bottom" if i % 2 == 0 else "top"))


def antechamber(bp, rng):
    """B2: the decontamination antechamber (x -32..-19, z -5..5) and the site of grace."""
    x0, x1, z0, z1 = -32, -19, -5, 5
    _carve_room(bp, x0, FY, z0, x1, FY + 6, z1, panel=True)
    # floor: a grated walkway to the bulkhead
    for x in range(x0 + 1, x1):
        bp.set(x, FY, 0, "waxed_copper_grate" if x % 2 else "polished_deepslate")
    # site of grace: the waystone on a deepslate plinth, benches, candles and lanterns
    gx, gz = -27, -2
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(gx + dx, FY, gz + dz, "chiseled_deepslate" if dx == dz == 0 else "polished_deepslate")
    bp.set(gx, FY + 1, gz, MOD["waystone"])
    for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bp.set(gx + dx, FY + 1, gz + dz, f"candle[candles={1 + (dx + dz + 2) % 3},lit=true,waterlogged=false]")
    for x in (-30, -29):
        bp.set(x, FY + 1, -4, stair("dark_oak_stairs", "south"))
    bp.set(-31, FY + 1, -4, "dark_oak_slab[type=bottom,waterlogged=false]")
    bp.set(-28, FY + 1, -4, "potted_dead_bush")
    bp.set(-31, FY + 1, 4, "barrel[facing=up,open=false]")
    bp.set(-31, FY + 2, 4, "lantern[hanging=false,waterlogged=false]")
    for x in (-29, -23):
        bp.chain(x, FY + 4, 0, FY + 5)
        bp.lantern(x, FY + 3, 0, hanging=True)
    bp.set(-26, FY + 5, -2, "verdant_froglight[axis=y]")
    # decontamination nozzles over the walkway, a dead scientist's notes
    for x in range(-25, -20, 2):
        bp.set(x, FY + 5, 0, "lightning_rod[facing=down,powered=false,waterlogged=false]")
    bp.set(-21, FY + 1, 4, "lectern[facing=north,has_book=false,powered=false]")
    bp.set(-20, FY + 1, 4, "skeleton_skull[rotation=10]")
    bp.set(-22, FY + 1, -4, "cauldron")
    # the bulkhead into the core: hazard frame on the antechamber side, passage through the drum
    for k, (z, y) in enumerate([(-2, FY + 1), (-2, FY + 2), (-2, FY + 3), (-2, FY + 4), (-2, FY + 5), (-1, FY + 5),
                                (0, FY + 5), (1, FY + 5), (2, FY + 5), (2, FY + 4), (2, FY + 3), (2, FY + 2), (2, FY + 1)]):
        _hazard(bp, x1, y, z, k)
    _open(bp, x1, FY + 1, -1, -15, FY + 4, 1)
    for x in range(x1, -14):
        bp.set(x, FY, 0, "waxed_copper_grate")
        for z in (-1, 1):
            bp.set(x, FY, z, "polished_deepslate")
        bp.set(x, FY + 5, 0, METAL)
    # from the stairwell (south)
    _open(bp, -28, FY + 1, z1, -26, FY + 3, z1)


def b2_corridor(bp, rng, vein):
    """B2: the corridor from the stairwell's foot (z 23) north to the antechamber (z 5)."""
    for z in range(6, 23):
        for x in range(-29, -24):
            bp.set(x, FY - 1, z, "deepslate_tiles")
            bp.set(x, FY + 4, z, WALL.pick(x, FY + 4, z))
            for y in range(FY, FY + 4):
                if x in (-29, -25):
                    bp.set(x, y, z, WALL.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air" if y > FY else ("reinforced_deepslate" if x == -27 and z % 4 == 0 else "polished_deepslate"))
        if z % 4 == 2:
            bp.set(-27, FY + 4, z, "sea_lantern")
    for z in range(12, 18):     # sculk seeping in from the core
        if rng.random() < 0.6:
            bp.set(rng.choice((-28, -26)), FY, z, "sculk")
    bp.set(-26, FY + 1, 15, vein(down=True))


# ============================================================ the Containment Core
def dome_in(rho):
    """Height of the inner dome surface above the springing line."""
    return math.sqrt(max(0.0, R * R - rho * rho)) * 6.0 / R


def core(bp, rng, vein, spread_sculk):
    top = FY + DRUM            # springing line of the dome
    # ---- drum, floor and dome shell
    for x in range(-R - 3, R + 4):
        for z in range(-R - 3, R + 4):
            d = math.hypot(x, z)
            if d > R + 2.6:
                continue
            ang = math.degrees(math.atan2(z, x)) % 360
            bp.set(x, FY - 1, z, "deepslate_tiles")
            bp.set(x, FY - 2, z, "reinforced_deepslate" if d > R else "deepslate_tiles")
            if d <= R + 0.5:
                if d < 1.0:
                    b = "reinforced_deepslate"
                elif d < 3.6:
                    b = "reinforced_deepslate" if (int(d * 3) + int(ang / 30)) % 3 else "sculk"
                elif 5.5 <= d < 6.5:
                    b = "yellow_concrete" if int(ang / 15) % 2 else "black_concrete"
                elif 9.5 <= d < 10.5:
                    b = "waxed_copper_grate" if int(ang / 10) % 3 else "verdant_froglight[axis=y]"
                elif d > R - 0.8:
                    b = "reinforced_deepslate"
                elif min(ang % 22.5, 22.5 - ang % 22.5) * d < 9:
                    b = "deepslate_tiles"
                elif int(d) % 3 == 0:
                    b = "polished_deepslate"
                else:
                    b = "deepslate_tiles" if (x + z) % 2 else "polished_deepslate"
                bp.set(x, FY, z, b)
                for y in range(FY + 1, top + int(dome_in(d)) + 1):
                    bp.set(x, y, z, "air")
            else:
                bp.set(x, FY, z, "reinforced_deepslate")
                for y in range(FY + 1, top + 1):
                    outer = d > R + 1.6
                    if outer:
                        bp.set(x, y, z, CORE.pick(x, y, z))
                    elif y in (FY + 4, FY + 5) or y == top - 1:
                        bp.set(x, y, z, "light_blue_stained_glass")      # glowing containment strips
                    elif y == FY + 1:
                        bp.set(x, y, z, "reinforced_deepslate")
                    else:
                        bp.set(x, y, z, WALL.pick(x, y, z))
                if d > R + 1.6:
                    for y in (FY + 4, FY + 5, top - 1):
                        bp.set(x, y, z, "sea_lantern")
    # dome shell (2 thick) with ribs
    for x in range(-R - 3, R + 4):
        for z in range(-R - 3, R + 4):
            rho = math.hypot(x, z)
            if rho > R + 2.6:
                continue
            hin = dome_in(rho) if rho <= R else -1
            hout = math.sqrt(max(0.0, (R + 2.5) ** 2 - rho * rho)) * 8.5 / (R + 2.5)
            ang = math.degrees(math.atan2(z, x)) % 360
            rib = min(ang % 30, 30 - ang % 30) * max(rho, 1) < 22
            for y in range(top + 1, top + int(hout) + 2):
                if hin >= 0 and y - top <= hin:
                    continue
                bp.set(x, y, z, "reinforced_deepslate" if rib else CORE.pick(x, y, z))
    # ---- twelve pilasters with froglight caps, clamps and hanging chains
    for k in range(12):
        a = math.radians(k * 30 + 15)
        px, pz = round(math.cos(a) * (R - 0.2)), round(math.sin(a) * (R - 0.2))
        if abs(pz) <= 2 and abs(px) > 10:
            continue                       # leave the two bulkheads (east, west) clear
        for y in range(FY + 1, top + 1):
            bp.set(px, y, pz, METAL if y in (FY + 1, FY + 6) else "reinforced_deepslate")
        bp.set(px, top, pz, "verdant_froglight[axis=y]")
        cx, cz = round(math.cos(a) * (R - 1.4)), round(math.sin(a) * (R - 1.4))
        bp.chain(cx, top - 3, cz, top + int(dome_in(math.hypot(cx, cz))))
        bp.lantern(cx, top - 4, cz, hanging=True, soul=True)
    # ---- bulkhead frames (east and west) on the arena side
    for sx in (-1, 1):
        x = sx * R
        for y in range(FY + 1, FY + 6):
            for z in (-2, 2):
                bp.set(x, y, z, METAL)
        for z in range(-2, 3):
            bp.set(x, FY + 5, z, "yellow_concrete" if z % 2 else "black_concrete")
        _open(bp, x, FY + 1, -1, x + sx * 3, FY + 4, 1)
    # ---- the ruptured catalyst column: its upper half hangs from the dome, shattered at the bottom
    apex = top + int(dome_in(0))
    for y in range(apex - 7, apex + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                corner = dx and dz
                if y < apex - 5 and not corner and (dx or dz) and rng.random() < 0.5:
                    continue                       # torn glass at the bottom
                if dx == 0 and dz == 0:
                    b = "sculk_catalyst[bloom=true]" if y == apex - 4 else "sculk"
                else:
                    b = METAL_D if corner or y in (apex - 2, apex) else "tinted_glass"
                bp.set(dx, y, dz, b)
    for (dx, dz) in ((-1, -1), (1, 1)):          # jagged corner posts torn longer
        bp.set(dx, apex - 8, dz, "iron_bars")
        bp.set(dx, apex - 9, dz, "iron_bars")
    bp.set(0, apex - 8, 0, "pearlescent_froglight[axis=y]")
    bp.set(0, apex - 9, 0, vein(up=True))
    for (dx, dz) in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        bp.chain(dx, apex - 4, dz, apex - 1)
        bp.set(dx, apex - 5, dz, METAL)
    # the shattered tank base around the seal: corner posts, broken glass, blooming catalysts
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bp.set(dx, FY + 1, dz, METAL_D)
        bp.set(dx, FY + 2, dz, "iron_bars" if (dx + dz) % 4 else "air")
    for (dx, dz) in ((-1, -2), (2, -1), (1, 2), (-2, 1)):
        bp.set(dx, FY + 1, dz, "tinted_glass")
    for (dx, dz) in ((3, 2), (-3, -2), (2, -3), (-2, 3)):
        bp.set(dx, FY + 1, dz, "sculk_catalyst[bloom=true]")
    for (dx, dz) in ((1, -2), (-2, -1), (2, 1), (-1, 2), (0, 3), (3, 0)):
        bp.set(dx, FY + 1, dz, vein(down=True))
    # ---- broken glass tanks around the edge
    for k, deg in enumerate((30, 90, 150, 210, 270, 330)):
        a = math.radians(deg)
        tx, tz = round(math.cos(a) * 12.2), round(math.sin(a) * 12.2)
        tank(bp, tx, tz, k, rng, vein)
    # ---- sculk creeping in from the edges and around the catalyst
    for i, (sx, sz, rr) in enumerate(((-11, -9, 6), (12, 9, 6), (4, -14, 5), (-7, 13, 6), (0, 0, 5), (14, -4, 4))):
        spread_sculk(bp, sx, sz, rr, 90 + i, y_floor=FY,
                     region=(-R, -R, R, R))
    for (x, z) in ((-12, -8), (11, 10), (-8, 12)):
        bp.set(x, FY + 1, z, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
    bp.set(13, FY + 1, -6, "sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]")
    bp.set(-13, FY + 1, 5, "sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]")
    # the seal, last, so the sculk does not cover it
    bp.boss_seal(0, FY, 0, "brasshaven:sculk_spawn", R)


def tank(bp, cx, cz, k, rng, vein):
    """A broken specimen tank: iron base and cap, a glass shell blown open toward the centre."""
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            corner = dx and dz
            bp.set(cx + dx, FY + 1, cz + dz, METAL_D if corner else "polished_deepslate")
            for y in range(FY + 2, FY + 6):
                if dx == 0 and dz == 0:
                    continue
                facing_in = (dx * cx + dz * cz) < 0
                if corner:
                    bp.set(cx + dx, y, cz + dz, METAL_D if y in (FY + 2, FY + 5) else "iron_bars")
                elif facing_in and y < FY + 5 - (k % 2):
                    bp.set(cx + dx, y, cz + dz, "air")
                else:
                    bp.set(cx + dx, y, cz + dz, "glass" if rng.random() < 0.8 else "air")
            if k % 3 != 1:
                bp.set(cx + dx, FY + 6, cz + dz, METAL_D if corner else SLAB_TOP)
    inside = ("sculk", "sculk", "bone_block[axis=y]")[k % 3]
    bp.set(cx, FY + 2, cz, inside)
    bp.set(cx, FY + 3, cz, vein(down=True) if inside == "sculk" else "skeleton_skull[rotation=0]")
    if k % 3 == 1:   # the fallen cap lies next to the tank
        bp.set(cx - (1 if cx > 0 else -1) * 2, FY + 1, cz, SLAB_TOP)


# ============================================================ reward: the catalyst vault and the shortcut
def vault(bp, rng):
    x0, x1, z0, z1 = 20, 30, -5, 5
    _carve_room(bp, x0, FY, z0, x1, FY + 6, z1, panel=True)
    # passage from the core's east bulkhead, blocked by sealed bars until the boss falls
    for x in range(R + 1, x0 + 1):
        for z in (-2, 2):
            for y in range(FY, FY + 6):
                bp.set(x, y, z, WALL.pick(x, y, z))
        for z in (-1, 0, 1):
            bp.set(x, FY, z, "waxed_copper_grate" if z == 0 else "polished_deepslate")
            bp.set(x, FY + 5, z, METAL)
            for y in range(FY + 1, FY + 5):
                bp.set(x, y, z, "air")
    for z in (-1, 0, 1):
        for y in range(FY + 1, FY + 5):
            bp.set(19, y, z, MOD["vault_bars"])
    # the vault: a plinth with the reward chest, specimen shelves, the director's research
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(27 + dx, FY + 1, dz, "polished_deepslate" if dx or dz else "reinforced_deepslate")
    bp.chest(27, FY + 2, 0, "west", LOOT + "sealed_lab")
    bp.set(27, FY + 5, 0, "pearlescent_froglight[axis=y]")
    for x in range(21, 26):
        for z, f in ((-4, "south"), (4, "north")):
            bp.set(x, FY + 1, z, "polished_deepslate")
            bp.set(x, FY + 2, z, ["amethyst_cluster[facing=up,waterlogged=false]", "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]",
                                  "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]", "light_blue_stained_glass",
                                  "sculk_catalyst[bloom=false]"][(x + z) % 5])
    bp.barrel(29, FY + 1, -4, "up", LOOT + "sealed_lab")
    bp.set(29, FY + 1, 4, "lectern[facing=west,has_book=false,powered=false]")
    for x in (22, 25):
        bp.set(x, FY + 5, 0, "verdant_froglight[axis=y]")
    # shortcut: a ladder in a service duct up to a hidden trapdoor in the airlock floor (27, 0, 2)
    for y in range(FY + 1, 0):
        bp.set(27, y, 3, METAL if y % 5 == 0 else "polished_deepslate")   # the duct the ladder hangs on
        if y >= FY + 6:
            for (x, z) in ((26, 2), (28, 2), (27, 1)):
                bp.set(x, y, z, "polished_deepslate")
        bp.set(27, y, 2, "ladder[facing=north,waterlogged=false]")
    bp.set(27, 0, 2, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")


def build(bp):
    """Dig the lair under the lab. Called last by underground.sealed_lab."""
    from .underground import spread_sculk, vein
    rng = random.Random(311)
    landing(bp, rng, vein)
    shaft(bp, rng, vein)
    cold_store(bp, rng, vein)
    stairwell(bp, rng)
    b2_corridor(bp, rng, vein)
    antechamber(bp, rng)
    core(bp, rng, vein, spread_sculk)
    vault(bp, rng)
    # doorways cut through the stairwell: at the top from the cold store, at the bottom to the B2 corridor
    _open(bp, -27, B1 + 1, 20, -27, B1 + 3, 23)
    _open(bp, -28, FY + 1, 23, -28, FY + 3, 23)
    # boss mist across both bulkheads (after carving: it only fills open cells)
    bp.mist(-R - 2, FY + 1, -1, -R - 2, FY + 4, 1)
    bp.mist(R + 2, FY + 1, -1, R + 2, FY + 4, 1)
