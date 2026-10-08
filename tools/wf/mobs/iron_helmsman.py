"""The Iron Helmsman (Le Timonier de Fer): pilot and champion of the Walking Fortress, about 5.2 blocks tall.

Silhouette idea: a hulking armoured sea captain fused into a steam harness. A barrel chest under a captain's coat of
riveted iron plates with brass trim and epaulettes, a sunken visor helm with a peaked brim and one glowing amber
slit, a copper boiler on his back with a short smoking stack leaning off to his left. Strong asymmetry: the RIGHT arm
ends in a banded harpoon-cannon (a barbed harpoon in its muzzle) under a huge pauldron; the LEFT arm drags a ship's
anchor on a chain, its crown scraping the deck beside him.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

NAVY = (40, 46, 66)
NAVY_D = (24, 28, 42)


def coat(seed=0, base=NAVY):
    """Captain's coat cloth: dark navy, brass piping down the edges, faint folds, darker toward the hem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 0.8)
        if x in (0, w - 1):
            return B.BRASS_D
        if y == h - 1:
            return B.BRASS
        k = 1.04 + (0.08 if x % 4 == 1 else 0.0) - 0.25 * (y / max(1, h)) + (B.n(x, y, seed) - 0.5) * 0.05
        return mul(base, k)
    return f


def coat_plate(seed=0):
    """A riveted iron coat plate with a brass rim and a rivet line down the middle."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(B.IRON, 1.05 if face == "top" else 0.7)
        if y == 0:
            return B.BRASS_L
        if x in (0, w - 1) or y == h - 1:
            return B.BRASS_D
        if x == w // 2 and y % 3 == 1:
            return B.BRASS
        k = 1.1 - 0.25 * (y / max(1, h)) + (B.n(x, y, seed) - 0.5) * 0.08
        return mul(B.IRON_L if (x + y // 4) % 5 == 0 else B.IRON, k)
    return f


def chest_paint(f, x, y, w, h):
    """The breastplate: navy coat on the sides and back, a riveted iron cuirass in front with two lapels of brass,
    a row of brass buttons and a round furnace port (glow) over the heart."""
    if f in ("top", "bottom"):
        return B.iron(30)(f, x, y, w, h)
    if f != "front":
        return coat(31)(f, x, y, w, h)
    cx = (w - 1) / 2
    if abs(x - cx) > w / 2 - 3:                       # coat edges
        return mul(NAVY, 1.0 - 0.2 * y / h)
    if abs(abs(x - cx) - (w / 2 - 3.5)) < 0.6:
        return B.BRASS_L if y < 2 else B.BRASS        # lapel trim
    if abs(x - cx) < 0.6 and y % 3 == 2 and y > 12:
        return B.BRASS_L                              # buttons
    if y == 0:
        return B.IRON_L
    if (x + 1) % 6 == 0 and y % 4 == 1:
        return B.BRASS                                # rivets
    return mul(B.IRON, 1.12 - 0.3 * y / h + (B.n(x, y, 32) - 0.5) * 0.06)


def helm_paint(f, x, y, w, h):
    """The visor helm: dark iron, a brass rim, a horizontal amber slit across the front, breathing holes below."""
    if f == "top":
        return mix(B.IRON, B.IRON_L, 0.4)
    if f == "bottom":
        return B.IRON_D
    if f == "front":
        if y in (4, 5) and 1 <= x <= w - 2:
            return B.AMBER if y == 4 else B.AMBER_D
        if y == 3 or y == 6:
            return B.SOOT
        if y >= 8 and x % 2 == 1 and 2 <= x <= w - 3:
            return B.SOOT                              # breathing holes
    if y == 0:
        return B.BRASS
    return mul(B.IRON, 1.08 - 0.2 * y / h + (B.n(x, y, 33) - 0.5) * 0.06)


def slit_glow(f, x, y, w, h):
    if f == "front" and y in (4, 5) and 1 <= x <= w - 2:
        return B.AMBER_L if y == 4 else B.AMBER
    return None


def link(seed=0):
    return B.plate(B.IRON_L, B.IRON_D, mix(B.IRON_L, (255, 255, 255), 0.3), seed=seed, grad=0.1)


def build():
    m = Model("iron_helmsman", seed=97, shadow=2.0, walk_speed=0.7, walk_scale=0.9)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -34, 0))
    m.part("skirt", "pelvis", pivot=(0, 1, 0))
    m.part("tails", "pelvis", pivot=(0, 0, 6), rot=(6, 0, 0))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0), rot=(8, 0, 0))
    m.part("head", "chest", pivot=(0, -20, -5), rot=(-8, 0, 0))
    m.part("boiler", "chest", pivot=(0, -11, 8))
    m.part("stack", "boiler", pivot=(4, -10, 6), rot=(-6, 0, 12))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(7 * sx, 0, 0), rot=(0, 0, -4 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 16, 0), rot=(0, 0, 4 * sx))
    m.part("arm_r", "chest", pivot=(-16, -17, 0), rot=(-8, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 13, 0), rot=(-48, 0, 0))
    m.part("harpoon", "fore_r", pivot=(0, 19, 0))
    m.part("arm_l", "chest", pivot=(16, -17, 0), rot=(4, 0, -22))
    m.part("fore_l", "arm_l", pivot=(0, 13, 0), rot=(-8, 0, 8))
    m.part("chain", "fore_l", pivot=(0, 16, 0), rot=(0, 0, 12))
    m.part("anchor", "chain", pivot=(0, 9, 0), rot=(10, 55, 0))

    # ---- legs: armoured thighs, heavy greaves with brass knee cops, iron sabatons
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -4.5, -2, -4.5, 9, 17, 9, coat(2 + (sx > 0)))
        m.box(th, -5, 2, -5.2, 10, 9, 2, coat_plate(4 + (sx > 0)))                 # tasset over the front
        m.box(sh, -5, -2, -6, 10, 6, 4, B.brass(6, rivet_step=3))                    # knee cop
        m.box(sh, -4.5, 0, -4.5, 9, 14, 9, B.iron(7 + (sx > 0), rivet_step=4))
        m.box(sh, -5, 4, -5.2, 10, 2, 10, B.BRASS_D)                                 # greave band
        m.box(sh, -6, 14, -8, 12, 4, 13, B.iron(9, rivet_step=3))                     # sabaton
        m.box(sh, -5, 15, -9, 10, 3, 1, B.brass(10))                                 # toe cap

    # ---- pelvis, belt and the plated coat skirt
    m.box("pelvis", -10, -4, -6, 20, 6, 12, B.iron(11, rivet_step=3))
    m.box("waist", -10, -6, -7, 20, 6, 14, B.bands(B.LEATHER, B.BRASS_D, every=3, seed=12))
    m.box("waist", -3, -6, -7.8, 6, 6, 1, B.brass(13))                               # buckle
    m.box("skirt", -11, 0, -7.5, 10, 13, 2, coat_plate(14))
    m.box("skirt", 1, 0, -7.5, 10, 13, 2, coat_plate(15))
    m.box("skirt", -12, 0, -6, 2, 12, 12, coat(16))
    m.box("skirt", 10, 0, -6, 2, 12, 12, coat(17))
    m.box("tails", -11, 0, 0, 10, 21, 2, coat(18))
    m.box("tails", 1, 0, 0, 10, 21, 2, coat(19))
    m.box("tails", -11, 6, 2, 22, 2, 1, B.BRASS_D)

    # ---- the barrel chest: cuirass in front, navy coat around, brass epaulette ridge, furnace port over the heart
    m.box("chest", -13, -22, -8, 26, 22, 16, chest_paint)
    m.box("chest", -14, -23, -6, 28, 3, 12, B.plate(B.IRON_L, B.IRON_D, seed=34))     # shoulder yoke
    m.box("chest", -6, -9, -9, 6, 6, 1, B.lens(B.AMBER, B.BRASS, B.AMBER_L), glow=B.lens_glow(B.AMBER, B.AMBER_L))
    m.box("chest", 3, -18, -8.8, 4, 4, 1, B.gauge())                                # pressure gauge
    m.box("chest", -9, -23, -9, 18, 4, 3, B.plate(B.IRON, B.IRON_D, B.IRON_L, seed=35))  # gorget
    # copper steam pipes from the boiler over the right shoulder down to the cannon
    m.box("chest", -15, -21, 2, 3, 3, 7, B.rod(B.COPPER, 36))
    m.box("chest", -16, -24, 0, 4, 4, 4, B.copper(37))

    # ---- head: sunken visor helm, peaked brim, brass crest ridge and badge
    m.box("head", -5, -11, -5, 10, 11, 10, helm_paint, glow=slit_glow)
    m.box("head", -6, -9, -8, 12, 1, 4, B.plate(B.IRON_D, B.SOOT, B.IRON, seed=38))   # peak
    m.box("head", -1, -13, -5, 2, 3, 10, B.brass(39))                               # crest ridge
    m.box("head", -2, -8, -5.6, 4, 2, 1, B.brass(40))                               # badge

    # ---- boiler on the back: banded copper drum, firebox grate, rivets, the smoking stack
    m.box("boiler", -8, -10, 0, 16, 20, 11, B.bands(B.COPPER, B.COPPER_D, every=4, seed=41))
    m.box("boiler", -9, -11, 1, 18, 2, 9, B.BRASS_D)
    m.box("boiler", -9, 8, 1, 18, 2, 9, B.BRASS_D)
    m.box("boiler", -4, 2, 10.5, 8, 6, 1, {"back": B.grate(fire=B.AMBER_D), "*": B.IRON},
          glow={"back": lambda f, x, y, w, h: (None if x in (0, w - 1) or y in (0, h - 1) or x % 2 == 0
                                               else (B.AMBER_L if y >= h - 2 else B.AMBER))})
    m.box("boiler", -6, -8, 10.6, 3, 3, 1, {"back": B.gauge(), "*": B.BRASS})
    m.box("boiler", -10, -4, 4, 2, 10, 3, B.rod(B.BRASS, 42))                      # side pipe
    m.box("stack", -2.5, -15, -2.5, 5, 16, 5, B.soot(B.IRON, 43))
    m.box("stack", -3.5, -17, -3.5, 7, 3, 7, B.plate(B.BRASS_D, B.BRASS_DD, B.BRASS, seed=44))
    m.box("stack", -3, -5, -3, 6, 2, 6, B.BRASS_D)

    # ---- right arm: a great pauldron, iron arm, the harpoon-cannon
    m.box("arm_r", -8, -6, -7, 12, 8, 14, B.plate(B.IRON, B.IRON_D, B.IRON_L, seed=45, rivet_step=3))
    m.box("arm_r", -8.5, -1, -7.5, 13, 2, 15, B.BRASS_D)                            # pauldron rim
    m.box("arm_r", -4, 0, -4, 8, 14, 8, B.iron(46))
    m.box("arm_r", -2, -9, -3, 4, 4, 6, B.brass(47))                               # pauldron fin
    m.box("fore_r", -5, 0, -5, 10, 17, 10, B.bands(B.IRON, B.BRASS_D, every=4, seed=48))
    m.box("fore_r", -6, 15, -6, 12, 4, 12, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=49))  # muzzle ring
    m.box("fore_r", -3, 18.6, -3, 6, 1, 6, {"bottom": B.SOOT, "*": B.BRASS_D})         # bore
    m.box("fore_r", 5, 3, -2, 2, 8, 4, B.rod(B.COPPER, 50))                         # feed pipe
    m.box("harpoon", -1, -2, -1, 2, 6, 2, B.rod(B.IRON_L, 51))
    m.box("harpoon", -2, 4, -2, 4, 2, 4, B.IRON_L)
    m.box("harpoon", -1.5, 6, -1.5, 3, 3, 3, B.plate(B.IRON_L, B.IRON, seed=52))
    m.box("harpoon", -0.5, 9, -0.5, 1, 2, 1, B.IRON_L)
    m.box("harpoon", -3, 4, -0.5, 1, 3, 1, B.IRON_L)                                 # barbs
    m.box("harpoon", 2, 4, -0.5, 1, 3, 1, B.IRON_L)

    # ---- left arm: a chain-wrapped pauldron, plated forearm and fist, the chain and the anchor
    m.box("arm_l", -4, -5, -6, 11, 7, 12, B.plate(B.IRON, B.IRON_D, B.IRON_L, seed=53, rivet_step=3))
    m.box("arm_l", -4.5, -1, -6.5, 12, 2, 13, B.BRASS_D)
    m.box("arm_l", -4, 0, -4, 8, 14, 8, B.iron(54))
    m.box("arm_l", -4.5, 4, -4.5, 9, 2, 9, link(55))                                # chain coil
    m.box("arm_l", -4.5, 8, -4.5, 9, 2, 9, link(56))
    m.box("fore_l", -4.5, 0, -4.5, 9, 12, 9, coat_plate(57))
    m.box("fore_l", -4, 12, -4.5, 8, 6, 8, B.iron(58))                              # fist
    for k in range(4):
        if k % 2 == 0:
            m.box("chain", -1, k * 2.4, -0.5, 2, 3, 1, link(60 + k))
        else:
            m.box("chain", -0.5, k * 2.4, -1, 1, 3, 2, link(60 + k))
    # anchor hangs in the x-y plane: ring, stock, shank, crown with two curved arms and barbed flukes
    m.box("anchor", -2.5, -2, -0.5, 5, 4, 1, B.BRASS)                                # ring
    m.box("anchor", -9, 2, -1.5, 18, 3, 3, B.plate(B.BRASS_D, B.BRASS_DD, B.BRASS, seed=64))   # stock
    m.box("anchor", -10, 1.5, -2, 2, 4, 4, B.BRASS)
    m.box("anchor", 8, 1.5, -2, 2, 4, 4, B.BRASS)
    m.box("anchor", -2, 1, -2, 4, 22, 4, B.iron(65, rivet_step=3))                   # shank
    m.box("anchor", -5, 21, -2.5, 10, 4, 5, B.iron(66, rivet_step=2))                # crown
    for sx in (-1, 1):
        m.box("anchor", (5 if sx > 0 else -10), 18, -2, 5, 5, 4, B.iron(67))
        m.box("anchor", (9 if sx > 0 else -13), 13, -2, 4, 7, 4, B.iron(68))
        m.box("anchor", (10 if sx > 0 else -16), 8, -2.5, 6, 6, 5, B.plate(B.IRON_L, B.IRON_D, seed=69))  # fluke
        m.box("anchor", (12 if sx > 0 else -14), 6, -1.5, 2, 2, 3, B.IRON_L)          # barb point
    m.box("anchor", -1.5, 22, -3.1, 3, 2, 1, B.AMBER, glow={"front": B.AMBER})        # rivet

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (0, 6, 0)), (2.4, (0, 6, 0)), (3.2, (0, -4, 0)), (4.0, (0, 0, 0)))
    idle.rot("stack", (0, (0, 0, 0)), (1.0, (0, 0, 2)), (2.0, (0, 0, 0)), (3.0, (0, 0, -2)), (4.0, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 0)), (2.0, (4, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("tails", (0, (0, 0, 0)), (2.0, (3, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    walk.rot("thigh_r", (0, (22, 0, 0)), (0.9, (-22, 0, 0)), (1.8, (22, 0, 0)))
    walk.rot("thigh_l", (0, (-22, 0, 0)), (0.9, (22, 0, 0)), (1.8, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.45, (28, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (1.35, (28, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_r", (0, (-8, 0, 0)), (0.9, (8, 0, 0)), (1.8, (-8, 0, 0)))
    walk.rot("chain", (0, (10, 0, 0)), (0.9, (22, 0, 0)), (1.8, (10, 0, 0)))     # the anchor drags behind
    walk.rot("anchor", (0, (12, 0, 0)), (0.9, (20, 0, 0)), (1.8, (12, 0, 0)))
    walk.rot("chest", (0, (0, 4, 0)), (0.9, (0, -4, 0)), (1.8, (0, 4, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -1.2, 0)), (0.9, (0, 0, 0)), (1.35, (0, -1.2, 0)), (1.8, (0, 0, 0)))
    walk.rot("tails", (0, (6, 0, 0)), (0.45, (12, 0, 0)), (0.9, (6, 0, 0)), (1.35, (12, 0, 0)), (1.8, (6, 0, 0)))

    # sweep: the anchor is hauled back and out to his left (1.0 s = 20 ticks), then swung across the front
    a = m.anim("sweep", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-10, 40, -70)), (1.0, (-12, 45, -75)), (1.15, (-85, -55, 15), "linear"),
          (1.4, (-80, -60, 15)), (1.9, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (1.0, (0, 0, -30)), (1.15, (0, 0, 40), "linear"), (1.4, (0, 0, 30)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (0, 35, 0)), (1.15, (0, -35, 0), "linear"), (1.4, (0, -38, 0)), (1.9, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (1.0, (0, 10, 0)), (1.15, (0, -10, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-30, 0, -20)), (1.15, (10, 0, 10), "linear"), (1.9, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.0, (12, 0, -4)), (1.9, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.0, (-14, 0, 6)), (1.9, (0, 0, 0)))

    # slam: the anchor is heaved overhead with both arms (1.1 s = 22 ticks) and brought down in front
    a = m.anim("slam", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.95, (-170, 0, -15)), (1.1, (-175, 0, -18)), (1.2, (-55, 0, -10), "linear"),
          (1.55, (-58, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.95, (-150, 0, 25)), (1.1, (-155, 0, 25)), (1.2, (-50, 0, 10), "linear"),
          (1.55, (-50, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (1.1, (30, 0, 0)), (1.2, (-50, 0, 0), "linear"), (1.55, (-40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-18, 0, 0)), (1.2, (26, 0, 0), "linear"), (1.55, (22, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1.5, 0)), (1.2, (0, -4, 0), "linear"), (1.55, (0, -3.5, 0)), (2.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-26, 0, -8 * sx), "linear"),
              (1.55, (-24, 0, -8 * sx)), (2.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (40, 0, 0), "linear"), (1.55, (38, 0, 0)), (2.0, (0, 0, 0)))

    # harpoon: the cannon arm is raised and aimed, the boiler builds pressure (0.8 s = 16 ticks), then fires
    a = m.anim("harpoon", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-70, 10, 10)), (0.8, (-72, 10, 10)), (0.86, (-95, 10, 10), "linear"),
          (1.2, (-80, 10, 10)), (1.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.6, (8, 0, 0)), (1.2, (8, 0, 0)), (1.7, (0, 0, 0)))
    a.pos("harpoon", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (0.86, (0, -14, 0), "linear"), (1.0, (0, -4, 0)),
          (1.25, (0, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (0, -20, 0)), (0.86, (-6, -14, 0), "linear"), (1.2, (0, -16, 0)), (1.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (0, -10, 0)), (1.7, (0, 0, 0)))
    a.scale("boiler", (0, (1, 1, 1)), (0.8, (1.08, 1.08, 1.08)), (0.86, (0.96, 0.96, 0.96), "linear"), (1.7, (1, 1, 1)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (-16, 0, 0)), (1.7, (0, 0, 0)))

    # vent: he hunches, the boiler swells and hisses (1.2 s = 24 ticks), then blows scalding steam all around him
    a = m.anim("vent", 2.3)
    a.rot("chest", (0, (0, 0, 0)), (1.1, (24, 0, 0)), (1.2, (26, 0, 0)), (1.3, (-14, 0, 0), "linear"),
          (1.8, (-12, 0, 0)), (2.3, (0, 0, 0)))
    a.scale("boiler", (0, (1, 1, 1)), (1.2, (1.15, 1.12, 1.15)), (1.3, (0.94, 0.94, 0.94), "linear"),
            (1.8, (0.97, 0.97, 0.97)), (2.3, (1, 1, 1)))
    a.scale("stack", (0, (1, 1, 1)), (1.2, (1.1, 0.9, 1.1)), (1.3, (0.95, 1.2, 0.95), "linear"), (1.8, (1, 1.1, 1)),
            (2.3, (1, 1, 1)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.2, (20, 0, 10 * sx)), (1.3, (-30, 0, -55 * sx), "linear"),
              (1.8, (-28, 0, -50 * sx)), (2.3, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.2, (-20, 0, -6 * sx)), (1.8, (-10, 0, -6 * sx)), (2.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.2, (32, 0, 0)), (1.8, (16, 0, 0)), (2.3, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.2, (0, -3, 0)), (1.3, (0, 0.5, 0), "linear"), (1.8, (0, -1.5, 0)), (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-10, 0, 0)), (1.3, (-24, 0, 0), "linear"), (1.8, (-20, 0, 0)), (2.3, (0, 0, 0)))

    # charge: shoulder lowered behind the pauldron (0.8 s = 16 ticks), then he barrels forward
    a = m.anim("charge", 2.1)
    a.rot("chest", (0, (0, 0, 0)), (0.7, (28, 30, 0)), (0.8, (30, 32, 0)), (0.9, (34, 24, 0), "linear"),
          (1.5, (34, 24, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-40, 0, 20)), (1.5, (-45, 0, 20)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (30, 0, 10)), (1.5, (35, 0, 10)), (2.1, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.9, (60, 0, 0), "linear"), (1.5, (60, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-24, -20, 0)), (1.5, (-24, -20, 0)), (2.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, -3, 0)), (1.5, (0, -2, 0)), (2.1, (0, 0, 0)))
    # three heavy strides during the rush
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (-20, 0, 0)), (0.9, (-34, 0, 0), "linear"), (1.05, (30, 0, 0), "linear"),
          (1.2, (-34, 0, 0), "linear"), (1.35, (30, 0, 0), "linear"), (1.5, (0, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (24, 0, 0)), (0.9, (30, 0, 0), "linear"), (1.05, (-34, 0, 0), "linear"),
          (1.2, (30, 0, 0), "linear"), (1.35, (-34, 0, 0), "linear"), (1.5, (0, 0, 0)), (2.1, (0, 0, 0)))

    # overload (phase 2): fists clenched, he arches back as the boiler glows and swells (1.2 s = 24 ticks), then
    # fire bursts from the deck in a spreading pattern while the stack belches
    a = m.anim("overload", 3.4)
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-22, 0, 0)), (1.2, (-24, 0, 0)), (1.3, (18, 0, 0), "linear"),
          (2.6, (16, 0, 0)), (3.4, (0, 0, 0)))
    a.scale("boiler", (0, (1, 1, 1)), (1.2, (1.2, 1.15, 1.2)), (1.3, (1.0, 1.0, 1.0), "linear"),
            (1.6, (1.1, 1.1, 1.1)), (1.9, (1.0, 1.0, 1.0)), (2.2, (1.1, 1.1, 1.1)), (2.6, (1.0, 1.0, 1.0)), (3.4, (1, 1, 1)))
    a.scale("stack", (0, (1, 1, 1)), (1.2, (1.15, 0.85, 1.15)), (1.3, (0.9, 1.25, 0.9), "linear"), (2.6, (1, 1.15, 1)),
            (3.4, (1, 1, 1)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.2, (-30, 0, -40 * sx)), (1.3, (30, 0, -20 * sx), "linear"),
              (2.6, (28, 0, -20 * sx)), (3.4, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.3, (-16, 0, -10 * sx), "linear"), (2.6, (-16, 0, -10 * sx)), (3.4, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.3, (26, 0, 0), "linear"), (2.6, (26, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-26, 0, 0)), (1.3, (10, 0, 0), "linear"), (2.6, (8, 0, 0)), (3.4, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.3, (0, -2.5, 0), "linear"), (2.6, (0, -2.5, 0)), (3.4, (0, 0, 0)))

    # whirl (phase 2): the chain is paid out (0.7 s = 14 ticks), then the anchor spins around him for 2 s
    a = m.anim("whirl", 3.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-10, 0, -80)), (0.7, (-10, 0, -85)), (2.7, (-10, 0, -85)), (3.4, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.7, (0, 0, -18)), (2.7, (0, 0, -18)), (3.4, (0, 0, 0)))
    a.rot("anchor", (0, (0, 0, 0)), (0.7, (0, -55, -10)), (2.7, (0, -55, -10)), (3.4, (0, 0, 0)))
    a.rot("bone", (0, (0, 0, 0), "linear"), (0.7, (0, 0, 0), "linear"), (2.7, (0, -1440, 0), "linear"),
          (3.4, (0, -1440, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-20, 0, 40)), (2.7, (-20, 0, 40)), (3.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 0, 0)), (2.7, (-6, 0, 0)), (3.4, (0, 0, 0)))

    # broadside (phase 2): the cannon arm is raised to the sky like a signal (1.0 s = 20 ticks), he bellows, and the
    # walker's guns answer; he holds the arm up while the shells rain down
    a = m.anim("broadside", 3.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-165, 0, 15)), (1.0, (-170, 0, 15)), (1.08, (-178, 0, 15), "linear"),
          (2.9, (-172, 0, 15)), (3.6, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (-10, 0, 0), "linear"), (2.9, (0, 0, 0)), (3.6, (0, 0, 0)))
    a.pos("harpoon", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.08, (0, -3, 0), "linear"), (1.3, (0, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (2.9, (-26, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (2.9, (-12, 0, 0)), (3.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (0, 0, -20)), (2.9, (0, 0, -18)), (3.6, (0, 0, 0)))

    # roar (phase two): arms flung wide, head thrown back, the boiler swells and the stack belches
    a = m.anim("roar", 2.0)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-40, 0, -55 * sx)), (1.6, (-45, 0, -60 * sx)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("boiler", (0, (1, 1, 1)), (0.6, (1.15, 1.15, 1.15)), (1.6, (1.12, 1.12, 1.12)), (2.0, (1, 1, 1)))
    a.scale("stack", (0, (1, 1, 1)), (0.6, (1, 1.3, 1)), (1.6, (1, 1.25, 1)), (2.0, (1, 1, 1)))

    # stagger: pressure lost, he sags onto one knee, the anchor dropped, the cannon arm hanging
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.2, (0, -6, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (1.2, (-60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.2, (60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (70, 0, 0)), (1.2, (70, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, -8)), (1.2, (28, 0, -8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 10)), (1.2, (26, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (14, 0, 10)), (1.2, (16, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (1.2, (12, 0, -10)), (1.6, (0, 0, 0)))
