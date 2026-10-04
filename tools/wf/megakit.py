"""Shared helpers for the giant steampunk structures (Geothermal Foundry, Tesla Observatory, Crystal Cathedral).

Small, composable pieces: smooth 2D value noise for natural ground and rock, railings and catwalks, lattice
towers, chimneys that smoke, chains, spheres and gothic (pointed) arch profiles.
"""
import math

from .arch import stair

W = "wayfarers:"
BRASS, COPPER, VERD, IRON = W + "brass_plating", W + "copper_plating", W + "verdigris_plating", W + "dark_iron_plating"
TREAD, GEAR, PIPES, GAUGE = W + "diamond_plate", W + "gear_panel", W + "copper_pipes", W + "pressure_gauge"
EDISON, AETHER, MAHOGANY, LEATHER, SMOKE = (W + "edison_lamp", W + "aether_conduit", W + "mahogany_panelling",
                                           W + "leather_padding", W + "smokestack_bricks")
BRASS_STAIRS, BRASS_SLAB = W + "brass_plating_stairs", W + "brass_plating_slab"
IRON_STAIRS, IRON_SLAB, IRON_WALL = (W + "dark_iron_plating_stairs", W + "dark_iron_plating_slab",
                                     W + "dark_iron_plating_wall")
TREAD_SLAB, TREAD_STAIRS = W + "diamond_plate_slab", W + "diamond_plate_stairs"
SMOKE_STAIRS, SMOKE_SLAB, SMOKE_WALL = (W + "smokestack_brick_stairs", W + "smokestack_brick_slab",
                                        W + "smokestack_brick_wall")
COPPER_STAIRS, VERD_STAIRS = W + "copper_plating_stairs", W + "verdigris_plating_stairs"
MAHOGANY_STAIRS, MAHOGANY_SLAB = W + "mahogany_panelling_stairs", W + "mahogany_panelling_slab"
CHANDELIER, HANG_LAMP, TABLE = W + "brass_chandelier", W + "hanging_edison_lamp", W + "mahogany_table"
BARS = "iron_bars"
AIR = "minecraft:air"

DIR_VEC = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ noise
def hash01(x, z, seed=0):
    n = (x * 73856093) ^ (z * 19349663) ^ (seed * 83492791)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def hash3(x, y, z, seed=0):
    return hash01(x * 31 + y * 1013, z * 17 - y * 7, seed)


def vnoise(x, z, scale=6.0, seed=0):
    """Smooth 2D value noise in 0..1."""
    fx, fz = x / scale, z / scale
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a = hash01(ix, iz, seed)
    b = hash01(ix + 1, iz, seed)
    c = hash01(ix, iz + 1, seed)
    d = hash01(ix + 1, iz + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def fbm(x, z, scale=8.0, seed=0):
    return 0.6 * vnoise(x, z, scale, seed) + 0.3 * vnoise(x, z, scale / 2.3, seed + 7) + \
        0.1 * vnoise(x, z, scale / 5.1, seed + 13)


# ------------------------------------------------------------------ directions
def out_facing(dx, dz):
    """Horizontal direction pointing along (dx, dz) (dominant axis)."""
    if abs(dz) >= abs(dx):
        return "north" if dz < 0 else "south"
    return "west" if dx < 0 else "east"


def is_air(bp, x, y, z):
    b = bp.get(x, y, z)
    return b is None or b == AIR


# ------------------------------------------------------------------ small parts
def railing(bp, x, y, z, facing):
    bp.set(x, y, z, f"{W}brass_railing[facing={facing}]")


def smoke(bp, x, y, z, signal=True):
    """A lit campfire (smoke column) on a hay bale at (x, y, z); the hay is at y - 1."""
    bp.set(x, y - 1, z, "hay_block[axis=y]" if signal else IRON)
    bp.set(x, y, z, f"campfire[facing=north,lit=true,signal_fire={'true' if signal else 'false'},waterlogged=false]")


def chain(bp, x, y0, z, y1):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        bp.set(x, y, z, "iron_chain[axis=y,waterlogged=false]")


def hang_lamp(bp, x, y, z, length=1, lamp=HANG_LAMP):
    """A lamp hanging under a ceiling at y + length + 1 (chain of `length`, lamp at y)."""
    chain(bp, x, y + 1, z, y + length)
    bp.set(x, y, z, lamp)


def lantern_post(bp, x, y, z, h=3, top=EDISON, post=IRON_WALL, base=IRON):
    bp.set(x, y, z, base)
    for k in range(1, h):
        bp.set(x, y + k, z, post)
    bp.set(x, y + h, z, top)


def sphere(bp, cx, cy, cz, r, spec, hollow=False, shell=0.8, fn=None):
    ri = int(math.ceil(r)) + 1
    for x in range(cx - ri, cx + ri + 1):
        for y in range(cy - ri, cy + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if d <= r + 0.35 and (not hollow or d > r - shell):
                    bp.set(x, y, z, fn(x, y, z) if fn else spec)


def disk(bp, cx, y, cz, r, spec, inner=-1.0):
    ri = int(math.ceil(r)) + 1
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            d = math.hypot(x - cx, z - cz)
            if inner < d <= r + 0.35:
                bp.set(x, y, z, spec(x, z) if callable(spec) else spec)


def ring_railing(bp, cx, y, cz, r, gaps=()):
    """Brass railing around a circular platform of radius r (on its outer edge cells)."""
    ri = int(math.ceil(r)) + 1
    for x in range(cx - ri, cx + ri + 1):
        for z in range(cz - ri, cz + ri + 1):
            d = math.hypot(x - cx, z - cz)
            if r - 0.65 < d <= r + 0.35:
                if any(g(x - cx, z - cz) for g in gaps):
                    continue
                railing(bp, x, y, z, out_facing(x - cx, z - cz))


# ------------------------------------------------------------------ walkways
def catwalk(bp, a0, a1, b, y, axis="x", half=1, rails=True, deck=TREAD, edge=IRON, brackets=True):
    """Straight catwalk along `axis` from a0 to a1 (inclusive), centred on b, width 2*half+1, with railings on
    both edges and brackets under the deck every 4 blocks."""
    lo, hi = min(a0, a1), max(a0, a1)
    for a in range(lo, hi + 1):
        for k in range(-half, half + 1):
            x, z = (a, b + k) if axis == "x" else (b + k, a)
            edge_cell = abs(k) == half and half > 0
            bp.set(x, y, z, edge if edge_cell else deck)
            if rails and edge_cell:
                f = (("north" if k < 0 else "south") if axis == "x" else ("west" if k < 0 else "east"))
                if is_air(bp, x, y + 1, z):
                    railing(bp, x, y + 1, z, f)
        if brackets and (a - lo) % 4 == 2:
            for k in (-half, half):
                x, z = (a, b + k) if axis == "x" else (b + k, a)
                f = (("south" if k < 0 else "north") if axis == "x" else ("east" if k < 0 else "west"))
                if is_air(bp, x, y - 1, z):
                    bp.set(x, y - 1, z, stair(IRON_STAIRS, f, "top"))


def clear_rails(bp, x, y, z):
    b = bp.get(x, y, z)
    if b and "railing" in b:
        bp.set(x, y, z, "air")


# ------------------------------------------------------------------ towers & chimneys
def lattice_tower(bp, cx, cz, y0, y1, r=2, band_every=6, corner=IRON, band=BRASS, ladder_face="south"):
    """Open steel tower: corner columns, X-bracing with iron bars, brass bands, a ladder inside one face."""
    for y in range(y0, y1 + 1):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                ex, ez = abs(x - cx) == r, abs(z - cz) == r
                if ex and ez:
                    bp.set(x, y, z, corner if (y - y0) % band_every else band)
                elif ex or ez:
                    if (y - y0) % band_every == 0:
                        bp.set(x, y, z, corner)
                    else:
                        u = (x - cx) if ez else (z - cz)
                        k = (y - y0) % band_every
                        if abs(u) == round(abs(k - band_every / 2) * r / (band_every / 2)):
                            bp.set(x, y, z, BARS)
    if ladder_face:
        dx, dz = DIR_VEC[ladder_face]
        lx, lz = cx + dx * (r - 1), cz + dz * (r - 1)
        wx, wz = cx + dx * r, cz + dz * r
        for y in range(y0 + 1, y1 + 1):
            bp.set(wx, y, wz, corner)
            bp.set(lx, y, lz, f"ladder[facing={OPP[ladder_face]},waterlogged=false]")


def chimney(bp, cx, cz, y0, h, r=3, body=SMOKE, band=BRASS, cap=IRON, smoke_top=True, bands=(10,)):
    """Round brick chimney with brass bands, a flared crown and a smoking signal fire inside the top."""
    top = y0 + h
    for y in range(y0, top + 1):
        rr = r + (1 if y >= top - 1 else 0) + (1 if y < y0 + 3 else 0)
        ring_spec = body
        if any((y - y0) % b == 0 for b in bands) and y > y0 + 3:
            ring_spec = band
        for x in range(cx - rr - 1, cx + rr + 2):
            for z in range(cz - rr - 1, cz + rr + 2):
                d = math.hypot(x - cx, z - cz)
                if rr - 0.9 < d <= rr + 0.35:
                    if ring_spec == band and d > rr - 0.2:
                        bp.set(x, y, z, band)
                    bp.set(x, y, z, cap if y == top else ring_spec)
                elif d <= rr - 0.9 and y > y0:
                    bp.set(x, y, z, "air")
    # soot: blackened crown courses
    for x in range(cx - r - 2, cx + r + 3):
        for z in range(cz - r - 2, cz + r + 3):
            d = math.hypot(x - cx, z - cz)
            if r + 0.1 < d <= r + 1.35:
                bp.set(x, top - 2, z, stair(SMOKE_STAIRS, out_facing(cx - x, cz - z), "top"))
    if smoke_top:
        bp.set(cx, top - 3, cz, IRON)
        smoke(bp, cx, top - 1, cz)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if r >= 3:
                bp.set(cx + dx * 2, top - 2, cz + dz * 2, IRON)
                smoke(bp, cx + dx * 2, top - 1, cz + dz * 2, signal=True)
    return top


def pointed_arch(half_w, h):
    """Gothic pointed arch profile: for |u| <= half_w, the height of the intrados (lowest free y above the springing
    line is 0..h). Two circle arcs of radius ~1.4*half_w meeting at the apex h."""
    R = half_w * 1.6
    def height(u):
        u = abs(u)
        c = R - half_w   # centre of each arc, on the opposite side
        v = R * R - (u + c) ** 2
        if v <= 0:
            return 0
        return math.sqrt(v) * h / math.sqrt(R * R - c * c)
    return height
