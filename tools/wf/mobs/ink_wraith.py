"""Ink Wraith (Spectre d'encre): the spilt ink of the Starfall Library risen into a shape, about 2 blocks tall, floating.

Silhouette idea: a scribe's ghost poured out of an inkwell. A hooded, legless shape of glossy black ink with a deep
blue-violet sheen, its robe trailing off into three ragged, dripping tails instead of legs. Under the hood it wears a
cracked parchment mask with two ink-blot eye holes that glow a cold starlight violet, ink running down from them like
tears. Torn pages are stuck to its chest, written over in a crabbed hand, and three loose pages circle it slowly. Its
arms are long and thin, the hands grey with old ink, each finger ending in a sharpened quill nib. It glides through
the bookshelves as if they were not there, throws splashes of blinding ink, and rakes with its nibs.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

INK = (22, 20, 34)
INK_L = (46, 42, 72)
INK_S = (78, 82, 140)
INK_D = (10, 9, 16)
PARCH = (226, 212, 172)
PARCH_D = (178, 156, 112)
PARCH_L = (244, 236, 210)
SCRAWL = (52, 44, 60)
HAND = (120, 118, 132)
HAND_D = (78, 76, 92)
NIB = (232, 226, 210)
EYE = (190, 168, 255)
EYE_L = (238, 230, 255)
GOLD = (196, 160, 72)


def ink(seed=0, drip=False):
    """Glossy ink: near-black with a blue-violet sheen streak running down each side, lighter where it catches the
    light at the top; ``drip``: the bottom rows run into ragged drips (transparent gaps)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return INK_D if not drip or (x + y + seed) % 2 else None
        if face == "top":
            return INK_L if (x + y + seed) % 5 == 0 else INK
        if drip and y >= h - 2 and K.h(x, seed) % 3 != 0:
            if y == h - 1 or K.h(x, seed) % 3 == 1:
                return None
        sheen = (x + K.h(y // 3, seed)) % 7 == 0
        c = INK_S if sheen and y < h - 1 else (INK_L if (x + seed) % 4 == 1 else INK)
        if K.h(x, y, seed) % 19 == 0:
            c = mix(c, INK_S, 0.5)
        return mul(c, 1.08 - 0.2 * y / max(1, h))
    return f


def page(seed=0):
    """A torn page: parchment written over in tight lines of scrawl, a burnt brown edge."""
    def f(face, x, y, w, h):
        if face in ("left", "right", "top", "bottom"):
            return PARCH_D
        if x in (0, w - 1) or y in (0, h - 1):
            return PARCH_D if K.h(x, y, seed) % 3 else (150, 120, 80)
        if y % 2 == 1 and K.h(x, y, seed) % 4:
            return SCRAWL
        return PARCH if (x + y) % 5 else PARCH_L
    return f


def build():
    m = Model("ink_wraith", seed=1223, shadow=0.45, walk_speed=0.8, walk_scale=0.6)

    # ------------------------------------------------------------------ skeleton: floating, tails instead of legs
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -17, 0), rot=(8, 0, 0))
    m.part("tail1", "body", pivot=(0, 0, 0.5))
    m.part("tail2", "tail1", pivot=(0, 5, 0.5), rot=(10, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 4.5, 0.5), rot=(12, 0, 0))
    m.part("head", "body", pivot=(0, -12, -0.5), rot=(-8, 0, 0))
    m.part("peak", "head", pivot=(0, -8, 2))
    m.part("arm_r", "body", pivot=(-5, -11, 0), rot=(-16, 0, 12))
    m.part("forearm_r", "arm_r", pivot=(0, 6.5, 0), rot=(-30, 0, 0))
    m.part("arm_l", "body", pivot=(5, -11, 0), rot=(-16, 0, -12))
    m.part("forearm_l", "arm_l", pivot=(0, 6.5, 0), rot=(-30, 0, 0))
    m.part("pages", "body", pivot=(0, -6, 0))
    for i in range(3):
        m.part(f"page{i}", "pages", pivot=(0, 0, 0), rot=(0, i * 120, 0))
    # the ink orb gathered for the splash: hidden at the chest until the throw
    m.part("orb", "body", pivot=(0, -7, -6), scale=(0.02, 0.02, 0.02))

    # ------------------------------------------------------------------ robe and tails
    m.box("body", -4, -12, -2.5, 8, 12, 5, ink(1))
    m.box("body", -4.5, -12.5, -3, 9, 3, 6, ink(2))                                          # shoulders of the robe
    m.box("body", -1, -11, -3.2, 2, 11, 1, {"*": INK_L, "front": lambda f_, x, y, w, h: GOLD if y % 4 == 1 else INK_L})
    # torn pages stuck to the chest
    m.box("body", -3.6, -10, -3.3, 3, 4, 1, page(3))
    m.box("body", 1.2, -8, -3.3, 2, 3, 1, page(4))
    m.box("body", 0.4, -4, 2.6, 3, 4, 1, page(5))
    m.box("tail1", -5, 0, -3.5, 10, 5, 7, ink(6, drip=True))
    m.box("tail2", -3.5, 0, -2.5, 7, 5, 5, ink(7, drip=True))
    m.box("tail3", -2, 0, -1.5, 4, 5, 3, ink(8, drip=True))
    m.box("tail3", -0.5, 4, -0.5, 1, 2, 1, INK_S)                                            # the last drop

    # ------------------------------------------------------------------ head: a hood, a cracked parchment mask
    m.box("head", -4, -8, -3.5, 8, 8, 7, ink(10))
    m.box("head", -4.5, -8.5, -4.5, 9, 2, 2, ink(11))                                        # hood rim over the brow
    m.box("head", -4.5, -7, -4.5, 1, 7, 2, ink(12))
    m.box("head", 3.5, -7, -4.5, 1, 7, 2, ink(13))
    eyes = {(1, 2), (2, 2), (1, 3), (4, 2), (5, 2), (4, 3), (5, 3)}

    def mask(f_, x, y, w, h):
        if f_ != "front":
            return PARCH_D
        if (x, y) in eyes:
            return EYE
        if y >= 4 and x in (1, 5) and K.h(x, y) % 2 == 0:
            return SCRAWL                                                                   # ink running like tears
        if (x, y) in {(3, 0), (3, 1), (2, 1), (3, 4), (4, 5)}:
            return PARCH_D                                                                  # the crack
        return PARCH if (x + y) % 4 else PARCH_L

    def mask_glow(f_, x, y, w, h):
        return (EYE_L if (x, y) in {(1, 2), (5, 2)} else EYE) if f_ == "front" and (x, y) in eyes else None
    m.box("head", -3.5, -7, -4, 7, 7, 1, mask, glow={"*": mask_glow})
    m.box("peak", -2, -2, -1, 4, 3, 5, ink(14))                                               # the hood's slumped peak
    m.box("peak", -1, -1, 4, 2, 2, 2, ink(15, drip=True))

    # ------------------------------------------------------------------ arms: thin sleeves, inky hands, quill nibs
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 8, 3, ink(20 + sx))
        m.box(fore, -1.5, -0.5, -1.5, 3, 3, 3, ink(22 + sx, drip=True), grow=0.2)          # ragged cuff
        m.box(fore, -1, 0, -1, 2, 6, 2, {"*": HAND, "front": HAND_D, "top": HAND_D})
        for k, fx in enumerate((-1, 0, 1)):
            m.box(fore, fx - 0.5, 6, -1, 1, 4, 1, lambda f_, x, y, w, h: NIB if y >= h - 1 else (SCRAWL if y == h - 2 else HAND_D))
    # the loose pages circling at chest height
    for i in range(3):
        m.box(f"page{i}", -1.5, -2 + i, -8.5, 3, 4, 1, page(30 + i))
    m.box("orb", -2.5, -2.5, -2.5, 5, 5, 5, {"*": lambda f_, x, y, w, h: INK_S if (x + y) % 3 == 0 else INK_L},
          glow={"*": lambda f_, x, y, w, h: EYE if (x + y) % 3 == 0 else (90, 80, 170)})

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0, loop=True)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, 1.2, 0)), (3.0, (0, 0, 0)))
    idle.rot("tail1", (0, (0, 0, 0)), (1.5, (8, 0, 4)), (3.0, (0, 0, 0)))
    idle.rot("tail2", (0, (0, 0, 0)), (1.0, (6, 0, -6)), (2.0, (12, 0, 6)), (3.0, (0, 0, 0)))
    idle.rot("tail3", (0, (0, 0, 0)), (0.7, (10, 0, 8)), (1.7, (16, 0, -8)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (0, 14, -6)), (2.0, (4, -10, 4)), (3.0, (0, 0, 0)))
    idle.rot("peak", (0, (0, 0, 0)), (1.5, (12, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-8, 0, 6)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-8, 0, -6)), (3.0, (0, 0, 0)))
    idle.rot("pages", (0, (0, 0, 0), "linear"), (1.0, (0, 120, 0), "linear"), (2.0, (0, 240, 0), "linear"),
             (3.0, (0, 360, 0), "linear"))
    for i in range(3):
        idle.pos(f"page{i}", (0, (0, 0, 0)), (0.5 + i * 0.8, (0, 1.2, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("body", (0, (12, 0, 0)), (0.8, (16, 0, 0)), (1.6, (12, 0, 0)))                   # leaning into the glide
    walk.rot("tail1", (0, (20, 0, 0)), (0.8, (26, 0, 4)), (1.6, (20, 0, 0)))
    walk.rot("tail2", (0, (20, 0, -6)), (0.8, (28, 0, 6)), (1.6, (20, 0, -6)))
    walk.rot("tail3", (0, (24, 0, 8)), (0.8, (34, 0, -8)), (1.6, (24, 0, 8)))
    walk.rot("arm_r", (0, (20, 0, 10)), (0.8, (26, 0, 14)), (1.6, (20, 0, 10)))
    walk.rot("arm_l", (0, (20, 0, -10)), (0.8, (26, 0, -14)), (1.6, (20, 0, -10)))
    walk.rot("head", (0, (-10, 0, 0)), (0.8, (-12, 0, 0)), (1.6, (-10, 0, 0)))

    # claw: the right hand drawn back high, nibs spread (0.4 s telegraph), then raked down across (lands at 0.4 s =
    # 8 ticks)
    a = m.anim("claw", 0.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (-150, -20, 30)), (0.4, (-154, -20, 32)), (0.5, (-30, 30, -10), "linear"),
          (0.65, (-24, 30, -10)), (0.9, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.35, (-40, 0, 0)), (0.5, (0, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (-8, 24, 0)), (0.5, (16, -20, 0), "linear"), (0.65, (14, -18, 0)), (0.9, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.35, (0, 1, 1.5)), (0.5, (0, -0.5, -3), "linear"), (0.65, (0, -0.5, -3)), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.35, (-10, -16, 0)), (0.5, (8, 10, 0)), (0.9, (0, 0, 0)))
    a.rot("tail1", (0, (0, 0, 0)), (0.35, (-14, 0, 0)), (0.5, (24, 0, 0)), (0.9, (0, 0, 0)))

    # splash: both hands cup together at the chest while the ink orb swells between them (0.7 s telegraph), then it is
    # flung forward (thrown at 0.7 s = 14 ticks)
    a = m.anim("splash", 1.3)
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.3, (-60, -30 * s, 10 * s)), (0.65, (-50, -36 * s, 10 * s)), (0.7, (-52, -36 * s, 10 * s)),
              (0.8, (-100, 10 * s, 6 * s), "linear"), (1.0, (-96, 10 * s, 6 * s)), (1.3, (0, 0, 0)))
        a.rot("fore" + arm, (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (0.7, (-56, 0, 0)), (0.8, (0, 0, 0), "linear"), (1.3, (0, 0, 0)))
    a.scale("orb", (0, (1, 1, 1)), (0.15, (1.3, 1.3, 1.3)), (0.6, (1.98, 1.98, 1.98)), (0.7, (2.1, 2.1, 2.1)), (0.74, (1, 1, 1), "linear"),
            (1.3, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-14, 0, 0)), (0.7, (-16, 0, 0)), (0.8, (20, 0, 0), "linear"), (1.0, (18, 0, 0)), (1.3, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 2, 2)), (0.8, (0, 0, -2), "linear"), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (0.8, (-6, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("tail2", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (0.8, (30, 0, 0)), (1.3, (0, 0, 0)))

    # dive: it melts into a bookshelf, shrinking into a puddle of ink (0.5 s), is gone while the ink bubbles out of
    # another shelf, and bursts out of it nibs first (strikes at 0.9 s = 18 ticks)
    a = m.anim("dive", 1.6)
    a.scale("body", (0, (1, 1, 1)), (0.2, (1.1, 0.9, 1.1)), (0.5, (0.05, 0.05, 0.05), "linear"), (0.8, (0.05, 0.05, 0.05)),
            (0.88, (1.15, 1.15, 1.15), "linear"), (1.0, (1, 1, 1)), (1.6, (1, 1, 1)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, -8, -4), "linear"), (0.8, (0, -2, 4)), (0.9, (0, 0, -3), "linear"), (1.1, (0, 0, -3)),
          (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (0.8, (30, 0, 0)), (0.9, (20, 0, 0)), (1.6, (0, 0, 0)))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.5, (-150, 0, 10 * s)), (0.85, (-120, 0, 30 * s)), (0.9, (-80, 0, 4 * s), "linear"),
              (1.1, (-76, 0, 4 * s)), (1.6, (0, 0, 0)))
    a.rot("tail1", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("tail2", (0, (0, 0, 0)), (0.9, (30, 0, 0)), (1.6, (0, 0, 0)))
