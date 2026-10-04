"""Painted item sprites: shapes drawn from primitives (segments, discs, polygons, ASCII stamps) on a 16x16 grid of
material keys, then shaded and outlined automatically so every sprite shares one light (top-left), a 1-px dark
outline and the steampunk palette of STYLE_STEAMPUNK.md.

gen_textures.render_sprite() looks a shape up in PAINTED before falling back to the ASCII SHAPES of sprites.py, so
a painted shape keeps working with every (material, handle, accent) combination: "M" is the item's material, "H"
its handle, "A" its accent; the fixed keys below are the shared steampunk metals and glows.

Tones: shine > light > mid > dark > deep (> outline). Auto tone: light on top/left edges, dark on bottom/right
edges, mid inside, per material region (a brass band inside an iron blade gets its own bevel).
"""
import math

from .png import Canvas

# fixed steampunk materials: (light, mid, dark, outline)
STEAM = {
    "B": ((250, 222, 130), (204, 162, 72), (140, 100, 40), (56, 36, 14)),      # brass
    "C": ((240, 166, 104), (186, 112, 52), (122, 64, 30), (50, 24, 10)),       # copper
    "V": ((150, 232, 220), (67, 179, 174), (34, 112, 110), (14, 46, 46)),      # verdigris
    "I": ((232, 232, 240), (170, 170, 182), (102, 102, 116), (36, 36, 46)),    # steel
    "X": ((104, 96, 98), (66, 60, 62), (40, 36, 38), (18, 14, 16)),            # dark iron
    "W": ((164, 104, 66), (112, 66, 42), (74, 40, 26), (34, 16, 10)),          # mahogany
    "T": ((178, 132, 84), (134, 92, 54), (92, 60, 34), (40, 24, 12)),          # light oak
    "L": ((172, 72, 58), (116, 40, 34), (78, 22, 20), (34, 8, 8)),             # oxblood leather
    "N": ((196, 146, 92), (150, 100, 58), (102, 64, 34), (42, 24, 12)),        # tan leather
    "Q": ((250, 242, 222), (230, 216, 184), (196, 178, 146), (84, 70, 50)),    # cream / paper / bone
    "E": ((214, 252, 255), (90, 222, 255), (32, 150, 210), (10, 50, 80)),      # aether glow
    "R": ((255, 232, 160), (255, 182, 72), (216, 118, 28), (90, 40, 10)),      # amber glow
    "F": ((255, 246, 190), (255, 196, 70), (232, 96, 24), (96, 24, 8)),        # flame
    "G": ((186, 248, 255), (120, 200, 240), (60, 130, 200), (20, 44, 90)),     # glass / ice
    "K": ((70, 60, 58), (46, 38, 36), (30, 24, 22), (14, 10, 10)),             # ink / soot
    "P": ((236, 200, 255), (190, 120, 240), (120, 60, 180), (40, 14, 70)),     # void / amethyst glow
    "S": ((150, 255, 210), (60, 210, 150), (24, 130, 90), (8, 50, 34)),        # sculk / emerald glow
    "Z": ((255, 120, 100), (210, 40, 40), (130, 18, 24), (50, 6, 8)),          # ruby / blood
    "Y": ((255, 255, 255), (236, 240, 244), (200, 206, 214), (120, 124, 130)),  # sparkle / steam (no outline)
}

TONES = ("shine", "light", "mid", "dark", "deep", "outline")


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def mul(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def tones(pal):
    """(light, mid, dark, outline) -> dict of the six tones."""
    light, mid, dark, outline = (tuple(c[:3]) for c in pal)
    return {"shine": mix(light, (255, 255, 255), 0.5), "light": light, "mid": mid, "dark": dark,
            "deep": mix(dark, outline, 0.5), "outline": outline}


def two_tone(lo, hi):
    """Palette from a (light, dark) pair (handles and accents of sprites.py)."""
    lo, hi = tuple(lo[:3]), tuple(hi[:3])
    return (mix(lo, (255, 255, 255), 0.12), mix(lo, hi, 0.45), hi, mul(hi, 0.36))


class Art:
    def __init__(self, mats, n=16):
        self.n = n
        self.pal = {k: tones(v) for k, v in mats.items()}
        self.m = [[None] * n for _ in range(n)]
        self.force = {}
        self.no_outline = set()

    # ------------------------------------------------------------------ painting
    def px(self, x, y, key, tone=None):
        x, y = int(x), int(y)
        if 0 <= x < self.n and 0 <= y < self.n:
            self.m[y][x] = key
            if tone is None:
                self.force.pop((x, y), None)
            else:
                self.force[(x, y)] = tone

    def tone(self, x, y, tone):
        if 0 <= x < self.n and 0 <= y < self.n and self.m[y][x] is not None:
            self.force[(x, y)] = tone

    def paint(self, key, test, tone=None):
        for y in range(self.n):
            for x in range(self.n):
                if test(x + 0.5, y + 0.5):
                    if key is None:
                        self.m[y][x] = None
                        self.force.pop((x, y), None)
                    else:
                        self.px(x, y, key, tone)

    def clear(self, test):
        self.paint(None, test)

    def disc(self, key, cx, cy, r, tone=None):
        self.paint(key, lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r, tone)

    def ring(self, key, cx, cy, r0, r1, tone=None):
        self.paint(key, lambda x, y: r0 * r0 < (x - cx) ** 2 + (y - cy) ** 2 <= r1 * r1, tone)

    def ellipse(self, key, cx, cy, rx, ry, tone=None):
        self.paint(key, lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0, tone)

    def seg(self, key, x0, y0, x1, y1, w, tone=None):
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy

        def t(x, y):
            u = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / ll)) if ll else 0.0
            px, py = x0 + u * dx, y0 + u * dy
            return (x - px) ** 2 + (y - py) ** 2 <= w * w
        self.paint(key, t, tone)

    def poly(self, key, pts, tone=None):
        """Filled polygon (even-odd rule), points in pixel-edge coordinates."""
        def inside(x, y):
            c = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    c = not c
                j = i
            return c
        self.paint(key, inside, tone)

    def box(self, key, x0, y0, x1, y1, tone=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, key, tone)

    def line(self, key, pts, tone=None):
        """1-px pixel line through integer points (Bresenham)."""
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = abs(x1 - x0), -abs(y1 - y0)
            sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
            err = dx + dy
            while True:
                self.px(x0, y0, key, tone)
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy

    def stamp(self, rows, legend, ox=0, oy=0):
        """ASCII stamp: legend char -> key or (key, tone); '.' and unknown chars are skipped."""
        if isinstance(rows, str):
            rows = rows.strip("\n").split("\n")
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                spec = legend.get(ch)
                if spec is None:
                    continue
                if spec == "clear":
                    self.px(ox + x, oy + y, None)
                    continue
                key, tone = (spec, None) if isinstance(spec, str) else spec
                self.px(ox + x, oy + y, key, tone)

    def sphere(self, key, cx, cy, r, shine=True):
        """Paint a disc shaded like a lit ball (light from the top-left)."""
        for y in range(self.n):
            for x in range(self.n):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d2 = dx * dx + dy * dy
                if d2 > r * r:
                    continue
                k = (dx + dy) / (r * 1.4142)          # -1 top-left .. 1 bottom-right
                rim = math.sqrt(d2) / r
                if shine and abs(dx + r * 0.42) < 0.9 and abs(dy + r * 0.42) < 0.9:
                    t = "shine"
                elif k < -0.42:
                    t = "light"
                elif k < 0.22:
                    t = "mid"
                elif k < 0.62 or rim < 0.8:
                    t = "dark"
                else:
                    t = "deep"
                self.px(x, y, key, t)

    def shade_dir(self, key, ax, ay, cuts=(-0.45, 0.25, 0.7)):
        """Re-tone every pixel of ``key`` by its projection on (ax, ay) (normalised over the region): a long
        gradient for blades and wings instead of the edge bevel."""
        cells = [(x, y) for y in range(self.n) for x in range(self.n) if self.m[y][x] == key]
        if not cells:
            return
        p = [x * ax + y * ay for x, y in cells]
        lo, hi = min(p), max(p)
        for (x, y), v in zip(cells, p):
            t = -1 + 2 * (v - lo) / (hi - lo) if hi > lo else 0
            self.force[(x, y)] = "light" if t < cuts[0] else "mid" if t < cuts[1] else "dark" if t < cuts[2] else "deep"

    def alias(self, key, like):
        """A second region key with the palette of ``like`` (two touching lumps of one metal keep their own bevels)."""
        self.pal[key] = self.pal[like]

    def solo(self, *keys):
        """No outline drawn around these keys (glows, sparks, smoke)."""
        self.no_outline |= set(keys)

    # ------------------------------------------------------------------ rendering
    def render(self, outline=True):
        n = self.n
        cv = Canvas(n, n)

        def key(x, y):
            return self.m[y][x] if 0 <= x < n and 0 <= y < n else None

        for y in range(n):
            for x in range(n):
                k = self.m[y][x]
                if k is None:
                    continue
                t = self.force.get((x, y))
                if isinstance(t, tuple):
                    cv.set(x, y, t)
                    continue
                if t is None:
                    up, left = key(x, y - 1) == k, key(x - 1, y) == k
                    down, right = key(x, y + 1) == k, key(x + 1, y) == k
                    if not up or not left:
                        t = "light" if (down and right) or not (up or left) else "mid"
                    elif not down or not right:
                        t = "dark"
                    else:
                        t = "mid"
                cv.set(x, y, self.pal[k][t])
        if outline:
            for y in range(n):
                for x in range(n):
                    if self.m[y][x] is not None:
                        continue
                    near = [key(xx, yy) for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))]
                    near = [k for k in near if k is not None and k not in self.no_outline]
                    if near:
                        c = min((self.pal[k]["outline"] for k in near), key=sum)
                        cv.set(x, y, c)
        return cv


# ------------------------------------------------------------------ helpers shared by the sprites
def haft(a, x0, y0, x1, y1, key="H", w=0.75):
    """A 2-px diagonal shaft (light upper-left edge, dark lower-right edge by the auto tone)."""
    a.seg(key, x0, y0, x1, y1, w)


def diag(a, key, x0, y0, length, tone=None, width=2):
    """Clean 45-degree band going up-right from (x0, y0): ``width`` px per row (pixel-art staircase)."""
    for i in range(length):
        for k in range(width):
            a.px(x0 + i + k, y0 - i, key, tone)


def rivet(a, x, y, key="B"):
    a.px(x, y, key, "shine")


def cube(a, ox, oy, key, size=8):
    """Isometric block (light top, mid left, dark right faces) in a size x size box."""
    h, q = size / 2, size / 4
    a.poly(key, [(ox + h, oy), (ox + size, oy + q), (ox + h, oy + h), (ox, oy + q)], "light")
    a.poly(key, [(ox, oy + q), (ox + h, oy + h), (ox + h, oy + size), (ox, oy + size - q)], "mid")
    a.poly(key, [(ox + h, oy + h), (ox + size, oy + q), (ox + size, oy + size - q), (ox + h, oy + size)], "deep")
    for x in range(int(ox + 1), int(ox + size - 1)):
        a.tone(x, int(oy + q), "shine") if a.force.get((x, int(oy + q))) == "light" else None
    for y in range(int(oy + h), int(oy + size - 1)):
        a.tone(int(ox + h - 1), y, "light")


PAINTED = {}


def painted(name):
    def deco(fn):
        PAINTED[name] = fn
        return fn
    return deco


def sprite(shape, mats):
    """mats: {'M': (l, m, d, o), 'H': ..., 'A': ...} -> Canvas, or None when the shape is not painted."""
    fn = PAINTED.get(shape)
    if fn is None:
        return None
    a = Art({**STEAM, **mats, "a": mats["A"]})
    a.solo("Y", "a")          # sparkles, steam and accent motes float free of the outline
    fn(a)
    return a.render()


from . import itemart_shapes, itemart_tools, itemart_trinkets  # noqa: E402,F401  (registers the painted shapes)
