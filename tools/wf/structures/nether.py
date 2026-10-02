"""Nether structures. The Nether has a roof, so placement uses absolute heights."""
import math

from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD

NETHER = ["#minecraft:is_nether"]


# ============================================================ Basalt fortress
def basalt_fortress(bp):
    S = 26
    bp.fill(0, -6, 0, S, -1, S, "basalt[axis=y]", keep=True)
    bp.fill(0, 0, 0, S, 0, S, "polished_blackstone_bricks")
    # curtain walls with battlements
    bp.walls(0, 1, 0, S, 8, S, "polished_blackstone_bricks")
    bp.clear(1, 1, 1, S - 1, 8, S - 1)
    for i in range(0, S + 1, 2):
        for (x, z) in ((i, 0), (i, S), (0, i), (S, i)):
            bp.set(x, 9, z, "polished_blackstone_brick_wall")
    for i in range(1, S):
        for (x, z) in ((i, 1), (i, S - 1), (1, i), (S - 1, i)):
            bp.set(x, 8, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
    # corner towers
    for cx, cz in ((0, 0), (S, 0), (0, S), (S, S)):
        bp.fill(cx - 2, -4, cz - 2, cx + 2, 13, cz + 2, "polished_basalt[axis=y]")
        bp.clear(cx - 1, 1, cz - 1, cx + 1, 12, cz + 1)
        for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)):
            bp.set(cx + dx, 14, cz + dz, "blackstone_wall")
        bp.fill(cx - 1, 13, cz - 1, cx + 1, 13, cz + 1, "polished_blackstone")
        bp.set(cx, 15, cz, "magma_block")
        bp.set(cx, 16, cz, "fire")
        bp.fill(cx - 2, 4, cz, cx + 2, 5, cz, "iron_bars")
        bp.fill(cx, 4, cz - 2, cx, 5, cz + 2, "iron_bars")
        bp.fill(cx, 4, cz, cx, 5, cz, "air")
    # gatehouse
    g = S // 2
    bp.clear(g - 2, 1, S, g + 2, 6, S)
    bp.fill(g - 3, 1, S + 1, g - 3, 10, S + 1, "polished_basalt[axis=y]")
    bp.fill(g + 3, 1, S + 1, g + 3, 10, S + 1, "polished_basalt[axis=y]")
    bp.fill(g - 3, 7, S, g + 3, 10, S + 1, "polished_blackstone_bricks")
    bp.set(g, 8, S + 1, "gilded_blackstone")
    for x in range(g - 2, g + 3):
        bp.set(x, 6, S, "chain[axis=y,waterlogged=false]")
    # keep in the centre
    k0, k1 = 7, S - 7
    bp.room(k0, 0, k0, k1, 14, k1, "nether_bricks", floor="polished_blackstone", ceiling="nether_bricks")
    bp.fill(k0, 7, k0, k1, 7, k1, "nether_bricks")
    bp.clear(k0 + 1, 7, k0 + 1, k0 + 2, 7, k0 + 2)
    for i in range(6):
        bp.stairs(k0 + 1, 1 + i, k1 - 1 - i, "nether_brick_stairs", "north")
    bp.clear(k0 + 1, 7, k1 - 6, k0 + 1, 7, k1 - 1)
    g2 = (k0 + k1) // 2
    bp.clear(g2 - 1, 1, k1, g2 + 1, 4, k1)
    bp.fill(g2 - 1, 1, k1, g2 + 1, 4, k1, "air")
    for x in (k0, k1):
        for y in (3, 10):
            bp.fill(x, y, g2 - 1, x, y + 1, g2 + 1, "iron_bars")
    bp.chest(g2, 1, k0 + 1, "south", LOOT + "basalt_fortress")
    bp.chest(g2, 8, k0 + 1, "south", LOOT + "basalt_fortress_keep")
    bp.set(g2 - 2, 8, k0 + 1, "gilded_blackstone")
    bp.set(g2 + 2, 8, k0 + 1, "gilded_blackstone")
    bp.spawner(g2, 1, g2, "minecraft:blaze")
    bp.spawner(g2, 8, g2, MOB["basalt_guard"])
    for x, z in ((k0 + 2, k0 + 2), (k1 - 2, k0 + 2), (k0 + 2, k1 - 2), (k1 - 2, k1 - 2)):
        bp.lantern(x, 6, z, hanging=True, soul=True)
        bp.lantern(x, 13, z, hanging=True, soul=True)
    bp.pyramid_roof(k0, k0, k1, k1, 15, "blackstone_stairs", overhang=1)
    # courtyard: lava moat and braziers
    for x in range(2, S - 1):
        for z in range(2, S - 1):
            if (x in (5, S - 5) or z in (5, S - 5)) and k0 - 2 <= x <= k1 + 2 and k0 - 2 <= z <= k1 + 2:
                bp.set(x, 0, z, "lava")
    for x in (g2 - 1, g2, g2 + 1):
        bp.set(x, 0, S - 5, "polished_blackstone_bricks")
    for x, z in ((3, 3), (S - 3, 3), (3, S - 3), (S - 3, S - 3)):
        bp.set(x, 1, z, "soul_campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
        bp.set(x, 0, z, "soul_soil")


register(StructureDef(
    "basalt_fortress", "nether", ["basalt_deltas", "nether_wastes", "soul_sand_valley"],
    [Piece("fortress", basalt_fortress)], spacing=26, separation=9, step="surface_structures",
    adaptation="beard_box", height=("uniform", 34, 62),
    title_fr="Forteresse de basalte", title_en="Basalt Fortress"))


# ============================================================ Chain bridge over the lava sea
def chain_bridge(bp):
    L = 44
    by = 34  # deck height above the template bottom; with start height 8 the deck sits ~y41
    for pz in (0, L):
        bp.blob(0, 0, pz, 5, 6, 5, "basalt[axis=y]", noise=0.4)
        bp.fill(-3, 0, pz - 3, 3, by + 10, pz + 3, "polished_basalt[axis=y]")
        bp.fill(-2, by + 1, pz - 2, 2, by + 9, pz + 2, "air")
        bp.fill(-3, by + 11, pz - 3, 3, by + 11, pz + 3, "polished_blackstone_bricks")
        for dx, dz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            bp.set(dx, by + 12, pz + dz, "blackstone_wall")
            bp.set(dx, by + 13, pz + dz, "soul_lantern[hanging=false,waterlogged=false]")
        bp.fill(-1, by + 1, pz - 3, 1, by + 4, pz + 3, "air")
        bp.fill(-3, by + 1, pz - 1, 3, by + 4, pz + 1, "air")
        bp.fill(-2, by, pz - 2, 2, by, pz + 2, "polished_blackstone")
    # deck
    for z in range(3, L - 2):
        sag = round(3 * math.sin(math.pi * (z - 3) / (L - 6)))
        y = by - sag
        for x in range(-1, 2):
            bp.set(x, y, z, "crimson_planks" if x == 0 else "crimson_slab[type=top,waterlogged=false]")
        bp.set(-2, y + 1, z, "crimson_fence")
        bp.set(2, y + 1, z, "crimson_fence")
        bp.set(-2, y, z, "crimson_slab[type=top,waterlogged=false]")
        bp.set(2, y, z, "crimson_slab[type=top,waterlogged=false]")
        # suspension chains up to the main cables
        cable = by + 10 - round(9 * math.sin(math.pi * (z - 3) / (L - 6)))
        for x in (-2, 2):
            bp.set(x, cable, z, "chain[axis=z,waterlogged=false]")
            if z % 3 == 0:
                for yy in range(y + 2, cable):
                    bp.set(x, yy, z, "chain[axis=y,waterlogged=false]")
        if z % 9 == 0:
            bp.lantern(2, y + 2, z)
    mid = L // 2
    bp.chest(1, by - 3 + 1, mid, "west", LOOT + "chain_bridge")


register(StructureDef(
    "chain_bridge", "nether", ["nether_wastes", "basalt_deltas", "crimson_forest", "soul_sand_valley"],
    [Piece("bridge", chain_bridge)], spacing=22, separation=7, adaptation="none",
    height=("absolute", 8), processors="none",
    title_fr="Pont de chaînes suspendu", title_en="Chain Bridge"))


# ============================================================ Piglin sanctuary (crimson forest)
def piglin_sanctuary(bp):
    R = 12
    bp.disk(0, -1, 0, R + 1, "blackstone")
    bp.disk(0, 0, 0, R, "polished_blackstone_bricks")
    bp.disk(0, 0, 0, R - 3, "crimson_nylium")
    # ring of gilded pillars with gold caps
    for a in range(0, 360, 30):
        x, z = round(math.cos(math.radians(a)) * R), round(math.sin(math.radians(a)) * R)
        bp.fill(x, 1, z, x, 7, z, "polished_blackstone_bricks")
        bp.set(x, 4, z, "gilded_blackstone")
        bp.set(x, 8, z, "gold_block" if a % 60 == 0 else "shroomlight")
    # central golden idol
    bp.fill(-2, 1, -2, 2, 1, 2, "polished_blackstone")
    bp.fill(-1, 2, -1, 1, 2, 1, "gilded_blackstone")
    bp.fill(0, 3, 0, 0, 6, 0, "gold_block")
    bp.set(-1, 5, 0, "gold_block")
    bp.set(1, 5, 0, "gold_block")
    bp.set(0, 7, 0, "piglin_head[rotation=8]")
    for x, z in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bp.set(x, 2, z, "soul_campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    # offering chests and treasure piles
    bp.chest(0, 1, -4, "south", LOOT + "piglin_sanctuary")
    bp.chest(0, 1, 4, "north", LOOT + "piglin_sanctuary")
    for _ in range(14):
        x, z = bp.rng.randint(-R + 4, R - 4), bp.rng.randint(-R + 4, R - 4)
        if 3 < math.hypot(x, z) < R - 3:
            bp.set(x, 1, z, bp.rng.choice(["crimson_fungus", "crimson_roots", "crimson_roots", "gold_block"]))
    # huge fungi framing the shrine
    for (fx, fz) in ((-R - 4, -3), (R + 4, 4)):
        bp.fill(fx, -2, fz, fx, 11, fz, "crimson_stem[axis=y]")
        bp.blob(fx, 13, fz, 5, 3, 5, "nether_wart_block", noise=0.3)
        for _ in range(8):
            bp.set(fx + bp.rng.randint(-4, 4), 11, fz + bp.rng.randint(-4, 4), "shroomlight")
        for _ in range(10):
            vx, vz = fx + bp.rng.randint(-4, 4), fz + bp.rng.randint(-4, 4)
            for k in range(bp.rng.randint(1, 4)):
                bp.set(vx, 10 - k, vz, "weeping_vines_plant" if k < 3 else "weeping_vines[age=20]")
    bp.spawner(6, 1, -6, "minecraft:piglin")


register(StructureDef(
    "piglin_sanctuary", "nether", ["crimson_forest", "nether_wastes"],
    [Piece("sanctuary", piglin_sanctuary)], spacing=24, separation=8, adaptation="beard_box",
    height=("uniform", 32, 70), processors="aging",
    title_fr="Sanctuaire piglin", title_en="Piglin Sanctuary"))


# ============================================================ Lava foundry
def lava_foundry(bp):
    W, D = 24, 18
    bp.fill(0, 0, 0, W, 4, D, "nether_bricks")  # foundations standing in the lava sea
    for x in range(0, W + 1, 6):
        for z in (0, D):
            bp.fill(x, -6, z, x, 0, z, "nether_bricks")
    bp.room(0, 5, 0, W, 14, D, "nether_bricks", floor="polished_blackstone", ceiling="red_nether_bricks")
    bp.gable_roof(0, 0, W, D, 15, "red_nether_brick_stairs", ridge_axis="x", overhang=1, fill="nether_bricks")
    # smelting line: hoppers, furnaces, cauldron of lava
    for x in range(3, W - 2, 3):
        bp.set(x, 6, 3, "blast_furnace[facing=south,lit=true]")
        bp.set(x, 7, 3, "hopper[enabled=true,facing=down]")
        bp.set(x + 1, 6, 3, "lava_cauldron")
    bp.fill(3, 6, D - 3, W - 3, 6, D - 3, "magma_block")
    for x in range(3, W - 2, 4):
        bp.set(x, 7, D - 3, "anvil[facing=east]")
    # molten channel through the hall
    bp.fill(1, 5, D // 2, W - 1, 5, D // 2, "lava")
    for x in range(1, W):
        bp.set(x, 6, D // 2 - 1, "nether_brick_fence")
        bp.set(x, 6, D // 2 + 1, "nether_brick_fence")
    for x in (W // 3, 2 * W // 3):
        bp.fill(x, 5, D // 2, x, 5, D // 2, "polished_blackstone")
        bp.set(x, 6, D // 2 - 1, "air")
        bp.set(x, 6, D // 2 + 1, "air")
    # chimneys
    for x in (4, W - 4):
        bp.fill(x, 15, D // 2 - 4, x + 1, 24, D // 2 - 3, "bricks")
        bp.fill(x, 24, D // 2 - 4, x + 1, 24, D // 2 - 3, "air")
        bp.set(x, 23, D // 2 - 4, "campfire[lit=true,signal_fire=true,waterlogged=false,facing=north]")
    # windows, doors, loot
    for x in range(3, W - 1, 4):
        for z in (0, D):
            bp.fill(x, 8, z, x + 1, 10, z, "iron_bars")
    bp.clear(0, 6, D // 2 - 3, 0, 8, D // 2 - 2)
    bp.clear(W, 6, D // 2 + 2, W, 8, D // 2 + 3)
    bp.chest(W - 1, 6, 1, "west", LOOT + "lava_foundry")
    bp.chest(1, 6, D - 1, "east", LOOT + "lava_foundry")
    bp.fill(W - 3, 6, D - 1, W - 1, 6, D - 1, "gold_block")
    bp.fill(W - 3, 7, D - 1, W - 2, 7, D - 1, "iron_block")
    bp.spawner(W // 2, 6, 5, "minecraft:magma_cube")
    for x in range(4, W, 6):
        bp.lantern(x, 13, D // 2, hanging=True)
    # docks
    for z in (D // 2 - 3, D // 2 - 2):
        for x in range(-6, 0):
            bp.set(x, 5, z, "crimson_planks")
    for z in (D // 2 + 2, D // 2 + 3):
        for x in range(W + 1, W + 7):
            bp.set(x, 5, z, "warped_planks")


register(StructureDef(
    "lava_foundry", "nether", ["nether_wastes", "basalt_deltas", "crimson_forest", "warped_forest"],
    [Piece("foundry", lava_foundry)], spacing=24, separation=8, adaptation="none",
    height=("absolute", 27), processors="aging",
    title_fr="Fonderie de lave", title_en="Lava Foundry"))


# ============================================================ Soul tower (soul sand valley)
def soul_tower(bp):
    r, h = 5, 34
    bp.disk(0, -3, 0, r + 3, "soul_soil")
    bp.disk(0, 0, 0, r + 2, "polished_blackstone_bricks")
    bp.cylinder(0, 1, 0, h, r, "polished_blackstone_bricks")
    for y in range(1, h + 1, 5):
        bp.disk(0, y, 0, r, "chiseled_polished_blackstone", hollow=True)
    # floors with a central soul fire well
    for fy in range(8, h, 8):
        bp.disk(0, fy, 0, r - 1, "polished_blackstone")
        bp.set(0, fy, 0, "soul_soil")
        bp.set(0, fy + 1, 0, "soul_fire")
        bp.fill(r, fy + 2, 0, r, fy + 4, 0, "iron_bars")
        bp.fill(-r, fy + 2, 0, -r, fy + 4, 0, "iron_bars")
        bp.lantern(2, fy + 1, 2, soul=True)
    bp.ladder(0, 1, -r + 1, h, "south")
    for fy in range(8, h, 8):
        bp.set(0, fy, -r + 1, "ladder[facing=south,waterlogged=false]")
    bp.clear(0, 1, r, 0, 2, r)
    bp.set(0, 1, r, "air")
    # top: open crown of blackstone spikes
    bp.disk(0, h + 1, 0, r + 1, "polished_blackstone")
    bp.set(0, h + 1, -r + 1, "ladder[facing=south,waterlogged=false]")
    for a in range(0, 360, 45):
        x, z = round(math.cos(math.radians(a)) * (r + 1)), round(math.sin(math.radians(a)) * (r + 1))
        bp.fill(x, h + 2, z, x, h + 4 + (a // 45) % 3, z, "blackstone_wall")
    bp.chest(1, h + 2, 1, "north", LOOT + "soul_tower")
    bp.chest(2, 9, -2, "west", LOOT + "soul_tower")
    bp.spawner(-2, 17, 2, MOB["basalt_guard"])
    bp.spawner(2, 25, 2, "minecraft:blaze")
    # bone ribs half-buried around the base
    for a in (20, 140, 260):
        cx, cz = round(math.cos(math.radians(a)) * 12), round(math.sin(math.radians(a)) * 12)
        for k in range(-4, 5, 2):
            bp.line((cx + k, -1, cz - 3), (cx + k, 5 - abs(k) // 2, cz), "bone_block[axis=y]")
            bp.line((cx + k, 5 - abs(k) // 2, cz), (cx + k, -1, cz + 3), "bone_block[axis=y]")


register(StructureDef(
    "soul_tower", "nether", ["soul_sand_valley"], [Piece("tower", soul_tower)],
    spacing=22, separation=7, adaptation="beard_box", height=("uniform", 30, 48), processors="aging",
    title_fr="Tour des âmes", title_en="Soul Tower"))


# ============================================================ Piglin market
def piglin_market(bp):
    S = 22
    bp.fill(-S // 2, -2, -S // 2, S // 2, 0, S // 2, "blackstone", keep=True)
    bp.fill(-S // 2, 0, -S // 2, S // 2, 0, S // 2, "polished_blackstone_bricks")
    for x in range(-S // 2, S // 2 + 1):
        for z in range(-S // 2, S // 2 + 1):
            if (x + z) % 2 == 0 and abs(x) < S // 2 and abs(z) < S // 2:
                bp.set(x, 0, z, "gilded_blackstone" if bp.rng.random() < 0.06 else "polished_blackstone")
    # market stalls with crimson/warped awnings
    stalls = [(-7, -7, "crimson"), (0, -8, "warped"), (7, -7, "crimson"), (-7, 7, "warped"), (7, 7, "crimson")]
    for sx, sz, wood in stalls:
        for dx, dz in ((-2, -1), (2, -1), (-2, 1), (2, 1)):
            bp.fill(sx + dx, 1, sz + dz, sx + dx, 3, sz + dz, f"{wood}_fence")
        for dx in range(-3, 4):
            for dz in range(-2, 3):
                bp.set(sx + dx, 4, sz + dz,
                       f"{wood}_slab[type=bottom,waterlogged=false]" if abs(dz) == 2 else
                       ("red_wool" if wood == "crimson" else "cyan_wool"))
        bp.fill(sx - 1, 1, sz, sx + 1, 1, sz, f"{wood}_planks")
        bp.barrel(sx - 1, 2, sz, "up", LOOT + "piglin_market")
        bp.set(sx, 2, sz, "gold_block")
        bp.set(sx + 1, 2, sz, "soul_lantern[hanging=false,waterlogged=false]")
    # central gold fountain (lava)
    bp.disk(0, 0, 0, 3, "gold_block")
    bp.disk(0, 1, 0, 3, "polished_blackstone_brick_wall", hollow=True)
    bp.disk(0, 0, 0, 2, "lava")
    bp.fill(0, 0, 0, 0, 3, 0, "gilded_blackstone")
    bp.set(0, 4, 0, "shroomlight")
    # surrounding archways
    for d, (dx, dz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        cx, cz = dx * (S // 2), dz * (S // 2)
        for w in (-2, 2):
            x, z = cx + (w if dz else 0), cz + (w if dx else 0)
            bp.fill(x, 1, z, x, 6, z, "polished_blackstone_bricks")
        for w in range(-2, 3):
            x, z = cx + (w if dz else 0), cz + (w if dx else 0)
            bp.set(x, 7, z, "polished_blackstone_bricks")
        bp.set(cx, 6, cz, "soul_lantern[hanging=true,waterlogged=false]")
    bp.chest(-2, 1, 4, "north", LOOT + "piglin_market")
    bp.set(0, 1, -6, MOD["waystone"])
    bp.spawner(4, 1, 0, "minecraft:piglin")


register(StructureDef(
    "piglin_market", "nether", ["crimson_forest", "warped_forest", "nether_wastes"],
    [Piece("market", piglin_market)], spacing=24, separation=8, adaptation="beard_box",
    height=("uniform", 32, 64), processors="aging",
    title_fr="Marché piglin", title_en="Piglin Market"))
