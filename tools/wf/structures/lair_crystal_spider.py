"""Lair of the Crystal Matriarch, under the Crystal Grotto (called from underground.crystal_grotto).

A second, deeper geode lies under the first one: the Matriarch's nest. The way down:

  1. the cutters' branch   an arch on the south side of the old mine tunnel, a short passage with a
                           spider spawner in a webbed alcove
  2. the Crystal Stair     an open spiral stair winding 38 blocks down a round amethyst shaft around a
                           single giant lithite crystal that grows up its whole height
  3. the Brood Hollow      halfway down, a cave off the stair: egg sacs, webs, bones, a cave-spider
                           spawner and a chest
  4. the Last Lantern      the site of grace at the foot of the stair: a waystone among copper lanterns
                           and crystal-cutter's benches, the mist in a pointed amethyst portal
  5. the Nest              a geode (floor radius ~18, 18 high) with a clear calcite floor, webbed edges,
                           glowing egg sacs, eight crystal pillars around the floor, crystal stalactites,
                           and a crystal window in the chasm floor above that lets the nest's glow shine up
  6. the Hoard             a sealed crystal pocket in the west wall (mist on its door), the reward
"""
import math
import random

from ..arch import stair
from ..parts import LOOT, MOD

LC = "wayfarers:lithite_block"
AIR = "minecraft:air"

NC_Y = -42                 # nest geode centre
NF = -44                   # nest floor
NR = (20.0, 17.0, 20.0)    # nest radii (interior edge at 15/16 of these)
ARENA_R = 16
SX, SZ = 30, 12            # Crystal Stair shaft axis
TOP = -6                   # floor of the mine tunnel (the stair starts one below)
RING_IN, RING_OUT = 1.6, 4.6
STRATA = ("calcite", "calcite", "tuff", "dripstone_block", "calcite", "smooth_basalt")
WOOL = ("white_wool", "white_wool", "light_gray_wool")


def nest_r(x, y, z):
    """Pseudo-radius of the nest geode (cavity edge = 15), lumpy like the grotto above."""
    rx, ry, rz = NR
    v = math.sqrt((x / rx) ** 2 + ((y - NC_Y) / ry) ** 2 + (z / rz) ** 2) * 16
    return v + 0.6 * math.sin(x * 0.5 + y * 0.35) + 0.5 * math.cos(z * 0.45 - x * 0.25) + 0.4 * math.sin(y * 0.6 + z * 0.3)


def shell(bp, x0, y0, z0, x1, y1, z1, block="smooth_basalt"):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, block if (x * 3 + y * 7 + z) % 11 else "tuff")


def egg_sac(bp, x, y, z, rng):
    """A spider egg sac: a glowing pearl core wrapped in silk, webs clinging around it."""
    bp.set(x, y, z, "pearlescent_froglight[axis=y]")
    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
        if rng.random() < 0.75 and bp.get(x + dx, y + dy, z + dz) == AIR:
            bp.set(x + dx, y + dy, z + dz, rng.choice(WOOL))
    for dx, dy, dz in ((1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1), (1, 0, 1), (-1, 0, -1), (0, 2, 0)):
        if rng.random() < 0.5 and bp.get(x + dx, y + dy, z + dz) == AIR:
            bp.set(x + dx, y + dy, z + dz, "cobweb")


def grow_crystals(bp, cells, rng, chance=0.3):
    """Amethyst buds and clusters on exposed amethyst faces among `cells`."""
    faces = (("up", 0, 1, 0), ("down", 0, -1, 0), ("north", 0, 0, -1), ("south", 0, 0, 1),
             ("east", 1, 0, 0), ("west", -1, 0, 0))
    for (x, y, z) in cells:
        b = bp.get(x, y, z)
        if b not in ("minecraft:amethyst_block", "minecraft:budding_amethyst") or rng.random() > chance:
            continue
        order = list(faces)
        rng.shuffle(order)
        for face, dx, dy, dz in order:
            if bp.get(x + dx, y + dy, z + dz) == AIR:
                kind = rng.choice(["amethyst_cluster", "large_amethyst_bud", "medium_amethyst_bud", "amethyst_cluster"])
                bp.set(x + dx, y + dy, z + dz, f"{kind}[facing={face},waterlogged=false]")
                break


# ------------------------------------------------------------------ the nest
def nest(bp, rng):
    from .underground import crystal_spire
    cells = []
    for x in range(-25, 26):
        for z in range(-25, 26):
            for y in range(NF - 4, NC_Y + 21):
                r = nest_r(x, y, z)
                if y < NF:
                    if r < 19.0 or math.hypot(x, z) < 22:
                        b = STRATA[(y + 60) % len(STRATA)] if r < 15 else "smooth_basalt"
                        if bp.get(x, y, z) is None:
                            bp.set(x, y, z, b)
                    continue
                if r < 15.0:
                    if y == NF:
                        b = nest_floor(x, z)
                    else:
                        b = "air"
                elif r < 16.6:
                    b = "budding_amethyst" if rng.random() < 0.1 else "amethyst_block"
                    cells.append((x, y, z))
                elif r < 17.6:
                    b = "calcite"
                elif r < 19.0:
                    b = "smooth_basalt"
                else:
                    continue
                if y == NF and r >= 15.0:
                    b = "calcite"
                bp.set(x, y, z, b)
    # eight crystal pillars standing around the floor, two of them broken short; stalactites above
    pillars = [(a, 15.0, LC if i % 2 else "amethyst_block", 18 if i not in (2, 5) else 8)
               for i, a in enumerate((20, 65, 110, 155, 200, 245, 290, 335))]
    for a, rad, blk, ln in pillars:
        px, pz = round(math.cos(math.radians(a)) * rad), round(math.sin(math.radians(a)) * rad)
        lean = (-math.cos(math.radians(a)) * 0.12, 1, -math.sin(math.radians(a)) * 0.12)
        crystal_spire(bp, px, NF, pz, lean, ln, 2.7, blk, tip="amethyst_cluster")
        crystal_spire(bp, px, NF, pz, (math.cos(math.radians(a + 40)) * 0.6, 1, math.sin(math.radians(a + 40)) * 0.6),
                      ln * 0.45, 0.9, "amethyst_block" if blk == LC else LC, tip="amethyst_cluster")
    for a, rad, ln, r0, blk in ((10, 9, 8, 1.6, LC), (80, 6, 6, 1.3, "amethyst_block"), (140, 10, 7, 1.5, LC),
                                (215, 7, 9, 1.8, "amethyst_block"), (280, 10, 6, 1.3, LC), (330, 4, 7, 1.4, "amethyst_block"),
                                (180, 12, 5, 1.1, LC), (40, 13, 5, 1.1, "amethyst_block")):
        px, pz = round(math.cos(math.radians(a)) * rad), round(math.sin(math.radians(a)) * rad)
        for y in range(NC_Y + 18, NF, -1):
            if bp.get(px, y, pz) == AIR:
                crystal_spire(bp, px, y + 1, pz, (0, -1, 0), ln, r0, blk, tip="amethyst_cluster")
                break
    cells += [(x, y, z) for (x, y, z), b in list(bp.blocks.items())
              if -25 <= x <= 25 and -25 <= z <= 25 and NF <= y <= NC_Y + 20 and b[0] == "minecraft:amethyst_block"]
    return cells


def nest_floor(x, z):
    """Calcite floor with rings of smooth basalt and a silk-white star at the heart."""
    d = math.hypot(x, z)
    ang = math.degrees(math.atan2(z, x)) % 360
    spoke = min(ang % 45, 45 - ang % 45) * math.pi / 180 * d < 0.5
    if d < 1.5:
        return "amethyst_block"
    if d < 3.0:
        return "polished_diorite" if spoke else "calcite"
    if 6.5 <= d < 7.4 or 12.5 <= d < 13.4:
        return "smooth_basalt"
    if spoke and d < 12.5:
        return "polished_diorite"
    return "calcite" if (int(d) + int(ang / 30)) % 5 else "polished_tuff"


def nest_dressing(bp, rng):
    """Webbed edges, egg sacs, hanging silk curtains (never in front of the two doors)."""
    def near_door(x, z):
        return (x > 10 and 7 <= z <= 17) or (x < -12 and abs(z) <= 4)
    for x in range(-19, 20):
        for z in range(-19, 20):
            d = math.hypot(x, z)
            if d < 14.2 or near_door(x, z):
                continue
            y = NF + 1
            if bp.get(x, y, z) == AIR and nest_r(x, y, z) < 15 and rng.random() < 0.55:
                bp.set(x, y, z, "cobweb")
                if rng.random() < 0.35 and bp.get(x, y + 1, z) == AIR:
                    bp.set(x, y + 1, z, "cobweb")
    sacs = [(a, r) for a, r in ((5, 16.2), (45, 16.5), (95, 16.0), (130, 16.4), (170, 15.8), (230, 16.3), (265, 16.0),
                                (310, 16.4), (350, 15.9), (195, 15.5))]
    for a, r in sacs:
        x, z = round(math.cos(math.radians(a)) * r), round(math.sin(math.radians(a)) * r)
        if near_door(x, z):
            continue
        egg_sac(bp, x, NF + 1, z, rng)
        if rng.random() < 0.5:
            egg_sac(bp, x + rng.choice((-1, 1)), NF + 3, z + rng.choice((-1, 1)), rng)
    # silk curtains hanging from the vault around the edge
    for k in range(28):
        a = rng.uniform(0, 360)
        r = rng.uniform(12.5, 16.0)
        x, z = round(math.cos(math.radians(a)) * r), round(math.sin(math.radians(a)) * r)
        if near_door(x, z):
            continue
        for y in range(NC_Y + 18, NF + 3, -1):
            if bp.get(x, y, z) == AIR and bp.get(x, y + 1, z) not in (AIR, None):
                for k2 in range(rng.randint(2, 6)):
                    if bp.get(x, y - k2, z) == AIR and y - k2 > NF + 3:
                        bp.set(x, y - k2, z, "cobweb")
                break
    bp.boss_seal(0, NF, 0, "wayfarers:crystal_spider", ARENA_R)


# ------------------------------------------------------------------ the crystal window from the chasm
def chasm_window(bp):
    """A 3x3 crystal shaft from the floor of the grotto's chasm down to the nest's vault, capped by
    purple glass: the nest glows up through the chasm floor."""
    wx, wz = -2, -8
    lowest = None
    for y in range(-12, -24, -1):
        if bp.get(wx, y, wz) == AIR:
            lowest = y
        elif lowest is not None:
            break
    if lowest is None:
        return
    for y in range(lowest - 1, NC_Y, -1):
        if all(bp.get(wx + dx, y, wz + dz) == AIR for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            break   # reached the nest's vault
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                edge = max(abs(dx), abs(dz)) == 2
                if edge:
                    if bp.get(wx + dx, y, wz + dz) in (None, AIR) or y < lowest - 1:
                        bp.set(wx + dx, y, wz + dz, LC if (y + dx + dz) % 4 == 0 else "amethyst_block")
                else:
                    bp.set(wx + dx, y, wz + dz, "purple_stained_glass" if y == lowest - 1 else "air")
    for dx, dz in ((-1, -1), (1, 1), (1, -1), (-1, 1)):
        bp.set(wx + dx, lowest, wz + dz, "amethyst_cluster[facing=up,waterlogged=false]")


# ------------------------------------------------------------------ the cutters' branch and the Crystal Stair
def branch(bp):
    shell(bp, 25, TOP - 2, 2, 33, TOP + 6, 8)
    for x in range(27, 30):
        for z in range(2, 8):
            bp.set(x, TOP, z, "calcite" if (x + z) % 3 else "polished_diorite")
            for y in range(TOP + 1, TOP + 5):
                bp.set(x, y, z, "air")
    for z in range(3, 8):          # copper-framed arch of the old crystal cutters
        for x in (26, 30):
            for y in range(TOP + 1, TOP + 5):
                bp.set(x, y, z, "waxed_oxidized_cut_copper" if z % 2 else "waxed_oxidized_copper_grate")
        for x in range(26, 31):
            bp.set(x, TOP + 5, z, "waxed_chiseled_copper" if z in (3, 7) else "waxed_oxidized_cut_copper")
    bp.set(28, TOP + 4, 4, "waxed_copper_lantern[hanging=true,waterlogged=false]")
    # a webbed alcove in the east wall with the spider spawner
    for z in (5, 6):
        for y in range(TOP + 1, TOP + 3):
            bp.set(30, y, z, "air")
            bp.set(31, y, z, "air")
    bp.spawner(31, TOP + 1, 5, "minecraft:spider")
    bp.set(31, TOP + 2, 6, "cobweb")
    bp.set(30, TOP + 2, 5, "cobweb")
    bp.set(31, TOP + 1, 6, "bone_block[axis=y]")


def sector(x, z):
    """Spiral sector (0..15) of a cell around the shaft axis: 0 points north, clockwise from above."""
    a = (math.degrees(math.atan2(z - SZ, x - SX)) + 90) % 360
    return int(a // 22.5)


def stair_facing(s):
    """Facing of a stair block in sector s: toward the previous (higher) sector."""
    a = math.radians(-90 + (s + 0.5) * 22.5)
    tx, tz = math.sin(a), -math.cos(a)      # tangent pointing back up the spiral (counter-clockwise)
    if abs(tx) >= abs(tz):
        return "east" if tx > 0 else "west"
    return "south" if tz > 0 else "north"


def crystal_stair(bp, rng):
    """An open spiral around a giant lithite crystal: step = block at TOP - 1 - (sector + 16 * turn)."""
    bottom = NF
    cells = []
    for x in range(SX - 8, SX + 9):
        for z in range(SZ - 8, SZ + 9):
            d = math.hypot(x - SX, z - SZ)
            for y in range(bottom - 3, TOP + 6):
                if d <= RING_OUT:
                    if d <= RING_IN - 0.2:
                        b = LC if (y % 7) else "amethyst_block"          # the crystal column
                    elif y < bottom:
                        b = "calcite"
                    elif y == bottom:
                        b = "polished_diorite" if d > 3.5 else "calcite"
                    else:
                        b = "air"
                    if y >= TOP + 5 and d > RING_IN - 0.2:
                        b = "calcite"                                     # the shaft's cap
                    bp.set(x, y, z, b)
                elif d <= RING_OUT + 1.0:
                    if bp.get(x, y, z) is None or bp.get(x, y, z) == "minecraft:smooth_basalt" or y < TOP - 1:
                        b = "budding_amethyst" if rng.random() < 0.08 else "amethyst_block"
                        bp.set(x, y, z, b)
                        cells.append((x, y, z))
                elif d <= RING_OUT + 2.0:
                    if bp.get(x, y, z) is None or y < TOP - 1:
                        bp.set(x, y, z, "calcite")
                elif d <= RING_OUT + 3.0:
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, "smooth_basalt")
    # the steps
    for x in range(SX - 5, SX + 6):
        for z in range(SZ - 5, SZ + 6):
            d = math.hypot(x - SX, z - SZ)
            if not (RING_IN - 0.2 < d <= RING_OUT):
                continue
            s = sector(x, z)
            for turn in range(3):
                y = TOP - 1 - (s + 16 * turn)
                if y < bottom:
                    break
                outer = d > RING_OUT - 0.9
                bp.set(x, y, z, "polished_diorite" if outer else "calcite")
                if y - 1 > bottom:
                    bp.set(x, y - 1, z, "calcite")
    # a crystal balustrade on the inner edge: amethyst clusters on alternate steps
    for x in range(SX - 3, SX + 4):
        for z in range(SZ - 3, SZ + 4):
            d = math.hypot(x - SX, z - SZ)
            if RING_IN - 0.2 < d <= RING_IN + 0.8:
                s = sector(x, z)
                for turn in range(3):
                    y = TOP - 1 - (s + 16 * turn)
                    if y > bottom and s % 2 == 0 and bp.get(x, y + 1, z) == AIR:
                        bp.set(x, y + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
    # copper lanterns hung from the shaft wall every half turn
    for k in range(5):
        s_tot = 4 + k * 8
        s = s_tot % 16
        a = math.radians(-90 + (s + 0.5) * 22.5)
        x, z = SX + round(math.cos(a) * (RING_OUT + 0.5)), SZ + round(math.sin(a) * (RING_OUT + 0.5))
        y = TOP - 1 - s_tot + 4
        if y > bottom + 2:
            bp.set(x, y, z, "waxed_copper_bulb[lit=true,powered=false]")
    grow_crystals(bp, cells, rng, 0.25)
    # the passage from the branch lands on the first step (north)
    for x in range(SX - 1, SX + 2):
        for z in range(SZ - 5, SZ - 3):
            bp.set(x, TOP, z, "calcite")
            for y in range(TOP + 1, TOP + 5):
                bp.set(x, y, z, "air")


# ------------------------------------------------------------------ the Brood Hollow
def brood_hollow(bp, rng):
    """A cave opening east off the stair, where it passes the east side on its second turn."""
    y0 = TOP - 1 - (4 + 16)                # the east step of the second turn
    cx, cz = SX + 9, SZ
    cells = set()
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 6, cz + 7):
            for y in range(y0, y0 + 7):
                v = ((x - cx) / 4.5) ** 2 + ((z - cz) / 5.5) ** 2 + ((y - y0 - 1.5) / 4.0) ** 2
                if v <= 1.0 + 0.12 * math.sin(x * 1.3 + z):
                    cells.add((x, y, z))
    for (x, y, z) in cells:
        bp.set(x, y, z, "air")
    for (x, y, z) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    p = (x + dx, y + dy, z + dz)
                    if p not in cells and bp.get(*p) in (None, "minecraft:smooth_basalt", "minecraft:calcite"):
                        bp.set(*p, "tuff" if (p[0] + p[1]) % 3 else "smooth_basalt")
    for (x, y, z) in cells:                 # flat floor
        if y == y0:
            bp.set(x, y, z, "calcite" if (x + z) % 3 else "tuff")
    # doorway from the stair (x = SX + 4..SX + 6)
    for x in range(SX + 3, cx - 3):
        for z in range(SZ - 1, SZ + 2):
            bp.set(x, y0, z, "calcite")
            for y in range(y0 + 1, y0 + 4):
                bp.set(x, y, z, "air")
    for (x, y, z) in sorted(cells):
        if y == y0 + 1 and rng.random() < 0.18 and x > cx - 3:
            bp.set(x, y, z, "cobweb")
    for (x, z) in ((cx + 2, cz - 3), (cx + 3, cz + 2), (cx - 1, cz + 4), (cx + 1, cz - 5)):
        if (x, y0 + 1, z) in cells:
            egg_sac(bp, x, y0 + 1, z, rng)
    bp.spawner(cx, y0 + 1, cz, "minecraft:cave_spider")
    bp.chest(cx + 3, y0 + 1, cz - 1, "west", LOOT + "crystal_grotto")
    bp.set(cx + 2, y0 + 1, cz + 1, "bone_block[axis=x]")
    bp.set(cx - 2, y0 + 1, cz - 2, "skeleton_skull[rotation=6]")
    bp.set(cx, y0 + 5, cz, "waxed_copper_lantern[hanging=true,waterlogged=false]")


# ------------------------------------------------------------------ the Last Lantern (site of grace)
def grace(bp):
    x0, x1, z0, z1 = 19, 25, 9, 15
    y = NF
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for yy in range(y - 2, y + 7):
                if edge or yy < y or yy == y + 6:
                    bp.set(x, yy, z, "calcite" if (yy + x + z) % 4 else "polished_diorite")
                elif yy == y:
                    bp.set(x, yy, z, "polished_diorite" if (x + z) % 2 else "calcite")
                else:
                    h = 5 if (z0 < z < z1) else 4
                    bp.set(x, yy, z, "air" if yy - y <= h else "calcite")
    # copper pilasters and a coffered copper ceiling
    for x in (x0 - 1, x1 + 1):
        for z in (z0, z1):
            for yy in range(y + 1, y + 6):
                bp.set(x, yy, z, "waxed_oxidized_copper_grate" if yy % 2 else "waxed_oxidized_cut_copper")
    for x in range(x0, x1 + 1):
        bp.set(x, y + 6, (z0 + z1) // 2, "waxed_cut_copper")
    # open to the stair's foot (east) and to the nest portal (west)
    for z in range(z0 + 2, z1 - 1):
        for x in range(x1 + 1, SX - 3):
            bp.set(x, y, z, "calcite")
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
    # the waystone, a crystal lamp, cutters' benches and copper lanterns
    bp.set(x1, y + 1, z1, MOD["waystone"])
    bp.set(x1 - 1, y + 1, z1, "waxed_copper_bulb[lit=true,powered=false]")
    bp.set(x1, y + 1, z1 - 1, LC)
    bp.set(x1, y + 2, z1 - 1, "amethyst_cluster[facing=up,waterlogged=false]")
    for x in (x0 + 1, x0 + 2, x0 + 3):
        bp.set(x, y + 1, z0, stair("polished_diorite_stairs", "north"))
    bp.set(x0 + 4, y + 1, z0, "stonecutter[facing=south]")
    bp.set(x0 + 5, y + 1, z0, "barrel[facing=up,open=false]")
    bp.set(x0 + 5, y + 2, z0, "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(x0 + 1, y + 1, z1, "grindstone[face=floor,facing=north]")
    for (x, z) in ((x0 + 1, z0 + 2), (x1 - 1, z0 + 2), (x0 + 3, z1 - 1)):
        bp.set(x, y + 5, z, "waxed_copper_chain[axis=y,waterlogged=false]")
        bp.set(x, y + 4, z, "waxed_copper_lantern[hanging=true,waterlogged=false]")
    # the pointed amethyst portal into the nest (x 14..18), mist at its mouth
    from .underground import pointed_h
    for x in range(12, x0):
        for z in range(SZ - 3, SZ + 4):
            ph = pointed_h(z - SZ, 2.5, 3)
            for yy in range(y + 1, y + 7):
                inside = ph is not None and yy - y <= ph and abs(z - SZ) <= 2
                if inside:
                    bp.set(x, yy, z, "air")
                elif x >= 15 and bp.get(x, yy, z) in (None, AIR, "minecraft:smooth_basalt", "minecraft:calcite"):
                    bp.set(x, yy, z, "amethyst_block" if abs(z - SZ) == 3 else "calcite")
            if abs(z - SZ) <= 2:
                bp.set(x, y, z, "polished_diorite" if (x + z) % 2 else "calcite")
    for yy in range(y + 1, y + 6):
        for z in (SZ - 3, SZ + 3):
            bp.set(18, yy, z, LC if yy == y + 5 else "amethyst_block")


# ------------------------------------------------------------------ the Hoard
def hoard(bp, rng):
    px, py, pz = -22, NF + 2, 0
    for x in range(px - 5, px + 6):
        for y in range(py - 5, py + 6):
            for z in range(pz - 5, pz + 6):
                d = math.dist((x, y, z), (px, py, pz))
                if y < NF:
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, "smooth_basalt")
                    continue
                if d <= 2.6 and y >= NF + 1:
                    bp.set(x, y, z, "air")
                elif d <= 3.4:
                    bp.set(x, y, z, LC if (x + y + z) % 3 == 0 else "amethyst_block")
                elif d <= 4.2 and bp.get(x, y, z) is None:
                    bp.set(x, y, z, "calcite")
                elif d <= 5.0 and bp.get(x, y, z) is None:
                    bp.set(x, y, z, "smooth_basalt")
    for x in range(px - 2, px + 3):
        for z in range(pz - 2, pz + 3):
            if bp.get(x, NF + 1, z) == AIR or math.hypot(x - px, z - pz) <= 2.2:
                bp.set(x, NF, z, "calcite")
    for x in range(px + 2, -16):           # tunnel from the nest
        for z in (-1, 0, 1):
            bp.set(x, NF, z, "calcite")
            for y in range(NF + 1, NF + 4):
                bp.set(x, y, z, "air")
    bp.chest(px - 1, NF + 1, pz, "east", LOOT + "crystal_grotto")
    bp.chest(px - 1, NF + 1, pz + 1, "east", LOOT + "crystal_grotto")
    bp.set(px - 1, NF + 1, pz - 1, LC)
    bp.set(px - 1, NF + 2, pz - 1, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(px, NF + 1, pz - 2, "bone_block[axis=y]")
    bp.set(px + 1, NF + 1, pz + 2, "skeleton_skull[rotation=10]")
    bp.set(px - 1, NF + 1, pz + 2, "cobweb")


def build(bp):
    """Carve the lair. Call at the very end of crystal_grotto() (after its crystal growth pass)."""
    rng = random.Random(911)
    cells = nest(bp, rng)
    chasm_window(bp)
    hoard(bp, rng)
    branch(bp)
    crystal_stair(bp, rng)
    brood_hollow(bp, rng)
    grace(bp)
    grow_crystals(bp, cells, rng, 0.3)
    nest_dressing(bp, rng)
    bp.mist(16, NF + 1, SZ - 2, 16, NF + 6, SZ + 2)      # the portal from the Last Lantern
    bp.mist(-19, NF + 1, -2, -18, NF + 4, 2)              # the hoard's door
