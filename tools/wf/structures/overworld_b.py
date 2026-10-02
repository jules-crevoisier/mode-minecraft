"""Overworld structures (group B)."""
import math

from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import (LOOT, MOB, MOD, banner_pole, crate_stack, garden, lamp_post, leaves, palm, path,
                     round_tower, timber_house, tree)

TEMPERATE = ["#minecraft:is_forest", "plains", "sunflower_plains", "meadow", "#minecraft:is_taiga",
             "savanna", "cherry_grove"]



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
    bp.set(px + 4, 1, pz + 6, MOD["waystone"])
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

