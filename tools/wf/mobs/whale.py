"""Humpback Whale (Baleine à bosse): huge, rare and peaceful, in the deep oceans. It cruises slowly, surfaces to
blow, and sings. Built at half scale (root scale 2): a long, slightly humped body with knobby tubercles on the
head, a grooved white throat, barnacle clusters, very long white-edged pectoral fins (two segments each), a small
dorsal hump and wide notched flukes that beat up and down through a three-joint tail.

Actions: sing (fins spread, head tilts, a slow roll), spout (the blowhole puffs, the back arches at the surface).
"""
from ..models import Model
from ..texgen import mix, mul

BACK = (46, 58, 76)
BACK_L = (70, 86, 108)
SIDE = (88, 100, 118)
BELLY = (226, 230, 232)
GROOVE = (150, 156, 166)
BARNACLE = (214, 208, 190)
BARNACLE_D = (150, 140, 124)
EYE = (16, 16, 20)


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


def hide(seed, belly_from=0.62, grooves=False, barnacles=0.0):
    """Dark mottled back, lighter flanks, white (grooved) belly; scattered barnacles."""
    def f(face, x, y, w, h):
        if face == "top":
            c = mix(BACK, BACK_L, 0.4 * _n(x // 2, y // 2, seed))
            if barnacles and _n(x, y, seed + 9) < barnacles:
                return BARNACLE if _n(x, y, seed + 3) < 0.6 else BARNACLE_D
            return c
        if face == "bottom":
            if grooves and x % 3 == 0:
                return GROOVE
            return mix(BELLY, GROOVE, 0.15 * _n(x, y, seed))
        v = y / max(1, h - 1)
        if v > belly_from:
            if grooves and (x + (y % 2)) % 3 == 0:
                return GROOVE
            return BELLY
        c = mix(BACK, SIDE, min(1.0, v * 1.4))
        if barnacles and _n(x, y, seed + 11) < barnacles * 0.6:
            return BARNACLE_D
        return mix(c, BACK_L, 0.25 * _n(x // 2, y // 2, seed + 1))
    return f


def fin(seed, tip=False):
    """Pectoral fin: dark mottled top with a white knobby leading edge, white underside."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BELLY
        if face == "top":
            if y >= h - 2 or (y == h - 3 and x % 2 == 0):
                return BELLY            # the white scalloped leading edge
            return mix(BACK, BELLY, 0.15 + 0.35 * _n(x, y, seed)) if _n(x // 2, y, seed) > 0.25 else BACK_L
        return mix(SIDE, BELLY, 0.5)
    return f


def build():
    m = Model("whale", seed=191, shadow=3.0, head=None, walk_speed=0.5, walk_scale=0.6)
    m.preview_idle = True

    m.part("bone", pivot=(0, 24, 0), scale=(2, 2, 2))
    m.part("body", "bone", pivot=(0, -8, 0))
    m.part("tail1", "body", pivot=(0, -1, 12))
    m.part("tail2", "tail1", pivot=(0, 0, 11))
    m.part("flukes", "tail2", pivot=(0, 0, 9))

    # ---- torso and head
    m.box("body", -8, -7, -16, 16, 14, 28, hide(1, barnacles=0.0))
    m.box("body", -7, -8, -12, 14, 1, 18, hide(2))                                 # the hump of the back
    m.box("body", -7, -6, -29, 14, 12, 13, hide(3, belly_from=0.58, grooves=True, barnacles=0.03))
    m.box("body", -5, -5, -35, 10, 9, 6, hide(4, belly_from=0.55, grooves=True, barnacles=0.08))
    m.box("body", -6.5, 3, -34, 13, 4, 18, hide(5, belly_from=0.0, grooves=True))   # grooved throat
    # knobby tubercles along the rostrum, blowhole, eyes
    for i, (x, z) in enumerate(((-2, -33), (2, -32), (0, -30), (-3, -28), (3, -27), (-1, -25))):
        m.box("body", x - 0.5, -6 if z < -29 else -7, z, 1, 1, 1, BARNACLE if i % 2 else BACK_L)
    m.box("body", -1.5, -7.2, -20, 3, 1, 2, {"top": lambda f, x, y, w, h: EYE if x == 1 else BACK, "*": BACK})
    for sx in (-1, 1):
        m.box("body", (6.6 if sx > 0 else -7.6), 1, -24, 1, 1, 1, EYE)
        m.box("body", (6.4 if sx > 0 else -7.4), 3, -31, 1, 2, 3, BARNACLE)          # barnacles on the jaw

    # ---- pectoral fins: long, two segments, swept back
    for side, sx in (("r", -1), ("l", 1)):
        root, tip = f"fin_{side}", f"fin_{side}_tip"
        m.part(root, "body", pivot=(7 * sx, 4, -12), rot=(0, 30 * sx, 25 * sx))
        m.part(tip, root, pivot=(12 * sx, 0, 0), rot=(0, 10 * sx, 0))
        m.box(root, 0 if sx > 0 else -12, -1, -3, 12, 2, 6, fin(10 + sx))
        m.box(tip, 0 if sx > 0 else -11, -0.5, -2, 11, 1, 4, fin(12 + sx, tip=True))

    # ---- tail stock with a small dorsal hump, flukes
    m.box("tail1", -6, -5, 0, 12, 10, 11, hide(20, belly_from=0.7))
    m.box("tail1", -1, -8, 2, 2, 3, 5, {"*": BACK, "top": BACK_L})                    # dorsal hump
    m.box("tail2", -4, -3, 0, 8, 6, 9, hide(21, belly_from=0.75))

    def fluke(face, x, y, w, h):
        # wide flukes: notched at the middle of the trailing edge, scalloped, white with dark marks below
        back = y if face == "top" else h - 1 - y
        if face in ("top", "bottom"):
            cx = abs(x - (w - 1) / 2)
            if back == 0 and (cx < 1 or x % 3 == 0):
                return None
            if back <= 1 and cx > w / 2 - 2:
                return None
            if face == "bottom":
                return BELLY if _n(x, y, 7) > 0.2 else GROOVE
            return mix(BACK, BACK_L, 0.3 * _n(x, y, 8))
        return BACK
    m.box("flukes", -13, -1, 0, 26, 2, 8, fluke)
    m.box("flukes", -2, -1.5, -1, 4, 3, 3, hide(22))

    # ------------------------------------------------------------------ animations
    L = 4.0
    idle = m.anim("idle", L)
    idle.rot("tail1", (0, (5, 0, 0)), (L / 2, (-5, 0, 0)), (L, (5, 0, 0)))
    idle.rot("tail2", (0, (2, 0, 0)), (L * 0.3, (9, 0, 0)), (L * 0.8, (-9, 0, 0)), (L, (2, 0, 0)))
    idle.rot("flukes", (0, (-4, 0, 0)), (L * 0.4, (14, 0, 0)), (L * 0.9, (-14, 0, 0)), (L, (-4, 0, 0)))
    idle.rot("body", (0, (-1.5, 0, 0)), (L / 2, (1.5, 0, 0)), (L, (-1.5, 0, 0)))
    idle.pos("body", (0, (0, 0.4, 0)), (L / 2, (0, -0.4, 0)), (L, (0, 0.4, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        idle.rot(f"fin_{side}", (0, (6, 0, 0)), (L / 2, (-6, 0, -6 * sx)), (L, (6, 0, 0)))
        idle.rot(f"fin_{side}_tip", (0, (0, 0, 0)), (L * 0.6, (0, 0, -8 * sx)), (L, (0, 0, 0)))

    walk = m.anim("walk", 3.0)
    walk.rot("tail1", (0, (4, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (4, 0, 0)))
    walk.rot("flukes", (0, (-6, 0, 0)), (1.5, (6, 0, 0)), (3.0, (-6, 0, 0)))

    # sing: the fins open wide, the head lifts a little and the whale rolls slowly onto its side and back
    a = m.anim("sing", 4.0)
    a.rot("body", (0, (0, 0, 0)), (1.2, (-6, 0, 18)), (2.8, (-6, 0, 18)), (4.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"fin_{side}", (0, (0, 0, 0)), (1.2, (0, -25 * sx, -30 * sx)), (2.8, (0, -25 * sx, -35 * sx)),
              (4.0, (0, 0, 0)))
    a.rot("flukes", (0, (0, 0, 0)), (1.5, (12, 0, 0)), (2.5, (-8, 0, 0)), (4.0, (0, 0, 0)))
    # spout: the back arches at the surface while the blowhole puffs
    a = m.anim("spout", 2.0)
    a.rot("body", (0, (0, 0, 0)), (0.6, (-5, 0, 0)), (1.4, (3, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("tail1", (0, (0, 0, 0)), (0.6, (8, 0, 0)), (1.4, (-6, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (2.0, (0, 0, 0)))
    return m
