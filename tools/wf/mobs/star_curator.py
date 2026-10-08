"""The Star-Eater Curator (Le Conservateur dévoreur d'étoiles): the keeper of the Starfall Library, about 5.6 blocks.

Silhouette idea: a hooded scholar whose head is the falling star that wrecked his library. A very tall, narrow figure
in a floor-length robe of deep indigo velvet, its hem flared and torn, brass trim and constellations embroidered in
glowing thread down the front; a stiff brass-edged mantle over the shoulders and a tall standing collar behind the
head. In place of a head, a cracked, charred meteorite: the crust has split open across the face and through the
cracks you look into a starfield (a little nebula, two brighter stars where eyes would be); a broken chip of rock
floats beside it with a ring of glowing motes. Five books orbit him at chest height. Asymmetry: his RIGHT hand holds
a tall astrolabe staff (a brass shaft, an astrolabe disc at its head inside two armillary hoops that turn round a
white star); his LEFT hand is raised palm-up, a page curling off it.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

ROBE = (46, 34, 84)            # indigo velvet
ROBE_L = (78, 62, 128)
ROBE_D = (26, 18, 50)
ROBE_DD = (16, 10, 32)
PURP = (160, 104, 168)         # purpur lining
PURP_L = (206, 160, 210)
PURP_D = (104, 62, 116)
GOLD = (214, 172, 80)
GOLD_L = (250, 222, 140)
GOLD_D = (140, 104, 44)
CRUST = (52, 44, 48)           # charred meteorite crust
CRUST_L = (96, 86, 88)
CRUST_D = (28, 24, 28)
IRONM = (120, 104, 98)         # meteoric iron glints
EMBER = (226, 120, 60)         # the still-hot rim of a crack
SPACE = (12, 8, 30)            # the starfield inside
NEBULA = (92, 46, 150)
NEBULA_L = (170, 96, 214)
STAR = (255, 252, 230)
STAR_B = (190, 220, 255)
PAGE = (232, 218, 186)
PAGE_D = (186, 168, 132)
INK = (40, 32, 30)
COVERS = ((128, 40, 52), (38, 98, 110), (108, 70, 40), (88, 50, 122), (48, 92, 60))


# ---------------------------------------------------------------- paint
def robe(seed=0, embroider=True, ragged=0):
    """Indigo velvet: soft vertical folds, darker toward the hem, a brass trim row at the bottom, constellations
    stitched in glowing thread (the glow layer is robe_glow with the same seed)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return ROBE_DD
        if face == "top":
            return ROBE_L if (x + y) % 4 == 0 else ROBE
        if ragged:
            cut = h - 1 - int(B.n(x // 2, 0, seed) * ragged)
            if y > cut:
                return None
            if y == cut:
                return GOLD_D
        fold = (x + int(B.n(x // 3, 1, seed) * 2)) % 5
        c = (ROBE_L, ROBE, ROBE, ROBE_D, ROBE)[fold]
        c = mul(c, 1.06 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if not ragged and y == h - 1:
            return GOLD_D
        if not ragged and y == h - 2 and h > 6:
            return GOLD if x % 2 else GOLD_L
        if embroider and _stitch(x, y, w, h, seed):
            return STAR_B if B.n(x, y, seed + 9) < 0.5 else STAR
        return c
    return f


def _stitch(x, y, w, h, seed):
    """A sparse constellation: a few stars on a 5x5 lattice, jittered, joined by nothing (the thread is the stars)."""
    if w < 5 or h < 6:
        return False
    cx, cy = x // 5, y // 6
    jx = int(B.n(cx, cy, seed + 3) * 5)
    jy = int(B.n(cy, cx, seed + 4) * 6)
    return x % 5 == jx and y % 6 == jy and B.n(cx, cy, seed + 5) < 0.42


def robe_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if _stitch(x, y, w, h, seed):
            return STAR_B if B.n(x, y, seed + 9) < 0.5 else STAR
        return None
    return f


def trim(face, x, y, w, h):
    """Brass trim: a bright edge, a chased line, dark under-edge."""
    if face == "bottom":
        return GOLD_D
    if face == "top" or y == 0:
        return GOLD_L
    if y == h - 1:
        return GOLD_D
    return GOLD if (x + y) % 3 else mix(GOLD, GOLD_L, 0.5)


def lining(face, x, y, w, h):
    return PURP_L if y == 0 else (PURP if (x + y) % 5 else PURP_D)


def mantle(seed=0):
    """The stiff shoulder mantle: purpur velvet panels with a brass rim and a row of little star studs."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return PURP_D
        if x in (0, w - 1) or y in (0, h - 1):
            return GOLD if (x + y) % 2 else GOLD_D
        if face == "top":
            return mix(PURP, PURP_L, 0.3) if (x + y) % 3 else PURP
        if y == h // 2 and x % 3 == 1:
            return GOLD_L
        return mul(PURP if (x // 2) % 2 else mix(PURP, ROBE, 0.35), 1.04 - 0.14 * y / max(1, h))
    return f


def crust(seed=0, cracks=0.0):
    """Charred meteorite crust: knobbly dark rock with paler bumps, meteoric-iron glints and (with ``cracks``) split
    seams that open onto the starfield."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        c = mul(CRUST, 0.9 + r * 0.25)
        if B.n(x // 2, y // 2, seed + 1) < 0.22:
            c = CRUST_L if r > 0.5 else mix(CRUST, CRUST_L, 0.5)
        if B.n(x // 2 + 3, y // 2, seed + 2) < 0.12:
            c = CRUST_D
        if r > 0.94:
            c = IRONM
        if cracks and face != "bottom" and _seam(x, y, w, h, seed) and B.n(x, y, seed + 7) < cracks:
            return _space(x, y, seed)
        if face == "bottom":
            c = mul(c, 0.7)
        return c
    return f


def _seam(x, y, w, h, seed):
    """A jagged crack wandering down the face."""
    off = int(B.n(0, y // 2, seed + 11) * 3)
    return x == (w // 3 + off + y // 3) % max(1, w)


def _space(x, y, seed):
    r = B.n(x, y, seed + 21)
    if r < 0.12:
        return STAR if r < 0.07 else STAR_B
    if B.n(x // 2, y // 2, seed + 22) < 0.3:
        return mix(SPACE, NEBULA, 0.6)
    return SPACE


def crust_glow(seed=0, cracks=0.0):
    def f(face, x, y, w, h):
        if cracks and face != "bottom" and _seam(x, y, w, h, seed) and B.n(x, y, seed + 7) < cracks:
            c = _space(x, y, seed)
            return c if c in (STAR, STAR_B) else mix(NEBULA, SPACE, 0.4)
        return None
    return f


def face_paint(face, x, y, w, h):
    """The front of the meteorite head: the crust has split wide open in a jagged diamond; inside, a starfield with a
    nebula and two bright stars where the eyes would be, rimmed by still-hot ember."""
    if face != "front":
        return crust(500, cracks=0.9)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2 + 0.5
    jag = (B.n(y, 0, 503) - 0.5) * 2.2 + (B.n(x, 1, 504) - 0.5) * 1.4
    d = abs(x - cx) * 0.95 + abs(y - cy) * 0.8 + jag
    if d < 4.8:
        if (x, y) in ((int(cx) - 2, int(cy) - 1), (int(cx) + 2, int(cy) - 1)):
            return STAR
        if (x, y) in ((int(cx) - 2, int(cy)), (int(cx) + 2, int(cy))):
            return STAR_B
        r = B.n(x, y, 505)
        if r < 0.1:
            return STAR_B
        if abs(x - cx + 1) + abs(y - cy - 1.5) < 2.2:
            return NEBULA_L if r > 0.5 else NEBULA
        return SPACE if r > 0.35 else mix(SPACE, NEBULA, 0.5)
    if d < 5.8:
        return EMBER if B.n(x, y, 506) < 0.5 else mix(EMBER, CRUST, 0.4)
    return crust(501, cracks=0.0)(face, x, y, w, h)


def face_glow(face, x, y, w, h):
    if face != "front":
        return crust_glow(500, cracks=0.9)(face, x, y, w, h)
    c = face_paint(face, x, y, w, h)
    if c in (STAR, STAR_B, NEBULA_L, NEBULA):
        return c
    if c == EMBER:
        return EMBER
    if c == SPACE or c == mix(SPACE, NEBULA, 0.5):
        return mix(SPACE, NEBULA, 0.35)
    return None


def book_cover(col, seed=0):
    light = mix(col, (255, 255, 255), 0.25)
    dark = mul(col, 0.6)

    def f(face, x, y, w, h):
        if face in ("left", "right", "top", "bottom") and min(w, h) <= 2:
            return PAGE if (y % 2 or face in ("top", "bottom")) else PAGE_D          # the page block
        if x in (0, w - 1) or y in (0, h - 1):
            return GOLD if (x + y) % 2 else GOLD_D                                   # brass corners and rims
        if y == h // 2 and 1 <= x <= w - 2:
            return light
        if (x, y) == (w // 2, h // 2 - 2):
            return GOLD_L                                                            # a star on the cover
        return col if B.n(x, y, seed) > 0.15 else dark
    return f


def pages(face, x, y, w, h):
    if face in ("front", "back", "top"):
        if 1 <= x <= w - 2 and y % 2 == 1 and B.n(x, y, 77) < 0.7:
            return INK
        return PAGE
    return PAGE_D


def staff_shaft(face, x, y, w, h):
    if face in ("top", "bottom"):
        return GOLD_D
    if y % 9 == 0:
        return GOLD_L                                                                # brass collars
    k = 1.15 if x == w // 2 else (0.85 if x in (0, w - 1) else 1.0)
    return mul(mix(B.MAHOGANY_D, ROBE_D, 0.4), k + (B.n(x, y, 31) - 0.5) * 0.1)


def mater(face, x, y, w, h):
    """The astrolabe disc (the mater): a brass plate engraved with a star map, the rete's pointers glowing."""
    if face not in ("front", "back"):
        return GOLD_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r > w / 2 - 0.2:
        return GOLD_D
    if r > w / 2 - 1.2:
        return GOLD_L if y < cy else GOLD
    if r < 1.0:
        return STAR
    ang = math.degrees(math.atan2(y - cy, x - cx)) % 360
    if (ang % 45) < 9 and r > 1.5:
        return STAR_B                                                                # the rete's star pointers
    return mix(GOLD_D, INK, 0.45) if B.n(x, y, 41) < 0.6 else GOLD_D


def mater_glow(face, x, y, w, h):
    c = mater(face, x, y, w, h)
    return c if c in (STAR, STAR_B) else None


def hoop(face, x, y, w, h):
    return GOLD_L if (x + y) % 3 == 0 else GOLD


def glove(face, x, y, w, h):
    return B.brass(60)(face, x, y, w, h)


def star_core(face, x, y, w, h):
    return STAR if (x + y) % 2 == 0 else STAR_B


def mote(face, x, y, w, h):
    return STAR_B if (x + y) % 2 else NEBULA_L


# ---------------------------------------------------------------- build
def build():
    m = Model("star_curator", seed=733, shadow=1.4, walk_speed=0.7, walk_scale=0.6, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -46, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("hem", "skirt", pivot=(0, 30, 0))
    m.part("chest", "hips", pivot=(0, -2, 0), rot=(-3, 0, 0))
    m.part("collar", "chest", pivot=(0, -21, 3))
    m.part("neck", "chest", pivot=(0, -21, -0.5))
    m.part("head", "neck", pivot=(0, -2, 0))
    m.part("chip", "head", pivot=(11, -11, 2))
    m.part("motes", "head", pivot=(0, -7, 0))
    m.part("arm_r", "chest", pivot=(-9.5, -18, 0), rot=(-8, 0, 16))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-30, 0, -6))
    m.part("staff", "fore_r", pivot=(0, 14, -1), rot=(38, 0, -14))
    m.part("astro", "staff", pivot=(0, -44, 0))
    m.part("hoop_a", "astro", pivot=(0, 0, 0))
    m.part("hoop_b", "astro", pivot=(0, 0, 0), rot=(0, 90, 0))
    m.part("arm_l", "chest", pivot=(9.5, -18, 0), rot=(-20, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-60, 0, 8))
    m.part("orbit", "bone", pivot=(0, -52, 0))
    for k in range(5):
        a = k * 72
        r = 21 if k % 2 else 19
        x, z = math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r
        m.part(f"book_{k}", "orbit", pivot=(x, (k % 3) * 3 - 3, z), rot=(0, -a + 90, 10 if k % 2 else -8))

    # ---- the robe: three flaring tiers down to the floor, a front opening edged in brass, a torn hem
    m.box("skirt", -7, -1, -5, 14, 12, 10, robe(10))
    m.box("skirt", -9, 10, -7, 18, 12, 14, robe(11))
    m.box("skirt", -11, 21, -9, 22, 10, 18, robe(12))
    m.box("hem", -12.5, 0, -10.5, 25, 16, 21, robe(13, ragged=3))
    m.box("skirt", -1.5, 0, -5.6, 3, 11, 1, lining)                                   # the front opening
    m.box("skirt", -2, 10, -7.6, 4, 12, 1, lining)
    m.box("skirt", -2.5, 21, -9.6, 5, 10, 1, lining)
    m.box("hem", -3, 0, -11.1, 6, 14, 1, lining)
    for (x, y0, z, h) in ((-2.4, -1, -5.8, 12), (1.4, -1, -5.8, 12), (-3, 10, -7.8, 12), (2, 10, -7.8, 12),
                          (-3.5, 21, -9.8, 10), (2.5, 21, -9.8, 10)):
        m.box("skirt", x, y0, z, 1, h, 1, trim)                                       # brass edging down the front
    m.box("hem", -4, 0, -11.3, 1, 13, 1, trim)
    m.box("hem", 3, 0, -11.3, 1, 13, 1, trim)
    m.box("skirt", -7.5, -2, -5.5, 15, 2, 11, trim)                                   # the belt
    m.box("skirt", -2, -3, -6.4, 4, 4, 1, B.dial(numerals=8))                         # a little dial buckle
    m.box("skirt", -6, 2, -6, 2, 6, 1, pages)                                         # a note tucked in the belt
    m.box("skirt", 5, 1, -5.8, 2, 7, 2, B.brass(14))                                  # a brass scroll case
    m.box("skirt", 5.4, 0, -5.4, 1, 1, 1, GOLD_L)

    # ---- torso, mantle, collar
    m.box("chest", -6.5, -21, -4, 13, 21, 8, robe(20))
    m.box("chest", -10.5, -22, -6, 21, 6, 12, mantle(21))                             # the stiff mantle
    m.box("chest", -9.5, -16, -6.2, 19, 2, 1, trim)                                   # its lower rim, front
    m.box("chest", -9.5, -16, 5.2, 19, 2, 1, trim)
    m.box("chest", -3.5, -14, -5.0, 7, 7, 1, B.dial(rim=B.BRASS, face_c=(36, 28, 62), marks=STAR_B, numerals=8),
          glow=B.lens_glow(core=(110, 80, 200), glass=STAR, rim_px=True))             # the astrolabe pectoral
    m.box("chest", -1, -7, -4.8, 2, 6, 1, trim)                                       # its chain to the belt
    m.box("collar", -8, -8, 1, 16, 9, 2, mantle(22))                                # the standing collar
    m.box("collar", -9, -10, 1.5, 2, 11, 2, trim)
    m.box("collar", 7, -10, 1.5, 2, 11, 2, trim)
    m.box("collar", -7, -9, 2.6, 14, 1, 1, trim)
    m.box("collar", -7, -7, 0.6, 14, 7, 1, lining)
    m.box("neck", -2.5, -3, -2.5, 5, 4, 5, crust(30))

    # ---- the meteorite head: a big cracked core, lumps that break its outline, a floating chip and motes
    m.box("head", -7, -14, -7, 14, 14, 14, face_paint, glow=face_glow)
    m.box("head", -5, -16, -4, 8, 3, 8, crust(31, cracks=0.4), glow=crust_glow(31, cracks=0.4))
    m.box("head", 3, -15, -3, 5, 5, 6, crust(32))
    m.box("head", -8.5, -10, -3, 2, 6, 7, crust(33, cracks=0.5), glow=crust_glow(33, cracks=0.5))
    m.box("head", 6.5, -7, -4, 2, 5, 6, crust(34))
    m.box("head", -4, -12, 6.5, 9, 9, 2, crust(35, cracks=0.6), glow=crust_glow(35, cracks=0.6))
    m.box("head", -3, -1, -6, 7, 2, 7, crust(36))
    m.box("chip", -1.5, -1.5, -1.5, 3, 3, 3, crust(37, cracks=0.8), glow=crust_glow(37, cracks=0.8))
    for k in range(4):
        a = math.radians(k * 90 + 30)
        m.box("motes", math.cos(a) * 12 - 0.5, -0.5 + (k % 2) * 2, math.sin(a) * 12 - 0.5, 1, 1, 1, mote, glow=mote)

    # ---- right arm: a long sleeve and bell cuff, a brass glove round the astrolabe staff
    m.box("arm_r", -3, -2, -3, 6, 15, 6, robe(40, embroider=False))
    m.box("arm_r", -3.5, -3, -3.5, 7, 4, 7, mantle(41))
    m.box("fore_r", -3, 0, -3, 6, 9, 6, robe(42, embroider=False))
    m.box("fore_r", -4.5, 7, -4.5, 9, 6, 9, robe(43, embroider=False, ragged=2))     # the bell cuff
    m.box("fore_r", -4.6, 7, -4.6, 9, 1, 9, trim)
    m.box("fore_r", -2, 11, -2, 4, 5, 4, glove)
    # the staff: a dark shaft ringed in brass, a spike below, the astrolabe on top
    m.box("staff", -1, -40, -1, 2, 56, 2, staff_shaft)
    m.box("staff", -0.5, 16, -0.5, 1, 4, 1, GOLD_D)
    m.box("staff", -1.5, -41, -1.5, 3, 2, 3, B.brass(50))
    m.box("staff", -0.5, -44, -0.5, 1, 3, 1, GOLD)
    m.box("astro", -5, -5, -0.5, 10, 10, 1, mater, glow=mater_glow)
    m.box("astro", -1.5, -1.5, -1.5, 3, 3, 3, star_core, glow=star_core)
    m.box("astro", -0.5, -7, -0.5, 1, 2, 1, GOLD_L)                                   # the throne (top ring)
    for hp in ("hoop_a", "hoop_b"):
        for k in range(8):
            seg = f"{hp}_{k}"
            m.part(seg, hp, pivot=(0, 0, 0), rot=(0, 0, k * 45))
            m.box(seg, -2, -8.5, -0.5, 4, 1, 1, hoop)

    # ---- left arm: raised, palm up, a page curling off the fingers
    m.box("arm_l", -3, -2, -3, 6, 15, 6, robe(60, embroider=False))
    m.box("arm_l", -3.5, -3, -3.5, 7, 4, 7, mantle(61))
    m.box("fore_l", -3, 0, -3, 6, 9, 6, robe(62, embroider=False))
    m.box("fore_l", -4.5, 7, -4.5, 9, 6, 9, robe(63, embroider=False, ragged=2))
    m.box("fore_l", -4.6, 7, -4.6, 9, 1, 9, trim)
    m.box("fore_l", -2, 11, -2.5, 4, 4, 5, glove)
    m.box("fore_l", -3, 15, -4, 6, 1, 4, pages)                                       # the page on the palm
    m.box("fore_l", -0.5, 16, -1, 1, 1, 1, STAR, glow=STAR)                           # a mote of light on it

    # ---- the orbiting books: open covers round a page block
    for k in range(5):
        p = f"book_{k}"
        col = COVERS[k]
        m.box(p, -3.5, -4.5, -0.5, 7, 9, 1, book_cover(col, k))                       # the spine side cover
        m.box(p, -3, -4, 0.5, 6, 8, 2, pages)                                         # the page block
        m.box(p, -3.5, -4.5, 2.5, 7, 9, 1, book_cover(col, k + 5))
        m.box(p, -4, -4.5, -0.5, 1, 9, 4, book_cover(mul(col, 0.8), k + 9))           # the spine

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("hips", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (3, 10, 2)), (2.7, (-2, -8, -2)), (4.0, (0, 0, 0)))
    idle.rot("chip", (0, (0, 0, 0)), (2.0, (40, 180, 20)), (4.0, (0, 360, 0)))
    idle.pos("chip", (0, (0, 0, 0)), (2.0, (0, 1.5, 0)), (4.0, (0, 0, 0)))
    idle.rot("motes", (0, (0, 0, 0)), (2.0, (0, -180, 0)), (4.0, (0, -360, 0)))
    idle.rot("orbit", (0, (0, 0, 0)), (2.0, (0, 180, 0)), (4.0, (0, 360, 0)))
    for k in range(5):
        idle.pos(f"book_{k}", (0, (0, 0, 0)), (1.0 + k * 0.5, (0, 1.6, 0)), (4.0, (0, 0, 0)))
    idle.rot("hoop_a", (0, (0, 0, 0)), (2.0, (0, 180, 0)), (4.0, (0, 360, 0)))
    idle.rot("hoop_b", (0, (0, 0, 0)), (2.0, (180, 0, 0)), (4.0, (360, 0, 0)))
    idle.rot("hem", (0, (0, 0, 0)), (2.0, (2, 3, 0)), (4.0, (0, 0, 0)))
    idle.rot("fore_l", (0, (0, 0, 0)), (2.0, (-6, 0, 4)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.4)
    walk.pos("hips", (0, (0, 0, 0)), (0.6, (0, 0.8, 0)), (1.2, (0, 0, 0)), (1.8, (0, 0.8, 0)), (2.4, (0, 0, 0)))
    walk.rot("skirt", (0, (5, 4, 0)), (1.2, (5, -4, 0)), (2.4, (5, 4, 0)))
    walk.rot("hem", (0, (8, -3, 0)), (1.2, (8, 3, 0)), (2.4, (8, -3, 0)))
    walk.rot("chest", (0, (3, -4, 0)), (1.2, (3, 4, 0)), (2.4, (3, -4, 0)))
    walk.rot("arm_r", (0, (-4, 0, 0)), (1.2, (4, 0, 0)), (2.4, (-4, 0, 0)))
    walk.rot("orbit", (0, (0, 0, 0)), (2.4, (0, 180, 0)))

    # staff: the astrolabe swung back over his right shoulder (0.7 s = 14 ticks), a forehand sweep at 0.7 s, a
    # backhand at 1.2 s, a thrust at 1.7 s (the thrust only in phase 2)
    a = m.anim("staff", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-110, -20, 50)), (0.7, (-116, -22, 54)), (0.78, (-70, 40, -40), "linear"),
          (1.1, (-76, 56, -50)), (1.2, (-70, -30, 46), "linear"), (1.5, (-80, 0, 10)), (1.7, (-84, 0, 10)),
          (1.76, (-96, 0, 6), "linear"), (2.0, (-96, 0, 6)), (2.6, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.7, (20, 0, 0)), (0.78, (40, 0, 0), "linear"), (1.2, (40, 0, 0)),
          (1.5, (150, 0, 0)), (1.7, (150, 0, 0)), (1.76, (164, 0, 0), "linear"), (2.0, (164, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, 30, 0)), (0.78, (6, -30, 0), "linear"), (1.1, (4, -34, 0)),
          (1.2, (6, 28, 0), "linear"), (1.5, (-6, 0, 0)), (1.7, (-8, 0, 0)), (1.76, (16, 0, 0), "linear"),
          (2.0, (14, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-10, 0, -30)), (1.2, (-10, 0, -40)), (2.0, (-20, 0, -20)), (2.6, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.78, (0, -10, 0)), (1.2, (0, 10, 0)), (1.8, (6, 0, 0)), (2.6, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.7, (0, 0, 0)), (1.76, (0, -1, -2), "linear"), (2.0, (0, -1, -2)), (2.6, (0, 0, 0)))

    # volley: the left hand raised, the books drawn in tight and spinning faster (0.9 s = 18 ticks), then flung out
    a = m.anim("volley", 2.1)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-150, 0, -10)), (0.9, (-156, 0, -12)), (0.96, (-80, 0, 10), "linear"),
          (1.4, (-80, 0, 10)), (2.1, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (0.96, (-10, 0, 0), "linear"), (1.4, (-10, 0, 0)),
          (2.1, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (0.9, (0, 540, 0)), (0.96, (0, 600, 0), "linear"), (1.4, (0, 700, 0)),
          (2.1, (0, 720, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (0.9, (0.6, 1.0, 0.6)), (0.96, (1.6, 1.0, 1.6), "linear"), (1.4, (1.3, 1, 1.3)),
            (2.1, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-10, 10, 0)), (0.96, (8, -6, 0), "linear"), (1.4, (6, -6, 0)),
          (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (0.96, (6, 0, 0), "linear"), (2.1, (0, 0, 0)))

    # well: the staff planted before him, both hands on it (1.0 s = 20 ticks): the gravity well opens at the impact,
    # he leans on the staff while everything is drawn in, then wrenches it round
    a = m.anim("well", 3.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-60, 0, -20)), (1.0, (-64, 0, -22)), (1.06, (-40, 0, -10), "linear"),
          (3.0, (-40, 0, -10)), (3.2, (-60, 30, -10)), (3.8, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.8, (50, 0, 0)), (1.0, (56, 0, 0)), (1.06, (32, 0, 0), "linear"),
          (3.0, (32, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 0, 30)), (1.0, (-74, 0, 34)), (1.06, (-50, 0, 30), "linear"),
          (3.0, (-50, 0, 30)), (3.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.06, (18, 0, 0), "linear"), (3.0, (16, 0, 0)),
          (3.2, (10, 20, 0)), (3.8, (0, 0, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (1.0, (1.2, 1.0, 1.2)), (1.06, (0.5, 1.0, 0.5), "linear"), (3.0, (0.4, 1, 0.4)),
            (3.2, (1.8, 1, 1.8), "linear"), (3.8, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (1.0, (0, 120, 0)), (3.0, (0, 1080, 0)), (3.8, (0, 1080, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.06, (0, -2, 0), "linear"), (3.0, (0, -2, 0)), (3.8, (0, 0, 0)))

    # starfall: the astrolabe raised to the dome (0.8 s = 16 ticks), then a sweep down toward the floor as the shards fall
    a = m.anim("starfall", 4.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-170, 0, -10)), (0.8, (-176, 0, -12)), (0.86, (-150, 0, -8), "linear"),
          (2.6, (-150, 0, -8)), (3.0, (-60, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.8, (165, 0, 0)), (2.6, (165, 0, 0)), (3.0, (60, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-120, 0, -40)), (0.86, (-130, 0, -50), "linear"), (2.6, (-130, 0, -50)),
          (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (0.86, (-44, 0, 0), "linear"), (2.6, (-36, 0, 0)),
          (3.0, (10, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (2.6, (-12, 0, 0)), (3.0, (10, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("astro", (0, (1, 1, 1)), (0.8, (1.4, 1.4, 1.4)), (0.86, (1.7, 1.7, 1.7), "linear"), (2.6, (1.5, 1.5, 1.5)),
            (4.0, (1, 1, 1)))

    # orbit: he draws in (0.6 s = 12 ticks), the books spin out in a wide sweeping ring round him
    a = m.anim("orbit", 2.0)
    a.scale("orbit", (0, (1, 1, 1)), (0.6, (0.5, 1.0, 0.5)), (0.64, (2.0, 1.0, 2.0), "linear"), (1.2, (1.7, 1, 1.7)),
            (2.0, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (0.6, (0, 90, 0)), (1.2, (0, 540, 0)), (2.0, (0, 720, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.6, (0, 4, 0)), (0.64, (0, -18, 0), "linear"), (1.2, (0, -16, 0)),
          (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, -20)), (0.64, (-30, 0, 60), "linear"), (1.2, (-26, 0, 56)),
          (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-20, 0, 20)), (0.64, (-30, 0, -60), "linear"), (1.2, (-26, 0, -56)),
          (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (12, 0, 0)), (0.64, (-10, 0, 0), "linear"), (1.2, (-8, 0, 0)), (2.0, (0, 0, 0)))

    # lance: the staff levelled like a lance (0.8 s = 16 ticks), then he streaks along the line in starlight
    a = m.anim("lance", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-80, 10, 20)), (0.8, (-84, 12, 22)), (0.86, (-90, 0, 4), "linear"),
          (1.3, (-90, 0, 4)), (2.1, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.8, (150, 0, 0)), (0.86, (158, 0, 0), "linear"), (1.3, (158, 0, 0)),
          (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, 20, 0)), (0.86, (22, 0, 0), "linear"), (1.3, (20, 0, 0)),
          (2.1, (0, 0, 0)))
    a.rot("skirt", (0, (0, 0, 0)), (0.86, (0, 0, 0)), (1.0, (14, 0, 0)), (1.3, (12, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.86, (0, 0, 0)), (1.0, (8, 0, 0)), (1.3, (6, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (20, 0, -20)), (0.86, (40, 0, -30), "linear"), (2.1, (0, 0, 0)))

    # pagestorm (phase 2): both arms flung up, the books torn open (1.2 s = 24 ticks); the pages burst out over the hall
    a = m.anim("pagestorm", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-140, 0, 40)), (1.2, (-146, 0, 44)), (1.26, (-110, 0, 80), "linear"),
          (1.6, (-110, 0, 80)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-140, 0, -40)), (1.2, (-146, 0, -44)), (1.26, (-110, 0, -80), "linear"),
          (1.6, (-110, 0, -80)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-30, 0, 0)), (1.26, (-40, 0, 0), "linear"), (1.6, (-36, 0, 0)), (2.2, (0, 0, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (1.2, (0.7, 1.4, 0.7)), (1.26, (2.2, 1.0, 2.2), "linear"), (1.6, (1.8, 1, 1.8)),
            (2.2, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (1.2, (0, 360, 0)), (2.2, (0, 720, 0)))
    for k in range(5):
        a.rot(f"book_{k}", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.26, (0, 0, 90), "linear"), (1.6, (40, 0, 90)),
              (2.2, (0, 0, 0)))

    # constellation (phase 2): he traces the stars with the staff's tip (1.0 s = 20 ticks), then strikes the floor and
    # the lines burst star by star
    a = m.anim("constellation", 3.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-100, -30, 30)), (0.6, (-110, 20, 20)), (0.9, (-130, 0, 10)),
          (1.0, (-134, 0, 10)), (1.06, (-50, 0, 6), "linear"), (2.4, (-50, 0, 6)), (3.2, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.06, (-40, 0, 0), "linear"), (2.4, (-40, 0, 0)),
          (3.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (-4, -16, 0)), (0.6, (-6, 16, 0)), (1.0, (-10, 0, 0)), (1.06, (20, 0, 0), "linear"),
          (2.4, (18, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-40, 0, -50)), (2.4, (-40, 0, -50)), (3.2, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.06, (0, -3, 0), "linear"), (2.4, (0, -3, 0)), (3.2, (0, 0, 0)))

    # invert (phase 3, invulnerable): he rises off the floor, robe hanging upward, arms spread, the head splitting
    # wider (2.0 s = 40 ticks), then the crater's gravity flips
    a = m.anim("invert", 4.0)
    a.pos("hips", (0, (0, 0, 0)), (1.6, (0, 12, 0)), (2.0, (0, 14, 0)), (2.06, (0, 6, 0), "linear"), (3.2, (0, 4, 0)),
          (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-60, 0, 70)), (2.0, (-70, 0, 80)), (2.06, (-160, 0, 40), "linear"),
          (3.2, (-160, 0, 40)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-60, 0, -70)), (2.0, (-70, 0, -80)), (2.06, (-160, 0, -40), "linear"),
          (3.2, (-160, 0, -40)), (4.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.6, (0, 40, 0)), (2.0, (-16, 60, 0)), (2.06, (20, 80, 0), "linear"), (3.2, (10, 40, 0)),
          (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (-40, 0, 0), "linear"), (3.2, (-30, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (2.0, (1.15, 1.15, 1.15)), (2.06, (1.3, 1.3, 1.3), "linear"), (3.2, (1.2, 1.2, 1.2)),
            (4.0, (1, 1, 1)))
    a.scale("orbit", (0, (1, 1, 1)), (2.0, (1.4, 1.0, 1.4)), (2.06, (2.2, 1, 2.2), "linear"), (3.2, (1.8, 1, 1.8)),
            (4.0, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (2.0, (0, 360, 180)), (4.0, (0, 720, 360)))

    # blink (phase 3): he folds into starlight, arms wrapped round the staff (0.7 s = 14 ticks), and vanishes
    a = m.anim("blink", 1.2)
    a.scale("bone", (0, (1, 1, 1)), (0.6, (0.7, 1.15, 0.7)), (0.7, (0.4, 1.3, 0.4)), (0.76, (0.2, 1.4, 0.2), "linear"),
            (0.9, (0.8, 1.05, 0.8)), (1.2, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-20, 0, -30)), (0.9, (-20, 0, -30)), (1.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-30, 0, 40)), (0.9, (-30, 0, 40)), (1.2, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (0.7, (0, 360, 0)), (1.2, (0, 720, 0)))

    # starlance (phase 3): from a crystal node, the astrolabe aimed across the crater (0.9 s = 18 ticks): a beam of
    # starlight, then he holds the pose, spent
    a = m.anim("starlance", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-96, 0, 10)), (0.9, (-100, 0, 10)), (0.96, (-90, 0, 4), "linear"),
          (1.5, (-90, 0, 4)), (2.1, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.9, (175, 0, 0)), (0.96, (172, 0, 0), "linear"), (1.5, (172, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-70, 0, -10)), (0.96, (-60, 0, -20), "linear"), (1.5, (-60, 0, -20)),
          (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-8, 0, 0)), (0.96, (10, 0, 0), "linear"), (1.5, (8, 0, 0)), (2.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, 0, 2)), (0.96, (0, 0, 3), "linear"), (1.5, (0, 0, 3)), (2.1, (0, 0, 0)))
    a.scale("astro", (0, (1, 1, 1)), (0.9, (1.5, 1.5, 1.5)), (0.96, (1.9, 1.9, 1.9), "linear"), (1.5, (1.3, 1.3, 1.3)),
            (2.1, (1, 1, 1)))

    # roar (phase two): arms flung wide, the meteorite head thrown back, the books scattering
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 70)), (1.6, (-44, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (0.5, (1.8, 1.0, 1.8)), (1.6, (1.7, 1, 1.7)), (2.0, (1, 1, 1)))
    a.scale("head", (0, (1, 1, 1)), (0.5, (1.2, 1.2, 1.2)), (1.6, (1.15, 1.15, 1.15)), (2.0, (1, 1, 1)))

    # stagger: he sags onto the staff, the head lolling, the books dropping low and slowing
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -8, 0)), (1.6, (0, -8, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -14)), (1.6, (30, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-30, 0, 10)), (1.6, (-30, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (1.6, (20, 0, -10)), (2.0, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.3, (0, -26, 0)), (1.6, (0, -26, 0)), (2.0, (0, 0, 0)))
