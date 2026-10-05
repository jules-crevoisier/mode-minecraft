"""Lair of the Gryphon Knight: the sky plaza in front of the temple of the Sky Island.

The south lawn becomes a great circular plaza (clear floor radius 14) jutting out over the void on a new
mass of rock fused to the island: a floor of quartz and calcite rings with a gold and lapis rosette, the
boss seal at its heart, a balustrade and a ring of broken columns at the edge (the gryphon soars over
them), and to the south an apse on a crag holding the nest of gold and feathers (the reward chest, the
gryphon's eggs). Two gates, both misted: the propylon at the foot of the portico steps, and the west gate
beside the arrival of the spiral stair (a bench and lanterns there; the rotunda waystone across the west
bridge is the site of grace).

Called at the end of ``overworld_b.sky_island`` with the island's surface height and top map.
"""
import math
import random

from .. import arch
from ..arch import Palette, slab, stair
from ..parts import LOOT

AX, AZ = -2, 28          # plaza centre (the seal)
R_FLOOR = 14             # clear floor radius
R_EDGE = 16              # balustrade / column ring
NX, NZ, NR = -2, 47, 6   # the nest apse (south)
HELIX = (-9, 11)         # the island's spiral stair (keep its headroom)
SPIKES = ((-6, 34, 3.5, 12), (5, 40, 3.0, 9), (-2, 26, 4.0, 8), (-12, 42, 2.5, 7))


def _r(x, z):
    return math.hypot(x - AX, z - AZ)


def _in_shape(x, z, pad=0.0):
    return _r(x, z) <= R_EDGE + 0.5 + pad or math.hypot(x - NX, z - NZ) <= NR + 0.5 + pad


def _ang(x, z):
    return math.degrees(math.atan2(z - AZ, x - AX)) % 360


def build(bp, Y, main):
    rng = random.Random(77)
    floor_pal = Palette({"calcite": 4, "smooth_quartz": 3, "polished_diorite": 2}, seed=71, scale=2.5)
    worn = Palette({"calcite": 4, "cobblestone": 1, "mossy_cobblestone": 2, "polished_diorite": 2,
                    "moss_block": 1}, seed=72, scale=2.0)
    rock = Palette({"stone": 5, "andesite": 2, "tuff": 2, "calcite": 1, "cobblestone": 1}, seed=73, scale=3.0)
    TRIM = "quartz_pillar[axis=y]"

    water = {(x, z) for (x, y, z), b in bp.blocks.items() if b[0] == "minecraft:water"}
    cells = [(x, z) for x in range(AX - 22, AX + 23) for z in range(AZ - 22, NZ + NR + 3) if _in_shape(x, z)]

    # ---------------------------------------------------------------- clear the lawn (never the portico steps)
    for x in range(AX - 20, AX + 21):
        for z in range(AZ - 17, NZ + NR + 3):
            if z >= 12 and _in_shape(x, z, pad=1.0):
                for y in range(Y + 1, Y + 26):
                    if bp.get(x, y, z) is not None:
                        bp.remove(x, y, z)
    # the lone birch that stood on the lawn edge
    for (x, y, z), b in list(bp.blocks.items()):
        if -13 <= x <= -3 and 7 <= z <= 17 and y > Y and b[0] in ("minecraft:birch_log", "minecraft:birch_leaves"):
            bp.remove(x, y, z)

    # ---------------------------------------------------------------- the rock mass under the plaza
    cx, cz = AX, (AZ + NZ) // 2
    for (x, z) in cells:
        if (x, z) in water or any((x + dx, z + dz) in water for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            continue
        q = min(1.0, math.hypot((x - cx) / 20.0, (z - cz) / 26.0))
        depth = 2 + 30 * (1 - q) ** 2.1 + 1.5 * math.sin(x * 0.7) * math.cos(z * 0.6)
        for sx_, sz_, sr, sd in SPIKES:                  # hanging rock spikes like the island's own
            dd = math.hypot(x - sx_, z - sz_)
            if dd < sr:
                depth += sd * (1 - dd / sr)
        if math.hypot(x - HELIX[0], z - HELIX[1]) <= 8.5:
            depth = 1                                    # the spiral stair passes under the lip
        for y in range(Y - 1, Y - int(depth) - 1, -1):
            if bp.get(x, y, z) is None:
                inner = _in_shape(x, z, pad=-2.5)
                bp.set(x, y, z, "dirt" if (y >= Y - 2 and inner) else rock.pick(x, y, z))
    # dress the new underside: roots, vines, lichen, a few hanging spikes
    for (x, z) in cells:
        if (x, z) in main:
            continue
        y = Y - 1
        while bp.get(x, y - 1, z) is not None and y > Y - 40:
            y -= 1
        r = rng.random()
        if bp.get(x, y - 1, z) is not None:
            continue
        if r < 0.08:
            bp.set(x, y, z, "rooted_dirt")
            bp.set(x, y - 1, z, "hanging_roots[waterlogged=false]")
        elif r < 0.14:
            bp.set(x, y, z, "moss_block")
            for k in range(1, rng.randint(2, 6)):
                bp.set(x, y - k, z, "vine[north=true]")
        elif r < 0.2:
            bp.set(x, y - 1, z, "glow_lichen[down=false,east=false,north=false,south=false,up=true,"
                                "waterlogged=false,west=false]")
        elif r < 0.215:
            for k in range(1, rng.randint(3, 6)):
                bp.set(x, y - k, z, rock.pick(x, y - k, z))

    # ---------------------------------------------------------------- the floor: rings, rosette and rays
    for (x, z) in cells:
        r = _r(x, z)
        a = _ang(x, z)
        in_apse = r > R_EDGE + 0.5
        if in_apse:
            b = worn.pick(x, Y, z) if rng.random() < 0.8 else "grass_block[snowy=false]"
        elif r < 1.5:
            b = "chiseled_quartz_block"
        elif r < 2.6:
            b = "gold_block"
        elif r < 6.0:
            b = "smooth_quartz" if int(a // 22.5) % 2 else "calcite"
        elif r < 7.0:
            b = "brasshaven:rune_lamp" if int((a + 11.25) // 22.5) % 4 == 0 and abs((a + 11.25) % 22.5 - 11.25) < 3 \
                else "lapis_block"
        elif r < 7.8:
            b = "chiseled_quartz_block"
        elif r < 12.0:
            ray = abs(((a + 11.25) % 45) - 22.5) < 2.2 * 8 / max(r, 1)
            b = "quartz_bricks" if ray else floor_pal.pick(x, Y, z)
        elif r < 14.0:
            b = worn.pick(x, Y, z)
        elif r < 15.0:
            b = "chiseled_quartz_block" if int(a // 10) % 3 else "quartz_bricks"
        else:
            b = "polished_diorite"
        bp.set(x, Y, z, b)
        if bp.get(x, Y - 1, z) in (None, "minecraft:dirt", "minecraft:grass_block", "minecraft:coarse_dirt"):
            bp.set(x, Y - 1, z, "stone")
    # moss and grass creeping through the worn outer ring
    for (x, z) in cells:
        if 12.0 <= _r(x, z) < 14.6 and rng.random() < 0.12 and bp.get(x, Y + 1, z) is None:
            bp.set(x, Y + 1, z, rng.choice(["moss_carpet", "short_grass", "moss_carpet"]))

    # ---------------------------------------------------------------- the balustrade around the whole shape
    edge = set()
    for (x, z) in cells:
        if _r(x, z) > R_EDGE - 0.6 or math.hypot(x - NX, z - NZ) > NR - 0.6:
            if any(not _in_shape(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                if _r(x, z) >= R_FLOOR + 0.8 or _r(x, z) > R_EDGE - 0.6:
                    edge.add((x, z))
    north_gate = {(x, z) for (x, z) in edge if abs(x - AX) <= 2 and z < AZ}
    west_dir = math.degrees(math.atan2(13 - AZ, -13.5 - AX)) % 360
    west_gate = {(x, z) for (x, z) in edge if min(abs(_ang(x, z) - west_dir), 360 - abs(_ang(x, z) - west_dir)) < 10.0}
    for (x, z) in edge:
        if (x, z) in north_gate or (x, z) in west_gate:
            continue
        if int(_ang(x, z) // 7.5) % 3 == 0:              # posts between runs of balustrade
            bp.set(x, Y + 1, z, "chiseled_quartz_block")
            bp.set(x, Y + 2, z, slab("smooth_quartz_slab"))
        else:
            bp.set(x, Y + 1, z, "diorite_wall")

    # ---------------------------------------------------------------- the ring of columns (12, many broken)
    heights = [12, 4, 9, 3, 11, 6, 12, 5, 8, 3, 10, 7]
    for i in range(12):
        a = math.radians(i * 30 + 15)
        x, z = AX + round(math.cos(a) * (R_EDGE - 0.5)), AZ + round(math.sin(a) * (R_EDGE - 0.5))
        if (x, z) in north_gate or (x, z) in west_gate or z < 13:
            continue
        h = heights[i]
        bp.set(x, Y + 1, z, "chiseled_quartz_block")
        for y in range(Y + 2, Y + 1 + h):
            bp.set(x, y, z, TRIM)
        if h >= 10:                                       # intact: capital and a lantern
            bp.set(x, Y + 1 + h, z, "chiseled_quartz_block")
            for dx, dz, f in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
                bp.set(x + dx, Y + 1 + h, z + dz, stair("smooth_quartz_stairs", f, "top"))
            bp.lantern(x, Y + 2 + h, z)
        else:                                             # broken: jagged top, the drum lying outside
            bp.set(x, Y + 1 + h, z, slab("smooth_quartz_slab"))
            ox, oz = math.cos(a), math.sin(a)
            for k in range(2, 2 + max(2, 8 - h)):
                px, pz = round(x + ox * k), round(z + oz * k)
                if _in_shape(px, pz) and _r(px, pz) > R_FLOOR + 0.5 and bp.get(px, Y + 1, pz) is None:
                    bp.set(px, Y + 1, pz, "quartz_pillar[axis=x]" if abs(ox) > abs(oz) else "quartz_pillar[axis=z]")
        if i % 3 == 1:
            bp.set(x, Y + 3, z + (1 if z > AZ else -1), "light_blue_wall_banner[facing=%s]" % ("south" if z > AZ else "north"))

    # ---------------------------------------------------------------- the propylon at the foot of the portico
    for gx in (AX - 3, AX + 3):
        bp.set(gx, Y + 1, 12, "chiseled_quartz_block")
        for y in range(Y + 2, Y + 8):
            bp.set(gx, y, 12, TRIM)
        bp.set(gx, Y + 8, 12, "chiseled_quartz_block")
        bp.set(gx, Y + 9, 12, "gold_block")
        bp.lantern(gx, Y + 10, 12)
    for x in range(AX - 3, AX + 4):
        bp.set(x, Y + 7, 12, "smooth_quartz")
        bp.set(x, Y + 7, 13, stair("smooth_quartz_stairs", "north", "top"))
        bp.set(x, Y + 7, 11, stair("smooth_quartz_stairs", "south", "top"))
    bp.set(AX, Y + 8, 12, "chiseled_quartz_block")
    bp.set(AX, Y + 6, 13, "light_blue_wall_banner[facing=south]")
    for x in range(AX - 2, AX + 3):
        bp.set(x, Y, 12, "polished_diorite")

    # ---------------------------------------------------------------- the west gate by the spiral stair
    wg = sorted(west_gate)
    for (x, z) in (wg[0], wg[-1]):
        bp.set(x, Y + 1, z, "chiseled_quartz_block")
        for y in range(Y + 2, Y + 6):
            bp.set(x, y, z, TRIM)
        bp.set(x, Y + 6, z, "chiseled_quartz_block")
        bp.lantern(x, Y + 7, z)
    gate_cells = [c for c in wg if c not in (wg[0], wg[-1])]
    for (x, z) in gate_cells:
        bp.set(x, Y, z, "polished_diorite")
        bp.set(x, Y + 5, z, "smooth_quartz_slab[type=top,waterlogged=false]")
    # the landing outside: a bench, lanterns and a paved way to the west bridge (rotunda waystone)
    path = Palette({"calcite": 3, "polished_diorite": 2, "gravel": 1}, seed=74)
    for t in range(0, 26):
        px = round(-12.5 - t * 0.38)
        pz = round(14 - t * 0.38)
        for dx in (-1, 0, 1):
            x, z = px + dx, pz
            if (x, z) in main and not _in_shape(x, z) and bp.get(x, Y + 1, z) in (None, "minecraft:short_grass") \
                    and bp.get(x, Y, z) not in (None, "minecraft:air") and "stairs" not in (bp.get(x, Y, z) or ""):
                bp.set(x, Y, z, path.pick(x, Y, z))
                bp.remove(x, Y + 1, z)
    bench_x, bench_z = -16, 15
    if bp.get(bench_x, Y, bench_z):
        bp.set(bench_x, Y + 1, bench_z, stair("smooth_quartz_stairs", "north"))
        bp.set(bench_x + 1, Y + 1, bench_z, stair("smooth_quartz_stairs", "north"))
    for (x, z) in ((-17, 12), (-14, 16)):
        if bp.get(x, Y, z):
            bp.set(x, Y + 1, z, "birch_fence")
            bp.set(x, Y + 2, z, "birch_fence")
            bp.lantern(x, Y + 3, z)

    # ---------------------------------------------------------------- the apse: crag and the nest
    for x in range(NX - NR, NX + NR + 1):
        for z in range(NZ - NR, NZ + NR + 1):
            d = math.hypot(x - NX, z - NZ)
            if d <= 4.6:
                top = Y + 1 + (1 if d < 3.2 else 0)
                for y in range(Y + 1, top + 1):
                    bp.set(x, y, z, rock.pick(x, y, z) if d > 3.2 or y < top else "coarse_dirt")
    # the nest: a ring of branches, a bowl of white feathers, gold, eggs and the reward chest
    for x in range(NX - 4, NX + 5):
        for z in range(NZ - 4, NZ + 5):
            d = math.hypot(x - NX, z - NZ)
            yy = Y + 3
            if 2.6 <= d <= 4.0:
                axis = "x" if abs(x - NX) < abs(z - NZ) else "z"
                bp.set(x, yy, z, rng.choice([f"stripped_birch_log[axis={axis}]", f"spruce_log[axis={axis}]",
                                              f"stripped_oak_log[axis={axis}]", "hay_block[axis=y]"]))
                if rng.random() < 0.4:
                    bp.set(x, yy + 1, z, rng.choice(["birch_fence", "white_wool", "dead_bush"]))
            elif d < 2.6:
                bp.set(x, yy - 1, z, "white_wool")
                bp.set(x, yy, z, rng.choice(["white_carpet", "white_carpet", "light_gray_carpet"]))
    bp.set(NX - 1, Y + 3, NZ + 1, "gold_block")
    bp.set(NX + 1, Y + 3, NZ - 1, "raw_gold_block")
    bp.set(NX + 2, Y + 4, NZ + 2, "gold_block")
    bp.set(NX - 2, Y + 4, NZ - 2, "raw_gold_block")
    bp.set(NX + 1, Y + 3, NZ + 1, "sniffer_egg[hatch=0]")
    bp.set(NX - 1, Y + 3, NZ - 1, "sniffer_egg[hatch=1]")
    bp.chest(NX, Y + 3, NZ, "north", LOOT + "sky_island")
    bp.set(NX, Y + 3, NZ - 2, "bell[attachment=floor,facing=north,powered=false]")
    # steps up the crag from the plaza
    for k, (x, z) in enumerate(((NX, NZ - 5), (NX, NZ - 4))):
        bp.set(x, Y + 1 + k, z, stair("smooth_quartz_stairs", "north"))
    # two tall columns flank the nest, with braziers
    for sx in (-1, 1):
        x, z = NX + sx * 5, NZ - 1
        if _in_shape(x, z):
            bp.set(x, Y + 1, z, "chiseled_quartz_block")
            for y in range(Y + 2, Y + 10):
                bp.set(x, y, z, TRIM)
            bp.set(x, Y + 10, z, "chiseled_quartz_block")
            bp.set(x, Y + 11, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")

    # ---------------------------------------------------------------- seal and mist (after the gateways)
    bp.boss_seal(AX, Y, AZ, "brasshaven:gryphon_knight", 15)
    for (x, z) in north_gate:
        bp.fill(x, Y + 1, z, x, Y + 6, z, "air")
        bp.mist(x, Y + 1, z, x, Y + 6, z)
    for (x, z) in gate_cells:
        bp.fill(x, Y + 1, z, x, Y + 4, z, "air")
        bp.mist(x, Y + 1, z, x, Y + 4, z)
    arch.vines_on(bp, ((AX - 20, Y - 30, AZ - 4), (AX + 20, Y - 1, NZ + 8)), chance=0.02, seed=78, max_len=6)
