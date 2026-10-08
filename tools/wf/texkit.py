"""Hand-pixelled texture kit: hue-shifted colour ramps, clustered (not per-pixel) noise and the host stones the
ores sit in. Shared by blockart (ores, metal blocks), texgen_steam (plates) and itemart (item tones).

Rules it encodes (STYLE_STEAMPUNK.md "Item sprites and block faces"):
- a material is a ramp of 4-6 flat tones; shadows slide toward cool violet-blue and lose a little lightness fast,
  highlights slide toward warm cream and lose saturation, so nothing is just "the same colour, darker";
- noise is drawn as clusters of 2-4 pixels snapped to the ramp, never per-pixel jitter;
- light comes from the top-left: a lit edge on the top/left of every raised shape, a cast shadow bottom-right.
"""
import colorsys
import math
import random

from .png import Canvas

WARM_HUE = 0.12      # highlights drift toward this (warm cream / yellow)
COOL_HUE = 0.70      # shadows drift toward this (blue-violet)


def _clamp(v):
    return max(0, min(255, int(round(v))))


def _hue_toward(h, target, amount):
    d = (target - h + 0.5) % 1.0 - 0.5
    return (h + d * amount) % 1.0


def shift(c, t):
    """Shade colour ``c`` by ``t`` in [-1, 1]: t<0 darker and cooler (hue slides toward blue-violet, saturation
    up a little), t>0 lighter and warmer (hue slides toward cream, saturation drops). HSV, so chroma follows value."""
    r, g, b = (v / 255.0 for v in c[:3])
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    grey = s < 0.1
    k = abs(t)
    if t < 0:
        if not grey:
            h = _hue_toward(h, COOL_HUE, 0.13 * k)
            s = min(1.0, s * (1 + 0.3 * k))
        v = v * (1 - 0.66 * k)
    else:
        if not grey:
            h = _hue_toward(h, WARM_HUE, 0.12 * k)
            s = s * (1 - 0.38 * k)
        v = v + (1 - v) * 0.85 * k
    r, g, b = colorsys.hsv_to_rgb(h, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    out = [r * 255, g * 255, b * 255]
    if grey:  # near-greys: a faint cool tint in the shadows, a faint warm one in the lights
        tint = (-3, -2, 7) if t < 0 else (5, 3, -3)
        out = [x + d * k * 1.6 for x, d in zip(out, tint)]
    return tuple(_clamp(x) for x in out)


def ramp(base, n=5, lo=-0.8, hi=0.75):
    """``n`` tones from the darkest (index 0) to the brightest, hue-shifted around ``base``."""
    if n == 1:
        return [tuple(base[:3])]
    return [shift(base, lo + (hi - lo) * i / (n - 1)) for i in range(n)]


def ramp_from(pal, n=6):
    """A (light, mid, dark, outline) palette widened to an n-tone hue-shifted ramp anchored on its mid."""
    light, mid, dark, outline = (tuple(c[:3]) for c in pal)
    return ramp(mid, n, -0.78, 0.72)


def mix(a, b, t):
    return tuple(_clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ clustered noise
def value_noise(seed, cell=4, size=16):
    """Tileable smooth noise in [0, 1] with features about ``cell`` pixels wide."""
    rng = random.Random(seed)
    g = size // cell
    grid = [[rng.random() for _ in range(g)] for _ in range(g)]
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            fx, fy = x / cell, y / cell
            x0, y0 = int(fx) % g, int(fy) % g
            x1, y1 = (x0 + 1) % g, (y0 + 1) % g
            tx, ty = fx - int(fx), fy - int(fy)
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0][x0] + (grid[y0][x1] - grid[y0][x0]) * tx
            b = grid[y1][x0] + (grid[y1][x1] - grid[y1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def field(seed, weights=((4, 0.6), (2, 0.3)), jitter=0.12, size=16):
    """Sum of value-noise octaves plus a little pixel jitter, normalised to [0, 1]."""
    rng = random.Random(f"j{seed}")
    acc = [[0.0] * size for _ in range(size)]
    for i, (cell, w) in enumerate(weights):
        n = value_noise(f"{seed}/{i}", cell, size)
        for y in range(size):
            for x in range(size):
                acc[y][x] += n[y][x] * w
    for y in range(size):
        for x in range(size):
            acc[y][x] += rng.uniform(-jitter, jitter)
    flat = [v for row in acc for v in row]
    lo, hi = min(flat), max(flat)
    return [[(v - lo) / (hi - lo) for v in row] for row in acc]


def quantize(f, cuts):
    """Field -> tone indices: cuts are ascending thresholds (len(cuts)+1 tones)."""
    return [[sum(v > c for c in cuts) for v in row] for row in f]


def despeckle(idx, passes=2):
    """Lone pixels (no edge neighbour of the same tone) take their most common neighbour: clusters, not dust."""
    n = len(idx)
    for _ in range(passes):
        out = [row[:] for row in idx]
        for y in range(n):
            for x in range(n):
                v = idx[y][x]
                nb = [idx[(y + dy) % n][(x + dx) % n] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if v not in nb:
                    out[y][x] = max(set(nb), key=nb.count)
        idx = out
    return idx


def paint(idx, tones):
    cv = Canvas(len(idx[0]), len(idx))
    for y, row in enumerate(idx):
        for x, v in enumerate(row):
            cv.set(x, y, tones[max(0, min(len(tones) - 1, v))])
    return cv


# ------------------------------------------------------------------ host stones (ore backgrounds)
HOST_BASE = {"stone": (126, 126, 128), "deepslate": (80, 80, 88), "netherrack": (110, 44, 44)}


def host_tones(host):
    base = HOST_BASE[host]
    if host == "netherrack":
        return [shift(base, -0.62), shift(base, -0.35), shift(base, -0.1), base, shift(base, 0.22)]
    if host == "deepslate":
        return [shift(base, -0.55), shift(base, -0.3), shift(base, -0.1), base, shift(base, 0.16)]
    return [shift(base, -0.42), shift(base, -0.2), shift(base, -0.05), base, shift(base, 0.16)]


def host_idx(host, seed):
    """Tone indices (0 darkest .. 4 lightest) of a host stone, drawn as clusters."""
    rng = random.Random(f"host{host}{seed}")
    if host == "deepslate":
        # long horizontal strata: stretch the noise sideways, then cut thin dark seams between the layers
        f = field(f"{seed}ds", ((8, 0.5), (4, 0.35), (2, 0.15)), 0.08)
        f = [[(f[y][x] + f[y][(x + 3) % 16] + f[y][(x + 6) % 16]) / 3 for x in range(16)] for y in range(16)]
        lo = min(min(r) for r in f)
        hi = max(max(r) for r in f)
        f = [[(v - lo) / (hi - lo) for v in r] for r in f]
        idx = quantize(f, (0.12, 0.36, 0.64, 0.88))
        for y in (rng.randrange(1, 5), rng.randrange(6, 10), rng.randrange(11, 15)):
            x = rng.randrange(16)
            for _ in range(rng.randint(3, 6)):
                idx[y][x % 16] = 1
                if rng.random() < 0.25:
                    y = (y + rng.choice((-1, 1))) % 16
                x += 1
        return despeckle(idx, 1)
    if host == "netherrack":
        f = field(f"{seed}nr", ((4, 0.55), (2, 0.35)), 0.1)
        idx = quantize(f, (0.2, 0.38, 0.6, 0.82))
        return despeckle(idx, 2)
    f = field(f"{seed}st", ((4, 0.55), (2, 0.3)), 0.1)
    idx = quantize(f, (0.16, 0.34, 0.68, 0.86))
    idx = despeckle(idx, 2)
    # a couple of short dark cracks like vanilla stone
    for _ in range(2):
        x, y = rng.randrange(16), rng.randrange(16)
        for _ in range(rng.randint(2, 3)):
            idx[y % 16][x % 16] = 0
            x += rng.choice((1, 1, 0))
            y += rng.choice((0, 1))
    return idx


def host(host_name, seed):
    tones = host_tones(host_name)
    return paint(host_idx(host_name, seed), tones), tones


def tmul(c, f):
    """Drop-in for texgen.mul(c, f) (scale brightness by ``f``) that hue-shifts instead: darkening slides cool,
    brightening slides warm and desaturates, and a bright colour pushed up turns cream instead of clipping."""
    c = tuple(c[:3])
    if abs(f - 1.0) < 1e-6:
        return c
    if f < 1:
        return shift(c, -min(1.0, (1 - f) / 0.66))
    v = max(c) / 255.0
    if v >= 0.999:
        k = min(1.0, (f - 1) * 0.9)
    else:
        k = min(1.0, max(v, 0.35) * (f - 1) / ((1 - v) * 0.85))
    return shift(c, k)


def grain_field(seed, levels=3, cell=2, stretch=1):
    """Tone offsets in {-1, 0, +1} (levels=3) laid out as 2-4 px clusters; ``stretch`` > 1 smears them sideways
    (brushed metal, wood)."""
    f = field(f"g{seed}", ((cell * 2, 0.5), (cell, 0.5)), 0.08)
    if stretch > 1:
        f = [[sum(f[y][(x + k) % 16] for k in range(stretch)) / stretch for x in range(16)] for y in range(16)]
        lo = min(min(r) for r in f)
        hi = max(max(r) for r in f)
        f = [[(v - lo) / (hi - lo) for v in r] for r in f]
    cuts = (0.3, 0.7) if levels == 3 else (0.5,)
    idx = despeckle(quantize(f, cuts), 1)
    off = (levels - 1) // 2
    return [[v - off for v in row] for row in idx]
