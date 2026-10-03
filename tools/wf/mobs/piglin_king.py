"""The Golden Piglin King (Le Roi piglin doré): a massive piglin brute king, about 4.2 blocks tall and
3 wide.

Silhouette idea: a huge round belly bound in gold chains under a gilded breastplate, a hunched boar
head thrust forward with curling ivory tusks and a tall spiked crown, a dark fur mantle and a short
crimson cape, and a giant golden flanged mace with a crescent axe blade carried on the right shoulder.
"""
from ..models import FACE_ID, Model
from ..texgen import mix, mul
from .ash_lord import hsh

SKIN = (222, 146, 138)
SKIN_D = (170, 96, 96)
SKIN_L = (246, 186, 172)
SNOUT = (238, 166, 156)
NOSTRIL = (86, 34, 38)
GOLD = (236, 186, 54)
GOLD_HI = (255, 238, 150)
GOLD_D = (176, 116, 26)
GOLD_DD = (112, 66, 18)
CRIMSON = (150, 22, 34)
CRIMSON_D = (92, 12, 22)
CRIMSON_L = (196, 52, 56)
FUR = (72, 46, 34)
FUR_D = (44, 28, 22)
IVORY = (238, 228, 198)
IVORY_D = (186, 168, 132)
LEATHER = (90, 56, 36)
LEATHER_D = (58, 36, 24)
RUBY = (230, 36, 64)
EYE = (255, 206, 72)


def gold(seed, emboss=None, rim=True, worn=0.0):
    """Polished gold lit from above: bright top edge, warm shadow below, darker rim, a soft sheen band,
    and an optional embossed pattern ('border', 'studs', 'scales', 'bands')."""
    def paint(face, x, y, w, h):
        k = 1 + (hsh(seed, x // 2, y // 2, FACE_ID[face]) - 0.5) * 0.10
        c = mul(GOLD, k)
        side = face not in ("top", "bottom")
        if face == "top":
            c = mix(c, GOLD_HI, 0.2)
            if x in (0, w - 1) or y in (0, h - 1):
                c = mix(c, GOLD_D, 0.45)
            elif (x + y) % 7 == 0 and w > 4:
                c = mix(c, GOLD_HI, 0.5)
        elif face == "bottom":
            c = mix(c, GOLD_DD, 0.5)
        if side and h > 2:
            t = y / max(1, h - 1)
            c = mix(c, GOLD_HI, 0.5) if y == 0 else mix(c, GOLD_D, max(0.0, t - 0.45))
            if abs(t - 0.28) < 0.09:
                c = mix(c, GOLD_HI, 0.25)  # sheen band
            if y == h - 1:
                c = mix(c, GOLD_DD, 0.6)
        if rim and side and w > 3 and (x == 0 or x == w - 1):
            c = mix(c, GOLD_D, 0.55)
        if emboss == "border" and side and w > 6 and h > 5:
            # an embossed ridge one texel in from the edge: lit on its top/left, shadowed bottom/right
            inside = 1 <= x <= w - 2 and 1 <= y <= h - 2
            if inside and (x == 1 or y == 1):
                c = GOLD_HI
            elif inside and (x == w - 2 or y == h - 2):
                c = GOLD_D
            elif inside and (x == 2 or y == 2) and x < w - 2 and y < h - 2:
                c = mix(c, GOLD_D, 0.35)
        elif emboss == "studs" and side and x % 3 == 1 and y % 3 == 1:
            c = GOLD_HI
        elif emboss == "studs" and side and x % 3 == 1 and y % 3 == 2:
            c = GOLD_DD
        elif emboss == "scales" and side:
            row = y // 2
            if (x + (row % 2) * 2) % 4 == 0 or y % 2 == 1 and (x + (row % 2) * 2) % 4 in (1, 3):
                c = mix(c, GOLD_D, 0.6)
        elif emboss == "bands" and side and y % 4 == 3:
            c = mix(c, GOLD_DD, 0.5)
        if worn and hsh(seed, x, y, 9) < worn:
            c = mix(c, GOLD_DD, 0.5)
        return c
    return paint


def skin(seed, base=SKIN, bristle=True, scars=(), lit_top=True, grad=True):
    """Piglin hide: warm pink, darker toward the bottom, coarse dark bristles and pale scars."""
    def paint(face, x, y, w, h):
        k = 1 + (hsh(seed, x // 2, y // 2, FACE_ID[face]) - 0.5) * 0.09
        c = mul(base, k)
        if face == "top" and lit_top:
            c = mix(c, SKIN_L, 0.25)
        elif face == "bottom":
            c = mix(c, SKIN_D, 0.6)
        elif h > 3 and grad:
            c = mix(c, SKIN_D, max(0.0, y / h - 0.55))
        if bristle and hsh(seed, x, y, FACE_ID[face]) < 0.03:
            c = mix(c, (112, 64, 60), 0.7)
        for (sf, sx, sy, ln) in scars:
            if face == sf and sx <= x < sx + ln and y == sy + (x - sx) // 2:
                return SKIN_L
        return c
    return paint


def cloth(seed, base=CRIMSON, trim=True, ragged=0):
    """Royal crimson cloth: soft folds, a gold-embroidered hem."""
    def paint(face, x, y, w, h):
        if ragged and face in ("front", "back") and y > h - 1 - int(hsh(seed, x // 2) * ragged):
            return None
        phase = (x + 2 * hsh(seed, x // 3)) / 3.0
        fold = abs(((phase % 2.0) - 1.0))
        c = mix(CRIMSON_D, CRIMSON_L, fold * 0.75)
        if base != CRIMSON:
            c = mix(c, base, 0.6)
        if trim and face in ("front", "back", "left", "right"):
            if y >= h - 2:
                return GOLD if y == h - 2 else GOLD_D
            if (x == 0 or x == w - 1) and w > 4:
                return GOLD_D
        return c
    return paint


def fur(seed):
    def paint(face, x, y, w, h):
        r = hsh(seed, x, y, FACE_ID[face])
        c = FUR if r > 0.3 else FUR_D if r < 0.15 else mix(FUR, (110, 78, 56), 0.5)
        if face not in ("top", "bottom") and y == h - 1 and hsh(seed, x) < 0.5:
            return None  # shaggy lower edge
        if face == "top":
            c = mix(c, (120, 86, 60), 0.2)
        return c
    return paint


def solid(c, glow=None):
    return c, glow


def build():
    m = Model("piglin_king", seed=2, shadow=1.6, walk_speed=0.8, walk_scale=1.0)

    def box(part, x, y, z, w, h, d, mat, grow=0.0):
        paint, glow = mat if isinstance(mat, tuple) and len(mat) == 2 and not isinstance(mat[0], int) else (mat, None)
        m.box(part, x, y, z, w, h, d, paint, glow=glow, grow=grow)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -17, 0))
    m.part("loin", "hips", pivot=(0, 3, -9), rot=(-4, 0, 0))
    m.part("torso", "hips", pivot=(0, -4, 0), rot=(6, 0, 0))
    m.part("belly", "torso", pivot=(0, -7, -2))
    m.part("head", "torso", pivot=(0, -25, -7), rot=(4, 0, 0))
    m.part("jaw", "head", pivot=(0, -1, -3))
    m.part("ear_r", "head", pivot=(-8, -10, -1), rot=(0, 0, 55))
    m.part("ear_l", "head", pivot=(8, -10, -1), rot=(0, 0, -55))
    m.part("cape", "torso", pivot=(0, -26, 9), rot=(10, 0, 0))
    m.part("arm_r", "torso", pivot=(-17, -21, 0), rot=(0, 0, 8))
    m.part("forearm_r", "arm_r", pivot=(0, 12, 0), rot=(-100, 0, 0))
    m.part("mace", "forearm_r", pivot=(0, 13, 0), rot=(55, 0, -15))
    m.part("arm_l", "torso", pivot=(17, -21, 0), rot=(0, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(0, 12, 0), rot=(-15, 0, 0))
    m.part("leg_r", "bone", pivot=(-7, -17, 0), rot=(0, 0, 4))
    m.part("shin_r", "leg_r", pivot=(0, 9, 0), rot=(0, 0, -4))
    m.part("leg_l", "bone", pivot=(7, -17, 0), rot=(0, 0, -4))
    m.part("shin_l", "leg_l", pivot=(0, 9, 0), rot=(0, 0, 4))

    # ------------------------------------------------------------------ hips and legs
    box("hips", -12, -4, -9, 24, 7, 17, cloth(1, trim=False))                 # crimson waist wrap
    box("hips", -13, -5, -10, 26, 3, 19, gold(2))            # gold belt

    def buckle(f, x, y, w, h):
        # a boar's snout emblem: an oval with two nostrils
        cx, cy = (w - 1) / 2, (h - 1) / 2
        if ((x - cx) / (w / 2)) ** 2 + ((y - cy) / (h / 2)) ** 2 > 1.0:
            return None
        if y == round(cy) and x in (round(cx) - 1, round(cx) + 1):
            return GOLD_DD
        return gold(3)(f, x, y, w, h)
    box("hips", -4, -7, -11, 8, 6, 1, ({"front": buckle, "*": None}, None))
    box("hips", -1, -5, -12, 2, 2, 1, solid(RUBY, RUBY))
    box("loin", -6, 0, -1, 12, 13, 1, cloth(4))
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        box(leg, -5, 0, -5, 10, 9, 10, cloth(10 + sx, base=(120, 20, 30), trim=False))   # breeches
        box(leg, -6, -1, -6, 12, 4, 12, gold(12 + sx, emboss="bands"))                   # thigh plate
        box(shin, -5, 0, -5, 10, 4, 10, skin(14 + sx))
        box(shin, -6, 3, -7, 12, 5, 13, gold(16 + sx, emboss="border"))                 # gold sabatons
        box(shin, -5, 7, -8, 10, 1, 3, solid(GOLD_DD))                                    # toe rim

    # ------------------------------------------------------------------ torso: belly, breastplate, mantle
    box("belly", -13, -8, -9, 26, 15, 19, skin(20, scars=(("front", 3, 3, 6),)))
    box("belly", -12, -6, -12, 24, 12, 3, skin(21, base=SKIN_L, lit_top=False, grad=False))
    box("belly", -9, -4, -15, 18, 9, 3, ({"front": lambda f, x, y, w, h: NOSTRIL if (x, y) in ((8, 5), (9, 5)) else
                                          skin(22, base=SKIN_L, grad=False)(f, x, y, w, h), "*": skin(22, base=SKIN_L, lit_top=False, grad=False)}, None))
    # one heavy gold chain swagged across the belly, links alternating face-on and edge-on
    swag = ((-13, -5, -10), (-11, -3, -13), (-9, -1, -15), (-6, 1, -16), (-3, 2, -16), (0, 2, -16), (3, 1, -16),
            (6, -1, -16), (9, -3, -13), (11, -5, -10))
    for i, (x, y, z) in enumerate(swag):
        if i % 2 == 0:
            box("belly", x, y, z, 3, 2, 1, ({"*": lambda f, xx, yy, w, h: GOLD_HI if yy == 0 else GOLD_D}, None))
        else:
            box("belly", x, y, z, 3, 1, 1, solid(GOLD_D))
    box("belly", -2, 3, -17, 4, 4, 1, ({"*": lambda f, x, y, w, h: RUBY if 0 < x < 3 and 0 < y < 3 else GOLD_HI}, 
                                         {"*": lambda f, x, y, w, h: RUBY if 0 < x < 3 and 0 < y < 3 else None}))
    box("torso", -15, -27, -9, 30, 11, 17, ({"front": gold(30, emboss="border"), "*": gold(30)}, None))
    box("torso", -9, -26, -10, 18, 7, 1, gold(31, emboss="scales"))              # scaled gorget plate
    box("torso", -2, -22, -11, 4, 4, 1, solid(RUBY, RUBY))                         # breast jewel
    # crimson sash from the left shoulder to the right hip
    for i in range(6):
        box("torso", 10 - i * 3, -27 + i * 2, -10, 4, 3, 1, cloth(32 + i, trim=False))
    box("torso", -16, -30, -7, 32, 5, 16, fur(33))                                 # fur mantle

    # ------------------------------------------------------------------ head: boar king
    def face(f, x, y, w, h):
        base = skin(40)(f, x, y, w, h)
        if y in (5, 6) and x in (1, 2, 3, w - 4, w - 3, w - 2):
            return (40, 20, 14) if y == 6 or x in (1, w - 2) else EYE
        if y == 3 and 1 <= x <= w - 2:
            return mix(base, SKIN_D, 0.6)     # heavy brow shadow
        return base
    box("head", -8, -12, -7, 16, 12, 13, ({"front": face, "*": skin(41)},
                                         {"front": lambda f, x, y, w, h: EYE if y == 5 and x in (2, 3, w - 4, w - 3) else None}))
    box("head", -8, -9, -8, 16, 2, 1, skin(42, base=SKIN_D))                       # brow ridge

    def snout_front(f, x, y, w, h):
        if y in (2, 3) and x in (1, 2, w - 3, w - 2):
            return NOSTRIL
        if y == 0:
            return SKIN_L
        return skin(43, base=SNOUT, bristle=False)(f, x, y, w, h)
    box("head", -4, -7, -12, 8, 7, 5, ({"front": snout_front, "*": skin(43, base=SNOUT, bristle=False)}, None))
    box("head", -2, 0, -12, 4, 2, 1, solid(GOLD_HI))                               # nose ring
    box("jaw", -7, 0, -9, 14, 4, 11, skin(44, base=SKIN_D))
    box("jaw", -6, 0, -10, 12, 1, 1, solid(IVORY_D))                                # lower teeth
    for sx in (-1, 1):
        x = -8 if sx < 0 else 6
        box("jaw", x, -6, -10, 2, 7, 2, ({"*": lambda f, xx, yy, w, h: IVORY if yy < h - 2 else IVORY_D}, None))
        box("jaw", x + sx * 2, -9, -10, 2, 3, 2, solid(IVORY))                     # tusk tips curling out
    for ear, sx in (("ear_r", -1), ("ear_l", 1)):
        box(ear, -1, 0, -4, 2, 10, 7, skin(45 + sx, base=SKIN))
        box(ear, -1 + sx, 6, -1, 1, 3, 3, solid(GOLD_HI))                          # gold earrings
    # crown: a heavy gold band with eight points, rubies on the band and the tallest point
    box("head", -8, -15, -8, 16, 3, 15, ({"top": None, "bottom": None, "side": gold(50, emboss="bands")}, None))
    for i, (x, z, hgt, wx, wz) in enumerate(((-1, -9, 9, 2, 2), (-6, -9, 6, 2, 1), (4, -9, 6, 2, 1),
                                              (-8, -4, 6, 1, 2), (7, -4, 6, 1, 2), (-8, 2, 5, 1, 2),
                                              (7, 2, 5, 1, 2), (-1, 6, 6, 2, 1))):
        box("head", x, -15 - hgt, z, wx, hgt, wz, gold(51 + i))
    box("head", -1, -26, -10, 2, 2, 2, solid(RUBY, RUBY))
    for x in (-5, -1, 3):
        box("head", x, -14, -9, 2, 1, 1, solid(RUBY, RUBY))

    # ------------------------------------------------------------------ cape
    box("cape", -14, 0, 0, 28, 24, 1, ({"back": cloth(60), "front": cloth(61), "*": cloth(62)}, None))

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        box(arm, -7, -6, -8, 14, 9, 16, gold(70 + sx, emboss="border"))         # gold pauldron
        box(arm, -6 if sx < 0 else -7, -8, -6, 13, 2, 12, gold(72 + sx))          # pauldron crest
        box(arm, -5, 0, -5, 10, 12, 10, skin(74 + sx, scars=(("front", 2, 4, 5),) if sx > 0 else ()))
        box(arm, -6, 5, -6, 12, 2, 12, gold(76 + sx))                             # arm ring
        box(fore, -6, 0, -6, 12, 9, 12, gold(78 + sx, emboss="border"))          # bracer
        box(fore, -5, 9, -5, 10, 6, 10, ({"*": skin(80 + sx), "front": lambda f, x, y, w, h: GOLD_HI if y == 2 and x % 3 == 1
                                        else skin(80 + sx)(f, x, y, w, h)}, None))  # fist with rings

    # ------------------------------------------------------------------ the golden mace-axe (haft along -y)
    box("mace", -1, -30, -1, 3, 36, 3, ({"*": lambda f, x, y, w, h: LEATHER if (y // 2) % 2 else LEATHER_D}, None))
    box("mace", -2, 6, -2, 5, 3, 5, gold(90))                                      # pommel
    box("mace", -2, -31, -2, 5, 2, 5, gold(91))                                    # collar
    box("mace", -5, -43, -5, 11, 12, 11, gold(92, emboss="border"))                # the head
    box("mace", -1, -41, -8, 3, 8, 3, gold(93))                                    # flanges
    box("mace", -1, -41, 6, 3, 8, 3, gold(94))
    box("mace", -8, -41, -1, 3, 8, 3, gold(95))
    box("mace", -1, -48, -1, 3, 5, 3, gold(96))                                    # top spike
    box("mace", 0, -50, 0, 1, 2, 1, solid(GOLD_HI))

    def axe(f, x, y, w, h):
        if f in ("left", "right"):
            if x == w - 1 or x == w - 2 and 0 < y < h - 1:
                return (255, 248, 210)  # honed edge
            return gold(97)(f, x, y, w, h)
        return gold(97)(f, x, y, w, h)
    box("mace", 6, -45, -1, 4, 16, 3, (axe, None))
    box("mace", 10, -47, -1, 3, 20, 3, (axe, None))
    box("mace", -1, -40, -1, 3, 3, 1, solid(RUBY, RUBY), grow=0.0)

    _anims(m)
    return m


def _anims(m):
    Z = (0, 0, 0)
    idle = m.anim("idle", 3.0)
    idle.scale("belly", (0, (1, 1, 1)), (1.5, (1.04, 1.02, 1.05)), (3.0, (1, 1, 1)))
    idle.rot("torso", (0, Z), (1.5, (-2, 0, 0)), (3.0, Z))
    idle.rot("head", (0, Z), (1.0, (3, 6, 0)), (2.0, (2, -6, 0)), (3.0, Z))
    idle.rot("jaw", (0, Z), (1.5, (6, 0, 0)), (3.0, Z))
    idle.rot("ear_r", (0, Z), (0.7, (0, 0, -8)), (1.5, (0, 0, 4)), (3.0, Z))
    idle.rot("ear_l", (0, Z), (0.9, (0, 0, 8)), (1.8, (0, 0, -4)), (3.0, Z))
    idle.rot("cape", (0, Z), (1.5, (4, 0, 0)), (3.0, Z))
    idle.rot("arm_l", (0, Z), (1.5, (-3, 0, -3)), (3.0, Z))

    walk = m.anim("walk", 1.6)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (24 * sign, 0, 0)), (0.8, (-24 * sign, 0, 0)), (1.6, (24 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, Z), (0.4, (25 if sign > 0 else 0, 0, 0)), (0.8, Z), (1.2, (25 if sign < 0 else 0, 0, 0)), (1.6, Z))
    walk.rot("torso", (0, (0, 0, 5)), (0.8, (0, 0, -5)), (1.6, (0, 0, 5)))   # heavy side-to-side waddle
    walk.rot("head", (0, (0, 0, -4)), (0.8, (0, 0, 4)), (1.6, (0, 0, -4)))
    walk.rot("arm_l", (0, (-20, 0, 0)), (0.8, (20, 0, 0)), (1.6, (-20, 0, 0)))
    walk.scale("belly", (0, (1, 1, 1)), (0.4, (1.03, 0.97, 1.03)), (0.8, (1, 1, 1)), (1.2, (1.03, 0.97, 1.03)), (1.6, (1, 1, 1)))
    walk.pos("bone", (0, Z), (0.4, (0, -1.5, 0)), (0.8, Z), (1.2, (0, -1.5, 0)), (1.6, Z))

    ST = (100, 0, 0)       # forearm offset that straightens the arm (rest is bent -100)
    EXT = (125, 0, 15)     # mace offset that lines the haft up with a straight arm (head beyond the fist)

    def off(v, dx=0.0, dy=0.0, dz=0.0):
        return (v[0] + dx, v[1] + dy, v[2] + dz)
    # smash: the mace lifted high over the crown, head hanging behind, then brought down (impact 0.85 s)
    a = m.anim("smash", 1.8)
    for arm, zr in (("arm_r", 10), ("arm_l", -15)):
        a.rot(arm, (0, Z), (0.75, (-175, 0, zr)), (0.85, (-95, 0, zr * 0.4), "linear"), (1.3, (-90, 0, zr * 0.4)), (1.8, Z))
    a.rot("forearm_r", (0, Z), (0.75, ST), (0.85, ST), (1.3, ST), (1.8, Z))
    a.rot("forearm_l", (0, Z), (0.75, (-20, 0, 0)), (0.85, (-30, 0, 0)), (1.8, Z))
    a.rot("mace", (0, Z), (0.75, off(EXT, -75)), (0.85, EXT, "linear"), (1.3, EXT), (1.8, Z))
    a.rot("torso", (0, Z), (0.75, (-22, 0, 0)), (0.85, (30, 0, 0), "linear"), (1.3, (28, 0, 0)), (1.8, Z))
    a.rot("head", (0, Z), (0.75, (-15, 0, 0)), (0.85, (10, 0, 0)), (1.8, Z))
    a.rot("jaw", (0, Z), (0.75, (25, 0, 0)), (0.9, (5, 0, 0)), (1.8, Z))
    a.pos("bone", (0, Z), (0.75, (0, 1, 2)), (0.85, (0, -4, -5), "linear"), (1.3, (0, -4, -5)), (1.8, Z))
    # swing: the mace swung far out to his right, then a flat sweep across to the left (impact 0.70 s)
    a = m.anim("swing", 1.5)
    a.rot("torso", (0, Z), (0.6, (0, 55, 0)), (0.7, (8, -55, 0), "linear"), (0.95, (6, -60, 0)), (1.5, Z))
    a.rot("arm_r", (0, Z), (0.6, (-25, 35, 80)), (0.7, (-85, -75, 0), "linear"), (0.95, (-80, -80, 0)), (1.5, Z))
    a.rot("forearm_r", (0, Z), (0.6, ST), (0.95, ST), (1.5, Z))
    a.rot("mace", (0, Z), (0.6, EXT), (0.95, EXT), (1.5, Z))
    a.rot("arm_l", (0, Z), (0.6, (-40, 0, -40)), (0.7, (-10, 0, -10)), (1.5, Z))
    a.rot("head", (0, Z), (0.6, (0, -30, 0)), (0.7, (0, 25, 0)), (1.5, Z))
    a.pos("bone", (0, Z), (0.6, (0, -1, 3)), (0.7, (0, 0, -5), "linear"), (1.0, (0, 0, -5)), (1.5, Z))
    # charge: paw the ground, head and belly lowered, then the charge (wind-up 0.75 s, runs to 1.35 s)
    a = m.anim("charge", 2.0)
    a.rot("torso", (0, Z), (0.75, (30, 0, 0)), (1.35, (34, 0, 0)), (1.7, (10, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.75, (-20, 0, 0)), (1.35, (-24, 0, 0)), (2.0, Z))
    a.rot("arm_r", (0, Z), (0.75, (30, 0, 20)), (1.35, (30, 0, 20)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.75, (40, 0, -25)), (1.35, (40, 0, -25)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.25, (30, 0, 0)), (0.45, (-10, 0, 0)), (0.6, (30, 0, 0)), (0.75, (-20, 0, 0)),
          (0.9, (35, 0, 0), "linear"), (1.05, (-35, 0, 0), "linear"), (1.2, (35, 0, 0), "linear"), (1.35, (-35, 0, 0), "linear"),
          (1.7, (0, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (0.75, (15, 0, 0)), (0.9, (-35, 0, 0), "linear"), (1.05, (35, 0, 0), "linear"),
          (1.2, (-35, 0, 0), "linear"), (1.35, (35, 0, 0), "linear"), (1.7, Z), (2.0, Z))
    a.scale("belly", (0, (1, 1, 1)), (0.75, (1.06, 1.0, 1.08)), (1.35, (1.06, 1.0, 1.08)), (2.0, (1, 1, 1)))
    a.pos("bone", (0, Z), (0.75, (0, -2, 2)), (1.35, (0, -2, -2)), (2.0, Z))
    # pound: mace and fist raised, a hop, then both hammer the ground with the belly (impact 1.00 s)
    a = m.anim("pound", 2.0)
    for arm, zr in (("arm_r", 25), ("arm_l", -25)):
        a.rot(arm, (0, Z), (0.8, (-170, 0, zr)), (1.0, (-95, 0, zr * 0.3), "linear"), (1.5, (-90, 0, zr * 0.3)), (2.0, Z))
    a.rot("forearm_r", (0, Z), (0.8, ST), (1.5, ST), (2.0, Z))
    a.rot("forearm_l", (0, Z), (0.8, (-30, 0, 0)), (1.0, (-10, 0, 0)), (2.0, Z))
    a.rot("mace", (0, Z), (0.8, off(EXT, -60)), (1.0, EXT, "linear"), (1.5, EXT), (2.0, Z))
    a.rot("torso", (0, Z), (0.8, (-25, 0, 0)), (1.0, (35, 0, 0), "linear"), (1.5, (32, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.5, (0, -3, 0)), (0.8, (0, 8, 0)), (1.0, (0, -5, -3), "linear"), (1.5, (0, -5, -3)), (2.0, Z))
    a.scale("belly", (0, (1, 1, 1)), (0.95, (1, 1, 1)), (1.05, (1.12, 0.9, 1.1), "linear"), (1.3, (1, 1, 1)), (2.0, (1, 1, 1)))
    a.rot("jaw", (0, Z), (0.8, (30, 0, 0)), (1.2, (10, 0, 0)), (2.0, Z))
    # coins: dig into the treasure at his belt and fling gold to the sky (impact 0.70 s = 14 ticks)
    a = m.anim("coins", 1.8)
    a.rot("arm_l", (0, Z), (0.45, (25, 0, -10)), (0.6, (35, 0, -5)), (0.7, (-170, 0, -20), "linear"), (1.2, (-165, 0, -20)), (1.8, Z))
    a.rot("forearm_l", (0, Z), (0.45, (-40, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.8, Z))
    a.rot("torso", (0, Z), (0.45, (18, -20, 0)), (0.7, (-18, 10, 0), "linear"), (1.2, (-15, 10, 0)), (1.8, Z))
    a.rot("head", (0, Z), (0.45, (10, 0, 0)), (0.7, (-30, 0, 0)), (1.2, (-30, 0, 0)), (1.8, Z))
    a.rot("jaw", (0, Z), (0.7, (30, 0, 0)), (1.2, (30, 0, 0)), (1.8, Z))
    # summon: a bellowing call to his brutes, head thrown back, a fist beating the chest (impact 0.60 s)
    a = m.anim("summon", 1.8)
    a.rot("head", (0, Z), (0.5, (-40, 0, 0)), (1.3, (-40, 0, 0)), (1.8, Z))
    a.rot("jaw", (0, Z), (0.5, (40, 0, 0)), (1.3, (40, 0, 0)), (1.8, Z))
    a.rot("torso", (0, Z), (0.5, (-18, 0, 0)), (1.3, (-18, 0, 0)), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.3, (-60, 0, -10)), (0.45, (-40, -40, 0)), (0.6, (-70, -50, 0)), (0.75, (-40, -40, 0)),
          (0.9, (-70, -50, 0)), (1.3, (-60, 0, -10)), (1.8, Z))
    a.rot("ear_r", (0, Z), (0.5, (0, 0, 25)), (1.3, (0, 0, 25)), (1.8, Z))
    a.rot("ear_l", (0, Z), (0.5, (0, 0, -25)), (1.3, (0, 0, -25)), (1.8, Z))
    # throw: the mace wound back behind the head, hurled spinning out along a line and caught on its
    # return (release at 0.80 s = 16 ticks, farthest at 1.25 s, back in the hand at 1.7 s)
    a = m.anim("throw", 2.4)
    a.rot("arm_r", (0, Z), (0.7, (-160, 0, 30)), (0.8, (-104, 0, 0), "linear"), (1.75, (-104, 0, 0)), (1.9, (-90, 0, 0)), (2.4, Z))
    a.rot("forearm_r", (0, Z), (0.7, ST), (1.9, ST), (2.4, Z))
    a.rot("mace", (0, Z), (0.7, off(EXT, -70)), (0.8, EXT, "linear"), (1.25, off(EXT, -720), "linear"),
          (1.7, off(EXT, -1440), "linear"), (1.9, off(EXT, -1440)), (2.4, (-1440, 0, 0)))
    a.pos("mace", (0, Z), (0.8, Z), (1.25, (0, -176, 0), "linear"), (1.7, Z, "linear"), (2.4, Z))
    a.rot("torso", (0, Z), (0.7, (-12, 30, 0)), (0.8, (14, -15, 0), "linear"), (1.75, (12, -15, 0)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.7, (-50, 0, -30)), (0.8, (10, 0, -10)), (2.4, Z))
    a.pos("bone", (0, Z), (0.7, (0, 0, 3)), (0.8, (0, 0, -4), "linear"), (1.75, (0, 0, -4)), (2.4, Z))
    # whirl: mace held out at arm's length, three heavy turns (wind-up 0.60 s, spins until 1.6 s)
    a = m.anim("whirl", 2.2)
    a.rot("bone", (0, Z), (0.6, (0, 50, 0)), (1.6, (0, -1030, 0), "linear"), (1.8, (0, -1080, 0)), (2.2, (0, -1080, 0)))
    a.rot("arm_r", (0, Z), (0.6, (-10, 0, 85)), (1.6, (-10, 0, 85)), (2.2, Z))
    a.rot("forearm_r", (0, Z), (0.6, ST), (1.6, ST), (2.2, Z))
    a.rot("mace", (0, Z), (0.6, EXT), (1.6, EXT), (2.2, Z))
    a.rot("arm_l", (0, Z), (0.6, (-10, 0, -80)), (1.6, (-10, 0, -80)), (2.2, Z))
    a.rot("torso", (0, Z), (0.6, (8, 30, 0)), (1.6, (8, 0, 0)), (2.2, Z))
    a.rot("cape", (0, Z), (0.6, (10, 0, 0)), (0.9, (65, 0, 0)), (1.6, (65, 0, 0)), (2.2, Z))
    # roar: phase two, enraged: arms flung wide, head up, belly heaving
    a = m.anim("roar", 2.6)
    a.rot("torso", (0, Z), (0.5, (-20, 0, 0)), (2.1, (-20, 0, 0)), (2.6, Z))
    a.rot("head", (0, Z), (0.5, (-35, 0, 0)), (2.1, (-35, 0, 0)), (2.6, Z))
    a.rot("jaw", (0, Z), (0.5, (40, 0, 0)), (2.1, (40, 0, 0)), (2.6, Z))
    a.rot("arm_r", (0, Z), (0.5, (-40, 0, 70)), (2.1, (-40, 0, 70)), (2.6, Z))
    a.rot("arm_l", (0, Z), (0.5, (-40, 0, -70)), (2.1, (-40, 0, -70)), (2.6, Z))
    a.scale("belly", (0, (1, 1, 1)), (0.5, (1.08, 1.04, 1.1)), (1.3, (1.02, 1, 1.03)), (2.1, (1.08, 1.04, 1.1)), (2.6, (1, 1, 1)))
    # stagger: posture broken, sits down hard, the mace dropped to the ground
    a = m.anim("stagger", 2.5)
    a.pos("bone", (0, Z), (0.3, (0, -7, 3)), (2.1, (0, -7, 3)), (2.5, Z))
    for leg, sx in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, Z), (0.3, (-70, 0, 15 * sx)), (2.1, (-70, 0, 15 * sx)), (2.5, Z))
    a.rot("torso", (0, Z), (0.3, (-15, 0, 0)), (2.1, (-15, 0, 0)), (2.5, Z))
    a.rot("head", (0, Z), (0.3, (25, 0, 10)), (2.1, (25, 0, 10)), (2.5, Z))
    a.rot("arm_r", (0, Z), (0.3, (-20, 0, 30)), (2.1, (-20, 0, 30)), (2.5, Z))
    a.rot("forearm_r", (0, Z), (0.3, (100, 0, 0)), (2.1, (100, 0, 0)), (2.5, Z))
    a.rot("mace", (0, Z), (0.3, (95, 0, 15)), (2.1, (95, 0, 15)), (2.5, Z))
    a.rot("arm_l", (0, Z), (0.3, (-20, 0, -30)), (2.1, (-20, 0, -30)), (2.5, Z))
