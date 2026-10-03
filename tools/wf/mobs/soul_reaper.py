"""The Soul Reaper (La Faucheuse des âmes): a hovering 4.5-block reaper, boss of the Soul Tower.

Silhouette: a deep pointed hood over a skull with soul-fire eyes, a heavy ragged mantle bristling with
bone spikes, layered robes that end in tatters over a glowing soul core instead of legs, skeletal arms
wrapped in chains with soul lanterns swinging from them, and a gigantic scythe whose crescent blade
arcs high over the hood, its inner edge burning pale cyan.
"""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
CLOTH = (50, 47, 58)        # outer robe: ash black with a violet cast
CLOTH_D = (28, 26, 34)
CLOTH_L = (84, 79, 92)
INNER = (30, 42, 48)        # inner robe: drowned teal black
INNER_D = (17, 24, 29)
HEM = (104, 98, 108)        # worn, dusty hem
THREAD = (128, 158, 156)    # pale teal embroidery (not glowing)
BONE = (218, 210, 188)
BONE_D = (164, 152, 128)
BONE_DD = (104, 94, 80)
IRON = (66, 70, 78)
IRON_D = (34, 36, 42)
IRON_L = (112, 118, 128)
RUST = (104, 74, 54)
SOUL = (96, 232, 242)
SOUL_L = (196, 255, 255)
SOUL_D = (36, 140, 160)
VOID = (8, 10, 14)


def _h(*v):
    """Deterministic hash of integers -> 0..65535."""
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def cloth(base=CLOTH, dark=CLOTH_D, light=CLOTH_L, seed=0, tatter=0, hem=True, holes=True, grad=0.3,
          lining=None, inner="back"):
    """Hanging cloth: irregular soft folds (two beating waves), darker toward the bottom, a dusty hem band,
    dust specks, and a ragged bottom cut into strips of varied length (``tatter`` texels deep)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 0.75)
        if lining is not None and face == inner:
            b = lining
        else:
            b = base
        if tatter:
            sw = 2 + _h(seed, x // 3) % 3
            strip = (x + seed) // sw
            r = _h(strip, seed, 7)
            cut = r % (tatter + 1)
            if r % 5 == 0:
                cut = tatter  # a few deep rents
            if y >= h - cut:
                return None
            if holes and y >= h - tatter - 4 and _h(x, y, seed, 3) % 31 == 0:
                return None
        s = 0.6 * math.sin(x * 0.95 + seed * 1.7) + 0.4 * math.sin(x * 0.41 + seed * 0.6 + y * 0.03)
        col = mul(b, 1.0 + 0.2 * s)
        if (x * 7 + seed) % 11 == 0:
            col = mix(col, (b[0] - 4, b[1] + 4, b[2] + 8), 0.5)   # a cold cast in some threads
        if s < -0.72:
            col = mix(col, dark, 0.6)        # deep crease
        elif s > 0.8:
            col = mix(col, light, 0.3)       # lit ridge
        t = y / max(1, h - 1)
        col = mul(col, 1.1 - grad * t)
        if hem and tatter and h - tatter - 3 <= y <= h - tatter - 2:
            col = mix(col, HEM, 0.4)
        r2 = _h(x, y, seed, FACE_N[face])
        if r2 % 41 == 0:
            col = mix(col, light, 0.4)       # dust
        elif r2 % 53 == 0:
            col = mix(col, dark, 0.6)        # small tear shadow
        return col
    return f


def embroidered(base=CLOTH, seed=0, tatter=6, band_from_bottom=10, lining=INNER_D, motif=True, outer="front"):
    """Outer robe: cloth with a pale teal embroidered band (a running zig-zag of souls) above the hem."""
    inner = "back" if outer == "front" else "front"
    under = cloth(base, CLOTH_D, CLOTH_L, seed=seed, tatter=tatter, lining=lining, inner=inner)

    def f(face, x, y, w, h):
        c = under(face, x, y, w, h)
        if c is None or face in ("top", "bottom", inner):
            return c
        band = h - band_from_bottom
        if y in (band - 1, band + 3):
            return mix(c, THREAD, 0.45)
        if motif and band <= y <= band + 2:
            k = (x + seed) % 6
            if (y - band) == (0 if k < 2 else 1 if k in (2, 5) else 2):
                return THREAD
        return c
    return f


def bone(seed=0, ridges=0, base=BONE, dark=BONE_D):
    """Old bone: ivory, darker grooves along the length, cracks, light ends."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mix(base, (240, 234, 216), 0.3)
        col = base
        if (x == 0 or x == w - 1) and w > 2:
            col = mix(col, dark, 0.45)
        if ridges and y % ridges == 0:
            col = mix(col, dark, 0.6)
        r = _h(x, y, seed, FACE_N[face])
        if r % 23 == 0:
            col = mix(col, BONE_DD, 0.7)
        elif r % 7 == 0:
            col = mul(col, 0.94)
        t = y / max(1, h - 1)
        return mul(col, 1.04 - 0.14 * t)
    return f


def spike_paint(seed=0, tip=False):
    """Bone spike: ridged, yellowed at the root, darkening and sharpening to the tip (top)."""
    def f(face, x, y, w, h):
        if face == "top":
            return BONE_DD if tip else BONE_D
        if face == "bottom":
            return BONE_D
        t = y / max(1, h - 1)  # 0 at the top
        col = mix(BONE_DD, BONE, 0.25 + 0.75 * t) if tip else mix(BONE_D, BONE, 0.4 + 0.6 * t)
        if not tip and y % 3 == 2:
            col = mix(col, BONE_D, 0.55)
        if x == 0 and w > 1:
            col = mul(col, 0.86)
        if _h(x, y, seed) % 19 == 0:
            col = mix(col, BONE_DD, 0.5)
        return col
    return f


def iron(seed=0, rim=True, base=IRON, rust=True):
    def f(face, x, y, w, h):
        col = base
        if rim and (x == 0 or y == 0 or x == w - 1 or y == h - 1) and w > 2 and h > 2:
            col = IRON_D
        elif y == 1 and h > 3:
            col = mix(col, IRON_L, 0.4)
        r = _h(x, y, seed, FACE_N[face])
        if rust and r % 17 == 0:
            col = mix(col, RUST, 0.6)
        elif r % 5 == 0:
            col = mul(col, 0.9)
        return col
    return f


def chain_wrap(seed=0, every=3):
    """Chains coiled round a bone: diagonal link rows every ``every`` texels, transparent between."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        row = (y + x // 2 + seed) % every
        if row == 0:
            link = (x + y) % 3
            return IRON_L if link == 0 else IRON if link == 1 else IRON_D
        if row == 1 and (x + seed) % 3 == 1:
            return IRON_D
        return None
    return f


def chain_strand(seed=0):
    """A hanging chain drawn on a thin plane: alternating open and edge-on links."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return IRON
        k = (y + seed) % 4
        if w <= 2:
            if k in (0, 3):
                return IRON_L if k == 0 else IRON
            return IRON_D if x == 0 and k == 1 else None
        mid = w // 2
        if k in (0, 3):
            return (IRON_L if k == 0 else IRON) if x in (mid - 1, mid) else None
        return IRON_D if x == mid else None
    return f


def soul_core(seed=0):
    """The soul fire the reaper floats on: bright at the bottom, licking up between the tatters."""
    def f(face, x, y, w, h):
        t = y / max(1, h - 1)
        lick = (_h(x, seed) % 5) * 0.07
        if t < 0.3 - lick:
            return mix(SOUL_D, VOID, 0.6)
        return mix(SOUL_D, SOUL_L, min(1.0, t * 1.1))
    return f


def soul_glow(seed=0, floor=0.3):
    def f(face, x, y, w, h):
        t = y / max(1, h - 1)
        lick = (_h(x, seed) % 5) * 0.07
        if t < floor - lick:
            return None
        return mix(SOUL, SOUL_L, t)
    return f


# ------------------------------------------------------------------ face pieces
def skull_face(face, x, y, w, h):
    """8x9 skull front: brow ridge, deep sockets with soul pupils, nasal hole, cheekbones, upper teeth."""
    sock_l = x in (1, 2) and y in (3, 4)
    sock_r = x in (5, 6) and y in (3, 4)
    if sock_l or sock_r:
        return SOUL_L if (x in (2, 5) and y == 3) else SOUL if y == 3 else VOID
    if y == 2 and x in (1, 2, 5, 6):
        return BONE_D  # brow shadow
    if y in (5, 6) and x in (3, 4):
        return VOID if y == 6 or x == 3 else BONE_DD  # nose
    if y == 8:
        return VOID if x % 2 else (236, 228, 206)  # teeth
    if y == 7:
        return BONE_D if x in (0, 7) else BONE
    if y == 0:
        return (232, 226, 206)
    if x in (0, 7) and y > 4:
        return BONE_D
    if (x, y) in ((3, 1), (3, 2), (4, 0)):
        return BONE_DD  # a crack running from the crown
    return BONE


def skull_glow(face, x, y, w, h):
    if x in (1, 2, 5, 6) and y in (3, 4):
        return SOUL_L if (x in (2, 5) and y == 3) else SOUL if y == 3 else None
    return None


def chest_front(face, x, y, w, h):
    """Open robe over a ribcage, soul fire smouldering between the ribs."""
    if x < 3 or x >= w - 3:
        return cloth(seed=11)(face, x, y, w, h)
    if x in (3, w - 4):
        return CLOTH_D
    mid = w // 2
    if y < 3:
        return mul(BONE, 0.92) if y == 2 else CLOTH_D   # clavicles under the collar
    if x in (mid - 1, mid):
        return BONE if y % 3 else BONE_D                 # sternum / spine
    if y > 15:
        return INNER_D
    if y % 3 == 2:
        return BONE if abs(x - mid) < 5 - (y > 11) else BONE_D   # ribs, shortening downward
    return VOID


def chest_glow(face, x, y, w, h):
    """Only the cores of the gaps between the ribs smoulder, brightest low in the chest."""
    mid = w // 2
    if face != "front" or not (4 <= y <= 14) or y % 3 != 0 or abs(x - mid + 0.5) > 3.6 - (y < 8):
        return None
    if x in (mid - 1, mid):
        return None
    return SOUL if y >= 9 and (x + y) % 3 else SOUL_D


def hood_trim(face, x, y, w, h):
    """Front edge of the cowl: a pale teal embroidered border."""
    if (y + x) % 3 == 0:
        return mix(THREAD, CLOTH_L, 0.3)
    return THREAD if x == w // 2 else mix(CLOTH, THREAD, 0.35)


def hood_inner(face, x, y, w, h):
    """Inside of the cowl: black void with a faint teal rim."""
    return mix(VOID, INNER, 0.35) if (y == 0 or x == 0) else VOID


def blade_paint(seg, n):
    """Scythe blade: blackened steel with a fuller line, pale cyan sharpened inner (bottom) edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return (150, 220, 226)
        if face == "top":
            return IRON_D
        edge = h - y  # 1 = last row
        if edge == 1:
            return (176, 236, 240)
        if edge == 2:
            return (120, 178, 186)
        if y == 0:
            return IRON_L  # spine highlight
        if y == h // 2 - 1 and 1 <= x < w - 1 and face in ("front", "back"):
            return IRON_D  # fuller groove
        col = mix(IRON_D, IRON, 0.6)
        if face in ("front", "back") and _h(x, seg) % 9 == 0 and 1 <= y < h - 3:
            col = mix(col, SOUL_D, 0.6)  # rune scratch
        return col
    return f


def blade_glow(seg, n):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SOUL_L
        if face in ("front", "back"):
            if h - y == 1:
                return SOUL_L
            if h - y == 2 and (x + seg) % 3 == 0:
                return SOUL
            if _h(x, seg) % 9 == 0 and 1 <= y < h - 3:
                return SOUL_D
        return None
    return f


def lantern_body(face, x, y, w, h):
    if face in ("top", "bottom"):
        return IRON_D
    if x in (0, w - 1) or y in (0, h - 1):
        return IRON_D
    if x == w // 2:
        return IRON  # middle bar
    return mix(SOUL, SOUL_L, y / max(1, h - 1))


def lantern_glow(face, x, y, w, h):
    if face in ("top", "bottom") or x in (0, w - 1) or y in (0, h - 1) or x == w // 2:
        return None
    return mix(SOUL, SOUL_L, y / max(1, h - 1))


# ------------------------------------------------------------------ build
INNER_PANELS = 8
OUTER_ANGLES = (35, 90, 145, 180, -145, -90, -35)   # the outer robe is split at the front


def _dir(theta):
    """Outward horizontal direction (model space) for a yaw angle: 0 = front (-z), 90 = right (-x)."""
    t = math.radians(theta)
    return -math.sin(t), -math.cos(t)


def build():
    m = Model("soul_reaper", seed=37, shadow=1.3, walk_speed=0.6, walk_scale=1.0)

    # ---------------- skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -36, 0))
    m.part("chest", "body", pivot=(0, -1, 0), rot=(12, 0, 0))
    m.part("head", "chest", pivot=(0, -24, -2), rot=(-8, 0, 0))
    m.part("jaw", "head", pivot=(0, -4, -4))
    m.part("hood_t1", "head", pivot=(0, -20, 2), rot=(-58, 0, 0))
    m.part("hood_t2", "hood_t1", pivot=(0, -7, 0), rot=(-35, 0, 6))
    m.part("hood_t3", "hood_t2", pivot=(0, -6, 0), rot=(-30, 0, 8))
    m.part("cape", "chest", pivot=(0, -24, 7), rot=(14, 0, 0))
    m.part("cape_l", "cape", pivot=(9, 0, 0), rot=(0, -22, 0))
    m.part("cape_r", "cape", pivot=(-9, 0, 0), rot=(0, 22, 0))
    m.part("arm_r", "chest", pivot=(-14, -20, 0), rot=(-10, 0, 14))
    m.part("sleeve_r", "arm_r", pivot=(0, 0, 0), rot=(6, 0, 4))
    m.part("forearm_r", "arm_r", pivot=(0, 13, 0), rot=(-62, 0, 0))
    m.part("hand_r", "forearm_r", pivot=(0, 12, 0))
    m.part("scythe", "hand_r", pivot=(0, 3, 0), rot=(72, 0, -18))
    m.part("arm_l", "chest", pivot=(14, -20, 0), rot=(-6, 0, -16))
    m.part("sleeve_l", "arm_l", pivot=(0, 0, 0), rot=(6, 0, -4))
    m.part("forearm_l", "arm_l", pivot=(0, 13, 0), rot=(-50, 0, 0))
    m.part("hand_l", "forearm_l", pivot=(0, 12, 0))
    m.part("chain_l", "hand_l", pivot=(0, 4, 0), rot=(56, 0, 6))
    m.part("lantern_l", "chain_l", pivot=(0, 18, 0))
    m.part("chain_e", "forearm_l", pivot=(1, 3, 2), rot=(46, 0, -4))
    m.part("chain_r", "forearm_r", pivot=(-1, 6, 2), rot=(62, 0, 0))

    # ---------------- lower body: a soul fire under a bell of layered, torn robes
    m.box("body", -7, -2, -5, 14, 10, 10, cloth(INNER, INNER_D, CLOTH, seed=1, grad=0.1))
    m.box("body", -6, 8, -4.5, 12, 12, 9, cloth(INNER_D, VOID, INNER, seed=2, grad=0.1))
    m.box("body", -5, 20, -4, 10, 9, 8, soul_core(3), glow=soul_glow(3))
    for i in range(INNER_PANELS):          # inner robe: eight long teal-black panels, longer at the back
        th = 360 / INNER_PANELS * i
        dx, dz = _dir(th)
        back = (1 - math.cos(math.radians(th))) / 2
        name = f"robe{i}"
        m.part(name, "body", pivot=(dx * 6.0, 2, dz * 6.0), rot=(-13 - 9 * back, th, 0))
        ln = int(31 + 7 * back)
        paint = cloth(INNER, INNER_D, (62, 80, 84), seed=4 + i, tatter=10, lining=INNER_D)
        if i == 0:   # the front panel shown through the split carries an embroidered stole
            base = paint

            def paint(face, x, y, w, h, base=base):
                c = base(face, x, y, w, h)
                if c is not None and face == "front" and x in (3, 5) and y < h - 12:
                    return THREAD if y % 4 else mix(THREAD, SOUL_D, 0.5)
                return c
        m.box(name, -4.5, 0, -1, 9, ln, 2, paint)
    for i, th in enumerate(OUTER_ANGLES):   # outer robe: ash-black, embroidered, split at the front
        dx, dz = _dir(th)
        back = (1 - math.cos(math.radians(th))) / 2
        name = f"cloak{i}"
        m.part(name, "body", pivot=(dx * 7.5, 0, dz * 7.5), rot=(-17 - 10 * back, th, 0))
        m.box(name, -5.5, 0, -1, 11, int(22 + 9 * back), 1, embroidered(seed=20 + i, tatter=7))
    # belt of vertebrae and chain with a skull buckle
    m.box("body", -8, -2, -6, 16, 3, 12, {
        "side": lambda f_, x, y, w, h: (BONE if x % 3 else BONE_DD) if y == 1 else IRON_D if x % 2 else IRON,
        "*": IRON_D})
    m.box("body", -2, -3, -8, 4, 4, 2, {"front": lambda f_, x, y, w, h:
                                        VOID if (y == 1 and x in (0, 3)) or (y == 3 and x == 1) else BONE,
                                        "*": BONE_D},
          glow={"front": lambda f_, x, y, w, h: SOUL if (y == 1 and x in (0, 3)) else None})

    # ---------------- chest: open robe over a smouldering ribcage, tiered mantle, bone spikes
    m.box("chest", -8, -21, -5, 16, 21, 10, {"front": chest_front, "*": cloth(seed=11)},
          glow={"front": chest_glow})
    m.box("chest", -9, -21, -6, 3, 21, 1, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=15))   # lapels
    m.box("chest", 6, -21, -6, 3, 21, 1, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=16))
    # mantle: a wide torn lower tier open at the front, the shoulder tier, the cowl collar
    m.box("chest", -16, -21, -8, 12, 10, 16, {"top": cloth(seed=17), "*": cloth(seed=17, tatter=5, holes=False)})
    m.box("chest", 4, -21, -8, 12, 10, 16, {"top": cloth(seed=18), "*": cloth(seed=18, tatter=5, holes=False)})
    m.box("chest", -14, -25, -7, 28, 6, 14, {"*": cloth(CLOTH_L, CLOTH, HEM, seed=19, grad=0.15, tatter=2,
                                                        holes=False)})
    m.box("chest", -9, -28, -6, 18, 4, 12, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=20, grad=0.0))
    # long torn cape falling from the shoulders, in three hinged widths so it wraps the back
    m.box("cape", -9, 0, 0, 18, 46, 1, embroidered(CLOTH, seed=74, outer="back", tatter=12, band_from_bottom=17,
                                                   lining=INNER_D))
    m.box("cape_l", 0, 0, 0, 8, 40, 1, embroidered(CLOTH, seed=75, outer="back", tatter=11, band_from_bottom=16,
                                                   lining=INNER_D))
    m.box("cape_r", -8, 0, 0, 8, 40, 1, embroidered(CLOTH, seed=76, outer="back", tatter=11, band_from_bottom=16,
                                                    lining=INNER_D))
    m.box("chest", -18, -27, -6, 7, 3, 12, bone(21, ridges=3))     # scapula plates under the spikes
    m.box("chest", 11, -27, -6, 7, 3, 12, bone(22, ridges=3))

    # bone spikes: base and curved tip parts; three great ones on the right, two on the left
    spikes = (("r1", (-15, -27, -1), (8, 0, 30), 11, (0, 0, -22)), ("r2", (-12, -27, 4), (-28, 0, 16), 9, (-18, 0, -8)),
              ("r3", (-17, -26, -4), (22, 0, 58), 7, (0, 0, -24)),
              ("l1", (14, -27, 2), (-16, 0, -26), 10, (-10, 0, 20)), ("l2", (16, -26, -3), (16, 0, -52), 6, (0, 0, 22)))
    for i, (key, piv, rot, ln, curl) in enumerate(spikes):
        base, tip = f"spk_{key}", f"spk_{key}t"
        m.part(base, "chest", pivot=piv, rot=rot)
        m.part(tip, base, pivot=(0, -ln, 0), rot=curl)
        m.box(base, -2, -ln, -2, 4, ln, 4, spike_paint(30 + i))
        m.box(tip, -1.5, -int(ln * 0.8), -1.5, 3, int(ln * 0.8), 3, spike_paint(40 + i, tip=True))
        m.box(tip, -0.5, -int(ln * 0.8) - 4, -0.5, 1, 4, 1, spike_paint(50 + i, tip=True))

    # ---------------- head: a deep cowl, its opening a pointed arch, a skull set far back inside
    m.box("head", -8, -17, -9, 16, 2, 16, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=60, grad=0.0))       # crown
    m.box("head", -8, -15, -9, 2, 17, 16, {"left": hood_inner, "front": hood_trim, "*": cloth(seed=61, tatter=3, holes=False)})
    m.box("head", 6, -15, -9, 2, 17, 16, {"right": hood_inner, "front": hood_trim, "*": cloth(seed=62, tatter=3, holes=False)})
    m.box("head", -6, -15, 5, 12, 17, 2, cloth(seed=63))
    m.box("head", -6, -15, -4, 12, 16, 9, {"front": hood_inner, "*": VOID})                        # the dark inside
    m.box("head", -7, -18, -11, 14, 3, 3, {"front": hood_trim, "*": cloth(CLOTH_L, CLOTH, HEM, seed=64, grad=0.0)})             # overhanging brim
    for (x, y, w, hh) in ((-6, -15, 4, 2), (2, -15, 4, 2), (-6, -13, 2, 2), (4, -13, 2, 2)):        # pointed arch
        m.box("head", x, y, -10, w, hh, 2, {"front": cloth(CLOTH_D, VOID, CLOTH, seed=65), "*": CLOTH_D})
    m.box("head", -4, -12, -7, 8, 9, 6, {"front": skull_face, "top": BONE, "*": bone(66)},
          glow={"front": skull_glow})
    m.box("jaw", -3, 0, -3, 6, 3, 5, {"front": lambda f_, x, y, w, h: (236, 228, 206) if y == 0 and x % 2 == 0
                                      else VOID if y == 0 else BONE_D if y == 2 else BONE, "*": bone(67)})
    m.box("head", -6, -20, -6, 12, 3, 12, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=71, grad=0.0))       # peaked crown
    m.box("head", -4, -22, -3, 8, 2, 8, cloth(CLOTH, CLOTH_D, CLOTH_L, seed=72, grad=0.0))
    m.box("head", -7, -2, 5, 14, 6, 3, cloth(seed=73, tatter=3, holes=False))                     # cowl drape
    m.box("hood_t1", -5, -7, -4, 10, 7, 8, cloth(seed=68, grad=0.0))
    m.box("hood_t2", -3, -6, -3, 6, 6, 6, cloth(seed=69, grad=0.0))
    m.box("hood_t3", -1.5, -6, -1.5, 3, 6, 3, cloth(CLOTH_D, VOID, CLOTH, seed=70, grad=0.0))

    # ---------------- arms: bell sleeves over chained skeletal arms with clawed hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, sleeve, fore, hand = f"arm_{side}", f"sleeve_{side}", f"forearm_{side}", f"hand_{side}"
        m.box(arm, -1.5, 0, -1.5, 3, 13, 3, bone(80 + sx))
        m.box(sleeve, -5, -3, -5, 10, 9, 10, {"top": cloth(seed=81 + sx), "*": cloth(seed=82 + sx)})
        m.box(sleeve, -6, 6, -6, 12, 11, 12, {"top": None, "bottom": None,
                                              "*": cloth(CLOTH, CLOTH_D, CLOTH_L, seed=83 + sx, tatter=7)})
        m.box(fore, -2, 0, -1, 2, 12, 2, bone(84 + sx))
        m.box(fore, 0, 0, -1, 2, 12, 2, bone(85 + sx))
        m.box(fore, -2.5, 1, -1.5, 5, 9, 3, chain_wrap(86 + sx), grow=0.25)
        m.box(fore, -2, 10, -1.5, 4, 2, 3, bone(87 + sx))
        m.box(hand, -2, 0, -2, 4, 3, 4, bone(88 + sx))
        for k in range(4):
            m.box(hand, -2 + k, 3, -2, 1, 5, 1, {"*": lambda f_, x, y, w, h, k=k: BONE_DD if y >= 3 else
                                                 (BONE if k % 2 else BONE_D)})
        m.box(hand, 2 if sx > 0 else -3, 1, 0, 1, 3, 1, bone(89 + sx))

    # ---------------- chains and soul lanterns
    m.box("chain_l", -1, 0, 0, 2, 18, 0, chain_strand(1))
    m.box("chain_l", 0, 0, -1, 0, 18, 2, chain_strand(3))
    m.box("lantern_l", -1, -1, -1, 2, 1, 2, IRON_L)
    m.box("lantern_l", -3.5, 0, -3.5, 7, 2, 7, iron(90))
    m.box("lantern_l", -3, 2, -3, 6, 8, 6, lantern_body, glow=lantern_glow)
    m.box("lantern_l", -3.5, 10, -3.5, 7, 1, 7, iron(91, rim=False))
    m.box("lantern_l", -1, 11, -1, 2, 2, 2, iron(92, rim=False))
    for name, ln in (("chain_e", 8), ("chain_r", 6)):
        m.box(name, -1, 0, 0, 2, ln, 0, chain_strand(2))
        m.box(name, 0, 0, -1, 0, ln, 2, chain_strand(4))
        m.box(name, -2, ln, -2, 4, 1, 4, iron(93, rim=False))
        m.box(name, -1.5, ln + 1, -1.5, 3, 4, 3, lantern_body, glow=lantern_glow)
        m.box(name, -2, ln + 5, -2, 4, 1, 4, iron(94, rim=False))

    # ---------------- the scythe: bone-ringed iron snath, skull collar, a crescent blade in segments
    def snath(face, x, y, w, h):
        if face in ("top", "bottom"):
            return IRON_D
        if y % 14 in (0, 1):
            return BONE if y % 14 == 0 else BONE_D
        if 46 <= y <= 60:
            return (92, 70, 58) if (x + y) % 2 else (64, 46, 38)   # leather grip
        col = mix(IRON_D, IRON, 0.5)
        return mix(col, IRON_L, 0.3) if x == 1 else col
    m.box("scythe", -1.5, -62, -1.5, 3, 86, 3, snath)
    m.box("scythe", -1, 24, -1, 2, 4, 2, iron(95, rim=False))
    m.box("scythe", -0.5, 28, -0.5, 1, 3, 1, IRON_L)
    m.box("scythe", -2.5, -69, -2.5, 5, 8, 5, iron(96))                                   # collar
    m.box("scythe", -2, -68, -5, 4, 4, 2, {"front": lambda f_, x, y, w, h: VOID if y == 1 and x in (0, 3)
                                           else BONE, "*": BONE_D},
          glow={"front": lambda f_, x, y, w, h: SOUL if y == 1 and x in (0, 3) else None})
    m.box("scythe", -5.5, -67, -1, 3, 3, 2, iron(97, rim=False))                         # back spur
    m.box("scythe", -8, -66, -0.5, 3, 2, 1, IRON_L)
    m.box("scythe", -1, -71, -1, 2, 2, 2, IRON_L)
    m.part("ribbon", "scythe", pivot=(-2.5, -63, 0), rot=(0, 0, 8))
    m.box("ribbon", -3, 0, 0, 3, 18, 0, cloth(INNER, INNER_D, THREAD, seed=98, tatter=5, hem=False))
    m.part("blade", "scythe", pivot=(1.5, -68, 0))
    segs = ((12, 12), (11, 10), (10, 9), (9, 7), (8, 5), (7, 4), (6, 2))
    rots = (0, 9, 13, 16, 19, 22, 26)
    parent = "blade"
    for i, ((ln, ht), r) in enumerate(zip(segs, rots)):
        name = f"blade{i}"
        m.part(name, parent, pivot=(0 if i == 0 else segs[i - 1][0] - 1, 0, 0), rot=(0, 0, r))
        m.box(name, 0, -2, -1, ln, ht, 2, blade_paint(i, len(segs)), glow=blade_glow(i, len(segs)))
        if i < 4:   # vertebra spurs along the spine
            m.box(name, ln // 2 - 1, -4, -0.5, 2, 2, 1, spike_paint(60 + i, tip=True))
        parent = name

    _anims(m)
    return m


def _rest(a, part, kind, keys):
    """Add a channel that always ends at rest at the animation's end."""
    end = (1, 1, 1) if kind == "scale" else (0, 0, 0)
    keys = list(keys)
    if keys[-1][0] < a.length:
        keys.append((a.length, end))
    getattr(a, kind)(part, *keys)


def _panels():
    """(part, yaw) of every robe panel."""
    out = [(f"robe{i}", 360 / INNER_PANELS * i) for i in range(INNER_PANELS)]
    out += [(f"cloak{i}", th) for i, th in enumerate(OUTER_ANGLES)]
    return out


def _skirt(a, keys, trail=0.0):
    """Flare every robe panel: keys = [(t, flare_deg)], flare > 0 opens the bell; ``trail`` > 0 also
    streams the back panels out and tucks the front ones (a glide)."""
    for name, th in _panels():
        c = math.cos(math.radians(th))
        k = 1.25 if name.startswith("cloak") else 1.0
        _rest(a, name, "rot", [(t, (-(f * k) + trail * c * (f / max(1e-6, max(abs(v) for _, v in keys) or 1)), 0, 0))
                               for t, f in keys])


def _anims(m):
    Z = (0, 0, 0)
    L = "linear"
    # idle: a slow hover bob, a wave running round the robe hem, chains swinging, the hood breathing
    a = m.anim("idle", 4.0)
    a.pos("bone", (0, Z), (1.0, (0, 1.5, 0)), (2.0, (0, 2.5, 0)), (3.0, (0, 1.0, 0)), (4.0, Z))
    a.rot("chest", (0, Z), (2.0, (3, 0, 0)), (4.0, Z))
    a.rot("head", (0, Z), (1.3, (-3, 4, 0)), (2.6, (2, -3, 0)), (4.0, Z))
    a.rot("hood_t2", (0, Z), (2.0, (-8, 0, 5)), (4.0, Z))
    a.rot("hood_t3", (0, Z), (2.4, (-10, 0, -6)), (4.0, Z))
    a.rot("jaw", (0, Z), (2.4, (6, 0, 0)), (3.0, Z), (4.0, Z))
    a.rot("ribbon", (0, Z), (1.5, (10, 0, -8)), (3.0, (-6, 0, 6)), (4.0, Z))
    for name, th in _panels():   # a slow wave travelling round the hem
        amp = 5 if name.startswith("cloak") else 4
        ph = math.radians(th)
        a.rot(name, *[(k * 0.5, (amp * math.sin(math.pi * k / 4 + ph), 0, 0)) for k in range(9)])
    a.rot("chain_l", (0, Z), (1.0, (6, 0, 5)), (2.0, Z), (3.0, (-5, 0, -4)), (4.0, Z))
    a.rot("chain_e", (0, Z), (1.5, (-8, 0, 6)), (3.0, (5, 0, -3)), (4.0, Z))
    a.rot("chain_r", (0, Z), (1.2, (6, 0, -6)), (2.8, (-6, 0, 4)), (4.0, Z))
    a.rot("arm_l", (0, Z), (2.0, (-3, 0, -2)), (4.0, Z))
    a.rot("arm_r", (0, Z), (2.0, (2, 0, 1)), (4.0, Z))

    # drift (walk): leaning into the glide, the robe streaming behind
    a = m.anim("walk", 1.6)
    a.rot("body", (0, (10, 0, 0)), (0.8, (13, 0, 0)), (1.6, (10, 0, 0)))
    a.rot("head", (0, (-9, 0, 0)), (0.8, (-12, 0, 0)), (1.6, (-9, 0, 0)))
    a.rot("chain_l", (0, (22, 0, 0)), (0.8, (28, 0, 0)), (1.6, (22, 0, 0)))
    a.rot("ribbon", (0, (30, 0, 0)), (0.8, (40, 0, 0)), (1.6, (30, 0, 0)))
    for name, th in _panels():
        c = math.cos(math.radians(th))
        a.rot(name, (0, (8 * c - 6 * (1 - c), 0, 0)), (0.8, (10 * c - 9 * (1 - c), 0, 0)),
              (1.6, (8 * c - 6 * (1 - c), 0, 0)))

    # sweep: the scythe hauled far back to the right (0.8 s), then a flat crescent across the front
    a = m.anim("sweep", 1.7)
    _rest(a, "chest", "rot", [(0, Z), (0.8, (-4, 45, 0)), (0.95, (6, -50, 0), L), (1.2, (6, -48, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.8, (-80, 85, -14)), (0.95, (-80, -55, -14), L), (1.2, (-78, -52, -14))])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.8, (62, 0, 0)), (1.2, (62, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.6, (108, 0, 18)), (1.2, (108, 0, 18))])
    _rest(a, "arm_l", "rot", [(0, Z), (0.8, (-40, 0, -30)), (0.95, (-10, 0, -10), L)])
    _rest(a, "bone", "pos", [(0, Z), (0.8, (0, 3, 4)), (0.95, (0, 1, -8), L), (1.2, (0, 1, -8))])
    _skirt(a, [(0, 0), (0.8, 4), (0.95, 14), (1.3, 6)])

    # combo: forehand sweep at 0.7 s, the blade spun round the snath, a backhand at 1.2 s
    a = m.anim("combo", 2.1)
    _rest(a, "chest", "rot", [(0, Z), (0.7, (-4, 45, 0)), (0.82, (6, -50, 0), L), (1.05, (2, -60, 0)),
                              (1.2, (6, 45, 0), L), (1.45, (4, 42, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.7, (-80, 85, -14)), (0.82, (-80, -55, -14), L), (1.05, (-80, -75, -14)),
                              (1.2, (-80, 80, -14), L), (1.45, (-78, 76, -14))])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.6, (62, 0, 0)), (1.6, (62, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.5, (108, 0, 18)), (0.85, (108, 0, 18)), (1.05, (108, 180, 18)),
                               (1.6, (108, 180, 18)), (1.85, (60, 90, 10))])
    _rest(a, "bone", "pos", [(0, Z), (0.7, (0, 3, 4)), (0.82, (0, 1, -8), L), (1.2, (0, 2, -13), L),
                             (1.45, (0, 2, -13))])
    _skirt(a, [(0, 0), (0.7, 4), (0.82, 14), (1.05, 6), (1.2, 16), (1.5, 6)])

    # throw: the scythe drawn back over the shoulder (0.9 s) and hurled; caught again at 2.4 s
    a = m.anim("throw", 3.0)
    _rest(a, "chest", "rot", [(0, Z), (0.9, (-14, 50, 0)), (1.0, (14, -30, 0), L), (2.3, (10, -25, 0)),
                              (2.45, (-4, 20, 0), L), (2.6, (-2, 15, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.9, (170, 20, -14)), (1.0, (-80, -15, -14), L), (2.3, (-78, -10, -14)),
                              (2.45, (-50, 40, 10), L)])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.9, (20, 0, 0)), (1.0, (62, 0, 0), L), (2.3, (60, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.9, (108, 0, 18)), (2.4, (108, 0, 18)), (2.6, (40, 0, 10))])
    _rest(a, "scythe", "scale", [(0, (1, 1, 1)), (0.98, (1, 1, 1)), (1.0, (0.01, 0.01, 0.01), L),
                                 (2.38, (0.01, 0.01, 0.01)), (2.4, (1, 1, 1), L)])
    _rest(a, "arm_l", "rot", [(0, Z), (0.9, (-50, 0, -40)), (1.0, (-20, 0, -20), L)])
    _rest(a, "bone", "pos", [(0, Z), (0.9, (0, 3, 4)), (1.0, (0, 0, -5), L), (2.3, (0, 1, -4))])
    _skirt(a, [(0, 0), (0.9, 5), (1.0, 12), (1.6, 4)])

    # wave: the scythe raised two-handed high overhead (1.0 s), the blade driven into the floor
    a = m.anim("wave", 2.05)
    _rest(a, "chest", "rot", [(0, Z), (1.0, (-30, 0, 0)), (1.1, (28, 0, 0), L), (1.6, (25, 0, 0))])
    _rest(a, "head", "rot", [(0, Z), (1.0, (-16, 0, 0)), (1.1, (10, 0, 0), L), (1.6, (8, 0, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (1.0, (170, 0, -24)), (1.1, (-70, 0, -14), L), (1.6, (-66, 0, -14))])
    _rest(a, "arm_l", "rot", [(0, Z), (1.0, (166, 0, 26)), (1.1, (-74, 0, 26), L), (1.6, (-70, 0, 24))])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.8, (62, 0, 0)), (1.6, (62, 0, 0))])
    _rest(a, "forearm_l", "rot", [(0, Z), (0.8, (50, 0, 0)), (1.6, (50, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.7, (108, -90, 18)), (1.6, (108, -90, 18))])
    _rest(a, "bone", "pos", [(0, Z), (1.0, (0, 9, 3)), (1.1, (0, -4, -6), L), (1.6, (0, -4, -6))])
    _skirt(a, [(0, 0), (1.0, -6), (1.1, 20), (1.7, 6)])

    # reap: materialises out of soul smoke behind the target, rears up (0.8 s), a diagonal chop
    a = m.anim("reap", 1.75)
    _rest(a, "bone", "scale", [(0, (0.15, 0.15, 0.15)), (0.3, (1.05, 1.05, 1.05)), (0.4, (1, 1, 1)),
                               (1.75, (1, 1, 1))])
    _rest(a, "chest", "rot", [(0, Z), (0.8, (-24, 25, 0)), (0.9, (36, -20, 0), L), (1.3, (32, -18, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.8, (165, 30, -14)), (0.9, (-60, -25, -14), L), (1.3, (-56, -22, -14))])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.6, (62, 0, 0)), (1.3, (62, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.5, (108, -90, 18)), (1.4, (108, -90, 18))])
    _rest(a, "arm_l", "rot", [(0, Z), (0.8, (-60, 0, -50)), (0.9, (-20, 0, -20), L)])
    _rest(a, "bone", "pos", [(0, Z), (0.8, (0, 6, 3)), (0.9, (0, -2, -6), L), (1.3, (0, -2, -6))])
    _skirt(a, [(0, 0), (0.3, 18), (0.8, 2), (0.9, 14), (1.4, 4)])

    # lash: the lantern chain wheeled overhead (0.7 s), then cracked forward like a flail
    a = m.anim("lash", 1.6)
    _rest(a, "arm_l", "rot", [(0, Z), (0.35, (-120, 0, -60)), (0.7, (-165, -20, -40)), (0.8, (-80, 20, 16), L),
                              (1.1, (-76, 18, 16))])
    _rest(a, "forearm_l", "rot", [(0, Z), (0.7, (10, 0, 0)), (0.8, (50, 0, 0), L), (1.1, (46, 0, 0))])
    _rest(a, "chain_l", "rot", [(0, Z), (0.35, (-150, 0, 0)), (0.7, (-330, 0, 0)), (0.8, (-416, 0, 0), L),
                                (1.1, (-410, 0, 0)), (1.6, (-360, 0, 0))])
    _rest(a, "chest", "rot", [(0, Z), (0.7, (-10, -25, 0)), (0.8, (14, 25, 0), L), (1.1, (10, 20, 0))])
    _rest(a, "lantern_l", "scale", [(0, (1, 1, 1)), (0.7, (1.3, 1.3, 1.3)), (0.85, (1.6, 1.6, 1.6), L),
                                    (1.1, (1, 1, 1))])
    _rest(a, "bone", "pos", [(0, Z), (0.7, (0, 2, 2)), (0.8, (0, 0, -5), L), (1.1, (0, 0, -5))])
    _skirt(a, [(0, 0), (0.7, 4), (0.8, 12), (1.2, 4)])

    # erupt (phase 2): both arms flung up, the reaper rises, souls burst from the floor
    a = m.anim("erupt", 3.1)
    _rest(a, "bone", "pos", [(0, Z), (0.8, (0, 12, 0)), (2.3, (0, 14, 0))])
    _rest(a, "chest", "rot", [(0, Z), (0.8, (-26, 0, 0)), (2.3, (-26, 0, 0))])
    _rest(a, "head", "rot", [(0, Z), (0.8, (-28, 0, 0)), (2.3, (-28, 0, 0))])
    _rest(a, "jaw", "rot", [(0, Z), (0.8, (32, 0, 0)), (2.3, (32, 0, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.8, (-150, 0, 40)), (2.3, (-150, 0, 40))])
    _rest(a, "arm_l", "rot", [(0, Z), (0.8, (-150, 0, -40)), (2.3, (-150, 0, -40))])
    _rest(a, "forearm_r", "rot", [(0, Z), (0.8, (40, 0, 0)), (2.3, (40, 0, 0))])
    _rest(a, "scythe", "rot", [(0, Z), (0.8, (20, 0, 0)), (2.3, (20, 0, 0))])
    _skirt(a, [(0, 0), (0.8, 26), (2.3, 30), (3.1, 0)])

    # summon: the great lantern raised high, the jaw agape, souls called up through it
    a = m.anim("summon", 2.0)
    _rest(a, "arm_l", "rot", [(0, Z), (0.7, (-160, 0, -16)), (1.4, (-160, 0, -16))])
    _rest(a, "forearm_l", "rot", [(0, Z), (0.7, (40, 0, 0)), (1.4, (40, 0, 0))])
    _rest(a, "chain_l", "rot", [(0, Z), (0.7, (-60, 0, 0)), (1.4, (-56, 0, 0))])
    _rest(a, "lantern_l", "scale", [(0, (1, 1, 1)), (0.7, (1.8, 1.8, 1.8)), (1.4, (1.6, 1.6, 1.6))])
    _rest(a, "head", "rot", [(0, Z), (0.7, (-25, 0, 0)), (1.4, (-25, 0, 0))])
    _rest(a, "jaw", "rot", [(0, Z), (0.7, (30, 0, 0)), (1.4, (30, 0, 0))])
    _rest(a, "bone", "pos", [(0, Z), (0.7, (0, 5, 0)), (1.4, (0, 5, 0))])
    _skirt(a, [(0, 0), (0.7, 14), (1.4, 10)])

    # grab (phase 2): the claw drawn back (0.9 s), a lunging snatch; the victim lifted, drained, hurled
    a = m.anim("grab", 3.6)
    _rest(a, "arm_l", "rot", [(0, Z), (0.9, (40, -30, -40)), (1.0, (-84, 10, 16), L), (1.3, (-90, 10, 16)),
                              (2.6, (-140, 10, 16)), (2.75, (-50, 10, 16), L), (3.0, (-46, 6, 10))])
    _rest(a, "forearm_l", "rot", [(0, Z), (0.9, (-40, 0, 0)), (1.0, (50, 0, 0), L), (2.6, (40, 0, 0))])
    _rest(a, "hand_l", "rot", [(0, Z), (0.9, (-30, 0, 0)), (1.05, (50, 0, 0), L), (2.75, (50, 0, 0)),
                               (2.8, (-20, 0, 0), L)])
    _rest(a, "chest", "rot", [(0, Z), (0.9, (-10, -35, 0)), (1.0, (16, 15, 0), L), (1.3, (6, 10, 0)),
                              (2.6, (-16, 0, 0)), (2.75, (22, 0, 0), L), (3.0, (18, 0, 0))])
    _rest(a, "head", "rot", [(0, Z), (1.3, (-10, 0, 0)), (2.6, (-20, 0, 0))])
    _rest(a, "jaw", "rot", [(0, Z), (1.3, (35, 0, 0)), (2.6, (35, 0, 0)), (2.8, Z)])
    _rest(a, "bone", "pos", [(0, Z), (0.9, (0, 2, 4)), (1.0, (0, 0, -10), L), (1.3, (0, 2, -10)),
                             (2.6, (0, 7, -8))])
    _rest(a, "chain_l", "rot", [(0, Z), (1.0, (-30, 0, 0), L), (2.6, (-20, 0, 0))])
    _skirt(a, [(0, 0), (0.9, 4), (1.0, 14), (2.6, 10), (2.75, 18), (3.2, 4)])

    # roar (phase change): hood thrown back, arms spread wide, the robe blown open by soul fire
    a = m.anim("roar", 2.4)
    _rest(a, "chest", "rot", [(0, Z), (0.5, (-24, 0, 0)), (1.9, (-24, 0, 0))])
    _rest(a, "head", "rot", [(0, Z), (0.5, (-32, 0, 0)), (1.9, (-32, 0, 0))])
    _rest(a, "jaw", "rot", [(0, Z), (0.5, (42, 0, 0)), (1.9, (42, 0, 0))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.5, (-40, 0, 70)), (1.9, (-40, 0, 70))])
    _rest(a, "arm_l", "rot", [(0, Z), (0.5, (-40, 0, -70)), (1.9, (-40, 0, -70))])
    _rest(a, "bone", "pos", [(0, Z), (0.5, (0, 8, 0)), (1.9, (0, 8, 0))])
    _skirt(a, [(0, 0), (0.5, 32), (1.9, 30)])

    # stagger: posture broken, the reaper sags toward the floor, scythe drooping
    a = m.anim("stagger", 2.5)
    _rest(a, "bone", "pos", [(0, Z), (0.3, (0, -10, 2)), (2.0, (0, -10, 2))])
    _rest(a, "chest", "rot", [(0, Z), (0.3, (32, 0, -8)), (2.0, (30, 0, -8))])
    _rest(a, "head", "rot", [(0, Z), (0.3, (20, 0, 10)), (2.0, (20, 0, 10))])
    _rest(a, "arm_r", "rot", [(0, Z), (0.3, (30, 0, 20)), (2.0, (30, 0, 20))])
    _rest(a, "arm_l", "rot", [(0, Z), (0.3, (30, 0, -20)), (2.0, (30, 0, -20))])
    _rest(a, "scythe", "rot", [(0, Z), (0.3, (-12, 0, -28)), (2.0, (-12, 0, -28))])
    _skirt(a, [(0, 0), (0.3, -8), (2.0, -8)])
