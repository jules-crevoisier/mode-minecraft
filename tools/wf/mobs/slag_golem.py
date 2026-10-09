"""Slag Golem (Golem de scories): the waste of the Forge of the Basalt Titan walking on its own, about 2.4 blocks tall.

Silhouette idea: a heap of cooled slag and basalt that the titan's forge poured out and never stopped glowing inside.
A hunched, top-heavy brute with no neck: a huge barrel chest of dark basalt columns split by glowing orange seams,
two lumpy shoulder masses crusted with rust-brown slag, a small sunken head under a heavy brow with two ember eyes and
a molten slot of a mouth. Its arms hang to the ground and end in enormous fists of still-molten slag, black crust
plates floating on white-hot rock, dripping. Short stumpy legs on wide flat feet. It moves slowly, slams its molten
fists, and every blow leaves a puddle of cooling slag on the floor.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

BASALT = (58, 56, 64)
BASALT_L = (92, 90, 98)
BASALT_D = (34, 32, 40)
CRUST = (122, 74, 44)
CRUST_D = (78, 44, 28)
CRUST_L = (160, 104, 62)
CHAR = (30, 24, 24)
CHAR_L = (56, 44, 40)
HOT = (255, 120, 24)
HOT_L = (255, 214, 96)
HOT_W = (255, 246, 196)
HOT_D = (196, 58, 12)
EYE = (255, 176, 40)


def crack(x, y, w, h, seed):
    """True on a glowing seam: a few zigzag cracks running down the face, branching now and then."""
    if w < 3:
        return False
    for c in range(1, w - 1):
        if K.h(c, seed) % 7 != 0 or c % 3 == 0 and w < 8:
            continue
        wig = (K.h(c, y // 2, seed) % 3) - 1
        if x == c + wig:
            return True
        if y % 6 == 3 and x == c + wig + 1 and K.h(c, y, seed) % 2 == 0:       # a short branch
            return True
    return y > 1 and K.h(x, y, seed, 7) % 131 == 0                             # a lone glowing pore


def basalt(seed=0, crust=0.12, cracks=True):
    """Basalt columns (vertical striations, a lit top) split by glowing seams, with blotches of rusty slag crust."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BASALT_D
        if face == "top":
            c = BASALT_L if (x + y) % 4 == 0 else BASALT
            if K.h(x // 2, y // 2, seed) % 100 < crust * 100:
                c = CRUST if (x + y) % 3 else CRUST_L
            return c
        if cracks and crack(x, y, w, h, seed):
            return CHAR
        c = (BASALT, BASALT_D, BASALT_L, BASALT)[(x + K.h(x // 2, seed)) % 4]
        c = mul(c, 1.06 - 0.16 * y / max(1, h))
        if K.h(x // 2, y // 2, seed + 3) % 100 < crust * 100:
            c = mix(CRUST, CRUST_D, (x + y) % 2 * 0.6)
        return c
    return f


def basalt_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if crack(x, y, w, h, seed):
            return HOT_L if K.h(x, y, seed) % 3 == 0 else HOT
        return None
    return f


def molten(seed=0, crust=0.42):
    """Still-molten slag: white-hot rock under floating black crust plates edged in red."""
    def f(face, x, y, w, h):
        r = K.h(x // 3, (y + x // 3) // 3, seed, {"top": 1, "bottom": 2}.get(face, 3)) % 100
        if r < crust * 100:
            return CHAR_L if (x + y) % 3 == 0 else CHAR
        if r < crust * 100 + 10:
            return HOT_D
        return HOT_L if K.h(x, y, seed) % 7 == 0 else HOT
    return f


def molten_glow(seed=0, crust=0.42):
    def f(face, x, y, w, h):
        r = K.h(x // 3, (y + x // 3) // 3, seed, {"top": 1, "bottom": 2}.get(face, 3)) % 100
        if r < crust * 100:
            return None
        if r < crust * 100 + 10:
            return HOT_D
        return HOT_W if K.h(x, y, seed) % 5 == 0 else HOT_L
    return f


def drip(face, x, y, w, h):
    return HOT_L if y < h - 1 else HOT_W


def build():
    m = Model("slag_golem", seed=1201, shadow=0.95, walk_speed=0.6, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton: hunched, arms to the ground
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-4.5, -11, 0))
    m.part("shin_r", "leg_r", pivot=(0, 6, 0))
    m.part("leg_l", "bone", pivot=(4.5, -11, 0))
    m.part("shin_l", "leg_l", pivot=(0, 6, 0))
    m.part("body", "bone", pivot=(0, -11, 1), rot=(16, 0, 0))
    m.part("head", "body", pivot=(0, -16, -5), rot=(-14, 0, 0))
    m.part("jaw", "head", pivot=(0, -1, -1))
    m.part("arm_r", "body", pivot=(-8.5, -14, 0), rot=(-14, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(-1, 8, 0), rot=(-12, 0, 0))
    m.part("fist_r", "forearm_r", pivot=(0, 8, 0))
    m.part("arm_l", "body", pivot=(8.5, -14, 0), rot=(-14, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(1, 8, 0), rot=(-12, 0, 0))
    m.part("fist_l", "forearm_l", pivot=(0, 8, 0))
    # a gobbet of slag torn off the shoulder for the lob: hidden in the left fist until the throw
    m.part("glob", "fist_l", pivot=(0, 3, -1), scale=(0.02, 0.02, 0.02))

    # ------------------------------------------------------------------ legs: stumps of stacked basalt, flat feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3, -1, -3, 6, 7, 6, basalt(2 + sx), glow=basalt_glow(2 + sx))
        m.box(shin, -3.5, 0, -3.5, 7, 4, 7, basalt(4 + sx, crust=0.3), glow=basalt_glow(4 + sx))
        m.box(shin, -4, 4, -5, 8, 1, 9, {"top": BASALT_L, "*": BASALT_D})                   # flat foot
        for k in range(3):
            m.box(shin, -3.5 + k * 2.5, 3.5, -5.5, 2, 1, 1, CHAR_L)                           # stubby toes
        m.box(leg, -1.5 * -sx - 1, 1, -3.4, 2, 2, 1, CRUST_L)                                   # a slag knob

    # ------------------------------------------------------------------ body: a barrel chest of basalt columns
    m.box("body", -7, -16, -4.5, 14, 16, 9, basalt(10), glow=basalt_glow(10))
    m.box("body", -6, -2, -4, 12, 3, 8, basalt(11, crust=0.4), glow=basalt_glow(11))         # the gut, sagging
    # the furnace heart showing through a split in the chest
    m.box("body", -2, -12, -5, 4, 5, 1, molten(12, crust=0.2), glow=molten_glow(12, crust=0.2))
    m.box("body", -3, -13, -4.9, 6, 1, 1, CHAR_L)
    m.box("body", -3, -7, -4.9, 6, 1, 1, CHAR_L)
    # lumpy shoulder masses crusted with slag, and a ridge of basalt columns along the back
    for sx in (-1, 1):
        m.box("body", -8.5 if sx < 0 else 2.5, -18, -5, 6, 5, 10, basalt(13 + sx, crust=0.5), glow=basalt_glow(13 + sx))
        m.box("body", -9 if sx < 0 else 5, -16, -2, 4, 3, 5, basalt(15 + sx, crust=0.7, cracks=False))
    for i, (x, hgt) in enumerate(((-4.5, 4), (-1.5, 6), (1.5, 5), (4, 3))):
        m.box("body", x, -16 - hgt, 2, 2, hgt, 2, basalt(20 + i, crust=0.1), glow=basalt_glow(20 + i))
    # slag icicles hanging off the gut
    for i, x in enumerate((-4.5, -1, 2.5)):
        m.box("body", x, 1, -3.5, 1, 1 + i % 2, 1, drip, glow=drip)

    # ------------------------------------------------------------------ head: sunk between the shoulders
    def face(f_, x, y, w, h):
        if y == 2 and x in (1, 4):
            return EYE
        if y == 1 and 0 <= x <= 5:
            return BASALT_D                                                                   # under the brow
        return basalt(30, crust=0.1, cracks=False)(f_, x, y, w, h)

    def face_glow(f_, x, y, w, h):
        return HOT_W if y == 2 and x in (1, 4) else None
    m.box("head", -3, -5, -4, 6, 5, 6, {"front": face, "*": basalt(31, crust=0.2)},
          glow={"front": face_glow, "*": None})
    m.box("head", -3.5, -6, -4.5, 7, 2, 3, basalt(32, crust=0.3, cracks=False))                # heavy brow
    m.box("jaw", -2.5, 0, -3.5, 5, 2, 4, {"top": HOT, "front": lambda f_, x, y, w, h: HOT if y == 0 and 0 < x < w - 1
                                         else BASALT_D, "*": BASALT_D},
          glow={"top": HOT_L, "front": lambda f_, x, y, w, h: HOT_L if y == 0 and 0 < x < w - 1 else None, "*": None})

    # ------------------------------------------------------------------ arms: columns of basalt, molten fists
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, fist = f"arm_{side}", f"forearm_{side}", f"fist_{side}"
        m.box(arm, -3 + sx * 0.5, -2, -3, 5, 10, 6, basalt(40 + sx, crust=0.25), glow=basalt_glow(40 + sx))
        m.box(fore, -3, 0, -3.5, 6, 8, 7, basalt(42 + sx, crust=0.35), glow=basalt_glow(42 + sx))
        m.box(fore, -3.5, 5, -4, 7, 3, 8, molten(44 + sx, crust=0.6), glow=molten_glow(44 + sx, crust=0.6))   # cooling wrist
        m.box(fist, -4, 0, -4.5, 8, 7, 8, molten(46 + sx), glow=molten_glow(46 + sx))
        # knuckle plates of black crust and drips of slag under the fist
        for k in range(3):
            m.box(fist, -3.5 + k * 2.5, 1, -5.2, 2, 2, 1, {"*": CHAR, "front": CHAR_L})
        m.box(fist, -1 + sx * 2, 7, -2, 1, 2, 1, drip, glow=drip)
        m.box(fist, 1 - sx * 2, 7, 1, 1, 1, 1, drip, glow=drip)
    m.box("glob", -2, -2, -2, 4, 4, 4, molten(50, crust=0.25), glow=molten_glow(50, crust=0.25))

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.6)
    idle.pos("body", (0, (0, 0, 0)), (1.8, (0, -0.6, 0)), (3.6, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.8, (3, 0, 0)), (3.6, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (4, 12, 0)), (2.4, (0, -10, 0)), (3.6, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.8, (10, 0, 0)), (3.6, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.8, (4, 0, 2)), (3.6, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.8, (4, 0, -2)), (3.6, (0, 0, 0)))
    idle.rot("fist_r", (0, (0, 0, 0)), (0.9, (0, 0, 6)), (2.7, (0, 0, -4)), (3.6, (0, 0, 0)))
    idle.rot("fist_l", (0, (0, 0, 0)), (0.9, (0, 0, -6)), (2.7, (0, 0, 4)), (3.6, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    walk.rot("leg_r", (0, (20, 0, 0)), (0.9, (-20, 0, 0)), (1.8, (20, 0, 0)))
    walk.rot("leg_l", (0, (-20, 0, 0)), (0.9, (20, 0, 0)), (1.8, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.45, (0, 0, 0)), (1.35, (24, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.45, (24, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("body", (0, (0, 6, 6)), (0.9, (0, -6, -6)), (1.8, (0, 6, 6)))                     # a heavy shoulder roll
    walk.pos("body", (0, (0, 0, 0)), (0.45, (0, 1.0, 0)), (0.9, (0, 0, 0)), (1.35, (0, 1.0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_r", (0, (-14, 0, 0)), (0.9, (14, 0, 0)), (1.8, (-14, 0, 0)))
    walk.rot("arm_l", (0, (14, 0, 0)), (0.9, (-14, 0, 0)), (1.8, (14, 0, 0)))
    walk.rot("head", (0, (0, -5, 0)), (0.9, (0, 5, 0)), (1.8, (0, -5, 0)))

    # punch: the right fist dragged back past the hip, the shoulder wound up (0.6 s telegraph, the fist flaring), then
    # a haymaker straight ahead (lands at 0.6 s = 12 ticks)
    a = m.anim("punch", 1.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (40, 0, 20)), (0.6, (-90, 0, 0), "linear"), (0.75, (-86, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (-50, 0, 0)), (0.6, (0, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (-6, 30, 0)), (0.6, (12, -20, 0), "linear"), (0.75, (10, -18, 0)), (1.2, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, 0, 1.5)), (0.6, (0, -1, -3), "linear"), (0.75, (0, -1, -3)), (1.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-30, 0, -10)), (0.6, (20, 0, -10)), (1.2, (0, 0, 0)))
    a.scale("fist_r", (0, (1, 1, 1)), (0.5, (1.18, 1.18, 1.18)), (0.6, (1.1, 1.1, 1.1)), (1.0, (1, 1, 1)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (0.6, (-16, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.5, (-10, 0, 0)), (0.6, (18, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (0.7, (10, 0, 0)), (1.2, (0, 0, 0)))

    # slam: both fists heaved up over the head, the body arching back (0.9 s telegraph), then brought down together
    # onto the floor (lands at 0.9 s = 18 ticks): a splash of slag
    a = m.anim("slam", 1.7)
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.7, (-170, 0, -14 * s)), (0.85, (-178, 0, -12 * s)), (0.9, (-40, 0, -6 * s), "linear"),
              (1.15, (-40, 0, -6 * s)), (1.7, (0, 0, 0)))
    for fore in ("forearm_r", "forearm_l"):
        a.rot(fore, (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (0.9, (-10, 0, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.7, (-22, 0, 0)), (0.85, (-24, 0, 0)), (0.9, (34, 0, 0), "linear"), (1.15, (32, 0, 0)),
          (1.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.7, (0, 1.5, 1)), (0.9, (0, -3, -2), "linear"), (1.15, (0, -3, -2)), (1.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-20, 0, 0)), (0.9, (14, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.7, (30, 0, 0)), (0.95, (14, 0, 0)), (1.7, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.7, (-8, 0, 6 * s)), (0.9, (-30, 0, 12 * s), "linear"), (1.15, (-30, 0, 12 * s)),
              (1.7, (0, 0, 0)))
        a.rot("shin_" + leg[-1], (0, (0, 0, 0)), (0.9, (40, 0, 0), "linear"), (1.15, (40, 0, 0)), (1.7, (0, 0, 0)))
    a.scale("fist_r", (0, (1, 1, 1)), (0.85, (1.15, 1.15, 1.15)), (1.1, (1, 1, 1)))
    a.scale("fist_l", (0, (1, 1, 1)), (0.85, (1.15, 1.15, 1.15)), (1.1, (1, 1, 1)))

    # lob: the left hand claws a gobbet of slag off the right shoulder (0.35 s), swings it back overhead (0.8 s
    # telegraph: the gobbet swells in the fist), then hurls it overhand (released at 0.8 s = 16 ticks)
    a = m.anim("lob", 1.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-80, 40, 50)), (0.4, (-80, 40, 50)), (0.7, (-200, 0, -10)), (0.8, (-208, 0, -10)),
          (0.92, (-60, 0, -6), "linear"), (1.05, (-50, 0, -6)), (1.4, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (0.7, (-60, 0, 0)), (0.92, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.scale("glob", (0, (1, 1, 1)), (0.3, (1, 1, 1)), (0.4, (1.6, 1.6, 1.6)), (0.78, (1.98, 1.98, 1.98)), (0.8, (1.98, 1.98, 1.98)),
            (0.82, (1, 1, 1), "linear"), (1.4, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (6, 20, 0)), (0.7, (-16, -24, 0)), (0.8, (-18, -26, 0)), (0.92, (20, 18, 0), "linear"),
          (1.05, (18, 16, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 10)), (0.7, (-40, 0, 30)), (0.92, (20, 0, 10)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (10, -30, 0)), (0.7, (-14, 10, 0)), (0.92, (6, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (16, 0, 0)), (0.92, (-20, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (-12, 0, 0)), (0.92, (16, 0, 0)), (1.4, (0, 0, 0)))
