"""Void Larva (Larve du vide): a fat segmented End grub (about 1.2 blocks long). Black-violet chitin plates on
its back, a pale ribbed belly, rows of violet bioluminescent spots that pulse, six stubby legs, and a round
lamprey maw ringed with teeth and four hooked mandibles, its throat glowing.

Animations: idle (segments pulse one after another), walk (the crawl: a sideways segment wave), bite (rear,
lunge, mandibles snap at 0.5 s = 10 ticks), burrow (dives into the ground, hidden from 0.6 to 1.0 s, bursts
out again).
"""
import math

from ..models import Model
from ..texgen import mix, mul

CHITIN = (46, 30, 72)
CHITIN_D = (24, 14, 40)
CHITIN_L = (92, 64, 140)
BELLY = (128, 106, 154)
BELLY_D = (88, 70, 114)
LIP = (128, 70, 146)
TOOTH = (232, 222, 240)
THROAT = (22, 4, 30)
GLOW = (214, 128, 255)
GLOW_HOT = (246, 210, 255)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def segment(seed=0, spots=True):
    """A body ring: glossy chitin plate on the top with a bright rim, pale ribbed belly underneath,
    sides darkening downward with a row of glow spots."""
    def f(face, x, y, w, h):
        r = _h(x, y, seed, FACE_N[face])
        if face == "top":
            c = CHITIN_L if (x == 0 or x == w - 1 or y == 0) else mix(CHITIN, CHITIN_L, 0.25)
            if y == h // 2 and 1 < x < w - 2:
                c = mix(c, CHITIN_D, 0.5)                        # dorsal seam
            if r % 17 == 0:
                c = mix(c, (170, 140, 220), 0.4)                 # gloss
            return c
        if face == "bottom":
            return BELLY_D if y % 2 else BELLY
        if face in ("front", "back"):
            t = y / max(1, h - 1)
            return mix(CHITIN_D, BELLY_D, max(0.0, t - 0.6) * 2.0)
        # sides: plate edge on top, chitin, then the belly below
        t = y / max(1, h - 1)
        if y == 0:
            return CHITIN_L
        if t > 0.72:
            return BELLY if (x % 2 == 0) else BELLY_D
        c = mix(CHITIN, CHITIN_D, t * 0.6)
        if x == 0 or x == w - 1:
            c = mix(c, CHITIN_D, 0.6)                            # groove between segments
        if spots and _spot(face, x, y, w, h, seed):
            return (90, 40, 130)
        return c
    return f


def _spot(face, x, y, w, h, seed):
    if face not in ("left", "right") or w < 3:
        return False
    cy = int(h * 0.42)
    k = 1 + _h(seed, FACE_N[face]) % max(1, w - 2)
    return (y == cy and x == k) or (y == cy + 1 and x == max(1, w - 1 - k) and w > 3)


def spot_glow(seed=0):
    def f(face, x, y, w, h):
        if _spot(face, x, y, w, h, seed):
            return GLOW_HOT if (x + y) % 2 else GLOW
        if face == "top" and y == h // 2 and x == w // 2:
            return (*GLOW, 200)                                   # a dorsal light on every plate
        return None
    return f


def maw(face, x, y, w, h):
    """Round lamprey mouth on the front of the head (w=h=8)."""
    if face != "front":
        return segment(70, spots=False)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r > 3.6:
        return CHITIN_D
    if r > 2.9:
        return LIP
    if r > 2.0:
        ang = math.atan2(y - cy, x - cx)
        return TOOTH if int((ang + math.pi) / (2 * math.pi) * 10) % 2 == 0 else (60, 20, 70)
    if r > 1.0:
        return THROAT
    return (120, 40, 160)


def maw_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r <= 1.0:
        return GLOW_HOT
    if r <= 2.0:
        return (*GLOW, 110)
    return None


def build():
    m = Model("void_larva", seed=71, shadow=0.5, walk_speed=1.0, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -4.5, 1))
    m.part("seg1", "body", pivot=(0, 0, -3))
    m.part("head", "seg1", pivot=(0, 0, -4))
    m.part("mand_t", "head", pivot=(0, -3, -3), rot=(-20, 0, 0))
    m.part("mand_b", "head", pivot=(0, 3, -3), rot=(20, 0, 0))
    m.part("mand_r", "head", pivot=(-3, 0, -3), rot=(0, 20, 0))
    m.part("mand_l", "head", pivot=(3, 0, -3), rot=(0, -20, 0))
    m.part("seg3", "body", pivot=(0, 0.5, 3))
    m.part("seg4", "seg3", pivot=(0, 0.5, 4))
    m.part("tail", "seg4", pivot=(0, 0.5, 3))
    legs = []
    for i, (parent, z) in enumerate((("seg1", -2), ("body", 0), ("seg3", 2))):
        for side, sx in (("r", -1), ("l", 1)):
            name = f"leg{i}_{side}"
            x = sx * (4.5 if parent == "seg1" else 4 if parent == "body" else 3.5)
            m.part(name, parent, pivot=(x, 2.5, z), rot=(0, 0, -35 * sx))
            legs.append((name, sx, i))

    m.box("body", -4, -4, -3, 8, 8, 6, segment(1), glow=spot_glow(1))
    m.box("body", -3, -5, -2.5, 6, 1, 5, segment(11, spots=False), glow=spot_glow(11))   # rounded back plate
    m.box("seg1", -4.5, -4.5, -4, 9, 9, 4, segment(2), glow=spot_glow(2))
    m.box("seg1", -3.5, -5.5, -3.5, 7, 1, 3, segment(12, spots=False), glow=spot_glow(12))
    m.box("head", -4, -4, -3, 8, 8, 3, maw, glow=maw_glow)
    m.box("head", -3, -5, -2, 6, 1, 2, CHITIN_L)                                  # brow plate
    mand_paint = (lambda f_, xx, yy, ww, hh: TOOTH if f_ == "front" else
                  mix(CHITIN_L, TOOTH, 0.4) if f_ == "top" else (88, 60, 110))
    for p, (x, y, z, w, h, d), hook in (
            ("mand_t", (-1, -1, -3, 2, 1, 3), (-0.5, 0, -4, 1, 1, 1)),
            ("mand_b", (-1, 0, -3, 2, 1, 3), (-0.5, -1, -4, 1, 1, 1)),
            ("mand_r", (-1, -1, -3, 1, 2, 3), (0, -0.5, -4, 1, 1, 1)),
            ("mand_l", (0, -1, -3, 1, 2, 3), (-1, -0.5, -4, 1, 1, 1))):
        m.box(p, x, y, z, w, h, d, mand_paint)
        m.box(p, *hook, TOOTH)                                                     # hooked tip, bent inward
    m.box("seg3", -3.5, -3.5, 0, 7, 7, 4, segment(3), glow=spot_glow(3))
    m.box("seg3", -2.5, -4.5, 0.5, 5, 1, 3, segment(13, spots=False), glow=spot_glow(13))
    m.box("seg4", -3, -3, 0, 6, 6, 3, segment(4), glow=spot_glow(4))
    spine = (lambda f_, xx, yy, ww, hh: (200, 170, 240) if yy == 0 else CHITIN_L)
    for part, x, y, z in (("body", -2.5, -6, -1), ("body", 1.5, -6, -1), ("seg3", -2, -5.5, 1.5), ("seg3", 1, -5.5, 1.5),
                          ("seg4", -0.5, -4, 1), ("seg1", -0.5, -7, -2.5)):
        m.box(part, x, y, z, 1, 2 if part != "seg1" else 2, 1, spine)
    m.box("tail", -2, -2, 0, 4, 4, 3, segment(5, spots=False), glow=spot_glow(5))
    m.box("tail", -1, -1, 3, 2, 2, 2, {"back": GLOW, "*": CHITIN_L}, glow={"back": GLOW_HOT})
    for name, sx, i in legs:
        m.box(name, -0.5, 0, -0.5, 1, 3, 1, lambda f_, xx, yy, ww, hh: CHITIN_D if yy == hh - 1 else CHITIN)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.0)
    for k, part in enumerate(("seg1", "body", "seg3", "seg4", "tail")):
        t0 = k * 0.25
        idle.scale(part, (0, (1, 1, 1)), (t0 + 0.01, (1, 1, 1)), (t0 + 0.4, (1.07, 1.08, 1.0)), (t0 + 0.8, (1, 1, 1)),
                   (2.0, (1, 1, 1)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (-4, 6, 0)), (2.0, (0, 0, 0)))
    for p, axis in (("mand_t", 0), ("mand_b", 0), ("mand_r", 1), ("mand_l", 1)):
        s = -1 if p in ("mand_t", "mand_l") else 1
        v = [0, 0, 0]
        v[axis] = 10 * s * (1 if axis == 0 else -1)
        idle.rot(p, (0, (0, 0, 0)), (0.3, tuple(v)), (0.6, (0, 0, 0)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    for k, (part, amp) in enumerate((("seg1", 10), ("body", 7), ("seg3", 12), ("seg4", 14), ("tail", 16))):
        ph = k * 0.2
        keys = []
        for i in range(5):
            t = i * 0.25
            a = amp * math.sin(2 * math.pi * (t / 1.0 + ph))
            hump = 4 * math.sin(2 * math.pi * (t / 1.0 + ph + 0.25))
            keys.append((t, (round(hump, 2), round(a, 2), 0)))
        walk.rot(part, *keys)
    for name, sx, i in legs:
        ph = 0.5 * (i % 2) + (0.25 if sx > 0 else 0)
        keys = [(t, (round(35 * math.sin(2 * math.pi * (t + ph)), 2), 0, 0)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        walk.rot(name, *keys)

    # bite: rear up with the maw gaping (telegraph), lunge and snap at 0.5 s (10 ticks)
    a = m.anim("bite", 1.0)
    a.rot("seg1", (0, (0, 0, 0)), (0.42, (-28, 0, 0)), (0.5, (14, 0, 0), "linear"), (0.7, (10, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.42, (-12, 0, 0)), (0.5, (10, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.42, (-8, 0, 0)), (0.5, (4, 0, 0)), (1.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.42, (0, 0, 2)), (0.5, (0, 0, -4), "linear"), (0.7, (0, 0, -4)), (1.0, (0, 0, 0)))
    a.rot("mand_t", (0, (0, 0, 0)), (0.42, (-45, 0, 0)), (0.5, (25, 0, 0), "linear"), (0.7, (20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_b", (0, (0, 0, 0)), (0.42, (45, 0, 0)), (0.5, (-25, 0, 0), "linear"), (0.7, (-20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.42, (0, 45, 0)), (0.5, (0, -25, 0), "linear"), (0.7, (0, -20, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.42, (0, -45, 0)), (0.5, (0, 25, 0), "linear"), (0.7, (0, 20, 0)), (1.0, (0, 0, 0)))
    a.scale("seg1", (0, (1, 1, 1)), (0.42, (1.1, 1.1, 1.0)), (0.5, (0.95, 0.95, 1.1)), (1.0, (1, 1, 1)))

    # burrow: nose-dive into the ground, hidden from 0.6 s to 1.0 s, burst out with a rear
    a = m.anim("burrow", 1.6)
    a.rot("seg1", (0, (0, 0, 0)), (0.3, (35, 0, 0)), (0.6, (45, 0, 0)), (1.0, (-40, 0, 0)), (1.25, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (0.6, (35, 0, 0)), (1.0, (-25, 0, 0)), (1.25, (-15, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("seg3", (0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.6, (-20, 0, 0)), (1.0, (10, 0, 0)), (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -4, -2)), (0.6, (0, -16, -3)), (1.0, (0, -16, 0)), (1.15, (0, 3, 0)),
          (1.3, (0, 1, 0)), (1.6, (0, 0, 0)))
    for p, v in (("mand_t", (-40, 0, 0)), ("mand_b", (40, 0, 0)), ("mand_r", (0, 40, 0)), ("mand_l", (0, -40, 0))):
        a.rot(p, (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.15, v), (1.6, (0, 0, 0)))
    return m
