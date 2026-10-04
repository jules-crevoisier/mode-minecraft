"""Procedural 16x16 textures for the world blocks (wf/worldblocks.py): two woods and three stones.

Same conventions as texgen.py: vanilla-like shading (light top-left, dark bottom-right), small per-pixel noise,
textures tile seamlessly (every pattern wraps around the 16 px edge). Cut-out textures (leaves, sapling, door,
trapdoor) only use fully opaque or fully transparent pixels, so the game puts them in the cutout layer.
"""
import math
import random

from .png import Canvas
from .texgen import clamp, mix, mul

CLEAR = (0, 0, 0, 0)


def _rgb(c, f=1.0):
    return tuple(clamp(v * f) for v in c[:3])


def _hash(x, y, seed):
    """Deterministic pseudo-random value in [0, 1) for a pixel (no RNG state, so patterns can wrap)."""
    n = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def _smooth(x, y, seed, period=16, cell=4):
    """Tileable value noise in [0, 1): bilinear between cell corners, wrapping every `period` px."""
    n = period // cell
    gx, gy = x / cell, y / cell
    x0, y0 = int(math.floor(gx)), int(math.floor(gy))
    tx, ty = gx - x0, gy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)

    def v(i, j):
        return _hash(i % n, j % n, seed)
    a = v(x0, y0) + (v(x0 + 1, y0) - v(x0, y0)) * tx
    b = v(x0, y0 + 1) + (v(x0 + 1, y0 + 1) - v(x0, y0 + 1)) * tx
    return a + (b - a) * ty


# ------------------------------------------------------------------ wood
def bark(base, dark, light, seed=0, ridge=None):
    """Log side: vertical bark plates split by dark grooves, with short cross cracks (like oak / dark oak logs)."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    # plate boundaries: columns that are grooves (wrap around 16)
    grooves = set()
    x = rng.randint(0, 2)
    while x < 16:
        grooves.add(x)
        x += rng.choice((3, 4, 4, 5))
    for x in range(16):
        drift = rng.choice((-1, 0, 0, 1))
        col_tint = 1 + rng.uniform(-0.06, 0.06)
        for y in range(16):
            gx = (x + (drift if y > 8 else 0)) % 16
            n = _smooth(x, y, seed, cell=4)
            f = col_tint * (0.94 + n * 0.14) * (1 + rng.uniform(-0.05, 0.05))
            if gx in grooves:
                c = _rgb(dark, 1 + rng.uniform(-0.08, 0.04))
            elif (gx - 1) % 16 in grooves:
                c = _rgb(mix(base, light, 0.45), f)  # lit edge of a plate
            elif (gx + 1) % 16 in grooves:
                c = _rgb(mix(base, dark, 0.35), f)
            else:
                c = _rgb(base, f)
            cv.set(x, y, c)
    # short horizontal cracks across plates
    for _ in range(rng.randint(4, 6)):
        cx, cy = rng.randrange(16), rng.randrange(16)
        for dx in range(rng.randint(1, 2)):
            cv.set((cx + dx) % 16, cy, _rgb(dark, 1.05))
        cv.set(cx % 16, (cy + 1) % 16, _rgb(mix(base, light, 0.5)))
    if ridge:  # sparse coloured flecks (lichen, rust)
        for _ in range(ridge[1]):
            cv.set(rng.randrange(16), rng.randrange(16), _rgb(ridge[0], 1 + rng.uniform(-0.1, 0.1)))
    return cv


def stripped_side(base, dark, seed=0):
    """Stripped log side: smooth, with long vertical grain lines."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    lines = {x: rng.random() < 0.35 for x in range(16)}
    for x in range(16):
        tint = 1 + rng.uniform(-0.04, 0.04)
        for y in range(16):
            n = _smooth(x, y, seed + 3, cell=8)
            f = tint * (0.95 + n * 0.1) * (1 + rng.uniform(-0.025, 0.025))
            c = _rgb(base, f)
            if lines[x] and _hash(x, y // 3, seed) > 0.3:
                c = _rgb(mix(base, dark, 0.35), f)
            cv.set(x, y, c)
    return cv


def log_top(core, ring, bark_c, bark_dark, seed=0, rings=3):
    """Log end: rounded-square growth rings, a one-pixel bark rim."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            if x in (0, 15) or y in (0, 15):
                c = _rgb(bark_dark if (x + y + seed) % 3 == 0 else bark_c, 1 + rng.uniform(-0.06, 0.06))
            else:
                d = 0.55 * max(abs(dx), abs(dy)) + 0.45 * math.hypot(dx, dy) * 0.92
                d += (_smooth(x, y, seed, cell=4) - 0.5) * 1.1  # wobbly rings
                band = int(d * rings / 6.6 * 2)
                c = mix(core, ring, 0.55) if band % 2 else core
                if d < 1.0:
                    c = mix(core, ring, 0.8)
                if x in (1, 14) or y in (1, 14):
                    c = mix(c, ring, 0.5)  # sapwood just under the bark
                c = _rgb(c, 1 + rng.uniform(-0.035, 0.035))
            cv.set(x, y, c)
    return cv


def planks(base, dark, light, seed=0, boards=4):
    """Planks: boards with a dark seam under each, staggered butt joints and horizontal grain."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    h = 16 // boards
    for b in range(boards):
        tint = 1 + rng.uniform(-0.07, 0.07)
        joint = rng.randrange(16)
        grain_rows = [rng.random() < 0.5 for _ in range(h)]
        for yy in range(h):
            y = b * h + yy
            for x in range(16):
                f = tint * (1 + rng.uniform(-0.03, 0.03))
                if yy == h - 1:
                    c = _rgb(dark, 1 + rng.uniform(-0.04, 0.04))
                elif x == joint:
                    c = _rgb(dark, 1.08)
                elif x == (joint + 1) % 16:
                    c = _rgb(light, f)
                elif yy == 0:
                    c = _rgb(mix(base, light, 0.35), f)
                else:
                    c = _rgb(base, f)
                    if grain_rows[yy] and _hash(x // 3, y, seed) > 0.55:
                        c = _rgb(mix(base, dark, 0.3), f)
                cv.set(x, y, c)
    return cv


def leaves(base, light, dark, seed=0, holes=0.2, specks=None):
    """Leaves: overlapping leaf clusters (lit top-left, shaded bottom-right) with see-through gaps."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    shade = [[0.0] * 16 for _ in range(16)]
    cover = [[False] * 16 for _ in range(16)]
    for _ in range(46):
        cx, cy, r = rng.randrange(16), rng.randrange(16), rng.choice((1.3, 1.6, 2.0, 2.2))
        tone = rng.uniform(-0.12, 0.12)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = math.hypot(dx, dy)
                if d <= r:
                    x, y = (cx + dx) % 16, (cy + dy) % 16
                    cover[y][x] = True
                    # light from the top-left of each cluster
                    shade[y][x] = tone + (-dx - dy) / (r * 6.0) + (0.1 if d < r * 0.5 else 0)
    for y in range(16):
        for x in range(16):
            if not cover[y][x] or _hash(x, y, seed + 9) < holes * 0.5:
                continue
            s = shade[y][x] + rng.uniform(-0.05, 0.05)
            c = mix(base, light, min(1, s * 1.7)) if s > 0 else mix(base, dark, min(1, -s * 2.0))
            cv.set(x, y, _rgb(c))
    # carve holes so the canopy reads as leaves, not a solid block
    for _ in range(int(holes * 30)):
        x, y = rng.randrange(16), rng.randrange(16)
        cv.set(x, y, CLEAR)
        if rng.random() < 0.5:
            cv.set((x + 1) % 16, y, CLEAR)
    if specks:
        colour, n = specks
        for _ in range(n):
            x, y = rng.randrange(16), rng.randrange(16)
            if cv.get(x, y)[3]:
                cv.set(x, y, colour)
                for dx, dy in ((1, 0), (0, 1)):
                    p = cv.get((x + dx) % 16, (y + dy) % 16)
                    if p[3]:
                        cv.set((x + dx) % 16, (y + dy) % 16, mix(p, colour, 0.45))
    return cv


def sapling(trunk, leaf, leaf_light, leaf_dark, seed=0, specks=None):
    """Cross-model sapling: a thin forked stem and a small round crown."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(9, 16):
        cv.set(7 + (1 if y < 12 and y % 3 == 0 else 0), y, _rgb(trunk, 1.1 if y % 2 else 0.9))
    cv.set(8, 11, _rgb(trunk, 0.8))
    cv.set(9, 10, _rgb(trunk, 0.9))
    cv.set(6, 12, _rgb(trunk))
    cv.set(5, 11, _rgb(trunk, 0.85))
    blobs = [(7, 5, 3.3), (4, 8, 2.0), (11, 7, 2.3), (9, 3, 2.0)]
    for cx, cy, r in blobs:
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - cx, y - cy)
                if d <= r and rng.random() > 0.08:
                    lit = (cx - x) + (cy - y)
                    c = leaf_light if lit > 1.2 else leaf_dark if lit < -1.2 else leaf
                    cv.set(x, y, _rgb(c, 1 + rng.uniform(-0.06, 0.06)))
    if specks:
        for _ in range(specks[1]):
            x, y = rng.randint(3, 13), rng.randint(2, 9)
            if cv.get(x, y)[3]:
                cv.set(x, y, specks[0])
    return cv


def door(base, frame_c, dark, light, half, seed=0, window=None, bands=None):
    """Door half (16x16): a framed slab of vertical boards. `window` (glass colour or "hole") cuts two panes in the
    top half; `bands` (metal colour) adds iron straps."""
    rng = random.Random(seed + (0 if half == "top" else 7))
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            f = 1 + rng.uniform(-0.04, 0.04)
            if x in (0, 15) or (half == "top" and y == 0) or (half == "bottom" and y == 15):
                c = _rgb(frame_c, f * (1.08 if x == 0 or y == 0 else 0.86))
            elif x in (1, 14):
                c = _rgb(mix(frame_c, base, 0.5), f)
            else:
                board = (x - 2) // 3
                lx = (x - 2) % 3
                c = _rgb(base, f * (1 + (board % 2) * 0.05))
                if lx == 2:
                    c = _rgb(mix(base, dark, 0.55), f)
                elif lx == 0:
                    c = _rgb(mix(base, light, 0.25), f)
            cv.set(x, y, c)
    # a cross rail mid-door and a rail near the edge
    rails = (7, 8) if half == "bottom" else (12, 13)
    for x in range(1, 15):
        cv.set(x, rails[0], _rgb(frame_c, 1.06))
        cv.set(x, rails[1], _rgb(frame_c, 0.8))
    if half == "top" and window:
        for (x0, x1) in ((3, 7), (9, 13)):
            for y in range(3, 10):
                for x in range(x0, x1):
                    edge = x in (x0, x1 - 1) or y in (3, 9)
                    if edge:
                        cv.set(x, y, _rgb(frame_c, 0.9 if x == x1 - 1 or y == 9 else 1.05))
                    elif window == "hole":
                        cv.set(x, y, CLEAR)
                    else:
                        cv.set(x, y, _rgb(window, 1.12 if (x + y) % 5 == 0 else 1.0))
    if bands:
        for y in ((3, 4) if half == "top" else (11, 12)):
            for x in range(1, 15):
                cv.set(x, y, _rgb(bands, 1.1 if y % 2 else 0.8))
            for x in (3, 12):
                cv.set(x, y if y % 2 else y - 1, _rgb(bands, 1.4))
    if half == "bottom":  # handle
        for y in (2, 3, 4):
            cv.set(12, y, _rgb(dark, 0.7))
        cv.set(12, 1, _rgb(light, 1.1))
    return cv


def trapdoor(base, frame_c, dark, light, seed=0, holes=True):
    """Trapdoor: frame, two crossed boards and (optionally) see-through gaps."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            f = 1 + rng.uniform(-0.04, 0.04)
            if x in (0, 15) or y in (0, 15):
                c = _rgb(frame_c, f * (1.08 if x == 0 or y == 0 else 0.84))
            elif x in (1, 14) or y in (1, 14):
                c = _rgb(mix(frame_c, base, 0.45), f)
            else:
                lx = (x - 2) % 4
                c = _rgb(base, f)
                if lx == 3:
                    c = _rgb(mix(base, dark, 0.5), f)
                elif lx == 0:
                    c = _rgb(mix(base, light, 0.25), f)
            cv.set(x, y, c)
    for i in range(2, 14):
        cv.set(i, 7, _rgb(frame_c, 1.04))
        cv.set(i, 8, _rgb(frame_c, 0.82))
    if holes:
        for (x0, y0) in ((3, 3), (10, 3), (3, 10), (10, 10)):
            for dy in range(3):
                for dx in range(3):
                    if (dx, dy) != (1, 1) or True:
                        cv.set(x0 + dx, y0 + dy, CLEAR)
            cv.set(x0 + 1, y0 + 1, CLEAR)
    return cv


def door_item(base, frame_c, dark, light, seed=0, window=None, bands=None):
    """Inventory sprite of a door: the two halves squeezed into 16x16, with an outline."""
    top, bottom = door(base, frame_c, dark, light, "top", seed, window, bands), \
        door(base, frame_c, dark, light, "bottom", seed, window, bands)
    cv = Canvas(16, 16)
    outline = _rgb(frame_c, 0.55)
    for y in range(16):
        src = top if y < 8 else bottom
        sy = (y % 8) * 2 + (1 if y >= 8 else 0)
        for x in range(4, 12):
            sx = 1 + (x - 4) * 2 - (1 if x > 7 else 0)
            p = src.get(min(15, sx), min(15, sy))
            cv.set(x, y, p if p[3] else CLEAR)
    for y in range(16):
        cv.set(3, y, outline)
        cv.set(12, y, outline)
    for x in range(3, 13):
        cv.set(x, 0, outline)
        cv.set(x, 15, outline)
    cv.set(10, 10, _rgb(light, 1.2))
    return cv


# ------------------------------------------------------------------ stone
def marble(seed=0, base=(234, 232, 228), vein=(160, 162, 170), soft=(210, 210, 214), veins=4):
    """White marble: near-flat white with fine noise and thin grey veins that wander diagonally (wrapping)."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = _smooth(x, y, seed, cell=8)
            cv.set(x, y, _rgb(base, 0.965 + n * 0.05 + rng.uniform(-0.012, 0.012)))
    for v in range(veins):
        x, y = rng.uniform(0, 16), float(rng.randrange(16))
        slope = rng.choice((-1, 1)) * rng.uniform(0.3, 0.9)
        main = v == 0
        colour = vein if main else mix(vein, soft, 0.45)
        length = 13 if main else rng.randint(5, 9)
        px, py = int(x) % 16, int(y) % 16
        for _ in range(length):
            cv.set(px, py, _rgb(colour, 1 + rng.uniform(-0.04, 0.04)))
            side = (px + (1 if slope > 0 else -1)) % 16
            cv.set(side, py, mix(cv.get(side, py), soft, 0.55))
            # step down one row, drifting sideways by the slope (plus a wobble); fill gaps so the line stays connected
            if rng.random() < 0.3:
                slope = -slope * rng.uniform(0.6, 1.0)  # veins meander instead of running straight
            x += slope + rng.uniform(-0.5, 0.5)
            nx, ny = int(math.floor(x)) % 16, (py + 1) % 16
            while (nx - px) % 16 not in (0, 1, 15):
                px = (px + (1 if (nx - px) % 16 < 8 else -1)) % 16
                cv.set(px, py, _rgb(colour, 1.03))
            px, py = nx, ny
    return cv


def polished(base_tex, light, dark, inset_light=1.04):
    """Polished block from a natural texture: smoothed, with a bevelled frame like polished diorite."""
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            p = base_tex.get(x, y)
            # soften: average with the next pixel so the noise reads finer
            q = base_tex.get((x + 1) % 16, (y + 1) % 16)
            c = mix(p, q, 0.5)
            if x == 0 or y == 0:
                c = mix(c, light, 0.55)
            elif x == 15 or y == 15:
                c = mix(c, dark, 0.55)
            elif x == 1 or y == 1:
                c = _rgb(c, inset_light)
            elif x == 14 or y == 14:
                c = mix(c, dark, 0.2)
            cv.set(x, y, c)
    return cv


def stone_bricks(base_tex, mortar, seed=0, rows=4, brick_w=8, bevel=0.1, var=0.06):
    """Bricks cut from a natural texture (keeps its veins/specks), running bond, bevelled edges."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    h = 16 // rows
    for r in range(rows):
        off = 0 if r % 2 == 0 else brick_w // 2
        for bx in range(-brick_w, 16 + brick_w, brick_w):
            tint = 1 + rng.uniform(-var, var)
            x0 = bx + off
            for yy in range(h):
                y = r * h + yy
                for x in range(x0, x0 + brick_w):
                    if not 0 <= x < 16:
                        continue
                    lx = x - x0
                    if yy == h - 1 or lx == brick_w - 1:
                        cv.set(x, y, _rgb(mortar, 1 + rng.uniform(-0.04, 0.04)))
                        continue
                    f = tint
                    if yy == 0 or lx == 0:
                        f *= 1 + bevel
                    elif yy == h - 2 or lx == brick_w - 2:
                        f *= 1 - bevel
                    cv.set(x, y, _rgb(base_tex.get(x, y), f))
    return cv


def pillar_side(base, light, dark, seed=0):
    """Fluted column side: vertical flutes (lit left edge, shadowed groove) and a band at top and bottom."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            f = 1 + rng.uniform(-0.015, 0.015)
            lx = x % 4
            c = {0: mix(base, light, 0.5), 1: base, 2: base, 3: mix(base, dark, 0.45)}[lx]
            if x in (0, 15):
                c = mix(base, dark, 0.25) if x == 15 else mix(base, light, 0.3)
            if y in (0, 15):
                c = mix(base, dark, 0.45) if y == 15 else mix(base, light, 0.6)
            elif y in (1, 14):
                c = base if y == 1 else mix(base, dark, 0.15)
            cv.set(x, y, _rgb(c, f))
    return cv


def pillar_top(base, light, dark, seed=0):
    """Column end: bevelled square with a carved ring."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            c = base
            if x == 0 or y == 0:
                c = mix(base, light, 0.55)
            elif x == 15 or y == 15:
                c = mix(base, dark, 0.5)
            elif 4.6 <= d < 5.6:
                c = mix(base, dark, 0.35) if x + y > 15 else mix(base, light, 0.4)
            elif 5.6 <= d < 6.4:
                c = mix(base, dark, 0.2) if x + y <= 15 else mix(base, light, 0.25)
            cv.set(x, y, _rgb(c, 1 + rng.uniform(-0.015, 0.015)))
    return cv


def chiseled_marble(base, light, dark, accent, seed=0):
    """Carved panel: a framed lozenge with a small rosette, on polished marble."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            c = base
            if x in (0, 15) or y in (0, 15):
                c = mix(base, light, 0.5) if x == 0 or y == 0 else mix(base, dark, 0.5)
            elif x in (2, 13) or y in (2, 13):
                c = mix(base, dark, 0.3) if x == 13 or y == 13 else mix(base, light, 0.3)
            d = abs(x - 7.5) + abs(y - 7.5)
            if 4.5 <= d < 5.5:
                c = mix(base, dark, 0.38) if y > 7.5 else mix(base, light, 0.35)
            elif 5.5 <= d < 6.3:
                c = mix(base, light, 0.25) if y > 7.5 else mix(base, dark, 0.22)
            ax, ay = abs(x - 7.5), abs(y - 7.5)
            if (ax < 1 and ay < 3) or (ay < 1 and ax < 3):
                c = accent if (ax < 1 and ay < 1) else mix(accent, dark, 0.25)
            elif ax < 2 and ay < 2:
                c = mix(base, dark, 0.3)
            cv.set(x, y, _rgb(c, 1 + rng.uniform(-0.015, 0.015)))
    return cv


def speckled(base, palette, seed=0, streak=None, grain=0.05, blotch=0.12):
    """Granite-like rock: soft blotches, coloured specks; `streak` = (colour, count) adds short vertical drips."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = _smooth(x, y, seed, cell=4)
            c = _rgb(base, 1 - blotch + n * blotch * 2 + rng.uniform(-grain, grain))
            if rng.random() < 0.22:
                c = _rgb(rng.choice(palette), 1 + rng.uniform(-0.06, 0.06))
            cv.set(x, y, c)
    if streak:
        colour, count = streak
        for _ in range(count):
            x, y = rng.randrange(16), rng.randrange(16)
            for dy in range(rng.randint(2, 4)):
                p = cv.get(x, (y + dy) % 16)
                cv.set(x, (y + dy) % 16, mix(p, colour, 0.65 - dy * 0.12))
    return cv


def layered(base, dark, light, seed=0, specks=None):
    """Slate: horizontal cleavage layers of slightly different tones, broken dark seams."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    row_tint = []
    t = 1.0
    for y in range(16):
        if rng.random() < 0.35:
            t = 1 + rng.uniform(-0.08, 0.08)
        row_tint.append(t)
    seams = {y: rng.random() < 0.4 for y in range(16)}
    for y in range(16):
        for x in range(16):
            n = _smooth(x, y, seed + 5, cell=8)
            c = _rgb(base, row_tint[y] * (0.95 + n * 0.1) * (1 + rng.uniform(-0.035, 0.035)))
            if seams[y] and _hash(x // 3, y, seed) > 0.45:
                c = _rgb(dark, 1 + rng.uniform(-0.05, 0.05))
                p = (y - 1) % 16
                cv.set(x, p, mix(cv.get(x, p) if cv.get(x, p)[3] else c, light, 0.25))
            cv.set(x, y, c)
    if specks:
        for _ in range(specks[1]):
            cv.set(rng.randrange(16), rng.randrange(16), _rgb(specks[0], 1 + rng.uniform(-0.08, 0.08)))
    return cv


def slate_tiles(base, dark, light, seed=0, size=4):
    """Small square tiles like deepslate tiles: each tile bevelled and slightly tinted."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for ty in range(0, 16, size):
        for tx in range(0, 16, size):
            tint = 1 + rng.uniform(-0.09, 0.09)
            for yy in range(size):
                for xx in range(size):
                    x, y = tx + xx, ty + yy
                    f = tint * (1 + rng.uniform(-0.03, 0.03))
                    if xx == size - 1 or yy == size - 1:
                        c = _rgb(dark, 1 + rng.uniform(-0.04, 0.04))
                    elif xx == 0 or yy == 0:
                        c = _rgb(mix(base, light, 0.16), f)
                    else:
                        c = _rgb(base, f)
                    cv.set(x, y, c)
    return cv
