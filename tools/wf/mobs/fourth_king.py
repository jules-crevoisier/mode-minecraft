"""The Fourth King (Le Quatrième Roi): the seated colossus of the Necropolis of Kings whose face was chiselled away,
risen as a gaunt mummified monarch about 6 blocks tall.

Silhouette idea: a king too tall and too thin to be alive. Long stick legs in loose wrappings under a pleated kilt
striped sandstone and lapis, a narrow hunched torso where the bandages have rotted open over the ribs, arms that hang
to the knees. His head is the colossus's mask in small: a sandstone-and-lapis nemes with flaring wings and long
lappets, the face a cracked stone mask whose right half was chiselled off, a dark hollow behind it where one lapis
eye still burns, and the stump of a broken white crown. Strong asymmetry: in the RIGHT hand a royal flail (a banded
gold-and-lapis handle, three beaded lashes ending in lapis weights); in the LEFT a long scarab sceptre, taller than his
shoulder, crowned by a lapis scarab with gilded wings spread under a glowing sun-disc; a slab of the throne still
fused to his left shoulder, glyphs glowing in its cracks; a ragged linen cape of strips, one strip streaming from the
right forearm.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

WRAP = (176, 160, 128)          # old linen, greyed by the tomb
WRAP_L = (206, 192, 160)
WRAP_D = (118, 104, 82)
FLESH = (70, 54, 44)            # the dried skin where the wrappings rotted open
FLESH_D = (40, 30, 26)
BONE = (214, 202, 170)
STONE = (214, 190, 134)         # the sandstone of the colossus
STONE_L = (236, 218, 170)
STONE_D = (160, 134, 88)
STONE_DD = (112, 90, 58)
LAPIS = (40, 66, 160)
LAPIS_L = (96, 132, 214)
LAPIS_D = (24, 38, 102)
GOLD = (218, 172, 64)
GOLD_L = (252, 222, 128)
GOLD_D = (150, 108, 34)
VOID = (16, 14, 24)
GLOW = (120, 176, 255)          # the lapis light in his eye, his cracks and the scarab
GLOW_L = (206, 230, 255)
CALCITE = (232, 228, 214)
CALCITE_D = (180, 174, 158)


# ---------------------------------------------------------------- paint
def wraps(seed=0, rot=0.0, gilt=0.0):
    """Tomb linen: staggered strips with dark seams, rot holes showing dried skin (``rot`` = how much), a few strips
    of old gold leaf (``gilt``)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return WRAP_D
        if face == "top":
            return WRAP_L if (x + y) % 3 else WRAP
        row = y + (x // 3 + seed) % 3
        k = row % 3
        strip = row // 3 * 5 + x // 3
        if rot and B.n(x // 2, y // 2, seed + 11) < rot:
            return FLESH if B.n(x, y, seed + 12) > 0.3 else FLESH_D
        if k == 0:
            return mul(WRAP_D, 0.92)
        if gilt and B.n(strip, 0, seed) < gilt:
            return GOLD if k == 1 else GOLD_D
        c = WRAP_L if k == 1 else WRAP
        if B.n(strip, 1, seed + 3) < 0.2:
            c = mul(c, 0.84)                                        # a stained strip
        return mul(c, 1.03 - 0.14 * y / max(1, h))
    return f


def ribs(face, x, y, w, h):
    """The torso: the wrappings rotted open over the ribcage in front (bone bars over a dark hollow)."""
    if face != "front":
        return wraps(30, rot=0.08)(face, x, y, w, h)
    cx = (w - 1) / 2
    if 3 <= y <= h - 5 and 2 <= x <= w - 3 and abs(x - cx) > 0.6:
        if (y - 3) % 3 == 0:
            return BONE if abs(x - cx) < w / 2 - 2 else mul(BONE, 0.82)  # a rib
        return VOID if abs(x - cx) < 3 else FLESH_D
    if abs(x - cx) <= 0.6 and 2 <= y <= h - 4:
        return mul(BONE, 0.9)                                        # the sternum
    return wraps(31, rot=0.05)(face, x, y, w, h)


def stone(seed=0, cracks=0.0, glyph=False):
    """Weathered sandstone: horizontal bedding, chips, darker underside; optional cracks (filled with VOID, their
    glowing lines come from ``stone_glow``) and a carved glyph."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return STONE_D
        c = STONE_L if (y + seed) % 4 == 0 else STONE
        r = B.n(x, y, seed)
        if r < 0.06:
            c = STONE_DD
        elif r > 0.92:
            c = STONE_L
        if cracks and _crack(x, y, w, h, seed, cracks):
            return VOID
        if glyph and face in ("front", "left", "right") and 1 <= x <= w - 2 and 1 <= y <= h - 2:
            gx, gy = x - 1, y - 1
            if (gx + gy * 3 + seed) % 5 == 0:
                c = LAPIS_D
        return mul(c, 1.05 - 0.15 * y / max(1, h))
    return f


def _crack(x, y, w, h, seed, amount):
    """A jagged crack running down the face: one texel wide, wandering by noise."""
    if w < 3:
        return False
    x0 = int(w * (0.3 + 0.4 * B.n(seed, 1, 7)))
    drift = int((B.n(y // 2, seed, 9) - 0.5) * 3)
    return x == x0 + drift and B.n(y, seed, 5) < 0.6 + amount


def stone_glow(seed=0, cracks=0.3):
    def f(face, x, y, w, h):
        if face in ("front", "left", "right", "back") and _crack(x, y, w, h, seed, cracks):
            return GLOW
        return None
    return f


def lapis_stripes(seed=0, every=2, gold_hem=False):
    """The royal stripes of the nemes and the kilt: sandstone and lapis bands; optional gold hem."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return LAPIS_D
        if gold_hem and y >= h - 1 and face != "top":
            return GOLD if x % 2 else GOLD_D
        if face == "top":
            return STONE_L if (x // every) % 2 == 0 else LAPIS_L
        band = (y // every) % 2 if face != "top" else (x // every) % 2
        c = STONE if band == 0 else LAPIS
        if B.n(x, y, seed) < 0.05:
            c = STONE_DD                                              # a chip in the paint
        return mul(c, 1.06 - 0.16 * y / max(1, h))
    return f


def pleats(face, x, y, w, h):
    """The kilt: vertical pleats in sandstone and lapis, a gold belt line at the top, a frayed hem."""
    if face == "bottom":
        return LAPIS_D
    if face == "top" or y == 0:
        return GOLD if x % 2 else GOLD_D
    if y == h - 1 and B.n(x, 0, 41) < 0.4:
        return None
    c = (STONE, STONE_L, LAPIS, LAPIS_D)[x % 4]
    return mul(c, 1.04 - 0.18 * y / max(1, h))


def gold(seed=0, lapis_every=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        if face == "top":
            return GOLD_L
        if lapis_every and y % lapis_every == lapis_every - 1:
            return LAPIS if (x + y) % 3 else LAPIS_D
        return mul(GOLD, 1.08 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
    return f


def lapis(seed=0, glint=True):
    def f(face, x, y, w, h):
        if face == "bottom":
            return LAPIS_D
        c = LAPIS
        r = B.n(x, y, seed)
        if glint and r > 0.9:
            c = GOLD_L                                                # pyrite flecks in the lapis
        elif r < 0.25:
            c = LAPIS_D
        if face == "top":
            c = mix(c, LAPIS_L, 0.4)
        return c
    return f


def collar_paint(f, x, y, w, h):
    """The broad collar: rows of lapis, gold and sandstone beads, cracked through on one side."""
    if f == "bottom":
        return GOLD_D
    row = y if f != "top" else min(y, h - 1 - y)
    pal = (GOLD_L, LAPIS, STONE, LAPIS_D, GOLD)
    c = pal[row % len(pal)]
    if x % 2 and c in (LAPIS, LAPIS_D):
        c = mul(c, 0.8)
    if f == "front" and x == w - 4 + (y % 2):
        return VOID                                                   # the crack through the collar
    return c


def mask_paint(f, x, y, w, h):
    """The face: the colossus's stone mask. The left half (his left, +x, the viewer's right) is intact: a calm carved
    eye lined in lapis, a straight nose, closed lips; the right half was chiselled away down to a dark hollow with
    chisel marks round its edge and one burning lapis eye inside."""
    if f in ("top", "bottom"):
        return stone(60)(f, x, y, w, h)
    if f != "front":
        return lapis_stripes(61)(f, x, y, w, h)
    cut = 3 + (1 if y in (2, 3, 7, 8) else 0) + (1 if y in (4, 5, 6) else 0)   # the jagged chisel line
    if x < cut and 1 <= y <= h - 2:
        if x == cut - 1:
            return STONE_DD if y % 2 else STONE_D                      # the chisel marks along the edge
        if y == 4 and x in (1, 2):
            return GLOW_L if x == 2 else GLOW                          # the burning eye in the hollow
        return VOID if (x + y) % 5 else FLESH_D
    if y == 0:
        return LAPIS
    if y == 3 and x >= cut:
        return LAPIS_D                                                # the brow line
    if y == 4 and x in (w - 3, w - 2):
        return BONE if x == w - 3 else LAPIS_D                         # the carved eye, lapis-lined
    if 4 <= y <= 6 and x == w // 2 + 1:
        return STONE_L if y < 6 else STONE_DD                          # what is left of the nose
    if y == 8 and w // 2 <= x <= w - 3:
        return STONE_DD                                               # closed lips
    if y == 9 and x == w // 2 + 1:
        return STONE_D
    if y == 5 and x == w - 2 and B.n(5, 5, 3) < 2:
        return LAPIS_D                                                # the cosmetic line from the eye
    return stone(62, cracks=0.0)(f, x, y, w, h)


def mask_glow(f, x, y, w, h):
    if f == "front" and y == 4 and x in (1, 2):
        return GLOW_L if x == 2 else GLOW
    return None


def crown_paint(f, x, y, w, h):
    """The broken white crown: chalky calcite, a jagged snapped top, a gold band at the base."""
    if f == "bottom":
        return CALCITE_D
    if y >= h - 1 and f != "top":
        return GOLD if x % 2 else GOLD_D
    if f == "top":
        return CALCITE_D if (x + y) % 2 else STONE_DD                  # the snapped surface
    if y == 0 and B.n(x, 1, 70) < 0.5:
        return None                                                    # a jagged break along the top
    c = CALCITE if B.n(x, y, 71) > 0.08 else CALCITE_D
    return mul(c, 0.98 + 0.08 * y / max(1, h))


def scarab_paint(f, x, y, w, h):
    """The sceptre's scarab: polished lapis with a gold ridge down its back, gold-flecked."""
    if f == "bottom":
        return LAPIS_D
    if f == "top" and x == w // 2:
        return GOLD_L
    if f == "front" and y == h - 1:
        return GOLD
    return lapis(80)(f, x, y, w, h)


def wing_paint(f, x, y, w, h):
    """A gilded wing: gold feathers banded with lapis toward the tip, rows of little feathers."""
    if f == "bottom":
        return GOLD_D
    if f in ("front", "back", "top"):
        if x % 3 == 2:
            return LAPIS if y % 2 else LAPIS_D
        return GOLD_L if y == 0 else (GOLD if (x + y) % 2 else mul(GOLD, 0.9))
    return GOLD_D


def disc_glow(f, x, y, w, h):
    return GLOW_L if (x + y) % 3 else GLOW


def chain_paint(f, x, y, w, h):
    """A string of beads: gold and lapis alternating."""
    return GOLD if (y // 2) % 2 == 0 else LAPIS


def glyph_glow(seed):
    def f(face, x, y, w, h):
        if face in ("front", "left", "right") and 1 <= x <= w - 2 and 1 <= y <= h - 2:
            gx, gy = x - 1, y - 1
            if (gx + gy * 3 + seed) % 5 == 0:
                return GLOW
        return None
    return f


def cloth(seed=0):
    """The cape's old linen: long vertical threads, darker toward the hem, a few holes, frayed end."""
    def f(face, x, y, w, h):
        if face != "top" and y >= h - 1 - int(B.n(x, 0, seed) * 4):
            return None
        if face != "top" and B.n(x, y // 3, seed + 4) < 0.04:
            return None                                                # moth holes
        c = mix(WRAP, WRAP_D, 0.35) if x % 2 else mix(WRAP, WRAP_D, 0.15)
        if B.n(x, y // 4, seed + 2) < 0.12:
            c = mul(c, 0.82)
        return mul(c, 1.0 - 0.3 * y / max(1, h))
    return f


def strip_paint(seed=0):
    """A loose linen strip: ragged end, frayed edges."""
    def f(face, x, y, w, h):
        if face != "top" and y >= h - 1 - int(B.n(x, 0, seed) * 3):
            return None
        return wraps(seed)(face, x, y, w, h)
    return f


# ---------------------------------------------------------------- build
def build():
    m = Model("fourth_king", seed=431, shadow=1.3, walk_speed=0.6, walk_scale=0.8, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -46, 0))
    m.part("leg_r", "hips", pivot=(-3.5, 0, 0))
    m.part("shin_r", "leg_r", pivot=(0, 22, 0))
    m.part("leg_l", "hips", pivot=(3.5, 0, 0))
    m.part("shin_l", "leg_l", pivot=(0, 22, 0))
    m.part("kilt", "hips", pivot=(0, 0, 0))
    m.part("waist", "hips", pivot=(0, -2, 0))
    m.part("chest", "waist", pivot=(0, -8, 0), rot=(10, 0, 0))
    m.part("cape", "chest", pivot=(0, -17, 4.2), rot=(6, 0, 0))
    m.part("neck", "chest", pivot=(0, -18, -1))
    m.part("head", "neck", pivot=(0, -4, 0), rot=(-8, 0, 0))
    m.part("arm_r", "chest", pivot=(-8.5, -16, 0), rot=(-6, 0, 6))
    m.part("fore_r", "arm_r", pivot=(0, 17, 0), rot=(-26, 0, 0))
    m.part("hand_r", "fore_r", pivot=(0, 16, 0))
    m.part("flail", "hand_r", pivot=(0, 2.5, -0.5), rot=(-70, 0, 0))
    for i, (x, rz) in enumerate(((-1.4, 10), (0, 0), (1.4, -10))):
        m.part(f"lash_{i}", "flail", pivot=(x, 9.5, 0), rot=(88, 0, rz))
    m.part("strip_r", "fore_r", pivot=(0, 6, 1.6), rot=(20, 0, 10))
    m.part("arm_l", "chest", pivot=(8.5, -16, 0), rot=(-4, 0, -20))
    m.part("fore_l", "arm_l", pivot=(0, 17, 0), rot=(-48, 0, 0))
    m.part("hand_l", "fore_l", pivot=(0, 16, 0))
    m.part("sceptre", "hand_l", pivot=(0, 2, 0), rot=(44, 0, 16))
    m.part("wing_r", "sceptre", pivot=(-2.5, -47, 0), rot=(0, 0, 18))
    m.part("wing_l", "sceptre", pivot=(2.5, -47, 0), rot=(0, 0, -18))

    # ---- legs: stick-thin, in loose wrappings, gold anklets, bare bony feet
    for s, leg, shin in ((-1, "leg_r", "shin_r"), (1, "leg_l", "shin_l")):
        m.box(leg, -2, -1, -2, 4, 23, 4, wraps(10 + s, rot=0.06))
        m.box(leg, -2.5, 8, -2.5, 5, 2, 5, wraps(12 + s, gilt=0.3))                      # a band round the thigh
        m.box(shin, -1.5, 0, -1.5, 3, 21, 3, wraps(14 + s, rot=0.1))
        m.box(shin, -2, -1, -2, 4, 2, 4, wraps(16 + s))                                    # the knee
        m.box(shin, -2, 17, -2, 4, 2, 4, gold(18 + s))                                     # the anklet
        m.box(shin, -2, 21, -5, 4, 3, 6, wraps(20 + s, rot=0.25))                          # the foot
        m.box(shin, -1.5, 22, -6, 3, 2, 1, BONE)                                           # bony toes
    m.box("leg_r", -2.4, 2, 1.8, 1, 10, 1, strip_paint(22))                                # a loose bandage

    # ---- the kilt: pleated, striped sandstone and lapis, a lapis-and-gold apron, a gold belt
    m.box("kilt", -6, -3, -4, 12, 13, 8, pleats)
    m.box("kilt", -6.5, -4, -4.5, 13, 2, 9, gold(40, lapis_every=0))                       # the belt
    m.box("kilt", -2.5, -2, -5.2, 5, 15, 1, lapis_stripes(42, every=2, gold_hem=True))    # the apron
    m.box("kilt", -1.5, -3.5, -5.6, 3, 3, 1, gold(43))                                     # the buckle
    m.box("kilt", -7, 1, -3, 1, 9, 6, pleats)                                              # side flare
    m.box("kilt", 6, 1, -3, 1, 9, 6, pleats)

    # ---- torso: a thin spine, a hunched chest rotted open over the ribs, the broad collar
    m.box("waist", -3, -8, -2.5, 6, 9, 5, wraps(50, rot=0.18))
    m.box("waist", -1, -8, 1.5, 2, 9, 2, BONE)                                             # the spine, bare
    m.box("chest", -7, -18, -4, 14, 18, 8, ribs)
    m.box("chest", -7.5, -19, -4.5, 15, 4, 9, collar_paint)                                # the broad collar
    m.box("chest", -5, -15, -5, 10, 2, 1, collar_paint)                                    # its lower rows
    m.box("chest", -3, -13, -4.8, 6, 1, 1, GOLD)                                           # the pendant's chain
    m.box("chest", -1.5, -12.5, -5.3, 3, 3, 1, lapis(52), glow=None)                       # a lapis pectoral
    m.box("chest", -6, -6, -4.6, 12, 3, 1, wraps(53, gilt=0.25))                           # a band under the ribs
    # the slab of the throne fused to the left shoulder: sandstone, a glyph, glowing cracks
    m.box("chest", 5, -22, -4.5, 7, 7, 9, stone(54, cracks=0.3, glyph=True), glow=stone_glow(54))
    m.box("chest", 7, -24, -3, 4, 2, 6, stone(55))
    m.box("chest", 9, -15, -3.5, 3, 4, 6, stone(56, cracks=0.2), glow=stone_glow(56))
    m.box("chest", -9, -19, -3, 3, 3, 6, wraps(57, gilt=0.5))                              # the right shoulder

    # ---- the cape: ragged strips of linen down the back
    for i, (x, ln) in enumerate(((-6, 34), (-3.5, 40), (-1, 44), (1.5, 38), (4, 42), (6.5, 30))):
        m.box("cape", x - 1.25, 0, (i % 2) * 0.5, 3, ln, 1, cloth(60 + i))
    m.box("cape", -7, -1, -0.5, 14, 4, 2, wraps(68))

    m.box("neck", -2, -4, -2, 4, 5, 4, wraps(70, rot=0.3))

    # ---- head: nemes with flaring wings and long striped lappets, the broken stone mask, the snapped crown
    m.box("head", -4.5, -11, -5, 9, 11, 9, mask_paint, glow=mask_glow)
    m.box("head", -5, -12, -3.5, 10, 2, 9, lapis_stripes(80, every=1))                     # the nemes over the brow
    m.box("head", -7, -10, -3, 2, 9, 7, lapis_stripes(81, every=2))                        # its wings at the temples
    m.box("head", 5, -10, -3, 2, 9, 7, lapis_stripes(82, every=2))
    m.box("head", -7.5, -2, -2.5, 3, 13, 2, lapis_stripes(83, every=2, gold_hem=True))     # lappets on the chest
    m.box("head", 4.5, -2, -2.5, 3, 13, 2, lapis_stripes(84, every=2, gold_hem=True))
    m.box("head", -4, -9, 4, 8, 12, 2, lapis_stripes(85, every=2))                         # the queue behind
    m.box("head", -1, -1, -5.6, 2, 5, 1, lapis_stripes(86, every=1))                       # the false beard
    m.box("head", -3, -17, -3, 6, 6, 6, crown_paint)                                       # the snapped white crown
    m.box("head", -2, -22, -2, 4, 5, 4, crown_paint)                                       # its broken upper bulb
    m.box("head", -3.5, -12.5, -3, 7, 2, 7, gold(87))                                      # its gold band
    m.box("head", -0.5, -14, -4.2, 1, 3, 1, GOLD)                                          # the broken uraeus
    m.box("head", -1.5, -13, -4.8, 3, 1, 1, GOLD_D)

    # ---- right arm: gaunt, gold armlet, the royal flail
    m.box("arm_r", -2, -1, -2, 4, 18, 4, wraps(90, rot=0.12))
    m.box("arm_r", -2.5, 4, -2.5, 5, 2, 5, gold(91, lapis_every=2))                        # an armlet
    m.box("fore_r", -1.5, 0, -1.5, 3, 16, 3, wraps(92, rot=0.15))
    m.box("fore_r", -2, 11, -2, 4, 3, 4, gold(93))                                         # a bracelet
    m.box("hand_r", -2, 0, -2, 4, 4, 4, wraps(94, rot=0.3))
    m.box("hand_r", -1.5, 3, -2.5, 3, 2, 1, BONE)                                          # bony fingers
    m.box("strip_r", -1, 0, 0, 2, 14, 1, strip_paint(95))
    # the flail: a banded handle (down +y, turned forward), three beaded lashes with lapis weights
    m.box("flail", -1, -3, -1, 2, 13, 2, gold(100, lapis_every=2))
    m.box("flail", -1.5, -4, -1.5, 3, 2, 3, lapis(101))                                    # the pommel
    m.box("flail", -1.5, 8.5, -1.5, 3, 2, 3, GOLD)                                         # the head of the handle
    for i in range(3):
        p = f"lash_{i}"
        m.box(p, -0.5, 0, -0.5, 1, 12, 1, chain_paint)
        m.box(p, -1.5, 12, -1.5, 3, 4, 3, lapis(102 + i), glow=None)                       # the lapis weight
        m.box(p, -1, 15.5, -1, 2, 1, 2, GOLD)

    # ---- left arm: gaunt, the scarab sceptre
    m.box("arm_l", -2, -1, -2, 4, 18, 4, wraps(110, rot=0.12))
    m.box("arm_l", -2.5, 9, -2.5, 5, 2, 5, gold(111))
    m.box("fore_l", -1.5, 0, -1.5, 3, 16, 3, wraps(112, rot=0.15))
    m.box("fore_l", -2, 10, -2, 4, 4, 4, gold(113, lapis_every=2))
    m.box("hand_l", -2, 0, -2, 4, 4, 4, wraps(114, rot=0.3))
    # the sceptre: a long gilt shaft banded with lapis; at its head a lapis scarab, wings spread, holding up a sun
    m.box("sceptre", -1, -44, -1, 2, 58, 2, gold(120, lapis_every=4))
    m.box("sceptre", -1.5, 13, -1.5, 3, 2, 3, lapis(121))                                  # the butt-cap
    m.box("sceptre", -2, -43, -2, 4, 2, 4, GOLD_D)                                         # the collar
    m.box("sceptre", -2.5, -49, -2.5, 5, 6, 5, scarab_paint)                               # the scarab's body
    m.box("sceptre", -1.5, -48, -3.5, 3, 3, 1, scarab_paint)                               # its head
    m.box("sceptre", -2, -47, -4.2, 1, 1, 1, GOLD_L)                                       # its jaws
    m.box("sceptre", 1, -47, -4.2, 1, 1, 1, GOLD_L)
    m.box("sceptre", -2.5, -53, -1, 5, 1, 2, GOLD)                                         # the forelegs lifting the sun
    m.box("sceptre", -3, -58, -1, 6, 5, 2, disc_glow, glow=disc_glow)                     # the sun-disc
    m.box("sceptre", -2, -59, -1, 4, 1, 2, disc_glow, glow=disc_glow)
    m.box("sceptre", -2, -53, -1, 4, 1, 2, disc_glow, glow=disc_glow)
    m.box("wing_r", -9, -1, -0.5, 9, 4, 1, wing_paint)
    m.box("wing_r", -7, 3, -0.5, 6, 2, 1, wing_paint)
    m.box("wing_l", 0, -1, -0.5, 9, 4, 1, wing_paint)
    m.box("wing_l", 1, 3, -0.5, 6, 2, 1, wing_paint)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, -0.5, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (3, 10, 2)), (2.6, (-2, -8, -2)), (4.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (2.0, (6, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("strip_r", (0, (0, 0, 0)), (1.5, (10, 0, -8)), (3.0, (-6, 0, 6)), (4.0, (0, 0, 0)))
    for i in range(3):
        idle.rot(f"lash_{i}", (0, (0, 0, 0)), (1.0 + 0.3 * i, (8, 0, 6)), (2.6 + 0.2 * i, (-8, 0, -5)), (4.0, (0, 0, 0)))
    idle.rot("wing_r", (0, (0, 0, 0)), (2.0, (0, 0, 10)), (4.0, (0, 0, 0)))
    idle.rot("wing_l", (0, (0, 0, 0)), (2.0, (0, 0, -10)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.6)
    walk.rot("leg_r", (0, (-22, 0, 0)), (1.3, (22, 0, 0)), (2.6, (-22, 0, 0)))
    walk.rot("leg_l", (0, (22, 0, 0)), (1.3, (-22, 0, 0)), (2.6, (22, 0, 0)))
    walk.rot("shin_r", (0, (8, 0, 0)), (0.65, (34, 0, 0)), (1.3, (4, 0, 0)), (2.6, (8, 0, 0)))
    walk.rot("shin_l", (0, (4, 0, 0)), (1.3, (8, 0, 0)), (1.95, (34, 0, 0)), (2.6, (4, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.65, (0, 1, 0)), (1.3, (0, 0, 0)), (1.95, (0, 1, 0)), (2.6, (0, 0, 0)))
    walk.rot("chest", (0, (2, -5, 0)), (1.3, (2, 5, 0)), (2.6, (2, -5, 0)))
    walk.rot("arm_r", (0, (14, 0, 0)), (1.3, (-12, 0, 0)), (2.6, (14, 0, 0)))
    walk.rot("arm_l", (0, (-6, 0, 0)), (1.3, (6, 0, 0)), (2.6, (-6, 0, 0)))
    walk.rot("cape", (0, (10, 0, 0)), (1.3, (14, 0, 0)), (2.6, (10, 0, 0)))
    walk.rot("kilt", (0, (0, 4, 0)), (1.3, (0, -4, 0)), (2.6, (0, 4, 0)))

    # flail: raised behind the right shoulder (0.7 s = 14 ticks), a forehand lash at 0.7 s, a backhand at 1.2 s, an
    # overhead lash down a line at 1.7 s
    a = m.anim("flail", 2.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-150, -20, 40)), (0.7, (-156, -22, 44)), (0.76, (-70, 30, -40), "linear"),
          (1.1, (-110, 50, -40)), (1.2, (-70, -30, 40), "linear"), (1.55, (-176, 0, 6)), (1.7, (-178, 0, 6)),
          (1.76, (-50, 0, 4), "linear"), (2.1, (-50, 0, 4)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 30, 0)), (0.76, (8, -28, 0), "linear"), (1.1, (6, -30, 0)),
          (1.2, (8, 26, 0), "linear"), (1.55, (-14, 0, 0)), (1.7, (-16, 0, 0)), (1.76, (22, 0, 0), "linear"),
          (2.1, (20, 0, 0)), (2.7, (0, 0, 0)))
    for i in range(3):
        a.rot(f"lash_{i}", (0, (0, 0, 0)), (0.7, (40, 0, 0)), (0.78, (-60, 0, 0), "linear"), (1.2, (40, 0, 0)),
              (1.28, (-60, 0, 0), "linear"), (1.7, (50, 0, 0)), (1.78, (-50, 0, 0), "linear"), (2.2, (0, 0, 0)),
              (2.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (10, 0, -10)), (1.7, (16, 0, -14)), (2.7, (0, 0, 0)))

    # smite: the flail swung up in both hands over his head (1.0 s = 20 ticks), crashed into the floor ahead
    a = m.anim("smite", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-172, 0, -14)), (1.0, (-176, 0, -16)), (1.06, (-40, 0, -6), "linear"),
          (1.6, (-44, 0, -6)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-150, 0, 20)), (1.0, (-154, 0, 22)), (1.06, (-50, 0, 10), "linear"),
          (1.6, (-50, 0, 10)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.06, (30, 0, 0), "linear"), (1.6, (28, 0, 0)), (2.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.06, (0, -5, 0), "linear"), (1.6, (0, -5, 0)), (2.1, (0, 0, 0)))
    for i in range(3):
        a.rot(f"lash_{i}", (0, (0, 0, 0)), (1.0, (60, 0, 0)), (1.08, (-40, 0, 0), "linear"), (1.6, (-30, 0, 0)),
              (2.1, (0, 0, 0)))

    # beam_low: the sceptre lowered to the floor on his left (1.1 s = 22 ticks), then swept low across the arena
    # from his left to his right for 2 s
    a = m.anim("beam_low", 3.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -50)), (1.1, (-42, 0, -54)), (3.1, (-42, 0, -54)), (3.9, (0, 0, 0)))
    a.rot("sceptre", (0, (0, 0, 0)), (1.1, (40, 0, 0)), (3.1, (40, 0, 0)), (3.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (18, 70, 0)), (1.1, (20, 74, 0)), (2.1, (22, 0, 0), "linear"),
          (3.1, (20, -74, 0), "linear"), (3.5, (12, -40, 0)), (3.9, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (1.1, (0, 20, 0)), (3.1, (0, -20, 0), "linear"), (3.9, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, -4, 0)), (3.1, (0, -4, 0)), (3.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.1, (20, 0, 30)), (3.1, (20, 0, 30)), (3.9, (0, 0, 0)))
    a.scale("wing_r", (0, (1, 1, 1)), (1.1, (1.3, 1.3, 1.3)), (3.1, (1.3, 1.3, 1.3)), (3.9, (1, 1, 1)))
    a.scale("wing_l", (0, (1, 1, 1)), (1.1, (1.3, 1.3, 1.3)), (3.1, (1.3, 1.3, 1.3)), (3.9, (1, 1, 1)))

    # beam_high: the sceptre raised level with his eyes (1.0 s = 20 ticks), the beam scythes across ahead of him and
    # back over 1.5 s at head height
    a = m.anim("beam_high", 3.3)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-96, 0, -6)), (1.0, (-100, 0, -8)), (2.5, (-100, 0, -8)), (3.3, (0, 0, 0)))
    a.rot("sceptre", (0, (0, 0, 0)), (1.0, (-40, 0, 0)), (2.5, (-40, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 36, 0)), (1.75, (-8, -36, 0)), (2.5, (-8, 36, 0)), (3.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (2.5, (-10, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (14, 0, 20)), (2.5, (14, 0, 20)), (3.3, (0, 0, 0)))
    a.scale("wing_r", (0, (1, 1, 1)), (1.0, (1.4, 1.4, 1.4)), (2.5, (1.4, 1.4, 1.4)), (3.3, (1, 1, 1)))
    a.scale("wing_l", (0, (1, 1, 1)), (1.0, (1.4, 1.4, 1.4)), (2.5, (1.4, 1.4, 1.4)), (3.3, (1, 1, 1)))

    # sandfall: the sceptre thrust up at the ceiling (0.9 s = 18 ticks), a jab; the sand comes down after
    a = m.anim("sandfall", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-160, 0, -10)), (0.9, (-164, 0, -10)), (0.96, (-178, 0, -4), "linear"),
          (1.3, (-176, 0, -4)), (1.9, (0, 0, 0)))
    a.rot("sceptre", (0, (0, 0, 0)), (0.9, (-40, 0, 0)), (1.3, (-46, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-34, 0, 0)), (1.3, (-30, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, -10, 0)), (0.96, (-18, -10, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-30, 0, 40)), (1.3, (-30, 0, 40)), (1.9, (0, 0, 0)))

    # swarm: the sceptre levelled at one of you, the scarab's wings open (0.8 s = 16 ticks), and the swarm pours out
    a = m.anim("swarm", 1.7)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-70, 0, -20)), (0.8, (-72, 0, -20)), (0.85, (-96, 0, -4), "linear"),
          (1.2, (-94, 0, -4)), (1.7, (0, 0, 0)))
    a.rot("sceptre", (0, (0, 0, 0)), (0.8, (-20, 0, 0)), (0.85, (-50, 0, 0), "linear"), (1.2, (-50, 0, 0)),
          (1.7, (0, 0, 0)))
    a.scale("wing_r", (0, (1, 1, 1)), (0.8, (1.6, 1.6, 1.6)), (0.86, (1.9, 1.9, 1.9), "linear"), (1.2, (1.6, 1.6, 1.6)),
            (1.7, (1, 1, 1)))
    a.scale("wing_l", (0, (1, 1, 1)), (0.8, (1.6, 1.6, 1.6)), (0.86, (1.9, 1.9, 1.9), "linear"), (1.2, (1.6, 1.6, 1.6)),
            (1.7, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, -20, 0)), (0.85, (10, -10, 0), "linear"), (1.7, (0, 0, 0)))

    # drain: the sceptre lifted high and the free hand clawed open toward the jars (1.0 s = 20 ticks), held for 2.5 s
    # while the jars empty into him
    a = m.anim("drain", 4.3)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-166, 0, -20)), (1.0, (-170, 0, -22)), (3.5, (-170, 0, -22)), (4.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-80, 0, 70)), (1.0, (-84, 0, 74)), (2.2, (-80, 0, 70)), (3.5, (-84, 0, 74)),
          (4.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (2.2, (-34, 6, 0)), (3.5, (-30, -6, 0)), (4.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (3.5, (-16, 0, 0)), (4.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 2, 0)), (3.5, (0, 3, 0)), (4.3, (0, 0, 0)))
    a.scale("wing_r", (0, (1, 1, 1)), (1.0, (1.5, 1.5, 1.5)), (3.5, (1.5, 1.5, 1.5)), (4.3, (1, 1, 1)))
    a.scale("wing_l", (0, (1, 1, 1)), (1.0, (1.5, 1.5, 1.5)), (3.5, (1.5, 1.5, 1.5)), (4.3, (1, 1, 1)))

    # procession: he leans into a long gliding stride (0.7 s = 14 ticks), sweeps across the floor, and at 1.3 s the
    # flail comes down overhead where he lands
    a = m.anim("procession", 2.2)
    a.rot("chest", (0, (0, 0, 0)), (0.7, (30, 0, 0)), (0.76, (36, 0, 0), "linear"), (1.1, (-14, 0, 0)),
          (1.3, (-16, 0, 0)), (1.36, (26, 0, 0), "linear"), (1.7, (24, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (40, 0, 20)), (1.1, (-170, 0, 6)), (1.3, (-176, 0, 6)), (1.36, (-46, 0, 4), "linear"),
          (1.7, (-46, 0, 4)), (2.2, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (-40, 0, 0)), (1.1, (30, 0, 0)), (1.7, (10, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (30, 0, 0)), (1.1, (-36, 0, 0)), (1.7, (-10, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.76, (50, 0, 0)), (1.2, (40, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (30, 0, -20)), (1.7, (20, 0, -20)), (2.2, (0, 0, 0)))
    for i in range(3):
        a.rot(f"lash_{i}", (0, (0, 0, 0)), (1.3, (60, 0, 0)), (1.4, (-40, 0, 0), "linear"), (2.2, (0, 0, 0)))

    # sandburst: he draws his arms in, hunched (0.6 s = 12 ticks), then flings them out: sand bursts all round him
    a = m.anim("sandburst", 1.35)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-30, 0, -30)), (0.64, (-40, 0, 80), "linear"), (1.0, (-36, 0, 74)),
          (1.35, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-30, 0, 30)), (0.64, (-40, 0, -80), "linear"), (1.0, (-36, 0, -74)),
          (1.35, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (26, 0, 0)), (0.64, (-14, 0, 0), "linear"), (1.0, (-10, 0, 0)), (1.35, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.6, (0, -3, 0)), (0.64, (0, 1, 0), "linear"), (1.35, (0, 0, 0)))

    # seal (phase 3, invulnerable): arms raised to the ceiling, head thrown back (1.5 s = 30 ticks); then his fists
    # come down and the tomb seals into darkness
    a = m.anim("seal", 3.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-170, 0, 30)), (1.5, (-176, 0, 34)), (1.56, (-60, 0, 20), "linear"),
          (2.8, (-60, 0, 20)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-170, 0, -30)), (1.5, (-176, 0, -34)), (1.56, (-60, 0, -20), "linear"),
          (2.8, (-60, 0, -20)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-40, 0, 0)), (1.56, (20, 0, 0), "linear"), (2.8, (18, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-24, 0, 0)), (1.56, (26, 0, 0), "linear"), (2.8, (24, 0, 0)), (3.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, 2, 0)), (1.56, (0, -6, 0), "linear"), (2.8, (0, -6, 0)), (3.5, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.5, (30, 0, 0)), (1.6, (-10, 0, 0)), (3.5, (0, 0, 0)))

    # verdict (phase 3): he kneels, arms spread wide, face lifted to his three brothers (1.2 s = 24 ticks), and holds
    # it for 4 s while their gaze sweeps the tomb
    a = m.anim("verdict", 6.0)
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -14, 0)), (1.2, (0, -15, 0)), (5.2, (0, -15, 0)), (6.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.2, (-80, 0, 0)), (5.2, (-80, 0, 0)), (6.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.2, (90, 0, 0)), (5.2, (90, 0, 0)), (6.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.2, (-10, 0, 0)), (5.2, (-10, 0, 0)), (6.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.2, (80, 0, 0)), (5.2, (80, 0, 0)), (6.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.2, (-100, 0, 70)), (5.2, (-100, 0, 70)), (6.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.2, (-100, 0, -70)), (5.2, (-100, 0, -70)), (6.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-36, 0, 0)), (3.2, (-36, 30, 0)), (5.2, (-36, -30, 0)), (6.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-12, 0, 0)), (5.2, (-12, 0, 0)), (6.0, (0, 0, 0)))

    # roar (phase two): sceptre and flail flung wide, head thrown back, the wings spread
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-120, 0, -50)), (1.6, (-124, 0, -54)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.6, (-36, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-22, 0, 0)), (1.6, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("wing_r", (0, (1, 1, 1)), (0.5, (1.6, 1.6, 1.6)), (1.6, (1.6, 1.6, 1.6)), (2.0, (1, 1, 1)))
    a.scale("wing_l", (0, (1, 1, 1)), (0.5, (1.6, 1.6, 1.6)), (1.6, (1.6, 1.6, 1.6)), (2.0, (1, 1, 1)))

    # stagger: he sags on his long legs, head lolling, the sceptre leaning on the floor
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -10, 0)), (1.6, (0, -10, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.6, (-40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (-30, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (34, 0, 10)), (1.6, (36, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (34, 0, -16)), (1.6, (34, 0, -16)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (14, 0, 20)), (1.6, (14, 0, 20)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-30, 0, -20)), (1.6, (-30, 0, -20)), (2.0, (0, 0, 0)))
