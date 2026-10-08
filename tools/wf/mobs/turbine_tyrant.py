"""The Turbine Tyrant (Le Tyran des turbines): the engineer of the Dam of the Drowned Valley, fused into the turbine
he would not leave when the valley flooded; about 5.7 blocks tall with his smokestacks.

Silhouette idea: a walking turbine housing. His body is a great round scroll-case of riveted iron and brass (seen from
the front a drum with the turbine's intake in its belly, a glowing eye where the impeller spins), carried on two thick
hydraulic legs; the engineer's soot-black torso grows out of its top, a flat cap and amber goggles, a respirator with
a hose plugged into the housing. Behind his shoulders two smokestacks rise above his head (the left one bent).
Strong asymmetry: his RIGHT arm ends in a turbine rotor, four twisted blades round a brass hub, that spins; in his
LEFT fist a valve-wrench as long as a man, its jaw held open by a brass worm screw. The volute's outlet pipe curls
out of his left flank; a valve wheel and three pressure gauges sit on the housing's right shoulder.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

LEATHER = (74, 52, 40)
LEATHER_D = (44, 30, 24)
LEATHER_L = (112, 82, 60)
SKIN = (176, 128, 100)
SKIN_D = (120, 82, 62)
SOOTSKIN = (92, 70, 60)
CAP = (52, 50, 56)
CAP_D = (30, 28, 32)
MOUST = (210, 206, 198)
STEEL = (150, 152, 160)
STEEL_L = (204, 206, 214)
STEEL_D = (90, 92, 100)
RUST = (140, 74, 40)
HOT = (255, 120, 40)
GUN = (104, 98, 94)          # the case: oiled gunmetal
GUN_L = (150, 144, 136)


# ---------------------------------------------------------------- paint
def housing(seed=0, top_row=False):
    """The scroll-case: dark riveted iron with brass seams every few rows, rust weeping from the rivets."""
    base = B.plate(GUN, B.IRON, GUN_L, rivet=B.BRASS_L, seed=seed, grad=0.18, rivet_step=4, worn=0.12)

    def f(face, x, y, w, h):
        if face == "top" and top_row:
            return mul(B.IRON_L, 0.9 + (B.n(x, y, seed) - 0.5) * 0.1)
        c = base(face, x, y, w, h)
        if c is None:
            return mul(GUN, 1.05)
        if face in ("front", "back", "left", "right") and y > 0 and B.n(x, y // 3, seed + 4) < 0.05:
            return mix(c, RUST, 0.55)                                   # rust streaks under the rivets
        return c
    return f


def seam(seed=0):
    """A brass seam band round the case."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return B.BRASS_D
        if face == "top":
            return B.BRASS_L
        c = B.BRASS_L if y == 0 else B.BRASS
        if x % 4 == 1:
            c = B.BRASS_L                                               # bolt heads
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.1)
    return f


def intake(face, x, y, w, h):
    """The intake ring on the belly: a brass bezel round a dark throat with the impeller glowing inside."""
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    outer = min(w, h) / 2
    if r > outer:
        return None
    if r > outer - 1.5:
        return B.BRASS_L if y < cy else B.BRASS
    if r > outer - 2.6:
        return B.BRASS_D if (int(math.degrees(math.atan2(y - cy, x - cx))) // 30) % 2 else B.BRASS_DD
    return mix(B.SOOT, B.AMBER_D, 0.35 - 0.3 * r / outer)


def intake_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    outer = min(w, h) / 2
    if r < outer - 2.6:
        return mix(B.AMBER_D, B.AMBER, 1.0 - r / outer) if r > 2 else B.AMBER_L
    return None


def leather(seed=0, buckles=False):
    """The engineer's coat: oiled leather, soot, brass buckles on straps."""
    def f(face, x, y, w, h):
        if face == "top":
            return LEATHER_D
        c = mul(LEATHER, 1.06 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if B.n(x // 2, y // 2, seed + 2) < 0.12:
            c = mix(c, B.SOOT, 0.5)
        if buckles and face == "front":
            if y in (3, 4) and abs(x - w // 3) <= 1:
                return B.BRASS_L if y == 3 else B.BRASS
            if abs(x - w // 3) == 0 or (y in (6, 7) and x > 1):
                return LEATHER_D                                        # the strap and the bib's edge
        return c
    return f


def head_paint(face, x, y, w, h):
    """The engineer's face: sooty skin, a heavy white moustache, the goggle strap round the head."""
    if face == "bottom":
        return SKIN_D
    if y in (3, 4):
        if face != "front":
            return CAP_D                                                # the goggle strap round the head
    if face != "front":
        return mix(SKIN, SOOTSKIN, B.n(x, y, 7)) if face != "top" else CAP
    if y == 7 and 1 <= x <= w - 2:
        return MOUST if x not in (w // 2 - 1, w // 2) else mul(MOUST, 0.85)
    if y == 8 and x in (1, 2, w - 3, w - 2):
        return MOUST
    if y == 6 and x in (w // 2 - 1, w // 2):
        return SKIN_D                                                   # the nose
    if y >= 8:
        return mix(SKIN, SOOTSKIN, 0.7)
    return mix(SKIN, SOOTSKIN, 0.35 + B.n(x, y, 11) * 0.4)


def blade(seed=0):
    """A turbine blade: polished steel, a brass root, a worn leading edge."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            c = STEEL_L if face == "top" else STEEL_D
            if x < 3:
                return B.BRASS if face == "top" else B.BRASS_D
            if y == 0:
                return mul(STEEL_L, 1.05)
            return mul(c, 1.0 - 0.15 * x / max(1, w) + (B.n(x, y, seed) - 0.5) * 0.08)
        return STEEL_D if x >= 3 else B.BRASS_D
    return f


def wrench_steel(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return STEEL_L
        if face == "bottom":
            return STEEL_D
        k = 1.12 if x == w // 2 else (0.82 if x in (0, w - 1) else 1.0)
        c = mul(STEEL, k + (B.n(x, y, seed) - 0.5) * 0.06)
        if B.n(x, y // 2, seed + 1) < 0.08:
            c = mix(c, RUST, 0.5)
        return c
    return f


def worm(face, x, y, w, h):
    """The jaw's adjusting screw: brass threads."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    return B.BRASS_L if (y + x) % 2 == 0 else B.BRASS_D


def grip(face, x, y, w, h):
    if face in ("top", "bottom"):
        return LEATHER_D
    return LEATHER_L if (y + x) % 3 == 0 else LEATHER


def goggle(face, x, y, w, h):
    return B.lens(B.AMBER, B.BRASS_L, B.AMBER_L)(face, x, y, w, h)


# ---------------------------------------------------------------- build
def build():
    m = Model("turbine_tyrant", seed=262, shadow=2.0, walk_speed=0.6, walk_scale=0.7, glow_pulse=0.08)

    m.part("bone", pivot=(0, 24, 0))
    m.part("housing", "bone", pivot=(0, -28, 0))
    m.part("impeller", "housing", pivot=(0, -16, -13))
    m.part("stacks", "housing", pivot=(0, -30, 9))
    m.part("stack_bend", "stacks", pivot=(9, -18, 0), rot=(0, 0, -24))
    m.part("chest", "housing", pivot=(0, -31, -1))
    m.part("head", "chest", pivot=(0, -19, -2))
    m.part("hose", "head", pivot=(0, -1, -6))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(9 * sx, -28, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 14, -1))
    m.part("arm_r", "chest", pivot=(-15, -15, 0), rot=(-34, 0, 14))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-42, 0, -6))
    m.part("rotor", "fore_r", pivot=(0, 17, 0))
    for i in range(4):
        m.part(f"blade{i}", "rotor", pivot=(0, 0, 0), rot=(24, 90 * i + 45, 0))
    m.part("arm_l", "chest", pivot=(15, -15, 0), rot=(-8, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-38, 0, 6))
    m.part("wrench", "fore_l", pivot=(0, 13, -1), rot=(58, 0, 0))

    # ---- legs: thick hydraulic thighs, piston shins, iron boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -5, -2, -5, 10, 8, 10, B.iron(1 + sx, rivet_step=3))            # the hip drum
        m.box(leg, -4, 6, -4, 8, 9, 8, B.bands(B.IRON, B.BRASS_D, every=3, seed=3))
        m.box(leg, -3, 12, -6, 6, 5, 2, B.brass(4))                                 # knee cap
        m.box(shin, -3.5, 0, -2.5, 7, 12, 7, B.iron(5 + sx))
        m.box(shin, -2.5, 1, -4.5, 2, 10, 2, B.rod(STEEL, 6))                       # piston rods
        m.box(shin, 0.5, 1, -4.5, 2, 10, 2, B.rod(STEEL, 7))
        m.box(shin, -3, 0, -5, 6, 2, 3, B.brass(8))
        m.box(shin, -5, 11, -8, 10, 3, 13, B.iron(9, rivet_step=3))                 # the boot
        m.box(shin, -4, 11.5, -9, 8, 2, 1, B.BRASS)                                 # toe cap

    # ---- the turbine housing: a round drum seen from the front (rows of widening plates), brass seams
    widths = (16, 26, 30, 32, 32, 30, 26, 18)
    for k, wdt in enumerate(widths):
        y = -32 + 4 * k
        d = 22 if k in (0, 7) else 24
        m.box("housing", -wdt / 2, y, -d / 2, wdt, 4, d, housing(10 + k, top_row=k == 0))
    m.box("housing", -15.5, -21, -12.5, 31, 2, 25, seam(20))                        # seams
    m.box("housing", -15.5, -12, -12.5, 31, 2, 25, seam(21))
    m.box("housing", -12.5, -29, -11.5, 25, 1, 23, seam(19))
    m.box("housing", -14, -2, -9, 28, 4, 18, B.iron(22, rivet_step=3))               # hip frame
    m.box("housing", -10, -26, -13.5, 20, 20, 1, intake, glow=intake_glow)          # the intake eye
    m.box("impeller", -7, -0.5, -0.5, 14, 1, 1, STEEL_L, glow=None)
    m.box("impeller", -0.5, -7, -0.5, 1, 14, 1, STEEL_L)
    m.box("impeller", -1.5, -1.5, -1, 3, 3, 1, B.AMBER_L, glow=B.AMBER_L)
    # the volute's outlet: a copper pipe curling out of the left flank and down behind the left hip
    m.box("housing", 15, -27, -5, 5, 6, 10, B.copper(23))
    m.box("housing", 18, -23, -4, 5, 14, 8, B.bands(B.COPPER, B.COPPER_D, every=3, seed=24))
    m.box("housing", 17, -10, -3, 6, 6, 10, B.copper(25))
    m.box("housing", 17.5, -9.5, 7, 5, 5, 3, B.soot(B.COPPER, 26))                 # its mouth, sooted
    m.box("housing", 17.5, -23.5, -4.5, 6, 1, 9, seam(27))
    # the right shoulder of the case: a valve wheel and three pressure gauges
    m.box("housing", -17, -26, -6, 2, 2, 2, B.IRON_D)                               # valve stem
    m.box("housing", -18, -30, -10, 1, 10, 10, B.cog(B.BRASS, teeth=6, hub=0.3, spokes=4, faces=("left", "right")))
    for i, (x, y) in enumerate(((-12, -30), (-6, -31), (4, -31))):
        m.box("housing", x, y, -12.5, 4, 4, 1, B.dial(B.BRASS, B.CREAM, B.IRON, B.BRASS_D, numerals=8))
    m.box("housing", 8, -31, -12, 2, 4, 1, B.gauge())
    m.box("housing", -2, -36, -4, 4, 4, 4, B.brass(28))                              # the safety valve
    m.box("housing", -1, -38, -3, 2, 2, 2, B.BRASS_L)
    # rivets of the front plates (bolt heads standing proud)
    for x, y in ((-13, -17), (12, -17), (-11, -6), (10, -6), (-9, -29), (8, -29)):
        m.box("housing", x, y, -12.8, 1, 1, 1, B.BRASS_L)

    # ---- the smokestacks behind the shoulders (the left one bent)
    m.box("stacks", -11, -32, -2.5, 5, 32, 5, B.bands(B.IRON, B.BRASS_D, every=6, seed=30))
    m.box("stacks", -12, -36, -3.5, 7, 4, 7, B.soot(B.IRON, 31))                    # the crown
    m.box("stacks", -12, -8, -3.5, 7, 3, 7, B.brass(32))
    m.box("stacks", 6, -18, -2.5, 5, 18, 5, B.bands(B.IRON, B.BRASS_D, every=6, seed=33))
    m.box("stacks", 5, -6, -3.5, 7, 3, 7, B.brass(34))
    m.box("stack_bend", -3, -14, -2.5, 5, 14, 5, B.soot(B.IRON, 35, amount=0.2))
    m.box("stack_bend", -4, -17, -3.5, 7, 3, 7, B.soot(B.IRON, 36))

    # ---- the engineer's torso out of the top of the case
    m.box("chest", -10, -6, -6, 20, 7, 12, leather(40))                              # waist sunk in the case
    m.box("chest", -12, -18, -7, 24, 13, 13, leather(41, buckles=True))
    m.box("chest", -9, -16, -7.5, 18, 10, 1, leather(42, buckles=True))              # the bib of the apron
    m.box("chest", -14, -20, -6, 8, 6, 11, B.iron(43, rivet_step=3))                  # right pauldron (iron)
    m.box("chest", 6, -21, -6, 9, 7, 11, B.brass(44, rivet_step=3))                   # left pauldron (brass)
    m.box("chest", 8, -23, -4, 5, 2, 7, B.BRASS_D)
    m.box("chest", -7, -13, -8.2, 3, 3, 1, B.dial(B.BRASS, B.CREAM, B.IRON, B.BRASS_D, numerals=6))
    m.box("chest", -3, -20, -3, 6, 3, 6, leather(45))                                # neck / collar

    # ---- head: sooty face, flat cap, amber goggles, a respirator and its hose down into the case
    m.box("head", -5, -10, -5, 10, 10, 10, head_paint)
    m.box("head", -6, -12, -6, 12, 3, 12, B.plate(CAP, CAP_D, mix(CAP, (255, 255, 255), 0.2), seed=50))
    m.box("head", -6, -10, -9, 12, 1, 4, B.plate(CAP, CAP_D, CAP, seed=51))          # the peak
    m.box("head", -4.5, -8, -5.8, 4, 3, 1, goggle, glow=B.lens_glow(B.AMBER, B.AMBER_L))
    m.box("head", 0.5, -8, -5.8, 4, 3, 1, goggle, glow=B.lens_glow(B.AMBER, B.AMBER_L))
    m.box("head", -0.5, -7.5, -5.6, 1, 1, 1, B.BRASS_D)
    m.box("head", -3, -3, -6.2, 6, 3, 2, B.iron(52))                                  # respirator
    m.box("head", -1, -2.5, -6.8, 2, 2, 1, B.grate(B.IRON, B.SOOT))
    m.box("hose", -1, 0, -1, 2, 8, 2, B.bands(LEATHER_D, B.BRASS_D, every=2, seed=53))

    # ---- right arm: an iron arm ending in the rotor
    m.box("arm_r", -5, -3, -5, 10, 7, 10, B.iron(60, rivet_step=3))                  # shoulder drum
    m.box("arm_r", -3.5, 3, -3.5, 7, 10, 7, B.bands(B.IRON, B.BRASS_D, every=4, seed=61))
    m.box("fore_r", -4, 0, -4, 8, 10, 8, B.iron(62))
    m.box("fore_r", -2, 10, -2, 4, 6, 4, B.rod(STEEL, 63))                           # the shaft
    m.box("fore_r", -3, 13, -3, 6, 2, 6, B.brass(64))
    m.box("rotor", -3, -1, -3, 6, 4, 6, B.brass(65, rivet_step=2))                   # hub
    m.box("rotor", -1.5, 3, -1.5, 3, 2, 3, B.AMBER, glow=B.AMBER)                   # its hot nose
    for i in range(4):
        m.box(f"blade{i}", 2, 0, -2.5, 19, 1, 5, blade(70 + i))
        m.box(f"blade{i}", 18, -0.5, -3, 3, 2, 6, B.brass(74 + i))                   # brass tip

    # ---- left arm: a brass arm, an iron gauntlet, the great valve-wrench
    m.box("arm_l", -4.5, -3, -5, 9, 7, 10, B.brass(80, rivet_step=3))
    m.box("arm_l", -3.5, 3, -3.5, 7, 10, 7, leather(81))
    m.box("fore_l", -4, 0, -4, 8, 9, 8, B.bands(B.IRON, B.BRASS_D, every=3, seed=82))
    m.box("fore_l", -4.5, 8, -4.5, 9, 6, 9, B.iron(83))                               # gauntlet
    m.box("wrench", -1.5, -8, -2, 3, 36, 4, wrench_steel(84))                        # the handle
    m.box("wrench", -2, -2, -2.5, 4, 8, 5, grip)                                     # leather grip
    m.box("wrench", -2, -10, -2.5, 4, 3, 5, STEEL_D)
    m.box("wrench", -5, 26, -3, 10, 5, 6, wrench_steel(85))                           # the head
    m.box("wrench", -5, 31, -3, 3, 7, 6, wrench_steel(86))                            # fixed jaw
    m.box("wrench", 2, 31, -3, 3, 5, 6, wrench_steel(87))                             # sliding jaw
    m.box("wrench", -2, 27, -4, 4, 3, 1, worm)                                        # the worm screw
    m.box("wrench", -4.5, 24, -2.5, 9, 2, 5, B.brass(88))

    _anims(m)
    return m


def _spin(a, t0, t1, turns, part="rotor", axis=1):
    """A linear spin of ``part`` from t0 to t1 (whole turns, so it ends where it started)."""
    keys = []
    steps = max(2, turns * 4)
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        ang = 360.0 * turns * i / steps
        vec = (0, ang, 0) if axis == 1 else (0, 0, ang)
        keys.append((t, vec, "linear"))
    a.rot(part, *keys)


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (0, 10, 0)), (2.6, (4, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("rotor", (0, (0, 0, 0), "linear"), (4.0, (0, 90, 0), "linear"))
    idle.rot("impeller", (0, (0, 0, 0), "linear"), (4.0, (0, 0, 180), "linear"))
    idle.rot("wrench", (0, (0, 0, 0)), (2.0, (4, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("hose", (0, (0, 0, 0)), (2.0, (6, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("stack_bend", (0, (0, 0, 0)), (1.0, (0, 0, 2)), (3.0, (0, 0, -2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    for side, ph in (("r", 0.0), ("l", 1.0)):
        walk.rot(f"leg_{side}", (0, (24 if ph == 0 else -24, 0, 0)), (1.0, (-24 if ph == 0 else 24, 0, 0)),
                 (2.0, (24 if ph == 0 else -24, 0, 0)))
        lift = 0.5 if ph == 0 else 1.5
        keys = [(0, (0, 0, 0)), (lift, (26, 0, 0)), (lift + 0.5, (0, 0, 0)), (2.0, (0, 0, 0))]
        if lift > 0.5:
            keys.insert(1, (lift - 0.5, (0, 0, 0)))
        walk.rot(f"shin_{side}", *keys)
    walk.pos("housing", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("housing", (0, (0, 0, 3)), (1.0, (0, 0, -3)), (2.0, (0, 0, 3)))
    walk.rot("arm_l", (0, (-8, 0, 0)), (1.0, (8, 0, 0)), (2.0, (-8, 0, 0)))
    walk.rot("arm_r", (0, (6, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (6, 0, 0)))
    walk.rot("rotor", (0, (0, 0, 0), "linear"), (2.0, (0, 180, 0), "linear"))

    # rotor: the rotor drawn back to his right while it spins up with a whine (1.1 s = 22 ticks), then swept across
    # his front to the left (240 degrees), the housing twisting with it
    a = m.anim("rotor", 2.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-10, -60, 50)), (1.1, (-12, -66, 54)), (1.25, (-30, 80, -10), "linear"),
          (1.5, (-26, 86, -12)), (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.1, (20, 0, 0)), (1.25, (30, 0, 0), "linear"), (2.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (0, 30, 0)), (1.25, (6, -34, 0), "linear"), (1.5, (6, -36, 0)), (2.1, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (1.1, (0, 14, 0)), (1.25, (0, -16, 0), "linear"), (1.5, (0, -16, 0)),
          (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (10, 0, -20)), (1.25, (-20, 0, -30), "linear"), (2.1, (0, 0, 0)))
    _spin(a, 0.0, 2.1, 6)

    # wrench: the valve-wrench heaved up over his left shoulder in both arms (1.0 s = 20 ticks), then slammed into the
    # floor in front of him: the floor cracks in a line
    a = m.anim("wrench", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-160, 0, -10)), (1.0, (-168, 0, -8)), (1.1, (-84, 30, -10), "linear"),
          (1.5, (-82, 30, -10)), (2.0, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.1, (0, 0, 0), "linear"), (2.0, (0, 0, 0)))
    a.rot("wrench", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (1.1, (-30, 0, 0), "linear"), (1.5, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-18, -10, 0)), (1.1, (26, 22, 0), "linear"), (1.5, (24, 22, 0)), (2.0, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (1.1, (8, 0, 0), "linear"), (1.5, (8, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-30, 0, 40)), (1.1, (10, 0, 30), "linear"), (2.0, (0, 0, 0)))
    a.pos("housing", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.1, (0, -2, 0), "linear"), (1.5, (0, -2, 0)), (2.0, (0, 0, 0)))

    # vents: the wrench jammed onto the valve wheel of his right shoulder (0.9 s = 18 ticks), then cranked round and
    # round for 1.5 s while the floor grates blow
    a = m.anim("vents", 3.1)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-70, 60, -10)), (0.9, (-74, 66, -12)),
          (1.2, (-100, 70, -20)), (1.5, (-74, 66, -12)), (1.8, (-100, 70, -20)), (2.1, (-74, 66, -12)),
          (2.4, (-100, 70, -20)), (2.6, (-74, 66, -12)), (3.1, (0, 0, 0)))
    a.rot("wrench", (0, (0, 0, 0)), (0.9, (-40, 0, 60)), (2.6, (-40, 0, 60)), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, 26, 0)), (2.6, (0, 26, 0)), (3.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (14, 20, 0)), (1.2, (-24, 0, 0), "linear"), (2.6, (-20, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 40)), (2.6, (-20, 0, 40)), (3.1, (0, 0, 0)))

    # pressure: he plants his feet and seals himself in (2.3 s = 46 ticks): the case swells, the stacks shake, arms
    # pulled in; then he vents it all in one radial blast, arms flung wide, head thrown back
    a = m.anim("pressure", 3.8)
    a.scale("housing", (0, (1, 1, 1)), (2.2, (1.1, 1.06, 1.1)), (2.3, (1.12, 1.07, 1.12)), (2.36, (0.94, 0.96, 0.94),
            "linear"), (2.6, (1, 1, 1)), (3.8, (1, 1, 1)))
    a.pos("housing", (0, (0, 0, 0)), (0.6, (0, -3, 0)), (2.3, (0, -3, 0)), (2.36, (0, 1, 0), "linear"),
          (3.2, (0, 0, 0)), (3.8, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (20, 0, 30 * sx)), (2.3, (24, 0, 34 * sx)),
              (2.38, (-40, 0, -80 * sx), "linear"), (3.2, (-38, 0, -76 * sx)), (3.8, (0, 0, 0)))
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.6, (-14, 0, -10 * sx)), (2.3, (-14, 0, -10 * sx)), (3.2, (-6, 0, -6 * sx)),
              (3.8, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.6, (26, 0, 0)), (2.3, (26, 0, 0)), (3.2, (10, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (18, 0, 0)), (2.3, (20, 0, 0)), (2.38, (-24, 0, 0), "linear"), (3.2, (-20, 0, 0)),
          (3.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.3, (20, 0, 0)), (2.38, (-34, 0, 0), "linear"), (3.2, (-30, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("stacks", (0, (0, 0, 0)), (1.0, (2, 0, 2)), (1.2, (-2, 0, -2)), (1.4, (2, 0, 2)), (1.6, (-3, 0, -2)),
          (1.8, (3, 0, 3)), (2.0, (-3, 0, -3)), (2.2, (3, 0, 3)), (2.38, (-8, 0, 0), "linear"), (3.0, (0, 0, 0)),
          (3.8, (0, 0, 0)))
    _spin(a, 0.0, 3.8, 10)

    # charge: shoulders down, rotor levelled like a ram (0.8 s = 16 ticks), then he barrels forward for 0.6 s
    a = m.anim("charge", 2.1)
    a.rot("housing", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (0.85, (22, 0, 0), "linear"), (1.4, (22, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-60, 0, 20)), (0.85, (-80, 0, 10), "linear"), (1.4, (-80, 0, 10)),
          (2.1, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (0.85, (42, 0, 0)), (1.4, (42, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (30, 0, -20)), (1.4, (30, 0, -20)), (2.1, (0, 0, 0)))
    for side, ph in (("r", 0), ("l", 1)):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.8, (-10 if ph else 20, 0, 0)), (0.95, (30 if ph else -30, 0, 0)),
              (1.1, (-30 if ph else 30, 0, 0)), (1.25, (30 if ph else -30, 0, 0)), (1.4, (0, 0, 0)), (2.1, (0, 0, 0)))
    _spin(a, 0.0, 2.1, 6)

    # stomp: a hydraulic leg lifted, steam hissing (0.6 s = 12 ticks), slammed down: steam bursts out of the case
    a = m.anim("stomp", 1.5)
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-50, 0, 0)), (0.6, (-52, 0, 0)), (0.66, (4, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.6, (40, 0, 0)), (0.66, (0, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (0.6, (-6, 0, 6)), (0.66, (6, 0, -2), "linear"), (1.0, (4, 0, 0)), (1.5, (0, 0, 0)))
    a.pos("housing", (0, (0, 0, 0)), (0.6, (0, 2, 0)), (0.66, (0, -2, 0), "linear"), (1.0, (0, -1, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-30, 0, -30)), (0.66, (10, 0, -20), "linear"), (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, 30)), (0.66, (10, 0, 20), "linear"), (1.5, (0, 0, 0)))

    # grind (phase 2): rotor sweep at 0.9 s (18 ticks), wrench slam at 1.5 s, rotor backswing at 2.1 s
    a = m.anim("grind", 3.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-10, -60, 50)), (0.9, (-12, -66, 54)), (1.0, (-30, 80, -10), "linear"),
          (1.8, (-30, 84, -10)), (2.1, (-14, -70, 50), "linear"), (2.5, (-12, -66, 50)), (3.2, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.0, (30, 0, 0), "linear"), (2.5, (30, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -20)), (1.35, (-166, 0, -8)), (1.5, (-84, 30, -10), "linear"),
          (2.0, (-82, 30, -10)), (3.2, (0, 0, 0)))
    a.rot("wrench", (0, (0, 0, 0)), (1.35, (40, 0, 0)), (1.5, (-30, 0, 0), "linear"), (2.2, (-30, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, 30, 0)), (1.0, (6, -34, 0), "linear"), (1.35, (-14, -10, 0)),
          (1.5, (24, 22, 0), "linear"), (1.95, (10, -20, 0)), (2.1, (6, 34, 0), "linear"), (2.5, (6, 32, 0)),
          (3.2, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (0.9, (0, 14, 0)), (1.0, (0, -16, 0), "linear"), (1.5, (8, 0, 0), "linear"),
          (2.1, (0, 16, 0), "linear"), (2.5, (0, 14, 0)), (3.2, (0, 0, 0)))
    _spin(a, 0.0, 3.2, 9)

    # vortex (phase 2): the rotor raised before him like a fan (1.0 s = 20 ticks), it spins up and draws the air (and
    # everyone) in for 1.2 s, then he whirls round once at 2.3 s
    a = m.anim("vortex", 3.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-70, 20, 20)), (1.0, (-74, 22, 20)), (2.2, (-76, 22, 20)),
          (2.3, (-40, 120, 20), "linear"), (2.5, (-36, 130, 20)), (3.2, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (2.2, (-30, 0, 0)), (2.5, (0, 0, 0)), (3.2, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (2.2, (-8, 0, 0)), (2.3, (0, -40, 0), "linear"),
          (2.5, (0, -50, 0)), (3.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 10, 0)), (2.2, (-10, 10, 0)), (2.3, (4, -30, 0), "linear"), (3.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (20, 0, -30)), (2.2, (20, 0, -30)), (2.3, (-30, 0, -60), "linear"),
          (3.2, (0, 0, 0)))
    _spin(a, 0.0, 3.2, 16)

    # overload (phase 3, invulnerable): he drops to one knee and cranks his own heart (1.5 s = 30 ticks), the rotor
    # raised and screaming, then rises and slams the floor: sparks everywhere
    a = m.anim("overload", 3.5)
    a.pos("housing", (0, (0, 0, 0)), (0.4, (0, -8, 0)), (1.5, (0, -8, 0)), (1.6, (0, -2, 0), "linear"), (2.8, (0, -2, 0)),
          (3.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (-70, 0, 0)), (1.5, (-70, 0, 0)), (1.6, (-10, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (70, 0, 0)), (1.5, (70, 0, 0)), (1.6, (10, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (1.5, (20, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (60, 0, 0)), (1.5, (60, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-170, 0, 20)), (1.5, (-174, 0, 20)), (1.6, (-30, 0, 30), "linear"),
          (2.8, (-30, 0, 30)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-70, 60, -10)), (0.7, (-100, 70, -20)), (1.0, (-70, 60, -10)),
          (1.3, (-100, 70, -20)), (1.5, (-70, 60, -10)), (1.6, (-20, 0, -40), "linear"), (3.5, (0, 0, 0)))
    a.rot("wrench", (0, (0, 0, 0)), (0.4, (-40, 0, 60)), (1.5, (-40, 0, 60)), (1.6, (40, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-30, 0, 0)), (1.6, (20, 0, 0), "linear"), (2.8, (14, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-14, 10, 0)), (1.6, (20, 0, 0), "linear"), (2.8, (16, 0, 0)), (3.5, (0, 0, 0)))
    _spin(a, 0.0, 3.5, 20)

    # dash (phase 3): crouched like a sprinter, rotor forward and blazing (1.0 s = 20 ticks), then three dashes across
    # the chamber in 2.25 s
    a = m.anim("dash", 4.05)
    a.rot("housing", (0, (0, 0, 0)), (1.0, (20, 0, 0)), (1.05, (28, 0, 0), "linear"), (3.25, (28, 0, 0)), (4.05, (0, 0, 0)))
    a.pos("housing", (0, (0, 0, 0)), (1.0, (0, -3, 0)), (3.25, (0, -3, 0)), (4.05, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-80, 0, 16)), (3.25, (-82, 0, 16)), (4.05, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (3.25, (40, 0, 0)), (4.05, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (40, 0, -20)), (3.25, (40, 0, -20)), (4.05, (0, 0, 0)))
    keys_r, keys_l = [(0, (0, 0, 0)), (1.0, (20, 0, 0))], [(0, (0, 0, 0)), (1.0, (-16, 0, 0))]
    t, s = 1.15, 1
    while t < 3.25:
        keys_r.append((t, (-34 * s, 0, 0)))
        keys_l.append((t, (34 * s, 0, 0)))
        t += 0.15
        s = -s
    keys_r += [(3.4, (0, 0, 0)), (4.05, (0, 0, 0))]
    keys_l += [(3.4, (0, 0, 0)), (4.05, (0, 0, 0))]
    a.rot("leg_r", *keys_r)
    a.rot("leg_l", *keys_l)
    _spin(a, 0.0, 4.05, 24)

    # roar (phase two): arms wide, head thrown back, every vent of the case blowing
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.6, (-18, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("housing", (0, (1, 1, 1)), (0.5, (1.06, 1.04, 1.06)), (1.6, (1.06, 1.04, 1.06)), (2.0, (1, 1, 1)))
    _spin(a, 0.0, 2.0, 6)

    # stagger: the case lurches, a knee buckles, the wrench's head on the floor, the rotor winding down
    a = m.anim("stagger", 2.0)
    a.pos("housing", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.6, (-40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("housing", (0, (0, 0, 0)), (0.3, (14, 0, -8)), (1.6, (16, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 8)), (1.6, (28, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, -10)), (1.6, (26, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (20, 0, 10)), (1.6, (22, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (1.6, (12, 0, -10)), (2.0, (0, 0, 0)))
