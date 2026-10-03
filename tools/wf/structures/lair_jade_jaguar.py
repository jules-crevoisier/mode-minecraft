"""Lair of the Jade Jaguar, under the Jungle Ziggurat.

Nothing lay under the pyramid until now. The way down starts in the **secret tomb** behind the treasure hall's
cracked north panel (x -4..4, z -17..-10, floor y 0, see ``ziggurat`` in overworld_b.py):

* **The serpent stair** leaves the tomb's north wall and dives 14 blocks under the forecourt.
* **The passage of masks** (walk y -13) runs west for 38 blocks: carved jade masks with glowing eyes, roots
  breaking through the vault, a guard alcove (skeleton spawner), a hidden offering niche, and three dart traps
  (pressure plates that fire the dispensers set in the north wall).
* **The root stair**, a rough cave stair, drops 22 more blocks to the south (cave spider spawner on a ledge), then
  a short landing leads to the **site of grace**: a shrine room with the waystone, benches and candles.
* **The sacred cenote** (walk y -35): a vast cavern (radius 24, 22 high) with a ring of still water around the
  **sacrificial platform** (radius 13, a carved sun-stone floor), six jaguar stelae around its rim, hanging vines
  and glow berries, and three **light wells** that bring real daylight down from the pyramid's terraces. Two
  causeways cross the water; the mist closes both.
* **The hoard grotto** east of the cenote holds the reward.
"""
import math
import random

from .. import nbt
from ..arch import Palette, stair
from ..parts import LOOT, MOD

AIR = "air"
WATER = "water[level=0]"
CARVED = Palette({"tuff_bricks": 4, "chiseled_tuff_bricks": 1, "mossy_stone_bricks": 2, "polished_tuff": 1}, seed=91, scale=2.5)
ROCK = Palette({"stone": 4, "tuff": 3, "mossy_cobblestone": 1, "andesite": 1, "cobblestone": 1}, seed=92, scale=3.0)
JADE = Palette({"oxidized_cut_copper": 3, "weathered_cut_copper": 1, "oxidized_copper": 1}, seed=93, scale=2.0)
EYE = "verdant_froglight[axis=y]"
GOLD = "gold_block"

L1 = -13           # walking level of the passage of masks (floor blocks at y -14)
L3 = -35           # walking level of the grace, the causeways and the platform (top blocks at y -36)
WY = -37           # water surface (top water blocks)
CR, CTOP, CBOT = 24, -15, -41   # cavern radius, roof and floor
PR = 13            # platform radius
SEAL_R = 16


def build(bp):
    rng = random.Random(77)
    _cenote(bp, rng)                 # the cavern first: the passages and rooms are cut through its rock shell
    _platform(bp, rng)
    _serpent_stair(bp)
    _passage(bp, rng)
    _root_stair(bp, rng)
    _grace(bp)
    _light_wells(bp, rng)
    _hoard(bp, rng)
    _mists(bp)


# ------------------------------------------------------------------ helpers
def _noise(x, y, z, seed=0):
    return (math.sin(x * 0.37 + seed) * math.cos(z * 0.31 - seed * 0.7) + math.sin(y * 0.45 + x * 0.13 + seed * 1.3)) * 0.5


def _tube(bp, x0, x1, y0, y1, z0, z1, wall=CARVED, floor=None, ceiling=None):
    """A corridor box: walls of the palette around a cleared interior (x0..x1 etc. are the wall planes)."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(y0, y1 + 1):
                if y == y0:
                    bp.set(x, y, z, floor or wall.pick(x, y, z))
                elif y == y1:
                    bp.set(x, y, z, ceiling or wall.pick(x, y, z))
                else:
                    bp.set(x, y, z, wall.pick(x, y, z) if edge else AIR)


def _mask(bp, x, y, z, facing):
    """A jade mask carved in a wall (the wall plane is at x/z, the face looks toward ``facing``)."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
    ux, uz = (1, 0) if dz else (0, 1)
    for u in (-1, 0, 1):
        for v in (0, 1, 2):
            bp.set(x + ux * u, y + v, z + uz * u, "oxidized_copper" if v == 2 or u == 0 else "oxidized_cut_copper")
    bp.set(x - ux, y + 1, z - uz, EYE)
    bp.set(x + ux, y + 1, z + uz, EYE)
    bp.set(x, y, z, "chiseled_tuff")
    bp.set(x + dx, y + 2, z + dz, stair("oxidized_cut_copper_stairs", {"north": "south", "south": "north",
                                                                          "east": "west", "west": "east"}[facing], "top"))


def _dart_trap(bp, x, z_wall, z_plate):
    """A pressure plate in front of a dispenser hidden in the wall: stepping on it fires arrows across it."""
    facing = "south" if z_plate > z_wall else "north"
    items = nbt.List([nbt.Compound({"Slot": nbt.Byte(0), "id": nbt.String("minecraft:arrow"), "count": nbt.Int(24)})])
    bp.set(x, L1, z_wall, f"dispenser[facing={facing},triggered=false]", {"Items": items})
    bp.set(x, L1, z_plate, "polished_blackstone_pressure_plate[powered=false]")


# ------------------------------------------------------------------ the serpent stair (tomb -> passage)
def _serpent_stair(bp):
    # the tomb's north wall opens behind the sarcophagus under a lintel of jade
    bp.clear(-1, 1, -17, 1, 3, -17)
    for x in (-2, 2):
        bp.fill(x, 1, -17, x, 4, -17, "chiseled_tuff_bricks")
    for x in range(-2, 3):
        bp.set(x, 4, -17, "oxidized_cut_copper" if x else EYE)
    for i in range(14):
        y, z = -i, -18 - i
        for x in range(-1, 2):
            bp.set(x, y, z, stair("tuff_brick_stairs", "south"))
            bp.set(x, y - 1, z, "tuff_bricks")
            for c in range(1, 5):
                bp.set(x, y + c, z, AIR)
            bp.set(x, y + 5, z, "tuff_bricks" if i % 4 else "chiseled_tuff_bricks")
        for x in (-2, 2):
            for yy in range(y - 1, y + 6):
                bp.set(x, yy, z, "oxidized_cut_copper" if yy == y + 1 else CARVED.pick(x, yy, z))
        if i % 4 == 2:
            bp.lantern(0, y + 4, z, hanging=True, soul=True)


# ------------------------------------------------------------------ the passage of masks (walk y -13)
def _passage(bp, rng):
    x0, x1, z0, z1 = -39, 2, -35, -31
    _tube(bp, x0, x1, L1 - 1, L1 + 5, z0, z1, floor="mossy_stone_bricks", ceiling="tuff_bricks")
    bp.clear(-1, L1, z1, 1, L1 + 3, z1)                     # the serpent stair arrives from the south
    # the floor: a processional band of jade between worn flagstones
    for x in range(x0 + 1, x1):
        bp.set(x, L1 - 1, -33, "oxidized_cut_copper" if x % 3 else "chiseled_tuff")
    for x in range(x0 + 1, x1, 6):
        _mask(bp, x, L1 + 1, z0, "south")
        _mask(bp, x + 3, L1 + 1, z1, "north")
    # roots breaking through the vault, moss on the stones
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            r = rng.random()
            if r < 0.10:
                bp.set(x, L1 + 4, z, "hanging_roots[waterlogged=false]")
            elif r < 0.16:
                bp.set(x, L1, z, "moss_carpet")
            elif r < 0.19:
                bp.set(x, L1 + 4, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    # three dart traps (dispensers in the north wall), the plates just in front of them
    for x in (-9, -19, -29):
        _dart_trap(bp, x, z0, z0 + 1)
        bp.set(x - 1, L1 + 2, z0, "chiseled_tuff")
        bp.set(x + 1, L1 + 2, z0, "chiseled_tuff")
    # a guard alcove with a spawner, and a hidden offering niche behind cracked bricks
    for x in range(-25, -22):
        for z in (z1, z1 + 1, z1 + 2):
            for y in range(L1, L1 + 3):
                bp.set(x, y, z, AIR)
        bp.set(x, L1 - 1, z1 + 1, "mossy_stone_bricks")
        bp.set(x, L1 - 1, z1 + 2, "mossy_stone_bricks")
        bp.set(x, L1 + 3, z1 + 1, "tuff_bricks")
        bp.set(x, L1 + 3, z1 + 2, "tuff_bricks")
    for z in (z1 + 1, z1 + 2, z1 + 3):
        for y in range(L1 - 1, L1 + 4):
            for x in (-26, -22):
                bp.set(x, y, z, CARVED.pick(x, y, z))
    bp.fill(-25, L1 - 1, z1 + 3, -23, L1 + 3, z1 + 3, "tuff_bricks")
    bp.spawner(-24, L1, z1 + 2, "minecraft:skeleton")
    bp.set(-6, L1, z0, "cracked_stone_bricks")
    bp.set(-6, L1 + 1, z0, "cracked_stone_bricks")
    bp.clear(-6, L1, z0 - 2, -6, L1 + 1, z0 - 1)
    bp.fill(-7, L1 - 1, z0 - 3, -5, L1 + 2, z0 - 3, "tuff_bricks")
    for x in (-7, -5):
        bp.fill(x, L1 - 1, z0 - 2, x, L1 + 2, z0 - 1, "tuff_bricks")
    bp.set(-6, L1 - 1, z0 - 2, "tuff_bricks")
    bp.set(-6, L1 + 2, z0 - 2, "tuff_bricks")
    bp.set(-6, L1 + 2, z0 - 1, "tuff_bricks")
    bp.chest(-6, L1, z0 - 2, "south", LOOT + "ziggurat")
    # torches on the masks' brows are too bright for a tomb: soul lanterns on chains instead
    for x in range(x0 + 4, x1, 8):
        bp.chain(x, L1 + 4, -33, L1 + 4)
        bp.lantern(x, L1 + 3, -33, hanging=True, soul=True)
    # the end of the passage turns south into the root stair
    bp.clear(-38, L1, z1, -36, L1 + 3, z1)


# ------------------------------------------------------------------ the root stair (walk -13 -> -35)
def _root_stair(bp, rng):
    for i in range(22):
        y, z = L1 - 1 - i, -31 + i
        for x in range(-41, -33):
            inner = -38 <= x <= -36
            for yy in range(y - 2, y + 7):
                rough = abs(x + 37) + (0.6 if _noise(x, yy, z, 3) > 0.3 else 0) >= 3.2 or yy <= y - 1 or yy >= y + 5
                if inner and y <= yy < y + 5:
                    continue
                if rough or not inner:
                    bp.set(x, yy, z, ROCK.pick(x, yy, z))
        for x in range(-38, -35):
            bp.set(x, y, z, stair("cobblestone_stairs" if (x + i) % 3 else "mossy_cobblestone_stairs", "north"))
            for c in range(1, 5):
                bp.set(x, y + c, z, AIR)
        if i % 3 == 0:
            bp.set(-37, y + 4, z, "glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]")
        if rng.random() < 0.3:
            bp.set(rng.choice((-38, -36)), y + 4, z, "hanging_roots[waterlogged=false]")
    # a ledge in the east wall halfway down, where the spiders nest
    for z in range(-22, -19):
        for x in (-35, -34):
            for y in range(L1 - 12, L1 - 9):
                bp.set(x, y, z, AIR)
            bp.set(x, L1 - 13, z, "mossy_cobblestone")
    bp.spawner(-34, L1 - 12, -21, "minecraft:cave_spider")
    bp.set(-35, L1 - 12, -20, "cobweb")
    bp.set(-34, L1 - 10, -22, "cobweb")
    # landing at the bottom (walk -35), lit by a lantern, turning east to the grace
    _tube(bp, -39, -35, L3 - 1, L3 + 4, -10, 2, wall=ROCK, floor="mossy_stone_bricks")
    bp.lantern(-37, L3 + 3, -5, hanging=True)


# ------------------------------------------------------------------ the site of grace
def _grace(bp):
    x0, x1, z0, z1 = -35, -27, -6, 6
    _tube(bp, x0, x1, L3 - 1, L3 + 6, z0, z1, floor="polished_tuff", ceiling="tuff_bricks")
    bp.clear(x0, L3, -1, x0, L3 + 3, 1)                     # from the landing
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if (x + z) % 4 == 0:
                bp.set(x, L3 - 1, z, "chiseled_tuff")
    cx, cz = -31, 0
    bp.fill(cx - 1, L3 - 1, cz - 1, cx + 1, L3 - 1, cz + 1, "oxidized_cut_copper")
    bp.set(cx, L3 - 1, cz, GOLD)
    bp.set(cx, L3, cz, MOD["waystone"])
    for (x, z) in ((cx - 2, cz - 3), (cx + 2, cz - 3), (cx - 2, cz + 3), (cx + 2, cz + 3)):
        bp.set(x, L3, z, "chiseled_tuff_bricks")
        bp.set(x, L3 + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    for x in range(cx - 1, cx + 2):
        bp.stairs(x, L3, z0 + 1, "jungle_stairs", "south")
        bp.stairs(x, L3, z1 - 1, "jungle_stairs", "north")
    bp.chain(cx, L3 + 5, cz, L3 + 5)
    bp.lantern(cx, L3 + 4, cz, hanging=True)
    for z in (z0, z1):
        _mask(bp, cx, L3 + 2, z, "south" if z == z0 else "north")
    for (x, z) in ((x0 + 1, z0 + 1), (x0 + 1, z1 - 1)):
        bp.set(x, L3, z, "potted_fern")
    bp.set(x1 - 1, L3, z0 + 1, "decorated_pot[facing=west,waterlogged=false,cracked=false]")
    # the passage east to the cenote: a carved gate in the rock
    for x in range(x1, -21):
        for z in range(-2, 3):
            for y in range(L3 - 1, L3 + 6):
                inner = abs(z) <= 1 and L3 <= y <= L3 + 3
                bp.set(x, y, z, AIR if inner else ("mossy_stone_bricks" if y == L3 - 1 else CARVED.pick(x, y, z)))
    for z in (-2, 2):
        bp.fill(-24, L3, z, -24, L3 + 4, z, "chiseled_tuff_bricks")
    for z in range(-2, 3):
        bp.set(-24, L3 + 4, z, "oxidized_cut_copper" if z else EYE)


# ------------------------------------------------------------------ the sacred cenote (the arena)
def _cenote(bp, rng):
    up, down = CTOP - WY, WY - CBOT
    for x in range(-CR - 3, CR + 4):
        for z in range(-CR - 3, CR + 4):
            rho = math.hypot(x, z)
            for y in range(CBOT - 2, CTOP + 3):
                ry = up if y >= WY else down
                n = _noise(x, y, z, 7) * 0.08
                d = (rho / CR) ** 2 + ((y - WY) / ry) ** 2 - n
                if d <= 1.0:
                    if y <= WY and rho > PR - 0.5:
                        # the water ring, the shore climbing out of it near the cavern wall
                        shore = rho > CR - 4 + 1.5 * _noise(x, 0, z, 2)
                        if shore and y >= WY - (rho - (CR - 4)) * 0.8:
                            bp.set(x, y, z, "moss_block" if y == WY else ROCK.pick(x, y, z))
                        else:
                            bp.set(x, y, z, WATER)
                    else:
                        bp.set(x, y, z, AIR)
                elif d <= 1.35:
                    b = ROCK.pick(x, y, z)
                    if y > WY + 2 and rng.random() < 0.06:
                        b = "moss_block"
                    bp.set(x, y, z, b)
    # the cavern roof: hanging vines, glow berries, spore blossoms and stalactites
    for x in range(-CR, CR + 1):
        for z in range(-CR, CR + 1):
            top = None
            for y in range(CTOP + 2, WY, -1):
                if bp.get(x, y, z) == "minecraft:air" and bp.get(x, y + 1, z) not in (None, "minecraft:air"):
                    top = y
                    break
            if top is None:
                continue
            r = rng.random()
            if r < 0.04:
                n = rng.randint(3, 8)
                for k in range(n):
                    if bp.get(x, top - k, z) != "minecraft:air":
                        break
                    last = k == n - 1
                    berries = "true" if rng.random() < 0.35 else "false"
                    bp.set(x, top - k, z, f"cave_vines[age=25,berries={berries}]" if last else f"cave_vines_plant[berries={berries}]")
            elif r < 0.06:
                bp.set(x, top, z, "spore_blossom")
            elif r < 0.09:
                bp.set(x, top, z, "pointed_dripstone[thickness=frustum,vertical_direction=down,waterlogged=false]")
                bp.set(x, top - 1, z, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
    # jungle vines draped down the cavern walls (each strand hangs on the rock behind it)
    sides = (("north", 0, -1), ("south", 0, 1), ("west", -1, 0), ("east", 1, 0))
    for x in range(-CR - 1, CR + 2):
        for z in range(-CR - 1, CR + 2):
            for y in range(CTOP, WY + 3, -1):
                if bp.get(x, y, z) != "minecraft:air" or rng.random() > 0.05:
                    continue
                for face, dx, dz in sides:
                    wall = bp.get(x + dx, y, z + dz)
                    if wall in (None, "minecraft:air", "minecraft:water") or "vine" in wall:
                        continue
                    for k in range(rng.randint(3, 9)):
                        if bp.get(x, y - k, z) != "minecraft:air" or bp.get(x + dx, y - k, z + dz) in (None, "minecraft:air"):
                            break
                        bp.set(x, y - k, z, f"vine[{face}=true]")
                    break
    # lily pads, sea pickles and ferns on the shore
    for x in range(-CR, CR + 1):
        for z in range(-CR, CR + 1):
            if bp.get(x, WY, z) == "minecraft:water" and bp.get(x, WY + 1, z) == "minecraft:air":
                if rng.random() < 0.05:
                    bp.set(x, WY + 1, z, "lily_pad")
                elif rng.random() < 0.02:
                    bp.set(x, WY - 1, z, "sea_pickle[pickles=3,waterlogged=true]")
            elif bp.get(x, WY, z) == "minecraft:moss_block" and bp.get(x, WY + 1, z) == "minecraft:air":
                q = rng.random()
                if q < 0.25:
                    bp.set(x, WY + 1, z, "fern")
                elif q < 0.32:
                    bp.set(x, WY + 1, z, "large_fern[half=lower]")
                    bp.set(x, WY + 2, z, "large_fern[half=upper]")
                elif q < 0.36:
                    bp.set(x, WY + 1, z, "azalea")


def _platform(bp, rng):
    # the drum of the platform rises from the water floor
    for x in range(-PR - 1, PR + 2):
        for z in range(-PR - 1, PR + 2):
            rho = math.hypot(x, z)
            if rho > PR + 0.4:
                continue
            for y in range(CBOT - 1, L3 - 1):
                bp.set(x, y, z, "tuff_bricks" if rho > PR - 1 else "tuff")
            a = math.degrees(math.atan2(z, x)) % 360
            # the sun stone: a ring of glyph blocks, a band of jade, gold rays and the altar at the heart
            if rho > PR - 0.6:
                b = "polished_tuff"
            elif rho > PR - 1.6:
                b = "chiseled_tuff_bricks" if int(a // 12) % 2 else "tuff_bricks"
            elif rho > 9.5:
                b = "oxidized_cut_copper" if int(a // 8) % 3 else "chiseled_tuff"
            elif rho > 8.5:
                b = GOLD if int(a // 15) % 2 == 0 else "polished_tuff"
            elif rho > 4.5:
                b = ("oxidized_chiseled_copper" if int(a // 22.5) % 2 else "weathered_chiseled_copper") if int(a // 45) % 2 else "polished_tuff"
            elif rho > 3.5:
                b = "oxidized_cut_copper"
            elif rho > 1.5:
                b = "chiseled_tuff" if int(a // 30) % 2 else GOLD
            else:
                b = "chiseled_tuff_bricks"
            bp.set(x, L3 - 1, z, b)
            for y in range(L3, L3 + 22):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)
    # a rim of steps going down to the water all around
    for a in range(0, 360, 3):
        x = round(math.cos(math.radians(a)) * (PR + 1))
        z = round(math.sin(math.radians(a)) * (PR + 1))
        if math.hypot(x, z) > PR + 0.4 and bp.get(x, WY, z) == "minecraft:water":
            f = "east" if abs(x) >= abs(z) and x < 0 else "west" if abs(x) >= abs(z) else "south" if z < 0 else "north"
            bp.set(x, WY, z, stair("tuff_brick_stairs", f, "bottom"))
    # six jaguar stelae on the rim (the entrance axis z = 0 stays clear)
    for k, ang in enumerate((30, 90, 150, 210, 270, 330)):
        px = round(math.cos(math.radians(ang)) * (PR - 2.5))
        pz = round(math.sin(math.radians(ang)) * (PR - 2.5))
        _stela(bp, px, pz, 9 + (k % 2) * 2)
    # causeways west (from the grace) and east (to the hoard) across the water
    for side in (-1, 1):
        for i in range(PR - 1, CR + 1):
            x = side * i
            for z in range(-2, 3):
                bp.set(x, L3 - 1, z, ("oxidized_cut_copper" if z == 0 else "mossy_stone_bricks") if abs(z) < 2
                       else "tuff_bricks")
                for y in range(WY - 3, L3 - 1):
                    if abs(z) == 2 or i % 4 == 0:
                        bp.set(x, y, z, "tuff_bricks")
                for y in range(L3, L3 + 5):
                    if abs(z) < 2:
                        bp.set(x, y, z, AIR)
                if abs(z) == 2:
                    bp.set(x, L3, z, "tuff_brick_wall" if i % 3 else "chiseled_tuff_bricks")
                    if i % 6 == 0:
                        bp.set(x, L3 + 1, z, "lantern[hanging=false,waterlogged=false]")
    bp.boss_seal(0, L3 - 1, 0, "wayfarers:jade_jaguar", SEAL_R)


def _stela(bp, x, z, h):
    """A 2x2 stela carved with a jaguar head at the top (jade with glowing eyes and a gold diadem)."""
    for dx in (0, 1):
        for dz in (0, 1):
            for y in range(L3, L3 + h):
                bp.set(x + dx, y, z + dz, "chiseled_tuff_bricks" if (y - L3) % 4 == 0 else
                       "oxidized_cut_copper" if (y - L3) % 4 == 2 else "tuff_bricks")
    top = L3 + h
    for dx in (-1, 0, 1, 2):
        for dz in (-1, 0, 1, 2):
            bp.set(x + dx, top, z + dz, "oxidized_copper")
            bp.set(x + dx, top + 1, z + dz, "oxidized_cut_copper" if dx in (0, 1) or dz in (0, 1) else AIR)
    for dx in (0, 1):
        for dz in (0, 1):
            bp.set(x + dx, top + 2, z + dz, GOLD)
    # glowing eyes on every face
    for (ex, ez) in ((-1, 0), (-1, 1), (2, 0), (2, 1), (0, -1), (1, -1), (0, 2), (1, 2)):
        bp.set(x + ex, top + 1, z + ez, EYE)
    for dx in (0, 1):
        bp.set(x + dx, top + 3, z, "oxidized_copper")
        bp.set(x + dx, top + 3, z + 1, "oxidized_copper")


# ------------------------------------------------------------------ the light wells: daylight from the terraces
def _light_wells(bp, rng):
    for (sx, sz) in ((12, 12), (-14, 8), (7, -15)):
        m = max(abs(sx), abs(sz), abs(sx + 1), abs(sz + 1))
        t = max(k for k in range(8) if 29 - 3 * k >= m)       # the terrace of the highest tier that covers it
        top = 4 * t + 3
        for y in range(CTOP - 6, top + 1):
            for dx in range(-1, 3):
                for dz in range(-1, 3):
                    inner = dx in (0, 1) and dz in (0, 1)
                    cur = bp.get(sx + dx, y, sz + dz)
                    if inner:
                        bp.set(sx + dx, y, sz + dz, AIR if y < top else "iron_bars[east=true,north=true,south=true,waterlogged=false,west=true]")
                    elif cur is None or cur not in ("minecraft:air", "minecraft:water"):
                        bp.set(sx + dx, y, sz + dz, "mossy_stone_bricks" if (y + dx + dz) % 5 else "chiseled_stone_bricks")
        for dx in range(-1, 3):                              # a mossy rim around the grate on the terrace
            for dz in range(-1, 3):
                if not (dx in (0, 1) and dz in (0, 1)):
                    bp.set(sx + dx, top, sz + dz, "mossy_stone_bricks")
                bp.set(sx + dx, top + 1, sz + dz, AIR)
        # where the light falls: a patch of moss and flowers, and vines hanging around the hole
        for dx in range(-2, 4):
            for dz in range(-2, 4):
                x, z = sx + dx, sz + dz
                if bp.get(x, L3 - 1, z) is not None and bp.get(x, L3, z) == "minecraft:air" and math.hypot(x, z) < PR - 0.5:
                    continue                                   # the platform's carved floor stays clean
                ground = None
                for y in range(L3 + 3, WY - 2, -1):
                    if bp.get(x, y, z) == "minecraft:air" and bp.get(x, y - 1, z) not in (None, "minecraft:air", "minecraft:water"):
                        ground = y
                        break
                if ground is not None and rng.random() < 0.5:
                    bp.set(x, ground, z, rng.choice(["fern", "short_grass", "blue_orchid", "moss_carpet"]))


# ------------------------------------------------------------------ the hoard grotto (reward)
def _hoard(bp, rng):
    x0, x1, z0, z1 = CR + 1, CR + 13, -6, 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(L3 - 2, L3 + 8):
                d = ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2 + (z / ((z1 - z0) / 2)) ** 2 + ((y - L3) / 7.0) ** 2 * (1 if y > L3 else 9)
                n = _noise(x, y, z, 11) * 0.1
                if y >= L3 and d < 0.85 - n:
                    bp.set(x, y, z, AIR)
                elif d < 1.25:
                    bp.set(x, y, z, "mossy_stone_bricks" if y == L3 - 1 else ROCK.pick(x, y, z))
    # the way in from the east causeway
    for x in range(CR - 2, x0 + 2):
        for z in range(-1, 2):
            for y in range(L3, L3 + 4):
                bp.set(x, y, z, AIR)
            bp.set(x, L3 - 1, z, "mossy_stone_bricks")
    for z in (-2, 2):
        bp.fill(x0, L3, z, x0, L3 + 4, z, "chiseled_tuff_bricks")
    for z in range(-2, 3):
        bp.set(x0, L3 + 4, z, "oxidized_cut_copper" if z else EYE)
    # the hoard: a jade idol on a gold dais, chests, heaps of gold
    cx = x1 - 3
    bp.fill(cx - 1, L3 - 1, -2, cx + 1, L3 - 1, 2, GOLD)
    bp.fill(cx, L3, -1, cx, L3 + 2, 1, "oxidized_copper")
    bp.set(cx, L3 + 3, 0, "oxidized_cut_copper")
    bp.set(cx - 1, L3 + 2, -1, EYE)
    bp.set(cx - 1, L3 + 2, 1, EYE)
    bp.chest(cx - 2, L3, -1, "west", LOOT + "ziggurat")
    bp.chest(cx - 2, L3, 1, "west", LOOT + "ziggurat")
    for (x, z) in ((cx, -3), (cx + 1, -3), (cx, 3), (cx - 1, 3), (cx - 3, -4), (cx - 4, 4)):
        bp.set(x, L3, z, rng.choice([GOLD, "raw_gold_block", GOLD, "emerald_block"]))
    for (x, z) in ((cx - 5, -3), (cx - 5, 3)):
        bp.set(x, L3, z, "decorated_pot[facing=west,waterlogged=false,cracked=false]")
    bp.lantern(cx - 3, L3 + 4, 0, hanging=True)
    for z in (-4, 4):
        bp.set(cx - 1, L3, z, "soul_campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]")


# ------------------------------------------------------------------ the mist (after the gates are carved)
def _mists(bp):
    bp.mist(-24, L3, -1, -24, L3 + 3, 1)          # from the grace
    bp.mist(CR + 1, L3, -1, CR + 1, L3 + 3, 1)    # toward the hoard
