"""The Swamp Crone (La Grand-Mère du marais): a giant hunched hag, about 3.5 blocks tall (4 with her hat).

Silhouette: bent nearly double under a bubbling iron cauldron strapped to her back, a long crooked nose
and pointed chin jutting from a curtain of wild grey hair, a ragged witch hat whose tip flops sideways, a
gnarled staff taller than she is with a witch-light lantern swinging from its crook. Frog-webbed feet poke
from a ragged robe; bottles, a pouch and a dried frog dangle from her belt; a live frog rides the cauldron.
"""
import math

from ..models import Model
from ..texgen import mix, mul

SKIN = (136, 150, 100)
SKIN_D = (94, 108, 70)
SKIN_L = (172, 182, 128)
WART = (104, 92, 64)
ROBE = (72, 56, 82)
ROBE_D = (44, 34, 54)
ROBE_L = (104, 84, 112)
PATCH = (110, 84, 58)
SHAWL = (86, 106, 58)
SHAWL_D = (56, 72, 38)
SHAWL_L = (118, 140, 76)
HAIR = (200, 200, 190)
HAIR_D = (142, 142, 136)
HAT = (46, 40, 56)
HAT_L = (74, 64, 86)
HAT_D = (30, 26, 36)
LEATHER = (112, 72, 42)
LEATHER_D = (74, 46, 28)
BRASS = (218, 176, 74)
IRON = (54, 54, 60)
IRON_L = (94, 94, 104)
IRON_D = (30, 30, 34)
SOOT = (40, 36, 34)
BREW = (132, 255, 84)
BREW_D = (64, 176, 44)
EYE = (230, 255, 96)
WOOD = (94, 70, 48)
WOOD_D = (60, 44, 30)
WOOD_L = (130, 102, 72)
LIGHT = (214, 255, 140)
FROG = (96, 150, 58)
FROG_D = (62, 104, 40)
BELLY = (222, 176, 96)
NAIL = (40, 34, 28)


def _h(*args):
    v = 0x9E3779B1
    for a in args:
        v = ((v ^ (int(a) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        v ^= v >> 13
        v = (v * 0xC2B2AE35) & 0xFFFFFFFF
        v ^= v >> 16
    return (v & 0xFFFF) / 65536.0


FID = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


# ---------------------------------------------------------------------------------------------- painters
def cloth(base=ROBE, dark=ROBE_D, light=ROBE_L, seed=0, hem=0, patches=True, holes=0.0, trim=False):
    """Woven cloth: soft vertical folds, a faint weave, sewn-on patches with stitches, a ragged hem
    (``hem`` rows cut out irregularly) and moth holes."""
    def f(face, x, y, w, h):
        fid = FID[face]
        if face in ("top", "bottom"):
            return mul(dark, 0.9) if face == "bottom" else base
        if hem and y >= h - 1 - int(_h(x, seed, fid) * hem):
            return None
        if holes and _h(x // 2, y // 2, seed, fid, 9) < holes and 2 < y < h - hem - 2:
            return None
        fold = math.sin((x + fid * 3) * 0.75 + seed + 0.6 * math.sin(y * 0.15))
        c = mix(base, light if fold > 0 else dark, min(0.7, abs(fold) * 0.7) if abs(fold) > 0.45 else 0)
        if (x + y) % 2 == 0:
            c = mul(c, 0.96)
        # embroidered hem band: lit borders around a row of faded eye glyphs
        band = h - hem - 7
        if trim and h >= 14 and band <= y <= band + 4:
            if y in (band, band + 4):
                return mix(BRASS, base, 0.55)
            gx, gy = x % 5, y - band - 1
            if (gy == 1 and gx in (1, 3)) or (gy in (0, 2) and gx == 2):
                return mix(BRASS, base, 0.3)
            if gy == 1 and gx == 2:
                return mix(BREW_D, base, 0.2)
            return mul(base, 0.8)
        if y > h - hem - 5 and _h(x, y, seed, 31) < 0.18:
            return (58, 52, 34)                         # mud splatter
        if patches and w >= 6 and h >= 8:
            px = int(_h(seed, fid, 1) * (w - 4))
            py = int(_h(seed, fid, 2) * (h - 6)) + 1
            pw, ph = 3 + int(_h(seed, fid, 3) * 2), 3 + int(_h(seed, fid, 4) * 2)
            if px <= x < px + pw and py <= y < py + ph and _h(seed, fid, 5) < 0.6:
                inner = PATCH if _h(seed, fid, 6) < 0.5 else SHAWL_D
                edge = x in (px, px + pw - 1) or y in (py, py + ph - 1)
                return mix(inner, (220, 210, 170), 0.5) if edge and (x + y) % 2 else inner
        if y >= h - 2 - hem:
            c = mix(c, (52, 60, 34), 0.45)          # hem soaked in bog water
        return c
    return f


def knit(seed=0, fringe=3):
    """Knitted shawl: rows of V stitches, a darker band, a fringe of strands at the bottom."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SHAWL_D
        if face == "top":
            return SHAWL if (x + y) % 2 else SHAWL_L
        if fringe and y >= h - fringe:
            return (SHAWL_D if x % 2 else SHAWL) if (x + seed) % 3 != 2 and y < h - 1 + (x % 2) else None
        # ribbed knit: 2-texel columns, each stitch lit at its top, a darker purl row every 3
        c = SHAWL_L if (x // 2) % 2 == 0 else SHAWL
        if y % 2 == 1:
            c = mix(c, SHAWL_D, 0.35)
        if y % 6 == 5:
            c = SHAWL_D
        if 1 <= y % 8 <= 2 and (y // 8) % 2:
            c = mix((150, 80, 60), c, 0.3)           # a faded red stripe
        return c
    return f


def skin(seed=0, warts=0.03, base=SKIN):
    """Sickly olive skin: mottled, with raised warts (a dark dot with a lit edge) and wrinkle lines."""
    def f(face, x, y, w, h):
        fid = FID[face]
        c = mix(base, SKIN_D, _h(x // 2, y // 2, seed, fid) * 0.35)
        r = _h(x, y, seed, fid, 3)
        if r < warts:
            return WART
        if r < warts * 1.6:
            return SKIN_L
        if face not in ("top", "bottom") and y % 3 == 0 and _h(x // 3, y, seed) < 0.3:
            c = mul(c, 0.86)                         # wrinkles
        return c
    return f


def face_paint(face, x, y, w, h):
    """The crone's face (front): heavy brows, deep sockets with slit eyes, crow's feet, sunken cheeks and a
    lipless mouth with one snag tooth."""
    base = skin(5)(face, x, y, w, h)
    if face != "front":
        return base
    cx = (w - 1) / 2
    ex = abs(x - cx)
    if y == 0 and ex <= 2.5 and x % 2:
        return SKIN_D                                    # furrowed forehead
    if y == 1 and 0.5 <= ex <= 1.5:
        return SKIN_D
    if y == 2 and 0.5 <= ex <= 3.5:
        return SKIN_L if ex > 1 else SKIN_D              # heavy brow ridge, knit in the middle
    if y == 5 and x == 1 or y == 6 and x == 6:
        return WART                                      # warts on the cheeks
    if y == 3 and 0.5 <= ex <= 3.5:
        return (26, 24, 18) if 1 <= ex <= 3 else SKIN_D  # sockets
    if y == 4 and 1 <= ex <= 3:
        return SKIN_D
    if y == 4 and ex == 3.5:
        return mul(SKIN_D, 0.85)                         # crow's feet
    if 5 <= y <= 7 and ex == 3.5:
        return mul(SKIN_D, 0.9)                          # sunken cheeks
    if y == 7 and ex <= 2.5:
        return (40, 26, 24)                              # mouth
    if y == 8 and ex == 1.5 and x < cx:
        return (226, 214, 160)                           # snag tooth
    if y == 8 and ex <= 2.5:
        return SKIN_D
    return base


def face_glow(face, x, y, w, h):
    if face != "front":
        return None
    ex = abs(x - (w - 1) / 2)
    if y == 3 and 1.5 <= ex <= 2.5:
        return EYE
    return None


def hair(seed=0, density=0.85, ln=(0.45, 1.0)):
    """Wild grey hair (planes): long wavy strands, cut out between them and at their ends."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if _h(x, seed, 1) > density:
            return None
        L = h * (ln[0] + (ln[1] - ln[0]) * _h(x, seed, 2))
        if y > L:
            return None
        c = HAIR if (x + int(1.5 * math.sin(y * 0.5 + x))) % 3 else HAIR_D
        if y < 2:
            c = mul(c, 0.8)
        return c
    return f


def felt(seed=0, base=HAT, band_rows=None, patches=True):
    """Hat felt: dark with a soft sheen, stitched patches; ``band_rows`` = (start, end) for a leather band
    with a brass buckle centred on the front face."""
    def f(face, x, y, w, h):
        fid = FID[face]
        if face == "bottom":
            return HAT_D
        c = mix(base, HAT_L, 0.3 * (1 + math.sin(x * 0.7 + y * 0.4 + seed)) / 2)
        if face == "top":
            return c
        if band_rows and band_rows[0] <= y < band_rows[1]:
            if face == "front" and abs(x - (w - 1) / 2) <= 1.5:
                return BRASS if (x + y) % 3 else (150, 110, 40)
            return LEATHER if y == band_rows[0] else LEATHER_D
        if patches and w >= 6 and h >= 5 and _h(seed, fid) < 0.5:
            px, py = int(_h(seed, fid, 1) * (w - 3)), int(_h(seed, fid, 2) * (h - 3))
            if px <= x < px + 3 and py <= y < py + 3:
                return (88, 64, 52) if (x + y) % 2 else (200, 190, 150) if x == px else (88, 64, 52)
        return c
    return f


def brim(seed=0):
    """The hat brim: felt with a ragged, nibbled outer edge (cut out)."""
    fe = felt(seed, patches=False)

    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if edge == 0 and _h(x, y, seed) < 0.45:
                return None
            if edge <= 1 and face == "top":
                return HAT_L if (x + y) % 2 else HAT
            return fe(face, x, y, w, h)
        return None if _h(x, seed, FID[face]) < 0.4 else HAT_D
    return f


def iron(seed=0, drips=True):
    """Cauldron iron: riveted horizontal bands, a lit rim, soot streaks and runs of glowing brew."""
    def f(face, x, y, w, h):
        fid = FID[face]
        if face == "top":
            return IRON_L
        if face == "bottom":
            return IRON_D
        c = mix(IRON, SOOT, _h(x, y // 3, seed, fid) * 0.5)
        if y == 0:
            c = IRON_L
        if y in (2, h - 3):
            c = IRON_D if x % 4 else (150, 150, 160)     # riveted bands
        if drips and _h(x, seed, fid) < 0.22 and y < 2 + int(_h(x, seed, 7) * (h - 3)):
            c = BREW_D                                     # brew run down the side
        return c
    return f


def iron_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if _h(x, seed, FID[face]) < 0.22 and y < 2 + int(_h(x, seed, 7) * (h - 3)):
            return BREW_D if y > 1 else BREW
        return None
    return f


def brew(face, x, y, w, h):
    r = _h(x, y, 99)
    if r < 0.12:
        return (210, 255, 170)
    return BREW if (x // 2 + y // 2) % 3 else mix(BREW, BREW_D, 0.4)


def gnarled(seed=0, runes=False):
    """Staff wood: twisted grain, knots, a few glowing carved runes."""
    def f(face, x, y, w, h):
        fid = FID[face]
        if face in ("top", "bottom"):
            return WOOD_L
        g = (y + x * 3 + int(2 * math.sin(y * 0.3 + seed))) % 7
        c = WOOD_D if g == 0 else WOOD_L if g == 3 else WOOD
        if _h(y // 5, seed, fid) < 0.15 and y % 5 == 2:
            c = WOOD_D                                   # knots
        if runes and y % 9 == 4 and face == "front":
            c = (70, 110, 60)
        return c
    return f


def rune_glow(face, x, y, w, h):
    return LIGHT if face == "front" and y % 9 == 4 else None


def frog_paint(face, x, y, w, h):
    if face == "top":
        return FROG if (x + y) % 3 else FROG_D
    if face == "bottom":
        return BELLY
    if face == "front":
        return BELLY if y >= h - 1 else FROG
    return FROG_D if y == 0 else FROG


def glass(col):
    def f(face, x, y, w, h):
        if face == "top":
            return (120, 90, 60)                          # cork
        return mix(col, (255, 255, 255), 0.35) if x == 0 and y < h - 1 else col
    return f


# ---------------------------------------------------------------------------------------------- builder
def build():
    m = Model("swamp_crone", seed=30, shadow=1.2, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -24, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=(38, 0, 0))
    m.part("head", "torso", pivot=(0, -14, -2), rot=(-40, 0, 0))
    m.part("nose", "head", pivot=(0, -5, -4.5), rot=(18, 0, 6))
    m.part("chin", "head", pivot=(0, 0, -3.5), rot=(-12, 0, 0))
    m.part("hair", "head", pivot=(0, -8, 0))
    m.part("hat", "head", pivot=(0, -8, 0), rot=(-6, 0, 8))
    m.part("brim", "hat", pivot=(0, 0, 0), rot=(9, 0, -4))
    m.part("hat2", "hat", pivot=(0, -7, 0), rot=(-12, 0, 10))
    m.part("hat3", "hat2", pivot=(0, -7, 0), rot=(-18, 0, 24))
    m.part("hat4", "hat3", pivot=(0, -6, 0), rot=(-10, 0, 52))
    m.part("cauldron", "torso", pivot=(0, -7, 5), rot=(-38, 0, 0))
    m.part("bubbles", "cauldron", pivot=(0, -12, 7))
    m.part("frog", "cauldron", pivot=(5.5, -13, 3), rot=(0, -30, 0))
    m.part("arm_r", "torso", pivot=(-7, -12, -1), rot=(-44, 0, 34))
    m.part("forearm_r", "arm_r", pivot=(0, 11, 0), rot=(-30, 0, 0))
    m.part("hand_r", "forearm_r", pivot=(0, 11, 0))
    m.part("staff", "hand_r", pivot=(0, 2, 0), rot=(36, 0, -30))
    m.part("lantern", "staff", pivot=(-7, -49, 0))
    m.part("arm_l", "torso", pivot=(7, -12, -1), rot=(-50, 0, -12))
    m.part("forearm_l", "arm_l", pivot=(0, 11, 0), rot=(-38, 0, 0))
    m.part("hand_l", "forearm_l", pivot=(0, 11, 0))
    m.part("charms", "hips", pivot=(0, -1, 0))
    m.part("leg_r", "hips", pivot=(-3.5, 0, 0))
    m.part("leg_l", "hips", pivot=(3.5, 0, 0))

    # ------------------------------------------------------------------ robe and legs
    m.box("hips", -7, -4, -5, 14, 5, 10, cloth(seed=1, patches=False))
    m.box("hips", -7.5, -2, -5.5, 15, 2, 11, {"*": lambda f, x, y, w, h: LEATHER if y == 0 else LEATHER_D,
                                              "front": lambda f, x, y, w, h: BRASS if 6 <= x <= 8 else LEATHER})
    m.box("skirt", -8, 0, -6, 16, 21, 12, cloth(seed=2, hem=3, holes=0.03, trim=True))
    m.box("skirt", -6, 1, -6.6, 11, 17, 0, cloth(PATCH, LEATHER_D, (140, 110, 80), seed=3, hem=3, patches=False))
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"
        m.box(leg, -1.5, 0, -1.5, 3, 21, 3, skin(10 + sx))
        # frog-webbed foot with three long toes
        m.box(leg, -2.5, 21, -4.5, 5, 3, 6, skin(12 + sx))
        for i, dx in enumerate((-2.5, -0.5, 1.5)):
            m.box(leg, dx, 22, -8.5, 1, 2, 4, skin(14 + i, warts=0))
            m.box(leg, dx, 23, -9, 1, 1, 1, NAIL)

    # charms dangling from the belt: bottles, a pouch, a dried frog on a string
    for i, (x, z, col, hgt) in enumerate(((-6, -6, (90, 200, 120), 4), (-3.5, -6.3, (200, 80, 160), 3),
                                          (5.5, -5.5, (120, 160, 240), 4))):
        m.box("charms", x - 0.5, 0, z, 1, 1, 1, LEATHER_D)
        m.box("charms", x - 1, 1, z - 0.5, 2, hgt, 2, glass(col), glow=glass(col))
    m.box("charms", 6, 0, -1, 3, 5, 4, cloth(LEATHER, LEATHER_D, (150, 100, 60), seed=4, patches=False))
    m.box("charms", -8.5, 0, 1, 0, 4, 1, LEATHER_D)
    m.box("charms", -9.5, 4, 0, 2, 5, 3, frog_paint)

    # ------------------------------------------------------------------ torso, shawl, straps
    m.box("torso", -6, -14, -4, 12, 14, 9, cloth(seed=5))
    m.box("torso", -7.5, -15, -5, 15, 7, 11, knit(6, fringe=3))
    for x in (-5, 3):
        m.box("torso", x, -14, -4.6, 2, 14, 1, {"*": lambda f, x_, y, w, h: LEATHER if x_ == 0 else LEATHER_D,
                                                "front": lambda f, x_, y, w, h: BRASS if y == 8 else LEATHER})

    # ------------------------------------------------------------------ head: face, nose, chin, hair, hat
    m.box("head", -4, -9, -4, 8, 10, 8, {"front": face_paint, "*": skin(20)}, glow={"front": face_glow})
    m.box("nose", -1, -1, -6, 2, 2, 6, skin(21, warts=0.06))
    m.box("nose", -1, 0, -7.5, 2, 3, 2, skin(22, warts=0.0))
    m.box("nose", 0.5, -1.5, -4, 1, 1, 1, WART)
    m.box("chin", -2, 0, -2, 4, 3, 3, skin(23, warts=0.05))
    m.box("hair", -5, -1, 3.8, 10, 20, 0, hair(30))
    m.box("hair", -4.6, -1, -1.5, 0, 17, 6, hair(31))
    m.box("hair", 4.6, -1, -1.5, 0, 18, 6, hair(32))
    m.box("hair", -5.4, 0, 0, 0, 14, 4, hair(33, density=0.9))
    m.box("hair", 5.4, 0, 0, 0, 15, 4, hair(34, density=0.9))
    # wild tufts sticking out sideways
    for i, (x, rz) in enumerate(((-4, 60), (4, -60), (-3, 100), (3, -110))):
        t = m.part(f"tuft{i}", "hair", pivot=(x, 1, 1), rot=(10, 0, rz))
        m.box(t, -2, 0, 0, 4, 8, 0, hair(40 + i, density=0.95, ln=(0.6, 1.0)))
    # hat: ragged brim, a crooked cone in four segments, a band with a buckle, a charm at the tip
    m.box("brim", -11, -1, -11, 22, 1, 22, brim(50))
    m.box("hat", -6, -7, -6, 12, 7, 12, felt(51, band_rows=(4, 6)))
    m.box("hat2", -4.5, -7, -4.5, 9, 8, 9, felt(52))
    m.box("hat3", -3, -6, -3, 6, 7, 6, felt(53))
    m.box("hat4", -2, -6, -2, 4, 7, 4, felt(54, patches=False))
    m.box("hat4", -0.5, -6.5, -0.5, 1, 5, 1, LEATHER_D)
    m.box("hat4", -1, -2, -1, 2, 2, 2, (220, 214, 190))       # a little bone bead

    # ------------------------------------------------------------------ the cauldron on her back
    m.box("cauldron", -7, -11, 0, 14, 11, 14, iron(60), glow=iron_glow(60))
    m.box("cauldron", -8, -13, -1, 16, 2, 16, {"top": None, "*": iron(61, drips=False)})
    m.box("cauldron", -6, -12, 1, 12, 1, 12, brew, glow=brew)
    m.box("cauldron", -5, 0, 2, 10, 2, 10, iron(62, drips=False))
    for x, z in ((-6, 1), (5, 1), (-6, 12), (5, 12)):
        m.box("cauldron", x, 0, z, 1, 3, 1, IRON_D)              # little legs
    m.box("cauldron", -8.5, -9, 6, 1, 2, 3, IRON_L)              # handles
    m.box("cauldron", 7.5, -9, 6, 1, 2, 3, IRON_L)
    lad = m.part("ladle", "cauldron", pivot=(-3, -12, 9), rot=(-20, 0, -25))
    m.box(lad, -0.5, -12, -0.5, 1, 12, 1, gnarled(63))
    m.box(lad, -1.5, -13, -1.5, 3, 1, 3, WOOD_D)
    for i, (x, z) in enumerate(((-2, -1), (2, 1), (0, 3))):
        m.box("bubbles", x - 1, -2, z - 1, 2, 2, 2, brew, glow=brew)
    m.box("frog", -1.5, -2, -2, 3, 2, 4, frog_paint)
    m.box("frog", -1.5, -3, -2.5, 1, 1, 1, (230, 200, 60), glow=(230, 200, 60))
    m.box("frog", 0.5, -3, -2.5, 1, 1, 1, (230, 200, 60), glow=(230, 200, 60))

    # ------------------------------------------------------------------ arms: right holds the staff
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, hand = f"arm_{side}", f"forearm_{side}", f"hand_{side}"
        m.box(arm, -2.5, -1, -2.5, 5, 9, 5, cloth(seed=70 + sx, hem=2, patches=False))
        m.box(arm, -1.5, 0, -1.5, 3, 11, 3, skin(71 + sx))
        m.box(fore, -1.5, 0, -1.5, 3, 11, 3, skin(72 + sx))
        m.box(fore, -2, 0, -2, 4, 2, 4, LEATHER_D)
        m.box(hand, -2, 0, -2, 4, 3, 4, skin(73 + sx))
        for i, dx in enumerate((-1.5, 0, 1.5)):
            f = m.part(f"finger_{side}{i}", hand, pivot=(dx, 3, -1), rot=(-20, 0, (i - 1) * 12))
            m.box(f, -0.5, 0, -0.5, 1, 5, 1, skin(74 + i, warts=0))
            m.box(f, -0.5, 5, -0.5, 1, 1, 1, NAIL)

    # the staff: gnarled, taller than her, a crook at the top with the witch-light lantern
    m.box("staff", -1, -46, -1, 2, 64, 2, gnarled(80, runes=True), glow={"front": rune_glow})
    m.box("staff", -1.5, -34, -1.5, 3, 3, 3, (226, 216, 190))   # a skull-bead on the shaft
    crook = m.part("crook", "staff", pivot=(0, -45, 0), rot=(0, 0, -60))
    m.box(crook, -1, -7, -1, 2, 7, 2, gnarled(81))
    crook2 = m.part("crook2", crook, pivot=(0, -6, 0), rot=(0, 0, -70))
    m.box(crook2, -1, -5, -1, 2, 5, 2, gnarled(82))
    m.box("lantern", -0.5, 0, -0.5, 1, 3, 1, IRON_D)
    m.box("lantern", -2, 3, -2, 4, 1, 4, IRON)
    m.box("lantern", -1.5, 4, -1.5, 3, 4, 3, LIGHT, glow=LIGHT)
    m.box("lantern", -2, 8, -2, 4, 1, 4, IRON)
    for x, z in ((-2, -2), (1, -2), (-2, 1), (1, 1)):
        m.box("lantern", x, 4, z, 1, 4, 1, IRON_D)

    _animate(m)
    return m


def _animate(m):
    Z = (0, 0, 0)
    ONE = (1, 1, 1)

    idle = m.anim("idle", 3.2)
    idle.rot("torso", (0, Z), (1.6, (4, 0, 0)), (3.2, Z))
    idle.rot("head", (0, Z), (0.8, (-4, 6, 0)), (2.0, (3, -5, 0)), (3.2, Z))
    idle.rot("hair", (0, Z), (1.6, (6, 0, 3)), (3.2, Z))
    idle.rot("hat4", (0, Z), (1.0, (0, 0, 10)), (2.2, (0, 0, -6)), (3.2, Z))
    idle.rot("hat3", (0, Z), (1.6, (0, 0, 5)), (3.2, Z))
    idle.rot("lantern", (0, Z), (0.8, (0, 0, 12)), (2.4, (0, 0, -12)), (3.2, Z))
    idle.rot("frog", (0, Z), (2.0, Z), (2.2, (0, 40, 0)), (2.9, (0, 40, 0)), (3.2, Z))
    idle.pos("frog", (0, Z), (2.0, Z), (2.1, (0, 1.5, 0)), (2.2, Z), (3.2, Z))
    for i, (part, dt) in enumerate((("bubbles", 0.0),)):
        idle.pos(part, (0, Z), (0.8, (0, 1.5, 0)), (1.6, (0, 0, 0)), (2.4, (0, 2, 0)), (3.2, Z))
        idle.scale(part, (0, ONE), (0.8, (1.3, 1.3, 1.3)), (1.6, (0.8, 0.8, 0.8)), (2.4, (1.2, 1.2, 1.2)), (3.2, ONE))
    idle.rot("arm_l", (0, Z), (1.6, (-6, 0, -4)), (3.2, Z))
    for i in range(3):
        idle.rot(f"finger_l{i}", (0, Z), (0.4 + i * 0.3, (-25, 0, 0)), (1.2 + i * 0.3, Z), (3.2, Z))

    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.8, (-22, 0, 0)), (1.6, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.8, (22, 0, 0)), (1.6, (-22, 0, 0)))
    walk.rot("skirt", (0, (0, 0, 3)), (0.8, (0, 0, -3)), (1.6, (0, 0, 3)))
    walk.rot("torso", (0, (0, 4, 0)), (0.8, (0, -4, 0)), (1.6, (0, 4, 0)))
    walk.rot("arm_r", (0, (-8, 0, 0)), (0.8, (8, 0, 0)), (1.6, (-8, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, 0)), (0.8, (-10, 0, 0)), (1.6, (10, 0, 0)))
    walk.pos("bone", (0, Z), (0.4, (0, 1, 0)), (0.8, Z), (1.2, (0, 1, 0)), (1.6, Z))
    walk.rot("cauldron", (0, (0, 0, -3)), (0.8, (0, 0, 3)), (1.6, (0, 0, -3)))

    # throw: reaches back over her shoulder into the cauldron (0.5 s), hurls a potion overarm (0.65 s)
    a = m.anim("throw", 1.4)
    a.rot("arm_l", (0, Z), (0.45, (-150, 0, 40)), (0.5, (-160, 0, 30)), (0.65, (-40, 0, -10), "linear"),
          (0.85, (-30, 0, -10)), (1.4, Z))
    a.rot("forearm_l", (0, Z), (0.45, (-60, 0, 0)), (0.65, (0, 0, 0), "linear"), (1.4, Z))
    a.rot("torso", (0, Z), (0.45, (-10, -25, 0)), (0.65, (8, 20, 0), "linear"), (0.85, (8, 18, 0)), (1.4, Z))
    a.rot("head", (0, Z), (0.45, (0, 20, 0)), (0.65, (6, -10, 0)), (1.4, Z))

    # swipe: the staff drawn far back to her right (0.5 s), a wide swing across (0.65 s)
    a = m.anim("swipe", 1.3)
    a.rot("torso", (0, Z), (0.5, (-6, 45, 0)), (0.65, (6, -50, 0), "linear"), (0.8, (6, -48, 0)), (1.3, Z))
    a.rot("arm_r", (0, Z), (0.5, (-20, 40, 50)), (0.65, (-40, -40, -10), "linear"), (0.8, (-40, -40, -10)), (1.3, Z))
    a.rot("staff", (0, Z), (0.5, (-40, 0, 0)), (0.65, (-60, 0, 0), "linear"), (1.3, Z))
    a.rot("head", (0, Z), (0.5, (0, -20, 0)), (0.65, (0, 15, 0)), (1.3, Z))

    # hex: raises the lantern high toward the target (0.7 s), thrusts it forward (0.8 s): the mark is laid
    a = m.anim("hex", 1.6)
    a.rot("arm_r", (0, Z), (0.7, (-60, 0, 20)), (0.8, (-20, 0, 0), "linear"), (1.1, (-20, 0, 0)), (1.6, Z))
    a.rot("staff", (0, Z), (0.7, (-30, 0, 0)), (0.8, (10, 0, 0), "linear"), (1.1, (10, 0, 0)), (1.6, Z))
    a.scale("lantern", (0, ONE), (0.7, (1.6, 1.6, 1.6)), (0.8, (1.2, 1.2, 1.2)), (1.1, (1.2, 1.2, 1.2)), (1.6, ONE))
    a.rot("torso", (0, Z), (0.7, (-12, 0, 0)), (0.8, (6, 0, 0), "linear"), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.7, (-40, 0, -40)), (1.1, (-40, 0, -40)), (1.6, Z))
    a.rot("head", (0, Z), (0.7, (-10, 0, 0)), (0.8, (4, 0, 0)), (1.6, Z))

    # summon: bows deep (0.75 s) and tips the cauldron over her head (0.9 s): slimes pour out
    a = m.anim("summon", 1.8)
    a.rot("torso", (0, Z), (0.75, (30, 0, 0)), (0.9, (50, 0, 0), "linear"), (1.3, (48, 0, 0)), (1.8, Z))
    a.rot("cauldron", (0, Z), (0.75, (20, 0, 0)), (0.9, (40, 0, 0), "linear"), (1.3, (38, 0, 0)), (1.8, Z))
    a.rot("head", (0, Z), (0.75, (-30, 0, 0)), (1.3, (-30, 0, 0)), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.75, (-30, 0, -50)), (1.3, (-30, 0, -50)), (1.8, Z))
    a.scale("bubbles", (0, ONE), (0.75, (2, 2, 2)), (0.9, (2.5, 2.5, 2.5)), (1.3, ONE), (1.8, ONE))

    # hop: a frog crouch (0.6 s), leap (0.7 s), airborne, lands heavily (1.05 s), straightens
    a = m.anim("hop", 1.6)
    a.pos("bone", (0, Z), (0.6, (0, -5, 0)), (0.7, (0, 2, 0), "linear"), (0.9, (0, 10, -4)),
          (1.05, (0, -4, -6), "linear"), (1.3, (0, -4, -6)), (1.6, Z))
    a.rot("leg_r", (0, Z), (0.6, (-40, 0, 0)), (0.7, (20, 0, 0), "linear"), (1.05, (-30, 0, 0)), (1.6, Z))
    a.rot("leg_l", (0, Z), (0.6, (-40, 0, 0)), (0.7, (20, 0, 0), "linear"), (1.05, (-30, 0, 0)), (1.6, Z))
    a.rot("torso", (0, Z), (0.6, (16, 0, 0)), (0.7, (-14, 0, 0), "linear"), (1.05, (22, 0, 0), "linear"), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.6, (30, 0, -20)), (0.9, (-90, 0, -50)), (1.05, (-20, 0, -20)), (1.6, Z))
    a.rot("arm_r", (0, Z), (0.6, (20, 0, 10)), (0.9, (-40, 0, 30)), (1.05, (0, 0, 0)), (1.6, Z))

    # erupt: staff and claw raised high, the cauldron boils over (0.75 s), the staff strikes the mud (0.9 s)
    a = m.anim("erupt", 2.0)
    a.rot("arm_r", (0, Z), (0.75, (-90, 0, 20)), (0.9, (10, 0, 0), "linear"), (1.3, (10, 0, 0)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.75, (-120, 0, -40)), (0.9, (-20, 0, -20), "linear"), (2.0, Z))
    a.rot("torso", (0, Z), (0.75, (-20, 0, 0)), (0.9, (14, 0, 0), "linear"), (1.3, (12, 0, 0)), (2.0, Z))
    a.rot("cauldron", (0, Z), (0.3, (0, 0, 6)), (0.4, (0, 0, -6)), (0.5, (0, 0, 6)), (0.6, (0, 0, -6)),
          (0.75, Z), (0.9, (10, 0, 0)), (2.0, Z))
    a.scale("bubbles", (0, ONE), (0.75, (2.4, 2.4, 2.4)), (1.2, (2.0, 2.0, 2.0)), (2.0, ONE))
    a.rot("head", (0, Z), (0.75, (-30, 0, 0)), (0.9, (5, 0, 0)), (2.0, Z))

    # dash: mounts the staff like a broom (0.75 s), streaks forward (0.75-1.15 s), hops off
    a = m.anim("dash", 1.8)
    a.rot("arm_r", (0, Z), (0.75, (14, 0, -30)), (1.15, (14, 0, -30)), (1.5, Z), (1.8, Z))
    a.rot("forearm_r", (0, Z), (0.75, (20, 0, 0)), (1.15, (20, 0, 0)), (1.5, Z), (1.8, Z))
    a.rot("staff", (0, Z), (0.75, (30, 0, 34)), (1.15, (30, 0, 34)), (1.5, Z), (1.8, Z))
    a.rot("torso", (0, Z), (0.75, (18, 0, 0)), (1.15, (22, 0, 0)), (1.5, Z), (1.8, Z))
    a.pos("bone", (0, Z), (0.75, (0, 5, 0)), (0.85, (0, 6, -2), "linear"), (1.15, (0, 6, -2)), (1.5, Z), (1.8, Z))
    a.rot("leg_r", (0, Z), (0.75, (-30, 0, 0)), (1.15, (-30, 0, 0)), (1.5, Z), (1.8, Z))
    a.rot("leg_l", (0, Z), (0.75, (20, 0, 0)), (1.15, (20, 0, 0)), (1.5, Z), (1.8, Z))
    a.rot("hair", (0, Z), (0.75, (30, 0, 0)), (1.15, (40, 0, 0)), (1.5, Z), (1.8, Z))
    a.rot("hat", (0, Z), (0.75, (-20, 0, 0)), (1.15, (-25, 0, 0)), (1.5, Z), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.75, (40, 0, -30)), (1.15, (40, 0, -30)), (1.5, Z), (1.8, Z))

    # barrage: two throws, left then a second reach (0.6 s and 1.2 s)
    a = m.anim("barrage", 2.0)
    a.rot("arm_l", (0, Z), (0.45, (-160, 0, 30)), (0.6, (-40, 0, -10), "linear"), (1.0, (-160, 0, 30)),
          (1.2, (-30, 0, 10), "linear"), (1.5, (-30, 0, 10)), (2.0, Z))
    a.rot("forearm_l", (0, Z), (0.45, (-60, 0, 0)), (0.6, Z, "linear"), (1.0, (-60, 0, 0)), (1.2, Z, "linear"),
          (2.0, Z))
    a.rot("torso", (0, Z), (0.45, (-10, -25, 0)), (0.6, (8, 18, 0), "linear"), (1.0, (-10, -20, 0)),
          (1.2, (10, 24, 0), "linear"), (1.5, (8, 20, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.45, (0, 20, 0)), (0.6, (0, -10, 0)), (1.0, (0, 20, 0)), (1.2, (0, -10, 0)), (2.0, Z))

    # roar: a shrieking cackle: head thrown back, arms and staff flung up, the hat flops
    a = m.anim("roar", 2.4)
    a.rot("torso", (0, Z), (0.4, (-30, 0, 0)), (2.0, (-30, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.4, (-30, 0, 0)), (0.6, (-36, 0, 6)), (0.8, (-30, 0, -6)), (1.0, (-36, 0, 6)),
          (1.2, (-30, 0, -6)), (1.4, (-36, 0, 6)), (2.0, (-30, 0, 0)), (2.4, Z))
    a.rot("arm_r", (0, Z), (0.4, (-100, 0, 30)), (2.0, (-100, 0, 30)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.4, (-120, 0, -50)), (2.0, (-120, 0, -50)), (2.4, Z))
    a.rot("hat4", (0, Z), (0.6, (0, 0, 30)), (1.2, (0, 0, -20)), (2.0, (0, 0, 20)), (2.4, Z))
    a.scale("lantern", (0, ONE), (0.4, (1.5, 1.5, 1.5)), (2.0, (1.5, 1.5, 1.5)), (2.4, ONE))
    a.scale("bubbles", (0, ONE), (0.4, (2.2, 2.2, 2.2)), (2.0, (2.2, 2.2, 2.2)), (2.4, ONE))

    # stagger: knees buckle, the cauldron lurches, the hat slips over her face
    a = m.anim("stagger", 2.0)
    a.pos("bone", (0, Z), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.3, (-60, 0, 0)), (1.6, (-60, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (0.3, (-40, 0, 0)), (1.6, (-40, 0, 0)), (2.0, Z))
    a.rot("torso", (0, Z), (0.3, (20, 0, 12)), (1.6, (20, 0, 12)), (2.0, Z))
    a.rot("cauldron", (0, Z), (0.3, (0, 0, -18)), (1.6, (0, 0, -18)), (2.0, Z))
    a.rot("hat", (0, Z), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, Z))
    a.rot("arm_r", (0, Z), (0.3, (30, 0, 10)), (1.6, (30, 0, 10)), (2.0, Z))
