"""Clockwork Spider (Araignée-horloge): a small, fast brass automaton of the badlands and the savanna highlands.

Silhouette idea: a wind-up toy gone feral. A riveted brass thorax on eight needle legs that bend at little cog
joints, a dark iron head with two big ruby lenses and copper pincers, and a banded spring barrel for an abdomen
with a big wind-up key on top that never stops turning.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

RUBY = (255, 70, 46)
RUBY_L = (255, 190, 150)


def build():
    m = Model("clockwork_spider", seed=71, shadow=0.55, walk_speed=2.2, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -6, 0))
    m.part("head", "body", pivot=(0, -1, -4))
    m.part("mand_r", "head", pivot=(-1.5, 1, -4), rot=(0, -12, 0))
    m.part("mand_l", "head", pivot=(1.5, 1, -4), rot=(0, 12, 0))
    m.part("abdomen", "body", pivot=(0, -1.5, 3.5), rot=(-14, 0, 0))
    m.part("key", "abdomen", pivot=(0, -3, 3))

    # ---- thorax: a dark iron chassis under a riveted brass shell, a copper cog turning on top, cog bosses
    m.part("crown", "body", pivot=(0, -4, 0))
    m.box("body", -4, -2, -4, 8, 3, 8, B.iron(1, rivet_step=3))
    m.box("body", -4.5, -3, -4.5, 9, 1, 9, B.brass(2))
    m.box("body", -3.5, -4, -3.5, 7, 1, 7, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=3))
    m.box("body", -3, 1, -3, 6, 1, 6, B.iron(4))
    m.box("crown", -2.5, -1, -2.5, 5, 1, 5, B.cog(B.COPPER, B.COPPER_D, teeth=8, hub=0.2, faces=("top", "bottom"), edges=True))
    m.box("crown", -0.5, -2, -0.5, 1, 1, 1, B.BRASS_L)
    for sx in (-1, 1):
        m.box("body", 4 if sx > 0 else -5, -2.5, -2.5, 1, 5, 5,
              B.cog(B.COPPER, B.COPPER_D, teeth=8, hub=0.25, faces=("left", "right")))

    # ---- head: iron mask, two big ruby lenses and two small ones, a brass brow
    def face(f, x, y, w, h):
        if f == "front":
            if y == 0:
                return B.BRASS
            return mul(B.IRON, 1.05 - 0.1 * y / h)
        return B.iron(5)(f, x, y, w, h)
    m.box("head", -2.5, -2, -4, 5, 4, 4, face)
    m.box("head", -3, -2.5, -3.5, 6, 1, 3, B.brass(6))                               # brow plate
    for sx in (-1, 1):
        x = 0.2 if sx > 0 else -2.2
        m.box("head", x, -1.4, -4.4, 2, 2, 1, B.lens(RUBY, B.BRASS, RUBY_L), glow=B.lens_glow(RUBY, RUBY_L))
        m.box("head", 1.6 * sx - 0.5, -2.9, -3.8, 1, 1, 1, RUBY, glow={"front": RUBY, "*": None})
    # copper pincers, hooked inward
    for side, sx in (("r", -1), ("l", 1)):
        part = f"mand_{side}"
        m.box(part, -0.5, -0.5, -3, 1, 1, 3, B.copper(7 + sx))
        m.box(part, -0.5 - sx * 0.8, -0.5, -4, 1, 1, 1, B.COPPER_D)

    # ---- abdomen: the spring barrel, hooped and riveted, with an iron end cap and an exhaust nub
    m.box("abdomen", -3, -3, 0, 6, 6, 6, B.bands(B.BRASS, B.BRASS_DD, every=2, seed=8))
    m.box("abdomen", -2, -2, 6, 4, 4, 1, B.iron(9))
    m.box("abdomen", -0.5, -0.5, 7, 1, 1, 2, B.soot(B.COPPER, 10))
    # ---- the wind-up key: an iron shaft and a two-lobed brass bow standing up from the barrel
    m.box("key", -0.5, -4, -0.5, 1, 4, 1, B.rod(B.IRON_L, 11))

    m.box("key", -5.5, -8, -0.5, 11, 6, 1, B.key_bow())

    # ---- eight needle legs: an iron femur rising from a cog hip, a cog knee, a long brass shin
    for side, sx in (("r", -1), ("l", 1)):
        for i, (z, yaw) in enumerate(((-3, 34), (-1, 12), (1, -12), (3, -34))):
            leg, foot = f"leg_{side}{i}", f"foot_{side}{i}"
            m.part(leg, "body", pivot=(4 * sx, -0.5, z), rot=(0, yaw * sx, -32 * sx))
            m.part(foot, leg, pivot=(6 * sx, 0, 0), rot=(0, 0, 50 * sx))
            m.box(leg, 0 if sx > 0 else -6, -0.5, -0.5, 6, 1, 1, B.rod(B.IRON, 20 + i))
            m.box(leg, (5 if sx > 0 else -6), -1, -1, 1, 2, 2,
                  B.cog(B.BRASS, B.BRASS_D, teeth=6, hub=0.0, faces=("left", "right"), edges=True))
            m.box(foot, -0.5, 0, -0.5, 1, 8, 1, B.rod(mix(B.BRASS, B.BRASS_D, 0.4), 30 + i))
            m.box(foot, -0.5, 8, -0.5, 1, 2, 1, B.rod(B.IRON_D, 40 + i))

    # ------------------------------------------------------------------ animations
    legs = [(f"leg_{s}{i}", f"foot_{s}{i}", sx, i) for s, sx in (("r", -1), ("l", 1)) for i in range(4)]

    idle = m.anim("idle", 2.0)
    idle.rot("key", (0, (0, 0, 0), "linear"), (2.0, (0, 360, 0), "linear"))
    idle.rot("crown", (0, (0, 0, 0), "linear"), (2.0, (0, -720, 0), "linear"))
    idle.pos("body", (0, (0, 0, 0)), (0.5, (0, 0.4, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0.4, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.5, (3, -8, 0)), (1.2, (-2, 7, 0)), (2.0, (0, 0, 0)))
    idle.rot("mand_r", (0, (0, 0, 0)), (0.15, (0, -20, 0)), (0.3, (0, 0, 0)), (1.1, (0, 0, 0)), (1.25, (0, -16, 0)),
             (1.4, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("mand_l", (0, (0, 0, 0)), (0.15, (0, 20, 0)), (0.3, (0, 0, 0)), (1.1, (0, 0, 0)), (1.25, (0, 16, 0)),
             (1.4, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("abdomen", (0, (0, 0, 0)), (1.0, (-3, 0, 0)), (2.0, (0, 0, 0)))

    # walk: quick alternating tetrapod gait (L0 R1 L2 R3 against R0 L1 R2 L3)
    walk = m.anim("walk", 0.5)
    for leg, foot, sx, i in legs:
        phase = (i + (0 if sx > 0 else 1)) % 2
        sw = 18 if phase == 0 else -18
        lift = -16 * sx
        if phase == 0:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.125, (0, 0, lift)), (0.25, (0, -sw * sx, 0)), (0.5, (0, sw * sx, 0)))
        else:
            walk.rot(leg, (0, (0, sw * sx, 0)), (0.25, (0, -sw * sx, 0)), (0.375, (0, 0, lift)), (0.5, (0, sw * sx, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.125, (0, 0.5, 0)), (0.25, (0, 0, 0)), (0.375, (0, 0.5, 0)), (0.5, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, -2)), (0.25, (0, 0, 2)), (0.5, (0, 0, -2)))
    walk.rot("abdomen", (0, (0, 5, 0)), (0.25, (0, -5, 0)), (0.5, (0, 5, 0)))

    # bite: rear back with pincers wide (0.25 s = 5 ticks), snap, recover
    a = m.anim("bite", 0.6)
    a.rot("head", (0, (0, 0, 0)), (0.2, (-25, 0, 0)), (0.25, (-28, 0, 0)), (0.32, (16, 0, 0), "linear"), (0.42, (10, 0, 0)),
          (0.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.25, (-12, 0, 0)), (0.32, (6, 0, 0), "linear"), (0.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.25, (0, 1, 1.5)), (0.32, (0, -0.5, -2.5), "linear"), (0.42, (0, -0.5, -2.5)),
          (0.6, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.25, (0, -45, 0)), (0.32, (0, 22, 0), "linear"), (0.42, (0, 18, 0)), (0.6, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.25, (0, 45, 0)), (0.32, (0, -22, 0), "linear"), (0.42, (0, -18, 0)), (0.6, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        if i == 0:
            a.rot(leg, (0, (0, 0, 0)), (0.25, (0, 0, -28 * sx)), (0.32, (0, 12 * sx, 6 * sx), "linear"), (0.6, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (0.6, (0, 360, 0), "linear"))

    # leap: crouch while the key whirs (0.35 s = 7 ticks), spring with the front legs up, land
    a = m.anim("leap", 1.0)
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -2.5, 1.5)), (0.35, (0, -2.5, 1.5)), (0.45, (0, 3, -3), "linear"),
          (0.75, (0, 2, -3)), (0.85, (0, -1, -1.5)), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (10, 0, 0)), (0.45, (-24, 0, 0), "linear"), (0.75, (-8, 0, 0)), (0.85, (6, 0, 0)),
          (1.0, (0, 0, 0)))
    a.rot("abdomen", (0, (0, 0, 0)), (0.35, (-12, 0, 0)), (0.45, (22, 0, 0), "linear"), (0.85, (0, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (0.35, (0, 720, 0), "linear"), (1.0, (0, 1080, 0), "linear"))
    a.rot("mand_r", (0, (0, 0, 0)), (0.35, (0, -40, 0)), (0.75, (0, -40, 0)), (0.85, (0, 16, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.35, (0, 40, 0)), (0.75, (0, 40, 0)), (0.85, (0, -16, 0), "linear"), (1.0, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        if i < 2:
            a.rot(leg, (0, (0, 0, 0)), (0.35, (0, 0, 14 * sx)), (0.45, (0, 24 * sx, -42 * sx), "linear"),
                  (0.75, (0, 24 * sx, -38 * sx)), (0.85, (0, 0, 10 * sx)), (1.0, (0, 0, 0)))
            a.rot(foot, (0, (0, 0, 0)), (0.45, (0, 0, -30 * sx), "linear"), (0.75, (0, 0, -24 * sx)), (1.0, (0, 0, 0)))
        else:
            a.rot(leg, (0, (0, 0, 0)), (0.35, (0, 0, 18 * sx)), (0.45, (0, -28 * sx, -6 * sx), "linear"),
                  (0.75, (0, -24 * sx, -10 * sx)), (0.85, (0, 0, 8 * sx)), (1.0, (0, 0, 0)))
    return m
