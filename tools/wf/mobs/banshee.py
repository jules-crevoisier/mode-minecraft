"""Banshee: a floating spectral woman (about 2 blocks). Long silver hair streaming behind her, a tattered
grave gown that dissolves into glowing wisps instead of legs, a long torn train that trails in the air,
hollow black eye sockets with pale cyan pin-point eyes and a jaw that drops impossibly wide to wail.

Animations: idle (hovering bob, gown and hair floating), walk (the slow forward drift: leaning, gown and
hair streaming back), wail (telegraphed scream, impact 0.8 s = 16 ticks), claw (rake, impact 0.6 s = 12 ticks).
"""
import math

from ..models import Model
from ..texgen import mix, mul

SKIN = (214, 226, 232)
SKIN_D = (136, 156, 174)
SKIN_L = (232, 240, 244)
GOWN = (128, 148, 170)
GOWN_D = (70, 84, 110)
GOWN_L = (196, 212, 226)
SHADE = (36, 50, 74)
HAIR = (226, 232, 238)
HAIR_D = (150, 162, 178)
HOLLOW = (12, 16, 26)
GLOW = (176, 252, 255)
WISP = (150, 220, 240)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
def gown(seed=0, tatter=0, base=GOWN, dark=GOWN_D, light=GOWN_L, grad=0.45, hem=True, top_shade=0.0):
    """Grave linen: soft vertical folds, fading to a cold blue-black toward the bottom, torn strips."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 0.7)
        if tatter:
            sw = 1 + _h(seed, x // 2) % 3
            r = _h((x + seed) // sw, seed, 5)
            cut = r % (tatter + 1)
            if r % 4 == 0:
                cut = tatter
            if y >= h - cut:
                return None
        s = 0.65 * math.sin(x * 1.25 + seed) + 0.35 * math.sin(x * 0.5 + seed * 0.7)
        c = mul(base, 1.0 + 0.12 * s)
        if s < -0.7:
            c = mix(c, dark, 0.55)
        elif s > 0.82:
            c = mix(c, light, 0.45)
        t = y / max(1, h - 1)
        c = mix(c, SHADE, grad * t * t)
        if top_shade and y == 0:
            c = mix(c, dark, top_shade)
        if hem and tatter and y == h - tatter - 2:
            c = mix(c, light, 0.35)
        r2 = _h(x, y, seed, FACE_N[face])
        if r2 % 37 == 0:
            c = mix(c, light, 0.4)
        elif r2 % 29 == 0:
            c = mix(c, dark, 0.5)
        return c
    return f


def wisp_glow(seed=0, tatter=0, from_y=0.5, alpha=90):
    """Faint spectral luminescence on the lower part of the gown (emissive, partly transparent)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if tatter:
            sw = 1 + _h(seed, x // 2) % 3
            r = _h((x + seed) // sw, seed, 5)
            cut = r % (tatter + 1)
            if r % 4 == 0:
                cut = tatter
            if y >= h - cut:
                return None
        t = y / max(1, h - 1)
        if t < from_y:
            return None
        a = int(alpha * (t - from_y) / max(0.01, 1 - from_y))
        if (x + y + seed) % 3 == 0:
            a = int(a * 1.4)
        return (*WISP, max(0, min(255, a)))
    return f


def skin(seed=0, base=SKIN, gaunt=True):
    def f(face, x, y, w, h):
        c = mul(base, 1 + ((_h(x, y, seed, FACE_N[face]) % 100) - 50) / 900)
        if face == "top":
            return mix(c, SKIN_L, 0.25)
        if face == "bottom":
            return mul(c, 0.8)
        if gaunt and (x == 0 or x == w - 1):
            c = mix(c, SKIN_D, 0.4)
        if _h(x, y, seed) % 23 == 0:
            c = mix(c, (150, 170, 200), 0.5)  # a faint vein
        return c
    return f


def hair(seed=0, ragged=6, streak=True):
    """Long silver hair: strands along the length, darker roots and partings, ragged ends."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return HAIR_D if face == "bottom" else HAIR
        if ragged:
            cut = _h(x, seed, 11) % (ragged + 1)
            if y >= h - cut:
                return None
        k = _h(x, seed) % 5
        c = HAIR if k in (0, 1, 3) else mix(HAIR, HAIR_D, 0.55)
        if k == 4:
            c = mix(HAIR, HAIR_D, 0.85)
        if streak and (x + y // 3 + seed) % 7 == 0:
            c = mix(c, (255, 255, 255), 0.5)
        t = y / max(1, h - 1)
        return mix(c, (120, 140, 168), 0.35 * t)
    return f


def face_paint():
    """Front of the skull: hollow eye sockets, sunken cheeks, a thin grey mouth line."""
    base = skin(7)

    def f(face, x, y, w, h):
        c = base(face, x, y, w, h)
        if face != "front":
            return c
        # w=6, h=5: brow at y=1, sockets y=2..3
        if y in (2, 3) and x in (1, 4):
            return HOLLOW
        if y in (2, 3) and x in (0, 5) and y == 3:
            return mix(c, SKIN_D, 0.5)
        if y == 1 and x in (1, 4):
            return mix(c, SKIN_D, 0.7)   # heavy brow shadow
        if y == 4 and x in (1, 4):
            return mix(c, SKIN_D, 0.55)  # dark under the eyes
        if y == 4 and x in (0, 5):
            return mix(c, SKIN_D, 0.35)
        return c
    return f


def eye_glow(face, x, y, w, h):
    if face == "front" and y == 3 and x in (1, 4):
        return GLOW
    return None


# ------------------------------------------------------------------ model
def build():
    m = Model("banshee", seed=31, shadow=0.45, walk_speed=0.7, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -18, 0))
    m.part("torso", "body", pivot=(0, 0, 0), rot=(4, 0, 0))
    m.part("head", "torso", pivot=(0, -10, -0.5))
    m.part("jaw", "head", pivot=(0, -2, 1.5))
    m.part("hair", "head", pivot=(0, -6.5, 3), rot=(12, 0, 0))
    m.part("hair_tip", "hair", pivot=(0, 11, 0.5), rot=(10, 0, 0))
    m.part("lock_r", "head", pivot=(-3, -5, -2), rot=(-6, 0, 6))
    m.part("lock_l", "head", pivot=(3, -5, -2), rot=(-6, 0, -6))
    m.part("arm_r", "torso", pivot=(-4.5, -8.5, 0), rot=(-14, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(0, 7, 0), rot=(-22, 0, 0))
    m.part("arm_l", "torso", pivot=(4.5, -8.5, 0), rot=(-10, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(0, 7, 0), rot=(-18, 0, 0))
    m.part("skirt", "body", pivot=(0, 0, 0))
    m.part("skirt2", "skirt", pivot=(0, 4, 0.5), rot=(4, 0, 0))
    m.part("skirt3", "skirt2", pivot=(0, 6, 0.5), rot=(12, 0, 0))
    m.part("tail", "skirt3", pivot=(0, 4, 0.5), rot=(22, 0, 0))
    m.part("train", "skirt2", pivot=(0, 1, 3.5), rot=(38, 0, 0))
    m.part("train_tip", "train", pivot=(0, 8, 0), rot=(18, 0, 0))

    # torso: narrow waist, bony shoulders under a torn bodice
    m.box("torso", -2.5, -3, -1.5, 5, 3, 3, gown(2, top_shade=0.2))
    def bodice(f_, x, y, w, h):
        if y < 2:
            return SKIN_D if (y == 1 and x in (2, 4)) else skin(3)(f_, x, y, w, h)
        if y == 2:
            return GOWN_L if x % 2 == 0 else mix(GOWN_L, GOWN_D, 0.4)   # frayed lace neckline
        if x == 3:
            return (40, 48, 70) if y % 2 else (90, 104, 130)            # laced bodice seam
        return mix(gown(4, grad=0.0)(f_, x, y, w, h), GOWN_D, 0.25 if x in (0, 6) else 0.0)
    m.box("torso", -3.5, -9, -2, 7, 6, 4, {"front": bodice, "*": gown(4, grad=0.0)})
    m.box("torso", -3, -3.5, -1.8, 6, 1, 3, (52, 62, 88))     # dark sash
    m.box("torso", -4, -9.5, -2, 8, 1, 4, skin(5))          # collarbones / shoulder line
    m.box("torso", -1, -11, -1, 2, 2, 2, skin(6))           # neck
    # head: gaunt skull, hollow eyes, a jaw that drops wide
    m.box("head", -3, -7, -3.5, 6, 5, 6, {"front": face_paint(), "*": skin(7)}, glow=eye_glow)
    m.box("head", -2, -2, -3, 4, 2, 3, {"front": lambda f_, x, y, w, h: (60, 10, 40) if y == 0 else (20, 4, 18),
                                        "*": HOLLOW},
          glow={"front": lambda f_, x, y, w, h: (120, 240, 255, 200) if y == 1 and x in (1, 2) else None})
    m.box("jaw", -2.5, 0, -5, 5, 2, 5, {
        "front": lambda f_, x, y, w, h: (70, 80, 100) if y == 0 else skin(8)(f_, x, y, w, h),
        "top": (40, 20, 40), "*": skin(8)})
    # hair: a cap, a long sheet streaming down the back, two locks framing the face
    m.box("head", -3.5, -7.6, -3.8, 7, 2, 7, {"top": lambda f_, x, y, w, h: HAIR_D if x == 3 else hair(2, 0)("front", x, y, w, h),
                                              "*": hair(2, 0)})
    m.box("head", -3.6, -6, -1.5, 1, 4, 5, hair(3, 0))
    m.box("head", 2.6, -6, -1.5, 1, 4, 5, hair(4, 0))
    m.box("hair", -4, 0, 0, 8, 12, 1, hair(5, 0))
    m.box("hair_tip", -4, 0, -0.5, 8, 10, 1, hair(6, 6))
    m.box("lock_r", -1, 0, -1, 2, 11, 1, hair(7, 4))
    m.box("lock_l", -1, 0, -1, 2, 11, 1, hair(8, 4))

    # arms: thin, long, with tattered bell sleeves and long claws
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1, -0.5, -1, 2, 8, 2, gown(20 + sx, grad=0.1))
        m.box(fore, -0.5, 0, -0.5, 1, 6, 1, skin(22 + sx))
        m.box(fore, -1.5, -1, -1.5, 3, 7, 3, gown(23 + sx, tatter=4, grad=0.3),
              glow=wisp_glow(23 + sx, 4, 0.5, 70))
        for i, dx in enumerate((-0.9, 0, 0.9)):
            m.box(fore, dx - 0.5, 6, -1 + (i % 2) * 0.3, 1, 3 + (i == 1), 1,
                  lambda f_, x, y, w, h: (60, 70, 92) if y >= h - 1 else SKIN_D)

    # gown: a narrow waist flaring to a ragged hem, then tapering into a ghostly tail (no legs)
    m.box("skirt", -3.5, 0, -2.5, 7, 4, 5, gown(30, grad=0.1, top_shade=0.3))
    m.box("skirt2", -4.5, 0, -3.5, 9, 6, 7, gown(31, tatter=2, grad=0.35), glow=wisp_glow(31, 2, 0.55, 60))
    m.box("skirt3", -3.5, 0, -2.5, 7, 4, 5, gown(32, tatter=2, base=mix(GOWN, GOWN_D, 0.4), grad=0.55),
          glow=wisp_glow(32, 2, 0.0, 90))
    m.box("tail", -2, 0, -1.5, 4, 5, 3, gown(33, tatter=3, base=mix(GOWN_D, WISP, 0.25), grad=0.2),
          glow=wisp_glow(33, 3, 0.0, 170))
    # torn strips hanging from the hem
    for i, (x, z, hh) in enumerate(((-4.6, -2.5, 7), (4.6, -1.0, 6), (-4.6, 1.5, 5), (4.6, 2.0, 8))):
        m.box("skirt2", x, 3, z, 0, hh, 2, {"left": gown(50 + i, tatter=3, grad=0.6), "right": gown(50 + i, tatter=3, grad=0.6),
                                            "*": None}, glow={"side": wisp_glow(50 + i, 3, 0.3, 120)})
    m.box("skirt2", -2, 3, -3.6, 3, 7, 0, {"front": gown(56, tatter=4, grad=0.6), "back": gown(56, tatter=4, grad=0.6),
                                           "*": None}, glow={"side": wisp_glow(56, 4, 0.3, 120)})
    m.box("train", -3, 0, 0, 6, 8, 0, gown(40, tatter=0, grad=0.3))
    m.box("train_tip", -3, 0, 0, 6, 8, 0, gown(41, tatter=6, grad=0.7), glow=wisp_glow(41, 6, 0.2, 110))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.2)
    idle.pos("bone", (0, (0, 0, 0)), (1.6, (0, 1.6, 0)), (3.2, (0, 0, 0)))
    idle.rot("torso", (0, (0, 0, 0)), (1.6, (-3, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (2, -6, 3)), (2.4, (2, 6, -3)), (3.2, (0, 0, 0)))
    idle.rot("skirt", (0, (0, 0, 0)), (1.6, (3, 0, 1)), (3.2, (0, 0, 0)))
    idle.rot("skirt2", (0, (2, 0, 0)), (1.0, (6, 0, -2)), (2.6, (-1, 0, 2)), (3.2, (2, 0, 0)))
    idle.rot("skirt3", (0, (4, 0, 0)), (1.3, (10, 0, 3)), (2.8, (0, 0, -3)), (3.2, (4, 0, 0)))
    idle.rot("tail", (0, (0, 0, 0)), (0.9, (8, 0, 6)), (2.4, (-2, 0, -6)), (3.2, (0, 0, 0)))
    idle.rot("train", (0, (0, 0, 0)), (1.6, (10, 3, 0)), (3.2, (0, 0, 0)))
    idle.rot("train_tip", (0, (0, 0, 0)), (1.0, (-8, 0, 0)), (2.2, (14, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("hair", (0, (0, 0, 0)), (1.6, (8, 0, 2)), (3.2, (0, 0, 0)))
    idle.rot("hair_tip", (0, (0, 0, 0)), (1.2, (12, 0, -3)), (2.6, (-4, 0, 3)), (3.2, (0, 0, 0)))
    idle.rot("lock_r", (0, (0, 0, 0)), (1.6, (-6, 0, 4)), (3.2, (0, 0, 0)))
    idle.rot("lock_l", (0, (0, 0, 0)), (1.6, (-6, 0, -4)), (3.2, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.6, (-6, 0, 4)), (3.2, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.6, (-4, 0, -5)), (3.2, (0, 0, 0)))
    idle.rot("forearm_r", (0, (0, 0, 0)), (1.6, (-8, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.6, (6, 0, 0)), (3.2, (0, 0, 0)))

    # drift: lean into the glide, everything streams backward
    walk = m.anim("walk", 2.0)
    walk.rot("body", (0, (8, 0, 0)), (1.0, (11, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("head", (0, (-8, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (-8, 0, 0)))
    walk.rot("tail", (0, (14, 0, 0)), (0.5, (22, 0, 5)), (1.5, (12, 0, -5)), (2.0, (14, 0, 0)))
    walk.rot("skirt", (0, (10, 0, 0)), (1.0, (14, 0, 2)), (2.0, (10, 0, 0)))
    walk.rot("skirt2", (0, (12, 0, 0)), (1.0, (16, 0, -3)), (2.0, (12, 0, 0)))
    walk.rot("skirt3", (0, (16, 0, 0)), (0.5, (24, 0, 4)), (1.5, (14, 0, -4)), (2.0, (16, 0, 0)))
    walk.rot("train", (0, (18, 0, 0)), (1.0, (26, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("train_tip", (0, (10, 0, 0)), (0.6, (24, 0, 0)), (1.4, (4, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("hair", (0, (22, 0, 0)), (1.0, (30, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("hair_tip", (0, (14, 0, 0)), (0.7, (24, 0, 0)), (1.6, (8, 0, 0)), (2.0, (14, 0, 0)))
    walk.rot("arm_r", (0, (28, 0, 6)), (1.0, (34, 0, 10)), (2.0, (28, 0, 6)))
    walk.rot("arm_l", (0, (34, 0, -10)), (1.0, (28, 0, -6)), (2.0, (34, 0, -10)))

    # wail: rise and arch back (telegraph), then a wide-jawed scream thrust forward (16 ticks)
    a = m.anim("wail", 2.2)
    a.pos("bone", (0, (0, 0, 0)), (0.8, (0, 3, 2)), (0.9, (0, 2, -2), "linear"), (1.5, (0, 2, -2)), (2.2, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.8, (-22, 0, 0)), (0.9, (16, 0, 0), "linear"), (1.5, (14, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-34, 0, 0)), (0.9, (12, 0, 0), "linear"), (1.5, (10, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.8, (18, 0, 0)), (0.9, (62, 0, 0), "linear"), (1.5, (58, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-70, 0, 70)), (0.9, (30, 0, 55), "linear"), (1.5, (34, 0, 60)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 0, -70)), (0.9, (30, 0, -55), "linear"), (1.5, (34, 0, -60)), (2.2, (0, 0, 0)))
    a.rot("hair", (0, (0, 0, 0)), (0.8, (-8, 0, 0)), (0.9, (8, 0, 0), "linear"), (1.5, (12, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("hair_tip", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.9, (-6, 0, 0)), (1.5, (4, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("lock_r", (0, (0, 0, 0)), (0.9, (30, 0, 25)), (1.5, (35, 0, 30)), (2.2, (0, 0, 0)))
    a.rot("lock_l", (0, (0, 0, 0)), (0.9, (30, 0, -25)), (1.5, (35, 0, -30)), (2.2, (0, 0, 0)))
    a.rot("skirt3", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.5, (24, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.9, (25, 0, 0)), (1.5, (30, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("train", (0, (0, 0, 0)), (0.9, (30, 0, 0)), (1.5, (35, 0, 0)), (2.2, (0, 0, 0)))

    # claw: the right arm rises behind the head (telegraph), rakes down at 0.6 s (12 ticks)
    a = m.anim("claw", 1.3)
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, 1.5, 1.5)), (0.6, (0, 0, -3), "linear"), (0.85, (0, 0, -3)), (1.3, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-10, 28, 0)), (0.6, (14, -24, 0), "linear"), (0.85, (12, -20, 0)), (1.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-160, 0, 25)), (0.6, (-25, 0, -25), "linear"), (0.85, (-20, 0, -20)), (1.3, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (0.6, (0, 0, 0), "linear"), (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-30, 0, -40)), (0.6, (10, 0, -20)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-8, 15, 0)), (0.6, (10, -10, 0)), (1.3, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.6, (35, 0, 0)), (1.3, (0, 0, 0)))
    return m
