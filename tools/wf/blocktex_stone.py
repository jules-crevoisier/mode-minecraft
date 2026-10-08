"""Decorative stone faces for wf/blocktex.py that were flat fills or per-pixel speckle: polished / carved guild
stone, guild floor tiles, rust rock and its polished cut, the gilded trim's top. Clustered tone patches only, light
from the top-left."""
from .png import Canvas
from . import texkit as K

GUILD = (204, 180, 138)
RUST = (160, 86, 54)
EMBER_STONE = (56, 48, 54)
GOLD = (232, 182, 72)


def ramp(mid, lo=-0.7, hi=0.6):
    return K.ramp(mid, 6, lo, hi)


def mottle(seed, cuts=(0.3, 0.72), weights=((8, 0.55), (4, 0.35), (2, 0.1))):
    """Tone offsets -1/0/+1 laid out as soft 3-6 px patches (never single pixels)."""
    f = K.field(seed, weights, 0.04)
    idx = K.despeckle(K.quantize(f, cuts), 2)
    return [[v - 1 for v in row] for row in idx]


def bevel(cv, r, x0, y0, x1, y1, hi=5, lo=1, base=3, inner=True):
    for x in range(x0, x1 + 1):
        cv.set(x, y0, r[hi])
        cv.set(x, y1, r[lo])
    for y in range(y0, y1 + 1):
        cv.set(x0, y, r[hi])
        cv.set(x1, y, r[lo])
    cv.set(x1, y0, r[base])
    cv.set(x0, y1, r[base])
    if inner:
        for x in range(x0 + 1, x1):
            cv.set(x, y0 + 1, r[hi - 1])
            cv.set(x, y1 - 1, r[lo + 1])
        for y in range(y0 + 1, y1):
            cv.set(x0 + 1, y, r[hi - 1])
            cv.set(x1 - 1, y, r[lo + 1])


def slab(mid, seed, base=3):
    r = ramp(mid)
    m = mottle(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, r[base + m[y][x]])
    return cv, r


def polished_guild_stone():
    """A polished sandstone slab: a soft bevel, faint cloudy patches, one hairline joint across the middle."""
    cv, r = slab(GUILD, "pgs")
    bevel(cv, r, 0, 0, 15, 15, 5, 1, 3, inner=False)
    for x in range(1, 15):
        cv.set(x, 7, r[2])
        cv.set(x, 8, r[4])
    return cv


def carved_guild_stone_top():
    """Carved top: a sunk square panel framed by a raised border, a small lozenge carved in the middle."""
    cv, r = slab(GUILD, "cgt")
    bevel(cv, r, 0, 0, 15, 15, 5, 1, 3, inner=False)
    # sunk panel: shadow on its top-left wall, light on its bottom-right wall
    for i in range(3, 13):
        cv.set(i, 3, r[1])
        cv.set(3, i, r[1])
        cv.set(i, 12, r[5])
        cv.set(12, i, r[5])
    for y in range(4, 12):
        for x in range(4, 12):
            cv.set(x, y, r[2] if (x + y) % 7 else r[3])
    for y in range(16):
        for x in range(16):
            d = abs(x - 7.5) + abs(y - 7.5)
            if 2.0 <= d < 3.0:
                cv.set(x, y, r[1] if x + y < 15 else r[4])
            elif d < 2.0:
                cv.set(x, y, r[3])
    return cv


def guild_tiles():
    """Guild floor tiles: a diagonal checker of cream and honey sandstone squares, 4 px each, with fine grout."""
    a = ramp(GUILD, -0.6, 0.6)
    b = ramp(K.shift(GUILD, -0.18), -0.6, 0.5)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            tx, ty = x // 4, y // 4
            px, py = x % 4, y % 4
            r = a if (tx + ty) % 2 == 0 else b
            if px == 3 or py == 3:
                c = r[1]
            elif px == 0 or py == 0:
                c = r[5] if (tx + ty) % 2 == 0 else r[4]
            else:
                c = r[3]
            cv.set(x, y, c)
    for x, y in ((1, 1), (9, 5), (5, 13), (13, 9)):  # a little wear on a few cream tiles
        cv.set(x, y, a[4])
        cv.set(x + 1, y, a[4])
    return cv


def rust_rock():
    """Rust rock: banded sedimentary rock, warm iron-red layers with darker partings and a few oxide streaks
    running down."""
    r = ramp(RUST, -0.72, 0.56)
    f = K.field("rustrock", ((8, 0.5), (4, 0.35), (2, 0.15)), 0.03)
    # stretch sideways into layers
    f = [[(f[y][x] + f[y][(x + 2) % 16] + f[y][(x + 4) % 16] + f[y][(x + 6) % 16]) / 4 for x in range(16)]
         for y in range(16)]
    lo = min(min(row) for row in f)
    hi = max(max(row) for row in f)
    idx = K.despeckle(K.quantize([[(v - lo) / (hi - lo) for v in row] for row in f], (0.18, 0.42, 0.66, 0.86)), 2)
    cv = K.paint([[v + 1 for v in row] for row in idx], r)
    for y in (4, 11):  # bedding partings
        for x in range(16):
            if (x * 5 + y) % 9 not in (0, 1):
                cv.set(x, y, r[0] if idx[y][x] < 2 else r[1])
    ochre = K.shift((196, 120, 52), 0.1)
    for x, y0, n in ((3, 5, 3), (12, 0, 3), (8, 12, 3)):  # oxide streaks
        for i in range(n):
            cv.set(x, (y0 + i) % 16, ochre if i == 0 else K.mix(ochre, r[2], 0.4))
    return cv


def polished_rust_rock():
    """Polished rust rock: the bands smoothed into a cut face with a bevel."""
    cv = rust_rock()
    r = ramp(RUST, -0.72, 0.56)
    bevel(cv, r, 0, 0, 15, 15, 5, 0, 3)
    return cv


def gilded_trim_top():
    """Gilded trim top: a polished dark ember-stone slab with a gold inlay line and corner studs."""
    cv, r = slab(EMBER_STONE, "gtt", base=2)
    g = ramp(GOLD, -0.6, 0.6)
    bevel(cv, r, 0, 0, 15, 15, 4, 0, 2, inner=False)
    for i in range(3, 13):
        cv.set(i, 3, g[4])
        cv.set(3, i, g[4])
        cv.set(i, 12, g[1])
        cv.set(12, i, g[1])
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        cv.set(x, y, g[5])
        cv.set(x + 1, y, g[3])
        cv.set(x, y + 1, g[3])
        cv.set(x + 1, y + 1, g[0])
    return cv


FACES = {
    "polished_guild_stone": polished_guild_stone, "carved_guild_stone_top": carved_guild_stone_top,
    "guild_tiles": guild_tiles, "rust_rock": rust_rock, "polished_rust_rock": polished_rust_rock,
    "gilded_trim_top": gilded_trim_top,
}
