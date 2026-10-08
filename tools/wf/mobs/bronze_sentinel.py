"""The Bronze Sentinel (La Sentinelle d'airain): the living guardian of the Fallen Colossus, about 5.6 blocks tall.

Silhouette idea: a knight automaton of stone under bronze plate, the statue's own guard come alive. Oxidised
verdigris streaks run down the plates, moss grows in every joint, the cross-visor great helm is broken at one corner
and glows gold from inside. Strong asymmetry: a great tower shield (taller than a man) on the LEFT arm, a long
greatsword in the RIGHT hand whose point rests on the ground in front of him; a torn mossy tabard hangs between the
legs and the helm's crest is snapped off at the back.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

BRONZE = (150, 104, 56)
BRONZE_L = (204, 156, 92)
BRONZE_D = (96, 62, 34)
VERD = (86, 168, 146)
VERD_L = (140, 212, 186)
VERD_D = (50, 116, 100)
STONE = (128, 126, 118)
STONE_L = (164, 162, 152)
STONE_D = (86, 84, 78)
MOSS = (82, 122, 44)
MOSS_L = (122, 160, 62)
MOSS_D = (50, 84, 30)
GOLD = (255, 204, 86)
GOLD_L = (255, 240, 176)
GOLD_D = (214, 150, 40)
CLOTH = (70, 92, 52)


def verd_plate(seed=0, verd=0.45, rivets=True):
    """A bronze plate gone green: a lit bronze top edge, darker rim, verdigris streaks running down from the top
    (more green lower down and in the streak columns), rivets at the corners."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(BRONZE_D, 0.8)
        if face == "top":
            if B.n(x, y, seed + 3) < verd * 0.45:
                return VERD_L if B.n(x, y, seed) < 0.3 else VERD
            return mul(BRONZE, 1.1)
        if w > 2 and h > 2:
            if y == 0:
                return BRONZE_L
            if x == 0 or x == w - 1 or y == h - 1:
                return BRONZE_D if B.n(x, y, seed) > verd else VERD_D
        if rivets and w > 4 and h > 4 and y in (1, h - 2) and x in (1, w - 2):
            return mix(BRONZE_L, (255, 240, 200), 0.3)
        col = B.n(x, 0, seed + 11)                  # streak strength of this column
        streak = col < 0.22 and B.n(x, y // 3, seed + 13) < 0.8
        g = verd * 0.5 * (0.2 + 0.8 * y / max(1, h)) + (0.55 * verd + 0.2 if streak else 0.0)
        if B.n(x, y, seed) < g:
            c = VERD if B.n(x, y, seed + 5) > 0.25 else VERD_L
            return mul(c, 1.0 - 0.15 * y / max(1, h))
        return mul(BRONZE, 1.08 - 0.25 * y / max(1, h) + (B.n(x, y, seed + 9) - 0.5) * 0.08)
    return f


def stone(seed=0, moss=0.15):
    """Weathered grey stone: block joints, cracks, a little moss on the upper faces."""
    def f(face, x, y, w, h):
        if face == "top":
            return MOSS if B.n(x, y, seed) < moss * 2.5 else STONE_L
        if face == "bottom":
            return STONE_D
        if (y % 6 == 5) or (x % 7 == (3 if (y // 6) % 2 else 6)):
            return mul(STONE_D, 0.9)
        if B.n(x, y, seed + 2) < moss * (1.0 - y / max(1, h)):
            return MOSS_L if B.n(x, y, seed) < 0.4 else MOSS
        return mul(STONE, 1.06 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
    return f


def moss(seed=0):
    """A mossy joint: clumps of three greens, dark gaps, a few pale tips."""
    def f(face, x, y, w, h):
        v = B.n(x, y, seed)
        if face == "bottom":
            return MOSS_D
        if v < 0.15:
            return mul(MOSS_D, 0.8)
        if v > 0.85:
            return MOSS_L
        return mul(MOSS, 0.9 + 0.2 * B.n(x // 2, y // 2, seed + 1))
    return f


def tabard(seed=0):
    """A torn mossy tabard: dark green cloth with a faded gold sun, ragged hem (transparent notches)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return mul(CLOTH, 0.8)
        if y >= h - 3 and B.n(x, 0, seed) < 0.35 + 0.2 * (y - (h - 3)):
            return None                                 # ragged hem
        cx = (w - 1) / 2
        if 2 <= y <= 7 and (abs(x - cx) + abs(y - 4.5)) < 3.2:
            return mix(GOLD_D, CLOTH, 0.45)
        if B.n(x, y, seed + 4) < 0.25:
            return MOSS
        return mul(CLOTH, 1.05 - 0.2 * y / h + (B.n(x, y, seed) - 0.5) * 0.1)
    return f


def breast_paint(f, x, y, w, h):
    """The breastplate: verdigris bronze with a raised gold-lit rune band across the chest and a crack."""
    if f != "front":
        return verd_plate(70, verd=0.5)(f, x, y, w, h)
    cx = (w - 1) / 2
    if y in (7, 8) and 3 <= x <= w - 4:
        return GOLD_D if (x % 3) else BRONZE_D               # the rune band
    if abs(x - (cx + 4 - y * 0.35)) < 0.6 and 10 <= y <= 20:
        return mul(STONE_D, 0.6)                             # a crack showing stone
    return verd_plate(71, verd=0.42)(f, x, y, w, h)


def breast_glow(f, x, y, w, h):
    if f == "front" and y in (7, 8) and 3 <= x <= w - 4 and x % 3:
        return GOLD if y == 7 else GOLD_D
    return None


def helm_paint(f, x, y, w, h):
    """Great helm: verdigris bronze, a cross-shaped visor (a horizontal eye slit and a vertical breathing slit),
    broken off at the lower right corner where the gold light spills out."""
    if f == "top":
        return mix(VERD, BRONZE, 0.5) if B.n(x, y, 80) < 0.5 else BRONZE_L
    if f == "bottom":
        return BRONZE_D
    if f == "front":
        cx = w // 2
        if y in (4, 5) and 1 <= x <= w - 2:
            return GOLD if y == 4 else GOLD_D
        if x in (cx - 1, cx) and 4 <= y <= h - 3:
            return GOLD if y < 8 else GOLD_D
        if x <= 2 and y >= h - 4:
            return GOLD_D if (x + y) % 2 else mul(BRONZE_D, 0.6)   # the broken corner
        if y in (3, 6) and 1 <= x <= w - 2:
            return mul(BRONZE_D, 0.7)
    return verd_plate(81, verd=0.5, rivets=False)(f, x, y, w, h)


def helm_glow(f, x, y, w, h):
    if f != "front":
        return None
    cx = w // 2
    if y in (4, 5) and 1 <= x <= w - 2:
        return GOLD_L if y == 4 else GOLD
    if x in (cx - 1, cx) and 4 <= y <= h - 3:
        return GOLD_L if y < 8 else GOLD
    if x <= 2 and y >= h - 4 and (x + y) % 2:
        return GOLD
    return None


def shield_paint(f, x, y, w, h):
    """The tower shield face: a thick bronze rim, verdigris field, a gold-lit sun boss with rays, cracks."""
    if f != "front":
        if f == "back":
            return stone(90, moss=0.05)(f, x, y, w, h)
        return verd_plate(91, verd=0.3, rivets=False)(f, x, y, w, h)
    if x in (0, w - 1) or y in (0, h - 1):
        return BRONZE_L if y == 0 else BRONZE_D
    if x in (1, w - 2) or y in (1, h - 2):
        return BRONZE
    cx, cy = (w - 1) / 2, h * 0.42
    d = ((x - cx) ** 2 + ((y - cy) * 0.9) ** 2) ** 0.5
    if d < 2.2:
        return GOLD_L if d < 1.2 else GOLD
    if d < 3.6:
        return BRONZE_L
    if (abs(x - cx) < 0.6 or abs(y - cy) < 0.6) and d < 7.5:
        return GOLD_D                                          # the rays
    if abs(x - (cx - 5 + (y - cy) * 0.25)) < 0.6 and y > cy + 4:
        return mul(STONE_D, 0.6)                               # a long crack
    if y % 9 == 4 and (x == 2 or x == w - 3):
        return mix(BRONZE_L, (255, 240, 200), 0.3)             # rivets down the rim
    return verd_plate(92, verd=0.55, rivets=False)(f, x, y, w, h)


def shield_glow(f, x, y, w, h):
    if f != "front":
        return None
    cx, cy = (w - 1) / 2, h * 0.42
    d = ((x - cx) ** 2 + ((y - cy) * 0.9) ** 2) ** 0.5
    if d < 2.2:
        return GOLD_L if d < 1.2 else GOLD
    if (abs(x - cx) < 0.6 or abs(y - cy) < 0.6) and 3.6 <= d < 7.5:
        return GOLD_D
    return None


def blade_paint(f, x, y, w, h):
    """The greatsword blade: pale bronze edges, a darker fuller with gold runes, green tarnish near the guard."""
    if f in ("top", "bottom"):
        return BRONZE_L
    if f in ("left", "right"):
        return mix(BRONZE_L, (255, 250, 230), 0.4)
    if x in (0, w - 1):
        return mix(BRONZE_L, (255, 250, 230), 0.35)
    if x == w // 2 and y % 4 == 1 and y < h - 4:
        return GOLD
    if x == w // 2:
        return BRONZE_D
    if y < 8 and B.n(x, y, 95) < 0.5 - y * 0.05:
        return VERD
    return mul(BRONZE, 1.15 - 0.1 * y / h)


def blade_glow(f, x, y, w, h):
    if f in ("front", "back") and x == w // 2 and y % 4 == 1 and y < h - 4:
        return GOLD
    return None


def build():
    m = Model("bronze_sentinel", seed=131, shadow=2.2, walk_speed=0.6, walk_scale=0.85)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -38, 0))
    m.part("tabard", "pelvis", pivot=(0, 2, -7))
    m.part("tabard_b", "pelvis", pivot=(0, 2, 6))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0), rot=(4, 0, 0))
    m.part("head", "chest", pivot=(0, -23, -1), rot=(-4, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(6.5 * sx, 0, 0), rot=(0, 0, -3 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 18, 0), rot=(0, 0, 3 * sx))
    m.part("arm_r", "chest", pivot=(-15, -19, 0), rot=(-6, 0, 6))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-26, 0, 0))
    m.part("sword", "fore_r", pivot=(0, 14, -0.5), rot=(-10, 0, -4))
    m.part("arm_l", "chest", pivot=(15, -19, 0), rot=(-8, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-62, 0, 6))
    m.part("shield", "fore_l", pivot=(3, 8, -2), rot=(68, -6, 0))

    # ---- legs: stone thighs under cuisses, verdigris greaves, mossy knees, broad bronze sabatons
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -4.5, -2, -4.5, 9, 18, 9, stone(2 + (sx > 0)))
        m.box(th, -5, 1, -5.5, 10, 12, 3, verd_plate(4 + (sx > 0)))                 # cuisse
        m.box(th, -5.5 if sx < 0 else 3.5, 2, -4, 2, 10, 8, verd_plate(6))          # outer plate
        m.box(sh, -5, -1, -5, 10, 3, 10, moss(8 + (sx > 0)))                         # moss in the knee
        m.box(sh, -5, -3, -7, 10, 6, 3, verd_plate(10, verd=0.6))                    # poleyn
        m.box(sh, -2, -4, -7.5, 4, 3, 1, B.plate(BRONZE_L, BRONZE_D, seed=12))       # its spike
        m.box(sh, -4.5, 2, -5, 9, 13, 10, verd_plate(13 + (sx > 0), verd=0.55))      # greave
        m.box(sh, -6, 15, -8, 12, 5, 13, verd_plate(15, verd=0.35))                  # sabaton
        m.box(sh, -5, 17, -9, 10, 3, 1, B.plate(BRONZE_L, BRONZE_D, seed=16))        # toe cap

    # ---- pelvis, faulds and the torn tabard
    m.box("pelvis", -10, -4, -6, 20, 7, 12, stone(20))
    m.box("pelvis", -11, 2, -7, 22, 6, 2, B.bands(BRONZE, VERD_D, every=3, seed=21))  # faulds
    m.box("pelvis", -12, 1, -5, 2, 9, 10, verd_plate(22))                           # tassets
    m.box("pelvis", 10, 1, -5, 2, 9, 10, verd_plate(23))
    m.box("pelvis", -10, 1, 5, 20, 6, 2, B.bands(BRONZE, VERD_D, every=3, seed=24))
    m.box("tabard", -5, 0, -1, 10, 20, 1, tabard(25))
    m.box("tabard_b", -6, 0, 0, 12, 22, 1, tabard(26))

    # ---- the waist: a mossy joint under a bronze belt
    m.box("waist", -9, -6, -6, 18, 6, 12, moss(30))
    m.box("waist", -10, -3, -6.5, 20, 3, 13, B.plate(BRONZE, BRONZE_D, BRONZE_L, seed=31))
    m.box("waist", -2, -4, -7.2, 4, 4, 1, B.plate(GOLD_D, BRONZE_D, seed=32))       # buckle

    # ---- chest: breastplate with the gold rune band, back plate, gorget, moss on the shoulders
    m.box("chest", -12, -22, -8, 24, 22, 15, breast_paint, glow=breast_glow)
    m.box("chest", -1, -21, -9, 2, 19, 1, B.plate(BRONZE_L, BRONZE_D, seed=33))     # ridge
    m.box("chest", -10, -20, 7, 20, 17, 2, verd_plate(34, verd=0.6))                # back plate
    m.box("chest", -2, -24, 7, 4, 22, 3, stone(35, moss=0.4))                       # stone spine
    m.box("chest", -8, -25, -7, 16, 4, 13, verd_plate(36, verd=0.5))                # gorget
    m.box("chest", -13, -23, -6, 26, 2, 12, moss(37))                              # moss on the yoke

    # ---- head: great helm with the broken cross visor, snapped crest
    m.box("head", -6, -13, -6, 12, 13, 12, helm_paint, glow=helm_glow)
    m.box("head", -6.5, -9, -6.5, 13, 1, 13, B.plate(BRONZE_D, mul(BRONZE_D, 0.6), BRONZE, seed=40))  # brow band
    m.box("head", -1, -17, -6, 2, 4, 8, B.plate(BRONZE_L, BRONZE_D, seed=41))      # crest (snapped behind)
    m.box("head", -1, -15, 2, 2, 2, 2, mul(STONE_D, 0.8))                          # the stump
    m.box("head", 6, -6, -2, 1, 3, 3, moss(42))                                    # moss in the hinge
    m.box("head", -7, -6, -2, 1, 3, 3, moss(43))

    # ---- right arm: layered pauldron, stone arm, mossy elbow, vambrace and gauntlet
    m.box("arm_r", -8, -6, -7, 12, 8, 14, verd_plate(45, verd=0.5))
    m.box("arm_r", -8.5, 1, -7.5, 11, 3, 15, verd_plate(46, verd=0.4))
    m.box("arm_r", -7, -7, -5, 8, 1, 10, moss(47))
    m.box("arm_r", -4, 2, -4, 8, 10, 8, stone(48))
    m.box("arm_r", -4.5, 11, -4.5, 9, 3, 9, moss(49))
    m.box("fore_r", -4.5, 0, -4.5, 9, 11, 9, verd_plate(50, verd=0.5))
    m.box("fore_r", -4, 11, -4.5, 8, 5, 8, B.plate(BRONZE, BRONZE_D, BRONZE_L, seed=51))
    # the greatsword: pommel and grip above the fist, a wide crossguard, a 40-pixel blade
    m.box("sword", -1.5, -7, -1.5, 3, 3, 3, B.plate(GOLD_D, BRONZE_D, GOLD, seed=52))
    m.box("sword", -1, -4, -1, 2, 7, 2, B.rod(B.LEATHER, 53))
    m.box("sword", -7, 3, -1.5, 14, 2, 3, B.plate(BRONZE_L, BRONZE_D, seed=54))
    m.box("sword", -8, 2, -1, 2, 4, 2, BRONZE_L)
    m.box("sword", 6, 2, -1, 2, 4, 2, BRONZE_L)
    m.box("sword", -2.5, 5, -1, 5, 40, 2, blade_paint, glow=blade_glow)
    m.box("sword", -1.5, 45, -1, 3, 2, 2, mix(BRONZE_L, (255, 250, 230), 0.3))
    m.box("sword", -0.5, 47, -1, 1, 1, 2, mix(BRONZE_L, (255, 250, 230), 0.5))

    # ---- left arm: pauldron, arm, the tower shield
    m.box("arm_l", -4, -6, -7, 12, 8, 14, verd_plate(56, verd=0.55))
    m.box("arm_l", -2.5, 1, -7.5, 11, 3, 15, verd_plate(57, verd=0.45))
    m.box("arm_l", -1, -7, -5, 8, 1, 10, moss(58))
    m.box("arm_l", -4, 2, -4, 8, 10, 8, stone(59))
    m.box("arm_l", -4.5, 11, -4.5, 9, 3, 9, moss(60))
    m.box("fore_l", -4.5, 0, -4.5, 9, 11, 9, verd_plate(61, verd=0.5))
    m.box("fore_l", -4, 11, -4.5, 8, 5, 8, B.plate(BRONZE, BRONZE_D, BRONZE_L, seed=62))
    m.box("shield", -11, -18, -6, 22, 36, 3, shield_paint, glow=shield_glow)
    m.box("shield", -11.5, -19, -5.5, 23, 2, 2, B.plate(BRONZE_L, BRONZE_D, seed=63))   # top rim
    m.box("shield", -3, -4, -3, 6, 8, 3, B.plate(BRONZE_D, mul(BRONZE_D, 0.6), seed=64))  # grip block
    m.box("shield", -10, 14, -6.5, 6, 3, 1, moss(65))                                     # moss on the foot

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.7, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (0, 7, 0)), (2.3, (0, 7, 0)), (3.2, (0, -5, 0)), (4.0, (0, 0, 0)))
    idle.rot("tabard", (0, (0, 0, 0)), (2.0, (-4, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("tabard_b", (0, (0, 0, 0)), (2.0, (4, 0, -2)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-2, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (2, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("thigh_r", (0, (20, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("thigh_l", (0, (-20, 0, 0)), (1.0, (20, 0, 0)), (2.0, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (26, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (26, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("arm_r", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))
    walk.rot("chest", (0, (0, 3, 0)), (1.0, (0, -3, 0)), (2.0, (0, 3, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("tabard", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))

    # bash: the shield drawn in and the shoulder set (0.7 s = 14 ticks), then a lunging shove behind it
    a = m.anim("bash", 1.7)
    a.rot("chest", (0, (0, 0, 0)), (0.6, (10, 30, 0)), (0.7, (12, 32, 0)), (0.8, (14, -18, 0), "linear"),
          (1.1, (12, -16, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (20, 20, 10)), (0.8, (-40, -10, 0), "linear"), (1.1, (-38, -10, 0)),
          (1.7, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.8, (20, 0, 0), "linear"), (1.1, (18, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (20, 0, 10)), (1.1, (10, 0, 6)), (1.7, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.7, (0, -3, 2)), (0.8, (0, -2, -6), "linear"), (1.1, (0, -2, -6)),
          (1.7, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.8, (-34, 0, 0), "linear"), (1.1, (-30, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.8, (24, 0, 0), "linear"), (1.1, (22, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.7, (-16, 0, 0)), (0.8, (24, 0, 0), "linear"), (1.1, (20, 0, 0)), (1.7, (0, 0, 0)))

    # overhead: the greatsword heaved high over the helm (1.1 s = 22 ticks), brought down in front, the ground cracks
    a = m.anim("overhead", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.95, (-168, 0, -14)), (1.1, (-172, 0, -16)), (1.2, (-42, 0, -10), "linear"),
          (1.5, (-44, 0, -10)), (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (10, 0, 0), "linear"), (1.5, (10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (1.1, (30, 0, 0)), (1.2, (-24, 0, 0), "linear"), (1.5, (-22, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-16, 8, 0)), (1.2, (26, -6, 0), "linear"), (1.5, (24, -6, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (10, 0, -16)), (1.5, (6, 0, -12)), (2.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1, 0)), (1.2, (0, -4, 0), "linear"), (1.5, (0, -3.5, 0)), (2.1, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-24, 0, -6 * sx), "linear"),
              (1.5, (-22, 0, -6 * sx)), (2.1, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (36, 0, 0), "linear"), (1.5, (34, 0, 0)),
              (2.1, (0, 0, 0)))

    # cleave: the blade drawn far back to his right (0.8 s = 16 ticks), then swept across the front
    a = m.anim("cleave", 1.65)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-14, -40, 72)), (0.8, (-16, -44, 76)), (0.95, (-86, 56, -14), "linear"),
          (1.2, (-82, 60, -14)), (1.65, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (0.95, (-70, 0, 0), "linear"), (1.2, (-66, 0, 0)), (1.65, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (0, -36, 0)), (0.95, (0, 38, 0), "linear"), (1.2, (0, 40, 0)), (1.65, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, -10, 0)), (0.95, (0, 10, 0), "linear"), (1.65, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-20, 0, -14)), (0.95, (10, 0, -6), "linear"), (1.65, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (12, 0, 4)), (1.65, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (-14, 0, -6)), (1.65, (0, 0, 0)))

    # shieldwall: the tower shield swung in front and planted (0.5 s = 10 ticks), he crouches behind it for 2 s
    a = m.anim("shieldwall", 3.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-26, 0, 12)), (0.5, (-28, 0, 12)), (2.5, (-28, 0, 12)), (3.0, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.5, (8, 0, 0)), (2.5, (8, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("shield", (0, (0, 0, 0)), (0.5, (-8, 4, 0)), (2.5, (-8, 4, 0)), (3.0, (0, 0, 0)))
    a.pos("shield", (0, (0, 0, 0)), (0.5, (-13, 0, 0)), (2.5, (-13, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (2.5, (14, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-30, 0, 14)), (2.5, (-30, 0, 14)), (3.0, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.5, (-50, 0, 0)), (2.5, (-50, 0, 0)), (3.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-8, 0, 0)), (2.5, (-8, 0, 0)), (3.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -4, 0)), (2.5, (0, -4, 0)), (3.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.5, (-24, 0, -8 * sx)), (2.5, (-24, 0, -8 * sx)), (3.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.5, (34, 0, 0)), (2.5, (34, 0, 0)), (3.0, (0, 0, 0)))

    # stomp: the right foot raised high (0.9 s = 18 ticks), driven down; a ring of force rolls out
    a = m.anim("stomp", 1.65)
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (-72, 0, 8)), (0.9, (-76, 0, 8)), (1.0, (-6, 0, 0), "linear"),
          (1.25, (-6, 0, 0)), (1.65, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.9, (64, 0, 0)), (1.0, (8, 0, 0), "linear"), (1.25, (8, 0, 0)), (1.65, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (6, 0, 0)), (1.0, (-10, 0, 0), "linear"), (1.65, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, 0, -6)), (1.0, (18, 0, 0), "linear"), (1.25, (16, 0, 0)), (1.65, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-30, 0, 30)), (1.0, (10, 0, 10), "linear"), (1.65, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-20, 0, -30)), (1.0, (6, 0, -10), "linear"), (1.65, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, 2, 0)), (1.0, (0, -3, 0), "linear"), (1.25, (0, -2.5, 0)), (1.65, (0, 0, 0)))

    # dance (phase 2): blade held out to the side (0.6 s = 12 ticks), then three whirling turns while he advances
    a = m.anim("dance", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-10, 0, 80)), (0.6, (-10, 0, 84)), (2.4, (-10, 0, 84)), (3.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.6, (26, 0, 0)), (2.4, (26, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.6, (-6, 0, 0)), (2.4, (-6, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-6, 0, -24)), (2.4, (-6, 0, -24)), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (6, -24, 0)), (0.7, (6, 0, 0)), (2.4, (6, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("bone", (0, (0, 0, 0), "linear"), (0.6, (0, 0, 0), "linear"), (2.4, (0, -1080, 0), "linear"),
          (3.1, (0, -1080, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.6, (0, -2, 0)), (2.4, (0, -2, 0)), (3.1, (0, 0, 0)))

    # topple (phase 2): he crouches and raises the blade (1.0 s = 20 ticks), leaps, topples forward through the air
    # and lands sword-first on the marked circle (1 s of flight), then stays bent over his blade
    a = m.anim("topple", 2.9)
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, -6, 0)), (1.0, (0, -6, 0)), (1.15, (0, 2, 0), "linear"), (1.9, (0, 0, 0)),
          (2.0, (0, -6, 0), "linear"), (2.5, (0, -5, 0)), (2.9, (0, 0, 0)))
    a.rot("bone", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (-14, 0, 0)), (1.9, (-30, 0, 0)), (2.0, (-12, 0, 0), "linear"),
          (2.5, (-10, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-150, 0, -10)), (1.0, (-155, 0, -10)), (1.9, (-175, 0, -14)),
          (2.0, (-50, 0, -8), "linear"), (2.5, (-48, 0, -8)), (2.9, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (1.9, (30, 0, 0)), (2.0, (-20, 0, 0), "linear"), (2.5, (-20, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (20, 0, -20)), (1.9, (-20, 0, -30)), (2.0, (0, 0, -10), "linear"),
          (2.9, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.0, (-40, 0, -8 * sx)), (1.15, (20, 0, -4 * sx), "linear"),
              (1.9, (-30, 0, -6 * sx)), (2.0, (-36, 0, -8 * sx), "linear"), (2.5, (-34, 0, -8 * sx)), (2.9, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.0, (60, 0, 0)), (1.15, (10, 0, 0), "linear"), (1.9, (40, 0, 0)),
              (2.0, (50, 0, 0), "linear"), (2.5, (48, 0, 0)), (2.9, (0, 0, 0)))

    # beams (phase 2): the blade lifted point-up to the sky (1.0 s = 20 ticks), then driven into the floor as he
    # kneels; rune light runs out across the arena while he holds it there
    a = m.anim("beams", 4.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-170, 0, 6)), (1.0, (-172, 0, 6)), (1.1, (-70, 0, 6), "linear"),
          (3.5, (-70, 0, 6)), (4.2, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (26, 0, 0)), (1.1, (-10, 0, 0), "linear"), (3.5, (-10, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (1.0, (180, 0, 0)), (1.05, (90, 0, 0), "linear"), (1.1, (-14, 0, 0), "linear"),
          (3.5, (-14, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.1, (14, 0, 0), "linear"), (3.5, (14, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.1, (22, 0, 0), "linear"), (3.5, (22, 0, 0)), (4.2, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (0, -7, 0), "linear"), (3.5, (0, -7, 0)), (4.2, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.1, (-60, 0, 0), "linear"), (3.5, (-60, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.1, (60, 0, 0), "linear"), (3.5, (60, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.1, (18, 0, 0), "linear"), (3.5, (18, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.1, (72, 0, 0), "linear"), (3.5, (72, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (10, 0, -14)), (3.5, (10, 0, -14)), (4.2, (0, 0, 0)))

    # roar (phase two): sword and shield flung wide, the helm thrown back, plates shaken loose
    a = m.anim("roar", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-60, 0, 60)), (1.8, (-64, 0, 64)), (2.2, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.6, (60, 0, 0)), (1.8, (60, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-10, 0, -36)), (1.8, (-12, 0, -40)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-32, 0, 0)), (1.0, (-28, 6, 0)), (1.4, (-30, -6, 0)), (1.8, (-30, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (1.8, (-14, 0, 0)), (2.2, (0, 0, 0)))
    a.pos("chest", (0, (0, 0, 0)), (0.7, (0, 0.6, 0)), (0.8, (0, -0.4, 0)), (0.9, (0, 0.6, 0)), (1.0, (0, -0.4, 0)),
          (1.1, (0, 0, 0)), (2.2, (0, 0, 0)))

    # stagger: his balance broken, he drops to one knee leaning on the greatsword, the shield sagging
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -7, 0)), (1.2, (0, -7, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (1.2, (-60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.2, (60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (18, 0, 0)), (1.2, (18, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (72, 0, 0)), (1.2, (72, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 8)), (1.2, (28, 0, 8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (22, 0, -10)), (1.2, (24, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 6)), (1.2, (-22, 0, 6)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (6, 0, -10)), (1.2, (8, 0, -10)), (1.6, (0, 0, 0)))
