"""Art of the relic gear (wf/relics.py): painted item sprites (itemart primitives, one light from the top-left, auto
outline), the four armour layers worn on the body (64x32 humanoid UVs, painted with texkit hue-shifted ramps) and the
3D in-hand archetypes of the big weapons (registered into held3d.ARCHETYPES / HELD when held3d is imported).

Keys: M material, H handle, A accent, plus itemart.STEAM (B brass, Q cream/bone, F flame, G ice, X dark iron,
N tan leather, L oxblood, Y sparkle, P void glow, E aether, Z ruby...).
"""
import math
import random

from . import itemart
from .itemart import diag, painted
from .itemart_shapes import L, collar, shaft
from .png import Canvas
from .sprites import ACCENTS, HANDLES, MATERIALS

# the relic materials (light, mid, dark, outline), added to the shared palette so held3d can use them too
RELIC_MATERIALS = {
    "glacier": ((228, 242, 252), (164, 194, 218), (94, 122, 156), (26, 38, 62)),
    "magma": ((128, 114, 118), (78, 66, 70), (46, 38, 42), (16, 10, 12)),
    "tide": ((196, 238, 226), (92, 176, 168), (38, 104, 112), (10, 40, 46)),
    "wind": ((252, 246, 230), (226, 214, 188), (172, 152, 122), (70, 56, 40)),
    "stone": ((238, 234, 220), (194, 188, 170), (130, 124, 112), (48, 44, 40)),
    "halo": ((255, 252, 236), (242, 228, 168), (198, 170, 96), (82, 62, 26)),
    "wood": ((178, 130, 82), (134, 92, 54), (90, 60, 34), (36, 22, 12)),
}
for _k, _v in RELIC_MATERIALS.items():
    MATERIALS.setdefault(_k, _v)


def render(shape, mat, handle="dark", accent="gold"):
    return itemart.sprite(shape, {"M": MATERIALS[mat], "H": itemart.two_tone(*HANDLES[handle]),
                                  "A": itemart.two_tone(*ACCENTS[accent])})


# ------------------------------------------------------------------ armour: Jarl's Frostplate (glacier)
def _fur(a, cells, key="Q"):
    """Fur trim: alternating light/mid tufts."""
    for i, (x, y) in enumerate(cells):
        a.px(x, y, key, "shine" if (x + y) % 3 == 0 else "light" if i % 2 else "mid")


@painted("relic_frostplate_helmet")
def frost_helmet(a):
    """Horned helm: a steel dome with an ice band, a nasal guard, two bone horns curling up from the sides."""
    a.stamp([
        ".....MMMMMM.....",
        "....MMMMMMMM....",
        "...MMMMMMMMMM...",
        "...AAAAAAAAAA...",
        "...MMMKMMKMMM...",
        "...MMK.MM.KMM...",
        "...MM..MM..MM...",
        "....M..MM..M....",
    ], {"M": "M", "A": "A", "K": "X"}, 0, 5)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.2, 0.75))
    # horns: bone, sweeping out and up from the temples
    a.stamp([
        "Q..............Q",
        "QQ............QQ",
        ".QQ..........QQ.",
        ".QQ..........QQ.",
        "..QQ........QQ..",
        "...QQ......QQ...",
    ], {"Q": "Q"}, 0, 0)
    a.shade_dir("Q", 1.0, 0.8, cuts=(-0.4, 0.2, 0.7))
    a.px(3, 0, "Q", "shine")
    a.px(12, 0, "Q", "light")
    a.px(6, 6, "M", "shine")
    a.px(7, 5, "M", "shine")
    for x, y in ((4, 10), (11, 10)):
        a.px(x, y, "B", "shine")
    a.px(7, 8, "A", "shine")


@painted("relic_frostplate_chestplate")
def frost_chest(a):
    """Frostplate: a steel cuirass with a white fur mantle over the shoulders and an ice gem at the heart."""
    itemart.PAINTED["chestplate"](a)
    _fur(a, [(1, 3), (2, 2), (3, 2), (4, 2), (5, 3), (9, 3), (10, 2), (11, 2), (12, 2), (13, 3),
             (1, 4), (2, 3), (3, 3), (4, 3), (10, 3), (11, 3), (12, 3), (13, 4), (6, 4), (8, 4)])
    a.px(7, 4, "Q", "light")
    a.sphere("G", 7.5, 7.5, 1.4)
    a.px(7, 7, "G", "shine")


@painted("relic_frostplate_leggings")
def frost_legs(a):
    """Frost greaves: plated legs, ice knee cops, a fur band at the shins."""
    itemart.PAINTED["leggings"](a)
    for x in (4, 5, 10, 11):
        a.px(x, 7, "G", "light" if x in (4, 10) else "mid")
    _fur(a, [(3, 10), (4, 10), (5, 10), (6, 10), (9, 10), (10, 10), (11, 10), (12, 10)])


@painted("relic_frostplate_boots")
def frost_boots(a):
    """Frost sabatons: steel boots with thick fur cuffs and iron soles."""
    itemart.PAINTED["boots"](a)
    _fur(a, [(3, 5), (4, 5), (5, 5), (8, 5), (9, 5), (10, 5), (2, 6), (6, 6), (7, 6), (11, 6)])
    a.px(4, 9, "G", "light")
    a.px(9, 9, "G", "light")


# ------------------------------------------------------------------ armour: Caldera Magmaguard (caldera)
def _seams(a, cells):
    """Molten cracks: glowing flame pixels, brightest in the middle of each crack."""
    for i, (x, y) in enumerate(cells):
        if a.m[y][x] is not None:
            a.px(x, y, "F", "shine" if i % 3 == 1 else "light" if i % 3 == 0 else "mid")


@painted("relic_magmaguard_helmet")
def magma_helmet(a):
    """Magmaguard helm: a squat basalt great helm with a glowing eye slit, magma veins and brass rivets."""
    a.stamp([
        "....MMMMMMMM....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMFFFFFFFFMM..",
        "..MMMMMMMMMMMM..",
        "..MMMM.MM.MMMM..",
        "..MMMM.MM.MMMM..",
        "...MMMMMMMMMM...",
    ], {"M": "M", "F": "F"}, 0, 4)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.15, 0.7))
    for x in range(4, 12):
        a.px(x, 8, "F", "shine" if x in (6, 9) else "light")
    _seams(a, [(5, 5), (5, 6), (6, 7), (10, 5), (10, 6), (9, 10), (9, 11), (5, 10)])
    for x, y in ((3, 6), (12, 6), (3, 11), (12, 11)):
        a.px(x, y, "B", "shine")
    a.px(7, 4, "A", "light")
    a.px(8, 4, "A", "mid")
    a.px(7, 3, "A", "shine")


@painted("relic_magmaguard_chestplate")
def magma_chest(a):
    """Magmaguard cuirass: basalt plates split by molten seams around a glowing core, brass pauldron rims."""
    itemart.PAINTED["chestplate"](a)
    _seams(a, [(4, 5), (4, 6), (5, 7), (5, 8), (10, 5), (10, 6), (9, 7), (9, 8), (6, 11), (9, 11)])
    a.sphere("F", 7.5, 6.5, 1.6)
    for x in (1, 2, 3, 4, 10, 11, 12, 13):
        a.px(x, 3, "B", "light" if x < 8 else "mid")


@painted("relic_magmaguard_leggings")
def magma_legs(a):
    """Magmaguard tassets: basalt legs with molten knee seams."""
    itemart.PAINTED["leggings"](a)
    _seams(a, [(4, 6), (5, 7), (4, 8), (10, 6), (11, 7), (10, 8), (7, 3), (8, 3)])


@painted("relic_magmaguard_boots")
def magma_boots(a):
    """Magmaguard boots: heavy basalt boots, molten toe seams, brass cuffs."""
    itemart.PAINTED["boots"](a)
    _seams(a, [(3, 10), (4, 11), (10, 10), (11, 11), (5, 8), (10, 8)])


# ------------------------------------------------------------------ armour: Tidewarden (abbey)
def _scales(a, x0, y0, x1, y1):
    """Fish-scale mail: every other row offset, the top of each scale lit."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if a.m[y][x] != "M":
                continue
            if (x + (y // 2) % 2 * 1) % 2 == 0 and y % 2 == 0:
                a.tone(x, y, "light")
            elif y % 2 == 1 and (x + (y // 2) % 2) % 2 == 1:
                a.tone(x, y, "deep")


@painted("relic_tidewarden_helmet")
def tide_helmet(a):
    """Tidewarden sallet: a rounded sea-steel helm swept back into a tail, a fin crest of sapphire, a pearl brow."""
    a.stamp([
        "......AAA.......",
        ".....AAAAA......",
        "....MMMMMMMM....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMMM.",
        "..MKKKKKKKMMMMMM",
        "..MM......MMMMM.",
        "..MM......MMM...",
        "...M......MM....",
    ], {"M": "M", "A": "A", "K": "X"}, 0, 2)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.2, 0.75))
    a.shade_dir("A", 1.0, 0.3, cuts=(-0.3, 0.3, 0.8))
    a.px(6, 2, "A", "shine")
    a.px(5, 5, "M", "shine")
    a.px(6, 5, "M", "shine")
    a.sphere("Q", 7.5, 7.0, 0.9, shine=False)
    a.px(7, 7, "Q", "shine")
    for x in (10, 12, 14):
        a.px(x, 8, "M", "deep")


@painted("relic_tidewarden_chestplate")
def tide_chest(a):
    """Tidewarden hauberk: scale mail of sea-steel with a shell clasp at the collar and a sapphire belt."""
    itemart.PAINTED["chestplate"](a)
    _scales(a, 2, 4, 12, 11)
    a.disc("Q", 7.5, 3.2, 1.3)
    a.px(7, 2, "Q", "shine")
    a.px(8, 4, "Q", "dark")


@painted("relic_tidewarden_leggings")
def tide_legs(a):
    """Tidewarden chausses: scale-mail legs under a sapphire waist band."""
    itemart.PAINTED["leggings"](a)
    _scales(a, 3, 3, 12, 11)


@painted("relic_tidewarden_boots")
def tide_boots(a):
    """Tidewarden wading boots: tall sea-steel boots with scalloped shell cuffs."""
    itemart.PAINTED["boots"](a)
    for x, y in ((3, 5), (5, 5), (8, 5), (10, 5)):
        a.px(x, y, "Q", "light")
    for x, y in ((4, 5), (9, 5)):
        a.px(x, y, "Q", "shine")


# ------------------------------------------------------------------ armour: Pilgrim's Windrobes (ascent)
@painted("relic_windrobe_helmet")
def wind_hood(a):
    """Wind hood: a peaked cream hood with a red trim, the face in shadow, a ribbon trailing in the wind."""
    itemart.PAINTED["hood"](a)
    for x in range(0, 15):
        if a.m[12][x] is not None:
            a.px(x, 12, "A", "mid" if x % 3 else "light")
    a.px(6, 9, "Q", "light")
    a.px(9, 9, "Q", "light")
    for i, (x, y) in enumerate(((10, 2), (11, 2), (12, 3), (13, 3), (14, 4), (15, 4))):
        a.px(x, y, "A", "light" if i % 2 else "mid")


@painted("relic_windrobe_chestplate")
def wind_robe(a):
    """Windrobe: a wide-sleeved cream robe, a red sash knotted at the hip with its ends fluttering."""
    itemart.PAINTED["robe"](a)
    for x in range(4, 10):
        a.px(x, 8, "A", "light" if x < 6 else "mid")
    a.px(10, 9, "A", "mid")
    a.px(11, 10, "A", "dark")
    a.px(10, 10, "A", "light")
    for x, y in ((6, 4), (5, 5), (6, 6), (7, 5), (6, 5)):
        a.px(x, y, "M", "light")
    # wind stripes woven in the hem
    for x in (3, 5, 9, 11):
        if a.m[13][x] is not None:
            a.px(x, 13, "A", "dark")


@painted("relic_windrobe_leggings")
def wind_trousers(a):
    """Wind trousers: loose cream trousers wrapped with red bands at the calf."""
    itemart.PAINTED["leggings"](a)
    for x in (3, 4, 5, 6, 9, 10, 11, 12):
        a.px(x, 9, "A", "mid" if x % 2 else "light")


@painted("relic_windrobe_boots")
def wind_sandals(a):
    """Wind sandals: cream foot wraps on oak soles, oxblood straps crossing up to the ankle."""
    a.stamp([
        "..MM.....MM.....",
        "..MM.....MM.....",
        "..MMM....MMM....",
        ".MMMMM..MMMMM...",
        "MMMMMMM.MMMMMMM.",
        "WWWWWWW.WWWWWWW.",
    ], {"M": "M", "W": "W"}, 0, 7)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.2, 0.75))
    for ox in (0, 8):
        for x, y in ((2, 7), (3, 8), (2, 9), (3, 10), (4, 10), (1, 11), (5, 11)):
            a.px(ox + x, y, "L", "light" if (x + y) % 2 else "mid")
    for x in range(0, 7):
        a.px(x, 12, "W", "light" if x < 3 else "mid")


@painted("relic_magma_maul")
def magma_maul(a):
    """Caldera Magma Maul: a great basalt block cracked open on a molten core, brass-bound, on a dark haft."""
    shaft(a, 8, grip=(1, 5))
    collar(a, 7)
    a.stamp([
        ".MMMMMMMM.",
        "MMMMMMMMMM",
        "MMMMMMMMMM",
        "MMMMMMMMMM",
        "MMMMMMMMMM",
        "MMMMMMMMMM",
        ".MMMMMMMM.",
    ], {"M": "M"}, 5, 0)
    a.shade_dir("M", 0.8, 1.0, cuts=(-0.55, 0.1, 0.65))
    for x, y in ((7, 1), (8, 2), (8, 3), (9, 4), (12, 1), (11, 2), (12, 3), (11, 5), (7, 5), (6, 3)):
        a.px(x, y, "F", "mid")
    a.sphere("F", 9.6, 3.4, 1.5)
    a.px(9, 3, "F", "shine")
    for y in range(0, 7):
        a.px(5, y, "B", "light" if y < 3 else "mid") if a.m[y][5] else None
        a.px(14, y, "B", "dark" if y > 2 else "mid") if a.m[y][14] else None
    a.px(6, 0, "M", "shine")
    a.px(7, 0, "M", "shine")


@painted("relic_bastion_cannon")
def bastion_cannon(a):
    """Bastion Hand-Cannon: a flared brass barrel banded with dark iron, a glowing touch-hole, an oak stock."""
    # stock: a curved oak butt in the bottom-left corner
    a.poly("H", [(0.5, 15.5), (0.5, 12.0), (3.0, 10.2), (6.2, 10.6), (4.2, 13.2), (2.6, 15.5)])
    a.shade_dir("H", 1.0, 0.6, cuts=(-0.5, 0.15, 0.65))
    # barrel along the diagonal, widening to a bell mouth at the top right
    a.seg("M", 4.6, 11.4, 12.2, 3.8, 1.25)
    a.disc("M", 13.0, 3.0, 2.3)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.1, 0.6))
    a.disc("X", 13.4, 2.6, 1.0)
    a.px(13, 2, "X", "deep")
    for i in (0, 3):                       # iron bands
        x, y = 6 + i * 2, 9 - i * 2
        a.px(x, y, "X", "mid")
        a.px(x + 1, y + 1, "X", "dark")
        a.px(x - 1, y - 1, "X", "light")
    a.px(7, 7, "F", "shine")               # the lit touch-hole
    a.px(6, 6, "Y", "mid")
    a.px(5, 5, "Y", "light")
    a.px(11, 4, "M", "shine")
    a.px(9, 6, "M", "shine")
    # trigger guard
    a.px(5, 13, "X", "mid")
    a.px(6, 13, "X", "dark")


@painted("relic_rimefang_spear")
def rimefang_spear(a):
    """Rimefang Spear: a dark haft wrapped in fur, an iron socket and a long fang of blue ice, frost riming it."""
    shaft(a, 9, grip=(1, 4))
    a.px(4, 11, "Q", "light")
    a.px(5, 10, "Q", "mid")
    collar(a, 8, key="X")
    a.stamp([
        "......s",
        ".....ls",
        "....lsd",
        "...lsde",
        "..lsde.",
        ".lsde..",
        ".sde...",
        "..e....",
    ], L("G", None), 9, 0)
    for x, y in ((12, 1), (14, 3), (11, 4)):
        a.px(x, y, "Y", "light")
    a.px(8, 7, "A", "light")
    a.px(8, 8, "A", "mid")


@painted("relic_oathbreaker")
def oathbreaker(a):
    """Oathbreaker: a broad limestone greatsword with a gold-rimmed fuller and a crack across it, a wide gold guard,
    a key-ring pommel."""
    # blade from the guard (5, 10) up to the tip (15, 0), three pixels wide with a fuller
    for i in range(10):
        x, y = 6 + i, 9 - i
        a.px(x - 1, y, "M", "light")
        a.px(x, y, "M", "mid" if i < 8 else "light")
        a.px(x, y + 1, "M", "dark")
        a.px(x + 1, y + 1, "M", "deep") if i < 9 else None
    for i in range(1, 8):
        a.px(6 + i, 9 - i + 1, "A", "light" if i % 2 else "mid")
    a.px(15, 0, "M", "shine")
    a.px(14, 0, "M", "light")
    # the crack (an oath broken)
    a.px(10, 5, "X", "mid")
    a.px(11, 5, "X", "dark")
    # guard
    for i in range(-3, 4):
        a.px(5 + i, 10 + i, "B", "light" if i < 0 else "mid" if i == 0 else "dark")
    a.px(2, 7, "A", "shine")
    a.px(8, 13, "A", "dark")
    # grip and ring pommel
    diag(a, "H", 2, 13, 3, width=2)
    a.ring("B", 1.5, 14.5, 0.4, 1.4)


@painted("relic_toll_billhook")
def toll_billhook(a):
    """Toll-Warden's Billhook: an oak pole, a broad steel bill whose tip curls back into a hook, a spur behind and a
    gilded toll seal on the socket."""
    shaft(a, 10, grip=(1, 4))
    a.poly("M", [(10.0, 6.6), (9.6, 3.4), (11.2, 1.0), (14.0, 0.2), (15.4, 0.8), (13.4, 1.8), (12.4, 3.4), (12.8, 5.0),
                 (11.6, 6.8)])
    a.shade_dir("M", 1.0, 0.8, cuts=(-0.5, 0.1, 0.65))
    a.px(10, 2, "M", "shine")
    a.px(14, 0, "M", "light")
    a.seg("X", 12.6, 6.2, 14.6, 7.0, 0.5)        # the spur
    a.disc("A", 10.4, 7.4, 0.9)                  # the toll seal
    a.px(10, 7, "A", "shine")


@painted("relic_undertow_glaive")
def undertow_glaive(a):
    """Undertow Glaive: a bone haft, a sea-steel blade curling over like a breaking wave, foam on its crest."""
    shaft(a, 10, grip=(1, 4))
    collar(a, 9, key="A")
    a.poly("M", [(10.0, 6.0), (11.0, 2.0), (13.5, 0.2), (15.8, 0.6), (14.0, 2.0), (13.2, 4.0), (12.4, 6.6)])
    a.shade_dir("M", 1.0, 0.8, cuts=(-0.5, 0.1, 0.65))
    for x, y in ((13, 0), (14, 0), (15, 0), (12, 1)):
        a.px(x, y, "Q", "shine" if x == 14 else "light")
    a.px(11, 3, "M", "shine")
    a.px(13, 5, "A", "light")


@painted("relic_gale_staff")
def gale_staff(a):
    """Pilgrim's Gale Staff: a knotted walking staff with a crook, a bronze bell hung from it and red prayer
    ribbons streaming in the wind."""
    a.seg("M", 2.0, 15.0, 10.5, 3.0, 0.75)
    a.seg("M", 10.5, 3.0, 12.0, 1.0, 0.75)
    a.seg("M", 12.0, 1.0, 14.0, 1.2, 0.7)
    a.seg("M", 14.0, 1.2, 14.6, 3.2, 0.6)
    a.shade_dir("M", 1.0, 0.4, cuts=(-0.6, 0.1, 0.7))
    for x, y in ((5, 11), (8, 7)):
        a.px(x, y, "M", "deep")
        a.px(x - 1, y, "M", "light")
    # bell under the crook end
    a.stamp([".d.", "lmd", "lmd", "ddd"], L("C", None), 13, 4)
    a.px(14, 8, "X", "mid")
    # ribbons
    for i, (x, y) in enumerate(((9, 5), (8, 4), (7, 4), (6, 3), (5, 3), (9, 6), (8, 6), (7, 7), (6, 7))):
        a.px(x, y, "A", "light" if i % 2 else "mid")
    a.px(4, 2, "Y", "light")
    a.px(3, 6, "Y", "mid")


@painted("relic_starfall_lance")
def starfall_lance(a):
    """Starfall Lance: a purpur haft, a long pale-gold lance point and a four-pointed star at its collar, motes of
    starlight trailing behind."""
    shaft(a, 9, grip=(1, 4))
    a.stamp([
        ".....s",
        "....ls",
        "...lsd",
        "..lsd.",
        ".lsd..",
        "lsd...",
        "sd....",
    ], L("M", None), 9, 0)
    # four-pointed star at the collar
    cx, cy = 9, 7
    for dx, dy, t in ((0, 0, "shine"), (1, 0, "light"), (-1, 0, "light"), (0, 1, "light"), (0, -1, "light"),
                      (2, 0, "mid"), (-2, 0, "mid"), (0, 2, "mid"), (0, -2, "mid")):
        a.px(cx + dx, cy + dy, "A", t)
    for x, y in ((4, 4), (6, 2), (2, 7), (12, 10)):
        a.px(x, y, "Y", "light")


# ------------------------------------------------------------------ accessories
@painted("relic_jarl_mantle")
def jarl_mantle(a):
    """Jarl's Bear Mantle: a brown bear-fur cloak seen from behind, a white fur collar and an ice-stone clasp."""
    a.poly("M", [(4, 3), (12, 3), (14.5, 15), (1.5, 15)])
    a.shade_dir("M", 1.0, 0.4, cuts=(-0.55, 0.15, 0.7))
    rng = random.Random(7)
    for y in range(5, 15):
        for x in range(16):
            if a.m[y][x] == "M" and rng.random() < 0.22:
                a.tone(x, y, "dark" if rng.random() < 0.6 else "light")
    for x in range(3, 13):
        a.px(x, 3, "Q", "light" if x % 2 else "mid")
        a.px(x, 2, "Q", "shine" if x % 3 == 0 else "light") if 4 <= x <= 11 else None
    for x in (2, 13):
        a.px(x, 4, "Q", "mid")
    a.sphere("A", 7.9, 4.6, 1.3)
    a.px(7, 4, "A", "shine")
    # ragged hem
    for x in range(2, 15, 2):
        if a.m[14][x] == "M":
            a.px(x, 14, None)


@painted("relic_ember_signet")
def ember_signet(a):
    """Castellan's Ember Signet: a heavy gold band with an oval bezel holding a glowing ember seal."""
    a.ring("M", 8.0, 10.8, 2.0, 3.7)
    a.ellipse("M", 8.0, 5.0, 3.6, 2.8)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.15, 0.65))
    a.ellipse("A", 8.0, 5.0, 2.4, 1.7)
    a.px(7, 4, "F", "shine")
    a.px(8, 5, "F", "light")
    a.px(8, 4, "F", "light")
    a.px(7, 5, "F", "mid")
    a.px(5, 3, "M", "shine")


@painted("relic_pilgrim_band")
def pilgrim_band(a):
    """Pilgrim's Wind Band: a worn brass ring engraved with a spiral of wind, a puff of aether light above it."""
    a.ring("M", 8.0, 10.0, 2.6, 4.6)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.15, 0.65))
    for x, y in ((5, 7), (7, 6), (10, 7), (11, 9), (10, 12), (6, 13)):
        a.px(x, y, "A", "light")
    for i, (x, y) in enumerate(((6, 3), (7, 2), (8, 2), (9, 3), (8, 4), (10, 2), (11, 1))):
        a.px(x, y, "Y", "light" if i % 2 else "mid")


@painted("relic_tide_pendant")
def tide_pendant(a):
    """Abbey Tide Pendant: a fine chain, a scallop shell of sea-steel cradling a pearl."""
    for i, (x, y) in enumerate(((2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (13, 1), (12, 2), (11, 3), (10, 4), (9, 5))):
        a.px(x, y, "B", "light" if i % 2 else "dark")
    a.poly("M", [(4.5, 9.0), (8.0, 5.5), (11.5, 9.0), (10.5, 13.5), (5.5, 13.5)])
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.15, 0.65))
    for x in (6, 8, 10):
        for y in range(9, 14):
            if a.m[y][x] == "M":
                a.tone(x, y, "dark")
    a.sphere("Q", 8.0, 10.5, 1.6)
    a.px(7, 9, "Q", "shine")
    a.px(8, 6, "A", "light")


@painted("relic_halo_locket")
def halo_locket(a):
    """Halo Locket: a chain, a broken ring of gold around a glowing core of starlight."""
    for i, (x, y) in enumerate(((2, 0), (3, 1), (4, 2), (5, 3), (13, 0), (12, 1), (11, 2), (10, 3))):
        a.px(x, y, "B", "light" if i % 2 else "dark")
    a.ring("M", 8.0, 9.5, 2.6, 4.4)
    a.clear(lambda x, y: x > 9.0 and y < 8.0 and x - 9.0 > (8.0 - y) * 0.2)       # the break in the halo
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.15, 0.65))
    a.sphere("E", 8.0, 9.5, 1.8)
    a.px(7, 8, "Y", "light")
    for x, y in ((12, 5), (13, 4), (14, 6)):
        a.px(x, y, "Y", "light")


@painted("relic_oath_girdle")
def oath_girdle(a):
    """Oathbound Girdle: a broad leather belt, a gold buckle shaped like the toll key, studs along it."""
    a.box("M", 0, 6, 15, 10)
    a.shade_dir("M", 0.0, 1.0, cuts=(-0.5, 0.2, 0.7))
    for x in range(0, 16):
        a.px(x, 6, "M", "light")
        a.px(x, 10, "M", "deep")
    for x in (1, 3, 12, 14):
        a.px(x, 8, "B", "shine")
    a.ring("A", 7.5, 8.0, 1.2, 2.9)
    a.px(7, 8, "A", "mid")
    a.px(8, 8, "A", "mid")
    a.px(9, 8, "A", "light")
    a.px(10, 8, "A", "light")
    a.px(10, 9, "A", "dark")
    a.px(5, 6, "A", "shine")
    # loose tongue hanging down
    a.box("M", 12, 11, 13, 13)
    a.px(12, 12, "B", "light")


# ------------------------------------------------------------------ armour layers worn on the body
def _ramp(pal):
    from .itemart import tones
    t = tones(pal)
    return [t["shine"], t["light"], t["mid"], t["dark"], t["deep"], t["outline"]]


def armor_layer(prefix, legs=False):
    """64x32 humanoid (or leggings) layer: each cube face shaded from the top-left, with plate seams, trim and the
    set's own details (fur, horns' roots, magma seams, scales, cloth folds)."""
    s = {"frostplate": ("glacier", "Q", (230, 240, 248)), "magmaguard": ("magma", "F", (255, 160, 60)),
         "tidewarden": ("tide", "Q", (236, 230, 210)), "windrobe": ("wind", "A", (200, 50, 44))}[prefix]
    mat, _trim, trim = s
    base = _ramp(MATERIALS[mat])
    accent = _ramp(itemart.two_tone(*ACCENTS[{"frostplate": "ice", "magmaguard": "ember", "tidewarden": "sapphire",
                                              "windrobe": "red"}[prefix]]))
    brass = _ramp(itemart.STEAM["B"])
    fire = _ramp(itemart.STEAM["F"])
    rng = random.Random(prefix + str(legs))
    cv = Canvas(64, 32)

    def faces(u, v, w, h, d):
        # (x, y, width, height, kind) of the unfolded cube: top, bottom, right, front, left, back
        return [(u + d, v, w, d, "top"), (u + d + w, v, w, d, "bottom"), (u, v + d, d, h, "side"),
                (u + d, v + d, w, h, "front"), (u + d + w, v + d, d, h, "side"), (u + d + w + d, v + d, w, h, "back")]

    def paint_box(u, v, w, h, d, part):
        for (x0, y0, ww, hh, kind) in faces(u, v, w, h, d):
            for y in range(y0, y0 + hh):
                for x in range(x0, x0 + ww):
                    fx, fy = (x - x0) / max(1, ww - 1), (y - y0) / max(1, hh - 1)
                    k = 2
                    if kind == "top":
                        k = 1
                    elif kind == "bottom":
                        k = 3
                    else:
                        k = 2 + (fy > 0.75) - (fx < 0.2 and fy < 0.5)
                    if rng.random() < 0.12:
                        k += rng.choice((-1, 1))
                    edge = x in (x0, x0 + ww - 1) or y in (y0, y0 + hh - 1)
                    if edge:
                        k = 4 if (x == x0 + ww - 1 or y == y0 + hh - 1) else max(1, k - 1)
                    cv.set(x, y, base[max(0, min(5, k))])
            detail(x0, y0, ww, hh, kind, part)

    def detail(x0, y0, w, h, kind, part):
        if kind in ("top", "bottom"):
            return
        if prefix == "frostplate":
            if part in ("body", "arm") and h >= 12:      # fur mantle on the shoulders / sleeve tops
                for x in range(x0, x0 + w):
                    for y in range(y0, y0 + 2 + (x % 2)):
                        cv.set(x, y, (232, 236, 236) if (x + y) % 3 else (250, 252, 252))
            if part == "head" and kind == "front":
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + 3, accent[1])
                for y in range(y0 + 3, y0 + 7):
                    cv.set(x0 + 3, y, base[1])
                    cv.set(x0 + 4, y, base[3])
                for x in (x0 + 1, x0 + 2, x0 + 5, x0 + 6):
                    cv.set(x, y0 + 4, (0, 0, 0, 0))
            if part == "boots":
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + h - 5, (236, 240, 240))
            if part in ("legs", "waist") and kind == "front":
                for y in range(y0 + 4, y0 + 6):
                    for x in range(x0, x0 + w):
                        cv.set(x, y, accent[2])
        elif prefix == "magmaguard":
            for _ in range(max(1, w * h // 18)):         # molten cracks
                x, y = x0 + rng.randrange(w), y0 + rng.randrange(h)
                for k in range(rng.randint(2, 4)):
                    if x0 <= x < x0 + w and y0 <= y < y0 + h:
                        cv.set(x, y, fire[1 if k == 1 else 2])
                    x += rng.choice((-1, 0, 1))
                    y += 1
            if part == "head" and kind == "front":
                for x in range(x0 + 1, x0 + w - 1):
                    cv.set(x, y0 + 4, fire[0] if x in (x0 + 2, x0 + 5) else fire[1])
            if kind == "front" and part in ("body", "waist"):
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + (h - 3 if part == "body" else 0), brass[2])
                    cv.set(x, y0 + (h - 4 if part == "body" else 1), brass[1])
            for x, y in ((x0 + 1, y0 + 1), (x0 + w - 2, y0 + 1)):
                cv.set(x, y, brass[0])
        elif prefix == "tidewarden":
            for y in range(y0 + 1, y0 + h - 1):          # scale mail
                for x in range(x0, x0 + w):
                    if y % 2 == 0 and (x + y // 2) % 2 == 0:
                        cv.set(x, y, base[1])
                    elif y % 2 == 1 and (x + y // 2) % 2 == 1:
                        cv.set(x, y, base[3])
            if part == "head":
                if kind == "front":
                    for x in range(x0 + 1, x0 + w - 1):
                        cv.set(x, y0 + 4, (0, 0, 0, 0) if x not in (x0 + 3, x0 + 4) else base[2])
                    cv.set(x0 + 3, y0 + 2, (236, 230, 210))
                    cv.set(x0 + 4, y0 + 2, (210, 200, 180))
                for x in range(x0, x0 + w):
                    cv.set(x, y0, accent[1])
            if kind == "front" and part in ("body", "waist"):
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + (h - 3 if part == "body" else 0), accent[2])
        elif prefix == "windrobe":
            for x in range(x0, x0 + w):                   # cloth folds
                if (x - x0) % 3 == 1:
                    for y in range(y0 + 2, y0 + h - 1):
                        cv.set(x, y, base[3] if y % 4 else base[2])
            if part == "head" and kind == "front":
                for y in range(y0 + 2, y0 + h):
                    for x in range(x0 + 1, x0 + w - 1):
                        cv.set(x, y, (0, 0, 0, 0))
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + 1, accent[1])
            if part == "body" and kind in ("front", "back"):
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + h - 4, accent[1])
                    cv.set(x, y0 + h - 3, accent[3])
            if part == "arm":
                for x in range(x0, x0 + w):
                    cv.set(x, y0 + h - 2, accent[2])
            if part in ("legs", "boots"):
                for y in range(y0 + h - 4, y0 + h):
                    for x in range(x0, x0 + w):
                        if (x + y) % 3 == 0:
                            cv.set(x, y, accent[2])

    if legs:
        paint_box(0, 16, 4, 12, 4, "legs")
        paint_box(16, 16, 8, 12, 4, "waist")
    else:
        paint_box(0, 0, 8, 8, 8, "head")
        paint_box(16, 16, 8, 12, 4, "body")
        paint_box(40, 16, 4, 12, 4, "arm")
        paint_box(0, 16, 4, 12, 4, "boots")
    if not legs and prefix == "windrobe":
        # the hood: only the head layer's outer region would sit over the hat; keep the inner face clear above
        pass
    return cv


# ------------------------------------------------------------------ gen_textures
def textures():
    from . import relics, held3d
    out = {}
    for prefix, s in relics.SETS.items():
        for piece in relics.PIECES:
            out[f"item/{prefix}_{piece}"] = render(f"relic_{prefix}_{piece}", s["mat"], "dark", s["accent"])
        out[f"entity/equipment/humanoid/{prefix}"] = armor_layer(prefix)
        out[f"entity/equipment/humanoid_leggings/{prefix}"] = armor_layer(prefix, legs=True)
    for wid, w in relics.WEAPONS.items():
        mat, handle, accent = w["sprite"]
        out[f"item/{wid}"] = render(f"relic_{wid}", mat, handle, accent)
    for aid, acc in relics.ACCESSORIES.items():
        mat, accent = acc["sprite"]
        out[f"item/{aid}"] = render(f"relic_{aid}", mat, "dark", accent)
    return out


# ------------------------------------------------------------------ 3D in-hand archetypes (held3d)
def _held_archetypes():
    from .held3d import _grip, _shaft, box

    def magma_maul():
        """A great basalt block on a dark haft, molten seams glowing through, brass bands at both faces."""
        out = _shaft(-3, 18, 1.8) + _grip(3, 10, 2.4)
        out += [box(3, 18, 5, 13, 25, 11, "mid"),
                box(2.5, 18.5, 4.5, 3, 24.5, 11.5, "brass"), box(13, 18.5, 4.5, 13.5, 24.5, 11.5, "brass_dark"),
                box(5, 19, 4.8, 6, 24, 5, "glow"), box(9, 18.5, 4.8, 10, 23, 5, "glow"),
                box(6, 21, 4.8, 9, 22, 5, "glow"), box(10.5, 20, 11, 11.5, 24.5, 11.2, "glow"),
                box(5.5, 20, 11, 7.5, 21, 11.2, "glow"), box(7, 25, 7, 9, 26, 9, "dark"),
                box(6.5, 17, 6.5, 9.5, 18, 9.5, "brass_dark"), box(7, -4, 7, 9, -3, 9, "brass")]
        return out

    def oath_greatsword():
        """A broad limestone blade with a gilded fuller, a crack across it, a wide gold guard and a key-ring pommel."""
        top = 30
        out = _grip(2, 8.5, 2.2) + [box(6.5, 0, 6.5, 9.5, 2, 9.5, "accent"),
                                    box(7.25, -2, 7.25, 8.75, 0, 8.75, "accent_dark")]
        out += [box(2, 8.5, 6.75, 14, 10, 9.25, "accent"), box(1, 9, 7, 2, 11.5, 9, "accent_dark"),
                box(14, 9, 7, 15, 11.5, 9, "accent_dark"),
                box(5, 10, 7.3, 11, top, 8.7, "mid"), box(4.6, 11, 7.55, 5, top - 1, 8.45, "light"),
                box(11, 11, 7.55, 11.4, top - 1, 8.45, "light"), box(7.5, 11, 7.1, 8.5, top - 3, 8.9, "accent_dark"),
                box(5.5, top, 7.45, 10.5, top + 1, 8.55, "light"), box(7, top + 1, 7.6, 9, 31.5, 8.4, "light"),
                box(5, 19, 7.2, 8, 19.6, 8.8, "dark"), box(8, 19.6, 7.2, 11, 20.2, 8.8, "dark")]
        return out

    def cannon():
        """A brass barrel flaring into a bell mouth, dark iron bands, an oak stock and grip, a glowing touch-hole."""
        out = [box(6.8, -2, 6.8, 9.2, 8, 9.2, "handle"), box(6.4, -4, 6.0, 9.6, -1, 10, "handle_dark"),
               box(7, 7, 6.6, 9, 9, 9.4, "iron_dark")]
        out += [box(6.25, 9, 6.25, 9.75, 25, 9.75, "mid"), box(5.25, 25, 5.25, 10.75, 28, 10.75, "light"),
                box(5.75, 28, 5.75, 10.25, 28.5, 10.25, "outline"),
                box(5.9, 12, 5.9, 10.1, 13, 10.1, "iron_dark"), box(5.9, 20, 5.9, 10.1, 21, 10.1, "iron_dark"),
                box(5.5, 24, 5.5, 10.5, 25, 10.5, "iron_dark"), box(7.5, 15, 9.75, 8.5, 16, 10.25, "glow"),
                box(7.5, 5, 9.2, 8.5, 7, 10.6, "iron_dark")]
        return out

    def rime_spear():
        """A dark haft wrapped in fur at the grip, an iron socket and a long fang of blue ice with frost spurs."""
        out = _shaft(-6, 20, 1.5) + _grip(2, 9, 2.2) + [box(6.6, 9, 6.6, 9.4, 10, 9.4, "cream")]
        out += [box(6.6, 19, 6.6, 9.4, 21, 9.4, "iron_dark"),
                box(6.75, 21, 7.25, 9.25, 27, 8.75, "mid"), box(7.25, 27, 7.5, 8.75, 30, 8.5, "light"),
                box(7.6, 30, 7.7, 8.4, 31.5, 8.3, "glow"), box(5.5, 22, 7.6, 6.75, 24, 8.4, "glow"),
                box(9.25, 23, 7.6, 10.5, 25, 8.4, "glow")]
        return out

    def billhook():
        """An oak pole, a broad steel bill curling into a hook at the tip, a back spur and a gilded seal."""
        out = _shaft(-6, 21, 1.5) + _grip(2, 9, 2.0)
        out += [box(6.6, 20, 6.6, 9.4, 21.5, 9.4, "accent"),
                box(7, 21.5, 7.5, 9.5, 28, 8.5, "mid"), box(5.5, 22, 7.55, 7, 27, 8.45, "light"),
                box(8, 28, 7.5, 10.5, 30, 8.5, "mid"), box(9.5, 26.5, 7.55, 11, 29, 8.45, "light"),
                box(9.5, 22.5, 7.6, 12, 23.5, 8.4, "iron_dark")]
        return out

    def glaive():
        """A bone haft with a sapphire collar and a sea-steel blade curling over like a breaking wave, foam crest."""
        out = _shaft(-6, 22, 1.5) + _grip(3, 9, 2.0)
        out += [box(6.5, 21, 6.5, 9.5, 22.5, 9.5, "accent"),
                box(7, 22.5, 7.5, 9.5, 29, 8.5, "mid"), box(9.5, 25, 7.55, 11, 30, 8.45, "mid"),
                box(10.5, 28.5, 7.6, 13, 31, 8.4, "light"), box(12, 30, 7.65, 14.5, 31.5, 8.35, "cream"),
                box(6.5, 23, 7.6, 7, 28, 8.4, "light"), box(8.5, 22.5, 7.4, 9, 26, 8.6, "dark")]
        return out

    def gale_staff():
        """A knotted wooden staff curling into a crook, a bronze bell hung from it, red ribbons streaming."""
        out = _shaft(-6, 24, 1.6, "handle") + [box(6.6, 6, 6.6, 9.4, 6.8, 9.4, "handle_dark"),
                                                box(6.6, 15, 6.6, 9.4, 15.8, 9.4, "handle_dark")]
        out += [box(7.2, 24, 7.2, 8.8, 29, 8.8, "handle"), box(8.8, 28, 7.2, 12, 29.6, 8.8, "handle"),
                box(11, 25, 7.2, 12.6, 28, 8.8, "handle"),
                box(10.6, 22, 7, 13, 24.5, 9, "brass"), box(11.1, 21.3, 7.5, 12.5, 22, 8.5, "brass_dark"),
                box(5, 23.5, 7.8, 7.2, 24.3, 8.2, "accent"), box(3, 22, 7.8, 5, 22.8, 8.2, "accent"),
                box(4.5, 20, 7.8, 7.2, 20.8, 8.2, "accent_dark"), box(2.5, 18.8, 7.8, 4.5, 19.6, 8.2, "accent_dark")]
        return out

    def star_lance():
        """A purpur haft, a gold vamplate, a long pale-gold lance point and a four-pointed star at the collar."""
        out = _shaft(-6, 16, 1.6) + _grip(2, 8, 2.2)
        out += [box(5, 9, 5, 11, 10.5, 11, "accent_dark"), box(5.5, 10.5, 5.5, 10.5, 12, 10.5, "accent"),
                box(6.5, 16, 6.5, 9.5, 23, 9.5, "mid"), box(7, 23, 7, 9, 28, 9, "light"),
                box(7.5, 28, 7.5, 8.5, 31.5, 8.5, "light"),
                box(3.5, 17.5, 7.6, 12.5, 18.5, 8.4, "glow"), box(7.6, 13.5, 3.5, 8.4, 22.5, 12.5, "glow"),
                box(7.25, 17, 7.25, 8.75, 19, 8.75, "glow")]
        return out

    return {"relic_magma_maul": magma_maul, "relic_cannon": cannon, "relic_rime_spear": rime_spear,
            "relic_oath_greatsword": oath_greatsword, "relic_billhook": billhook, "relic_glaive": glaive,
            "relic_gale_staff": gale_staff, "relic_star_lance": star_lance}


def register_held(archetypes, held):
    """Called at the end of held3d.py: adds the relic archetypes and the weapons that use them."""
    from . import relics
    archetypes.update(_held_archetypes())
    held.update(relics.held())
