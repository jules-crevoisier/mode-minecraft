"""The Head Gardener (Le Jardinier en chef): the champion of the Sunken Arboretum, about 3.8 blocks tall.

Silhouette idea: a tall brass gardening automaton left to tend the palm house alone until the garden grew into it.
A barrel-chested riveted copper body gone green at the edges, moss and ivy spilling out of every seam; a glass bell
jar for a head on a brass collar ring, a glowing magenta-and-gold flower growing inside it where a face should be.
Very long arms that end in pruning shears (two steel blades on a brass pivot bolt, red-lacquered grips for forearms),
which open and snap. On his back a verdigris watering can made into a cannon: a barrel runs over his RIGHT shoulder to
a big sprinkler rose, a ribbed hose loops from the can round to his hip. Stout piston legs in flowerpot boots; roots
trail from his feet across the floor.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

MOSS = (92, 140, 52)
MOSS_L = (138, 186, 74)
MOSS_D = (58, 96, 36)
LEAF = (70, 150, 60)
LEAF_L = (120, 200, 90)
LEAF_D = (40, 98, 40)
ROOT = (122, 92, 60)
ROOT_L = (164, 128, 86)
ROOT_D = (84, 60, 40)
STEEL = (200, 206, 212)
STEEL_L = (244, 248, 252)
STEEL_D = (132, 138, 146)
GRIP = (176, 40, 34)            # the shears' red-lacquered grips
GRIP_D = (118, 24, 22)
GLASS = (206, 236, 240)
GLASS_L = (246, 255, 255)
PETAL = (236, 86, 170)          # the flower in the bell jar
PETAL_L = (255, 170, 220)
PETAL_D = (176, 46, 120)
POLLEN = (255, 214, 80)
POLLEN_L = (255, 244, 170)
SAP = (120, 230, 90)            # the chlorophyll window
SAP_L = (210, 255, 170)
POT = (176, 92, 60)             # terracotta flowerpot boots
POT_D = (128, 62, 40)
WATER = (90, 170, 230)


# ---------------------------------------------------------------- paint
def mossy(base, seed=0, amount=0.14, rows=()):
    """Wraps a paint function: moss creeping over it (thickest along ``rows`` (the seams) and on top faces)."""
    def f(face, x, y, w, h):
        c = base(face, x, y, w, h) if callable(base) else base
        if face == "bottom":
            return c
        r = B.n(x // 2, y // 2, seed)
        near = any(abs(y - s) <= 1 for s in rows)
        k = amount + (0.35 if near else 0.0) + (0.25 if face == "top" else 0.0)
        if r < k:
            q = B.n(x, y, seed + 5)
            return MOSS_L if q > 0.7 else (MOSS if q > 0.25 else MOSS_D)
        return c
    return f


def body(face, x, y, w, h):
    """The copper body (18 x 22 x 12): riveted plates, horizontal seams at rows 7 and 15 and a vertical seam down the
    front, verdigris near the bottom, moss spilling out of the seams."""
    if face == "bottom":
        return B.COPPER_D
    if face == "top":
        return mossy(B.COPPER, 3, 0.4)(face, x, y, w, h)
    if y in (7, 15):
        return B.BRASS_D if x % 3 else B.BRASS_L                                       # the seam straps, riveted
    if face == "front" and x == w // 2:
        return B.COPPER_D
    base = B.copper(61, grad=0.25)(face, x, y, w, h)
    if y > 15 and B.n(x, y, 63) < 0.35:
        base = mix(base, B.VERD, 0.6)                                                   # verdigris toward the waist
    return mossy(base, 65, 0.06, rows=(7, 15))(face, x, y, w, h)


def porthole(face, x, y, w, h):
    """A round window on the chest (6 x 6 x 1): a brass bezel round glowing green sap with bubbles."""
    if face != "front":
        return B.BRASS_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if d > 2.9:
        return B.BRASS_D
    if d > 2.0:
        return B.BRASS_L if y < cy else B.BRASS
    return SAP_L if (x, y) in ((2, 2), (3, 3)) else SAP


def porthole_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    return (SAP_L if (x, y) in ((2, 2), (3, 3)) else SAP) if d <= 2.0 else None


def collar(face, x, y, w, h):
    """The brass collar ring the bell jar sits in, riveted."""
    if face in ("top", "bottom"):
        return B.BRASS_D if face == "bottom" else B.BRASS
    if y == 0:
        return B.BRASS_L if x % 3 == 1 else B.BRASS
    return B.BRASS_D


def jar(face, x, y, w, h):
    """The glass bell jar (12 x 11 x 12): see-through, a brass frame on its edges and a mullion down each side, a few
    pale glints on the glass, condensation drops at the bottom."""
    if face == "bottom":
        return None
    if face == "top":
        if x in (0, w - 1) or y in (0, h - 1) or x == w // 2 or y == h // 2:
            return B.BRASS
        return (GLASS_L if (x + y) % 5 == 0 else None)
    if x in (0, w - 1) or x == w // 2:
        return B.BRASS_L if y == 0 else B.BRASS
    if y == 0:
        return B.BRASS_L
    if (x + y) % 7 == 0 and y < h - 3:
        return GLASS_L                                                                 # a diagonal glint
    if y >= h - 2 and B.n(x, y, 71) > 0.6:
        return GLASS                                                                   # condensation
    return None


def cap(face, x, y, w, h):
    return B.brass(73)(face, x, y, w, h)


def petals(face, x, y, w, h):
    """The bloom: magenta petals, lighter at the tips, a ring of gold pollen on top."""
    if face == "top":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        return POLLEN_L if d < 1.0 else (POLLEN if d < 1.8 else (PETAL_L if (x + y) % 2 else PETAL))
    if face == "bottom":
        return PETAL_D
    return PETAL_L if y == 0 else (PETAL if (x + y) % 3 else PETAL_D)


def petals_glow(face, x, y, w, h):
    if face == "bottom":
        return None
    if face == "top":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        return POLLEN_L if d < 1.8 else PETAL_L
    return PETAL_L if y == 0 else (PETAL if (x + y) % 2 else None)


def stem(face, x, y, w, h):
    return LEAF_D if y % 3 == 0 else LEAF


def leaf(face, x, y, w, h):
    """A flat leaf (a 0-thick plane): an almond shape with a midrib, transparent round it."""
    if face not in ("front", "back"):
        return None
    cx = (w - 1) / 2
    half = (w / 2) * (1 - abs((y - (h - 1) / 2) / (h / 2)) ** 1.6)
    if abs(x - cx) > half + 0.3:
        return None
    if abs(x - cx) < 0.6:
        return LEAF_L
    return LEAF if (x + y) % 3 else LEAF_D


def vine(seed=0):
    """A hanging strand of ivy (a plane): a wavy stem with leaves every few texels, transparent between."""
    def f(face, x, y, w, h):
        if face not in ("front", "back", "left", "right"):
            return None
        sx = int(round((w - 1) / 2 + ((y + seed) % 6 - 2.5) * 0.3))
        if x == sx:
            return LEAF_D
        if (y + seed) % 4 in (1, 2) and abs(x - sx) <= 1 + ((y + seed) % 4 == 1):
            return LEAF_L if B.n(x, y, seed) > 0.5 else LEAF
        return None
    return f


def moss_pad(face, x, y, w, h):
    """A cushion of moss (on the shoulders, the hips), ragged at the edges."""
    r = B.n(x, y, 81)
    if face == "bottom":
        return MOSS_D
    if face != "top" and y == h - 1 and r > 0.5:
        return None
    return MOSS_L if r > 0.72 else (MOSS if r > 0.2 else MOSS_D)


def brass_limb(seed=0):
    def f(face, x, y, w, h):
        base = B.brass(seed, grad=0.18)(face, x, y, w, h)
        return mossy(base, seed + 1, 0.04)(face, x, y, w, h)
    return f


def copper_limb(seed=0):
    def f(face, x, y, w, h):
        base = B.copper(seed, grad=0.18)(face, x, y, w, h)
        return mossy(base, seed + 1, 0.06)(face, x, y, w, h)
    return f


def grip(face, x, y, w, h):
    """The forearm as a shear handle: red lacquer with dark wrapping bands, brass ends."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    if y in (0, h - 1):
        return B.BRASS
    if y % 4 == 2:
        return GRIP_D
    return GRIP if (x + y) % 5 else mul(GRIP, 1.15)


def blade(face, x, y, w, h):
    """A shear blade: bright steel with a ground edge and a darker spine."""
    if face == "top":
        return STEEL
    if face == "bottom":
        return STEEL_D
    if face in ("front", "back"):
        return STEEL_L if x == w - 1 else (STEEL if (x + y) % 6 else STEEL_D)
    return STEEL_L if face == "right" else STEEL_D


def bolt(face, x, y, w, h):
    if face in ("left", "right"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        return B.BRASS_L if abs(x - cx) < 1 and abs(y - cy) < 1 else B.BRASS
    return B.BRASS_D


def can(face, x, y, w, h):
    """The watering can (10 x 12 x 8): verdigris copper in brass hoops, a painted water line."""
    if face == "top":
        return mossy(B.VERD, 91, 0.3)(face, x, y, w, h)
    if face == "bottom":
        return B.VERD_D
    if y % 5 == 0:
        return B.BRASS_L if x % 3 == 1 else B.BRASS
    base = mix(B.COPPER, B.VERD, 0.55 + 0.3 * B.n(x, y, 93))
    return mossy(base, 95, 0.05)(face, x, y, w, h)


def barrel(face, x, y, w, h):
    """The cannon barrel over the shoulder: brass, banded."""
    if face in ("front", "back"):
        return B.BRASS_D
    return B.BRASS_L if y == 0 else (B.BRASS_D if (y + x) % 5 == 0 else B.BRASS)


def rose(face, x, y, w, h):
    """The sprinkler rose: a brass disc pierced with holes; water glints in them."""
    if face == "front":
        if x in (0, w - 1) or y in (0, h - 1):
            return B.BRASS_D
        return WATER if (x + y) % 2 == 0 else B.BRASS
    return B.BRASS


def rose_glow(face, x, y, w, h):
    if face != "front" or x in (0, w - 1) or y in (0, h - 1):
        return None
    return WATER if (x + y) % 2 == 0 else None


def hose(face, x, y, w, h):
    return (52, 70, 50) if (x + y) % 2 else (78, 98, 70)


def pot(face, x, y, w, h):
    """Flowerpot boots: terracotta with a rolled rim, moss creeping over the rim."""
    if face == "bottom":
        return POT_D
    if face == "top":
        return MOSS if B.n(x, y, 101) > 0.4 else POT
    if y < 2:
        return MOSS if B.n(x, y, 103) > 0.6 else mul(POT, 1.1)
    return POT if (x * 3 + y) % 7 else POT_D


def root(face, x, y, w, h):
    """A root: bark brown, paler streaks."""
    r = B.n(x, y, 107)
    if face == "top":
        return ROOT_L if r > 0.5 else ROOT
    return ROOT_D if r < 0.3 else (ROOT_L if r > 0.8 else ROOT)


def root_strand(face, x, y, w, h):
    """Fine roots fanned out flat (a plane): thin brown lines, transparent between."""
    if face not in ("top", "bottom"):
        return None
    if (x + y // 3) % 3 == 0 or (y % 4 == 0 and x % 2 == 0):
        return ROOT if B.n(x, y, 109) > 0.3 else ROOT_D
    return None


# ---------------------------------------------------------------- build
def build():
    m = Model("thorn_gardener", seed=919, shadow=1.4, walk_speed=0.7, walk_scale=0.8, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -24, 0))
    m.part("chest", "hips", pivot=(0, -2, 0))
    m.part("head", "chest", pivot=(0, -23, 0))
    m.part("flower", "head", pivot=(0, -4, 0))
    m.part("can", "chest", pivot=(0, -14, 6))
    m.part("cannon", "can", pivot=(-9, -12, 2))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5 * sx, -24, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 12, 0))
        m.part(f"arm_{side}", "chest", pivot=(12 * sx, -20, 0), rot=(-6, 0, 8 * -sx))
        m.part(f"fore_{side}", f"arm_{side}", pivot=(0, 13, 0), rot=(-34, 0, 0))
        m.part(f"jaw_{side}a", f"fore_{side}", pivot=(0, 13, 0), rot=(0, 0, 9))
        m.part(f"jaw_{side}b", f"fore_{side}", pivot=(0, 13, 0), rot=(0, 0, -9))

    # ---- legs: copper pistons in flowerpot boots, roots trailing from the feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3.5, -1, -3.5, 7, 13, 7, copper_limb(10 + sx))
        m.box(leg, -4, 10, -4, 8, 3, 8, B.brass(12 + sx))                              # the knee hoop
        m.box(shin, -2.5, 0, -2.5, 5, 6, 5, B.iron(14 + sx))                           # the piston rod
        m.box(shin, -4.5, 5, -4.5, 9, 7, 9, pot)                                       # the flowerpot boot
        m.box(shin, -5, 4, -5, 10, 2, 10, pot)                                         # its rolled rim
        m.box(shin, -2, 10, -7, 4, 2, 3, root)                                         # roots out of the toe
        m.box(shin, -4 if sx < 0 else 1, 11, 4, 3, 1, 6, root)                         # trailing behind
        m.box(shin, 4 * sx - (2 if sx < 0 else 0), 11, -2, 2, 1, 5, root)
        m.box(shin, -7, 11.9, -3, 14, 0, 14, root_strand)                              # fine roots fanned out

    # ---- hips, the body, the chlorophyll window, moss and ivy out of the seams
    m.box("hips", -9, -2, -6, 18, 5, 12, copper_limb(20))
    m.box("hips", -9.5, 1, -6.5, 19, 2, 13, B.brass(21))                               # the waist strap
    m.box("hips", -8, -1, 6, 6, 2, 3, moss_pad)
    m.box("chest", -9, -22, -6, 18, 22, 12, body)
    m.box("chest", -3, -17, -6.6, 6, 6, 1, porthole, glow=porthole_glow)
    m.box("chest", -10, -23, -7, 20, 2, 14, B.brass(22))                               # the shoulder yoke
    m.box("chest", -14, -24, -4, 7, 2, 8, moss_pad)                                    # moss cushions
    m.box("chest", 7, -24, -4, 7, 2, 8, moss_pad)
    m.box("chest", -6, -24, -6, 12, 1, 10, moss_pad)
    for k, (x, y, hh) in enumerate(((-8, -15, 9), (-4, -7, 7), (5, -15, 10), (7, -7, 8), (0, -7, 6))):
        m.box("chest", x, y, -6.2, 3, hh, 0, vine(k * 3))                              # ivy down the front
    for k, (x, hh) in enumerate(((-7, 11), (-2, 8), (4, 12))):
        m.box("chest", x, -22, 6.1, 3, hh, 0, vine(k * 5 + 1))                         # and down the back
    m.box("chest", -9.1, -15, -4, 0, 10, 3, vine(11))                                  # and the sides
    m.box("chest", 9.1, -8, 1, 0, 8, 3, vine(13))

    # ---- the head: a brass collar, the glass bell jar, the glowing flower inside, a ring handle on top
    m.box("head", -4, -2, -4, 8, 2, 8, B.iron(30))                                     # the neck
    m.box("head", -7, -4, -7, 14, 2, 14, collar)
    m.box("head", -6, -15, -6, 12, 11, 12, jar)
    m.box("head", -3, -17, -3, 6, 2, 6, cap)
    m.box("head", -1, -20, -0.5, 2, 3, 1, B.BRASS_L)                                   # the ring handle
    m.box("head", -5.5, -5, -5.5, 11, 1, 11, mossy(B.VERD_D, 31, 0.6))                 # soil and moss in the jar
    m.box("flower", -0.5, -6, -0.5, 1, 6, 1, stem)
    m.box("flower", -4, -4, 0, 4, 3, 0, leaf)
    m.box("flower", 0, -5, 0, 4, 3, 0, leaf)
    m.box("flower", -3, -9, -3, 6, 3, 6, petals, glow=petals_glow)                     # the bloom
    m.box("flower", -2, -10, -2, 4, 1, 4, POLLEN, glow=POLLEN_L)
    m.box("flower", -4, -8, -1, 1, 2, 2, PETAL_L, glow=PETAL_L)                        # outer petals
    m.box("flower", 3, -8, -1, 1, 2, 2, PETAL_L, glow=PETAL_L)
    m.box("flower", -1, -8, -4, 2, 2, 1, PETAL_L, glow=PETAL_L)
    m.box("flower", -1, -8, 3, 2, 2, 1, PETAL_L, glow=PETAL_L)

    # ---- the watering-can cannon on his back, the barrel over the right shoulder, the hose to the hip
    m.box("can", -5, -8, 0, 10, 12, 8, can)
    m.box("can", -2, -10, 2, 4, 2, 4, B.brass(40))                                     # the filler cap
    m.box("can", 5, -6, 2, 2, 7, 3, B.brass(41))                                       # the handle
    m.box("can", -8, -12, 1, 3, 6, 4, barrel)                                          # the elbow to the barrel
    m.box("cannon", -1.5, -1.5, -15, 3, 3, 17, barrel)
    m.box("cannon", -2, -2, -9, 4, 4, 1, B.BRASS_D)                                    # bands
    m.box("cannon", -2, -2, -3, 4, 4, 1, B.BRASS_D)
    m.box("cannon", -3, -3, -17, 6, 6, 2, rose, glow=rose_glow)                        # the sprinkler rose
    m.box("can", 3, 3, 6, 2, 2, 3, hose)                                               # the hose loops to the hip
    m.box("can", 5, 4, 3, 2, 2, 4, hose)
    m.box("can", 7, 5, -2, 2, 6, 2, hose)
    m.box("can", -4, -8.1, 1, 8, 0, 6, vine(17))
    m.box("can", -5.1, -6, 2, 0, 9, 3, vine(19))

    # ---- the arms: brass upper arms, red shear-grip forearms, two steel blades on a brass bolt at each wrist
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -3, -2, -3, 6, 14, 6, brass_limb(50 + sx))
        m.box(arm, -3.5, -3, -3.5, 7, 3, 7, B.copper(52 + sx))                         # the shoulder cap
        m.box(arm, -3.5, 10, -3.5, 7, 3, 7, B.brass(54 + sx))                          # the elbow
        m.box(fore, -2.5, 0, -2.5, 5, 12, 5, grip)
        m.box(fore, -3, 11, -3, 6, 3, 6, bolt)                                         # the pivot bolt
        m.box(arm, -3.1 if sx < 0 else 3.1, 0, -2, 0, 10, 3, vine(21 + sx))             # ivy round the arm
        for j, k in ((f"jaw_{side}a", -1), (f"jaw_{side}b", 1)):
            m.box(j, -0.5 + 0.5 * k, 1, -1.5, 1, 18, 3, blade)                         # the blade
            m.box(j, -0.5 + 0.5 * k, 19, -1, 1, 3, 2, blade)                           # its point
            m.box(j, -1 + 0.5 * k, 1, -2, 2, 3, 4, STEEL_D)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.5, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (3, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("flower", (0, (0, 0, 0)), (1.0, (0, 0, 6)), (2.0, (0, 0, -6)), (3.0, (0, 0, 0)))
    idle.scale("flower", (0, (1, 1, 1)), (1.5, (1.1, 1.05, 1.1)), (3.0, (1, 1, 1)))
    for s in ("r", "l"):
        idle.rot(f"jaw_{s}a", (0, (0, 0, 9)), (1.5, (0, 0, 14)), (3.0, (0, 0, 9)))
        idle.rot(f"jaw_{s}b", (0, (0, 0, -9)), (1.5, (0, 0, -14)), (3.0, (0, 0, -9)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (20, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("leg_l", (0, (-20, 0, 0)), (1.0, (20, 0, 0)), (2.0, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (16, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.0, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.0, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 4, 2)), (1.0, (0, -4, -2)), (2.0, (0, 4, 2)))
    walk.rot("arm_l", (0, (12, 0, -8)), (1.0, (-12, 0, -8)), (2.0, (12, 0, -8)))
    walk.rot("arm_r", (0, (-12, 0, 8)), (1.0, (12, 0, 8)), (2.0, (-12, 0, 8)))
    walk.rot("flower", (0, (0, 0, 4)), (1.0, (0, 0, -4)), (2.0, (0, 0, 4)))

    # snip (16 / 14 / 14): both shear arms swing out wide, the blades opening (0.8 s); the right shears snap shut
    # across his front at 0.8 s, the left ones at 1.2 s
    a = m.anim("snip", 2.2)
    a.rot("arm_r", (0, (-6, 0, 8)), (0.7, (-70, 50, 40)), (0.8, (-72, 54, 40)), (0.86, (-70, -40, 0), "linear"),
          (1.4, (-60, -30, 4)), (2.2, (-6, 0, 8)))
    a.rot("arm_l", (0, (-6, 0, -8)), (0.7, (-60, -40, -30)), (1.1, (-72, -54, -40)), (1.2, (-72, -54, -40)),
          (1.26, (-70, 40, 0), "linear"), (1.6, (-60, 30, -4)), (2.2, (-6, 0, -8)))
    a.rot("jaw_ra", (0, (0, 0, 9)), (0.7, (0, 0, 40)), (0.8, (0, 0, 42)), (0.84, (0, 0, 0), "linear"), (2.2, (0, 0, 9)))
    a.rot("jaw_rb", (0, (0, 0, -9)), (0.7, (0, 0, -40)), (0.8, (0, 0, -42)), (0.84, (0, 0, 0), "linear"),
          (2.2, (0, 0, -9)))
    a.rot("jaw_la", (0, (0, 0, 9)), (1.1, (0, 0, 40)), (1.2, (0, 0, 42)), (1.24, (0, 0, 0), "linear"), (2.2, (0, 0, 9)))
    a.rot("jaw_lb", (0, (0, 0, -9)), (1.1, (0, 0, -40)), (1.2, (0, 0, -42)), (1.24, (0, 0, 0), "linear"),
          (2.2, (0, 0, -9)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (4, 30, 0)), (0.86, (6, -20, 0), "linear"), (1.2, (6, -24, 0)),
          (1.26, (6, 20, 0), "linear"), (2.2, (0, 0, 0)))

    # lunge (22 / 12 / 16): he crouches with the right shears drawn back wide open (1.1 s), springs forward along the
    # line (1.1-1.3 s) and the blades snap shut at full reach at 1.3 s
    a = m.anim("lunge", 2.5)
    a.rot("arm_r", (0, (-6, 0, 8)), (1.0, (30, 20, 30)), (1.1, (32, 20, 30)), (1.2, (-90, 0, 4), "linear"),
          (1.6, (-86, 0, 4)), (2.5, (-6, 0, 8)))
    a.rot("fore_r", (0, (-34, 0, 0)), (1.0, (-60, 0, 0)), (1.2, (0, 0, 0), "linear"), (1.6, (0, 0, 0)),
          (2.5, (-34, 0, 0)))
    a.rot("jaw_ra", (0, (0, 0, 9)), (1.1, (0, 0, 45)), (1.26, (0, 0, 45)), (1.3, (0, 0, 0), "linear"), (2.5, (0, 0, 9)))
    a.rot("jaw_rb", (0, (0, 0, -9)), (1.1, (0, 0, -45)), (1.26, (0, 0, -45)), (1.3, (0, 0, 0), "linear"),
          (2.5, (0, 0, -9)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (10, 20, 0)), (1.2, (26, -6, 0), "linear"), (1.6, (22, -4, 0)),
          (2.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 3, 0)), (1.2, (0, 0, 0), "linear"), (1.6, (0, 1, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.1, (-30, 0, 0)), (1.3, (-40, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.1, (20, 0, 0)), (1.3, (30, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.1, (40, 0, 0)), (1.3, (10, 0, 0)), (2.5, (0, 0, 0)))

    # thorns (20 / 24 / 14): both shears raised and plunged point-first into the platform at 1.0 s; he holds them in
    # the ground while the thorns run out
    a = m.anim("thorns", 2.9)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-6, 0, 8 * sz)), (0.9, (-160, 0, 10 * sz)), (1.0, (-164, 0, 10 * sz)),
              (1.06, (-40, 0, 6 * sz), "linear"), (2.3, (-38, 0, 6 * sz)), (2.9, (-6, 0, 8 * sz)))
        a.rot(f"fore_{s}", (0, (-34, 0, 0)), (1.0, (0, 0, 0)), (2.3, (-20, 0, 0)), (2.9, (-34, 0, 0)))
        a.rot(f"jaw_{s}a", (0, (0, 0, 9)), (1.0, (0, 0, 0)), (2.3, (0, 0, 0)), (2.9, (0, 0, 9)))
        a.rot(f"jaw_{s}b", (0, (0, 0, -9)), (1.0, (0, 0, 0)), (2.3, (0, 0, 0)), (2.9, (0, 0, -9)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-12, 0, 0)), (1.06, (26, 0, 0), "linear"), (2.3, (22, 0, 0)), (2.9, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -1, 0)), (1.06, (0, 2.5, 0), "linear"), (2.3, (0, 2.5, 0)), (2.9, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (1.06, (1.3, 1.3, 1.3), "linear"), (2.3, (1.15, 1.15, 1.15)), (2.9, (1, 1, 1)))

    # snare (24 / 10 / 14): the left shears stabbed into the ground at his feet, the vine creeping out (1.2 s); he
    # wrenches it up at 1.2 s and the snare closes
    a = m.anim("snare", 2.4)
    a.rot("arm_l", (0, (-6, 0, -8)), (0.4, (-50, 0, -10)), (0.5, (-20, 0, -6), "linear"), (1.1, (-24, 0, -6)),
          (1.2, (-24, 0, -6)), (1.26, (-110, 0, -20), "linear"), (1.7, (-100, 0, -20)), (2.4, (-6, 0, -8)))
    a.rot("fore_l", (0, (-34, 0, 0)), (0.5, (-10, 0, 0)), (1.2, (-10, 0, 0)), (1.26, (-50, 0, 0), "linear"),
          (2.4, (-34, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (20, -10, 0)), (1.2, (22, -10, 0)), (1.26, (-10, 6, 0), "linear"),
          (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (1.2, (16, 0, 0)), (1.26, (-10, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.rot("flower", (0, (0, 0, 0)), (1.2, (20, 0, 0)), (1.26, (-20, 0, 0), "linear"), (2.4, (0, 0, 0)))

    # spray (26 / 20 / 14): he leans forward and levels the watering-can cannon over his right shoulder, the can
    # filling (1.3 s); it sprays from 1.3 s to 2.3 s, shaking him
    a = m.anim("spray", 3.0)
    a.rot("cannon", (0, (0, 0, 0)), (1.2, (12, 0, 0)), (1.3, (14, 0, 0)), (1.34, (8, 0, 0), "linear"),
          (1.6, (12, 0, 0)), (1.9, (8, 0, 0)), (2.3, (12, 0, 0)), (3.0, (0, 0, 0)))
    a.scale("can", (0, (1, 1, 1)), (1.2, (1.08, 1.04, 1.12)), (1.34, (0.98, 1, 0.98), "linear"), (2.3, (0.94, 0.98, 0.94)),
            (3.0, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (1.3, (18, -8, 0)), (1.34, (14, -8, 0), "linear"), (1.5, (17, -6, 0)),
          (1.7, (14, -8, 0)), (1.9, (17, -6, 0)), (2.3, (16, -8, 0)), (3.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-6, 0, 8)), (1.3, (-40, 0, 20)), (2.3, (-40, 0, 20)), (3.0, (-6, 0, 8)))
    a.rot("arm_l", (0, (-6, 0, -8)), (1.3, (10, 0, -20)), (2.3, (10, 0, -20)), (3.0, (-6, 0, -8)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.3, (-16, 0, 0)), (2.3, (-16, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.3, (18, 0, 0)), (2.3, (18, 0, 0)), (3.0, (0, 0, 0)))

    # call (phase 2, 20 / 10 / 16): the shears clacked together over his head three times (1.0 s): the garden's
    # creatures answer at 1.0 s
    a = m.anim("call", 2.3)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-6, 0, 8 * sz)), (0.3, (-170, 0, 24 * sz)), (0.45, (-170, 0, 8 * sz)),
              (0.6, (-170, 0, 24 * sz)), (0.75, (-170, 0, 8 * sz)), (0.9, (-170, 0, 24 * sz)), (1.0, (-170, 0, 6 * sz)),
              (1.6, (-160, 0, 10 * sz)), (2.3, (-6, 0, 8 * sz)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.6, (-20, 0, 0)), (2.3, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (1.0, (1.35, 1.35, 1.35)), (1.6, (1.3, 1.3, 1.3)), (2.3, (1, 1, 1)))

    # pollen (phase 2, 18 / 12 / 14): he bows and shakes his head, the bloom swelling (0.9 s); it bursts open at
    # 0.9 s and the pollen flies
    a = m.anim("pollen", 2.2)
    a.rot("head", (0, (0, 0, 0)), (0.3, (14, 0, 10)), (0.5, (14, 0, -10)), (0.7, (14, 0, 10)), (0.9, (16, 0, 0)),
          (0.96, (-24, 0, 0), "linear"), (1.5, (-20, 0, 0)), (2.2, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (0.9, (1.45, 1.3, 1.45)), (0.96, (1.6, 1.5, 1.6), "linear"), (1.5, (1.2, 1.2, 1.2)),
            (2.2, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (16, 0, 0)), (0.96, (-10, 0, 0), "linear"), (2.2, (0, 0, 0)))

    # ignite (phase 3, 40 / 20 / 20): both shears thrown up toward the sun-lamp, the flower opening wide, the light
    # gathering (2.0 s); he slams them down at 2.0 s as the lamp ignites
    a = m.anim("ignite", 4.0)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-6, 0, 8 * sz)), (1.0, (-160, 0, 30 * sz)), (2.0, (-172, 0, 20 * sz)),
              (2.06, (-40, 0, 10 * sz), "linear"), (3.2, (-40, 0, 10 * sz)), (4.0, (-6, 0, 8 * sz)))
        a.rot(f"jaw_{s}a", (0, (0, 0, 9)), (2.0, (0, 0, 45)), (2.06, (0, 0, 0), "linear"), (4.0, (0, 0, 9)))
        a.rot(f"jaw_{s}b", (0, (0, 0, -9)), (2.0, (0, 0, -45)), (2.06, (0, 0, 0), "linear"), (4.0, (0, 0, -9)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (8, 0, 0), "linear"), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (2.0, (-14, 0, 0)), (2.06, (20, 0, 0), "linear"), (3.2, (16, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (2.0, (1.6, 1.6, 1.6)), (2.06, (1.7, 1.7, 1.7), "linear"), (3.2, (1.4, 1.4, 1.4)),
            (4.0, (1, 1, 1)))
    a.pos("hips", (0, (0, 0, 0)), (2.0, (0, -1, 0)), (2.06, (0, 2, 0), "linear"), (3.2, (0, 2, 0)), (4.0, (0, 0, 0)))

    # photosynth (phase 3, 30 / 50 / 16): he plants his shears, spreads his arms and turns his face up to the lamp
    # (1.5 s), basking with the flower wide open until 4.0 s
    a = m.anim("photosynth", 4.8)
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, (-6, 0, 8 * sz)), (1.5, (-20, 0, 70 * sz)), (4.0, (-24, 0, 74 * sz)),
              (4.8, (-6, 0, 8 * sz)))
        a.rot(f"jaw_{s}a", (0, (0, 0, 9)), (1.5, (0, 0, 30)), (4.0, (0, 0, 30)), (4.8, (0, 0, 9)))
        a.rot(f"jaw_{s}b", (0, (0, 0, -9)), (1.5, (0, 0, -30)), (4.0, (0, 0, -30)), (4.8, (0, 0, -9)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-34, 0, 0)), (2.5, (-36, 6, 0)), (3.3, (-36, -6, 0)), (4.0, (-34, 0, 0)),
          (4.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-10, 0, 0)), (4.0, (-10, 0, 0)), (4.8, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (1.5, (1.5, 1.5, 1.5)), (2.75, (1.65, 1.6, 1.65)), (4.0, (1.5, 1.5, 1.5)),
            (4.8, (1, 1, 1)))

    # roar (phase two): arms flung wide, the jar thrown back, the flower blazing
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-28, 0, 0)), (1.6, (-26, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-6, 0, 8)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (-6, 0, 8)))
    a.rot("arm_l", (0, (-6, 0, -8)), (0.5, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (-6, 0, -8)))
    a.scale("flower", (0, (1, 1, 1)), (0.5, (1.5, 1.5, 1.5)), (1.6, (1.5, 1.5, 1.5)), (2.0, (1, 1, 1)))
    for s in ("r", "l"):
        a.rot(f"jaw_{s}a", (0, (0, 0, 9)), (0.5, (0, 0, 45)), (1.6, (0, 0, 45)), (2.0, (0, 0, 9)))
        a.rot(f"jaw_{s}b", (0, (0, 0, -9)), (0.5, (0, 0, -45)), (1.6, (0, 0, -45)), (2.0, (0, 0, -9)))

    # stagger: his gears seize, he sinks to one knee leaning on the right shears, the flower wilting
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, 6, 0)), (1.6, (0, 6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 6)), (1.6, (28, 0, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -10)), (1.6, (26, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-6, 0, 8)), (0.3, (-30, 0, 10)), (1.6, (-30, 0, 10)), (2.0, (-6, 0, 8)))
    a.rot("flower", (0, (0, 0, 0)), (0.3, (40, 0, 10)), (1.6, (44, 0, 10)), (2.0, (0, 0, 0)))
    a.scale("flower", (0, (1, 1, 1)), (0.3, (0.8, 0.7, 0.8)), (1.6, (0.8, 0.7, 0.8)), (2.0, (1, 1, 1)))
