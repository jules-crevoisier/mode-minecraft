"""The Root Mother (La Mère-Racine): a towering treant matriarch, about 5 blocks tall plus her crown.

Silhouette: a hunched bark giantess whose head carries a wide, asymmetric crown of branches heavy with
leaves and hanging moss; ape-long arms (a massive right arm with a thorned bracer, a slender ivy-wound left
arm with whip-like fingers) end in root claws; her legs split into roots at the feet. A pale carved mask
hides her face; her chest is a hollow cage of roots around a glowing amber heart that beats.
"""
import math

from ..models import Model
from ..texgen import mix, mul

BARK = (88, 63, 44)
BARK_D = (56, 39, 28)
BARK_L = (128, 98, 70)
FURROW = (33, 23, 17)
LICHEN = (150, 162, 128)
MOSS = (80, 116, 44)
MOSS_D = (48, 76, 30)
MOSS_L = (124, 156, 64)
LEAF = (66, 122, 50)
LEAF_D = (36, 80, 34)
LEAF_L = (112, 164, 72)
PINK = (232, 150, 196)
PINK_D = (180, 96, 150)
PINK_L = (252, 200, 228)
BLOSSOM_C = (255, 226, 120)
MASK = (226, 214, 186)
MASK_D = (172, 156, 126)
MASK_L = (244, 236, 214)
OCHRE = (168, 52, 36)
HEART = (255, 196, 84)
HEART_C = (255, 246, 196)
SAP = (255, 156, 52)
EYE = (176, 255, 156)
FUNGUS = (236, 142, 58)
FUNGUS_L = (255, 196, 110)
ROOT = (104, 78, 56)
CAVE = (40, 24, 16)


def _h(*args):
    """Deterministic hash of integers -> [0, 1)."""
    v = 0x9E3779B1
    for a in args:
        v = ((v ^ (int(a) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        v ^= v >> 13
        v = (v * 0xC2B2AE35) & 0xFFFFFFFF
        v ^= v >> 16
    return (v & 0xFFFF) / 65536.0


FID = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


# ---------------------------------------------------------------------------------------------- painters
def bark(seed=0, moss=2, base=BARK, lichen=0.02, knots=True, twist=0.0, top_moss=0.45):
    """Fluted bark: long vertical furrows that wander gently, a lit ridge beside each furrow, rare plate
    breaks, small lichen clumps, a knot per large face, and moss creeping down from the top edge."""
    def f(face, x, y, w, h):
        fid = FID[face]
        if face == "top":
            if _h(x // 2, y // 2, seed, 7) < top_moss:
                return mix(MOSS, MOSS_L if (x + y) % 3 == 0 else MOSS_D, 0.4)
            ring = int(math.hypot(x - w / 2, y - h / 2)) % 2
            return mul(BARK_L, 0.92) if ring else mul(base, 0.95)
        if face == "bottom":
            return mul(BARK_D, 0.8)
        col = x + round(1.0 * math.sin(y * 0.28 + seed * 1.7 + fid)) + int(y * twist)
        p = (col + seed) % 6
        c = (FURROW, BARK_D, base, base, BARK_L, mix(base, BARK_L, 0.45))[p]
        if p == 0 and _h(col // 6, y // 4, seed, fid) < 0.1:
            c = BARK_D                       # furrows break into plates now and then
        if p in (2, 3) and _h(col // 6, y, seed + 3, fid) < 0.03:
            c = FURROW                       # a short crack across a plate
        if _h(x // 2, y // 2, seed, fid, 11) < lichen:
            c = LICHEN if (x + y) % 2 else mix(LICHEN, base, 0.4)
        if knots and w >= 6 and h >= 9:
            kx = 2 + int(_h(seed, fid, 1) * (w - 4))
            ky = 2 + int(_h(seed, fid, 2) * (h - 5))
            d = ((x - kx) / 1.6) ** 2 + ((y - ky) / 2.2) ** 2
            if d < 1.0:
                c = FURROW if d < 0.5 else mix(FURROW, BARK_D, 0.5)
            elif d < 2.3:
                c = BARK_L if d < 1.6 else mix(BARK_L, base, 0.5)
        if moss and y < moss + int(_h(x, seed, fid) * (moss + 2)) - 1:
            c = mix(MOSS, MOSS_D if (x + y) % 3 == 0 else MOSS_L, 0.35)
        return c
    return f


def ivy_bark(seed=0):
    """Slender limb wound with a spiral of ivy."""
    b = bark(seed, moss=1, knots=False)

    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return b(face, x, y, w, h)
        off = {"front": 0, "left": w, "back": 2 * w, "right": 3 * w}.get(face, 0)
        u = (x + off + y) % 11
        if u in (0, 1, 2):
            if u == 1 and y % 3 == 0:
                return LEAF_L
            return LEAF_D if u == 2 else LEAF
        return b(face, x, y, w, h)
    return f


def sap_cracks(seed=0, faces=("front",)):
    """Glow layer: one thin amber vein that forks down a bark face, fading out."""
    def f(face, x, y, w, h):
        if face not in faces:
            return None
        x0 = 1 + int(_h(seed, FID[face]) * (w - 2))
        y0 = int(_h(seed, 2, FID[face]) * h * 0.3)
        ln = int(h * 0.55)
        if not (y0 <= y < y0 + ln):
            return None
        path = x0 + round(1.2 * math.sin((y - y0) * 0.55 + seed))
        fork = path + (y - y0 - ln // 2) // 2 if y - y0 > ln // 2 else None
        if x == path or x == fork:
            return SAP if (y - y0) < ln - 3 else mix(SAP, (120, 60, 20), 0.5)
        return None
    return f


def heart_walls(face, x, y, w, h):
    """Glow layer for the heart cavity walls: veins radiating from the heart."""
    if face in ("top", "bottom"):
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    a = math.atan2(y - cy, x - cx)
    k = round(a / (math.pi / 3))
    if abs(a - k * math.pi / 3) < 0.16 and math.hypot(x - cx, y - cy) > 1.5:
        return mix(SAP, HEART, 0.4)
    return None


def heart_paint(face, x, y, w, h):
    d = math.hypot(x - (w - 1) / 2, y - (h - 1) / 2)
    if d < 1.0:
        return HEART_C
    if d < 2.0:
        return HEART
    # a few dark veins on the rim of the heart
    return (190, 92, 30) if (x + 2 * y) % 4 == 0 else SAP


def cavity(seed=0):
    """Dark, sap-soaked wood inside the chest hollow."""
    def f(face, x, y, w, h):
        return mix(CAVE, (96, 52, 22), _h(x // 2, y, seed) * 0.5)
    return f


def leaves(seed=0, ragged=3, pink=False, holes=0.4):
    """Leaf mass painted as overlapping clumps: each 3x3 clump is lit on its upper-left and shadowed on its
    lower-right, clumps alternate shades; the lower edge is cut out raggedly. ``pink`` paints blossom."""
    lo, mid, hi = (PINK_D, PINK, PINK_L) if pink else (LEAF_D, LEAF, LEAF_L)

    def f(face, x, y, w, h):
        fid = FID[face]
        if face not in ("top", "bottom"):
            if y >= h - 1 - int(_h(x // 2, seed, fid) * ragged):
                return None
            if (x == 0 or x == w - 1) and _h(x, y // 2, seed, fid, 4) < holes:
                return None
        elif face == "bottom":
            if _h(x, y, seed, 2) < 0.3:
                return None
        sx = x + (1 if (y // 3) % 2 else 0)
        cx, cy, lx, ly = sx // 3, y // 3, sx % 3, y % 3
        shade = _h(cx, cy, seed, fid)
        c = lo if shade < 0.28 else mid if shade < 0.8 else hi
        if lx == 0 and ly == 0:
            c = mix(c, hi, 0.6)
        elif lx == 2 and ly == 2:
            c = mix(c, lo, 0.6)
        if face == "top":
            c = mix(c, hi, 0.2)
        r = _h(x, y, seed, fid, 8)
        if not pink and r < 0.02:
            return PINK_L
        if pink and r < 0.03:
            return BLOSSOM_C
        if not pink and r > 0.99:
            return (186, 40, 50)
        return c
    return f


def leaf_glow(seed=0):
    """Glow layer for leaf masses: sparse fireflies and golden pollen glinting inside the canopy."""
    def f(face, x, y, w, h):
        if face == "bottom" or y >= h - 3:
            return None
        r = _h(x, y, seed, FID[face], 21)
        if r < 0.012:
            return (236, 255, 150)
        if r < 0.02:
            return (255, 214, 110)
        return None
    return f


def moss_strands(seed=0, density=0.75, dark=False):
    """Hanging moss (for zero-thickness planes): stringy strands of varying length, cut-out between them."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if _h(x, seed, 1) > density:
            return None
        ln = h * (0.3 + 0.7 * _h(x, seed, 2))
        if y > ln:
            return None
        if y > ln - 2 and (x + y) % 2:
            return None
        c = MOSS_D if _h(x, seed, 3) < 0.4 else MOSS
        if y % 4 == int(_h(x, seed, 5) * 4):
            c = MOSS_L
        if dark:
            c = mix(c, (52, 66, 40), 0.45)
        if y < 2:
            c = mix(c, (40, 60, 26), 0.4)
        return c
    return f


def rootlets(seed=0, density=0.55):
    """Hanging rootlets (planes): thin brown strands."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if _h(x, seed, 1) > density:
            return None
        ln = h * (0.3 + 0.7 * _h(x, seed, 2))
        if y > ln:
            return None
        return ROOT if _h(x, y // 3, seed) < 0.7 else BARK_D
    return f


def mask_paint(face, x, y, w, h):
    """The carved mask: pale wood with a brow arch, hollow eyes, thin ochre tears, a branching forehead
    sigil, a crack, and a narrow mouth of splinter teeth."""
    if face != "front":
        return MASK_L if face == "top" else MASK_D
    cx = (w - 1) / 2
    ex = abs(x - cx)
    c = mul(MASK, 1 + 0.035 * math.sin(x * 1.3 + y * 0.2))
    if x in (0, w - 1):
        c = MASK_D
    if y >= h - 2 and ex > 3:
        c = MASK_D
    # brow arch over each eye: lit ridge, carved shadow below
    if y == 4 and 1.5 <= ex <= 4.5:
        c = MASK_L
    if y == 5 and 1.5 <= ex <= 4.5:
        c = MASK_D
    # eye sockets (the glow is painted separately)
    if 6 <= y <= 8 and 1.5 <= ex <= 4.5:
        if y == 8 and ex > 3.5 or y == 6 and ex < 2:
            return MASK_D
        return (16, 12, 10)
    # thin ochre tears
    if 9 <= y <= 13 and ex == 3.5:
        return OCHRE if y < 13 else mix(OCHRE, MASK, 0.5)
    # forehead sigil: a little tree
    if (ex < 0.6 and 0 <= y <= 3) or (y == 1 and 0.6 < ex < 1.6) or (y == 0 and 1.6 < ex < 2.6):
        return OCHRE
    # crack through the right brow
    if x == 3 + (y // 3) and y <= 4:
        c = (64, 50, 40)
    # a thin closed mouth, carved
    if y == 12 and ex <= 1.5:
        return (52, 40, 32)
    if y == 13 and ex <= 0.5:
        return MASK_D
    # carved cheek grooves framing the face
    if 9 <= y <= 13 and ex == 5.5 - (y - 9) // 2:
        return MASK_D
    return c


def mask_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx = (w - 1) / 2
    ex = abs(x - cx)
    if y == 7 and 2.5 <= ex <= 3.5:
        return EYE
    if (y == 6 and 2.5 <= ex <= 4.5) or (y == 7 and ex == 4.5) or (y == 8 and ex == 2.5):
        return mul(EYE, 0.55)
    return None


def fungus(face, x, y, w, h):
    if face == "top":
        return FUNGUS_L if (x + y) % 3 else (255, 230, 170)
    if face == "bottom":
        return (180, 120, 70) if x % 2 else (140, 90, 50)
    return FUNGUS if y == 0 else mul(FUNGUS, 0.8)


def fungus_glow(face, x, y, w, h):
    if face == "bottom":
        return None
    return (255, 180, 96) if face == "top" or y == 0 else None


def claw(seed=0):
    """Root claw: bark that darkens to a polished black tip."""
    b = bark(seed, moss=0, lichen=0.0, knots=False, top_moss=0)

    def f(face, x, y, w, h):
        t = y / max(1, h - 1)
        if face in ("top", "bottom"):
            return mul(BARK_D, 0.7)
        c = b(face, x, y, w, h)
        return mix(c, (26, 20, 16), min(1.0, (t - 0.3) * 1.4)) if t > 0.3 else c
    return f


def thorn(face, x, y, w, h):
    return (214, 200, 160) if face == "top" or x == 0 else (124, 102, 72)


# ---------------------------------------------------------------------------------------------- builder
def build():
    m = Model("root_mother", seed=78, shadow=1.8, walk_speed=0.7, walk_scale=1.0)
    seq = [0]
    pods = []

    def nid(prefix):
        seq[0] += 1
        return f"{prefix}{seq[0]}"

    def limb(parent, pivot, rot, segs, seed):
        """A chain of bark segments pointing up (-y) from ``pivot``: segs = [(length, thick, bend_rot)].
        Returns the segment part names (the last one is the tip)."""
        names = []
        par, piv = parent, pivot
        for i, (ln, t, bend) in enumerate(segs):
            n = m.part(nid("br"), par, pivot=piv, rot=rot if i == 0 else bend)
            m.box(n, -t / 2, -ln, -t / 2, t, ln, t, bark(seed + i, moss=1, knots=False, top_moss=0.2))
            names.append(n)
            par, piv = n, (0, -ln + 1, 0)
        return names

    def canopy(parent, cx, cy, cz, w, h, d, seed, pink=False, moss=14):
        """A leaf mass: a broad body, a drooping lobe on one side, a smaller cap, a moss curtain below."""
        m.box(parent, cx - w / 2, cy - h, cz - d / 2, w, h, d, leaves(seed, pink=pink), glow=leaf_glow(seed))
        lw, lh, ld = max(4, w // 2), max(3, h - 2), max(4, d - 4)
        m.box(parent, cx - w / 2 - lw / 2, cy - lh + 2, cz - ld / 2, lw, lh, ld, leaves(seed + 1, pink=pink))
        cw, cd = max(4, w - 6), max(4, d - 5)
        m.box(parent, cx - cw / 2 + 1, cy - h - 3, cz - cd / 2, cw, 4, cd, leaves(seed + 2, pink=pink, ragged=1))
        # an amber sap pod hanging under the mass
        pod = m.part(nid("pod"), parent, pivot=(cx + w / 4, cy - 1, cz))
        m.box(pod, -0.5, 0, -0.5, 1, 3, 1, (90, 60, 30))
        m.box(pod, -1, 3, -1, 2, 3, 2, heart_paint, glow=heart_paint)
        pods.append(pod)
        if moss:
            m.box(parent, cx - w / 2 + 1, cy - 2, cz - d / 2 - 0.3, w - 2, moss, 0, moss_strands(seed + 50))
            m.box(parent, cx - w / 2 + 2, cy - 2, cz + d / 2 - 1, w - 3, moss - 3, 0, moss_strands(seed + 51))

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -32, 0))
    m.part("torso", "hips", pivot=(0, -4, 0), rot=(12, 0, 0))
    m.part("chest", "torso", pivot=(0, -9, 0), rot=(0, -5, 0))
    m.part("heart", "chest", pivot=(0, -10, -3))
    m.part("neck", "chest", pivot=(0, -20, -1), rot=(-4, 0, 0))
    m.part("head", "neck", pivot=(0, -6, 0), rot=(-10, 0, 0))
    m.part("mask", "head", pivot=(0, -4, -4))
    m.part("hair", "head", pivot=(0, -9, 4), rot=(8, 0, 0))
    m.part("crown", "head", pivot=(0, -10, 1))
    m.part("shawl", "chest", pivot=(0, -19, 6), rot=(10, 0, 0))
    m.part("arm_r", "chest", pivot=(-13, -16, 0), rot=(-10, 0, 12))
    m.part("forearm_r", "arm_r", pivot=(0, 16, 0), rot=(-22, 0, -4))
    m.part("hand_r", "forearm_r", pivot=(0, 16, 0))
    m.part("arm_l", "chest", pivot=(12, -16, 0), rot=(-6, 0, -12))
    m.part("forearm_l", "arm_l", pivot=(0, 16, 0), rot=(-16, 0, 4))
    m.part("hand_l", "forearm_l", pivot=(0, 17, 0))
    m.part("leg_r", "bone", pivot=(-5, -32, 0), rot=(0, 0, 7))
    m.part("shin_r", "leg_r", pivot=(0, 15, 0))
    m.part("foot_r", "shin_r", pivot=(0, 13, 0), rot=(0, 0, -7))
    m.part("leg_l", "bone", pivot=(5, -32, 0), rot=(0, 0, -7))
    m.part("shin_l", "leg_l", pivot=(0, 15, 0))
    m.part("foot_l", "shin_l", pivot=(0, 13, 0), rot=(0, 0, 7))
    m.part("skirt", "hips", pivot=(0, 2, 0))

    # ------------------------------------------------------------------ hips and the skirt of rootlets
    m.box("hips", -8, -5, -6, 16, 8, 12, bark(1, moss=0))
    m.box("skirt", -8, 0, -6.4, 16, 12, 0, rootlets(3))
    m.box("skirt", -8, 0, 6.4, 16, 14, 0, rootlets(4))
    m.box("skirt", -8.4, 0, -6, 0, 13, 12, rootlets(5))
    m.box("skirt", 8.4, 0, -6, 0, 11, 12, rootlets(6))
    for i, (x, z, ln) in enumerate(((-6.5, -6.5, 10), (-1, -6.8, 7), (4, -6.5, 12), (7, 2, 9), (-8, 3, 11),
                                    (2, 6, 8))):
        m.box("skirt", x, -1, z, 2, ln, 2, claw(60 + i))

    # ------------------------------------------------------------------ torso: twisted waist, root-cage chest
    m.box("torso", -5.5, -10, -4.5, 11, 10, 9, bark(2, moss=0, twist=0.35))
    # chest frame around the heart hollow (x -5..5, 12 high, open to the front)
    m.box("chest", -10, -20, -6, 5, 20, 12, {"left": cavity(1), "*": bark(3, twist=0.3, moss=0)},
          glow={"front": sap_cracks(31)})
    m.box("chest", 5, -20, -6, 5, 20, 12, {"right": cavity(2), "*": bark(4, twist=0.3, moss=0)},
          glow={"front": sap_cracks(32)})
    m.box("chest", -5, -20, -6, 10, 4, 12, {"bottom": cavity(3), "*": bark(5, moss=0)})
    m.box("chest", -5, -4, -6, 10, 4, 12, {"top": cavity(4), "*": bark(6, moss=0)})
    m.box("chest", -5, -16, -1, 10, 12, 7, {"front": cavity(5), "*": bark(7)}, glow={"front": heart_walls})
    # sloping shoulder masses (no flat table top): two stepped burls
    m.box("chest", -11, -22, -5, 8, 3, 10, bark(8, moss=1, top_moss=0.6))
    m.box("chest", 3, -22, -5, 8, 3, 10, bark(9, moss=1, top_moss=0.6))
    # the heart and the roots caging it
    m.box("heart", -3, -3, -3, 6, 6, 6, heart_paint, glow=heart_paint)
    for i, (rz, ln, dz, dy) in enumerate(((40, 15, -5.6, 0), (-36, 15, -5.4, 0), (90, 13, -6.0, 0),
                                          (8, 11, -5.8, 4))):
        n = m.part(f"rib{i}", "chest", pivot=(0, -10 + dy, dz), rot=(0, 0, rz))
        m.box(n, -ln / 2, -0.5, -0.5, ln, 1, 1, claw(70 + i))
    # bracket fungi stepping up the flanks
    for i, (x, y, z, w, d) in enumerate(((-12.5, -8, -2, 3, 4), (-12, -12, 1, 2, 3), (10, -15, -3, 3, 4),
                                         (10, -6, 0, 2, 3), (10, -10, 2, 2, 2))):
        m.box("chest", x, y, z, w, 1, d, fungus, glow=fungus_glow)

    # a mossy shawl down the back
    m.box("shawl", -10, 0, 0.5, 20, 30, 0, moss_strands(9, density=0.92))
    m.box("shawl", -7, 1, 1.0, 14, 24, 0, moss_strands(19, density=0.7, dark=True))

    # ------------------------------------------------------------------ neck, head, mask, hair
    m.box("neck", -3, -7, -3, 6, 8, 6, bark(10, moss=0, twist=0.4))
    m.box("head", -5, -10, -4, 10, 10, 9, bark(11, moss=2))
    m.box("mask", -6, -8, -2, 12, 16, 2, mask_paint, glow={"front": mask_glow})
    m.box("mask", -3.5, 8, -1.8, 7, 3, 2, {"front": lambda f, x, y, w, h: MASK_D if y == h - 1 else MASK,
                                           "*": MASK_D})
    m.box("mask", -1, 11, -1.6, 2, 2, 2, MASK_D)
    m.box("hair", -6, 0, 0, 12, 28, 0, moss_strands(12, density=0.9))
    m.box("hair", -6.5, 2, -4, 0, 16, 5, moss_strands(13, density=0.6))
    m.box("hair", 6.5, 2, -4, 0, 18, 5, moss_strands(14, density=0.6))

    # ------------------------------------------------------------------ crown of branches
    # the great right bough: the heaviest mass of the crown, leaning out over the shoulder
    b = limb("crown", (-3, 0, 0), (-6, 0, -46), [(20, 5, None), (14, 4, (0, 0, 34)), (8, 3, (0, 0, 20))], 20)
    canopy(b[1], -4, -8, 0, 24, 10, 18, 1, moss=18)
    canopy(b[2], 1, -5, 0, 13, 6, 12, 2, moss=0)
    twig = m.part(nid("br"), b[0], pivot=(0, -10, 0), rot=(20, 0, -55))
    m.box(twig, -1, -9, -1, 2, 9, 2, bark(25, moss=0, knots=False))
    canopy(twig, 0, -8, 0, 12, 6, 10, 3, moss=12)

    # the left bough: lower, flowering pink
    b = limb("crown", (3, 0, 0), (-2, 0, 40), [(16, 4, None), (14, 3, (0, 0, -30)), (8, 2, (10, 0, -20))], 30)
    canopy(b[1], 3, -8, 0, 20, 9, 16, 4, pink=True, moss=16)
    canopy(b[2], 0, -5, 0, 12, 6, 10, 5, moss=0)

    # the tall central leader
    b = limb("crown", (0, 0, 2), (-20, 0, -4), [(22, 4, None), (12, 3, (12, 0, 14))], 40)
    canopy(b[1], 0, -9, 0, 16, 8, 14, 6, moss=10)

    # a back bough
    b = limb("crown", (2, 0, 3), (-36, 0, 22), [(15, 3, None), (8, 2, (-10, 0, 18))], 50)
    canopy(b[1], 0, -7, 0, 15, 7, 13, 7)

    # a broken branch over the brow, hung with moss
    b = limb("crown", (-2, 1, -2), (26, 0, -16), [(9, 2, None)], 60)
    m.box(b[0], -1.5, -9, -1.2, 3, 7, 0, moss_strands(61))

    # ------------------------------------------------------------------ the massive right arm
    m.box("arm_r", -6, -5, -5, 10, 9, 10, bark(70, moss=3, top_moss=0.7))      # burl shoulder
    m.box("arm_r", -7, -6, -1, 3, 1, 3, fungus, glow=fungus_glow)
    m.box("arm_r", -4.5, -8, -3, 2, 4, 2, bark(75, moss=0, knots=False))        # a snapped twig
    m.box("arm_r", -4, 0, -4, 8, 17, 8, bark(71, moss=0))
    m.box("forearm_r", -4.5, 0, -4.5, 9, 16, 9, bark(72, moss=0))
    for i, (x, y, z, w, h, d) in enumerate(((-6.5, 3, -1, 2, 1, 1), (-6.5, 8, 1, 2, 1, 1), (4.5, 5, -2, 2, 1, 1),
                                            (4.5, 9, 2, 2, 1, 1), (-1, 4, -6.5, 1, 1, 2), (1, 8, -6.5, 1, 1, 2),
                                            (-2, 6, 4.5, 1, 1, 2))):
        m.box("forearm_r", x, y, z, w, h, d, thorn)
    m.box("forearm_r", -5, 11, -5, 10, 3, 10, bark(73, moss=0, base=BARK_D, top_moss=0))   # wrist band
    m.box("hand_r", -4, 0, -4, 8, 4, 8, bark(74, moss=0, top_moss=0))
    for i, (x, z, rx, rz) in enumerate(((-3, -3, -18, 14), (-1, -3.5, -22, 4), (1.5, -3, -20, -6),
                                        (3, -1, -10, -20))):
        f = m.part(f"claw_r{i}", "hand_r", pivot=(x, 3, z), rot=(rx, 0, rz))
        m.box(f, -1, 0, -1, 2, 9, 2, claw(80 + i))
        t = m.part(f"tip_r{i}", f, pivot=(0, 8.5, 0), rot=(-28, 0, 0))
        m.box(t, -1, 0, -1, 2, 8, 2, claw(84 + i))
    th = m.part("thumb_r", "hand_r", pivot=(-3.5, 2, 1), rot=(10, 0, 40))
    m.box(th, -1, 0, -1, 2, 8, 2, claw(88))

    # ------------------------------------------------------------------ the slender left arm, whip fingers
    m.box("arm_l", -4, -4, -4, 8, 7, 8, bark(90, moss=3, top_moss=0.7))
    sap = m.part("sapling", "arm_l", pivot=(1, -3, 0), rot=(0, 0, -14))      # a sapling sprouting from it
    m.box(sap, -1, -8, -1, 2, 8, 2, bark(91, moss=0, knots=False))
    m.box(sap, -3.5, -13, -3, 7, 6, 6, leaves(92, ragged=1))
    m.box("arm_l", -3, 0, -3, 6, 17, 6, ivy_bark(93))
    m.box("forearm_l", -2.5, 0, -2.5, 5, 17, 5, ivy_bark(94))
    m.box("forearm_l", 2.5, 4, -2, 2, 1, 3, fungus, glow=fungus_glow)
    m.box("forearm_l", -2.5, 6, -2.8, 5, 9, 0, moss_strands(97, density=0.6))
    m.box("hand_l", -3, 0, -3, 6, 3, 6, bark(95, moss=0, top_moss=0))
    for i, (x, z, rx, rz) in enumerate(((-2, -2, -14, 16), (0, -2.5, -18, 0), (2, -2, -14, -16))):
        f = m.part(f"claw_l{i}", "hand_l", pivot=(x, 2.5, z), rot=(rx, 0, rz))
        m.box(f, -0.5, 0, -0.5, 1, 12, 1, claw(96 + i))
        t = m.part(f"tip_l{i}", f, pivot=(0, 11.5, 0), rot=(-30, 0, 0))
        m.box(t, -0.5, 0, -0.5, 1, 9, 1, claw(99 + i))

    # ------------------------------------------------------------------ legs that split into roots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin, foot = f"leg_{side}", f"shin_{side}", f"foot_{side}"
        m.box(leg, -4.5, 0, -4.5, 9, 16, 9, bark(110 + sx, moss=0))
        m.box(shin, -4, 0, -4, 8, 13, 8, bark(112 + sx, moss=0, twist=0.3))
        for i, (yaw, ln, t) in enumerate(((-24, 10, 3), (18, 9, 3), (78, 8, 3), (165, 8, 2), (-100, 7, 2))):
            yaw = yaw * -sx
            r = m.part(f"root_{side}{i}", foot, pivot=(0, -1, 0), rot=(12, yaw, 0))
            m.box(r, -t / 2, 0, -ln, t, t, ln, claw(120 + i * 2 + (sx > 0)))
            tip = m.part(f"rtip_{side}{i}", r, pivot=(0, t / 2, -ln + 1), rot=(14, 0, 0))
            m.box(tip, -0.5, -0.5, -5, 1, 1, 5, claw(130 + i))

    _animate(m, pods)
    return m


def _animate(m, pods):
    Z = (0, 0, 0)
    ONE = (1, 1, 1)

    idle = m.anim("idle", 4.0)
    idle.rot("torso", (0, Z), (2, (3, 0, 0)), (4, Z))
    idle.rot("head", (0, Z), (1.2, (-3, 4, 0)), (2.6, (2, -3, 0)), (4, Z))
    idle.rot("crown", (0, Z), (2, (0, 0, 3)), (4, Z))
    idle.rot("shawl", (0, Z), (2, (6, 0, 1)), (4, Z))
    idle.rot("hair", (0, Z), (1.4, (6, 0, -2)), (2.8, (-2, 0, 2)), (4, Z))
    idle.rot("arm_r", (0, Z), (2, (-3, 0, 2)), (4, Z))
    idle.rot("arm_l", (0, Z), (2, (4, 0, -2)), (4, Z))
    idle.rot("sapling", (0, Z), (2, (0, 0, 6)), (4, Z))
    for i in range(3):
        idle.rot(f"tip_l{i}", (0, Z), (1 + i * 0.4, (-14, 0, 0)), (4, Z))
    beat = [(0, ONE), (0.15, (1.3, 1.3, 1.3)), (0.35, ONE), (0.55, (1.18, 1.18, 1.18)), (0.8, ONE), (2.0, ONE),
            (2.15, (1.3, 1.3, 1.3)), (2.35, ONE), (2.55, (1.18, 1.18, 1.18)), (2.8, ONE), (4.0, ONE)]
    idle.scale("heart", *beat)
    for i, pod in enumerate(pods):
        t0 = 0.4 + (i * 0.37) % 1.8
        idle.rot(pod, (0, Z), (t0, (8, 0, 6 if i % 2 else -6)), (t0 + 1.5, (-6, 0, 0)), (4, Z))

    walk = m.anim("walk", 2.0)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (22 * sign, 0, 0)), (1.0, (-22 * sign, 0, 0)), (2.0, (22 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, Z), (0.5, (28 if sign > 0 else 0, 0, 0)), (1.0, Z),
                 (1.5, (28 if sign < 0 else 0, 0, 0)), (2.0, Z))
    walk.rot("arm_r", (0, (-16, 0, 0)), (1.0, (16, 0, 0)), (2.0, (-16, 0, 0)))
    walk.rot("arm_l", (0, (16, 0, 0)), (1.0, (-16, 0, 0)), (2.0, (16, 0, 0)))
    walk.rot("torso", (0, (0, 0, 3)), (1.0, (0, 0, -3)), (2.0, (0, 0, 3)))
    walk.rot("crown", (0, (0, 0, -3)), (1.0, (0, 0, 3)), (2.0, (0, 0, -3)))
    walk.pos("bone", (0, Z), (0.5, (0, -2, 0)), (1.0, Z), (1.5, (0, -2, 0)), (2.0, Z))

    # sweep: the great right arm drawn back and out (0.8 s), a flat sweep across (strike 0.8 s), recover
    a = m.anim("sweep", 1.6)
    a.rot("torso", (0, Z), (0.8, (4, 40, 0)), (0.95, (10, -50, 0), "linear"), (1.15, (10, -48, 0)), (1.6, Z))
    a.rot("arm_r", (0, Z), (0.8, (-40, 50, 70)), (0.95, (-80, -30, 30), "linear"), (1.15, (-78, -30, 30)), (1.6, Z))
    a.rot("forearm_r", (0, Z), (0.8, (-10, 0, 0)), (0.95, Z), (1.6, Z))
    a.rot("head", (0, Z), (0.8, (0, -20, 0)), (0.95, (0, 15, 0)), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.8, (-20, 0, -30)), (0.95, (10, 0, -10)), (1.6, Z))

    # grab: arms spread wide (wind-up), lunge and clutch (0.8 s), lift high, slam down (1.65 s), recover
    a = m.anim("grab", 2.4)
    a.rot("torso", (0, Z), (0.7, (-14, 0, 0)), (0.8, (24, 0, 0), "linear"), (1.45, (-20, 0, 0)),
          (1.65, (34, 0, 0), "linear"), (1.9, (30, 0, 0)), (2.4, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (0.7, (-60, 0, 60 * s)), (0.8, (-80, 0, -6 * s), "linear"), (1.45, (-175, 0, -4 * s)),
              (1.65, (-50, 0, 0), "linear"), (1.9, (-45, 0, 0)), (2.4, Z))
    a.rot("forearm_r", (0, Z), (0.8, (-20, 0, 0)), (1.45, (-10, 0, 0)), (1.65, Z), (2.4, Z))
    a.rot("head", (0, Z), (0.7, (-14, 0, 0)), (0.8, (8, 0, 0)), (1.45, (-26, 0, 0)), (1.65, (10, 0, 0)), (2.4, Z))
    a.pos("bone", (0, Z), (0.7, (0, 0, 2)), (0.8, (0, 0, -6), "linear"), (1.45, (0, 0, -6)),
          (1.65, (0, -3, -8), "linear"), (1.9, (0, -3, -8)), (2.4, Z))

    # erupt: both claws raised high (0.9 s), driven into the ground, roots erupt beneath the players
    a = m.anim("erupt", 2.0)
    a.rot("torso", (0, Z), (0.9, (-22, 0, 0)), (1.05, (40, 0, 0), "linear"), (1.5, (38, 0, 0)), (2.0, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (0.9, (-165, 0, 10 * s)), (1.05, (-38, 0, 4 * s), "linear"), (1.5, (-36, 0, 4 * s)),
              (2.0, Z))
    a.rot("head", (0, Z), (0.9, (-25, 0, 0)), (1.05, (10, 0, 0)), (2.0, Z))
    a.rot("crown", (0, Z), (0.9, (-8, 0, 0)), (1.05, (6, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.9, (0, 3, 0)), (1.05, (0, -5, 0), "linear"), (1.5, (0, -5, 0)), (2.0, Z))

    # volley: the crown flares and the body rears back (0.7 s), then the left arm whips thorns forward
    a = m.anim("volley", 1.6)
    a.rot("torso", (0, Z), (0.7, (-24, -20, 0)), (0.85, (16, 14, 0), "linear"), (1.1, (14, 12, 0)), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.7, (-150, 0, -40)), (0.85, (-60, 0, 10), "linear"), (1.1, (-58, 0, 10)), (1.6, Z))
    a.rot("forearm_l", (0, Z), (0.7, (-40, 0, 0)), (0.85, Z), (1.6, Z))
    a.scale("crown", (0, ONE), (0.7, (1.18, 1.18, 1.18)), (0.85, (0.95, 0.95, 0.95), "linear"), (1.6, ONE))
    a.rot("head", (0, Z), (0.7, (-30, 0, 0)), (0.85, (8, 0, 0)), (1.6, Z))
    a.rot("arm_r", (0, Z), (0.7, (10, 0, 30)), (1.6, Z))

    # timber: rears up creaking (1.0 s), falls forward like a felled tree (1.25 s), lies there, pushes up
    a = m.anim("timber", 3.0)
    a.rot("bone", (0, Z), (1.0, (-12, 0, 0)), (1.25, (80, 0, 0), "linear"), (1.32, (76, 0, 0)), (2.1, (78, 0, 0)),
          (2.6, (40, 0, 0)), (3.0, Z))
    a.pos("bone", (0, Z), (1.0, (0, 0, 3)), (1.25, (0, 4, -6), "linear"), (2.1, (0, 4, -6)), (3.0, Z))
    a.rot("torso", (0, Z), (1.0, (-14, 0, 0)), (1.25, (-8, 0, 0)), (2.1, (-8, 0, 0)), (3.0, Z))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, Z), (1.0, (10, 0, 4 * s)), (1.25, (-14, 0, 8 * s), "linear"), (2.1, (-14, 0, 8 * s)), (3.0, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (1.0, (-170, 0, 18 * s)), (1.25, (-150, 0, 40 * s), "linear"), (2.1, (-150, 0, 38 * s)),
              (2.6, (-80, 0, 20 * s)), (3.0, Z))
    a.rot("head", (0, Z), (1.0, (-24, 0, 0)), (1.25, (-40, 0, 0)), (2.1, (-40, 0, 0)), (3.0, Z))

    # spores: arms spread, head thrown back, the crown shakes out clouds of spores
    a = m.anim("spores", 2.2)
    a.rot("torso", (0, Z), (0.8, (-20, 0, 0)), (1.6, (-18, 0, 0)), (2.2, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (0.8, (-40, 0, 80 * s)), (1.6, (-44, 0, 78 * s)), (2.2, Z))
    a.rot("head", (0, Z), (0.8, (-30, 0, 0)), (1.6, (-30, 0, 0)), (2.2, Z))
    a.rot("crown", (0, Z), (0.8, Z), (0.9, (0, 0, 10)), (1.0, (0, 0, -10)), (1.1, (0, 0, 10)),
          (1.2, (0, 0, -10)), (1.3, (0, 0, 10)), (1.4, (0, 0, -8)), (1.6, Z), (2.2, Z))
    a.scale("heart", (0, ONE), (0.8, (1.7, 1.7, 1.7)), (1.6, (1.6, 1.6, 1.6)), (2.2, ONE))

    # sprout: kneels and presses both claws to the soil (0.8 s): saplings rise
    a = m.anim("sprout", 2.0)
    a.pos("bone", (0, Z), (0.8, (0, -8, 0)), (1.2, (0, -8, 0)), (2.0, Z))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, Z), (0.8, (-50 if s > 0 else 10, 0, 0)), (1.2, (-50 if s > 0 else 10, 0, 0)), (2.0, Z))
    for shin, s in (("shin_r", 1), ("shin_l", -1)):
        a.rot(shin, (0, Z), (0.8, (60 if s > 0 else 30, 0, 0)), (1.2, (60 if s > 0 else 30, 0, 0)), (2.0, Z))
    a.rot("torso", (0, Z), (0.8, (30, 0, 0)), (1.2, (30, 0, 0)), (2.0, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (0.8, (-20, 0, 20 * s)), (1.2, (-20, 0, 20 * s)), (2.0, Z))

    # rootwave: both arms raised overhead for a long wind-up (1.1 s), smashed down: rings of roots
    a = m.anim("rootwave", 2.4)
    a.rot("torso", (0, Z), (1.1, (-26, 0, 0)), (1.25, (44, 0, 0), "linear"), (1.7, (42, 0, 0)), (2.4, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (1.1, (-180, 0, -14 * s)), (1.25, (-30, 0, 10 * s), "linear"), (1.7, (-30, 0, 10 * s)),
              (2.4, Z))
    a.scale("crown", (0, ONE), (1.1, (1.2, 1.2, 1.2)), (1.25, ONE), (2.4, ONE))
    a.scale("heart", (0, ONE), (1.1, (1.6, 1.6, 1.6)), (1.25, ONE), (2.4, ONE))
    a.pos("bone", (0, Z), (1.1, (0, 4, 0)), (1.25, (0, -6, 0), "linear"), (1.7, (0, -6, 0)), (2.4, Z))

    # roar: phase change, arms flung wide, the mask raised to the sky, the heart flares
    a = m.anim("roar", 2.6)
    a.rot("torso", (0, Z), (0.5, (-26, 0, 0)), (2.0, (-26, 0, 0)), (2.6, Z))
    a.rot("head", (0, Z), (0.5, (-40, 0, 0)), (2.0, (-40, 0, 0)), (2.6, Z))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, Z), (0.5, (-60, 0, 70 * s)), (2.0, (-64, 0, 74 * s)), (2.6, Z))
    a.scale("heart", (0, ONE), (0.5, (1.8, 1.8, 1.8)), (2.0, (1.8, 1.8, 1.8)), (2.6, ONE))
    a.scale("crown", (0, ONE), (0.5, (1.15, 1.15, 1.15)), (2.0, (1.15, 1.15, 1.15)), (2.6, ONE))

    # stagger: posture broken, slumps onto one knee, a claw on the ground
    a = m.anim("stagger", 2.2)
    a.pos("bone", (0, Z), (0.3, (0, -8, 2)), (1.8, (0, -8, 2)), (2.2, Z))
    a.rot("leg_r", (0, Z), (0.3, (-55, 0, 0)), (1.8, (-55, 0, 0)), (2.2, Z))
    a.rot("shin_r", (0, Z), (0.3, (65, 0, 0)), (1.8, (65, 0, 0)), (2.2, Z))
    a.rot("leg_l", (0, Z), (0.3, (20, 0, 0)), (1.8, (20, 0, 0)), (2.2, Z))
    a.rot("shin_l", (0, Z), (0.3, (55, 0, 0)), (1.8, (55, 0, 0)), (2.2, Z))
    a.rot("torso", (0, Z), (0.3, (24, 0, -8)), (1.8, (24, 0, -8)), (2.2, Z))
    a.rot("head", (0, Z), (0.3, (20, 0, 10)), (1.8, (20, 0, 10)), (2.2, Z))
    a.rot("arm_r", (0, Z), (0.3, (-30, 0, 10)), (1.8, (-30, 0, 10)), (2.2, Z))
    a.rot("crown", (0, Z), (0.3, (10, 0, 6)), (1.8, (10, 0, 6)), (2.2, Z))
