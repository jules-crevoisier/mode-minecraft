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


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


GLOWSPOT = (120, 240, 210)


def rotten(base=SKIN, dark=SKIN_D, seed=0, glow_spots=False):
    """Drowned flesh: teal skin, darker toward the bottom, sunken vein lines, pale barnacle clusters and (optionally)
    a few bioluminescent spots (the matching glow is :func:`rotten_glow`)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(dark, 0.8)
        if glow_spots and _spot(face, x, y, seed):
            return GLOWSPOT
        if _barnacle(face, x, y, seed):
            return SHELL if _n(x, y, seed + 3) < 0.6 else mul(SHELL, 0.75)
        if (x + (y // 3) + seed) % 7 == 0 and face != "top":
            return mix(dark, (30, 60, 70), 0.4)                                    # a sunken vein
        c = mix(base, dark, min(1.0, 0.15 + 0.6 * y / max(1, h)) if face != "top" else 0.0)
        return mul(c, 0.94 + 0.12 * _n(x // 2, y // 2, seed))
    return f


def _barnacle(face, x, y, seed):
    return face != "bottom" and _n(x // 2, y // 2, seed + 11) < 0.09 and (x + y) % 2 == 0


def _spot(face, x, y, seed):
    return face in ("front", "left", "right", "back") and _n(x, y, seed + 21) < 0.008


def rotten_glow(seed=0):
    def f(face, x, y, w, h):
        return GLOWSPOT if _spot(face, x, y, seed) else None
    return f


def armour(base=STEEL, dark=STEEL_D, rust=(130, 86, 52), seed=0):
    """Sunken plate: a gold-lit top edge, dark rim, rivets, rust streaks running down from the rivets, barnacle
    clusters and green weed on the lower edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(dark, 0.8)
        if face == "top":
            if _barnacle(face, x, y, seed):
                return SHELL
            return mix(base, (190, 210, 210), 0.18) if (x in (0, w - 1) or y in (0, h - 1)) else mul(base, 1.08)
        if w > 3 and h > 3:
            if y == 0:
                return mix(base, (200, 220, 220), 0.3)
            if x in (0, w - 1) or y == h - 1:
                return KELP_D if (y == h - 1 and _n(x, 0, seed) < 0.4) else dark
            if y == 1 and x % 4 == 1:
                return GOLD_D                                                       # rivets
            if x % 4 == 1 and y > 1 and _n(x, 0, seed + 5) < 0.6 and y < 2 + 6 * _n(x, 1, seed):
                return mix(rust, base, 0.3)                                         # rust weeping from the rivet
        if _barnacle(face, x, y, seed):
            return SHELL if _n(x, y, seed + 3) < 0.6 else mul(SHELL, 0.75)
        return mul(base, 1.06 - 0.22 * y / max(1, h) + (_n(x, y, seed) - 0.5) * 0.06)
    return f


def shell_paint(seed=0):
    """A giant scallop shell: ribs fanning out, lit crests, darker grooves, a pink lip."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return (150, 120, 110)
        if face == "top" or face in ("left", "right"):
            k = (x if face == "top" else y) % 3
        else:
            k = x % 3
        c = (mix(SHELL, (255, 250, 236), 0.3), SHELL, mul(SHELL, 0.72))[k]
        if face not in ("top", "bottom") and y == h - 1:
            c = (214, 140, 140)
        return c
    return f


def coral(col, seed=0):
    """Branching coral: lit tips, darker base, pores."""
    def f(face, x, y, w, h):
        if face == "top":
            return mix(col, (255, 255, 255), 0.35)
        if face == "bottom":
            return mul(col, 0.6)
        c = mul(col, 1.1 - 0.4 * y / max(1, h))
        if (x + y + seed) % 3 == 0:
            c = mul(c, 0.82)
        return c
    return f


def coral_glow(col):
    return {"top": mix(col, (255, 255, 255), 0.35), "*": None}


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


def sailcloth(seed=0):
    """The cape: torn grey-blue sailcloth with kelp grown through it and a faded gold trident sigil."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return KELP_D
        if y > h - 2 - (x * 5 + seed) % 6 or (x % 7 == 3 and y > h - 9 and _n(x, y // 4, seed) < 0.7):
            return None                                                             # rags and a split
        if face == "back":
            cx = (w - 1) / 2
            if 6 <= y <= 18 and abs(x - cx) < 0.6 or (y == 8 and abs(x - cx) <= 4) or (y in (6, 7) and abs(abs(x - cx) - 4) < 0.6):
                return mix(GOLD_D, (70, 86, 100), 0.4)                              # the sigil
            if (x + _n(x // 3, 0, seed) * 3) % 5 < 1:
                return KELP
            return mul((76, 92, 108), 1.05 - 0.3 * y / h)
        return kelp_strands(seed)(face, x, y, w, h)
    return f


def build():
    m = Model("drowned_warden", seed=12, shadow=1.4, walk_speed=0.8, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -30, 0))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(10, 0, 0))
    m.part("head", "torso", pivot=(0, -21, -3))
    m.part("jaw", "head", pivot=(0, -2, -2))
    m.part("beard", "jaw", pivot=(0, 4, -3.5))
    m.part("cape", "torso", pivot=(0, -20, 7), rot=(8, 0, 0))
    m.part("arm_r", "torso", pivot=(-14, -18, 0))
    m.part("forearm_r", "arm_r", pivot=(0, 14, 0), rot=(-20, 0, 0))
    m.part("trident", "forearm_r", pivot=(0, 13, -1), rot=(10, 0, 0))
    m.part("arm_l", "torso", pivot=(14, -18, 0))
    m.part("forearm_l", "arm_l", pivot=(0, 14, 0), rot=(-15, 0, 0))
    m.part("chain", "hips", pivot=(9, 1, -5), rot=(0, 0, -8))
    m.part("lantern", "chain", pivot=(0, 10, 0))
    m.part("leg_r", "bone", pivot=(-6, -30, 0))
    m.part("shin_r", "leg_r", pivot=(0, 15, 0))
    m.part("leg_l", "bone", pivot=(6, -30, 0))
    m.part("shin_l", "leg_l", pivot=(0, 15, 0))

    # ------------------------------------------------------------------ body
    # pelvis with a kelp skirt and a gold-buckled belt
    def belt(f_, x, y, w, h):
        if f_ == "front" and y < 2:
            return GOLD if (abs(x - w // 2) > 1 or y == 0) else (120, 255, 220)  # gold belt, a sea-gem buckle
        return armour(seed=1)(f_, x, y, w, h)
    m.box("hips", -10, -5, -6, 20, 7, 12, belt, glow={"front": lambda f_, x, y, w, h: (120, 255, 220)
                                                       if y == 1 and abs(x - w // 2) <= 1 else None, "*": None})
    m.box("hips", -11, 1, -7, 22, 9, 14, {"side": kelp_strands(1), "*": None})
    # barrel chest plate (gold trim) and a sunken, rotten belly
    def chest(f_, x, y, w, h):
        if f_ == "front" and (y in (0, h - 1) or x in (0, w - 1)):
            return GOLD_D if (x + y) % 3 else GOLD
        return armour(seed=2)(f_, x, y, w, h)
    m.box("torso", -11, -21, -7, 22, 15, 13, chest)
    m.box("torso", -9, -7, -6, 18, 7, 11, rotten(seed=3, glow_spots=True), glow=rotten_glow(3))
    # ribs showing through a rotten breach in the plate, a glow of sea-light inside
    m.box("torso", -6, -17, -8, 7, 8, 1, lambda f_, x, y, w, h: SHELL if y % 2 == 0 else (20, 70, 64),
          glow={"front": lambda f_, x, y, w, h: (60, 180, 150) if y % 2 else None, "*": None})
    # shoulder mantle of shells
    m.box("torso", -12, -23, -5, 24, 3, 10, shell_paint(4))
    # coral growing out of his back: three branching spikes over the cape
    for i, (x, hgt, tilt, col) in enumerate(((-7, 10, -14, (220, 80, 100)), (6, 13, 12, (230, 120, 70)),
                                            (-1, 8, 0, (200, 90, 170)))):
        p = m.part(f"coral{i}", "torso", pivot=(x, -20, 6), rot=(-24, 0, tilt))
        m.box(p, -1, -hgt, -1, 2, hgt, 2, coral(col, i), glow=coral_glow(col))
        m.box(p, (1 if i % 2 else -3), -hgt + 3, -0.5, 2, 1, 1, coral(col, i + 3))
        m.box(p, (1 if i % 2 else -3), -hgt + 1, -0.5, 1, 2, 1, coral(col, i + 4), glow=coral_glow(col))

    # head: a long drowned face, sunken cheeks, glowing eyes under a heavy brow, a coral crown
    eyes = {(2, 4), (3, 4), (6, 4), (7, 4)}

    def face(f_, x, y, w, h):
        if (x, y) in eyes:
            return EYE
        if y == 4 and x in (1, 8):
            return (24, 36, 36)
        if y == 3 and 1 <= x <= 8:
            return mul(SKIN_D, 0.7)                                                 # the brow's shadow
        if y < 2:
            return SKIN_D
        if y in (6, 7) and x in (1, 8):
            return mix(SKIN_D, (20, 40, 40), 0.5)                                   # sunken cheeks
        return rotten(seed=5)(f_, x, y, w, h)
    m.box("head", -5, -11, -6, 10, 11, 10, {"front": face, "*": rotten(seed=5)},
          glow={"front": lambda f_, x, y, w, h: EYE if (x, y) in eyes else None, "*": None})
    m.box("jaw", -4, 0, -4, 8, 4, 7, {"front": bands([(1, (30, 40, 40)), (3, rotten(seed=6))]), "*": rotten(seed=6)})
    m.box("beard", -4, 0, 0, 8, 10, 1, kelp_strands(2))                             # kelp beard
    m.box("beard", -2, 0, -0.5, 4, 13, 1, kelp_strands(3))
    # crown: gold band with coral and gold points
    m.box("head", -6, -13, -7, 12, 3, 12, framed(GOLD, GOLD_D))
    for i, (x, z, hgt, col) in enumerate(((-5, -6, 6, GOLD), (-1, -7, 8, (220, 70, 90)), (3, -6, 6, GOLD),
                                          (-6, -1, 5, (220, 70, 90)), (5, -1, 7, (230, 120, 70)),
                                          (-1, 3, 5, GOLD))):
        paint = framed(GOLD, GOLD_D) if col == GOLD else coral(col, 10 + i)
        m.box("head", x, -13 - hgt, z, 2, hgt, 2, paint, glow=None if col == GOLD else coral_glow(col))
    m.box("head", -1, -23, -7, 2, 2, 2, (120, 255, 220), glow=(120, 255, 220))  # sea gem on the tallest point

    # cape of kelp and torn sailcloth
    m.box("cape", -11, 0, 0, 22, 34, 1, sailcloth(4))

    # a drowned ship's chain hanging from the belt, a sunken lantern at its end
    for k in range(5):
        m.box("chain", -0.5, k * 2, -0.5 - (k % 2) * 0.0, 1, 2, 1 + (k % 2), lambda f_, x, y, w, h: STEEL if y == 0 else STEEL_D)
    m.box("lantern", -2, 0, -2, 4, 5, 4, {"front": lambda f_, x, y, w, h: (120, 255, 220) if 0 < x < w - 1 and 0 < y < h - 1
                                          else GOLD_D, "back": lambda f_, x, y, w, h: (120, 255, 220) if 0 < x < w - 1 and 0 < y < h - 1
                                          else GOLD_D, "*": GOLD_D},
          glow={"front": lambda f_, x, y, w, h: (120, 255, 220) if 0 < x < w - 1 and 0 < y < h - 1 else None,
                "back": lambda f_, x, y, w, h: (120, 255, 220) if 0 < x < w - 1 and 0 < y < h - 1 else None, "*": None})
    m.box("lantern", -2.5, -1, -2.5, 5, 1, 5, GOLD_D)

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        if sx < 0:
            # the trident arm: a giant scallop-shell pauldron, much bigger than the other (asymmetry)
            m.box(arm, -8, -8, -7, 13, 9, 14, shell_paint(20))
            m.box(arm, -9, -9, -3, 3, 3, 6, coral((220, 80, 100), 21), glow=coral_glow((220, 80, 100)))
        else:
            m.box(arm, -4, -6, -6, 10, 8, 12, armour(seed=21 + sx))
        m.box(arm, -4 if sx < 0 else -3, 0, -4, 7, 15, 7, rotten(seed=22 + sx, glow_spots=True), glow=rotten_glow(22 + sx))
        m.box(fore, -4 if sx < 0 else -3, 0, -4, 7, 12, 7, {"*": rotten(seed=23 + sx),
                                                            "side": bands([(3, GOLD_D), (9, rotten(seed=23 + sx))])})
        # claw hand with long dark nails
        m.box(fore, -4 if sx < 0 else -3, 12, -4, 7, 4, 7, rotten(SKIN_D, (30, 60, 56), seed=24 + sx))
        m.box(fore, -3.5 if sx < 0 else -2.5, 16, -4, 6, 2, 1, lambda f_, x, y, w, h: (30, 40, 40) if x % 2 == 0 else None)

    # trident: shaft along the part's -y (pointing up from the fist), barbed prongs that glow
    m.box("trident", -1, -50, -1, 2, 56, 2, bands([(4, PRISM_D), (2, GOLD), (40, framed(PRISM_D, mul(PRISM_D, 0.7))),
                                                  (2, GOLD), (8, PRISM_D)]))
    m.box("trident", -6, -53, -1.5, 12, 3, 3, framed(GOLD, GOLD_D))
    m.box("trident", -2, -55, -2, 4, 2, 4, framed(GOLD, GOLD_D))
    prong_glow = {"front": lambda f_, x, y, w, h: PRISM if y < 3 else None, "*": None}
    for i, x in enumerate((-6, -1, 4)):
        hgt = 12 if x == -1 else 8
        m.box("trident", x, -53 - hgt, -1, 2, hgt, 2, coral(PRISM, 31 + i), glow=prong_glow)
        bx = x - 1 if x < 0 else x + 2
        if x != -1:
            m.box("trident", bx, -53 - hgt + 1, -0.5, 1, 2, 1, PRISM)               # outward barbs
    m.box("trident", -1, -67, -1, 2, 2, 2, (180, 255, 235), glow=(180, 255, 235))

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -5, 0, -5, 10, 16, 10, armour(seed=40 + sx))
        m.box(leg, -5.5, 2, -5.5, 11, 3, 11, bands([(1, GOLD), (2, armour(STEEL_D, seed=43 + sx))]))
        m.box(shin, -4, 0, -4, 8, 12, 8, rotten(seed=41 + sx))
        m.box(shin, -5, 10, -7, 10, 5, 12, armour(STEEL_D, (32, 40, 46), seed=42 + sx))  # heavy sabaton
        m.box(shin, -4.5, -2, -6, 9, 4, 3, armour(seed=44 + sx))                        # knee guard

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.rot("torso", (0, (0, 0, 0)), (1.5, (3, 0, 0)), (3, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (-4, 3, 0)), (3, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.5, (6, 0, 2)), (3, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.0, (8, 0, 0)), (2.0, (0, 0, 0)), (3, (0, 0, 0)))
    idle.pos("torso", (0, (0, 0, 0)), (1.5, (0, 0.8, 0)), (3, (0, 0, 0)))                 # heavy breathing
    idle.rot("beard", (0, (0, 0, 0)), (1.0, (-8, 0, 3)), (2.2, (4, 0, -3)), (3, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 0)), (1.5, (6, 0, 4)), (3, (0, 0, 0)))
    idle.rot("lantern", (0, (0, 0, 0)), (1.0, (-6, 10, 0)), (2.0, (4, -10, 0)), (3, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-4, 0, -3)), (3, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (3, 0, 2)), (3, (0, 0, 0)))
    for i in range(3):
        idle.rot(f"coral{i}", (0, (0, 0, 0)), (0.8 + i * 0.5, (4, 0, (-3, 3, 2)[i])), (3, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (25 * sign, 0, 0)), (0.8, (-25 * sign, 0, 0)), (1.6, (25 * sign, 0, 0)))
    for shin, sign in (("shin_r", 1), ("shin_l", -1)):
        walk.rot(shin, (0, (0, 0, 0)), (0.4, (30 if sign > 0 else 0, 0, 0)), (0.8, (0, 0, 0)),
                 (1.2, (30 if sign < 0 else 0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (-18, 0, 0)), (0.8, (18, 0, 0)), (1.6, (-18, 0, 0)))
    walk.rot("arm_r", (0, (8, 0, 0)), (0.8, (-8, 0, 0)), (1.6, (8, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.4, (0, -1.5, 0)), (0.8, (0, 0, 0)), (1.2, (0, -1.5, 0)), (1.6, (0, 0, 0)))
    walk.rot("torso", (0, (0, 6, 2)), (0.8, (0, -6, -2)), (1.6, (0, 6, 2)))
    walk.rot("cape", (0, (12, 0, 0)), (0.4, (18, 0, 2)), (0.8, (12, 0, 0)), (1.2, (18, 0, -2)), (1.6, (12, 0, 0)))
    walk.rot("beard", (0, (10, 0, 0)), (0.4, (16, 0, 0)), (0.8, (10, 0, 0)), (1.2, (16, 0, 0)), (1.6, (10, 0, 0)))
    walk.rot("chain", (0, (-14, 0, 0)), (0.8, (14, 0, 0)), (1.6, (-14, 0, 0)))

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
