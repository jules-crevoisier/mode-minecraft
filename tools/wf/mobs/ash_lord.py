"""The Ash Lord (Le Seigneur des Cendres): a 4.7-block knight in blackened, ember-cracked plate.

Silhouette idea: a horned and crowned great helm (the left horn broken), a huge right pauldron with
flaming spikes, a long cape torn into three smouldering strips, and a greatsword longer than a man,
held low with its tip trailing embers on the ground. Lava glows through the cracks of every plate.
"""
import random

from ..models import FACE_ID, Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
STEEL = (50, 46, 52)          # blackened plate
STEEL_HI = (112, 104, 108)    # worn top edges
STEEL_LO = (24, 22, 26)       # undersides, rims
BRONZE = (146, 98, 50)        # filigree trims
BRONZE_HI = (204, 150, 80)
EMBER = (226, 92, 28)         # crack colour in the base texture
EMBER_HOT = (255, 196, 96)    # crack cores (glow layer)
EMBER_GLOW = (255, 132, 40)
CLOTH = (60, 28, 28)          # smouldering cape
CLOTH_D = (36, 18, 20)
CLOTH_L = (86, 42, 36)
ASH = (92, 86, 82)
HORN = (128, 116, 104)
HORN_TIP = (34, 28, 26)
LEATHER = (66, 42, 30)
BLADE = (66, 60, 62)
BLADE_EDGE = (150, 140, 134)


def hsh(*vals):
    """Deterministic hash of integers -> 0..1 (stable across runs, unlike hash() on strings)."""
    h = 2166136261
    for v in vals:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 0xFFFFFFFF


_CRACKS = {}


def crack_map(w, h, seed, n=2, reach=None):
    """Jagged lava cracks on a w x h face: {(x, y): 2 core | 1 tail} plus the set of halo texels."""
    key = (w, h, seed, n, reach)
    if key in _CRACKS:
        return _CRACKS[key]
    rng = random.Random(seed * 7919 + w * 131 + h * 17)
    pts = {}

    def walk(x, y, dx, dy, length, depth):
        for k in range(length):
            if 0 <= x < w and 0 <= y < h:
                pts[(x, y)] = max(pts.get((x, y), 0), 2 if k < length - 2 else 1)
            r = rng.random()
            if r < 0.42:
                x += dx
            elif r < 0.84:
                y += dy
            else:
                x += dx
                y += dy
            if depth < 2 and rng.random() < 0.10:
                walk(x, y, -dx if rng.random() < 0.5 else dx, dy, max(2, (length - k) // 2), depth + 1)
    for _ in range(n if w * h > 12 else 0):
        x, y = rng.randrange(w), rng.randrange(h)
        dx, dy = rng.choice((1, -1)), rng.choice((1, -1))
        walk(x, y, dx, dy, reach or rng.randint(max(3, (w + h) // 4), max(4, (w + h) // 2)), 0)
    halo = set()
    for (x, y) in pts:
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ox, y + oy)
            if q not in pts and 0 <= q[0] < w and 0 <= q[1] < h:
                halo.add(q)
    _CRACKS[key] = (pts, halo)
    return pts, halo


def plate(seed, base=STEEL, cracks=0, rim=True, rivets=False, trim=None, reach=None, faces=None, border=False):
    """Blackened plate lit from above-left: bevelled edges (bright top, dark bottom), a hammered mottle,
    an optional bronze filigree border or trim line, rivets and a few long lava cracks.
    Returns (paint, glow)."""
    def crack(face, w, h):
        if not cracks or (faces and face not in faces):
            return {}, set()
        return crack_map(w, h, seed * 13 + FACE_ID[face], cracks, reach)

    def paint(face, x, y, w, h):
        pts, halo = crack(face, w, h)
        if (x, y) in pts:
            return EMBER_HOT if pts[(x, y)] == 2 else EMBER
        mottle = 1 + (hsh(seed, x // 2, y // 2, FACE_ID[face]) - 0.5) * 0.12 + (hsh(seed, x, y) - 0.5) * 0.05
        c = mul(base, mottle)
        side = face not in ("top", "bottom")
        if face == "top":
            c = mix(c, STEEL_HI, 0.22)
        elif face == "bottom":
            c = mix(c, STEEL_LO, 0.55)
        elif face in ("back",):
            c = mul(c, 0.92)
        if side and h > 2:
            if y == 0:
                c = mix(c, STEEL_HI, 0.6)
            elif y == h - 1:
                c = mix(c, STEEL_LO, 0.7)
            if rim and w > 2 and x == 0:
                c = mix(c, STEEL_HI, 0.25)
            elif rim and w > 2 and x == w - 1:
                c = mix(c, STEEL_LO, 0.5)
        if border and side and w > 6 and h > 5:
            on = (x in (1, w - 2) and 1 <= y <= h - 2) or (y in (1, h - 2) and 1 <= x <= w - 2)
            if on:
                c = BRONZE_HI if (x + y) % 4 == 0 else BRONZE
            elif (x in (2, w - 3) and 2 <= y <= h - 3) or (y in (2, h - 3) and 2 <= x <= w - 3):
                c = mix(c, STEEL_LO, 0.5)  # engraved shadow inside the filigree
        if trim is not None and side and y == trim and 0 < x < w - 1:
            c = BRONZE_HI if x % 3 else BRONZE
        if rivets and side and w > 5 and h > 5 and x in (1, w - 2) and y in (1, h - 2):
            return (150, 136, 120)
        if (x, y) in halo:
            c = mix(c, (120, 42, 20), 0.5)
        return c

    def glow(face, x, y, w, h):
        pts, _ = crack(face, w, h)
        v = pts.get((x, y))
        if v == 2:
            return EMBER_HOT
        if v == 1:
            return EMBER_GLOW
        return None
    return paint, glow


def seam(seed=0):
    """Molten seam showing between plates (waist, neck, joints)."""
    def paint(face, x, y, w, h):
        return EMBER_HOT if hsh(seed, x, y) < 0.35 else EMBER

    def glow(face, x, y, w, h):
        return EMBER_HOT if hsh(seed, x, y) < 0.35 else EMBER_GLOW
    return paint, glow


def lames(seed, rows=3, base=STEEL, cracks=0):
    """Overlapping horizontal lames (articulated plates): every band lit on top, shadowed below."""
    p, g = plate(seed, base, cracks)

    def paint(face, x, y, w, h):
        if face in ("top", "bottom"):
            return p(face, x, y, w, h)
        band = max(2, h // rows)
        k = y % band
        c = p(face, x, y, w, h)
        if c in (EMBER, EMBER_HOT):
            return c
        if k == 0:
            return mix(c, STEEL_HI, 0.45)
        if k == band - 1:
            return mix(c, STEEL_LO, 0.65)
        return c
    return paint, g


def cloth(seed, ragged=6, burn=True, base=CLOTH):
    """Smouldering cloth: soft vertical folds darkening toward the hem, ash dusting, a ragged burnt hem
    with a line of embers along it."""
    def hem(x, w, h):
        return h - 1 - int(hsh(seed, x // 2) * ragged) if ragged else h

    def paint(face, x, y, w, h):
        if face in ("front", "back") or (face in ("left", "right") and ragged):
            cut = hem(x, w, h)
            if y > cut:
                return None
            if burn and y == cut:
                return EMBER
            if burn and y >= cut - 2:
                return mix((30, 16, 14), CLOTH_D, 0.3 * (cut - y))
        phase = (x + 2 * hsh(seed, x // 3)) / 3.0
        fold = abs(((phase % 2.0) - 1.0))  # 0 at a crease, 1 on the crest of a fold
        c = mix(CLOTH_D, CLOTH_L, fold * 0.8)
        c = mix(c, (28, 14, 14), min(0.45, y / max(1, h) * 0.5))
        if hsh(seed, x, y) < 0.04:
            c = mix(c, ASH, 0.5)
        return c

    def glow(face, x, y, w, h):
        if not burn or face not in ("front", "back"):
            return None
        return EMBER_GLOW if y == hem(x, w, h) else None
    return paint, glow


def horn(seed, tip=False):
    def paint(face, x, y, w, h):
        t = x / max(1, w - 1)
        c = mix(HORN, HORN_TIP, t * 0.8 if not tip else 0.6 + t * 0.4)
        if x % 2 == 0:
            c = mul(c, 0.82)  # growth rings
        if face == "top":
            c = mix(c, (130, 116, 104), 0.25)
        return c
    return paint


def blade(seed, core=True, width_rows=None):
    """Blade flat (the x faces of a blade cube running along z): bevelled edges and a lava core channel."""
    def paint(face, x, y, w, h):
        if face in ("left", "right"):
            mid = (h - 1) / 2
            dist = abs(y - mid)
            if core and dist < 1.0:
                return EMBER_HOT if hsh(seed, x // 2) < 0.3 else EMBER
            if y == 0 or y == h - 1:
                return BLADE_EDGE
            if y == 1 or y == h - 2:
                return mix(BLADE, BLADE_EDGE, 0.35)
            c = mul(BLADE, 1 + (hsh(seed, x, y) - 0.5) * 0.12)
            if core and dist < 2.0:
                c = mix(c, (120, 40, 20), 0.5)
            return c
        if face in ("top", "bottom"):
            return BLADE_EDGE
        return mix(BLADE, BLADE_EDGE, 0.4)

    def glow(face, x, y, w, h):
        if core and face in ("left", "right") and abs(y - (h - 1) / 2) < 1.0:
            return EMBER_HOT if hsh(seed, x // 2) < 0.3 else EMBER_GLOW
        return None
    return paint, glow


def solid(c, glow=None):
    return c, glow


def build():
    m = Model("ash_lord", seed=55, shadow=1.3, walk_speed=0.7, walk_scale=1.0)

    def box(part, x, y, z, w, h, d, mat, grow=0.0):
        paint, glow = mat if isinstance(mat, tuple) and len(mat) == 2 and not isinstance(mat[0], int) else (mat, None)
        m.box(part, x, y, z, w, h, d, paint, glow=glow, grow=grow)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -30, 0))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=(4, 0, 0))
    m.part("head", "torso", pivot=(0, -26, -1), rot=(-4, 0, 0))
    m.part("horn_r", "head", pivot=(-5, -6, 0), rot=(0, 8, 4))
    m.part("horn_r2", "horn_r", pivot=(-7, 0, 0), rot=(0, 0, 22))
    m.part("horn_r3", "horn_r2", pivot=(-7, 0, 0), rot=(0, -18, 34))
    m.part("horn_r4", "horn_r3", pivot=(-6, 0, 0), rot=(0, -30, 34))
    m.part("horn_l", "head", pivot=(5, -6, 0), rot=(0, -8, -4))
    m.part("horn_l2", "horn_l", pivot=(7, 0, 0), rot=(0, 0, -22))
    m.part("cape", "torso", pivot=(0, -23, 8), rot=(7, 0, 0))
    m.part("cape_a", "cape", pivot=(-9, 18, 0), rot=(3, 0, 2))
    m.part("cape_b", "cape", pivot=(0, 18, 0), rot=(5, 0, 0))
    m.part("cape_c", "cape", pivot=(9, 18, 0), rot=(2, 0, -2))
    m.part("tabard", "hips", pivot=(0, 2, -7), rot=(-3, 0, 0))
    m.part("arm_r", "torso", pivot=(-13, -20, 0))
    m.part("spikes_r", "arm_r", pivot=(-4, -7, 0), rot=(0, 0, -22))
    m.part("forearm_r", "arm_r", pivot=(0, 12, 0), rot=(-28, 0, 0))
    m.part("sword", "forearm_r", pivot=(0, 14, 0), rot=(58, 0, 0))
    m.part("arm_l", "torso", pivot=(12, -20, 0), rot=(0, 0, -4))
    m.part("forearm_l", "arm_l", pivot=(0, 12, 0), rot=(-12, 0, 0))
    m.part("leg_r", "bone", pivot=(-5, -30, 0))
    m.part("shin_r", "leg_r", pivot=(0, 14, 0))
    m.part("leg_l", "bone", pivot=(5, -30, 0))
    m.part("shin_l", "leg_l", pivot=(0, 14, 0))

    # ------------------------------------------------------------------ hips and legs
    box("hips", -9, -4, -6, 18, 7, 12, plate(1, trim=1))
    box("hips", -8, -6, -5, 16, 2, 10, seam(1))                                 # molten waist seam
    box("hips", -3, -3, -7, 6, 4, 1, solid(lambda f, x, y, w, h: BRONZE_HI if (x + y) % 2 else BRONZE))
    box("hips", -1, -2, -8, 2, 2, 1, solid(EMBER_HOT, EMBER_HOT))              # ember stone in the buckle
    box("tabard", -5, 0, -1, 10, 18, 1, cloth(3, ragged=5))
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        box(leg, -4, 0, -4, 8, 14, 8, plate(10 + sx, cracks=1 if sx > 0 else 0, reach=9))
        box(leg, -5, -2, -6, 10, 9, 2, lames(12 + sx, rows=3))                    # front tasset
        box(leg, -6 if sx < 0 else 4, -2, -5, 2, 10, 10, lames(14 + sx, rows=3))  # outer tasset
        box(shin, -3, -1, -3, 6, 2, 6, seam(2 + sx))                              # knee glow
        box(shin, -4, 1, -4, 8, 11, 8, plate(16 + sx, border=True))
        box(shin, -3, -2, -6, 6, 5, 2, plate(18 + sx))                            # knee cop
        box(shin, -1, -1, -8, 2, 2, 2, solid(STEEL_HI))                           # knee spike
        box(shin, -5, 12, -7, 10, 4, 11, plate(20 + sx, trim=0))                  # sabaton
        box(shin, -4, 13, -9, 8, 3, 2, plate(22 + sx))                            # pointed toe

    # ------------------------------------------------------------------ torso
    box("torso", -8, -8, -5, 16, 8, 10, lames(30, rows=3))                     # banded abdomen
    box("torso", -7, -10, -4, 14, 2, 8, seam(4))                               # molten seam under the chest
    chest_p, chest_g = plate(31, rivets=True, border=True)
    heart = crack_map(22, 14, 777, 5, 7)[0]

    def chest_front(f, x, y, w, h):
        # the furnace heart: a core under the breastbone with jagged cracks radiating from it
        dx, dy = x - w / 2 + 0.5, y - 6
        if abs(dx) + abs(dy) < 1.6:
            return EMBER_HOT
        if abs(dx) + abs(dy) < 2.6:
            return EMBER
        if (x, y) in heart and abs(dx) < 8:
            return EMBER if heart[(x, y)] == 1 else EMBER_HOT
        return chest_p(f, x, y, w, h)

    def chest_front_glow(f, x, y, w, h):
        dx, dy = x - w / 2 + 0.5, y - 6
        if abs(dx) + abs(dy) < 1.6:
            return (255, 244, 190)
        if abs(dx) + abs(dy) < 2.6:
            return EMBER_HOT
        if (x, y) in heart and abs(dx) < 8:
            return EMBER_GLOW
        return None
    box("torso", -11, -23, -7, 22, 13, 13, ({"front": chest_front, "*": chest_p}, {"front": chest_front_glow}))
    box("torso", -2, -22, -8, 4, 3, 1, plate(35))                              # breastbone ridge (above the heart)
    box("torso", -12, -24, -3, 24, 5, 10, plate(32, trim=4))                   # shoulder yoke
    box("torso", -6, -27, -5, 12, 4, 10, lames(33, rows=2))                    # gorget
    box("torso", -4, -28, -4, 8, 1, 8, seam(5))                                # glow at the neck
    box("torso", -9, -26, 1, 18, 4, 7, cloth(34, ragged=0, burn=False))        # cloth collar under the cape

    # ------------------------------------------------------------------ head: crowned great helm
    helm_p, _ = plate(41, border=False)

    def visor(f, x, y, w, h):
        if y in (3, 4) and 0 < x < w - 1:
            return (22, 10, 8) if y == 4 else EMBER   # the burning slit
        if x in (w // 2 - 1, w // 2) and 4 < y < h - 1:
            return (22, 10, 8)
        if 4 < y < h - 1 and (x + y) % 3 == 0 and x not in (0, w - 1):
            return (30, 26, 30)                        # breathing holes
        return helm_p(f, x, y, w, h)

    def visor_glow(f, x, y, w, h):
        if y == 3 and 0 < x < w - 1:
            return EMBER_HOT if 1 < x < w - 2 else EMBER_GLOW
        if y == 4 and x in (2, w - 3):
            return (255, 244, 190)  # two burning eyes inside the slit
        return None
    box("head", -5, -11, -5, 10, 11, 10, plate(40, rim=True))
    box("head", -4, -9, -6, 8, 9, 1, ({"front": visor, "*": helm_p}, {"front": visor_glow}))
    box("head", -1, -11, -7, 2, 8, 1, plate(42))                               # nasal ridge
    box("head", -6, -4, -6, 12, 4, 11, lames(43, rows=2))                      # bevor
    # crown: a bronze circlet with tall black-iron points, the front one carrying an ember
    def crown_band(f, x, y, w, h):
        if f in ("top", "bottom"):
            return None  # an open ring: the helm shows through
        return BRONZE_HI if y == 0 else BRONZE if (x % 4) else EMBER

    box("head", -6, -13, -6, 12, 2, 12, (crown_band, {"side": lambda f, x, y, w, h: EMBER_GLOW if y == 1 and x % 4 == 0 else None}))

    def point(f, x, y, w, h):
        if y == 0:
            return BRONZE_HI
        if y >= h - 2:
            return BRONZE
        return mix(STEEL, STEEL_HI, 0.35 if f in ("front", "left") else 0.05)
    for (x, z, hgt, wx, wz) in ((-1, -6, 11, 2, 1), (-5, -6, 7, 2, 1), (3, -6, 7, 2, 1), (-6, -2, 6, 1, 2),
                                (5, -2, 6, 1, 2), (-6, 3, 5, 1, 2), (5, 3, 5, 1, 2), (-1, 5, 6, 2, 1)):
        box("head", x, -13 - hgt, z, wx, hgt, wz, (point, None))
    box("head", -1, -21, -7, 2, 3, 1, solid(EMBER_HOT, (255, 244, 190)))
    # horns: the right sweeps out, up and forward like a crescent; the left is snapped, glowing at the break
    box("horn_r", -7, -3, -3, 7, 5, 5, horn(1))
    box("horn_r2", -7, -2, -2, 7, 4, 4, horn(2))
    box("horn_r3", -6, -2, -2, 6, 3, 3, horn(3, tip=True))
    box("horn_r4", -6, -1, -1, 6, 2, 2, horn(4, tip=True))
    box("horn_l", 0, -3, -3, 7, 5, 5, horn(5))
    box("horn_l2", 0, -2, -2, 4, 4, 4, ({"*": horn(6), "left": lambda f, x, y, w, h: EMBER_HOT if (x + y) % 3 == 0 else EMBER},
                                        {"left": lambda f, x, y, w, h: EMBER_HOT if (x + y) % 3 == 0 else EMBER_GLOW}))

    # ------------------------------------------------------------------ cape (three smouldering strips)
    box("cape", -13, 0, 0, 26, 19, 1, cloth(60, ragged=0, burn=False))
    box("cape", -14, -2, -1, 28, 3, 3, cloth(64, ragged=0, burn=False))     # rolled top over the pauldrons
    box("cape_a", -5, 0, 0, 9, 23, 1, cloth(61, ragged=6))
    box("cape_b", -4, 0, 0, 8, 17, 1, cloth(62, ragged=5))
    box("cape_c", -4, 0, 0, 9, 27, 1, cloth(63, ragged=7))

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        if sx < 0:
            # the sword arm: a towering layered pauldron, cracked through, with three flaming spikes
            box(arm, -9, -7, -7, 12, 9, 14, plate(70, cracks=1, reach=12, trim=1, border=False, rivets=True))
            box(arm, -10, 1, -6, 11, 4, 12, lames(71, rows=2))
            for i, (z, hgt) in enumerate(((-5, 7), (-1, 10), (3, 6))):
                box("spikes_r", -2, -hgt, z, 3, hgt, 3, plate(72 + i, rim=True))
                box("spikes_r", -1, -hgt - 3, z + 1, 1, 3, 1, solid(BRONZE_HI))
                box("spikes_r", -2, -hgt - 1, z, 3, 1, 3, solid(EMBER_HOT, EMBER_HOT))
        else:
            box(arm, -2, -6, -6, 10, 8, 12, plate(75, trim=1, border=False))
            box(arm, -1, 1, -5, 9, 3, 10, lames(76, rows=2))
            box(arm, 0, -7, -2, 6, 1, 4, solid(BRONZE_HI))  # cape clasp
        box(arm, -4 if sx < 0 else -3, 0, -4, 7, 12, 7, lames(77 + sx, rows=4))
        box(fore, -3 if sx < 0 else -2, -1, -3, 5, 2, 6, seam(6 + sx))              # elbow glow
        box(fore, -5 if sx < 0 else -4, 0, -5, 9, 4, 10, plate(79 + sx, trim=0))    # flared cuff
        box(fore, -4 if sx < 0 else -3, 4, -4, 7, 8, 8, plate(81 + sx, border=True))
        box(fore, -4 if sx < 0 else -3, 11, -4, 7, 6, 8, plate(83 + sx))            # gauntlet fist

    # ------------------------------------------------------------------ the greatsword (blade along -z)
    box("sword", -1, -1, -1, 2, 2, 9, (lambda f, x, y, w, h: LEATHER if (x + y) % 3 else mul(LEATHER, 0.7), None))
    box("sword", -2, -2, 8, 4, 4, 3, plate(90))                                # pommel
    box("sword", -1, -1, 11, 2, 2, 1, solid(EMBER_HOT, EMBER_HOT))
    box("sword", -2, -9, -4, 4, 18, 3, plate(91, trim=None, border=False))     # crossguard
    box("sword", -2, -11, -5, 4, 2, 3, solid(BRONZE_HI))                        # guard tips
    box("sword", -2, 9, -5, 4, 2, 3, solid(BRONZE_HI))
    box("sword", -1, -2, -5, 2, 4, 1, solid(EMBER_HOT, EMBER_HOT))              # ember set in the guard
    box("sword", -1, -4, -40, 2, 8, 35, blade(94))
    box("sword", -1, -3, -46, 2, 6, 6, blade(95))
    box("sword", -1, -2, -50, 2, 4, 4, blade(96, core=False))
    box("sword", -1, -1, -53, 2, 2, 3, blade(97, core=False))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.2)
    idle.rot("torso", (0, (0, 0, 0)), (1.6, (2.5, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.6, (-3, -4, 0)), (3.2, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.6, (-3, 0, -2)), (3.2, (0, 0, 0)))
    idle.rot("sword", (0, (0, 0, 0)), (1.6, (-3, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.6, (4, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("cape_a", (0, (0, 0, 0)), (1.1, (6, 0, 3)), (2.2, (2, 0, -2)), (3.2, (0, 0, 0)))
    idle.rot("cape_b", (0, (0, 0, 0)), (0.8, (4, 0, 0)), (2.0, (9, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("cape_c", (0, (0, 0, 0)), (1.4, (8, 0, -3)), (2.6, (3, 0, 1)), (3.2, (0, 0, 0)))
    idle.pos("hips", (0, (0, 0, 0)), (1.6, (0, -0.6, 0)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (22 * sign, 0, 0)), (0.9, (-22 * sign, 0, 0)), (1.8, (22 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, (0, 0, 0)), (0.45, (28 if sign > 0 else 0, 0, 0)), (0.9, (0, 0, 0)),
                 (1.35, (28 if sign < 0 else 0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_l", (0, (-16, 0, 0)), (0.9, (16, 0, 0)), (1.8, (-16, 0, 0)))
    walk.rot("arm_r", (0, (5, 0, 0)), (0.9, (-5, 0, 0)), (1.8, (5, 0, 0)))
    walk.rot("torso", (0, (0, 4, 0)), (0.9, (0, -4, 0)), (1.8, (0, 4, 0)))
    walk.rot("cape", (0, (10, 0, 0)), (0.9, (14, 0, 0)), (1.8, (10, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.45, (0, -1.2, 0)), (0.9, (0, 0, 0)), (1.35, (0, -1.2, 0)), (1.8, (0, 0, 0)))
    _actions(m)
    return m


def _actions(m):
    """Every action: a long readable wind-up, a fast linear strike, a recovery that ends at rest.
    Impact times (s) x 20 = wind-up ticks in AshLord.java."""
    Z = (0, 0, 0)
    ALONG = 32   # sword offset that lines the blade up with the forearm (rest tilt is 58 degrees)
    CROSS = -58  # sword offset that holds the blade square to the forearm
    # combo 1: the blade cocked far out to his right, then a flat sweep across to his left (impact 0.70 s)
    a = m.anim("combo1", 1.4)
    a.rot("torso", (0, Z), (0.6, (-4, 55, 0)), (0.7, (8, -50, 0), "linear"), (0.95, (8, -55, 0)), (1.4, Z))
    a.rot("arm_r", (0, Z), (0.6, (-25, 35, 85)), (0.7, (-85, -75, 0), "linear"), (0.95, (-80, -80, 0)), (1.4, Z))
    a.rot("forearm_r", (0, Z), (0.6, (0, 0, 0)), (0.7, (25, 0, 0), "linear"), (1.4, Z))
    a.rot("sword", (0, Z), (0.6, (ALONG, 0, 0)), (0.7, (ALONG, 0, 0)), (0.95, (ALONG, 0, 0)), (1.4, Z))
    a.rot("arm_l", (0, Z), (0.6, (-35, 0, -35)), (0.7, (-10, 0, -10)), (1.4, Z))
    a.rot("head", (0, Z), (0.6, (0, -25, 0)), (0.7, (0, 20, 0)), (1.4, Z))
    a.rot("cape", (0, Z), (0.6, (10, 0, -12)), (0.8, (25, 0, 18)), (1.4, Z))
    a.pos("bone", (0, Z), (0.6, (0, -1, 3)), (0.7, (0, 0, -5), "linear"), (1.0, (0, 0, -5)), (1.4, Z))
    # combo 2: the blade wound across his body to the left, then a backhand sweep to the right (impact 0.55 s)
    a = m.anim("combo2", 1.3)
    a.rot("torso", (0, Z), (0.45, (0, -55, 0)), (0.55, (8, 50, 0), "linear"), (0.8, (6, 55, 0)), (1.3, Z))
    a.rot("arm_r", (0, Z), (0.45, (-80, -85, 0)), (0.55, (-85, 70, 10), "linear"), (0.8, (-80, 75, 10)), (1.3, Z))
    a.rot("forearm_r", (0, Z), (0.45, (15, 0, 0)), (0.55, (0, 0, 0), "linear"), (1.3, Z))
    a.rot("sword", (0, Z), (0.45, (ALONG, 0, 0)), (0.55, (ALONG, 0, 0)), (0.8, (ALONG, 0, 0)), (1.3, Z))
    a.rot("arm_l", (0, Z), (0.45, (-20, 0, -25)), (1.3, Z))
    a.rot("head", (0, Z), (0.45, (0, 25, 0)), (0.55, (0, -15, 0)), (1.3, Z))
    a.rot("cape", (0, Z), (0.45, (12, 0, 14)), (0.7, (25, 0, -18)), (1.3, Z))
    a.pos("bone", (0, Z), (0.45, (0, 0, 1)), (0.55, (0, 0, -6), "linear"), (0.85, (0, 0, -6)), (1.3, Z))
    # combo 3: the blade lifted over his head, point to the sky behind him, then a cleave (impact 0.90 s)
    a = m.anim("combo3", 1.9)
    for arm, zr in (("arm_r", 15), ("arm_l", -25)):
        a.rot(arm, (0, Z), (0.8, (-170, 0, zr)), (0.9, (-50, 0, zr * 0.5), "linear"), (1.35, (-45, 0, zr * 0.5)), (1.9, Z))
    a.rot("forearm_r", (0, Z), (0.8, (-25, 0, 0)), (0.9, (0, 0, 0), "linear"), (1.9, Z))
    a.rot("forearm_l", (0, Z), (0.8, (-45, 0, 0)), (0.9, (-35, 0, 0)), (1.9, Z))
    a.rot("sword", (0, Z), (0.8, (-20, 0, 0)), (0.9, (ALONG, 0, 0), "linear"), (1.35, (ALONG, 0, 0)), (1.9, Z))
    a.rot("torso", (0, Z), (0.8, (-22, 10, 0)), (0.9, (32, 0, 0), "linear"), (1.35, (30, 0, 0)), (1.9, Z))
    a.rot("head", (0, Z), (0.8, (-12, 0, 0)), (0.9, (12, 0, 0)), (1.9, Z))
    a.rot("cape", (0, Z), (0.8, (-5, 0, 0)), (0.95, (40, 0, 0)), (1.9, Z))
    a.pos("bone", (0, Z), (0.8, (0, 1, 2)), (0.9, (0, -5, -6), "linear"), (1.35, (0, -5, -6)), (1.9, Z))
    # thrust: the sword drawn back level at the hip, point forward, then a lunging stab (impact 0.75 s)
    a = m.anim("thrust", 1.6)
    a.rot("torso", (0, Z), (0.65, (-5, 40, 0)), (0.75, (14, -20, 0), "linear"), (1.1, (12, -18, 0)), (1.6, Z))
    a.rot("arm_r", (0, Z), (0.65, (35, 20, 15)), (0.75, (-80, -5, 0), "linear"), (1.1, (-78, -5, 0)), (1.6, Z))
    a.rot("forearm_r", (0, Z), (0.65, (-105, 0, 0)), (0.75, (0, 0, 0), "linear"), (1.6, Z))
    a.rot("sword", (0, Z), (0.65, (ALONG, 0, 0)), (0.75, (ALONG, 0, 0)), (1.1, (ALONG, 0, 0)), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.65, (-55, 0, -25)), (0.75, (15, 0, -10)), (1.6, Z))
    a.rot("leg_r", (0, Z), (0.65, (10, 0, 0)), (0.75, (-35, 0, 0), "linear"), (1.1, (-35, 0, 0)), (1.6, Z))
    a.rot("shin_r", (0, Z), (0.75, (20, 0, 0)), (1.1, (20, 0, 0)), (1.6, Z))
    a.rot("leg_l", (0, Z), (0.65, (-5, 0, 0)), (0.75, (28, 0, 0), "linear"), (1.1, (28, 0, 0)), (1.6, Z))
    a.pos("bone", (0, Z), (0.65, (0, -2, 4)), (0.75, (0, -3, -12), "linear"), (1.1, (0, -3, -12)), (1.6, Z))
    # leap: crouch, leap with the sword raised behind the head, crash down point-first (impact 1.05 s)
    a = m.anim("leap", 2.0)
    a.pos("bone", (0, Z), (0.45, (0, -5, 0)), (0.75, (0, 18, -4)), (0.95, (0, 10, -8)), (1.05, (0, -6, -10), "linear"),
          (1.5, (0, -6, -10)), (2.0, Z))
    for arm, zr in (("arm_r", 10), ("arm_l", -20)):
        a.rot(arm, (0, Z), (0.45, (30, 0, zr)), (0.8, (-175, 0, zr)), (1.05, (-40, 0, zr), "linear"), (1.5, (-40, 0, zr)), (2.0, Z))
    a.rot("sword", (0, Z), (0.45, (0, 0, 0)), (0.8, (-25, 0, 0)), (1.05, (ALONG, 0, 0), "linear"), (1.5, (ALONG, 0, 0)), (2.0, Z))
    a.rot("torso", (0, Z), (0.45, (22, 0, 0)), (0.8, (-18, 0, 0)), (1.05, (35, 0, 0), "linear"), (1.5, (32, 0, 0)), (2.0, Z))
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, Z), (0.45, (-40, 0, 0)), (0.8, (-10 * sign, 0, 0)), (1.05, (-50 if sign > 0 else 20, 0, 0)),
              (1.5, (-50 if sign > 0 else 20, 0, 0)), (2.0, Z))
    for shin in ("shin_r", "shin_l"):
        a.rot(shin, (0, Z), (0.45, (60, 0, 0)), (0.8, (20, 0, 0)), (1.05, (55, 0, 0)), (1.5, (55, 0, 0)), (2.0, Z))
    a.rot("cape", (0, Z), (0.75, (40, 0, 0)), (1.05, (-10, 0, 0)), (1.3, (30, 0, 0)), (2.0, Z))
    # trail: the blade drags a burning furrow behind him, then rips up to the sky (impact 0.85 s)
    a = m.anim("trail", 1.8)
    a.rot("torso", (0, Z), (0.5, (20, 35, 0)), (0.75, (24, 30, 0)), (0.85, (-15, -20, 0), "linear"), (1.2, (-12, -20, 0)), (1.8, Z))
    a.rot("arm_r", (0, Z), (0.5, (35, 0, 25)), (0.75, (40, 0, 30)), (0.85, (-155, 0, 10), "linear"), (1.2, (-150, 0, 10)), (1.8, Z))
    a.rot("sword", (0, Z), (0.5, (20, 0, 0)), (0.75, (20, 0, 0)), (0.85, (ALONG, 0, 0), "linear"), (1.2, (ALONG, 0, 0)), (1.8, Z))
    a.rot("arm_l", (0, Z), (0.5, (-30, 0, -40)), (0.85, (20, 0, -20)), (1.8, Z))
    a.pos("bone", (0, Z), (0.5, (0, -2, 2)), (0.75, (0, -2, -3)), (0.85, (0, 1, -6), "linear"), (1.2, (0, 0, -6)), (1.8, Z))
    # plant: lift the sword high, plunge it into the ground, hold while the pillars erupt (impact 0.90 s)
    a = m.anim("plant", 2.4)
    for arm, zr in (("arm_r", 25), ("arm_l", -25)):
        a.rot(arm, (0, Z), (0.75, (-150, 0, zr)), (0.9, (-35, 0, zr), "linear"), (1.8, (-35, 0, zr)), (2.4, Z))
    a.rot("forearm_r", (0, Z), (0.75, (-30, 0, 0)), (0.9, (0, 0, 0), "linear"), (2.4, Z))
    a.rot("forearm_l", (0, Z), (0.75, (-30, 0, 0)), (0.9, (-20, 0, 0)), (2.4, Z))
    a.rot("sword", (0, Z), (0.75, (ALONG, 0, 0)), (0.9, (30, 0, 0), "linear"), (1.8, (30, 0, 0)), (2.4, Z))
    a.rot("torso", (0, Z), (0.75, (-15, 0, 0)), (0.9, (28, 0, 0), "linear"), (1.8, (26, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.75, (-15, 0, 0)), (1.0, (10, 0, 0)), (1.8, (-10, 0, 0)), (2.4, Z))
    a.pos("bone", (0, Z), (0.75, (0, 1, 0)), (0.9, (0, -6, -2), "linear"), (1.8, (0, -6, -2)), (2.4, Z))
    a.rot("leg_r", (0, Z), (0.9, (-40, 0, 0)), (1.8, (-40, 0, 0)), (2.4, Z))
    a.rot("shin_r", (0, Z), (0.9, (50, 0, 0)), (1.8, (50, 0, 0)), (2.4, Z))
    a.rot("leg_l", (0, Z), (0.9, (25, 0, 0)), (1.8, (25, 0, 0)), (2.4, Z))
    a.rot("shin_l", (0, Z), (0.9, (40, 0, 0)), (1.8, (40, 0, 0)), (2.4, Z))
    # meteor: the blade raised straight to the burning sky, calling the ash down (impact 0.80 s)
    a = m.anim("meteor", 2.0)
    a.rot("arm_r", (0, Z), (0.6, (-170, 0, 12)), (0.8, (-178, 0, 8), "linear"), (1.5, (-176, 0, 10)), (2.0, Z))
    a.rot("sword", (0, Z), (0.6, (ALONG, 0, 0)), (1.5, (ALONG, 0, 0)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.6, (-40, 0, -50)), (1.5, (-40, 0, -50)), (2.0, Z))
    a.rot("torso", (0, Z), (0.6, (-15, 0, 0)), (1.5, (-15, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.6, (-30, 0, 0)), (1.5, (-30, 0, 0)), (2.0, Z))
    a.rot("cape", (0, Z), (0.8, (30, 0, 0)), (1.5, (20, 0, 0)), (2.0, Z))
    # spin: blade held out level at arm's length, two full burning turns (wind-up 0.60 s, spins to 1.4 s)
    a = m.anim("spin", 2.0)
    a.rot("bone", (0, Z), (0.6, (0, 50, 0)), (1.4, (0, -670, 0), "linear"), (1.6, (0, -720, 0)), (2.0, (0, -720, 0)))
    a.rot("arm_r", (0, Z), (0.6, (-10, 0, 85)), (1.4, (-10, 0, 85)), (2.0, Z))
    a.rot("forearm_r", (0, Z), (0.6, (28, 0, 0)), (1.4, (28, 0, 0)), (2.0, Z))
    a.rot("sword", (0, Z), (0.6, (ALONG, 0, 0)), (1.4, (ALONG, 0, 0)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.6, (-10, 0, -80)), (1.4, (-10, 0, -80)), (2.0, Z))
    a.rot("torso", (0, Z), (0.6, (10, 30, 0)), (1.4, (8, 0, 0)), (2.0, Z))
    a.rot("cape", (0, Z), (0.6, (10, 0, 0)), (0.9, (60, 0, 0)), (1.4, (60, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.6, (0, -2, 0)), (1.4, (0, -1, 0)), (2.0, Z))
    # roar: phase change, the blade ignites: sword raised high, chest out, head thrown back
    a = m.anim("roar", 2.6)
    a.rot("torso", (0, Z), (0.5, (-22, 0, 0)), (2.1, (-22, 0, 0)), (2.6, Z))
    a.rot("head", (0, Z), (0.5, (-35, 0, 0)), (2.1, (-35, 0, 0)), (2.6, Z))
    a.rot("arm_r", (0, Z), (0.5, (-130, 0, 40)), (2.1, (-130, 0, 40)), (2.6, Z))
    a.rot("sword", (0, Z), (0.5, (ALONG, 0, 0)), (2.1, (ALONG, 0, 0)), (2.6, Z))
    a.rot("arm_l", (0, Z), (0.5, (-30, 0, -70)), (2.1, (-30, 0, -70)), (2.6, Z))
    a.rot("cape", (0, Z), (0.5, (45, 0, 0)), (1.3, (35, 0, 0)), (2.1, (45, 0, 0)), (2.6, Z))
    # stagger: posture broken, down on one knee, leaning on the planted sword
    a = m.anim("stagger", 2.5)
    a.pos("bone", (0, Z), (0.3, (0, -9, 2)), (2.1, (0, -9, 2)), (2.5, Z))
    a.rot("leg_r", (0, Z), (0.3, (-75, 0, 0)), (2.1, (-75, 0, 0)), (2.5, Z))
    a.rot("shin_r", (0, Z), (0.3, (75, 0, 0)), (2.1, (75, 0, 0)), (2.5, Z))
    a.rot("leg_l", (0, Z), (0.3, (15, 0, 0)), (2.1, (15, 0, 0)), (2.5, Z))
    a.rot("shin_l", (0, Z), (0.3, (75, 0, 0)), (2.1, (75, 0, 0)), (2.5, Z))
    a.rot("torso", (0, Z), (0.3, (25, 0, 0)), (2.1, (25, 0, 0)), (2.5, Z))
    a.rot("head", (0, Z), (0.3, (20, 0, 0)), (2.1, (20, 0, 0)), (2.5, Z))
    a.rot("arm_r", (0, Z), (0.3, (-30, 0, 10)), (2.1, (-30, 0, 10)), (2.5, Z))
    a.rot("sword", (0, Z), (0.3, (35, 0, 0)), (2.1, (35, 0, 0)), (2.5, Z))
    a.rot("arm_l", (0, Z), (0.3, (-20, 0, -15)), (2.1, (-20, 0, -15)), (2.5, Z))
