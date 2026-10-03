"""Overworld structures (group A): Guild outpost, Mountain monastery, Forgotten library, Coastal lighthouse.

All four are composed from the architecture kit (`wf.arch`) plus a few local helpers below
(gothic windows, rose windows, flying buttresses, curtain walls, dormers, timber storeys...).
Coordinates: x east, y up, z south; y=0 is the ground layer. Front previews look at the south
and east faces, so main entrances face south/east.
"""
import math
import random

from .. import arch as A
from ..arch import Palette
from ..blueprint import OPPOSITE, with_props
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD
from . import lair_archivist, lair_bell_keeper

TEMPERATE = ["#minecraft:is_forest", "plains", "sunflower_plains", "meadow", "#minecraft:is_taiga",
             "savanna", "cherry_grove"]

# ------------------------------------------------------------------ Wayfarers blocks
GB = "wayfarers:guild_bricks"
GB_ST = "wayfarers:guild_brick_stairs"
GB_SL = "wayfarers:guild_brick_slab"
GB_WALL = "wayfarers:guild_brick_wall"
MGB = "wayfarers:mossy_guild_bricks"
CRGB = "wayfarers:cracked_guild_bricks"
PGS = "wayfarers:polished_guild_stone"
PGS_ST = "wayfarers:polished_guild_stone_stairs"
PGS_SL = "wayfarers:polished_guild_stone_slab"
CGS = "wayfarers:carved_guild_stone"
RUNE = "wayfarers:rune_lamp"

# roofs: (full block, stairs, slab)
ROOF = {
    "azure": ("wayfarers:guild_roof_tiles", "wayfarers:guild_roof_tile_stairs", "wayfarers:guild_roof_tile_slab"),
    "crimson": ("wayfarers:crimson_roof_tiles", "wayfarers:crimson_roof_tile_stairs",
                "wayfarers:crimson_roof_tile_slab"),
    "slate": ("wayfarers:slate_roof_tiles", "wayfarers:slate_roof_tile_stairs", "wayfarers:slate_roof_tile_slab"),
    "deepslate": ("deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_slab"),
    "copper": ("waxed_oxidized_cut_copper", "waxed_oxidized_cut_copper_stairs", "waxed_oxidized_cut_copper_slab"),
    "dark_oak": ("dark_oak_planks", "dark_oak_stairs", "dark_oak_slab"),
    "spruce": ("spruce_planks", "spruce_stairs", "spruce_slab"),
}

pos = A._pos


def stp(block, facing, half="bottom"):
    return A.stair(block, facing, half)


def slb(block, kind="bottom"):
    return A.slab(block, kind)


def side_of(face):
    """Direction of increasing u along a facade."""
    return A._along_dir(face)


def leaves(spec):
    return with_props(spec, persistent=True, distance=1, waterlogged=False)


def fset(bp, face, line, u, out, y, spec, keep=False):
    x, z = pos(face, line, u, out)
    bp.set(x, y, z, spec.pick(x, y, z) if hasattr(spec, "pick") else spec, keep=keep)


def pset(bp, face, line, u, out, y, pal):
    x, z = pos(face, line, u, out)
    bp.set(x, y, z, A.as_pal(pal).pick(x, y, z))


# ------------------------------------------------------------------ roofs
def roof(bp, x0, z0, x1, z1, y, R, *, axis="x", overhang=1, steep=1.0, gable=None, under=None, hollow=True,
         ridge_cap=None):
    """Gable roof over the box x0..x1 / z0..z1 starting at height y. `steep` may be fractional
    (1.5 = alternating 1 and 2 rows per step). `gable` palette fills the gable end walls.
    The inside is cleared (only where nothing is set yet) so attics stay hollow.
    Returns the ridge height."""
    full, st, sl = R
    if axis == "x":
        lo, hi, a0, a1, ends = z0 - overhang, z1 + overhang, x0 - overhang, x1 + overhang, (x0, x1)
        f_lo, f_hi = "south", "north"

        def P(a, yy, b):
            return a, yy, b
    else:
        lo, hi, a0, a1, ends = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang, (z0, z1)
        f_lo, f_hi = "east", "west"

        def P(a, yy, b):
            return b, yy, a
    gpal = A.as_pal(gable) if gable else None
    yy, i = y, 0
    while lo + i <= hi - i:
        rows = max(1, round((i + 1) * steep) - round(i * steep))
        for k in range(rows):
            last = k == rows - 1
            for a in range(a0, a1 + 1):
                if lo + i == hi - i:
                    bp.set(*P(a, yy, lo + i), (ridge_cap or slb(sl)) if last else full)
                else:
                    bp.set(*P(a, yy, lo + i), stp(st, f_lo) if last else full)
                    bp.set(*P(a, yy, hi - i), stp(st, f_hi) if last else full)
                    if hollow and a0 < a < a1:
                        for b in range(lo + i + 1, hi - i):
                            bp.set(*P(a, yy, b), "air", keep=True)
            if gpal:
                for b in range(lo + i + 1, hi - i):
                    for a in ends:
                        x, _, z = P(a, yy, b)
                        bp.set(x, yy, z, gpal.pick(x, yy, z))
            yy += 1
        i += 1
    if under:
        for a in range(a0, a1 + 1):
            bp.set(*P(a, y - 1, lo), stp(under, f_hi, "top"))
            bp.set(*P(a, y - 1, hi), stp(under, f_lo, "top"))
    return yy - 1


def dormer(bp, face, line, u, y, R, wall, glass="glass_pane", depth=4, trim=None):
    """Wall dormer: a small gabled bay rising from the facade plane (out=0) into the roof."""
    full, st, sl = R
    s = side_of(face)
    wall = A.as_pal(wall)
    for out in range(0, -depth, -1):
        for du in (-1, 0, 1):
            for dy in range(0, 3):
                x, z = pos(face, line, u + du, out)
                if out == 0 or abs(du) == 1:
                    bp.set(x, y + dy, z, wall.pick(x, y + dy, z))
                else:
                    bp.set(x, y + dy, z, "air")
    for dy in (1, 2):
        fset(bp, face, line, u, 0, y + dy, glass)
    if trim:
        for du in (-1, 1):
            for dy in range(0, 3):
                fset(bp, face, line, u + du, 0, y + dy, trim)
    for out in range(1, -depth - 1, -1):
        fset(bp, face, line, u - 2, out, y + 2, stp(st, s))
        fset(bp, face, line, u + 2, out, y + 2, stp(st, OPPOSITE[s]))
        fset(bp, face, line, u - 1, out, y + 3, stp(st, s))
        fset(bp, face, line, u + 1, out, y + 3, stp(st, OPPOSITE[s]))
        fset(bp, face, line, u, out, y + 3, full)
        fset(bp, face, line, u, out, y + 4, slb(sl))
    fset(bp, face, line, u, 1, y, stp(st, OPPOSITE[face], "top"))


# ------------------------------------------------------------------ windows
def gwindow(bp, face, line, cu, y0, h, glass, frame, frame_st, w=3, sill=None, hood=True, mullion=None):
    """Pointed (gothic) window of odd width w, h tall straight part, with jambs/hood moulding
    protruding one block and an optional sill."""
    half = w // 2
    s = side_of(face)
    for du in range(-half, half + 1):
        for y in range(y0, y0 + h):
            fset(bp, face, line, cu + du, 0, y, glass)
    if mullion and w >= 3:
        for y in range(y0, y0 + h):
            fset(bp, face, line, cu, 0, y, mullion)
    for r in range(half):
        y = y0 + h + r
        ru = half - r
        fset(bp, face, line, cu - ru, 0, y, stp(frame_st, OPPOSITE[s], "top"))
        fset(bp, face, line, cu + ru, 0, y, stp(frame_st, s, "top"))
        for du in range(-ru + 1, ru):
            fset(bp, face, line, cu + du, 0, y, glass)
    fset(bp, face, line, cu, 0, y0 + h + half, frame)
    if hood:
        for y in range(y0, y0 + h):
            for du in (-half - 1, half + 1):
                fset(bp, face, line, cu + du, 1, y, frame)
        for r in range(half + 1):
            y = y0 + h + r
            ru = half + 1 - r
            fset(bp, face, line, cu - ru, 1, y, stp(frame_st, s))
            fset(bp, face, line, cu + ru, 1, y, stp(frame_st, OPPOSITE[s]))
        fset(bp, face, line, cu, 1, y0 + h + half + 1, frame)
    if sill:
        for du in range(-half - 1, half + 2):
            fset(bp, face, line, cu + du, 1, y0 - 1, stp(sill, OPPOSITE[face], "top"))


def rose(bp, face, line, cu, cy, r, frame, glasses, center=None, spokes=8, ring=None):
    """Rose window in a facade plane, with tracery spokes and a moulded outer ring."""
    for du in range(-r - 1, r + 2):
        for dy in range(-r - 1, r + 2):
            d = math.hypot(du, dy)
            if d > r + 0.45:
                continue
            ang = math.atan2(dy, du) % (2 * math.pi / spokes)
            arc = min(ang, 2 * math.pi / spokes - ang) * d
            if d > r - 0.55:
                b = frame
            elif d < 1.0:
                b = center or frame
            elif arc < 0.45 and d > 1.5:
                b = frame
            else:
                b = glasses[min(len(glasses) - 1, int(d * len(glasses) / r))]
            fset(bp, face, line, cu + du, 0, cy + dy, b)
            if r - 0.6 < d <= r + 0.45:
                fset(bp, face, line, cu + du, 1, cy + dy, ring or frame)


def shutters(bp, face, line, u, y, h, wood):
    for du in (-1, 1):
        for dy in range(h):
            fset(bp, face, line, u + du, 1, y + dy,
                 f"{wood}_trapdoor[facing={face},half=bottom,open=true,powered=false,waterlogged=false]")


def wall_lamp(bp, face, line, u, y, bracket, soul=False):
    fset(bp, face, line, u, 1, y + 1, stp(bracket, OPPOSITE[face], "top"))
    x, z = pos(face, line, u, 1)
    bp.lantern(x, y, z, hanging=True, soul=soul)


# ------------------------------------------------------------------ walls & masses
def gothic_wall(bp, face, line, u0, u1, y0, y1, wall, trim, trim_st, *, bay=5, win=None, buttress=None,
                plinth=None, plinth_st=None, cornice_st=None, parapet=None):
    """Wall plane with buttresses every `bay` blocks and windows centred in each bay.
    win = dict(y=, h=, w=, glass=, mullion=, sill=) ; buttress = (block, stairs, depth)."""
    wall = A.as_pal(wall)
    lo, hi = min(u0, u1), max(u0, u1)
    for u in range(lo, hi + 1):
        for y in range(y0, y1 + 1):
            pset(bp, face, line, u, 0, y, wall)
        if plinth:
            for y in range(y0, y0 + 2):
                pset(bp, face, line, u, 0, y, plinth)
            if plinth_st:
                fset(bp, face, line, u, 1, y0, stp(plinth_st, OPPOSITE[face]))
        if cornice_st:
            fset(bp, face, line, u, 1, y1, stp(cornice_st, OPPOSITE[face], "top"))
        if parapet:
            pset(bp, face, line, u, 0, y1 + 1, parapet)
    piers = list(range(lo, hi + 1, bay))
    if piers[-1] != hi:
        piers.append(hi)
    for u in piers:
        if buttress:
            blk, bst, depth = buttress
            A.buttress(bp, face, line, u, y0, y1 - y0 - 1, blk, bst, depth)
            for y in range(y0, y1 + 1):
                pset(bp, face, line, u, 0, y, trim)
        else:
            for y in range(y0, y1 + 1):
                pset(bp, face, line, u, 0, y, trim)
                pset(bp, face, line, u, 1, y, trim)
    if win:
        for a, b in zip(piers, piers[1:]):
            if b - a - 1 < win.get("w", 3) + 2 - 2:
                continue
            cu = (a + b) // 2
            gwindow(bp, face, line, cu, y0 + win["y"], win["h"], win.get("glass", "glass_pane"), win.get("frame", trim),
                    trim_st, w=win.get("w", 3), sill=win.get("sill"), hood=win.get("hood", True),
                    mullion=win.get("mullion"))
    return piers


def flying_buttress(bp, face, line, u, y_wall, dist, y0, block, st, cap=None):
    """Pier `dist` blocks out from the wall, linked to the wall top (y_wall) by a sloping arch."""
    yp = y_wall - (dist - 1)
    for y in range(y0, yp + 1):
        fset(bp, face, line, u, dist, y, block)
    for y in range(y0, y0 + (yp - y0) // 2):
        fset(bp, face, line, u, dist + 1, y, block)
    fset(bp, face, line, u, dist + 1, y0 + (yp - y0) // 2, stp(st, OPPOSITE[face]))
    for k, d in enumerate(range(dist - 1, 0, -1)):
        yy = yp + k + 1
        fset(bp, face, line, u, d, yy, block)
        fset(bp, face, line, u, d, yy + 1, stp(st, OPPOSITE[face]))
        fset(bp, face, line, u, d, yy - 1, stp(st, face, "top"))
    # pinnacle
    fset(bp, face, line, u, dist, yp + 1, block)
    fset(bp, face, line, u, dist, yp + 2, cap or block)
    fset(bp, face, line, u, dist, yp + 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def curtain(bp, x0, z0, x1, z1, y0, h, pal, trim, trim_st, merlon=None, skip=()):
    """Thick (2) crenellated curtain wall around a rectangle, walkway at y0+h, buttress
    pilasters outside. `skip` = list of (xa, za, xb, zb) boxes left open (gates, towers)."""
    pal = A.as_pal(pal)

    def skipped(x, z):
        return any(a <= x <= c and b <= z <= d for a, b, c, d in skip)

    faces = (("north", z0, x0, x1, 1), ("south", z1, x0, x1, -1), ("west", x0, z0, z1, 1), ("east", x1, z0, z1, -1))
    for face, line, a, b, inward in faces:
        for u in range(a, b + 1):
            for t in (0, 1):
                x, z = (u, line + inward * t) if face in ("north", "south") else (line + inward * t, u)
                if skipped(x, z):
                    continue
                for y in range(y0, y0 + h + 1):
                    bp.set(x, y, z, pal.pick(x, y, z))
                bp.set(x, y0 + h, z, A.as_pal(trim).pick(x, y0 + h, z) if t == 0 else
                       slb(trim_st.replace("_stairs", "_slab"), "top"))
            ox, oz = pos(face, line, u, 0)
            if skipped(ox, oz):
                continue
            # merlons on the outer edge
            if u % 2 == 0:
                bp.set(ox, y0 + h + 1, oz, A.as_pal(merlon or pal).pick(ox, y0 + h + 1, oz))
                bp.set(ox, y0 + h + 2, oz, slb(trim_st.replace("_stairs", "_slab")))
            else:
                bp.set(ox, y0 + h + 1, oz, slb(trim_st.replace("_stairs", "_slab")))
            # corbel line under the parapet + plinth
            fset(bp, face, line, u, 1, y0 + h, stp(trim_st, OPPOSITE[face], "top"))
            fset(bp, face, line, u, 1, y0, stp(trim_st, OPPOSITE[face]))
            if (u - a) % 6 == 3:
                A.buttress(bp, face, line, u, y0, h - 1, A.as_pal(trim).pick(ox, 0, oz), trim_st, 2)


def timber_storey(bp, x0, z0, x1, z1, y0, y1, log, infill, *, glass="glass_pane", post_every=3, wood=None,
                  windows=True, faces=("north", "south", "east", "west")):
    """Half-timbered storey: log posts + braces, plaster infill, framed windows with shutters."""
    infill = A.as_pal(infill)
    sides = {"north": (z0, x0, x1), "south": (z1, x0, x1), "west": (x0, z0, z1), "east": (x1, z0, z1)}
    for face in faces:
        line, a, b = sides[face]
        for u in range(a, b + 1):
            for y in range(y0, y1 + 1):
                pset(bp, face, line, u, 0, y, infill)
        ax = "x" if face in ("north", "south") else "z"
        for u in range(a, b + 1):
            fset(bp, face, line, u, 0, y0, with_props(log, axis=ax))
            fset(bp, face, line, u, 0, y1, with_props(log, axis=ax))
        posts = list(range(a, b + 1, post_every))
        if posts[-1] != b:
            posts.append(b)
        for k, u in enumerate(posts):
            for y in range(y0, y1 + 1):
                fset(bp, face, line, u, 0, y, with_props(log, axis="y"))
        for k, (pa, pb) in enumerate(zip(posts, posts[1:])):
            mid = (pa + pb) // 2
            if windows and k % 2 == 0 and pb - pa >= 3:
                for y in range(y0 + 1, y1):
                    fset(bp, face, line, mid, 0, y, glass)
                if wood:
                    shutters(bp, face, line, mid, y0 + 1, y1 - y0 - 1, wood)
            elif pb - pa >= 2:
                # diagonal brace
                fset(bp, face, line, pa + 1, 0, y0 + 1, with_props(log, axis=ax))
                fset(bp, face, line, pb - 1, 0, y1 - 1, with_props(log, axis=ax))


def pave(bp, x0, z0, x1, z1, y, pal, chance=1.0, seed=0, keep=False):
    rng = random.Random(seed)
    pal = A.as_pal(pal)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if rng.random() < chance:
                bp.set(x, y, z, pal.pick(x, y, z), keep=keep)


def path_line(bp, pts, y, pal, width=3, seed=0):
    rng = random.Random(seed)
    pal = A.as_pal(pal)
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            for dx in range(-(width // 2), width - width // 2):
                for dz in range(-(width // 2), width - width // 2):
                    if rng.random() < 0.92:
                        bp.set(x + dx, y, z + dz, pal.pick(x + dx, y, z + dz))


def lamp_post(bp, x, y, z, post="dark_oak_fence", h=3, soul=False, base=None):
    if base:
        bp.set(x, y, z, base)
        y += 1
    bp.fill(x, y, z, x, y + h - 1, z, post)
    bp.lantern(x, y + h, z, soul=soul)


def banner_pole(bp, x, y, z, color, h=5, rot=0, post="dark_oak_fence"):
    bp.fill(x, y, z, x, y + h - 1, z, post)
    bp.set(x, y + h, z, f"{color}_banner[rotation={rot}]")


def skirt(bp, y=0, depth=7, spread=3, seed=0, top="grass_block[snowy=false]", rock="stone"):
    A.terrain_skirt(bp, A.footprint_of(bp, y), y, depth=depth, spread=spread, seed=seed, top=top, rock=rock)


def door_in(bp, face, line, u, y, wood, steps=None):
    for dy in (1, 2):
        fset(bp, face, line, u, 0, y + dy, "air")
    x, z = pos(face, line, u, 0)
    bp.door(x, y + 1, z, face, wood)
    if steps:
        fset(bp, face, line, u, 1, y, stp(steps, OPPOSITE[face]))


def round_ring(cx, cz, r):
    pts = set()
    for a in range(0, 360, 3):
        pts.add((cx + round(math.cos(math.radians(a)) * r), cz + round(math.sin(math.radians(a)) * r)))
    return pts


def rock_cliff(bp, cx, cz, rx, rz, y_top, depth, pal, seed=0, top=None, noise=1.5):
    """Irregular rocky mass whose top surface is at y_top (with noisy edges)."""
    rng = random.Random(seed)
    pal = A.as_pal(pal)
    for x in range(cx - rx - 3, cx + rx + 4):
        for z in range(cz - rz - 3, cz + rz + 4):
            d = math.hypot((x - cx) / rx, (z - cz) / rz)
            n = math.sin(x * 0.7 + seed) * 0.08 + math.cos(z * 0.6 + seed * 2) * 0.08 + rng.uniform(-0.05, 0.05)
            if d + n > 1.0:
                continue
            h = y_top - int(max(0.0, (d + n - 0.55)) * noise * 8)
            for y in range(y_top - depth, h + 1):
                bp.set(x, y, z, pal.pick(x, y, z))
            if top and h == y_top:
                bp.set(x, h, z, top)


def _face_to(cx, cz, x, z):
    """Horizontal direction pointing from (x, z) toward the centre."""
    dx, dz = cx - x, cz - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _dist(dx, dz, shape):
    if shape == "square":
        return max(abs(dx), abs(dz))
    if shape == "octagon":
        return max(abs(dx), abs(dz), (abs(dx) + abs(dz)) / 1.42)
    return math.hypot(dx, dz)


def cone(bp, cx, cz, y, r, R, h=None, finial="lightning_rod[facing=up,powered=false,waterlogged=false]",
         hollow=True, only=None, shape="round"):
    """Smooth steep cone/spire roof (stairs on the skin, full blocks below), r = base radius.
    shape: round, octagon or square."""
    full, st, sl = R
    h = h or int(r * 2.8) + 2
    for k in range(h):
        rr = (r + 0.4) * (1 - k / h)
        if rr < 0.45:
            break
        for x in range(cx - r - 2, cx + r + 3):
            for z in range(cz - r - 2, cz + r + 3):
                d = _dist(x - cx, z - cz, shape)
                if d > rr or (only and not only(x, z)):
                    continue
                if d > rr - 1.0:
                    rr_next = (r + 0.4) * (1 - (k + 1) / h)
                    bp.set(x, y + k, z, stp(st, _face_to(cx, cz, x, z)) if d > rr_next else full)
                elif d > rr - 2.0 or not hollow:
                    bp.set(x, y + k, z, full)
                else:
                    bp.set(x, y + k, z, "air")
    top = y + k
    bp.set(cx, top, cz, full)
    bp.set(cx, top + 1, cz, "wayfarers:polished_guild_stone_slab[type=bottom,waterlogged=false]"
           if finial is None else finial)
    return top + 1


def rtower(bp, cx, cz, y0, h, r, wall, R, *, floor="spruce_planks", corbel=None, trim=None, ladder=True,
           floors_every=6, lights=True, slits=True, cone_h=None, crown="cone", parapet=None):
    """Round tower with corbelled eave and a sharp cone roof (crown='cone') or crenellations ('crenels')."""
    wall = A.as_pal(wall)
    for y in range(y0, y0 + h + 1):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.4:
                    bp.set(x, y, z, wall.pick(x, y, z) if d > r - 0.8 else "air")
    bp.disk(cx, y0, cz, r, floor)
    for fy in range(y0 + floors_every, y0 + h - 1, floors_every):
        bp.disk(cx, fy, cz, r - 1, floor)
        if lights:
            bp.chain(cx, fy - 1, cz, fy - 1)
            bp.lantern(cx, fy - 2, cz, hanging=True)
    if ladder:
        bp.ladder(cx, y0 + 1, cz - r + 1, y0 + h, "south")
    if slits:
        for i, fy in enumerate(range(y0 + 3, y0 + h - 2, 4)):
            a = math.radians(i * 70 + 30)
            x, z = cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)
            bp.set(x, fy, z, "glass_pane")
            bp.set(x, fy + 1, z, "glass_pane")
    top = y0 + h
    if trim:
        for (x, z) in round_ring(cx, cz, r):
            bp.set(x, top, z, A.as_pal(trim).pick(x, top, z))
    if corbel:
        for (x, z) in round_ring(cx, cz, r + 1):
            if math.hypot(x - cx, z - cz) > r + 0.5:
                bp.set(x, top, z, stp(corbel, OPPOSITE[_face_to(cx, cz, x, z)], "top"))
    if crown == "crenels":
        bp.disk(cx, top + 1, cz, r + 1, A.as_pal(trim or wall).pick(cx, top, cz))
        bp.disk(cx, top + 1, cz, r - 1, floor)
        k = 0
        for (x, z) in sorted(round_ring(cx, cz, r + 1), key=lambda p: math.atan2(p[1] - cz, p[0] - cx)):
            k += 1
            bp.set(x, top + 2, z, (parapet or wall).pick(x, top + 2, z) if k % 2 and hasattr(parapet or wall, "pick")
                   else slb(R[2]))
        if ladder:
            bp.set(cx, top + 1, cz - r + 1, "ladder[facing=south,waterlogged=false]")
            bp.set(cx, top, cz - r + 1, "ladder[facing=south,waterlogged=false]")
        return top + 2
    bp.disk(cx, top + 1, cz, r + 1, R[0])
    bp.disk(cx, top + 1, cz, r - 1, floor)
    if crown == "spire":
        return spire2(bp, cx, cz, top + 2, r + 1, R, steep=max(2, round((cone_h or 2 * r) / (r + 1))),
                      shape="round", tip=2)
    return cone(bp, cx, cz, top + 2, r + 1, R, h=cone_h)


def lean_to(bp, face, line, u0, u1, y, depth, R, *, under=None, overhang=1):
    """Single-pitch roof: low eave on the `face` side at wall plane `line`, rising one block per
    row toward the inside for `depth` rows (overhang rows extend outward)."""
    full, st, sl = R
    for k in range(-overhang, depth):
        yy = y + k + overhang
        for u in range(u0, u1 + 1):
            fset(bp, face, line, u, -k, yy, stp(st, OPPOSITE[face]))
            if k > -overhang:
                fset(bp, face, line, u, -k, yy - 1, full)
    if under:
        for u in range(u0, u1 + 1):
            fset(bp, face, line, u, overhang, y - 1, stp(under, face, "top"))


def arcade(bp, face, line, u0, u1, y0, h, col, arch_st, *, every=3, cap=None):
    """Open arcade in a wall plane: columns every `every`, small pointed arches between them."""
    s = side_of(face)
    for u in range(u0, u1 + 1):
        for y in range(y0 + 1, y0 + h + 2):
            fset(bp, face, line, u, 0, y, "air")
    cols = list(range(u0, u1 + 1, every))
    if cols[-1] != u1:
        cols.append(u1)
    for u in cols:
        for y in range(y0 + 1, y0 + h + 1):
            fset(bp, face, line, u, 0, y, col if y < y0 + h else (cap or col))
    for a, b in zip(cols, cols[1:]):
        fset(bp, face, line, a + 1, 0, y0 + h, stp(arch_st, OPPOSITE[s], "top"))
        fset(bp, face, line, b - 1, 0, y0 + h, stp(arch_st, s, "top"))
        for u in range(a, b + 1):
            fset(bp, face, line, u, 0, y0 + h + 1, cap or col)


def pinnacle(bp, x, y, z, block, R, h=3):
    """Small gothic pinnacle: shaft of `h` blocks topped by a tiny spire and a rod."""
    for k in range(h):
        bp.set(x, y + k, z, block)
    return cone(bp, x, z, y + h, 1, R, h=3, shape="square")


def spire2(bp, cx, cz, y, r, R, steep=2, shape="octagon", tip=3, rod=True, ribbed=True):
    """Regular stepped spire: every ring is `steep` rows tall (full blocks then a row of stairs on the
    edge), shrinking by one per ring, finished with a slender tip. Returns the top y."""
    full, st, sl = R
    lim = {"octagon": 0.3, "square": 0.0, "round": 0.35}[shape]
    yy = y
    for rr in range(r, 0, -1):
        for k in range(steep):
            for x in range(cx - rr - 1, cx + rr + 2):
                for z in range(cz - rr - 1, cz + rr + 2):
                    d = _dist(x - cx, z - cz, shape)
                    if d > rr + lim:
                        continue
                    edge = d > rr - 1 + lim
                    if edge and (k == steep - 1 or (ribbed and k > 0)):
                        bp.set(x, yy, z, stp(st, _face_to(cx, cz, x, z)))
                    elif edge or k == 0:
                        bp.set(x, yy, z, full)
                    else:
                        bp.set(x, yy, z, "air")
            yy += 1
    for k in range(tip):
        bp.set(cx, yy + k, cz, full)
    if rod:
        bp.set(cx, yy + tip, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return yy + tip


# ================================================================== GUILD OUTPOST
OUTPOST_STYLES = {
    # roof tiles, timber log, wood set, plaster infill, banner colour, awning stripes
    "azure": dict(roof="azure", log="dark_oak_log", wood="spruce", plaster={"calcite": 4, "polished_diorite": 1},
                  banner="blue", carpet="blue_carpet", awning=("blue_wool", "white_wool"), glass="light_blue"),
    "crimson": dict(roof="crimson", log="stripped_spruce_log", wood="oak",
                    plaster={"smooth_sandstone": 3, "sandstone": 1},
                    banner="red", carpet="red_carpet", awning=("red_wool", "yellow_wool"), glass="orange"),
    "slate": dict(roof="slate", log="dark_oak_log", wood="pale_oak", plaster={"pale_oak_planks": 4,
                                                                               "stripped_pale_oak_wood": 1},
                  banner="green", carpet="green_carpet", awning=("green_wool", "white_wool"), glass="lime"),
}


def guild_outpost(style):
    S = OUTPOST_STYLES[style]

    def build(bp):
        R = ROOF[S["roof"]]
        log, wood = S["log"], S["wood"]
        planks, wst, fence = f"{wood}_planks", f"{wood}_stairs", f"{wood}_fence"
        wall = Palette({GB: 10, MGB: 2, CRGB: 1}, seed=3)
        stone = Palette({"stone_bricks": 6, "tuff_bricks": 3, "andesite": 1, "mossy_stone_bricks": 2, "cobblestone": 1},
                        seed=5, scale=2.5)
        base = Palette({"tuff_bricks": 3, "polished_tuff": 1}, seed=7)
        plaster = Palette(S["plaster"], seed=11)
        banner = S["banner"]
        stained = f"{S['glass']}_stained_glass_pane"

        # ---------------------------------------------------------- ground: courtyard paving
        yard = Palette({"gravel": 2, "coarse_dirt": 2, "dirt_path": 3, "cobblestone": 1, "grass_block[snowy=false]": 3},
                       seed=21, scale=2.0)
        pave(bp, 4, 4, 42, 42, 0, yard)
        plaza = Palette({"stone_bricks": 4, "polished_andesite": 2, "cracked_stone_bricks": 1, PGS: 1}, seed=22)
        mx, mz = 23, 31   # waystone monument
        for x in range(14, 33):
            for z in range(22, 41):
                if math.hypot(x - mx, z - mz) <= 7.5:
                    bp.set(x, 0, z, plaza.pick(x, 0, z))
        path_line(bp, [(50, 30), (30, 30)], 0, plaza, width=5)
        path_line(bp, [(21, 25), (21, 22)], 0, plaza, width=5)

        # ---------------------------------------------------------- curtain wall + corner towers
        curtain(bp, 3, 3, 43, 43, 0, 7, stone, base, "tuff_brick_stairs",
                skip=[(36, 24, 47, 36), (33, 3, 45, 19), (20, 39, 26, 46)])
        # mid-wall tower breaking the long south curtain
        qx0, qx1, qz0, qz1 = 20, 26, 39, 45
        bp.clear(qx0 + 1, 1, qz0 + 1, qx1 - 1, 11, qz1 - 1)
        for face, line, a, b in (("south", qz1, qx0, qx1), ("east", qx1, qz0, qz1), ("west", qx0, qz0, qz1),
                                 ("north", qz0, qx0, qx1)):
            A.facade(bp, face, line, a, b, 0, 11, stone, base, pilaster_every=6, window_y=6, window_h=2,
                     plinth=base, plinth_stairs="tuff_brick_stairs", cornice_stairs="tuff_brick_stairs",
                     sill="tuff_brick_stairs")
        bp.fill(qx0 + 1, 6, qz0 + 1, qx1 - 1, 6, qz1 - 1, planks)
        bp.fill(qx0, 12, qz0, qx1, 12, qz1, R[0])
        A.spire(bp, (qx0 + qx1) // 2, (qz0 + qz1) // 2, 13, 3, R[0], R[1], steep=2, round_=False)
        door_in(bp, "north", qz0, 23, 0, "spruce")
        bp.ladder(qx0 + 1, 1, qz1 - 1, 11, "north")
        bp.set(qx0 + 1, 6, qz1 - 1, "ladder[facing=north,waterlogged=false]")
        for u in (22, 24):
            A.banner_wall(bp, u, 9, qz1 + 1, "south", banner)
            A.banner_wall(bp, u, 8, qz1 + 1, "south", banner)
        wall_lamp(bp, "south", qz1, 23, 4, "tuff_brick_stairs")
        A.furnish(bp, qx0 + 1, 7, qz0 + 1, qx1 - 1, qz1 - 1, "bedroom", wood=wood)
        A.stair_run(bp, 5, 1, 19, "north", 7, 2, "tuff_brick_stairs", fill="tuff_bricks", clear=3)
        for cx, cz, crown in ((4, 4, "spire"), (4, 42, "spire"), (42, 42, "crenels")):
            top = rtower(bp, cx, cz, 0, 11, 3, stone, R, trim=base, floor=planks, corbel="tuff_brick_stairs",
                         crown=crown, floors_every=5, cone_h=11)
            dx = 1 if cx < 23 else -1
            dz = 1 if cz < 23 else -1
            for k in (2, 3):
                bp.set(cx + dx * k, 1, cz + dz * k, "air")
                bp.set(cx + dx * k, 2, cz + dz * k, "air")
            if crown == "crenels":
                banner_pole(bp, cx, top - 1, cz, banner, h=3, post=fence)

        # ---------------------------------------------------------- gatehouse (east)
        gx0, gx1, gz0, gz1, gc = 36, 45, 25, 35, 30
        bp.clear(gx0 + 1, 1, gz0 + 1, gx1 - 1, 12, gz1 - 1)
        for face, line, a, b in (("east", gx1, gz0, gz1), ("west", gx0, gz0, gz1), ("north", gz0, gx0, gx1),
                                 ("south", gz1, gx0, gx1)):
            A.facade(bp, face, line, a, b, 0, 12, wall, base, pilaster_every=5, window_y=7, window_h=2,
                     plinth=base, plinth_stairs="tuff_brick_stairs", cornice_stairs=GB_ST, sill=GB_ST)
        bp.fill(gx0 + 1, 6, gz0 + 1, gx1 - 1, 6, gz1 - 1, planks)
        pave(bp, gx0 + 1, gz0 + 1, gx1 - 1, gz1 - 1, 12, base)
        bp.clear(gx0 - 1, 1, gc - 1, gx1 + 1, 5, gc + 1)
        pave(bp, gx0 - 1, gc - 2, gx1 + 2, gc + 2, 0, plaza)
        for face, line in (("east", gx1), ("west", gx0)):
            A.arch_door(bp, face, line, gc, 0, width=3, height=4, trim=PGS, stairs=PGS_ST)
            fset(bp, face, line, gc, 0, 8, CGS)
            fset(bp, face, line, gc, 1, 8, CGS)
        for z in range(gc - 1, gc + 2):
            bp.set(gx1 - 1, 5, z, "iron_bars")    # raised portcullis
            bp.set(gx0 + 2, 5, z, "iron_bars")
        # crenellated roof terrace
        for x in range(gx0, gx1 + 1):
            for z in (gz0, gz1):
                bp.set(x, 13, z, wall.pick(x, 13, z) if x % 2 == 0 else slb(GB_SL))
        for z in range(gz0, gz1 + 1):
            for x in (gx0, gx1):
                bp.set(x, 13, z, wall.pick(x, 13, z) if z % 2 == 0 else slb(GB_SL))
        for tz in (gz0, gz1):
            rtower(bp, gx1, tz, 0, 16, 2, wall, R, trim=base, floor=planks, corbel=GB_ST, ladder=False,
                   lights=False, floors_every=5, cone_h=10, crown="spire")
        banner_pole(bp, gx0 + 2, 13, gc, banner, h=4, post=fence)
        for u in (gc - 3, gc + 3):
            A.banner_wall(bp, gx1 + 1, 10, u, "east", banner)
            A.banner_wall(bp, gx1 + 1, 9, u, "east", banner)
            wall_lamp(bp, "east", gx1, u, 4, GB_ST)
            wall_lamp(bp, "west", gx0, u, 4, GB_ST)
        bp.chest(gx0 + 1, 7, gz0 + 1, "south", LOOT + "guild_outpost")
        bp.ladder(gx0 + 1, 1, gz1 - 1, 12, "north")
        A.furnish(bp, gx0 + 3, 7, gz0 + 1, gx1 - 2, gz0 + 3, "armory", wood=wood)
        bp.bed(gx1 - 2, 7, gz1 - 3, "south", banner)
        bp.bed(gx1 - 4, 7, gz1 - 3, "south", banner)
        bp.lantern(gc + 8, 11, gc, hanging=True)

        # ---------------------------------------------------------- the grand hall (north)
        hx0, hx1, hz0, hz1 = 9, 31, 8, 20
        bp.clear(hx0 + 1, 1, hz0 + 1, hx1 - 1, 11, hz1 - 1)
        for face, line, a, b in (("south", hz1, hx0, hx1), ("north", hz0, hx0, hx1), ("west", hx0, hz0, hz1),
                                 ("east", hx1, hz0, hz1)):
            A.facade(bp, face, line, a, b, 0, 5, wall, base, pilaster_every=4, window_y=2, window_h=2,
                     plinth=base, plinth_stairs="tuff_brick_stairs", sill=GB_ST, cornice_stairs=GB_ST)
        # jettied half-timbered upper storey on carved corbels
        timber_storey(bp, hx0 - 1, hz0 - 1, hx1 + 1, hz1 + 1, 6, 11, log, plaster, wood=wood if wood != "pale_oak"
                      else "dark_oak")
        for x in range(hx0 - 1, hx1 + 2):
            bp.set(x, 5, hz0 - 1, stp(wst, "south", "top"))
            bp.set(x, 5, hz1 + 1, stp(wst, "north", "top"))
        for z in range(hz0 - 1, hz1 + 2):
            bp.set(hx0 - 1, 5, z, stp(wst, "east", "top"))
            bp.set(hx1 + 1, 5, z, stp(wst, "west", "top"))
        # gallery (north + west) inside
        bp.fill(hx0, 6, hz0, hx1, 6, hz0 + 3, planks)
        bp.fill(hx0, 6, hz0, hx0 + 2, 6, hz1, planks)
        for x in range(hx0 + 3, hx1):
            bp.set(x, 7, hz0 + 4, fence)
        for z in range(hz0 + 4, hz1):
            bp.set(hx0 + 3, 7, z, fence)
        ridge = roof(bp, hx0 - 1, hz0 - 1, hx1 + 1, hz1 + 1, 12, R, axis="x", overhang=1, steep=1.25,
                     gable=plaster, under=wst)
        # exposed timber on the gables + gable windows
        gnames = {A.as_pal(k).items[0][0] for k in S["plaster"]}
        gnames = {("minecraft:" + n) if ":" not in n else n for n in gnames}
        for z in range(hz0, hz1 + 1):
            for x in (hx0 - 1, hx1 + 1):
                if (z - hz0) % 3 == 0:
                    for y in range(12, ridge):
                        if bp.get(x, y, z) in gnames or (bp.get(x, y, z) or "").endswith(("calcite", "diorite",
                                                                                          "sandstone", "wood")):
                            bp.set(x, y, z, with_props(log, axis="y"))
            for x in (hx0 - 1, hx1 + 1):
                for y in range(12, ridge):
                    b = bp.get(x, y, z) or ""
                    if b.endswith(("_stairs",)) is False and y == 12:
                        bp.set(x, y, z, with_props(log, axis="z"))
        for x in (hx0 - 1, hx1 + 1):
            for dz in (-1, 0, 1):
                bp.set(x, 15, (hz0 + hz1) // 2 + dz, stained)
                bp.set(x, 16, (hz0 + hz1) // 2 + dz, stained)
        for u in (11, 28):
            dormer(bp, "south", hz1 + 1, u, 12, R, plaster, trim=with_props(log, axis="y"), glass=stained)
            dormer(bp, "north", hz0 - 1, u, 12, R, plaster, trim=with_props(log, axis="y"))
        # cross-gabled entrance wing in stone with a great window
        cx0, cx1, cz0, cz1, cc = 16, 24, 20, 26, 20
        bp.clear(cx0 + 1, 1, cz0, cx1 - 1, 12, cz1 - 1)
        for face, line, a, b in (("south", cz1, cx0, cx1), ("west", cx0, cz0 + 1, cz1), ("east", cx1, cz0 + 1, cz1)):
            A.facade(bp, face, line, a, b, 0, 12, wall, PGS, pilaster_every=8 if face == "south" else 5,
                     window_y=7, window_h=0 if face == "south" else 3, plinth=base,
                     plinth_stairs="tuff_brick_stairs", sill=GB_ST, cornice_stairs=PGS_ST)
        bp.clear(cx0 + 1, 1, hz1 - 1, cx1 - 1, 11, hz1 + 1)
        A.arch_door(bp, "south", cz1, cc, 0, width=3, height=4, trim=PGS, stairs=PGS_ST, door=wood if wood != "pale_oak"
                    else "spruce", steps="tuff_brick_stairs", steps_n=1)
        gwindow(bp, "south", cz1, cc, 7, 3, stained, PGS, PGS_ST, w=3, sill=PGS_ST)
        roof(bp, cx0, cz0 - 3, cx1, cz1, 13, R, axis="z", overhang=1, steep=1.25, gable=wall, under=wst)
        rose(bp, "south", cz1, cc, 17, 1, PGS, [stained], center=stained)
        bp.set(cc, 21, cz1 + 1, CGS)
        for u in (cc - 2, cc + 2):
            A.banner_wall(bp, u, 5, cz1 + 1, "south", banner)
        for u in (cx0, cx1):
            wall_lamp(bp, "south", cz1, u, 4, PGS_ST)
        # chimney stacks (west gable + north slope)
        for (x0, z0, x1, z1) in ((hx0 - 2, 13, hx0 - 1, 15), (25, hz0 - 3, 26, hz0 - 2)):
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    for y in range(0, ridge + 3):
                        bp.set(x, y, z, "polished_tuff" if y % 5 == 4 else base.pick(x, y, z))
                    bp.set(x, ridge + 3, z, "tuff_brick_wall")
            bp.set(x0, ridge + 2, z0, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
            bp.set(x0, ridge + 3, z0, "air")
        for z in (13, 14, 15):
            bp.set(hx0, 1, z, "campfire[lit=false,signal_fire=false,waterlogged=false,facing=east]")
            bp.set(hx0, 2, z, "air")
            bp.set(hx0, 3, z, "air")
            bp.set(hx0 + 1, 4, z, stp("tuff_brick_stairs", "east", "top"))
            bp.set(hx0 - 1, 1, z, "tuff_bricks")
        bp.set(hx0, 1, 14, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=east]")
        # hall interior: floor, feasting table, benches, chandeliers, banners, guild desk
        floor = Palette({planks: 3, "polished_tuff" if wood == "pale_oak" else "spruce_planks"
                         if wood != "spruce" else "dark_oak_planks": 1}, seed=31)
        for x in range(hx0 + 1, hx1):
            for z in range(hz0 + 1, hz1):
                bp.set(x, 0, z, floor.pick(x, 0, z))
        for x in range(hx0 + 6, hx1 - 3):
            bp.set(x, 1, 15, fence)
            bp.set(x, 2, 15, S["carpet"])
            bp.stairs(x, 1, 14, wst, "south")
            bp.stairs(x, 1, 16, wst, "north")
        for x in range(hx0 + 7, hx1 - 3, 5):
            bp.set(x, 3, 15, "candle[candles=3,lit=true,waterlogged=false]")
            bp.chain(x, 8, 15, ridge - 1)
            A.chandelier(bp, x, 8, 15)
        bp.set(hx1 - 2, 1, 15, "lectern[facing=west,has_book=false,powered=false]")
        bp.set(hx1 - 1, 1, 12, "cartography_table")
        bp.chest(hx1 - 1, 1, 18, "west", LOOT + "guild_outpost")
        bp.set(hx1 - 1, 1, 17, "barrel[facing=up,open=false]")
        for x in range(hx0 + 5, hx1 - 1, 4):
            A.banner_wall(bp, x, 4, hz1 - 1, "north", banner)
        A.furnish(bp, hx0 + 4, 7, hz0, hx1 - 1, hz0 + 1, "library", wood=wood)
        for i in range(6):
            bp.stairs(hx1 - 1 - i, 1 + i, hz0 + 1, wst, "west")
        bp.fill(hx1 - 6, 6, hz0 + 1, hx1 - 1, 6, hz0 + 1, "air")
        bp.fill(hx1 - 6, 7, hz0 + 1, hx1 - 1, 8, hz0 + 1, "air")

        # ---------------------------------------------------------- map tower (north-east)
        tcx, tcz = 38, 11
        mt = Palette({GB: 8, MGB: 1, CRGB: 1}, seed=41)
        rtower(bp, tcx, tcz, 0, 27, 5, mt, R, trim=PGS, floor=planks, corbel=PGS_ST, floors_every=6, cone_h=17,
               crown="spire")
        for (x, z) in round_ring(tcx, tcz, 6):
            bp.set(x, 0, z, base.pick(x, 0, z))
            bp.set(x, 1, z, stp("tuff_brick_stairs", OPPOSITE[_face_to(tcx, tcz, x, z)]))
            for y in (8, 14, 20):
                bp.set(x, y, z, stp(PGS_ST, OPPOSITE[_face_to(tcx, tcz, x, z)], "top"))
        for k in range(8):
            a = math.radians(k * 45 + 22)
            x, z = tcx + round(math.cos(a) * 5), tcz + round(math.sin(a) * 5)
            for y in range(22, 26):
                bp.set(x, y, z, stained if k % 2 else "glass_pane")
        bp.clear(tcx - 5, 1, tcz, tcx - 5, 2, tcz)
        bp.door(tcx - 5, 1, tcz, "west", "spruce")
        bp.clear(hx1, 1, tcz, hx1 + 2, 2, tcz)
        bp.door(hx1, 1, tcz, "east", "spruce")
        bp.fill(hx1 + 1, 0, tcz, tcx - 6, 0, tcz, PGS)
        # secret guild vault under the map tower (hidden trapdoor beside the ladder)
        bp.clear(36, -4, 9, 40, -1, 13)
        for x in range(35, 42):
            for z in range(8, 15):
                for y in range(-5, 0):
                    if x in (35, 41) or z in (8, 14) or y == -5:
                        bp.set(x, y, z, base.pick(x, y, z))
        bp.ladder(40, -4, 11, -1, "west")
        bp.set(40, 0, 11, "spruce_trapdoor[facing=west,half=top,open=false,powered=false,waterlogged=false]")
        bp.chest(36, -4, 11, "east", LOOT + "guild_outpost")
        bp.set(36, -4, 9, "gold_block")
        bp.set(36, -4, 13, "barrel[facing=up,open=false]")
        bp.set(37, -4, 9, "barrel[facing=up,open=false]")
        bp.set(38, -2, 11, "lantern[hanging=true,waterlogged=false]")
        bp.set(38, -1, 11, "iron_chain[axis=y,waterlogged=false]")
        bp.set(37, -4, 13, f"{banner}_carpet")
        # map room on the top floor
        bp.set(tcx + 2, 25, tcz, "cartography_table")
        bp.set(tcx - 2, 25, tcz + 2, "lectern[facing=north,has_book=false,powered=false]")
        bp.chest(tcx + 2, 25, tcz + 2, "west", LOOT + "guild_outpost")
        bp.set(tcx + 3, 25, tcz - 1, "bookshelf")
        bp.set(tcx + 3, 25, tcz + 1, "bookshelf")
        bp.set(tcx, 25, tcz + 3, S["carpet"])
        bp.set(tcx + 1, 25, tcz + 3, S["carpet"])
        for y in (17, 18):
            A.banner_wall(bp, tcx, y, tcz + 6, "south", banner)
            A.banner_wall(bp, tcx + 6, y, tcz, "east", banner)

        # ---------------------------------------------------------- waystone monument
        for (x, z) in round_ring(mx, mz, 4):
            bp.set(x, 1, z, stp(PGS_ST, _face_to(mx, mz, x, z)))
        bp.disk(mx, 1, mz, 3, PGS)
        for (x, z) in round_ring(mx, mz, 3):
            bp.set(x, 2, z, stp(GB_ST, _face_to(mx, mz, x, z)))
        bp.disk(mx, 2, mz, 2, GB)
        bp.set(mx, 3, mz, CGS)
        bp.set(mx, 4, mz, MOD["waystone"])
        for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            bp.fill(mx + dx, 3, mz + dz, mx + dx, 7, mz + dz, GB_WALL)
            bp.set(mx + dx, 3, mz + dz, PGS)
        for x in range(mx - 2, mx + 3):
            for z in range(mz - 2, mz + 3):
                if x in (mx - 2, mx + 2) or z in (mz - 2, mz + 2):
                    bp.set(x, 8, z, PGS)
        for x in range(mx - 3, mx + 4):
            bp.set(x, 8, mz - 3, stp(PGS_ST, "south", "top"))
            bp.set(x, 8, mz + 3, stp(PGS_ST, "north", "top"))
        for z in range(mz - 2, mz + 3):
            bp.set(mx - 3, 8, z, stp(PGS_ST, "east", "top"))
            bp.set(mx + 3, 8, z, stp(PGS_ST, "west", "top"))
        cone(bp, mx, mz, 9, 3, R, h=8)
        bp.set(mx, 8, mz, RUNE)
        bp.chain(mx, 7, mz, 7)
        bp.lantern(mx, 6, mz, hanging=True)
        for dx, dz, rot in ((-5, 0, 4), (5, 0, 12), (0, 5, 0), (0, -5, 8)):
            banner_pole(bp, mx + dx, 1, mz + dz, banner, h=4, rot=rot, post=fence)
        for dx, dz in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
            lamp_post(bp, mx + dx, 1, mz + dz, post=fence, h=3, base=PGS)

        # ---------------------------------------------------------- stables (west)
        sx0, sx1, sz0, sz1 = 5, 12, 21, 35
        bp.fill(sx0, 0, sz0, sx1, 0, sz1, "coarse_dirt")
        for z in range(sz0, sz1 + 1):
            for y in range(1, 5):
                bp.set(sx0, y, z, stone.pick(sx0, y, z))
        for z in range(sz0, sz1 + 1, 3):
            for y in range(1, 5):
                bp.set(sx1, y, z, with_props(log, axis="y"))
            bp.set(sx1 - 1, 4, z, stp(wst, "east", "top"))
        for x in range(sx0, sx1 + 1):
            for zz in (sz0, sz1):
                for y in range(1, 5):
                    bp.set(x, y, zz, plaster.pick(x, y, zz) if 0 < x - sx0 < sx1 - sx0 else with_props(log, axis="y"))
        for z in range(sz0, sz1 + 1):
            bp.set(sx1, 5, z, with_props(log, axis="z"))
            bp.set(sx0, 5, z, with_props(log, axis="z"))
        roof(bp, sx0, sz0, sx1, sz1, 6, R, axis="z", overhang=1, steep=1.0, gable=plaster, under=wst)
        for z in range(sz0 + 3, sz1, 3):
            for x in range(sx0 + 1, sx1 - 2):
                bp.set(x, 1, z, fence)
            bp.set(sx0 + 1, 1, z + 1, "hay_block[axis=y]")
            bp.set(sx0 + 1, 2, z + 1, "hay_block[axis=x]")
            bp.set(sx0 + 1, 1, z - 1, "cauldron")
            bp.lantern(sx0 + 3, 4, z + 1, hanging=True)
        bp.barrel(sx0 + 1, 1, sz0 + 1, "up")
        bp.set(sx0 + 2, 1, sz0 + 1, "hay_block[axis=y]")
        bp.set(sx0 + 1, 1, sz1 - 1, "hay_block[axis=y]")
        bp.set(sx0 + 2, 1, sz1 - 1, "hay_block[axis=z]")
        bp.set(sx0 + 1, 2, sz1 - 1, "hay_block[axis=y]")
        for z in range(sz0 + 1, sz1, 4):
            bp.set(sx1 + 1, 1, z, "cauldron")

        # ---------------------------------------------------------- market stall (south)
        kx0, kx1, kz0, kz1 = 27, 34, 36, 40
        for x in (kx0, kx1):
            for z in (kz0, kz1):
                bp.fill(x, 1, z, x, 3, z, fence)
        aw1, aw2 = S["awning"]
        for x in range(kx0 - 1, kx1 + 2):
            for i, z in enumerate(range(kz0 - 1, kz1 + 2)):
                bp.set(x, 4 + (1 if 2 <= i <= 4 else 0), z, aw1 if x % 2 else aw2)
        for x in range(kx0 + 1, kx1):
            bp.set(x, 1, kz0, "barrel[facing=up,open=false]" if x % 3 else planks)
            bp.set(x, 2, kz0, f"{'spruce' if wood == 'pale_oak' else wood}_pressure_plate[powered=false]")
        bp.set(kx0 + 1, 1, kz1, "pumpkin")
        bp.set(kx0 + 2, 1, kz1, "melon")
        bp.set(kx0 + 3, 1, kz1, "hay_block[axis=y]")
        bp.set(kx1 - 1, 1, kz1, "composter[level=6]")
        bp.barrel(kx1 - 2, 1, kz1, "up")
        bp.set(kx0 + 2, 2, kz0, "decorated_pot[cracked=false,facing=south,waterlogged=false]")
        bp.set(kx1 - 2, 2, kz0, "potted_red_tulip")
        bp.chain(kx0 + 3, 4, kz0 + 2, 4)
        bp.lantern(kx0 + 3, 3, kz0 + 2, hanging=True)
        for (x, z) in ((kx1 + 2, kz1), (kx1 + 2, kz1 - 1), (kx1 + 3, kz1)):
            bp.barrel(x, 1, z, "up")
        bp.set(kx1 + 2, 2, kz1, "barrel[facing=north,open=false]")

        # ---------------------------------------------------------- herb garden + well (south-west)
        gdx0, gdx1, gdz0, gdz1 = 11, 19, 36, 41
        for x in range(gdx0, gdx1 + 1):
            for z in range(gdz0, gdz1 + 1):
                if x in (gdx0, gdx1) or z in (gdz0, gdz1):
                    bp.set(x, 0, z, "grass_block[snowy=false]")
                    if (x + z) % 3 and z != gdz0 or (z == gdz0 and x % 4 == 0):
                        bp.set(x, 1, z, leaves("azalea_leaves" if (x * z) % 5 else "flowering_azalea_leaves"))
                elif x == 15:
                    bp.set(x, 0, z, "water")
                elif z == gdz0 + 2:
                    bp.set(x, 0, z, "grass_block[snowy=false]")
                    bp.set(x, 1, z, ("rose_bush[half=lower]", "peony[half=lower]", "lilac[half=lower]")[x % 3])
                    bp.set(x, 2, z, ("rose_bush[half=upper]", "peony[half=upper]", "lilac[half=upper]")[x % 3])
                else:
                    bp.set(x, 0, z, "farmland[moisture=7]")
                    bp.set(x, 1, z, "wheat[age=7]")
        bp.set(15, 1, gdz0, "air")
        wx, wz = 39, 39
        bp.fill(wx - 1, -4, wz - 1, wx + 1, 0, wz + 1, "cobblestone")
        bp.fill(wx, -3, wz, wx, 0, wz, "water")
        bp.fill(wx - 1, 1, wz - 1, wx + 1, 1, wz + 1, "mossy_cobblestone")
        bp.set(wx, 1, wz, "water")
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bp.fill(wx + dx, 2, wz + dz, wx + dx, 3, wz + dz, fence)
        roof(bp, wx - 1, wz - 1, wx + 1, wz + 1, 4, ROOF["spruce"], axis="x", overhang=1, hollow=False)
        bp.chain(wx, 2, wz, 3)

        # ---------------------------------------------------------- lamps, crates, life
        for (x, z) in ((33, 26), (33, 34), (14, 23), (28, 22), (12, 38), (8, 17)):
            lamp_post(bp, x, 1, z, post=fence, h=3)
        for (x, z) in ((6, 38), (7, 38), (41, 21), (40, 22)):
            bp.barrel(x, 1, z, "up")
        bp.set(8, 1, 38, "hay_block[axis=y]")
        bp.set(6, 1, 40, "grindstone[face=floor,facing=north]")
        bp.set(7, 1, 40, "smithing_table")
        bp.set(8, 1, 40, "anvil[facing=east]")
        rng = random.Random(5)
        for _ in range(60):
            x, z = rng.randint(5, 41), rng.randint(5, 41)
            if bp.get(x, 0, z) == "minecraft:grass_block" and not bp.get(x, 1, z):
                bp.set(x, 1, z, rng.choice(["short_grass", "short_grass", "fern", "dandelion", "poppy", "cornflower"]))

        # ---------------------------------------------------------- outside: road, trees, meadow
        A.big_oak(bp, -1, 1, 9, 9, seed=2, crown=4)
        A.oak(bp, 15, 1, 0, 7, seed=1)
        A.spruce(bp, 0, 1, 30, 11)
        A.spruce(bp, 30, 1, 0, 9)
        A.oak(bp, 47, 1, 41, 6, seed=3)
        A.bush(bp, 47, 1, 21)
        A.bush(bp, 14, 1, 46, "spruce_leaves")
        A.bush(bp, 47, 1, 37)
        A.boulder(bp, 47, 1, 15, 2, seed=4)
        A.boulder(bp, 0, 1, 40, 2, seed=5)
        A.moss_on(bp, ((-2, 0, -2), (48, 9, 48)), chance=0.08, seed=4)
        A.vines_on(bp, ((0, 2, 0), (46, 9, 3)), chance=0.05, seed=6)
        A.vines_on(bp, ((0, 2, 0), (3, 9, 46)), chance=0.05, seed=7)
        for x in range(0, 48):
            for z in range(0, 48):
                if not bp.get(x, 0, z):
                    bp.set(x, 0, z, "grass_block[snowy=false]")
        A.landscape(bp, 0, 0, 51, 47, 1, density=0.2, seed=9)
        skirt(bp, 0, depth=6, spread=2, seed=1)

    return build


register(StructureDef(
    "guild_outpost", "overworld", TEMPERATE,
    [Piece("outpost_spruce", guild_outpost("azure"), 2),
     Piece("outpost_oak", guild_outpost("crimson"), 1),
     Piece("outpost_birch", guild_outpost("slate"), 1)],
    spacing=28, separation=10, exclusion=("minecraft:villages", 4),
    title_fr="Avant-poste de la Guilde", title_en="Guild Outpost"))


# ================================================================== MOUNTAIN MONASTERY
def monastery(bp):
    P = 5                                   # platform (main terrace) floor level
    R = ROOF["slate"]
    CU = ROOF["copper"]
    W = Palette({"calcite": 5, "polished_diorite": 2, "diorite": 1}, seed=101, scale=2.5)
    T = Palette({"stone_bricks": 5, "cracked_stone_bricks": 1}, seed=102)
    TS = "stone_brick_stairs"
    BASE = Palette({"stone_bricks": 3, "andesite": 2, "cobblestone": 1, "mossy_stone_bricks": 2, "tuff_bricks": 2},
                   seed=103, scale=2.0)
    glass_a = ["yellow_stained_glass", "orange_stained_glass", "red_stained_glass", "purple_stained_glass",
               "blue_stained_glass"]

    # ---------------------------------------------------------- crypt (secret, carved before the fill)
    bp.clear(12, 0, 10, 22, 3, 22)
    for x in range(11, 24):
        for z in range(9, 24):
            for y in range(-1, 5):
                if x in (11, 23) or z in (9, 23) or y in (-1, 4):
                    bp.set(x, y, z, BASE.pick(x, y, z))
    for z in range(12, 22, 3):
        for x in (13, 21):
            bp.fill(x, 0, z, x, 0, z + 1, "polished_deepslate")
            bp.set(x, 1, z, "candle[candles=2,lit=true,waterlogged=false]")
    for x, z in ((12, 10), (22, 10), (12, 22), (22, 22), (16, 16), (18, 20)):
        bp.set(x, 3 if (x, z) != (16, 16) else 0, z, "cobweb" if (x, z) != (16, 16) else "cobweb")
    bp.spawner(17, 0, 17, MOB["ruin_walker"])
    bp.chest(17, 0, 21, "north", LOOT + "monastery")
    bp.set(16, 0, 21, "skeleton_skull[rotation=8]")
    bp.lantern(17, 3, 13, hanging=True, soul=True)
    bp.lantern(17, 3, 20, hanging=True, soul=True)
    bp.ladder(17, 0, 10, 4, "south")
    bp.set(17, P, 10, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")

    # ---------------------------------------------------------- cathedral: aisles, nave, apse
    NX0, NX1, Z0, Z1 = 11, 23, 16, 46        # nave walls x, nave z range (facade at Z1)
    AX0, AX1 = 6, 28                         # aisle outer walls
    bp.clear(AX0 + 1, P + 1, Z0, AX1 - 1, 40, Z1 - 1)
    nave_floor = Palette({"polished_andesite": 1, "polished_diorite": 1}, seed=9, scale=1.0)
    for x in range(AX0, AX1 + 1):
        for z in range(Z0, Z1 + 1):
            bp.set(x, P, z, nave_floor.pick(x, P, z) if NX0 < x < NX1 else T.pick(x, P, z))
    win_aisle = dict(y=3, h=4, w=3, glass="light_blue_stained_glass_pane", sill=TS)
    gothic_wall(bp, "west", AX0, Z0, Z1, P, P + 10, W, T, TS, bay=6, win=win_aisle, plinth=BASE,
                plinth_st=TS, cornice_st=TS)
    gothic_wall(bp, "east", AX1, Z0, Z1, P, P + 10, W, T, TS, bay=6, win=win_aisle, plinth=BASE,
                plinth_st=TS, cornice_st=TS)
    for x in list(range(AX0, NX0 + 1)) + list(range(NX1, AX1 + 1)):
        for y in range(P, P + 11):
            bp.set(x, y, Z0, W.pick(x, y, Z0))
    win_clere = dict(y=17, h=2, w=3, glass="purple_stained_glass_pane", hood=False)
    gothic_wall(bp, "west", NX0, Z0, Z1, P, P + 20, W, T, TS, bay=6, win=win_clere, cornice_st=TS)
    gothic_wall(bp, "east", NX1, Z0, Z1, P, P + 20, W, T, TS, bay=6, win=win_clere, cornice_st=TS)
    # aisle lean-to roofs and their end triangles
    lean_to(bp, "west", AX0, Z0 - 1, Z1 + 1, P + 11, 5, R, under=TS)
    lean_to(bp, "east", AX1, Z0 - 1, Z1 + 1, P + 11, 5, R, under=TS)
    for z in (Z0, Z1):
        for k in range(5):
            for y in range(P + 11, P + 12 + k):
                for x in (AX0 + k, AX1 - k):
                    bp.set(x, y, z, W.pick(x, y, z))
    # interior arcades nave <-> aisles
    for line, face in ((NX0, "west"), (NX1, "east")):
        for zc in range(Z0 + 3, Z1, 6):
            gwindow(bp, face, line, zc, P + 1, 6, "air", T.pick(0, 0, 0), TS, w=5, hood=False)
    # tie beams + chandeliers + pews
    for z in range(Z0 + 6, Z1, 6):
        for x in range(NX0 + 1, NX1):
            bp.set(x, P + 21, z, "dark_oak_log[axis=x]")
    for z in range(Z0 + 9, Z1, 6):
        bp.chain(17, P + 18, z, P + 33)
        A.chandelier(bp, 17, P + 17, z)
        for x in (8, 26):
            bp.chain(x, P + 8, z, P + 11)
            bp.lantern(x, P + 7, z, hanging=True)
    for z in range(Z0 + 8, Z1 - 3, 2):
        for x in list(range(NX0 + 2, 16)) + list(range(19, NX1 - 1)):
            bp.stairs(x, P + 1, z, "dark_oak_stairs", "south")
    for z in range(Z0 + 4, Z1 - 2, 6):
        for x in (AX0 + 1, AX1 - 1):
            bp.set(x, P + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    for x in range(16, 19):
        for z in range(Z0 + 2, Z1):
            bp.set(x, P + 1, z, "red_carpet") if bp.get(x, P + 1, z) is None or \
                bp.get(x, P + 1, z) == "minecraft:air" else None

    # apse (semicircular choir) with tall lancets and radial buttresses
    acx, acz, ar = 17, Z0, 6
    for x in range(acx - ar - 1, acx + ar + 2):
        for z in range(acz - ar - 1, acz + 1):
            d = math.hypot(x - acx, z - acz)
            if d <= ar + 0.4:
                for y in range(P, P + 21):
                    bp.set(x, y, z, W.pick(x, y, z) if d > ar - 0.8 else "air")
                bp.set(x, P, z, nave_floor.pick(x, P, z) if d <= ar - 0.8 else BASE.pick(x, P, z))
    for ang in (200, 235, 270, 305, 340):
        a = math.radians(ang)
        x, z = acx + round(math.cos(a) * ar), acz + round(math.sin(a) * ar)
        for y in range(P + 4, P + 17):
            bp.set(x, y, z, "yellow_stained_glass_pane" if y % 4 else "orange_stained_glass_pane")
        bp.set(x, P + 17, z, T.pick(x, 0, z))
    for ang in (182, 218, 252, 288, 322, 358):
        a = math.radians(ang)
        for k, rr in enumerate((ar + 1, ar + 2)):
            x, z = acx + round(math.cos(a) * rr), acz + round(math.sin(a) * rr)
            top = P + 18 - k * 6
            for y in range(P, top + 1):
                bp.set(x, y, z, T.pick(x, y, z))
            bp.set(x, top + 1, z, stp(TS, _face_to(acx, acz, x, z)))
    for (x, z) in round_ring(acx, acz, ar + 1):
        if z <= acz and math.hypot(x - acx, z - acz) > ar + 0.5:
            bp.set(x, P + 20, z, stp(TS, OPPOSITE[_face_to(acx, acz, x, z)], "top"))
    cone(bp, acx, acz, P + 21, ar + 1, R, h=16, only=lambda x, z: z <= acz, finial=R[0])
    # nave roof (built after the apse cone so it wins at the junction)
    ridge = roof(bp, NX0, Z0, NX1, Z1, P + 21, R, axis="z", overhang=1, steep=2, gable=W, under=TS)
    bp.fill(17, ridge + 1, Z1 + 1, 17, ridge + 4, Z1 + 1, "stone_brick_wall")
    bp.set(16, ridge + 3, Z1 + 1, "stone_brick_wall")
    bp.set(18, ridge + 3, Z1 + 1, "stone_brick_wall")
    # flèche (slender copper spire on an open lantern) above the choir
    bp.fill(16, ridge - 2, 18, 18, ridge, 20, T.pick(0, 0, 0))
    for (x, z) in ((16, 18), (18, 18), (16, 20), (18, 20)):
        bp.fill(x, ridge + 1, z, x, ridge + 2, z, "stone_brick_wall")
    bp.lantern(17, ridge + 1, 19)
    bp.fill(16, ridge + 3, 18, 18, ridge + 3, 20, T.pick(1, 1, 1))
    spire2(bp, 17, 19, ridge + 4, 1, CU, steep=4, shape="square", tip=2)
    # altar and choir
    bp.fill(14, P + 1, 11, 20, P + 1, 13, "polished_andesite")
    for x in range(14, 21):
        bp.stairs(x, P + 1, 14, "polished_andesite_stairs", "north")
    bp.fill(16, P + 2, 11, 18, P + 2, 11, "chiseled_stone_bricks")
    bp.set(17, P + 3, 11, "gold_block")
    bp.set(16, P + 3, 11, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(18, P + 3, 11, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(17, P + 2, 13, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(17, P + 1, 10, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(17, P, 10, "air")
    for x in (12, 22):
        for y in (P + 6, P + 7):
            bp.set(x, y, 13, f"purple_wall_banner[facing={'east' if x == 12 else 'west'}]")
    bp.chain(17, P + 14, 13, P + 30)
    A.chandelier(bp, 17, P + 13, 13)

    # facade (south): portal, rose window, pinnacled buttresses
    for x in range(AX0, AX1 + 1):
        for y in range(P, P + 21 if NX0 <= x <= NX1 else P + 11):
            bp.set(x, y, Z1, W.pick(x, y, Z1))
        bp.set(x, P, Z1, BASE.pick(x, P, Z1))
        bp.set(x, P + 1, Z1, BASE.pick(x, P + 1, Z1))
    for x in range(NX0, NX1 + 1):
        bp.set(x, P + 20, Z1 + 1, stp(TS, "north", "top"))
        bp.set(x, P + 11, Z1 + 1, stp(TS, "north", "top"))
    gwindow(bp, "south", Z1, 17, P + 1, 6, "air", "chiseled_stone_bricks", TS, w=5, hood=True)
    for y in range(P + 1, P + 7):
        bp.set(15, y, Z1, "stone_brick_wall")
        bp.set(19, y, Z1, "stone_brick_wall")
    bp.door(16, P + 1, Z1, "south", "dark_oak", hinge="left")
    bp.door(18, P + 1, Z1, "south", "dark_oak", hinge="right")
    for y in range(P + 1, P + 3):
        bp.set(17, y, Z1, "air")
    # porch gablet over the portal
    for k in range(5):
        for out in (1, 2):
            fset(bp, "south", Z1, 17 - 4 + k, out, P + 10 + k, stp(TS, "east"))
            fset(bp, "south", Z1, 17 + 4 - k, out, P + 10 + k, stp(TS, "west"))
            for u in range(17 - 3 + k, 17 + 4 - k):
                fset(bp, "south", Z1, u, out, P + 10 + k, T)
    for out in (1, 2):
        fset(bp, "south", Z1, 17, out, P + 14, "chiseled_stone_bricks")
    fset(bp, "south", Z1, 17, 2, P + 15, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for u in (13, 21):
        for out in (1, 2):
            for y in range(P, P + 10):
                fset(bp, "south", Z1, u, out, y, T)
        x, z = pos("south", Z1, u, 2)
        pinnacle(bp, x, P + 10, z, "chiseled_stone_bricks", CU, h=2)
    rose(bp, "south", Z1, 17, P + 16, 4, "stone_bricks", glass_a, center="yellow_stained_glass",
         ring="chiseled_stone_bricks")
    gwindow(bp, "south", Z1, 17, P + 24, 4, "purple_stained_glass_pane", "chiseled_stone_bricks", TS, w=1)
    for u in (8, 26):
        gwindow(bp, "south", Z1, u, P + 3, 4, "light_blue_stained_glass_pane", T, TS, w=1, sill=TS)
    for u in (NX0, NX1, AX0, AX1):
        A.buttress(bp, "south", Z1, u, P, 19 if u in (NX0, NX1) else 9, T.pick(u, 0, 0), TS, 3)
    for u in (NX0, NX1):
        x, z = pos("south", Z1, u, 1)
        pinnacle(bp, x, P + 19, z, T.pick(x, 1, z), CU, h=5)
    for u in (AX0, AX1):
        x, z = pos("south", Z1, u, 1)
        pinnacle(bp, x, P + 10, z, T.pick(x, 1, z), CU, h=2)
    for u in (14, 20):
        wall_lamp(bp, "south", Z1, u, P + 4, TS)
    # flying buttresses over the aisles
    for zc in range(Z0 + 6, Z1 - 1, 6):
        flying_buttress(bp, "west", NX0, zc, P + 19, 7, P, T.pick(0, zc, 0), TS)
        if zc < 38:
            flying_buttress(bp, "east", NX1, zc, P + 19, 6, P, T.pick(1, zc, 0), TS)

    # ---------------------------------------------------------- bell tower (campanile), south-east of the facade
    bx0, bx1, bz0, bz1 = 29, 37, 38, 46
    bcx, bcz = 33, 42
    BH = P + 46
    bp.clear(bx0 + 1, P + 1, bz0 + 1, bx1 - 1, BH, bz1 - 1)
    for face, line, a, b in (("south", bz1, bx0, bx1), ("east", bx1, bz0, bz1), ("north", bz0, bx0, bx1),
                             ("west", bx0, bz0, bz1)):
        A.facade(bp, face, line, a, b, P, BH, W, T, pilaster_every=8, window_y=4, window_h=4,
                 floors=[P, P + 11, P + 22], floor_band=T, plinth=BASE, plinth_stairs=TS,
                 cornice_stairs=TS, sill=TS)
        gwindow(bp, face, line, (a + b) // 2, P + 35, 5, "air", "chiseled_stone_bricks", TS, w=3, hood=True,
                sill=TS)
        for y in (P + 11, P + 22, P + 33):
            for u in range(a, b + 1):
                fset(bp, face, line, u, 1, y, stp(TS, OPPOSITE[face], "top"))
        for u in (a, b):
            A.buttress(bp, face, line, u, P, 30, T.pick(u, 0, line), TS, 2)
        fset(bp, face, line, (a + b) // 2, 1, P + 26, "chiseled_stone_bricks")
    for fy in (P + 11, P + 22, P + 33):
        bp.fill(bx0 + 1, fy, bz0 + 1, bx1 - 1, fy, bz1 - 1, "spruce_planks")
        bp.set(bx0 + 1, fy, bz0 + 1, "air")
        bp.chain(bcx, fy - 1, bcz, fy - 1)
        bp.lantern(bcx, fy - 2, bcz, hanging=True)
    pave(bp, bx0 + 1, bz0 + 1, bx1 - 1, bz1 - 1, P, T)
    bp.ladder(bx0 + 1, P + 1, bz0 + 1, BH - 1, "south")
    bp.fill(bcx - 1, BH - 1, bcz, bcx + 1, BH - 1, bcz, "dark_oak_log[axis=x]")
    bp.set(bcx, BH - 2, bcz, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.fill(bx0, BH, bz0, bx1, BH, bz1, T.pick(0, 0, 0))
    for x in range(bx0, bx1 + 1):
        for z in range(bz0, bz1 + 1):
            if x in (bx0, bx1) or z in (bz0, bz1):
                bp.set(x, BH + 1, z, "stone_brick_wall" if (x + z) % 2 else "chiseled_stone_bricks")
    for (x, z) in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1)):
        pinnacle(bp, x, BH + 1, z, "stone_bricks", CU, h=2)
    spire2(bp, bcx, bcz, BH + 1, 4, CU, steep=5, shape="octagon", tip=3)
    door_in(bp, "south", bz1, bcx, P, "spruce")
    wall_lamp(bp, "south", bz1, bcx - 2, P + 4, TS)
    wall_lamp(bp, "south", bz1, bcx + 2, P + 4, TS)

    # ---------------------------------------------------------- cloister wings
    wood_floor = Palette({"spruce_planks": 3, "stripped_spruce_wood": 1}, seed=5)

    # north wing: the great library hall (tall gothic windows, inner galleries)
    lx0, lx1, lz0, lz1, LE = 29, 68, 6, 13, P + 14
    bp.clear(lx0 + 1, P + 1, lz0 + 1, lx1 - 1, LE, lz1 - 1)
    gothic_wall(bp, "north", lz0, lx0, lx1, P, LE, W, T, TS, bay=6, plinth=BASE, plinth_st=TS, cornice_st=TS,
                buttress=(T.pick(0, 0, 0), TS, 2),
                win=dict(y=3, h=7, w=3, glass="glass_pane", sill=TS, mullion="iron_bars"))
    gothic_wall(bp, "south", lz1, lx0, lx1, P, LE, W, T, TS, bay=6, cornice_st=TS,
                win=dict(y=10, h=1, w=3, glass="glass_pane", hood=False))
    for face, line in (("west", lx0), ("east", lx1)):
        for u in range(lz0, lz1 + 1):
            for y in range(P, LE + 1):
                pset(bp, face, line, u, 0, y, W)
        gwindow(bp, face, line, 10, P + 4, 6, "light_blue_stained_glass_pane", "chiseled_stone_bricks", TS, w=3,
                sill=TS, mullion="iron_bars")
        for u in (lz0, lz1):
            A.buttress(bp, face, line, u, P, 12, T.pick(u, 0, 0), TS, 2)
    pave(bp, lx0 + 1, lz0 + 1, lx1 - 1, lz1 - 1, P, wood_floor)
    lr = roof(bp, lx0, lz0, lx1, lz1, LE + 1, R, axis="x", overhang=1, steep=1.5, gable=W, under=TS)
    for face, line in (("west", lx0), ("east", lx1)):
        rose(bp, face, line, 9 if face == "west" else 10, LE + 4, 1, "chiseled_stone_bricks", ["glass_pane"],
             center="glass_pane")
    for u in (38, 50, 62):
        dormer(bp, "north", lz0, u, LE + 1, R, W, trim="stone_bricks")
    # galleries along both long walls with bookcases above and below
    for z0g, z1g, rail in ((lz0 + 1, lz0 + 2, lz0 + 3), (lz1 - 2, lz1 - 1, lz1 - 3)):
        bp.fill(lx0 + 1, P + 7, z0g, lx1 - 1, P + 7, z1g, "spruce_planks")
        for x in range(lx0 + 1, lx1):
            bp.set(x, P + 8, rail, "spruce_fence")
            bp.set(x, P + 7, rail, stp("spruce_stairs", "north" if rail > 9 else "south", "top")) \
                if x % 6 else bp.set(x, P + 7, rail, "spruce_planks")
            if x % 6 == 5:
                bp.fill(x, P + 1, rail, x, P + 6, rail, "stripped_spruce_log[axis=y]")
    for x in range(lx0 + 1, lx1):
        if (x - lx0) % 6 in (2, 3, 4):
            for z in (lz0 + 1, lz1 - 1):
                for y in list(range(P + 1, P + 3)) + list(range(P + 8, P + 10)):
                    bp.set(x, y, z, "bookshelf" if (x * y) % 7 else "chiseled_bookshelf[facing=%s,"
                           "slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,"
                           "slot_4_occupied=false,slot_5_occupied=true]" % ("south" if z == lz0 + 1 else "north"))
    for x in range(lx0 + 4, lx1 - 2, 6):
        bp.set(x, P + 1, 9, "spruce_fence")
        bp.set(x, P + 2, 9, "spruce_pressure_plate[powered=false]")
        bp.set(x + 1, P + 1, 9, "spruce_fence")
        bp.set(x + 1, P + 2, 9, "candle[candles=3,lit=true,waterlogged=false]")
        bp.stairs(x, P + 1, 10, "spruce_stairs", "south")
        bp.stairs(x + 1, P + 1, 10, "spruce_stairs", "south")
        bp.set(x + 3, P + 1, 9, "lectern[facing=south,has_book=false,powered=false]")
        bp.chain(x + 2, P + 13, 9, lr - 1)
        A.chandelier(bp, x + 2, P + 12, 9)
    bp.chest(lx1 - 1, P + 8, lz0 + 1, "west", LOOT + "monastery_library")
    bp.set(lx1 - 2, P + 8, lz0 + 1, "enchanting_table")
    for i in range(6):
        bp.stairs(lx0 + 1 + i, P + 1 + i, lz1 - 3, "spruce_stairs", "east")
        bp.set(lx0 + 1 + i, P + 7, lz1 - 3, "air")
    bp.fill(lx0 + 1, P + 7, lz1 - 3, lx0 + 7, P + 8, lz1 - 3, "air")
    door_in(bp, "south", lz1, 45, P, "spruce")

    # east wing: dormitory, stone ground floor + half-timbered upper floor
    dx0, dx1, dz0, dz1 = 61, 68, 14, 38
    bp.clear(dx0 + 1, P + 1, dz0 + 1, dx1 - 1, P + 11, dz1 - 1)
    for face, line, a, b in (("east", dx1, dz0, dz1), ("south", dz1, dx0, dx1), ("west", dx0, dz0, dz1)):
        A.facade(bp, face, line, a, b, P, P + 5, W, T, pilaster_every=4, window_y=2, window_h=2, plinth=BASE,
                 plinth_stairs=TS, cornice_stairs="spruce_stairs", sill=TS, arched=False)
    timber_storey(bp, dx0, dz0, dx1, dz1, P + 6, P + 11, "spruce_log", Palette({"calcite": 3, "white_terracotta": 1},
                  seed=4), wood="spruce", faces=("east", "south", "west"))
    pave(bp, dx0 + 1, dz0 + 1, dx1 - 1, dz1 - 1, P, wood_floor)
    bp.fill(dx0 + 1, P + 6, dz0 + 1, dx1 - 1, P + 6, dz1 - 1, "spruce_planks")
    dr = roof(bp, dx0, dz0 - 1, dx1, dz1, P + 12, R, axis="z", overhang=1, steep=1.5,
              gable=Palette({"calcite": 3, "white_terracotta": 1}, seed=4), under="spruce_stairs")
    for u in (20, 26, 32):
        dormer(bp, "east", dx1, u, P + 12, R, Palette({"calcite": 1}), trim="spruce_log[axis=y]")
    for z in range(dz0 + 1, dz1 - 1, 3):
        bp.bed(dx1 - 1, P + 1, z, "west", "white")
        bp.bed(dx1 - 1, P + 7, z, "west", "light_gray")
        bp.set(dx1 - 1, P + 1, z + 1, "barrel[facing=up,open=false]")
        bp.set(dx1 - 1, P + 2, z + 1, "candle[candles=1,lit=true,waterlogged=false]")
        bp.set(dx1 - 1, P + 7, z + 1, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=false,"
               "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=false]")
    bp.chest(dx0 + 1, P + 7, dz1 - 1, "east", LOOT + "monastery")
    for i in range(6):
        bp.stairs(dx0 + 1, P + 1 + i, 30 - i, "spruce_stairs", "north")
        bp.set(dx0 + 1, P + 6, 30 - i, "air")
    for z in range(dz0 + 3, dz1, 6):
        bp.lantern(64, P + 5, z, hanging=True)
        bp.lantern(64, P + 11, z, hanging=True)
    door_in(bp, "west", dx0, 22, P, "spruce")
    A.fill_pal(bp, 66, P + 1, dz1 - 3, 67, dr + 2, dz1 - 2, Palette({"bricks": 3, "stone_bricks": 1}, seed=2))
    bp.set(66, dr + 2, dz1 - 3, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(66, P + 1, dz1 - 3, "campfire[lit=false,signal_fire=false,waterlogged=false,facing=west]")
    bp.set(66, P + 2, dz1 - 3, "air")

    # south wing: refectory + kitchen, buttressed with tall windows
    sx0, sx1, sz0, sz1, SE = 39, 60, 31, 38, P + 10
    bp.clear(sx0 + 1, P + 1, sz0 + 1, sx1 - 1, SE, sz1 - 1)
    gothic_wall(bp, "south", sz1, sx0, sx1, P, SE, W, T, TS, bay=5, plinth=BASE, plinth_st=TS, cornice_st=TS,
                buttress=(T.pick(2, 2, 2), TS, 2), win=dict(y=2, h=4, w=3, glass="glass_pane", sill=TS))
    for face, line, a, b in (("north", sz0, sx0, sx1), ("west", sx0, sz0, sz1), ("east", sx1, sz0, sz1)):
        for u in range(a, b + 1):
            for y in range(P, SE + 1):
                pset(bp, face, line, u, 0, y, W)
    gwindow(bp, "west", sx0, 34, P + 3, 4, "glass_pane", T, TS, w=3, sill=TS)
    pave(bp, sx0 + 1, sz0 + 1, sx1 - 1, sz1 - 1, P, Palette({"stone_bricks": 2, "polished_andesite": 1}, seed=8))
    sr = roof(bp, sx0, sz0, sx1, sz1, SE + 1, R, axis="x", overhang=1, steep=1.5, gable=W, under=TS)
    for x in range(sx0 + 3, 52):
        for z in (34, 35):
            bp.set(x, P + 1, z, "spruce_fence")
            bp.set(x, P + 2, z, "white_carpet")
        bp.stairs(x, P + 1, 33, "spruce_stairs", "south")
        bp.stairs(x, P + 1, 36, "spruce_stairs", "north")
    for x in range(sx0 + 4, 52, 4):
        bp.set(x, P + 3, 34, "candle[candles=3,lit=true,waterlogged=false]")
    bp.fill(53, P + 1, sz0 + 1, 53, P + 4, sz1 - 1, "stone_bricks")
    bp.clear(53, P + 1, 34, 53, P + 3, 35)
    A.furnish(bp, 54, P + 1, sz0 + 1, sx1 - 1, sz1 - 1, "kitchen", wood="spruce", loot=LOOT + "monastery")
    for x in (43, 49):
        bp.chain(x, P + 9, 34, sr - 1)
        A.chandelier(bp, x, P + 8, 34)
    for (x, z) in ((57, 32), (45, 32)):
        A.fill_pal(bp, x, P + 1, z, x + 1, sr + 2, z + 1, Palette({"bricks": 3, "stone_bricks": 1}, seed=x))
        bp.set(x, sr + 2, z, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(57, P + 1, 32, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=south]")
    bp.set(57, P + 2, 32, "air")
    bp.set(45, P + 1, 32, "stone_bricks")
    door_in(bp, "north", sz0, 47, P, "spruce")
    door_in(bp, "south", sz1, 41, P, "spruce", steps=TS)

    # ---------------------------------------------------------- cloister arcades around the garth
    cl = Palette({"grass_block[snowy=false]": 1}, seed=1)
    pave(bp, 29, 14, 60, 30, P, T)
    pave(bp, 34, 18, 56, 26, P, cl)
    arcade(bp, "south", 17, 33, 57, P, 3, "stone_brick_wall", TS, every=3, cap="chiseled_stone_bricks")
    arcade(bp, "north", 27, 33, 57, P, 3, "stone_brick_wall", TS, every=3, cap="chiseled_stone_bricks")
    arcade(bp, "west", 57, 17, 27, P, 3, "stone_brick_wall", TS, every=3, cap="chiseled_stone_bricks")
    arcade(bp, "east", 33, 17, 27, P, 3, "stone_brick_wall", TS, every=3, cap="chiseled_stone_bricks")
    lean_to(bp, "south", 17, 29, 61, P + 5, 4, R, under=TS)
    lean_to(bp, "north", 27, 29, 61, P + 5, 4, R, under=TS)
    lean_to(bp, "west", 57, 14, 30, P + 5, 4, R, under=TS)
    lean_to(bp, "east", 33, 14, 30, P + 5, 5, R, under=TS)
    for x in range(30, 61, 4):
        bp.lantern(x, P + 4, 15, hanging=True)
        bp.lantern(x, P + 4, 29, hanging=True)
    for z in range(16, 30, 4):
        bp.lantern(59, P + 4, z, hanging=True)
        bp.lantern(30, P + 4, z, hanging=True)
    door_in(bp, "east", AX1, 25, P, "spruce")
    door_in(bp, "south", 13, 40, P, "spruce")
    # garth: gravel cross paths, fountain, cherry trees, flower beds
    for x in range(34, 57):
        bp.set(x, P, 22, "gravel")
    for z in range(18, 27):
        bp.set(45, P, z, "gravel")
    fx, fz = 45, 22
    for (x, z) in round_ring(fx, fz, 3):
        bp.set(x, P + 1, z, stp("polished_andesite_stairs", OPPOSITE[_face_to(fx, fz, x, z)]))
    bp.disk(fx, P, fz, 2, "water")
    bp.disk(fx, P - 1, fz, 3, "stone_bricks")
    bp.fill(fx, P, fz, fx, P + 2, fz, "chiseled_stone_bricks")
    bp.disk(fx, P + 3, fz, 1, "stone_brick_slab[type=bottom,waterlogged=false]")
    bp.set(fx, P + 3, fz, "water")
    for (x, z, s) in ((37, 19, 1), (53, 19, 2), (37, 25, 3), (53, 25, 4)):
        A.oak(bp, x, P + 1, z, 5, seed=s, log="cherry_log", leaves="cherry_leaves")
    rng = random.Random(7)
    for x in range(34, 57):
        for z in range(18, 27):
            if bp.get(x, P, z) == "minecraft:grass_block" and not bp.get(x, P + 1, z) and rng.random() < 0.35:
                bp.set(x, P + 1, z, rng.choice(["pink_petals[facing=north,flower_amount=3]", "lily_of_the_valley",
                                                "azure_bluet", "short_grass", "allium", "peony[half=lower]"]))
                if bp.get(x, P + 1, z) == "minecraft:peony":
                    bp.set(x, P + 2, z, "peony[half=upper]")

    # ---------------------------------------------------------- platform, retaining walls, terraces
    PX0, PX1, PZ0, PZ1 = 2, 70, 3, 50
    top = Palette({"grass_block[snowy=false]": 5, "coarse_dirt": 1, "moss_block": 1}, seed=55)
    pave(bp, PX0, PZ0, PX1, PZ1, P, top, keep=True)
    for face, line, a, b in (("south", PZ1, PX0, PX1), ("north", PZ0, PX0, PX1), ("west", PX0, PZ0, PZ1),
                             ("east", PX1, PZ0, PZ1)):
        for u in range(a, b + 1):
            for y in range(-3, P + 1):
                pset(bp, face, line, u, 0, y, BASE)
            fset(bp, face, line, u, 1, P, stp(TS, OPPOSITE[face], "top"))
            if not (face == "south" and 10 <= u <= 24):
                fset(bp, face, line, u, 0, P + 1, "stone_brick_wall" if u % 3 else "stone_bricks")
        for u in range(a + 3, b, 7):
            A.buttress(bp, face, line, u, -3, P + 2, BASE.pick(u, 0, line), TS, 2)
    for u in range(PX0 + 6, PX1, 7):
        x, z = pos("south", PZ1, u, 0)
        if not 10 <= x <= 24:
            bp.lantern(x, P + 2, z)
    bp.fill(PX0 + 1, -3, PZ0 + 1, PX1 - 1, P - 1, PZ1 - 1, "stone", keep=True)
    # grand stair from the forecourt up to the portal
    A.stair_run(bp, 11, 1, PZ1 + 5, "north", 5, 13, TS, fill="stone_bricks", clear=3)
    for x in (10, 24):
        bp.fill(x, 0, PZ1 + 1, x, P + 1, PZ1 + 5, "stone_bricks")
        bp.set(x, P + 2, PZ1 + 1, "lantern[hanging=false,waterlogged=false]")
    # paths on the terrace
    path_line(bp, [(17, PZ1 - 1), (17, Z1 + 3)], P, Palette({"gravel": 2, "stone_bricks": 1}), width=5)
    path_line(bp, [(24, 48), (38, 48), (38, 40)], P, Palette({"gravel": 2, "coarse_dirt": 1}), width=2)
    # herb garden, beehives and orchard between the refectory and the edge
    for x in range(40, 60, 3):
        for z in range(41, 47):
            bp.set(x, P, z, "farmland[moisture=7]")
            bp.set(x, P + 1, z, "wheat[age=7]")
        bp.set(x + 1, P, 43, "water")
    for (x, z) in ((62, 42), (64, 46)):
        A.oak(bp, x, P + 1, z, 5, seed=x)
    bp.set(60, P + 1, 40, "beehive[facing=south,honey_level=3]")
    bp.set(66, P + 1, 41, "beehive[facing=west,honey_level=5]")
    for (x, z) in ((3, 8), (3, 30)):
        A.spruce(bp, x + 1, P + 1, z, 10)
    # forecourt with the waystone shrine
    FZ0, FZ1 = PZ1 + 1, PZ1 + 13
    fpal = Palette({"stone_bricks": 3, "cobblestone": 2, "mossy_cobblestone": 1, "gravel": 1}, seed=60)
    pave(bp, PX0, FZ0, 44, FZ1, 0, fpal)
    wx, wz = 32, FZ0 + 6
    bp.fill(wx - 2, 1, wz - 2, wx + 2, 1, wz + 2, "stone_bricks")
    for (x, z) in round_ring(wx, wz, 3):
        if max(abs(x - wx), abs(z - wz)) == 3:
            bp.set(x, 1, z, stp(TS, _face_to(wx, wz, x, z)))
    bp.fill(wx - 1, 2, wz - 1, wx + 1, 2, wz + 1, "chiseled_stone_bricks")
    bp.set(wx, 3, wz, MOD["waystone"])
    for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bp.fill(wx + dx, 2, wz + dz, wx + dx, 4, wz + dz, "stone_brick_wall")
        bp.set(wx + dx, 5, wz + dz, "lantern[hanging=false,waterlogged=false]")
    for (x, z) in ((4, FZ1 - 1), (40, FZ1 - 1), (4, FZ0 + 2)):
        lamp_post(bp, x, 1, z, post="spruce_fence", h=3, base="stone_bricks")
    A.spruce(bp, 8, 1, FZ1 - 3, 11)
    A.spruce(bp, 40, 1, FZ0 + 3, 9)
    # stepped vegetable terraces on the east, below the platform
    for x in range(46, PX1 + 1):
        for z in range(FZ0, FZ0 + 6):
            for y in range(-3, 3):
                bp.set(x, y, z, BASE.pick(x, y, z) if z == FZ0 + 5 or x in (46, PX1) else "dirt")
            bp.set(x, 3, z, "farmland[moisture=7]" if (x % 3) and z < FZ0 + 5 else
                   ("water" if z < FZ0 + 5 else BASE.pick(x, 3, z)))
            if bp.get(x, 3, z) == "minecraft:farmland":
                bp.set(x, 4, z, "wheat[age=7]")
        for z in range(FZ0 + 6, FZ1 + 1):
            bp.set(x, 0, z, "grass_block[snowy=false]")
    for x in range(48, PX1, 4):
        fset(bp, "south", FZ0 + 5, x, 1, 0, stp(TS, "north"))
    A.stair_run(bp, 44, 1, FZ0 + 3, "east", 3, 2, TS, fill="stone_bricks", clear=3)
    for z in range(FZ0 + 7, FZ1, 2):
        for x in range(48, PX1 - 1):
            if x % 5:
                bp.set(x, 1, z, leaves("azalea_leaves" if x % 2 else "flowering_azalea_leaves"))

    # ---------------------------------------------------------- weathering, ground, nature
    A.moss_on(bp, ((0, -4, 0), (72, P + 2, 66)), chance=0.12, seed=3)
    A.vines_on(bp, ((0, -3, 0), (72, P + 4, 3)), chance=0.08, seed=5)
    A.vines_on(bp, ((0, -3, 0), (2, P + 4, 66)), chance=0.08, seed=6)
    bp.weather({"calcite": ["diorite", "calcite"]}, 0.05)
    skirt(bp, 0, depth=5, spread=2, seed=11, top="grass_block[snowy=false]")
    A.landscape(bp, -3, -3, 75, 68, 1, density=0.25, seed=12)
    lair_bell_keeper.build(bp)          # crypt stair -> catacombs -> bell chamber (the Bell Keeper)


register(StructureDef(
    "mountain_monastery", "overworld",
    ["meadow", "grove", "snowy_slopes", "cherry_grove", "windswept_hills", "windswept_forest",
     "stony_peaks"],
    [Piece("monastery", monastery)], spacing=40, separation=14,
    spawns=[("wayfarers:map_wraith", 10, 1, 2), ("wayfarers:ruin_walker", 6, 1, 2)],
    title_fr="Monastère des cimes", title_en="Mountain Monastery"))


# ================================================================== FORGOTTEN LIBRARY
def great_chandelier(bp, x, y, z, top, r=3, soul=False):
    """Large ring chandelier hanging from `top` down to y: chain, ring of lanterns and candles."""
    bp.chain(x, y + 1, z, top)
    bp.set(x, y, z, "dark_oak_planks")
    bp.lantern(x, y - 1, z, hanging=True, soul=soul)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
        for k in range(1, r + 1):
            px, pz = x + dx * k, z + dz * k
            if abs(dx) + abs(dz) == 2 and k == r:
                continue
            bp.set(px, y, pz, "dark_oak_fence" if k < r else "dark_oak_planks")
        ex, ez = x + dx * (r if abs(dx) + abs(dz) == 1 else r - 1), z + dz * (r if abs(dx) + abs(dz) == 1 else r - 1)
        bp.set(ex, y + 1, ez, "candle[candles=4,lit=true,waterlogged=false]")
        bp.chain(ex, y - 1, ez, y - 1)
        bp.lantern(ex, y - 2, ez, hanging=True, soul=soul)


def library(bp):
    CW = ("waxed_weathered_cut_copper", "waxed_weathered_cut_copper_stairs", "waxed_weathered_cut_copper_slab")
    R = CW
    W = Palette({"tuff_bricks": 7, "tuff": 1, "polished_tuff": 1, "mossy_stone_bricks": 1}, seed=201, scale=2.5)
    T = Palette({PGS: 5, CGS: 1}, seed=202)
    TS = PGS_ST
    BASE = Palette({"polished_deepslate": 2, "deepslate_bricks": 3, "cracked_deepslate_bricks": 1}, seed=203)
    BS = "deepslate_brick_stairs"
    G1, G2 = "cyan_stained_glass_pane", "light_blue_stained_glass_pane"
    HX0, HX1, HZ0, HZ1, HE = 16, 64, 6, 30, 24     # main hall walls and eave height
    CZ = 18                                         # long axis centre line
    shelf = "bookshelf"

    def cshelf(face):
        return (f"chiseled_bookshelf[facing={face},slot_0_occupied=true,slot_1_occupied=true,"
                "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")

    # ---------------------------------------------------------- the hall shell
    bp.clear(HX0 + 1, 1, HZ0 + 1, HX1 - 1, HE, HZ1 - 1)
    floor = Palette({"polished_deepslate": 1, "polished_tuff": 1}, seed=3, scale=1.0)
    for x in range(HX0, HX1 + 1):
        for z in range(HZ0, HZ1 + 1):
            bp.set(x, 0, z, floor.pick(x, 0, z) if (x + z) % 2 else ("polished_tuff" if (x // 6 + z // 6) % 2
                                                                     else "polished_deepslate"))
    for face, line in (("south", HZ1), ("north", HZ0)):
        piers = gothic_wall(bp, face, line, HX0, HX1, 0, HE, W, T, TS, bay=6, plinth=BASE, plinth_st=BS,
                            cornice_st=TS, buttress=(T.pick(0, 0, 0), TS, 3),
                            win=dict(y=3, h=6, w=3, glass=G1, sill=TS, mullion="iron_bars"))
        for a, b in zip(piers, piers[1:]):
            cu = (a + b) // 2
            gwindow(bp, face, line, cu, 13, 7, G2, T, TS, w=3, sill=TS, mullion="iron_bars")
            for u in range(a + 1, b):
                fset(bp, face, line, u, 1, 11, stp(TS, OPPOSITE[face], "top"))
        for u in piers[1:-1]:
            x, z = pos(face, line, u, 1)
            pinnacle(bp, x, HE + 1, z, T.pick(x, 0, z), R, h=3)
    for x in range(HX0, HX1 + 1):
        for z in (HZ0, HZ1):
            bp.set(x, HE + 1, z, GB_WALL if x % 2 else PGS)
    for z in range(HZ0, HZ1 + 1):
        for y in range(0, HE + 1):
            bp.set(HX0, y, z, W.pick(HX0, y, z))
            bp.set(HX1, y, z, W.pick(HX1, y, z))
    ridge = roof(bp, HX0, HZ0, HX1, HZ1, HE + 1, R, axis="x", overhang=1, steep=1.25, gable=W, under=TS)
    for u in (25, 37, 49):
        for face, line in (("north", HZ0), ("south", HZ1)):
            dormer(bp, face, line, u, HE + 2, R, W, glass=G2, trim="chiseled_tuff_bricks", depth=5)
    for x in range(HX0 + 2, HX1 - 1, 4):
        bp.set(x, ridge + 1, CZ, "tuff_brick_wall")
    # flèche: open octagonal lantern with a slender copper spire above the crossing
    fx = 46
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        for y in range(ridge - 2, ridge + 5):
            bp.set(fx + dx, y, CZ + dz, PGS if y < ridge + 1 else GB_WALL)
    for x in range(fx - 2, fx + 3):
        for z in range(CZ - 2, CZ + 3):
            bp.set(x, ridge, z, PGS)
            bp.set(x, ridge + 5, z, PGS)
    bp.lantern(fx, ridge + 1, CZ)
    bp.set(fx, ridge + 4, CZ, RUNE)
    for (x, z) in ((fx - 3, CZ), (fx + 3, CZ), (fx, CZ - 3), (fx, CZ + 3)):
        bp.set(x, ridge + 5, z, stp(PGS_ST, OPPOSITE[_face_to(fx, CZ, x, z)], "top"))
    spire2(bp, fx, CZ, ridge + 6, 2, R, steep=5, shape="octagon", tip=3)

    # ---------------------------------------------------------- interior: galleries, stacks, reading nave
    GY1, GY2 = 11, 17
    for zg0, zg1, edge, inward in ((HZ0 + 1, HZ0 + 4, HZ0 + 4, 1), (HZ1 - 4, HZ1 - 1, HZ1 - 4, -1)):
        bp.fill(HX0 + 1, GY1, zg0, HX1 - 1, GY1, zg1, "dark_oak_planks")
        z2 = HZ0 + 2 if inward == 1 else HZ1 - 2
        bp.fill(HX0 + 1, GY2, min(z2, zg0 if inward == 1 else zg1), HX1 - 1, GY2,
                max(z2, zg0 if inward == 1 else zg1), "dark_oak_planks")
        for x in range(HX0 + 1, HX1):
            bp.set(x, GY1 + 1, edge, "dark_oak_fence")
            bp.set(x, GY1, edge + inward, stp("dark_oak_stairs", "north" if inward == 1 else "south", "top"))
            bp.set(x, GY2 + 1, z2, "dark_oak_fence")
        for x in range(HX0 + 3, HX1 - 1, 6):
            bp.fill(x, 1, edge, x, GY1 - 1, edge, "dark_oak_log[axis=y]")
            bp.set(x, GY1 - 1, edge + inward, stp("dark_oak_stairs", "north" if inward == 1 else "south", "top"))
            bp.fill(x, GY1 + 1, z2, x, GY2 - 1, z2, "dark_oak_log[axis=y]")
    face_n, face_s = "south", "north"
    for x in range(HX0 + 1, HX1):
        k = (x - HX0) % 6
        for (zw, f, step) in ((HZ0 + 1, face_n, 1), (HZ1 - 1, face_s, -1)):
            if k in (0, 1, 5):                          # bookcases on the piers, full height
                for y in list(range(1, GY1)) + list(range(GY1 + 1, GY2)) + list(range(GY2 + 1, HE - 1)):
                    bp.set(x, y, zw, shelf if (x * 7 + y * 3) % 9 else cshelf(f))
            if k == 0:                                  # perpendicular stacks forming alcoves
                for d in range(1, 3):
                    for y in range(1, 6):
                        bp.set(x, y, zw + step * d, shelf if (x + y + d) % 5 else cshelf("east"))
                    for y in range(GY1 + 1, GY1 + 4):
                        bp.set(x, y, zw + step * d, shelf)
            if k == 3:                                  # reading alcove in each bay
                bp.set(x, 1, zw + step, "dark_oak_fence")
                bp.set(x, 2, zw + step, "dark_oak_pressure_plate[powered=false]")
                bp.stairs(x, 1, zw + step * 2, "dark_oak_stairs", f)
                bp.lantern(x, GY1 - 1, zw + step, hanging=True)
                bp.set(x, GY1 + 1, zw + step, "lectern[facing=%s,has_book=false,powered=false]" % OPPOSITE[f])
    # stairs to the galleries (west end) and ladders to the upper catwalks
    A.stair_run(bp, HX0 + 1, 1, HZ0 + 15, "north", GY1, 2, "dark_oak_stairs", fill=None, clear=3)
    A.stair_run(bp, HX0 + 1, 1, HZ1 - 15, "south", GY1, 2, "dark_oak_stairs", fill=None, clear=3)
    for z in range(HZ0 + 4, HZ0 + 16):
        for x in (HX0 + 1, HX0 + 2):
            bp.set(x, GY1, z, "air") if z > HZ0 + 4 else None
    for z in range(HZ1 - 15, HZ1 - 3):
        for x in (HX0 + 1, HX0 + 2):
            bp.set(x, GY1, z, "air") if z < HZ1 - 4 else None
    for z in (HZ0 + 3, HZ1 - 3):
        bp.ladder(HX1 - 2, GY1 + 1, z, GY2 + 1, "west")
        bp.set(HX1 - 2, GY2, z, "ladder[facing=west,waterlogged=false]")
    # the reading nave: long tables, lecterns, carpet runner, globes of light
    for x in range(HX0 + 5, HX1 - 3):
        bp.set(x, 0, CZ, "red_wool" if x % 2 else "red_terracotta")
    for x0 in range(HX0 + 6, HX1 - 6, 8):
        for zt in (CZ - 3, CZ + 3):
            for x in range(x0, x0 + 5):
                bp.set(x, 1, zt, "dark_oak_fence" if x in (x0, x0 + 4) else "dark_oak_planks")
                bp.set(x, 2, zt, "dark_oak_pressure_plate[powered=false]" if x % 2 else "air")
                bp.stairs(x, 1, zt - 1, "dark_oak_stairs", "south")
                bp.stairs(x, 1, zt + 1, "dark_oak_stairs", "north")
            bp.set(x0 + 2, 2, zt, "candle[candles=3,lit=true,waterlogged=false]")
            bp.set(x0 + 1, 2, zt, "potted_fern" if x0 % 16 else "air")
        bp.set(x0 + 6, 1, CZ - 1, "lectern[facing=south,has_book=false,powered=false]")
    for xc in (24, 40, 56):
        great_chandelier(bp, xc, 16, CZ, ridge - 1, r=3)
    # guardians and treasures
    bp.spawner(40, 1, CZ, MOB["map_wraith"])
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(40 + dx, 1, CZ + dz, "chiseled_tuff_bricks" if dx else "air")
    bp.set(40, 1, CZ - 1, "air")
    bp.spawner(HX0 + 8, GY1 + 1, HZ0 + 3, MOB["map_wraith"])
    bp.chest(HX0 + 4, 1, HZ0 + 2, "south", LOOT + "library")
    bp.chest(HX1 - 3, GY2 + 1, HZ0 + 2, "south", LOOT + "library")

    # ---------------------------------------------------------- octagonal map room annex (south side)
    ox, oz, orr, OH = 43, 40, 6, 12
    for x in range(ox - orr - 2, ox + orr + 3):
        for z in range(oz - orr - 2, oz + orr + 3):
            d = _dist(x - ox, z - oz, "octagon")
            if d <= orr + 0.3:
                bp.set(x, 0, z, floor.pick(x, 0, z))
                for y in range(1, OH + 1):
                    bp.set(x, y, z, W.pick(x, y, z) if d > orr - 0.7 else "air")
                bp.set(x, 1, z, BASE.pick(x, 1, z)) if d > orr - 0.7 else None
            elif d <= orr + 1.3:
                bp.set(x, OH, z, stp(TS, OPPOSITE[_face_to(ox, oz, x, z)], "top"))
                bp.set(x, 0, z, BASE.pick(x, 0, z))
                bp.set(x, 1, z, stp(BS, _face_to(ox, oz, x, z)))
    for (dx, dz) in ((orr, 0), (-orr, 0), (0, orr), (orr - 2, orr - 2), (-orr + 2, orr - 2), (orr - 2, -orr + 2),
                     (-orr + 2, -orr + 2)):
        x, z = ox + dx, oz + dz
        for y in range(3, 10):
            bp.set(x, y, z, G1 if y < 9 else T.pick(x, y, z))
    for (dx, dz) in ((orr, orr - 3), (orr, -orr + 3), (-orr, orr - 3), (-orr, -orr + 3),
                     (orr - 3, orr), (-orr + 3, orr)):
        x, z = ox + dx + (1 if dx > 0 else -1 if dx < 0 else 0), oz + dz + (1 if dz > 0 else -1 if dz < 0 else 0)
        for y in range(0, OH - 2):
            bp.set(x, y, z, T.pick(x, y, z))
        bp.set(x, OH - 2, z, stp(TS, _face_to(ox, oz, x, z)))
    spire2(bp, ox, oz, OH + 1, orr + 1, R, steep=2, shape="octagon", tip=2)
    bp.clear(ox - 1, 1, HZ1, ox + 1, 4, oz - orr)
    for x in (ox - 2, ox + 2):
        for z in range(HZ1 + 1, oz - orr + 1):
            for y in range(0, 6):
                bp.set(x, y, z, W.pick(x, y, z))
    for z in range(HZ1 + 1, oz - orr + 1):
        for x in range(ox - 1, ox + 2):
            bp.set(x, 0, z, "polished_deepslate")
            bp.set(x, 5, z, W.pick(x, 5, z))
        bp.set(ox - 2, 6, z, stp(TS, "west"))
        bp.set(ox + 2, 6, z, stp(TS, "east"))
        bp.set(ox, 6, z, PGS)
        bp.set(ox - 1, 6, z, slb(PGS_SL))
        bp.set(ox + 1, 6, z, slb(PGS_SL))
    gwindow(bp, "south", HZ1, ox, 1, 3, "air", CGS, TS, w=3, hood=False)
    bp.disk(ox, 1, oz, 2, "dark_oak_planks")
    bp.set(ox, 2, oz, "cartography_table")
    for (dx, dz, f) in ((0, -3, "south"), (0, 3, "north"), (-3, 0, "east"), (3, 0, "west")):
        bp.stairs(ox + dx, 1, oz + dz, "dark_oak_stairs", f)
    great_chandelier(bp, ox, OH - 2, oz, OH + 6, r=2)
    for (dx, dz) in ((-4, 2), (4, 2), (-2, 4), (2, 4), (-4, -2), (4, -2)):
        for y in range(1, 4):
            bp.set(ox + dx, y, oz + dz, shelf)
    bp.chest(ox, 1, oz + 5, "north", LOOT + "library")

    # ---------------------------------------------------------- east front: twin towers, narthex, rose window
    FX = HX1
    for z in range(HZ0, HZ1 + 1):
        bp.set(FX, 0, z, BASE.pick(FX, 0, z))
        bp.set(FX, 1, z, BASE.pick(FX, 1, z))
    rose(bp, "east", FX, CZ, 16, 5, "chiseled_tuff_bricks", ["yellow_stained_glass", "orange_stained_glass",
                                                             "cyan_stained_glass", "blue_stained_glass",
                                                             "purple_stained_glass"],
         center="yellow_stained_glass", ring="polished_tuff")
    for u, yy in ((CZ - 2, 27), (CZ, 29), (CZ + 2, 27)):
        gwindow(bp, "east", FX, u, yy, 3 + (yy == 29), G2, CGS, TS, w=1)
    gwindow(bp, "east", FX, CZ, 1, 6, "air", CGS, TS, w=5, hood=True)
    for y in range(1, 7):
        bp.set(FX, y, CZ - 2, "tuff_brick_wall")
        bp.set(FX, y, CZ + 2, "tuff_brick_wall")
    bp.door(FX, 1, CZ - 1, "east", "dark_oak", hinge="left")
    bp.door(FX, 1, CZ + 1, "east", "dark_oak", hinge="right")
    bp.set(FX, 1, CZ, "air")
    bp.set(FX, 2, CZ, "air")
    # narthex (vaulted porch) between the towers
    NX = FX + 7
    bp.clear(FX + 1, 1, HZ0 + 5, NX - 1, 10, HZ1 - 5)
    pave(bp, FX + 1, HZ0 + 5, NX, HZ1 - 5, 0, Palette({"polished_tuff": 2, "tuff_bricks": 1}, seed=5))
    for u in range(HZ0 + 5, HZ1 - 4):
        for y in range(0, 12):
            pset(bp, "east", NX, u, 0, y, W)
    for zc in (CZ - 5, CZ, CZ + 5):
        gwindow(bp, "east", NX, zc, 1, 4 + (zc == CZ), "air", CGS, TS, w=3, hood=True)
        A.buttress(bp, "east", NX, zc - 3, 0, 10, T.pick(zc, 0, 0), TS, 2) if zc != CZ - 5 else None
    for z in range(HZ0 + 5, HZ1 - 4):
        bp.set(NX + 1, 11, z, stp(TS, "west", "top"))
        bp.set(NX, 12, z, "tuff_brick_wall" if z % 2 else "chiseled_tuff_bricks")
        for x in range(FX + 1, NX):
            bp.set(x, 11, z, W.pick(x, 11, z))
            bp.set(x, 12, z, "moss_carpet" if (x * z) % 7 == 0 else "air") if x < NX else None
    for k in range(5):
        for u in (CZ - 4 + k, CZ + 4 - k):
            fset(bp, "east", NX, u, 0, 12 + k, stp(TS, "south" if u < CZ else "north"))
        for u in range(CZ - 3 + k, CZ + 4 - k):
            fset(bp, "east", NX, u, 0, 12 + k, W)
    fset(bp, "east", NX, CZ, 0, 16, "chiseled_tuff_bricks")
    pinnacle(bp, NX, 17, CZ, "chiseled_tuff_bricks", CW, h=2)
    for z in (CZ - 3, CZ + 3):
        bp.lantern(FX + 3, 9, z, hanging=True)
        bp.chain(FX + 3, 10, z, 10)
    for x in range(FX + 1, NX):
        for z in range(CZ - 1, CZ + 2):
            bp.set(x, 0, z, "red_terracotta" if z == CZ else "polished_deepslate")
    for i in range(1, 4):
        for z in range(CZ - 4, CZ + 5):
            bp.set(NX + i, 1 - i, z, stp(BS, "west"))
    # twin towers
    for (tz0, tz1, secret) in ((HZ0 - 4, HZ0 + 4, False), (HZ1 - 4, HZ1 + 4, True)):
        tx0, tx1 = FX, FX + 8
        tcx, tcz = FX + 4, (tz0 + tz1) // 2
        TH = 36
        bp.clear(tx0 + 1, 1, tz0 + 1, tx1 - 1, TH - 1, tz1 - 1)
        for face, line, a, b in (("east", tx1, tz0, tz1), ("north", tz0, tx0, tx1), ("south", tz1, tx0, tx1),
                                 ("west", tx0, tz0, tz1)):
            A.facade(bp, face, line, a, b, 0, TH, W, T, pilaster_every=8, window_y=4, window_h=4,
                     floors=[0, 12, 24] if face != "west" else [24], floor_band=T, plinth=BASE,
                     plinth_stairs=BS, cornice_stairs=TS, sill=TS, glass=G2)
            for u in (a, b):
                A.buttress(bp, face, line, u, 0, 26, T.pick(u, 1, line), TS, 2)
            gwindow(bp, face, line, (a + b) // 2, 28, 4, "air", CGS, TS, w=3, sill=TS)
            for y in (12, 24):
                for u in range(a, b + 1):
                    fset(bp, face, line, u, 1, y, stp(TS, OPPOSITE[face], "top"))
        pave(bp, tx0 + 1, tz0 + 1, tx1 - 1, tz1 - 1, 0, BASE)
        for fy in (12, 24, 27):
            bp.fill(tx0 + 1, fy, tz0 + 1, tx1 - 1, fy, tz1 - 1, "dark_oak_planks")
            bp.set(tx1 - 1, fy, tz0 + 1, "air")
            bp.lantern(tcx, fy - 1, tcz, hanging=True)
        bp.ladder(tx1 - 1, 1, tz0 + 1, TH - 1, "south")
        bp.fill(tx0, TH, tz0, tx1, TH, tz1, T.pick(0, 0, 0))
        for x in range(tx0, tx1 + 1):
            for z in range(tz0, tz1 + 1):
                if x in (tx0, tx1) or z in (tz0, tz1):
                    bp.set(x, TH + 1, z, "tuff_brick_wall" if (x + z) % 2 else "chiseled_tuff_bricks")
        for (x, z) in ((tx0, tz0), (tx1, tz0), (tx0, tz1), (tx1, tz1)):
            pinnacle(bp, x, TH + 1, z, "polished_tuff", R, h=3)
        spire2(bp, tcx, tcz, TH + 1, 4, R, steep=4, shape="octagon", tip=3)
        if secret:
            # secret study: only reachable by breaking two bookshelves in the hall's south-east corner
            sx = tx0
            bp.set(sx, 1, HZ1 - 2, shelf)
            bp.set(sx, 2, HZ1 - 2, shelf)
            bp.set(sx - 1, 1, HZ1 - 2, "air")
            bp.set(sx - 1, 2, HZ1 - 2, "air")
            for x in range(tx0 + 1, tx1):
                for z in (tz0 + 1, tz1 - 1):
                    if x != tx1 - 1:
                        bp.set(x, 1, z, shelf)
                        bp.set(x, 2, z, shelf)
            bp.set(tcx, 1, tcz, "enchanting_table")
            bp.chest(tx0 + 1, 1, tcz + 2, "east", LOOT + "library_secret")
            bp.set(tx0 + 1, 1, tcz - 1, "lectern[facing=east,has_book=false,powered=false]")
            bp.set(tcx + 2, 1, tcz, "candle[candles=4,lit=true,waterlogged=false]")
            bp.set(tx0 + 1, 1, tcz + 1, "cobweb")
            bp.set(tcx, 1, tcz + 2, "purple_carpet")
            bp.set(tcx, 1, tcz - 2, "purple_carpet")
            for z in range(tz0 + 1, tz1):
                for y in (1, 2):
                    bp.set(tx0, y, z, W.pick(tx0, y, z)) if z != HZ1 - 2 else None
        else:
            bp.set(tx0 + 2, 1, tz1, "air")
            bp.set(tx0 + 2, 2, tz1, "air")
            bp.door(tx0 + 2, 1, tz1, "south", "dark_oak")
            bp.barrel(tx0 + 1, 13, tz0 + 1, "up", None)
            bp.set(tcx, 25, tcz, "cartography_table")
        bp.set(tcx, TH - 2, tcz, "bell[attachment=ceiling,facing=north,powered=false]") if not secret else None

    # ---------------------------------------------------------- west rotunda (domed reading room, half collapsed)
    rcx, rcz, rr, RH = 8, CZ, 8, 22
    for x in range(rcx - rr - 1, rcx + rr + 2):
        for z in range(rcz - rr - 1, rcz + rr + 2):
            d = math.hypot(x - rcx, z - rcz)
            if d <= rr + 0.4:
                bp.set(x, 0, z, floor.pick(x, 0, z))
                for y in range(1, RH + 1):
                    bp.set(x, y, z, W.pick(x, y, z) if d > rr - 0.8 else "air")
            if rr + 0.4 < d <= rr + 1.4:
                bp.set(x, 0, z, BASE.pick(x, 0, z))
                bp.set(x, 1, z, stp(BS, _face_to(rcx, rcz, x, z)))
    for k in range(10):
        a = math.radians(k * 36 + 18)
        x, z = rcx + round(math.cos(a) * rr), rcz + round(math.sin(a) * rr)
        if x >= HX0 - 1:
            continue
        for y in range(4, 19):
            bp.set(x, y, z, (G1 if y < 11 else G2) if y not in (11, 18) else T.pick(x, y, z))
        ab = a + math.radians(18)
        bx, bz = rcx + round(math.cos(ab) * (rr + 1)), rcz + round(math.sin(ab) * (rr + 1))
        for y in range(1, RH - 2):
            bp.set(bx, y, bz, T.pick(bx, y, bz))
        bp.set(bx, RH - 2, bz, stp(TS, _face_to(rcx, rcz, bx, bz)))
    for (x, z) in round_ring(rcx, rcz, rr + 1):
        if math.hypot(x - rcx, z - rcz) > rr + 0.5:
            bp.set(x, RH, z, stp(TS, OPPOSITE[_face_to(rcx, rcz, x, z)], "top"))
    bp.disk(rcx, RH + 1, rcz, rr, T.pick(0, 0, 0), hollow=True)
    A.dome(bp, rcx, RH + 1, rcz, rr, Palette({CW[0]: 3, "waxed_weathered_copper": 1}, seed=7), ribs="polished_tuff",
           oculus=False)
    bp.cylinder(rcx, RH + rr + 1, rcz, RH + rr + 4, 1, "chiseled_tuff_bricks")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(rcx + dx, RH + rr + 2, rcz + dz, G2)
        bp.set(rcx + dx, RH + rr + 3, rcz + dz, G2)
    cone(bp, rcx, rcz, RH + rr + 5, 2, CW, h=5)
    # rotunda interior: ring of bookcases, central reading desk
    for (x, z) in round_ring(rcx, rcz, rr - 2):
        if math.hypot(x - rcx, z - rcz) > rr - 2.5 and (math.atan2(z - rcz, x - rcx) % 0.9) > 0.25 and x < rcx + 4:
            for y in range(1, 5):
                bp.set(x, y, z, shelf)
    bp.disk(rcx, 1, rcz, 1, "dark_oak_planks")
    bp.set(rcx, 2, rcz, "lectern[facing=east,has_book=false,powered=false]")
    great_chandelier(bp, rcx, 15, rcz, RH + rr - 1, r=2)
    for (x, z) in round_ring(rcx, rcz, rr - 1):
        if math.hypot(x - rcx, z - rcz) > rr - 1.5:
            bp.set(x, 11, z, "dark_oak_planks" if x < HX0 - 1 else bp.get(x, 11, z) or "air")
    # open the hall into the rotunda with a tall arch
    gwindow(bp, "west", HX0, CZ, 1, 9, "air", CGS, TS, w=5, hood=False)

    # ---------------------------------------------------------- the ruin: collapsed north-west quarter
    rng = random.Random(77)
    for (x, y, z), b in list(bp.blocks.items()):
        if x < 30 and z < CZ - 1 and y > 3:
            n = math.sin(x * 0.5) * 2 + math.cos(z * 0.7) * 2 + rng.uniform(-1.5, 1.5)
            cut = 14 + (x - 4) * 0.5 + n + (z - 2) * 0.6
            if y > cut and b[0] != "minecraft:spawner" and b[0] != "minecraft:chest":
                bp.blocks[(x, y, z)] = ("minecraft:air", {}, None) if (x < HX0 - 1 or HZ0 < z or y > HE + 1) \
                    else bp.blocks[(x, y, z)]
                if HZ0 - 3 <= z <= HZ0 + 1 and x >= HX0 - 1 and y > cut + 2:
                    bp.blocks[(x, y, z)] = ("minecraft:air", {}, None)
    A.rubble(bp, 1, 11, 24, CZ - 2, 1, 60, blocks=("tuff_bricks", "tuff", "cobblestone", "mossy_cobblestone",
                                                   "polished_tuff", "gravel"), seed=4)
    A.rubble(bp, HX0 - 2, HZ0 - 4, 30, HZ0 - 1, 1, 25, blocks=("tuff_bricks", "tuff", "mossy_cobblestone",
                                                               "moss_block"), seed=5)
    for (x, z) in ((4, 14), (10, 12), (20, 9), (13, 15)):
        bp.set(x, 1, z, leaves("azalea_leaves") if (x + z) % 2 else leaves("flowering_azalea_leaves"))
    A.dark_tree(bp, 6, 1, 14, 10, seed=3)
    for (x, z) in ((19, 10), (23, 12), (12, 20), (26, 14)):
        bp.set(x, 1, z, "cobweb")
        bp.set(x, 4, z + 1, "cobweb")
    A.moss_on(bp, ((-4, 0, -6), (32, 40, CZ)), chance=0.4, seed=8,
              mapping={"minecraft:tuff_bricks": "mossy_stone_bricks", "minecraft:polished_tuff": "mossy_cobblestone",
                       "minecraft:dark_oak_planks": "moss_block", "minecraft:polished_deepslate": "moss_block"})
    A.vines_on(bp, ((-4, 1, -6), (32, 40, 12)), chance=0.12, seed=9, max_len=6)
    A.vines_on(bp, ((-4, 1, -6), (2, 40, 40)), chance=0.1, seed=10, max_len=6)
    A.vines_on(bp, ((-4, 1, -6), (80, 30, 40)), chance=0.012, seed=11, max_len=4)

    # ---------------------------------------------------------- forecourt and forest setting
    court = Palette({"tuff_bricks": 3, "cobblestone": 2, "mossy_cobblestone": 2, "gravel": 1, "moss_block": 1},
                    seed=88, scale=2.0)
    pave(bp, NX + 1, CZ - 6, NX + 13, CZ + 6, 0, court, chance=0.9, seed=1, keep=True)
    path_line(bp, [(NX + 13, CZ), (NX + 16, CZ + 2)], 0, court, width=3, seed=2)
    for (x, z) in ((NX + 6, CZ - 6), (NX + 6, CZ + 6), (NX + 12, CZ - 6), (NX + 12, CZ + 6)):
        lamp_post(bp, x, 1, z, post="dark_oak_fence", h=3, base="chiseled_tuff_bricks")
    for (x, z) in ((NX + 9, CZ - 4), (NX + 9, CZ + 4)):     # weathered statues on plinths
        bp.set(x, 1, z, "chiseled_tuff_bricks")
        bp.set(x, 2, z, "polished_tuff")
        bp.set(x, 3, z, "tuff_brick_wall")
        bp.set(x, 4, z, "chiseled_tuff")
    for (x, z, s) in ((NX + 4, -5, 1), (NX + 8, 40, 2), (40, -6, 3), (60, 44, 4), (-3, 32, 5), (24, 44, 6)):
        A.big_oak(bp, x, 1, z, 9, seed=s, crown=4) if s % 2 else A.birch(bp, x, 1, z, 8, seed=s)
    A.dark_tree(bp, 26, 1, -6, 9, seed=7)
    A.boulder(bp, NX + 16, 1, -4, 2, seed=1, blocks=("tuff", "andesite", "mossy_cobblestone"))
    for x in range(-5, NX + 12):
        for z in range(-6, 50):
            if not bp.get(x, 0, z):
                bp.set(x, 0, z, "grass_block[snowy=false]" if (x * 3 + z * 7) % 11 else "podzol[snowy=false]")
    A.landscape(bp, -5, -6, NX + 12, 50, 1, density=0.3, seed=21,
                flowers=("fern", "fern", "lily_of_the_valley", "allium", "azure_bluet", "oxeye_daisy"))
    skirt(bp, 0, depth=5, spread=2, seed=31)
    lair_archivist.build(bp)            # secret study stair -> buried scriptorium -> Forbidden Archive


register(StructureDef(
    "forgotten_library", "overworld",
    ["forest", "birch_forest", "dark_forest", "flower_forest", "old_growth_birch_forest", "taiga",
     "plains"],
    [Piece("library", library)], spacing=34, separation=12,
    spawns=[("wayfarers:map_wraith", 10, 1, 2)],
    title_fr="Bibliothèque oubliée", title_en="Forgotten Library"))


# ================================================================== COASTAL LIGHTHOUSE
def lighthouse(bp):
    rock = Palette({"stone": 5, "andesite": 3, "tuff": 2, "cobblestone": 1, "diorite": 1, "mossy_cobblestone": 1},
                   seed=301, scale=3.5)
    SB = Palette({"stone_bricks": 5, "cracked_stone_bricks": 1, "mossy_stone_bricks": 2, "andesite": 1}, seed=302)
    WHITE = Palette({"calcite": 4, "polished_diorite": 1}, seed=303)
    RED = Palette({"red_terracotta": 4, "bricks": 1}, seed=304)
    CO = ("waxed_cut_copper", "waxed_cut_copper_stairs", "waxed_cut_copper_slab")
    TOP = 10                                   # plateau height of the rocky cape
    rng = random.Random(5)

    # ---------------------------------------------------------- the sea, the beach and the rocky cape
    for x in range(-30, 34):
        for z in range(-18, 32):
            sea = z > 4 - (x + 30) * 0.12 + math.sin(x * 0.3) * 1.5 or x < -20 + math.cos(z * 0.4) * 2
            if sea:
                depth = 3 + int(min(4, max(0, (z - 8) * 0.25)))
                bp.set(x, -depth - 1, z, "sand" if (x + z) % 5 else "gravel")
                for y in range(-depth, 0):
                    bp.set(x, y, z, "water")
                if rng.random() < 0.12:
                    bp.set(x, -depth, z, "seagrass")
                elif rng.random() < 0.03 and depth > 2:
                    for k in range(depth - 1):
                        bp.set(x, -depth + k, z, "kelp_plant" if k < depth - 2 else "kelp[age=20]")
            else:
                bp.set(x, 0, z, "sand" if x > 12 or z > -6 else "grass_block[snowy=false]")
                bp.set(x, -1, z, "sand")
    ccx, ccz, crx, crz = 0, -2, 20, 14
    for x in range(ccx - crx - 3, ccx + crx + 4):
        for z in range(ccz - crz - 3, ccz + crz + 4):
            d = math.hypot((x - ccx) / crx, (z - ccz) / crz)
            n = math.sin(x * 0.45) * 0.07 + math.cos(z * 0.5 + 1) * 0.07 + math.sin((x + z) * 0.9) * 0.04
            dd = d + n
            if dd > 1.0:
                continue
            fall = max(0.0, (dd - 0.62) / 0.38)
            h = TOP - int(round((fall ** 1.6) * (TOP + 2)))
            for y in range(-6, h + 1):
                bp.set(x, y, z, rock.pick(x, y, z))
            if h >= TOP - 1:
                bp.set(x, h, z, "grass_block[snowy=false]" if (x * 7 + z) % 9 else "coarse_dirt")
            elif h > 1 and rng.random() < 0.3:
                bp.set(x, h, z, "moss_block")
    # sea stacks and boulders
    for (x, z, r, hh) in ((-24, 14, 3, 8), (-17, 22, 2, 4), (22, 22, 2, 3), (-26, -6, 2, 5)):
        for y in range(-6, hh + 1):
            t = (y + 6) / (hh + 6)
            rr = r * (1.15 - 0.6 * t)
            for dx in range(-r - 1, r + 2):
                for dz in range(-r - 1, r + 2):
                    if math.hypot(dx * 1.1, dz) <= rr + rng.uniform(-0.4, 0.4):
                        bp.set(x + dx, y, z + dz, rock.pick(x + dx, y, z + dz))
        bp.set(x, hh + 1, z, "moss_block")

    # ---------------------------------------------------------- the lighthouse
    LX, LZ = -4, -3
    y0 = TOP
    for x in range(LX - 9, LX + 10):
        for z in range(LZ - 9, LZ + 10):
            d = _dist(x - LX, z - LZ, "octagon")
            if d <= 8.3:
                for y in range(y0 - 3, y0 + 1):
                    bp.set(x, y, z, SB.pick(x, y, z))
            if 7.3 < d <= 8.3:
                bp.set(x, y0 + 1, z, stp("stone_brick_stairs", _face_to(LX, LZ, x, z)))
    SH0, SH1 = y0 + 9, y0 + 37          # shaft (tapered, banded)

    def rad(y):
        if y < SH0:
            return 6.0
        nb = (SH1 - SH0) // 4
        return 5.4 - 1.5 * ((y - SH0) // 4) / nb
    for y in range(y0 + 1, SH1 + 1):
        r = rad(y)
        for x in range(LX - 7, LX + 8):
            for z in range(LZ - 7, LZ + 8):
                d = math.hypot(x - LX, z - LZ)
                if d <= r + 0.4:
                    if d > r - 0.9:
                        if y < SH0:
                            b = SB.pick(x, y, z)
                        else:
                            b = (RED if ((y - SH0) // 4) % 2 else WHITE).pick(x, y, z)
                        bp.set(x, y, z, b)
                    else:
                        bp.set(x, y, z, "air")
    for (x, z) in round_ring(LX, LZ, 7):
        bp.set(x, SH0, z, stp("stone_brick_stairs", OPPOSITE[_face_to(LX, LZ, x, z)], "top"))
    bp.disk(LX, y0, LZ, 5, "polished_andesite")
    # central newel + spiral stair of slabs up to the watch room
    for y in range(y0 + 1, SH1 - 3):
        bp.set(LX, y, LZ, "stone_bricks")
    ring = []
    for x in range(LX - 2, LX + 3):
        for z in range(LZ - 2, LZ + 3):
            if max(abs(x - LX), abs(z - LZ)) == 2:
                ring.append((x, z))
    ring.sort(key=lambda p: math.atan2(p[1] - LZ, p[0] - LX))
    i = 0
    for y in range(y0 + 1, SH1 - 3):
        for half in ("bottom", "top"):
            x, z = ring[i % len(ring)]
            bp.slab(x, y, z, "stone_brick_slab", half)
            i += 1
    for k, y in enumerate(range(y0 + 5, SH1 - 3, 4)):
        a = math.radians(k * 75 + 40)
        r = rad(y)
        x, z = LX + round(math.cos(a) * r), LZ + round(math.sin(a) * r)
        bp.set(x, y, z, "glass_pane")
        bp.set(x, y + 1, z, "glass_pane")
    for y in range(y0 + 3, SH1 - 3, 7):
        bp.set(LX + 1, y, LZ, "wall_torch[facing=east]")
    # entrance (south) with arch and steps
    A.arch_door(bp, "south", LZ + 6, LX, y0, width=1, height=2, trim="chiseled_stone_bricks",
                stairs="stone_brick_stairs")
    for dz in (5, 6):
        bp.set(LX, y0 + 1, LZ + dz, "air")
        bp.set(LX, y0 + 2, LZ + dz, "air")
    bp.door(LX, y0 + 1, LZ + 6, "south", "spruce")
    wall_lamp(bp, "south", LZ + 6, LX - 2, y0 + 3, "stone_brick_stairs")
    wall_lamp(bp, "south", LZ + 6, LX + 2, y0 + 3, "stone_brick_stairs")
    # watch room at the top of the shaft
    WR = SH1 - 3
    bp.disk(LX, WR, LZ, 3, "spruce_planks")
    bp.ladder(LX, WR + 1, LZ - 3, SH1 + 1, "south")
    bp.set(LX, WR, LZ - 3, "ladder[facing=south,waterlogged=false]")
    bp.set(LX, WR - 1, LZ - 3, "ladder[facing=south,waterlogged=false]")
    bp.set(LX - 1, WR - 1, LZ - 2, "air")
    bp.chest(LX + 2, WR + 1, LZ, "west", LOOT + "lighthouse")
    bp.set(LX - 2, WR + 1, LZ, "cartography_table")
    bp.set(LX, WR + 1, LZ + 2, "lectern[facing=north,has_book=false,powered=false]")
    for (x, z) in ((LX, LZ + 4), (LX + 4, LZ), (LX - 4, LZ)):
        bp.set(x, WR + 2, z, "glass_pane")
        bp.set(x, WR + 3, z, "glass_pane")
    # gallery on corbels, iron railing
    G = SH1 + 1
    for rr_ in (4, 5):
        for (x, z) in round_ring(LX, LZ, rr_):
            if math.hypot(x - LX, z - LZ) > rr_ - 0.5:
                bp.set(x, SH1 - (5 - rr_), z, stp("polished_andesite_stairs", OPPOSITE[_face_to(LX, LZ, x, z)], "top"))
    bp.disk(LX, G, LZ, 5, "polished_andesite")
    bp.disk(LX, G + 1, LZ, 5, "iron_bars", hollow=True)
    # lamp room: copper mullions, glass, a blazing core
    for y in range(G + 1, G + 6):
        for (x, z) in round_ring(LX, LZ, 3):
            a = math.degrees(math.atan2(z - LZ, x - LX)) % 45
            bp.set(x, y, z, "waxed_cut_copper" if (a < 8 or a > 37) else "glass_pane")
    bp.disk(LX, G + 1, LZ, 2, "air")
    for y in range(G + 2, G + 6):
        bp.disk(LX, y, LZ, 2, "air")
    bp.set(LX, G + 1, LZ, "sea_lantern")
    bp.set(LX, G + 2, LZ, "glowstone")
    bp.set(LX, G + 3, LZ, "sea_lantern")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(LX + dx, G + 2, LZ + dz, "sea_lantern")
        bp.set(LX + dx, G + 3, LZ + dz, "end_rod[facing=%s]" % {(1, 0): "east", (-1, 0): "west", (0, 1): "south",
                                                                 (0, -1): "north"}[(dx, dz)])
    bp.set(LX, G + 4, LZ, "copper_bulb[lit=true,powered=false]")
    bp.set(LX, G, LZ - 3, "ladder[facing=south,waterlogged=false]")
    bp.set(LX, G + 1, LZ - 3, "air")
    bp.set(LX, G + 2, LZ - 3, "air")
    bp.disk(LX, G + 6, LZ, 3, CO[0])
    for (x, z) in round_ring(LX, LZ, 4):
        if math.hypot(x - LX, z - LZ) > 3.5:
            bp.set(x, G + 6, z, stp(CO[1], OPPOSITE[_face_to(LX, LZ, x, z)], "top"))
    A.dome(bp, LX, G + 6, LZ, 3, Palette({CO[0]: 3, "waxed_copper_block": 1}, seed=3), ribs=None, oculus=False)
    bp.set(LX, G + 10, LZ, CO[0])
    bp.set(LX, G + 11, LZ, "waxed_copper_grate")
    bp.set(LX, G + 12, LZ, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # ---------------------------------------------------------- keeper's cottage
    kx0, kx1, kz0, kz1 = 7, 16, -11, -4
    plaster = Palette({"calcite": 3, "white_terracotta": 1}, seed=7)
    pave(bp, kx0, kz0, kx1, kz1, TOP, Palette({"spruce_planks": 3, "stripped_spruce_wood": 1}, seed=2))
    bp.clear(kx0 + 1, TOP + 1, kz0 + 1, kx1 - 1, TOP + 8, kz1 - 1)
    for face, line, a, b in (("south", kz1, kx0, kx1), ("north", kz0, kx0, kx1), ("east", kx1, kz0, kz1),
                             ("west", kx0, kz0, kz1)):
        A.facade(bp, face, line, a, b, TOP, TOP + 4, SB, "stone_bricks", pilaster_every=3, window_y=2, window_h=2,
                 plinth=Palette({"cobblestone": 2, "mossy_cobblestone": 1}), plinth_stairs="cobblestone_stairs",
                 arched=False, sill=None)
    timber_storey(bp, kx0, kz0, kx1, kz1, TOP + 5, TOP + 8, "spruce_log", plaster, wood="spruce", post_every=3,
                  faces=("south", "north"))
    bp.fill(kx0 + 1, TOP + 5, kz0 + 1, kx1 - 1, TOP + 5, kz1 - 1, "spruce_planks")
    for face, line, a, b in (("east", kx1, kz0, kz1), ("west", kx0, kz0, kz1)):
        for u in range(a, b + 1):
            for y in range(TOP + 5, TOP + 9):
                pset(bp, face, line, u, 0, y, plaster)
    kr = roof(bp, kx0, kz0, kx1, kz1, TOP + 9, ROOF["slate"], axis="x", overhang=1, steep=1.25, gable=plaster,
              under="spruce_stairs")
    for x in (kx0, kx1):
        bp.set(x, TOP + 10, (kz0 + kz1) // 2, "glass_pane")
        bp.set(x, TOP + 11, (kz0 + kz1) // 2, "glass_pane")
    dormer(bp, "south", kz1, 12, TOP + 9, ROOF["slate"], plaster, trim="spruce_log[axis=y]")
    A.arch_door(bp, "south", kz1, 9, TOP, width=1, height=2, trim="spruce_log[axis=y]", stairs="spruce_stairs")
    bp.door(9, TOP + 1, kz1, "south", "spruce")
    bp.set(9, TOP, kz1 + 1, "stone_brick_stairs[facing=north,half=bottom]")
    A.fill_pal(bp, kx1 - 2, TOP + 1, kz0 - 1, kx1 - 1, kr + 2, kz0, SB)
    bp.set(kx1 - 2, kr + 2, kz0, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(kx1 - 2, TOP + 1, kz0 + 1, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=south]")
    bp.set(kx1 - 1, TOP + 1, kz0 + 1, "smoker[facing=south,lit=true]")
    bp.set(kx1 - 3, TOP + 1, kz0 + 1, "barrel[facing=up,open=false]")
    bp.table(12, TOP + 1, -7, "spruce_pressure_plate", "spruce_fence")
    bp.stairs(11, TOP + 1, -7, "spruce_stairs", "east")
    bp.stairs(13, TOP + 1, -7, "spruce_stairs", "west")
    bp.chest(kx0 + 1, TOP + 1, kz0 + 1, "south", LOOT + "lighthouse")
    bp.set(kx0 + 1, TOP + 1, kz1 - 1, "bookshelf")
    bp.set(kx0 + 1, TOP + 2, kz1 - 1, "potted_blue_orchid")
    bp.lantern(12, TOP + 4, -7, hanging=True)
    bp.bed(kx1 - 2, TOP + 6, kz1 - 2, "north", "light_blue")
    bp.set(kx1 - 1, TOP + 6, kz1 - 1, "barrel[facing=up,open=false]")
    bp.set(kx0 + 1, TOP + 6, kz0 + 1, "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=false,"
           "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=true]")
    for i in range(4):
        bp.stairs(kx0 + 2 + i, TOP + 1 + i, kz0 + 1, "spruce_stairs", "east")
    bp.fill(kx0 + 2, TOP + 5, kz0 + 1, kx0 + 5, TOP + 5, kz0 + 1, "air")
    bp.lantern(12, TOP + 8, -7, hanging=True)
    # lean-to net shed on the east side
    for z in range(kz0 + 1, kz1):
        bp.set(kx1 + 3, TOP + 1, z, "spruce_fence") if z in (kz0 + 1, kz1 - 1) else None
        bp.set(kx1 + 3, TOP + 2, z, "spruce_fence") if z in (kz0 + 1, kz1 - 1) else None
    lean_to(bp, "east", kx1 + 3, kz0, kz1, TOP + 3, 3, ROOF["spruce"])
    bp.barrel(kx1 + 1, TOP + 1, kz0 + 2, "up")
    bp.barrel(kx1 + 2, TOP + 1, kz0 + 2, "up")
    bp.set(kx1 + 1, TOP + 1, kz0 + 4, "cobweb")

    # ---------------------------------------------------------- waystone, garden, lamps on the plateau
    wx, wz = 10, 1
    for (x, z) in round_ring(wx, wz, 2):
        bp.set(x, TOP + 1, z, stp("stone_brick_stairs", _face_to(wx, wz, x, z)))
    bp.disk(wx, TOP + 1, wz, 1, "chiseled_stone_bricks")
    bp.set(wx, TOP + 2, wz, MOD["waystone"])
    for (x, z) in ((wx - 3, wz - 2), (wx + 3, wz + 2)):
        lamp_post(bp, x, TOP + 1, z, post="spruce_fence", h=3)
    for x in range(1, 6):
        bp.set(x, TOP, -9, "farmland[moisture=7]")
        bp.set(x, TOP + 1, -9, "wheat[age=7]")
        bp.set(x, TOP + 1, -10, "spruce_fence")
    bp.set(0, TOP + 1, -9, "composter[level=4]")
    for (x, z) in ((3, -6), (16, 0)):
        bp.set(x, TOP + 1, z, "spruce_fence")
        bp.set(x, TOP + 2, z, "spruce_fence")
    path_line(bp, [(LX, LZ + 8), (LX, 6), (8, 6), (8, 4)], TOP, Palette({"gravel": 2, "coarse_dirt": 1}), width=2,
              seed=4)
    path_line(bp, [(8, 4), (9, -3)], TOP, Palette({"gravel": 2, "coarse_dirt": 1}), width=2, seed=5)

    # ---------------------------------------------------------- stairs carved into the cliff, harbour, boat
    A.stair_run(bp, 7, 1, 15, "north", TOP, 2, "stone_brick_stairs", fill="stone_bricks", clear=4)
    for k in range(TOP):
        z = 15 - k
        for x in (6, 9):
            if (bp.get(x, k + 1, z) in (None, "minecraft:air", "minecraft:water")):
                bp.set(x, k + 1, z, "stone_brick_wall")
                for y in range(-3, k + 1):
                    bp.set(x, y, z, SB.pick(x, y, z), keep=True)
    lamp_post(bp, 6, 2, 13, post="stone_brick_wall", h=1)
    lamp_post(bp, 9, TOP - 3, 9, post="stone_brick_wall", h=1)
    # dock
    for z in range(16, 30):
        for x in range(5, 11):
            bp.set(x, 0, z, "spruce_planks" if (x + z) % 4 else "stripped_spruce_log[axis=z]")
        if z % 4 == 0:
            for x in (5, 10):
                for y in range(-6, 2):
                    bp.set(x, y, z, "spruce_log[axis=y]")
    for x in range(5, 11):
        bp.set(x, 0, 15, "stone_bricks")
        bp.set(x, 0, 16, "stone_bricks")
    for (x, z) in ((5, 28), (10, 28), (10, 20)):
        bp.lantern(x, 2, z)
    bp.barrel(6, 1, 26, "up", LOOT + "lighthouse")
    bp.barrel(6, 1, 25, "up")
    bp.set(7, 1, 26, "barrel[facing=north,open=false]")
    bp.set(9, 1, 18, "cauldron")
    # moored sloop
    bx = 13
    for z in range(18, 28):
        taper = 1 if z in (18, 27) else 0
        bp.set(bx, -2, z, "dark_oak_planks")
        for x in range(bx - 1 + taper, bx + 2 - taper):
            bp.set(x, -1, z, "spruce_planks")
        if not taper:
            bp.set(bx - 1, 0, z, "dark_oak_slab[type=bottom,waterlogged=false]" if 19 < z < 26 else "spruce_planks")
            bp.set(bx + 1, 0, z, "dark_oak_slab[type=bottom,waterlogged=false]" if 19 < z < 26 else "spruce_planks")
        bp.set(bx, -1, z, "spruce_planks")
    bp.set(bx, 0, 17, stp("spruce_stairs", "north"))
    bp.set(bx, 0, 28, stp("spruce_stairs", "south"))
    bp.set(bx, -1, 17, stp("spruce_stairs", "north", "top"))
    bp.set(bx, -1, 28, stp("spruce_stairs", "south", "top"))
    for y in range(0, 10):
        bp.set(bx, y, 22, "spruce_fence")
    for y in range(2, 9):
        for z in range(23, 23 + max(0, (9 - y) * 4 // 7) + 1):
            bp.set(bx, y, z, "white_wool")
    for y in range(3, 8):
        bp.set(bx, y, 21, "white_wool") if y < 7 else None
    bp.set(bx, 10, 22, "spruce_fence")
    bp.set(bx, 0, 25, "barrel[facing=up,open=false]")
    bp.set(bx, 0, 20, "chest[facing=north,type=single,waterlogged=false]")
    bp.set(11, 1, 22, "spruce_fence")

    # ---------------------------------------------------------- smugglers' sea cave (secret)
    for x in range(-22, -12):
        for z in range(-2, 4):
            for y in range(-1, 3):
                if math.hypot((x + 17) / 5, (y - 1) / 2.6) <= 1.0 and abs(z - 1) <= 2:
                    bp.set(x, y, z, "water" if y < 0 else "air")
    for x in range(-15, -12):
        for z in range(-1, 4):
            bp.set(x, 0, z, "spruce_planks")
            for y in range(1, 3):
                bp.set(x, y, z, "air")
    bp.chest(-13, 1, 3, "west", LOOT + "lighthouse")
    bp.spawner(-15, 1, 1, "minecraft:drowned")
    bp.barrel(-13, 1, -1, "up")
    bp.barrel(-14, 1, -1, "up")
    bp.set(-13, 3, 1, "lantern[hanging=true,waterlogged=false]")
    bp.set(-13, 4, 1, "iron_chain[axis=y,waterlogged=false]") if bp.get(-13, 4, 1) else None

    # ---------------------------------------------------------- vegetation and weathering
    A.landscape(bp, -20, -16, 20, 10, TOP + 1, density=0.35, seed=7,
                flowers=("short_grass", "fern", "dandelion", "oxeye_daisy", "azure_bluet", "cornflower"))
    for (x, z) in ((-14, -10), (14, 4), (-10, 6)):
        A.bush(bp, x, TOP + 1, z, "oak_leaves" if x > 0 else "azalea_leaves")
    for (x, z) in ((24, -4), (27, 6), (19, 9)):
        bp.set(x, 1, z, "dead_bush" if x % 2 else "short_dry_grass")
    for x in range(20, 24):
        bp.set(x, 1, 2, "stripped_oak_log[axis=x]")  # driftwood
    A.moss_on(bp, ((-30, -6, -18), (34, TOP + 30, 32)), chance=0.12, seed=9)
    A.vines_on(bp, ((-30, -2, -18), (34, TOP, 32)), chance=0.05, seed=3, max_len=4)


register(StructureDef(
    "coastal_lighthouse", "overworld", ["beach", "stony_shore", "snowy_beach"],
    [Piece("lighthouse", lighthouse)], spacing=28, separation=10, processors="aging",
    title_fr="Phare côtier", title_en="Coastal Lighthouse"))
