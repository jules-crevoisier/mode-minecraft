"""Sylvan Palace (Palais sylvain): an elven palace grown into and around a colossal silver tree (mega-structure).

Ground y = 0, the great tree at (0, 0):
  * an 11-block silver trunk (pale oak and birch bark) rising 70 blocks on eight arching buttress roots,
    crowned by a 46-block canopy of azalea, birch and oak leaves studded with shroomlight "fruits",
  * a spiral stair winding once around the trunk from the root gate to the third terrace,
  * three white-rimmed terraces carried by branch brackets (y 14, 30, 46), with leaf-domed pavilions:
    the guest pavilions, the music and banquet halls, the queen's chamber and the library in the leaves,
  * rooms inside the trunk at every terrace: the Heart spring, the throne hall, the royal treasury, and a
    ladder up through the heartwood to the Moon Lantern, a glass observatory above the crown,
  * three smaller tree houses on their own trees, joined to the first terrace by rope bridges,
  * the Moon Pool at the foot of the tree: a round white basin with a crescent sculpture, lilies and
    a garden of white flowers, azalea bushes and lantern posts.
"""
import math

from .. import interior as INT
from ..arch import Palette, stair, slab
from ..defs import Piece, StructureDef, register
from ..parts import LOOT

def LV(name):
    return f"{name}[distance=1,persistent=true,waterlogged=false]"


BARK = Palette({"birch_wood[axis=y]": 6, "stripped_pale_oak_wood[axis=y]": 2, "stripped_birch_wood[axis=y]": 1},
               seed=2, scale=3.0)
LEAF = Palette({LV("azalea_leaves"): 3, LV("oak_leaves"): 2, LV("flowering_azalea_leaves"): 2, LV("birch_leaves"): 2},
               seed=4, scale=2.5)
WHITE = Palette({"calcite": 3, "smooth_quartz": 2, "quartz_bricks": 2}, seed=6, scale=2.0)
GOLD = "gold_block"
PLANK, PLANK_SLAB, FENCE = "birch_planks", "birch_slab", "birch_fence"
PILLAR = "quartz_pillar[axis=y]"
TRUNK_TOP = 75
LEVELS = (14, 30, 46)   # terrace decks
STAIR_R = (6, 7)
SATELLITES = ((34, 10, 22, 160), (-12, 33, 22, 250), (-26, -24, 22, 10))   # x, z, deck y, bridge angle seed


def trunk_r(y):
    return 5.5 if y < 44 else max(2.6, 5.5 - (y - 44) * 0.11)


def _dir(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _hash(x, y, z, s=0):
    n = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (s * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


# ------------------------------------------------------------------ the great tree
def trunk(bp):
    for y in range(-2, TRUNK_TOP + 1):
        r = trunk_r(y)
        ri = int(r) + 2
        for x in range(-ri, ri + 1):
            for z in range(-ri, ri + 1):
                d = math.hypot(x, z)
                if d <= r:
                    # vertical bark ridges: every few degrees the bark stands out in darker wood
                    a = math.degrees(math.atan2(z, x)) % 360
                    ridge = d > r - 1 and int(a / 22.5) % 2 == 0 and _hash(x, y // 4, z, 5) < 0.35
                    bp.set(x, y, z, "pale_oak_wood[axis=y]" if ridge else BARK.pick(x, y, z))


def roots(bp):
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        reach = 15 + (k % 3) * 2
        for i in range(0, 61):
            t = i / 60
            rad = 4.5 + (reach - 4.5) * t
            y = 9 * (1 - t) ** 1.6 - 0.5
            th = 2.4 * (1 - t) + 0.9
            cx, cz = math.cos(a) * rad, math.sin(a) * rad
            for x in range(int(cx - th) - 1, int(cx + th) + 2):
                for z in range(int(cz - th) - 1, int(cz + th) + 2):
                    for yy in range(int(y - th) - 1, int(y + th) + 2):
                        if (x - cx) ** 2 + (z - cz) ** 2 + ((yy - y) * 1.3) ** 2 <= th * th and yy >= -2:
                            bp.set(x, yy, z, BARK.pick(x, yy, z))
        # moss and ferns where the root meets the ground
        ex, ez = round(math.cos(a) * reach), round(math.sin(a) * reach)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if bp.get(ex + dx, 0, ez + dz) is None and abs(dx) + abs(dz) <= 3:
                    bp.set(ex + dx, 0, ez + dz, "moss_block")
                    if _hash(ex + dx, 1, ez + dz) < 0.4:
                        bp.set(ex + dx, 1, ez + dz, "fern" if _hash(dx, 2, dz) < 0.5 else "moss_carpet")


def canopy(bp):
    """A crown of four stacked leaf tiers (like a mallorn), lumpy and drooping at the edges."""
    tiers = ((56, 22, 3.5), (64, 16, 3.5), (71, 10, 3.0))
    for ti, (base, R, th) in enumerate(tiers):
        for x in range(-R - 3, R + 4):
            for z in range(-R - 3, R + 4):
                d = math.hypot(x, z)
                a = math.atan2(z, x)
                rr = R * (0.86 + 0.14 * math.sin(a * 5 + ti * 1.7) + (_hash(x, ti, z, 4) - 0.5) * 0.12)
                if d > rr:
                    continue
                k = 1 - (d / rr) ** 2
                top = base + th * math.sqrt(k) + (_hash(x, 1, z, ti) - 0.5) * 1.2
                bot = base - 1.5 * math.sqrt(k)
                for y in range(int(bot), int(top) + 1):
                    if bp.get(x, y, z) is None:
                        h = _hash(x, y, z, 8)
                        bp.set(x, y, z, "shroomlight" if h < 0.01 else LEAF.pick(x, y, z))
                # drooping fringe
                if d > rr - 1.5 and _hash(x, 2, z, ti) < 0.45:
                    for i in range(1, 2 + int(_hash(x, 3, z, ti) * 3)):
                        y = int(bot) - i
                        if bp.get(x, y, z) is None:
                            bp.set(x, y, z, LEAF.pick(x, y, z))
    # branches spreading under the tiers
    for k in range(12):
        a = math.radians(k * 30 + 5)
        y0 = 51 + (k % 3) * 2
        rr = 11 + (k % 2) * 5
        n = rr * 2
        for i in range(n + 1):
            t = i / n
            x = round(math.cos(a) * (3 + (rr - 3) * t))
            z = round(math.sin(a) * (3 + (rr - 3) * t))
            y = round(y0 + 5 * math.sin(t * math.pi / 2))
            axis = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            hidden = all((bp.get(x + dx, y + dy, z + dz) or "").endswith(("leaves", "_log", "_wood"))
                         for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1)))
            if t < 0.35 or hidden:
                bp.set(x, y, z, f"birch_log[axis={axis}]")
    # glow berries hanging under the lowest tier
    for k in range(18):
        a = math.radians(k * 20 + 7)
        rr = 10 + (k % 5) * 2.5
        x, z = round(math.cos(a) * rr), round(math.sin(a) * rr)
        top = None
        for y in range(49, 63):
            b = bp.get(x, y, z)
            if b and "leaves" in b:
                top = y
                break
        if top is not None and bp.get(x, top - 1, z) is None:
            n = 2 + k % 4
            for i in range(1, n + 1):
                bp.set(x, top - i, z, "cave_vines_plant[berries=true]" if i < n else "cave_vines[age=25,berries=true]")


TERRACES = {
    # deck y: (core radius, [(angle, distance, lobe radius)])
    14: (9, [(16, 10, 5), (110, 10, 5), (223, 10, 5), (330, 10, 6), (60, 8, 4)]),
    30: (10, [(200, 11, 6), (330, 11, 6), (90, 12, 5)]),
    46: (8, [(140, 9, 5), (250, 9, 5), (20, 9, 4)]),
}


def _lobe_xy(a, dist):
    return round(math.cos(math.radians(a)) * dist), round(math.sin(math.radians(a)) * dist)


def terrace(bp, L):
    core, lobes = TERRACES[L]
    centres = [(0, 0, core)] + [(*_lobe_xy(a, d), r) for (a, d, r) in lobes]

    def inside(x, z):
        return any(math.hypot(x - cx, z - cz) <= r + 0.4 for (cx, cz, r) in centres) and \
            math.hypot(x, z) > trunk_r(L) - 0.2

    cells = {(x, z) for x in range(-24, 25) for z in range(-24, 25) if inside(x, z)}
    rim = {(x, z) for (x, z) in cells if any((x + dx, z + dz) not in cells and math.hypot(x + dx, z + dz) > trunk_r(L)
                                             for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for (x, z) in cells:
        if (x, z) in rim:
            bp.set(x, L, z, WHITE.pick(x, L, z))
            out = [(dx, dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, z + dz) not in cells]
            dx, dz = out[0]
            bp.set(x + dx, L, z + dz, stair("quartz_stairs", _dir(-dx, -dz), "top"), keep=True)
        else:
            ring = int(min(math.hypot(x - cx, z - cz) for (cx, cz, r) in centres))
            bp.set(x, L, z, "stripped_birch_wood[axis=y]" if ring % 3 == 0 else PLANK)
    # railing with white posts and lanterns
    for (x, z) in sorted(rim):
        if bp.get(x, L + 1, z) is None:
            post = (x * 7 + z * 3) % 9 == 0
            bp.set(x, L + 1, z, PILLAR if post else FENCE)
            if post:
                bp.set(x, L + 2, z, "lantern[hanging=false,waterlogged=false]")
    # branch brackets from the trunk to every lobe, and lanterns hanging under the deck
    ring = [(round(math.cos(math.radians(a)) * core), round(math.sin(math.radians(a)) * core), 0)
            for a in range(45, 360, 90)]
    for (cx, cz, r) in centres[1:] + ring:
        a = math.atan2(cz, cx)
        dist = math.hypot(cx, cz) + r * 0.4
        r0 = trunk_r(L - 8) - 0.5
        n = 30
        for i in range(n + 1):
            t = i / n
            rad = r0 + (dist - r0) * t
            x, z = round(math.cos(a) * rad), round(math.sin(a) * rad)
            y = round(L - 8 + 7 * math.sqrt(t))
            for yy in (y, y - 1) if t < 0.4 else (y,):
                if bp.get(x, yy, z) is None:
                    bp.set(x, yy, z, BARK.pick(x, yy, z))
        if r:
            if bp.get(cx, L - 1, cz) is None:
                bp.chain(cx, L - 2, cz, L - 1)
                bp.lantern(cx, L - 3, cz, hanging=True)


def planter(bp, x, y, z):
    """A white planter with a flowering azalea and a lantern."""
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(x + dx, y + 1, z + dz, "quartz_bricks" if (dx or dz) else "moss_block")
    bp.set(x, y + 2, z, "flowering_azalea")
    for dx in (-1, 1):
        bp.set(x + dx, y + 2, z, "moss_carpet")
        bp.set(x, y + 2, z + dx, "moss_carpet")



def spiral_stair(bp):
    """One turn around the trunk from the root gate (south) up to the third terrace."""
    top = LEVELS[2]
    a0 = math.radians(90)
    path = []
    ang = a0
    y = 1
    while y <= top:
        rm = (STAIR_R[0] + STAIR_R[1]) / 2 + 0.5
        cells = []
        for rr in STAIR_R:
            x, z = round(math.cos(ang) * rr), round(math.sin(ang) * rr)
            cells.append((x, z))
        tx, tz = -math.sin(ang), math.cos(ang)          # tangent (counter-clockwise when seen from above)
        f = _dir(tx, tz)
        path.append((y, cells, f, ang))
        ang += 1.0 / rm
        y += 1
    for (y, cells, f, ang) in path:
        for (x, z) in cells:
            bp.set(x, y, z, stair("birch_stairs", f))
            if bp.get(x, y - 1, z) is None:
                bp.set(x, y - 1, z, PLANK)
            for yy in range(y + 1, y + 4):
                b = bp.get(x, yy, z)
                if b is None or "leaves" in b or "planks" in b or "stripped_birch" in b or "quartz" in b \
                        or "calcite" in b or "fence" in b or "lantern" in b:
                    bp.set(x, yy, z, "air")
        ox, oz = round(math.cos(ang) * (STAIR_R[1] + 1)), round(math.sin(ang) * (STAIR_R[1] + 1))
        if bp.get(ox, y + 1, oz) in (None, "minecraft:air"):
            bp.set(ox, y, oz, WHITE.pick(ox, y, oz))
            bp.set(ox, y + 1, oz, FENCE if y % 8 else PILLAR)
            if y % 8 == 0:
                bp.set(ox, y + 2, oz, "lantern[hanging=false,waterlogged=false]")
    # clear the railing where the stair arrives on each terrace
    for L in LEVELS:
        for (y, cells, f, ang) in path:
            if L - 1 <= y <= L + 1:
                for rr in range(STAIR_R[0], STAIR_R[1] + 3):
                    x, z = round(math.cos(ang) * rr), round(math.sin(ang) * rr)
                    for yy in (L + 1, L + 2):
                        if bp.get(x, yy, z) and ("fence" in bp.get(x, yy, z) or "lantern" in bp.get(x, yy, z)
                                                 or "pillar" in bp.get(x, yy, z)):
                            bp.set(x, yy, z, "air")
    # root gate at the foot of the stair
    gx = 0
    for x in range(-3, 4):
        for y in range(1, 8):
            edge = abs(x) == 3 or y == 7 or (abs(x) == 2 and y == 6)
            if edge:
                bp.set(gx + x, y, 9, PILLAR if abs(x) == 3 and y < 6 else WHITE.pick(x, y, 9))
    for x in range(-4, 5):
        bp.set(x, 8, 9, LEAF.pick(x, 8, 9))
        bp.set(x, 8, 10, LEAF.pick(x, 8, 10))
    bp.set(0, 8, 9, GOLD)
    bp.set(0, 9, 9, "end_rod[facing=up]")


# ------------------------------------------------------------------ pavilions
def pod(bp, cx, y, cz, r, door, kind, seed=0):
    """A round pavilion: white base ring, quartz columns and arched windows, a leaf dome with gold ribs."""
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = math.hypot(x - cx, z - cz)
            if d <= r + 0.4:
                bp.set(x, y, z, WHITE.pick(x, y, z) if d > r - 0.6 else ("stripped_birch_wood[axis=y]"
                                                                        if (x + z) % 2 else PLANK))
                for yy in range(y + 1, y + r + 6):
                    bp.set(x, yy, z, "air")
    h = 5
    for a in range(0, 360, 4):
        ar = math.radians(a)
        x, z = cx + round(math.cos(ar) * r), cz + round(math.sin(ar) * r)
        col = a % 45 == 0
        for yy in range(y + 1, y + h):
            if col:
                bp.set(x, yy, z, PILLAR)
            elif yy == y + 1:
                bp.set(x, yy, z, WHITE.pick(x, yy, z))
            else:
                bp.set(x, yy, z, "white_stained_glass_pane" if yy < y + h - 1 else "quartz_bricks")
        bp.set(x, y + h, z, "chiseled_quartz_block")
    # door gap facing `door` (an angle in degrees)
    da = math.radians(door)
    for k in (-1, 0, 1):
        x = cx + round(math.cos(da) * r - math.sin(da) * k * 0.9)
        z = cz + round(math.sin(da) * r + math.cos(da) * k * 0.9)
        for yy in range(y + 1, y + h - 1):
            bp.set(x, yy, z, "air")
    # leaf dome on a white cornice, eight gold ribs and a finial
    R = r + 1
    dy0 = y + h
    for a in range(0, 360, 3):
        ar = math.radians(a)
        x, z = cx + round(math.cos(ar) * (r + 1)), cz + round(math.sin(ar) * (r + 1))
        bp.set(x, dy0, z, stair("quartz_stairs", _dir(cx - x, cz - z), "top"))
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            for yy in range(dy0 + 1, dy0 + R + 2):
                d = math.sqrt((x - cx) ** 2 + ((yy - dy0) * 1.1) ** 2 + (z - cz) ** 2)
                if R - 0.8 < d <= R + 0.35:
                    bp.set(x, yy, z, LV("flowering_azalea_leaves") if (x + yy + z) % 3 == 0 else LV("azalea_leaves"))
                elif d <= R - 0.8:
                    bp.set(x, yy, z, "air")
    ytop = dy0 + 1 + round((R + 0.2) / 1.1)
    bp.set(cx, ytop, cz, GOLD)
    bp.set(cx, ytop + 1, cz, "end_rod[facing=up]")
    bp.chain(cx, ytop - 2, cz, ytop - 1)
    bp.lantern(cx, ytop - 3, cz, hanging=True)
    # furniture
    if kind == "guest":
        bp.bed(cx - 1, y + 1, cz - r + 1, "south", "white")
        bp.bed(cx + 1, y + 1, cz - r + 1, "south", "light_blue")
        bp.set(cx, y + 1, cz + r - 2, "potted_lily_of_the_valley")
        bp.chest(cx + r - 1, y + 1, cz, "west", loot=LOOT + "sylvan_palace")
    elif kind == "music":
        for (dx, dz) in ((-2, 0), (2, 0), (0, -2)):
            bp.set(cx + dx, y + 1, cz + dz, "note_block[instrument=harp,note=12,powered=false]")
        bp.set(cx, y + 1, cz, "jukebox[has_record=false]")
        bp.set(cx - 2, y + 1, cz + 2, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        bp.set(cx + 2, y + 1, cz + 2, "birch_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    elif kind == "banquet":
        for dx in range(-2, 3):
            bp.set(cx + dx, y + 1, cz, "birch_fence")
            bp.set(cx + dx, y + 2, cz, "white_carpet")
            bp.set(cx + dx, y + 1, cz - 1, stair("birch_stairs", "south"))
            bp.set(cx + dx, y + 1, cz + 1, stair("birch_stairs", "north"))
        bp.barrel(cx - r + 1, y + 1, cz, "up", loot=LOOT + "sylvan_palace")
    elif kind == "queen":
        bp.bed(cx, y + 1, cz - 1, "north", "white")
        bp.set(cx - 2, y + 1, cz - 2, "potted_white_tulip")
        bp.set(cx + 2, y + 1, cz - 2, "potted_azure_bluet")
        bp.set(cx + 2, y + 1, cz + 1, "lectern[facing=west,has_book=false,powered=false]")
        bp.chest(cx - 2, y + 1, cz + 1, "east", loot=LOOT + "sylvan_palace_royal")
    elif kind == "library":
        for a in range(0, 360, 8):
            ar = math.radians(a)
            x, z = cx + round(math.cos(ar) * (r - 1)), cz + round(math.sin(ar) * (r - 1))
            if abs(((a - door + 180) % 360) - 180) > 40:
                bp.set(x, y + 1, z, "bookshelf")
                bp.set(x, y + 2, z, "chiseled_bookshelf[facing=north]" if a % 3 else "bookshelf")
        bp.set(cx, y + 1, cz, "enchanting_table")
        bp.chest(cx + 1, y + 1, cz + 1, "north", loot=LOOT + "sylvan_palace")


def trunk_room(bp, L, door_deg, kind):
    """A round room hollowed in the heartwood at a terrace, its door looking out at `door_deg`."""
    r = 3.4
    for x in range(-4, 5):
        for z in range(-4, 5):
            d = math.hypot(x, z)
            if d <= r:
                bp.set(x, L, z, "stripped_pale_oak_wood[axis=y]" if (x + z) % 2 else "pale_oak_planks")
                for y in range(L + 1, L + 7):
                    bp.set(x, y, z, "air")
                bp.set(x, L + 7, z, "stripped_pale_oak_wood[axis=y]")
    da = math.radians(door_deg)
    for rad in range(3, 7):
        x, z = round(math.cos(da) * rad), round(math.sin(da) * rad)
        for y in (L + 1, L + 2, L + 3):
            bp.set(x, y, z, "air")
        bp.set(x, L, z, PLANK)
        bp.set(x, L + 4, z, GOLD if rad == 6 else "stripped_pale_oak_wood[axis=y]")
    bp.chain(0, L + 6, 0, L + 6)
    bp.lantern(0, L + 5, 0, hanging=True)
    if kind == "spring":
        for (x, z) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x, L, z, "water[level=0]")
            bp.set(x, L - 1, z, "sea_lantern")
        for (x, z) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
            bp.set(x, L + 1, z, "potted_flowering_azalea_bush")
    elif kind == "throne":
        bx, bz = -round(math.cos(da) * 2), -round(math.sin(da) * 2)
        f = _dir(math.cos(da), math.sin(da))
        bp.set(bx, L + 1, bz, stair("quartz_stairs", {"north": "south", "south": "north", "east": "west",
                                                      "west": "east"}[f]))
        bp.set(bx - round(math.cos(da)), L + 1, bz - round(math.sin(da)), GOLD)
        bp.set(bx - round(math.cos(da)), L + 2, bz - round(math.sin(da)), GOLD)
        bp.set(bx - round(math.cos(da)), L + 3, bz - round(math.sin(da)), "end_rod[facing=up]")
        for (x, z) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
            if bp.get(x, L + 1, z) == "minecraft:air":
                bp.set(x, L + 1, z, "potted_white_tulip")
    elif kind == "treasury":
        bp.chest(-2, L + 1, 0, "east", loot=LOOT + "sylvan_palace_royal")
        bp.chest(2, L + 1, 0, "west", loot=LOOT + "sylvan_palace_royal")
        bp.set(0, L + 1, -2, GOLD)
        bp.set(0, L + 2, -2, "amethyst_cluster[facing=up,waterlogged=false]")
        # the ladder through the heartwood to the Moon Lantern
        for y in range(L + 1, TRUNK_TOP + 1):
            bp.set(0, y, 2, "ladder[facing=north,waterlogged=false]")
            if y > L + 6:
                bp.set(0, y, 1, "air")
                bp.set(0, y, 3, "pale_oak_wood[axis=y]")
        bp.set(0, L + 7, 1, "air")


def moon_lantern(bp):
    """A glass observatory on the trunk top, above the crown."""
    y0 = TRUNK_TOP + 1
    for x in range(-6, 7):
        for z in range(-6, 7):
            d = math.hypot(x, z)
            if d <= 6.4:
                floor = "stripped_birch_wood[axis=y]" if (x + z) % 2 else PLANK
                bp.set(x, y0, z, WHITE.pick(x, y0, z) if d > 5.4 else floor)
                for y in range(y0 + 1, y0 + 9):
                    bp.set(x, y, z, "air")
    bp.set(0, y0, 2, "birch_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for a in range(0, 360, 4):
        x, z = round(math.cos(math.radians(a)) * 6), round(math.sin(math.radians(a)) * 6)
        bp.set(x, y0 + 1, z, PILLAR if a % 45 == 0 else FENCE)
    R = 4
    for x in range(-R - 1, R + 2):
        for z in range(-R - 1, R + 2):
            for y in range(y0 + 1, y0 + R + 4):
                d = math.sqrt(x * x + ((y - y0 - 1) * 0.9) ** 2 + z * z)
                if R - 0.6 < d <= R + 0.4:
                    rib = x == 0 or z == 0
                    bp.set(x, y, z, "smooth_quartz" if rib else "glass")
    for (x, z) in ((R, 0), (-R, 0), (0, R), (0, -R)):
        bp.set(x, y0 + 1, z, "air")
        bp.set(x, y0 + 2, z, "air")
    top = y0 + 1 + round((R + 0.4) / 0.9)
    bp.set(0, top, 0, GOLD)
    bp.set(0, top + 1, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(-1, y0 + 1, -1, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(1, y0 + 1, -1, "cartography_table")
    bp.chest(0, y0 + 1, -2, "south", loot=LOOT + "sylvan_palace_royal")
    bp.chain(0, top - 2, 0, top - 1)
    bp.lantern(0, top - 3, 0, hanging=True)


# ------------------------------------------------------------------ tree houses and bridges
def small_tree(bp, cx, cz, deck):
    h = deck + 12
    for y in range(-1, h + 1):
        r = 2.4 if y < deck + 4 else 1.5
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                if math.hypot(x - cx, z - cz) <= r:
                    bp.set(x, y, z, BARK.pick(x, y, z))
    for k in range(4):                        # little roots
        a = math.radians(k * 90 + 45)
        for i in range(3, 6):
            x, z = cx + round(math.cos(a) * i), cz + round(math.sin(a) * i)
            for y in range(-1, 6 - i):
                bp.set(x, y, z, BARK.pick(x, y, z))
    for ti, (base, R, th) in enumerate(((h - 3, 9, 2.5), (h + 2, 6, 2.5), (h + 6, 3, 2.0))):
        for x in range(cx - R - 1, cx + R + 2):
            for z in range(cz - R - 1, cz + R + 2):
                d = math.hypot(x - cx, z - cz)
                a = math.atan2(z - cz, x - cx)
                rr = R * (0.85 + 0.15 * math.sin(a * 4 + ti + cx))
                if d > rr:
                    continue
                k = math.sqrt(1 - (d / rr) ** 2)
                for y in range(int(base - k), int(base + th * k) + 1):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, "shroomlight" if _hash(x, y, z, 9) < 0.015 else LEAF.pick(x, y, z))
                if d > rr - 1.2 and _hash(x, 5, z, ti) < 0.5:
                    for i in range(1, 3):
                        if bp.get(x, int(base - k) - i, z) is None:
                            bp.set(x, int(base - k) - i, z, LEAF.pick(x, 0, z))
    # deck and brackets
    R = 7
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x - cx, z - cz)
            if 2.4 < d <= R + 0.4:
                bp.set(x, deck, z, WHITE.pick(x, deck, z) if d > R - 0.6 else PLANK)
    for a in range(0, 360, 5):
        x, z = cx + round(math.cos(math.radians(a)) * R), cz + round(math.sin(math.radians(a)) * R)
        if bp.get(x, deck + 1, z) is None:
            bp.set(x, deck + 1, z, FENCE)
    for k in range(6):
        a = math.radians(k * 60)
        for i in range(0, 6):
            x, z = cx + round(math.cos(a) * (2 + i)), cz + round(math.sin(a) * (2 + i))
            bp.set(x, deck - 6 + i, z, BARK.pick(x, deck - 6 + i, z))


def bridge(bp, p0, p1):
    """A rope bridge (birch slabs on chains between fence rails) with a gentle sag."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(z1 - z0)) * 1.5) + 1
    length = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / length, (z1 - z0) / length
    px, pz = -uz, ux
    last = None
    for i in range(n + 1):
        t = i / n
        yf = y0 + (y1 - y0) * t - 1.6 * 4 * t * (1 - t)
        bx, bz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
        yb = math.floor(yf)
        kind = "top" if yf - yb >= 0.5 else "bottom"
        for w in (-1, 0, 1):
            x, z = round(bx + px * w), round(bz + pz * w)
            if bp.get(x, yb, z) in (None, "minecraft:air") or "leaves" in (bp.get(x, yb, z) or ""):
                bp.set(x, yb, z, slab(PLANK_SLAB, kind))
                for yy in range(yb + 1, yb + 4):
                    if bp.get(x, yy, z) is not None and "leaves" in bp.get(x, yy, z):
                        bp.set(x, yy, z, "air")
        for w in (-2, 2):
            x, z = round(bx + px * w), round(bz + pz * w)
            if bp.get(x, yb + 1, z) in (None, "minecraft:air") or "leaves" in (bp.get(x, yb + 1, z) or ""):
                bp.set(x, yb, z, slab(PLANK_SLAB, kind))
                bp.set(x, yb + 1, z, FENCE)
        last = (round(bx), yb, round(bz))
    return last


def satellites(bp):
    kinds = ("guest", "music", "guest")
    for i, (sx, sz, deck, _) in enumerate(SATELLITES):
        small_tree(bp, sx, sz, deck)
        d = math.hypot(sx, sz)
        ux, uz = sx / d, sz / d
        # pavilion on the deck, door towards the great tree
        door = math.degrees(math.atan2(-uz, -ux))
        pod(bp, sx + round(ux * 3), deck, sz + round(uz * 3), 3, door, kinds[i], seed=i)
        # rope bridge from the first terrace to the deck
        L1 = LEVELS[0]
        a = (round(ux * 14), L1, round(uz * 14))
        b = (sx - round(ux * 7), deck, sz - round(uz * 7))
        bridge(bp, a, b)
        for (x, y, z) in (a, b):
            for w in (-2, 2):
                xx, zz = x + round(-uz * w), z + round(ux * w)
                bp.set(xx, y + 1, zz, PILLAR)
                bp.set(xx, y + 2, zz, PILLAR)
                bp.set(xx, y + 3, zz, "lantern[hanging=false,waterlogged=false]")
            for w in (-1, 0, 1):
                xx, zz = x + round(-uz * w), z + round(ux * w)
                for yy in (y + 1, y + 2, y + 3):
                    if bp.get(xx, yy, zz) is not None and "pillar" not in bp.get(xx, yy, zz):
                        bp.set(xx, yy, zz, "air")


# ------------------------------------------------------------------ the moon pool and garden
def moon_pool(bp):
    cx, cz, r = 0, 25, 8
    for x in range(cx - r - 6, cx + r + 7):
        for z in range(cz - r - 6, cz + r + 7):
            d = math.hypot(x - cx, z - cz)
            if d <= r - 0.6:
                deep = d < r - 2.5
                bp.set(x, 0, z, "water[level=0]")
                bp.set(x, -1, z, "water[level=0]" if deep else "calcite")
                bp.set(x, -2, z, "sea_lantern" if deep and (x + z) % 4 == 0 else "calcite")
                if _hash(x, 0, z, 12) < 0.07 and d > 3:
                    bp.set(x, 1, z, "lily_pad")
            elif d <= r + 0.4:
                bp.set(x, 0, z, WHITE.pick(x, 0, z))
                bp.set(x, 1, z, "quartz_slab[type=bottom,waterlogged=false]" if int(d * 7) % 5 else "air")
            elif d <= r + 5.4 and bp.get(x, 0, z) is None:
                bp.set(x, 0, z, "grass_block[snowy=false]")
                h = _hash(x, 1, z, 13)
                if h < 0.35:
                    bp.set(x, 1, z, ["lily_of_the_valley", "white_tulip", "azure_bluet", "oxeye_daisy", "allium",
                                     "short_grass", "fern"][int(h * 100) % 7])
                elif h > 0.97:
                    for (dx, dz, dy) in ((0, 0, 1), (1, 0, 1), (0, 1, 1), (0, 0, 2)):
                        bp.set(x + dx, dy, z + dz, LV("flowering_azalea_leaves"), keep=True)
    # the crescent moon sculpture on an islet
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            bp.set(x, 0, z, "calcite")
            bp.set(x, -1, z, "calcite")
    bp.set(cx, 1, cz, PILLAR)
    bp.set(cx, 2, cz, PILLAR)
    for k in range(0, 181, 12):
        a = math.radians(k + 90)
        x = cx + round(math.cos(a) * 3 * 0.6)
        y = 6 + round(math.sin(a) * 3)
        bp.set(x, y, cz, "smooth_quartz")
        if 30 < k < 150:
            bp.set(x - 1 if x <= cx else x + 1, y, cz, "smooth_quartz")
    for y in range(3, 10):
        if bp.get(cx, y, cz) is None:
            bp.set(cx, y, cz, "air")
    bp.set(cx, 3, cz, GOLD)
    bp.set(cx - 2, 6, cz, "pearlescent_froglight[axis=y]")
    # lantern posts and a path from the root gate
    for z in range(10, cz - r):
        for x in (-1, 0, 1):
            bp.set(x, 0, z, "moss_block" if (x + z) % 3 == 0 else "dirt_path")
    for a in range(0, 360, 45):
        x, z = cx + round(math.cos(math.radians(a)) * (r + 2)), cz + round(math.sin(math.radians(a)) * (r + 2))
        bp.set(x, 0, z, "grass_block[snowy=false]")
        bp.set(x, 1, z, "birch_fence")
        bp.set(x, 2, z, "birch_fence")
        bp.set(x, 3, z, "lantern[hanging=false,waterlogged=false]")


def sylvan_palace(bp):
    trunk(bp)
    roots(bp)
    canopy(bp)
    for L in LEVELS:
        terrace(bp, L)
    # pavilions on the terrace lobes, doors facing the trunk
    for (L, a, d, r, kind) in ((14, 330, 10, 4, "guest"), (30, 200, 11, 4, "banquet"), (30, 330, 11, 4, "music"),
                               (46, 140, 9, 3, "queen"), (46, 250, 9, 3, "library")):
        x, z = _lobe_xy(a, d)
        pod(bp, x, L, z, r, a + 180, kind)
    for (L, a, d) in ((14, 60, 8), (30, 90, 13), (30, 70, 9), (30, 110, 9), (46, 20, 10)):
        x, z = _lobe_xy(a, d)
        planter(bp, x, L, z)
    for (L, kind, door) in ((LEVELS[0], "spring", 0), (LEVELS[1], "throne", 90), (LEVELS[2], "treasury", 20)):
        trunk_room(bp, L, door, kind)
    spiral_stair(bp)
    satellites(bp)
    moon_lantern(bp)
    moon_pool(bp)
    # the sylvan court lives in the pavilions and the heartwood halls: a bed and a job site each
    court = {"guest": [("librarian", 3)], "banquet": [("butcher", 3)], "music": [("shepherd", 3)],
             "queen": [("cleric", 5)], "library": [("librarian", 4)]}
    for i, (L, a, d, r, kind) in enumerate(((14, 330, 10, 4, "guest"), (30, 200, 11, 4, "banquet"),
                                            (30, 330, 11, 4, "music"), (46, 140, 9, 3, "queen"),
                                            (46, 250, 9, 3, "library"))):
        x, z = _lobe_xy(a, d)
        INT.populate(bp, court[kind], region=((x - r, L + 1, z - r), (x + r, L + 1, z + r)), vtype="plains",
                     seed=i, bed_colour="white")
    for i, (L, people) in enumerate(((LEVELS[0], [("farmer", 3)]), (LEVELS[1], [("cartographer", 4)]))):
        INT.populate(bp, people, region=((-4, L + 1, -4), (4, L + 1, 4)), vtype="plains", seed=10 + i,
                     bed_colour="light_blue")
    # furnished pods and trunk halls: beds of moss and wool, shelves of seeds and books, potted saplings
    INT.decorate(bp, dict(INT.THEMES["home"], wood="birch", rugs=["green", "lime", "white"],
                          floor={"plant": 4, "bookshelf": 2, "barrel": 2, "pot": 2, "workbench": 1, "bed": 1,
                                 "chiseled": 1},
                          shelf_items=["wheat_seeds", "pumpkin_seeds", "book", "honey_bottle", "glow_berries",
                                       "sweet_berries", "oak_sapling"],
                          banners=["green", "lime", "white"]), seed=1)


register(StructureDef(
    "sylvan_palace", "overworld",
    ["dark_forest", "old_growth_spruce_taiga", "old_growth_pine_taiga", "old_growth_birch_forest", "flower_forest"],
    [Piece("palace", sylvan_palace)],
    spacing=64, separation=24, adaptation="beard_thin", processors="none", max_distance=100,
    peaceful=True,
    title_fr="Palais sylvain", title_en="Sylvan Palace"))
