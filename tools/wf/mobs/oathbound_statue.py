"""Oathbound Statue-Knight (Chevalier-statue lié par serment): the stone guardians of the Kneeling Gate, about 2.6 blocks
tall.

Silhouette idea: a knight who swore to guard the gate past death and was turned to stone keeping the oath. Weathered
grey limestone carved as full plate: a closed great helm with a cross-shaped visor, a small stone crown and a crest
sweeping back like a frozen plume, broad pauldrons, a long carved surcoat and a heavy cape with a broken hem. Moss
grows in the folds and cracks run all over it. The oath binds it still: a stone tablet engraved with the oath hangs
on its chest from a chain, and broken shackles with a few chain links hang from both wrists. It holds a greatsword as
long as a man, point down.
Two texture variants on the same cubes: "dormant" (cold stone, dark cracks) while it kneels in its niche, and "awake"
(the cracks, the visor and the oath runes burn with an old gold light) once someone comes too close.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

STONE = (150, 148, 140)
STONE_L = (196, 194, 184)
STONE_D = (96, 94, 90)
STONE_DD = (64, 62, 60)
MOSS = (88, 112, 58)
MOSS_D = (60, 82, 40)
GOLD = (255, 196, 84)
GOLD_L = (255, 238, 170)
GOLD_D = (190, 120, 40)
CHAIN = (88, 84, 82)
CHAIN_D = (52, 50, 50)

VARIANTS = ["dormant", "awake"]


def crack(face, x, y, w, h, seed):
    """A zig-zag crack (one per face of a large enough cube), plus a short branch."""
    if face in ("bottom", "top") or w < 5 or h < 5:
        return False
    s = seed + {"front": 1, "back": 2, "left": 3, "right": 4}[face]
    if K.h(s, 7) % 5 >= 2:
        return False
    x0 = 1 + K.h(s, w, h) % (w - 2)
    xi = x0 + ((y + s) // 2) % 2 - (1 if (y + s) % 5 == 0 else 0)
    if x == xi and 1 <= y <= h - 2 - K.h(s, 3) % 3:
        return True
    yb = 1 + K.h(s, 9) % max(1, h - 3)
    return y == yb and 0 < x - xi <= 2


def stone(seed=0, awake=False, moss=0.04, cracks=True):
    """Weathered limestone: chisel marks, lit top edges, darker toward the bottom, moss in the lower rows and on the
    top faces, cracks (dark on the dormant statue, burning gold on the awake one)."""
    def f(face, x, y, w, h):
        if cracks and crack(face, x, y, w, h, seed):
            return GOLD if awake else STONE_DD
        if face == "bottom":
            return STONE_D
        r = K.h(x, y, seed, face == "top") % 1000 / 1000
        lim = moss * (1.5 if face == "top" else 0.2 + 1.6 * (y / max(1, h)) ** 2)
        if r < lim * 0.6:
            return MOSS if K.h(x, y, seed + 1) % 3 else MOSS_D
        if face == "top":
            return STONE_L if x in (0, w - 1) or y in (0, h - 1) else mul(STONE, 1.08)
        if y == 0:
            return STONE_L
        c = mul(STONE, 1.05 - 0.22 * y / max(1, h))
        if r > 0.96:
            c = mix(c, STONE_D, 0.6)
        elif r > 0.92:
            c = mix(c, STONE_L, 0.3)
        if (x // 3 + y // 2 + seed) % 7 == 0 and face != "top":
            c = mul(c, 0.94)                                                                  # chisel marks
        return c
    return f


def stone_glow(seed=0, awake=False):
    def f(face, x, y, w, h):
        if awake and crack(face, x, y, w, h, seed):
            return GOLD_L if K.h(x, y, seed) % 3 == 0 else GOLD
        return None
    return f


def carved_folds(seed=0, awake=False, hem_broken=True):
    """Stone cloth: deep vertical folds, a ragged broken hem, moss collecting low."""
    def f(face, x, y, w, h):
        if hem_broken and face not in ("top", "bottom") and y >= h - 1 - K.h(x // 2, seed) % 4:
            return None
        if crack(face, x, y, w, h, seed):
            return GOLD if awake else STONE_DD
        k = (x + K.h(x // 3, seed)) % 4
        c = STONE_D if k == 0 else (STONE_L if k == 2 else STONE)
        c = mul(c, 1.04 - 0.25 * y / max(1, h))
        if y > h * 0.6 and K.h(x, y, seed) % 6 == 0:
            c = MOSS_D
        return c
    return f


def build(variant="dormant"):
    awake = variant == "awake"
    m = Model("oathbound_statue", seed=637, shadow=0.8, walk_speed=0.7, walk_scale=1.0, variants=VARIANTS)

    def S(seed, moss=0.04, cracks=True):
        return stone(seed, awake, moss, cracks)

    def G(seed):
        return stone_glow(seed, awake)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-3, -17, 0))
    m.part("shin_r", "leg_r", pivot=(0, 9, 0))
    m.part("leg_l", "bone", pivot=(3, -17, 0))
    m.part("shin_l", "leg_l", pivot=(0, 9, 0))
    m.part("body", "bone", pivot=(0, -17, 0))
    m.part("head", "body", pivot=(0, -16, -0.5))
    m.part("cape", "body", pivot=(0, -15, 3.6), rot=(4, 0, 0))
    m.part("skirt_f", "body", pivot=(0, 0, -3.2))
    m.part("skirt_b", "body", pivot=(0, 0, 3.2))
    m.part("tablet", "body", pivot=(0, -14, -3.8))
    m.part("arm_r", "body", pivot=(-7.5, -14, 0), rot=(-10, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 7, 0), rot=(-30, 0, 0))
    m.part("sword", "forearm_r", pivot=(0, 6.5, -0.5), rot=(10, 0, 0))
    m.part("arm_l", "body", pivot=(7.5, -14, 0), rot=(4, 0, -6))
    m.part("forearm_l", "arm_l", pivot=(0, 7, 0), rot=(-12, 0, 0))
    m.part("shackle_l", "forearm_l", pivot=(1, 4, 0), rot=(0, 0, -8))
    m.part("shackle_r", "forearm_r", pivot=(-1, 4, 0), rot=(0, 0, 8))

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, 0, -2.5, 5, 9, 5, S(3 + sx), glow=G(3 + sx))
        m.box(leg, -3, 7, -3.5, 6, 3, 2, S(5 + sx, cracks=False))                          # poleyn
        m.box(shin, -2.5, 0, -2.5, 5, 6, 5, S(6 + sx, 0.2), glow=G(6 + sx))
        m.box(shin, -3, 6, -4.5, 6, 2, 7, S(7 + sx, 0.35, cracks=False))                    # sabaton

    # ------------------------------------------------------------------ body
    def breast(f_, x, y, w, h):
        if f_ == "front" and x == w // 2 and 1 <= y <= h - 3:
            return STONE_L                                                                    # the medial ridge
        return S(10)(f_, x, y, w, h)
    m.box("body", -6, -16, -3.5, 12, 13, 7, breast, glow=G(10))
    m.box("body", -5, -3.5, -3, 10, 4, 6, S(11), glow=G(11))
    m.box("body", -5.5, -4, -3.3, 11, 1, 7, {"*": STONE_D, "front": lambda f_, x, y, w, h: STONE_L if x == w // 2 else STONE_D},
          grow=0.1)                                                                           # sword belt
    m.box("skirt_f", -5.5, 0, -0.5, 11, 7, 1, carved_folds(12, awake), glow=G(12))
    m.box("skirt_b", -5.5, 0, -0.5, 11, 7, 1, carved_folds(13, awake), glow=G(13))
    m.box("body", -6.2, 0, -2.5, 1, 6, 5, carved_folds(14, awake, hem_broken=False))
    m.box("body", 5.2, 0, -2.5, 1, 6, 5, carved_folds(15, awake, hem_broken=False))
    m.box("body", -6.5, -17, -4, 13, 2, 8, S(16, 0.3, cracks=False))                          # gorget / collar
    m.box("cape", -6.5, 0, 0, 13, 27, 1, carved_folds(17, awake), glow=G(17))

    # the oath tablet hanging on the chest from a chain
    m.box("tablet", -3, 0, 0, 1, 2, 1, CHAIN)
    m.box("tablet", 2, 0, 0, 1, 2, 1, CHAIN)

    def oath(f_, x, y, w, h):
        if f_ != "front":
            return STONE_D
        if x in (0, w - 1) or y in (0, h - 1):
            return STONE_L if y == 0 else STONE_D
        if y % 2 == 0 and 1 <= x <= w - 2 and K.h(x, y, 18) % 4 != 0:
            return GOLD if awake else STONE_DD                                               # engraved lines of the oath
        return mix(STONE, STONE_L, 0.25)
    m.box("tablet", -3.5, 2, -0.6, 7, 6, 1, oath,
          glow={"front": lambda f_, x, y, w, h: GOLD if awake and 0 < x < w - 1 and 0 < y < h - 1 and y % 2 == 0 and
                K.h(x, y, 18) % 4 != 0 else None, "*": None})

    # ------------------------------------------------------------------ head: the great helm, crown and crest
    def helm(f_, x, y, w, h):
        if f_ == "front":
            if y == 3 and 1 <= x <= w - 2:
                return GOLD_L if awake and x in (2, w - 3) else (GOLD if awake else STONE_DD)   # the eye slit
            if x in (w // 2 - 1, w // 2) and 4 <= y <= 6:
                return GOLD_D if awake else STONE_DD                                           # the breath slot
            if x in (w // 2 - 1, w // 2) and y >= 4:
                return STONE_L
        return S(20, 0.15)(f_, x, y, w, h)

    def helm_glow(f_, x, y, w, h):
        if not awake or f_ != "front":
            return None
        if y == 3 and 1 <= x <= w - 2:
            return GOLD_L if x in (2, w - 3) else GOLD
        if x in (w // 2 - 1, w // 2) and 4 <= y <= 6:
            return GOLD_D
        return None
    m.box("head", -4, -9, -4, 8, 9, 8, helm, glow=helm_glow)
    m.box("head", -4.5, -10, -4.5, 9, 2, 9, S(21, 0.25, cracks=False))                       # crown band
    for i, (x, z) in enumerate(((-4.5, -4.5), (-0.5, -4.5), (3.5, -4.5), (-4.5, 3.5), (3.5, 3.5))):
        m.box("head", x, -12, z, 1, 2, 1, S(22 + i, 0.4, cracks=False))                       # crown points
    m.part("crest", "head", pivot=(0, -10, -2), rot=(-12, 0, 0))
    m.box("crest", -0.5, -3, -1, 1, 3, 4, S(28, 0.2, cracks=False))
    m.box("crest", -0.5, -2.5, 3, 1, 3, 4, S(29, 0.2, cracks=False))
    m.box("crest", -0.5, -1.5, 7, 1, 4, 3, S(30, 0.3, cracks=False))                          # the plume falls back

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -4 + sx * 0.5, -3, -3.5, 7, 5, 7, S(40 + sx, 0.25), glow=G(40 + sx))          # pauldron
        m.box(arm, -3.5 + sx * 0.5, 1, -3, 6, 1, 6, S(41 + sx, cracks=False))
        m.box(arm, -2.5, 0, -2.5, 5, 7, 5, S(42 + sx), glow=G(42 + sx))
        m.box(fore, -2.5, 0, -2.5, 5, 5, 5, S(43 + sx), glow=G(43 + sx))
        m.box(fore, -2.5, 5, -2.5, 5, 3, 5, S(44 + sx, 0.05, cracks=False))                   # gauntlet
        # the broken shackle round the wrist and two hanging links
        sh = f"shackle_{side}"
        m.box(sh, -3 - (1 if sx < 0 else 0), -1, -3, 6, 2, 6, {"*": CHAIN, "top": CHAIN_D}, grow=0.05)
        m.box(sh, -0.5 + sx * 2.5, 1, -0.5, 1, 2, 1, lambda f_, x, y, w, h: CHAIN if y == 0 else CHAIN_D)
        m.box(sh, -0.5 + sx * 2.5, 3, -0.5, 1, 2, 1, lambda f_, x, y, w, h: CHAIN_D if y == 0 else CHAIN)

    # ------------------------------------------------------------------ the greatsword: grip in the right fist, the
    # blade along the part's +y
    m.box("sword", -0.5, -5, -0.5, 1, 4, 1, {"*": STONE_D})                                  # grip
    m.box("sword", -1, -6.5, -1, 2, 2, 2, S(50, 0.2, cracks=False))                          # pommel
    m.box("sword", -4, 1, -1, 8, 1, 2, S(51, 0.2, cracks=False))                             # crossguard
    m.box("sword", -4.5, 0.5, -0.5, 1, 2, 1, STONE_L)
    m.box("sword", 3.5, 0.5, -0.5, 1, 2, 1, STONE_L)

    def blade(f_, x, y, w, h):
        if crack(f_, x, y, w, h, 52):
            return GOLD if awake else STONE_DD
        if f_ in ("front", "back") and x == w // 2:
            return STONE_D                                                                    # the fuller
        if f_ in ("left", "right"):
            return STONE_L
        return mul(STONE, 1.08 - 0.2 * y / h)
    m.box("sword", -2, 2, -0.5, 4, 21, 1, blade, glow=G(52), grow=0.1)
    m.box("sword", -1.5, 23, -0.5, 3, 2, 1, STONE)                                            # the tip
    m.box("sword", -0.5, 25, -0.5, 1, 1, 1, STONE_L)

    _anims(m)
    return m


def _kneel(a, t0, t1, hold_from=None):
    """Keyframes of the kneeling oath pose between t0 and t1 (constant)."""
    pose = {
        "bone": ("pos", (0, -8.5, 0)),
        "leg_r": ("rot", (-88, 0, 4)), "shin_r": ("rot", (88, 0, 0)),
        "leg_l": ("rot", (-4, 0, -4)), "shin_l": ("rot", (88, 0, 0)),
        "body": ("rot", (10, 0, 0)), "head": ("rot", (26, 0, 0)),
        "arm_r": ("rot", (-34, -14, -26)), "forearm_r": ("rot", (-34, 0, 0)), "sword": ("rot", (70, 0, 0)),
        "arm_l": ("rot", (-52, 14, 40)), "forearm_l": ("rot", (-48, 0, 0)),
        "cape": ("rot", (18, 0, 0)), "skirt_f": ("rot", (-40, 0, 0)), "skirt_b": ("rot", (30, 0, 0)),
    }
    return pose


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, -0.3, 0)), (4.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (2.0, (2, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("shackle_l", (0, (0, 0, 0)), (2.0, (0, 0, 4)), (4.0, (0, 0, 0)))
    idle.rot("shackle_r", (0, (0, 0, 0)), (2.0, (0, 0, -4)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (20, 0, 0)), (0.8, (-20, 0, 0)), (1.6, (20, 0, 0)))
    walk.rot("leg_l", (0, (-20, 0, 0)), (0.8, (20, 0, 0)), (1.6, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.4, (0, 0, 0)), (1.2, (26, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.4, (26, 0, 0)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (-12, 0, 0)), (0.8, (12, 0, 0)), (1.6, (-12, 0, 0)))
    walk.rot("body", (0, (2, 5, 0)), (0.8, (2, -5, 0)), (1.6, (2, 5, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.4, (0, -1, 0)), (0.8, (0, 0, 0)), (1.2, (0, -1, 0)), (1.6, (0, 0, 0)))  # heavy steps
    walk.rot("cape", (0, (6, 0, 0)), (0.8, (10, 0, 0)), (1.6, (6, 0, 0)))
    walk.rot("skirt_f", (0, (-8, 0, 0)), (0.8, (6, 0, 0)), (1.6, (-8, 0, 0)))

    pose = _kneel(None, 0, 0)

    # dormant: kneeling on one knee, both hands on the planted sword, head bowed (held for the whole loop; the entity
    # restarts it while it sleeps)
    a = m.anim("dormant", 4.0)
    for part, (kind, v) in pose.items():
        (a.pos if kind == "pos" else a.rot)(part, (0, v), (4.0, v))

    # wake: the head lifts first, then it rises from the knee and grips the sword (1.6 s)
    a = m.anim("wake", 1.6)
    late = {"head"}
    for part, (kind, v) in pose.items():
        ch = a.pos if kind == "pos" else a.rot
        if part in late:
            ch(part, (0, v), (0.4, (-12, 0, 0)), (1.0, (-8, 0, 0)), (1.6, (0, 0, 0)))
        else:
            ch(part, (0, v), (0.4, v), (1.3, tuple(c * 0.05 for c in v)), (1.6, (0, 0, 0)))

    # slam: the greatsword raised high over the crown and held (1.1 s telegraph), then brought down with both hands
    # (lands at 1.1 s = 22 ticks: a shockwave in front of it)
    a = m.anim("slam", 1.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-175, 0, -10)), (1.1, (-178, 0, -10)), (1.22, (-62, 0, -14), "linear"),
          (1.5, (-58, 0, -14)), (1.9, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.22, (24, 0, 0), "linear"), (1.5, (24, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-170, 0, 18)), (1.22, (-62, 20, 34), "linear"), (1.5, (-58, 20, 34)), (1.9, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.22, (-30, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (1.22, (26, 0, 0), "linear"), (1.5, (24, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.22, (8, 0, 0)), (1.9, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.9, (0, 1, 1)), (1.22, (0, -3, -2), "linear"), (1.5, (0, -3, -2)), (1.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.22, (-26, 0, 0)), (1.5, (-26, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.22, (20, 0, 0)), (1.5, (20, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.22, (18, 0, 0)), (1.5, (18, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (-4, 0, 0)), (1.22, (30, 0, 0)), (1.9, (0, 0, 0)))

    # sweep: the sword carried far out to the right (0.85 s telegraph), a flat sweep across the front (lands at
    # 0.85 s = 17 ticks)
    a = m.anim("sweep", 1.5)
    a.rot("body", (0, (0, 0, 0)), (0.75, (4, 60, 0)), (0.85, (4, 55, 0)), (1.0, (6, -70, 0), "linear"), (1.2, (6, -65, 0)),
          (1.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-80, 0, 60)), (1.0, (-85, 0, -30), "linear"), (1.2, (-80, 0, -30)), (1.5, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.75, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.75, (-10, 0, 0)), (1.0, (-10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.75, (-60, 0, 40)), (1.0, (-50, 0, -10)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.75, (0, -40, 0)), (1.0, (0, 40, 0)), (1.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.75, (0, -1.5, 0)), (1.0, (0, -1.5, -1)), (1.5, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.75, (10, 0, -10)), (1.0, (20, 0, 14)), (1.5, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.75, (-12 * s, 0, 6 * s)), (1.0, (12 * s, 0, 6 * s)), (1.5, (0, 0, 0)))

    # charge: it levels the sword at the hip, point first, and plants its feet (0.9 s telegraph), then strides forward
    # driving the point (0.9 to 1.5 s: the entity lunges 4 blocks), and recovers
    a = m.anim("charge", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-40, 20, 0)), (0.9, (-44, 20, 0)), (1.1, (-74, 0, 0), "linear"), (1.6, (-74, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.8, (-50, 0, 0)), (1.1, (-14, 0, 0), "linear"), (1.6, (-14, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("sword", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (1.1, (-20, 0, 0)), (1.6, (-20, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-50, -20, 30)), (1.1, (-70, -10, 30)), (1.6, (-70, -10, 30)), (2.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.8, (6, 30, 0)), (1.1, (16, 0, 0), "linear"), (1.6, (16, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (1.0, (-30, 0, 0)), (1.2, (24, 0, 0)), (1.4, (-30, 0, 0)), (1.6, (0, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-20, 0, 0)), (1.0, (24, 0, 0)), (1.2, (-30, 0, 0)), (1.4, (24, 0, 0)), (1.6, (0, 0, 0)),
          (2.2, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.8, (0, -1.5, 1)), (1.1, (0, -1, -1)), (1.6, (0, -1, -1)), (2.2, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.9, (6, 0, 0)), (1.2, (40, 0, 0)), (1.6, (30, 0, 0)), (2.2, (0, 0, 0)))
