"""Block faces of the guild utility blocks, boss altars and metal storage blocks (ores: wf/texore.py), in the shaded
steampunk style of texgen_steam (brass frames, rivets, bevels, aether and amber glows; STYLE_STEAMPUNK.md).

Every function returns a 16x16 Canvas; gen_textures.block_textures() and metal_textures() call them.
"""
import math
import random

from .png import Canvas
from .texgen import bricks, mix
from .texkit import tmul as mul  # hue-shifted shading
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


# ------------------------------------------------------------------ metal storage and raw blocks
def _metal_ramp(palette):
    """Six hue-shifted tones (0 deepest .. 5 brightest) around a metal palette's mid tone."""
    from . import texkit as K
    return K.ramp(tuple(palette[1][:3]), 6, -0.72, 0.7)


def _framed(r, seed, field=2):
    """A bevelled block face: lit top/left rim, shaded bottom/right rim, a field of tone ``field`` with a few
    brushed streaks."""
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, r[field])
    # brushed streaks: a few horizontal 3-6 px runs one tone up, clustered rather than per pixel
    rng = random.Random(f"brush{seed}")
    for _ in range(5):
        x, y, n = rng.randrange(2, 12), rng.randrange(2, 14), rng.randint(3, 6)
        for i in range(n):
            if x + i < 14:
                cv.set(x + i, y, r[field + 1])
    for i in range(16):
        cv.set(i, 0, r[5])
        cv.set(0, i, r[5])
        cv.set(i, 15, r[0])
        cv.set(15, i, r[0])
    for i in range(1, 15):
        cv.set(i, 1, r[4])
        cv.set(1, i, r[4])
        cv.set(i, 14, r[1])
        cv.set(14, i, r[1])
    cv.set(15, 0, r[3])
    cv.set(0, 15, r[3])
    return cv


def _rivet6(cv, x, y, r):
    """A 2x2 domed rivet: bright cap, mid sides, deep shadow pixel bottom-right."""
    cv.set(x, y, r[5])
    cv.set(x + 1, y, r[3])
    cv.set(x, y + 1, r[3])
    cv.set(x + 1, y + 1, r[0])


def _inset(cv, r, x0, y0, x1, y1, raised=True):
    hi, lo = (r[4], r[1]) if raised else (r[1], r[4])
    for x in range(x0, x1 + 1):
        cv.set(x, y0, hi)
        cv.set(x, y1, lo)
    for y in range(y0, y1 + 1):
        cv.set(x0, y, hi)
        cv.set(x1, y, lo)


def storage_block(palette, kind, seed):
    """Metal storage blocks, each with its own construction: brass a riveted boss plate, zinc a galvanised sheet with
    its crystal spangle, mithril raised filigree, orichalcum a hammered plate, aether a cut crystal."""
    r = _metal_ramp(palette)
    light, mid, dark, outline = (tuple(c[:3]) for c in palette)
    if kind == "brass":
        cv = _framed(r, seed)
        # raised centre boss with a recessed groove round it and a stamped cog-tooth ring
        _inset(cv, r, 3, 3, 12, 12, raised=False)
        _inset(cv, r, 4, 4, 11, 11, raised=True)
        for y in range(5, 11):
            for x in range(5, 11):
                cv.set(x, y, r[3] if (x + y) < 16 else r[2])
        for x, y in ((7, 5), (8, 5), (5, 7), (5, 8)):
            cv.set(x, y, r[4])
        for x, y in ((7, 10), (8, 10), (10, 7), (10, 8)):
            cv.set(x, y, r[1])
        cv.set(7, 7, r[1])
        cv.set(8, 8, r[5])
        for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
            _rivet6(cv, x, y, r)
        return cv
    if kind == "zinc":
        # galvanised spangle: big flat crystal facets of slightly different greys, crisp edges between them
        rng = random.Random(seed)
        pts = [(rng.uniform(0, 16), rng.uniform(0, 16), rng.choice((2, 3, 3, 4))) for _ in range(13)]
        cv = Canvas(16, 16)
        for y in range(16):
            for x in range(16):
                best = sorted(((min(abs(x - px), 16 - abs(x - px)) ** 2 + min(abs(y - py), 16 - abs(y - py)) ** 2, t)
                               for px, py, t in pts))
                edge = best[1][0] - best[0][0] < 2.2
                cv.set(x, y, r[best[0][1] - 1] if edge and best[0][1] > best[1][1] else r[best[0][1]])
        for i in range(16):
            cv.set(i, 0, r[5])
            cv.set(0, i, r[5])
            cv.set(i, 15, r[0])
            cv.set(15, i, r[0])
        for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
            _rivet6(cv, x, y, r)
        return cv
    if kind == "mithril":
        # a pale plate with a raised rhombus of filigree and a four-point star in the middle
        cv = _framed(r, seed, field=2)
        for y in range(2, 14):
            for x in range(2, 14):
                d = abs(x - 7.5) + abs(y - 7.5)
                up, left = y < 7.5, x < 7.5
                if 5.0 <= d < 6.0:
                    cv.set(x, y, r[5] if up and left else r[1] if not up and not left else r[4] if up else r[3])
                elif 6.0 <= d < 7.0:
                    cv.set(x, y, r[0] if not up and not left else r[1] if not up or not left else r[2])
                elif d < 5.0:
                    cv.set(x, y, r[3])
        star = {(7, 4): 5, (8, 4): 4, (7, 5): 5, (8, 5): 3, (4, 7): 5, (5, 7): 5, (4, 8): 4, (5, 8): 3,
                (10, 7): 4, (11, 7): 3, (10, 8): 2, (11, 8): 1, (7, 10): 4, (8, 10): 2, (7, 11): 3, (8, 11): 1,
                (6, 6): 5, (7, 6): 5, (8, 6): 4, (9, 6): 3, (6, 7): 5, (7, 7): 5, (8, 7): 4, (9, 7): 2,
                (6, 8): 4, (7, 8): 4, (8, 8): 3, (9, 8): 1, (6, 9): 3, (7, 9): 2, (8, 9): 1, (9, 9): 1}
        for (x, y), t in star.items():
            cv.set(x, y, r[t])
        cv.set(7, 7, (255, 255, 255))
        for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
            _rivet6(cv, x, y, r)
        return cv
    if kind == "orichalcum":
        # a hammered bowl: one big concave dish in the plate (shadow on its upper-left wall, light caught on the
        # lower-right wall) and four small dents round it
        cv = _framed(r, seed, field=3)
        for y in range(2, 14):
            for x in range(2, 14):
                dx, dy = x + 0.5 - 8, y + 0.5 - 8
                d = math.hypot(dx, dy)
                if d <= 5.2:
                    k = (dx + dy) / (d * 1.41) if d else 0
                    if d > 4.2:
                        cv.set(x, y, r[0] if k < -0.3 else r[5] if k > 0.3 else r[2])
                    elif d > 3.0:
                        cv.set(x, y, r[1] if k < -0.2 else r[4] if k > 0.4 else r[2])
                    else:
                        cv.set(x, y, r[2] if k < 0 else r[3])
        for mx, my in ((3, 3), (11, 3), (3, 11), (11, 11)):
            cv.set(mx, my, r[1])
            cv.set(mx + 1, my, r[2])
            cv.set(mx, my + 1, r[2])
            cv.set(mx + 1, my + 1, r[5])
        cv.set(6, 10, r[5])
        cv.set(10, 6, r[5])
        return cv
    # cut-crystal block: a faceted diamond set in a bevelled frame, each facet one flat tone, bright edges
    cv2 = Canvas(16, 16)
    glint = mix(r[5], (255, 255, 255), 0.5)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            inner = abs(dx) + abs(dy) < 5.0
            if abs(abs(dx) + abs(dy) - 5.0) < 0.6 or (inner and (abs(dx - dy) < 0.6 or abs(dx + dy) < 0.6)):
                c = r[5] if dy < 0 or dx < 0 else r[3]
            elif inner:
                c = r[5] if dy < 0 and abs(dx) < -dy else r[3] if dx < 0 else r[1] if dy > 0 else r[2]
            else:
                c = r[4] if dy < -abs(dx) else r[3] if dx < -abs(dy) else (r[0] if dy > abs(dx) else r[1])
            cv2.set(x, y, c)
    for i in range(16):
        cv2.set(i, 0, r[5])
        cv2.set(0, i, r[5])
        cv2.set(i, 15, mix(r[0], outline, 0.4))
        cv2.set(15, i, mix(r[0], outline, 0.4))
    for x, y in ((6, 4), (7, 5)):
        cv2.set(x, y, glint)
    return cv2


def raw_block(palette, seed):
    """Raw ore block: rounded lumps packed together, each shaded as a lit ball from the top-left on a hue-shifted
    ramp, with deep crevices between them."""
    r = _metal_ramp(palette)
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, r[0])
    lumps = []
    for gy in range(3):
        for gx in range(3):
            lumps.append((gx * 5.33 + 2.6 + (2.6 if gy % 2 else 0) + rng.uniform(-0.8, 0.8),
                          gy * 5.33 + 2.6 + rng.uniform(-0.7, 0.7), rng.uniform(2.9, 3.5)))
    rng.shuffle(lumps)
    for cx, cy, rad in lumps:
        bump = rng.choice((0, 0, 0, -1))
        for y in range(16):
            for x in range(16):
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        dx, dy = x + 0.5 - cx - ox, y + 0.5 - cy - oy
                        d2 = dx * dx + dy * dy
                        if d2 <= rad * rad:
                            k = (dx + dy) / (rad * 1.41)
                            t = 5 if k < -0.68 and d2 > rad * rad * 0.25 else 4 if k < -0.25 else 3 if k < 0.3 else 2 if k < 0.7 else 1
                            cv.set(x, y, r[max(1, t + bump)])
    return cv
