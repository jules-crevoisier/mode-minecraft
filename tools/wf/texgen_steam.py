"""Steampunk block textures (brass, copper, iron, mahogany, leather), in the same 16x16 shaded style as texgen.

Palette from tools/STYLE_STEAMPUNK.md: brass, copper, verdigris, dark iron, mahogany, oxblood leather,
cream, amber glow and aether cyan.
"""
import math
import random

from .png import Canvas
from .texgen import mix, mul

BRASS = (181, 150, 66)
COPPER = (184, 115, 51)
VERDIGRIS = (67, 179, 174)
DARK_IRON = (52, 46, 46)
MAHOGANY = (107, 63, 42)
LEATHER = (110, 36, 30)
CREAM = (215, 195, 161)
AMBER = (255, 179, 71)
AETHER = (63, 208, 255)


def _base(base, seed, grain=0.04):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(base, 1 + rng.uniform(-grain, grain)))
    return cv


def _bevel(cv, base, light=1.18, dark=0.72):
    for i in range(16):
        cv.set(i, 0, mul(base, light))
        cv.set(0, i, mul(base, light))
        cv.set(i, 15, mul(base, dark))
        cv.set(15, i, mul(base, dark))
    return cv


def _rivet(cv, x, y, base):
    cv.set(x, y, mul(base, 1.45))
    cv.set(x + 1, y, mul(base, 1.1))
    cv.set(x, y + 1, mul(base, 1.0))
    cv.set(x + 1, y + 1, mul(base, 0.55))


def riveted_plate(base, seed=0, patina=None, patina_amount=0.0):
    """Two plates with a seam, rivets along the edges; optional verdigris patches."""
    rng = random.Random(seed)
    cv = _base(base, seed, 0.035)
    # brushed streaks
    for y in range(16):
        if rng.random() < 0.3:
            for x in range(16):
                cv.set(x, y, mul(cv.get(x, y), 1.05))
    _bevel(cv, base)
    for x in range(1, 15):
        cv.set(x, 7, mul(base, 0.6))
        cv.set(x, 8, mul(base, 1.2))
    for x in (2, 6, 10, 13):
        _rivet(cv, x, 2, base)
        _rivet(cv, x, 11, base)
    if patina:
        for _ in range(int(40 * patina_amount)):
            x, y = rng.randrange(16), rng.randrange(16)
            for dx, dy in ((0, 0), (1, 0), (0, 1)):
                if 0 <= x + dx < 16 and 0 <= y + dy < 16 and rng.random() < 0.8:
                    cv.set(x + dx, y + dy, mix(cv.get(x + dx, y + dy), patina, 0.55 + rng.uniform(0, 0.3)))
    return cv


def gear_panel(frame_c, gear_c, seed=0):
    """A recessed panel with a big cog and a small one meshing with it."""
    cv = _base(mul(frame_c, 0.55), seed, 0.05)
    _bevel(cv, frame_c, 1.25, 0.8)
    for i in range(1, 15):
        cv.set(i, 1, mul(frame_c, 0.9))
        cv.set(1, i, mul(frame_c, 0.9))

    def cog(cx, cy, r, teeth, phase):
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx) + phase
                tooth = math.cos(a * teeth) > 0.35
                if d <= r - 1.0 or (d <= r + 0.7 and tooth):
                    if d < 1.2:
                        cv.set(x, y, mul(gear_c, 0.35))
                    elif r * 0.38 < d < r * 0.62:
                        cv.set(x, y, mul(gear_c, 0.6))
                    else:
                        cv.set(x, y, mul(gear_c, 1.2 if dx + dy < 0 else 0.9))
    cog(6.5, 6.5, 5.0, 8, 0.0)
    cog(12.2, 12.2, 3.0, 6, 0.3)
    return cv


def pipe_casing(base, band, seed=0):
    """A vertical pipe bundle: three rounded pipes with banding clamps."""
    cv = _base(mul(base, 0.5), seed, 0.03)
    for px in (1, 6, 11):
        for x in range(px, px + 4):
            t = (x - px) / 3
            f = 0.75 + 0.55 * math.sin(t * math.pi) + (0.15 if x == px + 1 else 0)
            for y in range(16):
                cv.set(x, y, mul(base, f))
    for y in (3, 12):
        for x in range(16):
            if cv.get(x, y)[0] > base[0] * 0.6:
                cv.set(x, y, mul(band, 1.15))
                cv.set(x, y + 1, mul(band, 0.8))
    return cv


def gauge(base, face, needle, seed=0):
    """A brass-rimmed pressure gauge on an iron plate."""
    cv = riveted_plate(DARK_IRON, seed)
    cx, cy = 7.5, 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d <= 6.3:
                if d > 5.0:
                    cv.set(x, y, mul(base, 1.25 if x + y < 15 else 0.8))
                else:
                    cv.set(x, y, mul(face, 1 - d * 0.02))
    for a in range(-135, 136, 45):
        r = math.radians(a - 90)
        cv.set(int(round(cx + math.cos(r) * 4.2)), int(round(cy + math.sin(r) * 4.2)), mul(face, 0.45))
    for i in range(5):
        r = math.radians(30 - 90)
        cv.set(int(round(cx + math.cos(r) * i)), int(round(cy + math.sin(r) * i)), needle)
    cv.set(7, 7, mul(base, 0.6))
    cv.set(8, 8, mul(base, 0.6))
    return cv


def edison_lamp(frame_c, glass, filament, seed=0):
    """Iron cage over a warm glass bulb with a looped filament."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5) / 7.5
            cv.set(x, y, mix(mul(glass, 1.15), mul(glass, 0.75), min(1, d + rng.uniform(-0.04, 0.04))))
    for x, y in ((6, 4), (6, 5), (6, 6), (7, 7), (8, 7), (9, 6), (9, 5), (9, 4), (7, 8), (8, 8), (7, 9), (8, 9),
                 (7, 10), (8, 10)):
        cv.set(x, y, filament)
    for i in range(16):
        for c in (0, 15):
            cv.set(i, c, mul(frame_c, 1.1 if c == 0 else 0.75))
            cv.set(c, i, mul(frame_c, 1.1 if c == 0 else 0.75))
        cv.set(i, 5, mul(frame_c, 0.95))
        cv.set(i, 11, mul(frame_c, 0.95))
        cv.set(5, i, mul(frame_c, 0.95))
        cv.set(10, i, mul(frame_c, 0.95))
    return cv


def planks_panel(base, seed=0):
    """Mahogany wainscot: vertical boards with a raised frame and dark grooves."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for x in range(16):
        board = x // 4
        tint = 1 + (board % 2) * 0.06 - 0.03
        for y in range(16):
            grain = 0.06 * math.sin((y + board * 3) * 1.3 + x * 0.2) + rng.uniform(-0.03, 0.03)
            cv.set(x, y, mul(base, tint + grain))
        if x % 4 == 0:
            for y in range(16):
                cv.set(x, y, mul(base, 0.6))
    for x in range(16):
        cv.set(x, 0, mul(base, 1.2))
        cv.set(x, 1, mul(base, 0.8))
        cv.set(x, 14, mul(base, 1.15))
        cv.set(x, 15, mul(base, 0.65))
    return cv


def tufted_leather(base, button, seed=0):
    """Chesterfield padding: diamond tufting with buttons."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            # distance to nearest tuft on a diamond lattice (every 8 px, offset rows)
            best = 99
            for tx, ty in ((0, 0), (8, 0), (16, 0), (4, 8), (12, 8), (0, 16), (8, 16), (16, 16), (-4, 8), (20, 8)):
                best = min(best, math.hypot(x - tx, y - ty))
            f = 0.72 + min(1.0, best / 5.0) * 0.45 + rng.uniform(-0.03, 0.03)
            cv.set(x, y, mul(base, f))
    for tx, ty in ((0, 0), (8, 0), (4, 8), (12, 8), (0, 15), (8, 15), (15, 0), (15, 15)):
        if 0 <= tx < 16 and 0 <= ty < 16:
            cv.set(tx, ty, button)
    return cv


def soot_bricks(base, mortar, seed=0):
    """Smokestack bricks: small red bricks with soot stains."""
    from .texgen import bricks
    cv = bricks(base, mortar, seed=seed, rows=4, brick_w=8, var=0.12)
    rng = random.Random(seed + 1)
    for _ in range(5):
        cx, cy, r = rng.randrange(16), rng.randrange(16), rng.uniform(2, 4)
        for y in range(16):
            for x in range(16):
                d = math.hypot(min(abs(x - cx), 16 - abs(x - cx)), min(abs(y - cy), 16 - abs(y - cy)))
                if d < r:
                    cv.set(x, y, mix(cv.get(x, y), (34, 28, 28), (1 - d / r) * 0.55))
    return cv


def grate(base, seed=0):
    """Diamond-plate iron flooring (solid, so it works everywhere a full block does)."""
    cv = _base(base, seed, 0.04)
    for y in range(16):
        for x in range(16):
            if (x + 2 * (y // 4)) % 4 == 0 and y % 4 in (1, 2):
                cv.set(x, y, mul(base, 1.35))
                cv.set(min(15, x + 1), y, mul(base, 0.8))
    _bevel(cv, base)
    return cv


def aether_conduit(base, glow, seed=0):
    """Dark iron block with glowing aether channels."""
    cv = riveted_plate(base, seed)
    for i in range(3, 13):
        cv.set(i, 5, glow)
        cv.set(i, 10, glow)
        cv.set(3, 5 + (i - 3) % 6, glow)
        cv.set(12, 5 + (i - 3) % 6, glow)
    for x, y in ((3, 5), (12, 5), (3, 10), (12, 10)):
        cv.set(x, y, (255, 255, 255))
    for y in (4, 6, 9, 11):
        for x in range(3, 13):
            cv.set(x, y, mix(cv.get(x, y), glow, 0.35))
    return cv


# ---------------------------------------------------------------- machines (wf/machines.py)
def machine_frame(inner, seed=0):
    """Dark iron housing with brass corners and a recessed 12x12 window filled with ``inner``."""
    cv = _base(DARK_IRON, seed, 0.05)
    _bevel(cv, mul(DARK_IRON, 1.3), 1.25, 0.6)
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, BRASS)
    for i in range(2, 14):
        cv.set(i, 2, mul(DARK_IRON, 0.55))
        cv.set(2, i, mul(DARK_IRON, 0.55))
        cv.set(i, 13, mul(DARK_IRON, 1.4))
        cv.set(13, i, mul(DARK_IRON, 1.4))
    for y in range(3, 13):
        for x in range(3, 13):
            c = inner(x - 3, y - 3)
            if c is not None:
                cv.set(x, y, c)
    return cv


def machine_side(seed=0):
    """Machine casing: brass plate with a vent grille."""
    cv = riveted_plate(BRASS, seed)
    for y in range(4, 12):
        for x in range(4, 12):
            cv.set(x, y, mul(DARK_IRON, 0.8) if y % 2 == 0 else mul(BRASS, 0.75))
    return cv


def machine_top(seed=0):
    return riveted_plate(DARK_IRON, seed)


def _glyph(rows, colors, back):
    rows = [r.ljust(10, ".") for r in rows]

    def inner(x, y):
        ch = rows[y][x] if y < len(rows) else "."
        return colors[ch] if ch != "." else back(x, y)
    return inner


def _dark_back(base=(30, 26, 26)):
    return lambda x, y: mul(base, 1.0 + ((x * 7 + y * 13) % 5 - 2) * 0.03)


MACHINE_GLYPHS = {
    # 10x10 glyphs drawn inside the window; letters map to colours below
    "harvester": ["..s.....s.", ".ss....ss.", "sss...sss.", ".bb...bb..", "..bb.bb...",
                  "...bbb....", "..wwwww...", ".w.w.w.w..", "w..w.w..w.", "...w.w...."],
    "sprinkler": ["....bb....", "...bccb...", "..bccccb..", "...bccb...", "....bb....",
                  ".d..bb..d.", "d.d.bb.d.d", "..d.bb.d..", ".d..bb..d.", "....bb...."],
    "vacuum": ["..aaaaaa..", ".a......a.", "a..aaaa..a", "a.a....a.a", "a.a.cc.a.a",
               "a.a.cc.a.a", "a.a....a.a", "a..aaaa..a", ".a......a.", "..aaaaaa.."],
    "breaker": ["s........s", ".s......s.", "..s.ss.s..", "...ssss...", "..ssbbss..",
                "..ssbbss..", "...ssss...", "..s.ss.s..", ".s......s.", "s........s"],
    "placer": ["....bb....", "...bbbb...", "..bbbbbb..", ".bb.bb.bb.", "....bb....",
               "....bb....", "..cccccc..", "..cccccc..", "..cccccc..", "..cccccc.."],
    "timer": ["...bbbb...", "..bccccb..", ".bcccdccb.", "bccccdcccb", "bccccdcccb",
              "bccccddddb", "bccccccccb", ".bccccccb.", "..bccccb..", "...bbbb..."],
    "transmitter": ["....aa....", "...a..a...", "..a.aa.a..", ".a.a..a.a.", "....bb....",
                    "....bb....", "....bb....", "...bbbb...", "..bbbbbb..", ".bbbbbbbb."],
    "receiver": [".bbbbbbbb.", "b........b", "b.aaaaaa.b", ".b......b.", "..b.aa.b..",
                 "...bbbb...", "....bb....", "....bb....", "...bbbb...", "..bbbbbb.."],
    "detector": ["...bbbb...", "..bccccb..", ".bccaaccb.", "bccaddaccb", "bcaddddacb",
                 "bcaddddacb", "bccaddaccb", ".bccaaccb.", "..bccccb..", "...bbbb..."],
}


def machine_glow(name):
    """The colour a machine's window lights up with: amber for steam work, aether cyan for the wireless/vacuum ones."""
    return AETHER if name in ("transmitter", "receiver", "vacuum") else AMBER


def machine_window(name, on=False):
    """The 10x10 glyph window of a machine as a function (x, y) -> colour.

    Off: the glyph in its own metal colours, a little dimmed, on a sooty dark glass. On (running / powered): the glass
    is backlit (a warm glow brightest behind the glyph centre), the glyph pixels run hot (mixed toward a pale
    filament white) and every dark pixel touching the glyph catches a halo of the glow, so the whole symbol lights up
    even when it has no ``a`` (glow) pixels of its own. The block model draws this window as an emissive element
    when on (wf/machines.py model)."""
    glow = machine_glow(name)
    colors = {
        "s": (210, 214, 220), "b": BRASS, "w": (214, 190, 90), "c": CREAM if name in ("timer", "detector") else COPPER,
        "d": (170, 30, 30) if name in ("timer", "detector") else (90, 170, 230),
        "a": glow,
    }
    if name == "sprinkler":
        colors["c"] = (90, 170, 230)
    if name == "detector" and on:
        colors["d"] = (255, 70, 50)
    rows = [r.ljust(10, ".") for r in MACHINE_GLYPHS[name]]
    lit = {(x, y) for y in range(10) for x in range(10) if rows[y][x] != "."}
    hot = mix(glow, (255, 244, 220), 0.55)
    if not on:
        dark = _dark_back((30, 26, 26))

        def inner(x, y):
            ch = rows[y][x]
            if ch == ".":
                return dark(x, y)
            return mul(glow, 0.42) if ch == "a" else mul(colors[ch], 0.82)
        return inner

    def back(x, y):
        d = math.hypot(x - 4.5, y - 4.5) / 6.0
        f = max(0.0, 1.0 - d) ** 1.6
        c = mix(mul(glow, 0.13), mul(glow, 0.40), f)
        # a soft halo on the glass right next to the glyph (edge neighbours count more than corners)
        near = sum((x + dx, y + dy) in lit for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) * 2 + \
            sum((x + dx, y + dy) in lit for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)))
        if near:
            c = mix(c, mul(glow, 0.8), min(0.42, 0.07 * near))
        return mul(c, 1.0 + ((x * 7 + y * 13) % 5 - 2) * 0.02)

    def inner(x, y):
        ch = rows[y][x]
        if ch == ".":
            return back(x, y)
        if ch == "a":
            return hot
        if ch == "d":  # coloured marks (timer hands, detector eye, water drops) keep their colour, brighter
            return mix(mul(colors[ch], 1.25), (255, 244, 220), 0.12)
        # metal parts glow from within: their own colour pushed toward the filament white, tinted by the glow
        return mix(mix(mul(colors[ch], 1.12), glow, 0.18), (255, 246, 226), 0.30)
    return inner


def machine_face(name, on=False, seed=0):
    """The whole front of a machine (frame + window): the item icons and screens use it."""
    return machine_frame(machine_window(name, on), seed)


def machine_front_frame(seed=0):
    """The machine front with its window cut out (transparent): the block models draw the window one pixel deeper."""
    cv = machine_frame(lambda x, y: None, seed)
    for y in range(3, 13):
        for x in range(3, 13):
            cv.set(x, y, (0, 0, 0, 0))
    return cv


# ---------------------------------------------------------------- furniture surfaces (wf/furniture.py)
def plain_wood(base, seed=0):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            g = 0.07 * math.sin(y * 0.9 + math.sin(x * 0.7) * 1.5) + rng.uniform(-0.03, 0.03)
            cv.set(x, y, mul(base, 1 + g))
    return cv


def smooth_metal(base, seed=0):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            f = 1.12 - 0.22 * (x + y) / 30 + rng.uniform(-0.025, 0.025)
            cv.set(x, y, mul(base, f))
    for i in range(3, 8):
        cv.set(i, 15 - i - 4, mul(base, 1.3))
    return cv


def glow_bulb(glass, core, seed=0):
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5) / 10.6
            cv.set(x, y, mix(core, glass, min(1.0, d * 1.3)))
    return cv


def chain(metal):
    cv = Canvas(16, 16)
    for y in range(16):
        for x in (6, 7, 8, 9):
            link = (y // 4) % 2
            edge = x in (6, 9) if link == 0 else y % 4 in (0, 3)
            if link == 0 or x in (7, 8):
                cv.set(x, y, mul(metal, 0.7 if edge else 1.15))
    return cv


def wax(base, seed=0):
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(base, 1 + rng.uniform(-0.04, 0.04) - y * 0.008))
    return cv
