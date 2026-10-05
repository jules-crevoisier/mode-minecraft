"""Deep Dwarven City (Cité naine des profondeurs): a lost dwarf kingdom carved deep underground (mega-structure).

Layout (x east, z south, y up; origin y = 0 is the cavern floor):
  * the Outer City: a 69 x 37 cavern cut square by the dwarves (vertical walls, natural domed ceiling up to
    ~38 blocks high), with
      - a central Hearth: a lava basin and a 14-block brazier column fed by two rivers of fire that pour from
        lava falls in the east and west walls,
      - forges and a smelter with blast-furnace towers (west), a tavern and a gem-cutters' hall (east),
      - three levels of housing terraces cut into the side walls, joined by stairwells carved in the rock,
      - a mine-cart line from a station by the gate to the mine tunnel in the south wall,
  * the Gate: on the north wall, a raised terrace and a stair, a 13-block stepped portal and two 22-block
    dwarf statues (one with a mithril axe, one with a war hammer),
  * the Great Hall behind it: a pillared nave with gold-trimmed capitals and fire channels under glass,
  * the Throne Room: an octagon with the throne on a dais between lava basins,
  * the Treasure Vault under the throne, reached by a trapdoor hidden under a carpet behind the throne.
"""
import math

from .. import interior as INT
from .. import denizens
from ..arch import Palette, stair, slab
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOD

W = "brasshaven:"
GILD, MITH = W + "gilded_trim", W + "mithril_block"
POL, TILE, CHIS, BRK = "polished_deepslate", "deepslate_tiles", "chiseled_deepslate", "deepslate_bricks"
BLACK, BLACK_BR = "polished_blackstone", "polished_blackstone_bricks"
TILE_ST, BRK_ST, POL_ST = "deepslate_tile_stairs", "deepslate_brick_stairs", "polished_deepslate_stairs"
BRK_WALL, POL_WALL, TILE_WALL = "deepslate_brick_wall", "polished_deepslate_wall", "deepslate_tile_wall"
LAVA = "lava[level=0]"

ROCK = Palette({"deepslate": 6, "cobbled_deepslate": 2, "tuff": 2, "deepslate_tiles": 1}, seed=3, scale=4.0)
MASON = Palette({BRK: 6, TILE: 2, "cracked_deepslate_bricks": 1}, seed=5, scale=2.5)
DARK = Palette({BLACK_BR: 4, BLACK: 1, "cracked_polished_blackstone_bricks": 1}, seed=7, scale=2.0)

HX = 34          # cavern half width (air for |x| <= HX)
Z0, Z1 = 0, 36   # cavern depth (air for Z0 <= z <= Z1)
TER = 3          # gate terrace / great hall floor
LEVELS = (7, 13, 19)   # housing terraces (walkway block y)
HALL_Z1 = -32    # great hall back wall
THRONE_Z, THRONE_Y, THRONE_R = -42, 5, 9
VAULT_Y = -6


def _hash(x, y, z, s=0):
    n = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (s * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


_NOISE = Palette({"a": 1}, seed=11, scale=5.0)


def noise(x, y, z):
    return _NOISE._noise(x, y, z)


def ceil_y(x, z):
    """Top air block of the cavern at column (x, z): a natural dome, 28 at the walls, ~38 in the middle."""
    xx = max(-HX, min(HX, x))
    zz = max(Z0, min(Z1, z))
    k = (1 - (xx / 38) ** 2) * (1 - ((zz - 18) / 22) ** 2)
    return int(28 + 10 * k + noise(x, 40, z) * 4 - 2)


def wall_in(y, z, side):
    """How far the rough rock juts in from the side wall near the ceiling (0 below the terraces)."""
    if y <= 23:
        return 0
    return int(noise(side * 50, y, z) * 4 * min(1.0, (y - 23) / 5))


def in_cavern(x, y, z):
    if not (Z0 <= z <= Z1 and 1 <= y <= ceil_y(x, z)):
        return False
    side = 1 if x > 0 else -1
    return abs(x) <= HX - wall_in(y, z, side)


# ------------------------------------------------------------------ rock, cavern, floor
def cavern(bp):
    for x in range(-HX - 8, HX + 9):
        for z in range(Z0 - 3, Z1 + 9):
            top = ceil_y(x, z) + 3
            for y in range(-3, top + 1):
                if in_cavern(x, y, z):
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, ROCK.pick(x, y, z))
    # ore veins and crystals in the rock face
    ores = ["deepslate_gold_ore", "deepslate_iron_ore", W + "deepslate_mithril_ore", "deepslate_copper_ore",
            "deepslate_diamond_ore", "deepslate_emerald_ore"]
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] == "minecraft:air":
            continue
        h = _hash(x, y, z, 9)
        if h < 0.012:
            bp.set(x, y, z, ores[int(_hash(x, y, z, 4) * len(ores)) % len(ores)])
    # floor: polished deepslate tiles in a 6-block grid of deepslate tiles
    for x in range(-HX, HX + 1):
        for z in range(Z0, Z1 + 1):
            grid = x % 6 == 0 or z % 6 == 0
            bp.set(x, 0, z, TILE if grid else POL)
            bp.set(x, -1, z, "deepslate")
    # the walls are dressed masonry up to the first terrace: the city base course
    for z in range(Z0, Z1 + 1):
        for side in (-1, 1):
            for y in range(1, 6):
                bp.set(side * (HX + 1), y, z, MASON.pick(side * (HX + 1), y, z) if y < 5 else POL)
    for x in range(-HX, HX + 1):
        for y in range(1, 6):
            bp.set(x, y, Z1 + 1, MASON.pick(x, y, Z1 + 1) if y < 5 else POL)


def ceiling_details(bp):
    """Stalactites and hanging lanterns on long chains."""
    for x in range(-HX + 2, HX - 1, 3):
        for z in range(Z0 + 2, Z1 - 1, 3):
            h = _hash(x, 0, z, 21)
            c = ceil_y(x, z)
            if not in_cavern(x, c, z) or in_cavern(x, c + 1, z):
                continue
            if h < 0.28:
                n = 1 + int(_hash(x, 1, z, 3) * 4)
                parts = ["base", "frustum", "middle", "tip"][-n:] if n > 1 else ["tip"]
                for i, p in enumerate(parts):
                    thick = "frustum" if p == "base" else p
                    bp.set(x, c - i, z,
                           f"pointed_dripstone[thickness={thick},vertical_direction=down,waterlogged=false]")
    for (x, z, L) in ((-20, 6, 12), (20, 6, 12), (-12, 28, 14), (12, 28, 14), (-24, 20, 10), (24, 20, 10),
                      (0, 30, 16), (-8, 12, 16), (8, 12, 16), (-30, 30, 9), (30, 30, 9)):
        c = ceil_y(x, z)
        bp.chain(x, c - L, z, c)
        bp.lantern(x, c - L - 1, z, hanging=True)


# ------------------------------------------------------------------ the gate
def statue(bp, cx, by, cz, weapon):
    """A 22-block dwarf king facing south: boots, mail skirt, belt, breastplate, white braided beard,
    horned helmet, both hands on a war hammer or a mithril axe planted in front of him."""
    def put(u, y, v, spec):
        bp.set(cx + u, by + y, cz + v, spec)

    for y in range(0, 2):                       # boots
        for u in list(range(-3, 0)) + list(range(1, 4)):
            for v in range(-1, 3):
                put(u, y, v, BLACK)
    for y in range(2, 4):                       # legs
        for u in list(range(-3, 0)) + list(range(1, 4)):
            for v in range(-1, 2):
                put(u, y, v, "tuff_bricks")
    for y in range(4, 8):                       # mail skirt, flared
        r = 4 if y < 6 else 3
        for u in range(-r, r + 1):
            for v in range(-2, 3):
                put(u, y, v, "chiseled_tuff" if v == 2 and (u + y) % 2 else "polished_tuff")
    for u in range(-4, 5):                      # belt with a mithril buckle
        for v in range(-2, 3):
            put(u, 8, v, GILD)
    put(0, 8, 3, MITH)
    for y in range(9, 15):                      # torso: breastplate with gilded edges
        for u in range(-4, 5):
            for v in range(-2, 3):
                edge = abs(u) == 4 or y == 14
                put(u, y, v, GILD if edge and v == 2 else ("chiseled_tuff_bricks" if v == 2 else "tuff_bricks"))
    for side in (-1, 1):                        # pauldrons
        for y in (13, 14, 15):
            for v in range(-2, 3):
                put(side * 5, y, v, GILD if y == 13 else BLACK)
        put(side * 4, 15, 0, BLACK)
        for y in range(9, 13):                  # arms down to the hands
            put(side * 5, y, 0, "tuff_bricks")
            put(side * 5, y, 1, "tuff_bricks")
        for (u, v) in ((side * 4, 2), (side * 3, 3), (side * 2, 4)):
            put(u, 10, v, "polished_tuff")
            put(u, 9, v, GILD if u == side * 4 else "polished_tuff")
        put(side * 1, 10, 4, "polished_tuff")   # fists around the haft
        put(side * 1, 9, 4, "polished_tuff")
    for y in range(15, 20):                     # head
        for u in range(-2, 3):
            for v in range(-2, 3):
                put(u, y, v, "polished_tuff")
    put(-1, 17, 3, BLACK)                       # eyes and nose
    put(1, 17, 3, BLACK)
    put(0, 16, 3, "polished_tuff")
    for u in range(-3, 4):                      # helmet: rim, dome, crest, horns
        for v in range(-3, 4):
            if max(abs(u), abs(v)) == 3:
                put(u, 18, v, GILD)
    for y in (19, 20):
        for u in range(-2, 3):
            for v in range(-2, 3):
                put(u, y, v, BLACK if y == 19 else (GILD if abs(u) + abs(v) <= 1 else BLACK))
    for v in range(-2, 3):
        put(0, 21, v, GILD)
    for side in (-1, 1):
        put(side * 3, 19, 0, "bone_block[axis=x]")
        put(side * 4, 20, 0, "bone_block[axis=y]")
        put(side * 4, 21, 0, "bone_block[axis=y]")
        put(side * 4, 22, -1, "bone_block[axis=y]")
    for y in range(4, 16):                      # beard: wide under the face, tapering into two braids
        w = 2 if y >= 9 else (1 if y >= 6 else 0)
        for u in range(-w, w + 1):
            put(u, y, 3, "calcite")
        if y in (14, 15):                       # moustache
            for u in range(-2, 3):
                put(u, y, 4, "calcite")
    for side in (-1, 1):
        for y in (3, 4, 5):
            put(side * 2, y, 3, "calcite")
        put(side * 2, 2, 3, GILD)
    # the weapon, planted in front of him (haft through the fists)
    for y in range(0, 13):
        put(0, y, 5, "dark_oak_log[axis=y]" if weapon == "axe" else POL_WALL)
    put(0, 9, 4, "dark_oak_log[axis=y]" if weapon == "axe" else POL_WALL)
    if weapon == "hammer":
        for u in range(-2, 3):
            for v in range(4, 7):
                for y in range(0, 3):
                    put(u, y, v, GILD if y == 1 and abs(u) == 2 else BLACK_BR)
    else:
        for y in range(11, 17):
            put(0, y, 5, "dark_oak_log[axis=y]")
        put(0, 17, 5, GILD)
        for y in range(12, 17):                 # double-bitted mithril head
            w = {12: 1, 13: 2, 14: 3, 15: 2, 16: 1}[y]
            for u in range(1, w + 1):
                put(u, y, 5, MITH)
                put(-u, y, 5, MITH)


def gate(bp):
    # terrace and grand stair
    for x in range(-23, 24):
        for z in range(Z0, 11):
            for y in range(1, TER):
                bp.set(x, y, z, MASON.pick(x, y, z))
            bp.set(x, TER, z, TILE if (x % 5 == 0 or z % 5 == 0) else POL)
    for x in range(-23, 24):
        if abs(x) > 8:
            bp.set(x, TER + 1, 10, BRK_WALL)
    for z in range(Z0, 11):
        for side in (-1, 1):
            bp.set(side * 23, TER + 1, z, BRK_WALL)
    for (x, z) in ((-23, 10), (23, 10), (-9, 10), (9, 10)):
        bp.set(x, TER + 1, z, BRK)
        bp.set(x, TER + 2, z, CHIS)
        bp.lantern(x, TER + 3, z)
    for i, z in enumerate((11, 12, 13)):
        for x in range(-8, 9):
            bp.set(x, TER - i, z, stair(TILE_ST, "north"))
            for y in range(1, TER - i):
                bp.set(x, y, z, MASON.pick(x, y, z))
        for side in (-1, 1):
            bp.set(side * 9, TER - i, z, POL)
            for y in range(1, TER - i):
                bp.set(side * 9, y, z, POL)
    # dressed facade on the cavern wall
    for x in range(-25, 26):
        for y in range(TER + 1, 31):
            if not in_cavern(x, y, 0):
                continue
            bp.set(x, y, -1, MASON.pick(x, y, -1))
    # frieze band and secondary pilasters
    for x in range(-25, 26):
        for y in (25, 26):
            if in_cavern(x, y, 0):
                bp.set(x, y, 0, GILD if (y == 25 and x % 4 == 0) or (y == 26 and x % 4 == 2) else CHIS)
    for px in (-25, -10, 10, 25):
        for y in range(TER + 1, 25):
            bp.set(px, y, 0, TILE if y % 6 else POL)
        bp.set(px, TER + 1, 1, stair(TILE_ST, "north"))
        bp.set(px, 24, 1, stair(TILE_ST, "north", "top"))
    # the portal: pilasters, stepped frame, lintel, pediment, emblem
    for side in (-1, 1):
        for x in (side * 6, side * 7):
            for z in (0, 1):
                for y in range(TER + 1, 21):
                    flute = x == side * 6 and z == 1 and y % 2 == 0
                    bp.set(x, y, z, POL if flute else TILE)
            bp.set(x, TER + 1, 2, stair(TILE_ST, "north"))
        for y in (19, 20):
            for x in (side * 5, side * 6, side * 7, side * 8):
                bp.set(x, y, 1, GILD if y == 19 else CHIS)
    opening = set()
    for y in range(TER + 1, 17):
        w = 4 if y <= 13 else {14: 3, 15: 2, 16: 1}[y]
        for x in range(-w, w + 1):
            opening.add((x, y))
    for x in range(-5, 6):
        for y in range(TER + 1, 21):
            if (x, y) in opening:
                for z in range(-1, 3):
                    bp.set(x, y, z, "air")
            elif any((x + dx, y + dy) in opening for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                bp.set(x, y, 0, GILD)
                bp.set(x, y, -1, CHIS)
            else:
                bp.set(x, y, 0, CHIS if (x + y) % 3 else POL)
    for x in range(-8, 9):                       # lintel
        for z in (0, 1, 2):
            bp.set(x, 21, z, POL if z < 2 else stair(POL_ST, "north", "top"))
        bp.set(x, 22, 0, GILD)
        bp.set(x, 22, 1, slab("polished_deepslate_slab"))
    for i, y in enumerate(range(23, 28)):        # stepped pediment
        w = 7 - i * 2
        if w < 0:
            break
        for x in range(-w, w + 1):
            if in_cavern(x, y, 0):
                bp.set(x, y, 0, TILE if abs(x) == w else POL)
    for x in range(-2, 3):                       # mithril rune lozenge above the door
        for y in range(17, 21):
            d = abs(x) + abs(y - 18.5)
            if d <= 1.6:
                bp.set(x, y, 0, MITH)
            elif d <= 2.6:
                bp.set(x, y, 0, GILD)
    # the gate leaves, swung open against the jambs inside
    for side in (-1, 1):
        for z in range(-5, -1):
            for y in range(TER + 1, TER + 11):
                bp.set(side * 4, y, z, GILD if (y - TER) % 3 == 0 or z == -5 else W + "dark_iron_plating")
    # braziers on the terrace
    for side in (-1, 1):
        x = side * 11
        bp.set(x, TER + 1, 6, BRK)
        bp.set(x, TER + 2, 6, BLACK)
        bp.set(x, TER + 3, 6, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + d[0], TER + 1, 6 + d[1], stair(BRK_ST, {(1, 0): "west", (-1, 0): "east", (0, 1): "north",
                                                               (0, -1): "south"}[d]))
    statue(bp, -17, TER + 4, 3, "axe")
    statue(bp, 17, TER + 4, 3, "hammer")
    for side in (-1, 1):                         # pedestals
        for x in range(side * 17 - 4, side * 17 + 5):
            for z in range(0, 10):
                for y in range(TER + 1, TER + 4):
                    edge = abs(x - side * 17) == 4 or z in (0, 9)
                    bp.set(x, y, z, (GILD if y == TER + 3 else CHIS) if edge else MASON.pick(x, y, z))


# ------------------------------------------------------------------ the great hall
def great_hall(bp):
    z0, z1 = -2, HALL_Z1 + 1   # interior z range (z1 < z0)

    def inside(x, y, z):
        if not (z1 <= z <= z0 and TER + 1 <= y):
            return False
        ax = abs(x)
        return (ax <= 13 and y <= 16) or (ax <= 10 and y <= 18) or (ax <= 8 and y <= 20) or (ax <= 5 and y <= 22)

    for x in range(-16, 17):
        for z in range(z1 - 2, z0 + 1):
            for y in range(TER - 2, 26):
                if inside(x, y, z):
                    bp.set(x, y, z, "air")
                elif y <= TER or any(inside(x + dx, y + dy, z + dz)
                                     for dx in (-2, 0, 2) for dy in (-2, 0, 2) for dz in (-2, 0, 2)):
                    bp.set(x, y, z, MASON.pick(x, y, z) if y > TER else POL)
    # floor: a polished nave with a gilded runner, fire channels under glass along the aisles
    for z in range(z1, z0 + 1):
        for x in range(-13, 14):
            ax = abs(x)
            if ax == 11:
                bp.set(x, TER, z, "glass")
                bp.set(x, TER - 1, z, LAVA)
                bp.set(x, TER - 2, z, BLACK)
            elif ax <= 1:
                bp.set(x, TER, z, GILD if ax == 1 else (MITH if z % 6 == 0 else BLACK_BR))
            else:
                bp.set(x, TER, z, TILE if (z % 6 == 0 or ax in (5, 9)) else POL)
    # pillars with flared gilded capitals and arcades between them
    for z in (-7, -13, -19, -25):
        for side in (-1, 1):
            px = side * 7
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for y in range(TER + 1, 17):
                        bp.set(px + dx, y, z + dz, POL if (dx == 0) != (dz == 0) else "tuff_bricks")
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) == 2:
                        bp.set(px + dx, TER + 1, z + dz, stair(POL_ST, _away(dx, dz)))
                        bp.set(px + dx, 15, z + dz, stair(TILE_ST, _toward(dx, dz), "top"))
                        bp.set(px + dx, 16, z + dz, CHIS)
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bp.set(px + dx, TER + 2, z + dz, CHIS if (dx, dz) != (0, 0) else POL)
                    bp.set(px + dx, 14, z + dz, GILD)
            bp.set(px, 15, z - 2, MITH)
            bp.set(px, 15, z + 2, MITH)
            # banners on the nave side
            bp.set(px - side * 2, 11, z, f"red_wall_banner[facing={'east' if side < 0 else 'west'}]")
            # beams to the side wall
            for x in range(px + side * 3, side * 14, side):
                bp.set(x, 16, z, TILE)
                bp.set(x, 15, z, stair(TILE_ST, "west" if side > 0 else "east", "top") if x == px + side * 3 else "air")
    # transverse gilded ribs in the nave vault
    for z in (-4, -10, -16, -22, -28):
        for x in range(-10, 11):
            for y in range(17, 24):
                if not inside(x, y, z) and inside(x, y - 1, z):
                    bp.set(x, y, z, GILD)
    # side alcoves with ancestor statues and braziers
    for z in (-4, -10, -16, -22, -28):
        for side in (-1, 1):
            ax = side * 14
            for y in range(TER + 1, TER + 8):
                for dz in (-1, 0, 1):
                    bp.set(ax, y, z + dz, "air")
                    bp.set(ax + side, y, z + dz, MASON.pick(ax, y, z))
            for dz in (-1, 0, 1):
                bp.set(ax, TER + 8, z + dz, stair(TILE_ST, "east" if side > 0 else "west", "top"))
            ancestor(bp, ax, TER + 1, z, "west" if side > 0 else "east")
    # chandeliers down the nave
    for z in (-7, -13, -19, -25):
        bp.chain(0, 17, z, 21)
        bp.set(0, 16, z, W + "brass_chandelier")
    for z in (-4, -16, -28):
        for side in (-1, 1):
            bp.set(side * 4, TER + 1, z, POL_WALL)
            bp.set(side * 4, TER + 2, z, POL_WALL)
            bp.lantern(side * 4, TER + 3, z)
    # steps up to the throne room
    for x in range(-3, 4):
        bp.set(x, TER + 1, HALL_Z1 + 2, stair(BRK_ST, "north"))
        bp.set(x, TER + 2, HALL_Z1 + 1, stair(BRK_ST, "north"))
        bp.set(x, TER + 1, HALL_Z1 + 1, BRK)
        for y in range(THRONE_Y + 1, THRONE_Y + 9):
            bp.set(x, y, HALL_Z1, "air")
        bp.set(x, THRONE_Y, HALL_Z1, POL)
        for y in range(1, THRONE_Y):
            bp.set(x, y, HALL_Z1, BRK)
    for x in range(-4, 5):
        bp.set(x, THRONE_Y + 9, HALL_Z1 + 1, GILD if abs(x) < 4 else CHIS)
    for side in (-1, 1):
        for y in range(TER + 1, THRONE_Y + 10):
            bp.set(side * 4, y, HALL_Z1 + 1, TILE if y % 3 else GILD)


def _away(dx, dz):
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def _toward(dx, dz):
    return {"west": "east", "east": "west", "north": "south", "south": "north"}[_away(dx, dz)]


def ancestor(bp, x, y, z, facing):
    """A 6-block statue of an ancestor in an alcove, with a gilded helmet and a beard."""
    fx, fz = {"east": (1, 0), "west": (-1, 0)}[facing]
    bp.set(x, y, z, CHIS)
    bp.set(x, y + 1, z, TILE)
    bp.set(x, y + 2, z, TILE)
    bp.set(x, y + 3, z, POL)
    bp.set(x, y + 4, z, POL)
    bp.set(x, y + 5, z, GILD)
    bp.set(x + fx, y + 2, z, "calcite")
    bp.set(x + fx, y + 3, z, stair("polished_tuff_stairs", "west" if fx > 0 else "east", "top"))
    for dz in (-1, 1):
        bp.set(x, y + 2, z + dz, stair(TILE_ST, "north" if dz > 0 else "south", "top"))
    bp.set(x + fx, y, z, BRK)
    bp.set(x + fx, y + 1, z, "lantern[hanging=false,waterlogged=false]")


# ------------------------------------------------------------------ throne room and vault
def throne_room(bp):
    cz, fy, r = THRONE_Z, THRONE_Y, THRONE_R

    def octo(x, z, rr):
        return max(abs(x), abs(z - cz), (abs(x) + abs(z - cz)) / 1.42) <= rr

    for x in range(-r - 3, r + 4):
        for z in range(cz - r - 3, cz + r + 4):
            for y in range(VAULT_Y - 2, fy + 21):
                if not octo(x, z, r + 2.5):
                    continue
                if octo(x, z, r) and y > fy:
                    dome = fy + 12 + 6 * (1 - (max(abs(x), abs(z - cz)) / (r + 1)) ** 2)
                    bp.set(x, y, z, "air" if y <= dome else DARK.pick(x, y, z))
                else:
                    bp.set(x, y, z, DARK.pick(x, y, z) if y > fy else MASON.pick(x, y, z))
            if octo(x, z, r):
                ring = max(abs(x), abs(z - cz))
                bp.set(x, fy, z, GILD if ring in (3, 7) else (BLACK_BR if ring > 3 else MITH if ring == 0 else POL))
    # four pillars and a gilded cornice
    for (px, pz) in ((-5, cz - 5), (5, cz - 5), (-5, cz + 5), (5, cz + 5)):
        for y in range(fy + 1, fy + 14):
            for dx in (0, 1):
                for dz in (0, 1):
                    bp.set(px + dx - (1 if px > 0 else 0), y, pz + dz - (1 if pz > cz else 0),
                           GILD if y in (fy + 1, fy + 12) else (CHIS if y == fy + 13 else TILE))
    for x in range(-r, r + 1):
        for z in range(cz - r, cz + r + 1):
            if octo(x, z, r) and not octo(x, z, r - 1):
                bp.set(x, fy + 11, z, GILD)
                bp.set(x, fy + 1, z, POL)
    # the doorway on the south side
    for x in range(-3, 4):
        bp.set(x, fy + 1, cz + r, "air")
    # dais and throne
    for x in range(-4, 5):
        for z in range(cz - r, cz - 3):
            bp.set(x, fy + 1, z, POL if z < cz - 4 else stair(POL_ST, "north"))
    for x in range(-2, 3):
        for z in range(cz - r, cz - 5):
            bp.set(x, fy + 2, z, BLACK_BR if z < cz - 6 else stair("polished_blackstone_brick_stairs", "north"))
    ty, tz = fy + 3, cz - 7
    bp.set(0, ty, tz, stair("polished_blackstone_stairs", "north"))
    for side in (-1, 1):
        bp.set(side, ty, tz, GILD)
        bp.set(side, ty + 1, tz, slab("polished_blackstone_slab"))
    for y in range(ty, ty + 5):
        for x in (-1, 0, 1):
            bp.set(x, y, tz - 1, MITH if (x == 0 and y in (ty + 2, ty + 3)) else GILD)
    bp.set(0, ty + 5, tz - 1, GILD)
    for x in (-1, 1):
        bp.set(x, ty + 5, tz - 1, "gold_block")
    bp.set(0, ty + 6, tz - 1, "gold_block")
    # lava basins flanking the dais, banners behind
    for side in (-1, 1):
        for x in (side * 6, side * 7):
            for z in (cz - 6, cz - 5):
                bp.set(x, fy, z, LAVA)
                bp.set(x, fy - 1, z, BLACK)
        for x in (side * 5, side * 8):
            for z in (cz - 7, cz - 6, cz - 5, cz - 4):
                bp.set(x, fy + 1, z, POL_WALL)
        for z in (cz - 7, cz - 4):
            for x in (side * 6, side * 7):
                bp.set(x, fy + 1, z, POL_WALL)
        for x in (side * 3, side * 2):
            bp.set(x, fy + 6, cz - r - 1 + 1, "air")
        bp.set(side * 3, fy + 7, cz - r, f"black_wall_banner[facing=south]")
        bp.set(side * 5, fy + 7, cz - r + 1, f"red_wall_banner[facing=south]")
    # chandelier under the dome
    bp.chain(0, fy + 14, cz, fy + 17)
    bp.set(0, fy + 13, cz, W + "brass_chandelier")
    for (x, z) in ((-6, cz), (6, cz)):
        bp.set(x, fy + 1, z, POL_WALL)
        bp.lantern(x, fy + 2, z)
    bp.spawner(-3, fy + 1, cz + 3, "brasshaven:skeleton_knight")


def secret_way(bp):
    """Behind the throne, a trapdoor under a carpet; a ladder down through the rock into the vault."""
    fy, sz = THRONE_Y, THRONE_Z - THRONE_R
    bp.set(0, fy + 2, sz, "dark_oak_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(0, fy + 3, sz, "red_carpet")
    for y in range(VAULT_Y + 1, fy + 2):
        bp.set(0, y, sz, "ladder[facing=south,waterlogged=false]")
        bp.set(0, y, sz - 1, BLACK_BR)
        for x in (-1, 1):
            if y > VAULT_Y + 6:
                bp.set(x, y, sz, BLACK_BR)


def vault(bp):
    cz, y0 = THRONE_Z, VAULT_Y
    x0, x1, z0, z1 = -7, 7, cz - 9, cz + 5
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0, y0 + 7):
                edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
                if y == y0:
                    bp.set(x, y, z, GILD if (x + z) % 4 == 0 and not edge else BLACK_BR)
                elif y == y0 + 6 or edge:
                    bp.set(x, y, z, DARK.pick(x, y, z) if not (edge and y == y0 + 5) else GILD)
                else:
                    bp.set(x, y, z, "air")
    # hoard: heaps of gold and ore along the walls, mithril on plinths
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if abs(x) <= 1 and z == z0:
                continue                      # the foot of the secret ladder
            h = 1 + int(_hash(x, 0, z, 33) * 2)
            for y in range(y0 + 1, y0 + 1 + h):
                hoard = ["gold_block", "raw_gold_block", "gold_block", "raw_iron_block"]
                bp.set(x, y, z, hoard[int(_hash(x, y, z, 2) * 4) % 4])
    for z in range(z0 + 1, z1):
        if z == cz - 9 or abs(z - (z0 + z1) // 2) > 3:
            continue
        for x in (x0, x1):
            bp.set(x, y0 + 1, z, CHIS)
            bp.set(x, y0 + 2, z, MITH if z % 2 else "emerald_block")
    for (x, z) in ((-4, z1 - 1), (4, z1 - 1), (-4, z0 + 2), (4, z0 + 2)):
        bp.chest(x, y0 + 1, z, "north" if z > cz else "south", loot=LOOT + "dwarven_city_vault")
    # the king's own chest on a plinth behind bars
    bp.set(0, y0 + 1, cz - 2, BLACK_BR)
    bp.chest(0, y0 + 2, cz - 2, "south", loot=LOOT + "dwarven_city_vault")
    for x in (-1, 0, 1):
        for z in (cz - 3, cz - 2, cz - 1):
            if (x, z) not in ((0, cz - 2), (0, cz - 1)):
                bp.set(x, y0 + 1, z, "iron_bars")
    for (x, z) in ((-5, cz), (5, cz)):
        bp.set(x, y0 + 5, z, BLACK_BR)
        bp.lantern(x, y0 + 4, z, hanging=True)
    bp.spawner(0, y0 + 1, cz + 3, "brasshaven:skeleton_knight")


# ------------------------------------------------------------------ the outer city
def hearth(bp):
    cx, cz = 0, 20
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.4:
                bp.set(x, 0, z, LAVA)
                bp.set(x, -1, z, BLACK)
                bp.set(x, -2, z, BLACK)
            elif d <= 5.4:
                bp.set(x, 0, z, BLACK_BR)
                bp.set(x, 1, z, POL_WALL)
            elif d <= 7.4:
                bp.set(x, 0, z, GILD if int(math.degrees(math.atan2(z - cz, x - cx))) % 30 < 8 else "polished_tuff")
            elif d <= 9.4 and bp.get(x, 0, z) in (POL, TILE, "minecraft:" + POL, "minecraft:" + TILE):
                bp.set(x, 0, z, "tuff_bricks")
    for x in range(cx - 1, cx + 2):             # the column
        for z in range(cz - 1, cz + 2):
            for y in range(-2, 14):
                bp.set(x, y, z, GILD if y % 4 == 0 and y > 0 else (POL if (x - cx) * (z - cz) == 0 else TILE))
    for (dx, dz, f) in ((2, 0, "west"), (-2, 0, "east"), (0, 2, "north"), (0, -2, "south")):
        for y in (12,):
            bp.set(cx + dx, y, cz + dz, stair(TILE_ST, f, "top"))
    bp.disk(cx, 13, cz, 3, BLACK)                # the brazier bowl with its fire
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            d = math.hypot(x - cx, z - cz)
            if 2.4 < d <= 3.4:
                bp.set(x, 14, z, BLACK_BR)
                bp.set(x, 15, z, GILD if (x + z) % 2 else slab("polished_blackstone_brick_slab"))
            elif d <= 2.4:
                bp.set(x, 14, z, LAVA)
    for (dx, dz) in ((3, 3), (-3, 3), (3, -3), (-3, -3)):
        c = ceil_y(cx + dx, cz + dz)
        bp.chain(cx + dx, 16, cz + dz, c)
        bp.set(cx + dx, 15, cz + dz, GILD)
    bp.set(cx, 1, cz - 8, MOD["waystone"])


def lava_rivers(bp):
    for side in (-1, 1):
        # the lava fall in the wall, behind a grate
        x = side * (HX + 1)
        for z in (20, 21):
            for y in range(1, 27):
                bp.set(x + side, y, z, LAVA)
                bp.set(x, y, z, "iron_bars" if y > 5 else LAVA)
                bp.set(x + side * 2, y, z, BLACK)
            for y in (5, 27):
                bp.set(x, y, z, GILD)
        for y in range(1, 28):
            for z in (19, 22):
                bp.set(x, y, z, POL if y % 4 else GILD)
        # the river channel to the hearth
        for xx in range(side * 5, side * (HX + 1) + side, side):
            for z in (20, 21):
                bp.set(xx, 0, z, LAVA)
                bp.set(xx, -1, z, BLACK)
            for z in (19, 22):
                bp.set(xx, 0, z, BLACK_BR)
        # bridges
        for bx in (side * 12, side * 24):
            for xx in (bx - 1, bx, bx + 1):
                for z in (20, 21):
                    bp.set(xx, 0, z, BRK)
                for z in (19, 22):
                    bp.set(xx, 1, z, BRK_WALL if xx == bx else slab("deepslate_brick_slab"))
            for z in (19, 22):
                bp.set(bx - 2, 1, z, BRK)
                bp.set(bx + 2, 1, z, BRK)
                bp.lantern(bx - 2, 2, z)


def avenue(bp):
    for z in range(14, Z1 + 1):
        for x in range(-4, 5):
            if math.hypot(x, z - 20) <= 7.4:
                continue
            bp.set(x, 0, z, GILD if abs(x) == 4 else ("chiseled_tuff_bricks" if z % 4 == 0 else "tuff_bricks")
                   if abs(x) <= 1 else "polished_tuff")
        if z % 5 == 0 and abs(z - 20) > 8:
            for side in (-1, 1):
                bp.set(side * 5, 1, z, POL)
                bp.set(side * 5, 2, z, POL_WALL)
                bp.set(side * 5, 3, z, POL_WALL)
                bp.lantern(side * 5, 4, z)


def railway(bp):
    rx = 9
    # station platform by the gate stairs
    for z in range(14, 19):
        for x in (rx - 2, rx - 1):
            bp.set(x, 1, z, slab("polished_deepslate_slab"))
    bp.set(rx, 1, 13, "polished_deepslate")
    bp.set(rx, 2, 13, "lever[face=floor,facing=south,powered=false]")
    for z in range(14, Z1 + 9):
        powered = z % 8 == 3
        bp.set(rx, 1, z, f"powered_rail[powered=false,shape=north_south,waterlogged=false]" if powered
               else "rail[shape=north_south,waterlogged=false]")
        bp.set(rx, 0, z, BRK if z <= Z1 else POL)
        if z in (20, 21):
            bp.set(rx, 0, z, BRK)
            bp.set(rx - 1, 0, z, BRK)
            bp.set(rx + 1, 0, z, BRK)
    bp.entity(rx, 1, 15, {"id": "minecraft:minecart"})
    bp.entity(rx, 1, 17, {"id": "minecraft:chest_minecart", "LootTable": LOOT + "dwarven_city"})
    # the mine tunnel in the south wall, its portal and the cave-in at its end
    for z in range(Z1 + 1, Z1 + 9):
        for x in range(rx - 2, rx + 3):
            for y in range(1, 6):
                inner = abs(x - rx) <= 1 and y <= 4 or abs(x - rx) <= 2 and y <= 3
                bp.set(x, y, z, "air" if inner else ROCK.pick(x, y, z))
        if z % 3 == 0:
            for y in range(1, 4):
                bp.set(rx - 2, y, z, "dark_oak_log[axis=y]")
                bp.set(rx + 2, y, z, "dark_oak_log[axis=y]")
            for x in range(rx - 2, rx + 3):
                bp.set(x, 4, z, "dark_oak_log[axis=x]")
            bp.lantern(rx + 1, 3, z, hanging=True)
    for (x, y) in ((rx - 1, 1), (rx, 1), (rx + 1, 1), (rx - 1, 2), (rx, 2), (rx + 1, 3), (rx, 3), (rx - 1, 4)):
        bp.set(x, y, Z1 + 8, "cobbled_deepslate" if (x + y) % 2 else "tuff")
    bp.set(rx, 1, Z1 + 7, "cobbled_deepslate")
    for y in range(1, 9):
        for x in range(rx - 4, rx + 5):
            frame = abs(x - rx) >= 3 or y >= 6
            if frame and y <= 8 and abs(x - rx) <= 4:
                bp.set(x, y, Z1 + 1, GILD if y == 6 and abs(x - rx) <= 3 else (TILE if abs(x - rx) == 4 else POL))
    bp.set(rx, 7, Z1 + 1, CHIS)


def building(bp, x0, x1, z0, z1, h, front_x, *, seed=0):
    """A dwarven hall: masonry walls with pilasters, a stepped crenellated roof, an arcaded front facing the
    avenue (at x = front_x), lanterns inside. Returns the interior box."""
    xs, xe = min(x0, x1), max(x0, x1)
    for x in range(xs, xe + 1):
        for z in range(z0, z1 + 1):
            edge = x in (xs, xe) or z in (z0, z1)
            for y in range(1, h + 1):
                if edge:
                    pil = (z - z0) % 4 == 0 or x in (xs, xe) and z in (z0, z1)
                    bp.set(x, y, z, TILE if pil else MASON.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, h + 1, z, POL)
            bp.set(x, 0, z, TILE if (x + z) % 2 else POL)
    # gilded band and corbel cornice
    for x in range(xs, xe + 1):
        for z in (z0, z1):
            bp.set(x, h, z, GILD)
    for z in range(z0, z1 + 1):
        for x in (xs, xe):
            bp.set(x, h, z, GILD)
    top = bp.pyramid_roof(xs, z0, xe, z1, h + 2, "waxed_cut_copper_stairs", overhang=1,
                          cap="waxed_cut_copper_slab[type=bottom,waterlogged=false]")
    for x in range(xs - 1, xe + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (xs - 1, xe + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, h + 1, z, stair(TILE_ST, _away(x - (xs + xe) / 2, 0) if x in (xs - 1, xe + 1)
                                          else _away(0, z - (z0 + z1) / 2), "top"))
    bp.set((xs + xe) // 2, top, (z0 + z1) // 2, GILD)
    bp.set((xs + xe) // 2, top + 1, (z0 + z1) // 2, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # arcaded front: three stepped arches
    sgn = 1 if front_x == xe else -1
    for z in range(z0 + 1, z1):
        k = (z - z0) % 4
        if k == 0:
            continue
        top = 5 if k == 2 else 4
        for y in range(1, top + 1):
            bp.set(front_x, y, z, "air")
    for z in range(z0, z1 + 1, 4):
        bp.set(front_x + sgn, 1, z, stair(TILE_ST, "west" if sgn > 0 else "east"))
        for y in range(1, h + 1):
            bp.set(front_x, y, z, TILE)
        bp.set(front_x + sgn, h - 1, z, stair(TILE_ST, "west" if sgn > 0 else "east", "top"))
    for z in range(z0 + 2, z1, 4):
        if bp.get(front_x, 1, z) == "minecraft:air":
            bp.set(front_x, h - 1, z, CHIS)
    for z in range(z0 + 2, z1 - 1, 4):
        bp.set((xs + xe) // 2, h, z, POL)
        bp.lantern((xs + xe) // 2, h - 1, z, hanging=True)
    return xs + 1, xe - 1, z0 + 1, z1 - 1


def forge(bp):
    xa, xb, za, zb = building(bp, -30, -14, 3, 15, 8, -14)
    # the great hearth against the back wall: a blackstone furnace with a lava belly and a chimney to the ceiling
    for z in range(6, 13):
        for y in range(1, 6):
            for x in (-29, -28, -27):
                edge = z in (6, 12) or y in (1, 5) or x == -29
                bp.set(x, y, z, DARK.pick(x, y, z) if edge else ("air" if y > 2 else LAVA))
        bp.set(-27, 3, z, "iron_bars" if 7 <= z <= 11 else BLACK_BR)
        bp.set(-27, 4, z, "iron_bars" if 7 <= z <= 11 else BLACK_BR)
        bp.set(-27, 2, z, BLACK_BR if z in (6, 12) else "air")
    for z in range(7, 12):
        bp.set(-27, 2, z, BLACK_BR)
        bp.set(-28, 2, z, LAVA)
        bp.set(-28, 1, z, BLACK)
    for x in range(-29, -26):
        for z in range(8, 11):
            for y in range(6, ceil_y(x, z) + 2):
                edge = x in (-29, -27) or z in (8, 10)
                bp.set(x, y, z, (GILD if y % 6 == 0 else BLACK_BR) if edge else "air")
    # anvils, smithing tables, grindstones, quench trough, blast furnaces
    for z in (5, 13):
        bp.set(-24, 1, z, "anvil[facing=east]")
        bp.set(-22, 1, z, "smithing_table")
        bp.set(-20, 1, z, "grindstone[face=floor,facing=east]")
    for z in (8, 9, 10):
        bp.set(-23, 1, z, "blast_furnace[facing=east,lit=false]")
        bp.set(-23, 2, z, "blast_furnace[facing=east,lit=false]" if z == 9 else BLACK_BR)
    bp.set(-19, 1, 8, "water_cauldron[level=3]")
    bp.set(-19, 1, 9, "water_cauldron[level=3]")
    bp.set(-19, 1, 10, "lava_cauldron")
    bp.chest(-17, 1, 4, "south", loot=LOOT + "dwarven_city_forge")
    bp.chest(-17, 1, 14, "north", loot=LOOT + "dwarven_city_forge")
    for z in (5, 13):
        bp.set(-25, 1, z, W + "deepslate_mithril_ore" if z == 5 else "raw_iron_block")
        bp.set(-26, 1, z, "raw_gold_block" if z == 5 else "raw_copper_block")


def smelter(bp):
    xa, xb, za, zb = building(bp, -30, -14, 24, 35, 7, -14)
    # two blast-furnace towers rising through the roof
    for (tx, tz) in ((-25, 28), (-25, 32)):
        top = 20
        for y in range(1, top + 1):
            for x in range(tx - 2, tx + 3):
                for z in range(tz - 2, tz + 3):
                    d = math.hypot(x - tx, z - tz)
                    if d <= 2.4:
                        if d > 1.4:
                            bp.set(x, y, z, GILD if y % 5 == 0 else ("copper_block" if y % 5 == 1 else BRK))
                        else:
                            bp.set(x, y, z, LAVA if y <= 2 else "air")
        for z in (tz - 1, tz, tz + 1):
            bp.set(tx + 2, 2, z, "iron_bars")
            bp.set(tx + 2, 3, z, "iron_bars")
        bp.set(tx + 2, 1, tz, BLACK_BR)
        bp.set(tx, 0, tz, BLACK)
        for x in range(tx - 1, tx + 2):
            for z in range(tz - 1, tz + 2):
                bp.set(x, 0, z, BLACK)
    # ore carts and crates of raw metal
    for (x, z, b) in ((-19, 26, "raw_iron_block"), (-19, 27, "raw_gold_block"), (-18, 26, "raw_copper_block"),
                      (-19, 33, W + "raw_mithril_block"), (-18, 33, "raw_iron_block"), (-19, 32, "coal_block")):
        bp.set(x, 1, z, b)
    bp.barrel(-16, 1, 34, "up", loot=LOOT + "dwarven_city_forge")
    bp.set(-21, 1, 30, "stonecutter[facing=east]")
    bp.set(-21, 1, 31, "crafting_table")


def tavern(bp):
    xa, xb, za, zb = building(bp, 14, 30, 3, 15, 8, 14)
    # long tables with benches, a bar of barrels, a hearth
    for z in (6, 11):
        for x in range(18, 26):
            bp.set(x, 1, z, "dark_oak_slab[type=top,waterlogged=false]")
            bp.set(x, 1, z - 1, stair("dark_oak_stairs", "north"))
            bp.set(x, 1, z + 1, stair("dark_oak_stairs", "south"))
        for x in (19, 22, 24):
            bp.set(x, 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    for z in range(4, 15):
        bp.set(28, 1, z, "barrel[facing=west,open=false]")
        bp.set(29, 1, z, "barrel[facing=up,open=false]")
        bp.set(29, 2, z, "barrel[facing=west,open=false]")
    bp.barrel(28, 2, 9, "up", loot=LOOT + "dwarven_city")
    for x in range(26, 27):
        for z in range(5, 14):
            bp.set(x, 1, z, "polished_deepslate_slab[type=top,waterlogged=false]" if z != 9 else "air")
    bp.set(22, 1, 14, "smoker[facing=north,lit=false]")
    bp.set(23, 1, 14, "cauldron")
    bp.set(21, 1, 14, "barrel[facing=up,open=false]")
    for x in (19, 24):
        bp.chain(x, 7, 8, 7)
        bp.set(x, 6, 8, W + "brass_chandelier")


def gem_hall(bp):
    xa, xb, za, zb = building(bp, 14, 30, 24, 35, 7, 14)
    for z in (26, 29, 32):
        bp.set(22, 1, z, "stonecutter[facing=west]")
        bp.set(23, 1, z, "polished_deepslate_slab[type=top,waterlogged=false]")
        bp.set(23, 2, z, "amethyst_cluster[facing=up,waterlogged=false]")
    # display cases: ore and gem blocks under glass
    for i, b in enumerate(("emerald_block", W + "mithril_block", "diamond_block", "amethyst_block", "lapis_block",
                           "gold_block")):
        x, z = 28, 25 + i * 2
        bp.set(x, 1, z, CHIS)
        bp.set(x, 2, z, b)
        bp.set(x, 3, z, "glass")
    bp.chest(17, 1, 25, "south", loot=LOOT + "dwarven_city")
    bp.chest(17, 1, 34, "north", loot=LOOT + "dwarven_city")
    bp.set(20, 1, 34, "grindstone[face=floor,facing=north]")


# ------------------------------------------------------------------ housing terraces
TUNNELS = []   # (side, zlo, zhi, ylo, yhi) rock carved by stairwells: no house there


def terraces(bp):
    for side in (-1, 1):
        sx = side
        # floor -> level 1: an outside stair along the wall at the south end
        for i in range(7):
            z = Z1 - i
            y = 1 + i
            for ax in (32, 33, 34):
                bp.set(sx * ax, y, z, stair(BRK_ST, "north"))
                for yy in range(1, y):
                    bp.set(sx * ax, yy, z, MASON.pick(sx * ax, yy, z))
            bp.set(sx * 31, y + 1, z, BRK_WALL)
            for yy in range(1, y + 1):
                bp.set(sx * 31, yy, z, MASON.pick(sx * 31, yy, z))
        spans = {LEVELS[0]: (2, Z1 - 7), LEVELS[1]: (2, Z1 - 7), LEVELS[2]: (2, Z1 - 7)}
        for L, (za, zb) in spans.items():
            for z in range(za, zb + 1):
                for ax in (32, 33, 34):
                    bp.set(sx * ax, L, z, TILE if ax == 32 else "polished_tuff")
                bp.set(sx * 31, L, z, POL)
                bp.set(sx * 31, L + 1, z, BRK if z % 4 == 0 else BRK_WALL)
                if z % 4 == 0:
                    bp.set(sx * 31, L + 2, z, "lantern[hanging=false,waterlogged=false]")
                    # stepped corbel under the walkway
                    bp.set(sx * 31, L - 1, z, stair(TILE_ST, "east" if sx > 0 else "west", "top"))
                    bp.set(sx * 32, L - 1, z, TILE)
                    bp.set(sx * 32, L - 2, z, stair(TILE_ST, "east" if sx > 0 else "west", "top"))
                    for ax in (33, 34):
                        bp.set(sx * ax, L - 1, z, TILE)
                        bp.set(sx * ax, L - 2, z, TILE)
                    bp.set(sx * 33, L - 3, z, stair(TILE_ST, "east" if sx > 0 else "west", "top"))
                    bp.set(sx * 34, L - 3, z, TILE)
            for ax in (31, 32, 33, 34):                 # closed north end
                bp.set(sx * ax, L + 1, za - 1, BRK_WALL if ax == 31 else "air")
            bp.set(sx * 31, L + 1, za, BRK)
            for ax in (32, 33, 34):
                bp.set(sx * ax, L + 1, za - 1, BRK_WALL)
                bp.set(sx * ax, L, za - 1, POL)
        # stairwells carved in the rock between the levels
        stairwell(bp, sx, LEVELS[0], 2, +1)                 # north end, rising south
        stairwell(bp, sx, LEVELS[1], Z1 - 7, -1)            # south end, rising north
        # houses on each level
        for L in LEVELS:
            for zc in (6, 12, 18, 24):
                if any(t[0] == sx and t[1] - 3 <= zc <= t[2] + 3 and t[3] - 4 <= L <= t[4] for t in TUNNELS):
                    continue
                house(bp, sx, L, zc)


def stairwell(bp, sx, L, zdoor, dirz):
    """From walkway level L at z = zdoor, into the wall, up 6 steps along z (direction dirz), out onto L + 6."""
    ax0 = HX + 1
    zs = [zdoor + dirz * (i + 1) for i in range(6)]
    TUNNEL_Z = sorted([zdoor] + zs + [zs[-1] + dirz])
    TUNNELS.append((sx, TUNNEL_Z[0], TUNNEL_Z[-1], L, L + 10))
    for z in TUNNEL_Z:
        for ax in range(ax0, ax0 + 4):
            for y in range(L - 1, L + 11):
                bp.set(sx * ax, y, z, MASON.pick(sx * ax, y, z))
    for ax in (ax0 + 1, ax0 + 2):
        for y in range(L + 1, L + 4):
            bp.set(sx * ax, y, zdoor, "air")
        bp.set(sx * ax, L, zdoor, POL)
        for i, z in enumerate(zs):
            y = L + 1 + i
            bp.set(sx * ax, y, z, stair(BRK_ST, "south" if dirz > 0 else "north"))
            for yy in range(y + 1, y + 5):
                bp.set(sx * ax, yy, z, "air")
        zt = zs[-1] + dirz
        bp.set(sx * ax, L + 6, zt, POL)
        for yy in range(L + 7, L + 10):
            bp.set(sx * ax, yy, zt, "air")
    # doorways in the wall face
    for y in range(L + 1, L + 4):
        bp.set(sx * ax0, y, zdoor, "air")
    for y in range(L + 7, L + 10):
        bp.set(sx * ax0, y, zs[-1] + dirz, "air")
    bp.set(sx * ax0, L + 6, zs[-1] + dirz, POL)
    for (y, z) in ((L + 4, zdoor), (L + 10, zs[-1] + dirz)):
        bp.set(sx * ax0, y, z, CHIS)
        bp.set(sx * (ax0 - 1), y, z, stair(TILE_ST, "west" if sx > 0 else "east", "top"))
    bp.lantern(sx * (ax0 + 3) - sx, L + 4, zs[2], hanging=True)
    bp.set(sx * (ax0 + 3) - sx, L + 5, zs[2], "air")


def house(bp, sx, L, zc):
    """A home cut into the cavern wall: framed door, two lit windows, a carved room with bed, hearth, table."""
    ax0 = HX + 1
    for ax in range(ax0, ax0 + 6):
        for z in range(zc - 3, zc + 4):
            for y in range(L, L + 6):
                inner = ax0 + 1 <= ax <= ax0 + 4 and zc - 2 <= z <= zc + 2 and L + 1 <= y <= L + 4
                if inner:
                    bp.set(sx * ax, y, z, "air")
                elif ax > ax0:
                    bp.set(sx * ax, y, z, MASON.pick(sx * ax, y, z) if y > L else TILE)
    for ax in range(ax0 + 1, ax0 + 5):
        for z in range(zc - 2, zc + 3):
            bp.set(sx * ax, L, z, "spruce_planks" if (ax + z) % 2 else "stripped_spruce_wood[axis=x]")
    # facade: door, frame, lintel, windows
    f = "west" if sx > 0 else "east"   # the door looks out to the cavern
    for y in range(L + 1, L + 5):
        for z in range(zc - 3, zc + 4):
            bp.set(sx * ax0, y, z, MASON.pick(sx * ax0, y, z))
    for y in (L + 1, L + 2):
        bp.set(sx * ax0, y, zc, "air")
    bp.door(sx * ax0, L + 1, zc, f, "dark_oak")
    for dz in (-1, 1):
        for y in (L + 1, L + 2, L + 3):
            bp.set(sx * ax0, y, zc + dz, POL)
    bp.set(sx * ax0, L + 3, zc, CHIS)
    for dz in (-1, 0, 1):
        bp.set(sx * ax0, L + 4, zc + dz, GILD if dz == 0 else TILE)
        bp.set(sx * (ax0 - 1), L + 4, zc + dz, stair(TILE_ST, "east" if sx < 0 else "west", "top"))
    for dz in (-2, 2):
        bp.set(sx * (ax0 - 1), L + 3, zc + dz, f"{'red' if (zc + L) % 2 else 'orange'}_wall_banner[facing={f}]")
    for dz in (-3, 3):
        bp.set(sx * ax0, L + 2, zc + dz, "iron_bars")
        bp.set(sx * ax0, L + 3, zc + dz, "iron_bars")
        bp.set(sx * (ax0 - 1), L + 1, zc + dz, stair(TILE_ST, "east" if sx < 0 else "west", "top"))
    # inside
    back = sx * (ax0 + 4)
    colour = ["red", "brown", "gray", "orange"][(zc + L) % 4]
    bp.bed(sx * (ax0 + 3), L + 1, zc - 2, "east" if sx > 0 else "west", colour)
    bp.set(back, L + 1, zc + 2, "furnace[facing=" + ("west" if sx > 0 else "east") + ",lit=false]")
    bp.set(back, L + 1, zc + 1, "barrel[facing=up,open=false]")
    bp.set(sx * (ax0 + 2), L + 1, zc + 2, "crafting_table")
    if (zc + L) % 3 == 0:
        bp.chest(back, L + 1, zc, "west" if sx > 0 else "east", loot=LOOT + "dwarven_city")
    else:
        bp.set(back, L + 1, zc, "bookshelf" if (zc + L) % 2 else "barrel[facing=up,open=false]")
    bp.set(sx * (ax0 + 2), L + 4, zc, CHIS)
    bp.set(sx * (ax0 + 2), L + 4, zc + 1, "air")
    bp.lantern(sx * (ax0 + 2), L + 4, zc + 1, hanging=True)
    bp.set(sx * (ax0 + 2), L + 5, zc + 1, TILE)


def dwarven_city(bp):
    TUNNELS.clear()
    cavern(bp)
    great_hall(bp)
    throne_room(bp)
    vault(bp)
    secret_way(bp)
    gate(bp)
    lava_rivers(bp)
    hearth(bp)
    avenue(bp)
    railway(bp)
    forge(bp)
    smelter(bp)
    tavern(bp)
    gem_hall(bp)
    terraces(bp)
    ceiling_details(bp)
    citizens(bp)


def citizens(bp):
    """The dwarves who never left (wf/denizens.py): smiths at the forge and smelter, brewers at the tavern, miners and
    gemcutters in the workshops, families in the wall houses, and guards in horned helms on the avenue."""
    v = dict(void_solid=True)
    zones = [
        ((-30, 1, 3), (-14, 9, 15), ["smith", "smith", "gemcutter"], "forge"),
        ((-30, 1, 24), (-14, 8, 35), ["smith", "miner"], "forge"),
        ((14, 1, 3), (30, 9, 15), ["brewer", "brewer", "miner"], "kitchen"),
        ((14, 1, 24), (30, 8, 35), ["miner", "gemcutter"], "workshop"),
    ]
    for i, (a, b, people, theme) in enumerate(zones):
        INT.populate(bp, people, region=(a, b), seed=i, folk="dwarf", **v)
        if i == 2:
            # the Dwarf Elder hands out contracts by the tavern hearth (wf/npcs.py)
            INT.quest_npc_in(bp, "dwarf_elder", region=(a, b), seed=1, **v)
        INT.decorate(bp, dict(INT.THEMES[theme], banners=["black", "yellow", "gray"]), seed=i, region=(a, b), **v)
    houses = ((-HX - 6, 0, Z0 - 2), (-HX - 1, 30, Z1 + 2)), ((HX + 1, 0, Z0 - 2), (HX + 6, 30, Z1 + 2))
    for i, h in enumerate(houses):
        INT.populate(bp, ["miner", "brewer", "smith", "gemcutter"][i * 2:i * 2 + 2], region=h, seed=10 + i,
                     folk="dwarf", **v)
        INT.decorate(bp, dict(INT.THEMES["home"], centre=None), seed=10 + i, region=h, min_area=6, **v)
    # the city watch: guards on the avenue and by the great hall (they fight whatever comes out of the dark)
    denizens.guards(bp, "dwarf", [(-4, 1, 20), (4, 1, 8), (4, 1, 30)], **v)
    INT.decorate(bp, dict(INT.THEMES["hall"], banners=["black", "yellow", "gray"]), seed=20,
                 region=((-40, -10, -60), (40, 20, -1)), **v)


register(StructureDef(
    "dwarven_city", "overworld", ["#minecraft:is_overworld"],
    [Piece("city", dwarven_city)],
    spacing=80, separation=32, adaptation="none", height=("uniform", -58, -54), processors="aging",
    step="underground_structures", max_distance=110, foundation=False,
    # the dwarves still live here: no natural monster spawns (the sealed vault keeps its skeleton knights)
    peaceful=True,
    title_fr="Cité naine des profondeurs", title_en="Deep Dwarven City"))
