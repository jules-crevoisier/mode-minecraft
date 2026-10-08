"""Tesla Observatory: an aether-science campus on a mountain crag (Lot 7, mega-structures).

Layout, terrace y = 0 on a rocky crag that widens downwards so the whole campus sits on any peak:
  * the Great Observatory (west): a cream-stone drum with brass pilasters under a verdigris copper dome cut by an
    observing slit, through which a 30-block brass telescope points at the sky; star-chart hall, alchemy lab and
    observing floor inside,
  * the Tesla Tower (north-east): a generator hall with dynamos under a 70-block lattice tower around a copper
    coil, crowned by a great toroid bristling with lightning rods and end rods,
  * the Orrery Rotunda (south-east): planets of wool and concrete on brass arms circling a glowing sun under a
    glass dome topped by an armillary sphere,
  * the Library and Laboratory wing between them, a courtyard with a sundial, balustrades and lamp posts.
Style: Piltover cream stone, brass and verdigris (tools/STYLE_STEAMPUNK.md), cyan aether glow.
"""
import math

from .. import interior as INT
from ..arch import spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import (AETHER, BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP,
                       IRON, IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_SLAB, MAHOGANY_STAIRS,
                       PIPES, TABLE, TREAD, VERD, W, chain, fbm, hang_lamp, hash01, hash3, is_air, lantern_post,
                       out_facing, railing, ring_railing, vnoise)
from ..parts import LOOT

CREAM, CREAM2, CREAM_TRIM = "calcite", "polished_diorite", "smooth_quartz"
DARK, DARK2 = "polished_deepslate", "deepslate_tiles"
DARK_STAIRS, DARK_SLAB, DARK_WALL = "polished_deepslate_stairs", "polished_deepslate_slab", "polished_deepslate_wall"
CREAM_STAIRS, CREAM_SLAB = "polished_diorite_stairs", "polished_diorite_slab"
OXI, OXI_CUT, OXI_STAIRS, OXI_SLAB = ("oxidized_copper", "oxidized_cut_copper", "oxidized_cut_copper_stairs",
                                      "oxidized_cut_copper_slab")
WEA_CUT = "waxed_weathered_cut_copper"
CU, CU_CUT, CU_GRATE, CU_BULB = ("waxed_copper_block", "waxed_cut_copper", "waxed_copper_grate",
                                 "waxed_copper_bulb[lit=true,powered=false]")
ROD = "lightning_rod[facing=up,powered=false,waterlogged=false]"

R_TERRACE = 39
OBS_X, OBS_Z, OBS_R, OBS_H = -18, -4, 12, 16
TES_X, TES_Z = 20, -18
ORR_X, ORR_Z, ORR_R, ORR_H = 20, 20, 11, 11
LIB_X0, LIB_X1, LIB_Z0, LIB_Z1 = -13, 6, 13, 27


def wall_pal(x, y, z):
    n = vnoise(x + y * 0.5, z - y * 0.3, 3.0, 61)
    return CREAM if n < 0.55 else CREAM2


def edge_r(x, z):
    return R_TERRACE + 3 * (fbm(x, z, 9.0, 4) - 0.5)


# ------------------------------------------------------------------ crag and terrace
def crag(bp):
    """The mountain top: a terrace on a rocky crag that widens downwards for 26 blocks (outer shell + top slab)."""
    depth = 26
    for x in range(-R_TERRACE - 18, R_TERRACE + 19):
        for z in range(-R_TERRACE - 18, R_TERRACE + 19):
            r = math.hypot(x, z - 2)
            er = edge_r(x, z)
            for d in range(1, depth + 1):
                y = -d
                reach = er + d * 0.55 + 4 * (fbm(x + d * 3, z - d * 2, 7.0, 9) - 0.5)
                if r > reach:
                    continue
                if d > 8 and r < reach - 4:
                    continue   # below 8 blocks only the outer shell: the real mountain fills the core
                n = vnoise(x + d, z, 4.0, 12 + d // 5)
                spec = ("stone" if n < 0.45 else "andesite" if n < 0.7 else "tuff" if n < 0.88 else "calcite")
                if d <= 2 and r > er - 1:
                    spec = DARK2 if d == 1 else "cobbled_deepslate"
                bp.set(x, y, z, spec)
            # mossy or snowy ledges where the crag steps out
            top_out = er
            if top_out < r <= er + 14:
                for d in range(1, depth + 1):
                    reach = er + d * 0.55 + 4 * (fbm(x + d * 3, z - d * 2, 7.0, 9) - 0.5)
                    if r <= reach:
                        if hash01(x, z, 77) < 0.35 and is_air(bp, x, -d + 1, z):
                            bp.set(x, -d + 1, z, "moss_carpet")
                        break


def terrace(bp):
    for x in range(-R_TERRACE - 3, R_TERRACE + 4):
        for z in range(-R_TERRACE - 3, R_TERRACE + 4):
            r = math.hypot(x, z - 2)
            er = edge_r(x, z)
            if r > er:
                continue
            n = vnoise(x, z, 5.0, 14)
            if r > er - 1.2:
                spec = DARK
            elif (x + z) % 9 == 0 and n < 0.3:
                spec = "mossy_stone_bricks"
            else:
                spec = "stone_bricks" if n < 0.45 else ("polished_andesite" if n < 0.8 else "cracked_stone_bricks")
            bp.set(x, 0, z, spec)
            for y in range(1, 13):
                bp.set(x, y, z, "air")
    # balustrade along the edge: cream posts and brass rails
    for x in range(-R_TERRACE - 3, R_TERRACE + 4):
        for z in range(-R_TERRACE - 3, R_TERRACE + 4):
            r = math.hypot(x, z - 2)
            er = edge_r(x, z)
            if er - 1.2 < r <= er:
                if any(math.hypot(x + dx, z + dz - 2) > edge_r(x + dx, z + dz) for dx, dz in
                       ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    post = (x * 3 + z * 7) % 6 == 0
                    if abs(x) <= 2 and z > 0:
                        continue  # the south stair
                    bp.set(x, 1, z, CREAM_TRIM if post else "diorite_wall")
                    if post:
                        bp.set(x, 2, z, "polished_diorite_slab[type=bottom,waterlogged=false]")
    # paved paths: brass-edged walks between the buildings
    for (x0, z0, x1, z1) in ((-3, -12, 2, 40), (-6, 0, 12, 4), (-8, 6, 0, 13), (6, 18, 10, 22), (10, -11, 15, 0)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if bp.get(x, 0, z) is not None and math.hypot(x, z - 2) < edge_r(x, z) - 1.5:
                    bp.set(x, 0, z, "polished_deepslate" if (x + z) % 2 else "polished_andesite")


def grand_stair(bp):
    """Stairs descending the crag on the south side, so visitors can walk up from the slopes."""
    zs = int(edge_r(0, 44)) + 2
    zs = 0
    for z in range(30, 60):
        if math.hypot(0, z - 2) > edge_r(0, z) - 0.5:
            zs = z
            break
    for i in range(0, 20):
        z = zs + i
        y = -1 - i
        for x in range(-2, 3):
            bp.set(x, y, z, stair(DARK_STAIRS, "north") if abs(x) < 2 else DARK)
            for yy in range(y - 4, y):
                bp.set(x, yy, z, "stone" if abs(x) < 2 else "cobbled_deepslate")
            for yy in range(y + 1, y + 4):
                if abs(x) < 2:
                    bp.set(x, yy, z, "air")
        for x in (-3, 3):
            bp.set(x, y, z, DARK)
            bp.set(x, y + 1, z, DARK_WALL)
            if i % 5 == 0:
                bp.set(x, y + 2, z, EDISON)
    for x in (-3, 3):
        bp.set(x, 1, zs - 1, CREAM_TRIM)
        bp.set(x, 2, zs - 1, CREAM_TRIM)
        bp.set(x, 3, zs - 1, EDISON)


# ------------------------------------------------------------------ helpers
def drum(bp, cx, cz, r, y0, y1, floors, windows, pilasters=12, door_dirs=()):
    """Round stone drum with a dark plinth, iron pilasters with brass capitals, arched windows on every floor."""
    for y in range(y0, y1 + 1):
        for x in range(cx - r - 2, cx + r + 3):
            for z in range(cz - r - 2, cz + r + 3):
                d = math.hypot(x - cx, z - cz)
                if d <= r - 0.6:
                    if y == y0 or y in floors:
                        continue
                    bp.set(x, y, z, "air")
                elif d <= r + 0.4:
                    spec = wall_pal(x, y, z)
                    if y <= y0 + 1:
                        spec = DARK2
                    elif y == y1:
                        spec = BRASS
                    elif y in floors:
                        spec = DARK
                    bp.set(x, y, z, spec)
    # floors
    for fy in [y0] + list(floors):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= r - 0.6:
                    ring = abs(d - (r - 3)) < 0.5
                    bp.set(x, fy, z, (BRASS if ring else MAHOGANY if fy != y0 else DARK) if fy != y0 else
                           ("polished_deepslate" if ring else DARK2 if (x + z) % 2 else "deepslate_bricks"))
    # pilasters and windows
    for k in range(pilasters):
        a = 2 * math.pi * k / pilasters
        px, pz = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
        for y in range(y0, y1):
            bp.set(px, y, pz, IRON if (y - y0) % 8 else BRASS)
        bp.set(px, y1, pz, stair(BRASS_STAIRS, out_facing(cx - px, cz - pz), "top"))
        bp.set(px, y0, pz, DARK2)
        # window in the middle of the bay
        b = a + math.pi / pilasters
        wx, wz = cx + math.cos(b) * r, cz + math.sin(b) * r
        for (wy0, wy1) in windows:
            for y in range(wy0, wy1 + 1):
                for off in (-0.6, 0.6):
                    tx = cx + math.cos(b) * r + (-math.sin(b)) * off
                    tz = cz + math.sin(b) * r + math.cos(b) * off
                    gx, gz = round(tx), round(tz)
                    if abs(math.hypot(gx - cx, gz - cz) - r) <= 0.7:
                        bp.set(gx, y, gz, "glass_pane" if y < wy1 else CREAM_TRIM)
            sx, sz = round(cx + math.cos(b) * (r + 1)), round(cz + math.sin(b) * (r + 1))
            bp.set(sx, wy0 - 1, sz, stair(CREAM_STAIRS, out_facing(cx - sx, cz - sz), "top"))


def doorway(bp, cx, cz, r, y0, direction, width=3, height=4, door=None):
    """Cut an arched entrance through a drum wall on `direction` (north/south/east/west)."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[direction]
    half = width // 2
    for depth in range(r - 2, r + 3):
        for u in range(-half - 1, half + 2):
            x = cx + dx * depth + (u if dz else 0)
            z = cz + dz * depth + (u if dx else 0)
            for y in range(y0 + 1, y0 + height + 2):
                inner = abs(u) <= half and y <= y0 + height
                if inner:
                    bp.set(x, y, z, "air")
                elif depth >= r and depth <= r + 1:
                    bp.set(x, y, z, BRASS if y == y0 + height + 1 else IRON)
            if abs(u) <= half:
                bp.set(x, y0, z, DARK)
    if door:
        x, z = cx + dx * r, cz + dz * r
        if width == 1:
            bp.door(x, y0 + 1, z, direction, door)


def dome(bp, cx, cy, cz, r, fn, slit=None, ribs=8, rib_spec=WEA_CUT):
    """Hemispherical dome shell; fn(x, y, z) gives the material, slit(x, y, z) True carves the observing slit."""
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            for y in range(cy, cy + r + 2):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if d <= r - 0.6:
                    bp.set(x, y, z, "air")
                elif d <= r + 0.4:
                    if slit and slit(x, y, z):
                        bp.set(x, y, z, "air")
                        continue
                    ang = math.degrees(math.atan2(z - cz, x - cx))
                    on_rib = ribs and min(abs((ang - k * 360 / ribs + 180) % 360 - 180) for k in range(ribs)) * \
                        math.pi / 180 * math.hypot(x - cx, z - cz) < 0.6
                    bp.set(x, y, z, rib_spec if on_rib else fn(x, y, z))


def cylinder_along(bp, p0, d, t0, t1, radius, fn):
    """Solid cylinder along unit vector d from p0 + t0*d to p0 + t1*d; fn(t, rho) gives the block (or None)."""
    pts = [(p0[i] + d[i] * t) for t in (t0, t1) for i in range(3)]
    xs, ys, zs = pts[0::3], pts[1::3], pts[2::3]
    R = radius + 1.5
    for x in range(int(min(xs) - R), int(max(xs) + R) + 1):
        for y in range(int(min(ys) - R), int(max(ys) + R) + 1):
            for z in range(int(min(zs) - R), int(max(zs) + R) + 1):
                v = (x - p0[0], y - p0[1], z - p0[2])
                t = v[0] * d[0] + v[1] * d[1] + v[2] * d[2]
                if t < t0 or t > t1:
                    continue
                q = (v[0] - t * d[0], v[1] - t * d[1], v[2] - t * d[2])
                rho = math.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2)
                spec = fn(t, rho)
                if spec:
                    bp.set(x, y, z, spec)


# ------------------------------------------------------------------ the Great Observatory
def observatory(bp):
    cx, cz, r, h = OBS_X, OBS_Z, OBS_R, OBS_H
    drum(bp, cx, cz, r, 0, h, floors=(8,), windows=((2, 6), (10, 14)), pilasters=12)
    # outer walk around the dome base, with railing
    for x in range(cx - r - 3, cx + r + 4):
        for z in range(cz - r - 3, cz + r + 4):
            d = math.hypot(x - cx, z - cz)
            if r - 0.6 < d <= r + 2.4:
                bp.set(x, h, z, TREAD if d > r + 0.4 else BRASS)
            if r + 1.6 < d <= r + 2.4:
                bp.set(x, h - 1, z, stair(BRASS_STAIRS, out_facing(cx - x, cz - z), "top"))
    ring_railing(bp, cx, h + 1, cz, r + 2)
    # telescope floor
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            if math.hypot(x - cx, z - cz) <= r - 0.6:
                bp.set(x, h, z, TREAD if (x + z) % 3 else IRON)

    # the dome, with a slit facing south-east and the brass ring it turns on
    sdir = (math.cos(math.radians(-50)), math.sin(math.radians(-50)))   # north-east, towards the pole star

    def slit(x, y, z):
        vx, vz = x - cx, z - cz
        along = vx * sdir[0] + vz * sdir[1]
        across = -vx * sdir[1] + vz * sdir[0]
        return abs(across) <= 2.2 and (along > -3 or y > h + 1 + r - 3) and y > h + 1

    def shell(x, y, z):
        n = vnoise(x * 1.3, z * 1.3 + y, 3.0, 71)
        return OXI if n < 0.55 else ("waxed_weathered_copper" if n < 0.85 else OXI_CUT)

    dr = r - 1
    dome(bp, cx, h + 1, cz, dr, shell, slit=slit, ribs=8)
    for x in range(cx - dr - 1, cx + dr + 2):
        for z in range(cz - dr - 1, cz + dr + 2):
            d = math.hypot(x - cx, z - cz)
            if dr - 0.6 < d <= dr + 0.4:
                bp.set(x, h + 1, z, BRASS if not slit(x, h + 2, z) else BRASS)
    # slit frame: brass edges along the opening
    for x in range(cx - dr - 1, cx + dr + 2):
        for z in range(cz - dr - 1, cz + dr + 2):
            for y in range(h + 2, h + dr + 3):
                d = math.sqrt((x - cx) ** 2 + (y - h - 1) ** 2 + (z - cz) ** 2)
                if dr - 0.6 < d <= dr + 0.4 and not slit(x, y, z):
                    if any(slit(x + ex, y, z + ez) for ex, ez in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        bp.set(x, y, z, BRASS)
    telescope(bp, cx, cz, h, sdir)
    observatory_inside(bp, cx, cz, r, h)
    for direction in ("east", "south"):
        doorway(bp, cx, cz, r, 0, direction, width=3, height=4)


def telescope(bp, cx, cz, floor, sdir):
    """A 30-block brass refractor on a fork mount, aimed through the slit at 38 degrees."""
    el = math.radians(38)
    d = (sdir[0] * math.cos(el), math.sin(el), sdir[1] * math.cos(el))
    p0 = (cx, floor + 6, cz)

    def tube(t, rho):
        if t > 21.5 and rho < 2.6:
            return "glass" if rho < 1.6 and t > 23.2 else BRASS if rho > 1.6 else "air"
        if rho <= 1.6:
            if t < -7:
                return COPPER
            band = int(t) % 5 == 0
            return COPPER if band else BRASS
        if rho <= 2.4 and (int(t) % 5 == 0 or t > 20):
            return BRASS
        return None

    cylinder_along(bp, p0, d, -8, 24, 2.6, tube)
    # dew-cap lens glow and the eyepiece
    e = (p0[0] - d[0] * 8.6, p0[1] - d[1] * 8.6, p0[2] - d[2] * 8.6)
    bp.set(round(e[0]), round(e[1]), round(e[2]), GAUGE)
    # fork mount: pier, gear ring, two arms and the trunnion axle
    for y in range(floor + 1, floor + 4):
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if math.hypot(x - cx, z - cz) <= 2.4:
                    bp.set(x, y, z, GEAR if y == floor + 3 and (x + z) % 2 else IRON)
    ax = (-sdir[1], sdir[0])
    for side in (-1, 1):
        for k in range(0, 4):
            x = round(cx + ax[0] * 3 * side)
            z = round(cz + ax[1] * 3 * side)
            bp.set(x, floor + 3 + k, z, IRON if k < 3 else BRASS)
        bp.set(round(cx + ax[0] * 2 * side), floor + 6, round(cz + ax[1] * 2 * side), GEAR)
    # the observer's chair and the star atlas
    ex, ez = round(cx - sdir[0] * 5), round(cz - sdir[1] * 5)
    bp.set(ex, floor + 1, ez, W + "mahogany_chair[facing=%s]" % out_facing(sdir[0], sdir[1]))
    bp.set(ex - 1, floor + 1, ez + 2, TABLE)
    bp.set(ex + 2, floor + 1, ez - 1, "lectern[facing=%s,has_book=false,powered=false]" % out_facing(sdir[0], sdir[1]))


def ring_furnish(bp, cx, cz, rad, y, items, step_deg=20, skip=()):
    """Furniture around the inner wall of a round room: items cycle [(block, block above or None)], '%s' in a
    block spec is replaced by the direction facing the room centre. `skip` = ((x, z, radius), ...) to keep clear."""
    k = 0
    for deg in range(0, 360, step_deg):
        a = math.radians(deg)
        x, z = cx + round(math.cos(a) * rad), cz + round(math.sin(a) * rad)
        if any(math.hypot(x - sx, z - sz) <= sr for sx, sz, sr in skip):
            continue
        if bp.get(x, y, z) != "minecraft:air" or bp.get(x, y + 1, z) != "minecraft:air":
            continue
        f = out_facing(cx - x, cz - z)
        low, high = items[k % len(items)]
        k += 1
        bp.set(x, y, z, low % f if "%s" in low else low)
        if high:
            bp.set(x, y + 1, z, high % f if "%s" in high else high)


def observatory_inside(bp, cx, cz, r, h):
    # spiral stair in a cage at the north-west of the drum, through both floors
    sx, sz = cx - 6, cz - 5
    for y in (8, h):
        for x in range(sx - 2, sx + 3):
            for z in range(sz - 2, sz + 3):
                bp.set(x, y, z, "air")
    bp.spiral_stairs(sx, sz, 1, h - 1, 2, W + "diamond_plate_slab", center=W + "copper_pipe[axis=y]")
    for x in range(sx - 2, sx + 3):
        for z in range(sz - 2, sz + 3):
            if max(abs(x - sx), abs(z - sz)) == 2 and bp.get(x, h, z) == "minecraft:air":
                pass
    for y in (8, h):
        for (x, z) in ((sx + 3, sz), (sx, sz + 3), (sx + 3, sz + 1), (sx + 1, sz + 3)):
            bp.set(x, y, z, TREAD)
    # ground floor: the Star Chart Hall: a mosaic of the night sky, bookcases between the windows, globes
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            if d <= 6.4:
                star = hash01(x, z, 5) < 0.12
                bp.set(x, 0, z, "gold_block" if d < 0.6 else ("white_concrete" if star else
                                                               ("blue_terracotta" if d > 3.5 else "lapis_block")))
    for k in range(12):
        a = 2 * math.pi * k / 12
        x, z = cx + round(math.cos(a) * (r - 1)), cz + round(math.sin(a) * (r - 1))
        if bp.get(x, 1, z) == "minecraft:air" and not (abs(x - (cx + r - 1)) < 2 and abs(z - cz) < 3) and \
                not (abs(z - (cz + r - 1)) < 2 and abs(x - cx) < 3):
            for y in (1, 2, 3):
                bp.set(x, y, z, "bookshelf" if y < 3 else "chiseled_bookshelf[facing=%s,slot_0_occupied=true,"
                       "slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,"
                       "slot_5_occupied=true]" % out_facing(cx - x, cz - z))
    for (dx, dz) in ((4, -4), (-4, 4)):
        bp.set(cx + dx, 1, cz + dz, IRON)
        bp.set(cx + dx, 2, cz + dz, "blue_concrete")
        bp.set(cx + dx, 3, cz + dz, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    bp.chest(cx + 7, 1, cz - 6, "west", loot=LOOT + "observatory_study")
    hang_lamp(bp, cx, 6, cz, length=1, lamp=CHANDELIER)
    # first floor: the alchemy laboratory
    lab_y = 9
    for k, (dx, dz) in enumerate(((5, 0), (5, 2), (5, -2), (3, 6), (0, 7), (-3, 6))):
        x, z = cx + dx, cz + dz
        bp.set(x, lab_y, z, TABLE if k % 2 else "polished_deepslate")
        bp.set(x, lab_y + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    for (dx, dz) in ((7, 4), (2, 8), (-1, 8)):
        bp.set(cx + dx, lab_y, cz + dz, "water_cauldron[level=2]")
    bp.set(cx - 2, lab_y, cz + 3, "enchanting_table")
    for (dx, dz) in ((-4, 3), (0, 3), (-2, 5), (-2, 1)):
        bp.set(cx + dx, lab_y, cz + dz, "bookshelf")
    ring_furnish(bp, cx, cz, r - 2, lab_y, [
        (TABLE, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]"),
        ("barrel[facing=up,open=false]", None), ("lectern[facing=%s,has_book=false,powered=false]", None),
        (TABLE, "potted_crimson_fungus"), ("cauldron", None), (W + "compacting_crate[facing=%s]", None),
        (TABLE, "amethyst_cluster[facing=up,waterlogged=false]"), ("bookshelf", "bookshelf"),
        ("smoker[facing=%s,lit=true]", None), (TABLE, "potted_warped_fungus")], skip=((sx, sz, 3),))
    bp.chest(cx + 8, lab_y, cz - 3, "west", loot=LOOT + "observatory_lab")
    bp.barrel(cx + 8, lab_y, cz + 1, "up", loot=LOOT + "observatory_lab")
    for (dx, dz) in ((6, -6), (-2, -8)):
        bp.set(cx + dx, lab_y, cz + dz, "amethyst_block")
        bp.set(cx + dx, lab_y + 1, cz + dz, "amethyst_cluster[facing=up,waterlogged=false]")
    hang_lamp(bp, cx + 3, h - 2, cz + 3, length=1)
    hang_lamp(bp, cx - 3, h - 2, cz + 3, length=1)
    # observing floor: the vault of discoveries
    bp.chest(cx - 4, h + 1, cz + 7, "north", loot=LOOT + "observatory_vault")
    bp.set(cx - 5, h + 1, cz + 7, "cartography_table")
    bp.set(cx - 3, h + 1, cz + 7, W + "compacting_crate[facing=north]")


# ------------------------------------------------------------------ the Tesla Tower
def tesla(bp):
    cx, cz = TES_X, TES_Z
    hx = 7
    top = 10
    # generator hall
    for x in range(cx - hx, cx + hx + 1):
        for z in range(cz - hx, cz + hx + 1):
            ex, ez = abs(x - cx) == hx, abs(z - cz) == hx
            bp.set(x, 0, z, DARK2 if (ex or ez) else (TREAD if (x + z) % 4 else IRON))
            for y in range(1, top):
                if ex or ez:
                    corner = ex and ez
                    pil = (x - cx) % 4 == 3 or (z - cz) % 4 == 3 if not corner else True
                    if corner or (ex and (z - cz) % 4 == 0) or (ez and (x - cx) % 4 == 0):
                        spec = IRON if y < top - 1 else BRASS
                    elif 2 <= y <= 6:
                        spec = "glass_pane" if y < 6 else stair(DARK_STAIRS, "north" if ez and z < cz else "south"
                                                                if ez else "west" if x < cx else "east", "top")
                    elif y == 1:
                        spec = DARK2
                    elif y == 7:
                        spec = BRASS
                    else:
                        spec = DARK
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, top, z, DARK if (ex or ez) else IRON)
    # fix the window heads: real arches need the stairs to face along the wall, simpler: dark lintel
    for x in range(cx - hx, cx + hx + 1):
        for z in range(cz - hx, cz + hx + 1):
            if (abs(x - cx) == hx or abs(z - cz) == hx) and bp.get(x, 6, z) and "stairs" in bp.get(x, 6, z):
                bp.set(x, 6, z, DARK)
    # parapet and corner pinnacle coils
    for x in range(cx - hx - 1, cx + hx + 2):
        for z in range(cz - hx - 1, cz + hx + 2):
            if max(abs(x - cx), abs(z - cz)) == hx + 1:
                bp.set(x, top, z, stair(DARK_STAIRS, out_facing(cx - x, cz - z) if True else "north", "top"))
            if max(abs(x - cx), abs(z - cz)) == hx:
                bp.set(x, top + 1, z, DARK_WALL if (x + z) % 2 else CREAM_TRIM)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = cx + sx * (hx - 1), cz + sz * (hx - 1)
            mini_coil(bp, x, top + 1, z)
    # doors west and south
    for (dx, dz) in ((-hx, 0), (0, hx)):
        for u in (-1, 0, 1):
            x = cx + dx + (u if dz else 0)
            z = cz + dz + (u if dx else 0)
            for y in range(1, 5):
                bp.set(x, y, z, "air")
            bp.set(x, 5, z, BRASS)
    generator_hall(bp, cx, cz, hx, top)
    tower(bp, cx, cz, top)


def mini_coil(bp, x, y, z):
    for k in range(4):
        bp.set(x, y + k, z, CU_GRATE if k % 2 else CU)
    bp.set(x, y + 4, z, CU_BULB)
    bp.set(x, y + 5, z, ROD)


def generator_hall(bp, cx, cz, hx, top):
    # two dynamos: copper drums lying east-west with clockwork end plates
    for dz in (-4, 4):
        for x in range(cx - 4, cx + 3):
            for dy in (1, 2, 3):
                for w in (-1, 0, 1):
                    if abs(w) == 1 and dy in (1, 3):
                        continue
                    end = x in (cx - 4, cx + 2)
                    bp.set(x, dy, cz + dz + w, GEAR if end else (COPPER if x % 2 else BRASS))
        for x in range(cx + 3, cx + 6):
            bp.set(x, 2, cz + dz, W + "copper_pipe[axis=x]")
        bp.set(cx + 6, 2, cz + dz, AETHER)
    # control desk with levers and gauges against the north wall
    for x in range(cx - 3, cx + 4):
        bp.set(x, 1, cz - hx + 1, IRON)
        bp.set(x, 2, cz - hx + 1, GAUGE if x % 2 else "lever[face=floor,facing=south,powered=false]")
    for x in range(cx - 3, cx + 4):
        bp.set(x, 2, cz - hx + 1, GAUGE if x % 2 else IRON)
        if x % 2 == 0:
            bp.set(x, 3, cz - hx + 1, "lever[face=floor,facing=south,powered=false]")
    # the coil base rising through the ceiling
    for y in range(1, top + 1):
        for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(cx + dx, y, cz + dz, AETHER if (dx, dz) == (0, 0) else (CU if y % 3 else CU_BULB))
    hang_lamp(bp, cx - 4, top - 2, cz, length=1)
    hang_lamp(bp, cx + 4, top - 2, cz, length=1)
    bp.chest(cx + hx - 1, 1, cz + hx - 1, "west", loot=LOOT + "tesla_tower")


def tower(bp, cx, cz, base):
    """Stepped lattice tower around the coil: 4 -> 3 -> 2 block half-width, balconies at each step."""
    stages = [(base, 26, 4), (26, 42, 3), (42, 58, 2)]
    for (y0, y1, r) in stages:
        for y in range(y0 + 1, y1 + 1):
            for x in range(cx - r, cx + r + 1):
                for z in range(cz - r, cz + r + 1):
                    ex, ez = abs(x - cx) == r, abs(z - cz) == r
                    if ex and ez:
                        bp.set(x, y, z, IRON if (y - y0) % 8 else BRASS)
                    elif ex or ez:
                        u = (x - cx) if ez else (z - cz)
                        k = (y - y0) % 8
                        if (y - y0) % 8 == 0:
                            bp.set(x, y, z, IRON)
                        elif abs(u) == round(abs(k - 4) * r / 4):
                            bp.set(x, y, z, "iron_bars")
        # balcony at the top of each stage
        br = r + 2
        for x in range(cx - br, cx + br + 1):
            for z in range(cz - br, cz + br + 1):
                m = max(abs(x - cx), abs(z - cz))
                if 1 < m <= br and not (x == cx and z == cz + 2):
                    bp.set(x, y1, z, TREAD if m < br else IRON)
                    if m == br:
                        railing(bp, x, y1 + 1, z, out_facing(x - cx, z - cz) if abs(x - cx) != abs(z - cz)
                                else ("north" if z < cz else "south"))
        for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bp.set(cx + sx * (r + 1), y1 - 1, cz + sz * (r + 1), stair(IRON_STAIRS, out_facing(-sx, 0), "top"))
            bp.set(cx + sx * br, y1 + 1, cz + sz * br, EDISON)
    # the coil: copper grates and blocks with glowing aether rings, a ladder on its south face
    for y in range(base + 1, 61):
        for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if (dx, dz) == (0, 0):
                spec = AETHER
            else:
                spec = CU_BULB if y % 6 == 0 else (CU_GRATE if y % 2 else CU)
            bp.set(cx + dx, y, cz + dz, spec)
        bp.set(cx, y, cz + 2, "ladder[facing=south,waterlogged=false]")
    for y in (26, 42, 58):
        bp.set(cx, y, cz + 2, "ladder[facing=south,waterlogged=false]")
    # the crown: a copper toroid with bulbs, lightning rods and end rods, over a copper sphere
    ty, R, rr = 64, 6.0, 1.6
    for y in range(58, 61):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                bp.set(x, y, z, CU if (x - cx) * (z - cz) else bp.get(x, y, z) or CU)
    for y in range(61, ty):
        bp.set(cx, y, cz, CU_GRATE if y % 2 else CU)
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            q = math.hypot(x - cx, z - cz)
            for y in range(ty - 3, ty + 4):
                dd = math.hypot(q - R, y - ty)
                if dd <= rr + 0.2:
                    equator = abs(y - ty) == 0 and q > R + 1
                    bp.set(x, y, z, BRASS if equator else CU)
    # spokes from the column to the ring
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(1, 5):
            bp.set(cx + dx * k, ty, cz + dz * k, "waxed_copper_bars" if 1 < k < 4 else CU_CUT)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, z = cx + round(math.cos(a) * R), cz + round(math.sin(a) * R)
        topy = max(y for y in range(ty - 3, ty + 4) if bp.get(x, y, z) in ("minecraft:" + CU, "minecraft:" + BRASS[10:])
                   or (bp.get(x, y, z) or "").endswith(("copper_block", "brass_plating")))
        bp.set(x, topy, z, CU_BULB)
        bp.set(x, topy + 1, z, ROD)
        ox, oz = cx + round(math.cos(a) * (R + rr + 1)), cz + round(math.sin(a) * (R + rr + 1))
        f = out_facing(math.cos(a), math.sin(a)) if abs(math.cos(a)) > 0.3 and abs(math.sin(a)) > 0.3 else \
            out_facing(math.cos(a), math.sin(a))
        bp.set(ox, ty, oz, "end_rod[facing=%s]" % f)
    # the top electrode: a copper sphere with a crown of rods
    sy = ty + 6
    for y in range(ty, sy - 2):
        bp.set(cx, y, cz, CU_GRATE if y % 2 else CU)
    for x in range(cx - 3, cx + 4):
        for y in range(sy - 3, sy + 4):
            for z in range(cz - 3, cz + 4):
                d = math.sqrt((x - cx) ** 2 + (y - sy) ** 2 + (z - cz) ** 2)
                if d <= 2.5:
                    bp.set(x, y, z, CU if d > 1.4 else AETHER)
    bp.set(cx, sy + 3, cz, CU)
    bp.set(cx, sy + 4, cz, ROD)
    bp.set(cx, sy + 5, cz, "end_rod[facing=up]")
    for (dx, dz, f) in ((3, 0, "east"), (-3, 0, "west"), (0, 3, "south"), (0, -3, "north")):
        bp.set(cx + dx, sy, cz + dz, "end_rod[facing=%s]" % f)


# ------------------------------------------------------------------ the Orrery Rotunda
def orrery(bp):
    cx, cz, r, h = ORR_X, ORR_Z, ORR_R, ORR_H
    drum(bp, cx, cz, r, 0, h, floors=(), windows=((2, 8),), pilasters=10)
    # zodiac floor: a ring of twelve coloured signs around a brass compass
    colours = ["red", "orange", "yellow", "lime", "green", "cyan", "light_blue", "blue", "purple", "magenta", "pink",
               "white"]
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            d = math.hypot(x - cx, z - cz)
            if d > r - 0.6:
                continue
            a = (math.degrees(math.atan2(z - cz, x - cx)) + 360) % 360
            if 7.5 < d <= 9.5:
                bp.set(x, 0, z, colours[int(a // 30)] + "_glazed_terracotta[facing=north]")
            elif 6.5 < d <= 7.5 or 9.5 < d:
                bp.set(x, 0, z, BRASS if 6.5 < d <= 7.5 else DARK2)
            else:
                bp.set(x, 0, z, "polished_deepslate" if (x + z) % 2 else "deepslate_tiles")
    # glass dome on iron ribs
    def glass(x, y, z):
        return "glass"
    dome(bp, cx, h + 1, cz, r, glass, ribs=10, rib_spec=IRON)
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = math.hypot(x - cx, z - cz)
            if r - 0.6 < d <= r + 0.4:
                bp.set(x, h + 1, z, BRASS)
            if r + 0.4 < d <= r + 1.4:
                bp.set(x, h, z, stair(BRASS_STAIRS, out_facing(cx - x, cz - z), "top"))
    # armillary sphere on the lantern at the top
    ay = h + 1 + r + 3
    for y in range(h + r + 1, ay - 2):
        bp.set(cx, y, cz, IRON)
    for k in range(0, 360, 10):
        a = math.radians(k)
        c, s = round(math.cos(a) * 2.6), round(math.sin(a) * 2.6)
        bp.set(cx + c, ay + s, cz, BRASS)
        bp.set(cx, ay + s, cz + c, BRASS)
        bp.set(cx + c, ay, cz + s, COPPER)
    bp.set(cx, ay, cz, AETHER)
    bp.set(cx, ay + 3, cz, ROD)
    # the sun on its brass pillar
    for y in range(1, 9):
        bp.set(cx, y, cz, BRASS if y % 3 else GEAR)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, 1, cz + dz, stair(BRASS_STAIRS, out_facing(-dx, -dz)))
    sun_y = 11
    for x in range(cx - 3, cx + 4):
        for y in range(sun_y - 3, sun_y + 4):
            for z in range(cz - 3, cz + 4):
                d = math.sqrt((x - cx) ** 2 + (y - sun_y) ** 2 + (z - cz) ** 2)
                if d <= 2.5:
                    bp.set(x, y, z, "ochre_froglight[axis=y]" if hash3(x, y, z, 2) < 0.5 else "shroomlight")
    # planets on arms: (name blocks, orbit radius, angle, height, size)
    planets = [
        (("light_gray_concrete",), 4, 20, 6, 0),
        (("yellow_terracotta", "white_terracotta"), 5, 110, 7, 1),
        (("blue_concrete", "lime_concrete", "white_concrete"), 7, 200, 5, 1),
        (("red_terracotta", "orange_terracotta"), 8, 290, 8, 1),
        (("orange_wool", "white_wool", "brown_wool"), 8, 60, 3, 2),
        (("yellow_wool", "white_wool"), 9, 160, 9, 1),
        (("light_blue_concrete",), 9, 250, 4, 1),
    ]
    for idx, (mats, orbit, ang, y, size) in enumerate(planets):
        a = math.radians(ang)
        px, pz = cx + round(math.cos(a) * orbit), cz + round(math.sin(a) * orbit)
        # arm: brass rod from the pillar to the planet, then a short drop
        n = max(abs(px - cx), abs(pz - cz))
        arm_y = y + size + 1
        for i in range(1, n + 1):
            x = cx + round((px - cx) * i / n)
            z = cz + round((pz - cz) * i / n)
            if math.sqrt((x - cx) ** 2 + (arm_y - sun_y) ** 2 + (z - cz) ** 2) > 2.6:
                bp.set(x, arm_y, z, BRASS_SLAB + "[type=top,waterlogged=false]" if i < n else BRASS)
        for yy in range(y + size + 1, arm_y):
            bp.set(px, yy, pz, "iron_chain[axis=y,waterlogged=false]")
        if math.sqrt((arm_y - sun_y) ** 2) > 2.6:
            bp.set(cx, arm_y, cz, GEAR)
        for x in range(px - size, px + size + 1):
            for yy in range(y - size, y + size + 1):
                for z in range(pz - size, pz + size + 1):
                    d = math.sqrt((x - px) ** 2 + (yy - y) ** 2 + (z - pz) ** 2)
                    if d <= size + 0.45:
                        m = mats[int(hash3(x, yy, z, idx) * len(mats))] if len(mats) > 1 else mats[0]
                        if idx == 4:   # banded giant
                            m = mats[(yy - y) % 3]
                        bp.set(x, yy, z, m)
        if idx == 5:   # the ringed planet
            for x in range(px - 3, px + 4):
                for z in range(pz - 3, pz + 4):
                    d = math.hypot(x - px, z - pz)
                    if 1.6 < d <= 3.0:
                        bp.set(x, y, z, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
        if idx == 2:   # the moon
            bp.set(px + 2, y + 1, pz, "white_concrete")
            bp.set(px + 1, y + 1, pz, "iron_chain[axis=x,waterlogged=false]")
    # the arm pillar continues above the sun to the dome
    for y in range(sun_y + 3, h + r):
        bp.set(cx, y, cz, IRON if y % 4 else BRASS)
    # benches around for the lectures
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        x, z = cx + round(math.cos(a) * (r - 1.5)), cz + round(math.sin(a) * (r - 1.5))
        if bp.get(x, 1, z) == "minecraft:air":
            bp.set(x, 1, z, W + "mahogany_chair[facing=%s]" % out_facing(cx - x, cz - z))
    bp.chest(cx - 3, 1, cz - r + 2, "south", loot=LOOT + "observatory_study")
    for direction in ("west", "north"):
        doorway(bp, cx, cz, r, 0, direction, width=3, height=4)


# ------------------------------------------------------------------ Library and Laboratory wing
def library(bp):
    x0, x1, z0, z1 = LIB_X0, LIB_X1, LIB_Z0, LIB_Z1
    h1, h2 = 7, 14
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            ex, ez = x in (x0, x1), z in (z0, z1)
            bp.set(x, 0, z, DARK2 if (ex or ez) else ("polished_deepslate" if (x + z) % 2 else "deepslate_bricks"))
            for y in range(1, h2 + 1):
                if ex or ez:
                    corner = ex and ez
                    pil = (ez and (x - x0) % 4 == 0) or (ex and (z - z0) % 4 == 0)
                    if corner or pil:
                        spec = IRON if y not in (h1, h2) else BRASS
                    elif y in (h1,):
                        spec = BRASS
                    elif y <= 1:
                        spec = DARK2
                    elif (2 <= y <= 5 or 9 <= y <= 12) and ((ez and (x - x0) % 4 == 2) or (ex and (z - z0) % 4 == 2)):
                        spec = "glass_pane"
                    else:
                        spec = wall_pal(x, y, z)
                    bp.set(x, y, z, spec)
                else:
                    bp.set(x, y, z, MAHOGANY if y == h1 else "air")
    # window heads and sills
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if (x - x0) % 4 == 2:
                for wy in (6, 13):
                    bp.set(x, wy, z, CREAM_TRIM)
                f = "north" if z == z0 else "south"
                for wy in (1, 8):
                    bp.set(x, wy, z + (-1 if z == z0 else 1), stair(CREAM_STAIRS, "south" if z == z0 else "north", "top"))
    # copper roof (ridge along x) with dormers and a cupola
    y = h2 + 1
    k = 0
    while z0 - 1 + k <= z1 + 1 - k:
        for x in range(x0 - 1, x1 + 2):
            if z0 - 1 + k == z1 + 1 - k:
                bp.set(x, y + k, z0 - 1 + k, OXI_SLAB + "[type=bottom,waterlogged=false]")
            else:
                bp.set(x, y + k, z0 - 1 + k, stair(OXI_STAIRS, "south"))
                bp.set(x, y + k, z1 + 1 - k, stair(OXI_STAIRS, "north"))
        for z in range(z0 + k, z1 - k + 1):
            for x in (x0, x1):
                bp.set(x, y + k, z, wall_pal(x, y + k, z))
        k += 1
    ridge = y + k - 1
    for x in range(x0 - 1, x1 + 2):
        if bp.get(x, ridge, (z0 + z1) // 2) is None:
            bp.set(x, ridge, (z0 + z1) // 2, OXI_CUT)
    # gable oculi
    for x in (x0, x1):
        bp.set(x, y + 3, (z0 + z1) // 2, "glass_pane")
        bp.set(x, y + 3, (z0 + z1) // 2 - 1, BRASS)
        bp.set(x, y + 3, (z0 + z1) // 2 + 1, BRASS)
    # cupola with a weather vane
    mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
    for yy in range(ridge, ridge + 4):
        for x in range(mx - 1, mx + 2):
            for z in range(mz - 1, mz + 2):
                edge = abs(x - mx) == 1 and abs(z - mz) == 1
                bp.set(x, yy, z, BRASS if edge else ("glass" if yy < ridge + 3 else BRASS))
    bp.set(mx, ridge + 4, mz, OXI_CUT)
    bp.set(mx, ridge + 5, mz, ROD)
    # doors: west to the observatory walk, east to the orrery, north to the courtyard
    for (x, z, f) in ((x0, (z0 + z1) // 2, "west"), (x1, 20, "east"), ((x0 + x1) // 2, z0, "north")):
        for y in range(1, 5):
            for u in (-1, 0, 1):
                xx, zz = (x, z + u) if f in ("west", "east") else (x + u, z)
                bp.set(xx, y, zz, "air")
        for u in (-1, 0, 1):
            xx, zz = (x, z + u) if f in ("west", "east") else (x + u, z)
            bp.set(xx, 5, zz, BRASS)
    # ground floor library: shelves in aisles, reading desks, chandeliers
    for x in range(x0 + 2, x1 - 1, 3):
        for z in range(z0 + 2, z1 - 1):
            if abs(z - (z0 + z1) // 2) <= 1 or z == 20:
                continue
            if x in range((x0 + x1) // 2 - 1, (x0 + x1) // 2 + 2):
                continue
            for y in (1, 2, 3):
                bp.set(x, y, z, "bookshelf")
            bp.set(x, 4, z, MAHOGANY_SLAB + "[type=bottom,waterlogged=false]")
    for x in range(x0 + 3, x1 - 1, 6):
        hang_lamp(bp, x, h1 - 2, (z0 + z1) // 2, length=1, lamp=CHANDELIER)
    bp.set(x0 + 1, 1, z1 - 1, "lectern[facing=east,has_book=false,powered=false]")
    bp.chest(x1 - 1, 1, z1 - 1, "west", loot=LOOT + "observatory_study")
    # stair to the upper floor (north-east corner)
    for i in range(h1):                 # the last step sits in the upper floor: it lands level with it
        x = x1 - 1 - i
        bp.set(x, i + 1, z0 + 1, stair(MAHOGANY_STAIRS, "west"))
        for yy in range(i + 2, i + 5):
            if yy >= h1:
                bp.set(x, yy, z0 + 1, "air")
    # upper floor laboratory: long benches with brewing stands, a tesla model, an aether still
    yy = h1 + 1
    for x in range(x0 + 2, x1 - 1):
        if x % 3 == 0:
            continue
        bp.set(x, yy, z1 - 1, TABLE)
        if x % 3 == 1:
            bp.set(x, yy + 1, z1 - 1, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    for x in range(x0 + 2, x1 - 3, 4):
        bp.set(x, yy, z0 + 3, "cauldron")
        bp.set(x + 1, yy, z0 + 3, "amethyst_block")
        bp.set(x + 1, yy + 1, z0 + 3, "amethyst_cluster[facing=up,waterlogged=false]")
        bp.set(x + 2, yy, z0 + 3, AETHER)
    mini_coil(bp, (x0 + x1) // 2, yy, (z0 + z1) // 2)
    bp.chest(x0 + 1, yy, z1 - 1, "east", loot=LOOT + "observatory_lab")
    bp.set(x0 + 1, yy, z0 + 1, "enchanting_table")
    for x in range(x0 + 3, x1 - 1, 6):
        hang_lamp(bp, x, h2 - 2, (z0 + z1) // 2 + 3, length=1)


def walks(bp):
    """Covered walks: observatory to library, library to orrery."""
    # observatory south door (OBS_X, OBS_Z + OBS_R) to the library north side
    for z in range(OBS_Z + OBS_R + 1, LIB_Z0):
        for x in range(OBS_X - 2, OBS_X + 3):
            bp.set(x, 0, z, DARK)
            for y in range(1, 6):
                bp.set(x, y, z, "air")
        for x in (OBS_X - 2, OBS_X + 2):
            bp.set(x, 1, z, CREAM_TRIM if z % 2 else "diorite_wall")
        for x in range(OBS_X - 3, OBS_X + 4):
            bp.set(x, 6, z, stair(OXI_STAIRS, "east" if x < OBS_X else "west") if x != OBS_X else OXI_CUT)
        for x in (OBS_X - 2, OBS_X + 2):
            if z % 3 == 0:
                for y in range(1, 6):
                    bp.set(x, y, z, IRON if y < 5 else BRASS)
    for x in range(OBS_X - 2, OBS_X + 3):
        for y in range(1, 5):
            bp.set(x, y, LIB_Z0, "air")
    # library to orrery
    for x in range(LIB_X1 + 1, ORR_X - ORR_R + 1):
        for z in range(18, 23):
            bp.set(x, 0, z, DARK)
            for y in range(1, 6):
                bp.set(x, y, z, "air")
            bp.set(x, 6, z, stair(OXI_STAIRS, "south" if z < 20 else "north") if z != 20 else OXI_CUT)
        for z in (18, 22):
            bp.set(x, 1, z, CREAM_TRIM if x % 2 else "diorite_wall")


def courtyard(bp):
    """A sundial on a dais at the crossing of the walks, benches and lamp posts."""
    cx, cz = 2, 2
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.4:
                bp.set(x, 0, z, CREAM_TRIM if d > 3.5 else DARK)
            if 3.5 < d <= 4.4:
                bp.set(x, 1, z, "polished_diorite_slab[type=bottom,waterlogged=false]")
    for k in range(12):
        a = 2 * math.pi * k / 12
        x, z = cx + round(math.cos(a) * 3), cz + round(math.sin(a) * 3)
        bp.set(x, 0, z, "gold_block" if k % 3 == 0 else BRASS)
    for y in range(1, 4):
        bp.set(cx, y, cz, CREAM_TRIM if y < 3 else BRASS)
    for k in range(1, 4):
        bp.set(cx + k, 3 + k, cz, IRON_WALL if k < 3 else IRON)
    bp.set(cx, 4, cz, "lightning_rod[facing=east,powered=false,waterlogged=false]")
    for (x, z) in ((cx - 6, cz - 6), (cx + 6, cz - 6), (cx - 6, cz + 6), (cx + 6, cz + 6), (-2, 34), (2, 34),
                   (-10, -14), (10, -22), (-30, 16), (34, 6), (32, 34), (-34, -18)):
        if is_air(bp, x, 1, z) and bp.get(x, 0, z) is not None:
            lantern_post(bp, x, 0, z, h=4, top=EDISON, post="diorite_wall", base=CREAM_TRIM)
    for (x, z, f) in ((cx - 6, cz, "east"), (cx + 6, cz, "west")):
        for dz in (-1, 0, 1):
            bp.set(x, 1, z + dz, stair(DARK_STAIRS, f))
    # a small refractor on a tripod for visitors
    tx, tz = -6, -14
    bp.set(tx, 1, tz, IRON_WALL)
    bp.set(tx, 2, tz, IRON)
    bp.set(tx + 1, 3, tz, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    bp.set(tx, 3, tz, COPPER)


def greenhouse(bp):
    """The botanist's glasshouse: iron ribs, a glass gable roof, beds of herbs and flowers, a little fountain."""
    x0, x1, z0, z1 = -33, -17, 14, 24
    h = 5
    mz = (z0 + z1) // 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            ex, ez = x in (x0, x1), z in (z0, z1)
            rib = (x - x0) % 4 == 0
            bp.set(x, 0, z, DARK2 if (ex or ez) else ("moss_block" if abs(z - mz) > 1 else "polished_andesite"))
            for y in range(1, h + 1):
                if ex or ez:
                    bp.set(x, y, z, IRON if (rib and ez) or (ex and (z - z0) % 4 == 0) or y == h or y == 1 and False
                           else (DARK2 if y == 1 else "glass_pane"))
                else:
                    bp.set(x, y, z, "air")
    # glass gable roof on iron rafters
    half = (z1 - z0) // 2
    for k in range(half + 1):
        y = h + 1 + k
        for x in range(x0, x1 + 1):
            for z in (z0 + k, z1 - k):
                rib = (x - x0) % 4 == 0
                bp.set(x, y, z, IRON if rib or x in (x0, x1) else "glass")
            if x in (x0, x1):
                for z in range(z0 + k + 1, z1 - k):
                    bp.set(x, y, z, "glass")
    for x in range(x0, x1 + 1):
        bp.set(x, h + 1 + half, mz, BRASS if (x - x0) % 4 == 0 else IRON)
    # beds
    plants = ["allium", "azure_bluet", "cornflower", "lily_of_the_valley", "oxeye_daisy", "red_tulip", "fern",
              "blue_orchid", "torchflower"]
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if abs(z - mz) <= 1:
                continue
            if hash01(x, z, 31) < 0.55:
                bp.set(x, 1, z, plants[int(hash01(x, z, 32) * len(plants))])
            elif hash01(x, z, 33) < 0.25:
                bp.set(x, 1, z, "flowering_azalea" if hash01(x, z, 34) < 0.5 else "azalea")
    fx = (x0 + x1) // 2
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(fx + dx, 0, mz + dz, CREAM_TRIM)
    bp.set(fx, 1, mz, "water_cauldron[level=3]")
    bp.set(fx, 1, mz - 1, "air")
    bp.set(fx, 1, mz + 1, "air")
    for x in (x0 + 4, x1 - 4):
        hang_lamp(bp, x, h - 1, mz, length=0)
    # doors on both gable ends
    for x in (x0, x1):
        for y in (1, 2, 3):
            bp.set(x, y, mz, "air")
    bp.chest(x1 - 1, 1, z1 - 1, "west", loot=LOOT + "observatory_study")


def open_ground(bp, x, z, r, height=10):
    """True when the terrace around (x, z) is bare paving with nothing built above it."""
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            g = bp.get(x + dx, 0, z + dz) or ""
            if not g.endswith(("stone_bricks", "polished_andesite", "polished_deepslate")):
                return False
            for y in range(1, height):
                if bp.get(x + dx, y, z + dz) not in ("minecraft:air", None):
                    return False
    return True


def planter(bp, x, z, tree=True):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = max(abs(dx), abs(dz)) == 2
            bp.set(x + dx, 0, z + dz, DARK2 if edge else "moss_block")
            if edge:
                bp.set(x + dx, 1, z + dz, DARK_SLAB + "[type=bottom,waterlogged=false]")
            elif (dx or dz) and hash01(x + dx, z + dz, 3) < 0.5:
                bp.set(x + dx, 1, z + dz, "fern" if hash01(x + dx, z + dz, 4) < 0.5 else "lily_of_the_valley")
    if tree:
        spruce(bp, x, 1, z, h=7 + int(hash01(x, z, 9) * 4))


def lightning_garden(bp):
    """Four pylons around the Tesla tower, each a small coil wired to the tower with copper chains."""
    cx, cz = TES_X, TES_Z
    for (dx, dz) in ((-12, -4), (12, -4), (-12, 10), (12, 10)):
        x, z = cx + dx, cz + dz
        if math.hypot(x, z - 2) > edge_r(x, z) - 3:
            continue
        for ddx in (-1, 0, 1):
            for ddz in (-1, 0, 1):
                bp.set(x + ddx, 0, z + ddz, DARK2)
                bp.set(x + ddx, 1, z + ddz, DARK_SLAB + "[type=bottom,waterlogged=false]" if ddx or ddz else IRON)
        for y in range(2, 7):
            bp.set(x, y, z, IRON if y % 2 else CU)
        mini_coil(bp, x, 7, z)


def condenser(bp):
    """The aether condenser: a great glass sphere on a brass stand, glowing at its heart, piped to the Tesla tower."""
    cx, cz, cy, r = 3, -15, 8, 4
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            d = math.hypot(x - cx, z - cz)
            if d <= 3.4:
                bp.set(x, 0, z, DARK2 if d > 2.4 else BRASS)
            if 2.4 < d <= 3.4:
                bp.set(x, 1, z, DARK_SLAB + "[type=bottom,waterlogged=false]")
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        for y in range(1, cy - r + 2):
            bp.set(cx + dx, y, cz + dz, IRON if y % 2 else BRASS)
    for x in range(cx - r - 1, cx + r + 2):
        for y in range(cy - r - 1, cy + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if r - 0.6 < d <= r + 0.4:
                    band = abs(y - cy) == 0
                    bp.set(x, y, z, BRASS if band else "light_blue_stained_glass")
                elif d <= r - 0.6:
                    bp.set(x, y, z, "air")
    for y in range(cy - r + 1, cy + 3):
        bp.set(cx, y, cz, AETHER if y != cy else "sea_lantern")
    for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        bp.set(cx + dx, cy + 1, cz + dz, "end_rod[facing=%s]" % f)
    bp.set(cx, cy + r + 1, cz, BRASS)
    bp.set(cx, cy + r + 2, cz, ROD)
    # pipe to the generator hall
    for x in range(cx + r + 1, TES_X - 7):
        bp.set(x, 2, cz, W + "copper_pipe[axis=x]")
        if x % 4 == 0:
            bp.set(x, 1, cz, IRON_WALL)
    bp.set(cx + r, 2, cz, BRASS)
    bp.set(cx + r, 1, cz, IRON)


def weather_mast(bp):
    """A slender meteorological mast: anemometer cups, wind vane and a signal lamp."""
    x, z = -4, -27
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(x + dx, 0, z + dz, DARK)
            bp.set(x + dx, 1, z + dz, DARK_STAIRS + "[facing=%s,half=bottom,shape=straight,waterlogged=false]"
                   % out_facing(-dx, -dz) if (dx or dz) and not (dx and dz) else DARK_SLAB + "[type=bottom,waterlogged=false]")
    for y in range(1, 22):
        bp.set(x, y, z, IRON if y % 5 else BRASS)
    for y in (7, 14):
        for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            bp.set(x + dx, y, z + dz, "iron_trapdoor[facing=%s,half=bottom,open=true,powered=false,waterlogged=false]" % f)
    for (dx, dz) in ((1, 0), (2, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + dx, 22, z + dz, "iron_chain[axis=%s,waterlogged=false]" % ("x" if dx else "z"))
    bp.set(x, 22, z, BRASS)
    bp.set(x + 3, 22, z, "iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    bp.set(x, 23, z, EDISON)
    bp.set(x, 24, z, ROD)


def campus(bp):
    crag(bp)
    terrace(bp)
    grand_stair(bp)
    walks(bp)
    courtyard(bp)
    observatory(bp)
    library(bp)
    orrery(bp)
    tesla(bp)
    greenhouse(bp)
    condenser(bp)
    lightning_garden(bp)
    weather_mast(bp)
    for (x, z) in ((-8, -6), (12, -4), (-4, 30), (6, 31), (-36, 2), (34, -2), (-24, -26), (8, -30), (30, 36)):
        if open_ground(bp, x, z, 3) and math.hypot(x, z - 2) < edge_r(x, z) - 4:
            planter(bp, x, z, tree=(x + z) % 2 == 0)
    # the fellows of the observatory: astronomers, librarians, an electrician
    lib = ((LIB_X0, -10, LIB_Z0), (LIB_X1, 40, LIB_Z1))
    INT.populate(bp, [("librarian", 3), "librarian"], region=lib, seed=1)
    INT.decorate(bp, "library", seed=1, region=lib)
    INT.populate(bp, [("cartographer", 3), "toolsmith", "cleric"], seed=2)
    INT.decorate(bp, "steampunk", seed=2)


register(StructureDef(
    "tesla_observatory", "overworld",
    ["#minecraft:is_mountain", "windswept_hills", "windswept_gravelly_hills", "windswept_forest"],
    [Piece("campus", campus)],
    spacing=64, separation=24, adaptation="beard_thin", processors="none", max_distance=116,
    peaceful=True,
    title_fr="Observatoire Tesla", title_en="Tesla Observatory"))
