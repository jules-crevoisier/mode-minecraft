"""The Colossus's Heart (Le Cœur du Colosse): the still-beating brass engine-heart of the Fallen Colossus, about 6.2
blocks tall with its floating helm.

Silhouette idea: a knight that is not quite there. The statue's heart, a riveted brass engine-heart with copper
arteries, a valve wheel on its crown and amber light leaking from its seams, hangs in an iron cage of ribs; round it the
heart has pulled loose bronze plates and stone rubble into the shape of a knight, every plate held a finger's breadth
off the next by glowing magnetic tethers (the gaps are the point: you see through it). The breastplate is split down
the middle so the heart shows and glows. The helm floats above the gorget with nothing between. Strong asymmetry: a
colossal broken greatsword (a fragment of the statue's own blade) in the RIGHT hand, its point carried low in front;
on the LEFT forearm a great curved shield-plate torn from the statue's breastplate, a gold sun boss on it; the left
pauldron is a heaped double plate with the snapped crest-fin of a helmet stuck in it.

Three texture variants on the same cubes (``modelVariant()``):
  * ``whole``: the armoured knight (phase 1);
  * ``burst``: the armour gone (painted away), the heart exposed in its cage on rubble legs, and two rings of plates
    orbiting it (painted in only here; they spin in ``idle``) (phase 2);
  * ``reforged``: the knight re-formed, the plates seamed with glowing amber where the heart welded them back
    (phase 3; the entity also grows 15% through its SCALE attribute).
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B
from .bronze_sentinel import moss, stone

VARIANTS = ["whole", "burst", "reforged"]

BRONZE = (150, 104, 56)
BRONZE_L = (204, 156, 92)
BRONZE_D = (96, 62, 34)
VERD = (86, 168, 146)
VERD_D = (50, 116, 100)
STONE_D = (86, 84, 78)
GOLD = (255, 204, 86)
GOLD_D = (214, 150, 40)
AMBER = (255, 170, 60)
AMBER_L = (255, 228, 150)
AMBER_D = (220, 110, 30)
IRON = (62, 58, 58)
IRON_L = (104, 98, 94)
IRON_D = (36, 32, 32)
HEART = (206, 152, 64)          # polished brass of the heart: brighter than the weathered bronze round it
HEART_L = (246, 210, 128)
HEART_D = (130, 84, 34)
COPPER = (188, 108, 58)
COPPER_L = (232, 156, 98)
COPPER_D = (116, 60, 32)


def _gone(face, x, y, w, h):
    return None


# ---------------------------------------------------------------- paint
def heart_brass(seed=0, seams=True):
    """The heart's riveted brass: lit top edge, rivet rows, and wandering seams that leak amber light."""
    base = B.plate(HEART, HEART_D, HEART_L, seed=seed, rivet_step=3, grad=0.28, worn=0.08)

    def f(face, x, y, w, h):
        if seams and face not in ("top", "bottom") and _seam(x, y, w, h, seed):
            return AMBER_D
        return base(face, x, y, w, h)
    return f


def _seam(x, y, w, h, seed):
    """A jagged crack running down the face: one column that drifts left and right with height."""
    if w < 4 or h < 4:
        return False
    col = int(w * (0.3 + 0.4 * B.n(seed, 1, 77))) + int((B.n(y // 2, seed, 78) - 0.5) * 2.4)
    return x == col and 1 <= y <= h - 2


def heart_glow(seed=0):
    def f(face, x, y, w, h):
        if face not in ("top", "bottom") and _seam(x, y, w, h, seed):
            return AMBER_L if y % 3 else AMBER
        return None
    return f


def copper_pipe(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return COPPER_D
        c = COPPER_L if x == 0 else COPPER_D if x == w - 1 else COPPER
        if (y + seed) % 5 == 0:
            c = mix(c, VERD, 0.5)                                    # verdigris at the joints
        return c
    return f


def iron_rib(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        c = IRON_L if (face == "top" or x == 0) else IRON
        if B.n(x, y, seed) < 0.12:
            c = mix(c, COPPER_D, 0.5)                                # rust
        return mul(c, 1.0 - 0.15 * y / max(1, h))
    return f


def tether(face, x, y, w, h):
    return AMBER_D


def tether_glow(face, x, y, w, h):
    return AMBER_L if (x + y) % 3 else AMBER


def gauge(face, x, y, w, h):
    """A pressure gauge on the heart: cream dial, black ticks, a red needle in the red."""
    if face != "front":
        return HEART_D
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = math.hypot(x - cx, y - cy)
    if d > cx + 0.2:
        return HEART_D
    if d > cx - 0.8:
        return HEART_L
    if abs((x - cx) + (y - cy)) < 0.6 and x > cx - 0.5:
        return (176, 32, 30)
    return B.CREAM if (x + y) % 4 else B.CREAM_D


def valve_wheel(face, x, y, w, h):
    if face in ("top", "bottom"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = math.hypot(x - cx, y - cy)
        if d > cx - 0.9 or x == round(cx) or y == round(cy):
            return (176, 40, 34) if face == "top" else (110, 26, 22)
        return None
    return (150, 34, 30)


def blade(seed=0):
    """The colossal sword fragment: bronze with a bright edge, a dark fuller, verdigris rot and nicks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BRONZE_D
        if face == "top":
            return BRONZE_L
        if face in ("left", "right"):
            return BRONZE_L if (y + seed) % 7 else BRONZE_D               # the edges, nicked
        if x in (0, w - 1):
            return mix(BRONZE_L, (255, 240, 210), 0.35)
        if x == w // 2 and 3 < y < h - 4:
            return mul(BRONZE_D, 0.8)                                     # the fuller
        if B.n(x, y // 2, seed) < 0.18 + 0.25 * y / max(1, h):
            return VERD if B.n(x, y, seed + 3) < 0.6 else VERD_D
        return mul(BRONZE, 1.08 - 0.2 * y / max(1, h))
    return f


def shield_face(f, x, y, w, h):
    """The shield-plate: a curved piece of the statue's breastplate, verdigris bronze, a rune band and a gold sun boss."""
    if f in ("left",):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = math.hypot(x - cx, (y - cy) * 0.8)
        if d < 3.2:
            return GOLD if d < 2 else GOLD_D
        if y in (int(cy) - 6, int(cy) + 6) and 2 <= x <= w - 3:
            return GOLD_D if x % 3 else BRONZE_D
        if (x + y * 2) % 23 == 0:
            return mul(STONE_D, 0.6)                                       # cracks showing stone
    return bplate(220, verd=0.4)(f, x, y, w, h)


def shield_glow(f, x, y, w, h):
    if f == "left":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        if math.hypot(x - cx, (y - cy) * 0.8) < 2:
            return GOLD
    return None


def helm_paint(f, x, y, w, h):
    """The floating helm: a verdigris great helm with a T visor; amber heart-light inside."""
    if f == "front":
        cx = w // 2
        if y in (5, 6) and 1 <= x <= w - 2:
            return AMBER if y == 5 else AMBER_D
        if x in (cx - 1, cx) and 5 <= y <= h - 3:
            return AMBER if y < 9 else AMBER_D
        if y in (4, 7) and 1 <= x <= w - 2:
            return mul(BRONZE_D, 0.7)
        if y == h - 1:
            return mul(BRONZE_D, 0.6)                                      # torn lower edge
    return bplate(240, verd=0.45, rivets=False)(f, x, y, w, h)


def helm_glow(f, x, y, w, h):
    if f == "front":
        cx = w // 2
        if y in (5, 6) and 1 <= x <= w - 2:
            return AMBER_L if y == 5 else AMBER
        if x in (cx - 1, cx) and 5 <= y <= h - 3:
            return AMBER_L if y < 9 else AMBER
    return None


def bplate(seed=0, verd=0.3, rivets=True):
    """Weathered statue bronze: a lit top edge, a dark rim, a soft vertical gradient, verdigris running down from the
    top in a few drip columns (no speckle), rivets in the corners and a faint panel line."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(BRONZE_D, 0.75)
        if face == "top":
            return mix(BRONZE_L, VERD, 0.35) if B.n(x // 2, y // 2, seed) < verd else mul(BRONZE_L, 0.95)
        if w > 2 and h > 2:
            if y == 0:
                return BRONZE_L
            if x == 0 or x == w - 1 or y == h - 1:
                return mul(BRONZE_D, 0.9)
        if rivets and w > 4 and h > 4 and y in (1, h - 2) and x in (1, w - 2):
            return mix(BRONZE_L, (255, 240, 200), 0.4)
        drip = B.n(x, 0, seed + 11) < verd * 0.55
        length = int(h * (0.3 + 0.7 * B.n(x, 1, seed + 12)))
        if drip and y <= length:
            return VERD if (y + x) % 3 else mix(VERD, VERD_D, 0.5)
        if h > 8 and y == h // 2 and 0 < x < w - 1:
            return mul(BRONZE, 0.8)                                      # a panel line
        k = 1.1 - 0.28 * y / max(1, h) + (B.n(x // 2, y // 2, seed) - 0.5) * 0.08
        return mul(BRONZE, k)
    return f


def reforged_glow(seed=0):
    """Phase 3: the heart welded the plates back with its own fire: a glowing amber crack across each plate face."""
    def f(face, x, y, w, h):
        if face in ("bottom", "top") or w < 5 or h < 5 or B.n(seed, 9, 30) > 0.75:
            return None
        row = int(h * (0.3 + 0.4 * B.n(seed, 2, 31)) + 1.2 * math.sin(x * 0.9 + seed))
        if y == row and 0 < x < w - 1 and B.n(x // 3, 0, seed + 5) < 0.8:
            return AMBER_D if (x + seed) % 5 else AMBER
        return None
    return f


def reforged_plate(seed=0, verd=0.3):
    base = bplate(seed, verd=verd)
    glow = reforged_glow(seed)

    def f(face, x, y, w, h):
        g = glow(face, x, y, w, h)
        return mix(g, BRONZE_D, 0.3) if g is not None else base(face, x, y, w, h)
    return f


# ---------------------------------------------------------------- build
def build(variant=None):
    variant = variant or "whole"
    burst = variant == "burst"
    reforged = variant == "reforged"
    m = Model("colossus_heart", seed=733, shadow=2.0, walk_speed=0.55, walk_scale=0.75, variants=VARIANTS,
              glow_pulse=0.0)

    def box(part, x, y, z, w, h, d, paint, glow=None, kind="core"):
        """kind: core (always), armour (gone in burst, amber-seamed when reforged), orbit (only in burst)."""
        if kind == "armour":
            if burst:
                paint, glow = _gone, None
            elif reforged and not callable(glow):
                seed = int(abs(x * 7 + y * 13 + z * 3 + w + h * 5)) % 97
                paint, glow = reforged_plate(seed), reforged_glow(seed)
        elif kind == "orbit" and not burst:
            paint, glow = _gone, None
        m.box(part, x, y, z, w, h, d, paint, glow=glow)

    def plate(seed, verd=0.3):
        return bplate(seed, verd=min(0.6, verd * 0.75))

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -42, 0))
    m.part("chest", "hips", pivot=(0, -4, 0), rot=(4, 0, 0))
    m.part("heart", "chest", pivot=(0, -20, -1))
    m.part("cage", "chest", pivot=(0, -20, 0))
    m.part("plates", "chest", pivot=(0, 0, 0))
    m.part("head", "chest", pivot=(0, -41, -1), rot=(-4, 0, 0))
    m.part("pauldron_r", "chest", pivot=(-17, -36, 0), rot=(0, 0, 12))
    m.part("pauldron_l", "chest", pivot=(17, -36, 0), rot=(0, 0, -14))
    m.part("debris", "chest", pivot=(0, -20, 0))
    m.part("arm_r", "chest", pivot=(-19, -30, 0), rot=(-8, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 14, 0), rot=(-36, 0, 0))
    m.part("sword", "fore_r", pivot=(0, 16, -1), rot=(-30, 0, -4))
    m.part("arm_l", "chest", pivot=(19, -30, 0), rot=(-6, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 14, 0), rot=(-58, 0, 6))
    m.part("shield", "fore_l", pivot=(4, 7, -1), rot=(62, -8, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "bone", pivot=(7.5 * sx, -42, 0), rot=(0, 0, -4 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 20, 0), rot=(0, 0, 4 * sx))
    # the orbiting plates of phase 2: two rings on the root, level whatever the body does
    m.part("orbit_in", "bone", pivot=(0, -60, 0))
    m.part("orbit_out", "bone", pivot=(0, -34, 0))
    for k in range(4):
        a = k * 90
        r = math.radians(a)
        m.part(f"oi_{k}", "orbit_in", pivot=(math.cos(r) * 34, (k % 2) * 4 - 2, math.sin(r) * 34), rot=(0, -a + 90, 12))
    for k in range(6):
        a = k * 60 + 30
        r = math.radians(a)
        m.part(f"oo_{k}", "orbit_out", pivot=(math.cos(r) * 54, (k % 2) * 6 - 3, math.sin(r) * 54), rot=(0, -a + 90, -8))

    # ---- legs: columns of stacked rubble, bronze greaves and knee cops floating a finger off them
    for side, sx in (("r", -1), ("l", 1)):
        t, s = f"thigh_{side}", f"shin_{side}"
        box(t, -4.5, 0, -4.5, 9, 9, 9, stone(300 + sx))
        box(t, -4, 9, -4, 8, 11, 8, stone(302 + sx, moss=0.2))
        box(t, -5, 1, -6, 10, 13, 1, plate(310 + sx), kind="armour")          # cuisse
        box(t, 4.5 * sx - (1 if sx > 0 else 0) - 0.5 * sx, 2, -4, 1, 11, 8, plate(312 + sx), kind="armour")
        box(t, -4.5, 17, -6.5, 9, 6, 2, plate(314 + sx, verd=0.6), kind="armour")   # knee cop
        box(t, -0.5, 14, -5.5, 1, 3, 1, tether, glow=tether_glow)
        box(s, -3, 0, -3, 6, 9, 6, stone(320 + sx))
        box(s, -3.5, 9, -3.5, 7, 9, 7, stone(322 + sx, moss=0.25))
        box(s, -4.5, 2, -5.5, 9, 14, 2, plate(330 + sx, verd=0.55), kind="armour")  # greave
        box(s, -4.5, 3, 3.5, 9, 12, 1, plate(332 + sx, verd=0.6), kind="armour")
        box(s, -5, 18, -9, 10, 4, 13, plate(334 + sx, verd=0.5))                    # sabaton (the feet stay)
        box(s, -4, 16, -8, 8, 2, 4, plate(336 + sx, verd=0.5), kind="armour")
        box(s, -0.5, 16, -6, 1, 2, 1, tether, glow=tether_glow)

    # ---- hips: a rubble girdle, tassets hanging from tethers
    box("hips", -8, -5, -5.5, 16, 9, 11, stone(340, moss=0.25))
    box("hips", -11, 2, -8, 10, 11, 1, plate(342), kind="armour")
    box("hips", 1, 2, -8, 10, 11, 1, plate(343), kind="armour")
    box("hips", -10, 2, 6.5, 20, 10, 1, plate(344), kind="armour")
    box("hips", -12, 1, -6, 1, 10, 12, plate(345), kind="armour")
    box("hips", 11, 1, -6, 1, 10, 12, plate(346), kind="armour")
    box("hips", -6, 0, -7.5, 1, 2, 1, tether, glow=tether_glow)
    box("hips", 5, 0, -7.5, 1, 2, 1, tether, glow=tether_glow)
    box("hips", -9, 4, -6.5, 3, 3, 2, moss(347))

    # ---- chest: the spine of rubble behind, the iron cage, the split cuirass, the gorget
    box("chest", -3.5, -36, 3, 7, 36, 5, stone(350, moss=0.15))                # the spine column
    box("chest", -6, -6, -4, 12, 6, 8, stone(351))                             # the belly rubble
    box("chest", -6, -38, -5, 12, 3, 10, plate(352), kind="armour")            # gorget
    box("plates", -15, -34, -9, 12, 22, 3, plate(360), kind="armour")          # breastplate, right half
    box("plates", 3, -34, -9, 12, 22, 3, plate(361), kind="armour")            # left half (the gap shows the heart)
    box("plates", -14, -34, 5.5, 28, 24, 3, plate(362, verd=0.55), kind="armour")   # backplate
    box("plates", -17, -31, -6, 2, 18, 11, plate(363), kind="armour")
    box("plates", 15, -31, -6, 2, 18, 11, plate(364), kind="armour")
    box("plates", -10, -12, -8, 9, 7, 2, plate(365, verd=0.5), kind="armour")  # plackart, two pieces
    box("plates", 1, -11, -8, 9, 6, 2, plate(366, verd=0.5), kind="armour")
    box("plates", -3, -32, -8.5, 6, 1, 1, tether, glow=tether_glow)          # tethers across the split
    box("plates", -3, -24, -8.5, 6, 1, 1, tether, glow=tether_glow)
    box("plates", -3, -15, -8.5, 6, 1, 1, tether, glow=tether_glow)
    box("plates", -15, -14, -6, 2, 1, 1, tether, glow=tether_glow)
    box("plates", 13, -13, -6, 2, 1, 1, tether, glow=tether_glow)
    box("plates", -9, -36, -6, 3, 2, 3, moss(367), kind="armour")

    # ---- rubble the heart keeps hovering round itself
    for i, (x, y, z, sz) in enumerate(((-22, -22, 8, 4), (21, -8, 7, 3), (-20, 4, -8, 3), (23, -26, -5, 3))):
        box("debris", x, y, z, sz, sz, sz, stone(380 + i, moss=0.1))

    # ---- the cage: iron ribs round the heart
    for i, (x, z) in enumerate(((-10, -7), (8, -7), (-10, 4), (8, 4))):
        box("cage", x, -14, z, 2, 26, 2, iron_rib(370 + i))
    box("cage", -10, -15, -7, 20, 2, 2, iron_rib(375))
    box("cage", -10, 11, -7, 20, 2, 2, iron_rib(376))
    box("cage", -10, -15, 4, 20, 2, 2, iron_rib(377))
    box("cage", -10, -3, -8, 2, 2, 13, iron_rib(378))
    box("cage", 8, -3, -8, 2, 2, 13, iron_rib(379))

    # ---- the heart: a brass engine-heart, two ventricles, atria, copper arteries, a gauge, a valve wheel
    box("heart", -6, -6, -5, 12, 13, 10, heart_brass(400), glow=heart_glow(400))
    box("heart", 1, 0, -5.5, 6, 9, 9, heart_brass(401), glow=heart_glow(401))         # left ventricle, swollen
    box("heart", -4, 7, -4, 8, 3, 7, heart_brass(402, seams=False))                    # the apex
    box("heart", -6, -10, -4, 5, 4, 7, heart_brass(403, seams=False))                  # atria
    box("heart", 1, -10, -3, 5, 4, 6, heart_brass(404, seams=False))
    box("heart", -2, -17, -2, 3, 8, 3, copper_pipe(405))                               # aorta
    box("heart", -2, -18, -2, 9, 2, 3, copper_pipe(406))                               # its arch
    box("heart", 5, -18, -2, 2, 5, 3, copper_pipe(407))
    box("heart", -6, -14, 0, 2, 5, 2, copper_pipe(408))                                # pulmonary pipes
    box("heart", -9, -14, 0, 4, 2, 2, copper_pipe(409))
    box("heart", -3, -4, -6, 5, 5, 1, gauge)                                           # pressure gauge
    box("heart", -5, -22, -4, 7, 1, 7, valve_wheel)                                    # valve wheel on a stem
    box("heart", -2, -21, -1, 1, 4, 1, B.rod())
    box("heart", -7, 2, -2, 1, 4, 4, copper_pipe(410))                                 # a feed pipe out the side
    box("heart", -6.5, -1, -5.5, 2, 2, 1, heart_brass(411, seams=False), glow=AMBER_L)  # a vent glowing

    # ---- head: the floating helm, a broken crest fin
    box("head", -6.5, -13, -6.5, 13, 13, 13, helm_paint, glow=helm_glow, kind="armour")
    box("head", -0.5, -18, -3, 1, 6, 11, plate(420, verd=0.6), kind="armour")
    box("head", -7, -4, -7, 14, 2, 1, plate(421), kind="armour")
    box("head", -1, 1, -1, 2, 2, 2, tether, glow=tether_glow)                          # the tether to the gorget

    # ---- pauldrons: right a stack of lames, left a heaped double plate with a snapped crest-fin in it
    box("pauldron_r", -8, -6, -7.5, 11, 8, 15, plate(430), kind="armour")
    box("pauldron_r", -9, 1, -8, 11, 4, 16, plate(431, verd=0.55), kind="armour")
    box("pauldron_r", -9.5, 5, -7.5, 9, 3, 15, plate(432, verd=0.6), kind="armour")
    box("pauldron_l", -3, -8, -8.5, 13, 10, 17, plate(433), kind="armour")
    box("pauldron_l", -2, 1, -9, 13, 5, 18, plate(434, verd=0.55), kind="armour")
    box("pauldron_l", 3, -16, -2, 1, 9, 9, plate(435, verd=0.6), kind="armour")       # the crest-fin shard
    box("pauldron_l", 0, -10, -6, 6, 2, 5, moss(436), kind="armour")

    # ---- right arm: rubble core, plates, a gauntlet; the colossal sword fragment
    box("arm_r", -3, 0, -3, 6, 14, 6, stone(440))
    box("arm_r", -4, 2, -4.5, 8, 9, 1, plate(441), kind="armour")
    box("arm_r", -4.5, 11, -3.5, 2, 5, 7, plate(442, verd=0.6), kind="armour")         # couter
    box("fore_r", -2.5, 0, -2.5, 5, 13, 5, stone(443))
    box("fore_r", -3.5, 2, -3.5, 7, 9, 7, plate(444), kind="armour")                   # vambrace
    box("fore_r", -3.5, 12, -3.5, 7, 6, 7, plate(445, verd=0.4))                       # gauntlet (the fist stays)
    box("sword", -1, -6, -1, 2, 10, 2, B.LEATHER)   # grip
    box("sword", -1.5, -8, -1.5, 3, 2, 3, GOLD_D, kind="armour")                       # pommel
    box("sword", -8, 4, -2.5, 16, 3, 5, plate(450, verd=0.4), kind="armour")           # crossguard
    box("sword", -4, 7, -1.5, 8, 30, 3, blade(451), kind="armour")                     # the blade
    box("sword", -3.5, 39, -1.5, 7, 14, 3, blade(452), kind="armour")                  # past the crack
    box("sword", -2.5, 53, -1.5, 5, 5, 3, blade(453), kind="armour")                   # the broken point
    box("sword", -1, 37, -1, 2, 2, 2, tether, glow=tether_glow, kind="armour")         # the crack, held by a tether

    # ---- left arm: rubble core, plates; the great shield-plate on the forearm
    box("arm_l", -3, 0, -3, 6, 14, 6, stone(460))
    box("arm_l", -4, 2, -4.5, 8, 9, 1, plate(461), kind="armour")
    box("fore_l", -2.5, 0, -2.5, 5, 13, 5, stone(462))
    box("fore_l", -3.5, 2, -3.5, 7, 9, 7, plate(463), kind="armour")
    box("fore_l", -3.5, 12, -3.5, 7, 6, 7, plate(464, verd=0.4))
    box("shield", 0, -14, -11, 3, 30, 22, shield_face, glow=shield_glow, kind="armour")
    box("shield", 2, -10, -8, 2, 22, 16, plate(470, verd=0.5), kind="armour")          # the curve behind
    box("shield", -1, 0, -1, 1, 2, 2, tether, glow=tether_glow, kind="armour")

    # ---- the orbiting plates (phase 2 only): four big plates near, six chunks of rubble and bronze far
    for k in range(4):
        box(f"oi_{k}", -6, -8, -1, 12, 16, 2, plate(480 + k, verd=0.5), kind="orbit")
        box(f"oi_{k}", -0.5, -9, -1.5, 1, 1, 3, tether, glow=tether_glow, kind="orbit")
    for k in range(6):
        box(f"oo_{k}", -4, -4, -4, 8, 8, 8, stone(490 + k, moss=0.1), kind="orbit")
        box(f"oo_{k}", -5, -3, -5, 10, 6, 1, plate(496 + k, verd=0.5), kind="orbit")

    _anims(m)
    return m


ARMOUR_PARTS = ("plates", "head", "pauldron_r", "pauldron_l", "sword", "shield")


def _anims(m):
    # idle: the heart beats (lub-dub every second), the loose plates drift, the orbit rings spin (seen in phase 2)
    idle = m.anim("idle", 6.0)
    beat = []
    for i in range(6):
        t = i * 1.0
        beat += [(t, (1, 1, 1)), (t + 0.12, (1.1, 1.1, 1.1)), (t + 0.24, (1.0, 1.0, 1.0)),
                 (t + 0.36, (1.07, 1.07, 1.07)), (t + 0.55, (1, 1, 1))]
    beat.append((6.0, (1, 1, 1)))
    idle.scale("heart", *beat)
    idle.pos("head", (0, (0, 0, 0)), (1.5, (0, 1.0, 0)), (3.0, (0, 0, 0)), (4.5, (0, 1.2, 0)), (6.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (2, 6, 0)), (4.0, (-2, -5, 0)), (6.0, (0, 0, 0)))
    idle.pos("pauldron_r", (0, (0, 0, 0)), (1.2, (0, 0.8, 0)), (3.0, (0, -0.4, 0)), (4.8, (0, 0.6, 0)), (6.0, (0, 0, 0)))
    idle.pos("pauldron_l", (0, (0, 0, 0)), (1.8, (0, -0.8, 0)), (3.6, (0, 0.5, 0)), (6.0, (0, 0, 0)))
    idle.pos("plates", (0, (0, 0, 0)), (3.0, (0, 0.5, 0)), (6.0, (0, 0, 0)))
    idle.pos("shield", (0, (0, 0, 0)), (2.0, (0.6, 0, 0)), (4.0, (0, 0, 0)), (6.0, (0, 0, 0)))
    idle.rot("chest", (0, (0, 0, 0)), (3.0, (1.5, 0, 0)), (6.0, (0, 0, 0)))
    idle.rot("debris", (0, (0, 0, 0)), (6.0, (0, 360, 0), "linear"))
    idle.pos("debris", (0, (0, 0, 0)), (1.5, (0, 1.5, 0)), (3.0, (0, 0, 0)), (4.5, (0, -1.5, 0)), (6.0, (0, 0, 0)))
    idle.rot("orbit_in", (0, (0, 0, 0)), (6.0, (0, 720, 0), "linear"))
    idle.rot("orbit_out", (0, (0, 0, 0)), (6.0, (0, -360, 0), "linear"))
    for k in range(4):
        idle.rot(f"oi_{k}", (0, (0, 0, 0)), (1.5, (6, 0, 0)), (3.0, (0, 0, 0)), (4.5, (-6, 0, 0)), (6.0, (0, 0, 0)))
    for k in range(6):
        idle.rot(f"oo_{k}", (0, (0, 0, 0)), (6.0, (360, 0, 360), "linear"))

    walk = m.anim("walk", 2.4)
    walk.rot("thigh_r", (0, (-20, 0, 0)), (1.2, (20, 0, 0)), (2.4, (-20, 0, 0)))
    walk.rot("thigh_l", (0, (20, 0, 0)), (1.2, (-20, 0, 0)), (2.4, (20, 0, 0)))
    walk.rot("shin_r", (0, (10, 0, 0)), (0.6, (30, 0, 0)), (1.2, (0, 0, 0)), (2.4, (10, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.2, (10, 0, 0)), (1.8, (30, 0, 0)), (2.4, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.6, (0, 1.5, 0)), (1.2, (0, 0, 0)), (1.8, (0, 1.5, 0)), (2.4, (0, 0, 0)))
    walk.rot("chest", (0, (2, -6, 0)), (1.2, (2, 6, 0)), (2.4, (2, -6, 0)))
    walk.rot("arm_r", (0, (8, 0, 0)), (1.2, (-6, 0, 0)), (2.4, (8, 0, 0)))
    walk.rot("arm_l", (0, (-8, 0, 0)), (1.2, (6, 0, 0)), (2.4, (-8, 0, 0)))
    walk.pos("head", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (1.2, (0, 0, 0)), (1.8, (0, 1, 0)), (2.4, (0, 0, 0)))

    # sweep: the sword drawn back over the right shoulder (0.9 s = 18 ticks), swept round to the left (wide, low)
    a = m.anim("sweep", 1.75)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-80, 52, 0)), (0.9, (-82, 56, 0)), (0.98, (-82, -50, 0), "linear"),
          (1.25, (-80, -54, 0)), (1.75, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.75, (34, 0, 0)), (0.9, (36, 0, 0)), (1.25, (36, 0, 0)), (1.75, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.75, (28, 0, 0)), (0.9, (30, 0, 0)), (1.25, (30, 0, 0)), (1.75, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-4, 48, 0)), (0.98, (6, -50, 0), "linear"), (1.25, (6, -52, 0)), (1.75, (0, 0, 0)))
    a.rot("hips", (0, (0, 0, 0)), (0.9, (0, 16, 0)), (0.98, (0, -16, 0), "linear"), (1.75, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-20, 0, -30)), (1.25, (10, 0, -20)), (1.75, (0, 0, 0)))
    a.pos("pauldron_r", (0, (0, 0, 0)), (0.9, (-1.5, 1, 0)), (0.98, (1, 0, 0), "linear"), (1.75, (0, 0, 0)))

    # cleave: the sword raised high in both hands (1.1 s = 22 ticks), brought down straight ahead into the floor
    a = m.anim("cleave", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-170, 10, 10)), (1.1, (-176, 12, 10)), (1.18, (-34, 0, 4), "linear"),
          (1.7, (-32, 0, 4)), (2.2, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.1, (30, 0, 0)), (1.18, (10, 0, 0), "linear"), (2.2, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (1.1, (20, 0, 0)), (1.18, (16, 0, 0), "linear"), (1.7, (16, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (-150, -20, 20)), (1.18, (-50, 0, 0), "linear"), (1.7, (-48, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.18, (24, 0, 0), "linear"), (1.7, (22, 0, 0)), (2.2, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 1.5, 0)), (1.18, (0, -4, 0), "linear"), (1.7, (0, -4, 0)), (2.2, (0, 0, 0)))
    a.pos("head", (0, (0, 0, 0)), (1.1, (0, 2, 0)), (1.18, (0, -2, -1), "linear"), (2.2, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (1.1, (1.15, 1.15, 1.15)), (1.18, (0.9, 0.9, 0.9), "linear"), (2.2, (1, 1, 1)))

    # lunge: the sword drawn back at the hip, point forward (0.8 s = 16 ticks), then a long lunging thrust
    a = m.anim("lunge", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (30, -20, 10)), (0.8, (34, -22, 10)), (0.86, (-80, 0, 0), "linear"),
          (1.3, (-80, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (0.86, (36, 0, 0), "linear"), (1.3, (36, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (0.86, (22, 0, 0), "linear"), (1.3, (22, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 30, 0)), (0.86, (14, -14, 0), "linear"), (1.3, (14, -14, 0)), (2.1, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (0.86, (-40, 0, 0), "linear"), (1.3, (-40, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.86, (30, 0, 0), "linear"), (1.3, (30, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.86, (24, 0, 0), "linear"), (1.3, (24, 0, 0)), (2.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.8, (0, 0, 2)), (0.86, (0, -3, -4), "linear"), (1.3, (0, -3, -4)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.86, (30, 0, -20), "linear"), (1.3, (30, 0, -20)), (2.1, (0, 0, 0)))

    # shieldthrow: the shield-plate drawn across the body (0.9 s = 18 ticks), flung out like a discus at 0.9 s; the
    # arm stays out while it flies (2 s), and catches it at 2.9 s
    a = m.anim("shieldthrow", 3.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 60, -40)), (0.9, (-74, 64, -44)), (0.98, (-80, -40, -80), "linear"),
          (2.8, (-70, -30, -70)), (2.9, (-60, 30, -50)), (3.5, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (0.98, (60, 0, 0), "linear"), (2.9, (40, 0, 0)), (3.5, (0, 0, 0)))
    a.scale("shield", (0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.94, (0.01, 0.01, 0.01), "linear"), (2.86, (0.01, 0.01, 0.01)),
            (2.9, (1, 1, 1), "linear"), (3.5, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, -40, 0)), (0.98, (0, 30, 0), "linear"), (2.8, (0, 20, 0)),
          (2.9, (0, -10, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-10, 0, 20)), (2.9, (-10, 0, 20)), (3.5, (0, 0, 0)))

    # rubble: both arms raised, the heart flaring (1.0 s = 20 ticks): the chunks it tore from the walls are hurled
    a = m.anim("rubble", 2.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-150, 0, 40)), (1.0, (-156, 0, 44)), (1.06, (-70, 0, 10), "linear"),
          (2.2, (-70, 0, 10)), (2.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-150, 0, -40)), (1.0, (-156, 0, -44)), (1.06, (-70, 0, -10), "linear"),
          (2.2, (-70, 0, -10)), (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.06, (12, 0, 0), "linear"), (2.2, (10, 0, 0)), (2.9, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (1.0, (1.25, 1.25, 1.25)), (1.06, (0.92, 0.92, 0.92), "linear"),
            (1.6, (1.12, 1.12, 1.12)), (2.2, (1.0, 1.0, 1.0)), (2.9, (1, 1, 1)))
    a.pos("heart", (0, (0, 0, 0)), (1.0, (0, 2, 0)), (1.06, (0, 0, -2), "linear"), (2.9, (0, 0, 0)))
    for p in ("pauldron_r", "pauldron_l", "head"):
        a.pos(p, (0, (0, 0, 0)), (1.0, (0, 2.5, 0)), (1.06, (0, 0, 0), "linear"), (2.9, (0, 0, 0)))

    # magnet: arms thrown wide, the heart swelling (0.7 s = 14 ticks); the pull lasts to 2.2 s, then everything is
    # slammed shut (the clang at active tick 30 = 2.2 s)
    a = m.anim("magnet", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-90, 0, 60)), (0.7, (-92, 0, 64)), (2.1, (-96, 0, 70)),
          (2.2, (-80, 0, -20), "linear"), (2.6, (-76, 0, -16)), (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-90, 0, -60)), (0.7, (-92, 0, -64)), (2.1, (-96, 0, -70)),
          (2.2, (-80, 0, 20), "linear"), (2.6, (-76, 0, 16)), (3.1, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.7, (1.2, 1.2, 1.2)), (1.0, (1.1, 1.1, 1.1)), (1.3, (1.22, 1.22, 1.22)),
            (1.6, (1.1, 1.1, 1.1)), (1.9, (1.25, 1.25, 1.25)), (2.2, (0.85, 0.85, 0.85), "linear"), (3.1, (1, 1, 1)))
    a.scale("orbit_in", (0, (1, 1, 1)), (0.7, (1.2, 1, 1.2)), (2.1, (1.3, 1, 1.3)), (2.2, (0.3, 1, 0.3), "linear"),
            (2.6, (0.6, 1, 0.6)), (3.1, (1, 1, 1)))
    a.scale("orbit_out", (0, (1, 1, 1)), (0.7, (1.15, 1, 1.15)), (2.1, (1.2, 1, 1.2)), (2.2, (0.25, 1, 0.25), "linear"),
            (2.6, (0.6, 1, 0.6)), (3.1, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (2.1, (-12, 0, 0)), (2.2, (14, 0, 0), "linear"), (3.1, (0, 0, 0)))
    a.pos("plates", (0, (0, 0, 0)), (0.7, (0, 0, -1.5)), (2.1, (0, 0, -2)), (2.2, (0, 0, 0.5), "linear"), (3.1, (0, 0, 0)))

    # rings (phase 2): the heart rises in its cage and blazes (1.0 s = 20 ticks), then the plates sweep in rings for
    # 3.5 s while it hangs there, then it settles
    a = m.anim("rings", 5.2)
    a.pos("heart", (0, (0, 0, 0)), (1.0, (0, 6, 0)), (4.5, (0, 6, 0)), (5.2, (0, 0, 0)))
    a.pos("cage", (0, (0, 0, 0)), (1.0, (0, 5, 0)), (4.5, (0, 5, 0)), (5.2, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.9, (1.3, 1.3, 1.3)), (1.0, (1.35, 1.35, 1.35)), (1.06, (1.15, 1.15, 1.15), "linear"),
            (4.5, (1.15, 1.15, 1.15)), (5.2, (1, 1, 1)))
    a.scale("orbit_in", (0, (1, 1, 1)), (1.0, (0.8, 1, 0.8)), (1.06, (1.4, 1, 1.4), "linear"), (2.5, (1.6, 1, 1.6)),
            (3.0, (2.2, 1, 2.2)), (4.5, (2.2, 1, 2.2)), (5.2, (1, 1, 1)))
    a.scale("orbit_out", (0, (1, 1, 1)), (1.0, (0.9, 1, 0.9)), (1.06, (1.6, 1, 1.6), "linear"), (2.5, (1.8, 1, 1.8)),
            (3.0, (2.3, 1, 2.3)), (4.5, (2.3, 1, 2.3)), (5.2, (1, 1, 1)))
    a.rot("orbit_in", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (4.5, (0, 1080, 0), "linear"), (5.2, (0, 0, 0)))
    a.rot("orbit_out", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (4.5, (0, -720, 0), "linear"), (5.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-30, 0, 70)), (4.5, (-30, 0, 70)), (5.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-30, 0, -70)), (4.5, (-30, 0, -70)), (5.2, (0, 0, 0)))

    # platestorm (phase 2): the plates gather in a crown above the heart (0.8 s = 16 ticks), then fly out one by one
    a = m.anim("platestorm", 3.0)
    a.pos("orbit_in", (0, (0, 0, 0)), (0.8, (0, 14, 0)), (2.3, (0, 12, 0)), (3.0, (0, 0, 0)))
    a.scale("orbit_in", (0, (1, 1, 1)), (0.8, (0.55, 1, 0.55)), (0.86, (1.4, 1, 1.4), "linear"), (2.3, (1.2, 1, 1.2)),
            (3.0, (1, 1, 1)))
    a.rot("orbit_in", (0, (0, 0, 0)), (0.8, (0, 180, 0)), (2.3, (0, 900, 0), "linear"), (3.0, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.8, (1.2, 1.2, 1.2)), (0.86, (0.9, 0.9, 0.9), "linear"), (1.2, (1.15, 1.15, 1.15)),
            (1.6, (0.95, 0.95, 0.95)), (2.0, (1.15, 1.15, 1.15)), (2.3, (1, 1, 1)), (3.0, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-160, 0, 20)), (0.86, (-100, 0, 20), "linear"), (2.3, (-100, 0, 30)),
          (3.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (0.86, (8, 0, 0), "linear"), (3.0, (0, 0, 0)))

    # vent (phase 2): the heart contracts (0.7 s = 14 ticks) and bursts steam out of every seam
    a = m.anim("vent", 1.6)
    a.scale("heart", (0, (1, 1, 1)), (0.6, (0.82, 0.82, 0.82)), (0.7, (0.8, 0.8, 0.8)), (0.74, (1.4, 1.4, 1.4), "linear"),
            (1.0, (1.2, 1.2, 1.2)), (1.6, (1, 1, 1)))
    a.scale("cage", (0, (1, 1, 1)), (0.7, (0.92, 0.95, 0.92)), (0.74, (1.15, 1.05, 1.15), "linear"), (1.6, (1, 1, 1)))
    a.scale("orbit_in", (0, (1, 1, 1)), (0.7, (0.8, 1, 0.8)), (0.74, (1.5, 1, 1.5), "linear"), (1.6, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.74, (-10, 0, 0), "linear"), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-20, 0, -10)), (0.74, (-40, 0, 60), "linear"), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-20, 0, 10)), (0.74, (-40, 0, -60), "linear"), (1.6, (0, 0, 0)))

    # reforge (phase 3, once): the rings close in on the heart (1.5 s = 30 ticks) and the plates slam back on, bigger
    a = m.anim("reforge", 3.5)
    a.scale("orbit_in", (0, (1, 1, 1)), (1.2, (0.5, 1, 0.5)), (1.45, (0.05, 0.4, 0.05)), (1.5, (0.01, 0.01, 0.01)),
            (3.45, (0.01, 0.01, 0.01)), (3.5, (1, 1, 1), "linear"))
    a.scale("orbit_out", (0, (1, 1, 1)), (1.2, (0.4, 1, 0.4)), (1.45, (0.05, 0.4, 0.05)), (1.5, (0.01, 0.01, 0.01)),
            (3.45, (0.01, 0.01, 0.01)), (3.5, (1, 1, 1), "linear"))
    a.rot("orbit_in", (0, (0, 0, 0)), (1.5, (0, 1080, 0)), (3.5, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (1.4, (1.4, 1.4, 1.4)), (1.5, (1.45, 1.45, 1.45)), (1.56, (1.0, 1.0, 1.0), "linear"),
            (3.5, (1, 1, 1)))
    for p in ARMOUR_PARTS:
        a.scale(p, (0, (1, 1, 1)), (1.5, (1.3, 1.3, 1.3)), (1.56, (0.96, 0.96, 0.96), "linear"), (1.8, (1.04, 1.04, 1.04)),
                (2.2, (1, 1, 1)), (3.5, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.4, (-40, 0, 80)), (1.5, (-42, 0, 84)), (1.56, (-20, 0, 10), "linear"),
          (2.6, (-20, 0, 10)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.4, (-40, 0, -80)), (1.5, (-42, 0, -84)), (1.56, (-20, 0, -10), "linear"),
          (2.6, (-20, 0, -10)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-18, 0, 0)), (1.56, (16, 0, 0), "linear"), (2.6, (14, 0, 0)), (3.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, -3, 0)), (1.56, (0, -6, 0), "linear"), (2.6, (0, -5, 0)), (3.5, (0, 0, 0)))

    # quake (phase 3): the sword lifted point-down in both hands (0.9 s = 18 ticks), driven into the floor of the
    # helm; it stays planted while the debris falls (1.5 s), then is wrenched out
    a = m.anim("quake", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-150, 0, 30)), (0.9, (-154, 0, 30)), (0.96, (-40, 0, 10), "linear"),
          (2.4, (-40, 0, 10)), (3.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (-60, 0, 0)), (0.96, (-20, 0, 0), "linear"), (2.4, (-20, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.9, (160, 0, 0)), (0.96, (150, 0, 0), "linear"), (2.4, (150, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-140, 0, -30)), (0.96, (-40, 0, -10), "linear"), (2.4, (-40, 0, -10)),
          (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (0.96, (22, 0, 0), "linear"), (2.4, (20, 0, 0)), (3.1, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, 2, 0)), (0.96, (0, -5, 0), "linear"), (2.4, (0, -5, 0)), (3.1, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.9, (1.2, 1.2, 1.2)), (0.96, (0.9, 0.9, 0.9), "linear"), (1.3, (1.15, 1.15, 1.15)),
            (1.7, (0.95, 0.95, 0.95)), (2.1, (1.12, 1.12, 1.12)), (2.4, (1, 1, 1)), (3.1, (1, 1, 1)))

    # burst (the phase-2 roar): the heart flares and the armour blows apart (the plates fly out and shrink away; the
    # entity switches to the burst texture at 1.5 s, when they are gone), the orbit rings take their place
    a = m.anim("burst", 2.5)
    a.scale("heart", (0, (1, 1, 1)), (0.8, (1.4, 1.4, 1.4)), (0.9, (1.5, 1.5, 1.5)), (0.95, (1.0, 1.0, 1.0), "linear"),
            (1.6, (1.2, 1.2, 1.2)), (2.5, (1, 1, 1)))
    outs = {"plates": (0, 6, -14), "head": (0, 16, -6), "pauldron_r": (-14, 6, 0), "pauldron_l": (14, 8, 0),
            "sword": (-6, -4, -16), "shield": (16, 0, -4)}
    for p, (x, y, z) in outs.items():
        a.pos(p, (0, (0, 0, 0)), (0.9, (x * 0.05, y * 0.05, z * 0.05)), (1.3, (x, y, z)), (2.45, (x * 1.4, y * 1.4, z * 1.4)),
              (2.5, (0, 0, 0), "linear"))
        a.scale(p, (0, (1, 1, 1)), (0.9, (1, 1, 1)), (1.4, (0.5, 0.5, 0.5)), (2.45, (0.2, 0.2, 0.2)),
                (2.5, (1, 1, 1), "linear"))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (0.95, (10, 0, 0), "linear"), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-40, 0, 40)), (1.0, (-90, 0, 100), "linear"), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -40)), (1.0, (-90, 0, -100), "linear"), (2.5, (0, 0, 0)))
    a.scale("orbit_in", (0, (0.01, 0.01, 0.01)), (1.45, (0.01, 0.01, 0.01)), (1.55, (1.6, 1, 1.6), "linear"),
            (2.5, (1, 1, 1)))
    a.scale("orbit_out", (0, (0.01, 0.01, 0.01)), (1.45, (0.01, 0.01, 0.01)), (1.55, (1.8, 1, 1.8), "linear"),
            (2.5, (1, 1, 1)))

    # stagger: the heart misfires, the body sags, the plates rattle
    a = m.anim("stagger", 2.5)
    a.rot("chest", (0, (0, 0, 0)), (0.2, (24, 0, 10)), (1.8, (20, 0, 8)), (2.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.2, (0, -6, 0)), (1.8, (0, -5, 0)), (2.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (1.8, (-26, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.2, (50, 0, 0)), (1.8, (46, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (20, 0, 30)), (1.8, (16, 0, 26)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (20, 0, -30)), (1.8, (16, 0, -26)), (2.5, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.2, (0.8, 0.8, 0.8)), (0.5, (1.1, 1.1, 1.1)), (0.8, (0.85, 0.85, 0.85)),
            (1.2, (1.05, 1.05, 1.05)), (1.8, (0.9, 0.9, 0.9)), (2.5, (1, 1, 1)))
    a.pos("head", (0, (0, 0, 0)), (0.2, (2, -4, -2)), (1.0, (1, -3, -1)), (1.8, (2, -4, -2)), (2.5, (0, 0, 0)))
    for p in ("pauldron_r", "pauldron_l", "plates"):
        a.pos(p, (0, (0, 0, 0)), (0.3, (0, -1.5, 0)), (0.6, (0, 0.5, 0)), (0.9, (0, -1, 0)), (1.8, (0, -1, 0)),
              (2.5, (0, 0, 0)))
