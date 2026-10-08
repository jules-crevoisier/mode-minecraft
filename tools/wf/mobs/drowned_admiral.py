"""The Drowned Admiral (L'Amiral noyé): the last commander of the Leviathan Dreadnought, about 5.9 blocks tall with his
hat. He holds the boiler hall of his broken ship.

Silhouette idea: a diving helmet under an admiral's bicorne. A towering naval officer in a waterlogged navy greatcoat
(crimson lining, tarnished gold buttons, epaulettes with dripping fringes, long split tails) stands on lead-soled
diving boots; instead of a head, a round brass diving helmet with a glowing sea-green porthole and two side ports, an
air hose to a copper tank on his back, and a sodden bicorne worn athwart on top of the dome. Strong asymmetry: his
RIGHT hand holds a broad boarding cutlass with a brass basket hilt; his LEFT forearm IS a short deck cannon (an iron
breech at the elbow, a banded barrel, a brass muzzle with an amber glow in the bore), a boarding hook on a chain coiled
under it. Barnacles crust his boots, shoulders, helmet and coat; kelp hangs from his hem, his sleeves and his hat.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

NAVY = (38, 46, 74)
NAVY_L = (66, 80, 112)
NAVY_D = (20, 24, 42)
CRIMSON = (118, 34, 36)
CRIMSON_D = (72, 20, 24)
GOLD = (204, 164, 72)
GOLD_L = (246, 214, 128)
GOLD_D = (128, 96, 40)
BREECH = (168, 164, 146)       # sodden white breeches
BREECH_D = (112, 110, 96)
LEATHER = (66, 44, 32)
LEATHER_D = (40, 26, 20)
SKIN = (124, 138, 128)         # drowned grey-green flesh (the hand)
SKIN_D = (78, 90, 84)
BARN = (206, 200, 180)         # barnacles
BARN_D = (124, 118, 100)
KELP = (64, 104, 52)
KELP_D = (38, 66, 32)
KELP_L = (104, 140, 70)
SALT = (196, 204, 200)         # salt crust on the hem
SEA = (96, 236, 196)           # the drowned light in the porthole
SEA_L = (200, 255, 236)
STEEL = (170, 176, 180)
STEEL_L = (226, 232, 236)
STEEL_D = (98, 102, 108)
VERD = B.VERD
EMBER = (255, 150, 60)
EMBER_L = (255, 222, 150)


# ---------------------------------------------------------------- paint
def coat(seed=0, buttons=False, lapels=False, hem=False, ragged=False):
    """The waterlogged greatcoat: navy wool darkened by the sea, tide-marks, salt crust at the hem, optional double row
    of gold buttons and crimson lapels on the front."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return None if ragged else NAVY_D
        if ragged and face != "top":
            cut = h - 1 - int(B.n(x, 0, seed) * 4)
            if y > cut:
                return None
        r = B.n(x, y, seed)
        c = mul(NAVY, 1.08 - 0.22 * y / max(1, h) + (r - 0.5) * 0.12)
        if (y + int(B.n(x // 3, 0, seed) * 3)) % 7 == 0:
            c = mix(c, NAVY_L, 0.35)                                   # tide-marks
        if B.n(x // 2, y // 2, seed + 3) < 0.07:
            c = mix(c, VERD, 0.3)                                      # sea growth
        if face == "front":
            cx = (w - 1) / 2
            if lapels and abs(x - cx) >= w * 0.18 and abs(x - cx) <= w * 0.32 and y < h * 0.55:
                c = CRIMSON if B.n(x, y, seed + 5) > 0.15 else CRIMSON_D
            if buttons and y % 4 == 1 and y < h - 2 and abs(abs(x - cx) - w * 0.25) < 0.6:
                c = GOLD if B.n(x, y, seed + 6) > 0.3 else mix(GOLD, VERD, 0.5)
            if buttons and abs(x - cx) < 0.6:
                c = NAVY_D                                             # the front seam
        if hem and y >= h - 2:
            c = mix(c, SALT, 0.55 if y == h - 1 else 0.3)
        if face == "top":
            c = mix(c, NAVY_L, 0.25)
        return c
    return f


def lining(seed=0):
    """Crimson lining on the inside of the tails, faded and torn."""
    def f(face, x, y, w, h):
        if face in ("front",):
            return mul(CRIMSON, 1.0 + (B.n(x, y, seed) - 0.5) * 0.2)
        return coat(seed)(face, x, y, w, h)
    return f


def gold(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        c = mul(GOLD, 1.06 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
        if face == "top":
            c = mix(c, GOLD_L, 0.4)
        if B.n(x, y, seed + 2) < 0.18:
            c = mix(c, VERD, 0.5)                                      # tarnish
        return c
    return f


def fringe(seed=0):
    """The epaulette's bullion fringe, dripping: gold strands of uneven length."""
    def f(face, x, y, w, h):
        if face == "top":
            return GOLD_D
        if face == "bottom":
            return None
        if x % 2 == 1:
            return None
        if y > h - 1 - int(B.n(x, 0, seed) * 2):
            return None
        return GOLD if y < h - 1 else GOLD_D
    return f


def breeches(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return BREECH_D
        c = mul(BREECH, 1.04 - 0.16 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if B.n(x // 2, y // 2, seed + 4) < 0.15:
            c = mix(c, KELP_D, 0.3)                                    # sea stains
        return c
    return f


def boot(seed=0):
    """Diving boots: dark leather, a brass ankle band, barnacles crusting the lower half."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return LEATHER_D
        c = mul(LEATHER, 1.06 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.14)
        if y in (2, 3) and face != "top":
            c = B.BRASS if (x + y) % 3 else B.BRASS_D                  # the brass band and its bolts
        if y > h * 0.5 and B.n(x, y, seed + 3) < 0.12:
            c = BARN if B.n(x, y, seed + 4) < 0.6 else BARN_D
        return c
    return f


def lead_sole(seed=0):
    def f(face, x, y, w, h):
        if face == "top":
            return B.BRASS_D
        if face == "front" and y < 2:
            return B.BRASS if x % 2 else B.BRASS_L                     # the brass toe cap
        c = mul((70, 72, 76), 1.0 + (B.n(x, y, seed) - 0.5) * 0.14)
        if B.n(x, y, seed + 2) < 0.18:
            c = BARN_D
        return c
    return f


def helmet(seed=0, verdigris=0.18):
    """The diving helmet's copper-brass dome: riveted seams, verdigris blooms, barnacles."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return B.BRASS_DD
        c = mul(B.COPPER if (x // 4 + y // 5) % 2 else mix(B.COPPER, B.BRASS, 0.5),
                1.1 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if x % 5 == 0 or (face != "top" and y % 6 == 0):
            c = mix(c, B.BRASS_L, 0.35) if (x + y) % 2 else B.COPPER_D  # seams and rivets
        if B.n(x // 2, y // 2, seed + 5) < verdigris:
            c = mix(c, VERD, 0.65)
        if B.n(x, y, seed + 9) < 0.03:
            c = BARN
        if face == "top":
            c = mix(c, B.COPPER_L, 0.25)
        return c
    return f


def porthole(face, x, y, w, h):
    """The front port: a heavy brass rim, a cross of bars over sea-green glass that glows from inside."""
    if face != "front":
        return B.brass(301)(face, x, y, w, h)
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if (x + y) % 3 == 0 else B.BRASS
    if x == w // 2 or y == h // 2:
        return B.BRASS_D                                               # the guard bars
    return SEA_L if (x + y) % 5 == 0 else SEA


def porthole_glow(face, x, y, w, h):
    if face != "front" or x in (0, w - 1) or y in (0, h - 1) or x == w // 2 or y == h // 2:
        return None
    return SEA_L if (x + y) % 5 == 0 else SEA


def side_port(face, x, y, w, h):
    if face not in ("left", "right"):
        return B.brass(302)(face, x, y, w, h)
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS
    return SEA


def side_port_glow(face, x, y, w, h):
    if face not in ("left", "right") or x in (0, w - 1) or y in (0, h - 1):
        return None
    return SEA


def felt(seed=0, trim=True):
    """The bicorne: sodden black-navy felt, a gold lace edge, kelp in the brim."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return NAVY_D
        c = mul((30, 32, 46), 1.08 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
        if trim and face in ("front", "back") and y == 0:
            c = GOLD if (x + seed) % 3 else GOLD_D
        if B.n(x // 2, y, seed + 3) < 0.06:
            c = KELP_D
        return c
    return f


def kelp(seed=0):
    """A ragged strand of kelp: ribbed, darker toward the tip, torn end."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        if y > h - 1 - int(B.n(x, 0, seed) * 2):
            return None
        c = KELP if (y + seed) % 3 else KELP_L
        return mix(c, KELP_D, 0.5 * y / max(1, h))
    return f


def barnacle(face, x, y, w, h):
    if face == "top":
        return BARN_D if (x + y) % 2 == 0 and w > 1 else BARN
    return BARN if (x + y) % 2 else mul(BARN, 0.85)


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = mul(SKIN, 1.04 - 0.16 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.14)
        if B.n(x, y, seed + 4) < 0.1:
            c = mix(c, KELP_D, 0.4)
        return c
    return f


def steel(seed=0, edge="front"):
    """The cutlass blade: grey steel, a bright edge, a dark fuller, sea rust spots."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STEEL_D
        c = mul(STEEL, 1.02 + (B.n(x, y, seed) - 0.5) * 0.08)
        if face in ("left", "right"):
            if x == 0:
                c = STEEL_L                                            # the edge (toward -z)
            elif x == w - 1:
                c = STEEL_D                                            # the spine
            elif w > 2 and x == w // 2:
                c = mul(STEEL, 0.82)                                   # the fuller
        if B.n(x, y, seed + 3) < 0.05:
            c = (132, 84, 54)                                          # rust
        return c
    return f


def cannon(seed=0, bands=True):
    """The deck-cannon forearm: blackened iron, brass bands every few texels, soot near the muzzle."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(B.IRON, 0.9 if face == "top" else 0.6)
        c = mul(B.IRON, 1.14 - 0.12 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if face in ("front", "back", "left", "right") and (x in (0, w - 1)):
            c = mul(c, 0.8)
        if bands and y % 6 == 0:
            c = B.BRASS if x % 3 else B.BRASS_L
        if y > h - 4 and B.n(x, y, seed + 2) < 0.4:
            c = B.SOOT
        if B.n(x, y, seed + 6) < 0.04:
            c = BARN
        return c
    return f


def muzzle(face, x, y, w, h):
    """The brass muzzle ring; its bore (the bottom face) glows with the next charge."""
    if face == "bottom":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = max(abs(x - cx), abs(y - cy))
        if d < 1.6:
            return EMBER_L if d < 0.8 else EMBER
        if d < 2.6:
            return B.SOOT
        return B.BRASS_D
    return B.brass(303)(face, x, y, w, h)


def muzzle_glow(face, x, y, w, h):
    if face != "bottom":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = max(abs(x - cx), abs(y - cy))
    if d < 1.6:
        return EMBER_L if d < 0.8 else EMBER
    return None


def iron_chain(face, x, y, w, h):
    return B.IRON_L if (y + x) % 2 else B.IRON


def hook_paint(face, x, y, w, h):
    c = mul(B.IRON_L, 1.0 + (B.n(x, y, 77) - 0.5) * 0.2)
    if face == "top":
        return mix(c, (200, 200, 200), 0.3)
    return c


# ---------------------------------------------------------------- build
def _barnacles(m, part, spots, seed=0):
    """Small barnacle clusters: each spot (x, y, z, size) is a cone of 1-2 texel cubes."""
    for (x, y, z, s) in spots:
        m.box(part, x, y, z, s, 1, s, barnacle)
        if s >= 2:
            m.box(part, x + (s - 1) / 2, y - 1, z + (s - 1) / 2, 1, 1, 1, BARN_D)


def build():
    m = Model("drowned_admiral", seed=419, shadow=1.7, walk_speed=0.7, walk_scale=0.75, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5.5 * sx, -36, 0), rot=(0, 0, -2 * sx))
        m.part(f"boot_{side}", f"leg_{side}", pivot=(0, 18, 0), rot=(0, 0, 2 * sx))
    m.part("pelvis", "bone", pivot=(0, -36, 0))
    m.part("skirt", "pelvis", pivot=(0, -1, 0))
    m.part("tails", "pelvis", pivot=(0, -1, 5))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -4, 0), rot=(6, 0, 0))
    m.part("tank", "chest", pivot=(0, -12, 8))
    m.part("head", "chest", pivot=(0, -22, -1), rot=(-6, 0, 0))
    m.part("hat", "head", pivot=(0, -21, 1), rot=(-4, 0, -8))
    m.part("arm_r", "chest", pivot=(-16, -18, 0), rot=(-8, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-40, 0, -6))
    m.part("cutlass", "fore_r", pivot=(0, 13, -0.5), rot=(-36, 0, 0))
    m.part("arm_l", "chest", pivot=(16, -18, 0), rot=(-4, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-56, 0, 6))
    m.part("hook", "fore_l", pivot=(5.5, 6, 1), rot=(56, 0, 0))

    # ---- legs: sodden white breeches, tall diving boots with lead soles and brass toe caps
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"leg_{side}", -3.5, -1, -3.5, 7, 19, 7, breeches(10 + sx))
        m.box(f"boot_{side}", -4, 0, -4, 8, 14, 8, boot(12 + sx))
        m.box(f"boot_{side}", -4.5, -1, -4.5, 9, 3, 9, boot(14 + sx))                    # the folded boot top
        m.box(f"boot_{side}", -5, 14, -6, 10, 4, 11, lead_sole(16 + sx))
        _barnacles(m, f"boot_{side}", ((-4.6, 9, -2, 2), (3, 11, 1, 2), (-2, 13, -4.6, 1), (2.5, 6, -4.4, 1)), sx)
    m.box("boot_r", -2, 4, -4.6, 1, 6, 1, kelp(18))

    # ---- the greatcoat's skirt: two front panels open over the breeches, the sides, the long split tails behind
    m.box("pelvis", -12, -4, -8, 24, 5, 16, coat(20, hem=False))
    m.box("pelvis", -12.5, -1, -8.5, 25, 2, 17, LEATHER)                                # the sword belt
    m.box("pelvis", -2, -1.5, -9, 4, 3, 1, gold(21))                                    # its buckle
    m.box("skirt", -12, 0, -8, 9, 22, 3, coat(22, hem=True, ragged=True))
    m.box("skirt", 3, 0, -8, 9, 22, 3, coat(23, hem=True, ragged=True))
    m.box("skirt", -13, 0, -6, 3, 24, 11, coat(24, hem=True, ragged=True))
    m.box("skirt", 10, 0, -6, 3, 24, 11, coat(25, hem=True, ragged=True))
    m.box("skirt", -3.5, 0, -7.5, 1, 20, 1, lining(26))                                  # crimson inside the front
    m.box("skirt", 2.5, 0, -7.5, 1, 20, 1, lining(27))
    m.box("tails", -12, 0, 0, 11, 30, 3, coat(28, hem=True, ragged=True))
    m.box("tails", 1, 0, 0, 11, 30, 3, coat(29, hem=True, ragged=True))
    for i, (x, ln) in enumerate(((-11, 8), (-6, 12), (-1.5, 6), (4, 10), (9, 7), (-12.5, 5))):
        m.box("tails", x, 28 + (i % 2), 1, 1, ln, 1, kelp(30 + i))                     # kelp hanging from the hem
    m.box("skirt", -10, 21, -8.5, 1, 7, 1, kelp(36))
    m.box("skirt", 8, 20, -8.5, 1, 9, 1, kelp(37))
    _barnacles(m, "tails", ((-9, 18, 2.6, 2), (5, 24, 2.6, 2), (-3, 10, 2.6, 1)), 3)

    # ---- the torso: double-breasted coat, crimson lapels, a sash of medals, broad shoulders under the epaulettes
    m.box("waist", -11.5, -4, -7.5, 23, 5, 15, coat(40, buttons=True))
    m.box("chest", -13, -22, -8, 26, 22, 16, coat(41, buttons=True, lapels=True))
    m.box("chest", -9, -18, -8.6, 2, 3, 1, gold(42))                                    # medals on the breast
    m.box("chest", -6, -18, -8.6, 2, 3, 1, (150, 40, 40))
    m.box("chest", -12, -21, -8.6, 1, 16, 1, (150, 40, 40))                             # the sash edge
    for side, sx in (("r", -1), ("l", 1)):
        x0 = -19.5 if sx < 0 else 10.5
        m.box("chest", x0, -24, -5.5, 9, 3, 11, gold(44 + sx))                          # epaulette boards
        m.box("chest", x0, -21, -5.5, 9, 4, 11, fringe(46 + sx))                        # bullion fringe
    _barnacles(m, "chest", ((-17, -25, -2, 2), (14, -25, 1, 2), (-11, -6, -8.8, 1), (9, -12, -8.8, 2),
                            (-12, -15, 7.6, 2), (10, -3, 7.6, 1)), 4)
    m.box("chest", 13, -10, -6, 1, 9, 1, kelp(48))
    # the diving tank on his back and the air hose up to the helmet
    m.box("tank", -5, -8, 0, 10, 18, 6, B.bands(B.COPPER, B.COPPER_D, every=5, seed=50))
    m.box("tank", -2, -10, 1.5, 4, 2, 3, B.brass(51))
    m.box("tank", -1, -11, 2.5, 2, 1, 2, B.IRON)
    for k in range(4):
        m.box("tank", -4 + k * 0.5, -12 - k * 2, 2 - k * 1.2, 2, 2, 2, B.rod((70, 62, 54), 52 + k))

    # ---- the diving helmet: corselet over the shoulders, a round dome, the sea-green port, side ports, a bicorne
    m.box("head", -11, -2, -9, 22, 4, 18, B.brass(60, rivet_step=3))                   # the corselet
    m.box("head", -8.5, -4, -8.5, 17, 2, 17, B.brass(61, rivet_step=2))                # the neck ring
    m.box("head", -8, -20, -8, 16, 16, 16, helmet(62))
    m.box("head", -9, -18, -7, 18, 12, 14, helmet(63))
    m.box("head", -7, -18, -9, 14, 12, 18, helmet(64))
    m.box("head", -6, -21, -6, 12, 2, 12, helmet(65))
    m.box("head", -5, -17, -10.5, 10, 10, 2, porthole, glow=porthole_glow)              # the front port
    for sx in (-1, 1):
        m.box("head", 8.5 if sx > 0 else -10.5, -15, -3, 2, 6, 6, side_port, glow=side_port_glow)
    m.box("head", -1.5, -8, -11, 3, 2, 2, B.brass(66))                                  # the speaking valve
    m.box("head", -2, -16, 8.5, 4, 4, 2, B.brass(67))                                   # the hose coupling
    _barnacles(m, "head", ((5, -19, -6, 2), (-7, -12, 6, 2), (-9.5, -9, -2, 1), (4, -6, 8.6, 1)), 5)
    # the bicorne, worn athwart: a long peaked brim of sodden felt, gold lace, a cockade, a strand of kelp
    m.box("hat", -16, -5, -3, 32, 5, 6, felt(70))
    m.box("hat", -12, -8, -2.5, 24, 3, 5, felt(71, trim=False))
    m.box("hat", -6, -10, -2, 12, 2, 4, felt(72, trim=False))
    m.box("hat", -2, -7, -3.6, 4, 4, 1, {"front": (176, 40, 40), "*": GOLD})            # the cockade
    m.box("hat", -0.5, -6, -3.8, 1, 2, 1, GOLD_L)
    m.box("hat", 12, 0, -0.5, 1, 9, 1, kelp(73))
    m.box("hat", -14, 0, 0, 1, 6, 1, kelp(74))

    # ---- right arm: a coat sleeve with a gold-laced cuff, a drowned hand, the boarding cutlass
    m.box("arm_r", -4.5, -3, -4.5, 9, 15, 9, coat(80))
    m.box("fore_r", -4, 0, -4, 8, 9, 8, coat(81))
    m.box("fore_r", -4.5, 5, -4.5, 9, 4, 9, gold(82))                                   # the admiral's cuff
    m.box("fore_r", -2.5, 9, -2.5, 5, 5, 5, skin(83))
    _barnacles(m, "arm_r", ((-4.8, 2, -1, 2), (2, 9, -4.8, 1)), 6)
    m.box("arm_r", -4.8, 8, 2, 1, 8, 1, kelp(84))
    # the cutlass: its grip in the fist, a brass basket hilt round the knuckles, a broad blade curving back
    m.box("cutlass", -1, -4, -1, 2, 6, 2, LEATHER)                                     # the grip
    m.box("cutlass", -1.5, -5, -1.5, 3, 1, 3, B.brass(85))                              # the pommel
    m.box("cutlass", -3, 2, -3.5, 6, 1, 6, B.brass(86))                                 # the guard plate
    m.box("cutlass", -3, -5, -3.5, 6, 7, 1, B.brass(87))                                # the basket's shell
    m.box("cutlass", -3, -5, -3.5, 1, 7, 4, B.brass(88))
    m.box("cutlass", 2, -5, -3.5, 1, 7, 4, B.brass(89))
    for k in range(6):
        z = -1.5 - k * 0.6 + (k * k) * 0.25                                           # forward then curving back
        d = 4 if k < 5 else 3
        m.box("cutlass", -0.5, 3 + k * 5, z, 1, 5, d, steel(90 + k))
    m.box("cutlass", -0.5, 33, 1.0, 1, 3, 2, steel(97))                                 # the clipped point

    # ---- left arm: a barnacled sleeve, and below the elbow the deck cannon, a boarding hook on a chain under it
    m.box("arm_l", -4.5, -3, -4.5, 9, 14, 9, coat(100))
    _barnacles(m, "arm_l", ((3.6, 0, -2, 2), (-1, 8, 3.6, 2), (4.6, 7, 2, 1)), 7)
    m.box("fore_l", -5, -1, -5, 10, 8, 10, B.iron(101, rivet_step=3))                   # the breech at the elbow
    m.box("fore_l", -5.5, 3, -5.5, 11, 2, 11, B.brass(102))
    m.box("fore_l", -3.5, 7, -3.5, 7, 18, 7, cannon(103))                               # the barrel
    m.box("fore_l", -4.5, 24, -4.5, 9, 3, 9, muzzle, glow=muzzle_glow)                  # the muzzle
    m.box("fore_l", -1, 11, -4.6, 2, 3, 1, B.brass(104))                                # the fore-sight
    m.box("fore_l", -4.6, 14, -1, 1, 4, 2, B.brass(105))                                # a trunnion
    m.box("fore_l", 3.6, 14, -1, 1, 4, 2, B.brass(106))
    for k in range(3):
        m.box("fore_l", -4, 10 + k * 3, -4, 8, 1, 8, iron_chain)                        # chain coiled round the barrel
    # the boarding hook: a short chain down to a four-pronged grapnel
    for k in range(5):
        m.box("hook", -0.5, k * 2, -0.5, 1, 2, 1, iron_chain)
    m.box("hook", -0.5, 10, -0.5, 1, 5, 1, hook_paint)                                  # the shank
    m.box("hook", -1, 9, -1, 2, 1, 2, B.IRON)                                           # its ring
    for (dx, dz) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        m.box("hook", -0.5 + dx * 1.5, 14, -0.5 + dz * 1.5, 1, 1, 1, hook_paint)
        m.box("hook", -0.5 + dx * 2.5, 11, -0.5 + dz * 2.5, 1, 3, 1, hook_paint)         # prongs curving up

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, -0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.4, (0, 12, 0)), (2.8, (2, -8, 0)), (4.0, (0, 0, 0)))
    idle.rot("hat", (0, (0, 0, 0)), (2.0, (0, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("tails", (0, (0, 0, 0)), (2.0, (4, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("skirt", (0, (0, 0, 0)), (2.0, (2, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("hook", (0, (0, 0, 0)), (1.3, (8, 0, 6)), (2.7, (-6, 0, -4)), (4.0, (0, 0, 0)))
    idle.rot("cutlass", (0, (0, 0, 0)), (2.0, (4, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("fore_l", (0, (0, 0, 0)), (2.0, (-4, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("boot_r", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (24, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("boot_l", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, 1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, 1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 5, 0)), (1.0, (0, -5, 0)), (2.0, (0, 5, 0)))
    walk.rot("skirt", (0, (4, 0, 2)), (1.0, (4, 0, -2)), (2.0, (4, 0, 2)))
    walk.rot("tails", (0, (10, 0, 0)), (1.0, (16, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("arm_r", (0, (-10, 0, 0)), (1.0, (10, 0, 0)), (2.0, (-10, 0, 0)))
    walk.rot("arm_l", (0, (8, 0, 0)), (1.0, (-8, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("hook", (0, (14, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (14, 0, 0)))

    # slash: the cutlass drawn back over his right shoulder (0.7 s = 14 ticks), a forehand cut across at 0.7 s, the
    # blade carried round and a backhand cut at 1.2 s (active tick 10), recovery to 2.3 s
    a = m.anim("slash", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-80, -20, 70)), (0.7, (-86, -24, 76)), (0.8, (-70, 60, -20), "linear"),
          (1.0, (-76, 66, -26)), (1.2, (-64, -30, 60), "linear"), (1.5, (-60, -34, 62)), (2.3, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (20, 0, 0)), (0.8, (30, 0, 0), "linear"), (1.2, (30, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.7, (-40, 0, 30)), (0.8, (-30, 0, -20), "linear"), (1.0, (-36, 0, -24)),
          (1.2, (-36, 0, 30), "linear"), (1.5, (-30, 0, 26)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, 30, 0)), (0.8, (8, -30, 0), "linear"), (1.0, (6, -34, 0)),
          (1.2, (8, 26, 0), "linear"), (1.5, (6, 28, 0)), (2.3, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.7, (0, 10, 0)), (0.8, (0, -10, 0), "linear"), (1.2, (0, 10, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-20, 0, -30)), (1.2, (-10, 0, -20)), (2.3, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.8, (10, 0, -10)), (1.25, (14, 0, 12)), (2.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (0.8, (8, 0, 0), "linear"), (2.3, (0, 0, 0)))

    # thrust: he sets his feet and draws the cutlass back at the hip, point forward (0.8 s = 16 ticks), then lunges
    # through you point first
    a = m.anim("thrust", 1.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-30, 0, 30)), (0.8, (-24, 0, 34)), (0.85, (-92, 0, 4), "linear"),
          (1.2, (-90, 0, 4)), (1.9, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (-50, 0, 0)), (0.85, (10, 0, 0), "linear"), (1.2, (10, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.8, (-50, 0, 0)), (0.85, (-80, 0, 0), "linear"), (1.2, (-80, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, 24, 0)), (0.85, (22, -10, 0), "linear"), (1.2, (20, -10, 0)), (1.9, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, -2, 3)), (0.85, (0, -3, -4), "linear"), (1.2, (0, -3, -4)), (1.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (0.85, (-40, 0, 0), "linear"), (1.2, (-36, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("boot_r", (0, (0, 0, 0)), (0.85, (30, 0, 0), "linear"), (1.2, (28, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (0.85, (24, 0, 0), "linear"), (1.2, (22, 0, 0)), (1.9, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.85, (24, 0, 0)), (1.2, (20, 0, 0)), (1.9, (0, 0, 0)))

    # cannon: the cannon arm raised level and steadied with the right hand under it, the aim laser held on the target
    # (1.4 s = 28 ticks), the shot at 1.4 s kicks the arm up and the body back
    a = m.anim("cannon", 2.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-80, -10, -6)), (1.4, (-84, -14, -4)), (1.45, (-120, -14, -10), "linear"),
          (1.8, (-96, -14, -6)), (2.5, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.5, (52, 0, -6)), (1.4, (52, 0, -6)), (1.45, (40, 0, -6), "linear"), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-60, 30, 30)), (1.4, (-62, 34, 30)), (1.45, (-50, 20, 30), "linear"),
          (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (0, -20, 0)), (1.4, (0, -22, 0)), (1.45, (-12, -18, 0), "linear"),
          (1.9, (-4, -16, 0)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (4, -14, 6)), (1.4, (4, -16, 6)), (1.5, (-8, -10, 0)), (2.5, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.4, (0, -1, 0)), (1.45, (0, -1, 3), "linear"), (2.0, (0, 0, 1)), (2.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.4, (-16, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (1.4, (14, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("hook", (0, (0, 0, 0)), (1.4, (60, 0, 0)), (1.6, (100, 0, 0)), (2.5, (0, 0, 0)))

    # valves: the cutlass raised high as a signal, the cannon arm swung down and back (1.2 s = 24 ticks); the blade
    # chops down at 1.2 s: "vent!" and the boiler valves burst; he holds the order while the steam roars
    a = m.anim("valves", 4.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-170, 0, 10)), (1.2, (-176, 0, 12)), (1.3, (-80, 0, 10), "linear"),
          (3.7, (-78, 0, 12)), (4.4, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (1.2, (20, 0, 0)), (1.3, (-60, 0, 0), "linear"), (3.7, (-56, 0, 0)), (4.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (30, 0, -30)), (1.2, (34, 0, -34)), (1.3, (-10, 0, -40), "linear"),
          (3.7, (-10, 0, -40)), (4.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-14, 10, 0)), (1.3, (14, -4, 0), "linear"), (3.7, (12, -4, 0)), (4.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-20, 0, 0)), (1.3, (6, 0, 0), "linear"), (3.7, (4, 0, 0)), (4.4, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.2, (0, 1, 0)), (1.3, (0, -2, 0), "linear"), (3.7, (0, -2, 0)), (4.4, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (1.3, (16, 0, 0)), (2.5, (24, 0, 4)), (3.7, (20, 0, -4)), (4.4, (0, 0, 0)))

    # hook: the boarding hook whirled round under the cannon arm (0.9 s = 18 ticks), flung at the target at 0.9 s;
    # the chain is hauled in hand over hand until 1.6 s, recovery to 2.3 s
    a = m.anim("hook", 2.3)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-60, 0, -60)), (0.6, (-40, 0, -70)), (0.9, (-110, 0, -40)),
          (0.95, (-90, 0, -10), "linear"), (1.25, (-40, 0, -20)), (1.6, (-10, 0, -20)), (2.3, (0, 0, 0)))
    a.rot("hook", (0, (0, 0, 0)), (0.3, (0, 0, 120)), (0.6, (0, 0, 240)), (0.9, (-90, 0, 360)), (0.95, (-100, 0, 360), "linear"),
          (1.6, (-30, 0, 360)), (2.3, (0, 0, 360)))
    a.scale("hook", (0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.95, (1, 4.0, 1), "linear"), (1.25, (1, 2.2, 1)), (1.6, (1, 1, 1)),
            (2.3, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 20)), (1.25, (-50, 30, 10)), (1.6, (-20, 0, 20)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-6, -24, 0)), (0.95, (10, 16, 0), "linear"), (1.25, (-6, 10, 0)), (1.6, (-8, 0, 0)),
          (2.3, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.25, (0, 0, 2)), (1.6, (0, 0, 1)), (2.3, (0, 0, 0)))

    # stamp: a lead-soled boot lifted high (0.6 s = 12 ticks) and stamped down
    a = m.anim("stamp", 1.35)
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-70, 0, 0)), (0.6, (-74, 0, 0)), (0.65, (4, 0, 0), "linear"), (1.0, (4, 0, 0)),
          (1.35, (0, 0, 0)))
    a.rot("boot_r", (0, (0, 0, 0)), (0.6, (60, 0, 0)), (0.65, (0, 0, 0), "linear"), (1.35, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-12, 0, 6)), (0.65, (14, 0, 0), "linear"), (1.0, (12, 0, 0)), (1.35, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.6, (0, 2, 0)), (0.65, (0, -2, 0), "linear"), (1.0, (0, -2, 0)), (1.35, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-30, 0, -40)), (0.65, (-10, 0, -20), "linear"), (1.35, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-30, 0, 40)), (0.65, (-10, 0, 20), "linear"), (1.35, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.6, (-8, 0, 0)), (0.75, (14, 0, 0)), (1.35, (0, 0, 0)))

    # broadside (phase 2): the cannon arm raised (1.2 s = 24 ticks), three shots at 1.2, 2.2 and 3.2 s (active 0, 20, 40),
    # the arm kicked up by each recoil and lowered back onto the next aim; recovery to 4.2 s
    a = m.anim("broadside", 4.2)
    keys = [(0, (0, 0, 0)), (0.6, (-80, -10, -6)), (1.2, (-84, -12, -4))]
    for k in range(3):
        t = 1.2 + k
        keys += [(t + 0.05, (-122, -12, -10), "linear"), (t + 0.4, (-94, -12, -6))]
        if k < 2:
            keys += [(t + 1.0, (-84, -12, -4))]
    keys += [(4.2, (0, 0, 0))]
    a.rot("arm_l", *keys)
    ckeys = [(0, (0, 0, 0)), (1.2, (0, -22, 0))]
    for k in range(3):
        t = 1.2 + k
        ckeys += [(t + 0.05, (-12, -18, 0), "linear"), (t + 0.45, (-2, -22, 0))]
    ckeys += [(4.2, (0, 0, 0))]
    a.rot("chest", *ckeys)
    a.rot("fore_l", (0, (0, 0, 0)), (0.6, (52, 0, -6)), (3.4, (52, 0, -6)), (4.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 0, 40)), (3.4, (-40, 0, 40)), (4.2, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.6, (-50, 0, 0)), (3.4, (-50, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (-16, 0, 0)), (3.4, (-16, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (3.4, (14, 0, 0)), (4.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (4, -16, 6)), (3.4, (4, -16, 6)), (4.2, (0, 0, 0)))

    # boarding (phase 2): forehand at 0.8 s (16 ticks), backhand at 1.3 s, then a leap and an overhead chop that lands
    # at 2.0 s (active 24); recovery to 3.1 s
    a = m.anim("boarding", 3.1)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-80, -20, 70)), (0.8, (-86, -24, 76)), (0.9, (-70, 60, -20), "linear"),
          (1.1, (-76, 66, -26)), (1.3, (-64, -30, 60), "linear"), (1.5, (-150, 0, 20)), (1.9, (-176, 0, 12)),
          (2.0, (-70, 0, 8), "linear"), (2.4, (-66, 0, 8)), (3.1, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (0.8, (-40, 0, 30)), (0.9, (-30, 0, -20), "linear"), (1.3, (-36, 0, 30), "linear"),
          (1.9, (30, 0, 0)), (2.0, (-70, 0, 0), "linear"), (2.4, (-66, 0, 0)), (3.1, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 30, 0)), (0.9, (8, -30, 0), "linear"), (1.3, (8, 26, 0), "linear"),
          (1.9, (-22, 0, 0)), (2.0, (26, 0, 0), "linear"), (2.4, (24, 0, 0)), (3.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.4, (0, -2, 0)), (1.7, (0, 10, -6)), (1.95, (0, 4, -12)), (2.0, (0, -3, -14), "linear"),
          (2.4, (0, -3, -14)), (3.1, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.4, (10, 0, 0)), (1.7, (-50, 0, 0)), (2.0, (-30, 0, 0), "linear"), (2.4, (-28, 0, 0)),
          (3.1, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.4, (-10, 0, 0)), (1.7, (30, 0, 0)), (2.0, (20, 0, 0), "linear"), (3.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.5, (-30, 0, -40)), (1.9, (-60, 0, -50)), (2.0, (-20, 0, -30), "linear"), (3.1, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.9, (12, 0, -10)), (1.35, (14, 0, 12)), (1.8, (-20, 0, 0)), (2.1, (30, 0, 0)),
          (3.1, (0, 0, 0)))

    # charge (phase 2): helmet lowered, cannon arm braced forward like a ram (0.8 s = 16 ticks), then he charges for
    # 0.6 s; recovery to 2.1 s
    a = m.anim("charge", 2.1)
    a.rot("chest", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (1.4, (32, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (1.4, (10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-70, 0, 10)), (1.4, (-70, 0, 10)), (2.1, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (56, 0, 0)), (1.4, (56, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (20, 0, 20)), (1.4, (20, 0, 20)), (2.1, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (0.95, (-36, 0, 0), "linear"), (1.1, (30, 0, 0)), (1.25, (-36, 0, 0)),
          (1.4, (20, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (0.95, (30, 0, 0), "linear"), (1.1, (-36, 0, 0)), (1.25, (30, 0, 0)),
          (1.4, (-10, 0, 0)), (2.1, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (1.0, (40, 0, 0)), (1.4, (36, 0, 0)), (2.1, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.8, (0, -3, 2)), (1.4, (0, -2, 0)), (2.1, (0, 0, 0)))

    # scuttle (phase 3, invulnerable): he drops to one knee and drives the cutlass into the deck with both hands (1.5 s
    # = 30 ticks): the sea cocks open and the hall floods; he rises out of the water
    a = m.anim("scuttle", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -12, 0)), (1.5, (0, -12, 0)), (1.55, (0, -14, 0), "linear"), (2.8, (0, -12, 0)),
          (3.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (-80, 0, 0)), (2.8, (-80, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("boot_r", (0, (0, 0, 0)), (0.4, (80, 0, 0)), (2.8, (80, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (10, 0, 0)), (2.8, (10, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("boot_l", (0, (0, 0, 0)), (0.4, (80, 0, 0)), (2.8, (80, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-160, 0, -10)), (1.5, (-170, 0, -14)), (1.55, (-60, 0, -20), "linear"),
          (2.8, (-60, 0, -20)), (3.5, (0, 0, 0)))
    a.rot("cutlass", (0, (0, 0, 0)), (1.5, (60, 0, 0)), (1.55, (-30, 0, 0), "linear"), (2.8, (-30, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-150, 0, 20)), (1.5, (-160, 0, 24)), (1.55, (-60, 0, 30), "linear"),
          (2.8, (-60, 0, 30)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.5, (-16, 0, 0)), (1.55, (30, 0, 0), "linear"), (2.8, (26, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-24, 0, 0)), (1.55, (16, 0, 0), "linear"), (2.8, (14, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (2.8, (-30, 0, 0)), (3.5, (0, 0, 0)))

    # roar (phase two): cutlass and cannon flung wide, the helmet thrown back, the hat askew
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-120, 0, -30)), (1.6, (-124, 0, -34)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-36, 0, 0)), (1.6, (-32, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("hat", (0, (0, 0, 0)), (0.6, (-10, 0, 10)), (1.6, (-8, 0, 12)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (1.6, (-18, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("tails", (0, (0, 0, 0)), (0.6, (24, 0, 0)), (1.1, (30, 0, 8)), (1.6, (24, 0, -8)), (2.0, (0, 0, 0)))

    # stagger: he sags onto one knee, leaning on the cutlass, the helmet hanging, the hat tipped over
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -12, 0)), (1.6, (0, -12, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-80, 0, 0)), (1.6, (-80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("boot_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("boot_l", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.6, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, -8)), (1.6, (32, 0, -8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, 12)), (1.6, (26, 0, 12)), (2.0, (0, 0, 0)))
    a.rot("hat", (0, (0, 0, 0)), (0.3, (0, 0, 18)), (1.6, (0, 0, 20)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-40, 0, 10)), (1.6, (-38, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (20, 0, -16)), (1.6, (22, 0, -16)), (2.0, (0, 0, 0)))
