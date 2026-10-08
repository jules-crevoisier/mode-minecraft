"""The Lock-Master (Le Maître des écluses): warden of the Great Aqueduct's cistern, about 5.2 blocks tall.

Silhouette idea: a hulking hydraulic warden, a riveted brass boiler of a body on short piston legs, the head sunk low
between the shoulders: a round diving helm with one glowing porthole, a spoked valve wheel bolted on top for a crown.
Strong asymmetry: in the LEFT hand a whole sluice gate for a shield (a tall iron-framed panel of wet oak planks with
iron straps, a valve wheel in its middle and rack teeth down its edge); in the RIGHT a pressure-lance longer than he is
tall (a brass vamplate over the grip, a copper hose coiled down the shaft, a nozzle for a point that glows with the
pressure behind it). On his back two banded copper tanks green with verdigris, their sight glasses glowing with
pressurised water; a big valve wheel on the right pauldron, a stack of plates on the left; a pressure gauge and a
grille of glowing vents on the boiler. Everything is wet: verdigris streaks under the rivets, water stains on the oak.
"""
import functools
import math

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

BRASS = (192, 150, 68)
BRASS_L = (240, 206, 122)
BRASS_D = (122, 88, 38)
COP = (176, 104, 58)
COP_D = (112, 62, 34)
VERD = (78, 162, 142)
VERD_L = (128, 206, 184)
VERD_D = (46, 106, 94)
IRON = (62, 60, 64)
IRON_L = (106, 102, 108)
IRON_D = (34, 32, 36)
OAK = (92, 66, 42)
OAK_L = (124, 92, 60)
OAK_D = (58, 40, 26)
WATER = (70, 196, 236)
WATER_L = (196, 246, 255)
WATER_D = (34, 120, 170)
GLASS = (40, 70, 84)


# ---------------------------------------------------------------- paint
def _verdigris(c, x, y, seed, amount):
    """Green streaks running down from rivet rows and seams: the wet brass of a cistern."""
    if amount and B.n(x, 0, seed + 11) < amount and B.n(x, y // 3, seed + 12) < 0.65:
        return mix(c, VERD if B.n(x, y, seed + 13) < 0.6 else VERD_D, 0.55)
    return c


def brass(seed=0, verd=0.12, rivets=4, base=BRASS):
    """Riveted brass plate: lit top rim, dark rim, rivet rows every ``rivets`` texels, verdigris streaks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(base, 0.62)
        if face == "top":
            c = mul(base, 1.1 + (B.n(x, y, seed) - 0.5) * 0.08)
            return mix(c, BRASS_L, 0.4) if x in (0, w - 1) or y in (0, h - 1) else c
        if w > 2 and h > 2:
            if y == 0:
                return BRASS_L
            if x in (0, w - 1) or y == h - 1:
                return mul(base, 0.6)
        if rivets and w > 4 and h > 4 and y in (1, h - 2) and x % rivets == 1:
            return mix(base, (255, 240, 200), 0.5)
        c = mul(base, 1.06 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        if B.n(x // 2, y // 2, seed + 5) < 0.06:
            c = mul(c, 0.82)                                    # dents
        return _verdigris(c, x, y, seed, verd)
    return f


def boiler(seed=0, every=7):
    """The boiler body: brass hoops every ``every`` texels with rivet heads on them, streaked green below them."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return brass(seed)(face, x, y, w, h)
        if y % every == 0:
            return BRASS_L if x % 3 == 1 else mul(BRASS, 0.78)
        if y % every == 1:
            return mul(BRASS, 0.7)
        c = mul(BRASS, 1.08 - 0.2 * (y % every) / every + (B.n(x, y, seed) - 0.5) * 0.07)
        if face in ("left", "right") or x in (0, w - 1):
            c = mul(c, 0.9)
        return _verdigris(c, x, y, seed, 0.16)
    return f


def iron(seed=0, rivets=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        if face == "top":
            return IRON_L if x in (0, w - 1) or y in (0, h - 1) else IRON
        if w > 2 and h > 2 and y == 0:
            return IRON_L
        if rivets and w > 3 and h > 3 and y in (1, h - 2) and x % rivets == 1:
            return BRASS
        return mul(IRON, 1.05 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
    return f


def copper(seed=0, every=5):
    """A banded copper tank, heavy verdigris."""
    def f(face, x, y, w, h):
        if face == "top":
            return mix(COP, VERD, 0.4)
        if face == "bottom":
            return COP_D
        if y % every == 0:
            return mix(COP_D, BRASS_L, 0.4) if x % 3 == 1 else COP_D
        c = mul(COP, 1.1 - 0.2 * (y % every) / every + (B.n(x, y, seed) - 0.5) * 0.08)
        if B.n(x, y // 2, seed + 4) < 0.35 or B.n(x // 2, y // 3, seed + 6) < 0.25:
            c = mix(c, VERD if B.n(x, y, seed) < 0.5 else VERD_L, 0.6)
        return c
    return f


def sight(face, x, y, w, h):
    """A sight glass: a dark glass strip with the water level glowing in its lower part."""
    if face != "front" and face != "back":
        return BRASS_D
    if y > h * 0.35:
        return WATER if (x + y) % 4 else WATER_L
    return GLASS


def sight_glow(face, x, y, w, h):
    if face not in ("front", "back") or y <= h * 0.35:
        return None
    return WATER_L if y == int(h * 0.35) + 1 else WATER


def oak(seed=0):
    """The gate's wet oak planks: vertical boards with dark seams, water stains rising from the bottom."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return OAK_D
        if x % 4 == 3:
            return OAK_D
        c = mul(OAK, 1.06 + (B.n(x // 4, 0, seed) - 0.5) * 0.18 + (B.n(x, y, seed) - 0.5) * 0.1)
        if B.n(x, y // 2, seed + 3) < 0.08:
            c = OAK_L                                           # grain
        wet = y / max(1, h)
        if wet > 0.6:
            c = mix(c, (40, 52, 46), (wet - 0.6) * 1.5)         # the waterline
        return c
    return f


def strap(seed=0):
    """Iron straps riveted across the gate."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        if face in ("front", "back") and h >= 1 and w > 3 and x % 4 == 2:
            return BRASS
        return mul(IRON, 1.05 + (B.n(x, y, seed) - 0.5) * 0.15)
    return f


def rack(face, x, y, w, h):
    """The gate's rack: brass teeth down its edge."""
    if face in ("top", "bottom"):
        return BRASS_D
    return BRASS_L if y % 3 == 0 else (BRASS if y % 3 == 1 else BRASS_D)


@functools.lru_cache(maxsize=None)
def _porthole(w, h):
    return (w - 1) / 2, (h - 1) / 2, min(w, h) / 2


def porthole(face, x, y, w, h):
    """The helm's porthole: thick brass rim, three cage bars, glowing water-light behind the glass."""
    if face != "front":
        return brass(71)(face, x, y, w, h)
    cx, cy, outer = _porthole(w, h)
    r = math.hypot(x - cx, y - cy)
    if r > outer - 0.2:
        return mul(BRASS, 0.7)
    if r > outer - 1.3:
        return BRASS_L if y < cy else BRASS
    if x in (int(cx) - 2, int(cx) + 2) or y == int(cy):
        return IRON_D                                           # the cage
    return WATER_L if r < 1.2 else WATER


def porthole_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy, outer = _porthole(w, h)
    r = math.hypot(x - cx, y - cy)
    if r > outer - 1.3 or x in (int(cx) - 2, int(cx) + 2) or y == int(cy):
        return None
    return WATER_L if r < 1.6 else WATER


def helm(seed=0):
    """The diving helm: brass with a raised collar band and bolts; the porthole is its own cube."""
    def f(face, x, y, w, h):
        if face == "top":
            return mul(BRASS, 1.12)
        if face == "bottom":
            return BRASS_D
        if y >= h - 2:
            return BRASS_L if y == h - 2 and x % 3 == 1 else mul(BRASS, 0.7)    # the breastplate collar
        if y == 2:
            return mul(BRASS, 0.78)                                         # the seam under the crown
        c = mul(BRASS, 1.12 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if face in ("left", "right") and 4 <= y <= 7 and 3 <= x <= w - 4:
            c = mul(c, 0.85)                                                # side windows (blind plates)
        return _verdigris(c, x, y, seed, 0.1)
    return f


def vents(face, x, y, w, h):
    return B.grate(frame=IRON, slot=(20, 40, 50), fire=WATER_D)(face, x, y, w, h)


def vents_glow(face, x, y, w, h):
    return B.grate_glow(fire=WATER, hot=WATER_L)(face, x, y, w, h)


def nozzle_glow(face, x, y, w, h):
    return WATER_L if face == "front" else WATER


def glow(c):
    return lambda face, x, y, w, h: c


# ---------------------------------------------------------------- build
def build():
    m = Model("lock_master", seed=211, shadow=2.2, walk_speed=0.6, walk_scale=0.8)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -30, 0))
    m.part("skirt", "pelvis", pivot=(0, 3, -8), rot=(-4, 0, 0))
    m.part("skirt_b", "pelvis", pivot=(0, 3, 8), rot=(5, 0, 0))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0))
    m.part("head", "chest", pivot=(0, -27, -3))
    m.part("crown", "head", pivot=(0, -16, 0))
    m.part("tanks", "chest", pivot=(0, -13, 10))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(8 * sx, 2, 0), rot=(0, 0, -4 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 15, 0), rot=(0, 0, 4 * sx))
    m.part("arm_r", "chest", pivot=(-19, -23, 0), rot=(6, 0, 14))
    m.part("wheel", "arm_r", pivot=(-9, -3, 0))
    m.part("fore_r", "arm_r", pivot=(-0.5, 12, 0), rot=(-62, 0, -14))
    m.part("lance", "fore_r", pivot=(0, 12, 0), rot=(50, 0, 0))
    m.part("arm_l", "chest", pivot=(19, -23, 0), rot=(4, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0.5, 12, 0), rot=(-40, 0, 10))
    m.part("shield", "fore_l", pivot=(1, 7, -6), rot=(40, -8, 0))

    # ---- legs: piston thighs with hydraulic rams down the front, heavy iron boots
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        s = 3 if sx < 0 else 4
        m.box(th, -5, -1, -5, 10, 16, 10, brass(s, rivets=3))
        m.box(th, -5.5, 1, -5.5, 11, 3, 11, iron(s + 1, rivets=3))                    # hoop
        m.box(th, -1.5, 3, -7, 3, 12, 2, B.rod(IRON_L, s))                             # the ram's cylinder
        m.box(sh, -1, -2, -7, 2, 6, 1, B.rod((176, 176, 188), s + 2))                  # ...its polished rod
        m.box(sh, -6, -2, -6, 12, 5, 12, iron(s + 3, rivets=3))                        # knee housing
        m.box(sh, -4.5, 2, -4.5, 9, 7, 9, brass(s + 4, rivets=0))
        m.box(sh, -6.5, 8, -9, 13, 5, 15, iron(s + 5, rivets=3))                       # boot
        m.box(sh, -5.5, 9, -10, 11, 3, 1, BRASS_D)                                     # toe cap

    # ---- hips: an iron housing, brass skirt plates front and back
    m.box("pelvis", -12, -4, -8, 24, 8, 16, iron(10, rivets=4))
    m.box("skirt", -11, 0, -1, 10, 10, 1, brass(11, rivets=3))
    m.box("skirt", 1, 0, -1, 10, 10, 1, brass(12, rivets=3))
    m.box("skirt_b", -11, 0, 0, 22, 9, 1, brass(13, rivets=3))
    m.box("waist", -11, -6, -7, 22, 6, 14, B.bands(IRON, IRON_L, every=2, seed=14))

    # ---- the boiler: hooped brass, a yoke of iron over the shoulders, a gauge and the vents
    m.box("chest", -15, -28, -10, 30, 28, 20, boiler(20))
    m.box("chest", -17, -30, -9, 34, 5, 18, iron(21, rivets=4))                       # the yoke
    m.box("chest", -12, -26, -11, 24, 9, 1, brass(22, rivets=3))                       # breast plate
    m.box("chest", 3, -24, -12, 7, 7, 1, B.gauge(BRASS, (190, 30, 30)))                # the gauge
    m.box("chest", -10, -14, -11, 13, 8, 1, vents, glow=vents_glow)
    m.box("chest", -14, -6, -11, 28, 3, 1, iron(23, rivets=3))                         # belly band
    m.box("chest", -15.5, -16, -6, 1, 10, 12, brass(24))                               # side valve plates
    m.box("chest", 14.5, -16, -6, 1, 10, 12, brass(25))
    m.box("chest", -3, -26, 10, 6, 22, 1, iron(26, rivets=3))                          # spine plate

    # ---- the tanks on his back, their sight glasses, pipes over the right shoulder
    for x0, s in ((-13, 30), (3, 31)):
        m.box("tanks", x0, -14, 0, 10, 26, 9, copper(s))
        m.box("tanks", x0 + 1, -16, 1, 8, 2, 7, BRASS_D)                               # caps
        m.box("tanks", x0 + 2, -18, 3, 4, 2, 3, B.rod(IRON_L, s))                      # valves
        m.box("tanks", x0 + 3, -9, 9, 4, 16, 1, sight, glow=sight_glow)
    m.box("tanks", -10, -18, 4, 2, 2, 2, BRASS)
    m.box("tanks", -16, -20, 4, 9, 2, 2, B.rod(COP, 33))                               # the hose to the arm
    m.box("tanks", -18, -20, -2, 2, 2, 7, B.rod(COP, 34))

    # ---- head: the diving helm sunk between the shoulders, porthole, the valve-wheel crown
    m.box("head", -7, -13, -7, 14, 13, 14, helm(40))
    m.box("head", -4.5, -10.5, -8, 9, 9, 1, porthole, glow=porthole_glow)
    m.box("head", -8, -2, -8, 16, 2, 16, iron(41, rivets=3))                           # collar
    for bx, bz in ((-7.5, -4), (6.5, -4), (-7.5, 3), (6.5, 3)):
        m.box("head", bx, -8, bz, 1, 2, 1, BRASS_L)                                    # bolts
    m.box("head", -6, -15, -6, 12, 2, 12, helm(43))                                    # the dome
    m.box("head", -7.5, -11, -6, 1, 9, 12, helm(44))                                   # rounded flanks
    m.box("head", 6.5, -11, -6, 1, 9, 12, helm(45))
    m.box("head", -6, -11, 6.5, 12, 9, 1, helm(46))
    m.box("head", -1.5, -17, -1.5, 3, 2, 3, B.rod(IRON_L, 42))                         # the stem
    m.box("crown", -6, -1, -6, 12, 1, 12, B.cog(BRASS, teeth=8, hub=0.2, spokes=4, faces=("top", "bottom")))
    m.box("crown", -1, -2, -1, 2, 1, 2, BRASS_L)

    # ---- right arm: the valve-wheel pauldron, plated arm, gauntlet, and the pressure-lance
    m.box("arm_r", -8, -6, -8, 13, 7, 16, brass(50, rivets=3))
    m.box("arm_r", -7, -8, -6, 10, 2, 12, brass(51, rivets=0))
    m.box("wheel", -1, -7, -7, 1, 14, 14, B.cog(BRASS_L, teeth=8, hub=0.2, spokes=6, faces=("left", "right")))
    m.box("wheel", 0, -1, -1, 1, 2, 2, IRON)
    m.box("arm_r", -4.5, 0, -4.5, 9, 12, 9, iron(52, rivets=3))
    m.box("arm_r", -5, 4, -5, 10, 3, 10, BRASS_D)
    m.box("fore_r", -5, 0, -5, 10, 9, 10, brass(53, rivets=3))
    m.box("fore_r", -5.5, 8, -5.5, 11, 7, 11, iron(54, rivets=3))                      # gauntlet
    ln = "lance"
    m.box(ln, -1.5, -1.5, -58, 3, 3, 72, iron(60))                                     # the shaft
    m.box(ln, -2.5, -2.5, 10, 5, 5, 6, copper(61))                                     # counterweight tank
    m.box(ln, -5, -5, -5, 10, 10, 1, brass(62, rivets=0))                              # vamplate
    m.box(ln, -4, -4, -7, 8, 8, 2, brass(63, rivets=0))
    m.box(ln, -3, -3, -10, 6, 6, 3, brass(64, rivets=0))
    m.box(ln, -2, -2, -14, 4, 4, 4, BRASS_D)
    for z in range(-50, -14, 6):                                                       # the coiled hose
        m.box(ln, -2, -2, z, 4, 4, 2, COP)
    m.box(ln, 1.5, -3, -20, 2, 2, 2, B.gauge(BRASS, (190, 30, 30)))
    m.box(ln, -2.5, -2.5, -62, 5, 5, 4, brass(65, rivets=0))                           # the nozzle
    m.box(ln, -2, -2, -63, 4, 4, 1, WATER, glow=nozzle_glow)
    m.box(ln, -1, -1, -70, 2, 2, 7, B.rod((186, 186, 196), 66))                        # the point

    # ---- left arm: layered pauldron, arm, gauntlet, and the sluice-gate shield
    m.box("arm_l", -5, -6, -8, 13, 6, 16, brass(70, rivets=3))
    m.box("arm_l", -4, -9, -6, 11, 3, 12, brass(71, rivets=3))
    m.box("arm_l", -3, -11, -4, 9, 2, 8, BRASS_D)
    m.box("arm_l", -4.5, 0, -4.5, 9, 12, 9, iron(72, rivets=3))
    m.box("fore_l", -5, 0, -5, 10, 9, 10, brass(73, rivets=3))
    m.box("fore_l", -5.5, 8, -5.5, 11, 6, 11, iron(74, rivets=3))
    sh = "shield"
    m.box(sh, -12, -22, -2, 24, 40, 2, oak(80))                                        # the planks
    m.box(sh, -13, -23, -3, 26, 2, 4, iron(81, rivets=3))                              # frame
    m.box(sh, -13, 17, -3, 26, 2, 4, iron(82, rivets=3))
    m.box(sh, -13, -21, -3, 2, 38, 4, iron(83))
    m.box(sh, 11, -21, -3, 2, 38, 4, iron(84))
    m.box(sh, -14, -20, -2, 1, 36, 2, rack)                                            # rack teeth
    for y in (-14, 8):
        m.box(sh, -11, y, -2.5, 22, 2, 1, strap(85 + y))                               # straps
    m.box(sh, -6, -9, -3.5, 12, 12, 1, B.cog(BRASS, teeth=8, hub=0.2, spokes=4))       # the valve wheel
    m.box(sh, -1, -4, -4, 2, 2, 1, IRON)
    m.box(sh, -3, 19, -2, 6, 2, 2, BRASS_D)                                            # the lifting lug

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.9, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (0, 8, 0)), (2.4, (0, 8, 0)), (3.3, (0, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("crown", (0, (0, 0, 0)), (4.0, (0, 90, 0)))
    idle.rot("wheel", (0, (0, 0, 0)), (2.0, (20, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (2, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("skirt", (0, (0, 0, 0)), (2.0, (-2, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("thigh_r", (0, (18, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("thigh_l", (0, (-18, 0, 0)), (1.0, (18, 0, 0)), (2.0, (-18, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (22, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (22, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 5, 2)), (1.0, (0, -5, -2)), (2.0, (0, 5, 2)))
    walk.rot("arm_l", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("skirt", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))

    # thrust: the lance drawn back along his right side, his weight on the back foot (0.8 s = 16 ticks), then driven
    # straight ahead at full reach (the arm and the lance in one line), a lunge step with the left foot
    a = m.anim("thrust", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (34, 0, 0)), (0.8, (38, 0, 0)), (0.9, (-58, 0, 0), "linear"),
          (1.15, (-56, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.9, (52, 0, 0), "linear"), (1.15, (50, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (0.9, (12, 0, 0), "linear"), (1.15, (12, 0, 0)), (1.7, (0, 0, 0)))
    a.pos("lance", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (0.9, (0, 0, -8), "linear"), (1.15, (0, 0, -8)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, 26, 0)), (0.9, (14, -22, 0), "linear"), (1.15, (12, -20, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-20, 0, -10)), (0.9, (10, 0, -6), "linear"), (1.7, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (6, 0, 0)), (0.9, (-34, 0, 0), "linear"), (1.15, (-34, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.9, (26, 0, 0), "linear"), (1.15, (26, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.9, (16, 0, 0), "linear"), (1.15, (16, 0, 0)), (1.7, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, 0, 2)), (0.9, (0, -2, -3), "linear"), (1.15, (0, -2, -3)), (1.7, (0, 0, 0)))

    # skewer (phase 2): three thrusts (0.7 s = 14 ticks, then 1.2 and 1.7 s), each drawn back half way
    a = m.anim("skewer", 2.6)
    keys_a, keys_f, keys_c, keys_p = [], [], [], []
    for i, t in enumerate((0.7, 1.2, 1.7)):
        back = t - (0.12 if i else 0.0)
        keys_a += [(t - 0.1 if i else 0.6, (34, 0, 0)), (t, (-58, 0, 0), "linear"), (t + 0.18, (-56, 0, 0))]
        keys_f += [(t - 0.1 if i else 0.6, (-10, 0, 0)), (t, (52, 0, 0), "linear"), (t + 0.18, (50, 0, 0))]
        keys_c += [(t - 0.1 if i else 0.6, (-4, 24, 0)), (t, (12, -20, 0), "linear"), (t + 0.18, (10, -18, 0))]
        keys_p += [(t - 0.1 if i else 0.6, (0, 0, 0)), (t, (0, 0, -8), "linear"), (t + 0.18, (0, 0, -8))]
        del back
    a.rot("arm_r", (0, (0, 0, 0)), *keys_a, (2.6, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), *keys_f, (2.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), *keys_c, (2.6, (0, 0, 0)))
    a.pos("lance", (0, (0, 0, 0)), *keys_p, (2.6, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (1.9, (10, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.6, (4, 0, 0)), (0.7, (-30, 0, 0), "linear"), (1.9, (-34, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.7, (24, 0, 0), "linear"), (1.9, (26, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-24, 0, -10)), (1.9, (-20, 0, -10)), (2.6, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.7, (0, -2, -2), "linear"), (1.9, (0, -2, -4)), (2.6, (0, 0, 0)))

    # spin: shield tucked, lance swung back across his left side (0.9 s = 18 ticks), then he pivots on his heel and
    # the lance sweeps all the way round at knee height
    a = m.anim("spin", 1.9)
    a.rot("bone", (0, (0, 0, 0)), (0.9, (0, 40, 0)), (1.1, (0, -320, 0), "linear"), (1.25, (0, -330, 0)),
          (1.9, (0, -360, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-10, 0, 40)), (0.9, (-10, 0, 44)), (1.1, (-14, 0, 52), "linear"),
          (1.25, (-14, 0, 52)), (1.9, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.25, (20, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (10, -30, 0)), (1.1, (8, 30, 0), "linear"), (1.25, (6, 26, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-30, 0, -6)), (1.25, (-30, 0, -6)), (1.9, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, -3, 0)), (1.25, (0, -3, 0)), (1.9, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.9, (-20, 0, 8 * sx)), (1.25, (-20, 0, 8 * sx)), (1.9, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.9, (24, 0, 0)), (1.25, (24, 0, 0)), (1.9, (0, 0, 0)))

    # bash: the sluice gate raised square in front of him, he leans into it and walks behind it (1.2 s = 24 ticks:
    # frontal hits are blocked), then the shoulder drives the gate forward in a rush
    a = m.anim("bash", 2.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-50, 24, 0)), (1.2, (-52, 26, 0)), (1.3, (-70, 14, 0), "linear"),
          (1.6, (-70, 14, 0)), (2.4, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.4, (-6, 0, 0)), (1.2, (-6, 0, 0)), (1.3, (6, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.rot("shield", (0, (0, 0, 0)), (0.4, (6, 14, 0)), (1.6, (6, 14, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.4, (12, -20, 0)), (1.2, (14, -22, 0)), (1.3, (24, -14, 0), "linear"),
          (1.6, (22, -14, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (24, 0, 10)), (1.6, (24, 0, 10)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-12, 18, 0)), (1.6, (-12, 18, 0)), (2.4, (0, 0, 0)))
    step = [(0.4 + 0.2 * i, ((-16 if i % 2 else 10), 0, 0)) for i in range(4)]
    a.rot("thigh_l", (0, (0, 0, 0)), *step, (1.2, (-24, 0, 0)), (1.3, (-40, 0, 0), "linear"), (1.6, (-40, 0, 0)),
          (2.4, (0, 0, 0)))
    step = [(0.4 + 0.2 * i, ((10 if i % 2 else -16), 0, 0)) for i in range(4)]
    a.rot("thigh_r", (0, (0, 0, 0)), *step, (1.2, (14, 0, 0)), (1.3, (24, 0, 0), "linear"), (1.6, (24, 0, 0)),
          (2.4, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.2, (10, 0, 0)), (1.3, (30, 0, 0), "linear"), (1.6, (30, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -2, 0)), (1.2, (0, -2, 0)), (1.3, (0, -3, -3), "linear"),
          (1.6, (0, -3, -3)), (2.4, (0, 0, 0)))

    # jets: feet planted wide, the lance levelled at the hip and braced under the arm (1.0 s = 20 ticks), then the
    # nozzle opens: he holds the pose while the whole body turns with the jet (the entity turns), then lowers it
    a = m.anim("jets", 3.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-12, 0, 6)), (1.0, (-14, 0, 6)), (1.05, (-8, 0, 6), "linear"),
          (3.0, (-10, 0, 6)), (3.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (-18, 0, 0)), (1.0, (-20, 0, 0)), (3.0, (-20, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.8, (36, 0, 0)), (1.0, (38, 0, 0)), (3.0, (38, 0, 0)), (3.8, (0, 0, 0)))
    a.pos("lance", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.05, (0, 0, 3), "linear"), (1.2, (0, 0, 1)), (3.0, (0, 0, 1)),
          (3.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-36, 0, -12)), (3.0, (-36, 0, -12)), (3.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (6, 10, 0)), (1.05, (-4, 10, 0), "linear"), (3.0, (-2, 10, 0)), (3.8, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, -3, 0)), (3.0, (0, -3, 0)), (3.8, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.8, (-14 * sx, 0, 14 * sx)), (3.0, (-14 * sx, 0, 14 * sx)),
              (3.8, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.8, (16, 0, -6 * sx)), (3.0, (16, 0, -6 * sx)), (3.8, (0, 0, 0)))

    # sluice: the lance raised high, point to the vault, the shield lifted (1.0 s = 20 ticks), then the butt slammed
    # into the floor: the gates in the dome drop on the marked tiles
    a = m.anim("sluice", 2.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-160, 0, 8)), (1.0, (-166, 0, 8)), (1.08, (-40, 0, 10), "linear"),
          (1.6, (-42, 0, 10)), (2.4, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (1.0, (42, 0, 0)), (1.08, (20, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.8, (34, 0, 0)), (1.0, (34, 0, 0)), (1.08, (-64, 0, 0), "linear"),
          (1.6, (-64, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 0, -20)), (1.0, (-72, 0, -20)), (1.08, (-20, 0, -10), "linear"),
          (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (1.08, (16, 0, 0), "linear"), (1.6, (14, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (6, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.08, (0, -3, 0), "linear"), (1.6, (0, -3, 0)), (2.4, (0, 0, 0)))

    # surge (phase 2): crouched, lance levelled, the tanks hissing (0.8 s = 16 ticks), then the jet drives him
    # forward like a ram for 0.7 s
    a = m.anim("surge", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (0.8, (-32, 0, 0)), (1.5, (-32, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (14, 0, 0)), (1.5, (14, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (0.7, (-6, 0, 0)), (1.5, (-6, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-44, 10, 0)), (1.5, (-44, 10, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (24, 0, 0)), (1.5, (26, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-18, 0, 0)), (1.5, (-18, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("tanks", (0, (0, 0, 0)), (0.7, (-6, 0, 0)), (0.8, (4, 0, 0), "linear"), (1.5, (2, 0, 0)), (2.3, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.7, (0, -4, 2)), (0.8, (0, -3, -2), "linear"), (1.5, (0, -3, -2)), (2.3, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.7, (-40, 0, 0)), (1.5, (-40, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.7, (40, 0, 0)), (1.5, (40, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.7, (28, 0, 0)), (1.5, (28, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.7, (14, 0, 0)), (1.5, (14, 0, 0)), (2.3, (0, 0, 0)))

    # burst (phase 2): the gate lifted high on his left arm (0.9 s = 18 ticks), slammed edge-down into the floor: the
    # tanks vent a ring of scalding steam
    a = m.anim("burst", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.75, (-150, 0, -16)), (0.9, (-156, 0, -18)), (0.98, (-40, 0, -8), "linear"),
          (1.3, (-42, 0, -8)), (1.9, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (0.98, (-10, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-16, 12, 0)), (0.98, (22, -6, 0), "linear"), (1.3, (20, -6, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (20, 0, 20)), (0.98, (0, 0, 10), "linear"), (1.9, (0, 0, 0)))
    a.rot("tanks", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (0.98, (8, 0, 0), "linear"), (1.3, (6, 0, 0)), (1.9, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, 1, 0)), (0.98, (0, -4, 0), "linear"), (1.3, (0, -4, 0)), (1.9, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (0.98, (-24, 0, 10 * sx), "linear"),
              (1.3, (-24, 0, 10 * sx)), (1.9, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.98, (30, 0, 0), "linear"), (1.3, (30, 0, 0)), (1.9, (0, 0, 0)))

    # flush (phase 3): he plants the lance and wrenches the valve wheel on his shoulder round (1.5 s = 30 ticks,
    # invulnerable): the cistern's sluices open; then he runs with the lance levelled for 6.8 s (four charges)
    a = m.anim("flush", 9.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-30, 0, 20)), (1.5, (-32, 0, 22)), (1.6, (-40, 0, 0), "linear"),
          (8.4, (-40, 0, 0)), (9.3, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (20, 0, 0), "linear"), (8.4, (20, 0, 0)), (9.3, (0, 0, 0)))
    a.rot("lance", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (-2, 0, 0), "linear"), (8.4, (-2, 0, 0)), (9.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-150, 0, 60)), (0.9, (-150, -40, 60)), (1.5, (-150, 40, 60)),
          (1.6, (-50, 10, 0), "linear"), (8.4, (-50, 10, 0)), (9.3, (0, 0, 0)))
    a.rot("wheel", (0, (0, 0, 0)), (0.4, (0, 0, 0)), (1.5, (360, 0, 0)), (8.4, (1440, 0, 0)), (9.3, (1440, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.4, (-6, -20, 0)), (1.5, (-8, -24, 0)), (1.6, (20, 0, 0), "linear"),
          (8.4, (20, 0, 0)), (9.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-10, -30, 0)), (1.5, (-14, -30, 0)), (1.6, (-14, 0, 0), "linear"),
          (8.4, (-14, 0, 0)), (9.3, (0, 0, 0)))
    run_r = [(1.6 + 0.3 * i, ((-36 if i % 2 else 30), 0, 0), "linear") for i in range(23)]
    run_l = [(1.6 + 0.3 * i, ((30 if i % 2 else -36), 0, 0), "linear") for i in range(23)]
    a.rot("thigh_r", (0, (0, 0, 0)), (1.5, (0, 0, 0)), *run_r, (9.3, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.5, (0, 0, 0)), *run_l, (9.3, (0, 0, 0)))
    a.rot("tanks", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (6, 0, 0), "linear"), (8.4, (6, 0, 0)), (9.3, (0, 0, 0)))

    # reel: his guard broken (a heavy blow on the gate or a hit in the back): the shield flung aside at 0.3 s, he
    # staggers back a step and hangs open for 1.5 s
    a = m.anim("reel", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-60, 0, -70), "linear"), (0.6, (-20, 0, -50)), (1.6, (-18, 0, -46)),
          (2.0, (0, 0, 0)))
    a.rot("shield", (0, (0, 0, 0)), (0.3, (0, -30, 0), "linear"), (1.6, (0, -30, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (-22, 14, 0), "linear"), (0.6, (-14, 10, 6)), (1.6, (-12, 10, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-24, 0, 0), "linear"), (0.6, (10, 0, 14)), (1.6, (10, 0, 14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-10, 0, 30), "linear"), (0.6, (10, 0, 24)), (1.6, (10, 0, 24)), (2.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, 0, 3), "linear"), (0.6, (0, -3, 4)), (1.6, (0, -3, 4)), (2.0, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.6, (24, 0, 0)), (1.6, (24, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (1.6, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, (0, 0, 0)))

    # roar (phase two): lance and gate thrown wide, the porthole flaring, the tanks venting
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-120, 0, 40)), (1.6, (-124, 0, 42)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-110, 0, -40)), (1.6, (-114, 0, -42)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-26, 0, 0)), (1.6, (-24, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("tanks", (0, (0, 0, 0)), (0.5, (-6, 0, 0)), (1.0, (4, 0, 0)), (1.6, (-4, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("crown", (0, (0, 0, 0)), (1.6, (0, 360, 0)), (2.0, (0, 360, 0)))

    # stagger: his posture broken, he sinks on one knee, propped on the gate
    a = m.anim("stagger", 2.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -8, 0)), (2.0, (0, -8, 0)), (2.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (2.0, (20, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (70, 0, 0)), (2.0, (70, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (-66, 0, 0)), (2.0, (-66, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (66, 0, 0)), (2.0, (66, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (24, 0, -8)), (2.0, (26, 0, -8)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, 10)), (2.0, (28, 0, 10)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-20, 0, -6)), (2.0, (-22, 0, -6)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (30, 0, 20)), (2.0, (30, 0, 20)), (2.5, (0, 0, 0)))
