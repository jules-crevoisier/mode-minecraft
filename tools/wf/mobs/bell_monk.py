"""Bell Monk (Moine des cloches): the silent pilgrim-warden of Pilgrim's Ascent, about 1.95 blocks tall.

Silhouette idea: a gaunt bell-ringer who took a vow of silence and lets his bells speak for him. A tall thin monk in
a heavy weathered habit of ash-grey wool with a long dark scapular embroidered with a bronze bell, a rope girdle with
a hanging prayer scroll, a deep cowl over a pale gaunt face: his eyes are bound with a strip of cloth marked with a
glowing sigil and his lips are sewn shut. A wooden yoke rests across his shoulders with a small bronze bell hanging
from each end; in his right hand a big bronze handbell, prayer beads wound round his left. Bare feet in rag wraps.
He rings a ring of sound along the ground (jump over it), swings the handbell at close range and lifts it high for a
deafening knell.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

WOOL = (124, 118, 108)
WOOL_D = (78, 74, 68)
DARK = (58, 50, 52)
DARK_D = (36, 30, 32)
SKIN = (206, 186, 168)
SKIN_D = (150, 128, 112)
BRONZE = (196, 138, 58)
BRONZE_L = (248, 204, 120)
BRONZE_D = (120, 76, 30)
VERDI = (92, 156, 132)
WOOD = (110, 78, 48)
WOOD_D = (70, 48, 30)
ROPE = (176, 150, 100)
ROPE_D = (126, 104, 66)
SIGIL = (255, 214, 120)
SIGIL_L = (255, 246, 200)
CLOTH = (214, 204, 182)


def bronze(seed=0, verdigris=0.08):
    """Cast bronze: a bright rim of light, darker toward the mouth, verdigris freckles."""
    def f(face, x, y, w, h):
        if face == "top":
            return BRONZE_L
        if face == "bottom":
            return BRONZE_D
        c = mul(BRONZE, 1.15 - 0.35 * y / max(1, h))
        if x == w // 3:
            c = mix(c, BRONZE_L, 0.5)
        if K.h(x, y, seed) % 1000 / 1000 < verdigris:
            c = VERDI
        return c
    return f


def bell_mouth_glow():
    return {"bottom": lambda f_, x, y, w, h: SIGIL if 0 < x < w - 1 and 0 < y < h - 1 else None, "*": None}


def build():
    m = Model("bell_monk", seed=653, shadow=0.5, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -11, 0))
    m.part("leg_l", "bone", pivot=(2, -11, 0))
    m.part("body", "bone", pivot=(0, -11, 0), rot=(6, 0, 0))
    m.part("skirt", "body", pivot=(0, 0, 0))
    m.part("head", "body", pivot=(0, -12, -0.5), rot=(4, 0, 0))
    m.part("yoke", "body", pivot=(0, -11.5, 1.2))
    m.part("bell_yr", "yoke", pivot=(-9.5, 1, 0))
    m.part("bell_yl", "yoke", pivot=(9.5, 1, 0))
    m.part("arm_r", "body", pivot=(-5, -10.5, 0), rot=(-8, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 6, 0), rot=(-58, 0, 0))
    m.part("handbell", "forearm_r", pivot=(0, 6.5, -0.3), rot=(62, 0, 0))
    m.part("clapper", "handbell", pivot=(0, 2, 0))
    m.part("arm_l", "body", pivot=(5, -10.5, 0), rot=(-30, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 6, 0), rot=(-50, 0, 0))
    m.part("beads", "forearm_l", pivot=(0, 6.5, 0), rot=(50, 0, 0))
    m.part("scroll", "body", pivot=(2.5, -1, -2.6), rot=(0, 0, -6))

    # ------------------------------------------------------------------ legs: thin legs under the hem, rag-wrapped feet
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"
        m.box(leg, -1.5, 0, -1.5, 3, 10, 3, K.cloth(WOOL_D, mul(WOOL_D, 0.75), seed=2 + sx))
        m.box(leg, -1.5, 8, -1.5, 3, 2, 3, {"*": lambda f_, x, y, w, h: CLOTH if (x + y) % 2 else mul(CLOTH, 0.8)})  # wraps
        m.box(leg, -1.5, 10, -3, 3, 1, 4, SKIN_D)                                                # bare toes

    # ------------------------------------------------------------------ body: habit, scapular, girdle, skirt
    m.box("body", -4, -11, -2, 8, 11, 4, K.cloth(WOOL, WOOL_D, seed=10))

    def scapular(f_, x, y, w, h):
        if f_ != "front":
            return DARK_D
        bell = {(2, 3), (1, 4), (2, 4), (3, 4), (1, 5), (2, 5), (3, 5), (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (2, 7)}
        if (x, y) in bell:
            return BRONZE if y < 7 else BRONZE_L                                                 # the embroidered bell
        if x in (0, w - 1):
            return mix(DARK, BRONZE_D, 0.4)
        return DARK if (x + y) % 5 else DARK_D
    m.box("body", -2.5, -10.5, -2.4, 5, 19, 1, scapular)                                          # down to the shins
    m.box("body", -4.5, -1.5, -2.5, 9, 1, 5, {"*": ROPE_D, "front": lambda f_, x, y, w, h: ROPE if x % 2 else ROPE_D},
          grow=0.1)                                                                                # rope girdle
    m.box("body", -2.6, -0.5, -2.8, 1, 5, 1, ROPE)                                                # girdle knot ends
    m.box("body", -1.6, -0.5, -2.8, 1, 4, 1, ROPE_D)

    def hem(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return WOOL_D
        if y == h - 1 and K.h(x, 11) % 3 == 0:
            return None
        return K.cloth(WOOL, WOOL_D, seed=11)(f_, x, y, w, h)
    m.box("skirt", -4.5, 0, -2.5, 9, 9, 5, hem)
    m.box("scroll", -1, 0, -0.5, 2, 4, 1, {"front": lambda f_, x, y, w, h: CLOTH if y % 2 else mul(CLOTH, 0.82),
                                           "*": mul(CLOTH, 0.85)})
    m.box("scroll", -1.2, -0.5, -0.7, 2, 1, 1, (150, 40, 34))                                    # wax seal

    # ------------------------------------------------------------------ head: gaunt face, blindfold, sewn lips, cowl
    def face(f_, x, y, w, h):
        if y in (2, 3):
            if y == 2 and x in (1, 2, 4, 5):
                return SIGIL if x in (2, 4) else mix(CLOTH, SIGIL, 0.3)                          # the sigil on the cloth
            return CLOTH if (x + y) % 2 else mul(CLOTH, 0.88)                                   # blindfold
        if y == 5 and 1 <= x <= 5:
            return (60, 30, 30) if x % 2 else SKIN_D                                            # the stitched lips
        if y == 4 and x in (0, 6) or y == 5 and x in (0, 6):
            return mul(SKIN_D, 0.85)                                                             # hollow cheeks
        return SKIN if y > 0 else mul(SKIN, 0.75)
    m.box("head", -3.5, -7, -3.5, 7, 7, 7, {"front": face, "*": K.skin(SKIN_D, 20)},
          glow={"front": lambda f_, x, y, w, h: (SIGIL_L if x in (2, 4) else SIGIL) if y == 2 and x in (1, 2, 4, 5) else None,
                "*": None})

    def cowl(f_, x, y, w, h):
        if f_ == "front" and 1 <= x <= w - 2 and 1 <= y:
            return None
        if f_ == "bottom":
            return None
        return K.cloth(WOOL, WOOL_D, seed=21)(f_, x, y, w, h)
    m.box("head", -4, -7.8, -4.2, 8, 8, 8, cowl)
    m.box("head", -3, -8.8, -3, 6, 1, 6, K.cloth(WOOL, WOOL_D, seed=24))                         # rounded crown
    m.box("head", -1.5, -7, 3.8, 3, 7, 2, K.cloth(WOOL_D, mul(WOOL_D, 0.75), seed=22))            # cowl tail behind
    m.box("head", -5, 0, -3.5, 10, 2, 8, K.cloth(WOOL, WOOL_D, seed=23))                         # cowl folds on the shoulders

    # ------------------------------------------------------------------ the yoke and its two bells
    m.box("yoke", -10, -1, -1, 20, 2, 2, K.wood(WOOD, WOOD_D, seed=30, vertical=False))
    m.box("yoke", -10.5, -1.5, -1.5, 1, 3, 3, WOOD_D)
    m.box("yoke", 9.5, -1.5, -1.5, 1, 3, 3, WOOD_D)
    for b in ("bell_yr", "bell_yl"):
        m.box(b, -0.5, 0, -0.5, 1, 2, 1, ROPE)
        m.box(b, -1.5, 2, -1.5, 3, 3, 3, bronze(31))
        m.box(b, -2, 4.5, -2, 4, 1, 4, bronze(32), glow=bell_mouth_glow())

    # ------------------------------------------------------------------ arms: wide sleeves
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2, -1, -2, 4, 7, 4, K.cloth(WOOL, WOOL_D, seed=40 + sx))
        m.box(fore, -2.5, 0, -2.5, 5, 5, 5, K.cloth(WOOL, WOOL_D, seed=41 + sx, hem=DARK))       # the wide sleeve
        m.box(fore, -1.5, 4.5, -1.5, 3, 2, 3, K.skin(SKIN, 42 + sx))                            # bony hand

    # the handbell: a wooden handle up through the fist, the bronze bell below, a clapper inside
    m.box("handbell", -0.5, -3.5, -0.5, 1, 4, 1, K.wood(WOOD, WOOD_D, seed=50))
    m.box("handbell", -1, -4.5, -1, 2, 1, 2, BRONZE_D)
    m.box("handbell", -1.5, 0.5, -1.5, 3, 2, 3, bronze(51))
    m.box("handbell", -2, 2.5, -2, 4, 2, 4, bronze(52))
    m.box("handbell", -2.5, 4.5, -2.5, 5, 1, 5, bronze(53), glow=bell_mouth_glow())
    m.box("clapper", -0.5, 0, -0.5, 1, 3, 1, BRONZE_D)
    m.box("clapper", -1, 3, -1, 2, 1, 2, BRONZE_D)

    # prayer beads hanging from the left hand
    for k in range(4):
        m.box("beads", -0.5, k * 1.5, -0.5, 1, 1, 1, (90, 40, 30) if k % 2 else (130, 60, 40))
    m.box("beads", -1, 6, -0.5, 2, 2, 1, BRONZE)                                                 # a little bronze bell charm

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, -0.3, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (4, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("handbell", (0, (0, 0, 0)), (1.0, (6, 0, 4)), (2.0, (-4, 0, -4)), (3.0, (0, 0, 0)))
    idle.rot("clapper", (0, (0, 0, 0)), (1.0, (10, 0, 6)), (2.0, (-8, 0, -6)), (3.0, (0, 0, 0)))
    idle.rot("bell_yr", (0, (0, 0, 0)), (1.5, (6, 0, 4)), (3.0, (0, 0, 0)))
    idle.rot("bell_yl", (0, (0, 0, 0)), (1.5, (-6, 0, -4)), (3.0, (0, 0, 0)))
    idle.rot("beads", (0, (0, 0, 0)), (1.5, (8, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (18, 0, 0)), (0.6, (-18, 0, 0)), (1.2, (18, 0, 0)))
    walk.rot("leg_l", (0, (-18, 0, 0)), (0.6, (18, 0, 0)), (1.2, (-18, 0, 0)))
    walk.rot("skirt", (0, (4, 0, 2)), (0.6, (4, 0, -2)), (1.2, (4, 0, 2)))
    walk.rot("arm_r", (0, (-10, 0, 0)), (0.6, (10, 0, 0)), (1.2, (-10, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.5, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.5, 0)), (1.2, (0, 0, 0)))
    walk.rot("bell_yr", (0, (14, 0, 6)), (0.6, (-10, 0, -6)), (1.2, (14, 0, 6)))
    walk.rot("bell_yl", (0, (-10, 0, -6)), (0.6, (14, 0, 6)), (1.2, (-10, 0, -6)))
    walk.rot("handbell", (0, (14, 0, 0)), (0.6, (-14, 0, 0)), (1.2, (14, 0, 0)))
    walk.rot("clapper", (0, (-20, 0, 0)), (0.6, (20, 0, 0)), (1.2, (-20, 0, 0)))

    # wave: the handbell raised high and held trembling (0.9 s telegraph), then swung down hard: the ring of sound goes
    # out along the ground (rung at 0.9 s = 18 ticks)
    a = m.anim("wave", 1.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-160, 0, 20)), (0.75, (-165, 0, 18)), (0.85, (-160, 0, 22)), (0.9, (-165, 0, 20)),
          (1.0, (-50, 0, 10), "linear"), (1.2, (-45, 0, 10)), (1.5, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (1.0, (20, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("handbell", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (0.9, (-20, 0, 0)), (1.0, (30, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("clapper", (0, (0, 0, 0)), (0.7, (20, 0, 0)), (0.8, (-20, 0, 0)), (0.9, (20, 0, 0)), (1.0, (-40, 0, 0)),
          (1.2, (30, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-12, 10, 0)), (0.9, (-14, 10, 0)), (1.0, (16, -6, 0), "linear"), (1.2, (14, -6, 0)),
          (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-24, 0, 0)), (1.0, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (10, 0, -30)), (1.0, (20, 0, -20)), (1.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (1.0, (0, -1.5, -1), "linear"), (1.2, (0, -1.5, -1)), (1.5, (0, 0, 0)))

    # bash: a backhand swing of the heavy handbell at close range (lands at 0.3 s = 6 ticks)
    a = m.anim("bash", 0.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (-70, 0, 60)), (0.3, (-80, 0, -40), "linear"), (0.45, (-70, 0, -40)), (0.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (0, 30, 0)), (0.3, (6, -30, 0), "linear"), (0.45, (6, -26, 0)), (0.7, (0, 0, 0)))
    a.rot("handbell", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (0.3, (40, 0, 0)), (0.7, (0, 0, 0)))
    a.rot("clapper", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (0.45, (30, 0, 0)), (0.7, (0, 0, 0)))

    # knell: both hands lift the handbell over the cowl and shake it ever harder (1.2 s telegraph), then the knell
    # (tolled at 1.2 s = 24 ticks: darkness and a push for everyone around)
    a = m.anim("knell", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-170, 0, -14)), (1.2, (-172, 0, -14)), (1.3, (-150, 0, -10)), (1.7, (-150, 0, -10)),
          (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-150, 0, 26)), (1.2, (-155, 0, 26)), (1.3, (-140, 0, 20)), (1.7, (-140, 0, 20)),
          (2.0, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (1.7, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("handbell", (0, (0, 0, 0)), (0.7, (-20, 0, 0)), (0.85, (-20, 0, 14)), (0.95, (-20, 0, -14)), (1.05, (-20, 0, 18)),
          (1.15, (-20, 0, -18)), (1.2, (-20, 0, 0)), (1.3, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("clapper", (0, (0, 0, 0)), (0.9, (0, 0, 30)), (1.0, (0, 0, -30)), (1.1, (0, 0, 30)), (1.2, (0, 0, -40)),
          (1.4, (0, 0, 20)), (2.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.7, (-16, 0, 0)), (1.2, (-18, 0, 0)), (1.3, (-8, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (1.2, (-34, 0, 0)), (1.7, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.7, (0, 1.5, 0)), (1.2, (0, 2, 0)), (1.3, (0, 0, 0)), (2.0, (0, 0, 0)))
    for b, s in (("bell_yr", 1), ("bell_yl", -1)):
        a.rot(b, (0, (0, 0, 0)), (1.2, (0, 0, 10 * s)), (1.3, (30, 0, -30 * s)), (1.6, (-20, 0, 20 * s)), (2.0, (0, 0, 0)))
