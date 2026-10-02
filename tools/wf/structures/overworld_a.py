"""Overworld structures (group A)."""
import math

from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import (LOOT, MOB, MOD, banner_pole, crate_stack, garden, lamp_post, leaves, palm, path,
                     round_tower, timber_house, tree)

TEMPERATE = ["#minecraft:is_forest", "plains", "sunflower_plains", "meadow", "#minecraft:is_taiga",
             "savanna", "cherry_grove"]


# ============================================================ Guild outpost
def guild_outpost(wood, roof, banner):
    def build(bp):
        # cobbled yard
        for x in range(-2, 22):
            for z in range(-2, 20):
                if bp.rng.random() < 0.9:
                    bp.set(x, 0, z, bp.rng.choice(["gravel", "coarse_dirt", "dirt_path", "cobblestone"]))
        ridge = timber_house(bp, 0, 0, 0, 11, 9, floors=2, wood=wood, roof=roof, door_side="south",
                             loot=LOOT + "guild_outpost", interior="map")
        # lookout tower attached on the east side
        round_tower(bp, 16, 0, 4, 3, 14, wall="stone_bricks", floor=f"{wood}_planks",
                    roof=f"{roof}_stairs", roof_block=f"{roof}_planks", floors_every=5)
        bp.clear(11, 1, 4, 13, 2, 4)
        bp.door(13, 1, 4, "west", wood)
        bp.fill(11, 1, 4, 12, 1, 4, "air")
        bp.fill(11, 0, 3, 13, 0, 5, "stone_bricks")
        bp.chest(17, 11, 4, "west", LOOT + "guild_outpost")
        bp.set(15, 11, 4, "cartography_table")
        # yard: fence, campfire, notice board, map table, crates
        for x in range(-2, 22):
            for z in (-2, 19):
                bp.set(x, 1, z, f"{wood}_fence")
        for z in range(-2, 20):
            for x in (-2, 21):
                bp.set(x, 1, z, f"{wood}_fence")
        for x in (4, 5, 6):
            bp.set(x, 1, 19, "air")
        bp.set(4, 1, 19, f"{wood}_fence_gate[facing=south,in_wall=false,open=true,powered=false]")
        bp.set(6, 1, 19, f"{wood}_fence_gate[facing=south,in_wall=false,open=true,powered=false]")
        bp.set(5, 1, 19, "air")
        bp.set(10, 0, 14, "cobblestone")
        bp.set(10, 1, 14, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
        for dx, dz, f in ((-1, 0, "east"), (1, 0, "west"), (0, -1, "south"), (0, 1, "north")):
            bp.stairs(10 + dx * 2, 1, 14 + dz * 2, f"{wood}_stairs", f)
        bp.set(15, 1, 15, "fletching_table")
        bp.set(16, 1, 15, "smithing_table")
        bp.set(17, 1, 15, "anvil[facing=north]")
        crate_stack(bp, 19, 1, 17)
        crate_stack(bp, 19, 1, 16)
        bp.set(18, 1, 17, "hay_block[axis=y]")
        # the guild's "waystone" plinth (replaced by the real block once the mod registers it)
        bp.fill(1, 1, 13, 3, 1, 15, "chiseled_stone_bricks")
        bp.set(2, 2, 14, MOD["waystone"])
        bp.set(2, 3, 14, "lantern[hanging=false,waterlogged=false]")
        for x, z in ((1, 13), (3, 13), (1, 15), (3, 15)):
            bp.set(x, 2, z, "stone_brick_wall")
        banner_pole(bp, 7, 1, 17, banner)
        banner_pole(bp, 3, 1, 17, banner)
        lamp_post(bp, 12, 1, 10, f"{wood}_fence")
        lamp_post(bp, 0, 1, 11, f"{wood}_fence")
        garden(bp, 14, 0, 9, 20, 12)
        path(bp, [(5, 10), (5, 19)], 0, "dirt_path")
        # small stable
        bp.fill(-1, 1, 12, -1, 3, 18, f"{wood}_fence")
        bp.clear(-1, 1, 13, -1, 3, 17)
        tree(bp, 20, 1, 10, "oak_log", "oak_leaves", 5, 2)
    return build


register(StructureDef(
    "guild_outpost", "overworld", TEMPERATE,
    [Piece("outpost_spruce", guild_outpost("spruce", "dark_oak", "blue"), 2),
     Piece("outpost_oak", guild_outpost("oak", "spruce", "red"), 1),
     Piece("outpost_birch", guild_outpost("birch", "dark_oak", "green"), 1)],
    spacing=28, separation=10, exclusion=("minecraft:villages", 4),
    title_fr="Avant-poste de la Guilde", title_en="Guild Outpost"))



# ============================================================ Mountain monastery
def monastery(bp):
    S = 30
    roof = "deepslate_tile_stairs"
    bp.fill(0, -6, 0, S, -1, S, "stone_bricks", keep=True)
    bp.fill(0, 0, 0, S, 0, S, "stone_bricks")
    wings = [  # (x0, z0, x1, z1, ridge_axis)
        (0, 0, S, 6, "x"),     # north: chapel
        (0, S - 6, S, S, "x"),  # south: gatehouse + kitchen
        (0, 7, 6, S - 7, "z"),  # west: dormitory
        (S - 6, 7, S, S - 7, "z"),  # east: library
    ]
    for x0, z0, x1, z1, ax in wings:
        bp.room(x0, 0, z0, x1, 6, z1, "stone_bricks", floor="spruce_planks", ceiling="spruce_planks")
    for x0, z0, x1, z1, ax in wings:
        bp.gable_roof(x0, z0, x1, z1, 7, roof, ridge_axis=ax, overhang=1, fill="stone_bricks")
    # re-open the walls between wings so the cloister is continuous
    bp.clear(1, 1, 1, S - 1, 5, 5)
    bp.clear(1, 1, S - 5, S - 1, 5, S - 1)
    bp.clear(1, 1, 6, 5, 5, S - 6)
    bp.clear(S - 5, 1, 6, S - 1, 5, S - 6)
    # dividing walls between functional rooms
    bp.fill(1, 1, 6, 5, 5, 6, "stone_bricks")
    bp.fill(S - 5, 1, 6, S - 1, 5, 6, "stone_bricks")
    bp.fill(1, 1, S - 6, 5, 5, S - 6, "stone_bricks")
    bp.fill(S - 5, 1, S - 6, S - 1, 5, S - 6, "stone_bricks")
    for x, z in ((3, 6), (S - 3, 6), (3, S - 6), (S - 3, S - 6)):
        bp.door(x, 1, z, "south", "spruce")
    # log frame columns on the outer walls + tall windows
    for i in range(0, S + 1, 5):
        for (x, z) in ((i, 0), (i, S), (0, i), (S, i)):
            bp.fill(x, 1, z, x, 6, z, "spruce_log[axis=y]")
    for i in range(2, S - 1, 5):
        for (x, z) in ((i + 1, 0), (i + 1, S), (0, i + 1), (S, i + 1)):
            if 0 < x < S or 0 < z < S:
                bp.fill(x, 2, z, x, 4, z, "glass_pane")
    # cloister arcade on the inner faces
    inner = [(x, 6) for x in range(6, S - 5)] + [(x, S - 6) for x in range(6, S - 5)] + \
            [(6, z) for z in range(7, S - 6)] + [(S - 6, z) for z in range(7, S - 6)]
    for (x, z) in inner:
        on_post = (x % 3 == 0) if z in (6, S - 6) else (z % 3 == 0)
        if on_post:
            bp.fill(x, 1, z, x, 4, z, "stone_brick_wall")
            bp.set(x, 1, z, "stone_bricks")
        else:
            bp.clear(x, 1, z, x, 3, z)
            bp.set(x, 4, z, "stone_brick_slab[type=top]")
    # courtyard garden
    bp.fill(7, 0, 7, S - 7, 0, S - 7, "grass_block[snowy=false]")
    path(bp, [(15, 7), (15, S - 7)], 0, "gravel")
    path(bp, [(7, 15), (S - 7, 15)], 0, "gravel")
    bp.disk(15, 0, 15, 3, "stone_bricks")
    bp.disk(15, 1, 15, 3, "stone_brick_wall", hollow=True)
    bp.disk(15, 0, 15, 2, "water")
    bp.fill(15, 1, 15, 15, 2, 15, "chiseled_stone_bricks")
    bp.set(15, 3, 15, "lantern[hanging=false,waterlogged=false]")
    for (x, z) in ((10, 10), (20, 10), (10, 20), (20, 20)):
        tree(bp, x, 1, z, "cherry_log", "cherry_leaves", 4, 2)
    for _ in range(40):
        x, z = bp.rng.randint(8, S - 8), bp.rng.randint(8, S - 8)
        if bp.get(x, 0, z) == "minecraft:grass_block" and not bp.get(x, 1, z):
            bp.set(x, 1, z, bp.rng.choice(["poppy", "azure_bluet", "cornflower", "lily_of_the_valley",
                                           "fern"]))
    # chapel (north wing)
    for x in range(8, S - 7, 3):
        bp.stairs(x, 1, 2, "spruce_stairs", "north")
        bp.stairs(x, 1, 4, "spruce_stairs", "north")
    bp.fill(2, 1, 2, 3, 1, 4, "polished_andesite")
    bp.set(2, 2, 3, "lectern[facing=east,has_book=false,powered=false]")
    for z in (2, 4):
        bp.set(2, 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    for x in range(1, S, 5):
        bp.set(x + 2, 3, 0, "light_blue_stained_glass_pane")
    # bell tower in the north-east corner
    bx, bz = S - 4, 1
    bp.fill(bx - 1, 0, bz - 1, bx + 3, 16, bz + 3, "stone_bricks")
    bp.clear(bx, 1, bz, bx + 2, 15, bz + 2)
    bp.ladder(bx + 1, 1, bz + 2, 15, "north")
    for dy in (12, 13, 14):
        for (x, z) in ((bx + 1, bz - 1), (bx + 1, bz + 3), (bx - 1, bz + 1), (bx + 3, bz + 1)):
            bp.set(x, dy, z, "air")
    bp.set(bx + 1, 15, bz + 1, "spruce_planks")
    bp.set(bx + 1, 14, bz + 1, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.fill(bx, 15, bz, bx + 2, 15, bz + 2, "spruce_planks")
    bp.set(bx + 1, 15, bz + 2, "ladder[facing=north,waterlogged=false]")
    bp.pyramid_roof(bx - 1, bz - 1, bx + 3, bz + 3, 17, roof, overhang=1)
    # dormitory (west wing)
    for z in range(8, S - 8, 3):
        bp.bed(1, 1, z, "east", "white")
    bp.chest(4, 1, 20, "west", LOOT + "monastery")
    # library (east wing)
    bp.bookshelf_wall(S - 1, 1, 8, S - 1, 4, S - 8, chance_empty=0.1)
    for z in range(9, S - 9, 4):
        bp.table(S - 3, 1, z, "spruce_pressure_plate", "spruce_fence")
        bp.chair(S - 4, 1, z, "spruce_stairs", "east")
    bp.set(S - 2, 1, S - 8, "enchanting_table")
    bp.chest(S - 2, 1, 8, "west", LOOT + "monastery_library")
    # gatehouse / kitchen (south wing)
    bp.clear(14, 1, S, 16, 4, S)
    bp.door(14, 1, S, "south", "spruce", hinge="left")
    bp.door(16, 1, S, "south", "spruce", hinge="right")
    bp.set(15, 1, S, "air")
    bp.set(15, 2, S, "air")
    bp.fill(14, 4, S, 16, 4, S, "chiseled_stone_bricks")
    for dx in range(-2, 3):
        bp.stairs(15 + dx, 0, S + 1, "stone_brick_stairs", "north")
    bp.set(3, 1, S - 1, "smoker[facing=north,lit=false]")
    bp.set(4, 1, S - 1, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.barrel(2, 1, S - 1, "up", LOOT + "monastery")
    bp.set(1, 1, S - 1, "composter[level=4]")
    bp.set(10, 1, 14, MOD["waystone"])
    for x in range(S - 5, S):
        bp.barrel(x, 1, S - 1, "north")
    for x, z in ((15, 3), (15, S - 3), (3, 15), (S - 3, 15)):
        bp.lantern(x, 5, z, hanging=True)
    bp.weather({"stone_bricks": ["mossy_stone_bricks", "cracked_stone_bricks"]}, 0.08)


register(StructureDef(
    "mountain_monastery", "overworld",
    ["meadow", "grove", "snowy_slopes", "cherry_grove", "windswept_hills", "windswept_forest",
     "stony_peaks"],
    [Piece("monastery", monastery)], spacing=40, separation=14,
    title_fr="Monastère des cimes", title_en="Mountain Monastery"))



# ============================================================ Forgotten library
def library(bp):
    W, D, H = 28, 16, 12
    bp.fill(0, -4, 0, W, -1, D, "stone_bricks", keep=True)
    bp.room(0, 0, 0, W, H, D, "stone_bricks", floor="dark_oak_planks")
    for x in range(1, W):
        for z in range(1, D):
            if (x + z) % 2 == 0:
                bp.set(x, 0, z, "spruce_planks")
    bp.gable_roof(0, 0, W, D, H + 1, "deepslate_tile_stairs", ridge_axis="x", overhang=1, fill="stone_bricks")
    bp.fill(1, H, 1, W - 1, H, D - 1, "dark_oak_planks")
    # buttresses and tall stained windows
    for x in range(0, W + 1, 4):
        for z, dz in ((0, -1), (D, 1)):
            bp.fill(x, 0, z + dz, x, H - 3, z + dz, "stone_bricks")
            bp.set(x, H - 2, z + dz, f"stone_brick_stairs[facing={'south' if dz < 0 else 'north'},half=bottom]")
            bp.fill(x, 1, z, x, H - 1, z, "chiseled_stone_bricks" if x % 8 == 0 else "stone_bricks")
        if 0 < x < W:
            for z in (0, D):
                bp.fill(x + 2, 2, z, x + 2, H - 3, z, "light_blue_stained_glass_pane")
                bp.set(x + 2, H - 2, z, "stone_bricks")
    # entrance (west)
    bp.clear(0, 1, D // 2 - 1, 0, 4, D // 2 + 1)
    bp.door(0, 1, D // 2 - 1, "west", "dark_oak", hinge="right")
    bp.door(0, 1, D // 2 + 1, "west", "dark_oak", hinge="left")
    bp.fill(0, 1, D // 2, 0, 2, D // 2, "air")
    bp.fill(0, 3, D // 2 - 1, 0, 4, D // 2 + 1, "chiseled_stone_bricks")
    for dz in range(-2, 3):
        bp.stairs(-1, 0, D // 2 + dz, "stone_brick_stairs", "east")
    # mezzanine balconies along the long walls
    my = 6
    for z0, z1 in ((1, 4), (D - 4, D - 1)):
        bp.fill(1, my, z0, W - 1, my, z1, "dark_oak_planks")
        rail_z = z1 + 1 if z0 == 1 else z0 - 1
        for x in range(1, W):
            bp.set(x, my + 1, rail_z, "dark_oak_fence")
            bp.set(x, my, rail_z, "dark_oak_slab[type=top,waterlogged=false]")
        for x in range(3, W - 1, 4):
            bp.fill(x, 1, rail_z, x, my - 1, rail_z, "dark_oak_log[axis=y]")
    # stairs up to the north balcony, along the east wall
    for i in range(my):
        bp.stairs(W - 1, 1 + i, 10 - i, "dark_oak_stairs", "north")
    bp.set(W - 1, my + 1, 5, "air")
    # bookshelf stacks
    for x in range(2, W - 1):
        for z in (1, D - 1):
            for y in range(1, H - 1):
                if y != my and not (x + 2) % 4 == 0:
                    bp.set(x, y, z, "bookshelf" if bp.rng.random() > 0.08 else "chiseled_bookshelf[facing=%s]" %
                           ("south" if z == 1 else "north"))
    for x in range(5, W - 4, 5):
        for z in (6, 10):
            bp.fill(x, 1, z, x + 2, 3, z, "bookshelf")
    # reading tables + lecterns
    for x in range(4, W - 3, 5):
        bp.set(x + 1, 1, 8, "lectern[facing=west,has_book=false,powered=false]")
        bp.chair(x, 1, 8, "dark_oak_stairs", "east")
    # chandeliers
    for x in range(5, W, 7):
        bp.chain(x, H - 3, D // 2, H - 1)
        bp.set(x, H - 4, D // 2, "lantern[hanging=true,waterlogged=false]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + dx, H - 4, D // 2 + dz, "candle[candles=4,lit=true,waterlogged=false]")
            bp.set(x + dx, H - 5, D // 2 + dz, "dark_oak_slab[type=top,waterlogged=false]")
    bp.chest(W - 2, 1, D - 3, "west", LOOT + "library")
    bp.chest(2, my + 1, 2, "east", LOOT + "library")
    # secret study behind the bookshelves at the east end
    bp.room(W, 0, 5, W + 6, 5, 11, "stone_bricks", floor="dark_oak_planks", ceiling="stone_bricks")
    bp.fill(W, 1, 7, W, 2, 7, "bookshelf")  # the 'fake' shelves you break to get in
    bp.set(W + 3, 1, 8, "enchanting_table")
    for z in range(6, 11):
        bp.set(W + 5, 1, z, "bookshelf")
        bp.set(W + 5, 2, z, "bookshelf")
    bp.chest(W + 1, 1, 10, "east", LOOT + "library_secret")
    bp.lantern(W + 3, 4, 8, hanging=True)
    bp.set(W + 1, 1, 6, "cobweb")
    bp.spawner(W // 2, 1, D // 2, MOB["map_wraith"])


register(StructureDef(
    "forgotten_library", "overworld",
    ["forest", "birch_forest", "dark_forest", "flower_forest", "old_growth_birch_forest", "taiga",
     "plains"],
    [Piece("library", library)], spacing=34, separation=12,
    title_fr="Bibliothèque oubliée", title_en="Forgotten Library"))



# ============================================================ Coastal lighthouse
def lighthouse(bp):
    bp.blob(0, -1, 0, 9, 4, 9, "andesite", noise=0.5, half="bottom")
    bp.blob(0, 0, 0, 8, 2, 8, "stone", noise=0.5, half="bottom")
    bp.disk(0, 0, 0, 5, "stone_bricks")
    r, h = 4, 26
    bp.cylinder(0, 1, 0, h, r, "white_concrete")
    for y in range(1, h + 1):
        if (y // 4) % 2 == 1:
            bp.disk(0, y, 0, r, "red_concrete", hollow=True)
    bp.disk(0, 1, 0, r - 1, "air")
    # spiral stair made of slabs around a central column
    bp.fill(0, 1, 0, 0, h, 0, "stone_bricks")
    ring = [(2, -2), (2, -1), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (-1, 2), (-2, 2), (-2, 1),
            (-2, 0), (-2, -1), (-2, -2), (-1, -2), (0, -2), (1, -2)]
    i = 0
    for y in range(1, h - 3):
        for half in ("bottom", "top"):
            x, z = ring[i % len(ring)]
            bp.slab(x, y, z, "stone_brick_slab", half)
            i += 1
    bp.ladder(0, h - 6, -1, h + 1, "north")  # last stretch up through the gallery floor
    for dy in range(4, h, 6):
        bp.fill(r, dy, 0, r, dy + 1, 0, "glass_pane")
        bp.fill(-r, dy + 3, 0, -r, dy + 4, 0, "glass_pane")
    bp.clear(0, 1, r, 0, 2, r)
    bp.door(0, 1, r, "south", "spruce")
    # gallery + lamp room
    bp.disk(0, h + 1, 0, r + 2, "stone_bricks")
    bp.disk(0, h + 2, 0, r + 2, "iron_bars", hollow=True)
    bp.disk(0, h + 2, 0, r + 1, "air")
    bp.cylinder(0, h + 2, 0, h + 5, r - 1, "glass", hollow=True)
    bp.fill(0, h + 2, 0, 0, h + 4, 0, "sea_lantern")
    bp.set(0, h + 3, 0, "glowstone")
    bp.set(0, h + 1, -1, "ladder[facing=north,waterlogged=false]")
    bp.clear(r - 1, h + 2, 0, r - 1, h + 3, 0)  # step out onto the gallery
    bp.disk(0, h + 6, 0, r, "red_concrete")
    bp.cone_roof(0, h + 7, 0, r - 1, "red_nether_brick_stairs", block="red_nether_bricks",
                 cap="lightning_rod[facing=up,powered=false,waterlogged=false]")
    # keeper's cottage
    timber_house(bp, 7, 0, -4, 9, 7, floors=1, wood="spruce", roof="dark_oak", door_side="south",
                 loot=LOOT + "lighthouse", interior="home")
    bp.bed(13, 1, 0, "west", "light_blue")
    # dock
    for z in range(-12, -5):
        bp.set(-2, 0, z, "spruce_planks")
        bp.set(-1, 0, z, "spruce_planks")
        if z % 3 == 0:
            bp.fill(-3, -4, z, -3, 1, z, "spruce_log[axis=y]")
            bp.fill(0, -4, z, 0, 1, z, "spruce_log[axis=y]")
    bp.lantern(-3, 2, -12)
    bp.barrel(-1, 1, -11, "up", LOOT + "lighthouse")
    bp.set(3, 1, 6, MOD["waystone"])


register(StructureDef(
    "coastal_lighthouse", "overworld", ["beach", "stony_shore", "snowy_beach"],
    [Piece("lighthouse", lighthouse)], spacing=28, separation=10, processors="aging",
    title_fr="Phare côtier", title_en="Coastal Lighthouse"))

