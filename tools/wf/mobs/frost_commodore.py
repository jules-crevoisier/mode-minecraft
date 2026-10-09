"""The Frozen Commodore (Le Commodore gelé): the champion of the Icebound Fleet, about 3.8 blocks tall.

Silhouette idea: the expedition's commander, dead in the ice but kept moving by a frost-rimed brass life-support rig.
A huge, broad figure in a long navy greatcoat lined and collared with grey fur, double-breasted with brass buttons and
gold epaulettes, the whole coat crusted with patches of ice and fringed with icicles at the hem and the cuffs. His head
is an iron hood made like a diving helmet: a domed iron bell on a brass collar ring, a round porthole visor in front,
cracked and frosted, glowing pale blue from inside; a frozen white beard spills out under the visor in a fan of
icicles. On his back a copper boiler drum (the life-support rig) in brass hoops, iced over, with two vent pipes over
his shoulders venting cold steam and two hoses running into the helmet. Fur-topped sea boots. Asymmetry: his RIGHT hand
grips a huge ice-encrusted ship's anchor by its shank, its chain wound round his forearm; his LEFT hand holds a stubby
brass signal-flare pistol with a wide barrel.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

NAVY = (44, 56, 82)            # the greatcoat's wool
NAVY_L = (68, 84, 114)
NAVY_D = (28, 35, 54)
NAVY_DD = (18, 22, 36)
FUR = (196, 188, 170)          # grey-white fur
FUR_L = (226, 220, 204)
FUR_D = (146, 136, 118)
FUR_DD = (104, 96, 82)
ICE = (190, 228, 248)
ICE_L = (236, 250, 255)
ICE_D = (128, 178, 214)
ICE_DD = (84, 132, 172)
FROST = (170, 228, 255)        # the glow of the rig and the visor
FROST_L = (226, 248, 255)
GOLD = (226, 186, 84)
GOLD_D = (160, 118, 44)
SKIN = (150, 170, 184)         # frostbitten, blue-grey
TROUSER = (36, 38, 46)
LEATHER = (60, 40, 30)
LEATHER_D = (38, 26, 20)


# ---------------------------------------------------------------- paint
def iced(base, seed=0, amount=0.16):
    """Wraps a paint function: patches of ice crust over it (more toward the bottom of each face)."""
    def f(face, x, y, w, h):
        c = base(face, x, y, w, h) if callable(base) else base
        if face == "bottom":
            return c
        bias = 0.08 * y / max(1, h) if face != "top" else 0.1
        r = B.n(x // 2, y // 2, seed)
        if r < amount + bias:
            return ICE_L if B.n(x, y, seed + 3) > 0.7 else (ICE if r < (amount + bias) * 0.6 else ICE_D)
        return c
    return f


def wool(seed=0):
    """Navy greatcoat wool: a faint twill, darker folds."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return NAVY_DD
        r = B.n(x, y, seed)
        if face == "top":
            return NAVY_L if r > 0.75 else NAVY
        if (x + y) % 5 == 0:
            return NAVY_D
        return mul(NAVY, 0.92 + r * 0.18)
    return f


def coat(face, x, y, w, h):
    """The greatcoat's body (20 x 24 x 12): double-breasted, two rows of brass buttons, a fur placket down the middle
    under the collar, a black leather belt with a brass buckle low down, ice crusting it here and there."""
    base = wool(11)(face, x, y, w, h)
    if face in ("top", "bottom"):
        return base
    if y in (17, 18):
        if face == "front" and abs(x - (w - 1) / 2) <= 2:
            return GOLD if y == 17 else GOLD_D                                         # the buckle
        return LEATHER if y == 17 else LEATHER_D                                       # the belt
    if face == "front":
        cx = (w - 1) / 2
        if abs(x - cx) <= 0.6:
            return NAVY_DD                                                             # the coat's opening
        if abs(abs(x - cx) - 4) < 0.6 and 3 <= y <= 15 and y % 4 == 3:
            return B.BRASS_L                                                           # the buttons
        if abs(abs(x - cx) - 4) < 0.6 and 3 <= y <= 15 and y % 4 == 0:
            return B.BRASS_D
    if face == "back" and 2 <= x <= w - 3 and y >= 19:
        return NAVY_D if x % 3 == 0 else base                                          # the back pleats
    return iced(base, 13, 0.04)(face, x, y, w, h)


def skirt(seed=0):
    """The coat's long skirt panels: wool, a fur trim along the hem, ice and a fringe of icicles at the bottom."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return FUR_D
        if face != "top" and y >= h - 2:
            return FUR if (x + y) % 3 else FUR_D
        base = wool(seed)(face, x, y, w, h)
        return iced(base, seed + 1, 0.05)(face, x, y, w, h)
    return f


def fur(seed=0):
    """Grey-white fur: tufted, a darker shade in the roots."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "bottom":
            return FUR_DD
        if r > 0.72:
            return FUR_L
        if r < 0.18 or (x * 3 + y) % 7 == 0:
            return FUR_D
        return FUR
    return f


def epaulette(face, x, y, w, h):
    """Gold epaulettes with a fringe."""
    if face == "top":
        return GOLD if (x + y) % 3 else (250, 222, 130)
    if face == "bottom":
        return GOLD_D
    return GOLD if x % 2 == 0 else GOLD_D


def fringe(face, x, y, w, h):
    if face in ("top", "bottom"):
        return GOLD_D
    return GOLD if x % 2 == 0 else GOLD_D


def helm(face, x, y, w, h):
    """The iron hood (14 x 13 x 14), a diving bell: riveted dark iron, rimed with frost toward the top."""
    if face == "bottom":
        return B.IRON_D
    r = B.n(x, y, 21)
    if face == "top":
        return ICE_L if r > 0.55 else (ICE if r > 0.3 else B.IRON_L)
    if y in (0, 1) and r > 0.35:
        return ICE if r > 0.6 else ICE_D                                               # frost on the dome
    if y == h - 1 or (y == 4 and x % 3 == 1):
        return B.BRASS_L if y == 4 else B.IRON_D                                       # rivets round the bell
    return mul(B.IRON, 0.95 + (r - 0.5) * 0.18)


def dome(face, x, y, w, h):
    if face == "bottom":
        return B.IRON_D
    r = B.n(x, y, 25)
    return ICE_L if r > 0.5 else (ICE if r > 0.25 else B.IRON_L)


def collar_ring(face, x, y, w, h):
    """The brass collar ring the hood is bolted to."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    if x % 3 == 1 and y == 0:
        return B.BRASS_L
    return B.BRASS if y == 0 else B.BRASS_D


VISOR = ["..####..",
         ".#....#.",
         "#......#",
         "#......#",
         "#......#",
         "#......#",
         ".#....#.",
         "..####.."]
CRACK = {(2, 2), (3, 3), (3, 4), (4, 4), (5, 5), (4, 2), (5, 1), (2, 5)}


def visor(face, x, y, w, h):
    """The round porthole visor (8 x 8 x 1): a brass bezel, the glass cracked and frosted, pale blue light inside."""
    if face != "front":
        return B.BRASS_D
    ch = VISOR[y][x] if y < len(VISOR) and x < len(VISOR[y]) else "."
    if ch == "#":
        return B.BRASS_L if y < 3 else B.BRASS
    if (x, y) in ((0, 0), (7, 0), (0, 7), (7, 7), (1, 0), (0, 1), (6, 0), (7, 1), (0, 6), (1, 7), (6, 7), (7, 6)):
        return B.IRON
    if (x, y) in CRACK:
        return ICE_L
    return FROST if (x + y) % 3 else ICE


def visor_glow(face, x, y, w, h):
    if face != "front":
        return None
    ch = VISOR[y][x] if y < len(VISOR) and x < len(VISOR[y]) else "."
    if ch == "#" or (x, y) in ((0, 0), (7, 0), (0, 7), (7, 7), (1, 0), (0, 1), (6, 0), (7, 1), (0, 6), (1, 7), (6, 7),
                                (7, 6)):
        return None
    if (x, y) in CRACK:
        return FROST_L
    return FROST if 2 <= x <= 5 and 2 <= y <= 5 else None


def beard(face, x, y, w, h):
    """The frozen beard: white hair turning to ice toward the tips."""
    if face == "top":
        return FUR_L
    k = y / max(1, h - 1)
    if k > 0.6:
        return ICE_L if (x + y) % 2 else ICE
    if x % 2 == 0:
        return FUR_L
    return mix(FUR_L, ICE, k)


def icicle(face, x, y, w, h):
    if face == "top":
        return ICE
    return ICE_L if x == 0 or y < h // 2 else ICE_D


def boiler(face, x, y, w, h):
    """The life-support boiler on his back (12 x 16 x 7): copper in brass hoops, iced over, a gauge on its side."""
    if face == "top":
        return ICE_L if B.n(x, y, 31) > 0.4 else B.COPPER_D
    if face == "bottom":
        return B.COPPER_D
    if y % 5 in (0, 1):
        return B.BRASS_L if (y % 5 == 0 and x % 3 == 1) else (B.BRASS if y % 5 == 0 else B.BRASS_D)
    base = B.copper(33, grad=0.3)(face, x, y, w, h)
    return iced(base, 35, 0.12)(face, x, y, w, h)


def pipe(face, x, y, w, h):
    """A vent pipe: copper turning white with frost toward the mouth."""
    if face == "top":
        return B.SOOT
    k = 1 - y / max(1, h - 1)
    if k > 0.6 and B.n(x, y, 37) > 0.3:
        return ICE_L
    return mix(B.COPPER, ICE, k * 0.5)


def hose(face, x, y, w, h):
    """A ribbed rubber hose."""
    return (40, 44, 50) if (x + y) % 2 else (62, 66, 74)


def steam(face, x, y, w, h):
    return (236, 246, 255, 190) if (x + y) % 2 else (210, 230, 246, 160)


def gauge(face, x, y, w, h):
    if face != "front":
        return B.BRASS_D
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if y == 0 else B.BRASS_D
    if (x, y) == (1, 1):
        return (190, 30, 30)
    return B.CREAM


def frost_glow(face, x, y, w, h):
    """A pale blue glow over a small rig window."""
    return FROST if (x + y) % 2 else FROST_L


def sleeve(seed=0):
    def f(face, x, y, w, h):
        if face != "top" and y >= h - 2:
            return fur(seed + 2)(face, x, y, w, h)                                    # the fur cuff
        return iced(wool(seed), seed + 1, 0.04)(face, x, y, w, h)
    return f


def glove(face, x, y, w, h):
    if face == "bottom":
        return LEATHER_D
    return LEATHER if (x + y) % 4 else LEATHER_D


def trousers(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "bottom":
            return NAVY_DD
        return mul(TROUSER, 0.9 + r * 0.2)
    return f


def boot(seed=0):
    """Black sea boots with a fur top, salt and ice on the toes."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return (20, 18, 18)
        r = B.n(x, y, seed)
        if face != "top" and y >= h - 2 and r > 0.5:
            return ICE_D
        return (30, 28, 30) if r > 0.3 else (46, 42, 44)
    return f


def anchor_iron(seed=0):
    """The anchor's iron: black and pitted, half buried in ice."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "top":
            return ICE_L if r > 0.3 else ICE
        if r > 0.82:
            return ICE_L
        if r > 0.7:
            return ICE
        return mul(B.IRON, 0.85 + r * 0.3)
    return f


def anchor_ice(face, x, y, w, h):
    """A clear crust of ice on the anchor."""
    r = B.n(x, y, 47)
    return ICE_L if r > 0.5 else (ICE if r > 0.2 else ICE_D)


def link(face, x, y, w, h):
    if face in ("top", "bottom"):
        return (120, 126, 136)
    return (168, 174, 186) if y in (0, h - 1) else (110, 116, 128)


def pistol(face, x, y, w, h):
    """The signal-flare pistol: a stubby brass barrel, a mahogany grip."""
    if face == "front":
        return B.SOOT if 0 < x < w - 1 and 0 < y < h - 1 else B.BRASS_D
    return B.BRASS_L if y == 0 else (B.BRASS if (x + y) % 3 else B.BRASS_D)


def flare(face, x, y, w, h):
    return (255, 120, 60) if (x + y) % 2 else (255, 200, 120)


# ---------------------------------------------------------------- build
def build():
    m = Model("frost_commodore", seed=913, shadow=1.6, walk_speed=0.6, walk_scale=0.8, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -24, 0))
    m.part("skirt_f", "hips", pivot=(0, 2, -6))
    m.part("skirt_b", "hips", pivot=(0, 2, 6))
    m.part("chest", "hips", pivot=(0, -2, 0))
    m.part("head", "chest", pivot=(0, -25, -1))
    m.part("beard", "head", pivot=(0, -1, -6))
    m.part("rig", "chest", pivot=(0, -14, 7))
    m.part("steam", "rig", pivot=(0, -18, 2))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5 * sx, -24, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 12, 0))
    m.part("arm_r", "chest", pivot=(-13, -22, 0), rot=(-6, 0, 16))
    m.part("fore_r", "arm_r", pivot=(-0.5, 11, 0), rot=(-30, 0, -4))
    m.part("anchor", "fore_r", pivot=(0, 11, -1), rot=(60, 0, 0))
    m.part("arm_l", "chest", pivot=(13, -22, 0), rot=(-6, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0.5, 11, 0), rot=(-40, 0, 4))
    m.part("pistol", "fore_l", pivot=(0, 11, -1), rot=(60, 0, 0))

    # ---- legs: dark trousers, fur-topped sea boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3.5, -1, -3.5, 7, 13, 7, trousers(1 + sx))
        m.box(shin, -3.5, 0, -3.5, 7, 6, 7, trousers(3 + sx))
        m.box(shin, -4, 2, -4, 8, 3, 8, fur(5 + sx))                                  # the boot's fur top
        m.box(shin, -4, 5, -4, 8, 6, 8, boot(7 + sx))
        m.box(shin, -4, 9, -6.5, 8, 3, 3, boot(9 + sx))                               # the toe
        m.box(shin, -3, 10.6, -6.8, 6, 1, 1, ICE_D)                                   # ice on the toe cap

    # ---- hips and the long coat skirt (split front and back panels, down to the boots' tops)
    m.box("hips", -10, -2, -6.5, 20, 5, 13, wool(20))
    m.box("skirt_f", -10.5, 0, -1, 10, 17, 1, skirt(21))                              # the two front panels
    m.box("skirt_f", 0.5, 0, -1, 10, 17, 1, skirt(22))
    m.box("skirt_b", -10.5, 0, 0, 21, 18, 1, skirt(23))                               # the back panel
    m.box("hips", -11, 0, -6, 1, 15, 12, skirt(24))                                    # the sides
    m.box("hips", 10, 0, -6, 1, 15, 12, skirt(25))
    for k, x in enumerate((-9, -6, -2, 3, 7)):                                        # icicles off the hem
        m.box("skirt_f", x, 17, -1, 1, 2 + k % 2, 1, icicle)
    for k, x in enumerate((-8, -3, 2, 6, 9)):
        m.box("skirt_b", x, 18, 0, 1, 2 + (k + 1) % 2, 1, icicle)

    # ---- the greatcoat's body, the fur collar, the epaulettes
    m.box("chest", -10, -24, -6, 20, 24, 12, coat)
    m.box("chest", -9, -27, -7, 18, 5, 14, fur(30))                                   # the great fur collar
    m.box("chest", -2, -22, -6.6, 4, 12, 1, fur(31))                                  # the fur placket
    m.box("chest", -15, -25, -5, 6, 3, 10, epaulette)
    m.box("chest", 9, -25, -5, 6, 3, 10, epaulette)
    m.box("chest", -15.5, -22, -5, 1, 3, 10, fringe)
    m.box("chest", 14.5, -22, -5, 1, 3, 10, fringe)
    m.box("chest", 5, -20, -6.8, 3, 2, 1, (180, 40, 40))                              # a ribbon bar
    m.box("chest", 5, -18, -6.8, 3, 1, 1, GOLD)

    # ---- the iron hood: a diving bell on a brass collar, the cracked porthole visor, the frozen beard
    m.box("head", -8, -1, -8, 16, 2, 16, collar_ring)
    m.box("head", -7, -14, -7, 14, 13, 14, helm)
    m.box("head", -5, -16, -5, 10, 2, 10, dome)
    m.box("head", -4, -11, -8, 8, 8, 1, visor, glow=visor_glow)
    m.box("head", -5, -12, -8.6, 10, 1, 1, B.BRASS_D)                                 # the visor's guard bars
    m.box("head", -0.5, -12, -8.8, 1, 10, 1, B.BRASS_D)
    m.box("head", -8.6, -9, -2, 2, 4, 4, B.brass(40))                                 # side ports
    m.box("head", 6.6, -9, -2, 2, 4, 4, B.brass(41))
    m.box("head", -1.5, -17, -1.5, 3, 1, 3, B.BRASS)                                  # the valve on top
    m.box("beard", -5, 0, -1.5, 10, 4, 2, beard)                                       # the beard spills out
    m.box("beard", -4, 4, -1.6, 8, 4, 2, beard)
    m.box("beard", -3, 8, -1.4, 6, 3, 1, beard)
    for k, x in enumerate((-4, -2, 0.5, 2.5)):                                        # icicles in the beard
        m.box("beard", x, 7 + k % 2 * 2, -1.8, 1, 3 + k % 2, 1, icicle)

    # ---- the life-support rig on his back: the boiler drum, vent pipes, hoses, cold steam
    m.box("rig", -6, -16, 0, 12, 16, 7, boiler)
    m.box("rig", -5, -17.5, 0.5, 10, 2, 6, B.brass(50))                               # its crown
    m.box("rig", 6, -11, 2, 1, 4, 3, gauge)
    m.box("rig", -3, -8, 6.6, 6, 3, 1, frost_glow, glow=frost_glow)                   # the pilot window
    for sx in (-4.5, 3.0):
        m.box("rig", sx, -26, 2, 2, 11, 2, pipe)                                      # the vent pipes
        m.box("rig", sx - 0.5, -27, 1.5, 3, 1, 3, B.brass(51 + int(sx)))
        m.box("steam", sx - 1.5, -12, -1, 4, 4, 4, steam)                             # cold steam over them
        m.box("steam", sx - 0.5, -15, 0, 2, 3, 2, steam)
    m.box("rig", -8, -14, -3, 2, 2, 4, hose)                                          # hoses into the helmet
    m.box("rig", 6, -14, -3, 2, 2, 4, hose)
    m.box("rig", -8, -16, -6, 2, 2, 3, hose)
    m.box("rig", 6, -16, -6, 2, 2, 3, hose)

    # ---- right arm: the sleeve, the glove, the anchor (its chain wound round the forearm)
    m.box("arm_r", -4, -2, -3.5, 7, 13, 7, sleeve(60))
    m.box("fore_r", -3.5, 0, -3.5, 7, 11, 7, sleeve(62))
    m.box("fore_r", -4, 2, -4, 8, 1, 8, link)                                         # the chain wound round
    m.box("fore_r", -4, 5, -4, 8, 1, 8, link)
    m.box("fore_r", -3, 11, -3, 6, 4, 6, glove)
    m.box("fore_r", -2, 12, -5, 2, 1, 1, icicle)                                      # an icicle off the cuff
    # the anchor: held by the shank just under the stock, the crown far below the fist
    m.box("anchor", -1.5, -14, -1.5, 3, 34, 3, anchor_iron(70))                        # the shank
    m.box("anchor", -0.5, -17, -2.5, 1, 3, 5, anchor_iron(71))                        # the ring at the top
    m.box("anchor", -1.5, -16, -1, 3, 1, 2, anchor_iron(72))
    m.box("anchor", -6, -10, -1, 12, 2, 2, anchor_iron(73))                            # the stock
    m.box("anchor", -7, -10.5, -1.5, 2, 3, 3, B.brass(74))
    m.box("anchor", 5, -10.5, -1.5, 2, 3, 3, B.brass(75))
    m.box("anchor", -2, 18, -3, 4, 4, 6, anchor_iron(76))                             # the crown
    m.box("anchor", -1.5, 15, -8, 3, 4, 5, anchor_iron(77))                           # the arms curving up
    m.box("anchor", -1.5, 15, 3, 3, 4, 5, anchor_iron(78))
    m.box("anchor", -1.5, 10, -11, 3, 6, 4, anchor_iron(79))
    m.box("anchor", -1.5, 10, 7, 3, 6, 4, anchor_iron(80))
    m.box("anchor", -2.5, 6, -13, 5, 5, 5, anchor_iron(81))                          # the spade flukes
    m.box("anchor", -2.5, 6, 8, 5, 5, 5, anchor_iron(82))
    m.box("anchor", -2.5, 2, -2.5, 5, 10, 5, anchor_ice)                              # the ice crust
    m.box("anchor", -2.5, 16, -4, 5, 3, 8, anchor_ice)
    m.box("anchor", -0.5, 11, -12, 1, 4, 1, icicle)                                   # icicles off the flukes
    m.box("anchor", -0.5, 11, 11, 1, 4, 1, icicle)
    m.box("anchor", -0.5, 22, -0.5, 1, 3, 1, icicle)
    for k in range(3):                                                                # the chain to his wrist
        m.box("anchor", -0.5 - (k % 2) * 0.5, -20 - k * 2, -0.5 + (k % 2) * 0.5, 1 + k % 2, 2, 1, link)

    # ---- left arm: the sleeve, the glove, the flare pistol
    m.box("arm_l", -3, -2, -3.5, 7, 13, 7, sleeve(64))
    m.box("fore_l", -3.5, 0, -3.5, 7, 11, 7, sleeve(66))
    m.box("fore_l", -3, 11, -3, 6, 4, 6, glove)
    m.box("pistol", -1, 2, -1.5, 2, 4, 3, B.MAHOGANY_D)                               # the grip
    m.box("pistol", -1.5, 0, -7, 3, 3, 9, pistol)                                     # the stubby barrel
    m.box("pistol", -2, -0.5, -8, 4, 4, 2, pistol)                                    # its wide mouth
    m.box("pistol", -1, 0.5, -8.2, 2, 2, 1, flare, glow=flare)                        # the flare inside

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.2)
    idle.pos("chest", (0, (0, 0, 0)), (1.6, (0, 0.6, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.6, (4, -5, 0)), (3.2, (0, 0, 0)))
    idle.scale("steam", (0, (1, 1, 1)), (0.8, (1.2, 1.4, 1.2)), (1.6, (0.8, 0.9, 0.8)), (2.4, (1.25, 1.5, 1.25)),
               (3.2, (1, 1, 1)))
    idle.rot("skirt_f", (0, (0, 0, 0)), (1.6, (-3, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.6, (4, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("fore_r", (0, (-30, 0, -4)), (1.6, (-34, 0, -4)), (3.2, (-30, 0, -4)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (18, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (18, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.0, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.0, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 5, 2)), (1.0, (0, -5, -2)), (2.0, (0, 5, 2)))
    walk.rot("skirt_f", (0, (-10, 0, 0)), (1.0, (-4, 0, 0)), (2.0, (-10, 0, 0)))
    walk.rot("skirt_b", (0, (6, 0, 0)), (1.0, (12, 0, 0)), (2.0, (6, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, -8)), (1.0, (-10, 0, -8)), (2.0, (10, 0, -8)))
    walk.rot("arm_r", (0, (-10, 0, 8)), (1.0, (6, 0, 8)), (2.0, (-10, 0, 8)))

    # anchor (18 / 22 / 14): the anchor hauled back over his right shoulder (0.9 s), swung round across his body at
    # 0.9 s (the forehand), then hauled back the other way at 1.5 s (the backhand); he settles
    a = m.anim("anchor", 2.7)
    a.rot("arm_r", (0, (-6, 0, 16)), (0.8, (-80, 70, 30)), (0.9, (-84, 74, 30)), (0.96, (-80, -60, -10), "linear"),
          (1.4, (-76, -66, -14)), (1.5, (-76, -66, -14)), (1.56, (-80, 60, 30), "linear"), (2.0, (-60, 50, 24)),
          (2.7, (-6, 0, 16)))
    a.rot("anchor", (0, (60, 0, 0)), (0.9, (-80, 0, 0)), (0.96, (-90, 0, 0), "linear"), (1.5, (-90, 0, 0)),
          (1.56, (-84, 0, 0), "linear"), (2.7, (60, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (2, 40, 0)), (0.9, (2, 44, 0)), (0.96, (4, -36, 0), "linear"),
          (1.5, (4, -40, 0)), (1.56, (4, 30, 0), "linear"), (2.0, (2, 24, 0)), (2.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (1.5, (10, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.9, (12, 0, 0)), (1.5, (-10, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("skirt_b", (0, (0, 0, 0)), (0.96, (20, 0, 10)), (1.56, (20, 0, -10)), (2.7, (0, 0, 0)))

    # throw (24 / 36 / 14): the anchor whirled round his head on its chain (1.2 s), let fly at 1.2 s (the anchor is
    # gone from his hand while it flies and bites), the chain hauled in hand over hand; it slams back into his grip
    # at 2.7 s
    a = m.anim("throw", 3.7)
    a.rot("arm_r", (0, (-6, 0, 16)), (0.4, (-160, 0, 20)), (0.7, (-160, 90, 20)), (1.0, (-160, 180, 20)),
          (1.2, (-150, 0, 10)), (1.26, (-80, 0, 0), "linear"), (1.6, (-70, 0, 10)), (2.0, (-40, 0, 20)),
          (2.3, (-70, 0, 10)), (2.6, (-40, 0, 20)), (2.7, (-60, 0, 10)), (3.7, (-6, 0, 16)))
    a.scale("anchor", (0, (1, 1, 1)), (1.2, (1, 1, 1)), (1.22, (0.02, 0.02, 0.02), "linear"),
            (2.68, (0.02, 0.02, 0.02)), (2.7, (1, 1, 1), "linear"), (3.7, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-6, 20, 0)), (1.26, (14, -20, 0), "linear"), (2.7, (6, -6, 0)),
          (3.7, (0, 0, 0)))
    a.rot("arm_l", (0, (-6, 0, -8)), (1.2, (-20, 0, -30)), (1.6, (-50, -30, -10)), (2.0, (-30, 0, -20)),
          (2.3, (-50, -30, -10)), (2.7, (-30, 0, -20)), (3.7, (-6, 0, -8)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.2, (16, 0, 0)), (2.7, (10, 0, 0)), (3.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.2, (-18, 0, 0)), (2.7, (-12, 0, 0)), (3.7, (0, 0, 0)))

    # spikes (20 / 30 / 14): the anchor raised high in both hands (1.0 s) and driven flukes-first into the deck at
    # 1.0 s; he leans on it while the spikes run out
    a = m.anim("spikes", 3.2)
    a.rot("arm_r", (0, (-6, 0, 16)), (0.9, (-170, 0, 20)), (1.0, (-174, 0, 20)), (1.06, (-50, 0, 10), "linear"),
          (2.5, (-48, 0, 10)), (3.2, (-6, 0, 16)))
    a.rot("arm_l", (0, (-6, 0, -8)), (0.9, (-160, 0, -20)), (1.0, (-164, 0, -20)), (1.06, (-50, 0, -10), "linear"),
          (2.5, (-48, 0, -10)), (3.2, (-6, 0, -8)))
    a.rot("anchor", (0, (60, 0, 0)), (1.0, (-10, 0, 0)), (1.06, (-20, 0, 0), "linear"), (2.5, (-20, 0, 0)),
          (3.2, (60, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (1.06, (24, 0, 0), "linear"), (2.5, (20, 0, 0)), (3.2, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -1, 0)), (1.06, (0, 2.5, 0), "linear"), (2.5, (0, 2.5, 0)), (3.2, (0, 0, 0)))
    a.scale("steam", (0, (1.0, 1.0, 1.0)), (1.06, (1.6, 1.9, 1.6), "linear"), (2.0, (1.3, 1.5, 1.3)), (3.2, (1.0, 1.0, 1.0)))

    # breath (30 / 24 / 16): he throws his head back, the rig wheezing as it fills him with cold (1.5 s), then leans
    # in and breathes a freezing cone through the cracked visor until 2.7 s
    a = m.anim("breath", 3.5)
    a.rot("head", (0, (0, 0, 0)), (1.4, (-30, 0, 0)), (1.5, (-32, 0, 0)), (1.56, (16, 0, 0), "linear"),
          (2.7, (14, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.4, (-14, 0, 0)), (1.5, (-16, 0, 0)), (1.56, (14, 0, 0), "linear"),
          (2.7, (12, 0, 0)), (3.5, (0, 0, 0)))
    a.scale("chest", (0, (1, 1, 1)), (1.4, (1.06, 1.03, 1.08)), (1.56, (0.98, 1, 0.98), "linear"), (2.7, (1, 1, 1)),
            (3.5, (1, 1, 1)))
    a.scale("steam", (0, (1.0, 1.0, 1.0)), (1.4, (0.3, 0.3, 0.3)), (1.56, (1.5, 1.8, 1.5), "linear"), (2.7, (1.4, 1.8, 1.4)),
            (3.5, (1, 1, 1)))
    a.rot("arm_r", (0, (-6, 0, 16)), (1.5, (-10, 0, 30)), (2.7, (-10, 0, 30)), (3.5, (-6, 0, 16)))
    a.rot("arm_l", (0, (-6, 0, -8)), (1.5, (-10, 0, -30)), (2.7, (-10, 0, -30)), (3.5, (-6, 0, -8)))
    a.rot("beard", (0, (0, 0, 0)), (1.56, (-30, 0, 0), "linear"), (2.7, (-24, 0, 0)), (3.5, (0, 0, 0)))

    # hurl (20 / 12 / 14): the anchor dragged low behind him through the deck's ice (1.0 s), then heaved up in an
    # uppercut at 1.0 s that tears blocks of ice loose and flings them high
    a = m.anim("hurl", 2.3)
    a.rot("arm_r", (0, (-6, 0, 16)), (0.9, (40, 0, 20)), (1.0, (44, 0, 20)), (1.06, (-150, 0, 10), "linear"),
          (1.5, (-140, 0, 10)), (2.3, (-6, 0, 16)))
    a.rot("anchor", (0, (60, 0, 0)), (1.0, (-100, 0, 0)), (1.06, (-20, 0, 0), "linear"), (2.3, (60, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (24, 20, 0)), (1.06, (-14, -10, 0), "linear"), (1.5, (-10, -8, 0)),
          (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 2, 0)), (1.06, (0, -1, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.0, (20, 0, 0)), (1.5, (-6, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.5, (6, 0, 0)), (2.3, (0, 0, 0)))

    # strays (phase 2, 20 / 10 / 16): the flare pistol raised straight up (1.0 s) and fired at 1.0 s: the signal
    # calls the frozen crew
    a = m.anim("strays", 2.3)
    a.rot("arm_l", (0, (-6, 0, -8)), (0.8, (-176, 0, -6)), (1.0, (-178, 0, -6)), (1.06, (-168, 0, -10), "linear"),
          (1.6, (-170, 0, -8)), (2.3, (-6, 0, -8)))
    a.rot("fore_l", (0, (-40, 0, 4)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)), (2.3, (-40, 0, 4)))
    a.rot("pistol", (0, (30, 0, 0)), (0.8, (90, 0, 0)), (1.6, (90, 0, 0)), (2.3, (30, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-24, 0, 0)), (1.6, (-24, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (1.06, (-10, 0, 0), "linear"), (2.3, (0, 0, 0)))

    # flare (phase 2, 16 / 10 / 12): the pistol levelled at you (0.8 s), the shot at 0.8 s and its kick
    a = m.anim("flare", 1.9)
    a.rot("arm_l", (0, (-6, 0, -8)), (0.6, (-88, 0, 4)), (0.8, (-90, 0, 4)), (0.86, (-110, 0, 4), "linear"),
          (1.2, (-96, 0, 4)), (1.9, (-6, 0, -8)))
    a.rot("fore_l", (0, (-40, 0, 4)), (0.6, (0, 0, 0)), (1.2, (0, 0, 0)), (1.9, (-40, 0, 4)))
    a.rot("pistol", (0, (30, 0, 0)), (0.6, (90, 0, 0)), (1.2, (90, 0, 0)), (1.9, (30, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (0, -20, 0)), (0.86, (-4, -16, 0), "linear"), (1.9, (0, 0, 0)))

    # blizzard (phase 3, 40 / 20 / 20): the rig's valves thrown wide: he lifts the anchor and the pistol, the steam
    # roaring white (2.0 s), and brings the anchor down on the deck at 2.0 s; the blizzard closes in
    a = m.anim("blizzard", 4.0)
    a.rot("arm_r", (0, (-6, 0, 16)), (1.0, (-150, 0, 40)), (2.0, (-170, 0, 30)), (2.06, (-40, 0, 10), "linear"),
          (3.2, (-40, 0, 10)), (4.0, (-6, 0, 16)))
    a.rot("arm_l", (0, (-6, 0, -8)), (1.0, (-150, 0, -40)), (2.0, (-160, 0, -30)), (2.06, (-60, 0, -40), "linear"),
          (3.2, (-60, 0, -40)), (4.0, (-6, 0, -8)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-6, 4, 2)), (0.8, (-6, -4, -2)), (1.1, (-6, 4, 2)), (1.4, (-6, -4, -2)),
          (2.0, (-16, 0, 0)), (2.06, (22, 0, 0), "linear"), (3.2, (18, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-26, 0, 0)), (2.06, (10, 0, 0), "linear"), (4.0, (0, 0, 0)))
    a.scale("steam", (0, (1.0, 1.0, 1.0)), (2.0, (1.6, 1.9, 1.6)), (2.06, (1.7, 2.0, 1.7), "linear"), (3.2, (1.6, 1.9, 1.6)),
            (4.0, (1, 1, 1)))
    a.pos("hips", (0, (0, 0, 0)), (2.0, (0, -1, 0)), (2.06, (0, 2, 0), "linear"), (3.2, (0, 2, 0)), (4.0, (0, 0, 0)))

    # ramshock (phase 3, 30 / 40 / 16): he plants the anchor and braces against it, bellowing (1.5 s); the ship rams
    # the floe at 1.5 s and he rides the lurch, swaying, until the deck settles
    a = m.anim("ramshock", 4.3)
    a.rot("arm_r", (0, (-6, 0, 16)), (0.6, (-50, 0, 10)), (1.5, (-50, 0, 10)), (2.0, (-44, 0, 16)), (2.6, (-52, 0, 6)),
          (3.4, (-48, 0, 10)), (4.3, (-6, 0, 16)))
    a.rot("anchor", (0, (60, 0, 0)), (0.6, (-20, 0, 0)), (3.4, (-20, 0, 0)), (4.3, (60, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (14, 0, 0)), (1.4, (-10, 0, 0)), (1.5, (-12, 0, 0)), (1.56, (16, 0, 6), "linear"),
          (2.0, (8, 0, -6)), (2.6, (12, 0, 4)), (3.4, (6, 0, 0)), (4.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.4, (-24, 0, 0)), (1.56, (10, 0, 0), "linear"), (4.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.6, (0, 1.5, 0)), (1.56, (0, 2.5, 0), "linear"), (2.0, (0, 1.0, 0)),
          (2.6, (0, 2.0, 0)), (4.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (-20, 0, 6)), (3.4, (-20, 0, 6)), (4.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (20, 0, -6)), (3.4, (20, 0, -6)), (4.3, (0, 0, 0)))
    a.rot("skirt_f", (0, (0, 0, 0)), (1.56, (-30, 0, 0), "linear"), (2.6, (-14, 0, 0)), (4.3, (0, 0, 0)))

    # roar (phase two): the hood thrown back, arms wide, the rig blasting steam
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-28, 0, 0)), (1.6, (-26, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-6, 0, 16)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (-6, 0, 16)))
    a.rot("arm_l", (0, (-6, 0, -8)), (0.5, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (-6, 0, -8)))
    a.scale("steam", (0, (1.0, 1.0, 1.0)), (0.5, (1.6, 1.9, 1.6)), (1.6, (1.6, 1.9, 1.6)), (2.0, (1.0, 1.0, 1.0)))
    a.rot("beard", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.6, (-20, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: the rig sputters, he sinks to one knee, leaning on the anchor
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, 6, 0)), (1.6, (0, 6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 6)), (1.6, (28, 0, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -10)), (1.6, (26, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-6, 0, 16)), (0.3, (-40, 0, 20)), (1.6, (-40, 0, 20)), (2.0, (-6, 0, 16)))
    a.scale("steam", (0, (1.0, 1.0, 1.0)), (0.3, (0.2, 0.2, 0.2)), (1.6, (0.3, 0.3, 0.3)), (2.0, (1.0, 1.0, 1.0)))
