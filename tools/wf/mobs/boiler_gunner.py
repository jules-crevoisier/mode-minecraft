"""Boiler Gunner (Canonnier-chaudière): a gun crew of one, left aboard the Walking Fortress Wreck, about 2.3 blocks.

Silhouette idea: a boiler that took up artillery. Its whole torso is an upright riveted iron boiler drum bound with
brass hoops, a glowing firebox door low on its belly. Its head is a squat brass dome with one big pressure-gauge eye,
the needle twitching. A tall soot-black smokestack with a spark-arrester cage rises from its back between two small
exhaust pipes. Its right arm IS a flak cannon: a thick barrel with a slotted brass muzzle brake and a shell drum
under the breech, braced by a pipe from the boiler. The left arm ends in a heavy coal-shovel hand. Two short piston
legs on round elephant feet carry it slowly. It plants its feet and takes aim before every shot (the gauge climbs
to red), belches fire from the firebox at anyone who gets close, and stamps the deck.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B
from . import folkkit as K

IRON = (66, 64, 68)
IRON_L = (112, 110, 112)
IRON_D = (36, 34, 38)
SOOT = (26, 24, 26)
FIRE = (255, 120, 30)
FIRE_L = (255, 220, 110)
FIRE_D = (170, 50, 16)
RED = (180, 40, 30)
GLASS = (200, 226, 220)
CREAM = B.CREAM


def iron(seed=0, step=3):
    return B.plate(IRON, IRON_D, IRON_L, rivet=B.BRASS, seed=seed, rivet_step=step)


def boiler(seed=0):
    """The drum: iron plates, a brass hoop every five rows, rivet lines, rust tears under the rivets, soot rising."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return iron(seed)(face, x, y, w, h)
        if y % 5 == 0:
            return B.BRASS_L if x % 3 == 1 else B.BRASS                                      # hoop with rivets
        if y % 5 == 1 and x % 3 == 1:
            return mix(IRON, (130, 70, 40), 0.5)                                            # rust tear
        if x % 6 == 0:
            return IRON_D                                                                    # plate seam
        c = mul(IRON, 1.12 - 0.25 * ((y % 5) / 5) + (B.n(x, y, seed) - 0.5) * 0.08)
        if y < 3:
            c = mix(c, SOOT, 0.4)
        return c
    return f


def build():
    m = Model("boiler_gunner", seed=1013, shadow=0.85, walk_speed=0.7, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-4, -9, 0))
    m.part("shin_r", "leg_r", pivot=(0, 5, 0))
    m.part("leg_l", "bone", pivot=(4, -9, 0))
    m.part("shin_l", "leg_l", pivot=(0, 5, 0))
    m.part("body", "bone", pivot=(0, -9, 0))
    m.part("head", "body", pivot=(0, -20, -0.5))
    m.part("needle", "head", pivot=(0, -3, -4.7))
    m.part("door", "body", pivot=(-3, -6, -5.6))
    m.part("stack", "body", pivot=(0, -18, 4))
    m.part("arm_r", "body", pivot=(-8.5, -17, 0), rot=(-10, 0, 0))
    m.part("cannon", "arm_r", pivot=(-1, 6, -1), rot=(100, 0, 0))
    m.part("barrel", "cannon", pivot=(0, 0, 0))
    m.part("arm_l", "body", pivot=(8.5, -17, 0), rot=(-6, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0.5, 6, 0), rot=(-20, 0, 0))
    m.part("shovel", "forearm_l", pivot=(0, 6, 0))

    # ------------------------------------------------------------------ legs: short pistons, elephant feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, -1, -2.5, 5, 6, 5, iron(1 + sx))
        m.box(leg, -3, -1.5, -3, 6, 2, 6, B.brass(2 + sx))
        m.box(shin, -1.5, 0, -1.5, 3, 2, 3, B.rod((180, 180, 186), 3 + sx))
        m.box(shin, -3, 2, -3, 6, 2, 6, iron(4 + sx))
        m.box(shin, -3.5, 3, -3.5, 7, 1, 7, {"*": IRON_D, "top": IRON})
        for k in range(3):
            m.box(shin, -2.5 + k * 2, 3, -4, 1, 1, 1, B.BRASS_D)                              # toe bolts

    # ------------------------------------------------------------------ body: the boiler drum
    m.box("body", -6, -20, -5, 12, 19, 10, boiler(10))
    m.box("body", -5, -21, -4, 10, 1, 8, iron(11))                                          # the drum's top plate
    m.box("body", -6.5, -2, -5.5, 13, 2, 11, iron(12))                                       # base ring
    m.box("body", -5, -1, -4, 10, 1, 8, IRON_D)
    # the firebox: a door frame, the grate glowing behind the door
    m.box("body", -3.5, -7, -5.4, 7, 6, 1, B.grate(IRON_D, SOOT, FIRE), glow={"front": B.grate_glow(FIRE, FIRE_L), "*": None})
    m.box("door", 0, 0, -0.5, 6, 5, 1, {"front": lambda f_, x, y, w, h: B.BRASS if x in (0, w - 1) or y in (0, h - 1)
                                         else (IRON_D if (x + y) % 2 else IRON), "*": IRON_D,
                                         "back": lambda f_, x, y, w, h: FIRE_D})
    m.box("door", 4.5, 2, -1.3, 1, 1, 1, B.BRASS_L)                                          # door latch
    # pipes and a valve wheel on the front of the drum, a coal chute on the side
    m.box("body", 3.5, -18, -5.6, 1, 10, 1, B.rod(B.COPPER, 13))
    m.box("body", 2.5, -12, -6.4, 3, 3, 1, B.cog(RED, mul(RED, 0.6), teeth=6, hub=0.3, faces=("front", "back")))
    m.box("body", -5, -18, -5.6, 3, 2, 1, B.gauge())
    m.box("body", 6, -13, -2, 2, 5, 4, iron(14))                                             # coal chute
    m.box("body", -8, -18, -2, 2, 4, 4, iron(15))                                            # cannon mount
    # shell rack strapped on the back
    for k in range(4):
        m.box("body", -4.5 + k * 2.2, -12, 5, 2, 5, 2, {"*": B.BRASS, "top": RED, "bottom": B.BRASS_D})
    m.box("body", -5, -10, 5.5, 10, 1, 2, (90, 54, 34), grow=0.15)

    # ------------------------------------------------------------------ head: a brass dome with one big gauge eye
    m.box("head", -4, -4, -4, 8, 4, 8, B.brass(20))
    m.box("head", -3, -6, -3, 6, 2, 6, B.brass(21))
    m.box("head", -1, -7, -1, 2, 1, 2, B.BRASS_L)                                            # the whistle
    m.box("head", -0.5, -9, -0.5, 1, 2, 1, B.BRASS_D)

    def dial(f_, x, y, w, h):
        if f_ != "front":
            return B.BRASS_D
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if r > cx + 0.3:
            return None
        if r > cx - 0.8:
            return B.BRASS_L if y < cy else B.BRASS
        if y <= 1 and x >= w - 3:
            return RED                                                                       # the red zone
        if r > cx - 1.6 and (x + y) % 2 == 0:
            return IRON_D                                                                    # tick marks
        return CREAM
    m.box("head", -3, -6, -4.5, 6, 6, 1, dial, glow={"front": lambda f_, x, y, w, h:
          (255, 236, 190) if ((x - 2.5) ** 2 + (y - 2.5) ** 2) ** 0.5 < 1.6 else None, "*": None})
    m.box("needle", -0.5, -2, -0.3, 1, 2, 1, RED)
    m.box("head", -5, -3, -1.5, 1, 2, 3, B.BRASS_D)                                          # ear valves
    m.box("head", 4, -3, -1.5, 1, 2, 3, B.BRASS_D)

    # ------------------------------------------------------------------ smokestack with a spark arrester, side pipes
    m.box("stack", -1.5, -14, -1.5, 3, 14, 3, B.soot(IRON, 30))
    m.box("stack", -2, -6, -2, 4, 1, 4, B.BRASS_D)
    m.box("stack", -2.5, -18, -2.5, 5, 4, 5, {"*": lambda f_, x, y, w, h: None if (x % 2 and 0 < y < h - 1) else SOOT,
                                              "top": SOOT, "bottom": SOOT},
          glow={"*": lambda f_, x, y, w, h: FIRE_D if (x % 2 and y == h - 2) else None})   # the spark cage
    m.box("body", -5, -24, 3, 2, 6, 2, B.soot(B.COPPER, 31))
    m.box("body", 3, -23, 3, 2, 5, 2, B.soot(B.COPPER, 32))

    # ------------------------------------------------------------------ the flak cannon (right arm)
    m.box("arm_r", -2, -1, -2, 4, 5, 4, iron(40))
    m.box("arm_r", -2.5, -2, -2.5, 5, 3, 5, B.brass(41))
    m.box("arm_r", -1.5, 4, -1.5, 3, 3, 3, IRON_D)
    m.box("cannon", -2.5, -2, -2.5, 5, 7, 5, iron(42, step=2))                                 # breech block
    m.box("cannon", -2, 4, -4.5, 4, 4, 3, {"*": B.BRASS, "top": B.BRASS_L, "front": lambda f_, x, y, w, h:
                                           RED if (x + y) % 3 == 0 else B.BRASS_D})          # shell drum
    m.box("barrel", -1.5, -12, -1.5, 3, 10, 3, B.rod(IRON_L, 43))
    m.box("barrel", -2, -15, -2, 4, 4, 4, {"*": lambda f_, x, y, w, h: B.BRASS_D if y in (1, 2) and x % 2 else B.BRASS,
                                          "top": lambda f_, x, y, w, h: SOOT if 0 < x < w - 1 and 0 < y < h - 1 else B.BRASS_L,
                                          "bottom": B.BRASS_D})                               # slotted muzzle brake
    m.box("barrel", -2, -6, -2, 4, 1, 4, B.BRASS_D)
    m.box("barrel", -0.5, -14, 2, 1, 1, 1, B.BRASS_L)                                          # foresight

    # ------------------------------------------------------------------ the shovel hand (left arm)
    m.box("arm_l", -2, -1, -2, 4, 6, 4, iron(50))
    m.box("arm_l", -2.5, -2, -2.5, 5, 3, 5, B.brass(51))
    m.box("forearm_l", -1.5, 0, -1.5, 3, 6, 3, iron(52))
    m.box("shovel", -0.5, 0, -0.5, 1, 3, 1, K.wood((120, 86, 52), (80, 56, 34), seed=53))
    m.box("shovel", -3, 3, -3, 6, 6, 1, {"front": lambda f_, x, y, w, h: SOOT if y > 3 and (x + y) % 2 else IRON,
                                         "*": IRON_D})                                       # the blade
    m.box("shovel", -3, 8, -3, 6, 1, 3, IRON_D)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, -0.4, 0)), (3.0, (0, 0, 0)))
    idle.rot("needle", (0, (0, 0, 0)), (0.4, (0, 0, 30)), (0.6, (0, 0, 10)), (1.6, (0, 0, -20)), (1.8, (0, 0, -5)),
             (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (0, 12, 0)), (2.0, (0, -10, 0)), (3.0, (0, 0, 0)))
    idle.scale("stack", (0, (1, 1, 1)), (0.2, (1.04, 1.0, 1.04)), (0.4, (1, 1, 1)), (1.6, (1, 1, 1)), (1.8, (1.04, 1.0, 1.04)),
               (2.0, (1, 1, 1)), (3.0, (1, 1, 1)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (18, 0, 0)), (0.8, (-18, 0, 0)), (1.6, (18, 0, 0)))
    walk.rot("leg_l", (0, (-18, 0, 0)), (0.8, (18, 0, 0)), (1.6, (-18, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.4, (0, 0, 0)), (1.2, (22, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.4, (22, 0, 0)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, 5)), (0.8, (0, 0, -5)), (1.6, (0, 0, 5)))                       # a ponderous rock
    walk.pos("body", (0, (0, 0, 0)), (0.4, (0, 0.9, 0)), (0.8, (0, 0, 0)), (1.2, (0, 0.9, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, 0)), (0.8, (-10, 0, 0)), (1.6, (10, 0, 0)))
    walk.rot("needle", (0, (0, 0, -10)), (0.8, (0, 0, 10)), (1.6, (0, 0, -10)))

    # flak: plants its feet, the cannon swings up to aim while the gauge climbs into the red (1.0 s telegraph: the aim
    # locks at 0.75 s), then the shot (at 1.0 s = 20 ticks): the barrel kicks back, the whole body rocks
    a = m.anim("flak", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (1.0, (-36, 0, 0)), (1.05, (-56, 0, 0), "linear"), (1.3, (-44, 0, 0)),
          (1.8, (0, 0, 0)))
    a.rot("cannon", (0, (0, 0, 0)), (0.6, (0, 0, 4)), (1.0, (0, 0, 4)), (1.8, (0, 0, 0)))
    a.pos("barrel", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.03, (0, -3, 0), "linear"), (1.4, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("needle", (0, (0, 0, 0)), (0.3, (0, 0, 40)), (0.6, (0, 0, 70)), (0.9, (0, 0, 95)), (0.95, (0, 0, 88)),
          (1.0, (0, 0, 100)), (1.1, (0, 0, -20)), (1.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-6, 14, 0)), (1.0, (-6, 14, 0)), (1.05, (-14, 10, 0), "linear"), (1.3, (-4, 8, 0)),
          (1.8, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, -1, 0)), (1.0, (0, -1, 0)), (1.05, (0, -0.5, 2), "linear"), (1.3, (0, -1, 0.5)),
          (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-6, -14, 0)), (1.0, (-6, -14, 0)), (1.3, (4, -8, 0)), (1.8, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.5, (-6 * s, 0, 12 * s)), (1.4, (-6 * s, 0, 12 * s)), (1.8, (0, 0, 0)))
    a.scale("stack", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.05, (1.15, 0.9, 1.15)), (1.3, (1, 1, 1)), (1.8, (1, 1, 1)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-20, 0, -20)), (1.4, (-20, 0, -20)), (1.8, (0, 0, 0)))

    # belch: leans in and swings the firebox door open, the glow brightening (0.6 s telegraph), then a gout of fire
    # (from 0.6 s = 12 ticks to 1.0 s)
    a = m.anim("belch", 1.4)
    a.rot("door", (0, (0, 0, 0)), (0.5, (0, -100, 0)), (0.6, (0, -110, 0)), (1.1, (0, -110, 0)), (1.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (-8, 0, 0)), (0.6, (14, 0, 0), "linear"), (1.0, (16, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, 0, 1)), (0.6, (0, -1, -1.5), "linear"), (1.0, (0, -1, -1.5)), (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (10, 0, 20)), (1.0, (10, 0, 20)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (10, 0, -20)), (1.0, (10, 0, -20)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (0.6, (6, 0, 0)), (1.4, (0, 0, 0)))
    a.scale("stack", (0, (1, 1, 1)), (0.6, (1, 1, 1)), (0.7, (1.12, 0.92, 1.12)), (0.9, (1.06, 0.96, 1.06)), (1.4, (1, 1, 1)))

    # stomp: rocks onto its right foot and lifts the left high, the shovel raised (0.7 s telegraph), then stamps the
    # deck (at 0.7 s = 14 ticks): a shockwave
    a = m.anim("stomp", 1.3)
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (-50, 0, -10)), (0.65, (-52, 0, -10)), (0.72, (6, 0, 0), "linear"), (1.3, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.6, (40, 0, 0)), (0.72, (0, 0, 0), "linear"), (1.3, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-6, 0, -12)), (0.72, (8, 0, 6), "linear"), (0.9, (6, 0, 4)), (1.3, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (-1, 1.5, 0)), (0.72, (0, -1.5, 0), "linear"), (0.9, (0, -1, 0)), (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-120, 0, -20)), (0.72, (-30, 0, -10), "linear"), (1.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (0, 0, 20)), (0.72, (10, 0, 10)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-10, 0, 8)), (0.72, (8, 0, 0)), (1.3, (0, 0, 0)))
