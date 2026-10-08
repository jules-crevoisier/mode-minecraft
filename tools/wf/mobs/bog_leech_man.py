"""Bog Leech-Man (Homme-sangsue des tourbières): the thing under the walkways of the Mire Stilt-City, about 1.9 blocks.

Silhouette idea: a man the bog turned into a leech. A hunched, glossy body of olive-black flesh ringed like a worm,
too-long arms with webbed three-fingered hands hanging to its knees, frog-splayed legs on webbed feet. Its head is a
blunt eyeless snout ending in a round lamprey mouth: rings of hooked yellow teeth around a pink throat; a cluster of
tiny black pin-eyes sits on top. A ragged fin ridge runs down its back, smaller leeches cling to its shoulders and
arms, duckweed and reeds are plastered over it. It lurks in the water, leaps out at its prey, latches on with the
mouth and drinks.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

SKIN = (66, 72, 44)
SKIN_L = (118, 128, 76)
SKIN_D = (34, 38, 24)
BELLY = (132, 118, 70)
BELLY_D = (96, 84, 50)
SHEEN = (176, 190, 140)
STRIPE = (150, 104, 44)
MOUTH = (176, 70, 84)
MOUTH_D = (96, 30, 42)
TOOTH = (228, 210, 150)
TOOTH_D = (170, 150, 96)
EYE = (12, 12, 10)
WEED = (96, 150, 52)
WEED_D = (58, 100, 36)
REED = (150, 140, 84)
MUD = (74, 58, 40)
LEECH = (46, 34, 30)
LEECH_L = (110, 70, 54)


def flesh(seed=0, rings=True, belly=False):
    """Leech skin: glossy olive-black, ringed every two rows, a wet highlight running down, orange flank stripes."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = SKIN
        if belly and face == "front":
            c = BELLY if 0 < x < w - 1 else mix(BELLY, SKIN, 0.5)
        if rings and face != "top" and y % 2 == 1:
            c = mul(c, 0.84)                                                             # the annulations
        if face in ("left", "right") and abs(x - w // 2) == 0 and y % 4 < 2:
            c = mix(c, STRIPE, 0.6)                                                      # a broken flank stripe
        if face != "top" and x == 1 and y % 4 == 0:
            c = mix(c, SHEEN, 0.35)                                                      # the wet sheen
        if face == "top":
            c = mix(c, SHEEN, 0.2) if (x + y) % 3 == 0 else c
        r = K.h(x // 2, y // 2, seed) % 41
        if r == 0:
            c = mix(c, MUD, 0.6)
        elif r == 1:
            c = mix(c, WEED_D, 0.6)
        return c
    return f


def duckweed(base, seed=0, amount=0.25):
    def f(face, x, y, w, h):
        c = K.call(base, face, x, y, w, h)
        if c is None or face == "bottom":
            return c
        lim = amount * (1.2 if face == "top" else max(0.0, 1 - y / max(1, h) * 2.2))
        r = K.h(x // 2, y // 2, seed, 7) % 100 / 100
        if r < lim * 0.6:
            return WEED
        if r < lim:
            return WEED_D
        return c
    return f


def lamprey(face, x, y, w, h):
    """The round mouth seen head-on: lip rim, rings of hooked teeth, pink throat, a dark hole."""
    if face != "front":
        return flesh(30, rings=False)(face, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    if r > cx + 0.3:
        return mix(SKIN, SKIN_D, 0.4)
    if r > cx - 0.7:
        return SKIN_L if (x + y) % 2 else mix(SKIN_L, MOUTH, 0.3)                       # the lip
    if r > cx - 1.7:
        return TOOTH if (x + y) % 2 == 0 else MOUTH_D                                    # outer teeth ring
    if r > 1.2:
        return TOOTH_D if (x * 3 + y) % 4 == 0 else MOUTH
    return MOUTH_D


def leech(seed=0):
    def f(face, x, y, w, h):
        c = LEECH if (x + y + seed) % 2 else mix(LEECH, LEECH_L, 0.4)
        if face == "top":
            c = mix(c, LEECH_L, 0.3)
        return c
    return f


def fin(seed=0):
    def f(face, x, y, w, h):
        if face in ("left", "right"):
            if y == 0 and (x + seed) % 2 == 0:
                return None
            return mix(SKIN, STRIPE, 0.35) if y < 2 else SKIN_D
        return SKIN_D
    return f


def build():
    m = Model("bog_leech_man", seed=733, shadow=0.6, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton (deep crouch, head thrust forward)
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2.5, -11, 0.5), rot=(-20, 0, 8))
    m.part("shin_r", "leg_r", pivot=(0, 6, 0), rot=(34, 0, 0))
    m.part("foot_r", "shin_r", pivot=(0, 5.5, 0), rot=(-14, 0, 0))
    m.part("leg_l", "bone", pivot=(2.5, -11, 0.5), rot=(-20, 0, -8))
    m.part("shin_l", "leg_l", pivot=(0, 6, 0), rot=(34, 0, 0))
    m.part("foot_l", "shin_l", pivot=(0, 5.5, 0), rot=(-14, 0, 0))
    m.part("body", "bone", pivot=(0, -11, 1), rot=(32, 0, 0))
    m.part("chest", "body", pivot=(0, -7, 0), rot=(10, 0, 0))
    m.part("head", "chest", pivot=(0, -6, -1), rot=(-40, 0, 0))
    m.part("mouth", "head", pivot=(0, -2.5, -6))
    m.part("arm_r", "chest", pivot=(-5, -5, 0), rot=(-26, 0, 12))
    m.part("forearm_r", "arm_r", pivot=(0, 7, 0), rot=(-24, 0, 0))
    m.part("hand_r", "forearm_r", pivot=(0, 6, 0))
    m.part("arm_l", "chest", pivot=(5, -5, 0), rot=(-26, 0, -12))
    m.part("forearm_l", "arm_l", pivot=(0, 7, 0), rot=(-24, 0, 0))
    m.part("hand_l", "forearm_l", pivot=(0, 6, 0))
    m.part("leech_back", "chest", pivot=(2, -4, 3), rot=(30, 20, 0))
    m.part("leech_arm", "arm_l", pivot=(2, 3, 0), rot=(0, 0, -20))
    m.part("reeds", "chest", pivot=(-3, -6, 0))

    # ------------------------------------------------------------------ legs: frog-splayed, webbed feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin, foot = f"leg_{side}", f"shin_{side}", f"foot_{side}"
        m.box(leg, -2, 0, -2, 4, 6, 4, duckweed(flesh(1 + sx), 2 + sx, 0.1))
        m.box(shin, -1.5, 0, -1.5, 3, 6, 3, flesh(3 + sx))

        def web(f_, x, y, w, h):
            if f_ in ("top", "bottom"):
                if y == 0 and x % 2 == 1:
                    return None                                                          # gaps between the toes
                return mix(SKIN, MOUTH_D, 0.2) if f_ == "top" and y < h - 1 and x % 2 == 1 else SKIN_D
            return SKIN_D
        m.box(foot, -2.5, 0, -4.5, 5, 1, 6, web)
        for tx in (-2.5, -0.5, 1.5):
            m.box(foot, tx, 0, -5.5, 1, 1, 1, TOOTH_D)                                    # little hooked claws

    # ------------------------------------------------------------------ body: ringed belly and back, fin ridge
    m.box("body", -3.5, -7, -2.5, 7, 8, 5, flesh(10, belly=True))
    m.box("chest", -4.5, -7, -3, 9, 7, 6, duckweed(flesh(11, belly=True), 12, 0.18))
    m.box("chest", -4, -7.5, -2.5, 8, 1, 5, flesh(13, rings=False))                     # the hunched shoulders
    for i, (y, hgt) in enumerate(((-7, 3), (-4, 3), (-1, 2))):
        m.box("chest" if i < 2 else "body", -0.5, y + (0 if i < 2 else -5), 2.5 if i < 2 else 2, 1, hgt, 3, fin(i))
    m.box("body", -0.5, -3, 2, 1, 4, 2, fin(5))
    # mud caked on the hips
    m.box("body", -3.8, -1, -2.8, 7, 2, 5, duckweed(lambda f_, x, y, w, h: MUD if (x + y) % 3 else mul(MUD, 0.8), 14, 0.3),
          grow=0.15)

    # ------------------------------------------------------------------ head: blunt eyeless snout, lamprey mouth
    m.box("head", -3, -5, -6, 6, 5, 7, flesh(20, rings=True))
    m.box("head", -2.5, -5.5, -3, 5, 1, 4, flesh(21, rings=False))
    # the pin-eye cluster on top, glinting
    for i, (x, z) in enumerate(((-1.5, -3.5), (0.5, -4), (-0.5, -2.5), (1.5, -2.8))):
        m.box("head", x, -6, z, 1, 1, 1, {"top": EYE, "*": EYE}, glow={"top": (190, 200, 120) if i % 2 == 0 else None, "*": None})
    m.box("mouth", -3.5, -3, -1, 7, 7, 1, lamprey,
          glow={"front": lambda f_, x, y, w, h: (120, 30, 40) if ((x - 3) ** 2 + (y - 3) ** 2) ** 0.5 < 1.3 else None,
                "*": None})
    m.box("mouth", -3, -2.5, 0, 6, 6, 1, flesh(22, rings=False))
    # gill slits along the neck
    m.box("head", -3.2, -3, -2, 1, 2, 3, {"left": lambda f_, x, y, w, h: MOUTH_D if x % 2 == 0 else SKIN_D, "*": SKIN_D,
                                         "right": lambda f_, x, y, w, h: MOUTH_D if x % 2 == 0 else SKIN_D})
    m.box("head", 2.2, -3, -2, 1, 2, 3, {"left": lambda f_, x, y, w, h: MOUTH_D if x % 2 == 0 else SKIN_D, "*": SKIN_D,
                                        "right": lambda f_, x, y, w, h: MOUTH_D if x % 2 == 0 else SKIN_D})

    # ------------------------------------------------------------------ arms: too long, webbed three-fingered hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, hand = f"arm_{side}", f"forearm_{side}", f"hand_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 8, 3, duckweed(flesh(40 + sx), 41 + sx, 0.15))
        m.box(fore, -1.2, 0, -1.2, 2, 6, 2, flesh(42 + sx))
        m.box(fore, -1.5, 0, -1.5, 3, 2, 3, flesh(43 + sx, rings=False))                   # the elbow knob
        m.box(hand, -1.5, 0, -1.5, 3, 2, 3, flesh(44 + sx, rings=False))
        for k, fx in enumerate((-1.5, -0.5, 0.5)):
            m.box(hand, fx, 2, -1.5, 1, 3, 1, SKIN_D)                                      # long fingers
            m.box(hand, fx, 5, -1.7, 1, 1, 1, TOOTH_D)                                     # hooked claw tips
        m.box(hand, -1.5, 2, -1.2, 3, 2, 1, (*mix(SKIN, MOUTH_D, 0.3), 200))              # the web between the fingers

    # ------------------------------------------------------------------ hangers-on: leeches, reeds
    m.box("leech_back", -1, -0, -1, 2, 5, 2, leech(1))
    m.box("leech_back", -0.5, -1, -0.5, 1, 1, 1, MOUTH_D)
    m.box("leech_arm", -0.5, 0, -1, 1, 4, 2, leech(2))
    m.box("chest", -4.8, -5, -1, 1, 3, 2, leech(3))
    m.box("body", 3.3, -5, 0, 1, 3, 2, leech(4))
    for i, (x, z, hgt) in enumerate(((0, 0, 6), (1, 1, 4), (-1, 1.5, 5))):
        m.box("reeds", x, -hgt, z, 1, hgt, 1, {"*": REED if i % 2 else mix(REED, WEED, 0.4), "top": (110, 80, 50)})

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.6)
    idle.pos("body", (0, (0, 0, 0)), (1.3, (0, -0.6, 0)), (2.6, (0, 0, 0)))
    idle.rot("chest", (0, (0, 0, 0)), (1.3, (4, 0, 0)), (2.6, (0, 0, 0)))                     # slow breathing
    idle.scale("chest", (0, (1, 1, 1)), (1.3, (1.04, 1.0, 1.06)), (2.6, (1, 1, 1)))
    idle.rot("head", (0, (0, 0, 0)), (0.7, (6, 16, 0)), (1.6, (-4, -14, 0)), (2.6, (0, 0, 0)))
    idle.scale("mouth", (0, (1, 1, 1)), (0.4, (1.15, 1.15, 1)), (0.8, (1, 1, 1)), (2.6, (1, 1, 1)))
    idle.rot("leech_back", (0, (0, 0, 0)), (1.3, (14, 0, 6)), (2.6, (0, 0, 0)))
    idle.rot("leech_arm", (0, (0, 0, 0)), (1.3, (-10, 0, -8)), (2.6, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.3, (6, 0, 2)), (2.6, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.3, (4, 0, -2)), (2.6, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("leg_r", (0, (26, 0, 0)), (0.5, (-26, 0, 0)), (1.0, (26, 0, 0)))
    walk.rot("leg_l", (0, (-26, 0, 0)), (0.5, (26, 0, 0)), (1.0, (-26, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.25, (-10, 0, 0)), (0.75, (14, 0, 0)), (1.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (14, 0, 0)), (0.25, (0, 0, 0)), (0.5, (-10, 0, 0)), (1.0, (14, 0, 0)))
    walk.rot("arm_r", (0, (-24, 0, 0)), (0.5, (24, 0, 0)), (1.0, (-24, 0, 0)))                # knuckles near the ground
    walk.rot("arm_l", (0, (24, 0, 0)), (0.5, (-24, 0, 0)), (1.0, (24, 0, 0)))
    walk.rot("body", (0, (0, 6, 4)), (0.5, (0, -6, -4)), (1.0, (0, 6, 4)))                    # a slithering twist
    walk.rot("chest", (0, (0, -6, -3)), (0.5, (0, 6, 3)), (1.0, (0, -6, -3)))
    walk.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.5, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.5, 0)), (1.0, (0, 0, 0)))
    walk.rot("head", (0, (0, 6, 0)), (0.5, (0, -6, 0)), (1.0, (0, 6, 0)))
    walk.rot("leech_back", (0, (10, 0, 0)), (0.5, (-6, 0, 0)), (1.0, (10, 0, 0)))

    # claw: the right arm drawn back over the shoulder (0.4 s), a raking swipe down and across (lands at 0.4 s = 8 ticks)
    a = m.anim("claw", 0.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.32, (-140, 0, 40)), (0.4, (-150, 0, 44)), (0.5, (-10, 0, -30), "linear"),
          (0.65, (-6, 0, -30)), (0.9, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.32, (-40, 0, 0)), (0.5, (-10, 0, 0), "linear"), (0.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.32, (-14, 26, 0)), (0.5, (14, -24, 0), "linear"), (0.65, (12, -20, 0)), (0.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.32, (-10, -16, 0)), (0.5, (6, 10, 0)), (0.9, (0, 0, 0)))
    a.scale("mouth", (0, (1, 1, 1)), (0.32, (1.3, 1.3, 1)), (0.5, (1.1, 1.1, 1)), (0.9, (1, 1, 1)))
    a.pos("body", (0, (0, 0, 0)), (0.32, (0, 0, 1)), (0.5, (0, -0.5, -1.5), "linear"), (0.65, (0, -0.5, -1.5)), (0.9, (0, 0, 0)))

    # leap: sinks low on its frog legs, arms back, the mouth flaring open (0.6 s telegraph), then springs (launch at
    # 0.6 s = 12 ticks) arms reaching forward, mouth wide
    a = m.anim("leap", 1.3)
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, -3, 1)), (0.6, (0, -3.2, 1)), (0.7, (0, 1, -1), "linear"), (1.1, (0, 1, -1)),
          (1.3, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (0.6, (18, 0, 0)), (0.7, (-14, 0, 0), "linear"), (1.1, (-10, 0, 0)),
          (1.3, (0, 0, 0)))
    for side, s in (("r", 1), ("l", -1)):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.5, (-40, 0, 14 * s)), (0.6, (-42, 0, 14 * s)), (0.7, (40, 0, 4 * s), "linear"),
              (1.1, (30, 0, 4 * s)), (1.3, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (0.7, (-20, 0, 0), "linear"), (1.1, (-10, 0, 0)), (1.3, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.5, (50, 0, -20 * s)), (0.6, (54, 0, -22 * s)), (0.7, (-70, 0, 10 * s), "linear"),
              (1.1, (-64, 0, 14 * s)), (1.3, (0, 0, 0)))
        a.rot(f"hand_{side}", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (0.7, (-30, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (0.7, (20, 0, 0)), (1.3, (0, 0, 0)))
    a.scale("mouth", (0, (1, 1, 1)), (0.4, (1.2, 1.2, 1)), (0.5, (1.0, 1.0, 1)), (0.6, (1.35, 1.35, 1)), (0.7, (1.5, 1.5, 1)),
            (1.1, (1.45, 1.45, 1)), (1.3, (1, 1, 1)))

    # latch: clamped onto the prey, arms wrapped round it, the mouth pulsing as it drinks (a gulp every second: drains
    # at 1.0, 2.0 and 3.0 s = 20, 40, 60 ticks)
    a = m.anim("latch", 3.0)
    a.rot("body", (0, (0, 0, 0)), (0.2, (-20, 0, 0)), (3.0, (-20, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.2, (-10, 0, 0)), (3.0, (-10, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.2, (30, 0, 0)), (3.0, (30, 0, 0)))
    for side, s in (("r", 1), ("l", -1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.2, (-40, 20 * s, -24 * s)), (3.0, (-40, 20 * s, -24 * s)))
        a.rot(f"forearm_{side}", (0, (0, 0, 0)), (0.2, (10, 0, -40 * s)), (3.0, (10, 0, -40 * s)))
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.2, (-50, 0, 20 * s)), (3.0, (-50, 0, 20 * s)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.2, (60, 0, 0)), (3.0, (60, 0, 0)))
    gulps = [(0, (1, 1, 1))]
    for k in range(3):
        t = k * 1.0
        gulps += [(t + 0.6, (1.3, 1.3, 1)), (t + 1.0, (0.85, 0.85, 1))]
    a.scale("mouth", *gulps)
    a.scale("chest", (0, (1, 1, 1)), (0.6, (1.0, 1.0, 1.0)), (1.0, (1.08, 1.0, 1.1)), (1.6, (1.0, 1.0, 1.0)),
            (2.0, (1.1, 1.0, 1.12)), (2.6, (1.02, 1.0, 1.02)), (3.0, (1.12, 1.0, 1.14)))
