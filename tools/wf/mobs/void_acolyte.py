"""Void Acolyte (Acolyte du vide): the cultist of the Shattered Halo, about 1.9 blocks tall.

Silhouette idea: a priest of a broken heaven. A tall, thin figure in a long black-violet robe trimmed with tarnished
gold, the hem torn and lined with a faint void glow; the deep hood is empty but for a cracked white porcelain mask
with a single vertical violet eye-slit. Behind its head floats a broken gilded halo, a ring with a missing arc,
echoing the Shattered Halo itself, and three void shards drift round it. A curved ritual dagger in its right hand,
an orb of violet light hovering over its open left palm. It blinks a few blocks away (its arrival point flickers first),
throws glowing orbs and stabs whoever corners it.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

ROBE = (40, 28, 56)
ROBE_L = (72, 54, 96)
ROBE_D = (22, 14, 32)
GOLD = (206, 170, 84)
GOLD_L = (255, 228, 150)
GOLD_D = (130, 98, 40)
PORC = (232, 228, 236)
PORC_D = (172, 166, 182)
VOID = (190, 110, 255)
VOID_L = (248, 220, 255)
VOID_D = (100, 50, 160)
SKIN = (120, 104, 150)
SHARD = (60, 40, 90)


def robe(seed=0, trim=False, lining=False):
    """Heavy robe: soft folds, a sheen along the crests, gold trim down the front edges, a torn hem whose lowest row
    glows with the void lining."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return VOID_D if lining else ROBE_D
        if face == "top":
            return ROBE_L if (x + y) % 3 == 0 else ROBE
        if lining and y >= h - 1 - K.h(x, seed) % 2:
            if K.h(x, seed + 1) % 3 == 0:
                return None
            return VOID_D if y == h - 1 else mix(ROBE, VOID_D, 0.6)
        if trim and face == "front" and x in (w // 2 - 1, w // 2):
            return GOLD if y % 3 else GOLD_D
        k = (x + K.h(x // 3, seed)) % 4
        c = ROBE_D if k == 0 else (ROBE_L if k == 2 else ROBE)
        return mul(c, 1.06 - 0.2 * y / max(1, h))
    return f


def robe_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return VOID_D if face == "bottom" else None
        if y >= h - 1 - K.h(x, seed) % 2 and K.h(x, seed + 1) % 3 != 0:
            return VOID if y == h - 1 else None
        return None
    return f


def gilt(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return GOLD_L
        if face == "bottom":
            return GOLD_D
        return GOLD if (x + y + seed) % 3 else mix(GOLD, GOLD_L, 0.5)
    return f


def build():
    m = Model("void_acolyte", seed=661, shadow=0.5, walk_speed=1.0, walk_scale=1.0, glow_pulse=0.12)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-1.8, -11, 0))
    m.part("leg_l", "bone", pivot=(1.8, -11, 0))
    m.part("body", "bone", pivot=(0, -11, 0))
    m.part("skirt", "body", pivot=(0, 0, 0))
    m.part("head", "body", pivot=(0, -11.5, -0.3))
    m.part("halo", "head", pivot=(0, -5, 4.6), rot=(-8, 0, 0))
    m.part("arm_r", "body", pivot=(-4.5, -10, 0), rot=(-14, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 6, 0), rot=(-34, 0, 0))
    m.part("dagger", "forearm_r", pivot=(0, 6.5, -0.3), rot=(90, 0, 0))
    m.part("arm_l", "body", pivot=(4.5, -10, 0), rot=(-20, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 6, 0), rot=(-60, 0, 0))
    m.part("orb", "forearm_l", pivot=(0, 6.5, -3.5), rot=(80, 0, 0))
    m.part("shards", "body", pivot=(0, -8, 0))

    # ------------------------------------------------------------------ legs under the robe
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"
        m.box(leg, -1.5, 0, -1.5, 3, 10, 3, robe(2 + sx))
        m.box(leg, -1.5, 9, -2.5, 3, 2, 4, {"*": ROBE_D, "top": GOLD_D})                         # pointed slippers

    # ------------------------------------------------------------------ body
    m.box("body", -3.5, -11, -2, 7, 11, 4, robe(10, trim=True))
    m.box("body", -4, -11.5, -2.5, 8, 3, 5, {"*": gilt(11), "front": lambda f_, x, y, w, h: GOLD_L if y == 0 else
                                            (VOID if x == w // 2 and y == 1 else GOLD)},
          glow={"front": lambda f_, x, y, w, h: VOID if x == w // 2 and y == 1 else None, "*": None})  # gilded collar
    m.box("body", -3.8, -2, -2.3, 8, 1, 5, {"*": GOLD_D, "front": lambda f_, x, y, w, h: GOLD if x % 2 else GOLD_D},
          grow=0.05)                                                                                 # sash
    m.box("body", -1, -1, -2.6, 2, 5, 1, robe(12, trim=True))                                       # sash tail
    m.box("skirt", -4, 0, -2.5, 8, 10, 5, robe(13, trim=True, lining=True), glow=robe_glow(13))
    m.box("body", -3, -10, 1.8, 6, 9, 1, robe(14))                                                  # back panel

    # ------------------------------------------------------------------ head: the empty hood and the cracked mask
    def hood(f_, x, y, w, h):
        if f_ == "front" and 1 <= x <= w - 2 and y >= 1:
            return None
        if f_ == "bottom":
            return None
        return robe(20)(f_, x, y, w, h)
    m.box("head", -3.5, -7.5, -3.5, 7, 8, 7, hood)
    m.box("head", -3, -7, -3, 6, 7, 6, ROBE_D)                                                       # darkness inside
    m.box("head", -1, -9, -1, 2, 2, 3, robe(21))                                                     # hood peak

    def mask(f_, x, y, w, h):
        if f_ != "front":
            return PORC_D
        if x == w // 2 and 1 <= y <= h - 2:
            return VOID_L if y in (2, 3) else VOID                                                  # the eye slit
        if (x, y) in {(1, 1), (1, 2), (2, 3), (3, 4), (0, 4)}:
            return (90, 84, 100)                                                                    # a crack
        if y == h - 1 and x in (1, 3):
            return PORC_D
        return PORC if (x + y) % 4 else mix(PORC, PORC_D, 0.5)
    m.box("head", -2.5, -6.5, -3.7, 5, 6, 1, mask,
          glow={"front": lambda f_, x, y, w, h: (VOID_L if y in (2, 3) else VOID) if x == w // 2 and 1 <= y <= h - 2 else None,
                "*": None})

    # the broken halo: a ring of gilded segments round the back of the head, one arc missing
    r = 6.0
    for i in range(12):
        if i in (2, 3):
            continue                                                                                # the missing arc
        ang = math.radians(i * 30)
        cx, cy = round(math.cos(ang) * r * 2) / 2, round(math.sin(ang) * r * 2) / 2
        m.box("halo", cx - 1, cy - 1, -0.5, 2, 2, 1, gilt(30 + i),
              glow={"front": GOLD_L if i % 3 == 0 else None, "back": GOLD_L if i % 3 == 0 else None, "*": None})
    for i, (x, y) in enumerate(((3.5, -6.5), (5.5, -3.5))):                                         # chips drifting out
        m.box("halo", x, y, -0.5, 1, 1, 1, gilt(50 + i))

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 7, 3, robe(40 + sx))
        m.box(fore, -2, 0, -2, 4, 5, 4, robe(41 + sx))                                              # flared sleeve
        m.box(fore, -2.1, 4, -2.1, 4, 1, 4, GOLD, grow=0.1)                                           # gold cuff
        m.box(fore, -1, 5, -1, 2, 3, 2, K.skin(SKIN, 42 + sx))                                       # thin grey hand
    # the ritual dagger: a dark grip, a gold guard, a curved violet-black blade (along the part's -y once rotated)
    m.box("dagger", -0.5, -1, -0.5, 1, 3, 1, ROBE_D)
    m.box("dagger", -1.5, -2, -0.5, 3, 1, 1, gilt(60))
    m.box("dagger", -0.5, -6, -0.5, 1, 4, 1, {"*": SHARD, "front": VOID}, glow={"front": VOID, "*": None})
    m.box("dagger", -0.5, -8, 0.5, 1, 2, 1, {"*": SHARD, "front": VOID_L}, glow={"front": VOID_L, "*": None})  # the curve
    # the orb of void light over the left palm
    def orb(f_, x, y, w, h):
        return VOID_L if (x, y) == (1, 1) else (VOID if (x + y) % 2 else VOID_D)
    m.box("orb", -1.5, -1.5, -1.5, 3, 3, 3, orb, glow=lambda f_, x, y, w, h: VOID_L if (x, y) == (1, 1) else VOID)

    # three void shards drifting round the body
    for i, (x, y, z, hh) in enumerate(((-7, -2, -2, 3), (7, 1, 1, 4), (0, -5, 6, 2))):
        p = m.part(f"shard{i}", "shards", pivot=(x, y, z), rot=(20 * i, 30 * i, 15))
        m.box(p, -0.5, -hh / 2, -0.5, 1, hh, 1, {"*": SHARD, "front": VOID_D}, glow={"front": VOID, "top": VOID_L, "*": None})

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, -0.3, 0)), (4.0, (0, 0, 0)))
    idle.rot("halo", (0, (0, 0, 0)), (2.0, (0, 0, 180)), (4.0, (0, 0, 360)), )
    idle.rot("shards", (0, (0, 0, 0)), (2.0, (0, -180, 0)), (4.0, (0, -360, 0)))
    for i in range(3):
        idle.pos(f"shard{i}", (0, (0, 0, 0)), (1.0 + i * 0.5, (0, 1.2, 0)), (4.0, (0, 0, 0)))
    idle.pos("orb", (0, (0, 0, 0)), (1.0, (0, 0.6, 0)), (2.0, (0, 0, 0)), (3.0, (0, 0.6, 0)), (4.0, (0, 0, 0)))
    idle.rot("orb", (0, (0, 0, 0)), (4.0, (0, 360, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (0, 0, 8)), (4.0, (0, 0, 0)))                          # a slow tilt of the mask

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (16, 0, 0)), (0.6, (-16, 0, 0)), (1.2, (16, 0, 0)))
    walk.rot("leg_l", (0, (-16, 0, 0)), (0.6, (16, 0, 0)), (1.2, (-16, 0, 0)))
    walk.rot("skirt", (0, (5, 0, 2)), (0.6, (5, 0, -2)), (1.2, (5, 0, 2)))
    walk.rot("arm_r", (0, (-8, 0, 0)), (0.6, (8, 0, 0)), (1.2, (-8, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.4, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.4, 0)), (1.2, (0, 0, 0)))

    # cast: the orb drawn in to the chest and fed (0.7 s telegraph, it swells), then the open palm thrust out (the orb
    # flies at 0.7 s = 14 ticks)
    a = m.anim("cast", 1.1)
    a.rot("arm_l", (0, (0, 0, 0)), (0.55, (-40, 30, 0)), (0.7, (-44, 30, 0)), (0.8, (-90, -10, 0), "linear"), (0.95, (-88, -10, 0)),
          (1.1, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.55, (-60, 0, 0)), (0.8, (0, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.scale("orb", (0, (1, 1, 1)), (0.6, (1.9, 1.9, 1.9)), (0.7, (2.1, 2.1, 2.1)), (0.75, (0.1, 0.1, 0.1), "linear"),
            (0.95, (0.1, 0.1, 0.1)), (1.1, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.55, (-6, -20, 0)), (0.8, (8, 16, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-10, 0, 0)), (0.8, (4, 0, 0)), (1.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (10, 0, 20)), (0.8, (14, 0, 16)), (1.1, (0, 0, 0)))
    a.rot("halo", (0, (0, 0, 0)), (0.7, (0, 0, -120)), (1.1, (0, 0, -180)))

    # blink: it folds into itself with a twist and is gone (it moves at 0.45 s = 9 ticks)
    a = m.anim("blink", 0.5)
    a.scale("bone", (0, (1, 1, 1)), (0.2, (1.15, 0.85, 1.15)), (0.45, (0.05, 1.4, 0.05)), (0.5, (0.05, 1.4, 0.05)))
    a.rot("bone", (0, (0, 0, 0)), (0.45, (0, 160, 0)), (0.5, (0, 180, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (-20, 0, 60)), (0.5, (0, 0, 10)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (-20, 0, -60)), (0.5, (0, 0, -10)))

    # reform: it unfolds where it landed (0.4 s)
    a = m.anim("reform", 0.4)
    a.scale("bone", (0, (0.05, 1.4, 0.05)), (0.25, (1.15, 0.9, 1.15)), (0.4, (1, 1, 1)))
    a.rot("bone", (0, (0, -180, 0)), (0.25, (0, 10, 0)), (0.4, (0, 0, 0)))

    # stab: the dagger drawn back to the hip, then a quick upward stab (lands at 0.3 s = 6 ticks)
    a = m.anim("stab", 0.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (30, 0, 10)), (0.3, (-90, 0, -10), "linear"), (0.45, (-86, 0, -10)), (0.7, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.2, (-60, 0, 0)), (0.3, (10, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (-4, 24, 0)), (0.3, (10, -16, 0), "linear"), (0.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.2, (0, 0, 1)), (0.3, (0, -0.5, -2.5), "linear"), (0.7, (0, 0, 0)))
