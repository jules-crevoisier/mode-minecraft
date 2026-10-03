"""The Rune Colossus (Le Colosse runique): the stone circle risen as a giant.

About 5.8 blocks tall, hunched like a great ape, assembled from standing stones and lintels: a boulder
torso fronted by a carved slab with the circle-rune, a lintel laid across the shoulders, legs and arms of
standing stones, a monolith head with slit eyes, and on its back a whole trilithon (two uprights and a
slipped capstone) - the circle it guards, carried like a crown. Asymmetric: the right fist is a huge
boulder of stacked stones, the left arm a long tapering menhir. Moss and lichen on every top face; runes
and cracks glow cyan (emissive layer).
"""
import math

from ..models import Model
from ..texgen import mix, mul
from .gryphon_knight import hsh, jit, nz

# ---------------------------------------------------------------- palette
GREY = (124, 126, 124)
BLUE_GREY = (108, 116, 124)
TUFF = (128, 122, 110)
DARK = (78, 80, 82)
MOSS = (86, 120, 52)
MOSS_D = (58, 88, 40)
MOSS_L = (122, 150, 70)
LICHEN = (190, 186, 120)
LICHEN_O = (196, 140, 70)
GROOVE = (34, 52, 62)
RUNE = (96, 236, 255)
RUNE_HOT = (190, 252, 255)

GLYPHS = [
    [".#.", "#.#", ".#.", ".#.", ".#."],   # tiwaz
    ["#.#", "##.", "#.#", "##.", "#.."],   # fehu
    ["##.", "#.#", "#.#", "#.#", "#.#"],   # uruz
    ["#..", "##.", "#.#", "##.", "#.."],   # thurisaz
    ["..#", ".#.", "#..", ".#.", "..#"],   # kaunan
    ["#.#", "#.#", ".#.", "#.#", "#.#"],   # gebo
    ["#.#", "###", "#.#", "#.#", "#.#"],   # mannaz
    [".#.", "#.#", ".#.", "#.#", "#.#"],   # othala
    ["#.#", "###", ".#.", ".#.", ".#."],   # algiz
    ["#.#", ".#.", ".#.", "#.#", ".#."],   # ingwaz-ish
]


class Stone:
    """One carved stone: a painted surface (big soft value blotches, chisel marks, chipped light top edge,
    darker foot, lichen, moss creeping over the top) plus carved runes and cracks that glow.

    ``runes``: {face: "column" | "ring" | "row"} where to carve glyph columns / the circle rune / a row.
    ``cracks``: number of glowing cracks per large side face. ``moss``: 0..1 how far moss creeps down."""

    def __init__(self, base=GREY, seed=0, runes=None, cracks=0, moss=0.35, lichen=True, glow=True):
        self.base, self.seed, self.runes, self.cracks = base, seed, runes or {}, cracks
        self.moss, self.lichen, self.do_glow = moss, lichen, glow
        self._cache = {}

    # ---------------------------------------------------------------- carving pattern per face
    def carve(self, face, w, h):
        key = (face, w, h)
        if key in self._cache:
            return self._cache[key]
        pts = {}                                   # (x, y) -> "rune" | "crack"
        kind = self.runes.get(face)
        sd = hsh(self.seed, len(face), w, h)
        if kind == "column" and w >= 5 and h >= 8:
            cx = w // 2 - 1
            y = 2 + sd % 3
            i = sd
            while y + 5 <= h - 2:
                g = GLYPHS[i % len(GLYPHS)]
                for gy, row in enumerate(g):
                    for gx, ch in enumerate(row):
                        if ch == "#":
                            pts[(cx + gx, y + gy)] = "rune"
                y += 7
                i += 3
        elif kind == "row" and w >= 8 and h >= 6:
            y = h // 2 - 2
            x = 2
            i = sd
            while x + 3 <= w - 2:
                for gy, row in enumerate(GLYPHS[i % len(GLYPHS)]):
                    for gx, ch in enumerate(row):
                        if ch == "#":
                            pts[(x + gx, y + gy)] = "rune"
                x += 5
                i += 7
        elif kind == "ring" and w >= 13 and h >= 13:
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = min(w, h) / 2 - 2.5
            for yy in range(h):
                for xx in range(w):
                    d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                    if abs(d - r) < 0.55:
                        pts[(xx, yy)] = "rune"
                    elif d < 1.6:
                        pts[(xx, yy)] = "rune"
            # four spokes and glyphs around the ring
            for k in range(8):
                a = k * math.pi / 4
                for t in (r - 2.0, r - 3.0):
                    pts[(round(cx + math.cos(a) * t), round(cy + math.sin(a) * t))] = "rune"
        # glowing cracks: jagged random walks from an edge
        if self.cracks and face in ("front", "back", "left", "right") and w >= 6 and h >= 8:
            for c in range(self.cracks):
                s = hsh(self.seed, c, len(face), 7)
                x = 1 + s % max(1, w - 2)
                y = 0 if c % 2 == 0 else h - 1
                dy = 1 if y == 0 else -1
                for step in range(int(h * 0.55)):
                    pts.setdefault((x, y), "crack")
                    r = hsh(s, step) % 5
                    if r == 0 and x > 1:
                        x -= 1
                    elif r == 1 and x < w - 2:
                        x += 1
                    elif r == 2 and step > 3 and hsh(s, step, 1) % 4 == 0:  # side branch
                        bx = x + (1 if x < w // 2 else -1)
                        pts.setdefault((bx, y), "crack")
                        pts.setdefault((bx + (1 if x < w // 2 else -1), y + dy), "crack")
                    y += dy
                    if not 0 <= y < h:
                        break
        self._cache[key] = pts
        return pts

    # ---------------------------------------------------------------- painters
    def paint(self, face, x, y, w, h):
        sd = self.seed
        # large soft blotches (4 px cells blended) give the "big stone" read, not per-pixel noise
        cell = (nz(x // 4, y // 4, sd + 11) + nz((x + 2) // 4, (y + 2) // 4, sd + 12)) / 2
        c = mul(self.base, 0.9 + cell * 0.2)
        if hsh(x, y, sd) % 17 == 0:
            c = mul(c, 0.88)                                  # pits
        if (x * 3 + y * 5 + sd) % 29 == 0:
            c = mix(c, (176, 176, 168), 0.35)                 # quartz flecks
        pts = self.carve(face, w, h)
        p = pts.get((x, y))
        if p == "rune":
            return GROOVE
        if p == "crack":
            return mul(GROOVE, 0.8)
        if face == "top":
            m = nz(x // 2, y // 2, sd + 5)
            if m < 0.62 + self.moss * 0.3:
                return jit(MOSS_L if m < 0.2 else (MOSS if m < 0.5 else MOSS_D), x, y, sd, 0.05)
            return mix(c, (150, 150, 140), 0.2)
        if face == "bottom":
            return mul(c, 0.85)
        # moss creeping over the upper edge of the sides, in irregular drips
        drip = int(self.moss * 6 * nz(x, 0, sd + 3) + (1 if self.moss > 0 else 0))
        if y < drip:
            return jit(MOSS if (x + y) % 3 else MOSS_D, x, y, sd, 0.05)
        if y == drip:
            c = mix(c, MOSS_D, 0.35)
        if self.lichen:
            ln = nz(x // 2, y // 2, sd + 9)
            if ln > 0.955:
                c = mix(c, LICHEN, 0.7)
            elif ln < 0.012:
                c = mix(c, LICHEN_O, 0.6)
        # chisel marks: faint diagonal strokes
        if (x + y * 2 + sd) % 9 == 0:
            c = mul(c, 0.94)
        # chipped light edges, darker foot
        if x == 0 or x == w - 1:
            c = mul(c, 0.93)
        if y == h - 1 and h > 3:
            c = mul(c, 0.82)
        elif y >= h - 3 and h > 8:
            c = mul(c, 0.92)
        # glow bleeding around runes: a lighter halo on the stone
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if pts.get((x + dx, y + dy)) == "rune":
                c = mix(c, (120, 170, 176), 0.35)
                break
        return jit(c, x, y, sd, 0.025)

    def glow(self, face, x, y, w, h):
        if not self.do_glow:
            return None
        p = self.carve(face, w, h).get((x, y))
        if p == "rune":
            return RUNE
        if p == "crack":
            return RUNE if (x + y) % 3 else RUNE_HOT
        return None


def S(m, part, box, stone):
    x, y, z, w, h, d = box
    m.box(part, x, y, z, w, h, d, stone.paint, glow=stone.glow)


def build():
    m = Model("rune_colossus", seed=62, shadow=2.4, walk_speed=0.7, walk_scale=1.0, head="head")
    g = lambda h: 24 - h  # noqa: E731  height above the ground -> model y

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, g(40) - 24, 0))
    m.part("torso", "hips", pivot=(0, -4, 2), rot=(14, 0, 0))            # hunched forward
    m.part("head", "torso", pivot=(0, -34, -8), rot=(-14, 0, 0))
    m.part("slab", "torso", pivot=(0, -15, -14), rot=(0, 0, 4))
    m.part("lintel", "torso", pivot=(0, -30, 0), rot=(0, 0, -3))
    m.part("crown", "torso", pivot=(-4, -57, 10), rot=(0, 0, 7))         # the slipped capstone
    for side, sx in (("l", 1), ("r", -1)):
        m.part(f"arm_{side}", "torso", pivot=(sx * 27, -27, 0), rot=(-14, 0, sx * -6))
        m.part(f"forearm_{side}", f"arm_{side}", pivot=(0, 22, 0), rot=(-18, 0, 0))
        m.part(f"fist_{side}", f"forearm_{side}", pivot=(0, 20, 0))
        m.part(f"leg_{side}", "hips", pivot=(sx * 10, 2, 1))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 17, 0))

    # ------------------------------------------------------------------ hips and legs
    S(m, "hips", (-15, -6, -10, 30, 12, 19), Stone(TUFF, 1, moss=0.1))
    for side, sx in (("l", 1), ("r", -1)):
        S(m, f"leg_{side}", (-7, -2, -7, 14, 19, 14), Stone(GREY, 10 + sx, cracks=1 if sx > 0 else 0, moss=0.2))
        S(m, f"shin_{side}", (-6.5, 0, -6.5, 13, 16, 13), Stone(BLUE_GREY, 12 + sx, moss=0.0))
        S(m, f"shin_{side}", (-8, 15, -10, 16, 6, 18), Stone(DARK, 14 + sx, moss=0.0, lichen=False))  # foot slab

    # ------------------------------------------------------------------ torso: boulder, carved slab, lintel
    S(m, "torso", (-19, -28, -13, 38, 28, 26), Stone(GREY, 20, cracks=2, moss=0.3))
    S(m, "torso", (-15, -4, -11, 30, 8, 22), Stone(TUFF, 21, moss=0.0))
    S(m, "slab", (-14, -10, -2, 28, 20, 3), Stone(BLUE_GREY, 22, runes={"front": "ring"}, moss=0.15))
    S(m, "lintel", (-30, -4, -11, 60, 7, 22), Stone(TUFF, 23, runes={"front": "row"}, moss=0.6))     # shoulder lintel
    # the trilithon on its back: two uprights (one shorter) and the slipped capstone
    S(m, "torso", (-18, -56, 4, 9, 23, 9), Stone(GREY, 24, runes={"front": "column"}, moss=0.4))
    S(m, "torso", (9, -53, 4, 9, 20, 9), Stone(BLUE_GREY, 25, cracks=1, moss=0.4))
    S(m, "crown", (-19, -6, -6, 46, 7, 12), Stone(TUFF, 26, runes={"back": "row"}, moss=0.9))
    # rubble and small stones lodged on the shoulders
    S(m, "torso", (-26, -37, -6, 7, 3, 8), Stone(GREY, 27, moss=0.8))
    S(m, "torso", (20, -38, -4, 6, 4, 6), Stone(DARK, 28, moss=0.8))

    # ------------------------------------------------------------------ head: a carved monolith
    def face_glow(f_, x, y, w, h):
        if f_ != "front":
            return None
        if y in (6, 7) and (2 <= x <= 5 or w - 6 <= x <= w - 3):
            return RUNE_HOT
        if y == 14 and 4 <= x <= w - 5 and x % 2 == 0:
            return RUNE                                                  # the carved mouth
        return None
    head = Stone(BLUE_GREY, 30, runes={"left": "column", "right": "column"}, moss=0.7)

    def head_paint(f_, x, y, w, h):
        if face_glow(f_, x, y, w, h):
            return GROOVE
        if f_ == "front" and y == 8 and 1 <= x <= w - 2:
            return mul(BLUE_GREY, 0.6)                                    # brow shadow
        return head.paint(f_, x, y, w, h)

    def head_glow(f_, x, y, w, h):
        return face_glow(f_, x, y, w, h) or head.glow(f_, x, y, w, h)
    m.box("head", -8, -18, -7, 16, 19, 13, head_paint, glow=head_glow)
    S(m, "head", (-9, -15, -9, 18, 3, 4), Stone(GREY, 31, moss=0.2))                                  # brow ridge
    S(m, "head", (-6, -21, -4, 9, 3, 9), Stone(GREY, 32, moss=1.0))                                   # broken cap
    S(m, "head", (-7, -2, -9, 14, 4, 5), Stone(TUFF, 33, moss=0.0))                                   # jaw stone

    # ------------------------------------------------------------------ arms
    # left: a long tapering menhir; right: a heavier arm ending in a boulder fist
    S(m, "arm_l", (-6, -3, -6, 12, 25, 12), Stone(GREY, 40, runes={"left": "column"}, moss=0.3))
    S(m, "forearm_l", (-6.5, 0, -6.5, 13, 21, 13), Stone(BLUE_GREY, 41, cracks=1, moss=0.1))
    S(m, "fist_l", (-7.5, 0, -8, 15, 12, 16), Stone(TUFF, 42, moss=0.2))
    S(m, "fist_l", (-6, 2, -10, 12, 7, 3), Stone(DARK, 43, moss=0.0))                                 # knuckle stone
    S(m, "arm_r", (-7, -4, -7, 14, 26, 14), Stone(TUFF, 44, runes={"right": "column"}, moss=0.3))
    S(m, "arm_r", (-9, -7, -8, 18, 6, 16), Stone(GREY, 45, moss=0.7))         # pauldron slab
    S(m, "forearm_r", (-8, 0, -8, 16, 21, 16), Stone(GREY, 46, cracks=1, moss=0.1))
    S(m, "fist_r", (-11, 0, -11, 22, 15, 22), Stone(BLUE_GREY, 47, cracks=1, moss=0.3))
    S(m, "fist_r", (-7, -4, -6, 13, 5, 13), Stone(TUFF, 48, moss=0.6))                                # stacked stone
    S(m, "fist_r", (-9, 12, -13, 18, 5, 4), Stone(DARK, 49, moss=0.0))                                # knuckles

    # ------------------------------------------------------------------ details: knee caps, elbows, flank stones,
    # a cairn on the back, vines trailing from the capstone
    for side, sx in (("l", 1), ("r", -1)):
        S(m, f"leg_{side}", (-6, 9, -9, 12, 8, 3), Stone(TUFF, 50 + sx, moss=0.5))                     # knee cap
        S(m, f"forearm_{side}", (-5, -3, 3, 10, 6, 5), Stone(DARK, 52 + sx, moss=0.6))                # elbow
        S(m, "torso", (sx * 19 - (4 if sx > 0 else 0) + (0 if sx > 0 else -0), -22, -9, 4, 14, 16),
          Stone(BLUE_GREY, 54 + sx, cracks=1, moss=0.3))                                               # flank stone
    S(m, "torso", (-6, -31, 11, 12, 6, 5), Stone(GREY, 56, moss=0.9))                                   # cairn
    S(m, "torso", (-3, -35, 12, 6, 4, 4), Stone(TUFF, 57, moss=1.0))
    S(m, "fist_l", (-8.5, 5, -6, 3, 6, 10), Stone(GREY, 58, moss=0.2))
    S(m, "fist_r", (9, 4, -8, 4, 8, 14), Stone(TUFF, 59, moss=0.3))

    def vines(f_, x, y, w, h):
        if f_ not in ("front", "back"):
            return None
        if y > h - 2 - (x * 7 % 5) or x % 3 == 1:
            return None
        return MOSS if (x + y) % 4 else MOSS_D
    m.box("crown", -17, 1, 6.5, 22, 14, 0, vines)
    m.box("crown", 8, 1, 6.5, 14, 10, 0, vines)
    # a cracked rune tablet hanging on chains across the chest
    m.box("slab", -9, -16, -3, 1, 8, 1, (70, 72, 76))
    m.box("slab", 8, -16, -3, 1, 8, 1, (70, 72, 76))

    anims(m)
    return m


Z3 = (0, 0, 0)


def anims(m):
    # ---------------------------------------------------------------- idle: slow heavy breath, grinding head
    a = m.anim("idle", 4.0)
    a.rot("torso", (0, Z3), (2.0, (-2.5, 0, 0)), (4.0, Z3))
    a.rot("head", (0, Z3), (1.5, (3, 6, 0)), (3.0, (-2, -5, 0)), (4.0, Z3))
    a.rot("arm_l", (0, Z3), (2.0, (3, 0, -2)), (4.0, Z3))
    a.rot("arm_r", (0, Z3), (2.0, (3, 0, 2)), (4.0, Z3))
    a.rot("crown", (0, Z3), (2.0, (0, 0, 1.5)), (4.0, Z3))
    a.pos("hips", (0, Z3), (2.0, (0, 0.6, 0)), (4.0, Z3))

    # ---------------------------------------------------------------- walk: ponderous, rolling the shoulders
    a = m.anim("walk", 2.0)
    a.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    a.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    a.rot("shin_l", (0, Z3), (0.5, (25, 0, 0)), (1.0, Z3), (2.0, Z3))
    a.rot("shin_r", (0, Z3), (1.0, Z3), (1.5, (25, 0, 0)), (2.0, Z3))
    a.rot("arm_l", (0, (18, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (18, 0, 0)))
    a.rot("arm_r", (0, (-15, 0, 0)), (1.0, (15, 0, 0)), (2.0, (-15, 0, 0)))
    a.rot("torso", (0, (0, 6, 3)), (1.0, (0, -6, -3)), (2.0, (0, 6, 3)))
    a.pos("hips", (0, Z3), (0.5, (0, 2, 0)), (1.0, Z3), (1.5, (0, 2, 0)), (2.0, Z3))

    # ---------------------------------------------------------------- slam: both fists raised high, hammered
    # down (impact 1.1 s = 22 t), the rune rings ripple out, slow recovery
    a = m.anim("slam", 2.2)
    for side in ("l", "r"):
        a.rot(f"arm_{side}", (0, Z3), (0.9, (-175, 0, 0)), (1.1, (-35, 0, 0), "linear"), (1.6, (-30, 0, 0)), (2.2, Z3))
        a.rot(f"forearm_{side}", (0, Z3), (0.9, (-20, 0, 0)), (1.1, (-10, 0, 0), "linear"), (2.2, Z3))
    a.rot("torso", (0, Z3), (0.9, (-22, 0, 0)), (1.1, (32, 0, 0), "linear"), (1.6, (30, 0, 0)), (2.2, Z3))
    a.rot("head", (0, Z3), (0.9, (-15, 0, 0)), (1.1, (5, 0, 0)), (2.2, Z3))
    a.pos("hips", (0, Z3), (0.9, (0, 3, 0)), (1.1, (0, -5, 0), "linear"), (1.6, (0, -5, 0)), (2.2, Z3))
    a.rot("leg_l", (0, Z3), (1.1, (-25, 0, 0), "linear"), (1.6, (-25, 0, 0)), (2.2, Z3))
    a.rot("shin_l", (0, Z3), (1.1, (30, 0, 0), "linear"), (1.6, (30, 0, 0)), (2.2, Z3))

    # ---------------------------------------------------------------- stomp: lifts the right leg high,
    # stamps (impact 0.8 s = 16 t)
    a = m.anim("stomp", 1.6)
    a.rot("leg_r", (0, Z3), (0.65, (-70, 0, 0)), (0.8, (0, 0, 0), "linear"), (1.6, Z3))
    a.rot("shin_r", (0, Z3), (0.65, (60, 0, 0)), (0.8, Z3, "linear"), (1.6, Z3))
    a.rot("torso", (0, Z3), (0.65, (-12, 0, -8)), (0.8, (10, 0, 4), "linear"), (1.6, Z3))
    a.rot("arm_l", (0, Z3), (0.65, (-30, 0, -30)), (0.8, (10, 0, 0)), (1.6, Z3))
    a.rot("arm_r", (0, Z3), (0.65, (-20, 0, 25)), (0.8, (10, 0, 0)), (1.6, Z3))
    a.pos("hips", (0, Z3), (0.65, (0, 2, 0)), (0.8, (0, -2, 0), "linear"), (1.6, Z3))

    # ---------------------------------------------------------------- throw: tears a boulder up with the right
    # fist, winds back over the shoulder, hurls (release 1.0 s = 20 t)
    a = m.anim("throw", 2.0)
    a.rot("arm_r", (0, Z3), (0.35, (20, 0, 0)), (0.8, (-160, 0, 25)), (1.0, (-50, 0, -10), "linear"), (1.4, (-30, 0, 0)), (2.0, Z3))
    a.rot("forearm_r", (0, Z3), (0.35, (-30, 0, 0)), (0.8, (-60, 0, 0)), (1.0, (0, 0, 0), "linear"), (2.0, Z3))
    a.rot("torso", (0, Z3), (0.35, (18, 0, 0)), (0.8, (-14, 35, 0)), (1.0, (14, -30, 0), "linear"), (1.4, (10, -25, 0)), (2.0, Z3))
    a.rot("arm_l", (0, Z3), (0.8, (-40, 0, -25)), (1.0, (10, 0, -10)), (2.0, Z3))
    a.rot("head", (0, Z3), (0.8, (-10, -20, 0)), (1.0, (5, 20, 0)), (2.0, Z3))

    # ---------------------------------------------------------------- beam: leans back, the head and the
    # chest ring charge, then a long rune beam (fires 1.1 s = 22 t, held ~0.8 s)
    a = m.anim("beam", 2.6)
    a.rot("torso", (0, Z3), (0.9, (-18, 0, 0)), (1.1, (8, 0, 0), "linear"), (1.9, (10, 0, 0)), (2.6, Z3))
    a.rot("head", (0, Z3), (0.9, (-22, 0, 0)), (1.1, (8, 0, 0), "linear"), (1.9, (10, 0, 0)), (2.6, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"arm_{side}", (0, Z3), (0.9, (-20, 0, sx * -45)), (1.1, (-10, 0, sx * -60), "linear"), (1.9, (-10, 0, sx * -60)), (2.6, Z3))
        a.rot(f"forearm_{side}", (0, Z3), (0.9, (-40, 0, 0)), (1.9, (-30, 0, 0)), (2.6, Z3))
    a.pos("hips", (0, Z3), (0.9, (0, 1, 2)), (1.1, (0, -1, -1), "linear"), (1.9, (0, -1, -1)), (2.6, Z3))

    # ---------------------------------------------------------------- sweep: backhand with the long left arm
    # across the front (impact 0.85 s = 17 t)
    a = m.anim("sweep", 1.8)
    a.rot("torso", (0, Z3), (0.7, (0, 40, 0)), (0.85, (6, -45, 0), "linear"), (1.2, (5, -40, 0)), (1.8, Z3))
    a.rot("arm_l", (0, Z3), (0.7, (-70, 0, -70)), (0.85, (-80, 0, 30), "linear"), (1.2, (-60, 0, 30)), (1.8, Z3))
    a.rot("forearm_l", (0, Z3), (0.7, (-20, 0, 0)), (0.85, (-5, 0, 0)), (1.8, Z3))
    a.rot("arm_r", (0, Z3), (0.7, (20, 0, 20)), (0.85, (-20, 0, 0)), (1.8, Z3))

    # ---------------------------------------------------------------- overload (phase 2): both fists driven
    # into the ground, runes surge down the arms (impact 1.0 s = 20 t), held while the lines erupt
    a = m.anim("overload", 3.0)
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"arm_{side}", (0, Z3), (0.8, (-150, 0, sx * -25)), (1.0, (-40, 0, sx * 10), "linear"), (2.4, (-40, 0, sx * 10)), (3.0, Z3))
        a.rot(f"forearm_{side}", (0, Z3), (0.8, (-30, 0, 0)), (1.0, (-30, 0, 0)), (2.4, (-30, 0, 0)), (3.0, Z3))
    a.rot("torso", (0, Z3), (0.8, (-25, 0, 0)), (1.0, (40, 0, 0), "linear"), (2.4, (40, 0, 0)), (3.0, Z3))
    a.rot("head", (0, Z3), (0.8, (-20, 0, 0)), (1.0, (-20, 0, 0)), (2.4, (-25, 0, 0)), (3.0, Z3))
    a.pos("hips", (0, Z3), (0.8, (0, 3, 0)), (1.0, (0, -8, 0), "linear"), (2.4, (0, -8, 0)), (3.0, Z3))
    for side in ("l", "r"):
        a.rot(f"leg_{side}", (0, Z3), (1.0, (-30, 0, 0), "linear"), (2.4, (-30, 0, 0)), (3.0, Z3))
        a.rot(f"shin_{side}", (0, Z3), (1.0, (45, 0, 0), "linear"), (2.4, (45, 0, 0)), (3.0, Z3))

    # ---------------------------------------------------------------- detach (phase 2): the right forearm tears
    # free on a tether of runes, flies forward and crashes down 4 blocks ahead (impact 1.2 s = 24 t), returns
    a = m.anim("detach", 2.6)
    # (offsets are in the raised arm's frame: local +y points forward, local +z points down)
    a.rot("arm_r", (0, Z3), (0.8, (-80, 0, 0)), (2.0, (-80, 0, 0)), (2.6, Z3))
    a.pos("forearm_r", (0, Z3), (0.8, (0, 0, 2)), (1.0, (0, -30, -22)), (1.2, (0, -60, 28), "linear"),
          (1.9, (0, -60, 28)), (2.3, (0, -12, 4)), (2.6, Z3))
    a.rot("forearm_r", (0, Z3), (0.8, (-30, 0, 0)), (1.0, (40, 0, 0)), (1.2, (108, 0, 0), "linear"),
          (1.9, (108, 0, 0)), (2.3, (20, 0, 0)), (2.6, Z3))
    a.rot("torso", (0, Z3), (0.8, (-15, 20, 0)), (1.2, (15, -10, 0), "linear"), (2.0, (12, -10, 0)), (2.6, Z3))
    a.rot("arm_l", (0, Z3), (0.8, (-30, 0, -30)), (1.2, (10, 0, -10)), (2.6, Z3))

    # ---------------------------------------------------------------- roar (phase change): rears up, arms out,
    # the crown capstone grinds
    a = m.anim("roar", 2.6)
    a.rot("torso", (0, Z3), (0.6, (-28, 0, 0)), (2.0, (-28, 0, 0)), (2.6, Z3))
    a.rot("head", (0, Z3), (0.6, (-20, 0, 0)), (1.2, (-20, 12, 0)), (1.6, (-20, -12, 0)), (2.0, (-20, 0, 0)), (2.6, Z3))
    a.rot("crown", (0, Z3), (0.6, (0, 0, 8)), (1.3, (0, 0, -3)), (2.0, (0, 0, 6)), (2.6, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"arm_{side}", (0, Z3), (0.6, (-40, 0, sx * -70)), (2.0, (-40, 0, sx * -75)), (2.6, Z3))
        a.rot(f"forearm_{side}", (0, Z3), (0.6, (-50, 0, 0)), (2.0, (-50, 0, 0)), (2.6, Z3))

    # ---------------------------------------------------------------- stagger: knees buckle, one fist props it up
    a = m.anim("stagger", 2.4)
    a.pos("hips", (0, Z3), (0.35, (0, -12, 0)), (1.9, (0, -12, 0)), (2.4, Z3))
    a.rot("leg_l", (0, Z3), (0.35, (-70, 0, 0)), (1.9, (-70, 0, 0)), (2.4, Z3))
    a.rot("shin_l", (0, Z3), (0.35, (80, 0, 0)), (1.9, (80, 0, 0)), (2.4, Z3))
    a.rot("leg_r", (0, Z3), (0.35, (-20, 0, 10)), (1.9, (-20, 0, 10)), (2.4, Z3))
    a.rot("shin_r", (0, Z3), (0.35, (60, 0, 0)), (1.9, (60, 0, 0)), (2.4, Z3))
    a.rot("torso", (0, Z3), (0.35, (30, 0, 8)), (1.9, (30, 0, 8)), (2.4, Z3))
    a.rot("head", (0, Z3), (0.35, (10, 15, 10)), (1.9, (10, 15, 10)), (2.4, Z3))
    a.rot("arm_r", (0, Z3), (0.35, (-25, 0, 0)), (1.9, (-25, 0, 0)), (2.4, Z3))
    a.rot("arm_l", (0, Z3), (0.35, (25, 0, -20)), (1.9, (25, 0, -20)), (2.4, Z3))
    a.rot("crown", (0, Z3), (0.35, (0, 0, 10)), (1.9, (0, 0, 10)), (2.4, Z3))
