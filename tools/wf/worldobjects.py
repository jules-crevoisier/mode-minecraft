"""Natural objects of the world overhaul, saved as structure templates (data/wayfarers/structure/worldobjects/*.nbt,
mod data, always loaded) and scattered by template features (wf/worldfeatures.py): curved thorn spikes, stone arches,
aether crystal shards, banded hoodoos, hot-spring terraces with coloured rims and giant flat-capped mushrooms.

Every object is built around x = z = 0 (the template feature centres it on the placement point). y = 0 is the
buried foot: the features sink them 2 blocks so they root in the ground. Several seeded variants of each kind.
Only solid blocks are saved (no air), so objects never carve the terrain around them, except the hot springs
which hold water.
"""
import math
import os
import random

from .blueprint import Blueprint

VARIANTS = {"thorn": 8, "arch": 3, "crystal": 4, "hoodoo": 5, "hot_spring": 3, "flat_mushroom": 6,
            "ash_column": 3}


def _put(bp, x, y, z, spec):
    bp.set(int(round(x)), int(round(y)), int(round(z)), spec)


def _horn_path(height, lean, bend, az, ds=0.2):
    """Points (x, y, z, s) along a horn rising `height` blocks: it leaves the ground leaning `lean` radians from
    the vertical and curls over (the angle grows as s^1.7, so the bend is strongest near the tip) to lean + bend."""
    pts, x, y = [], 0.0, 0.0
    n = 400
    for i in range(n + 1):                       # a unit-length curve, scaled to the height below
        s = i / n
        a = lean + bend * s ** 1.7
        pts.append((x, y, s))
        x += math.sin(a) / n
        y += math.cos(a) / n
    k = height / max(p[1] for p in pts)
    step = max(1, int(n * ds / (k * 1.0)))      # about one point every `ds` blocks
    return [(math.cos(az) * px * k, py * k, math.sin(az) * px * k, s) for px, py, s in pts[::step]]


def _horn_blocks(bp, rng, path, r0, x0=0.0, z0=0.0, y0=2.0):
    """A horn along `path`: radius r0 at the foot tapering to a single block at the tip (the centre line is kept
    face-connected, so the thin tip never breaks into diagonal steps)."""
    prev = None
    for px, py, pz, s in path:
        c = (int(round(x0 + px)), int(round(y0 + py)), int(round(z0 + pz)))
        if prev and sum(a != b for a, b in zip(c, prev)) > 1:
            for k in range(3):                  # step one axis at a time
                if c[k] != prev[k]:
                    prev = tuple(c[j] if j == k else prev[j] for j in range(3))
                    if prev != c:
                        bp.set(*prev, "blackstone")
        prev = c
        r = r0 * (1.0 - s) ** 1.15 + 0.32
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r:
                        v = rng.random()
                        blk = ("crying_obsidian" if v < 0.02 else "basalt[axis=y]" if v < 0.22
                               else "polished_blackstone" if v < 0.4 else "blackstone")
                        _put(bp, x0 + px + dx, y0 + py + dy, z0 + pz + dz, blk)


def thorn(bp, rng):
    """A slim curved horn of blackstone and basalt, 15-30 blocks tall: 3-4 blocks thick at the foot, it rises
    almost straight, then curls over like a ram's horn and ends in a 1-block point. Some grow a second, smaller
    horn from the same foot."""
    height = rng.uniform(17, 31)
    az = rng.uniform(0, 2 * math.pi)
    r0 = rng.uniform(1.25, 1.75) + height / 40.0
    path = _horn_path(height, math.radians(rng.uniform(4, 14)), math.radians(rng.uniform(55, 95)), az)
    reach = max(math.hypot(p[0], p[2]) for p in path)
    # shift the foot back so the whole horn stays centred (the template is centred on its placement point)
    x0, z0 = -math.cos(az) * reach / 2.0, -math.sin(az) * reach / 2.0
    _horn_blocks(bp, rng, path, r0, x0, z0)
    if rng.random() < 0.45:
        az2 = az + rng.uniform(2.0, 4.3)
        small = _horn_path(height * rng.uniform(0.35, 0.55), math.radians(rng.uniform(10, 25)),
                           math.radians(rng.uniform(40, 80)), az2)
        _horn_blocks(bp, rng, small, r0 * 0.6, x0 + math.cos(az2) * r0 * 0.6, z0 + math.sin(az2) * r0 * 0.6)
    for y in range(0, 3):                       # buried foot
        ri = int(r0) + 2
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dz * dz <= (r0 + 0.8) ** 2:
                    bp.set(int(round(x0)) + dx, y, int(round(z0)) + dz, "blackstone")


STRATA = ["tuff", "andesite", "deepslate[axis=y]", "stone", "polished_andesite", "tuff", "cobbled_deepslate",
          "smooth_basalt", "andesite", "calcite"]


def arch(bp, rng):
    """A natural stone arch of banded grey rock (tuff, andesite, deepslate, basalt), span 16-26, 12-20 high."""
    span = rng.randint(8, 13)
    height = rng.randint(12, 20)
    thick = rng.uniform(2.2, 3.4)
    phase = rng.randint(0, len(STRATA) - 1)
    for i in range(0, 181):
        a = math.radians(i)
        cx = -math.cos(a) * span
        cy = math.sin(a) * height + 2
        r = thick * (1.0 + 0.35 * (1 - math.sin(a)))       # thicker legs
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + (dz * 1.3) ** 2 <= r * r:
                        y = cy + dy
                        band = STRATA[(int(y // 3) + phase) % len(STRATA)]
                        _put(bp, cx + dx, y, dz, band)
    for x in (-span, span):                             # legs down to the buried foot
        for y in range(0, 4):
            for dx in range(-3, 4):
                for dz in range(-2, 3):
                    if dx * dx + dz * dz <= 9:
                        bp.set(x + dx, y, dz, STRATA[(y // 3 + phase) % len(STRATA)])
    for (x, y, z), b in list(bp.blocks.items()):        # white ash on the top surfaces
        if (x, y + 1, z) not in bp.blocks and y > height * 0.7 and rng.random() < 0.6:
            bp.set(x, y, z, "calcite")


def crystal(bp, rng):
    """A cluster of 2-4 leaning aether crystal shards, 7-16 long: amethyst cores in a purple glass skin, magenta
    glass tips, amethyst clusters at the foot."""
    n = rng.randint(2, 4)
    for k in range(n):
        length = rng.uniform(9, 16) if k == 0 else rng.uniform(5, 11)
        tilt = math.radians(rng.uniform(18, 45) if k else rng.uniform(8, 25))
        az = rng.uniform(0, 2 * math.pi) if k else rng.uniform(0, 2 * math.pi)
        dx, dy, dz = math.sin(tilt) * math.cos(az), math.cos(tilt), math.sin(tilt) * math.sin(az)
        r0 = rng.uniform(1.1, 1.7) if k == 0 else rng.uniform(0.8, 1.2)
        steps = int(length * 4)
        for i in range(steps):
            t = i / steps
            px, py, pz = dx * length * t, 1 + dy * length * t, dz * length * t
            r = r0 * (1.0 if t < 0.65 else max(0.0, (1.0 - t) / 0.35)) + 0.25
            ri = int(math.ceil(r))
            for ox in range(-ri, ri + 1):
                for oz in range(-ri, ri + 1):
                    d2 = ox * ox + oz * oz
                    if d2 <= r * r:
                        tip = t > 0.8
                        skin = d2 > (r - 0.9) ** 2
                        blk = ("magenta_stained_glass" if tip else "purple_stained_glass") if skin and r > 1.2 else \
                            ("amethyst_block" if not tip else "magenta_stained_glass")
                        _put(bp, px + ox, py, pz + oz, blk)
    for _ in range(10):
        x, z = rng.randint(-3, 3), rng.randint(-3, 3)
        if (x, 1, z) not in bp.blocks:
            bp.set(x, 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
    for x in range(-2, 3):
        for z in range(-2, 3):
            bp.set(x, 0, z, "budding_amethyst" if (x + z) % 3 == 0 else "amethyst_block")


HOODOO_BANDS = ["white_terracotta", "yellow_terracotta", "orange_terracotta", "red_terracotta", "terracotta",
                "orange_terracotta", "light_gray_terracotta", "yellow_terracotta", "red_terracotta", "brown_terracotta"]


def hoodoo(bp, rng):
    """A banded terracotta hoodoo, 6-25 tall: a cone with a pointed top, sometimes a sandstone cap (mini mesa)."""
    h = rng.randint(6, 25)
    r0 = 1.5 + h / 7.0 + rng.uniform(0, 1.2)
    capped = rng.random() < 0.35
    phase = rng.randint(0, 9)
    wob = rng.uniform(0, 6.28)
    for y in range(0, h + 1):
        t = y / h
        r = r0 * (1 - t) ** 0.75 + (0.6 if t < 0.95 else 0.0)
        r *= 1.0 + 0.12 * math.sin(y * 0.9 + wob)              # eroded, wavy flanks
        if capped and t > 0.8:
            r = max(r, r0 * 0.55)
        ri = int(math.ceil(r))
        band = HOODOO_BANDS[(y // 2 + phase) % len(HOODOO_BANDS)]
        if capped and y >= h - 1:
            band = "smooth_red_sandstone"
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dz * dz <= r * r:
                    bp.set(dx, y, dz, band)


RIMS = ["white_terracotta", "yellow_terracotta", "orange_terracotta", "calcite"]


def hot_spring(bp, rng):
    """Hot-spring terraces: 3-4 stepped pools of turquoise water, rims of white, yellow and orange travertine."""
    tiers = rng.randint(3, 5)
    r = rng.uniform(3.5, 5.5)
    cx = cz = 0.0
    ang = rng.uniform(0, 6.28)
    top = tiers + 2
    for k in range(tiers):
        y = top - k
        rr = r * (1.0 - 0.12 * k)
        ri = int(math.ceil(rr)) + 1
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz * 1.15)
                x, z = int(round(cx + dx)), int(round(cz + dz))
                if d <= rr + 1:
                    for yy in range(0, y):                   # a solid travertine body down to the foot
                        bp.set(x, yy, z, "calcite" if yy < y - 2 else RIMS[(k + yy) % 3])
                    if d <= rr - 0.5:
                        bp.set(x, y - 1, z, "cyan_terracotta" if d < rr * 0.5 else "light_blue_terracotta")
                        bp.set(x, y, z, "water")
                    else:
                        bp.set(x, y, z, RIMS[k % len(RIMS)])
        cx += math.cos(ang) * r * 1.1
        cz += math.sin(ang) * r * 1.1
        ang += rng.uniform(-0.8, 0.8)
    bp.set(0, top - 1, 0, "magma_block")


def flat_mushroom(bp, rng, size=None):
    """A giant red mushroom: a broad, gently domed cap (radius 5-9) on a thick leaning stem 10-22 tall, the rim
    turned down, curtains of weeping vines (2-8 long) hanging from under it, a few shroomlights in the gills."""
    big = rng.random() < 0.6 if size is None else size
    h = rng.randint(14, 22) if big else rng.randint(9, 14)
    rc = rng.uniform(7.0, 9.0) if big else rng.uniform(5.0, 6.8)
    lean = rng.uniform(0.5, 3.0)
    az = rng.uniform(0, 6.28)
    sr = 1.5 if big else 1.0                          # stem radius: 3 or 2 blocks thick
    for y in range(0, h):
        t = y / h
        x, z = math.cos(az) * lean * t * t, math.sin(az) * lean * t * t
        rr = sr + (0.8 if y < 2 else 0.0)              # a flared foot
        ri = int(math.ceil(rr))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dz * dz <= rr * rr:
                    _put(bp, x + dx, y, z + dz, "mushroom_stem")
    tx, tz = math.cos(az) * lean, math.sin(az) * lean
    R = int(math.ceil(rc)) + 1
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            x, z = int(round(tx + dx)), int(round(tz + dz))
            if d <= rc:
                dome = int(1.6 * (1.0 - (d / rc) ** 2) + 0.5)        # 0-2 blocks higher in the middle
                for k in range(dome + 1):
                    bp.set(x, h + k, z, "red_mushroom_block")
                if d > 1.8 and rng.random() < 0.05:
                    bp.set(x, h - 1, z, "shroomlight")
            elif d <= rc + 1.0:
                bp.set(x, h, z, "red_mushroom_block")
                bp.set(x, h - 1, z, "red_mushroom_block")                 # down-turned rim
                if rng.random() < 0.7:
                    n = rng.randint(2, 8)
                    for k in range(n):
                        bp.set(x, h - 2 - k, z, "weeping_vines" if k == n - 1 else "weeping_vines_plant")
    for _ in range(int(rc * 2)):                      # a few vines under the cap too
        a, d = rng.uniform(0, 6.28), rng.uniform(sr + 1.5, rc - 0.5)
        x, z = int(round(tx + math.cos(a) * d)), int(round(tz + math.sin(a) * d))
        if (x, h - 1, z) not in bp.blocks:
            n = rng.randint(1, 5)
            for k in range(n):
                bp.set(x, h - 1 - k, z, "weeping_vines" if k == n - 1 else "weeping_vines_plant")


def ash_column(bp, rng):
    """A ruined column of banded grey rock with an ash-white top, 8-18 tall (ashen wastes)."""
    h = rng.randint(8, 18)
    r = rng.uniform(1.8, 3.0)
    phase = rng.randint(0, 9)
    for y in range(0, h):
        rr = r * (1.0 - 0.25 * (y / h)) + 0.3 * math.sin(y * 1.3)
        ri = int(math.ceil(rr))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if dx * dx + dz * dz <= rr * rr:
                    bp.set(dx, y, dz, "calcite" if y == h - 1 else STRATA[(y // 2 + phase) % len(STRATA)])


BUILDERS = {"thorn": thorn, "arch": arch, "crystal": crystal, "hoodoo": hoodoo, "hot_spring": hot_spring,
            "flat_mushroom": flat_mushroom, "ash_column": ash_column}


def blueprints():
    for kind, n in VARIANTS.items():
        for i in range(n):
            bp = Blueprint(f"worldobjects/{kind}_{i}")
            BUILDERS[kind](bp, random.Random(f"{kind}:{i}"))
            yield kind, i, bp


def template_ids(kind):
    return [f"wayfarers:worldobjects/{kind}_{i}" for i in range(VARIANTS[kind])]


def write(root):
    out = os.path.join(root, "src", "main", "resources", "data", "wayfarers", "structure", "worldobjects")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    names = []
    for kind, i, bp in blueprints():
        bp.save(os.path.join(out, f"{kind}_{i}.nbt"))
        (lo, hi) = bp.bounds()
        if max(hi[0] - lo[0], hi[2] - lo[2]) > 30:
            raise ValueError(f"{kind}_{i} is wider than 30 blocks: it would reach past the neighbouring chunks")
        names.append(f"{kind}_{i}")
    return names
