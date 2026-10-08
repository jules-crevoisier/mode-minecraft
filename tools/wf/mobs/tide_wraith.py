"""Tide Wraith (Spectre des marées): the drowned ghost of the Tidal Abbey, about 2 blocks tall.

Silhouette idea: a sailor the sea never gave back. A hunched, half-see-through ghost of pale sea-green light that
floats a hand above the ground: no legs, only a long robe of rotted sailcloth and kelp that tapers into wisps of
spray. A drowned skull with a hanging jaw and two drowned-lantern eyes looks out of a barnacled hood hung with strands
of seaweed; ribs show through its spectral chest. Its arms are far too long, ending in webbed claws, and a rusted
chain with a fishing gaff is wound round its right wrist: it hooks its prey and drags it under. In water it moves
like a current and blows pass through it.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

GHOST = (120, 206, 190)
GHOST_L = (196, 250, 236)
GHOST_D = (58, 132, 128)
BONE = (214, 222, 200)
BONE_D = (140, 150, 132)
EYE = (120, 255, 214)
EYE_L = (230, 255, 246)
SAIL = (98, 112, 104)
SAIL_D = (60, 72, 70)
KELP = (52, 104, 62)
KELP_D = (32, 70, 44)
SHELL = (210, 204, 186)
RUST = (130, 76, 44)
RUST_D = (84, 46, 28)


def a(c, alpha):
    return (*c[:3], alpha)


def spectral(seed=0, alpha=170):
    """Ghost flesh: see-through sea-green light, brighter at the top, veined with darker currents."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return a(GHOST_D, alpha - 30)
        k = 1.08 - 0.3 * y / max(1, h)
        c = mul(GHOST, k)
        if (x + y // 2 + seed) % 5 == 0:
            c = mix(c, GHOST_D, 0.5)
        if K.h(x, y, seed) % 13 == 0:
            c = GHOST_L
        return a(c, alpha)
    return f


def ribs(seed=0):
    def f(face, x, y, w, h):
        if face == "front" and 1 <= x <= w - 2 and 2 <= y <= h - 3:
            if x == w // 2 or x == w // 2 - 1:
                return BONE_D                                                                 # sternum
            if y % 2 == 0:
                return BONE
        return spectral(seed)(face, x, y, w, h)
    return f


def rags(seed=0, alpha=230, wisps=False, ragged=True):
    """Rotted sailcloth with kelp grown through it: vertical strips, holes, a torn lower edge; ``wisps`` fades the
    lowest rows into ghost light."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return a(SAIL_D, alpha) if face == "top" else None
        if ragged and y >= h - 1 - (K.h(x, seed) % 3):
            return None
        if K.h(x, y // 2, seed) % 17 == 0:
            return None                                                                       # a moth-eaten hole
        if wisps and y >= h // 2:
            return a(mix(GHOST, GHOST_L, (x % 2) * 0.4), 120 - 12 * (y - h // 2))
        if (x + seed) % 4 == 1:
            c = KELP if (y + x) % 3 else KELP_D
        else:
            c = mul(SAIL, 1.06 - 0.3 * y / max(1, h)) if x % 2 else mul(SAIL_D, 1.1)
        if K.h(x, y, seed + 3) % 29 == 0:
            c = SHELL
        return a(c, alpha)
    return f


def rags_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom") or y < h // 2:
            return None
        if y >= h - 1 - (K.h(x, seed) % 3) or K.h(x, y // 2, seed) % 17 == 0:
            return None
        return a(GHOST_L, 90)
    return f


def build():
    m = Model("tide_wraith", seed=649, shadow=0.4, walk_speed=0.9, walk_scale=1.0, render="entityTranslucent",
              glow_pulse=0.08)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("float", "bone", pivot=(0, -15, 0))
    m.part("torso", "float", pivot=(0, 0, 0), rot=(18, 0, 0))
    m.part("head", "torso", pivot=(0, -11, -1.5), rot=(-10, 0, 0))
    m.part("jaw", "head", pivot=(0, -0.5, -1), rot=(22, 0, 0))
    m.part("robe1", "float", pivot=(0, 0, 0.5))
    m.part("robe2", "robe1", pivot=(0, 6, 0.5), rot=(6, 0, 0))
    m.part("robe3", "robe2", pivot=(0, 5, 0.5), rot=(10, 0, 0))
    m.part("arm_r", "torso", pivot=(-5, -10, 0), rot=(-16, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(0, 8, 0), rot=(-24, 0, 0))
    m.part("arm_l", "torso", pivot=(5, -10, 0), rot=(-10, 0, -10))
    m.part("forearm_l", "arm_l", pivot=(0, 8, 0), rot=(-30, 0, 0))
    m.part("chain", "forearm_r", pivot=(-0.5, 9, 0), rot=(10, 0, 8))
    m.part("gaff", "chain", pivot=(0, 6, 0))
    m.part("weed_r", "head", pivot=(-3, -2, -2))
    m.part("weed_l", "head", pivot=(3, -2, -2))

    # ------------------------------------------------------------------ torso: spectral chest with ribs, rag mantle
    m.box("torso", -4, -11, -2.5, 8, 11, 5, ribs(1),
          glow={"front": lambda f_, x, y, w, h: a(EYE, 140) if 1 <= x <= w - 2 and 2 <= y <= h - 3 and y % 2 == 1 and
                x not in (w // 2, w // 2 - 1) else None, "*": None})
    m.box("torso", -5, -11.5, -3, 10, 4, 6, rags(2, ragged=False))                          # shoulder mantle
    m.box("torso", -4.5, -8, 1.8, 9, 8, 1, rags(3))                                           # rags down the back
    m.box("torso", -4.5, -2, -3, 9, 2, 6, {"*": a(RUST_D, 240), "front": lambda f_, x, y, w, h: a(RUST, 250) if x % 3 else
                                          a(RUST_D, 250)}, grow=0.05)                          # a rope belt gone to rust

    # ------------------------------------------------------------------ the robe tapering into spray
    m.box("robe1", -5, 0, -3, 10, 7, 6, rags(4))
    m.box("robe2", -4, 0, -2.5, 8, 6, 5, rags(5, alpha=210), glow=rags_glow(5))
    m.box("robe3", -3, 0, -2, 6, 6, 4, rags(6, alpha=180, wisps=True), glow=rags_glow(6))
    m.box("robe3", -1.5, 5, -1, 3, 3, 2, spectral(7, alpha=90), glow=a(GHOST_L, 80))

    # ------------------------------------------------------------------ head: drowned skull in a barnacled hood
    eyes = {(1, 2), (4, 2)}

    def skull(f_, x, y, w, h):
        if f_ == "front":
            if (x, y) in eyes:
                return EYE_L
            if y == 2 and x in (0, 2, 3, 5) or y == 1 and x in (1, 4):
                return (30, 46, 46)                                                           # the sockets
            if y == 4 and x in (2, 3):
                return (40, 50, 48)                                                           # the nose hole
            if y == 5:
                return BONE if x % 2 else BONE_D                                              # upper teeth
        c = BONE if (x + y) % 5 else BONE_D
        return mix(c, KELP, 0.25) if K.h(x, y, 8) % 9 == 0 else c
    m.box("head", -3, -6, -3, 6, 6, 6, skull,
          glow={"front": lambda f_, x, y, w, h: EYE if (x, y) in eyes else None, "*": None})
    m.box("jaw", -2.5, 0, -2.5, 5, 2, 4, {"front": lambda f_, x, y, w, h: BONE if y == 0 and x % 2 == 0 else BONE_D,
                                          "*": BONE_D})

    def hood(f_, x, y, w, h):
        if f_ == "front" and 1 <= x <= w - 2 and y >= 2:
            return None                                                                       # the open face
        if f_ == "bottom":
            return None
        if K.h(x, y, 9) % 11 == 0:
            return a(SHELL, 255)                                                              # barnacles
        return a(mul(SAIL, 1.1 - 0.3 * y / max(1, h)) if (x + y) % 4 else SAIL_D, 245)
    m.box("head", -4, -7.5, -4, 8, 8, 8, hood)
    m.box("head", -3, -8.5, -2, 6, 1, 6, a(SAIL_D, 245))                                      # the hood's crown
    m.box("head", -1, -8.5, 3, 2, 3, 2, rags(10, ragged=False))                               # the hood's tail
    for wpart, sx in (("weed_r", -1), ("weed_l", 1)):
        m.box(wpart, -0.5, 0, -0.5, 1, 9, 1, lambda f_, x, y, w, h: None if y >= 8 - (sx > 0) else
              a(KELP if y % 3 else KELP_D, 240))
        m.box(wpart, -0.5 + sx * 0.8, 0, 0.5, 1, 6, 1, lambda f_, x, y, w, h: a(KELP_D if y % 2 else KELP, 240))

    # ------------------------------------------------------------------ the long arms and webbed claws
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.5, 0, -1.5, 3, 8, 3, spectral(20 + sx, alpha=180))
        m.box(arm, -2, -1, -2, 4, 3, 4, rags(21 + sx, ragged=True))                          # rag sleeve
        m.box(fore, -1.5, 0, -1.5, 3, 8, 3, spectral(22 + sx, alpha=170))
        m.box(fore, -2, 8, -2, 4, 2, 4, spectral(23 + sx, alpha=200))                         # palm
        for i, fx in enumerate((-2, -0.5, 1)):
            m.box(fore, fx, 10, -2, 1, 4, 1, {"*": a(GHOST_D, 220), "bottom": a(BONE, 255)})  # long fingers
        m.box(fore, -1.5, 10, -1.6, 3, 3, 0, {"front": a(GHOST_L, 110), "back": a(GHOST_L, 110), "*": None})  # webbing

    # the rusted chain and the gaff hook wound round the right wrist
    m.box("forearm_r", -2, 6, -2, 4, 1, 4, a(RUST, 255), grow=0.15)
    for k in range(3):
        m.box("chain", -0.5, k * 2, -0.5, 1, 2, 1, lambda f_, x, y, w, h: a(RUST if y == 0 else RUST_D, 255))
    m.box("gaff", -0.5, 0, -0.5, 1, 4, 1, a(RUST_D, 255))
    m.box("gaff", -0.5, 3, -2.5, 1, 1, 2, a(RUST, 255))
    m.box("gaff", -0.5, 1, -3.5, 1, 3, 1, {"*": a(RUST, 255), "top": a((200, 190, 170), 255)})  # the hook point

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("float", (0, (0, 0, 0)), (1.5, (0, 1.5, 0)), (3.0, (0, 0, 0)))                    # bobbing on a swell
    idle.rot("torso", (0, (0, 0, 0)), (1.5, (4, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("robe1", (0, (0, 0, 0)), (1.0, (6, 0, -3)), (2.0, (-2, 0, 3)), (3.0, (0, 0, 0)))
    idle.rot("robe2", (0, (0, 0, 0)), (1.2, (10, 0, 4)), (2.2, (-4, 0, -4)), (3.0, (0, 0, 0)))
    idle.rot("robe3", (0, (0, 0, 0)), (1.4, (14, 0, -6)), (2.4, (-6, 0, 6)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-8, 0, 4)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-6, 0, -4)), (3.0, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (1.6, (0, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 0)), (1.5, (12, 0, -6)), (3.0, (0, 0, 0)))
    idle.rot("weed_r", (0, (0, 0, 0)), (1.5, (8, 0, 4)), (3.0, (0, 0, 0)))
    idle.rot("weed_l", (0, (0, 0, 0)), (1.5, (6, 0, -4)), (3.0, (0, 0, 0)))

    # glide: leaning into the motion, the robe streaming behind, arms trailing
    walk = m.anim("walk", 1.2)
    walk.rot("torso", (0, (6, 0, 0)), (0.6, (8, 0, 0)), (1.2, (6, 0, 0)))
    walk.rot("robe1", (0, (12, 0, 0)), (0.6, (16, 0, 4)), (1.2, (12, 0, 0)))
    walk.rot("robe2", (0, (10, 0, 0)), (0.6, (14, 0, -6)), (1.2, (10, 0, 0)))
    walk.rot("robe3", (0, (10, 0, 0)), (0.6, (16, 0, 8)), (1.2, (10, 0, 0)))
    walk.rot("arm_r", (0, (14, 0, 0)), (0.6, (18, 0, 6)), (1.2, (14, 0, 0)))
    walk.rot("arm_l", (0, (16, 0, 0)), (0.6, (10, 0, -6)), (1.2, (16, 0, 0)))
    walk.rot("weed_r", (0, (20, 0, 0)), (1.2, (20, 0, 0)))
    walk.rot("weed_l", (0, (20, 0, 0)), (1.2, (20, 0, 0)))
    walk.pos("float", (0, (0, 0, 0)), (0.6, (0, 0.8, 0)), (1.2, (0, 0, 0)))

    # rake: the left claw drawn back high, then a raking swipe across (lands at 0.35 s = 7 ticks)
    an = m.anim("rake", 0.8)
    an.rot("arm_l", (0, (0, 0, 0)), (0.25, (-150, 0, -30)), (0.35, (-40, 0, 30), "linear"), (0.55, (-30, 0, 30)), (0.8, (0, 0, 0)))
    an.rot("forearm_l", (0, (0, 0, 0)), (0.25, (-40, 0, 0)), (0.35, (0, 0, 0), "linear"), (0.8, (0, 0, 0)))
    an.rot("torso", (0, (0, 0, 0)), (0.25, (-6, -24, 0)), (0.35, (16, 24, 0), "linear"), (0.55, (14, 20, 0)), (0.8, (0, 0, 0)))
    an.rot("jaw", (0, (0, 0, 0)), (0.25, (30, 0, 0)), (0.5, (10, 0, 0)), (0.8, (0, 0, 0)))
    an.pos("float", (0, (0, 0, 0)), (0.25, (0, 1, 1)), (0.35, (0, 0, -3), "linear"), (0.8, (0, 0, 0)))

    # grab: both arms reach out wide and the jaw gapes (0.8 s telegraph), then it lunges and its claws close on the
    # prey (lands at 0.8 s = 16 ticks), then it pulls its arms back in, dragging
    an = m.anim("grab", 1.6)
    for arm, s in (("arm_r", 1), ("arm_l", -1)):
        an.rot(arm, (0, (0, 0, 0)), (0.7, (-100, 0, 40 * s)), (0.8, (-96, 0, 34 * s)), (0.9, (-90, 0, -12 * s), "linear"),
               (1.3, (-50, 0, -16 * s)), (1.6, (0, 0, 0)))
    for fore in ("forearm_r", "forearm_l"):
        an.rot(fore, (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.9, (-30, 0, 0), "linear"), (1.3, (-60, 0, 0)), (1.6, (0, 0, 0)))
    an.rot("torso", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (0.9, (20, 0, 0), "linear"), (1.3, (-6, 0, 0)), (1.6, (0, 0, 0)))
    an.rot("head", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (0.9, (6, 0, 0)), (1.6, (0, 0, 0)))
    an.rot("jaw", (0, (0, 0, 0)), (0.7, (46, 0, 0)), (0.9, (8, 0, 0), "linear"), (1.6, (0, 0, 0)))
    an.pos("float", (0, (0, 0, 0)), (0.7, (0, 2, 2)), (0.9, (0, 0, -5), "linear"), (1.3, (0, 1, 2)), (1.6, (0, 0, 0)))
    an.rot("robe1", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (0.9, (30, 0, 0)), (1.6, (0, 0, 0)))
    an.rot("robe3", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (0.9, (36, 0, 0)), (1.6, (0, 0, 0)))

    # sink: it folds down into a swirl and is gone (it reappears elsewhere at 0.8 s = 16 ticks)
    an = m.anim("sink", 0.9)
    an.pos("bone", (0, (0, 0, 0)), (0.3, (0, 2, 0)), (0.8, (0, -18, 0)), (0.9, (0, -20, 0)))
    an.scale("bone", (0, (1, 1, 1)), (0.3, (1.05, 1.1, 1.05)), (0.8, (0.2, 0.15, 0.2)), (0.9, (0.1, 0.1, 0.1)))
    an.rot("bone", (0, (0, 0, 0)), (0.3, (0, 20, 0)), (0.8, (0, -200, 0)), (0.9, (0, -220, 0)))
    an.rot("arm_r", (0, (0, 0, 0)), (0.3, (-160, 0, 20)), (0.8, (-170, 0, 10)), (0.9, (-170, 0, 10)))
    an.rot("arm_l", (0, (0, 0, 0)), (0.3, (-160, 0, -20)), (0.8, (-170, 0, -10)), (0.9, (-170, 0, -10)))

    # rise: it spirals up out of the water behind its prey (0.7 s)
    an = m.anim("rise", 0.7)
    an.pos("bone", (0, (0, -20, 0)), (0.5, (0, 2, 0)), (0.7, (0, 0, 0)))
    an.scale("bone", (0, (0.1, 0.1, 0.1)), (0.5, (1.05, 1.1, 1.05)), (0.7, (1, 1, 1)))
    an.rot("bone", (0, (0, 220, 0)), (0.5, (0, -10, 0)), (0.7, (0, 0, 0)))
    an.rot("arm_r", (0, (-170, 0, 10)), (0.5, (-60, 0, 30)), (0.7, (0, 0, 0)))
    an.rot("arm_l", (0, (-170, 0, -10)), (0.5, (-60, 0, -30)), (0.7, (0, 0, 0)))
    an.rot("jaw", (0, (0, 0, 0)), (0.4, (40, 0, 0)), (0.7, (0, 0, 0)))
