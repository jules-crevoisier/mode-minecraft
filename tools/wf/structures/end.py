"""End structures: floating over the void around the outer islands."""
import math

from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD

OUTER_END = ["end_highlands", "end_midlands", "small_end_islands", "end_barrens"]


def floating_rock(bp, cx, cy, cz, rx, ry, rz, top="end_stone", body="end_stone"):
    bp.blob(cx, cy, cz, rx, ry, rz, body, noise=0.45, half="bottom")
    tops = {}
    for (x, y, z), b in bp.blocks.items():
        if b[0] == f"minecraft:{body}" and y > tops.get((x, z), -999):
            tops[(x, z)] = y
    for (x, z), y in tops.items():
        bp.set(x, y, z, top)


def chorus(bp, x, y, z, h):
    """A chorus plant with a few branches; connection properties computed afterwards."""
    cells = set()
    for k in range(h):
        cells.add((x, y + k, z))
    for k in range(2, h - 1, 2):
        dx, dz = bp.rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        for j in range(1, 3):
            cells.add((x + dx * j, y + k, z + dz * j))
        cells.add((x + dx * 2, y + k + 1, z + dz * 2))
    for (cx, cy, cz) in cells:
        props = {}
        for d, (dx, dy, dz) in (("up", (0, 1, 0)), ("down", (0, -1, 0)), ("north", (0, 0, -1)),
                                ("south", (0, 0, 1)), ("east", (1, 0, 0)), ("west", (-1, 0, 0))):
            n = (cx + dx, cy + dy, cz + dz)
            props[d] = "true" if n in cells or (d == "down" and cy == y) else "false"
        bp.set(cx, cy, cz, ("minecraft:chorus_plant", props))
    topmost = max(cells, key=lambda p: p[1])
    bp.set(topmost[0], topmost[1] + 1, topmost[2], "chorus_flower[age=5]")


# ============================================================ Void observatory
def void_observatory(bp):
    floating_rock(bp, 0, 0, 0, 12, 9, 12)
    bp.disk(0, 0, 0, 9, "end_stone_bricks")
    bp.disk(0, 0, 0, 7, "purpur_block")
    bp.sphere(0, 0, 0, 7, "purpur_block", hollow=True, half="top")
    bp.sphere(0, 0, 0, 6, "air", half="top")
    bp.disk(0, 0, 0, 6, "purpur_block")
    # glass ring around the dome
    for a in range(0, 360, 10):
        x, z = round(math.cos(math.radians(a)) * 7), round(math.sin(math.radians(a)) * 7)
        for y in (2, 3):
            if bp.get(x, y, z) == "minecraft:purpur_block":
                bp.set(x, y, z, "magenta_stained_glass")
    # telescope aimed at the sky through an oculus
    bp.fill(-1, 7, -1, 1, 7, 1, "air")
    bp.fill(0, 1, 0, 0, 2, 0, "purpur_pillar[axis=y]")
    bp.set(0, 3, 0, "end_rod[facing=up]")
    for p in ((0, 4, 0), (0, 5, 1), (0, 6, 1)):
        bp.set(*p, "obsidian")
    bp.set(0, 7, 1, "end_rod[facing=up]")
    # doorway
    bp.clear(-1, 1, 7, 1, 3, 7)
    bp.fill(-1, 0, 8, 1, 0, 11, "end_stone_bricks")
    for z in range(8, 12):
        bp.set(-2, 1, z, "end_stone_brick_wall")
        bp.set(2, 1, z, "end_stone_brick_wall")
    bp.set(-2, 2, 11, "end_rod[facing=up]")
    bp.set(2, 2, 11, "end_rod[facing=up]")
    # star charts and loot
    bp.set(4, 1, -2, "cartography_table")
    bp.set(4, 1, -1, "lectern[facing=west,has_book=false,powered=false]")
    bp.chest(-4, 1, -2, "east", LOOT + "void_observatory")
    bp.set(-4, 1, 2, "ender_chest[facing=east,waterlogged=false]")
    bp.set(3, 1, 3, "enchanting_table")
    bp.bookshelf_wall(5, 1, 1, 5, 2, 4, 0.0)
    for x, z in ((-5, 0), (5, -4), (0, -5)):
        bp.set(x, 1, z, "end_rod[facing=up]")
    # orbiting satellite rocks with crystals
    for a in (30, 150, 270):
        sx, sz = round(math.cos(math.radians(a)) * 17), round(math.sin(math.radians(a)) * 17)
        floating_rock(bp, sx, 4, sz, 3, 3, 3)
        bp.set(sx, 5, sz, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.spawner(0, 1, -4, MOB["void_stalker"])


register(StructureDef(
    "void_observatory", "end", OUTER_END, [Piece("observatory", void_observatory)],
    spacing=20, separation=6, adaptation="none", height=("uniform", 60, 85), processors="aging",
    title_fr="Observatoire du vide", title_en="Void Observatory"))


# ============================================================ Floating chorus garden
def chorus_garden(bp):
    floating_rock(bp, 0, 0, 0, 14, 8, 11)
    for _ in range(12):
        x, z = bp.rng.randint(-11, 11), bp.rng.randint(-8, 8)
        column = [y for (xx, y, zz) in bp.blocks if xx == x and zz == z]
        top = max(column) if column else None
        if top is not None and bp.get(x, top, z) == "minecraft:end_stone":
            chorus(bp, x, top + 1, z, bp.rng.randint(4, 7))
    # gardener's purpur pavilion
    bp.fill(-3, 1, -3, 3, 1, 3, "purpur_block")
    for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        bp.fill(x, 2, z, x, 5, z, "purpur_pillar[axis=y]")
    bp.fill(-3, 6, -3, 3, 6, 3, "purpur_slab[type=bottom,waterlogged=false]")
    bp.fill(-2, 2, -2, 2, 5, 2, "air")
    bp.chest(0, 2, 0, "south", LOOT + "chorus_garden")
    bp.set(1, 2, -2, "composter[level=6]")
    bp.set(-1, 2, -2, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(0, 5, 0, "end_rod[facing=down]")
    # hanging gardens beneath the island
    for _ in range(25):
        x, z = bp.rng.randint(-10, 10), bp.rng.randint(-8, 8)
        bottoms = [y for (xx, y, zz) in bp.blocks if xx == x and zz == z]
        if bottoms:
            b = min(bottoms)
            n = bp.rng.randint(2, 6)
            for k in range(1, n):
                bp.set(x, b - k, z, "obsidian" if k == 1 and bp.rng.random() < 0.3 else "end_stone")
            if bp.rng.random() < 0.3:
                bp.set(x, b - n, z, "end_rod[facing=down]")


register(StructureDef(
    "chorus_garden", "end", OUTER_END, [Piece("garden", chorus_garden)],
    spacing=18, separation=5, adaptation="none", height=("uniform", 55, 80), processors="none",
    title_fr="Jardin flottant de chorus", title_en="Floating Chorus Garden"))


# ============================================================ End archive
def end_archive(bp):
    floating_rock(bp, 0, 0, 0, 9, 10, 9)
    W = 6
    H = 30
    bp.fill(-W, 0, -W, W, 0, W, "end_stone_bricks")
    bp.walls(-W + 1, 1, -W + 1, W - 1, H, W - 1, "purpur_block")
    for x in (-W + 1, W - 1):
        for z in (-W + 1, W - 1):
            bp.fill(x, 1, z, x, H + 2, z, "purpur_pillar[axis=y]")
    bp.clear(-W + 2, 1, -W + 2, W - 2, H, W - 2)
    # stacked reading floors linked by a spiral of slabs along the walls
    for fy in range(6, H, 6):
        bp.fill(-W + 2, fy, -W + 2, W - 2, fy, W - 2, "purpur_block")
        bp.fill(-1, fy, -1, 1, fy, 1, "air")
        bp.fill(-1, fy, -1, 1, fy, 1, "purpur_slab[type=top,waterlogged=false]")
        bp.clear(-W + 2, fy, -W + 2, -W + 3, fy, -W + 3)
        bp.bookshelf_wall(W - 2, fy + 1, -W + 2, W - 2, fy + 3, W - 2, 0.05)
        bp.bookshelf_wall(-W + 2, fy + 1, W - 2, W - 3, fy + 3, W - 2, 0.05)
        bp.set(0, fy + 1, 0, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(0, fy + 4, 0, "end_rod[facing=down]")
        for i in range(-W + 3, W - 2, 3):
            for (x, z) in ((i, -W + 1), (i, W - 1), (-W + 1, i), (W - 1, i)):
                bp.fill(x, fy + 2, z, x, fy + 4, z, "magenta_stained_glass_pane")
        for i in range(-W + 1, W):
            for (x, z) in ((i, -W + 1), (i, W - 1), (-W + 1, i), (W - 1, i)):
                if bp.get(x, fy, z) == "minecraft:purpur_block":
                    bp.set(x, fy, z, "end_stone_bricks")
    bp.fill(-W + 2, 1, -W + 2, -W + 2, H - 1, -W + 2, "purpur_pillar[axis=y]")
    bp.ladder(-W + 3, 1, -W + 2, H, "south")
    bp.bookshelf_wall(W - 2, 1, -W + 2, W - 2, 3, W - 2, 0.05)
    bp.set(0, 1, 0, "enchanting_table")
    bp.set(2, 1, 2, MOD["waystone"])
    bp.clear(0, 1, W - 1, 0, 2, W - 1)
    # dome roof
    bp.sphere(0, H, 0, W, "purpur_block", hollow=True, half="top")
    bp.sphere(0, H, 0, W - 1, "air", half="top")
    bp.fill(-W + 2, H, -W + 2, W - 2, H, W - 2, "purpur_block")
    bp.set(-W + 3, H, -W + 2, "ladder[facing=south,waterlogged=false]")
    bp.set(0, H + W + 1, 0, "end_rod[facing=up]")
    bp.set(0, H + 1, 0, "dragon_head[rotation=8]")
    bp.chest(2, H + 1, 2, "north", LOOT + "end_archive_top")
    bp.chest(-3, 7, 3, "east", LOOT + "end_archive")
    bp.chest(3, 19, -3, "west", LOOT + "end_archive")
    bp.spawner(2, 13, 2, "minecraft:endermite")
    # flying buttresses to two satellite rocks
    for sx in (-15, 15):
        floating_rock(bp, sx, 10, 0, 4, 4, 4)
        bp.line((sx, 11, 0), (W * (1 if sx > 0 else -1), 16, 0), "end_stone_brick_wall")
        bp.set(sx, 12, 0, "end_rod[facing=up]")


register(StructureDef(
    "end_archive", "end", OUTER_END, [Piece("archive", end_archive)],
    spacing=22, separation=7, adaptation="none", height=("uniform", 50, 70), processors="aging",
    title_fr="Archive de l'End", title_en="End Archive"))


# ============================================================ Void ship wreck
def void_ship(bp):
    L = 30
    floating_rock(bp, 0, -2, 18, 9, 6, 9)
    tilt = 0.12
    for z in range(0, L):
        hw = max(1, round(4 * math.sin(math.pi * min(1.0, 0.2 + z / L))))
        dy = round((z - L / 2) * tilt)
        for y in range(0, 5):
            w = hw if y >= 2 else max(1, hw - (2 - y))
            for x in range(-w, w + 1):
                edge = abs(x) == w or y == 0
                bp.set(x, y + dy, z, "purpur_block" if edge else "air")
        for x in range(-hw, hw + 1):
            bp.set(x, 5 + dy, z, "purpur_slab[type=bottom,waterlogged=false]" if abs(x) == hw else "end_stone_bricks")
    # snapped mast and torn magenta sails
    bp.fill(0, 6, 14, 0, 18, 14, "purpur_pillar[axis=y]")
    for y in range(9, 17):
        for x in range(-4, 5):
            if bp.rng.random() < 0.7 - (y - 9) * 0.05:
                bp.set(x, y, 15, "magenta_wool")
    bp.line((0, 6, 22), (5, 4, 28), "purpur_pillar[axis=y]")
    # the broken bow section embedded in the rock
    for (x, y, z), b in list(bp.blocks.items()):
        if z > 24 and bp.rng.random() < 0.25 and b[0] != "minecraft:end_stone":
            bp.remove(x, y, z)
    bp.chest(0, 1, 6, "south", LOOT + "void_ship")
    bp.set(0, 6, 2, "dragon_head[rotation=0]")
    bp.set(2, 1, 10, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
    bp.spawner(-1, 1, 12, MOB["void_stalker"])
    for z in range(2, L - 4, 6):
        bp.set(3, 6, z, "end_rod[facing=up]")


register(StructureDef(
    "void_ship", "end", OUTER_END, [Piece("ship", void_ship)],
    spacing=24, separation=8, adaptation="none", height=("uniform", 55, 80), processors="none",
    title_fr="Épave du vide", title_en="Void Ship Wreck"))


# ============================================================ Void Warden's nest (End mini-boss lair)
def void_nest(bp):
    floating_rock(bp, 0, 0, 0, 16, 11, 16, top="obsidian", body="end_stone")
    bp.disk(0, 0, 0, 11, "obsidian")
    bp.disk(0, 0, 0, 9, "crying_obsidian", hollow=True)
    bp.disk(0, 0, 0, 7, "end_stone_bricks")
    # curved spikes like a ribcage around the arena
    for a in range(0, 360, 30):
        ang = math.radians(a)
        bx, bz = math.cos(ang) * 12, math.sin(ang) * 12
        for t in range(0, 14):
            r = 12 - t * 0.45
            x, z = round(math.cos(ang) * r), round(math.sin(ang) * r)
            bp.set(x, 1 + t, z, "obsidian" if t < 10 else "crying_obsidian")
    # arena centre: the summoning altar (activated by the mod's boss logic)
    bp.fill(-1, 1, -1, 1, 1, 1, "purpur_block")
    bp.set(0, 2, 0, MOD["void_altar"])
    for x, z in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        bp.set(x, 1, z, "end_rod[facing=up]")
    for a in range(0, 360, 90):
        x, z = round(math.cos(math.radians(a + 45)) * 6), round(math.sin(math.radians(a + 45)) * 6)
        bp.fill(x, 1, z, x, 3, z, "obsidian")
        bp.set(x, 4, z, "end_rod[facing=up]")
    bp.chest(0, 1, -8, "south", LOOT + "void_nest")
    bp.chest(0, 1, 8, "north", LOOT + "void_nest")


register(StructureDef(
    "void_nest", "end", ["end_highlands", "end_midlands"], [Piece("nest", void_nest)],
    spacing=36, separation=12, adaptation="none", height=("uniform", 58, 75), processors="none",
    title_fr="Nid du Gardien du Vide", title_en="Void Warden's Nest"))
