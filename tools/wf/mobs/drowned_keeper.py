"""The Drowned Lightkeeper (Le Gardien noyé du phare): the champion of the Leviathan Lighthouse, about 3.4 blocks.

Silhouette idea: the old keeper of the light, drowned in a storm and brought back fused with the great clockwork lens.
A broad, stooped man in a long faded-mustard oilskin coat streaked with weed and salt, a sou'wester hat with its long
back flap, a drowned grey-green face with a white beard dripping kelp and pale glowing eyes. His coat hangs open on a
ribcage of barnacled bone, and in it, for a heart, a brass storm lantern burns amber. On his back, rising behind his
head like a halo, the great Fresnel lens of the lighthouse in its brass ring, turning slowly on its clockwork. In his
right hand a long whaling harpoon with a barbed iron head and a chain wound round its shaft; in his left the curved
jawbone of a whale, worn as a club. Sea boots crusted with barnacles, kelp hanging from his sleeves and hem.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

OIL = (196, 158, 54)            # faded mustard oilskin
OIL_L = (226, 192, 88)
OIL_D = (138, 106, 34)
OIL_DD = (92, 70, 26)
WEED = (64, 96, 58)             # weed and algae streaks
WEED_L = (96, 136, 76)
KELP = (58, 88, 44)
KELP_L = (92, 126, 60)
SKIN = (112, 142, 130)          # drowned grey-green
SKIN_L = (146, 174, 160)
SKIN_D = (72, 98, 92)
BEARD = (214, 220, 212)
BEARD_D = (156, 166, 160)
EYE = (190, 250, 255)
BONE = (226, 216, 190)
BONE_D = (176, 162, 132)
BONE_DD = (120, 108, 88)
RIBDARK = (30, 34, 36)
RUBBER = (34, 34, 38)
RUBBER_L = (64, 64, 70)
BARN = (206, 200, 178)
WOOD = (108, 76, 48)
WOOD_D = (72, 48, 30)
STEEL = (150, 156, 164)
STEEL_L = (204, 210, 218)
STEEL_D = (86, 90, 98)
LAMP = (255, 196, 92)
LAMP_L = (255, 236, 170)
LENS = (170, 222, 226)
LENS_L = (226, 252, 255)


# ---------------------------------------------------------------- paint
def oilskin(seed=0, hem_rows=(), seam_cols=()):
    """Faded oilskin: a waxy sheen in long vertical strokes, weed streaks running down, darker folds at the edges."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return OIL_DD
        if y in hem_rows:
            return OIL_D if (x + y) % 3 else OIL_DD
        if face in ("front", "back") and x in seam_cols:
            return OIL_DD
        r = B.n(x, y, seed)
        streak = B.n(x, 0, seed + 5)
        if streak > 0.82 and y > 1:
            return WEED_L if r > 0.7 else WEED
        c = OIL_L if r > 0.86 else (OIL if r > 0.2 else OIL_D)
        if x in (0, w - 1) and face != "top":
            c = mix(c, OIL_DD, 0.45)
        if y >= h - 2 and face not in ("top", "bottom"):
            c = mix(c, WEED, 0.35)                                                  # the wet, weedy hem
        return c
    return f


def ribs(face, x, y, w, h):
    """The open front of the coat: barnacled ribs of bone over the dark hollow."""
    if face != "front":
        return RIBDARK
    if x == w // 2 or x == w // 2 - 1:
        return BONE_D if y % 2 else BONE_DD                                         # the breastbone
    if y % 3 == 0:
        return BONE if B.n(x, y, 3) > 0.25 else BARN
    return RIBDARK if B.n(x, y, 4) > 0.2 else WEED


def lantern(face, x, y, w, h):
    """The storm lantern in his chest: a brass frame round amber glass."""
    if face in ("top", "bottom") or x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if (x + y) % 2 == 0 else B.BRASS_D
    return LAMP_L if (x, y) == (w // 2, h // 2) else LAMP


def lantern_glow(face, x, y, w, h):
    if face in ("top", "bottom") or x in (0, w - 1) or y in (0, h - 1):
        return None
    return LAMP_L


def face(face_, x, y, w, h):
    """The drowned face (8 x 9): a heavy brow, deep sockets with pale glowing eyes, a broken nose, hollow cheeks
    and the beard (its own cube) below; weed in the hair at the sides."""
    if face_ == "top":
        return KELP
    if face_ == "front":
        if y == 2 and 1 <= x <= 6:
            return SKIN_D                                                           # the brow
        if y == 3 and x in (1, 2, 5, 6):
            return EYE if x in (2, 5) else RIBDARK                                  # sockets and eyes
        if y in (4, 5) and x in (3, 4):
            return SKIN_L if y == 4 else SKIN
        if y == 5 and x in (1, 6):
            return SKIN_D                                                           # hollow cheeks
        if y == 0:
            return BEARD_D                                                          # lank white hair
    if face_ in ("left", "right") and y < 4:
        return BEARD_D if (x + y) % 2 else KELP
    r = B.n(x, y, 41)
    return SKIN_L if r > 0.86 else (SKIN if r > 0.18 else SKIN_D)


def face_glow(face_, x, y, w, h):
    if face_ == "front" and y == 3 and x in (2, 5):
        return EYE
    return None


def beard(face, x, y, w, h):
    """A long white beard, matted, kelp threaded through it."""
    if face == "front" and y == h - 1 and x % 2:
        return None
    if B.n(x, y, 51) > 0.93:
        return KELP_L
    return BEARD if (x + y) % 3 else BEARD_D


def sou_wester(face, x, y, w, h):
    """The sou'wester: oilskin with a stitched brim edge."""
    if face == "bottom":
        return OIL_DD
    if face != "top" and y == h - 1:
        return OIL_DD
    r = B.n(x, y, 61)
    return OIL_L if r > 0.85 else (OIL if r > 0.2 else OIL_D)


def boot(face, x, y, w, h):
    """Rubber sea boots crusted with barnacles."""
    if face == "bottom":
        return RUBBER
    if B.n(x, y, 71) > 0.93:
        return BARN
    return RUBBER_L if (face == "front" and x == 1) else RUBBER


def trousers(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        return OIL_D if r > 0.3 else OIL_DD
    return f


def hand(face, x, y, w, h):
    r = B.n(x, y, 81)
    return SKIN if r > 0.25 else SKIN_D


def kelp(face, x, y, w, h):
    if y == h - 1 and x % 2:
        return None
    return KELP_L if (x + y) % 3 == 0 else KELP


def shaft(face, x, y, w, h):
    """The harpoon's ash shaft, a chain wound round it every few texels."""
    if y % 9 in (3, 4):
        return STEEL_D if (x + y) % 2 else STEEL
    return WOOD if (y + x) % 4 else WOOD_D


def iron_head(face, x, y, w, h):
    if face == "top" or y == 0:
        return STEEL_L
    return STEEL if (x + y) % 2 else STEEL_D


def jawbone(seed=0):
    """Bleached whale jawbone: long grain, barnacles near the end."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BONE_D
        r = B.n(x, y, seed)
        if r > 0.9:
            return BARN
        if x in (0, w - 1):
            return BONE_D
        return BONE if (y + r * 3) % 5 > 1 else BONE_D
    return f


def lens(face, x, y, w, h):
    """The great Fresnel lens seen face on (front and back): a brass ring, concentric glass prisms inside, a bullseye
    in the middle; the corners are cut away so it reads as a disc."""
    if face not in ("front", "back"):
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = math.hypot(x - cx, y - cy)
    rr = w / 2
    if d > rr:
        return None
    if d > rr - 1.6:
        return B.BRASS_L if (x + y) % 3 == 0 else B.BRASS
    if d < 1.6:
        return LENS_L
    ring = int(d) % 2
    return LENS if ring else mix(LENS, B.BRASS_D, 0.35)


def lens_glow(face, x, y, w, h):
    if face != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = math.hypot(x - cx, y - cy)
    rr = w / 2
    if d > rr - 1.6:
        return None
    if d < 1.6:
        return LENS_L
    return (200, 244, 248) if int(d) % 2 else None


def lens_frame(face, x, y, w, h):
    """The clockwork drive behind the lens: dark iron with brass teeth."""
    if face in ("front", "back"):
        return B.cog(teeth=8)(face, x, y, w, h)
    return B.BRASS_D


def chain(face, x, y, w, h):
    return STEEL if (y + x) % 2 else STEEL_D


# ---------------------------------------------------------------- build
def build():
    m = Model("drowned_keeper", seed=1409, shadow=1.0, walk_speed=0.7, walk_scale=0.75, glow_pulse=0.07)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -21, 0))
    m.part("skirt_f", "hips", pivot=(0, 0, -3.5), rot=(-4, 0, 0))
    m.part("skirt_b", "hips", pivot=(0, 0, 3.5), rot=(6, 0, 0))
    m.part("chest", "hips", pivot=(0, -3, 0), rot=(8, 0, 0))
    m.part("lens", "chest", pivot=(0, -18, 5.5))
    m.part("heart", "chest", pivot=(0, -9, -4))
    m.part("head", "chest", pivot=(0, -16, -1), rot=(-6, 0, 0))
    m.part("hat", "head", pivot=(0, -8, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(2.8 * sx, -21, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 10, 0))
    m.part("arm_r", "chest", pivot=(-8, -14, 0), rot=(-6, 0, 4))
    m.part("fore_r", "arm_r", pivot=(0, 9, 0), rot=(-30, 0, 0))
    m.part("harpoon", "fore_r", pivot=(0, 9.5, 0), rot=(36, 0, 0))
    m.part("arm_l", "chest", pivot=(8, -14, 0), rot=(-4, 0, -6))
    m.part("fore_l", "arm_l", pivot=(0, 9, 0), rot=(-20, 0, 0))
    m.part("jaw", "fore_l", pivot=(0, 10, 0), rot=(14, 0, 0))

    # ---- legs: oilskin trousers into barnacled sea boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2.5, -1, -2.5, 5, 11, 5, trousers(10 + sx))
        m.box(shin, -2.5, 0, -2.5, 5, 6, 5, trousers(12 + sx), grow=-0.2)
        m.box(shin, -2.75, 4, -2.75, 5, 7, 5, boot, grow=0.25)
        m.box(shin, -2.5, 9, -4.5, 5, 2, 7, boot)

    # ---- hips and the long coat skirts (front flaps open over the legs, the back panel to the knees)
    m.box("hips", -6, -3, -3.5, 12, 4, 7, oilskin(20))
    m.box("skirt_f", -6, 0, -0.5, 4, 12, 1, oilskin(21, hem_rows=(11,)))
    m.box("skirt_f", 2, 0, -0.5, 4, 12, 1, oilskin(22, hem_rows=(11,)))
    m.box("skirt_b", -6, 0, -0.5, 12, 13, 1, oilskin(23, hem_rows=(12,), seam_cols=(6,)))
    m.box("skirt_f", -5, 12, -0.5, 1, 4, 1, kelp)                                  # kelp from the hem
    m.box("skirt_b", 3, 13, -0.5, 1, 3, 1, kelp)

    # ---- the chest: the open oilskin coat over a barnacled ribcage, a high collar, the shoulder capes
    m.box("chest", -6.5, -15, -3.5, 13, 15, 7, oilskin(24))
    m.box("chest", -3, -14, -3.9, 6, 12, 1, ribs)
    m.box("chest", -6.5, -14, -4.2, 3, 14, 1, oilskin(25))                         # the coat's front edges
    m.box("chest", 3.5, -14, -4.2, 3, 14, 1, oilskin(26))
    m.box("chest", -5, -17, -3.5, 10, 2, 6, oilskin(27))                           # the turned-up collar
    m.box("chest", -8.5, -16, -4, 17, 3, 8, oilskin(28, hem_rows=(2,)))            # the shoulder cape
    m.box("chest", -1.5, -6, 3.5, 3, 4, 2, B.iron(29))                             # the lens mount's spine
    m.box("chest", -2, -17, 3.5, 4, 11, 2, B.iron(30))

    # ---- the heart: a brass storm lantern burning in the ribs
    m.box("heart", -2.5, -3, -1.6, 5, 6, 3, lantern, glow=lantern_glow)
    m.box("heart", -1.5, -4, -1.1, 3, 1, 2, B.BRASS_D)                               # its cap and ring
    m.box("heart", -0.5, -5, -0.7, 1, 1, 1, B.BRASS_L)

    # ---- the great lens on his back, turning on its clockwork drive
    m.box("lens", -3, -3, -0.5, 6, 6, 1, lens_frame)
    m.box("lens", -10, -10, 1, 20, 20, 1, lens, glow=lens_glow)
    m.box("lens", -1.5, -1.5, 0.5, 3, 3, 1, B.BRASS_L)

    # ---- the head: the drowned face, beard and sou'wester
    m.box("head", -4, -8, -4, 8, 8, 8, face, glow=face_glow)
    m.box("head", -4, -2, -4.6, 8, 7, 1, beard)
    m.box("head", -3, 5, -4.6, 6, 3, 1, beard)
    m.box("hat", -6, -1, -6, 12, 1, 12, sou_wester)                                # the brim
    m.box("hat", -5, -1, 5.5, 10, 1, 4, sou_wester)                                # the long back flap
    m.box("hat", -4.5, -4, -4.5, 9, 3, 9, sou_wester)                              # the crown
    m.box("hat", -3, -5, -3, 6, 1, 6, sou_wester)

    # ---- arms: oilskin sleeves, drowned hands, kelp trailing
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -2, -1, -2, 4, 10, 4, oilskin(50 + sx))
        m.box(fore, -2, 0, -2, 4, 7, 4, oilskin(52 + sx, hem_rows=(6,)), grow=0.2)
        m.box(fore, -1.5, 7, -1.5, 3, 3, 3, hand)
        m.box(fore, 1.5 * sx, 3, -0.5, 1, 6, 1, kelp)

    # ---- the whaling harpoon in the right hand: ash shaft, chain wound on, a barbed iron head on top
    m.box("harpoon", -0.5, -20, -0.5, 1, 32, 1, shaft)
    m.box("harpoon", -1, -25, -1, 2, 5, 2, iron_head)
    m.box("harpoon", -0.5, -27, -0.5, 1, 2, 1, STEEL_L)
    m.box("harpoon", -2.5, -22, -0.5, 1, 3, 1, iron_head)                          # the barbs
    m.box("harpoon", 1.5, -22, -0.5, 1, 3, 1, iron_head)
    m.box("harpoon", -1, -2, -1, 2, 4, 2, chain)                                   # the chain's coil at the grip

    # ---- the whale's jawbone in the left hand, curving forward down to its knob
    m.box("jaw", -1.5, -1, -1.5, 3, 5, 3, jawbone(90))
    m.box("jaw", -2, 4, -2.5, 4, 7, 4, jawbone(91))
    m.box("jaw", -2.5, 10, -3.5, 5, 6, 5, jawbone(92))
    m.box("jaw", -2, 15, -4.5, 4, 3, 4, jawbone(93))

    _anims(m)
    return m


def _abs(m, a):
    """Write rotation keys as absolute poses: the part's rest rotation is taken off (keyframes add to it)."""
    orig = a.rot

    def rot(part, *keys):
        r = m.parts[part].rot
        return orig(part, *[(k[0], tuple(k[1][i] - r[i] for i in range(3))) + tuple(k[2:]) for k in keys])
    a.rot = rot
    return a


def _anims(m):
    REST = {"arm_r": (-6, 0, 4), "fore_r": (-30, 0, 0), "harpoon": (36, 0, 0), "arm_l": (-4, 0, -6),
            "fore_l": (-20, 0, 0), "jaw": (14, 0, 0), "chest": (8, 0, 0), "head": (-6, 0, 0),
            "skirt_f": (-4, 0, 0), "skirt_b": (6, 0, 0)}

    idle = _abs(m, m.anim("idle", 3.0))
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, -0.5, 0)), (3.0, (0, 0, 0)))
    idle.rot("chest", (0, REST["chest"]), (1.5, (10, 0, 0)), (3.0, REST["chest"]))
    idle.rot("head", (0, REST["head"]), (1.5, (-2, -8, -3)), (3.0, REST["head"]))
    idle.rot("lens", (0, (0, 0, 0)), (3.0, (0, 0, 360), "linear"))                 # the lens turns on its clockwork
    idle.scale("heart", (0, (1, 1, 1)), (0.4, (1.12, 1.12, 1.12)), (0.8, (1, 1, 1)), (3.0, (1, 1, 1)))
    idle.rot("skirt_b", (0, REST["skirt_b"]), (1.5, (9, 0, 0)), (3.0, REST["skirt_b"]))

    walk = _abs(m, m.anim("walk", 2.2))
    walk.rot("leg_r", (0, (22, 0, 0)), (1.1, (-22, 0, 0)), (2.2, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.1, (22, 0, 0)), (2.2, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.55, (22, 0, 0)), (1.1, (0, 0, 0)), (2.2, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.65, (22, 0, 0)), (2.2, (0, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, -6)), (1.1, (-18, 0, -6)), (2.2, (10, 0, -6)))
    walk.rot("arm_r", (0, (-12, 0, 4)), (1.1, (0, 0, 4)), (2.2, (-12, 0, 4)))
    walk.rot("skirt_f", (0, (-10, 0, 0)), (0.55, (-18, 0, 0)), (1.1, (-10, 0, 0)), (1.65, (-18, 0, 0)), (2.2, (-10, 0, 0)))
    walk.rot("skirt_b", (0, (12, 0, 0)), (0.55, (18, 0, 0)), (1.1, (12, 0, 0)), (1.65, (18, 0, 0)), (2.2, (12, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.55, (0, -0.8, 0)), (1.1, (0, 0, 0)), (1.65, (0, -0.8, 0)), (2.2, (0, 0, 0)))
    walk.rot("lens", (0, (0, 0, 0)), (2.2, (0, 0, 180), "linear"))

    # thrust (14 / 6 / 14): he draws the harpoon back level at his hip, the barbs toward you (0.7 s), and drives it
    # straight ahead at 0.7 s, leaning into it; then he hauls it back
    a = _abs(m, m.anim("thrust", 1.7))
    a.rot("arm_r", (0, REST["arm_r"]), (0.6, (-60, 30, 10)), (0.7, (-62, 32, 10)), (0.76, (-88, 0, 0), "linear"),
          (1.0, (-86, 0, 0)), (1.7, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.6, (-30, 0, 0)), (0.76, (0, 0, 0), "linear"), (1.0, (0, 0, 0)),
          (1.7, REST["fore_r"]))
    a.rot("harpoon", (0, REST["harpoon"]), (0.6, (180, 0, 0)), (0.76, (178, 0, 0)), (1.0, (178, 0, 0)),
          (1.7, REST["harpoon"]))
    a.pos("harpoon", (0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.7, (0, 6, 0)), (0.76, (0, -4, 0), "linear"),
          (1.0, (0, -4, 0)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, REST["chest"]), (0.6, (4, 28, 0)), (0.76, (20, -16, 0), "linear"), (1.0, (18, -12, 0)),
          (1.7, REST["chest"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.6, (-30, 0, -20)), (0.76, (10, 0, -20)), (1.7, REST["arm_l"]))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (0.76, (-24, 0, 0), "linear"), (1.0, (-24, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (0.76, (16, 0, 0), "linear"), (1.0, (16, 0, 0)), (1.7, (0, 0, 0)))

    # throw (18 / 20 / 14): he lifts the harpoon over his shoulder, the chain paying out from his left fist (0.9 s),
    # hurls it at 0.9 s (the harpoon leaves his hand), then hauls the chain in hand over hand and catches it at 1.9 s
    a = _abs(m, m.anim("throw", 2.6))
    a.rot("arm_r", (0, REST["arm_r"]), (0.8, (-160, 0, 20)), (0.9, (-164, 0, 22)), (0.96, (-70, 0, 0), "linear"),
          (1.2, (-50, 0, 0)), (1.45, (-80, 0, 0)), (1.7, (-40, 0, 0)), (1.9, (-70, 0, 0)), (2.6, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.8, (-50, 0, 0)), (0.96, (0, 0, 0), "linear"), (1.9, (-20, 0, 0)),
          (2.6, REST["fore_r"]))
    a.rot("harpoon", (0, REST["harpoon"]), (0.8, (120, 0, 0)), (0.9, (124, 0, 0)), (2.6, (124, 0, 0)))
    a.scale("harpoon", (0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.93, (0, 0, 0), "linear"), (1.86, (0, 0, 0)),
            (1.9, (1, 1, 1), "linear"), (2.6, (1, 1, 1)))
    a.rot("arm_l", (0, REST["arm_l"]), (0.8, (-70, 0, -10)), (1.2, (-60, 0, 0)), (1.45, (-30, 0, 0)),
          (1.7, (-70, 0, 0)), (1.9, (-40, 0, 0)), (2.6, REST["arm_l"]))
    a.rot("chest", (0, REST["chest"]), (0.8, (-6, 30, 0)), (0.96, (22, -14, 0), "linear"), (1.9, (14, 0, 0)),
          (2.6, REST["chest"]))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (16, 0, 0)), (0.96, (-20, 0, 0), "linear"), (2.0, (-10, 0, 0)), (2.6, (0, 0, 0)))

    # whirl (18 / 16 / 14): he swings the harpoon low on its chain, winding up (0.9 s), then whirls it round himself
    # once at ankle-to-knee height (0.9-1.7 s) and catches it back
    a = _abs(m, m.anim("whirl", 2.4))
    a.rot("arm_r", (0, REST["arm_r"]), (0.8, (-50, 0, 70)), (0.9, (-50, 0, 74)), (1.7, (-50, 0, 74)),
          (2.4, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.9, (0, 0, 0)), (1.7, (0, 0, 0)), (2.4, REST["fore_r"]))
    a.rot("harpoon", (0, REST["harpoon"]), (0.9, (90, 0, 0)), (1.7, (90, 0, 0)), (2.4, REST["harpoon"]))
    a.scale("harpoon", (0, (1, 1, 1)), (0.9, (1, 1.6, 1)), (1.7, (1, 1.6, 1)), (2.1, (1, 1, 1)), (2.4, (1, 1, 1)))
    a.rot("bone", (0, (0, 0, 0)), (0.8, (0, 40, 0)), (0.9, (0, 44, 0)), (1.7, (0, -316, 0), "linear"),
          (2.4, (0, -360, 0)))
    a.rot("chest", (0, REST["chest"]), (0.9, (20, 0, 0)), (1.7, (20, 0, 0)), (2.4, REST["chest"]))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -2, 0)), (1.7, (0, -2, 0)), (2.4, (0, 0, 0)))
    a.rot("skirt_b", (0, REST["skirt_b"]), (0.9, (40, 0, 0)), (1.7, (40, 0, 0)), (2.4, REST["skirt_b"]))
    a.rot("skirt_f", (0, REST["skirt_f"]), (0.9, (-34, 0, 0)), (1.7, (-34, 0, 0)), (2.4, REST["skirt_f"]))

    # sweep (24 / 40 / 16): he plants the harpoon and raises his left arm to the great lamp; the lens on his back
    # spins up and his lantern heart blazes (1.2 s); from 1.2 s the lamp's beam sweeps half the room for 2 s while he
    # turns slowly with it, arm high
    a = _abs(m, m.anim("sweep", 4.0))
    a.rot("arm_l", (0, REST["arm_l"]), (1.1, (-170, 0, -10)), (1.2, (-172, 0, -12)), (3.2, (-166, 0, -14)),
          (4.0, REST["arm_l"]))
    a.rot("fore_l", (0, REST["fore_l"]), (1.2, (0, 0, 0)), (3.2, (0, 0, 0)), (4.0, REST["fore_l"]))
    a.rot("arm_r", (0, REST["arm_r"]), (1.2, (-30, 0, 10)), (3.2, (-30, 0, 10)), (4.0, REST["arm_r"]))
    a.rot("harpoon", (0, REST["harpoon"]), (1.2, (66, 0, 0)), (3.2, (66, 0, 0)), (4.0, REST["harpoon"]))
    a.rot("head", (0, REST["head"]), (1.2, (-34, 0, 0)), (3.2, (-30, 0, 0)), (4.0, REST["head"]))
    a.rot("chest", (0, REST["chest"]), (1.2, (-8, 0, 0)), (3.2, (-6, 0, 0)), (4.0, REST["chest"]))
    a.rot("lens", (0, (0, 0, 0)), (1.2, (0, 0, 540)), (3.2, (0, 0, 1260), "linear"), (4.0, (0, 0, 1440)))
    a.scale("heart", (0, (1, 1, 1)), (1.2, (1.4, 1.4, 1.4)), (3.2, (1.4, 1.4, 1.4)), (4.0, (1, 1, 1)))

    # surge (phase 2, 22 / 40 / 16): he raises the jawbone and the harpoon high and calls the storm (1.1 s), then
    # smashes both down on the deck at 1.1 s: the sea rolls in, wave after wave, while he holds them down
    a = _abs(m, m.anim("surge", 3.9))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.0, (-170, 0, 16 * sz)), (1.1, (-172, 0, 16 * sz)),
              (1.2, (-50, 0, 10 * sz), "linear"), (3.1, (-48, 0, 10 * sz)), (3.9, REST[f"arm_{s}"]))
        a.rot(f"fore_{s}", (0, REST[f"fore_{s}"]), (1.1, (0, 0, 0)), (1.2, (-10, 0, 0)), (3.1, (-10, 0, 0)),
              (3.9, REST[f"fore_{s}"]))
    a.rot("harpoon", (0, REST["harpoon"]), (1.1, (20, 0, 0)), (1.2, (70, 0, 0)), (3.1, (70, 0, 0)),
          (3.9, REST["harpoon"]))
    a.rot("chest", (0, REST["chest"]), (1.1, (-14, 0, 0)), (1.2, (34, 0, 0), "linear"), (3.1, (30, 0, 0)),
          (3.9, REST["chest"]))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (0, -3, 0), "linear"), (3.1, (0, -3, 0)), (3.9, (0, 0, 0)))
    a.rot("head", (0, REST["head"]), (1.1, (-30, 0, 0)), (1.2, (10, 0, 0)), (3.9, REST["head"]))

    # call (phase 2, 20 / 10 / 16): he swings his lantern heart's light over the floor like a signal lamp, beckoning
    # with the jawbone (1.0 s); at 1.0 s the drowned crew climbs in
    a = _abs(m, m.anim("call", 2.3))
    a.rot("arm_l", (0, REST["arm_l"]), (0.4, (-100, 0, -40)), (0.7, (-100, 0, 20)), (1.0, (-110, 0, -30)),
          (1.1, (-60, 0, -10)), (2.3, REST["arm_l"]))
    a.rot("chest", (0, REST["chest"]), (0.4, (4, 20, 0)), (0.7, (4, -20, 0)), (1.0, (-10, 0, 0)), (1.3, (14, 0, 0)),
          (2.3, REST["chest"]))
    a.rot("head", (0, REST["head"]), (1.0, (-24, 0, 0)), (1.3, (0, 0, 0)), (2.3, REST["head"]))
    a.scale("heart", (0, (1, 1, 1)), (0.5, (1.3, 1.3, 1.3)), (1.0, (1.5, 1.5, 1.5)), (1.3, (1, 1, 1)),
            (2.3, (1, 1, 1)))

    # overload (phase 3, 40 / 20 / 20): the lens tears itself up off his back and blazes over his head while he
    # sags, arms out, the lantern heart flaring (2.0 s); at 2.0 s he throws his head back: the Lamp Overload
    a = _abs(m, m.anim("overload", 4.0))
    a.pos("lens", (0, (0, 0, 0)), (1.6, (0, 8, -4)), (2.0, (0, 10, -5)), (3.2, (0, 10, -5)), (4.0, (0, 0, 0)))
    a.rot("lens", (0, (0, 0, 0)), (2.0, (-70, 0, 1080)), (3.2, (-70, 0, 1800)), (4.0, (0, 0, 2160)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.9, (-30, 0, 70 * sz)), (2.0, (-32, 0, 72 * sz)),
              (2.06, (-100, 0, 40 * sz), "linear"), (3.2, (-96, 0, 40 * sz)), (4.0, REST[f"arm_{s}"]))
    a.rot("head", (0, REST["head"]), (1.9, (16, 0, 0)), (2.0, (14, 0, 0)), (2.06, (-36, 0, 0), "linear"),
          (3.2, (-30, 0, 0)), (4.0, REST["head"]))
    a.rot("chest", (0, REST["chest"]), (1.9, (26, 0, 0)), (2.06, (-14, 0, 0), "linear"), (3.2, (-10, 0, 0)),
          (4.0, REST["chest"]))
    a.scale("heart", (0, (1, 1, 1)), (1.9, (1.5, 1.5, 1.5)), (2.06, (1.9, 1.9, 1.9), "linear"), (3.2, (1.5, 1.5, 1.5)),
            (4.0, (1, 1, 1)))

    # slam (phase 3, 22 / 10 / 18): he heaves the whale's jawbone up over his head with both hands (1.1 s) and brings
    # it down on the deck in front of him at 1.1 s, staying bent over it, then wrenches it free
    a = _abs(m, m.anim("slam", 2.5))
    a.rot("arm_l", (0, REST["arm_l"]), (1.0, (-176, 0, -4)), (1.1, (-178, 0, -4)), (1.16, (-70, 0, 0), "linear"),
          (1.7, (-66, 0, 0)), (2.5, REST["arm_l"]))
    a.rot("fore_l", (0, REST["fore_l"]), (1.1, (-10, 0, 0)), (1.16, (0, 0, 0)), (2.5, REST["fore_l"]))
    a.rot("jaw", (0, REST["jaw"]), (1.1, (40, 0, 0)), (1.16, (20, 0, 0)), (1.7, (20, 0, 0)), (2.5, REST["jaw"]))
    a.rot("arm_r", (0, REST["arm_r"]), (1.0, (-150, 0, 30)), (1.1, (-152, 0, 30)), (1.16, (-60, 0, 10), "linear"),
          (1.7, (-56, 0, 10)), (2.5, REST["arm_r"]))
    a.rot("chest", (0, REST["chest"]), (1.0, (-16, 0, 0)), (1.1, (-18, 0, 0)), (1.16, (40, 0, 0), "linear"),
          (1.7, (38, 0, 0)), (2.5, REST["chest"]))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 1, 0)), (1.16, (0, -3, 0), "linear"), (1.7, (0, -3, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.1, (-10, 0, 0)), (1.16, (-30, 0, 0), "linear"), (1.7, (-30, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.16, (20, 0, 0), "linear"), (1.7, (20, 0, 0)), (2.5, (0, 0, 0)))

    # roar (phase two): he throws his arms wide and his head back, the lantern flaring, the lens spinning
    a = _abs(m, m.anim("roar", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.5, (-30, 0, 90)), (1.6, (-32, 0, 92)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.5, (-30, 0, -90)), (1.6, (-32, 0, -92)), (2.0, REST["arm_l"]))
    a.rot("head", (0, REST["head"]), (0.5, (-36, 0, 0)), (1.6, (-34, 0, 0)), (2.0, REST["head"]))
    a.rot("chest", (0, REST["chest"]), (0.5, (-12, 0, 0)), (1.6, (-10, 0, 0)), (2.0, REST["chest"]))
    a.rot("lens", (0, (0, 0, 0)), (2.0, (0, 0, 720)))
    a.scale("heart", (0, (1, 1, 1)), (0.5, (1.5, 1.5, 1.5)), (1.6, (1.5, 1.5, 1.5)), (2.0, (1, 1, 1)))

    # stagger: the lantern gutters, he sinks onto one knee leaning on the harpoon, head bowed, the lens stalled
    a = _abs(m, m.anim("stagger", 2.0))
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, REST["chest"]), (0.3, (34, 0, 6)), (1.6, (36, 0, 6)), (2.0, REST["chest"]))
    a.rot("head", (0, REST["head"]), (0.3, (30, 0, -12)), (1.6, (30, 0, -12)), (2.0, REST["head"]))
    a.rot("arm_r", (0, REST["arm_r"]), (0.3, (-40, 0, 10)), (1.6, (-40, 0, 10)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (10, 0, -10)), (1.6, (10, 0, -10)), (2.0, REST["arm_l"]))
    a.scale("heart", (0, (1, 1, 1)), (0.3, (0.7, 0.7, 0.7)), (1.6, (0.7, 0.7, 0.7)), (2.0, (1, 1, 1)))
