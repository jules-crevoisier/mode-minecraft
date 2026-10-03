"""Map Wraith (Spectre des cartes): a hovering paper ghost, about 1.8 blocks tall.

Silhouette: a hunched body bound in strips of old maps and letters under a pointed parchment hood whose
opening is an ink-black void, a rolled scroll across the shoulders, a great sea chart worn as a cloak,
long thin arms ending in fans of quill fingers dripping ink, a skirt of loose page strips that never touches
the ground, and a few pages orbiting it.
"""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
PAPER = (226, 210, 168)
PAPER_L = (244, 234, 204)
PAPER_D = (186, 160, 112)
AGED = (150, 116, 70)
FOX = (170, 128, 78)          # foxing spots
INK = (30, 26, 34)
INK_L = (70, 62, 78)
INK_B = (44, 58, 92)          # blue-black chart ink
SEA = (196, 204, 182)
LAND = (212, 184, 124)
SEAL = (160, 36, 30)
VOID = (8, 6, 12)
EYE = (226, 236, 255)
QUILL = (236, 232, 220)
QUILL_D = (176, 170, 160)

FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
def parchment_px(x, y, seed=0, fid=0, base=PAPER):
    """Old paper: warm tone drifting across the sheet, foxing spots, a few fibres."""
    t = 0.5 + 0.5 * math.sin(x * 0.7 + seed) * math.cos(y * 0.45 + seed * 0.3)
    c = mix(base, PAPER_D, 0.25 * t)
    r = _h(x, y, seed, fid)
    if r % 29 == 0:
        c = mix(c, FOX, 0.55)
    elif r % 37 == 0:
        c = mix(c, PAPER_L, 0.6)
    return c


def script(seed=0, ragged=0, base=PAPER, ink=INK, margin=1, edge=True):
    """A page of handwriting: lines of ink words every two texels, an aged edge and a torn bottom."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face in ("top", "bottom"):
            return mul(base, 0.9)
        if ragged and y >= h - 1 - (_h(seed, x, fid) % (ragged + 1)):
            return None
        c = parchment_px(x, y, seed, fid, base)
        if edge and (x == 0 or x == w - 1) and w > 2:
            c = mix(c, AGED, 0.45)
        line = (y + seed) % 3 == 1
        if line and margin <= x < w - margin and y < h - ragged - 1:
            word = _h(seed, y, (x + _h(seed, y) % 4) // 4, fid) % 3
            if word != 0 and (x + _h(seed, y)) % 4 != 3:
                c = mix(c, ink, 0.5 if _h(x, y, seed) % 3 else 0.7)
        return c
    return f


def chart(seed=0, ragged=0, compass=None, cross=None):
    """A sea chart: wavy coastline in blue-black ink, ochre land with hatching, sea with wave marks, faint
    lat/long grid, a dotted red route, an optional compass star and a red X."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face in ("top", "bottom"):
            return PAPER_D
        if ragged and y >= h - 1 - (_h(seed, x, fid) % (ragged + 1)):
            return None
        coast = w * 0.5 + 2.6 * math.sin(y * 0.55 + seed) + 1.4 * math.sin(y * 1.3 + seed * 2)
        land = x > coast
        c = parchment_px(x, y, seed, fid, LAND if land else SEA)
        if abs(x - coast) < 0.75:
            return INK_B
        if land and (x + y) % 4 == 0:
            c = mix(c, AGED, 0.4)                       # hatching
        if not land and y % 4 == 1 and (x + y // 4) % 3 == 0:
            c = mix(c, INK_B, 0.45)                     # wave marks
        if (x + seed) % 6 == 0 or (y + seed) % 7 == 0:
            c = mix(c, PAPER_D, 0.45)                   # grid
        route_x = int(w * 0.3 + y * 0.35) % max(1, w)
        if x == route_x and y % 2 == 0:
            c = SEAL                                    # dotted route
        if compass and face in ("back", "front"):
            cx, cy = compass
            dx, dy = x - cx, y - cy
            if (dx == 0 and abs(dy) <= 2) or (dy == 0 and abs(dx) <= 2):
                c = INK
            elif abs(dx) == 1 and abs(dy) == 1:
                c = INK_L
        if cross and face in ("back", "front"):
            cx, cy = cross
            if abs(x - cx) == abs(y - cy) and abs(x - cx) <= 1:
                c = SEAL
        if (x == 0 or x == w - 1) and w > 2:
            c = mix(c, AGED, 0.4)
        return c
    return f


def folded(seed=0):
    """Folded parchment (the hood): soft vertical creases with a lit edge, ink blots, a scrap of chart on
    the left side and a line of writing along the bottom hem."""
    m = chart(seed + 5)

    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face == "left" and 1 <= y <= 4 and 1 <= x <= w - 2:
            return m(face, x, y, w, h)
        c = parchment_px(x, y, seed, fid)
        k = (x + _h(seed, fid) % 3) % 4
        if k == 0:
            c = mix(c, PAPER_D, 0.45)                 # crease shadow
        elif k == 1:
            c = mix(c, PAPER_L, 0.35)                 # lit side of the fold
        if face not in ("top", "bottom") and y == h - 2 and _h(seed, x // 3, fid) % 3:
            c = mix(c, INK, 0.5)                      # writing along the hem
        if _h(x // 2, y // 2, seed, fid) % 23 == 0:
            c = mix(c, INK_L, 0.55)                   # ink blot
        return c
    return f


def wrapped(seed=0):
    """Bandage wrap of torn strips running diagonally (gaps let the dark body show through)."""
    s = script(seed, edge=False, margin=0)
    m = chart(seed + 3)

    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        k = (x + y + _h(seed, FACE_N[face]) % 3) // 3
        if k % 3 == 2:
            return None
        if (x + y) % 3 == 0:
            return mix(parchment_px(x, y, seed), AGED, 0.5)   # strip edge shadow
        return m(face, x, y, w, h) if k % 4 == 0 else s(face, x, y, w, h)
    return f


def shadow_body(face, x, y, w, h):
    r = _h(x, y, 77)
    return (44, 38, 42) if r % 5 else (26, 22, 28)


def quill(seed=0):
    """A quill finger: off-white shaft, the nib (bottom) black and wet with ink."""
    def f(face, x, y, w, h):
        if y >= h - 2:
            return INK if y == h - 1 else INK_L
        if face == "bottom":
            return INK
        return QUILL if (y + seed) % 3 else QUILL_D
    return f


def vane(seed=0):
    """Feather vane plane: barbs slanting down to the shaft, darker tip band."""
    def f(face, x, y, w, h):
        if y < 1 and x > 0:
            return None
        if (x + y + seed) % 2 == 0:
            c = QUILL
        else:
            c = mix(QUILL, QUILL_D, 0.6)
        if y == h - 1:
            c = mix(c, INK_L, 0.4)
        if x == w - 1 and (y + seed) % 3 == 0:
            return None                                 # split barbs
        return c
    return f


# ------------------------------------------------------------------ model
STRIPS = [  # (name, x, z, length, flutter phase, outward flare (rx, rz) for the scatter)
    ("strip_f1", -3.0, -3.0, 10, 0.0, (-45, -12)),
    ("strip_f2", 0.0, -3.4, 9, 0.5, (-50, 0)),
    ("strip_f3", 3.0, -3.0, 10, 1.0, (-45, 12)),
    ("strip_r", -4.2, 0.0, 9, 1.5, (0, -50)),
    ("strip_l", 4.2, 0.0, 10, 0.3, (0, 50)),
    ("strip_b1", -2.5, 3.2, 10, 0.8, (45, -10)),
    ("strip_b2", 2.5, 3.2, 9, 1.3, (45, 10)),
]
PAGES = [("page_1", (9, 0, 0), (0, 70, 15)), ("page_2", (-6, -4, 6), (10, -30, -20)),
         ("page_3", (-4, 3, -8), (-15, 20, 10))]


def build():
    m = Model("map_wraith", seed=33, shadow=0.5, walk_speed=1.2, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -11, 0), rot=(10, 0, 0))
    m.part("head", "body", pivot=(0, -8, -1), rot=(-8, 0, 0))
    m.part("hood_tip", "head", pivot=(0, -7.5, 1.5), rot=(-30, 0, 0))
    m.part("hood_tip2", "hood_tip", pivot=(0, -4, 0.5), rot=(-45, 0, 0))
    m.part("cape", "body", pivot=(0, -8.5, 3.6), rot=(14, 0, 0))
    m.part("arm_r", "body", pivot=(-5.5, -7, -0.5), rot=(-52, 0, 22))
    m.part("forearm_r", "arm_r", pivot=(0, 5.5, 0), rot=(-8, 0, 0))
    m.part("arm_l", "body", pivot=(5.5, -7, -0.5), rot=(-52, 0, -22))
    m.part("forearm_l", "arm_l", pivot=(0, 5.5, 0), rot=(-8, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        for i, (dx, rz) in enumerate(((-1, -16), (0, 0), (1, 16))):
            m.part(f"quill_{side}{i}", f"forearm_{side}", pivot=(dx * 0.9, 4.5, 0), rot=(-22, 0, rz * 1.4))
    for name, x, z, length, _, _ in STRIPS:
        m.part(name, "body", pivot=(x, 0, z))
    m.part("pages", "bone", pivot=(0, -15, 0))
    for name, pos, rot in PAGES:
        m.part(name, "pages", pivot=pos, rot=rot)

    # ------------------------------------------------------------------ body
    m.box("body", -4, -8, -3, 8, 8, 6, shadow_body)
    m.box("body", -4, -8, -3, 8, 8, 6, wrapped(1), grow=0.35)
    # a short ragged capelet of letters over the shoulders
    m.box("body", -5, -9, -3.5, 10, 4, 7, script(4, ragged=2, edge=False))
    # rolled scroll laid across the back of the shoulders, curled ends
    m.box("body", -7, -10, 1, 14, 2, 2, {"left": lambda f_, x, y, w, h: AGED if (x + y) % 2 else PAPER_D,
                                         "right": lambda f_, x, y, w, h: AGED if (x + y) % 2 else PAPER_D,
                                         "*": script(5, edge=False, margin=0)})
    m.box("body", -1, -6, -3.8, 2, 2, 1, lambda f_, x, y, w, h: SEAL if (x + y) % 3 else (120, 24, 20))  # wax seal

    # head: a pointed hood of parchment around an ink-black void
    def hood_front(f_, x, y, w, h):
        if 1 <= x <= w - 2 and 1 <= y:
            return None  # the opening
        return mix(parchment_px(x, y, 9), AGED, 0.35 if y == 0 or x in (0, w - 1) else 0)
    hood = folded(9)
    m.box("head", -4, -8, -4.5, 8, 9, 8, {"front": hood_front, "*": hood})
    eye_pts = {(1, 3), (5, 3)}

    def void_face(f_, x, y, w, h):
        if (x, y) in eye_pts:
            return EYE
        if y >= h - 2 and x % 2 == 0:
            return INK_L  # ink dripping from the void
        return VOID if (x + y) % 4 else (16, 12, 22)
    eye_pts = {(1, 3), (4, 3)}
    m.box("head", -3, -7, -3, 6, 7, 6, {"front": void_face, "*": VOID},
          glow={"front": lambda f_, x, y, w, h: (180, 196, 255) if (x, y) in eye_pts else None, "*": None})
    # overhanging brim of the hood
    m.box("head", -4.5, -8.5, -5.5, 9, 2, 2, folded(12))
    # pointed hood peak curling back, ink-stained tip
    m.box("hood_tip", -3, -4, -3, 6, 4, 5, folded(10))
    m.box("hood_tip2", -1.5, -4, -1.5, 3, 4, 3, folded(11))
    m.box("hood_tip2", -0.5, -6, -0.5, 1, 2, 1, lambda f_, x, y, w, h: INK_L if y == 0 else AGED)
    # ink drips under the hood rim
    m.box("head", -3, 1, -4.5, 1, 2, 0, {"front": lambda f_, x, y, w, h: INK, "back": lambda f_, x, y, w, h: INK, "*": None})
    m.box("head", 2, 1, -4.5, 1, 3, 0, {"front": lambda f_, x, y, w, h: INK if y < 2 else INK_L,
                                        "back": lambda f_, x, y, w, h: INK, "*": None})

    # great sea chart worn as a cloak
    m.box("cape", -5, 0, 0, 10, 18, 1, {"back": chart(2, ragged=3, compass=(3, 4), cross=(7, 11)),
                                         "front": chart(3, ragged=3), "*": PAPER_D})

    # skirt of hanging strips (letters and chart scraps)
    for i, (name, x, z, length, _, _) in enumerate(STRIPS):
        paint = chart(20 + i, ragged=2) if i % 3 == 1 else script(20 + i, ragged=2)
        m.box(name, -1.5, 0, -0.5, 3, length, 1, paint)

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.5, -0.5, -1.5, 3, 6, 3, {"*": script(40 + sx, edge=False, margin=0), "top": PAPER_D})
        m.box(arm, -2, -1.5, -2, 4, 3, 4, wrapped(42 + sx))  # shoulder wrap
        m.box(fore, -1.5, 0, -1.5, 3, 5, 3, script(44 + sx, edge=False, margin=0))
        m.box(fore, -1.5, 2, -1.5, 3, 3, 3, wrapped(46 + sx), grow=0.3)  # wrapped wrist
        for i in range(3):
            q = f"quill_{side}{i}"
            m.box(q, -0.5, 0, -0.5, 1, 8 if i == 1 else 7, 1, quill(i))
            m.box(q, 0, 0, 0.5, 0, 5, 2, {"left": vane(i), "right": vane(i), "*": None})

    # ------------------------------------------------------------------ orbiting pages
    for i, (name, _, _) in enumerate(PAGES):
        paint = script(60 + i, ragged=0) if i != 1 else chart(61, compass=(1, 2))
        m.box(name, -2, -2.5, 0, 4, 5, 0, {"front": paint, "back": script(63 + i), "*": None})

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.4)
    idle.pos("bone", (0, (0, 0, 0)), (1.2, (0, 1.5, 0)), (2.4, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.2, (3, 0, 2)), (2.4, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 0, 6)), (1.8, (0, 0, -6)), (2.4, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (0.8, (10, 0, 2)), (1.6, (4, 0, -2)), (2.4, (0, 0, 0)))
    for name, x, z, length, phase, _ in STRIPS:
        amp = 12 if z else 8
        ax = (amp if z < 0 else -amp if z > 0 else 0)
        az = (amp if x > 0 else -amp) if not z else 0
        keys = []
        for k in range(5):
            t = k * 0.6
            s = math.sin((t / 2.4 + phase / 2.4) * 2 * math.pi)
            keys.append((t, (-ax * 0.5 * (1 + s) + 4 * s, 0, az * 0.5 * (1 + s))))
        keys[-1] = (2.4, keys[0][1])
        idle.rot(name, *keys)
    idle.rot("pages", (0, (0, 0, 0), "linear"), (2.4, (0, 360, 0), "linear"))
    for i, (name, _, _) in enumerate(PAGES):
        idle.rot(name, (0, (0, 0, 0)), (0.6 + 0.2 * i, (20, 0, 10)), (1.6 + 0.2 * i, (-15, 0, -10)), (2.4, (0, 0, 0)))
        idle.pos(name, (0, (0, 0, 0)), (1.2, (0, 2 if i % 2 else -2, 0)), (2.4, (0, 0, 0)))
    for side in ("r", "l"):
        idle.rot(f"arm_{side}", (0, (0, 0, 0)), (1.2, (-8, 0, 0)), (2.4, (0, 0, 0)))
        for i in range(3):
            idle.rot(f"quill_{side}{i}", (0, (0, 0, 0)), (0.4 + 0.25 * i, (-12, 0, 0)), (1.0 + 0.25 * i, (6, 0, 0)),
                     (2.4, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("body", (0, (16, 0, 0)), (0.6, (18, 0, 0)), (1.2, (16, 0, 0)))
    walk.rot("head", (0, (-12, 0, 0)), (0.6, (-14, 0, 0)), (1.2, (-12, 0, 0)))
    walk.rot("cape", (0, (8, 0, 0)), (0.3, (15, 0, 3)), (0.6, (10, 0, 0)), (0.9, (15, 0, -3)), (1.2, (8, 0, 0)))
    for name, x, z, length, phase, _ in STRIPS:
        walk.rot(name, (0, (18, 0, 0)), (0.3 + phase * 0.1, (30, 0, 0)), (0.9, (14, 0, 0)), (1.2, (18, 0, 0)))
    for side in ("r", "l"):
        walk.rot(f"arm_{side}", (0, (18, 0, 0)), (0.6, (26, 0, 0)), (1.2, (18, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (1.2, (0, 0, 0)))

    # rake: both quill hands drawn up and back (telegraph), slashed down crosswise at 0.5 s (10 ticks)
    a = m.anim("rake", 1.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (-150, 0, 30)), (0.5, (-35, 0, -35), "linear"), (0.7, (-30, 0, -30)),
          (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.35, (-150, 0, -30)), (0.5, (-35, 0, 35), "linear"), (0.7, (-30, 0, 30)),
          (1.0, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.35, (-40, 0, 0)), (0.5, (10, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.35, (-40, 0, 0)), (0.5, (10, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (-14, 0, 0)), (0.5, (24, 0, 0), "linear"), (0.7, (20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.35, (-20, 0, 0)), (0.5, (-10, 0, 0)), (1.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.35, (0, 2, 2)), (0.5, (0, -1, -4), "linear"), (0.7, (0, -1, -4)), (1.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.35, (-6, 0, 0)), (0.5, (16, 0, 0)), (1.0, (0, 0, 0)))
    for name, x, z, length, phase, _ in STRIPS:
        a.rot(name, (0, (0, 0, 0)), (0.35, (-10, 0, 0)), (0.55, (35, 0, 0)), (1.0, (0, 0, 0)))

    # scatter: struck, the wraith bursts apart a little - pages fly outward, then it gathers itself again
    a = m.anim("scatter", 0.8)
    a.rot("body", (0, (0, 0, 0)), (0.1, (-22, 0, 6), "linear"), (0.45, (-10, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.1, (-25, 0, -8), "linear"), (0.45, (-10, 0, 0)), (0.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.1, (0, 2, 3), "linear"), (0.45, (0, 1, 1)), (0.8, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.1, (-30, 0, 60), "linear"), (0.45, (-10, 0, 20)), (0.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.1, (-30, 0, -60), "linear"), (0.45, (-10, 0, -20)), (0.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.1, (30, 0, 0), "linear"), (0.45, (12, 0, 0)), (0.8, (0, 0, 0)))
    for name, x, z, length, phase, (fx, fz) in STRIPS:
        a.rot(name, (0, (0, 0, 0)), (0.1, (fx, 0, fz), "linear"), (0.45, (fx * 0.3, 0, fz * 0.3)), (0.8, (0, 0, 0)))
    a.scale("pages", (0, (1, 1, 1)), (0.12, (1.7, 1.3, 1.7), "linear"), (0.5, (1.15, 1.05, 1.15)), (0.8, (1, 1, 1)))
    a.rot("pages", (0, (0, 0, 0)), (0.12, (0, 60, 0), "linear"), (0.8, (0, 0, 0)))
    return m
