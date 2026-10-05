"""Lantern Wisp (Feu follet): the light thief of the catacombs and the tombs.

Silhouette idea: a lantern that walks on air. A rusty iron lantern cage with a pale soul-flame for a body and a
mischievous face inside it, two wisps of flame for arms, and a flickering tail that trails below. It drinks the flames
of the candles around it: three texture variants (dim, lit, blazing) show how much light it has stolen.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

VARIANTS = ["dim", "lit", "blazing"]
IRON = (70, 64, 62)
IRON_D = (40, 36, 36)
RUST = (130, 72, 40)
# flame colours per variant: (core, light, edge)
FLAME = {
    "dim": ((70, 120, 150), (150, 200, 220), (40, 70, 100)),
    "lit": ((90, 210, 230), (210, 250, 255), (50, 130, 170)),
    "blazing": ((150, 240, 255), (250, 255, 255), (90, 190, 230)),
}


def cage(seed=0):
    """Iron bars: a frame and vertical bars, the gaps transparent (the flame shows through)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            if 1 <= x <= w - 2 and 1 <= y <= h - 2 and face == "bottom":
                return None
            return IRON if (x + y) % 3 else RUST
        if x in (0, w - 1) or y in (0, h - 1):
            return IRON if K.h(x, y, seed) % 5 else RUST
        if face == "front":
            return None                                                         # the open window: the face shows
        if x % 2 == 0:
            return IRON_D
        return None
    return f


def build(variant=None):
    v = variant or VARIANTS[0]
    core, light, edge = FLAME[v]
    m = Model("lantern_wisp", seed=387, shadow=0.3, variants=VARIANTS, render="entityCutout", walk_speed=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -12, 0))
    m.part("head", "body", pivot=(0, -4, 0))
    m.part("arm_r", "body", pivot=(-4, -5, 0), rot=(0, 0, 30))
    m.part("arm_l", "body", pivot=(4, -5, 0), rot=(0, 0, -30))
    m.part("tail", "body", pivot=(0, 0, 0))
    m.part("tail2", "tail", pivot=(0, 3, 0.5))
    m.part("tail3", "tail2", pivot=(0, 3, 0.5))

    def flame(f_, x, y, w, h):
        c = core if (x + y) % 3 else edge
        if y < 2:
            c = light
        return c

    def face(f_, x, y, w, h):
        if f_ == "front":
            if y == 2 and x in (1, 4):
                return (20, 30, 40)                                              # hollow eyes
            if y == 4 and 1 <= x <= 4:
                return (20, 30, 40) if x in (1, 4) or y == 4 else light          # a wide grin
        return flame(f_, x, y, w, h)

    def face_glow(f_, x, y, w, h):
        if f_ == "front" and ((y == 2 and x in (1, 4)) or (y == 4 and 1 <= x <= 4)):
            return None
        return light if y < 2 else core

    # the flame body inside the cage, with the face (it is the "head": it looks at its prey)
    m.box("head", -3, -6, -3, 6, 6, 6, face, glow=face_glow)
    # the iron lantern around it, a cap, a ring on top
    m.box("body", -3.5, -10.5, -3.5, 7, 9, 7, cage(1))
    m.box("body", -4, -11.5, -4, 8, 1, 8, {"*": IRON, "top": lambda f_, x, y, w, h: RUST if (x * y) % 5 == 0 else IRON})
    m.box("body", -2, -13.5, -2, 4, 2, 4, {"*": IRON_D, "top": IRON})
    m.box("body", -1, -16, -0.5, 2, 3, 1, {"front": lambda f_, x, y, w, h: None if (x, y) == (0, 1) or (x, y) == (1, 1) else IRON,
                                           "back": lambda f_, x, y, w, h: None if y == 1 else IRON, "*": IRON_D})
    m.box("body", -4, -1.5, -4, 8, 1, 8, {"*": IRON, "bottom": IRON_D})

    # flame arms
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        m.box(arm, -1 if sx < 0 else -1, 0, -1, 2, 5, 2, flame, glow=lambda f_, x, y, w, h: core if y > 0 else light)
        m.box(arm, -0.5, 5, -0.5, 1, 2, 1, edge, glow={"*": edge})

    # the trailing tail of flame below the cage
    m.box("tail", -2, 0, -2, 4, 3, 4, flame, glow=lambda f_, x, y, w, h: core)
    m.box("tail2", -1.5, 0, -1.5, 3, 3, 3, flame, glow=lambda f_, x, y, w, h: core)
    m.box("tail3", -1, 0, -1, 2, 3, 2, {"*": edge, "bottom": None}, glow=lambda f_, x, y, w, h: edge)

    # ------------------------------------------------------------------ animations (always floating)
    idle = m.anim("idle", 2.0)
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, 1.5, 0)), (2.0, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, -3)), (1.0, (0, 0, 3)), (2.0, (0, 0, -3)))
    idle.rot("tail", (0, (8, 0, 0)), (0.5, (0, 0, 8)), (1.0, (-6, 0, 0)), (1.5, (0, 0, -8)), (2.0, (8, 0, 0)))
    idle.rot("tail2", (0, (10, 0, 6)), (0.5, (-6, 0, 10)), (1.0, (10, 0, -6)), (1.5, (-6, 0, -10)), (2.0, (10, 0, 6)))
    idle.rot("tail3", (0, (14, 0, -8)), (0.5, (-10, 0, 12)), (1.0, (14, 0, 8)), (1.5, (-10, 0, -12)), (2.0, (14, 0, -8)))
    idle.scale("head", (0, (1, 1, 1)), (0.25, (1.05, 1.1, 1.05)), (0.5, (1, 1, 1)), (0.8, (0.96, 1.06, 0.96)), (1.2, (1, 1, 1)),
               (1.6, (1.04, 0.95, 1.04)), (2.0, (1, 1, 1)))                     # the flame flickers
    idle.rot("arm_r", (0, (0, 0, 0)), (1.0, (-20, 0, 10)), (2.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.0, (-20, 0, -10)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("body", (0, (14, 0, 0)), (1.0, (14, 0, 0)))
    walk.rot("tail", (0, (30, 0, 0)), (0.5, (36, 0, 0)), (1.0, (30, 0, 0)))

    # snuff: leans toward a candle and inhales its flame (the flame swells at 0.6 s)
    a = m.anim("snuff", 0.9)
    a.rot("body", (0, (0, 0, 0)), (0.4, (25, 0, 0)), (0.6, (25, 0, 0)), (0.9, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.4, (0.8, 0.8, 0.8)), (0.6, (1.3, 1.3, 1.3), "linear"), (0.9, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-90, 0, 20)), (0.6, (-40, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-90, 0, -20)), (0.6, (-40, 0, 0)), (0.9, (0, 0, 0)))

    # lunge: a cold-flame dash at its prey (contact at 0.35 s = 7 ticks)
    a = m.anim("lunge", 0.7)
    a.rot("body", (0, (0, 0, 0)), (0.25, (-20, 0, 0)), (0.35, (40, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-150, 0, 0)), (0.35, (-40, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-150, 0, 0)), (0.35, (-40, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.35, (1.2, 1.2, 1.2)), (0.7, (1, 1, 1)))

    # pulse: gathers the stolen light, then lets out a wave of darkness (at 0.5 s = 10 ticks)
    a = m.anim("pulse", 1.0)
    a.scale("head", (0, (1, 1, 1)), (0.45, (0.6, 0.6, 0.6)), (0.5, (1.5, 1.5, 1.5), "linear"), (1.0, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (0, 0, -60)), (0.5, (0, 0, 70), "linear"), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (0, 0, 60)), (0.5, (0, 0, -70), "linear"), (1.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.45, (0, 2, 0)), (0.5, (0, -1, 0)), (1.0, (0, 0, 0)))
    return m
