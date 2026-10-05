"""Lair of the Forge King, under the Dwarven Forge (called from underground.dwarven_forge).

The descent, from the great hall down to the King's Crucible (about 38 blocks below the hall floor):

  1. the King's Stair     a balustraded stairwell opening in the nave floor (east of the rune medallion),
                          guarded by the hall's spawner, plunging west under the medallion
  2. the Molten Gallery   a long gallery along a lava channel fed by lava falls from wall slits; a magma
                          cube nest in a wall alcove, a supply barrel
  3. the Ancestors' Hall  a processional stair descending west under the gate cavern between eight
                          dwarven ancestor statues standing in tall niches, the vault rising as it goes
  4. the Forge-fathers' crypt  stone coffins, urns, a ruin-walker spawner
  5. the Collapsed Way    a narrow stair back east under everything, half-buried by a cave-in
  6. the Last Anvil       the site of grace: a waystone, benches, a brazier, an anvil, the mist-filled portal
  7. the King's Crucible  a round domed forge-arena (radius 14), lava running in a channel at the very
                          edge, eight great pilasters with ember lamps, chimneys of light in the dome and
                          a central oculus of glowing lithite over the seal; the throne and its anvils in
                          an apse to the east, the treasury behind the throne (mist on that door too)
"""
import math

from ..arch import Palette, stair
from ..parts import LOOT, MOB, MOD

LB = "brasshaven:lithite_bricks"
LC = "brasshaven:lithite_block"
GT = "brasshaven:gilded_trim"
PB = "polished_blackstone_bricks"
PBS = "polished_blackstone_brick_stairs"
PBW = "polished_blackstone_brick_wall"
PBSL = "polished_blackstone_brick_slab"
AIR = "minecraft:air"

DEEP_WALL = Palette({"deepslate_bricks": 5, "deepslate_tiles": 3, "cracked_deepslate_bricks": 2, LB: 1},
                    seed=141, scale=1.6)
DEEP_ROCK = Palette({"deepslate": 6, "cobbled_deepslate": 2, "tuff": 2, "smooth_basalt": 1}, seed=142, scale=3)
CRUCIBLE = Palette({PB: 6, "polished_blackstone": 2, "cracked_polished_blackstone_bricks": 1}, seed=143, scale=1.4)

# the arena
AX, AZ, AY, AR = 34, 0, -38, 14
DRUM = 9            # straight wall height above the floor before the dome springs
G_Y = -12           # floor of the molten gallery
CRYPT_Y = -26       # floor of the crypt at the bottom of the ancestors' hall


# ------------------------------------------------------------------ small helpers
def shell(bp, x0, y0, z0, x1, y1, z1, pal=DEEP_ROCK):
    """Fill the box with rock where nothing was placed yet (never overwrites rooms)."""
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, pal.pick(x, y, z))


def air(bp, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                bp.set(x, y, z, "air")


# ------------------------------------------------------------------ 1. the King's Stair
def kings_stair(bp):
    from .underground import hanging
    # floor top of each step: x = 43 -> -1 ... x = 32 -> -12
    shell(bp, 29, -16, -5, 45, 0, 5, DEEP_WALL)
    for x in range(32, 44):
        f = x - 44
        top = 0 if x >= 37 else f + 6
        for z in range(-2, 3):
            bp.set(x, f, z, stair(PBS, "east"))
            for y in range(f - 3, f):
                bp.set(x, y, z, PB)
            air(bp, x, f + 1, z, x, top, z)
        for z in (-3, 3):
            for y in range(f - 1, top + 1):
                bp.set(x, y, z, GT if y == f + 4 else PB if (x % 4 == 0) else DEEP_WALL.pick(x, y, z))
        if x < 37:      # stepped ceiling, corbelled with upside-down stairs
            for z in range(-3, 4):
                bp.set(x, top + 1, z, PB if abs(z) < 3 else DEEP_WALL.pick(x, top + 1, z))
            for z in (-2, 2):
                bp.set(x, top, z, stair(PBS, "south" if z < 0 else "north", "top"))
    # landing at the foot
    for x in range(29, 32):
        for z in range(-2, 3):
            bp.set(x, G_Y, z, "polished_deepslate")
            air(bp, x, G_Y + 1, z, x, G_Y + 6, z)
    # balustrade around the opening in the nave, gilded corner posts with lanterns
    for x in range(36, 44):
        for z in (-3, 3):
            bp.set(x, 0, z, PB)
            bp.set(x, 1, z, PBW)
    for z in range(-3, 4):
        bp.set(36, 0, z, PB)
        bp.set(36, 1, z, PBW)
    for x, z in ((36, -3), (36, 3), (43, -3), (43, 3)):
        bp.set(x, 1, z, GT)
        bp.set(x, 2, z, "chiseled_polished_blackstone")
        bp.lantern(x, 3, z)
    # a carved king's mask over the stair, facing the hall: the way is no secret
    bp.set(36, 2, 0, GT)
    bp.set(36, 3, 0, "chiseled_polished_blackstone")
    bp.set(36, 4, 0, LC)
    for z in (-1, 1):
        bp.set(36, 2, z, stair(PBS, "east"))
    hanging(bp, 34, -3, 0, 2)


# ------------------------------------------------------------------ 2. the Molten Gallery
def molten_gallery(bp):
    from .underground import hanging
    x0, x1 = 6, 31
    shell(bp, x0 - 3, G_Y - 4, -8, x1 + 2, -4, 8, DEEP_WALL)
    for x in range(x0, x1 + 1):
        bay = (x - x0) % 5 == 0
        for z in range(-4, 5):
            # stepped vault: 7 high in the middle, lower at the sides (softened later)
            h = 7 if abs(z) <= 1 else 6 if abs(z) <= 3 else 5
            air(bp, x, G_Y + 1, z, x, G_Y + h, z)
            bp.set(x, G_Y + h + 1, z, PB if bay else DEEP_WALL.pick(x, G_Y + h + 1, z))
            if z <= 0:      # the walkway
                bp.set(x, G_Y, z, PB if z in (-4, 0) else "polished_deepslate" if (x + z) % 3 else "deepslate_tiles")
            elif z == 1:    # the kerb with a low rail
                bp.set(x, G_Y, z, "polished_blackstone")
                bp.set(x, G_Y + 1, z, PBW if not bay else "chiseled_polished_blackstone")
            elif x in (x0, x1):     # the channel ends in a stone lip
                bp.set(x, G_Y, z, PB)
            else:           # the channel: lava one block below the walkway
                bp.set(x, G_Y, z, "air")
                bp.set(x, G_Y - 1, z, "lava")
                bp.set(x, G_Y - 2, z, PB)
        bp.set(x, G_Y - 1, 1, PB)
        # back wall of the channel and the walkway wall
        for y in range(G_Y - 1, G_Y + 6):
            bp.set(x, y, 5, PB if bay else DEEP_WALL.pick(x, y, 5))
            bp.set(x, y, -5, PB if bay else DEEP_WALL.pick(x, y, -5))
        bp.set(x, G_Y + 4, -5, GT)
        bp.set(x, G_Y + 4, 5, GT)
    # lava falls pouring from slits in the far wall into the channel
    for x in (10, 18, 26):
        for y in range(G_Y, G_Y + 6):
            bp.set(x, y, 4, "lava")
            bp.set(x, y, 5, PB)
        bp.set(x, G_Y + 6, 4, "chiseled_polished_blackstone")
        bp.set(x - 1, G_Y + 5, 4, stair(PBS, "east", "top"))
        bp.set(x + 1, G_Y + 5, 4, stair(PBS, "west", "top"))
    # walkway wall: niches with ember braziers between the pilasters, hanging lanterns
    for x in range(x0 + 2, x1 - 1, 5):
        bp.set(x, G_Y + 1, -5, "air")
        bp.set(x, G_Y + 2, -5, "air")
        bp.set(x, G_Y, -5, "magma_block")
        bp.set(x, G_Y + 1, -5, "campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
        bp.set(x, G_Y + 3, -5, stair(PBS, "south", "top"))
        hanging(bp, x, G_Y + 8, -1, 2)
    # magma cube nest in a deep alcove; a supply barrel and crates at the west end
    for z in (-5, -6, -7):
        air(bp, 20, G_Y + 1, z, 22, G_Y + 3, z)
        for x in range(20, 23):
            bp.set(x, G_Y, z, "magma_block")
    bp.spawner(21, G_Y + 1, -7, "minecraft:magma_cube")
    bp.barrel(x0, G_Y + 1, -4, "up", LOOT + "dwarven_mine")
    bp.barrel(x0, G_Y + 2, -4, "east")
    bp.set(x0 + 1, G_Y + 1, -4, "raw_iron_block")
    bp.set(x0, G_Y + 1, -3, "coal_block")


# ------------------------------------------------------------------ 3. the Ancestors' Hall
def floor_at(x):
    """Floor top of the processional stair, x = 5 (-12) down to x = -23 (-26)."""
    return G_Y - (5 - x) // 2


def ceil_at(x):
    return min(-5, floor_at(x) + 12)


ANCESTORS = (-3, -10, -17)


def ancestor(bp, cx, base, cz, inward):
    """A dwarven ancestor statue (13 tall): stepped pedestal with a lithite plaque, plated skirt, broad
    shoulders, fists folded on a planted war hammer, a long calcite beard ringed with gold, glowing
    lithite eyes, a gilded horned helm. inward = +1 / -1 along z (the way it looks)."""
    s = inward
    tuff = Palette({"polished_tuff": 3, "tuff_bricks": 3, "chiseled_tuff_bricks": 1}, seed=cx * 7 + cz, scale=1.5)
    back = "south" if s < 0 else "north"

    def P(u, f, y, b):            # u along x, f toward the hall, y up from the base
        bp.set(cx + u, base + y, cz + s * f, b)
    for u in range(-2, 3):        # pedestal
        for f in range(-2, 3):
            P(u, f, 0, GT if abs(u) == 2 or abs(f) == 2 else PB)
            if abs(u) <= 1 and abs(f) <= 1:
                P(u, f, 1, "polished_blackstone")
    P(0, 2, 1, LC)
    P(-1, 2, 1, stair(PBS, back))
    P(1, 2, 1, stair(PBS, back))
    for u in (-1, 1):             # boots with upturned toes
        P(u, 0, 2, "polished_blackstone")
        P(u, 1, 2, stair("polished_blackstone_stairs", back))
    for u in range(-2, 3):        # plated skirt and a gilded belt
        for f in range(-1, 2):
            if abs(u) == 2 and f == 1:
                continue
            P(u, f, 3, "iron_block" if (u + f) % 2 == 0 else "polished_blackstone")
            P(u, f, 4, GT if f == 1 else tuff.pick(u, 4, f))
    for y in (5, 6, 7):           # barrel chest
        for u in range(-2, 3):
            for f in range(-1, 2):
                P(u, f, y, tuff.pick(u, y, f))
    for u in (-3, 3):             # pauldrons, arms, fists folded on the hammer
        P(u, 0, 7, "polished_blackstone")
        P(u, -1, 7, "polished_blackstone")
        P(u, 1, 7, stair(PBS, back, "top"))
        P(u, 0, 6, tuff.pick(u, 6, 0))
        P(u, 0, 5, tuff.pick(u, 5, 0))
    for u in (-1, 1):
        P(u, 2, 5, "polished_tuff")
    for y in (2, 3, 4):           # the war hammer: head planted at its feet, haft up to the fists
        P(0, 3, y, PBW if y > 2 else "iron_block")
    P(-1, 3, 2, "iron_block")
    P(1, 3, 2, "iron_block")
    P(0, 3, 5, GT)
    for y in (8, 9, 10):          # head
        for u in range(-1, 2):
            for f in range(-1, 2):
                P(u, f, y, "polished_tuff")
    P(-1, 1, 9, LC)               # eyes
    P(1, 1, 9, LC)
    P(0, 2, 9, stair("polished_tuff_stairs", back, "top"))   # nose
    beard = ((8, 2), (7, 2), (6, 2), (5, 1), (4, 1), (3, 0))
    for y, w in beard:            # long beard over the chest, braided with gold
        for u in range(-w, w + 1):
            P(u, 2, y, "gold_block" if (y == 5 and abs(u) == 1) else "calcite" if (u + y) % 2 else "polished_diorite")
    P(0, 2, 8, stair("diorite_stairs", back, "top"))         # moustache
    for u in range(-2, 3):        # helm: gilded rim, blackstone dome, golden crest, horns
        for f in range(-2, 3):
            if abs(u) + abs(f) <= 3:
                P(u, f, 11, GT if (abs(u) == 2 or abs(f) == 2) else PB)
    for u in range(-1, 2):
        for f in range(-1, 2):
            P(u, f, 12, PB if (u or f) else "gold_block")
    P(0, 0, 13, "gold_block")
    for u in (-3, 3):
        P(u, 0, 11, "bone_block[axis=x]")
        P(u, 0, 12, "bone_block[axis=y]")


def ancestors_hall(bp):
    from .underground import hanging
    xa, xb = -24, 5
    shell(bp, xa - 2, CRYPT_Y - 4, -14, xb + 1, -4, 14, DEEP_WALL)
    for x in range(xa, xb + 1):
        f, c = floor_at(x), ceil_at(x)
        drop = floor_at(x + 1) > f if x < xb else False   # this cell is lower than the next one east
        for z in range(-5, 6):
            for y in range(f - 3, f):
                bp.set(x, y, z, PB)
            bp.set(x, f, z, PB if abs(z) <= 1 else "polished_deepslate" if abs(z) <= 4 else "polished_blackstone")
            # vault: higher in the middle (softened), gilded transverse ribs over the landings
            h = c - (0 if abs(z) <= 2 else 1 if abs(z) <= 4 else 2)
            air(bp, x, f + 1, z, x, h - 1, z)
            if drop:            # the step up to the next landing (east)
                bp.set(x, f + 1, z, stair(PBS, "east"))
            rib = (x - xa) % 6 == 0
            bp.set(x, h, z, PB if rib else DEEP_WALL.pick(x, h, z))
            if rib and abs(z) <= 1:
                bp.set(x, h, z, GT)
        for z in (-6, 6):
            for y in range(f, c):
                bp.set(x, y, z, PB if y == f else DEEP_WALL.pick(x, y, z))
            bp.set(x, f + 1, z, "polished_blackstone")
    # the statues in tall pointed niches, facing each other across the stair, a lithite halo behind each
    for cx in ANCESTORS:
        base = floor_at(cx)
        for s in (-1, 1):
            for x in range(cx - 4, cx + 5):
                for zz in range(6, 13):
                    z = zz * s
                    u = abs(x - cx)
                    top = min(base + 14, -6) - max(0, u - 1)
                    for y in range(base - 1, base + 16):
                        if u <= 3 and zz <= 11 and base <= y <= top:
                            bp.set(x, y, z, "air")
                        elif zz == 12 or u == 4 or y == base - 1 or bp.get(x, y, z) is None:
                            bp.set(x, y, z, PB if zz == 12 else DEEP_WALL.pick(x, y, z))
            for x in (cx - 4, cx + 4):     # niche jambs
                for y in range(base, min(base + 12, -6)):
                    bp.set(x, y, 6 * s, GT if y == base + 10 else "polished_blackstone")
            for (u, dy) in ((-2, 8), (-2, 9), (-2, 10), (2, 8), (2, 9), (2, 10), (-1, 11), (0, 11), (1, 11),
                            (-1, 7), (1, 7)):
                if base + dy <= min(base + 14, -6):
                    bp.set(cx + u, base + dy, 12 * s, LC)
            ancestor(bp, cx, base, 9 * s, -s)
            bp.set(cx - 3, base + 1, 7 * s, "candle[candles=3,lit=true,waterlogged=false]")
            bp.set(cx + 3, base + 1, 7 * s, "candle[candles=2,lit=true,waterlogged=false]")
        hanging(bp, cx, ceil_at(cx), 0, 3)
    # a great carved relief of the first king on the west wall, above the crypt door
    for z in range(-5, 6):
        for y in range(CRYPT_Y + 9, ceil_at(xa) + 1):
            bp.set(xa - 1, y, z, PB)
    for z, y, b in ((-1, 0, LC), (1, 0, LC), (0, -1, "chiseled_polished_blackstone"), (0, 2, GT), (-1, 2, GT),
                    (1, 2, GT), (0, 3, "gold_block"), (-2, 3, "gold_block"), (2, 3, "gold_block")):
        bp.set(xa - 1, CRYPT_Y + 9 + y, z, b)


# ------------------------------------------------------------------ 4. the Forge-fathers' crypt
def crypt(bp):
    from .underground import hanging
    x0, x1, z0, z1 = -31, -26, -6, 6
    y = CRYPT_Y
    shell(bp, x0 - 1, y - 3, z0 - 2, x1 + 1, y + 9, z1 + 2, DEEP_WALL)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, "polished_deepslate" if (x + z) % 2 else "deepslate_tiles")
            h = 7 - (abs(z) > 4)
            air(bp, x, y + 1, z, x, y + h, z)
            bp.set(x, y + h + 1, z, PB if x % 2 == 0 else DEEP_WALL.pick(x, y + h + 1, z))
    # a carved wall between the hall's foot (x = -24) and the crypt, with a pointed doorway
    for z in range(z0, z1 + 1):
        for yy in range(y, y + 9):
            bp.set(-25, yy, z, GT if yy == y + 6 else PB)
    from .underground import pointed_h
    for z in range(-2, 3):
        ph = pointed_h(z, 2.5, 3)
        for yy in range(y + 1, y + 7):
            if ph is not None and yy - y <= ph:
                bp.set(-25, yy, z, "air")
    # stone coffins along the north and south walls, a lid of slabs, gold on the chest
    for z in (-5, 5):
        for x in (-30, -27):
            for xx in (x, x + 1):
                bp.set(xx, y + 1, z, "polished_blackstone")
                bp.set(xx, y + 2, z, PBSL + "[type=bottom,waterlogged=false]")
            bp.set(x, y + 2, z, "gold_block" if x == -30 else PBSL + "[type=bottom,waterlogged=false]")
    for z in (-3, 3):
        bp.set(-31, y + 1, z, "decorated_pot[facing=east,waterlogged=false,cracked=true]")
    bp.set(-31, y + 1, 0, "skeleton_skull[rotation=4]")
    bp.set(-31, y + 1, -1, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(-31, y + 1, 1, "candle[candles=3,lit=true,waterlogged=false]")
    hanging(bp, -28, y + 8, 0, 3)
    bp.spawner(-29, y + 1, -2, MOB["ruin_walker"])
    bp.chest(-31, y + 1, 2, "east", LOOT + "dwarven_mine")


# ------------------------------------------------------------------ 5. the Collapsed Way
def way_floor(x):
    return CRYPT_Y if x <= -25 else max(AY, CRYPT_Y - (x + 25) // 2)


def collapsed_way(bp):
    """From the crypt's south door: a short passage, then a long stair east under everything, half
    blocked by a cave-in, down to the level of the arena."""
    y0 = CRYPT_Y
    shell(bp, -30, AY - 3, 6, 8, y0 + 7, 18, DEEP_ROCK)
    for x in range(-29, -26):           # passage south out of the crypt
        for z in range(7, 17):
            bp.set(x, y0, z, "polished_deepslate")
            air(bp, x, y0 + 1, z, x, y0 + 4, z)
    air(bp, -29, y0 + 1, 6, -27, y0 + 3, 7)              # the crypt's south door
    for x in range(-29, 8):
        f = way_floor(x)
        step = way_floor(x - 1) > f     # the cell to the west is higher: a stair leads down into this one
        for z in range(14, 17):
            for y in range(f - 2, f):
                bp.set(x, y, z, "deepslate_tiles")
            bp.set(x, f, z, "polished_deepslate" if (x + z) % 4 else "deepslate_tiles")
            air(bp, x, f + 1, z, x, f + 5, z)
            if step:
                bp.set(x, f + 1, z, stair("polished_deepslate_stairs", "west"))
            bp.set(x, f + 6, z, DEEP_WALL.pick(x, f + 6, z))
        for z in ((17,) if x <= -27 or 5 <= x <= 7 else (13, 17)):   # openings: crypt passage, grace door
            for y in range(f, f + 6):
                bp.set(x, y, z, DEEP_WALL.pick(x, y, z))
        if x % 6 == 0:          # timber props, like a mine
            for z in (14, 16):
                for y in range(f + 1 + step, f + 5):
                    bp.set(x, y, z, "dark_oak_log[axis=y]")
            for z in range(14, 17):
                bp.set(x, f + 5, z, "dark_oak_log[axis=z]")
            bp.lantern(x, f + 4, 15, hanging=True)
    # the cave-in: rubble heaped along the north side, a fallen beam, cobwebs
    for x, z, h in ((-14, 14, 2), (-13, 14, 3), (-12, 14, 2), (-13, 15, 1), (-11, 14, 1), (-6, 16, 2), (-5, 16, 1)):
        f = way_floor(x)
        for k in range(h):
            bp.set(x, f + 1 + k, z, "cobbled_deepslate" if k < h - 1 else "gravel")
    for x in range(-10, -7):
        bp.set(x, way_floor(x) + 3, 15, "stripped_dark_oak_log[axis=x]")
    bp.set(-12, way_floor(-12) + 5, 16, "cobweb")
    bp.set(-3, way_floor(-3) + 5, 14, "cobweb")


# ------------------------------------------------------------------ 6. the Last Anvil (site of grace)
def grace(bp):
    from .underground import hanging
    x0, x1, z0, z1 = 3, 15, -5, 6
    y = AY
    shell(bp, x0 - 2, y - 3, z0 - 2, x1 + 1, y + 9, z1 + 9, DEEP_WALL)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, PB if abs(z) <= 1 else "polished_deepslate")
            for yy in range(y - 2, y):
                bp.set(x, yy, z, PB)
            dz = z - 0.5
            h = 5 + int(2.2 * math.sqrt(max(0.0, 1 - (dz / 6.0) ** 2)))
            air(bp, x, y + 1, z, x, y + h, z)
            bp.set(x, y + h + 1, z, PB if x % 4 == 1 else DEEP_WALL.pick(x, y + h + 1, z))
    # door from the Collapsed Way (south wall, x 5..7)
    for x in range(5, 8):
        for z in range(7, 14):
            bp.set(x, y, z, "polished_deepslate")
            air(bp, x, y + 1, z, x, y + 4, z)
    # the waystone on a gilded plinth against the west wall, lit by lithite
    bp.set(x0, y, 0, GT)
    bp.set(x0, y + 1, 0, MOD["waystone"])
    for z in (-1, 1):
        bp.set(x0, y + 1, z, "chiseled_polished_blackstone")
        bp.set(x0, y + 2, z, LC)
    bp.set(x0 - 1, y + 3, 0, LC)
    # benches, a brazier and the last anvil of the dwarves
    for x in (6, 7, 9, 10):
        bp.set(x, y + 1, -5, stair("dark_oak_stairs", "north"))
        bp.set(x, y + 1, 6, stair("dark_oak_stairs", "south"))
    bp.set(8, y + 1, -5, "dark_oak_slab[type=bottom,waterlogged=false]")
    bp.set(8, y + 1, 6, "barrel[facing=up,open=false]")
    bp.set(8, y + 2, 6, "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(6, y + 1, 0, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    for z in (-1, 1):
        bp.set(6, y + 1, z, PBW)
    bp.set(11, y + 1, -3, "anvil[facing=east]")
    bp.set(11, y + 1, 3, "smithing_table")
    hanging(bp, 7, y + 8, 0, 2)
    hanging(bp, 12, y + 8, 0, 2)
    # the great portal into the Crucible: a pointed arch through the drum wall
    from .underground import pointed_h
    for x in range(x1 - 1, AX - AR - 1):
        for z in range(-3, 4):
            ph = pointed_h(z, 3.5, 4)
            for yy in range(y + 1, y + 10):
                if ph is not None and yy - y <= ph:
                    bp.set(x, yy, z, "air")
            bp.set(x, y, z, PB)
    for z in (-4, 4):
        for yy in range(y + 1, y + 8):
            bp.set(x1, yy, z, GT if yy == y + 7 else "polished_blackstone")
    for x in range(AX - AR - 4, AX - AR + 1):          # bridge over the lava channel into the arena
        for z in range(-2, 3):
            bp.set(x, y, z, "polished_blackstone" if abs(z) < 2 else GT)
            bp.set(x, y + 1, z, "air")


# ------------------------------------------------------------------ 7. the King's Crucible
def crucible(bp):
    from .underground import hanging
    R = AR
    Rw = R + 3.5                     # inner face of the drum wall
    shell(bp, AX - R - 7, AY - 4, AZ - R - 7, AX + R + 8, AY + DRUM + 14, AZ + R + 7, CRUCIBLE)
    # floor, lava channel, drum and dome
    for x in range(AX - R - 6, AX + R + 7):
        for z in range(AZ - R - 6, AZ + R + 7):
            d = math.hypot(x - AX, z - AZ)
            if d > Rw + 2.5:
                continue
            ang = math.degrees(math.atan2(z - AZ, x - AX)) % 360
            for y in range(AY - 3, AY):
                bp.set(x, y, z, PB)
            if d <= R + 0.5:
                # concentric floor: a forge sigil of ember brick at the heart, gilded rings, eight
                # spokes of carved stone, blackstone and deepslate bands between them
                spoke = min(ang % 45, 45 - ang % 45) * math.pi / 180 * d < 0.55
                if d < 1.6:
                    b = "gold_block"
                elif d < 2.6:
                    b = LC if int(ang / 45) % 2 == 0 else GT
                elif d < 5.5:
                    b = "chiseled_polished_blackstone" if spoke else "brasshaven:ember_bricks"
                elif d < 6.4 or 11.6 <= d < 12.5:
                    b = GT
                elif spoke:
                    b = "chiseled_polished_blackstone"
                elif d < 11.6:
                    b = PB if int(d) % 2 else "polished_blackstone"
                else:
                    b = "polished_deepslate"
                bp.set(x, AY, z, b)
            elif d <= R + 1.5:
                bp.set(x, AY, z, "polished_blackstone")       # kerb
                bp.set(x, AY + 1, z, "polished_blackstone_slab[type=bottom,waterlogged=false]")
            elif d <= R + 3.0:
                bp.set(x, AY, z, "lava")                      # the molten channel at the very edge
                bp.set(x, AY - 1, z, "magma_block")
            else:
                bp.set(x, AY, z, PB)
            if d <= Rw:
                top = AY + DRUM + dome_h(d)
                for y in range(AY + 1, top + 1):
                    if not (R + 0.5 < d <= R + 1.5 and y == AY + 1):
                        bp.set(x, y, z, "air")
                bp.set(x, top + 1, z, dome_block(x, top + 1, z, d, ang))
                bp.set(x, top + 2, z, CRUCIBLE.pick(x, top + 2, z))
            else:
                for y in range(AY + 1, AY + DRUM + 3):
                    bp.set(x, y, z, CRUCIBLE.pick(x, y, z))
    # string courses on the drum: a gilded band and a band of lithite
    for x in range(AX - R - 6, AX + R + 7):
        for z in range(AZ - R - 6, AZ + R + 7):
            d = math.hypot(x - AX, z - AZ)
            if Rw < d <= Rw + 1.2:
                bp.set(x, AY + 6, z, GT)
                bp.set(x, AY + DRUM, z, "chiseled_polished_blackstone")
    # eight great pilasters with ember lamps; lava pours from lion-mouth slots between them
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        px, pz = AX + round(math.cos(a) * (Rw + 0.3)), AZ + round(math.sin(a) * (Rw + 0.3))
        for y in range(AY, AY + DRUM + 4):
            for ox, oz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if math.hypot(px + ox - AX, pz + oz - AZ) >= Rw - 0.6:
                    bp.set(px + ox, y, pz + oz, GT if y in (AY + 6, AY + DRUM + 3) else "polished_blackstone")
        ix, iz = AX + round(math.cos(a) * (Rw - 0.8)), AZ + round(math.sin(a) * (Rw - 0.8))
        bp.set(ix, AY + 4, iz, "brasshaven:ember_lamp")
        bp.set(ix, AY + 3, iz, stair(PBS, _facing_out(a), "top"))
        bp.set(ix, AY + 5, iz, stair(PBS, _facing_out(a)))
    for k in (1, 3, 5, 7):
        forge_hearth(bp, math.radians(k * 45))
    for k in (2, 6):
        a = math.radians(k * 45)
        fx, fz = AX + round(math.cos(a) * (Rw + 0.6)), AZ + round(math.sin(a) * (Rw + 0.6))
        for y in range(AY, AY + 6):
            bp.set(fx, y, fz, "lava")
        bp.set(fx, AY + 6, fz, "chiseled_polished_blackstone")
        for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if bp.get(fx + ox, AY + 3, fz + oz) != AIR:
                for y in range(AY, AY + 6):
                    if bp.get(fx + ox, y, fz + oz) != AIR:
                        bp.set(fx + ox, y, fz + oz, PB)
    # chimneys of light: four shafts through the dome, lined with glowing lithite and shroomlight
    for k in range(4):
        a = math.radians(k * 90 + 45)
        cx, cz = AX + round(math.cos(a) * 8), AZ + round(math.sin(a) * 8)
        base = AY + DRUM + dome_h(8) - 1
        for y in range(base, base + 6):
            for ox in (-1, 0, 1):
                for oz in (-1, 0, 1):
                    edge = abs(ox) == 1 or abs(oz) == 1
                    if edge:
                        bp.set(cx + ox, y, cz + oz, LC if (y + ox + oz) % 3 == 0 else PB)
                    else:
                        bp.set(cx, y, cz, "air")
        bp.set(cx, base + 6, cz, "shroomlight")
    # the central oculus over the seal: a ring of lithite and a crucible hanging on chains
    top = AY + DRUM + dome_h(0)
    for x in range(AX - 3, AX + 4):
        for z in range(AZ - 3, AZ + 4):
            d = math.hypot(x - AX, z - AZ)
            if d <= 2.5:
                for y in range(top + 1, top + 4):
                    bp.set(x, y, z, "air" if d <= 1.5 else LC)
                bp.set(x, top + 4, z, "shroomlight" if d <= 1.5 else PB)
    for ox, oz in ((-1, 0), (1, 0), (0, -1), (0, 1)):          # the King's crucible, hung over the seal
        bp.chain(AX + ox, top - 3, AZ + oz, top + 3)
        bp.set(AX + ox, top - 4, AZ + oz, "chiseled_polished_blackstone")
    bp.set(AX, top - 4, AZ, "cauldron")
    bp.lantern(AX, top - 5, AZ, hanging=True)
    # lanterns on long chains around the ring
    for k in range(8):
        a = math.radians(k * 45)
        x, z = AX + round(math.cos(a) * 11), AZ + round(math.sin(a) * 11)
        hanging(bp, x, AY + DRUM + dome_h(11) + 1, z, 5)
    throne_apse(bp)
    # anvils of the royal smithy at the edge, by the pilasters (never on the fighting floor)
    for k in (1, 3, 5, 7):
        a = math.radians(k * 45 + 22.5)
        x, z = AX + round(math.cos(a) * (R + 1)), AZ + round(math.sin(a) * (R + 1))
        bp.set(x, AY + 1, z, "anvil[facing=" + ("north" if k % 4 == 1 else "east") + "]")
    bp.boss_seal(AX, AY, AZ, "brasshaven:forge_king", AR)


def forge_hearth(bp, a):
    """A forge mouth sunk in the drum wall: blast furnaces glowing at the back, a bed of magma behind
    an iron grille, a gilded lintel under a carved hood."""
    ux, uz = math.cos(a), math.sin(a)          # outward
    vx, vz = -uz, ux                           # lateral
    Rw = AR + 3.5

    def at(depth, lat):
        return AX + round(ux * (Rw + depth) + vx * lat), AZ + round(uz * (Rw + depth) + vz * lat)
    for depth in (0, 1, 2, 3):
        for lat in (-1.5, -0.5, 0.5, 1.5):
            x, z = at(depth, lat)
            for y in range(AY, AY + 7):
                if depth == 3 or abs(lat) > 1:
                    if bp.get(x, y, z) != AIR:
                        bp.set(x, y, z, PB)
                elif y == AY:
                    bp.set(x, y, z, "magma_block" if depth >= 1 else "polished_blackstone")
                elif depth == 2:
                    b = "blast_furnace[facing=" + _facing_out(a + math.pi) + ",lit=true]" if y <= AY + 2 else \
                        "brasshaven:ember_lamp" if y == AY + 3 else PB
                    bp.set(x, y, z, b)
                elif y <= AY + 4:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, GT if y == AY + 5 else PB)
    for lat in (-1.5, -0.5, 0.5, 1.5):
        x, z = at(0, lat)
        if abs(lat) < 1:
            bp.set(x, AY + 1, z, "iron_bars")
            bp.set(x, AY + 2, z, "iron_bars")
        bp.set(x, AY + 5, z, GT)
        bp.set(x, AY + 6, z, stair(PBS, _facing_out(a + math.pi), "top"))


def dome_h(d):
    """Height of the dome's inner surface above the drum at distance d from the axis."""
    Rd = AR + 3.5
    if d >= Rd:
        return 0
    return int(round(11 * math.sqrt(1 - (d / Rd) ** 2)))


def dome_block(x, y, z, d, ang):
    """Coffered dome: sixteen gilded ribs, a belt of glowing lithite, deepslate panels."""
    rib = min(ang % 22.5, 22.5 - ang % 22.5) * max(d, 1) * math.pi / 180 < 0.7
    if rib:
        return GT if d > 3 else PB
    if 9.5 < d < 10.5:
        return LC
    if 13.5 < d < 14.5 or 5.5 < d < 6.3:
        return PB
    return "deepslate_tiles" if (x + z) % 3 else "polished_deepslate"


def _facing_out(a):
    c, s = math.cos(a), math.sin(a)
    if abs(c) >= abs(s):
        return "east" if c > 0 else "west"
    return "south" if s > 0 else "north"


def throne_apse(bp):
    """The east apse: a stepped dais behind a bridge over the channel, the throne between two great
    anvils, a forge-hearth behind it, and the treasury door."""
    from .underground import hanging
    R = AR
    xs = AX + R + 1                  # first apse block (beyond the kerb)
    inner = AX + R + 3              # last x inside the drum
    for x in range(xs, xs + 9):
        for z in range(-5, 6):
            for y in range(AY - 2, AY):
                bp.set(x, y, z, PB)
            step = min(3, max(0, (x - xs) - 2))
            bp.set(x, AY, z, PB)
            for y in range(AY + 1, AY + 1 + step):
                bp.set(x, y, z, PB if abs(z) < 5 else GT)
            if x <= inner:          # the bridge over the channel, under the dome
                if step == 0:
                    bp.set(x, AY + 1, z, "air")
                continue
            air(bp, x, AY + 1 + step, z, x, AY + DRUM + 2, z)
            bp.set(x, AY + DRUM + 3, z, PB)
        if x > inner:
            for z in (-6, 6):
                for y in range(AY, AY + DRUM + 3):
                    bp.set(x, y, z, "polished_blackstone" if y < AY + DRUM else GT)
    for x in range(xs + 2, xs + 5):
        bp.set(x, AY + 1 + (x - xs - 2), 0, stair(PBS, "west"))
        for z in (-1, 1):
            bp.set(x, AY + 1 + (x - xs - 2), z, stair(PBS, "west"))
    # throne
    ty = AY + 4
    tx = xs + 6
    bp.set(tx, ty, 0, stair("polished_blackstone_stairs", "east"))
    for z in (-1, 1):
        bp.set(tx, ty, z, "chiseled_polished_blackstone")
        bp.set(tx, ty + 1, z, "gold_block")
        bp.set(tx, ty + 2, z, LC)
    for y in range(ty, ty + 5):
        bp.set(tx + 1, y, 0, GT if y < ty + 4 else "gold_block")
    bp.set(tx + 1, ty + 5, 0, LC)
    for z in (-1, 1):
        for y in range(ty, ty + 4):
            bp.set(tx + 1, y, z, PB)
    # two great anvils flank the throne, braziers beyond them
    for z in (-3, 3):
        bp.set(tx - 1, ty, z, "anvil[facing=east]")
        bp.set(tx - 1, ty, z + (1 if z > 0 else -1), "magma_block")
        bp.set(tx - 1, ty + 1, z + (1 if z > 0 else -1), "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    hanging(bp, xs + 4, AY + DRUM + 3, -3, 3)
    hanging(bp, xs + 4, AY + DRUM + 3, 3, 3)
    # treasury door behind the throne (south side of the apse back wall)
    for z in (-4, -3, -2):
        bp.set(xs + 9, ty - 1, z, PB)
        air(bp, xs + 9, ty, z, xs + 9, ty + 3, z)


def treasury(bp):
    from .underground import hanging
    R = AR
    xs = AX + R + 1
    x0, x1, z0, z1 = xs + 10, xs + 14, -8, 3
    y = AY + 3
    shell(bp, x0 - 2, y - 3, z0 - 2, x1 + 2, y + 8, z1 + 2, CRUCIBLE)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, "gold_block" if (x + z) % 5 == 0 else "polished_blackstone")
            air(bp, x, y + 1, z, x, y + 5, z)
            bp.set(x, y + 6, z, PB)
    bp.chest(x1, y + 1, -3, "west", LOOT + "dwarven_vault")
    bp.chest(x1, y + 1, -1, "west", LOOT + "dwarven_vault")
    bp.barrel(x1, y + 1, 1, "west", LOOT + "dwarven_mine")
    for x, z, h in ((x0, z0, 2), (x0 + 1, z0, 1), (x0, z0 + 1, 1), (x1, z0, 3), (x1 - 1, z0, 2), (x1, z0 + 1, 1)):
        for k in range(h):
            bp.set(x, y + 1 + k, z, "gold_block" if (k + x) % 2 else "raw_gold_block")
    bp.set(x1, y + 1, -2, LC)
    bp.set(x1, y + 2, -2, "amethyst_cluster[facing=up,waterlogged=false]")
    hanging(bp, (x0 + x1) // 2, y + 6, -2, 2)


def mists(bp):
    R = AR
    bp.mist(AX - R - 4, AY + 1, -3, AX - R - 4, AY + 8, 3)          # west portal from the site of grace
    xs = AX + R + 1
    bp.mist(xs + 9, AY + 4, -4, xs + 9, AY + 7, -2)                  # treasury door behind the throne


def build(bp):
    """Carve the whole lair. Call at the end of dwarven_forge(), before soften()."""
    crucible(bp)
    treasury(bp)
    grace(bp)
    collapsed_way(bp)
    crypt(bp)
    ancestors_hall(bp)
    molten_gallery(bp)
    kings_stair(bp)
    from .underground import soften
    soften(bp, 4, G_Y + 4, -5, 32, -5, 5)
    soften(bp, -24, CRYPT_Y + 6, -5, 5, -5, 5)
    soften(bp, 3, AY + 4, -5, 15, AY + 9, 6)
    mists(bp)
