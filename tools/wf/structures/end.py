"""End structures: monumental builds floating over the void around the outer islands.

Every build sits on its own floating rock (absolute heights, no terrain adaptation): a flat top
with a rounded lip and a deep, spiky underside hung with end rods, chains of starlight and
amethyst. Shared kit at the top of the file, one builder per structure below.

Materials (End theme): void bricks (dark walls) + purpur (trim, pilasters, ribs) + end stone
bricks (plinths, paving, rails) + one accent per build (oxidized copper, magenta wool, crying
obsidian...). Starlight blocks and end rods carry the light.
"""
import math
import random

from .. import interior as INT
from ..arch import Palette, slab, stair
from ..blueprint import OPPOSITE, Blueprint
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD

OUTER_END = ["end_highlands", "end_midlands", "small_end_islands", "end_barrens"]

# ------------------------------------------------------------------ materials
VB = "brasshaven:void_bricks"
VB_ST = "brasshaven:void_brick_stairs"
VB_SL = "brasshaven:void_brick_slab"
VB_WA = "brasshaven:void_brick_wall"
STAR = "brasshaven:starlight_block"
ESB = "end_stone_bricks"
ESB_ST = "end_stone_brick_stairs"
ESB_SL = "end_stone_brick_slab"
ESB_WA = "end_stone_brick_wall"
PUR = "purpur_block"
PUR_P = "purpur_pillar[axis=y]"
PUR_ST = "purpur_stairs"
PUR_SL = "purpur_slab"
FROG = "pearlescent_froglight[axis=y]"
ROD_UP = "end_rod[facing=up]"
ROD_DOWN = "end_rod[facing=down]"


def void_pal(seed=0):
    return Palette({VB: 12, "obsidian": 1}, seed=seed, scale=2.5)


def purpur_pal(seed=0):
    return Palette({PUR: 5, PUR_P: 2}, seed=seed, scale=2.0)


def paving_pal(seed=0):
    return Palette({ESB: 8, "end_stone": 1}, seed=seed, scale=2.0)


# ------------------------------------------------------------------ geometry helpers
def face_in(x, z, cx, cz):
    """Cardinal facing pointing from (x, z) toward the centre."""
    dx, dz = x - cx, z - cz
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def face_vec(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def ring_pts(cx, cz, r, inner=None):
    """Columns of a 1-thick circle of radius r (same rule as Blueprint.disk hollow)."""
    inner = r - 1 if inner is None else inner
    out = []
    R = int(math.ceil(r)) + 1
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if inner + 0.4 < d <= r + 0.4:
                out.append((x, z))
    return out


def disk_pts(cx, cz, r):
    R = int(math.ceil(r)) + 1
    return [(x, z) for x in range(cx - R, cx + R + 1) for z in range(cz - R, cz + R + 1)
            if math.hypot(x - cx, z - cz) <= r + 0.4]


def adiff(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def _noise(seed, scale):
    return Palette({"x": 1}, seed=seed, scale=scale)._noise


# ------------------------------------------------------------------ floating rocks
def rock_lobe(cx, top, cz, rx, rz, depth, seed, spikes=6, lip=True):
    """Column heightfield {(x, z): (bottom, top)} of one floating-rock lobe: flat top with a
    rounded lip, an inverted-mountain underside and a few long stalactite spikes."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(4)]
    n2 = _noise(seed + 7, 3.5)
    spk = []
    for _ in range(spikes):
        a = rng.uniform(0, 2 * math.pi)
        e = rng.uniform(0.0, 0.7) ** 0.8
        spk.append((cx + math.cos(a) * e * rx, cz + math.sin(a) * e * rz,
                    rng.uniform(2.2, 2.0 + min(rx, rz) * 0.28), rng.uniform(0.35, 0.85) * depth))
    cols = {}
    R = int(max(rx, rz) * 1.25) + 2
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            dx, dz = (x - cx) / rx, (z - cz) / rz
            th = math.atan2(dz, dx)
            rim = 1 + 0.10 * math.sin(3 * th + ph[0]) + 0.06 * math.sin(5 * th + ph[1]) \
                + 0.035 * math.sin(11 * th + ph[2])
            e = math.hypot(dx, dz) / rim
            if e > 1:
                continue
            t = top - (1 if lip and e > 0.88 else 0) - (1 if lip and e > 0.97 else 0)
            dep = 1.5 + depth * (1 - e ** 1.7) ** 0.9 * (0.72 + 0.5 * n2(x, 0, z))
            for (sx, sz, sr, sl) in spk:
                dd = math.hypot(x - sx, z - sz)
                if dd < sr:
                    dep += sl * (1 - dd / sr) ** 1.7
            cols[(x, z)] = (round(t - dep), t)
    return cols


def merge_cols(*many):
    out = {}
    for cols in many:
        for k, (b, t) in cols.items():
            if k in out:
                ob, ot = out[k]
                out[k] = (min(b, ob), max(t, ot))
            else:
                out[k] = (b, t)
    return out


def build_rock(bp, cols, seed, surface="end_stone", deco=1.0, glow=True, keep=False):
    """Materialize a rock heightfield: end stone with obsidian veins, glowing crystal seams on
    the underside, and hanging end rods / starlight chains / amethyst on stalactite tips."""
    rng = random.Random(seed)
    vein = _noise(seed + 3, 3.0)
    for (x, z), (b, t) in cols.items():
        for y in range(b, t + 1):
            if y == t:
                blk = surface
            else:
                v = vein(x * 0.8, y * 2.2, z * 0.8)
                if v > 0.80:
                    blk = "obsidian"
                elif v > 0.77 and y - b < 3:
                    blk = "crying_obsidian"
                else:
                    blk = "end_stone"
            bp.set(x, y, z, blk, keep=keep)
    for (x, z), (b, t) in cols.items():
        nbs = [cols.get((x + dx, z + dz)) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        tip = all(n is None or n[0] > b for n in nbs)
        r = rng.random()
        if keep and bp.get(x, b - 1, z):
            continue
        if tip and t - b > 3:
            bp.set(x, b, z, "crying_obsidian" if rng.random() < 0.5 else "obsidian")
            if r < 0.35 * deco:
                bp.set(x, b - 1, z, ROD_DOWN)
            elif r < 0.62 * deco and glow:
                n = rng.randint(1, 4)
                bp.chain(x, b - n, z, b - 1)
                bp.set(x, b - n - 1, z, STAR if rng.random() < 0.5 else FROG)
            elif r < 0.85 * deco:
                bp.set(x, b - 1, z, "amethyst_cluster[facing=down,waterlogged=false]")
        elif r < 0.035 * deco:
            bp.set(x, b - 1, z, ROD_DOWN)
        elif r < 0.06 * deco:
            bp.set(x, b - 1, z, "amethyst_cluster[facing=down,waterlogged=false]")
        elif r < 0.10 * deco and glow:
            bp.set(x, b, z, STAR)


def rock(bp, cx, top, cz, rx, rz, depth, seed, spikes=6, surface="end_stone", deco=1.0):
    cols = rock_lobe(cx, top, cz, rx, rz, depth, seed, spikes)
    build_rock(bp, cols, seed, surface, deco)
    return cols


# ------------------------------------------------------------------ vegetation & lights
def chorus_tree(bp, x, y, z, h, rng, branches=3):
    """Organic chorus plant (connections computed from the cell set) with flowers on its tips."""
    cells, flowers = set(), []

    def grow(px, py, pz, length, depth):
        for k in range(length):
            cells.add((px, py + k, pz))
        ty = py + length - 1
        if depth >= branches or length < 2:
            flowers.append((px, ty + 1, pz))
            return
        dirs = rng.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], rng.randint(1, 3) if depth < 2 else rng.randint(1, 2))
        if rng.random() < 0.5:
            flowers.append((px, ty + 1, pz))
        for dx, dz in dirs:
            cells.add((px + dx, ty, pz + dz))
            grow(px + dx, ty + 1, pz + dz, rng.randint(1, max(2, length // 2 + 1)), depth + 1)

    grow(x, y, z, h, 0)
    every = cells | set(flowers)
    for (cx, cy, cz) in cells:
        props = {}
        for d, (dx, dy, dz) in (("up", (0, 1, 0)), ("down", (0, -1, 0)), ("north", (0, 0, -1)),
                                ("south", (0, 0, 1)), ("east", (1, 0, 0)), ("west", (-1, 0, 0))):
            props[d] = "true" if (cx + dx, cy + dy, cz + dz) in every or (d == "down" and cy == y) else "false"
        bp.set(cx, cy, cz, ("minecraft:chorus_plant", props))
    for f in flowers:
        if f not in cells:
            bp.set(*f, "chorus_flower[age=5]")
    bp.set(x, y - 1, z, "end_stone")


def chorus_patch(bp, cols, pts, rng, hmin=3, hmax=7, branches=3):
    """Chorus plants on rock columns (only where the top is bare end stone)."""
    for (x, z) in pts:
        if (x, z) not in cols:
            continue
        t = cols[(x, z)][1]
        if bp.get(x, t, z) != "minecraft:end_stone" or bp.get(x, t + 1, z):
            continue
        chorus_tree(bp, x, t + 1, z, rng.randint(hmin, hmax), rng, branches)


def star_lamp(bp, x, y, z, h=2, post=VB_WA, cap=PUR_SL):
    """Lamp post: wall post, starlight block, slab cap with an end rod."""
    for k in range(h):
        bp.set(x, y + k, z, post)
    bp.set(x, y + h, z, STAR)
    bp.set(x, y + h + 1, z, slab(cap))
    bp.set(x, y + h + 2, z, ROD_UP)


def hang_star(bp, x, y, z, n=2, light=FROG):
    """Chain hanging from the block above y, light at the bottom."""
    bp.chain(x, y - n + 1, z, y)
    bp.set(x, y - n, z, light)


def brazier(bp, x, y, z, h=3, body=VB, bowl=VB_ST, fire=STAR):
    """Pillar with a stair bowl holding a starlight core and end-rod flames."""
    for k in range(h):
        bp.set(x, y + k, z, body)
    top = y + h
    bp.set(x, top, z, fire)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + dx, top, z + dz, stair(bowl, face_vec(-dx, -dz), "top"))
        bp.set(x + dx, top + 1, z + dz, ROD_UP)
    for dx, dz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        bp.set(x + dx, top, z + dz, slab(bowl.replace("stairs", "slab"), "top"))
    bp.set(x, top + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")


# ------------------------------------------------------------------ bridges
def bridge(bp, a, b, width=3, rise=2.0, deck=PUR, deck_slab=PUR_SL, edge=VB, rail=ESB_WA, lamp_every=7,
           keel=VB):
    """Arched bridge between two walking surfaces a=(x, surface_y, z) and b. Half-slab steps keep
    it walkable; walls make the parapet, end rods light it and a keel gives the underside depth."""
    (x0, y0, z0), (x1, y1, z1) = a, b
    L = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    px, pz = -uz, ux
    hw = width // 2
    deck_s, rail_s = {}, {}
    n = int(L * 3) + 1
    for i in range(n + 1):
        t = i / n
        cx, cz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
        s = y0 + (y1 - y0) * t + rise * math.sin(math.pi * t)
        for w in range(-hw - 1, hw + 2):
            X, Z = round(cx + px * w), round(cz + pz * w)
            target = rail_s if abs(w) == hw + 1 else deck_s
            target.setdefault((X, Z), []).append((s, t))
    for (X, Z), ss in deck_s.items():
        s = sorted(v for v, _ in ss)[len(ss) // 2]
        q = round(s * 2)
        if q % 2 == 0:
            y = q // 2 - 1
            bp.set(X, y, Z, deck)
        else:
            y = (q - 1) // 2
            bp.set(X, y, Z, slab(deck_slab))
            bp.set(X, y - 1, Z, keel)
        for k in range(1, 4):
            if not bp.get(X, y + k, Z) or bp.get(X, y + k, Z) in ("minecraft:air",):
                bp.set(X, y + k, Z, "air")
    k = 0
    for (X, Z), ss in sorted(rail_s.items(), key=lambda kv: sorted(kv[1])[0][1]):
        if (X, Z) in deck_s:
            continue
        s = sorted(v for v, _ in ss)[len(ss) // 2]
        top = math.ceil(s - 0.01)
        bp.set(X, top - 1, Z, edge)
        bp.set(X, top - 2, Z, slab(VB_SL, "top"))
        bp.set(X, top, Z, rail)
        k += 1
        if lamp_every and k % lamp_every == 0:
            bp.set(X, top + 1, Z, ROD_UP)
    # keel under the centre line + a lantern chain at mid-span
    for i in range(n + 1):
        t = i / n
        X, Z = round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)
        s = y0 + (y1 - y0) * t + rise * math.sin(math.pi * t)
        yb = math.ceil(s - 0.01) - 2
        if 0.08 < t < 0.92:
            bp.set(X, yb, Z, keel, keep=False)
            if abs(t - 0.5) < 0.02:
                hang_star(bp, X, yb - 1, Z, 3)


# ------------------------------------------------------------------ round towers
def round_wall(bp, cx, cz, y0, y1, r, pal, clear=True):
    for (x, z) in ring_pts(cx, cz, r):
        for y in range(y0, y1 + 1):
            bp.set(x, y, z, pal.pick(x, y, z))
    if clear:
        for (x, z) in disk_pts(cx, cz, r - 1):
            for y in range(y0, y1 + 1):
                bp.set(x, y, z, "air")


def ring_stairs(bp, cx, cz, y, r, spec, half="top", inward=True):
    """A ring of stairs at radius r: corbels/cornices (top) or plinth slopes (bottom)."""
    for (x, z) in ring_pts(cx, cz, r):
        f = face_in(x, z, cx, cz)
        bp.set(x, y, z, stair(spec, f if inward else OPPOSITE[f], half))


def pilasters(bp, cx, cz, y0, y1, r, n, a0, spec=PUR_P, cap=PUR_ST, base=ESB):
    out = []
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        x, z = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
        bp.fill(x, y0, z, x, y1, z, spec)
        bp.set(x, y0, z, base)
        if cap:
            ox, oz = cx + round(math.cos(a) * (r + 2)), cz + round(math.sin(a) * (r + 2))
            bp.set(ox, y1, oz, stair(cap, face_in(ox, oz, cx, cz), "top"))
            bp.set(ox, y0, oz, stair(ESB_ST, face_in(ox, oz, cx, cz)))
        out.append((x, z, a))
    return out


def round_windows(bp, cx, cz, r, bays, wy0, wy1, half_w=1.1, glass="purple_stained_glass_pane",
                  hood=PUR_ST, keystone=STAR, sill=ESB_SL):
    """Tall windows in a round wall, with sill, hood mould and a glowing keystone."""
    pts = ring_pts(cx, cz, r)
    for b in bays:
        sel = [(x, z) for (x, z) in pts if adiff(math.atan2(z - cz, x - cx), b) * r <= half_w]
        for (x, z) in sel:
            for y in range(wy0, wy1 + 1):
                bp.set(x, y, z, glass)
            bp.set(x, wy1 + 1, z, PUR)
            a = math.atan2(z - cz, x - cx)
            ox, oz = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
            if (ox, oz) not in pts:
                if sill:
                    bp.set(ox, wy0 - 1, oz, slab(sill, "top"))
                if hood:
                    bp.set(ox, wy1 + 1, oz, stair(hood, face_in(ox, oz, cx, cz), "top"))
        if keystone:
            kx, kz = cx + round(math.cos(b) * r), cz + round(math.sin(b) * r)
            bp.set(kx, wy1 + 2, kz, keystone)


def helix(bp, cx, cz, s0, s1, r_in, r_out, pitch, a0=0.0, step=PUR, step_slab=PUR_SL, ccw=True):
    """Spiral stair around (cx, cz): walking surface rises `pitch` per turn from s0 to s1.
    Returns {(x, z): surface} of the topmost turn (for landing openings)."""
    R = int(r_out) + 1
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if not (r_in - 0.3 <= d <= r_out + 0.3):
                continue
            a = math.atan2(z - cz, x - cx)
            frac = ((a - a0) if ccw else (a0 - a)) % (2 * math.pi) / (2 * math.pi)
            k = 0
            while True:
                s = s0 + (frac + k) * pitch
                if s > s1 + 0.01:
                    break
                q = round(s * 2)
                if q % 2 == 0:
                    y = q // 2 - 1
                    bp.set(x, y, z, step)
                else:
                    y = (q - 1) // 2
                    bp.set(x, y, z, slab(step_slab))
                    bp.set(x, y - 1, z, slab(step_slab, "top"))
                for c in range(1, 4):
                    if math.ceil(s) + c - 1 <= s1 + 2:
                        bp.set(x, y + c, z, "air")
                k += 1


# ------------------------------------------------------------------ 3D curves
def ring3d(bp, c, R, u, v, spec, thick=False):
    n = int(2 * math.pi * R * 4)
    for i in range(n):
        t = 2 * math.pi * i / n
        p = [c[j] + R * (math.cos(t) * u[j] + math.sin(t) * v[j]) for j in range(3)]
        bp.set(round(p[0]), round(p[1]), round(p[2]), spec)
        if thick:
            bp.set(round(p[0]), round(p[1]) + 1, round(p[2]), spec)


def tube(bp, p0, d, length, r0, r1, body, rings=None, ring_every=4, back=0.0):
    """Solid cylinder along unit vector d from p0 (t in [-back, length]), radius r0 -> r1."""
    pts = [[p0[j] + d[j] * t for j in range(3)] for t in (-back, length)]
    lo = [math.floor(min(p[j] for p in pts)) - int(max(r0, r1)) - 2 for j in range(3)]
    hi = [math.ceil(max(p[j] for p in pts)) + int(max(r0, r1)) + 2 for j in range(3)]
    for x in range(lo[0], hi[0] + 1):
        for y in range(lo[1], hi[1] + 1):
            for z in range(lo[2], hi[2] + 1):
                w = (x - p0[0], y - p0[1], z - p0[2])
                t = w[0] * d[0] + w[1] * d[1] + w[2] * d[2]
                if t < -back or t > length:
                    continue
                perp = math.sqrt(max(0.0, w[0] ** 2 + w[1] ** 2 + w[2] ** 2 - t * t))
                rr = r0 + (r1 - r0) * max(0.0, t) / length
                if perp <= rr + 0.25:
                    is_ring = rings and (int(round(t)) % ring_every == 0)
                    bp.set(x, y, z, rings if is_ring else body.pick(x, y, z) if isinstance(body, Palette) else body)


# ================================================================== Void observatory
def void_observatory(bp):
    rng = random.Random(11)
    F = [0, 10, 20, 30]       # floor blocks of the tower storeys; dome gallery on F[3]
    R = 8                     # tower radius
    # --- rocks: main lobe + armillary lobe, three satellites
    main = merge_cols(rock_lobe(0, -1, 0, 19, 18, 24, 101, spikes=8),
                      rock_lobe(-19, -1, -3, 11, 10, 15, 102, spikes=4))
    build_rock(bp, main, 103)
    sat_e = rock(bp, 31, 5, -5, 6, 6, 11, 104, spikes=2)
    sat_s = rock(bp, 5, -4, 30, 6, 5, 10, 105, spikes=2)
    sat_nw = rock(bp, -21, 8, -26, 5, 5, 9, 106, spikes=2)

    # --- plaza: raised paving disc with a purpur ring, starlight inlays and a stepped edge
    pave = paving_pal(5)
    for (x, z) in disk_pts(0, 0, 15):
        bp.set(x, 0, z, pave.pick(x, 0, z))
    for (x, z) in disk_pts(-19, -3, 8):
        bp.set(x, 0, z, pave.pick(x, 0, z))
    for (x, z) in ring_pts(0, 0, 13.5):
        if math.hypot(x + 19, z + 3) > 8.4:
            bp.set(x, 0, z, PUR)
    for (x, z) in ring_pts(-19, -3, 6.5):
        bp.set(x, 0, z, PUR)
    for k in range(16):
        a = 2 * math.pi * k / 16
        bp.set(round(math.cos(a) * 11), 0, round(math.sin(a) * 11), STAR)
    for cx, cz, r, avoid in ((0, 0, 16, (-19, -3, 8.6)), (-19, -3, 9, (0, 0, 15.6))):
        for (x, z) in ring_pts(cx, cz, r):
            if math.hypot(x - avoid[0], z - avoid[1]) > avoid[2]:
                bp.set(x, 0, z, stair(ESB_ST, face_in(x, z, cx, cz)))
    # lamp posts around the plaza edge
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        x, z = round(math.cos(a) * 14.6), round(math.sin(a) * 14.6)
        if math.hypot(x + 19, z + 3) > 9:
            star_lamp(bp, x, 1, z)

    # --- the tower
    wall = void_pal(7)
    round_wall(bp, 0, 0, 1, F[3], R, wall)
    for (x, z) in disk_pts(0, 0, R):
        bp.set(x, 0, z, VB)
    # plinth: thick end stone brick base with a sloped course
    for (x, z) in ring_pts(0, 0, R + 1):
        for y in (1, 2):
            bp.set(x, y, z, ESB)
        bp.set(x, 3, z, stair(ESB_ST, face_in(x, z, 0, 0)))
    pils = pilasters(bp, 0, 0, 1, F[3] - 1, R, 8, math.pi / 8)
    for fy in (F[1], F[2]):
        for (x, z) in ring_pts(0, 0, R + 1):
            if not bp.get(x, fy, z):
                bp.set(x, fy, z, stair(VB_ST, face_in(x, z, 0, 0), "top"))
            if not bp.get(x, fy + 1, z):
                bp.set(x, fy + 1, z, slab(PUR_SL))
    bays = [2 * math.pi * k / 8 for k in range(8)]
    door_a = math.atan2(1, 0)  # south
    for i, fy in enumerate(F[:3]):
        round_windows(bp, 0, 0, R, [b for b in bays if i > 0 or adiff(b, door_a) > 0.1],
                      fy + 3, fy + 7, keystone=STAR if i != 1 else None)
    # floors (with the central well for the helix stair)
    for fy in F[1:]:
        for (x, z) in disk_pts(0, 0, R - 1):
            d = math.hypot(x, z)
            if d > 3.9:
                bp.set(x, fy, z, PUR if (x + z) % 2 else VB)
        for (x, z) in ring_pts(0, 0, 4.6, 3.6):
            bp.set(x, fy, z, ESB)
    # central column: purpur pillar with a starlight core, helix stair around it
    for y in range(1, F[3] + 4):
        for (x, z) in disk_pts(0, 0, 1):
            bp.set(x, y, z, STAR if (y % 9 == 5 and (x, z) != (0, 0)) else PUR_P)
    helix(bp, 0, 0, 1, F[3] + 1, 1.6, 3.6, 10.0, a0=math.pi / 2)
    # well railing (leave the landing open where the helix arrives)
    for fy in F[1:]:
        for (x, z) in ring_pts(0, 0, 4.6, 3.6):
            a = math.atan2(z, x)
            frac = (a - math.pi / 2) % (2 * math.pi) / (2 * math.pi)
            if frac > 0.16:
                bp.set(x, fy + 1, z, ESB_WA)
    # entrance portal (south): arched door with steps and flanking braziers
    bp.fill(-1, 1, R - 1, 1, 4, R + 1, "air")
    for dx in (-2, 2):
        bp.fill(dx, 1, R + 1, dx, 6, R + 1, PUR_P)
        bp.fill(dx, 1, R + 2, dx, 4, R + 2, VB)
        bp.set(dx, 5, R + 2, stair(VB_ST, "north"))
    bp.fill(-1, 5, R + 1, 1, 6, R + 1, PUR)
    bp.set(-1, 4, R + 1, stair(PUR_ST, "east", "top"))
    bp.set(1, 4, R + 1, stair(PUR_ST, "west", "top"))
    bp.set(0, 7, R + 1, STAR)
    bp.set(0, 6, R + 2, stair(PUR_ST, "north", "top"))
    for dx in (-1, 0, 1):
        bp.set(dx, 0, R + 1, ESB)
        bp.set(dx, 0, R + 2, ESB)
    for dx in (-4, 4):
        brazier(bp, dx, 1, R + 4, h=2)

    # --- gallery, windowed drum and copper dome
    for (x, z) in disk_pts(0, 0, R + 3):
        if math.hypot(x, z) > R - 0.6:
            bp.set(x, F[3], z, VB)
    ring_stairs(bp, 0, 0, F[3] - 1, R + 1, VB_ST)
    ring_stairs(bp, 0, 0, F[3] - 1, R + 2, VB_ST)
    ring_stairs(bp, 0, 0, F[3] - 2, R + 1, VB_ST)
    ring_stairs(bp, 0, 0, F[3], R + 4, VB_ST)
    for (x, z) in ring_pts(0, 0, R + 3):
        bp.set(x, F[3] + 1, z, ESB_WA)
    for (x, z, a) in pils:  # brackets under the gallery, lamps on the parapet
        ox, oz = round(math.cos(a) * (R + 2)), round(math.sin(a) * (R + 2))
        bp.set(ox, F[3] - 1, oz, PUR)
        bp.set(ox, F[3] - 2, oz, stair(PUR_ST, face_in(ox, oz, 0, 0), "top"))
        gx, gz = round(math.cos(a) * (R + 3)), round(math.sin(a) * (R + 3))
        star_lamp(bp, gx, F[3] + 1, gz, h=1, post=ESB_WA)
    drum_top = F[3] + 4
    round_wall(bp, 0, 0, F[3] + 1, drum_top, R, void_pal(8))
    pilasters(bp, 0, 0, F[3] + 1, drum_top, R, 16, 0, cap=None, base=PUR)
    round_windows(bp, 0, 0, R, [math.pi / 8 + k * math.pi / 4 for k in range(8)], F[3] + 2, F[3] + 3,
                  half_w=0.7, glass="magenta_stained_glass_pane", keystone=None)
    ring_stairs(bp, 0, 0, drum_top, R + 1, PUR_ST)
    for z in (R - 1, R, R + 1):  # doorway from the dome room onto the gallery
        bp.fill(0, F[3] + 1, z, 0, F[3] + 2, z, "air")
    shell = Palette({"oxidized_copper": 4, "oxidized_cut_copper": 3, "weathered_cut_copper": 1}, seed=3, scale=2.5)
    dc = drum_top
    DR = R
    for x in range(-DR - 2, DR + 3):
        for y in range(dc, dc + DR + 2):
            for z in range(-DR - 2, DR + 3):
                d = math.sqrt(x * x + (y - dc) ** 2 * 1.0 + z * z)
                if DR - 0.6 < d <= DR + 0.45:
                    bp.set(x, y, z, shell.pick(x, y, z))
                elif d <= DR - 0.6:
                    bp.set(x, y, z, "air")
    for k in range(8):  # purpur ribs
        a = 2 * math.pi * k / 8 + math.pi / 8
        for t in range(0, 91, 2):
            tt = math.radians(t)
            x = round(math.cos(a) * math.cos(tt) * (DR + 0.7))
            z = round(math.sin(a) * math.cos(tt) * (DR + 0.7))
            y = dc + round(math.sin(tt) * (DR + 0.7))
            bp.set(x, y, z, PUR)
    # the observing slit, facing south-east, from the drum to the crown
    slit_a = math.pi / 4
    for x in range(-DR - 2, DR + 3):
        for y in range(dc + 1, dc + DR + 3):
            for z in range(-DR - 2, DR + 3):
                d = math.sqrt(x * x + (y - dc) ** 2 + z * z)
                hr = math.hypot(x, z)
                if DR - 1.6 < d <= DR + 1.6 and (hr < 1.5 or adiff(math.atan2(z, x), slit_a) * max(hr, 1) <= 1.6):
                    bp.set(x, y, z, "air")
    # lantern cupola on the crown
    top = dc + DR + 1
    for (x, z) in disk_pts(0, 0, 2):
        bp.set(x, top, z, PUR)
    for (x, z) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        bp.fill(x, top + 1, z, x, top + 3, z, PUR_P)
    bp.set(0, top + 1, 0, STAR)
    bp.set(0, top + 2, 0, STAR)
    for (x, z) in disk_pts(0, 0, 2):
        bp.set(x, top + 4, z, slab(PUR_SL, "top") if math.hypot(x, z) > 1.5 else PUR)
    bp.set(0, top + 5, 0, PUR_P)
    bp.set(0, top + 6, 0, STAR)
    bp.set(0, top + 7, 0, "lightning_rod[facing=up,powered=false,waterlogged=false]")

    # --- the great telescope, aimed through the slit
    el = math.radians(36)
    d = (math.cos(el) * math.cos(slit_a), math.sin(el), math.cos(el) * math.sin(slit_a))
    pivot = (-1.0, dc + 3.0, -1.0)
    brass = Palette({"waxed_cut_copper": 3, "waxed_copper_block": 2}, seed=9, scale=2)
    tube(bp, pivot, d, 24, 1.8, 1.1, brass, rings="waxed_chiseled_copper", ring_every=5, back=4)
    tip = [pivot[j] + d[j] * 24.6 for j in range(3)]
    bp.set(round(tip[0]), round(tip[1]), round(tip[2]), "glass")
    bp.set(round(tip[0]), round(tip[1]) + 1, round(tip[2]), ROD_UP)
    # mount: a copper column with a stepped foot under the pivot
    bp.fill(-1, F[3] + 1, -1, -1, dc + 1, -1, "waxed_copper_block")
    for (x, z) in ((-2, -1), (-1, -2), (0, -1), (-1, 0)):
        bp.set(x, F[3] + 1, z, stair("waxed_cut_copper_stairs", face_in(x, z, -1, -1)))

    # --- stair turret (north-east): a slender tower rising past the gallery with a copper spire
    tx, tz = 8, -8
    round_wall(bp, tx, tz, 0, F[3] + 12, 3, void_pal(12))
    for (x, z) in ring_pts(tx, tz, 4):
        bp.set(x, 1, z, ESB)
        bp.set(x, 2, z, stair(ESB_ST, face_in(x, z, tx, tz)))
        bp.set(x, F[3] + 12, z, stair(VB_ST, face_in(x, z, tx, tz), "top"))
    round_windows(bp, tx, tz, 3, [-math.pi / 4, -3 * math.pi / 4], F[3] + 7, F[3] + 9, half_w=0.6,
                  glass="magenta_stained_glass_pane", hood=None, sill=None)
    for by in range(8, F[3] + 6, 8):  # purpur string courses
        for (x, z) in ring_pts(tx, tz, 4):
            if math.hypot(x, z) > R + 0.6:
                bp.set(x, by, z, stair(PUR_ST, face_in(x, z, tx, tz), "top"))
    for k, y in enumerate(range(6, F[3] + 6, 7)):
        a = -math.pi / 4 + (k % 2) * 0.6
        bp.set(tx + round(math.cos(a) * 3), y, tz + round(math.sin(a) * 3), "purple_stained_glass_pane")
        bp.set(tx + round(math.cos(a) * 3), y + 1, tz + round(math.sin(a) * 3), "purple_stained_glass_pane")
    for (x, z) in disk_pts(tx, tz, 4):
        bp.set(x, F[3] + 13, z, VB)
    for (x, z) in ring_pts(tx, tz, 4):
        bp.set(x, F[3] + 14, z, ESB_WA)
    sp = Palette({"waxed_oxidized_cut_copper": 3, "waxed_oxidized_copper": 2}, seed=4, scale=2)
    y = F[3] + 14
    for rr in (3, 3, 2, 2, 2, 1, 1, 1, 1):
        for (x, z) in disk_pts(tx, tz, rr):
            if math.hypot(x - tx, z - tz) > rr - 0.6 or rr == 1:
                bp.set(x, y, z, sp.pick(x, y, z))
        y += 1
    bp.fill(tx, y, tz, tx, y + 1, tz, "waxed_oxidized_copper")
    bp.set(tx, y + 2, tz, STAR)
    bp.set(tx, y + 3, tz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.ladder(tx + 2, 1, tz, F[3] + 2, "west")
    for yy in (1, 2):  # doorway between the tower and the turret
        for (x, z) in ((5, -6), (6, -6), (7, -6), (6, -7)):
            bp.set(x, yy, z, "air")
    for yy in (F[3] + 1, F[3] + 2):  # doorway onto the gallery
        bp.set(tx - 3, yy, tz, "air")
        bp.set(tx - 2, yy, tz, "air")

    # --- interiors
    # ground floor: hall of star charts (purpur compass ring, starlight inlays, chart desks)
    for (x, z) in ring_pts(0, 0, 5.5):
        bp.set(x, 0, z, PUR)
    for k in range(8):
        a = 2 * math.pi * k / 8
        bp.set(round(math.cos(a) * 6.5), 0, round(math.sin(a) * 6.5), STAR)
        bp.set(round(math.cos(a) * 4.5), 0, round(math.sin(a) * 4.5), "crying_obsidian")
    for (x, z, a) in pils:
        ix, iz = round(math.cos(a) * (R - 1)), round(math.sin(a) * (R - 1))
        if adiff(a, math.pi) > 0.5:
            bp.fill(ix, 1, iz, ix, 3, iz, "bookshelf")
            bp.set(ix, 4, iz, "candle[candles=3,lit=true,waterlogged=false]")
    for k, item in enumerate(["cartography_table", "lectern[facing=west,has_book=false,powered=false]",
                              "barrel[facing=up,open=false]", "lectern[facing=north,has_book=false,powered=false]",
                              "crafting_table", "loom[facing=north]"]):
        a = [math.pi / 4 * j for j in (0, 3, 5, 6, 1, 7)][k]
        x, z = round(math.cos(a) * 6), round(math.sin(a) * 6)
        bp.set(x, 1, z, item)
        cx, cz = round(math.cos(a) * 5), round(math.sin(a) * 5)
        bp.stairs(cx, 1, cz, PUR_ST, face_in(cx, cz, 0, 0))
    bp.bookshelf_wall(-7, 1, -1, -7, 2, 1)
    bp.set(6, 1, -3, "ender_chest[facing=west,waterlogged=false]")
    bp.chest(6, 1, 3, "west", LOOT + "void_observatory")
    for (x, z) in ((5, -5), (-5, -5), (-5, 5), (5, 5)):
        hang_star(bp, x, F[1] - 1, z, 2)
    # second floor: the star library (spawner in the stacks)
    fy = F[1]
    for (x, z) in ring_pts(0, 0, R - 1):
        bp.fill(x, fy + 1, z, x, fy + 2, z, "bookshelf")
    for (x, z, a) in pils:
        ix, iz = round(math.cos(a) * (R - 1)), round(math.sin(a) * (R - 1))
        bp.fill(ix, fy + 1, iz, ix, fy + 7, iz, "bookshelf")
    for (x, z) in ((5, 0), (-5, 0)):
        bp.set(x, fy + 1, z, "lectern[facing=north,has_book=false,powered=false]")
    bp.set(0, fy + 1, 5, "enchanting_table")
    bp.spawner(0, fy + 1, -5, MOB["void_stalker"])
    for (x, z) in ((4, 4), (-4, -4), (4, -4), (-4, 4)):
        hang_star(bp, x, F[2] - 1, z, 2, STAR)
    # third floor: instrument workshop
    fy = F[2]
    for (x, z), item in zip(((5, 2), (5, -2), (-5, 2), (-5, -2), (2, 5), (-2, 5), (2, -5), (-2, -5)),
                            ["brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]",
                             "amethyst_cluster[facing=up,waterlogged=false]", "barrel[facing=up,open=false]",
                             "smithing_table", "cauldron", "grindstone[face=floor,facing=north]",
                             "barrel[facing=up,open=false]", "crafting_table"]):
        bp.set(x, fy + 1, z, item)
    bp.bed(-5, fy + 1, 4, "east", "magenta")
    for (x, z) in ((4, 4), (-4, -4), (4, -4)):
        hang_star(bp, x, F[3] - 1, z, 2)
    # dome room: telescope chair, the best chest and charts
    fy = F[3]
    bp.chest(-4, fy + 1, 3, "east", LOOT + "void_observatory")
    bp.set(-4, fy + 1, -3, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(3, fy + 1, -4, "cartography_table")
    bp.stairs(-3, fy + 1, -3, PUR_ST, "west")
    for (x, z) in ((5, 0), (-5, 0), (0, -5)):
        bp.set(x, fy + 1, z, "candle[candles=3,lit=true,waterlogged=false]")

    # --- the armillary sphere on the west terrace
    ac = (-19, 10, -3)
    bp.fill(-20, 1, -4, -18, 1, -2, PUR)
    bp.fill(-19, 2, -3, -19, 3, -3, PUR_P)
    for (x, z) in ring_pts(-19, -3, 2.2, 1):
        bp.set(x, 1, z, stair(PUR_ST, face_in(x, z, -19, -3)))
    ring3d(bp, ac, 7, (1, 0, 0), (0, 1, 0), "waxed_copper_block")                  # meridian
    ring3d(bp, ac, 7, (0, 0, 1), (0, 1, 0), "waxed_oxidized_cut_copper")           # colure
    e = math.radians(28)
    ring3d(bp, ac, 6, (1, 0, 0), (0, math.sin(e), math.cos(e)), "gold_block")     # ecliptic
    ring3d(bp, ac, 7, (1, 0, 0), (0, 0, 1), "waxed_oxidized_copper")             # equator
    ring3d(bp, ac, 4, (math.cos(e), math.sin(e), 0), (0, 0, 1), "waxed_weathered_cut_copper")
    for j in range(-6, 7):  # polar axis
        bp.set(ac[0], ac[1] + j, ac[2], "iron_chain[axis=y,waterlogged=false]")
    bp.set(ac[0], ac[1] - 7, ac[2], "waxed_copper_block")
    bp.fill(ac[0], 4, ac[2], ac[0], ac[1] - 8, ac[2], PUR_P)
    for (dx, dy, dz) in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        bp.set(ac[0] + dx, ac[1] + dy, ac[2] + dz, STAR)
    for (dx, dz, f) in ((2, 0, "east"), (-2, 0, "west"), (0, 2, "south"), (0, -2, "north")):
        bp.set(ac[0] + dx, ac[1], ac[2] + dz, f"end_rod[facing={f}]")
    bp.set(ac[0], ac[1] + 8, ac[2], ROD_UP)
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, z = -19 + round(math.cos(a) * 7.5), -3 + round(math.sin(a) * 7.5)
        brazier(bp, x, 1, z, h=1, body=PUR_P, bowl=PUR_ST)

    # --- satellites: lens turret (east), obelisk (south), chorus shrine (north-west)
    st = void_pal(21)
    round_wall(bp, 31, -5, 6, 15, 3, st)
    for (x, z) in disk_pts(31, -5, 3):
        bp.set(x, 5, z, VB)
    for (x, z) in ring_pts(31, -5, 4):
        bp.set(x, 6, z, stair(ESB_ST, face_in(x, z, 31, -5)))
        bp.set(x, 15, z, stair(VB_ST, face_in(x, z, 31, -5), "top"))
    for (x, z) in disk_pts(31, -5, 4):
        bp.set(x, 16, z, VB)
    for (x, z) in ring_pts(31, -5, 4):
        bp.set(x, 17, z, ESB_WA)
    round_windows(bp, 31, -5, 3, [0, math.pi / 2, math.pi, -math.pi / 2], 9, 11, half_w=0.6, keystone=None,
                  hood=None)
    bp.fill(30, 6, -5, 30, 7, -5, "air")
    bp.fill(28, 6, -5, 28, 7, -5, "air")
    bp.ladder(32, 6, -5, 16, "west")
    bp.set(32, 16, -5, "air")
    bp.set(31, 6, -6, "barrel[facing=up,open=false]")
    sd = (math.cos(math.radians(30)) * math.cos(-0.5), math.sin(math.radians(30)), math.cos(math.radians(30)) * math.sin(-0.5))
    tube(bp, (31.0, 19.0, -5.0), sd, 8, 1.0, 0.8, brass, rings="waxed_chiseled_copper", ring_every=4, back=2)
    bp.fill(31, 17, -5, 31, 18, -5, "waxed_copper_block")
    # obelisk + chorus on the south rock
    for y in range(-3, 13):
        w = 1 if y < 9 else 0
        for dx in range(-w, w + 1):
            for dz in range(-w, w + 1):
                bp.set(5 + dx, y, 30 + dz, VB if (y % 5) else PUR)
    bp.set(5, 13, 30, STAR)
    bp.set(5, 14, 30, ROD_UP)
    for (x, z) in ring_pts(5, 30, 2.2, 1):
        bp.set(x, -3, z, stair(ESB_ST, face_in(x, z, 5, 30)))
    chorus_patch(bp, sat_s, [(1, 28), (8, 32), (3, 33), (8, 27)], rng, 3, 6)
    # chorus shrine: a ring of purpur posts around a starlight font
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, z = -21 + round(math.cos(a) * 3.5), -26 + round(math.sin(a) * 3.5)
        bp.fill(x, 9, z, x, 12, z, PUR_P)
        bp.set(x, 13, z, slab(PUR_SL))
    bp.set(-21, 9, -26, STAR)
    bp.set(-21, 10, -26, "amethyst_cluster[facing=up,waterlogged=false]")
    chorus_patch(bp, sat_nw, [(-24, -24), (-18, -28), (-20, -22), (-25, -28)], rng, 3, 6)

    # --- bridges linking the satellites
    bridge(bp, (15, 1, -3), (27, 6, -5), width=3, rise=2.5)
    bridge(bp, (2, 1, 16), (4, -3, 26), width=3, rise=1.5)
    bridge(bp, (-20, 1, -12), (-21, 9, -22), width=3, rise=1.5)

    # --- chorus around the plaza and secret star vault under the tower
    chorus_patch(bp, main, [(rng.randint(-26, 18), rng.randint(-18, 18)) for _ in range(28)], rng, 3, 5)
    # the vault: a bookshelf on the ground floor hides a ladder down into the rock
    bp.set(-7, 1, 0, "bookshelf")
    bp.set(-7, 2, 0, "bookshelf")
    bp.set(-7, 0, 0, "air")
    bp.ladder(-7, -8, 0, 0, "east")
    bp.clear(-6, -9, -3, -1, -5, 3)
    bp.fill(-7, -10, -4, 0, -10, 4, VB)
    bp.fill(-6, -10, -3, -1, -10, 3, "obsidian")
    bp.set(-4, -10, 0, STAR)
    bp.chest(-2, -9, 0, "west", LOOT + "void_observatory")
    bp.set(-2, -9, -2, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.set(-2, -9, 2, "amethyst_cluster[facing=up,waterlogged=false]")
    hang_star(bp, -4, -5, 0, 1, STAR)
    bp.spawner(-5, -9, -2, MOB["void_stalker"])
    INT.decorate(bp, "end", seed=1)


register(StructureDef(
    "void_observatory", "end", OUTER_END, [Piece("observatory", void_observatory)],
    spacing=20, separation=6, adaptation="none", height=("uniform", 60, 85), processors="aging",
    spawns=[("brasshaven:rift_sentinel", 5, 1, 1), ("minecraft:enderman", 10, 1, 2)], creatures=[("rift_sentinel", 2)],
    title_fr="Observatoire du vide", title_en="Void Observatory"))


# ================================================================== Floating chorus garden
def terrace(bp, cx, cz, r0, y_base, y_top, seed, wall, top="end_stone", coping=PUR_ST, rough=0.08):
    """Organic terrace: retaining wall (palette) with purpur coping overhang and a sloped plinth.
    Returns the set of columns inside."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.3) for _ in range(3)]
    R = int(r0 * (1 + rough * 2)) + 2
    inside = set()
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            th = math.atan2(z - cz, x - cx)
            rr = r0 * (1 + rough * math.sin(3 * th + ph[0]) + rough * 0.6 * math.sin(5 * th + ph[1]))
            if math.hypot(x - cx, z - cz) <= rr:
                inside.add((x, z))
    nb4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    edge = {p for p in inside if any((p[0] + dx, p[1] + dz) not in inside for dx, dz in nb4)}
    for (x, z) in inside:
        for y in range(y_base, y_top):
            bp.set(x, y, z, wall.pick(x, y, z) if (x, z) in edge else "end_stone")
        bp.set(x, y_top, z, PUR if (x, z) in edge else top)
    for (x, z) in edge:
        for dx, dz in nb4:
            o = (x + dx, z + dz)
            if o in inside:
                continue
            f = face_vec(-dx, -dz)
            bp.set(o[0], y_top, o[1], stair(coping, f, "top"))
            bp.set(o[0], y_base, o[1], stair(ESB_ST, f))
    return inside, edge


def steps(bp, x, z, direction, y_from, n, width=3, fill=ESB, spec=PUR_ST):
    """Straight flight climbing toward `direction`: step k is a stair block at y_from + k."""
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[direction]
    px, pz = -dz, dx
    hw = width // 2
    for k in range(n):
        for w in range(-hw, hw + 1):
            sx, sz = x + dx * k + px * w, z + dz * k + pz * w
            bp.set(sx, y_from + k, sz, stair(spec, direction))
            for yy in range(y_from - 2, y_from + k):
                bp.set(sx, yy, sz, fill)
            for c in range(1, 4):
                bp.set(sx, y_from + k + c, sz, "air")
        for w in (-hw - 1, hw + 1):
            sx, sz = x + dx * k + px * w, z + dz * k + pz * w
            for yy in range(y_from - 1, y_from + k + 1):
                bp.set(sx, yy, sz, fill)
            bp.set(sx, y_from + k + 1, sz, ESB_WA)


def gazebo(bp, cx, y, cz, r, n=8, h=5, roof="dome", loot=None):
    """Open purpur pavilion: columns on a ring, arched lintels, an entablature and a dome."""
    cols = []
    for k in range(n):
        a = 2 * math.pi * k / n + math.pi / n
        cols.append((cx + round(math.cos(a) * r), cz + round(math.sin(a) * r)))
    for (x, z) in disk_pts(cx, cz, r + 1):
        bp.set(x, y - 1, z, PUR if math.hypot(x - cx, z - cz) > r - 0.5 else ESB)
    for (x, z) in ring_pts(cx, cz, r + 2):
        bp.set(x, y - 1, z, stair(PUR_ST, face_in(x, z, cx, cz)))
    for (x, z) in cols:
        bp.set(x, y, z, VB)
        bp.fill(x, y + 1, z, x, y + h - 1, z, PUR_P)
        bp.set(x, y + h, z, PUR)
    top = y + h
    for (a, b) in zip(cols, cols[1:] + cols[:1]):
        L = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for i in range(L + 1):
            px = round(a[0] + (b[0] - a[0]) * i / L)
            pz = round(a[1] + (b[1] - a[1]) * i / L)
            bp.set(px, top, pz, VB)
            if 0 < i < L and (i == 1 or i == L - 1):
                to = a if i == 1 else b
                bp.set(px, top - 1, pz, stair(PUR_ST, face_vec(to[0] - px, to[1] - pz), "top"))
    for (x, z) in ring_pts(cx, cz, r + 1):
        bp.set(x, top, z, stair(VB_ST, face_in(x, z, cx, cz), "top"))
    for (x, z) in disk_pts(cx, cz, r):
        if not bp.get(x, top, z):
            bp.set(x, top, z, slab(PUR_SL, "top"))
    if roof == "dome":
        for x in range(cx - r - 1, cx + r + 2):
            for yy in range(top + 1, top + r + 2):
                for z in range(cz - r - 1, cz + r + 2):
                    d = math.sqrt((x - cx) ** 2 + ((yy - top) * 1.15) ** 2 + (z - cz) ** 2)
                    if r - 0.6 < d <= r + 0.45:
                        bp.set(x, yy, z, PUR)
                    elif d <= r - 0.6:
                        bp.set(x, yy, z, "air")
        for k in range(n):  # void-brick ribs above each column
            a = 2 * math.pi * k / n + math.pi / n
            for t in range(0, 91, 3):
                tt = math.radians(t)
                x = cx + round(math.cos(a) * math.cos(tt) * (r + 0.6))
                z = cz + round(math.sin(a) * math.cos(tt) * (r + 0.6))
                bp.set(x, top + 1 + round(math.sin(tt) * (r + 0.6) / 1.15), z, VB)
        ytop = top + int(r / 1.15) + 1
        for (x, z) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(cx + x, ytop + 1, cz + z, PUR_P)
        bp.set(cx, ytop, cz, STAR)
        bp.set(cx, ytop + 1, cz, STAR)
        bp.set(cx, ytop + 2, cz, PUR)
        for (x, z) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(cx + x, ytop + 2, cz + z, stair(PUR_ST, face_vec(-x, -z)))
        bp.set(cx, ytop + 3, cz, PUR_P)
        bp.set(cx, ytop + 4, cz, ROD_UP)
        hang_star(bp, cx, ytop - 1, cz, 2, FROG)
    else:
        for (x, z) in disk_pts(cx, cz, r):
            bp.set(x, top + 1, z, slab(PUR_SL))
        bp.set(cx, top + 1, cz, PUR)
        bp.set(cx, top + 2, cz, STAR)
        bp.set(cx, top + 3, cz, ROD_UP)
    return cols, top


def hanging_vines(bp, cols, rng, chance=0.12, max_len=8):
    """Pale hanging moss trailing from the underside of a rock (the 'hanging garden')."""
    for (x, z), (b, t) in cols.items():
        if t - b < 3 or rng.random() > chance or bp.get(x, b - 1, z):
            continue
        n = rng.randint(2, max_len)
        for k in range(1, n + 1):
            if bp.get(x, b - k, z):
                break
            bp.set(x, b - k, z, f"pale_hanging_moss[tip={'true' if k == n else 'false'}]")


def chorus_garden(bp):
    rng = random.Random(23)
    # --- the rock: main island, two islets
    main = merge_cols(rock_lobe(0, 0, 0, 25, 19, 22, 201, spikes=8),
                      rock_lobe(-8, 0, -6, 14, 12, 26, 202, spikes=3))
    build_rock(bp, main, 203, deco=0.6)
    isl_e = rock(bp, 33, 3, 7, 7, 6, 12, 204, spikes=2, deco=0.6)
    isl_w = rock(bp, -22, -3, 23, 6, 6, 11, 205, spikes=2, deco=0.6)
    isl_n = rock(bp, 10, 7, -27, 5, 4, 9, 206, spikes=1, deco=0.6)
    wall = Palette({ESB: 6, VB: 2}, seed=4, scale=2.0)

    # --- terraces: lower ring (y 0) -> middle terrace (top 4) -> crown terrace (top 8)
    mid, mid_edge = terrace(bp, 2, -1, 15, 1, 4, 207, wall)
    top_in, top_edge = terrace(bp, 3, -2, 9.5, 5, 8, 208, wall, top=ESB, rough=0.04)
    # paving: a ring path on the middle terrace and radial paths to the stairs
    pave = paving_pal(9)
    for (x, z) in ring_pts(3, -2, 11.5, 9.6):
        if (x, z) in mid and (x, z) not in mid_edge:
            bp.set(x, 4, z, pave.pick(x, 4, z))
    for (x, z) in ring_pts(3, -2, 12.5):
        if (x, z) in mid and (x, z) not in mid_edge and bp.get(x, 4, z) == "minecraft:end_stone":
            bp.set(x, 4, z, PUR)
    for (x, z) in top_in:
        if (x, z) not in top_edge and (x + z) % 5 == 0:
            bp.set(x, 8, z, PUR)
    # stairs: south flight to the middle terrace, and to the crown; an east flight too
    steps(bp, 2, 17, "north", 1, 4, width=5)
    for z in range(14, 17):
        for x in range(0, 5):
            bp.set(x, 4, z, ESB)
    for z in range(10, 14):
        for x in range(1, 4):
            bp.set(x, 4, z, pave.pick(x, 4, z))
    steps(bp, 3, 10, "north", 5, 4, width=3)
    steps(bp, 18, -1, "west", 1, 4, width=3)
    for x in range(12, 15):
        for z in range(-2, 1):
            bp.set(x, 4, z, pave.pick(x, 4, z))
    # lower path around the base of the middle terrace
    for (x, z) in ring_pts(2, -1, 17.5, 16):
        if (x, z) in main and bp.get(x, 0, z) == "minecraft:end_stone":
            bp.set(x, 0, z, PUR if (x * 3 + z) % 7 == 0 else ESB)

    # --- the crown pavilion
    pc = (3, -2)
    cols, ptop = gazebo(bp, pc[0], 9, pc[1], 6, n=8, h=7)
    bp.chest(pc[0] + 2, 9, pc[1] - 2, "west", LOOT + "chorus_garden")
    bp.set(pc[0] - 2, 9, pc[1] - 2, "composter[level=6]")
    bp.set(pc[0] - 2, 9, pc[1] + 2, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    bp.set(pc[0] + 2, 9, pc[1] + 2, "lectern[facing=west,has_book=false,powered=false]")
    # starlight font in the middle (a basin of water around a glowing core)
    for (x, z) in ring_pts(pc[0], pc[1], 1.5, 0.5):
        bp.set(x, 9, z, stair(PUR_ST, face_in(x, z, pc[0], pc[1]), "top"))
    bp.set(pc[0], 8, pc[1], STAR)
    bp.set(pc[0], 9, pc[1], "water[level=0]")
    # balustrade around the crown terrace
    for (x, z) in top_edge:
        if not (abs(x - 3) <= 1 and z > 3):
            bp.set(x, 9, z, ESB_WA)
    for (x, z) in list(top_edge)[::9]:
        if not (abs(x - 3) <= 1 and z > 3):
            star_lamp(bp, x, 9, z, h=1, post=ESB_WA)

    # --- reflecting pool on the middle terrace (east), lamp posts, pergolas
    for (x, z) in disk_pts(11, -10, 2.6):
        if (x, z) in mid and (x, z) not in mid_edge:
            bp.set(x, 4, z, "water[level=0]")
            bp.set(x, 3, z, STAR if (x + z) % 3 == 0 else PUR)
    for (x, z) in ring_pts(11, -10, 3.6):
        if (x, z) in mid and (x, z) not in mid_edge:
            bp.set(x, 4, z, PUR)
            if (x + z) % 2:
                bp.set(x, 5, z, slab(PUR_SL))
    for (x, z) in ((-8, 4), (-6, -11), (4, -14), (14, 6), (-9, -3), (8, 9)):
        if (x, z) in mid:
            star_lamp(bp, x, 5, z)
    for (x, z) in ((-14, 10), (-20, -2), (-12, -17), (16, -15), (20, 10), (7, 17), (-4, 17)):
        if (x, z) in main:
            star_lamp(bp, x, 1, z, h=3)
    # pergola over the south stair: two purpur arches hung with froglights
    for zz in (13, 10):
        for x in (0, 4):
            bp.fill(x, 5, zz, x, 8, zz, PUR_P)
        bp.fill(0, 9, zz, 4, 9, zz, VB)
        bp.set(1, 8, zz, stair(PUR_ST, "west", "top"))
        bp.set(3, 8, zz, stair(PUR_ST, "east", "top"))
        hang_star(bp, 2, 8, zz, 1, FROG)

    # --- the lantern spire: a slender belfry on the middle terrace (north-west)
    lx, lz = -8, 5
    for y in range(5, 24):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                corner = dx and dz
                bp.set(lx + dx, y, lz + dz, PUR_P if corner else VB)
    for (x, z) in ring_pts(lx, lz, 2.4, 1.4):
        bp.set(x, 5, z, stair(ESB_ST, face_in(x, z, lx, lz)))
    for by in (11, 17):
        for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            bp.set(lx + dx, by, lz + dz, stair(PUR_ST, face_vec(-dx, -dz), "top"))
    for y in range(19, 23):  # open belfry with a starlight core
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bp.set(lx + dx, y, lz + dz, "air")
        bp.set(lx, y, lz, STAR if y in (20, 21) else "air")
    for (x, z) in ring_pts(lx, lz, 2.4, 0.4):
        bp.set(x, 24, z, stair(VB_ST, face_in(x, z, lx, lz), "top"))
    for y, rr in ((24, 1), (25, 1), (26, 0), (27, 0)):
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                bp.set(lx + dx, y, lz + dz, PUR if rr else PUR_P)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(lx + dx, 26, lz + dz, stair(PUR_ST, face_vec(-dx, -dz)))
    bp.set(lx, 28, lz, STAR)
    bp.set(lx, 29, lz, ROD_UP)

    # --- chorus forests: tall groves on the lower ring, smaller ones on the middle terrace
    lower = [p for p in main if p not in mid and math.hypot(p[0] - 2, p[1] + 1) > 17.5]
    rng.shuffle(lower)
    chorus_patch(bp, main, lower[:26], rng, 4, 7, branches=3)
    inner = [p for p in mid if p not in mid_edge and p not in top_in and bp.get(p[0], 4, p[1]) == "minecraft:end_stone"]
    rng.shuffle(inner)
    for (x, z) in inner[:16]:
        if bp.get(x, 5, z) is None and all(bp.get(x + dx, 5, z + dz) is None for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            chorus_tree(bp, x, 5, z, rng.randint(2, 4), rng, 2)

    # --- islets: east gazebo with a chest, west moon gate, north chorus spire; bridges
    gazebo(bp, 33, 4, 7, 3, n=4, h=4, roof="flat")
    bp.chest(33, 4, 7, "north", LOOT + "chorus_garden")
    chorus_patch(bp, isl_e, [(29, 3), (37, 10), (36, 3), (30, 11)], rng, 4, 7)
    gx, gz = -22, 23
    for (x, z) in disk_pts(gx, gz, 3):
        bp.set(x, -3, z, ESB)
    for t in range(0, 181, 6):  # moon gate ring facing the bridge
        a = math.radians(t)
        bp.set(gx + round(math.cos(a) * 3.5), -2 + round(math.sin(a) * 3.5) + 0, gz, PUR)
    bp.fill(gx - 4, -2, gz, gx - 4, -2, gz, PUR)
    bp.set(gx, 2, gz, STAR)
    for x in (gx - 2, gx + 2):
        bp.stairs(x, -2, gz + 2, PUR_ST, "south")
    chorus_patch(bp, isl_w, [(-25, 20), (-19, 26), (-26, 25), (-18, 20)], rng, 4, 7)
    chorus_patch(bp, isl_n, [(10, -27), (8, -26), (12, -28)], rng, 6, 10)
    bridge(bp, (23, 1, 3), (29, 4, 6), width=3, rise=1.5)
    bridge(bp, (-14, 1, 16), (-19, -2, 21), width=3, rise=1.0)
    bridge(bp, (8, 1, -18), (10, 8, -24), width=1, rise=1.0, lamp_every=4)

    # --- hanging gardens: glow-berry vines, ledges with chorus and lamps under the rim
    hanging_vines(bp, main, rng, 0.10, 9)
    hanging_vines(bp, isl_e, rng, 0.15, 6)
    hanging_vines(bp, isl_w, rng, 0.15, 6)
    for (lx, ly, lz) in ((-23, -6, 6), (16, -5, 15), (-4, -7, -20), (22, -8, -9)):
        led = rock_lobe(lx, ly, lz, 4, 3, 4, lx * 7 + lz, spikes=1, lip=False)
        build_rock(bp, led, lz * 3 + 1, deco=0.5)
        chorus_patch(bp, led, [(lx + rng.randint(-2, 2), lz + rng.randint(-1, 1)) for _ in range(3)], rng, 3, 5, 2)
        star_lamp(bp, lx, ly + 1, lz, h=1)
        hanging_vines(bp, led, rng, 0.35, 5)

    # --- secret grotto under the crown: the glowing font block hides a ladder shaft into the rock
    gc = (pc[0], pc[1] + 4)
    for (x, z) in ring_pts(gc[0], gc[1], 5):
        for y in range(-8, -1):
            bp.set(x, y, z, "end_stone")
    for (x, z) in disk_pts(gc[0], gc[1], 4):
        bp.fill(x, -7, z, x, -3, z, "air")
        bp.set(x, -8, z, "moss_block" if (x * 3 + z) % 4 else STAR)
        bp.set(x, -2, z, "end_stone")
        if rng.random() < 0.3:
            bp.set(x, -3, z, "pale_hanging_moss[tip=true]")
    bp.chest(gc[0], -7, gc[1] + 3, "north", LOOT + "chorus_garden")
    bp.spawner(gc[0] + 2, -7, gc[1], "minecraft:endermite")
    hang_star(bp, gc[0] - 1, -3, gc[1], 1, FROG)
    for (x, z) in ((gc[0] - 3, gc[1]), (gc[0] - 2, gc[1] + 2), (gc[0] + 3, gc[1] + 1)):
        bp.set(x, -8, z, "end_stone")
        chorus_tree(bp, x, -7, z, rng.randint(2, 3), rng, 1)
    bp.fill(pc[0], -7, pc[1] - 1, pc[0], 8, pc[1] - 1, "end_stone")
    bp.ladder(pc[0], -7, pc[1], 8, "south")
    bp.set(pc[0], 9, pc[1], STAR)
    INT.decorate(bp, dict(INT.THEMES["end"], density=0.25), seed=1, centre=False)


register(StructureDef(
    "chorus_garden", "end", OUTER_END, [Piece("garden", chorus_garden)],
    spacing=18, separation=5, adaptation="none", height=("uniform", 55, 80), processors="none",
    spawns=[("brasshaven:rift_sentinel", 4, 1, 1), ("minecraft:enderman", 10, 1, 2)], creatures=[("rift_sentinel", 1)],
    title_fr="Jardin flottant de chorus", title_en="Floating Chorus Garden"))


# ================================================================== End archive
def octagon(a, b):
    """Columns of an octagon: |x|,|z| <= a and |x| + |z| <= b (centred on 0, 0)."""
    return {(x, z) for x in range(-a, a + 1) for z in range(-a, a + 1) if abs(x) + abs(z) <= b}


def oct_edge(cells):
    return {p for p in cells if any((p[0] + dx, p[1] + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def oct_outside(cells):
    """Cells just outside the octagon, with the facing that points back at it."""
    out = {}
    for (x, z) in cells:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            o = (x + dx, z + dz)
            if o not in cells:
                out[o] = face_vec(-dx, -dz)
    return out


def flying_buttress(bp, p0, p1, thick=4.0, body=VB, cap=PUR_SL):
    """Flying buttress from a pier p0=(x, y, z) to a wall point p1: a sloped beam with a half-slab
    coping and an arched soffit (quarter ellipse) springing low from the pier."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    L = math.hypot(x1 - x0, z1 - z0)
    n = int(L * 3) + 1
    cols = {}
    for i in range(n + 1):
        t = i / n
        x, z = round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)
        cols.setdefault((x, z), []).append(t)
    for (x, z), ts in cols.items():
        t = sorted(ts)[len(ts) // 2]
        s = y0 + (y1 - y0) * t
        q = round(s * 2)
        top = q // 2
        spring = y0 - thick
        bot = round(spring + (s - 2 - spring) * math.sqrt(max(0.0, 1 - (1 - t) ** 2)))
        for y in range(bot, top):
            bp.set(x, y, z, body)
        if q % 2:
            bp.set(x, top, z, slab(cap))
        else:
            bp.set(x, top - 1, z, cap.replace("_slab", "_block") if cap.endswith("_slab") else cap)
        if bot < top - 2:
            bp.set(x, bot - 1, z, slab(VB_SL, "top"))
    for t in (0.33, 0.66):
        x, z = round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)
        s = y0 + (y1 - y0) * t
        bp.set(x, round(s * 2) // 2 + 1, z, ROD_UP)


def pier(bp, x, z, y0, y1, pal, spire=8):
    """3x3 buttress pier with purpur corners, a setback and a pinnacle."""
    for y in range(y0, y1 + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bp.set(x + dx, y, z + dz, PUR_P if (dx and dz) else pal.pick(x + dx, y, z + dz))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x + 2 * dx, y0, z + 2 * dz, stair(ESB_ST, face_vec(-dx, -dz)))
        bp.set(x + 2 * dx, y1, z + 2 * dz, stair(VB_ST, face_vec(-dx, -dz), "top"))
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        bp.set(x + dx, y1 + 1, z + dz, slab(PUR_SL))
    for k in range(spire):
        bp.set(x, y1 + 1 + k, z, PUR if k < spire - 3 else PUR_P)
        if k == 1:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bp.set(x + dx, y1 + 1 + k, z + dz, stair(PUR_ST, face_vec(-dx, -dz)))
    bp.set(x, y1 + spire - 2, z, STAR)
    bp.set(x, y1 + spire + 1, z, ROD_UP)


def end_archive(bp):
    rng = random.Random(31)
    F = [0, 11, 22, 33, 44]   # hall floors; F[4] = roof walk / dome chamber floor
    A, B = 10, 14             # tower octagon
    # --- rocks
    main = rock_lobe(0, -1, 0, 22, 21, 26, 301, spikes=9)
    build_rock(bp, main, 302)
    sats = []
    for k, ang in enumerate((0.0, 2.1, 4.2)):
        sx, sz = round(math.cos(ang) * 33), round(math.sin(ang) * 33)
        sats.append((sx, sz, ang, rock(bp, sx, 8, sz, 6, 6, 13, 303 + k, spikes=2)))

    # --- plaza: octagonal paving with a purpur border and a stepped rim
    plaza = octagon(17, 24)
    pave = paving_pal(3)
    for (x, z) in plaza:
        bp.set(x, 0, z, pave.pick(x, 0, z))
    for (x, z) in oct_edge(octagon(15, 21)):
        bp.set(x, 0, z, PUR)
    for (o, f) in oct_outside(plaza).items():
        bp.set(o[0], 0, o[1], stair(ESB_ST, f))
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        bp.set(round(math.cos(a) * 13), 0, round(math.sin(a) * 13), STAR)

    # --- tower body: four stacked reading halls
    wall = void_pal(13)
    body = octagon(A, B)
    edge = oct_edge(body)
    inner = body - edge
    for (x, z) in body:
        bp.set(x, 0, z, VB)
        for y in range(1, F[4]):
            bp.set(x, y, z, wall.pick(x, y, z) if (x, z) in edge else "air")
    # plinth + floor bands (shadow lines) + cornice
    for (o, f) in oct_outside(body).items():
        bp.set(o[0], 1, o[1], ESB)
        bp.set(o[0], 2, o[1], stair(ESB_ST, f))
        for fy in F[1:4]:
            bp.set(o[0], fy, o[1], stair(VB_ST, f, "top"))
            bp.set(o[0], fy + 1, o[1], slab(PUR_SL))
        bp.set(o[0], F[4] - 1, o[1], stair(VB_ST, f, "top"))
        bp.set(o[0], F[4], o[1], VB)
    for (o, f) in oct_outside(octagon(A + 1, B + 1)).items():
        bp.set(o[0], F[4], o[1], stair(VB_ST, f, "top"))
    # corner piers at the eight vertices, rising into pinnacles above the roof walk
    verts = [(A, 4), (4, A), (-4, A), (-A, 4), (-A, -4), (-4, -A), (4, -A), (A, -4)]
    for (vx, vz) in verts:
        ox, oz = vx + (1 if vx > 0 else -1) * (abs(vx) == A), vz + (1 if vz > 0 else -1) * (abs(vz) == A)
        for y in range(1, F[4] + 1):
            bp.set(ox, y, oz, PUR_P)
            bp.set(vx, y, vz, PUR_P)
        bp.set(ox, F[4] + 1, oz, PUR)
        bp.set(ox, F[4] + 2, oz, PUR_P)
        bp.set(ox, F[4] + 3, oz, STAR)
        bp.set(ox, F[4] + 4, oz, ROD_UP)
    # windows: tall lancets with a glowing mullion on the cardinal faces, glass on the diagonals
    for fy in F[:4]:
        wy0, wy1 = fy + 3, fy + 8
        for (fx, fz, ux, uz) in ((0, A, 1, 0), (0, -A, 1, 0), (A, 0, 0, 1), (-A, 0, 0, 1)):
            nx, nz = (fx > 0) - (fx < 0), (fz > 0) - (fz < 0)
            for u in (-2, -1, 0, 1, 2):
                x, z = fx + ux * u, fz + uz * u
                for y in range(wy0, wy1 + 1):
                    bp.set(x, y, z, PUR_P if u == 0 else "purple_stained_glass_pane")
                bp.set(x, wy1 + 1, z, PUR)
                bp.set(x + nx, wy0 - 1, z + nz, slab(ESB_SL, "top"))
            bp.set(fx, (wy0 + wy1) // 2, fz, STAR)
            for u, f in ((-2, None), (2, None)):
                x, z = fx + ux * u, fz + uz * u
                side = face_vec(ux * (1 if u < 0 else -1), uz * (1 if u < 0 else -1))
                bp.set(x, wy1, z, stair(PUR_ST, side, "top"))
            bp.set(fx, wy1 + 2, fz, STAR)
            for u in (-1, 1):
                bp.set(fx + ux * u + nx, wy1 + 2, fz + uz * u + nz, stair(PUR_ST, face_vec(-nx, -nz), "top"))
            bp.set(fx + nx, wy1 + 2, fz + nz, stair(PUR_ST, face_vec(-nx, -nz), "top"))
        for sx in (-1, 1):
            for sz in (-1, 1):
                for (x, z) in ((7 * sx, 7 * sz), (8 * sx, 6 * sz), (6 * sx, 8 * sz)):
                    for y in range(wy0 + 1, wy1):
                        bp.set(x, y, z, "magenta_stained_glass")
                bp.set(7 * sx, wy1, 7 * sz, STAR)
    # floors with the central well
    for fy in F[1:5]:
        for (x, z) in inner:
            d = math.hypot(x, z)
            if d > 3.9:
                bp.set(x, fy, z, ESB if d < 4.7 else (PUR if (x + z) % 2 else VB))
    # central column (starlight core) and the spiral stair through every hall
    for y in range(1, F[4] + 1):
        for (x, z) in disk_pts(0, 0, 1):
            bp.set(x, y, z, STAR if (y % 11 == 6 and (x, z) != (0, 0)) else PUR_P)
    helix(bp, 0, 0, 1, F[4] + 1, 1.6, 3.6, 11.0, a0=math.pi / 2)
    for fy in F[1:5]:
        for (x, z) in ring_pts(0, 0, 4.6, 3.6):
            frac = (math.atan2(z, x) - math.pi / 2) % (2 * math.pi) / (2 * math.pi)
            if frac > 0.16:
                bp.set(x, fy + 1, z, ESB_WA)

    # --- entrance portal (south) with a porch, steps, the waystone and braziers
    for x in range(-2, 3):
        for y in range(1, 7):
            for z in (A - 1, A, A + 1):
                bp.set(x, y, z, "air")
    for x in (-3, 3):
        for z in (A + 1, A + 2):
            bp.fill(x, 1, z, x, 9, z, PUR_P)
        bp.set(x, 10, A + 2, STAR)
    for x in range(-3, 4):
        bp.set(x, 7, A + 1, VB)
        bp.set(x, 8, A + 1, VB)
        bp.set(x, 7, A + 2, PUR)
        bp.set(x, 8, A + 2, stair(PUR_ST, "south"))
    for (x, f) in ((-2, "east"), (2, "west")):
        bp.set(x, 6, A + 1, stair(PUR_ST, f, "top"))
        bp.set(x, 6, A, stair(PUR_ST, f, "top"))
    bp.set(0, 9, A + 2, PUR)
    bp.set(0, 10, A + 2, "dragon_head[powered=false,rotation=0]")
    for x in range(-2, 3):
        bp.set(x, 0, A + 1, ESB)
        bp.set(x, 0, A + 2, ESB)
    bp.set(0, 1, 16, MOD["waystone"])
    for (x, z) in ring_pts(0, 16, 2.2, 1):
        bp.set(x, 0, z, PUR)
    for x in (-5, 5):
        brazier(bp, x, 1, 15, h=3)

    # --- flying buttresses: four piers on the plaza, three on satellite rocks
    pal = void_pal(17)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        px, pz = round(math.cos(a) * 16), round(math.sin(a) * 16)
        pier(bp, px, pz, 1, 24, pal, spire=7)
        flying_buttress(bp, (round(math.cos(a) * 14.6), 23, round(math.sin(a) * 14.6)),
                        (round(math.cos(a) * 9.6), 29, round(math.sin(a) * 9.6)), thick=5)
    for (sx, sz, ang, cols) in sats:
        pier(bp, sx, sz, 9, 31, pal, spire=10)
        for (o, f) in oct_outside({(sx + dx, sz + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)}).items():
            bp.set(o[0], 9, o[1], stair(ESB_ST, f))
        wx, wz = round(math.cos(ang) * 11), round(math.sin(ang) * 11)
        flying_buttress(bp, (sx - round(math.cos(ang) * 1.5), 30, sz - round(math.sin(ang) * 1.5)), (wx, 42, wz),
                        thick=10)
        chorus_patch(bp, cols, [(sx + rng.randint(-5, 5), sz + rng.randint(-5, 5)) for _ in range(6)], rng, 3, 5)
        star_lamp(bp, sx + 3, 9, sz + 1, h=1)

    # --- roof walk, upper drum and the dragon-crowned dome
    roof = octagon(A, B)
    for (x, z) in roof:
        bp.set(x, F[4], z, VB)
    for (x, z) in oct_edge(roof):
        bp.set(x, F[4] + 1, z, ESB_WA)
    drum = octagon(7, 10)
    dedge = oct_edge(drum)
    D0, D1 = F[4] + 1, F[4] + 9
    for (x, z) in drum:
        for y in range(D0, D1 + 1):
            bp.set(x, y, z, wall.pick(x, y, z) if (x, z) in dedge else "air")
    for (o, f) in oct_outside(drum).items():
        bp.set(o[0], D0, o[1], stair(ESB_ST, f))
        bp.set(o[0], D1, o[1], stair(PUR_ST, f, "top"))
    for (vx, vz) in ((7, 3), (3, 7), (-3, 7), (-7, 3), (-7, -3), (-3, -7), (3, -7), (7, -3)):
        bp.fill(vx, D0, vz, vx, D1, vz, PUR_P)
    for (fx, fz, ux, uz) in ((0, 7, 1, 0), (0, -7, 1, 0), (7, 0, 0, 1), (-7, 0, 0, 1)):
        for u in (-1, 0, 1):
            for y in range(D0 + 2, D1 - 1):
                bp.set(fx + ux * u, y, fz + uz * u, "magenta_stained_glass_pane")
        nx, nz = (fx > 0) - (fx < 0), (fz > 0) - (fz < 0)
        bp.set(fx + nx, D1 - 1, fz + nz, f"dragon_wall_head[facing={face_vec(nx, nz)},powered=false]")
    for z in (6, 7):  # doorway from the dome chamber onto the roof walk
        bp.fill(0, D0, z, 0, D0 + 1, z, "air")
    dc = D1
    DR = 7
    for x in range(-DR - 1, DR + 2):
        for y in range(dc, dc + DR + 2):
            for z in range(-DR - 1, DR + 2):
                d = math.sqrt(x * x + ((y - dc) * 1.1) ** 2 + z * z)
                if DR - 0.6 < d <= DR + 0.45:
                    bp.set(x, y, z, PUR)
                elif d <= DR - 0.6 and y > dc:
                    bp.set(x, y, z, "air")
    for k in range(8):
        a = 2 * math.pi * k / 8
        for t in range(0, 91, 3):
            tt = math.radians(t)
            x = round(math.cos(a) * math.cos(tt) * (DR + 0.6))
            z = round(math.sin(a) * math.cos(tt) * (DR + 0.6))
            bp.set(x, dc + round(math.sin(tt) * (DR + 0.6) / 1.1), z, VB)
    for k in range(8):  # small dormer lights between the ribs
        a = 2 * math.pi * (k + 0.5) / 8
        bp.set(round(math.cos(a) * 6.3), dc + 3, round(math.sin(a) * 6.3), STAR)
    ltop = dc + int(DR / 1.1) + 1
    for (x, z) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        bp.fill(x, ltop, z, x, ltop + 2, z, PUR_P)
    bp.fill(0, ltop - 1, 0, 0, ltop + 2, 0, STAR)
    for (x, z) in octagon(2, 3):
        bp.set(x, ltop + 3, z, PUR if max(abs(x), abs(z)) < 2 else slab(PUR_SL))
    bp.set(0, ltop + 4, 0, PUR)
    bp.set(0, ltop + 5, 0, "dragon_head[powered=false,rotation=0]")
    for (x, z, f) in ((2, 0, "east"), (-2, 0, "west"), (0, 2, "south"), (0, -2, "north")):
        bp.set(x, ltop + 1, z, f"dragon_wall_head[facing={f},powered=false]")
    for (x, z) in ((1, 0), (-1, 0), (0, -1)):
        bp.set(x, ltop + 4, z, ROD_UP)

    # --- interiors
    stacks = [math.pi / 8 + k * math.pi / 4 for k in range(8)]
    for i, fy in enumerate(F[:4]):
        # wall shelving under the windows and radial book stacks
        for (x, z) in oct_edge(inner):
            if not (i == 0 and abs(x) <= 2 and z > 0):
                bp.fill(x, fy + 1, z, x, fy + 2, z, "bookshelf")
        for a in stacks:
            if adiff(a, math.pi / 2 + 0.5) < 0.6 or (i == 0 and adiff(a, math.pi / 2) < 0.6):
                continue
            for r in (5.5, 6.5, 7.5):
                x, z = round(math.cos(a) * r), round(math.sin(a) * r)
                bp.fill(x, fy + 1, z, x, fy + 3, z, "bookshelf" if rng.random() > 0.1 else "chiseled_bookshelf[facing=north]")
            x, z = round(math.cos(a) * 5.5), round(math.sin(a) * 5.5)
            bp.set(x, fy + 4, z, "candle[candles=3,lit=true,waterlogged=false]")
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            hang_star(bp, round(math.cos(a) * 6), fy + 10, round(math.sin(a) * 6), 2, FROG)
        for (x, z) in ((5, 0), (-5, 0), (0, -5)):
            bp.set(x, fy + 1, z, "lectern[facing=" + face_in(x, z, 0, 0) + ",has_book=false,powered=false]")
    # hall 1: catalogue room
    bp.set(-6, 1, 3, "cartography_table")
    bp.set(6, 1, 3, "enchanting_table")
    # hall 2: the stacks (endermites in the shelves)
    bp.spawner(6, F[1] + 1, -3, "minecraft:endermite")
    bp.chest(-6, F[1] + 1, 3, "east", LOOT + "end_archive")
    # hall 3: the forbidden shelves, guarded
    bp.spawner(-6, F[2] + 1, -3, MOB["void_stalker"])
    bp.set(6, F[2] + 1, 3, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    # hall 4: scriptorium
    bp.set(0, F[3] + 1, -6, "enchanting_table")
    for (x, z) in ((6, 3), (-6, 3), (6, -3)):
        bp.set(x, F[3] + 1, z, "lectern[facing=" + face_in(x, z, 0, 0) + ",has_book=false,powered=false]")
    # dome chamber: the archivist's treasure under the starlit dome
    bp.chest(0, F[4] + 1, -5, "south", LOOT + "end_archive_top")
    for (x, z) in ((-4, -3), (4, -3), (-4, 3), (4, 3)):
        bp.set(x, F[4] + 1, z, "bookshelf")
        bp.set(x, F[4] + 2, z, "candle[candles=4,lit=true,waterlogged=false]")
    hang_star(bp, 0, ltop - 2, 0, 3, STAR)

    # --- secret: a bookshelf in hall 1 hides a ladder down to the sealed vault in the rock
    bp.fill(0, -8, -A + 1, 0, 2, -A + 1, "air")
    bp.set(0, 1, -A + 1, "bookshelf")
    bp.set(0, 2, -A + 1, "bookshelf")
    bp.ladder(0, -8, -A + 1, 0, "south")
    bp.clear(-4, -8, -8, 4, -4, -3)
    bp.fill(-5, -9, -9, 5, -9, -2, VB)
    bp.fill(-4, -9, -8, 4, -9, -3, "obsidian")
    bp.chest(-3, -8, -4, "north", LOOT + "end_archive")
    bp.bookshelf_wall(-4, -8, -8, -1, -6, -8)
    bp.bookshelf_wall(1, -8, -8, 4, -6, -8)
    bp.spawner(3, -8, -4, MOB["void_stalker"])
    hang_star(bp, 0, -4, -5, 1, STAR)

    # --- chorus on the rim
    rim = [p for p in main if p not in plaza and bp.get(p[0], main[p][1], p[1]) == "minecraft:end_stone"]
    rng.shuffle(rim)
    chorus_patch(bp, main, rim[:18], rng, 3, 6)
    # reading tables, lecterns and stacks of forbidden books in every gallery
    INT.decorate(bp, dict(INT.THEMES["library"], wood="warped", ceiling="end_rod", rugs=["purple", "magenta", "black"],
                          shelf_items=["book", "enchanted_book", "ender_pearl", "paper", "ender_eye"],
                          banners=["purple", "magenta", "black"]), seed=1)


register(StructureDef(
    "end_archive", "end", OUTER_END, [Piece("archive", end_archive)],
    spacing=22, separation=7, adaptation="none", height=("uniform", 50, 70), processors="aging",
    title_fr="Archive de l'End", title_en="End Archive",
    spawns=[("brasshaven:void_stalker", 10, 1, 2), ("brasshaven:rift_sentinel", 5, 1, 1)],
    creatures=[("rift_sentinel", 2)]))


# ================================================================== Void ship wreck
SHIP_L = 58
DECK = 8


def _half_beam(z):
    u = z / (SHIP_L - 1)
    if u < 0.12:
        return 5.0 + (u / 0.12) * 1.8
    if u < 0.55:
        return 6.8
    return 6.8 * math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2))


def _keel(z):
    u = z / (SHIP_L - 1)
    if u < 0.12:
        return (0.12 - u) / 0.12 * 3
    if u > 0.72:
        return ((u - 0.72) / 0.28) ** 1.6 * 7
    return 0.0


def sail(m, x0, x1, y0, y1, z, billow=2.0, torn=0, holes=()):
    """A continuous two-layer sail hanging under a yard at y1 + 1: billows toward +z, magenta with
    purple vertical stripes. `torn` cuts the lower corners diagonally; `holes` are clean (x, y)
    2x2 rips."""
    rip = {(hx + dx, hy + dy) for hx, hy in holes for dx in (0, 1) for dy in (0, 1)}
    for x in range(x0, x1 + 1):
        u = (x - x0) / max(1, x1 - x0)
        cut = max(0, torn - min(x - x0, x1 - x))
        for y in range(y0 + cut, y1 + 1):
            if (x, y) in rip:
                continue
            v = (y - y0) / max(1, y1 - y0)
            dz = round(billow * math.sin(math.pi * u) ** 0.7 * math.sin(math.pi * (0.2 + 0.8 * v)) ** 0.6)
            wool = "purple_wool" if (x - x0) % 4 == 2 else "magenta_wool"
            m.set(x, y, z + dz, wool)
            m.set(x, y, z + dz + 1, wool)


def ship_model(rng):
    """The intact-ish End ship in local coordinates: bow toward +z, keel at y 0, deck at y DECK."""
    m = Blueprint("void_ship_local")
    inside = set()
    for z in range(SHIP_L):
        b, k = _half_beam(z), _keel(z)
        for y in range(int(round(k)), DECK + 1):
            f = (y - k + 0.5) / (DECK - k + 0.5)
            w = b * (0.35 + 0.65 * min(1.0, max(0.0, f)) ** 0.55)
            for x in range(-int(w + 0.3), int(w + 0.3) + 1):
                inside.add((x, y, z))
    for (x, y, z) in inside:
        shell = any((x + dx, y + dy, z + dz) not in inside
                    for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
        if y == DECK:
            edge = (x + 1, y, z) not in inside or (x - 1, y, z) not in inside
            m.set(x, y, z, VB if edge else "purpur_pillar[axis=z]")
        elif shell:  # plank bands: void-brick bottom, purpur strake, purpur sides, dark wale
            m.set(x, y, z, VB if y <= 3 or y == DECK - 1 else "purpur_pillar[axis=z]" if y == 4 else PUR)
        else:
            m.set(x, y, z, "air")
        if y == 3 and not shell:
            m.set(x, y, z, "purpur_pillar[axis=z]" if x % 2 else PUR)
    # bulwarks: purpur rail with a slab cap, end-rod lanterns, portholes
    for z in range(SHIP_L):
        row = [x for (x, y, zz) in inside if y == DECK and zz == z]
        if not row:
            continue
        for x in (min(row), max(row)):
            m.set(x, DECK + 1, z, PUR)
            m.set(x, DECK + 2, z, slab(PUR_SL))
            if z % 6 == 3:
                m.set(x, DECK + 3, z, ROD_UP)
            if z % 4 == 1 and 4 < z < 50:
                m.set(x, 6, z, STAR if z % 8 == 5 else "magenta_stained_glass")
        for x, f in ((min(row) - 1, "east"), (max(row) + 1, "west")):  # gunwale cap + rubbing strake
            m.set(x, DECK + 1, z, stair(VB_ST, f, "top"))
            if z > 2:
                m.set(x, 4, z, stair(VB_ST, f, "top"))
    # stern castle (captain's cabin) z 0..11, poop deck at DECK + 5
    P = DECK + 5
    for z in range(0, 12):
        row = [x for (x, y, zz) in inside if y == DECK and zz == z]
        lo, hi = min(row), max(row)
        for x in range(lo, hi + 1):
            for y in range(DECK + 1, P):
                wall = x in (lo, hi) or z in (0, 11)
                m.set(x, y, z, (VB if y == DECK + 1 else PUR) if wall else "air")
            m.set(x, P, z, "purpur_pillar[axis=z]" if x % 3 else PUR)
        for x in (lo - 1, hi + 1):
            m.set(x, P, z, stair(VB_ST, "east" if x < lo else "west", "top"))
        for x in (lo, hi):
            m.set(x, P + 1, z, VB_WA)
    for x in range(-4, 5):  # stern gallery windows
        for y in (DECK + 2, DECK + 3):
            m.set(x, y, 0, "magenta_stained_glass_pane" if x % 3 else PUR_P)
        m.set(x, DECK + 4, -1, stair(PUR_ST, "south", "top"))
        m.set(x, P + 1, 0, VB_WA)
    for x in range(-3, 4):
        m.set(x, 6, 0, STAR if x % 2 else "magenta_stained_glass")
    for x in range(-5, 6):
        m.set(x, P + 1, 11, VB_WA)
    m.set(0, DECK + 1, 11, "air")
    m.set(0, DECK + 2, 11, "air")
    for x in (-4, 4):
        star_lamp(m, x, P + 1, 1, h=2)
    # forecastle z 47..53, raised to DECK + 3
    Fq = DECK + 3
    for z in range(46, 54):
        row = [x for (x, y, zz) in inside if y == DECK and zz == z]
        if not row:
            continue
        lo, hi = min(row), max(row)
        for x in range(lo, hi + 1):
            for y in range(DECK + 1, Fq):
                m.set(x, y, z, (PUR if (x in (lo, hi) or z == 46) else "air"))
            m.set(x, Fq, z, PUR)
        for x in (lo, hi):
            m.set(x, Fq + 1, z, VB_WA)
    m.set(0, DECK + 1, 46, "air")
    m.set(0, DECK + 2, 46, "air")
    # masts, yards and torn magenta sails
    def mast(z, y0, y1):
        for y in range(y0, y1 + 1):
            m.set(0, y, z, PUR_P)
        m.set(0, DECK + 1, z, PUR)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m.set(dx, DECK + 1, z + dz, stair(PUR_ST, face_vec(-dx, -dz)))

    def yard(z, y, hw):
        for x in range(-hw, hw + 1):
            m.set(x, y, z, "purpur_pillar[axis=x]")
        m.set(-hw - 1, y, z, ROD_UP.replace("up", "west"))
        m.set(hw + 1, y, z, ROD_UP.replace("up", "east"))

    mast(26, 3, 44)                           # main mast, intact
    yard(26, 23, 10)
    yard(26, 32, 8)
    yard(26, 40, 5)
    sail(m, -9, 9, 13, 22, 27, 3.0, torn=2, holes=((-5, 15), (4, 18)))
    sail(m, -7, 7, 25, 31, 27, 2.0, torn=1)
    sail(m, -4, 4, 34, 39, 27, 1.0)
    m.set(0, 45, 26, STAR)
    m.set(0, 46, 26, ROD_UP)
    mast(8, P, P + 14)                        # mizzen, snapped
    yard(8, P + 9, 5)
    sail(m, -4, 4, P + 3, P + 8, 9, 1.5, torn=2, holes=((1, P + 4),))
    for y in range(P + 12, P + 15):
        if rng.random() < 0.5:
            m.set(0, y, 8, "air")
    mast(40, 3, 27)                           # fore mast, broken: its top lies across the deck
    m.set(0, 27, 40, "air")
    m.set(0, 26, 40, slab(PUR_SL))
    yard(40, 21, 8)
    sail(m, -7, 7, 12, 20, 41, 2.5, torn=3, holes=((-3, 15), (2, 13)))
    m.line((1, DECK + 1, 42), (-14, DECK - 4, 50), "purpur_pillar[axis=x]")
    for k in (-3, -2, -1, 1, 2, 3):  # its tangled yard and a draped sail
        m.set(-7 + k, DECK - 1, 46 + (k // 2), "purpur_pillar[axis=z]")
    for x in range(-12, -5):
        drop = (x < -9) + (x < -11)
        for z in range(47, 51):
            if rng.random() < 0.7:
                m.set(x, DECK - 1 - drop, z, "magenta_wool")
    # bowsprit + dragon figurehead
    m.line((0, DECK + 3, SHIP_L - 4), (0, DECK + 9, SHIP_L + 7), "purpur_pillar[axis=z]")
    m.set(0, DECK + 10, SHIP_L + 7, "dragon_head[powered=false,rotation=0]")
    hz, hy = SHIP_L + 3, DECK + 1
    tube(m, (0.0, hy - 9.0, SHIP_L - 3.0), (0, 0.8, 0.6), 11.0, 1.9, 1.4, VB)
    for x in range(-2, 3):               # skull
        for z in range(0, 5):
            for y in range(1, 5):
                if not (abs(x) == 2 and (y == 4 or z in (0, 4))):
                    m.set(x, hy + y, hz + z, VB)
    for x in (-1, 0, 1):                 # snout, open jaws
        for z in range(5, 9):
            m.set(x, hy + 1, hz + z, VB)
            m.set(x, hy + 2, hz + z, VB if z < 7 else stair(VB_ST, "north"))
            m.set(x, hy + 3, hz + z, stair(VB_ST, "north") if z < 7 else "air")
        for z in range(1, 9):
            m.set(x, hy - 1, hz + z, slab(VB_SL, "top"))
            m.set(x, hy, hz + z, "air")
    m.set(0, hy, hz + 1, STAR)           # glowing throat
    for x in (-1, 1):
        m.set(x, hy, hz + 8, ROD_DOWN)       # fangs
        m.set(x, hy, hz + 5, ROD_DOWN)
    for x in (-2, 2):
        m.set(x, hy + 3, hz + 3, STAR)       # eyes
        m.line((x, hy + 5, hz + 1), (x + (x // 2), hy + 8, hz - 3), VB_WA)
        m.set(x + (x // 2), hy + 9, hz - 3, ROD_UP)
    for k in range(7):
        m.set(0, hy + 5 - (k + 1) // 2, hz - k, VB_WA)    # crest down the neck
    # deck clutter: crates and shulker cargo along the rails, a capstan, lamp posts
    for z in (16, 19, 34, 37):
        for x in (-5, 5):
            m.barrel(x, DECK + 1, z, "up")
            if z % 2:
                m.set(x, DECK + 2, z, "magenta_shulker_box[facing=up]")
    m.set(0, DECK + 1, 18, "waxed_cut_copper")
    m.set(0, DECK + 2, 18, slab("waxed_cut_copper_slab"))
    for (x, z) in ((-3, 14), (3, 14), (-3, 44), (3, 38)):
        star_lamp(m, x, DECK + 1, z, h=1, post=VB_WA)
    # interiors: captain's cabin
    m.bed(-3, DECK + 1, 2, "south", "magenta")
    m.chest(3, DECK + 1, 2, "west", LOOT + "void_ship")
    m.set(3, DECK + 1, 5, "lectern[facing=west,has_book=false,powered=false]")
    m.set(-3, DECK + 1, 7, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
    m.set(0, DECK + 1, 4, "cartography_table")
    hang_star(m, 0, P - 1, 6, 1, FROG)
    # the hold: cargo, the second chest and the guardian spawner
    for z in range(31, 40, 2):
        for x in (-4, 4):
            m.barrel(x, 4, z, "up")
            if rng.random() < 0.6:
                m.set(x, 5, z, "magenta_shulker_box[facing=up]" if rng.random() < 0.5 else "barrel[facing=up,open=false]")
    m.chest(3, 4, 22, "west", LOOT + "void_ship")
    m.spawner(0, 4, 20, MOB["void_stalker"])
    for z in (18, 34):
        hang_star(m, 0, 7, z, 1, FROG)
    for x in (-1, 0, 1):  # hatch down to the hold
        for z in range(28, 33):
            m.set(x, DECK, z, "air")
        for k, z in enumerate(range(29, 33)):
            m.set(x, 4 + k, z, stair(PUR_ST, "south"))
            for y in range(3, 4 + k):
                m.set(x, y, z, PUR)
    # wreck damage: a breach low on the port side (cargo spills out), holes in the deck
    for z in range(30, 38):
        for y in range(1, 6):
            if abs(z - 34) + abs(y - 3) * 1.4 < 4.5 + rng.uniform(-0.8, 0.8):
                for x in range(-8, -3):
                    if m.get(x, y, z) and m.get(x, y, z) != "minecraft:air" and x < -3:
                        m.set(x, y, z, "air")
    for (x, z) in ((3, 44), (2, 45), (4, 43), (-2, 15), (-3, 16)):
        m.set(x, DECK, z, "air")
    return m


def void_ship(bp):
    rng = random.Random(41)
    m = ship_model(rng)
    roll, pitch = math.radians(6), math.radians(8)
    cr, sr, cp, sp = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch)
    piv = (0.0, 4.0, 29.0)

    def fwd(x, y, z):
        x, y, z = x - piv[0], y - piv[1], z - piv[2]
        x, y = x * cr - y * sr, x * sr + y * cr           # roll to port
        y, z = y * cp - z * sp, y * sp + z * cp           # pitch nose-down
        return x + piv[0], y + piv[1], z + piv[2]

    def inv(x, y, z):
        x, y, z = x - piv[0], y - piv[1], z - piv[2]
        y, z = y * cp + z * sp, -y * sp + z * cp
        x, y = x * cr + y * sr, -x * sr + y * cr
        return x + piv[0], y + piv[1], z + piv[2]

    (mx, my, mz), (Mx, My, Mz) = m.bounds()
    corners = [fwd(x, y, z) for x in (mx, Mx) for y in (my, My) for z in (mz, Mz)]
    lo = [math.floor(min(c[j] for c in corners)) - 1 for j in range(3)]
    hi = [math.ceil(max(c[j] for c in corners)) + 1 for j in range(3)]
    for X in range(lo[0], hi[0] + 1):
        for Y in range(lo[1], hi[1] + 1):
            for Z in range(lo[2], hi[2] + 1):
                lx, ly, lz = inv(X, Y, Z)
                b = m.blocks.get((round(lx), round(ly), round(lz)))
                if b:
                    bp.blocks[(X, Y, Z)] = b
    # forward pass: thin sheets (sails, rails) keep every block, no resampling holes
    for (x, y, z), b in m.blocks.items():
        if b[0] != "minecraft:air":
            X, Y, Z = (round(c) for c in fwd(x, y, z))
            if (X, Y, Z) not in bp.blocks:
                bp.blocks[(X, Y, Z)] = b

    # --- the rock the ship ploughed into (it fills around the hull, never inside it)
    cols = merge_cols(rock_lobe(-3, 2, 31, 17, 15, 17, 401, spikes=9),
                      rock_lobe(9, 0, 22, 8, 7, 10, 402, spikes=2),
                      rock_lobe(-12, 0, 40, 7, 6, 9, 404, spikes=2))
    build_rock(bp, cols, 403, keep=True)
    # ploughed mounds and scattered debris along the furrow
    for (x, z) in cols:
        t = cols[(x, z)][1]
        if 3.5 < abs(x - 0.5 + (z - 30) * 0.05) < 10 and 16 < z < 44 and rng.random() < 0.55:
            h = 1 + (rng.random() < 0.4)
            for k in range(1, h + 1):
                bp.set(x, t + k, z, "end_stone", keep=True)
    spill = [(-10, 33), (-11, 35), (-12, 32), (-9, 37), (-13, 36), (-11, 39), (-14, 34), (-8, 30)]
    for i, (x, z) in enumerate(spill):
        if (x, z) not in cols:
            continue
        t = cols[(x, z)][1]
        while bp.get(x, t + 1, z) and t < 12:
            t += 1
        item = ["barrel[facing=up,open=false]", "magenta_shulker_box[facing=up]", "barrel[facing=east,open=false]",
                PUR, "purple_shulker_box[facing=up]", "barrel[facing=up,open=false]", ROD_UP, "magenta_wool"][i]
        bp.set(x, t + 1, z, item)
    bp.chest(-12, cols.get((-12, 37), (0, 2))[1] + 1, 37, "east", LOOT + "void_ship")
    for (x, z) in ((-15, 30), (-6, 46), (8, 45), (6, 31), (-16, 41)):
        if (x, z) in cols:
            t = cols[(x, z)][1]
            if not bp.get(x, t + 1, z):
                star_lamp(bp, x, t + 1, z, h=1, post=VB_WA)
    rim = [p for p in cols if abs(p[0]) > 8]
    rng.shuffle(rim)
    chorus_patch(bp, cols, rim[:16], rng, 3, 6)
    # below decks: cargo, bunks and the crew's long-abandoned clutter
    INT.decorate(bp, dict(INT.THEMES["end"], floor={"crates": 3, "barrel": 2, "shulker": 2, "bed": 2, "end_rod": 1}),
                 seed=1, loot=LOOT + "void_ship")


register(StructureDef(
    "void_ship", "end", OUTER_END, [Piece("ship", void_ship)],
    spacing=24, separation=8, adaptation="none", height=("uniform", 55, 80), processors="none",
    spawns=[("brasshaven:rift_sentinel", 5, 1, 1), ("minecraft:enderman", 8, 1, 2)], creatures=[("rift_sentinel", 2)],
    title_fr="Épave du vide", title_en="Void Ship Wreck"))


# ================================================================== Void Warden's nest (End mini-boss lair)
def claw(bp, a, r0, h, reach, base_r, body="obsidian", vein="crying_obsidian"):
    """Colossal curved claw rooted at angle a, radius r0: rises, bows outward, then hooks over the
    arena. A smooth solid obsidian body tapering to a point, a continuous crying-obsidian vein along
    its inner edge (studded with starlight) and an end-rod tip."""
    n = int(h * 8)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 + 2.0 * math.sin(math.pi * t * 0.7) - reach * t ** 1.9
        y = h * math.sin(t * math.pi / 2) ** 1.1
        rr = 0.75 + (base_r - 0.75) * (1 - t) ** 1.2
        pts.append((ca * r, y, sa * r, rr, t))
    for (px, py, pz, rr, t) in pts:
        R = int(rr) + 1
        for x in range(round(px) - R, round(px) + R + 1):
            for y in range(round(py) - R, round(py) + R + 1):
                for z in range(round(pz) - R, round(pz) + R + 1):
                    if (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= rr * rr:
                        bp.set(x, y, z, body)
    # the vein: the arena-facing surface line (the curve's inner side, i.e. toward the axis and down)
    for i, (px, py, pz, rr, t) in enumerate(pts[:-1]):
        nx, ny, nz = pts[i + 1][0] - px, pts[i + 1][1] - py, pts[i + 1][2] - pz
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        # inward normal: radial-in vector made perpendicular to the tangent
        ix, iy, iz = -ca, 0.0, -sa
        dot = (ix * nx + iy * ny + iz * nz) / ln
        ix, iy, iz = ix - dot * nx / ln, iy - dot * ny / ln, iz - dot * nz / ln
        il = math.sqrt(ix * ix + iy * iy + iz * iz) or 1
        q = (round(px + ix / il * (rr - 0.3)), round(py + iy / il * (rr - 0.3)), round(pz + iz / il * (rr - 0.3)))
        bp.set(*q, STAR if t > 0.1 and i % 40 == 20 else vein)
    px, py, pz, _, _ = pts[-1]
    bp.set(round(px), round(py) - 1, round(pz), ROD_DOWN)
    return pts


def void_nest(bp):
    rng = random.Random(53)
    AR = 17                       # arena radius (kept clear for the fight)
    # --- rocks: the lair rock (dark, heavy) and the approach islet to the south
    main = rock_lobe(0, -1, 0, 27, 26, 28, 501, spikes=11)
    build_rock(bp, main, 502, deco=1.3)
    app = rock(bp, 0, -2, 41, 7, 6, 12, 503, spikes=3, deco=1.2)

    # --- arena floor: void bricks with purpur and end-stone rings, obsidian spokes, starlight studs
    for (x, z) in disk_pts(0, 0, AR):
        d = math.hypot(x, z)
        a = math.atan2(z, x)
        blk = VB
        if 5.5 < d <= 6.6 or AR - 0.6 < d:
            blk = PUR if d < 7 else "crying_obsidian"
        elif 11.5 < d <= 12.6:
            blk = ESB
        elif d > 7 and min(adiff(a, k * math.pi / 4) for k in range(8)) * d < 0.6:
            blk = STAR if round(d) % 4 == 0 else "obsidian"
        bp.set(x, 0, z, blk)
        for y in range(1, 5):
            bp.set(x, y, z, "air")
    # rim: a raised ring with a stepped inner edge
    for (x, z) in disk_pts(0, 0, AR + 6):
        d = math.hypot(x, z)
        if AR + 0.4 < d:
            bp.set(x, 0, z, VB)
            bp.set(x, 1, z, ESB if d < AR + 3.5 else VB if d < AR + 5.5 else "obsidian")
    for (x, z) in ring_pts(0, 0, AR + 1):
        bp.set(x, 1, z, stair(VB_ST, OPPOSITE[face_in(x, z, 0, 0)]))

    # --- the dais at the centre (the boss seal is set by lair_void_warden)
    for (x, z) in disk_pts(0, 0, 2):
        bp.set(x, 1, z, PUR)
    for (x, z) in ring_pts(0, 0, 3):
        bp.set(x, 1, z, stair(PUR_ST, face_in(x, z, 0, 0)))
    for (x, z) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        bp.set(x, 2, z, ROD_UP)
    # a floating halo of crying obsidian high above the altar
    ring3d(bp, (0, 27, 0), 6, (1, 0, 0), (0, 0, 1), "crying_obsidian")
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, z = round(math.cos(a) * 6), round(math.sin(a) * 6)
        bp.set(x, 26, z, ROD_DOWN if k % 2 else STAR)
    bp.set(0, 27, 0, STAR)
    for (x, z) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(x, 27, z, f"end_rod[facing={face_vec(x, z)}]")
    bp.set(0, 26, 0, ROD_DOWN)

    # --- the ring of colossal claws (taller behind the altar, in the north)
    n = 10
    for k in range(n):
        a = 2 * math.pi * k / n
        north = max(0.0, -math.sin(a))
        claw(bp, a, AR + 5, 26 + 10 * north, 15 + 2 * north, 2.2 + 0.4 * north)
        cx, cz = round(math.cos(a) * (AR + 5)), round(math.sin(a) * (AR + 5))
        for (x, z) in ring_pts(cx, cz, 4):  # a clean sloped collar where each claw grips the rock
            if math.hypot(x, z) > AR + 1.5:
                bp.set(x, 2, z, stair(VB_ST, face_in(x, z, cx, cz)))
    # starlight braziers between the claws
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        if adiff(a, math.pi / 2) < 0.2 or adiff(a, -math.pi / 2) < 0.2:
            continue
        x, z = round(math.cos(a) * (AR + 3)), round(math.sin(a) * (AR + 3))
        brazier(bp, x, 2, z, h=2, body=VB, bowl=VB_ST)

    # --- the hoard behind the altar (north): a raised dais between the two great claws
    for (x, z) in disk_pts(0, -(AR + 4), 3.5):
        bp.set(x, 1, z, VB)
        bp.set(x, 2, z, PUR if math.hypot(x, z + AR + 4) < 2.5 else VB)
    for (x, z) in ring_pts(0, -(AR + 4), 4.5):
        if bp.get(x, 1, z) != "minecraft:air":
            bp.set(x, 2, z, stair(VB_ST, face_in(x, z, 0, -(AR + 4))))
    for (x, z) in ((-2, -(AR + 6)), (0, -(AR + 7)), (2, -(AR + 6))):
        bp.chest(x, 3, z, "south", LOOT + "void_nest")
    for (x, z, b) in ((-3, -(AR + 4), "raw_gold_block"), (3, -(AR + 4), "amethyst_block"),
                      (-1, -(AR + 5), "gold_block"), (1, -(AR + 5), "amethyst_cluster[facing=up,waterlogged=false]"),
                      (-3, -(AR + 3), "amethyst_cluster[facing=up,waterlogged=false]"),
                      (3, -(AR + 3), "dragon_head[powered=false,rotation=0]")):
        bp.set(x, 3, z, b)
    bp.set(0, 3, -(AR + 4), "crying_obsidian")
    bp.set(0, 4, -(AR + 4), "amethyst_cluster[facing=up,waterlogged=false]")

    # --- the approach: a causeway from the southern islet through a gate of two fangs
    bridge(bp, (0, 0, AR + 6), (0, -1, 35), width=5, rise=1.5, deck=VB, deck_slab=VB_SL, edge="obsidian",
           rail=VB_WA, keel="obsidian", lamp_every=5)
    for (x, z) in disk_pts(0, 40, 4):
        bp.set(x, -2, z, VB)
    for x in (-4, 4):
        brazier(bp, x, -1, 39, h=3)
    for z in range(AR + 1, AR + 7):
        for x in range(-2, 3):
            bp.set(x, 1, z, VB)
            bp.set(x, 2, z, "air")

    # --- the underside: hanging cages of the Warden's victims
    for (cx, cz) in ((-9, 6), (11, -7)):
        b = main.get((cx, cz), (-20, 0))[0]
        bp.chain(cx, b - 6, cz, b - 1)
        for y in range(b - 10, b - 6):
            for (x, z) in ((cx - 1, cz - 1), (cx + 1, cz - 1), (cx - 1, cz + 1), (cx + 1, cz + 1)):
                bp.set(x, y, z, "iron_bars")
        bp.fill(cx - 1, b - 7, cz - 1, cx + 1, b - 7, cz + 1, "obsidian")
        bp.fill(cx - 1, b - 11, cz - 1, cx + 1, b - 11, cz + 1, "obsidian")
        bp.set(cx, b - 10, cz, "skeleton_skull[powered=false,rotation=4]")
        bp.set(cx, b - 12, cz, ROD_DOWN)

    # --- the boss: seal on the dais, the Fang Gate and its mist, site of grace, caged hoard
    from . import lair_void_warden
    lair_void_warden.build(bp, AR)


register(StructureDef(
    "void_nest", "end", ["end_highlands", "end_midlands"], [Piece("nest", void_nest)],
    spacing=36, separation=12, adaptation="none", height=("uniform", 58, 75), processors="none",
    title_fr="Nid du Gardien du Vide", title_en="Void Warden's Nest"))
