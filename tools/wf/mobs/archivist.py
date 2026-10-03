"""The Archivist (L'Archiviste): a spectral scholar of parchment and ink hovering over the floor of
the Forbidden Archive. It has no legs: under a narrow waist a skirt of loose pages fans out like an
upturned flower and tapers into a curling tail of ink. A halo of fanned pages stands behind its
lantern head, whose glass glows like a reading lamp behind two ink-black eyes and a rune. Four long
arms hold two open tomes, a giant quill and an inkwell."""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
PARCH = (230, 212, 168)
PARCH_D = (184, 156, 110)
BURN = (104, 72, 44)
INK = (30, 26, 50)
INK_L = (70, 64, 118)
LEATHER = (110, 40, 36)
LEATHER_D = (66, 24, 24)
GOLD = (226, 184, 82)
GOLD_D = (150, 110, 44)
IRON = (54, 52, 60)
IRON_L = (118, 114, 126)
LAMP = (255, 222, 150)
LAMP_D = (236, 160, 72)
RUNE = (120, 232, 255)
FEATHER = (236, 236, 244)
FEATHER_D = (170, 172, 190)

L = "linear"
Z = (0, 0, 0)


def _h(x, y, s):
    v = (x * 73856093) ^ (y * 19349663) ^ (s * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def _side(face):
    return face not in ("top", "bottom")


def _glyph(x, y, seed):
    """Rune pixels: small 3x3 glyphs laid on a grid."""
    gx, gy = x // 4, y // 4
    lx, ly = x % 4, y % 4
    if lx == 3 or ly == 3:
        return False
    bits = int(_h(gx, gy, seed) * 512)
    return bool(bits >> (ly * 3 + lx) & 1)


# ------------------------------------------------------------------ paints
def parchment(seed=0, text=True, ragged=0, runes=False, base=PARCH):
    """Aged paper: soft stains, burnt margins, lines of handwriting, optional glowing runes."""
    def f(face, x, y, w, h):
        if ragged and _side(face):
            cut = int(_h(x, 3, seed) * ragged * 1.5)
            if y >= h - cut:
                return None
        stain = _h(x // 3, y // 3, seed + 1)
        c = mix(base, PARCH_D, 0.45 * stain)
        edge = min(x, y, w - 1 - x, h - 1 - y) if _side(face) else 9
        if edge == 0:
            return mix(BURN, c, 0.25)
        if edge == 1 and _h(x, y, seed + 2) < 0.5:
            c = mix(c, BURN, 0.35)
        if text and face in ("front", "back") and w >= 5 and 2 <= x < w - 2 and y >= 2 and y % 3 == 0:
            word = (x + int(_h(y, 0, seed) * 7)) % 6
            if word < 4:
                return mix(INK, c, 0.55)
        if runes and face in ("front", "back") and _glyph(x, y, seed) and 1 <= x < w - 1 and 1 <= y < h - 1 \
                and (y // 4) % 3 == 1:
            return mix(RUNE, INK, 0.4)
        return c
    return f


def parchment_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back") and _glyph(x, y, seed) and 1 <= x < w - 1 and 1 <= y < h - 1 \
                and (y // 4) % 3 == 1:
            return RUNE
        return None
    return f


def soaked(paint, start=0.55):
    """Pages drinking ink from below: the lower part darkens into wet blue-black, with wicking streaks."""
    def f(face, x, y, w, h):
        c = paint(face, x, y, w, h)
        if c is None or not _side(face):
            return c
        t = y / max(1, h - 1) - start + 0.25 * (_h(x, 5, 17) - 0.5)
        if t > 0:
            return mix(c, INK, min(1.0, t * 2.6))
        return c
    return f


def ink_runes(seed):
    """Faint runes surfacing in the ink."""
    def f(face, x, y, w, h):
        if _side(face) and _glyph(x + seed, y, seed) and (x // 4 + y // 4) % 3 == 0:
            return mul(RUNE, 0.55)
        return None
    return f


def ink(seed=0, drips=False):
    """Glossy ink: blue-black with a highlight streak and wet drips."""
    def f(face, x, y, w, h):
        c = mul(INK, 0.9 + 0.2 * _h(x, y, seed))
        if face == "top" or (_side(face) and (x + y + seed) % 7 == 0 and y < h // 2):
            c = mix(c, INK_L, 0.6)
        if drips and _side(face) and _h(x, 9, seed) < 0.3 and y > h - 3:
            return mix(INK_L, INK, 0.5)
        return c
    return f


def leather(seed=0):
    def f(face, x, y, w, h):
        corner = (x in (0, w - 1)) and (y in (0, h - 1))
        if corner:
            return GOLD
        if x == 0 or y == 0 or x == w - 1 or y == h - 1:
            return LEATHER_D
        c = mul(LEATHER, 0.9 + 0.2 * _h(x, y, seed))
        if face in ("front", "back", "top", "bottom") and (x == w // 2 or y == h // 2) and w > 4:
            return GOLD_D                                                     # tooled cross on the cover
        return c
    return f


def iron(face, x, y, w, h):
    return IRON_L if (y == 0 and _side(face)) or face == "top" else IRON


def lamp_glass(face, x, y, w, h):
    """Lantern glass: warm light, two ink-black eyes with runs on the front, a rune on the brow."""
    c = mix(LAMP, LAMP_D, y / max(1, h - 1))
    if face == "front":
        if _eye(x, y):
            return INK
        if y == 1 and 3 <= x <= 4:
            return RUNE
    if _side(face) and (x in (0, w - 1)):
        return mul(c, 0.8)
    return c


def _eye(x, y):
    """Slanted ink eyes (inner corners low: a glare) with ink running down the glass."""
    return (y == 3 and x in (1, 2, 5, 6)) or (y == 4 and x in (2, 3, 4, 5)) or (y in (5, 6) and x == 2) or \
        (y in (5, 6, 7) and x == 5)


def lamp_glow(face, x, y, w, h):
    if face == "bottom":
        return None
    if face == "front" and _eye(x, y):
        return None
    if face == "front" and y == 1 and 3 <= x <= 4:
        return RUNE
    return mix(LAMP, LAMP_D, y / max(1, h - 1))


def feather(face, x, y, w, h):
    if not _side(face):
        return FEATHER_D
    if face in ("front", "back"):
        mid = (w - 1) / 2
        if abs(x - mid) > mid * min(1.0, (y + 1) / 7) + 0.5:
            return None                                                       # tapered tip
        if abs(x - mid) < 0.6:
            return (214, 204, 184)                                            # rachis
        c = FEATHER_D if (y - int(abs(x - mid))) % 4 == 0 else FEATHER
        if abs(x - mid) > mid - 0.6:
            c = mul(c, 0.86)
        return mix(c, INK, 0.7) if y >= h - 4 else c                          # ink-soaked base
    return FEATHER_D


# ------------------------------------------------------------------ model
def build():
    m = Model("archivist", seed=89, shadow=1.0, walk_speed=0.6, walk_scale=0.6)

    # ---------------------------------------------------------- skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -40, 0))
    m.part("chest", "body", pivot=(0, -1, 0), rot=(6, 0, 0))
    m.part("head", "chest", pivot=(0, -21, -1), scale=(1.25, 1.25, 1.25))
    m.part("halo", "chest", pivot=(0, -19, 5), rot=(-10, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_u{side}", "chest", pivot=(10 * sx, -17, 0), rot=(-10, 0, 62 * -sx))
        m.part(f"fore_u{side}", f"arm_u{side}", pivot=(0, 12, 0), rot=(-80, 0, 0))
        m.part(f"tome_{side}", f"fore_u{side}", pivot=(0, 13, -1), rot=(129, 66 * sx, -9 * sx))
        m.part(f"cover_{side}a", f"tome_{side}", pivot=(0, 0, 0), rot=(0, 0, 22))
        m.part(f"cover_{side}b", f"tome_{side}", pivot=(0, 0, 0), rot=(0, 0, -22))
        m.part(f"arm_d{side}", "chest", pivot=(7 * sx, -7, -1), rot=(-14, 0, 44 * -sx))
        m.part(f"fore_d{side}", f"arm_d{side}", pivot=(0, 10, 0), rot=(-60, 0, 0))
    m.part("quill", "fore_dr", pivot=(0, 11, -1), rot=(42, 0, -66))
    m.part("inkwell", "fore_dl", pivot=(0, 11, 0), rot=(42, 0, 66))
    # skirt: two rings of pages fanned outward like an upturned flower
    for i in range(8):
        m.part(f"page_o{i}", "body", pivot=(0, 1, 0), rot=(-52, i * 45 + 22.5, 0))
        m.part(f"page_i{i}", "body", pivot=(0, 1, 0), rot=(-28, i * 45, 0))
    # curling tail of ink and scrolls
    m.part("orbit", "body", pivot=(0, -6, 0))
    m.part("tail1", "body", pivot=(0, 4, 0), rot=(8, 0, 0))
    m.part("tail2", "tail1", pivot=(0, 9, 0.5), rot=(14, 0, 6))
    m.part("tail3", "tail2", pivot=(0, 8, 0.5), rot=(16, 0, 6))

    # ---------------------------------------------------------- body
    m.box("body", -6, -2, -4, 12, 6, 8, {"side": parchment(1, ragged=2), "*": PARCH_D})
    m.box("body", -6.5, -3, -4.5, 13, 2, 9, leather(2))                         # book-strap belt
    m.box("chest", -6, -9, -4, 12, 8, 8, parchment(2, text=False))             # narrow waist
    m.box("chest", -7, -19, -4, 14, 10, 8, {"front": parchment(3, runes=True), "*": parchment(4)},
          glow={"front": parchment_glow(3)})
    m.box("chest", -2, -19, 4, 4, 18, 2, leather(5))                            # a book spine down the back
    m.box("chest", -9, -21, -5, 18, 4, 10, parchment(6, base=(214, 196, 150)))  # shoulder mantle
    m.box("chest", -4, -23, -3, 8, 2, 6, leather(8))                            # collar clasp
    m.box("chest", -7.5, -12, -4.5, 15, 1, 9, GOLD_D)                           # binding bands
    m.box("chest", -6.5, -5, -4.5, 13, 1, 9, GOLD_D)
    # halo: seven pages fanned behind the head, edges glowing with runes
    for i in range(7):
        ang = -60 + i * 20
        name = f"fan{i}"
        m.part(name, "halo", pivot=(0, 0, 0), rot=(0, 0, ang))
        hgt = 28 if i % 2 == 0 else 22
        m.box(name, -2.5, -hgt, 0, 5, hgt, 1, {"front": parchment(20 + i, runes=True), "back": parchment(30 + i),
                                               "*": PARCH_D}, glow={"front": parchment_glow(20 + i)})

    # ---------------------------------------------------------- head: a reading lantern
    m.box("head", -5, -1, -5, 10, 2, 10, iron)                                  # base plate
    m.box("head", -4, -9, -4, 8, 8, 8, lamp_glass, glow=lamp_glow)
    for x, z in ((-5, -5), (4, -5), (-5, 4), (4, 4)):
        m.box("head", x, -10, z, 1, 10, 1, iron)                                # corner posts
    m.box("head", -5, -11, -5, 10, 2, 10, iron)
    m.box("head", -3.5, -13, -3.5, 7, 2, 7, iron)
    m.box("head", -1.5, -15, -1.5, 3, 2, 3, {"*": GOLD, "top": GOLD_D})
    m.box("head", -0.5, -19, -2, 1, 4, 4, {"*": IRON_L})                        # ring handle
    # a scholar's hood of parchment draped over the back of the lantern
    m.box("head", -6, -10, 2, 12, 11, 4, parchment(7, ragged=3))

    # ---------------------------------------------------------- arms: rolled parchment sleeves, ink hands
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"arm_u{side}", -2.5, -2, -2.5, 5, 13, 5, parchment(40 + sx, text=False))
        m.box(f"arm_u{side}", -3, -3, -3, 6, 3, 6, leather(41 + sx))
        m.box(f"fore_u{side}", -2, 0, -2, 4, 11, 4, parchment(42 + sx, text=False))
        m.box(f"fore_u{side}", -2.5, 8, -2.5, 5, 5, 5, ink(43 + sx, drips=True))      # ink-stained hand
        m.box(f"arm_d{side}", -2, -1, -2, 4, 11, 4, parchment(44 + sx, text=False))
        m.box(f"fore_d{side}", -1.5, 0, -1.5, 3, 9, 3, parchment(45 + sx, text=False))
        m.box(f"fore_d{side}", -2, 8, -2, 4, 4, 4, ink(46 + sx, drips=True))
        # open tome: pages block + two covers splayed in a V
        tome = f"tome_{side}"
        m.box(tome, -7, -1.5, -8, 14, 2, 16, {"top": parchment(50 + sx, runes=True), "*": PARCH_D},
              glow={"top": parchment_glow(50 + sx)})
        m.box(tome, -0.5, -2, -8, 1, 1, 16, PARCH_D)                            # gutter
        m.box(f"cover_{side}a", 0, -0.5, -8.5, 8, 1, 17, leather(52 + sx))
        m.box(f"cover_{side}b", -8, -0.5, -8.5, 8, 1, 17, leather(53 + sx))
    # giant quill: shaft, feather vane, ink-wet nib
    m.box("quill", -0.5, -10, -0.5, 1, 26, 1, (214, 204, 180))
    m.box("quill", -3.5, -40, -0.5, 7, 30, 1, feather)
    m.box("quill", -1, 16, -1, 2, 2, 2, INK_L)
    m.box("quill", -0.5, 18, -0.5, 1, 4, 1, INK)
    # inkwell: dark glass with a glowing rune
    m.box("inkwell", -2.5, 0, -2.5, 5, 5, 5, {"front": lambda f_, x, y, w, h: RUNE if (x, y) in ((2, 1), (1, 2), (3, 2),
                                                                                                 (2, 3)) else INK,
                                              "*": ink(60)}, glow={"front": lambda f_, x, y, w, h: RUNE if (x, y) in
                                                                   ((2, 1), (1, 2), (3, 2), (2, 3)) else None})
    m.box("inkwell", -1.5, -1, -1.5, 3, 1, 3, GOLD)

    # ---------------------------------------------------------- skirt pages and ink tail
    for i in range(8):
        m.box(f"page_o{i}", -4.5, 0, -7, 9, 20, 1, {"front": soaked(parchment(70 + i, ragged=4, runes=i % 2 == 0)),
                                                    "back": soaked(parchment(80 + i, ragged=4)), "*": PARCH_D},
              glow={"front": parchment_glow(70 + i)} if i % 2 == 0 else None)
        m.box(f"page_i{i}", -4, 0, -5.5, 8, 15, 1, {"front": soaked(parchment(90 + i, ragged=3, base=(214, 196, 150))),
                                                   "back": soaked(parchment(100 + i, ragged=3)), "*": PARCH_D})
    for i, (ox, oy, oz) in enumerate(((17, -6, 4), (-15, 4, 9), (5, -14, -17), (-9, 10, -15))):
        m.box("orbit", ox - 2.5, oy - 3.5, oz, 5, 7, 1, {"front": parchment(120 + i, runes=True), "back": parchment(130 + i),
                                                       "*": PARCH_D}, glow={"front": parchment_glow(120 + i)})
    m.box("tail1", -6, 0, -6, 12, 10, 12, ink(110), glow=ink_runes(110))
    m.box("tail2", -4, 0, -4, 8, 9, 8, ink(111), glow=ink_runes(111))
    m.box("tail3", -2.5, 0, -2.5, 5, 8, 5, ink(112, drips=True))
    m.box("tail3", -0.5, 8, -0.5, 1, 4, 1, INK_L)

    _animations(m)
    return m


def _animations(m):
    idle = m.anim("idle", 4.0)
    idle.pos("body", (0, Z), (1.0, (0, 1.5, 0)), (2.0, Z), (3.0, (0, -1.5, 0)), (4.0, Z))
    idle.rot("halo", (0, Z), (2.0, (0, 0, 4)), (4.0, Z))
    idle.rot("orbit", (0, Z), (4.0, (0, -360, 0), L))
    idle.pos("orbit", (0, Z), (1.0, (0, 2, 0)), (2.0, Z), (3.0, (0, -2, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.4, (4, 8, 0)), (2.8, (-3, -8, 0)), (4.0, Z))
    idle.rot("tail1", (0, Z), (1.0, (6, 0, 8)), (2.0, Z), (3.0, (6, 0, -8)), (4.0, Z))
    idle.rot("tail2", (0, Z), (1.3, (10, 0, -10)), (2.6, (4, 0, 10)), (4.0, Z))
    idle.rot("tail3", (0, Z), (1.6, (14, 0, 12)), (3.2, (6, 0, -12)), (4.0, Z))
    for i in range(8):                       # pages lift and settle in a slow travelling ripple
        t0 = 0.4 * i
        idle.rot(f"page_o{i}", (0, Z), (t0 + 0.05, Z), (t0 + 0.6, (-12, 0, 0)), (t0 + 1.2, Z), (4.0, Z))
    for side, sx in (("r", -1), ("l", 1)):
        idle.rot(f"arm_u{side}", (0, Z), (2.0, (-6, 0, 4 * sx)), (4.0, Z))
        idle.rot(f"arm_d{side}", (0, Z), (2.0, (6, 0, 0)), (4.0, Z))
        idle.rot(f"cover_{side}a", (0, Z), (1.0, (0, 0, 6)), (2.0, Z), (4.0, Z))

    walk = m.anim("walk", 2.0)               # gliding: leans into the motion, the tail trails behind
    walk.rot("body", (0, (10, 0, 0)), (1.0, (12, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("tail1", (0, (24, 0, 0)), (1.0, (30, 0, 0)), (2.0, (24, 0, 0)))
    walk.rot("tail2", (0, (16, 0, 0)), (1.0, (22, 0, 0)), (2.0, (16, 0, 0)))

    # volley (impact 0.7 s = 14 t): tomes drawn to the chest, then thrust open toward the target
    a = m.anim("volley", 1.3)
    _tomes(a, [(0.5, (30, 0, 0), (40, 0, 0)), (0.7, (-40, 0, 0), (60, 0, 0), L), (0.95, (-36, 0, 0), (56, 0, 0))], 1.3)
    a.rot("chest", (0, Z), (0.5, (-10, 0, 0)), (0.7, (12, 0, 0), L), (0.95, (10, 0, 0)), (1.3, Z))
    a.rot("halo", (0, Z), (0.5, (-14, 0, 0)), (0.7, (10, 0, 0), L), (1.3, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (0.9, 0.9, 1)), (0.7, (1.15, 1.15, 1), L), (1.0, (1, 1, 1)), (1.3, (1, 1, 1)))

    # ink pool (impact 0.8 s = 16 t): the quill raised high, then slashed down at the floor
    a = m.anim("ink_pool", 1.6)
    _quill_arm(a, [(0.6, (-160, 0, 10)), (0.8, (-20, 0, 0), L), (1.15, (-16, 0, 0))], 1.6)
    a.rot("arm_dl", (0, Z), (0.6, (-90, 0, -20)), (0.8, (10, 0, -10), L), (1.15, (10, 0, -10)), (1.6, Z))
    a.rot("inkwell", (0, Z), (0.6, (0, 0, 0)), (0.8, (-110, 0, 0), L), (1.15, (-110, 0, 0)), (1.6, Z))
    a.rot("chest", (0, Z), (0.6, (-16, 10, 0)), (0.8, (24, -6, 0), L), (1.15, (20, 0, 0)), (1.6, Z))
    a.pos("body", (0, Z), (0.6, (0, 4, 0)), (0.8, (0, -5, -2), L), (1.15, (0, -5, -2)), (1.6, Z))

    # blink (vanish at 0.5 s = 10 t): folds into its pages and is gone, unfolds elsewhere
    a = m.anim("blink", 1.3)
    a.scale("bone", (0, (1, 1, 1)), (0.35, (1.1, 0.9, 1.1)), (0.5, (0.05, 0.05, 0.05), L), (0.7, (0.05, 0.05, 0.05)),
            (0.95, (1.08, 1.08, 1.08)), (1.3, (1, 1, 1)))
    a.rot("bone", (0, Z), (0.5, (0, 180, 0), L), (0.7, (0, 180, 0)), (0.95, (0, 340, 0)), (1.3, (0, 360, 0)))
    a.rot("halo", (0, Z), (0.35, (-30, 0, 0)), (0.95, (10, 0, 0)), (1.3, Z))

    # summon (impact 0.9 s = 18 t): every arm raised, the tomes held to the ceiling, the lantern thrown back
    a = m.anim("summon", 1.9)
    _tomes(a, [(0.7, (-90, 0, 0), (40, 0, 0)), (1.4, (-90, 0, 0), (40, 0, 0))], 1.9)
    _quill_arm(a, [(0.7, (-150, 0, 20)), (1.4, (-150, 0, 20))], 1.9)
    a.rot("arm_dl", (0, Z), (0.7, (-150, 0, -20)), (1.4, (-150, 0, -20)), (1.9, Z))
    a.rot("head", (0, Z), (0.7, (-26, 0, 0)), (1.4, (-26, 0, 0)), (1.9, Z))
    a.rot("chest", (0, Z), (0.7, (-14, 0, 0)), (1.4, (-14, 0, 0)), (1.9, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.7, (1.2, 1.2, 1)), (1.4, (1.2, 1.2, 1)), (1.9, (1, 1, 1)))
    a.pos("body", (0, Z), (0.7, (0, 6, 0)), (1.4, (0, 6, 0)), (1.9, Z))

    # quill stab (impact 0.6 s = 12 t): the great quill levelled like a spear and driven forward
    a = m.anim("quill_stab", 1.3)
    _quill_arm(a, [(0.45, (-60, 30, 30)), (0.6, (-96, -10, 0), L), (0.9, (-92, -10, 0))], 1.3)
    a.rot("chest", (0, Z), (0.45, (-6, 30, 0)), (0.6, (16, -20, 0), L), (0.9, (14, -18, 0)), (1.3, Z))
    a.pos("bone", (0, Z), (0.45, (0, 0, 4)), (0.6, (0, 0, -10), L), (0.9, (0, 0, -10)), (1.3, Z))
    a.rot("body", (0, Z), (0.45, (-8, 0, 0)), (0.6, (16, 0, 0), L), (0.9, (14, 0, 0)), (1.3, Z))

    # ink storm (spin from 0.8 s = 16 t, 1.4 s of whirling): arms flung wide, the whole body spinning
    a = m.anim("ink_storm", 2.8)
    a.rot("bone", (0, Z), (0.8, (0, 30, 0)), (2.2, (0, -690, 0), L), (2.8, (0, -720, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_u{side}", (0, Z), (0.8, (10, 0, 20 * -sx)), (2.2, (10, 0, 20 * -sx)), (2.8, Z))
        a.rot(f"arm_d{side}", (0, Z), (0.8, (0, 0, 50 * -sx)), (2.2, (0, 0, 50 * -sx)), (2.8, Z))
    a.pos("body", (0, Z), (0.8, (0, 6, 0)), (2.2, (0, 6, 0)), (2.8, Z))
    a.rot("tail1", (0, Z), (0.8, (30, 0, 0)), (2.2, (30, 0, 0)), (2.8, Z))
    for i in range(8):
        a.rot(f"page_o{i}", (0, Z), (0.8, (-30, 0, 0)), (2.2, (-30, 0, 0)), (2.8, Z))

    # barrage (bursts at 0.6, 0.9, 1.2 s = 12, 18, 24 t): the tomes thrust in turn, faster and faster
    a = m.anim("barrage", 1.8)
    for side, t0 in (("r", 0.6), ("l", 0.9)):
        keys = [(0, Z), (0.4, (30, 0, 0))]
        for t in (t0, t0 + 0.6) if side == "r" else (t0,):
            keys += [(t, (-40, 0, 0), L), (t + 0.15, (20, 0, 0))]
        keys += [(1.45, (10, 0, 0)), (1.8, Z)]
        a.rot(f"arm_u{side}", *keys)
    a.rot("chest", (0, Z), (0.6, (8, -14, 0), L), (0.9, (8, 14, 0), L), (1.2, (10, -10, 0), L), (1.8, Z))
    a.rot("halo", (0, Z), (0.4, (-16, 0, 0)), (1.45, (-16, 0, 0)), (1.8, Z))

    # mirror (impact 0.8 s = 16 t): arms folded over the lantern, then flung wide as the copies split away
    a = m.anim("mirror", 1.6)
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_u{side}", (0, Z), (0.6, (-60, 0, 50 * sx)), (0.8, (0, 0, 40 * -sx), L), (1.2, (0, 0, 36 * -sx)),
              (1.6, Z))
        a.rot(f"arm_d{side}", (0, Z), (0.6, (-40, 0, 30 * sx)), (0.8, (0, 0, 50 * -sx), L), (1.2, (0, 0, 46 * -sx)),
              (1.6, Z))
    a.rot("chest", (0, Z), (0.6, (14, 0, 0)), (0.8, (-12, 0, 0), L), (1.2, (-10, 0, 0)), (1.6, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.6, (0.8, 0.8, 1)), (0.8, (1.3, 1.3, 1), L), (1.2, (1.2, 1.2, 1)), (1.6, (1, 1, 1)))

    # roar (phase two): the halo flares, every arm spread, the lantern blazing upward
    a = m.anim("roar", 2.4)
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_u{side}", (0, Z), (0.5, (-50, 0, 20 * -sx)), (1.9, (-50, 0, 20 * -sx)), (2.4, Z))
        a.rot(f"arm_d{side}", (0, Z), (0.5, (-20, 0, 50 * -sx)), (1.9, (-20, 0, 50 * -sx)), (2.4, Z))
    a.rot("head", (0, Z), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, Z))
    a.rot("chest", (0, Z), (0.5, (-18, 0, 0)), (1.9, (-18, 0, 0)), (2.4, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (1.35, 1.35, 1)), (1.9, (1.35, 1.35, 1)), (2.4, (1, 1, 1)))
    a.pos("body", (0, Z), (0.5, (0, 8, 0)), (1.9, (0, 8, 0)), (2.4, Z))
    for i in range(8):
        a.rot(f"page_o{i}", (0, Z), (0.5, (-34, 0, 0)), (1.9, (-34, 0, 0)), (2.4, Z))

    # stagger: the spell falters, it sinks, pages fold shut, the lantern droops
    a = m.anim("stagger", 2.4)
    a.pos("body", (0, Z), (0.3, (0, -12, 0)), (1.9, (0, -12, 0)), (2.4, Z))
    a.rot("chest", (0, Z), (0.3, (30, 0, 0)), (1.9, (30, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.3, (26, 0, 10)), (1.9, (26, 0, 10)), (2.4, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.3, (0.7, 0.7, 1)), (1.9, (0.7, 0.7, 1)), (2.4, (1, 1, 1)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_u{side}", (0, Z), (0.3, (40, 0, 30 * sx)), (1.9, (40, 0, 30 * sx)), (2.4, Z))
        a.rot(f"arm_d{side}", (0, Z), (0.3, (20, 0, 20 * sx)), (1.9, (20, 0, 20 * sx)), (2.4, Z))
    for i in range(8):
        a.rot(f"page_o{i}", (0, Z), (0.3, (34, 0, 0)), (1.9, (34, 0, 0)), (2.4, Z))
        a.rot(f"page_i{i}", (0, Z), (0.3, (20, 0, 0)), (1.9, (20, 0, 0)), (2.4, Z))


QUILL_ALIGN = (-42, 0, 66)    # quill offset that lines it up with the forearm, nib first
FORE_STRAIGHT = (60, 0, 0)


def _quill_arm(a, keys, length):
    """Lower right arm with a straightened forearm and the quill held in line with it."""
    t0, t1 = keys[0][0], keys[-1][0]
    a.rot("arm_dr", (0, Z), *keys, (length, Z))
    a.rot("fore_dr", (0, Z), (t0, FORE_STRAIGHT), (t1, FORE_STRAIGHT), (length, Z))
    a.rot("quill", (0, Z), (t0, QUILL_ALIGN), (t1, QUILL_ALIGN), (length, Z))


def _tomes(a, keys, length):
    """Both upper arms together: keys are (t, arm offset, forearm offset[, interp])."""
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_u{side}", (0, Z), *[(k[0], (k[1][0], k[1][1], k[1][2] * -sx)) + tuple(k[3:]) for k in keys],
              (length, Z))
        a.rot(f"fore_u{side}", (0, Z), *[(k[0], k[2]) + tuple(k[3:]) for k in keys], (length, Z))
