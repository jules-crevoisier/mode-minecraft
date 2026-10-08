"""The Frost Jarl (Le Jarl de givre): the dead king of the Glacier Hall, about 5.7 blocks tall.

Silhouette idea: a towering Norse king frozen solid on his feet, rime grown over him like a second armour. Pale
frost-blue skin, two cold white-blue eyes under an iron helm with a nasal; a crown of ice spikes rises from the helm.
A huge braided beard of hoarfrost hangs to his belt, icicles dripping from it (his jaw opens for the ice breath). A
white wolf pelt over his shoulders, its head snarling on his left shoulder, a long navy cloak with a fur edge and a
ragged, frozen hem; a mail hauberk under an iron breastplate with a gold knot on the belt.
Strong asymmetry: in his RIGHT fist a great bearded Dane axe whose blade is a crescent of blue ice with a glowing
edge; on his LEFT arm a round Viking shield (spruce planks, a white rune-wolf, an iron boss and rim) crusted with
frost and hung with icicles; a cluster of ice crystals has grown out of his RIGHT shoulder blade, the right horn of
the helm whole and the left one snapped off.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

SKIN = (150, 180, 200)
SKIN_L = (200, 224, 236)
SKIN_D = (96, 124, 150)
ICE = (160, 214, 242)
ICE_L = (226, 248, 255)
ICE_D = (86, 150, 204)
GLOW = (130, 236, 255)
GLOW_L = (220, 252, 255)
IRON = (96, 102, 116)
IRON_L = (158, 166, 180)
IRON_D = (50, 54, 66)
FUR = (226, 224, 216)
FUR_D = (160, 158, 150)
WOOL = (46, 64, 108)
WOOL_D = (26, 36, 66)
LEATHER = (96, 64, 44)
LEATHER_D = (60, 40, 28)
GOLD = (222, 178, 70)
GOLD_L = (255, 228, 140)
GOLD_D = (150, 110, 34)
WOOD = (118, 84, 54)
WOOD_D = (78, 54, 34)
BEARD = (238, 246, 250)
BEARD_D = (178, 202, 220)


# ---------------------------------------------------------------- paint
def frost(c, x, y, seed, amount=0.18):
    """Speckle rime over a colour: a few pale crystals."""
    if B.n(x, y, seed) < amount:
        return mix(c, ICE_L, 0.55)
    return c


def skin(seed=0):
    """Frozen skin: pale blue, darker below, rime flecks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        k = 1.06 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.10
        return frost(mul(SKIN, k), x, y, seed + 3, 0.12)
    return f


def iron(seed=0, rime=0.15):
    """Dark iron plate with a lit top edge, a rim and frost creeping up from the bottom."""
    base = B.plate(IRON, IRON_D, IRON_L, rivet=IRON_L, seed=seed, grad=0.18)

    def f(face, x, y, w, h):
        c = base(face, x, y, w, h)
        if c is None:
            return c
        if face not in ("top", "bottom") and y >= h * 0.6 and B.n(x, y, seed + 9) < rime + 0.3 * (y / max(1, h) - 0.6):
            return mix(c, ICE_L, 0.6)
        return frost(c, x, y, seed + 1, rime * 0.5)
    return f


def mail(seed=0):
    """Mail: rows of tiny rings, dark gaps, rime in the links."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return IRON_D
        if (x + (y // 2) % 2) % 2 == 0 and y % 2 == 0:
            return IRON_D
        c = mul(IRON_L if y % 2 else IRON, 1.0 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        return frost(c, x, y, seed + 2, 0.10)
    return f


def fur(seed=0, dark=False):
    """White wolf fur: streaky tufts, darker underside, ragged."""
    base = FUR_D if dark else FUR

    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(base, 0.75)
        streak = B.n(x, y // 3, seed) - 0.5
        k = 1.03 - 0.12 * y / max(1, h) + streak * 0.16
        c = mul(base, k)
        if face != "top" and y == h - 1 and B.n(x, 0, seed + 4) < 0.35:
            return mul(base, 0.68)
        return c
    return f


def wool(seed=0):
    """The cloak: navy wool with vertical folds, a fur edge at the top, a frozen ragged hem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOL_D
        if y < 3:
            return fur(seed)(face, x, y, w, 3)
        hem = h - 1 - int(B.n(x, 0, seed) * 4)
        if y > hem:
            return None
        if y >= hem - 2:
            return mix(WOOL, ICE_L, 0.55)                    # frozen hem
        k = 1.02 - 0.18 * y / max(1, h) + (0.10 if x % 4 == 1 else -0.05 if x % 4 == 3 else 0.0)
        c = mul(WOOL, k + (B.n(x, y, seed) - 0.5) * 0.05)
        if face == "back" and w >= 20:                     # a white wolf head woven on the back
            cx, cy = (w - 1) / 2, 16
            dx, dy = abs(x - cx), y - cy
            if 0 <= dy <= 8 and dx <= 4 - dy * 0.35 or -4 <= dy < 0 and 2 <= dx <= 4 + dy * 0.5:
                return mix(FUR, ICE_L, 0.2)
        return frost(c, x, y, seed + 5, 0.05)
    return f


def leather(seed=0):
    return B.bands(LEATHER, LEATHER_D, every=4, seed=seed)


def ice(seed=0, bright=False):
    """Clear ice: pale, lit top, a darker core streak, bright facets."""
    def f(face, x, y, w, h):
        if face == "top":
            return ICE_L
        if face == "bottom":
            return ICE_D
        k = (B.n(x, y, seed) - 0.5) * 0.12
        c = mix(ICE, ICE_D, 0.35 + 0.4 * y / max(1, h)) if x == w // 2 else mix(ICE, ICE_L, 0.3 - 0.3 * y / max(1, h))
        if bright and (x + y) % 5 == 0:
            c = ICE_L
        return mul(c, 1.0 + k)
    return f


def ice_glow(seed=0, amount=0.25):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        return GLOW if B.n(x, y, seed) < amount else None
    return f


def breast_paint(f, x, y, w, h):
    """The hauberk: mail all round; in front an iron breastplate with a gold knot boss and rime on the plates."""
    if f != "front":
        return mail(70)(f, x, y, w, h)
    cx = (w - 1) / 2
    dx = x - cx
    if y < 3:
        return mail(71)(f, x, y, w, h)
    plate_w = 10.5 - max(0, y - 14) * 0.35
    if abs(dx) <= plate_w:
        if abs(abs(dx) - plate_w) < 0.8 or y == 3:
            return IRON_D if y > 3 else IRON_L
        if abs(dx) < 0.6:
            return IRON_L                                   # the ridge
        r = math.hypot(dx, y - 9)
        if r <= 3.2:                                        # gold knot boss
            if r > 2.4:
                return GOLD_D
            return GOLD_L if (round(dx) + y) % 3 == 0 else GOLD
        c = mul(IRON, 1.08 - 0.25 * (y - 3) / max(1, h - 3) + (0.08 if dx < 0 else -0.04))
        return frost(c, x, y, 72, 0.08 + 0.25 * (y / h))
    return mail(73)(f, x, y, w, h)


def face_paint(f, x, y, w, h):
    """The jarl's face under the helm: frozen skin, frosted brows, white-blue eyes, a grim mouth (hidden by the
    beard), hoarfrost cheeks."""
    if f == "bottom":
        return SKIN_D
    if f != "front":
        return skin(80)(f, x, y, w, h)
    if y == 5 and x in (2, 3, w - 4, w - 3):
        return GLOW_L                                        # eyes
    if y == 6 and x in (2, 3, w - 4, w - 3):
        return GLOW
    if y == 4 and 1 <= x <= w - 2 and x not in (w // 2 - 1, w // 2):
        return mix(BEARD, ICE_L, 0.4)                       # frosted brows
    if y >= 7 and x in (1, w - 2):
        return BEARD                                        # sideburns
    if y == 8 and w // 2 - 2 <= x <= w // 2 + 1:
        return SKIN_D
    return skin(81)(f, x, y, w, h)


def face_glow(f, x, y, w, h):
    if f == "front" and y in (5, 6) and x in (2, 3, w - 4, w - 3):
        return GLOW_L if y == 5 else GLOW
    return None


def beard_paint(seed=0):
    """Hoarfrost beard: long white-blue strands, darker between them."""
    def f(face, x, y, w, h):
        if face == "top":
            return BEARD_D
        if face == "bottom":
            return ICE
        strand = (x + seed) % 3
        c = BEARD if strand == 0 else (mix(BEARD, ICE_L, 0.4) if strand == 1 else BEARD_D)
        return mul(c, 1.04 - 0.14 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
    return f


def mouth_paint(f, x, y, w, h):
    """Inside of the mouth (seen when the jaw drops): a cold glowing throat."""
    return (40, 70, 100) if f != "top" else (60, 120, 160)


def mouth_glow(f, x, y, w, h):
    return GLOW if f in ("top", "front") else None


def shield_paint(seed=0):
    """Round shield face: vertical spruce planks, a white rune-wolf on blue halves, frost at the edges."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return IRON_D                                   # the rim seen edge-on
        if face == "back":
            return mul(WOOD_D, 1.0 - 0.1 * (x % 4 == 0))
        # front: plank seams every 4 texels, painted halves, rime toward the rim
        return None
    return f


SH_R = 13               # shield radius (px)


def shield_front(row_y, half):
    """Paint of the front face of one shield row at height ``row_y`` (px from the centre), half-width ``half``."""
    def f(face, x, y, w, h):
        if face != "front":
            return shield_paint()(face, x, y, w, h)
        px = x - half + 0.5                                 # px from the centre line
        py = row_y + y + 0.5
        r = math.hypot(px, py)
        if r > SH_R - 1.4:
            return IRON_L if py < 0 else IRON                # iron rim
        if r < 2.6:
            return IRON_L if px < 0 and py < 0 else IRON     # boss (the dome sits on top)
        c = (226, 232, 236) if (px < 0) == (py < 0) else (52, 86, 150)   # quartered white / blue
        # the rune wolf: a white zig-zag across the blue quarters, a blue one across the white
        if abs(py - px * 0.0) < 0.9 and 3 < abs(px) < SH_R - 2:
            c = (52, 86, 150) if c[0] > 200 else (226, 232, 236)
        if abs(px) < 0.9 and 3 < abs(py) < SH_R - 2:
            c = (52, 86, 150) if c[0] > 200 else (226, 232, 236)
        if int(px + SH_R) % 4 == 0:
            c = mul(c, 0.82)                                # plank seams
        c = mul(c, 1.0 + (B.n(x, y + row_y, 11) - 0.5) * 0.1)
        if r > SH_R - 4 and B.n(int(px * 3), int(py * 3), 12) < 0.35:
            c = mix(c, ICE_L, 0.6)                          # frost crust near the rim
        return c
    return f


def blade_paint(f, x, y, w, h):
    """The axe blade: blue ice, darker toward the haft, lit facets, a white-hot frost edge."""
    if f == "top":
        return ICE_L
    if f == "bottom":
        return ICE_D
    t = x / max(1, w - 1) if f in ("front", "back") else 0.5
    c = mix(ICE_D, ICE, 0.4 + 0.6 * (1 - t)) if f == "front" else mix(ICE_D, ICE, 0.3 + 0.5 * t)
    if (x * 2 + y) % 7 == 0:
        c = mix(c, ICE_L, 0.5)
    return mul(c, 1.0 + (B.n(x, y, 91) - 0.5) * 0.1)


# ---------------------------------------------------------------- build
def build():
    m = Model("frost_jarl", seed=181, shadow=2.0, walk_speed=0.7, walk_scale=0.9, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -34, 0))
    m.part("skirt_f", "pelvis", pivot=(0, 3, -7), rot=(-4, 0, 0))
    m.part("skirt_b", "pelvis", pivot=(0, 3, 7), rot=(5, 0, 0))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -5, 0), rot=(4, 0, 0))
    m.part("cloak", "chest", pivot=(0, -24, 9), rot=(6, 0, 0))
    m.part("rime", "chest", pivot=(-9, -20, 8), rot=(-28, 0, 26))
    m.part("pelt", "chest", pivot=(9, -33, -6), rot=(0, -14, 6))
    m.part("head", "chest", pivot=(0, -30, -3), rot=(-4, 0, 0))
    m.part("jaw", "head", pivot=(0, -3, -4))
    m.part("braid", "jaw", pivot=(0, 14, -2), rot=(-6, 0, 0))
    m.part("horn_r", "head", pivot=(-7, -9, 0), rot=(0, 0, 0))
    m.part("horn_l", "head", pivot=(7, -9, 0), rot=(0, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(7 * sx, 0, 0), rot=(0, 0, -3 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 16, 0), rot=(0, 0, 3 * sx))
    m.part("arm_r", "chest", pivot=(-18, -22, 0), rot=(-8, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-26, 0, -6))
    m.part("axe", "fore_r", pivot=(0, 15, 0), rot=(40, 0, 0))
    m.part("arm_l", "chest", pivot=(18, -22, 0), rot=(-10, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-78, 0, 6))
    m.part("shield", "fore_l", pivot=(0, 19, 0), rot=(84, -18, 0))

    # ---- legs: wrapped leather leggings, fur boots with iron toe caps
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -5, -2, -5, 10, 18, 10, mail(2 + (sx > 0)))
        m.box(th, -5.5, 0, -5.5, 11, 8, 3, iron(4 + (sx > 0)))                        # thigh plate
        m.box(sh, -4.5, -1, -4.5, 9, 11, 9, leather(6 + (sx > 0)))
        m.box(sh, -5, -2, -6, 10, 5, 3, iron(8))                                         # knee cop
        m.box(sh, -6, 8, -6, 12, 3, 12, fur(9 + (sx > 0)))                              # boot cuff
        m.box(sh, -5.5, 10, -6.5, 11, 8, 12, fur(11, dark=True))                        # fur boot
        m.box(sh, -5.5, 15, -9, 11, 3, 3, iron(12))                                     # toe cap
        for k in range(2):                                                               # cross straps
            m.box(sh, -5, 1 + 4 * k, -5, 10, 1, 10, LEATHER_D)

    # ---- pelvis, mail skirt front and back, the belt and its gold knot
    m.box("pelvis", -11, -4, -7, 22, 8, 14, mail(14))
    m.box("skirt_f", -10, 0, -1, 20, 15, 2, mail(15))
    m.box("skirt_f", -4, 0, -1.5, 8, 13, 1, WOOL)                                       # a navy apron strip
    m.box("skirt_b", -10, 0, -1, 20, 16, 2, mail(16))
    m.box("waist", -12, -5, -8, 24, 6, 16, leather(17))
    m.box("waist", -3, -6, -9, 6, 7, 1, GOLD, glow={"front": lambda f, x, y, w, h: GOLD_L if (x + y) % 3 == 0 else None})
    m.box("waist", 8, -2, -8.5, 3, 9, 3, LEATHER_D)                                    # a horn pouch strap
    m.box("waist", 8.5, 6, -9, 4, 6, 4, (210, 196, 170))                                # drinking horn tip

    # ---- the torso: hauberk, breastplate, fur mantle, the wolf pelt, the cloak
    m.box("chest", -14, -26, -8, 28, 26, 16, breast_paint)
    m.box("chest", -16, -29, -9, 32, 7, 19, fur(20))                                    # the fur mantle
    m.box("chest", -12, -31, -7, 24, 3, 14, fur(21))
    m.box("chest", -15, -23, 7, 30, 10, 3, fur(22, dark=True))                          # mantle's back drape
    m.box("pelt", -4, -3, -6, 8, 6, 9, fur(23))                                         # the wolf head on the left shoulder
    m.box("pelt", -2.5, -1, -10, 5, 4, 4, fur(24))                                      # snout
    m.box("pelt", -2, 3, -10, 4, 1, 4, (232, 232, 224))                                 # fangs
    m.box("pelt", -4, -5, -2, 2, 3, 2, fur(25, dark=True))                              # ears
    m.box("pelt", 2, -5, -2, 2, 3, 2, fur(25, dark=True))
    m.box("pelt", -3, -1, -6.5, 6, 1, 1, (30, 30, 34),
          glow={"front": lambda f, x, y, w, h: GLOW if x in (0, w - 1) else None})       # the wolf's eyes
    m.box("cloak", -14, 0, 0, 28, 46, 2, wool(26))

    # ---- the rime: ice crystals grown out of his right shoulder blade
    for (x, y, z, w, h, d, s) in ((-2, -14, -2, 4, 14, 4, 30), (2, -9, -1, 3, 9, 3, 31), (-5, -10, 0, 3, 10, 3, 32),
                                  (-1, -19, -1, 2, 6, 2, 33), (4, -5, 2, 2, 5, 2, 34)):
        m.box("rime", x, y, z, w, h, d, ice(s, bright=True), glow=ice_glow(s, 0.18))

    # ---- head: frozen face, iron helm with a nasal, a crown of ice spikes; the beard on the jaw
    m.box("head", -6, -11, -6, 12, 11, 12, face_paint, glow=face_glow)
    m.box("head", -6.5, -13, -6.5, 13, 7, 13, iron(40, rime=0.25))                       # helm bowl
    m.box("head", -4.5, -15, -4.5, 9, 2, 9, iron(41, rime=0.3))
    m.box("head", -7, -7, -7, 14, 1, 14, GOLD_D)                                        # brow band
    m.box("head", -1, -7, -7.5, 2, 5, 1, IRON_L)                                        # nasal
    m.box("head", -7, -7, -4, 1, 6, 9, iron(42))                                        # cheek guards
    m.box("head", 6, -7, -4, 1, 6, 9, iron(43))
    for i, (x, z, hgt) in enumerate(((-4, -4, 5), (-1, -5, 8), (2, -4, 5), (4, -1, 4), (-5, -1, 4), (-1, 2, 5))):
        m.box("head", x, -15 - hgt, z, 2, hgt, 2, ice(44 + i, bright=True), glow=ice_glow(44 + i, 0.3))
    m.box("jaw", -5, -1, -2.5, 10, 3, 3, mouth_paint, glow=mouth_glow)
    m.box("jaw", -6, 1, -3.5, 12, 14, 5, beard_paint(50))                                 # the beard
    m.box("jaw", -7, -3, -1, 2, 10, 3, beard_paint(51))                                 # side whiskers
    m.box("jaw", 5, -3, -1, 2, 10, 3, beard_paint(52))
    m.box("braid", -2.5, 0, -2, 5, 10, 4, beard_paint(53))
    m.box("braid", -3, 4, -2.5, 6, 2, 5, GOLD)                                          # beard ring
    m.box("braid", -1, 10, -1, 2, 4, 2, ice(54), glow=ice_glow(54, 0.4))                # icicles
    for x in (-5, 3):
        m.box("jaw", x, 15, -2, 2, 3, 2, ice(55 + x), glow=ice_glow(55 + x, 0.35))
    # horns: the right one whole and curving up, the left one snapped
    m.box("horn_r", -4, -2, -2, 4, 4, 4, (214, 204, 180))
    m.box("horn_r", -7, -6, -1.5, 4, 5, 3, (226, 216, 194))
    m.box("horn_r", -8, -12, -1, 3, 6, 2, (236, 230, 212))
    m.box("horn_r", -8, -15, -0.5, 2, 3, 1, ICE_L)
    m.box("horn_l", 0, -2, -2, 4, 4, 4, (214, 204, 180))
    m.box("horn_l", 3, -4, -1.5, 3, 3, 3, (180, 170, 150))                              # the jagged stump

    # ---- right arm: bare frozen arm with a gold ring, iron pauldron on fur, leather bracer; the axe
    m.box("arm_r", -8, -6, -7, 13, 9, 14, iron(60, rime=0.25))
    m.box("arm_r", -9, -3, -7.5, 2, 6, 15, fur(61))                                     # fur trim
    m.box("arm_r", -4.5, 0, -4.5, 9, 14, 9, skin(62))
    m.box("arm_r", -5, 9, -5, 10, 2, 10, GOLD)                                          # arm ring
    m.box("fore_r", -5, 0, -5, 10, 12, 10, leather(63))
    m.box("fore_r", -5.5, 2, -5.5, 11, 6, 11, iron(64))                                 # bracer
    m.box("fore_r", -4.5, 12, -4.5, 9, 6, 9, skin(65))                                  # fist
    # the Dane axe: a long ash haft wrapped in leather, gold collars, a bearded crescent of ice
    m.box("axe", -1.5, -14, -1.5, 3, 46, 3, B.rod(WOOD, 70))
    m.box("axe", -2, -15, -2, 4, 2, 4, GOLD)                                            # pommel
    m.box("axe", -2, -6, -2, 4, 8, 4, leather(71))                                      # grip
    m.box("axe", -2, 18, -2, 4, 2, 4, GOLD)
    m.box("axe", -2, 30, -2, 4, 3, 4, GOLD_D)
    # the bearded crescent of ice: a narrow neck, a broad body, a long curved edge
    m.box("axe", -1, 22, -6, 2, 6, 4, blade_paint)                                      # neck
    m.box("axe", -1, 19, -11, 2, 13, 5, blade_paint, glow=ice_glow(72, 0.10))           # body
    m.box("axe", -1, 16, -15, 2, 20, 4, blade_paint, glow=ice_glow(73, 0.10))           # outer blade
    m.box("axe", -1, 14, -15, 2, 2, 2, blade_paint)                                     # upper horn
    m.box("axe", -1, 36, -14, 2, 3, 2, blade_paint)                                     # the beard's hook
    m.box("axe", -1.5, 17, -16, 3, 18, 1, ICE_L, glow={"side": lambda f, x, y, w, h: GLOW if (y + x) % 3 else GLOW_L,
                                                      "front": GLOW_L})                # the glowing edge
    m.box("axe", -1.5, 22, 1.5, 3, 4, 4, iron(74))                                      # back spike
    m.box("axe", -1, 23, 5.5, 2, 2, 2, IRON_L)

    # ---- left arm: pauldron, bare arm, bracer; the round shield on the forearm
    m.box("arm_l", -5, -6, -7, 13, 9, 14, iron(80, rime=0.25))
    m.box("arm_l", -4.5, 0, -4.5, 9, 14, 9, skin(81))
    m.box("arm_l", -5, 4, -5, 10, 2, 10, GOLD)
    m.box("fore_l", -5, 0, -5, 10, 12, 10, leather(82))
    m.box("fore_l", -5.5, 3, -5.5, 11, 6, 11, iron(83))
    m.box("fore_l", -4.5, 12, -4.5, 9, 6, 9, skin(84))
    for k in range(-SH_R, SH_R, 2):
        mid = k + 1
        half = int(round(math.sqrt(max(0.0, SH_R ** 2 - mid ** 2))))
        if half <= 1:
            continue
        m.box("shield", -half, k, -1, 2 * half, 2, 2, shield_front(k, half))
    m.box("shield", -3, -3, -3, 6, 6, 2, iron(85))                                      # boss
    m.box("shield", -2, -2, -3.5, 4, 4, 1, IRON_L)
    m.box("shield", -2, -6, 1, 4, 12, 1, LEATHER_D)                                     # strap behind
    for (x, ln) in ((-6, 4), (-2, 6), (3, 5), (7, 3)):
        m.box("shield", x, SH_R - 2, -1, 1, ln, 1, ice(90 + x), glow=ice_glow(90 + x, 0.3))   # icicles

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.4, (0, 6, 0)), (2.6, (0, 6, 0)), (3.4, (0, -5, 0)), (4.0, (0, 0, 0)))
    idle.rot("cloak", (0, (0, 0, 0)), (2.0, (4, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("braid", (0, (0, 0, 0)), (2.0, (4, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.0, (-3, 0, 0)), (1.6, (0, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("axe", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    walk.rot("thigh_r", (0, (22, 0, 0)), (0.9, (-22, 0, 0)), (1.8, (22, 0, 0)))
    walk.rot("thigh_l", (0, (-22, 0, 0)), (0.9, (22, 0, 0)), (1.8, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.45, (28, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (1.35, (28, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_r", (0, (-8, 0, 0)), (0.9, (8, 0, 0)), (1.8, (-8, 0, 0)))
    walk.rot("arm_l", (0, (6, 0, 0)), (0.9, (-6, 0, 0)), (1.8, (6, 0, 0)))
    walk.rot("chest", (0, (0, 4, 0)), (0.9, (0, -4, 0)), (1.8, (0, 4, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -1.2, 0)), (0.9, (0, 0, 0)), (1.35, (0, -1.2, 0)), (1.8, (0, 0, 0)))
    walk.rot("cloak", (0, (10, 0, 0)), (0.45, (16, 0, 0)), (0.9, (10, 0, 0)), (1.35, (16, 0, 0)), (1.8, (10, 0, 0)))
    walk.rot("skirt_f", (0, (-6, 0, 0)), (0.9, (6, 0, 0)), (1.8, (-6, 0, 0)))

    # cleave: the axe hauled up and back over his right shoulder (0.9 s = 18 ticks), then a diagonal cut down across
    # his front from right to left
    a = m.anim("cleave", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-150, -20, 30)), (0.9, (-158, -22, 32)), (1.02, (-40, 40, -10), "linear"),
          (1.25, (-34, 44, -14)), (1.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (1.02, (10, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.9, (-30, 0, 0)), (1.02, (20, 0, 0), "linear"), (1.25, (20, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-8, 30, 0)), (1.02, (16, -30, 0), "linear"), (1.25, (14, -32, 0)),
          (1.8, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.9, (0, 10, 0)), (1.02, (0, -12, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-10, 0, -20)), (1.02, (10, 0, 10), "linear"), (1.8, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.9, (12, 0, 0)), (1.02, (-14, 0, 4), "linear"), (1.8, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (1.02, (12, 0, -4), "linear"), (1.8, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (0.9, (8, 0, -6)), (1.1, (18, 0, 8)), (1.8, (0, 0, 0)))

    # bash: the shield raised square before him, the shoulder dropped (0.6 s = 12 ticks), then a heavy shove
    a = m.anim("bash", 1.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-18, 0, 12)), (0.6, (-20, 0, 14)), (0.68, (-56, 0, 6), "linear"),
          (0.9, (-54, 0, 6)), (1.5, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.6, (12, 0, 0)), (0.68, (34, 0, 0), "linear"), (0.9, (34, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (10, -24, 0)), (0.68, (18, 14, 0), "linear"), (0.9, (16, 12, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (10, 18, 0)), (0.68, (6, -8, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (14, 0, 16)), (0.68, (24, 0, 10), "linear"), (1.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.6, (-28, 0, 0)), (0.68, (-36, 0, 0), "linear"), (0.9, (-34, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.6, (26, 0, 0)), (0.68, (20, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (0.68, (24, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.6, (0, -2, 1)), (0.68, (0, -2, -5), "linear"), (0.9, (0, -2, -5)), (1.5, (0, 0, 0)))

    # breath: he rears back, chest swelling, jaw clenched as the cold gathers (1.0 s = 20 ticks), then the jaw drops
    # and the ice breath pours out, his head turning from his right to his left for 1.5 s
    a = m.anim("breath", 3.2)
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-22, 0, 0)), (1.0, (-24, 0, 0)), (1.08, (6, 18, 0), "linear"),
          (2.5, (6, -18, 0)), (3.2, (0, 0, 0)))
    a.scale("chest", (0, (1, 1, 1)), (1.0, (1.06, 1.04, 1.08)), (1.1, (1, 1, 1)), (3.2, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-26, 0, 0)), (1.08, (2, 22, 0), "linear"), (2.5, (2, -22, 0)), (3.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (-32, 0, 0), "linear"), (2.5, (-30, 0, 0)), (2.7, (0, 0, 0)),
          (3.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-10, 0, 34)), (2.5, (-10, 0, 30)), (3.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-30, 0, -36)), (2.5, (-30, 0, -30)), (3.2, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.0, (14, 0, 0)), (1.08, (-10, 0, 0), "linear"), (2.5, (-10, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.08, (8, 0, 0), "linear"), (2.5, (8, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("braid", (0, (0, 0, 0)), (1.08, (-30, 0, 0)), (1.3, (-20, 0, 8)), (2.5, (-24, 0, -8)), (3.2, (0, 0, 0)))

    # spikes: the axe raised high in both hands (1.1 s = 22 ticks), then driven into the floor before him; lines of
    # ice spikes run out from the blade
    a = m.anim("spikes", 3.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.95, (-170, 0, 14)), (1.1, (-174, 0, 12)), (1.2, (-58, 0, 2), "linear"),
          (2.3, (-60, 0, 4)), (3.0, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.1, (-10, 0, 0)), (1.2, (-18, 0, 0), "linear"), (2.3, (-18, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (1.1, (-40, 0, 0)), (1.2, (8, 0, 0), "linear"), (2.3, (8, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (-60, 0, -30)), (1.2, (-20, 0, -20), "linear"), (2.3, (-20, 0, -20)),
          (3.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-18, 0, 0)), (1.2, (28, 0, 0), "linear"), (2.3, (26, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-12, 0, 0)), (1.2, (-10, 0, 0), "linear"), (3.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1.5, 0)), (1.2, (0, -3, 0), "linear"), (2.3, (0, -3, 0)), (3.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-30, 0, -6 * sx), "linear"),
              (2.3, (-30, 0, -6 * sx)), (3.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (44, 0, 0), "linear"), (2.3, (44, 0, 0)),
              (3.0, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (1.1, (-6, 0, 0)), (1.3, (30, 0, 0)), (2.0, (12, 0, 0)), (3.0, (0, 0, 0)))

    # leap: he crouches, axe drawn back low (1.0 s = 20 ticks), springs (airborne 1.0-1.5 s, axe raised overhead) and
    # crashes down on his mark at 1.5 s
    a = m.anim("leap", 2.3)
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, -7, 0)), (1.0, (0, -8, 0)), (1.1, (0, 2, 0), "linear"), (1.45, (0, 1, 0)),
          (1.5, (0, -4, 0), "linear"), (1.9, (0, -4, 0)), (2.3, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.8, (-50, 0, -6 * sx)), (1.0, (-54, 0, -6 * sx)),
              (1.1, (10, 0, 0), "linear"), (1.4, (-30, 0, 0)), (1.5, (-36, 0, -6 * sx), "linear"),
              (1.9, (-34, 0, -6 * sx)), (2.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.8, (70, 0, 0)), (1.0, (74, 0, 0)), (1.1, (10, 0, 0), "linear"),
              (1.4, (40, 0, 0)), (1.5, (50, 0, 0), "linear"), (1.9, (48, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (30, 0, 0)), (1.1, (-14, 0, 0), "linear"), (1.45, (-16, 0, 0)),
          (1.5, (30, 0, 0), "linear"), (1.9, (26, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (40, 0, 20)), (1.1, (-150, 0, 10), "linear"), (1.45, (-172, 0, 10)),
          (1.5, (-60, 0, 4), "linear"), (1.9, (-62, 0, 4)), (2.3, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (1.45, (-30, 0, 0)), (1.5, (10, 0, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (20, 0, -20)), (1.1, (-80, 0, -40), "linear"), (1.5, (-30, 0, -30)),
          (2.3, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.2, (60, 0, 0)), (1.45, (50, 0, 0)), (1.6, (-10, 0, 0)),
          (2.3, (0, 0, 0)))

    # huscarls: the axe thrust to the sky, a bellow (0.8 s = 16 ticks), then slammed haft-first on the floor: his
    # frozen huscarls rise from the ice
    a = m.anim("huscarls", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-176, 0, 8)), (0.8, (-178, 0, 6)), (0.9, (-40, 0, 10), "linear"),
          (1.3, (-38, 0, 10)), (1.8, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.8, (-20, 0, 0)), (0.9, (-28, 0, 0), "linear"), (1.3, (-28, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-30, 0, 0)), (0.9, (6, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.3, (-28, 0, 0)), (0.8, (-30, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-16, 0, 0)), (0.9, (10, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-20, 0, -40)), (0.9, (0, 0, -20), "linear"), (1.8, (0, 0, 0)))

    # rampage (phase 2): three blows in a row, each with its own wind-up: a right-to-left cleave at 0.8 s
    # (16 ticks), a left-to-right backhand at 1.3 s, an overhead chop at 1.9 s
    a = m.anim("rampage", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-140, -20, 40)), (0.8, (-146, -22, 42)), (0.9, (-40, 50, -14), "linear"),
          (1.15, (-60, 60, -30)), (1.3, (-50, -50, 40), "linear"), (1.65, (-150, 0, 14)), (1.75, (-172, 0, 12)),
          (1.9, (-56, 0, 4), "linear"), (2.4, (-58, 0, 4)), (3.1, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.8, (-30, 0, 0)), (0.9, (20, 0, 0), "linear"), (1.3, (20, 0, 0)),
          (1.75, (-36, 0, 0)), (1.9, (8, 0, 0), "linear"), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, 30, 0)), (0.9, (12, -30, 0), "linear"), (1.15, (6, -36, 0)),
          (1.3, (8, 30, 0), "linear"), (1.75, (-18, 0, 0)), (1.9, (28, 0, 0), "linear"), (2.4, (26, 0, 0)),
          (3.1, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, 10, 0)), (0.9, (0, -12, 0), "linear"), (1.3, (0, 12, 0), "linear"),
          (1.9, (0, 0, 0), "linear"), (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-10, 0, -24)), (1.3, (-30, 0, -40)), (1.9, (-20, 0, -20)), (3.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.75, (0, 1, 0)), (1.9, (0, -3, 0), "linear"), (2.4, (0, -3, 0)), (3.1, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.8, (10 * sx, 0, 0)), (1.3, (-10 * sx, 0, 0)), (1.75, (0, 0, 0)),
              (1.9, (-30, 0, -6 * sx), "linear"), (2.4, (-30, 0, -6 * sx)), (3.1, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.75, (0, 0, 0)), (1.9, (44, 0, 0), "linear"), (2.4, (44, 0, 0)),
              (3.1, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (0.9, (14, 0, 10)), (1.4, (14, 0, -10)), (1.95, (30, 0, 0)), (3.1, (0, 0, 0)))

    # rimeburst (phase 2): the axe spun once and planted upright before him, both hands on the pommel (1.1 s = 22
    # ticks); rings of ice spikes burst outward from it one after another
    a = m.anim("rimeburst", 3.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-120, 0, 20)), (0.95, (-90, 30, 10)), (1.1, (-62, 24, 0)),
          (1.2, (-50, 20, -6), "linear"), (2.9, (-50, 20, -6)), (3.6, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.5, (-120, 0, 0)), (0.95, (-60, 0, 0)), (1.1, (-46, 0, 0)), (1.2, (-40, 0, 0), "linear"),
          (2.9, (-40, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (-60, -30, 0)), (1.2, (-50, -36, 0), "linear"), (2.9, (-50, -36, 0)),
          (3.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-12, 0, 0)), (1.2, (18, 0, 0), "linear"), (2.9, (16, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (-6, 0, 0), "linear"), (3.6, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1, 0)), (1.2, (0, -3, 0), "linear"), (2.9, (0, -3, 0)), (3.6, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (1.2, (24, 0, 0)), (1.6, (40, 0, 0)), (2.2, (30, 0, 6)), (2.9, (36, 0, -6)),
          (3.6, (0, 0, 0)))

    # winter (phase 3, invulnerable): he sinks to one knee, axe raised in both hands as the frost climbs him (1.5 s
    # = 30 ticks), then drives it into the floor: the hall freezes over
    a = m.anim("winter", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -13, 0)), (1.5, (0, -13, 0)), (1.6, (0, -14, 0), "linear"), (2.8, (0, -13, 0)),
          (3.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.4, (-78, 0, 0)), (2.8, (-78, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (78, 0, 0)), (2.8, (78, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.4, (18, 0, 0)), (2.8, (18, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (80, 0, 0)), (2.8, (80, 0, 0)), (3.5, (0, 0, 0)))
    shake = [(0.4 + 0.1 * i, (-170 + (4 if i % 2 else -4), 0, 10)) for i in range(11)]
    a.rot("arm_r", (0, (0, 0, 0)), *shake, (1.6, (-52, 0, 4), "linear"), (2.8, (-54, 0, 4)), (3.5, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (1.5, (-40, 0, 0)), (1.6, (10, 0, 0), "linear"), (2.8, (10, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-150, 0, -20)), (1.5, (-155, 0, -20)), (1.6, (-30, 0, -40), "linear"),
          (2.8, (-30, 0, -40)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-16, 0, 0)), (1.6, (30, 0, 0), "linear"), (2.8, (28, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-30, 0, 0)), (1.6, (-34, 0, 0), "linear"), (2.8, (-30, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (-34, 0, 0), "linear"), (2.6, (-30, 0, 0)), (3.5, (0, 0, 0)))
    a.scale("rime", (0, (1, 1, 1)), (1.5, (1.2, 1.25, 1.2)), (1.6, (1.45, 1.55, 1.45), "linear"), (3.5, (1, 1, 1)))
    a.rot("cloak", (0, (0, 0, 0)), (1.5, (10, 0, 0)), (1.7, (40, 0, 0)), (2.4, (20, 0, 0)), (3.5, (0, 0, 0)))

    # blizzard (phase 3, spectacle): the axe raised to the oculus, turning, the storm gathering (1.2 s = 24 ticks);
    # then held high while ice spikes rain from the blizzard
    a = m.anim("blizzard", 4.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-176, 0, 10)), (1.2, (-178, 0, 6)), (1.28, (-172, 0, 18), "linear"),
          (3.2, (-170, 0, 16)), (4.0, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0), "linear"), (0.6, (0, 0, 0), "linear"), (1.2, (0, 720, 0), "linear"),
          (1.28, (0, 720, 0), "linear"), (3.2, (0, 720, 0)), (4.0, (0, 720, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-34, 0, 0)), (3.2, (-30, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.2, (-10, 0, 0)), (1.28, (-30, 0, 0), "linear"), (3.2, (-26, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-18, 0, 0)), (3.2, (-14, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.2, (-40, 0, -50)), (3.2, (-40, 0, -45)), (4.0, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (0.6, (20, 0, 10)), (1.2, (30, 0, -10)), (2.0, (36, 0, 10)), (2.8, (30, 0, -10)),
          (4.0, (0, 0, 0)))

    # roar (phase two): axe and shield flung wide, head thrown back, the jaw open
    a = m.anim("roar", 2.0)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-40, 0, -55 * sx)), (1.6, (-45, 0, -60 * sx)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cloak", (0, (0, 0, 0)), (0.6, (30, 0, 0)), (1.1, (40, 0, 8)), (1.6, (30, 0, -8)), (2.0, (0, 0, 0)))

    # stagger: the frost cracks: he sags onto one knee, axe head on the floor, the shield dropped
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -13, 0)), (1.2, (0, -13, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (-78, 0, 0)), (1.2, (-78, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (78, 0, 0)), (1.2, (78, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (18, 0, 0)), (1.2, (18, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.2, (80, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, -8)), (1.2, (28, 0, -8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 10)), (1.2, (26, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (10, 0, 14)), (1.2, (12, 0, 14)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (40, 0, -16)), (1.2, (42, 0, -16)), (1.6, (0, 0, 0)))
