"""Art of the vault gear of the colossal structures (wf/colossal_gear.py): painted item sprites (itemart primitives,
one light from the top-left, auto outline), the six armour layers worn on the body (64x32 humanoid UVs, each face
shaded from the top-left with the set's own plates, trims and emblems) and the 3D in-hand archetypes of the six
weapons (registered into held3d.ARCHETYPES / HELD when held3d is imported).

Keys: M material, H handle, A accent, plus itemart.STEAM (B brass, C copper, V verdigris, I steel, X dark iron,
W mahogany, T oak, L oxblood, N tan leather, Q cream, E aether, R amber, F flame, G glass, K ink, S sculk glow,
Z ruby, Y sparkle).
"""
import math
import random

from . import itemart
from .itemart import painted, tones
from .itemart_shapes import L, collar, shaft
from .png import Canvas
from .sprites import ACCENTS, HANDLES, MATERIALS

# the materials of the six sets (light, mid, dark, outline), added to the shared palette so held3d can use them too
COLOSSAL_MATERIALS = {
    "lockbrass": ((244, 220, 146), (192, 152, 74), (120, 88, 40), (48, 32, 14)),
    "engineer": ((176, 182, 192), (116, 122, 134), (68, 72, 84), (24, 26, 32)),
    "bogreed": ((184, 176, 112), (128, 122, 72), (82, 78, 44), (32, 30, 16)),
    "sungold": ((255, 238, 156), (234, 190, 66), (170, 118, 28), (70, 44, 8)),
    "navyiron": ((138, 152, 178), (86, 98, 126), (50, 58, 82), (18, 22, 36)),
    "stalker": ((158, 174, 102), (100, 122, 64), (60, 80, 42), (22, 30, 14)),
    "jade": ((176, 242, 196), (86, 188, 130), (38, 118, 82), (12, 46, 30)),
}
for _k, _v in COLOSSAL_MATERIALS.items():
    MATERIALS.setdefault(_k, _v)


def render(shape, mat, handle="dark", accent="gold"):
    return itemart.sprite(shape, {"M": MATERIALS[mat], "H": itemart.two_tone(*HANDLES[handle]),
                                  "A": itemart.two_tone(*ACCENTS[accent])})


def _rivets(a, cells, key="B"):
    for x, y in cells:
        if a.m[y][x] is not None:
            a.px(x, y, key, "shine")


# ================================================================== Lock-Keeper's Brass (Great Aqueduct)
@painted("colossal_lockkeeper_helmet")
def lock_helmet(a):
    """Diving helm: a round brass dome, a big round porthole of aether glass with a bolted rim, a collar of dark iron."""
    a.disc("M", 7.5, 7.0, 6.3)
    a.clear(lambda x, y: y > 12.2)
    a.shade_dir("M", 1.0, 0.8, cuts=(-0.55, 0.15, 0.7))
    a.disc("B", 7.5, 7.4, 3.7)                      # the porthole rim
    a.sphere("G", 7.5, 7.4, 2.6)                    # the glass
    a.px(6, 6, "Y", "light")
    a.px(5, 7, "Y", "mid")
    for x, y in ((7, 3), (4, 7), (11, 7), (7, 11)):  # the rim's bolts
        a.px(x, y, "X", "mid")
    a.box("X", 2, 12, 13, 13)                       # the collar
    for x in range(2, 14):
        a.px(x, 12, "X", "light" if x < 8 else "mid")
        a.px(x, 13, "X", "dark")
    _rivets(a, [(3, 13), (6, 13), (9, 13), (12, 13)])
    a.px(4, 3, "M", "shine")
    a.px(5, 2, "M", "shine")
    for x, y in ((2, 9), (12, 10)):                  # verdigris bloom
        a.px(x, y, "V", "dark")


@painted("colossal_lockkeeper_chestplate")
def lock_chest(a):
    """Brass cuirass: riveted plates, a round depth gauge glowing aether blue on the breast, verdigris on the seams."""
    itemart.PAINTED["chestplate"](a)
    for y in range(4, 10):
        a.px(7, y, "M", "light")
        a.px(8, y, "M", "dark")
    _rivets(a, [(3, 5), (3, 8), (12, 5), (12, 8), (4, 11), (11, 11)])
    a.disc("X", 7.9, 6.6, 2.0)
    a.sphere("E", 7.9, 6.6, 1.3, shine=False)
    a.px(7, 6, "Y", "light")
    a.px(8, 7, "K", "mid")
    for x, y in ((10, 9), (2, 4), (6, 12)):
        a.px(x, y, "V", "dark")


@painted("colossal_lockkeeper_leggings")
def lock_legs(a):
    """Wading greaves: brass legs with riveted knee plates and verdigris streaks where the water stood."""
    itemart.PAINTED["leggings"](a)
    for x in (4, 5, 10, 11):
        a.px(x, 7, "B", "light" if x in (4, 10) else "mid")
    _rivets(a, [(3, 5), (12, 5)])
    for x, y in ((3, 10), (12, 11)):
        a.px(x, y, "V", "dark")


@painted("colossal_lockkeeper_boots")
def lock_boots(a):
    """Weighted boots: brass shins on fat lead soles, a riveted toe cap, a glowing gauge on each cuff."""
    a.stamp([
        "..XXX...XXX.....",
        "..MMM...MMM.....",
        "..MMM...MMM.....",
        "..MMM...MMM.....",
        ".MMMMM.MMMMM....",
        "MMMMMM.MMMMMMM..",
        "MMMMMM.MMMMMMM..",
        "XXXXXX.XXXXXXX..",
        "XXXXXX.XXXXXXX..",
    ], {"M": "M", "X": "X"}, 0, 4)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.2, 0.75))
    a.shade_dir("X", 0.3, 1.0, cuts=(-0.3, 0.3, 0.8))
    for x, y in ((3, 4), (9, 4)):
        a.px(x, y, "E", "light")
    _rivets(a, [(1, 9), (4, 9), (8, 9), (12, 9)])
    a.px(3, 6, "M", "shine")
    a.px(9, 6, "M", "shine")
    a.px(5, 10, "V", "mid")


# ================================================================== Turbine Engineer's Rig (Drowned Dam)
@painted("colossal_turbine_engineer_helmet")
def turbine_helmet(a):
    """Goggled cap: a soot-grey leather cap with ear flaps and a short brim, brass goggles with glowing ember lenses."""
    a.stamp([
        ".....MMMMMM.....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        ".MMMMMMMMMMMMMM.",
        "..MM........MM..",
        "..MM........MM..",
        "..MM........MM..",
        "...M........M...",
    ], {"M": "M"}, 0, 3)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.15, 0.7))
    for y in (3, 4, 5, 6):                      # stitched seam down the crown
        a.px(7, y, "M", "deep" if y % 2 else "dark")
    for cx in (5.0, 10.0):                       # goggles on the brim
        a.disc("B", cx, 7.0, 2.1)
        a.sphere("F", cx, 7.0, 1.2, shine=False)
    a.px(4, 6, "F", "shine")
    a.px(9, 6, "F", "shine")
    a.px(7, 7, "B", "mid")
    a.px(8, 7, "B", "dark")
    for x in (1, 14):
        a.px(x, 7, "N", "mid")                   # the strap
    a.px(5, 4, "M", "shine")
    a.px(6, 4, "M", "light")


@painted("colossal_turbine_engineer_chestplate")
def turbine_chest(a):
    """Boiler rig: a steel coat crossed by leather straps, a copper pressure gauge on the chest, pipes over the
    shoulders to the boiler on the back."""
    itemart.PAINTED["chestplate"](a)
    for i in range(8):                            # crossed straps
        a.px(3 + i, 4 + i, "N", "mid" if i % 2 else "light") if a.m[4 + i][3 + i] else None
        a.px(12 - i, 4 + i, "N", "dark" if i % 2 else "mid") if a.m[4 + i][12 - i] else None
    a.disc("C", 7.9, 7.2, 2.1)
    a.disc("Q", 7.9, 7.2, 1.3)
    a.px(8, 6, "Z", "mid")                        # the gauge needle in the red
    a.px(8, 7, "K", "mid")
    a.px(7, 8, "Q", "dark")
    for x, y in ((2, 2), (3, 2), (11, 2), (12, 2)):  # copper pipes over the shoulders
        a.px(x, y, "C", "light" if x < 8 else "mid")
    a.px(2, 3, "C", "dark")
    a.px(12, 3, "C", "dark")
    a.px(7, 10, "B", "light")
    a.px(8, 10, "B", "dark")


@painted("colossal_turbine_engineer_leggings")
def turbine_legs(a):
    """Piston trousers: steel legs braced by bright piston rods along the outsides, copper knee joints."""
    itemart.PAINTED["leggings"](a)
    for y in range(4, 11):
        a.px(3, y, "I", "light" if y % 3 else "mid")
        a.px(12, y, "I", "mid" if y % 3 else "dark")
    for x in (4, 5, 10, 11):
        a.px(x, 7, "C", "light" if x in (4, 10) else "mid")
    a.px(3, 7, "C", "shine")
    a.px(12, 7, "C", "mid")


@painted("colossal_turbine_engineer_boots")
def turbine_boots(a):
    """Hobnail boots: steel-capped work boots with copper cuffs and a row of brass hobnails on the heavy soles."""
    itemart.PAINTED["boots"](a)
    for x in (4, 5, 6, 9, 10, 11):
        a.px(x, 5, "C", "light" if x in (4, 9) else "mid")
    for x in range(0, 15):
        if a.m[12][x] == "X" and x % 2 == 0:
            a.px(x, 12, "B", "light")
    a.px(1, 11, "I", "light")
    a.px(13, 11, "I", "mid")


# ================================================================== Bog Pilgrim's Wraps (Mire Stilt-City)
@painted("colossal_bog_pilgrim_helmet")
def bog_helmet(a):
    """Reed hat: a wide conical hat of woven reed over a dark veil, a marsh-light charm hanging from the brim."""
    a.poly("M", [(7.5, 1.0), (15.6, 9.2), (14.6, 10.4), (0.4, 10.4), (-0.6, 9.2)])
    a.shade_dir("M", 1.0, 0.9, cuts=(-0.5, 0.15, 0.7))
    for y in range(3, 10):                        # the weave: rings around the cone
        for x in range(16):
            if a.m[y][x] == "M" and (y % 3 == 0) and (x + y) % 2 == 0:
                a.tone(x, y, "dark")
            elif a.m[y][x] == "M" and y % 3 == 1 and x % 3 == 0:
                a.tone(x, y, "light")
    a.box("K", 4, 11, 11, 12)                     # the veil
    a.px(5, 12, "K", "dark")
    a.px(10, 12, "K", "dark")
    a.clear(lambda x, y: y > 12 and not (13.0 < x < 14.0))
    a.px(13, 11, "N", "mid")                     # the charm's cord and glowing bead
    a.px(13, 12, "S", "light")
    a.px(13, 13, "S", "mid")
    a.px(7, 2, "M", "shine")
    a.px(6, 3, "M", "light")
    a.px(7, 1, "N", "light")                     # a knot of twine at the tip


@painted("colossal_bog_pilgrim_chestplate")
def bog_chest(a):
    """Waxed coat: a long olive coat with a hood fallen on the shoulders, reed bands across it and a hanging marsh
    lantern charm glowing green."""
    itemart.PAINTED["robe"](a)
    for x in range(16):
        for y in range(16):
            if a.m[y][x] == "B":
                a.px(x, y, "N", "mid" if x % 2 else "light")     # a twine belt instead of gold
    for x, y in ((4, 3), (5, 3), (6, 3), (9, 3), (10, 3), (11, 3)):
        a.px(x, y, "M", "light")
    a.px(7, 3, "M", "deep")
    a.px(8, 3, "M", "deep")
    for y in range(9, 14):                        # reed stripes down the skirt
        for x in (4, 10):
            if a.m[y][x] == "M":
                a.px(x, y, "M", "dark")
    a.px(5, 9, "X", "mid")                        # the lantern charm on the belt
    a.px(5, 10, "S", "light")
    a.px(5, 11, "X", "dark")
    a.px(6, 5, "S", "mid")


@painted("colossal_bog_pilgrim_leggings")
def bog_legs(a):
    """Wrapped leggings: olive cloth bound with diagonal strips of tan gator hide."""
    itemart.PAINTED["leggings"](a)
    for y in range(4, 12):
        for x in range(3, 13):
            if a.m[y][x] == "M" and (x + y) % 4 == 0:
                a.px(x, y, "N", "mid" if (x + y) % 8 else "dark")
    for x in range(3, 13):
        if a.m[2][x] == "A":
            a.px(x, 2, "N", "dark" if x % 2 else "mid")
    a.px(7, 2, "S", "light")


@painted("colossal_bog_pilgrim_boots")
def bog_boots(a):
    """Stilt boots: tall olive boots strapped to raised wooden platforms that keep the pilgrim out of the mud."""
    a.stamp([
        "..MMM...MMM.....",
        "..MMM...MMM.....",
        "..MMM...MMM.....",
        ".MMMM..MMMM.....",
        "MMMMM.MMMMMM....",
        "TTTTT.TTTTTT....",
        ".T.T...T..T.....",
        ".T.T...T..T.....",
        "TTTT..TTTTT.....",
    ], {"M": "M", "T": "T"}, 1, 4)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.2, 0.75))
    for ox in (0, 6):
        for x, y in ((3, 5), (4, 6), (3, 7)):
            a.px(ox + x, y, "N", "light" if y % 2 else "mid")
    a.px(3, 4, "M", "shine")
    a.px(9, 4, "M", "shine")
    a.px(2, 12, "S", "mid")                      # a smear of glowing bog-moss


# ================================================================== Sun-Priest's Regalia (Sun-Engine Ziggurat)
@painted("colossal_sun_priest_helmet")
def sun_helmet(a):
    """Disc crown: a striped gold-and-lapis headcloth falling to the shoulders, a blazing sun disc between two horns."""
    a.stamp([
        "....MMMMMMMM....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMKKKKKKMMM..",
        ".MMMMK....KMMMM.",
        ".MMMM......MMMM.",
        "MMMMM......MMMMM",
        "MMMM........MMMM",
        "MMM..........MMM",
    ], {"M": "M", "K": "K"}, 0, 6)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.2, 0.75))
    for y in range(6, 15):                       # lapis stripes on the headcloth
        for x in range(16):
            if a.m[y][x] == "M" and (y % 2 == 0):
                a.px(x, y, "A", "mid" if x < 8 else "dark")
    for x in range(4, 12):                       # the gold brow band
        a.px(x, 8, "M", "light")
    a.px(7, 9, "Z", "light")                     # a ruby uraeus on the brow
    a.px(8, 9, "Z", "mid")
    a.sphere("F", 7.9, 3.2, 2.6)                 # the sun disc
    a.px(7, 2, "F", "shine")
    for x, y in ((4, 2), (4, 3), (5, 4), (11, 2), (11, 3), (10, 4)):   # the horns cradling it
        a.px(x, y, "M", "mid")
    a.px(4, 1, "M", "light")
    a.px(11, 1, "M", "light")


@painted("colossal_sun_priest_chestplate")
def sun_chest(a):
    """Pectoral: a broad collar of gold and lapis bands over a pale linen tunic, a sun disc at its heart."""
    itemart.PAINTED["chestplate"](a)
    for y in range(4, 12):
        for x in range(16):
            if a.m[y][x] == "M" and y >= 7:
                a.px(x, y, "Q", None)             # the linen below the collar
    for x in range(16):
        if a.m[10][x] == "A":
            a.px(x, 10, "M", "mid")
    for k, (cx, cy) in enumerate(((7.5, 3.0),)):
        a.ring("A", 7.5, 3.0, 2.6, 3.6)
        a.ring("M", 7.5, 3.0, 3.6, 4.6)
        a.ring("A", 7.5, 3.0, 4.6, 5.4)
    a.clear(lambda x, y: y < 2.0 and 4 < x < 11)
    a.sphere("F", 7.5, 5.6, 1.4, shine=False)
    a.px(7, 5, "F", "shine")
    a.px(3, 2, "M", "shine")


@painted("colossal_sun_priest_leggings")
def sun_legs(a):
    """Pleated kilt: a pale linen kilt with fine pleats, a gold belt and a striped lapis-and-gold apron."""
    a.stamp([
        "MMMMMMMMMM",
        "QQQQQQQQQQ",
        "QQQQQQQQQQ",
        "QQQQQQQQQQ",
        "QQQQQQQQQQQ",
        "QQQQQQQQQQQ",
        "QQQQQQQQQQQQ",
        "QQQ......QQQ",
    ], {"M": "M", "Q": "Q"}, 2, 2)
    a.shade_dir("Q", 1.0, 0.4, cuts=(-0.6, 0.25, 0.8))
    for y in range(3, 10):
        for x in range(2, 15):
            if a.m[y][x] == "Q" and x % 2 == 1:
                a.tone(x, y, "dark")
    for y in range(3, 9):                        # the apron down the middle
        a.px(6, y, "A", "light" if y % 2 else "mid")
        a.px(7, y, "M", "light" if y % 2 else "mid")
        a.px(8, y, "A", "mid" if y % 2 else "dark")
    a.px(6, 9, "M", "mid")
    a.px(8, 9, "M", "dark")
    a.px(7, 2, "F", "shine")
    a.px(3, 2, "M", "shine")


@painted("colossal_sun_priest_boots")
def sun_boots(a):
    """Gilded sandals: gold soles, straps crossing up to a lapis-studded ankle band."""
    a.stamp([
        "..MM.....MM.....",
        "..MM.....MM.....",
        "..MMM....MMM....",
        ".MMMMM..MMMMM...",
        "MMMMMMM.MMMMMMM.",
        "MMMMMMM.MMMMMMM.",
    ], {"M": "M"}, 0, 7)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.2, 0.75))
    for ox in (0, 8):
        for x, y in ((2, 8), (3, 9), (2, 10), (4, 10)):
            a.px(ox + x, y, "Q", "light" if (x + y) % 2 else "mid")
        a.px(ox + 2, 7, "A", "light")
        a.px(ox + 3, 7, "A", "mid")
    a.px(1, 11, "M", "shine")
    a.px(9, 11, "M", "light")


# ================================================================== Ironclad Officer's Plate (Dreadnought Wreck)
@painted("colossal_ironclad_helmet")
def iron_helmet(a):
    """Peaked helm: a navy steel dome with a gold braid band, a black lacquered peak, an anchor badge, cheek plates."""
    a.stamp([
        "....MMMMMMM.....",
        "...MMMMMMMMM....",
        "..MMMMMMMMMMM...",
        "..MMMMMMMMMMM...",
        "..AAAAAAAAAAA...",
        "KKKKKKKKKKKKKK..",
        ".KKMMMMMMMMMKK..",
        "...MM.....MM....",
        "...MM.....MM....",
        "....M.....M.....",
    ], {"M": "M", "A": "A", "K": "K"}, 1, 3)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.15, 0.7))
    a.shade_dir("A", 1.0, 0.0, cuts=(-0.5, 0.3, 0.8))
    a.px(1, 8, "K", "light")
    a.px(2, 8, "K", "light")
    for x, y in ((7, 4), (7, 5), (6, 5), (8, 5), (7, 6)):    # the anchor badge
        a.px(x, y, "B", "light" if y < 6 else "mid")
    a.px(6, 6, "B", "dark")
    a.px(8, 6, "B", "dark")
    a.px(5, 4, "M", "shine")
    a.px(4, 5, "M", "light")
    for x in (4, 11):
        a.px(x, 9, "B", "shine")


@painted("colossal_ironclad_chestplate")
def iron_chest(a):
    """Armoured coat: a navy plate coat, double-breasted with two rows of gold buttons, gold epaulettes and a red sash."""
    itemart.PAINTED["chestplate"](a)
    for y in range(4, 10):
        a.px(7, y, "M", "dark")
        a.px(8, y, "M", "dark")
    for y in (5, 7, 9):
        a.px(5, y, "B", "shine")
        a.px(10, y, "B", "light")
    for x in (1, 2, 3, 4, 10, 11, 12, 13):           # epaulettes with fringes
        a.px(x, 2, "B", "light" if x < 8 else "mid")
    for x in (1, 3, 11, 13):
        a.px(x, 3, "B", "dark")
    for x in range(3, 13):
        if a.m[10][x] is not None:
            a.px(x, 10, "Z", "mid" if x % 2 else "light")


@painted("colossal_ironclad_leggings")
def iron_legs(a):
    """Plated trousers: navy plate legs with a gold stripe down each outer seam and riveted knee plates."""
    itemart.PAINTED["leggings"](a)
    for y in range(3, 11):
        a.px(3, y, "B", "light")
        a.px(12, y, "B", "mid")
    for x in (4, 5, 10, 11):
        a.px(x, 7, "M", "light")
    _rivets(a, [(5, 8), (10, 8)], key="I")


@painted("colossal_ironclad_boots")
def iron_boots(a):
    """Deck boots: tall black lacquered boots with steel toe caps and gold-trimmed tops."""
    a.stamp([
        "..AAA...AAA.....",
        "..KKK...KKK.....",
        "..KKK...KKK.....",
        "..KKK...KKK.....",
        "..KKK...KKK.....",
        ".KKKK..KKKK.....",
        "KKKKKK.KKKKKK...",
        "XXXXXX.XXXXXX...",
    ], {"A": "A", "K": "K", "X": "X"}, 1, 5)
    a.shade_dir("K", 1.0, 0.6, cuts=(-0.6, 0.0, 0.6))
    for x, y in ((3, 6), (9, 6)):
        a.px(x, y, "K", "shine")
    for x, y in ((1, 11), (2, 11), (8, 11), (9, 11)):
        a.px(x, y, "I", "light" if x in (1, 8) else "mid")


# ================================================================== Canopy Stalker's Leathers (Canopy Temple-City)
@painted("colossal_canopy_stalker_helmet")
def stalker_helmet(a):
    """Feathered mask: a close leather hood with a dark eye band and a fan of red and green feathers over the crown."""
    a.stamp([
        "....MMMMMMM.....",
        "...MMMMMMMMM....",
        "..MMMMMMMMMMM...",
        "..KKKKKKKKKKK...",
        "..MMMMMMMMMMM...",
        "..MM.MMMMM.MM...",
        "...M.MMMMM.M....",
        "......MMM.......",
    ], {"M": "M", "K": "K"}, 1, 6)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.15, 0.7))
    a.px(5, 9, "Y", "mid")                         # the eyes glinting in the band
    a.px(9, 9, "Y", "mid")
    feathers = [((4, 5), (2, 1)), ((6, 5), (5, 0)), ((8, 5), (9, 0)), ((10, 5), (12, 1))]
    for k, ((x0, y0), (x1, y1)) in enumerate(feathers):
        a.seg("Z" if k % 2 == 0 else "A", x0 + 0.5, y0 + 0.5, x1 + 0.5, y1 + 0.5, 0.6)
    a.px(2, 1, "Z", "light")
    a.px(12, 1, "A", "light")
    a.px(5, 0, "A", "shine")
    a.px(9, 0, "Z", "shine")
    a.px(7, 7, "B", "light")                       # a gold bead holding the fan


@painted("colossal_canopy_stalker_chestplate")
def stalker_chest(a):
    """Leaf jerkin: green leather sewn with rows of overlapping leaves, a gold jaguar-claw clasp."""
    itemart.PAINTED["chestplate"](a)
    for y in range(3, 12):
        for x in range(16):
            if a.m[y][x] != "M":
                continue
            if (x + (y // 2) * 2) % 4 == 0 and y % 2 == 0:
                a.px(x, y, "a", "dark")
            elif (x + (y // 2) * 2) % 4 == 1 and y % 2 == 1:
                a.tone(x, y, "deep")
    for x in range(16):
        if a.m[10][x] == "A":
            a.px(x, 10, "N", "mid" if x % 2 else "dark")
    a.px(7, 4, "B", "light")
    a.px(8, 4, "B", "mid")
    a.px(7, 5, "Q", "light")


@painted("colossal_canopy_stalker_leggings")
def stalker_legs(a):
    """Vine leggings: green leather legs wound with living vines, a leaf here and there."""
    itemart.PAINTED["leggings"](a)
    for i in range(9):
        x, y = 3 + (i % 4), 3 + i
        if a.m[y][x] == "M":
            a.px(x, y, "a", "dark")
        x2 = 12 - (i % 4)
        if a.m[y][x2] == "M":
            a.px(x2, y, "a", "deep")
    for x in range(3, 13):
        if a.m[2][x] == "A":
            a.px(x, 2, "N", "mid" if x % 2 else "dark")
    a.px(5, 6, "a", "shine")
    a.px(10, 9, "a", "light")


@painted("colossal_canopy_stalker_boots")
def stalker_boots(a):
    """Climbing wraps: soft leather foot wraps bound with cord, bone claws at the toes for gripping bark."""
    itemart.PAINTED["boots"](a)
    for ox in (0, 7):
        for x, y in ((3, 7), (4, 8), (3, 9)):
            if a.m[y][ox + x] is not None:
                a.px(ox + x, y, "N", "light" if y % 2 else "mid")
    for x in range(16):
        if a.m[12][x] == "X":
            a.px(x, 12, "M", "dark")
    for x, y in ((0, 12), (1, 13), (13, 12), (14, 13)):
        a.px(x, y, "Q", "light")


# ================================================================== weapons
@painted("colossal_sluice_hook")
def sluice_hook(a):
    """Sluice-Hook Spear: an oak pole, a brass socket wound with chain, a long point and a barbed hook curling back
    from it, a glint of aether in the socket."""
    shaft(a, 10, grip=(1, 4))
    collar(a, 8, key="B")
    a.stamp([
        ".....s",
        "....ls",
        "...lsd",
        "..lsd.",
        ".lsd..",
    ], L("M", None), 10, 0)
    # the hook: from the socket out to the right, down and curling back up into a barb
    a.seg("M", 11.6, 5.4, 13.6, 7.0, 0.6)
    a.seg("M", 13.6, 7.0, 15.2, 6.4, 0.6)
    a.seg("M", 15.2, 6.4, 15.4, 4.2, 0.5)
    a.px(15, 3, "M", "shine")
    a.px(12, 5, "M", "light")
    a.px(14, 7, "M", "dark")
    a.disc("B", 10.4, 5.6, 1.2)
    a.px(10, 5, "B", "light")
    a.px(11, 6, "E", "light")
    for x, y in ((7, 8), (6, 9), (8, 7)):            # a few links of chain round the pole
        a.px(x, y, "I", "light" if (x + y) % 2 else "dark")


@painted("colossal_rivet_cannon")
def rivet_cannon(a):
    """Dam-Wright's Rivet Cannon: a stubby steel barrel with a flared brass muzzle glowing red-hot, a copper drum of
    rivets, a pressure gauge, an oak grip."""
    # oak grip down-left
    a.poly("H", [(2.0, 15.5), (1.0, 13.0), (3.8, 9.6), (6.6, 10.4), (4.4, 13.6), (3.6, 15.5)])
    a.shade_dir("H", 1.0, 0.4, cuts=(-0.5, 0.15, 0.7))
    # barrel along a shallow diagonal toward the top right
    a.seg("M", 4.0, 9.0, 12.0, 4.0, 1.5)
    a.disc("B", 13.0, 3.4, 2.4)
    a.shade_dir("M", 0.6, 1.0, cuts=(-0.5, 0.1, 0.6))
    a.disc("F", 13.4, 3.0, 1.1)
    a.px(13, 2, "F", "shine")
    a.px(12, 3, "Y", "mid")
    # the rivet drum under the barrel
    a.disc("C", 8.0, 9.2, 2.3)
    for x, y in ((7, 8), (9, 9), (7, 10)):
        a.px(x, y, "B", "shine")
    a.px(8, 9, "X", "mid")
    # gauge on top
    a.disc("Q", 6.0, 5.2, 1.1)
    a.px(6, 4, "Z", "mid")
    a.px(5, 6, "X", "mid")
    a.px(8, 5, "M", "shine")
    a.px(10, 4, "M", "light")
    a.px(3, 11, "X", "mid")                          # trigger
    a.px(4, 12, "X", "dark")


@painted("colossal_bog_flail")
def bog_flail(a):
    """Bog-Lantern Flail: a wrapped dark grip, a sagging chain and a caged iron lantern holding a sickly green marsh
    light."""
    shaft(a, 5, key="H", grip=(1, 4), butt="B")
    collar(a, 5, key="X")
    for i, (x, y) in enumerate(((7, 8), (8, 8), (9, 9), (10, 9), (11, 8))):
        a.px(x, y, "I", "light" if i % 2 == 0 else "dark")
    # the lantern: a ring on top, a cage around a glowing core
    a.box("X", 10, 2, 14, 7)
    a.box("S", 11, 3, 13, 6)
    for y in range(3, 7):
        a.px(12, y, "X", "mid")
    a.px(11, 3, "S", "shine")
    a.px(13, 5, "S", "dark")
    a.box("M", 10, 1, 14, 1)
    a.box("M", 10, 7, 14, 7)
    a.px(12, 0, "M", "light")
    a.px(10, 1, "M", "light")
    a.px(14, 7, "M", "dark")
    a.px(15, 4, "a", "light")                        # motes of marsh light
    a.px(9, 2, "a", "mid")


@painted("colossal_khopesh")
def khopesh(a):
    """Solar Khopesh: a dark grip, a short straight neck and a great crescent blade of gold, its inner edge bright, a
    lapis inlay and a sun glint."""
    shaft(a, 5, key="H", grip=(1, 4), butt="B")
    collar(a, 5, key="A")
    a.seg("M", 6.5, 8.5, 9.0, 6.0, 0.8)              # the neck
    # the crescent: an outer circle minus an inner one, the opening toward the bottom right
    cx, cy = 11.2, 6.0
    a.paint("M", lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= 4.6 ** 2
            and (x - (cx + 1.6)) ** 2 + (y - (cy + 1.6)) ** 2 > 3.6 ** 2 and y < 9.5 and x > 7.5)
    a.shade_dir("M", 0.8, 1.0, cuts=(-0.5, 0.1, 0.65))
    for y in range(16):
        for x in range(16):
            if a.m[y][x] == "M" and (x - (cx + 1.6)) ** 2 + (y - (cy + 1.6)) ** 2 <= 4.5 ** 2:
                a.tone(x, y, "shine")                # the sharpened inner edge
    a.px(9, 3, "A", "light")
    a.px(10, 2, "A", "mid")
    a.px(8, 5, "A", "dark")
    a.px(12, 1, "Y", "light")
    a.px(14, 2, "Y", "mid")


@painted("colossal_boarding_axe")
def boarding_axe(a):
    """Boarding Axe: a short oak haft with a gold-wire grip, a navy-blued steel head with a bright bearded edge and a
    back spike, gilded rivets."""
    shaft(a, 10, key="H", grip=(1, 4), butt="B")
    collar(a, 8, key="A")
    # head: a bearded blade up-left of the haft top, a spike behind
    a.poly("M", [(11.8, 3.8), (8.8, 6.8), (5.8, 7.8), (3.4, 7.2), (2.4, 4.8), (3.6, 2.4), (6.2, 0.6), (9.0, 0.4),
                 (10.4, 1.6)])
    a.shade_dir("M", 0.6, 1.0, cuts=(-0.5, 0.1, 0.65))
    for y in range(16):                                   # the bright cutting edge along the outer arc
        for x in range(16):
            if a.m[y][x] == "M" and (x - 9.5) ** 2 + (y - 6.0) ** 2 > 5.0 ** 2:
                a.tone(x, y, "shine")
    a.seg("X", 12.2, 4.4, 14.4, 6.6, 0.5)                 # the back spike
    a.px(14, 6, "X", "light")
    a.px(11, 3, "A", "shine")
    a.px(10, 5, "A", "light")


@painted("colossal_blowpipe")
def blowpipe(a):
    """Jade Blowpipe: a long thin tube of jade banded in gold, a carved frog on the mouthpiece and a feathered dart
    leaving the far end."""
    a.seg("M", 1.5, 14.5, 12.5, 3.5, 0.75)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.1, 0.6))
    for i in (2, 6, 10):                              # gold bands
        x, y = 1 + i, 14 - i
        a.px(x, y, "A", "light")
        a.px(x + 1, y, "A", "mid")
        a.px(x, y + 1, "A", "dark")
    a.disc("A", 1.8, 14.2, 1.3)                       # the mouthpiece
    a.px(1, 13, "A", "shine")
    a.px(4, 12, "S", "light")                         # the frog carving
    a.px(5, 12, "S", "mid")
    a.px(4, 11, "K", "mid")
    a.px(13, 2, "M", "light")
    # the dart in flight
    a.px(15, 0, "I", "light")
    a.px(14, 1, "Z", "mid")
    a.px(13, 0, "Z", "light")
    a.px(15, 1, "Y", "mid")


# ------------------------------------------------------------------ armour layers worn on the body
def _ramp(pal):
    t = tones(pal)
    return [t["shine"], t["light"], t["mid"], t["dark"], t["deep"], t["outline"]]


CLEAR = (0, 0, 0, 0)
STEAM = itemart.STEAM


class _Layer:
    """A 64x32 humanoid armour texture painted face by face. Faces of a cube at (u, v) of size (w, h, d):
    top, bottom, right side, front, left side, back."""

    def __init__(self, seed):
        self.cv = Canvas(64, 32)
        self.rng = random.Random(seed)

    @staticmethod
    def faces(u, v, w, h, d):
        return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
                "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + d + w + d, v + d, w, h)}

    def set(self, x, y, c):
        self.cv.set(x, y, c)

    def fill(self, rect, ramp, rows=None, noise=0.06):
        """Shade one face: lit top-left, dark bottom-right edge, a soft vertical gradient; rows limits the face to its
        bottom ``rows`` pixels (boots)."""
        x0, y0, w, h = rect
        top = y0 + h - rows if rows else y0
        for y in range(top, y0 + h):
            for x in range(x0, x0 + w):
                fy = (y - top) / max(1, y0 + h - 1 - top)
                k = 1.6 + fy * 1.2
                if x == x0 or y == top:
                    k -= 0.8
                if x == x0 + w - 1 or y == y0 + h - 1:
                    k += 1.0
                if self.rng.random() < noise:
                    k += self.rng.choice((-0.6, 0.6))
                self.set(x, y, ramp[max(0, min(4, int(round(k))))])

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.set(x, y, c)

    def clear(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, CLEAR)


# the body parts of the 64x32 humanoid layer: (u, v, w, h, d)
HEAD = (0, 0, 8, 8, 8)
BODY = (16, 16, 8, 12, 4)
ARM = (40, 16, 4, 12, 4)
LEG = (0, 16, 4, 12, 4)


def _paint_set(prefix, legs):
    from . import colossal_gear
    s = colossal_gear.SETS[prefix]
    base = _ramp(MATERIALS[s["mat"]])
    acc = _ramp(itemart.two_tone(*ACCENTS[s["accent"]]))
    brass, copper, iron, cream = (_ramp(STEAM[k]) for k in "BCXQ")
    leather, glass, flame, verd = (_ramp(STEAM[k]) for k in "NGFV")
    L_ = _Layer(prefix + str(legs))
    F = _Layer.faces
    fill = L_.fill

    def all_faces(part, ramp=base, rows=None, skip=()):
        f = F(*part)
        for kind, rect in f.items():
            if kind in skip:
                continue
            if rows and kind == "top":
                continue
            fill(rect, ramp, rows=rows if kind not in ("bottom",) else None)
        return f

    if legs:
        # -------- leggings: the legs and the waist (body cube of the leggings texture, only its lower part matters)
        if prefix == "sun_priest":
            lf = all_faces(LEG, _ramp(STEAM["Q"]))
            wf = all_faces(BODY, _ramp(STEAM["Q"]))
        else:
            lf = all_faces(LEG)
            wf = all_faces(BODY)
        for kind in ("front", "back", "left", "right"):
            x0, y0, w, h = wf[kind]
            L_.clear(x0, y0, x0 + w - 1, y0 + 4)                       # nothing above the belt line
            L_.hline(x0, x0 + w - 1, y0 + 5, acc[2] if prefix not in ("bog_pilgrim", "canopy_stalker") else leather[2])
            L_.hline(x0, x0 + w - 1, y0 + 6, acc[3] if prefix not in ("bog_pilgrim", "canopy_stalker") else leather[3])
        L_.clear(*[c for c in (wf["top"][0], wf["top"][1], wf["top"][0] + wf["top"][2] - 1, wf["top"][1] + 3)])
        fx, fy, fw, fh = wf["front"]
        lx, ly, lw, lh = lf["front"]
        if prefix == "lockkeeper":
            L_.set(fx + 3, fy + 5, brass[0])
            L_.set(fx + 4, fy + 5, brass[1])
            for kind in ("front", "left", "right", "back"):
                x0, y0, w, h = lf[kind]
                L_.hline(x0, x0 + w - 1, y0 + 5, brass[1])            # knee plate rims
                L_.hline(x0, x0 + w - 1, y0 + 7, brass[3])
                L_.set(x0 + 1, y0 + 6, brass[0])
                L_.set(x0 + w - 2, y0 + 10, verd[1])
        elif prefix == "turbine_engineer":
            for kind in ("left", "right"):
                x0, y0, w, h = lf[kind]
                L_.vline(x0 + 1, y0 + 1, y0 + h - 2, _ramp(STEAM["I"])[1])   # piston rods
                L_.vline(x0 + 2, y0 + 1, y0 + h - 2, _ramp(STEAM["I"])[3])
                L_.set(x0 + 1, y0 + 6, copper[1])
                L_.set(x0 + 2, y0 + 6, copper[2])
            L_.hline(lx, lx + lw - 1, ly + 6, copper[2])
        elif prefix == "bog_pilgrim":
            for kind in ("front", "back", "left", "right"):
                x0, y0, w, h = lf[kind]
                for y in range(y0, y0 + h):
                    for x in range(x0, x0 + w):
                        if (x + y) % 4 == 0:
                            L_.set(x, y, leather[1 if (x + y) % 8 else 2])
        elif prefix == "sun_priest":
            for kind in ("front", "back", "left", "right"):
                x0, y0, w, h = lf[kind]
                for x in range(x0, x0 + w, 2):
                    L_.vline(x, y0, y0 + 7, cream[3])                   # pleats
                L_.clear(x0, y0 + 8, x0 + w - 1, y0 + h - 1)           # bare shins under the kilt
            for kind in ("front", "back"):
                x0, y0, w, h = wf[kind]
                L_.hline(x0, x0 + w - 1, y0 + 5, base[1])
                L_.hline(x0, x0 + w - 1, y0 + 6, base[3])
            for y in range(fy + 7, fy + fh):                            # the striped apron
                L_.set(fx + 3, y, acc[1] if y % 2 else base[1])
                L_.set(fx + 4, y, acc[2] if y % 2 else base[2])
        elif prefix == "ironclad":
            for kind in ("left", "right"):
                x0, y0, w, h = lf[kind]
                L_.vline(x0 + w // 2, y0, y0 + h - 1, brass[1])        # the gold stripe
            for kind in ("front",):
                x0, y0, w, h = lf[kind]
                L_.hline(x0, x0 + w - 1, y0 + 5, base[1])
                L_.set(x0 + 1, y0 + 6, _ramp(STEAM["I"])[0])
            L_.set(fx + 3, fy + 5, brass[0])
            L_.set(fx + 4, fy + 5, brass[1])
        elif prefix == "canopy_stalker":
            vine = acc
            for kind in ("front", "back", "left", "right"):
                x0, y0, w, h = lf[kind]
                for i in range(h):
                    x = x0 + (i // 2) % w
                    L_.set(x, y0 + i, base[4] if i % 3 else vine[3])
                L_.set(x0 + 1, y0 + 4, vine[2])
        return L_.cv

    # -------- helmet, chestplate, boots
    hf = all_faces(HEAD)
    bf = all_faces(BODY)
    af = all_faces(ARM)
    gf = all_faces(LEG, rows=5)          # boots: the bottom 5 rows of the leg (the top stays clear)
    hx, hy, hw, hh = hf["front"]
    bx, by, bw, bh = bf["front"]
    ax_, ay_, aw, ah = af["front"]

    def helm_rim(c1, c2):
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = hf[kind]
            L_.hline(x0, x0 + w - 1, y0 + h - 1, c2)
            L_.hline(x0, x0 + w - 1, y0 + h - 2, c1)

    def boot_cuffs(c1, c2):
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            L_.hline(x0, x0 + w - 1, y0 + h - 5, c1)
            L_.hline(x0, x0 + w - 1, y0 + h - 1, c2)

    if prefix == "lockkeeper":
        # a domed diving helm: a big round porthole on the front, side ports, bolts round the collar
        for (cx, cy, r) in ((hx + 3.5, hy + 3.6, 2.9),):
            for y in range(hy, hy + hh):
                for x in range(hx, hx + hw):
                    d = math.hypot(x + 0.5 - (cx + 0.5), y + 0.5 - (cy + 0.5))
                    if d <= r - 1.0:
                        L_.set(x, y, glass[1] if (x - hx) + (y - hy) < 6 else glass[2])
                    elif d <= r:
                        L_.set(x, y, brass[1] if y < cy else brass[3])
        L_.set(hx + 2, hy + 2, glass[0])
        for kind in ("left", "right"):
            x0, y0, w, h = hf[kind]
            for y in range(y0 + 3, y0 + 5):
                for x in range(x0 + 3, x0 + 5):
                    L_.set(x, y, glass[2])
            for x, y in ((x0 + 2, y0 + 3), (x0 + 5, y0 + 4), (x0 + 3, y0 + 2), (x0 + 4, y0 + 5)):
                L_.set(x, y, brass[1])
        helm_rim(iron[1], iron[3])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = hf[kind]
            for x in range(x0 + 1, x0 + w, 3):
                L_.set(x, y0 + h - 2, brass[0])
        # cuirass: a central seam, rivet rows, the depth gauge, verdigris
        L_.vline(bx + 3, by + 1, by + bh - 2, base[1])
        L_.vline(bx + 4, by + 1, by + bh - 2, base[3])
        for y in range(by + 2, by + bh - 1, 3):
            L_.set(bx + 1, y, brass[0])
            L_.set(bx + bw - 2, y, brass[0])
        for x, y, c in ((bx + 3, by + 3, iron[2]), (bx + 4, by + 3, iron[2]), (bx + 3, by + 4, acc[1]),
                        (bx + 4, by + 4, acc[2]), (bx + 3, by + 5, iron[3]), (bx + 4, by + 5, iron[3])):
            L_.set(x, y, c)
        L_.hline(bx, bx + bw - 1, by + bh - 3, iron[2])
        L_.hline(bx, bx + bw - 1, by + bh - 2, iron[3])
        for kind in ("back",):
            x0, y0, w, h = bf[kind]
            L_.hline(x0 + 1, x0 + w - 2, y0 + 2, iron[1])            # the air-hose manifold on the back
            L_.hline(x0 + 1, x0 + w - 2, y0 + 3, iron[3])
            L_.set(x0 + 1, y0 + 2, brass[0])
            L_.set(x0 + w - 2, y0 + 2, brass[0])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = af[kind]
            L_.hline(x0, x0 + w - 1, y0 + 3, brass[1])               # shoulder plate rims
            L_.hline(x0, x0 + w - 1, y0 + h - 3, iron[2])
        for x, y in ((bx + 6, by + 8), (bx + 1, by + 6)):
            L_.set(x, y, verd[1])
        boot_cuffs(brass[1], iron[4])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            L_.hline(x0, x0 + w - 1, y0 + h - 2, iron[2])            # the lead soles
    elif prefix == "turbine_engineer":
        # a leather cap with goggles on the brow
        L_.hline(hx, hx + hw - 1, hy + 3, leather[3])
        for gx in (hx + 1, hx + 5):
            L_.set(gx, hy + 3, brass[1])
            L_.set(gx + 1, hy + 3, brass[2])
            L_.set(gx, hy + 4, flame[1])
            L_.set(gx + 1, hy + 4, flame[2])
            L_.set(gx, hy + 2, brass[0])
            L_.set(gx + 1, hy + 2, brass[1])
        L_.clear(hx, hy + 5, hx + hw - 1, hy + hh - 1)                # the face stays bare
        for kind in ("left", "right"):
            x0, y0, w, h = hf[kind]
            L_.hline(x0, x0 + w - 1, y0 + 3, leather[2])
            L_.clear(x0, y0 + 6, x0 + w - 1, y0 + h - 1)
        x0, y0, w, h = hf["back"]
        L_.hline(x0, x0 + w - 1, y0 + 3, leather[2])
        # the rig: crossed straps over the steel coat, a gauge, a boiler on the back with copper pipes
        for i in range(bh - 3):
            L_.set(bx + min(bw - 1, i * bw // (bh - 3)), by + i, leather[1])
            L_.set(bx + bw - 1 - min(bw - 1, i * bw // (bh - 3)), by + i, leather[2])
        for x, y, c in ((bx + 3, by + 4, copper[1]), (bx + 4, by + 4, copper[2]), (bx + 3, by + 5, cream[1]),
                        (bx + 4, by + 5, _ramp(STEAM["Z"])[2])):
            L_.set(x, y, c)
        x0, y0, w, h = bf["back"]
        for y in range(y0 + 1, y0 + h - 2):
            for x in range(x0 + 1, x0 + w - 1):
                L_.set(x, y, copper[1 if x < x0 + 3 else 2 if x < x0 + 6 else 3])
        L_.hline(x0 + 1, x0 + w - 2, y0 + 3, brass[1])
        L_.hline(x0 + 1, x0 + w - 2, y0 + 8, brass[2])
        L_.set(x0 + 3, y0 + 5, flame[1])
        L_.set(x0 + 4, y0 + 5, flame[2])
        for kind in ("left", "right"):
            x0, y0, w, h = bf[kind]
            L_.vline(x0 + 1, y0, y0 + 5, copper[1])
        L_.hline(bx, bx + bw - 1, by + bh - 2, leather[3])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = af[kind]
            L_.hline(x0, x0 + w - 1, y0 + h - 4, leather[2])         # gauntlet cuffs
            L_.hline(x0, x0 + w - 1, y0 + h - 3, leather[3])
        x0, y0, w, h = af["front"]
        L_.set(x0 + 1, y0 + h - 6, cream[1])                          # a wrist gauge
        L_.set(x0 + 2, y0 + h - 6, copper[2])
        boot_cuffs(copper[1], iron[3])
        for kind in ("front", "left", "right"):
            x0, y0, w, h = gf[kind]
            for x in range(x0, x0 + w, 2):
                L_.set(x, y0 + h - 1, brass[1])                       # hobnails
    elif prefix == "bog_pilgrim":
        # the wide reed hat: the head's top and a band low on the sides; the face under a dark veil
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = hf[kind]
            for y in range(y0, y0 + 3):
                for x in range(x0, x0 + w):
                    L_.set(x, y, base[1 + ((x + y) % 3 == 0)])
            L_.hline(x0, x0 + w - 1, y0 + 3, base[3])
            L_.clear(x0, y0 + 4, x0 + w - 1, y0 + h - 1)
        x0, y0, w, h = hf["front"]
        for x in range(x0, x0 + w):
            for y in range(y0 + 4, y0 + 6):
                if (x + y) % 2 == 0:
                    L_.set(x, y, _ramp(STEAM["K"])[2])
        x0, y0, w, h = hf["top"]
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                ring = max(abs(x - x0 - 3.5), abs(y - y0 - 3.5))
                L_.set(x, y, base[1 if int(ring) % 2 else 2])
        # the waxed coat: hood bunched on the shoulders, twine belt, lantern charm, reed stripes
        for kind in ("front", "back", "left", "right"):
            x0, y0, w, h = bf[kind]
            L_.hline(x0, x0 + w - 1, y0, base[1])
            L_.hline(x0, x0 + w - 1, y0 + 1, base[2])
            L_.hline(x0, x0 + w - 1, y0 + 7, leather[1])
            for x in range(x0 + 1, x0 + w, 3):
                L_.vline(x, y0 + 8, y0 + h - 1, base[3])
        L_.set(bx + 2, by + 8, iron[2])
        L_.set(bx + 2, by + 9, _ramp(STEAM["S"])[1])
        L_.set(bx + 2, by + 10, iron[3])
        L_.vline(bx + 4, by + 2, by + 6, base[3])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = af[kind]
            for y in range(y0 + 6, y0 + h, 2):
                L_.hline(x0, x0 + w - 1, y, leather[2])               # wrapped sleeves
        boot_cuffs(leather[1], _ramp(STEAM["T"])[3])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            L_.hline(x0, x0 + w - 1, y0 + h - 2, _ramp(STEAM["T"])[1])  # the wooden stilt soles
            L_.set(x0 + 1, y0 + h - 3, leather[1])
    elif prefix == "sun_priest":
        # striped nemes headcloth, a gold brow band, the uraeus; the face open
        for kind in ("front", "left", "right", "back", "top"):
            x0, y0, w, h = hf[kind]
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    if (y - y0) % 2 == 1:
                        L_.set(x, y, acc[1] if kind != "back" else acc[2])
        L_.clear(hx + 1, hy + 3, hx + hw - 2, hy + hh - 1)
        L_.hline(hx, hx + hw - 1, hy + 2, base[0])
        L_.set(hx + 3, hy + 2, _ramp(STEAM["Z"])[1])
        L_.set(hx + 4, hy + 2, _ramp(STEAM["Z"])[2])
        for kind in ("left", "right"):
            x0, y0, w, h = hf[kind]
            L_.clear(x0, y0 + 3, x0 + 2, y0 + h - 1)
        # the pectoral: banded collar over linen, the sun disc
        for kind in ("front", "back", "left", "right"):
            x0, y0, w, h = bf[kind]
            for y in range(y0 + 4, y0 + h):
                for x in range(x0, x0 + w):
                    L_.set(x, y, cream[1] if x < x0 + w - 1 else cream[2])
        for i, c in enumerate((base[1], acc[1], base[2], acc[2])):
            L_.hline(bx, bx + bw - 1, by + i, c)
            L_.hline(bf["back"][0], bf["back"][0] + bw - 1, by + i, c if i < 2 else cream[1])
        L_.set(bx + 3, by + 4, flame[0])
        L_.set(bx + 4, by + 4, flame[1])
        L_.set(bx + 3, by + 5, flame[1])
        L_.set(bx + 4, by + 5, flame[2])
        L_.hline(bx, bx + bw - 1, by + bh - 4, base[1])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = af[kind]
            L_.clear(x0, y0 + 4, x0 + w - 1, y0 + h - 1)                  # bare arms below the shoulder
            L_.hline(x0, x0 + w - 1, y0 + 6, base[1])                     # gold armlets
            L_.hline(x0, x0 + w - 1, y0 + 7, acc[2])
            L_.hline(x0, x0 + w - 1, y0 + h - 3, base[1])
            L_.hline(x0, x0 + w - 1, y0 + h - 2, base[3])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            L_.clear(x0, y0 + h - 5, x0 + w - 1, y0 + h - 3)
            L_.set(x0 + 1, y0 + h - 4, base[1])                          # the sandal straps
            L_.set(x0 + 2, y0 + h - 3, base[2])
            L_.hline(x0, x0 + w - 1, y0 + h - 5, acc[1])
    elif prefix == "ironclad":
        # peaked helm: navy dome, gold braid, a black peak at the front, anchor badge
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = hf[kind]
            L_.hline(x0, x0 + w - 1, y0 + 3, brass[1])
            L_.hline(x0, x0 + w - 1, y0 + 4, brass[3])
            L_.clear(x0, y0 + 6, x0 + w - 1, y0 + h - 1)
        L_.clear(hx + 1, hy + 5, hx + hw - 2, hy + hh - 1)
        L_.hline(hx, hx + hw - 1, hy + 5, _ramp(STEAM["K"])[1])
        L_.set(hx + 3, hy + 1, brass[0])
        L_.set(hx + 4, hy + 1, brass[1])
        L_.set(hx + 3, hy + 2, brass[2])
        for kind in ("left", "right"):
            x0, y0, w, h = hf[kind]
            for y in range(y0 + 5, y0 + h - 1):
                L_.set(x0 + w - 2, y, base[2])                            # cheek plates
                L_.set(x0 + w - 1, y, base[3])
        # double-breasted plate coat: two rows of gold buttons, epaulettes, a red sash
        L_.vline(bx + 3, by, by + bh - 1, base[3])
        L_.vline(bx + 4, by, by + bh - 1, base[3])
        for y in range(by + 2, by + bh - 3, 2):
            L_.set(bx + 1, y, brass[0])
            L_.set(bx + 6, y, brass[1])
        L_.hline(bx, bx + bw - 1, by + bh - 4, _ramp(STEAM["Z"])[1])
        L_.hline(bx, bx + bw - 1, by + bh - 3, _ramp(STEAM["Z"])[2])
        L_.hline(bx, bx + 2, by, brass[1])
        L_.hline(bx + 5, bx + 7, by, brass[1])
        for kind in ("front", "left", "right", "back", "top"):
            x0, y0, w, h = af[kind]
            if kind == "top":
                for y in range(y0, y0 + h):
                    L_.hline(x0, x0 + w - 1, y, brass[1])
                continue
            L_.hline(x0, x0 + w - 1, y0, brass[0])                      # epaulette and fringe
            for x in range(x0, x0 + w, 2):
                L_.set(x, y0 + 1, brass[2])
            L_.hline(x0, x0 + w - 1, y0 + h - 3, brass[1])              # gold cuff braid
        boot_cuffs(brass[1], iron[4])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            for y in range(y0 + h - 4, y0 + h - 1):
                for x in range(x0, x0 + w):
                    L_.set(x, y, _ramp(STEAM["K"])[1 if x == x0 else 2])
        x0, y0, w, h = gf["front"]
        L_.hline(x0, x0 + w - 1, y0 + h - 2, _ramp(STEAM["I"])[1])       # steel toe caps
    elif prefix == "canopy_stalker":
        # a leather hood with an eye band and a crest of feathers
        L_.hline(hx, hx + hw - 1, hy + 4, _ramp(STEAM["K"])[2])
        L_.set(hx + 2, hy + 4, _ramp(STEAM["Y"])[2])
        L_.set(hx + 5, hy + 4, _ramp(STEAM["Y"])[2])
        L_.clear(hx + 2, hy + 6, hx + 5, hy + hh - 1)
        ruby = _ramp(STEAM["Z"])
        for kind in ("top", "back"):
            x0, y0, w, h = hf[kind]
            for x in range(x0 + 2, x0 + w - 2):
                for y in range(y0, y0 + (h if kind == "top" else 3)):
                    L_.set(x, y, (ruby if x % 2 else acc)[1 if y % 2 else 2])
        # leaf jerkin: overlapping leaf scales, a claw clasp
        for kind in ("front", "back", "left", "right"):
            x0, y0, w, h = bf[kind]
            for y in range(y0 + 1, y0 + h - 2):
                for x in range(x0, x0 + w):
                    if (x + (y // 2) * 2) % 4 == 0 and y % 2 == 0:
                        L_.set(x, y, acc[3])
                    elif (x + (y // 2) * 2) % 4 == 1 and y % 2 == 1:
                        L_.set(x, y, base[4])
            L_.hline(x0, x0 + w - 1, y0 + h - 2, leather[2])
        L_.set(bx + 3, by + 1, brass[1])
        L_.set(bx + 4, by + 1, cream[1])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = af[kind]
            for y in range(y0 + 5, y0 + h - 1, 3):
                L_.hline(x0, x0 + w - 1, y, leather[1])                 # bracer cords
        boot_cuffs(leather[1], base[4])
        for kind in ("front", "left", "right", "back"):
            x0, y0, w, h = gf[kind]
            L_.set(x0 + 1, y0 + h - 3, leather[1])
            L_.set(x0 + 2, y0 + h - 4, leather[1])
        x0, y0, w, h = gf["front"]
        for x in range(x0, x0 + w, 2):
            L_.set(x, y0 + h - 1, cream[1])                                # bone claws at the toes
    return L_.cv


def armor_layer(prefix, legs=False):
    return _paint_set(prefix, legs)


# ------------------------------------------------------------------ gen_textures
def textures():
    from . import colossal_gear as g
    out = {}
    for prefix, s in g.SETS.items():
        for piece in g.PIECES:
            out[f"item/{prefix}_{piece}"] = render(f"colossal_{prefix}_{piece}", s["mat"], "dark", s["accent"])
        out[f"entity/equipment/humanoid/{prefix}"] = armor_layer(prefix)
        out[f"entity/equipment/humanoid_leggings/{prefix}"] = armor_layer(prefix, legs=True)
    for wid, w in g.WEAPONS.items():
        mat, handle, accent = w["sprite"]
        out[f"item/{wid}"] = render(w["held"], mat, handle, accent)
    return out


# ------------------------------------------------------------------ 3D in-hand archetypes (held3d)
def _held_archetypes():
    from .held3d import _grip, _shaft, box

    def sluice_hook():
        """An oak pole, a brass socket with a wound chain, a long steel point and a barbed hook curling back."""
        out = _shaft(-6, 21, 1.5) + _grip(2, 9, 2.0)
        out += [box(6.5, 20, 6.5, 9.5, 22.5, 9.5, "brass"), box(6.8, 22.5, 6.8, 9.2, 23.2, 9.2, "brass_dark"),
                box(7.4, 21, 6.3, 8.6, 21.8, 9.7, "glow"),
                box(7.1, 23.2, 7.4, 8.9, 28, 8.6, "mid"), box(7.5, 28, 7.6, 8.5, 31, 8.4, "light"),
                box(8.9, 23.2, 7.5, 12.2, 24.6, 8.5, "mid"),                         # the hook arm
                box(12.2, 23.2, 7.55, 13.6, 28.0, 8.45, "mid"), box(11.0, 27.0, 7.6, 12.2, 28.4, 8.4, "light"),
                box(12.4, 28.0, 7.6, 13.4, 29.2, 8.4, "light")]
        for k, y in enumerate((15, 16.6, 18.2)):                                     # the chain
            out.append(box(6.6, y, 7.6, 9.4, y + 1.2, 8.4, "steel") if k % 2 == 0
                       else box(7.6, y, 6.6, 8.4, y + 1.2, 9.4, "steel"))
        return out

    def rivet_cannon():
        """An oak pistol grip, a steel barrel with a flared brass muzzle glowing hot, a copper rivet drum, a gauge."""
        out = [box(7, -2, 7, 9, 7, 9, "handle"), box(6.8, -3, 6.6, 9.2, -1.5, 9.4, "handle_dark"),
               box(7.2, 6, 9, 8.8, 8, 10, "iron_dark")]                              # the trigger guard
        out += [box(6.4, 7, 6.4, 9.6, 21, 9.6, "mid"), box(6.2, 9, 6.2, 9.8, 10, 9.8, "dark"),
                box(5.4, 21, 5.4, 10.6, 24, 10.6, "brass"), box(5.9, 24, 5.9, 10.1, 24.6, 10.1, "glow"),
                box(5.6, 18, 5.6, 10.4, 19, 10.4, "brass_dark"),
                box(9.6, 11, 6.2, 12.4, 16, 9.8, "accent_dark"),                    # the copper drum
                box(12.4, 12, 6.8, 12.8, 15, 9.2, "brass"),
                box(7.0, 13, 9.6, 9.0, 15, 10.4, "cream"), box(7.8, 14, 10.4, 8.2, 14.6, 10.6, "ink")]
        return out

    def bog_flail():
        """A wrapped grip, an iron collar, a short sagging chain and a caged iron lantern with a green light."""
        out = [box(7, -1, 7, 9, 9, 9, "wrap"), box(6.6, -2.5, 6.6, 9.4, -1, 9.4, "iron_dark"),
               box(6.6, 9, 6.6, 9.4, 11, 9.4, "iron_dark"), box(7, 11, 7.6, 9, 13, 8.4, "steel")]
        for k, (x, y) in enumerate(((8, 12.8), (8.6, 14.8), (9.4, 16.8))):
            out.append(box(x - 1, y, 7.6, x + 1, y + 2.4, 8.4, "steel") if k % 2 == 0
                       else box(x - 0.4, y, 7, x + 0.4, y + 2.4, 9, "steel"))
        cx, cz = 10.6, 8.0
        out += [box(cx - 1, 19, cz - 1, cx + 1, 20, cz + 1, "dark"),                # the hanging ring
                box(cx - 2.6, 20, cz - 2.6, cx + 2.6, 21, cz + 2.6, "dark"),        # the lantern cap
                box(cx - 2.2, 27, cz - 2.2, cx + 2.2, 28, cz + 2.2, "dark"),
                box(cx - 1.6, 21, cz - 1.6, cx + 1.6, 27, cz + 1.6, "glow")]         # the marsh light
        for dx, dz in ((-2.2, -2.2), (1.6, -2.2), (-2.2, 1.6), (1.6, 1.6)):          # the cage bars
            out.append(box(cx + dx, 21, cz + dz, cx + dx + 0.6, 27, cz + dz + 0.6, "iron_dark"))
        out.append(box(cx - 0.8, 28, cz - 0.8, cx + 0.8, 29.2, cz + 0.8, "mid"))
        return out

    def khopesh():
        """A dark grip and pommel, a short neck, then a great gold crescent opening forward, a bright inner edge."""
        out = _grip(1, 8, 2.2) + [box(6.6, -1, 6.6, 9.4, 1, 9.4, "accent"), box(6.4, 8, 6.4, 9.6, 9.2, 9.6, "accent")]
        out += [box(7.2, 9.2, 7.4, 8.8, 15, 8.6, "mid")]                             # the neck
        cx, cy, r0, r1 = 10.0, 21.0, 4.0, 6.4
        for k in range(14):                                                          # the crescent, segment by segment
            a0 = math.radians(200 - k * 15)
            x = cx + math.cos(a0) * (r0 + r1) / 2
            y = cy + math.sin(a0) * (r0 + r1) / 2
            key = "light" if k in (0, 1, 12, 13) else "mid"
            out.append(box(x - 1.3, y - 1.3, 7.4, x + 1.3, y + 1.3, 8.6, key))
            ix = cx + math.cos(a0) * (r0 - 0.4)
            iy = cy + math.sin(a0) * (r0 - 0.4)
            if 2 <= k <= 11:
                out.append(box(ix - 0.5, iy - 0.5, 7.6, ix + 0.5, iy + 0.5, 8.4, "glow"))
        out.append(box(6.8, 18, 7.2, 8.0, 20, 8.8, "accent"))                       # a lapis inlay
        return out

    def boarding_axe():
        """A short oak haft with a gold-wired grip, a blued steel bearded head with a bright edge, a back spike."""
        out = _shaft(-4, 22, 1.6) + _grip(1, 8, 2.2) + [box(6.8, 4, 6.8, 9.2, 4.6, 9.2, "accent")]
        out += [box(6.6, 17, 6.6, 9.4, 18, 9.4, "accent"),
                box(5.6, 18, 7.3, 8.6, 23, 8.7, "mid"),                              # the head's body
                box(2.6, 16, 7.4, 5.6, 24, 8.6, "light"), box(1.4, 15, 7.5, 2.6, 24.5, 8.5, "steel"),  # the bearded blade
                box(2.6, 13.5, 7.5, 4.2, 16, 8.5, "light"), box(1.8, 13.2, 7.55, 2.6, 15, 8.45, "steel"),
                box(8.6, 19.5, 7.5, 12.6, 21, 8.5, "dark"), box(12.6, 19.8, 7.6, 14, 20.7, 8.4, "light"),
                box(6.6, 22, 6.6, 9.4, 23, 9.4, "accent_dark"), box(4.0, 20, 7.2, 5.0, 21, 8.8, "accent")]
        return out

    def blowpipe():
        """A long thin jade tube banded with gold, a gold mouthpiece with a carved frog, a dart at the far end."""
        out = [box(7.3, -6, 7.3, 8.7, 30, 8.7, "mid"), box(7.0, -7, 7.0, 9.0, -5, 9.0, "accent"),
               box(7.6, 30, 7.6, 8.4, 31, 8.4, "ink")]
        for y in (2, 12, 22, 28):
            out.append(box(7.05, y, 7.05, 8.95, y + 1, 8.95, "accent"))
        out += [box(8.7, -3, 7.4, 9.6, -1.6, 8.6, "accent_dark"), box(9.0, -2.0, 7.6, 9.8, -1.6, 8.4, "glow"),
                box(7.0, 6, 7.0, 9.0, 9, 9.0, "accent_dark")]                       # the grip wrap
        return out

    return {"colossal_sluice_hook": sluice_hook, "colossal_rivet_cannon": rivet_cannon,
            "colossal_bog_flail": bog_flail, "colossal_khopesh": khopesh,
            "colossal_boarding_axe": boarding_axe, "colossal_blowpipe": blowpipe}


def register_held(archetypes, held):
    """Called at the end of held3d.py: adds the archetypes and the weapons that use them."""
    from . import colossal_gear
    archetypes.update(_held_archetypes())
    held.update(colossal_gear.held())
