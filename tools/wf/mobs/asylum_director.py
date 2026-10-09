"""The Asylum Director (La Directrice de l'asile): the champion of the Clockwork Asylum, about 3.6 blocks tall.

Silhouette idea: a tall, thin surgeon in a long stained white coat, with four spindly brass surgical arms spread from
her back like a spider's legs (a scalpel and a bone saw high, forceps and a syringe low). Long legs in dark trousers
and buttoned boots show under the coat, which is open below the belt and split into tails at the back. Her face is
hidden by a brass plague-doctor mask: a long curved beak, two round green lenses that glow, rivets; a white surgical
cap over grey hair in a bun, and a head mirror strapped to her brow. A high starched collar and a black cravat. In her
chest a glass plate set in brass shows a clockwork heart ticking (red-amber glow). Black rubber gloves with long
fingers; from her LEFT hand a brass pocket watch dangles on its chain; her RIGHT hand is free (it conducts the arms).
On her back a brass harness with a turning cog carries the four arms.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

COAT = (226, 222, 206)          # stained white coat
COAT_L = (244, 242, 232)
COAT_D = (184, 180, 164)
COAT_DD = (140, 134, 118)
STAIN = (128, 70, 52)           # old rust-brown stains
STAIN_D = (92, 46, 36)
OIL = (86, 80, 66)
TROUS = (52, 50, 58)
TROUS_D = (34, 32, 40)
BOOT = (30, 26, 28)
BOOT_L = (64, 56, 58)
GLOVE = (28, 30, 34)
GLOVE_L = (70, 76, 84)
SKIN = (214, 200, 190)          # pale
HAIR = (150, 148, 150)
HAIR_D = (104, 102, 108)
GREEN = (120, 236, 150)         # the lenses, the syringe's serum
GREEN_L = (220, 255, 226)
GREEN_D = (50, 140, 80)
HEART = (236, 80, 60)
HEART_L = (255, 190, 120)
STEEL = (196, 202, 210)
STEEL_L = (240, 244, 250)
STEEL_D = (120, 126, 136)
BLACK = (22, 20, 24)


# ---------------------------------------------------------------- paint
def coat(seed=0, open_front=0, hem=True, buttons=False):
    """The long white coat: faint vertical folds, greyer toward the hem, old rust-brown stains and oil smears; with
    ``open_front`` the front parts in the middle (``open_front`` texels) to show the trousers."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return COAT_DD
        if face == "top":
            return COAT_L if (x + y) % 4 == 0 else COAT
        if open_front and face == "front":
            mid = (w - 1) / 2
            if abs(x - mid) < open_front / 2:
                return TROUS_D if y > 0 else COAT_D
            if abs(x - mid) < open_front / 2 + 1:
                return COAT_D                                                          # the coat's front edges
        fold = (x + int(B.n(x // 2, 1, seed) * 2)) % 4
        c = (COAT_L, COAT, COAT, COAT_D)[fold]
        c = mul(c, 1.03 - 0.16 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.05)
        if buttons and face == "front" and x == w // 2 and y % 4 == 1:
            return B.BRASS_L
        if hem and y == h - 1:
            return COAT_DD
        r = B.n(x // 2, y // 2, seed + 11)
        if r < 0.07:
            return STAIN if B.n(x, y, seed + 3) > 0.35 else STAIN_D                    # dried stains
        if r > 0.95 and y > h // 2:
            return mix(c, OIL, 0.6)                                                    # oil smears low down
        if y > h - 4 and B.n(x, y, seed + 5) < 0.25:
            return mix(c, STAIN, 0.35)                                                 # a dirty hem
        return c
    return f


def torso_paint(face, x, y, w, h):
    """The coat's bodice: lapels in a V, brass buttons down the right side of the opening, a breast pocket with the
    watch chain's fob; the glass plate covers the middle (painted dark, the heart sits in front)."""
    if face == "front":
        mid = (w - 1) / 2
        if 3 <= y <= 9 and abs(x - mid) <= 2:
            return BLACK                                                               # the cavity behind the glass
        d = abs(x - mid) - (h - 1 - y) * 0.0
        if y <= 2 and abs(x - mid) <= 1:
            return BLACK                                                               # the cravat
        if y < 12 and abs(abs(x - mid) - (1.0 + y * 0.25)) < 0.6:
            return COAT_D                                                              # the lapel edges
        if y >= 12 and x == int(mid) + 1 and y % 3 == 0:
            return B.BRASS_L                                                           # buttons
        if x == w - 2 and y == 11:
            return B.BRASS                                                             # the fob in the pocket
    return coat(31, hem=False)(face, x, y, w, h)


def frame(face, x, y, w, h):
    """The glass chest plate: a brass frame, clear glass (cut out) with a few glints and a cross-bar of rivets."""
    if face in ("front", "back"):
        if x in (0, w - 1) or y in (0, h - 1):
            if (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
                return B.BRASS_D
            return B.BRASS_L if y == 0 else B.BRASS
        if face == "front" and (x + y) == 3:
            return (220, 240, 240, 180)                                                # a glint on the glass
        return None
    return B.BRASS_D


def heart(face, x, y, w, h):
    if face in ("front", "back"):
        if B.cog_mask(x, y, w, h, teeth=6, hub=0.0):
            return HEART if (x + y) % 2 else HEART_L
        return None
    return mul(HEART, 0.6)


def heart_glow(face, x, y, w, h):
    if face in ("front", "back") and B.cog_mask(x, y, w, h, teeth=6, hub=0.0):
        return HEART_L if (x, y) == (w // 2, h // 2) else HEART
    return None


def trousers(face, x, y, w, h):
    if face in ("top", "bottom"):
        return TROUS_D
    c = TROUS if (x + y // 3) % 3 else TROUS_D
    return mul(c, 1.0 + (B.n(x, y, 41) - 0.5) * 0.08)


def boot(face, x, y, w, h):
    """Buttoned boots: black leather, a row of brass buttons up the outside, a lit toe."""
    if face == "bottom":
        return BLACK
    if face == "top":
        return BOOT_L
    if face in ("left", "right") and x == w // 2 and y % 2 == 0 and y < h - 1:
        return B.BRASS
    if y == h - 1:
        return BLACK
    return BOOT_L if (face == "front" and y >= h - 2) else BOOT


def glove(face, x, y, w, h):
    if face == "top":
        return GLOVE_L
    return GLOVE_L if (x == 0 and face == "front") or B.n(x, y, 51) > 0.86 else GLOVE


def sleeve(seed=0, cuff=True):
    def f(face, x, y, w, h):
        if face == "bottom":
            return GLOVE
        if cuff and y >= h - 2 and face != "top":
            return COAT_L if y == h - 2 else B.BRASS
        return coat(seed, hem=False)(face, x, y, w, h)
    return f


def mask(face, x, y, w, h):
    """The brass mask plate over her face: riveted, darker round the lens sockets, a vent grille under them."""
    plate = B.brass(61, grad=0.3)
    if face == "front":
        if y == h - 1 and x % 2 == 0:
            return B.IRON                                                              # the vent
        if (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            return B.BRASS_L
    return plate(face, x, y, w, h)


def lens(face, x, y, w, h):
    if face == "front":
        if (x, y) == (0, 0):
            return GREEN_L
        return GREEN
    return B.BRASS_D


def lens_glow(face, x, y, w, h):
    if face == "front":
        return GREEN_L if (x, y) == (0, 0) else GREEN
    return None


def beak(face, x, y, w, h):
    """The plague-doctor beak: brass banded with darker seams, a bright ridge on top."""
    if face == "top":
        return B.BRASS_L if x == w // 2 else B.BRASS
    if face == "bottom":
        return B.BRASS_D
    if (y if face in ("left", "right") else 0) == 0 and face in ("left", "right") and x % 3 == 0:
        return B.BRASS_L
    if face in ("left", "right") and x % 3 == 2:
        return B.BRASS_D                                                               # seams round the beak
    return mul(B.BRASS, 1.0 + (B.n(x, y, 62) - 0.5) * 0.1)


def cap(face, x, y, w, h):
    """The white surgical cap, gathered at the back."""
    if face == "bottom":
        return HAIR_D
    if face == "top":
        return COAT_L if (x + y) % 3 else COAT
    if y == h - 1:
        return COAT_D
    return COAT if (x + y) % 4 else COAT_D


def head_paint(face, x, y, w, h):
    """Her head behind the mask: grey hair drawn back under the cap, pale skin at the sides, a strap of the mask."""
    if face == "front":
        return SKIN if y >= h - 2 else HAIR_D
    if face in ("left", "right"):
        if y == 3:
            return B.LEATHER                                                           # the mask's strap
        if y >= 4 and x >= w // 2:
            return SKIN
        return HAIR if (x + y) % 3 else HAIR_D
    if face == "back":
        return B.LEATHER if y == 3 else (HAIR if (x + y) % 3 else HAIR_D)
    return HAIR_D


def hair(face, x, y, w, h):
    return HAIR if (x + 2 * y) % 3 else HAIR_D


def mirror(face, x, y, w, h):
    """The head mirror: a polished steel disc with a hole in the middle."""
    if face == "front":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = math.hypot(x - cx, y - cy)
        if r < 0.5:
            return BLACK
        return STEEL_L if x < cx else STEEL
    return STEEL_D


def steel(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return STEEL_L
        if face == "bottom":
            return STEEL_D
        return STEEL_L if (x + seed) % 2 == 0 and B.n(x, y, seed) > 0.3 else STEEL
    return f


def saw_blade(face, x, y, w, h):
    """The bone saw: a steel blade with a toothed edge (the front edge of the face), rust near the teeth."""
    if face in ("left", "right"):
        if x == 0:
            return STEEL_D if y % 2 else STEEL_L                                      # the teeth
        if x == 1 and B.n(x, y, 71) < 0.3:
            return STAIN
        return STEEL if (x + y) % 3 else STEEL_L
    return STEEL_D


def syringe(face, x, y, w, h):
    """The syringe's glass barrel: brass caps top and bottom, green serum inside, black graduations."""
    if face in ("top", "bottom") or y in (0, h - 1):
        return B.BRASS
    if x == 0 and y % 2 == 1:
        return BLACK
    return GREEN if y >= 2 else (200, 230, 220)


def syringe_glow(face, x, y, w, h):
    if face in ("top", "bottom") or y in (0, 1, h - 1):
        return None
    if x == 0 and y % 2 == 1:
        return None
    return GREEN


def joint(face, x, y, w, h):
    return B.BRASS_L if (x + y) % 2 else B.BRASS_D


def rod(seed=0):
    return B.rod(B.BRASS, seed)


def gear(face, x, y, w, h):
    if face not in ("front", "back"):
        return None
    if B.cog_mask(x, y, w, h, teeth=8, hub=0.25):
        return B.BRASS_L if y < h / 2 else B.BRASS
    return None


def harness(face, x, y, w, h):
    return B.brass(81, rivet_step=2)(face, x, y, w, h)


def chain_link(face, x, y, w, h):
    return B.BRASS_L if face in ("front", "top") else B.BRASS_D


# ---------------------------------------------------------------- build
ARMS = (  # name, side (+1 = her left), mount y on the harness, upper length, fore length
    ("saw", 1, -3, 16, 13),
    ("scalpel", -1, -3, 16, 13),
    ("forceps", 1, 3, 10, 11),
    ("syringe", -1, 3, 10, 11),
)
# rest pose of each arm: the upper segment rises out and back, the forearm hooks down and forward
ARM_REST = {
    "saw": ((-25, 0, 38), (140, 0, -50)),
    "scalpel": ((-25, 0, -38), (140, 0, 50)),
    "forceps": ((-20, 0, 105), (95, 0, -50)),
    "syringe": ((-20, 0, -105), (95, 0, 50)),
}


def build():
    m = Model("asylum_director", seed=907, shadow=1.0, walk_speed=0.9, walk_scale=0.7, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, 0, 0))
    m.part("leg_r", "body", pivot=(-2, -26, 0))
    m.part("leg_l", "body", pivot=(2, -26, 0))
    m.part("hips", "body", pivot=(0, -26, 0))
    m.part("tails", "hips", pivot=(0, 0, 0))
    m.part("hem", "tails", pivot=(0, 10, 0))
    m.part("chest", "hips", pivot=(0, 0, 0))
    m.part("heart", "chest", pivot=(0, -13.5, -2.6))
    m.part("neck", "chest", pivot=(0, -21, 0))
    m.part("head", "neck", pivot=(0, -2, 0))
    m.part("beak", "head", pivot=(0, -3, -4.2), rot=(22, 0, 0))
    m.part("arm_r", "chest", pivot=(-5, -19, 0), rot=(0, 0, 6))
    m.part("fore_r", "arm_r", pivot=(0, 11, 0), rot=(-18, 0, 0))
    m.part("hand_r", "fore_r", pivot=(0, 10, 0))
    m.part("arm_l", "chest", pivot=(5, -19, 0), rot=(-10, 0, -6))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-40, 0, 0))
    m.part("hand_l", "fore_l", pivot=(0, 10, 0))
    m.part("watch", "hand_l", pivot=(0, 4, 0))
    m.part("lid", "watch", pivot=(0, 5, -0.5))
    m.part("pack", "chest", pivot=(0, -14, 2.5))
    m.part("cog", "pack", pivot=(0, -1, 2.5))

    # ---- legs: long, thin, dark trousers and buttoned boots
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -1.5, 0, -1.5, 3, 22, 3, trousers)
        m.box(leg, -2, 21, -2.5, 4, 5, 5, boot)
        m.box(leg, -1.5, 25, -3.5, 3, 1, 1, BOOT_L)                                      # the toe cap

    # ---- the coat: skirts open at the front, tails split at the back, stained white
    m.box("tails", -5, 0, -3.5, 10, 10, 7, coat(12, open_front=2))
    m.box("hem", -5.5, 0, -4, 5, 10, 8, coat(13))                                        # right skirt
    m.box("hem", 0.5, 0, -4, 5, 10, 8, coat(14))                                         # left skirt
    m.box("tails", -5.5, -1.5, -4, 11, 2, 8, B.LEATHER)                                  # the belt
    m.box("tails", -1, -1.8, -4.4, 2, 2, 1, B.brass(15))                                 # its buckle
    m.box("tails", 3, 1, -4.3, 2, 3, 1, coat(16, hem=False))                             # a pocket
    m.box("tails", 3.5, 0, -4.6, 1, 1, 1, B.BRASS_L)                                     # the chain's anchor

    # ---- torso: the bodice, the glass plate, the ticking heart, shoulders, collar
    m.box("chest", -4, -20, -2.5, 8, 20, 5, torso_paint)
    m.box("chest", -5, -21, -3, 10, 3, 6, coat(21, hem=False))                           # shoulders
    m.box("chest", -2.5, -23, -2.5, 5, 2, 5, {"*": COAT_L, "front": coat(22, hem=False)})  # the high collar
    m.box("chest", -1, -21.5, -3.2, 2, 2, 1, BLACK)                                      # the cravat knot
    m.box("chest", -3, -18, -3.4, 6, 8, 1, frame)                                        # the glass chest plate
    m.box("heart", -2, -2, -0.5, 4, 4, 1, heart, glow=heart_glow)
    m.box("heart", -0.5, -0.5, -0.8, 1, 1, 1, B.BRASS_L)

    # ---- head: the cap, the hair, the brass plague mask with green lenses and a long beak, the head mirror
    m.box("neck", -1, -3, -1, 2, 4, 2, SKIN)
    m.box("head", -3.5, -8, -3.5, 7, 8, 7, head_paint)
    m.box("head", -4, -10, -4, 8, 3, 8, cap)
    m.box("head", -1.5, -6, 3.2, 3, 3, 2, hair)                                          # the bun
    m.box("head", -3, -7, -4.3, 6, 6, 1, mask)
    for x in (-2.6, 0.6):
        m.box("head", x, -6, -4.9, 2, 2, 1, lens, glow=lens_glow)
    m.box("head", -1.5, -10, -4.8, 3, 3, 1, mirror)                                      # the head mirror
    m.box("head", -4.2, -6.5, -3, 1, 2, 3, B.brass(63))                                  # mask hinges
    m.box("head", 3.2, -6.5, -3, 1, 2, 3, B.brass(64))
    m.box("beak", -1.5, -1.5, -6, 3, 3, 6, beak)
    m.box("beak", -1, -1, -9, 2, 2, 3, beak)
    m.box("beak", -0.5, -0.5, -10, 1, 1, 1, B.BRASS_D)

    # ---- arms: long coat sleeves, black gloves with long fingers; the pocket watch from her left hand
    for side, arm, fore, hand in ((-1, "arm_r", "fore_r", "hand_r"), (1, "arm_l", "fore_l", "hand_l")):
        m.box(arm, -1.5, -1, -1.5, 3, 12, 3, sleeve(40 + side, cuff=False))
        m.box(fore, -1.5, 0, -1.5, 3, 10, 3, sleeve(42 + side))
        m.box(hand, -1, 0, -1.5, 2, 3, 3, glove)
        for k, z in enumerate((-1.5, -0.5, 0.5)):
            m.box(hand, -0.5 - 0.5 * side, 3, z, 1, 4 if k == 1 else 3, 1, glove)       # long fingers
    for k in range(3):
        m.box("watch", -0.5, k * 1.5, -0.5, 1, 1, 1, chain_link)
    m.box("watch", -2, 5, -0.5, 4, 4, 1, B.dial(numerals=12))
    m.box("watch", -0.5, 4.2, -0.6, 1, 1, 1, B.BRASS_L)                                  # the crown
    m.box("lid", -2, 0, -0.5, 4, 4, 0, {"front": B.brass(66), "back": B.brass(67)})     # the hinged lid (flat)

    # ---- the harness and its cog, the four surgical arms
    m.box("pack", -3, -5, 0, 6, 10, 2, harness)
    m.box("pack", -1, -7, 0.5, 2, 2, 1, B.brass(82))
    m.box("cog", -3, -3, -0.5, 6, 6, 1, gear)
    m.box("cog", -1, -1, 0, 2, 2, 1, HEART, glow=HEART)
    for name, side, y, up, fore in ARMS:
        (ur, fr) = ARM_REST[name]
        sa, sf, tool = f"sa_{name}", f"sf_{name}", f"tool_{name}"
        m.part(sa, "pack", pivot=(side * 2.2, y, 1.5), rot=ur)
        m.part(sf, sa, pivot=(0, -up, 0), rot=fr)
        m.part(tool, sf, pivot=(0, -fore, 0))
        m.box(sa, -1, -1, -1, 2, 2, 2, joint)
        m.box(sa, -0.5, -up, -0.5, 1, up, 1, rod(83))
        m.box(sa, -0.5, -up * 0.6, -1, 1, 2, 2, B.IRON)                                  # a piston collar
        m.box(sf, -1, -1, -1, 2, 2, 2, joint)
        m.box(sf, -0.5, -fore, -0.5, 1, fore, 1, rod(84))
        m.box(tool, -1, -1, -1, 2, 2, 2, B.brass(85))                                    # the tool's chuck
    # the tools (each points along -y, past the end of its forearm)
    m.box("tool_scalpel", -0.5, -4, -0.5, 1, 3, 1, B.BRASS_D)
    m.box("tool_scalpel", -0.5, -9, -1, 1, 5, 2, steel(91))
    m.box("tool_scalpel", -0.5, -10, -1, 1, 1, 1, STEEL_L)
    m.box("tool_saw", -0.5, -3, -1, 1, 2, 2, B.BRASS_D)
    m.box("tool_saw", -0.5, -11, -2, 1, 8, 4, saw_blade)
    m.box("tool_saw", -0.5, -12, 0.5, 1, 9, 1, B.IRON)                                  # the frame's back
    m.box("tool_syringe", -1, -3, -1, 2, 2, 2, B.BRASS_D)                               # plunger cap
    m.box("tool_syringe", -1, -9, -1, 2, 6, 2, syringe, glow=syringe_glow)
    m.box("tool_syringe", -0.5, -12, -0.5, 1, 3, 1, STEEL_L)                            # the needle
    m.box("tool_syringe", -1.5, -4, -0.5, 3, 1, 1, B.BRASS)                             # finger flange
    m.part("prong_a", "tool_forceps", pivot=(-0.6, -1, 0), rot=(0, 0, -8))
    m.part("prong_b", "tool_forceps", pivot=(0.6, -1, 0), rot=(0, 0, 8))
    m.box("prong_a", -0.5, -7, -0.5, 1, 7, 1, steel(92))
    m.box("prong_b", -0.5, -7, -0.5, 1, 7, 1, steel(93))
    m.box("prong_a", -0.5, -8, -1, 1, 1, 2, STEEL_L)
    m.box("prong_b", -0.5, -8, -1, 1, 1, 2, STEEL_L)

    _anims(m)
    return m


def _arm(a, name, *keys):
    """Keyframes for a surgical arm's two segments: each key is (t, upper rot, fore rot[, interp]); rotations are
    offsets from the rest pose, like every channel."""
    up, fo = [], []
    for k in keys:
        t, u, f = k[0], k[1], k[2]
        extra = k[3:] if len(k) > 3 else ()
        up.append((t, u) + extra)
        fo.append((t, f) + extra)
    a.rot(f"sa_{name}", *up)
    a.rot(f"sf_{name}", *fo)


Z = (0, 0, 0)


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.rot("chest", (0, Z), (2.0, (2, 0, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (1.2, (4, 10, 0)), (2.8, (-2, -8, 0)), (4.0, Z))
    idle.rot("cog", (0, Z), (4.0, (0, 0, 360)))
    idle.scale("heart", (0, (1, 1, 1)), (0.5, (1.25, 1.25, 1.25)), (0.7, (1, 1, 1)), (2.0, (1, 1, 1)),
               (2.5, (1.25, 1.25, 1.25)), (2.7, (1, 1, 1)), (4.0, (1, 1, 1)))
    idle.rot("watch", (0, Z), (1.0, (0, 0, 12)), (3.0, (0, 0, -12)), (4.0, Z))
    idle.rot("hem", (0, Z), (2.0, (4, 0, 0)), (4.0, Z))
    for k, (name, side, *_r) in enumerate(ARMS):
        ph = 0.6 * k
        _arm(idle, name, (0, Z, Z), (1.0 + ph, (6, 0, side * 6), (-10, 0, 0)), (2.6 + ph * 0.5, (-4, 0, -side * 4), (8, 0, 0)),
             (4.0, Z, Z))
    idle.rot("prong_a", (0, Z), (2.0, (0, 0, 6)), (4.0, Z))
    idle.rot("prong_b", (0, Z), (2.0, (0, 0, -6)), (4.0, Z))

    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (28, 0, 0)), (0.8, (-28, 0, 0)), (1.6, (28, 0, 0)))
    walk.rot("leg_l", (0, (-28, 0, 0)), (0.8, (28, 0, 0)), (1.6, (-28, 0, 0)))
    walk.rot("hem", (0, (14, 0, 0)), (0.8, (18, 0, 0)), (1.6, (14, 0, 0)))
    walk.rot("arm_r", (0, (-14, 0, 0)), (0.8, (14, 0, 0)), (1.6, (-14, 0, 0)))
    walk.rot("chest", (0, (6, 0, 0)), (1.6, (6, 0, 0)))
    walk.rot("watch", (0, (20, 0, 0)), (0.8, (30, 0, 0)), (1.6, (20, 0, 0)))
    for k, (name, side, *_r) in enumerate(ARMS):
        sgn = 1 if k % 2 == 0 else -1
        _arm(walk, name, (0, (sgn * 10, 0, 0), (sgn * -10, 0, 0)), (0.8, (-sgn * 10, 0, 0), (sgn * 10, 0, 0)),
             (1.6, (sgn * 10, 0, 0), (sgn * -10, 0, 0)))

    # scalpel (14 / 8 / 14): the scalpel arm draws far back over her shoulder (0.7 s), then she lunges and it stabs
    # straight ahead at 0.7 s
    a = m.anim("scalpel", 1.8)
    _arm(a, "scalpel", (0, Z, Z), (0.6, (-30, 0, 30), (40, 0, 0)), (0.7, (-34, 0, 32), (44, 0, 0)),
         (0.76, (60, 0, -20), (-70, 0, 0), "linear"), (1.1, (58, 0, -20), (-66, 0, 0)), (1.8, Z, Z))
    a.rot("chest", (0, Z), (0.7, (-8, -20, 0)), (0.76, (16, 10, 0), "linear"), (1.1, (14, 8, 0)), (1.8, Z))
    a.rot("arm_r", (0, Z), (0.7, (-20, 0, 30)), (0.76, (-70, 0, 10), "linear"), (1.1, (-66, 0, 10)), (1.8, Z))
    a.pos("body", (0, Z), (0.7, (0, 0, 2)), (0.76, (0, -1, -5), "linear"), (1.1, (0, -1, -5)), (1.8, Z))
    a.rot("leg_r", (0, Z), (0.76, (-30, 0, 0), "linear"), (1.1, (-28, 0, 0)), (1.8, Z))
    a.rot("leg_l", (0, Z), (0.76, (24, 0, 0), "linear"), (1.1, (22, 0, 0)), (1.8, Z))

    # saw (16 / 24 / 14): the bone-saw arm rises high to her left (0.8 s) and sweeps across her front at 0.8 s; a
    # turn, and back across at 1.5 s (phase 2)
    a = m.anim("saw", 2.7)
    _arm(a, "saw", (0, Z, Z), (0.7, (-20, 30, 30), (-30, 0, 20)), (0.8, (-22, 32, 32), (-32, 0, 20)),
         (0.88, (40, -60, -30), (-60, 0, 30), "linear"), (1.2, (40, -60, -30), (-60, 0, 30)),
         (1.45, (40, -40, -20), (-60, 0, 30)), (1.5, (40, 40, 10), (-60, 0, 30), "linear"), (2.0, (30, 30, 10), (-40, 0, 20)),
         (2.7, Z, Z))
    a.rot("chest", (0, Z), (0.8, (-6, 34, 0)), (0.88, (10, -36, 0), "linear"), (1.45, (8, -30, 0)),
          (1.5, (8, 30, 0), "linear"), (2.0, (4, 20, 0)), (2.7, Z))
    a.rot("arm_r", (0, Z), (0.8, (-30, 0, 40)), (1.5, (-30, 0, 40)), (2.7, Z))
    a.rot("hem", (0, Z), (0.88, (0, -14, 0)), (1.5, (0, 14, 0)), (2.7, Z))

    # syringe (18 / 12 / 12): the syringe arm swings round to aim past her shoulder, the plunger drawn (0.9 s), and
    # fires at 0.9 s (a fan in phase 2)
    a = m.anim("syringe", 2.1)
    _arm(a, "syringe", (0, Z, Z), (0.8, (60, 0, 50), (-60, 0, 10)), (0.9, (62, 0, 52), (-62, 0, 10)),
         (0.95, (66, 0, 52), (-70, 0, 10), "linear"), (1.5, (60, 0, 50), (-60, 0, 10)), (2.1, Z, Z))
    a.pos("tool_syringe", (0, Z), (0.9, (0, -1.5, 0)), (0.95, (0, 1.5, 0), "linear"), (1.5, Z), (2.1, Z))
    a.rot("arm_r", (0, Z), (0.9, (-80, 0, 0)), (1.5, (-80, 0, 0)), (2.1, Z))
    a.rot("head", (0, Z), (0.9, (8, 0, 0)), (1.5, (8, 0, 0)), (2.1, Z))
    a.rot("chest", (0, Z), (0.9, (-4, 14, 0)), (0.95, (2, 10, 0), "linear"), (2.1, Z))

    # rewind (20 / 8 / 14): she raises the pocket watch to her lenses and winds the crown back (1.0 s); the lid snaps
    # open at 1.0 s and the four arms flinch inward
    a = m.anim("rewind", 2.1)
    a.rot("arm_l", (0, Z), (0.6, (-110, 0, 20)), (1.0, (-120, 0, 24)), (1.06, (-130, 0, 30), "linear"),
          (1.4, (-130, 0, 30)), (2.1, Z))
    a.rot("fore_l", (0, Z), (0.6, (-30, 0, 0)), (1.4, (-30, 0, 0)), (2.1, Z))
    a.rot("watch", (0, Z), (0.6, (30, 0, 0)), (1.0, (30, 0, -20)), (1.06, (30, 0, 340), "linear"), (1.4, (30, 0, 360)),
          (2.1, (0, 0, 360)))
    a.rot("lid", (0, Z), (1.0, Z), (1.06, (-120, 0, 0), "linear"), (1.4, (-120, 0, 0)), (2.1, Z))
    a.rot("arm_r", (0, Z), (0.8, (-60, 0, -30)), (1.0, (-64, 0, -34)), (1.06, (-40, 0, 40), "linear"), (2.1, Z))
    a.rot("head", (0, Z), (1.0, (16, -10, 0)), (1.06, (-10, 0, 0), "linear"), (2.1, Z))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (1.0, (10, 0, side * 20), (20, 0, 0)), (1.06, (-20, 0, -side * 20), (-30, 0, 0), "linear"),
             (1.4, (-16, 0, -side * 16), (-24, 0, 0)), (2.1, Z, Z))

    # pendulum (24 / 36 / 14): the watch lifted high on its chain (1.2 s), then swung like a pendulum: three swings
    # at 1.2, 1.8 and 2.4 s
    a = m.anim("pendulum", 3.7)
    a.rot("arm_l", (0, Z), (1.0, (-170, 0, 0)), (1.2, (-172, 0, 0)), (3.0, (-170, 0, 0)), (3.7, Z))
    a.rot("fore_l", (0, Z), (1.0, (0, 0, 0)), (3.7, Z))
    a.rot("watch", (0, Z), (1.0, (0, 0, 70)), (1.2, (0, 0, 72)), (1.7, (0, 0, -72)), (1.8, (0, 0, -72)),
          (2.3, (0, 0, 72)), (2.4, (0, 0, 72)), (2.9, (0, 0, -72)), (3.2, (0, 0, -30)), (3.7, Z))
    a.scale("watch", (0, (1, 1, 1)), (1.0, (1.8, 1.8, 1.8)), (3.0, (1.8, 1.8, 1.8)), (3.7, (1, 1, 1)))
    a.rot("arm_r", (0, Z), (1.2, (-40, 0, 60)), (3.0, (-40, 0, 60)), (3.7, Z))
    a.rot("head", (0, Z), (1.2, (-24, 0, 0)), (3.0, (-24, 0, 0)), (3.7, Z))
    a.rot("chest", (0, Z), (1.2, (-6, 0, 0)), (1.7, (-6, 0, -6)), (2.3, (-6, 0, 6)), (2.9, (-6, 0, -6)), (3.7, Z))

    # spiders (18 / 4 / 14): she bends low, the four arms spread wide and rap the floor (0.9 s) to wake the clockwork
    # spiders
    a = m.anim("spiders", 1.8)
    a.rot("chest", (0, Z), (0.8, (30, 0, 0)), (0.9, (34, 0, 0)), (1.1, (30, 0, 0)), (1.8, Z))
    a.rot("head", (0, Z), (0.9, (-20, 0, 0)), (1.8, Z))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (0.8, (20, 0, side * 30), (-40, 0, 0)), (0.9, (22, 0, side * 32), (-42, 0, 0)),
             (0.95, (40, 0, side * 10), (40, 0, 0), "linear"), (1.2, (36, 0, side * 10), (36, 0, 0)), (1.8, Z, Z))
    a.rot("arm_r", (0, Z), (0.9, (-30, 0, 40)), (1.8, Z))

    # forceps (phase 2, 16 / 22 / 14): the forceps arm shoots forward and closes (0.8 s), hauls back by 1.1 s, and
    # the saw cuts at 1.5 s
    a = m.anim("forceps", 2.6)
    _arm(a, "forceps", (0, Z, Z), (0.7, (-20, 0, -30), (40, 0, 0)), (0.8, (-22, 0, -32), (42, 0, 0)),
         (0.86, (40, -60, -70), (-60, 0, 0), "linear"), (1.1, (10, -30, -40), (20, 0, 0)), (1.5, (10, -30, -40), (20, 0, 0)),
         (2.6, Z, Z))
    a.rot("prong_a", (0, Z), (0.8, (0, 0, -20)), (0.86, (0, 0, 8), "linear"), (1.5, (0, 0, 8)), (2.6, Z))
    a.rot("prong_b", (0, Z), (0.8, (0, 0, 20)), (0.86, (0, 0, -8), "linear"), (1.5, (0, 0, -8)), (2.6, Z))
    _arm(a, "saw", (0, Z, Z), (1.1, (-20, 30, 30), (-30, 0, 20)), (1.45, (-22, 32, 32), (-32, 0, 20)),
         (1.5, (40, -60, -30), (-60, 0, 30), "linear"), (1.9, (36, -56, -28), (-56, 0, 28)), (2.6, Z, Z))
    a.rot("chest", (0, Z), (0.8, (-6, -16, 0)), (0.86, (10, 10, 0), "linear"), (1.45, (-4, 26, 0)),
          (1.5, (8, -30, 0), "linear"), (2.6, Z))

    # dissect (phase 2, 16 / 30 / 14): all four arms raised (0.8 s), then each strikes its own quarter in turn at 0.8,
    # 1.2, 1.6 and 2.0 s
    a = m.anim("dissect", 3.0)
    order = ("scalpel", "saw", "syringe", "forceps")
    for k, name in enumerate(order):
        side = dict((n, s) for n, s, *_r in ARMS)[name]
        t = 0.8 + 0.4 * k
        keys = [(0, Z, Z), (0.7, (-30, 0, side * 20), (40, 0, 0))]
        if t > 0.8:
            keys.append((t - 0.06, (-34, 0, side * 22), (44, 0, 0)))
        keys += [(t, (-34, 0, side * 22), (44, 0, 0)), (t + 0.06, (50, 0, -side * 10), (-60, 0, 0), "linear"),
                 (t + 0.3, (40, 0, -side * 10), (-50, 0, 0)), (3.0, Z, Z)]
        if t + 0.3 >= 3.0:
            keys = keys[:-1]
        _arm(a, name, *keys)
    a.rot("chest", (0, Z), (0.8, (-8, 0, 0)), (0.86, (8, 20, 0), "linear"), (1.26, (8, -20, 0), "linear"),
          (1.66, (8, 16, 0), "linear"), (2.06, (8, -16, 0), "linear"), (2.4, (4, 0, 0)), (3.0, Z))
    a.rot("arm_r", (0, Z), (0.8, (-40, 0, 50)), (2.4, (-40, 0, 50)), (3.0, Z))

    # timeslip (phase 2, 12 / 2 / 8): she winds the watch and thins to a sliver (0.6 s), vanishes and reappears
    a = m.anim("timeslip", 1.1)
    a.scale("body", (0, (1, 1, 1)), (0.5, (0.7, 1.08, 0.7)), (0.6, (0.4, 1.15, 0.4)), (0.66, (0.1, 1.3, 0.1), "linear"),
            (0.8, (0.8, 1.05, 0.8)), (1.1, (1, 1, 1)))
    a.rot("arm_l", (0, Z), (0.5, (-90, 0, -20)), (0.8, (-90, 0, -20)), (1.1, Z))
    a.rot("watch", (0, Z), (0.6, (0, 0, -360)), (1.1, (0, 0, -360)))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (0.6, (20, 0, -side * 30), (30, 0, 0)), (0.8, (20, 0, -side * 30), (30, 0, 0)), (1.1, Z, Z))

    # midnight (phase 3, 40 / 20 / 20): she rises on her toes, arms spread like clock hands, the heart racing, the
    # four arms spinning out (2.0 s); at 2.0 s the great clock strikes
    a = m.anim("midnight", 4.0)
    a.pos("body", (0, Z), (1.6, (0, 4, 0)), (2.0, (0, 5, 0)), (2.06, (0, 2, 0), "linear"), (3.2, (0, 2, 0)), (4.0, Z))
    a.rot("arm_r", (0, Z), (1.0, (0, 0, 90)), (2.0, (0, 0, 100)), (2.06, (0, 0, 160), "linear"), (3.2, (0, 0, 160)),
          (4.0, Z))
    a.rot("arm_l", (0, Z), (1.0, (0, 0, -90)), (2.0, (0, 0, -100)), (2.06, (0, 0, -40), "linear"), (3.2, (0, 0, -40)),
          (4.0, Z))
    a.rot("head", (0, Z), (2.0, (-30, 0, 0)), (2.06, (-36, 0, 0), "linear"), (3.2, (-24, 0, 0)), (4.0, Z))
    a.scale("heart", (0, (1, 1, 1)), (0.5, (1.4, 1.4, 1.4)), (0.7, (1, 1, 1)), (1.2, (1.5, 1.5, 1.5)), (1.4, (1, 1, 1)),
            (1.8, (1.7, 1.7, 1.7)), (2.0, (1.2, 1.2, 1.2)), (2.06, (2.0, 2.0, 2.0), "linear"), (3.2, (1.3, 1.3, 1.3)),
            (4.0, (1, 1, 1)))
    a.rot("cog", (0, Z), (2.0, (0, 0, 1440)), (4.0, (0, 0, 2160)))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (2.0, (-10, 0, side * 30), (-60, 0, 0)), (2.06, (-14, 0, side * 40), (-80, 0, 0), "linear"),
             (3.2, (-12, 0, side * 36), (-70, 0, 0)), (4.0, Z, Z))

    # hands (phase 3, 30 / 180 / 16): at the dial's centre she lifts her right arm forward (the minute hand) and her
    # left arm out to the side (the hour hand) (1.5 s) and holds them while the great hands sweep round; she turns with
    # them (the entity's facing follows the minute hand)
    a = m.anim("hands", 11.3)
    a.rot("arm_r", (0, Z), (1.2, (-90, 0, 0)), (1.5, (-92, 0, 0)), (10.5, (-92, 0, 0)), (11.3, Z))
    a.rot("fore_r", (0, Z), (1.2, (18, 0, 0)), (10.5, (18, 0, 0)), (11.3, Z))
    a.rot("arm_l", (0, Z), (1.2, (0, 0, -90)), (1.5, (0, 0, -92)), (10.5, (0, 0, -92)), (11.3, Z))
    a.rot("fore_l", (0, Z), (1.2, (40, 0, 0)), (10.5, (40, 0, 0)), (11.3, Z))
    a.rot("head", (0, Z), (1.5, (-14, 0, 0)), (10.5, (-14, 0, 0)), (11.3, Z))
    a.rot("cog", (0, Z), (1.5, (0, 0, 180)), (10.5, (0, 0, 1800)), (11.3, (0, 0, 1800)))
    a.scale("heart", (0, (1, 1, 1)), (1.5, (1.5, 1.5, 1.5)), (10.5, (1.5, 1.5, 1.5)), (11.3, (1, 1, 1)))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (1.5, (-10, 0, side * 24), (-30, 0, 0)), (10.5, (-10, 0, side * 24), (-30, 0, 0)),
             (11.3, Z, Z))

    # roar (phase two): head thrown back, arms and the four surgical arms flung wide, the heart flaring
    a = m.anim("roar", 2.0)
    a.rot("head", (0, Z), (0.5, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, Z))
    a.rot("arm_r", (0, Z), (0.5, (-40, 0, 70)), (1.6, (-44, 0, 74)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.5, (-40, 0, -70)), (1.6, (-44, 0, -74)), (2.0, Z))
    a.scale("heart", (0, (1, 1, 1)), (0.5, (1.8, 1.8, 1.8)), (1.6, (1.6, 1.6, 1.6)), (2.0, (1, 1, 1)))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (0.5, (-20, 0, side * 30), (-50, 0, 0)), (1.6, (-18, 0, side * 28), (-46, 0, 0)), (2.0, Z, Z))

    # stagger: she buckles to one knee, the arms sag, the watch swinging
    a = m.anim("stagger", 2.0)
    a.pos("body", (0, Z), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.3, (-80, 0, 0)), (1.6, (-80, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (0.3, (40, 0, 0)), (1.6, (40, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, Z))
    a.rot("head", (0, Z), (0.3, (24, 0, -14)), (1.6, (24, 0, -14)), (2.0, Z))
    a.rot("watch", (0, Z), (0.3, (0, 0, 40)), (0.8, (0, 0, -30)), (1.3, (0, 0, 15)), (2.0, Z))
    for name, side, *_r in ARMS:
        _arm(a, name, (0, Z, Z), (0.3, (30, 0, -side * 20), (40, 0, 0)), (1.6, (32, 0, -side * 20), (42, 0, 0)), (2.0, Z, Z))
