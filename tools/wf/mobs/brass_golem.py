"""Brass Golem (Golem de laiton): the friendly automaton a player builds from two Blocks of Brass and a Clockwork
Heart. About 2.3 blocks tall.

Silhouette idea: a walking boiler with a heart, read like a wind-up toy. A round barrel chest of riveted brass
hoops with a glowing furnace door for a belly, a small round copper diving-helmet head with a protruding porthole
(two round aether eyes behind the glass) and a whistle on top, two tall smokestacks with rattling soot lids on the
shoulders, big dome pauldrons, thin iron upper arms ending in huge banded forearms and piston fists, short stout
legs with knee pistons in big round-toed boots, and a huge wind-up key turning in its back. Brass weathered with
verdigris in the seams and soot around the stacks.
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B
from . import folkkit as K


def patina(spec, amount=0.3, seed=0):
    """Weathered brass: verdigris gathers in short runs along the bottom seam of a side face."""
    def f(face, x, y, w, h):
        c = spec(face, x, y, w, h) if callable(spec) else spec
        if c is None or face in ("top", "bottom") or h < 4:
            return c
        if y == h - 2 and K.h(x // 3, seed, 1) % 3 == 0:
            return mix(c, B.VERD_D, amount + 0.15)
        if y == h - 3 and K.h(x // 3, seed, 1) % 3 == 0 and K.h(x, seed, 2) % 3 == 0:
            return mix(c, B.VERD, amount)
        return c
    return f


def ring(rim=B.BRASS, rim_l=B.BRASS_L):
    """A porthole ring on a 7 x 7 front face: a round brass rim, see-through in the middle."""
    def f(face, x, y, w, h):
        if face not in ("front", "back"):
            return rim
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = math.hypot(x - cx, (y - cy) * 1.05)
        if r < 2.4:
            return None
        if r > 3.7:
            return None
        return rim_l if y < cy else (rim if y < cy + 2 else B.BRASS_D)
    return f


def visor(f, x, y, w, h):
    """The helmet front (8 x 7): smoked glass with two round aether eyes and a grille mouth."""
    if f != "front":
        return patina(B.copper(15), 0.25, 15)(f, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, (y - cy) * 1.15)
    if r > 3.6:
        return mul(B.COPPER, 0.9 if y > cy else 1.05)
    if (y, x) in EYES:
        return B.AETHER_L if (y, x) in GLINT else B.AETHER
    if y == 5 and 2 <= x <= 5:
        return B.IRON_L if x % 2 else B.IRON                                       # grille mouth
    return mix(B.IRON_D, B.GLASS, 0.18 if y > 1 else 0.35)


EYES = {(2, 1), (2, 2), (3, 1), (3, 2), (2, 5), (2, 6), (3, 5), (3, 6)}
GLINT = {(2, 1), (2, 5)}


def visor_glow(f, x, y, w, h):
    if f == "front" and (y, x) in EYES:
        return B.AETHER_L if (y, x) in GLINT else B.AETHER
    return None


def wave(anim, part, length, amp, phase=0.0, base=(0, 0, 0), kind="rot", n=8):
    """A seamless sine loop: base + amp * sin(2 pi (t / length + phase))."""
    keys = []
    for i in range(n + 1):
        s = math.sin(2 * math.pi * (i / n + phase))
        keys.append((round(length * i / n, 4), tuple(round(base[k] + amp[k] * s, 3) for k in range(3))))
    getattr(anim, kind)(part, *keys)


def build():
    m = Model("brass_golem", seed=79, shadow=0.9, walk_speed=1.1, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -10, 0))
    m.part("chest", "body", pivot=(0, -3, 0))
    m.part("head", "chest", pivot=(0, -13.5, -1))
    m.part("key", "chest", pivot=(0, -7, 5.5))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(3.5 * sx, -10, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 5, 0))
        m.part(f"arm_{side}", "chest", pivot=(9 * sx, -11, 0), rot=(0, 0, 8 * sx))
        m.part(f"fore_{side}", f"arm_{side}", pivot=(0, 8, 0), rot=(-8, 0, -4 * sx))
        m.part(f"piston_{side}", f"fore_{side}", pivot=(0, 6, 0))
        m.part(f"stack_{side}", "chest", pivot=(4 * sx, -14, 1.5), rot=(-6, 0, 10 * sx))
        m.part(f"lid_{side}", f"stack_{side}", pivot=(0, -7, 0))

    # ---- legs: iron thighs, brass knee caps with a little piston behind, short shins, big round-toed boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2, -1, -2, 4, 6, 4, B.iron(1 + (sx > 0)))
        m.box(leg, -2.5, 3.5, -2.8, 5, 2, 2, patina(B.brass(3), 0.3, 3))         # knee cap
        m.box(leg, -0.5, 1, 1.8, 1, 5, 1, B.rod(B.IRON_L, 4))                     # knee piston rod
        m.box(shin, -1.5, 0, -1.5, 3, 2, 3, B.rod(B.COPPER, 5))
        m.box(shin, -3, 2, -3.5, 6, 3, 7, patina(B.brass(6 + (sx > 0), rivet_step=2), 0.3, 6))   # boot
        m.box(shin, -2.5, 2.5, -4.5, 5, 2, 1, B.brass(8))       # round toe cap
        m.box(shin, -3.5, 4, -3.5, 7, 1, 7, B.IRON_D)                             # the sole

    # ---- pelvis and the round boiler chest (an octagonal barrel: a wide box and a deep box)
    m.box("body", -5, -3, -3.5, 10, 4, 7, B.iron(9, rivet_step=3))
    m.box("body", -5.5, -1, -4, 11, 1, 8, B.IRON_D)                               # belt
    hoops = patina(B.bands(B.BRASS, B.BRASS_DD, every=4, seed=8), 0.35, 8)
    m.box("chest", -7.5, -12.5, -4.5, 15, 12, 9, hoops)
    m.box("chest", -6.5, -13, -5.5, 13, 13, 11, hoops)
    m.box("chest", -6, -14, -4, 12, 1, 8, B.plate(B.BRASS_L, B.BRASS, seed=9))   # shoulder deck
    # the furnace door with a heavy iron frame, hinge and latch; the fire shows through the grate
    m.box("chest", -4, -7.5, -6.2, 8, 5, 1, B.grate(fire=B.AMBER), glow=B.grate_glow())
    m.box("chest", -5, -8.5, -6.4, 10, 1, 1, B.iron(10))                          # lintel
    m.box("chest", -5, -2.5, -6.4, 10, 1, 1, B.iron(11))                          # sill
    m.box("chest", 4, -7.5, -6.6, 1, 2, 1, B.BRASS_L)                             # latch
    m.box("chest", 2.5, -12, -6, 3, 3, 1, B.gauge())                              # pressure gauge
    m.box("chest", -5.5, -12, -6, 4, 2, 1,
          lambda f_, x, y, w, h: B.CREAM if (f_ == "front" and 0 < x < w - 1 and y == 0) else B.copper(12)(f_, x, y, w, h))
    m.box("chest", -1, -12.5, -6, 2, 2, 1, B.AMBER, glow=B.AMBER)                 # the heart-lamp above the door
    # ---- the smokestacks with rattling soot lids
    for side, sx in (("r", -1), ("l", 1)):
        st, lid = f"stack_{side}", f"lid_{side}"
        m.box(st, -1.5, -6, -1.5, 3, 6, 3, B.soot(B.IRON, 12))
        m.box(st, -2, -7, -2, 4, 1, 4, B.soot(B.COPPER_D, 13))
        m.box(st, -2, -2, -2, 4, 1, 4, B.brass(14))                               # collar
        m.box(lid, -2, -1.5, -2, 4, 1, 4, {"top": B.SOOT, "*": B.IRON_D})
        m.box(lid, -0.5, -2.5, -0.5, 1, 1, 1, B.BRASS_L)                          # the knob
    # ---- the wind-up key in its back (turns around the shaft)
    m.box("key", -1, -1, 0, 2, 2, 3, B.rod(B.IRON_L, 14))
    m.box("key", -5.5, -3, 3, 11, 6, 1, B.key_bow())

    # ---- head: a round copper diving helmet, a protruding porthole ring, side portholes, whistle and bulb
    m.box("head", -4, -7, -4, 8, 7, 8, visor, glow=visor_glow)
    m.box("head", -4.5, -6, -3, 9, 5, 6, patina(B.copper(16), 0.25, 16))       # rounding: the cheeks bulge out
    m.box("head", -3.5, -6.5, -4.8, 7, 7, 1, ring())                             # the porthole ring
    m.box("head", -3, -8, -3, 6, 1, 6, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=17))
    m.box("head", -0.5, -10, -0.5, 1, 2, 1, B.rod(B.BRASS_L, 18))                # whistle
    m.box("head", -1, -11, -1, 2, 1, 2, B.AMBER, glow=B.AMBER)                    # signal bulb
    m.box("head", -4.5, -0.5, -4.5, 9, 1, 9, B.brass(19, rivet_step=2))          # neck collar
    for sx in (-1, 1):
        m.box("head", 4 if sx > 0 else -5, -5, -1.5, 1, 3, 3,
              lambda f_, x, y, w, h: B.GLASS if (f_ in ("left", "right") and x == 1 and y == 1) else B.BRASS_L)

    # ---- arms: dome pauldrons, thin iron upper arms, huge banded forearms, extending piston fists
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, piston = f"arm_{side}", f"fore_{side}", f"piston_{side}"
        m.box(arm, -3.5, -3.5, -3.5, 7, 5, 7, patina(B.brass(20 + (sx > 0), rivet_step=2), 0.3, 20))
        m.box(arm, -3, -4.5, -3, 6, 1, 6, B.plate(B.BRASS_L, B.BRASS, seed=22))  # the dome top
        m.box(arm, -4, 0.5, -4, 8, 1, 8, B.BRASS_D)                                # pauldron rim
        m.box(arm, -1.5, 1.5, -1.5, 3, 6, 3, B.rod(B.IRON, 23))
        m.box(arm, -2, 6.5, -2, 4, 2, 4, B.iron(24))                               # elbow joint
        m.box(fore, -3, 0, -3, 6, 6, 6, patina(B.bands(B.COPPER, B.COPPER_D, every=3, seed=25), 0.25, 25))
        m.box(piston, -1, -1, -1, 2, 3, 2, B.rod(B.IRON_L, 26))
        m.box(piston, -3.5, 2, -3.5, 7, 5, 7, B.iron(27 + (sx > 0)))
        m.box(piston, -4, 2.5, -4, 8, 2, 1, patina(B.brass(29), 0.3, 29))         # knuckle plate

    _anims(m)
    return m


def _anims(m):
    arms = (("r", -1), ("l", 1))

    # idle: the key ticks round, the boiler breathes, the soot lids puff in turn (a little steam pressure), the
    # head bobbles a beat behind the chest, the heavy forearms sway after the shoulders
    idle = m.anim("idle", 2.0)
    idle.rot("key", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 360), "linear"))
    idle.pos("chest", (0, (0, 0, 0)), (1.0, (0, 0.6, 0)), (2.0, (0, 0, 0)))
    idle.scale("chest", (0, (1, 1, 1)), (1.0, (1.025, 0.99, 1.025)), (2.0, (1, 1, 1)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 0, 6)), (1.0, (0, 0, 6)), (1.4, (0, 0, -3)), (2.0, (0, 0, 0)))
    idle.pos("head", (0, (0, 0, 0)), (1.2, (0, 0.4, 0)), (2.0, (0, 0, 0)))
    for side, sx in arms:
        t0 = 0.4 if sx < 0 else 1.4
        idle.pos(f"lid_{side}", (0, (0, 0, 0)), (t0, (0, 0, 0)), (t0 + 0.08, (0, -1.5, 0), "linear"), (t0 + 0.3, (0, 0, 0)),
                 (2.0, (0, 0, 0)))
        idle.rot(f"lid_{side}", (0, (0, 0, 0)), (t0, (0, 0, 0)), (t0 + 0.08, (-10, 0, 8 * sx)), (t0 + 0.3, (0, 0, 0)),
                 (2.0, (0, 0, 0)))
        wave(idle, f"arm_{side}", 2.0, (-2, 0, 2 * sx), 0.0)
        wave(idle, f"fore_{side}", 2.0, (-3, 0, 0), 0.15)

    # walk: a stomping toddle; the shins fold as each boot lifts, the body rolls over the planted foot, the
    # forearms swing a beat behind the shoulders, the lids rattle on every step
    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (25, 0, 0)), (0.6, (-25, 0, 0)), (1.2, (25, 0, 0)))
    walk.rot("leg_l", (0, (-25, 0, 0)), (0.6, (25, 0, 0)), (1.2, (-25, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.9, (30, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (0.6, (0, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("arm_r", (0, (-18, 0, 0)), (0.6, (18, 0, 0)), (1.2, (-18, 0, 0)))
    walk.rot("arm_l", (0, (18, 0, 0)), (0.6, (-18, 0, 0)), (1.2, (18, 0, 0)))
    wave(walk, "fore_r", 1.2, (-12, 0, 0), 0.1, base=(-8, 0, 0))
    wave(walk, "fore_l", 1.2, (12, 0, 0), 0.1, base=(-8, 0, 0))
    walk.rot("body", (0, (0, 0, -3)), (0.3, (0, 0, 0)), (0.6, (0, 0, 3)), (0.9, (0, 0, 0)), (1.2, (0, 0, -3)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.8, 0)), (1.2, (0, 0, 0)))
    walk.rot("head", (0, (0, 0, 2)), (0.15, (0, 0, 4)), (0.75, (0, 0, -4)), (1.2, (0, 0, 2)))
    for side, sx in arms:
        walk.pos(f"lid_{side}", (0, (0, 0, 0)), (0.05, (0, -0.8, 0)), (0.2, (0, 0, 0)), (0.6, (0, 0, 0)), (0.65, (0, -0.8, 0)),
                 (0.8, (0, 0, 0)), (1.2, (0, 0, 0)))
        wave(walk, f"stack_{side}", 1.2, (0, 0, 3), 0.3)

    # punch: plants the back foot, twists the boiler away and cocks the right arm back with the forearm folded
    # while the piston hisses (0.4 s = 8 ticks), then the whole body unwinds and the fist shoots out at 0.46 s
    a = m.anim("punch", 0.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (38, -15, 0)), (0.4, (44, -18, 0)), (0.46, (-85, 10, 0), "linear"),
          (0.6, (-80, 10, 0)), (0.9, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.3, (-45, 0, 0)), (0.4, (-55, 0, 0)), (0.46, (8, 0, 0), "linear"), (0.6, (8, 0, 0)),
          (0.9, (0, 0, 0)))
    a.pos("piston_r", (0, (0, 0, 0)), (0.4, (0, 1, 0)), (0.46, (0, -5, 0), "linear"), (0.6, (0, -4, 0)), (0.75, (0, 0, 0)),
          (0.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (-4, -16, 0)), (0.4, (-6, -22, 0)), (0.46, (8, 22, 0), "linear"),
          (0.6, (6, 18, 0)), (0.9, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, 0, 1)), (0.46, (0, 0, -1.5), "linear"), (0.6, (0, 0, -1.5)), (0.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (14, 0, 0)), (0.46, (10, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (-12, 0, 0)), (0.46, (-16, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-30, 0, -10)), (0.46, (25, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.4, (-40, 0, 0)), (0.6, (-10, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (4, 18, 0)), (0.46, (-4, -16, 0), "linear"), (0.9, (0, 0, 0)))
    for side, sx in arms:
        a.pos(f"lid_{side}", (0, (0, 0, 0)), (0.46, (0, 0, 0)), (0.5, (0, -2.5, 0), "linear"), (0.75, (0, 0, 0)),
              (0.9, (0, 0, 0)))

    # slam: rises onto its toes leaning back, both fists high overhead (0.6 s = 12 ticks), then crashes them into
    # the ground at 0.68 s, knees buckling, the pistons firing, the lids blowing off their stacks
    a = m.anim("slam", 1.2)
    for side, sx in arms:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (-165, 0, -10 * sx)), (0.6, (-170, 0, -10 * sx)),
              (0.68, (-40, 0, 6 * sx), "linear"), (0.9, (-45, 0, 6 * sx)), (1.2, (0, 0, 0)))
        a.rot(f"fore_{side}", (0, (0, 0, 0)), (0.5, (-35, 0, 0)), (0.6, (-40, 0, 0)), (0.68, (0, 0, 0), "linear"),
              (1.2, (0, 0, 0)))
        a.pos(f"piston_{side}", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (0.68, (0, -5, 0), "linear"), (0.9, (0, -4, 0)),
              (1.2, (0, 0, 0)))
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.68, (-28, 0, -4 * sx), "linear"), (0.9, (-26, 0, -4 * sx)),
              (1.2, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.68, (40, 0, 0), "linear"), (0.9, (36, 0, 0)),
              (1.2, (0, 0, 0)))
        a.pos(f"lid_{side}", (0, (0, 0, 0)), (0.68, (0, 0, 0)), (0.74, (0, -4, 0), "linear"), (0.9, (0, -1, 0)),
              (1.05, (0, 0, 0)), (1.2, (0, 0, 0)))
        a.rot(f"lid_{side}", (0, (0, 0, 0)), (0.68, (0, 0, 0)), (0.8, (-25, 0, 20 * sx)), (1.05, (0, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (0.68, (24, 0, 0), "linear"), (0.9, (20, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-18, 0, 0)), (0.68, (10, 0, 0), "linear"), (0.75, (16, 0, 0)), (1.2, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 1.5, 0)), (0.68, (0, -2.5, 0), "linear"), (0.9, (0, -2, 0)), (1.2, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (0.6, (0, 0, 540), "linear"), (1.2, (0, 0, 720), "linear"))

    # cheer: a happy whistle when built or repaired, arms up waving, two little hops, the lids tooting
    a = m.anim("cheer", 1.4)
    for side, sx in arms:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.3, (-155, 0, 32 * sx)), (0.55, (-145, 0, 42 * sx)), (0.8, (-155, 0, 32 * sx)),
              (1.05, (-145, 0, 42 * sx)), (1.4, (0, 0, 0)))
        a.rot(f"fore_{side}", (0, (0, 0, 0)), (0.3, (0, 0, -20 * sx)), (0.55, (0, 0, 20 * sx)), (0.8, (0, 0, -20 * sx)),
              (1.05, (0, 0, 20 * sx)), (1.4, (0, 0, 0)))
        t0 = 0.45 if sx < 0 else 0.75
        a.pos(f"lid_{side}", (0, (0, 0, 0)), (t0, (0, 0, 0)), (t0 + 0.06, (0, -2, 0), "linear"), (t0 + 0.2, (0, 0, 0)),
              (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.45, (0, 3, 0)), (0.6, (0, 0, 0)), (0.75, (0, 3, 0)), (0.9, (0, 0, 0)),
          (1.4, (0, 0, 0)))
    for side in ("r", "l"):
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (0, 0, 0)), (0.75, (20, 0, 0)),
              (0.9, (0, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-12, 0, 10)), (0.7, (-12, 0, -10)), (1.0, (-12, 0, 10)), (1.4, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (1.4, (0, 0, 1080), "linear"))
