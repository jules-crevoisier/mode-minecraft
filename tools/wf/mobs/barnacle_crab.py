"""Barnacle Crab (Crabe à bernacles): the scuttling guardian of the sunken temples, citadels and wrecks.

Silhouette idea: a living reef. A wide, low crab whose carapace is crusted with white barnacle cones and trailing
kelp, one enormous lopsided clamp claw (and one small picking claw), eyes on stalks and six spiky legs. It climbs walls
under water, clamps its prey in the big claw, and hides in its shell when hurt.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

SHELL = (170, 70, 52)
SHELL_D = (112, 42, 34)
SHELL_L = (214, 120, 86)
BELLY = (226, 190, 150)
BARN = (226, 222, 210)
BARN_D = (150, 146, 136)
KELP = (70, 120, 60)
KELP_D = (44, 84, 40)
EYE = (30, 30, 34)
GLOW = (120, 255, 220)


def carapace(seed=0):
    """Red-brown shell, darker ridges, a crust of barnacles and green algae stains."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BELLY if (x + y) % 3 else mul(BELLY, 0.9)
        r = K.h(x, y, seed) % 100
        c = SHELL if (x + y // 2) % 4 else SHELL_D
        if face == "top" and r < 14:
            return BARN if r < 8 else BARN_D                                    # barnacle crust
        if r > 90:
            c = mix(c, KELP, 0.5)                                               # algae
        if face in ("front", "back", "left", "right") and y == 0:
            c = SHELL_L
        return c
    return f


def barnacle():
    def f(face, x, y, w, h):
        if face == "top":
            return (40, 46, 50) if w > 1 and 0 < x < w - 1 and 0 < y < h - 1 else BARN   # the open mouth
        return BARN if y < h - 1 else BARN_D
    return f


def claw_paint(seed=0):
    def f(face, x, y, w, h):
        c = carapace(seed)(face, x, y, w, h)
        if face in ("front", "back", "left", "right") and y == h - 1:
            return mix(c, (230, 220, 200), 0.4)                                 # pale tips
        return c
    return f


def build():
    m = Model("barnacle_crab", seed=375, shadow=0.8, walk_speed=2.0, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -5, 0))
    m.part("eye_r", "body", pivot=(-2, -4, -5))
    m.part("eye_l", "body", pivot=(2, -4, -5))
    m.part("claw_r", "body", pivot=(-6, -1, -5), rot=(0, 30, 0))
    m.part("pincer_r", "claw_r", pivot=(-1, 1, -6))
    m.part("claw_l", "body", pivot=(6, -1, -5), rot=(0, -30, 0))
    m.part("pincer_l", "claw_l", pivot=(0.5, 0.5, -3))

    # ------------------------------------------------------------------ carapace with barnacles and kelp
    m.box("body", -7, -4, -6, 14, 5, 11, carapace(1))
    m.box("body", -5, -6, -4, 10, 2, 8, carapace(2))
    m.box("body", -6, 1, -5, 12, 1, 9, {"*": BELLY, "bottom": mul(BELLY, 0.85)})
    for i, (bx, bz, s) in enumerate(((-4, -2, 2), (2, -3, 3), (-1, 1, 2), (3, 1, 2), (-5, 2, 1), (5, -1, 1))):
        m.box("body", bx, -6 - s, bz, s, s, s, barnacle())
    for i, (kx, kz, ln) in enumerate(((-6, 4, 6), (-2, 5, 8), (4, 5, 5), (6.5, 0, 4))):
        m.box("body", kx, -3, kz, 1, ln, 0 if kx != 6.5 else 1,
              lambda f_, x, y, w, h: (KELP if (y + x) % 3 else KELP_D) if f_ not in ("top", "bottom") else None)
    # mouth plates and a bubble-blowing slit
    m.box("body", -2, -2, -6.5, 4, 2, 1, lambda f_, x, y, w, h: (60, 30, 30) if f_ == "front" and y == 1 else SHELL_D)

    # ------------------------------------------------------------------ eye stalks (glinting black pearls)
    for e in ("eye_r", "eye_l"):
        m.box(e, -0.5, -3, -0.5, 1, 3, 1, SHELL_L)
        m.box(e, -1, -5, -1, 2, 2, 2, {"*": EYE, "front": lambda f_, x, y, w, h: (220, 240, 240) if (x, y) == (0, 0) else EYE},
              glow={"front": lambda f_, x, y, w, h: GLOW if (x, y) == (1, 1) else None, "*": None})

    # ------------------------------------------------------------------ the great clamp (right) and the picker (left)
    m.box("claw_r", -2, -1, -2, 3, 3, 5, carapace(3))                               # forearm
    m.box("claw_r", -4, -3, -7, 6, 6, 6, carapace(4))                               # the swollen palm
    for bx, bz in ((-3, -6), (0, -4)):
        m.box("claw_r", bx, -5, bz, 1, 2, 1, barnacle())
    m.box("claw_r", -4, -2, -11, 6, 2, 4, claw_paint(5))                           # fixed upper jaw
    m.box("pincer_r", -3, -1, -5, 6, 2, 5, claw_paint(6))                          # moving lower jaw
    m.box("pincer_r", -3, -2, -5, 1, 1, 1, BARN)                                    # serrations
    m.box("pincer_r", 1, -2, -5, 1, 1, 1, BARN)

    m.box("claw_l", -1, -1, -3, 2, 2, 3, carapace(7))
    m.box("claw_l", -1.5, -1, -5, 3, 1, 2, claw_paint(8))
    m.box("pincer_l", -1, 0, -2, 2, 1, 2, claw_paint(9))

    # ------------------------------------------------------------------ six legs, jointed and spiked
    legs = []
    for side, sx in (("r", -1), ("l", 1)):
        for i, (z, yaw) in enumerate(((-2, 22), (1, 0), (4, -24))):
            leg, foot = f"leg_{side}{i}", f"foot_{side}{i}"
            m.part(leg, "body", pivot=(6.5 * sx, -1, z), rot=(0, yaw * sx, -30 * sx))
            m.part(foot, leg, pivot=(5 * sx, 0, 0), rot=(0, 0, 70 * sx))
            m.box(leg, 0 if sx > 0 else -5, -1, -1, 5, 2, 2, carapace(10 + i))
            m.box(foot, -0.5, 0, -0.5, 1, 6, 1, lambda f_, x, y, w, h: SHELL_D if y >= h - 2 else SHELL)
            legs.append((leg, foot, sx, i))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.4)
    idle.rot("eye_r", (0, (0, 0, 0)), (0.6, (-10, 10, 0)), (1.4, (6, -6, 0)), (2.4, (0, 0, 0)))
    idle.rot("eye_l", (0, (0, 0, 0)), (0.8, (8, -8, 0)), (1.6, (-8, 10, 0)), (2.4, (0, 0, 0)))
    idle.rot("pincer_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (0.5, (0, 0, 0)), (1.2, (0, 0, 0)), (1.4, (30, 0, 0)),
             (1.6, (0, 0, 0)), (2.4, (0, 0, 0)))
    idle.rot("claw_l", (0, (0, 0, 0)), (0.3, (-20, 0, 0)), (0.5, (0, 0, 0)), (1.2, (0, 0, 0)), (1.4, (-20, 0, 0)),
             (1.6, (0, 0, 0)), (2.4, (0, 0, 0)))                                   # picks food to its mouth
    idle.pos("body", (0, (0, 0, 0)), (1.2, (0, 0.4, 0)), (2.4, (0, 0, 0)))
    idle.rot("pincer_r", (0, (0, 0, 0)), (1.8, (0, 0, 0)), (2.0, (20, 0, 0)), (2.2, (0, 0, 0)), (2.4, (0, 0, 0)))

    # walk: a sideways-looking scuttle (alternating tripods)
    walk = m.anim("walk", 0.5)
    for leg, foot, sx, i in legs:
        ph = (i + (0 if sx > 0 else 1)) % 2
        sw = 16 if ph else -16
        walk.rot(leg, (0, (0, sw, 0)), (0.125, (0, 0, -18 * sx if ph else 0)), (0.25, (0, -sw, 0)),
                 (0.375, (0, 0, 0 if ph else -18 * sx)), (0.5, (0, sw, 0)))
    walk.rot("body", (0, (0, 0, -3)), (0.25, (0, 0, 3)), (0.5, (0, 0, -3)))

    # snap: the small claw jabs (lands at 0.3 s = 6 ticks)
    a = m.anim("snap", 0.6)
    a.rot("claw_l", (0, (0, 0, 0)), (0.2, (-30, 30, 0)), (0.3, (10, -20, 0), "linear"), (0.6, (0, 0, 0)))
    a.rot("pincer_l", (0, (0, 0, 0)), (0.2, (45, 0, 0)), (0.3, (0, 0, 0), "linear"), (0.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.2, (0, -10, 0)), (0.3, (0, 8, 0)), (0.6, (0, 0, 0)))

    # clamp: the great claw rears up and gapes (0.6 s telegraph), then slams shut at 0.6 s (12 ticks)
    a = m.anim("clamp", 1.0)
    a.rot("claw_r", (0, (0, 0, 0)), (0.5, (-40, -10, 0)), (0.6, (10, -25, 0), "linear"), (0.8, (6, -20, 0)), (1.0, (0, 0, 0)))
    a.rot("pincer_r", (0, (0, 0, 0)), (0.5, (60, 0, 0)), (0.6, (0, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (-12, 15, 0)), (0.6, (6, -10, 0), "linear"), (1.0, (0, 0, 0)))

    # hold: squeezes what it caught (played again while it holds a player)
    a = m.anim("hold", 0.5)
    a.rot("claw_r", (0, (6, -20, 0)), (0.25, (2, -24, 3)), (0.5, (0, 0, 0)))
    a.rot("pincer_r", (0, (0, 0, 0)), (0.25, (-6, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.25, (0, 0, 3)), (0.5, (0, 0, 0)))

    # hide: pulls every limb under the shell (tucked at 0.3 s) and stays shut until 2.7 s
    a = m.anim("hide", 3.0)
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, -3, 0)), (2.7, (0, -3, 0)), (3.0, (0, 0, 0)))
    a.rot("claw_r", (0, (0, 0, 0)), (0.3, (0, 70, 0)), (2.7, (0, 70, 0)), (3.0, (0, 0, 0)))
    a.rot("claw_l", (0, (0, 0, 0)), (0.3, (0, -60, 0)), (2.7, (0, -60, 0)), (3.0, (0, 0, 0)))
    a.pos("eye_r", (0, (0, 0, 0)), (0.3, (0, -3, 0)), (2.7, (0, -3, 0)), (3.0, (0, 0, 0)))
    a.pos("eye_l", (0, (0, 0, 0)), (0.3, (0, -3, 0)), (2.7, (0, -3, 0)), (3.0, (0, 0, 0)))
    for leg, foot, sx, i in legs:
        a.rot(leg, (0, (0, 0, 0)), (0.3, (0, 0, 40 * sx)), (2.7, (0, 0, 40 * sx)), (3.0, (0, 0, 0)))
    return m
