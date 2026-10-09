"""The Corsair Captain (La Capitaine corsaire): the sky-pirate who took the moored airship of the Airship Graveyard and
never came down from its top deck, about 4.8 blocks tall.

Silhouette idea: a tall, lean captain under a spinning rotor. A long teal greatcoat with two rows of brass buttons,
turned-back brass cuffs and gold epaulettes, its tails reaching her boots and streaming in the wind; buff breeches,
tall black boots with turned-down cuffs, a red sash knotted on the left hip and a bandolier of brass flare
cartridges across the chest. A tricorn of black leather edged in brass, brass aviator goggles with sky-blue lenses
strapped over its front, a white plume; a long auburn braid and a red scarf blowing back. On her back a brass rotor
engine whose mast rises over the hat to a four-blade rotor (always turning). Asymmetry: her RIGHT hand holds a
basket-hilted cutlass, her LEFT a heavy brass harpoon gun with a drum magazine, a barbed harpoon in its muzzle and a
red flare canister slung under the barrel.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

COAT = (38, 74, 86)            # teal greatcoat
COAT_L = (64, 106, 116)
COAT_D = (22, 46, 56)
COAT_DD = (14, 30, 38)
LINING = (150, 40, 40)         # crimson lining
GOLD = (236, 190, 84)
GOLD_L = (255, 232, 150)
GOLD_D = (160, 116, 40)
BUFF = (196, 170, 126)         # breeches
BUFF_D = (150, 126, 90)
BOOT = (34, 28, 28)
BOOT_L = (70, 58, 54)
BOOT_D = (20, 16, 16)
SKIN = (222, 176, 146)
SKIN_D = (180, 132, 106)
SKIN_L = (240, 200, 172)
HAIR = (150, 64, 34)
HAIR_L = (196, 98, 52)
HAIR_D = (100, 40, 22)
SCARF = (178, 42, 40)
SCARF_L = (220, 76, 64)
SCARF_D = (120, 24, 26)
HAT = (30, 26, 28)
HAT_L = (62, 54, 56)
SKY = (110, 200, 240)          # goggle lenses
SKY_L = (200, 240, 255)
PLUME = (236, 232, 222)
PLUME_D = (190, 184, 172)
STEEL = (176, 182, 192)
STEEL_L = (226, 232, 240)
STEEL_D = (110, 116, 128)
FLARE = (230, 70, 40)
FLARE_L = (255, 170, 80)
SHIRT = (226, 216, 196)


# ---------------------------------------------------------------- paint
def coat(seed=0, buttons=False, hem=False, cuff=False):
    """Teal broadcloth: soft vertical folds, darker toward the bottom. ``buttons``: two rows of brass buttons down the
    front with dark button-holes and a crimson lapel edge; ``hem``: a gold braid at the bottom; ``cuff``: none."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return COAT_DD
        if face == "top":
            return COAT_L if (x + y) % 4 == 0 else COAT
        if hem and y >= h - 2:
            return GOLD if (x + y) % 2 == 0 or y == h - 1 else GOLD_D
        fold = (x + int(B.n(x // 3, 1, seed) * 2)) % 5
        c = (COAT_L, COAT, COAT, COAT_D, COAT)[fold]
        c = mul(c, 1.08 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if buttons and face == "front":
            cx = (w - 1) / 2
            dx = abs(x - cx)
            if dx < 1.0:
                return COAT_DD                                                      # the closing seam
            if 1.0 <= dx < 2.0:
                return mix(LINING, c, 0.25)                                         # crimson lapel edge
            if round(dx) == 4 and y % 4 == 1 and y < h - 2:
                return GOLD_L if y % 8 == 1 else GOLD                               # brass buttons
            if round(dx) == 4 and y % 4 == 2 and y < h - 2:
                return GOLD_D
        return c
    return f


def lapel(face, x, y, w, h):
    """The turned-back lapels: crimson lining with a gold edge."""
    if face in ("top", "bottom"):
        return mul(LINING, 0.8)
    if x == 0 or x == w - 1:
        return GOLD_D
    return LINING if (x + y) % 5 else mul(LINING, 0.85)


def braid(face, x, y, w, h):
    """Gold braid (cuffs, epaulette edges, hat trim)."""
    if face == "bottom":
        return GOLD_D
    if face == "top" or y == 0:
        return GOLD_L
    if y == h - 1:
        return GOLD_D
    return GOLD if (x + y) % 2 else mix(GOLD, GOLD_L, 0.4)


def epaulette(face, x, y, w, h):
    """A gold epaulette board with a fringe of bullion hanging off its sides."""
    if face == "top":
        if x in (0, w - 1) or y in (0, h - 1):
            return GOLD_D
        return GOLD_L if (x + y) % 3 == 0 else GOLD
    if face == "bottom":
        return GOLD_D
    return GOLD if x % 2 == 0 else GOLD_D


def breeches(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return BUFF_D
        c = mul(BUFF, 1.05 - 0.15 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
        if face in ("left", "right") and x == w // 2:
            return mul(BUFF_D, 0.9)                                                 # the side seam
        return c
    return f


def boot(seed=0, cuff=False):
    """Black riding leather with a highlight down the shin; ``cuff`` is the turned-down brown top."""
    def f(face, x, y, w, h):
        if cuff:
            if face == "top":
                return BOOT_D
            return mix(B.LEATHER, BOOT_L, 0.4) if (x + y) % 4 else B.LEATHER
        if face == "bottom":
            return BOOT_D
        if face == "top":
            return BOOT_L
        k = 1.5 if (face == "front" and x in (w // 2, w // 2 - 1) and y < h - 2) else 1.0
        c = mul(BOOT, k + (B.n(x, y, seed) - 0.5) * 0.15)
        if y == h - 1:
            return BOOT_D
        return c
    return f


def sole(face, x, y, w, h):
    if face == "bottom":
        return BOOT_D
    if y == h - 1:
        return (52, 36, 26)                                                         # the heel and welt
    return boot(9)(face, x, y, w, h)


def sash(face, x, y, w, h):
    if face in ("top", "bottom"):
        return SCARF_D
    return SCARF_L if (x + 2 * y) % 5 == 0 else (SCARF if y % 3 else SCARF_D)


def belt(face, x, y, w, h):
    if face == "front" and abs(x - (w - 1) / 2) < 1.6:
        return GOLD_L if y in (0, h - 1) else GOLD                                  # the buckle
    return B.LEATHER if y not in (0, h - 1) else mul(B.LEATHER, 0.7)


def bandolier(face, x, y, w, h):
    """A leather strap of brass flare cartridges with red caps."""
    if face in ("left", "right", "bottom", "top"):
        return mul(B.LEATHER, 0.8)
    if y % 3 == 0:
        return mul(B.LEATHER, 0.75)
    return FLARE if y % 3 == 1 and x in (1, 2) else (GOLD if x in (1, 2) else B.LEATHER)


def shirt(face, x, y, w, h):
    """The frilled stock at the throat."""
    return SHIRT if (x + y) % 3 else mul(SHIRT, 0.88)


def skin(seed=0):
    def f(face, x, y, w, h):
        return mul(SKIN, 1.02 + (B.n(x, y, seed) - 0.5) * 0.06)
    return f


def face_paint(face, x, y, w, h):
    """The front of the head (10 x 10): the hat's shadow, sharp brows, grey-blue eyes, a scar over the left cheek, a
    thin smirk; braid-coloured hair framing the sides."""
    if face in ("left", "right"):
        if x <= 1 or y <= 3 or (face == "left" and x >= w - 3):
            return HAIR if (x + y) % 3 else HAIR_D
        if 4 <= y <= 6 and 4 <= x <= 5:
            return SKIN_D                                                           # the ear
        return skin(3)(face, x, y, w, h)
    if face == "back":
        return HAIR_L if (x + 2 * y) % 5 == 0 else (HAIR if (x + y) % 3 else HAIR_D)
    if face == "top":
        return HAIR
    if face == "bottom":
        return SKIN_D
    if y == 0:
        return HAIR_D                                                               # the fringe under the brim
    if y == 1:
        return HAIR if x in (0, 1, w - 2, w - 1) else mul(SKIN_D, 0.85)
    if x in (0, w - 1):
        return HAIR                                                                 # hair framing the face
    if y == 3 and x in (2, 3, 6, 7):
        return HAIR_D                                                               # brows, a sharp angle
    if y == 4 and x in (2, 3, 6, 7):
        return (238, 238, 232) if x in (2, 7) else (70, 110, 140)                  # eyes
    if y == 5 and x in (2, 3, 6, 7):
        return SKIN_D
    if x == 7 and y in (5, 6, 7):
        return (196, 120, 110)                                                      # the scar on her left cheek
    if y in (5, 6) and x in (4, 5):
        return SKIN_D if y == 6 else SKIN_L                                         # the nose
    if y == 8 and 3 <= x <= 6:
        return (150, 70, 66) if x != 6 else (170, 90, 80)                          # the smirk
    return skin(4)(face, x, y, w, h)


def hat(seed=0, trim=False):
    """Black leather, a faint grain; ``trim``: the brass edge along the top."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(HAT, 0.7)
        if trim and (y == 0 or face == "top" and (x in (0, w - 1) or y in (0, h - 1))):
            return GOLD
        c = mul(HAT, 1.0 + (B.n(x, y, seed) - 0.5) * 0.25)
        if face == "top" and (x + y) % 5 == 0:
            c = HAT_L
        return c
    return f


def goggle_band(face, x, y, w, h):
    return mul(B.LEATHER, 0.85) if y % 2 else B.LEATHER


def plume(face, x, y, w, h):
    if face in ("top", "bottom"):
        return PLUME_D
    if x == w // 2:
        return PLUME_D                                                              # the quill
    return PLUME if (y + x) % 3 else mix(PLUME, PLUME_D, 0.5)


def hair_braid(face, x, y, w, h):
    if face in ("top", "bottom"):
        return HAIR_D
    if y % 3 == 0:
        return HAIR_D
    return HAIR_L if (x + y) % 3 == 0 else HAIR


def scarf(face, x, y, w, h):
    if y >= h - 2 and x % 2 == 0:
        return None                                                                 # frayed end
    if face in ("top", "bottom"):
        return SCARF_D
    return SCARF_L if (x + y) % 4 == 0 else (SCARF if y % 4 else SCARF_D)


def glove(face, x, y, w, h):
    return mul(B.LEATHER, 0.75) if (x + y) % 4 == 0 else mul(B.LEATHER, 0.95)


def blade(face, x, y, w, h):
    """The cutlass blade: bright steel with a darker spine and a light edge."""
    if face in ("left", "right"):
        if y == 0:
            return STEEL_D                                                          # the spine
        if y == h - 1:
            return STEEL_L                                                          # the edge
        return STEEL if (x + y) % 5 else STEEL_L
    return STEEL_D if face == "top" else STEEL_L


def basket(face, x, y, w, h):
    """The brass basket hilt: bars with gaps."""
    if face in ("top", "bottom"):
        return GOLD_D
    return GOLD_L if (x + y) % 2 == 0 else GOLD_D


def barrel(seed=0):
    """The harpoon gun's barrel: dark iron banded in brass."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            if face == "front" and 0 < x < w - 1 and 0 < y < h - 1:
                return B.SOOT                                                       # the bore
            return B.BRASS_D
        bandpos = y if face in ("left", "right") else x
        if face in ("left", "right"):
            bandpos = x
        if face in ("top", "bottom"):
            bandpos = y
        if bandpos % 6 == 0:
            return B.BRASS_L if face == "top" else B.BRASS
        return mul(B.IRON_L, 1.15 if face == "top" else (0.8 if face == "bottom" else 1.0))
    return f


def drum(face, x, y, w, h):
    return B.copper(71)(face, x, y, w, h) if (x + y) % 4 else B.COPPER_L


def canister(face, x, y, w, h):
    if face in ("front", "back"):
        return FLARE_L
    return FLARE if (x + y) % 3 else mul(FLARE, 0.8)


def canister_glow(face, x, y, w, h):
    return FLARE_L if face == "front" else None


def lens(face, x, y, w, h):
    if face != "front":
        return B.BRASS_D
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if y == 0 else B.BRASS
    return SKY_L if (x, y) == (1, 1) else SKY


def lens_glow(face, x, y, w, h):
    if face != "front" or x in (0, w - 1) or y in (0, h - 1):
        return None
    return SKY_L if (x, y) == (1, 1) else SKY


def rotor_blade(face, x, y, w, h):
    """A rotor blade: lacquered mahogany with a brass tip."""
    if x <= 1 or x >= w - 2:
        return B.BRASS_L if face == "top" else B.BRASS
    if face == "top":
        return B.MAHOGANY if (x // 2) % 2 else mix(B.MAHOGANY, (200, 140, 100), 0.25)
    return B.MAHOGANY_D


def rotor_blade_z(face, x, y, w, h):
    """The same blade laid along z (its long axis runs along the texture's y on the top face)."""
    if face == "top":
        if y <= 1 or y >= h - 2:
            return B.BRASS_L
        return B.MAHOGANY if (y // 2) % 2 else mix(B.MAHOGANY, (200, 140, 100), 0.25)
    if x <= 1 or x >= w - 2:
        return B.BRASS
    return B.MAHOGANY_D


def engine(face, x, y, w, h):
    """The rotor engine on her back: a brass casing, a gauge on the back face, a glowing vent grille below it."""
    if face == "back":
        cx = (w - 1) / 2
        if 2 <= y <= 5 and abs(x - cx) <= 2:
            return B.gauge()(face, int(x - cx + 2), y - 2, 5, 4)
        if h - 5 <= y <= h - 3 and 1 <= x <= w - 2:
            return B.AMBER if x % 2 else B.SOOT                                     # the vent
    return B.brass(81, rivet_step=3)(face, x, y, w, h)


def engine_glow(face, x, y, w, h):
    if face == "back" and h - 5 <= y <= h - 3 and 1 <= x <= w - 2 and x % 2:
        return B.AMBER
    return None


# ---------------------------------------------------------------- build
def build():
    m = Model("corsair_captain", seed=919, shadow=1.0, walk_speed=0.9, walk_scale=0.7, glow_pulse=0.04)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -32, 0))
    m.part("leg_r", "hips", pivot=(-3.6, 1, 0))
    m.part("shin_r", "leg_r", pivot=(0, 15, 0))
    m.part("leg_l", "hips", pivot=(3.6, 1, 0))
    m.part("shin_l", "leg_l", pivot=(0, 15, 0))
    m.part("tail_b", "hips", pivot=(0, 0, 4.5), rot=(6, 0, 0))
    m.part("tail_r", "hips", pivot=(-6.5, 0, 0), rot=(0, 0, 4))
    m.part("tail_l", "hips", pivot=(6.5, 0, 0), rot=(0, 0, -4))
    m.part("chest", "hips", pivot=(0, -2, 0))
    m.part("neck", "chest", pivot=(0, -22, 0))
    m.part("head", "neck", pivot=(0, -2, 0))
    m.part("plume", "head", pivot=(6, -14, 2), rot=(-25, 0, 18))
    m.part("braid", "head", pivot=(2.5, -3, 4.5), rot=(18, 0, -6))
    m.part("braid_end", "braid", pivot=(0, 9, 0), rot=(8, 0, 0))
    m.part("scarf", "neck", pivot=(-1, -1, 4), rot=(55, 0, 8))
    m.part("scarf_end", "scarf", pivot=(0, 9, 0), rot=(18, 0, 0))
    m.part("pack", "chest", pivot=(0, -14, 4.5))
    m.part("rotor", "pack", pivot=(0, -36, 3))
    m.part("arm_r", "chest", pivot=(-9, -20, 0), rot=(-6, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 11, 0), rot=(-30, 0, 0))
    m.part("cutlass", "fore_r", pivot=(0, 11, -0.5), rot=(40, 0, 0))
    m.part("tip", "cutlass", pivot=(0, 0, -13), rot=(-14, 0, 0))
    m.part("arm_l", "chest", pivot=(9, -20, 0), rot=(-14, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-62, 0, 0))
    m.part("gun", "fore_l", pivot=(0, 11, 0), rot=(70, 0, 0))

    # ---- legs: buff breeches, tall black boots with turned-down cuffs
    for s, leg, shin in ((-1, "leg_r", "shin_r"), (1, "leg_l", "shin_l")):
        m.box(leg, -3, 0, -3, 6, 16, 6, breeches(10 + s))
        m.box(shin, -3.5, 0, -3.5, 7, 13, 7, boot(12 + s))
        m.box(shin, -4, -1, -4, 8, 3, 8, boot(14 + s, cuff=True))
        m.box(shin, -3.5, 13, -6.5, 7, 3, 10, sole)

    # ---- the hips: belt, sash knotted on the left, the coat's long tails
    m.box("hips", -7, -2, -4.5, 14, 4, 9, coat(20))
    m.box("hips", -7.5, -3, -5, 15, 3, 10, belt)
    m.box("hips", -7.6, -1, -4.8, 15, 2, 10, sash)
    m.box("hips", 6.5, -1, -3, 2, 9, 2, sash)                                          # the knot's tails
    m.box("hips", 6.8, 7, -3.2, 2, 2, 2, SCARF_D)
    m.box("tail_b", -7.5, 0, 0, 15, 27, 1, coat(21, hem=True))
    m.box("tail_b", -7, 0, -0.6, 14, 25, 1, lapel)                                    # crimson lining inside
    m.box("tail_r", -1, 0, -4.5, 1, 26, 9, coat(22, hem=True))
    m.box("tail_l", 0, 0, -4.5, 1, 26, 9, coat(23, hem=True))
    m.box("tail_r", -0.4, 1, -4.6, 3, 18, 1, coat(24, hem=True))                      # the open front edges
    m.box("tail_l", -2.6, 1, -4.6, 3, 18, 1, coat(25, hem=True))

    # ---- the torso: the double-breasted greatcoat, lapels, epaulettes, the bandolier, the stock at the throat
    m.box("chest", -7, -22, -4.5, 14, 22, 9, coat(30, buttons=True))
    m.box("chest", -7.5, -22, -5, 3, 12, 1, lapel)
    m.box("chest", 4.5, -22, -5, 3, 12, 1, lapel)
    m.box("chest", -2, -23, -5.2, 4, 5, 1, shirt)                                     # the frilled stock
    m.box("chest", -6, -26, 1.5, 12, 5, 3, coat(31))                                  # the high standing collar
    m.box("chest", -6.2, -26.4, 1.3, 12, 1, 3, braid)
    m.box("chest", -11, -23.5, -4, 6, 2, 8, epaulette)
    m.box("chest", 5, -23.5, -4, 6, 2, 8, epaulette)
    m.box("chest", -11.2, -21.5, -4, 1, 3, 8, epaulette)                              # bullion fringe
    m.box("chest", 10.2, -21.5, -4, 1, 3, 8, epaulette)
    for k in range(6):                                                                # the bandolier, shoulder to hip
        m.box("chest", 4 - k * 2.0, -20 + k * 3.2, -5.6, 3, 3, 1, bandolier)
    m.box("neck", -2.5, -2, -2.5, 5, 3, 5, skin(40))

    # ---- the head: face, tricorn with brass trim, goggles, plume; the braid and scarf streaming back
    m.box("head", -5, -10, -5, 10, 10, 10, face_paint)
    m.box("head", -5.5, -11, -5.5, 11, 3, 11, hat(41))                                # crown band
    m.box("head", -9, -12, -8, 18, 2, 16, hat(42, trim=True))                         # the brim
    m.box("head", -10, -16, -6, 2, 4, 12, hat(43, trim=True))                         # three turned-up sides
    m.box("head", 8, -16, -6, 2, 4, 12, hat(44, trim=True))
    m.box("head", -8, -16, 6, 16, 4, 2, hat(45, trim=True))
    m.box("head", -1.5, -15, -9.5, 3, 4, 2, hat(46, trim=True))                       # the front point
    m.box("head", -5, -17, -4.5, 10, 6, 9, hat(47))                                   # the crown
    m.box("head", -5.4, -15.5, -5.2, 11, 2, 1, goggle_band)
    m.box("head", -4.5, -17, -6.2, 4, 4, 2, lens, glow=lens_glow)
    m.box("head", 0.5, -17, -6.2, 4, 4, 2, lens, glow=lens_glow)
    m.box("head", -0.5, -16, -5.8, 1, 1, 1, B.BRASS)                                  # the bridge
    m.box("plume", -1, -12, 0, 2, 13, 4, plume)
    m.box("braid", -1.5, 0, -1.5, 3, 10, 3, hair_braid)
    m.box("braid_end", -1, 0, -1, 2, 8, 2, hair_braid)
    m.box("braid_end", -1.5, 7, -1.5, 3, 2, 3, B.BRASS)                               # a brass bead at its end
    m.box("scarf", -2, 0, 0, 4, 10, 1, scarf)
    m.box("scarf_end", -1.5, 0, 0, 3, 9, 1, scarf)

    # ---- the rotor pack: an engine casing, two pressure tanks, exhausts, the mast and the four-blade rotor
    m.box("pack", -5, -7, 0, 10, 14, 6, engine, glow=engine_glow)
    m.box("pack", -7.5, -6, 1, 3, 11, 4, B.bands(B.COPPER, B.BRASS_D, every=3, seed=82))
    m.box("pack", 4.5, -6, 1, 3, 11, 4, B.bands(B.COPPER, B.BRASS_D, every=3, seed=83))
    m.box("pack", -4, -11, 2, 2, 5, 2, B.soot(B.IRON, 84))
    m.box("pack", 2, -10, 2, 2, 4, 2, B.soot(B.IRON, 85))
    m.box("pack", -1, -34, 3.5, 2, 28, 2, B.rod(B.IRON_L, 86))                        # the mast
    m.box("pack", -1.5, -20, 3, 3, 1, 3, B.BRASS)
    m.box("pack", -2, -8, 5.5, 4, 2, 1, B.BRASS_D)
    m.box("rotor", -2, -2, -2, 4, 2, 4, B.brass(87))                                  # the hub
    m.box("rotor", -19, -1, -1, 17, 1, 2, rotor_blade)
    m.box("rotor", 2, -1, -1, 17, 1, 2, rotor_blade)
    m.box("rotor", -1, -1, -19, 2, 1, 17, rotor_blade_z)
    m.box("rotor", -1, -1, 2, 2, 1, 17, rotor_blade_z)
    m.box("rotor", -0.5, -4, -0.5, 1, 2, 1, B.BRASS_L)                                # the spinner

    # ---- right arm: coat sleeve, turned-back brass cuff, glove, a basket-hilted cutlass
    m.box("arm_r", -3, -2, -3, 6, 13, 6, coat(50))
    m.box("fore_r", -2.5, 0, -2.5, 5, 7, 5, coat(51))
    m.box("fore_r", -3, 6, -3, 6, 3, 6, braid)
    m.box("fore_r", -2, 9, -2, 4, 4, 4, glove)
    m.box("cutlass", -0.5, -0.5, -1, 1, 1, 3, B.LEATHER)                              # the grip in the fist
    m.box("cutlass", -2, -2.5, -3, 4, 5, 2, basket)                                   # the basket guard
    m.box("cutlass", -0.5, 1, 1.5, 1, 1, 1, B.BRASS_L)                                # the pommel
    m.box("cutlass", -0.5, -1.5, -13, 1, 3, 10, blade)
    m.box("tip", -0.5, -1.5, -9, 1, 3, 9, blade)
    m.box("tip", -0.5, -1, -11, 1, 2, 2, blade)

    # ---- left arm: sleeve, cuff, glove, the harpoon gun
    m.box("arm_l", -3, -2, -3, 6, 13, 6, coat(60))
    m.box("fore_l", -2.5, 0, -2.5, 5, 7, 5, coat(61))
    m.box("fore_l", -3, 6, -3, 6, 3, 6, braid)
    m.box("fore_l", -2, 9, -2, 4, 4, 4, glove)
    m.box("gun", -1, -1, -1, 2, 5, 3, B.MAHOGANY)                                     # the pistol grip
    m.box("gun", -1.5, -5, -16, 3, 3, 20, barrel(90))                                 # the barrel
    m.box("gun", -2.5, -6, -7, 5, 5, 5, drum)                                         # the drum magazine
    m.box("gun", -1, -2, 3, 2, 3, 4, B.MAHOGANY)                                      # the short stock
    m.box("gun", -1, -2, -14, 2, 2, 7, canister, glow=canister_glow)                  # the flare canister
    m.box("gun", -0.5, -4, -21, 1, 1, 5, STEEL_D)                                     # the harpoon shaft
    m.box("gun", -2, -5, -25, 4, 3, 4, blade)                                     # the barbed head
    m.box("gun", -0.5, -6, -2, 1, 1, 2, B.BRASS_L)                                    # the sight

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.0)
    idle.rot("rotor", (0, (0, 0, 0)), (0.5, (0, 90, 0), "linear"), (1.0, (0, 180, 0), "linear"),
             (1.5, (0, 270, 0), "linear"), (2.0, (0, 360, 0), "linear"))
    idle.pos("chest", (0, (0, 0, 0)), (1.0, (0, 0.5, 0)), (2.0, (0, 0, 0)))
    idle.rot("tail_b", (0, (0, 0, 0)), (1.0, (6, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("tail_r", (0, (0, 0, 0)), (1.0, (2, 0, 3)), (2.0, (0, 0, 0)))
    idle.rot("tail_l", (0, (0, 0, 0)), (1.0, (2, 0, -3)), (2.0, (0, 0, 0)))
    idle.rot("scarf", (0, (0, 0, 0)), (0.5, (8, 6, 0)), (1.0, (-4, -4, 0)), (1.5, (6, 4, 0)), (2.0, (0, 0, 0)))
    idle.rot("scarf_end", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (1.0, (-6, 0, 0)), (1.5, (10, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("braid", (0, (0, 0, 0)), (1.0, (6, 0, 4)), (2.0, (0, 0, 0)))
    idle.rot("plume", (0, (0, 0, 0)), (1.0, (-8, 0, 4)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (-24, 0, 0)), (0.6, (24, 0, 0)), (1.2, (-24, 0, 0)))
    walk.rot("leg_l", (0, (24, 0, 0)), (0.6, (-24, 0, 0)), (1.2, (24, 0, 0)))
    walk.rot("shin_r", (0, (10, 0, 0)), (0.3, (30, 0, 0)), (0.6, (0, 0, 0)), (1.2, (10, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (0.9, (30, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("arm_r", (0, (14, 0, 0)), (0.6, (-14, 0, 0)), (1.2, (14, 0, 0)))
    walk.rot("tail_b", (0, (14, 0, 0)), (0.3, (18, 0, 0)), (0.6, (14, 0, 0)), (0.9, (18, 0, 0)), (1.2, (14, 0, 0)))
    walk.rot("tail_r", (0, (0, 0, 6)), (0.6, (0, 0, 2)), (1.2, (0, 0, 6)))
    walk.rot("tail_l", (0, (0, 0, -2)), (0.6, (0, 0, -6)), (1.2, (0, 0, -2)))
    walk.pos("hips", (0, (0, 0, 0)), (0.3, (0, 0.8, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.8, 0)), (1.2, (0, 0, 0)))
    walk.rot("chest", (0, (2, 4, 0)), (0.6, (2, -4, 0)), (1.2, (2, 4, 0)))

    # cutlass (2.7 s): the blade drawn back over her right shoulder (0.7 s = 14 ticks), a forehand cut at 0.7 s, a
    # backhand at 1.2 s, a lunging thrust at 1.7 s (the thrust only in phase 2)
    a = m.anim("cutlass", 2.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-150, -20, 40)), (0.7, (-156, -22, 44)), (0.76, (-60, 40, -30), "linear"),
          (1.1, (-66, 50, -40)), (1.2, (-80, -40, 50), "linear"), (1.5, (-70, 0, 10)), (1.7, (-74, 0, 10)),
          (1.76, (-96, 0, 4), "linear"), (2.0, (-96, 0, 4)), (2.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (0.76, (10, 0, 0), "linear"), (1.5, (0, 0, 0)),
          (1.7, (-20, 0, 0)), (1.76, (20, 0, 0), "linear"), (2.0, (20, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, 34, 0)), (0.76, (8, -30, 0), "linear"), (1.1, (6, -34, 0)),
          (1.2, (6, 30, 0), "linear"), (1.5, (-4, 0, 0)), (1.7, (-6, 10, 0)), (1.76, (18, -6, 0), "linear"),
          (2.0, (16, -6, 0)), (2.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (10, 0, -30)), (1.2, (10, 0, -40)), (2.0, (20, 0, -20)), (2.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.7, (0, 0, 0)), (1.76, (-30, 0, 0), "linear"), (2.0, (-30, 0, 0)),
          (2.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.7, (0, 0, 0)), (1.76, (24, 0, 0), "linear"), (2.0, (24, 0, 0)), (2.7, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.7, (0, 0, 0)), (1.76, (0, -2, -3), "linear"), (2.0, (0, -2, -3)), (2.7, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (0.76, (10, -14, 0)), (1.2, (10, 14, 0)), (1.8, (24, 0, 0)), (2.7, (0, 0, 0)))

    # harpoon (2.4 s): the gun levelled at you (0.9 s = 18 ticks), the harpoon fires at 0.9 s (recoil), she cranks
    # the line in (0.95-1.4 s), then a cutlass cut at 1.5 s on whoever was reeled in
    a = m.anim("harpoon", 2.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-76, 0, -6)), (0.9, (-80, 0, -6)), (0.95, (-100, 0, -6), "linear"),
          (1.4, (-50, 0, -10)), (1.6, (-40, 0, -14)), (2.4, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (62, 0, 0)), (0.95, (52, 0, 0), "linear"), (1.4, (20, 0, 0)),
          (2.4, (0, 0, 0)))
    a.rot("gun", (0, (0, 0, 0)), (0.9, (24, 0, 0)), (1.4, (10, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-4, -26, 0)), (0.95, (-10, -26, 0), "linear"), (1.4, (0, -10, 0)),
          (1.46, (8, 30, 0), "linear"), (1.8, (6, 26, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 30)), (1.4, (-140, -20, 40)), (1.46, (-60, 40, -30), "linear"),
          (1.8, (-60, 40, -30)), (2.4, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -1, 0)), (0.95, (0, -1, 2), "linear"), (1.4, (0, -1, 0)), (2.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.9, (-14, 0, 0)), (1.8, (-14, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.9, (14, 0, 0)), (1.8, (14, 0, 0)), (2.4, (0, 0, 0)))

    # gust (2.7 s): feet planted, the rotor tilted forward and spun up (1.0 s = 20 ticks), the gust from 1.0 to 2.0 s
    a = m.anim("gust", 2.7)
    a.rot("rotor", (0, (0, 0, 0)), (0.5, (0, 360, 0), "linear"), (1.0, (25, 1080, 0), "linear"),
          (1.5, (30, 2160, 0), "linear"), (2.0, (30, 3240, 0), "linear"), (2.7, (0, 3600, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (16, 0, 0)), (1.06, (20, 0, 0), "linear"), (2.0, (20, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-30, 0, 60)), (2.0, (-30, 0, 60)), (2.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-30, 0, -60)), (2.0, (-30, 0, -60)), (2.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.0, (-10, 0, 14)), (2.0, (-10, 0, 14)), (2.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.0, (10, 0, -14)), (2.0, (10, 0, -14)), (2.7, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -3, 0)), (2.0, (0, -3, 0)), (2.7, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (1.0, (40, 0, 0)), (1.5, (55, 0, 0)), (2.0, (45, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("scarf", (0, (0, 0, 0)), (1.0, (30, 0, 0)), (2.0, (30, 0, 0)), (2.7, (0, 0, 0)))

    # divebomb (3.4 s): a crouch under the screaming rotor (0.8 s = 16 ticks), take-off at 0.8 s; airborne with the
    # cutlass raised in both hands, then the plunge strikes at 2.3 s
    a = m.anim("divebomb", 3.4)
    a.rot("rotor", (0, (0, 0, 0)), (0.8, (0, 1440, 0), "linear"), (2.3, (0, 4320, 0), "linear"),
          (3.4, (0, 5040, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.7, (0, -6, 0)), (0.8, (0, -6, 0)), (0.86, (0, 2, 0), "linear"),
          (2.2, (0, 2, 0)), (2.3, (0, -6, -2), "linear"), (2.8, (0, -6, -2)), (3.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-60, 0, 0)), (0.86, (-80, 0, 0), "linear"), (2.2, (-80, 0, 0)),
          (2.3, (-50, 0, 0), "linear"), (2.8, (-50, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.8, (70, 0, 0)), (0.86, (100, 0, 0), "linear"), (2.2, (100, 0, 0)),
          (2.3, (60, 0, 0), "linear"), (2.8, (60, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (0.86, (-70, 0, 0), "linear"), (2.2, (-70, 0, 0)),
          (2.3, (20, 0, 0), "linear"), (2.8, (20, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.8, (60, 0, 0)), (0.86, (100, 0, 0), "linear"), (2.2, (100, 0, 0)),
          (2.3, (80, 0, 0), "linear"), (2.8, (80, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-30, 0, 20)), (0.86, (-170, 0, 10), "linear"), (2.2, (-176, 0, 10)),
          (2.3, (-60, 0, 0), "linear"), (2.8, (-60, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.86, (-30, 0, 0)), (2.2, (-30, 0, 0)), (2.3, (40, 0, 0), "linear"),
          (2.8, (40, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-30, 0, -20)), (0.86, (-20, 0, -70), "linear"), (2.2, (-20, 0, -70)),
          (2.3, (-10, 0, -40), "linear"), (3.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (0.86, (-10, 0, 0), "linear"), (2.2, (-12, 0, 0)),
          (2.3, (18, 0, 0), "linear"), (2.8, (16, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (0.86, (-30, 0, 0)), (2.2, (-40, 0, 0)), (2.3, (40, 0, 0), "linear"),
          (3.4, (0, 0, 0)))

    # flareshot (1.8 s): the gun swung up and aimed (0.7 s = 14 ticks), a flare at 0.7 s, a second at 1.0 s
    a = m.anim("flareshot", 1.8)
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-80, -10, -4)), (0.7, (-84, -10, -4)), (0.74, (-104, -10, -4), "linear"),
          (0.95, (-84, -10, -4)), (1.0, (-84, -10, -4)), (1.04, (-104, -10, -4), "linear"), (1.3, (-84, -10, -4)),
          (1.8, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.7, (62, 0, 0)), (1.3, (62, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("gun", (0, (0, 0, 0)), (0.7, (24, 0, 0)), (1.3, (24, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, -20, 0)), (0.74, (-8, -20, 0), "linear"), (1.3, (-4, -20, 0)),
          (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (0, -14, 0)), (1.3, (0, -14, 0)), (1.8, (0, 0, 0)))

    # boarding (2.3 s): a crouch, cutlass levelled ahead (0.9 s = 18 ticks), the rush on the rotor 0.9-1.6 s
    a = m.anim("boarding", 2.3)
    a.rot("rotor", (0, (0, 0, 0)), (0.9, (-20, 1080, 0), "linear"), (1.6, (-30, 2520, 0), "linear"),
          (2.3, (0, 2880, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (24, 10, 0)), (0.9, (26, 10, 0)), (0.96, (36, 0, 0), "linear"),
          (1.6, (34, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-70, 10, 10)), (0.96, (-96, 0, 6), "linear"), (1.6, (-96, 0, 6)),
          (2.3, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (0.96, (20, 0, 0), "linear"), (1.6, (20, 0, 0)),
          (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (20, 0, -30)), (1.6, (40, 0, -40)), (2.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.9, (-40, 0, 0)), (0.96, (-60, 0, 0), "linear"), (1.6, (-60, 0, 0)),
          (2.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.9, (30, 0, 0)), (0.96, (40, 0, 0), "linear"), (1.6, (40, 0, 0)), (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -4, 0)), (1.6, (0, -3, 0)), (2.3, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (0.96, (60, 0, 0)), (1.6, (64, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("scarf", (0, (0, 0, 0)), (0.96, (35, 0, 0)), (1.6, (35, 0, 0)), (2.3, (0, 0, 0)))

    # cyclone (2.3 s): twisted back, cutlass out wide (0.8 s = 16 ticks), two full spins at 0.8 s and 1.2 s
    a = m.anim("cyclone", 2.3)
    a.rot("bone", (0, (0, 0, 0)), (0.7, (0, -30, 0)), (0.8, (0, -34, 0)), (1.0, (0, 360, 0), "linear"),
          (1.2, (0, 360, 0)), (1.4, (0, 720, 0), "linear"), (2.3, (0, 720, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-20, 0, 90)), (1.4, (-20, 0, 90)), (2.3, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.8, (-40, 0, 0)), (1.4, (-40, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-20, 0, -90)), (1.4, (-20, 0, -90)), (2.3, (0, 0, 0)))
    a.rot("tail_r", (0, (0, 0, 0)), (0.8, (0, 0, 20)), (1.4, (0, 0, 40)), (2.3, (0, 0, 0)))
    a.rot("tail_l", (0, (0, 0, 0)), (0.8, (0, 0, -20)), (1.4, (0, 0, -40)), (2.3, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.4, (50, 0, 0)), (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.8, (0, -2, 0)), (1.4, (0, -2, 0)), (2.3, (0, 0, 0)))

    # flarebomb (phase 3, 2.9 s): the gun raised to the sky (1.0 s = 20 ticks), three flares fired up at 1.0, 1.3 and
    # 1.6 s; they fall on the deck afterwards
    a = m.anim("flarebomb", 2.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-170, 0, -10)), (1.0, (-174, 0, -10)), (1.04, (-160, 0, -10), "linear"),
          (1.3, (-174, 0, -10)), (1.34, (-160, 0, -10), "linear"), (1.6, (-174, 0, -10)),
          (1.64, (-160, 0, -10), "linear"), (2.2, (-170, 0, -10)), (2.9, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (62, 0, 0)), (2.2, (62, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("gun", (0, (0, 0, 0)), (1.0, (24, 0, 0)), (2.2, (24, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (2.2, (-30, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, -10, 0)), (2.2, (-10, -10, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-20, 0, 30)), (2.2, (-20, 0, 30)), (2.9, (0, 0, 0)))

    # muster (2.2 s): a signal flare fired straight up (1.0 s = 20 ticks), then the cutlass sweeps forward: boarders!
    a = m.anim("muster", 2.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-176, 0, 6)), (1.0, (-178, 0, 6)), (1.04, (-164, 0, 6), "linear"),
          (1.5, (-150, 0, 6)), (2.2, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (62, 0, 0)), (1.5, (62, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("gun", (0, (0, 0, 0)), (1.0, (24, 0, 0)), (1.5, (24, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-150, 0, 30)), (1.2, (-150, 0, 30)), (1.3, (-90, 0, 0), "linear"),
          (1.7, (-90, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.3, (6, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.3, (10, 0, 0)), (2.2, (0, 0, 0)))

    # listing (phase 3, 3.5 s): the ship heels over; she braces, leaning against the tilt (1.5 s = 30 ticks), and
    # drives the cutlass into the deck at 1.5 s
    a = m.anim("listing", 3.5)
    a.rot("bone", (0, (0, 0, 0)), (1.0, (0, 0, 10)), (1.5, (0, 0, 12)), (1.56, (0, 0, 4), "linear"), (2.6, (0, 0, 4)),
          (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (0, 0, -16)), (1.5, (20, 0, -16)), (1.56, (40, 0, -4), "linear"),
          (2.6, (36, 0, -4)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-150, 0, 20)), (1.5, (-160, 0, 20)), (1.56, (-40, 0, 0), "linear"),
          (2.6, (-40, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (1.5, (-20, 0, 0)), (1.56, (60, 0, 0), "linear"), (2.6, (60, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-20, 0, -60)), (2.6, (-20, 0, -60)), (3.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, -2, 0)), (1.56, (0, -6, 0), "linear"), (2.6, (0, -6, 0)), (3.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.56, (-50, 0, 0), "linear"), (2.6, (-50, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.56, (60, 0, 0), "linear"), (2.6, (60, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.56, (30, 0, 0), "linear"), (2.6, (30, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.56, (70, 0, 0), "linear"), (2.6, (70, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("tail_b", (0, (0, 0, 0)), (1.5, (30, 0, 20)), (2.6, (20, 0, 10)), (3.5, (0, 0, 0)))

    # roar (phase two): cutlass and gun flung wide, head thrown back, the rotor howling
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-60, 0, 80)), (1.6, (-64, 0, 84)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 0, -80)), (1.6, (-64, 0, -84)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("rotor", (0, (0, 0, 0)), (2.0, (0, 2160, 0), "linear"))
    a.rot("tail_b", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (1.6, (40, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: down on one knee, the rotor coughing to a stop
    a = m.anim("stagger", 2.5)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -9, 0)), (2.1, (0, -9, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-80, 0, 0)), (2.1, (-80, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (2.1, (80, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (2.1, (20, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (90, 0, 0)), (2.1, (90, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 6)), (2.1, (32, 0, 6)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -12)), (2.1, (26, 0, -12)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-20, 0, 10)), (2.1, (-20, 0, 10)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (2.1, (10, 0, -10)), (2.5, (0, 0, 0)))
    a.rot("rotor", (0, (0, 0, 0)), (0.3, (0, 200, 0)), (2.1, (0, 330, 0)), (2.5, (0, 360, 0)))
