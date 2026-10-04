"""Block faces of the guild utility blocks, boss altars, lithite ore and metal storage blocks, in the shaded
steampunk style of texgen_steam (brass frames, rivets, bevels, aether and amber glows; STYLE_STEAMPUNK.md).

Every function returns a 16x16 Canvas; gen_textures.block_textures() and metal_textures() call them.
"""
import math
import random

from .png import Canvas
from .texgen import bricks, mix, mul
from .texgen_steam import AETHER, BRASS, DARK_IRON, MAHOGANY, VERDIGRIS, _base, _bevel, _rivet

STONE = (124, 124, 130)
OAK = (150, 106, 62)


def _px(cv, pts, c):
    for x, y in pts:
        if 0 <= x < 16 and 0 <= y < 16:
            cv.set(x, y, c)


def _glow(cv, x, y, core, glow, r=1):
    """A glowing pixel with a soft halo blended into its neighbours."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = x + dx, y + dy
            if (dx or dy) and 0 <= nx < 16 and 0 <= ny < 16 and abs(dx) + abs(dy) <= r:
                cv.set(nx, ny, mix(cv.get(nx, ny), glow, 0.35))
    cv.set(x, y, core)


def _stone(base, seed, grain=0.06):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(base, 1 + rng.uniform(-grain, grain)))
    # a few darker flecks like vanilla stone
    for _ in range(14):
        x, y = rng.randrange(16), rng.randrange(16)
        cv.set(x, y, mul(base, 0.84))
    return cv


def _brass_band(cv, y, h=2, rivets=(2, 7, 12)):
    for x in range(16):
        cv.set(x, y, mul(BRASS, 1.3))
        for k in range(1, h):
            cv.set(x, y + k, mul(BRASS, 1.0 if k < h - 1 else 0.7))
    for x in rivets:
        cv.set(x, y + h // 2, mul(BRASS, 1.6))
        cv.set(x + 1, y + h // 2, mul(BRASS, 0.6))


# ------------------------------------------------------------------ waystone
def waystone_side():
    """Two ashlar courses with a carved channel holding a glowing aether rune, brass bands top and bottom."""
    cv = _stone(STONE, 1)
    for x in range(16):
        cv.set(x, 8, mul(STONE, 0.62))
        cv.set(x, 9, mul(STONE, 1.16))
    _bevel(cv, STONE, 1.15, 0.7)
    # channel
    for y in range(3, 13):
        cv.set(5, y, mul(STONE, 0.55))
        cv.set(10, y, mul(STONE, 1.2))
        for x in range(6, 10):
            cv.set(x, y, mul(STONE, 0.42))
    glyph = [(7, 4), (8, 4), (7, 5), (6, 6), (7, 6), (8, 6), (9, 6), (7, 7), (8, 8), (8, 9), (7, 10), (6, 10),
             (9, 10), (8, 11)]
    for x, y in glyph:
        cv.set(x, y, mix(AETHER, (255, 255, 255), 0.25))
    for x, y in ((7, 4), (6, 6), (8, 9), (7, 10)):
        cv.set(x, y, (230, 252, 255))
    _brass_band(cv, 0, 2, rivets=(1, 7, 13))
    _brass_band(cv, 14, 2, rivets=(1, 7, 13))
    return cv


def waystone_top():
    """Polished cap: a brass ring around a dark well, an aether compass star glowing in it."""
    cv = _stone(mul(STONE, 1.12), 2, 0.04)
    _bevel(cv, mul(STONE, 1.12), 1.12, 0.72)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if 4.6 <= d < 6.2:
                cv.set(x, y, mul(BRASS, 1.25 if (x + y) < 15 else 0.8))
            elif d < 4.6:
                cv.set(x, y, mul(DARK_IRON, 0.9 + 0.1 * (d / 4.6)))
    star = {(7, 3): 0, (8, 3): 0, (7, 12): 0, (8, 12): 0, (3, 7): 0, (3, 8): 0, (12, 7): 0, (12, 8): 0}
    for i in range(4, 12):
        star[(i, 7 if i < 8 else 8)] = 1
        star[(7 if i < 8 else 8, i)] = 1
    for (x, y), _ in star.items():
        cv.set(x, y, mix(AETHER, (255, 255, 255), 0.2))
    for x, y in ((7, 7), (8, 8), (7, 8), (8, 7)):
        cv.set(x, y, (236, 254, 255))
    for x, y in ((5, 5), (10, 5), (5, 10), (10, 10)):
        cv.set(x, y, mul(AETHER, 0.55))
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, BRASS)
    return cv


# ------------------------------------------------------------------ guild utility blocks
def _planks(base, seed, vertical=False, boards=4):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    w = 16 // boards
    for b in range(boards):
        tint = 1 + rng.uniform(-0.08, 0.08)
        for i in range(w):
            for j in range(16):
                x, y = (b * w + i, j) if vertical else (j, b * w + i)
                f = tint * (1 + rng.uniform(-0.04, 0.04))
                if i == w - 1:
                    f *= 0.62
                elif i == 0:
                    f *= 1.12
                if rng.random() < 0.06:
                    f *= 0.86
                cv.set(x, y, mul(base, f))
    return cv


def _bracket(cv, x0, y0, sx, sy):
    """L-shaped brass corner bracket with a rivet, pointing (sx, sy) into the face."""
    for k in range(4):
        cv.set(x0 + sx * k, y0, mul(BRASS, 1.25 if k < 3 else 0.9))
        cv.set(x0, y0 + sy * k, mul(BRASS, 1.1 if k < 3 else 0.8))
    cv.set(x0 + sx, y0 + sy, mul(BRASS, 0.75))
    cv.set(x0, y0, mul(BRASS, 1.5))


def sorting_chest_side():
    """Mahogany crate with brass corner brackets and a brass plate stamped with two sorting arrows."""
    cv = _planks(MAHOGANY, 3, vertical=True)
    _bevel(cv, mul(MAHOGANY, 0.8), 1.2, 0.55)
    for (x, y, sx, sy) in ((0, 0, 1, 1), (15, 0, -1, 1), (0, 15, 1, -1), (15, 15, -1, -1)):
        _bracket(cv, x, y, sx, sy)
    for y in range(4, 12):
        for x in range(2, 14):
            edge = x in (2, 13) or y in (4, 11)
            cv.set(x, y, mul(BRASS, (1.3 if x == 2 or y == 4 else 0.7) if edge else 1.0))
    # two arrows, one up and one down: items go in, items come out
    up = [(5, 5), (4, 6), (5, 6), (6, 6), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (5, 8), (5, 9), (5, 10)]
    down = [(10, 5), (10, 6), (10, 7), (8, 8), (9, 8), (10, 8), (11, 8), (12, 8), (9, 9), (10, 9), (11, 9), (10, 10)]
    for x, y in up + down:
        cv.set(x, y, mul(DARK_IRON, 0.8))
        if (x + 1, y + 1) not in up + down and x < 13 and y < 11:
            cv.set(x + 1, y + 1, mul(BRASS, 1.35))
    return cv


def sorting_chest_top():
    """Lid: planks inside a brass frame, a brass label plate and two hinges."""
    cv = _planks(MAHOGANY, 4)
    for i in range(16):
        for k in (0, 1):
            c = mul(BRASS, 1.25 if k == 0 else 0.85)
            cv.set(i, k, c if k == 0 else mul(BRASS, 1.05))
            cv.set(k, i, mul(BRASS, 1.2))
            cv.set(i, 15 - k, mul(BRASS, 0.7 if k == 0 else 0.9))
            cv.set(15 - k, i, mul(BRASS, 0.7 if k == 0 else 0.9))
    for x in range(5, 11):
        cv.set(x, 7, mul(BRASS, 1.2))
        cv.set(x, 8, mul(BRASS, 0.8))
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, BRASS)
    return cv


def guild_terminal_front():
    """A brass-bezelled aether screen with glowing ledger lines, a row of brass keys and a little gauge."""
    cv = _base(DARK_IRON, 5, 0.05)
    _bevel(cv, mul(DARK_IRON, 1.3), 1.25, 0.6)
    for y in range(1, 11):
        for x in range(2, 14):
            edge = x in (2, 13) or y in (1, 10)
            if edge:
                cv.set(x, y, mul(BRASS, 1.3 if (x == 2 or y == 1) else 0.75))
            else:
                cv.set(x, y, (16, 40, 44) if y % 2 else (20, 48, 52))
    lines = [(4, 3, 7), (4, 5, 9), (4, 7, 5), (10, 7, 2)]
    for x0, y, n in lines:
        for x in range(x0, x0 + n):
            cv.set(x, y, mix(AETHER, (255, 255, 255), 0.15) if x == x0 else mul(AETHER, 0.85))
    cv.set(12, 2, (220, 250, 255))
    cv.set(3, 2, (60, 90, 96))
    for x in range(3, 13, 2):
        cv.set(x, 12, mul(BRASS, 1.35))
        cv.set(x, 13, mul(BRASS, 0.7))
    _rivet(cv, 1, 13, BRASS)
    _rivet(cv, 13, 13, BRASS)
    return cv


def guild_terminal_side():
    """Riveted dark iron casing with a mahogany panel and a vent."""
    cv = _base(DARK_IRON, 6, 0.05)
    _bevel(cv, mul(DARK_IRON, 1.3), 1.25, 0.6)
    for y in range(3, 13):
        for x in range(3, 13):
            cv.set(x, y, mul(MAHOGANY, 1.0 + (0.08 if x % 3 == 0 else 0) - (0.2 if x % 3 == 2 else 0)))
    for i in range(3, 13):
        cv.set(i, 2, mul(DARK_IRON, 0.6))
        cv.set(2, i, mul(DARK_IRON, 0.6))
        cv.set(i, 13, mul(DARK_IRON, 1.5))
        cv.set(13, i, mul(DARK_IRON, 1.5))
    for x in range(5, 11):
        cv.set(x, 6, mul(DARK_IRON, 0.5))
        cv.set(x, 9, mul(DARK_IRON, 0.5))
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, BRASS)
    return cv


def compacting_crate_side():
    """Oak crate: three boards in an iron-banded frame, a diagonal brace and corner rivets."""
    cv = _planks(OAK, 31, boards=4)
    for i in range(16):
        for k in (0, 15):
            cv.set(i, k, mul(DARK_IRON, 1.3 if k == 0 else 0.9))
            cv.set(k, i, mul(DARK_IRON, 1.3 if k == 0 else 0.9))
    for i in range(1, 15):
        cv.set(i, 15 - i, mul(OAK, 1.18))
        if i < 14:
            cv.set(i + 1, 15 - i, mul(OAK, 0.66))
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, (170, 170, 178))
    return cv


def compacting_crate_front():
    """Iron-framed oak face with a deep recess (the stored item is drawn in it) and a brass count plate."""
    cv = _planks(OAK, 32, boards=4)
    for i in range(16):
        for k in (0, 15):
            cv.set(i, k, mul(DARK_IRON, 1.3 if k == 0 else 0.9))
            cv.set(k, i, mul(DARK_IRON, 1.3 if k == 0 else 0.9))
    for y in range(2, 12):
        for x in range(3, 13):
            cv.set(x, y, mul((58, 40, 24), 1.0 + 0.05 * ((x + y) % 2)))
    for i in range(3, 13):
        cv.set(i, 2, mul((40, 28, 16), 1.0))
        cv.set(3, min(11, i - 1), mul((40, 28, 16), 1.0))
        cv.set(i, 11, mul(OAK, 1.2))
        cv.set(12, min(11, i - 1), mul(OAK, 1.2))
    for x in range(4, 12):
        cv.set(x, 13, mul(BRASS, 1.2))
        cv.set(x, 14, mul(BRASS, 0.75))
    _rivet(cv, 1, 1, (170, 170, 178))
    _rivet(cv, 13, 1, (170, 170, 178))
    return cv


def grave():
    """Weathered gravestone slab: an engraved cross with a lit edge, cracks and lichen."""
    rng = random.Random(7)
    base = (132, 132, 128)
    cv = _stone(base, 7, 0.07)
    _bevel(cv, base, 1.15, 0.65)
    cross = [(x, y) for y in range(3, 13) for x in (7, 8)] + [(x, y) for x in range(5, 11) for y in (5, 6)]
    for x, y in cross:
        cv.set(x, y, mul(base, 0.5))
    for x, y in cross:
        if (x + 1, y) not in cross:
            cv.set(x + 1, y, mul(base, 1.22))
        if (x, y + 1) not in cross:
            cv.set(x, y + 1, mul(base, 1.18))
    for _ in range(10):
        x, y = rng.randrange(1, 15), rng.randrange(1, 15)
        cv.set(x, y, rng.choice(((96, 118, 70), (118, 132, 80), (84, 100, 62))))
    for x, y in ((2, 12), (3, 13), (3, 14), (12, 2), (13, 3)):
        cv.set(x, y, mul(base, 0.62))
    return cv


def sealed_bars():
    """Cutout: dark iron bars with rounded shading, two riveted cross bars and an aether seal line."""
    cv = Canvas(16, 16)
    for x0 in (1, 5, 9, 13):
        for y in range(16):
            cv.set(x0, y, mul(DARK_IRON, 1.9))
            cv.set(x0 + 1, y, mul(DARK_IRON, 1.15))
    for y0 in (2, 12):
        for x in range(16):
            cv.set(x, y0, mul(BRASS, 1.2))
            cv.set(x, y0 + 1, mul(BRASS, 0.7))
        for x0 in (1, 5, 9, 13):
            cv.set(x0, y0, mul(BRASS, 1.6))
    for x0 in (1, 5, 9, 13):
        for y in (6, 7, 8, 9):
            cv.set(x0 + 1, y, mix(mul(DARK_IRON, 1.15), VERDIGRIS, 0.7))
        cv.set(x0 + 1, 7, mix(AETHER, (255, 255, 255), 0.3))
    return cv


# ------------------------------------------------------------------ altars and seals
def _altar_side(stone, mortar, glow, seed):
    cv = bricks(stone, mortar, seed=seed, rows=4, brick_w=8, var=0.08, bevel=0.14)
    # carved central panel with a rune glyph
    for y in range(4, 12):
        for x in range(4, 12):
            cv.set(x, y, mul(stone, 0.62))
    for i in range(4, 12):
        cv.set(i, 3, mul(stone, 1.25))
        cv.set(3, i, mul(stone, 1.25))
        cv.set(i, 12, mul(stone, 0.55))
        cv.set(12, i, mul(stone, 0.55))
    glyph = [(7, 5), (8, 5), (6, 6), (9, 6), (7, 7), (8, 7), (7, 8), (8, 8), (6, 9), (9, 9), (5, 10), (10, 10)]
    for x, y in glyph:
        _glow(cv, x, y, mix(glow, (255, 255, 255), 0.4), glow)
    for x in range(16):
        cv.set(x, 0, mul(stone, 1.3))
        cv.set(x, 15, mul(stone, 0.5))
    return cv


def _altar_top(stone, mortar, glow, seed):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(stone, 1.05 + rng.uniform(-0.05, 0.05)))
    _bevel(cv, stone, 1.25, 0.55)
    for i in range(2, 14):
        cv.set(i, 2, mul(mortar, 1.0))
        cv.set(2, i, mul(mortar, 1.0))
        cv.set(i, 13, mul(stone, 1.25))
        cv.set(13, i, mul(stone, 1.25))
    for a in range(0, 360, 10):
        x = 7.5 + 4.2 * math.cos(math.radians(a))
        y = 7.5 + 4.2 * math.sin(math.radians(a))
        cv.set(int(round(x)), int(round(y)), mix(glow, (255, 255, 255), 0.2))
    for x, y in ((7, 7), (8, 8), (7, 8), (8, 7)):
        _glow(cv, x, y, mix(glow, (255, 255, 255), 0.6), glow)
    for x, y in ((7, 4), (4, 7), (11, 8), (8, 11)):
        cv.set(x, y, mul(glow, 0.8))
    return cv


WARDEN_STONE, WARDEN_MORTAR, WARDEN_GLOW = (52, 112, 104), (24, 58, 58), (120, 255, 226)
VOID_STONE, VOID_MORTAR, VOID_GLOW = (50, 30, 70), (20, 10, 32), (236, 150, 255)
SEAL_STONE, SEAL_MORTAR, SEAL_GLOW = (40, 37, 44), (18, 16, 20), (110, 230, 255)


def warden_altar_side():
    return _altar_side(WARDEN_STONE, WARDEN_MORTAR, WARDEN_GLOW, 8)


def warden_altar_top():
    return _altar_top(WARDEN_STONE, WARDEN_MORTAR, WARDEN_GLOW, 9)


def void_altar_side():
    return _altar_side(VOID_STONE, VOID_MORTAR, VOID_GLOW, 10)


def void_altar_top():
    return _altar_top(VOID_STONE, VOID_MORTAR, VOID_GLOW, 12)


def boss_seal_side():
    """Black seal stone in a gilded frame, a soul-fire rune burning in its carved panel."""
    cv = _altar_side(SEAL_STONE, SEAL_MORTAR, SEAL_GLOW, 21)
    for x in range(16):
        cv.set(x, 0, mul(BRASS, 1.35))
        cv.set(x, 1, mul(BRASS, 0.85))
        cv.set(x, 14, mul(BRASS, 1.1))
        cv.set(x, 15, mul(BRASS, 0.6))
    return cv


def boss_seal_top():
    cv = _altar_top(SEAL_STONE, SEAL_MORTAR, SEAL_GLOW, 23)
    for i in range(16):
        cv.set(i, 0, mul(BRASS, 1.35))
        cv.set(0, i, mul(BRASS, 1.35))
        cv.set(i, 15, mul(BRASS, 0.6))
        cv.set(15, i, mul(BRASS, 0.6))
    return cv


# ------------------------------------------------------------------ ores
def crystal_ore(host, seed, light, mid, dark, deep=False):
    """Host stone with five small crystal clusters: lit facet, mid body, dark base, a shadow in the stone."""
    rng = random.Random(seed)
    cv = _stone(host, seed, 0.07)
    if deep:
        for y in range(0, 16, 4):
            for x in range(16):
                if rng.random() < 0.5:
                    cv.set(x, y, mul(host, 0.86))
    spots = [(2, 2), (9, 1), (12, 7), (4, 9), (9, 12)]
    for cx, cy in spots:
        cx += rng.randint(0, 1)
        cy += rng.randint(0, 1)
        shape = [(0, 1), (1, 0), (1, 1), (2, 1), (1, 2)] if rng.random() < 0.5 else [(0, 0), (1, 0), (0, 1), (1, 1), (2, 2)]
        cells = {(cx + dx, cy + dy) for dx, dy in shape}
        for x, y in cells:
            for sx, sy in ((x + 1, y), (x, y + 1), (x + 1, y + 1)):
                if (sx, sy) not in cells and 0 <= sx < 16 and 0 <= sy < 16:
                    cv.set(sx, sy, mul(host, 0.5))
        for x, y in cells:
            if 0 <= x < 16 and 0 <= y < 16:
                up = (x, y - 1) in cells
                left = (x - 1, y) in cells
                cv.set(x, y, light if not (up or left) else dark if (x + 1, y) not in cells and (x, y + 1) not in cells else mid)
    return cv


# ------------------------------------------------------------------ metal storage and raw blocks
def storage_block(palette, kind, seed):
    """Metal storage block faces: brass/zinc riveted plates, mithril filigree, orichalcum hammered plate,
    aether faceted crystal."""
    light, mid, dark, outline = (tuple(c[:3]) for c in palette)
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(mid, 1 + rng.uniform(-0.025, 0.025)))
    for i in range(16):
        cv.set(i, 0, light)
        cv.set(0, i, light)
        cv.set(i, 15, mix(dark, outline, 0.4))
        cv.set(15, i, mix(dark, outline, 0.4))
    for i in range(1, 15):
        cv.set(i, 1, mix(light, mid, 0.5))
        cv.set(1, i, mix(light, mid, 0.5))
        cv.set(i, 14, dark)
        cv.set(14, i, dark)
    if kind in ("brass", "zinc"):
        for x in range(2, 14):
            cv.set(x, 7, dark)
            cv.set(x, 8, light)
        for x, y in ((3, 3), (11, 3), (3, 11), (11, 11)):
            cv.set(x, y, mix(light, (255, 255, 255), 0.4))
            cv.set(x + 1, y, mid)
            cv.set(x, y + 1, mid)
            cv.set(x + 1, y + 1, dark)
        for x, y in ((7, 3), (7, 11)):
            cv.set(x, y, light)
            cv.set(x + 1, y + 1, dark)
    elif kind == "mithril":
        # inlaid filigree: a diamond lattice of bright lines with a star at its heart
        def lattice(x, y):
            return (x + y) % 6 == 3 or (x - y) % 6 == 0
        for y in range(2, 14):
            for x in range(2, 14):
                if lattice(x, y):
                    cv.set(x, y, light)
                elif lattice(x - 1, y - 1) and x > 2 and y > 2:
                    cv.set(x, y, mix(mid, dark, 0.5))
        cv.set(7, 7, mix(light, (255, 255, 255), 0.6))
        cv.set(8, 8, mix(light, (255, 255, 255), 0.6))
    elif kind == "orichalcum":
        # hammered plate: dimples lit from the top-left
        for cy in (4, 8, 12):
            for cx in (4, 8, 12):
                ox = cx + (2 if cy == 8 else 0) - 1
                if 2 <= ox <= 13:
                    cv.set(ox, cy - 1, dark)
                    cv.set(ox - 1, cy - 1, mix(dark, mid, 0.5))
                    cv.set(ox + 1, cy, light)
                    cv.set(ox, cy, mix(light, mid, 0.4))
    else:
        # cut-crystal block: a faceted diamond set in a bevelled frame, each facet a flat tone, bright edges
        cv2 = Canvas(16, 16)
        glint = mix(light, (255, 255, 255), 0.5)
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7.5, y - 7.5
                inner = abs(dx) + abs(dy) < 5.0
                if abs(abs(dx) + abs(dy) - 5.0) < 0.6 or (inner and (abs(dx - dy) < 0.6 or abs(dx + dy) < 0.6)):
                    c = mix(light, mid, 0.2)
                elif inner:
                    c = light if dy < 0 and abs(dx) < -dy else mid if dx < 0 else dark if dy > 0 else mix(mid, dark, 0.4)
                else:
                    c = mix(mid, light, 0.3) if dy < -abs(dx) else mid if dx < -abs(dy) else (
                        mix(dark, outline, 0.3) if dy > abs(dx) else mix(mid, dark, 0.6))
                cv2.set(x, y, c)
        for i in range(16):
            cv2.set(i, 0, light)
            cv2.set(0, i, light)
            cv2.set(i, 15, mix(dark, outline, 0.5))
            cv2.set(15, i, mix(dark, outline, 0.5))
        for x, y in ((6, 4), (7, 5)):
            cv2.set(x, y, glint)
        return cv2
    return cv


def raw_block(palette, seed):
    """Raw ore block: rounded lumps of ore packed together, each lit from the top-left."""
    light, mid, dark, outline = (tuple(c[:3]) for c in palette)
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mix(dark, outline, 0.35))
    lumps = []
    for gy in range(4):
        for gx in range(4):
            lumps.append((gx * 4 + 2 + (2 if gy % 2 else 0) + rng.uniform(-0.7, 0.7), gy * 4 + 2 + rng.uniform(-0.6, 0.6),
                          rng.uniform(1.9, 2.5)))
    for cx, cy, r in lumps:
        tint = 1 + rng.uniform(-0.08, 0.06)
        for y in range(16):
            for x in range(16):
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        dx, dy = x + 0.5 - cx - ox, y + 0.5 - cy - oy
                        if dx * dx + dy * dy <= r * r:
                            k = (dx + dy) / (r * 1.41)
                            c = light if k < -0.5 else mid if k < 0.3 else dark
                            cv.set(x, y, mul(c, tint))
    return cv
