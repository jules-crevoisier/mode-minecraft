"""Gargoyle (Gargouille): a crouching stone grotesque, perched on its knuckles like a cathedral statue.
Folded bat wings whose wrist claws jut above the shoulders, swept-back ram horns, a heavy brow over glowing
red eyes, a fanged grimace, a ridge of stone spines and an arrow-tipped tail. Weathered limestone with
chisel marks, dark crevices, lichen and a few red-glowing cracks over the heart.

Animations: idle (the statue pose, barely breathing), walk (a fast knuckle-lope), swipe (two-claw combo, hits
at 0.6 s and 1.0 s = 12 / 20 ticks), dive (coil, leap with wings spread, crash), wings (wings spread screech).
"""
from ..models import Model
from ..texgen import mix, mul

STONE = (134, 131, 124)
STONE_D = (84, 82, 80)
STONE_DD = (52, 50, 52)
STONE_L = (176, 172, 162)
LICHEN = (128, 140, 84)
LICHEN2 = (170, 150, 80)
EYE = (255, 70, 40)
EMBER = (255, 96, 48)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def stone(seed=0, base=STONE, chisel=True, lichen=True, cracks=True):
    """Weathered carved stone: chisel stripes, darker crevices toward edges and bottom, a crack or two,
    lichen spots on top faces, light-catching top rims."""
    def f(face, x, y, w, h):
        r = _h(x, y, seed, FACE_N[face])
        c = mul(base, 1 + ((r % 100) - 50) / 700)
        if face == "top":
            c = mix(c, STONE_L, 0.3)
            if lichen and r % 13 == 0:
                c = mix(c, LICHEN if r % 2 else LICHEN2, 0.7)
            return c
        if face == "bottom":
            return mix(c, STONE_DD, 0.45)
        if chisel and (x + y * 2 + seed) % 5 == 0:
            c = mul(c, 0.93)                         # diagonal chisel strokes
        if (x == 0 or x == w - 1) and w > 2:
            c = mix(c, STONE_D, 0.35)                # edge crevice
        if y == 0 and h > 2:
            c = mix(c, STONE_L, 0.35)                # catch light on the upper rim
        t = y / max(1, h - 1)
        c = mix(c, STONE_D, 0.3 * t)
        if cracks and w >= 4 and h >= 4:
            cx = 1 + _h(seed, FACE_N[face]) % max(1, w - 2)
            if abs(x - (cx + (y // 2) % 2 - (y // 3) % 2)) == 0 and (_h(seed, FACE_N[face], 9) % 3 == 0):
                c = STONE_DD
        if lichen and r % 61 == 0:
            c = mix(c, LICHEN, 0.6)
        return c
    return f


def heart_cracks(face, x, y, w, h):
    """Glowing red fissures over the chest."""
    if face != "front":
        return None
    pts = {(4, 1), (5, 2), (4, 3), (5, 3), (3, 4), (6, 4), (6, 5), (2, 5), (7, 1)}
    return (*EMBER, 220) if (x, y) in pts else None


def membrane(seed=0):
    """Stone wing membrane: darker slate between pale ribs, scalloped bottom edge between the fingers."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STONE_D
        # scallops: four bays along the horizontal (z) axis of the plane
        bay = w / 4.0
        u = (x % bay) / bay
        depth = int(3 * (1 - abs(u - 0.5) * 2))
        if y >= h - 1 - depth:
            return None
        rib = int(x % bay) == 0
        c = STONE if rib else mix(STONE_D, (96, 92, 98), 0.4)
        if not rib and (y + x * 3 + seed) % 9 == 0:
            c = mix(c, STONE_DD, 0.4)
        r = _h(x, y, seed)
        if r % 17 == 0:
            c = mul(c, 0.9)
        return mix(c, STONE_DD, 0.3 * y / max(1, h - 1))
    return f


def face_front(face, x, y, w, h):
    """Skull front (w=7, h=6): heavy brow, deep sockets with red eyes, wrinkled cheeks."""
    base = stone(70, chisel=False, cracks=False, lichen=False)(face, x, y, w, h)
    if y == 1:
        return mix(base, STONE_L, 0.25)               # brow ridge lit from above
    if y == 2 and x in (1, 2, 4, 5):
        return STONE_DD                               # under-brow shadow
    if y == 3 and x in (1, 2, 4, 5):
        return (120, 20, 10)
    if y >= 4 and x in (0, 6):
        return mix(base, STONE_D, 0.5)
    if y == 5 and x in (2, 4):
        return mix(base, STONE_D, 0.6)                # cheek furrows
    return base


def eye_glow(face, x, y, w, h):
    if face == "front" and y == 3 and x in (1, 2, 4, 5):
        return EYE if x in (2, 4) else (255, 140, 90)
    if face == "front" and y == 2 and x in (2, 4):
        return (*EYE, 110)
    return None


def build():
    m = Model("gargoyle", seed=47, shadow=0.55, walk_speed=1.6, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("torso", "bone", pivot=(0, -12, 2), rot=(38, 0, 0))
    m.part("head", "torso", pivot=(0, -13, -1.5), rot=(-34, 0, 0))
    m.part("jaw", "head", pivot=(0, -1.5, -2))
    m.part("horn_r", "head", pivot=(-3, -6, 0), rot=(-35, 0, -30))
    m.part("horn_r2", "horn_r", pivot=(0, -5, 0), rot=(-50, 0, 10))
    m.part("horn_r3", "horn_r2", pivot=(0, -4, 0), rot=(-50, 0, 0))
    m.part("horn_l", "head", pivot=(3, -6, 0), rot=(-35, 0, 30))
    m.part("horn_l2", "horn_l", pivot=(0, -5, 0), rot=(-50, 0, -10))
    m.part("horn_l3", "horn_l2", pivot=(0, -4, 0), rot=(-50, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "torso", pivot=(sx * 5.5, -11.5, -0.5), rot=(-46, 0, -6 * sx))
        m.part(f"forearm_{side}", f"arm_{side}", pivot=(0, 7, 0), rot=(-12, 0, 0))
        m.part(f"wing_{side}", "torso", pivot=(sx * 3.5, -13, 3), rot=(-40, -12 * sx, 6 * -sx))
        m.part(f"wingtip_{side}", f"wing_{side}", pivot=(0, -9, 0))
        m.part(f"thigh_{side}", "bone", pivot=(sx * 3.5, -11.5, 2.5), rot=(-70, 8 * sx, 0))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 7, 0), rot=(110, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 9, 0), rot=(-40, 0, 0))
    m.part("tail", "bone", pivot=(0, -10.5, 5), rot=(62, 0, 0))
    m.part("tail2", "tail", pivot=(0, 7, 0), rot=(-40, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 6, 0), rot=(-30, 0, 0))

    # torso: pot belly and a broad hunched chest, a ridge of spines down the back
    m.box("torso", -4, -6, -3, 8, 7, 6, stone(1))
    m.box("torso", -5, -13, -3.5, 10, 8, 7, {"front": stone(2), "*": stone(2)}, glow={"front": heart_cracks})
    m.box("torso", -6, -14, -2.5, 12, 3, 5, stone(3))                    # shoulder yoke
    for i, (y, hh) in enumerate(((-14, 3), (-11, 3), (-8, 2), (-5, 2))):
        m.box("torso", -0.5, y - hh + 1, 3, 1, hh, 2, stone(4 + i, chisel=False))

    # head: heavy skull with a pushed-out snout, fanged jaw, pointed ears and ram horns
    m.box("head", -3.5, -6, -4.5, 7, 6, 7, {"front": face_front, "*": stone(70)}, glow={"front": eye_glow})
    m.box("head", -4, -5.5, -5, 8, 1, 2, stone(71, cracks=False))       # brow ridge
    m.box("head", -2, -3, -7, 4, 2, 3, {
        "front": lambda f_, x, y, w, h: STONE_DD if y == 1 and x in (0, 3) else stone(72)(f_, x, y, w, h),
        "*": stone(72)})                                                   # snout with nostrils
    m.box("head", -2.5, -1.5, -6.5, 5, 1, 2, {"bottom": (220, 214, 196), "front": lambda f_, x, y, w, h:
          (226, 220, 200) if x % 2 == 0 else (40, 14, 12), "*": stone(73)})  # upper fangs
    for sx in (-1, 1):
        m.box("head", 3.5 if sx > 0 else -5.5, -6, -1, 2, 3, 1, stone(74 + sx))     # ear
        m.box("head", 4.5 if sx > 0 else -6.5, -8, -1, 2, 2, 1, stone(76 + sx))     # ear tip
    m.box("jaw", -2.5, 0, -5, 5, 2, 5, {"top": (60, 16, 14), "front": lambda f_, x, y, w, h:
          (226, 220, 200) if y == 0 and x in (0, 2, 4) else stone(78)(f_, x, y, w, h), "*": stone(78)},
          glow={"top": lambda f_, x, y, w, h: (255, 80, 40, 90)})
    def horn(seed, base):
        return lambda f_, x, y, w, h: mix(stone(seed, base=base, lichen=False, cracks=False)(f_, x, y, w, h),
                                          STONE_DD, 0.35) if (y % 2 == 0 and f_ not in ("top", "bottom")) else \
            stone(seed, base=base, lichen=False, cracks=False)(f_, x, y, w, h)
    for side in ("r", "l"):
        m.box(f"horn_{side}", -1.5, -5, -1.5, 3, 5, 3, horn(80, (110, 102, 94)))
        m.box(f"horn_{side}2", -1, -4, -1, 2, 4, 2, horn(81, (96, 90, 84)))
        m.box(f"horn_{side}3", -0.5, -4, -0.5, 1, 4, 1, horn(82, (70, 66, 64)))

    # arms: knuckle-walking, thick forearms, three-taloned stone hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2, -2, -2, 4, 4, 4, stone(90 + sx))
        m.box(arm, -1.5, 1, -1.5, 3, 7, 3, stone(92 + sx))
        m.box(fore, -1.5, 0, -1.5, 3, 7, 3, stone(94 + sx))
        m.box(fore, -2, 6.5, -2.5, 4, 2, 4, stone(96 + sx))
        for i, dx in enumerate((-1.5, -0.2, 1.1)):
            m.box(fore, dx, 7.5, -3.5, 1, 2, 2, lambda f_, x, y, w, h: STONE_DD if f_ == "front" else STONE_D)

    # wings: folded sheets behind the body; the wrist claw pokes above the shoulder
    for side, sx in (("r", -1), ("l", 1)):
        w = f"wing_{side}"
        m.box(w, -1, -9, -1, 2, 10, 2, stone(100 + sx, lichen=False))
        m.box(f"wingtip_{side}", -0.5, -3, -0.5, 1, 3, 1, STONE_DD)       # wrist claw above the shoulder
        m.box(f"wingtip_{side}", -0.5, -0.5, 0.5, 1, 1, 12, stone(102 + sx, lichen=False))  # long finger bone
        m.box(f"wingtip_{side}", -0.5, 0, 6, 1, 8, 1, stone(103 + sx, lichen=False))      # second finger
        m.box(w, 0, -8.5, 0.5, 0, 19, 12, {"left": membrane(101 + sx), "right": membrane(101 + sx), "*": None})

    # legs: crouched digitigrade legs with taloned feet
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"thigh_{side}", -2, -1, -2, 4, 8, 4, stone(110 + sx))
        m.box(f"shin_{side}", -1.5, 0, -1.5, 3, 9, 3, stone(112 + sx))
        m.box(f"foot_{side}", -2, 0, -4, 4, 2, 5, stone(114 + sx))
        for i, dx in enumerate((-2, -0.5, 1)):
            m.box(f"foot_{side}", dx, 0.5, -5.5, 1, 1.5 if False else 1, 2, STONE_DD)

    # tail: three tapering segments and an arrowhead
    m.box("tail", -1.5, 0, -1.5, 3, 7, 3, stone(120))
    m.box("tail2", -1, 0, -1, 2, 6, 2, stone(121))
    m.box("tail3", -0.5, 0, -0.5, 1, 4, 1, stone(122))
    m.box("tail3", -1.5, 4, -1, 3, 3, 2, stone(123, chisel=False))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.rot("torso", (0, (0, 0, 0)), (2.0, (-1.5, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (1, 4, 0)), (4.0, (0, 0, 0)))
    idle.rot("tail3", (0, (0, 0, 0)), (2.0, (0, 6, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 0.8)
    for side, sign in (("r", 1), ("l", -1)):
        walk.rot(f"thigh_{side}", (0, (22 * sign, 0, 0)), (0.4, (-22 * sign, 0, 0)), (0.8, (22 * sign, 0, 0)))
        walk.rot(f"shin_{side}", (0, (0, 0, 0)), (0.2, (-25 if sign > 0 else 0, 0, 0)), (0.4, (0, 0, 0)),
                 (0.6, (-25 if sign < 0 else 0, 0, 0)), (0.8, (0, 0, 0)))
        walk.rot(f"arm_{side}", (0, (-26 * sign, 0, 0)), (0.4, (26 * sign, 0, 0)), (0.8, (-26 * sign, 0, 0)))
        walk.rot(f"wing_{side}", (0, (0, 0, 0)), (0.2, (8, 8 * sign, 0)), (0.4, (0, 0, 0)), (0.6, (8, 8 * sign, 0)),
                 (0.8, (0, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.2, (0, 1.2, 0)), (0.4, (0, 0, 0)), (0.6, (0, 1.2, 0)), (0.8, (0, 0, 0)))
    walk.rot("torso", (0, (4, 0, 0)), (0.2, (8, 0, 0)), (0.4, (4, 0, 0)), (0.6, (8, 0, 0)), (0.8, (4, 0, 0)))
    walk.rot("tail", (0, (0, 10, 0)), (0.4, (0, -10, 0)), (0.8, (0, 10, 0)))

    # swipe: rear up, right claw from high (hit 0.6 s), then the left (hit 1.0 s)
    a = m.anim("swipe", 1.5)
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-30, 20, 0)), (0.6, (2, -25, 0), "linear"), (0.85, (-24, -18, 0)),
          (1.0, (6, 25, 0), "linear"), (1.2, (4, 20, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (0.6, (-6, 10, 0)), (0.85, (14, 0, 0)), (1.0, (-6, -10, 0)),
          (1.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (25, 0, 0)), (1.0, (30, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-125, 0, 30)), (0.6, (10, 0, -20), "linear"), (0.85, (20, 0, -10)),
          (1.2, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-20, 0, -10)), (0.85, (-130, 0, -30)), (1.0, (10, 0, 20), "linear"),
          (1.2, (12, 0, 12)), (1.5, (0, 0, 0)))
    a.rot("wing_r", (0, (0, 0, 0)), (0.5, (0, -25, 15)), (1.0, (0, -15, 8)), (1.5, (0, 0, 0)))
    a.rot("wing_l", (0, (0, 0, 0)), (0.5, (0, 25, -15)), (1.0, (0, 15, -8)), (1.5, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, 3, 1)), (0.6, (0, 0, -3), "linear"), (0.85, (0, 2, -3)),
          (1.0, (0, 0, -6), "linear"), (1.2, (0, 0, -6)), (1.5, (0, 0, 0)))

    # dive: coil (0-0.5), launch with wings spread, claws forward through the air, crash (1.1 s), fold
    a = m.anim("dive", 1.6)
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, -2.5, 2)), (0.6, (0, 4, -2), "linear"), (1.1, (0, 2, -4)),
          (1.2, (0, -2, -4), "linear"), (1.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (0.6, (30, 0, 0)), (1.1, (40, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-10, 0, 0)), (0.6, (-25, 0, 0)), (1.1, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (30, 0, 0)), (1.1, (35, 0, 0)), (1.3, (5, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.5, (10, 30 * sx, 0)), (0.6, (20, 85 * sx, -50 * sx), "linear"),
              (1.1, (25, 80 * sx, -40 * sx)), (1.25, (10, 40 * sx, -10 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (0.6, (-80, 0, 20 * sx)), (1.1, (-70, 0, 10 * sx)),
              (1.2, (10, 0, 0), "linear"), (1.6, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.5, (-15, 0, 0)), (0.6, (55, 0, 0)), (1.1, (40, 0, 0)), (1.2, (0, 0, 0)),
              (1.6, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.5, (15, 0, 0)), (0.6, (-50, 0, 0)), (1.1, (-30, 0, 0)), (1.2, (0, 0, 0)),
              (1.6, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (1.1, (-35, 0, 0)), (1.6, (0, 0, 0)))

    # wings: the statue wakes - wings unfurl wide, it rears and screeches, then folds back
    a = m.anim("wings", 1.6)
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-28, 0, 0)), (1.1, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-18, 0, 0)), (1.1, (-22, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (40, 0, 0)), (1.1, (42, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.4, (10, 90 * sx, -55 * sx)), (0.75, (20, 95 * sx, -45 * sx)),
              (1.1, (10, 90 * sx, -55 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.4, (-30, 0, 45 * -sx)), (1.1, (-30, 0, 50 * -sx)), (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.4, (0, 2, 0)), (1.1, (0, 2, 0)), (1.6, (0, 0, 0)))
    return m
