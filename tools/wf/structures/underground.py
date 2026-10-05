"""Underground / deep dark structures (placed at fixed depths, encapsulated in rock).

  dwarven_forge   a fan-vaulted dwarven hall behind a carved gate guarded by two colossal statues,
                  with a great forge, lava falls, barracks, a sealed vault and a hidden smithy cellar
  crystal_grotto  a giant geode bristling with amethyst and lithite spires, a crystal-cutter's
                  workshop on calcite terraces, bridges over a glowing chasm
  sealed_lab      a deep-dark research complex: blast door, observation gallery over containment
                  cells, control room, archive and a sculk-eaten specimen vault
"""
import math
import random

from .. import interior as I
from ..arch import Palette, stair
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB
from . import lair_forge_king
from . import lair_crystal_spider

DEEP = ["#minecraft:is_overworld"]

# Brasshaven deep blocks
LB = "brasshaven:lithite_bricks"
LBS = "brasshaven:lithite_brick_stairs"
LBSL = "brasshaven:lithite_brick_slab"
LBW = "brasshaven:lithite_brick_wall"
LC = "brasshaven:lithite_block"          # glowing crystal
LORE = "brasshaven:lithite_ore"
GT = "brasshaven:gilded_trim"            # gold-banded dark stone

PB = "polished_blackstone_bricks"
PBS = "polished_blackstone_brick_stairs"
PBW = "polished_blackstone_brick_wall"

AIR = "minecraft:air"
DIRS4 = (("north", 0, -1), ("south", 0, 1), ("east", 1, 0), ("west", -1, 0))

# full block -> its stair, used to corbel stepped ceilings into smooth curves
STAIR_OF = {
    "brasshaven:lithite_bricks": LBS,
    "minecraft:deepslate_tiles": "deepslate_tile_stairs",
    "minecraft:deepslate_bricks": "deepslate_brick_stairs",
    "minecraft:polished_deepslate": "polished_deepslate_stairs",
    "minecraft:cobbled_deepslate": "cobbled_deepslate_stairs",
    "minecraft:polished_blackstone_bricks": PBS,
    "minecraft:polished_blackstone": "polished_blackstone_stairs",
    "minecraft:tuff_bricks": "tuff_brick_stairs",
    "minecraft:polished_tuff": "polished_tuff_stairs",
    "minecraft:tuff": "tuff_stairs",
    "minecraft:calcite": None,
    "minecraft:prismarine_bricks": "prismarine_brick_stairs",
}


def _air(bp, x, y, z):
    return bp.get(x, y, z) == AIR


def soften(bp, x0, y0, z0, x1, y1, z1, floor=False):
    """Turn stepped ceilings (or floors with floor=True) into smooth curves: every air cell
    under (over) a solid block that also touches a solid block sideways gets a stair."""
    todo = []
    vy = -1 if floor else 1
    half = "bottom" if floor else "top"
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(y0, y1 + 1):
                if not _air(bp, x, y, z) or not STAIR_OF.get(bp.get(x, y + vy, z)):
                    continue
                for f, dx, dz in DIRS4:
                    s = STAIR_OF.get(bp.get(x + dx, y, z + dz))
                    if s:
                        todo.append((x, y, z, s, f))
                        break
    for x, y, z, s, f in todo:
        bp.set(x, y, z, stair(s, f, half))


def pointed_h(u, a, spring, k=1.5):
    """Height of a pointed (gothic) arch of half-width a at offset u, or None outside it."""
    u = abs(u)
    if u > a:
        return None
    r = a * k
    return spring + math.sqrt(max(0.0, r * r - (u + r - a) ** 2))


def rock_shell(bp, inside, x0, y0, z0, x1, y1, z1, pal, thick=2):
    """Clear an organic cavity (inside(x,y,z) -> bool) to air and wrap it in a rock shell."""
    cells = set()
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if inside(x, y, z):
                    cells.add((x, y, z))
    for (x, y, z) in cells:
        bp.set(x, y, z, "air")
    for (x, y, z) in cells:
        for dx in range(-thick, thick + 1):
            for dy in range(-thick, thick + 1):
                for dz in range(-thick, thick + 1):
                    p = (x + dx, y + dy, z + dz)
                    if p not in cells and p not in bp.blocks:
                        bp.set(*p, pal.pick(*p))
    return cells


def hanging(bp, x, y_ceiling, z, drop, soul=False):
    """Lantern on a chain hanging `drop` blocks below a ceiling block at y_ceiling."""
    bp.chain(x, y_ceiling - drop + 1, z, y_ceiling - 1)
    bp.lantern(x, y_ceiling - drop, z, hanging=True, soul=soul)


def crystal(bp, x, y, z, h, up=True, block=LC, tip="amethyst_cluster"):
    """A spire of glowing crystal: `h` blocks tall (or hanging down) with a cluster tip."""
    d = 1 if up else -1
    for k in range(h):
        bp.set(x, y + d * k, z, block)
    if tip:
        bp.set(x, y + d * h, z, f"{tip}[facing={'up' if up else 'down'},waterlogged=false]")


# ============================================================ Dwarven forge
FX0, FX1 = 1, 63              # hall interior x
FZ = 15                       # hall interior |z|
F_TOP = 26                    # vault crown cap
PIL_X = (6, 16, 26, 36, 46)   # pillar rows at z = +-8
DWARF_WALL = Palette({"deepslate_bricks": 6, "deepslate_tiles": 3, LB: 2, "cracked_deepslate_bricks": 1},
                     seed=41, scale=1.4)
DWARF_VAULT = Palette({"deepslate_tiles": 5, LB: 2, "deepslate_bricks": 2}, seed=42, scale=1.3)
CAVE_ROCK = Palette({"deepslate": 6, "tuff": 3, "cobbled_deepslate": 2, "smooth_basalt": 1}, seed=43, scale=4,
                    accent=LORE, accent_chance=0.03)


def dwarf_pillar(bp, cx, cz, top, gem=True, cap=12):
    """Massive octagonal pillar: blackstone plinth, fluted lithite/deepslate shaft with gilded
    bands and glowing gems, corbelled capital; the shaft runs on into the fan vault."""
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            ax, az = abs(dx), abs(dz)
            x, z = cx + dx, cz + dz
            if bp.get(x, 1, z) is None and bp.get(x, 0, z) is None:
                continue  # never build into the rock (half pilasters stay flush with the wall)
            # plinth
            bp.set(x, 1, z, "chiseled_polished_blackstone" if ax == 3 and az == 3 else PB)
            if max(ax, az) <= 2:
                bp.set(x, 2, z, PB)
            elif max(ax, az) == 3 and min(ax, az) <= 2:
                f = ("west" if dx > 0 else "east") if ax == 3 else ("north" if dz > 0 else "south")
                bp.set(x, 2, z, stair(PBS, f))
            if ax + az > 3 or max(ax, az) > 2:
                continue
            for y in range(3, top + 1):
                if y == 3 or y == cap - 1:
                    b = GT
                elif ax + az == 3:
                    b = "polished_blackstone"
                elif (ax == 2 and dz == 0) or (az == 2 and dx == 0):
                    b = LC if (gem and y == 7) else LB
                elif max(ax, az) == 2:
                    b = "deepslate_tiles"
                else:
                    b = "deepslate"
                if y == cap and (ax == 2 or az == 2):
                    b = "chiseled_deepslate"
                bp.set(x, y, z, b)
    # capital: corbel ring of upside-down stairs
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            ax, az = abs(dx), abs(dz)
            if max(ax, az) == 3 and min(ax, az) <= 1 and _air(bp, cx + dx, cap + 1, cz + dz):
                f = ("west" if dx > 0 else "east") if ax == 3 else ("north" if dz > 0 else "south")
                bp.set(cx + dx, cap + 1, cz + dz, stair(PBS, OPP[f], "top"))


OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def dwarf_statue(bp, cx, cz, base_y, face, outer):
    """Colossal dwarf guardian (25 blocks with pedestal) carved in tuff, calcite beard, gilded
    blackstone armour. face = east/west (the way it looks), outer = +1/-1 along z: hammer side."""
    fdx = 1 if face == "east" else -1
    back = OPP[face]

    def P(f, u, y, b):
        bp.set(cx + fdx * f, base_y + y, cz + u, b)

    body = Palette({"tuff_bricks": 4, "polished_tuff": 2, "tuff": 1}, seed=7, scale=2)
    beard = ("calcite", "polished_diorite", "calcite")
    side_out = "south" if outer > 0 else "north"
    side_in = OPP[side_out]
    # pedestal 9x9 with gilded band and a glowing lithite plaque
    for f in range(-4, 5):
        for u in range(-4, 5):
            for y in range(-1, 4):
                b = GT if y == 2 else PB
                if y == 3:
                    b = "chiseled_polished_blackstone" if abs(f) == 4 or abs(u) == 4 else "polished_blackstone"
                P(f, u, y, b)
    for u in (-1, 0, 1):
        P(4, u, 1, LC)
    # boots with upturned toes
    for u in (-2, -1, 1, 2):
        for f in range(-1, 4):
            P(f, u, 4, "polished_blackstone")
        P(4, u, 4, stair("polished_blackstone_stairs", back))
        for f in range(-1, 2):
            P(f, u, 5, "polished_blackstone")
        for f in (-1, 0, 1):
            P(f, u, 6, body.pick(f, 6, u))
    # mail skirt and torso
    for y in range(7, 16):
        for f in range(-2, 4):
            for u in range(-3, 4):
                if (f == -2 or f == 3) and abs(u) == 3:
                    continue
                b = body.pick(f, y, u)
                if y == 7:
                    b = "iron_block" if (u + f) % 2 == 0 else "polished_blackstone"
                if y == 10:
                    b = GT
                P(f, u, y, b)
    for u in range(-3, 4):
        P(4, u, 7, stair("polished_blackstone_stairs", back))   # flared hem
    P(4, 0, 10, "gold_block")                                     # belt buckle
    # shoulders, arms, fists
    for s_ in (-1, 1):
        for f in (-1, 0, 1, 2):
            P(f, 4 * s_, 15, "polished_blackstone")
            P(f, 4 * s_, 16, GT)
        P(f, 5 * s_, 15, stair("polished_blackstone_stairs", side_in if s_ == outer else side_out, "top"))
        for y in range(11, 15):
            for f in (0, 1):
                P(f, 4 * s_, y, body.pick(f, y, 4 * s_))
        P(2, 4 * s_, 11, "polished_tuff")
        P(2, 4 * s_, 10, "polished_tuff")
    # war hammer planted beside the outer fist
    hu = 5 * outer
    for y in range(4, 20):
        P(2, hu, y, "polished_blackstone_wall")
    for f in (1, 2, 3):
        for y in (19, 20, 21):
            P(f, hu, y, "gold_block" if (f == 2 and y == 20) else "iron_block")
    P(2, hu, 22, GT)
    # head with glowing eyes, heavy brow and nose
    for y in range(16, 21):
        for f in range(-1, 4):
            for u in range(-2, 3):
                if f == -1 and abs(u) == 2:
                    continue
                P(f, u, y, "polished_tuff")
    for u in (-1, 1):
        P(3, u, 18, LC)
    P(4, 0, 18, "polished_tuff")
    P(4, 0, 17, stair("polished_tuff_stairs", back, "top"))
    for u in range(-2, 3):
        if u:
            P(4, u, 19, stair("polished_blackstone_stairs", back, "top"))
    # beard: wide, layered, braided with gold
    widths = {17: 2, 16: 3, 15: 3, 14: 3, 13: 3, 12: 2, 11: 2, 10: 1, 9: 1, 8: 0}
    for y, w in widths.items():
        for u in range(-w, w + 1):
            if y == 17 and u == 0:
                continue
            b = beard[(u + y) % 3]
            if y == 11 and abs(u) == 2:
                b = "gold_block"
            if y == 17:
                b = stair("diorite_stairs", back, "top")   # moustache
            P(4, u, y, b)
            if abs(u) <= 1 and 11 <= y <= 15:
                P(5, u, y, beard[(u + y + 1) % 3])
    P(4, 0, 7, "gold_block")
    P(5, 0, 10, stair("diorite_stairs", back))
    # helmet: gilded rim, blackstone dome, golden crest, curling horns
    for f in range(-2, 5):
        for u in range(-3, 4):
            if f == -2 and abs(u) == 3:
                continue
            P(f, u, 21, GT)
    for f in range(-1, 4):
        for u in range(-2, 3):
            P(f, u, 22, PB)
    for f in range(0, 3):
        for u in range(-1, 2):
            P(f, u, 23, PB if u else "gold_block")
    P(1, 0, 24, "gold_block")
    for s_ in (-1, 1):
        P(1, 4 * s_, 21, "bone_block[axis=z]")
        P(1, 5 * s_, 22, "bone_block[axis=y]")
        P(1, 5 * s_, 23, "bone_block[axis=y]")
        P(1, 4 * s_, 24, "bone_block[axis=z]")
        P(1, 5 * s_, 21, "bone_block[axis=z]")


def dwarven_forge(bp):
    X0, X1, Z = FX0, FX1, FZ
    # ---------------------------------------------------------------- hall shell
    bp.fill(-3, -3, -Z - 3, X1 + 3, 0, Z + 3, "deepslate_tiles")
    for x in range(-3, X1 + 4):
        for z in range(-Z - 3, Z + 4):
            for y in range(1, F_TOP + 6):
                if X0 <= x <= X1 and -Z <= z <= Z:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, DWARF_WALL.pick(x, y, z))
    # ---------------------------------------------------------------- floor
    for x in range(X0, X1 + 1):
        for z in range(-Z, Z + 1):
            az = abs(z)
            if az <= 1:
                b = "chiseled_polished_blackstone" if x % 5 == 1 else "polished_blackstone_bricks"
            elif az == 2:
                b = "polished_deepslate"
            elif az <= 5:
                b = "polished_deepslate" if (x + az) % 4 == 0 else "deepslate_tiles"
            else:
                b = "polished_deepslate" if ((x // 2) + (z // 2)) % 2 == 0 else "deepslate_bricks"
            if x in PIL_X and az <= 6:
                b = "polished_blackstone_bricks"  # transverse floor bands
            bp.set(x, 0, z, b)
    # rune medallion between the 3rd and 4th pillar pairs
    mx = 31
    for x in range(mx - 5, mx + 6):
        for z in range(-5, 6):
            d = math.hypot(x - mx, z)
            if 3.6 < d <= 4.4:
                bp.set(x, 0, z, "chiseled_polished_blackstone")
            elif 4.4 < d <= 5.2:
                bp.set(x, 0, z, "polished_blackstone")
            elif d <= 1.2:
                bp.set(x, 0, z, "gold_block")
            elif 1.2 < d <= 2.3:
                bp.set(x, 0, z, LB)
    bp.set(mx, 0, 0, LC)
    # ---------------------------------------------------------------- vaults (basilica in dwarven style)
    # nave |z|<=6 under a stepped angular vault, arcades in the pillar rows (|z| 7..9),
    # aisles |z| 10..15, and a taller forge crossing for x >= 49.
    crown = {}
    for x in range(X0, X1 + 1):
        for z in range(-Z, Z + 1):
            az = abs(z)
            u = ((x - 6) % 10) - 5          # offset from the arcade bay centre
            if x >= 47:
                h = min(31, int(16 + 1.5 * (16 - az)))
                if x in (47, 48):
                    h -= 2
            elif az <= 6:
                h = min(28, 19 + 2 * (7 - az))
                if x in PIL_X and az <= 5:
                    h -= 1
            elif az <= 9:
                h = {0: 16, 1: 15, 2: 13}.get(abs(u), 1)
            else:
                h = 15 + int(2 * min(az - 9.5, 15.5 - az))
                if x in PIL_X:
                    h = {10: 15, 11: 16, 12: 17, 13: 16}.get(az, 15)
            crown[(x, z)] = h
            for y in range(h, F_TOP + 6):
                bp.set(x, y, z, DWARF_VAULT.pick(x, y, z))
    # trims: transverse ribs and arcade rings in blackstone, ridge of glowing lithite
    for (x, z), h in crown.items():
        az = abs(z)
        u = ((x - 6) % 10) - 5
        if (x in PIL_X and (az <= 5 or az >= 10)) or (x in (47, 48)):
            bp.set(x, h, z, PB)
        elif 7 <= az <= 9 and abs(u) <= 2:
            bp.set(x, h, z, PB if az != 8 else "polished_blackstone")
        elif az <= 1 and x < 47:
            bp.set(x, h, z, LC if (x % 5 == 1 and z == 0) else "chiseled_polished_blackstone" if z == 0 else PB)
    # nave face of the arcade walls: gilded string course and glowing clerestory lights
    for x in range(X0, 47):
        u = ((x - 6) % 10) - 5
        for s in (-1, 1):
            if bp.get(x, 17, 7 * s) not in (None, AIR):
                bp.set(x, 17, 7 * s, GT)
                bp.set(x, 17, 9 * s, GT)
            if u == 0:
                for y in (19, 20):
                    bp.set(x, y, 7 * s, LC)
                bp.set(x, 18, 7 * s, "chiseled_polished_blackstone")
                bp.set(x, 21, 7 * s, "chiseled_polished_blackstone")
    # ---------------------------------------------------------------- pillars & wall pilasters
    for x in PIL_X:
        for z in (-8, 8):
            dwarf_pillar(bp, x, z, 19)
        for z in (-16, 16):
            dwarf_pillar(bp, x, z, 16, gem=False)
    for z in (-8, 8):
        dwarf_pillar(bp, 0, z, 19, gem=False)
    for z in (-16, 16):
        dwarf_pillar(bp, 56, z, 18, gem=False)
    # ---------------------------------------------------------------- side walls: niches, friezes, lava runnels
    bays = [(9, 13), (19, 23), (29, 33), (39, 43), (49, 53), (59, 63)]
    for side in (-1, 1):
        zw, zb = 16 * side, 17 * side   # wall face, niche back
        for i, (a, b) in enumerate(bays):
            c = (a + b) // 2
            door = (side == -1 and c == 21) or (side == 1 and c == 31)
            for x in range(a, b + 1):
                bp.set(x, 1, zw, PB)
                bp.set(x, 2, zw, "polished_blackstone")
                bp.set(x, 12, zw, GT)
                bp.set(x, 13, zw, "chiseled_deepslate" if x % 2 else "chiseled_polished_blackstone")
                bp.set(x, 14, zw, "polished_deepslate")
            if door:
                continue
            # tall pointed niche, recessed one block
            for x in range(c - 1, c + 2):
                top = 10 if x == c else 9
                for y in range(3, top + 1):
                    bp.set(x, y, zw, "air")
                    bp.set(x, y, zb, "deepslate_tiles")
                bp.set(x, 3, zw, "polished_blackstone_slab[type=bottom,waterlogged=false]")
            bp.set(c - 1, 9, zw, stair("polished_blackstone_stairs", "west", "top"))
            bp.set(c + 1, 9, zw, stair("polished_blackstone_stairs", "east", "top"))
            for x in (c - 2, c + 2):
                for y in range(3, 11):
                    bp.set(x, y, zw, "polished_blackstone" if y < 10 else GT)
            if i % 2 == 0:
                # lithite geode in the niche
                for y in range(3, 9):
                    bp.set(c, y, zb, LC if y % 2 else "amethyst_block")
                bp.set(c - 1, 4, zw, f"amethyst_cluster[facing=up,waterlogged=false]")
                bp.set(c + 1, 4, zw, f"large_amethyst_bud[facing=up,waterlogged=false]")
                bp.set(c, 4, zw, LC)
                bp.set(c, 5, zw, "amethyst_cluster[facing=up,waterlogged=false]")
            else:
                # carved ancestor relief with glowing rune eyes
                for y in range(4, 9):
                    bp.set(c, y, zb, "chiseled_deepslate" if y != 7 else LC)
                bp.set(c - 1, 7, zb, "polished_deepslate")
                bp.set(c + 1, 7, zb, "polished_deepslate")
                bp.set(c, 4, zw, "decorated_pot[facing=" + ("south" if side < 0 else "north") +
                       ",waterlogged=false,cracked=false]")
            # lava runnel along the wall, behind a low rail
            for x in range(a, b + 1):
                bp.set(x, 0, 15 * side, "lava")
                bp.set(x, -1, 15 * side, PB)
                bp.set(x, 1, 14 * side, PBW)
            bp.set(c, 2, 14 * side, "lantern[hanging=false,waterlogged=false]")
    # ---------------------------------------------------------------- chandeliers & arcade lanterns
    for x in (11, 21, 31, 41):
        dwarf_chandelier(bp, x, crown[(x, 0)], 0, crown[(x, 0)] - 15)
    for x in (11, 21, 31, 41):
        for z in (-8, 8):
            hanging(bp, x, crown[(x, z)], z, 2)
        for z in (-12, 12):
            hanging(bp, x, crown[(x, z)], z, 5)
    # ---------------------------------------------------------------- the great forge (east end)
    great_forge(bp)
    # ---------------------------------------------------------------- west gate & court
    gate_court(bp)
    # ---------------------------------------------------------------- barracks (north) & vault (south)
    barracks(bp)
    vault(bp)
    soften(bp, X0, 12, -Z, X1, F_TOP + 5, Z)
    # guards: one in the hall before the forge, one in the barracks
    bp.spawner(44, 1, 0, MOB["ruin_walker"])
    # the King's Stair down to the Forge King's crucible (lair_forge_king.py)
    lair_forge_king.build(bp)
    # an abandoned dwarven forge: tools left on the benches, crates of ore, dust and webs
    I.decorate(bp, dict(I.THEMES["forge"], ceiling=None, loot_barrels=1, rubble=["cobbled_deepslate", "deepslate",
                                                                                    "tuff", "gravel"]),
               seed=1, void_solid=True, loot=LOOT + "dwarven_vault")
    I.decorate(bp, dict(I.THEMES["ruin"], rubble=["cobbled_deepslate", "deepslate", "tuff", "gravel"]), seed=2,
               void_solid=True, density=0.2)


def dwarf_chandelier(bp, x, yc, z, drop):
    """Great iron ring chandelier: chain from the vault, lithite heart, lanterns on four arms."""
    yb = yc - drop
    bp.chain(x, yb + 1, z, yc - 1)
    bp.set(x, yb, z, LC)
    bp.set(x, yb - 1, z, "chiseled_polished_blackstone")
    bp.lantern(x, yb - 2, z, hanging=True)
    for _, dx, dz in DIRS4:
        for k in (1, 2, 3):
            bp.set(x + dx * k, yb, z + dz * k, PBW)
        bp.lantern(x + dx * 3, yb - 1, z + dz * 3, hanging=True)
        bp.set(x + dx * 3, yb + 1, z + dz * 3, "candle[candles=4,lit=true,waterlogged=false]")
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        bp.set(x + dx * 2, yb, z + dz * 2, PBW)
        bp.set(x + dx, yb, z + dz, PBW)
        bp.lantern(x + dx * 2, yb - 1, z + dz * 2, hanging=True)


def great_forge(bp):
    # raised dais
    for x in range(51, 64):
        for z in range(-15, 16):
            if bp.get(x, 1, z) == AIR:
                bp.set(x, 1, z, "polished_blackstone" if (x + z) % 3 else "polished_deepslate")
    for z in range(-13, 14):
        if bp.get(51, 1, z) == "minecraft:polished_blackstone" or bp.get(51, 1, z) == "minecraft:polished_deepslate":
            bp.set(51, 1, z, stair("polished_blackstone_stairs", "east"))
    # hearth block with glowing firebox
    for x in range(57, 64):
        for z in range(-7, 8):
            for y in range(2, 9):
                bp.set(x, y, z, PB if y < 8 else GT)
    for x in range(57, 63):
        for z in range(-3, 4):
            for y in range(2, 7):
                bp.set(x, y, z, "air")
    for x in range(58, 63):
        for z in range(-3, 4):
            bp.set(x, 1, z, "lava")
            bp.set(x, 0, z, PB)
    for z in range(-3, 4):
        bp.set(57, 1, z, "polished_blackstone")
        bp.set(57, 2, z, PBW)
    for z in (-3, 3):
        bp.set(57, 6, z, stair(PBS, "south" if z < 0 else "north", "top"))
    for z in range(-4, 5):
        bp.set(56, 7, z, stair(PBS, "west", "top"))
    bp.set(57, 7, 0, "gold_block")
    # tapering hood and chimney
    for i in range(0, 12):
        y = 9 + i
        hz = max(3, 8 - i // 2)
        xa = min(59, 55 + i // 2)
        for x in range(xa, 64):
            for z in range(-hz, hz + 1):
                edge = x == xa or abs(z) == hz
                bp.set(x, y, z, PB if edge or y < 11 else "air")
                if edge and (y - 9) % 4 == 3:
                    bp.set(x, y, z, GT)
        # interior smoke shaft
        for x in range(xa + 1, 63):
            for z in range(-hz + 1, hz):
                bp.set(x, y, z, "air")
    for y in range(21, F_TOP + 12):
        for x in range(59, 64):
            for z in range(-3, 4):
                edge = x in (59, 63) or abs(z) == 3
                bp.set(x, y, z, PB if edge else "air")
    for x in range(58, 64):
        for z in (-4, 4):
            bp.set(x, 20, z, stair(PBS, "north" if z > 0 else "south", "top"))
    for z in range(-4, 5):
        bp.set(58, 20, z, stair(PBS, "east", "top"))
    for y in range(2, 21):  # back wall of the firebox / shaft
        for z in range(-3, 4):
            bp.set(63, y, z, PB)
    # glowing rune on the hood front
    for dz, dy in ((0, 0), (-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2), (0, -2)):
        x = 55 + (12 + dy - 9) // 2
        bp.set(x, 12 + dy, dz, LC)
    # hood lip: chains with lanterns
    for z in (-7, -4, 4, 7):
        hanging(bp, 54 if abs(z) == 4 else 55, 9, z, 2)
    # anvils, furnaces, quench troughs
    for z in (-2, 2):
        bp.set(54, 2, z, "anvil[facing=north]")
    bp.set(54, 2, 0, "smithing_table")
    for z in (-6, -5, 5, 6):
        bp.set(56, 2, z, "blast_furnace[facing=west,lit=true]")
        bp.set(56, 3, z, "blast_furnace[facing=west,lit=true]" if abs(z) == 6 else "polished_blackstone_slab[type=bottom,waterlogged=false]")
    for z in (-9, 9):
        bp.set(53, 2, z, "water_cauldron[level=3]")
        bp.set(53, 2, z + (1 if z < 0 else -1), "grindstone[face=floor,facing=east]")
    bp.barrel(62, 2, -9, "up", LOOT + "dwarven_mine")
    bp.barrel(62, 2, -8, "up")
    bp.barrel(62, 3, -9, "west")
    for z in (8, 9):
        bp.set(62, 2, z, "raw_iron_block" if z == 8 else "raw_gold_block")
    bp.set(61, 2, 9, "coal_block")
    bp.set(61, 3, 9, "raw_copper_block")
    # lava falls pouring from slots in the east wall into basins
    for s in (-1, 1):
        zc = 12 * s
        for y in range(2, 23):
            bp.set(64, y, zc, "lava")
        for z in (zc - 1, zc + 1):
            for y in range(2, 23):
                bp.set(64, y, z, PB)
        bp.set(64, 1, zc, PB)
        bp.set(63, 23, zc, stair(PBS, "west", "top"))
        bp.set(64, 23, zc, "chiseled_polished_blackstone")
        for x in range(60, 64):
            for z in range(zc - 2, zc + 3):
                if abs(z) <= 15:
                    bp.set(x, 1, z, "lava")
                    bp.set(x, 0, z, PB)
        for x in range(59, 64):
            for z in (zc - 3 * s, ):
                bp.set(x, 2, z, PBW)
        for z in range(zc - 3, zc + 4):
            if abs(z) <= 15:
                bp.set(59, 2, z, PBW)
                bp.set(59, 1, z, PB)


def gate_court(bp):
    """Cavern before the west gate: carved portal, two colossal dwarves rising out of lava."""
    def inside(x, y, z):
        if y < 1 or x > -4:
            return False
        p = 2.6
        n = math.sin(x * 0.7 + z * 0.3) * 0.04 + math.cos(z * 0.5 - y * 0.4) * 0.04
        v = (abs(x + 4) / 21.0) ** p + (abs(z) / 26.0) ** p + (y / 38.0) ** p
        return v <= 1 + n
    rock_shell(bp, inside, -26, 1, -28, -4, 40, 28, CAVE_ROCK)
    # floor: lava lake with a central causeway
    for x in range(-26, -3):
        for z in range(-28, 29):
            if inside(x, 1, z) or inside(x, 2, z):
                if abs(z) <= 3:
                    bp.set(x, 0, z, "polished_blackstone_bricks" if abs(z) < 3 else "polished_blackstone")
                    bp.set(x, -1, z, PB)
                elif abs(z) == 4:
                    bp.set(x, 0, z, PB)
                    bp.set(x, 1, z, PBW)
                    bp.set(x, -1, z, PB)
                else:
                    bp.set(x, 0, z, "lava")
                    bp.set(x, -1, z, "lava")
                    bp.set(x, -2, z, "magma_block")
    for x in range(-24, -7, 4):
        for s in (-1, 1):
            bp.set(x, 1, 4 * s, "polished_blackstone_bricks")
            bp.set(x, 2, 4 * s, PBW)
            bp.set(x, 3, 4 * s, "lantern[hanging=false,waterlogged=false]")
    # ---------------- the portal: stepped pointed archivolts carved into a projecting block
    for x in range(-7, -2):
        for z in range(-9, 10):
            for y in range(0, 25):
                b = {-7: PB, -6: LB, -5: "polished_blackstone", -4: LB, -3: PB}[x]
                if y == 13:
                    b = GT
                bp.set(x, y, z, b)
    orders = [(-7, 7.5, 12), (-6, 6.5, 11), (-5, 5.5, 10), (-4, 4.5, 9)]
    for x, a, spring in orders:
        for z in range(-9, 10):
            for y in range(1, 25):
                h = pointed_h(z, a, spring)
                if h is not None and (y <= spring or y <= h):
                    bp.set(x, y, z, "air")
    for x in range(-3, 1):  # the door passage through the wall
        for z in range(-3, 4):
            h = pointed_h(z, 3.5, 7)
            for y in range(1, 13):
                if h is not None and y <= h:
                    bp.set(x, y, z, "air")
        for z in range(-3, 4):
            bp.set(x, 0, z, "polished_blackstone_bricks")
    # raised portcullis teeth and iron-studded doors swung open against the jambs
    for z in range(-2, 3):
        bp.set(-2, 10 if abs(z) < 2 else 9, z, "iron_bars")
    for z in (-3, 3):
        for y in range(1, 8):
            bp.set(-1, y, z, "dark_oak_planks" if y % 3 else "iron_block")
    # crest above the portal: dwarf-king mask with glowing eyes
    for z in range(-4, 5):
        for y in range(18, 25):
            bp.set(-8, y, z, "polished_blackstone" if abs(z) < 4 or y > 20 else PB)
    for z in (-2, 2):
        bp.set(-9, 22, z, LC)
    bp.set(-9, 21, 0, stair("polished_blackstone_stairs", "east", "top"))
    for z in range(-3, 4):
        bp.set(-9, 23, z, stair(PBS, "east", "top"))
        bp.set(-8, 25, z, GT)
    for z in range(-2, 3):
        bp.set(-9, 20, z, stair("polished_tuff_stairs", "east", "top"))
        bp.set(-9, 19, z, "polished_tuff" if abs(z) < 2 else "air")
    bp.set(-9, 18, 0, "polished_tuff")
    bp.set(-9, 17, 0, stair("polished_tuff_stairs", "east", "top"))
    for s in (-1, 1):
        bp.set(-8, 25, 5 * s, "bone_block[axis=z]")
        bp.set(-8, 26, 6 * s, "bone_block[axis=y]")
        bp.set(-8, 27, 6 * s, "end_rod[facing=up]")
    for s in (-1, 1):
        for z in range(10 * s, 23 * s, s):
            for y in range(1, 30):
                if bp.get(-4, y, z) == AIR:
                    b = "deepslate_tiles" if abs(z) % 4 else PB
                    if y in (13, 26):
                        b = GT
                    bp.set(-4, y, z, b)
    # ---------------- the two guardians
    for s in (-1, 1):
        dwarf_statue(bp, -13, 14 * s, 0, "west", -s)
    # stalactites and crystals in the cavern roof
    rng = random.Random(4)
    for _ in range(60):
        x, z = rng.randint(-22, -6), rng.randint(-20, 20)
        for y in range(34, 5, -1):
            if bp.get(x, y, z) == AIR and bp.get(x, y + 1, z) not in (None, AIR):
                if rng.random() < 0.3:
                    crystal(bp, x, y, z, rng.randint(1, 3), up=False)
                else:
                    L = rng.randint(1, 4)
                    for k in range(L):
                        th = "tip" if k == L - 1 else ("frustum" if k == L - 2 else "middle")
                        if L == 1:
                            th = "tip"
                        bp.set(x, y - k, z, f"pointed_dripstone[thickness={th},vertical_direction=down,waterlogged=false]")
                break
    # approach tunnel climbing west
    for x in range(-32, -23):
        k = max(0, -25 - x)
        for z in range(-3, 4):
            for y in range(k, k + 7):
                bp.set(x, y, z, CAVE_ROCK.pick(x, y, z))
        for z in range(-2, 3):
            bp.set(x, k, z, stair("polished_blackstone_brick_stairs", "west") if x < -25 else PB)
            for y in range(k + 1, k + 6):
                bp.set(x, y, z, "air")
    bp.lantern(-29, 8, 2, hanging=True)


def barracks(bp):
    x0, x1, z0, z1 = 9, 35, -32, -20
    pal = Palette({"deepslate_bricks": 5, LB: 1, "deepslate_tiles": 2}, seed=51, scale=1.5)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, -1, z, "deepslate_tiles")
            for y in range(0, 10):
                inner = x0 < x < x1 and z0 < z < z1
                if not inner:
                    bp.set(x, y, z, pal.pick(x, y, z))
                    continue
                dz = z - (z0 + z1) / 2
                h = 5 + 3.2 * math.sqrt(max(0, 1 - (dz / 6.0) ** 2))
                if y == 0:
                    bp.set(x, y, z, "spruce_planks" if (x + z) % 7 else "dark_oak_planks")
                elif y < h:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, pal.pick(x, y, z))
    # transverse arches of blackstone every 5 blocks
    for x in range(x0 + 3, x1, 5):
        for z in range(z0 + 1, z1):
            for y in range(4, 10):
                if bp.get(x, y, z) != AIR and bp.get(x, y - 1, z) == AIR:
                    bp.set(x, y, z, PB)
                    break
        for y in range(1, 4):
            bp.set(x, y, z0 + 1, "polished_blackstone")
            bp.set(x, y, z1 - 1, "polished_blackstone")
        hanging(bp, x, 8, -26, 2)
    # corridor from the hall
    for x in range(20, 23):
        for z in range(-19, -15):
            for y in range(1, 5):
                bp.set(x, y, z, "air")
            bp.set(x, 0, z, PB)
    for z in range(-20, -15):
        for y in range(1, 6):
            bp.set(19, y, z, PB)
            bp.set(23, y, z, PB)
        bp.set(21, 5, z, PB)
        bp.set(20, 5, z, stair(PBS, "east", "top"))
        bp.set(22, 5, z, stair(PBS, "west", "top"))
    bp.set(21, 6, -15, LC)
    bp.door(21, 1, -20, "north", "dark_oak")
    bp.set(20, 1, -20, "air")
    bp.set(22, 1, -20, "air")
    for x in (20, 22):
        for y in (1, 2):
            bp.set(x, y, -20, "iron_bars")
    # bunks along the north wall
    colors = ["brown", "red", "gray", "brown", "black", "red", "gray", "brown"]
    for i, x in enumerate(range(x0 + 2, x1 - 1, 3)):
        if x > x1 - 2:
            break
        bp.bed(x, 1, z0 + 2, "north", colors[i % len(colors)])
        bp.set(x, 3, z0 + 1, "dark_oak_slab[type=top,waterlogged=false]")
        bp.set(x, 3, z0 + 2, "dark_oak_slab[type=top,waterlogged=false]")
        bp.bed(x, 4, z0 + 2, "north", colors[(i + 3) % len(colors)])
        if x + 1 < x1:
            for y in range(1, 5):
                bp.set(x + 1, y, z0 + 1, "dark_oak_log[axis=y]")
            bp.set(x + 1, 1, z0 + 2, "dark_oak_fence")
            bp.lantern(x + 1, 5, z0 + 1)
            if x + 2 < x1:
                bp.barrel(x + 2, 1, z0 + 1, "up", LOOT + "dwarven_mine" if i in (1, 5) else None)
                bp.set(x + 2, 2, z0 + 1, "candle[candles=2,lit=true,waterlogged=false]")
    # feasting table with benches
    zt = -25
    for x in range(13, 31):
        bp.set(x, 1, zt, "dark_oak_slab[type=top,waterlogged=false]" if x % 4 else "dark_oak_planks")
        bp.set(x, 1, zt - 1, stair("spruce_stairs", "south"))
        bp.set(x, 1, zt + 1, stair("spruce_stairs", "north"))
    for x, item in ((14, "candle[candles=3,lit=true,waterlogged=false]"), (18, "cake[bites=2]"),
                    (22, "candle[candles=4,lit=true,waterlogged=false]"), (26, "decorated_pot[facing=north,waterlogged=false,cracked=false]"),
                    (29, "candle[candles=2,lit=true,waterlogged=false]")):
        bp.set(x, 2, zt, item)
    # hearth on the east wall
    for z in range(-28, -21):
        for y in range(1, 9):
            bp.set(x1 - 1, y, z, "bricks" if abs(z + 25) < 3 else PB)
    for z in range(-26, -23):
        for y in (1, 2):
            bp.set(x1 - 1, y, z, "air")
    bp.set(x1 - 1, 1, -25, "campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")
    bp.set(x1 - 2, 3, -25, GT)
    for z in (-26, -24):
        bp.set(x1 - 2, 3, z, stair(PBS, "west", "top"))
    # weapon racks and a map table at the west end
    for z in (-29, -27, -23):
        bp.entity(x0 + 1, 1, z, {"id": "minecraft:armor_stand", "Rotation": [270.0, 0.0]})
    bp.set(x0 + 2, 1, -21, "cartography_table")
    bp.set(x0 + 3, 1, -21, "lectern[facing=south,has_book=false,powered=false]")
    # secret: a crumbling patch of wall at the west end hides the master smith's cellar
    for y in (1, 2):
        bp.set(x0, y, -25, "cracked_deepslate_bricks")
    bp.set(x0, 3, -25, "chiseled_deepslate")
    for x in range(1, x0):
        for y in (1, 2):
            bp.set(x, y, -25, "air")
        bp.set(x, 0, -25, "cobbled_deepslate")
    for x in range(0, 8):
        for z in range(-31, -27):
            for y in range(0, 6):
                edge = x in (0, 7) or z in (-31, -28) or y in (0, 5)
                bp.set(x, y, z, "cobbled_deepslate" if edge else "air")
    for z in (-28, -27, -26):
        for y in (1, 2):
            bp.set(4, y, z, "air")
        bp.set(4, 0, z, "cobbled_deepslate")
        bp.set(3, 1, z, "cobbled_deepslate")
        bp.set(5, 1, z, "cobbled_deepslate")
    bp.chest(6, 1, -30, "west", LOOT + "dwarven_vault")
    bp.set(1, 1, -30, "smithing_table")
    bp.set(1, 1, -29, "anvil[facing=north]")
    bp.set(3, 1, -30, "gold_block")
    bp.set(4, 1, -30, "raw_gold_block")
    bp.set(3, 4, -29, LC)
    bp.spawner(22, 1, -28, MOB["ruin_walker"])


def vault(bp):
    x0, x1, z0, z1 = 22, 40, 20, 34
    pal = Palette({"polished_blackstone_bricks": 4, "deepslate_tiles": 2, LB: 2}, seed=52)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, -1, z, PB)
            for y in range(0, 11):
                inner = x0 < x < x1 and z0 < z < z1
                if not inner:
                    bp.set(x, y, z, pal.pick(x, y, z))
                    continue
                dx = x - (x0 + x1) / 2
                h = 6 + 3.5 * math.sqrt(max(0, 1 - (dx / 8.0) ** 2))
                if y == 0:
                    bp.set(x, y, z, "gold_block" if (x % 4 == 3 and z % 4 == 3) else
                           "chiseled_polished_blackstone" if (x + z) % 2 == 0 else "polished_blackstone")
                elif y < h:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, pal.pick(x, y, z))
    cx = (x0 + x1) // 2
    # passage through the hall wall: round vault door with an iron door and a call button
    for z in range(16, 21):
        for x in range(30, 33):
            for y in range(1, 4):
                bp.set(x, y, z, "air")
            bp.set(x, 0, z, PB)
    for x in range(27, 36):
        for y in range(0, 9):
            d = math.hypot(x - 31, y - 3.5)
            if 3.0 < d <= 4.6:
                bp.set(x, y, 15, GT if d > 3.8 else "iron_block")
    bp.set(31, 8, 15, "gold_block")
    bp.door(31, 1, 18, "north", "iron")
    for x in (30, 32):
        for y in (1, 2):
            bp.set(x, y, 18, "iron_block")
    bp.set(30, 2, 15, "polished_blackstone_button[face=wall,facing=north,powered=false]")
    bp.set(32, 2, 19, "polished_blackstone_button[face=wall,facing=south,powered=false]")
    # treasure: gold hoard, ore stacks, two great chests on a dais
    bp.fill(cx - 2, 1, z1 - 3, cx + 2, 1, z1 - 2, "polished_blackstone_bricks")
    bp.chest(cx - 1, 2, z1 - 2, "north", LOOT + "dwarven_vault")
    bp.chest(cx + 1, 2, z1 - 2, "north", LOOT + "dwarven_vault")
    bp.set(cx, 2, z1 - 2, LC)
    bp.set(cx, 3, z1 - 2, "amethyst_cluster[facing=up,waterlogged=false]")
    for x, z, h in ((x0 + 2, z1 - 2, 3), (x0 + 3, z1 - 2, 2), (x0 + 2, z1 - 3, 2), (x0 + 4, z1 - 2, 1),
                    (x1 - 2, z1 - 2, 3), (x1 - 3, z1 - 2, 2), (x1 - 2, z1 - 3, 1), (x1 - 2, z0 + 2, 2)):
        for y in range(1, h + 1):
            bp.set(x, y, z, "gold_block" if (x + y) % 3 else "raw_gold_block")
    for x in (x0 + 2, x0 + 3):
        bp.set(x, 1, z0 + 2, "raw_iron_block")
    bp.set(x0 + 2, 2, z0 + 2, "raw_iron_block")
    bp.set(x0 + 2, 1, z0 + 3, "emerald_block")
    for x in (x0 + 5, x1 - 5):
        for y in range(1, 9):
            bp.set(x, y, z0 + 7, GT if y in (1, 8) else LC if y == 5 else "polished_blackstone")
    hanging(bp, cx, 9, (z0 + z1) // 2, 3)
    for x in (cx - 4, cx + 4):
        hanging(bp, x, 8, z0 + 4, 2)


register(StructureDef(
    "dwarven_forge", "overworld", DEEP, [Piece("forge", dwarven_forge)],
    spacing=30, separation=10, step="underground_structures", adaptation="encapsulate",
    height=("uniform", -58, -36), spawns=[(MOB["ruin_walker"], 10, 1, 2)],
    title_fr="Forge naine", title_en="Dwarven Forge"))


# ============================================================ Crystal grotto
GEODE = (19.0, 17.5, 18.0)      # cavity radii scale (x, y, z)
COPPER_PIL = ("waxed_oxidized_cut_copper", "waxed_oxidized_copper_grate", "waxed_weathered_cut_copper")


def _geode_r(x, y, z):
    """Pseudo-radius (cavity edge = 15) with a gentle lumpy noise."""
    rx, ry, rz = GEODE
    v = math.sqrt((x / rx) ** 2 + (y / ry) ** 2 + (z / rz) ** 2) * 16
    return v + 0.6 * math.sin(x * 0.55 + y * 0.3) + 0.5 * math.cos(z * 0.45 - x * 0.2) + 0.4 * math.sin(y * 0.7 + z * 0.3)


def _chasm(z):
    """Centre line and half-width of the crystal chasm crossing the geode north-south."""
    return 1.5 * math.sin(z / 5.0), 4.5 + 3.0 * math.exp(-(z / 5.0) ** 2)


def grotto_floor(x, z):
    """Terrace top y at (x, z), or None inside the chasm."""
    c, w = _chasm(z)
    if math.hypot(x - c, z) <= 3.2:
        return -7                       # the island pinnacle
    if abs(x - c) <= w:
        return None
    if x < c:
        e = (c - w) - x
        return -7 if e < 3.5 else -5 if e < 7 else -3
    e = x - (c + w)
    return -7 if e < 4.5 else -5


def crystal_spire(bp, x, y, z, d, length, r0, block, tip=None):
    """Tapered crystal growing from (x,y,z) along direction d; only fills air (or rock)."""
    n = math.sqrt(sum(c * c for c in d))
    ux, uy, uz = (c / n for c in d)
    end = None
    for i in range(int(length * 2) + 1):
        t = i / 2.0
        r = r0 * (1 - t / length) ** 0.9 + 0.25
        px, py, pz = x + ux * t, y + uy * t, z + uz * t
        rr = int(math.ceil(r))
        for ox in range(-rr, rr + 1):
            for oy in range(-rr, rr + 1):
                for oz in range(-rr, rr + 1):
                    q = (round(px) + ox, round(py) + oy, round(pz) + oz)
                    if math.dist(q, (px, py, pz)) <= r:
                        cur = bp.get(*q)
                        if cur in (AIR, "minecraft:amethyst_block", "minecraft:calcite", "minecraft:tuff",
                                   "minecraft:smooth_basalt", "minecraft:budding_amethyst"):
                            bp.set(*q, block)
        end = (round(px), round(py), round(pz))
    if tip and end:
        face = "up" if uy > 0.5 else "down" if uy < -0.5 else None
        if face:
            tx, ty, tz = end[0], end[1] + (1 if face == "up" else -1), end[2]
            if bp.get(tx, ty, tz) == AIR:
                bp.set(tx, ty, tz, f"{tip}[facing={face},waterlogged=false]")


def crystal_grotto(bp):
    rng = random.Random(77)
    strata = ("calcite", "calcite", "tuff", "dripstone_block", "calcite", "smooth_basalt")
    # ---------------------------------------------------------------- geode shell and cavity
    for x in range(-23, 24):
        for y in range(-21, 21):
            for z in range(-22, 23):
                r = _geode_r(x, y, z)
                if r < 15.0:
                    fl = grotto_floor(x, z)
                    if fl is not None and y <= fl:
                        if y == fl:
                            b = "calcite"
                        else:   # banded strata glinting with lithite veins
                            b = strata[(y + 30) % len(strata)]
                            if rng.random() < 0.06:
                                b = LORE if rng.random() < 0.8 else LC
                    else:
                        b = "air"
                elif r < 16.6:
                    b = "budding_amethyst" if rng.random() < 0.1 else "amethyst_block"
                elif r < 17.6:
                    b = "calcite"
                elif r < 19.0:
                    b = "smooth_basalt"
                else:
                    continue
                bp.set(x, y, z, b)
    # terrace lips: calcite steps where a terrace drops to the next one
    for x in range(-20, 21):
        for z in range(-19, 20):
            fl = grotto_floor(x, z)
            if fl is None or bp.get(x, fl, z) != "minecraft:calcite":
                continue
            for f, dx, dz in DIRS4:
                n = grotto_floor(x + dx, z + dz)
                if n is not None and n == fl - 2 and bp.get(x + dx, n + 1, z + dz) == AIR:
                    bp.set(x + dx, n + 1, z + dz, stair("polished_diorite_stairs" if (x + z) % 3 else
                                                        "diorite_stairs", OPP[f]))
    # ---------------------------------------------------------------- crystal spires
    spires = [  # (start, direction, length, radius, block)
        ((-3, -17, -3), (0.1, 1, 0.05), 13, 2.4, LC), ((5, -17, 6), (-0.2, 1, -0.1), 11, 2.0, LC),
        ((-1, -17, 12), (0.2, 1, -0.3), 9, 1.6, "amethyst_block"), ((2, -17, -12), (-0.1, 1, 0.3), 10, 1.8, LC),
        ((1, -16, -7), (0.4, 1, 0), 7, 1.3, "amethyst_block"), ((-3, -16, 7), (-0.3, 1, 0.2), 7, 1.2, LC),
        ((4, -16, -2), (0.3, 1, 0.3), 6, 1.1, "amethyst_block"), ((-4, -16, 1), (-0.4, 1, 0.1), 6, 1.0, LC),
        ((-6, 17, -4), (0.1, -1, 0.1), 10, 2.0, LC), ((5, 17, 3), (-0.15, -1, 0), 10, 2.2, "amethyst_block"),
        ((0, 17, -10), (0, -1, 0.25), 8, 1.6, LC), ((9, 14, -8), (-0.3, -1, 0.2), 8, 1.5, LC),
        ((-10, 14, 8), (0.25, -1, -0.2), 8, 1.5, "amethyst_block"), ((-1, 17, 9), (0.1, -1, -0.2), 7, 1.3, LC),
        ((12, 13, 6), (-0.3, -1, -0.1), 6, 1.2, LC), ((12, 14, -3), (-0.3, -1, 0.1), 6, 1.2, LC),
        ((17, 0, -8), (-1, 0.5, 0.3), 8, 1.7, LC), ((-15, 2, -14), (0.8, 0.3, 0.7), 8, 1.6, "amethyst_block"),
        ((15, -2, 12), (-1, 0.6, -0.4), 8, 1.6, "amethyst_block"), ((-4, 0, 17), (0.2, 0.4, -1), 8, 1.5, LC),
        ((7, 4, -17), (-0.3, 0.2, 1), 7, 1.4, LC), ((17, 6, 4), (-1, -0.2, 0), 7, 1.4, "amethyst_block"),
        ((8, -9, -10), (-0.5, 0.4, 0.4), 6, 1.2, LC), ((7, -10, 9), (-0.6, 0.5, -0.3), 6, 1.2, LC),
        ((-7, -10, -9), (0.6, 0.5, 0.3), 5, 1.1, "amethyst_block"),
    ]
    for (sx, sy, sz), d, L, r, blk in spires:
        crystal_spire(bp, sx, sy, sz, d, L, r, blk, tip="amethyst_cluster")
    # the island's heart crystal: a cluster of three lithite pillars
    for (ox, oz), d, L, r in (((0, 0), (0, 1, 0), 9, 1.6), ((1, 1), (0.5, 1, 0.4), 6, 1.0), ((-1, -1), (-0.5, 1, -0.3), 5, 0.9)):
        crystal_spire(bp, ox, -6, oz, d, L, r, LC, tip="amethyst_cluster")
    # ---------------------------------------------------------------- bridges over the chasm
    # copper bridge to the island (west) and a crystal arch (east), deck at y -7
    for x in range(-9, 10):
        for z in (-1, 0, 1):
            c, w = _chasm(z)
            if grotto_floor(x, z) is None:
                if x < 0:
                    bp.set(x, -7, z, "waxed_weathered_cut_copper" if z == 0 else "waxed_weathered_cut_copper_slab[type=top,waterlogged=false]")
                    bp.set(x, -8, z, stair("waxed_weathered_cut_copper_stairs", "south" if z < 0 else "north", "top") if z else "waxed_weathered_copper_grate")
                else:
                    bp.set(x, -7, z, "calcite")
                    bp.set(x, -8, z, "amethyst_block")
                    if z == 0:
                        bp.set(x, -9, z, "amethyst_block")
                for y in range(-6, -3):
                    if bp.get(x, y, z) not in (AIR,):
                        bp.set(x, y, z, "air")
        if grotto_floor(x, 0) is None or abs(x) in (3, 4):
            for z in (-2, 2):
                if x < 0:
                    bp.set(x, -7, z, "waxed_weathered_cut_copper")
                    bp.set(x, -6, z, "waxed_copper_bars")
                else:
                    bp.set(x, -7, z, "calcite")
                    bp.set(x, -6, z, "amethyst_cluster[facing=up,waterlogged=false]" if x % 2 else "air")
    for x in (-8, -4):
        for z in (-2, 2):
            bp.set(x, -6, z, "waxed_oxidized_copper_grate")
            bp.set(x, -5, z, "waxed_copper_lantern[hanging=false,waterlogged=false]")
    # a sagging chain bridge further south (z = 11)
    zb = 11
    c, w = _chasm(zb)
    xa, xb = int(math.floor(c - w)) - 1, int(math.ceil(c + w)) + 1
    for x in range(xa, xb + 1):
        t = (x - xa) / max(1, xb - xa)
        sag = round(1.6 * math.sin(math.pi * t))
        y = -7 - sag
        for z in (zb - 1, zb, zb + 1):
            bp.set(x, y, z, "dark_oak_slab[type=top,waterlogged=false]" if z != zb else "dark_oak_planks")
            for yy in range(y + 1, y + 4):
                if bp.get(x, yy, z) not in (AIR,):
                    bp.set(x, yy, z, "air")
        for z in (zb - 2, zb + 2):
            bp.set(x, y + 1, z, "waxed_copper_chain[axis=x,waterlogged=false]")
    for x in (xa - 1, xb + 1):
        for z in (zb - 2, zb + 2):
            for y in range(-6, -2):
                bp.set(x, y, z, COPPER_PIL[y % 3])
            bp.set(x, -2, z, "waxed_copper_bulb[lit=true,powered=false]")
    # ---------------------------------------------------------------- crystal-cutter's workshop (west upper terrace)
    yf = -3
    pil = [(-10, -6), (-10, 6), (-10, 0), (-15, -6), (-15, 6)]
    for (px, pz) in pil:
        bp.set(px, yf, pz, "waxed_chiseled_copper")
        for y in range(yf + 1, 5):
            bp.set(px, y, pz, COPPER_PIL[(y + 9) % 3] if y not in (yf + 1, 4) else "waxed_chiseled_copper")
        bp.set(px, 5, pz, "waxed_copper_bulb[lit=true,powered=false]")
    # copper canopy (lean-to against the geode wall)
    for x in range(-18, -8):
        for z in range(-8, 9):
            y = 6 + (-9 - x) // 3
            if _geode_r(x, y, z) >= 15:
                continue
            if x == -9:
                bp.set(x, y, z, stair("waxed_weathered_cut_copper_stairs", "west"))
                bp.set(x, y - 1, z, stair("waxed_oxidized_cut_copper_stairs", "east", "top"))
            elif z in (-8, 8):
                bp.set(x, y, z, stair("waxed_weathered_cut_copper_stairs", "south" if z < 0 else "north", "top"))
            else:
                bp.set(x, y, z, "waxed_weathered_cut_copper" if (x + z) % 4 else "waxed_weathered_copper_grate")
    for (x, z) in ((-12, -3), (-12, 3), (-13, 0)):
        y = 6 + (-9 - x) // 3
        bp.set(x, y - 1, z, "waxed_copper_chain[axis=y,waterlogged=false]")
        bp.set(x, y - 2, z, "waxed_copper_lantern[hanging=true,waterlogged=false]")
    # benches and tools along the back
    wy = yf + 1
    bench = [("stonecutter[facing=east]", -16, -5), ("grindstone[face=floor,facing=east]", -16, -4),
             ("smithing_table", -16, -3), ("crafting_table", -16, -2), ("cartography_table", -16, 2),
             ("lectern[facing=east,has_book=false,powered=false]", -16, 3), ("fletching_table", -16, 4)]
    for spec, x, z in bench:
        bp.set(x, wy, z, spec)
    bp.chest(-16, wy, 0, "east", LOOT + "crystal_grotto")
    bp.set(-16, wy, -1, "barrel[facing=up,open=false]")
    bp.set(-16, wy, 1, "barrel[facing=up,open=false]")
    bp.set(-16, wy + 1, -1, "decorated_pot[facing=east,waterlogged=false,cracked=false]")
    bp.set(-16, wy + 1, 1, "amethyst_cluster[facing=up,waterlogged=false]")
    # the crystal lathe: a lithite heart on a copper grate, lightning rods as spindles
    bp.set(-13, wy, 0, "waxed_copper_grate")
    bp.set(-13, wy + 1, 0, LC)
    bp.set(-13, wy + 2, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in (-1, 1):
        bp.set(-13, wy + 1, z, f"lightning_rod[facing={'north' if z < 0 else 'south'},powered=false,waterlogged=false]")
        bp.set(-13, wy, z, "waxed_cut_copper")
    bp.set(-12, wy, 0, "stonecutter[facing=west]")
    # display cases of tinted glass with specimens
    for z in (-6, 6):
        for x in (-13, -12):
            bp.set(x, wy, z, "waxed_chiseled_copper")
            bp.set(x, wy + 1, z, "tinted_glass" if x == -12 else LC)
        bp.set(-12, wy + 1, z, "glass")
        bp.set(-12, wy + 2, z, "waxed_cut_copper_slab[type=bottom,waterlogged=false]")
        bp.set(-13, wy + 2, z, "amethyst_cluster[facing=up,waterlogged=false]")
    # a cot and the copper golem assistant
    bp.bed(-14, wy, -4, "north", "purple")
    bp.set(-11, wy, 4, "waxed_copper_golem_statue[copper_golem_pose=sitting,facing=east,waterlogged=false]")
    bp.set(-11, wy, -3, "decorated_pot[facing=east,waterlogged=false,cracked=false]")
    for x in range(-15, -10):
        for z in range(-5, 6):
            if bp.get(x, yf, z) == "minecraft:calcite" and (x + z) % 2 == 0:
                bp.set(x, yf, z, "polished_diorite")
    # ---------------------------------------------------------------- silverfish nest in the terrace face
    bp.spawner(-8, -5, -9, "minecraft:silverfish")
    for (x, y, z) in ((-8, -5, -10), (-9, -5, -9), (-8, -4, -9)):
        bp.set(x, y, z, "infested_deepslate[axis=y]" if y == -4 else "infested_stone")
    # ---------------------------------------------------------------- exit tunnel east, with a mine cart track
    for x in range(10, 31):
        for z in range(-2, 3):
            for y in range(-6, 0):
                inside = abs(z) <= 1 and -5 <= y <= -2
                if inside:
                    bp.set(x, y, z, "air")
                elif bp.get(x, y, z) in (None, "minecraft:smooth_basalt", "minecraft:calcite", "minecraft:amethyst_block",
                                         "minecraft:budding_amethyst"):
                    if _geode_r(x, y, z) >= 15 or x > 20:
                        bp.set(x, y, z, "tuff" if (x + y) % 4 else "deepslate")
        bp.set(x, -6, 0, "calcite")
        for z in (-1, 1):
            bp.set(x, -6, z, "calcite")
        bp.set(x, -5, 0, "rail[shape=east_west,waterlogged=false]")
        if x % 4 == 0 and x > 12:
            for z in (-1, 1):
                for y in (-5, -4, -3):
                    bp.set(x, y, z, COPPER_PIL[0] if y < -3 else "waxed_chiseled_copper")
            bp.set(x, -2, -1, "waxed_cut_copper")
            bp.set(x, -2, 0, "waxed_cut_copper")
            bp.set(x, -2, 1, "waxed_cut_copper")
            bp.set(x, -3, 0, "waxed_copper_lantern[hanging=true,waterlogged=false]")
    bp.entity(18, -5, 0, {"id": "minecraft:minecart"})
    # ---------------------------------------------------------------- secret: a sealed geode pocket behind the north wall
    px, py, pz = -8, 2, -19
    for x in range(px - 5, px + 6):
        for y in range(py - 5, py + 6):
            for z in range(pz - 5, pz + 6):
                d = math.dist((x, y, z), (px, py, pz))
                if d <= 2.0:
                    bp.set(x, y, z, "air")
                elif d <= 2.9:
                    bp.set(x, y, z, LC if (x + y + z) % 3 == 0 else "amethyst_block")
                elif d <= 3.6 and bp.get(x, y, z) is None:
                    bp.set(x, y, z, "calcite")
                elif d <= 4.3 and bp.get(x, y, z) is None:
                    bp.set(x, y, z, "smooth_basalt")
    bp.set(px, py - 2, pz, "calcite")
    bp.chest(px, py - 1, pz, "south", LOOT + "crystal_grotto")
    for z in range(pz + 2, pz + 6):     # the giveaway: a tinted peephole glowing in the wall
        if bp.get(px, py, z) not in (AIR,) and _geode_r(px, py, z) >= 15:
            bp.set(px, py, z, "tinted_glass")
    # ---------------------------------------------------------------- crystal growth on every exposed amethyst face
    faces = (("up", 0, 1, 0), ("down", 0, -1, 0), ("north", 0, 0, -1), ("south", 0, 0, 1),
             ("east", 1, 0, 0), ("west", -1, 0, 0))
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] not in ("minecraft:amethyst_block", "minecraft:budding_amethyst") or rng.random() > 0.3:
            continue
        order = list(faces)
        rng.shuffle(order)
        for face, dx, dy, dz in order:
            if bp.get(x + dx, y + dy, z + dz) == AIR:
                kind = rng.choice(["amethyst_cluster", "large_amethyst_bud", "medium_amethyst_bud", "amethyst_cluster"])
                bp.set(x + dx, y + dy, z + dz, f"{kind}[facing={face},waterlogged=false]")
                break
    # the Crystal Stair down to the Crystal Matriarch's nest (lair_crystal_spider.py)
    lair_crystal_spider.build(bp)
    I.decorate(bp, "mine", seed=1, void_solid=True, density=0.2, rugs=False, centre=False)


register(StructureDef(
    "crystal_grotto", "overworld", DEEP, [Piece("grotto", crystal_grotto)],
    spacing=26, separation=8, step="underground_structures", adaptation="none",
    height=("uniform", -58, -20), processors="none",
    title_fr="Grotte de cristal", title_en="Crystal Grotto"))


# ============================================================ Sealed laboratory (deep dark)
LAB_WALL = Palette({"polished_deepslate": 5, "deepslate_tiles": 3, "cracked_deepslate_tiles": 1}, seed=61, scale=1.5)
LAB_PANEL = Palette({"smooth_stone": 4, "polished_diorite": 1}, seed=62, scale=2)


def vein(**faces):
    f = {k: "false" for k in ("down", "up", "north", "south", "east", "west")}
    f.update({k: "true" for k in faces})
    return "sculk_vein[" + ",".join(f"{k}={v}" for k, v in f.items()) + ",waterlogged=false]"


def lab_room(bp, x0, z0, x1, z1, h, floor="polished_deepslate", panel=True):
    """Walls (deepslate frame, pale lab panels inside), floor grid, ceiling with light strips."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, -1, z, "deepslate_tiles")
            bp.set(x, h, z, LAB_WALL.pick(x, h, z))
            bp.set(x, h + 1, z, "deepslate_tiles")
            for y in range(0, h):
                if edge:
                    bp.set(x, y, z, LAB_WALL.pick(x, y, z))
                elif y == 0:
                    bp.set(x, y, z, floor if (x + z) % 2 else "deepslate_tiles")
                else:
                    bp.set(x, y, z, "air")
    if panel:
        # pale panels on the inner wall faces between a dark skirting and a dark frieze
        for x in range(x0 + 1, x1):
            for z, d in ((z0, 1), (z1, -1)):
                for y in range(2, h - 1):
                    bp.set(x, y, z, LAB_PANEL.pick(x, y, z) if (x - x0) % 4 else "polished_deepslate")
        for z in range(z0 + 1, z1):
            for x in (x0, x1):
                for y in range(2, h - 1):
                    bp.set(x, y, z, LAB_PANEL.pick(x, y, z) if (z - z0) % 4 else "polished_deepslate")


def hazard_frame(bp, plane, axis, c, y0, half, height):
    """Yellow/black hazard stripes around an opening (axis 'x': opening spans z, wall at x=plane)."""
    for u in range(c - half - 1, c + half + 2):
        for y in range(y0, y0 + height + 2):
            ring = u in (c - half - 1, c + half + 1) or y == y0 + height + 1
            if not ring:
                continue
            b = "yellow_concrete" if (u + y) % 2 else "black_concrete"
            bp.set(*((plane, y, u) if axis == "x" else (u, y, plane)), b)


def spread_sculk(bp, cx, cz, radius, seed, y_floor=0, region=None):
    """Sculk creeping out from (cx, cz): floor turns to sculk, veins climb walls, sensors sprout."""
    rng = random.Random(seed)
    for x in range(cx - radius, cx + radius + 1):
        for z in range(cz - radius, cz + radius + 1):
            if region and not (region[0] <= x <= region[2] and region[1] <= z <= region[3]):
                continue
            d = math.hypot(x - cx, z - cz) + rng.uniform(-1.5, 1.5)
            if d > radius:
                continue
            p = 1.0 - d / radius
            floor = bp.get(x, y_floor, z)
            above = bp.get(x, y_floor + 1, z)
            if floor and floor != AIR and above == AIR and rng.random() < 0.25 + 0.75 * p:
                bp.set(x, y_floor, z, "sculk")
                r = rng.random()
                if r < 0.04 * p:
                    bp.set(x, y_floor + 1, z, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
                elif r < 0.25:
                    bp.set(x, y_floor + 1, z, vein(down=True))
            # veins creeping up adjacent walls
            for f, dx, dz in DIRS4:
                for y in range(y_floor + 1, y_floor + 1 + int(1 + 4 * p)):
                    if bp.get(x, y, z) == AIR and bp.get(x + dx, y, z + dz) not in (None, AIR) and \
                            "glass" not in (bp.get(x + dx, y, z + dz) or "") and rng.random() < 0.5 * p:
                        bp.set(x, y, z, vein(**{f: True}))


def sealed_lab(bp):
    rng = random.Random(23)
    H = 6
    # ---------------------------------------------------------------- control room: octagon with stepped dome
    R = 9
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            ax, az = abs(x), abs(z)
            if ax + az > R + 4:
                continue
            edge = ax == R or az == R or ax + az == R + 4
            bp.set(x, -1, z, "deepslate_tiles")
            ring = max(ax, az, (ax + az) * 0.75)
            top = 11 - int(ring / 2.6)
            for y in range(0, top + 2):
                if edge or y >= top:
                    bp.set(x, y, z, LAB_WALL.pick(x, y, z))
                elif y == 0:
                    b = "polished_deepslate" if (ax + az) % 3 else "deepslate_tiles"
                    if ax + az <= 2:
                        b = "reinforced_deepslate"
                    bp.set(x, y, z, b)
                else:
                    bp.set(x, y, z, "air")
    soften(bp, -R, 5, -R, R, 12, R)
    # central containment column with a dormant sculk catalyst, ringed by end rods
    for y in range(1, 6):
        for x, z in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bp.set(x, y, z, "iron_block" if y in (1, 5) else "tinted_glass")
        for x, z in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            bp.set(x, y, z, "glass" if y not in (1, 5) else "iron_block")
    bp.set(0, 1, 0, "reinforced_deepslate")
    bp.set(0, 2, 0, "sculk_catalyst[bloom=false]")
    for y in (3, 4):
        bp.set(0, y, 0, "air")
    bp.set(0, 5, 0, "pearlescent_froglight[axis=y]")
    for y in range(6, 10):
        bp.set(0, y, 0, "iron_chain[axis=y,waterlogged=false]")
    # console ring with chairs
    for x in range(-6, 7):
        for z in range(-6, 7):
            d = max(abs(x), abs(z))
            if d == 5 and not (abs(x) <= 1 or abs(z) <= 1):
                bp.set(x, 1, z, "polished_deepslate_slab[type=top,waterlogged=false]" if (x + z) % 3 else "smooth_stone_slab[type=top,waterlogged=false]")
                k = (x * 7 + z * 3) % 5
                top = ["comparator[facing=north,mode=compare,powered=false]", "repeater[delay=2,facing=east,locked=false,powered=false]",
                       "lever[face=floor,facing=north,powered=false]", "daylight_detector[inverted=false,power=0]",
                       "stone_button[face=floor,facing=north,powered=false]"][k]
                bp.set(x, 2, z, top)
            elif d == 6 and not (abs(x) <= 1 or abs(z) <= 1) and (x + z) % 2 == 0:
                f = "north" if z == 6 else "south" if z == -6 else "west" if x == 6 else "east"
                bp.set(x, 1, z, stair("polished_deepslate_stairs", f))
    # "screens" on the diagonal walls: tinted panes over sea lanterns
    for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        for k in range(-1, 2):
            x, z = sx * (6 + k + 1), sz * (6 - k + 1)
            for y in (3, 4):
                if bp.get(x, y, z) not in (None, AIR):
                    bp.set(x, y, z, "sea_lantern" if (k + y) % 2 else "light_blue_stained_glass")
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.set(x, 8, z, "verdant_froglight[axis=y]")
    # ---------------------------------------------------------------- observation corridor and containment cells (west)
    X0, X1 = -34, -9
    lab_room(bp, X0, -3, X1, 3, H)
    for x in range(X0 + 1, X1):
        bp.set(x, 0, 0, "waxed_oxidized_copper_grate" if x % 2 else "polished_deepslate")
        if x % 4 == 0:
            bp.set(x, H, 0, "ochre_froglight[axis=y]")
    walls = (-34, -28, -22, -16, -10)
    cells = []
    for side in (-1, 1):
        for i in range(4):
            a, b = walls[i], walls[i + 1]
            z0, z1 = (-10, -3) if side < 0 else (3, 10)
            lab_room(bp, a, z0, b, z1, H, floor="deepslate_tiles", panel=False)
            cells.append((a, b, z0, z1, side, i))
            # tinted observation window and a locked iron door onto the corridor
            zw = -3 if side < 0 else 3
            cxm = (a + b) // 2
            for x in range(a + 1, b):
                for y in (2, 3, 4):
                    bp.set(x, y, zw, "tinted_glass" if x != cxm else "iron_block")
            for y in (1, 5):
                for x in range(a + 1, b):
                    bp.set(x, y, zw, "iron_block" if y == 5 else "polished_deepslate")
            bp.door(cxm, 1, zw, "north" if side < 0 else "south", "iron")
            bp.set(cxm, 3, zw, "iron_block")
            bp.set(cxm + 1, 2, zw + (1 if side < 0 else -1), "polished_blackstone_button[face=wall,facing=" +
                   ("south" if side < 0 else "north") + ",powered=false]")
            zc = zw + (1 if side < 0 else -1)
            bp.set(cxm, 5, zw, "redstone_lamp[lit=false]")
            for x in (cxm - 1, cxm, cxm + 1):   # hazard stripes on the floor before each cell
                bp.set(x, 0, zc, "yellow_concrete" if (x + i) % 2 else "black_concrete")
    fill_cells(bp, cells, rng)
    # ---------------------------------------------------------------- airlock, blast door and approach (east)
    lab_room(bp, R, -3, 30, 3, 5)
    for x in range(R, 31):
        bp.set(x, 0, 0, "yellow_concrete" if x % 2 else "black_concrete")
    for xd in (14, 20):     # airlock doors
        for z in (-2, -1, 1, 2):
            for y in range(1, 5):
                bp.set(xd, y, z, "iron_block")
        for y in (3, 4):
            bp.set(xd, y, 0, "iron_block")
        bp.door(xd, 1, 0, "east", "iron")
        bp.set(xd - 1, 2, 1, "polished_blackstone_button[face=wall,facing=west,powered=false]")
        bp.set(xd + 1, 2, -1, "polished_blackstone_button[face=wall,facing=east,powered=false]")
    for x in range(15, 20):          # decontamination nozzles over a grated floor
        for z in (-1, 0, 1):
            bp.set(x, 0, z, "waxed_copper_grate")
        bp.set(x, 4, -2 if x % 2 else 2, "lightning_rod[facing=down,powered=false,waterlogged=false]")
        bp.set(x, 5, 0, "green_stained_glass")
        bp.set(x, 6, 0, "verdant_froglight[axis=y]")
    # the blast door: a giant hazard-striped frame, its iron leaves jammed half open
    BX = 30
    for z in range(-6, 7):
        for y in range(-1, 10):
            bp.set(BX, y, z, "polished_deepslate" if abs(z) > 4 or y > 7 else "iron_block")
            bp.set(BX + 1, y, z, "deepslate_tiles")
    for z in range(-5, 6):
        for y in range(0, 9):
            if abs(z) == 5 or y == 8:
                bp.set(BX + 1, y, z, "yellow_concrete" if (z + y) % 2 else "black_concrete")
    for z in range(-1, 2):
        for y in range(1, 5):
            bp.set(BX, y, z, "air")
            bp.set(BX + 1, y, z, "air")
    for z in (-4, 4):
        for y in range(1, 8):
            bp.set(BX + 1, y, z, "iron_block")
    bp.set(BX, 6, 0, "redstone_lamp[lit=false]")
    bp.set(BX + 2, 6, 0, "redstone_block")
    for x in range(BX + 2, BX + 11):  # rough tunnel out into the caves
        for z in range(-3, 4):
            for y in range(-1, 7):
                inner = abs(z) <= 2 - (1 if y >= 5 else 0) and 1 <= y <= 5
                bp.set(x, y, z, "air" if inner else ("cobbled_deepslate" if (x + y + z) % 3 else "deepslate"))
            bp.set(x, 0, z, "cobbled_deepslate" if abs(z) <= 2 else "deepslate")
    bp.set(BX + 4, 1, -2, "lantern[hanging=false,waterlogged=false]")
    bp.set(BX + 8, 1, 2, "skeleton_skull[rotation=6]")
    # ---------------------------------------------------------------- archive (north) with a hidden director's office
    lab_room(bp, -8, -24, 8, -10, H)
    for x in range(-6, 7, 3):
        for z in range(-21, -12):
            if z != -17:
                for y in (1, 2, 3):
                    bp.set(x, y, z, "bookshelf" if rng.random() > 0.25 else
                           "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,"
                           "slot_3_occupied=false,slot_4_occupied=true,slot_5_occupied=false]")
                if rng.random() < 0.2:
                    bp.set(x + 1, 1, z, "cobweb")
    for x in range(-7, 8):
        bp.set(x, 1, -23, "barrel[facing=south,open=false]")
        bp.set(x, 2, -23, "barrel[facing=south,open=false]" if x % 2 else "bookshelf")
    bp.set(-4, 1, -11, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(4, 1, -11, "lectern[facing=south,has_book=false,powered=false]")
    bp.chest(7, 1, -12, "west", LOOT + "sealed_lab")
    for x in (-3, 3):
        bp.set(x, H, -17, "verdant_froglight[axis=y]")
    # the office hides behind the north barrels: one of them is a hollow false front
    lab_room(bp, -4, -30, 4, -24, 5)
    bp.set(0, 1, -23, "air")
    bp.set(0, 2, -23, "barrel[facing=south,open=false]")
    bp.set(0, 1, -24, "air")
    bp.set(0, 2, -24, "air")
    bp.set(0, 1, -28, "polished_deepslate_slab[type=top,waterlogged=false]")
    bp.set(-1, 1, -28, "polished_deepslate_slab[type=top,waterlogged=false]")
    bp.set(1, 1, -28, "polished_deepslate_slab[type=top,waterlogged=false]")
    bp.set(0, 2, -28, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(0, 1, -27, stair("dark_oak_stairs", "north"))
    bp.chest(3, 1, -29, "west", LOOT + "sealed_lab")
    bp.set(-3, 1, -29, "cartography_table")
    bp.set(-3, 1, -25, "potted_wither_rose")
    bp.set(-3, 2, -29, "candle[candles=3,lit=false,waterlogged=false]")
    bp.set(0, 4, -27, "soul_lantern[hanging=true,waterlogged=false]")
    # ---------------------------------------------------------------- specimen laboratory (south), half eaten by sculk
    lab_room(bp, -8, 10, 8, 24, H)
    for x in range(-6, 7, 4):
        for z in range(13, 21):
            bp.set(x, 1, z, "smooth_stone_slab[type=top,waterlogged=false]" if z % 3 else "iron_block")
        bp.set(x, 2, 14, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        bp.set(x, 2, 17, "cauldron")
        bp.set(x, 2, 19, ["red_stained_glass", "lime_stained_glass", "cyan_stained_glass", "purple_stained_glass"][(x + 6) // 4])
    for z in range(12, 23, 2):     # specimen tanks along the east wall
        for y in (1, 2, 3):
            bp.set(7, y, z, "glass" if y < 3 else "iron_block")
        bp.set(6, 1, z, "polished_deepslate")
    bp.set(7, 1, 14, "sea_pickle[pickles=3,waterlogged=false]")
    bp.chest(-7, 1, 23, "east", LOOT + "sealed_lab")
    bp.set(-7, 1, 11, "sculk_catalyst[bloom=true]")
    bp.set(-6, 1, 23, "sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]")
    for x in (-4, 4):
        bp.set(x, H, 17, "ochre_froglight[axis=y]")
    # ---------------------------------------------------------------- doorways between the wings
    for z in (-1, 0, 1):           # control room <-> corridor (west) and airlock (east)
        for y in (1, 2, 3):
            bp.set(-R, y, z, "air")
            bp.set(R, y, z, "air")
    for zd in (-10, 10):           # control room <-> archive (north) and specimen lab (south)
        hazard_frame(bp, zd, "z", 0, 0, 1, 3)
        for x in (-1, 0, 1):
            for y in (1, 2, 3):
                for z in (zd, zd + (1 if zd < 0 else -1)):
                    bp.set(x, y, z, "air")
    # ---------------------------------------------------------------- the breach: sculk pouring out of cell 2 north
    spread_sculk(bp, -19, -6, 15, 5)
    spread_sculk(bp, -5, 18, 9, 6)
    spread_sculk(bp, 0, -17, 6, 7)
    bp.spawner(-19, 1, -6, MOB["map_wraith"])
    bp.spawner(2, 1, 21, MOB["map_wraith"])
    # the boss lair below: shaft from the breached cell down to the Containment Core
    from . import lair_sculk_spawn
    lair_sculk_spawn.build(bp)
    # the lab as it was left: benches, brewing stands, notes on the shelves, then dust and webs
    I.decorate(bp, dict(I.THEMES["lab"], ceiling=None, loot_barrels=1), seed=1, void_solid=True,
               loot=LOOT + "sealed_lab")
    I.decorate(bp, "ruin", seed=2, void_solid=True, density=0.15)


def fill_cells(bp, cells, rng):
    """Eight containment cells, each with its own failed experiment."""
    for (a, b, z0, z1, side, i) in cells:
        cx = (a + b) // 2
        zi0, zi1 = z0 + 1, z1 - 1
        back = zi0 if side < 0 else zi1
        mid = (zi0 + zi1) // 2
        kind = (i + (0 if side < 0 else 4))
        bp.set(cx, 6, mid, "verdant_froglight[axis=y]" if kind % 2 else "ochre_froglight[axis=y]")
        if kind == 0:      # sculk specimen bed
            for x in range(a + 1, b):
                for z in range(zi0, zi1 + 1):
                    bp.set(x, 0, z, "sculk")
            bp.set(cx, 1, back, "sculk_shrieker[can_summon=false,shrieking=false,waterlogged=false]")
            bp.set(cx - 1, 1, mid, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
            bp.set(cx + 1, 1, back, "calibrated_sculk_sensor[facing=south,power=0,sculk_sensor_phase=inactive,waterlogged=false]")
        elif kind == 1:    # the breach: glass blown out, sculk erupting from the catalyst
            for x in range(a + 1, b):
                for y in (2, 3, 4):
                    if rng.random() < 0.7:
                        bp.set(x, y, -3, "air")
            bp.set(cx - 1, 1, back, "sculk_catalyst[bloom=true]")
            bp.set(cx + 1, 1, back, "sculk_catalyst[bloom=false]")
        elif kind == 2:    # chained heavy core
            bp.set(cx, 1, mid, "heavy_core[waterlogged=false]")
            bp.set(cx, 0, mid, "reinforced_deepslate")
            for (x, z) in ((a + 1, zi0), (b - 1, zi0), (a + 1, zi1), (b - 1, zi1)):
                bp.set(x, 1, z, "reinforced_deepslate")
                bp.set(x, 2, z, "iron_chain[axis=y,waterlogged=false]")
            for x in range(a + 1, b):
                bp.set(x, 4, mid, "iron_chain[axis=x,waterlogged=false]")
        elif kind == 3:    # remains of a test subject
            bp.set(cx, 1, back, "skeleton_skull[rotation=8]")
            bp.set(cx - 1, 1, mid, "bone_block[axis=x]")
            bp.set(cx + 1, 1, mid, "cobweb")
            bp.set(a + 1, 4, zi0, "cobweb")
            bp.set(b - 1, 1, back, "soul_lantern[hanging=false,waterlogged=false]")
        elif kind == 4:    # flooded glow-squid tank (sealed: no door, glass all round)
            for x in range(a + 1, b):
                for z in range(zi0, zi1 + 1):
                    for y in range(1, 5):
                        bp.set(x, y, z, "water")
                    bp.set(x, 0, z, "sand" if (x + z) % 2 else "gravel")
            bp.set(cx, 1, 3, "iron_block")
            bp.set(cx, 2, 3, "tinted_glass")
            bp.set(cx + 1, 2, 2, "air")
            bp.set(cx, 1, mid, "sea_pickle[pickles=4,waterlogged=true]")
            bp.set(cx - 1, 1, back, "kelp_plant")
            bp.set(cx - 1, 2, back, "kelp[age=20]")
            bp.entity(cx, 2, mid, {"id": "minecraft:glow_squid", "PersistenceRequired": 1})
        elif kind == 5:    # echo resonance rig
            bp.set(cx, 1, mid, "reinforced_deepslate")
            bp.set(cx, 2, mid, "amethyst_block")
            bp.set(cx, 3, mid, "amethyst_cluster[facing=up,waterlogged=false]")
            for x in (cx - 2, cx + 2):
                bp.set(x, 1, mid, "sculk_sensor[power=0,sculk_sensor_phase=inactive,waterlogged=false]")
            bp.set(cx, 1, back, "note_block[instrument=basedrum,note=0,powered=false]")
        elif kind == 6:    # overgrown botanical specimen
            for x in range(a + 1, b):
                for z in range(zi0, zi1 + 1):
                    bp.set(x, 0, z, "moss_block")
                    if rng.random() < 0.4:
                        bp.set(x, 1, z, rng.choice(["moss_carpet", "short_grass", "fern", "azalea"]))
            bp.set(cx, 5, mid, "spore_blossom")
            bp.set(a + 1, 4, back, "glow_lichen[down=false,east=false,north=" + ("true" if side < 0 else "false") +
                   ",south=" + ("true" if side > 0 else "false") + ",up=false,waterlogged=false,west=true]")
        else:              # prisoner's cell
            bp.bed(a + 1, 1, back, "east", "gray")
            bp.set(b - 1, 1, back, "cauldron")
            bp.set(cx, 1, mid, "cobweb")
            bp.set(b - 1, 1, mid, "lectern[facing=west,has_book=false,powered=false]")


register(StructureDef(
    "sealed_lab", "overworld", ["deep_dark", "dripstone_caves", "lush_caves"],
    [Piece("lab", sealed_lab)], spacing=28, separation=9, step="underground_structures",
    adaptation="encapsulate", height=("uniform", -59, -42), spawns=[(MOB["map_wraith"], 10, 1, 2)],
    title_fr="Laboratoire scellé", title_en="Sealed Laboratory"))
