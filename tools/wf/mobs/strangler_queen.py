"""The Strangler Fig Queen (La Reine-figuier étrangleur): the lost queen of the Canopy Temple-City, about 6.1 blocks tall.

Silhouette idea: a tree that is a woman. A towering, slender queen of woven roots rises out of a flared skirt of
strangler-fig roots that pours over the summit floor and grips it (thick roots splayed out round her like the buttress
roots of the trunks round her city); her torso is braided root armoured with carved jade (a pectoral, a collar of jade
beads, a jade belt), her face a serene jade mask with glowing gold eyes, and on her head a crown of big orchids
(magenta, pink, white) and bromeliad spikes, aerial roots hanging from it down her back like hair. Strong asymmetry:
her LEFT arm is a long thorned root-whip in five tapering segments that trails on the floor, barbed at the tip; in her
RIGHT hand a jade macuahuitl (a flat paddle of dark wood edged with jade and obsidian teeth). Moss and little orchids
grow on her shoulders and in the skirt.

The same file builds ``jaguar_spirit``: the see-through jade jaguars she drops from the canopy in phase 2.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

ROOT = (98, 74, 54)            # strangler-fig root bark
ROOT_L = (146, 116, 84)
ROOT_D = (58, 42, 32)
AERIAL = (176, 156, 122)       # pale hanging aerial roots
AERIAL_D = (120, 102, 78)
JADE = (58, 158, 108)
JADE_L = (138, 222, 166)
JADE_D = (28, 94, 64)
JADE_DD = (18, 60, 42)
GOLD = (214, 174, 74)
GOLD_D = (140, 104, 40)
MOSS = (86, 128, 50)
MOSS_L = (132, 170, 74)
MOSS_D = (48, 78, 30)
LEAF = (58, 132, 52)
LEAF_L = (110, 176, 80)
LEAF_D = (34, 84, 34)
ORCHID = (226, 92, 176)        # magenta
ORCHID_L = (250, 170, 220)
ORCHID_P = (240, 140, 196)     # pink
ORCHID_W = (246, 238, 244)     # white
ORCHID_C = (250, 214, 84)      # the yellow lip
EYE = (255, 236, 140)
EYE_L = (255, 250, 214)
THORN = (214, 200, 160)
THORN_D = (150, 132, 96)
OBSID = (36, 28, 50)
OBSID_L = (88, 70, 120)
WOOD = (82, 50, 34)            # the macuahuitl's dark wood
WOOD_L = (124, 82, 54)
WOOD_D = (50, 30, 20)


# ---------------------------------------------------------------- paint
def bark(seed=0, mossy=0.08, pale=False):
    """Braided strangler-fig roots: diagonal strands crossing (a plait), dark grooves between them, moss in the
    hollows; the paler aerial-root version for the hair."""
    base, light, dark = (AERIAL, mix(AERIAL, (240, 230, 200), 0.3), AERIAL_D) if pale else (ROOT, ROOT_L, ROOT_D)

    def f(face, x, y, w, h):
        if face == "bottom":
            return dark
        if face == "top":
            return light if (x + y) % 3 else base
        k = (x + y) % 6
        k2 = (x - y) % 6
        c = base
        if k == 0 or k2 == 0:
            c = dark                                                   # the grooves of the plait
        elif k == 1 or k2 == 1:
            c = light                                                  # a strand catching the light
        c = mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.14 - 0.08 * y / max(1, h))
        if mossy and B.n(x // 2, y // 2, seed + 7) < mossy:
            c = mix(c, MOSS, 0.75)
        return c
    return f


def strands(seed=0, pale=False, ragged=0):
    """Vertical root strands (the skirt, the hair): each column a root, with knots; an uneven, ragged end."""
    base, light, dark = (AERIAL, mix(AERIAL, (240, 230, 200), 0.3), AERIAL_D) if pale else (ROOT, ROOT_L, ROOT_D)

    def f(face, x, y, w, h):
        if face == "bottom":
            return dark
        if ragged and face != "top":
            cut = h - 1 - int(B.n(x, 0, seed) * ragged)
            if y > cut:
                return None
        col = (x + int(B.n(x, 1, seed) * 2)) % 3
        c = (light, base, dark)[col]
        if B.n(x, y // 3, seed + 3) < 0.10:
            c = mix(c, dark, 0.6)                                       # a knot
        c = mul(c, 1.04 - 0.14 * y / max(1, h))
        if not pale and B.n(x // 2, y // 3, seed + 5) < 0.09:
            c = mix(c, MOSS, 0.7)
        if face == "top":
            c = light
        return c
    return f


def jade(seed=0, rim=True, glyph=False):
    """Carved jade: deep green with paler veins, a polished highlight top-left, a gold rim; an optional glyph."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return JADE_D
        if rim and (x in (0, w - 1) or y in (0, h - 1)) and face not in ("top",):
            return GOLD if (x + y) % 2 else GOLD_D
        v = B.n(x // 2 + y, y // 3, seed)
        c = mix(JADE, JADE_L, 0.35) if v < 0.16 else JADE
        if B.n(x, y, seed + 2) < 0.07:
            c = JADE_D
        c = mul(c, 1.08 - 0.18 * (x + y) / max(1, w + h))
        if glyph and face in ("front", "back") and 1 < x < w - 2 and 1 < y < h - 2:
            cx, cy = (w - 1) / 2, (h - 1) / 2
            if abs(x - cx) + abs(y - cy) in (2, 3) or (x == int(cx) and y == int(cy)):
                c = JADE_DD                                             # a carved sun glyph
        if face == "top":
            c = mix(c, JADE_L, 0.3)
        return c
    return f


def moss(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        c = mul(MOSS, 1.0 + (r - 0.5) * 0.25)
        if B.n(x // 2, y // 2, seed + 2) < 0.2:
            c = MOSS_D
        elif r > 0.85:
            c = MOSS_L
        return c
    return f


def leaf(seed=0):
    """A broad tropical leaf: a pale midrib, darker edges."""
    def f(face, x, y, w, h):
        if face in ("top", "front", "back"):
            if x == w // 2:
                return LEAF_L
            if x in (0, w - 1):
                return LEAF_D
            return mul(LEAF, 1.0 + (B.n(x, y, seed) - 0.5) * 0.18)
        return LEAF_D
    return f


def petal(color, seed=0):
    light = mix(color, (255, 255, 255), 0.4)
    dark = mul(color, 0.72)

    def f(face, x, y, w, h):
        if face == "bottom":
            return dark
        if (x in (0, w - 1)) and (y in (0, h - 1)):
            return dark
        return light if (x + y + seed) % 4 == 0 else color
    return f


def lip(face, x, y, w, h):
    return ORCHID_C if (x + y) % 2 else mix(ORCHID_C, ORCHID, 0.35)


def thorn(face, x, y, w, h):
    return THORN if face in ("top", "front", "left") else THORN_D


def obsidian(face, x, y, w, h):
    return OBSID_L if (x + y) % 3 == 0 else OBSID


def wood(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOD_D
        c = WOOD_L if (y + seed) % 5 == 0 else WOOD
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.12)
    return f


def mask_paint(f, x, y, w, h):
    """The jade mask: a serene, carved face, gold-lidded glowing eyes, a straight nose, closed lips, gold earrings."""
    if f != "front":
        return jade(70, rim=False)(f, x, y, w, h)
    if y == 3 and 1 <= x <= w - 2:
        return JADE_DD                                                 # the carved brow line
    if y == 4 and x in (1, 2, w - 3, w - 2):
        return GOLD                                                    # gold lids
    if y == 5 and x in (1, 2, w - 3, w - 2):
        return EYE_L if x in (2, w - 3) else EYE
    if 5 <= y <= 7 and x in (w // 2 - 1, w // 2):
        return JADE_L if y < 7 else JADE_D                             # the nose
    if y == 8 and w // 2 - 2 <= x <= w // 2 + 1:
        return (150, 60, 70) if 0 < x - (w // 2 - 2) < 3 else JADE_D   # closed lips, painted cinnabar
    if y in (6, 7) and x in (0, w - 1):
        return JADE_D                                                  # the cheekbones
    if y == h - 1:
        return JADE_D
    return jade(71, rim=False)(f, x, y, w, h)


def mask_glow(f, x, y, w, h):
    if f == "front" and y == 5 and x in (1, 2, w - 3, w - 2):
        return EYE_L if x in (2, w - 3) else EYE
    return None


def macuahuitl_teeth(face, x, y, w, h):
    """The teeth: alternating jade and obsidian blades set into the edge."""
    return (JADE_L if y % 2 == 0 else JADE) if (y // 2) % 2 == 0 else obsidian(face, x, y, w, h)


def teeth_glow(face, x, y, w, h):
    return JADE_L if (y // 2) % 2 == 0 and y % 2 == 0 else None


# ---------------------------------------------------------------- build
def build():
    m = Model("strangler_queen", seed=419, shadow=1.8, walk_speed=0.7, walk_scale=0.7, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    # the buttress roots splayed round her on the floor: eight roots, each turned about the vertical
    for k in range(8):
        a = k * 45 + (12 if k % 2 else -8)
        m.part(f"root_{k}", "bone", pivot=(0, 0, 0), rot=(0, a, 0))
    m.part("hips", "bone", pivot=(0, -40, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("waist", "hips", pivot=(0, -2, 0))
    m.part("chest", "waist", pivot=(0, -8, 0), rot=(-4, 0, 0))
    m.part("neck", "chest", pivot=(0, -18, -0.5))
    m.part("head", "neck", pivot=(0, -3, 0))
    m.part("crown", "head", pivot=(0, -10, 0))
    m.part("hair", "head", pivot=(0, -8, 3.5), rot=(7, 0, 0))
    m.part("arm_r", "chest", pivot=(-9.5, -15, 0), rot=(-10, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-38, 0, -4))
    m.part("maca", "fore_r", pivot=(0, 13, -0.5), rot=(4, 0, 0))
    m.part("whip_1", "chest", pivot=(9.5, -15, 0), rot=(4, 0, -24))
    m.part("whip_2", "whip_1", pivot=(0, 12, 0), rot=(-8, 0, 6))
    m.part("whip_3", "whip_2", pivot=(0, 13, 0), rot=(-14, 0, -10))
    m.part("whip_4", "whip_3", pivot=(0, 13, 0), rot=(20, 0, -40))
    m.part("whip_5", "whip_4", pivot=(0, 12, 0), rot=(30, 0, -36))

    # ---- the buttress roots on the floor: each a long root arching out of the skirt and running into the stone
    for k in range(8):
        p = f"root_{k}"
        ln = 9 + (k * 5) % 7
        m.box(p, -2, -4, -12 - ln, 4, 4, ln, bark(10 + k, mossy=0.14))
        m.box(p, -1.5, -10, -14, 3, 6, 4, bark(20 + k, mossy=0.1))                     # the arch into the skirt
        m.box(p, -1, -2, -14 - ln - 4, 2, 2, 5, bark(30 + k))                          # the thin end
        if k % 3 == 0:
            m.box(p, 1.5, -3, -16 - ln // 2, 2, 1, 2, thorn)

    # ---- the skirt: a cone of hanging root strands, flared, its ragged hem gripping the floor; moss, small orchids
    m.box("skirt", -8, -1, -6, 16, 9, 12, bark(40, mossy=0.1))
    m.box("skirt", -10, 7, -8, 20, 11, 16, strands(41))
    m.box("skirt", -12, 16, -10, 24, 12, 20, strands(42, ragged=2))
    m.box("skirt", -14, 26, -12, 28, 14, 24, strands(43, ragged=4))
    m.box("skirt", -9, 30, -13, 6, 10, 1, strands(44, ragged=3))                         # loose strands in front
    m.box("skirt", 3, 28, -13, 5, 12, 1, strands(45, ragged=3))
    m.box("skirt", -15, 22, -4, 1, 18, 8, strands(46, ragged=3))
    m.box("skirt", 14, 24, -6, 1, 16, 9, strands(47, ragged=3))
    for i, (x, z, y0, ln) in enumerate(((-11, -9, 8, 22), (9, -9, 6, 24), (-11, 7, 9, 22), (9, 7, 7, 23),
                                        (-4, -11, 12, 18), (2, 10, 14, 17), (-13, -1, 17, 13), (12, 2, 15, 15))):
        m.box("skirt", x, y0, z, 2, ln, 2, bark(160 + i, mossy=0.12))                 # roots spilling over the tiers
    m.box("skirt", -11, 14, -10, 6, 3, 1, moss(48))
    m.box("skirt", 6, 22, 9, 6, 4, 2, moss(49))
    for (x, y, z, col) in ((-11, 18, -11, ORCHID), (9, 26, -13, ORCHID_W), (12, 12, 7, ORCHID_P)):
        m.box("skirt", x, y, z, 3, 3, 1, petal(col, x))
        m.box("skirt", x + 1, y + 1, z - 0.5, 1, 1, 1, lip)
    m.box("skirt", -9, -2.5, -6.5, 18, 2, 13, jade(50, glyph=False))                     # the jade belt
    m.box("skirt", -2.5, -3, -7.2, 5, 5, 1, jade(51, glyph=True))                        # its buckle, a sun
    m.box("skirt", -2, 2, -7.0, 4, 10, 1, jade(52))                                      # a jade apron
    m.box("skirt", -1.5, 12, -7.0, 3, 3, 1, GOLD)

    # ---- the torso: a slender waist and chest of braided root, a jade pectoral, a collar of jade beads
    m.box("waist", -5.5, -8, -3.5, 11, 8, 7, bark(60))
    m.box("chest", -8, -18, -4.5, 16, 18, 9, bark(61))
    m.box("chest", -7, -15, -5.5, 14, 9, 1, jade(62, glyph=True))                        # the pectoral
    m.box("chest", -5, -6, -5.2, 10, 2, 1, jade(63))
    for i in range(9):                                                                   # the bead collar
        a = math.radians(-90 + i * 22.5)
        x, z = math.sin(a) * 7.5, -math.cos(a) * 4.8
        m.box("chest", x - 1, -18.5, z - 1, 2, 2, 2, jade(64 + i, rim=False))
    m.box("chest", -9.5, -18.5, -3.5, 4, 4, 7, moss(74))                                 # moss on the shoulders
    m.box("chest", 5.5, -19, -3.5, 4, 3, 7, moss(75))
    m.box("chest", 6, -21, -2, 3, 2, 1, petal(ORCHID_P, 3))                              # a little orchid
    m.box("chest", 7, -20.5, -2.5, 1, 1, 1, lip)
    m.box("chest", -4, -17, 4.5, 8, 14, 1, strands(76))                                  # the back, roots
    m.box("neck", -2, -4, -2, 4, 5, 4, bark(77))

    # ---- head: the jade mask, gold earspools; aerial roots hanging down her back like hair
    m.box("head", -4, -10, -4.5, 8, 10, 8, mask_paint, glow=mask_glow)
    m.box("head", -4.5, -11, -3, 9, 3, 8, bark(80))                                      # the root cap under the crown
    m.box("head", -5, -5, -1, 1, 3, 3, GOLD)                                             # earspools
    m.box("head", 4, -5, -1, 1, 3, 3, GOLD)
    m.box("head", -5.5, -2, -0.5, 1, 4, 2, jade(81, rim=False))
    m.box("head", 4.5, -2, -0.5, 1, 4, 2, jade(82, rim=False))
    for i, (x, ln) in enumerate(((-5, 30), (-3, 38), (-1, 44), (1, 40), (3, 34), (5, 28), (-4, 22), (2, 26))):
        m.box("hair", x - 0.5 if i < 6 else x, 0, (i % 3) * 0.6, 1 if i % 2 else 2, ln, 1,
              strands(84 + i, pale=True, ragged=2))
    m.box("hair", -5, 0, -0.5, 10, 6, 2, bark(92, pale=True))

    # ---- the crown: a band of root and jade, five big orchids, bromeliad spikes fanning up behind
    m.box("crown", -5, -2, -5, 10, 3, 9, bark(100))
    m.box("crown", -5.5, -1, -5.5, 11, 1, 1, jade(101, rim=False))
    for k, (a, h, w) in enumerate(((-60, 10, 3), (-30, 13, 3), (0, 16, 3), (30, 12, 3), (60, 9, 3), (90, 7, 2),
                                   (-90, 8, 2))):
        p = f"spike_{k}"
        m.part(p, "crown", pivot=(0, -1, 1), rot=(-18 if abs(a) < 80 else -6, 0, a * 0.55))
        m.box(p, -w / 2, -h, 0, w, h, 1, leaf(110 + k))
    orchids = ((-4.5, -4, -5, ORCHID), (0, -6, -5.5, ORCHID_W), (4.5, -4, -5, ORCHID_P),
               (-6, -3, -1, ORCHID_P), (6, -3, -1, ORCHID))
    for i, (x, y, z, col) in enumerate(orchids):
        p = f"orchid_{i}"
        m.part(p, "crown", pivot=(x, y, z), rot=(-10, 0, (i - 2) * 8))
        m.box(p, -3.5, -1.5, -0.5, 7, 3, 1, petal(col, i))                               # the side petals
        m.box(p, -1.5, -4, -0.5, 3, 7, 1, petal(col, i + 1))                             # top and bottom petals
        m.box(p, -1, -0.5, -1.4, 2, 2, 1, lip, glow=ORCHID_C)                            # the glowing lip

    # ---- right arm: braided root, a jade bracer, the macuahuitl
    m.box("arm_r", -3, -2, -3, 6, 15, 6, bark(120))
    m.box("arm_r", -3.5, -3, -3.5, 7, 4, 7, jade(121))                                   # a jade pauldron
    m.box("fore_r", -2.5, 0, -2.5, 5, 13, 5, bark(122))
    m.box("fore_r", -3, 5, -3, 6, 5, 6, jade(123, glyph=True))                           # the bracer
    m.box("fore_r", -2, 12, -2.5, 4, 3, 4, bark(124))                                    # the fist
    # the macuahuitl: a grip and pommel, then a broad flat paddle of dark wood, edged both sides with teeth
    m.box("maca", -1, -4, -1, 2, 10, 2, wood(130))
    m.box("maca", -1.5, -5, -1.5, 3, 2, 3, GOLD)                                         # the pommel
    m.box("maca", -1.5, 5, -1.5, 3, 1, 3, GOLD_D)                                        # the guard
    m.box("maca", -2.5, 6, -1, 5, 26, 2, wood(131))                                      # the paddle
    m.box("maca", -2, 31, -1, 4, 2, 2, wood(132))                                        # the rounded end
    m.box("maca", -1, 9, -1.4, 2, 18, 1, jade(133, rim=False))                           # an inlaid jade strip
    m.box("maca", -4, 8, -0.5, 2, 23, 1, macuahuitl_teeth, glow=teeth_glow)              # the teeth, both edges
    m.box("maca", 2, 8, -0.5, 2, 23, 1, macuahuitl_teeth, glow=teeth_glow)

    # ---- left arm: the thorned root-whip in five tapering segments, a barb at the tip
    sizes = ((6, 13), (5, 14), (4, 14), (3, 13), (2, 13))
    for i, (s, ln) in enumerate(sizes):
        p = f"whip_{i + 1}"
        m.box(p, -s / 2, -1, -s / 2, s, ln, s, bark(140 + i, mossy=0.06))
        for j in range(2 if i < 4 else 1):                                               # thorns along it
            y = 3 + j * 6
            side = (i + j) % 4
            if side == 0:
                m.box(p, -s / 2 - 2, y, -0.5, 2, 1, 1, thorn)
            elif side == 1:
                m.box(p, -0.5, y, -s / 2 - 2, 1, 1, 2, thorn)
            elif side == 2:
                m.box(p, s / 2, y, -0.5, 2, 1, 1, thorn)
            else:
                m.box(p, -0.5, y, s / 2, 1, 1, 2, thorn)
    m.box("whip_1", -3.5, -3, -3.5, 7, 4, 7, jade(149))                                  # the shoulder's jade
    m.box("whip_1", -2, 4, -4, 4, 3, 1, moss(150))
    m.box("whip_5", -1.5, 11, -1.5, 3, 3, 3, bark(151))                                  # the barbed tip
    m.box("whip_5", -3, 12, -0.5, 6, 1, 1, thorn)
    m.box("whip_5", -0.5, 12, -3, 1, 1, 6, thorn)
    m.box("whip_5", -0.5, 13, -0.5, 1, 4, 1, thorn)
    m.box("whip_3", 2, 6, -1, 3, 1, 3, petal(ORCHID_W, 5))                               # an orchid on the whip
    m.box("whip_3", 3, 5.5, -0.5, 1, 1, 1, lip)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, -0.6, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.4, (2, 8, 0)), (2.8, (-2, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("hair", (0, (0, 0, 0)), (2.0, (5, 0, 3)), (4.0, (0, 0, 0)))
    idle.rot("skirt", (0, (0, 0, 0)), (2.0, (1, 4, 0)), (4.0, (0, 0, 0)))
    idle.rot("whip_2", (0, (0, 0, 0)), (1.0, (-6, 0, 4)), (2.0, (0, 0, -2)), (3.0, (6, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("whip_4", (0, (0, 0, 0)), (1.0, (10, 0, -6)), (2.0, (-6, 0, 4)), (3.0, (8, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("whip_5", (0, (0, 0, 0)), (1.5, (-14, 0, 8)), (3.0, (10, 0, -6)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 2)), (4.0, (0, 0, 0)))
    for i in range(5):
        idle.rot(f"orchid_{i}", (0, (0, 0, 0)), (1.0 + i * 0.4, (6, 0, 4)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.4)
    walk.pos("hips", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (1.2, (0, 0, 0)), (1.8, (0, 1, 0)), (2.4, (0, 0, 0)))
    walk.rot("skirt", (0, (4, 6, 2)), (1.2, (4, -6, -2)), (2.4, (4, 6, 2)))
    walk.rot("chest", (0, (2, -5, 0)), (1.2, (2, 5, 0)), (2.4, (2, -5, 0)))
    walk.rot("whip_1", (0, (10, 0, 0)), (1.2, (-6, 0, 0)), (2.4, (10, 0, 0)))
    walk.rot("whip_4", (0, (10, 0, 0)), (1.2, (24, 0, 0)), (2.4, (10, 0, 0)))
    walk.rot("arm_r", (0, (-6, 0, 0)), (1.2, (8, 0, 0)), (2.4, (-6, 0, 0)))
    walk.rot("hair", (0, (12, 0, 0)), (1.2, (16, 0, 0)), (2.4, (12, 0, 0)))
    for k in range(8):
        walk.rot(f"root_{k}", (0, (0, 0, 0)), (0.6 + 0.2 * (k % 4), (-4, 0, 0)), (2.4, (0, 0, 0)))

    # lash: the whip drawn back over her left shoulder, coiled (0.8 s = 16 ticks), then cracked straight ahead
    a = m.anim("lash", 1.7)
    a.rot("whip_1", (0, (0, 0, 0)), (0.7, (-150, 0, -20)), (0.8, (-160, 0, -22)), (0.88, (-84, 0, 6), "linear"),
          (1.2, (-80, 0, 6)), (1.7, (0, 0, 0)))
    a.rot("whip_2", (0, (0, 0, 0)), (0.8, (60, 0, 0)), (0.88, (-10, 0, 0), "linear"), (1.2, (0, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("whip_3", (0, (0, 0, 0)), (0.8, (70, 0, 0)), (0.9, (-6, 0, 0), "linear"), (1.2, (0, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("whip_4", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (0.92, (-30, 0, 0), "linear"), (1.2, (-26, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("whip_5", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.94, (-46, 0, 0), "linear"), (1.2, (-40, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-8, -26, 0)), (0.88, (10, 18, 0), "linear"), (1.2, (8, 16, 0)), (1.7, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, -10, 0)), (0.88, (0, 8, 0), "linear"), (1.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (20, 0, 20)), (1.2, (10, 0, 14)), (1.7, (0, 0, 0)))
    a.rot("hair", (0, (0, 0, 0)), (0.8, (-6, 0, -8)), (1.0, (14, 0, 8)), (1.7, (0, 0, 0)))

    # combo: the macuahuitl raised over her right shoulder (0.7 s = 14 ticks), a forehand cut at 0.7 s, a backhand at
    # 1.2 s, an overhead blow at 1.7 s (the last in phase 2)
    a = m.anim("combo", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-120, -10, 50)), (0.7, (-126, -12, 54)), (0.78, (-70, 40, -40), "linear"),
          (1.1, (-80, 60, -50)), (1.2, (-70, -30, 50), "linear"), (1.5, (-160, 0, 10)), (1.7, (-160, 0, 10)),
          (1.78, (-50, 0, 6), "linear"), (2.0, (-50, 0, 6)), (2.6, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.78, (20, 0, 0), "linear"), (1.5, (30, 0, 0)), (1.78, (10, 0, 0)),
          (2.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 28, 0)), (0.78, (6, -30, 0), "linear"), (1.1, (4, -34, 0)),
          (1.2, (6, 30, 0), "linear"), (1.5, (-14, 0, 0)), (1.7, (-16, 0, 0)), (1.78, (20, 0, 0), "linear"),
          (2.0, (18, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.7, (0, 10, 0)), (0.78, (0, -10, 0), "linear"), (1.2, (0, 10, 0), "linear"),
          (1.78, (6, 0, 0), "linear"), (2.6, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.7, (0, 0, -30)), (1.2, (0, 0, -40)), (2.0, (-20, 0, -20)), (2.6, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.78, (0, -8, 0)), (1.2, (0, 8, 0)), (1.8, (4, 0, 0)), (2.6, (0, 0, 0)))

    # rootline: the whip plunged into the floor ahead (1.0 s = 20 ticks): roots burst out along three lines
    a = m.anim("rootline", 2.7)
    a.rot("whip_1", (0, (0, 0, 0)), (0.8, (-150, 0, -10)), (1.0, (-156, 0, -10)), (1.06, (-60, 0, 0), "linear"),
          (2.0, (-56, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("whip_2", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (1.06, (20, 0, 0), "linear"), (2.0, (24, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("whip_3", (0, (0, 0, 0)), (1.0, (30, 0, 0)), (1.06, (30, 0, 0), "linear"), (2.0, (30, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, -10, 0)), (1.06, (24, 6, 0), "linear"), (2.0, (22, 6, 0)), (2.7, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.06, (0, -3, 0), "linear"), (2.0, (0, -3, 0)), (2.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (10, 0, 30)), (2.0, (10, 0, 30)), (2.7, (0, 0, 0)))
    for k in range(8):
        a.rot(f"root_{k}", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (-14, 0, 0), "linear"), (2.0, (-10, 0, 0)), (2.7, (0, 0, 0)))

    # rootring: the macuahuitl lifted high in both hands (1.1 s = 22 ticks), driven into the floor: rings of roots
    # erupt round her one after another
    a = m.anim("rootring", 3.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-170, 0, -10)), (1.1, (-176, 0, -12)), (1.16, (-40, 0, -6), "linear"),
          (2.6, (-40, 0, -6)), (3.3, (0, 0, 0)))
    a.rot("maca", (0, (0, 0, 0)), (1.1, (40, 0, 0)), (1.16, (-40, 0, 0), "linear"), (2.6, (-40, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (1.1, (-160, 0, 20)), (1.16, (-40, 0, 10), "linear"), (2.6, (-40, 0, 10)),
          (3.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-22, 0, 0)), (1.16, (28, 0, 0), "linear"), (2.6, (24, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.16, (10, 0, 0), "linear"), (3.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 2, 0)), (1.16, (0, -5, 0), "linear"), (2.6, (0, -5, 0)), (3.3, (0, 0, 0)))
    for k in range(8):
        a.rot(f"root_{k}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-18, 0, 0), "linear"), (1.6, (-6, 0, 0)),
              (2.0, (-16, 0, 0)), (2.6, (-8, 0, 0)), (3.3, (0, 0, 0)))

    # pollen: she bows her head and shakes the orchid crown (0.9 s = 18 ticks), then flings the pollen out
    a = m.anim("pollen", 2.1)
    a.rot("head", (0, (0, 0, 0)), (0.2, (20, 14, 8)), (0.4, (20, -14, -8)), (0.6, (22, 14, 8)), (0.8, (20, -10, -6)),
          (0.9, (24, 0, 0)), (0.96, (-24, 0, 0), "linear"), (1.4, (-20, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (16, 0, 0)), (0.96, (-12, 0, 0), "linear"), (1.4, (-10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-30, 0, 40)), (0.96, (-60, 0, 70), "linear"), (1.4, (-60, 0, 70)), (2.1, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.9, (-30, 0, -40)), (0.96, (-60, 0, -70), "linear"), (1.4, (-60, 0, -70)),
          (2.1, (0, 0, 0)))
    for i in range(5):
        a.rot(f"orchid_{i}", (0, (0, 0, 0)), (0.3, (20, 0, 14)), (0.6, (-20, 0, -14)), (0.9, (20, 0, 10)),
              (0.96, (-40, 0, 0), "linear"), (1.4, (-10, 0, 0)), (2.1, (0, 0, 0)))
    a.scale("crown", (0, (1, 1, 1)), (0.9, (1.1, 1.1, 1.1)), (0.96, (1.3, 1.3, 1.3), "linear"), (1.4, (1.1, 1.1, 1.1)),
            (2.1, (1, 1, 1)))

    # swing: the whip flung up and forward to catch a hold (0.8 s = 16 ticks), she hauls herself along it
    a = m.anim("swing", 2.1)
    a.rot("whip_1", (0, (0, 0, 0)), (0.7, (-170, 0, -6)), (0.8, (-176, 0, -6)), (0.86, (-110, 0, 0), "linear"),
          (1.4, (-100, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("whip_4", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (0.9, (-30, 0, 0), "linear"), (1.4, (-40, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("whip_5", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (0.9, (-46, 0, 0), "linear"), (1.4, (-46, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-10, -20, 0)), (0.86, (26, 0, 0), "linear"), (1.4, (26, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (30, 0, 30)), (0.86, (-70, 0, 20), "linear"), (1.4, (-70, 0, 20)),
          (2.1, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.86, (0, 0, 0)), (1.0, (26, 0, 0)), (1.4, (22, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("hair", (0, (0, 0, 0)), (0.86, (10, 0, 0)), (1.0, (40, 0, 0)), (1.4, (36, 0, 0)), (2.1, (0, 0, 0)))

    # thorns: she draws in (0.6 s = 12 ticks), then thorns burst from the skirt all round her
    a = m.anim("thorns", 1.35)
    a.scale("skirt", (0, (1, 1, 1)), (0.6, (0.85, 1.0, 0.85)), (0.64, (1.3, 0.95, 1.3), "linear"), (0.9, (1.2, 1.0, 1.2)),
            (1.35, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (0.64, (-14, 0, 0), "linear"), (1.0, (-10, 0, 0)), (1.35, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, -20)), (0.64, (-30, 0, 60), "linear"), (1.0, (-26, 0, 56)),
          (1.35, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.6, (-20, 0, 20)), (0.64, (-30, 0, -60), "linear"), (1.0, (-26, 0, -56)),
          (1.35, (0, 0, 0)))
    for k in range(8):
        a.rot(f"root_{k}", (0, (0, 0, 0)), (0.6, (6, 0, 0)), (0.64, (-20, 0, 0), "linear"), (1.0, (-12, 0, 0)),
              (1.35, (0, 0, 0)))

    # whipstorm (phase 2): the whip whirled overhead (0.9 s = 18 ticks), then swept round her twice at knee height
    a = m.anim("whipstorm", 2.4)
    a.rot("whip_1", (0, (0, 0, 0)), (0.3, (-170, 0, 0)), (0.9, (-176, 0, 0)), (0.95, (-90, 0, -80), "linear"),
          (1.7, (-90, 0, -80)), (2.4, (0, 0, 0)))
    a.rot("whip_3", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (0.95, (-10, 0, 0), "linear"), (1.7, (-10, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("whip_4", (0, (0, 0, 0)), (0.9, (30, 0, 0)), (0.95, (-30, 0, 0), "linear"), (1.7, (-30, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (-6, 120, 0)), (0.6, (-6, 240, 0)), (0.9, (-6, 360, 0)),
          (0.95, (6, 360, 0), "linear"), (1.3, (6, 540, 0), "linear"), (1.7, (6, 720, 0), "linear"), (2.4, (0, 720, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.9, (0, 40, 0)), (1.3, (0, 120, 0)), (1.7, (0, 240, 0)), (2.4, (0, 360, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 50)), (1.7, (-20, 0, 50)), (2.4, (0, 0, 0)))
    a.rot("hair", (0, (0, 0, 0)), (0.9, (30, 0, 20)), (1.7, (40, 0, 20)), (2.4, (0, 0, 0)))

    # snare (phase 2): the whip cast low ahead (0.9 s = 18 ticks); whoever it catches is hauled in, and at 1.5 s the
    # macuahuitl comes down on them
    a = m.anim("snare", 2.4)
    a.rot("whip_1", (0, (0, 0, 0)), (0.8, (-40, 0, -60)), (0.9, (-44, 0, -64)), (0.95, (-88, 0, 0), "linear"),
          (1.2, (-40, 0, -20)), (1.6, (-20, 0, -20)), (2.4, (0, 0, 0)))
    a.rot("whip_4", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (0.95, (-20, 0, 0), "linear"), (1.2, (40, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 20)), (1.3, (-170, 0, 10)), (1.5, (-174, 0, 10)),
          (1.56, (-50, 0, 6), "linear"), (1.9, (-50, 0, 6)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (6, -20, 0)), (1.2, (-6, 10, 0)), (1.5, (-16, 0, 0)), (1.56, (24, 0, 0), "linear"),
          (1.9, (20, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, 1, 0)), (1.56, (0, -4, 0), "linear"), (1.9, (0, -4, 0)), (2.4, (0, 0, 0)))

    # canopy (phase 2): she crouches into her roots (1.0 s = 20 ticks), springs up into the sun-disc and clings there,
    # whip coiled round a spoke, macuahuitl ready, looking down on the summit, for nine seconds
    a = m.anim("canopy", 10.2)
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -8, 0)), (1.0, (0, -9, 0)), (1.1, (0, 4, 0), "linear"), (1.4, (0, 0, 0)),
          (10.0, (0, 0, 0)), (10.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (30, 0, 0)), (1.1, (-20, 0, 0), "linear"), (1.5, (34, 0, 0)), (10.0, (34, 0, 0)),
          (10.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.5, (30, 0, 0)), (5.0, (30, 20, 0)), (8.0, (30, -20, 0)),
          (10.0, (30, 0, 0)), (10.2, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (1.0, (20, 0, -20)), (1.1, (-176, 0, 0), "linear"), (1.5, (-170, 0, -10)),
          (10.0, (-170, 0, -10)), (10.2, (0, 0, 0)))
    a.rot("whip_2", (0, (0, 0, 0)), (1.5, (-40, 0, 0)), (10.0, (-40, 0, 0)), (10.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (30, 0, 20)), (1.5, (-60, 0, 40)), (10.0, (-60, 0, 40)), (10.2, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (-30, 0, 0)), (10.0, (-30, 0, 0)), (10.2, (0, 0, 0)))
    a.scale("skirt", (0, (1, 1, 1)), (1.0, (1.1, 0.8, 1.1)), (1.4, (0.8, 0.7, 0.8)), (10.0, (0.8, 0.7, 0.8)),
            (10.2, (1, 1, 1)))
    for k in range(8):
        a.scale(f"root_{k}", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.1, (0.2, 0.2, 0.2), "linear"), (10.0, (0.2, 0.2, 0.2)),
                (10.2, (1, 1, 1)))

    # plunge (phase 2): crouched on the disc (1.2 s = 24 ticks) she dives onto the marked spot, macuahuitl first
    a = m.anim("plunge", 2.5)
    a.rot("chest", (0, (0, 0, 0)), (1.2, (36, 0, 0)), (1.26, (40, 0, 0), "linear"), (1.8, (30, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-170, 0, 10)), (1.2, (-176, 0, 10)), (1.26, (-40, 0, 6), "linear"),
          (1.8, (-40, 0, 6)), (2.5, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (1.2, (-120, 0, -40)), (1.26, (-30, 0, -50), "linear"), (1.8, (-30, 0, -50)),
          (2.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.2, (0, 2, 0)), (1.26, (0, -7, 0), "linear"), (1.8, (0, -6, 0)), (2.5, (0, 0, 0)))
    for k in range(8):
        a.rot(f"root_{k}", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.3, (-20, 0, 0), "linear"), (2.5, (0, 0, 0)))

    # overgrowth (phase 3, invulnerable): she sinks into her roots, arms raised, the crown blooming (1.5 s = 30 ticks),
    # then the whole summit erupts in roots
    a = m.anim("overgrowth", 3.5)
    a.pos("hips", (0, (0, 0, 0)), (0.5, (0, -10, 0)), (1.5, (0, -10, 0)), (1.56, (0, 3, 0), "linear"), (2.8, (0, 2, 0)),
          (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-150, 0, 40)), (1.5, (-160, 0, 50)), (1.56, (-120, 0, 80), "linear"),
          (2.8, (-120, 0, 80)), (3.5, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.6, (-150, 0, -40)), (1.5, (-160, 0, -50)), (1.56, (-120, 0, -80), "linear"),
          (2.8, (-120, 0, -80)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-30, 0, 0)), (1.56, (-40, 0, 0), "linear"), (2.8, (-36, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-14, 0, 0)), (1.56, (-20, 0, 0), "linear"), (2.8, (-18, 0, 0)), (3.5, (0, 0, 0)))
    a.scale("crown", (0, (1, 1, 1)), (1.5, (1.3, 1.3, 1.3)), (1.56, (1.5, 1.5, 1.5), "linear"), (2.8, (1.4, 1.4, 1.4)),
            (3.5, (1, 1, 1)))
    for k in range(8):
        a.scale(f"root_{k}", (0, (1, 1, 1)), (1.5, (1.0, 1.0, 1.0)), (1.56, (1.6, 1.8, 1.6), "linear"),
                (2.8, (1.5, 1.6, 1.5)), (3.5, (1, 1, 1)))

    # cages (phase 3): both hands raised, fingers spread, the roots coiling (1.2 s = 24 ticks), then her fists clench
    a = m.anim("cages", 2.7)
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-120, 0, 60)), (1.2, (-126, 0, 64)), (1.26, (-80, 0, 20), "linear"),
          (2.0, (-80, 0, 20)), (2.7, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (1.0, (-120, 0, -60)), (1.2, (-126, 0, -64)), (1.26, (-80, 0, -20), "linear"),
          (2.0, (-80, 0, -20)), (2.7, (0, 0, 0)))
    a.rot("whip_3", (0, (0, 0, 0)), (1.2, (-40, 0, 0)), (1.26, (60, 0, 0), "linear"), (2.0, (60, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-16, 0, 0)), (1.26, (14, 0, 0), "linear"), (2.0, (12, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-24, 0, 0)), (1.26, (16, 0, 0), "linear"), (2.0, (14, 0, 0)), (2.7, (0, 0, 0)))

    # harvest (phase 3): she crouches toward a cage (1.0 s = 20 ticks), leaps onto it and crushes it
    a = m.anim("harvest", 2.3)
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -6, 0)), (1.0, (0, -7, 0)), (1.06, (0, -4, 0), "linear"), (1.6, (0, -4, 0)),
          (2.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-170, 0, 10)), (1.0, (-176, 0, 10)), (1.06, (-30, 0, 6), "linear"),
          (1.6, (-30, 0, 6)), (2.3, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (1.0, (-150, 0, -20)), (1.06, (-20, 0, -10), "linear"), (1.6, (-20, 0, -10)),
          (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.06, (34, 0, 0), "linear"), (1.6, (30, 0, 0)), (2.3, (0, 0, 0)))

    # roar (phase two): arms flung wide, head thrown back, the crown blooming, the roots lifting round her
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 70)), (1.6, (-44, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.5, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("crown", (0, (1, 1, 1)), (0.5, (1.3, 1.3, 1.3)), (1.6, (1.25, 1.25, 1.25)), (2.0, (1, 1, 1)))
    for k in range(8):
        a.rot(f"root_{k}", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: she sags into her skirt of roots, head bowed, the whip limp on the floor
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -12, 0)), (1.6, (0, -12, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (34, 0, 10)), (1.6, (36, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -12)), (1.6, (30, 0, -12)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (10, 0, 20)), (1.6, (12, 0, 20)), (2.0, (0, 0, 0)))
    a.rot("whip_1", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (1.6, (20, 0, -10)), (2.0, (0, 0, 0)))


# ---------------------------------------------------------------- the jaguar spirits
SPIRIT = (96, 214, 150)
SPIRIT_L = (196, 255, 214)
SPIRIT_D = (40, 130, 90)


def spirit(seed=0, spots=True):
    """See-through jade light with darker rosettes (the jaguar's spots), paler belly."""
    def f(face, x, y, w, h):
        c = SPIRIT
        if face == "bottom":
            c = SPIRIT_L
        elif spots and face != "bottom":
            r = B.n(x // 2, y // 2, seed)
            if r < 0.16 and (x + y) % 2 == 0:
                c = SPIRIT_D                                            # a rosette
            elif r > 0.9:
                c = SPIRIT_L
        if face == "top":
            c = mix(c, SPIRIT_L, 0.2)
        return (*c[:3], 176)
    return f


def spirit_glow(seed=0):
    def f(face, x, y, w, h):
        if face != "bottom" and B.n(x // 2, y // 2, seed) < 0.16 and (x + y) % 2 == 0:
            return SPIRIT_L
        return None
    return f


def spirit_face(f, x, y, w, h):
    if f == "front" and y == 2 and x in (1, w - 2):
        return (*EYE_L, 255)
    if f == "front" and y == h - 1 and 2 <= x <= w - 3:
        return (*SPIRIT_D, 200)
    return spirit(7)(f, x, y, w, h)


def spirit_face_glow(f, x, y, w, h):
    if f == "front" and y == 2 and x in (1, w - 2):
        return EYE_L
    return None


def build_spirit():
    m = Model("jaguar_spirit", seed=421, shadow=0.6, walk_speed=1.4, walk_scale=1.0, render="entityTranslucent",
              glow_pulse=0.15)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -11, 0))
    m.part("head", "body", pivot=(0, -2, -9))
    m.part("jaw", "head", pivot=(0, 1, -3))
    m.part("tail", "body", pivot=(0, -3, 9), rot=(-30, 0, 0))
    m.part("tail_2", "tail", pivot=(0, 0, 8), rot=(30, 0, 0))
    for name, x, z in (("leg_fr", -2.5, -6), ("leg_fl", 2.5, -6), ("leg_br", -2.5, 7), ("leg_bl", 2.5, 7)):
        m.part(name, "body", pivot=(x, 2, z))

    m.box("body", -3.5, -4, -9, 7, 7, 18, spirit(1), glow=spirit_glow(1))
    m.box("body", -3, -4.5, -6, 6, 1, 8, spirit(2, spots=False))                    # the ridge of the back
    m.box("head", -3.5, -3, -6, 7, 6, 6, spirit_face, glow=spirit_face_glow)
    m.box("head", -2, -1, -8, 4, 3, 2, spirit(3))                                    # the muzzle
    m.box("head", -3.5, -5, -3, 2, 2, 1, spirit(4, spots=False))                     # ears
    m.box("head", 1.5, -5, -3, 2, 2, 1, spirit(5, spots=False))
    m.box("jaw", -2, 0, -5, 4, 1, 4, spirit(6, spots=False))
    m.box("jaw", -1.5, -1, -5.2, 1, 1, 1, (*THORN, 230))                             # fangs
    m.box("jaw", 0.5, -1, -5.2, 1, 1, 1, (*THORN, 230))
    for name in ("leg_fr", "leg_fl", "leg_br", "leg_bl"):
        m.box(name, -1.5, 0, -1.5, 3, 9, 3, spirit(8 + len(name)), glow=spirit_glow(8))
        m.box(name, -1.5, 8, -2.5, 3, 1, 4, spirit(9, spots=False))                 # paws
    m.box("tail", -1, -1, 0, 2, 2, 9, spirit(10), glow=spirit_glow(10))
    m.box("tail_2", -1, -1, 0, 2, 2, 8, spirit(11), glow=spirit_glow(11))

    idle = m.anim("idle", 2.0)
    idle.rot("tail", (0, (0, 0, 0)), (1.0, (6, 20, 0)), (2.0, (0, 0, 0)))
    idle.rot("tail_2", (0, (0, 0, 0)), (1.0, (10, 24, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (4, 8, 0)), (2.0, (0, 0, 0)))
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, 0.4, 0)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 0.8)
    walk.rot("leg_fr", (0, (30, 0, 0)), (0.4, (-30, 0, 0)), (0.8, (30, 0, 0)))
    walk.rot("leg_bl", (0, (30, 0, 0)), (0.4, (-30, 0, 0)), (0.8, (30, 0, 0)))
    walk.rot("leg_fl", (0, (-30, 0, 0)), (0.4, (30, 0, 0)), (0.8, (-30, 0, 0)))
    walk.rot("leg_br", (0, (-30, 0, 0)), (0.4, (30, 0, 0)), (0.8, (-30, 0, 0)))
    walk.rot("body", (0, (2, 0, 0)), (0.4, (-2, 0, 0)), (0.8, (2, 0, 0)))
    walk.rot("tail", (0, (10, 0, 0)), (0.4, (-4, 0, 0)), (0.8, (10, 0, 0)))

    # pounce: crouched, haunches wiggling (0.5 s = 10 ticks), then the leap, claws out
    a = m.anim("pounce", 1.2)
    a.pos("body", (0, (0, 0, 0)), (0.45, (0, -3, 1)), (0.5, (0, -3, 1)), (0.55, (0, 2, -1), "linear"), (0.8, (0, 1, 0)),
          (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (8, 0, 0)), (0.55, (-14, 0, 0), "linear"), (0.8, (6, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_fr", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.55, (-80, 0, 0), "linear"), (0.8, (-40, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_fl", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.55, (-80, 0, 0), "linear"), (0.8, (-40, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_br", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.55, (50, 0, 0), "linear"), (0.8, (20, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_bl", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.55, (50, 0, 0), "linear"), (0.8, (20, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (0.8, (30, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.2, (0, 20, 0)), (0.35, (0, -20, 0)), (0.5, (0, 20, 0)), (0.6, (20, 0, 0)),
          (1.2, (0, 0, 0)))

    # claw: a paw raised (0.4 s = 8 ticks), raked down
    a = m.anim("claw", 0.9)
    a.rot("leg_fr", (0, (0, 0, 0)), (0.35, (-110, 0, -10)), (0.4, (-114, 0, -10)), (0.45, (-10, 0, 0), "linear"),
          (0.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (-10, 10, 0)), (0.45, (8, -6, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-10, 0, 0)), (0.45, (10, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (34, 0, 0)), (0.9, (0, 0, 0)))
    return m
