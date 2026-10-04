"""Brass Golem (Golem de laiton): the friendly automaton a player builds from two Blocks of Brass and a Clockwork
Heart. About 2.3 blocks tall.

Silhouette idea: a walking boiler with a heart. A barrel chest of brass hoops with a glowing furnace grate for a
belly, a small copper diving-helmet head with two round aether eyes and a whistle on top, long arms ending in
piston fists, short stubby legs in big brass boots, two little smokestacks on the shoulders and a huge wind-up key
turning in its back.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B


def build():
    m = Model("brass_golem", seed=79, shadow=0.9, walk_speed=1.1, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -10, 0))
    m.part("chest", "body", pivot=(0, -3, 0))
    m.part("head", "chest", pivot=(0, -13, -1))
    m.part("key", "chest", pivot=(0, -7, 5))
    m.part("leg_r", "bone", pivot=(-3.5, -10, 0))
    m.part("leg_l", "bone", pivot=(3.5, -10, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "chest", pivot=(8.5 * sx, -11, 0), rot=(0, 0, 6 * sx))
        m.part(f"fore_{side}", f"arm_{side}", pivot=(0, 8, 0))
        m.part(f"piston_{side}", f"fore_{side}", pivot=(0, 6, 0))

    # ---- legs: iron thighs, brass knee caps, copper piston shins, big brass boots
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"
        m.box(leg, -2, 0, -2, 4, 5, 4, B.iron(1 + (sx > 0)))
        m.box(leg, -2.5, 3, -2.6, 5, 2, 1, B.brass(3))
        m.box(leg, -1.5, 5, -1.5, 3, 3, 3, B.rod(B.COPPER, 4))
        m.box(leg, -2.5, 8, -3.5, 5, 2, 6, B.brass(5 + (sx > 0)))
        m.box(leg, -2, 7, -2, 4, 1, 4, B.BRASS_D)

    # ---- pelvis and the boiler chest
    m.box("body", -5, -3, -3, 10, 3, 6, B.iron(7, rivet_step=3))
    m.box("chest", -7, -13, -5, 14, 13, 10, B.bands(B.BRASS, B.BRASS_DD, every=4, seed=8))
    m.box("chest", -6, -14, -4, 12, 1, 8, B.plate(B.BRASS_L, B.BRASS, seed=9))           # shoulder deck
    m.box("chest", -4, -7, -5.6, 8, 5, 1, B.grate(fire=B.AMBER), glow=B.grate_glow())  # the furnace belly
    m.box("chest", -5, -8, -5.8, 10, 1, 1, B.iron(10))                                  # grate lintel
    m.box("chest", 3, -12, -5.5, 3, 3, 1, B.gauge())                                    # pressure gauge
    m.box("chest", -6, -12, -5.5, 3, 2, 1, B.copper(11))                                # name plate
    m.box("chest", -4, -1, -5.4, 8, 1, 1, B.IRON_D)                                     # belt
    for sx in (-1, 1):                                                                   # shoulder smokestacks
        m.box("chest", (3 if sx > 0 else -5), -18, 1, 2, 4, 2, B.soot(B.IRON, 12))
        m.box("chest", (2.5 if sx > 0 else -5.5), -19, 0.5, 3, 1, 3, B.soot(B.COPPER_D, 13))
    # ---- the wind-up key in its back (turns around the shaft)
    m.box("key", -1, -1, 0, 2, 2, 3, B.rod(B.IRON_L, 14))
    m.box("key", -5.5, -3, 3, 11, 6, 1, B.key_bow())

    # ---- head: a copper diving helmet, a round porthole with two aether eyes, a whistle on top
    def visor(f, x, y, w, h):
        if f != "front":
            return B.copper(15)(f, x, y, w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = ((x - cx) ** 2 + ((y - cy) * 1.15) ** 2) ** 0.5
        if r > 3.6:
            return mul(B.COPPER, 0.9 if y > cy else 1.05)
        if r > 2.9:
            return B.BRASS_L if y < cy else B.BRASS                                      # porthole ring
        if y in (2, 3) and x in (1, 2, 5, 6):
            return B.AETHER_L if (y, x) in ((2, 1), (2, 5)) else B.AETHER                # round eyes with a glint
        if y == 5 and 2 <= x <= 5:
            return B.IRON_L if x % 2 else B.IRON                                          # grille mouth
        return mix(B.IRON_D, B.GLASS, 0.18)
    m.box("head", -4, -7, -4, 8, 7, 8, visor,
          glow={"front": lambda f, x, y, w, h: (B.AETHER_L if (y, x) in ((2, 1), (2, 5)) else B.AETHER)
                     if (y in (2, 3) and x in (1, 2, 5, 6)) else None})
    m.box("head", -3, -8, -3, 6, 1, 6, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=16))
    m.box("head", -0.5, -10, -0.5, 1, 2, 1, B.rod(B.BRASS_L, 17))                        # whistle
    m.box("head", -1, -11, -1, 2, 1, 2, B.AMBER, glow=B.AMBER)                            # signal bulb
    for sx in (-1, 1):                                                                   # ear bolts
        m.box("head", (4 if sx > 0 else -5), -4, -1, 1, 2, 2, B.BRASS_L)

    # ---- arms: brass pauldrons, iron upper arms, copper forearms, extending piston fists
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, piston = f"arm_{side}", f"fore_{side}", f"piston_{side}"
        m.box(arm, -3, -3, -3, 6, 5, 6, B.brass(18 + (sx > 0), rivet_step=2))
        m.box(arm, -1.5, 2, -1.5, 3, 6, 3, B.rod(B.IRON, 20))
        m.box(fore, -2.5, 0, -2.5, 5, 6, 5, B.bands(B.COPPER, B.COPPER_D, every=3, seed=21))
        m.box(piston, -1, -1, -1, 2, 3, 2, B.rod(B.IRON_L, 22))
        m.box(piston, -3, 2, -3, 6, 5, 6, B.iron(23 + (sx > 0)))
        m.box(piston, -3.5, 2.5, -3.5, 7, 2, 1, B.brass(25))                              # knuckle plate

    # ------------------------------------------------------------------ animations
    arms = (("r", -1), ("l", 1))

    idle = m.anim("idle", 2.0)
    idle.rot("key", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 360), "linear"))
    idle.pos("chest", (0, (0, 0, 0)), (1.0, (0, 0.6, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 0, 6)), (1.0, (0, 0, 6)), (1.4, (0, 0, -3)), (2.0, (0, 0, 0)))
    for side, sx in arms:
        idle.rot(f"arm_{side}", (0, (0, 0, 0)), (1.0, (-2, 0, 2 * sx)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (25, 0, 0)), (0.6, (-25, 0, 0)), (1.2, (25, 0, 0)))
    walk.rot("leg_l", (0, (-25, 0, 0)), (0.6, (25, 0, 0)), (1.2, (-25, 0, 0)))
    walk.rot("arm_r", (0, (-18, 0, 0)), (0.6, (18, 0, 0)), (1.2, (-18, 0, 0)))
    walk.rot("arm_l", (0, (18, 0, 0)), (0.6, (-18, 0, 0)), (1.2, (18, 0, 0)))
    walk.rot("body", (0, (0, 0, -3)), (0.3, (0, 0, 0)), (0.6, (0, 0, 3)), (0.9, (0, 0, 0)), (1.2, (0, 0, -3)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.8, 0)), (1.2, (0, 0, 0)))
    walk.rot("head", (0, (0, 0, 3)), (0.6, (0, 0, -3)), (1.2, (0, 0, 3)))

    # punch: the right arm cocks back and the piston hisses (0.4 s = 8 ticks), then the fist shoots out
    a = m.anim("punch", 0.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (35, -10, 0)), (0.4, (38, -10, 0)), (0.46, (-85, 10, 0), "linear"),
          (0.6, (-80, 10, 0)), (0.9, (0, 0, 0)))
    a.pos("piston_r", (0, (0, 0, 0)), (0.4, (0, 1, 0)), (0.46, (0, -5, 0), "linear"), (0.6, (0, -4, 0)), (0.75, (0, 0, 0)),
          (0.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.4, (0, -18, 0)), (0.46, (6, 20, 0), "linear"), (0.6, (4, 16, 0)), (0.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-20, 0, 0)), (0.46, (20, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (0, 14, 0)), (0.46, (0, -14, 0), "linear"), (0.9, (0, 0, 0)))

    # slam: both fists rise overhead (0.6 s = 12 ticks) and crash into the ground, pistons firing
    a = m.anim("slam", 1.2)
    for side, sx in arms:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (-165, 0, -10 * sx)), (0.6, (-170, 0, -10 * sx)),
              (0.68, (-40, 0, 6 * sx), "linear"), (0.9, (-45, 0, 6 * sx)), (1.2, (0, 0, 0)))
        a.pos(f"piston_{side}", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (0.68, (0, -5, 0), "linear"), (0.9, (0, -4, 0)),
              (1.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-14, 0, 0)), (0.68, (22, 0, 0), "linear"), (0.9, (18, 0, 0)), (1.2, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 1, 0)), (0.68, (0, -2, 0), "linear"), (0.9, (0, -1.5, 0)), (1.2, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (0.6, (0, 0, 540), "linear"), (1.2, (0, 0, 720), "linear"))

    # cheer: a happy whistle when built or repaired, arms up, a little hop
    a = m.anim("cheer", 1.4)
    for side, sx in arms:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.3, (-155, 0, 32 * sx)), (0.55, (-145, 0, 42 * sx)), (0.8, (-155, 0, 32 * sx)),
              (1.05, (-145, 0, 42 * sx)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.45, (0, 3, 0)), (0.6, (0, 0, 0)), (0.75, (0, 3, 0)), (0.9, (0, 0, 0)),
          (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-12, 0, 10)), (0.7, (-12, 0, -10)), (1.0, (-12, 0, 10)), (1.4, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (1.4, (0, 0, 1080), "linear"))
    return m
