"""The Sunken Citadel: the mod's flagship dungeon and home of the Drowned Warden boss.

It is a single watertight template (a jigsaw layout would leave unsealed doorways
whenever a branch fails to place, flooding the halls). The layout is a 3x3 grid of
cells laid out on the ocean floor: an entrance tower that breaks the sea surface,
six themed rooms joined by glass tunnels, the boss arena and a sealed vault.
Three variants shuffle the room themes.
"""
import math

from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOD

CELL = 19
HALF = 7          # room half-size (15x15 rooms)
ROOM_H = 8
HULL = "prismarine_bricks"
TRIM = "dark_prismarine"


def room_shell(bp, cx, cz, height=ROOM_H, glass_roof=False):
    x0, x1, z0, z1 = cx - HALF, cx + HALF, cz - HALF, cz + HALF
    bp.fill(x0, -3, z0, x1, -1, z1, HULL, keep=True)
    bp.room(x0, 0, z0, x1, height, z1, HULL, floor=TRIM, ceiling=HULL)
    for x in (x0, x1):
        for z in (z0, z1):
            bp.fill(x, 0, z, x, height, z, TRIM)
    if glass_roof:
        bp.fill(x0 + 2, height, z0 + 2, x1 - 2, height, z1 - 2, "glass")
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if (x + z) % 4 == 0:
                bp.set(x, 0, z, "prismarine")
    for x, z in ((x0 + 1, z0 + 1), (x1 - 1, z0 + 1), (x0 + 1, z1 - 1), (x1 - 1, z1 - 1)):
        bp.set(x, height - 1, z, "sea_lantern")


def tunnel(bp, a, b):
    """Glass-walled tunnel between two cell centres (axis aligned)."""
    (ax, az), (bx, bz) = a, b
    if az == bz:
        xa, xb = sorted((ax, bx))
        xa, xb = xa + HALF, xb - HALF
        bp.fill(xa, -1, az - 3, xb, 6, az + 3, HULL)
        bp.fill(xa, 2, az - 3, xb, 4, az - 3, "glass")
        bp.fill(xa, 2, az + 3, xb, 4, az + 3, "glass")
        bp.fill(xa, 6, az - 2, xb, 6, az + 2, "glass")
        bp.clear(xa, 1, az - 2, xb, 5, az + 2)
        bp.fill(xa, 0, az - 2, xb, 0, az + 2, TRIM)
    else:
        za, zb = sorted((az, bz))
        za, zb = za + HALF, zb - HALF
        bp.fill(ax - 3, -1, za, ax + 3, 6, zb, HULL)
        bp.fill(ax - 3, 2, za, ax - 3, 4, zb, "glass")
        bp.fill(ax + 3, 2, za, ax + 3, 4, zb, "glass")
        bp.fill(ax - 2, 6, za, ax + 2, 6, zb, "glass")
        bp.clear(ax - 2, 1, za, ax + 2, 5, zb)
        bp.fill(ax - 2, 0, za, ax + 2, 0, zb, TRIM)


# ------------------------------------------------------------------ room themes
def armory(bp, cx, cz):
    room_shell(bp, cx, cz)
    for dx in range(-5, 6, 2):
        bp.entity(cx + dx, 1, cz - 6, {"id": "minecraft:armor_stand", "Rotation": [0.0, 0.0]})
        bp.set(cx + dx, 0, cz - 6, "polished_andesite")
    for dz in (-2, 2):
        bp.fill(cx - 5, 1, cz + dz, cx + 5, 1, cz + dz, "spruce_slab[type=top,waterlogged=false]")
    bp.set(cx - 6, 1, cz + 5, "anvil[facing=east]")
    bp.set(cx - 6, 1, cz + 4, "grindstone[face=floor,facing=east]")
    bp.set(cx + 6, 1, cz + 5, "smithing_table")
    bp.chest(cx + 6, 1, cz, "west", LOOT + "citadel_armory")
    bp.barrel(cx - 6, 1, cz, "east", LOOT + "citadel_armory")
    bp.spawner(cx, 1, cz, "minecraft:drowned")


def library(bp, cx, cz):
    room_shell(bp, cx, cz)
    bp.bookshelf_wall(cx - 6, 1, cz - 6, cx + 6, 4, cz - 6, 0.1)
    bp.bookshelf_wall(cx - 6, 1, cz - 5, cx - 6, 4, cz + 2, 0.1)
    for dz in (-2, 2):
        bp.set(cx, 1, cz + dz, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(cx + 5, 1, cz - 4, "enchanting_table")
    bp.chest(cx + 6, 1, cz + 3, "west", LOOT + "citadel_library")
    bp.lantern(cx, ROOM_H - 1, cz, hanging=True)


def aquarium(bp, cx, cz):
    room_shell(bp, cx, cz, glass_roof=True)
    for (ox, oz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.walls(cx + ox - 2, 1, cz + oz - 2, cx + ox + 2, 5, cz + oz + 2, "glass")
        bp.fill(cx + ox - 1, 1, cz + oz - 1, cx + ox + 1, 5, cz + oz + 1, "water[level=0]")
        bp.set(cx + ox, 1, cz + oz, "sea_pickle[pickles=4,waterlogged=true]")
        for k in range(1, 5):
            bp.set(cx + ox - 1, k, cz + oz + 1, "kelp_plant" if k < 4 else "kelp[age=20]")
        bp.set(cx + ox + 1, 1, cz + oz - 1, "brain_coral_block")
    bp.chest(cx, 1, cz, "south", LOOT + "citadel_common")


def prison(bp, cx, cz):
    room_shell(bp, cx, cz)
    for i, dx in enumerate((-5, -1, 3)):
        bp.walls(cx + dx - 1, 1, cz - 6, cx + dx + 2, 4, cz - 3, "iron_bars")
        bp.clear(cx + dx, 1, cz - 5, cx + dx + 1, 3, cz - 4)
        bp.set(cx + dx, 1, cz - 5, "cobweb" if i != 1 else "skeleton_skull[rotation=0]")
    bp.chest(cx - 5, 1, cz - 5, "south", LOOT + "citadel_common")
    bp.spawner(cx, 1, cz + 3, "minecraft:drowned")
    bp.set(cx + 6, 1, cz + 6, "lantern[hanging=false,waterlogged=false]")


def garden(bp, cx, cz):
    room_shell(bp, cx, cz, glass_roof=True)
    bp.fill(cx - 5, 0, cz - 5, cx + 5, 0, cz + 5, "moss_block")
    for _ in range(30):
        x, z = cx + bp.rng.randint(-5, 5), cz + bp.rng.randint(-5, 5)
        bp.set(x, 1, z, bp.rng.choice(["azalea", "flowering_azalea", "moss_carpet", "fern",
                                        "small_dripleaf[facing=north,half=lower,waterlogged=false]"]))
    bp.disk(cx, 0, cz, 2, "water")
    bp.set(cx, 1, cz, "lily_pad")
    bp.barrel(cx + 6, 1, cz - 6, "up", LOOT + "citadel_common")


def shrine(bp, cx, cz):
    room_shell(bp, cx, cz, height=11)
    bp.fill(cx - 2, 1, cz - 6, cx + 2, 1, cz - 4, "dark_prismarine")
    bp.set(cx, 2, cz - 5, "conduit[waterlogged=false]")
    for dx in (-2, 2):
        bp.fill(cx + dx, 2, cz - 6, cx + dx, 6, cz - 6, "prismarine_wall")
        bp.set(cx + dx, 7, cz - 6, "sea_lantern")
    for dz in range(-1, 6, 2):
        bp.stairs(cx - 3, 1, cz + dz, "prismarine_brick_stairs", "east")
        bp.stairs(cx + 3, 1, cz + dz, "prismarine_brick_stairs", "west")
    bp.chest(cx, 1, cz - 3, "south", LOOT + "citadel_shrine")


THEMES = [armory, library, aquarium, prison, garden]


# ------------------------------------------------------------------ special cells
def entrance_tower(bp, cx, cz):
    room_shell(bp, cx, cz)
    r, top = 4, 52
    bp.cylinder(cx, ROOM_H, cz, top, r, HULL)
    bp.clear(cx - 2, ROOM_H, cz - 2, cx + 2, ROOM_H, cz + 2)
    bp.disk(cx, ROOM_H, cz, r - 1, "air")
    for y in range(ROOM_H + 6, top, 12):
        for dx, dz in ((r, 0), (-r, 0), (0, -r)):
            bp.set(cx + dx, y, cz + dz, "sea_lantern")
    bp.fill(cx, 1, cz + 1, cx, top, cz + 1, TRIM)
    bp.ladder(cx, 1, cz, top + 1, "north")
    # lookout cabin above the waves
    bp.disk(cx, top + 1, cz, r + 2, HULL)
    bp.disk(cx, top + 2, cz, r + 2, "prismarine_wall", hollow=True)
    bp.cylinder(cx, top + 2, cz, top + 5, r - 1, "glass", hollow=True)
    bp.disk(cx, top + 6, cz, r - 1, TRIM)
    bp.set(cx, top + 7, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(cx, top + 5, cz, "sea_lantern")
    bp.set(cx, top + 1, cz, "ladder[facing=north,waterlogged=false]")
    for y in (top + 2, top + 3):
        bp.set(cx, y, cz - r + 1, "air")
        bp.set(cx, y, cz + r - 1, "air")
    bp.set(cx - 2, top + 2, cz + 2, "lantern[hanging=false,waterlogged=false]")
    bp.set(cx + 2, top + 2, cz - 2, MOD["waystone"])
    bp.chest(cx - 5, 1, cz - 5, "south", LOOT + "citadel_common")


def boss_arena(bp, cx, cz):
    R, H = 10, 15
    bp.disk(cx, -2, cz, R + 1, HULL)
    bp.disk(cx, -1, cz, R + 1, HULL)
    bp.cylinder(cx, 0, cz, 6, R + 1, HULL)
    bp.disk(cx, 0, cz, R, TRIM)
    bp.sphere(cx, 6, cz, R + 1, "glass", hollow=True, half="top")
    bp.sphere(cx, 6, cz, R, "air", half="top")
    for a in range(0, 360, 30):  # dome ribs
        for t in range(0, 90, 4):
            x = cx + round(math.cos(math.radians(a)) * math.cos(math.radians(t)) * (R + 1))
            z = cz + round(math.sin(math.radians(a)) * math.cos(math.radians(t)) * (R + 1))
            y = 6 + round(math.sin(math.radians(t)) * (R + 1))
            bp.set(x, y, z, TRIM)
    for a in range(0, 360, 60):
        x, z = cx + round(math.cos(math.radians(a)) * 7), cz + round(math.sin(math.radians(a)) * 7)
        bp.fill(x, 1, z, x, 9, z, "prismarine_bricks")
        bp.set(x, 10, z, "sea_lantern")
    for ring_r in (3, 5):
        for a in range(0, 360, 8):
            x, z = cx + round(math.cos(math.radians(a)) * ring_r), cz + round(math.sin(math.radians(a)) * ring_r)
            bp.set(x, 0, z, "prismarine" if ring_r == 3 else "sea_lantern")
    bp.fill(cx - 1, 1, cz - 1, cx + 1, 1, cz + 1, TRIM)
    bp.set(cx, 2, cz, MOD["guardian_altar"])
    for x, z in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
        bp.set(x, 2, z, "prismarine_wall")
    bp.chest(cx, 1, cz - R + 1, "south", LOOT + "citadel_arena")


def vault(bp, cx, cz):
    room_shell(bp, cx, cz, height=7)
    for x in range(cx - 5, cx + 6, 2):
        bp.chest(x, 1, cz - 6, "south", LOOT + "citadel_vault" if x % 4 == 1 else None)
    bp.fill(cx - 5, 1, cz + 5, cx - 3, 2, cz + 6, "gold_block")
    bp.fill(cx + 3, 1, cz + 5, cx + 5, 1, cz + 6, "emerald_block")
    bp.set(cx + 4, 2, cz + 5, "diamond_block")
    bp.set(cx, 1, cz, "beacon")
    bp.fill(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "iron_block")


def citadel(variant):
    def build(bp):
        bp.rng.seed(f"citadel-{variant}")

        def g(i, j):
            return i * CELL, j * CELL

        links = [((0, 1), (0, 0)), ((0, 0), (-1, 0)), ((0, 0), (1, 0)), ((-1, 0), (-1, 1)),
                 ((1, 0), (1, 1)), ((1, 0), (1, -1))]
        # tunnels first: rooms built afterwards re-seal their own walls
        for a, b in links:
            tunnel(bp, g(*a), g(*b))
        themes = THEMES[:]
        bp.rng.shuffle(themes)
        for theme, cell in zip(themes, [(-1, 0), (1, 0), (-1, 1), (1, 1)]):
            theme(bp, *g(*cell))
        entrance_tower(bp, *g(0, 1))
        hx, hz = g(0, 0)
        room_shell(bp, hx, hz, height=10)
        bp.fill(hx - 1, 1, hz - 1, hx + 1, 1, hz + 1, TRIM)
        bp.fill(hx, 2, hz, hx, 4, hz, "prismarine_bricks")
        bp.set(hx, 5, hz, "sea_lantern")
        shrine(bp, *g(1, -1))
        vault(bp, *g(-1, -1))
        ax, az = g(0, -1)
        boss_arena(bp, ax, az)
        # doorways through both walls of every tunnel
        for a, b in links:
            (x0, z0), (x1, z1) = g(*a), g(*b)
            if z0 == z1:
                for x in (min(x0, x1) + HALF, max(x0, x1) - HALF):
                    bp.clear(x, 1, z0 - 2, x, 5, z0 + 2)
            else:
                for z in (min(z0, z1) + HALF, max(z0, z1) - HALF):
                    bp.clear(x0 - 2, 1, z, x0 + 2, 5, z)
        # central hall -> arena: short archway (arena wall sits right next to the hall)
        bp.fill(ax - 3, -1, az + 11, ax + 3, 6, hz - HALF, HULL)
        bp.clear(ax - 2, 1, az + 10, ax + 2, 5, hz - HALF)
        bp.fill(ax - 2, 0, az + 11, ax + 2, 0, hz - HALF, TRIM)
        # arena -> vault, sealed with iron bars (opened by defeating the Warden)
        vx, vz = g(-1, -1)
        bp.fill(vx + HALF, -1, vz - 3, ax - 11, 6, vz + 3, HULL)
        bp.clear(vx + HALF, 1, vz - 2, ax - 10, 5, vz + 2)
        bp.fill(vx + HALF, 0, vz - 2, ax - 11, 0, vz + 2, TRIM)
        bp.fill(vx + HALF, 1, vz - 2, vx + HALF, 5, vz + 2, MOD["vault_bars"])
    return build


register(StructureDef(
    "sunken_citadel", "overworld", ["deep_ocean", "deep_cold_ocean", "deep_lukewarm_ocean",
                                     "deep_frozen_ocean", "ocean", "cold_ocean"],
    [Piece(f"citadel_{v}", citadel(v)) for v in range(3)],
    spacing=48, separation=16, heightmap="OCEAN_FLOOR_WG", adaptation="beard_box", processors="none",
    exclusion=("minecraft:ocean_monuments", 6), max_distance=100,
    title_fr="Citadelle engloutie", title_en="Sunken Citadel"))
