"""The Abbess of the Tides (L'Abbesse des Marées): the drowned saint of the Tidal Abbey, about 5.4 blocks tall.

Silhouette idea: a tall, stooped abbess who walked into the sea at the last high tide and came back up the stair of
her own church. Her long robe of sea-dark linen falls to the floor without a seam, so she glides; its hem is torn into
rags and trails kelp. Over it a faded crimson chasuble with a tarnished gold orphrey cross, crusted with barnacles. A
wimple and a long veil of grey-green linen frame a drowned face (grey-green skin, two sea-glass eyes that glow),
and a crown of red, orange and violet coral has grown through the veil.
Strong asymmetry: in her RIGHT hand a tall crozier of black driftwood banded in verdigris, its crook a great nautilus
shell spiral with a sea-glass lamp hanging inside the curl; from her LEFT hand a bell-censer swings on a long chain:
a bronze bell with a pierced lid, brine smoke glowing inside. A cluster of barnacles and a starfish have taken her
right shoulder; long strands of kelp hang from her left hip and her right sleeve.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

LINEN = (40, 84, 90)          # the robe: sea-dark linen
LINEN_L = (70, 122, 124)
LINEN_D = (22, 48, 56)
ALGAE = (58, 98, 62)
CRIMSON = (110, 44, 60)       # the chasuble, faded by the sea
CRIMSON_L = (150, 70, 82)
CRIMSON_D = (66, 26, 40)
GOLD = (196, 160, 80)
GOLD_L = (236, 210, 130)
GOLD_D = (130, 100, 46)
VERDI = (92, 156, 132)        # verdigris
VERDI_L = (150, 206, 180)
VEIL = (186, 198, 184)
VEIL_L = (222, 230, 216)
VEIL_D = (128, 146, 134)
SKIN = (124, 148, 136)
SKIN_L = (160, 184, 168)
SKIN_D = (78, 100, 92)
GLASS = (110, 238, 214)       # sea glass
GLASS_L = (210, 255, 244)
BARN = (204, 200, 184)        # barnacles
BARN_D = (120, 116, 104)
CORAL_R = (214, 64, 72)
CORAL_O = (236, 132, 58)
CORAL_V = (170, 82, 176)
WOOD = (70, 60, 52)           # black driftwood
WOOD_D = (40, 34, 30)
NACRE = (232, 216, 184)
NACRE_D = (150, 92, 62)
NACRE_P = (246, 236, 226)
BRONZE = (156, 110, 62)
BRONZE_D = (92, 62, 34)
BRONZE_L = (210, 162, 98)
KELP = (64, 112, 44)
KELP_D = (38, 72, 30)
STAR = (230, 120, 60)


# ---------------------------------------------------------------- paint
def barnacles(c, x, y, seed, amount=0.08):
    """A few barnacles over a colour: a pale ring with a dark mouth."""
    r = B.n(x // 2, y // 2, seed)
    if r < amount:
        return BARN_D if (x + y) % 2 else BARN
    return c


def linen(seed=0, ragged=False, algae=0.25):
    """Sea-dark linen: vertical folds, algae creeping up from the hem, a few barnacles, a torn hem."""
    def f(face, x, y, w, h):
        if face == "top":
            return LINEN_D
        if face == "bottom":
            return None if ragged else LINEN_D
        if ragged:
            cut = h - 1 - int(B.n(x, 0, seed) * 5)
            if y > cut:
                return None
        fold = 0.10 if x % 5 == 1 else (-0.08 if x % 5 == 3 else 0.0)
        k = 1.06 - 0.20 * y / max(1, h) + fold + (B.n(x, y, seed) - 0.5) * 0.06
        c = mul(LINEN, k)
        low = y / max(1, h)
        if B.n(x, y // 2, seed + 3) < algae * low * low:
            c = mix(c, ALGAE, 0.6)
        if y > 0 and B.n(x * 3, y, seed + 5) < 0.02:
            c = LINEN_L
        return barnacles(c, x, y, seed + 7, 0.02)
    return f


def chasuble(seed=0, cross=True):
    """Faded crimson chasuble: a tarnished gold orphrey cross (the Y of the vestment), barnacles over it."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return CRIMSON_D
        cx = (w - 1) / 2
        dx = abs(x - cx)
        c = mul(CRIMSON, 1.04 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        if cross and face in ("front", "back"):
            band = dx <= 1.6 or (6 <= y <= 8 and dx <= w * 0.42)
            if band:
                edge = dx > 1.0 and not (6 <= y <= 8) or y in (6, 8) and dx > 1.6
                c = GOLD_D if edge else (GOLD_L if (x + y) % 4 == 0 else GOLD)
                if B.n(x, y, seed + 2) < 0.30:
                    c = mix(c, VERDI, 0.65)
        if face != "top" and y >= h - 2:
            c = mix(c, GOLD_D, 0.5) if y == h - 1 else c          # a dull gold hem line
        return barnacles(c, x, y, seed + 9, 0.022)
    return f


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        k = 1.05 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.10
        c = mul(SKIN, k)
        if B.n(x, y, seed + 4) < 0.06:
            return SKIN_D                                           # sea rot
        return c
    return f


def veil(seed=0, edge=True):
    def f(face, x, y, w, h):
        if face == "bottom":
            return VEIL_D
        if face == "top":
            return VEIL_L
        k = 1.04 - 0.16 * y / max(1, h) + (0.06 if x % 4 == 0 else 0.0) + (B.n(x, y, seed) - 0.5) * 0.05
        c = mul(VEIL, k)
        if edge and (x == 0 or x == w - 1):
            c = mul(VEIL, 0.8)
        if B.n(x, y // 3, seed + 6) < 0.10 * (y / max(1, h)):
            c = mix(c, ALGAE, 0.4)
        return c
    return f


def long_veil(seed=0):
    """The veil down her back: torn at the bottom."""
    base = veil(seed)

    def f(face, x, y, w, h):
        if face in ("front", "back", "left", "right"):
            cut = h - 1 - int(B.n(x, 0, seed) * 6)
            if y > cut:
                return None
        return base(face, x, y, w, h)
    return f


def face_paint(f, x, y, w, h):
    """The drowned face: grey-green, hollow cheeks, two sea-glass eyes, a thin lipless mouth."""
    if f != "front":
        return skin(80)(f, x, y, w, h)
    if y in (3, 4) and x in (2, 3, w - 4, w - 3):
        return GLASS_L if y == 3 else GLASS
    if y == 2 and 1 <= x <= w - 2 and x not in (w // 2 - 1, w // 2):
        return SKIN_D                                               # brows
    if y == 5 and x in (2, 3, w - 4, w - 3):
        return SKIN_D                                               # sunken under-eyes
    if y in (6, 7) and x in (1, w - 2):
        return SKIN_D                                               # hollow cheeks
    if y == 8 and w // 2 - 2 <= x <= w // 2 + 1:
        return (40, 46, 44)
    if y == 5 and x in (w // 2 - 1, w // 2):
        return SKIN_L                                               # the nose
    return skin(81)(f, x, y, w, h)


def face_glow(f, x, y, w, h):
    if f == "front" and y in (3, 4) and x in (2, 3, w - 4, w - 3):
        return GLASS_L if y == 3 else GLASS
    return None


def coral(colour, seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return mix(colour, (255, 240, 230), 0.35)
        k = 1.05 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12
        c = mul(colour, k)
        if (x + y * 2) % 5 == 0:
            c = mul(colour, 0.72)                                   # polyps
        return c
    return f


def wood(seed=0):
    return B.rod(WOOD, seed)


def verdigris(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        c = GOLD_L if y == 0 else GOLD
        if B.n(x, y, seed) < 0.45:
            c = mix(c, VERDI, 0.7)
        return c
    return f


def nacre(seed=0, stripe=True):
    """Nautilus shell: cream nacre with brown tiger stripes, pearly highlights on top."""
    def f(face, x, y, w, h):
        if face == "top":
            return NACRE_P
        if face == "bottom":
            return mul(NACRE, 0.8)
        c = NACRE
        if stripe and (x + seed) % 4 == 0:
            c = mix(NACRE, NACRE_D, 0.75)
        return mul(c, 1.04 - 0.12 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
    return f


def bronze(seed=0):
    base = B.plate(BRONZE, BRONZE_D, BRONZE_L, seed=seed, grad=0.2, worn=0.1)

    def f(face, x, y, w, h):
        c = base(face, x, y, w, h)
        if c is not None and B.n(x, y, seed + 3) < 0.28:
            return mix(c, VERDI, 0.6)
        return c
    return f


def censer_lid(face, x, y, w, h):
    """The pierced lid: bronze with a ring of holes where the brine smoke glows."""
    if face in ("top", "front", "back", "left", "right") and (x + y) % 3 == 1 and 0 < x < w - 1:
        return (30, 60, 56)
    return bronze(40)(face, x, y, w, h)


def censer_glow(face, x, y, w, h):
    if face in ("top", "front", "back", "left", "right") and (x + y) % 3 == 1 and 0 < x < w - 1:
        return GLASS
    return None


def kelp(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return KELP_D
        c = KELP if (y // 2 + x) % 3 else KELP_D
        if (y + seed) % 7 == 0:
            c = mix(KELP, (190, 170, 60), 0.4)                     # a bladder
        return c
    return f


def barnacle_paint(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return BARN_D if (x + y) % 2 else (70, 66, 60)          # the open mouth
        return mul(BARN, 1.0 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
    return f


# ---------------------------------------------------------------- build
def build():
    m = Model("tide_abbess", seed=227, shadow=1.8, walk_speed=0.7, walk_scale=0.8, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -36, 0))
    m.part("robe", "pelvis", pivot=(0, 0, 0))
    m.part("hem", "robe", pivot=(0, 28, 0))
    m.part("kelp_hip", "pelvis", pivot=(11, 2, -2), rot=(0, 0, -4))
    m.part("waist", "pelvis", pivot=(0, -2, 0))
    m.part("chest", "waist", pivot=(0, -4, 0), rot=(10, 0, 0))
    m.part("front_panel", "chest", pivot=(0, -2, -8), rot=(-8, 0, 0))
    m.part("back_panel", "chest", pivot=(0, -4, 7), rot=(6, 0, 0))
    m.part("head", "chest", pivot=(0, -24, -2), rot=(6, 0, 0))
    m.part("veil", "head", pivot=(0, -4, 6), rot=(-16, 0, 0))
    m.part("crown", "head", pivot=(0, -12, 0))
    m.part("barnacles", "chest", pivot=(-12, -22, 0))
    m.part("arm_r", "chest", pivot=(-14, -20, 0), rot=(-6, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-52, 0, -4))
    m.part("kelp_sleeve", "fore_r", pivot=(-3, 10, 3), rot=(52, 0, 0))
    m.part("crozier", "fore_r", pivot=(0, 13, 0), rot=(58, 0, 0))
    m.part("crook", "crozier", pivot=(0, -42, 0))
    m.part("lamp", "crook", pivot=(0, -11, -6))
    m.part("arm_l", "chest", pivot=(14, -20, 0), rot=(-14, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-38, 0, 4))
    m.part("chain", "fore_l", pivot=(0, 13, -1), rot=(52, 0, 10))
    m.part("censer", "chain", pivot=(0, 16, 0))

    # ---- the robe: three widening drums of linen to the floor, a torn hem that sways
    m.box("pelvis", -10, -4, -7, 20, 8, 14, linen(1, algae=0.0))
    m.box("robe", -11, 4, -8, 22, 10, 16, linen(2, algae=0.1))
    m.box("robe", -12, 14, -9, 24, 10, 18, linen(3, algae=0.2))
    m.box("robe", -13, 24, -10, 26, 5, 20, linen(4, algae=0.35))
    m.box("hem", -14, 0, -11, 28, 8, 22, linen(5, ragged=True, algae=0.6))
    for i, (x, z) in enumerate(((-13, -9), (9, -10), (-5, 9), (11, 6), (2, -11))):
        m.box("hem", x, 2, z, 2, 2, 2, barnacle_paint(10 + i))           # barnacles on the hem
    # kelp strands from the left hip
    m.box("kelp_hip", 0, 0, -1, 2, 30, 1, kelp(1))
    m.box("kelp_hip", 2, 4, 1, 1, 24, 1, kelp(4))
    m.box("kelp_hip", -1, 2, 2, 1, 20, 1, kelp(6))

    # ---- the torso: an alb of linen, the crimson chasuble over it, a gold orphrey, barnacles
    m.box("waist", -10, -6, -7, 20, 8, 14, linen(6, algae=0.0))
    m.box("waist", -11, -2, -7.5, 22, 2, 15, GOLD_D)                        # the cincture
    m.box("waist", 7, 0, -8, 2, 9, 1, GOLD_D)                               # its tassel
    m.box("chest", -12, -22, -7, 24, 22, 14, chasuble(20, cross=False))
    m.box("chest", -14, -24, -8, 28, 6, 16, chasuble(21, cross=False))       # the shoulders
    m.box("front_panel", -9, 0, -1, 18, 30, 1, chasuble(22))
    m.box("back_panel", -10, 0, 0, 20, 30, 1, chasuble(23))
    m.box("chest", 4, -16, -8, 4, 4, 1, STAR, glow=None)                     # a starfish on the left breast
    m.box("chest", 5, -18, -8, 2, 8, 1, STAR)
    m.box("chest", 3, -15, -8, 6, 2, 1, STAR)
    # barnacles over the right shoulder
    for i, (x, y, z, s) in enumerate(((-2, -4, -5, 4), (1, -5, -1, 3), (-3, -3, 2, 3), (2, -3, 3, 2), (-1, -6, -2, 2),
                                      (3, -2, -6, 2), (-4, -1, -7, 2))):
        m.box("barnacles", x, y, z, s, s, s, barnacle_paint(30 + i))

    # ---- head: the drowned face, wimple and veil, a crown of coral grown through the veil
    m.box("head", -5, -10, -5, 10, 10, 10, face_paint, glow=face_glow)
    m.box("head", -6, -12, -6, 12, 3, 12, veil(40))                          # veil over the brow
    m.box("head", -6.5, -10, -5, 1, 12, 11, veil(41))                        # sides
    m.box("head", 5.5, -10, -5, 1, 12, 11, veil(42))
    m.box("head", -6, -10, 5, 12, 11, 2, veil(43))                           # back of the head
    m.box("head", -6, -1, -6, 12, 4, 11, veil(44, edge=False))               # the wimple under the chin
    m.box("head", -1, -11, -6.5, 2, 1, 1, GOLD)                              # a tarnished brow jewel
    m.box("veil", -7, 0, 0, 14, 34, 2, long_veil(45))
    for i, (x, z, hgt, col) in enumerate(((-4, -3, 6, CORAL_R), (-1, -4, 9, CORAL_O), (2, -3, 7, CORAL_V),
                                          (4, 0, 5, CORAL_R), (-5, 1, 5, CORAL_V), (0, 2, 6, CORAL_R),
                                          (-2, -1, 4, CORAL_O))):
        m.box("crown", x, -hgt, z, 2, hgt, 2, coral(col, 50 + i))
    for (x, y, z, col) in ((-6, -5, -3, CORAL_R), (4, -8, -4, CORAL_O), (2, -6, 1, CORAL_V), (-3, -7, 2, CORAL_O)):
        m.box("crown", x, y, z, 2, 1, 1, coral(col, 60))                     # side branches

    # ---- right arm: a wide sleeve, a bare drowned hand, the crozier
    m.box("arm_r", -5, -3, -5, 9, 15, 10, chasuble(70, cross=False))
    m.box("fore_r", -5, 0, -5, 10, 9, 10, linen(71, algae=0.3))              # the alb's sleeve
    m.box("fore_r", -6, 5, -6, 12, 5, 12, linen(72, ragged=True, algae=0.5))  # flared cuff
    m.box("fore_r", -2.5, 9, -2.5, 5, 5, 5, skin(73))                        # hand
    m.box("kelp_sleeve", 0, 0, 0, 1, 18, 1, kelp(2))
    m.box("kelp_sleeve", 1, 2, 1, 1, 12, 1, kelp(5))
    # the crozier: a black driftwood staff, verdigris bands, a nautilus crook with a sea-glass lamp in its curl
    m.box("crozier", -1, -42, -1, 2, 86, 2, wood(80))
    m.box("crozier", -1.5, 42, -1.5, 3, 3, 3, verdigris(81))                 # the ferrule
    for y in (-8, 8, 24):
        m.box("crozier", -1.5, y, -1.5, 3, 2, 3, verdigris(82 + y))
    m.box("crozier", -2, -46, -2, 4, 5, 4, verdigris(85))                    # the knop
    m.box("crozier", -2.5, -44, -2.5, 5, 2, 5, GOLD_D)
    # the nautilus: a spiral of shell segments rising off the knop, curling over forward and down, then in toward its
    # heart (u = forward, v = up, around a centre 6 forward and 8 up)
    for k in range(11):
        phi = math.radians(-127 - 30 * k)
        r = 9.5 * math.exp(-0.07 * k)
        u, v = 6 + r * math.cos(phi), 8 + r * math.sin(phi)
        size = 4 if k < 4 else (3 if k < 8 else 2)
        m.box("crook", -size / 2, -v - size / 2, -u - size / 2, size, size, size, nacre(90 + k))
    m.box("crook", -1, -2, -1.5, 2, 3, 3, nacre(110, stripe=False))          # the neck into the knop
    m.box("lamp", -0.5, 0, -0.5, 1, 3, 1, BRONZE_D)                          # chain of the lamp
    m.box("lamp", -1.5, 3, -1.5, 3, 4, 3, GLASS, glow=GLASS)                 # the sea-glass lamp
    m.box("lamp", -2, 2.5, -2, 4, 1, 4, BRONZE)

    # ---- left arm: the sleeve, the hand, the bell-censer on its chain
    m.box("arm_l", -4, -3, -5, 9, 15, 10, chasuble(74, cross=False))
    m.box("fore_l", -5, 0, -5, 10, 9, 10, linen(75, algae=0.3))
    m.box("fore_l", -6, 5, -6, 12, 5, 12, linen(76, ragged=True, algae=0.5))
    m.box("fore_l", -2.5, 9, -2.5, 5, 5, 5, skin(77))
    m.box("chain", -0.5, 0, -0.5, 1, 16, 1, {"side": lambda f, x, y, w, h: BRONZE_L if y % 2 else BRONZE_D,
                                              "*": BRONZE})
    m.box("censer", -1, 0, -1, 2, 2, 2, bronze(120))                         # the ring
    m.box("censer", -2, 2, -2, 4, 2, 4, censer_lid, glow=censer_glow)       # the pierced lid
    m.box("censer", -3, 4, -3, 6, 4, 6, censer_lid, glow=censer_glow)
    m.box("censer", -4, 8, -4, 8, 4, 8, bronze(121))                         # the bell's waist
    m.box("censer", -5, 12, -5, 10, 2, 10, bronze(122))                      # the flared lip
    m.box("censer", -1, 12, -1, 2, 3, 2, BRONZE_D)                           # the clapper
    m.box("censer", -4.5, 9, -4.5, 9, 1, 9, GOLD_D)                          # a gilt band

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (0, 8, 0)), (2.4, (4, 8, 0)), (3.4, (0, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("veil", (0, (0, 0, 0)), (2.0, (5, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 0)), (1.0, (10, 0, 4)), (2.0, (0, 0, 0)), (3.0, (-10, 0, -4)), (4.0, (0, 0, 0)))
    idle.rot("censer", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (0, 0, 0)), (3.0, (6, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("lamp", (0, (0, 0, 0)), (1.3, (8, 0, 6)), (2.6, (-6, 0, -4)), (4.0, (0, 0, 0)))
    idle.rot("kelp_hip", (0, (0, 0, 0)), (1.5, (8, 0, -6)), (3.0, (-6, 0, 4)), (4.0, (0, 0, 0)))
    idle.rot("kelp_sleeve", (0, (0, 0, 0)), (1.8, (-8, 0, 6)), (4.0, (0, 0, 0)))
    idle.rot("hem", (0, (0, 0, 0)), (2.0, (2, 0, 1)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("robe", (0, (0, 0, 2)), (1.0, (0, 0, -2)), (2.0, (0, 0, 2)))
    walk.rot("hem", (0, (-6, 0, 3)), (0.5, (6, 0, 0)), (1.0, (-6, 0, -3)), (1.5, (6, 0, 0)), (2.0, (-6, 0, 3)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, 0.8, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0.8, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 4, 0)), (1.0, (0, -4, 0)), (2.0, (0, 4, 0)))
    walk.rot("veil", (0, (14, 0, 0)), (1.0, (20, 0, 0)), (2.0, (14, 0, 0)))
    walk.rot("chain", (0, (14, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (14, 0, 0)))
    walk.rot("back_panel", (0, (8, 0, 0)), (1.0, (14, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("arm_l", (0, (6, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (6, 0, 0)))
    walk.rot("kelp_hip", (0, (12, 0, 0)), (1.0, (20, 0, 0)), (2.0, (12, 0, 0)))

    # sweep: the crozier drawn back over her right shoulder (0.8 s = 16 ticks), then swept across her front
    a = m.anim("sweep", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-60, -10, 70)), (0.8, (-66, -12, 74)), (0.92, (-70, 60, -30), "linear"),
          (1.15, (-62, 64, -34)), (1.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.92, (20, 0, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.8, (-50, 0, 20)), (0.92, (-60, 0, -10), "linear"), (1.15, (-58, 0, -12)),
          (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 32, 0)), (0.92, (8, -34, 0), "linear"), (1.15, (6, -36, 0)), (1.7, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, 12, 0)), (0.92, (0, -12, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.8, (8, 0, -10)), (1.0, (20, 0, 14)), (1.7, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.8, (0, 8, 0)), (1.0, (0, -10, 0)), (1.7, (0, 0, 0)))

    # censer: the bell-censer swung back low behind her (0.9 s = 18 ticks), then flung round in a wide arc in front
    a = m.anim("censer", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.75, (36, 0, -64)), (0.9, (40, 0, -68)), (1.05, (-76, -50, 20), "linear"),
          (1.3, (-70, -54, 24)), (1.9, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.9, (-40, 0, 40)), (1.05, (-80, 0, -40), "linear"), (1.3, (-60, 0, -50)),
          (1.9, (0, 0, 0)))
    a.rot("censer", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.05, (-30, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, -30, 0)), (1.05, (8, 34, 0), "linear"), (1.3, (6, 36, 0)), (1.9, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.9, (0, -10, 0)), (1.05, (0, 12, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.9, (6, 0, 12)), (1.1, (20, 0, -14)), (1.9, (0, 0, 0)))

    # tidewave: the crozier raised high in both hands (1.1 s = 22 ticks), then its foot struck on the floor: the tide
    # rises behind her and sweeps the hall
    a = m.anim("tidewave", 3.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-110, 0, 20)), (1.1, (-120, 0, 22)), (1.2, (-40, 0, 6), "linear"),
          (3.1, (-40, 0, 6)), (3.8, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.1, (130, 0, 0)), (1.2, (28, 0, 0), "linear"), (3.1, (28, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (-100, 0, -40)), (1.2, (-50, 0, -60), "linear"), (3.1, (-50, 0, -60)),
          (3.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (12, 0, 0), "linear"), (3.1, (10, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-30, 0, 0)), (1.2, (-4, 0, 0), "linear"), (3.8, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 2, 0)), (1.2, (0, -2, 0), "linear"), (3.1, (0, -2, 0)), (3.8, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (1.1, (-4, 0, 0)), (1.4, (22, 0, 0)), (2.2, (16, 0, 8)), (3.1, (18, 0, -8)),
          (3.8, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.5, (10, 0, 0)), (2.5, (8, 0, 0)), (3.8, (0, 0, 0)))

    # acolytes: the censer lifted and swung in a slow circle, her head bowed in prayer (0.9 s = 18 ticks), then the
    # crozier struck down: her drowned acolytes rise
    a = m.anim("acolytes", 1.8)
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (-90, 0, -30)), (0.9, (-100, 0, -20)), (1.0, (-40, 0, -30), "linear"),
          (1.8, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.3, (0, 0, 40)), (0.6, (40, 0, 0)), (0.9, (0, 0, -40)), (1.0, (20, 0, 0)),
          (1.8, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-40, 0, 16)), (1.0, (-10, 0, 8), "linear"), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (24, 0, 0)), (1.0, (-20, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (12, 0, 0)), (1.0, (-6, 0, 0), "linear"), (1.8, (0, 0, 0)))

    # toll: the bell-censer raised high over her coral crown (1.0 s = 20 ticks), then rung hard three times: the tide
    # draws everyone in (1.0 s), and the brine bursts round her at 1.8 s
    a = m.anim("toll", 2.7)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-160, 0, -10)), (1.0, (-170, 0, -8)), (1.05, (-150, 0, -16), "linear"),
          (1.35, (-170, 0, -8), "linear"), (1.4, (-150, 0, -16), "linear"), (1.7, (-170, 0, -8)),
          (1.8, (-110, 0, -40), "linear"), (2.2, (-100, 0, -40)), (2.7, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (1.0, (-50, 0, 0)), (1.05, (30, 0, 0), "linear"), (1.35, (-40, 0, 0), "linear"),
          (1.4, (30, 0, 0), "linear"), (1.7, (-30, 0, 0)), (1.8, (40, 0, 0), "linear"), (2.7, (0, 0, 0)))
    a.rot("censer", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.05, (30, 0, 0), "linear"), (1.35, (-30, 0, 0)),
          (1.4, (30, 0, 0), "linear"), (1.8, (0, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.8, (-26, 0, 0)), (2.0, (10, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, -6)), (1.8, (-12, 0, -6)), (1.9, (16, 0, 0), "linear"),
          (2.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-20, 0, 30)), (1.8, (-20, 0, 30)), (2.7, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (1.0, (6, 0, 0)), (1.9, (20, 0, 0)), (2.7, (0, 0, 0)))

    # surge: she leans into the tide, crozier levelled (0.7 s = 14 ticks), then glides forward point first
    a = m.anim("surge", 1.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-20, 0, 30)), (0.7, (-16, 0, 32)), (0.78, (-80, 0, 4), "linear"),
          (1.2, (-78, 0, 4)), (1.9, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.7, (40, 0, 0)), (0.78, (-24, 0, 0), "linear"), (1.2, (-24, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 20, 0)), (0.78, (24, -6, 0), "linear"), (1.2, (24, -6, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (10, 0, -20)), (0.78, (40, 0, -30), "linear"), (1.2, (40, 0, -30)), (1.9, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.78, (10, 0, 0)), (0.9, (30, 0, 0)), (1.2, (26, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.78, (0, 0, 0)), (0.9, (24, 0, 0)), (1.2, (20, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.78, (0, 0, 0)), (0.95, (60, 0, 0)), (1.3, (40, 0, 0)), (1.9, (0, 0, 0)))

    # baptism (phase 2): the crozier lifted, the lamp swinging, her free hand turned up (0.9 s = 18 ticks); then she
    # blesses the floor with it: geysers of brine burst where her rings close
    a = m.anim("baptism", 3.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-150, 0, 10)), (0.9, (-156, 0, 8)), (1.0, (-90, 0, 14), "linear"),
          (2.4, (-90, 0, 14)), (3.0, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.9, (158, 0, 0)), (1.0, (122, 0, 0), "linear"), (2.4, (122, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("lamp", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (0.9, (-30, 0, 0)), (1.0, (40, 0, 0)), (1.6, (-20, 0, 0)),
          (2.4, (10, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-60, 0, -50)), (1.0, (-30, 0, -70), "linear"), (2.4, (-30, 0, -70)),
          (3.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-24, 0, 0)), (1.0, (10, 0, 0), "linear"), (3.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (1.0, (8, 0, 0), "linear"), (2.4, (6, 0, 0)), (3.0, (0, 0, 0)))

    # thurible (phase 2): two swings of the censer: forehand from her left at 0.8 s (16 ticks), backhand at 1.4 s
    a = m.anim("thurible", 2.3)
    a.rot("arm_l", (0, (0, 0, 0)), (0.65, (30, 0, -70)), (0.8, (34, 0, -72)), (0.92, (-70, -50, 24), "linear"),
          (1.2, (-80, -60, 30)), (1.4, (-40, 50, -80), "linear"), (1.7, (-30, 50, -84)), (2.3, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.8, (-40, 0, 40)), (0.92, (-80, 0, -40), "linear"), (1.2, (-70, 0, -60)),
          (1.4, (-80, 0, 60), "linear"), (1.7, (-60, 0, 50)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (0, -30, 0)), (0.92, (8, 32, 0), "linear"), (1.2, (6, 36, 0)),
          (1.4, (8, -34, 0), "linear"), (1.7, (6, -36, 0)), (2.3, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, -10, 0)), (0.92, (0, 12, 0), "linear"), (1.4, (0, -12, 0), "linear"),
          (2.3, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.9, (14, 0, -14)), (1.45, (18, 0, 14)), (2.3, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.92, (0, 10, 0)), (1.45, (0, -10, 0)), (2.3, (0, 0, 0)))

    # flood (phase 3, invulnerable): she sinks to her knees, censer raised and rung three times as the water rises
    # round her (1.5 s = 30 ticks), then the crozier is driven into the floor: the hall floods
    a = m.anim("flood", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -12, 0)), (1.5, (0, -12, 0)), (1.6, (0, -13, 0), "linear"),
          (2.8, (0, -12, 0)), (3.5, (0, 0, 0)))
    a.scale("robe", (0, (1, 1, 1)), (0.4, (1.08, 0.7, 1.08)), (2.8, (1.08, 0.7, 1.08)), (3.5, (1, 1, 1)))
    a.rot("hem", (0, (0, 0, 0)), (0.4, (0, 0, 0)), (2.8, (0, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-160, 0, -10)), (0.5, (-150, 0, -14), "linear"), (0.9, (-168, 0, -10)),
          (1.0, (-150, 0, -14), "linear"), (1.4, (-168, 0, -10)), (1.5, (-150, 0, -14), "linear"),
          (1.6, (-60, 0, -50), "linear"), (2.8, (-60, 0, -50)), (3.5, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.5, (30, 0, 0), "linear"), (0.9, (-30, 0, 0)), (1.0, (30, 0, 0), "linear"),
          (1.4, (-30, 0, 0)), (1.5, (30, 0, 0), "linear"), (2.0, (0, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.5, (-70, 0, 20)), (1.6, (-20, 0, 10), "linear"), (2.8, (-20, 0, 10)),
          (3.5, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.5, (-20, 0, 0)), (1.6, (14, 0, 0), "linear"), (2.8, (14, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-36, 0, 0)), (1.6, (20, 0, 0), "linear"), (2.8, (18, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-16, 0, 0)), (1.6, (24, 0, 0), "linear"), (2.8, (22, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.8, (18, 0, 0)), (2.8, (12, 0, 0)), (3.5, (0, 0, 0)))

    # riptide (phase 3, spectacle): she bows low into the flood, censer and crozier swept back (1.0 s = 20 ticks), then
    # swims through the water from mark to mark for 2 s, leaning far forward like a diving gull
    a = m.anim("riptide", 3.8)
    a.rot("chest", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (1.0, (44, 0, 0)), (1.08, (60, 0, 0), "linear"), (3.0, (60, 0, 0)),
          (3.8, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.08, (16, 0, 0), "linear"), (3.0, (16, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (-50, 0, 0), "linear"), (3.0, (-50, 0, 0)), (3.8, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.0, (50, 0, -30 * sx)), (1.08, (70, 0, -20 * sx), "linear"),
              (3.0, (70, 0, -20 * sx)), (3.8, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.0, (-196, 0, 0)), (3.0, (-196, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (1.08, (80, 0, 0)), (3.0, (80, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (1.08, (30, 0, 0)), (2.0, (34, 0, 6)), (3.0, (30, 0, -6)), (3.8, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.08, (30, 0, 0)), (2.0, (36, 0, 0)), (3.0, (30, 0, 0)), (3.8, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, -4, 0)), (1.08, (0, -6, 0), "linear"), (3.0, (0, -6, 0)), (3.8, (0, 0, 0)))

    # roar (phase two): crozier and censer flung wide, head thrown back, the veil streaming
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 60)), (1.6, (-44, 0, 64)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-40, 0, -60)), (1.6, (-44, 0, -64)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (1.6, (-18, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (1.1, (26, 0, 8)), (1.6, (20, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.6, (-30, 0, -40)), (1.6, (-20, 0, -30)), (2.0, (0, 0, 0)))

    # stagger: she sags to her knees, the crozier's foot on the floor, the censer dropped to the ground
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -12, 0)), (1.6, (0, -12, 0)), (2.0, (0, 0, 0)))
    a.scale("robe", (0, (1, 1, 1)), (0.3, (1.08, 0.7, 1.08)), (1.6, (1.08, 0.7, 1.08)), (2.0, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, -8)), (1.6, (32, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 10)), (1.6, (26, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-10, 0, 14)), (1.6, (-8, 0, 14)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (30, 0, -16)), (1.6, (32, 0, -16)), (2.0, (0, 0, 0)))
