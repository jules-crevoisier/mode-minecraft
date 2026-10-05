"""Rift Sentinel (Sentinelle de la faille): the floating warden of the End archives, observatories and wrecks.

Silhouette idea: a lighthouse of the void. A tall obsidian obelisk floating above the ground, split down the middle by
a single violet eye, with four rune tablets orbiting it like the hands of a clock and a crystal spike below. It
charges a tether beam (the tablets lock in front of the eye) that drags its prey toward it, and blinks away when hurt.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

OBS = (34, 26, 48)
OBS_D = (20, 14, 30)
OBS_L = (70, 56, 96)
PURPUR = (170, 120, 170)
PURPUR_D = (120, 80, 124)
EYE = (220, 110, 255)
EYE_L = (255, 220, 255)
RUNE = (200, 150, 255)
CRYSTAL = (230, 210, 255)


def obsidian(seed=0):
    def f(face, x, y, w, h):
        r = K.h(x, y, seed) % 100
        c = OBS if r > 25 else OBS_D
        if r > 94:
            c = mix(OBS_L, EYE, 0.3)                                             # a glint
        if face == "top":
            c = mul(c, 1.2)
        if face in ("front", "back", "left", "right") and (x in (0, w - 1)):
            c = mul(c, 0.8)
        return c
    return f


def tablet(seed=0):
    """A purpur rune tablet: a frame and a glyph that glows."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return PURPUR_D
        if x in (0, w - 1) or y in (0, h - 1):
            return PURPUR_D
        if glyph(x, y, w, h, seed):
            return RUNE
        return PURPUR if (x + y) % 3 else mul(PURPUR, 0.9)
    return f


def glyph(x, y, w, h, seed):
    if not (1 <= x <= w - 2 and 1 <= y <= h - 2):
        return False
    return (x == w // 2) or (y == h // 2 and K.h(x, seed) % 2 == 0) or (y == 1 + seed % 2 and x % 2 == 1)


def tablet_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back") and glyph(x, y, w, h, seed):
            return RUNE
        return None
    return f


def build():
    m = Model("rift_sentinel", seed=411, shadow=0.4, walk_speed=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -14, 0))
    m.part("head", "body", pivot=(0, -6, 0))
    m.part("ring", "body", pivot=(0, -6, 0))
    m.part("spike", "body", pivot=(0, 4, 0))

    # ------------------------------------------------------------------ the obelisk: a lower block, the eye, a cap
    m.box("body", -4, -2, -4, 8, 6, 8, obsidian(1))
    m.box("body", -3, -14, -3, 6, 4, 6, obsidian(2))
    m.box("body", -2, -17, -2, 4, 3, 4, obsidian(3))
    m.box("body", -1, -19, -1, 2, 2, 2, CRYSTAL, glow={"*": CRYSTAL})

    def eye_block(f_, x, y, w, h):
        if f_ == "front":
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = ((x - cx) ** 2 + ((y - cy) * 1.3) ** 2) ** 0.5
            if r < 1.0:
                return (30, 0, 40)                                               # the pupil
            if r < 2.4:
                return EYE_L if r < 1.6 else EYE
            if abs(x - cx) < 0.6:
                return EYE                                                       # the rift line
        return obsidian(4)(f_, x, y, w, h)

    def eye_glow(f_, x, y, w, h):
        if f_ != "front":
            return None
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = ((x - cx) ** 2 + ((y - cy) * 1.3) ** 2) ** 0.5
        if 1.0 <= r < 2.4:
            return EYE_L if r < 1.6 else EYE
        if abs(x - cx) < 0.6 and r >= 2.4:
            return EYE
        return None
    # the eye block (the "head": it looks at its prey)
    m.box("head", -3.5, -4, -3.5, 7, 8, 7, eye_block, glow=eye_glow)

    # the crystal spike under it
    m.box("spike", -2, 0, -2, 4, 3, 4, obsidian(5))
    m.box("spike", -1, 3, -1, 2, 4, 2, CRYSTAL, glow={"*": mix(CRYSTAL, EYE, 0.4)})

    # ------------------------------------------------------------------ four orbiting rune tablets
    for i, yaw in enumerate((0, 90, 180, 270)):
        holder = f"arm{i}"
        m.part(holder, "ring", pivot=(0, 0, 0), rot=(0, yaw, 0))
        tab = f"tab{i}"
        m.part(tab, holder, pivot=(0, 0, -8), rot=(0, 0, 0))
        m.box(tab, -2.5, -4, -0.5, 5, 8, 1, tablet(i), glow=tablet_glow(i))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.rot("ring", (0, (0, 0, 0), "linear"), (4.0, (0, 360, 0), "linear"))
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, 2, 0)), (4.0, (0, 0, 0)))
    idle.rot("spike", (0, (0, 0, 0), "linear"), (4.0, (0, -360, 0), "linear"))
    for i in range(4):
        idle.pos(f"tab{i}", (0, (0, 0, 0)), (1.0 + i * 0.5, (0, 1.5, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("body", (0, (8, 0, 0)), (1.0, (8, 0, 0)))

    # charge: the tablets swing in front of the eye and the beam builds (1.0 s = 20 ticks), then it fires
    a = m.anim("charge", 1.4)
    for i, yaw in enumerate((0, 90, 180, 270)):
        target = (0, (-30, -10, 10, 30)[i], 0)
        a.rot(f"arm{i}", (0, (0, 0, 0)), (0.6, (0, -yaw + target[1], 0)), (1.0, (0, -yaw + target[1], 0)),
              (1.4, (0, 0, 0)))
        a.pos(f"tab{i}", (0, (0, 0, 0)), (0.6, (0, 0, 3)), (1.0, (0, 0, 3)), (1.1, (0, 0, -1), "linear"), (1.4, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.9, (1.15, 1.15, 1.15)), (1.0, (0.9, 0.9, 0.9), "linear"), (1.4, (1, 1, 1)))
    a.rot("body", (0, (0, 0, 0)), (0.9, (-8, 0, 0)), (1.0, (6, 0, 0), "linear"), (1.4, (0, 0, 0)))

    # blink: folds in on itself (gone at 0.25 s) and unfolds where it reappears
    a = m.anim("blink", 0.6)
    a.scale("body", (0, (1, 1, 1)), (0.25, (0.1, 1.4, 0.1), "linear"), (0.35, (0.1, 1.4, 0.1)), (0.6, (1, 1, 1)))
    a.rot("ring", (0, (0, 0, 0), "linear"), (0.6, (0, 720, 0), "linear"))

    # shove: the tablets slam outward to push away whoever is too close (at 0.3 s = 6 ticks)
    a = m.anim("shove", 0.8)
    for i in range(4):
        a.pos(f"tab{i}", (0, (0, 0, 0)), (0.25, (0, 0, 3)), (0.3, (0, 0, -6), "linear"), (0.5, (0, 0, -5)), (0.8, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.25, (0.85, 0.85, 0.85)), (0.3, (1.2, 1.2, 1.2), "linear"), (0.8, (1, 1, 1)))
    return m
