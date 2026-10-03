"""Ember Imp (Imp de braise): a small Nether fire imp (about 1 block). A big horned head with a wicked
fanged grin and glowing yellow eyes, a pot belly that burns through its charcoal skin, little goat legs,
leathery bat wings that never stop beating, and a long whip tail ending in a glowing ember spade. Its skin
is cracked like cooling lava: the cracks glow.

Animations: idle (hovering with fast wing beats), walk (bouncy hopping flutter), throw (a fire orb grows in
the raised hand, released at 0.5 s = 10 ticks), hop (a big evasive leap back), cackle (head thrown back,
jaw chattering, belly shaking).
"""
from ..models import Model
from ..texgen import mix, mul

SKIN = (92, 34, 28)
SKIN_D = (56, 20, 20)
SKIN_L = (128, 54, 40)
BELLY = (150, 70, 36)
HORN = (40, 32, 32)
HORN_L = (92, 80, 76)
MEMBRANE = (110, 30, 26)
MEMBRANE_D = (66, 16, 16)
EMBER = (255, 150, 40)
EMBER_HOT = (255, 226, 120)
EYE = (255, 236, 90)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}
_CRACKS = {}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def cracks(face, w, h, seed, n=1):
    """Deterministic jagged crack paths on a face: a set of texels."""
    key = (face, w, h, seed, n)
    if key not in _CRACKS:
        pts = set()
        for k in range(n):
            x = _h(seed, k, FACE_N[face]) % max(1, w)
            y0 = _h(seed, k, 5, FACE_N[face]) % max(1, h // 2)
            y1 = min(h, y0 + h // 2 + _h(seed, k, 6) % (h // 2 + 1))
            for y in range(y0, y1):
                if 0 <= x < w:
                    pts.add((x, y))
                step = (_h(seed, k, y, FACE_N[face]) % 5) // 2 - 1 if y % 2 else 0
                x = max(0, min(w - 1, x + step))
            # a short branch
            by = _h(seed, k, 77) % max(1, h)
            bx = next((px for px, py in pts if py == by), 0)
            for i in range(1, 2):
                if 0 <= bx + i < w and by + i < h:
                    pts.add((bx + i, by + i))
        _CRACKS[key] = pts
    return _CRACKS[key]


def skin(seed=0, base=SKIN, n=1, belly=False):
    """Charcoal hide with dark, soot-edged cracks (the glow layer lights them)."""
    def f(face, x, y, w, h):
        r = _h(x, y, seed, FACE_N[face])
        c = mul(base, 1 + ((r % 100) - 50) / 600)
        if face == "top":
            c = mix(c, SKIN_L, 0.3)
        elif face == "bottom":
            c = mix(c, SKIN_D, 0.5)
        if belly and face == "front":
            c = mix(c, BELLY, 0.6)
        if face not in ("top", "bottom") and min(w, h) >= 4 and (x, y) in cracks(face, w, h, seed, n):
            return (40, 12, 8)
        if r % 19 == 0:
            c = mix(c, SKIN_D, 0.6)               # soot
        return c
    return f


def ember_glow(seed=0, n=1, belly=False, hot=False):
    def f(face, x, y, w, h):
        if belly and face == "front":
            # the belly burns from within: a hot core with radiating cracks
            cx, cy = (w - 1) / 2, (h - 1) / 2 + 0.5
            d = abs(x - cx) + abs(y - cy)
            if d <= 0.6:
                return EMBER_HOT
            if d <= 1.6:
                return (*EMBER, 170)
            if (x, y) in cracks(face, w, h, seed, n):
                return (*EMBER, 200)
            return None
        if face in ("top", "bottom") or min(w, h) < 4:
            return None
        if (x, y) in cracks(face, w, h, seed, n) and _h(x, y, seed, 3) % 4:
            return EMBER_HOT if hot and _h(x, y, seed) % 3 == 0 else (*EMBER, 210)
        return None
    return f


def horn(face, x, y, w, h):
    t = y / max(1, h - 1)
    c = mix(HORN_L, HORN, t) if face not in ("top", "bottom") else HORN
    return mul(c, 0.85) if y % 2 else c


def membrane(seed=0, side=1):
    """Bat wing: dark red membrane, bony fingers fanning out, scalloped lower edge."""
    def f(face, x, y, w, h):
        if face not in ("front", "back"):
            return MEMBRANE_D
        u = x if side > 0 else w - 1 - x   # 0 at the body
        # three bays between the fingers along the outer edge
        bay = w / 3.0
        k = (u % bay) / bay
        if y >= h - 1 - int(2.5 * (1 - abs(k - 0.5) * 2)) and u > 1:
            return None
        if y == 0:
            return HORN                    # the arm bone along the top
        if int(u % bay) == 0 and u > 0:
            return mix(HORN, MEMBRANE_D, 0.3)   # finger
        c = mix(MEMBRANE, MEMBRANE_D, y / max(1, h - 1) * 0.7)
        if (u + y * 2 + seed) % 7 == 0:
            c = mix(c, (150, 50, 30), 0.4)   # veins
        return c
    return f


def membrane_glow(side=1):
    def f(face, x, y, w, h):
        if face not in ("front", "back"):
            return None
        u = x if side > 0 else w - 1 - x
        bay = w / 3.0
        if y == h - 3 and int(u % bay) == 1:
            return (*EMBER, 120)
        return None
    return f


def face_front(face, x, y, w, h):
    """Head front (w=7, h=6): heavy brow, big glowing eyes, a wide grin of fangs across the bottom."""
    base = skin(5, cracks_n := 0)(face, x, y, w, h) if False else skin(5, n=0)(face, x, y, w, h)
    if y == 1 and x in (1, 2, 4, 5):
        return SKIN_D                       # brow shadow
    if y == 2 and x in (1, 2, 4, 5):
        return (60, 40, 10)
    if y == 4 and 1 <= x <= 5:
        return (240, 230, 210) if x % 2 == 1 else (30, 8, 6)    # upper fangs
    if y == 3 and x == 3:
        return SKIN_D                       # nose slit
    return base


def eye_glow(face, x, y, w, h):
    if face == "front" and y == 2 and x in (1, 2, 4, 5):
        return EYE if x in (2, 4) else (255, 180, 60)
    return None


def build():
    m = Model("ember_imp", seed=59, shadow=0.35, walk_speed=1.4, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -8, 0))
    m.part("head", "body", pivot=(0, -6.5, -0.5))
    m.part("jaw", "head", pivot=(0, -1, -1))
    m.part("horn_r", "head", pivot=(-2.5, -6, -1.5), rot=(-25, 0, -30))
    m.part("horn_r2", "horn_r", pivot=(0, -3, 0), rot=(-40, 0, 15))
    m.part("horn_l", "head", pivot=(2.5, -6, -1.5), rot=(-25, 0, 30))
    m.part("horn_l2", "horn_l", pivot=(0, -3, 0), rot=(-40, 0, -15))
    m.part("arm_r", "body", pivot=(-3.5, -5.5, 0), rot=(-10, 0, 20))
    m.part("forearm_r", "arm_r", pivot=(0, 3.5, 0), rot=(-40, 0, 0))
    m.part("orb", "forearm_r", pivot=(0, 5, -0.5), scale=(0.02, 0.02, 0.02))
    m.part("arm_l", "body", pivot=(3.5, -5.5, 0), rot=(-10, 0, -20))
    m.part("forearm_l", "arm_l", pivot=(0, 3.5, 0), rot=(-40, 0, 0))
    m.part("leg_r", "body", pivot=(-1.5, 0.5, 0), rot=(-30, 0, 5))
    m.part("shin_r", "leg_r", pivot=(0, 3, 0), rot=(55, 0, 0))
    m.part("leg_l", "body", pivot=(1.5, 0.5, 0), rot=(-30, 0, -5))
    m.part("shin_l", "leg_l", pivot=(0, 3, 0), rot=(55, 0, 0))
    m.part("wing_r", "body", pivot=(-1.5, -5.5, 2), rot=(-10, 30, -22))
    m.part("wing_l", "body", pivot=(1.5, -5.5, 2), rot=(-10, -30, 22))
    m.part("tail", "body", pivot=(0, -0.5, 2), rot=(-35, 0, 0))
    m.part("tail2", "tail", pivot=(0, 0, 5), rot=(45, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 0, 4), rot=(55, 0, 0))

    # body: a pot belly that glows from within, narrow chest
    m.box("body", -3, -4, -2.5, 6, 5, 5, {"front": skin(1, belly=True), "*": skin(1)},
          glow=ember_glow(1, belly=True))
    m.box("body", -3.5, -6.5, -2, 7, 3, 4, skin(2), glow=ember_glow(2))

    # head: big skull, glowing eyes, fanged grin, pointed ears, swept horns
    m.box("head", -3.5, -6, -3.5, 7, 5, 6, {"front": face_front, "*": skin(5)}, glow={"front": eye_glow, "*": ember_glow(5)})
    m.box("head", -1, -3, -4.5, 2, 2, 1, skin(6, n=0))                         # snout
    m.box("jaw", -3, 0, -2.5, 6, 2, 5, {"front": lambda f_, x, y, w, h: (240, 230, 210) if y == 0 and x % 2 == 0
                                       else skin(7, n=0)(f_, x, y, w, h), "top": (70, 12, 6), "*": skin(7, n=0)},
          glow={"top": lambda f_, x, y, w, h: (*EMBER, 160)})
    m.box("jaw", -1, 2, -2, 2, 1, 2, skin(8, n=0))                             # pointed chin
    for sx in (-1, 1):
        m.box("head", 3.5 if sx > 0 else -6.5, -4.5, -0.5, 3, 1, 2, skin(9, n=0))    # ear
        m.box("head", 5.5 if sx > 0 else -7.5, -5.5, 0, 2, 1, 1, skin(10, n=0))     # ear tip
    for side in ("r", "l"):
        m.box(f"horn_{side}", -1, -3, -1, 2, 3, 2, horn)
        m.box(f"horn_{side}2", -0.5, -3, -0.5, 1, 3, 1, horn, glow=lambda f_, x, y, w, h: (*EMBER, 200) if y == 0 else None)

    # arms with claws, a fire orb hidden in the right hand (grows during the throw)
    for side in ("r", "l"):
        m.box(f"arm_{side}", -0.5, 0, -0.5, 1, 4, 1, skin(20))
        m.box(f"forearm_{side}", -0.5, 0, -0.5, 1, 4, 1, skin(21))
        m.box(f"forearm_{side}", -1, 4, -1, 2, 1, 2, skin(22, n=0))
        m.box(f"forearm_{side}", -1, 5, -1, 2, 1, 1, HORN)
    m.box("orb", -2.5, -2.5, -2.5, 5, 5, 5, lambda f_, x, y, w, h: EMBER_HOT if 1 <= x <= 3 and 1 <= y <= 3 else EMBER,
          glow=lambda f_, x, y, w, h: (255, 250, 200) if x == 2 and y == 2 else EMBER_HOT if 1 <= x <= 3 and 1 <= y <= 3
          else EMBER)

    # goat legs with hooves
    for side in ("r", "l"):
        m.box(f"leg_{side}", -1, 0, -1, 2, 3, 2, skin(30))
        m.box(f"shin_{side}", -0.5, 0, -0.5, 1, 3, 1, skin(31, n=0))
        m.box(f"shin_{side}", -1, 3, -1.5, 2, 1, 2, HORN)

    # wings: spread membranes behind the shoulders
    m.box("wing_r", -10, -3, 0, 10, 8, 0, membrane(40, -1), glow=membrane_glow(-1))
    m.box("wing_l", 0, -3, 0, 10, 8, 0, membrane(41, 1), glow=membrane_glow(1))

    # whip tail with an ember spade
    m.box("tail", -0.5, -0.5, 0, 1, 1, 5, skin(50, n=0))
    m.box("tail2", -0.5, -0.5, 0, 1, 1, 4, skin(51, n=0))
    m.box("tail3", -0.5, -0.5, 0, 1, 1, 3, skin(52, n=0))
    m.box("tail3", -1.5, -1, 3, 3, 2, 1, {"*": (200, 70, 30)}, glow=lambda f_, x, y, w, h: EMBER_HOT if (x + y) % 2 else EMBER)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 1.2)
    idle.pos("bone", (0, (0, 0, 0)), (0.6, (0, 1.5, 0)), (1.2, (0, 0, 0)))
    flap = [(0, 0), (0.15, -40), (0.3, 0), (0.45, -40), (0.6, 0), (0.75, -40), (0.9, 0), (1.05, -40), (1.2, 0)]
    idle.rot("wing_r", *[(t, (0, -a, a * 0.3)) for t, a in flap])
    idle.rot("wing_l", *[(t, (0, a, -a * 0.3)) for t, a in flap])
    idle.rot("tail", (0, (0, 0, 0)), (0.6, (8, 20, 0)), (1.2, (0, 0, 0)))
    idle.rot("tail2", (0, (0, -10, 0)), (0.6, (0, 15, 0)), (1.2, (0, -10, 0)))
    idle.rot("tail3", (0, (0, 15, 0)), (0.6, (0, -20, 0)), (1.2, (0, 15, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (-4, 0, 5)), (1.2, (0, 0, 0)))
    idle.rot("leg_r", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (1.2, (0, 0, 0)))
    idle.rot("leg_l", (0, (10, 0, 0)), (0.6, (0, 0, 0)), (1.2, (10, 0, 0)))

    walk = m.anim("walk", 0.6)   # hopping flutter: every stride is a little hop
    walk.pos("bone", (0, (0, 0, 0)), (0.15, (0, 3, 0)), (0.3, (0, 0, 0)), (0.45, (0, 3, 0)), (0.6, (0, 0, 0)))
    walk.rot("body", (0, (10, 0, 0)), (0.15, (16, 0, 0)), (0.3, (10, 0, 0)), (0.45, (16, 0, 0)), (0.6, (10, 0, 0)))
    walk.rot("leg_r", (0, (30, 0, 0)), (0.15, (-30, 0, 0)), (0.3, (30, 0, 0)), (0.45, (-30, 0, 0)), (0.6, (30, 0, 0)))
    walk.rot("leg_l", (0, (30, 0, 0)), (0.15, (-30, 0, 0)), (0.3, (30, 0, 0)), (0.45, (-30, 0, 0)), (0.6, (30, 0, 0)))
    walk.rot("wing_r", (0, (0, 30, 0)), (0.15, (0, -20, 20)), (0.3, (0, 30, 0)), (0.45, (0, -20, 20)), (0.6, (0, 30, 0)))
    walk.rot("wing_l", (0, (0, -30, 0)), (0.15, (0, 20, -20)), (0.3, (0, -30, 0)), (0.45, (0, 20, -20)), (0.6, (0, -30, 0)))
    walk.rot("arm_r", (0, (20, 0, 0)), (0.3, (-20, 0, 0)), (0.6, (20, 0, 0)))
    walk.rot("arm_l", (0, (-20, 0, 0)), (0.3, (20, 0, 0)), (0.6, (-20, 0, 0)))

    # throw: wind back while the orb swells (telegraph), hurl at 0.5 s (10 ticks)
    a = m.anim("throw", 1.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.42, (-165, 0, -35)), (0.5, (-60, 0, -15), "linear"), (0.7, (-50, 0, -10)),
          (1.2, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.42, (-10, 0, 0)), (0.5, (10, 0, 0), "linear"), (1.2, (0, 0, 0)))
    # the orb's rest scale is 0.02: a keyframe of 1.98 adds 0.98, i.e. full size
    a.scale("orb", (0, (1, 1, 1)), (0.12, (1.5, 1.5, 1.5)), (0.42, (1.98, 1.98, 1.98)), (0.5, (1, 1, 1), "linear"),
            (1.2, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.42, (-10, 30, 0)), (0.5, (14, -25, 0), "linear"), (0.7, (10, -20, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.42, (-6, -20, 0)), (0.5, (6, 15, 0)), (1.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.42, (10, 0, 0)), (0.5, (30, 0, 0)), (0.8, (25, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.42, (-50, 0, -30)), (0.5, (20, 0, -20)), (1.2, (0, 0, 0)))

    # hop: a big evasive leap backward, wings beating hard
    a = m.anim("hop", 0.9)
    a.pos("bone", (0, (0, 0, 0)), (0.2, (0, -2, 0)), (0.45, (0, 8, 4)), (0.7, (0, 3, 2)), (0.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (20, 0, 0)), (0.45, (-25, 0, 0)), (0.7, (-10, 0, 0)), (0.9, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.2, (0, 40 * sx, 0)), (0.3, (0, -40 * sx, -30 * sx)),
              (0.45, (0, 40 * sx, 0)), (0.6, (0, -40 * sx, -30 * sx)), (0.75, (0, 30 * sx, 0)), (0.9, (0, 0, 0)))
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.2, (-40, 0, 0)), (0.45, (40, 0, 0)), (0.9, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.45, (-60, 0, -50 * sx)), (0.9, (0, 0, 0)))

    # cackle: head thrown back, jaw chattering, belly shaking, tail lashing
    a = m.anim("cackle", 1.4)
    a.rot("head", (0, (0, 0, 0)), (0.25, (-30, 0, 0)), (1.1, (-28, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), *[(0.25 + i * 0.1, ((30 if i % 2 == 0 else 8), 0, 0)) for i in range(9)], (1.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), *[(0.25 + i * 0.1, (-8, 0, 4 if i % 2 else -4)) for i in range(9)], (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-50, 0, -40)), (1.1, (-50, 0, -40)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-50, 0, 40)), (1.1, (-50, 0, 40)), (1.4, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.4, (10, 40, 0)), (0.7, (10, -40, 0)), (1.0, (10, 40, 0)), (1.4, (0, 0, 0)))
    return m
