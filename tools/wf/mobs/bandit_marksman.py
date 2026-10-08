"""Bandit Marksman (Tireur bandit): the sharpshooter of the bandit camps and the ruined watchtowers.

Silhouette idea: a scarecrow with a longbow. A deep red hood over a black face scarf (only two cold eyes show), a
patched leather long coat with a bandolier of brass smoke bombs across the chest, a quiver bristling over the
shoulder and a recurve bow that is taller than its arm.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

HOOD = (140, 36, 34)
HOOD_D = (100, 24, 24)
SCARF = (36, 32, 34)
COAT = (110, 78, 50)
COAT_D = (80, 56, 36)
PATCH = (150, 112, 70)
SKIN = (200, 150, 116)
EYE = (226, 236, 240)
BRASS = (204, 160, 72)
BRASS_D = (130, 96, 40)
BOW = (92, 60, 38)
BOW_L = (150, 104, 62)


def folds(base, dark, seed=0, lit=True):
    """Heavy cloth hanging in folds: vertical darker fold lines, a lit top edge, a shadowed lower edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(dark, 0.8)
        if face == "top":
            return mix(base, (255, 230, 210), 0.12) if lit else base
        if y == 0 and lit and h > 2:
            return mix(base, (255, 230, 210), 0.15)
        c = base
        if (x + K.h(seed, x // 3)) % 3 == 0:
            c = dark                                                            # a fold
        elif (x + K.h(seed, x // 3)) % 3 == 1:
            c = mix(base, (255, 230, 210), 0.06)
        if y >= h - 1 and h > 3:
            c = mul(c, 0.82)
        return c
    return f


def build():
    m = Model("bandit_marksman", seed=351, shadow=0.5, walk_speed=1.1, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("body", "bone", pivot=(0, -12, 0))
    m.part("head", "body", pivot=(0, -12, 0))
    m.part("coat", "body", pivot=(0, 0, 0))
    m.part("arm_r", "body", pivot=(-5, -11, 0), rot=(0, 0, 4))
    m.part("arm_l", "body", pivot=(5, -11, 0), rot=(0, 0, -4))
    m.part("off", "arm_l", pivot=(0, 9.5, 0))
    m.part("bow_top", "off", pivot=(0, -1, 0), rot=(-22, 0, 0))
    m.part("bow_bot", "off", pivot=(0, 1, 0), rot=(22, 0, 0))
    m.part("bomb", "arm_r", pivot=(0, 10, 0))

    coat = K.leather(COAT, seed=1, stitch=COAT_D)

    def patched(f_, x, y, w, h):
        if 2 <= x <= 4 and 3 <= y <= 5 and f_ in ("front", "left"):
            return PATCH if (x + y) % 3 else mul(PATCH, 0.8)                  # a sewn-on patch
        return coat(f_, x, y, w, h)

    # legs: dark trousers, tall boots
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -2, 0, -2, 4, 12, 4, lambda f_, x, y, w, h: K.leather((60, 44, 32), seed=2)(f_, x, y, w, h)
              if y >= 6 else K.cloth((70, 64, 60), (54, 50, 48), seed=3)(f_, x, y, w, h))

    # torso, bandolier with brass smoke bombs
    def torso(f_, x, y, w, h):
        if f_ == "front" and abs((x - y * 0.66) - 0.5) < 1.0:
            return BRASS if y % 3 == 1 else (70, 48, 30)                      # the bandolier and its bombs
        if f_ == "front" and x in (3, 4) and y < 3:
            return SCARF
        return patched(f_, x, y, w, h)
    m.box("body", -4, -12, -2, 8, 12, 4, torso)

    def belt(f_, x, y, w, h):
        if f_ == "front" and x == w // 2:
            return BRASS
        return (54, 38, 26)
    m.box("body", -4.5, -3, -2.5, 9, 1, 5, belt)

    # coat tails hanging to the knees, split at the back
    def tails(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return None
        if f_ == "back" and x in (w // 2 - 1, w // 2):
            return None                                                         # the vent
        if y == h - 1 and x % 3 == 0:
            return None                                                         # a ragged hem
        if f_ == "front" and 2 <= x <= w - 3:
            return None                                                         # open at the front
        return patched(f_, x, y, w, h)
    m.box("coat", -4.5, -2, -2.5, 9, 9, 5, tails)
    m.part("coat_b", "coat", pivot=(0, 2, 2.5))
    m.box("coat_b", -4, 0, 0, 8, 6, 1, {"front": None, "top": None, "bottom": None,
                                        "*": lambda f_, x, y, w, h: None if (y == h - 1 and x % 3 == 1) else patched(f_, x, y, w, h)})
    # belt pouches and a brass powder flask
    m.box("body", -5, -3.5, -1.5, 1, 3, 3, K.leather((96, 64, 40), seed=12, stitch=BRASS_D))
    m.box("body", 4, -3.5, -2, 1, 2, 2, {"*": BRASS, "top": BRASS_D})
    # boot cuffs
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -2.5, 5, -2.5, 5, 2, 5, K.leather((76, 54, 38), seed=13))

    # quiver over the right shoulder
    m.part("quiver", "body", pivot=(0, -6, 2), rot=(0, 0, 28))
    m.box("quiver", -1.5, -9, 0, 3, 10, 3, {"top": (30, 22, 18), "*": K.leather((90, 60, 36), seed=4, stitch=BRASS_D)})
    m.box("quiver", -2, -8, -0.5, 4, 1, 4, {"*": BRASS_D, "top": BRASS})                       # brass rim
    m.box("quiver", -1, -12, 0.5, 2, 3, 2, lambda f_, x, y, w, h: (236, 230, 220) if (x + y) % 2 else (150, 40, 34))
    m.box("quiver", -1.5, -11, 1, 1, 2, 1, (236, 230, 220))                                    # loose fletchings
    # shoulder cape of the hood
    mantle = folds(HOOD, HOOD_D, seed=5)

    def mantle_paint(f_, x, y, w, h):
        if f_ in ("front", "back", "left", "right") and y == h - 1 and K.h(x, f_ == "front") % 3 == 0:
            return None                                                         # a ragged, torn hem
        return mantle(f_, x, y, w, h)
    m.box("body", -5.5, -13, -3, 11, 4, 6, {"bottom": None, "*": mantle_paint})

    # ------------------------------------------------------------------ head: hood, scarf, two eyes
    def face(f_, x, y, w, h):
        if f_ == "front":
            if y <= 2:
                return folds(HOOD, HOOD_D, seed=6)(f_, x, y, w, h) if y < 2 else mul(HOOD_D, 0.6)
            if y == 3:
                if x in (2, 5):
                    return EYE
                if x in (1, 6):
                    return (40, 30, 26)
                return SKIN
            if y == 4:
                return mul(SKIN, 0.85) if 1 <= x <= 6 else SCARF
            return SCARF if (x + y) % 4 else (52, 46, 48)                       # the face scarf
        return folds(HOOD, HOOD_D, seed=7)(f_, x, y, w, h)
    m.box("head", -4, -8, -4, 8, 8, 8, face, glow={"front": lambda f_, x, y, w, h: (180, 200, 210) if y == 3 and x in (2, 5) else None,
                                                     "*": None})
    m.box("head", -4.5, -9, -4.5, 9, 3, 9, {"bottom": None, "front": lambda f_, x, y, w, h: None if y == h - 1 and 1 <= x <= w - 2
                                            else folds(HOOD, HOOD_D, seed=8)(f_, x, y, w, h),
                                            "*": folds(HOOD, HOOD_D, seed=8)})
    m.box("head", -1.5, -10, 3, 3, 3, 3, folds(HOOD, HOOD_D, seed=9))       # the hood's peak falling back
    m.box("head", -1, -8, 6, 2, 3, 2, folds(HOOD, HOOD_D, seed=10))          # ... and its long point
    # the face scarf's two loose tails, streaming behind the neck
    m.part("scarf", "head", pivot=(1.5, -1, 4), rot=(20, 0, 0))
    m.box("scarf", -1, 0, 0, 2, 7, 1, lambda f_, x, y, w, h: None if (y == h - 1 and x == 1) else (SCARF if (x + y) % 4 else (52, 46, 48)))
    m.box("scarf", -2.5, 0, 0.5, 1, 5, 1, SCARF)

    # ------------------------------------------------------------------ arms (leather sleeves, fingerless gloves)
    def sleeve(f_, x, y, w, h):
        if y >= h - 2:
            return SKIN if y == h - 1 and x % 2 else (50, 40, 34)
        if y == h - 4:
            return BRASS_D
        return coat(f_, x, y, w, h)
    for arm in ("arm_r", "arm_l"):
        m.box(arm, -1.5, -1, -1.5, 3, 12, 3, sleeve)

    # recurve bow in the left hand, a smoke bomb ready in the right
    m.box("off", -0.5, -1.5, -1.5, 1, 3, 1, K.leather((60, 40, 30), seed=10))
    stave = K.wood(BOW_L, BOW, seed=11)
    m.box("bow_top", -0.5, -9, -1.5, 1, 8, 1, stave)
    m.box("bow_bot", -0.5, 1, -1.5, 1, 8, 1, stave)
    m.box("bow_top", -0.5, -10, -0.5, 1, 1, 1, BRASS)                         # brass nocks
    m.box("bow_bot", -0.5, 9, -0.5, 1, 1, 1, BRASS)

    def bomb(f_, x, y, w, h):
        if f_ == "top":
            return (60, 60, 60) if (x + y) % 2 else (230, 120, 40)            # the fuse
        return BRASS if (x + y) % 3 else BRASS_D
    m.box("bomb", -1, -0.5, -1, 2, 2, 2, bomb)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, 0.4, 0)), (3.0, (0, 0, 0)))                         # breathing
    idle.rot("body", (0, (0, 0, 0)), (1.5, (2, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (0, 18, 0)), (1.3, (0, 18, 0)), (2.1, (-4, -16, 0)), (2.6, (-4, -16, 0)),
             (3.0, (0, 0, 0)))                                                                       # always scanning
    idle.rot("coat", (0, (0, 0, 0)), (1.5, (3, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("coat_b", (0, (0, 0, 0)), (1.0, (6, 0, 0)), (2.2, (2, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("scarf", (0, (0, 0, 0)), (0.7, (8, 0, 6)), (1.6, (-4, 0, -4)), (2.4, (6, 0, 4)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-4, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (3, 0, -2)), (3.0, (0, 0, 0)))
    idle.rot("bomb", (0, (0, 0, 0)), (1.5, (0, 90, 0)), (3.0, (0, 0, 0)))                         # tossing it idly
    idle.pos("bomb", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.85, (0, 2.5, 0)), (1.1, (0, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("leg_r", (0, (30, 0, 0)), (0.5, (-30, 0, 0)), (1.0, (30, 0, 0)))
    walk.rot("leg_l", (0, (-30, 0, 0)), (0.5, (30, 0, 0)), (1.0, (-30, 0, 0)))
    walk.rot("arm_r", (0, (-24, 0, 0)), (0.5, (24, 0, 0)), (1.0, (-24, 0, 0)))
    walk.rot("arm_l", (0, (20, 0, 0)), (0.5, (-20, 0, 0)), (1.0, (20, 0, 0)))
    walk.rot("coat", (0, (12, 0, 0)), (0.5, (18, 0, 0)), (1.0, (12, 0, 0)))
    walk.rot("coat_b", (0, (14, 0, 0)), (0.25, (24, 0, 0)), (0.5, (14, 0, 0)), (0.75, (24, 0, 0)), (1.0, (14, 0, 0)))
    walk.rot("body", (0, (5, -5, 0)), (0.5, (5, 5, 0)), (1.0, (5, -5, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.8, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.8, 0)), (1.0, (0, 0, 0)))
    walk.rot("head", (0, (-5, 5, 0)), (0.5, (-5, -5, 0)), (1.0, (-5, 5, 0)))
    walk.rot("scarf", (0, (40, 0, 0)), (0.25, (52, 0, 6)), (0.5, (40, 0, 0)), (0.75, (52, 0, -6)), (1.0, (40, 0, 0)))
    walk.rot("quiver", (0, (0, 0, -3)), (0.5, (0, 0, 3)), (1.0, (0, 0, -3)))

    # draw: raise the bow, draw to the cheek, hold, loose at 0.75 s (15 ticks)
    a = m.anim("draw", 1.1)
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-90, -12, 0)), (0.75, (-90, -12, 0)), (0.85, (-84, -12, 0)), (1.1, (0, 0, 0)))
    a.rot("off", (0, (0, 0, 0)), (0.25, (90, 0, 0)), (0.85, (90, 0, 0)), (1.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-90, 20, 0)), (0.7, (-92, 64, 0)), (0.75, (-92, 66, 0)),
          (0.8, (-80, 90, 10), "linear"), (1.1, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.25, (0, -22, 0)), (0.75, (0, -26, 0)), (1.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.25, (0, 22, 0)), (0.75, (0, 26, 0)), (1.1, (0, 0, 0)))
    a.rot("bow_top", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (0.78, (4, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("bow_bot", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.78, (-4, 0, 0), "linear"), (1.1, (0, 0, 0)))

    # throw: an underhand toss of a smoke bomb at its feet (released at 0.35 s = 7 ticks)
    a = m.anim("throw", 0.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (48, 0, 14)), (0.35, (-70, 0, 0), "linear"), (0.5, (-60, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.25, (14, 12, 0)), (0.35, (-6, -6, 0), "linear"), (0.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.25, (-20, 0, 0)), (0.35, (-26, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.25, (14, 0, 0)), (0.8, (0, 0, 0)))
    a.scale("bomb", (0, (1, 1, 1)), (0.34, (1, 1, 1)), (0.36, (0, 0, 0), "linear"), (0.7, (0, 0, 0)), (0.8, (1, 1, 1), "linear"))

    # kick: a quick front kick to push a pest away (lands at 0.25 s = 5 ticks)
    a = m.anim("kick", 0.6)
    a.rot("leg_r", (0, (0, 0, 0)), (0.15, (40, 0, 0)), (0.25, (-85, 0, 0), "linear"), (0.35, (-80, 0, 0)), (0.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.15, (-6, 0, 0)), (0.25, (12, 0, 0), "linear"), (0.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-30, 0, 30)), (0.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-20, 0, -26)), (0.6, (0, 0, 0)))
    a.rot("coat_b", (0, (0, 0, 0)), (0.25, (30, 0, 0)), (0.6, (0, 0, 0)))

    # dodge: a crouched hop backwards
    a = m.anim("dodge", 0.5)
    a.rot("body", (0, (0, 0, 0)), (0.1, (14, 0, 0)), (0.35, (-10, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.1, (-40, 0, 0)), (0.35, (20, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.1, (-40, 0, 0)), (0.35, (30, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("coat", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("coat_b", (0, (0, 0, 0)), (0.2, (-40, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("scarf", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (0.5, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.1, (0, -1, 0)), (0.25, (0, 2, 3)), (0.4, (0, 0, 4)), (0.5, (0, 0, 0)))
    return m
