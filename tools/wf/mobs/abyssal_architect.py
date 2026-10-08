"""The Abyssal Architect (L'Architecte de l'abîme): the builder-priest who raised the Inverted Spire downward into the
dark, and still hangs under its point over the lake. About 5.7 blocks tall (7 with the chains on his back).

Silhouette idea: a gaunt, stooped marionette of a priest hanging from chains. Three iron chains rise from a harness
between his shoulder blades to broken hooks high above his mitre, as if the spire still held him up. He has four
arms: a long upper pair and a thin lower pair growing from his ribs. The narrow slate cassock falls to the floor, its
hem torn and marked like a mason's rule (chalk tick marks, brass studs); a gold-stitched stole with square-and-compass
glyphs hangs down his front; a short hooded cape covers his shoulders. His face is a mask of pale weathered limestone
with three glowing soul-blue slits, under a tall mitre shaped like a pinnacle.
Strong asymmetry: his RIGHT upper hand swings a plumb-bob flail (a long chain and a great lead plumb-bob capped in
brass, a glowing plumb line down its side); his LEFT upper hand wields a compass-blade (giant dividers: one leg a
long steel blade, the other a needle point, hinged on a brass disc). The lower right hand holds a brass set-square,
the lower left a small soul lantern.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

SLATE = (64, 66, 78)            # the cassock: dark slate wool
SLATE_L = (96, 100, 114)
SLATE_D = (32, 33, 40)
ASH = (88, 84, 82)              # the cape
ASH_D = (56, 52, 52)
ASH_L = (122, 116, 110)
CHALK = (214, 210, 196)         # chalk rule marks
STONE = (196, 190, 172)         # the limestone mask
STONE_L = (226, 222, 206)
STONE_D = (138, 132, 118)
SKIN = (150, 146, 150)          # grey, gaunt skin
SKIN_D = (100, 96, 104)
SKIN_L = (184, 180, 182)
GOLD = (198, 160, 78)
GOLD_L = (238, 206, 128)
GOLD_D = (128, 96, 42)
BRASS = (186, 146, 68)
BRASS_L = (232, 200, 118)
BRASS_D = (116, 84, 36)
LEAD = (88, 94, 104)            # the plumb-bob
LEAD_L = (130, 138, 150)
LEAD_D = (54, 58, 68)
STEEL = (176, 182, 192)
STEEL_L = (226, 232, 238)
STEEL_D = (110, 116, 128)
IRON = (62, 60, 64)
IRON_L = (104, 102, 106)
IRON_D = (36, 34, 38)
SOUL = (96, 226, 246)           # soul-blue glow
SOUL_L = (206, 250, 255)
STOLE = (64, 40, 46)            # a dark wine stole
STOLE_D = (40, 24, 30)


# ---------------------------------------------------------------- paint
def cassock(seed=0, ragged=False, rule=False, seam=False, spire=False):
    """Slate wool in long narrow folds, darker toward the floor; ``rule``: chalk tick marks and brass studs like a
    mason's rule along the bottom; ``ragged``: a torn hem."""
    def f(face, x, y, w, h):
        if face == "top":
            return SLATE_D
        if face == "bottom":
            return None if ragged else SLATE_D
        if ragged:
            cut = h - 1 - int(B.n(x, 0, seed) * 4)
            if y > cut:
                return None
        fold = 0.12 if x % 4 == 1 else (-0.10 if x % 4 == 3 else 0.0)
        c = mul(SLATE, 1.06 - 0.22 * y / max(1, h) + fold + (B.n(x, y, seed) - 0.5) * 0.06)
        if rule:
            band = h - 6 if ragged else h - 3
            if y == band:
                c = mix(c, CHALK, 0.55)
            elif band - 3 <= y < band and x % 2 == 0:
                c = mix(c, CHALK, 0.6 if (x // 2) % 5 == 0 or y == band - 1 else 0.0)
            elif y == band + 1 and x % 6 == 2:
                c = BRASS_L
        if seam and face == "front" and abs(x - (w - 1) / 2) < 1.0:
            c = BRASS_D if y % 3 else BRASS_L                       # a brass-studded front seam
        if spire and face == "front":
            cx = (w - 1) / 2
            half = (h - 1 - y) * 0.45                               # a chalk sketch of the inverted spire
            if abs(abs(x - cx) - half) < 0.5 and half > 0.6 or y == 1 and abs(x - cx) <= (h - 2) * 0.45:
                c = mix(c, CHALK, 0.7)
        if B.n(x * 3, y, seed + 5) < 0.015:
            c = SLATE_L
        return c
    return f


def cape(seed=0):
    """The short hooded cape: ash wool, a brass edge, a torn lower edge."""
    def f(face, x, y, w, h):
        if face == "top":
            return ASH_L
        if face == "bottom":
            return ASH_D
        cut = h - 1 - int(B.n(x, 1, seed) * 3)
        if y > cut:
            return None
        c = mul(ASH, 1.05 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        if y == cut:
            c = BRASS_D if x % 2 else BRASS
        elif x % 5 == 2:
            c = mul(c, 0.86)
        return c
    return f


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = mul(SKIN, 1.05 - 0.15 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if y % 4 == 0 and face in ("front", "back"):
            c = mul(c, 0.82)                                        # knuckles and tendons
        return c
    return f


def mask_paint(f, x, y, w, h):
    """The limestone mask: three soul slits (two eyes, one on the brow), a carved square-and-compass, cracks."""
    if f != "front":
        return stone(90)(f, x, y, w, h)
    cx = (w - 1) / 2
    if y in (4, 5) and x in (1, 2, w - 3, w - 2):
        return SOUL_L if y == 4 else SOUL                            # the eye slits
    if 1 <= y <= 3 and abs(x - cx) < 0.6:
        return SOUL                                                  # the brow slit
    if y == 7 and abs(x - cx) <= 1.6:
        return STONE_D                                               # a thin carved mouth
    if y == 3 and x in (1, w - 2) or y in (5, 6) and x == int(cx) - 2:
        return STONE_D                                               # cracks
    if y == h - 1:
        return STONE_D
    return stone(91)(f, x, y, w, h)


def mask_glow(f, x, y, w, h):
    cx = (w - 1) / 2
    if f == "front" and (y in (4, 5) and x in (1, 2, w - 3, w - 2) or 1 <= y <= 3 and abs(x - cx) < 0.6):
        return SOUL_L if y in (1, 4) else SOUL
    return None


def stone(seed=0, carve=False):
    def f(face, x, y, w, h):
        if face == "top":
            return STONE_L
        if face == "bottom":
            return STONE_D
        c = mul(STONE, 1.05 - 0.16 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.10)
        if B.n(x, y, seed + 3) < 0.05:
            c = STONE_D                                              # pitting
        if carve and face in ("front", "back", "left", "right") and (y % 4 == 0 or x % 4 == 0 and y % 8 < 4):
            c = mul(c, 0.84)                                         # masonry courses on the mitre
        return c
    return f


def stole(seed=0):
    """The stole: dark wine silk, gold edges, square-and-compass glyphs stitched in gold every 8 texels."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STOLE_D
        if x == 0 or x == w - 1:
            return GOLD_D
        c = mul(STOLE, 1.04 - 0.12 * y / max(1, h))
        k = y % 8
        cx = (w - 1) / 2
        if face == "front" and w >= 4:
            if k == 2 and abs(x - cx) <= 0.6 or k == 3 and abs(x - cx) <= 1.2 or k == 4 and abs(x - cx) >= 0.8:
                c = GOLD_L if k == 2 else GOLD                       # the compass
            if k == 5 and abs(x - cx) <= 1.6:
                c = GOLD                                             # the square
        if y >= h - 2:
            c = GOLD if (x + y) % 2 else GOLD_D                      # fringe
        return c
    return f


def chain_paint(base=IRON, light=IRON_L, dark=IRON_D):
    """Chain links: alternating light (flat link) and dark (edge-on) every two texels."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return dark
        return light if (y // 2) % 2 == 0 else (dark if x == 0 or x == w - 1 else base)
    return f


def lead(seed=0, line=False):
    """The lead plumb-bob: dull blue-grey, a highlight down one edge, ``line``: the glowing plumb line."""
    def f(face, x, y, w, h):
        if face == "top":
            return LEAD_L
        if face == "bottom":
            return LEAD_D
        c = mul(LEAD, 1.08 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        if x == 0:
            c = LEAD_L
        if line and face in ("front", "back") and x == w // 2:
            return SOUL
        return c
    return f


def lead_glow(face, x, y, w, h):
    if face in ("front", "back") and x == w // 2:
        return SOUL
    return None


def blade(seed=0):
    """The compass-blade's steel leg: a bright edge on the front side, a fuller, a dark back."""
    def f(face, x, y, w, h):
        if face == "top":
            return STEEL_L
        if face == "bottom":
            return STEEL_D
        if face == "front" or face == "back":
            if x == 0:
                return STEEL_L                                        # the edge
            if x == w - 1:
                return STEEL_D
            return mul(STEEL, 0.9 if y % 6 == 3 else 1.0)            # graduation marks
        return mul(STEEL, 0.85 + (B.n(x, y, seed) - 0.5) * 0.06)
    return f


def brass(seed=0):
    return B.plate(BRASS, BRASS_D, BRASS_L, seed=seed, grad=0.25, worn=0.08)


def square_paint(face, x, y, w, h):
    """The set-square's brass: tick marks every two texels along its arms."""
    c = BRASS if (x + y) % 2 else BRASS_L
    if face in ("front", "back", "left", "right") and (x % 2 == 0 and y == 0 or y % 2 == 0 and x == 0):
        return BRASS_D
    return c


def lantern_glow(face, x, y, w, h):
    if face in ("front", "back", "left", "right") and 0 < x < w - 1 and 0 < y < h - 1:
        return SOUL_L if (x + y) % 3 else SOUL
    return None


def lantern_paint(face, x, y, w, h):
    if face in ("top", "bottom"):
        return IRON_D
    if 0 < x < w - 1 and 0 < y < h - 1:
        return SOUL
    return IRON


# ---------------------------------------------------------------- build
def build():
    m = Model("abyssal_architect", seed=331, shadow=1.6, walk_speed=0.65, walk_scale=0.8, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -40, 0))
    m.part("skirt", "pelvis", pivot=(0, 0, 0))
    m.part("hem", "skirt", pivot=(0, 28, 0))
    m.part("waist", "pelvis", pivot=(0, -2, 0))
    m.part("chest", "waist", pivot=(0, -10, 0), rot=(16, 0, 0))
    m.part("stole", "chest", pivot=(0, -21, -5.5), rot=(-14, 0, 0))
    m.part("cape", "chest", pivot=(0, -24, 0))
    m.part("chain_r", "chest", pivot=(-5, -20, 5), rot=(-20, 0, 26))
    m.part("chain_m", "chest", pivot=(0, -22, 5), rot=(-26, 0, 0))
    m.part("chain_l", "chest", pivot=(5, -20, 5), rot=(-20, 0, -26))
    m.part("neck", "chest", pivot=(0, -24, -2), rot=(-12, 0, 0))
    m.part("head", "neck", pivot=(0, -5, -1), rot=(-4, 0, 0))
    m.part("mitre", "head", pivot=(0, -11, 0.5))
    # upper arms: long and bony in wide sleeves
    m.part("arm_ur", "chest", pivot=(-11, -21, 0), rot=(-8, 0, 12))
    m.part("fore_ur", "arm_ur", pivot=(0, 19, 0), rot=(-46, 0, -6))
    m.part("flail", "fore_ur", pivot=(0, 21, 0), rot=(54, 0, -6))
    m.part("bob", "flail", pivot=(0, 20, 0))
    m.part("arm_ul", "chest", pivot=(11, -21, 0), rot=(-10, 0, -12))
    m.part("fore_ul", "arm_ul", pivot=(0, 19, 0), rot=(-52, 0, 4))
    m.part("compass", "fore_ul", pivot=(0, 20, 0), rot=(-10, 0, 0))
    m.part("compass_blade", "compass", pivot=(0, 1, 0), rot=(0, 0, 7))
    m.part("compass_leg", "compass", pivot=(0, 1, 0), rot=(0, 0, -9))
    # lower arms: thin, from the ribs
    m.part("arm_lr", "chest", pivot=(-6.5, -9, -1), rot=(-24, 0, 42))
    m.part("fore_lr", "arm_lr", pivot=(0, 12, 0), rot=(-64, 0, -30))
    m.part("square", "fore_lr", pivot=(0, 12, 0))
    m.part("arm_ll", "chest", pivot=(6.5, -9, -1), rot=(-18, 0, -40))
    m.part("fore_ll", "arm_ll", pivot=(0, 12, 0), rot=(-56, 0, 30))
    m.part("lantern", "fore_ll", pivot=(0, 12, 0), rot=(70, 0, -10))

    # ---- the cassock: a narrow column to the floor, a torn hem marked like a mason's rule
    m.box("pelvis", -7, -3, -5, 14, 6, 10, cassock(1))
    m.box("skirt", -8, 3, -6, 16, 13, 12, cassock(2, spire=True))
    m.box("skirt", -9, 16, -6.5, 18, 12, 13, cassock(3))
    m.box("hem", -10, 0, -7.5, 20, 12, 15, cassock(4, ragged=True, rule=True))
    m.box("hem", -5, 9, -10, 3, 3, 4, IRON_D)                                # pointed shoes under the hem
    m.box("hem", 2, 9, -10, 3, 3, 4, IRON_D)
    # a rope belt with a mason's mallet at the hip
    m.box("pelvis", -7.5, -3, -5.5, 15, 2, 11, {"*": lambda f, x, y, w, h: (150, 128, 92) if (x + y) % 3 else (110, 92, 62)})
    m.box("pelvis", 6.5, -1, -2, 2, 8, 2, (110, 80, 52))                      # the mallet's handle
    m.box("pelvis", 5.5, 7, -3.5, 4, 4, 5, (126, 92, 60))                    # the mallet's head

    # ---- the gaunt torso: ribs under thin wool, the harness of the chains on the back
    m.box("waist", -6, -10, -4, 12, 11, 8, cassock(6, seam=True))
    m.box("chest", -7, -22, -4.5, 14, 13, 9, cassock(7, seam=True))
    m.box("chest", -9, -24, -5, 18, 4, 10, cassock(8))                       # the shoulders
    for i, y in enumerate((-19, -16, -13)):                                  # brass buttons down the front
        m.box("chest", -0.5, y, -5.5, 1, 1, 1, BRASS_L)
    m.box("chest", -6, -23, 4, 12, 3, 2, IRON)                               # the harness: a yoke on the back
    m.box("chest", -1.5, -21, 4.5, 3, 14, 2, IRON)                           # its spine strap
    m.box("chest", -2.5, -23.5, 5.5, 5, 3, 2, brass(10))                     # the ring the chains hang from
    m.box("stole", -2.5, 0, -0.5, 5, 34, 1, stole(12))
    m.box("cape", -10, -1, -6, 20, 10, 12, cape(14))                         # the short cape over the shoulders
    m.box("cape", -5, -3, 4, 10, 6, 4, cape(15))                             # the hood thrown back
    # the chains: three strands rising to broken hooks high above the mitre
    for part, seed in (("chain_r", 20), ("chain_m", 21), ("chain_l", 22)):
        ln = 44 if part == "chain_m" else 38
        m.box(part, -1, -ln, -1, 2, ln, 2, chain_paint())
        m.box(part, -2, -ln - 3, -1, 4, 3, 2, IRON_D)                        # a broken hook
        m.box(part, -2, -ln - 5, -1, 2, 2, 2, IRON_L)

    # ---- head: the limestone mask in a hood, a pinnacle mitre
    m.box("neck", -2, -6, -2, 4, 7, 4, skin(30))
    m.box("head", -4.5, -10, -5, 9, 10, 8, mask_paint, glow=mask_glow)
    m.box("head", -5.5, -11, -3.5, 11, 12, 9, cape(31))                      # the hood round the mask
    m.box("mitre", -4, -6, -3, 8, 6, 7, stone(32, carve=True))
    m.box("mitre", -3, -12, -2, 6, 6, 5, stone(33, carve=True))
    m.box("mitre", -2, -17, -1, 4, 5, 3, stone(34, carve=True))
    m.box("mitre", -1, -21, -0.5, 2, 4, 2, stone(35))
    m.box("mitre", -4.5, -2, -3.5, 9, 1, 8, GOLD_D)                          # a gilt band
    m.box("mitre", -0.5, -9, -2.5, 1, 1, 1, SOUL, glow=SOUL)                 # a soul gem on the mitre

    # ---- right upper arm: the plumb-bob flail
    m.box("arm_ur", -2, -2, -2, 4, 20, 4, skin(40))
    m.box("arm_ur", -3.5, -3, -3.5, 7, 12, 7, cassock(41, ragged=True))      # a wide torn sleeve
    m.box("fore_ur", -1.5, 0, -1.5, 3, 18, 3, skin(42))
    m.box("fore_ur", -2, 17, -2, 4, 4, 4, skin(43))                          # the hand
    m.box("fore_ur", -1, 20, -1, 2, 3, 2, (110, 80, 52))                     # the flail's grip
    m.box("flail", -0.5, 0, -0.5, 1, 20, 1, chain_paint(IRON, IRON_L, IRON_D))
    m.box("bob", -1, -1, -1, 2, 2, 2, brass(50))                             # the ring
    m.box("bob", -3, 1, -3, 6, 2, 6, brass(51))                              # the brass cap
    m.box("bob", -5, 3, -5, 10, 6, 10, lead(52, line=True), glow=lead_glow)
    m.box("bob", -3.5, 9, -3.5, 7, 4, 7, lead(53, line=True), glow=lead_glow)
    m.box("bob", -2, 13, -2, 4, 3, 4, lead(54))
    m.box("bob", -1, 16, -1, 2, 3, 2, brass(55))                             # the point
    m.box("bob", -5.5, 5, -5.5, 11, 1, 11, BRASS_D)                            # a brass girdle

    # ---- left upper arm: the compass-blade
    m.box("arm_ul", -2, -2, -2, 4, 20, 4, skin(60))
    m.box("arm_ul", -3.5, -3, -3.5, 7, 12, 7, cassock(61, ragged=True))
    m.box("fore_ul", -1.5, 0, -1.5, 3, 18, 3, skin(62))
    m.box("fore_ul", -2, 17, -2, 4, 4, 4, skin(63))
    m.box("compass", -2.5, -2.5, -1.5, 5, 5, 3, brass(70))                  # the hinge disc
    m.box("compass", -1, -4.5, -1, 2, 2, 2, BRASS_L)                         # its finial
    m.box("compass_blade", -1.5, 0, -1, 3, 32, 2, blade(71))                 # the blade leg
    m.box("compass_blade", -1, 32, -0.5, 2, 3, 1, STEEL_L)                   # its point
    m.box("compass_leg", -0.5, 0, -0.5, 1, 30, 1, IRON_L)                    # the needle leg
    m.box("compass_leg", -0.5, 30, -0.5, 1, 2, 1, STEEL_L)
    m.box("compass", -3, 10, -0.5, 6, 1, 1, BRASS_D)                         # the arc that sets the span

    # ---- the lower arms: a set-square and a soul lantern
    m.box("arm_lr", -1, 0, -1, 2, 13, 2, skin(80))
    m.box("arm_lr", -2, -1, -2, 4, 6, 4, cassock(81, ragged=True))
    m.box("fore_lr", -1, 0, -1, 2, 12, 2, skin(82))
    m.box("fore_lr", -1.5, 11, -1.5, 3, 3, 3, skin(83))
    m.box("square", -0.5, 0, -8, 1, 2, 11, square_paint)                     # the set-square's long arm
    m.box("square", -0.5, -7, -8, 1, 7, 2, square_paint)                     # its short arm
    m.box("arm_ll", -1, 0, -1, 2, 13, 2, skin(84))
    m.box("arm_ll", -2, -1, -2, 4, 6, 4, cassock(85, ragged=True))
    m.box("fore_ll", -1, 0, -1, 2, 12, 2, skin(86))
    m.box("fore_ll", -1.5, 11, -1.5, 3, 3, 3, skin(87))
    m.box("lantern", -0.5, 0, -0.5, 1, 3, 1, IRON_D)
    m.box("lantern", -2.5, 3, -2.5, 5, 1, 5, IRON)
    m.box("lantern", -2, 4, -2, 4, 5, 4, lantern_paint, glow=lantern_glow)
    m.box("lantern", -2.5, 9, -2.5, 5, 1, 5, IRON)

    _anims(m)
    return m


Z = (0, 0, 0)


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, Z), (2.0, (0, 0.7, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.3, (4, 10, 0)), (2.6, (0, -8, 4)), (4.0, Z))
    idle.rot("chain_r", (0, Z), (1.0, (3, 0, 3)), (2.5, (-2, 0, -2)), (4.0, Z))
    idle.rot("chain_m", (0, Z), (1.5, (-3, 0, 2)), (3.0, (2, 0, -2)), (4.0, Z))
    idle.rot("chain_l", (0, Z), (1.2, (2, 0, -3)), (2.8, (-3, 0, 2)), (4.0, Z))
    idle.rot("flail", (0, Z), (1.0, (12, 0, 6)), (2.0, Z), (3.0, (-12, 0, -6)), (4.0, Z))
    idle.rot("bob", (0, Z), (1.0, (-6, 0, 0)), (2.0, Z), (3.0, (6, 0, 0)), (4.0, Z))
    idle.rot("lantern", (0, Z), (1.4, (10, 0, 6)), (2.8, (-8, 0, -4)), (4.0, Z))
    idle.rot("arm_lr", (0, Z), (2.0, (-4, 0, 3)), (4.0, Z))
    idle.rot("arm_ll", (0, Z), (2.0, (-4, 0, -3)), (4.0, Z))
    idle.rot("compass_leg", (0, Z), (2.0, (0, 0, -3)), (4.0, Z))
    idle.rot("hem", (0, Z), (2.0, (2, 0, 1)), (4.0, Z))
    idle.rot("stole", (0, Z), (2.0, (4, 0, 2)), (4.0, Z))

    walk = m.anim("walk", 2.0)
    walk.rot("skirt", (0, (0, 0, 2)), (1.0, (0, 0, -2)), (2.0, (0, 0, 2)))
    walk.rot("hem", (0, (-6, 0, 3)), (0.5, (6, 0, 0)), (1.0, (-6, 0, -3)), (1.5, (6, 0, 0)), (2.0, (-6, 0, 3)))
    walk.pos("pelvis", (0, Z), (0.5, (0, 0.9, 0)), (1.0, Z), (1.5, (0, 0.9, 0)), (2.0, Z))
    walk.rot("chest", (0, (0, 5, 0)), (1.0, (0, -5, 0)), (2.0, (0, 5, 0)))
    walk.rot("arm_ur", (0, (8, 0, 0)), (1.0, (-8, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("arm_ul", (0, (-8, 0, 0)), (1.0, (8, 0, 0)), (2.0, (-8, 0, 0)))
    walk.rot("flail", (0, (18, 0, 0)), (1.0, (-14, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("lantern", (0, (12, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (12, 0, 0)))
    walk.rot("stole", (0, (8, 0, 0)), (1.0, (14, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("chain_m", (0, (4, 0, 0)), (1.0, (-4, 0, 0)), (2.0, (4, 0, 0)))

    # compass (1.4 s): the compass-blade drawn up and back over his left shoulder (0.6 s = 12 ticks), then slashed
    # down across his front
    a = m.anim("compass", 1.4)
    a.rot("arm_ul", (0, Z), (0.5, (-150, 0, -40)), (0.6, (-156, 0, -42)), (0.72, (-40, 30, 30), "linear"),
          (0.9, (-34, 32, 34)), (1.4, Z))
    a.rot("fore_ul", (0, Z), (0.6, (30, 0, 0)), (0.72, (20, 0, 0), "linear"), (1.4, Z))
    a.rot("compass", (0, Z), (0.6, (-30, 0, 0)), (0.72, (20, 0, 0), "linear"), (1.4, Z))
    a.rot("chest", (0, Z), (0.6, (-6, -24, 0)), (0.72, (14, 28, 0), "linear"), (0.9, (12, 30, 0)), (1.4, Z))
    a.rot("arm_ur", (0, Z), (0.6, (10, 0, 20)), (0.72, (-20, 0, 10), "linear"), (1.4, Z))
    a.rot("flail", (0, Z), (0.6, (-20, 0, 10)), (0.8, (40, 0, -20)), (1.4, Z))
    a.rot("hem", (0, Z), (0.6, (0, -8, 0)), (0.8, (0, 10, 0)), (1.4, Z))

    # flail (1.9 s): the plumb-bob whirled overhead on its chain (0.9 s = 18 ticks), then swept round in a huge
    # circle at the height of a man's chest
    a = m.anim("flail", 1.9)
    a.rot("arm_ur", (0, Z), (0.3, (-150, 0, 30)), (0.9, (-160, 0, 34)), (1.05, (-90, -60, 70), "linear"),
          (1.25, (-86, -70, 74)), (1.9, Z))
    a.rot("fore_ur", (0, Z), (0.3, (30, 0, 0)), (0.9, (36, 0, 0)), (1.05, (40, 0, 0), "linear"), (1.9, Z))
    a.rot("flail", (0, Z), (0.2, (-100, 0, 0)), (0.4, (-100, 180, 0)), (0.6, (-100, 360, 0)), (0.8, (-100, 540, 0)),
          (0.9, (-100, 620, 0)), (1.05, (-90, 700, 0), "linear"), (1.25, (-80, 720, 0)), (1.9, Z))
    a.rot("chest", (0, Z), (0.9, (-8, 34, 0)), (1.05, (10, -40, 0), "linear"), (1.25, (8, -44, 0)), (1.9, Z))
    a.rot("waist", (0, Z), (0.9, (0, 12, 0)), (1.05, (0, -14, 0), "linear"), (1.9, Z))
    a.rot("arm_ul", (0, Z), (0.9, (-30, 0, -40)), (1.05, (-10, 0, -20), "linear"), (1.9, Z))
    a.rot("hem", (0, Z), (0.9, (0, 10, 0)), (1.1, (0, -12, 0)), (1.9, Z))

    # plummet (2.4 s): the plumb-bob raised high behind him (1.0 s = 20 ticks), then hurled forward to crash down
    # 9 blocks ahead; reeled back along the floor at 1.4 s
    a = m.anim("plummet", 2.4)
    a.rot("arm_ur", (0, Z), (0.8, (-170, 0, 16)), (1.0, (-176, 0, 18)), (1.1, (-70, 0, 6), "linear"),
          (1.4, (-74, 0, 6)), (1.6, (-30, 0, 20), "linear"), (2.4, Z))
    a.rot("fore_ur", (0, Z), (1.0, (40, 0, 0)), (1.1, (0, 0, 0), "linear"), (1.4, (0, 0, 0)), (1.6, (-30, 0, 0)), (2.4, Z))
    a.rot("flail", (0, Z), (0.8, (80, 0, 0)), (1.0, (100, 0, 0)), (1.1, (-60, 0, 0), "linear"), (1.4, (-70, 0, 0)),
          (1.6, (20, 0, 0), "linear"), (2.4, Z))
    a.scale("flail", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.1, (1, 3.2, 1), "linear"), (1.4, (1, 3.2, 1)),
            (1.6, (1, 1, 1), "linear"), (2.4, (1, 1, 1)))
    a.scale("bob", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.1, (1, 0.3125, 1), "linear"), (1.4, (1, 0.3125, 1)),
            (1.6, (1, 1, 1), "linear"), (2.4, (1, 1, 1)))
    a.rot("chest", (0, Z), (1.0, (-14, 14, 0)), (1.1, (22, -6, 0), "linear"), (1.4, (20, -6, 0)), (1.6, (6, 10, 0)),
          (2.4, Z))
    a.rot("head", (0, Z), (1.0, (-20, 0, 0)), (1.1, (6, 0, 0), "linear"), (2.4, Z))
    a.rot("arm_ul", (0, Z), (1.0, (10, 0, -30)), (1.1, (30, 0, -36), "linear"), (2.4, Z))

    # masonry (3.5 s): plumb and compass lifted to the vault, his mask turned up (1.1 s = 22 ticks), then both arms
    # snapped down: the masonry falls on the marked spots
    a = m.anim("masonry", 3.5)
    a.rot("arm_ur", (0, Z), (0.9, (-168, 0, 20)), (1.1, (-174, 0, 22)), (1.2, (-40, 0, 40), "linear"),
          (2.8, (-40, 0, 40)), (3.5, Z))
    a.rot("arm_ul", (0, Z), (0.9, (-168, 0, -20)), (1.1, (-174, 0, -22)), (1.2, (-40, 0, -40), "linear"),
          (2.8, (-40, 0, -40)), (3.5, Z))
    a.rot("fore_ur", (0, Z), (1.1, (40, 0, 0)), (1.2, (0, 0, 0), "linear"), (3.5, Z))
    a.rot("fore_ul", (0, Z), (1.1, (46, 0, 0)), (1.2, (0, 0, 0), "linear"), (3.5, Z))
    a.rot("flail", (0, Z), (1.1, (130, 0, 0)), (1.2, (-20, 0, 0), "linear"), (1.6, (30, 0, 0)), (2.2, (-10, 0, 0)),
          (3.5, Z))
    a.rot("head", (0, Z), (1.1, (-40, 0, 0)), (1.2, (-10, 0, 0), "linear"), (2.8, (-14, 0, 0)), (3.5, Z))
    a.rot("chest", (0, Z), (1.1, (-26, 0, 0)), (1.2, (10, 0, 0), "linear"), (2.8, (8, 0, 0)), (3.5, Z))
    a.rot("arm_lr", (0, Z), (1.1, (-60, 0, 30)), (1.2, (-20, 0, 30), "linear"), (3.5, Z))
    a.rot("arm_ll", (0, Z), (1.1, (-60, 0, -30)), (1.2, (-20, 0, -30), "linear"), (3.5, Z))

    # swingdrop (2.3 s): crouched, his upper hands reaching up to the chains (0.9 s = 18 ticks), then flung across the
    # arena on them; he lands compass first at 1.5 s
    a = m.anim("swingdrop", 2.3)
    a.pos("pelvis", (0, Z), (0.8, (0, -7, 0)), (0.9, (0, -7, 0)), (1.0, (0, 2, 0), "linear"), (1.45, (0, 2, 0)),
          (1.5, (0, -8, 0), "linear"), (1.8, (0, -6, 0)), (2.3, Z))
    a.rot("arm_ur", (0, Z), (0.8, (-170, 0, 14)), (0.9, (-176, 0, 12)), (1.45, (-176, 0, 12)),
          (1.5, (-60, 0, 30), "linear"), (2.3, Z))
    a.rot("arm_ul", (0, Z), (0.8, (-170, 0, -14)), (0.9, (-176, 0, -12)), (1.45, (-150, 0, -12)),
          (1.5, (-40, 0, -10), "linear"), (1.8, (-44, 0, -10)), (2.3, Z))
    a.rot("compass", (0, Z), (1.45, (-60, 0, 0)), (1.5, (30, 0, 0), "linear"), (2.3, Z))
    a.rot("chest", (0, Z), (0.9, (30, 0, 0)), (1.0, (-10, 0, 0), "linear"), (1.45, (-6, 0, 0)), (1.5, (34, 0, 0), "linear"),
          (1.8, (30, 0, 0)), (2.3, Z))
    a.rot("hem", (0, Z), (1.0, (20, 0, 0)), (1.45, (24, 0, 0)), (1.6, (-6, 0, 0)), (2.3, Z))
    a.rot("flail", (0, Z), (1.0, (-50, 0, 0)), (1.45, (-60, 0, 0)), (1.7, (30, 0, 0)), (2.3, Z))

    # scribe (2.5 s, phase 2): the compass's needle planted at his feet (0.8 s = 16 ticks), then he spins once round
    # it, the blade leg sweeping a circle (outer ring at 0.8 s), and draws the blade in at 1.5 s
    a = m.anim("scribe", 2.5)
    a.rot("arm_ul", (0, Z), (0.7, (-60, 0, -60)), (0.8, (-64, 0, -64)), (1.5, (-64, 0, -64)), (1.55, (-30, 0, -10), "linear"),
          (1.8, (-30, 0, -10)), (2.5, Z))
    a.rot("compass_blade", (0, Z), (0.8, (0, 0, 50)), (1.5, (0, 0, 50)), (1.55, (0, 0, 0), "linear"), (2.5, Z))
    a.rot("bone", (0, Z), (0.8, (0, 30, 0)), (1.05, (0, -60, 0), "linear"), (1.3, (0, -150, 0), "linear"),
          (1.5, (0, -240, 0), "linear"), (1.8, (0, -330, 0), "linear"), (2.0, (0, -360, 0)),
          (2.02, Z, "linear"), (2.5, Z))
    a.rot("chest", (0, Z), (0.8, (24, -20, 0)), (1.8, (24, -20, 0)), (2.5, Z))
    a.rot("hem", (0, Z), (0.8, (0, 0, 0)), (1.0, (0, 0, -16)), (1.8, (0, 0, -16)), (2.5, Z))
    a.rot("flail", (0, Z), (0.8, Z), (1.0, (0, 0, 70)), (1.8, (0, 0, 70)), (2.5, Z))
    a.rot("stole", (0, Z), (1.0, (0, 0, -30)), (1.8, (0, 0, -30)), (2.5, Z))

    # eclipse (4.1 s, phase 2): the soul lantern raised high (1.0 s = 20 ticks) and snuffed: darkness. He stalks low,
    # compass-blade ready, and slashes at 3.0 s
    a = m.anim("eclipse", 4.1)
    a.rot("arm_ll", (0, Z), (0.8, (-160, 0, -10)), (1.0, (-166, 0, -8)), (1.1, (-40, 0, -30), "linear"), (3.4, (-40, 0, -30)),
          (4.1, Z))
    a.scale("lantern", (0, (1, 1, 1)), (1.0, (1.3, 1.3, 1.3)), (1.1, (0.6, 0.6, 0.6), "linear"), (3.4, (0.6, 0.6, 0.6)),
            (4.1, (1, 1, 1)))
    a.rot("head", (0, Z), (1.0, (-30, 0, 0)), (1.2, (10, 0, 0)), (2.6, (10, 0, 0)), (2.9, (-6, 0, 0)), (4.1, Z))
    a.rot("chest", (0, Z), (1.0, (-10, 0, 0)), (1.3, (34, 0, 0)), (2.85, (34, 20, 0)), (3.0, (36, 24, 0)),
          (3.1, (30, -36, 0), "linear"), (3.4, (28, -36, 0)), (4.1, Z))
    a.pos("pelvis", (0, Z), (1.0, (0, 0, 0)), (1.3, (0, -6, 0)), (3.4, (0, -6, 0)), (4.1, Z))
    a.rot("arm_ul", (0, Z), (1.3, (-60, 0, -30)), (2.85, (-140, 0, -40)), (3.0, (-150, 0, -44)),
          (3.1, (-40, 40, 30), "linear"), (3.4, (-36, 40, 30)), (4.1, Z))
    a.rot("arm_ur", (0, Z), (1.3, (20, 0, 20)), (3.4, (20, 0, 20)), (4.1, Z))
    a.rot("hem", (0, Z), (1.3, (10, 0, 0)), (2.0, (14, 0, 4)), (2.7, (10, 0, -4)), (3.4, (12, 0, 0)), (4.1, Z))

    # keystone (4.7 s, phase 2): all four hands raised to the vault (1.0 s = 20 ticks) to mark a checkerboard of
    # falling stones; the first half falls at 2.2 s (the other half marked), the second at 3.4 s
    a = m.anim("keystone", 4.7)
    for side, sx in (("r", 1), ("l", -1)):
        a.rot(f"arm_u{side}", (0, Z), (0.8, (-160, 0, 30 * sx)), (1.0, (-166, 0, 32 * sx)), (1.1, (-70, 0, 50 * sx), "linear"),
              (2.1, (-150, 0, 30 * sx)), (2.2, (-60, 0, 50 * sx), "linear"), (3.3, (-150, 0, 30 * sx)),
              (3.4, (-50, 0, 50 * sx), "linear"), (4.0, (-50, 0, 50 * sx)), (4.7, Z))
        a.rot(f"arm_l{side}", (0, Z), (0.8, (-120, 0, 40 * sx)), (1.0, (-124, 0, 42 * sx)), (2.2, (-110, 0, 40 * sx)),
              (3.4, (-100, 0, 40 * sx)), (4.0, (-60, 0, 30 * sx)), (4.7, Z))
    a.rot("head", (0, Z), (1.0, (-40, 0, 0)), (1.1, (-10, 0, 0), "linear"), (3.4, (-12, 0, 0)), (4.7, Z))
    a.rot("chest", (0, Z), (1.0, (-20, 0, 0)), (1.1, (6, 0, 0), "linear"), (2.1, (-10, 0, 0)), (2.2, (8, 0, 0), "linear"),
          (3.3, (-10, 0, 0)), (3.4, (10, 0, 0), "linear"), (4.7, Z))
    a.rot("flail", (0, Z), (1.0, (150, 0, 0)), (1.1, (0, 0, 0), "linear"), (2.1, (150, 0, 0)), (2.2, (0, 0, 0), "linear"),
          (3.3, (150, 0, 0)), (3.4, (0, 0, 0), "linear"), (4.7, Z))

    # unmoor (3.0 s, phase 3, invulnerable): the plumb-bob raised in both upper hands (1.5 s = 30 ticks), then driven
    # into the floor: the island breaks up
    a = m.anim("unmoor", 3.0)
    a.rot("arm_ur", (0, Z), (1.2, (-170, 0, -10)), (1.5, (-176, 0, -12)), (1.6, (-50, 0, -20), "linear"),
          (2.4, (-50, 0, -20)), (3.0, Z))
    a.rot("arm_ul", (0, Z), (1.2, (-170, 0, 10)), (1.5, (-176, 0, 12)), (1.6, (-50, 0, 20), "linear"),
          (2.4, (-50, 0, 20)), (3.0, Z))
    a.rot("flail", (0, Z), (1.5, (140, 0, 0)), (1.6, (-30, 0, 0), "linear"), (2.4, (-30, 0, 0)), (3.0, Z))
    a.pos("pelvis", (0, Z), (1.5, (0, 2, 0)), (1.6, (0, -10, 0), "linear"), (2.4, (0, -10, 0)), (3.0, Z))
    a.rot("chest", (0, Z), (1.5, (-24, 0, 0)), (1.6, (36, 0, 0), "linear"), (2.4, (34, 0, 0)), (3.0, Z))
    a.rot("head", (0, Z), (1.5, (-36, 0, 0)), (1.6, (10, 0, 0), "linear"), (3.0, Z))
    for name in ("chain_r", "chain_m", "chain_l"):
        a.rot(name, (0, Z), (1.5, (-10, 0, 0)), (1.6, (20, 0, 0), "linear"), (2.0, (-6, 0, 0)), (3.0, Z))

    # chainswing (7.1 s, phase 3): he crouches (1.2 s = 24 ticks) and leaps up onto the chains; he swings round the
    # arena hanging from them, diving three times (slams at 2.4, 3.9 and 5.4 s), and stays crouched after the last
    a = m.anim("chainswing", 7.1)
    hang = [(-176, 0, 10), (-176, 0, -10)]
    dive = [(-70, 0, 20), (-60, 0, -20)]
    keys_r, keys_l, keys_c = [(0, Z), (1.0, (-120, 0, 10)), (1.2, hang[0])], [(0, Z), (1.0, (-120, 0, -10)),
                                                                              (1.2, hang[1])], [(0, Z), (1.0, (30, 0, 0)), (1.2, (-10, 0, 0), "linear")]
    for slam in (2.4, 3.9, 5.4):
        keys_r += [(slam - 0.3, hang[0]), (slam, dive[0], "linear")]
        keys_l += [(slam - 0.3, hang[1]), (slam, dive[1], "linear")]
        keys_c += [(slam - 0.3, (-10, 0, 0)), (slam, (40, 0, 0), "linear")]
        if slam < 5:
            keys_r.append((slam + 0.3, hang[0]))
            keys_l.append((slam + 0.3, hang[1]))
            keys_c.append((slam + 0.3, (-10, 0, 0)))
    keys_r += [(6.2, dive[0]), (7.1, Z)]
    keys_l += [(6.2, dive[1]), (7.1, Z)]
    keys_c += [(6.2, (36, 0, 0)), (7.1, Z)]
    a.rot("arm_ur", *keys_r)
    a.rot("arm_ul", *keys_l)
    a.rot("chest", *keys_c)
    a.pos("pelvis", (0, Z), (1.0, (0, -7, 0)), (1.2, (0, 0, 0), "linear"), (5.4, (0, 0, 0)), (5.45, (0, -8, 0), "linear"),
          (6.2, (0, -7, 0)), (7.1, Z))
    a.rot("hem", (0, Z), (1.2, (20, 0, 0)), (2.0, (30, 0, 10)), (3.0, (24, 0, -10)), (4.0, (30, 0, 10)), (5.0, (24, 0, -10)),
          (5.4, (20, 0, 0)), (5.6, Z), (7.1, Z))
    a.rot("flail", (0, Z), (1.2, (-40, 0, 0)), (2.4, (-90, 0, 0)), (2.8, (-30, 0, 0)), (3.9, (-90, 0, 0)), (4.3, (-30, 0, 0)),
          (5.4, (-90, 0, 0)), (6.2, (-20, 0, 0)), (7.1, Z))
    for name in ("chain_r", "chain_m", "chain_l"):
        a.rot(name, (0, Z), (1.2, (24, 0, 0)), (5.4, (24, 0, 0)), (5.6, (-6, 0, 0)), (7.1, Z))

    # descend (3.8 s, the entrance): he hangs limp from the chains under the spire, swaying (1.5 s = 30 ticks), then
    # lets go and drops onto the island, landing in a crouch at about 2.1 s
    a = m.anim("descend", 3.8)
    a.rot("arm_ur", (0, Z), (0.1, (-176, 0, 8)), (1.5, (-176, 0, 8)), (1.6, (-110, 0, 60), "linear"), (2.1, (-60, 0, 40)),
          (2.6, (-50, 0, 30)), (3.8, Z))
    a.rot("arm_ul", (0, Z), (0.1, (-176, 0, -8)), (1.5, (-176, 0, -8)), (1.6, (-110, 0, -60), "linear"),
          (2.1, (-60, 0, -40)), (2.6, (-50, 0, -30)), (3.8, Z))
    a.rot("head", (0, Z), (0.1, (30, 0, 0)), (1.5, (30, 0, 10)), (1.6, (-20, 0, 0), "linear"), (2.1, (10, 0, 0)), (3.8, Z))
    a.rot("bone", (0, Z), (0.1, (0, 0, 0)), (0.6, (4, 0, 3)), (1.1, (-4, 0, -3)), (1.5, Z), (3.8, Z))
    a.rot("chest", (0, Z), (0.1, (-14, 0, 0)), (1.5, (-14, 0, 0)), (2.1, (34, 0, 0)), (2.6, (30, 0, 0)), (3.8, Z))
    a.pos("pelvis", (0, Z), (1.5, Z), (2.05, (0, 0, 0)), (2.1, (0, -10, 0), "linear"), (2.7, (0, -8, 0)), (3.8, Z))
    a.rot("hem", (0, Z), (0.1, (6, 0, 0)), (1.5, (6, 0, 0)), (1.6, (-30, 0, 0)), (2.1, (-30, 0, 0)), (2.3, (10, 0, 0)), (3.8, Z))
    a.rot("flail", (0, Z), (0.1, (-110, 0, 0)), (1.5, (-110, 0, 0)), (2.1, (-60, 0, 0)), (2.5, (30, 0, 0)), (3.8, Z))
    a.rot("arm_lr", (0, Z), (0.1, (20, 0, 4)), (1.5, (20, 0, 4)), (2.1, (-40, 0, 30)), (3.8, Z))
    a.rot("arm_ll", (0, Z), (0.1, (20, 0, -4)), (1.5, (20, 0, -4)), (2.1, (-40, 0, -30)), (3.8, Z))

    # roar (phase two): all four arms flung wide, mask thrown back, the chains shaking
    a = m.anim("roar", 2.0)
    a.rot("arm_ur", (0, Z), (0.6, (-60, 0, 80)), (1.6, (-64, 0, 84)), (2.0, Z))
    a.rot("arm_ul", (0, Z), (0.6, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, Z))
    a.rot("arm_lr", (0, Z), (0.6, (-30, 0, 60)), (1.6, (-30, 0, 64)), (2.0, Z))
    a.rot("arm_ll", (0, Z), (0.6, (-30, 0, -60)), (1.6, (-30, 0, -64)), (2.0, Z))
    a.rot("head", (0, Z), (0.6, (-40, 0, 0)), (1.6, (-36, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.6, (-22, 0, 0)), (1.6, (-20, 0, 0)), (2.0, Z))
    for i, name in enumerate(("chain_r", "chain_m", "chain_l")):
        a.rot(name, (0, Z), (0.7, (8, 0, 6 - 6 * i)), (0.9, (-8, 0, -6 + 6 * i)), (1.1, (8, 0, 6 - 6 * i)),
              (1.3, (-6, 0, 0)), (2.0, Z))

    # stagger: he sags on his chains, knees buckling, all four arms limp
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, Z), (0.3, (0, -10, 0)), (1.6, (0, -10, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.3, (34, 0, -8)), (1.6, (36, 0, -8)), (2.0, Z))
    a.rot("head", (0, Z), (0.3, (26, 0, 12)), (1.6, (28, 0, 12)), (2.0, Z))
    a.rot("arm_ur", (0, Z), (0.3, (30, 0, -6)), (1.6, (32, 0, -6)), (2.0, Z))
    a.rot("arm_ul", (0, Z), (0.3, (36, 0, 4)), (1.6, (38, 0, 4)), (2.0, Z))
    a.rot("arm_lr", (0, Z), (0.3, (30, 0, -10)), (1.6, (30, 0, -10)), (2.0, Z))
    a.rot("arm_ll", (0, Z), (0.3, (30, 0, 10)), (1.6, (30, 0, 10)), (2.0, Z))
    a.rot("hem", (0, Z), (0.3, (0, 0, 0)), (2.0, Z))
