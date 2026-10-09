"""Canopy Dart-Frog Assassin (Grenouille assassine de la canopée): the poison killer of the Canopy Temple-City, about
1.5 blocks tall in its crouch.

Silhouette idea: a poison dart frog that learned to hunt men. A lean, crouching frog-man on long folded hind legs,
skin of electric blue blotched with black and banded with sulphur yellow on the limbs, the colours that warn
everything in the jungle off. A wide flat head with two bulging golden eyes on top, a broad lipless mouth and a pale
throat sac that swells before it strikes. Over its shoulders a mantle of stitched dark leaves, a cord bandolier of
bamboo darts across its chest and a blowpipe slung on its back; its fingers end in round sticky pads. It leaps from
platform to platform, lashes its poisoned tongue out from several blocks away and slaps with its sticky hands.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

BLUE = (36, 108, 226)
BLUE_L = (92, 168, 255)
BLUE_D = (20, 58, 140)
SPOT = (16, 18, 30)
YELLOW = (250, 196, 36)
YELLOW_D = (196, 132, 20)
BELLY = (170, 214, 250)
THROAT = (238, 226, 160)
EYE = (255, 196, 40)
EYE_L = (255, 238, 140)
PUPIL = (14, 12, 10)
LEAF = (46, 92, 40)
LEAF_L = (82, 136, 56)
LEAF_D = (26, 54, 26)
CORD = (150, 112, 64)
BAMBOO = (170, 168, 78)
BAMBOO_D = (110, 112, 46)
TONGUE = (226, 92, 120)
TONGUE_D = (160, 50, 80)
POISON = (150, 230, 60)


def skin(seed=0, bands=False, belly=False):
    """Poison-frog skin: electric blue, a lit top, irregular black blotches; ``bands``: sulphur-yellow rings (limbs);
    ``belly``: the pale underside on the front face."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BLUE_D
        if belly and face == "front" and 0 < x < w - 1:
            return BELLY if (x + y) % 5 else mix(BELLY, BLUE_L, 0.4)
        if bands and face != "top" and (y + seed) % 5 in (0, 1):
            return YELLOW if (x + y) % 4 else YELLOW_D
        if K.h(x // 2, (y + x % 2) // 2, seed) % 7 == 0:
            return SPOT
        c = BLUE_L if face == "top" and (x + y) % 3 == 0 else BLUE
        return mul(c, 1.06 - 0.18 * y / max(1, h)) if face != "top" else c
    return f


def leaves(seed=0):
    """A mantle of stitched leaves: overlapping pointed leaf tips with a lit midrib, ragged at the bottom."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return LEAF_D if (x + seed) % 2 else None
        if face != "top" and y == h - 1 and (x + seed) % 3 == 1:
            return None
        if face != "top" and (x + seed) % 3 == 1:
            return LEAF_L                                                                     # midrib
        c = LEAF if (x + y // 2 + seed) % 3 else LEAF_D
        if K.h(x, y, seed) % 17 == 0:
            c = mix(c, (130, 110, 40), 0.5)
        return c
    return f


def bamboo(face, x, y, w, h):
    if face in ("top", "bottom"):
        return BAMBOO_D
    return BAMBOO_D if y % 4 == 0 else (BAMBOO if x % 2 == 0 else mix(BAMBOO, BAMBOO_D, 0.4))


def build():
    m = Model("dart_frog_assassin", seed=1259, shadow=0.55, walk_speed=1.2, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton: a deep crouch
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -9, 1.5))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "hips", pivot=(2.6 * sx, 0, 0), rot=(-60, 0, -14 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 6, 0), rot=(110, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 7, 0), rot=(-50, 0, 14 * sx))
    m.part("body", "hips", pivot=(0, 0, 0), rot=(34, 0, 0))
    m.part("head", "body", pivot=(0, -8.5, -1.5), rot=(-34, 0, 0))
    m.part("jaw", "head", pivot=(0, 0, 0.5))
    m.part("throat", "jaw", pivot=(0, 1.5, -3), scale=(1, 0.6, 1))
    m.part("tongue", "head", pivot=(0, 0.5, -6), scale=(0.02, 0.02, 0.02))
    m.part("arm_r", "body", pivot=(-4, -8, -0.5), rot=(-40, 0, 14))
    m.part("forearm_r", "arm_r", pivot=(0, 5, 0), rot=(-40, 0, 0))
    m.part("arm_l", "body", pivot=(4, -8, -0.5), rot=(-40, 0, -14))
    m.part("forearm_l", "arm_l", pivot=(0, 5, 0), rot=(-40, 0, 0))
    m.part("pipe", "body", pivot=(0, -6, 3), rot=(0, 0, 40))

    # ------------------------------------------------------------------ hind legs: long, folded, banded
    for side, sx in (("r", -1), ("l", 1)):
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        m.box(th, -1.5, -0.5, -1.5, 3, 7, 3, skin(1 + sx, bands=True))
        m.box(sh, -1, 0, -1, 2, 7, 2, skin(3 + sx, bands=True))
        m.box(ft, -1.5, 0.5, -5, 3, 1, 6, skin(5 + sx))
        for k, tx in enumerate((-2, -0.5, 1)):                                                 # long webbed toes
            m.box(ft, tx, 0.5, -7, 1, 1, 2, {"*": BLUE_D, "front": YELLOW})

    # ------------------------------------------------------------------ body: lean torso, leaf mantle, bandolier
    m.box("body", -3.5, -9, -2.5, 7, 9, 5, skin(10, belly=True))
    m.box("body", -4, -9.5, -3, 8, 4, 6, leaves(11))                                          # the leaf mantle
    m.box("body", -3, -10, -1, 6, 1, 4, leaves(12))
    # the bandolier of darts from the left shoulder to the right hip
    for i in range(5):
        x, y = 2.5 - i * 1.4, -8 + i * 1.6
        m.box("body", x, y, -2.9, 1, 1, 1, CORD)
        if i % 2 == 0:
            m.box("body", x - 0.3, y - 2, -3.4, 1, 3, 1, {"*": BAMBOO, "top": POISON})            # a dart, poison-tipped
    for i in range(5):
        m.box("body", 2.5 - i * 1.4, -8 + i * 1.6, 2.1, 1, 1, 1, CORD)

    # ------------------------------------------------------------------ head: wide and flat, eyes on top
    def mouth(f_, x, y, w, h):
        if f_ == "front" and y == h - 1:
            return SPOT                                                                       # the lip line
        return skin(20)(f_, x, y, w, h)
    m.box("head", -4, -3.5, -6, 8, 4, 7, {"front": mouth, "*": skin(21)})
    m.box("jaw", -4, 0, -6.5, 8, 2, 7, {"top": TONGUE_D, "front": lambda f_, x, y, w, h: BELLY if y else SPOT,
                                        "*": skin(22, belly=False)})
    for sx in (-1, 1):
        x0 = -4.5 if sx < 0 else 1.5

        def eye(f_, x, y, w, h):
            if f_ == "bottom":
                return BLUE_D
            if f_ in ("front", "left", "right") and y == 1 and x == 1:
                return PUPIL                                                                  # the pupil
            return EYE_L if (x, y) == (0, 0) else EYE
        m.box("head", x0, -5.5, -5, 3, 3, 3, eye, glow={"*": lambda f_, x, y, w, h: EYE if f_ != "bottom" and (x, y) != (1, 1) else None})
        m.box("head", x0 - 0.2, -3, -5.2, 3, 1, 3, skin(23 + sx))                                 # the lid ridge
    m.box("throat", -2.5, 0, -3, 5, 2, 4, {"*": THROAT, "bottom": mul(THROAT, 0.85)})
    m.box("tongue", -0.5, -0.5, -16, 1, 1, 16, {"*": TONGUE, "bottom": TONGUE_D})
    m.box("tongue", -1, -1, -17.5, 2, 2, 2, {"*": TONGUE_D, "front": POISON}, glow={"front": POISON, "*": None})

    # ------------------------------------------------------------------ arms: thin, banded, sticky pads
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1, -1, -1, 2, 6, 2, skin(30 + sx, bands=True))
        m.box(fore, -1, 0, -1, 2, 5, 2, skin(32 + sx))
        for k, fx in enumerate((-1.5, 0, 1.5)):
            m.box(fore, fx - 0.5, 5, -1, 1, 2, 1, BLUE_D)
            m.box(fore, fx - 0.5, 6.5, -1.5, 1, 1, 1, YELLOW)                                     # the round pads
    # the blowpipe slung across the back
    m.box("pipe", -0.5, -8, -0.5, 1, 16, 1, bamboo)
    m.box("pipe", -1, -9, -1, 2, 1, 2, BAMBOO_D)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.4)
    idle.scale("throat", (0, (1, 1, 1)), (0.3, (1.1, 1.8, 1.1)), (0.6, (1, 1, 1)), (1.5, (1, 1, 1)), (1.8, (1.1, 1.8, 1.1)),
               (2.1, (1, 1, 1)), (2.4, (1, 1, 1)))
    idle.pos("body", (0, (0, 0, 0)), (1.2, (0, -0.4, 0)), (2.4, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.5, (0, 16, 0)), (0.6, (0, 16, 0)), (1.3, (0, -14, 0)), (1.4, (0, -14, 0)),
             (2.4, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.2, (6, 0, 4)), (2.4, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.2, (6, 0, -4)), (2.4, (0, 0, 0)))

    # walk: short frog hops
    walk = m.anim("walk", 0.8)
    for side in ("r", "l"):
        walk.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.2, (-10, 0, 0)), (0.35, (40, 0, 0)), (0.55, (10, 0, 0)), (0.8, (0, 0, 0)))
        walk.rot(f"shin_{side}", (0, (0, 0, 0)), (0.2, (10, 0, 0)), (0.35, (-60, 0, 0)), (0.55, (-20, 0, 0)), (0.8, (0, 0, 0)))
        walk.rot(f"foot_{side}", (0, (0, 0, 0)), (0.35, (30, 0, 0)), (0.8, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.2, (0, -1, 0)), (0.4, (0, 3, -1)), (0.6, (0, 0.5, 0)), (0.8, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, 0)), (0.2, (8, 0, 0)), (0.4, (-10, 0, 0)), (0.8, (0, 0, 0)))
    walk.rot("arm_r", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (0.8, (0, 0, 0)))
    walk.rot("arm_l", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (0.8, (0, 0, 0)))

    # lash: the throat sac balloons and the head rears back, mouth gaping (0.6 s telegraph), then the tongue whips out
    # several blocks (hits at 0.6 s = 12 ticks) and snaps back
    a = m.anim("lash", 1.1)
    a.scale("throat", (0, (1, 1, 1)), (0.5, (1.3, 2.5, 1.3)), (0.6, (1.35, 2.7, 1.35)), (0.65, (1, 1, 1), "linear"), (1.1, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-26, 0, 0)), (0.6, (-28, 0, 0)), (0.65, (-8, 0, 0), "linear"), (0.9, (-6, 0, 0)),
          (1.1, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.6, (34, 0, 0)), (0.9, (30, 0, 0)), (1.1, (0, 0, 0)))
    a.scale("tongue", (0, (1, 1, 1)), (0.6, (1, 1, 1)), (0.62, (1.98, 1.98, 1.5), "linear"), (0.68, (1.98, 1.98, 5.0), "linear"),
            (0.76, (1.98, 1.98, 5.0)), (0.93, (1.98, 1.98, 1.3), "linear"), (0.95, (1, 1, 1), "linear"), (1.1, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (-12, 0, 0)), (0.65, (10, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1, 1)), (0.65, (0, 0, -1)), (1.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (20, 0, 30)), (0.7, (-10, 0, 10)), (1.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (20, 0, -30)), (0.7, (-10, 0, -10)), (1.1, (0, 0, 0)))

    # leap: sinks into a deep crouch, arms swept back (0.5 s telegraph), launches (at 0.5 s = 10 ticks) stretched out
    # long, and tucks in for the landing
    a = m.anim("leap", 1.3)
    for side, s in (("r", -1), ("l", 1)):
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.45, (-14, 0, 0)), (0.5, (-16, 0, 0)), (0.6, (80, 0, 0), "linear"), (0.95, (70, 0, 0)),
              (1.1, (0, 0, 0)), (1.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.45, (16, 0, 0)), (0.6, (-100, 0, 0), "linear"), (0.95, (-90, 0, 0)), (1.1, (0, 0, 0)))
        a.rot(f"foot_{side}", (0, (0, 0, 0)), (0.6, (60, 0, 0)), (0.95, (50, 0, 0)), (1.1, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.45, (50, 0, -20 * s)), (0.6, (-110, 0, 10 * s), "linear"), (0.95, (-100, 0, 10 * s)),
              (1.1, (-20, 0, 20 * s)), (1.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.45, (0, -2.5, 1)), (0.5, (0, -2.6, 1)), (0.6, (0, 2, -2), "linear"), (0.95, (0, 1, -2)),
          (1.1, (0, -1.5, 0)), (1.3, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.45, (14, 0, 0)), (0.6, (36, 0, 0), "linear"), (0.95, (30, 0, 0)), (1.1, (6, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.45, (-14, 0, 0)), (0.6, (-30, 0, 0)), (1.1, (0, 0, 0)))

    # slap: the right hand raised high, pads spread (0.35 s telegraph), then slapped down (lands at 0.35 s = 7 ticks)
    a = m.anim("slap", 0.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-150, 0, 30)), (0.35, (-156, 0, 32)), (0.45, (-40, 0, 0), "linear"), (0.6, (-36, 0, 0)),
          (0.8, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 0)), (0.45, (10, 0, 0), "linear"), (0.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (-10, 20, 0)), (0.45, (14, -14, 0), "linear"), (0.8, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, 1, 1)), (0.45, (0, -0.5, -2), "linear"), (0.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.3, (16, 0, 0)), (0.5, (0, 0, 0)))
