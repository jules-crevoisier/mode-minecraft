"""Architecture toolkit (v2): the building blocks for beautiful, monumental structures.

Everything works on a Blueprint `bp`. Conventions:
  * x = east, y = up, z = south. "facing" = the direction a facade looks OUT to.
  * Palettes are weighted material mixes with spatially coherent noise, so variation forms
    natural patches instead of salt-and-pepper speckle.
  * Helpers never clear terrain unless they say so; rooms use bp.clear()/bp.room().

Quick reference (see STYLE.md for how to combine them):
  Palette, fill_pal, wall_pal
  facade(...)            wall with plinth, pilasters, recessed arched windows, cornice
  arch_door(...)         arched doorway with steps
  buttress(...)          stepped buttress against a wall
  round_tower(...)       round tower: corbelled crown, crenels or steep spire roof, arrow slits
  square_tower(...)      square tower with corner quoins, belfry openings, pyramid/spire roof
  spire(...)             steep cone/pyramid with finial
  steep_roof(...)        gable roof with overhang trim, dormers, ridge
  dome(...)              ribbed dome with oculus
  stair_run(...)         straight staircase (any direction) with solid fill below
  terrain_skirt(...)     irregular rocky/earthy foundation so buildings sit naturally on slopes
  landscape(...)         grass, flowers, bushes, boulders over an area
  oak / spruce / birch / big_oak / dark_tree  realistic trees
  chandelier, hanging_lantern, banner_wall, vines_on, moss_on, rubble
  furnish(...)           furnished interiors: library, bedroom, kitchen, armory, treasury, chapel, study, storage
"""
import math
import random

from .blueprint import OPPOSITE, with_props

# ------------------------------------------------------------------ direction helpers
FACE_VEC = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
# for a facade facing F, the "along" axis (u) direction such that (u, out) is right-handed when viewed from outside
ALONG = {"north": (-1, 0), "south": (1, 0), "east": (0, -1), "west": (0, 1)}
LEFT_OF = {"north": "west", "south": "east", "east": "north", "west": "south"}
RIGHT_OF = {v: k for k, v in LEFT_OF.items()}


def stair(spec, facing, half="bottom"):
    return with_props(spec, facing=facing, half=half, shape="straight", waterlogged=False)


def slab(spec, kind="bottom"):
    return with_props(spec, type=kind, waterlogged=False)


# ------------------------------------------------------------------ palettes
class Palette:
    """Weighted material mix with coherent 3D value noise. Optional `accent` sprinkled rarely."""

    def __init__(self, weights, seed=0, scale=3.0, accent=None, accent_chance=0.0):
        if isinstance(weights, str):
            weights = {weights: 1}
        self.items = list(weights.items())
        self.total = sum(w for _, w in self.items)
        self.seed = seed
        self.scale = scale
        self.accent = accent
        self.accent_chance = accent_chance

    def _noise(self, x, y, z):
        def h(ix, iy, iz):
            n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (self.seed * 2654435761)
            n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
            return (n & 0xFFFF) / 65535.0
        s = self.scale
        fx, fy, fz = x / s, y / s, z / s
        ix, iy, iz = math.floor(fx), math.floor(fy), math.floor(fz)
        tx, ty, tz = fx - ix, fy - iy, fz - iz
        tx, ty, tz = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty), tz * tz * (3 - 2 * tz)
        c = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (tx if dx else 1 - tx) * (ty if dy else 1 - ty) * (tz if dz else 1 - tz)
                    c += w * h(ix + dx, iy + dy, iz + dz)
        return c

    def pick(self, x, y, z):
        if self.accent and self.accent_chance:
            n = ((x * 92821) ^ (y * 68917) ^ (z * 31337) ^ self.seed) % 1000
            if n < self.accent_chance * 1000:
                return self.accent
        v = self._noise(x, y, z) * 0.75 + (((x * 5 + y * 11 + z * 7 + self.seed) % 17) / 17.0) * 0.25
        acc = 0.0
        for item, w in self.items:
            acc += w / self.total
            if v <= acc:
                return item
        return self.items[-1][0]


def as_pal(p):
    return p if isinstance(p, Palette) else Palette(p)


def fill_pal(bp, x0, y0, z0, x1, y1, z1, pal):
    pal = as_pal(pal)
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                bp.set(x, y, z, pal.pick(x, y, z))


def wall_pal(bp, x0, y0, z0, x1, y1, z1, pal):
    """Four walls of a box with a palette."""
    pal = as_pal(pal)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            bp.set(x, y, z0, pal.pick(x, y, z0))
            bp.set(x, y, z1, pal.pick(x, y, z1))
        for z in range(z0, z1 + 1):
            bp.set(x0, y, z, pal.pick(x0, y, z))
            bp.set(x1, y, z, pal.pick(x1, y, z))


# ------------------------------------------------------------------ facades
def _pos(face, line, u, out):
    """Facade coordinates -> world (x, z). `line` = the wall plane coordinate (z for N/S, x for E/W)."""
    if face in ("north", "south"):
        return u, line + FACE_VEC[face][1] * out
    return line + FACE_VEC[face][0] * out, u


def facade(bp, face, line, u0, u1, y0, y1, wall, trim, *, pilaster_every=4, window=None, window_h=3,
           window_y=2, plinth=None, plinth_stairs=None, cornice_stairs=None, glass="glass_pane",
           sill=None, arched=True, floors=None, floor_band=None):
    """Decorated wall along u0..u1 (x for N/S facades, z for E/W), from y0 (floor) to y1 (top).

    wall/trim: palette or block. pilasters (trim) protrude 1 block every `pilaster_every`.
    window: None = automatic tall arched windows in every bay. floors: list of floor y's for
    multi-storey facades (windows repeated per floor, `floor_band` course between floors).
    plinth: base course block (default trim); *_stairs: stair block used for plinth slope and
    cornice (upside-down, protruding).
    """
    wall = as_pal(wall)
    trim_p = as_pal(trim)
    lo, hi = min(u0, u1), max(u0, u1)
    out_dir = face
    for u in range(lo, hi + 1):
        for y in range(y0, y1 + 1):
            x, z = _pos(face, line, u, 0)
            bp.set(x, y, z, wall.pick(x, y, z))
    # plinth
    pb = plinth or trim
    for u in range(lo, hi + 1):
        x, z = _pos(face, line, u, 0)
        bp.set(x, y0, z, as_pal(pb).pick(x, y0, z))
        if plinth_stairs:
            ox, oz = _pos(face, line, u, 1)
            bp.set(ox, y0, oz, stair(plinth_stairs, OPPOSITE[out_dir]))
    # pilasters
    pil = list(range(lo, hi + 1, pilaster_every))
    if pil[-1] != hi:
        pil.append(hi)
    for u in pil:
        for y in range(y0, y1 + 1):
            x, z = _pos(face, line, u, 0)
            bp.set(x, y, z, trim_p.pick(x, y, z))
            ox, oz = _pos(face, line, u, 1)
            bp.set(ox, y, oz, trim_p.pick(ox, y, oz))
        if plinth_stairs:
            ox, oz = _pos(face, line, u, 1)
            bp.set(ox, y0, oz, as_pal(pb).pick(ox, y0, oz))
    # floors bands
    floors = floors or [y0]
    if floor_band:
        for fy in floors[1:]:
            for u in range(lo, hi + 1):
                x, z = _pos(face, line, u, 0)
                bp.set(x, fy, z, as_pal(floor_band).pick(x, fy, z))
    # windows in each bay, each floor
    for fy in floors:
        top_limit = min(y1 - 1, fy + window_y + window_h)
        for a, b in zip(pil, pil[1:]):
            width = b - a - 1
            if width < 1:
                continue
            ww = 1 if width <= 2 else 2 if width <= 4 else 3
            start = a + 1 + (width - ww) // 2
            wy0 = fy + window_y
            wy1 = min(top_limit, wy0 + window_h - 1)
            if wy1 < wy0:
                continue
            for u in range(start, start + ww):
                x, z = _pos(face, line, u, 0)
                for y in range(wy0, wy1 + 1):
                    bp.set(x, y, z, glass)
                ox, oz = _pos(face, line, u, 1)
                if sill:
                    bp.set(ox, wy0 - 1, oz, stair(sill, OPPOSITE[out_dir], "top") if "stairs" in sill else sill)
            if arched and ww >= 2 and wy1 + 1 < y1:
                # arch: upside-down stairs at the two top corners, glass in the middle above
                ax0, az0 = _pos(face, line, start, 0)
                ax1, az1 = _pos(face, line, start + ww - 1, 0)
                st = cornice_stairs or (trim if isinstance(trim, str) and "stairs" in trim else None)
                if st:
                    side_dir = _along_dir(face)
                    bp.set(ax0, wy1, az0, stair(st, OPPOSITE[side_dir], "top"))
                    bp.set(ax1, wy1, az1, stair(st, side_dir, "top"))
            # lintel / keystone above
            mid = start + ww // 2
            kx, kz = _pos(face, line, mid, 0)
            bp.set(kx, wy1 + 1, kz, trim_p.pick(kx, wy1 + 1, kz))
    # cornice
    if cornice_stairs:
        for u in range(lo, hi + 1):
            ox, oz = _pos(face, line, u, 1)
            bp.set(ox, y1, oz, stair(cornice_stairs, OPPOSITE[out_dir], "top"))
            x, z = _pos(face, line, u, 0)
            bp.set(x, y1, z, trim_p.pick(x, y1, z))


def _along_dir(face):
    dx, dz = ALONG[face]
    return {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(dx, dz)]


def arch_door(bp, face, line, u, y, width=3, height=4, trim="stone_bricks", stairs="stone_brick_stairs",
              door=None, steps=None, steps_n=2):
    """Arched opening centred on u. Optionally a door (wood type) and outward steps."""
    half = width // 2
    for du in range(-half, half + 1):
        x, z = _pos(face, line, u + du, 0)
        ox, oz = _pos(face, line, u + du, 1)
        for dy in range(1, height + 1):
            bp.set(x, y + dy, z, "air")
            bp.set(ox, y + dy, oz, "air")  # keep plinths/sills of the facade out of the doorway
    # frame
    for du in (-half - 1, half + 1):
        for dy in range(1, height + 2):
            x, z = _pos(face, line, u + du, 0)
            bp.set(x, y + dy, z, trim)
            ox, oz = _pos(face, line, u + du, 1)
            bp.set(ox, y + dy, oz, trim)
    side = _along_dir(face)
    for du in range(-half, half + 1):
        x, z = _pos(face, line, u + du, 0)
        bp.set(x, y + height + 1, z, trim)
    lx, lz = _pos(face, line, u - half, 0)
    rx, rz = _pos(face, line, u + half, 0)
    if width >= 3:
        bp.set(lx, y + height, lz, stair(stairs, OPPOSITE[side], "top"))
        bp.set(rx, y + height, rz, stair(stairs, side, "top"))
    kx, kz = _pos(face, line, u, 1)
    bp.set(kx, y + height + 1, kz, trim)
    if door:
        dx, dz = _pos(face, line, u, 0)
        bp.door(dx, y + 1, dz, face, door)
        if width >= 3:
            ldx, ldz = _pos(face, line, u - 1, 0)
            rdx, rdz = _pos(face, line, u + 1, 0)
            bp.door(ldx, y + 1, ldz, face, door, hinge="left")
            bp.door(rdx, y + 1, rdz, face, door, hinge="right")
            # a stone mullion between the two leaves (an open gap would leave the door "unclosed")
            bp.set(dx, y + 1, dz, trim)
            bp.set(dx, y + 2, dz, trim)
    if steps:
        for i in range(1, steps_n + 1):
            for du in range(-half - 1, half + 2):
                x, z = _pos(face, line, u + du, i)
                bp.set(x, y + 1 - i, z, stair(steps, OPPOSITE[face]))
                for yy in range(y - 6, y + 1 - i):
                    bp.set(x, yy, z, trim, keep=True)


def buttress(bp, face, line, u, y0, h, block, stairs_block, depth=2):
    """Stepped buttress: full blocks near the wall, stairs sloping outward at each step."""
    for d in range(1, depth + 1):
        top = y0 + h - (d - 1) * max(1, h // (depth + 1)) - 1
        for y in range(y0, top + 1):
            x, z = _pos(face, line, u, d)
            bp.set(x, y, z, block)
        x, z = _pos(face, line, u, d)
        bp.set(x, top + 1, z, stair(stairs_block, OPPOSITE[face]))


# ------------------------------------------------------------------ towers, roofs, domes
def spire(bp, cx, cz, y, r, block, stairs_block=None, steep=2, finial="lightning_rod", round_=True):
    """Steep cone (round_) or pyramid. Each ring is `steep` blocks tall; stairs make the slope smooth."""
    yy = y
    rr = r
    while rr >= 1:
        for k in range(steep):
            for x in range(cx - rr - 1, cx + rr + 2):
                for z in range(cz - rr - 1, cz + rr + 2):
                    d = math.hypot(x - cx, z - cz) if round_ else max(abs(x - cx), abs(z - cz))
                    if d <= rr + 0.35:
                        on_edge = d > rr - 0.75
                        if on_edge and k == steep - 1 and stairs_block:
                            dx, dz = cx - x, cz - z
                            if abs(dx) >= abs(dz):
                                f = "east" if dx > 0 else "west"
                            else:
                                f = "south" if dz > 0 else "north"
                            bp.set(x, yy, z, stair(stairs_block, f))
                        elif on_edge or k == 0:
                            bp.set(x, yy, z, block)
            yy += 1
        rr -= 1
    bp.set(cx, yy, cz, block)
    bp.set(cx, yy + 1, cz, block)
    if finial:
        bp.set(cx, yy + 2, cz, finial if "[" in finial else (finial + "[facing=up,powered=false,waterlogged=false]"
                                                             if finial == "lightning_rod" else finial))
    return yy + 2


def round_tower(bp, cx, cz, y0, h, r, wall, *, trim=None, floor="spruce_planks", corbel_stairs=None,
                crown="crenels", roof_block=None, roof_stairs=None, slits=True, floors_every=6, ladder=True,
                windows="glass_pane", lights=True):
    """Round tower. crown: 'crenels' (battlements on a corbelled parapet) or 'spire' (steep roof)."""
    wall = as_pal(wall)
    for y in range(y0, y0 + h + 1):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.4:
                    if d > r - 0.8:
                        bp.set(x, y, z, wall.pick(x, y, z))
                    else:
                        bp.set(x, y, z, "air")
    bp.disk(cx, y0, cz, r, floor)
    for fy in range(y0 + floors_every, y0 + h, floors_every):
        bp.disk(cx, fy, cz, r - 1, floor)
        if lights:
            bp.chain(cx, fy - 1, cz, fy - 1)
            bp.lantern(cx, fy - 2, cz, hanging=True)
    if ladder:
        bp.ladder(cx, y0 + 1, cz - r + 1, y0 + h, "south")
    # slit windows in a spiral
    if slits:
        for i, fy in enumerate(range(y0 + 3, y0 + h - 1, 4)):
            a = math.radians(i * 70 + 30)
            x = cx + round(math.cos(a) * r)
            z = cz + round(math.sin(a) * r)
            bp.set(x, fy, z, windows)
            bp.set(x, fy + 1, z, windows)
    top = y0 + h
    if trim:
        bp.disk(cx, top, cz, r, trim, hollow=True)
    if corbel_stairs:
        for a in range(0, 360, 6):
            x = cx + round(math.cos(math.radians(a)) * (r + 1))
            z = cz + round(math.sin(math.radians(a)) * (r + 1))
            if math.hypot(x - cx, z - cz) > r + 0.5:
                dx, dz = x - cx, z - cz
                f = ("east" if dx > 0 else "west") if abs(dx) >= abs(dz) else ("south" if dz > 0 else "north")
                bp.set(x, top, z, stair(corbel_stairs, OPPOSITE[f], "top"))
    if crown == "crenels":
        bp.disk(cx, top + 1, cz, r + 1, trim or wall.pick(cx, top, cz))
        bp.disk(cx, top + 1, cz, r - 1, floor)
        if ladder:
            bp.set(cx, top + 1, cz - r + 1, "ladder[facing=south,waterlogged=false]")
            bp.set(cx, top, cz - r + 1, "ladder[facing=south,waterlogged=false]")
        k = 0
        for a in range(0, 360, 4):
            x = cx + round(math.cos(math.radians(a)) * (r + 1))
            z = cz + round(math.sin(math.radians(a)) * (r + 1))
            if math.hypot(x - cx, z - cz) > r + 0.5 and not bp.get(x, top + 2, z):
                k += 1
                bp.set(x, top + 2, z, wall.pick(x, top + 2, z) if k % 2 else "air")
                if k % 2:
                    bp.set(x, top + 3, z, slab(roof_stairs.replace("_stairs", "_slab")) if roof_stairs else "air")
        return top + 3
    roof_block = roof_block or "dark_oak_planks"
    bp.disk(cx, top + 1, cz, r + 1, roof_block)
    return spire(bp, cx, cz, top + 2, r + 1, roof_block, roof_stairs, steep=2)


def square_tower(bp, x0, z0, size, y0, h, wall, quoin, *, floor="spruce_planks", roof_block="dark_oak_planks",
                 roof_stairs="dark_oak_stairs", belfry=True, spire_steep=2, ladder=True, cornice_stairs=None):
    x1, z1 = x0 + size - 1, z0 + size - 1
    wall = as_pal(wall)
    for y in range(y0, y0 + h + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                if corner:
                    bp.set(x, y, z, quoin)
                elif edge:
                    bp.set(x, y, z, wall.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
    bp.fill(x0 + 1, y0, z0 + 1, x1 - 1, y0, z1 - 1, floor)
    for fy in range(y0 + 6, y0 + h - 1, 6):
        bp.fill(x0 + 1, fy, z0 + 1, x1 - 1, fy, z1 - 1, floor)
    if ladder:
        bp.ladder(x0 + 1, y0 + 1, z0 + 1, y0 + h, "south")
    top = y0 + h
    if belfry:
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        for dy in range(-4, -1):
            for x in range(x0 + 1, x1):
                bp.set(x, top + dy, z0, "air")
                bp.set(x, top + dy, z1, "air")
            for z in range(z0 + 1, z1):
                bp.set(x0, top + dy, z, "air")
                bp.set(x1, top + dy, z, "air")
        bp.set(cx, top - 1, cz, "bell[attachment=ceiling,facing=north,powered=false]")
    if cornice_stairs:
        for x in range(x0 - 1, x1 + 2):
            bp.set(x, top, z0 - 1, stair(cornice_stairs, "south", "top"))
            bp.set(x, top, z1 + 1, stair(cornice_stairs, "north", "top"))
        for z in range(z0, z1 + 1):
            bp.set(x0 - 1, top, z, stair(cornice_stairs, "east", "top"))
            bp.set(x1 + 1, top, z, stair(cornice_stairs, "west", "top"))
    bp.fill(x0, top, z0, x1, top, z1, roof_block)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    return spire(bp, cx, cz, top + 1, size // 2 + 1, roof_block, roof_stairs, steep=spire_steep, round_=False)


def steep_roof(bp, x0, z0, x1, z1, y, stairs_block, *, axis="x", overhang=1, steep=1, fill=None, under=None,
               ridge=None, dormers=0, dormer_stairs=None, dormer_wall=None):
    """Gable roof. steep=2 doubles the pitch (stair + full block per step). `under` lines the eave
    underside (upside-down stairs) for a crisp shadow line."""
    full = stairs_block.replace("_stairs", "_planks") if "planks" in stairs_block or "oak" in stairs_block or \
        "spruce" in stairs_block or "birch" in stairs_block else stairs_block.replace("_stairs", "")
    full = fill or full
    if axis == "x":
        lo, hi, a0, a1 = z0 - overhang, z1 + overhang, x0 - overhang, x1 + overhang
    else:
        lo, hi, a0, a1 = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
    yy = y
    i = 0
    while lo + i <= hi - i:
        for k in range(steep):
            for a in range(a0, a1 + 1):
                for side, f in ((lo + i, "south" if axis == "x" else "east"), (hi - i, "north" if axis == "x" else "west")):
                    p = (a, yy, side) if axis == "x" else (side, yy, a)
                    if lo + i == hi - i:
                        bp.set(*p, ridge or slab(stairs_block.replace("_stairs", "_slab")))
                    elif k == steep - 1:
                        bp.set(*p, stair(stairs_block, f))
                    else:
                        bp.set(*p, full)
            # gable end infill
            for b in range(lo + i + 1, hi - i):
                for a in ((x0, x1) if axis == "x" else (z0, z1)):
                    p = (a, yy, b) if axis == "x" else (b, yy, a)
                    bp.set(*p, fill or full)
            yy += 1
        i += 1
    if under:
        for a in range(a0, a1 + 1):
            for side, f in ((lo, "north" if axis == "x" else "west"), (hi, "south" if axis == "x" else "east")):
                p = (a, y - 1, side) if axis == "x" else (side, y - 1, a)
                bp.set(*p, stair(under, f, "top"))
    # dormers along the long sides
    if dormers and dormer_stairs:
        span = (a1 - a0)
        for n in range(dormers):
            a = a0 + (n + 1) * span // (dormers + 1)
            for side, f, d in ((lo, "south" if axis == "x" else "east", 1), (hi, "north" if axis == "x" else "west", -1)):
                b = side + d * 2
                for da in (-1, 0, 1):
                    for dy in range(0, 3):
                        p = (a + da, y + 1 + dy, b) if axis == "x" else (b, y + 1 + dy, a + da)
                        bp.set(*p, dormer_wall or full)
                p = (a, y + 2, b - d) if axis == "x" else (b - d, y + 2, a)
                bp.set(*p, "glass_pane")
                p = (a, y + 1, b - d) if axis == "x" else (b - d, y + 1, a)
                bp.set(*p, dormer_wall or full)
                for dy, da_list in ((3, (-1, 1)), (4, (0,))):
                    for da in da_list:
                        p = (a + da, y + 1 + dy, b) if axis == "x" else (b, y + 1 + dy, a + da)
                        if dy == 3:
                            ff = ("east" if da < 0 else "west") if axis == "x" else ("south" if da < 0 else "north")
                            bp.set(*p, stair(dormer_stairs, ff))
                        else:
                            bp.set(*p, slab(dormer_stairs.replace("_stairs", "_slab")))
    return yy


def dome(bp, cx, cy, cz, r, shell, *, ribs=None, oculus=True, rib_count=8, inner_clear=True):
    shell = as_pal(shell)
    for x in range(cx - r - 1, cx + r + 2):
        for y in range(cy, cy + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if r - 0.6 < d <= r + 0.4:
                    bp.set(x, y, z, shell.pick(x, y, z))
                elif d <= r - 0.6 and inner_clear:
                    bp.set(x, y, z, "air")
    if ribs:
        for k in range(rib_count):
            a = 2 * math.pi * k / rib_count
            for t in range(0, 91, 3):
                tt = math.radians(t)
                x = cx + round(math.cos(a) * math.cos(tt) * (r + 0.6))
                z = cz + round(math.sin(a) * math.cos(tt) * (r + 0.6))
                y = cy + round(math.sin(tt) * (r + 0.6))
                bp.set(x, y, z, ribs)
    if oculus:
        bp.disk(cx, cy + r, cz, max(1, r // 4), "glass")
        bp.disk(cx, cy + r + 1, cz, max(1, r // 4), "air")


def stair_run(bp, x, y, z, direction, length, width, stairs_block, fill=None, clear=4):
    """Staircase climbing toward `direction`, one step per block. Fills below with `fill`."""
    dx, dz = FACE_VEC[direction]
    px, pz = (-dz, dx)
    for i in range(length):
        for w in range(width):
            sx = x + dx * i + px * w
            sz = z + dz * i + pz * w
            bp.set(sx, y + i, sz, stair(stairs_block, direction))
            if fill:
                for yy in range(y - 4, y + i):
                    bp.set(sx, yy, sz, fill, keep=True)
            for c in range(1, clear + 1):
                bp.set(sx, y + i + c, sz, "air")


# ------------------------------------------------------------------ ground & nature
def terrain_skirt(bp, footprint, y_top, depth=6, spread=3, seed=0, top="grass_block[snowy=false]",
                  soil="dirt", rock="stone", rubble=("cobblestone", "mossy_cobblestone", "andesite")):
    """Natural mound below a footprint (iterable of (x,z)): rock core, soil, grass cap; widens with
    depth so the building looks rooted on any slope. Only fills empty (unset) positions."""
    rng = random.Random(seed)
    fp = set(footprint)
    if not fp:
        return
    for (x, z) in fp:
        for y in range(y_top - depth, y_top):
            bp.set(x, y, z, rock if rng.random() < 0.8 else rng.choice(rubble), keep=True)
    ring = set()
    for (x, z) in fp:
        for dx in range(-spread, spread + 1):
            for dz in range(-spread, spread + 1):
                p = (x + dx, z + dz)
                if p not in fp:
                    ring.add(p)
    for (x, z) in ring:
        dist = min(math.hypot(x - fx, z - fz) for fx, fz in _near(fp, x, z, spread))
        h = int(depth - dist * (depth / (spread + 1)) + rng.uniform(-1, 1))
        if h <= 0:
            continue
        for k in range(h):
            y = y_top - 1 - k
            mat = top if k == 0 else (soil if k < 3 else rock)
            bp.set(x, y, z, mat, keep=True)


def _near(fp, x, z, r):
    out = [(fx, fz) for fx in range(x - r, x + r + 1) for fz in range(z - r, z + r + 1) if (fx, fz) in fp]
    return out or [(x, z)]


def footprint_of(bp, y):
    return {(x, z) for (x, yy, z), b in bp.blocks.items() if yy == y and b[0] != "minecraft:air"}


def landscape(bp, x0, z0, x1, z1, y, density=0.25, seed=0, flowers=("poppy", "dandelion", "azure_bluet", "oxeye_daisy",
                                                                       "cornflower", "allium"), grass=True):
    rng = random.Random(seed)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if bp.get(x, y, z) or bp.get(x, y - 1, z) not in ("minecraft:grass_block", None):
                continue
            r = rng.random()
            if r < density * 0.6 and grass:
                bp.set(x, y, z, rng.choice(["short_grass", "short_grass", "fern"]))
            elif r < density:
                bp.set(x, y, z, rng.choice(flowers))


def bush(bp, x, y, z, leaves="oak_leaves", r=1):
    lv = with_props(leaves, persistent=True, distance=1, waterlogged=False)
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for dy in range(0, r + 1):
                if abs(dx) + abs(dz) + dy <= r + 1:
                    bp.set(x + dx, y + dy, z + dz, lv, keep=True)


def boulder(bp, x, y, z, r=2, blocks=("stone", "andesite", "cobblestone", "mossy_cobblestone"), seed=0):
    rng = random.Random(seed)
    for dx in range(-r, r + 1):
        for dy in range(-1, r):
            for dz in range(-r, r + 1):
                if dx * dx + (dy * 1.4) ** 2 + dz * dz <= r * r + rng.uniform(-1, 1):
                    bp.set(x + dx, y + dy, z + dz, rng.choice(blocks), keep=True)


def _leaves(spec):
    return with_props(spec, persistent=True, distance=1, waterlogged=False)


def oak(bp, x, y, z, h=6, seed=0, log="oak_log", leaves="oak_leaves"):
    rng = random.Random(seed)
    lv = _leaves(leaves)
    for i in range(h):
        bp.set(x, y + i, z, with_props(log, axis="y"))
    top = y + h
    for dy in range(-3, 2):
        rr = 3 if dy in (-2, -1) else 2 if dy in (-3, 0) else 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if dx * dx + dz * dz <= rr * rr + 1 and rng.random() < 0.92:
                    bp.set(x + dx, top + dy, z + dz, lv, keep=True)
    # a couple of branches
    for _ in range(2):
        ddx, ddz = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        bp.set(x + ddx, top - 2, z + ddz, with_props(log, axis="x" if ddx else "z"))


def spruce(bp, x, y, z, h=10, seed=0, log="spruce_log", leaves="spruce_leaves"):
    lv = _leaves(leaves)
    for i in range(h):
        bp.set(x, y + i, z, with_props(log, axis="y"))
    r = 3
    for i in range(2, h + 2):
        yy = y + i
        rr = max(0, int((h + 1 - i) / (h - 1) * r + 0.5)) if i % 2 == 0 else max(0, int((h + 1 - i) / (h - 1) * r))
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) + abs(dz) <= rr + (1 if rr > 1 else 0):
                    bp.set(x + dx, yy, z + dz, lv, keep=True)
    bp.set(x, y + h + 1, z, lv)
    bp.set(x, y + h + 2, z, lv)


def birch(bp, x, y, z, h=7, seed=0):
    oak(bp, x, y, z, h, seed, "birch_log", "birch_leaves")


def big_oak(bp, x, y, z, h=12, seed=0, log="oak_log", leaves="oak_leaves", crown=5):
    """Wide old tree with a 2x2 trunk, roots and several leaf clusters."""
    rng = random.Random(seed)
    L = with_props(log, axis="y")
    lv = _leaves(leaves)
    for i in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(x + dx, y + i, z + dz, L)
    for dx, dz in ((-1, 0), (2, 1), (0, -1), (1, 2)):
        bp.set(x + dx, y, z + dz, L)
    top = y + h
    clusters = [(x, top + 2, z)]
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi)
        bx = x + round(math.cos(a) * crown * 0.8)
        bz = z + round(math.sin(a) * crown * 0.8)
        by = top - rng.randint(0, 3)
        bp.line((x, top - 3, z), (bx, by, bz), with_props(log, axis="y"))
        clusters.append((bx, by + 1, bz))
    for (cx, cy, cz) in clusters:
        bp.blob(cx, cy, cz, crown - 1, 3, crown - 1, lv, noise=0.35)


def dark_tree(bp, x, y, z, h=9, seed=0):
    big_oak(bp, x, y, z, h, seed, "dark_oak_log", "dark_oak_leaves", crown=5)


# ------------------------------------------------------------------ details
def hanging_lantern(bp, x, y, z, chain=2, soul=False):
    bp.chain(x, y - chain + 1, z, y)
    bp.lantern(x, y - chain, z, hanging=True, soul=soul)


def chandelier(bp, x, y, z, arms=True, soul=False, candles=True):
    """Hangs from the ceiling at y (the block below the ceiling)."""
    bp.chain(x, y - 1, z, y)
    bp.lantern(x, y - 2, z, hanging=True, soul=soul)
    if arms:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(x + dx, y - 2, z + dz, "dark_oak_fence")
            if candles:
                bp.set(x + 2 * dx, y - 2, z + 2 * dz, "dark_oak_slab[type=top,waterlogged=false]")
                bp.set(x + 2 * dx, y - 1, z + 2 * dz, "candle[candles=3,lit=true,waterlogged=false]")


def vines_on(bp, region, chance=0.12, seed=0, max_len=5):
    """Drape vines down exposed vertical faces inside region ((x0,y0,z0),(x1,y1,z1))."""
    rng = random.Random(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    for (x, y, z), b in list(bp.blocks.items()):
        if not (x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1) or b[0] == "minecraft:air":
            continue
        if rng.random() > chance:
            continue
        for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
            if bp.get(x + dx, y, z + dz) is None:
                attach = OPPOSITE[d]
                for k in range(rng.randint(2, max_len)):
                    if bp.get(x + dx, y - k, z + dz) is not None or not bp.get(x, y - k, z):
                        break
                    bp.set(x + dx, y - k, z + dz, f"vine[{attach}=true]")
                break


def moss_on(bp, region, chance=0.15, seed=0, mapping=None):
    rng = random.Random(seed)
    mapping = mapping or {
        "minecraft:stone_bricks": "mossy_stone_bricks", "minecraft:cobblestone": "mossy_cobblestone",
        "minecraft:stone_brick_stairs": "mossy_stone_brick_stairs", "minecraft:stone_brick_slab": "mossy_stone_brick_slab",
        "minecraft:stone_brick_wall": "mossy_stone_brick_wall", "wayfarers:guild_bricks": "wayfarers:mossy_guild_bricks",
        "wayfarers:guild_brick_stairs": "wayfarers:mossy_guild_brick_stairs",
        "wayfarers:guild_brick_slab": "wayfarers:mossy_guild_brick_slab",
        "wayfarers:guild_brick_wall": "wayfarers:mossy_guild_brick_wall",
    }
    (x0, y0, z0), (x1, y1, z1) = region
    for (x, y, z), (name, props, data) in list(bp.blocks.items()):
        if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1 and name in mapping and rng.random() < chance:
            new = mapping[name] if ":" in mapping[name] else "minecraft:" + mapping[name]
            bp.blocks[(x, y, z)] = (new, props, data)


def rubble(bp, x0, z0, x1, z1, y, count, blocks=("cobblestone", "mossy_cobblestone", "stone_bricks", "andesite"),
           seed=0):
    rng = random.Random(seed)
    for _ in range(count):
        x, z = rng.randint(x0, x1), rng.randint(z0, z1)
        if not bp.get(x, y, z):
            bp.set(x, y, z, rng.choice(blocks))
            if rng.random() < 0.3 and not bp.get(x, y + 1, z):
                bp.set(x, y + 1, z, rng.choice(blocks).replace("stone_bricks", "stone_brick_slab[type=bottom]"))


def banner_wall(bp, x, y, z, facing, color="blue"):
    bp.set(x, y, z, f"{color}_wall_banner[facing={facing}]")


# ------------------------------------------------------------------ interiors
def furnish(bp, x0, y, z0, x1, z1, kind, *, wood="spruce", loot=None, seed=0, ceiling=None):
    """Fill the floor area (x0..x1, z0..z1) at height y (first air layer) with a themed interior."""
    rng = random.Random(seed)
    w, d = x1 - x0 + 1, z1 - z0 + 1
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    plank = f"{wood}_planks"
    st = f"{wood}_stairs"
    if kind == "library":
        for x in range(x0, x1 + 1):
            for yy in range(y, y + 3):
                bp.set(x, yy, z0, "bookshelf" if rng.random() > 0.1 else "chiseled_bookshelf[facing=south]")
        for z in range(z0 + 2, z1, 3):
            for x in range(x0 + 1, x1 - 1):
                if (x - x0) % 4 != 0:
                    bp.set(x, y, z, "bookshelf")
                    bp.set(x, y + 1, z, "bookshelf")
        bp.set(cx, y, z1, "lectern[facing=north,has_book=false,powered=false]")
        if loot:
            bp.chest(x1, y, z1, "west", loot)
    elif kind == "bedroom":
        for i, x in enumerate(range(x0, x1, 3)):
            bp.bed(x, y, z0, "south", rng.choice(["red", "blue", "white", "green", "light_blue"]))
            if x + 1 <= x1:
                bp.set(x + 1, y, z0, "barrel[facing=up,open=false]")
                bp.set(x + 1, y + 1, z0, "candle[candles=1,lit=true,waterlogged=false]")
        bp.set(cx, y, z1, "red_carpet")
        if loot:
            bp.chest(x1, y, z1, "west", loot)
    elif kind == "kitchen":
        for x in range(x0, x1 + 1):
            bp.set(x, y, z0, rng.choice(["smoker[facing=south,lit=false]", "barrel[facing=up,open=false]",
                                         "crafting_table", "furnace[facing=south,lit=false]"]))
        bp.table(cx, y, cz, f"{wood}_pressure_plate", f"{wood}_fence")
        for dx in (-1, 1):
            bp.stairs(cx + dx, y, cz, st, "east" if dx < 0 else "west")
        bp.set(x1, y, z1, "cauldron")
        bp.set(x0, y, z1, "composter[level=3]")
        if loot:
            bp.barrel(x0 + 1, y, z1, "up", loot)
    elif kind == "armory":
        for x in range(x0, x1 + 1, 2):
            bp.entity(x, y, z0, {"id": "minecraft:armor_stand"})
        bp.set(x0, y, z1, "anvil[facing=east]")
        bp.set(x0 + 1, y, z1, "grindstone[face=floor,facing=east]")
        bp.set(x0 + 2, y, z1, "smithing_table")
        if loot:
            bp.chest(x1, y, z1, "west", loot)
    elif kind == "treasury":
        for x in range(x0, x1 + 1, 2):
            bp.chest(x, y, z0, "south", loot if (x - x0) % 4 == 0 else None)
        bp.fill(x0, y, z1, x0 + 1, y, z1, "gold_block")
        bp.set(x1, y, z1, "emerald_block")
        bp.set(cx, y, cz, "decorated_pot[facing=north,waterlogged=false,cracked=false]")
    elif kind == "chapel":
        for z in range(z0 + 2, z1 + 1, 2):
            for x in list(range(x0, cx - 1)) + list(range(cx + 2, x1 + 1)):
                bp.stairs(x, y, z, st, "south")
        bp.fill(cx - 1, y, z0, cx + 1, y, z0, "polished_andesite")
        bp.set(cx, y + 1, z0, "lectern[facing=south,has_book=false,powered=false]")
        for dx in (-1, 1):
            bp.set(cx + dx, y + 1, z0, "candle[candles=4,lit=true,waterlogged=false]")
        if loot:
            bp.chest(x1, y, z0, "west", loot)
    elif kind == "study":
        bp.table(cx, y, cz, f"{wood}_pressure_plate", f"{wood}_fence")
        bp.stairs(cx, y, cz + 1, st, "north")
        bp.set(cx + 1, y, cz, "cartography_table")
        for x in range(x0, x1 + 1):
            bp.set(x, y, z0, "bookshelf")
        bp.set(x0, y, z1, "lectern[facing=east,has_book=false,powered=false]")
        if loot:
            bp.chest(x1, y, z1, "west", loot)
    elif kind == "storage":
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                if rng.random() < 0.8:
                    bp.barrel(x, y, z, "up")
                    if rng.random() < 0.5:
                        bp.barrel(x, y + 1, z, "north")
        if loot:
            bp.chest(cx, y, z0 + 1, "south", loot)
    if ceiling is not None:
        chandelier(bp, cx, ceiling - 1, cz)
