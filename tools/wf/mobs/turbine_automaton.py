"""Turbine Automaton (Automate à turbine): a maintenance machine of the Dam of the Drowned Valley, about 1.9 blocks tall.

Silhouette idea: a turbine that got up and walked off its shaft. A barrel-chested copper housing, green with verdigris
and streaked with old water lines, with a big six-bladed rotor turning behind a brass guard ring in its chest. A small
riveted iron head with a single amber slit sits low between two pipe-fed shoulder drums; two exhaust stacks rise from
its back. Short piston legs on wide splayed feet, and two heavy piston arms that end in flat paddle-blades. It spins
its rotor up until steam screams out of the stacks and then dashes in a straight line; up close it slams both paddles
down or vents a scalding cloud. When it breaks, its boiler bursts.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B
from . import folkkit as K

VERD = (78, 156, 138)
VERD_L = (128, 196, 172)
VERD_D = (46, 104, 94)
COPPER = B.COPPER
COPPER_D = B.COPPER_D
COPPER_L = B.COPPER_L
IRON = (70, 70, 74)
IRON_L = (120, 120, 124)
IRON_D = (38, 38, 42)
SILT = (112, 100, 76)
AMBER = (255, 172, 60)
AMBER_L = (255, 232, 160)
STEAM = (230, 236, 240)


def patina(base=COPPER, seed=0, amount=0.4, line=True):
    """Weathered copper: verdigris blooming from the seams and the bottom, a silt line where the water stood."""
    plate = B.plate(base, mul(base, 0.62), mix(base, (255, 240, 210), 0.35), seed=seed)

    def f(face, x, y, w, h):
        c = plate(face, x, y, w, h)
        if face == "bottom":
            return mix(c, VERD_D, 0.5)
        r = B.n(x // 2, (y + x % 2) // 2, seed + 3) * 0.75 + B.n(x, y, seed + 9) * 0.25
        edge = x in (0, w - 1) or (face != "top" and y in (0, h - 1))
        lim = amount * (0.7 if edge else 0.3) * (0.3 + 1.0 * (y / max(1, h)) if face != "top" else 0.5)
        if r < lim * 0.5:
            c = VERD_L if r < lim * 0.15 else VERD
        elif r < lim:
            c = mix(c, VERD_D, 0.5)
        if line and face not in ("top", "bottom") and h > 6 and y == h // 2 + (seed % 2):
            c = mix(c, SILT, 0.55)                                                     # the old water line
        return c
    return f


def iron(seed=0):
    return B.plate(IRON, IRON_D, IRON_L, rivet=B.BRASS, seed=seed)


def blade(seed=0):
    """A rotor blade: brass with a darker leading edge."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            if x in (0, w - 1):
                return B.BRASS_D
            return B.BRASS_L if y == 0 else mul(B.BRASS, 1.05 - 0.1 * (x / max(1, w)))
        return B.BRASS_D
    return f


def build():
    m = Model("turbine_automaton", seed=907, shadow=0.75, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-3.5, -9, 0))
    m.part("shin_r", "leg_r", pivot=(0, 5, 0))
    m.part("leg_l", "bone", pivot=(3.5, -9, 0))
    m.part("shin_l", "leg_l", pivot=(0, 5, 0))
    m.part("body", "bone", pivot=(0, -9, 0))
    m.part("head", "body", pivot=(0, -15, -1))
    m.part("rotor", "body", pivot=(0, -8, -4.6))
    for i in range(3):
        m.part(f"blade{i}", "rotor", rot=(0, 0, i * 60 + 15))
    m.part("arm_r", "body", pivot=(-8, -13, 0), rot=(0, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(-0.5, 6, 0), rot=(-20, 0, 0))
    m.part("paddle_r", "forearm_r", pivot=(0, 6, 0))
    m.part("arm_l", "body", pivot=(8, -13, 0), rot=(0, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(0.5, 6, 0), rot=(-20, 0, 0))
    m.part("paddle_l", "forearm_l", pivot=(0, 6, 0))
    m.part("stack_r", "body", pivot=(-3, -15, 3), rot=(-8, 0, 6))
    m.part("stack_l", "body", pivot=(3, -15, 3), rot=(-8, 0, -6))

    # ------------------------------------------------------------------ legs: pistons on splayed feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2, -1, -2, 4, 6, 4, iron(1 + sx))
        m.box(leg, -2.5, -1.5, -2.5, 5, 3, 5, patina(COPPER, 2 + sx))                     # hip drum
        m.box(shin, -1, 0, -1, 2, 3, 2, B.rod((176, 176, 180), 3 + sx))                   # polished piston rod
        m.box(shin, -1.5, -0.5, -1.5, 3, 1, 3, B.BRASS_D)
        m.box(shin, -3, 3, -4, 6, 1, 7, patina(COPPER, 4 + sx, line=False))              # wide foot plate
        m.box(shin, -2.5, 2, -3, 5, 1, 5, iron(5 + sx))
        for tx in (-3, -0.5, 2):
            m.box(shin, tx, 3, -5, 1, 1, 1, IRON_D)                                        # toe claws

    # ------------------------------------------------------------------ body: the turbine housing
    m.box("body", -6, -15, -4, 12, 14, 9, patina(COPPER, 10, 0.45))
    m.box("body", -5, -1, -3, 10, 2, 7, iron(11))                                          # undercarriage
    m.box("body", -5.5, -16, -3.5, 11, 1, 8, patina(COPPER, 12, 0.3, line=False))         # top lid
    # the guard ring round the rotor: brass frame with bolts, a dark well behind
    def ring(f_, x, y, w, h):
        if f_ != "front":
            return B.BRASS_D
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if r > cx + 0.4:
            return None
        if r > cx - 1.2:
            return B.BRASS_L if (x + y) % 4 == 0 else B.BRASS
        return (20, 22, 24) if r > 1.4 else IRON_D
    m.box("body", -5, -13, -4.4, 10, 10, 1, ring, glow={"front": lambda f_, x, y, w, h:
          (110, 60, 20) if 1.5 < ((x - 4.5) ** 2 + (y - 4.5) ** 2) ** 0.5 < 3.2 and (x + y) % 3 == 0 else None, "*": None})
    m.box("rotor", -1, -1, -0.6, 2, 2, 1, B.BRASS_L)                                       # hub
    m.box("rotor", -0.5, -0.5, -1.2, 1, 1, 1, IRON_D)
    for i in range(3):
        m.box(f"blade{i}", -1, -4, -0.3, 2, 8, 1, blade(i))
    # pressure gauge and a valve wheel on the belly, a riveted name plate
    m.box("body", 2.5, -2.5, -4.6, 2, 2, 1, B.gauge())
    m.box("body", -4.5, -2.5, -4.6, 2, 2, 1, {"front": lambda f_, x, y, w, h: (170, 40, 30), "*": B.BRASS_D})
    m.box("body", -6.5, -12, -2, 1, 6, 5, iron(13))                                        # side hatches
    m.box("body", 5.5, -12, -2, 1, 6, 5, iron(14))
    # algae and silt in the lower seams
    m.box("body", -6.2, -4, -4.2, 12, 1, 9, {"top": VERD_D, "*": lambda f_, x, y, w, h: None if (x + y) % 3 else VERD_D})
    # shoulder drums fed by pipes from the back
    for sx in (-1, 1):
        m.box("body", -8.5 if sx < 0 else 5.5, -15, -2.5, 3, 4, 5, patina(COPPER, 15 + sx, 0.5, line=False))
        m.box("body", -5 if sx < 0 else 4, -14, 4.6, 1, 10, 1, B.rod(B.COPPER, 17 + sx))       # pipe down the back
        m.box("body", -6 if sx < 0 else 4, -15, 4.6, 2, 1, 1, B.COPPER_D)
    m.box("body", -3, -12, 5, 6, 7, 2, iron(18))                                           # firebox at the back
    m.box("body", -2, -10, 6.5, 4, 3, 1, {"back": lambda f_, x, y, w, h: AMBER if x % 2 else IRON_D, "*": IRON_D},
          glow={"back": lambda f_, x, y, w, h: AMBER_L if x % 2 else None, "*": None})

    # ------------------------------------------------------------------ head: low iron dome, single amber slit
    def visor(f_, x, y, w, h):
        if f_ == "front" and y == 2 and 0 < x < w - 1:
            return AMBER
        return iron(20)(f_, x, y, w, h)
    m.box("head", -3, -4, -3, 6, 4, 5, visor,
          glow={"front": lambda f_, x, y, w, h: (AMBER_L if x in (2, 3) else AMBER) if y == 2 and 0 < x < w - 1 else None,
                "*": None})
    m.box("head", -2.5, -5, -2.5, 5, 1, 4, patina(COPPER, 21, 0.5, line=False))
    m.box("head", -0.5, -7, 0, 1, 2, 1, B.BRASS)                                           # a whistle on top
    m.box("head", -1, -7.5, -0.5, 2, 1, 2, B.BRASS_L)
    m.box("head", -3.5, -3, -2, 1, 2, 3, B.BRASS_D)                                         # ear bolts
    m.box("head", 2.5, -3, -2, 1, 2, 3, B.BRASS_D)

    # ------------------------------------------------------------------ exhaust stacks
    for side in ("r", "l"):
        st = f"stack_{side}"
        m.box(st, -1, -7, -1, 2, 7, 2, B.soot(COPPER_D, 30))
        m.box(st, -1.5, -8, -1.5, 3, 1, 3, B.soot(IRON, 31))
        m.box(st, -1.2, -3, -1.2, 2, 1, 2, B.BRASS_D, grow=0.2)

    # ------------------------------------------------------------------ arms: piston arms, paddle blades
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, pad = f"arm_{side}", f"forearm_{side}", f"paddle_{side}"
        m.box(arm, -1.5, 0, -1.5, 3, 6, 3, iron(40 + sx))
        m.box(arm, -2, -1, -2, 4, 2, 4, patina(COPPER, 41 + sx, line=False))
        m.box(fore, -1, 0, -1, 2, 3, 2, B.rod((176, 176, 180), 42 + sx))
        m.box(fore, -2, 3, -2, 4, 3, 4, patina(COPPER, 43 + sx, line=False))
        m.box(pad, -0.5, 0, -0.5, 1, 2, 1, IRON_D)
        # three flat paddle blades fanned out, a brass rim on each
        for k, ang in enumerate((-1, 0, 1)):
            m.box(pad, -3 + ang * 0.5, 1.5 + k * 0.0, -2.5 + k * 2, 6, 5, 1,
                  {"front": blade(44 + k), "back": blade(45 + k), "*": B.BRASS_D})
        m.box(pad, -0.5, 1, -3, 1, 6, 6, IRON_D)                                           # the hub plate

    _anims(m)
    return m


def _spin(a, part, t0, t1, deg_per_s, start=0.0):
    """Linear rotor spin about z from t0 to t1, keyed every 0.1 s (no smoothing overshoot)."""
    keys = []
    t = t0
    ang = start
    while t < t1 - 1e-6:
        keys.append((round(t, 3), (0, 0, ang), "linear"))
        step = min(0.1, t1 - t)
        ang += deg_per_s(t) * step if callable(deg_per_s) else deg_per_s * step
        t += step
    keys.append((round(t1, 3), (0, 0, ang), "linear"))
    a.rot(part, *keys)
    return ang


def _anims(m):
    idle = m.anim("idle", 2.0)
    _spin(idle, "rotor", 0, 2.0, 60)                                                     # 120 deg: the blades repeat every 120
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, -0.3, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 14, 0)), (1.3, (0, -10, 0)), (2.0, (0, 0, 0)))
    idle.rot("paddle_r", (0, (0, 0, 0)), (1.0, (0, 10, 0)), (2.0, (0, 0, 0)))
    idle.rot("paddle_l", (0, (0, 0, 0)), (1.0, (0, -10, 0)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    _spin(walk, "rotor", 0, 1.0, 120)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.5, (-22, 0, 0)), (1.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.5, (22, 0, 0)), (1.0, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.25, (0, 0, 0)), (0.75, (20, 0, 0)), (1.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.25, (20, 0, 0)), (0.5, (0, 0, 0)), (1.0, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, 4)), (0.5, (0, 0, -4)), (1.0, (0, 0, 4)))                   # a heavy waddle
    walk.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.8, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.8, 0)), (1.0, (0, 0, 0)))
    walk.rot("arm_r", (0, (-14, 0, 0)), (0.5, (14, 0, 0)), (1.0, (-14, 0, 0)))
    walk.rot("arm_l", (0, (14, 0, 0)), (0.5, (-14, 0, 0)), (1.0, (14, 0, 0)))

    # slam: both paddles raised high over the head (0.55 s), brought down together in front (lands at 0.6 s = 12 ticks)
    a = m.anim("slam", 1.1)
    _spin(a, "rotor", 0, 1.1, 90)
    for arm, fore, s in (("arm_r", "forearm_r", 1), ("arm_l", "forearm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.5, (-170, 0, -14 * s)), (0.55, (-172, 0, -14 * s)), (0.65, (-60, 0, -6 * s), "linear"),
              (0.85, (-56, 0, -6 * s)), (1.1, (0, 0, 0)))
        a.rot(fore, (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.65, (10, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (0.65, (20, 0, 0), "linear"), (0.85, (18, 0, 0)), (1.1, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, 1, 1)), (0.65, (0, -2, -1.5), "linear"), (0.85, (0, -2, -1.5)), (1.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-18, 0, 0)), (0.65, (10, 0, 0)), (1.1, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.5, (0, 0, 0)), (0.65, (-10, 0, 10 * s)), (0.85, (-10, 0, 10 * s)), (1.1, (0, 0, 0)))

    # dash: crouches and spins the rotor up, faster and faster (0.9 s telegraph: steam screams out of the stacks), then
    # launches forward head down (at 0.9 s = 18 ticks) for 0.7 s, then skids to a stop
    a = m.anim("dash", 2.0)
    _spin(a, "rotor", 0, 2.0, lambda t: 90 + 1500 * min(t, 0.9) if t < 1.6 else max(90.0, 1440 - (t - 1.6) * 3200))
    a.rot("body", (0, (0, 0, 0)), (0.8, (16, 0, 0)), (0.9, (18, 0, 0)), (1.0, (34, 0, 0), "linear"), (1.6, (34, 0, 0)),
          (1.75, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.8, (0, -1.5, 1)), (0.9, (0, -1.5, 1)), (1.0, (0, -1, -1), "linear"), (1.6, (0, -1, -1)),
          (1.75, (0, 0, 1)), (2.0, (0, 0, 0)))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.8, (30, 0, -20 * s)), (1.0, (50, 0, -30 * s)), (1.6, (50, 0, -30 * s)), (1.75, (-30, 0, 0)),
              (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (1.0, (-24, 0, 0)), (1.6, (-24, 0, 0)), (2.0, (0, 0, 0)))
    for st, s in (("stack_r", 1), ("stack_l", -1)):
        a.rot(st, (0, (0, 0, 0)), (0.3, (0, 0, 4 * s)), (0.4, (0, 0, -4 * s)), (0.5, (0, 0, 6 * s)), (0.6, (0, 0, -6 * s)),
              (0.7, (0, 0, 8 * s)), (0.8, (0, 0, -8 * s)), (0.9, (0, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-30, 0, 0)), (1.0, (40, 0, 0)), (1.15, (-40, 0, 0)), (1.3, (40, 0, 0)),
          (1.45, (-40, 0, 0)), (1.6, (30, 0, 0)), (1.75, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (1.0, (-40, 0, 0)), (1.15, (40, 0, 0)), (1.3, (-40, 0, 0)),
          (1.45, (40, 0, 0)), (1.6, (-30, 0, 0)), (1.75, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))

    # vent: sinks onto its haunches and throws its arms wide, the chest rattling (0.7 s telegraph), then blows a
    # scalding cloud all around (at 0.7 s = 14 ticks)
    a = m.anim("vent", 1.4)
    _spin(a, "rotor", 0, 1.4, lambda t: 200 + 900 * t)
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, -2, 0)), (0.7, (0, -2.2, 0)), (0.75, (0, 0.5, 0), "linear"), (1.0, (0, 0.3, 0)),
          (1.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (0, 0, 3)), (0.4, (0, 0, -3)), (0.5, (0, 0, 4)), (0.6, (0, 0, -4)), (0.7, (-6, 0, 0)),
          (0.75, (-14, 0, 0)), (1.0, (-10, 0, 0)), (1.4, (0, 0, 0)))
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        a.rot(arm, (0, (0, 0, 0)), (0.6, (-20, 0, 50 * s)), (0.75, (-30, 0, 80 * s)), (1.0, (-30, 0, 76 * s)), (1.4, (0, 0, 0)))
    for st, s in (("stack_r", 1), ("stack_l", -1)):
        a.rot(st, (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.75, (-20, 0, 14 * s)), (1.0, (-16, 0, 10 * s)), (1.4, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.6, (-30, 0, 12 * s)), (0.75, (0, 0, 8 * s)), (1.4, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.6, (34, 0, 0)), (0.75, (0, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.6, (34, 0, 0)), (0.75, (0, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (8, 0, 0)), (0.75, (-20, 0, 0)), (1.4, (0, 0, 0)))
