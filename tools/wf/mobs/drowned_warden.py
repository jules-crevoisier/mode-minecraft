"""Drowned Warden: a giant drowned king (about 4 blocks tall) in barnacled armour, with a coral crown,
a kelp beard and cape, glowing sea-green eyes and a great prismarine trident."""
from ..models import Model, bands, framed, speckle
from ..texgen import mix, mul

SKIN = (74, 132, 118)
SKIN_D = (46, 92, 84)
KELP = (44, 98, 52)
KELP_D = (28, 66, 36)
GOLD = (236, 196, 72)
GOLD_D = (168, 120, 36)
SHELL = (206, 200, 182)
STEEL = (78, 96, 104)
STEEL_D = (48, 60, 68)
PRISM = (96, 176, 160)
PRISM_D = (52, 112, 104)
EYE = (150, 255, 220)


def rotten(base=SKIN, dark=SKIN_D, seed=0):
    """Drowned flesh: mottled teal with darker patches and pale barnacle dots."""
    sp = speckle(base, 0.1, seed, dark, freq=4)

    def f(face, x, y, w, h):
        r = (x * 31 + y * 17 + seed * 7) % 23
        if r == 0:
            return SHELL
        return sp(face, x, y, w, h)
    return f


def armour(base=STEEL, dark=STEEL_D, rust=(120, 92, 60), seed=0):
    plate = speckle(base, 0.07, seed, rust, freq=9)
    return framed(plate, mul(dark, 0.9))


def kelp_strands(seed=0, ragged=True):
    """Hanging kelp: vertical strands, ragged transparent bottom edge."""
    def f(face, x, y, w, h):
        if ragged and face not in ("top", "bottom") and y >= h - 1 - ((x * 7 + seed) % 4):
            return None
        c = KELP if (x + seed) % 3 else KELP_D
        if (x * 13 + y * 3 + seed) % 11 == 0:
            c = mix(c, (90, 140, 60), 0.5)
        return c
    return f


def build():
    m = Model("drowned_warden", seed=12, shadow=1.4, walk_speed=0.8, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -30, 0))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(10, 0, 0))
    m.part("head", "torso", pivot=(0, -21, -3))
    m.part("jaw", "head", pivot=(0, -2, -2))
    m.part("cape", "torso", pivot=(0, -20, 7), rot=(8, 0, 0))
    m.part("arm_r", "torso", pivot=(-14, -18, 0))
    m.part("forearm_r", "arm_r", pivot=(0, 14, 0), rot=(-20, 0, 0))
    m.part("trident", "forearm_r", pivot=(0, 13, -1), rot=(10, 0, 0))
    m.part("arm_l", "torso", pivot=(14, -18, 0))
    m.part("forearm_l", "arm_l", pivot=(0, 14, 0), rot=(-15, 0, 0))
    m.part("leg_r", "bone", pivot=(-6, -30, 0))
    m.part("shin_r", "leg_r", pivot=(0, 15, 0))
    m.part("leg_l", "bone", pivot=(6, -30, 0))
    m.part("shin_l", "leg_l", pivot=(0, 15, 0))

    # ------------------------------------------------------------------ body
    # pelvis with a kelp skirt and a gold-buckled belt
    m.box("hips", -10, -5, -6, 20, 7, 12, {"*": armour(seed=1), "front": bands([(2, GOLD), (5, armour(seed=1))])})
    m.box("hips", -11, 1, -7, 22, 9, 14, {"side": kelp_strands(1), "*": None})
    # barrel chest plate and a sunken belly
    m.box("torso", -11, -21, -7, 22, 15, 13, {
        "front": framed(speckle(STEEL, 0.07, 2, (120, 92, 60), freq=9), GOLD_D, 1),
        "*": armour(seed=2)})
    m.box("torso", -9, -7, -6, 18, 7, 11, rotten(seed=3))
    # ribs showing through a rotten breach in the plate
    m.box("torso", -6, -17, -8, 7, 8, 1, lambda f_, x, y, w, h: SHELL if y % 2 == 0 else (30, 40, 40))
    # shoulder mantle of shells
    m.box("torso", -12, -23, -5, 24, 3, 10, speckle(SHELL, 0.12, 4, (150, 140, 120), freq=3))

    # head: a long drowned skull face with a coral crown
    m.box("head", -5, -11, -6, 10, 11, 10, {
        "front": lambda f_, x, y, w, h: EYE if y == 4 and x in (2, 3, 6, 7)
        else (24, 36, 36) if y == 4 and x in (1, 8) else SKIN_D if y < 2 else rotten(seed=5)(f_, x, y, w, h),
        "*": rotten(seed=5)})
    m.box("jaw", -4, 0, -4, 8, 4, 7, {"front": bands([(1, (30, 40, 40)), (3, rotten(seed=6))]), "*": rotten(seed=6)})
    m.box("jaw", -4, 4, -4, 8, 9, 1, kelp_strands(2))  # kelp beard
    # crown: gold band with coral and gold points
    m.box("head", -6, -13, -7, 12, 3, 12, framed(GOLD, GOLD_D))
    for i, (x, z, hgt, col) in enumerate(((-5, -6, 5, GOLD), (-1, -7, 7, (220, 70, 90)), (3, -6, 5, GOLD),
                                          (-6, -1, 4, (220, 70, 90)), (5, -1, 4, (220, 70, 90)),
                                          (-1, 3, 5, GOLD))):
        m.box("head", x, -13 - hgt, z, 2, hgt, 2, speckle(col, 0.1, 10 + i))
    m.box("head", -1, -21, -7, 2, 2, 2, (120, 255, 220), glow=(120, 255, 220))  # sea gem on the tallest point
    # eyes glow
    m.parts["head"].cubes[0].glow = {"front": lambda f_, x, y, w, h: EYE if y == 4 and x in (2, 3, 6, 7) else None}

    # cape of kelp and torn sailcloth
    m.box("cape", -11, 0, 0, 22, 34, 1, {
        "back": lambda f_, x, y, w, h: None if y > h - 2 - (x * 5 % 4) else
        (KELP_D if x % 4 == 0 else mix(KELP, (70, 90, 110), (y % 7) / 12)),
        "front": kelp_strands(4), "*": KELP_D})

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        # pauldron: a huge barnacled shell
        m.box(arm, -6 if sx < 0 else -4, -6, -6, 10, 8, 12, {
            "top": speckle(SHELL, 0.12, 20 + sx, (150, 140, 120), freq=3), "*": armour(seed=21 + sx)})
        m.box(arm, -4 if sx < 0 else -3, 0, -4, 7, 15, 7, rotten(seed=22 + sx))
        m.box(fore, -4 if sx < 0 else -3, 0, -4, 7, 12, 7, {"*": rotten(seed=23 + sx),
                                                            "side": bands([(3, GOLD_D), (9, rotten(seed=23 + sx))])})
        # claw hand
        m.box(fore, -4 if sx < 0 else -3, 12, -4, 7, 4, 7, rotten(SKIN_D, (30, 60, 56), seed=24 + sx))

    # trident: shaft along the part's -y (pointing up from the fist), three prongs
    m.box("trident", -1, -50, -1, 2, 56, 2, bands([(46, speckle(PRISM_D, 0.08, 30)), (2, GOLD), (8, PRISM_D)]))
    m.box("trident", -5, -53, -1, 10, 3, 2, framed(GOLD, GOLD_D))
    for i, x in enumerate((-5, -1, 3)):
        hgt = 9 if x == -1 else 7
        m.box("trident", x, -53 - hgt, -1, 2, hgt, 2, speckle(PRISM, 0.08, 31 + i), glow=None)
    m.box("trident", -1, -64, -1, 2, 2, 2, (180, 255, 235), glow=(180, 255, 235))

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -5, 0, -5, 10, 16, 10, armour(seed=40 + sx))
        m.box(shin, -4, 0, -4, 8, 12, 8, rotten(seed=41 + sx))
        m.box(shin, -5, 10, -7, 10, 5, 12, armour(STEEL_D, (32, 40, 46), seed=42 + sx))  # heavy sabaton

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.rot("torso", (0, (0, 0, 0)), (1.5, (3, 0, 0)), (3, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (-4, 3, 0)), (3, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.5, (6, 0, 2)), (3, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.0, (8, 0, 0)), (2.0, (0, 0, 0)), (3, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (25 * sign, 0, 0)), (0.8, (-25 * sign, 0, 0)), (1.6, (25 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, (0, 0, 0)), (0.4, (30 if sign > 0 else 0, 0, 0)), (0.8, (0, 0, 0)),
                 (1.2, (30 if sign < 0 else 0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (-18, 0, 0)), (0.8, (18, 0, 0)), (1.6, (-18, 0, 0)))
    walk.rot("arm_r", (0, (8, 0, 0)), (0.8, (-8, 0, 0)), (1.6, (8, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.4, (0, -1.5, 0)), (0.8, (0, 0, 0)), (1.2, (0, -1.5, 0)), (1.6, (0, 0, 0)))

    # thrust: pull the trident back (telegraph), lunge, recover
    a = m.anim("thrust", 1.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-60, 30, 0)), (0.75, (-95, -10, 0), "linear"), (1.1, (-90, -10, 0)), (1.5, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (0.75, (10, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.rot("trident", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (0.75, (-10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (-6, 25, 0)), (0.75, (14, -20, 0), "linear"), (1.1, (12, -18, 0)), (1.5, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 0, 3)), (0.75, (0, 0, -6), "linear"), (1.1, (0, 0, -6)), (1.5, (0, 0, 0)))

    # slam: both arms high over the head (long telegraph), smash the ground, slow recovery
    a = m.anim("slam", 1.9)
    for arm in ("arm_r", "arm_l"):
        a.rot(arm, (0, (0, 0, 0)), (0.9, (-170, 0, 0)), (1.05, (-40, 0, 0), "linear"), (1.5, (-35, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.9, (-18, 0, 0)), (1.05, (35, 0, 0), "linear"), (1.5, (30, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (1.05, (10, 0, 0)), (1.9, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.9, (0, 3, 0)), (1.05, (0, -4, 0), "linear"), (1.5, (0, -4, 0)), (1.9, (0, 0, 0)))

    # sweep: wide horizontal swing of the trident
    a = m.anim("sweep", 1.4)
    a.rot("torso", (0, (0, 0, 0)), (0.55, (0, 55, 0)), (0.8, (8, -60, 0), "linear"), (1.0, (6, -55, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-80, 40, 0)), (0.8, (-80, -50, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("trident", (0, (0, 0, 0)), (0.55, (10, 0, 0)), (0.8, (10, 0, 0)), (1.4, (0, 0, 0)))

    # summon: raise the trident to the sky, the head thrown back
    a = m.anim("summon", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-175, 0, 10)), (1.2, (-175, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.2, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 0, -40)), (1.2, (-60, 0, -40)), (1.6, (0, 0, 0)))

    # whirl: a full spin with the trident held out (the whirlpool attack)
    a = m.anim("whirl", 1.6)
    a.rot("bone", (0, (0, 0, 0)), (0.4, (0, 40, 0)), (1.2, (0, -320, 0), "linear"), (1.6, (0, -360, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-90, 0, -60)), (1.2, (-90, 0, -60)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-90, 0, 60)), (1.2, (-90, 0, 60)), (1.6, (0, 0, 0)))

    # roar: phase change, arms spread, crown thrown back
    a = m.anim("roar", 2.4)
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.9, (-20, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-35, 0, 0)), (1.9, (-35, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (35, 0, 0)), (1.9, (35, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-30, 0, 70)), (1.9, (-30, 0, 70)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-30, 0, -70)), (1.9, (-30, 0, -70)), (2.4, (0, 0, 0)))

    # stagger: posture broken, drops to one knee
    a = m.anim("stagger", 2.0)
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -7, 2)), (1.6, (0, -7, 2)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (1.6, (-60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.3, (14, 0, 0)), (1.6, (14, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (15, 0, 0)), (1.6, (15, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (20, 0, 10)), (1.6, (20, 0, 10)), (2.0, (0, 0, 0)))
    return m
