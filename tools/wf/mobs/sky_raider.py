"""Sky Raider (Pillard du ciel): the wind pirates of the Sky Isles.

Silhouette idea: a crow with a pilot's licence. A small, lean raider in a leather flight cap, a scarf whipping
behind, amber goggles that glow, and a pair of huge clockwork ornithopter wings (brass spars, patched canvas) that
beat all the time. Its boots end in steel grappling talons: it snatches its prey from above, lifts it and lets go.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B
from . import folkkit as K

LEATHER = (104, 70, 44)
LEATHER_D = (74, 48, 30)
CANVAS = (214, 196, 160)
CANVAS_D = (170, 150, 116)
SCARF = (60, 110, 160)
SKIN = (196, 156, 120)
STEEL = (170, 174, 182)


def membrane(seed=0):
    """Patched sail canvas between the spars: panels, a few patches and a rope seam."""
    def f(face, x, y, w, h):
        if face not in ("top", "bottom"):
            return mul(CANVAS_D, 0.8)
        if (x - 2) % 4 == 0:
            return B.BRASS_D if face == "top" else mul(B.BRASS_D, 0.8)            # the ribs
        if y == h - 1 and x % 2 == 0:
            return None                                                         # frayed trailing edge
        c = CANVAS if (y // 3) % 2 else mix(CANVAS, CANVAS_D, 0.45)
        if K.h(x // 3, y // 3, seed) % 7 == 0:
            c = mix(c, (170, 70, 50), 0.5)                                      # a red patch
        return c if face == "top" else mul(c, 0.86)
    return f


def build():
    m = Model("sky_raider", seed=363, shadow=0.4, walk_speed=1.4, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -12, 0), rot=(12, 0, 0))
    m.part("head", "body", pivot=(0, -9, -0.5))
    m.part("scarf", "head", pivot=(0, -1, 3), rot=(30, 0, 0))
    m.part("leg_r", "body", pivot=(-1.5, 0, 0))
    m.part("leg_l", "body", pivot=(1.5, 0, 0))
    m.part("arm_r", "body", pivot=(-4, -8, 0), rot=(0, 0, 10))
    m.part("arm_l", "body", pivot=(4, -8, 0), rot=(0, 0, -10))
    m.part("wing_r", "body", pivot=(-2, -8, 2.5), rot=(0, 20, 10))
    m.part("wing_l", "body", pivot=(2, -8, 2.5), rot=(0, -20, -10))
    m.part("tip_r", "wing_r", pivot=(-11, 0, 0))
    m.part("tip_l", "wing_l", pivot=(11, 0, 0))

    # ------------------------------------------------------------------ torso: flight jacket, harness, a boiler pack
    def jacket(f_, x, y, w, h):
        if f_ == "front" and x == w // 2:
            return B.BRASS                                                       # the zip
        if f_ == "front" and y == 3:
            return (50, 40, 30)                                                  # harness strap
        return K.leather(LEATHER, seed=1)(f_, x, y, w, h)
    m.box("body", -3, -9, -2, 6, 9, 4, jacket)
    m.box("body", -3.5, -9.5, -2.5, 7, 2, 5, K.leather((180, 160, 130), seed=2))   # fleece collar
    m.box("body", -2.5, -8, 2, 5, 6, 2, B.bands(B.COPPER, B.COPPER_D, every=2, seed=3))   # the wing motor
    m.box("body", -0.5, -10, 3, 1, 3, 1, B.soot(B.IRON_L, 4))

    # ------------------------------------------------------------------ head: flight cap with ear flaps, glowing goggles
    def face(f_, x, y, w, h):
        if f_ == "front":
            if y < 2:
                return K.leather(LEATHER_D, seed=5)(f_, x, y, w, h)
            if y in (2, 3) and x in (0, 1, 2, 3, 4, 5):
                if x in (1, 4) and y == 2:
                    return B.AMBER_L
                if x in (1, 2, 3, 4) and x not in (2, 3):
                    return B.AMBER
                return B.BRASS if y == 2 else B.BRASS_D                          # goggle frames and bridge
            if y == 5 and x in (2, 3):
                return (90, 50, 40)                                              # a grinning mouth
            if y == 5 and x in (1, 4):
                return (230, 220, 200)                                           # teeth
            return SKIN
        return K.leather(LEATHER_D, seed=6)(f_, x, y, w, h)

    def goggles_glow(f_, x, y, w, h):
        if f_ == "front" and y in (2, 3) and x in (1, 4):
            return B.AMBER_L if y == 2 else B.AMBER
        return None
    m.box("head", -3, -6, -3, 6, 6, 6, face, glow=goggles_glow)
    for sx in (-1, 1):
        m.box("head", 3 if sx > 0 else -4, -3, -2, 1, 4, 3, K.leather((180, 160, 130), seed=7))   # ear flaps
    m.box("scarf", -1.5, 0, 0, 3, 1, 7, {"*": lambda f_, x, y, w, h: SCARF if (x + y) % 3 else mul(SCARF, 0.8),
                                         "front": None})

    # ------------------------------------------------------------------ arms, hooked gauntlets
    for arm in ("arm_r", "arm_l"):
        m.box(arm, -1, -1, -1, 2, 8, 2, lambda f_, x, y, w, h: (60, 50, 44) if y >= h - 2 else
              K.leather(LEATHER, seed=8)(f_, x, y, w, h))
        m.box(arm, -1, 6, -2.5, 2, 1, 2, STEEL)                                  # a hooked finger guard

    # ------------------------------------------------------------------ legs ending in grappling talons
    for leg, sx in (("leg_r", -1), ("leg_l", 1)):
        m.box(leg, -1, 0, -1, 2, 7, 2, lambda f_, x, y, w, h: K.leather((70, 60, 54), seed=9)(f_, x, y, w, h))
        m.box(leg, -1.5, 7, -2.5, 3, 1, 4, B.iron(10))
        for k, dx in enumerate((-1.5, 0.5)):
            m.box(leg, dx, 8, -3, 1, 2, 1, STEEL)                                 # front talons
        m.box(leg, -0.5, 8, 1, 1, 2, 1, STEEL)                                    # back talon

    # ------------------------------------------------------------------ wings: brass spar, canvas, a hinged tip
    for side, sx in (("r", -1), ("l", 1)):
        wing, tip = f"wing_{side}", f"tip_{side}"
        x0 = 0 if sx > 0 else -11
        m.box(wing, x0, -0.5, -0.5, 11, 1, 1, B.rod(B.BRASS, 11))
        m.box(wing, x0, 0, 0.5, 11, 0, 9, membrane(12 + sx))
        m.box(tip, 0 if sx > 0 else -9, -0.5, -0.5, 9, 1, 1, B.rod(B.BRASS_L, 13))
        m.box(tip, 0 if sx > 0 else -9, 0, 0.5, 9, 0, 7, membrane(14 + sx))
        m.box(wing, (0 if sx > 0 else -2), -1, -1, 2, 2, 2, B.cog(B.BRASS, B.BRASS_D, teeth=6, hub=0.0,
                                                                  faces=("top", "bottom"), edges=True))

    # ------------------------------------------------------------------ animations (it always flies: idle beats)
    idle = m.anim("idle", 0.8)
    for side, sx in (("r", -1), ("l", 1)):
        idle.rot(f"wing_{side}", (0, (0, 0, 28 * sx)), (0.4, (0, 0, -22 * sx)), (0.8, (0, 0, 28 * sx)))
        idle.rot(f"tip_{side}", (0, (0, 0, 10 * sx)), (0.4, (0, 0, -16 * sx)), (0.8, (0, 0, 10 * sx)))
    idle.pos("body", (0, (0, 0, 0)), (0.4, (0, 1.2, 0)), (0.8, (0, 0, 0)))
    idle.rot("scarf", (0, (0, 8, 0)), (0.4, (6, -8, 0)), (0.8, (0, 8, 0)))
    idle.rot("leg_r", (0, (10, 0, 0)), (0.4, (16, 0, 0)), (0.8, (10, 0, 0)))
    idle.rot("leg_l", (0, (16, 0, 0)), (0.4, (10, 0, 0)), (0.8, (16, 0, 0)))

    walk = m.anim("walk", 0.6)
    walk.rot("body", (0, (20, 0, 0)), (0.6, (20, 0, 0)))
    walk.rot("scarf", (0, (20, 0, 0)), (0.3, (26, 0, 0)), (0.6, (20, 0, 0)))

    # screech: rears back, wings wide and still, a shriek (0.75 s = 15 ticks), then the dive starts
    a = m.anim("screech", 0.9)
    a.rot("body", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.75, (-30, 0, 0)), (0.85, (40, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-25, 0, 0)), (0.75, (-25, 0, 0)), (0.9, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.5, (0, 0, 40 * sx)), (0.75, (0, 0, 40 * sx)),
              (0.85, (0, -50 * sx, -10 * sx), "linear"), (0.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (0.75, (-40, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (0.75, (-40, 0, 0)), (0.9, (0, 0, 0)))

    # carry: talons clenched under it, heavy wing beats (played again while it holds its prey)
    a = m.anim("carry", 1.0)
    a.rot("leg_r", (0, (-10, 0, 0)), (0.5, (-14, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("leg_l", (0, (-10, 0, 0)), (0.5, (-14, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (-20, 0, 0)), (0.8, (-20, 0, 0)), (1.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.25, (0, 0, 46 * sx)), (0.5, (0, 0, -30 * sx)), (0.75, (0, 0, 46 * sx)),
              (1.0, (0, 0, 0)))

    # swipe: a talon kick in front of it (lands at 0.3 s = 6 ticks)
    a = m.anim("swipe", 0.7)
    a.rot("body", (0, (0, 0, 0)), (0.2, (-35, 0, 0)), (0.3, (10, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.2, (40, 0, 0)), (0.3, (-80, 0, 0), "linear"), (0.45, (-70, 0, 0)), (0.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.2, (40, 0, 0)), (0.3, (-70, 0, 0), "linear"), (0.45, (-60, 0, 0)), (0.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (-100, 0, 0)), (0.3, (-20, 0, 0), "linear"), (0.7, (0, 0, 0)))

    # stunned: crashed into the ground, wings crumpled, dizzy head (1.6 s on the ground)
    a = m.anim("stunned", 1.6)
    a.pos("body", (0, (0, 0, 0)), (0.15, (0, -5, 0)), (1.3, (0, -5, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.15, (50, 0, 10)), (1.3, (50, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-30, 20, 0)), (0.6, (-30, -20, 0)), (0.9, (-30, 20, 0)), (1.2, (-30, -20, 0)),
          (1.6, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.15, (0, 0, -50 * sx)), (1.3, (0, 0, -50 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"tip_{side}", (0, (0, 0, 0)), (0.15, (0, 0, -40 * sx)), (1.3, (0, 0, -40 * sx)), (1.6, (0, 0, 0)))
    return m
