"""The Tesla Archon (L'Archonte Tesla): the champion of the Storm Spire, about 3.4 blocks tall.

Silhouette idea: a mad electrical engineer who climbed into his own coil suit and never came out. A heavy copper
cuirass wound with coils, a glowing aether coil-core in the chest, and on his back a towering tesla coil (an iron
frame, a fat copper winding, a brass toroid crackling at its crown) that rises a head and a half over him. Two
smaller coils sit on his shoulders like pauldrons. His head: a gaunt, pale old face with a manic grin, a bushy grey
moustache, brass goggles with glowing aether lenses pushed down over the eyes and a shock of wild white hair standing
straight up from the static. The tails of a scorched white lab coat hang behind from under the cuirass, rubber-soled
iron boots and copper greaves in brass bands. Asymmetry: his RIGHT arm is a massive copper gauntlet, the forearm
wound with coil and three electrode prongs on the knuckles (the arc punch); thick black cables run from the backpack
into it. His LEFT hand holds a coil-staff: an iron shaft wound with copper, insulator discs and a glowing orb on top.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

CU = (186, 112, 58)             # bright copper
CU_L = (232, 160, 100)
CU_D = (120, 64, 32)
CU_DD = (72, 36, 18)
VERD = (78, 172, 156)
VERD_D = (46, 112, 104)
BRASS = (204, 162, 72)
BRASS_L = (246, 214, 126)
BRASS_D = (136, 98, 40)
IRON = (62, 58, 60)
IRON_L = (104, 98, 98)
IRON_D = (36, 32, 34)
RUBBER = (28, 26, 28)
RUBBER_L = (54, 50, 52)
COAT = (226, 222, 208)          # the scorched lab coat
COAT_D = (176, 168, 150)
SOOT = (60, 50, 44)
SKIN = (222, 196, 176)          # pale, never sees the sun
SKIN_D = (176, 144, 124)
SKIN_L = (240, 222, 206)
HAIR = (246, 246, 240)
HAIR_D = (196, 198, 200)
TASH = (180, 178, 172)
ARC = (130, 220, 255)           # the electric glow
ARC_L = (226, 248, 255)
ARC_D = (60, 150, 230)
CERAMIC = (232, 226, 214)       # insulator discs
CERAMIC_D = (178, 168, 150)


# ---------------------------------------------------------------- paint
def winding(seed=0, base=CU, band=BRASS, every=4):
    """A coil winding: tight horizontal copper turns, a lit streak, a brass band every few turns, verdigris flecks."""
    def f(face, x, y, w, h):
        if face == "top":
            return mul(base, 1.12) if (x + y) % 3 else mix(base, BRASS_L, 0.4)
        if face == "bottom":
            return mul(base, 0.62)
        if y % every == every - 1:
            return band if x % 3 else mul(band, 0.8)
        c = CU_L if y % 2 == 0 else base
        k = 1.12 if x == w // 2 else (0.82 if x in (0, w - 1) else 1.0)
        c = mul(c, k + (B.n(x, y, seed) - 0.5) * 0.06)
        if B.n(x // 2, y, seed + 5) < 0.06:
            c = VERD if B.n(x, y, seed) > 0.5 else VERD_D
        return c
    return f


def cuirass(face, x, y, w, h):
    """The copper cuirass: riveted plates, a brass rim at the neck and the waist, the chest's coil-core housing
    painted on the front as a dark ring (the lens itself is a separate glowing cube)."""
    if face == "bottom":
        return CU_DD
    if face == "top":
        return BRASS if x in (0, w - 1) or y in (0, h - 1) else CU_D
    if y == 0 or y == h - 1:
        return BRASS_L if x % 2 else BRASS
    if face == "front":
        mid = (w - 1) / 2
        dx, dy = x - mid, y - 5
        r = (dx * dx + dy * dy) ** 0.5
        if 2.4 < r <= 3.6:
            return IRON_D if r > 3.0 else BRASS_D                                     # the core's housing
        if y in (10, 11) and abs(dx) > 1.5:
            return BRASS_D                                                             # a band under the core
    if face == "back" and 2 <= x <= w - 3 and 2 <= y <= h - 3:
        return IRON if (x + y) % 4 else IRON_L                                         # the coil's mounting frame
    return B.copper(311, grad=0.3, rivet_step=4)(face, x, y, w, h)


def coat(seed=0):
    """The scorched white lab coat: faint folds, soot creeping up from the hem, a burnt hole here and there."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SOOT
        if face == "top":
            return COAT_D
        burn = (y / max(1, h)) ** 2 * 0.9
        if B.n(x, y // 2, seed + 3) < burn * 0.5:
            return SOOT if B.n(x, y, seed) < 0.5 else mul(SOOT, 0.7)
        c = COAT if (x + int(B.n(x // 2, 1, seed) * 2)) % 4 else COAT_D
        return mul(c, 1.02 - 0.15 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.05)
    return f


def rubber(face, x, y, w, h):
    if face == "top":
        return RUBBER_L
    return RUBBER if (x + y) % 5 else RUBBER_L


def boot(face, x, y, w, h):
    """Iron boots on thick rubber insulator soles (the bottom two rows), a brass toe-cap."""
    if face == "bottom":
        return RUBBER
    if y >= h - 2:
        return RUBBER if (x + y) % 4 else RUBBER_L
    if face == "front" and y >= h - 4:
        return BRASS_L if y == h - 4 else BRASS
    return B.iron(312)(face, x, y, w, h)


def greave(face, x, y, w, h):
    """Copper greaves in brass bands."""
    if face in ("top", "bottom"):
        return CU_D
    if y % 5 == 0:
        return BRASS if x % 2 else BRASS_L
    return B.copper(313, grad=0.2)(face, x, y, w, h)


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return SKIN_L
        if face == "bottom":
            return SKIN_D
        return SKIN if B.n(x, y, seed) > 0.15 else SKIN_D
    return f


def head_paint(face, x, y, w, h):
    """The engineer's head (8 x 8 x 8): pale and gaunt, deep cheek lines, a wide manic grin full of teeth under a
    bushy grey moustache; the goggles are separate cubes over the eyes."""
    if face == "front":
        if y == 2:
            return SKIN_D if x in (1, 2, 5, 6) else SKIN                              # the brow, furrowed
        if y in (3, 4):
            return mul(SKIN_D, 0.9) if x in (0, 7) else SKIN                           # under the goggles
        if y == 5:
            return TASH if 1 <= x <= 6 else SKIN_D                                     # the moustache
        if y == 6:
            if x in (1, 6):
                return TASH
            return (246, 242, 226) if 2 <= x <= 5 else SKIN_D                          # the grin's teeth
        if y == 7:
            return (70, 30, 30) if 2 <= x <= 5 else SKIN_D
        if y <= 1:
            return HAIR if (x + y) % 2 else HAIR_D                                     # the hairline
    if face == "top":
        return HAIR if (x + y) % 3 else HAIR_D
    if face in ("left", "right") and y <= 3:
        return HAIR if (x + y) % 2 else HAIR_D
    if face == "back" and y <= 5:
        return HAIR if (x + y) % 2 else HAIR_D
    return skin(321)(face, x, y, w, h)


def hair(face, x, y, w, h):
    """Wild white hair standing up from the static."""
    if face == "bottom":
        return HAIR_D
    return HAIR if B.n(x, y, 331) > 0.25 else HAIR_D


def tash(face, x, y, w, h):
    return TASH if (x + y) % 3 else mul(TASH, 0.8)


def goggle_rim(face, x, y, w, h):
    return BRASS_L if (x + y) % 3 == 0 else BRASS


def lens(face, x, y, w, h):
    return ARC_L if (x, y) == (0, 0) else ARC


def lens_glow(face, x, y, w, h):
    return ARC_L if face == "front" else None


def strap(face, x, y, w, h):
    return (70, 46, 34) if (x + y) % 4 else (96, 64, 46)


def core(face, x, y, w, h):
    if face == "front":
        mid_x, mid_y = (w - 1) / 2, (h - 1) / 2
        r = ((x - mid_x) ** 2 + (y - mid_y) ** 2) ** 0.5
        return ARC_L if r < 1.0 else ARC
    return ARC_D


def core_glow(face, x, y, w, h):
    if face != "front":
        return None
    mid_x, mid_y = (w - 1) / 2, (h - 1) / 2
    r = ((x - mid_x) ** 2 + (y - mid_y) ** 2) ** 0.5
    return ARC_L if r < 1.2 else ARC


def toroid(face, x, y, w, h):
    """The coil's brass toroid: polished brass with a hot blue streak where the arcs leave it."""
    if face == "top":
        return BRASS_L if (x + y) % 3 else (255, 238, 170)
    if face == "bottom":
        return BRASS_D
    if y == 0:
        return BRASS_L
    return BRASS if (x + y) % 4 else mix(BRASS, ARC, 0.35)


def spark_glow(face, x, y, w, h):
    if face == "bottom":
        return None
    return ARC_L if (x * 3 + y * 5) % 7 == 0 else None


def insulator(face, x, y, w, h):
    if face == "top":
        return CERAMIC
    if face == "bottom":
        return CERAMIC_D
    return CERAMIC if y == 0 else (CERAMIC_D if y == h - 1 else mix(CERAMIC, CERAMIC_D, 0.4))


def cable(face, x, y, w, h):
    if face in ("top", "bottom"):
        return RUBBER
    return RUBBER_L if x == w // 2 and y % 3 == 0 else RUBBER


def prong(face, x, y, w, h):
    if face == "top":
        return ARC_L
    return BRASS_L if y == 0 else BRASS


def prong_glow(face, x, y, w, h):
    return ARC_L if face == "top" or y == 0 else None


def gauge(face, x, y, w, h):
    return B.gauge()(face, x, y, w, h) if face == "front" else BRASS_D


def orb(face, x, y, w, h):
    return ARC_L if (x + y) % 3 == 0 else ARC


def orb_glow(face, x, y, w, h):
    return ARC_L if (x + y) % 2 == 0 else ARC


def mech(seed=0):
    return B.brass(seed, grad=0.3)


def joint(face, x, y, w, h):
    return IRON_L if (x + y) % 2 else IRON


# ---------------------------------------------------------------- build
def build():
    m = Model("tesla_archon", seed=1373, shadow=1.2, walk_speed=0.8, walk_scale=0.7, glow_pulse=0.09)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -18, 0))
    m.part("tails", "hips", pivot=(0, 0, 3.5))
    m.part("chest", "hips", pivot=(0, -2, 0))
    m.part("neck", "chest", pivot=(0, -16, -0.5))
    m.part("head", "neck", pivot=(0, -1, 0))
    m.part("hair", "head", pivot=(0, -8, 0))
    m.part("pack", "chest", pivot=(0, -8, 5))
    m.part("coil", "pack", pivot=(0, -10, 2))
    m.part("torus", "coil", pivot=(0, -18, 1.5))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(3.0 * sx, -18, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 9, 0))
        m.part(f"pcoil_{side}", "chest", pivot=(7.5 * sx, -16, 0))
    m.part("arm_r", "chest", pivot=(-8.5, -14, 0), rot=(-8, 0, 10))
    m.part("fore_r", "arm_r", pivot=(-0.5, 8, 0), rot=(-30, 0, -4))
    m.part("fist_r", "fore_r", pivot=(0, 10, 0))
    m.part("arm_l", "chest", pivot=(8.0, -14, 0), rot=(-6, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0.5, 8, 0), rot=(-40, 0, 4))
    m.part("hand_l", "fore_l", pivot=(0, 9, 0))
    m.part("staff", "hand_l", pivot=(0, 1.5, -0.5), rot=(40, 0, 6))
    m.part("staff_top", "staff", pivot=(0, -24, 0))

    # ---- legs: copper greaves, iron boots on rubber soles
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, -1, -2.5, 5, 10, 5, greave)
        m.box(leg, -3, 2, -3, 6, 2, 6, winding(340 + sx, every=2))                       # a coil round the thigh
        m.box(shin, -2.5, 0, -2.5, 5, 6, 5, greave)
        m.box(shin, -3, -1, -3, 6, 2, 6, joint)                                          # the knee joint
        m.box(shin, -3, 5, -4, 6, 4, 7, boot)                                            # the boot

    # ---- hips: a riveted iron belt with a brass buckle and a pouch of tools; the coat tails behind
    m.box("hips", -6, -2, -3.5, 12, 4, 7, B.iron(350, rivet_step=3))
    m.box("hips", -1.5, -1.5, -4.2, 3, 3, 1, B.brass(351))
    m.box("hips", 3, 0, -4.4, 3, 4, 2, strap)                                            # a pouch
    m.box("hips", -5.5, 0, -4.2, 1, 5, 1, BRASS_D)                                       # a wrench in the belt
    m.box("hips", -6, 4, -4.4, 2, 1, 1, BRASS)
    m.box("tails", -6, -1, 0, 12, 14, 1, coat(352))
    m.box("tails", -6.5, 0, -3, 1, 10, 3, coat(353))
    m.box("tails", 5.5, 0, -3, 1, 10, 3, coat(354))

    # ---- chest: the copper cuirass, the glowing coil-core, a gauge, the shoulder coils
    m.box("chest", -6.5, -16, -4, 13, 16, 8, cuirass)
    m.box("chest", -2, -13.5, -4.8, 4, 4, 1, core, glow=core_glow)                      # the coil-core lens
    m.box("chest", -3, -14.5, -4.5, 6, 1, 1, BRASS_L)
    m.box("chest", -3, -9.5, -4.5, 6, 1, 1, BRASS_D)
    m.box("chest", 2.5, -7, -4.6, 3, 3, 1, gauge)                                        # a pressure gauge
    m.box("chest", -5.5, -7, -4.6, 2, 5, 1, winding(355, every=2))                       # small chest coil
    m.box("chest", -4, -18, -3, 8, 2, 6, B.brass(356))                                   # the gorget
    for side, sx in (("r", -1), ("l", 1)):
        p = f"pcoil_{side}"
        m.box(p, -3, -1, -3, 6, 2, 6, IRON)                                              # the base plate
        m.box(p, -2, -6, -2, 4, 5, 4, winding(357 + sx, every=3))
        m.box(p, -2.5, -7, -2.5, 5, 1, 5, insulator)
        m.box(p, -1, -9, -1, 2, 2, 2, toroid, glow=spark_glow)                          # a little brass ball

    # ---- head: pale and gaunt, wild white hair, goggles with glowing lenses, a grin under the moustache
    m.box("neck", -2, -2, -2, 4, 3, 4, skin(360))
    m.box("head", -4, -8, -4, 8, 8, 8, head_paint)
    m.box("head", -4.5, -5.5, -4.6, 9, 1, 1, strap)                                      # the goggle strap
    m.box("head", -4.6, -5.5, -4, 1, 1, 8, strap)
    m.box("head", 3.6, -5.5, -4, 1, 1, 8, strap)
    for gx in (-3.5, 0.5):
        m.box("head", gx, -6, -5.2, 3, 3, 1, goggle_rim)
        m.box("head", gx + 0.5, -5.5, -5.6, 2, 2, 1, lens, glow=lens_glow)
    m.box("head", -0.5, -5, -5.0, 1, 1, 1, BRASS_D)                                      # the bridge
    m.box("head", -5, -4, -4.6, 3, 2, 1, tash)                                           # moustache wings
    m.box("head", 2, -4, -4.6, 3, 2, 1, tash)
    m.box("head", -1, -2, -4.6, 2, 1, 1, SKIN_D)                                         # the chin's cleft
    # the hair, standing straight up in tufts
    for k, (hx, hz, hh) in enumerate(((-4, -3, 4), (-1.5, -4, 5), (1.5, -3, 4), (-3, 0, 5), (1, 0, 6), (-4.5, 2, 3),
                                      (2.5, 2, 4), (-0.5, 2.5, 4))):
        m.box("hair", hx, -hh, hz, 3, hh, 3, hair)
    m.box("hair", -5.5, -2, -2, 2, 3, 4, hair)                                           # side tufts
    m.box("hair", 3.5, -2, -2, 2, 3, 4, hair)

    # ---- the tesla coil on his back
    m.box("pack", -5, -6, -1, 10, 12, 4, B.iron(370, rivet_step=3))                      # the frame
    m.box("pack", -4.5, -4, 3, 3, 8, 3, winding(371))                                    # two capacitor jars
    m.box("pack", 1.5, -4, 3, 3, 8, 3, winding(372))
    m.box("pack", -4, -5, 3.5, 2, 1, 2, insulator)
    m.box("pack", 2, -5, 3.5, 2, 1, 2, insulator)
    m.box("coil", -3, -3, -1.5, 6, 3, 6, insulator)                                      # the coil's foot
    m.box("coil", -2.5, -16, -1, 5, 13, 5, winding(373, every=5))                        # the winding
    m.box("coil", -1, -18, 0.5, 2, 2, 2, BRASS_D)                                        # the stem to the toroid
    for k in range(4):                                                                   # the toroid: a brass ring
        ang = k * 90
        if ang in (0, 180):
            m.box("torus", -5, -2, -1 + (4 if ang == 180 else -4), 10, 3, 2, toroid, glow=spark_glow)
        else:
            m.box("torus", (3 if ang == 90 else -5), -2, -3, 2, 3, 6, toroid, glow=spark_glow)
    m.box("torus", -1, -4, -1, 2, 2, 2, BRASS_L, glow=ARC_L)                            # the spark ball on top
    m.box("torus", -0.5, -6, -0.5, 1, 2, 1, ARC, glow=ARC_L)                                # a frozen arc

    # ---- right arm: a massive copper gauntlet wound with coil, three electrode prongs on the knuckles
    m.box("arm_r", -3, -2, -3, 5, 9, 6, B.copper(380, grad=0.25))
    m.box("arm_r", -4, -3, -3.5, 6, 4, 7, B.brass(381))                                  # the shoulder plate
    m.box("fore_r", -4, 0, -4, 7, 10, 8, winding(382, every=3))                          # the coil forearm
    m.box("fore_r", -4.5, 8, -4.5, 8, 2, 9, B.brass(383))
    m.box("fist_r", -4, 0, -4, 7, 6, 8, B.copper(384, grad=0.25))                        # the great fist
    m.box("fist_r", -3.5, 1, -4.6, 6, 4, 1, BRASS_D)                                     # knuckle plate
    for px in (-3, -1, 1):
        m.box("fist_r", px, 2, -6.6, 2, 2, 2, prong, glow=prong_glow)                    # electrodes
    m.box("fore_r", 2, -1, 3, 2, 2, 2, cable)                                            # the cable into the gauntlet
    m.box("arm_r", 1, -6, 3, 2, 8, 2, cable)

    # ---- left arm: a leaner copper arm, a leather glove round the coil-staff
    m.box("arm_l", -2, -2, -2.5, 4, 9, 5, B.copper(390, grad=0.25))
    m.box("arm_l", -2.5, -3, -3, 5, 3, 6, B.brass(391))
    m.box("fore_l", -2, 0, -2.5, 4, 9, 5, coat(392))                                     # the coat sleeve
    m.box("fore_l", -2.5, 7, -3, 5, 2, 6, BRASS_D)
    m.box("hand_l", -2, 0, -2, 4, 3, 4, strap)
    # the coil-staff: an iron shaft, a copper winding, insulator discs, a glowing orb in brass prongs
    m.box("staff", -1, -22, -1, 2, 36, 2, B.rod(IRON, 393))
    m.box("staff", -1.5, 12, -1.5, 3, 3, 3, BRASS_D)
    m.box("staff", -1.5, -18, -1.5, 3, 8, 3, winding(394, every=2))
    for y in (-20, -9, -6):
        m.box("staff", -2.5, y, -2.5, 5, 1, 5, insulator)
    m.box("staff_top", -1.5, -1, -1.5, 3, 2, 3, BRASS)
    for px, pz in ((-2, 0), (1, 0), (0, -2), (0, 1)):
        m.box("staff_top", px, -5, pz, 1, 4, 1, BRASS_L)                                 # the prongs
    m.box("staff_top", -1.5, -5, -1.5, 3, 3, 3, orb, glow=orb_glow)                      # the orb

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.6, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (4, 12, -4)), (1.6, (-2, -10, 6)), (2.3, (6, 4, -8)), (3.0, (0, 0, 0)))
    idle.rot("hair", (0, (0, 0, 0)), (0.75, (4, 0, 3)), (1.5, (-3, 0, -3)), (2.25, (3, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("torus", (0, (0, 0, 0)), (1.5, (0, 180, 0)), (3.0, (0, 360, 0)))
    idle.rot("tails", (0, (0, 0, 0)), (1.5, (6, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("fore_r", (0, (0, 0, 0)), (1.5, (-6, 0, 0)), (3.0, (0, 0, 0)))
    idle.pos("staff_top", (0, (0, 0, 0)), (0.1, (0, -0.3, 0)), (0.2, (0, 0, 0)), (1.6, (0, 0, 0)), (1.7, (0, -0.3, 0)),
             (1.8, (0, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (24, 0, 0)), (1.0, (-24, 0, 0)), (2.0, (24, 0, 0)))
    walk.rot("leg_l", (0, (-24, 0, 0)), (1.0, (24, 0, 0)), (2.0, (-24, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (20, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.0, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.0, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (4, 6, 0)), (1.0, (4, -6, 0)), (2.0, (4, 6, 0)))
    walk.rot("tails", (0, (16, 0, 0)), (1.0, (22, 0, 0)), (2.0, (16, 0, 0)))
    walk.rot("arm_r", (0, (-14, 0, 0)), (1.0, (14, 0, 0)), (2.0, (-14, 0, 0)))

    # arcpunch (14 / 10 / 14): the gauntlet cocked back, sparks climbing the coil (0.7 s), a driving punch at 0.7 s;
    # he holds it while the arc jumps on to the next player (active 8)
    a = m.anim("arcpunch", 1.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (40, -20, 30)), (0.7, (44, -22, 32)), (0.76, (-90, 10, 0), "linear"),
          (1.2, (-90, 10, 0)), (1.9, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (-70, 0, 0)), (0.76, (0, 0, 0), "linear"), (1.2, (0, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, 30, 0)), (0.76, (10, -24, 0), "linear"), (1.2, (8, -22, 0)),
          (1.9, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.7, (0, 0, 2)), (0.76, (0, -1, -3), "linear"), (1.2, (0, -1, -3)), (1.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (0.76, (20, 0, 0), "linear"), (1.2, (20, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.76, (-20, 0, 0), "linear"), (1.2, (-20, 0, 0)),
          (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (0.76, (6, 0, 0), "linear"), (1.9, (0, 0, 0)))

    # orb (20 / 6 / 14): both hands cupped before the core, a ball of lightning swelling between them (1.0 s), then
    # pushed out from the chest
    a = m.anim("orb", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-60, 30, 0)), (1.0, (-62, 32, 0)), (1.06, (-90, 0, 0), "linear"),
          (1.3, (-90, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-60, -30, 0)), (1.0, (-62, -32, 0)), (1.06, (-90, 0, 0), "linear"),
          (1.3, (-90, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (-40, 0, 0)), (1.06, (0, 0, 0), "linear"), (2.0, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.06, (0, 0, 0), "linear"), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 0, 0)), (1.06, (8, 0, 0), "linear"), (1.3, (6, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (1.0, (1.3, 1.3, 1.3)), (1.06, (1.0, 1.0, 1.0), "linear"), (2.0, (1, 1, 1)))

    # coilslam (22 / 8 / 16): both arms raised high, the coil blazing (1.1 s), both fists brought down on the floor
    a = m.anim("coilslam", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-170, 0, -10)), (1.1, (-176, 0, -12)), (1.16, (-40, 0, 10), "linear"),
          (1.5, (-40, 0, 10)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-170, 0, 10)), (1.1, (-176, 0, 12)), (1.16, (-40, 0, -10), "linear"),
          (1.5, (-40, 0, -10)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-14, 0, 0)), (1.16, (30, 0, 0), "linear"), (1.5, (28, 0, 0)), (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 1, 0)), (1.16, (0, -4, 0), "linear"), (1.5, (0, -4, 0)), (2.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.16, (-30, 0, 10), "linear"), (1.5, (-30, 0, 10)), (2.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.16, (-30, 0, -10), "linear"), (1.5, (-30, 0, -10)), (2.3, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.16, (40, 0, 0), "linear"), (1.5, (40, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.16, (40, 0, 0), "linear"), (1.5, (40, 0, 0)), (2.3, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (1.1, (1.35, 1.35, 1.35)), (1.16, (1, 1, 1), "linear"), (2.3, (1, 1, 1)))

    # arcline (24 / 12 / 14): the coil-staff levelled at you (the line drawn, he tracks until 0.7 s), the orb
    # flaring (1.2 s), then the discharge down the line
    a = m.anim("arcline", 2.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-80, -20, 0)), (1.2, (-84, -20, 0)), (1.26, (-96, -10, 0), "linear"),
          (1.8, (-96, -10, 0)), (2.5, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.7, (90, 0, 0)), (1.8, (90, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (0, -24, 0)), (1.2, (-4, -26, 0)), (1.26, (4, -20, 0), "linear"),
          (1.8, (4, -20, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-30, 0, 40)), (1.8, (-30, 0, 40)), (2.5, (0, 0, 0)))
    a.scale("staff_top", (0, (1, 1, 1)), (1.2, (1.6, 1.6, 1.6)), (1.26, (1.1, 1.1, 1.1), "linear"), (1.8, (1.1, 1.1, 1.1)),
            (2.5, (1, 1, 1)))
    a.pos("hips", (0, (0, 0, 0)), (1.2, (0, 0, 1)), (1.26, (0, 0, 2), "linear"), (2.5, (0, 0, 0)))

    # corona (phase 2, 30 / 40 / 16): staff and gauntlet thrown up to the sky, the coil blazing (1.5 s); he holds the
    # pose, conducting the strikes down from the corona ring
    a = m.anim("corona", 4.3)
    a.rot("arm_l", (0, (0, 0, 0)), (1.2, (-170, 0, 20)), (1.5, (-176, 0, 22)), (1.56, (-160, 0, 30), "linear"),
          (3.5, (-160, 0, 30)), (4.3, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.5, (-30, 0, 0)), (3.5, (-30, 0, 0)), (4.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.2, (-170, 0, -20)), (1.5, (-176, 0, -22)), (1.56, (-160, 0, -30), "linear"),
          (3.5, (-160, 0, -30)), (4.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-34, 0, 0)), (3.5, (-30, 0, 0)), (4.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-12, 0, 0)), (3.5, (-10, 0, 0)), (4.3, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (1.5, (1.5, 1.5, 1.5)), (3.5, (1.4, 1.4, 1.4)), (4.3, (1, 1, 1)))
    a.rot("torus", (0, (0, 0, 0)), (1.5, (0, 720, 0)), (3.5, (0, 1800, 0)), (4.3, (0, 1800, 0)))
    a.scale("hair", (0, (1, 1, 1)), (1.5, (1.2, 1.5, 1.2)), (3.5, (1.2, 1.5, 1.2)), (4.3, (1, 1, 1)))

    # magnet (phase 2, 20 / 36 / 16): arms spread wide, the core blazing (1.0 s); he leans back and draws everything
    # in, then claps the arms shut (the discharge at 2.4 s)
    a = m.anim("magnet", 3.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-80, 0, 70)), (1.0, (-82, 0, 74)), (2.3, (-86, 0, 80)),
          (2.4, (-90, 30, 10), "linear"), (2.8, (-90, 30, 10)), (3.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-80, 0, -70)), (1.0, (-82, 0, -74)), (2.3, (-86, 0, -80)),
          (2.4, (-90, -30, -10), "linear"), (2.8, (-90, -30, -10)), (3.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (2.3, (-16, 0, 0)), (2.4, (12, 0, 0), "linear"),
          (2.8, (10, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (2.3, (-20, 0, 0)), (2.4, (10, 0, 0), "linear"), (3.6, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (1.0, (1.3, 1.3, 1.3)), (2.3, (1.4, 1.4, 1.4)), (2.4, (1, 1, 1), "linear"),
            (3.6, (1, 1, 1)))

    # overload (phase 3, 40 / 20 / 20): he rises off the deck, every coil blazing, hair on end (2.0 s), and the
    # overload bursts out of him
    a = m.anim("overload", 4.0)
    a.pos("hips", (0, (0, 0, 0)), (1.6, (0, 10, 0)), (2.0, (0, 12, 0)), (2.06, (0, 8, 0), "linear"), (3.0, (0, 6, 0)),
          (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-60, 0, 70)), (2.0, (-70, 0, 90)), (2.06, (-40, 0, 110), "linear"),
          (3.0, (-40, 0, 100)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-60, 0, -70)), (2.0, (-70, 0, -90)), (2.06, (-40, 0, -110), "linear"),
          (3.0, (-40, 0, -100)), (4.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.6, (10, 0, 10)), (3.0, (10, 0, 10)), (4.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.6, (10, 0, -10)), (3.0, (10, 0, -10)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (-36, 0, 0), "linear"), (3.0, (-20, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("hair", (0, (1, 1, 1)), (2.0, (1.3, 1.8, 1.3)), (3.0, (1.2, 1.5, 1.2)), (4.0, (1, 1, 1)))
    a.scale("torus", (0, (1, 1, 1)), (2.0, (1.6, 1.6, 1.6)), (2.06, (2.0, 2.0, 2.0), "linear"), (3.0, (1.3, 1.3, 1.3)),
            (4.0, (1, 1, 1)))
    a.rot("torus", (0, (0, 0, 0)), (2.0, (0, 1440, 0)), (4.0, (0, 2160, 0)))
    a.rot("tails", (0, (0, 0, 0)), (2.0, (40, 0, 0)), (3.0, (30, 0, 0)), (4.0, (0, 0, 0)))

    # arcsweep (phase 3, 30 / 120 / 20): he lifts off and floats to the middle of the platform (1.5 s), then hangs
    # there with both arms out, spinning slowly while the arc beams sweep the deck under him, and drops back (7.5 s)
    a = m.anim("arcsweep", 8.5)
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, 4, 0)), (7.5, (0, 4, 0)), (8.0, (0, -1, 0)), (8.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.4, (-90, 0, 80)), (1.5, (-90, 0, 84)), (7.5, (-90, 0, 84)), (8.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.4, (-90, 0, -80)), (1.5, (-90, 0, -84)), (7.5, (-90, 0, -84)), (8.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.5, (16, 0, 6)), (7.5, (16, 0, 6)), (8.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.5, (6, 0, -6)), (7.5, (6, 0, -6)), (8.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.5, (30, 0, 0)), (7.5, (30, 0, 0)), (8.5, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (1.5, (30, 0, 0)), (7.5, (34, 0, 0)), (8.5, (0, 0, 0)))
    a.rot("torus", (0, (0, 0, 0)), (1.5, (0, 360, 0)), (7.5, (0, 2520, 0)), (8.5, (0, 2520, 0)))
    a.scale("torus", (0, (1, 1, 1)), (1.5, (1.4, 1.4, 1.4)), (7.5, (1.4, 1.4, 1.4)), (8.5, (1, 1, 1)))
    a.scale("hair", (0, (1, 1, 1)), (1.5, (1.2, 1.5, 1.2)), (7.5, (1.2, 1.5, 1.2)), (8.5, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (20, 0, 0)), (7.5, (20, 0, 0)), (8.5, (0, 0, 0)))

    # roar (phase two): head thrown back in a cackle, arms flung wide, the coil and the hair blazing
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-40, 0, 70)), (1.6, (-44, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-40, 0, -70)), (1.6, (-44, 0, -74)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-34, 0, 0)), (0.8, (-28, 6, 0)), (1.1, (-34, -6, 0)), (1.6, (-30, 0, 0)),
          (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (0.5, (1.5, 1.5, 1.5)), (1.6, (1.4, 1.4, 1.4)), (2.0, (1, 1, 1)))
    a.scale("hair", (0, (1, 1, 1)), (0.5, (1.2, 1.6, 1.2)), (1.6, (1.2, 1.5, 1.2)), (2.0, (1, 1, 1)))

    # stagger: he slumps, smoking, the coil sputtering, down on one knee
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -5, 0)), (1.6, (0, -5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.6, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -14)), (1.6, (26, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 10)), (1.6, (-20, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-50, 0, -10)), (1.6, (-50, 0, -10)), (2.0, (0, 0, 0)))
    a.scale("torus", (0, (1, 1, 1)), (0.3, (0.8, 0.8, 0.8)), (1.6, (0.8, 0.8, 0.8)), (2.0, (1, 1, 1)))
