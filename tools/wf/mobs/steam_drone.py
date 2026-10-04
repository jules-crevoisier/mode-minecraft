"""Steam Drone (Drone à vapeur): a hovering copper boiler that hunts at night and in the Undercity.

Silhouette idea: a flying kettle. A hooped copper boiler with one big ruby eye in an iron bezel, a sooty
smokestack puffing at the back, two brass outriggers carrying spinning rotors, a little tail propeller, a rivet
gun slung under the chin and two dangling grabber claws.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

RUBY = (255, 70, 46)
RUBY_L = (255, 196, 160)
RUBY_D = (190, 30, 24)


def blade(base=B.BRASS, seed=0):
    """A rotor blade: lighter leading edge, dark tip band."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            c = mul(base, 1.1 if face == "top" else 0.75)
            if x in (0, w - 1) or x in (1, w - 2):
                c = B.IRON_D if x in (0, w - 1) else mix(c, B.IRON_D, 0.4)
            return c
        return mul(base, 0.8)
    return f


def build():
    m = Model("steam_drone", seed=73, shadow=0.45, walk_speed=1.0, walk_scale=0.6, head="hull")

    m.part("bone", pivot=(0, 24, 0))
    m.part("hull", "bone", pivot=(0, -12, 0))
    m.part("stack", "hull", pivot=(0, -5, 2))
    m.part("gun", "hull", pivot=(0, 4, -2))
    m.part("prop", "hull", pivot=(0, 0, 5))
    m.part("claw_r", "hull", pivot=(-2.5, 4.5, 1))
    m.part("claw_l", "hull", pivot=(2.5, 4.5, 1))

    # ---- the boiler: hooped copper, brass dome on top, iron belly, a big ruby eye in an iron bezel
    m.box("hull", -4, -4, -4, 8, 8, 8, B.bands(B.COPPER, B.BRASS_D, every=3, seed=1))
    m.box("hull", -3, -5, -3, 6, 1, 6, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=2))
    m.box("hull", -2, -6, -2, 4, 1, 4, B.plate(B.BRASS_L, B.BRASS, seed=3))
    m.box("hull", -3, 4, -3, 6, 1, 6, B.iron(4))
    m.box("hull", -3, -3, -5, 6, 6, 1, B.iron(5))                                  # bezel
    m.box("hull", -2, -2, -5.6, 4, 4, 1, B.lens(RUBY, B.BRASS, RUBY_L), glow=B.lens_glow(RUBY, RUBY_L))
    m.box("hull", -3.5, -4.5, -5.5, 7, 1, 1, B.brass(6))                           # brow visor
    for sx in (-1, 1):                                                               # pressure gauges
        m.box("hull", (4 if sx > 0 else -5), -2, -1, 1, 2, 2, B.gauge())
        m.box("hull", (4 if sx > 0 else -5), 1, -3, 1, 1, 6, B.iron(7))              # side rails

    # ---- smokestack
    m.box("stack", -1, -4, -1, 2, 4, 2, B.soot(B.IRON, 8))
    m.box("stack", -1.5, -5, -1.5, 3, 1, 3, B.soot(B.BRASS_D, 9))

    # ---- outriggers and rotors
    for side, sx in (("r", -1), ("l", 1)):
        arm, rotor = f"arm_{side}", f"rotor_{side}"
        m.part(arm, "hull", pivot=(4 * sx, -3, 0), rot=(0, 0, -8 * sx))
        m.part(rotor, arm, pivot=(6 * sx, -2.5, 0))
        m.box(arm, 0 if sx > 0 else -5, -0.5, -0.5, 5, 1, 1, B.rod(B.BRASS, 10))
        m.box(arm, (4.5 if sx > 0 else -7.5), -1.5, -1.5, 3, 3, 3, B.iron(11))         # nacelle
        m.box(arm, (5 if sx > 0 else -7), 1.5, -1, 2, 1, 2, B.COPPER_D)                # exhaust
        m.box(rotor, -1, -1, -1, 2, 1, 2, B.BRASS_L)                                     # hub
        m.box(rotor, -6, -0.5, -1, 12, 1, 2, blade(B.BRASS, 12))                         # blades

    # ---- tail propeller
    m.box("prop", -0.5, -0.5, 0, 1, 1, 2, B.IRON_L)
    m.box("prop", -3, -0.5, 1.5, 6, 1, 1, blade(B.COPPER, 13))
    m.box("prop", -0.5, -3, 1.4, 1, 6, 1, blade(B.COPPER, 14))

    # ---- rivet gun under the chin
    m.box("gun", -1, 0, -5, 2, 2, 6, B.iron(15))
    m.box("gun", -1.5, -0.5, -6, 3, 3, 1, {"front": lambda f, x, y, w, h: B.SOOT if (x, y) == (1, 1) else B.BRASS,
                                           "*": B.brass(16)})
    m.box("gun", -0.5, -1, -1, 1, 1, 3, B.COPPER)                                     # feed pipe

    # ---- grabber claws
    for side, sx in (("r", -1), ("l", 1)):
        c = f"claw_{side}"
        m.box(c, -0.5, 0, -0.5, 1, 4, 1, B.rod(B.IRON_L, 17))
        m.box(c, -1, 4, -1, 2, 1, 2, B.BRASS_D)
        m.box(c, -0.5 + sx * 0.5, 5, -1, 1, 2, 1, B.IRON_D)
        m.box(c, -0.5 - sx * 0.5, 5, 0, 1, 2, 1, B.IRON_D)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 1.0)
    idle.rot("rotor_r", (0, (0, 0, 0), "linear"), (1.0, (0, 1440, 0), "linear"))
    idle.rot("rotor_l", (0, (0, 0, 0), "linear"), (1.0, (0, -1440, 0), "linear"))
    idle.rot("prop", (0, (0, 0, 0), "linear"), (1.0, (0, 0, 1080), "linear"))
    idle.pos("hull", (0, (0, 0, 0)), (0.5, (0, 1.0, 0)), (1.0, (0, 0, 0)))
    idle.rot("hull", (0, (0, 0, -2)), (0.5, (2, 0, 2)), (1.0, (0, 0, -2)))
    idle.rot("claw_r", (0, (6, 0, 4)), (0.5, (-4, 0, -2)), (1.0, (6, 0, 4)))
    idle.rot("claw_l", (0, (-4, 0, -4)), (0.5, (6, 0, 2)), (1.0, (-4, 0, -4)))
    idle.pos("stack", (0, (0, 0, 0)), (0.1, (0, 0.4, 0)), (0.2, (0, 0, 0)), (1.0, (0, 0, 0)))

    # flying forward: nose down, claws trailing
    walk = m.anim("walk", 1.0)
    walk.rot("hull", (0, (10, 0, 0)), (0.5, (12, 0, 0)), (1.0, (10, 0, 0)))
    walk.rot("claw_r", (0, (-25, 0, 0)), (0.5, (-30, 0, 0)), (1.0, (-25, 0, 0)))
    walk.rot("claw_l", (0, (-28, 0, 0)), (0.5, (-22, 0, 0)), (1.0, (-28, 0, 0)))

    # shoot: wind-up (0.3 s = 6 ticks) the drone steadies and the gun cocks back, then recoil
    a = m.anim("shoot", 0.6)
    a.pos("gun", (0, (0, 0, 0)), (0.25, (0, 0, 1.0)), (0.3, (0, 0, 1.0)), (0.34, (0, 0, 2.5), "linear"),
          (0.45, (0, 0, 0.6)), (0.6, (0, 0, 0)))
    a.rot("hull", (0, (0, 0, 0)), (0.3, (4, 0, 0)), (0.34, (-10, 0, 0), "linear"), (0.6, (0, 0, 0)))
    a.pos("hull", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.34, (0, 0.5, 1.5), "linear"), (0.6, (0, 0, 0)))
    a.pos("stack", (0, (0, 0, 0)), (0.34, (0, 0, 0)), (0.38, (0, 1.0, 0), "linear"), (0.6, (0, 0, 0)))

    # dive: rise and rear up (0.5 s = 10 ticks), then plunge nose first with claws spread, recover
    a = m.anim("dive", 1.4)
    a.pos("hull", (0, (0, 0, 0)), (0.45, (0, 3, 1.5)), (0.5, (0, 3, 1.5)), (0.6, (0, 0, -3), "linear"),
          (1.0, (0, -1, -3)), (1.4, (0, 0, 0)))
    a.rot("hull", (0, (0, 0, 0)), (0.45, (-22, 0, 0)), (0.5, (-24, 0, 0)), (0.6, (40, 0, 0), "linear"),
          (1.0, (35, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("rotor_r", (0, (0, 0, 0), "linear"), (0.5, (0, 1080, 0), "linear"), (1.4, (0, 2160, 0), "linear"))
    a.rot("rotor_l", (0, (0, 0, 0), "linear"), (0.5, (0, -1080, 0), "linear"), (1.4, (0, -2160, 0), "linear"))
    for c, sx in (("claw_r", -1), ("claw_l", 1)):
        a.rot(c, (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.6, (-50, 0, 30 * sx), "linear"), (1.0, (-45, 0, 25 * sx)),
              (1.4, (0, 0, 0)))
    return m
