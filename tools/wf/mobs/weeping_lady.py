"""The Weeping Lady (La Dame en pleurs): champion of the Lithite Well, a giant banshee matriarch (about 3.8 blocks,
4.5 with her crown) floating over the floor.

Silhouette: a tall veiled figure whose bell of pale lace skirts flares into tattered, glowing wisps; a crown of
jagged lithite shards (one broken) rising out of the veil; a long lace veil streaming down her back into a
train; and impossibly long arms with bell sleeves and four-clawed hands that hang to her knees. Through the
lace over her face: hollow eyes and streaks of crystal tears that glow mint, with lithite tear-drops hanging
from the veil's hem and a lithite brooch at her breast.

Animations (impact time -> Java wind-up ticks): claw 0.6 s (12), rake 0.55 s / 1.0 s (11 / 20), wail 0.9 s
(18), erupt 1.0 s (20), summon 0.6 s (12), veil 0.8 s (16), swoop 0.7 s (14), roar, stagger.
"""
import math

from ..models import Model
from ..texgen import mix, mul

LACE = (242, 240, 230)
LACE_D = (186, 188, 186)
UNDER = (70, 82, 106)
UNDER_D = (44, 52, 72)
SHADE = (40, 50, 70)
SKIN = (216, 224, 226)
SKIN_D = (150, 164, 176)
HOLLOW = (14, 20, 28)
LITH = (150, 240, 220)
LITH_L = (214, 255, 244)
LITH_D = (60, 150, 140)
CLAW = (52, 60, 76)
FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


def _tatter(x, y, h, seed, tatter):
    if not tatter:
        return False
    sw = 1 + _h(seed, x // 2) % 3
    r = _h((x + seed) // sw, seed, 5)
    cut = r % (tatter + 1)
    if r % 4 == 0:
        cut = tatter
    return y >= h - cut


# ------------------------------------------------------------------ paints
def lace(seed=0, base=LACE, under=UNDER, tile=6, tatter=0, holes=False, grad=0.4, scallop=True, net_holes=True):
    """Bobbin lace over a cold under-gown: diamond eyelets ringed with thread, a fine net between motifs,
    a scalloped band above the hem; holes become see-through on thin veils."""
    c0 = (tile - 1) / 2.0

    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 0.8) if face == "top" else mix(under, SHADE, 0.4)
        if _tatter(x, y, h, seed, tatter):
            return None
        u, v = (x + seed) % tile, (y + (tile // 2 if ((x + seed) // tile) % 2 else 0)) % tile
        d = abs(u - c0) + abs(v - c0)
        t = y / max(1, h - 1)
        if d < 0.9:
            if holes:
                return None
            c = mix(under, SHADE, 0.3)                        # eyelet: the under-gown shows through
        elif d < 1.9:
            c = base                                          # thread ring
        elif d < 2.6:
            c = mix(base, LACE_D, 0.35)
        else:
            if holes and net_holes and (x + y) % 2 == 0:
                return None
            c = mix(base, under, 0.62 if (x + y) % 2 else 0.18)   # open net: the dark under-gown shows
        if scallop and tatter and h - tatter - 4 <= y <= h - tatter - 3:
            c = base if (x % 4) in (1, 2) else mix(base, LACE_D, 0.6)
        c = mix(c, SHADE, grad * t * t)
        if _h(x, y, seed, FACE_N[face]) % 41 == 0:
            c = mix(c, LACE_D, 0.5)
        return c
    return f


def gown(seed=0, base=UNDER, tatter=0, grad=0.5):
    """Plain under-gown: soft vertical folds darkening to the hem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 0.75)
        if _tatter(x, y, h, seed, tatter):
            return None
        s = math.sin(x * 1.1 + seed) * 0.6 + math.sin(x * 0.4 + seed * 0.3) * 0.4
        c = mul(base, 1 + 0.12 * s)
        if s < -0.75:
            c = mix(c, UNDER_D, 0.5)
        return mix(c, SHADE, grad * (y / max(1, h - 1)) ** 2)
    return f


def wisp_glow(seed=0, tatter=0, from_t=0.55, alpha=110):
    def f(face, x, y, w, h):
        if face in ("top", "bottom") or _tatter(x, y, h, seed, tatter):
            return None
        t = y / max(1, h - 1)
        if t < from_t:
            return None
        a = int(alpha * (t - from_t) / max(0.01, 1 - from_t))
        if (x * 3 + y + seed) % 5 == 0:
            a = min(255, int(a * 1.6))
        return (*LITH, a)
    return f


def skin(seed=0, base=SKIN):
    def f(face, x, y, w, h):
        c = mul(base, 1 + ((_h(x, y, seed, FACE_N[face]) % 100) - 50) / 900)
        if face == "bottom":
            return mul(c, 0.8)
        if (x == 0 or x == w - 1) and w > 2:
            c = mix(c, SKIN_D, 0.4)
        if _h(x, y, seed) % 29 == 0:
            c = mix(c, (150, 175, 205), 0.45)     # faint blue veins
        return c
    return f


def crystal(seed=0, glow=False):
    """Lithite shard: pale facets with bright edges, deeper core, the tip the brightest."""
    def f(face, x, y, w, h):
        t = y / max(1, h - 1)  # 0 at the top
        if face == "top":
            return LITH_L if not glow else (*LITH_L, 255)
        if face == "bottom":
            return LITH_D if not glow else None
        edge = x == 0 or x == w - 1
        if glow:
            a = int(230 - 150 * t) if edge or t < 0.3 else int(90 - 60 * t)
            return (*(LITH_L if edge else LITH), max(0, a))
        c = mix(LITH_L, LITH_D, 0.2 + 0.6 * t)
        if edge:
            c = mix(c, LITH_L, 0.6)
        elif (x + y + seed) % 4 == 0:
            c = mix(c, LITH_D, 0.4)                  # inner fracture
        return c
    return f


def face_paint():
    """Front of the head (w=7, h=8): hollow eyes, sunken cheeks, tear tracks and a thin dark mouth."""
    sk = skin(9)

    def f(face, x, y, w, h):
        c = sk(face, x, y, w, h)
        if face != "front":
            return c
        if y == 2 and x in (1, 2, 4, 5):
            return mix(c, SKIN_D, 0.8)                 # brow shadow
        if y in (3, 4) and x in (1, 2, 4, 5):
            return HOLLOW                              # sockets
        if y >= 5 and x in (2, 4):
            return mix(LITH, SKIN_D, 0.3)              # tear tracks
        if y in (5, 6) and x in (0, 6):
            return mix(c, SKIN_D, 0.6)                 # hollow cheeks
        if y == 7 and x == 3:
            return (60, 64, 80)
        return c
    return f


def face_glow(face, x, y, w, h):
    if face != "front":
        return None
    if y == 4 and x in (2, 4):
        return LITH_L
    if y == 3 and x in (2, 4):
        return (*LITH, 150)
    if y >= 5 and x in (2, 4):
        return (*LITH, 230 - (y - 5) * 30)
    return None


def claw_paint(face, x, y, w, h):
    t = y / max(1, h - 1)
    return mix(SKIN_D, CLAW, min(1.0, t * 1.5)) if face not in ("top", "bottom") else CLAW


# ------------------------------------------------------------------ model
def build():
    m = Model("weeping_lady", seed=83, shadow=1.1, walk_speed=0.6, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -30, 0))
    m.part("torso", "body", pivot=(0, 0, 0), rot=(4, 0, 0))
    m.part("head", "torso", pivot=(0, -17, -0.5))
    m.part("jaw", "head", pivot=(0, -2, 1))
    m.part("veil", "head", pivot=(0, -11, 4), rot=(8, 0, 0))
    m.part("veil2", "veil", pivot=(0, 22, 0.5), rot=(14, 0, 0))
    m.part("crown_r", "head", pivot=(-3.5, -12.5, -1), rot=(0, 0, -22))
    m.part("crown_l", "head", pivot=(3.5, -12.5, -1), rot=(0, 0, 18))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"arm_{side}", "torso", pivot=(sx * 8, -15.5, 0), rot=(-8, 0, -10 * sx))
        m.part(f"forearm_{side}", f"arm_{side}", pivot=(0, 13, 0), rot=(-16, 0, 0))
        m.part(f"hand_{side}", f"forearm_{side}", pivot=(0, 13, 0), rot=(-12, 0, 0))
    m.part("skirt", "body", pivot=(0, 0, 0))
    m.part("skirt2", "skirt", pivot=(0, 8, 0.5), rot=(2, 0, 0))
    m.part("skirt3", "skirt2", pivot=(0, 9, 0.5), rot=(4, 0, 0))
    m.part("train", "skirt2", pivot=(0, 1, 6.5), rot=(42, 0, 0))
    m.part("train2", "train", pivot=(0, 12, 0), rot=(20, 0, 0))

    # torso: a narrow laced corset, a lace bodice, a high fan collar behind the head, a lithite brooch
    m.box("torso", -4.5, -8, -3, 9, 8, 6, {"front": lambda f_, x, y, w, h: (60, 70, 92) if x == 4 and y % 2 == 0 else
                                           gown(1, base=UNDER, grad=0.0)(f_, x, y, w, h), "*": gown(1, base=UNDER, grad=0.0)})
    m.box("torso", -6, -16, -3.5, 12, 8, 7, lace(2, tile=5, grad=0.0, scallop=False))
    m.box("torso", -7.5, -17.5, -3.5, 15, 3, 7, lace(3, base=(240, 238, 230), tile=4, grad=0.0, scallop=False))
    m.box("torso", -1.5, -13, -4.5, 3, 3, 1, crystal(4), glow=crystal(4, True))           # brooch
    m.box("torso", -5, -2, -3.5, 10, 2, 7, (70, 82, 104))                                 # sash
    m.box("torso", -1.5, -19, -1.5, 3, 2, 3, skin(5))                                     # neck
    m.part("collar", "torso", pivot=(0, -17, 2.5), rot=(-14, 0, 0))
    m.box("collar", -8, -13, 0, 16, 13, 0, {"front": lace(6, tile=4, tatter=2, grad=0.0, scallop=False, holes=True, net_holes=False),
                                           "back": lace(6, tile=4, tatter=2, grad=0.0, scallop=False, holes=True, net_holes=False),
                                           "*": None},
          glow={"side": lambda f_, x, y, w, h: (*LITH, 90) if y < 2 and x % 3 == 0 else None})

    # head: gaunt face, a lace half-veil over the eyes, lace cap, a crown of lithite
    m.box("head", -3.5, -10, -4, 7, 8, 7, {"front": face_paint(), "*": skin(9)}, glow=face_glow)
    m.box("head", -2.5, -3, -3.5, 5, 2, 4, {"front": (24, 30, 40), "*": HOLLOW},
          glow={"front": lambda f_, x, y, w, h: (*LITH, 180) if y == 1 and 1 <= x <= 3 else None})  # throat
    m.box("jaw", -3, 0, -5, 6, 3, 6, {"front": lambda f_, x, y, w, h: (60, 64, 80) if y == 0 else skin(10)(f_, x, y, w, h),
                                      "top": (30, 24, 40), "*": skin(10)})
    m.box("head", -4.5, -11.5, -5, 9, 2, 9, lace(11, tile=4, grad=0.0, scallop=False))              # lace cap
    m.box("head", -4.5, -10, -4, 1, 12, 8, lace(12, tile=4, tatter=4, grad=0.2))                   # side drapes
    m.box("head", 3.5, -10, -4, 1, 12, 8, lace(13, tile=4, tatter=4, grad=0.2))
    m.box("head", -4, -9.5, -5.2, 8, 5, 0, {"front": lace(14, tile=4, holes=True, grad=0.0, scallop=False, tatter=2),
                                           "back": lace(14, tile=4, holes=True, grad=0.0, scallop=False, tatter=2),
                                           "*": None})                                             # half-veil
    for i, (x, hh) in enumerate(((-3, 3), (2, 2))):
        m.box("head", x, -1, -4.6, 1, hh, 1, crystal(20 + i), glow=crystal(20 + i, True))          # crystal tears
    m.box("head", -4.5, -12.5, -5, 9, 1, 9, crystal(25), glow={"side": crystal(25, True)})         # circlet
    for i, (x, z, hh) in enumerate(((-2, -5, 9), (0.5, -5.5, 14), (2.5, -5, 8), (-1, 2.5, 7), (1.5, 2.5, 10))):
        w = 2 if hh > 8 else 1
        m.box("head", x - w / 2, -12.5 - hh, z, w, hh, 2, crystal(30 + i), glow=crystal(30 + i, True))
    m.box("crown_r", -1, -9, -1, 2, 9, 2, crystal(36), glow=crystal(36, True))
    m.box("crown_r", -2.5, -5, 0, 1, 5, 1, crystal(37), glow=crystal(37, True))
    m.box("crown_l", -1, -4, -1, 2, 4, 2, crystal(38), glow=crystal(38, True))                     # the broken shard
    m.box("veil", -5.5, 0, 0, 11, 22, 1, lace(40, tile=6, grad=0.25, scallop=False))
    m.box("veil2", -6, 0, 0, 12, 16, 1, lace(41, tile=6, tatter=6, grad=0.5), glow=wisp_glow(41, 6, 0.4, 90))

    # arms: lace-sleeved upper arms, bony forearms in bell sleeves, long four-clawed hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, hand = f"arm_{side}", f"forearm_{side}", f"hand_{side}"
        m.box(arm, -2, -1.5, -2, 4, 14, 4, lace(50 + sx, tile=4, grad=0.1, scallop=False))
        m.box(fore, -1, 0, -1, 2, 13, 2, skin(52 + sx))
        m.box(fore, -3, -1, -3, 6, 10, 6, lace(53 + sx, tile=4, tatter=4, grad=0.35), glow=wisp_glow(53 + sx, 4, 0.6, 70))
        m.box(hand, -2, 0, -2, 4, 3, 3, skin(54 + sx))
        for i, x in enumerate((-2, -0.75, 0.5, 1.75)):
            m.box(hand, x, 2.5, -1.5 - (i % 2) * 0.5, 1, 9 if i in (1, 2) else 7, 1, claw_paint)
        m.box(hand, (2.5 if sx < 0 else -3.5), 1, -1, 1, 5, 1, claw_paint)  # thumb claw

    # gown: a lace bell flaring over three tiers, dissolving into glowing tatters, a long train behind
    m.box("skirt", -5.5, 0, -4, 11, 8, 9, lace(60, grad=0.1, scallop=False))
    m.box("skirt2", -7.5, 0, -6, 15, 9, 12, lace(61, grad=0.2, scallop=False))
    m.box("skirt3", -9.5, 0, -7.5, 19, 9, 15, lace(62, tatter=7, grad=0.55), glow=wisp_glow(62, 7, 0.25, 170))
    m.box("skirt2", -8, 5, -6.5, 16, 4, 13, {"side": lace(63, tile=4, tatter=2, grad=0.1), "*": None})   # lace flounce
    for i, (x, z, hh) in enumerate(((-9.7, -5, 9), (9.7, -3, 8), (-9.7, 3, 7), (9.7, 4, 10))):
        m.box("skirt3", x, 3, z, 0, hh, 4, {"left": lace(70 + i, tatter=3, grad=0.6), "right": lace(70 + i, tatter=3, grad=0.6),
                                            "*": None}, glow={"side": wisp_glow(70 + i, 3, 0.2, 140)})
    m.box("train", -6, 0, 0, 12, 12, 0, {"front": lace(80, grad=0.2, scallop=False), "back": lace(80, grad=0.2, scallop=False),
                                         "*": None})
    m.box("train2", -6, 0, 0, 12, 12, 0, {"front": lace(81, tatter=6, grad=0.6), "back": lace(81, tatter=6, grad=0.6), "*": None},
          glow={"side": wisp_glow(81, 6, 0.3, 140)})

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.pos("bone", (0, (0, 0, 0)), (2.0, (0, 2.5, 0)), (4.0, (0, 0, 0)))
    idle.rot("torso", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (6, -6, 4)), (3.0, (6, 6, -4)), (4.0, (0, 0, 0)))
    idle.rot("veil", (0, (0, 0, 0)), (2.0, (6, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("veil2", (0, (0, 0, 0)), (1.4, (10, 0, -3)), (3.0, (-2, 0, 3)), (4.0, (0, 0, 0)))
    idle.rot("skirt2", (0, (0, 0, 0)), (2.0, (2, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("skirt3", (0, (0, 0, 0)), (1.3, (5, 0, -2)), (3.1, (-2, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("train", (0, (0, 0, 0)), (2.0, (8, 3, 0)), (4.0, (0, 0, 0)))
    idle.rot("train2", (0, (0, 0, 0)), (1.2, (-6, 0, 0)), (2.8, (12, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-5, 0, 4)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, -5)), (4.0, (0, 0, 0)))
    idle.rot("hand_r", (0, (0, 0, 0)), (1.0, (-12, 0, 0)), (2.0, (0, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("hand_l", (0, (0, 0, 0)), (2.5, (-10, 0, 0)), (3.5, (0, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.4)   # the drift: leaning into the glide, the lace streaming back
    walk.rot("body", (0, (7, 0, 0)), (1.2, (9, 0, 0)), (2.4, (7, 0, 0)))
    walk.rot("head", (0, (-6, 0, 0)), (1.2, (-8, 0, 0)), (2.4, (-6, 0, 0)))
    walk.rot("skirt2", (0, (6, 0, 0)), (1.2, (9, 0, 2)), (2.4, (6, 0, 0)))
    walk.rot("skirt3", (0, (10, 0, 0)), (0.6, (14, 0, 3)), (1.8, (8, 0, -3)), (2.4, (10, 0, 0)))
    walk.rot("train", (0, (14, 0, 0)), (1.2, (20, 0, 0)), (2.4, (14, 0, 0)))
    walk.rot("veil", (0, (14, 0, 0)), (1.2, (20, 0, 0)), (2.4, (14, 0, 0)))
    walk.rot("veil2", (0, (10, 0, 0)), (0.8, (18, 0, 0)), (1.8, (6, 0, 0)), (2.4, (10, 0, 0)))
    walk.rot("arm_r", (0, (16, 0, 4)), (1.2, (22, 0, 6)), (2.4, (16, 0, 4)))
    walk.rot("arm_l", (0, (22, 0, -6)), (1.2, (16, 0, -4)), (2.4, (22, 0, -6)))

    # claw: right arm rises high behind (0.6 s), a diagonal rake down across the front (12 ticks)
    a = m.anim("claw", 1.4)
    a.rot("torso", (0, (0, 0, 0)), (0.55, (-10, 30, 0)), (0.65, (14, -28, 0), "linear"), (0.9, (12, -24, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-165, 0, 30)), (0.65, (-30, 0, -30), "linear"), (0.9, (-25, 0, -25)), (1.4, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.55, (-35, 0, 0)), (0.65, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("hand_r", (0, (0, 0, 0)), (0.55, (-30, 0, 0)), (0.65, (20, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.55, (-25, 0, -30)), (0.65, (10, 0, -15)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-6, 15, 0)), (0.65, (8, -10, 0)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.55, (0, 2, 3)), (0.65, (0, 0, -5), "linear"), (0.9, (0, 0, -5)), (1.4, (0, 0, 0)))

    # rake: left claw (0.55 s / 11 ticks), then the right (1.0 s / 20 ticks)
    a = m.anim("rake", 1.7)
    a.rot("torso", (0, (0, 0, 0)), (0.45, (-6, -28, 0)), (0.55, (10, 24, 0), "linear"), (0.9, (-6, 28, 0)),
          (1.0, (12, -26, 0), "linear"), (1.25, (10, -22, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (-150, 0, -35)), (0.55, (-25, 0, 30), "linear"), (0.9, (-15, 0, 20)), (1.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (-20, 0, 10)), (0.9, (-155, 0, 35)), (1.0, (-25, 0, -30), "linear"),
          (1.25, (-20, 0, -25)), (1.7, (0, 0, 0)))
    a.rot("hand_l", (0, (0, 0, 0)), (0.45, (-30, 0, 0)), (0.55, (20, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("hand_r", (0, (0, 0, 0)), (0.9, (-30, 0, 0)), (1.0, (20, 0, 0)), (1.7, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.45, (0, 1, 2)), (0.55, (0, 0, -3), "linear"), (0.9, (0, 1, -2)),
          (1.0, (0, 0, -6), "linear"), (1.25, (0, 0, -6)), (1.7, (0, 0, 0)))

    # wail: rise and arch back with arms opening, jaw unhinging (18 ticks), a long scream, settle
    a = m.anim("wail", 2.4)
    a.pos("bone", (0, (0, 0, 0)), (0.85, (0, 5, 3)), (0.95, (0, 4, -3), "linear"), (1.9, (0, 4, -3)), (2.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.85, (-24, 0, 0)), (0.95, (14, 0, 0), "linear"), (1.9, (12, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.85, (-30, 0, 0)), (0.95, (14, 0, 0), "linear"), (1.9, (12, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.85, (25, 0, 0)), (0.95, (60, 0, 0), "linear"), (1.9, (58, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-60, 0, 75)), (0.95, (25, 0, 60), "linear"), (1.9, (30, 0, 64)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-60, 0, -75)), (0.95, (25, 0, -60), "linear"), (1.9, (30, 0, -64)), (2.4, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.85, (-4, 0, 0)), (0.95, (40, 0, 0), "linear"), (1.9, (45, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("veil2", (0, (0, 0, 0)), (0.95, (20, 0, 0)), (1.4, (30, 0, 0)), (1.9, (20, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("skirt3", (0, (0, 0, 0)), (0.95, (14, 0, 0)), (1.9, (16, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("train", (0, (0, 0, 0)), (0.95, (25, 0, 0)), (1.9, (28, 0, 0)), (2.4, (0, 0, 0)))

    # erupt: hands to the face, weeping (0-0.6), arms flung up, claws plunged at the floor (1.0 s / 20 ticks)
    a = m.anim("erupt", 2.0)
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.4, (-62, 0, 14 * sx)), (0.6, (-66, 0, 16 * sx)),
              (0.9, (-175, 0, -20 * sx)), (1.0, (-40, 0, -10 * sx), "linear"), (1.5, (-35, 0, -10 * sx)), (2.0, (0, 0, 0)))
        a.rot(f"forearm_{side}", (0, (0, 0, 0)), (0.4, (-112, 0, 0)), (0.6, (-115, 0, 0)), (0.9, (-10, 0, 0)),
              (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (25, 0, 0)), (0.6, (28, 0, 0)), (0.9, (-25, 0, 0)), (1.0, (20, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.4, (12, 0, 0)), (0.9, (-18, 0, 0)), (1.0, (24, 0, 0), "linear"), (1.5, (20, 0, 0)),
          (2.0, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.9, (0, 5, 0)), (1.0, (0, -3, 0), "linear"), (1.5, (0, -3, 0)), (2.0, (0, 0, 0)))

    # summon: arms spread low, palms up, the head thrown back (0.6 s / 12 ticks), held
    a = m.anim("summon", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 55)), (1.2, (-45, 0, 60)), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-40, 0, -55)), (1.2, (-45, 0, -60)), (1.8, (0, 0, 0)))
    a.rot("hand_r", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (1.2, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("hand_l", (0, (0, 0, 0)), (0.6, (-40, 0, 0)), (1.2, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-35, 0, 0)), (1.2, (-35, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (30, 0, 0)), (1.2, (30, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 4, 0)), (1.2, (0, 4, 0)), (1.8, (0, 0, 0)))

    # veil: arms crossed over the face (0-0.8 s), flung wide in a blinding flash (16 ticks)
    a = m.anim("veil", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-70, 0, -28)), (0.85, (-50, 0, 85), "linear"), (1.3, (-45, 0, 80)), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.75, (-70, 0, 28)), (0.85, (-50, 0, -85), "linear"), (1.3, (-45, 0, -80)), (1.8, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.75, (-105, 0, 0)), (0.85, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.75, (-100, 0, 0)), (0.85, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.75, (20, 0, 0)), (0.85, (-20, 0, 0)), (1.3, (-18, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.75, (-6, 0, 0)), (0.85, (50, 0, 0), "linear"), (1.3, (40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.75, (14, 0, 0)), (0.85, (-14, 0, 0), "linear"), (1.8, (0, 0, 0)))

    # swoop: lean back with both claws drawn (0.7 s / 14 ticks), glide forward claws first, recover
    a = m.anim("swoop", 1.6)
    a.rot("body", (0, (0, 0, 0)), (0.65, (-16, 0, 0)), (0.75, (30, 0, 0), "linear"), (1.1, (28, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (40, 0, 30)), (0.75, (-85, 0, 10), "linear"), (1.1, (-80, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.65, (40, 0, -30)), (0.75, (-85, 0, -10), "linear"), (1.1, (-80, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.65, (10, 0, 0)), (0.75, (-25, 0, 0)), (1.1, (-22, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.75, (35, 0, 0)), (1.1, (30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("skirt3", (0, (0, 0, 0)), (0.75, (30, 0, 0)), (1.1, (32, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("train", (0, (0, 0, 0)), (0.75, (30, 0, 0)), (1.1, (32, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.75, (35, 0, 0)), (1.1, (38, 0, 0)), (1.6, (0, 0, 0)))

    # roar: phase change - she rises, crown blazing, arms wide, a long silent scream
    a = m.anim("roar", 2.6)
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, 7, 0)), (2.0, (0, 7, 0)), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (-18, 0, 0)), (2.0, (-18, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-30, 0, 0)), (2.0, (-30, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.6, (55, 0, 0)), (2.0, (55, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, 95)), (2.0, (-25, 0, 100)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-20, 0, -95)), (2.0, (-25, 0, -100)), (2.6, (0, 0, 0)))
    a.rot("veil", (0, (0, 0, 0)), (0.6, (35, 0, 0)), (2.0, (40, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("skirt3", (0, (0, 0, 0)), (0.6, (-8, 0, 0)), (2.0, (-8, 0, 0)), (2.6, (0, 0, 0)))

    # stagger: posture broken - she sinks, folds forward, arms dangling, head hung
    a = m.anim("stagger", 2.5)
    a.pos("bone", (0, (0, 0, 0)), (0.35, (0, -7, 2)), (2.0, (0, -7, 2)), (2.5, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.35, (32, 0, 6)), (2.0, (30, 0, 6)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.35, (30, 0, -10)), (2.0, (28, 0, -10)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (25, 0, 6)), (2.0, (25, 0, 6)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.35, (30, 0, -4)), (2.0, (30, 0, -4)), (2.5, (0, 0, 0)))
    a.rot("skirt3", (0, (0, 0, 0)), (0.35, (-12, 0, 0)), (2.0, (-12, 0, 0)), (2.5, (0, 0, 0)))
    return m
