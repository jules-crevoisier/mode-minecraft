"""Gargoyle (Gargouille): a crouching stone grotesque, perched on its knuckles like a cathedral statue.
Folded bat wings whose wrist claws jut above the shoulders, swept-back ram horns, a heavy brow over glowing
red eyes, a fanged grimace, a ridge of stone spines and an arrow-tipped tail. Weathered limestone with
chisel marks, dark crevices, lichen and a few red-glowing cracks over the heart.

Animations: idle (the statue pose, barely breathing), walk (a fast knuckle-lope), swipe (two-claw combo, hits
at 0.6 s and 1.0 s = 12 / 20 ticks), dive (coil, leap with wings spread, crash), wings (wings spread screech).
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

STONE = (138, 134, 124)
STONE_D = (88, 85, 82)
STONE_DD = (50, 48, 52)
STONE_L = (186, 180, 166)
STAIN = (70, 72, 70)
LICHEN = (136, 146, 82)
LICHEN_L = (176, 172, 104)
LICHEN_D = (98, 112, 60)
MOSS = (84, 104, 52)
MEMBRANE = (104, 98, 102)
MEMBRANE_D = (70, 66, 72)
EYE = (255, 70, 40)
EYE_L = (255, 170, 110)
EMBER = (255, 96, 48)
FANG = (226, 220, 200)
MAW = (60, 16, 14)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _u(face, x, w):
    """Distance from the front (-z) end along a side face."""
    return x if face == "left" else w - 1 - x


def lichen_at(x, y, seed, density):
    """Lichen grows in rosettes: a cluster cell is chosen by the seed, then a small round patch with a pale rim
    and a darker heart is drawn in it. Returns a colour or None."""
    if density <= 0:
        return None
    cx, cy = x // 5, y // 5
    if K.h(cx, cy, seed, 31) % 100 >= density * 100:
        return None
    ox, oy = 1 + K.h(cx, cy, seed, 1) % 2, 1 + K.h(cx, cy, seed, 2) % 2
    d = abs(x % 5 - ox) + abs(y % 5 - oy)
    if d == 0:
        return LICHEN_D
    if d == 1:
        return LICHEN
    if d == 2 and K.h(x, y, seed) % 3:
        return LICHEN_L
    return None


def stone(seed=0, base=STONE, lichen=0.12, stains=True, cracks=True, chisel=True):
    """Weathered limestone, painted like a cathedral statue: lit from above (pale top planes and rims, shadowed
    lower sides and undersides), soft chiselled facets, dark rain streaks running down from the top edges, a crack
    on some faces and rosettes of yellow-green lichen on the upper surfaces."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face == "bottom":
            return mix(base, STONE_DD, 0.5)
        if face == "top":
            lc = lichen_at(x, y, seed + fid, lichen * 1.6)
            if lc:
                return lc
            c = mix(base, STONE_L, 0.4)
            if chisel and K.h(x // 3, y // 2, seed) % 4 == 0:
                c = mix(c, base, 0.5)
            return c
        t = y / max(1, h - 1)
        c = mix(mix(base, STONE_L, 0.22), mix(base, STONE_D, 0.5), t)
        if chisel:
            c = mul(c, (0.96, 1.0, 1.04)[K.h(x // 3, y // 3, seed, fid) % 3])     # chiselled facets
        if y == 0 and h > 2:
            c = mix(c, STONE_L, 0.45)                                              # lit upper rim
        if (x == 0 or x == w - 1) and w > 2:
            c = mix(c, STONE_D, 0.3)                                               # rounded-off edges
        if stains and w >= 4 and h > 4 and K.h(x, seed, fid) % 7 == 0 and 0 < y < 2 + K.h(x, seed, 7) % (h - 2):
            c = mix(c, STAIN, 0.25)                                                # rain streaks
        if cracks and w >= 5 and h >= 6 and K.h(seed, fid, 9) % 3 == 0:
            cx = 1 + K.h(seed, fid) % max(1, w - 3)
            if x == cx + (y // 3) % 2 and 0 < y < h - 2:
                return mix(c, STONE_DD, 0.7)
        if y < h * 0.45:
            lc = lichen_at(x, y, seed + fid, lichen)
            if lc:
                return lc
        if y == h - 1 and h > 3 and K.h(x, seed, fid, 3) % 4 == 0:
            return MOSS                                                            # moss in the bottom crevice
        return c
    return f


HEART = {(5, 0), (5, 1), (4, 2), (4, 3), (5, 3), (6, 4), (3, 4), (2, 5), (7, 5), (6, 6), (2, 6)}


def heart_cracks(face, x, y, w, h):
    """Glowing red fissures over the chest, forking from the collarbone down over the heart."""
    if face != "front":
        return None
    return (*EMBER, 230) if (x, y) in HEART else None


def heart_paint(face, x, y, w, h):
    if heart_cracks(face, x, y, w, h):
        return (120, 30, 20)
    return stone(2)(face, x, y, w, h)


def membrane(seed=0):
    """A folded stone bat wing: three finger ribs fanning from the wrist (top front corner) to the lower edge,
    slate membrane stretched between them, darkening toward the bottom, scalloped between the rib tips."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STONE_D
        u = _u(face, x, w)
        v = y / max(1, h - 1)
        tips = [0.0] + [(k / 3) * (w - 1) for k in (1, 2, 3)]
        for a, b in zip(tips, tips[1:]):
            if a <= u <= b and b > a:
                depth = int(3.2 * math.sin(math.pi * (u - a) / (b - a)))
                if y > h - 1 - depth:
                    return None
        for k in (1, 2):
            if round(tips[k] * (0.25 + 0.75 * v)) == u:
                return mix(STONE, STONE_L, 0.3 * (1 - v))                          # a finger rib
        if u == w - 1 or y == 0:
            return STONE
        c = mix(MEMBRANE, MEMBRANE_D, min(1.0, v * 0.9))
        if K.h(u // 4, y // 5, seed) % 5 == 0:
            c = mix(c, STAIN, 0.2)
        return c
    return f


def face_front(face, x, y, w, h):
    """Skull front (w=7, h=6): heavy brow, deep sockets with red eyes, wrinkled cheeks."""
    base = stone(70, chisel=False, cracks=False, lichen=0, stains=False)(face, x, y, w, h)
    if y == 0:
        return mix(base, STONE_L, 0.3)
    if y == 1:
        return mix(base, STONE_D, 0.25) if x == 3 else mix(base, STONE_L, 0.2)   # brow, a frown furrow
    if y == 2 and x in (1, 2, 4, 5):
        return STONE_DD                                                           # under-brow shadow
    if y == 3 and x in (1, 2, 4, 5):
        return (120, 20, 10)
    if y >= 4 and x in (0, 6):
        return mix(base, STONE_D, 0.5)
    if y == 5 and x in (2, 4):
        return mix(base, STONE_D, 0.6)                                            # cheek furrows
    return base


def eye_glow(face, x, y, w, h):
    if face == "front" and y == 3 and x in (1, 2, 4, 5):
        return EYE if x in (1, 5) else EYE_L
    if face == "front" and y == 2 and x in (2, 4):
        return (*EYE, 110)
    return None


def spade(face, x, y, w, h):
    """The arrowhead of the tail: a flat diamond (corners cut away)."""
    if face in ("front", "back"):
        cx = (w - 1) / 2
        if abs(x - cx) > (y + 0.6 if y < h / 2 else h - y - 0.4):
            return None
        return STONE_L if y == 0 else mix(STONE, STONE_D, y / h)
    return STONE_D


def wave(anim, part, length, amp, phase=0.0, base=(0, 0, 0), kind="rot", n=8):
    """A seamless sine loop: base + amp * sin(2 pi (t / length + phase))."""
    keys = []
    for i in range(n + 1):
        s = math.sin(2 * math.pi * (i / n + phase))
        keys.append((round(length * i / n, 4), tuple(round(base[k] + amp[k] * s, 3) for k in range(3))))
    getattr(anim, kind)(part, *keys)


def build():
    m = Model("gargoyle", seed=47, shadow=0.55, walk_speed=1.6, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("torso", "bone", pivot=(0, -12, 2), rot=(38, 0, 0))
    m.part("head", "torso", pivot=(0, -13, -1.5), rot=(-34, 0, 0))
    m.part("jaw", "head", pivot=(0, -1.5, -2))
    for side, sx in (("r", -1), ("l", 1)):
        # ram horns: out and up from the temples, then curling back and down behind the ears
        m.part(f"horn_{side}", "head", pivot=(sx * 3, -6, 0), rot=(-15, 0, 55 * sx))
        m.part(f"horn_{side}2", f"horn_{side}", pivot=(0, -4, 0), rot=(-65, 0, -10 * sx))
        m.part(f"horn_{side}3", f"horn_{side}2", pivot=(0, -3, 0), rot=(-70, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "torso", pivot=(sx * 5.5, -11.5, -0.5), rot=(-46, 0, -6 * sx))
        m.part(f"forearm_{side}", f"arm_{side}", pivot=(0, 7, 0), rot=(-12, 0, 0))
        m.part(f"wing_{side}", "torso", pivot=(sx * 3.5, -13, 3), rot=(-40, -14 * sx, 8 * -sx))
        m.part(f"wingtip_{side}", f"wing_{side}", pivot=(0, -11, 0), rot=(-10, 0, 0))
        m.part(f"thigh_{side}", "bone", pivot=(sx * 3.5, -11.5, 2.5), rot=(-70, 8 * sx, 0))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 7, 0), rot=(110, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 9, 0), rot=(-40, 0, 0))
    m.part("tail", "bone", pivot=(0, -10.5, 5), rot=(70, 0, 0))
    m.part("tail2", "tail", pivot=(0, 7, 0), rot=(30, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 6, 0), rot=(35, 0, 0))

    # torso: pot belly and a broad hunched chest with glowing heart cracks, a ridge of stone spines down the back
    m.box("torso", -4, -6, -3, 8, 7, 6, stone(1))
    m.box("torso", -5, -13, -3.5, 10, 8, 7, {"front": heart_paint, "*": stone(2)}, glow={"front": heart_cracks})
    m.box("torso", -6, -14, -2.5, 12, 3, 5, stone(3, lichen=0.25))                 # shoulder yoke
    m.box("torso", -3.5, -12, -4, 7, 3, 1, stone(5, stains=False, cracks=False))   # pectoral ridge
    for i, (y, hh) in enumerate(((-14, 4), (-10.5, 3), (-7.5, 3), (-4.5, 2))):
        m.box("torso", -0.5, y - hh + 1, 3, 1, hh, 2 + (i < 2), stone(6 + i, chisel=False, lichen=0))

    # head: heavy skull with a pushed-out snout, fanged jaw, pointed ears and ram horns
    m.box("head", -3.5, -6, -4.5, 7, 6, 7, {"front": face_front, "*": stone(70, lichen=0.2)}, glow={"front": eye_glow})
    m.box("head", -4, -5.5, -5, 8, 1, 2, stone(71, cracks=False, stains=False))   # brow ridge
    m.box("head", -1, -6.5, -4.8, 2, 1, 3, stone(79, cracks=False, stains=False))  # a frowning crest
    m.box("head", -2, -3, -7, 4, 2, 3, {
        "front": lambda f_, x, y, w, h: STONE_DD if y == 1 and x in (0, 3) else stone(72)(f_, x, y, w, h),
        "*": stone(72, stains=False)})                                             # snout with nostrils
    m.box("head", -2.5, -1.5, -6.5, 5, 1, 2, {"bottom": FANG, "front": lambda f_, x, y, w, h:
          FANG if x % 2 == 0 else (40, 14, 12), "*": stone(73)})                   # upper fangs
    for sx in (-1, 1):
        m.box("head", 3.5 if sx > 0 else -5.5, -6, -1, 2, 3, 1, stone(74 + sx))     # ear
        m.box("head", 4.5 if sx > 0 else -6.5, -8, -1, 2, 2, 1, stone(76 + sx))     # ear tip
    m.box("jaw", -2.5, 0, -5, 5, 2, 5, {"top": MAW, "front": lambda f_, x, y, w, h:
          FANG if y == 0 and x in (0, 2, 4) else stone(78)(f_, x, y, w, h), "*": stone(78, stains=False)},
          glow={"top": lambda f_, x, y, w, h: (255, 80, 40, 90)})

    def horn(seed, base):
        def f(f_, x, y, w, h):
            c = stone(seed, base=base, lichen=0, cracks=False, stains=False)(f_, x, y, w, h)
            if f_ not in ("top", "bottom") and y % 2 == 1:
                return mix(c, STONE_DD, 0.4)                                       # ridged rings
            return c
        return f
    for side in ("r", "l"):
        m.box(f"horn_{side}", -1.5, -4, -1.5, 3, 4, 3, horn(80, (124, 116, 104)))
        m.box(f"horn_{side}2", -1, -3, -1, 2, 3, 2, horn(81, (108, 100, 92)))
        m.box(f"horn_{side}3", -0.5, -3, -0.5, 1, 3, 1, horn(82, (90, 84, 80)))

    # arms: knuckle-walking, thick forearms, three-taloned stone hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2.5, -2.5, -2.5, 5, 5, 5, stone(90 + sx, lichen=0.3))         # round shoulder
        m.box(arm, -1.5, 1, -1.5, 3, 7, 3, stone(92 + sx))
        m.box(fore, -2, 0, -2, 4, 7, 4, stone(94 + sx))                           # heavy forearm
        m.box(fore, -2, 6.5, -2.5, 4, 2, 4, stone(96 + sx))
        for i, dx in enumerate((-1.5, -0.2, 1.1)):
            m.box(fore, dx, 7.5, -3.5, 1, 2, 2, lambda f_, x, y, w, h: STONE_DD if f_ == "front" else STONE_D)

    # wings: folded high behind the body, the wrist claws hooking forward above the head
    for side, sx in (("r", -1), ("l", 1)):
        w, tip = f"wing_{side}", f"wingtip_{side}"
        m.box(w, -1, -11, -1, 2, 12, 2, stone(100 + sx, lichen=0))                # the wing arm
        m.box(tip, -0.5, -3, -0.5, 1, 3, 1, stone(104 + sx, lichen=0, cracks=False))
        m.box(tip, -0.5, -3, -1.5, 1, 1, 1, STONE_DD)                              # the hooked wrist claw
        m.box(tip, -0.5, -0.5, 0.5, 1, 1, 13, stone(102 + sx, lichen=0, cracks=False))  # the long finger bone
        m.box(w, 0, -10.5, 0.5, 0, 22, 13, {"left": membrane(101 + sx), "right": membrane(101 + sx), "*": None})

    # legs: crouched digitigrade legs with taloned feet
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"thigh_{side}", -2, -1, -2, 4, 8, 4, stone(110 + sx))
        m.box(f"shin_{side}", -1.5, 0, -1.5, 3, 9, 3, stone(112 + sx))
        m.box(f"foot_{side}", -2, 0, -4, 4, 2, 5, stone(114 + sx, lichen=0.3))
        for i, dx in enumerate((-2, -0.5, 1)):
            m.box(f"foot_{side}", dx, 0.5, -5.5, 1, 1, 2, STONE_DD)

    # tail: three tapering segments curling up behind, ending in a flat arrowhead
    m.box("tail", -1.5, 0, -1.5, 3, 7, 3, stone(120))
    m.box("tail2", -1, 0, -1, 2, 6, 2, stone(121))
    m.box("tail3", -0.5, 0, -0.5, 1, 4, 1, stone(122))
    m.box("tail3", -2, 3.5, -0.5, 4, 4, 1, {"front": spade, "back": spade, "*": None})

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))
    # idle: the statue pose, barely breathing; the tail tip flicks, the wings settle, and every few seconds the
    # head snaps to one side, holds, and slowly turns back (a statue that is watching you)
    idle = m.anim("idle", 4.0)
    idle.rot("torso", (0, (0, 0, 0)), (2.0, (-1.5, 0, 0)), (4.0, (0, 0, 0)))
    idle.scale("torso", (0, (1, 1, 1)), (2.0, (1.02, 1.01, 1.03)), (4.0, (1, 1, 1)))
    idle.rot("head", (0, (0, 0, 0)), (1.6, (0, 0, 0)), (1.75, (4, 26, 0), "linear"), (2.6, (4, 24, 0)), (3.6, (0, 0, 0)),
             (4.0, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (1.75, (0, 0, 0)), (1.9, (10, 0, 0)), (2.3, (0, 0, 0)), (4.0, (0, 0, 0)))
    wave(idle, "tail", 4.0, (0, 5, 0), 0.0)
    wave(idle, "tail2", 4.0, (0, 8, 0), 0.12)
    wave(idle, "tail3", 4.0, (6, 12, 0), 0.25)
    for side, sx in sides:
        wave(idle, f"wing_{side}", 4.0, (2, 2 * sx, 0), 0.1)
        wave(idle, f"wingtip_{side}", 4.0, (4, 0, 0), 0.22)

    # walk: a fast knuckle-lope; the wings bounce a beat late, the tail swings, the head stays level
    walk = m.anim("walk", 0.8)
    for side, sign in (("r", 1), ("l", -1)):
        walk.rot(f"thigh_{side}", (0, (22 * sign, 0, 0)), (0.4, (-22 * sign, 0, 0)), (0.8, (22 * sign, 0, 0)))
        walk.rot(f"shin_{side}", (0, (0, 0, 0)), (0.2, (-25 if sign > 0 else 0, 0, 0)), (0.4, (0, 0, 0)),
                 (0.6, (-25 if sign < 0 else 0, 0, 0)), (0.8, (0, 0, 0)))
        walk.rot(f"arm_{side}", (0, (-26 * sign, 0, 0)), (0.4, (26 * sign, 0, 0)), (0.8, (-26 * sign, 0, 0)))
        walk.rot(f"forearm_{side}", (0, (0, 0, 0)), (0.2, (-20 if sign < 0 else 0, 0, 0)), (0.4, (0, 0, 0)),
                 (0.6, (-20 if sign > 0 else 0, 0, 0)), (0.8, (0, 0, 0)))
        wave(walk, f"wing_{side}", 0.8, (8, 4 * sign, 0), 0.62, base=(4, 0, 0), n=8)
        wave(walk, f"wingtip_{side}", 0.8, (10, 0, 0), 0.75, n=8)
    walk.pos("bone", (0, (0, 0, 0)), (0.2, (0, 1.2, 0)), (0.4, (0, 0, 0)), (0.6, (0, 1.2, 0)), (0.8, (0, 0, 0)))
    walk.rot("torso", (0, (4, 0, 0)), (0.2, (8, 0, 0)), (0.4, (4, 0, 0)), (0.6, (8, 0, 0)), (0.8, (4, 0, 0)))
    walk.rot("head", (0, (-4, 0, 0)), (0.2, (-8, 0, 0)), (0.4, (-4, 0, 0)), (0.6, (-8, 0, 0)), (0.8, (-4, 0, 0)))
    wave(walk, "tail", 0.8, (0, 10, 0), 0.0, n=8)
    wave(walk, "tail2", 0.8, (0, 12, 0), 0.15, n=8)
    wave(walk, "tail3", 0.8, (0, 16, 0), 0.3, n=8)

    # swipe: rears up and winds the right claw high and wide, wings flared (telegraph), rakes down (hit 0.6 s);
    # winds the left claw back over the other shoulder and rakes again (hit 1.0 s)
    a = m.anim("swipe", 1.5)
    a.rot("torso", (0, (0, 0, 0)), (0.35, (-26, 26, 0)), (0.5, (-32, 30, 0)), (0.6, (4, -25, 0), "linear"),
          (0.85, (-26, -26, 0)), (1.0, (8, 25, 0), "linear"), (1.2, (4, 20, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (18, -16, 0)), (0.6, (-6, 10, 0)), (0.85, (16, 14, 0)), (1.0, (-6, -10, 0)),
          (1.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.35, (28, 0, 0)), (0.6, (12, 0, 0)), (0.85, (32, 0, 0)), (1.0, (14, 0, 0)),
          (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (-120, 0, 45)), (0.5, (-135, 0, 50)), (0.6, (10, 0, -20), "linear"),
          (0.85, (20, 0, -10)), (1.2, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.6, (10, 0, 0), "linear"), (1.0, (0, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-20, 0, -10)), (0.75, (-125, 0, -45)), (0.85, (-135, 0, -50)),
          (1.0, (10, 0, 20), "linear"), (1.2, (12, 0, 12)), (1.5, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.85, (-30, 0, 0)), (1.0, (10, 0, 0), "linear"),
          (1.5, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.4, (5, 40 * sx, -25 * sx)), (0.6, (0, 20 * sx, -10 * sx)),
              (0.85, (5, 35 * sx, -22 * sx)), (1.0, (0, 15 * sx, -8 * sx)), (1.5, (0, 0, 0)))
        a.rot(f"wingtip_{side}", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (0.65, (10, 0, 0)), (0.85, (-15, 0, 0)),
              (1.05, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.5, (0, -25, 0)), (0.7, (0, 20, 0)), (0.85, (0, 25, 0)), (1.1, (0, -20, 0)),
          (1.5, (0, 0, 0)))
    a.rot("tail3", (0, (0, 0, 0)), (0.6, (0, -30, 0)), (0.8, (0, 25, 0)), (1.0, (0, 30, 0)), (1.2, (0, -25, 0)),
          (1.5, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, 3, 1.5)), (0.6, (0, 0, -3), "linear"), (0.85, (0, 2, -3)),
          (1.0, (0, 0, -6), "linear"), (1.2, (0, 0, -6)), (1.5, (0, 0, 0)))

    # dive: coils low with the wings half open and the head down (0 - 0.5 s), launches (0.5 s) wings spread wide,
    # claws forward through the air, crashes (1.1 s), folds up
    a = m.anim("dive", 1.6)
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, -3, 2.5)), (0.6, (0, 4, -2), "linear"), (1.1, (0, 2, -4)),
          (1.2, (0, -2, -4), "linear"), (1.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (18, 0, 0)), (0.6, (30, 0, 0)), (1.1, (40, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (0.6, (-25, 0, 0)), (1.1, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (12, 0, 0)), (0.6, (30, 0, 0)), (1.1, (35, 0, 0)), (1.3, (5, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.5, (10, 40 * sx, -15 * sx)), (0.6, (20, 85 * sx, -50 * sx), "linear"),
              (0.85, (30, 85 * sx, -55 * sx)), (1.1, (25, 80 * sx, -40 * sx)), (1.25, (10, 40 * sx, -10 * sx)),
              (1.6, (0, 0, 0)))
        a.rot(f"wingtip_{side}", (0, (0, 0, 0)), (0.5, (-15, 0, 0)), (0.6, (15, 0, 0)), (0.75, (-10, 0, 0)),
              (0.95, (12, 0, 0)), (1.1, (0, 0, 0)), (1.6, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (35, 0, 0)), (0.6, (-80, 0, 20 * sx)), (1.1, (-70, 0, 10 * sx)),
              (1.2, (10, 0, 0), "linear"), (1.6, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (0.6, (55, 0, 0)), (1.1, (40, 0, 0)), (1.2, (0, 0, 0)),
              (1.6, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.6, (-50, 0, 0)), (1.1, (-30, 0, 0)), (1.2, (0, 0, 0)),
              (1.6, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.5, (10, 0, 0)), (0.6, (-40, 0, 0)), (1.1, (-35, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("tail3", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.8, (25, 0, 0)), (1.1, (-10, 0, 0)), (1.3, (20, 0, 0)),
          (1.6, (0, 0, 0)))

    # wings: the statue wakes - wings unfurl wide, it rears and screeches, then folds back
    a = m.anim("wings", 1.6)
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-28, 0, 0)), (1.1, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-18, 0, 0)), (0.6, (-22, 6, 0)), (0.85, (-22, -6, 0)), (1.1, (-22, 0, 0)),
          (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (40, 0, 0)), (1.1, (42, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.4, (10, 90 * sx, -55 * sx)), (0.75, (20, 95 * sx, -45 * sx)),
              (1.1, (10, 90 * sx, -55 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"wingtip_{side}", (0, (0, 0, 0)), (0.4, (-25, 0, 0)), (0.55, (10, 0, 0)), (0.75, (-10, 0, 0)),
              (0.95, (8, 0, 0)), (1.1, (-5, 0, 0)), (1.6, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.4, (-30, 0, 45 * -sx)), (1.1, (-30, 0, 50 * -sx)), (1.6, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.4, (-20, 0, 0)), (1.1, (-20, 0, 0)), (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.4, (0, 2, 0)), (1.1, (0, 2, 0)), (1.6, (0, 0, 0)))
