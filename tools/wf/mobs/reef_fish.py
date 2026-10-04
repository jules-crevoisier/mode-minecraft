"""Reef Fish (Poisson de récif): a small, tall-bodied schooling fish of warm seas, in three liveries painted on the
same cubes: sunburst (yellow tang with a blue mask), clown (orange with black-edged white bands) and azure (blue
tang: royal blue, black swoosh, yellow tail).
"""
from ..models import Model
from ..texgen import mix, mul

WHITE = (250, 250, 244)
BLACK = (22, 22, 30)

LIVERIES = {
    # body, belly, fin, accent, tail
    "sunburst": ((255, 214, 40), (255, 240, 150), (255, 160, 30), (40, 110, 230), (255, 186, 40)),
    "clown": ((255, 112, 24), (255, 160, 90), (255, 128, 40), WHITE, (255, 120, 30)),
    "azure": ((40, 96, 230), (90, 150, 250), (30, 70, 190), BLACK, (255, 214, 40)),
}
ORDER = ["sunburst", "clown", "azure"]


def body_paint(liv, name, z0, y0):
    """Livery painted in absolute model coordinates (z from the snout at -6 to the tail at 5, y from the back at -3
    to the belly at 3), so the bands line up across the separate body boxes."""
    body, belly, fin, acc, tail = liv

    def f(face, x, y, w, h):
        if face == "top":
            return mul(body, 0.9) if name != "clown" or (z0 + h - 1 - y) not in (-4, 1) else WHITE
        if face == "bottom":
            return belly
        if face in ("left", "right"):
            z = z0 + (w - 1 - x if face == "right" else x)
        else:
            z = z0 if face == "front" else z0 + 99
        yy = y0 + y
        v = (yy + 3) / 6.0
        c = mix(body, belly, max(0.0, v - 0.55) * 1.6)
        if name == "sunburst":
            if z in (-5, -4) or face == "front":                  # blue mask over the eyes
                c = mix(acc, (255, 255, 255), 0.12) if yy < 1 else mix(acc, belly, 0.3)
            elif z == -3:
                c = mix(c, (255, 255, 255), 0.35)
        elif name == "clown":
            c = {-4: WHITE, -3: BLACK, 0: BLACK, 1: WHITE, 2: BLACK, 4: WHITE}.get(z, c)
        elif name == "azure":
            if -3 <= z <= 3 and abs(yy - (-1.5 + 0.6 * (z + 3))) < 1.0:
                c = BLACK                                         # the black swoosh along the flank
            if z >= 3 and -1 <= yy <= 1:
                c = mix(c, tail, 0.7)
        return c
    return f


def fin_paint(colour, edge, edge_at, seed=0, notch=False):
    """Flat fin: ``edge_at`` = which border carries the dark/light rim (top, bottom or back)."""
    def f(face, x, y, w, h):
        if notch and abs(y - (h - 1) / 2) < 1 and x > w - 3:
            return None   # forked tail
        c = colour if (x + y + seed) % 3 else mul(colour, 0.88)
        back = x == (0 if face == "right" else w - 1)
        if (edge_at == "top" and y == 0) or (edge_at == "bottom" and y == h - 1) or (edge_at == "back" and back):
            c = edge
        return (*c, 255)
    return f


def build(variant=None):
    variant = variant or ORDER[0]
    liv = LIVERIES[variant]
    body, belly, fin, acc, tail = liv
    edge = BLACK if variant == "clown" else mix(fin, (255, 255, 255), 0.2) if variant != "azure" else mul(fin, 0.6)
    m = Model("reef_fish", seed=113, shadow=0.15, head="body", variants=ORDER, walk_speed=1.6, walk_scale=1.0)
    m.preview_idle = True

    m.part("body", pivot=(0, 20, 0))
    m.part("tail", "body", pivot=(0, 0, 5))
    m.part("fin_r", "body", pivot=(-1, 1, -1), rot=(0, -30, 20))
    m.part("fin_l", "body", pivot=(1, 1, -1), rot=(0, 30, -20))

    # ---- tall, flat body: a deep core, a tapered head and a narrow tail stalk
    m.box("body", -1, -3, -3, 2, 6, 6, body_paint(liv, variant, -3, -3))
    m.box("body", -1, -2, -5, 2, 4, 2, body_paint(liv, variant, -5, -2))
    m.box("body", -1, -2, 3, 2, 4, 1, body_paint(liv, variant, 3, -2))
    m.box("body", -0.5, -1, 4, 1, 2, 1, body_paint(liv, variant, 4, -1))
    m.box("body", -0.5, -0.5, -6, 1, 1, 1, mul(acc if variant == "sunburst" else body, 0.8))
    # eyes
    for sx in (-1, 1):
        m.box("body", -1.2 if sx < 0 else 0.2, -1.5, -4.5, 1, 1, 1,
              {"left": BLACK, "right": BLACK, "*": WHITE}, grow=0.05)
    # dorsal and anal fins (flat), the blue tang's yellow spine before the tail
    fcol = body if variant == "azure" else fin
    m.box("body", 0, -6, -3, 0, 3, 6, fin_paint(fcol, edge, "top", 1))
    m.box("body", 0, 3, -1, 0, 2, 4, fin_paint(fcol, edge, "bottom", 2))
    m.box("body", -0.5, -2.6, 3, 1, 1, 1, tail if variant == "azure" else mul(body, 0.95))
    # ---- forked tail
    m.box("tail", 0, -2.5, 0, 0, 5, 3, fin_paint(tail, edge if variant != "sunburst" else mix(tail, WHITE, 0.4),
                                                  "back", 3, notch=True))
    # ---- pectoral fins
    m.box("fin_r", -2, 0, 0, 2, 0, 2, fin_paint(mix(fin, WHITE, 0.3), edge, "none", 4))
    m.box("fin_l", 0, 0, 0, 2, 0, 2, fin_paint(mix(fin, WHITE, 0.3), edge, "none", 5))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 0.8)
    idle.rot("tail", (0, (0, -22, 0)), (0.4, (0, 22, 0)), (0.8, (0, -22, 0)))
    idle.rot("body", (0, (0, 3, 0)), (0.4, (0, -3, 0)), (0.8, (0, 3, 0)))
    idle.rot("fin_r", (0, (0, 0, 0)), (0.2, (0, 0, 25)), (0.4, (0, 0, 0)), (0.6, (0, 0, 25)), (0.8, (0, 0, 0)))
    idle.rot("fin_l", (0, (0, 0, 0)), (0.2, (0, 0, -25)), (0.4, (0, 0, 0)), (0.6, (0, 0, -25)), (0.8, (0, 0, 0)))
    walk = m.anim("walk", 0.5)
    walk.rot("tail", (0, (0, -18, 0)), (0.25, (0, 18, 0)), (0.5, (0, -18, 0)))
    walk.rot("body", (0, (0, 4, 0)), (0.25, (0, -4, 0)), (0.5, (0, 4, 0)))
    return m
