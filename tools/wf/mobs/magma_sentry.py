"""Magma-forged Sentry (Sentinelle forgée de magma): the halberdier of the Caldera Ringwall, about 2.4 blocks tall.

Silhouette idea: a watchman forged rather than born. A tall, narrow suit of blackstone plate riveted with dark iron,
hollow but for the molten heart that glows through a barred grille in its breastplate and through every seam. A tall
bucket great-helm with a single burning visor slit and a basalt crest, two short chimney vents on its shoulder plates
breathing sparks, heavy greaves and segmented tassets. It stands its post with a halberd held upright, taller than
itself: an iron haft bound with brass rings, a crescent axe-blade with a glowing forged edge, a long top spike and a
back hook. It keeps its distance and strikes from far: a long thrust, an overhead blow that splits the ground into a
line of fire, a shove with the haft for anyone who gets too close.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

STONE = (46, 42, 48)
STONE_L = (86, 80, 88)
STONE_D = (26, 24, 30)
IRON = (82, 78, 80)
IRON_L = (140, 134, 132)
IRON_D = (44, 40, 42)
MAGMA = (255, 118, 26)
MAGMA_L = (255, 222, 120)
MAGMA_D = (176, 52, 14)
BRASS = (190, 146, 62)
BRASS_D = (124, 88, 34)
SOOT = (34, 30, 30)


def seam(face, x, y, w, h, seed):
    """Glowing joints between the plates: a horizontal seam every few rows, broken now and then."""
    if face in ("top", "bottom") or h < 5 or w < 4:
        return False
    step = 4 + seed % 2
    if y % step == step - 1 and y < h - 1:
        return K.h(x // 3, y, seed) % 3 != 0
    # a short vertical crack climbing from a seam now and then
    cx = 1 + K.h(seed, face == "front", w) % max(1, w - 2)
    return x == cx and step <= y < step + 2 and h > 7


def plate(seed=0, seams=True):
    """Blackstone plate: chiselled facets, a lit top bevel, a dark rim, soot toward the bottom, glowing seams."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return STONE_D
        if face == "top":
            return STONE_L if x in (0, w - 1) or y in (0, h - 1) else mul(STONE, 1.15)
        if seams and seam(face, x, y, w, h, seed):
            return MAGMA_D
        if y == 0:
            return STONE_L
        if x in (0, w - 1):
            return STONE_D
        r = K.h(x, y, seed) % 100
        c = mul(STONE, 1.08 - 0.3 * y / max(1, h))
        if r < 14:
            c = mix(c, SOOT, 0.6)
        elif r > 94:
            c = STONE_L
        return c
    return f


def plate_glow(seed=0):
    def f(face, x, y, w, h):
        return MAGMA if seam(face, x, y, w, h, seed) else None
    return f


def iron(seed=0, rivets=True):
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        if face == "top":
            return mix(IRON, IRON_L, 0.3)
        if w > 2 and h > 2:
            if y == 0:
                return IRON_L
            if x in (0, w - 1) or y == h - 1:
                return IRON_D
            if rivets and y == 1 and x % 3 == 1:
                return BRASS
        c = mul(IRON, 1.05 - 0.2 * y / max(1, h))
        return mix(c, (120, 70, 40), 0.4) if K.h(x, y, seed) % 23 == 0 else c
    return f


def molten(seed=0):
    def f(face, x, y, w, h):
        r = K.h(x, y, seed) % 7
        return MAGMA_L if r == 0 else (MAGMA_D if r > 4 else MAGMA)
    return f


def build():
    m = Model("magma_sentry", seed=623, shadow=0.7, walk_speed=0.9, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2.8, -15, 0))
    m.part("shin_r", "leg_r", pivot=(0, 8, 0))
    m.part("leg_l", "bone", pivot=(2.8, -15, 0))
    m.part("shin_l", "leg_l", pivot=(0, 8, 0))
    m.part("body", "bone", pivot=(0, -15, 0))
    m.part("head", "body", pivot=(0, -14, -0.5))
    m.part("arm_r", "body", pivot=(-7, -12, 0), rot=(-10, 0, 4))
    m.part("forearm_r", "arm_r", pivot=(0, 6, 0), rot=(-50, 0, 0))
    m.part("halberd", "forearm_r", pivot=(0, 6.5, -0.5), rot=(58, 0, 0))
    m.part("arm_l", "body", pivot=(7, -12, 0), rot=(6, 0, -6))
    m.part("forearm_l", "arm_l", pivot=(0, 6, 0), rot=(-14, 0, 0))
    m.part("vent_r", "body", pivot=(-6, -15, 1), rot=(-8, 0, -14))
    m.part("vent_l", "body", pivot=(6, -15, 1), rot=(-8, 0, 14))
    m.part("tasset_f", "body", pivot=(0, 0, -3))
    m.part("tasset_b", "body", pivot=(0, 0, 3))

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, 0, -2.5, 5, 8, 5, plate(3 + sx), glow=plate_glow(3 + sx))
        m.box(leg, -3, 6, -3.5, 6, 3, 2, iron(5 + sx))                                    # knee cop
        m.box(shin, -2.5, 0, -2.5, 5, 5, 5, iron(6 + sx))
        m.box(shin, -2.2, 1, -2.8, 4, 3, 1, {"front": lambda f_, x, y, w, h: MAGMA if x in (1, 2) and y == 1 else IRON_D,
                                             "*": IRON_D}, glow={"front": lambda f_, x, y, w, h: MAGMA if x in (1, 2) and
                                                                y == 1 else None, "*": None})
        m.box(shin, -3, 5, -4, 6, 2, 6, plate(7 + sx, seams=False))                        # sabaton

    # ------------------------------------------------------------------ body: breastplate with the molten heart
    def chest(f_, x, y, w, h):
        if f_ == "front" and 2 <= x <= w - 3 and 2 <= y <= 6:
            return IRON_D if x % 2 == 0 or y in (2, 6) else molten(10)(f_, x, y, w, h)      # the grille
        return plate(11)(f_, x, y, w, h)

    def chest_glow(f_, x, y, w, h):
        if f_ == "front" and 3 <= x <= w - 4 and 3 <= y <= 5 and x % 2 == 1:
            return MAGMA_L if y == 4 else MAGMA
        return plate_glow(11)(f_, x, y, w, h)
    m.box("body", -5.5, -14, -3.5, 11, 11, 7, chest, glow=chest_glow)
    m.box("body", -4, -3.5, -2.5, 8, 4, 5, iron(12))                                       # waist
    m.box("body", -5, -4, -3, 10, 1, 6, {"*": BRASS_D, "front": lambda f_, x, y, w, h: BRASS if x % 3 else BRASS_D},
          grow=0.1)                                                                          # belt of brass rings
    m.box("body", -6, -14.5, -4, 12, 2, 8, plate(13, seams=False))                          # gorget ridge
    m.box("tasset_f", -4.5, 0, -0.5, 9, 5, 1, plate(14), glow=plate_glow(14))
    m.box("tasset_b", -4.5, 0, -0.5, 9, 5, 1, plate(15), glow=plate_glow(15))
    m.box("body", -5.5, 0, -2.5, 1, 4, 5, plate(16, seams=False))                          # side tassets
    m.box("body", 4.5, 0, -2.5, 1, 4, 5, plate(17, seams=False))

    # chimney vents on the shoulder plates
    for v in ("vent_r", "vent_l"):
        m.box(v, -1, -5, -1, 2, 5, 2, iron(20, rivets=False))
        m.box(v, -1.5, -6, -1.5, 3, 1, 3, {"top": MAGMA, "*": IRON_D}, glow={"top": MAGMA_L, "*": None})

    # ------------------------------------------------------------------ head: the bucket great-helm
    def helm(f_, x, y, w, h):
        if f_ == "front":
            if y == 4 and 1 <= x <= w - 2:
                return MAGMA_L if x in (2, w - 3) else MAGMA                                # the burning visor slit
            if y == 3 and 1 <= x <= w - 2:
                return IRON_D
            if x == w // 2 and y >= 5:
                return IRON_L                                                               # the face ridge
            if y >= 6 and x in (1, 2, w - 3, w - 2) and (x + y) % 2 == 0:
                return SOOT                                                                 # breathing holes
        return iron(30)(f_, x, y, w, h)
    m.box("head", -3.5, -8, -3.5, 7, 8, 7, helm,
          glow={"front": lambda f_, x, y, w, h: (MAGMA_L if x in (2, w - 3) else MAGMA) if y == 4 and 1 <= x <= w - 2 else None,
                "*": None})
    m.box("head", -4, -8.5, -4, 8, 1, 8, {"*": BRASS_D, "top": BRASS})                       # brass brim at the top
    m.box("head", -0.5, -11, -4.5, 1, 3, 9, {"top": MAGMA, "*": plate(31, seams=False)},
          glow={"top": MAGMA_L, "*": None})                                                  # basalt crest
    m.box("head", -0.5, -12, -2, 1, 1, 4, STONE_L)
    m.box("head", -4, -2, -3, 8, 2, 6, iron(32), grow=0.05)                                 # bevor round the chin

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -3.5, -2.5, -3.5, 7, 4, 7, plate(40 + sx), glow=plate_glow(40 + sx))    # pauldron
        m.box(arm, -3, 1.5, -3, 6, 1, 6, BRASS_D)
        m.box(arm, -2, 0, -2, 4, 6, 4, iron(41 + sx))
        m.box(fore, -2.3, 0, -2.3, 4, 5, 4, plate(42 + sx), glow=plate_glow(42 + sx), grow=0.3)  # gauntlet cuff
        m.box(fore, -2, 5, -2, 4, 3, 4, {"*": iron(43 + sx, rivets=False),
                                         "front": lambda f_, x, y, w, h: MAGMA if y == 1 and x % 2 == 0 else IRON},
              glow={"front": lambda f_, x, y, w, h: MAGMA if y == 1 and x % 2 == 0 else None, "*": None})

    # ------------------------------------------------------------------ the halberd (haft along -y from the fist)
    def haft(f_, x, y, w, h):
        if y % 9 == 0:
            return BRASS
        return IRON_D if (x + y) % 3 == 0 else IRON
    m.box("halberd", -0.5, -30, -0.5, 1, 45, 1, haft)
    m.box("halberd", -1, 13, -1, 2, 2, 2, iron(50, rivets=False))                            # butt cap
    m.box("halberd", -1, -31, -1, 2, 3, 2, iron(51, rivets=False))                           # socket
    m.box("halberd", -0.5, -38, -0.5, 1, 7, 1, {"*": IRON_L, "top": MAGMA_L}, glow={"top": MAGMA_L, "*": None})  # top spike

    def blade(f_, x, y, w, h):
        if f_ in ("left", "right"):
            return MAGMA_L if x == 0 else IRON_L
        if f_ == "front":
            return MAGMA
        return IRON_L if y == 0 else IRON
    blade_glow = {"front": MAGMA_L, "left": lambda f_, x, y, w, h: MAGMA if x == 0 else None,
                  "right": lambda f_, x, y, w, h: MAGMA if x == 0 else None, "*": None}
    # the crescent axe blade, forward of the haft (part -z), widest at the edge
    m.box("halberd", -0.5, -30, -3, 1, 4, 2, iron(52, rivets=False))
    m.box("halberd", -0.5, -32, -5, 1, 8, 2, blade, glow=blade_glow)
    m.box("halberd", -0.5, -33, -6, 1, 10, 1, blade, glow=blade_glow)
    m.box("halberd", -0.5, -34, -7, 1, 12, 1, blade, glow=blade_glow)
    # the back hook
    m.box("halberd", -0.5, -30, 1, 1, 2, 2, iron(53, rivets=False))
    m.box("halberd", -0.5, -29, 3, 1, 3, 1, {"*": IRON_L, "bottom": MAGMA}, glow={"bottom": MAGMA, "*": None})
    # a scorched pennant under the head
    m.box("halberd", 0, -27, 0.5, 0, 6, 4, {"left": lambda f_, x, y, w, h: None if y > 3 + x % 3 else (120, 30, 22) if
                                             (x + y) % 4 else (70, 18, 14),
                                             "right": lambda f_, x, y, w, h: None if y > 3 + (w - 1 - x) % 3 else (120, 30, 22)
                                             if (x + y) % 4 else (70, 18, 14), "*": None})

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.2)
    idle.pos("body", (0, (0, 0, 0)), (1.6, (0, -0.4, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (0, 14, 0)), (1.6, (0, 0, 0)), (2.4, (0, -14, 0)), (3.2, (0, 0, 0)))  # scanning
    idle.rot("vent_r", (0, (0, 0, 0)), (1.6, (0, 0, -4)), (3.2, (0, 0, 0)))
    idle.rot("vent_l", (0, (0, 0, 0)), (1.6, (0, 0, 4)), (3.2, (0, 0, 0)))
    idle.rot("tasset_f", (0, (0, 0, 0)), (1.6, (-3, 0, 0)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.6, (-22, 0, 0)), (1.2, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.6, (22, 0, 0)), (1.2, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.9, (28, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.3, (28, 0, 0)), (0.6, (0, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("arm_l", (0, (-16, 0, 0)), (0.6, (16, 0, 0)), (1.2, (-16, 0, 0)))
    walk.rot("arm_r", (0, (4, 0, 0)), (0.6, (-4, 0, 0)), (1.2, (4, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, -0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, -0.8, 0)), (1.2, (0, 0, 0)))
    walk.rot("tasset_f", (0, (-10, 0, 0)), (0.6, (6, 0, 0)), (1.2, (-10, 0, 0)))
    walk.rot("tasset_b", (0, (6, 0, 0)), (0.6, (-10, 0, 0)), (1.2, (6, 0, 0)))

    # thrust: the halberd levelled and drawn far back (0.75 s telegraph), then driven straight out (lands at 0.75 s
    # = 15 ticks; it reaches 4.5 blocks)
    a = m.anim("thrust", 1.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-60, 20, 0)), (0.75, (-80, -6, 0), "linear"), (1.05, (-80, -6, 0)), (1.4, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (0.75, (40, 0, 0), "linear"), (1.05, (40, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.6, (115, 0, 0)), (0.75, (128, 0, 0)), (1.05, (128, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-50, -30, 0)), (0.75, (-70, -10, 0), "linear"), (1.05, (-70, -10, 0)), (1.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (0, 30, 0)), (0.75, (10, -10, 0), "linear"), (1.05, (8, -10, 0)), (1.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, -0.5, 2.5)), (0.75, (0, -1, -3), "linear"), (1.05, (0, -1, -3)), (1.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (0.75, (-30, 0, 0)), (1.05, (-30, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (0.75, (24, 0, 0)), (1.05, (24, 0, 0)), (1.4, (0, 0, 0)))

    # slam: the halberd swung up over the helm and held (1.0 s telegraph), then brought down onto the ground in front
    # (lands at 1.0 s = 20 ticks: a line of fire runs out from the blade)
    a = m.anim("slam", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-170, 0, 6)), (1.0, (-175, 0, 6)), (1.12, (-60, 0, 0), "linear"), (1.4, (-55, 0, 0)),
          (1.7, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (1.12, (20, 0, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.8, (130, 0, 0)), (1.0, (130, 0, 0)), (1.12, (132, 0, 0), "linear"), (1.4, (132, 0, 0)),
          (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-160, 0, -10)), (1.12, (-60, 0, 0), "linear"), (1.4, (-55, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (1.12, (24, 0, 0), "linear"), (1.4, (20, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (1.12, (10, 0, 0)), (1.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.8, (0, 1, 1)), (1.12, (0, -2.5, -1.5), "linear"), (1.4, (0, -2.5, -1.5)), (1.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.12, (-20, 0, 0)), (1.4, (-20, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.12, (16, 0, 0)), (1.4, (16, 0, 0)), (1.7, (0, 0, 0)))

    # shove: a short jab with the butt of the haft for a foe in its face (lands at 0.3 s = 6 ticks)
    a = m.anim("shove", 0.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (20, 0, 0)), (0.3, (-40, 0, 0), "linear"), (0.45, (-36, 0, 0)), (0.7, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.2, (-20, 0, 0)), (0.3, (30, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (10, 0, 0)), (0.3, (-50, 0, 0), "linear"), (0.45, (-46, 0, 0)), (0.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (-6, 10, 0)), (0.3, (8, -6, 0), "linear"), (0.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.2, (0, 0, 1)), (0.3, (0, 0, -2), "linear"), (0.7, (0, 0, 0)))
