"""Void Larva (Larve du vide): a fat segmented End grub (about 1.2 blocks long).

Silhouette idea: a glossy black-violet maggot that swells in the middle and tapers to a glowing tail lure. Each
ring is an armoured plate that overhangs the next like shingles, joined by pale, soft membrane folds; the back
arches up to the fattest ring, which carries two violet crystal growths. In front, a blind hooded head with three
pairs of tiny glowing ocelli and a round lamprey maw ringed with teeth, guarded by four big hooked mandibles that
spread wide before it strikes. Six stubby hooked legs under the front rings. Rows of bioluminescent spots (one per
ring and side) run down the flanks.

Animations: idle (a peristaltic swell running down the rings, the tail lure curling), walk (a vertical crawling
wave), bite (rears and coils with the mandibles spread, lunges and snaps at 0.5 s = 10 ticks), burrow (dives into
the ground, hidden from 0.6 to 1.0 s, bursts out again).
"""
import math

from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

# shared with larva_mother.py (keep these names and values: the brood mother is painted with them)
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

# the larva's own palette
SHELL = (44, 28, 70)
SHELL_D = (22, 12, 38)
SHELL_L = (104, 74, 156)
SHEEN = (176, 150, 226)
SOFT = (150, 124, 168)
SOFT_D = (106, 84, 126)
MEMBRANE = (186, 154, 196)
MEMBRANE_D = (136, 106, 152)
MOUTH_LIP = (140, 70, 150)
TOOTH_D = (170, 150, 186)
SPOT = (250, 216, 255)
CRYSTAL = (196, 140, 255)
CRYSTAL_L = (240, 214, 255)
CRYSTAL_D = (110, 60, 170)


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ legacy ring paint (used by larva_mother.py)
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
        t = y / max(1, h - 1)
        if y == 0:
            return CHITIN_L
        if t > 0.72:
            return BELLY if (x % 2 == 0) else BELLY_D
        c = mix(CHITIN, CHITIN_D, t * 0.6)
        if x == 0 or x == w - 1:
            c = mix(c, CHITIN_D, 0.6)                            # groove between segments
        if spots and _legacy_spot(face, x, y, w, h, seed):
            return (90, 40, 130)
        return c
    return f


def _legacy_spot(face, x, y, w, h, seed):
    if face not in ("left", "right") or w < 3:
        return False
    cy = int(h * 0.42)
    k = 1 + _h(seed, FACE_N[face]) % max(1, w - 2)
    return (y == cy and x == k) or (y == cy + 1 and x == max(1, w - 1 - k) and w > 3)


def spot_glow(seed=0):
    def f(face, x, y, w, h):
        if _legacy_spot(face, x, y, w, h, seed):
            return GLOW_HOT if (x + y) % 2 else GLOW
        if face == "top" and y == h // 2 and x == w // 2:
            return (*GLOW, 200)                                   # a dorsal light on every plate
        return None
    return f


# ------------------------------------------------------------------ the larva's paints
def _u(face, x, w):
    """Distance from the front (-z) end along a side face."""
    return x if face == "left" else w - 1 - x


def plate(seed=0, spots=True, belly_from=0.62):
    """An armoured ring: on top a glossy plate (a curved sheen band behind the lit front lip, a dark overlap shadow
    along the back edge); on the sides chitin darkening downward into the pale ribbed belly, with one round
    bioluminescent spot per side."""
    def f(face, x, y, w, h):
        if face == "top":
            fr = (h - 1 - y) / max(1, h - 1)                           # 0 at the front lip, 1 at the back edge
            if fr < 0.01:
                return SHELL_L                                          # the lit front lip
            cx = abs(x - (w - 1) / 2) / max(1, w / 2)
            if fr > 0.8 + 0.15 * cx:
                return mix(SHELL, SHELL_D, 0.6)                         # shadow where it tucks under the next ring
            band = abs(fr - (0.25 + 0.35 * cx * cx)) < 0.16             # a curved highlight, like a lacquered shell
            if band:
                return mix(SHELL, SHEEN, 0.5 if cx < 0.6 else 0.3)
            return mix(SHELL, SHELL_L, 0.25 * (1 - fr) * (1 - cx))
        if face == "bottom":
            return SOFT_D if y % 2 else SOFT
        v = y / max(1, h - 1)
        if face in ("front", "back"):
            return mix(SHELL_D, SOFT_D, max(0.0, v - belly_from) * 2.4)
        if spots and _spot(face, x, y, w, h):
            return (100, 46, 140)
        if y == 0:
            return SHELL_L
        if v > belly_from:
            return SOFT if y % 2 == 0 else SOFT_D                    # soft ribs of the belly
        u = _u(face, x, w)
        c = mix(SHELL, SHELL_D, v / belly_from * 0.7)
        if u == 0:
            c = mix(c, SHELL_L, 0.35)                                  # the lit front rim of the ring
        elif u == w - 1:
            c = mix(c, SHELL_D, 0.6)
        if y == 1 and 0 < u < w - 1:
            c = mix(c, SHEEN, 0.25)
        return c
    return f


def _spot(face, x, y, w, h):
    """One round spot per side face (2 x 2 with soft corners on big rings)."""
    if face not in ("left", "right") or w < 3 or h < 4:
        return False
    cy = int(h * 0.38)
    cx = (w - 1) // 2
    if w >= 4 and h >= 7:
        return x in (cx, cx + 1) and y in (cy, cy + 1)
    return x == cx and y == cy


def plate_glow(seed=0):
    def f(face, x, y, w, h):
        if _spot(face, x, y, w, h):
            cy = int(h * 0.38)
            return SPOT if y == cy else GLOW
        return None
    return f


def membrane(face, x, y, w, h):
    """The soft fold between two rings: pale lavender with wrinkles."""
    if face == "bottom":
        return MEMBRANE_D
    return MEMBRANE if (y + x // 3) % 3 else MEMBRANE_D


def maw(face, x, y, w, h):
    """Round lamprey mouth on the front of the head (w = h = 8)."""
    if face != "front":
        return plate(70, spots=False)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r > 3.6:
        return SHELL_D
    if r > 2.9:
        return MOUTH_LIP if y > cy else mix(MOUTH_LIP, (200, 120, 200), 0.3)
    if r > 2.0:
        ang = math.atan2(y - cy, x - cx)
        return TOOTH if int((ang + math.pi) / (2 * math.pi) * 10) % 2 == 0 else (60, 20, 70)
    if r > 1.0:
        return THROAT
    return (140, 50, 180)


def maw_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r <= 1.0:
        return SPOT
    if r <= 2.0:
        return (*GLOW, 120)
    return None


OCELLI = {(1, 1), (3, 1), (2, 2)}


def hood(face, x, y, w, h):
    """The head shield: a plate with three tiny glowing ocelli on each side."""
    if face in ("left", "right") and (_u(face, x, w), y) in OCELLI:
        return SPOT
    return plate(71, spots=False, belly_from=0.99)(face, x, y, w, h)


def hood_glow(face, x, y, w, h):
    if face in ("left", "right") and (_u(face, x, w), y) in OCELLI:
        return SPOT
    return None


def crystal(face, x, y, w, h):
    if face == "top":
        return CRYSTAL_L
    if face == "bottom":
        return CRYSTAL_D
    if x == 0 or face == "front":
        return mix(CRYSTAL, CRYSTAL_L, 0.5)
    return CRYSTAL if y < h - 1 else CRYSTAL_D


def crystal_glow(face, x, y, w, h):
    if face == "bottom":
        return None
    return CRYSTAL_L if y == 0 else (*CRYSTAL, 170)


def mandible(face, x, y, w, h):
    if face == "front":
        return TOOTH
    if face == "top":
        return mix(SHELL_L, TOOTH, 0.5)
    return SHELL_L if y == 0 else (88, 60, 110)


def wave(anim, part, length, amp, phase=0.0, base=(0, 0, 0), kind="rot", n=8):
    """A seamless sine loop: base + amp * sin(2 pi (t / length + phase))."""
    keys = []
    for i in range(n + 1):
        s = math.sin(2 * math.pi * (i / n + phase))
        keys.append((round(length * i / n, 4), tuple(round(base[k] + amp[k] * s, 3) for k in range(3))))
    getattr(anim, kind)(part, *keys)


RINGS = ("seg1", "body", "seg3", "seg4", "seg5", "tail")


def build():
    m = Model("void_larva", seed=71, shadow=0.5, walk_speed=1.0, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -6, 1))
    m.part("seg1", "body", pivot=(0, 0.5, -3), rot=(3, 0, 0))
    m.part("head", "seg1", pivot=(0, 0.5, -4))
    m.part("mand_t", "head", pivot=(0, -3, -4), rot=(-20, 0, 0))
    m.part("mand_b", "head", pivot=(0, 3, -4), rot=(20, 0, 0))
    m.part("mand_r", "head", pivot=(-3, 0, -4), rot=(0, 20, 0))
    m.part("mand_l", "head", pivot=(3, 0, -4), rot=(0, -20, 0))
    m.part("seg3", "body", pivot=(0, 0.5, 3))
    m.part("seg4", "seg3", pivot=(0, 0.8, 4), rot=(-5, 0, 0))
    m.part("seg5", "seg4", pivot=(0, 0.8, 4))
    m.part("tail", "seg5", pivot=(0, 0.6, 3), rot=(-10, 0, 0))
    legs = []
    for i, (parent, z, x) in enumerate((("seg1", -2, 4.0), ("body", -0.5, 4.5), ("seg3", 1.5, 4.0))):
        for side, sx in (("r", -1), ("l", 1)):
            name = f"leg{i}_{side}"
            m.part(name, parent, pivot=(x * sx, 3, z), rot=(-15, 0, -40 * sx))
            legs.append((name, sx, i))

    # ---- the rings: a core, a shingled plate on top that overhangs the ring behind, a soft membrane fold in front
    m.box("body", -5, -5, -2, 10, 10, 5, plate(1), glow=plate_glow(1))
    m.box("body", -5.5, -6, -2.5, 11, 4, 6, plate(11, spots=False, belly_from=0.99))
    m.box("body", -4, -4, -3, 8, 8, 1, membrane)
    m.box("seg1", -4.5, -4.5, -3, 9, 9, 3, plate(2), glow=plate_glow(2))
    m.box("seg1", -5, -5.5, -3.5, 10, 3, 4, plate(12, spots=False, belly_from=0.99))
    m.box("seg1", -3.5, -3.5, -4, 7, 7, 1, membrane)
    m.box("seg3", -4.5, -4.5, 1, 9, 9, 3, plate(3), glow=plate_glow(3))
    m.box("seg3", -5, -5.5, 0.5, 10, 3, 4, plate(13, spots=False, belly_from=0.99))
    m.box("seg3", -3.5, -3.5, 0, 7, 7, 1, membrane)
    m.box("seg4", -3.5, -3.5, 1, 7, 7, 3, plate(4), glow=plate_glow(4))
    m.box("seg4", -4, -4.3, 0.5, 8, 3, 4, plate(14, spots=False, belly_from=0.99))
    m.box("seg4", -2.5, -2.5, 0, 5, 5, 1, membrane)
    m.box("seg5", -2.5, -2.5, 1, 5, 5, 2, plate(5), glow=plate_glow(5))
    m.box("seg5", -3, -3.2, 0.5, 6, 2, 3, plate(15, spots=False, belly_from=0.99))
    m.box("seg5", -1.5, -1.5, 0, 3, 3, 1, membrane)
    # the tail: a tapering spike with a glowing lure bulb
    m.box("tail", -1.5, -1.5, 0, 3, 3, 3, plate(6, spots=False))
    m.box("tail", -1, -1, 3, 2, 2, 2, plate(7, spots=False))
    m.box("tail", -1, -2, 4.5, 2, 2, 2, {"*": GLOW, "top": SPOT}, glow={"*": GLOW, "top": SPOT})

    # crystal growths on the fattest ring, swept back
    for i, (x, hgt, tilt) in enumerate(((-2.5, 3, -20), (2, 3, 18), (0, 2, 0))):
        p = m.part(f"crystal{i}", "body" if i < 2 else "seg3", pivot=(x, -5.5, 0.5 if i < 2 else 2), rot=(-58, 0, tilt))
        m.box(p, -1, -hgt, -1, 2, hgt, 2, crystal, glow=crystal_glow)
        m.box(p, -0.5, -hgt - 1, -0.5, 1, 1, 1, CRYSTAL_L, glow=CRYSTAL_L)

    # ---- head: round maw, a hood with ocelli, four hooked mandibles
    m.box("head", -4, -4, -3, 8, 8, 3, maw, glow=maw_glow)
    m.box("head", -4.5, -5, -3.5, 9, 3, 4, hood, glow=hood_glow)
    m.box("head", -1, -5.5, -3.8, 2, 1, 2, SHELL_L)                           # the brow keel
    for p, (x, y, z, w, h, d), hook in (
            ("mand_t", (-1, -1, -3, 2, 1, 3), (-0.5, -0.5, -4, 1, 2, 1)),
            ("mand_b", (-1, 0, -3, 2, 1, 3), (-0.5, -0.5, -4, 1, 2, 1)),
            ("mand_r", (-1, -1, -3, 1, 2, 3), (-0.5, -0.5, -4, 2, 1, 1)),
            ("mand_l", (0, -1, -3, 1, 2, 3), (-0.5, -0.5, -4, 2, 1, 1))):
        m.box(p, x, y, z, w, h, d, mandible)
        m.box(p, *hook, {"*": TOOTH, "bottom": TOOTH_D})                      # hooked tip, bent inward

    for name, sx, i in legs:
        m.box(name, -0.5, 0, -0.5, 1, 3, 1, lambda f_, xx, yy, ww, hh: SHELL_L if yy == 0 else SHELL)
        m.box(name, -0.5 if sx > 0 else -0.5, 2.5, -1.5, 1, 1, 2, {"*": SHELL_D, "front": TOOTH_D})  # the hook

    _anims(m, legs)
    return m


def _anims(m, legs):
    # idle: a swell runs down the rings (peristalsis), the head sways, mandibles twitch, the lure curls
    idle = m.anim("idle", 2.0)
    for k, part in enumerate(RINGS[:5]):
        t0 = k * 0.25
        idle.scale(part, (0, (1, 1, 1)), (t0 + 0.01, (1, 1, 1)), (t0 + 0.4, (1.07, 1.08, 1.0)), (t0 + 0.8, (1, 1, 1)),
                   (2.0, (1, 1, 1)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (-4, 8, 0)), (1.4, (2, -6, 0)), (2.0, (0, 0, 0)))
    wave(idle, "tail", 2.0, (12, 6, 0), 0.0)
    wave(idle, "seg5", 2.0, (5, 4, 0), 0.9)
    for p, axis in (("mand_t", 0), ("mand_b", 0), ("mand_r", 1), ("mand_l", 1)):
        s = -1 if p in ("mand_t", "mand_l") else 1
        v = [0, 0, 0]
        v[axis] = 12 * s * (1 if axis == 0 else -1)
        idle.rot(p, (0, (0, 0, 0)), (0.3, tuple(v)), (0.45, (0, 0, 0)), (0.6, tuple(v)), (0.8, (0, 0, 0)), (2.0, (0, 0, 0)))
    for name, sx, i in legs:
        wave(idle, name, 2.0, (6, 0, 0), i * 0.2 + (0.5 if sx > 0 else 0))

    # crawl: a hump travels from the head to the tail (each ring lifts and pitches in turn), a little side sway
    walk = m.anim("walk", 1.0)
    for k, (part, amp) in enumerate((("seg1", 7), ("body", 5), ("seg3", 8), ("seg4", 9), ("seg5", 10), ("tail", 12))):
        ph = -k * 0.16
        wave(walk, part, 1.0, (amp, 3 + k, 0), ph, n=8)
    wave(walk, "body", 1.0, (0, 0.8, 0), 0.25, kind="pos")
    wave(walk, "head", 1.0, (-5, 4, 0), 0.1)
    for name, sx, i in legs:
        ph = 0.5 * (i % 2) + (0.25 if sx > 0 else 0)
        wave(walk, name, 1.0, (35, 0, 0), ph)

    # bite: rears up and coils back with the mandibles spread wide and the maw flared (telegraph, 0 - 0.42 s),
    # lunges and snaps shut at 0.5 s (10 ticks), shakes its prey, recovers
    a = m.anim("bite", 1.0)
    a.rot("seg1", (0, (0, 0, 0)), (0.3, (-26, 0, 0)), (0.42, (-34, 0, 0)), (0.5, (16, 0, 0), "linear"), (0.6, (12, 6, 0)),
          (0.7, (12, -6, 0)), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.42, (-16, 0, 0)), (0.5, (12, 0, 0), "linear"), (0.6, (10, 8, 0)), (0.7, (10, -8, 0)),
          (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.42, (-12, 0, 0)), (0.5, (6, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("seg3", (0, (0, 0, 0)), (0.42, (10, 0, 0)), (0.5, (-4, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("seg4", (0, (0, 0, 0)), (0.42, (10, 0, 0)), (0.55, (-6, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.42, (-25, 0, 0)), (0.6, (15, 0, 0)), (1.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.42, (0, 0, 2.5)), (0.5, (0, 0, -4), "linear"), (0.7, (0, 0, -4)), (1.0, (0, 0, 0)))
    a.scale("body", (0, (1, 1, 1)), (0.42, (1.08, 1.06, 0.88)), (0.5, (0.96, 0.96, 1.12), "linear"), (0.7, (1, 1, 1)),
            (1.0, (1, 1, 1)))
    a.scale("seg1", (0, (1, 1, 1)), (0.42, (1.12, 1.12, 0.9)), (0.5, (0.95, 0.95, 1.12), "linear"), (1.0, (1, 1, 1)))
    a.rot("mand_t", (0, (0, 0, 0)), (0.42, (-55, 0, 0)), (0.5, (25, 0, 0), "linear"), (0.7, (20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_b", (0, (0, 0, 0)), (0.42, (55, 0, 0)), (0.5, (-25, 0, 0), "linear"), (0.7, (-20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_r", (0, (0, 0, 0)), (0.42, (0, 55, 0)), (0.5, (0, -25, 0), "linear"), (0.7, (0, -20, 0)), (1.0, (0, 0, 0)))
    a.rot("mand_l", (0, (0, 0, 0)), (0.42, (0, -55, 0)), (0.5, (0, 25, 0), "linear"), (0.7, (0, 20, 0)), (1.0, (0, 0, 0)))

    # burrow: nose-dive into the ground, hidden from 0.6 s to 1.0 s, burst out with a rear and spread mandibles
    a = m.anim("burrow", 1.6)
    a.rot("seg1", (0, (0, 0, 0)), (0.3, (35, 0, 0)), (0.6, (45, 0, 0)), (1.0, (-40, 0, 0)), (1.25, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (0.6, (35, 0, 0)), (1.0, (-25, 0, 0)), (1.25, (-15, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("seg3", (0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.6, (-20, 0, 0)), (1.0, (10, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("seg4", (0, (0, 0, 0)), (0.3, (-12, 0, 0)), (0.6, (-25, 0, 0)), (1.0, (10, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.2, (-30, 0, 0)), (0.5, (-40, 0, 0)), (1.0, (10, 0, 0)), (1.3, (-20, 0, 0)),
          (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -4, -2)), (0.6, (0, -16, -3)), (1.0, (0, -16, 0)), (1.15, (0, 3, 0)),
          (1.3, (0, 1, 0)), (1.6, (0, 0, 0)))
    for p, v in (("mand_t", (-45, 0, 0)), ("mand_b", (45, 0, 0)), ("mand_r", (0, 45, 0)), ("mand_l", (0, -45, 0))):
        a.rot(p, (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.4, tuple(c * 0.3 for c in v)), (1.0, (0, 0, 0)), (1.15, v),
              (1.6, (0, 0, 0)))
