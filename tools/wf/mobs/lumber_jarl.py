"""The Lumber Jarl (Le Jarl du bois): the champion of the Timber Fortress, about 4 blocks tall.

Silhouette idea: a giant lumberjack warlord, broader than he is tall in the shoulders. A horned helm of iron under a
fur brim, a nose guard, a great braided red beard with iron rings on the braids; a red-and-black plaid shirt under a
mantle of chainmail and a fur collar over a barrel chest, a wide belt with a brass buckle; plaid trousers bound with
leather and heavy iron-shod boots. In both hands a steam chainsaw-axe: a long iron-banded haft, a little brass engine
with a smoking stack and a glowing firebox where the head should be, and from it a long steel bar ringed by a toothed
chain, a bearded axe blade on its back. On his back a log-carrier harness: an iron frame strapped over the shoulders
holding two spruce logs and two spare saw blades.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

PLAID = (178, 38, 34)
PLAID_D = (110, 22, 22)
PLAID_K = (34, 26, 26)
FUR = (124, 92, 62)
FUR_L = (170, 132, 92)
FUR_D = (78, 56, 38)
SKIN = (212, 156, 118)
SKIN_D = (168, 112, 82)
BEARD = (196, 74, 34)
BEARD_L = (236, 124, 62)
BEARD_D = (128, 44, 20)
MAIL = (148, 150, 158)
MAIL_L = (196, 200, 208)
MAIL_D = (86, 88, 96)
STEEL = (200, 206, 212)
STEEL_L = (244, 248, 252)
STEEL_D = (124, 130, 140)
WOOD = (112, 74, 42)
WOOD_L = (150, 104, 62)
WOOD_D = (72, 46, 26)
BARK = (84, 62, 40)
BARK_D = (52, 38, 26)
RING = (178, 140, 92)           # the log ends' growth rings
RING_L = (214, 180, 128)
LEATHER = (104, 66, 40)
LEATHER_D = (66, 40, 24)
HORN = (226, 214, 184)
HORN_D = (164, 148, 116)
FIRE = (255, 150, 50)
FIRE_L = (255, 228, 140)


# ---------------------------------------------------------------- paint
def plaid(seed=0):
    """Red-and-black buffalo check: 4-texel squares, the black bands crossing darker."""
    def f(face, x, y, w, h):
        a = (x // 3) % 2
        b = (y // 3) % 2
        if a and b:
            c = PLAID_K
        elif a or b:
            c = PLAID_D
        else:
            c = PLAID
        if face == "bottom":
            return mul(c, 0.7)
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def mail(face, x, y, w, h):
    """Chainmail: rows of little rings, staggered, a lit top row."""
    if face == "bottom":
        return MAIL_D
    if face == "top":
        return MAIL_L if (x + y) % 2 else MAIL
    xx = x + (y % 2)
    if y == 0:
        return MAIL_L
    if xx % 2 == 0:
        return MAIL_L if y % 2 == 0 else MAIL
    return MAIL_D


def fur(seed=0):
    """Shaggy fur: streaks, ragged lower edge on the sides."""
    def f(face, x, y, w, h):
        r = B.n(x, y // 2, seed)
        if face == "bottom":
            return FUR_D
        if face != "top" and y == h - 1 and r > 0.55:
            return None
        return FUR_L if r > 0.75 else (FUR if r > 0.25 else FUR_D)
    return f


def skin(face, x, y, w, h):
    return SKIN if B.n(x, y, 3) > 0.15 else SKIN_D


def face(face_, x, y, w, h):
    """The face (10 x 10 x 10 head): brows and fierce eyes, a ruddy nose; the rest is skin (the beard and helm cover
    the top and the jaw)."""
    if face_ != "front":
        return skin(face_, x, y, w, h)
    if y == 4 and x in (1, 2, 3, 6, 7, 8):
        return BEARD_D                                                                 # the brows
    if y == 5 and x in (2, 7):
        return (240, 236, 226)
    if y == 5 and x in (3, 6):
        return (40, 60, 90)                                                            # the eyes
    if y in (5, 6, 7) and x in (4, 5):
        return mix(SKIN, (200, 90, 70), 0.35)                                          # the nose
    return skin(face_, x, y, w, h)


def beard(seed=0):
    """Thick red beard: strands running down, lighter and darker locks."""
    def f(face, x, y, w, h):
        if face == "top":
            return BEARD_D
        r = B.n(x, y // 3, seed)
        if face != "bottom" and y == h - 1 and x % 2:
            return None
        return BEARD_L if r > 0.7 else (BEARD if r > 0.25 else BEARD_D)
    return f


def braid(face, x, y, w, h):
    """A braid: plaited segments, an iron ring every few texels."""
    if y % 5 == 4:
        return B.IRON_L if x % 2 == 0 else B.IRON
    return BEARD_L if (x + y) % 3 == 0 else (BEARD if (x + y) % 3 == 1 else BEARD_D)


def helm(face, x, y, w, h):
    """The iron helm: a riveted cap with a brass band low on it."""
    if face == "top":
        return B.IRON_L if x in (w // 2, w // 2 - 1) else B.IRON
    if y == h - 1:
        return B.BRASS if x % 3 else B.BRASS_L
    return B.iron(31)(face, x, y, w, h)


def horn(face, x, y, w, h):
    """An ox horn: ivory at the tip, darker at the root."""
    k = B.n(x, y, 41)
    return HORN if k > 0.3 else HORN_D


def horn_tip(face, x, y, w, h):
    return (244, 236, 214)


def belt(face, x, y, w, h):
    """The wide belt with a brass buckle in front."""
    if face == "front" and abs(x - (w - 1) / 2) < 2.0:
        return B.BRASS_L if y in (0, h - 1) or abs(x - (w - 1) / 2) > 1.2 else B.BRASS_D
    if face in ("top", "bottom"):
        return LEATHER_D
    return LEATHER if (x + y) % 6 else LEATHER_D


def wrap(face, x, y, w, h):
    """Leather bindings round the shins."""
    return LEATHER_D if (y + x // 2) % 3 == 0 else LEATHER


def boot(seed=0):
    """Iron-shod boots: dark leather uppers, an iron toe cap and sole."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return B.IRON_D
        if y >= h - 2:
            return B.IRON_L if y == h - 2 and x % 3 == 1 else B.IRON
        if face == "front" and y >= h - 4:
            return B.IRON_L if y == h - 4 else B.IRON
        return LEATHER_D if B.n(x, y, seed) < 0.3 else mul(LEATHER_D, 1.2)
    return f


def bracer(face, x, y, w, h):
    """Iron bracers over the forearms, studded."""
    if face in ("top", "bottom"):
        return B.IRON_D
    if y in (0, h - 1):
        return B.IRON_L
    return B.BRASS if (x + y) % 4 == 0 and y % 3 == 1 else B.IRON


def glove(face, x, y, w, h):
    return LEATHER if (x + y) % 4 else LEATHER_D


def haft(face, x, y, w, h):
    """The long haft: ash wood with grain, iron bands every 8 texels."""
    if y % 8 == 0:
        return B.IRON_L if x % 2 == 0 else B.IRON
    if face in ("top", "bottom"):
        return WOOD_D
    return WOOD_L if (x * 3 + y) % 7 == 0 else (WOOD if (y // 2 + x) % 3 else WOOD_D)


def grip_wrap(face, x, y, w, h):
    return LEATHER_D if y % 2 == 0 else LEATHER


def engine(face, x, y, w, h):
    """The little steam engine: a brass block with copper bands and a firebox grate on both broad sides."""
    if face in ("left", "right") and 1 <= y <= h - 2 and 1 <= x <= w - 2:
        return FIRE_L if (x + y) % 3 == 0 else (FIRE if x % 2 else B.SOOT)
    if y in (0, h - 1):
        return B.COPPER_L if x % 3 == 1 else B.COPPER
    return B.brass(61)(face, x, y, w, h)


def engine_glow(face, x, y, w, h):
    if face in ("left", "right") and 1 <= y <= h - 2 and 1 <= x <= w - 2:
        return FIRE_L if (x + y) % 3 == 0 else (FIRE if x % 2 else None)
    return None


def stack(face, x, y, w, h):
    return B.soot(B.IRON, 63)(face, x, y, w, h)


def bar(face, x, y, w, h):
    """The chainsaw bar: bright steel in the middle, the toothed chain round its edges (dark links, bright teeth)."""
    if face in ("top", "bottom"):
        return STEEL_L if x % 2 == 0 else B.IRON                                       # chain teeth along the edge
    if face in ("front", "back"):
        return B.IRON_D if y % 2 else STEEL_L                                           # the chain round the tip
    # the broad sides
    edge = y in (0, h - 1) or x in (0, w - 1)
    if edge:
        return STEEL_L if (x + y) % 2 == 0 else B.IRON
    if y in (1, h - 2):
        return B.IRON_D
    return STEEL if (x + y) % 9 else STEEL_D


def axe_blade(face, x, y, w, h):
    """The bearded axe blade: steel, a bright ground edge on the far side."""
    if face in ("front", "back", "left", "right"):
        if face in ("left", "right") and x == w - 1:
            return STEEL_L
        return STEEL if (x + y) % 5 else STEEL_D
    return STEEL_D


def log_side(face, x, y, w, h):
    """A spruce log lying across (along x): bark on the long faces, rings on the ends."""
    if face in ("left", "right"):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d > min(w, h) / 2 - 0.6:
            return BARK_D
        return RING_L if int(d) % 2 == 0 else RING
    return BARK if (x * 2 + y) % 5 else BARK_D


def strap(face, x, y, w, h):
    return LEATHER if (x + y) % 5 else LEATHER_D


def frame(face, x, y, w, h):
    return B.IRON_L if y == 0 else B.IRON


def blade_disc(face, x, y, w, h):
    """A spare saw blade (a flat disc standing sideways): steel teeth round the rim, a brass hub."""
    if face not in ("left", "right"):
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    r = w / 2
    if d > r:
        return None
    if d > r - 1.0:
        return STEEL_L if (x + y) % 2 == 0 else None                                    # the teeth
    if d < 1.2:
        return B.BRASS_L
    if d < 1.9:
        return B.BRASS_D
    return STEEL if (x * 2 + y) % 7 else STEEL_D


# ---------------------------------------------------------------- build
def build():
    m = Model("lumber_jarl", seed=929, shadow=1.5, walk_speed=0.7, walk_scale=0.8, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -22, 0))
    m.part("chest", "hips", pivot=(0, -3, 0))
    m.part("head", "chest", pivot=(0, -23, -1))
    m.part("beard", "head", pivot=(0, -4, -5.4))
    m.part("pack", "chest", pivot=(0, -12, 7))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5.5 * sx, -22, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 11, 0))
    m.part("arm_r", "chest", pivot=(-13.5, -18, 0), rot=(-20, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 11, 0), rot=(-34, 0, 0))
    m.part("axe", "fore_r", pivot=(0, 11.5, 0), rot=(54, 0, -10))
    m.part("saw", "axe", pivot=(0, -38, 0))
    m.part("arm_l", "chest", pivot=(13.5, -18, 0), rot=(-14, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-24, 0, 0))

    # ---- legs: plaid trousers, leather bindings, iron-shod boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -4, -1, -4, 8, 13, 8, plaid(10 + sx))
        m.box(shin, -3.5, 0, -3.5, 7, 6, 7, wrap)
        m.box(shin, -4.5, 5, -5, 9, 6, 10, boot(12 + sx))
        m.box(shin, -4, 6, -7, 8, 5, 2, boot(14 + sx))                                # the iron toe cap
        m.box(shin, -4.5, 0, -4.5, 9, 2, 9, fur(16 + sx))                             # fur cuffs

    # ---- hips and the barrel chest: plaid under a chainmail mantle, a fur collar, the belt
    m.box("hips", -10, -3, -6, 20, 6, 12, plaid(20))
    m.box("hips", -10.5, -1, -6.5, 21, 3, 13, belt)
    m.box("chest", -11, -20, -7, 22, 20, 14, plaid(21))
    m.box("chest", -12, -14, -8, 24, 4, 16, plaid(22))                                # the barrel belly bulge
    m.box("chest", -11.5, -21, -7.5, 23, 9, 15, mail)                                  # the chainmail mantle
    m.box("chest", -12.5, -12, -7.6, 3, 3, 15, mail)                                   # its hem at the sides
    m.box("chest", 9.5, -12, -7.6, 3, 3, 15, mail)
    m.box("chest", -12, -23, -6, 24, 3, 13, fur(23))                                   # the fur collar and shoulders
    m.box("chest", -15.5, -23, -4.5, 5, 4, 9, fur(24))
    m.box("chest", 10.5, -23, -4.5, 5, 4, 9, fur(25))
    m.box("chest", -3, -21, -8.2, 2, 18, 1, LEATHER)                                   # the harness straps (front)
    m.box("chest", 4, -21, -8.2, 2, 18, 1, LEATHER)
    m.box("chest", -3.5, -12, -8.6, 3, 3, 1, B.BRASS)                                  # their buckles
    m.box("chest", 3.5, -12, -8.6, 3, 3, 1, B.BRASS)

    # ---- the head: a fierce face, the horned iron helm with its fur brim and nose guard, the braided red beard
    m.box("head", -5, -10, -5, 10, 10, 10, face)
    m.box("head", -5.5, -13, -5.5, 11, 5, 11, helm)
    m.box("head", -6.5, -9, -6.5, 13, 2, 13, fur(32))                                 # the fur brim
    m.box("head", -0.5, -8, -6.6, 1, 4, 1, B.IRON_L)                                  # the nose guard
    m.box("head", -1.5, -14, -1.5, 3, 1, 3, B.BRASS)                                  # the crest knob
    for sx in (-1, 1):                                                                # the horns curving up and out
        m.box("head", 5.5 if sx > 0 else -8.5, -12, -1.5, 3, 3, 3, horn)
        m.box("head", 8.5 if sx > 0 else -10.5, -15, -1, 2, 4, 2, horn)
        m.box("head", 9.5 if sx > 0 else -11.5, -19, -0.5, 2, 4, 2, horn)
        m.box("head", 9.0 if sx > 0 else -11.0, -21, 0, 2, 2, 1, horn_tip)
        m.box("head", 5.4 if sx > 0 else -5.4, -6, -3, 0, 5, 6, fur(34 + sx))        # hair down the sides
    m.box("beard", -5, 0, -1, 10, 7, 3, beard(35))                                    # the beard
    m.box("beard", -4, 7, -1, 8, 3, 2, beard(36))
    m.box("beard", -4, -3, -1.6, 8, 2, 1, BEARD_D)                                    # the moustache
    m.box("beard", -3.5, 9, -0.5, 2, 9, 2, braid)                                     # two long braids
    m.box("beard", 1.5, 9, -0.5, 2, 9, 2, braid)

    # ---- the log-carrier harness on his back: iron frame, two logs across, two spare saw blades
    m.box("pack", -9, -10, 0, 2, 22, 2, frame)
    m.box("pack", 7, -10, 0, 2, 22, 2, frame)
    m.box("pack", -9, 4, 0, 18, 2, 3, frame)
    m.box("pack", -11, -13, 2, 22, 6, 6, log_side)                                     # the logs, ends showing
    m.box("pack", -10, -7, 2, 20, 6, 6, log_side)
    m.box("pack", -11.5, -11.5, 4, 23, 1, 2, strap)                                      # straps round them
    m.box("pack", -10.5, -5.5, 4, 21, 1, 2, strap)
    m.box("pack", -11, 0, 0, 1, 9, 9, blade_disc)                                     # the spare saw blades
    m.box("pack", 10, 0, 0, 1, 9, 9, blade_disc)
    m.box("pack", 6, -18, 3, 2, 5, 2, stack)                                         # a little kettle-stack

    # ---- arms: fur-and-mail upper arms, iron bracers, gloved hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -3.5, -2, -3.5, 7, 13, 7, mail)
        m.box(arm, -4, -3, -4, 8, 4, 8, fur(50 + sx))                                 # fur on the shoulder
        m.box(fore, -3, 0, -3, 6, 10, 6, bracer)
        m.box(fore, -2.5, 9, -2.5, 5, 4, 5, glove)

    # ---- the steam chainsaw-axe: the haft, the engine and stack, the toothed bar and the bearded blade
    m.box("axe", -1, -38, -1, 2, 48, 2, haft)
    m.box("axe", -1.5, -4, -1.5, 3, 8, 3, grip_wrap)                                  # the grips
    m.box("axe", -1.5, -20, -1.5, 3, 6, 3, grip_wrap)
    m.box("axe", -1.5, 10, -1.5, 3, 2, 3, B.IRON)                                     # the pommel
    m.box("saw", -3, -6, -3, 6, 7, 6, engine, glow=engine_glow)                       # the engine
    m.box("saw", -1, -11, 1, 2, 5, 2, stack)                                          # its smokestack
    m.box("saw", -1.5, -12, 0.5, 3, 1, 3, B.IRON_D)
    m.box("saw", -3.5, 1, -3.5, 7, 1, 7, B.COPPER)                                    # the engine's collar
    m.box("saw", -1, -8, -16, 2, 9, 13, bar)                                          # the chainsaw bar (forward)
    m.box("saw", -1.5, -6, -6, 3, 7, 3, B.brass(65))                                  # the sprocket housing
    m.box("saw", -0.5, -6, 3, 1, 8, 6, axe_blade)                                     # the bearded blade (behind)
    m.box("saw", -0.5, 2, 6, 1, 3, 3, axe_blade)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.6, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (2, -6, 0)), (3.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.5, (4, 0, 0)), (3.0, (0, 0, 0)))
    idle.pos("saw", (0, (0, 0, 0)), (0.1, (0, 0.2, 0)), (0.2, (0, 0, 0)), (0.3, (0, 0.2, 0)), (0.4, (0, 0, 0)),
             (3.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (18, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (18, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 5, 2)), (1.0, (0, -5, -2)), (2.0, (0, 5, 2)))
    walk.rot("beard", (0, (4, 0, 2)), (1.0, (4, 0, -2)), (2.0, (4, 0, 2)))

    # sweep (18 / 16 / 14): the chainsaw-axe cocked over his right shoulder, the engine revving (0.9 s); from 0.9 s he
    # drags the screaming chain across his front from right to left for 0.8 s (four bites), then recovers
    a = m.anim("sweep", 2.4)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.8, (-100, 40, 50)), (0.9, (-102, 42, 50)), (1.1, (-80, 0, 20)),
          (1.4, (-74, -30, 4)), (1.7, (-70, -50, -6)), (2.4, (-20, 0, 10)))
    a.rot("arm_l", (0, (-14, 0, -10)), (0.8, (-110, -10, 10)), (0.9, (-110, -10, 10)), (1.1, (-80, -30, -10)),
          (1.4, (-70, -50, -20)), (1.7, (-66, -60, -26)), (2.4, (-14, 0, -10)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-4, 36, 0)), (1.1, (4, 10, 0)), (1.4, (6, -20, 0)), (1.7, (6, -38, 0)),
          (2.4, (0, 0, 0)))
    a.pos("saw", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (0.95, (0, 0.5, 0)), (1.05, (0, -0.3, 0)), (1.15, (0, 0.5, 0)),
          (1.25, (0, -0.3, 0)), (1.35, (0, 0.5, 0)), (1.45, (0, -0.3, 0)), (1.55, (0, 0.5, 0)), (1.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.7, (10, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.9, (12, 0, 0)), (1.7, (-8, 0, 0)), (2.4, (0, 0, 0)))

    # chop (24 / 16 / 16): the axe raised high over his head in both hands (1.2 s), brought straight down at 1.2 s, the
    # bar biting the deck; he holds it there while the split runs, then wrenches it free
    a = m.anim("chop", 2.8)
    for s, sz in (("r", 1), ("l", -1)):
        rest = (-20, 0, 10) if s == "r" else (-14, 0, -10)
        a.rot(f"arm_{s}", (0, rest), (1.1, (-170, 0, 6 * sz)), (1.2, (-172, 0, 6 * sz)),
              (1.26, (-60, 0, 4 * sz), "linear"), (2.0, (-56, 0, 4 * sz)), (2.8, rest))
    a.rot("fore_r", (0, (-34, 0, 0)), (1.2, (-10, 0, 0)), (1.26, (-30, 0, 0), "linear"), (2.0, (-30, 0, 0)),
          (2.8, (-34, 0, 0)))
    a.rot("axe", (0, (54, 0, -10)), (1.2, (0, 0, 0)), (1.26, (-40, 0, 0), "linear"), (2.0, (-40, 0, 0)),
          (2.8, (54, 0, -10)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-16, 0, 0)), (1.26, (28, 0, 0), "linear"), (2.0, (24, 0, 0)), (2.8, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.2, (0, 1, 0)), (1.26, (0, -3, 0), "linear"), (2.0, (0, -3, 0)), (2.8, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.26, (-24, 0, 0), "linear"), (2.0, (-24, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.26, (20, 0, 0), "linear"), (2.0, (20, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.26, (30, 0, 0), "linear"), (2.0, (30, 0, 0)), (2.8, (0, 0, 0)))

    # blade (20 / 12 / 16): he pulls a spare saw blade off the harness with his left hand and winds back (1.0 s), then
    # flings it side-arm at 1.0 s; the throwing arm follows through
    a = m.anim("blade", 2.4)
    a.rot("arm_l", (0, (-14, 0, -10)), (0.4, (-160, 0, -10)), (0.6, (-40, 60, -60)), (1.0, (-50, 80, -80)),
          (1.06, (-80, -60, -40), "linear"), (1.6, (-70, -40, -30)), (2.4, (-14, 0, -10)))
    a.rot("fore_l", (0, (-24, 0, 0)), (0.6, (-80, 0, 0)), (1.0, (-90, 0, 0)), (1.06, (-10, 0, 0), "linear"),
          (2.4, (-24, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (0, 40, 0)), (1.06, (6, -34, 0), "linear"), (1.6, (4, -24, 0)),
          (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (-20, 0, 10)), (1.0, (-20, 0, 20)), (1.6, (-30, 0, 14)), (2.4, (-20, 0, 10)))

    # timber (20 / 10 / 16): he lifts the axe overhead in one hand and bellows "TIMBER!" (1.0 s), sweeping it down to
    # point at the sky's edge at 1.0 s as the logs start to fall
    a = m.anim("timber", 2.3)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.6, (-170, 0, 20)), (1.0, (-176, 0, 24)), (1.06, (-110, 0, 30), "linear"),
          (1.6, (-110, 0, 30)), (2.3, (-20, 0, 10)))
    a.rot("arm_l", (0, (-14, 0, -10)), (0.6, (-20, 0, -60)), (1.0, (-30, 0, -70)), (1.6, (-30, 0, -70)),
          (2.3, (-14, 0, -10)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-30, 0, 0)), (1.0, (-34, 0, 0)), (1.06, (6, 0, 0), "linear"),
          (2.3, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.06, (14, 0, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (1.06, (10, 0, 0), "linear"), (2.3, (0, 0, 0)))

    # roll (26 / 10 / 14): he reaches back and tears a log from the harness (0.8 s), swings it down in front of him and
    # kicks it on its way at 1.3 s
    a = m.anim("roll", 2.5)
    a.rot("arm_l", (0, (-14, 0, -10)), (0.5, (-190, 0, -20)), (0.8, (-200, 0, -24)), (1.2, (-40, 0, -10)),
          (1.3, (-30, 0, -10)), (2.5, (-14, 0, -10)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-10, 20, 0)), (1.2, (24, 0, 0)), (1.3, (16, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.1, (30, 0, 0)), (1.3, (-60, 0, 0), "linear"), (1.7, (-30, 0, 0)),
          (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.1, (40, 0, 0)), (1.3, (0, 0, 0), "linear"), (2.5, (0, 0, 0)))
    a.scale("pack", (0, (1, 1, 1)), (0.8, (1, 1, 1)), (0.86, (1, 0.6, 1), "linear"), (2.2, (1, 0.6, 1)), (2.5, (1, 1, 1)))

    # call (phase 2, 20 / 10 / 16): he hammers the haft on the deck three times and bellows for his crew (1.0 s)
    a = m.anim("call", 2.3)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.2, (-70, 0, 10)), (0.35, (-30, 0, 8)), (0.5, (-70, 0, 10)), (0.65, (-30, 0, 8)),
          (0.8, (-70, 0, 10)), (1.0, (-30, 0, 8)), (2.3, (-20, 0, 10)))
    a.rot("arm_l", (0, (-14, 0, -10)), (0.5, (-150, 0, -40)), (1.6, (-150, 0, -40)), (2.3, (-14, 0, -10)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-26, 0, 0)), (1.6, (-26, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (0.9, (-16, 0, 0)), (1.6, (-16, 0, 0)), (2.3, (0, 0, 0)))

    # overdrive (phase 3, 40 / 20 / 20): he raises the chainsaw-axe to the beam engine, the engine roaring and spewing
    # smoke (2.0 s); at 2.0 s he slams it into the deck and the engine overdrives
    a = m.anim("overdrive", 4.0)
    for s, sz in (("r", 1), ("l", -1)):
        rest = (-20, 0, 10) if s == "r" else (-14, 0, -10)
        a.rot(f"arm_{s}", (0, rest), (1.0, (-176, 0, 10 * sz)), (2.0, (-180, 0, 6 * sz)),
              (2.06, (-56, 0, 4 * sz), "linear"), (3.2, (-56, 0, 4 * sz)), (4.0, rest))
    a.rot("axe", (0, (54, 0, -10)), (2.0, (0, 0, 0)), (2.06, (-40, 0, 0), "linear"), (3.2, (-40, 0, 0)),
          (4.0, (54, 0, -10)))
    a.scale("saw", (0, (1, 1, 1)), (1.0, (1.1, 1.1, 1.1)), (2.0, (1.25, 1.2, 1.25)), (2.06, (1, 1, 1), "linear"),
            (4.0, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (10, 0, 0), "linear"), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (2.0, (-16, 0, 0)), (2.06, (26, 0, 0), "linear"), (3.2, (22, 0, 0)), (4.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (2.0, (0, 1, 0)), (2.06, (0, -3, 0), "linear"), (3.2, (0, -3, 0)), (4.0, (0, 0, 0)))

    # roar (phase two): the axe thrust to the sky, head thrown back, the beard flying
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (0.5, (-26, 0, 0)), (1.6, (-24, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-20, 0, 10)), (0.5, (-172, 0, 16)), (1.6, (-174, 0, 18)), (2.0, (-20, 0, 10)))
    a.rot("arm_l", (0, (-14, 0, -10)), (0.5, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (-14, 0, -10)))

    # stagger: winded, he drops to one knee leaning on the axe, head hanging
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (1.6, (-60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (70, 0, 0)), (1.6, (70, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (28, 0, 6)), (1.6, (30, 0, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -8)), (1.6, (30, 0, -8)), (2.0, (0, 0, 0)))
