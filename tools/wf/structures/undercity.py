"""The Undercity: a town hanging in a vast carved cavern, Zaun-style (Lot 6, mega-structures, underground).

The template carves its own cavern (an 80 x 46 x 80 ellipsoid) deep underground:
  * a toxic green lake on the floor with rusted pontoons,
  * a central pillar from floor to ceiling, ringed by platforms at three levels and climbed by ladders,
  * stilt houses on the cavern walls at each level, joined to the pillar by railed catwalks,
  * pipes, chimneys to the ceiling, green froglights and amber Edison lamps everywhere.
Origin y = 0 is the cavern floor level (the lake surface).
"""
import math

from ..defs import Piece, StructureDef, register
from ..parts import LOOT

W = "wayfarers:"
BRASS, IRON, TREAD, COPPER, VERD = (W + "brass_plating", W + "dark_iron_plating", W + "diamond_plate",
                                    W + "copper_plating", W + "verdigris_plating")
GEAR, PIPES, EDISON, AETHER, SMOKE = W + "gear_panel", W + "copper_pipes", W + "edison_lamp", W + "aether_conduit", W + "smokestack_bricks"
GREEN = "verdant_froglight[axis=y]"

RX, RY, RZ = 40, 26, 40
FLOOR = -4        # deepest point of the lake bed
LEVELS = [6, 16, 26]
PILLAR_R = 4


def cavern(bp):
    """Carve the ellipsoid (upper part) and a lake bowl (lower part), lining the shell with rock."""
    for x in range(-RX - 1, RX + 2):
        for z in range(-RZ - 1, RZ + 2):
            for y in range(FLOOR - 3, RY + 2):
                dy = (y - 4) / RY if y >= 4 else (y - 4) / 10.0
                d = (x / RX) ** 2 + dy ** 2 + (z / RZ) ** 2
                if d <= 1.0:
                    bp.set(x, y, z, "air")
                elif d <= 1.12:
                    rough = (x * 7 + y * 13 + z * 5) % 11 == 0
                    bp.set(x, y, z, "tuff" if rough else ("deepslate" if y < 12 else "stone"))
    # lake: below y 0 the bowl is water (with a lime glow from sea pickles)
    for x in range(-RX, RX + 1):
        for z in range(-RZ, RZ + 1):
            for y in range(FLOOR, 0):
                if bp.get(x, y, z) is not None and bp.get(x, y, z) == "minecraft:air":
                    bp.set(x, y, z, "water[level=0]")
            if bp.get(x, FLOOR - 1, z) is not None and bp.get(x, FLOOR - 1, z) != "minecraft:air":
                if (x * 3 + z * 5) % 17 == 0:
                    bp.set(x, FLOOR, z, "sea_pickle[pickles=4,waterlogged=true]")
    # shore ring: a mud and gravel beach where the bowl meets the walls
    for x in range(-RX, RX + 1):
        for z in range(-RZ, RZ + 1):
            r = math.hypot(x / RX, z / RZ)
            if 0.86 < r <= 1.0:
                for y in range(FLOOR, 1):
                    bp.set(x, y, z, "mud" if (x + z) % 3 else "gravel")


def pillar(bp):
    top = RY + 4
    for y in range(FLOOR - 2, top):
        for x in range(-PILLAR_R, PILLAR_R + 1):
            for z in range(-PILLAR_R, PILLAR_R + 1):
                d = math.hypot(x, z)
                if d <= PILLAR_R + 0.3:
                    band = y % 10 == 0
                    rib = (x == 0 or z == 0) and d > PILLAR_R - 0.8
                    bp.set(x, y, z, BRASS if band else (IRON if rib else SMOKE))
    # glowing seams
    for y in range(2, top, 5):
        for (x, z) in ((PILLAR_R, 1), (-PILLAR_R, -1), (1, -PILLAR_R), (-1, PILLAR_R)):
            bp.set(x, y, z, GREEN)
    # ladders up the north side of the pillar to every level
    for y in range(1, LEVELS[-1] + 1):
        bp.set(0, y, -PILLAR_R - 1, "ladder[facing=north,waterlogged=false]")
    # platforms around the pillar
    for ly in LEVELS:
        for x in range(-PILLAR_R - 4, PILLAR_R + 5):
            for z in range(-PILLAR_R - 4, PILLAR_R + 5):
                d = math.hypot(x, z)
                if PILLAR_R < d <= PILLAR_R + 4:
                    bp.set(x, ly, z, TREAD)
                    if d > PILLAR_R + 3.2:
                        facing = _out_facing(x, z)
                        bp.set(x, ly + 1, z, f"{W}brass_railing[facing={facing}]")
        bp.set(0, ly, -PILLAR_R - 1, TREAD)
        bp.set(0, ly + 1, -PILLAR_R - 1, "ladder[facing=north,waterlogged=false]")
        for (x, z) in ((PILLAR_R + 2, 0), (-PILLAR_R - 2, 0), (0, PILLAR_R + 2)):
            bp.set(x, ly + 4, z, IRON)
            bp.set(x, ly + 3, z, W + "hanging_edison_lamp")
    # brace arches from the pillar to the ceiling
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        for i in range(PILLAR_R, 18):
            x, z = round(math.cos(a) * i), round(math.sin(a) * i)
            y = top - 1 - int((i - PILLAR_R) * 0.25)
            bp.set(x, y, z, IRON)


def _out_facing(x, z):
    if abs(z) >= abs(x):
        return "north" if z < 0 else "south"
    return "west" if x < 0 else "east"


def _ring_point(ang, level_y, inset):
    """A point on the cavern wall at `level_y`, `inset` blocks inside the shell."""
    dy = (level_y - 4) / RY
    k = math.sqrt(max(0.05, 1 - dy * dy))
    rx, rz = RX * k - inset, RZ * k - inset
    return round(math.cos(ang) * rx), round(math.sin(ang) * rz)


def shack(bp, cx, y, cz, ang, seed):
    """A stilt house leaning on the cavern wall: rusted plates, a lit window, a chimney through the roof."""
    w, d, h = 3, 3, 4
    out = (math.cos(ang), math.sin(ang))
    face = _out_facing(-out[0], -out[1])  # facing the pillar
    mats = [COPPER, IRON, VERD, SMOKE]
    wall = mats[seed % len(mats)]
    for x in range(cx - w, cx + w + 1):
        for z in range(cz - d, cz + d + 1):
            edge = abs(x - cx) == w or abs(z - cz) == d
            bp.set(x, y, z, TREAD)
            for yy in range(y + 1, y + h + 1):
                if edge:
                    corner = abs(x - cx) == w and abs(z - cz) == d
                    window = yy == y + 2 and not corner and (x - cx + z - cz) % 3 == 0
                    bp.set(x, yy, z, BRASS if corner else ("glass_pane" if window else wall))
                else:
                    bp.set(x, yy, z, "air")
            bp.set(x, y + h + 1, z, W + "dark_iron_plating_slab[type=bottom,waterlogged=false]")
    # stilts down to the shore or the wall
    for (x, z) in ((cx - w, cz - d), (cx + w, cz - d), (cx - w, cz + d), (cx + w, cz + d)):
        yy = y - 1
        while yy > FLOOR - 2 and (bp.get(x, yy, z) is None or bp.get(x, yy, z) in ("minecraft:air", "minecraft:water")):
            bp.set(x, yy, z, W + "dark_iron_plating_wall")
            yy -= 1
    # door facing the pillar
    dx, dz = {"north": (0, -d), "south": (0, d), "west": (-w, 0), "east": (w, 0)}[face]
    bp.set(cx + dx, y + 1, cz + dz, "air")
    bp.set(cx + dx, y + 2, cz + dz, "air")
    bp.door(cx + dx, y + 1, cz + dz, face, "spruce")
    # inside: lamp, crate or chest, bed
    bp.set(cx, y + h, cz, W + "brass_chandelier" if seed % 3 == 0 else EDISON)
    if seed % 2:
        bp.chest(cx - w + 1, y + 1, cz, "east", loot=LOOT + "undercity")
    else:
        bp.set(cx - w + 1, y + 1, cz, W + "compacting_crate[facing=east]")
    bp.set(cx + w - 1, y + 1, cz + d - 1, W + "mahogany_table")
    # chimney
    for yy in range(y + h + 1, y + h + 5):
        bp.set(cx + w - 1, yy, cz - d + 1, SMOKE)
    bp.set(cx + w - 1, y + h + 4, cz - d + 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.set(cx + w - 1, y + h + 3, cz - d + 1, SMOKE)
    return cx + dx + (1 if face == "east" else -1 if face == "west" else 0), cz + dz + (1 if face == "south" else -1 if face == "north" else 0)


def catwalk(bp, p0, p1, y):
    (x0, z0), (x1, z1) = p0, p1
    n = max(abs(x1 - x0), abs(z1 - z0), 1)
    prev = None
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        z = round(z0 + (z1 - z0) * i / n)
        for ox, oz in ((0, 0), (1, 0), (0, 1)):
            if bp.get(x + ox, y, z + oz) is None or bp.get(x + ox, y, z + oz) in ("minecraft:air", "minecraft:water"):
                bp.set(x + ox, y, z + oz, TREAD)
        if i % 6 == 3:
            bp.set(x, y - 1, z, W + "dark_iron_plating_slab[type=top,waterlogged=false]")
        prev = (x, z)
    return prev


def pipes(bp):
    """Big pipes running along the walls and down into the lake."""
    for ang in range(15, 360, 60):
        a = math.radians(ang)
        for y in range(1, RY - 2):
            x, z = _ring_point(a, y, 2)
            if bp.get(x, y, z) is not None and bp.get(x, y, z) == "minecraft:air":
                bp.set(x, y, z, W + "copper_pipe[axis=y]")
                if y % 9 == 0:
                    bp.set(x, y, z, GEAR)


def lights(bp):
    for ang in range(0, 360, 20):
        a = math.radians(ang)
        x, z = _ring_point(a, RY - 6, 3)
        bp.set(x, RY - 6, z, GREEN)
    for (x, z) in ((10, 10), (-12, 8), (8, -14), (-9, -11), (16, -3), (-17, 2)):
        bp.set(x, 0, z, W + "dark_iron_plating_slab[type=bottom,waterlogged=true]")
        bp.set(x, 1, z, W + "smokestack_brick_wall")
        bp.set(x, 2, z, GREEN)


def undercity(bp):
    cavern(bp)
    pillar(bp)
    pipes(bp)
    seed = 0
    for li, ly in enumerate(LEVELS):
        for k in range(6):
            ang = math.radians(k * 60 + li * 20 + 10)
            cx, cz = _ring_point(ang, ly, 8)
            door = shack(bp, cx, ly, cz, ang, seed)
            seed += 1
            # catwalk from the house door to the pillar platform
            px, pz = round(math.cos(ang) * (PILLAR_R + 4)), round(math.sin(ang) * (PILLAR_R + 4))
            catwalk(bp, door, (px, pz), ly)
    lights(bp)
    # the boss of the place lives in the top tier's biggest shack: a vault on the pillar top
    bp.chest(0, LEVELS[-1] + 1, PILLAR_R + 2, "north", loot=LOOT + "undercity_vault")


register(StructureDef(
    "undercity", "overworld", ["#minecraft:is_overworld"],
    [Piece("cavern", undercity)],
    spacing=72, separation=28, adaptation="none", height=("uniform", -30, -12), processors="none",
    step="underground_structures", max_distance=100, foundation=False,
    # steam drones patrol the dark corners of the cavern, clockwork spiders scuttle on the catwalks
    spawns=[("wayfarers:steam_drone", 35, 1, 2), ("wayfarers:clockwork_spider", 30, 2, 3),
            ("minecraft:zombie", 40, 1, 3), ("minecraft:skeleton", 30, 1, 2), ("minecraft:creeper", 20, 1, 1)],
    title_fr="Les Bas-fonds", title_en="The Undercity"))
