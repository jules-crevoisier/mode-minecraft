"""The Bell Keeper (Le Sonneur de glas): a gaunt monk-knight about five blocks tall, stooped under a
pointed grey cowl with a faint ghostly face, tattered robes over dented plate, a broken bell-yoke
strapped across his back and, in his right fist, a huge cracked bronze bell swung on a heavy chain."""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
ROBE = (132, 127, 116)
ROBE_D = (82, 78, 72)
ROBE_L = (166, 160, 146)
SACK = (104, 92, 72)             # patches and rope
STEEL = (78, 84, 94)
STEEL_D = (44, 47, 56)
STEEL_L = (170, 178, 190)
BRONZE = (158, 102, 48)
BRONZE_D = (88, 54, 26)
BRONZE_L = (236, 184, 106)
PATINA = (78, 150, 124)
IRON = (62, 62, 66)
IRON_L = (120, 120, 126)
WOOD = (96, 66, 42)
WOOD_D = (60, 40, 26)
VOID = (14, 12, 20)
GHOST = (196, 220, 255)
GHOST_D = (86, 104, 140)
RUNE = (255, 206, 120)
CHAIN_REST = 4 / 64          # the chain part is 64 px long, scaled down to the 4 px between fist and bell


def _h(x, y, s):
    """Deterministic hash in [0, 1)."""
    v = (x * 73856093) ^ (y * 19349663) ^ (s * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65536.0


def _side(face):
    return face not in ("top", "bottom")


# ------------------------------------------------------------------ paints
def robe(base=ROBE, seed=0, hem=0, patch=True):
    """Heavy wool: broad soft vertical folds, grime toward the hem, a stitched patch, ragged hem."""
    def f(face, x, y, w, h):
        if hem and _side(face):
            cut = int(_h(x // 2, 0, seed) * hem * 1.7) + (x % 4 == 1)
            if y >= h - cut:
                return None
        if not _side(face):
            return mul(base, 0.86 + 0.06 * _h(x // 2, y // 2, seed))
        fold = math.sin((x + seed * 1.7) * 1.05) + 0.45 * math.sin((x + seed) * 2.3 + y * 0.08)
        c = mul(base, 0.92 + 0.11 * fold)
        if fold < -0.9:
            c = mul(base, 0.66)                                               # deep fold shadow
        c = mix(c, mul(base, 0.5), 0.45 * (y / max(1, h - 1)) ** 2)            # grime at the bottom
        if patch and w >= 6 and h >= 10:
            px, py = int(_h(1, 2, seed) * (w - 5)), int(_h(3, 4, seed) * (h - 8)) + 2
            if px <= x < px + 4 and py <= y < py + 5:
                edge = x in (px, px + 3) or y in (py, py + 4)
                return mul(SACK, 0.66) if edge and (x + y) % 2 else SACK
        if _h(x, y, seed + 9) < 0.025:
            return mul(base, 0.45)                                            # moth holes
        return c
    return f


def plate(base=STEEL, seed=0, dents=2, rivets=True, trim=None):
    """Dented armour plate: bright top edge, dark lower rim, rivets, a few hammered dents."""
    d_pts = [(_h(i, 1, seed), _h(i, 2, seed)) for i in range(dents)]
    rim = trim or mul(base, 0.6)

    def f(face, x, y, w, h):
        if y == 0 and _side(face):
            return mul(base, 1.45)
        if x == 0 or y == h - 1 or x == w - 1 or (y == 0 and not _side(face)):
            if rivets and (x + y) % 3 == 0 and _side(face):
                return STEEL_L
            return rim
        c = mul(base, 1.12 - 0.3 * y / max(1, h))
        for (u, v) in d_pts:
            cx, cy = 1 + u * (w - 2), 1 + v * (h - 2)
            dd = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dd < 1.1:
                c = mul(base, 0.62)
            elif dd < 1.9 and (x < cx or y < cy):
                c = mul(base, 1.3)
        if (x * 7 + y * 13 + seed) % 23 == 0:
            c = mix(c, (122, 84, 56), 0.5)                                    # rust spot
        return c
    return f


def bronze(seed=0, runes_at=None, crack=False, light=1.0):
    """Cast bronze shaded like a cylinder (specular streak, dark edges), verdigris drips, optional
    rune inscription band and crack."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(BRONZE_D, 0.8 * light)
        if face == "top":
            r = max(abs(x - (w - 1) / 2), abs(y - (h - 1) / 2)) / max(1, w / 2)
            c = mix(BRONZE_L, BRONZE, min(1, r * 1.3))
            if int(r * w / 2) % 3 == 2:
                c = mul(c, 0.82)                                              # turned rings
            if _h(x, y, seed + 3) < 0.05:
                c = mix(c, PATINA, 0.6)
            return mul(c, light)
        u = (x + 0.5) / w
        shade = 0.72 + 0.5 * math.sin(math.pi * u) - (0.14 if face in ("back", "left") else 0)
        c = mul(BRONZE, shade * light)
        if 0.24 < u < 0.34 and face in ("front", "right"):
            c = mix(c, BRONZE_L, 0.7)                                         # specular streak
        if runes_at is not None and runes_at <= y < runes_at + 3:
            if y != runes_at + 1:
                return mul(BRONZE_D, 0.95 * shade)
            return RUNE_BG if _rune(x, seed) else mul(BRONZE_D, 1.1)
        top = runes_at + 3 if runes_at is not None else 0
        drip = _h(x, 7, seed)
        if drip < 0.22 and top <= y < top + 2 + drip * 30 and not (x % 5 == 0 and y > top + 3):
            c = mix(c, PATINA, 0.8 - 0.5 * (y - top) / (3 + drip * 30))
        if crack and face == "front" and x == w // 2 + int(2 * math.sin(y * 0.9)):
            return VOID
        return c
    return f


RUNE_BG = (250, 210, 130)


def _rune(x, seed):
    return (x + seed) % 4 != 3 and _h(x, 11, seed) > 0.35


def bronze_glow(runes_at, seed=0, crack=False):
    def f(face, x, y, w, h):
        if not _side(face):
            return None
        if runes_at <= y < runes_at + 3 and y == runes_at + 1 and _rune(x, seed):
            return RUNE
        if crack and face == "front" and x == w // 2 + int(2 * math.sin(y * 0.9)):
            return (255, 150, 70)
        return None
    return f


def chain_link(face, x, y, w, h):
    if y in (0, h - 1) or x in (0, w - 1):
        return IRON_L if y == 0 else IRON
    return mul(IRON, 0.55)


def wood(seed=0):
    def f(face, x, y, w, h):
        if not _side(face):
            return WOOD_D if (x + y) % 3 == 0 else WOOD
        if (y + seed) % 9 in (0, 1):
            return IRON if (y + seed) % 9 == 0 else IRON_L                    # iron strap
        grain = (x * 3 + int(_h(x, y // 4, seed) * 3)) % 4
        return (WOOD, mul(WOOD, 1.15), WOOD_D, WOOD)[grain]
    return f


def _opening(x, y):
    """Arch-shaped cowl opening on the 12 x 14 front face (rows from the top)."""
    if y < 3 or y > 13 or x < 2 or x > 9:
        return False
    if y == 3:
        return 4 <= x <= 7
    if y == 4:
        return 3 <= x <= 8
    return True


def cowl_front(face, x, y, w, h):
    """The cowl seen from the front: a dark arched opening, deeper toward the top."""
    if _opening(x, y):
        if (y == 6 and x in (3, 4, 7, 8)) or (y in (8, 9) and x in (3, 8)):
            return (40, 46, 62)                                               # pale bone under the shadow
        return mix(VOID, (36, 34, 40), (y - 3) / 14)
    return robe(ROBE, 40, patch=False)(face, x, y, w, h)


def cowl_glow(face, x, y, w, h):
    if face != "front":
        return None
    if y == 7 and x in (3, 4, 7, 8):
        return GHOST if x in (4, 7) else GHOST_D
    if y == 8 and x in (4, 7):
        return mul(GHOST_D, 0.6)                                              # ghostly tear trails
    if y == 11 and 5 <= x <= 6:
        return mul(GHOST_D, 0.55)
    return None


# ------------------------------------------------------------------ model
def build():
    m = Model("bell_keeper", seed=51, shadow=1.3, walk_speed=0.7, walk_scale=1.0)

    # ---------------------------------------------------------- skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -36, 0))
    m.part("skirt_b", "hips", pivot=(0, 2, 6), rot=(5, 0, 0))
    m.part("tabard", "hips", pivot=(0, 1, -7), rot=(-4, 0, 0))
    m.part("torso", "hips", pivot=(0, -1, 0), rot=(22, 0, 0))
    m.part("head", "torso", pivot=(0, -27, -3), rot=(-22, 0, 0))
    m.part("brim", "head", pivot=(0, -13, -5), rot=(14, 0, 0))
    m.part("hood_tip", "head", pivot=(0, -16, 1), rot=(-24, 0, 0))
    m.part("hood_tip2", "hood_tip", pivot=(0, -4, 1), rot=(-34, 0, 0))
    m.part("cape", "torso", pivot=(5, -25, 7), rot=(-14, 0, 0))
    m.part("yoke", "torso", pivot=(0, -14, 8), rot=(0, 0, -32))
    m.part("hand_bell", "yoke", pivot=(0, -33, 2.5), rot=(0, 0, 32))
    m.part("arm_r", "torso", pivot=(-12, -23, 0), rot=(-6, 0, 24))
    m.part("forearm_r", "arm_r", pivot=(0, 19, 0), rot=(-94, 0, 0))
    m.part("hand_r", "forearm_r", pivot=(0, 16, 0))
    m.part("flail", "hand_r", pivot=(0, 5, 0), rot=(64, 0, -60))
    m.part("chain", "flail", scale=(1, CHAIN_REST, 1))
    m.part("bell", "flail", pivot=(0, 4, 0), scale=(1.2, 1.2, 1.2))
    m.part("arm_l", "torso", pivot=(12, -23, 0), rot=(-14, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 19, 0), rot=(-26, 0, 0))
    m.part("hand_l", "forearm_l", pivot=(0, 16, 0))
    m.part("leg_r", "bone", pivot=(-5, -36, 0))
    m.part("shin_r", "leg_r", pivot=(0, 18, 0))
    m.part("leg_l", "bone", pivot=(5, -36, 0))
    m.part("shin_l", "leg_l", pivot=(0, 18, 0))

    # ---------------------------------------------------------- pelvis, long robe
    m.box("hips", -8, -2, -6, 16, 4, 12, {"side": lambda f_, x, y, w, h: SACK if y in (1, 2) else ROBE_D,
                                          "*": ROBE_D})                       # rope belt
    m.box("hips", -9, 2, -7, 18, 13, 14, robe(seed=1, hem=3))
    m.box("skirt_b", -9, 0, 0, 18, 34, 2, {"back": robe(seed=2, hem=5), "front": robe(ROBE_D, 3, hem=5),
                                           "*": robe(seed=2, hem=5)})

    def tabard(face, x, y, w, h):
        """Scapular with a bronze bell emblem."""
        if _side(face) and y >= h - 1 - (x % 3 == 1) * 2:
            return None
        if face == "front":
            bx, by = x - w // 2, y - 8
            if by == -3 and bx in (-1, 0):
                return BRONZE_L
            if (by in (-2, -1) and -2 <= bx <= 1) or (by in (0, 1) and -3 <= bx <= 2) or (by == 2 and -4 <= bx <= 3):
                return BRONZE if by < 2 else BRONZE_D
            if by == 3 and bx in (-1, 0):
                return BRONZE_D
            if x in (0, w - 1):
                return mul(SACK, 0.8)
        return robe((86, 82, 80), 4, patch=False)(face, x, y, w, h)
    m.box("tabard", -4, 0, -1, 8, 31, 1, tabard)
    for bx, by in ((-7, 3), (6, 5), (-3, 6)):                                  # hanging prayer scrolls
        m.box("hips", bx, by, -8, 2, 6, 1, lambda f_, x, y, w, h: (214, 200, 166) if y < 5 else (150, 40, 36))

    # ---------------------------------------------------------- legs: robe drapes over plate greaves
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -4, 0, -5, 8, 24, 10, robe(seed=10 + sx, hem=4))
        m.box(shin, -3, -2, -3, 6, 15, 6, plate(seed=12 + sx, dents=1))
        m.box(shin, -4, 13, -6, 8, 5, 10, plate(STEEL_D, seed=14 + sx, dents=1, rivets=False))  # sabaton

    # ---------------------------------------------------------- torso
    m.box("torso", -6, -10, -4, 12, 10, 9, {"front": plate(seed=20, dents=1), "*": robe(seed=21, patch=False)})
    m.box("torso", -9, -23, -5, 18, 13, 11, {"front": plate(seed=22, dents=3, trim=BRONZE_D),
                                             "*": robe(seed=23)})
    m.box("torso", -2, -20, -6, 4, 5, 1, bronze(seed=24))                      # bell boss on the breastplate
    m.box("torso", -12, -28, -7, 24, 7, 15, robe(ROBE_L, 25, hem=3))           # hunched cowl mantle
    for i in range(6):                                                         # rosary of skulls
        m.box("torso", -7 + i * 2.6, -21 + i * 1.6, -7, 2, 2, 1, (226, 216, 190) if i % 2 else (168, 120, 70))

    # broken bell-yoke beam strapped across the back, jutting above the left shoulder
    m.box("yoke", -2.5, -28, 0, 5, 42, 5, wood(1))
    m.box("yoke", -3.5, -24, -1, 7, 3, 7, plate(IRON, seed=30, dents=0))
    # a small sanctus bell still hanging from the stub, swaying behind the shoulder
    m.box("hand_bell", -0.5, 0, -0.5, 1, 4, 1, chain_link)
    m.box("hand_bell", -2, 4, -2, 4, 2, 4, bronze(seed=34, light=1.1))
    m.box("hand_bell", -3, 6, -3, 6, 3, 6, bronze(seed=35))
    m.box("yoke", -1.5, -33, 1, 3, 5, 3, wood(2))                               # splintered end
    # half cape hanging from the left shoulder
    m.box("cape", -6, 0, 0, 12, 46, 1, {"back": robe((96, 94, 90), 31, hem=9), "front": robe(ROBE_D, 32, hem=9),
                                        "*": robe(ROBE_D, 32, hem=9)})

    # ---------------------------------------------------------- head: pointed cowl, recessed ghost face
    inner = mul(ROBE_D, 0.4)
    m.box("head", -6, -16, -5, 12, 14, 11, {"front": cowl_front, "*": robe(ROBE, 40, patch=False)}, glow=cowl_glow)
    m.box("head", -7, -9, -4, 14, 9, 9, robe(ROBE, 41, patch=False))            # cowl spilling on the shoulders
    # deep brim framing the opening: two side flaps and a drooping peak
    m.box("head", -5, -13, -8, 2, 12, 3, {"left": inner, "*": robe(ROBE_L, 45, patch=False)})
    m.box("head", 3, -13, -8, 2, 12, 3, {"right": inner, "*": robe(ROBE_L, 46, patch=False)})
    m.box("brim", -5, -1, -4, 10, 3, 5, {"bottom": inner, "*": robe(ROBE_L, 44, patch=False)})
    m.box("hood_tip", -4.5, -4, -5, 9, 4, 9, robe(ROBE, 47, patch=False))
    m.box("hood_tip2", -2.5, -4, -3, 5, 4, 5, robe(ROBE, 48, patch=False))
    m.box("hood_tip2", -1, -8, -1.5, 2, 4, 2, robe(ROBE_D, 49, patch=False))

    # ---------------------------------------------------------- arms
    # right: massive dented pauldron, sleeve, vambrace wrapped in chain, gauntlet
    m.box("arm_r", -7, -5, -6, 11, 8, 12, plate(seed=50, dents=3, trim=BRONZE_D))
    m.box("arm_r", -6, -7, -4, 8, 2, 8, plate(STEEL_L, seed=51, dents=1))
    m.box("arm_r", -3, 2, -3, 6, 13, 6, robe(seed=52, patch=False))
    m.box("arm_r", -4, 13, -4, 8, 6, 8, robe(seed=53, hem=2, patch=False))
    m.box("forearm_r", -3, 0, -3, 6, 16, 6, plate(seed=54, dents=1))
    for i in range(3):
        m.box("forearm_r", -3.5, 3 + i * 4, -3.5, 7, 1, 7, chain_link)
    m.box("hand_r", -3.5, 0, -3.5, 7, 6, 7, plate(STEEL_D, seed=55, dents=0))
    # left: bare gaunt sleeve, long bony claw
    m.box("arm_l", -3, -3, -4, 7, 6, 8, robe(ROBE_L, 56, patch=False))
    m.box("arm_l", -3, 2, -3, 6, 13, 6, robe(seed=57, patch=False))
    m.box("arm_l", -4, 13, -4, 8, 6, 8, robe(seed=58, hem=2, patch=False))
    m.box("forearm_l", -2, 0, -2, 4, 16, 4, plate(STEEL_D, seed=59, dents=1))
    m.box("hand_l", -2.5, 0, -2.5, 5, 4, 5, plate(STEEL_D, seed=60, dents=0))
    for i, fx in enumerate((-2, 0, 2)):
        m.box("hand_l", fx - 0.5, 4, -1.5 + (i == 1), 1, 6 - (i == 1), 1, (210, 198, 176))
    for i in range(4):                                                         # rosary dangling from the claw
        m.box("hand_l", -0.5, 10 + i * 2, -0.5, 1, 1, 1, (168, 120, 70) if i % 2 else (226, 216, 190))

    # ---------------------------------------------------------- the bell on its chain
    for i in range(16):                    # 64 px of chain, folded to 4 px at rest, paid out by the swings
        if i % 2 == 0:
            m.box("chain", -1.5, i * 4, -0.5, 3, 5, 1, chain_link)
        else:
            m.box("chain", -0.5, i * 4, -1.5, 1, 5, 3, chain_link)
    m.box("bell", -1, -1, -3, 2, 4, 6, bronze(seed=70))                        # canon loop
    m.box("bell", -4.5, 3, -4.5, 9, 2, 9, bronze(seed=71, light=1.1))
    m.box("bell", -6.5, 5, -6.5, 13, 3, 13, bronze(seed=72, light=1.05))
    m.box("bell", -7, 8, -7, 14, 8, 14, bronze(seed=73, runes_at=1, crack=True), glow=bronze_glow(1, 73, crack=True))
    m.box("bell", -8, 16, -8, 16, 6, 16, bronze(seed=74))
    m.box("bell", -9.5, 22, -9.5, 19, 3, 19, bronze(seed=75, light=0.95))
    m.box("bell", -10.5, 25, -10.5, 21, 2, 21, {"bottom": lambda f_, x, y, w, h: VOID if 2 <= x < w - 2 and
                                                2 <= y < h - 2 else BRONZE_D, "*": bronze(seed=76, light=1.15)})
    m.box("bell", -2, 24, -2, 4, 5, 4, (54, 50, 46))                            # clapper

    _animations(m)
    return m


L = "linear"
Z = (0, 0, 0)
STRAIGHT = (94, 0, 0)        # forearm offset that straightens the bent rest arm
TAUT = (-64, 0, 60)          # flail offset that pulls the chain taut along the arm


def _pay_out(a, *keys):
    """Pay out the chain: keys are (t, extra_px[, interp]); the bell slides along the chain axis."""
    a.pos("bell", *[(k[0], (0, -k[1], 0)) + tuple(k[2:]) for k in keys])
    a.scale("chain", *[(k[0], (1, 1 + (4 + k[1]) / 64 - CHAIN_REST, 1)) + tuple(k[2:]) for k in keys])


def _taut(a, t0, t1, t_end):
    """Straight arm and taut chain from t0 to t1, back to rest at t_end."""
    a.rot("forearm_r", (0, Z), (t0, STRAIGHT), (t1, STRAIGHT), (t_end, Z))
    a.rot("flail", (0, Z), (t0, TAUT), (t1, TAUT), (t_end, Z))


def _animations(m):
    idle = m.anim("idle", 4.0)
    idle.rot("torso", (0, Z), (2.0, (3, 0, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.3, (-3, 6, 0)), (2.7, (2, -5, 0)), (4.0, Z))
    idle.rot("cape", (0, Z), (2.0, (7, 0, 2)), (4.0, Z))
    idle.rot("skirt_b", (0, Z), (2.0, (4, 0, 0)), (4.0, Z))
    idle.rot("flail", (0, Z), (1.0, (0, 0, 3)), (3.0, (0, 0, -3)), (4.0, Z))
    idle.rot("arm_l", (0, Z), (2.0, (-4, 0, 0)), (4.0, Z))
    idle.rot("hand_bell", (0, Z), (1.0, (8, 0, 6)), (2.0, (0, 0, -6)), (3.0, (-8, 0, 4)), (4.0, Z))

    walk = m.anim("walk", 2.0)
    for leg, sgn in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (22 * sgn, 0, 0)), (1.0, (-22 * sgn, 0, 0)), (2.0, (22 * sgn, 0, 0)))
    for shin, sgn in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, Z), (0.5, (28 if sgn > 0 else 0, 0, 0)), (1.0, Z),
                 (1.5, (28 if sgn < 0 else 0, 0, 0)), (2.0, Z))
    walk.rot("arm_l", (0, (-16, 0, 0)), (1.0, (16, 0, 0)), (2.0, (-16, 0, 0)))
    walk.rot("flail", (0, (-8, 0, 0)), (1.0, (8, 0, 0)), (2.0, (-8, 0, 0)))
    walk.rot("cape", (0, (10, 0, 0)), (1.0, (16, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("skirt_b", (0, (8, 0, 0)), (1.0, (12, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("hand_bell", (0, (12, 0, 0)), (1.0, (-12, 0, 0)), (2.0, (12, 0, 0)))
    walk.pos("bone", (0, Z), (0.5, (0, -1.5, 0)), (1.0, Z), (1.5, (0, -1.5, 0)), (2.0, Z))

    # toll (impact 0.8 s = 16 t): the bell lifted before the chest, the claw rakes across it
    a = m.anim("toll", 1.5)
    _toll_strikes(a, (0.8,), 1.5)

    # smash (impact 1.0 s = 20 t): swung over the head on a taut chain, crashed down in front
    a = m.anim("smash", 2.0)
    _taut(a, 0.45, 1.5, 2.0)
    a.rot("arm_r", (0, Z), (0.85, (-190, 0, -16)), (1.0, (-52, 0, -16), L), (1.5, (-48, 0, -16)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.85, (-160, 0, 10)), (1.0, (-50, 0, 10), L), (1.5, (-45, 0, 10)), (2.0, Z))
    a.rot("torso", (0, Z), (0.85, (-28, 12, 0)), (1.0, (34, 0, 0), L), (1.5, (30, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.85, (-10, 0, 0)), (1.0, (-26, 0, 0)), (1.5, (-24, 0, 0)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.85, (-10, 0, 0)), (1.0, (-30, 0, 0), L), (1.5, (-30, 0, 0)), (2.0, Z))
    a.rot("shin_r", (0, Z), (0.85, (10, 0, 0)), (1.0, (30, 0, 0), L), (1.5, (30, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (1.0, (18, 0, 0), L), (1.5, (18, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.85, (0, 2, 3)), (1.0, (0, -4, -5), L), (1.5, (0, -4, -5)), (2.0, Z))
    _pay_out(a, (0, 0), (0.85, 4), (1.0, 12, L), (1.5, 12), (2.0, 0))

    # sweep (impact 0.85 s = 17 t): the bell flung out wide and swept round from right to left
    a = m.anim("sweep", 1.6)
    _taut(a, 0.4, 1.15, 1.6)
    a.rot("arm_r", (0, Z), (0.7, (8, 0, 62)), (0.85, (-8, 0, 62), L), (1.15, (-8, 0, 58)), (1.6, Z))
    a.rot("torso", (0, Z), (0.7, (6, 62, 0)), (0.85, (8, -78, 0), L), (1.15, (8, -84, 0)), (1.6, Z))
    a.rot("bone", (0, Z), (0.7, (0, 22, 0)), (0.85, (0, -38, 0), L), (1.15, (0, -42, 0)), (1.6, Z))
    a.rot("arm_l", (0, Z), (0.7, (-20, 0, -40)), (0.85, (10, 0, -60), L), (1.6, Z))
    a.rot("cape", (0, Z), (0.7, (-10, 0, -20)), (0.85, (20, 0, 30), L), (1.6, Z))
    _pay_out(a, (0, 0), (0.7, 10), (0.85, 18, L), (1.15, 18), (1.6, 0))

    # knell (impact 0.9 s = 18 t): the bell lifted, dropped mouth-down, held while it hums
    a = m.anim("knell", 2.6)
    a.rot("arm_r", (0, Z), (0.7, (-40, 0, -6)), (0.9, (6, 0, -10), L), (2.0, (6, 0, -10)), (2.6, Z))
    a.rot("flail", (0, Z), (0.7, (40, 0, 0)), (0.9, (-6, 0, 0), L), (2.0, (-6, 0, 0)), (2.6, Z))
    a.rot("torso", (0, Z), (0.7, (-12, 0, 0)), (0.9, (16, 0, 0), L), (2.0, (16, 0, 0)), (2.6, Z))
    a.rot("head", (0, Z), (0.7, (-14, 0, 0)), (0.9, (12, 0, 0)), (2.0, (12, 0, 0)), (2.6, Z))
    a.rot("arm_l", (0, Z), (0.7, (-120, 0, 30)), (0.9, (-110, 0, 30)), (2.0, (-110, 0, 30)), (2.6, Z))
    a.rot("forearm_l", (0, Z), (0.7, (-40, 0, 0)), (2.0, (-40, 0, 0)), (2.6, Z))
    a.pos("bone", (0, Z), (0.7, (0, 1, 0)), (0.9, (0, -3, 0), L), (2.0, (0, -3, 0)), (2.6, Z))
    a.scale("bell", (0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.98, (1.1, 0.92, 1.1), L), (1.15, (0.97, 1.03, 0.97)),
            (1.35, (1.07, 0.95, 1.07)), (1.55, (0.98, 1.02, 0.98)), (1.75, (1.04, 0.97, 1.04)), (2.0, (1, 1, 1)),
            (2.6, (1, 1, 1)))

    # charge (impact 0.7 s = 14 t): crouched, bell dragged behind, then a lunging uppercut
    a = m.anim("charge", 1.5)
    _taut(a, 0.35, 1.05, 1.5)
    a.rot("arm_r", (0, Z), (0.55, (52, 0, 6)), (0.7, (-150, 0, -6), L), (1.05, (-140, 0, -6)), (1.5, Z))
    a.rot("torso", (0, Z), (0.55, (30, 18, 0)), (0.7, (-14, -10, 0), L), (1.05, (-10, -8, 0)), (1.5, Z))
    a.rot("head", (0, Z), (0.55, (-26, 0, 0)), (0.7, (8, 0, 0)), (1.5, Z))
    a.rot("arm_l", (0, Z), (0.55, (30, 0, -30)), (0.7, (-40, 0, -20), L), (1.5, Z))
    a.rot("leg_r", (0, Z), (0.55, (-34, 0, 0)), (0.7, (-40, 0, 0), L), (1.05, (-30, 0, 0)), (1.5, Z))
    a.rot("shin_r", (0, Z), (0.55, (40, 0, 0)), (0.7, (20, 0, 0)), (1.5, Z))
    a.rot("leg_l", (0, Z), (0.55, (24, 0, 0)), (0.7, (30, 0, 0), L), (1.5, Z))
    a.pos("bone", (0, Z), (0.55, (0, -5, 4)), (0.7, (0, 0, -10), L), (1.05, (0, 0, -10)), (1.5, Z))
    _pay_out(a, (0, 0), (0.55, 8), (0.7, 10, L), (1.05, 10), (1.5, 0))

    # frenzy (hits at 0.55, 0.95 and 1.5 s = 11, 19, 30 t): sweep, backhand, overhead crash
    a = m.anim("frenzy", 2.3)
    _taut(a, 0.3, 1.85, 2.3)
    a.rot("arm_r", (0, Z), (0.4, (6, 0, 60)), (0.55, (-8, 0, 62), L), (0.8, (-14, 0, 60)), (0.95, (-6, 0, 60), L),
          (1.3, (-192, 0, -16)), (1.5, (-52, 0, -16), L), (1.85, (-48, 0, -16)), (2.3, Z))
    a.rot("torso", (0, Z), (0.4, (6, 58, 0)), (0.55, (8, -70, 0), L), (0.8, (8, -80, 0)), (0.95, (8, 55, 0), L),
          (1.3, (-26, 10, 0)), (1.5, (34, 0, 0), L), (1.85, (30, 0, 0)), (2.3, Z))
    a.rot("bone", (0, Z), (0.4, (0, 18, 0)), (0.55, (0, -30, 0), L), (0.8, (0, -34, 0)), (0.95, (0, 24, 0), L),
          (1.3, Z), (1.85, Z), (2.3, Z))
    a.rot("arm_l", (0, Z), (0.4, (-20, 0, -40)), (0.55, (10, 0, -60), L), (0.95, (-30, 0, -20), L),
          (1.3, (-160, 0, 10)), (1.5, (-50, 0, 10), L), (1.85, (-45, 0, 10)), (2.3, Z))
    a.rot("cape", (0, Z), (0.55, (20, 0, 30), L), (0.95, (10, 0, -25), L), (1.5, (30, 0, 0), L), (2.3, Z))
    a.pos("bone", (0, Z), (1.3, (0, 2, 2)), (1.5, (0, -4, -6), L), (1.85, (0, -4, -6)), (2.3, Z))
    _pay_out(a, (0, 0), (0.4, 14), (0.55, 18, L), (0.95, 18), (1.3, 6), (1.5, 14, L), (1.85, 14), (2.3, 0))

    # triple toll (strikes at 0.8, 1.25, 1.7 s = 16, 25, 34 t)
    a = m.anim("triple_toll", 2.4)
    _toll_strikes(a, (0.8, 1.25, 1.7), 2.4)

    # requiem (impact 0.8 s = 16 t): kneels, plants the bell, the claw raised to call the dead monks
    a = m.anim("requiem", 2.2)
    a.pos("bone", (0, Z), (0.6, (0, -9, 2)), (1.7, (0, -9, 2)), (2.2, Z))
    a.rot("leg_r", (0, Z), (0.6, (-70, 0, 0)), (1.7, (-70, 0, 0)), (2.2, Z))
    a.rot("shin_r", (0, Z), (0.6, (80, 0, 0)), (1.7, (80, 0, 0)), (2.2, Z))
    a.rot("leg_l", (0, Z), (0.6, (16, 0, 0)), (1.7, (16, 0, 0)), (2.2, Z))
    a.rot("shin_l", (0, Z), (0.6, (66, 0, 0)), (1.7, (66, 0, 0)), (2.2, Z))
    a.rot("torso", (0, Z), (0.6, (-6, 0, 0)), (0.8, (-14, 0, 0)), (1.7, (-14, 0, 0)), (2.2, Z))
    a.rot("head", (0, Z), (0.6, (-10, 0, 0)), (0.8, (-34, 0, 0)), (1.7, (-34, 0, 0)), (2.2, Z))
    a.rot("arm_l", (0, Z), (0.6, (-100, 0, -10)), (0.8, (-172, 0, -12)), (1.7, (-172, 0, -12)), (2.2, Z))
    a.rot("forearm_l", (0, Z), (0.8, (-10, 0, 0)), (1.7, (-10, 0, 0)), (2.2, Z))
    a.rot("arm_r", (0, Z), (0.6, (-12, 0, 4)), (1.7, (-12, 0, 4)), (2.2, Z))
    a.rot("flail", (0, Z), (0.6, (-6, 0, -56)), (1.7, (-6, 0, -56)), (2.2, Z))

    # bell fall (impact 1.1 s = 22 t): the chain paid out, the bell whirled high and brought down far away
    a = m.anim("bell_fall", 2.4)
    _taut(a, 0.4, 1.7, 2.4)
    a.rot("arm_r", (0, Z), (0.5, (-120, 0, 0)), (0.95, (-178, 0, -10)), (1.1, (-46, 0, -12), L), (1.7, (-42, 0, -12)),
          (2.4, Z))
    a.rot("arm_l", (0, Z), (0.95, (-60, 0, -50)), (1.1, (-30, 0, -30), L), (2.4, Z))
    a.rot("torso", (0, Z), (0.95, (-24, 0, 0)), (1.1, (30, 0, 0), L), (1.7, (28, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.95, (-24, 0, 0)), (1.1, (-20, 0, 0)), (1.7, (-20, 0, 0)), (2.4, Z))
    a.rot("leg_r", (0, Z), (1.1, (-26, 0, 0), L), (1.7, (-26, 0, 0)), (2.4, Z))
    a.rot("shin_r", (0, Z), (1.1, (26, 0, 0), L), (1.7, (26, 0, 0)), (2.4, Z))
    a.pos("bone", (0, Z), (0.95, (0, 2, 2)), (1.1, (0, -3, -4), L), (1.7, (0, -3, -4)), (2.4, Z))
    _pay_out(a, (0, 0), (0.5, 20), (0.95, 40), (1.1, 60, L), (1.7, 60), (2.4, 0))

    # roar (phase two): the cowl thrown back, the bell raised aloft on a taut chain
    a = m.anim("roar", 2.4)
    _taut(a, 0.5, 1.9, 2.4)
    a.rot("arm_r", (0, Z), (0.5, (-150, 0, 30)), (1.9, (-150, 0, 30)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.5, (-40, 0, -70)), (1.9, (-40, 0, -70)), (2.4, Z))
    a.rot("torso", (0, Z), (0.5, (-26, 0, 0)), (1.9, (-26, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, Z))
    a.scale("bell", (0, (1, 1, 1)), (0.6, (1, 1, 1)), (0.7, (1.1, 0.9, 1.1), L), (0.9, (0.96, 1.04, 0.96)),
            (1.2, (1.05, 0.96, 1.05)), (1.6, (1, 1, 1)), (2.4, (1, 1, 1)))

    # stagger: posture broken, falls to one knee, the bell slumps to the ground
    a = m.anim("stagger", 2.4)
    a.pos("bone", (0, Z), (0.3, (0, -9, 2)), (1.9, (0, -9, 2)), (2.4, Z))
    a.rot("leg_r", (0, Z), (0.3, (-66, 0, 0)), (1.9, (-66, 0, 0)), (2.4, Z))
    a.rot("shin_r", (0, Z), (0.3, (76, 0, 0)), (1.9, (76, 0, 0)), (2.4, Z))
    a.rot("leg_l", (0, Z), (0.3, (14, 0, 0)), (1.9, (14, 0, 0)), (2.4, Z))
    a.rot("shin_l", (0, Z), (0.3, (64, 0, 0)), (1.9, (64, 0, 0)), (2.4, Z))
    a.rot("torso", (0, Z), (0.3, (24, 0, 0)), (1.9, (24, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.3, (18, 0, 0)), (1.9, (18, 0, 0)), (2.4, Z))
    a.rot("arm_r", (0, Z), (0.3, (-44, 0, 18)), (1.9, (-44, 0, 18)), (2.4, Z))
    a.rot("flail", (0, Z), (0.3, (40, 0, -8)), (1.9, (40, 0, -8)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.3, (-30, 0, -10)), (1.9, (-30, 0, -10)), (2.4, Z))


def _toll_strikes(a, hits, length):
    """Bell raised before the chest; the left claw rakes across it at each hit time."""
    up, end = hits[0] - 0.2, hits[-1] + 0.3
    a.rot("arm_r", (0, Z), (up, (-40, 0, -16)), (end, (-40, 0, -16)), (length, Z))
    a.rot("forearm_r", (0, Z), (up, (12, 0, 0)), (end, (12, 0, 0)), (length, Z))
    a.rot("flail", (0, Z), (up, (30, 0, 0)), (end, (30, 0, 0)), (length, Z))
    a.rot("torso", (0, Z), (up, (-8, 22, 0)), (end, (-4, 4, 0)), (length, Z))
    a.rot("head", (0, Z), (up, (12, 10, 0)), (end, (12, 0, 0)), (length, Z))
    keys_l, keys_f, keys_b = [(0, Z), (up, (-50, 0, -60))], [(0, Z), (up, (-50, 0, 0))], \
        [(0, (1, 1, 1)), (hits[0] - 0.02, (1, 1, 1))]
    for i, t in enumerate(hits):
        keys_l.append((t, (-80, 0, 34), L))
        keys_f.append((t, (-8, 0, 0), L))
        keys_b += [(t + 0.04, (1.12, 0.9, 1.12), L), (t + 0.16, (0.96, 1.04, 0.96))]
        if i + 1 < len(hits):
            back = (t + hits[i + 1]) / 2 + 0.05
            keys_l.append((back, (-55, 0, -55)))
            keys_f.append((back, (-50, 0, 0)))
            keys_b.append((hits[i + 1] - 0.02, (1, 1, 1)))
    keys_l += [(end, (-70, 0, 20)), (length, Z)]
    keys_f += [(end, (-20, 0, 0)), (length, Z)]
    keys_b += [(end, (1, 1, 1)), (length, (1, 1, 1))]
    a.rot("arm_l", *keys_l)
    a.rot("forearm_l", *keys_f)
    a.scale("bell", *keys_b)
