"""Overworld structures (group C)."""
import math

from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import (LOOT, MOB, MOD, banner_pole, crate_stack, garden, lamp_post, leaves, palm, path,
                     round_tower, timber_house, tree)

TEMPERATE = ["#minecraft:is_forest", "plains", "sunflower_plains", "meadow", "#minecraft:is_taiga",
             "savanna", "cherry_grove"]



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
            bp.spawner(0, 1, -2, MOB["ruin_walker"])
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
    bp.spawner(-18, hy, 0, MOB["ruin_walker"])


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
    bp.spawner(0, cy + 1, 0, MOB["ruin_walker"])
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
