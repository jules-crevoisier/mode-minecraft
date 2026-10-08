"""The Solar Hierarch (Le Hiérarque solaire): the priest-automaton who tends the sun-engine of the Sun-Engine Ziggurat
and keeps the sun chamber under its lens. About 6 blocks tall with his halo.

Silhouette idea: a tall, narrow gilded priest standing in front of a great brass sun. A sun-disc halo of twelve rays
(long and short in turn) turns slowly behind his head, and three little brass planets orbit it on wire arms like the
orrery on the summit. He wears a long ivory robe of pleated linen that falls to the floor over brass sabatons, a lapis
and gold apron down its front, gilded tassets, a breastplate with the sun-engine's amber lens at its heart and two
flared pauldrons like sun rays. His face is a serene gold mask with amber eyes under a striped nemes headdress and a
tall crown topped by a little glowing sun; a braided false beard.
Strong asymmetry: in his RIGHT hand the sun-staff, taller than he is, crowned by a glowing sun orb in a brass ring with
four rays; on his LEFT forearm a great round mirror-shield of polished silver in a brass rim, a gold sun boss at its
centre and a streak of light across its face.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

GOLD = (214, 170, 72)
GOLD_L = (250, 222, 140)
GOLD_D = (140, 98, 36)
GOLD_DD = (88, 58, 22)
BRASS = (186, 146, 68)
BRASS_L = (232, 200, 118)
BRASS_D = (116, 84, 36)
LAPIS = (40, 72, 166)
LAPIS_L = (86, 124, 214)
LAPIS_D = (22, 38, 96)
LINEN = (226, 214, 184)
LINEN_L = (246, 238, 214)
LINEN_D = (172, 156, 122)
IRON = (58, 52, 52)
IRON_L = (96, 88, 84)
IRON_D = (34, 30, 30)
AMBER = (255, 178, 70)
AMBER_L = (255, 232, 160)
AMBER_D = (214, 110, 30)
SILVER = (196, 210, 222)
SILVER_L = (240, 248, 255)
SILVER_D = (122, 136, 152)
COPPER = (186, 112, 58)
COPPER_L = (228, 156, 96)


# ---------------------------------------------------------------- paint
def gold(seed=0, rim=True, rivets=False):
    """Gilded plate: lit top rim, darker rim, a soft vertical gradient and faint burnish streaks."""
    def f(face, x, y, w, h):
        if face == "top":
            return GOLD_L if (x == 0 or x == w - 1 or y == 0 or y == h - 1) else mix(GOLD, GOLD_L, 0.4)
        if face == "bottom":
            return GOLD_DD
        if rim and (x == 0 or x == w - 1 or y == h - 1) and w > 2 and h > 2:
            return GOLD_D
        if rim and y == 0 and h > 2:
            return GOLD_L
        c = mul(GOLD, 1.08 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if (x + 2 * y + seed) % 11 == 0:
            c = mix(c, GOLD_L, 0.35)                                 # burnish streak
        if rivets and (x in (1, w - 2)) and (y in (1, h - 2)):
            c = GOLD_L
        return c
    return f


def linen(seed=0, hem=False, ragged=False):
    """The ivory robe: long narrow pleats (light and shadow every 3 texels), a gold and lapis hem band."""
    def f(face, x, y, w, h):
        if face == "top":
            return LINEN_D
        if face == "bottom":
            return None if ragged else LINEN_D
        k = x % 3
        c = mul(LINEN, (1.08 if k == 0 else (0.94 if k == 1 else 0.84)) - 0.1 * y / max(1, h)
                + (B.n(x, y, seed) - 0.5) * 0.04)
        if hem:
            if y >= h - 2:
                return GOLD if (x + y) % 2 else GOLD_D
            if y == h - 3:
                return LAPIS
            if y == h - 4:
                return GOLD_L if x % 4 == 0 else GOLD
        return c
    return f


def apron(seed=0, emblem=False):
    """The apron down the robe's front: lapis and gold stripes, gold edges, a sun emblem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return GOLD_D
        if x == 0 or x == w - 1:
            return GOLD_D
        if face not in ("front", "back"):
            return GOLD
        cx = (w - 1) / 2
        if emblem and 2 <= y <= 6:
            d = math.hypot(x - cx, y - 4)
            if d <= 1.6:
                return AMBER_L if d < 0.8 else AMBER
            if d <= 2.4:
                return GOLD_L
        c = LAPIS if (y // 2) % 2 == 0 else GOLD
        if c == LAPIS and (x + y) % 5 == 0:
            c = LAPIS_L
        if y >= h - 2:
            return GOLD_D if x % 2 else GOLD_L                      # fringe
        return mul(c, 1.04 - 0.12 * y / max(1, h))
    return f


def apron_glow(face, x, y, w, h):
    cx = (w - 1) / 2
    if face == "front" and 2 <= y <= 6 and math.hypot(x - cx, y - 4) <= 1.6:
        return AMBER_L
    return None


def nemes(seed=0):
    """The striped headdress: gold and lapis stripes running down."""
    def f(face, x, y, w, h):
        if face == "top":
            return GOLD if x % 2 else LAPIS
        if face == "bottom":
            return GOLD_D
        if face in ("left", "right", "back"):
            return mul(GOLD if (y // 1) % 2 == 0 else LAPIS, 1.04 - 0.14 * y / max(1, h))
        return GOLD if (x % 2 == 0) else LAPIS
    return f


def mask_paint(face, x, y, w, h):
    """The serene gold face: amber eye slits, kohl lines, a straight nose and a thin closed mouth."""
    if face != "front":
        return gold(30)(face, x, y, w, h)
    cx = (w - 1) / 2
    if y == 4 and x in (1, 2, w - 3, w - 2):
        return AMBER_L if x in (2, w - 3) else AMBER
    if y == 3 and x in (1, 2, 3, w - 4, w - 3, w - 2):
        return LAPIS_D                                               # kohl brows
    if y == 5 and x in (0, w - 1):
        return LAPIS_D                                               # kohl wings
    if 4 <= y <= 6 and abs(x - cx) < 0.6:
        return GOLD_L                                                # the nose's ridge
    if y == 8 and abs(x - cx) <= 1.6:
        return GOLD_DD
    if y == h - 1:
        return GOLD_D
    return mul(GOLD, 1.1 - 0.15 * y / max(1, h))


def mask_glow(face, x, y, w, h):
    if face == "front" and y == 4 and x in (1, 2, w - 3, w - 2):
        return AMBER_L if x in (2, w - 3) else AMBER
    return None


def lens_paint(face, x, y, w, h):
    """The sun-engine's amber lens: a bright core and a darker rim of glass."""
    if face in ("top", "bottom", "left", "right"):
        return BRASS_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = math.hypot(x - cx, y - cy)
    return AMBER_L if d < 1.2 else (AMBER if d < 2.3 else AMBER_D)


def lens_glow(face, x, y, w, h):
    if face in ("front", "back"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = math.hypot(x - cx, y - cy)
        return AMBER_L if d < 1.2 else AMBER
    return None


def halo_disc(face, x, y, w, h):
    """A row of the halo's inner disc: gold engraved with concentric rings; the glow ring is painted by halo_glow."""
    if face in ("top", "bottom", "left", "right"):
        return GOLD_D
    return mix(GOLD, GOLD_L, 0.25) if (x + y) % 4 else GOLD


def ray_paint(face, x, y, w, h):
    """A sun ray: a bright edge, a gold body darkening toward the root."""
    if face in ("top", "bottom"):
        return GOLD_L
    if face in ("left", "right"):
        return GOLD_D
    if x == 0:
        return GOLD_L
    if x == w - 1:
        return GOLD_D
    return mul(GOLD, 1.12 - 0.3 * y / max(1, h))


def ray_glow(face, x, y, w, h):
    if face in ("front", "back") and w >= 3 and x == 1 and y < h - 2:
        return AMBER_L if y < 3 else AMBER
    if face in ("front", "back") and w < 3:
        return AMBER_L
    return None


def mirror_paint(x0, y0, r):
    """A row of the mirror's polished face (row origin x0, y0 in the disc, radius r): a cool silver gradient, a
    diagonal streak of reflected light across the whole disc and a thinner one beside it."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return BRASS_D
        if face == "back":
            return BRASS
        gx, gy = x0 + x, y0 + y
        c = mix(SILVER_D, SILVER, 0.25 + 0.6 * (1 - (gy + r) / (2 * r)))
        k = gx + gy
        if -4 <= k <= -1:
            return SILVER_L                                          # the streak of light
        if k in (2, 3):
            return mix(c, SILVER_L, 0.6)
        return c
    return f


mirror_paint.per_row = True


def mirror_glow(x0, y0, r):
    def f(face, x, y, w, h):
        if face == "front" and -4 <= x0 + x + y0 + y <= -1:
            return (220, 236, 255)
        return None
    return f


def staff_paint(face, x, y, w, h):
    """The staff: dark ebony wrapped in gold bands every 6 texels."""
    if face in ("top", "bottom"):
        return GOLD_D
    k = y % 6
    if k == 0:
        return GOLD_L
    if k == 1:
        return GOLD
    return mul((58, 40, 30), 1.0 + (0.12 if x == 0 else 0.0))


def orb_glow(face, x, y, w, h):
    return AMBER_L if (x + y) % 3 else AMBER


def leather(face, x, y, w, h):
    return (112, 52, 34) if (x + y) % 2 else (82, 36, 24)


def iron(seed=0):
    return B.plate(IRON, IRON_D, IRON_L, seed=seed, grad=0.2, worn=0.05)


def brass(seed=0):
    return B.plate(BRASS, BRASS_D, BRASS_L, seed=seed, grad=0.25, worn=0.08)


def bracer(seed=0):
    """Gold bracers with lapis bands."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return GOLD_D
        if y % 4 == 1:
            return LAPIS
        return gold(seed, rim=False)(face, x, y, w, h)
    return f


def disc_rows(m, part, r, z, d, paint, glow=None, step=2):
    """A flat disc of radius r in the x-y plane, built from rows ``step`` texels high, depth d from z."""
    y = -r
    while y < r - 0.01:
        yc = y + step / 2
        half = math.sqrt(max(0.0, r * r - yc * yc))
        w = max(2, int(round(half * 2 / 2)) * 2)
        if getattr(paint, "per_row", False):
            m.box(part, -w / 2, y, z, w, step, d, paint(-w / 2, y, r), glow=glow(-w / 2, y, r) if glow else None)
        else:
            m.box(part, -w / 2, y, z, w, step, d, paint, glow=glow)
        y += step


# ---------------------------------------------------------------- build
def build():
    m = Model("solar_hierarch", seed=417, shadow=1.5, walk_speed=0.7, walk_scale=0.8, glow_pulse=0.04)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -36, 0))
    m.part("skirt", "pelvis", pivot=(0, 0, 0))
    m.part("hem", "skirt", pivot=(0, 17, 0))
    m.part("waist", "pelvis", pivot=(0, -2, 0))
    m.part("chest", "waist", pivot=(0, -9, 0), rot=(2, 0, 0))
    m.part("pauldron_r", "chest", pivot=(-9, -15, 0), rot=(0, 0, 18))
    m.part("pauldron_l", "chest", pivot=(9, -15, 0), rot=(0, 0, -18))
    m.part("neck", "chest", pivot=(0, -17, 0))
    m.part("head", "neck", pivot=(0, -3, 0))
    m.part("crown", "head", pivot=(0, -10.5, 0))
    # the halo turns slowly behind the head; the planets orbit it
    m.part("halo", "chest", pivot=(0, -25, 9))
    m.part("halo_spin", "halo", pivot=(0, 0, 0))
    for k in range(12):
        m.part(f"ray{k}", "halo_spin", pivot=(0, 0, 0), rot=(0, 0, 30 * k))
    m.part("orbit", "halo", pivot=(0, 0, 1.5))
    for i, name in enumerate(("planet_a", "planet_b", "planet_c")):
        m.part(name, "orbit", pivot=(0, 0, 0), rot=(0, 0, 120 * i + 20))
    # right arm: the sun-staff
    m.part("arm_r", "chest", pivot=(-10, -14, 0), rot=(-10, 0, 22))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-50, 0, 0))
    m.part("staff", "fore_r", pivot=(0, 13, 0), rot=(60, 0, -22))
    m.part("staff_head", "staff", pivot=(0, -57, 0))
    # left arm: the mirror-shield
    m.part("arm_l", "chest", pivot=(10, -14, 0), rot=(-20, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-70, 0, 0))
    m.part("shield", "fore_l", pivot=(1, 16, 0), rot=(90, 0, 10))

    # ---- the robe: ivory linen to the floor, an apron down its front, gilded tassets, brass sabatons
    m.box("pelvis", -8, -3, -5, 16, 6, 10, gold(1, rivets=True))
    m.box("skirt", -9, 3, -6, 18, 14, 12, linen(2))
    m.box("hem", -10, 0, -7, 20, 19, 14, linen(3, hem=True))
    m.box("skirt", -3.5, 3, -6.5, 7, 14, 1, apron(4, emblem=True), glow=apron_glow)
    m.box("hem", -3.5, 0, -7.5, 7, 18, 1, apron(5))
    m.box("skirt", -10.5, 2, -5, 2, 10, 10, gold(6))                          # tassets
    m.box("skirt", 8.5, 2, -5, 2, 10, 10, gold(7))
    m.box("skirt", -9.5, 3, 5.5, 19, 2, 1, LAPIS)                             # a lapis sash knotted behind
    m.box("hem", -6, 16, -10, 4, 3, 4, brass(8))                              # sabatons under the hem
    m.box("hem", 2, 16, -10, 4, 3, 4, brass(9))

    # ---- waist: the gear band of the sun-engine
    m.box("waist", -6, -9, -4, 12, 9, 8, iron(10))
    m.box("waist", -6.5, -6, -4.5, 13, 3, 9, B.bands(BRASS, BRASS_D, every=2, seed=11))
    m.box("waist", -7.5, -8, -2, 1, 6, 6, B.cog(BRASS, BRASS_D, teeth=8, faces=("left", "right")))
    m.box("waist", 6.5, -8, -2, 1, 6, 6, B.cog(BRASS, BRASS_D, teeth=8, faces=("left", "right")))

    # ---- the breastplate and the sun-engine lens at its heart
    m.box("chest", -8, -16, -5, 16, 16, 10, gold(12, rivets=True))
    m.box("chest", -3, -12, -6, 6, 6, 1, lens_paint, glow=lens_glow)
    m.box("chest", -4, -13, -6, 8, 1, 1, BRASS_L)
    m.box("chest", -4, -6, -6, 8, 1, 1, BRASS_D)
    m.box("chest", -4, -12, -6, 1, 6, 1, BRASS)
    m.box("chest", 3, -12, -6, 1, 6, 1, BRASS)
    for i in range(4):                                                        # sun rays engraved round the lens
        m.box("chest", -7 + i * 4, -16, -5.5, 2, 2, 1, LAPIS)
    m.box("chest", -6, -18, -4, 12, 3, 8, nemes(13))                          # the gorget
    m.box("chest", -4.5, -15, 5, 9, 12, 3, brass(14))                         # the boiler on his back
    m.box("chest", -1, -23, 6.5, 2, 9, 2, BRASS_D)                            # the halo's mount
    m.box("chest", 3.5, -14, 7.5, 2, 10, 2, COPPER)                           # pipes
    m.box("chest", -5.5, -14, 7.5, 2, 10, 2, COPPER)
    # pauldrons like sun rays
    for side, sx in (("pauldron_r", -1), ("pauldron_l", 1)):
        m.box(side, -4 + sx * 1, -3, -5.5, 8, 5, 11, gold(15 + sx, rivets=True))
        m.box(side, -4 + sx * 3, 1, -5, 8, 3, 10, LAPIS)
        for k, zz in enumerate((-4.5, -1.5, 1.5)):                          # three flared rays
            m.box(side, sx * 4 - (0 if sx > 0 else 3), -5 - k % 2, zz, 3, 2, 3, ray_paint)

    # ---- head: gold mask, striped nemes, tall crown with a little sun, braided beard
    m.box("neck", -2, -3, -2, 4, 3, 4, iron(20))
    m.box("head", -4, -10, -4.5, 8, 10, 8, mask_paint, glow=mask_glow)
    m.box("head", -6, -10.5, -3.5, 12, 9, 8, nemes(21))
    m.box("head", -6, -1.5, -3, 2, 9, 3, nemes(22))                           # lappets over the chest
    m.box("head", 4, -1.5, -3, 2, 9, 3, nemes(23))
    m.box("head", -1, 0, -4.5, 2, 5, 2, nemes(24))                            # the braided false beard
    m.box("crown", -3.5, -4, -3, 7, 4, 6, gold(25))
    m.box("crown", -4, -1, -3.5, 8, 1, 7, LAPIS)
    m.box("crown", -2.5, -10, -2.5, 5, 6, 5, gold(26))
    m.box("crown", -1.5, -14, -1.5, 3, 4, 3, gold(27))
    m.box("crown", -1.5, -17, -1.5, 3, 3, 3, AMBER, glow=orb_glow)            # the crown's little sun
    m.box("crown", -3, -16, -0.5, 1, 1, 1, GOLD_L)
    m.box("crown", 2, -16, -0.5, 1, 1, 1, GOLD_L)

    # ---- the halo: a gold disc, twelve rays (long and short in turn) and a ring; three planets orbit it
    disc_rows(m, "halo_spin", 8.5, 0, 1, halo_disc)
    m.box("halo_spin", -3, -3, -0.5, 6, 6, 1, AMBER, glow=orb_glow)          # the glowing heart of the sun
    for k in range(12):
        p = f"ray{k}"
        if k % 2 == 0:
            m.box(p, -1.5, -20, 0, 3, 11, 1, ray_paint, glow=ray_glow)
            m.box(p, -0.5, -22, 0, 1, 2, 1, GOLD_L, glow=AMBER_L)
        else:
            m.box(p, -1, -16, 0, 2, 7, 1, ray_paint, glow=ray_glow)
        m.box(p, -4, -15, -0.5, 8, 1, 1, BRASS_L if k % 2 else BRASS)
    for name, col, size, r in (("planet_a", COPPER, 4, 27), ("planet_b", LAPIS, 3, 25), ("planet_c", BRASS, 5, 29)):
        m.box(name, -0.5, -r + size, -0.5, 1, r - size - 8, 1, BRASS_D)       # the wire arm
        h = size / 2
        m.box(name, -h, -r, -h, size, size, size,
              B.plate(col, mul(col, 0.6), mix(col, (255, 245, 220), 0.4), seed=40 + size))

    # ---- right arm: the sun-staff
    m.box("arm_r", -2.5, -2, -2.5, 5, 14, 5, bracer(30))
    m.box("arm_r", -3, 10, -3, 6, 3, 6, iron(31))                             # the elbow joint
    m.box("fore_r", -2, 0, -2, 4, 12, 4, bracer(32))
    m.box("fore_r", -2.5, 11, -2.5, 5, 4, 5, iron(33))                        # the fist
    m.box("staff", -1, -52, -1, 2, 78, 2, staff_paint)
    m.box("staff", -1.5, -3, -1.5, 3, 9, 3, leather)                          # the grip
    m.box("staff", -1.5, 26, -1.5, 3, 2, 3, GOLD_D)                           # the butt cap
    m.box("staff", -2, -50, -2, 4, 3, 4, gold(34))                            # the collar under the head
    m.box("staff", -1.5, -53, -1.5, 3, 2, 3, BRASS_L)
    m.box("staff_head", -2.5, -2.5, -2.5, 5, 5, 5, AMBER, glow=orb_glow)      # the sun orb
    m.box("staff_head", -5, -7, -1, 10, 2, 2, brass(35))                     # its ring (an octagon of bars)
    m.box("staff_head", -5, 5, -1, 10, 2, 2, brass(36))
    m.box("staff_head", -7, -5, -1, 2, 10, 2, brass(37))
    m.box("staff_head", 5, -5, -1, 2, 10, 2, brass(38))
    for cx, cy in ((-6, -6), (5, -6), (-6, 5), (5, 5)):
        m.box("staff_head", cx, cy, -0.5, 1, 1, 1, BRASS_L)
    m.box("staff_head", -0.5, -13, -0.5, 1, 6, 1, GOLD_L, glow=AMBER_L)        # four rays
    m.box("staff_head", -13, -0.5, -0.5, 6, 1, 1, GOLD_L, glow=AMBER_L)
    m.box("staff_head", 7, -0.5, -0.5, 6, 1, 1, GOLD_L, glow=AMBER_L)
    m.box("staff_head", -1, -10, -1, 2, 3, 2, GOLD)

    # ---- left arm: the mirror-shield
    m.box("arm_l", -2.5, -2, -2.5, 5, 14, 5, bracer(50))
    m.box("arm_l", -3, 10, -3, 6, 3, 6, iron(51))
    m.box("fore_l", -2, 0, -2, 4, 12, 4, bracer(52))
    m.box("fore_l", -2.5, 11, -2.5, 5, 4, 5, iron(53))
    disc_rows(m, "shield", 11, -2, 1, brass(54))                             # the brass back and rim
    disc_rows(m, "shield", 9, -3, 1, mirror_paint, glow=mirror_glow)        # the polished face
    m.box("shield", -2, -2, -4, 4, 4, 1, gold(55), glow=None)                 # the sun boss
    m.box("shield", -1, -1, -4.5, 2, 2, 1, AMBER, glow=AMBER_L)
    m.box("shield", -1.5, -1.5, -1, 3, 3, 2, IRON_D)                          # the strap mount

    _anims(m)
    return m


Z = (0, 0, 0)


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.rot("halo_spin", (0, Z, "linear"), (4.0, (0, 0, 30), "linear"))       # 12-fold: a seamless slow turn
    idle.rot("orbit", (0, Z, "linear"), (4.0, (0, 0, -360), "linear"))
    idle.pos("chest", (0, Z), (2.0, (0, 0.6, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.5, (3, 6, 0)), (3.0, (0, -5, 0)), (4.0, Z))
    idle.rot("arm_r", (0, Z), (2.0, (-3, 0, 1)), (4.0, Z))
    idle.rot("arm_l", (0, Z), (2.0, (-3, 0, -1)), (4.0, Z))
    idle.rot("hem", (0, Z), (2.0, (1.5, 0, 0)), (4.0, Z))

    walk = m.anim("walk", 2.0)
    walk.rot("hem", (0, (-5, 0, 2)), (0.5, (5, 0, 0)), (1.0, (-5, 0, -2)), (1.5, (5, 0, 0)), (2.0, (-5, 0, 2)))
    walk.rot("skirt", (0, (0, 0, 1.5)), (1.0, (0, 0, -1.5)), (2.0, (0, 0, 1.5)))
    walk.pos("pelvis", (0, Z), (0.5, (0, 0.8, 0)), (1.0, Z), (1.5, (0, 0.8, 0)), (2.0, Z))
    walk.rot("chest", (0, (0, 4, 0)), (1.0, (0, -4, 0)), (2.0, (0, 4, 0)))
    walk.rot("arm_r", (0, (6, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (6, 0, 0)))
    walk.rot("arm_l", (0, (-4, 0, 0)), (1.0, (4, 0, 0)), (2.0, (-4, 0, 0)))

    # sweep (1.6 s): the staff drawn back over his right shoulder (0.7 s = 14 ticks), then swept across his front
    a = m.anim("sweep", 1.6)
    a.rot("arm_r", (0, Z), (0.6, (-100, -30, 60)), (0.7, (-104, -34, 62)), (0.82, (-80, 60, -10), "linear"),
          (1.0, (-76, 64, -14)), (1.6, Z))
    a.rot("fore_r", (0, Z), (0.7, (30, 0, 0)), (0.82, (40, 0, 0), "linear"), (1.6, Z))
    a.rot("staff", (0, Z), (0.7, (-30, 0, 40)), (0.82, (-60, 0, -10), "linear"), (1.6, Z))
    a.rot("chest", (0, Z), (0.7, (-4, -30, 0)), (0.82, (8, 34, 0), "linear"), (1.0, (8, 36, 0)), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.7, (-10, 0, -10)), (0.82, (10, 0, -20), "linear"), (1.6, Z))
    a.rot("hem", (0, Z), (0.7, (0, -8, 0)), (0.9, (0, 10, 0)), (1.6, Z))

    # thrust (1.7 s): the staff levelled at the hip, sun forward (0.8 s = 16 ticks), then driven straight ahead
    a = m.anim("thrust", 1.7)
    a.rot("arm_r", (0, Z), (0.7, (-40, 0, 30)), (0.8, (-42, 0, 32)), (0.9, (-80, 0, 0), "linear"), (1.1, (-80, 0, 0)),
          (1.7, Z))
    a.rot("fore_r", (0, Z), (0.8, (-20, 0, 0)), (0.9, (40, 0, 0), "linear"), (1.1, (40, 0, 0)), (1.7, Z))
    a.rot("staff", (0, Z), (0.8, (-50, 0, 16)), (0.9, (-55, 0, 22), "linear"), (1.1, (-55, 0, 22)), (1.7, Z))
    a.rot("chest", (0, Z), (0.8, (0, 26, 0)), (0.9, (14, -18, 0), "linear"), (1.1, (14, -18, 0)), (1.7, Z))
    a.pos("pelvis", (0, Z), (0.8, (0, -2, 3)), (0.9, (0, -2, -6), "linear"), (1.1, (0, -2, -6)), (1.7, Z))
    a.rot("arm_l", (0, Z), (0.8, (10, 0, -16)), (0.9, (-30, 0, -10), "linear"), (1.7, Z))

    # combo (2.9 s): three blows: a sweep at 0.7 s (14 ticks), a backhand at 1.2 s, an overhead slam at 1.8 s
    a = m.anim("combo", 2.9)
    a.rot("arm_r", (0, Z), (0.6, (-100, -30, 60)), (0.7, (-102, -32, 60)), (0.8, (-80, 60, -10), "linear"),
          (1.1, (-84, 64, -20)), (1.2, (-90, -40, 50), "linear"), (1.5, (-170, 0, 20)), (1.7, (-176, 0, 18)),
          (1.8, (-50, 0, 10), "linear"), (2.2, (-50, 0, 10)), (2.9, Z))
    a.rot("fore_r", (0, Z), (0.7, (30, 0, 0)), (0.8, (40, 0, 0), "linear"), (1.2, (30, 0, 0)), (1.7, (40, 0, 0)),
          (1.8, (10, 0, 0), "linear"), (2.9, Z))
    a.rot("staff", (0, Z), (0.7, (-30, 0, 40)), (0.8, (-60, 0, -10), "linear"), (1.1, (-60, 0, -20)),
          (1.2, (-60, 0, 40), "linear"), (1.5, (150, 0, 0)), (1.7, (150, 0, 0)), (1.8, (-100, 0, 0), "linear"), (2.2, (-100, 0, 0)), (2.9, Z))
    a.rot("chest", (0, Z), (0.7, (-4, -30, 0)), (0.8, (8, 34, 0), "linear"), (1.1, (8, 34, 0)), (1.2, (6, -30, 0), "linear"),
          (1.7, (-16, 0, 0)), (1.8, (24, 0, 0), "linear"), (2.2, (22, 0, 0)), (2.9, Z))
    a.pos("pelvis", (0, Z), (1.7, (0, 1, 0)), (1.8, (0, -4, -2), "linear"), (2.2, (0, -4, -2)), (2.9, Z))
    a.rot("hem", (0, Z), (0.7, (0, -8, 0)), (0.9, (0, 10, 0)), (1.2, (0, -10, 0)), (1.8, (8, 0, 0)), (2.9, Z))

    # bash (1.3 s): the riposte: the mirror drawn in (0.5 s = 10 ticks), then slammed forward
    a = m.anim("bash", 1.3)
    a.rot("arm_l", (0, Z), (0.45, (10, 0, -30)), (0.5, (12, 0, -32)), (0.6, (-60, 0, 10), "linear"), (0.8, (-60, 0, 10)),
          (1.3, Z))
    a.rot("fore_l", (0, Z), (0.5, (-20, 0, 0)), (0.6, (40, 0, 0), "linear"), (0.8, (40, 0, 0)), (1.3, Z))
    a.rot("chest", (0, Z), (0.5, (-4, -24, 0)), (0.6, (12, 20, 0), "linear"), (0.8, (12, 20, 0)), (1.3, Z))
    a.pos("pelvis", (0, Z), (0.5, (0, 0, 2)), (0.6, (0, 0, -5), "linear"), (0.8, (0, 0, -5)), (1.3, Z))

    # flash (1.9 s): the mirror raised high and tilted to catch the light (0.9 s = 18 ticks), then flashed at you
    a = m.anim("flash", 1.9)
    a.rot("arm_l", (0, Z), (0.8, (-110, 0, -30)), (0.9, (-114, 0, -32)), (0.95, (-60, 0, -6), "linear"),
          (1.3, (-60, 0, -6)), (1.9, Z))
    a.rot("fore_l", (0, Z), (0.9, (10, 0, 0)), (0.95, (40, 0, 0), "linear"), (1.3, (40, 0, 0)), (1.9, Z))
    a.rot("shield", (0, Z), (0.9, (-40, 0, 0)), (0.95, (10, 0, 0), "linear"), (1.9, Z))
    a.rot("head", (0, Z), (0.9, (-20, 0, 0)), (0.95, (6, 0, 0), "linear"), (1.9, Z))
    a.rot("chest", (0, Z), (0.9, (-10, -10, 0)), (0.95, (6, 14, 0), "linear"), (1.9, Z))
    a.rot("arm_r", (0, Z), (0.9, (6, 0, 10)), (1.9, Z))

    # sunlance (8.5 s): the staff planted, the mirror lifted to the shaft (1.5 s = 30 ticks); he holds it there,
    # turning slowly, the beam reflected down to the floor (6 s), then lowers it
    a = m.anim("sunlance", 8.5)
    a.rot("arm_l", (0, Z), (1.2, (-150, 0, -20)), (1.5, (-156, 0, -22)), (3.0, (-150, 0, -26)), (4.5, (-156, 0, -18)),
          (6.0, (-150, 0, -26)), (7.5, (-156, 0, -22)), (8.5, Z))
    a.rot("fore_l", (0, Z), (1.5, (30, 0, 0)), (7.5, (30, 0, 0)), (8.5, Z))
    a.rot("shield", (0, Z), (1.5, (-60, 0, 0)), (4.5, (-50, 0, 0)), (7.5, (-60, 0, 0)), (8.5, Z))
    a.rot("arm_r", (0, Z), (1.0, (-20, 0, 26)), (7.5, (-20, 0, 26)), (8.5, Z))
    a.rot("staff", (0, Z), (1.0, (-16, 0, 0)), (7.5, (-16, 0, 0)), (8.5, Z))
    a.rot("head", (0, Z), (1.5, (-30, 0, 0)), (2.0, (14, 0, 0)), (7.5, (14, 0, 0)), (8.5, Z))
    a.rot("chest", (0, Z), (1.5, (-14, 0, 0)), (2.0, (-6, 0, 0)), (7.5, (-6, 0, 0)), (8.5, Z))
    a.scale("halo", (0, (1, 1, 1)), (1.5, (1.25, 1.25, 1)), (7.5, (1.25, 1.25, 1)), (8.5, (1, 1, 1)))

    # orrery (6.7 s): the staff raised high, the halo swelling (1.2 s = 24 ticks); the planets are sent round the
    # chamber on their arms for 4.5 s while he turns the staff like the orrery's spindle
    a = m.anim("orrery", 6.7)
    a.rot("arm_r", (0, Z), (1.0, (-150, 0, 10)), (1.2, (-160, 0, 12)), (2.5, (-160, 0, 12)), (4.0, (-150, 0, 8)),
          (5.7, (-160, 0, 12)), (6.7, Z))
    a.rot("fore_r", (0, Z), (1.2, (40, 0, 0)), (5.7, (40, 0, 0)), (6.7, Z))
    a.rot("staff", (0, Z), (1.2, (120, 0, 0)), (2.7, (120, 180, 0), "linear"), (4.2, (120, 360, 0), "linear"),
          (5.7, (120, 540, 0), "linear"), (5.75, (120, 0, 0), "linear"), (6.7, Z))
    a.rot("orbit", (0, Z), (1.2, (0, 0, 60)), (5.7, (0, 0, 1440), "linear"), (5.75, Z, "linear"), (6.7, Z))
    a.scale("orbit", (0, (1, 1, 1)), (1.2, (1.6, 1.6, 1)), (5.7, (1.6, 1.6, 1)), (6.7, (1, 1, 1)))
    a.rot("arm_l", (0, Z), (1.2, (-40, 0, -50)), (5.7, (-40, 0, -50)), (6.7, Z))
    a.rot("head", (0, Z), (1.2, (-26, 0, 0)), (5.7, (-20, 0, 0)), (6.7, Z))
    a.rot("chest", (0, Z), (1.2, (-12, 0, 0)), (5.7, (-10, 0, 0)), (6.7, Z))

    # flare (3.2 s, phase 2): the staff planted, the halo blazing (1.0 s = 20 ticks); three rings of fire roll out
    # from it at 1.0, 1.6 and 2.2 s
    a = m.anim("flare", 3.2)
    a.rot("arm_r", (0, Z), (0.8, (-150, 0, 20)), (1.0, (-156, 0, 22)), (1.05, (-60, 0, 20), "linear"),
          (1.55, (-90, 0, 20)), (1.6, (-60, 0, 20), "linear"), (2.15, (-90, 0, 20)), (2.2, (-60, 0, 20), "linear"),
          (2.6, (-60, 0, 20)), (3.2, Z))
    a.rot("staff", (0, Z), (1.0, (150, 0, 0)), (1.05, (60, 0, 0), "linear"), (2.6, (60, 0, 0)), (3.2, Z))
    a.scale("halo", (0, (1, 1, 1)), (1.0, (1.4, 1.4, 1)), (1.05, (1.0, 1.0, 1), "linear"), (1.55, (1.3, 1.3, 1)),
            (1.6, (1.0, 1.0, 1), "linear"), (2.15, (1.3, 1.3, 1)), (2.2, (1.0, 1.0, 1), "linear"), (3.2, (1, 1, 1)))
    a.rot("arm_l", (0, Z), (1.0, (-30, 0, -60)), (2.6, (-30, 0, -60)), (3.2, Z))
    a.rot("chest", (0, Z), (1.0, (-16, 0, 0)), (1.05, (10, 0, 0), "linear"), (2.6, (8, 0, 0)), (3.2, Z))
    a.rot("head", (0, Z), (1.0, (-24, 0, 0)), (1.05, (4, 0, 0), "linear"), (3.2, Z))

    # descent (2.3 s, phase 2): crouched, the staff raised two-handed (0.9 s = 18 ticks); he leaps and comes down on
    # the marked ring staff first at 1.35 s
    a = m.anim("descent", 2.3)
    a.pos("pelvis", (0, Z), (0.8, (0, -7, 0)), (0.9, (0, -7, 0)), (1.0, (0, 2, 0), "linear"), (1.3, (0, 2, 0)),
          (1.35, (0, -8, 0), "linear"), (1.7, (0, -6, 0)), (2.3, Z))
    a.rot("arm_r", (0, Z), (0.8, (-170, 0, 14)), (0.9, (-176, 0, 12)), (1.3, (-176, 0, 12)),
          (1.35, (-50, 0, 10), "linear"), (1.8, (-50, 0, 10)), (2.3, Z))
    a.rot("staff", (0, Z), (0.9, (150, 0, 0)), (1.3, (150, 0, 0)), (1.35, (-110, 0, 0), "linear"), (1.8, (-110, 0, 0)),
          (2.3, Z))
    a.rot("arm_l", (0, Z), (0.9, (-60, 0, -20)), (1.35, (-20, 0, -30), "linear"), (2.3, Z))
    a.rot("chest", (0, Z), (0.9, (26, 0, 0)), (1.0, (-10, 0, 0), "linear"), (1.3, (-12, 0, 0)), (1.35, (30, 0, 0), "linear"),
          (1.8, (26, 0, 0)), (2.3, Z))
    a.rot("hem", (0, Z), (1.0, (20, 0, 0)), (1.3, (22, 0, 0)), (1.45, (-6, 0, 0)), (2.3, Z))

    # eclipse (3.5 s, phase 3, invulnerable): he kneels, staff and mirror crossed over his head (1.5 s = 30 ticks);
    # the mirror swings over the sun-orb like a moon over the sun: the chamber goes dark
    a = m.anim("eclipse", 3.5)
    a.pos("pelvis", (0, Z), (1.2, (0, -9, 0)), (1.5, (0, -10, 0)), (2.5, (0, -10, 0)), (3.5, Z))
    a.rot("arm_r", (0, Z), (1.2, (-160, 0, -20)), (1.5, (-166, 0, -24)), (2.5, (-166, 0, -24)), (3.5, Z))
    a.rot("staff", (0, Z), (1.2, (160, 0, 20)), (2.5, (160, 0, 20)), (3.5, Z))
    a.rot("arm_l", (0, Z), (1.2, (-160, 0, 20)), (1.45, (-166, 0, 24)), (1.55, (-150, 0, 4), "linear"),
          (2.5, (-150, 0, 4)), (3.5, Z))
    a.rot("shield", (0, Z), (1.45, (-60, 0, 0)), (1.55, (-80, 0, 0), "linear"), (2.5, (-80, 0, 0)), (3.5, Z))
    a.rot("head", (0, Z), (1.5, (-40, 0, 0)), (2.5, (-34, 0, 0)), (3.5, Z))
    a.rot("hem", (0, Z), (1.2, (30, 0, 0)), (2.5, (30, 0, 0)), (3.5, Z))
    a.scale("halo", (0, (1, 1, 1)), (1.5, (1.5, 1.5, 1)), (2.5, (1.5, 1.5, 1)), (3.5, (1, 1, 1)))

    # sigils (5.3 s, phase 3): the staff raised (0.8 s = 16 ticks); he blinks to three sun-sigils (0.8, 1.9, 3.0 s)
    # and strikes the floor of each with the staff 0.4 s after landing; stays bowed after the third
    a = m.anim("sigils", 5.3)
    arm, staff, chest = [(0, Z), (0.7, (-150, 0, 14)), (0.8, (-156, 0, 14))], [(0, Z), (0.8, (150, 0, 0))], \
        [(0, Z), (0.8, (-12, 0, 0))]
    for land in (0.8, 1.9, 3.0):
        arm += [(land + 0.3, (-156, 0, 14)), (land + 0.4, (-50, 0, 10), "linear")]
        staff += [(land + 0.3, (150, 0, 0)), (land + 0.4, (-100, 0, 0), "linear")]
        chest += [(land + 0.3, (-12, 0, 0)), (land + 0.4, (26, 0, 0), "linear")]
        if land < 3:
            arm += [(land + 0.9, (-150, 0, 14)), (land + 1.1, (-156, 0, 14))]
            staff += [(land + 0.9, (150, 0, 0)), (land + 1.1, (150, 0, 0))]
            chest += [(land + 0.9, (-12, 0, 0)), (land + 1.1, (-12, 0, 0))]
    arm += [(4.4, (-50, 0, 10)), (5.3, Z)]
    staff += [(4.4, (-100, 0, 0)), (5.3, Z)]
    chest += [(4.4, (26, 0, 0)), (5.3, Z)]
    a.rot("arm_r", *arm)
    a.rot("staff", *staff)
    a.rot("chest", *chest)
    a.rot("arm_l", (0, Z), (0.8, (-40, 0, -40)), (4.4, (-40, 0, -40)), (5.3, Z))

    # reel (2.0 s): the mirror knocked aside, he staggers back open
    a = m.anim("reel", 2.0)
    a.rot("arm_l", (0, Z), (0.15, (-40, 0, -80), "linear"), (1.5, (-36, 0, -76)), (2.0, Z))
    a.rot("fore_l", (0, Z), (0.15, (40, 0, 0), "linear"), (1.5, (40, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.15, (-16, 20, 0), "linear"), (1.5, (-14, 18, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.15, (-14, 10, 0), "linear"), (1.5, (-12, 10, 0)), (2.0, Z))
    a.pos("pelvis", (0, Z), (0.2, (0, -1, 3)), (1.5, (0, -1, 3)), (2.0, Z))

    # roar (phase two): staff and mirror flung wide, head thrown back, the halo blazing
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, Z), (0.6, (-60, 0, 70)), (1.6, (-64, 0, 74)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.6, (-40, 0, -70)), (1.6, (-44, 0, -74)), (2.0, Z))
    a.rot("head", (0, Z), (0.6, (-36, 0, 0)), (1.6, (-34, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.6, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.6, (1.4, 1.4, 1)), (1.6, (1.4, 1.4, 1)), (2.0, (1, 1, 1)))

    # stagger: he sags, the staff drooping, the mirror hanging
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, Z), (0.3, (0, -8, 0)), (1.6, (0, -8, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.3, (30, 0, -8)), (1.6, (32, 0, -8)), (2.0, Z))
    a.rot("head", (0, Z), (0.3, (24, 0, 12)), (1.6, (26, 0, 12)), (2.0, Z))
    a.rot("arm_r", (0, Z), (0.3, (30, 0, -6)), (1.6, (32, 0, -6)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.3, (36, 0, 4)), (1.6, (38, 0, 4)), (2.0, Z))
    a.rot("hem", (0, Z), (0.3, (6, 0, 0)), (2.0, Z))
