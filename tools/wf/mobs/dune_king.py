"""The Dune King (Le Roi des dunes): the undead pharaoh-king of the Necropolis of Kings, about 4.6 blocks tall
(5.2 with the crown).

Silhouette idea: a gaunt mummy king under a towering double crown (the white bulb rising out of the red crown with
its tall back and gold curl), shoulders squared by a broad lapis-and-gold collar, a crook held upright like a
sceptre in the right hand and a beaded flail hanging from the left. Four canopic jars with animal-head lids orbit
around him at chest height, and his sunken eyes burn turquoise. Asymmetry: a loose bandage streams from the left
forearm, the right shoulder wears a gold pauldron shaped like a vulture wing.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

WRAP = (206, 188, 146)
WRAP_L = (232, 218, 182)
WRAP_D = (150, 128, 92)
GOLD = (232, 186, 70)
GOLD_L = (255, 226, 130)
GOLD_D = (164, 118, 36)
LAPIS = (40, 72, 166)
LAPIS_D = (24, 42, 104)
TURQ = (64, 224, 208)
TURQ_L = (190, 255, 246)
RED = (170, 46, 36)
RED_D = (112, 28, 24)
WHITE = (236, 230, 214)
SKIN = (92, 70, 52)
ALABASTER = (226, 214, 190)


def wraps(seed=0, gilt=0.0):
    """Mummy wrappings: diagonal strips with dark seams, stains, and (gilt > 0) strips of gold leaf."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return WRAP_D
        if face == "top":
            return WRAP_L
        row = y + (x // 4 + seed) % 3                 # staggered horizontal strips, 3 texels wide
        k = row % 3
        if k == 0:
            return mul(WRAP_D, 0.95)
        strip = row // 3 * 7 + x // 4
        if gilt and B.n(strip, 0, seed) < gilt:
            return GOLD_L if k == 1 else GOLD
        c = WRAP_L if k == 1 else WRAP
        if B.n(strip, 1, seed + 3) < 0.15:
            c = mul(c, 0.86)                          # an older, stained strip
        return mul(c, 1.04 - 0.12 * y / max(1, h))
    return f


def gold(seed=0, lapis_every=0):
    """Polished gold with a lit top edge; optional lapis inlay stripes every ``lapis_every`` rows."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        if face == "top":
            return GOLD_L
        if lapis_every and y % lapis_every == lapis_every - 1:
            return LAPIS if (x + y) % 4 else LAPIS_D
        if y == 0:
            return GOLD_L
        return mul(GOLD, 1.08 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def stripes(a, b, seed=0, every=2):
    """Vertical stripes of two colours (the nemes-like beard, crook bands)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return a
        c = a if (y // every) % 2 == 0 else b
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def collar_paint(f, x, y, w, h):
    """The usekh collar: concentric rows of lapis, gold and turquoise beads."""
    if f == "bottom":
        return GOLD_D
    row = y if f != "top" else (min(y, h - 1 - y, x, w - 1 - x))
    pal = (GOLD_L, LAPIS, GOLD, TURQ, GOLD, LAPIS_D)
    c = pal[row % len(pal)]
    if c in (LAPIS, TURQ) and (x % 2):
        c = mul(c, 0.82)
    return c


def face_paint(f, x, y, w, h):
    """The mummy face: dark leathery skin between wrappings, sunken turquoise eyes, a gold mask band on the brow."""
    if f in ("top", "bottom"):
        return wraps(40)(f, x, y, w, h)
    if f != "front":
        return wraps(41)(f, x, y, w, h)
    if y in (0, 1):
        return GOLD if y == 0 else GOLD_D
    if y == 4 and x in (1, 2, w - 3, w - 2):
        return TURQ_L if x in (2, w - 3) else TURQ
    if y in (3, 5) and x in (1, 2, 3, w - 4, w - 3, w - 2):
        return mul(SKIN, 0.5)
    if 3 <= y <= 7 and 2 < x < w - 3:
        return mul(SKIN, 0.9 + 0.2 * B.n(x, y, 42))
    if y >= 8 and x % 2 == 0 and 2 <= x <= w - 3:
        return mul(SKIN, 0.55)                                 # the grin
    return wraps(43)(f, x, y, w, h)


def eye_glow(f, x, y, w, h):
    if f == "front" and y == 4 and x in (1, 2, w - 3, w - 2):
        return TURQ_L if x in (2, w - 3) else TURQ
    return None


def white_crown(f, x, y, w, h):
    if f == "bottom":
        return mul(WHITE, 0.7)
    return mul(WHITE, 1.04 - 0.15 * y / max(1, h) + (B.n(x, y, 50) - 0.5) * 0.05)


def red_crown(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return RED_D
        if face == "top":
            return mul(RED, 1.1)
        if y == h - 1:
            return GOLD
        return mul(RED, 1.05 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def kilt_paint(f, x, y, w, h):
    """The royal kilt: pleated white linen with a gold hem."""
    if f in ("top", "bottom"):
        return mul(WHITE, 0.8)
    if y >= h - 2:
        return GOLD if y == h - 2 else GOLD_D
    return mul(WHITE, 0.92 if x % 2 else 1.02) if B.n(x, y, 55) > 0.1 else mul(WRAP, 0.9)


def apron_paint(f, x, y, w, h):
    """The front apron: gold with lapis chevrons and a turquoise scarab."""
    if f != "front":
        return gold(56)(f, x, y, w, h)
    cx = (w - 1) / 2
    if 2 <= y <= 4 and abs(x - cx) < 2:
        return TURQ
    if (y + int(abs(x - cx))) % 3 == 0 and y > 5:
        return LAPIS
    return gold(57)(f, x, y, w, h)


def jar_paint(f, x, y, w, h):
    """A canopic jar: alabaster with a column of turquoise hieroglyphs."""
    if f == "bottom":
        return mul(ALABASTER, 0.7)
    if f == "top":
        return ALABASTER
    if x == w // 2 and y % 2 == 1:
        return TURQ
    return mul(ALABASTER, 1.04 - 0.2 * y / max(1, h) + (B.n(x, y, 60) - 0.5) * 0.06)


def jar_glow(f, x, y, w, h):
    if f not in ("top", "bottom") and x == w // 2 and y % 2 == 1:
        return TURQ
    return None


def build():
    m = Model("dune_king", seed=151, shadow=1.6, walk_speed=0.8, walk_scale=0.9)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -30, 0))
    m.part("waist", "pelvis", pivot=(0, -3, 0))
    m.part("chest", "waist", pivot=(0, -5, 0), rot=(4, 0, 0))
    m.part("head", "chest", pivot=(0, -19, -1), rot=(-4, 0, 0))
    m.part("crown", "head", pivot=(0, -10, 0), rot=(-6, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(4 * sx, 0, 0))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 15, 0))
    m.part("arm_r", "chest", pivot=(-11, -16, 0), rot=(-6, 0, 24))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-60, 0, 0))
    m.part("crook", "fore_r", pivot=(0, 12, -1), rot=(64, 0, -22))
    m.part("arm_l", "chest", pivot=(11, -16, 0), rot=(-4, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-30, 0, 4))
    m.part("ribbon", "fore_l", pivot=(3, 4, 2), rot=(20, 0, -20))
    m.part("flail", "fore_l", pivot=(0, 12, -1), rot=(30, 0, 0))
    m.part("strands", "flail", pivot=(0, -9, -2))
    # the orbiting canopic jars: a ring at chest height turning slowly round him
    m.part("jars", "bone", pivot=(0, -44, 0))
    lids = ((GOLD, "human"), ((40, 36, 34), "jackal"), ((150, 110, 70), "baboon"), ((120, 90, 60), "falcon"))
    for k, (lid, kind) in enumerate(lids):
        a = math.pi / 4 + k * math.pi / 2
        m.part(f"jar_{k}", "jars", pivot=(round(20 * math.cos(a)), 0, round(20 * math.sin(a))))

    # ---- legs: thin wrapped legs, gold anklets, bare wrapped feet
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -3, -1, -3, 6, 16, 6, wraps(2 + (sx > 0)))
        m.box(sh, -2.5, 0, -2.5, 5, 13, 5, wraps(4 + (sx > 0)))
        m.box(sh, -3, 9, -3, 6, 2, 6, gold(6))                                   # anklet
        m.box(sh, -3, 13, -5, 6, 2, 8, wraps(7))                                 # foot

    # ---- pelvis: belt, pleated kilt, gold apron
    m.box("pelvis", -7, -3, -4, 14, 5, 8, gold(10, lapis_every=3))
    m.box("pelvis", -8, 1, -5, 16, 12, 10, kilt_paint)
    m.box("pelvis", -3, 1, -6, 6, 14, 1, apron_paint)

    # ---- waist and chest: wrapped ribs under gilded strips, the broad collar, a vulture-wing pauldron
    m.box("waist", -6, -5, -3.5, 12, 6, 7, wraps(12, gilt=0.3))
    m.box("chest", -9, -19, -5, 18, 19, 10, wraps(13, gilt=0.25))
    m.box("chest", -11, -20, -6, 22, 5, 12, collar_paint)                        # the usekh collar
    m.box("chest", -9, -15, -6.5, 18, 3, 1, collar_paint)                        # its front drop
    m.box("chest", -2, -12, -5.6, 4, 4, 1, B.lens(TURQ, GOLD, TURQ_L), glow=B.lens_glow(TURQ, TURQ_L))  # amulet
    m.box("chest", -7, -18, 5, 14, 12, 1, gold(14, lapis_every=4))               # back plate

    # ---- head: wrapped skull, gold brow, turquoise eyes, striped false beard, the double crown with the uraeus
    m.box("head", -4.5, -10, -4.5, 9, 10, 9, face_paint, glow=eye_glow)
    m.box("head", -1, 0, -5, 2, 5, 2, stripes(GOLD, LAPIS, 15))                 # false beard
    m.box("head", -5, -9, -2, 1, 8, 6, stripes(GOLD, LAPIS, 16))                # lappets
    m.box("head", 4, -9, -2, 1, 8, 6, stripes(GOLD, LAPIS, 17))
    m.box("crown", -5, -5, -5, 10, 5, 10, red_crown(18))                         # the red crown
    m.box("crown", -5, -15, 2, 10, 11, 3, red_crown(19))                         # its tall back
    m.box("crown", -3, -16, -3, 6, 11, 6, white_crown)                           # the white bulb
    m.box("crown", -2, -19, -2, 4, 3, 4, white_crown)
    m.box("crown", -1, -20, -1, 2, 1, 2, GOLD_L)                                  # knob
    m.box("crown", 3, -9, -4, 1, 5, 1, GOLD)                                      # the curl of the red crown
    m.box("crown", 3, -10, -6, 1, 1, 3, GOLD)
    m.box("crown", -1, -7, -6, 2, 4, 1, gold(20), glow={"front": lambda f, x, y, w, h: TURQ if y == 0 else None})  # uraeus

    # ---- right arm: vulture-wing pauldron, wrapped arm, gold bracer, the crook
    m.box("arm_r", -6, -4, -5, 9, 5, 10, gold(22, lapis_every=2))
    m.box("arm_r", -7, 0, -5.5, 4, 4, 11, gold(23, lapis_every=2))                # wing tips
    m.box("arm_r", -2.5, 0, -2.5, 5, 12, 5, wraps(24))
    m.box("fore_r", -2.5, 0, -2.5, 5, 11, 5, wraps(25, gilt=0.4))
    m.box("fore_r", -3, 2, -3, 6, 5, 6, gold(26, lapis_every=2))                  # bracer
    m.box("fore_r", -2.5, 11, -2.5, 5, 3, 5, mul(SKIN, 0.9))                       # hand
    m.box("crook", -1, -30, -1, 2, 42, 2, stripes(GOLD, LAPIS, 27, every=3))       # shaft
    m.box("crook", -1.5, -33, -1.5, 3, 3, 3, gold(28))
    m.box("crook", -2, -36, -1, 8, 3, 2, gold(29))                                 # the hook
    m.box("crook", 4, -35, -1, 3, 7, 2, stripes(GOLD, LAPIS, 30))
    m.box("crook", 3, -28, -1, 2, 2, 2, GOLD_L)

    # ---- left arm: wrapped arm with a loose bandage streaming off it, the flail
    m.box("arm_l", -2.5, -3, -3, 6, 4, 6, gold(32, lapis_every=2))
    m.box("arm_l", -2.5, 0, -2.5, 5, 12, 5, wraps(33))
    m.box("fore_l", -2.5, 0, -2.5, 5, 11, 5, wraps(34, gilt=0.4))
    m.box("fore_l", -3, 2, -3, 6, 5, 6, gold(35, lapis_every=2))
    m.box("fore_l", -2.5, 11, -2.5, 5, 3, 5, mul(SKIN, 0.9))
    m.box("ribbon", 0, 0, 0, 2, 16, 0, {"*": wraps(36), "front": wraps(36), "back": wraps(37)})
    m.box("flail", -1, -8, -1, 2, 12, 2, stripes(GOLD, LAPIS, 38, every=2))       # handle (held in the fist)
    m.box("flail", -1.5, -10, -1.5, 3, 2, 3, GOLD_L)
    for k, dx in enumerate((-2, 0, 2)):
        for j in range(5):
            m.box("strands", dx - 1, j * 3, -1, 2, 3, 2,
                  (LAPIS if j % 2 else GOLD) if k != 1 else (GOLD if j % 2 else TURQ))

    # ---- canopic jars: alabaster body, rim, an animal-head lid
    for k, (lid, kind) in enumerate(lids):
        j = f"jar_{k}"
        m.box(j, -2.5, -3, -2.5, 5, 7, 5, jar_paint, glow=jar_glow)
        m.box(j, -2, 4, -2, 4, 1, 4, mul(ALABASTER, 0.8))
        m.box(j, -3, -4, -3, 6, 1, 6, GOLD)
        m.box(j, -2, -7, -2, 4, 3, 4, lid, glow={"front": lambda f, x, y, w, h: TURQ if y == 1 and x in (0, w - 1) else None})
        if kind == "jackal":
            m.box(j, -2, -9, 0, 1, 2, 1, lid)
            m.box(j, 1, -9, 0, 1, 2, 1, lid)
            m.box(j, -1, -6, -4, 2, 2, 2, lid)
        elif kind == "falcon":
            m.box(j, -0.5, -6, -3, 1, 2, 1, GOLD)
        elif kind == "baboon":
            m.box(j, -1.5, -6, -3, 3, 2, 1, mul(lid, 0.8))
        else:
            m.box(j, -2.5, -7, -1, 1, 4, 3, stripes(GOLD, LAPIS, 61))
            m.box(j, 1.5, -7, -1, 1, 4, 3, stripes(GOLD, LAPIS, 62))

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 6.0)
    idle.rot("jars", (0, (0, 0, 0), "linear"), (6.0, (0, 360, 0), "linear"))
    for k in range(4):
        s = 1 if k % 2 else -1
        idle.pos(f"jar_{k}", (0, (0, 0, 0)), (1.5, (0, 1.6 * s, 0)), (3.0, (0, 0, 0)), (4.5, (0, -1.6 * s, 0)),
                 (6.0, (0, 0, 0)))
    idle.pos("chest", (0, (0, 0, 0)), (3.0, (0, 0.6, 0)), (6.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (0, 8, 0)), (3.0, (0, 8, 0)), (4.5, (0, -6, 0)), (6.0, (0, 0, 0)))
    idle.rot("ribbon", (0, (0, 0, 0)), (1.5, (14, 0, 8)), (3.0, (0, 0, 0)), (4.5, (10, 0, -6)), (6.0, (0, 0, 0)))
    idle.rot("strands", (0, (0, 0, 0)), (3.0, (6, 0, 4)), (6.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("thigh_r", (0, (18, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("thigh_l", (0, (-18, 0, 0)), (1.0, (18, 0, 0)), (2.0, (-18, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (22, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (22, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("arm_l", (0, (8, 0, 0)), (1.0, (-8, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("strands", (0, (10, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("chest", (0, (0, -3, 0)), (1.0, (0, 3, 0)), (2.0, (0, -3, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -0.8, 0)), (1.0, (0, 0, 0)), (1.5, (0, -0.8, 0)), (2.0, (0, 0, 0)))
    walk.rot("ribbon", (0, (20, 0, 0)), (1.0, (34, 0, 0)), (2.0, (20, 0, 0)))

    # flail: the flail raised behind his shoulder (0.7 s = 14 ticks), then three lashes (0.7, 1.2, 1.7 s)
    a = m.anim("flail", 2.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-150, 0, -30)), (0.7, (-155, 0, -32)), (0.78, (-40, 0, -6), "linear"),
          (1.1, (-120, 0, 20)), (1.2, (-125, 0, 22)), (1.28, (-30, 0, 30), "linear"), (1.6, (-150, 0, -10)),
          (1.7, (-160, 0, -10)), (1.8, (-20, 0, -4), "linear"), (2.0, (-24, 0, -4)), (2.4, (0, 0, 0)))
    a.rot("strands", (0, (0, 0, 0)), (0.7, (60, 0, 0)), (0.78, (-80, 0, 0), "linear"), (1.2, (60, 0, 20)),
          (1.28, (-80, 0, -20), "linear"), (1.7, (70, 0, 0)), (1.8, (-90, 0, 0), "linear"), (2.0, (-20, 0, 0)),
          (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-10, 24, 0)), (0.78, (12, -14, 0), "linear"), (1.2, (-6, -20, 0)),
          (1.28, (10, 18, 0), "linear"), (1.7, (-12, 20, 0)), (1.8, (16, -10, 0), "linear"), (2.0, (14, -8, 0)),
          (2.4, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (1.8, (-24, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.8, (20, 0, 0)), (2.4, (0, 0, 0)))

    # hook: the crook levelled and drawn back (0.8 s = 16 ticks), then it shoots out and hooks back toward him
    a = m.anim("hook", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-40, 30, 20)), (0.8, (-42, 32, 22)), (0.86, (-100, -6, 0), "linear"),
          (1.0, (-96, -6, 0)), (1.2, (-40, 10, 10)), (1.7, (0, 0, 0)))
    a.rot("crook", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (0.86, (-70, 0, 0), "linear"), (1.0, (-70, 0, 0)),
          (1.2, (-20, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, -26, 0)), (0.86, (10, 18, 0), "linear"), (1.0, (10, 18, 0)),
          (1.2, (-4, -10, 0)), (1.7, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (0.86, (-26, 0, 0), "linear"), (1.2, (-10, 0, 0)), (1.7, (0, 0, 0)))

    # sandstorm: both arms swept up, gathering the sand (1.0 s = 20 ticks), then thrust forward for 1.5 s of storm
    a = m.anim("sandstorm", 3.1)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.9, (-140, 0, -40 * sx)), (1.0, (-145, 0, -42 * sx)),
              (1.1, (-88, 0, 10 * sx), "linear"), (2.5, (-84, 0, 8 * sx)), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.1, (14, 0, 0), "linear"), (2.5, (12, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.1, (6, 0, 0), "linear"), (2.5, (6, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("jars", (0, (0, 0, 0)), (1.0, (0, 200, 0)), (2.5, (0, 720, 0)), (3.1, (0, 720, 0)))
    a.rot("ribbon", (0, (0, 0, 0)), (1.1, (60, 0, 0)), (2.5, (70, 0, 10)), (3.1, (0, 0, 0)))

    # summon: crook and flail crossed high over the crown (1.0 s = 20 ticks), then the crook butt struck on the floor
    a = m.anim("summon", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-160, 0, -20)), (1.0, (-165, 0, -22)), (1.08, (-30, 0, 4), "linear"),
          (1.5, (-30, 0, 4)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-160, 0, 20)), (1.0, (-165, 0, 22)), (1.08, (-50, 0, -30), "linear"),
          (1.5, (-50, 0, -30)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (1.08, (18, 0, 0), "linear"), (1.5, (16, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-26, 0, 0)), (1.08, (10, 0, 0), "linear"), (2.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.08, (0, -2.5, 0), "linear"), (1.5, (0, -2, 0)), (2.0, (0, 0, 0)))

    # jars: the crook pointed at the foe (0.7 s = 14 ticks), the jars spin faster and spit four curse bolts
    a = m.anim("jars", 2.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-80, 10, 0)), (0.7, (-84, 10, 0)), (2.0, (-84, 10, 0)), (2.5, (0, 0, 0)))
    a.rot("crook", (0, (0, 0, 0)), (0.7, (-60, 0, 0)), (2.0, (-60, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("jars", (0, (0, 0, 0)), (0.7, (0, 90, 0)), (2.0, (0, 450, 0)), (2.5, (0, 360, 0)))
    a.pos("jars", (0, (0, 0, 0)), (0.7, (0, 6, 0)), (2.0, (0, 6, 0)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-8, 0, 0)), (2.0, (-8, 0, 0)), (2.5, (0, 0, 0)))
    for k in range(4):
        t = 0.7 + k * 0.3
        a.scale(f"jar_{k}", (0, (1, 1, 1)), (t - 0.1, (1.25, 1.25, 1.25)), (t, (0.85, 0.85, 0.85), "linear"),
                (t + 0.2, (1, 1, 1)), (2.5, (1, 1, 1)))

    # quicksand (phase 2): palms turned down to the floor, he sinks the sand around him (1.0 s = 20 ticks), and pools of
    # quicksand open across the arena while he keeps the arms spread
    a = m.anim("quicksand", 3.7)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.9, (-30, 0, -70 * sx)), (1.0, (-30, 0, -72 * sx)),
              (1.1, (10, 0, -40 * sx), "linear"), (3.0, (10, 0, -40 * sx)), (3.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.1, (20, 0, 0), "linear"), (3.0, (18, 0, 0)), (3.7, (0, 0, 0)))
    a.pos("jars", (0, (0, 0, 0)), (1.0, (0, 10, 0)), (1.1, (0, -10, 0), "linear"), (3.0, (0, -8, 0)), (3.7, (0, 0, 0)))
    a.rot("jars", (0, (0, 0, 0)), (1.1, (0, 90, 0)), (3.0, (0, 540, 0)), (3.7, (0, 720, 0)))

    # scarabs (phase 2): the flail raised high (0.8 s = 16 ticks) and cracked on the floor; a swarm rolls out
    a = m.anim("scarabs", 2.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-170, 0, 10)), (0.8, (-172, 0, 10)), (0.88, (-30, 0, 0), "linear"),
          (2.3, (-30, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("strands", (0, (0, 0, 0)), (0.8, (80, 0, 0)), (0.88, (-60, 0, 0), "linear"), (2.3, (-40, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-14, 10, 0)), (0.88, (24, -6, 0), "linear"), (2.3, (20, -4, 0)), (2.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (0.88, (10, 0, 0), "linear"), (2.9, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.88, (0, -2, 0), "linear"), (2.3, (0, -2, 0)), (2.9, (0, 0, 0)))

    # judgement (phase 2): the crook held out level, eyes blazing (1.2 s = 24 ticks), then a beam sweeps from his left
    # to his right across the arena for 2.5 s while his whole body turns with it
    a = m.anim("judgement", 4.5)
    a.rot("arm_r", (0, (0, 0, 0)), (1.1, (-88, 0, 0)), (1.2, (-90, 0, 0)), (3.7, (-90, 0, 0)), (4.5, (0, 0, 0)))
    a.rot("crook", (0, (0, 0, 0)), (1.2, (-90, 0, 0)), (3.7, (-90, 0, 0)), (4.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.2, (-30, 0, -40)), (3.7, (-30, 0, -40)), (4.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 70, 0)), (1.2, (-8, 72, 0)), (3.7, (-8, -72, 0), "linear"),
          (4.5, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (1.2, (0, 18, 0)), (3.7, (0, -18, 0), "linear"), (4.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-10, 0, 0)), (3.7, (-10, 0, 0)), (4.5, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.2, (0, 3, 0)), (3.7, (0, 3, 0)), (4.5, (0, 0, 0)))

    # roar (phase two): he rises, arms flung up, the crown thrown back and the jars flung outward
    a = m.anim("roar", 2.4)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.7, (-150, 0, -40 * sx)), (2.0, (-155, 0, -44 * sx)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (2.0, (-28, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (2.0, (-12, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.7, (0, 6, 0)), (2.0, (0, 8, 0)), (2.4, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.7, (10, 0, 6)), (2.0, (12, 0, 6)), (2.4, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (6, 0, -6)), (2.0, (8, 0, -6)), (2.4, (0, 0, 0)))
    a.scale("jars", (0, (1, 1, 1)), (0.7, (1.5, 1, 1.5)), (2.0, (1.5, 1, 1.5)), (2.4, (1, 1, 1)))

    # stagger: his strength gone, he crumples forward on the crook, the jars sinking
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.2, (0, -6, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (-56, 0, 0)), (1.2, (-56, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.2, (60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (18, 0, 0)), (1.2, (18, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (70, 0, 0)), (1.2, (70, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (28, 0, -6)), (1.2, (30, 0, -6)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 8)), (1.2, (26, 0, 8)), (1.6, (0, 0, 0)))
    a.pos("jars", (0, (0, 0, 0)), (0.3, (0, -14, 0)), (1.2, (0, -14, 0)), (1.6, (0, 0, 0)))
