"""The Oathbound Gatekeeper (Le Gardien du Serment): the living knight of the Kneeling Gate, about 5.6 blocks tall.

Silhouette idea: one of the two 70-block statues above the pass, come down from the pass at giant size and awake. The same
pale limestone plate (darker low, calcite on the top edges), grey stone mail, waxed copper trim, a red-granite cloak
falling from the shoulders to the calves, an open helm with a nasal, cheek plates and a copper crest, a braided stone
beard over the breastplate. The oath that binds him to the gate shows as soul-blue light in his eyes and in the
cracks of his plate. Strong asymmetry: a tower shield taller than a man on the LEFT arm, its face carved with the gold
key of the toll; a long stone greatsword in the RIGHT hand, point down; and the gate's own key, a great gold key on an
iron chain, hanging from his belt at the right hip.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

LIME = (204, 196, 174)
LIME_L = (234, 228, 210)
LIME_D = (150, 142, 124)
LIME_DD = (104, 98, 86)
MAIL = (116, 116, 114)
MAIL_L = (152, 152, 148)
MAIL_D = (74, 74, 74)
COP = (182, 108, 62)
COP_L = (226, 158, 102)
COP_D = (114, 64, 36)
GRAN = (146, 60, 52)
GRAN_L = (180, 94, 80)
GRAN_D = (96, 38, 34)
GOLD = (240, 196, 80)
GOLD_L = (255, 236, 160)
GOLD_D = (180, 124, 34)
IRON = (70, 66, 66)
IRON_L = (112, 106, 104)
OATH = (110, 232, 236)
OATH_L = (210, 255, 255)
OATH_D = (40, 160, 178)


def lime(seed=0, trim=False, crack=0.0, grad=0.24):
    """Pale limestone plate: a calcite top edge, a darker rim (or a waxed copper trim), darker toward the bottom, faint
    speckles and fossil flecks, an optional hairline crack running down from the top."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(LIME_D, 0.85)
        if face == "top":
            if x in (0, w - 1) or y in (0, h - 1):
                return COP_L if trim else LIME_L
            return mul(LIME_L, 0.97 + (B.n(x, y, seed) - 0.5) * 0.06)
        if w > 2 and h > 2:
            if y == 0:
                return COP_L if trim else LIME_L
            if x in (0, w - 1) or y == h - 1:
                return (COP if B.n(x, y, seed) > 0.12 else COP_D) if trim else LIME_D
        if crack and w > 3:
            cx = int(B.n(seed, 0, 77) * (w - 2)) + 1
            if abs(x - (cx + (y * 0.4 if seed % 2 else -y * 0.4))) < 0.5 and y < h * (0.3 + crack):
                return mul(LIME_DD, 0.8)
        v = B.n(x, y, seed)
        if v < 0.015:
            return LIME_D
        if v > 0.98:
            return LIME_L
        return mul(LIME, 1.06 + grad * (0.4 - y / max(1, h)) * 0.6 + (B.n(x // 2, y // 2, seed + 3) - 0.5) * 0.07)
    return f


def lime_glow(seed=0, crack=0.0):
    """The oath light in the same hairline crack that lime(seed, crack=...) paints."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom") or not crack or w <= 3:
            return None
        cx = int(B.n(seed, 0, 77) * (w - 2)) + 1
        if abs(x - (cx + (y * 0.4 if seed % 2 else -y * 0.4))) < 0.5 and y < h * (0.3 + crack):
            return OATH if y % 3 else OATH_L
        return None
    return f


def mail(seed=0):
    """Grey stone mail: offset rows of rings, each ring lit on top, the rows darkening downward."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(MAIL, 1.05 if face == "top" else 0.7)
        ring = (x + (y // 2) % 2) % 2
        if y % 2 == 0:
            c = MAIL_L if ring else MAIL
        else:
            c = MAIL if ring else MAIL_D
        return mul(c, 1.04 - 0.16 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
    return f


def granite(seed=0, hem=False):
    """Red granite cloth: folds every five texels, black and white specks, a ragged darker hem."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GRAN_D
        if face == "top":
            return GRAN_L
        if hem and y >= h - 2:
            if B.n(x, 0, seed) < 0.3:
                return None
            return GRAN_D
        v = B.n(x, y, seed)
        if v < 0.02:
            return (70, 34, 32)
        if v > 0.985:
            return (214, 170, 156)
        fold = x % 5
        k = 1.1 if fold == 1 else (0.82 if fold == 4 else 1.0)
        return mul(GRAN, k * (1.06 - 0.16 * y / max(1, h)))
    return f


def copper(seed=0):
    return B.plate(COP, COP_D, COP_L, seed=seed)


def tabard_paint(f, x, y, w, h):
    """The tabard: red granite cloth with the gold key of the toll, bow up, a copper border, a ragged hem."""
    if f in ("top", "bottom", "left", "right"):
        return GRAN_D
    if y >= h - 2 and B.n(x, 0, 31) < 0.35:
        return None
    if x in (0, w - 1):
        return COP_D
    cx = (w - 1) / 2
    dy = y - 4.0
    if (x - cx) ** 2 + dy ** 2 <= 6.5 and (x - cx) ** 2 + dy ** 2 >= 1.5:
        return GOLD if dy < 0 else GOLD_D                   # the bow
    if abs(x - cx) < 0.6 and 6 <= y <= 15:
        return GOLD                                          # the shaft
    if 12 <= y <= 15 and cx < x <= cx + 2 and (y != 14 or x < cx + 2):
        return GOLD_D                                        # the bit
    return granite(32)(f, x, y, w, h)


def breast_paint(f, x, y, w, h):
    """The breastplate: limestone with a copper-trimmed neckline, a raised central ridge, a crack of oath light."""
    if f != "front":
        return lime(60, trim=f == "back")(f, x, y, w, h)
    if y in (0, 1):
        return COP_L if y == 0 else COP
    cx = (w - 1) / 2
    if abs(x - cx) < 1.0:
        return LIME_L if y < h - 3 else LIME_D
    if abs(x - (cx - 6 + y * 0.3)) < 0.55 and 4 <= y <= 15:
        return mul(LIME_DD, 0.8)
    if y in (10, 11) and abs(x - cx) > 2 and x not in (0, w - 1):
        return mul(LIME_D, 0.95)                             # the rib line
    return lime(61)(f, x, y, w, h)


def breast_glow(f, x, y, w, h):
    cx = (w - 1) / 2
    if f == "front" and abs(x - (cx - 6 + y * 0.3)) < 0.55 and 4 <= y <= 15:
        return OATH if y % 3 else OATH_L
    return None


def helm_paint(f, x, y, w, h):
    """Open helm over a stone face: a limestone skull with a copper brow band, deep eye sockets with soul-blue eyes,
    stone cheeks and a heavy moustache falling into the beard."""
    if f == "top":
        return LIME_L if B.n(x, y, 40) < 0.7 else LIME
    if f == "bottom":
        return LIME_DD
    if f == "front":
        if y <= 3:
            return COP_L if y == 3 else lime(41)(f, x, y, w, h)
        if y == 4:
            return COP_D
        if y in (5, 6):
            if x in (2, 3) or x in (w - 4, w - 3):
                return OATH if y == 5 else OATH_D
            return mul(LIME_DD, 0.55) if 1 <= x <= w - 2 else LIME_D
        if x in (0, w - 1):
            return LIME_D                                     # the cheek guards' edge
        if y >= 10 and 2 <= x <= w - 3:
            return mix(LIME_L, LIME, 0.5) if (x + y) % 3 else LIME_D     # moustache
        return mul((178, 168, 150), 1.0 + (B.n(x, y, 42) - 0.5) * 0.08)  # stone skin
    return lime(43, trim=False)(f, x, y, w, h)


def helm_glow(f, x, y, w, h):
    if f == "front" and y in (5, 6) and (x in (2, 3) or x in (w - 4, w - 3)):
        return OATH_L if y == 5 else OATH
    return None


def beard_paint(f, x, y, w, h):
    """Braided stone beard: three plaits with copper rings."""
    if f in ("top", "bottom"):
        return LIME_D
    if y % 5 == 4:
        return COP if x % 2 else COP_L
    k = (x + y // 2) % 3                                    # diagonal twists of the plaits
    return (LIME_L, (196, 186, 162), (150, 140, 120))[k]


def shield_paint(f, x, y, w, h):
    """The tower shield: a thick waxed-copper rim, a limestone field carved with the gold key of the toll (bow at the
    top), soul-blue runes either side of the shaft, cracks."""
    if f != "front":
        if f == "back":
            return mail(90)(f, x, y, w, h)
        return copper(91)(f, x, y, w, h)
    if x in (0, w - 1) or y in (0, h - 1):
        return COP_L if y == 0 else COP_D
    if x in (1, w - 2) or y in (1, h - 2):
        return COP
    cx = (w - 1) / 2
    by = 8.5
    d = ((x - cx) ** 2 + (y - by) ** 2) ** 0.5
    if 2.4 <= d <= 4.6:
        return GOLD_L if y < by - 2 else (GOLD if y < by + 2 else GOLD_D)     # the bow ring
    if abs(x - cx) < 1.0 and by + 4.4 <= y <= h - 6:
        return GOLD if x <= cx else GOLD_D                                    # the shaft
    if h - 13 <= y <= h - 6 and cx + 1 <= x <= cx + 5 and not (y == h - 10 and x >= cx + 3):
        return GOLD_D if x == cx + 5 or y == h - 6 else GOLD                  # the bit
    if x in (int(cx) - 5, int(cx) + 6) and 14 <= y <= h - 12 and y % 4 != 3:
        return OATH_D                                                         # rune columns
    if abs(x - (cx - 7 + (y - 20) * 0.25)) < 0.55 and y > 22:
        return mul(LIME_DD, 0.7)                                              # a long crack
    if y % 9 == 4 and x in (2, w - 3):
        return COP_L                                                          # rivets down the rim
    return lime(92, grad=0.15)(f, x, y, w, h)


def shield_glow(f, x, y, w, h):
    if f != "front":
        return None
    cx = (w - 1) / 2
    if x in (int(cx) - 5, int(cx) + 6) and 14 <= y <= h - 12 and y % 4 != 3:
        return OATH if y % 4 else OATH_L
    return None


def blade_paint(f, x, y, w, h):
    """The stone greatsword: pale grey edges honed almost white, a darker fuller cut with soul-blue runes."""
    if f in ("top", "bottom"):
        return LIME_L
    if f in ("left", "right"):
        return mix(LIME_L, (250, 250, 246), 0.5)
    if x in (0, w - 1):
        return mix(LIME_L, (250, 250, 246), 0.4)
    if x == w // 2 and y % 5 == 2 and y < h - 5:
        return OATH_D
    if x == w // 2:
        return mul(MAIL, 0.9)
    return mul((176, 174, 166), 1.08 - 0.12 * y / h + (B.n(x, y, 95) - 0.5) * 0.06)


def blade_glow(f, x, y, w, h):
    if f in ("front", "back") and x == w // 2 and y % 5 == 2 and y < h - 5:
        return OATH
    return None


def key_bow(f, x, y, w, h):
    """The great key's bow: a gold ring with a toothed rim (a 7 x 7 face, hollow in the middle)."""
    if f in ("front", "back"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d < 1.6:
            return None
        if d > 3.6:
            return None
        return GOLD_L if y < cy - 1 else (GOLD if y <= cy + 1 else GOLD_D)
    return GOLD_D


VARIANTS = ["oath", "broken"]


def _gone(face, x, y, w, h):
    return None


def build(variant=None):
    """``broken``: the same cubes with the shield painted away (the phase-3 shield break, modelVariant() 1)."""
    broken = variant == "broken"
    m = Model("oathbound_gatekeeper", seed=263, shadow=2.3, walk_speed=0.58, walk_scale=0.85, variants=VARIANTS)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -40, 0))
    m.part("tabard", "pelvis", pivot=(0, 3, -7.5))
    m.part("keychain", "pelvis", pivot=(-11, 1, -1), rot=(0, 0, 6))
    m.part("key", "keychain", pivot=(0, 15, 0), rot=(0, 20, 0))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0), rot=(4, 0, 0))
    m.part("head", "chest", pivot=(0, -25, -1), rot=(-4, 0, 0))
    m.part("beard", "head", pivot=(0, -1, -7))
    m.part("cloak", "chest", pivot=(0, -21, 8.5), rot=(2, 0, 0))
    m.part("cloak_lo", "cloak", pivot=(0, 26, 0.5), rot=(-2, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(6.5 * sx, 0, 0), rot=(0, 0, -3 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 20, 0), rot=(0, 0, 3 * sx))
    m.part("arm_r", "chest", pivot=(-16, -20, 0), rot=(-6, 0, 6))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-26, 0, 0))
    m.part("sword", "fore_r", pivot=(0, 14, -0.5), rot=(-12, 0, -4))
    m.part("arm_l", "chest", pivot=(16, -20, 0), rot=(-8, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-62, 0, 6))
    m.part("shield", "fore_l", pivot=(3, 8, -2), rot=(68, -6, 0))

    # ---- legs: stone mail thighs under limestone cuisses, copper-trimmed poleyns, greaves, broad sabatons
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -5, -2, -5, 10, 20, 10, mail(2 + (sx > 0)))
        m.box(th, -5.5, 1, -6, 11, 13, 3, lime(4 + (sx > 0)))                # cuisse
        m.box(th, -6 if sx < 0 else 4, 2, -4.5, 2, 11, 9, lime(6))                       # outer plate
        m.box(sh, -5.5, -3, -7.5, 11, 7, 3, lime(10))                         # poleyn
        m.box(sh, -2, -4, -8.5, 4, 3, 1, copper(12))                                     # its boss
        m.box(sh, -5, 2, -5.5, 10, 14, 10, lime(13 + (sx > 0), crack=0.3 if sx < 0 else 0.0),
              glow=lime_glow(13, 0.3) if sx < 0 else None)                               # greave
        m.box(sh, -5.5, -2, -4.5, 11, 5, 9, mail(14))                                    # the knee mail
        m.box(sh, -6.5, 15, -8.5, 13, 5, 14, lime(15))                        # sabaton
        m.box(sh, -5.5, 17, -9.5, 11, 3, 1, copper(16))                                  # toe cap

    # ---- pelvis: mail skirt, faulds, tassets, the tabard with the gold key
    m.box("pelvis", -11, -4, -7, 22, 8, 14, mail(20))
    m.box("pelvis", -12, 2, -7.5, 24, 6, 2, B.bands(LIME, COP_D, every=3, seed=21))     # faulds
    m.box("pelvis", -13, 1, -6, 2, 10, 12, lime(22))                          # tassets
    m.box("pelvis", 11, 1, -6, 2, 10, 12, lime(23))
    m.box("pelvis", -11, 1, 5.5, 22, 7, 2, B.bands(LIME, COP_D, every=3, seed=24))
    m.box("tabard", -5, 0, -1, 10, 24, 1, tabard_paint)

    # ---- the gate key on its chain, at the right hip
    m.box("keychain", -1, -1, -1, 2, 2, 2, IRON)                                        # the belt ring
    for i in range(4):
        if i % 2 == 0:
            m.box("keychain", -1, 1 + i * 3.5, -0.5, 2, 4, 1, B.rod(IRON_L, 30 + i))
        else:
            m.box("keychain", -0.5, 1 + i * 3.5, -1, 1, 4, 2, B.rod(IRON, 30 + i))
    m.box("key", -3.5, 0, -0.5, 7, 7, 1, key_bow)                                        # the bow
    m.box("key", -1, 7, -1, 2, 15, 2, B.plate(GOLD, GOLD_D, GOLD_L, seed=34))            # the shaft
    m.box("key", -2, 7, -1.5, 4, 1, 3, GOLD_D)                                           # collar
    m.box("key", 1, 16, -1, 4, 2, 2, GOLD)                                               # the bit's teeth
    m.box("key", 1, 19, -1, 3, 2, 2, GOLD_D)
    m.box("key", 3, 18, -1, 1, 1, 2, GOLD_D)

    # ---- the waist: mail under a copper-studded belt
    m.box("waist", -10, -6, -6.5, 20, 6, 13, mail(26))
    m.box("waist", -11, -3, -7, 22, 3, 14, B.plate(COP_D, mul(COP_D, 0.6), COP, seed=27, rivet_step=3))
    m.box("waist", -2.5, -4, -7.8, 5, 5, 1, B.plate(GOLD_D, mul(GOLD_D, 0.6), GOLD, seed=28))   # buckle

    # ---- chest: breastplate, back plate, gorget, the cloak's clasps
    m.box("chest", -13, -24, -8.5, 26, 24, 16, breast_paint, glow=breast_glow)
    m.box("chest", -1, -23, -9.5, 2, 21, 1, lime(29))                                    # ridge
    m.box("chest", -11, -22, 7, 22, 18, 2, lime(30))                          # back plate
    m.box("chest", -8, -26, -7.5, 16, 4, 14, lime(31, trim=True))                        # gorget
    for sx in (-1, 1):
        m.box("chest", 9 * sx - 1.5, -23, 7.5, 3, 3, 2, B.plate(GOLD_D, mul(GOLD_D, 0.6), GOLD, seed=32))  # clasps

    # ---- the red granite cloak, in two tiers that sway
    m.box("cloak", -13, 0, 0, 26, 26, 2, granite(35))
    m.box("cloak", -14, -1, -1, 28, 3, 3, granite(36))                                   # folded collar
    m.box("cloak_lo", -14, 0, -0.5, 28, 26, 2, granite(37, hem=True))

    # ---- head: open helm, nasal, cheek plates, copper crest, braided beard
    m.box("head", -7, -15, -7, 14, 15, 13, helm_paint, glow=helm_glow)
    m.box("head", -7.5, -11, -7.5, 15, 2, 14, B.plate(COP, COP_D, COP_L, seed=40))      # brow band
    m.box("head", -0.5, -11, -8.5, 1, 7, 1, lime(41))                                    # nasal
    m.box("head", -8, -9, -8, 3, 9, 7, lime(42))                                        # cheek plates
    m.box("head", 5, -9, -8, 3, 9, 7, lime(43))
    m.box("head", -1.5, -21, -8, 3, 7, 15, copper(44))                                   # crest
    m.box("head", -1, -22, -9, 2, 2, 3, COP_L)
    m.box("beard", -5, 0, -2.5, 10, 8, 3, beard_paint)
    m.box("beard", -4, 8, -2.5, 2, 8, 2, beard_paint)                                    # three plaits
    m.box("beard", -1, 8, -3, 2, 10, 2, beard_paint)
    m.box("beard", 2, 8, -2.5, 2, 8, 2, beard_paint)

    # ---- right arm: layered pauldron, mail arm, vambrace, gauntlet; the greatsword
    m.box("arm_r", -9, -7, -7.5, 13, 9, 15, lime(45))
    m.box("arm_r", -9.5, 1, -8, 12, 3, 16, lime(46))
    m.box("arm_r", -4, 2, -4, 8, 11, 8, mail(47))
    m.box("fore_r", -4.5, 0, -4.5, 9, 11, 9, lime(50))
    m.box("fore_r", -4, 11, -4.5, 8, 5, 8, B.plate(MAIL_L, MAIL_D, LIME_L, seed=51))
    m.box("sword", -1.5, -8, -1.5, 3, 3, 3, B.plate(GOLD_D, COP_D, GOLD, seed=52))      # pommel
    m.box("sword", -1, -5, -1, 2, 8, 2, B.rod(B.LEATHER, 53))
    m.box("sword", -8, 3, -1.5, 16, 2, 3, copper(54))                                    # crossguard
    m.box("sword", -9, 1, -1, 2, 4, 2, COP_L)
    m.box("sword", 7, 1, -1, 2, 4, 2, COP_L)
    m.box("sword", -3, 5, -1, 6, 42, 2, blade_paint, glow=blade_glow)
    m.box("sword", -2, 47, -1, 4, 2, 2, mix(LIME_L, (250, 250, 246), 0.3))
    m.box("sword", -1, 49, -1, 2, 1, 2, mix(LIME_L, (250, 250, 246), 0.5))

    # ---- left arm: pauldron, mail arm, vambrace; the tower shield carved with the key
    m.box("arm_l", -4, -7, -7.5, 13, 9, 15, lime(56))
    m.box("arm_l", -2.5, 1, -8, 12, 3, 16, lime(57))
    m.box("arm_l", -4, 2, -4, 8, 11, 8, mail(58))
    m.box("fore_l", -4.5, 0, -4.5, 9, 11, 9, lime(61))
    m.box("fore_l", -4, 11, -4.5, 8, 5, 8, B.plate(MAIL_L, MAIL_D, LIME_L, seed=62))
    m.box("shield", -12, -19, -6, 24, 40, 3, _gone if broken else shield_paint, glow=None if broken else shield_glow)
    m.box("shield", -12.5, -20, -5.5, 25, 2, 2, _gone if broken else copper(63))        # top rim
    m.box("shield", -3, -4, -3, 6, 8, 3, _gone if broken else B.plate(MAIL_D, mul(MAIL_D, 0.6), seed=64))  # grip

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))
    Z = (0, 0, 0)

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, Z), (2.0, (0, 0.7, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.3, (0, 6, 0)), (2.3, (0, 6, 0)), (3.2, (0, -5, 0)), (4.0, Z))
    idle.rot("cloak", (0, Z), (2.0, (3, 0, 1)), (4.0, Z))
    idle.rot("cloak_lo", (0, Z), (2.0, (4, 0, -1)), (4.0, Z))
    idle.rot("tabard", (0, Z), (2.0, (-3, 0, 2)), (4.0, Z))
    idle.rot("keychain", (0, Z), (1.0, (6, 0, 3)), (3.0, (-6, 0, -2)), (4.0, Z))
    idle.rot("key", (0, Z), (2.0, (0, 30, 0)), (4.0, Z))
    idle.rot("arm_l", (0, Z), (2.0, (-2, 0, 0)), (4.0, Z))
    idle.rot("arm_r", (0, Z), (2.0, (2, 0, 0)), (4.0, Z))

    walk = m.anim("walk", 2.0)
    walk.rot("thigh_r", (0, (20, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("thigh_l", (0, (-20, 0, 0)), (1.0, (20, 0, 0)), (2.0, (-20, 0, 0)))
    walk.rot("shin_r", (0, Z), (0.5, (26, 0, 0)), (1.0, Z), (2.0, Z))
    walk.rot("shin_l", (0, Z), (1.0, Z), (1.5, (26, 0, 0)), (2.0, Z))
    walk.rot("arm_r", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))
    walk.rot("chest", (0, (0, 3, 0)), (1.0, (0, -3, 0)), (2.0, (0, 3, 0)))
    walk.pos("pelvis", (0, Z), (0.5, (0, -1.2, 0)), (1.0, Z), (1.5, (0, -1.2, 0)), (2.0, Z))
    walk.rot("cloak", (0, (8, 0, 0)), (1.0, (12, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("cloak_lo", (0, (4, 0, 0)), (1.0, (10, 0, 0)), (2.0, (4, 0, 0)))
    walk.rot("keychain", (0, (-10, 0, 0)), (1.0, (12, 0, 0)), (2.0, (-10, 0, 0)))
    walk.rot("tabard", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))

    # sweep: the greatsword drawn far back to his right (0.8 s = 16 ticks), then swept flat across his front
    a = m.anim("sweep", 1.7)
    a.rot("arm_r", (0, Z), (0.7, (-14, -40, 74)), (0.8, (-16, -44, 78)), (0.95, (-86, 56, -14), "linear"),
          (1.2, (-82, 60, -14)), (1.7, Z))
    a.rot("sword", (0, Z), (0.8, (-40, 0, 0)), (0.95, (10, 0, 60), "linear"), (1.2, (10, 0, 56)), (1.7, Z))
    a.rot("chest", (0, Z), (0.8, (0, -36, 0)), (0.95, (0, 38, 0), "linear"), (1.2, (0, 40, 0)), (1.7, Z))
    a.rot("waist", (0, Z), (0.8, (0, -10, 0)), (0.95, (0, 10, 0), "linear"), (1.7, Z))
    a.rot("arm_l", (0, Z), (0.8, (-14, 0, -10)), (0.95, (6, 0, -6), "linear"), (1.7, Z))
    a.rot("cloak", (0, Z), (0.8, (8, 20, 0)), (1.0, (14, -24, 0)), (1.7, Z))
    a.rot("thigh_r", (0, Z), (0.8, (12, 0, 4)), (1.7, Z))
    a.rot("thigh_l", (0, Z), (0.8, (-14, 0, -6)), (1.7, Z))

    # thrust: behind the shield, the blade drawn back level at the hip (0.7 s = 14 ticks), then a lunging thrust
    a = m.anim("thrust", 1.8)
    a.rot("arm_r", (0, Z), (0.6, (-40, 0, 30)), (0.7, (-42, 0, 32)), (0.8, (-88, 0, 4), "linear"), (1.1, (-86, 0, 4)),
          (1.8, Z))
    a.rot("fore_r", (0, Z), (0.7, (-40, 0, 0)), (0.8, (14, 0, 0), "linear"), (1.1, (12, 0, 0)), (1.8, Z))
    a.rot("sword", (0, Z), (0.7, (36, 0, 0)), (0.8, (28, 0, 0), "linear"), (1.1, (28, 0, 0)), (1.8, Z))
    a.rot("chest", (0, Z), (0.7, (4, 26, 0)), (0.8, (16, -14, 0), "linear"), (1.1, (14, -12, 0)), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.7, (-20, 0, 10)), (1.1, (-10, 0, 6)), (1.8, Z))
    a.pos("pelvis", (0, Z), (0.7, (0, -3, 3)), (0.8, (0, -3, -7), "linear"), (1.1, (0, -3, -7)), (1.8, Z))
    a.rot("thigh_l", (0, Z), (0.7, (12, 0, 0)), (0.8, (-38, 0, 0), "linear"), (1.1, (-34, 0, 0)), (1.8, Z))
    a.rot("shin_l", (0, Z), (0.8, (26, 0, 0), "linear"), (1.1, (24, 0, 0)), (1.8, Z))
    a.rot("thigh_r", (0, Z), (0.7, (-14, 0, 0)), (0.8, (26, 0, 0), "linear"), (1.1, (22, 0, 0)), (1.8, Z))
    a.rot("cloak", (0, Z), (0.8, (6, 0, 0)), (1.1, (4, 0, 0)), (1.8, Z))

    # bash: the shield drawn in to the chest (0.6 s = 12 ticks), then rammed out at whoever stands in front
    a = m.anim("bash", 1.3)
    a.rot("arm_l", (0, Z), (0.5, (20, 20, 10)), (0.6, (22, 22, 10)), (0.7, (-44, -10, 0), "linear"), (0.9, (-40, -10, 0)),
          (1.3, Z))
    a.rot("fore_l", (0, Z), (0.6, (12, 0, 0)), (0.7, (24, 0, 0), "linear"), (0.9, (20, 0, 0)), (1.3, Z))
    a.rot("chest", (0, Z), (0.6, (8, 28, 0)), (0.7, (14, -16, 0), "linear"), (0.9, (12, -14, 0)), (1.3, Z))
    a.pos("pelvis", (0, Z), (0.6, (0, -2, 2)), (0.7, (0, -2, -5), "linear"), (0.9, (0, -2, -5)), (1.3, Z))
    a.rot("thigh_l", (0, Z), (0.6, (10, 0, 0)), (0.7, (-30, 0, 0), "linear"), (0.9, (-26, 0, 0)), (1.3, Z))
    a.rot("thigh_r", (0, Z), (0.6, (-12, 0, 0)), (0.7, (20, 0, 0), "linear"), (0.9, (18, 0, 0)), (1.3, Z))
    a.rot("arm_r", (0, Z), (0.6, (16, 0, 10)), (1.3, Z))

    # stomp: the right foot raised high (0.9 s = 18 ticks), driven down: force rolls out all round him
    a = m.anim("stomp", 1.7)
    a.rot("thigh_r", (0, Z), (0.8, (-74, 0, 8)), (0.9, (-78, 0, 8)), (1.0, (-6, 0, 0), "linear"), (1.25, (-6, 0, 0)),
          (1.7, Z))
    a.rot("shin_r", (0, Z), (0.9, (66, 0, 0)), (1.0, (8, 0, 0), "linear"), (1.25, (8, 0, 0)), (1.7, Z))
    a.rot("thigh_l", (0, Z), (0.9, (6, 0, 0)), (1.0, (-10, 0, 0), "linear"), (1.7, Z))
    a.rot("chest", (0, Z), (0.9, (-14, 0, -6)), (1.0, (18, 0, 0), "linear"), (1.25, (16, 0, 0)), (1.7, Z))
    a.rot("arm_r", (0, Z), (0.9, (-30, 0, 30)), (1.0, (10, 0, 10), "linear"), (1.7, Z))
    a.rot("arm_l", (0, Z), (0.9, (-20, 0, -26)), (1.0, (6, 0, -10), "linear"), (1.7, Z))
    a.rot("keychain", (0, Z), (0.9, (-20, 0, 20)), (1.05, (30, 0, -10)), (1.4, (-10, 0, 4)), (1.7, Z))
    a.pos("pelvis", (0, Z), (0.9, (0, 2, 0)), (1.0, (0, -3, 0), "linear"), (1.25, (0, -2.5, 0)), (1.7, Z))

    # keyfall: the key's chain wound round the gauntlet and the key swung up over the helm (0.9 s = 18 ticks), then
    # hurled at the target; he holds the follow-through while it falls a second later
    a = m.anim("keyfall", 2.5)
    a.rot("keychain", (0, Z), (0.5, (-80, 0, 40)), (0.9, (-200, 0, 20)), (1.0, (-90, 0, 0), "linear"),
          (1.9, (-80, 0, 0)), (2.5, Z))
    a.rot("key", (0, Z), (0.9, (0, 0, 0)), (1.0, (40, 0, 0), "linear"), (1.9, (40, 0, 0)), (2.5, Z))
    a.rot("arm_r", (0, Z), (0.5, (-40, 0, 10)), (0.9, (-160, 0, -10)), (1.0, (-80, 0, -6), "linear"), (1.9, (-74, 0, -4)),
          (2.5, Z))
    a.rot("sword", (0, Z), (0.9, (20, 0, 0)), (1.9, (10, 0, 0)), (2.5, Z))
    a.rot("chest", (0, Z), (0.9, (-14, 18, 0)), (1.0, (14, -10, 0), "linear"), (1.9, (12, -8, 0)), (2.5, Z))
    a.rot("arm_l", (0, Z), (0.9, (-6, 0, -20)), (1.9, (-10, 0, -14)), (2.5, Z))
    a.rot("head", (0, Z), (0.9, (-20, 0, 0)), (1.0, (4, 0, 0)), (1.9, (10, 0, 0)), (2.5, Z))
    a.rot("thigh_l", (0, Z), (0.9, (8, 0, 0)), (1.0, (-24, 0, 0), "linear"), (1.9, (-22, 0, 0)), (2.5, Z))
    a.rot("thigh_r", (0, Z), (0.9, (-8, 0, 0)), (1.0, (16, 0, 0), "linear"), (1.9, (14, 0, 0)), (2.5, Z))

    # wheel: he sets his feet and turns his shoulder (0.7 s = 14 ticks), then spins once round, blade out
    a = m.anim("wheel", 1.6)
    a.rot("arm_r", (0, Z), (0.6, (-12, -30, 70)), (0.7, (-12, -34, 80)), (0.95, (-12, 0, 86), "linear"),
          (1.15, (-10, 0, 80)), (1.6, Z))
    a.rot("sword", (0, Z), (0.7, (-40, 0, 0)), (0.95, (-80, 0, 0), "linear"), (1.15, (-70, 0, 0)), (1.6, Z))
    a.rot("bone", (0, Z), (0.7, (0, 30, 0)), (0.95, (0, -330, 0), "linear"), (1.15, (0, -360, 0)), (1.6, (0, -360, 0)))
    a.rot("chest", (0, Z), (0.7, (8, -20, 0)), (0.95, (8, 10, 0), "linear"), (1.6, Z))
    a.rot("cloak", (0, Z), (0.7, (10, 0, 0)), (0.95, (60, 0, 10)), (1.3, (20, 0, 0)), (1.6, Z))
    a.rot("cloak_lo", (0, Z), (0.95, (30, 0, 0)), (1.3, (10, 0, 0)), (1.6, Z))
    a.rot("keychain", (0, Z), (0.95, (-30, 0, 70)), (1.3, (10, 0, 10)), (1.6, Z))
    a.pos("pelvis", (0, Z), (0.7, (0, -3, 0)), (1.15, (0, -2, 0)), (1.6, Z))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, Z), (0.7, (-14, 0, -8 * sx)), (1.15, (-10, 0, -6 * sx)), (1.6, Z))
        a.rot(f"shin_{side}", (0, Z), (0.7, (22, 0, 0)), (1.15, (16, 0, 0)), (1.6, Z))

    # keyswing (phase 2): the key whirled on its chain round his hip (0.9 s = 18 ticks), then swung out wide in a
    # full circle at chest height: deadly at mid range, safe inside it or far outside
    a = m.anim("keyswing", 1.8)
    a.rot("keychain", (0, Z, "linear"), (0.3, (0, 0, 60), "linear"), (0.9, (0, -540, 84), "linear"),
          (1.1, (0, -900, 88), "linear"), (1.4, (0, -1080, 40)), (1.8, (0, -1080, 0)))
    a.rot("key", (0, Z), (0.9, (0, 0, -30)), (1.4, (0, 0, -20)), (1.8, Z))
    a.rot("arm_r", (0, Z), (0.9, (-60, 0, 40)), (1.1, (-50, 0, 50)), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.9, (-20, 0, -20)), (1.8, Z))
    a.rot("chest", (0, Z), (0.9, (-6, 20, 0)), (1.1, (-6, -20, 0)), (1.8, Z))
    a.pos("pelvis", (0, Z), (0.9, (0, -2, 0)), (1.8, Z))

    # overhead (phase 2): the greatsword heaved high over the helm (1.1 s = 22 ticks), crashed down in front; stone
    # hands burst up along the blade's line. His guard is open the whole time.
    a = m.anim("overhead", 2.2)
    a.rot("arm_r", (0, Z), (0.95, (-168, 0, -14)), (1.1, (-174, 0, -16)), (1.2, (-42, 0, -10), "linear"),
          (1.6, (-44, 0, -10)), (2.2, Z))
    a.rot("fore_r", (0, Z), (1.1, Z), (1.2, (10, 0, 0), "linear"), (1.6, (10, 0, 0)), (2.2, Z))
    a.rot("sword", (0, Z), (1.1, (30, 0, 0)), (1.2, (-24, 0, 0), "linear"), (1.6, (-22, 0, 0)), (2.2, Z))
    a.rot("chest", (0, Z), (1.1, (-16, 8, 0)), (1.2, (26, -6, 0), "linear"), (1.6, (24, -6, 0)), (2.2, Z))
    a.rot("arm_l", (0, Z), (1.1, (14, 0, -30)), (1.6, (10, 0, -24)), (2.2, Z))
    a.rot("cloak", (0, Z), (1.1, (12, 0, 0)), (1.2, (-14, 0, 0), "linear"), (1.6, (-12, 0, 0)), (2.2, Z))
    a.pos("pelvis", (0, Z), (1.1, (0, 1, 0)), (1.2, (0, -4, 0), "linear"), (1.6, (0, -3.5, 0)), (2.2, Z))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, Z), (1.1, Z), (1.2, (-24, 0, -6 * sx), "linear"), (1.6, (-22, 0, -6 * sx)), (2.2, Z))
        a.rot(f"shin_{side}", (0, Z), (1.1, Z), (1.2, (36, 0, 0), "linear"), (1.6, (34, 0, 0)), (2.2, Z))

    # toll (phase 2, spectacle): he raises the greatsword (1.2 s = 24 ticks) and strikes his own shield like the
    # gate's bell; the toll rolls through the floor and rows of stone hands punch up across the hall (2 s)
    a = m.anim("toll", 4.0)
    a.rot("arm_r", (0, Z), (1.0, (-150, 0, 30)), (1.2, (-156, 0, 34)), (1.3, (-70, 0, -30), "linear"),
          (3.2, (-66, 0, -28)), (4.0, Z))
    a.rot("fore_r", (0, Z), (1.2, (-20, 0, 0)), (1.3, (-30, 0, 0), "linear"), (3.2, (-28, 0, 0)), (4.0, Z))
    a.rot("sword", (0, Z), (1.2, (40, 0, 0)), (1.3, (-20, 0, 40), "linear"), (3.2, (-20, 0, 40)), (4.0, Z))
    a.rot("arm_l", (0, Z), (1.0, (-30, -30, 30)), (1.2, (-32, -32, 30)), (1.3, (-30, -36, 32)), (3.2, (-30, -30, 30)),
          (4.0, Z))
    a.rot("chest", (0, Z), (1.2, (-12, 14, 0)), (1.3, (8, -6, 0), "linear"), (1.5, (4, -4, 0)), (3.2, (4, -4, 0)),
          (4.0, Z))
    a.rot("head", (0, Z), (1.2, (-24, 0, 0)), (1.4, (6, 0, 0)), (3.2, (6, 0, 0)), (4.0, Z))
    a.pos("chest", (0, Z), (1.3, Z), (1.35, (0, -0.8, 0), "linear"), (1.45, (0, 0.4, 0)), (1.55, (0, -0.3, 0)),
          (1.7, Z), (4.0, Z))
    a.pos("pelvis", (0, Z), (1.2, (0, 0.5, 0)), (1.3, (0, -2, 0), "linear"), (3.2, (0, -2, 0)), (4.0, Z))

    # rush (phase 2): he sets the shield and lowers his head (0.8 s = 16 ticks), then charges behind it
    a = m.anim("rush", 2.2)
    a.rot("arm_l", (0, Z), (0.7, (-26, 0, 14)), (0.8, (-28, 0, 14)), (1.6, (-28, 0, 14)), (2.2, Z))
    a.rot("shield", (0, Z), (0.8, (-6, 4, 0)), (1.6, (-6, 4, 0)), (2.2, Z))
    a.pos("shield", (0, Z), (0.8, (-12, 0, 0)), (1.6, (-12, 0, 0)), (2.2, Z))
    a.rot("chest", (0, Z), (0.8, (20, 0, 0)), (1.6, (22, 0, 0)), (2.2, Z))
    a.rot("head", (0, Z), (0.8, (8, 0, 0)), (1.6, (8, 0, 0)), (2.2, Z))
    a.rot("arm_r", (0, Z), (0.8, (-20, 0, 20)), (1.6, (-20, 0, 20)), (2.2, Z))
    a.rot("sword", (0, Z), (0.8, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.2, Z))
    a.rot("cloak", (0, Z), (0.8, (4, 0, 0)), (1.0, (16, 0, 0)), (1.6, (16, 0, 0)), (2.2, Z))
    a.rot("cloak_lo", (0, Z), (1.0, (18, 0, 0)), (1.6, (18, 0, 0)), (2.2, Z))
    a.pos("pelvis", (0, Z), (0.8, (0, -3, 0)), (1.6, (0, -3, 0)), (2.2, Z))
    a.rot("thigh_r", (0, Z), (0.8, (-10, 0, 0)), (1.0, (-34, 0, 0)), (1.2, (24, 0, 0)), (1.4, (-34, 0, 0)),
          (1.6, (10, 0, 0)), (2.2, Z))
    a.rot("thigh_l", (0, Z), (0.8, (10, 0, 0)), (1.0, (24, 0, 0)), (1.2, (-34, 0, 0)), (1.4, (24, 0, 0)),
          (1.6, (-10, 0, 0)), (2.2, Z))
    a.rot("shin_r", (0, Z), (1.0, (40, 0, 0)), (1.2, (10, 0, 0)), (1.4, (40, 0, 0)), (1.6, (10, 0, 0)), (2.2, Z))
    a.rot("shin_l", (0, Z), (1.0, (10, 0, 0)), (1.2, (40, 0, 0)), (1.4, (10, 0, 0)), (1.6, (20, 0, 0)), (2.2, Z))

    # kneel (phase 3): like the statues above the pass he sinks onto one knee behind his planted shield, sword point
    # in the floor (1.0 s = 20 ticks), and holds the oath for 10 s while the gate heals him; then he rises
    a = m.anim("kneel", 12.2)
    K, HOLD, END = 1.0, 11.0, 12.2
    _kneel_pose(a, K, HOLD, END)
    a.rot("head", (0, Z), (K, (16, 0, 0)), (6.0, (12, 6, 0)), (HOLD, (16, 0, 0)), (END, Z))

    # broken: the shield shatters out of his grip, he reels back and stays open (3 s)
    a = m.anim("broken", 3.0)
    a.rot("arm_l", (0, Z), (0.3, (-60, 0, -70)), (2.4, (-50, 0, -60)), (3.0, Z))
    a.rot("fore_l", (0, Z), (0.3, (40, 0, 0)), (2.4, (36, 0, 0)), (3.0, Z))
    a.scale("shield", (0, (1, 1, 1)), (0.2, (1.3, 1.3, 1.3), "linear"), (0.3, (0.01, 0.01, 0.01), "linear"),
            (2.9, (0.01, 0.01, 0.01)), (3.0, (1, 1, 1)))
    a.rot("chest", (0, Z), (0.3, (-24, -20, 0)), (0.6, (-18, -16, 0)), (2.4, (-16, -12, 0)), (3.0, Z))
    a.rot("head", (0, Z), (0.3, (-26, 10, 0)), (2.4, (-20, 8, 0)), (3.0, Z))
    a.rot("arm_r", (0, Z), (0.3, (-10, 0, 50)), (2.4, (-6, 0, 40)), (3.0, Z))
    a.pos("pelvis", (0, Z), (0.3, (0, -1, 4)), (2.4, (0, -1, 4)), (3.0, Z))
    a.rot("thigh_r", (0, Z), (0.3, (20, 0, 0)), (2.4, (18, 0, 0)), (3.0, Z))
    a.rot("thigh_l", (0, Z), (0.3, (-16, 0, 0)), (2.4, (-14, 0, 0)), (3.0, Z))
    a.rot("shin_l", (0, Z), (0.3, (20, 0, 0)), (2.4, (18, 0, 0)), (3.0, Z))

    # fury (phase 3, shield broken): both hands on the hilt, three great swings (0.7 s = 14 ticks, then every 0.6 s)
    a = m.anim("fury", 3.0)
    a.rot("arm_r", (0, Z), (0.6, (-20, -40, 76)), (0.7, (-22, -44, 80)), (0.85, (-86, 56, -14), "linear"),
          (1.15, (-80, 70, -20)), (1.3, (-30, -30, 60), "linear"), (1.45, (-166, 0, -10)),
          (1.9, (-172, 0, -14)), (2.0, (-44, 0, -10), "linear"), (2.4, (-44, 0, -10)), (3.0, Z))
    a.rot("sword", (0, Z), (0.7, (-40, 0, 0)), (0.85, (-70, 0, 0), "linear"), (1.15, (-60, 0, 0)),
          (1.3, (-70, 0, 0), "linear"), (1.9, (30, 0, 0)), (2.0, (-24, 0, 0), "linear"), (2.4, (-22, 0, 0)), (3.0, Z))
    a.rot("arm_l", (0, Z), (0.7, (-40, 30, 30)), (0.85, (-60, -20, 10), "linear"), (1.3, (-60, 30, 30)),
          (1.9, (-150, 0, 20)), (2.0, (-50, 0, 10), "linear"), (2.4, (-40, 0, 10)), (3.0, Z))
    a.rot("chest", (0, Z), (0.7, (0, -36, 0)), (0.85, (0, 38, 0), "linear"), (1.15, (0, 30, 0)),
          (1.3, (0, -30, 0), "linear"), (1.9, (-16, 0, 0)), (2.0, (26, 0, 0), "linear"), (2.4, (24, 0, 0)), (3.0, Z))
    a.pos("pelvis", (0, Z), (0.7, (0, -2, 0)), (1.3, (0, -2, -3)), (1.9, (0, 1, -3)), (2.0, (0, -4, -5), "linear"),
          (2.4, (0, -3.5, -5)), (3.0, Z))
    a.rot("cloak", (0, Z), (0.85, (10, -16, 0)), (1.3, (10, 16, 0)), (1.9, (12, 0, 0)), (2.0, (-14, 0, 0)), (3.0, Z))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, Z), (1.9, (-6 * (sx > 0), 0, 0)), (2.0, (-24, 0, -6 * sx), "linear"),
              (2.4, (-22, 0, -6 * sx)), (3.0, Z))
        a.rot(f"shin_{side}", (0, Z), (1.9, Z), (2.0, (36, 0, 0), "linear"), (2.4, (34, 0, 0)), (3.0, Z))

    # roar (phase two): the bell of the gate answers him; sword and shield flung wide, the helm thrown back
    a = m.anim("roar", 2.2)
    a.rot("arm_r", (0, Z), (0.6, (-60, 0, 60)), (1.8, (-64, 0, 64)), (2.2, Z))
    a.rot("sword", (0, Z), (0.6, (60, 0, 0)), (1.8, (60, 0, 0)), (2.2, Z))
    a.rot("arm_l", (0, Z), (0.6, (-10, 0, -36)), (1.8, (-12, 0, -40)), (2.2, Z))
    a.rot("head", (0, Z), (0.6, (-32, 0, 0)), (1.0, (-28, 6, 0)), (1.4, (-30, -6, 0)), (1.8, (-30, 0, 0)), (2.2, Z))
    a.rot("beard", (0, Z), (0.6, (-20, 0, 0)), (1.8, (-18, 0, 0)), (2.2, Z))
    a.rot("chest", (0, Z), (0.6, (-16, 0, 0)), (1.8, (-14, 0, 0)), (2.2, Z))
    a.rot("cloak", (0, Z), (0.6, (20, 0, 0)), (1.2, (26, 0, 4)), (1.8, (20, 0, 0)), (2.2, Z))
    a.pos("chest", (0, Z), (0.7, (0, 0.6, 0)), (0.8, (0, -0.4, 0)), (0.9, (0, 0.6, 0)), (1.0, (0, -0.4, 0)),
          (1.1, Z), (2.2, Z))

    # stagger: his balance broken, he drops to one knee leaning on the greatsword, the shield sagging (2.5 s)
    a = m.anim("stagger", 2.5)
    a.pos("pelvis", (0, Z), (0.3, (0, -8, 0)), (2.0, (0, -8, 0)), (2.5, Z))
    a.rot("thigh_r", (0, Z), (0.3, (-60, 0, 0)), (2.0, (-60, 0, 0)), (2.5, Z))
    a.rot("shin_r", (0, Z), (0.3, (60, 0, 0)), (2.0, (60, 0, 0)), (2.5, Z))
    a.rot("thigh_l", (0, Z), (0.3, (18, 0, 0)), (2.0, (18, 0, 0)), (2.5, Z))
    a.rot("shin_l", (0, Z), (0.3, (74, 0, 0)), (2.0, (74, 0, 0)), (2.5, Z))
    a.rot("chest", (0, Z), (0.3, (26, 0, 8)), (2.0, (28, 0, 8)), (2.5, Z))
    a.rot("head", (0, Z), (0.3, (22, 0, -10)), (2.0, (24, 0, -10)), (2.5, Z))
    a.rot("arm_r", (0, Z), (0.3, (-20, 0, 6)), (2.0, (-22, 0, 6)), (2.5, Z))
    a.rot("arm_l", (0, Z), (0.3, (6, 0, -10)), (2.0, (8, 0, -10)), (2.5, Z))
    a.rot("cloak", (0, Z), (0.3, (-20, 0, 0)), (2.0, (-20, 0, 0)), (2.5, Z))


def _kneel_pose(a, k, hold, end):
    """One knee down, the other raised, shield planted before him, both hands resting on the greatsword's pommel."""
    Z = (0, 0, 0)

    def key(part, pose, target="rot"):
        ch = a.rot if target == "rot" else a.pos
        ch(part, (0, Z), (k, pose), (hold, pose), (end, Z))

    key("pelvis", (0, -15, 0), "pos")
    key("thigh_r", (-4, 0, 2))
    key("shin_r", (92, 0, 0))
    key("thigh_l", (-86, 0, -6))
    key("shin_l", (86, 0, 0))
    key("chest", (12, 0, 0))
    key("arm_l", (8, 0, 6))
    key("fore_l", (10, 0, 0))
    key("shield", (-14, 6, 0))
    key("arm_r", (-40, 0, -14))
    key("fore_r", (-20, 0, 0))
    key("sword", (90, 0, 10))
    key("cloak", (-6, 0, 0))
    key("cloak_lo", (16, 0, 0))
    key("keychain", (10, 0, 30))
