"""Sea Serpent (Serpent de mer): a rare mini-boss of the deep oceans. A horned, crested head with a hinged jaw full of
ivory teeth and glowing eyes, crimson gill frills, then a long chain of nine shrinking body segments with a crimson
dorsal crest, ending in a fan-shaped tail fin. Teal scales in arcs, cream belly plates.

Every segment is a child of the one before it, so a small rotation per segment, phase-shifted down the chain, makes
the whole body undulate (idle: lazy S-curve, walk: swimming, faster and wider).
Actions: bite, roar (rears up, jaw wide: the whirlpool), lunge (body straight, head low: the charge).
"""
import math

from ..models import Model
from ..texgen import mix, mul

SCALE = (26, 92, 102)
SCALE_L = (60, 160, 160)
SCALE_D = (14, 52, 64)
BELLY = (214, 200, 146)
BELLY_D = (168, 150, 100)
FIN = (186, 40, 52)
FIN_D = (110, 20, 34)
FIN_L = (236, 110, 96)
IVORY = (240, 232, 206)
EYE = (190, 255, 110)
EYE_L = (250, 255, 210)
MOUTH = (70, 16, 26)
HORN = (200, 190, 160)
HORN_D = (120, 106, 84)

SEGMENTS = 9


def _n(x, y, seed):
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


def scales(seed, belly=True):
    """Arcs of teal scales (offset every other row), cream belly plates underneath."""
    def f(face, x, y, w, h):
        if face == "bottom" and belly:
            return BELLY_D if y % 3 == 0 else mix(BELLY, BELLY_D, 0.25 * _n(x, y, seed))
        if face in ("left", "right") and belly and y >= h - 2:
            return mix(BELLY, SCALE, 0.3 if y == h - 2 else 0.0)
        xx = x + (y // 2 % 2) * 2
        c = SCALE
        if y % 2 == 0 and xx % 4 in (1, 2):
            c = mix(SCALE, SCALE_L, 0.55)     # the lit rim of each scale
        elif y % 2 == 1 and xx % 4 == 0:
            c = mix(SCALE, SCALE_D, 0.7)
        if face == "top":
            c = mix(c, SCALE_D, 0.25)
        return mix(c, SCALE_L, 0.12 * _n(x, y, seed))
    return f


def fin(seed, rib=3):
    """Crimson membrane with dark ribs and a light rim (flat fins: only the two broad faces show)."""
    def f(face, x, y, w, h):
        if x % rib == 0:
            c = FIN_D
        else:
            c = mix(FIN, FIN_L, 0.25 * (1 - y / max(1, h - 1)))
        if y == 0:
            c = FIN_L
        return c
    return f


def fan(seed):
    """A gill frill: a fan widening toward the back, ribbed, with a light rim (the plane's x runs along z)."""
    rib = fin(seed, rib=2)

    def f(face, x, y, w, h):
        back = w - 1 - x if face == "right" else x
        d = abs(y - (h - 1) / 2)
        if d > 1.0 + back * 0.65:
            return None
        if d > back * 0.65 - 0.2:
            return FIN_L
        return rib(face, back, y, w, h)
    return f


def build():
    m = Model("sea_serpent", seed=171, shadow=1.0, head="head", walk_speed=1.0, walk_scale=1.0)
    m.preview_idle = True

    m.part("bone", pivot=(0, 24, 0), scale=(1.4, 1.4, 1.4))
    m.part("seg0", "bone", pivot=(0, -12, 0))
    m.part("head", "seg0", pivot=(0, -1, -5))
    m.part("jaw", "head", pivot=(0, 2, -3))

    # ---- head: skull, long snout, brow ridges, glowing eyes, ivory teeth, two swept-back horns, crest
    palate = lambda f, x, y, w, h: BELLY if x in (0, w - 1) else MOUTH       # the roof of the mouth
    m.box("head", -5, -5, -10, 10, 7, 10, {"bottom": palate, "*": scales(1)})
    m.box("head", -4, -4, -17, 8, 5, 7, {"bottom": palate, "*": scales(2)})
    m.box("head", -3, -4.5, -19, 6, 4, 2, {"front": lambda f, x, y, w, h: SCALE_D if (x in (1, w - 2) and y == 1)
                                           else SCALE, "*": scales(3)})                 # nostrils
    for sx in (-1, 1):
        m.box("head", (3.5 if sx > 0 else -5.5), -6, -9, 2, 2, 6, scales(4 + sx, belly=False))   # brow ridge
        m.box("head", (4.6 if sx > 0 else -5.6), -4, -8, 1, 2, 2, EYE, glow={"*": EYE_L, "left": EYE, "right": EYE})
        # upper teeth along the snout
        m.box("head", (3 if sx > 0 else -4), 1, -17, 1, 1, 12,
              lambda f, x, y, w, h: IVORY if (x + y) % 2 == 0 else None)
    m.box("head", -3, 1, -18, 6, 1, 1, lambda f, x, y, w, h: IVORY if x % 2 == 0 else None)
    for sx in (-1, 1):
        hp = f"horn_{'l' if sx > 0 else 'r'}"
        m.part(hp, "head", pivot=(3 * sx, -5, -2), rot=(30, 25 * sx, 0))
        m.box(hp, -1, -1, 0, 2, 2, 7, {"*": HORN, "top": mix(HORN, IVORY, 0.4), "back": HORN_D})
        m.part(hp + "_tip", hp, pivot=(0, 0, 7), rot=(25, 0, 0))
        m.box(hp + "_tip", -0.5, -0.5, 0, 1, 1, 5, {"*": HORN_D, "top": HORN})
        # crimson gill frill fanning out behind the jaw
        gp = f"gill_{'l' if sx > 0 else 'r'}"
        m.part(gp, "head", pivot=(5 * sx, -1, -1), rot=(0, 30 * sx, 0))
        m.box(gp, 0, -4, 0, 0, 8, 6, fan(10 + sx))
    m.box("head", 0, -9, -9, 0, 4, 10, fin(12))                                                       # head crest
    # ---- lower jaw
    m.box("jaw", -3.5, 0, -13, 7, 3, 13, {"top": MOUTH, "*": scales(13), "bottom": BELLY})
    for sx in (-1, 1):
        m.box("jaw", (2.5 if sx > 0 else -3.5), -1, -12, 1, 1, 11,
              lambda f, x, y, w, h: IVORY if (x + y) % 2 == 1 else None)

    # ---- the body: nine segments, each a little thinner, each with a crest and belly plates
    prev = "seg0"
    for i in range(SEGMENTS):
        part = f"seg{i}"
        if i > 0:
            m.part(part, prev, pivot=(0, 0, 10))
        size = max(4, 10 - (i * 6) // (SEGMENTS - 1))
        half = size / 2
        m.box(part, -half, -half, 0 if i else -5, size, size, 10 if i else 15, scales(20 + i))
        crest = max(2, 5 - i // 2)
        m.box(part, 0, -half - crest, 1, 0, crest, 8, fin(30 + i))
        if i in (1, 2):   # a pair of small crimson fore-fins
            for sx in (-1, 1):
                m.box(part, (half if sx > 0 else -half), half - 2, 2, 0, 4, 6, fin(40 + i * 2 + sx))
        prev = part
    m.part("tail", prev, pivot=(0, 0, 10))
    m.box("tail", 0, -7, 0, 0, 14, 9, lambda f, x, y, w, h: None if abs(y - (h - 1) / 2) > 1 + x * 0.8
          else (FIN_L if abs(y - (h - 1) / 2) > x * 0.8 - 0.5 else fin(50)(f, x, y, w, h)))
    m.box("tail", -1.5, -1.5, 0, 3, 3, 3, scales(51))

    # ------------------------------------------------------------------ animations
    def wave(anim, length, amp_yaw, amp_pitch, phase, extra=None):
        steps = 8
        for i in range(SEGMENTS + 1):
            part = f"seg{i}" if i < SEGMENTS else "tail"
            keys = []
            for k in range(steps + 1):
                t = length * k / steps
                a = math.tau * k / steps - i * phase
                yaw = amp_yaw * (0.4 + 0.6 * i / SEGMENTS) * math.sin(a)
                pitch = amp_pitch * math.sin(a + 1.3)
                keys.append((round(t, 3), (round(pitch, 2), round(yaw, 2), 0)))
            anim.rot(part, *keys)

    idle = m.anim("idle", 2.4)
    wave(idle, 2.4, 9, 2.5, 0.65)
    idle.rot("jaw", (0, (4, 0, 0)), (1.2, (10, 0, 0)), (2.4, (4, 0, 0)))
    idle.rot("gill_l", (0, (0, 0, 0)), (1.2, (0, 14, 0)), (2.4, (0, 0, 0)))
    idle.rot("gill_r", (0, (0, 0, 0)), (1.2, (0, -14, 0)), (2.4, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    wave(walk, 1.2, 7, 2, 0.75)

    # bite: rear back (0.3 s), lunge and snap shut at 0.4 s (damage tick 8), recover
    a = m.anim("bite", 0.9)
    a.rot("jaw", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (0.4, (0, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-25, 0, 0)), (0.4, (12, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.pos("seg0", (0, (0, 0, 0)), (0.3, (0, 1, 3)), (0.4, (0, -1, -6), "linear"), (0.9, (0, 0, 0)))
    # roar: rears up out of the swell, jaw wide, frills flared (1.6 s; the whirlpool starts at 0.6 s)
    a = m.anim("roar", 1.6)
    a.rot("seg0", (0, (0, 0, 0)), (0.5, (-45, 0, 0)), (1.3, (-40, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("seg1", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (1.3, (28, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-15, 0, 0)), (0.7, (-20, 8, 0)), (1.0, (-20, -8, 0)), (1.3, (-15, 0, 0)),
          (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (55, 0, 0)), (1.3, (55, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("gill_l", (0, (0, 0, 0)), (0.5, (0, 50, 0)), (1.3, (0, 50, 0)), (1.6, (0, 0, 0)))
    a.rot("gill_r", (0, (0, 0, 0)), (0.5, (0, -50, 0)), (1.3, (0, -50, 0)), (1.6, (0, 0, 0)))
    # lunge: coils back (0.4 s), then shoots forward straight with the jaw open (charge), snaps at the end
    a = m.anim("lunge", 1.4)
    for i in range(1, SEGMENTS):
        s = 1 if i % 2 else -1
        a.rot(f"seg{i}", (0, (0, 0, 0)), (0.4, (0, 22 * s, 0)), (0.55, (0, -4 * s, 0), "linear"), (1.2, (0, 0, 0)),
              (1.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (0.6, (45, 0, 0)), (1.1, (45, 0, 0)), (1.2, (0, 0, 0), "linear"),
          (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-10, 0, 0)), (0.6, (8, 0, 0)), (1.4, (0, 0, 0)))
    return m
