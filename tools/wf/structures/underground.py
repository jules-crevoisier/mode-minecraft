"""Underground / deep dark structures (placed at fixed depths, encapsulated in rock)."""
import math

from ..defs import Piece, StructureDef, register
from ..parts import LOOT

DEEP = ["#minecraft:is_overworld"]


# ============================================================ Dwarven forge
def dwarven_forge(bp):
    W, D, H = 26, 20, 11
    bp.room(0, 0, 0, W, H, D, "deepslate_bricks", floor="polished_deepslate", ceiling="deepslate_tiles")
    # vaulted ceiling ribs
    for x in range(2, W, 4):
        for z in range(1, D):
            bp.set(x, H - 1, z, "polished_deepslate")
        bp.fill(x, 1, 1, x, H - 1, 1, "deepslate_tile_wall")
        bp.fill(x, 1, D - 1, x, H - 1, D - 1, "deepslate_tile_wall")
    # great forge: lava channel with anvils and blast furnaces
    bp.fill(3, 0, 8, W - 3, 0, 12, "polished_blackstone_bricks")
    bp.fill(4, 0, 10, W - 4, 0, 10, "lava")
    for x in range(4, W - 3):
        bp.set(x, 1, 9, "polished_blackstone_brick_wall")
        bp.set(x, 1, 11, "polished_blackstone_brick_wall")
    for x in range(5, W - 4, 4):
        bp.set(x, 1, 7, "anvil[facing=east]")
        bp.set(x + 1, 1, 7, "blast_furnace[facing=north,lit=true]")
        bp.set(x, 1, 13, "smithing_table")
        bp.set(x + 1, 1, 13, "grindstone[face=floor,facing=north]")
    # huge chimney hood over the forge
    bp.fill(3, H - 3, 8, W - 3, H - 3, 12, "polished_blackstone_bricks")
    bp.fill(4, H - 2, 9, W - 4, H, 11, "polished_blackstone_bricks")
    bp.fill(5, H - 3, 10, W - 5, H, 10, "air")
    bp.fill(5, H + 1, 10, 5, H + 8, 10, "air")
    # dwarven statue (two-tone, holding a hammer)
    sx, sz = W // 2, 3
    bp.fill(sx - 1, 1, sz - 1, sx + 1, 1, sz + 1, "polished_deepslate")
    bp.fill(sx, 2, sz, sx, 3, sz, "deepslate_tiles")
    bp.fill(sx - 1, 4, sz, sx + 1, 5, sz, "deepslate_bricks")
    bp.set(sx, 6, sz, "chiseled_deepslate")
    bp.set(sx - 2, 5, sz, "iron_block")
    bp.set(sx - 2, 4, sz, "polished_deepslate_wall")
    bp.set(sx, 6, sz + 1, "gold_block")
    # vault and dormitory
    bp.room(W, 0, 4, W + 8, 6, 16, "deepslate_bricks", floor="deepslate_tiles", ceiling="deepslate_bricks")
    bp.clear(W, 1, 9, W, 3, 11)
    bp.fill(W, 1, 10, W, 3, 10, "iron_bars")
    bp.set(W, 1, 10, "iron_door[facing=east,half=lower,hinge=left,open=false,powered=false]")
    bp.set(W, 2, 10, "iron_door[facing=east,half=upper,hinge=left,open=false,powered=false]")
    bp.set(W - 1, 2, 9, "stone_button[face=wall,facing=west,powered=false]")
    for z in (6, 8, 12, 14):
        bp.chest(W + 7, 1, z, "west", LOOT + "dwarven_vault")
    bp.fill(W + 2, 1, 5, W + 5, 1, 5, "raw_iron_block")
    bp.fill(W + 2, 1, 15, W + 5, 1, 15, "raw_gold_block")
    bp.set(W + 4, 1, 10, "raw_copper_block")
    bp.lantern(W + 4, 5, 10, hanging=True)
    # dormitory (west)
    bp.room(-9, 0, 4, 0, 6, 16, "deepslate_bricks", floor="spruce_planks", ceiling="deepslate_bricks")
    bp.clear(0, 1, 9, 0, 3, 11)
    for z in (5, 8, 12):
        bp.bed(-8, 1, z, "east", "brown")
    bp.barrel(-1, 1, 15, "up", LOOT + "dwarven_mine")
    bp.barrel(-1, 1, 5, "up")
    bp.set(-8, 1, 15, "crafting_table")
    bp.lantern(-4, 5, 10, hanging=True)
    # lighting
    for x in range(4, W, 6):
        for z in (3, D - 3):
            bp.lantern(x, H - 2, z, hanging=True)
            bp.chain(x, H - 1, z, H - 1)
    bp.spawner(W // 2, 1, D - 3, "minecraft:zombie")
    # exit tunnels into the caves
    for x in (6, W - 6):
        bp.clear(x - 1, 1, -7, x + 1, 3, 0)
        bp.fill(x - 1, 0, -7, x + 1, 0, -1, "cobbled_deepslate")
        bp.lantern(x, 1, -6)


register(StructureDef(
    "dwarven_forge", "overworld", DEEP, [Piece("forge", dwarven_forge)],
    spacing=30, separation=10, step="underground_structures", adaptation="encapsulate",
    height=("uniform", -48, -12), title_fr="Forge naine", title_en="Dwarven Forge"))


# ============================================================ Crystal grotto
def crystal_grotto(bp):
    R = 13
    # geode shell: smooth basalt > calcite > amethyst, carved out inside
    bp.sphere(0, 0, 0, R, "smooth_basalt")
    bp.sphere(0, 0, 0, R - 1, "calcite")
    bp.sphere(0, 0, 0, R - 2, "amethyst_block")
    bp.sphere(0, 0, 0, R - 3, "air")
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] == "minecraft:amethyst_block" and bp.rng.random() < 0.12:
            bp.set(x, y, z, "budding_amethyst")
    # crystals growing inward
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] != "minecraft:amethyst_block" or bp.rng.random() > 0.25:
            continue
        for face, (dx, dy, dz) in (("up", (0, 1, 0)), ("down", (0, -1, 0)), ("north", (0, 0, -1)),
                                   ("south", (0, 0, 1)), ("east", (1, 0, 0)), ("west", (-1, 0, 0))):
            if bp.get(x + dx, y + dy, z + dz) == "minecraft:air":
                kind = bp.rng.choice(["amethyst_cluster", "large_amethyst_bud", "medium_amethyst_bud"])
                bp.set(x + dx, y + dy, z + dz, f"{kind}[facing={face},waterlogged=false]")
                break
    # crystal-cutter's workshop on a calcite terrace
    fy = -6
    bp.disk(0, fy, 0, 8, "calcite")
    bp.disk(0, fy - 1, 0, 7, "calcite")
    for x in range(-8, 9):
        for z in range(-8, 9):
            if math.hypot(x, z) <= 8.35 and bp.get(x, fy + 1, z) and "amethyst" in bp.get(x, fy + 1, z):
                bp.set(x, fy + 1, z, "air")
    bp.set(0, fy + 1, 0, "stonecutter[facing=north]")
    bp.set(2, fy + 1, -1, "grindstone[face=floor,facing=west]")
    bp.set(-2, fy + 1, -1, "cartography_table")
    bp.chest(0, fy + 1, 3, "north", LOOT + "crystal_grotto")
    bp.set(-3, fy + 1, 3, "tinted_glass")
    bp.set(3, fy + 1, 3, "tinted_glass")
    bp.lantern(-3, fy + 2, 3)
    bp.lantern(3, fy + 2, 3)
    bp.set(0, fy + 1, -4, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # pillars of copper
    for x, z in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        for y in range(fy + 1, R):
            if bp.get(x, y, z) not in (None, "minecraft:air") and y > fy + 2:
                break
            bp.set(x, y, z, "oxidized_cut_copper" if (y % 3) else "waxed_copper_block")
    # a tunnel out
    for k in range(R - 3, R + 6):
        bp.clear(k, fy + 1, -1, k, fy + 3, 1)
        bp.fill(k, fy, -1, k, fy, 1, "calcite")
    bp.spawner(-4, fy + 1, -2, "minecraft:silverfish")


register(StructureDef(
    "crystal_grotto", "overworld", DEEP, [Piece("grotto", crystal_grotto)],
    spacing=26, separation=8, step="underground_structures", adaptation="none",
    height=("uniform", -40, 10), processors="none",
    title_fr="Grotte de cristal", title_en="Crystal Grotto"))


# ============================================================ Sealed laboratory (deep dark)
def sealed_lab(bp):
    W, D, H = 22, 18, 8
    bp.room(0, 0, 0, W, H, D, "deepslate_tiles",
            floor="polished_deepslate", ceiling="deepslate_tiles")
    bp.walls(0, 1, 0, W, 1, D, "polished_deepslate")
    # glass containment cells
    for i, x in enumerate(range(2, W - 2, 5)):
        bp.walls(x, 1, 1, x + 3, 4, 4, "tinted_glass")
        bp.clear(x + 1, 1, 2, x + 2, 3, 3)
        bp.set(x + 1, 1, 4, "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
        bp.set(x + 1, 2, 4, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
        bp.set(x + 1, 1, 5, "polished_blackstone_pressure_plate[powered=false]")
        bp.set(x + 2, 1, 2, ["sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]",
                             "sculk_catalyst[bloom=false]", "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]",
                             "sculk"][i % 4])
    # central console
    bp.fill(8, 1, 9, 13, 1, 10, "polished_blackstone")
    bp.set(9, 2, 9, "redstone_lamp[lit=false]")
    bp.set(10, 2, 9, "lever[face=floor,facing=south,powered=false]")
    bp.set(11, 2, 9, "comparator[facing=south,mode=compare,powered=false]")
    bp.set(12, 2, 9, "redstone_lamp[lit=false]")
    bp.set(10, 2, 10, "lectern[facing=north,has_book=false,powered=false]")
    # archive + loot
    bp.bookshelf_wall(1, 1, D - 1, W - 1, 3, D - 1, 0.3)
    bp.chest(2, 1, D - 2, "north", LOOT + "sealed_lab")
    bp.chest(W - 2, 1, D - 2, "north", LOOT + "sealed_lab")
    bp.set(W - 2, 1, 9, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    bp.set(W - 2, 1, 10, "cauldron")
    # sculk creeping in from cracks
    for (x, y, z), b in list(bp.blocks.items()):
        if y == 0 and bp.rng.random() < 0.18 and 0 < x < W and 0 < z < D:
            bp.set(x, y, z, "sculk")
            if bp.get(x, 1, z) == "minecraft:air" and bp.rng.random() < 0.1:
                bp.set(x, 1, z, "sculk_vein[down=true,up=false,north=false,south=false,east=false,"
                                "west=false,waterlogged=false]")
    for x in range(3, W, 6):
        for z in (7, 12):
            bp.set(x, H - 1, z, "ochre_froglight[axis=y]" if (x + z) % 2 else "verdant_froglight[axis=y]")
    # sealed blast door + corridor out
    bp.clear(W, 1, 8, W + 8, 4, 10)
    bp.fill(W, 0, 7, W + 8, 0, 11, "polished_deepslate")
    bp.fill(W + 1, 1, 7, W + 8, 5, 7, "deepslate_tiles")
    bp.fill(W + 1, 1, 11, W + 8, 5, 11, "deepslate_tiles")
    bp.fill(W + 1, 5, 8, W + 8, 5, 10, "deepslate_tiles")
    bp.fill(W, 1, 8, W, 4, 10, "iron_bars")
    bp.set(W, 1, 9, "air")
    bp.set(W, 2, 9, "air")
    bp.spawner(5, 1, 12, "minecraft:zombie")


register(StructureDef(
    "sealed_lab", "overworld", ["deep_dark", "dripstone_caves", "lush_caves"],
    [Piece("lab", sealed_lab)], spacing=28, separation=9, step="underground_structures",
    adaptation="encapsulate", height=("uniform", -52, -20),
    title_fr="Laboratoire scellé", title_en="Sealed Laboratory"))
