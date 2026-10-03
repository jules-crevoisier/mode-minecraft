"""The Sculk Spawn (Le Rejeton du sculk): a towering, hunched abomination grown out of the Sealed Lab's
catalyst (about 5 blocks tall with its tendrils).

Silhouette: a great crown of branching Warden tendrils over an eyeless skull hung low on the chest,
a hollow ribcage around a pulsing cyan heart, and two drooping arms with one joint too many whose
claws scrape the floor. The left arm is swollen with a sculk tumour and still wears its shackle;
a broken hazard-striped containment collar and its chain hang from the neck."""
from ..models import Model, FACE_ID
from ..texgen import mix, mul

SK = (24, 56, 68)        # sculk hide
SK_L = (44, 100, 112)    # cell centres
SK_D = (7, 22, 30)       # cell walls
CY = (64, 236, 248)      # soul glow
CY_D = (18, 128, 150)
BONE = (214, 206, 180)
BONE_D = (150, 140, 112)
BONE_S = (92, 86, 72)
CAV = (8, 12, 18)        # inside the ribcage
GUM = (60, 26, 40)       # mouth
IRON = (128, 134, 138)
IRON_D = (66, 70, 76)
RUST = (122, 78, 46)
HAZ_Y = (232, 184, 36)
HAZ_K = (30, 28, 26)


def _h(*v):
    r = 0x9E3779B9
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        r ^= r >> 13
    return r


def _cells(face, x, y, seed, s):
    """Jittered-grid Voronoi: (distance to nearest seed, gap to the second nearest, cell hash)."""
    fid = FACE_ID[face]
    gx, gy = x // s, y // s
    best = [(1e9, 0), (1e9, 0)]
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = gx + dx, gy + dy
            hh = _h(cx, cy, seed, fid)
            px = cx * s + (hh % 97) / 97 * s
            py = cy * s + ((hh >> 8) % 89) / 89 * s
            d = ((x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2) ** 0.5
            if d < best[0][0]:
                best = [(d, hh), best[0]]
            elif d < best[1][0]:
                best[1] = (d, hh)
    return best[0][0], best[1][0] - best[0][0], best[0][1]


def sculk(seed=0, s=5, base=SK, light=SK_L, wall=SK_D, pores=0):
    """Sculk hide: soft rounded cells with dark walls; growths carry glowing pores (pores=n: one cell in n)."""
    def f(face, x, y, w, h):
        d, gap, hh = _cells(face, x, y, seed, s)
        if gap < 0.6:
            return mix(wall, base, 0.35)
        if pores and hh % pores == 0 and d < 1.2:
            return CY
        c = mix(light, base, min(1.0, d / (s * 0.7)))
        if hh % 5 == 0:   # some cells darker: blotchy, like the Warden's hide
            c = mul(c, 0.78)
        return c
    return f


def sculk_glow(seed=0, s=5, pores=7):
    def f(face, x, y, w, h):
        d, gap, hh = _cells(face, x, y, seed, s)
        if gap >= 0.6 and pores and hh % pores == 0 and d < 1.2:
            return CY
        return None
    return f


def bone(face, x, y, w, h):
    """Ivory with a lit top edge and a shaded underside."""
    if face == "top":
        return mul(BONE, 1.05)
    if face == "bottom":
        return BONE_S
    if h > 2 and y == h - 1:
        return BONE_D
    if y == 0:
        return mul(BONE, 1.06)
    return BONE if (x * 3 + y * 5) % 11 else BONE_D


def iron(seed=0, hazard=False):
    def f(face, x, y, w, h):
        if hazard and face not in ("top", "bottom") and 0 < y < h - 1:
            return HAZ_Y if ((x + y) // 2) % 2 == 0 else HAZ_K
        if y == 0 or y == h - 1 or (face in ("top", "bottom") and (x in (0, w - 1))):
            return IRON_D
        if (x * 7 + y * 3 + seed) % 13 == 0:
            return RUST
        if x % 6 == 2 and y == 1:
            return (190, 196, 200)  # rivet
        return IRON
    return f


def chain(face, x, y, w, h):
    """Alternating oval links (transparent gaps), rust on every few links."""
    k = y % 4
    if face in ("top", "bottom"):
        return IRON_D
    if k == 3:
        return None if x != w // 2 else IRON_D
    col = IRON if k in (0, 2) else IRON_D
    if (y // 4) % 3 == 1:
        col = mix(col, RUST, 0.4)
    return col


def _tendril_core(x, y, w, h):
    """0 = rim, 1 = inner membrane, 2 = bright core (a soft glowing slit, ribbed every 4 px)."""
    if x == 0 or x == w - 1 or y == 0:
        return 0
    c = (w - 1) / 2
    if abs(x - c) <= (0.6 if w < 6 else 1.1):
        return 2
    return 1


def tendril(seed=0):
    """Broad Warden fin: dark rim, deep-teal membrane, a glowing slit down its middle."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            k = _tendril_core(x, y, w, h)
            return (SK_D, mix(CY_D, SK, 0.45 + 0.1 * ((x + y + seed) % 2)), CY)[k]
        return SK_D if face != "top" else SK
    return f


def tendril_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back") and _tendril_core(x, y, w, h) == 2:
            return CY
        return None
    return f


def cavity(face, x, y, w, h):
    """Inside of the ribcage: near-black sinew streaks and a few branching soul veins."""
    if face != "front":
        return CAV
    vein = (x + y // 3) % 7 == 0 or (y > h // 2 and (x - y // 2) % 9 == 0)
    if vein and y % 5 != 4:
        return CY_D
    return (14, 26, 34) if x % 3 == 0 else CAV


def heart(face, x, y, w, h):
    """Bright soul-flesh with darker vein lines and a dim rim."""
    if x in (0, w - 1) or y in (0, h - 1):
        return CY_D
    if (x * 5 + y * 3) % 7 == 0 or (x * 2 - y * 5) % 11 == 0:
        return (34, 178, 196)
    return CY if abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5) > 1.6 else (200, 255, 255)


def build():
    m = Model("sculk_spawn", seed=45, shadow=1.6, walk_speed=0.7, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -27, 2))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=(10, 0, 0))
    m.part("chest", "torso", pivot=(0, -11, 0), rot=(8, 0, 5))
    m.part("heart", "chest", pivot=(3, -13, -6))
    m.part("head", "chest", pivot=(-1, -32, -8), rot=(8, 6, -12))
    m.part("jaw", "head", pivot=(0, -1, -2))
    m.part("tendril_r", "head", pivot=(-5, -10, -4), rot=(-18, 20, -44))
    m.part("tendril_r2", "tendril_r", pivot=(-1, -16, 0), rot=(-12, 0, -22))
    m.part("tendril_l", "head", pivot=(5, -10, -4), rot=(-18, -20, 44))
    m.part("tendril_l2", "tendril_l", pivot=(1, -16, 0), rot=(-12, 0, 22))
    m.part("collar_chain", "chest", pivot=(-6, -26, -12), rot=(-30, 0, 0))
    m.part("arm_r", "chest", pivot=(-17, -24, -1), rot=(-22, 0, 22))
    m.part("arm_r2", "arm_r", pivot=(0, 17, 0), rot=(30, 0, -34))
    m.part("arm_r3", "arm_r2", pivot=(0, 15, 0), rot=(-40, 0, 22))
    m.part("hand_r", "arm_r3", pivot=(0, 15, 0), rot=(18, 0, 0))
    m.part("arm_l", "chest", pivot=(18, -24, -1), rot=(-22, 0, -22))
    m.part("arm_l2", "arm_l", pivot=(0, 19, 0), rot=(30, 0, 34))
    m.part("arm_l3", "arm_l2", pivot=(0, 15, 0), rot=(-40, 0, -22))
    m.part("hand_l", "arm_l3", pivot=(0, 15, 0), rot=(18, 0, 0))
    m.part("shackle_chain", "arm_l3", pivot=(0, 12, 4), rot=(30, 0, 0))
    m.part("leg_r", "hips", pivot=(-7, 0, 0), rot=(-28, 0, 9))
    m.part("shin_r", "leg_r", pivot=(0, 14, 0), rot=(56, 0, 0))
    m.part("foot_r", "shin_r", pivot=(0, 14, 0), rot=(-28, 0, -9))
    m.part("leg_l", "hips", pivot=(7, 0, 0), rot=(-28, 0, -9))
    m.part("shin_l", "leg_l", pivot=(0, 14, 0), rot=(56, 0, 0))
    m.part("foot_l", "shin_l", pivot=(0, 14, 0), rot=(-28, 0, 9))

    # ------------------------------------------------------------------ hips and legs
    m.box("hips", -9, -5, -5, 18, 8, 11, sculk(1))
    m.box("hips", -10, -4, -4, 3, 5, 9, bone)            # hip crests
    m.box("hips", 7, -4, -4, 3, 5, 9, bone)
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"leg_{side}", -4, -1, -4, 8, 15, 8, sculk(2 + sx))
        m.box(f"shin_{side}", -3, -1, -3, 6, 15, 6, sculk(4 + sx, s=4))
        m.box(f"shin_{side}", -2, -3, -6, 5, 5, 3, bone)   # knee spur
        m.box(f"foot_{side}", -4, -1, -6, 8, 3, 9, sculk(6 + sx, s=4))
        for x in (-4, -1, 2):
            m.box(f"foot_{side}", x, 0, -9, 2, 2, 3, bone)  # toe claws

    # ------------------------------------------------------------------ torso: spine, ribcage, heart
    m.box("torso", -6, -12, -2, 12, 13, 8, sculk(8))
    for i in range(4):
        m.box("torso", -1, -11 + i * 3, 6, 2, 2, 2, bone)   # vertebrae
    # back of the chest: a hunched mass of sculk; the front is a hollow ribcage
    m.box("chest", -13, -24, -1, 26, 24, 10, {"front": cavity, "*": sculk(10, s=6)})
    m.box("chest", -11, -22, -3, 22, 20, 2, cavity)
    # ribs: five hoops (rounded: shorter at the top and bottom) around the open chest, the third one
    # snapped on the right; a split sternum and a heavy collarbone yoke
    for i, half in enumerate((9, 11, 12, 11, 9)):
        y = -22 + i * 4
        right = 5 if i == 2 else half
        m.box("chest", 1, y, -11, half, 2, 2, bone)
        m.box("chest", -1 - right, y, -11, right, 2, 2, bone)
        m.box("chest", half, y, -10, 2, 2, 10, bone)
        m.box("chest", -half - 2, y, -10, 2, 2, 10, bone)
    m.box("chest", -9, -12, -12, 3, 2, 2, bone)              # the snapped end, bent outward
    m.box("chest", -1, -23, -12, 2, 9, 2, bone)
    m.box("chest", -1, -9, -12, 2, 5, 2, bone)
    m.box("chest", -13, -26, -11, 26, 3, 5, bone)
    m.box("heart", -4, -4, -4, 8, 8, 7, heart, glow=heart)
    m.box("heart", -1, -7, -2, 3, 3, 3, heart, glow=heart)   # severed artery
    # shoulder hump and sculk tumours on the back
    m.box("chest", -15, -30, -5, 30, 6, 14, sculk(11, s=6))
    m.box("chest", -13, -34, 0, 10, 5, 9, sculk(12, s=3, pores=3), glow=sculk_glow(12, s=3, pores=3))
    m.box("chest", 3, -36, -1, 11, 7, 10, sculk(13, s=3, pores=3), glow=sculk_glow(13, s=3, pores=3))
    m.box("chest", -4, -12, 8, 9, 8, 4, sculk(14, s=3, pores=3), glow=sculk_glow(14, s=3, pores=3))
    m.box("chest", -9, -30, 8, 16, 11, 6, sculk(15, s=4, pores=3), glow=sculk_glow(15, s=4, pores=3))
    for k in range(4):   # dorsal spikes along the hunched spine
        m.box("chest", -1, -25 + k * 5, 9, 2, 3, 3 + (k % 2) * 2, bone)
    # the containment collar: a hazard-striped iron band, its right half torn away
    m.box("chest", -3, -30, -13, 13, 4, 4, iron(1, hazard=True))
    m.box("chest", 7, -30, -11, 4, 4, 9, iron(2, hazard=True))
    m.box("chest", -7, -29, -12, 4, 2, 2, iron(3))
    m.box("collar_chain", 0, 0, -1, 2, 18, 2, chain)

    # ------------------------------------------------------------------ head: eyeless skull, jaw, tendril crown
    m.box("head", -8, -11, -13, 16, 10, 13, {
        "front": sculk(20, s=4),
        "bottom": lambda f_, x, y, w, h: (220, 220, 200) if y >= h - 2 and x % 2 == 0 else GUM,
        "*": sculk(21, s=4)})
    m.box("head", -7, -13, -12, 14, 2, 10, sculk(22, s=3))      # brow ridge
    m.box("head", -7, -2, -14, 14, 2, 1, lambda f_, x, y, w, h: BONE if x % 2 == 0 else CAV)  # upper fangs
    # glowing gill slits where the eyes should be
    m.box("head", -8, -8, -12, 1, 4, 8, {"right": lambda f_, x, y, w, h: CY if x % 3 == 0 else SK_D, "*": SK_D},
          glow={"right": lambda f_, x, y, w, h: CY if x % 3 == 0 else None})
    m.box("head", 7, -8, -12, 1, 4, 8, {"left": lambda f_, x, y, w, h: CY if x % 3 == 0 else SK_D, "*": SK_D},
          glow={"left": lambda f_, x, y, w, h: CY if x % 3 == 0 else None})
    m.box("jaw", -7, 0, -12, 14, 4, 11, {
        "top": lambda f_, x, y, w, h: CY if y == 0 and x % 2 == 1 else GUM,
        "front": lambda f_, x, y, w, h: BONE if y == 0 and x % 2 == 1 else sculk(23, s=3)(f_, x, y, w, h),
        "*": sculk(23, s=3)}, glow={"top": lambda f_, x, y, w, h: CY if y == 0 and x % 2 == 1 else None})
    for side, sx in (("r", -1), ("l", 1)):
        t1, t2 = f"tendril_{side}", f"tendril_{side}2"
        m.box(t1, -5, -20, -1, 10, 20, 2, tendril(1 + sx), glow=tendril_glow(1 + sx))
        m.box(t2, -4, -17, -1, 8, 17, 2, tendril(2 + sx), glow=tendril_glow(2 + sx))
        m.box(t2, -2, -23, -1, 4, 6, 2, tendril(3 + sx), glow=tendril_glow(3 + sx))
        # a branching prong on the outer edge
        m.box(t1, 5 if sx > 0 else -9, -16, -1, 4, 8, 2, tendril(4 + sx), glow=tendril_glow(4 + sx))
        m.box(t1, 9 if sx > 0 else -11, -20, -1, 2, 6, 2, tendril(5 + sx), glow=tendril_glow(5 + sx))

    # ------------------------------------------------------------------ arms: three segments and a long claw
    for side, sx in (("r", -1), ("l", 1)):
        big = sx > 0
        a1, a2, a3, hand = f"arm_{side}", f"arm_{side}2", f"arm_{side}3", f"hand_{side}"
        w1 = 8 if big else 7
        m.box(a1, -6, -6, -6, 12, 10, 12, sculk(30 + sx, s=4))
        # scapula spikes tearing out of the shoulder
        m.box(a1, -1 + 2 * sx, -12, -1, 2, 7, 2, bone)
        m.box(a1, 2 * sx - (3 if sx < 0 else 0) + (2 if sx > 0 else 0), -9, 2, 2, 4, 2, bone)
        m.box(a1, -w1 // 2, 0, -w1 // 2, w1, 19 if big else 17, w1, sculk(31 + sx))
        m.box(a2, -3, -1, -3, 6, 16, 6, sculk(32 + sx, s=4))
        m.box(a2, -4, -2, -2, 8, 4, 6, bone)                  # elbow knob
        m.box(a3, -3, -1, -3, 6, 16, 6, sculk(33 + sx, s=4))
        m.box(a3, -4, -2, -4, 8, 3, 7, bone)                  # second elbow
        m.box(hand, -4, 0, -4, 8, 5, 7, sculk(34 + sx, s=3))
        for x in (-4, -1, 2):
            ln = 14 if x == -1 else 12
            m.box(hand, x, 4, -4, 2, ln, 2,
                  lambda f_, xx, yy, w, h: BONE if yy >= h - 5 else SK_D if yy % 4 == 0 else SK_L)
        m.box(hand, 4 if sx > 0 else -5, 2, 1, 1, 7, 2, bone)  # thumb claw
    # the swollen left arm: a sculk tumour and the shackle with its broken chain
    m.box("arm_l2", -6, 1, -6, 12, 11, 12, sculk(40, s=3, pores=3), glow=sculk_glow(40, s=3, pores=3))
    m.box("arm_l3", -4, 9, -4, 8, 4, 8, iron(5, hazard=True))
    m.box("shackle_chain", 0, 0, -1, 2, 16, 2, chain)
    m.box("arm_r", -5, 6, -6, 6, 6, 5, sculk(41, s=2, pores=2), glow=sculk_glow(41, s=2, pores=2))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.2)
    idle.rot("chest", (0, (0, 0, 0)), (1.6, (-4, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (4, 6, 0)), (1.6, (0, 0, 0)), (2.4, (4, -6, 0)), (3.2, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.6, (10, 0, 0)), (3.2, (0, 0, 0)))
    # lub-dub heartbeat, twice per loop
    idle.scale("heart", (0, (1, 1, 1)), (0.15, (1.35, 1.35, 1.35)), (0.3, (1, 1, 1)), (0.45, (1.2, 1.2, 1.2)),
               (0.7, (1, 1, 1)), (1.6, (1, 1, 1)), (1.75, (1.35, 1.35, 1.35)), (1.9, (1, 1, 1)),
               (2.05, (1.2, 1.2, 1.2)), (2.3, (1, 1, 1)), (3.2, (1, 1, 1)))
    for t, sx in (("tendril_r", -1), ("tendril_l", 1)):
        idle.rot(t, (0, (0, 0, 0)), (0.4, (0, 0, 6 * sx)), (0.6, (0, 0, -2 * sx)), (1.6, (0, 0, 0)),
                 (2.0, (0, 0, 5 * sx)), (2.2, (0, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.6, (4, 0, -3)), (3.2, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.6, (-3, 0, 3)), (3.2, (0, 0, 0)))
    idle.rot("collar_chain", (0, (0, 0, 0)), (1.6, (6, 0, 8)), (3.2, (0, 0, 0)))
    idle.rot("shackle_chain", (0, (0, 0, 0)), (1.6, (-8, 0, 0)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    for leg, sh, sign in (("leg_r", "shin_r", 1), ("leg_l", "shin_l", -1)):
        walk.rot(leg, (0, (22 * sign, 0, 0)), (0.9, (-22 * sign, 0, 0)), (1.8, (22 * sign, 0, 0)))
        walk.rot(sh, (0, (0, 0, 0)), (0.45, (16 if sign > 0 else 0, 0, 0)), (0.9, (0, 0, 0)),
                 (1.35, (16 if sign < 0 else 0, 0, 0)), (1.8, (0, 0, 0)))
    # the arms drag and swing like dead weight, out of step with the legs
    walk.rot("arm_r", (0, (-14, 0, 0)), (0.9, (16, 0, 0)), (1.8, (-14, 0, 0)))
    walk.rot("arm_l", (0, (16, 0, 0)), (0.9, (-14, 0, 0)), (1.8, (16, 0, 0)))
    walk.rot("chest", (0, (0, 6, 0)), (0.9, (0, -6, 0)), (1.8, (0, 6, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.45, (0, -2, 0)), (0.9, (0, 0, 0)), (1.35, (0, -2, 0)), (1.8, (0, 0, 0)))

    # whip: the head and chest wind far to the right, the tendril crown lashes across (impact 0.8 s)
    a = m.anim("whip", 1.5)
    a.rot("chest", (0, (0, 0, 0)), (0.65, (-8, 50, 0)), (0.8, (6, -55, 0), "linear"), (1.05, (6, -50, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.65, (-10, 25, -15)), (0.8, (25, -30, 20), "linear"), (1.05, (20, -25, 15)), (1.5, (0, 0, 0)))
    for t in ("tendril_r", "tendril_l"):
        a.rot(t, (0, (0, 0, 0)), (0.65, (-40, 0, 0)), (0.8, (60, 0, 0), "linear"), (1.05, (50, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-60, 50, 40)), (0.8, (-80, -40, 10), "linear"), (1.05, (-70, -40, 10)), (1.5, (0, 0, 0)))

    # slam: both arms rise over the head (long telegraph) and crash down together (impact 1.0 s)
    a = m.anim("slam", 2.0)
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.85, (-185, 0, 10 * sx)), (1.0, (-55, 0, 0), "linear"), (1.5, (-50, 0, 0)), (2.0, (0, 0, 0)))
    for arm in ("arm_r2", "arm_l2"):
        a.rot(arm, (0, (0, 0, 0)), (0.85, (-30, 0, 0)), (1.0, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.85, (-28, 0, 0)), (1.0, (26, 0, 0), "linear"), (1.5, (22, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.85, (-15, 0, 0)), (1.0, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.85, (30, 0, 0)), (1.0, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.85, (0, 4, 2)), (1.0, (0, -4, -3), "linear"), (1.5, (0, -4, -3)), (2.0, (0, 0, 0)))

    # sonic: the skull draws back, the ribs flare, the jaw unhinges; the boom fires at 1.25 s
    a = m.anim("sonic", 2.1)
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-26, 0, 0)), (1.25, (10, 0, 0), "linear"), (1.6, (8, 0, 0)), (2.1, (0, 0, 0)))
    a.scale("chest", (0, (1, 1, 1)), (1.1, (1.12, 1.06, 1.12)), (1.25, (0.96, 1, 0.96), "linear"), (1.6, (1, 1, 1)), (2.1, (1, 1, 1)))
    a.scale("heart", (0, (1, 1, 1)), (1.1, (1.4, 1.4, 1.4)), (1.25, (0.8, 0.8, 0.8), "linear"), (1.6, (1, 1, 1)), (2.1, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-30, 0, 0)), (1.25, (22, 0, 0), "linear"), (1.6, (18, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.1, (50, 0, 0)), (1.6, (50, 0, 0)), (2.1, (0, 0, 0)))
    for t, sx in (("tendril_r", -1), ("tendril_l", 1)):
        a.rot(t, (0, (0, 0, 0)), (1.1, (30, 0, -20 * sx)), (1.25, (-20, 0, 15 * sx), "linear"), (2.1, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (1.1, (30, 0, 40 * sx)), (1.25, (10, 0, 30 * sx)), (2.1, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (1.1, (0, 0, 3)), (1.25, (0, 0, -2), "linear"), (2.1, (0, 0, 0)))

    # pulse: curls around the heart, then bursts open, arms flung wide (impact 0.9 s)
    a = m.anim("pulse", 1.9)
    a.pos("bone", (0, (0, 0, 0)), (0.75, (0, -6, 0)), (0.9, (0, 2, 0), "linear"), (1.3, (0, 1, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.75, (24, 0, 0)), (0.9, (-30, 0, 0), "linear"), (1.3, (-24, 0, 0)), (1.9, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.75, (-60, -30 * sx, -30 * sx)), (0.9, (-20, 0, 80 * sx), "linear"),
              (1.3, (-20, 0, 75 * sx)), (1.9, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.75, (0.7, 0.7, 0.7)), (0.9, (1.6, 1.6, 1.6), "linear"), (1.3, (1.3, 1.3, 1.3)), (1.9, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (0.75, (20, 0, 0)), (0.9, (-35, 0, 0), "linear"), (1.3, (-30, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.9, (45, 0, 0)), (1.3, (45, 0, 0)), (1.9, (0, 0, 0)))

    # erupt: rears up, then drives both claws into the floor and holds them there (impact 0.85 s)
    a = m.anim("erupt", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.65, (-24, 0, 0)), (0.85, (34, 0, 0), "linear"), (1.45, (32, 0, 0)), (2.0, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.65, (-150, 0, 20 * sx)), (0.85, (-40, 0, 6 * sx), "linear"), (1.45, (-40, 0, 6 * sx)), (2.0, (0, 0, 0)))
    for arm in ("arm_r3", "arm_l3"):
        a.rot(arm, (0, (0, 0, 0)), (0.65, (30, 0, 0)), (0.85, (30, 0, 0)), (1.45, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.65, (0, 3, 0)), (0.85, (0, -5, 0), "linear"), (1.45, (0, -5, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.65, (30, 0, 0)), (0.85, (5, 0, 0)), (2.0, (0, 0, 0)))

    # scream (phase 2): rears to full height, arms out, skull thrown back, jaw wide (impact 0.9 s)
    a = m.anim("scream", 2.4)
    a.rot("torso", (0, (0, 0, 0)), (0.75, (-20, 0, 0)), (0.9, (-28, 0, 0), "linear"), (1.9, (-28, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.75, (-14, 0, 0)), (1.9, (-16, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.75, (-20, 0, 0)), (0.9, (-40, 0, 0), "linear"), (1.9, (-40, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.75, (20, 0, 0)), (0.9, (55, 0, 0), "linear"), (1.9, (55, 0, 0)), (2.4, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.75, (-40, 0, 50 * sx)), (0.9, (-70, 0, 95 * sx), "linear"), (1.9, (-70, 0, 95 * sx)), (2.4, (0, 0, 0)))
    for t, sx in (("tendril_r", -1), ("tendril_l", 1)):
        a.rot(t, (0, (0, 0, 0)), (0.9, (-25, 0, 25 * sx), "linear"), (1.0, (-15, 0, 15 * sx)), (1.1, (-25, 0, 25 * sx)),
              (1.9, (-25, 0, 25 * sx)), (2.4, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.9, (1.35, 1.35, 1.35)), (1.9, (1.35, 1.35, 1.35)), (2.4, (1, 1, 1)))

    # lunge (phase 2): drops onto all fours, then springs claws-first (impact 0.7 s)
    a = m.anim("lunge", 1.8)
    a.rot("torso", (0, (0, 0, 0)), (0.55, (30, 0, 0)), (0.7, (40, 0, 0), "linear"), (1.2, (36, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.55, (0, -9, 4)), (0.7, (0, -4, -10), "linear"), (1.2, (0, -6, -10)), (1.8, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.55, (-20, 0, 10 * sx)), (0.7, (-120, 0, 10 * sx), "linear"),
              (0.85, (-60, 0, 10 * sx)), (1.2, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-25, 0, 0)), (0.7, (-10, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.55, (35, 0, 0)), (0.85, (35, 0, 0)), (1.8, (0, 0, 0)))
    for leg in ("leg_r", "leg_l"):
        a.rot(leg, (0, (0, 0, 0)), (0.55, (-30, 0, 0)), (0.7, (25, 0, 0), "linear"), (1.2, (0, 0, 0)), (1.8, (0, 0, 0)))

    # booms (phase 2): three sonic booms in a row, each with its own small draw-back (1.0, 1.6, 2.2 s)
    a = m.anim("booms", 3.0)
    keys_c, keys_h, keys_s = [(0, (0, 0, 0))], [(0, (0, 0, 0))], [(0, (1, 1, 1))]
    for i, t in enumerate((1.0, 1.6, 2.2)):
        draw = 0.85 if i == 0 else t - 0.35
        keys_c += [(draw, (-24, 12 * (i - 1), 0)), (t, (10, 12 * (i - 1), 0), "linear")]
        keys_h += [(draw, (-28, 0, 0)), (t, (20, 0, 0), "linear")]
        keys_s += [(draw, (1.4, 1.4, 1.4)), (t, (0.8, 0.8, 0.8), "linear")]
    keys_c += [(2.5, (8, 0, 0)), (3.0, (0, 0, 0))]
    keys_h += [(2.5, (16, 0, 0)), (3.0, (0, 0, 0))]
    keys_s += [(2.5, (1, 1, 1)), (3.0, (1, 1, 1))]
    a.rot("chest", *keys_c)
    a.rot("head", *keys_h)
    a.scale("heart", *keys_s)
    a.rot("jaw", (0, (0, 0, 0)), (0.85, (50, 0, 0)), (2.5, (50, 0, 0)), (3.0, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.85, (25, 0, 40 * sx)), (2.5, (25, 0, 40 * sx)), (3.0, (0, 0, 0)))

    # roar: phase change, rears up and spreads everything
    a = m.anim("roar", 2.6)
    a.rot("torso", (0, (0, 0, 0)), (0.6, (-26, 0, 0)), (2.1, (-26, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-30, 0, 0)), (2.1, (-30, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (55, 0, 0)), (2.1, (55, 0, 0)), (2.6, (0, 0, 0)))
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        a.rot(arm, (0, (0, 0, 0)), (0.6, (-60, 0, 80 * sx)), (2.1, (-60, 0, 80 * sx)), (2.6, (0, 0, 0)))
    for t, sx in (("tendril_r", -1), ("tendril_l", 1)):
        a.rot(t, (0, (0, 0, 0)), (0.6, (-20, 0, 30 * sx)), (0.7, (-10, 0, 20 * sx)), (0.8, (-20, 0, 30 * sx)),
              (0.9, (-10, 0, 20 * sx)), (2.1, (-20, 0, 30 * sx)), (2.6, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.6, (1.4, 1.4, 1.4)), (2.1, (1.4, 1.4, 1.4)), (2.6, (1, 1, 1)))

    # stagger: posture broken, collapses onto its knuckles, the heart flickering
    a = m.anim("stagger", 2.4)
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -10, 2)), (1.9, (0, -10, 2)), (2.4, (0, 0, 0)))
    for leg, sh in (("leg_r", "shin_r"), ("leg_l", "shin_l")):
        a.rot(leg, (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.9, (-40, 0, 0)), (2.4, (0, 0, 0)))
        a.rot(sh, (0, (0, 0, 0)), (0.3, (40, 0, 0)), (1.9, (40, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.3, (24, 0, 8)), (1.9, (24, 0, 8)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -10)), (1.9, (30, 0, -10)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 0)), (1.9, (-20, 0, 0)), (2.4, (0, 0, 0)))
    a.scale("heart", (0, (1, 1, 1)), (0.4, (0.6, 0.6, 0.6)), (0.6, (1.1, 1.1, 1.1)), (0.8, (0.6, 0.6, 0.6)),
            (1.4, (0.7, 0.7, 0.7)), (1.9, (0.6, 0.6, 0.6)), (2.4, (1, 1, 1)))
    return m
