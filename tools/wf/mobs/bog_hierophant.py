"""The Bog Hierophant (Le Hiérophante des tourbières): the rotting bishop of the Mire Stilt-City, about 5.9 blocks tall.

Silhouette idea: a bishop on stilts. A hunched, rotting prelate in a mantle of living moss stalks the witch-queen's
hall on two long, thin legs wrapped in mangrove roots, like the piles of his own town; his open cope swings round them.
Over a skull-like face of grey-green peat (two glowing marsh-light eyes, a slack jaw, a beard of hanging moss and roots)
rises a tall crooked mitre of rotted linen, stained green, its gold bands gone to verdigris, a toadstool grown on it.
Strong asymmetry: in his RIGHT hand a tall crozier of twisted black mangrove wood whose crook curls forward over a
hanging lantern of swamp-fire (the lure of his moves); his LEFT arm is a long bare bone-thin arm with a hooked claw
and a rosary of finger bones; a mossy hump on his back with vertebrae through it, leeches on his robe and legs, a lily
pad and a cluster of brown toadstools on his left shoulder, and a cloud of marsh-flies circling his head.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

MOSS = (78, 106, 46)
MOSS_L = (128, 152, 72)
MOSS_D = (44, 62, 28)
PEAT = (70, 58, 40)
VEST = (84, 50, 74)            # the chasuble: a rotted bishop's purple
VEST_L = (122, 80, 104)
VEST_D = (50, 28, 44)
GOLD = (176, 146, 74)
GOLD_D = (112, 88, 42)
VERDI = (96, 150, 120)
LINEN = (184, 176, 146)        # the mitre and the alb: rotted linen
LINEN_D = (128, 118, 92)
LINEN_L = (214, 206, 176)
SKIN = (112, 112, 86)          # bog flesh
SKIN_L = (150, 148, 112)
SKIN_D = (64, 64, 48)
BONE = (204, 196, 164)
BONE_D = (140, 130, 102)
WOOD = (66, 44, 36)            # black mangrove wood
WOOD_D = (40, 26, 22)
WOOD_L = (104, 74, 56)
IRON = (62, 60, 54)
IRON_L = (104, 100, 88)
FIRE = (196, 244, 96)          # swamp fire: the lantern and the eyes
FIRE_L = (240, 255, 176)
LEECH = (58, 30, 34)
LEECH_L = (110, 52, 54)
LILY = (70, 128, 48)
LILY_D = (42, 86, 30)
CAP = (146, 104, 70)           # brown toadstools
CAP_L = (186, 146, 104)
STALK = (210, 198, 168)
MUD = (78, 62, 46)
MUD_D = (50, 40, 30)
FLY = (34, 34, 30)


# ---------------------------------------------------------------- paint
def moss(seed=0, ragged=False, fringe=0):
    """Living moss: mottled greens, dark hollows, pale tips; a ragged, dripping hem; optional fringe of strands."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return None if ragged else MOSS_D
        if ragged and face != "top":
            cut = h - 1 - int(B.n(x, 0, seed) * (5 + fringe))
            if y > cut:
                return None
        r = B.n(x, y, seed)
        r2 = B.n(x // 2, y // 2, seed + 3)
        k = 1.04 - 0.16 * y / max(1, h) + (r - 0.5) * 0.18
        c = mul(MOSS, k)
        if r2 < 0.18:
            c = mix(c, MOSS_D, 0.7)
        elif r2 > 0.86:
            c = mix(c, MOSS_L, 0.6)
        if face == "top":
            c = mix(c, MOSS_L, 0.35)
        if B.n(x * 3, y * 5, seed + 9) < 0.025:
            c = PEAT                                                   # bare peat showing through
        return c
    return f


def vest(seed=0, orphrey=True):
    """The chasuble: rotted purple, a tarnished gold orphrey cross gone green, mould blooms."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return VEST_D
        cx = (w - 1) / 2
        dx = abs(x - cx)
        c = mul(VEST, 1.05 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if orphrey and face in ("front", "back"):
            if dx <= 1.5 or (4 <= y <= 5 and dx <= w * 0.4):
                c = GOLD if (x + y) % 3 else mix(GOLD, (240, 220, 140), 0.4)
                if dx > 1.0 and not 4 <= y <= 5:
                    c = GOLD_D
                if B.n(x, y, seed + 2) < 0.35:
                    c = mix(c, VERDI, 0.6)
        if B.n(x // 2, y // 3, seed + 5) < 0.10:
            c = mix(c, MOSS_D, 0.55)                                   # mould creeping in
        return c
    return f


def linen(seed=0, bands=(), stain=0.25):
    """Rotted linen: vertical weave, brown and green stains rising from the bottom, gold bands gone to verdigris."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return LINEN_D
        if y in bands and face != "top":
            c = GOLD if x % 3 else GOLD_D
            return mix(c, VERDI, 0.55) if B.n(x, y, seed + 1) < 0.4 else c
        c = mul(LINEN, 1.04 - 0.1 * y / max(1, h) + (0.05 if x % 3 == 0 else 0) + (B.n(x, y, seed) - 0.5) * 0.07)
        low = y / max(1, h)
        if B.n(x, y // 2, seed + 3) < stain * (0.4 + low):
            c = mix(c, PEAT if B.n(x, y, seed + 4) < 0.5 else MOSS_D, 0.45)
        if face == "top":
            c = LINEN_L
        return c
    return f


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = mul(SKIN, 1.05 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.14)
        if B.n(x, y, seed + 4) < 0.08:
            return mix(c, MOSS_D, 0.6)                                 # rot
        return c
    return f


def bone(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return BONE_D
        c = mul(BONE, 1.04 - 0.14 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if (y + seed) % 4 == 0 and h > 3:
            c = BONE_D                                                 # knuckles and joints
        if B.n(x, y, seed + 6) < 0.12:
            c = mix(c, MOSS_D, 0.4)
        return c
    return f


def face_paint(f, x, y, w, h):
    """The skull-like face: grey-green bog flesh drawn tight, hollow sockets with marsh-light eyes, a long nose ridge."""
    if f != "front":
        return skin(80)(f, x, y, w, h)
    if y in (4, 5) and x in (2, 3, w - 4, w - 3):
        return FIRE_L if y == 4 else FIRE
    if y in (3, 6) and x in (1, 2, 3, 4, w - 5, w - 4, w - 3, w - 2):
        return (30, 34, 24)                                            # the hollow sockets
    if y == 2 and 1 <= x <= w - 2:
        return SKIN_D                                                  # heavy brow
    if 4 <= y <= 7 and x in (w // 2 - 1, w // 2):
        return SKIN_L if y < 7 else (38, 40, 30)                       # nose ridge, the nostril pit
    if y in (8, 9) and x in (0, 1, w - 2, w - 1):
        return SKIN_D                                                  # sunken cheeks
    return skin(81)(f, x, y, w, h)


def face_glow(f, x, y, w, h):
    if f == "front" and y in (4, 5) and x in (2, 3, w - 4, w - 3):
        return FIRE_L if y == 4 else FIRE
    return None


def jaw_paint(f, x, y, w, h):
    if f == "front" and y == 0 and 1 <= x <= w - 2:
        return BONE if x % 2 else (40, 36, 28)                         # a row of teeth
    return skin(82)(f, x, y, w, h)


def wood(seed=0):
    """Twisted black mangrove wood: a spiral grain, knots."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOD_D
        k = 1.0 + (0.22 if (y + x * 2) % 5 == 0 else 0) - (0.18 if (y + x * 2) % 5 == 3 else 0)
        c = mul(WOOD, k + (B.n(x, y, seed) - 0.5) * 0.1)
        if B.n(x, y // 3, seed + 3) < 0.05:
            c = WOOD_L
        return c
    return f


def roots(seed=0, mud=0.4):
    """Mangrove roots wrapped round the legs, muddy toward the feet."""
    def f(face, x, y, w, h):
        if face == "top":
            return WOOD_L
        if face == "bottom":
            return MUD_D
        c = mul(WOOD if (x + y // 2) % 3 else WOOD_L, 1.0 + (B.n(x, y, seed) - 0.5) * 0.12)
        low = y / max(1, h)
        if B.n(x, y, seed + 2) < mud * low * low * 1.6:
            c = mix(c, MUD, 0.8)
        if B.n(x // 2, y, seed + 5) < 0.06:
            c = mix(c, MOSS, 0.6)
        return c
    return f


def iron(seed=0):
    return B.plate(IRON, mul(IRON, 0.6), IRON_L, seed=seed, grad=0.2, worn=0.15)


def lantern_glass(face, x, y, w, h):
    if face in ("top", "bottom"):
        return IRON
    if x in (0, w - 1):
        return IRON                                                    # the cage bars
    return FIRE if (x + y) % 3 else FIRE_L


def lantern_glow(face, x, y, w, h):
    if face in ("top", "bottom") or x in (0, w - 1):
        return None
    return FIRE if (x + y) % 3 else FIRE_L


def leech(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return LEECH_L
        return LEECH if (x + y + seed) % 3 else LEECH_L
    return f


def lily(face, x, y, w, h):
    if face == "top":
        return LILY_D if (x + y) % 4 == 0 or (x == w // 2 and y < h // 2) else LILY
    return LILY_D


def cap(face, x, y, w, h):
    if face == "top":
        return CAP_L if (x + y) % 3 == 0 else CAP
    return mul(CAP, 0.8)


def mud(seed=0):
    def f(face, x, y, w, h):
        c = mul(MUD, 1.0 + (B.n(x, y, seed) - 0.5) * 0.2)
        return MUD_D if B.n(x, y, seed + 1) < 0.2 else c
    return f


def fly_paint(face, x, y, w, h):
    return FLY


# ---------------------------------------------------------------- build
def build():
    m = Model("bog_hierophant", seed=331, shadow=1.6, walk_speed=0.75, walk_scale=0.8, glow_pulse=0.08)

    m.part("bone", pivot=(0, 24, 0))
    # two stilt legs wrapped in mangrove roots, bent a little like a heron's
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5 * sx, -34, 1), rot=(-8, 0, -3 * sx))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 17, 0), rot=(14, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 15, 0), rot=(-6, 0, 3 * sx))
    m.part("pelvis", "bone", pivot=(0, -34, 0))
    m.part("skirt", "pelvis", pivot=(0, -6, 0))
    m.part("waist", "pelvis", pivot=(0, -6, 0))
    m.part("chest", "waist", pivot=(0, -6, 0), rot=(20, 0, 0))
    m.part("stole", "chest", pivot=(0, -16, -7.5), rot=(-20, 0, 0))
    m.part("cape", "chest", pivot=(0, -24, 10), rot=(-4, 0, 0))
    m.part("head", "chest", pivot=(0, -22, -4), rot=(-14, 0, 0))
    m.part("jaw", "head", pivot=(0, -1, -1), rot=(10, 0, 0))
    m.part("beard", "jaw", pivot=(0, 2, -5), rot=(-16, 0, 0))
    m.part("mitre", "head", pivot=(0, -10, 0), rot=(-4, 0, 6))
    m.part("lappets", "mitre", pivot=(0, -1, 5), rot=(10, 0, 0))
    m.part("swarm", "chest", pivot=(0, -30, -4))
    m.part("arm_r", "chest", pivot=(-14, -18, 0), rot=(-6, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 14, 0), rot=(-52, 0, -4))
    m.part("crozier", "fore_r", pivot=(0, 13, 0), rot=(52, 0, 0))
    m.part("crook", "crozier", pivot=(0, -50, 0))
    m.part("lantern", "crook", pivot=(0, -12, -9))
    m.part("arm_l", "chest", pivot=(14, -18, 0), rot=(-10, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 14, 0), rot=(-36, 0, 4))
    m.part("claw", "fore_l", pivot=(0, 14, 0), rot=(10, 0, 0))
    m.part("rosary", "fore_l", pivot=(1, 11, 2), rot=(30, 0, 0))

    # ---- legs: thin stilts of bog flesh bound in mangrove roots, root toes splayed in the mud, leeches
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"leg_{side}", -2, -1, -2, 4, 18, 4, roots(10 + sx, mud=0.0))
        m.box(f"leg_{side}", -2.5, 3, -2.5, 5, 2, 5, roots(12 + sx, mud=0.0))           # root bindings
        m.box(f"leg_{side}", -2.5, 10, -2.5, 5, 2, 5, roots(14 + sx, mud=0.1))
        m.box(f"shin_{side}", -1.5, 0, -1.5, 3, 15, 3, roots(16 + sx, mud=0.5))
        m.box(f"shin_{side}", -2, -1, -2, 4, 3, 4, skin(18 + sx))                      # the knee
        m.box(f"shin_{side}", -2, 8, -2, 4, 2, 4, roots(19 + sx, mud=0.6))
        m.box(f"foot_{side}", -1.5, -1, -1.5, 3, 2, 3, mud(20 + sx))
        m.box(f"foot_{side}", -3.5, 0, -6, 2, 2, 5, roots(21 + sx, mud=0.9))            # three root toes
        m.box(f"foot_{side}", -0.5, 0, -7, 2, 2, 6, roots(22 + sx, mud=0.9))
        m.box(f"foot_{side}", 2, 0, -5, 2, 2, 4, roots(23 + sx, mud=0.9))
        m.box(f"foot_{side}", -1, 0, 1, 2, 2, 4, roots(24 + sx, mud=0.9))               # the back spur
    m.box("leg_r", 1.5, 6, -1, 1, 1, 3, leech(1))
    m.box("shin_l", -2, 4, -1, 1, 3, 1, leech(2))

    # ---- the open cope over the hips: a long mossy back panel and two side flaps, the alb's hem between them
    m.box("pelvis", -10, -6, -6, 20, 7, 12, vest(30, orphrey=False))
    m.box("skirt", -9, 0, -6, 18, 11, 11, linen(31, stain=0.5))                         # the alb, rotted short
    m.box("skirt", -12, 0, 3, 24, 25, 3, moss(32, ragged=True, fringe=3))
    m.box("skirt", -13, 0, -7, 3, 23, 11, moss(33, ragged=True, fringe=3))
    m.box("skirt", 10, 0, -7, 3, 23, 11, moss(34, ragged=True, fringe=3))
    m.box("skirt", -10, 2, -7, 3, 1, 1, leech(3))
    m.box("skirt", 8, 9, 6, 2, 1, 1, leech(4))
    m.box("skirt", 11, 14, -4, 1, 3, 1, leech(5))

    # ---- the torso: the chasuble, the moss mantle, a hump with vertebrae
    m.box("waist", -9, -6, -6, 18, 6, 12, vest(40, orphrey=False))
    m.box("waist", -10, -2, -6.5, 20, 2, 13, GOLD_D)                                   # the cincture
    m.box("chest", -11, -20, -7, 22, 20, 14, vest(41))
    m.box("chest", -14, -23, -8, 28, 6, 16, moss(42))                                  # the mossy collar
    m.box("chest", -14, -18, -8, 4, 22, 15, moss(43, ragged=True, fringe=2))            # the cope's two fronts
    m.box("chest", 10, -18, -8, 4, 22, 15, moss(44, ragged=True, fringe=2))
    m.box("chest", -8, -26, 2, 16, 10, 9, moss(45))                                    # the hump
    for i, (y, s) in enumerate(((-27, 3), (-23, 3), (-19, 2))):
        m.box("chest", -s / 2, y, 9, s, 2, 2, bone(46 + i))                            # vertebrae through it
    m.box("stole", -5, 0, -1, 10, 26, 1, vest(47))
    m.box("cape", -13, 0, 0, 26, 40, 2, moss(48, ragged=True, fringe=4))
    # a lily pad and three brown toadstools on his left shoulder
    m.box("chest", 7, -24, -6, 6, 1, 6, lily)
    for (x, z, hgt, cw) in ((10, 1, 4, 4), (12, -2, 3, 3), (8, 3, 2, 3)):
        m.box("chest", x, -23 - hgt, z, 1, hgt, 1, STALK)
        m.box("chest", x - (cw - 1) / 2, -24 - hgt, z - (cw - 1) / 2, cw, 1, cw, cap)
    m.box("chest", -13, -14, -9, 3, 1, 1, leech(6))
    m.box("chest", -6, -6, -8, 1, 3, 1, leech(7))

    # ---- head: the bog skull, slack jaw, a beard of moss and roots, the crooked mitre
    m.box("head", -5, -10, -6, 10, 10, 10, face_paint, glow=face_glow)
    m.box("head", -5.5, -11, -5, 11, 3, 10, skin(83))                                  # the bald crown under the mitre
    m.box("jaw", -4, 0, -5, 8, 3, 7, jaw_paint)
    for i, (x, ln, wd) in enumerate(((-3, 14, 2), (-1, 20, 2), (1, 17, 2), (3, 11, 1), (-4, 9, 1), (0, 24, 1))):
        m.box("beard", x - wd / 2 if wd == 1 else x - 1, 0, 0 - (i % 2), wd, ln, 1, moss(50 + i, ragged=True))
    m.box("beard", -2, 6, -1, 1, 8, 1, roots(57, mud=0.0))
    m.box("mitre", -5.5, -3, -5.5, 11, 3, 11, linen(60, bands=(0, 2)))
    for k, (wd, hgt) in enumerate(((10, 6), (8, 5), (6, 4), (4, 3), (2, 2))):          # the front horn
        y = -3 - sum(hh for _, hh in ((10, 6), (8, 5), (6, 4), (4, 3), (2, 2))[:k + 1])
        m.box("mitre", -wd / 2, y, -5, wd, hgt, 4, linen(61 + k, bands=(hgt - 1,) if k == 0 else (), stain=0.35))
    for k, (wd, hgt) in enumerate(((10, 5), (8, 5), (6, 3), (4, 3))):                  # the back horn, lower
        y = -3 - sum(hh for _, hh in ((10, 5), (8, 5), (6, 3), (4, 3))[:k + 1])
        m.box("mitre", -wd / 2, y, -1, wd, hgt, 4, linen(66 + k, stain=0.4))
    m.box("mitre", -1, -16, -5.5, 2, 9, 1, mix(GOLD, VERDI, 0.4), glow=None)           # the orphrey on the front
    m.box("mitre", -3, -12, -5.5, 6, 2, 1, mix(GOLD, VERDI, 0.4))
    m.box("mitre", -1, -14, -5.8, 2, 2, 1, FIRE, glow=FIRE)                            # a marsh-light jewel
    m.box("mitre", 3, -7, 3, 1, 3, 1, STALK)                                           # a toadstool on the mitre
    m.box("mitre", 2, -8, 2, 3, 1, 3, cap)
    m.box("lappets", -4, 0, 0, 2, 16, 1, linen(70, bands=(14,), stain=0.5))
    m.box("lappets", 2, 0, 0, 2, 14, 1, linen(71, bands=(12,), stain=0.5))

    # ---- the cloud of marsh-flies round his head: dark specks and a few marsh-lights
    for k in range(14):
        a = math.radians(k * 360 / 14 + (k % 3) * 11)
        r = 9 + (k % 4) * 2.5
        x, y, z = math.cos(a) * r, -((k * 7) % 11) + 2, math.sin(a) * r
        lit = k % 4 == 0
        m.box("swarm", x - 0.5, y - 0.5, z - 0.5, 1, 1, 1, FIRE if lit else fly_paint, glow=FIRE if lit else None)

    # ---- right arm: a mossy sleeve, a bog-flesh hand, the lantern-crozier
    m.box("arm_r", -4, -3, -4, 8, 16, 8, moss(80))
    m.box("fore_r", -4, 0, -4, 8, 9, 8, vest(81, orphrey=False))
    m.box("fore_r", -5, 5, -5, 10, 5, 10, moss(82, ragged=True))                        # flared, dripping cuff
    m.box("fore_r", -2, 9, -2, 4, 5, 4, skin(83))
    m.box("crozier", -1, -50, -1, 2, 92, 2, wood(84))
    m.box("crozier", -1.5, 40, -1.5, 3, 3, 3, iron(85))                                # the ferrule
    for y in (-20, 18):
        m.box("crozier", -1.5, y, -1.5, 3, 4, 3, moss(86 + y))                          # moss grown round the staff
    m.box("crozier", -2, -54, -2, 4, 5, 4, bone(87))                                   # a knop of bone
    m.box("crozier", -2.5, -52, -2.5, 5, 1, 5, GOLD_D)
    # the crook: twisted wood curling over forward and down, the lantern hung from its tip
    for k in range(9):
        phi = math.radians(-180 + 26 * k)
        r = 7.0
        u, v = 4.5 + r * math.cos(phi + math.pi), 6 + r * math.sin(phi + math.pi)
        size = 3 if k < 6 else 2
        m.box("crook", -size / 2, -v - size / 2, -u - size / 2, size, size, size, wood(90 + k))
    m.box("crook", -1, -3, -1, 2, 4, 2, wood(99))                                      # the neck into the knop
    m.box("lantern", -0.5, 0, -0.5, 1, 3, 1, IRON)                                     # its chain
    m.box("lantern", -2.5, 3, -2.5, 5, 1, 5, iron(100))                                # the lid
    m.box("lantern", -2, 4, -2, 4, 5, 4, lantern_glass, glow=lantern_glow)             # the swamp-fire inside
    m.box("lantern", -2.5, 9, -2.5, 5, 1, 5, iron(101))
    m.box("lantern", -1, 2, -1, 2, 1, 2, iron(102))                                    # the ring
    for (x, y, z) in ((-4, 2, 1), (3, 6, -3), (1, 10, 3), (-3, 8, -2)):                # flies round the light
        m.box("lantern", x, y, z, 1, 1, 1, fly_paint)

    # ---- left arm: a ragged sleeve over a bone-thin arm, a hooked claw, a rosary of finger bones
    m.box("arm_l", -4, -3, -4, 8, 15, 8, moss(110))
    m.box("fore_l", -4, -1, -4, 8, 6, 8, moss(111, ragged=True))
    m.box("fore_l", -1.5, 0, -1.5, 3, 14, 3, bone(112))
    m.box("claw", -2, 0, -2, 4, 3, 4, bone(113))
    for i, x in enumerate((-2, -0.5, 1)):
        m.box("claw", x, 2, -2, 1, 7, 1, bone(114 + i))                                # long hooked fingers
        m.box("claw", x, 8, -3, 1, 1, 2, BONE_D)
    m.box("claw", 2, 1, 0, 1, 5, 1, bone(117))                                         # the thumb
    for k in range(7):
        m.box("rosary", -0.5, k * 1.6, -0.5 + (k % 2) * 0.3, 1, 1, 1, BONE if k != 6 else FIRE,
              glow=FIRE if k == 6 else None)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, -0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (0, 10, 2)), (2.6, (4, -6, -2)), (4.0, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.0, (6, 0, 0)), (2.0, (0, 0, 0)), (3.0, (8, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.5, (6, 0, 4)), (3.0, (-4, 0, -3)), (4.0, (0, 0, 0)))
    idle.rot("swarm", (0, (0, 0, 0)), (1.0, (6, 90, 0)), (2.0, (0, 180, 6)), (3.0, (-6, 270, 0)), (4.0, (0, 0, 0)))
    idle.rot("lantern", (0, (0, 0, 0)), (1.2, (10, 0, 6)), (2.6, (-8, 0, -5)), (4.0, (0, 0, 0)))
    idle.rot("rosary", (0, (0, 0, 0)), (2.0, (-10, 0, 6)), (4.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (2.0, (3, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("skirt", (0, (0, 0, 0)), (2.0, (2, 0, -1)), (4.0, (0, 0, 0)))
    idle.rot("claw", (0, (0, 0, 0)), (1.6, (14, 0, 0)), (2.2, (0, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (24, 0, 0)), (1.0, (-24, 0, 0)), (2.0, (24, 0, 0)))
    walk.rot("leg_l", (0, (-24, 0, 0)), (1.0, (24, 0, 0)), (2.0, (-24, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (36, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.5, (36, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, 1.5, 0)), (1.0, (0, 0, 0)), (1.5, (0, 1.5, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 6, 0)), (1.0, (0, -6, 0)), (2.0, (0, 6, 0)))
    walk.rot("skirt", (0, (4, 0, 3)), (1.0, (4, 0, -3)), (2.0, (4, 0, 3)))
    walk.rot("cape", (0, (10, 0, 0)), (1.0, (16, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("lantern", (0, (16, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (16, 0, 0)))

    # sweep: the crozier drawn back over his right shoulder (0.8 s = 16 ticks), then swept across his front
    a = m.anim("sweep", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-60, -10, 70)), (0.8, (-66, -12, 74)), (0.92, (-70, 60, -30), "linear"),
          (1.15, (-62, 64, -34)), (1.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.92, (20, 0, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.8, (-50, 0, 20)), (0.92, (-60, 0, -10), "linear"), (1.15, (-58, 0, -12)),
          (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 32, 0)), (0.92, (8, -34, 0), "linear"), (1.15, (6, -36, 0)), (1.7, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, 12, 0)), (0.92, (0, -12, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.8, (8, 0, -10)), (1.0, (20, 0, 14)), (1.7, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.8, (0, 8, 0)), (1.0, (0, -10, 0)), (1.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-16, 0, 0)), (0.92, (10, 0, 0), "linear"), (1.7, (0, 0, 0)))

    # slam: the crozier lifted high over the mitre in both hands (1.0 s = 20 ticks), then brought down: the lantern
    # smashes on the floor ahead and the bog opens there
    a = m.anim("slam", 1.95)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-150, 0, 20)), (1.0, (-160, 0, 22)), (1.08, (-60, 0, 10), "linear"),
          (1.4, (-56, 0, 10)), (1.95, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.0, (130, 0, 0)), (1.08, (-96, 0, 0), "linear"), (1.4, (-94, 0, 0)), (1.95, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-150, 0, -36)), (1.08, (-70, 0, -30), "linear"), (1.4, (-66, 0, -30)),
          (1.95, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.08, (24, 0, 0), "linear"), (1.4, (22, 0, 0)), (1.95, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.08, (6, 0, 0), "linear"), (1.95, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 2, 0)), (1.08, (0, -4, 0), "linear"), (1.4, (0, -4, 0)), (1.95, (0, 0, 0)))
    a.rot("lantern", (0, (0, 0, 0)), (1.0, (-40, 0, 0)), (1.1, (50, 0, 0), "linear"), (1.5, (-20, 0, 0)), (1.95, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (1.2, (24, 0, 0)), (1.95, (0, 0, 0)))

    # lure: the lantern held out toward his prey, swinging slowly (0.9 s = 18 ticks); the swamp-fire leaps to them and
    # marks them, he holds the pose while the mark burns
    a = m.anim("lure", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-96, 0, 8)), (0.9, (-100, 0, 6)), (0.95, (-108, 0, 4), "linear"),
          (1.4, (-104, 0, 6)), (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (1.4, (40, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.4, (-10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("lantern", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (0.6, (-20, 0, 0)), (0.9, (16, 0, 0)), (0.95, (-30, 0, 0), "linear"),
          (1.4, (10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-10, -14, 0)), (1.4, (-10, -14, 0)), (2.1, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.9, (24, 0, 0)), (1.0, (30, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-30, 0, -40)), (1.4, (-30, 0, -40)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (6, -16, 0)), (1.4, (6, -16, 0)), (2.1, (0, 0, 0)))

    # mire: the crozier planted, his claw spread palm down and drawn toward the floor (1.0 s = 20 ticks): the bog
    # opens in circles round the hall and he holds them open
    a = m.anim("mire", 3.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-80, 0, -50)), (1.0, (-84, 0, -52)), (1.05, (-40, 0, -40), "linear"),
          (2.5, (-40, 0, -40)), (3.2, (0, 0, 0)))
    a.rot("claw", (0, (0, 0, 0)), (0.7, (-40, 0, 0)), (1.0, (-50, 0, 0)), (1.05, (40, 0, 0), "linear"), (2.5, (40, 0, 0)),
          (3.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-30, 0, 20)), (1.0, (-34, 0, 22)), (1.05, (-20, 0, 14), "linear"),
          (2.5, (-20, 0, 14)), (3.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 0, 0)), (1.05, (22, 0, 0), "linear"), (2.5, (20, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.05, (16, 0, 0), "linear"), (2.5, (14, 0, 0)), (3.2, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.05, (0, -3, 0), "linear"), (2.5, (0, -3, 0)), (3.2, (0, 0, 0)))
    a.rot("swarm", (0, (0, 0, 0)), (1.0, (0, 120, 0)), (2.5, (0, 400, 0)), (3.2, (0, 360, 0)))

    # stomp: a stilt leg lifted high (0.6 s = 12 ticks), stamped down: the mud splashes round him
    a = m.anim("stomp", 1.35)
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-60, 0, 0)), (0.6, (-64, 0, 0)), (0.65, (6, 0, 0), "linear"), (1.0, (6, 0, 0)),
          (1.35, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.6, (50, 0, 0)), (0.65, (0, 0, 0), "linear"), (1.35, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-10, 0, 6)), (0.65, (14, 0, 0), "linear"), (1.0, (12, 0, 0)), (1.35, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.6, (0, 2, 0)), (0.65, (0, -2, 0), "linear"), (1.0, (0, -2, 0)), (1.35, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-40, 0, -50)), (0.65, (-10, 0, -30), "linear"), (1.35, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (0.75, (10, 0, 0)), (1.35, (0, 0, 0)))

    # stride: he leans in on his long legs, crozier levelled (0.7 s = 14 ticks), then strides through you, ferrule
    # first, for half a second
    a = m.anim("stride", 1.8)
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 16, 0)), (0.75, (26, -4, 0), "linear"), (1.2, (26, -4, 0)), (1.8, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-20, 0, 30)), (0.75, (-84, 0, 4), "linear"), (1.2, (-80, 0, 4)), (1.8, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.7, (40, 0, 0)), (0.75, (-30, 0, 0), "linear"), (1.2, (-30, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.85, (-30, 0, 0), "linear"), (1.0, (24, 0, 0)), (1.15, (-30, 0, 0)),
          (1.2, (-20, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (0.85, (26, 0, 0), "linear"), (1.0, (-30, 0, 0)), (1.15, (24, 0, 0)),
          (1.2, (16, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.75, (14, 0, 0)), (0.9, (34, 0, 0)), (1.2, (30, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.75, (0, 0, 0)), (0.9, (20, 0, 0)), (1.2, (16, 0, 0)), (1.8, (0, 0, 0)))

    # leeches: he shudders, claw raised, the moss of his robe heaving (0.8 s = 16 ticks), then shakes himself: the
    # leeches drop off him onto the floor
    a = m.anim("leeches", 1.7)
    a.rot("chest", (0, (0, 0, 0)), (0.2, (4, 0, 6)), (0.4, (4, 0, -6)), (0.6, (4, 0, 6)), (0.8, (2, 0, -4)),
          (0.85, (16, 0, 10), "linear"), (0.95, (16, 0, -10), "linear"), (1.1, (12, 0, 4)), (1.7, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.8, (-8, 0, 0)), (0.85, (12, 0, 8), "linear"), (0.95, (12, 0, -8), "linear"),
          (1.7, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.9, (20, 0, 10)), (1.0, (20, 0, -10)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-120, 0, -30)), (0.85, (-60, 0, -60), "linear"), (1.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-24, 0, 0)), (0.9, (10, 14, 0)), (1.0, (10, -14, 0)), (1.7, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (1.7, (0, 0, 0)))

    # reap (phase 2): a forehand sweep at 0.8 s (16 ticks), the crozier carried round, a backhand at 1.4 s
    a = m.anim("reap", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-60, -10, 70)), (0.8, (-66, -12, 74)), (0.92, (-70, 60, -30), "linear"),
          (1.2, (-74, 70, -36)), (1.4, (-60, -20, 70), "linear"), (1.7, (-56, -24, 72)), (2.3, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (0.8, (-50, 0, 20)), (0.92, (-60, 0, -10), "linear"), (1.2, (-60, 0, -14)),
          (1.4, (-56, 0, 24), "linear"), (1.7, (-50, 0, 20)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 32, 0)), (0.92, (8, -34, 0), "linear"), (1.2, (6, -38, 0)),
          (1.4, (8, 32, 0), "linear"), (1.7, (6, 34, 0)), (2.3, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, 12, 0)), (0.92, (0, -12, 0), "linear"), (1.4, (0, 12, 0), "linear"),
          (2.3, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (14, 0, -14)), (1.45, (18, 0, 14)), (2.3, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.92, (0, 10, 0)), (1.45, (0, -10, 0)), (2.3, (0, 0, 0)))

    # swarm (phase 2): his arms spread, his jaw falls open (0.9 s = 18 ticks): the marsh-flies pour out of his robes
    # and hunt for two seconds
    a = m.anim("swarm", 3.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-40, 0, 60)), (2.9, (-40, 0, 60)), (3.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -64)), (2.9, (-40, 0, -64)), (3.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (2.9, (40, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-28, 0, 0)), (2.9, (-24, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (2.9, (-12, 0, 0)), (3.6, (0, 0, 0)))
    a.scale("swarm", (0, (1, 1, 1)), (0.9, (1.6, 1.6, 1.6)), (1.0, (2.6, 1.4, 2.6), "linear"), (2.9, (2.4, 1.4, 2.4)),
            (3.6, (1, 1, 1)))
    a.rot("swarm", (0, (0, 0, 0)), (0.9, (0, 180, 0)), (2.9, (0, 900, 0)), (3.6, (0, 1080, 0)))

    # wisp (phase 2): he sags and his body burns away into a marsh-light (0.9 s = 18 ticks); he is hidden while the
    # wisp flits from lantern to lantern, then reappears behind his prey crouched, the crozier drawn back (from 3.5 s)
    # and strikes at 3.9 s
    a = m.anim("wisp", 5.2)
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, -10, 0)), (3.5, (0, -10, 0)), (3.9, (0, -2, 0)), (4.5, (0, -2, 0)),
          (5.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (3.5, (30, 40, 0)), (3.85, (-6, 40, 0)), (3.95, (24, -30, 0), "linear"),
          (4.5, (20, -30, 0)), (5.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (20, 0, 20)), (3.5, (-60, -10, 70)), (3.85, (-66, -12, 74)),
          (3.95, (-70, 60, -30), "linear"), (4.5, (-62, 64, -34)), (5.2, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (3.5, (-50, 0, 20)), (3.85, (-50, 0, 20)), (3.95, (-60, 0, -10), "linear"),
          (4.5, (-58, 0, -12)), (5.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (20, 0, -20)), (3.5, (-40, 0, -50)), (4.5, (-30, 0, -40)), (5.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (30, 0, 0)), (3.5, (-10, 0, 0)), (5.2, (0, 0, 0)))
    a.scale("skirt", (0, (1, 1, 1)), (0.9, (1.2, 0.6, 1.2)), (3.5, (1.2, 0.6, 1.2)), (3.9, (1, 1, 1)), (5.2, (1, 1, 1)))

    # kindle (phase 3, invulnerable): he kneels, the lantern lifted high and the swamp gas rising round him (1.5 s =
    # 30 ticks), then the lantern is dashed on the floor: the gas ignites
    a = m.anim("kindle", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -14, 0)), (1.5, (0, -14, 0)), (1.6, (0, -15, 0), "linear"),
          (2.8, (0, -14, 0)), (3.5, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.4, (-70, 0, 0)), (2.8, (-70, 0, 0)), (3.5, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.4, (100, 0, 0)), (2.8, (100, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-160, 0, 16)), (1.5, (-170, 0, 14)), (1.6, (-50, 0, 10), "linear"),
          (2.8, (-50, 0, 10)), (3.5, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.5, (110, 0, 0)), (1.6, (0, 0, 0), "linear"), (2.8, (0, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-60, 0, -60)), (1.5, (-70, 0, -64)), (1.6, (-20, 0, -40), "linear"),
          (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-36, 0, 0)), (1.6, (20, 0, 0), "linear"), (2.8, (18, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-18, 0, 0)), (1.6, (28, 0, 0), "linear"), (2.8, (24, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.5, (30, 0, 0)), (1.7, (40, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.8, (24, 0, 0)), (2.8, (16, 0, 0)), (3.5, (0, 0, 0)))

    # firelines (phase 3, spectacle): the lantern swung round his head (1.0 s = 20 ticks), then flung down: lines of
    # burning swamp gas roll across the hall; he holds the crozier aloft over them, then sags, spent
    a = m.anim("firelines", 4.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-120, -40, 30)), (0.6, (-130, 40, 20)), (0.9, (-140, -30, 30)),
          (1.0, (-150, 0, 20)), (1.05, (-80, 0, 10), "linear"), (1.3, (-150, 0, 16)), (3.2, (-150, 0, 16)),
          (3.5, (-30, 0, 20)), (4.2, (0, 0, 0)))
    a.rot("crozier", (0, (0, 0, 0)), (1.0, (60, 0, 0)), (1.05, (-40, 0, 0), "linear"), (1.3, (140, 0, 0)), (3.2, (140, 0, 0)),
          (4.2, (0, 0, 0)))
    a.rot("lantern", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (0.6, (-50, 0, 30)), (0.9, (40, 0, -30)), (1.05, (-60, 0, 0), "linear"),
          (1.6, (20, 0, 0)), (3.2, (-10, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-40, 0, -70)), (3.2, (-40, 0, -70)), (3.5, (10, 0, -10)), (4.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.05, (10, 0, 0), "linear"), (3.2, (-10, 0, 0)), (3.5, (34, 0, 0)),
          (3.9, (32, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (3.2, (-26, 0, 0)), (3.5, (20, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.0, (36, 0, 0)), (3.2, (30, 0, 0)), (3.6, (12, 0, 0)), (4.2, (0, 0, 0)))

    # roar (phase two): crozier and claw flung wide, head thrown back, jaw open, the flies boiling out
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 60)), (1.6, (-44, 0, 64)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (1.6, (-36, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (44, 0, 0)), (1.6, (40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-22, 0, 0)), (1.6, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (1.1, (26, 0, 8)), (1.6, (20, 0, -8)), (2.0, (0, 0, 0)))
    a.scale("swarm", (0, (1, 1, 1)), (0.6, (2.2, 1.6, 2.2)), (1.6, (2.0, 1.5, 2.0)), (2.0, (1, 1, 1)))

    # stagger: his stilts buckle, he sags to his knees on the crozier, the mitre askew
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -14, 0)), (1.6, (0, -14, 0)), (2.0, (0, 0, 0)))
    for side in ("r", "l"):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.3, (100, 0, 0)), (1.6, (100, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (34, 0, -8)), (1.6, (36, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 12)), (1.6, (26, 0, 12)), (2.0, (0, 0, 0)))
    a.rot("mitre", (0, (0, 0, 0)), (0.3, (0, 0, 14)), (1.6, (0, 0, 16)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-10, 0, 14)), (1.6, (-8, 0, 14)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (30, 0, -16)), (1.6, (32, 0, -16)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
