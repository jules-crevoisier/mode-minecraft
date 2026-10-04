"""Manta Ray (Raie manta): a gentle giant of warm and temperate seas. A flat diamond body with swept-back wings that
beat in a slow travelling wave (inner and outer wing segments), curled cephalic fins at the mouth, a whip tail;
charcoal back with the white "shoulder" chevrons of a reef manta, a white belly freckled with dark spots.

Actions: breach (it leaps out of the water near the surface and belly-flops back).
"""
from ..models import Model
from ..texgen import mix, mul

BACK = (44, 52, 70)
BACK_L = (66, 78, 102)
EDGE = (30, 34, 46)
CHEVRON = (214, 220, 226)
BELLY = (232, 234, 238)
SPOT = (64, 70, 84)
MOUTH = (20, 20, 26)


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


def skin(seed, chevron=None, edge_rows=0):
    """Back on top, belly below; sides dark. ``chevron``: function (x, y, w, h) -> bool on the top face for the
    white shoulder patch."""
    def f(face, x, y, w, h):
        if face == "top":
            if y == 0 and h > 4:
                return EDGE  # darker trailing edge
            if chevron and chevron(x, y, w, h):
                return mix(CHEVRON, BACK_L, 0.15 * _n(x, y, seed))
            c = mix(BACK, BACK_L, 0.35 * _n(x // 2, y // 2, seed))
            return c
        if face == "bottom":
            c = BELLY
            if _n(x, y, seed + 5) < 0.05:
                c = SPOT
            return c
        return mix(EDGE, BACK, 0.4) if y < h / 2 else mix(BELLY, EDGE, 0.5)
    return f


def build():
    m = Model("manta_ray", seed=151, shadow=1.2, head="body", walk_speed=0.8, walk_scale=0.6)
    m.preview_idle = True

    m.part("body", pivot=(0, 21, 0))
    m.part("tail", "body", pivot=(0, 0, 10))
    m.part("horn_r", "body", pivot=(-5, 0, -10))
    m.part("horn_l", "body", pivot=(5, 0, -10))

    # ---- the body: a flat diamond with a raised back
    m.box("body", -7, -2, -8, 14, 4, 18, skin(1, chevron=lambda x, y, w, h: 3 <= y <= 8 and (x <= 2 or x >= w - 3)))
    m.box("body", -6, -1.5, -10, 12, 3, 2, {"front": lambda f, x, y, w, h: MOUTH if 0 < y < h - 1 and 1 < x < w - 2
                                             else BELLY, "*": skin(2)})
    m.box("body", -3, -3, -6, 6, 1, 12, skin(3))
    m.box("body", -4, -2, 10, 8, 3, 2, skin(4))
    # gill slits under the body
    m.box("body", -5, 2.01, -6, 10, 0, 5, lambda f, x, y, w, h: SPOT if f == "bottom" and x in (0, 1, w - 2, w - 1)
          and y % 2 == 0 else None)

    # ---- cephalic fins, curled forward on either side of the mouth
    for side, sx in (("r", -1), ("l", 1)):
        h = f"horn_{side}"
        m.box(h, -1 if sx < 0 else -1, -1, -4, 2, 2, 4, skin(5 + (sx > 0)))
        m.box(h, -1 if sx < 0 else -1, 0, -5, 2, 1, 1, BELLY)

    # ---- wings: inner and outer segments, swept back, thinner toward the tip
    for side, sx in (("r", -1), ("l", 1)):
        inner, outer = f"wing_{side}", f"wing_{side}_tip"
        m.part(inner, "body", pivot=(7 * sx, 0, -1))
        m.part(outer, inner, pivot=(12 * sx, 0, 1))

        def span(x0, w):
            return x0 if sx > 0 else -x0 - w
        # the white shoulder chevron sweeps from the body onto the leading half of the wing
        near = (lambda x, w: x) if sx < 0 else (lambda x, w: w - 1 - x)
        m.box(inner, span(0, 6), -1.5, -6, 6, 3, 15,
              skin(11 + sx, chevron=lambda x, y, w, h: 4 <= (h - 1 - y) - near(x, w) // 2 <= 7 and (h - 1 - y) >= 3))
        m.box(inner, span(6, 6), -1, -4, 6, 2, 11, skin(13 + sx, chevron=lambda x, y, w, h: False))
        m.box(outer, span(0, 6), -1, -3, 6, 2, 8, skin(15 + sx))
        m.box(outer, span(6, 4), -0.5, -1, 4, 1, 5, skin(17 + sx))
        m.box(outer, span(10, 2), -0.5, 0, 2, 1, 3, {"top": EDGE, "*": skin(19 + sx)})

    # ---- pelvic fins and the whip tail
    for sx in (-1, 1):
        m.box("body", (4 if sx > 0 else -6), -0.5, 9, 2, 1, 3, skin(21 + sx))
    m.box("tail", -0.5, -0.5, 0, 1, 1, 9, {"top": EDGE, "bottom": mix(BELLY, EDGE, 0.4), "*": EDGE})
    m.part("tail2", "tail", pivot=(0, 0, 9))
    m.box("tail2", -0.5, -0.5, 0, 1, 1, 9, {"top": EDGE, "*": mix(EDGE, BACK, 0.5)})

    # ------------------------------------------------------------------ animations
    L = 3.2
    idle = m.anim("idle", L)
    # a slow wave from the shoulder to the wing tip
    for side, sx in (("r", 1), ("l", -1)):
        idle.rot(f"wing_{'r' if sx > 0 else 'l'}", (0, (0, 0, 16 * sx)), (L / 2, (0, 0, -18 * sx)), (L, (0, 0, 16 * sx)))
        idle.rot(f"wing_{'r' if sx > 0 else 'l'}_tip", (0, (0, 0, 4 * sx)), (L * 0.2, (0, 0, 22 * sx)),
                 (L * 0.7, (0, 0, -24 * sx)), (L, (0, 0, 4 * sx)))
    idle.pos("body", (0, (0, -0.6, 0)), (L / 2, (0, 0.8, 0)), (L, (0, -0.6, 0)))
    idle.rot("body", (0, (2, 0, 0)), (L / 2, (-2, 0, 0)), (L, (2, 0, 0)))
    idle.rot("tail", (0, (4, 8, 0)), (L / 2, (-4, -8, 0)), (L, (4, 8, 0)))
    idle.rot("tail2", (0, (-6, -10, 0)), (L / 2, (6, 12, 0)), (L, (-6, -10, 0)))
    idle.rot("horn_r", (0, (0, -10, 0)), (L / 2, (0, 4, 0)), (L, (0, -10, 0)))
    idle.rot("horn_l", (0, (0, 10, 0)), (L / 2, (0, -4, 0)), (L, (0, 10, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("body", (0, (3, 0, 0)), (0.8, (5, 0, 0)), (1.6, (3, 0, 0)))
    walk.rot("tail", (0, (-6, 0, 0)), (0.8, (-3, 0, 0)), (1.6, (-6, 0, 0)))

    # breach: nose up as it bursts out, wings flung high, then a belly-flop
    a = m.anim("breach", 1.6)
    a.rot("body", (0, (0, 0, 0)), (0.35, (-45, 0, 0)), (0.8, (-10, 0, 8)), (1.2, (30, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in (("r", 1), ("l", -1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.35, (0, 0, 30 * sx)), (0.8, (0, 0, 45 * sx)), (1.2, (0, 0, -30 * sx)),
              (1.6, (0, 0, 0)))
        a.rot(f"wing_{side}_tip", (0, (0, 0, 0)), (0.5, (0, 0, 30 * sx)), (1.0, (0, 0, -20 * sx)), (1.6, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.4, (25, 0, 0)), (1.2, (-20, 0, 0)), (1.6, (0, 0, 0)))
    return m
