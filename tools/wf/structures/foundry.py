"""Geothermal Foundry: a steampunk ironworks built into the flank of a small volcano (Lot 7, mega-structures).

Layout, ground y = 0, the volcano to the north (z < 0):
  * the volcano (radius 34, rim 45 blocks up) with a smoking lava crater, magma gullies and steam vents,
  * the Forge of the Deep carved into it: a vaulted nave of iron columns, forge bays with blast furnaces and anvils,
    two steam hammers over a lava channel, and at the back the Heart, a domed chamber around a lava well,
  * the casting yard in front: a lava caldera with a bridge crane carrying a giant ladle, catwalks across,
  * two brick casting halls (sawtooth roofs, mezzanines, overhead cranes, furnace banks, rail lines),
  * four 55-block chimneys, geothermal pipes from the volcano to the halls, ore piles and a rail yard to the gate.
Style: tools/STYLE_STEAMPUNK.md (dark iron, soot bricks and basalt for mass; brass trims; lava and Edison light).
"""
import math

from .. import interior as INT
from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BARS, BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP,
                       IRON, IRON_SLAB, IRON_STAIRS, IRON_WALL, PIPES, SMOKE, SMOKE_SLAB, SMOKE_STAIRS, SMOKE_WALL,
                       TABLE, TREAD, TREAD_SLAB, AETHER, W, catwalk, chain, chimney, fbm, hang_lamp, hash01, hash3,
                       is_air, lattice_tower, lantern_post, out_facing, railing, ring_railing, smoke, vnoise)
from ..parts import LOOT

# volcano
VX, VZ, VR, VH = 0, -38, 35, 78
CRATER_R = 10
# forge nave carved into it
NAVE_X, NAVE_Z0, NAVE_Z1, NAVE_TOP = 11, -18, -44, 17
HEART_Z, HEART_R = -51, 8
# casting yard
POOL_X, POOL_Z, POOL_R = 0, 14, 9
CRANE_Y = 25
CAT_Y = 7
# halls (east one; the west one is mirrored)
HX0, HX1, HZ0, HZ1, HWALL = 22, 40, -8, 36, 12
PB = "polished_blackstone_bricks"
PBS = "polished_blackstone_brick_stairs"
PBSL = "polished_blackstone_brick_slab"
PBW = "polished_blackstone_brick_wall"


def cone_h(x, z):
    """Surface height of the volcano at (x, z), or None outside it: a concave stratovolcano cone with ridges and
    gullies, and a crater bowl at the top."""
    r = math.hypot(x - VX, z - VZ)
    a = math.atan2(z - VZ, x - VX)
    rr = VR * (0.9 + 0.2 * vnoise(math.cos(a) * 3 + 10, math.sin(a) * 3 + 10, 1.0, 11))
    if r > rr:
        return None
    n = fbm(x, z, 10.0, 3)
    ridge = 0.06 * math.sin(a * 7 + 2 * vnoise(x, z, 8.0, 5)) * min(1.0, r / 12)
    t = 1 - r / rr
    h = VH * t ** 1.4 * (0.93 + 0.12 * n + ridge)
    rim = VH * (1 - CRATER_R / VR) ** 1.4
    if r < CRATER_R:
        return int(rim - 7 + (r / CRATER_R) ** 2 * 6)
    if r < CRATER_R + 2:
        return int(max(h, rim + 1))
    return int(h)


def quarry_cut(x, z):
    """The forecourt is quarried out of the volcano's south flank: a flat cut in front of the portal, framed by
    stepped benches."""
    if z <= NAVE_Z0 - 1:
        return 999
    ax = abs(x)
    if ax <= 19:
        return 0
    return (ax - 19) * 3 + (2 if (ax - 19) % 2 else 0)


def rock(x, y, z, top):
    """Volcanic rock palette in strata: basalt and blackstone, grey tuff bands, obsidian and magma near the top."""
    band = vnoise(x * 0.35 + z * 0.2, y * 1.0, 3.0, 21)
    n = vnoise(x, z + y * 2, 7.0, 22)
    if y >= top - 1 and y > 40 and n < 0.3:
        return "magma_block"
    if band < 0.28:
        return "tuff" if y < 36 else "blackstone"
    if n < 0.45:
        return "basalt[axis=y]"
    if n < 0.75:
        return "blackstone"
    return "smooth_basalt"


# ------------------------------------------------------------------ ground and volcano
def ground(bp):
    for x in range(-54, 55):
        for z in range(-74, 54):
            r = math.hypot(x, (z - 4) * 1.05)
            edge = 47 + 6 * fbm(x, z, 11.0, 1)
            if r > edge and cone_h(x, z) is None:
                continue
            n = fbm(x, z, 6.0, 2)
            if r > edge - 4:
                spec = "coarse_dirt" if n < 0.45 else ("tuff" if n < 0.7 else "basalt[axis=y]")
            else:
                spec = ("blackstone" if n < 0.4 else "basalt[axis=y]" if n < 0.62 else
                        "smooth_basalt" if n < 0.85 else "magma_block")
            bp.set(x, 0, z, spec)
            for y in range(1, 11):
                bp.set(x, y, z, "air")


def volcano(bp):
    for x in range(VX - VR - 6, VX + VR + 7):
        for z in range(VZ - VR - 6, VZ + VR + 7):
            top = cone_h(x, z)
            if top is None or top < 1:
                continue
            top = min(top, quarry_cut(x, z))
            if top < 1:
                continue
            for y in range(0, top + 1):
                bp.set(x, y, z, rock(x, y, z, top))
            r = math.hypot(x - VX, z - VZ)
            # lava flows meandering down from the rim: a glowing magma core with a crust of obsidian
            ang = math.degrees(math.atan2(z - VZ, x - VX)) % 360
            for g in (40, 150, 215, 330):
                wob = (vnoise(r * 0.5, g, 1.0, 17) - 0.5) * 26
                d = abs((ang - g - wob + 180) % 360 - 180) * math.pi / 180 * r
                w = 0.8 + r / 22
                if d < w + 1.0 and CRATER_R < r < VR - 3:
                    bp.set(x, top, z, "magma_block" if d < w else "obsidian")
                    if d < w * 0.5 and r < VR - 8:
                        bp.set(x, top - 1, z, "magma_block")
            # an ash cap around the rim
            if top > VH * 0.5 and r > CRATER_R + 1 and bp.get(x, top, z) != "minecraft:magma_block" and \
                    vnoise(x, z, 3.0, 41) < 0.55:
                bp.set(x, top, z, "tuff" if hash01(x, z, 8) < 0.7 else "smooth_basalt")
            for y in range(top + 1, top + 4):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, "air")
    # crater: lava lake ringed with magma, smoke rising from vents
    floor = None
    for x in range(VX - CRATER_R, VX + CRATER_R + 1):
        for z in range(VZ - CRATER_R, VZ + CRATER_R + 1):
            r = math.hypot(x - VX, z - VZ)
            if r <= 7.5:
                top = cone_h(x, z)
                floor = top if floor is None else min(floor, top)
    for x in range(VX - 8, VX + 9):
        for z in range(VZ - 8, VZ + 9):
            r = math.hypot(x - VX, z - VZ)
            if r <= 7.5:
                top = cone_h(x, z)
                for y in range(floor, top + 1):
                    bp.set(x, y, z, "air")
                bp.set(x, floor - 1, z, "magma_block")
                bp.set(x, floor - 2, z, "basalt[axis=y]")
                if r <= 6.5:
                    bp.set(x, floor - 1, z, "lava[level=0]")
                    bp.set(x, floor - 2, z, "magma_block")
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        x, z = VX + round(math.cos(a) * 8), VZ + round(math.sin(a) * 8)
        top = cone_h(x, z)
        for y in range(top - 3, top + 1):
            bp.set(x, y, z, "basalt[axis=y]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + dx, top - 1, z + dz, "basalt[axis=y]")
        smoke(bp, x, top + 1, z)
        bp.set(x, top, z, "hay_block[axis=y]")
    # steam vents on the flanks
    for (x, z) in ((-20, -30), (18, -48), (-14, -62), (24, -26), (-26, -48), (10, -66)):
        top = cone_h(x, z)
        if top is None:
            continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + dx, top, z + dz, "smooth_basalt")
        bp.set(x, top, z, "hay_block[axis=y]")
        bp.set(x, top + 1, z, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


# ------------------------------------------------------------------ the Forge of the Deep (inside the volcano)
def nave_top(x):
    """Pointed vault: intrados height above the floor across the nave."""
    u = abs(x) / (NAVE_X + 0.5)
    return int(9 + (NAVE_TOP - 9) * (1 - u ** 1.7))


def nave(bp):
    for z in range(NAVE_Z1, NAVE_Z0 + 1):
        for x in range(-NAVE_X - 2, NAVE_X + 3):
            inside = abs(x) <= NAVE_X
            if not inside:
                # side walls: soot bricks with iron ribs
                for y in range(0, nave_top(NAVE_X) + 1):
                    bp.set(x, y, z, IRON if (z - NAVE_Z0) % 6 == 0 else SMOKE)
                continue
            top = nave_top(x)
            bp.set(x, 0, z, PB if (x + z) % 2 else "polished_blackstone")
            for y in range(1, top + 1):
                bp.set(x, y, z, "air")
            rib = (z - NAVE_Z0) % 6 == 0
            bp.set(x, top + 1, z, IRON if rib else SMOKE)
            bp.set(x, top + 2, z, IRON if rib else "blackstone")
            if rib and abs(x) < NAVE_X:
                bp.set(x, top, z, BRASS if abs(x) <= 1 else IRON)
    # lava channel under iron grating down the middle
    for z in range(NAVE_Z1 + 2, NAVE_Z0 - 2):
        for x in (-1, 0, 1):
            bp.set(x, -2, z, "magma_block")
            bp.set(x, -1, z, "lava[level=0]" if x == 0 else "magma_block")
            bp.set(x, 0, z, BARS if x == 0 else PB)
        for x in (-2, 2):
            bp.set(x, -1, z, "blackstone")
            bp.set(x, 0, z, "polished_blackstone" if z % 3 else BRASS)
    for z in (NAVE_Z1 + 1, NAVE_Z0 - 2):
        bp.set(0, -1, z, "blackstone")
        bp.set(0, 0, z, BRASS)
    # arcade of iron columns with brass capitals
    for z in range(NAVE_Z0 - 3, NAVE_Z1, -6):
        for x in (-7, 7):
            for y in range(1, 11):
                bp.set(x, y, z, IRON if y % 4 else GEAR)
            bp.set(x, 0, z, BRASS)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bp.set(x + dx, 1, z + dz, stair(IRON_STAIRS, out_facing(-dx, -dz)))
                bp.set(x + dx, 10, z + dz, stair(BRASS_STAIRS, out_facing(-dx, -dz), "top"))
            bp.set(x, 11, z, BRASS)
            for y in range(12, nave_top(x) + 1):
                bp.set(x, y, z, IRON)
            hang_lamp(bp, x + (2 if x > 0 else -2), 9, z, length=nave_top(x + (2 if x > 0 else -2)) - 10)
        # lamp over the channel
        hang_lamp(bp, 0, 12, z, length=NAVE_TOP - 12)
    # forge bays along the walls
    for i, z in enumerate(range(NAVE_Z0 - 6, NAVE_Z1 + 2, -6)):
        for side in (-1, 1):
            forge_bay(bp, side, z, i)
    portal(bp)
    steam_hammer(bp, -4, -29)
    steam_hammer(bp, 4, -37)
    heart(bp)


def forge_bay(bp, side, z, i):
    """A smith's bay between two ribs: a hooded double blast furnace, anvil, quench cauldron and tool rack."""
    x = side * NAVE_X
    f = "east" if side < 0 else "west"
    # hood: brick funnel above the furnaces climbing into the wall
    for dz in (-1, 0, 1):
        bp.set(x, 1, z + dz, "blast_furnace[facing=%s,lit=true]" % f)
        bp.set(x, 2, z + dz, "blast_furnace[facing=%s,lit=true]" % f if dz == 0 else SMOKE)
        bp.set(x - side, 4, z + dz, stair(SMOKE_STAIRS, f, "top"))
        bp.set(x, 4, z + dz, SMOKE)
        bp.set(x - side, 5, z + dz, SMOKE)
        bp.set(x - side * 2, 5, z + dz, stair(SMOKE_STAIRS, f, "top"))
        for y in range(6, nave_top(x - side) + 1):
            bp.set(x - side, y, z + dz, SMOKE if dz == 0 or y > 7 else stair(SMOKE_STAIRS, f, "top"))
    bp.set(x - side * 2, 6, z, BRASS)
    bp.set(x - side * 2, 7, z, GAUGE)
    ax = x - side * 3
    bp.set(ax, 1, z - 2, "anvil[facing=%s]" % ("north" if i % 2 else "south"))
    bp.set(ax, 1, z + 2, "lava_cauldron" if i % 2 == 0 else "water_cauldron[level=3]")
    bp.set(x - side, 1, z - 2, "smithing_table" if i % 2 else "grindstone[face=floor,facing=%s]" % f)
    if i % 2 == 0:
        bp.chest(x - side, 1, z + 2, f, loot=LOOT + "foundry_forge")
    else:
        bp.barrel(x - side, 1, z + 2, "up", loot=LOOT + "foundry_forge")


def portal(bp):
    """The volcano's iron gate: buttressed brick facade, pointed arch with brass archivolt and a gear rose window."""
    zf = NAVE_Z0 + 1   # facade plane

    def top_at(ax):
        return 34 - ax if ax <= 10 else 24

    for x in range(-17, 18):
        ax = abs(x)
        for y in range(0, top_at(ax) + 1):
            pil = ax in (12, 17) or ax == 6
            spec = IRON if pil else (SMOKE if y % 7 else BRASS)
            bp.set(x, y, zf, spec)
            bp.set(x, y, zf - 1, SMOKE)
            if pil and y < top_at(ax) - 1:
                bp.set(x, y, zf + 1, IRON if y % 6 else BRASS)
    # pediment coping in brass stairs, a cog finial on the apex
    for x in range(-11, 12):
        ax = abs(x)
        y = top_at(ax) + 1
        if ax == 0:
            bp.set(x, y, zf, BRASS)
        else:
            bp.set(x, y, zf, stair(BRASS_STAIRS, "west" if x > 0 else "east"))
            bp.set(x, y - 1, zf + 1, stair(BRASS_STAIRS, "north", "top"))
    for x in range(-17, -10):
        bp.set(x, 25, zf, BRASS_SLAB + "[type=bottom,waterlogged=false]")
        bp.set(-x, 25, zf, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    for dy in range(36, 41):
        bp.set(0, dy, zf, IRON)
    for dx, dy in ((-2, 38), (2, 38), (0, 40), (-1, 37), (1, 37), (-1, 39), (1, 39)):
        bp.set(dx, dy, zf, GEAR if abs(dx) == 2 or dy == 40 else BRASS)
    bp.set(0, 41, zf, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # two great buttresses flanking the archway, stepping down towards the yard
    for side in (-1, 1):
        for x in (side * 7, side * 8):
            for d in range(1, 5):
                top = 18 - d * 3
                for y in range(0, top + 1):
                    bp.set(x, y, zf + d, IRON if (y % 6 == 0 or x == side * 8) else SMOKE)
                bp.set(x, top + 1, zf + d, stair(IRON_STAIRS, "north"))
            bp.set(x, 19, zf, BRASS)
        bp.set(side * 7, 6, zf + 5, EDISON)
        bp.set(side * 7, 5, zf + 5, IRON)
        for y in range(0, 5):
            bp.set(side * 7, y, zf + 5, IRON)
    # buttress towers with smoking stacks
    for side in (-1, 1):
        for x in range(side * 13, side * 17 + side, side):
            for z in range(zf - 2, zf + 4):
                for y in range(0, 30):
                    edge = x in (side * 13, side * 16) or z in (zf - 2, zf + 3)
                    if edge or y in (0, 29):
                        bp.set(x, y, z, IRON if (y % 8 == 0 or (x in (side * 13, side * 16) and z in (zf - 2, zf + 3)))
                               else SMOKE)
        cx = side * 14 + side
        for z in range(zf - 1, zf + 3):
            for x in (side * 14, side * 15):
                bp.set(x, 30, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
        bp.set(side * 14, 30, zf, SMOKE)
        for y in range(30, 36):
            bp.set(side * 14, y, zf + 1, SMOKE)
        smoke(bp, side * 14, 36, zf + 1)
        bp.set(side * 15, 31, zf + 1, EDISON)
        for y in range(4, 28, 8):
            bp.set(cx, y, zf + 4, stair(IRON_STAIRS, "north"))
    # the pointed archway 9 wide, 13 high, with a brass archivolt and inner iron portcullis frieze
    hw = 4
    for x in range(-hw - 2, hw + 3):
        ax = abs(x)
        top = 13 if ax <= 1 else 12 if ax <= 2 else 11 if ax <= 3 else 9 if ax <= 4 else 0
        for z in (zf - 1, zf, zf + 1):
            for y in range(1, top + 1):
                bp.set(x, y, z, "air")
            if ax <= hw:
                bp.set(x, top + 1, z, BRASS)
                bp.set(x, top + 2, z, IRON if ax % 2 == 0 else BRASS)
        if ax == hw + 1:
            for y in range(1, 11):
                bp.set(x, y, zf + 1, BRASS if y % 3 == 0 else IRON)
    for x in range(-hw, hw + 1):
        bp.set(x, 13 if abs(x) <= 1 else 12 if abs(x) <= 2 else 11 if abs(x) <= 3 else 9, zf + 1, BARS)
    bp.set(0, 15, zf + 1, GEAR)
    # gear rose window
    cy = 20
    for x in range(-5, 6):
        for y in range(cy - 5, cy + 6):
            d = math.hypot(x, y - cy)
            if d <= 4.4:
                spoke = x == 0 or y == cy or abs(x) == abs(y - cy)
                bp.set(x, y, zf, GEAR if d < 1.2 else (IRON if spoke else "orange_stained_glass"))
                bp.set(x, y, zf - 1, "air" if d > 1.2 else IRON)
            elif d <= 5.4:
                tooth = (round(math.degrees(math.atan2(y - cy, x)) / 30)) % 2 == 0
                bp.set(x, y, zf, BRASS)
                if tooth:
                    bp.set(x, y, zf + 1, BRASS)
    # steps down to the yard
    for x in range(-6, 7):
        bp.set(x, 0, zf + 2, PB)
        bp.set(x, 0, zf + 3, PB)
    for x in (-6, 6):
        lantern_post(bp, x, 0, zf + 3, h=4)


def steam_hammer(bp, cx, cz):
    """A two-legged steam hammer: iron frame, copper cylinder, piston rod and a 3x3 hammer head over an anvil block."""
    for dx in (-2, 2):
        for y in range(1, 13):
            bp.set(cx + dx, y, cz, IRON if y % 4 else BRASS)
        bp.set(cx + dx, 0, cz, BRASS)
        bp.set(cx + dx, 1, cz - 1, stair(IRON_STAIRS, "south"))
        bp.set(cx + dx, 1, cz + 1, stair(IRON_STAIRS, "north"))
    for dx in range(-2, 3):
        bp.set(cx + dx, 13, cz, IRON)
        bp.set(cx + dx, 14, cz, BRASS if abs(dx) < 2 else IRON)
    for y in (10, 11, 12):
        for dx in (-1, 0, 1):
            bp.set(cx + dx, y, cz, PIPES if dx == 0 else COPPER)
    bp.set(cx, 9, cz, GAUGE)
    for y in (6, 7, 8):
        bp.set(cx, y, cz, "iron_chain[axis=y,waterlogged=false]" if y != 8 else IRON)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(cx + dx, 5, cz + dz, "iron_block")
            bp.set(cx + dx, 4, cz + dz, IRON if (dx or dz) else "iron_block")
            bp.set(cx + dx, 1, cz + dz, "polished_blackstone")
    bp.set(cx, 2, cz, "anvil[facing=east]")
    bp.set(cx, 1, cz, "iron_block")
    bp.set(cx + 3, 1, cz, W + "valve_wheel[facing=east]")
    bp.set(cx + 2, 2, cz + 1, W + "copper_pipe[axis=y]")


def heart(bp):
    """The Heart of the Forge: a domed round chamber around a lava well, girdled by geothermal pipes."""
    cz, r = HEART_Z, HEART_R
    for x in range(-r - 2, r + 3):
        for z in range(cz - r - 2, cz + r + 3):
            d = math.hypot(x, z - cz)
            if d > r + 1.5:
                continue
            for y in range(0, 20):
                dome = math.sqrt(max(0.0, (r + 0.5) ** 2 - d * d)) * 1.3 + 6
                if d > r + 0.4:
                    if y <= dome + 1 and z < cz + r - 1:
                        bp.set(x, y, z, SMOKE if y % 6 else BRASS)
                    continue
                if y == 0:
                    bp.set(x, 0, z, PB if d > 4.5 else BRASS if d > 3.5 else "magma_block")
                elif y < dome:
                    bp.set(x, y, z, "air")
                elif y < dome + 2:
                    rib = round(math.degrees(math.atan2(z - cz, x)) / 45) * 45
                    on_rib = abs(math.degrees(math.atan2(z - cz, x)) - rib) < 7
                    bp.set(x, y, z, BRASS if on_rib else IRON)
    # lava well
    for x in range(-3, 4):
        for z in range(cz - 3, cz + 4):
            d = math.hypot(x, z - cz)
            if d <= 2.5:
                bp.set(x, -1, z, "magma_block")
                bp.set(x, 0, z, "lava[level=0]")
            elif d <= 3.5:
                bp.set(x, -1, z, "blackstone")
                bp.set(x, 0, z, BRASS)
    ring_railing(bp, 0, 1, cz, 3)
    # four geothermal columns rising from the well rim to a great gear drum in the dome
    for k, (dx, dz) in enumerate(((5, 0), (-5, 0), (0, 5), (0, -5))):
        for y in range(1, 15):
            bp.set(dx, y, cz + dz, PIPES if y % 5 else AETHER)
        bp.set(dx, 15, cz + dz, BRASS)
    for x in range(-5, 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x, z - cz)
            if 3.6 < d <= 5.4:
                bp.set(x, 15, z, GEAR if (x + z) % 2 else BRASS)
    for y in range(13, 17):
        bp.set(0, y, cz, AETHER if y == 13 else IRON)
    # the vault on its dais at the back, gauges on the wall
    bp.set(0, 1, cz - 6, BRASS)
    bp.chest(0, 2, cz - 6, "south", loot=LOOT + "foundry_vault")
    for dx in (-1, 1):
        bp.set(dx, 1, cz - 6, stair(BRASS_STAIRS, "west" if dx > 0 else "east"))
        bp.set(dx * 2, 1, cz - 7, W + "copper_pipe[axis=y]")
        bp.set(dx * 2, 2, cz - 7, W + "copper_pipe[axis=y]")
    for x in range(-4, 5):
        if abs(x) > 1:
            z = cz - int(math.sqrt(max(0, 64 - x * x)))
            bp.set(x, 3, z, GAUGE)
    # doorway from the nave
    for x in range(-3, 4):
        for z in range(NAVE_Z1 - 1, cz - r + 3):
            for y in range(1, 8 if abs(x) < 3 else 6):
                bp.set(x, y, z, "air")
            bp.set(x, 0, z, PB)
    for x in (-4, 4):
        for y in range(0, 9):
            bp.set(x, y, NAVE_Z1 - 1, BRASS if y % 4 == 0 else IRON)


# ------------------------------------------------------------------ the casting yard
def yard(bp):
    # paved yard with tread-plate paths
    for x in range(-44, 45):
        for z in range(-16, 48):
            r = math.hypot(x, (z - 4) * 1.05)
            if r > 44 or not is_air(bp, x, 1, z) and bp.get(x, 0, z) is None:
                continue
            if bp.get(x, 1, z) not in (None, "minecraft:air"):
                continue
            if bp.get(x, 0, z) is not None and bp.get(x, 0, z).endswith("magma_block") and r > 30:
                continue
            path = abs(x) <= 2 or abs(z - 40) <= 1 or (abs(z - 14) <= 1 and abs(x) > POOL_R + 2)
            n = vnoise(x, z, 4.0, 31)
            if path:
                bp.set(x, 0, z, TREAD if (x + z) % 5 else IRON)
            elif r < 38:
                bp.set(x, 0, z, PB if n < 0.55 else ("polished_blackstone" if n < 0.8 else "cracked_polished_blackstone_bricks"))
    # the caldera: a lava basin with a brass-trimmed rim
    for x in range(-POOL_R - 3, POOL_R + 4):
        for z in range(POOL_Z - POOL_R - 3, POOL_Z + POOL_R + 4):
            d = math.hypot(x - POOL_X, z - POOL_Z)
            if d <= POOL_R + 0.4:
                bp.set(x, -3, z, "magma_block")
                bp.set(x, -2, z, "lava[level=0]")
                bp.set(x, -1, z, "lava[level=0]")
                bp.set(x, 0, z, "air")
            elif d <= POOL_R + 1.4:
                for y in (-3, -2, -1):
                    bp.set(x, y, z, "blackstone")
                bp.set(x, 0, z, BRASS)
            elif d <= POOL_R + 2.4:
                bp.set(x, 0, z, "polished_blackstone")
    ring_railing(bp, POOL_X, 1, POOL_Z, POOL_R + 1, gaps=[lambda dx, dz: False])
    # remove the railing where the rim cell holds it: railings stand on the brass ring
    lamps = [(POOL_R + 3, 0), (-POOL_R - 3, 0), (0, POOL_R + 3)]
    for dx, dz in lamps:
        lantern_post(bp, POOL_X + dx, 0, POOL_Z + dz, h=4)


def crane(bp):
    """Bridge crane over the caldera: four lattice legs, two runway girders, a bridge with trolley and the ladle."""
    legs = [(-14, 5), (14, 5), (-14, 23), (14, 23)]
    for (x, z) in legs:
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                bp.set(x + dx, 0, z + dz, IRON if max(abs(dx), abs(dz)) == 2 else PB)
        lattice_tower(bp, x, z, 1, CRANE_Y - 1, r=2, band_every=6,
                      ladder_face="west" if x < 0 else "east")
    for x in (-14, 14):
        for z in range(3, 26):
            for dx in (-1, 0, 1):
                bp.set(x + dx, CRANE_Y, z, IRON if dx else BRASS)
                bp.set(x + dx, CRANE_Y + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if dx else "rail[shape=north_south,waterlogged=false]")
            if z % 3 == 0:
                bp.set(x, CRANE_Y - 1, z, stair(IRON_STAIRS, "west" if x > 0 else "east", "top"))
    # the bridge across, 3 wide, with the trolley
    for x in range(-15, 16):
        for dz in (-1, 0, 1):
            bp.set(x, CRANE_Y + 2, POOL_Z + dz, IRON if dz else TREAD)
            bp.set(x, CRANE_Y + 3, POOL_Z + dz, BRASS_SLAB + "[type=bottom,waterlogged=false]" if dz and x % 2 == 0
                   else ("air" if dz else "air"))
        if x % 4 == 0:
            for dz in (-1, 1):
                bp.set(x, CRANE_Y + 1, POOL_Z + dz, stair(IRON_STAIRS, "north" if dz > 0 else "south", "top"))
    for dx in (-15, 15):
        for dz in (-2, 2):
            bp.set(dx, CRANE_Y + 2, POOL_Z + dz, IRON)
    # trolley cabin
    tx = -2
    for x in range(tx - 2, tx + 3):
        for dz in range(-2, 3):
            for y in (CRANE_Y - 1, CRANE_Y, CRANE_Y + 1):
                edge = abs(x - tx) == 2 or abs(dz) == 2
                if y == CRANE_Y - 1:
                    bp.set(x, y, POOL_Z + dz, IRON)
                elif edge:
                    bp.set(x, y, POOL_Z + dz, GEAR if (y == CRANE_Y and dz == 0) else COPPER)
    bp.set(tx, CRANE_Y, POOL_Z, GAUGE)
    # the ladle: an iron crucible brimming with lava, hung on four chains
    lx, ly = tx, 11
    for y in range(ly, ly + 7):
        for x in range(lx - 3, lx + 4):
            for z in range(POOL_Z - 3, POOL_Z + 4):
                d = math.hypot(x - lx, z - POOL_Z)
                rr = 3 if y > ly + 1 else 2
                if d <= rr + 0.35:
                    if y == ly or d > rr - 0.75:
                        bp.set(x, y, z, BRASS if y in (ly + 4, ly + 6) else IRON)
                    elif y == ly + 5:
                        bp.set(x, y, z, "lava[level=0]")
                    else:
                        bp.set(x, y, z, "magma_block")
    for x in (lx - 2, lx + 2):
        for z in (POOL_Z - 2, POOL_Z + 2):
            chain(bp, x, ly + 7, z, CRANE_Y - 2)
    bp.set(lx, ly - 1, POOL_Z, "magma_block")
    # a spare hook hanging from the bridge
    chain(bp, 8, 14, POOL_Z, CRANE_Y + 1)
    bp.set(8, 13, POOL_Z, IRON)
    bp.set(8, 12, POOL_Z, W + "copper_pipe[axis=y]")
    # walkway between the legs and the bridge: platforms on top of each leg
    for (x, z) in legs:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if bp.get(x + dx, CRANE_Y, z + dz) in (None, "minecraft:air"):
                    bp.set(x + dx, CRANE_Y, z + dz, TREAD)
        bp.set(x + (2 if x < 0 else -2), CRANE_Y + 1, z, "air")
        bp.set(x, CRANE_Y + 1, z + (2 if z > POOL_Z else -2), EDISON)
        # the leg's ladder climbs on through the runway girder
        s = -1 if x < 0 else 1
        for y in (CRANE_Y, CRANE_Y + 1):
            bp.set(x + 2 * s, y, z, IRON)
            bp.set(x + s, y, z, "ladder[facing=%s,waterlogged=false]" % ("east" if s < 0 else "west"))


def catwalks(bp):
    """The high walk across the caldera from hall to hall, propped on iron trestles."""
    catwalk(bp, -HX0, HX0, POOL_Z, CAT_Y, axis="x", half=1)
    for x in (-POOL_R - 2, POOL_R + 2):
        for dz in (-1, 1):
            for y in range(1, CAT_Y):
                bp.set(x, y, POOL_Z + dz, IRON_WALL if y % 3 else IRON)
    for x in (-5, 5):
        bp.set(x, CAT_Y + 1, POOL_Z - 1, "air")
    # a viewing platform at the middle, under the ladle
    for x in range(-3, 4):
        for dz in (-2, 2):
            bp.set(x, CAT_Y, POOL_Z + dz, IRON)
            railing(bp, x, CAT_Y + 1, POOL_Z + dz, "north" if dz < 0 else "south")
    for dz in (-1, 1):
        for x in (-3, 3):
            pass


# ------------------------------------------------------------------ casting halls
def hall(bp, s):
    """Casting hall on side s (+1 east, -1 west): a long brick mill with a sawtooth roof."""
    X = lambda u: s * u  # noqa: E731  (u: distance from the centre line)
    lo, hi = HX0, HX1
    for u in range(lo, hi + 1):
        for z in range(HZ0, HZ1 + 1):
            x = X(u)
            ew, ns = u in (lo, hi), z in (HZ0, HZ1)
            bp.set(x, 0, z, PB if ew or ns else (TREAD if (z % 6 == 0 or u == (lo + hi) // 2) else "polished_blackstone"))
            for y in range(1, HWALL + 1):
                if ew or ns:
                    pil = (z - HZ0) % 5 == 0 if ew else (u - lo) % 6 == 0
                    corner = ew and ns
                    if corner or pil:
                        spec = IRON if y < HWALL else BRASS
                    elif y in (1,):
                        spec = PB
                    elif 3 <= y <= 9 and (((z - HZ0) % 5 in (2, 3)) if ew else ((u - lo) % 6 in (2, 3, 4))):
                        spec = "glass_pane" if y < 9 else stair(SMOKE_STAIRS, "north", "top")
                    elif y == 7:
                        spec = BRASS
                    else:
                        spec = SMOKE
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, "air")
    # window heads: arched with upside-down stairs, proper orientation per wall
    for z in range(HZ0, HZ1 + 1):
        if (z - HZ0) % 5 in (2, 3):
            for u in (lo, hi):
                f = "north" if (z - HZ0) % 5 == 2 else "south"
                bp.set(X(u), 9, z, stair(SMOKE_STAIRS, OPPOSITE_OF[f], "top"))
    for u in range(lo, hi + 1):
        if (u - lo) % 6 in (2, 3, 4):
            for z in (HZ0, HZ1):
                bp.set(X(u), 9, z, SMOKE if (u - lo) % 6 == 3 else stair(SMOKE_STAIRS, "east" if X(u) < X(u + 1) and (u - lo) % 6 == 2 else "west", "top"))
    # pilasters stand proud of the wall with a plinth and a brass cap
    for z in range(HZ0, HZ1 + 1, 5):
        for u, out in ((lo, -1), (hi, 1)):
            x = X(u + out)
            for y in range(0, HWALL + 1):
                bp.set(x, y, z, IRON if y < HWALL else BRASS)
            bp.set(x, 1, z, PB)
    # cornice
    for z in range(HZ0 - 1, HZ1 + 2):
        for u, f in ((lo - 1, "east" if s > 0 else "west"), (hi + 1, "west" if s > 0 else "east")):
            bp.set(X(u), HWALL, z, stair(BRASS_STAIRS, f, "top"))
    for u in range(lo - 1, hi + 2):
        bp.set(X(u), HWALL, HZ0 - 1, stair(BRASS_STAIRS, "south", "top"))
        bp.set(X(u), HWALL, HZ1 + 1, stair(BRASS_STAIRS, "north", "top"))
    sawtooth(bp, s)
    hall_inside(bp, s)
    hall_gable(bp, s)
    # doors: a great arched opening on the yard side, a cart door at the south end
    for z in range(POOL_Z - 2, POOL_Z + 3):
        for y in range(1, 7):
            bp.set(X(lo), y, z, "air")
        bp.set(X(lo), 7, z, BRASS)
    for z in (POOL_Z - 3, POOL_Z + 3):
        for y in range(1, 8):
            bp.set(X(lo), y, z, IRON)
            bp.set(X(lo - 1), y, z, IRON if y < 7 else BRASS)
    bp.set(X(lo - 1), 8, POOL_Z, GEAR)
    mid = (lo + hi) // 2
    for u in range(mid - 2, mid + 3):
        for y in range(1, 6):
            bp.set(X(u), y, HZ1, "air")
        bp.set(X(u), 6, HZ1, BRASS)
    for u in range(mid - 1, mid + 2):
        for y in range(1, 4):
            bp.set(X(u), y, HZ0, "air")
    # catwalk door on the mezzanine
    for z in range(POOL_Z - 1, POOL_Z + 2):
        for y in range(CAT_Y + 1, CAT_Y + 4):
            bp.set(X(lo), y, z, "air")
        bp.set(X(lo), CAT_Y, z, TREAD)


OPPOSITE_OF = {"north": "south", "south": "north", "east": "west", "west": "east"}


def hall_gable(bp, s):
    """Stepped brick parapet on the south end with a great cog window and the lamps of the loading dock."""
    lo, hi = HX0, HX1
    mid = (lo + hi) // 2
    z = HZ1
    for u in range(lo, hi + 1):
        d = abs(u - mid)
        top = HWALL + 8 - (d // 2)
        for y in range(HWALL + 1, top + 1):
            bp.set(s * u, y, z, SMOKE if d % 3 else IRON)
        bp.set(s * u, top + 1, z, BRASS_SLAB + "[type=bottom,waterlogged=false]" if d % 2 else BRASS)
        bp.set(s * u, HWALL, z + 1, stair(BRASS_STAIRS, "north", "top"))
    # the cog window
    cy = HWALL + 3
    for u in range(mid - 4, mid + 5):
        for y in range(cy - 4, cy + 5):
            d = math.hypot(u - mid, y - cy)
            if d <= 3.4:
                spoke = u == mid or y == cy
                bp.set(s * u, y, z, GEAR if d < 1 else (IRON if spoke else "orange_stained_glass_pane"))
            elif d <= 4.4:
                bp.set(s * u, y, z, BRASS)
                if round(math.degrees(math.atan2(y - cy, u - mid)) / 30) % 2 == 0:
                    bp.set(s * u, y, z + 1, BRASS)
    # lamps on the pilaster tops
    for zz in range(HZ0, HZ1 + 1, 10):
        for u in (lo - 1, hi + 1):
            bp.set(s * u, HWALL + 1, zz, EDISON)
    # awning over the yard door
    for zz in range(POOL_Z - 4, POOL_Z + 5):
        for k in (1, 2, 3):
            bp.set(s * (lo - k), 8 - (k > 2), zz, IRON_SLAB + "[type=top,waterlogged=false]" if k < 3 else
                   IRON_SLAB + "[type=bottom,waterlogged=false]")
        if zz in (POOL_Z - 4, POOL_Z + 4):
            bp.set(s * (lo - 1), 7, zz, stair(IRON_STAIRS, "east" if s > 0 else "west", "top"))
    for zz in (POOL_Z - 3, POOL_Z + 3):
        hang_lamp(bp, s * (lo - 2), 6, zz, length=1)


def locomotive(bp, x0, z):
    """A little steam engine and its coal tender standing on the yard line."""
    for x in range(x0, x0 + 16):
        if x == x0 + 10:
            continue
        bp.set(x, 2, z, IRON)
    for x in range(x0 + 1, x0 + 7):
        for dy in (3, 4, 5):
            for dz in (-1, 0, 1):
                if abs(dz) == 1 and dy in (3, 5):
                    if dy == 3:
                        bp.set(x, dy, z + dz, stair(IRON_STAIRS, "south" if dz < 0 else "north", "top"))
                    else:
                        bp.set(x, dy, z + dz, stair(IRON_STAIRS, "south" if dz < 0 else "north"))
                else:
                    bp.set(x, dy, z + dz, BRASS if x % 2 == 0 else IRON)
    for x in range(x0 + 1, x0 + 10, 2):
        for dz in (-1, 1):
            bp.set(x, 2, z + dz * 2, W + "wall_cog[facing=%s]" % ("north" if dz < 0 else "south"))
            bp.set(x, 2, z + dz, IRON)
    bp.set(x0, 3, z, GAUGE)
    bp.set(x0, 4, z, EDISON)
    bp.set(x0 - 1, 2, z, stair(IRON_STAIRS, "east"))
    for y in (6, 7, 8):
        bp.set(x0 + 2, y, z, SMOKE if y < 8 else IRON)
    bp.set(x0 + 2, 9, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.set(x0 + 4, 6, z, BRASS)
    bp.set(x0 + 5, 6, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for x in range(x0 + 7, x0 + 10):
        for dz in (-1, 0, 1):
            for y in range(3, 7):
                edge = x == x0 + 9 or abs(dz) == 1
                if y == 3:
                    bp.set(x, y, z + dz, IRON)
                elif edge:
                    bp.set(x, y, z + dz, "glass_pane" if y == 5 and dz != 0 else COPPER)
                else:
                    bp.set(x, y, z + dz, "air")
            bp.set(x, 7, z + dz, IRON_SLAB + "[type=bottom,waterlogged=false]")
    bp.set(x0 + 7, 4, z, W + "valve_wheel[facing=east]")
    bp.set(x0 + 7, 5, z, GAUGE)
    for x in range(x0 + 11, x0 + 16):
        for dz in (-1, 0, 1):
            edge = x in (x0 + 11, x0 + 15) or abs(dz) == 1
            bp.set(x, 3, z + dz, IRON if edge else "coal_block")
            bp.set(x, 4, z + dz, (BRASS if edge else "coal_block") if (edge or (x + dz) % 2) else "air")


def sawtooth(bp, s):
    """North-light roof: teeth along z, each a glazed vertical face to the north and a slope down to the south."""
    lo, hi = HX0, HX1
    tooth = 6
    for z0 in range(HZ0, HZ1, tooth):
        for k in range(tooth):
            z = z0 + k
            if z > HZ1:
                break
            y = HWALL + 1 + (tooth - 1 - k)
            for u in range(lo, hi + 1):
                x = s * u
                if k == 0:
                    for yy in range(HWALL + 1, HWALL + tooth + 1):
                        frame = u in (lo, hi) or (u - lo) % 6 == 0 or yy in (HWALL + 1, HWALL + tooth)
                        bp.set(x, yy, z, IRON if frame else "glass_pane")
                    bp.set(x, HWALL + tooth + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
                else:
                    bp.set(x, y, z, stair(IRON_STAIRS, "north"))
                    if u in (lo, hi):
                        for yy in range(HWALL + 1, y):
                            bp.set(x, yy, z, SMOKE)
            # beam under each glazed face
        for u in range(lo + 1, hi):
            bp.set(s * u, HWALL, z0, IRON)
    # roof-top smoke stacks
    for z in (HZ0 + 8, HZ0 + 26):
        x = s * (HX1 - 4)
        for y in range(HWALL + 1, HWALL + 12):
            bp.set(x, y, z, SMOKE if y % 5 else BRASS)
        smoke(bp, x, HWALL + 12, z, signal=False)


def hall_inside(bp, s):
    lo, hi = HX0, HX1
    X = lambda u: s * u  # noqa: E731
    f_in = "west" if s > 0 else "east"   # facing from the outer wall towards the yard
    f_out = OPPOSITE_OF[f_in]
    # mezzanine along the outer wall (3 deep) and along the yard wall (2 deep) at y 7
    for z in range(HZ0 + 1, HZ1):
        for u in range(hi - 3, hi):
            bp.set(X(u), CAT_Y, z, TREAD)
        railing(bp, X(hi - 4), CAT_Y + 1, z, f_in)
        for u in (lo + 1, lo + 2):
            bp.set(X(u), CAT_Y, z, TREAD)
        railing(bp, X(lo + 3), CAT_Y + 1, z, f_out)
        if (z - HZ0) % 5 == 0:
            bp.set(X(hi - 4), CAT_Y, z, IRON)
            bp.set(X(lo + 3), CAT_Y, z, IRON)
            for y in range(1, CAT_Y):
                bp.set(X(hi - 4), y, z, IRON_WALL if y % 3 else IRON)
                bp.set(X(lo + 3), y, z, IRON_WALL if y % 3 else IRON)
            bp.set(X(hi - 4), CAT_Y - 1, z, IRON)
            bp.set(X(lo + 3), CAT_Y - 1, z, IRON)
    for z in (HZ0 + 1, HZ1 - 1):
        for u in range(lo + 1, hi):
            bp.set(X(u), CAT_Y, z, TREAD)
    for u in range(lo + 3, hi - 3):
        railing(bp, X(u), CAT_Y + 1, HZ0 + 2, "south")
        railing(bp, X(u), CAT_Y + 1, HZ1 - 2, "north")
    # stairs up to the mezzanine at the north end
    for i in range(CAT_Y):
        z = HZ0 + 3 + i
        for u in (hi - 3, hi - 2):
            bp.set(X(u), i + 1, z, stair(TREAD_STAIRS_N, "north"))
            for y in range(i + 2, i + 5):
                if y < CAT_Y or z > HZ0 + 2 + CAT_Y:
                    bp.set(X(u), y, z, "air")
        bp.set(X(hi - 3), CAT_Y, z, "air") if i < CAT_Y - 1 else None
        bp.set(X(hi - 2), CAT_Y, z, "air") if i < CAT_Y - 1 else None
    # furnace bank under the outer mezzanine: blast furnaces, smokers, lava cauldrons as moulds
    for z in range(HZ0 + 11, HZ1 - 1):
        u = hi - 1
        k = (z - HZ0) % 5
        if k == 0:
            continue
        bp.set(X(u), 1, z, "blast_furnace[facing=%s,lit=true]" % f_in if k in (1, 3) else "furnace[facing=%s,lit=true]" % f_in)
        bp.set(X(u), 2, z, "blast_furnace[facing=%s,lit=%s]" % (f_in, "true" if k == 2 else "false") if k != 4 else GAUGE)
        bp.set(X(u), 3, z, SMOKE)
        bp.set(X(u - 1), 4, z, stair(SMOKE_STAIRS, f_in, "top"))
        bp.set(X(u - 2), 1, z, "lava_cauldron" if k in (2, 3) else "cauldron")
    # casting line down the middle: rails on tread plate, with moulds and ingot stacks
    mid = (lo + hi) // 2
    for z in range(HZ0 + 1, HZ1):
        bp.set(X(mid), 0, z, TREAD)
        bp.set(X(mid), 1, z, "rail[shape=north_south,waterlogged=false]")
    for z in range(HZ0 + 6, HZ1 - 4, 7):
        for du in (-2, 2):
            bp.set(X(mid + du), 1, z, "iron_block" if du < 0 else "lava_cauldron")
            bp.set(X(mid + du), 1, z + 1, W + "compacting_crate[facing=north]" if du < 0 else "cauldron")
        bp.set(X(mid - 2), 2, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    # overhead crane: runway beams on the pilasters and a bridge with a hook
    for z in range(HZ0 + 1, HZ1):
        for u in (lo + 1, hi - 1):
            bp.set(X(u), HWALL - 1, z, IRON)
    cz = HZ0 + 20
    for u in range(lo + 1, hi):
        bp.set(X(u), HWALL - 1, cz, BRASS if u in (lo + 1, hi - 1) else IRON)
        bp.set(X(u), HWALL - 1, cz + 1, IRON)
    chain(bp, X(mid), 6, cz, HWALL - 2)
    bp.set(X(mid), 5, cz, IRON)
    bp.set(X(mid), 4, cz, "iron_block")
    # lamps along the roof beams
    for z0 in range(HZ0, HZ1, 6):
        for u in (lo + 5, hi - 6):
            hang_lamp(bp, X(u), HWALL - 2, z0, length=1)
    # machines and chests on the mezzanine, an office with the clerk's desk
    machines = [W + "block_breaker", W + "block_placer", W + "auto_harvester", W + "vacuum_hopper", W + "redstone_timer"]
    for i, z in enumerate(range(HZ0 + 12, HZ1 - 2, 5)):
        m = machines[i % len(machines)]
        bp.set(X(hi - 1), CAT_Y + 1, z, m + "[facing=%s,powered=false]" % f_in if "timer" not in m and "hopper" not in m
               else m + "[facing=%s,powered=false]" % f_in)
        bp.set(X(hi - 1), CAT_Y + 1, z + 1, TABLE)
    bp.chest(X(hi - 1), CAT_Y + 1, HZ1 - 2, f_in, loot=LOOT + "foundry_forge")
    bp.chest(X(lo + 1), 1, HZ1 - 2, f_out, loot=LOOT + "foundry_forge")
    bp.barrel(X(lo + 1), 1, HZ1 - 3, "up", loot=LOOT + "foundry_forge")
    # clerk's office: mahogany desk at the south end of the yard mezzanine
    bp.set(X(lo + 1), CAT_Y + 1, HZ1 - 4, TABLE)
    bp.set(X(lo + 2), CAT_Y + 1, HZ1 - 4, W + "mahogany_chair[facing=%s]" % f_out)
    bp.set(X(lo + 1), CAT_Y + 1, HZ1 - 5, "lectern[facing=%s,has_book=false,powered=false]" % f_in)


TREAD_STAIRS_N = W + "diamond_plate_stairs"


# ------------------------------------------------------------------ pipes, chimneys, rail yard
def geothermal_pipes(bp):
    """Two great insulated pipes from the volcano flank to the hall roofs, on lattice trestles."""
    for s in (-1, 1):
        y = 19
        PX = 19
        pts = [(s * PX, z) for z in range(-30, -11)] + [(s * x, -11) for x in range(PX, 32)]
        for i, (x, z) in enumerate(pts):
            for dy in (-1, 0, 1):
                for dd in (-1, 0, 1):
                    px, pz = (x + dd, z) if abs(x) == PX and z < -11 else (x, z + dd)
                    ring = i % 5 == 0
                    edge = abs(dy) == 1 or abs(dd) == 1
                    if edge:
                        bp.set(px, y + dy, pz, BRASS if ring else COPPER)
                    else:
                        bp.set(px, y + dy, pz, PIPES)
        # elbow joint and the drop into the hall roof
        for yy in range(HWALL + 2, y + 2):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    edge = abs(dx) == 1 or abs(dz) == 1
                    bp.set(s * 32 + dx, yy, -11 + dz, (BRASS if yy % 4 == 0 else COPPER) if edge else PIPES)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(s * 32 + dx, y + 2, -11 + dz, BRASS)
        bp.set(s * 32, y + 3, -11, GAUGE)
        # trestles
        for x in (s * 16, s * 24):
            for y2 in range(1, y - 1):
                for dz in (-1, 1):
                    bp.set(x, y2, -11 + dz * 2, IRON if y2 % 6 == 0 else IRON_WALL)
                bp.set(x, y2, -11, BARS if y2 % 6 == 3 else "air") if y2 < y - 2 else None
            for dz in (-2, -1, 0, 1, 2):
                bp.set(x, y - 2, -11 + dz, IRON)
        # where the pipe leaves the volcano: a brass collar
        zc = next(z for z in range(-30, -11) if (cone_h(s * PX, z) or 0) < y + 2)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if max(abs(dx), abs(dy)) == 2:
                    bp.set(s * PX + dx, y + dy, zc, BRASS)


def ore_yard(bp):
    """Rail yard from the gate to both halls, with ore piles and coal heaps between the tracks."""
    zr = 40
    for x in range(-31, 32):
        bp.set(x, 0, zr, TREAD)
        shape = "east_west"
        if x == 31:
            shape = "north_west"
        elif x == -31:
            shape = "north_east"
        bp.set(x, 1, zr, f"rail[shape={shape},waterlogged=false]")
    for s in (-1, 1):
        for z in range(HZ1 + 1, zr):
            bp.set(s * 31, 0, z, TREAD)
            bp.set(s * 31, 1, z, "rail[shape=north_south,waterlogged=false]")
    for z in range(zr + 1, 50):
        bp.set(0, 0, z, TREAD)
        bp.set(0, 1, z, "rail[shape=north_south,waterlogged=false]")
    # piles
    piles = [(-14, 33, ("coal_block", "blackstone", "coal_ore")), (14, 33, ("raw_iron_block", "iron_ore", "raw_iron_block")),
             (-20, 45, ("raw_copper_block", "copper_ore", "raw_copper_block")),
             (20, 45, (W + "raw_zinc_block", W + "zinc_ore", W + "raw_zinc_block")),
             (-40, 24, ("coal_block", "coal_ore", "blackstone")), (40, 40, ("raw_gold_block", "gold_ore", "raw_iron_block"))]
    for (px, pz, mats) in piles:
        for x in range(px - 4, px + 5):
            for z in range(pz - 4, pz + 5):
                d = math.hypot(x - px, z - pz)
                h = int(3.6 - d + vnoise(x, z, 2.0, px) * 1.2)
                for y in range(1, h + 1):
                    if is_air(bp, x, y, z):
                        bp.set(x, y, z, mats[int(hash3(x, y, z, 3) * 3)])
    locomotive(bp, -24, zr)
    # ingot stacks and crates by the halls' cart doors
    for s in (-1, 1):
        for k, (dx, dz) in enumerate(((5, 39), (6, 39), (5, 41), (7, 41), (6, 41))):
            x = s * (31 + dx)
            bp.set(x, 1, dz, "iron_block" if k % 2 else W + "brass_block")
            if k < 2:
                bp.set(x, 2, dz, "gold_block" if k == 0 and s > 0 else "iron_block")
        for dz in (37, 38):
            bp.set(s * 25, 1, dz, W + "compacting_crate[facing=south]")
            bp.barrel(s * 26, 1, dz, "up")


def gate(bp):
    """The yard gate on the south road: two brick pylons and an iron lintel with the foundry's gear."""
    zg = 48
    for s in (-1, 1):
        cx = s * 5
        for x in range(cx - 1, cx + 2):
            for z in range(zg - 1, zg + 2):
                for y in range(0, 13):
                    bp.set(x, y, z, BRASS if y in (0, 6, 12) else (IRON if (x - cx) and (z - zg) else SMOKE))
        bp.set(cx, 13, zg, IRON)
        bp.set(cx, 14, zg, EDISON)
        for y in (3, 9):
            bp.set(cx, y, zg + 2, W + "wall_cog[facing=south]")
    for x in range(-4, 5):
        bp.set(x, 10, zg, IRON)
        bp.set(x, 11, zg, BRASS if x % 2 else IRON)
        bp.set(x, 9, zg, stair(IRON_STAIRS, "east" if x < 0 else "west", "top") if abs(x) >= 3 else "air")
    for x in (-2, 2):
        hang_lamp(bp, x, 8, zg, length=1)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                bp.set(dx, 13 + dy, zg, GEAR if abs(dx) + abs(dy) == 1 else BRASS)
    bp.set(0, 13, zg, AETHER)
    for x in range(-1, 2):
        bp.set(x, 11, zg, BRASS)


def lights(bp):
    for (x, z) in ((-18, 0), (18, 0), (-18, 30), (18, 30), (-6, 30), (6, 30), (-34, 44), (34, 44)):
        if is_air(bp, x, 1, z):
            lantern_post(bp, x, 0, z, h=4)


def foundry(bp):
    ground(bp)
    volcano(bp)
    nave(bp)
    yard(bp)
    for s in (-1, 1):
        hall(bp, s)
    crane(bp)
    catwalks(bp)
    geothermal_pipes(bp)
    for (x, z, h) in ((-46, 2, 52), (46, 2, 52), (-46, 26, 46), (46, 26, 46)):
        chimney(bp, x, z, 0, h, r=3, bands=(12,))
        for y in range(2, 4):
            for k in range(1, 3):
                bp.set(x + (k + 3) * (1 if x < 0 else -1), y, z, W + "copper_pipe[axis=x]")
    ore_yard(bp)
    gate(bp)
    lights(bp)
    # the foundry crew: smiths in both casting halls, a mason at the ore yard
    for s in (-1, 1):
        xa, xb = sorted((s * HX0, s * HX1))
        hall_r = ((xa, 1, HZ0), (xb, HWALL, HZ1))
        INT.populate(bp, [("armorer", "toolsmith")[s > 0], ("weaponsmith", "mason")[s > 0]], region=hall_r,
                     vtype="savanna", seed=s + 2)
        INT.decorate(bp, dict(INT.THEMES["forge"], ceiling="edison"), seed=s + 2, region=hall_r)
    INT.decorate(bp, "steampunk", seed=5, density=0.3)


register(StructureDef(
    "geothermal_foundry", "overworld",
    ["#minecraft:is_badlands", "windswept_savanna", "savanna_plateau"],
    [Piece("foundry", foundry)],
    spacing=72, separation=28, adaptation="beard_thin", processors="none", max_distance=116,
    exclusion=("wayfarers:clockwork_citadel", 8),
    peaceful=True,
    title_fr="Fonderie géothermique", title_en="Geothermal Foundry"))
