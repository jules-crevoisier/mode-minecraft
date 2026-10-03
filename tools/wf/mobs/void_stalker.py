"""Void Stalker (Traqueur du vide): a tall, lanky hunter of the End, about 2.7 blocks tall.

Silhouette: a hunched, narrow-waisted body on long digitigrade legs, arms so long the claws hang by its
ankles, a smooth faceless head stretched backward with a single burning magenta eye slit, obsidian chitin
at every joint and down the spine, and a skin that is a window onto a starfield (glowing specks).
"""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
VOID_D = (12, 7, 24)
VIOLET = (46, 22, 80)
VIOLET_L = (84, 46, 132)
NEBULA_M = (112, 36, 120)
NEBULA_B = (30, 30, 98)
STAR = (236, 222, 255)
STAR_V = (196, 150, 255)
STAR_M = (255, 150, 236)
CHITIN = (20, 14, 28)
CHITIN_L = (76, 48, 112)
CHITIN_S = (128, 92, 170)
EYE = (255, 70, 220)
EYE_L = (255, 200, 250)

FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
def _star(x, y, seed, fid):
    """Star at this texel? Returns a colour or None. Sparse small stars, rarer bright crosses."""
    for dx, dy, big in ((0, 0, False), (1, 0, True), (-1, 0, True), (0, 1, True), (0, -1, True)):
        r = _h(x - dx, y - dy, seed, fid, 3)
        if r % 97 == 0:          # a bright cross-shaped star centred at (x - dx, y - dy)
            return STAR if (dx, dy) == (0, 0) else STAR_V
        if not big and r % 14 == 0:
            return (STAR, STAR_V, STAR_M)[r % 3]
    return None


def starfield(seed=0, grad=0.0):
    """Deep violet space with drifting nebula bands (magenta / blue) and star specks."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        s = _star(x, y, seed, fid)
        if s:
            return s
        n = math.sin(x * 0.55 + y * 0.35 + seed) + 0.7 * math.sin(y * 0.8 - x * 0.3 + seed * 1.7 + fid)
        c = mix(VOID_D, VIOLET, 0.8 + 0.2 * math.sin(x * 0.3 + seed))
        if n > 0.55:
            c = mix(c, NEBULA_M, min(0.75, (n - 0.55) * 0.9))
        elif n < -0.55:
            c = mix(c, NEBULA_B, min(0.75, (-0.55 - n) * 0.9))
        if abs(n - 0.55) < 0.12:
            c = mix(c, VIOLET_L, 0.5)                 # bright rim of the nebula band
        if grad and face not in ("top", "bottom"):
            c = mul(c, 1.0 - grad * y / max(1, h - 1))
        return c
    return f


def star_glow(seed=0):
    def f(face, x, y, w, h):
        s = _star(x, y, seed, FACE_N[face])
        return s if s else None
    return f


def chitin(seed=0):
    """Obsidian chitin: near-black with a violet sheen on the top edge and a few iridescent streaks."""
    def f(face, x, y, w, h):
        if face == "top":
            return CHITIN_L
        if face == "bottom":
            return CHITIN
        c = CHITIN
        if y == 0:
            c = mix(CHITIN_L, CHITIN_S, 0.3)
        elif y == 1:
            c = mix(CHITIN, CHITIN_L, 0.5)
        if (x + y * 2 + seed) % 7 == 0:
            c = mix(c, CHITIN_S, 0.35)
        return c
    return f


def claw(seed=0):
    def f(face, x, y, w, h):
        if y >= h - 1:
            return (220, 120, 230)   # pale magenta tip
        return mix(CHITIN, CHITIN_L, 0.3 + 0.4 * y / max(1, h - 1)) if (y + seed) % 3 else CHITIN_L
    return f


# ------------------------------------------------------------------ model
def mirror(x, w):
    return -(x + w)


def build():
    m = Model("void_stalker", seed=66, shadow=0.6, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -20, 0))
    m.part("torso", "hips", pivot=(0, -1, 0), rot=(20, 0, 0))
    m.part("head", "torso", pivot=(0, -13, -1.5), rot=(-16, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "torso", pivot=(4.5 * sx, -11.5, 0), rot=(-16, 0, -14 * sx))
        m.part(f"forearm_{side}", f"arm_{side}", pivot=(0, 13, 0), rot=(-30, 0, 6 * sx))
        m.part(f"hand_{side}", f"forearm_{side}", pivot=(0, 12, 0), rot=(-22, 0, 0))
        m.part(f"leg_{side}", "bone", pivot=(3 * sx, -20, 0), rot=(-32, 0, -4 * sx))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 10.5, 0), rot=(64, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 10, 0), rot=(-32, 0, 0))

    # ------------------------------------------------------------------ body
    m.box("hips", -3, -2, -2, 6, 3, 4, starfield(1), glow=star_glow(1))
    m.box("hips", -3.5, -0.5, -2.5, 7, 1, 5, chitin(2))                         # chitin girdle
    m.box("torso", -2, -5, -1.5, 4, 5, 3, starfield(3), glow=star_glow(3))     # wasp waist
    m.box("torso", -4, -12, -2.5, 8, 7, 5, starfield(4, grad=0.2), glow=star_glow(4))  # ribcage
    # chitin collar bones / shoulder caps and a spine of plates down the back
    m.box("torso", -5, -13, -2, 10, 2, 4, chitin(5))
    for i, y in enumerate((-12, -9, -6, -3)):
        m.box("torso", -1, y, 2.5 - (i > 1), 2, 2, 2, chitin(6 + i))
    # ribs: chitin bars across the front of the chest
    for y in (-10, -8):
        m.box("torso", -3.5, y, -3, 7, 1, 1, chitin(10 + y))

    # head: smooth faceless mask stretched backward, one burning eye slit
    slit = {(x, 3) for x in range(0, 6)} | {(2, 4), (3, 4)}

    def mask(f_, x, y, w, h):
        if (x, y) in slit:
            return EYE_L if x in (2, 3) else EYE
        if (y == 2 and 1 <= x <= 4) or (y == 4 and x in (1, 4)) or (y == 5 and x in (2, 3)):
            return (70, 16, 70)                       # scorched rim of the slit
        if y >= 5 and x in (2, 3) and y % 2:
            return mix(CHITIN, EYE, 0.25)             # faint seam down the mask
        t = y / max(1, h - 1)
        c = mix(mix(CHITIN, VIOLET_L, 0.45), VOID_D, 0.5 * t)
        if x in (0, w - 1):
            c = mul(c, 0.8)
        return c
    m.box("head", -1, -2, -1, 2, 2, 2, chitin(14))                              # neck
    m.box("head", -3, -8, -4, 6, 8, 6, {"front": mask, "top": starfield(15), "*": starfield(15)},
          glow={"front": lambda f_, x, y, w, h: (EYE_L if x in (2, 3) else EYE) if (x, y) in slit else None,
                "*": star_glow(15)})
    m.box("head", -2, 0, -4.5, 4, 2, 3, {"front": lambda f_, x, y, w, h: mix(CHITIN, VIOLET, 0.25), "*": chitin(19)})  # chin
    m.box("head", -2.5, -9, 1, 5, 5, 5, starfield(16), glow=star_glow(16))     # skull swept back
    m.box("head", -1.5, -9.5, 5, 3, 4, 3, starfield(17), glow=star_glow(17))
    m.box("head", -0.5, -10, -3, 1, 2, 10, chitin(18))                         # chitin crest along the skull

    # ------------------------------------------------------------------ limbs
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, hand = f"arm_{side}", f"forearm_{side}", f"hand_{side}"
        leg, shin, foot = f"leg_{side}", f"shin_{side}", f"foot_{side}"

        def bx(part, x, y, z, w, h, d, paint, glow=None):
            m.box(part, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        bx(arm, -1.5, -1.5, -1.5, 3, 3, 3, chitin(20 + sx))                     # shoulder knob
        bx(arm, -1, 0, -1, 2, 13, 2, starfield(21 + sx), glow=star_glow(21 + sx))
        bx(fore, -1.5, -1, -1.5, 3, 2, 3, chitin(22 + sx))                      # elbow
        bx(fore, -1, 0, -1, 2, 12, 2, starfield(23 + sx), glow=star_glow(23 + sx))
        bx(fore, -1.5, 8, -1.5, 3, 4, 3, chitin(24 + sx))                       # chitin bracer
        bx(hand, -1.5, 0, -1.5, 3, 2, 3, chitin(25 + sx))                       # palm
        for i, x in enumerate((-1.5, -0.5, 0.5)):
            bx(hand, x, 2, -1.5 + (i == 1) * -0.5, 1, 5 + (i == 1), 1, claw(i))
        bx(hand, -1.5, 1, 0.5, 1, 4, 1, claw(4))                                 # thumb claw, behind

        bx(leg, -1.5, -1, -1.5, 3, 3, 3, chitin(30 + sx))                       # hip joint
        bx(leg, -1, 0, -1, 2, 11, 2, starfield(31 + sx), glow=star_glow(31 + sx))
        bx(shin, -1.5, -1, -1.5, 3, 3, 3, chitin(32 + sx))                      # knee
        bx(shin, -1, 0, -1, 2, 10, 2, starfield(33 + sx), glow=star_glow(33 + sx))
        bx(foot, -1, 0, -1, 2, 2, 2, chitin(34 + sx))                           # ankle
        bx(foot, -1.5, 1, -5, 3, 1, 5, chitin(35 + sx))                         # long foot
        bx(foot, -1.5, 1, -6, 1, 1, 1, claw(5))
        bx(foot, 0.5, 1, -6, 1, 1, 1, claw(6))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.6)
    idle.rot("torso", (0, (0, 0, 0)), (1.3, (3, 0, 2)), (2.6, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.7, (0, 0, 12)), (1.0, (0, 0, 12)), (1.6, (4, -6, -6)), (2.6, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.3, (-4, 0, 3)), (2.6, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.3, (3, 0, -3)), (2.6, (0, 0, 0)))
    idle.rot("hand_r", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (0.7, (0, 0, 0)), (2.6, (0, 0, 0)))
    idle.rot("hand_l", (0, (0, 0, 0)), (1.6, (0, 0, 0)), (1.8, (-22, 0, 0)), (2.0, (0, 0, 0)), (2.6, (0, 0, 0)))
    idle.pos("hips", (0, (0, 0, 0)), (1.3, (0, -0.6, 0)), (2.6, (0, 0, 0)))

    walk = m.anim("walk", 1.4)
    walk.rot("leg_r", (0, (28, 0, 0)), (0.7, (-26, 0, 0)), (1.4, (28, 0, 0)))
    walk.rot("leg_l", (0, (-26, 0, 0)), (0.7, (28, 0, 0)), (1.4, (-26, 0, 0)))
    walk.rot("shin_r", (0, (-10, 0, 0)), (0.35, (20, 0, 0)), (0.7, (0, 0, 0)), (1.05, (-10, 0, 0)), (1.4, (-10, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.35, (-10, 0, 0)), (0.7, (-10, 0, 0)), (1.05, (20, 0, 0)), (1.4, (0, 0, 0)))
    walk.rot("arm_r", (0, (-22, 0, 0)), (0.7, (24, 0, 0)), (1.4, (-22, 0, 0)))
    walk.rot("arm_l", (0, (24, 0, 0)), (0.7, (-22, 0, 0)), (1.4, (24, 0, 0)))
    walk.rot("forearm_r", (0, (-10, 0, 0)), (0.7, (0, 0, 0)), (1.4, (-10, 0, 0)))
    walk.rot("forearm_l", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (1.4, (0, 0, 0)))
    walk.rot("torso", (0, (4, 6, 0)), (0.7, (4, -6, 0)), (1.4, (4, 6, 0)))
    walk.rot("head", (0, (-4, -6, 0)), (0.35, (0, 0, 0)), (0.7, (-4, 6, 0)), (1.05, (0, 0, 0)), (1.4, (-4, -6, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.35, (0, 1.2, 0)), (0.7, (0, 0, 0)), (1.05, (0, 1.2, 0)), (1.4, (0, 0, 0)))

    # rake: both long arms swung up and back (telegraph), claws scythed down together at 0.55 s (11 ticks)
    a = m.anim("rake", 1.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-150, 0, 40)), (0.55, (-30, 0, -30), "linear"), (0.75, (-25, 0, -25)),
          (1.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-150, 0, -40)), (0.55, (-30, 0, 30), "linear"), (0.75, (-25, 0, 25)),
          (1.1, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.4, (-50, 0, 0)), (0.55, (-10, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.4, (-50, 0, 0)), (0.55, (-10, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("hand_r", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (0.55, (-40, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("hand_l", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (0.55, (-40, 0, 0), "linear"), (1.1, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-22, 0, 0)), (0.55, (24, 0, 0), "linear"), (0.75, (20, 0, 0)), (1.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (10, 0, 0)), (0.55, (-20, 0, 0)), (1.1, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.4, (0, 0, 2)), (0.55, (0, -1, -4), "linear"), (0.75, (0, -1, -4)), (1.1, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (6, 0, 0)), (0.55, (-20, 0, 0)), (0.75, (-20, 0, 0)), (1.1, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (-4, 0, 0)), (0.55, (16, 0, 0)), (0.75, (16, 0, 0)), (1.1, (0, 0, 0)))

    # blink: it stretches into a thin line and collapses into nothing (teleport at 0.4 s = 8 ticks), then
    # unfolds again at its new position
    a = m.anim("blink", 1.0)
    a.scale("bone", (0, (1, 1, 1)), (0.25, (0.45, 1.35, 0.45)), (0.4, (0.05, 1.6, 0.05), "linear"),
            (0.45, (0.05, 1.6, 0.05)), (0.65, (0.5, 1.25, 0.5)), (0.85, (1.1, 0.92, 1.1)), (1.0, (1, 1, 1)))
    a.rot("bone", (0, (0, 0, 0)), (0.4, (0, 180, 0), "linear"), (0.45, (0, 180, 0)), (1.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (0, 0, 30)), (0.65, (0, 0, 30)), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (0, 0, -30)), (0.65, (0, 0, -30)), (1.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.25, (-30, 0, 0)), (0.65, (-20, 0, 0)), (1.0, (0, 0, 0)))
    return m
