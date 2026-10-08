"""Steampunk block textures (brass, copper, iron, mahogany, leather), in the same 16x16 shaded style as texgen.

Palette from tools/STYLE_STEAMPUNK.md: brass, copper, verdigris, dark iron, mahogany, oxblood leather,
cream, amber glow and aether cyan.
"""
import math
import random

from .png import Canvas
from .texgen import mix
from .texkit import tmul as mul  # hue-shifted shading
from .texgen import mul as _pmul  # plain scaling, for glows (a dim glow stays its own hue)

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
    """A flat field of ``base`` with clustered grain (2-4 px patches one shade up or down), not per-pixel noise."""
    from .texkit import grain_field
    g = grain_field(seed)
    cv = Canvas(16, 16)
    tones = {-1: mul(base, 1 - grain * 1.4), 0: tuple(base[:3]), 1: mul(base, 1 + grain * 1.4)}
    for y in range(16):
        for x in range(16):
            cv.set(x, y, tones[g[y][x]])
    return cv


def _bevel(cv, base, light=1.18, dark=0.72):
    for i in range(16):
        cv.set(i, 0, mul(base, light))
        cv.set(0, i, mul(base, light))
        cv.set(i, 15, mul(base, dark))
        cv.set(15, i, mul(base, dark))
    cv.set(15, 0, mul(base, (light + dark) / 2))
    cv.set(0, 15, mul(base, (light + dark) / 2))
    return cv


def _rivet(cv, x, y, base):
    """A 2x2 domed rivet head lit from the top-left, shaded bottom-right."""
    cv.set(x, y, mul(base, 1.5))
    cv.set(x + 1, y, mul(base, 1.05))
    cv.set(x, y + 1, mul(base, 0.95))
    cv.set(x + 1, y + 1, mul(base, 0.66))


def riveted_plate(base, seed=0, patina=None, patina_amount=0.0):
    """Two overlapping plates (the upper one casts a shadow line on the lower), staggered vertical seams so a wall
    of them reads as laid plates, domed rivets along each plate, clustered brushed streaks. Optional verdigris:
    patches grown from clustered noise that pool in the seams and run down under the rivets. A patina_amount of 0.6
    or more is a fully weathered plate: the verdigris is the surface and the copper only shows on the rivets."""
    from .texkit import grain_field, field
    copper = base
    weathered = bool(patina) and patina_amount >= 0.6
    if weathered:
        base = mix(base, patina, 0.78)
    g = grain_field(f"rp{seed}", stretch=4)
    cv = Canvas(16, 16)
    for y in range(16):
        upper = y < 8
        for x in range(16):
            f = (1.03 if upper else 0.97) + g[y][x] * 0.045
            cv.set(x, y, mul(base, f))
    _bevel(cv, base, 1.22, 0.62)
    # seam between the plates: upper plate's lower lip, its cast shadow, the lower plate's lit top edge
    for x in range(1, 15):
        cv.set(x, 6, mul(base, 0.84))
        cv.set(x, 7, mul(base, 0.52))
        cv.set(x, 8, mul(base, 1.16))
    # staggered butt joints
    for y in range(1, 6):
        cv.set(10, y, mul(base, 0.6))
        cv.set(11, y, mul(base, 1.14))
    for y in range(9, 15):
        cv.set(4, y, mul(base, 0.6))
        cv.set(5, y, mul(base, 1.14))
    rivets = [(2, 2), (7, 2), (13, 2), (2, 11), (8, 11), (13, 11)]
    for x, y in rivets:
        _rivet(cv, x, y, copper if weathered else base)
    if patina:
        f = field(f"pat{seed}", ((4, 0.6), (2, 0.4)), 0.1)
        cut = 1.0 - patina_amount * 0.55
        for y in range(16):
            for x in range(16):
                v = f[y][x] + (0.18 if y in (6, 7, 8) else 0)      # it pools in the seam
                if (x, y) in {(rx + i, ry + j) for rx, ry in rivets for i in (0, 1) for j in (0, 1)}:
                    continue
                if v > cut:
                    cv.set(x, y, mix(cv.get(x, y), patina, 0.6 if v < cut + 0.15 else 0.85))
        for x, y in rivets:
            for k in (2, 3):
                if y + k < 16 and (not weathered or k == 2):
                    cv.set(x, y + k, mix(cv.get(x, y + k), mul(patina, 0.85 if weathered else 1.0), 0.7))
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
    """Diamond (tread) plate: raised lozenges in a herringbone, alternately "/" and "\\", each lit on its upper-left
    end and shaded on its lower-right end (solid, so it works everywhere a full block does)."""
    cv = _base(base, seed, 0.03)
    hi, mid_, lo = mul(base, 1.45), mul(base, 1.18), mul(base, 0.6)
    for cy in range(0, 16, 4):
        for cx in range(0, 16, 4):
            if ((cx + cy) // 4) % 2:
                bar = [(cx + 2, cy), (cx + 1, cy + 1), (cx, cy + 2)]          # "/"
            else:
                bar = [(cx, cy), (cx + 1, cy + 1), (cx + 2, cy + 2)]          # "\\"
            for i, (x, y) in enumerate(bar):
                cv.set(x, y, hi if (x, y) == min(bar, key=lambda p: p[0] + p[1]) else mid_)
            for x, y in bar:
                if (x, y + 1) not in bar:
                    cv.set(x, (y + 1) % 16, lo)
    _bevel(cv, base, 1.2, 0.66)
    return cv


def aether_conduit(base, glow, seed=0):
    """Dark iron block crossed by glass aether channels: a white-hot core line, the glow, then a soft halo on the
    iron, meeting in a brass junction collar at the centre."""
    cv = riveted_plate(base, seed)
    core = mix(glow, (255, 255, 255), 0.65)
    halo = lambda c: mix(c, glow, 0.38)
    for i in range(1, 15):
        for (x, y) in ((i, 7), (i, 8), (7, i), (8, i)):
            cv.set(x, y, glow)
        for (x, y) in ((i, 6), (i, 9), (6, i), (9, i)):
            if not (6 <= x <= 9 and 6 <= y <= 9):
                cv.set(x, y, halo(cv.get(x, y)))
        cv.set(i, 7, core) if i not in (7, 8) else None
        cv.set(7, i, core) if i not in (7, 8) else None
    for x in range(5, 11):
        for y in range(5, 11):
            if x in (5, 10) or y in (5, 10):
                cv.set(x, y, mul(BRASS, 1.3 if x == 5 or y == 5 else 0.7))
            elif x in (6, 9) or y in (6, 9):
                cv.set(x, y, mul(BRASS, 1.0))
    for x, y in ((7, 7), (8, 8), (7, 8), (8, 7)):
        cv.set(x, y, core)
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
    """Machine casing: a riveted brass plate with a recessed vent - shadowed top/left lip, lit bottom/right lip,
    louvred slats (lit top edge, dark gap) over the sooty inside."""
    cv = riveted_plate(BRASS, seed)
    for y in range(4, 12):
        for x in range(4, 12):
            if (y - 4) % 2 == 0:
                cv.set(x, y, mul(DARK_IRON, 0.75))
            else:
                cv.set(x, y, mul(BRASS, 1.12) if x < 11 else mul(BRASS, 0.8))
    for i in range(3, 13):
        cv.set(i, 3, mul(BRASS, 0.55))
        cv.set(3, i, mul(BRASS, 0.55))
        cv.set(i, 12, mul(BRASS, 1.3))
        cv.set(12, i, mul(BRASS, 1.3))
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
    def edge(x, y):
        """+1 on a glyph pixel's lit (top/left) rim, -1 on its shaded (bottom/right) rim, 0 inside."""
        ch = rows[y][x]

        def same(xx, yy):
            return 0 <= xx < 10 and 0 <= yy < 10 and rows[yy][xx] == ch
        if not same(x, y - 1) or not same(x - 1, y):
            return 1 if same(x + 1, y) or same(x, y + 1) else 0
        if not same(x, y + 1) or not same(x + 1, y):
            return -1
        return 0

    if not on:
        def inner(x, y):
            ch = rows[y][x]
            if ch == ".":
                # sooty glass with one faint diagonal reflection near its top-left corner
                c = mul((30, 26, 28), 1.0 + ((x * 7 + y * 13) % 5 - 2) * 0.03)
                return mix(c, (70, 66, 70), 0.5) if x + y in (2, 3) else c
            if ch == "a":
                return _pmul(glow, 0.42)
            e = edge(x, y)
            return mul(colors[ch], 0.82 * (1.22 if e > 0 else 0.7 if e < 0 else 1.0))
        return inner

    def back(x, y):
        d = math.hypot(x - 4.5, y - 4.5) / 6.0
        f = max(0.0, 1.0 - d) ** 1.6
        c = mix(_pmul(glow, 0.13), _pmul(glow, 0.40), f)
        # a soft halo on the glass right next to the glyph (edge neighbours count more than corners)
        near = sum((x + dx, y + dy) in lit for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) * 2 + \
            sum((x + dx, y + dy) in lit for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)))
        if near:
            c = mix(c, _pmul(glow, 0.8), min(0.42, 0.07 * near))
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
        e = edge(x, y)
        return mix(mix(mul(colors[ch], 1.12 * (1.12 if e > 0 else 0.86 if e < 0 else 1.0)), glow, 0.18),
                   (255, 246, 226), 0.30)
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
