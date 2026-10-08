"""The Castellan of the Caldera (Le Châtelain de la caldeira): lord of the Caldera Ringwall, about 5.7 blocks tall.

Silhouette idea: a towering, upright lord in heavy basalt plate trimmed with tarnished bronze, the armour split all
over by cracks of cooling magma (white-hot at the core, dull red at the edges, black crust around). His great helm is
crowned by a ring of jagged obsidian spikes around a small crater that glows from inside: the caldera itself. A long
ash-red mantle falls from his shoulders, its hem singed and smouldering. Strong asymmetry: the RIGHT pauldron is a
small volcano (stacked plates rising to a glowing vent that smokes), the left shoulder is a low layered plate under a
drape of the mantle; the right hand holds a great halberd taller than he is (black iron haft, an obsidian axe blade
with a glowing magma edge, a spear point and a back spike) planted beside him; the left hand is a heavy gauntlet with
molten knuckles, the fist he drives into the floor to raise walls of obsidian. On his tabard the sigil of the
ringwall: a ring with a needle in its middle.
"""
import functools
import random

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

BASALT = (56, 50, 58)
BASALT_L = (98, 90, 100)
BASALT_D = (28, 24, 30)
OBS = (32, 24, 44)
OBS_L = (74, 58, 96)
OBS_D = (16, 12, 24)
TRIM = (172, 120, 60)
TRIM_L = (226, 178, 102)
TRIM_D = (104, 68, 32)
MAGMA = (255, 116, 26)
MAGMA_L = (255, 222, 120)
MAGMA_D = (176, 42, 14)
CRUST = (44, 22, 20)
CLOTH = (112, 32, 24)
CLOTH_L = (146, 50, 34)
CLOTH_D = (62, 18, 16)
IRON = (60, 56, 64)
IRON_L = (112, 106, 118)


# ---------------------------------------------------------------- paint
@functools.lru_cache(maxsize=None)
def _cracks(w, h, seed, count):
    """Jagged magma cracks across a w x h face: {pixel: heat} with heat 2 at the core, 1 at the cooling edge."""
    rnd = random.Random(seed * 6271 + w * 37 + h * 101)
    core = set()
    for _ in range(count):
        x = rnd.randint(1, max(1, w - 2))
        y = rnd.randint(0, max(0, h // 4))
        for _ in range(int(h * (0.5 + rnd.random() * 0.45))):
            core.add((x, y))
            y += 1
            x = max(0, min(w - 1, x + rnd.choice((-1, 0, 0, 1))))
            if rnd.random() < 0.18:                         # a short branch running sideways
                bx = x
                for _ in range(rnd.randint(1, 3)):
                    bx = max(0, min(w - 1, bx + rnd.choice((-1, 1))))
                    core.add((bx, y))
    out = {}
    for (x, y) in core:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if 0 <= p[0] < w and 0 <= p[1] < h and p not in core:
                out[p] = 1
    for p in core:
        out[p] = 2
    return out


def stone(seed=0, cracks=0, base=BASALT, light=BASALT_L, dark=BASALT_D):
    """Basalt: mottled dark stone, lit top, dark underside; ``cracks`` magma cracks (cooling edges painted dull red)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return dark
        if cracks and face in ("front", "back", "left", "right"):
            heat = _cracks(w, h, seed, cracks).get((x, y))
            if heat == 2:
                return MAGMA_D
            if heat == 1:
                return CRUST if B.n(x, y, seed + 3) < 0.5 else mix(MAGMA_D, CRUST, 0.55)
        k = 1.06 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.16
        c = mul(base, k)
        if B.n(x // 2, y // 2, seed + 5) < 0.12:
            c = mix(c, light, 0.55)
        if face == "top":
            c = mul(c, 1.15)
        return c
    return f


def cracks_glow(seed=0, cracks=2):
    """The emissive core of the cracks painted by ``stone``/``plate`` with the same seed and count."""
    def f(face, x, y, w, h):
        if face in ("front", "back", "left", "right") and _cracks(w, h, seed, cracks).get((x, y)) == 2:
            return MAGMA_L if B.n(x, y, seed + 1) < 0.3 else MAGMA
        return None
    return f


def plate(seed=0, cracks=0, base=BASALT):
    """A basalt plate rimmed with tarnished bronze: bright top rim, darker sides, rivets in the corners."""
    inner = stone(seed, cracks, base=base)

    def f(face, x, y, w, h):
        if face == "bottom":
            return TRIM_D
        if face == "top":
            return TRIM if (x in (0, w - 1) or y in (0, h - 1)) else inner(face, x, y, w, h)
        if w > 2 and h > 2:
            if y == 0:
                return TRIM_L
            if x in (0, w - 1) or y == h - 1:
                return TRIM_D if B.n(x, y, seed + 9) < 0.85 else TRIM
            if w > 5 and h > 5 and y in (1, h - 2) and x in (1, w - 2):
                return TRIM
        return inner(face, x, y, w, h)
    return f


def obsidian(seed=0, cracks=0):
    """Obsidian: glassy purple-black with pale streaks of reflection."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return OBS_D
        if cracks and face in ("front", "back", "left", "right"):
            heat = _cracks(w, h, seed, cracks).get((x, y))
            if heat == 2:
                return MAGMA_D
            if heat == 1:
                return CRUST
        c = mul(OBS, 1.05 - 0.15 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
        if (x + y + seed) % 7 == 0 and B.n(x, y, seed + 2) < 0.5:
            c = mix(c, OBS_L, 0.7)                          # glassy glints
        if face == "top":
            c = mul(c, 1.2)
        return c
    return f


def cloth(seed=0, sigil=False, hem=2):
    """The ash-red mantle / tabard: long folds, a singed hem that smoulders (glow), optional ringwall sigil."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return CLOTH_D
        if y >= h - hem:
            if B.n(x, 0, seed) < 0.35:
                return None                                 # burnt holes in the hem
            return CRUST if B.n(x, y, seed + 1) < 0.5 else MAGMA_D
        if y >= h - hem - 2 and B.n(x, y, seed + 2) < 0.4:
            return mix(CLOTH_D, CRUST, 0.5)                 # scorched band above the hem
        if sigil and face == "front" and w >= 8:
            cx, cy = (w - 1) / 2, 6.5
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 2.6 <= d <= 3.6:
                return TRIM_L if y < cy else TRIM            # the ring of walls
            if abs(x - cx) <= 0.6 and 4 <= y <= 9:
                return OBS_L                                 # the needle in the middle
            if x in (0, w - 1):
                return TRIM_D
        fold = 1.06 if x % 3 == 0 else (0.92 if x % 3 == 2 else 1.0)
        return mul(CLOTH, fold * (1.04 - 0.18 * y / max(1, h)) + (B.n(x, y, seed) - 0.5) * 0.05)
    return f


def cloth_glow(seed=0, hem=2):
    def f(face, x, y, w, h):
        if face in ("top", "bottom") or y < h - hem or B.n(x, 0, seed) < 0.35:
            return None
        return None if B.n(x, y, seed + 1) < 0.5 else MAGMA
    return f


def helm_paint(f, x, y, w, h):
    """The great helm: basalt with a bronze brow band; in front a T-shaped slit glowing from inside."""
    if f == "bottom":
        return BASALT_D
    if f == "top":
        return CRUST
    cx = (w - 1) / 2
    if y in (3, 4):
        if f == "front" and abs(x - cx) <= 3.6 and y == 4:
            return MAGMA                                    # the eye slit
        return TRIM_L if y == 3 else TRIM                   # brow band
    if f == "front" and abs(x - cx) <= 0.6 and 5 <= y <= h - 3:
        return MAGMA_D                                      # the mouth slit (dull)
    if f == "front" and y >= 6 and abs(x - cx) in (2.0, 3.0) and y % 2 == 0:
        return BASALT_D                                     # breaths
    return stone(91, cracks=1 if f != "front" else 0)(f, x, y, w, h)


def helm_glow(f, x, y, w, h):
    cx = (w - 1) / 2
    if f == "front" and y == 4 and abs(x - cx) <= 3.6:
        return MAGMA_L if abs(x - cx) <= 1.6 else MAGMA
    if f == "front" and abs(x - cx) <= 0.6 and 5 <= y <= h - 3:
        return MAGMA
    if f in ("back", "left", "right"):
        return cracks_glow(91, 1)(f, x, y, w, h)
    return None


def chest_paint(f, x, y, w, h):
    """The breastplate: basalt plates, bronze rims, a great magma rift running from the left shoulder to the right
    hip; bronze ribs below the collar."""
    if f == "bottom":
        return BASALT_D
    if f != "front":
        return plate(70, cracks=1)(f, x, y, w, h)
    if y == 0:
        return TRIM_L
    if x in (0, w - 1) or y == h - 1:
        return TRIM_D
    # the rift: a jagged diagonal band
    t = x / max(1, w - 1)
    centre = 2 + t * (h - 6) + (1.2 if B.n(x // 2, 0, 71) < 0.5 else -0.6)
    d = abs(y - centre)
    if d < 0.8:
        return MAGMA_D
    if d < 1.8:
        return CRUST
    cx = (w - 1) / 2
    if abs(x - cx) <= 0.6 and y > 2:
        return TRIM_D                                       # keel line
    if y in (3, 7) and abs(x - cx) < w / 2 - 2:
        return TRIM if y == 3 else TRIM_D                   # ribs
    return stone(72)(f, x, y, w, h)


def chest_glow(f, x, y, w, h):
    if f != "front":
        return cracks_glow(70, 1)(f, x, y, w, h) if f in ("back", "left", "right") else None
    if y == 0 or x in (0, w - 1) or y == h - 1:
        return None
    t = x / max(1, w - 1)
    centre = 2 + t * (h - 6) + (1.2 if B.n(x // 2, 0, 71) < 0.5 else -0.6)
    if abs(y - centre) < 0.8:
        return MAGMA_L if B.n(x, y, 73) < 0.35 else MAGMA
    return None


def haft(seed=0):
    """The halberd haft: black iron with a light streak, bronze rings every so often."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return IRON
        if y % 14 in (0, 1):
            return TRIM_L if y % 14 == 0 else TRIM_D
        k = 1.25 if x == w // 2 else 0.9
        return mul(IRON, k + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def edge(face, x, y, w, h):
    return MAGMA_L if face in ("front", "top") else MAGMA


def glow_all(c):
    return lambda face, x, y, w, h: c


# ---------------------------------------------------------------- build
def build():
    m = Model("caldera_castellan", seed=167, shadow=2.0, walk_speed=0.65, walk_scale=0.85)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -36, 0))
    m.part("fauld", "pelvis", pivot=(0, 2, -6.5), rot=(-3, 0, 0))
    m.part("tabard", "pelvis", pivot=(0, 3, -7.5), rot=(-5, 0, 0))
    m.part("fauld_b", "pelvis", pivot=(0, 2, 6.5), rot=(5, 0, 0))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0))
    m.part("head", "chest", pivot=(0, -24, -1))
    m.part("cape", "chest", pivot=(0, -21, 7.5), rot=(6, 0, 0))
    m.part("cape2", "cape", pivot=(0, 20, 0), rot=(4, 0, 0))
    m.part("drape", "chest", pivot=(14, -22, 0), rot=(0, 0, -10))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(6.5 * sx, 0, 0), rot=(0, 0, -3 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 17, 0), rot=(0, 0, 3 * sx))
    m.part("arm_r", "chest", pivot=(-16, -19, 0), rot=(0, 0, 20))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-28, 0, -20))
    m.part("halberd", "fore_r", pivot=(-1, 13.5, -0.5), rot=(28, 0, 0))
    m.part("arm_l", "chest", pivot=(16, -19, 0), rot=(4, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-12, 0, 6))

    # ---- legs: plated thighs, knee cops, cracked greaves, heavy sabatons
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        s = 2 + (sx > 0)
        m.box(th, -4.5, -1, -4.5, 9, 18, 9, stone(s))
        m.box(th, -5, 1, -5.5, 10, 10, 2, plate(4 + s))                                  # cuisse plate
        m.box(th, -5.5 + (4.5 if sx > 0 else 0), 1, -4.5, 1, 9, 9, plate(5 + s))          # outer cuisse
        m.box(sh, -5, -2, -6.5, 10, 6, 3, plate(6 + s))                                   # knee cop
        m.box(sh, -4.5, 0, -4.5, 9, 15, 9, stone(8 + s, cracks=1), glow=cracks_glow(8 + s, 1))
        m.box(sh, -5, 2, -5.5, 10, 9, 1, plate(10 + s))   # greave front
        m.box(sh, -5.5, 14, -8, 11, 5, 13, plate(12 + s))                                 # sabaton
        m.box(sh, -4.5, 16, -9, 9, 3, 1, TRIM_D)                                          # toe cap

    # ---- pelvis: belt with a molten buckle, plate faulds front and back, the tabard with the ringwall sigil
    m.box("pelvis", -10.5, -4, -6.5, 21, 7, 13, plate(14))
    m.box("waist", -9.5, -6, -6, 19, 7, 12, B.bands(BASALT, TRIM_D, every=4, seed=15))
    m.box("waist", -2.5, -6, -7, 5, 5, 1, TRIM, glow={"front": lambda f, x, y, w, h: MAGMA if 1 <= x <= 3 and 1 <= y <= 3 else None})
    m.box("fauld", -9, 0, -1, 7, 11, 1, plate(16))
    m.box("fauld", 2, 0, -1, 7, 11, 1, plate(17))
    m.box("tabard", -4, 0, -0.5, 8, 17, 1, cloth(18, sigil=True), glow=cloth_glow(18))
    m.box("fauld_b", -9, 0, 0, 18, 12, 1, plate(19, cracks=1), glow=cracks_glow(19, 1))

    # ---- the breastplate with its magma rift, the gorget, the back plate
    m.box("chest", -13, -22, -7.5, 26, 22, 15, chest_paint, glow=chest_glow)
    m.box("chest", -1.5, -20, -8.5, 3, 15, 1, plate(21))                               # keel
    m.box("chest", -7.5, -25, -6.5, 15, 4, 12, plate(22))                              # gorget
    m.box("chest", -11, -21, 7.5, 22, 18, 1, stone(23, cracks=2), glow=cracks_glow(23, 2))

    # ---- head: the great helm crowned by a crater of obsidian spikes glowing inside
    m.box("head", -5.5, -12, -5.5, 11, 12, 11, helm_paint, glow=helm_glow)
    m.box("head", -6, -1, -6, 12, 2, 12, plate(30))                                    # collar
    m.box("head", -6.5, -5, -6.5, 13, 1, 13, TRIM_D)                                   # brim under the crown
    m.box("head", -4, -12.5, -4, 8, 1, 8, MAGMA_D, glow={"top": glow_all(MAGMA), "*": None})   # molten crater
    spikes = ((-6, -6, 7), (-1, -6.5, 5), (4, -6, 8), (4.5, -1, 5), (4, 4, 6), (-1, 4.5, 4), (-6, 4, 7), (-6.5, -1, 4))
    for i, (x, z, hgt) in enumerate(spikes):
        m.box("head", x, -12 - hgt, z, 2, hgt, 2, obsidian(32 + i))
        m.box("head", x + 0.5, -13 - hgt, z + 0.5, 1, 1, 1, OBS_L)
    for x, z in ((-3, -6), (2, -6)):
        m.box("head", x, -11, z - 0.5, 1, 4, 1, TRIM)                                  # cheek rivets / ribs

    # ---- the mantle down his back and the drape over the left shoulder
    m.box("cape", -11, 0, 0, 22, 21, 1, cloth(40, hem=0))
    m.box("cape2", -11, 0, 0, 22, 20, 1, cloth(41, hem=3), glow=cloth_glow(41, hem=3))
    m.box("cape", -12, -1, -1, 24, 2, 2, TRIM_D)                                       # the clasp bar
    m.box("drape", -3, -2, -7, 7, 14, 14, cloth(42, hem=2), glow=cloth_glow(42, hem=2))

    # ---- right arm: the volcano pauldron with its smoking vent, plated arm, gauntlet, and the great halberd
    m.box("arm_r", -8, -7, -7, 13, 6, 14, plate(50))
    m.box("arm_r", -7, -10, -5.5, 11, 3, 11, plate(51))
    m.box("arm_r", -6, -14, -4.5, 9, 4, 9, stone(52, cracks=3), glow=cracks_glow(52, 3))
    m.box("arm_r", -5, -17, -3.5, 7, 3, 7, stone(53, cracks=2), glow=cracks_glow(53, 2))
    m.box("arm_r", -4, -17.5, -2.5, 5, 1, 5, MAGMA_D, glow={"top": glow_all(MAGMA_L), "*": None})   # the vent
    m.box("arm_r", -4, -1, -4, 8, 13, 8, stone(54))
    m.box("fore_r", -4.5, 0, -4.5, 9, 10, 9, plate(55))
    m.box("fore_r", -4.5, 10, -5, 9, 6, 10, plate(56))                                 # gauntlet
    m.box("fore_r", -5, 12, -5.5, 10, 2, 1, TRIM)
    hb = "halberd"
    m.box(hb, -1, -46, -1, 2, 87, 2, haft(60))                                         # haft, butt on the floor
    m.box(hb, -1.5, 39, -1.5, 3, 3, 3, TRIM_D)                                         # ferrule
    m.box(hb, -1.5, -50, -1.5, 3, 6, 3, plate(61))                                     # socket
    m.box(hb, -1, -62, -1, 2, 12, 2, obsidian(62))                                     # spear point
    m.box(hb, -0.5, -64, -0.5, 1, 2, 1, MAGMA_L, glow=MAGMA_L)
    m.box(hb, -1, -52, -14, 2, 5, 13, obsidian(63, cracks=1), glow=cracks_glow(63, 1))  # blade, upper beard
    m.box(hb, -1, -47, -13, 2, 6, 12, obsidian(64))
    m.box(hb, -1, -41, -12, 2, 5, 11, obsidian(65, cracks=1), glow=cracks_glow(65, 1))
    m.box(hb, -1, -36, -10, 2, 4, 9, obsidian(66))                                     # lower beard
    m.box(hb, -1, -32, -6, 2, 3, 5, obsidian(69))
    m.box(hb, -0.5, -53, -15, 1, 13, 1, edge, glow=edge)                               # the molten edge
    m.box(hb, -0.5, -40, -13, 1, 4, 1, edge, glow=edge)
    m.box(hb, -0.5, -36, -11, 1, 4, 1, edge, glow=edge)
    m.box(hb, -1, -47, 1, 2, 2, 5, obsidian(67))                                       # back spike
    m.box(hb, -0.5, -46.5, 6, 1, 1, 3, OBS_L)
    m.box(hb, -1.5, -30, -1.5, 3, 2, 3, TRIM)                                          # langet ring
    m.box(hb, -1.5, -6, -1.5, 3, 10, 3, B.bands(CLOTH_D, TRIM_D, every=3, seed=68))    # leather grip

    # ---- left arm: low layered pauldron (under the drape), plated arm, the heavy gauntlet with molten knuckles
    m.box("arm_l", -4, -6, -6.5, 12, 6, 13, plate(70))
    m.box("arm_l", -4, -1, -4, 8, 13, 8, stone(71))
    m.box("arm_l", -4.5, 3, -5, 9, 3, 10, plate(72))                                   # couter band
    m.box("fore_l", -5, 0, -5, 10, 10, 10, plate(73))
    m.box("fore_l", -5.5, 10, -5.5, 11, 8, 11, stone(74, cracks=2), glow=cracks_glow(74, 2))     # gauntlet
    m.box("fore_l", -5.5, 13, -6.5, 11, 3, 1, MAGMA_D, glow=glow_all(MAGMA))           # molten knuckles
    m.box("fore_l", -6, 9, -6, 12, 2, 12, TRIM_D)                                      # cuff

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.4, (0, 7, 0)), (2.6, (0, 7, 0)), (3.4, (0, -5, 0)), (4.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (2.0, (4, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("cape2", (0, (0, 0, 0)), (1.0, (3, 0, 0)), (2.5, (-2, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("drape", (0, (0, 0, 0)), (2.0, (0, 0, -2)), (4.0, (0, 0, 0)))
    idle.rot("tabard", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    walk.rot("thigh_r", (0, (20, 0, 0)), (0.9, (-20, 0, 0)), (1.8, (20, 0, 0)))
    walk.rot("thigh_l", (0, (-20, 0, 0)), (0.9, (20, 0, 0)), (1.8, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.45, (26, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (1.35, (26, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_l", (0, (-12, 0, 0)), (0.9, (12, 0, 0)), (1.8, (-12, 0, 0)))
    walk.rot("arm_r", (0, (6, 0, 0)), (0.9, (-6, 0, 0)), (1.8, (6, 0, 0)))
    walk.rot("chest", (0, (0, 4, 0)), (0.9, (0, -4, 0)), (1.8, (0, 4, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -1.0, 0)), (0.9, (0, 0, 0)), (1.35, (0, -1.0, 0)), (1.8, (0, 0, 0)))
    walk.rot("cape", (0, (10, 0, 0)), (0.45, (16, 0, 0)), (0.9, (10, 0, 0)), (1.35, (16, 0, 0)), (1.8, (10, 0, 0)))
    walk.rot("cape2", (0, (6, 0, 0)), (0.45, (12, 0, 0)), (0.9, (6, 0, 0)), (1.35, (12, 0, 0)), (1.8, (6, 0, 0)))
    walk.rot("tabard", (0, (-6, 0, 0)), (0.9, (6, 0, 0)), (1.8, (-6, 0, 0)))

    # sweep: the halberd hauled back over his right shoulder (0.9 s = 18 ticks), then swept flat across 230 degrees
    # in front of him from his right to his left
    a = m.anim("sweep", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-58, 70, 0)), (0.9, (-60, 80, 0)), (1.0, (-62, -70, 0), "linear"),
          (1.15, (-60, -80, 0)), (1.8, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.7, (150, 0, 0)), (1.15, (150, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, 40, 0)), (1.0, (0, -38, 0), "linear"), (1.15, (0, -42, 0)), (1.8, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.9, (0, 10, 0)), (1.0, (0, -10, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-50, 30, -10)), (1.0, (-30, -20, -20), "linear"), (1.8, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.9, (-14, 0, 6)), (1.8, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (12, 0, -4)), (1.8, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (8, 0, -10)), (1.05, (20, 0, 14)), (1.8, (0, 0, 0)))

    # chop: the halberd raised high in both hands (1.0 s = 20 ticks), brought straight down in front of him
    a = m.anim("chop", 1.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-165, 0, -10)), (1.0, (-170, 0, -12)), (1.1, (-40, 0, -14), "linear"),
          (1.4, (-42, 0, -14)), (1.9, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (10, 0, 0)), (1.1, (0, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.7, (150, 0, 0)), (1.4, (150, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-160, 0, -30)), (1.0, (-165, 0, -32)), (1.1, (-60, 0, -30), "linear"),
          (1.4, (-62, 0, -30)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-18, 0, 0)), (1.1, (24, 0, 0), "linear"), (1.4, (22, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.1, (-14, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1.0, 0)), (1.1, (0, -3, 0), "linear"), (1.4, (0, -3, 0)), (1.9, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (18, 0, 0), "linear"), (1.4, (18, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (-30, 0, 0), "linear"), (1.4, (-30, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (34, 0, 0), "linear"), (1.4, (34, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (-4, 0, 0)), (1.2, (26, 0, 0)), (1.9, (0, 0, 0)))

    # charge: the halberd levelled like a lance, head down (0.8 s = 16 ticks), then a heavy run for 1 s
    a = m.anim("charge", 2.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-48, 0, -6)), (0.8, (-50, 0, -6)), (1.8, (-50, 0, -6)), (2.5, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.7, (148, 0, 0)), (1.8, (148, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-50, 0, -14)), (1.8, (-50, 0, -14)), (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (24, 0, 0)), (1.8, (24, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-18, 0, 0)), (1.8, (-18, 0, 0)), (2.5, (0, 0, 0)))
    run_r = [(0.8 + 0.25 * i, ((-40 if i % 2 else 34), 0, 0), "linear") for i in range(5)]
    run_l = [(0.8 + 0.25 * i, ((34 if i % 2 else -40), 0, 0), "linear") for i in range(5)]
    a.rot("thigh_r", (0, (0, 0, 0)), (0.7, (24, 0, 0)), *run_r, (2.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), *run_l, (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.925, (40, 0, 0)), (1.175, (8, 0, 0)), (1.425, (40, 0, 0)),
          (1.675, (8, 0, 0)), (1.8, (20, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.7, (30, 0, 0)), (0.925, (8, 0, 0)), (1.175, (40, 0, 0)), (1.425, (8, 0, 0)),
          (1.675, (40, 0, 0)), (1.8, (20, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.0, (50, 0, 0)), (1.8, (52, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("cape2", (0, (0, 0, 0)), (1.0, (20, 0, 0)), (1.8, (24, 0, 0)), (2.5, (0, 0, 0)))

    # leap: a deep crouch, halberd drawn back (0.5 s), the jump (he is airborne from 0.5 to 1.2 s, halberd
    # overhead), and the landing chop at 1.2 s = 24 ticks; a long recovery hunched over the haft
    a = m.anim("leap", 2.3)
    a.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -6, 0)), (0.55, (0, 1, 0), "linear"), (1.1, (0, 0, 0)),
          (1.2, (0, -6, 0), "linear"), (1.8, (0, -5, 0)), (2.3, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.45, (-50, 0, -6 * sx)), (0.55, (14, 0, 0), "linear"),
              (1.1, (-30, 0, 0)), (1.2, (-55, 0, -6 * sx), "linear"), (1.8, (-50, 0, -6 * sx)), (2.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.45, (60, 0, 0)), (0.55, (10, 0, 0), "linear"), (1.1, (40, 0, 0)),
              (1.2, (65, 0, 0), "linear"), (1.8, (60, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (-150, 0, -10)), (1.1, (-170, 0, -12)),
          (1.2, (-40, 0, -14), "linear"), (1.8, (-42, 0, -14)), (2.3, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.5, (150, 0, 0)), (1.8, (150, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (30, 0, -20)), (0.6, (-140, 0, -30)), (1.1, (-160, 0, -30)),
          (1.2, (-60, 0, -30), "linear"), (1.8, (-58, 0, -30)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.45, (30, 0, 0)), (0.6, (-16, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (30, 0, 0), "linear"),
          (1.8, (26, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.5, (10, 0, 0)), (0.8, (-30, 0, 0)), (1.1, (-36, 0, 0)), (1.3, (40, 0, 0)),
          (1.8, (10, 0, 0)), (2.3, (0, 0, 0)))

    # stomp: the right foot raised high (0.7 s = 14 ticks), stamped down: the floor cracks around him
    a = m.anim("stomp", 1.45)
    a.rot("thigh_r", (0, (0, 0, 0)), (0.6, (-62, 0, 8)), (0.7, (-66, 0, 8)), (0.75, (-6, 0, 4), "linear"),
          (1.0, (-8, 0, 4)), (1.45, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.6, (50, 0, 0)), (0.7, (52, 0, 0)), (0.75, (6, 0, 0), "linear"), (1.45, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-12, 0, 6)), (0.75, (14, 0, 0), "linear"), (1.0, (12, 0, 0)), (1.45, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-40, 0, -40)), (0.75, (-10, 0, -20), "linear"), (1.45, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-6, 0, 4)), (0.75, (0, 0, 0), "linear"), (1.45, (0, 0, 0)))
    a.pos("halberd", (0, (0, 0, 0)), (0.7, (0, 4, 0)), (0.75, (0, 2, 0), "linear"), (1.45, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.7, (0, 1.5, 0)), (0.75, (0, -2, 0), "linear"), (1.0, (0, -2, 0)), (1.45, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (4, 0, 0)), (0.75, (-16, 0, 0), "linear"), (1.0, (-16, 0, 0)), (1.45, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.75, (20, 0, 0), "linear"), (1.0, (20, 0, 0)), (1.45, (0, 0, 0)))

    # rampart (phase 2): the left gauntlet raised high, magma pouring off it (1.0 s = 20 ticks), then driven into the
    # floor on one knee: walls of obsidian burst up across the arena
    a = m.anim("rampart", 2.1)
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-170, 0, -14)), (1.0, (-172, 0, -16)), (1.08, (-50, 0, -10), "linear"),
          (1.5, (-52, 0, -10)), (2.1, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.08, (-30, 0, 0), "linear"), (1.5, (-30, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-10, 0, 30)), (1.08, (10, 0, 24), "linear"), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, -14, 0)), (1.08, (30, 10, 0), "linear"), (1.5, (28, 10, 0)), (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.08, (6, 0, 0), "linear"), (2.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1.0, 0)), (1.08, (0, -8, 0), "linear"), (1.5, (0, -8, 0)), (2.1, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (20, 0, 0), "linear"), (1.5, (20, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (75, 0, 0), "linear"), (1.5, (75, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (-72, 0, 0), "linear"), (1.5, (-72, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (72, 0, 0), "linear"), (1.5, (72, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (1.2, (30, 0, 0)), (2.1, (0, 0, 0)))

    # reap (phase 2): the halberd drawn to his right (0.8 s = 16 ticks), a forehand sweep at 0.8 s, then the haft is
    # whipped round and a backhand sweep follows at 1.4 s (active tick 12)
    a = m.anim("reap", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-58, 70, 0)), (0.8, (-60, 80, 0)), (0.9, (-62, -70, 0), "linear"),
          (1.3, (-60, -84, 0)), (1.4, (-62, 72, 0), "linear"), (1.6, (-60, 80, 0)), (2.3, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.6, (150, 0, 0)), (1.6, (150, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (0, 40, 0)), (0.9, (0, -38, 0), "linear"), (1.3, (0, -44, 0)),
          (1.4, (0, 36, 0), "linear"), (1.6, (0, 40, 0)), (2.3, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, 10, 0)), (0.9, (0, -10, 0), "linear"), (1.3, (0, -12, 0)),
          (1.4, (0, 10, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-50, 30, -10)), (0.9, (-30, -20, -20), "linear"), (1.4, (-50, 30, -10), "linear"),
          (2.3, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (-14, 0, 6)), (1.4, (10, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (12, 0, -4)), (1.4, (-14, 0, -4)), (2.3, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (20, 0, 14)), (1.4, (20, 0, -14)), (2.3, (0, 0, 0)))

    # reel: his charge broke on his own wall: the shock throws him back at 0.3 s (6 ticks), he sags over the haft
    a = m.anim("reel", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.3, (-28, 0, 6), "linear"), (0.6, (24, 0, -6)), (1.6, (26, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-30, 0, 0), "linear"), (0.6, (26, 0, -12)), (1.6, (28, 0, -12)), (2.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, 0, 3), "linear"), (0.6, (0, -5, 2)), (1.6, (0, -5, 2)), (2.0, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.6, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.6, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.6, (40, 0, 0)), (1.6, (40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-30, 0, 30), "linear"), (0.6, (-20, 0, 10)), (1.6, (-20, 0, 10)), (2.0, (0, 0, 0)))
    a.pos("halberd", (0, (0, 0, 0)), (0.3, (0, 4, 0), "linear"), (0.6, (0, 7, 0)), (1.6, (0, 7, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-40, 0, -50), "linear"), (0.6, (10, 0, -10)), (1.6, (10, 0, -10)), (2.0, (0, 0, 0)))

    # heat (phase 3): he drives the halberd into the floor and kneels over it, straining, drawing the volcano's heat
    # (1.5 s = 30 ticks, invulnerable), then rises with arms flung wide, the cracks blazing
    a = m.anim("heat", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -8, 0)), (1.5, (0, -8, 0)), (1.6, (0, 1, 0), "linear"), (2.8, (0, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (1.5, (20, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (75, 0, 0)), (1.5, (75, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.4, (-72, 0, 0)), (1.5, (-72, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (72, 0, 0)), (1.5, (72, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    shake = [(0.4 + 0.1 * i, (22 + (4 if i % 2 else -4), 0, 0)) for i in range(11)]
    a.rot("chest", (0, (0, 0, 0)), *shake, (1.6, (-26, 0, 0), "linear"), (2.8, (-22, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-60, 0, 10)), (1.5, (-62, 0, 10)), (1.6, (-155, 0, -10), "linear"),
          (2.8, (-150, 0, -10)), (3.5, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.4, (40, 0, 0)), (1.5, (40, 0, 0)), (1.6, (155, 0, 0), "linear"), (2.8, (150, 0, 0)), (3.5, (0, 0, 0)))
    a.pos("halberd", (0, (0, 0, 0)), (0.4, (0, 7, 0)), (1.5, (0, 7, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-62, 0, -20)), (1.5, (-64, 0, -20)), (1.6, (-50, 0, -90), "linear"),
          (2.8, (-46, 0, -86)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (24, 0, 0)), (1.5, (26, 0, 0)), (1.6, (-36, 0, 0), "linear"), (2.8, (-32, 0, 0)),
          (3.5, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (1.5, (1, 1, 1)), (1.6, (1.1, 1.1, 1.1), "linear"), (2.8, (1.05, 1.05, 1.05)),
            (3.5, (1, 1, 1)))
    a.rot("cape", (0, (0, 0, 0)), (1.5, (6, 0, 0)), (1.7, (50, 0, 0)), (2.4, (20, 0, 0)), (3.5, (0, 0, 0)))

    # vents (phase 3, spectacle): the halberd raised overhead in both hands, drawing heat (1.0 s = 20 ticks), then its
    # butt slammed into the floor; he holds it there, head thrown back, while the floor vents erupt for 2.5 s
    a = m.anim("vents", 4.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-172, 0, -10)), (1.0, (-175, 0, -12)), (1.08, (-40, 0, -14), "linear"),
          (3.5, (-42, 0, -14)), (4.2, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.85, (175, 0, 0)), (1.0, (175, 0, 0)), (1.08, (150, 0, 0), "linear"), (3.5, (150, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-160, 0, -24)), (1.0, (-164, 0, -26)), (1.08, (-30, 0, -80), "linear"),
          (3.5, (-32, 0, -76)), (4.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.08, (6, 0, 0), "linear"), (3.5, (-14, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (-10, 0, 0), "linear"), (1.4, (-34, 0, 0)), (3.5, (-30, 0, 0)),
          (4.2, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1.0, 0)), (1.08, (0, -2, 0), "linear"), (3.5, (0, -2, 0)), (4.2, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (1.0, (-8, 0, 0)), (1.3, (34, 0, 0)), (2.4, (24, 0, 4)), (3.5, (28, 0, -4)),
          (4.2, (0, 0, 0)))

    # roar (phase two): the halberd thrust skyward, the left fist clenched, the crater on his helm flaring
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-160, 0, -10)), (1.6, (-164, 0, -12)), (2.0, (0, 0, 0)))
    a.rot("halberd", (0, (0, 0, 0)), (0.6, (160, 0, 0)), (1.6, (164, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-40, 0, -50)), (1.6, (-44, 0, -54)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-32, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.6, (30, 0, 0)), (1.1, (14, 0, 0)), (1.6, (26, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: his guard broken, he drops to one knee leaning on the haft
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -8, 0)), (1.2, (0, -8, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (75, 0, 0)), (1.2, (75, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (-72, 0, 0)), (1.2, (-72, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (72, 0, 0)), (1.2, (72, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 8)), (1.2, (28, 0, 8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, -10)), (1.2, (26, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-40, 0, 10)), (1.2, (-42, 0, 10)), (1.6, (0, 0, 0)))
    a.pos("halberd", (0, (0, 0, 0)), (0.3, (0, 9, 0)), (1.2, (0, 9, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (1.2, (12, 0, -10)), (1.6, (0, 0, 0)))
