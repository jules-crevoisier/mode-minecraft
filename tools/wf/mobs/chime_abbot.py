"""The Chime Abbot (L'Abbé des carillons): the champion of the Cloud Pagoda, about 3 blocks tall.

Silhouette idea: a little old monk who has outlived his body by turning half of it into clockwork, floating a hand's
breadth over the deck with a great brass halo of wind-chime rods fanned behind his bald head. Layered robes: a long
white under-robe, a cherry-red outer robe in three flaring tiers (the white showing down the front), a gold-edged red
kasaya slung over his left shoulder, a white obi with a gold cord, a heavy mala of brass and red beads with a bell at
its foot. Wide hanging sleeves, white-lined, from which brass mechanical forearms come out; a second, smaller pair of
clockwork arms folds out from under the sleeves and holds a little prayer bell before his belly. His head: an aged,
bald monk's face, drooping white brows and a long white beard; the right half of the skull is a riveted brass plate and
the right eye a glowing amber lens. Asymmetry: his RIGHT hand holds a tall bronze staff whose head is a brass dragon
(horns, whiskers, teal glowing eyes, a ring of chimes hanging from its jaws); his LEFT hand is open for the palm strike.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

RED = (176, 36, 50)            # cherry-red robe
RED_L = (218, 76, 84)
RED_D = (116, 20, 34)
RED_DD = (70, 12, 22)
WHITE = (238, 232, 220)
WHITE_D = (198, 188, 172)
WHITE_DD = (160, 148, 132)
GOLD = (214, 172, 80)
GOLD_L = (250, 222, 140)
GOLD_D = (140, 104, 44)
SKIN = (216, 178, 148)         # old, sun-browned skin
SKIN_L = (236, 204, 176)
SKIN_D = (168, 128, 100)
BEARD = (240, 238, 232)
BEARD_D = (196, 194, 190)
BRONZE = (156, 100, 54)
BRONZE_L = (210, 152, 88)
BRONZE_D = (96, 58, 30)
VERD = (78, 170, 150)
VERD_D = (48, 116, 102)
AMBER = (255, 184, 80)
AMBER_L = (255, 232, 170)
TEAL = (110, 240, 214)
TEAL_L = (210, 255, 246)
WOOD_D = (64, 36, 24)


# ---------------------------------------------------------------- paint
def robe(seed=0, panel=0, tiers=True, hem_trim=True, ragged=0):
    """Cherry-red silk: soft vertical folds, darker toward the hem, a gold trim row at the bottom; with ``panel`` the
    white under-robe shows down the middle of the front face (``panel`` texels wide)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return RED_DD
        if face == "top":
            return RED_L if (x + y) % 5 == 0 else RED
        if ragged:
            cut = h - 1 - int(B.n(x // 2, 0, seed) * ragged)
            if y > cut:
                return None
        if panel and face == "front":
            mid = (w - 1) / 2
            if abs(x - mid) < panel / 2:
                return WHITE if (x + y // 3) % 4 else WHITE_D
            if abs(x - mid) < panel / 2 + 1:
                return GOLD if y % 2 else GOLD_L                                       # gold edging of the opening
        fold = (x + int(B.n(x // 3, 1, seed) * 2)) % 5
        c = (RED_L, RED, RED, RED_D, RED)[fold]
        c = mul(c, 1.06 - 0.24 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if hem_trim and y == h - 1 and h > 3:
            return GOLD_D
        if hem_trim and y == h - 2 and h > 5:
            return GOLD if x % 2 else GOLD_L
        if tiers and h > 8 and B.n(x // 4, y // 5, seed + 4) < 0.08:
            return mix(c, GOLD, 0.35)                                                  # a faded cloud motif
        return c
    return f


def white(seed=0, trim=False):
    """White cotton under-robe and obi: faint folds, a soft shadow toward the bottom."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return WHITE_DD
        k = 1.02 - 0.12 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.05
        c = WHITE if (x + int(B.n(x // 2, 2, seed) * 2)) % 4 else WHITE_D
        if trim and y in (0, h - 1):
            return GOLD if x % 2 else GOLD_D
        return mul(c, k)
    return f


def chest_paint(face, x, y, w, h):
    """The robe's bodice: cherry red with a white crossed collar (left over right) and a kasaya band from the left
    shoulder down to the right hip."""
    if face == "front":
        mid = (w - 1) / 2
        # the crossed collar: two white bands meeting in a V
        d = abs(x - mid) - (h - 1 - y) * 0.42
        if y < h - 3 and -1.2 <= d <= 0.8 and y <= h * 0.75:
            return WHITE if d < 0.3 else WHITE_D
        # the kasaya: a gold-edged band running from the left shoulder (high x) down to the right hip (low x)
        k = (x - 1) - (w - 2) * (1 - y / max(1, h - 1))
        if abs(k) <= 1.5:
            return GOLD_L if abs(k) > 1.0 else mix(RED_D, GOLD, 0.25)
    if face == "back":
        k = (w - 1 - x - 1) - (w - 2) * (1 - y / max(1, h - 1))
        if abs(k) <= 1.5:
            return GOLD if abs(k) > 1.0 else mix(RED_D, GOLD, 0.25)
    return robe(20, tiers=False, hem_trim=False)(face, x, y, w, h)


def kasaya(face, x, y, w, h):
    """The shoulder fold of the kasaya: deep red patchwork in a gold grid (the monk's 'rice field' robe)."""
    if face == "bottom":
        return RED_DD
    if x in (0, w - 1) or y in (0, h - 1):
        return GOLD if (x + y) % 2 else GOLD_D
    if x % 4 == 0 or y % 3 == 0:
        return mix(GOLD_D, RED_D, 0.4)
    return mul(RED_D if (x // 4 + y // 3) % 2 else RED, 1.0 + (B.n(x, y, 61) - 0.5) * 0.08)


def sleeve(seed=0):
    """The wide hanging sleeves: red silk outside, the white lining showing at the opening (the bottom face) and as a
    rim on the lowest rows."""
    def f(face, x, y, w, h):
        if face == "bottom":
            if x in (0, w - 1) or y in (0, h - 1):
                return WHITE_D
            return mul(WHITE_DD, 0.55)                                                 # the dark inside of the sleeve
        if face != "top" and y >= h - 2:
            return WHITE if y == h - 2 else GOLD_D
        return robe(seed, tiers=False, hem_trim=False)(face, x, y, w, h)
    return f


def obi(face, x, y, w, h):
    """The white obi, a gold cord wound round its middle."""
    if face in ("top", "bottom"):
        return WHITE_D
    if y == h // 2:
        return GOLD_L if x % 3 else GOLD
    if y in (0, h - 1):
        return WHITE_D
    return WHITE if (x + y) % 5 else WHITE_D


def bead(col):
    light = mix(col, (255, 255, 255), 0.35)
    dark = mul(col, 0.6)

    def f(face, x, y, w, h):
        if face == "bottom":
            return dark
        if face == "top" or (x == 0 and y == 0):
            return light
        return col if (x + y) % 3 else dark
    return f


def skin(seed=0):
    def f(face, x, y, w, h):
        c = SKIN if B.n(x, y, seed) > 0.18 else SKIN_D
        if face == "top":
            c = SKIN_L if B.n(x, y, seed + 1) > 0.6 else SKIN
        if face == "bottom":
            c = SKIN_D
        return c
    return f


def head_paint(face, x, y, w, h):
    """The old abbot's head (8 x 9 x 8): bald and sun-browned; the right half of the skull (texel x < w/2 on the
    front, the viewer's left) is a riveted brass plate with a glowing amber lens for an eye; drooping white brows,
    a white moustache over the beard line, deep wrinkles."""
    plate = B.brass(70)
    if face == "front":
        if x < w // 2 and y <= 4:
            if (x, y) == (2, 4):
                return AMBER                                                           # the lens eye
            if (x, y) in ((1, 4), (3, 4), (2, 3), (2, 5)):
                return GOLD_D                                                          # its bezel
            if (x, y) in ((0, 0), (3, 0), (0, 3)):
                return GOLD_L                                                          # rivets
            return plate(face, x, y, w, h)
        if (x, y) == (w - 3, 4):
            return (40, 60, 70)                                                        # his living eye
        if (x, y) == (w - 2, 4):
            return WHITE
        if y == 3 and x >= w // 2 - 1:
            return BEARD                                                               # the drooping brow
        if y == 3 and x < w // 2 - 1:
            return BEARD_D
        if y == 1 and x >= w // 2 and x % 2 == 0:
            return SKIN_D                                                              # forehead wrinkles
        if y == 5 and x in (w // 2 - 1, w // 2):
            return SKIN_D                                                              # the nose's shadow
        if y == 6:
            return BEARD if 1 <= x <= w - 2 else SKIN_D                                # moustache
        if y >= 7:
            return BEARD if 1 <= x <= w - 2 else BEARD_D                               # the beard's root
        return skin(71)(face, x, y, w, h)
    if face == "right":                                                                # the brass side
        if y <= 5:
            if (x, y) in ((1, 1), (w - 2, 1), (1, 4), (w - 2, 4)):
                return GOLD_L
            if B.cog_mask(x, y - 0, w, 6, teeth=6, hub=0.3) and 1 <= x <= w - 2:
                return mix(GOLD, B.BRASS_D, 0.4)
            return plate(face, x, y, w, h)
        if y >= 7:
            return BEARD_D
        return skin(72)(face, x, y, w, h)
    if face == "top":
        if x < w // 2:
            return GOLD_L if (x + y) % 5 == 0 else plate(face, x, y, w, h)
        return skin(73)(face, x, y, w, h)
    if face == "left":
        if y >= 7:
            return BEARD_D
        if y == 3 and x <= 2:
            return BEARD
        return skin(74)(face, x, y, w, h)
    if face == "back":
        if x >= w // 2 and y <= 5:
            return plate(face, x, y, w, h)
        return skin(75)(face, x, y, w, h)
    return SKIN_D


def head_glow(face, x, y, w, h):
    if face == "front" and (x, y) == (2, 4):
        return AMBER_L
    return None


def beard(face, x, y, w, h):
    if face == "bottom":
        return BEARD_D
    if (x + y // 2) % 3 == 0:
        return BEARD_D
    return BEARD if B.n(x, y, 81) > 0.15 else mix(BEARD, BEARD_D, 0.5)


def brow(face, x, y, w, h):
    return BEARD if (x + y) % 2 else BEARD_D


def bronze(seed=0):
    """Old bronze: warm metal with verdigris crusts in the hollows."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        c = mul(BRONZE, 0.92 + r * 0.2)
        if face == "top":
            c = BRONZE_L if r > 0.4 else BRONZE
        if face == "bottom":
            c = BRONZE_D
        if B.n(x // 2, y // 2, seed + 3) < 0.14 and face != "top":
            c = VERD if r > 0.5 else VERD_D
        return c
    return f


def shaft(face, x, y, w, h):
    """The staff: dark lacquered wood wound with bronze bands, a wider grip near the hand."""
    if face in ("top", "bottom"):
        return BRONZE_D
    if y % 8 in (0, 1):
        return BRONZE_L if y % 8 == 0 else BRONZE
    k = 1.15 if x == w // 2 else 1.0
    return mul(WOOD_D, k + (B.n(x, y, 91) - 0.5) * 0.12)


def dragon_head(face, x, y, w, h):
    """The dragon's head on the staff: bronze scales, a gold brow ridge."""
    if face == "top":
        return GOLD if (x + y) % 3 == 0 else BRONZE_L
    if face == "front" and y == 0:
        return GOLD_L
    if (x + 2 * y) % 4 == 0:
        return BRONZE_D
    return bronze(95)(face, x, y, w, h)


def dragon_eye(face, x, y, w, h):
    return TEAL if (x + y) % 2 == 0 else TEAL_L


def chime_rod(seed=0):
    """A hanging chime rod: polished brass with a bright streak, darker bands, a verdigris tip."""
    def f(face, x, y, w, h):
        if face == "top":
            return GOLD_L
        if face == "bottom" or y == h - 1:
            return VERD
        if y % 4 == 3:
            return GOLD_D
        return GOLD_L if (x + seed) % 2 == 0 else GOLD
    return f


def chime_glow(face, x, y, w, h):
    if face in ("top", "bottom"):
        return None
    return (255, 236, 170) if y % 4 == 1 else None


def halo_seg(face, x, y, w, h):
    return GOLD_L if (x + y) % 4 == 0 else (GOLD if y == 0 else GOLD_D if y == h - 1 else B.BRASS)


def gear(face, x, y, w, h):
    if face not in ("front", "back"):
        return GOLD_D
    if B.cog_mask(x, y, w, h, teeth=8, hub=0.25):
        return GOLD_L if y < h / 2 else GOLD
    return None


def bell(face, x, y, w, h):
    if face == "bottom":
        return mul(GOLD_D, 0.6)
    if y == h - 1:
        return GOLD_L
    return GOLD if x % 2 else mix(GOLD, GOLD_L, 0.5)


def mech(seed=0):
    return B.brass(seed, grad=0.3)


def joint(face, x, y, w, h):
    return B.IRON_L if (x + y) % 2 else B.IRON


# ---------------------------------------------------------------- build
def build():
    m = Model("chime_abbot", seed=811, shadow=1.0, walk_speed=0.8, walk_scale=0.6, glow_pulse=0.04)

    m.part("bone", pivot=(0, 24, 0))
    m.part("float", "bone", pivot=(0, -3, 0))                    # he hovers a hand's breadth over the deck
    m.part("hips", "float", pivot=(0, -21, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("hem", "skirt", pivot=(0, 13, 0))
    m.part("chest", "hips", pivot=(0, -1, 0), rot=(-2, 0, 0))
    m.part("mala", "chest", pivot=(0, -13, -4.6))
    m.part("neck", "chest", pivot=(0, -14, 0))
    m.part("head", "neck", pivot=(0, -1, 0))
    m.part("beard", "head", pivot=(0, -1, -3))
    m.part("halo", "chest", pivot=(0, -21, 5.5))
    m.part("ring", "halo", pivot=(0, 0, 0))
    m.part("rods", "halo", pivot=(0, 0, 0))
    m.part("arm_r", "chest", pivot=(-7.5, -12, 0), rot=(-10, 0, 12))
    m.part("fore_r", "arm_r", pivot=(-0.5, 7, 0), rot=(-38, 0, -8))
    m.part("hand_r", "fore_r", pivot=(0, 12, 0))
    m.part("staff", "hand_r", pivot=(0, 1.5, -0.5), rot=(40, 0, -10))
    m.part("dragon", "staff", pivot=(0, -36, 0))
    m.part("jaw", "dragon", pivot=(0, 0, -3))
    m.part("chimes", "dragon", pivot=(0, 1, -9))
    m.part("arm_l", "chest", pivot=(7.5, -12, 0), rot=(-8, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0.5, 7, 0), rot=(-30, 0, 6))
    m.part("hand_l", "fore_l", pivot=(0, 12, 0))
    m.part("mech_r", "chest", pivot=(-5.5, -5, 0), rot=(-70, 30, 0))
    m.part("mech_l", "chest", pivot=(5.5, -5, 0), rot=(-70, -30, 0))
    m.part("prayer_bell", "chest", pivot=(0, -1, -9))

    # ---- the robes: a white under-robe to the floor, three flaring red tiers open down the front, a gold hem
    m.box("skirt", -5.5, 0, -4.5, 11, 13, 9, white(10))
    m.box("skirt", -6.5, -1, -5, 13, 7, 10, robe(11, panel=3))
    m.box("skirt", -7.5, 5, -6, 15, 8, 12, robe(12, panel=4))
    m.box("hem", -6, -1, -5, 12, 9, 10, white(13))
    m.box("hem", -9, 0, -7, 18, 8, 14, robe(14, panel=5, ragged=0))
    m.box("hem", -9.5, 7, -7.5, 19, 1, 15, robe(15, panel=5))                         # the gold-edged lip
    m.box("skirt", -7, -2.5, -5.5, 14, 4, 11, obi)                                    # the obi
    m.box("skirt", -2, -3, -6.6, 4, 5, 1, B.brass(16))                                # its brass clasp
    m.box("skirt", -1.5, 2, -6.4, 1, 6, 1, GOLD)                                      # the cord ends
    m.box("skirt", 0.5, 2, -6.4, 1, 5, 1, GOLD_D)
    m.box("skirt", 6.5, -1, -4, 2, 13, 7, kasaya)                                     # the kasaya's tail, left hip
    m.box("skirt", 7, 12, -2, 1, 3, 1, GOLD_L)                                        # its tassel
    m.box("skirt", 7, 12, 1, 1, 3, 1, GOLD_L)

    # ---- the bodice, kasaya, mala
    m.box("chest", -5.5, -14, -4, 11, 14, 8, chest_paint)
    m.box("chest", 1.5, -15, -4.5, 7, 4, 9, kasaya)                                   # the kasaya's shoulder fold
    m.box("chest", -8, -14, -3.5, 3, 3, 7, robe(21, tiers=False, hem_trim=False))     # right shoulder
    m.box("chest", 5, -12, -3.5, 3, 2, 7, kasaya)
    beads = [(-4, -1), (-3.6, 2), (-2.6, 5), (-1.2, 7.5), (1.2, 7.5), (2.6, 5), (3.6, 2), (4, -1)]
    for k, (bx, by) in enumerate(beads):
        m.box("mala", bx - 1, by - 1, -1, 2, 2, 2, bead(GOLD if k % 2 else RED_D))
    m.box("mala", -1.5, 9, -1.5, 3, 3, 3, bell)                                       # the mala's bell
    m.box("mala", -0.5, 12, -1, 1, 1, 1, GOLD_D)

    # ---- head: bald, half brass, drooping brows, a long white beard
    m.box("neck", -2, -2, -2, 4, 3, 4, skin(30))
    m.box("head", -4, -9, -4, 8, 9, 8, head_paint, glow=head_glow)
    m.box("head", -5, -6, -3, 1, 3, 4, B.brass(31))                                   # brass ear-plate, right
    m.box("head", -5.5, -5, -2.5, 1, 2, 3, GOLD_L)
    m.box("head", 4, -5, -2, 1, 2, 3, skin(32))                                       # the left ear
    m.box("head", 2, -6, -4.6, 4, 1, 1, brow)                                         # the left brow, drooping out
    m.box("head", 5, -6, -4.6, 2, 1, 1, brow)
    m.box("head", 6, -6, -4.6, 1, 3, 1, brow)
    m.box("head", -6, -6, -4.6, 2, 1, 1, brow)                                        # the right brow over the lens
    m.box("head", -6, -6, -4.6, 1, 2, 1, brow)
    m.box("head", -2, -5, -5.2, 2, 2, 1, (56, 40, 30))                                # lens housing
    m.box("head", -1.7, -4.7, -5.6, 1, 1, 1, AMBER, glow=AMBER_L)
    m.box("beard", -3, 0, -1.5, 6, 6, 2, beard)                                       # the beard, down the chest
    m.box("beard", -2, 6, -1.5, 4, 4, 2, beard)
    m.box("beard", -1, 10, -1.2, 2, 3, 1, beard)
    m.box("beard", -4, -1, -1.6, 2, 3, 1, beard)                                      # moustache tails
    m.box("beard", 2, -1, -1.6, 2, 3, 1, beard)
    m.box("head", -1.5, -10, -1.5, 3, 1, 3, B.brass(33))                              # a brass crown-boss
    m.box("head", -0.5, -11, -0.5, 1, 1, 1, AMBER, glow=AMBER)

    # ---- the halo: a brass ring with a gear hub behind the head; chime rods hang from its lower half
    for k in range(16):
        seg = f"ring_{k}"
        m.part(seg, "ring", pivot=(0, 0, 0), rot=(0, 0, k * 360 / 16))
        m.box(seg, -3, -15, -0.5, 6, 2, 1, halo_seg)
        if k % 2 == 0:
            m.box(seg, -0.5, -16, -1, 1, 1, 2, GOLD_L)                                # studs: you see it turn
    m.box("ring", -3, -3, -0.5, 6, 6, 1, gear)
    m.box("ring", -1, -1, -1.2, 2, 2, 1, AMBER, glow=AMBER)
    for k in range(4):
        spk = f"spoke_{k}"
        m.part(spk, "ring", pivot=(0, 0, 0), rot=(0, 0, 45 + k * 90))
        m.box(spk, -0.5, -14, 0, 1, 11, 1, GOLD_D)
    lengths = (7, 10, 13, 15, 13, 10, 7)
    for k, x in enumerate((-13, -9, -4.5, 0, 4.5, 9, 13)):
        y = math.sqrt(max(0.0, 14.0 ** 2 - x * x))                                    # hung from the ring's lower arc
        rod = f"rod_{k}"
        m.part(rod, "rods", pivot=(x, round(y * 2) / 2, 0.5))
        m.box(rod, -0.5, 0, -0.5, 1, lengths[k], 1, chime_rod(k), glow=chime_glow)
        m.box(rod, -1, -1, -1, 2, 1, 2, GOLD_D)                                       # its cap
    for x in (-14.5, 14.5):
        m.box("rods", x - 1, -1.5, 0, 2, 3, 2, bell)                                    # bells at the ring's sides

    # ---- right arm: a wide red sleeve, a brass mechanical forearm round the dragon staff
    m.box("arm_r", -3, -2, -3, 5, 9, 6, sleeve(40))
    m.box("fore_r", -4, 0, -4, 7, 10, 8, sleeve(41))                                  # the hanging sleeve
    m.box("fore_r", -1.5, 7, -1.5, 3, 5, 3, mech(42))                                 # the mechanical forearm
    m.box("fore_r", -2, 9, -2, 4, 1, 4, joint)
    m.box("hand_r", -2, 0, -2, 4, 3, 4, mech(43))
    m.box("hand_r", -2.5, 0.5, -1, 1, 2, 2, joint)
    # the staff: lacquered wood banded in bronze, a bronze foot, the dragon's head on top
    m.box("staff", -1, -34, -1, 2, 52, 2, shaft)
    m.box("staff", -1.5, 18, -1.5, 3, 2, 3, bronze(50))
    m.box("staff", -0.5, 20, -0.5, 1, 2, 1, BRONZE_D)
    m.box("staff", -1.5, -36, -1.5, 3, 3, 3, bronze(51))
    m.box("dragon", -2.5, -6, -4, 5, 5, 8, dragon_head)                                # the skull
    m.box("dragon", -2, -5, -9, 4, 3, 5, dragon_head)                                  # the snout
    m.box("dragon", -1.5, -5.6, -9.5, 3, 1, 2, GOLD)                                   # nostril ridge
    m.box("dragon", -3, -5, -3, 1, 1, 1, dragon_eye, glow=dragon_eye)
    m.box("dragon", 2, -5, -3, 1, 1, 1, dragon_eye, glow=dragon_eye)
    m.box("dragon", -2.5, -10, 1, 1, 4, 1, GOLD_L)                                     # horns, swept back
    m.box("dragon", 1.5, -10, 1, 1, 4, 1, GOLD_L)
    m.box("dragon", -2.5, -11, 2, 1, 1, 2, GOLD_L)
    m.box("dragon", 1.5, -11, 2, 1, 1, 2, GOLD_L)
    m.box("dragon", -1.5, -7, -2, 3, 1, 6, GOLD)                                       # the mane crest
    m.box("dragon", -1, -6, 4, 2, 4, 2, bronze(52))                                    # the neck into the staff
    m.box("dragon", -3.5, -3, -8, 1, 1, 4, GOLD_L)                                     # whiskers
    m.box("dragon", 2.5, -3, -8, 1, 1, 4, GOLD_L)
    m.box("dragon", -3.5, -2, -5, 1, 3, 1, GOLD)
    m.box("dragon", 2.5, -2, -5, 1, 3, 1, GOLD)
    m.box("jaw", -2, 0, -6, 4, 1, 6, dragon_head)                                      # the lower jaw
    m.box("jaw", -1.5, -1, -6, 1, 1, 1, WHITE)                                         # fangs
    m.box("jaw", 0.5, -1, -6, 1, 1, 1, WHITE)
    m.box("chimes", -2, 0, -0.5, 4, 1, 1, GOLD)                                        # a ring of chimes in its jaws
    for k, (x, ln) in enumerate(((-1.5, 4), (0, 5), (1.5, 4))):
        m.box("chimes", x - 0.5, 1, -0.5, 1, ln, 1, chime_rod(k + 3), glow=chime_glow)

    # ---- left arm: the sleeve, the brass forearm, an open hand for the palm strike
    m.box("arm_l", -2, -2, -3, 5, 9, 6, sleeve(60))
    m.box("fore_l", -3, 0, -4, 7, 10, 8, sleeve(61))
    m.box("fore_l", -1.5, 7, -1.5, 3, 5, 3, mech(62))
    m.box("fore_l", -2, 9, -2, 4, 1, 4, joint)
    m.box("hand_l", -2, 0, -1.5, 4, 3, 3, mech(63))                                    # the palm
    for k, x in enumerate((-2, -0.7, 0.6, 1.9)):
        m.box("hand_l", x, 3, -1, 1, 3 if k in (1, 2) else 2, 1, mech(64 + k))         # fingers
    m.box("hand_l", 2.5, 0.5, -1.5, 1, 2, 1, mech(68))                                 # the thumb

    # ---- the second pair of clockwork arms, folded out from under the sleeves, holding a prayer bell
    for side, part in ((-1, "mech_r"), (1, "mech_l")):
        m.box(part, -1, -1, -1, 2, 2, 2, joint)
        m.box(part, -0.5, 0, -0.5, 1, 7, 1, B.rod(B.BRASS, 70))
        m.box(part, -1, 6, -1, 2, 2, 2, joint)
        m.box(part, -1, 7.5, -1.5, 2, 2, 1, mech(71))                                  # pincer
    m.box("prayer_bell", -1.5, -1, -1.5, 3, 3, 3, bell)
    m.box("prayer_bell", -0.5, -2, -0.5, 1, 1, 1, GOLD_L)
    m.box("prayer_bell", -0.5, 2, -0.5, 1, 1, 1, GOLD_D)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("float", (0, (0, 0, 0)), (2.0, (0, 1.4, 0)), (4.0, (0, 0, 0)))
    idle.rot("ring", (0, (0, 0, 0)), (2.0, (0, 0, 180)), (4.0, (0, 0, 360)))
    for k in range(7):
        idle.rot(f"rod_{k}", (0, (0, 0, 0)), (1.0 + k * 0.3, (6 if k % 2 else -6, 0, 5 if k % 2 else -5)),
                 (4.0, (0, 0, 0)))
    idle.rot("hem", (0, (0, 0, 0)), (2.0, (3, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (2.0, (5, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.3, (2, 8, 0)), (2.7, (-1, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("fore_l", (0, (0, 0, 0)), (2.0, (-5, 0, 3)), (4.0, (0, 0, 0)))
    idle.rot("chimes", (0, (0, 0, 0)), (2.0, (12, 0, 4)), (4.0, (0, 0, 0)))
    idle.rot("prayer_bell", (0, (0, 0, 0)), (1.0, (0, 0, 10)), (3.0, (0, 0, -10)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.4)
    walk.rot("float", (0, (6, 0, 0)), (1.2, (6, 0, 0)), (2.4, (6, 0, 0)))             # he glides, leaning in
    walk.rot("hem", (0, (12, 3, 0)), (1.2, (12, -3, 0)), (2.4, (12, 3, 0)))
    walk.rot("fore_r", (0, (8, 0, 0)), (1.2, (12, 0, 0)), (2.4, (8, 0, 0)))
    walk.rot("fore_l", (0, (10, 0, 0)), (1.2, (14, 0, 0)), (2.4, (10, 0, 0)))
    walk.rot("beard", (0, (14, 0, 0)), (2.4, (14, 0, 0)))
    for k in range(7):
        walk.rot(f"rod_{k}", (0, (14, 0, 0)), (1.2, (18, 0, 0)), (2.4, (14, 0, 0)))

    # staff (14 / 26 / 14): the dragon staff swung back over the right shoulder (0.7 s), a forehand sweep at 0.7 s, a
    # turn and a backhand at 1.3 s, an overhead slam at 1.8 s (the slam only in phase 2)
    a = m.anim("staff", 2.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-100, -30, 60)), (0.7, (-106, -32, 64)), (0.78, (-70, 40, -40), "linear"),
          (1.2, (-76, 56, -50)), (1.3, (-70, -30, 46), "linear"), (1.6, (-150, 0, 10)), (1.8, (-156, 0, 10)),
          (1.86, (-60, 0, 6), "linear"), (2.1, (-60, 0, 6)), (2.7, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.7, (10, 0, 0)), (0.78, (50, 0, 0), "linear"), (1.3, (50, 0, 0)),
          (1.6, (30, 0, 0)), (1.86, (90, 0, 0), "linear"), (2.1, (90, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, 34, 0)), (0.78, (6, -30, 0), "linear"), (1.2, (4, -34, 0)),
          (1.3, (6, 28, 0), "linear"), (1.6, (-10, 0, 0)), (1.8, (-12, 0, 0)), (1.86, (16, 0, 0), "linear"),
          (2.1, (14, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-20, 0, -40)), (1.3, (-20, 0, -50)), (2.1, (-30, 0, -20)), (2.7, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.78, (0, -14, 0)), (1.3, (0, 14, 0)), (1.86, (10, 0, 0)), (2.7, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (1.8, (0, 3, 0)), (1.86, (0, -1, -2), "linear"), (2.1, (0, -1, -2)),
          (2.7, (0, 0, 0)))

    # palm (18 / 6 / 16): he draws the open left palm back to the hip, gathering wind (0.9 s), then drives it out:
    # a cone of wind ahead
    a = m.anim("palm", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (30, 0, -10)), (0.9, (34, 0, -12)), (0.96, (-90, 0, 0), "linear"),
          (1.3, (-90, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (-60, 0, 0)), (0.96, (0, 0, 0), "linear"), (1.3, (0, 0, 0)),
          (2.0, (0, 0, 0)))
    a.rot("hand_l", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (0.96, (-80, 0, 0), "linear"), (1.3, (-80, 0, 0)),
          (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-6, -30, 0)), (0.96, (10, 20, 0), "linear"), (1.3, (8, 18, 0)),
          (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-30, 0, 30)), (0.96, (10, 0, 20), "linear"), (2.0, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (0.9, (0, 0, 2)), (0.96, (0, 0, -4), "linear"), (1.3, (0, 0, -4)),
          (2.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.96, (-10, 0, 0)), (1.3, (-8, 0, 0)), (2.0, (0, 0, 0)))

    # chimering (20 / 44 / 16): he spreads both arms and the halo blazes (1.0 s), then the chime rods fly out of it
    # to hang in a circle round him; he holds the pose, conducting, while they ring one after another
    a = m.anim("chimering", 4.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-40, 0, 70)), (1.0, (-44, 0, 74)), (1.06, (-60, 0, 90), "linear"),
          (2.4, (-80, 0, 90)), (3.2, (-60, 0, 80)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -70)), (1.0, (-44, 0, -74)), (1.06, (-60, 0, -90), "linear"),
          (2.4, (-80, 0, -90)), (3.2, (-60, 0, -80)), (4.0, (0, 0, 0)))
    a.rot("ring", (0, (0, 0, 0)), (1.0, (0, 0, 540)), (3.2, (0, 0, 1080)), (4.0, (0, 0, 1080)))
    a.scale("halo", (0, (1, 1, 1)), (1.0, (1.35, 1.35, 1.35)), (1.06, (1.1, 1.1, 1.1), "linear"), (3.2, (1.1, 1.1, 1.1)),
            (4.0, (1, 1, 1)))
    a.scale("rods", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.06, (0.1, 0.1, 0.1), "linear"), (3.2, (0.1, 0.1, 0.1)),
            (3.6, (1, 1, 1)), (4.0, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.06, (-10, 0, 0), "linear"), (3.2, (-10, 0, 0)),
          (4.0, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (1.0, (0, 4, 0)), (3.2, (0, 5, 0)), (4.0, (0, 0, 0)))

    # petals (22 / 30 / 14): he whirls the staff overhead faster and faster (1.1 s), then sweeps it round: a ring
    # of cherry petals bursts out over the deck
    a = m.anim("petals", 3.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-150, 0, 20)), (1.1, (-170, 0, 10)), (1.16, (-90, 0, 60), "linear"),
          (2.6, (-90, 0, 60)), (3.3, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.5, (90, 0, 0)), (1.1, (90, 720, 0)), (1.16, (90, 760, 0), "linear"),
          (2.6, (90, 1080, 0)), (3.3, (0, 1080, 0)))
    a.rot("float", (0, (0, 0, 0)), (1.1, (0, -30, 0)), (1.16, (0, 20, 0), "linear"), (2.6, (0, 360, 0)),
          (3.3, (0, 360, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.1, (-30, 0, -60)), (2.6, (-30, 0, -70)), (3.3, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.1, (0, 20, 0)), (1.16, (0, -30, 0), "linear"), (2.6, (6, -20, 0)), (3.3, (0, 0, 0)))
    a.scale("hem", (0, (1, 1, 1)), (1.1, (1.1, 1, 1.1)), (1.16, (1.35, 0.9, 1.35), "linear"), (2.6, (1.2, 0.95, 1.2)),
            (3.3, (1, 1, 1)))

    # step (12 / 4 / 10): he draws into himself, sleeves wrapped round him (0.6 s), and scatters into a gust of
    # petals; he reappears at a corner of the deck
    a = m.anim("step", 1.3)
    a.scale("float", (0, (1, 1, 1)), (0.5, (0.8, 1.1, 0.8)), (0.6, (0.6, 1.2, 0.6)), (0.66, (0.15, 1.4, 0.15), "linear"),
            (0.85, (0.8, 1.05, 0.8)), (1.3, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, -40)), (0.85, (-40, 0, -40)), (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-40, 0, 40)), (0.85, (-40, 0, 40)), (1.3, (0, 0, 0)))
    a.rot("float", (0, (0, 0, 0)), (0.6, (0, 180, 0)), (0.66, (0, 240, 0), "linear"), (1.3, (0, 360, 0)))

    # flurry (phase 2, 14 / 34 / 14): three thrusts of the dragon staff at 0.7, 1.1 and 1.5 s, then a full spin at 2.0
    a = m.anim("flurry", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 30)), (0.7, (-44, 0, 30)), (0.76, (-90, 0, 4), "linear"),
          (0.95, (-50, 0, 20)), (1.1, (-54, 0, 20)), (1.16, (-92, 0, 4), "linear"), (1.35, (-50, 0, 20)),
          (1.5, (-54, 0, 20)), (1.56, (-94, 0, 4), "linear"), (1.8, (-80, 0, 70)), (2.0, (-82, 0, 74)),
          (2.06, (-82, 0, 80), "linear"), (2.4, (-80, 0, 70)), (3.1, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (0.7, (110, 0, 0)), (1.5, (110, 0, 0)), (1.8, (90, 0, 0)), (2.4, (90, 0, 0)),
          (3.1, (0, 0, 0)))
    a.rot("float", (0, (0, 0, 0)), (1.8, (0, 0, 0)), (2.0, (0, 40, 0)), (2.06, (0, -360, 0), "linear"),
          (2.4, (0, -360, 0)), (3.1, (0, -360, 0)))
    a.pos("float", (0, (0, 0, 0)), (0.7, (0, 0, 1)), (0.76, (0, 0, -3), "linear"), (1.1, (0, 0, 1)),
          (1.16, (0, 0, -3), "linear"), (1.5, (0, 0, 1)), (1.56, (0, 0, -3), "linear"), (2.0, (0, 0, 0)),
          (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 20, 0)), (0.76, (12, 0, 0), "linear"), (1.1, (-6, 20, 0)),
          (1.16, (12, 0, 0), "linear"), (1.5, (-6, 20, 0)), (1.56, (12, 0, 0), "linear"), (2.4, (4, 0, 0)),
          (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-20, 0, -40)), (2.4, (-20, 0, -40)), (3.1, (0, 0, 0)))

    # bellcrash (phase 2, 20 / 20 / 18): he gathers himself and soars up (1.0 s), hangs over the deck, then drops onto
    # the marked spot at 1.5 s, staff first
    a = m.anim("bellcrash", 2.9)
    a.pos("float", (0, (0, 0, 0)), (0.6, (0, -3, 0)), (1.0, (0, 40, 0)), (1.4, (0, 44, 0)), (1.5, (0, -2, 0), "linear"),
          (2.0, (0, -2, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-20, 0, 20)), (1.0, (-170, 0, 10)), (1.4, (-172, 0, 10)),
          (1.5, (-60, 0, 6), "linear"), (2.0, (-60, 0, 6)), (2.9, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.0, (20, 0, 0)), (1.4, (20, 0, 0)), (1.5, (100, 0, 0), "linear"),
          (2.0, (100, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-30, 0, -80)), (1.5, (-30, 0, -60)), (2.9, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.4, (20, 0, 0)), (1.5, (-10, 0, 0), "linear"), (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.4, (-10, 0, 0)), (1.5, (20, 0, 0), "linear"), (2.0, (18, 0, 0)), (2.9, (0, 0, 0)))

    # awaken (phase 3, 40 / 20 / 20): he rises, arms spread, the halo spinning ever faster, the dragon staff held high
    # (2.0 s), then the brass dragon's spirit tears free
    a = m.anim("awaken", 4.0)
    a.pos("float", (0, (0, 0, 0)), (1.6, (0, 14, 0)), (2.0, (0, 16, 0)), (2.06, (0, 10, 0), "linear"), (3.2, (0, 8, 0)),
          (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-120, 0, 30)), (2.0, (-176, 0, 10)), (2.06, (-160, 0, 30), "linear"),
          (3.2, (-160, 0, 30)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-60, 0, -70)), (2.0, (-70, 0, -80)), (2.06, (-90, 0, -60), "linear"),
          (3.2, (-90, 0, -60)), (4.0, (0, 0, 0)))
    a.rot("ring", (0, (0, 0, 0)), (2.0, (0, 0, 1440)), (4.0, (0, 0, 2160)))
    a.scale("halo", (0, (1, 1, 1)), (2.0, (1.4, 1.4, 1.4)), (2.06, (1.7, 1.7, 1.7), "linear"), (3.2, (1.3, 1.3, 1.3)),
            (4.0, (1, 1, 1)))
    a.scale("dragon", (0, (1, 1, 1)), (2.0, (1.5, 1.5, 1.5)), (2.06, (1.9, 1.9, 1.9), "linear"), (3.2, (1.4, 1.4, 1.4)),
            (4.0, (1, 1, 1)))
    a.rot("jaw", (0, (0, 0, 0)), (2.0, (30, 0, 0)), (2.06, (40, 0, 0), "linear"), (3.2, (30, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (-36, 0, 0), "linear"), (3.2, (-26, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.6, (0, 30, 0)), (2.0, (-10, 50, 0)), (2.06, (16, 70, 0), "linear"),
          (3.2, (10, 30, 0)), (4.0, (0, 0, 0)))

    # breath (phase 3, 20 / 40 / 16): he points the dragon staff at the far side of the deck (1.0 s), its jaws open,
    # and conducts the spirit dragon's passes with it
    a = m.anim("breath", 3.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-120, 20, 20)), (1.0, (-124, 20, 22)), (1.06, (-96, 0, 10), "linear"),
          (1.5, (-100, 30, 10)), (2.0, (-100, -30, 10)), (2.5, (-100, 30, 10)), (3.0, (-96, 0, 10)), (3.8, (0, 0, 0)))
    a.rot("staff", (0, (0, 0, 0)), (1.0, (120, 0, 0)), (1.06, (140, 0, 0), "linear"), (3.0, (140, 0, 0)),
          (3.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (3.0, (40, 0, 0)), (3.8, (0, 0, 0)))
    a.scale("dragon", (0, (1, 1, 1)), (1.0, (1.4, 1.4, 1.4)), (3.0, (1.4, 1.4, 1.4)), (3.8, (1, 1, 1)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-60, 0, -40)), (3.0, (-60, 0, -40)), (3.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-8, 10, 0)), (1.06, (6, 0, 0), "linear"), (3.0, (6, 0, 0)), (3.8, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (1.0, (0, 5, 0)), (3.0, (0, 5, 0)), (3.8, (0, 0, 0)))

    # roar (phase two): arms flung wide, head thrown back, every chime rod swinging out, the halo flaring
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (1.4, 1.4, 1.4)), (1.6, (1.3, 1.3, 1.3)), (2.0, (1, 1, 1)))
    for k in range(7):
        a.rot(f"rod_{k}", (0, (0, 0, 0)), (0.5, (-40, 0, (k - 3) * 12)), (1.6, (-30, 0, (k - 3) * 10)), (2.0, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (0.5, (0, 4, 0)), (1.6, (0, 4, 0)), (2.0, (0, 0, 0)))

    # stagger: he sinks to the deck, slumped over the staff, the halo tilting, the rods jangling
    a = m.anim("stagger", 2.0)
    a.pos("float", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -14)), (1.6, (26, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-30, 0, 10)), (1.6, (-30, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (1.6, (20, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("halo", (0, (0, 0, 0)), (0.3, (10, 0, 20)), (1.6, (10, 0, 20)), (2.0, (0, 0, 0)))
    for k in range(7):
        a.rot(f"rod_{k}", (0, (0, 0, 0)), (0.3, (20, 0, (3 - k) * 8)), (0.8, (-10, 0, (k - 3) * 6)),
              (1.6, (4, 0, 0)), (2.0, (0, 0, 0)))
