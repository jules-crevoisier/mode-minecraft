"""Procedural 16x16 block textures with Minecraft-like shading (bevels, per-brick tint, mortar)."""
import math
import random

from .png import Canvas


def clamp(v):
    return max(0, min(255, int(v)))


def mul(c, f):
    return tuple(clamp(v * f) for v in c[:3])


def _hmul(c, f):
    """mul() with hue-shifted shading (texkit.tmul): the block faces below shade with it."""
    from .texkit import tmul
    return tmul(c, f)


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def noise(cv, base, amount, seed, palette=None):
    rng = random.Random(seed)
    for y in range(cv.h):
        for x in range(cv.w):
            c = rng.choice(palette) if palette else base
            cv.set(x, y, _hmul(c, 1 + rng.uniform(-amount, amount)))


def bricks(base, mortar, seed=0, rows=4, brick_w=8, var=0.10, bevel=0.12, grain=0.05):
    """Running-bond bricks: per-brick tint, clustered surface grain, a lit top/left edge and a shaded bottom/right
    edge (hue-shifted), a chipped corner here and there, mortar recessed in a cooler dark tone."""
    from .texkit import grain_field
    rng = random.Random(seed)
    g = grain_field(f"br{seed}")
    cv = Canvas(16, 16)
    h = 16 // rows
    mortar_lo = _hmul(mortar, 0.86)
    for r in range(rows):
        off = 0 if r % 2 == 0 else brick_w // 2
        for bx in range(-brick_w, 16 + brick_w, brick_w):
            tint = 1 + rng.choice((-1, -0.5, 0, 0.5, 1)) * var
            chip = rng.random() < 0.35
            x0 = bx + off
            for y in range(r * h, r * h + h):
                for x in range(x0, x0 + brick_w):
                    if not 0 <= x < 16:
                        continue
                    lx, ly = x - x0, y - r * h
                    if ly == h - 1 or lx == brick_w - 1:
                        cv.set(x, y, mortar_lo if (x + y) % 5 == 0 else mortar)
                        continue
                    f = tint * (1 + g[y][x] * grain * 1.2)
                    if ly == 0 or lx == 0:
                        f *= 1 + bevel
                    elif ly == h - 2 or lx == brick_w - 2:
                        f *= 1 - bevel
                    if chip and lx == brick_w - 2 and ly == 0:
                        cv.set(x, y, mortar)
                        continue
                    cv.set(x, y, _hmul(base, f))
    return cv


def scales(base, seed=0, var=0.08):
    """Roof tiles laid as overlapping fish scales (4 px wide, 4 px tall, offset rows)."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    dark = _hmul(base, 0.55)
    for y in range(16):
        r = y // 4
        off = 0 if r % 2 == 0 else 2
        for x in range(16):
            lx = (x + off) % 4
            ly = y % 4
            tile = ((x + off) // 4, r)
            t = 1 + (hash((tile, seed)) % 100 / 100.0 - 0.5) * 2 * var
            if ly == 3 or (ly == 2 and lx in (0, 3)):
                cv.set(x, y, _hmul(dark, 1 + rng.uniform(-0.05, 0.05)))
            elif ly == 0 and lx in (1, 2):
                cv.set(x, y, _hmul(base, t * 1.22))
            else:
                cv.set(x, y, _hmul(base, t * (1.06 - ly * 0.06) * (1 + rng.uniform(-0.04, 0.04))))
    return cv


def polished(base, seed=0, border=None):
    """A smooth dressed stone face: clustered faint grain, a two-step bevel (lit top/left, shaded bottom/right)."""
    from .texkit import grain_field
    g = grain_field(f"po{seed}", cell=4)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            f = 1 + g[y][x] * 0.03
            rim = x in (0, 15) or y in (0, 15)
            if x == 0 or y == 0:
                f *= 1.15
            elif x == 15 or y == 15:
                f *= 0.76
            elif x == 1 or y == 1:
                f *= 1.05
            elif x == 14 or y == 14:
                f *= 0.9
            cv.set(x, y, _hmul(border if rim and border else base, f))
    return cv


def overlay_moss(cv, seed=0, amount=0.35):
    rng = random.Random(seed)
    moss = [(78, 104, 46), (96, 124, 52), (64, 88, 40)]
    for y in range(16):
        for x in range(16):
            # moss gathers on the lower side of bricks and drips down
            p = amount * (0.4 + 0.6 * ((y % 4) / 3.0))
            if rng.random() < p * (0.7 + 0.6 * math.sin(x * 0.9 + seed)):
                cv.set(x, y, rng.choice(moss))
    return cv


def overlay_cracks(cv, color, seed=0, n=3, glow=None):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(2, 13), rng.randint(1, 4)
        for _ in range(rng.randint(5, 9)):
            cv.set(x, y, color)
            if glow:
                for dx, dy in ((1, 0), (-1, 0)):
                    if rng.random() < 0.4:
                        cv.set(x + dx, y + dy, glow)
            x = max(0, min(15, x + rng.choice((-1, 0, 1))))
            y = min(15, y + 1)
    return cv


def stars(cv, colors, seed=0, n=5):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(0, 15), rng.randint(0, 15)
        cv.set(x, y, rng.choice(colors))
    return cv


def emblem(cv, color, shadow):
    """Compass rose carved into the centre of a block face."""
    pts = set()
    for i in range(-5, 6):
        pts.add((8 + i, 8 if abs(i) < 6 else 8))
        pts.add((8, 8 + i))
    for i in range(-3, 4):
        pts.add((8 + i, 8 + i))
        pts.add((8 + i, 8 - i))
    for (x, y) in pts:
        cv.set(x, y, color)
        sx, sy = min(15, x + 1), min(15, y + 1)
        if (sx, sy) not in pts:
            cv.set(sx, sy, shadow)
    for a in range(0, 360, 15):
        x = 8 + round(6.5 * math.cos(math.radians(a)))
        y = 8 + round(6.5 * math.sin(math.radians(a)))
        cv.set(x, y, shadow)
    return cv


def frame(cv, light, dark):
    for i in range(16):
        cv.set(i, 0, light)
        cv.set(0, i, light)
        cv.set(i, 15, dark)
        cv.set(15, i, dark)
    return cv


def runes(cv, glow, core, seed=0):
    rng = random.Random(seed)
    glyphs = [
        [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 2)],
        [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 2), (1, 1), (2, 0), (0, 0), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)],
    ]
    for gx in (3, 9):
        for gy in (3, 9):
            for (x, y) in rng.choice(glyphs):
                px, py = gx + x, gy + y
                cv.set(px, py, core)
                for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < 16 and 0 <= ny < 16 and cv.get(nx, ny)[:3] != core[:3]:
                        cv.set(nx, ny, mix(cv.get(nx, ny), glow, 0.55))
    return cv


def crystal(light, mid, dark, seed=0):
    """Faceted crystal mass: tileable Voronoi facets, each one flat tone picked by how it faces the top-left light
    (from a hue-shifted ramp between ``dark`` and ``light``); facet edges are lit on their upper-left side and
    shaded on their lower-right side, with a few glints on the brightest ridges."""
    from .texkit import mix as kmix
    rng = random.Random(seed)
    ramp = [_hmul(dark, 0.8), dark, kmix(dark, mid, 0.5), mid, kmix(mid, light, 0.5), light]
    cells = []
    for gy in range(3):
        for gx in range(3):
            cells.append((gx * 5.33 + rng.uniform(0.5, 4.8), gy * 5.33 + rng.uniform(0.5, 4.8),
                          rng.choice((1, 2, 2, 3, 3, 4))))

    def nearest(x, y):
        best = []
        for i, (cx, cy, _t) in enumerate(cells):
            dx = min(abs(x - cx), 16 - abs(x - cx))
            dy = min(abs(y - cy), 16 - abs(y - cy))
            best.append((dx * dx + dy * dy, i))
        best.sort()
        return best

    owner = [[nearest(x + 0.5, y + 0.5)[0][1] for x in range(16)] for y in range(16)]
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            i = owner[y][x]
            t = cells[i][2]
            up, left = owner[(y - 1) % 16][x], owner[y][(x - 1) % 16]
            down, right = owner[(y + 1) % 16][x], owner[y][(x + 1) % 16]
            if up != i or left != i:
                t = min(5, t + 1)          # the lit lip of the facet
            elif down != i or right != i:
                t = max(0, t - 1)          # the shaded fold below it
            cv.set(x, y, ramp[t])
    for i, (cx, cy, t) in enumerate(cells):
        if t >= 3:
            cv.set(int(cx) % 16, int(cy) % 16, kmix(light, (255, 255, 255), 0.6))
    return cv


def lamp(frame_c, glow, core, seed=0):
    cv = Canvas(16, 16)
    rng = random.Random(seed)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 1, 14, 15) or y in (0, 1, 14, 15)
            if edge:
                cv.set(x, y, _hmul(frame_c, (1.15 if x == 0 or y == 0 else 0.8 if x == 15 or y == 15 else 1.0)))
            else:
                d = math.hypot(x - 7.5, y - 7.5) / 7.0
                cv.set(x, y, mix(core, glow, min(1, d * 1.1 + rng.uniform(-0.05, 0.05))))
    for i in range(2, 14):
        cv.set(i, 7, _hmul(frame_c, 0.9))
        cv.set(7, i, _hmul(frame_c, 0.9))
    return cv


def trim(base, gold, seed=0):
    cv = polished(base, seed)
    for x in range(16):
        for y in (5, 10):
            cv.set(x, y, _hmul(gold, 0.8))
        for y in range(6, 10):
            cv.set(x, y, _hmul(gold, 1.0 + (0.15 if (x + y) % 4 == 0 else 0)))
    for x in range(0, 16, 4):
        cv.set(x, 7, _hmul(gold, 1.3))
        cv.set(x + 1, 8, _hmul(gold, 1.3))
    return cv
