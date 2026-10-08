"""The Starfall Library (La Bibliothèque de la chute d'étoile): a floating archive ~170 across over the outer islands of
the End. A spindle tower of purpur and brass 125 high stands on a rock island; three ring-shaped reading galleries
orbit it at three heights, held by chain-and-end-rod spokes like the rings of an astrolabe; a meteorite lies wedged in
its south-east flank, having torn through the middle gallery and cracked the map room and the stacks open. Colossal
tier (tools/BUILDING.md §1, §12 concept 19, §10 legacy-dungeon template, §15), steampunk accents (brass catwalks,
railings, a pneumatic-tube lift, gauges).

Silhouette (one noun phrase, §15.1): a stepped purpur spindle with a gilded lens dome and a needle hung with armillary
rings, girdled by three floating rings of shrinking radius, a dark boulder lodged in its side.

Layout, plaza y = 0 (feet 1), x east, z south, the tower axis at (0, 0); angles in degrees from +x toward +z.
Tower profile (outer radius): plinth 26 (y -1..14, the map room), body 22 (y 15..63: the stacks and the scriptorium),
upper drum 17 (y 64..92: the upper hall and the observatory), a ribbed glass dome to y ~105, a needle to ~126.
Rings: R1 r 58 feet 16 (whole), R2 r 46 feet 40 (broken: the arc 200..337), R3 r 34 feet 65 (whole).
  * arrival: the islet at (-17, 95) (waystone, pilgrims' camp, ruined gateway framing the tower); the low bridge to
    the plaza and the great door (a 7 x 13 brass portal with a wicket, the porch the compression); the side bridge
    climbs to R1's gatehouse (side route, §10.1) and the west or north spoke into the stacks;
  * the map room (feet 1, 49 across, 13 high): a giant floor star-chart round a glass oculus over the crater chamber,
    the meteorite's face breaking in from the south-east; two curved stairs up to the stacks;
  * the stacks (hub, feet 16): bookshelf canyons 30 high with rolling ladders and two catwalks (feet 28, 40), the
    second waystone; a stair winds up the tower wall past both catwalks to the scriptorium; from catwalk 40 an iron
    door opens onto R2 from the ring side only (shortcut back);
  * the copyists' scriptorium (feet 53), a stair onto the roof terrace (feet 65, vista), the upper hall (the
    celestial index, an armillary sphere, the third waystone), a stair up to the lens observatory (feet 81, the
    great telescope under the dome); its balcony starts a ramp that curls down round the tower to R3;
  * R3 -> a second hanging ramp down to R2 -> the broken gallery: floating open books step down across the gap
    (a brass catch basin hangs under them, with a ladder back up) onto the meteorite's back;
  * a corkscrew fissure inside the meteorite spirals down 36 blocks, a tunnel leads under the plaza to the site of
    grace, a narrow stair (compression) to the mist and the crater chamber: the boss arena under the tower (radius
    17, a dome 18 high, the oculus overhead); west, the sealed forbidden-stacks vault and its pneumatic-tube lift
    (a bubble column) up to a booth in the map room whose iron door opens from inside only (the shortcut back).
Loot gradient (§15.6): camp, map room, R1 tier 1; stacks, scriptorium, upper hall, rings 2; observatory and the
meteorite geode 2-3; the vault 3.
Height budget: the needle tops out ~126 above the plaza; the island keel reaches ~40 below it.
"""
import math

from ..arch import Palette, slab, stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, GAUGE, GEAR, HANG_LAMP, PIPES, TABLE,
                       TREAD, TREAD_SLAB, W, hash01, hash3, out_facing, vnoise)
from ..parts import LOOT, MOB, MOD
from .end import (ESB, ESB_SL, ESB_ST, ESB_WA, FROG, OUTER_END, PUR, PUR_P, PUR_SL, PUR_ST, ROD_DOWN, ROD_UP, STAR,
                  VB, VB_SL, VB_ST, VB_WA, brazier, build_rock, disk_pts, face_in, hang_star, ring3d, rock_lobe,
                  tube)

# the library's own guardian: the Star-Eater Curator, in the crater chamber (entity/boss/StarCurator.java)
BOSS = "brasshaven:star_curator"
MOB_ACOLYTE = W + "void_acolyte"
MOB_STALKER = MOB["void_stalker"]

AIR = "minecraft:air"
GOLD = "gold_block"
OBS = "obsidian"
CRY = "crying_obsidian"
PBB = "polished_blackstone_bricks"
SHELF = "bookshelf"
RAIL = W + "brass_railing"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
WATER = "water[level=0]"

# ------------------------------------------------------------------ dimensions
F_STACKS, F_CAT1, F_CAT2, F_SCRIPT, F_TERR, F_OBS = 16, 28, 40, 53, 65, 81
R1, R2, R3 = 58, 46, 34
HW1, HW2, HW3 = 4, 4, 3
F_R1, F_R2, F_R3 = 16, 40, 65
GH = 7                                   # gallery height (feet .. feet + 6, roof at feet + 7)
F_ARENA, F_GRACE = -22, -8
ARENA_R = 17.4
M = (23, 17, 23)                         # the meteorite's centre
M_R, M_RY = 16.0, 15.0
ISLET = (-17, 95)
F_ISLET = 3
GRACE = (4, 42)
VAULT = (-30, -6, -20, 6)                # x0, z0, x1, z1 of the forbidden stacks
LIFT = (-23, -3)                         # the pneumatic tube's column
OBS_DOOR = 60                            # the observatory balcony (angle)
R2_ARC = (200.0, 337.0)

# ------------------------------------------------------------------ materials
PLINTH = Palette({VB: 6, PBB: 2, OBS: 1}, seed=1901, scale=2.6)
BODY = Palette({PUR: 7, PUR_P: 2, ESB: 1}, seed=1902, scale=2.4)
UPPER = Palette({PUR: 5, ESB: 3, PUR_P: 1}, seed=1903, scale=2.2)
PAVE = Palette({ESB: 8, "end_stone": 1, PUR: 1}, seed=1904, scale=1.8)
KEEL = Palette({OBS: 5, CRY: 1, VB: 3}, seed=1905, scale=2.6)
CRUST = Palette({"blackstone": 5, "basalt[axis=y]": 3, "magma_block": 1, OBS: 1}, seed=1906, scale=1.7)
CORE = Palette({OBS: 4, CRY: 2, "raw_iron_block": 1, "blackstone": 2, "gilded_blackstone": 1}, seed=1907,
               scale=2.0)
CRATER = Palette({OBS: 5, CRY: 2, "blackstone": 3, "tuff": 1}, seed=1908, scale=2.2)
COVERS = ("crimson", "warped", "dark_oak", "mangrove", "cherry", "spruce")


# ------------------------------------------------------------------ small helpers
def ang(x, z):
    return math.degrees(math.atan2(z, x)) % 360.0


def polar(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def in_arc(a, a0, a1):
    """a (deg) within the arc a0 -> a1 going with increasing angle (a1 may exceed 360)."""
    return (a - a0) % 360.0 <= (a1 - a0) + 1e-9


def q2(s):
    return round(s * 2) / 2.0


def empty(bp, x, y, z):
    b = bp.get(x, y, z)
    return b is None or b == AIR


def air(bp, x0, y0, z0, x1, y1, z1):
    bp.fill(x0, y0, z0, x1, y1, z1, "air")


def surface(bp, x, z, s, full, half, under=None):
    """Walking surface at feet height s (multiple of 0.5): a full block, or a bottom slab on `under`. Returns the y
    of the top block."""
    n = math.floor(s)
    if s - n > 0.25:
        bp.set(x, n, z, slab(half))
        bp.set(x, n - 1, z, under or full)
        return n
    bp.set(x, n - 1, z, full)
    return n - 1


def railing(bp, x, y, z, facing):
    bp.set(x, y, z, f"{RAIL}[facing={facing}]")


def lectern(bp, x, y, z, facing):
    bp.set(x, y, z, f"lectern[facing={facing},has_book=false,powered=false]")


def candle(bp, x, y, z, n=3, color="white"):
    bp.set(x, y, z, f"{color}_candle[candles={n},lit=true,waterlogged=false]")


def chiseled(facing, seed):
    bits = [hash01(seed, k, 1931) < 0.6 for k in range(6)]
    props = ",".join(f"slot_{k}_occupied={'true' if b else 'false'}" for k, b in enumerate(bits))
    return f"chiseled_bookshelf[facing={facing},{props}]"


def shelf_block(x, y, z, facing):
    h = hash3(x, y, z, 1932)
    return chiseled(facing, x * 31 + y * 7 + z) if h < 0.14 else SHELF


def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def iron_door(bp, x, y, z, facing, hinge="left"):
    for half, dy in (("lower", 0), ("upper", 1)):
        bp.set(x, y + dy, z, f"iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def hang(bp, x, y_ceiling, z, n, lamp):
    """A chain of n under the ceiling block at y_ceiling, the lamp under it."""
    bp.chain(x, y_ceiling - n, z, y_ceiling - 1)
    bp.set(x, y_ceiling - n - 1, z, lamp)


def line3(bp, p0, p1, kind):
    """A 3D line of chains (kind 'chain') or end rods ('rod'), oriented along its dominant axis."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    n = int(max(abs(dx), abs(dy), abs(dz)) * 1.2) + 1
    if kind == "chain":
        axis = "y" if abs(dy) >= max(abs(dx), abs(dz)) else ("x" if abs(dx) >= abs(dz) else "z")
        spec = f"iron_chain[axis={axis},waterlogged=false]"
    else:
        spec = f"end_rod[facing={out_facing(dx, dz)}]"
    seen = set()
    for i in range(n + 1):
        t = i / n
        p = (round(x0 + dx * t), round(y0 + dy * t), round(z0 + dz * t))
        if p in seen:
            continue
        seen.add(p)
        if empty(bp, *p):
            bp.set(*p, spec)


# ------------------------------------------------------------------ helices (stairs winding round the axis)
def helix(bp, segs, rin, rout, floor_y, full=PUR, half=PUR_SL, fill=ESB, rail=True, cx=0, cz=0, clear=4):
    """Stair winding round (cx, cz) on the annulus rin < d <= rout. segs: [(a0, a1, s0, s1)] with a1 > a0 (degrees,
    may pass 360); s goes linearly from s0 to s1 (feet). Treads are slabs or full blocks (slope <= 0.5 per block).
    Solid fill under treads that are close to the floor (no crawl gaps), a slab support elsewhere, air above, a brass
    railing on the inner edge where it is high. Returns {(x, z): s}."""
    cells = {}
    R = int(rout) + 2
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if not (rin < d <= rout):
                continue
            a = ang(x - cx, z - cz)
            for (a0, a1, s0, s1) in segs:
                if in_arc(a, a0, a1):
                    t = ((a - a0) % 360.0) / (a1 - a0)
                    cells[(x, z)] = q2(s0 + (s1 - s0) * t)
                    break
    for (x, z), s in cells.items():
        y = surface(bp, x, z, s, full, half, under=fill)
        for c in range(1, clear + 1):
            bp.set(x, y + c, z, "air")
        if s - floor_y <= 4.0:
            for yy in range(floor_y - 1, y - (1 if s - math.floor(s) > 0.25 else 0)):
                bp.set(x, yy, z, fill)
        elif bp.get(x, y - 1, z) in (None, AIR):
            bp.set(x, y - 1, z, slab(half, "top"))
    if rail:
        for (x, z), s in cells.items():
            d = math.hypot(x - cx, z - cz)
            if d <= rin + 1.0 and s - floor_y > 1.5:
                y = math.floor(s) if s - math.floor(s) > 0.25 else math.floor(s)
                railing(bp, x, y if s - math.floor(s) > 0.25 else math.floor(s), z, out_facing(cx - x, cz - z))
    return cells


# ------------------------------------------------------------------ walkways (bridges, ramps)
def walkway(bp, pts, width=3, style="stone", rise=0.0, rails=True):
    """A walkway along a polyline of (x, feet s, z) points, quantised to half blocks (slope <= 0.5 per block).
    style: stone (purpur deck, wall rails, keel), brass (diamond plate, brass railings, chains up), rock (a tunnel
    floor: no rails, no keel). Returns {(x, z): s}."""
    hw = width // 2
    deck_c, rail_c = {}, {}
    total = sum(math.hypot(b[0] - a[0], b[2] - a[2]) for a, b in zip(pts, pts[1:])) or 1.0
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        if L < 1e-6:
            continue
        ux, uz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
        px, pz = -uz, ux
        n = int(L * 3) + 1
        if abs(b[1] - a[1]) / L > 0.51:
            print(f"starfall_library: walkway segment {a}->{b} too steep ({abs(b[1] - a[1]) / L:.2f})")
        for i in range(n + 1):
            t = i / n
            cx, cz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            tt = (acc + L * t) / total
            s = a[1] + (b[1] - a[1]) * t + rise * math.sin(math.pi * tt)
            for w in range(-hw - 1, hw + 2):
                X, Z = round(cx + px * w), round(cz + pz * w)
                tgt = rail_c if abs(w) == hw + 1 else deck_c
                tgt.setdefault((X, Z), []).append((abs(w), s, tt))
        acc += L
    out = {}
    for (X, Z), ss in deck_c.items():
        ss.sort()
        s = q2(ss[0][1])
        out[(X, Z)] = s
        mid = ss[0][0] == 0
        if style == "brass":
            full, half, under = (BRASS if mid else TREAD), (BRASS_SLAB if mid else TREAD_SLAB), BRASS
        elif style == "rock":
            full, half, under = ("blackstone" if mid else "polished_blackstone"), "polished_blackstone_slab", \
                "blackstone"
        else:
            full, half, under = (PUR if mid else ESB), (PUR_SL if mid else ESB_SL), VB
        y = surface(bp, X, Z, s, full, half, under=under)
        for c in range(1, 4):
            bp.set(X, y + c, Z, "air")
        if style != "rock" and bp.get(X, y - 1, Z) in (None, AIR):
            bp.set(X, y - 1, Z, slab(VB_SL if style == "stone" else BRASS_SLAB, "top"))
    if rails and style != "rock":
        k = 0
        for (X, Z), ss in sorted(rail_c.items(), key=lambda kv: min(v[2] for v in kv[1])):
            if (X, Z) in deck_c:
                continue
            ss.sort()
            s = q2(ss[0][1])
            top = math.ceil(s - 0.01)
            if not empty(bp, X, top - 1, Z):
                continue
            k += 1
            if style == "brass":
                bp.set(X, top - 1, Z, slab(BRASS_SLAB, "top"))
                nb = min(((x2, z2) for (x2, z2) in ((X + 1, Z), (X - 1, Z), (X, Z + 1), (X, Z - 1))
                          if (x2, z2) in deck_c), default=None)
                f = out_facing(X - nb[0], Z - nb[1]) if nb else "north"
                railing(bp, X, top, Z, f)
                if k % 8 == 0:
                    bp.set(X, top, Z, BRASS)
                    bp.set(X, top + 1, Z, LANT)
            else:
                bp.set(X, top - 1, Z, VB)
                bp.set(X, top - 2, Z, slab(VB_SL, "top"))
                if k % 7 == 0:
                    bp.set(X, top, Z, PUR_P)
                    bp.set(X, top + 1, Z, ROD_UP)
                else:
                    bp.set(X, top, Z, ESB_WA)
    if style == "stone":
        for (X, Z), s in out.items():
            if deck_c[(X, Z)][0][0] == 0 and empty(bp, X, math.floor(s) - 3, Z):
                bp.set(X, math.floor(s) - 2, Z, VB)
                if hash01(X, Z, 1940) < 0.12:
                    bp.set(X, math.floor(s) - 3, Z, ROD_DOWN)
    return out


# ------------------------------------------------------------------ the island
def island_cols():
    """{(x, z): (bottom, top)}: the rock under the plaza, deep under the tower, an organic rim."""
    cols = {}
    cx, cz, rx, rz = 4, 10, 46.0, 48.0
    for x in range(-50, 58):
        for z in range(-46, 66):
            dx, dz = (x - cx) / rx, (z - cz) / rz
            th = math.atan2(dz, dx)
            rim = 1 + 0.07 * math.sin(3 * th + 1.1) + 0.05 * math.sin(5 * th + 0.4) + 0.03 * math.sin(11 * th + 2.0)
            e = math.hypot(dx, dz) / rim
            if e > 1:
                continue
            top = 0 - (1 if e > 0.93 else 0) - (1 if e > 0.985 else 0)
            dep = 6 + 28 * max(0.0, 1 - e * e) ** 0.8 * (0.8 + 0.4 * vnoise(x, z, 9.0, 1941))
            # a keel spike under the tower and two lesser ones
            for (sx, sz, sr, sl) in ((0, 0, 14, 16), (18, 30, 7, 9), (-22, -14, 6, 8)):
                dd = math.hypot(x - sx, z - sz)
                if dd < sr:
                    dep += sl * (1 - dd / sr) ** 1.6
            cols[(x, z)] = (round(top - dep), top)
    return cols


def island(bp):
    cols = island_cols()
    build_rock(bp, cols, 1942, surface="end_stone")
    return cols


def plaza(bp, cols):
    """Paving round the tower: radial purpur lines, a gold ring, braziers, a low wall at the edge with gaps."""
    for (x, z), (b, t) in cols.items():
        d = math.hypot(x, z)
        if d > 38 or t < 0:
            continue
        a = ang(x, z)
        if 29.5 < d <= 30.5:
            spec = GOLD if (round(a) % 15) < 3 else PUR
        elif (round(a) % 30) < 2 and d > 27:
            spec = PUR
        elif d > 34.5:
            spec = ESB
        else:
            spec = PAVE.pick(x, 0, z)
        bp.set(x, 0, z, spec)
        bp.set(x, -1, z, ESB)
    # braziers on the gold ring, the edge wall (gaps at the bridge and toward the crater)
    for k in range(12):
        a = 15 + 30 * k
        if 30 < a < 70 or 90 < a < 110:
            continue
        x, z = polar(32, a)
        brazier(bp, round(x), 1, round(z), h=2)
    for (x, z), (b, t) in cols.items():
        d = math.hypot(x, z)
        a = ang(x, z)
        if 36.5 < d <= 37.5 and t == 0:
            if 95 <= a <= 112 or 20 <= a <= 70:
                continue
            bp.set(x, 1, z, PUR_P if (round(a) % 12) < 2 else ESB_WA)


# ------------------------------------------------------------------ the tower shell
def r_out(y):
    if y <= 2:
        return 27
    if y <= 14:
        return 26
    if y <= 63:
        return 22
    if y <= 92:
        return 17
    return None


def tower_shell(bp):
    """Plinth, body, upper drum: masonry shells, floors, string courses, pilasters, windows, a lining of bookshelves
    on the inner face of the rooms."""
    floors = {-1: ESB, 14: PUR, 15: PUR, 51: PUR, 52: "dark_oak_planks", 63: PUR, 64: PUR, 78: PUR, 79: PUR,
              80: VB}
    for y in range(-1, 93):
        ro = r_out(y)
        ri = ro - 2
        for x in range(-ro - 1, ro + 2):
            for z in range(-ro - 1, ro + 2):
                d = math.hypot(x, z)
                if d > ro + 0.4:
                    continue
                a = ang(x, z)
                if d > ri + 0.4:
                    # the wall
                    if y <= 14:
                        spec = PLINTH.pick(x, y, z)
                        if y in (0, 13):
                            spec = GOLD if y == 13 and (round(a) % 10) < 2 else PUR
                    elif y <= 63:
                        spec = BODY.pick(x, y, z)
                        if y in (30, 46, 62):
                            spec = BRASS
                    else:
                        spec = UPPER.pick(x, y, z)
                        if y in (79, 92):
                            spec = BRASS
                    # the inner face of the rooms is lined with books
                    inner = d <= ri + 1.4
                    room = (1 <= y <= 13) or (16 <= y <= 50) or (53 <= y <= 62) or (65 <= y <= 77)
                    if inner and room and spec not in (BRASS, GOLD):
                        spec = shelf_block(x, y, z, face_in(x, z, 0, 0))
                    bp.set(x, y, z, spec)
                else:
                    if y in floors:
                        spec = floors[y]
                        if y == 15 and d > ri - 0.6:
                            spec = PUR
                        bp.set(x, y, z, spec)
                    elif y == 0:
                        bp.set(x, y, z, VB)            # the map room floor (the star chart is laid later)
                    else:
                        bp.set(x, y, z, "air")
    # plinth: battered foot, roof terrace (feet 16) with a parapet, cornice
    for x in range(-28, 29):
        for z in range(-28, 29):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 22.4 < d <= 26.4:
                bp.set(x, 15, z, PAVE.pick(x, 15, z) if d < 25.4 else PUR)
                bp.set(x, 14, z, PLINTH.pick(x, 14, z))
                if d > 25.4:
                    bp.set(x, 16, z, PUR_P if (round(a) % 15) < 2 else ESB_WA)
            if 26.4 < d <= 27.4:
                bp.set(x, 14, z, stair(PUR_ST, out_facing(x, z), "top"))
                if d <= 27.4 and hash01(x, z, 1950) < 0.0:
                    pass
            if 27.4 < d <= 28.4:
                bp.set(x, -1, z, stair(VB_ST, face_in(x, z, 0, 0)))
    # pilasters: 16 round the plinth, 16 on the body, 12 on the upper drum
    for k in range(16):
        a = 11.25 + 22.5 * k
        if 80 < a < 100 or 30 < a < 62:
            continue
        x, z = polar(27.2, a)
        x, z = round(x), round(z)
        for y in range(0, 14):
            bp.set(x, y, z, PUR_P if 1 <= y <= 12 else GOLD)
        bp.set(x, 14, z, stair(PUR_ST, out_facing(x, z), "top"))
    for k in range(16):
        a = 22.5 * k
        if 30 < a < 62:
            continue
        x, z = polar(23.0, a)
        x, z = round(x), round(z)
        for y in range(16, 64):
            bp.set(x, y, z, BRASS if y in (30, 46, 62) else PUR_P)
        bp.set(x, 64, z, stair(PUR_ST, out_facing(x, z), "bottom"))
    for k in range(12):
        a = 15 + 30 * k
        x, z = polar(17.9, a)
        x, z = round(x), round(z)
        for y in range(65, 93):
            bp.set(x, y, z, BRASS if y in (79, 92) else PUR_P)
        bp.set(x, 93, z, GOLD)
        bp.set(x, 94, z, ROD_UP)
    # body cornice under the terrace
    for x in range(-24, 25):
        for z in range(-24, 25):
            d = math.hypot(x, z)
            if 22.4 < d <= 23.4:
                bp.set(x, 63, z, stair(PUR_ST, out_facing(x, z), "top"))
    windows(bp)


def _win(bp, a, r0, r1, y0, y1, half_w, glass, sill=True, hood=None):
    """A window through a round wall: cells between radii r0..r1 within half_w (blocks) of the ray at angle a."""
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    for x in range(-30, 31):
        for z in range(-30, 31):
            d = math.hypot(x, z)
            if not (r0 < d <= r1):
                continue
            t = x * ux + z * uz
            off = abs(-x * uz + z * ux)
            if t <= 0 or off > half_w:
                continue
            for y in range(y0, y1 + 1):
                bp.set(x, y, z, glass)
    if sill:
        sx, sz = polar(r1 + 0.6, a)
        bp.set(round(sx), y0 - 1, round(sz), slab(ESB_SL, "top"))
    if hood:
        sx, sz = polar(r1 + 0.6, a)
        bp.set(round(sx), y1 + 1, round(sz), stair(hood, face_in(round(sx), round(sz), 0, 0), "top"))


def windows(bp):
    gl = "purple_stained_glass_pane"
    # map room: 2 x 5 at y 5..9, skip the door bay and the meteorite
    for k in range(16):
        a = 22.5 * k
        if 70 < a < 110 or 20 < a < 72:
            continue
        _win(bp, a, 24.4, 26.4, 5, 9, 1.0, gl, hood=PUR_ST)
    # stacks: tall lancets 3 x 12 and a clerestory row
    for k in range(16):
        a = 11.25 + 22.5 * k
        if 25 < a < 66:
            continue
        _win(bp, a, 20.4, 22.4, 18, 28, 1.2, gl, hood=PUR_ST)
        _win(bp, a, 20.4, 22.4, 34, 43, 1.2, gl, hood=PUR_ST)
    # scriptorium: 2 x 5
    for k in range(16):
        a = 11.25 + 22.5 * k
        _win(bp, a, 20.4, 22.4, 55, 59, 1.0, "glass_pane", hood=PUR_ST)
    # upper hall 2 x 6, observatory 2 x 7
    for k in range(12):
        a = 30 * k
        if abs(((a - OBS_DOOR + 180) % 360) - 180) < 20:
            continue
        _win(bp, a, 15.4, 17.4, 68, 73, 1.0, gl)
        _win(bp, a, 15.4, 17.4, 83, 89, 1.0, "glass_pane")


def door_cut(bp, a, r0, r1, y, w=3, h=4, frame=PUR_P, lintel=GOLD):
    """A doorway along the ray at angle a through radii r0..r1, feet y, framed on the outside."""
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    px, pz = -uz, ux
    hw = w // 2
    t = r0
    while t <= r1:
        for o in range(-hw, hw + 1):
            x, z = round(ux * t + px * o), round(uz * t + pz * o)
            for yy in range(y, y + h):
                bp.set(x, yy, z, "air")
        t += 0.3
    for o in (-hw - 1, hw + 1):
        x, z = round(ux * r1 + px * o), round(uz * r1 + pz * o)
        for yy in range(y, y + h):
            bp.set(x, yy, z, frame)
        bp.set(x, y + h, z, lintel)
    for o in range(-hw, hw + 1):
        x, z = round(ux * r1 + px * o), round(uz * r1 + pz * o)
        bp.set(x, y + h, z, lintel if o == 0 else PUR)


def dome_and_needle(bp):
    """The ribbed lens dome (glass panels between gold ribs, a slit to the south-east) and the needle with its
    armillary rings."""
    for x in range(-18, 19):
        for z in range(-18, 19):
            for y in range(93, 107):
                d3 = math.sqrt(x * x + z * z + ((y - 92) * 17.0 / 13.0) ** 2)
                if d3 > 17.4:
                    continue
                a = ang(x, z)
                if d3 > 16.2:
                    rib = (round(a) % 30) < 4
                    slit = abs(((a - 45 + 180) % 360) - 180) * math.hypot(x, z) * 0.0175 < 1.6 and y < 103
                    if slit:
                        bp.set(x, y, z, "air")
                    elif rib or y == 93:
                        bp.set(x, y, z, GOLD if rib else BRASS)
                    else:
                        bp.set(x, y, z, "purple_stained_glass" if hash3(x, y, z, 1951) < 0.75 else "glass")
                else:
                    bp.set(x, y, z, "air")
    top = 92 + 13
    for y in range(top - 1, top + 8):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(dx, y, dz, GOLD if (y - top) % 4 == 0 else (PUR_P if abs(dx) + abs(dz) == 2 else PUR))
    for y in range(top + 8, top + 21):
        bp.set(0, y, 0, GOLD if y > top + 17 or y % 3 == 0 else PUR_P)
    bp.set(0, top + 21, 0, ROD_UP)
    # armillary rings round the needle
    c = (0, top + 9, 0)
    t1, t2 = math.radians(28), math.radians(-35)
    ring3d(bp, c, 6.5, (1, 0, 0), (0, math.sin(t1), math.cos(t1)), GOLD)
    ring3d(bp, c, 6.5, (0, 0, 1), (math.cos(t2), math.sin(t2), 0), BRASS)
    ring3d(bp, (0, top + 15, 0), 3.5, (1, 0, 0), (0, 0, 1), GOLD)
    for k in range(4):
        x, z = polar(6.5, 45 + 90 * k)
        bp.set(round(x), top + 9, round(z), ROD_UP)


# ------------------------------------------------------------------ the great door
def great_door(bp):
    """A porch south of the plinth: a pediment 26 high framing a brass portal 7 x 13 with a wicket; the passage
    behind it (5 wide, 5 high) is the compression before the map room."""
    X0, X1, Z0, Z1 = -9, 9, 24, 33
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            if math.hypot(x, z) <= 24.4:
                continue
            for y in range(0, 19):
                edge = x in (X0, X1) or z == Z1
                spec = PLINTH.pick(x, y, z) if not edge else (PUR_P if x in (X0, X1) else PLINTH.pick(x, y, z))
                if y in (13, 18):
                    spec = GOLD if y == 13 else PUR
                bp.set(x, y, z, spec)
            bp.set(x, -1, z, ESB)
    # pediment (stepped gable) and its gilded star
    for j in range(10):
        y = 19 + j
        for x in range(X0 + j, X1 - j + 1):
            for z in range(Z0 + 3, Z1 + 1):
                if math.hypot(x, z) <= 26.4:
                    continue
                edge = x in (X0 + j, X1 - j)
                bp.set(x, y, z, stair(PUR_ST, "east" if x == X0 + j else "west") if edge and j < 9 else PUR)
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(dx, 23 + dy, Z1 + 1, GOLD if (dx, dy) != (0, 0) else STAR)
    bp.set(0, 29, Z1 - 2, ROD_UP)
    # the portal recess: 7 wide, 13 high, brass leaves with a wicket 3 x 4
    for x in range(-3, 4):
        for y in range(1, 14):
            top = 14 - (1 if abs(x) == 3 else 0)
            if y >= top:
                continue
            leaf = BRASS if (y % 4) else GEAR
            bp.set(x, y, Z1, leaf)
            bp.set(x, y, Z1 + 1, "air")
    for x in (-4, 4):
        for y in range(0, 15):
            bp.set(x, y, Z1 + 1, PUR_P if y < 14 else GOLD)
    for x in range(-4, 5):
        bp.set(x, 14, Z1 + 1, GOLD if x == 0 else PUR)
        bp.set(x, 0, Z1 + 1, ESB)
        bp.set(x, 0, Z1 + 2, stair(ESB_ST, "north"))
    # the passage: wicket 3 x 4 in the leaves, then 5 x 5 through porch and plinth wall
    air(bp, -1, 1, Z1, 1, 4, Z1)
    for z in range(21, Z1):
        for x in range(-2, 3):
            for y in range(1, 6):
                bp.set(x, y, z, "air")
            bp.set(x, 0, z, PUR if x == 0 else ESB)
            bp.set(x, 6, z, PUR)
        for x in (-3, 3):
            for y in range(1, 6):
                if z % 3 == 0:
                    bp.set(x, y, z, PUR_P)
        if z % 3 == 0:
            bp.set(-2, 4, z, "end_rod[facing=east]")
            bp.set(2, 4, z, "end_rod[facing=west]")
    # lamps on the porch front
    for x in (-6, 6):
        bp.set(x, 6, Z1 + 1, slab(PUR_SL, "top"))
        bp.set(x, 7, Z1 + 1, STAR)
        bp.set(x, 8, Z1 + 1, ROD_UP)


# ------------------------------------------------------------------ the map room
CONSTELLATIONS = [
    [(-14, -6), (-10, -9), (-6, -8), (-3, -12), (1, -14)],
    [(6, -16), (9, -12), (13, -11), (15, -6)],
    [(-17, 6), (-13, 9), (-9, 8), (-8, 13), (-4, 16)],
    [(-4, 6), (-7, 4), (-9, 0), (-12, -2)],
    [(4, 9), (8, 12), (11, 17), (6, 19)],
]


def map_room(bp):
    """The giant floor star-chart (dark void bricks, gold rings and meridians, constellations of starlights joined by
    gold), the oculus over the crater chamber, two curved stairs up to the stacks, globes, lecterns and lamps."""
    R = 24.4
    for x in range(-25, 26):
        for z in range(-25, 26):
            d = math.hypot(x, z)
            if d > R:
                continue
            a = ang(x, z)
            if d <= 2.6:
                spec = "glass"
            elif d <= 3.6:
                spec = GOLD
            elif 8.5 < d <= 9.4 or 15.5 < d <= 16.4:
                spec = GOLD
            elif 21.6 < d <= 22.5:
                spec = PUR
            elif d > 22.5:
                spec = PUR if (round(a) % 10) < 3 else VB
            elif (round(a) % 30) < 2 and d > 3.6:
                spec = "purpur_block" if d < 21 else GOLD
            else:
                spec = VB if hash01(x, z, 1960) < 0.94 else (STAR if hash01(x, z, 1961) < 0.5 else FROG)
            bp.set(x, 0, z, spec)
    # the oculus shaft (down to the crater dome) is cut with the arena; the constellations
    for pts in CONSTELLATIONS:
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            n = max(abs(bx - ax), abs(bz - az))
            for i in range(n + 1):
                x, z = round(ax + (bx - ax) * i / n), round(az + (bz - az) * i / n)
                if bp.get(x, 0, z) not in ("minecraft:glass",):
                    bp.set(x, 0, z, "gold_block")
        for (x, z) in pts:
            bp.set(x, 0, z, STAR)
    # the ecliptic: a tilted ellipse of copper
    for i in range(240):
        t = 2 * math.pi * i / 240
        x, z = round(12.5 * math.cos(t) + 2), round(7.5 * math.sin(t) - 1)
        if math.hypot(x, z) > 3.6:
            bp.set(x, 0, z, "waxed_cut_copper")
    # the curved stairs up to the stacks (west and east), solid under them
    MAP_STAIRS.update(helix(bp, [(170, 262, 16, 1)], 17.0, 20.4, 1, full=PUR, half=PUR_SL,
                            fill=PLINTH.pick(0, 0, 0), rail=False))
    MAP_STAIRS.update(helix(bp, [(278, 370, 1, 16)], 17.0, 20.4, 1, full=PUR, half=PUR_SL,
                            fill=PLINTH.pick(0, 0, 0), rail=False))
    for x in range(-21, 22):
        for z in range(-21, 22):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 16.6 < d <= 17.6 and (in_arc(a, 170, 252) or in_arc(a, 288, 370)):
                y = 1
                while bp.get(x, y, z) not in (None, AIR) and y < 17:
                    y += 1
                if y < 16:
                    bp.set(x, y, z, PUR_P if (round(a) % 12) < 2 else ESB_WA)
    # globes on pedestals at the four diagonals, lecterns round the rim, cartography tables
    for k in range(4):
        a = 135 + 90 * k
        x, z = polar(11, a)
        x, z = round(x), round(z)
        if k == 3:
            continue                             # the meteorite side
        bp.set(x, 1, z, BRASS)
        bp.set(x, 2, z, GAUGE)
        bp.set(x, 3, z, "amethyst_block" if k % 2 else "lapis_block")
        bp.set(x, 4, z, ROD_UP)
    for k in range(12):
        a = 7.5 + 30 * k
        if 20 < a < 75 or 85 < a < 100:
            continue
        x, z = polar(13.5, a)
        lectern(bp, round(x), 1, round(z), face_in(round(x), round(z), 0, 0))
    for (x, z) in ((-6, 19), (6, 19)):
        bp.set(x, 1, z, "cartography_table")
    bp.set(-7, 1, 19, stair("dark_oak_stairs", "east"))
    bp.set(7, 1, 19, stair("dark_oak_stairs", "west"))
    bp.chest(-3, 1, -20, "south", loot=LOOT + "sl_maproom")
    candle(bp, -2, 1, -20, 3)
    bp.set(-4, 1, -20, TABLE)
    # the ceiling: a gold ring, a starlight chandelier over the oculus and lamps
    for x in range(-24, 25):
        for z in range(-24, 25):
            d = math.hypot(x, z)
            if 11.5 < d <= 12.4:
                bp.set(x, 14, z, GOLD)
    bp.set(0, 13, 0, CHANDELIER)
    for k in range(8):
        x, z = polar(12, 22.5 + 45 * k)
        hang_star(bp, round(x), 13, round(z), 3, light=FROG if k % 2 else STAR)
    bp.spawner(-12, 1, 6, MOB_ACOLYTE)


# ------------------------------------------------------------------ the stacks
MAP_STAIRS = {}
SHELVES = [(5, 6, 13), (-6, -5, 13), (11, 12, 8), (-12, -11, 8)]   # x0, x1, |z| max
SHELF_TOP = 45


def stacks(bp):
    """The bookshelf canyons: four walls of shelves 30 high round a central nave, end posts and purpur shelf
    courses, two catwalks, rolling ladders, the wall stair, lamps, the second waystone."""
    # floor: aisles in purpur and void bricks, a gold nave line
    for x in range(-20, 21):
        for z in range(-20, 21):
            d = math.hypot(x, z)
            if d > 20.4:
                continue
            spec = (GOLD if x == 0 and z % 4 == 0 else PUR) if abs(x) <= 1 else (VB if (x + z) % 2 else PUR)
            bp.set(x, 15, z, spec)
    # the stairwells of the map-room stairs come up through this floor
    for (x, z), st in MAP_STAIRS.items():
        top = math.floor(st) if st - math.floor(st) > 0.25 else math.floor(st) - 1
        if top < 15 and st > 12.4:
            bp.set(x, 15, z, "air")
    # the shelf walls
    for (x0, x1, zm) in SHELVES:
        for x in range(x0, x1 + 1):
            for z in range(-zm, zm + 1):
                for y in range(16, SHELF_TOP + 1):
                    endpost = abs(z) == zm
                    if endpost:
                        spec = PUR_P
                    elif y in (22, 34) or y == SHELF_TOP:
                        spec = PUR
                    else:
                        face = "east" if x == max(x0, x1) else "west"
                        spec = shelf_block(x, y, z, face)
                    bp.set(x, y, z, spec)
            for z in range(-zm, zm + 1):
                bp.set(x, SHELF_TOP + 1, z, slab(PUR_SL) if abs(z) != zm else PUR_P)
            for z in (-zm, zm):
                bp.set(x, SHELF_TOP + 2, z, ROD_UP)
    # the wall stair: 16 -> 28 (west landing) -> 40 (north landing) -> 53 (east, into the scriptorium)
    helix(bp, [(90, 166, 16, 28), (166, 190, 28, 28), (190, 266, 28, 40), (266, 290, 40, 40),
               (290, 372, 40, 53)], 16.5, 20.4, 16, full=PUR, half=PUR_SL, fill=ESB)
    # catwalk 28 (east-west, z -1..1): cut through the shelves, a diamond-plate deck, brass railings
    for x in range(-17, 18):
        if math.hypot(x, 0) > 17.0:
            continue
        for z in range(-1, 2):
            bp.set(x, 27, z, TREAD if z else BRASS)
            for y in range(28, 32):
                bp.set(x, y, z, "air")
        for z in (-2, 2):
            if any(x0 <= x <= x1 for (x0, x1, zm) in SHELVES):
                continue
            if bp.get(x, 27, z) in (None, AIR):
                bp.set(x, 27, z, slab(BRASS_SLAB, "top"))
            railing(bp, x, 28, z, "north" if z < 0 else "south")
    # catwalk 40 (north-south over the nave, x -1..1), hung on chains
    for z in range(-17, 18):
        if math.hypot(0, z) > 17.0:
            continue
        for x in range(-1, 2):
            bp.set(x, 39, z, TREAD if x else BRASS)
            for y in range(40, 43):
                bp.set(x, y, z, "air")
        for x in (-2, 2):
            bp.set(x, 39, z, slab(BRASS_SLAB, "top"))
            railing(bp, x, 40, z, "west" if x < 0 else "east")
            if z % 6 == 0:
                bp.chain(x, 41, z, 50)
    # rolling ladders: floor -> catwalk 28 on the canyon faces, catwalk 28 -> 40 on the nave face
    for (x, z, f) in ((7, 2, "east"), (-7, -2, "west")):
        for y in range(16, 28):
            bp.set(x, y, z, f"ladder[facing={f},waterlogged=false]")
        bp.set(x, 32, z - 1 if z > 0 else z + 1, "air")
    for z in range(-4, 5):                          # the rail the ladders roll on
        for x in (7, -7):
            if bp.get(x, 31, z) in (None, AIR):
                bp.set(x, 31, z, f"iron_chain[axis=z,waterlogged=false]")
    for y in range(28, 40):
        bp.set(4, y, 3, "ladder[facing=west,waterlogged=false]")
    for (x, z) in ((3, 2), (4, 2), (2, 3), (3, 3)):
        bp.set(x, 27, z, TREAD)
    for (x, z) in ((2, 3), (3, 3), (2, 4), (3, 4), (2, 2)):
        bp.set(x, 39, z, TREAD)
        bp.set(x, 40, z, "air")
    bp.set(2, 40, 3, "air")
    # catwalk ends: the east balcony (catwalk 28) and the south balcony (catwalk 40) hold chests
    bp.chest(16, 28, 0, "west", loot=LOOT + "sl_stacks")
    bp.chest(0, 40, 16, "north", loot=LOOT + "sl_stacks")
    candle(bp, 16, 28, 1, 2)
    # reading tables in the nave, the second waystone at its south end
    for z in (-10, -4, 4):
        for x in (-2, 2):
            bp.set(x, 16, z, TABLE)
            bp.set(x, 16, z - 1, stair("dark_oak_stairs", "south"))
            bp.set(x, 16, z + 1, stair("dark_oak_stairs", "north"))
        candle(bp, 2, 17, z, 2)
    bp.set(0, 16, 12, MOD["waystone"])
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(dx, 15, 12 + dz, GOLD)
    # lamps hanging into the canyons from the stacks' ceiling (y 51)
    for (x, z) in ((-9, -8), (9, 8), (-9, 6), (9, -5), (-15, 0), (15, -6), (0, -9), (0, 9), (-3, 0)):
        if math.hypot(x, z) < 16:
            hang(bp, x, 51, z, 8 + int(hash01(x, z, 1962) * 5), FROG if hash01(x, z, 1963) < 0.5 else LANT_H)
    # ceiling beams (radial purpur pillars under the scriptorium floor)
    for k in range(8):
        a = 22.5 * k
        ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
        for t in range(-19, 20):
            x, z = round(ux * t), round(uz * t)
            if math.hypot(x, z) <= 20:
                bp.set(x, 50, z, f"purpur_pillar[axis={'x' if abs(ux) > abs(uz) else 'z'}]")
    bp.spawner(9, 16, -6, MOB_STALKER)
    # doors at feet 16 onto the plinth terrace (R1 spokes), the catwalk-40 door onto R2 (iron, opens from the ring)
    door_cut(bp, 180, 19.6, 22.6, 16)
    door_cut(bp, 270, 19.6, 22.6, 16)
    door_cut(bp, 270, 19.6, 22.6, 40, w=3, h=4)
    for x in range(-1, 2):
        bp.set(x, 39, -21, BRASS)
        bp.set(x, 39, -22, BRASS)


def catwalk_door(bp):
    """The iron door from R2's spoke into catwalk 40: its lever is on the ring side only (a one-way shortcut)."""
    iron_door(bp, 0, 40, -22, "south")
    for y in (40, 41):
        bp.set(-1, y, -22, PUR_P)
        bp.set(1, y, -22, PUR_P)
    bp.set(0, 42, -22, PUR_P)
    lever(bp, 1, 41, -23, "north")


# ------------------------------------------------------------------ the scriptorium
def scriptorium(bp):
    """Copyists' desks (lecterns with stools) in two rings round the ink vat, paper racks, barrels, candles, the stair
    up to the roof terrace."""
    for x in range(-20, 21):
        for z in range(-20, 21):
            d = math.hypot(x, z)
            if d > 20.4:
                continue
            if bp.get(x, 52, z) in (None, AIR):
                continue
            bp.set(x, 52, z, PUR if d > 18.5 or d < 3.2 else ("dark_oak_planks" if (x + z) % 3 else "spruce_planks"))
    # the stair up to the terrace (feet 65), entirely inside the scriptorium's wall ring
    helix(bp, [(20, 96, 53, 65)], 16.5, 20.4, 53, full=PUR, half=PUR_SL, fill=ESB)
    # the ink vat and its brass pipes
    for (x, z) in disk_pts(0, 0, 2.2):
        bp.set(x, 53, z, COPPER if math.hypot(x, z) > 1.2 else "water_cauldron[level=3]")
    bp.set(0, 54, 0, "iron_chain[axis=y,waterlogged=false]")
    for y in range(54, 63):
        bp.set(0, y, 0, "iron_chain[axis=y,waterlogged=false]")
    bp.set(0, 55, 0, CHANDELIER)
    for y in range(53, 63):
        bp.set(2, y, -2, PIPES)
    # two rings of desks (lectern + stool), facing the vat
    for (rr, n, a0) in ((7.5, 10, 0), (12.5, 14, 10)):
        for k in range(n):
            a = a0 + 360.0 * k / n
            x, z = polar(rr, a)
            x, z = round(x), round(z)
            f = face_in(x, z, 0, 0)
            lectern(bp, x, 53, z, f)
            sx, sz = polar(rr + 1.2, a)
            sx, sz = round(sx), round(sz)
            if (sx, sz) != (x, z) and bp.get(sx, 53, sz) in (None, AIR):
                bp.set(sx, 53, sz, stair("dark_oak_stairs", f))
            cx, cz = polar(rr, a + 360.0 / n / 2)
            cx, cz = round(cx), round(cz)
            if bp.get(cx, 53, cz) in (None, AIR) and k % 2 == 0:
                candle(bp, cx, 53, cz, 1 + k % 3)
    # supplies along the wall: barrels, looms, drying racks of paper (white banners), a copyists' chest
    for k in range(10):
        a = 108 + 22 * k
        if in_arc(a, 340, 372):
            continue
        x, z = polar(15.5, a)
        x, z = round(x), round(z)
        if k % 3 == 0:
            bp.barrel(x, 53, z, "up")
        elif k % 3 == 1:
            bp.set(x, 53, z, "loom[facing=" + face_in(x, z, 0, 0) + "]")
        else:
            bp.set(x, 53, z, "cartography_table")
        bp.set(x, 58, z, "white_banner[rotation=0]")
    bp.chest(-15, 53, 4, "east", loot=LOOT + "sl_scriptorium")
    bp.spawner(-9, 53, -9, MOB_ACOLYTE)
    for k in range(6):
        x, z = polar(10, 30 + 60 * k)
        hang(bp, round(x), 63, round(z), 2, HANG_LAMP)
    # railing round the stair well arriving from the stacks (340..372 deg)
    for x in range(-21, 22):
        for z in range(-21, 22):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 15.6 < d <= 16.5 and in_arc(a, 338, 374) and bp.get(x, 52, z) not in (None, AIR):
                railing(bp, x, 53, z, out_facing(-x, -z) if False else out_facing(x, z))


# ------------------------------------------------------------------ terrace, upper hall, observatory
def terrace_and_hall(bp):
    """The roof terrace (feet 65) with a crenellated parapet; the upper hall (the celestial index) with its armillary
    sphere, catalogue cabinets, the third waystone and the stair up to the observatory."""
    for x in range(-23, 24):
        for z in range(-23, 24):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 17.4 < d <= 22.4:
                if bp.get(x, 64, z) in (None, AIR):
                    continue
                bp.set(x, 64, z, GOLD if 19.5 < d <= 20.3 and (round(a) % 20) < 3 else PAVE.pick(x, 64, z))
                if d > 21.4:
                    crenel = (round(a * 22.4 * 0.0175) % 2) == 0
                    bp.set(x, 65, z, PUR_P if (round(a) % 30) < 2 else (ESB_WA if crenel else slab(ESB_SL)))
                    if (round(a) % 30) < 2:
                        bp.set(x, 66, z, ROD_UP)
    # the hall floor, ceiling lamps
    for x in range(-15, 16):
        for z in range(-15, 16):
            d = math.hypot(x, z)
            if d <= 15.4:
                bp.set(x, 64, z, GOLD if 6.5 < d <= 7.4 else (VB if (x + z) % 2 else PUR))
    door_cut(bp, 90, 14.6, 17.6, 65, w=3, h=4)
    # the stair up to the observatory, against the hall wall
    helix(bp, [(100, 236, 65, 81)], 11.5, 15.4, 65, full=PUR, half=PUR_SL, fill=ESB)
    # the armillary sphere: three gilded rings round a starlight core on a brass column
    for y in range(65, 69):
        bp.set(0, y, 0, BRASS if y < 68 else GEAR)
    c = (0, 72, 0)
    ring3d(bp, c, 4.5, (1, 0, 0), (0, 0, 1), GOLD)
    ring3d(bp, c, 4.5, (1, 0, 0), (0, math.sin(math.radians(60)), math.cos(math.radians(60))), BRASS)
    ring3d(bp, c, 4.5, (0, 0, 1), (math.cos(math.radians(-50)), math.sin(math.radians(-50)), 0), GOLD)
    bp.set(0, 72, 0, STAR)
    for y in range(69, 72):
        bp.set(0, y, 0, "iron_chain[axis=y,waterlogged=false]")
    for y in range(73, 78):
        bp.set(0, y, 0, "iron_chain[axis=y,waterlogged=false]")
    # catalogue cabinets (chiseled shelves) in short arcs, lecterns
    for k in range(6):
        a = 280 + 25 * k
        x, z = polar(9, a)
        x, z = round(x), round(z)
        for y in range(65, 67):
            bp.set(x, y, z, chiseled(face_in(x, z, 0, 0), k * 7 + y))
    lectern(bp, -7, 65, 3, "east")
    lectern(bp, 7, 65, -3, "west")
    bp.set(-5, 65, -7, MOD["waystone"])
    bp.chest(6, 65, 7, "north", loot=LOOT + "sl_index")
    for k in range(6):
        x, z = polar(10, 60 * k)
        hang(bp, round(x), 78, round(z), 2, HANG_LAMP)


def observatory(bp):
    """The lens observatory (feet 81): a brass telescope 16 long aimed out of the dome's slit with a lens at its
    mouth, an orrery ring in the floor, star desks, the balcony door to the ramp."""
    for x in range(-15, 16):
        for z in range(-15, 16):
            d = math.hypot(x, z)
            if d <= 15.4 and bp.get(x, 80, z) not in (None, AIR):
                a = ang(x, z)
                bp.set(x, 80, z, GOLD if 9.5 < d <= 10.4 or (abs(((a - 45 + 180) % 360) - 180) < 3) else
                       (VB if d < 9.5 else PUR))
    # the telescope: pier, tube, lens
    for y in range(81, 85):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            bp.set(dx - 1, y, dz - 1, BRASS if y < 84 else GEAR)
    el = math.radians(40)
    az = math.radians(45)
    dvec = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
    tube(bp, (0, 86, 0), dvec, 15, 1.4, 2.4, BRASS, rings=GOLD, ring_every=4, back=3)
    lc = [0 + dvec[0] * 15.5, 86 + dvec[1] * 15.5, 0 + dvec[2] * 15.5]
    for x in range(-20, 21):
        for y in range(80, 106):
            for z in range(-20, 21):
                w = (x - lc[0], y - lc[1], z - lc[2])
                t = w[0] * dvec[0] + w[1] * dvec[1] + w[2] * dvec[2]
                if abs(t) > 0.6:
                    continue
                perp = math.sqrt(max(0.0, w[0] ** 2 + w[1] ** 2 + w[2] ** 2 - t * t))
                if perp <= 2.6:
                    bp.set(x, y, z, "glass")
                elif perp <= 3.6:
                    bp.set(x, y, z, GOLD)
    # star desks, a chest, the shulker sentinel
    for k in range(5):
        a = 150 + 30 * k
        x, z = polar(12.5, a)
        x, z = round(x), round(z)
        if bp.get(x, 81, z) in (None, AIR):
            lectern(bp, x, 81, z, face_in(x, z, 0, 0))
    bp.chest(-12, 81, -4, "east", loot=LOOT + "sl_observatory")
    bp.set(-12, 81, -3, TABLE)
    candle(bp, -12, 82, -3, 3)
    bp.spawner(-6, 81, 10, "minecraft:shulker")
    hang_star(bp, -6, 104, 0, 6)
    hang_star(bp, 6, 104, -5, 5)
    # the balcony and its door
    door_cut(bp, OBS_DOOR, 14.6, 17.6, 81, w=3, h=4)
    for x in range(-22, 23):
        for z in range(-22, 23):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 17.4 < d <= 20.6 and abs(((a - OBS_DOOR + 180) % 360) - 180) < 11:
                bp.set(x, 80, z, PUR)
                bp.set(x, 79, z, stair(PUR_ST, out_facing(x, z), "top") if d > 19.6 else PUR)


# ------------------------------------------------------------------ the rings
def ring(bp, R, F, hw, arcs, seed, spokes=(), gates=(), loot=None, chests=(), spawners=()):
    """A ring-shaped reading gallery: a deck 2*hw+1 wide on a keel (gold string course, obsidian bottom hung with end
    rods), an outer wall lined with bookshelves and pierced with windows, an inner arcade with a balustrade open to
    the tower, a purpur roof with a gold ridge; carrels in the bays. arcs: [(a0, a1)] (jagged where they end)."""
    cols = {}
    span = R + hw + 3
    for x in range(-span, span + 1):
        for z in range(-span, span + 1):
            d = math.hypot(x, z)
            u = d - R
            if abs(u) > hw + 1.45:
                continue
            a = ang(x, z)
            for (a0, a1) in arcs:
                full = (a1 - a0) >= 359.9
                j0 = 0 if full else 1.2 * math.sin(u * 1.3 + seed) + 0.7 * math.sin(u * 2.9 + seed * 1.7)
                j1 = 0 if full else 1.1 * math.sin(u * 1.1 + seed * 2.3) + 0.8 * math.sin(u * 3.3 + seed)
                lo, hi = a0 + j0 * 0.9, a1 + j1 * 0.9
                if full or in_arc(a, lo, hi):
                    e = 99.0 if full else min((a - lo) % 360, (hi - a) % 360) * math.pi / 180 * R
                    cols[(x, z)] = (u, a, e)
                    break
    keys = set(cols)
    for (x, z), (u, a, e) in cols.items():
        A = math.radians(a) * R
        pos = A % 7.0
        bay = int(A // 7.0)
        broken = e < 3.0
        deck = abs(u) <= hw + 0.4
        if not deck:
            # roof overhang only (and the outer buttress)
            if not broken and e > 4:
                if u > 0 and pos < 1.0:
                    for y in range(F - 2, F + GH):
                        bp.set(x, y, z, PUR_P if y < F + GH - 1 else GOLD)
                bp.set(x, F + GH, z, stair(PUR_ST, out_facing(x, z) if u > 0 else face_in(x, z, 0, 0)))
            continue
        # deck and keel
        top = PUR if abs(u) < 0.6 else (GOLD if abs(u) > hw - 0.5 and pos < 0.6 else PAVE.pick(x, F, z))
        if broken:
            top = "end_stone" if hash01(x, z, int(seed * 10)) < 0.5 else "cracked_polished_blackstone_bricks"
        bp.set(x, F - 1, z, top)
        uu = u / (hw + 1.0)
        depth = 2 + round(5 * max(0.0, 1 - uu * uu) ** 0.8)
        if broken:
            depth = max(1, depth - 3 + round(2 * hash01(x, z, int(seed * 10) + 1)))
        edge = any(n not in keys for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)))
        for y in range(F - 1 - depth, F - 1):
            t = F - 1 - y
            if y == F - 1 - depth:
                spec = KEEL.pick(x, y, z)
            elif edge and t == 1:
                spec = GOLD if pos < 1.2 or abs(u) > hw else PUR
            elif edge:
                spec = PUR
            else:
                spec = VB
            bp.set(x, y, z, spec)
        if abs(u) < 0.6 and pos < 0.5 and not broken:
            bp.set(x, F - 2 - depth, z, ROD_DOWN)
        if broken:
            continue
        # outer wall: facade layer + bookshelf lining, windows at the middle of each bay
        if u > hw - 1.6:
            outer = u > hw - 0.6
            win = 2.5 <= pos < 4.5
            for y in range(F, F + GH):
                if win and F + 1 <= y <= F + 4:
                    spec = "purple_stained_glass_pane"
                elif outer:
                    spec = PUR_P if pos < 1.0 else (ESB if y == F else BODY.pick(x, y, z))
                else:
                    spec = shelf_block(x, y, z, face_in(x, z, 0, 0)) if y < F + GH - 1 else PUR
                bp.set(x, y, z, spec)
        elif u < -hw + 0.6:
            # inner arcade: piers and a balustrade
            spoke = any(abs(((a - s + 180) % 360) - 180) * math.pi / 180 * R < 2.0 for s in spokes)
            if pos < 1.0 and not spoke:
                for y in range(F, F + GH):
                    bp.set(x, y, z, PUR_P if y < F + GH - 1 else GOLD)
            elif not spoke:
                bp.set(x, F, z, ESB_WA)
                bp.set(x, F + GH - 1, z, stair(PUR_ST, face_in(x, z, 0, 0), "top"))
                for y in range(F + 1, F + GH - 1):
                    bp.set(x, y, z, "air")
            else:
                for y in range(F, F + GH - 1):
                    bp.set(x, y, z, "air")
                bp.set(x, F + GH - 1, z, PUR)
        else:
            for y in range(F, F + GH):
                bp.set(x, y, z, "air")
        # roof
        if e > 4:
            ridge = abs(u) < 0.6
            bp.set(x, F + GH, z, GOLD if ridge else (PUR if abs(u) < hw - 1 else
                                                    stair(PUR_ST, out_facing(x, z) if u > 0 else face_in(x, z, 0, 0))))
            if ridge and pos < 0.6:
                bp.set(x, F + GH + 1, z, ROD_UP)
        else:
            if hash01(x, z, int(seed * 10) + 3) < 0.3:
                bp.set(x, F + GH - 1, z, "air")
    # carrels: in alternate bays a lectern and stool against the lining, or a table with two stools; lamps
    done = set()
    for (x, z), (u, a, e) in cols.items():
        if e < 6 or abs(u - (hw - 2)) > 0.5:
            continue
        A = math.radians(a) * R
        bay = int(A // 7.0)
        pos = A % 7.0
        if bay in done or not (3.0 <= pos < 4.0):
            continue
        done.add(bay)
        if not empty(bp, x, F, z):
            continue
        f = face_in(x, z, 0, 0)
        k = bay % 4
        if k == 0:
            lectern(bp, x, F, z, "north" if f == "south" else "south" if f == "north" else
                    ("east" if f == "west" else "west"))
        elif k == 1:
            bp.set(x, F, z, TABLE)
            candle(bp, x, F + 1, z, 2)
        elif k == 2:
            bp.barrel(x, F, z, "up")
        else:
            bp.set(x, F, z, "chiseled_bookshelf[facing=" + f + ",slot_0_occupied=true,slot_1_occupied=true,"
                   "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
        cx, cz = polar(R, a)
        if empty(bp, round(cx), F + GH - 2, round(cz)):
            hang(bp, round(cx), F + GH, round(cz), 1, LANT_H)
    for (a, name) in chests:
        x, z = polar(R + hw - 2, a)
        x, z = round(x), round(z)
        bp.chest(x, F, z, face_in(x, z, 0, 0), loot=LOOT + name)
    for (a, mob) in spawners:
        x, z = polar(R - 1, a)
        bp.spawner(round(x), F, round(z), mob)
    return cols


def terminator(bp, R, F, hw, a, toward):
    """A rail across a ring's deck near its broken end (toward = +1 / -1: the side the break is on)."""
    for k in range(-hw - 1, hw + 2):
        x, z = polar(R + k, a)
        x, z = round(x), round(z)
        if bp.get(x, F - 1, z) not in (None, AIR) and empty(bp, x, F, z):
            bp.set(x, F, z, ESB_WA if k % 3 else PUR_P)


def gatehouse(bp):
    """R1's gatehouse at 110 deg: a square pavilion over the ring with a pyramid roof; the side bridge comes in on its
    south face."""
    X0, X1, Z0, Z1 = -24, -15, 50, 59
    F = F_R1
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            wall = x in (X0, X1) or z in (Z0, Z1)
            for y in range(F - 4, F + 10):
                if y < F:
                    bp.set(x, y, z, VB if y > F - 4 else KEEL.pick(x, y, z))
                elif wall:
                    bp.set(x, y, z, PUR_P if (x in (X0, X1) and z in (Z0, Z1)) else
                           (GOLD if y == F + 9 else BODY.pick(x, y, z)))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, F - 1, z, PUR if (x + z) % 2 else ESB)
    bp.pyramid_roof(X0, Z0, X1, Z1, F + 10, PUR_ST, overhang=1, cap=GOLD)
    bp.set((X0 + X1) // 2, F + 16, (Z0 + Z1) // 2, ROD_UP)
    # openings: along the ring (the ring passes north-east / south-west through it) and the south door
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            d = math.hypot(x, z)
            if abs(d - R1) <= HW1 - 0.6 and (x in (X0, X1) or z in (Z0, Z1)):
                for y in range(F, F + 5):
                    bp.set(x, y, z, "air")
    for x in range(-21, -18):
        for y in range(F, F + 4):
            bp.set(x, y, Z1, "air")
    bp.set(-22, F + 4, Z1 + 1, STAR)
    bp.set(-18, F + 4, Z1 + 1, STAR)
    hang(bp, -20, F + 9, 54, 2, CHANDELIER)
    bp.spawner(-23, F, 51, "minecraft:enderman")


def stays(bp):
    """Chain-and-end-rod spokes: a chain stay from the tower down to each ring's roof, an end-rod strut under each
    deck, every 30 degrees (not where a walkway or ramp passes)."""
    specs = (
        # ring R, hw, feet, tower radius and stay height, strut tower radius
        (R1, HW1, F_R1, 22.5, 44, 27.5, ()),
        (R2, HW2, F_R2, 22.5, 60, 22.5, (220, 300)),
        (R3, HW3, F_R3, 17.5, 90, 22.5, ()),
    )
    for (R, hw, F, rt, yt, rs, skip) in specs:
        for k in range(12):
            a = 15 + 30 * k
            if skip and in_arc(a, skip[0], skip[1]):
                continue
            if R == R2 and not in_arc(a, R2_ARC[0] + 4, R2_ARC[1] - 4):
                continue
            if R == R3 and in_arc(a, OBS_DOOR, OBS_DOOR + 90):
                continue
            x0, z0 = polar(rt, a)
            x1, z1 = polar(R - hw - 1, a)
            line3(bp, (x0, yt, z0), (x1, F + GH + 1, z1), "chain")
            xs, zs = polar(rs, a)
            line3(bp, (xs, F - 3, zs), (x1, F - 3, z1), "rod")
            bp.set(round(x0), yt, round(z0), GOLD)


def spokes_walk(bp):
    """The walkable spokes: R1 -> plinth terrace (W, N), terrace -> R3 (E, W), the catwalk-40 door -> R2 (N)."""
    walkway(bp, [(-26.0, F_R1, 0), (-R1 + HW1 + 0.6, F_R1, 0)], width=3, style="brass")
    walkway(bp, [(0, F_R1, -26.0), (0, F_R1, -R1 + HW1 + 0.6)], width=3, style="brass")
    walkway(bp, [(22.0, F_R3, 0), (R3 - HW3 - 0.6, F_R3, 0)], width=3, style="brass")
    walkway(bp, [(-22.0, F_R3, 0), (-R3 + HW3 + 0.6, F_R3, 0)], width=3, style="brass")
    walkway(bp, [(0, F_R2, -22.6), (0, F_R2, -R2 + HW2 + 0.6)], width=3, style="brass")
    # gaps in the terrace parapets for them
    for (x, z) in ((-26, 0), (-25, 0), (0, -26), (0, -25), (22, 0), (21, 0), (-22, 0), (-21, 0)):
        for o in (-1, 0, 1):
            xx, zz = (x, z + o) if z == 0 else (x + o, z)
            y = F_R1 if abs(x) + abs(z) > 24 and (abs(x) == 26 or abs(z) == 26 or abs(x) == 25 or abs(z) == 25) \
                else F_R3
            bp.set(xx, y, zz, "air")


def ramps(bp):
    """The ramp from the observatory balcony curling down round the tower to R3, and the ramp from R3 to R2."""
    pts = []
    for i in range(25):
        t = i / 24
        r = 19.5 + (R3 - HW3 - 0.8 - 19.5) * t
        a = OBS_DOOR + 100 * t
        x, z = polar(r, a)
        pts.append((x, F_OBS - 16 * t, z))
    walkway(bp, pts, width=3, style="stone")
    pts = []
    for i in range(33):
        t = i / 32
        r = (R3 + HW3 + 1.0) + ((R2 - HW2 - 0.8) - (R3 + HW3 + 1.0)) * t
        a = 220 + 80 * t
        x, z = polar(r, a)
        pts.append((x, F_R3 - (F_R3 - F_R2) * t, z))
    walkway(bp, pts, width=3, style="stone")
    # chains holding them from above
    for (rr, a0, a1, s0, s1) in ((24, OBS_DOOR, OBS_DOOR + 100, F_OBS, F_R3), (40, 220, 300, F_R3, F_R2)):
        for k in range(1, 6):
            t = k / 6
            x, z = polar(rr, a0 + (a1 - a0) * t)
            s = s0 + (s1 - s0) * t
            y0 = math.floor(s) - 2
            for y in range(y0 - 6, y0):
                if empty(bp, round(x), y, round(z)):
                    bp.set(round(x), y, round(z), "iron_chain[axis=y,waterlogged=false]")
            bp.set(round(x), y0 - 7, round(z), FROG)


# ------------------------------------------------------------------ arrival
def arrival(bp):
    cx, cz = ISLET
    F = F_ISLET
    cols = rock_lobe(cx, F - 1, cz, 9.5, 8.5, 18, 1970, spikes=6)
    build_rock(bp, cols, 1970, surface="end_stone")
    for (x, z) in disk_pts(cx, cz, 6.5):
        if (x, z) in cols:
            d = math.hypot(x - cx, z - cz)
            bp.set(x, F - 1, z, PUR if 5.5 < d <= 6.9 else (GOLD if d < 1.5 else PAVE.pick(x, 0, z)))
    bp.set(cx, F, cz + 1, MOD["waystone"])
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, F - 1, cz + 1 + dz, GOLD)
    brazier(bp, cx + 5, F, cz + 2, h=2)
    brazier(bp, cx - 6, F, cz + 1, h=2)
    # pilgrims' camp: book crates, a lectern, a reading lamp
    bp.barrel(cx + 3, F, cz + 5, "up", loot=LOOT + "sl_camp")
    bp.barrel(cx + 4, F, cz + 5, "up")
    bp.set(cx + 2, F, cz + 5, SHELF)
    lectern(bp, cx - 2, F, cz + 5, "north")
    bp.set(cx - 3, F, cz + 5, LANT)
    bp.set(cx + 1, F, cz - 5, "purple_banner[rotation=8]")
    # the ruined gateway at the head of the low bridge, framing the tower
    gx, gz = cx + 4, cz - 6
    for (dx, h) in ((-3, 9), (3, 6)):
        for y in range(F, F + h):
            bp.set(gx + dx, y, gz, PUR_P if y < F + h - 1 else PUR)
    for dx in (-3, -2, -1, 0):
        bp.set(gx + dx, F + 9, gz, GOLD if dx == -3 else PUR)
    bp.set(gx - 3, F + 10, gz, ROD_UP)
    # the low bridge (to the plaza) and the side bridge (up to R1's gatehouse)
    walkway(bp, [(gx, float(F), gz - 1.0), (-8.0, 2.0, 66.0), (-5.0, 1.0, 50.0)], width=3, style="stone", rise=1.0)
    walkway(bp, [(-20.0, float(F), 88.0), (-20.0, float(F_R1), 60.0)], width=3, style="stone", rise=0.5)
    # a short path of paving from the bridge to the porch
    for z in range(34, 52):
        for x in range(-3, 4):
            if math.hypot(x, z) > 26.4 and bp.get(x, 0, z) not in (None, AIR):
                xx = x + round((z - 34) * -5 / 17.0)
                if bp.get(xx, 0, z) not in (None, AIR):
                    bp.set(xx, 0, z, PUR if x == 0 else ESB)


# ------------------------------------------------------------------ the meteorite
def m_surface_r(x, y, z):
    """Normalised radius of the meteorite (<= 1 inside), bumpy."""
    dx, dy, dz = x - M[0], y - M[1], z - M[2]
    n = 0.08 * (vnoise(x + y * 0.7, z - y * 0.4, 4.0, 1980) - 0.5)
    return math.sqrt((dx / M_R) ** 2 + (dy / M_RY) ** 2 + (dz / M_R) ** 2) - n


def meteorite(bp):
    """The meteorite: a charred crust with magma seams over an obsidian and meteoric-iron core, wedged in the tower;
    the crater rim of rubble round its foot, cracks in the walls it struck, scattered books."""
    cx, cy, cz = M
    for x in range(cx - 19, cx + 20):
        for z in range(cz - 19, cz + 20):
            for y in range(cy - 17, cy + 18):
                e = m_surface_r(x, y, z)
                if e > 1.0:
                    continue
                if y < 0 and math.hypot(x, z) < 24.4:
                    pass
                spec = CRUST.pick(x, y, z) if e > 0.86 else CORE.pick(x, y, z)
                bp.set(x, y, z, spec)
    # glowing veins on the crust
    for x in range(cx - 19, cx + 20):
        for z in range(cz - 19, cz + 20):
            for y in range(cy - 17, cy + 18):
                e = m_surface_r(x, y, z)
                if 0.9 < e <= 1.0 and hash3(x, y, z, 1981) < 0.05:
                    bp.set(x, y, z, STAR if hash3(x, y, z, 1982) < 0.5 else "magma_block")
    # the crater rim: rubble ring round the foot, sloping down to the plaza
    for x in range(cx - 24, cx + 25):
        for z in range(cz - 24, cz + 25):
            d = math.hypot(x - cx, z - cz)
            if d > 23 or math.hypot(x, z) < 27:
                continue
            h = 5.0 * max(0.0, 1 - abs(d - 15.5) / 7.5) + 1.2 * (vnoise(x, z, 3.0, 1983) - 0.5)
            top = round(h)
            for y in range(0, top + 1):
                if empty(bp, x, y, z):
                    spec = "end_stone" if hash3(x, y, z, 1984) < 0.5 else CRATER.pick(x, y, z)
                    if y == top and hash01(x, z, 1985) < 0.12:
                        spec = PUR if hash01(x, z, 1986) < 0.5 else SHELF
                    bp.set(x, y, z, spec)
            if bp.get(x, 0, z) in (ESB, "minecraft:end_stone_bricks", "minecraft:purpur_block"):
                bp.set(x, 0, z, "cracked_polished_blackstone_bricks" if hash01(x, z, 1987) < 0.3 else "end_stone")
    # cracks radiating through the tower walls round the impact (tuff and blackstone seams, no openings)
    for x in range(-28, 29):
        for z in range(-28, 29):
            for y in range(-1, 64):
                b = bp.get(x, y, z)
                if b is None or b == AIR:
                    continue
                e = m_surface_r(x, y, z)
                if 1.0 < e <= 1.45 and math.hypot(x, z) > 18.5:
                    if hash3(x, y, z, 1988) < 0.45 * (1.45 - e) / 0.45 + 0.1:
                        bp.set(x, y, z, "cracked_polished_blackstone_bricks" if hash3(x, y, z, 1989) < 0.6 else
                               "blackstone")
    # the map room floor near the impact: scorched
    for x in range(-24, 25):
        for z in range(-24, 25):
            if math.hypot(x, z) <= 24.4 and bp.get(x, 0, z) not in (None, AIR):
                e = m_surface_r(x, 1, z)
                if 1.0 < e <= 1.35 and hash01(x, z, 1990) < 0.7:
                    bp.set(x, 0, z, "magma_block" if hash01(x, z, 1991) < 0.2 else "blackstone")
    # books knocked out of the stacks and the map room, lying round the meteorite's foot inside
    for i in range(70):
        a = 45 + (hash01(i, 1, 1992) - 0.5) * 70
        r = 15 + 6 * hash01(i, 2, 1992)
        x, z = polar(r, a)
        x, z = round(x), round(z)
        for yb in (1, 16):
            y = yb
            while y < yb + 6 and not empty(bp, x, y, z):
                y += 1
            if y < yb + 6 and math.hypot(x, z) <= 20.4 and not empty(bp, x, y - 1, z) and hash01(i, yb, 1993) < 0.6:
                bp.set(x, y, z, SHELF if hash01(i, 3, 1992) < 0.6 else slab("dark_oak_slab"))


def fissure(bp):
    """The corkscrew down the meteorite: from its top (feet 33) four laps down to feet -3 under the plaza, a tunnel to
    the grace, glowing veins, an amethyst geode chamber off the second lap (the meteorite's own treasure)."""
    cx, cz = M[0], M[2]
    s0, s1, pitch, a0 = 33.0, -3.0, 9.0, 335.0
    total = (s0 - s1) / pitch * 360.0
    rin, rout = 2.4, 6.4
    cells = []
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if not (rin < d <= rout):
                continue
            a = ang(x - cx, z - cz)
            base = (a - a0) % 360.0
            k = 0
            while base + 360 * k <= total + 1e-6:
                phi = base + 360 * k
                s = q2(s0 - pitch * phi / 360.0)
                cells.append((x, z, s, phi))
                k += 1
    for (x, z, s, phi) in cells:
        for c in range(0, 5):
            bp.set(x, math.floor(s) + c, z, "air")
    for (x, z, s, phi) in cells:
        mid = abs(math.hypot(x - cx, z - cz) - 4.4) < 0.8
        y = surface(bp, x, z, s, "polished_blackstone" if mid else "blackstone", "polished_blackstone_slab",
                    under="blackstone")
        if hash01(x, z, int(phi)) < 0.05:
            wall = None
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if math.hypot(x + dx - cx, z + dz - cz) > rout:
                    wall = (x + dx, z + dz)
            if wall and not empty(bp, wall[0], y + 2, wall[1]):
                bp.set(wall[0], y + 2, wall[1], STAR)
    # the mouth: a rim of crying obsidian and amethyst
    mx, mz = polar(4.4, a0)
    for (x, z) in disk_pts(round(cx + mx), round(cz + mz), 3.5):
        for y in range(31, 36):
            if empty(bp, x, y, z) and not empty(bp, x, y - 1, z) and m_surface_r(x, y - 1, z) <= 1.05:
                if hash01(x, z, 1994) < 0.35:
                    bp.set(x, y, z, "amethyst_cluster[facing=up,waterlogged=false]")
                break
    # the geode: a small chamber off the corkscrew (second lap, toward the south-east), amethyst and the chest
    ga = a0 + 360 + 120
    gs = q2(s0 - pitch * (360 + 120) / 360.0)
    gx, gz = polar(9.5, ga)
    gx, gz = round(cx + gx), round(cz + gz)
    gy = math.floor(gs)
    for x in range(gx - 3, gx + 4):
        for z in range(gz - 3, gz + 4):
            for y in range(gy - 1, gy + 5):
                d = math.sqrt((x - gx) ** 2 + (z - gz) ** 2 + ((y - gy - 1.5) * 1.2) ** 2)
                if d <= 2.9:
                    bp.set(x, y, z, "air" if y >= gy else "amethyst_block")
                elif d <= 3.9 and not empty(bp, x, y, z):
                    bp.set(x, y, z, "amethyst_block" if hash3(x, y, z, 1995) < 0.7 else "budding_amethyst")
    # the passage from the corkscrew into the geode
    ex, ez = polar(5.5, ga)
    for t in range(0, 6):
        x, z = polar(5.0 + t * 0.9, ga)
        x, z = round(cx + x), round(cz + z)
        for y in range(gy, gy + 3):
            bp.set(x, y, z, "air")
        bp.set(x, gy - 1, z, "blackstone")
    bp.chest(gx, gy, gz, "north", loot=LOOT + "sl_meteorite")
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2)):
        bp.set(gx + dx, gy, gz + dz, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.spawner(gx, gy, gz - 2, "minecraft:endermite")
    # the tunnel from the corkscrew's foot to the grace (feet -3 -> -8)
    end_a = (a0 + total) % 360
    ex, ez = polar(4.4, end_a)
    ex, ez = cx + ex, cz + ez
    gxx, gzz = GRACE
    pts = [(ex, s1, ez), (ex + (gxx + 4 - ex) * 0.5, s1 - 1.5, ez + (gzz - 4 - ez) * 0.5), (gxx + 3.0, F_GRACE * 1.0,
                                                                                         gzz - 3.0)]
    out = walkway(bp, pts, width=3, style="rock", rails=False)
    for (x, z), s in out.items():
        y = math.floor(s)
        for c in range(0, 4):
            bp.set(x, y + c, z, "air")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (x + dx, z + dz) not in out:
                    for c in range(-1, 5):
                        if empty(bp, x + dx, y + c, z + dz) and y + c < 0:
                            bp.set(x + dx, y + c, z + dz, CRATER.pick(x + dx, y + c, z + dz))
        if empty(bp, x, y + 4, z) and y + 4 < 0:
            bp.set(x, y + 4, z, CRATER.pick(x, y + 4, z))
        if hash01(x, z, 1996) < 0.06:
            bp.set(x, y + 3, z, ROD_DOWN)


# ------------------------------------------------------------------ the broken gallery: book platforms, catch basin
def platform_path():
    pts = [(41.3, -20.2), (47, -13), (50, -4), (49, 5), (44.5, 13), (37.5, 18), (31.5, 20.5), (27.3, 21.3)]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return pts, L


def book_platforms(bp):
    """Open books floating across the gap of R2, each half a block lower than the last, stepping down onto the
    meteorite; a brass catch basin of water hangs under them with a ladder back up."""
    pts, L = platform_path()
    tot = L[-1]
    s_start, s_end = float(F_R2), 33.0
    plats = []
    step = 4.7
    n = int(tot / step)
    for i in range(1, n + 1):
        t = i * step
        if t > tot - 1.0:
            break
        k = max(j for j in range(len(L) - 1) if L[j] <= t)
        f = (t - L[k]) / (L[k + 1] - L[k])
        x = pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f
        z = pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f
        tx, tz = pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]
        tl = math.hypot(tx, tz)
        s = q2(s_start - (s_start - s_end) * t / tot)
        plats.append((x, z, tx / tl, tz / tl, s))
    cells = {}
    for i, (x, z, tx, tz, s) in enumerate(plats):
        for X in range(round(x) - 4, round(x) + 5):
            for Z in range(round(z) - 4, round(z) + 5):
                u = (X - x) * tx + (Z - z) * tz
                v = -(X - x) * tz + (Z - z) * tx
                if abs(u) <= 2.4 and abs(v) <= 2.3:
                    if (X, Z) not in cells or cells[(X, Z)][0] < s:
                        cells[(X, Z)] = (s, i, u, v)
    for (X, Z), (s, i, u, v) in cells.items():
        cover = COVERS[i % len(COVERS)]
        if abs(v) <= 0.5:
            full, half = "dark_oak_planks", "dark_oak_slab"            # the spine
        elif abs(v) >= 1.8 or abs(u) >= 2.0:
            full, half = f"{cover}_planks", f"{cover}_slab"           # the cover's edge
        else:
            full, half = "birch_planks", "birch_slab"                   # the pages
        y = surface(bp, X, Z, s, full, half, under=SHELF)
        for c in range(1, 4):
            if not empty(bp, X, y + c, Z) and bp.get(X, y + c, Z) not in ("minecraft:air",):
                pass
            bp.set(X, y + c, Z, "air")
        if empty(bp, X, y - 1, Z):
            bp.set(X, y - 1, Z, SHELF)
        if abs(u) < 0.6 and abs(v) < 0.6:
            bp.chain(X, y - 4, Z, y - 2)
            bp.set(X, y - 5, Z, STAR if i % 2 else FROG)
    # the catch basin: water two deep, ten below the books, under every book cell not above the meteorite
    yb = 27
    basin = set()
    for (X, Z), (s, i, u, v) in cells.items():
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                p = (X + dx, Z + dz)
                if m_surface_r(p[0], yb + 1, p[1]) <= 1.25 or math.hypot(*p) < R2 - HW2 + 0.5:
                    continue
                basin.add(p)
    for (X, Z) in basin:
        nb = [(X + 1, Z), (X - 1, Z), (X, Z + 1), (X, Z - 1)]
        rim = any(n not in basin for n in nb)
        bp.set(X, yb - 1, Z, BRASS if (X + Z) % 5 else COPPER)
        bp.set(X, yb - 2, Z, slab(BRASS_SLAB, "top") if not rim else COPPER)
        if rim:
            for y in range(yb, yb + 3):
                bp.set(X, y, Z, BRASS if y < yb + 2 else slab(BRASS_SLAB))
        else:
            bp.set(X, yb, Z, WATER)
            bp.set(X, yb + 1, Z, WATER)
    # chains from the basin rim up to nothing (the books hold it by magic): a few short hangers below it
    for (X, Z) in basin:
        if hash01(X, Z, 1997) < 0.06:
            bp.chain(X, yb - 5, Z, yb - 3)
            bp.set(X, yb - 6, Z, FROG)
    # the ladder back up: a brass post on the basin rim beside the third book
    x, z, tx, tz, s = plats[2]
    lx, lz = round(x - tz * 3.4), round(z + tx * 3.4)
    top = math.floor(s)
    for y in range(yb - 1, top + 1):
        bp.set(lx, y, lz, BRASS)
    nx, nz = -tz, tx
    ox, oz = (lx - (1 if nx > 0 else -1), lz) if abs(nx) >= abs(nz) else (lx, lz - (1 if nz > 0 else -1))
    f = out_facing(ox - lx, oz - lz)
    if True:
        for y in range(yb, math.ceil(s)):
            bp.set(ox, y, oz, f"ladder[facing={f},waterlogged=false]")
    bp.set(lx, top + 1, lz, LANT)
    return cells


def gap_debris(bp):
    """Shards of the middle gallery drifting in its gap and below it, a scorched trail on R2's broken end."""
    for j, (a, dr, dy, sz) in enumerate(((345, 3, -9, 2), (352, -2, -14, 3), (2, 4, -6, 2), (10, -3, -18, 2),
                                         (18, 6, -11, 1), (24, 1, 4, 1), (338, 7, 3, 1))):
        cx, cz = polar(R2 + dr, a)
        cx, cz = round(cx), round(cz)
        cy = F_R2 + dy
        for x in range(cx - sz - 1, cx + sz + 2):
            for z in range(cz - sz - 1, cz + sz + 2):
                if abs(x - cx) + abs(z - cz) > sz + 1:
                    continue
                y = cy + round(0.4 * (x - cx) - 0.3 * (z - cz))
                if not empty(bp, x, y, z):
                    continue
                bp.set(x, y, z, PUR if hash3(x, y, z, 1998 + j) < 0.6 else VB)
                if empty(bp, x, y - 1, z):
                    bp.set(x, y - 1, z, OBS)
                if (x, z) == (cx, cz) and empty(bp, x, y - 2, z):
                    bp.set(x, y - 2, z, ROD_DOWN)
    for x in range(30, 52):
        for z in range(-30, -8):
            d = math.hypot(x, z)
            if abs(d - R2) <= HW2 + 0.4 and in_arc(ang(x, z), 326, 342):
                if bp.get(x, F_R2 - 1, z) not in (None, AIR) and hash01(x, z, 1999) < 0.45:
                    bp.set(x, F_R2 - 1, z, "blackstone" if hash01(x, z, 2000) < 0.7 else "magma_block")


# ------------------------------------------------------------------ under the tower: grace, arena, vault, lift
def grace_room(bp):
    gx, gz = GRACE
    f = F_GRACE
    for x in range(gx - 6, gx + 7):
        for z in range(gz - 6, gz + 7):
            for y in range(f - 2, f + 8):
                d = math.sqrt((x - gx) ** 2 + (z - gz) ** 2)
                if d <= 5.4 and f <= y <= f + 6 - (1 if d > 4.4 else 0):
                    bp.set(x, y, z, "air")
                elif d <= 6.6:
                    if y >= f and bp.get(x, y, z) == AIR:
                        continue                    # the tunnel from the corkscrew comes in here
                    if empty(bp, x, y, z) or y < f or d > 5.4:
                        bp.set(x, y, z, CRATER.pick(x, y, z) if y != f - 1 else
                               (PUR if d < 1.5 or (d > 3.5 and d <= 4.4) else ESB))
    for (x, z) in disk_pts(gx, gz, 5.4):
        d = math.hypot(x - gx, z - gz)
        bp.set(x, f - 1, z, GOLD if d < 1.5 else (PUR if 3.5 < d <= 4.4 else ESB))
    bp.set(gx, f, gz + 2, MOD["waystone"])
    brazier(bp, gx - 3, f, gz + 3, h=1)
    brazier(bp, gx + 4, f, gz + 1, h=1)
    hang_star(bp, gx, f + 6, gz - 1, 2)
    bp.set(gx - 4, f, gz - 2, SHELF)
    bp.set(gx - 4, f + 1, gz - 2, LANT)


def passage(bp):
    """The compression: 3 wide, 4 high, from the grace north down 14 by two flights to the mist at the arena's
    south mouth."""
    gx, gz = GRACE
    x0, x1 = gx - 1, gx + 1
    # flat 37..34 (feet -8), stairs 33..27 (-9..-15), landing 26..24 (-15), stairs 23..17 (-16..-22), mouth
    f = F_GRACE
    profile = []
    z = gz - 5
    for _ in range(4):
        profile.append((z, f, None))
        z -= 1
    for k in range(7):
        f -= 1
        profile.append((z, f, "north"))
        z -= 1
    for _ in range(3):
        profile.append((z, f, None))
        z -= 1
    for k in range(7):
        f -= 1
        profile.append((z, f, "north"))
        z -= 1
    while math.hypot(gx, z) > ARENA_R - 0.5:
        profile.append((z, f, None))
        z -= 1
    mouth = None
    for (zz, ff, fc) in profile:
        for x in range(x0 - 1, x1 + 2):
            for y in range(ff - 2, ff + 5):
                if x in (x0 - 1, x1 + 1) or y in (ff - 2, ff + 4):
                    if empty(bp, x, y, zz) or y < 0:
                        bp.set(x, y, zz, CRATER.pick(x, y, zz))
        for x in range(x0, x1 + 1):
            for y in range(ff, ff + 4):
                bp.set(x, y, zz, "air")
            if fc:
                bp.set(x, ff - 1, zz, stair("polished_blackstone_brick_stairs", fc))
                bp.set(x, ff - 2, zz, PBB)
            else:
                bp.set(x, ff - 1, zz, PBB if x != gx else PUR)
        if zz % 3 == 0:
            bp.set(x0 - 1, ff + 2, zz, "end_rod[facing=east]")
        mouth = (zz, ff)
    return mouth


def arena(bp):
    """The crater chamber: radius 17, walls of glassy obsidian 12 high under a dome rising to 18, impact rings in the
    floor, a meteorite fragment in the south-east wall, the oculus shaft to the map room above."""
    fy = F_ARENA - 1
    R = ARENA_R
    for x in range(-21, 22):
        for z in range(-21, 22):
            d = math.hypot(x, z)
            if d > R + 3.0:
                continue
            ceil = -11 + 7 * math.sqrt(max(0.0, 1 - (d / (R + 0.6)) ** 2))
            for y in range(fy - 3, 1):
                if d <= R and fy < y <= ceil:
                    bp.set(x, y, z, "air")
                elif y < 0 or d > R:
                    if y < -1 or (d > 24.4):
                        spec = CRATER.pick(x, y, z)
                        if d > R and hash3(x, y, z, 2010) < 0.05:
                            spec = "amethyst_block"
                        bp.set(x, y, z, spec)
            # floor rings
            if d <= R:
                if d <= 2.6:
                    spec = "magma_block" if hash01(x, z, 2011) < 0.3 else "blackstone"
                elif d <= 5.5:
                    spec = "blackstone" if hash01(x, z, 2012) < 0.6 else OBS
                elif 10.5 < d <= 11.4:
                    spec = GOLD if (round(ang(x, z)) % 20) < 4 else PUR
                elif d > R - 1.0:
                    spec = PUR
                else:
                    spec = VB if int(d) % 3 else ESB
                bp.set(x, fy, z, spec)
    # radial cracks with glow in the walls, amethyst clusters on the dome
    for k in range(9):
        a = 20 + 40 * k
        for y in range(fy + 1, -10):
            x, z = polar(R + 0.6, a + 2 * math.sin(y * 0.7))
            x, z = round(x), round(z)
            if not empty(bp, x, y, z):
                bp.set(x, y, z, STAR if y % 4 == 0 else "magma_block")
    for i in range(60):
        a = 360 * hash01(i, 1, 2013)
        d = (R - 1) * math.sqrt(hash01(i, 2, 2013))
        x, z = polar(d, a)
        x, z = round(x), round(z)
        ceil = math.floor(-11 + 7 * math.sqrt(max(0.0, 1 - (math.hypot(x, z) / (R + 0.6)) ** 2)))
        if empty(bp, x, ceil, z) and not empty(bp, x, ceil + 1, z):
            bp.set(x, ceil, z, "amethyst_cluster[facing=down,waterlogged=false]" if i % 3 else ROD_DOWN)
    # the oculus shaft: radius 2.6 from the dome apex up to the glass in the map room floor
    for (x, z) in disk_pts(0, 0, 2.6):
        for y in range(-5, 0):
            bp.set(x, y, z, "air")
    for (x, z) in disk_pts(0, 0, 3.6):
        if math.hypot(x, z) > 2.6:
            for y in range(-5, 0):
                bp.set(x, y, z, GOLD if y == -1 else OBS)
    # the meteorite fragment in the south-east wall
    fx, fz = polar(R + 1.5, 45)
    for x in range(round(fx) - 5, round(fx) + 6):
        for z in range(round(fz) - 5, round(fz) + 6):
            for y in range(fy, fy + 10):
                d = math.sqrt((x - fx) ** 2 + (z - fz) ** 2 + ((y - fy - 3) * 1.1) ** 2)
                if d <= 4.4:
                    bp.set(x, y, z, CORE.pick(x, y, z) if d < 3.4 else CRUST.pick(x, y, z))
    # light: four starlight braziers round the ring, end rods on the wall
    for a in (0, 90, 180, 270):
        x, z = polar(R - 2.5, a + 45)
        bp.set(round(x), fy + 1, round(z), VB)
        bp.set(round(x), fy + 2, round(z), STAR)
        bp.set(round(x), fy + 3, round(z), "amethyst_cluster[facing=up,waterlogged=false]")
    for k in range(16):
        a = 11.25 + 22.5 * k
        x, z = polar(R - 0.2, a)
        if empty(bp, round(x), fy + 6, round(z)):
            bp.set(round(x), fy + 6, round(z), f"end_rod[facing={out_facing(-x, -z)}]")
    bp.boss_seal(0, fy, 0, BOSS, int(R) - 1)


def vault(bp):
    """The forbidden stacks: chained shelves, soul lanterns, a sealed lectern, two chests; sealed bars to the arena,
    the pneumatic-tube lift to the map room."""
    x0, z0, x1, z1 = VAULT
    f = F_ARENA
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 2, f + 8):
                wall = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1) or y in (f - 2, f - 1, f + 7)
                if wall:
                    bp.set(x, y, z, VB if y != f - 1 else (GOLD if (x + z) % 4 == 0 else PBB))
                else:
                    bp.set(x, y, z, "air")
    # shelves along the long walls, chained
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            for y in range(f, f + 6):
                if x in (x0, x1) or x % 3 == 0:
                    bp.set(x, y, z, PUR_P if x % 3 == 0 else shelf_block(x, y, z, "south" if z == z0 else "north"))
                else:
                    bp.set(x, y, z, chiseled("south" if z == z0 else "north", x * 11 + y))
            if x % 3 == 1:
                zz = z + (1 if z == z0 else -1)
                bp.chain(x, f + 3, zz, f + 6)
    for z in range(z0 + 1, z1):
        for y in range(f, f + 6):
            bp.set(x0, y, z, shelf_block(x0, y, z, "east"))
    # the sealed lectern, chests, skulls, soul lanterns
    lectern(bp, x0 + 2, f, 0, "east")
    bp.set(x0 + 1, f, 0, OBS)
    bp.set(x0 + 1, f + 1, 0, "wither_skeleton_skull[powered=false,rotation=12]")
    bp.chest(x0 + 4, f, z0 + 1, "south", loot=LOOT + "sl_vault")
    bp.chest(x0 + 4, f, z1 - 1, "north", loot=LOOT + "sl_vault")
    for (x, z) in ((x0 + 6, z0 + 1), (x0 + 6, z1 - 1), (x0 + 2, z0 + 2)):
        bp.set(x, f, z, "raw_gold_block" if (x + z) % 2 else "amethyst_block")
    for x in (x0 + 2, x0 + 7):
        hang(bp, x, f + 7, 0, 2, SOUL_H)
    # the passage to the arena, the sealed bars
    for x in range(x1 + 1, -15):
        for z in range(-1, 2):
            for y in range(f, f + 4):
                bp.set(x, y, z, "air")
            bp.set(x, f - 1, z, PBB)
        for z in (-2, 2):
            for y in range(f, f + 4):
                bp.set(x, y, z, PUR_P if x % 2 else VB)
        bp.set(x, f + 4, 0, VB)
        for z in (-1, 1):
            bp.set(x, f + 4, z, VB)
    for z in range(-1, 2):
        for y in range(f, f + 4):
            bp.set(-18, y, z, MOD["vault_bars"])
    for z in (-2, 2):
        for y in range(f, f + 5):
            bp.set(-18, y, z, PUR_P if y < f + 4 else GOLD)
    for z in range(-1, 2):
        bp.set(-18, f + 4, z, GOLD)


def lift(bp):
    """The pneumatic-tube lift: a bubble column in a brass-and-glass tube from the vault floor up to a booth in the map
    room; signs hold the water at its foot, the booth's iron door opens from inside (a lever by the tube)."""
    lx, lz = LIFT
    f = F_ARENA
    bp.set(lx, f - 1, lz, "soul_sand")
    for y in range(f, 1):
        bp.set(lx, y, lz, "bubble_column[drag=false]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                x, z = lx + dx, lz + dz
                if (dx, dz) == (1, 0) and y in (f, f + 1):
                    continue
                corner = dx != 0 and dz != 0
                bp.set(x, y, z, (BRASS if y % 6 else GEAR) if corner else ("glass" if y % 6 else BRASS))
    bp.set(lx + 1, f, lz, "spruce_sign[rotation=12,waterlogged=false]")
    bp.set(lx + 1, f + 1, lz, "spruce_wall_sign[facing=east,waterlogged=false]")
    bp.set(lx + 1, f + 2, lz, BRASS)
    for y in range(f, f + 7):
        bp.set(lx + 2, y, lz - 2, PIPES)
    # the booth in the map room: the tube's top is level with the floor (y 0); step off east, iron door further east
    for x in range(lx - 1, lx + 3):
        for z in range(lz - 1, lz + 2):
            for y in range(1, 5):
                wall = x in (lx - 1, lx + 2) or z in (lz - 1, lz + 1) or y == 4
                bp.set(x, y, z, (GLASS_B if (wall and y in (2, 3) and z != lz) else BRASS) if wall else "air")
            if (x, z) != (lx, lz):
                bp.set(x, 0, z, BRASS)
    bp.set(lx, 0, lz, "bubble_column[drag=false]")
    iron_door(bp, lx + 2, 1, lz, "east")
    lever(bp, lx + 1, 2, lz, "south")
    bp.set(lx, 5, lz, GAUGE)
    bp.set(lx + 1, 5, lz, PIPES)


GLASS_B = "glass"


# ------------------------------------------------------------------ the whole site
def starfall_library(bp):
    cols = island(bp)
    plaza(bp, cols)
    tower_shell(bp)
    dome_and_needle(bp)
    great_door(bp)
    map_room(bp)
    stacks(bp)
    scriptorium(bp)
    terrace_and_hall(bp)
    observatory(bp)
    ring(bp, R1, F_R1, HW1, [(0.0, 360.0)], 3.1, spokes=(180, 270, 110),
         chests=((150, "sl_gallery"), (330, "sl_gallery")), spawners=((225, "minecraft:endermite"),))
    gatehouse(bp)
    ring(bp, R2, F_R2, HW2, [R2_ARC], 5.3, spokes=(270,), chests=((235, "sl_gallery_high"),),
         spawners=((285, MOB_ACOLYTE),))
    terminator(bp, R2, F_R2, HW2, R2_ARC[0] + 3.5, -1)
    ring(bp, R3, F_R3, HW3, [(0.0, 360.0)], 7.7, spokes=(0, 180), chests=((200, "sl_gallery_high"),),
         spawners=((95, MOB_STALKER),))
    stays(bp)
    spokes_walk(bp)
    catwalk_door(bp)
    ramps(bp)
    arrival(bp)
    meteorite(bp)
    fissure(bp)
    book_platforms(bp)
    gap_debris(bp)
    grace_room(bp)
    arena(bp)
    passage(bp)
    gx, gz = GRACE
    bp.mist(gx - 1, F_ARENA, 17, gx + 1, F_ARENA + 3, 17)
    vault(bp)
    lift(bp)


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("arrival", (-13, F_ISLET, 88), (0, 60, 0)),
    ("map_room", (0, 1, 19), (6, 7, -8)),
    ("stacks", (0, F_STACKS, 15), (0, 40, -12)),
    ("scriptorium", (-12, F_SCRIPT, 8), (8, 57, -6)),
    ("observatory", (-8, F_OBS, -6), (6, 92, 6)),
    ("broken_gallery", (39, F_R2, -24), (30, 32, 18)),
    ("crater_arena", (4, F_ARENA, 13), (-4, -12, -8)),
]


register(StructureDef(
    "starfall_library", "end", OUTER_END,
    [Piece("library", starfall_library, views=VIEWS)],
    spacing=40, separation=14, adaptation="none", height=("uniform", 30, 40), processors="none", max_distance=116,
    ground=0, foundation=False,
    spawns=[("minecraft:enderman", 10, 1, 2), (MOB_STALKER, 5, 1, 2), (MOB_ACOLYTE, 5, 1, 2)],
    title_fr="La Bibliothèque de la chute d'étoile", title_en="The Starfall Library"))
