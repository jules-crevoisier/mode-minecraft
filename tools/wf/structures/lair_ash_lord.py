"""Lair of the Ash Lord, under the Basalt Fortress (called from nether.basalt_fortress).

The fortress already fills the whole template height (top at y116 absolute), so the lair lives in the
solid rock island between blueprint y=-14 (the template floor) and y=-2, sealed on every side against
the lava sea it sits in. The route:

  * the keep's secret vault (y=-6): a cracked block in the great-hall floor, a ladder down;
  * level 1, the Bone Nave: a long ossuary of basalt with skull niches, a guard spawner and a side cache;
  * the Ember Stair down to level 2, the Magma Gallery: two lanes on either side of a lava channel
    behind iron bars, burnt ossuaries in the walls, a blaze spawner;
  * the site of grace (waystone, benches, soul lights) in front of the mist;
  * the Throne of Ash (27 x 29, ceiling 11): a hall of ember bricks and blackstone with two colonnades,
    lava pools and lavafalls in alcoves along the walls only, a throne on a dais between braziers, and
    an iron grate in the courtyard floor above that shows the glow below;
  * behind the throne, the Ash Lord's hoard, barred until he falls.
"""
import math

from ..arch import Palette, slab, stair
from ..parts import LOOT, MOB, MOD

EB = "wayfarers:ember_bricks"
EBS = "wayfarers:ember_brick_stairs"
LAMP = "wayfarers:ember_lamp"
GILD = "wayfarers:gilded_trim"
PBB = "polished_blackstone_bricks"
CPBB = "cracked_polished_blackstone_bricks"
PBBS = "polished_blackstone_brick_stairs"
PBBSL = "polished_blackstone_brick_slab"
PBBW = "polished_blackstone_brick_wall"
PB = "polished_blackstone"
PBS = "polished_blackstone_stairs"
CHIS = "chiseled_polished_blackstone"
GBS = "gilded_blackstone"
PBAS = "polished_basalt[axis=y]"
CAMPFIRE = "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
CANDLES = "candle[candles=4,lit=true,waterlogged=false]"
BARS = "iron_bars"

WALL = Palette({EB: 6, PBB: 3, CPBB: 1}, seed=71, scale=2.5)
ROCKWALL = Palette({"basalt[axis=y]": 4, "blackstone": 3, PBB: 2, "smooth_basalt": 1}, seed=72, scale=2.0)
FLOOR = Palette({PB: 4, PBB: 3, CPBB: 1}, seed=73, scale=1.6)
SEALER = Palette({"blackstone": 3, "basalt[axis=y]": 2}, seed=74, scale=3.0)

# arena: interior x -13..13, z -8..20, walking level y=-13 (floor blocks at -14), ceiling at -2
AX, AZ = 0, 6
AR = 14
FLOOR_Y = -14
CEIL_Y = -2
COL_Z = (-5, 0, 5, 10, 15)          # colonnade rows (each column is 2x2: z, z+1)
GAPS = ((-3, -1), (2, 4), (7, 9), (12, 14))


class _Lair:
    """Tracks every cell the lair opens so the shell can be sealed afterwards."""

    def __init__(self, bp):
        self.bp = bp
        self.open = set()

    def air(self, x0, y0, z0, x1, y1, z1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.bp.set(x, y, z, "air")
                    self.open.add((x, y, z))

    def put(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.open.add((x, y, z))

    def seal(self):
        """Close the lair: every neighbour of an opened cell that the template leaves unset becomes rock,
        so no cavity ever touches the lava sea or the terrain around the template."""
        for (x, y, z) in list(self.open):
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                p = (x + dx, y + dy, z + dz)
                if self.bp.get(*p) is None:
                    self.bp.set(*p, SEALER.pick(*p))


def _box_room(L, x0, x1, z0, z1, y_floor, y_ceil, wall=WALL, floor=FLOOR, ceil=None):
    """Room with interior x0..x1, z0..z1: floor at y_floor, ceiling at y_ceil, 1-thick walls around."""
    bp = L.bp
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(y_floor, y_ceil + 1):
                if y == y_floor:
                    bp.set(x, y, z, floor.pick(x, y, z) if not edge else wall.pick(x, y, z))
                elif y == y_ceil:
                    bp.set(x, y, z, (ceil or wall).pick(x, y, z))
                elif edge:
                    bp.set(x, y, z, wall.pick(x, y, z))
                else:
                    L.air(x, y, z, x, y, z)


def _chandelier(L, x, y_ceil, z, soul=False):
    """Black iron chandelier hanging from the ceiling block at y_ceil."""
    bp = L.bp
    c = y_ceil - 2
    L.put(x, y_ceil - 1, z, "iron_chain[axis=y,waterlogged=false]")
    L.put(x, c, z, GILD)
    L.put(x, c - 1, z, LAMP)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        L.put(x + dx, c, z + dz, PBBW)
        L.put(x + 2 * dx, c, z + 2 * dz, PBBW)
        bp.lantern(x + 2 * dx, c - 1, z + 2 * dz, hanging=True, soul=soul)
        L.put(x + 2 * dx, c + 1, z + 2 * dz, "candle[candles=3,lit=true,waterlogged=false]")


def _brazier(L, x, y, z):
    """Big standing brazier, base at y."""
    L.put(x, y, z, CHIS)
    L.put(x, y + 1, z, PBBW)
    L.put(x, y + 2, z, GBS)
    for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
        L.put(x + dx, y + 2, z + dz, stair(PBBS, d, "top"))
        L.put(x + dx, y + 3, z + dz, CAMPFIRE)
    L.put(x, y + 3, z, "magma_block")
    L.put(x, y + 4, z, CAMPFIRE)


def _skull_niche(L, x, y, z, facing, k):
    """A burial niche cut into a wall: bones, a skull and a candle or a soul lantern."""
    bp = L.bp
    bp.set(x, y - 1, z, "bone_block[axis=y]")
    L.put(x, y, z, ("skeleton_skull[rotation=%d]" if k % 3 else "wither_skeleton_skull[rotation=%d]")
          % {"north": 8, "south": 0, "east": 12, "west": 4}[OPP[facing]])
    L.put(x, y + 1, z, "candle[candles=2,lit=true,waterlogged=false]" if k % 2 else "air")
    bp.set(x, y + 2, z, "bone_block[axis=x]" if facing in ("east", "west") else "bone_block[axis=z]")


OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ the route
def _vault_access(L):
    """The keep's secret vault: a cracked block in the great-hall floor and a working ladder down."""
    bp = L.bp
    # the old corner shaft is sealed off; the way down is now one block east of it
    for y in range(-2, 1):
        bp.set(-11, y, -19, PBB)
        bp.set(-11, y, -18, PBB)
    bp.set(-10, 1, -18, CPBB)
    L.air(-10, -6, -18, -10, 0, -18)
    bp.ladder(-10, -6, -18, 0, "south")
    for y in range(-1, 1):
        bp.set(-10, y, -19, PBB)
        bp.set(-9, y, -18, PBB)
        bp.set(-11, y, -18, PBB)
        bp.set(-10, y, -17, PBB)
    # a doorway in the vault's west wall, framed in chiseled blackstone
    L.air(-11, -6, -16, -11, -4, -16)
    for y in (-6, -5, -4):
        bp.set(-11, y, -17, CHIS)
        bp.set(-11, y, -15, CHIS)
    bp.set(-11, -3, -16, GILD)


def _bone_nave(L):
    """Level 1: corridor west from the vault, then the Bone Nave running south (walk y=-6)."""
    bp = L.bp
    # corridor (3 wide) from the vault door to the nave
    _box_room(L, -17, -12, -17, -15, -7, -2, wall=ROCKWALL)
    for x in range(-17, -11):
        L.air(x, -6, -16, x, -3, -16)
    for x in (-16, -13):
        bp.lantern(x, -3, -16, hanging=True, soul=True)
    # the nave: interior x -23..-19, z -18..10, ribbed vault
    _box_room(L, -23, -19, -18, 10, -7, -2, wall=ROCKWALL)
    L.air(-18, -6, -17, -18, -3, -15)     # opening to the corridor
    for z in range(-18, 11):
        bp.set(-21, -7, z, PBB if z % 4 else CHIS)       # a runner of brick down the middle
        if z % 4 == 0:
            # transverse rib + pilasters
            for x in range(-23, -18):
                L.put(x, -3, z, "polished_basalt[axis=x]")
            for x in (-23, -19):
                L.put(x, -6, z, PBAS)
                L.put(x, -5, z, PBAS)
                L.put(x, -4, z, stair(PBBS, "east" if x == -23 else "west", "top"))
        elif z % 4 == 2:
            bp.lantern(-21, -3, z, hanging=True, soul=True)
    # burial niches in the west wall (skulls, bones, candles)
    for k, z in enumerate(range(-17, 10, 2)):
        if z % 4 == 0:
            continue
        L.air(-24, -5, z, -24, -5, z)
        _skull_niche(L, -24, -5, z, "east", k)
    # bone piles along the floor of the east side
    for z in (-14, -9, -1, 6):
        bp.set(-19, -6, z, "bone_block[axis=z]")
        L.put(-19, -5, z, "skeleton_skull[rotation=4]")
    bp.spawner(-21, -6, -6, MOB["basalt_guard"])
    # side cache behind a gilded arch
    L.air(-18, -6, 1, -18, -5, 1)
    _box_room(L, -17, -15, 0, 2, -7, -3, wall=ROCKWALL)
    L.put(-16, -6, 1, "air")
    bp.chest(-15, -6, 1, "west", LOOT + "basalt_fortress")
    bp.set(-16, -6, 0, "candle[candles=3,lit=true,waterlogged=false]")
    bp.set(-16, -6, 2, "gold_block")
    bp.set(-18, -4, 1, GILD)


def _ember_stair(L):
    """From the nave (walk -6) down six steps to the landing of level 2 (walk -12)."""
    bp = L.bp
    for k in range(6):
        z = 11 + k
        y = -7 - k                      # stair block; walk on top of it
        for x in range(-24, -17):
            edge = x in (-24, -18)
            for yy in range(y - 2, -1):
                if edge:
                    bp.set(x, yy, z, ROCKWALL.pick(x, yy, z))
                elif yy < y:
                    bp.set(x, yy, z, ROCKWALL.pick(x, yy, z))
                elif yy == y:
                    L.put(x, yy, z, stair(PBBS, "north"))
                elif yy < -2:
                    L.air(x, yy, z, x, yy, z)
                else:
                    bp.set(x, yy, z, ROCKWALL.pick(x, yy, z))
        if k % 2 == 0:
            for x in (-24, -18):
                L.put(x, y + 3, z, LAMP)
    # landing (walk -12) x -23..-19, z 17..21
    _box_room(L, -23, -19, 17, 21, -13, -7, wall=ROCKWALL)
    L.air(-23, -12, 16, -19, -8, 16)
    bp.lantern(-21, -8, 19, hanging=True)


def _magma_gallery(L):
    """Level 2: two lanes either side of a lava channel behind iron bars (walk y=-12)."""
    bp = L.bp
    x0, x1, z0, z1 = -24, -7, 22, 28
    _box_room(L, x0, x1, z0, z1, -13, -8, wall=ROCKWALL)
    L.air(-23, -12, 21, -19, -9, 21)          # from the landing
    for x in range(x0, x1 + 1):
        bp.set(x, -14, 25, "blackstone")
        if -22 <= x <= -9:
            bp.set(x, -13, 25, "lava[level=0]")
            for z in (24, 26):
                L.put(x, -12, z, BARS)
                L.put(x, -11, z, BARS)
                bp.set(x, -13, z, CHIS if x % 3 == 0 else PBB)
        elif x in (-23, -8):
            L.put(x, -12, 25, BARS)
        if x % 3 == 0:
            for z in (22, 28):
                bp.set(x, -13, z, PBB)
    # vault ribs and lights over the channel
    for x in range(x0, x1 + 1, 4):
        for z in range(z0, z1 + 1):
            L.put(x, -9, z, "polished_basalt[axis=z]")
        L.put(x, -10, 22, stair(PBBS, "south", "top"))
        L.put(x, -10, 28, stair(PBBS, "north", "top"))
    for x in range(x0 + 2, x1, 4):
        bp.lantern(x, -9, 25, hanging=True)
    # burnt ossuaries in the south wall: bones and skulls behind bars, soul lanterns
    for k, x in enumerate(range(x0 + 1, x1, 2)):
        if x % 4 == 0:
            continue
        L.air(x, -12, 29, x, -11, 29)
        bp.set(x, -13, 29, "bone_block[axis=y]")
        L.put(x, -12, 29, "wither_skeleton_skull[rotation=8]" if k % 3 == 0 else "skeleton_skull[rotation=8]")
        L.put(x, -11, 29, "soul_lantern[hanging=false,waterlogged=false]" if k % 2 else "bone_block[axis=x]")
        bp.set(x, -10, 29, "bone_block[axis=x]")
    bp.spawner(-15, -12, 29, "minecraft:blaze")
    bp.set(-15, -11, 29, ROCKWALL.pick(-15, -11, 29))


def _site_of_grace(L):
    """Antechamber before the mist: waystone, benches, soul lights (walk y=-12)."""
    bp = L.bp
    _box_room(L, -5, 5, 22, 28, -13, -7, wall=WALL)
    L.air(-6, -12, 23, -6, -9, 27)            # from the gallery
    for z in range(22, 29):
        for x in range(-5, 6):
            bp.set(x, -13, z, GBS if (x, z) == (0, 26) else PBB if abs(x) < 2 else FLOOR.pick(x, -13, z))
    bp.set(0, -12, 27, MOD["waystone"])
    for x in (-1, 1):
        L.put(x, -12, 28, "candle[candles=3,lit=true,waterlogged=false]")
    # benches facing the waystone
    for z in (24, 25):
        L.put(-4, -12, z, stair(PBS, "east"))
        L.put(4, -12, z, stair(PBS, "west"))
    for x in (-4, 4):
        L.put(x, -12, 27, "soul_lantern[hanging=false,waterlogged=false]")
        bp.set(x, -10, 29, LAMP)
    bp.lantern(0, -8, 25, hanging=True, soul=True)
    for x in (-3, 3):
        bp.lantern(x, -8, 23, hanging=True)
    # the arena gate: a gilded pointed arch in the north wall
    L.air(-2, -12, 21, 2, -9, 21)
    L.air(-1, -8, 21, 1, -8, 21)
    for y in range(-12, -7):
        bp.set(-3, y, 21, CHIS)
        bp.set(3, y, 21, CHIS)
    for x in (-2, 2):
        bp.set(x, -8, 21, stair(PBBS, "east" if x < 0 else "west", "top"))
    bp.set(0, -7, 21, GILD)
    bp.set(0, -6, 21, LAMP)


# ------------------------------------------------------------------ the Throne of Ash
def _arena(L):
    bp = L.bp
    x0, x1, z0, z1 = AX - 13, AX + 13, AZ - 14, AZ + 14
    # shell: floor, walls, ceiling
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(FLOOR_Y, CEIL_Y + 1):
                if y == FLOOR_Y:
                    bp.set(x, y, z, _floor(x, z))
                elif y == CEIL_Y:
                    bp.set(x, y, z, "blackstone" if (x + z) % 2 else PBB)
                elif edge:
                    bp.set(x, y, z, WALL.pick(x, y, z))
                else:
                    L.air(x, y, z, x, y, z)
    # wall dressing: a basalt plinth course, a gilded string course, ember lamps
    for x in range(x0 - 1, x1 + 2):
        for z in (z0 - 1, z1 + 1):
            bp.set(x, -13, z, PBB)
            bp.set(x, -6, z, GILD)
    for z in range(z0 - 1, z1 + 2):
        for x in (x0 - 1, x1 + 1):
            bp.set(x, -13, z, PBB)
            bp.set(x, -6, z, GILD)
    # colonnades: 2x2 basalt columns with chiseled bases, gilded bands, ember capitals and arcades
    for sx in (-1, 1):
        cx = (8, 9) if sx > 0 else (-9, -8)
        for cz in COL_Z:
            for x in cx:
                for z in (cz, cz + 1):
                    L.put(x, -13, z, CHIS)
                    for y in range(-12, -4):
                        L.put(x, y, z, GILD if y == -9 else PBAS)
                    L.put(x, -4, z, EB)
                    L.put(x, -3, z, PBB)
            # corbels under the capital, outward on the four sides
            for z in (cz, cz + 1):
                L.put(cx[0] - 1, -5, z, stair(PBBS, "east", "top"))
                L.put(cx[1] + 1, -5, z, stair(PBBS, "west", "top"))
            for x in cx:
                L.put(x, -5, cz - 1, stair(PBBS, "south", "top"))
                L.put(x, -5, cz + 2, stair(PBBS, "north", "top"))
            L.put(cx[0], -10, cz - 1, LAMP if cz % 10 == 0 else stair(PBBS, "south", "top"))
            # wall pilaster facing the column
            wx = x1 + 1 if sx > 0 else x0 - 1
            for z in (cz, cz + 1):
                for y in range(-12, -2):
                    bp.set(wx, y, z, PBAS)
                bp.set(wx, -6, z, GILD)
            # transverse rib from the wall over the aisle to the column, and across the nave
            for x in range(min(wx, cx[0]), max(wx, cx[1]) + 1):
                L.put(x, -3, cz, "polished_basalt[axis=x]")
        # arcade lintels between the columns (pointed: stairs on the springers, blocks above)
        for (a, b) in zip(COL_Z, COL_Z[1:]):
            for x in cx:
                L.put(x, -4, a + 2, stair(PBBS, "south", "top"))
                L.put(x, -4, b - 1, stair(PBBS, "north", "top"))
                for z in range(a + 2, b):
                    L.put(x, -3, z, PBB)
    for cz in COL_Z:
        for x in range(-7, 8):
            L.put(x, -3, cz, "polished_basalt[axis=x]")
    # lava alcoves in the side walls between the pilasters: pools at the edge only, fed by lavafalls
    for sx in (-1, 1):
        rim = x1 + 1 if sx > 0 else x0 - 1
        for (za, zb) in GAPS:
            xs = [rim + sx, rim + 2 * sx]
            back = rim + 3 * sx
            for z in range(za - 1, zb + 2):
                for y in range(FLOOR_Y, -3):
                    for x in xs + [back]:
                        bp.set(x, y, z, WALL.pick(x, y, z))
            for z in range(za, zb + 1):
                for x in xs:
                    bp.set(x, FLOOR_Y, z, "magma_block")
                    bp.set(x, -13, z, "lava[level=0]")
                    L.air(x, -12, z, x, -6, z)
                L.put(rim, -13, z, CHIS)
                L.air(rim, -12, z, rim, -7, z)
            zm = (za + zb) // 2
            # the opening's pointed head and a gilded keystone
            L.put(rim, -7, za, stair(PBBS, "south", "top"))
            L.put(rim, -7, zb, stair(PBBS, "north", "top"))
            bp.set(rim, -6, zm, LAMP)
            # lavafall: an enclosed source at the back of the alcove, falling into the pool
            src = rim + 2 * sx
            bp.set(src, -5, zm, "lava[level=0]")
            for y in range(-12, -5):
                L.put(src, y, zm, "lava[level=8]")
            for (px, pz) in ((src - sx, zm), (src, zm - 1), (src, zm + 1)):
                bp.set(px, -5, pz, WALL.pick(px, -5, pz))
            bp.set(src, -4, zm, WALL.pick(src, -4, zm))
    # throne dais at the north end, between two great braziers, under banners
    for x in range(-5, 6):
        for z in range(z0, z0 + 3):
            L.put(x, -13, z, PBB if abs(x) < 5 and z < z0 + 2 else stair(PBBS, "south") if z == z0 + 2 else PBB)
        L.put(x, -13, z0 + 2, stair(PBBS, "south"))
    for x in range(-3, 4):
        L.put(x, -12, z0, PBB)
        L.put(x, -12, z0 + 1, stair(PBBS, "south"))
    for x in (-5, 5):
        L.put(x, -13, z0, PBB)
    L.put(0, -11, z0, stair("blackstone_stairs", "south"))            # the seat
    L.put(-1, -11, z0, CHIS)
    L.put(1, -11, z0, CHIS)
    L.put(-1, -10, z0, "polished_blackstone_button[face=floor,facing=south,powered=false]")
    L.put(1, -10, z0, "polished_blackstone_button[face=floor,facing=south,powered=false]")
    wz = z0 - 1
    for y in range(-11, -4):
        bp.set(0, y, wz, CHIS if y < -7 else GILD if y == -7 else "gold_block")
        bp.set(-1, y, wz, PBAS)
        bp.set(1, y, wz, PBAS)
    bp.set(0, -4, wz, LAMP)
    for x in (-2, 2):
        bp.set(x, -6, wz, GILD)
        bp.set(x, -5, wz, "gold_block")
    bp.set(-1, -4, wz, GILD)
    bp.set(1, -4, wz, GILD)
    for x in (-7, 7):
        _brazier(L, x, -13, z0 + 1)
    for x in (-4, 4):
        L.put(x, -8, z0, "red_wall_banner[facing=south]")
        L.put(x, -7, z0, "air")
    # the central sigil and the seal of the fight
    bp.boss_seal(AX, -13, AZ, "wayfarers:ash_lord", AR)
    L.open.add((AX, -13, AZ))
    # light: chandeliers over the nave and a ring of lamps around the grate above the centre
    for z in (AZ - 7, AZ + 8):
        _chandelier(L, AX, -2, z)
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        bp.set(AX + dx, CEIL_Y, AZ + dz, LAMP)
    # the courtyard grate above the centre shows the glow of the hall below
    L.air(AX - 1, -2, AZ - 1, AX + 1, -1, AZ + 1)
    for x in range(AX - 1, AX + 2):
        for z in range(AZ - 1, AZ + 2):
            bp.set(x, 0, z, BARS)
    # the step down from the gate
    for x in range(-2, 3):
        L.put(x, -13, z1, stair(PBBS, "south"))


def _floor(x, z):
    """Floor of the Throne of Ash: brick aisles, a checkered nave, a runner from the gate to the throne
    and a gilded sigil ring around the seal."""
    d = math.hypot(x - AX, z - AZ)
    ang = math.degrees(math.atan2(z - AZ, x - AX)) % 45
    if d < 1.6:
        return CHIS
    if 4.6 <= d < 5.4:
        return GILD
    if 5.4 <= d < 6.3:
        return GBS
    if 1.6 <= d < 4.6 and (ang < 7 or ang > 38):
        return EB
    if 1.6 <= d < 4.6:
        return PBB
    if abs(x - AX) <= 1:
        return "red_nether_bricks" if x == AX else GBS if z % 3 == 0 else PB
    if abs(x - AX) >= 10:
        return PBB if (x + z) % 5 else CPBB
    if abs(x - AX) == 7:
        return CHIS
    return PB if (x + z) % 2 else PBB


def _hoard(L):
    """Behind the throne, east: the Ash Lord's hoard, barred until he falls (walk y=-13)."""
    bp = L.bp
    _box_room(L, 3, 11, -17, -11, -14, -8, wall=WALL)
    L.air(6, -13, -10, 8, -10, -10)
    L.air(6, -13, -9, 8, -10, -9)
    for x in range(6, 9):
        bp.set(x, -14, -10, PBB)
        bp.set(x, -14, -9, PBB)
        for y in range(-13, -10):
            bp.set(x, y, -9, MOD["vault_bars"])
    bp.set(7, -9, -9, GILD)
    for z in range(-17, -10):
        for x in range(3, 12):
            bp.set(x, -14, z, GBS if (x + z) % 4 == 0 else PBB)
    bp.chest(7, -13, -17, "south", LOOT + "basalt_fortress_keep")
    bp.chest(4, -13, -14, "east", LOOT + "basalt_fortress_keep")
    for (x, z) in ((3, -17), (11, -17), (11, -12), (3, -11)):
        L.put(x, -13, z, "gold_block")
        L.put(x, -12, z, CANDLES)
    for x in (5, 9):
        L.put(x, -13, -17, GBS)
        L.put(x, -12, -17, "gold_block")
    L.put(10, -13, -15, "raw_gold_block")
    L.put(10, -13, -14, "gold_block")
    L.put(10, -12, -15, "gold_block")
    # the Ash Lord's spare blade, planted in a pedestal
    L.put(7, -13, -14, CHIS)
    L.put(7, -12, -14, "chain[axis=y,waterlogged=false]" if False else PBBW)
    L.put(7, -11, -14, GILD)
    bp.lantern(7, -9, -12, hanging=True)
    bp.set(3, -10, -14, LAMP)
    bp.set(11, -10, -14, LAMP)


def ash_lord_lair(bp):
    """Carve the lair under the Basalt Fortress. Call at the end of nether.basalt_fortress()."""
    L = _Lair(bp)
    _vault_access(L)
    _bone_nave(L)
    _ember_stair(L)
    _magma_gallery(L)
    _site_of_grace(L)
    _arena(L)
    _hoard(L)
    bp.mist(-2, -12, AZ + AR + 1, 2, -8, AZ + AR + 1)     # the only way into the hall: its south gate
    L.seal()
