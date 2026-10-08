"""Abyss Crawler (Rampant de l'abîme): the pale climber of the Inverted Spire, about 1.3 blocks long and knee-high.

Silhouette idea: something that grew up in the dark under the spire and never needed eyes. A long, low body of chalk-
white chitin in three overlapping segments, bruise-violet underneath, a row of cold blue glow-pits along its spine. Six
spindly legs bent high above the back like a harvestman's, ending in black hooked tips that grip stone, walls and
ceilings. Its head is an eyeless bony wedge whose jaw splits four ways like a flower, each petal lined with needle
teeth, a faint light deep in the throat. It walks up walls, waits on ceilings and drops onto whatever passes beneath.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

CHALK = (214, 210, 200)
CHALK_L = (240, 238, 230)
CHALK_D = (150, 144, 136)
BRUISE = (110, 84, 122)
BRUISE_D = (66, 48, 80)
TIP = (28, 24, 32)
GLOW = (90, 170, 255)
GLOW_L = (200, 236, 255)
THROAT = (120, 40, 70)
TOOTH = (250, 246, 236)


def chitin(seed=0, under=True):
    """Pale chitin plates: a lit top, faint growth lines, violet creeping up from the underside, grime in the cracks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BRUISE if under else CHALK_D
        if face == "top":
            c = CHALK_L if (x + y) % 5 == 0 else CHALK
            return mul(c, 0.86) if K.h(x, y, seed) % 13 == 0 else c
        c = mul(CHALK, 1.05 - 0.25 * y / max(1, h))
        if under and y >= h - 1 and h > 1:
            c = mix(c, BRUISE, 0.6)
        if (x + seed) % 4 == 0 and y > 0:
            c = mul(c, 0.9)                                                               # growth lines
        if K.h(x, y, seed, 3) % 17 == 0:
            c = mix(c, (60, 56, 52), 0.5)
        return c
    return f


def leg(seed=0, tip=False):
    def f(face, x, y, w, h):
        if tip and y >= h - 2:
            return TIP if y == h - 1 or face != "top" else mul(TIP, 1.4)
        if face in ("top", "bottom"):
            return CHALK_D
        c = CHALK if (y + seed) % 3 else CHALK_D
        return mix(c, BRUISE, 0.25) if y == 0 else c
    return f


def spine_pits(seed=0):
    """Glow pits along the top of a segment (paint): dark rims round blue points."""
    def f(face, x, y, w, h):
        if face == "top" and x == w // 2 and y % 3 == 1:
            return GLOW
        if face == "top" and abs(x - w // 2) == 1 and y % 3 == 1:
            return BRUISE_D
        return chitin(seed)(face, x, y, w, h)
    return f


def pits_glow(face, x, y, w, h):
    return (GLOW_L if y % 6 == 1 else GLOW) if face == "top" and x == w // 2 and y % 3 == 1 else None


def petal(seed=0):
    """One jaw petal: chalk outside, a row of needle teeth along the inner edge, throat-red inside."""
    def f(face, x, y, w, h):
        if face == "back":
            return THROAT if (x + y) % 3 else mul(THROAT, 0.7)
        if face == "front":
            return chitin(seed, under=False)(face, x, y, w, h)
        return CHALK_D
    return f


def build():
    m = Model("abyss_crawler", seed=941, shadow=0.7, walk_speed=1.8, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton: three segments, six legs, a head
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -7, -2))
    m.part("seg2", "body", pivot=(0, 0, 4))
    m.part("seg3", "seg2", pivot=(0, 0.5, 7))
    m.part("head", "body", pivot=(0, -0.5, -5))
    m.part("jaw_t", "head", pivot=(0, -2, -6))
    m.part("jaw_b", "head", pivot=(0, 2, -6))
    m.part("jaw_r", "head", pivot=(-2.5, 0, -6))
    m.part("jaw_l", "head", pivot=(2.5, 0, -6))
    LEGS = [("f", "body", -2.5, -30), ("m", "seg2", 2.5, 0), ("b", "seg2", 6.5, 30)]
    for key, parent, z, yaw in LEGS:
        for side, sx in (("r", -1), ("l", 1)):
            up = f"leg_{key}{side}"
            m.part(up, parent, pivot=(3.5 * sx, -0.5, z), rot=(0, yaw * -sx, 120 * -sx))
            m.part(f"shin_{key}{side}", up, pivot=(0, 8, 0), rot=(0, 0, 103 * sx))

    # ------------------------------------------------------------------ segments
    m.box("body", -4, -2.5, -5, 8, 5, 9, spine_pits(1), glow={"top": pits_glow, "*": None})
    m.box("body", -4.5, -3, -4, 9, 1, 7, chitin(2), grow=0.0)                              # overlapping plate rim
    m.box("seg2", -4.5, -3, 0, 9, 5, 8, spine_pits(3), glow={"top": pits_glow, "*": None})
    m.box("seg2", -5, -3.5, 1, 10, 1, 6, chitin(4))
    m.box("seg3", -3.5, -2, 0, 7, 4, 7, spine_pits(5), glow={"top": pits_glow, "*": None})
    m.box("seg3", -2.5, -1.5, 7, 5, 3, 3, chitin(6))
    m.box("seg3", -1.5, -1, 10, 3, 2, 3, chitin(7))
    m.box("seg3", -0.5, -0.5, 13, 1, 1, 3, {"*": TIP, "top": CHALK_D})                      # the tail spike
    # dorsal spines between the segments
    for part, z in (("body", -3), ("body", 1), ("seg2", 3), ("seg2", 6), ("seg3", 2)):
        m.box(part, -0.5, -5 if part != "seg3" else -4, z, 1, 2, 1, {"*": CHALK_D, "top": TIP})

    # ------------------------------------------------------------------ head: eyeless wedge, four-way jaw
    m.box("head", -3, -3, -6, 6, 6, 6, chitin(10, under=True))
    m.box("head", -2.5, -3.5, -5, 5, 1, 5, chitin(11, under=False))                         # brow ridge
    m.box("head", -3.5, -1, -4, 1, 2, 3, {"*": CHALK_D, "left": TIP, "right": TIP})        # sensory pits instead of eyes
    m.box("head", 2.5, -1, -4, 1, 2, 3, {"*": CHALK_D, "left": TIP, "right": TIP})
    m.box("head", -1.5, -1.5, -6.2, 3, 3, 1, THROAT, glow={"front": lambda f_, x, y, w, h: GLOW if (x, y) == (1, 1) else
                                                         (40, 70, 120), "*": None})        # the throat light
    # each petal: a plate hinged at the head's front edge, teeth on its rim
    for part, (x, y, w, h) in (("jaw_t", (-2.5, -1, 5, 1)), ("jaw_b", (-2.5, 0, 5, 1)), ("jaw_r", (-1, -2.5, 1, 5)),
                               ("jaw_l", (0, -2.5, 1, 5))):
        m.box(part, x, y, -4, w, h, 4, petal(sum(map(ord, part)) % 7))
        if part in ("jaw_t", "jaw_b"):
            for tx in (-2, 0, 2):
                m.box(part, tx - 0.5, y + (1 if part == "jaw_t" else -1), -4, 1, 1, 1, TOOTH)
        else:
            for ty in (-2, 0, 2):
                m.box(part, x + (1 if part == "jaw_r" else -1), ty - 0.5, -4, 1, 1, 1, TOOTH)

    # ------------------------------------------------------------------ legs: high-kneed, black hooked tips
    for key, parent, z, yaw in LEGS:
        for side, sx in (("r", -1), ("l", 1)):
            up, sh = f"leg_{key}{side}", f"shin_{key}{side}"
            m.box(up, -1, 0, -1, 2, 8, 2, leg(sum(map(ord, up)) % 5))
            m.box(up, -1.5, 7, -1.5, 3, 2, 3, chitin(12, under=False))                       # the knee knob
            m.box(sh, -0.5, 0, -0.5, 1, 12, 1, leg(sum(map(ord, sh)) % 5, tip=True))
            m.box(sh, -0.5, 11, -1.5, 1, 1, 1, TIP)                                            # the hook

    _anims(m)
    return m


def _gait(a, length, swing, lift):
    """Alternating tripods: front-right, mid-left, back-right together, then the other three."""
    half = length / 2
    for key in ("f", "m", "b"):
        for side in ("r", "l"):
            phase = (key in ("f", "b")) == (side == "r")
            s = 1 if phase else -1
            a.rot(f"leg_{key}{side}", (0, (0, swing * s, 0)), (half / 2, (0, 0, lift * (1 if side == "r" else -1) * (s > 0))),
                  (half, (0, -swing * s, 0)), (half * 1.5, (0, 0, lift * (1 if side == "r" else -1) * (s < 0))),
                  (length, (0, swing * s, 0)))


def _anims(m):
    idle = m.anim("idle", 2.4)
    idle.rot("seg2", (0, (0, 0, 0)), (1.2, (0, 4, 0)), (2.4, (0, 0, 0)))
    idle.rot("seg3", (0, (0, 0, 0)), (1.2, (4, -8, 0)), (2.4, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.6, (0, 10, 0)), (1.2, (-6, -4, 0)), (1.8, (0, -12, 0)), (2.4, (0, 0, 0)))
    for part, ax in (("jaw_t", (-1, 0, 0)), ("jaw_b", (1, 0, 0)), ("jaw_r", (0, 1, 0)), ("jaw_l", (0, -1, 0))):
        k = tuple(v * 10 for v in ax)
        idle.rot(part, (0, (0, 0, 0)), (0.3, k), (0.5, (0, 0, 0)), (1.4, (0, 0, 0)), (1.6, k), (1.8, (0, 0, 0)), (2.4, (0, 0, 0)))
    idle.pos("body", (0, (0, 0, 0)), (1.2, (0, -0.3, 0)), (2.4, (0, 0, 0)))

    walk = m.anim("walk", 0.6)
    _gait(walk, 0.6, 22, 14)
    walk.rot("seg2", (0, (0, 5, 0)), (0.3, (0, -5, 0)), (0.6, (0, 5, 0)))
    walk.rot("seg3", (0, (0, -8, 0)), (0.3, (0, 8, 0)), (0.6, (0, -8, 0)))
    walk.rot("head", (0, (0, -4, 0)), (0.3, (0, 4, 0)), (0.6, (0, -4, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.15, (0, 0.4, 0)), (0.3, (0, 0, 0)), (0.45, (0, 0.4, 0)), (0.6, (0, 0, 0)))

    # rake: the front rears up and both forelegs lift high (0.35 s), then hook down onto the prey (lands at 0.35 s =
    # 7 ticks)
    a = m.anim("rake", 0.8)
    a.rot("body", (0, (0, 0, 0)), (0.3, (-26, 0, 0)), (0.35, (-28, 0, 0)), (0.45, (12, 0, 0), "linear"), (0.6, (10, 0, 0)),
          (0.8, (0, 0, 0)))
    a.rot("seg2", (0, (0, 0, 0)), (0.3, (18, 0, 0)), (0.45, (-8, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (0.45, (-6, 0, 0)), (0.8, (0, 0, 0)))
    for side, s in (("r", -1), ("l", 1)):
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.3, (-70, 0, 40 * s)), (0.35, (-74, 0, 42 * s)), (0.45, (-10, 0, -10 * s), "linear"),
              (0.6, (-6, 0, -8 * s)), (0.8, (0, 0, 0)))
        a.rot(f"shin_f{side}", (0, (0, 0, 0)), (0.3, (0, 0, -40 * s)), (0.45, (0, 0, 20 * s), "linear"), (0.8, (0, 0, 0)))
    for part, ax in (("jaw_t", (-1, 0, 0)), ("jaw_b", (1, 0, 0)), ("jaw_r", (0, 1, 0)), ("jaw_l", (0, -1, 0))):
        a.rot(part, (0, (0, 0, 0)), (0.3, tuple(v * 30 for v in ax)), (0.45, (0, 0, 0)), (0.8, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, 1, 1)), (0.45, (0, -0.5, -2), "linear"), (0.6, (0, -0.5, -2)), (0.8, (0, 0, 0)))

    # screech: rears up on its back legs and the jaw petals peel slowly open (0.7 s telegraph, the throat light
    # swelling), then the screech (at 0.7 s = 14 ticks), petals flung wide and quivering
    a = m.anim("screech", 1.5)
    a.rot("body", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (0.7, (-42, 0, 0)), (0.75, (-46, 0, 0)), (1.2, (-44, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("seg2", (0, (0, 0, 0)), (0.6, (26, 0, 0)), (1.2, (26, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("seg3", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (1.2, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (16, 0, 0)), (0.75, (24, 0, 0)), (1.2, (20, 0, 0)), (1.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 3, 1)), (1.2, (0, 3, 1)), (1.5, (0, 0, 0)))
    for part, ax in (("jaw_t", (-1, 0, 0)), ("jaw_b", (1, 0, 0)), ("jaw_r", (0, 1, 0)), ("jaw_l", (0, -1, 0))):
        def k(d):
            return tuple(v * d for v in ax)
        a.rot(part, (0, (0, 0, 0)), (0.6, k(40)), (0.7, k(48)), (0.75, k(75)), (0.85, k(65)), (0.95, k(78)), (1.05, k(64)),
              (1.15, k(76)), (1.5, (0, 0, 0)))
    for side, s in (("r", -1), ("l", 1)):
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.6, (-50, 0, 30 * s)), (1.2, (-50, 0, 30 * s)), (1.5, (0, 0, 0)))
        a.rot(f"leg_m{side}", (0, (0, 0, 0)), (0.6, (-20, 0, 20 * s)), (1.2, (-20, 0, 20 * s)), (1.5, (0, 0, 0)))

    # drop: curls up tight, legs folding in over the belly (0.5 s telegraph: grit falls from where it clings), then lets
    # go (at 0.5 s = 10 ticks) and flings its legs wide to land on the prey
    a = m.anim("drop", 1.2)
    a.rot("body", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.5, (22, 0, 0)), (0.6, (-10, 0, 0), "linear"), (0.9, (-6, 0, 0)),
          (1.2, (0, 0, 0)))
    a.rot("seg2", (0, (0, 0, 0)), (0.45, (-30, 0, 0)), (0.6, (6, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("seg3", (0, (0, 0, 0)), (0.45, (-40, 0, 0)), (0.6, (10, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.45, (30, 0, 0)), (0.6, (-16, 0, 0), "linear"), (1.2, (0, 0, 0)))
    for key in ("f", "m", "b"):
        for side, s in (("r", -1), ("l", 1)):
            a.rot(f"leg_{key}{side}", (0, (0, 0, 0)), (0.45, (0, 0, 60 * s)), (0.5, (0, 0, 62 * s)), (0.6, (0, 0, -30 * s), "linear"),
                  (0.9, (0, 0, -24 * s)), (1.2, (0, 0, 0)))
            a.rot(f"shin_{key}{side}", (0, (0, 0, 0)), (0.45, (0, 0, -40 * s)), (0.6, (0, 0, 20 * s), "linear"), (1.2, (0, 0, 0)))
    for part, ax in (("jaw_t", (-1, 0, 0)), ("jaw_b", (1, 0, 0)), ("jaw_r", (0, 1, 0)), ("jaw_l", (0, -1, 0))):
        a.rot(part, (0, (0, 0, 0)), (0.5, (0, 0, 0)), (0.6, tuple(v * 50 for v in ax)), (1.0, tuple(v * 40 for v in ax)),
              (1.2, (0, 0, 0)))
