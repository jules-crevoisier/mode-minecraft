"""Lair of the Golden Piglin King, under the Piglin Sanctuary (called from nether.piglin_sanctuary).

The sanctuary's crown already reaches y114 absolute at its highest placement, so the template may only
grow two blocks deeper (to blueprint y=-10). To fit a proper hall under the ziggurat, the pillared
sanctum's floor (and everything standing on it) is lifted by two blocks; the King's Treasury then
spans the whole sanctum footprint underneath with a 10-block ceiling, and opens into two 14-block
vaulted apses carved into the solid first tier. The route:

  * a gilded arch in the sanctum's south-east wall and the Tithe Stair down through the first tier;
  * the Hall of Tribute (y=-3): heaped offerings, crimson banners, piglin heads on posts, a spawner;
  * a second stair down to the Smelting Way (y=-9): a molten channel behind gilded bars fed by spouts,
    a brute spawner at its far end;
  * the site of grace in a bay across from the treasury gate (waystone, benches, soul lights);
  * the King's Treasury (23 x 35): blackstone and gold, two colonnades, gold heaped along the walls,
    crimson banners, lava fountains in the four apse corners only, a golden throne before a sun disc;
  * behind the throne apse, the royal vault, barred until the King falls.
"""
import math

from ..arch import Palette, stair
from ..parts import LOOT, MOD

LAMP = "wayfarers:ember_lamp"
GILD = "wayfarers:gilded_trim"
PBB = "polished_blackstone_bricks"
CPBB = "cracked_polished_blackstone_bricks"
PBBS = "polished_blackstone_brick_stairs"
PBBW = "polished_blackstone_brick_wall"
PB = "polished_blackstone"
PBS = "polished_blackstone_stairs"
CHIS = "chiseled_polished_blackstone"
GBS = "gilded_blackstone"
PBAS = "polished_basalt[axis=y]"
BARS = "iron_bars"
CANDLES = "candle[candles=4,lit=true,waterlogged=false]"

WALL = Palette({PBB: 5, "blackstone": 2, CPBB: 1, GBS: 1}, seed=81, scale=2.5)
FLOOR = Palette({PB: 4, PBB: 3, GBS: 0.3}, seed=82, scale=1.6)
HEAP = Palette({"gold_block": 4, "raw_gold_block": 3, GBS: 1}, seed=83, scale=1.5)
SEALER = Palette({"blackstone": 3, "netherrack": 2}, seed=84, scale=3.0)

LIFT = 2                     # how far the sanctum floor is raised
SANCTUM = 11                 # sanctum interior half size (x, z in -11..11)
FLOOR_Y = -10                # treasury floor blocks (template bottom); walking level -9
WALK = FLOOR_Y + 1
APSE = 12                    # |z| beyond this the treasury opens into the vaulted apses
HALF_X, HALF_Z = 11, 17      # treasury interior half sizes
COLS = ((-15, -14), (-10, -9), (-5, -4), (4, 5), (9, 10), (14, 15))


class _Lair:
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
        """Every unset neighbour of an opened cell becomes rock: no cavity touches the world outside."""
        for (x, y, z) in list(self.open):
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                p = (x + dx, y + dy, z + dz)
                if p[1] >= FLOOR_Y and self.bp.get(*p) is None:     # never below the template floor
                    self.bp.set(*p, SEALER.pick(*p))


def _room(L, x0, x1, z0, z1, y_floor, y_ceil, wall=WALL, floor=FLOOR):
    bp = L.bp
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(y_floor, y_ceil + 1):
                if y in (y_floor, y_ceil) or edge:
                    bp.set(x, y, z, (floor if (y == y_floor and not edge) else wall).pick(x, y, z))
                else:
                    L.air(x, y, z, x, y, z)


def _chandelier(L, x, y_ceil, z):
    """Gold chandelier hanging from the ceiling block at y_ceil (lowest block 3 below it)."""
    bp = L.bp
    L.put(x, y_ceil - 1, z, "iron_chain[axis=y,waterlogged=false]")
    L.put(x, y_ceil - 2, z, "gold_block")
    L.put(x, y_ceil - 3, z, LAMP)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        L.put(x + dx, y_ceil - 2, z + dz, GILD)
        bp.lantern(x + dx, y_ceil - 3, z + dz, hanging=True)
        L.put(x + dx, y_ceil - 1, z + dz, "candle[candles=3,lit=true,waterlogged=false]")


def _piglin_post(L, x, y, z, rot):
    """A gilded post carrying a piglin head, like the trophies of the brutes' halls."""
    L.put(x, y, z, GBS)
    L.put(x, y + 1, z, PBBW)
    L.put(x, y + 2, z, "gold_block")
    L.put(x, y + 3, z, "piglin_head[rotation=%d]" % rot)


# ------------------------------------------------------------------ the sanctum, lifted
def _lift_sanctum(L):
    """Raise the sanctum floor and what stands on it by LIFT blocks; the chandeliers and the pillar
    shafts above stay where they are. The two doorways get steps up."""
    bp = L.bp
    n = SANCTUM
    for x in range(-n, n + 1):
        for z in range(-n, n + 1):
            old = {y: bp.blocks.get((x, y, z)) for y in range(-1, 7)}
            for ny in range(6, -1 + LIFT - 1, -1):
                src = old.get(ny - LIFT)
                if src is None or src[0] == "minecraft:air":
                    if ny >= 5:
                        continue            # keep the chandeliers hanging there
                    bp.set(x, ny, z, "air")
                else:
                    bp.blocks[(x, ny, z)] = src
    for sx in (-1, 1):
        for z in (-1, 0, 1):
            bp.set(sx * 12, 0, z, PBB)
            bp.set(sx * 12, 1, z, stair(PBBS, "west" if sx > 0 else "east"))
            bp.set(sx * 13, 0, z, stair(PBBS, "west" if sx > 0 else "east"))


# ------------------------------------------------------------------ the descent
def _tithe_stair(L):
    """From a gilded arch in the sanctum's east wall down through the first tier (walk 2 -> -3)."""
    bp = L.bp
    top = -1 + LIFT             # sanctum floor block y after the lift (walk on top: 2)
    # the arch in the sanctum wall (x=12), z 6..8
    L.air(12, top + 1, 6, 12, top + 3, 8)
    for y in range(top + 1, top + 5):
        bp.set(12, y, 5, CHIS)
        bp.set(12, y, 9, CHIS)
    bp.set(12, top + 4, 7, GILD)
    bp.set(11, top + 4, 7, "red_wall_banner[facing=west]")
    # landing x 13..15, z 5..9
    _room(L, 13, 15, 5, 8, top, top + 4)
    L.air(12, top + 1, 6, 12, top + 3, 8)
    # stair south: z 9..13, walk 1 .. -3 (stairs facing north, ascending back to the sanctum)
    for k in range(5):
        z = 9 + k
        y = top - 1 - k
        for x in range(12, 17):
            edge = x in (12, 16)
            for yy in range(y - 1, top + 5):
                if edge or yy < y or yy == top + 4:
                    bp.set(x, yy, z, WALL.pick(x, yy, z))
                elif yy == y:
                    L.put(x, yy, z, stair(PBBS, "north"))
                else:
                    L.air(x, yy, z, x, yy, z)
        bp.set(12 if k % 2 else 16, y + 2, z, LAMP)


def _hall_of_tribute(L):
    """Level A (walk -3): offerings heaped for the King, banners, piglin trophies, a piglin spawner."""
    bp = L.bp
    y0 = -4
    _room(L, 13, 21, 14, 21, y0, y0 + 6)
    L.air(13, y0 + 1, 13, 15, y0 + 4, 13)                # from the stair
    for x in range(13, 22):
        for z in range(14, 22):
            bp.set(x, y0, z, GBS if (x + z) % 5 == 0 else FLOOR.pick(x, y0, z))
    # offering heaps along the east wall
    for (x, z, h) in ((21, 15, 2), (21, 16, 3), (20, 16, 1), (21, 17, 2), (21, 20, 3), (20, 20, 2), (21, 21, 1), (20, 21, 1)):
        for k in range(h):
            L.put(x, y0 + 1 + k, z, HEAP.pick(x, y0 + 1 + k, z))
    L.put(21, y0 + 4, 16, CANDLES)
    bp.chest(21, y0 + 1, 18, "west", LOOT + "piglin_sanctuary")
    L.put(21, y0 + 1, 19, "gold_block")
    L.put(21, y0 + 2, 19, CANDLES)
    for (x, z, rot) in ((14, 15, 6), (14, 20, 2)):
        _piglin_post(L, x, y0 + 1, z, rot)
    for z in (16, 19):
        bp.set(13 - 1, y0 + 4, z, "red_wall_banner[facing=east]")
    for x in (16, 19):
        bp.set(x, y0 + 4, 22, "red_wall_banner[facing=north]")
    # the tribute altar in the middle: a gilded plinth, the offering bowl of gold, candles at its corners
    for x in range(16, 19):
        for z in range(16, 19):
            L.put(x, y0 + 1, z, GBS if (x + z) % 2 else CHIS)
    L.put(17, y0 + 2, 17, "gold_block")
    L.put(17, y0 + 3, 17, LAMP)
    for (x, z) in ((16, 16), (18, 16), (16, 18), (18, 18)):
        L.put(x, y0 + 2, z, CANDLES)
    for (x, z) in ((17, 15), (15, 17), (19, 17)):
        L.put(x, y0 + 1, z, stair(PBBS, {(17, 15): "south", (15, 17): "east", (19, 17): "west"}[(x, z)]))
    # more offerings heaped in the corners
    for (x, z, h) in ((13, 21, 2), (14, 21, 1), (13, 14, 1), (16, 21, 1), (19, 14, 2), (20, 14, 1)):
        for k in range(h):
            L.put(x, y0 + 1 + k, z, HEAP.pick(x, y0 + 1 + k, z))
        L.put(x, y0 + 1 + h, z, "light_weighted_pressure_plate[power=0]")
    _chandelier(L, 17, y0 + 6, 19)
    bp.spawner(20, y0 + 1, 15, "minecraft:piglin")


def _smelting_stair(L):
    """From the Hall of Tribute west along z 19..21 down to the Smelting Way (walk -3 -> -9)."""
    bp = L.bp
    L.air(12, -3, 19, 12, 0, 21)
    for k in range(6):
        x = 12 - k
        y = -5 - k                  # stair block; walk on top: -4 .. -9
        for z in range(18, 23):
            edge = z in (18, 22)
            for yy in range(max(y - 1, FLOOR_Y), 2):
                if edge or yy < y or yy == 1:
                    bp.set(x, yy, z, WALL.pick(x, yy, z))
                elif yy == y:
                    L.put(x, yy, z, stair(PBBS, "east"))
                else:
                    L.air(x, yy, z, x, yy, z)


def _smelting_way(L):
    """Level B (walk -9): lanes beside a molten channel fed by gilded spouts, behind gilded bars."""
    bp = L.bp
    x0, x1, z0, z1 = -14, 7, 19, 23
    _room(L, x0, x1, z0, z1, FLOOR_Y, -4)
    for x in range(x0, x1 + 1):
        if -4 <= x <= 4:
            continue                                    # the bay of the site of grace opens here
        if x0 + 1 <= x <= x1 - 1:
            bp.set(x, WALK, 23, "lava[level=0]")
            bp.set(x, WALK, 22, "gold_block" if x % 2 else GBS)
            L.put(x, WALK + 1, 22, BARS)
            L.put(x, WALK + 2, 22, BARS)
        if x % 4 == 0 and x0 + 1 <= x <= x1 - 1:
            # a spout in the south wall pours into the channel
            bp.set(x, -5, 23, "lava[level=0]")
            for y in range(WALK + 1, -5):
                L.put(x, y, 23, "lava[level=8]")
            for p in ((x - 1, -5, 23), (x + 1, -5, 23), (x, -5, 22)):
                bp.set(*p, GBS)
            bp.set(x, -4, 23, "gold_block")
    for x in (x0, x1):
        bp.set(x, WALK, 23, "gold_block")
        L.put(x, WALK + 1, 23, BARS)
    # lights and ribs
    for x in range(x0 + 1, x1, 4):
        for z in range(z0, z1 + 1):
            L.put(x, -5, z, "polished_basalt[axis=z]")
        bp.lantern(x + 2, -5, 20, hanging=True)
    # the far west end: a crypt of brutes with a spawner among bones and gold
    bp.spawner(x0, WALK, 20, "minecraft:piglin_brute")
    for z in (19, 21):
        L.put(x0, WALK, z, "bone_block[axis=y]")
        L.put(x0, WALK + 1, z, "piglin_head[rotation=4]")
    bp.set(x0 - 1, -6, 20, LAMP)


def _site_of_grace(L):
    """A bay across from the treasury gate (walk -9): waystone, benches, soul lights."""
    bp = L.bp
    _room(L, -4, 4, 24, 27, FLOOR_Y, -4)
    L.air(-4, WALK, 23, 4, -5, 23)
    for x in range(-4, 5):
        for z in range(19, 28):
            if abs(x) <= 1:
                bp.set(x, FLOOR_Y, z, "red_nether_bricks" if x == 0 else GBS)
    bp.set(0, WALK, 27, MOD["waystone"])
    for x in (-1, 1):
        L.put(x, WALK, 27, "candle[candles=3,lit=true,waterlogged=false]")
    for z in (25, 26):
        L.put(-4, WALK, z, stair(PBS, "east"))
        L.put(4, WALK, z, stair(PBS, "west"))
    for x in (-4, 4):
        L.put(x, WALK, 27, "soul_lantern[hanging=false,waterlogged=false]")
        L.put(x, WALK, 24, "soul_lantern[hanging=false,waterlogged=false]")
    bp.lantern(0, -5, 25, hanging=True, soul=True)
    bp.set(0, -6, 28, LAMP)


# ------------------------------------------------------------------ the King's Treasury
def _ceiling(x, z):
    """Highest air level over (x, z): the lifted sanctum floor in the middle, pointed vaults in the apses."""
    if abs(z) <= APSE:
        return LIFT - 2           # air up to y=0, the sanctum floor (y=1) above
    return 4 - max(0, abs(x) - 6) // 2


def _treasury(L):
    bp = L.bp
    for x in range(-HALF_X - 1, HALF_X + 2):
        for z in range(-HALF_Z - 1, HALF_Z + 2):
            edge = abs(x) == HALF_X + 1 or abs(z) == HALF_Z + 1
            top = _ceiling(max(-HALF_X, min(HALF_X, x)), max(-HALF_Z, min(HALF_Z, z)))
            bp.set(x, FLOOR_Y, z, _floor(x, z) if not edge else WALL.pick(x, FLOOR_Y, z))
            for y in range(WALK, top + 2):
                if y == top + 1 and abs(z) <= APSE:
                    continue        # the lifted sanctum floor (and its walls) is the ceiling here
                if edge or y == top + 1:
                    bp.set(x, y, z, WALL.pick(x, y, z))
                else:
                    L.air(x, y, z, x, y, z)
    # wall dressing: gilded plinth course and string course
    for x in range(-HALF_X - 1, HALF_X + 2):
        for z in range(-HALF_Z - 1, HALF_Z + 2):
            if abs(x) == HALF_X + 1 or abs(z) == HALF_Z + 1:
                bp.set(x, WALK, z, GBS)
                bp.set(x, -3, z, GILD)
    # the arch between the hall and each apse (under the sanctum walls, |z| = 12)
    for sz in (-1, 1):
        z = sz * APSE
        for x in range(-HALF_X, HALF_X + 1):
            if abs(x) >= 9:
                for y in range(WALK, 1):
                    L.put(x, y, z, WALL.pick(x, y, z))
            elif abs(x) >= 7:
                L.put(x, 0, z, stair(PBBS, "east" if x < 0 else "west", "top"))
    # colonnades: 2x2 columns of basalt banded in gold, carrying the sanctum
    for sx in (-1, 1):
        for (za, zb) in COLS:
            top = _ceiling(sx * 8, za)
            for x in (sx * 8, sx * 9):
                for z in (za, zb):
                    for y in range(WALK, top + 1):
                        L.put(x, y, z, CHIS if y == WALK else "gold_block" if y in (WALK + 4, top) else PBAS)
            for z in (za, zb):
                L.put(sx * 7, top, z, stair(PBBS, "west" if sx < 0 else "east", "top"))
                L.put(sx * 10, top, z, stair(PBBS, "east" if sx < 0 else "west", "top"))
            # banners on the wall behind, crimson cloth between gold
            wx = sx * (HALF_X + 1)
            for z in (za, zb):
                for y in range(WALK + 1, -3):
                    bp.set(wx, y, z, "gold_block" if y in (WALK + 4, -4) else PBAS)
            if abs(za) < APSE:
                bp.set(sx * HALF_X, -4, za, "red_wall_banner[facing=%s]" % ("east" if sx < 0 else "west"))
                bp.set(sx * HALF_X, -4, zb, "red_wall_banner[facing=%s]" % ("east" if sx < 0 else "west"))
                L.open.update({(sx * HALF_X, -4, za), (sx * HALF_X, -4, zb)})
    # gold heaped along the side walls between the columns (the edges only): stepped mounds, coins on top
    for sx in (-1, 1):
        for z in range(-HALF_Z + 3, HALF_Z - 2):
            if any(za <= z <= zb for (za, zb) in COLS) or abs(z) <= 1:
                continue
            h_wall = 2 + (1 if (z * 5 + sx * 3) % 3 else 0)
            for x, h in ((sx * HALF_X, h_wall), (sx * (HALF_X - 1), h_wall - 1)):
                for k in range(h):
                    L.put(x, WALK + k, z, HEAP.pick(x, WALK + k, z))
                cap = "light_weighted_pressure_plate[power=0]" if (x + z) % 3 else CANDLES
                L.put(x, WALK + h, z, cap)
    for sx in (-1, 1):
        for (x, z, h) in ((3, -17, 2), (4, -17, 2), (4, -16, 1), (3, -16, 1), (4, -15, 1)):
            for k in range(h):
                L.put(sx * x, WALK + 1 + k, z, HEAP.pick(sx * x, WALK + 1 + k, z))
            L.put(sx * x, WALK + 1 + h, z, "light_weighted_pressure_plate[power=0]")
    # lava fountains in the four apse corners: a gilded basin fed by a spout in the end wall
    for sx in (-1, 1):
        for sz in (-1, 1):
            xs = (sx * 10, sx * 11)
            zs = (sz * 16, sz * 17)
            for x in range(sx * 9, sx * 12, sx):
                for z in range(sz * 15, sz * 18, sz):
                    if x in xs and z in zs:
                        bp.set(x, WALK, z, "lava[level=0]")
                        L.air(x, WALK + 1, z, x, WALK + 1, z)
                    else:
                        L.put(x, WALK, z, "gold_block" if (x + z) % 2 else GBS)
            spout_x = sx * 10
            spout_y = _ceiling(spout_x, sz * 17) - 1
            bp.set(spout_x, spout_y, sz * 17, "lava[level=0]")
            for y in range(WALK + 1, spout_y):
                L.put(spout_x, y, sz * 17, "lava[level=8]")
            for p in ((spout_x - 1, spout_y, sz * 17), (spout_x + 1, spout_y, sz * 17), (spout_x, spout_y, sz * 16)):
                bp.set(*p, GBS)
            bp.set(spout_x, spout_y + 1, sz * 17, "gold_block")
    # the King's throne in the north apse, before a great sun disc of gold
    zt = -HALF_Z
    for x in range(-4, 5):
        for z in range(zt, zt + 4):
            L.put(x, WALK, z, GBS if abs(x) == 4 or z == zt + 3 else PBB)
        L.put(x, WALK, zt + 3, stair(PBBS, "south"))
    for x in range(-2, 3):
        for z in range(zt, zt + 2):
            L.put(x, WALK + 1, z, "gold_block")
        L.put(x, WALK + 1, zt + 2, stair(PBBS, "south"))
    L.put(0, WALK + 2, zt + 1, stair("crimson_stairs", "south"))
    for x in (-1, 1):
        L.put(x, WALK + 2, zt + 1, "gold_block")
        L.put(x, WALK + 3, zt + 1, "candle[candles=2,lit=true,waterlogged=false]")
    for y in range(WALK + 2, WALK + 6):
        L.put(0, y, zt, "gold_block" if y < WALK + 5 else "raw_gold_block")
        L.put(-1, y, zt, GBS if y < WALK + 4 else "air")
        L.put(1, y, zt, GBS if y < WALK + 4 else "air")
    L.put(0, WALK + 6, zt, "piglin_head[rotation=0]")
    wz = zt - 1
    for x in range(-4, 5):
        for y in range(WALK + 1, 4):
            d = ((x / 4.2) ** 2 + ((y + 1.5) / 5.0) ** 2)
            if d <= 1.0:
                bp.set(x, y, wz, "gold_block" if d < 0.45 else "raw_gold_block" if d < 0.8 else GILD)
    bp.set(0, -1, wz, LAMP)
    for x in (-6, 6):
        _brazier_gold(L, x, WALK, zt + 1)
    # the seal at the centre of the hall
    bp.boss_seal(0, WALK, 0, "wayfarers:piglin_king", 14)
    L.open.add((0, WALK, 0))
    # chandeliers under the sanctum floor
    for (x, z) in ((-4, -6), (4, -6), (-4, 6), (4, 6)):
        _chandelier(L, x, 1, z)


def _brazier_gold(L, x, y, z):
    L.put(x, y, z, CHIS)
    L.put(x, y + 1, z, PBBW)
    L.put(x, y + 2, z, "gold_block")
    L.put(x, y + 3, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def _floor(x, z):
    """Treasury floor: blackstone with a gilded border, a crimson runner from the gate to the throne and
    a sun of gold around the seal."""
    d = math.hypot(x, z)
    ang = math.degrees(math.atan2(z, x)) % 30
    if d < 1.5:
        return GBS
    if 1.5 <= d < 4.5 and (ang < 5 or ang > 25):
        return "gold_block"
    if 4.5 <= d < 5.3:
        return GILD
    if d < 4.5:
        return PBB
    if abs(x) == 0:
        return "red_nether_bricks"
    if abs(x) == 1:
        return GBS if z % 3 == 0 else PB
    if abs(x) == 7:
        return CHIS
    return PB if (x + z) % 2 else PBB


def _royal_vault(L):
    """Behind the north apse, east: the King's vault, barred until he falls (walk -9)."""
    bp = L.bp
    _room(L, 2, 9, -23, -20, FLOOR_Y, -4)
    for x in (5, 6):
        L.air(x, WALK, -19, x, WALK + 2, -19)
        bp.set(x, FLOOR_Y, -19, PBB)
        for y in range(WALK, WALK + 3):
            bp.set(x, y, -18, MOD["vault_bars"])
    bp.set(5, WALK + 3, -18, GILD)
    bp.set(6, WALK + 3, -18, GILD)
    for x in range(2, 10):
        for z in range(-23, -19):
            bp.set(x, FLOOR_Y, z, "gold_block" if (x + z) % 3 == 0 else GBS)
    bp.chest(5, WALK, -23, "south", LOOT + "piglin_sanctuary")
    bp.chest(8, WALK, -22, "west", LOOT + "piglin_sanctuary")
    for (x, z, h) in ((2, -23, 3), (3, -23, 2), (2, -22, 2), (9, -23, 3), (9, -20, 1), (2, -20, 1)):
        for k in range(h):
            L.put(x, WALK + k, z, HEAP.pick(x, WALK + k, z))
    L.put(9, WALK + 3, -23, CANDLES)
    L.put(2, WALK + 3, -23, CANDLES)
    _piglin_post(L, 6, WALK, -21, 0)
    bp.lantern(5, -5, -21, hanging=True)


def piglin_king_lair(bp):
    """Carve the King's Treasury under the Piglin Sanctuary. Call at the end of nether.piglin_sanctuary()."""
    L = _Lair(bp)
    _lift_sanctum(L)
    _tithe_stair(L)
    _hall_of_tribute(L)
    _smelting_way(L)
    _smelting_stair(L)      # after the gallery: its last steps cut through the gallery's east wall
    _treasury(L)
    _site_of_grace(L)       # after the treasury: it opens the bay south of the gate
    _royal_vault(L)
    # the treasury gate, in the south wall (z=18) across from the site of grace
    L.air(-2, WALK, HALF_Z + 1, 2, WALK + 3, HALF_Z + 1)
    L.air(-1, WALK + 4, HALF_Z + 1, 1, WALK + 4, HALF_Z + 1)
    for y in range(WALK, WALK + 5):
        bp.set(-3, y, HALF_Z + 1, CHIS)
        bp.set(3, y, HALF_Z + 1, CHIS)
    bp.set(0, WALK + 5, HALF_Z + 1, GILD)
    bp.mist(-2, WALK, HALF_Z + 1, 2, WALK + 4, HALF_Z + 1)
    L.seal()
