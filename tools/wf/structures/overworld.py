"""Overworld surface structures."""
import math

from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import (LOOT, banner_pole, crate_stack, garden, lamp_post, leaves, palm, path,
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
        bp.set(2, 2, 14, "lodestone")
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


# ============================================================ Ruined watchtower
def watchtower(ruined):
    def build(bp):
        bp.disk(0, -3, 0, 6, "cobblestone")
        bp.disk(0, 0, 0, 6, "stone_bricks")
        round_tower(bp, 0, 0, 0, 4, 22, wall="stone_bricks", floor="spruce_planks", floors_every=6,
                    battlements=True)
        # foundation buttresses
        for dx, dz in ((5, 0), (-5, 0), (0, 5), (0, -5)):
            bp.fill(dx, -4, dz, dx, 3, dz, "cobblestone")
            bp.set(dx, 4, dz, "cobblestone_wall")
        bp.clear(0, 1, 4, 0, 2, 4)
        bp.door(0, 1, 4, "south", "spruce")
        bp.stairs(0, 0, 5, "stone_brick_stairs", "north")
        # floor contents
        bp.chest(2, 7, 1, "west", LOOT + "watchtower")
        bp.set(-2, 7, 1, "spruce_slab[type=bottom,waterlogged=false]")
        bp.bed(-2, 13, -1, "south", "white")
        bp.barrel(2, 13, 0, "up", LOOT + "watchtower")
        bp.set(-1, 19, 1, "cartography_table")
        bp.set(1, 23, 1, "campfire[lit=true,signal_fire=true,waterlogged=false,facing=north]")
        bp.set(1, 22, 1, "hay_block[axis=y]")
        bp.set(-2, 23, -1, "bell[attachment=floor,facing=north,powered=false]")
        if ruined:
            bp.spawner(0, 1, -2, "minecraft:skeleton")
            bp.decay(0.10, protect=("ladder",), region=((-6, 14, -6), (6, 26, 6)))
            bp.weather({"stone_bricks": ["mossy_stone_bricks", "cracked_stone_bricks"]}, 0.3)
            for _ in range(25):
                x, z = bp.rng.randint(-8, 8), bp.rng.randint(-8, 8)
                if math.hypot(x, z) > 5.5:
                    bp.set(x, 0, z, bp.rng.choice(["mossy_cobblestone", "cobblestone", "stone_bricks"]))
                    if bp.rng.random() < 0.3:
                        bp.set(x, 1, z, "mossy_cobblestone")
    return build


register(StructureDef(
    "ruined_watchtower", "overworld",
    ["#minecraft:is_forest", "plains", "#minecraft:is_hill", "#minecraft:is_taiga", "windswept_hills",
     "meadow", "savanna_plateau", "stony_peaks"],
    [Piece("tower_ruined", watchtower(True), 3), Piece("tower_intact", watchtower(False), 1)],
    spacing=24, separation=8, processors="ruin",
    title_fr="Tour de guet en ruine", title_en="Ruined Watchtower"))


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


# ============================================================ Desert oasis + tomb
def oasis(bp):
    bp.disk(0, 0, 0, 13, "sand")
    bp.disk(0, 0, 0, 10, "grass_block[snowy=false]")
    bp.disk(0, -1, 0, 6, "sand")
    bp.disk(0, 0, 0, 6, "water")
    bp.disk(0, -1, 0, 4, "water")
    bp.disk(0, -2, 0, 4, "clay")
    for _ in range(14):
        a = bp.rng.uniform(0, 2 * math.pi)
        r = bp.rng.uniform(6.6, 9.5)
        x, z = round(math.cos(a) * r), round(math.sin(a) * r)
        bp.set(x, 1, z, bp.rng.choice(["fern", "dead_bush", "sugar_cane", "fern"]))
    for (x, z, lean) in ((-8, -4, (1, 0)), (7, -6, (0, 1)), (8, 5, (-1, 0)), (-5, 8, (0, -1))):
        palm(bp, x, 1, z, bp.rng.randint(6, 8), lean)
    for x, z in ((3, 6), (4, 6), (5, 5)):
        bp.set(x, 1, z, "sugar_cane")
        bp.set(x, 2, z, "sugar_cane")
    bp.set(-2, 1, 2, "lily_pad")
    # merchant pavilion
    px, pz = 14, -4
    bp.fill(px, 0, pz, px + 8, 0, pz + 8, "smooth_sandstone")
    for x, z in ((px, pz), (px + 8, pz), (px, pz + 8), (px + 8, pz + 8)):
        bp.fill(x, 1, z, x, 4, z, "cut_sandstone")
        bp.set(x, 1, z, "chiseled_sandstone")
    for x in range(px - 1, px + 10):
        for z in range(pz - 1, pz + 10):
            edge = x in (px - 1, px + 9) or z in (pz - 1, pz + 9)
            bp.set(x, 5, z, "smooth_sandstone_slab[type=bottom,waterlogged=false]" if edge else
                   ("white_wool" if (x + z) % 2 else "orange_wool"))
    bp.set(px + 4, 4, pz + 4, "lantern[hanging=true,waterlogged=false]")
    bp.barrel(px + 1, 1, pz + 7, "up", LOOT + "oasis")
    crate_stack(bp, px + 2, 1, pz + 7)
    bp.set(px + 7, 1, pz + 1, "loom[facing=west]")
    bp.set(px + 7, 1, pz + 2, "orange_carpet")
    bp.set(px + 6, 1, pz + 2, "orange_carpet")
    bp.set(px + 6, 1, pz + 1, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    # the tomb: trapdoor hidden under a carpet in the pavilion corner
    tx, tz = px + 1, pz + 1
    bp.set(tx, 1, tz, "orange_carpet")
    bp.set(tx, 0, tz, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(tx, -12, tz, -1, "south")
    bp.fill(tx - 1, -13, tz - 1, tx + 1, -1, tz - 1, "sandstone")
    bp.set(tx, -13, tz, "sandstone")
    # corridor west toward the burial chamber
    cy = -13
    bp.room(-6, cy, tz - 2, tx + 1, cy + 4, tz + 2, "cut_sandstone", floor="smooth_sandstone",
            ceiling="cut_sandstone")
    bp.ladder(tx, cy + 1, tz, -1, "south")
    for x in range(-5, tx, 3):
        bp.set(x, cy + 2, tz - 2, "chiseled_sandstone")
        bp.set(x, cy + 2, tz + 2, "chiseled_sandstone")
        bp.wall_torch(x, cy + 3, tz - 1, "south")
    # burial chamber
    c0x, c0z = -20, tz - 7
    bp.room(c0x, cy - 1, c0z, -6, cy + 7, c0z + 14, "sandstone", floor="orange_terracotta",
            ceiling="cut_sandstone")
    bp.clear(-6, cy + 1, tz - 1, -6, cy + 3, tz + 1)
    for x in range(c0x + 1, -6):
        for z in range(c0z + 1, c0z + 14):
            if (x + z) % 4 == 0:
                bp.set(x, cy - 1, z, "blue_terracotta")
    for x in (c0x + 3, -9):
        for z in (c0z + 3, c0z + 11):
            bp.fill(x, cy, z, x, cy + 6, z, "cut_sandstone")
            bp.set(x, cy + 3, z, "chiseled_sandstone")
    mx, mz = c0x + 7, c0z + 7
    # sarcophagus
    bp.fill(mx - 1, cy, mz - 2, mx + 1, cy, mz + 2, "chiseled_sandstone")
    bp.fill(mx - 1, cy + 1, mz - 2, mx + 1, cy + 1, mz + 2, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    bp.set(mx, cy + 1, mz - 2, "gold_block")
    bp.chest(mx - 3, cy, mz, "east", LOOT + "desert_tomb")
    bp.chest(mx + 3, cy, mz, "west", LOOT + "desert_tomb")
    bp.spawner(mx, cy, mz + 4, "minecraft:husk")
    bp.set(c0x + 1, cy, c0z + 1, "decorated_pot[facing=south,waterlogged=false,cracked=false]")
    bp.set(c0x + 1, cy, c0z + 13, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    for x, z in ((c0x + 2, c0z + 2), (c0x + 2, c0z + 12), (-8, c0z + 2), (-8, c0z + 12)):
        bp.lantern(x, cy + 5, z, hanging=True)
        bp.chain(x, cy + 6, z, cy + 6)
    # secret archaeology alcove behind the west wall
    bp.clear(c0x - 4, cy, mz - 1, c0x - 1, cy + 2, mz + 1)
    bp.fill(c0x, cy, mz - 1, c0x, cy + 2, mz + 1, "sandstone")
    for z in (mz - 1, mz, mz + 1):
        bp.set(c0x - 4, cy - 1, z, "suspicious_sand", {"LootTable": "minecraft:archaeology/desert_pyramid"})
    bp.chest(c0x - 3, cy, mz, "east", LOOT + "desert_tomb_secret")
    bp.fill(c0x - 5, cy - 1, mz - 2, c0x - 1, cy + 3, mz - 2, "sandstone", keep=True)
    bp.fill(c0x - 5, cy - 1, mz + 2, c0x - 1, cy + 3, mz + 2, "sandstone", keep=True)
    bp.fill(c0x - 5, cy + 3, mz - 1, c0x - 1, cy + 3, mz + 1, "sandstone", keep=True)


register(StructureDef(
    "desert_oasis", "overworld", ["desert"], [Piece("oasis", oasis)],
    spacing=26, separation=9, title_fr="Oasis et tombeau", title_en="Desert Oasis"))


# ============================================================ Sunken temple (ocean floor)
def sunken_temple(bp):
    bp.underwater = True
    R = 12
    bp.fill(-R, -3, -R, R, -1, R, "prismarine_bricks", keep=True)
    bp.fill(-R, 0, -R, R, 0, R, "prismarine_bricks")
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            if (x + z) % 2 == 0 and max(abs(x), abs(z)) < R - 1:
                bp.set(x, 0, z, "dark_prismarine")
    # stepped base
    bp.fill(-R + 2, 1, -R + 2, R - 2, 1, R - 2, "prismarine_bricks")
    bp.fill(-R + 3, 2, -R + 3, R - 3, 2, R - 3, "dark_prismarine")
    # dome
    bp.sphere(0, 3, 0, 8, "prismarine", hollow=True, half="top")
    bp.sphere(0, 3, 0, 7, "water[level=0]", half="top")
    bp.disk(0, 2, 0, 7, "dark_prismarine")
    for a in range(0, 360, 45):
        x = round(math.cos(math.radians(a)) * 8)
        z = round(math.sin(math.radians(a)) * 8)
        bp.set(x, 6, z, "sea_lantern")
    bp.set(0, 11, 0, "sea_lantern")
    # four arched entrances
    for dx, dz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        for k in range(6, 10):
            for w in (-1, 0, 1):
                x = dx * k + (w if dz else 0)
                z = dz * k + (w if dx else 0)
                bp.fill(x, 3, z, x, 5, z, "water[level=0]")
        for w in (-2, 2):
            x = dx * 9 + (w if dz else 0)
            z = dz * 9 + (w if dx else 0)
            bp.fill(x, 3, z, x, 7, z, "dark_prismarine")
            bp.set(x, 8, z, "sea_lantern")
    # corner obelisks
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (R - 2), sz * (R - 2)
            bp.fill(x, 1, z, x, 9, z, "prismarine_bricks")
            bp.set(x, 10, z, "sea_lantern")
            bp.set(x, 11, z, "prismarine_wall")
    # central conduit shrine: the player completes the frame to activate it
    bp.fill(-2, 3, -2, 2, 3, 2, "prismarine_bricks")
    for y in (4, 5, 6):
        for x, z in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            bp.set(x, y, z, "prismarine")
    bp.set(0, 5, 0, "conduit[waterlogged=true]")
    bp.chest(0, 4, 3, "south", LOOT + "sunken_temple")
    bp.chest(0, 4, -3, "north", LOOT + "sunken_temple")
    bp.spawner(5, 3, 5, "minecraft:drowned")
    bp.spawner(-5, 3, -5, "minecraft:drowned")
    # kelp & coral garden around
    for _ in range(60):
        x, z = bp.rng.randint(-R - 4, R + 4), bp.rng.randint(-R - 4, R + 4)
        if max(abs(x), abs(z)) > R:
            h = bp.rng.randint(1, 5)
            for y in range(0, h):
                bp.set(x, y, z, "kelp_plant" if y < h - 1 else "kelp[age=20]")
    for _ in range(30):
        x, z = bp.rng.randint(-R, R), bp.rng.randint(-R, R)
        if max(abs(x), abs(z)) >= R - 1 and not bp.get(x, 1, z):
            bp.set(x, 1, z, bp.rng.choice(["tube_coral", "brain_coral", "fire_coral", "horn_coral"]) +
                   "[waterlogged=true]")
    bp.weather({"prismarine_bricks": ["prismarine", "mossy_cobblestone"]}, 0.06)


register(StructureDef(
    "sunken_temple", "overworld", ["#minecraft:is_ocean"], [Piece("temple", sunken_temple)],
    spacing=30, separation=10, heightmap="OCEAN_FLOOR_WG", adaptation="beard_box", processors="none",
    title_fr="Temple englouti", title_en="Sunken Temple"))


# ============================================================ Swamp witch huts
def stilt_hut(bp, x0, z0, w, d, floor_y, wood, roof, contents):
    x1, z1 = x0 + w - 1, z0 + d - 1
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        bp.fill(x, -5, z, x, floor_y - 1, z, "mangrove_log[axis=y]" if wood == "mangrove" else f"{wood}_log[axis=y]")
    bp.room(x0, floor_y, z0, x1, floor_y + 4, z1, f"{wood}_planks", floor=f"{wood}_planks")
    bp.gable_roof(x0, z0, x1, z1, floor_y + 5, f"{roof}_stairs", ridge_axis="x", overhang=1,
                  fill=f"{wood}_planks")
    bp.fill(x0 + 1, floor_y + 5, z0 + 1, x1 - 1, floor_y + 5, z1 - 1, "air")
    bp.fill(x0 + 2, floor_y + 2, z0, x0 + 2, floor_y + 3, z0, "glass_pane")
    bp.fill(x1 - 2, floor_y + 2, z1, x1 - 2, floor_y + 3, z1, "glass_pane")
    contents(bp, x0, z0, x1, z1, floor_y)


def hang_vines(bp, x0, x1, z0, z1, min_y, count):
    """Drape vines down the outside of walls (vine attaches to the block it hangs from)."""
    tops = {}
    for (x, y, z), b in bp.blocks.items():
        if b[0] != "minecraft:air" and y > tops.get((x, z), -999):
            tops[(x, z)] = y
    for _ in range(count):
        x, z = bp.rng.randint(x0, x1), bp.rng.randint(z0, z1)
        top = tops.get((x, z))
        if top is None or top <= min_y:
            continue
        for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
            if not bp.get(x + dx, top - 1, z + dz):
                attach = {"north": "south", "south": "north", "east": "west", "west": "east"}[d]
                for k in range(1, bp.rng.randint(3, 6)):
                    if bp.get(x + dx, top - k, z + dz):
                        break
                    bp.set(x + dx, top - k, z + dz, f"vine[{attach}=true]")
                break


def witch_huts(bp):
    def brewery(bp, x0, z0, x1, z1, fy):
        bp.set(x0 + 1, fy + 1, z0 + 1, "cauldron")
        bp.set(x0 + 2, fy + 1, z0 + 1, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        bp.set(x1 - 1, fy + 1, z0 + 1, "crafting_table")
        for x in range(x0 + 1, x1):
            bp.set(x, fy + 3, z1 - 1, bp.rng.choice(["potted_red_mushroom", "potted_brown_mushroom",
                                                      "potted_fern", "potted_dead_bush"]))
            bp.set(x, fy + 2, z1 - 1, f"spruce_slab[type=top,waterlogged=false]")
        bp.chest(x1 - 1, fy + 1, z1 - 1, "west", LOOT + "witch_hut")
        bp.lantern((x0 + x1) // 2, fy + 4, (z0 + z1) // 2, hanging=True, soul=True)

    def library(bp, x0, z0, x1, z1, fy):
        bp.bookshelf_wall(x0 + 1, fy + 1, z0 + 1, x1 - 1, fy + 2, z0 + 1, 0.2)
        bp.set(x1 - 1, fy + 1, z1 - 1, "lectern[facing=west,has_book=false,powered=false]")
        bp.bed(x0 + 1, fy + 1, z1 - 2, "south", "purple")
        bp.barrel(x0 + 2, fy + 1, z1 - 1, "up", LOOT + "witch_hut")
        bp.lantern((x0 + x1) // 2, fy + 4, (z0 + z1) // 2, hanging=True, soul=True)
        bp.spawner(x1 - 2, fy - 3, (z0 + z1) // 2, "minecraft:witch")
        bp.fill(x1 - 3, fy - 4, (z0 + z1) // 2 - 1, x1 - 1, fy - 4, (z0 + z1) // 2 + 1, "mud_bricks")

    fy = 3
    stilt_hut(bp, 0, 0, 9, 7, fy, "spruce", "dark_oak", brewery)
    stilt_hut(bp, 14, 4, 8, 7, fy + 1, "mangrove", "mangrove", library)
    # rope bridge
    for x in range(9, 14):
        y = fy if x < 12 else fy + 1
        bp.set(x, y, 4, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x, y, 5, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x, y + 1, 3, "spruce_fence")
        bp.set(x, y + 1, 6, "spruce_fence")
    bp.clear(8, fy + 1, 4, 8, fy + 2, 5)
    bp.clear(14, fy + 2, 5, 14, fy + 3, 6)
    # entrance ladder + dock
    bp.clear(4, fy + 1, 6, 4, fy + 2, 6)
    bp.door(4, fy + 1, 6, "south", "spruce")
    for z in range(7, 12):
        bp.set(4, fy, z, "spruce_planks")
        bp.set(3, fy, z, "spruce_slab[type=top,waterlogged=false]")
        bp.set(5, fy, z, "spruce_slab[type=top,waterlogged=false]")
    for y in range(-3, fy):
        bp.set(4, y, 12, "spruce_log[axis=y]")
        if y >= 0:
            bp.set(4, y, 11, "ladder[facing=north,waterlogged=false]")
    bp.lantern(5, fy + 1, 11)
    # vines and swampy details
    hang_vines(bp, -1, 22, -1, 12, fy, 20)


register(StructureDef(
    "witch_huts", "overworld", ["swamp", "mangrove_swamp"], [Piece("huts", witch_huts)],
    spacing=24, separation=8, adaptation="none", processors="none",
    title_fr="Huttes des sorcières", title_en="Swamp Witch Huts"))


# ============================================================ Giant hollow tree
def giant_tree(log, leaf, wood):
    def build(bp):
        R, H = 4, 30
        L = f"{log}[axis=y]"
        lv = leaves(leaf)
        # roots
        for a in range(0, 360, 40):
            ang = math.radians(a + bp.rng.randint(-10, 10))
            for k in range(R, R + 6):
                x, z = round(math.cos(ang) * k), round(math.sin(ang) * k)
                y = max(0, 2 - (k - R) // 2)
                bp.fill(x, -3, z, x, y, z, L)
        bp.disk(0, 0, 0, R, f"{wood}_planks")
        for y in range(1, H + 1):
            r = R if y < H - 6 else R - 1
            bp.disk(0, y, 0, r - 1, "air")
            bp.disk(0, y, 0, r, L, hollow=True, thickness=1.6)
        # floors with spiral stairs
        floors = (9, 17, 25)
        for fy in floors:
            bp.disk(0, fy, 0, R - 1, f"{wood}_planks")
            bp.clear(-2, fy, -2, -1, fy, -1)
            bp.lantern(0, fy - 1, 0, hanging=True)
        for y in range(1, H - 4):
            seg = (y - 1) % 8
            x, z = [(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (2, -1), (2, 0), (2, 1)][seg] \
                if (y // 8) % 2 == 0 else [(2, 2), (1, 2), (0, 2), (-1, 2), (-2, 2), (-2, 1), (-2, 0), (-2, -1)][seg]
            bp.set(x, y, z, f"{wood}_slab[type=bottom,waterlogged=false]")
        # simpler + reliable: ladder column as well
        bp.ladder(0, 1, -R + 1, H - 4, "south")
        for fy in floors:
            bp.set(0, fy, -R + 1, "ladder[facing=south,waterlogged=false]")
        # door + windows
        bp.clear(0, 1, R, 0, 2, R)
        bp.door(0, 1, R, "south", wood)
        for fy in floors:
            for dx, dz in ((R, 0), (-R, 0), (0, R)):
                bp.fill(dx, fy + 2, dz, dx, fy + 3, dz, "glass_pane")
        # rooms
        bp.chest(2, 1, 1, "west", LOOT + "giant_tree")
        bp.set(-2, 1, 1, "crafting_table")
        bp.bed(2, floors[0] + 1, 0, "south", "green")
        bp.set(-2, floors[0] + 1, 1, "bookshelf")
        bp.barrel(-2, floors[1] + 1, 1, "up", LOOT + "giant_tree")
        bp.set(2, floors[1] + 1, 1, "cartography_table")
        bp.chest(2, floors[2] + 1, 0, "west", LOOT + "giant_tree_top")
        bp.set(-2, floors[2] + 1, 0, "lectern[facing=east,has_book=false,powered=false]")
        # canopy with branches
        top = H
        bp.disk(0, top + 1, 0, R, f"{wood}_planks")
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                if abs(math.hypot(x, z) - R) < 0.6:
                    bp.set(x, top + 2, z, f"{wood}_fence")
        bp.clear(0, top + 1, -R + 1, 0, top + 1, -R + 1)
        bp.set(0, top + 1, -R + 1, "ladder[facing=south,waterlogged=false]")
        for a in range(0, 360, 60):
            ang = math.radians(a + 15)
            ex, ez = round(math.cos(ang) * 11), round(math.sin(ang) * 11)
            ey = top - 4 + bp.rng.randint(-3, 3)
            bp.line((0, top - 8, 0), (ex, ey, ez), f"{log}[axis=y]")
            bp.blob(ex, ey + 2, ez, 5, 3, 5, lv, noise=0.4)
        bp.blob(0, top + 8, 0, 9, 5, 9, lv, noise=0.35)
        bp.clear(-R + 1, top + 2, -R + 1, R - 1, top + 4, R - 1)
        for (x, z) in ((3, 3), (-3, -2), (2, -3)):
            bp.lantern(x, top + 2, z)
    return build


register(StructureDef(
    "giant_tree", "overworld",
    ["forest", "flower_forest", "dark_forest", "old_growth_birch_forest", "birch_forest",
     "old_growth_pine_taiga", "old_growth_spruce_taiga"],
    [Piece("oak", giant_tree("oak_log", "oak_leaves", "oak"), 2),
     Piece("dark_oak", giant_tree("dark_oak_log", "dark_oak_leaves", "dark_oak"), 1)],
    spacing=26, separation=8, processors="none", adaptation="beard_thin",
    title_fr="Arbre-monde creux", title_en="Hollow Giant Tree"))


# ============================================================ Sky island
def sky_island(bp):
    Y = 38
    bp.blob(0, Y, 0, 13, 9, 11, "stone", noise=0.5, half="bottom")
    bp.blob(0, Y - 1, 0, 12, 4, 10, "dirt", noise=0.3, half="bottom")
    tops = {}
    for (x, y, z), b in list(bp.blocks.items()):
        if (x, z) not in tops or y > tops[(x, z)]:
            tops[(x, z)] = y
    for (x, z), y in tops.items():
        bp.set(x, y, z, "grass_block[snowy=false]")
    # ores glittering on the underside
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] == "minecraft:stone" and bp.rng.random() < 0.04:
            bp.set(x, y, z, bp.rng.choice(["iron_ore", "gold_ore", "lapis_ore", "diamond_ore", "amethyst_block"]))
    # ruined shrine
    bp.fill(-4, Y + 1, -4, 4, Y + 1, 4, "quartz_bricks")
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.fill(x, Y + 2, z, x, Y + 2 + bp.rng.randint(3, 6), z, "quartz_pillar[axis=y]")
    bp.fill(-4, Y + 7, -4, 4, Y + 7, -4, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    bp.set(0, Y + 2, 0, "chiseled_quartz_block")
    bp.set(0, Y + 3, 0, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.chest(0, Y + 2, 2, "south", LOOT + "sky_island")
    for x, z in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bp.set(x, Y + 2, z, "end_rod[facing=up]")
    tree(bp, 8, Y + 1, -4, "birch_log", "birch_leaves", 5, 2)
    tree(bp, -8, Y + 1, 3, "oak_log", "oak_leaves", 6, 2)
    bp.disk(6, Y, 5, 2, "water")
    for _ in range(30):
        x, z = bp.rng.randint(-11, 11), bp.rng.randint(-9, 9)
        if tops.get((x, z)) == Y and not bp.get(x, Y + 1, z):
            bp.set(x, Y + 1, z, bp.rng.choice(["oxeye_daisy", "allium", "blue_orchid", "fern"]))
    # glow-berry vines hanging underneath
    bottoms = {}
    for (x, y, z), b in bp.blocks.items():
        if b[0] != "minecraft:air" and ((x, z) not in bottoms or y < bottoms[(x, z)]):
            bottoms[(x, z)] = y
    for (x, z), y in bottoms.items():
        if bp.rng.random() < 0.12:
            n = bp.rng.randint(2, 7)
            for k in range(1, n):
                bp.set(x, y - k, z, "cave_vines_plant[berries=%s]" % ("true" if bp.rng.random() < 0.3 else "false"))
            bp.set(x, y - n, z, "cave_vines[age=25,berries=true]")
    # the way up: a vine-covered stone spire with a ladder
    base = 0
    sx, sz = -9, -7
    bp.fill(sx, base, sz, sx + 1, Y - 3, sz + 1, "mossy_cobblestone")
    bp.ladder(sx + 2, base + 1, sz, Y + 1, "east")
    bp.fill(sx - 1, base, sz - 1, sx + 2, base, sz + 2, "mossy_cobblestone")
    for y in range(base + 1, Y - 2, 3):
        bp.set(sx - 1, y, sz, "vine[east=true]")


register(StructureDef(
    "sky_island", "overworld", ["plains", "meadow", "#minecraft:is_forest", "savanna", "cherry_grove",
                                 "sunflower_plains"],
    [Piece("island", sky_island)], spacing=34, separation=12, adaptation="none", processors="none",
    title_fr="Île céleste", title_en="Sky Island"))


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


register(StructureDef(
    "forgotten_library", "overworld",
    ["forest", "birch_forest", "dark_forest", "flower_forest", "old_growth_birch_forest", "taiga",
     "plains"],
    [Piece("library", library)], spacing=34, separation=12,
    title_fr="Bibliothèque oubliée", title_en="Forgotten Library"))


# ============================================================ Abandoned dwarven mine
def dwarven_mine(bp):
    # surface: headframe over the shaft + workshop shed
    bp.fill(-3, 0, -3, 3, 0, 3, "spruce_planks")
    for x, z in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bp.fill(x, 1, z, x, 12, z, "spruce_log[axis=y]")
    for y in (6, 12):
        for x in range(-2, 3):
            bp.set(x, y, -2, "spruce_log[axis=x]")
            bp.set(x, y, 2, "spruce_log[axis=x]")
        for z in range(-1, 2):
            bp.set(-2, y, z, "spruce_log[axis=z]")
            bp.set(2, y, z, "spruce_log[axis=z]")
    bp.fill(-2, 13, 0, 2, 13, 0, "spruce_log[axis=x]")
    bp.set(0, 14, 0, "grindstone[face=floor,facing=north]")
    bp.chain(0, 4, 0, 12)
    bp.set(0, 3, 0, "iron_block")
    bp.pyramid_roof(-2, -2, 2, 2, 14, "spruce_stairs", overhang=0)
    # shaft
    depth = 32
    bp.clear(-1, -depth, -1, 1, 0, 1)
    for y in range(-depth, 1):
        for x, z in ((-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1), (-1, -2), (0, -2), (1, -2),
                     (-1, 2), (0, 2), (1, 2)):
            bp.set(x, y, z, "spruce_planks" if y % 6 else "spruce_log[axis=y]", keep=True)
    bp.fill(-1, 0, -1, 1, 0, 1, "air")
    bp.ladder(0, -depth + 1, -1, 0, "south")
    bp.fill(-1, 1, 1, 1, 1, 1, "spruce_fence")
    for y in range(-depth + 4, 0, 8):
        bp.lantern(1, y, 1)
        bp.set(1, y - 1, 1, "spruce_slab[type=top,waterlogged=false]")
    # shed
    bp.room(5, 0, -4, 12, 5, 3, "spruce_planks", floor="cobblestone")
    bp.gable_roof(5, -4, 12, 3, 6, "dark_oak_stairs", ridge_axis="x", overhang=1, fill="spruce_planks")
    bp.clear(5, 1, -1, 5, 2, -1)
    bp.door(5, 1, -1, "west", "spruce")
    bp.set(11, 1, -3, "blast_furnace[facing=south,lit=false]")
    bp.set(10, 1, -3, "smithing_table")
    bp.set(9, 1, -3, "anvil[facing=east]")
    bp.chest(11, 1, 2, "north", LOOT + "dwarven_mine")
    bp.barrel(7, 1, 2, "up")
    # underground hall + tunnels
    hy = -depth
    bp.room(-6, hy - 1, -6, 6, hy + 5, 6, "deepslate_bricks", floor="polished_deepslate",
            ceiling="deepslate_tiles")
    bp.clear(-1, hy + 5, -1, 1, hy + 5, 1)
    bp.fill(-1, hy, -2, 1, hy + 4, -2, "spruce_planks")  # backing for the ladder
    bp.ladder(0, hy, -1, hy + 5, "south")
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.fill(x, hy, z, x, hy + 4, z, "spruce_log[axis=y]")
        bp.lantern(x, hy + 4, z + (1 if z < 0 else -1), hanging=True)
    bp.chest(-5, hy, 0, "east", LOOT + "dwarven_mine")
    bp.set(5, hy, -2, "anvil[facing=north]")
    bp.set(5, hy, 2, "blast_furnace[facing=west,lit=false]")
    bp.set(-5, hy, -5, "crafting_table")
    ores = ["iron_ore", "deepslate_iron_ore", "deepslate_gold_ore", "deepslate_redstone_ore",
            "deepslate_lapis_ore", "coal_ore", "deepslate_diamond_ore", "deepslate_emerald_ore"]
    for (dx, dz, axis) in ((1, 0, "x"), (-1, 0, "x"), (0, 1, "z"), (0, -1, "z")):
        length = 22
        for k in range(7, 7 + length):
            cx, cz = dx * k, dz * k
            for w in (-1, 0, 1):
                tx, tz = (cx, cz + w) if axis == "x" else (cx + w, cz)
                bp.clear(tx, hy, tz, tx, hy + 2, tz)
                bp.set(tx, hy - 1, tz, "gravel" if bp.rng.random() < 0.5 else "cobbled_deepslate")
            shape = "east_west" if axis == "x" else "north_south"
            bp.set(cx, hy, cz, f"rail[shape={shape},waterlogged=false]")
            if k % 4 == 0:
                for w in (-1, 1):
                    tx, tz = (cx, cz + w) if axis == "x" else (cx + w, cz)
                    bp.fill(tx, hy, tz, tx, hy + 1, tz, "spruce_fence")
                for w in (-1, 0, 1):
                    tx, tz = (cx, cz + w) if axis == "x" else (cx + w, cz)
                    bp.set(tx, hy + 2, tz, "spruce_planks")
                if k % 8 == 0:
                    tx, tz = (cx, cz - 1) if axis == "x" else (cx - 1, cz)
                    bp.lantern(tx, hy + 1, tz)  # standing on the fence post below
            # ore veins in the walls
            for w in (-2, 2):
                tx, tz = (cx, cz + w) if axis == "x" else (cx + w, cz)
                for y in range(hy, hy + 3):
                    if bp.rng.random() < 0.12:
                        bp.set(tx, y, tz, bp.rng.choice(ores))
            if bp.rng.random() < 0.1:
                tx, tz = (cx, cz + 1) if axis == "x" else (cx + 1, cz)
                bp.set(tx, hy + 2, tz, "cobweb")
        ex, ez = dx * (7 + length), dz * (7 + length)
        toward_hall = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
        bp.chest(ex - dx, hy, ez - dz, toward_hall, LOOT + "dwarven_mine")
    bp.spawner(0, hy, 18, "minecraft:cave_spider")
    bp.spawner(-18, hy, 0, "minecraft:zombie")


register(StructureDef(
    "dwarven_mine", "overworld",
    ["#minecraft:is_mountain", "#minecraft:is_hill", "#minecraft:is_badlands", "windswept_hills",
     "windswept_gravelly_hills", "#minecraft:is_taiga"],
    [Piece("mine", dwarven_mine)], spacing=30, separation=10, adaptation="beard_thin",
    title_fr="Mine naine abandonnée", title_en="Abandoned Dwarven Mine"))


# ============================================================ Bandit camp
def tent(bp, x0, z0, length, color, facing_open="south"):
    """A-frame canvas tent, ridge along z."""
    for z in range(z0, z0 + length):
        bp.set(x0 - 2, 1, z, f"{color}_wool")
        bp.set(x0 + 2, 1, z, f"{color}_wool")
        bp.set(x0 - 1, 2, z, f"{color}_wool")
        bp.set(x0 + 1, 2, z, f"{color}_wool")
        bp.set(x0, 3, z, "spruce_log[axis=z]")
        for x in range(x0 - 1, x0 + 2):
            bp.set(x, 0, z, "brown_wool" if x == x0 else "spruce_planks")
            bp.set(x, 1, z, "air")
        bp.set(x0, 2, z, "air")
    back = z0 + length - 1
    bp.fill(x0 - 1, 1, back, x0 + 1, 1, back, f"{color}_wool")
    bp.set(x0, 2, back, f"{color}_wool")


def bandit_camp(bp):
    R = 15
    # palisade
    for a in range(0, 360, 4):
        x = round(math.cos(math.radians(a)) * R)
        z = round(math.sin(math.radians(a)) * R)
        h = 4 + (abs(x * 7 + z * 3) % 2)
        bp.fill(x, 0, z, x, h, z, "spruce_log[axis=y]")
        bp.set(x, h + 1, z, "spruce_fence")
    bp.clear(-1, 1, R - 1, 1, 4, R + 1)
    for x in (-2, 2):
        bp.fill(x, 1, R, x, 6, R, "stripped_spruce_log[axis=y]")
        bp.set(x, 7, R, "lantern[hanging=false,waterlogged=false]")
    bp.fill(-2, 5, R, 2, 5, R, "spruce_log[axis=x]")
    for x in range(-R + 1, R):
        for z in range(-R + 1, R):
            if math.hypot(x, z) < R - 0.5 and bp.rng.random() < 0.7:
                bp.set(x, 0, z, bp.rng.choice(["coarse_dirt", "dirt_path", "podzol", "gravel"]))
    # central fire pit
    bp.disk(0, 0, 0, 2, "cobblestone")
    bp.set(0, 1, 0, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    for x, z, f in ((-3, 0, "east"), (3, 0, "west"), (0, -3, "south")):
        bp.set(x, 1, z, f"spruce_log[axis={'z' if f in ('east', 'west') else 'x'}]")
    # tents
    tent(bp, -8, -10, 6, "red")
    tent(bp, 0, -12, 6, "brown")
    tent(bp, 8, -10, 6, "red")
    for x in (-8, 8):
        bp.bed(x, 1, -9, "south", "red")
    bp.chest(0, 1, -11, "south", LOOT + "bandit_camp")
    # watch platform
    wx, wz = -9, 6
    for x, z in ((wx, wz), (wx + 3, wz), (wx, wz + 3), (wx + 3, wz + 3)):
        bp.fill(x, 1, z, x, 7, z, "spruce_log[axis=y]")
    bp.fill(wx, 7, wz, wx + 3, 7, wz + 3, "spruce_planks")
    for x in range(wx, wx + 4):
        for z in range(wz, wz + 4):
            if x in (wx, wx + 3) or z in (wz, wz + 3):
                bp.set(x, 8, z, "spruce_fence")
    bp.set(wx + 1, 8, wz + 3, "air")
    bp.fill(wx + 1, 1, wz + 3, wx + 1, 6, wz + 3, "spruce_planks")
    bp.ladder(wx + 1, 1, wz + 4, 7, "south")
    bp.barrel(wx + 2, 8, wz + 1, "up", LOOT + "bandit_camp")
    # prisoner cages
    for cx in (6, 10):
        bp.fill(cx - 1, 0, 5, cx + 1, 0, 7, "cobblestone")
        bp.walls(cx - 1, 1, 5, cx + 1, 3, 7, "iron_bars")
        bp.fill(cx - 1, 4, 5, cx + 1, 4, 7, "spruce_slab[type=bottom,waterlogged=false]")
        bp.set(cx, 1, 6, "air")
    bp.set(6, 1, 6, "cobweb")
    # loot pile, weapon rack, target
    bp.chest(11, 1, -2, "west", LOOT + "bandit_camp")
    crate_stack(bp, 11, 1, -1)
    crate_stack(bp, 12, 1, 0)
    bp.set(12, 1, -2, "hay_block[axis=x]")
    bp.set(-12, 1, -2, "target")
    bp.set(-12, 2, -2, "carved_pumpkin[facing=east]")
    bp.set(-11, 1, 0, "fletching_table")
    bp.set(-11, 1, 1, "grindstone[face=floor,facing=east]")
    bp.spawner(0, -1, 4, "minecraft:pillager")
    bp.set(0, 0, 4, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(4, 1, 3, "white_banner[rotation=4]")


register(StructureDef(
    "bandit_camp", "overworld", ["plains", "savanna", "#minecraft:is_taiga", "sparse_jungle", "meadow"],
    [Piece("camp", bandit_camp)], spacing=26, separation=9, processors="none",
    title_fr="Campement de bandits", title_en="Bandit Camp"))


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


register(StructureDef(
    "coastal_lighthouse", "overworld", ["beach", "stony_shore", "snowy_beach"],
    [Piece("lighthouse", lighthouse)], spacing=28, separation=10, processors="aging",
    title_fr="Phare côtier", title_en="Coastal Lighthouse"))


# ============================================================ Jungle ziggurat
def ziggurat(bp):
    tiers = 6
    base = 14
    bp.fill(-base, -4, -base, base, -1, base, "cobblestone", keep=True)
    y = 0
    for t in range(tiers):
        r = base - t * 2
        bp.fill(-r, y, -r, r, y + 2, r, "stone_bricks")
        bp.fill(-r, y + 2, -r, r, y + 2, r, "mossy_stone_bricks")
        for x in range(-r, r + 1, 4):
            for z in (-r, r):
                bp.set(x, y + 1, z, "chiseled_stone_bricks")
        for z in range(-r, r + 1, 4):
            for x in (-r, r):
                bp.set(x, y + 1, z, "chiseled_stone_bricks")
        y += 3
    top = y
    # grand staircase climbing the south face (one step per block, jutting out in front)
    summit_r = base - (tiers - 1) * 2
    for i in range(top):
        z = summit_r + (top - 1 - i)
        for x in range(-3, 4):
            if abs(x) == 3:
                bp.fill(x, 0, z, x, i + 1, z, "mossy_stone_bricks")
                continue
            bp.fill(x, 0, z, x, i - 1, z, "stone_bricks")
            bp.stairs(x, i, z, "mossy_stone_brick_stairs" if (x + i) % 3 == 0 else "stone_brick_stairs", "north")
            bp.clear(x, i + 1, z, x, i + 4, z)
        if i % 6 == 3:
            for x in (-3, 3):
                bp.set(x, i + 2, z, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    # summit shrine
    r = base - tiers * 2 + 2
    bp.fill(-r, top, -r, r, top, r, "polished_andesite")
    for x, z in ((-r, -r), (r, -r), (-r, r), (r, r)):
        bp.fill(x, top + 1, z, x, top + 5, z, "mossy_stone_bricks")
        bp.set(x, top + 6, z, "jack_o_lantern[facing=south]")
    bp.fill(-r, top + 5, -r, r, top + 5, r, "mossy_stone_brick_slab[type=bottom,waterlogged=false]")
    bp.fill(-r + 1, top + 5, -r + 1, r - 1, top + 5, r - 1, "air")
    bp.set(0, top + 1, 0, "gold_block")
    bp.set(0, top + 2, 0, "emerald_block")
    bp.chest(0, top + 1, -2, "south", LOOT + "ziggurat")
    # inner chamber reached by a shaft from the summit
    cy = 3
    bp.room(-6, cy, -6, 6, cy + 6, 6, "chiseled_stone_bricks", floor="mossy_stone_bricks", ceiling="stone_bricks")
    bp.clear(1, cy + 6, 1, 1, top, 1)
    bp.set(1, top, 1, "mossy_stone_brick_slab[type=bottom,waterlogged=false]")
    bp.fill(1, cy + 1, 0, 1, top - 1, 0, "stone_bricks")
    bp.ladder(1, cy + 1, 1, top - 1, "south")
    bp.set(1, top, 1, "air")
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.fill(x, cy + 1, z, x, cy + 5, z, "mossy_cobblestone")
        bp.wall_torch(x + (1 if x < 0 else -1), cy + 3, z, "east" if x < 0 else "west")
    bp.chest(-5, cy + 1, 0, "east", LOOT + "ziggurat")
    bp.chest(5, cy + 1, 0, "west", LOOT + "ziggurat")
    bp.spawner(0, cy + 1, 4, "minecraft:skeleton")
    bp.set(0, cy + 1, -5, "lodestone")
    # vines, leaves and roots reclaiming the pyramid
    for (x, yy, z), b in list(bp.blocks.items()):
        if b[0].endswith("stone_bricks") and bp.rng.random() < 0.05:
            for d, (dx, dz) in (("south", (0, -1)), ("north", (0, 1)), ("west", (1, 0)), ("east", (-1, 0))):
                if not bp.get(x + dx, yy, z + dz):
                    for k in range(bp.rng.randint(1, 4)):
                        if bp.get(x + dx, yy - k, z + dz):
                            break
                        bp.set(x + dx, yy - k, z + dz, f"vine[{d}=true]")
                    break
    for _ in range(30):
        x, z = bp.rng.randint(-base, base), bp.rng.randint(-base, base)
        tops = [yy for (xx, yy, zz) in bp.blocks if xx == x and zz == z]
        if tops and bp.get(x, max(tops), z) and "stairs" not in bp.get(x, max(tops), z):
            bp.set(x, max(tops) + 1, z, leaves("jungle_leaves"))


register(StructureDef(
    "jungle_ziggurat", "overworld", ["jungle", "sparse_jungle", "bamboo_jungle"],
    [Piece("ziggurat", ziggurat)], spacing=30, separation=10,
    title_fr="Ziggourat de la jungle", title_en="Jungle Ziggurat"))


# ============================================================ Ice observatory
def ice_observatory(bp):
    bp.disk(0, 0, 0, 10, "packed_ice")
    bp.disk(0, 0, 0, 8, "spruce_planks")
    bp.sphere(0, 0, 0, 8, "snow_block", hollow=True, half="top")
    bp.sphere(0, 0, 0, 7, "air", half="top")
    bp.disk(0, 0, 0, 7, "spruce_planks")
    # ice ribs on the dome
    for a in range(0, 360, 45):
        for t in range(0, 90, 6):
            x = round(math.cos(math.radians(a)) * math.cos(math.radians(t)) * 8.4)
            z = round(math.sin(math.radians(a)) * math.cos(math.radians(t)) * 8.4)
            y = round(math.sin(math.radians(t)) * 8.4)
            if y >= 1:
                bp.set(x, y, z, "blue_ice")
    # opening slit for the telescope (north)
    for y in range(4, 9):
        for x in (-1, 0, 1):
            for z in range(-9, -3):
                if bp.get(x, y, z) in ("minecraft:snow_block", "minecraft:blue_ice"):
                    bp.set(x, y, z, "air")
    # telescope: tilted tube of copper with a glass lens
    bp.fill(-1, 1, -1, 1, 1, 1, "polished_deepslate")
    bp.fill(0, 2, 0, 0, 3, 0, "polished_deepslate_wall")
    tube = [(0, 4, 0), (0, 5, -1), (0, 6, -2), (0, 7, -3), (0, 7, -4)]
    for p in tube:
        bp.set(*p, "cut_copper")
    bp.set(0, 7, -5, "tinted_glass")
    bp.set(0, 4, 1, "lever[face=floor,facing=north,powered=false]")
    # interior
    bp.set(5, 1, 2, "cartography_table")
    bp.set(5, 1, 3, "lectern[facing=west,has_book=false,powered=false]")
    bp.bed(-5, 1, 2, "south", "light_blue")
    bp.chest(-5, 1, -2, "east", LOOT + "ice_observatory")
    bp.set(-4, 1, -4, "furnace[facing=east,lit=false]")
    bp.set(4, 1, -4, "crafting_table")
    bp.set(0, 1, 5, "white_carpet")
    for x in (-1, 1):
        bp.set(x, 1, 5, "white_carpet")
    bp.lantern(3, 1, -3)
    bp.lantern(-3, 1, 3)
    # entrance tunnel (south)
    for z in range(7, 12):
        for x in (-2, 2):
            bp.fill(x, 1, z, x, 3, z, "snow_block")
        bp.fill(-1, 4, z, 1, 4, z, "snow_block")
        bp.clear(-1, 1, z, 1, 3, z)
        bp.fill(-1, 0, z, 1, 0, z, "packed_ice")
    bp.door(0, 1, 11, "south", "spruce")
    bp.set(-1, 1, 11, "snow_block")
    bp.set(1, 1, 11, "snow_block")
    bp.fill(-1, 2, 11, 1, 3, 11, "snow_block")
    bp.set(0, 2, 11, "spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    # basement laboratory through a trapdoor
    bp.set(3, 0, 0, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.room(-4, -7, -4, 6, -1, 4, "packed_ice", floor="blue_ice", ceiling="spruce_planks")
    bp.set(3, 0, 0, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.fill(3, -6, -1, 3, -1, -1, "packed_ice")
    bp.ladder(3, -6, 0, -1, "south")
    bp.bookshelf_wall(-3, -6, -3, 5, -5, -3, 0.15)
    bp.set(-3, -6, 3, "brewing_stand[has_bottle_0=false,has_bottle_1=true,has_bottle_2=false]")
    bp.set(-2, -6, 3, "cauldron")
    bp.chest(5, -6, 3, "west", LOOT + "ice_observatory_lab")
    bp.lantern(0, -2, 0, hanging=True)
    bp.spawner(-2, -6, 0, "minecraft:stray")


register(StructureDef(
    "ice_observatory", "overworld",
    ["snowy_plains", "ice_spikes", "snowy_taiga", "grove", "snowy_slopes", "frozen_peaks"],
    [Piece("observatory", ice_observatory)], spacing=28, separation=9, processors="none",
    title_fr="Observatoire polaire", title_en="Ice Observatory"))


# ============================================================ Rune circle
def rune_circle(bp):
    R = 11
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = round(math.cos(a) * R), round(math.sin(a) * R)
        h = bp.rng.randint(4, 6)
        bp.fill(x, -2, z, x, h, z, "stone")
        # thicken the menhir towards the centre line
        nx, nz = (1 if x < 0 else -1 if x > 0 else 0), (1 if z < 0 else -1 if z > 0 else 0)
        bp.fill(x + nx, -1, z, x + nx, h - 2, z, "cobblestone")
        bp.set(x, h - 2, z, "chiseled_stone_bricks")
        if bp.rng.random() < 0.5:
            bp.set(x, h + 1, z, "mossy_cobblestone")
        if i % 3 == 0:
            bp.set(x, 1, z + (1 if z <= 0 else -1), "candle[candles=2,lit=false,waterlogged=false]")
    # lintels on alternate pairs
    for i in range(0, n, 4):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0 = (round(math.cos(a0) * R), round(math.sin(a0) * R))
        p1 = (round(math.cos(a1) * R), round(math.sin(a1) * R))
        bp.line((p0[0], 6, p0[1]), (p1[0], 6, p1[1]), "stone_bricks")
    bp.weather({"stone": ["mossy_cobblestone", "andesite", "cobblestone"],
                "cobblestone": ["mossy_cobblestone"]}, 0.35)
    # inner ring path and altar
    bp.disk(0, 0, 0, R - 3, "grass_block[snowy=false]")
    for a in range(0, 360, 6):
        x, z = round(math.cos(math.radians(a)) * (R - 3)), round(math.sin(math.radians(a)) * (R - 3))
        bp.set(x, 0, z, "mossy_cobblestone" if a % 12 else "gravel")
    bp.fill(-1, 0, -1, 1, 0, 1, "chiseled_stone_bricks")
    bp.fill(-1, 1, -1, 1, 1, 1, "stone_brick_slab[type=bottom,waterlogged=false]")
    bp.set(0, 1, 0, "lodestone")
    bp.set(0, 2, 0, "amethyst_cluster[facing=up,waterlogged=false]")
    for x, z in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bp.set(x, 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    # hidden crypt under the altar (break the slab at the altar's east step)
    cy = -9
    bp.room(-5, cy, -4, 5, cy + 5, 4, "deepslate_bricks", floor="deepslate_tiles", ceiling="deepslate_bricks")
    bp.set(2, 0, 0, "stone_brick_slab[type=top,waterlogged=false]")
    bp.fill(2, cy + 1, 0, 2, -1, 0, "air")
    bp.fill(2, cy + 1, 1, 2, -1, 1, "cobbled_deepslate")
    bp.ladder(2, cy + 1, 0, -1, "north")
    for z in (-3, 3):
        bp.fill(-4, cy + 1, z, -2, cy + 1, z, "polished_deepslate")
        bp.set(-3, cy + 2, z, "skeleton_skull[rotation=4]")
    bp.chest(-4, cy + 1, 0, "east", LOOT + "rune_circle")
    bp.spawner(0, cy + 1, 0, "minecraft:zombie")
    bp.lantern(0, cy + 4, 0, hanging=True, soul=True)
    for x in (-4, 4):
        bp.wall_torch(x, cy + 3, -3, "south", soul=True)


register(StructureDef(
    "rune_circle", "overworld",
    ["plains", "meadow", "#minecraft:is_taiga", "windswept_hills", "cherry_grove", "sunflower_plains",
     "snowy_plains"],
    [Piece("circle", rune_circle)], spacing=22, separation=7, processors="none",
    title_fr="Cercle de pierres runiques", title_en="Rune Circle"))


# ============================================================ Galleon wreck
def galleon(bp):
    bp.underwater = True
    L, Wd = 34, 5  # half-width at the widest point
    keel = 0
    deck = 6

    def half_width(z):
        t = z / L
        return max(1, round(Wd * math.sin(math.pi * min(1.0, 0.15 + t * 0.95))))

    for z in range(0, L + 1):
        hw = half_width(z)
        for y in range(keel, deck + 1):
            w = hw if y >= 3 else max(1, hw - (3 - y))  # rounded bilge
            for x in range(-w, w + 1):
                edge = abs(x) == w or y == keel
                bp.set(x, y, z, "dark_oak_planks" if edge else "water[level=0]")
        for x in range(-hw, hw + 1):
            bp.set(x, deck, z, "spruce_planks")
        for x in (-hw, hw):
            bp.set(x, deck + 1, z, "dark_oak_fence")
    # stern castle
    bp.room(-4, deck, 0, 4, deck + 5, 6, "dark_oak_planks", floor="spruce_planks", ceiling="spruce_planks")
    bp.fill(-3, deck + 2, 0, 3, deck + 3, 0, "glass_pane")
    bp.clear(0, deck + 1, 6, 0, deck + 2, 6)
    bp.chest(0, deck + 1, 1, "south", LOOT + "galleon_captain")
    bp.set(-3, deck + 1, 1, "cartography_table")
    bp.bed(3, deck + 1, 2, "south", "red")
    bp.fill(-4, deck + 6, 0, 4, deck + 6, 6, "dark_oak_fence")
    bp.clear(-3, deck + 6, 1, 3, deck + 6, 5)
    bp.fill(-3, deck + 5, 1, 3, deck + 5, 5, "spruce_planks")
    # masts with torn sails
    for mz, mh in ((12, 16), (22, 18), (30, 10)):
        bp.fill(0, keel + 1, mz, 0, deck + mh, mz, "stripped_dark_oak_log[axis=y]")
        for yy in (deck + mh // 2, deck + mh - 2):
            bp.fill(-5, yy, mz, 5, yy, mz, "stripped_dark_oak_log[axis=x]")
            for x in range(-5, 6):
                for k in range(1, 5):
                    if bp.rng.random() < 0.75:
                        bp.set(x, yy - k, mz + 1, "white_wool")
    # break the mid mast & make a hole in the hull
    for y in range(deck + 9, deck + 19):
        bp.remove(0, y, 22)
    bp.line((0, deck + 1, 23), (3, deck + 6, 31), "stripped_dark_oak_log[axis=z]")
    bp.clear(Wd - 1, 1, 14, Wd, 4, 18)
    # cargo holds
    for z in (10, 16, 20, 26):
        bp.barrel(-2, 1, z, "up", LOOT + "galleon_cargo" if z % 20 == 0 else None)
        bp.barrel(2, 1, z, "up")
    bp.chest(0, 1, 18, "north", LOOT + "galleon_cargo")
    bp.fill(-1, deck, 15, 1, deck, 16, "water[level=0]")
    bp.set(0, 1, 25, "gold_block")
    bp.spawner(0, 1, 8, "minecraft:drowned")
    # bowsprit + figurehead
    bp.line((0, deck, L), (0, deck + 4, L + 6), "stripped_dark_oak_log[axis=z]")
    bp.set(0, deck + 1, L + 1, "carved_pumpkin[facing=south]")
    for z in range(-1, L + 2):
        bp.set(0, keel - 1, z, "dark_oak_log[axis=z]")


register(StructureDef(
    "galleon_wreck", "overworld", ["#minecraft:is_ocean", "#minecraft:is_beach"],
    [Piece("galleon", galleon)], spacing=30, separation=10, heightmap="OCEAN_FLOOR_WG",
    adaptation="none", processors="none", title_fr="Épave de galion", title_en="Galleon Wreck"))
