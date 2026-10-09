"""The Spore Alchemist (L'Alchimiste des spores): the champion of the Spore Refinery, about 3.5 blocks tall.

Silhouette idea: a hunched alchemist half-consumed by the fungus he refined. He stoops forward over a long stained
leather apron worn on a dusty plum work coat; his head is a hood with a brass respirator mask, a stubby snout with
two filter canisters and two round goggle lenses glowing spore-green. His hump is a fly agaric sprouting out of his
back: a red cap with white warts on a pale stalk, gills underneath, and two little caps budding beside it. A brass
spore-tank is strapped to his lower back in copper bands, hoses running from it to the nozzle-gun in his LEFT hand
(a brass body, a copper nozzle with a flared mouth, a glass reservoir of glowing spores). His RIGHT hand leans on a
long dark stirring staff tipped with a round glass flask of glowing green brew, a little mushroom growing on its
pole. Shelf fungi (orange brackets) crowd his shoulders, white mycelium threads trail from his cuffs and his hem, and
his hands are mottled grey-green.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

PLUM = (86, 60, 78)             # the work coat
PLUM_L = (112, 82, 102)
PLUM_D = (60, 40, 56)
PLUM_DD = (40, 26, 38)
APRON = (128, 86, 52)           # tan leather apron, stained
APRON_L = (158, 112, 72)
APRON_D = (92, 60, 36)
STAIN = (70, 96, 52)            # green-brown spore stains
CAP = (196, 38, 34)             # the fly agaric
CAP_L = (226, 70, 56)
CAP_D = (140, 24, 24)
WART = (240, 232, 214)
STALK = (226, 218, 196)
STALK_D = (184, 174, 150)
GILL = (210, 196, 166)
GILL_D = (164, 148, 118)
MYC = (236, 234, 222)           # mycelium threads
MYC_D = (196, 192, 178)
SHELF = (196, 120, 52)          # bracket fungi
SHELF_L = (232, 168, 92)
SHELF_D = (130, 74, 34)
SPORE = (120, 236, 96)          # the glow of the lenses, the reservoir and the flask
SPORE_L = (200, 255, 170)
SPORE_D = (60, 160, 60)
SKIN = (128, 140, 118)          # mottled grey-green hands
SKIN_D = (96, 108, 88)
HOOD = (70, 52, 46)
HOOD_D = (48, 34, 30)
BOOT = (40, 32, 30)
BOOT_L = (66, 54, 48)
WOOD = (64, 42, 30)
WOOD_D = (44, 28, 20)
GLASS = (170, 214, 190)
HOSE = (52, 48, 46)


# ---------------------------------------------------------------- paint
def mossy(base, seed=0, amount=0.12):
    """Wraps a paint function: spots of green spore stain and white mycelium creeping up from the bottom."""
    def f(face, x, y, w, h):
        c = base(face, x, y, w, h) if callable(base) else base
        if face in ("top", "bottom"):
            return c
        k = y / max(1, h - 1)
        r = B.n(x // 2, y // 2, seed)
        if r < amount * (0.4 + k):
            return MYC if B.n(x, y, seed + 5) > 0.55 else STAIN
        return c
    return f


def wool(seed=0):
    """The plum work coat: a coarse weave, darker folds."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return PLUM_DD
        r = B.n(x, y, seed)
        if face == "top":
            return PLUM_L if r > 0.7 else PLUM
        if (x * 2 + y) % 7 == 0:
            return PLUM_D
        return mul(PLUM, 0.9 + r * 0.2)
    return f


def coat(face, x, y, w, h):
    """The coat's body (16 x 18 x 10): buttoned down the front, a brass-buckled strap of the tank across it."""
    base = wool(11)(face, x, y, w, h)
    if face in ("top", "bottom"):
        return base
    if face in ("left", "right") and abs(x - w // 2) <= 1 and y < 14:
        return B.BRASS_D if y % 5 == 2 else (52, 36, 28)                          # the tank straps
    return mossy(base, 13, 0.10)(face, x, y, w, h)


def apron(seed=0):
    """The long leather apron: tan, scuffed, a spill of green spore stain, stitched edges."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return APRON_D
        r = B.n(x, y, seed)
        if x in (0, w - 1):
            return APRON_D
        if B.n(x // 3, y // 3, seed + 2) < 0.16:
            return STAIN if r > 0.4 else mix(STAIN, APRON, 0.5)
        return APRON_L if r > 0.8 else (APRON if r > 0.2 else APRON_D)
    return f


def bib(face, x, y, w, h):
    """The apron's bib: leather, a pocket with two test tubes and a brass pen."""
    c = apron(17)(face, x, y, w, h)
    if face != "front":
        return c
    if h - 6 <= y <= h - 2 and 1 <= x <= w - 2:
        if y == h - 6:
            return APRON_D                                                        # the pocket's seam
        if x in (2, 4) and y <= h - 4:
            return GLASS if y == h - 5 else SPORE_D                               # the test tubes
        if x == 6 and y <= h - 3:
            return B.BRASS_L
    return c


def skirt(seed=0):
    """The coat's long tails: wool, frayed and grown through with mycelium at the hem."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return MYC_D
        if face != "top" and y >= h - 2:
            return MYC if (x + y) % 3 else PLUM_D
        return mossy(wool(seed), seed + 1, 0.12)(face, x, y, w, h)
    return f


def hood(face, x, y, w, h):
    """The rough hood, sagging, spotted with spores."""
    if face == "bottom":
        return HOOD_D
    r = B.n(x, y, 21)
    if face != "top" and B.n(x // 2, y // 2, 23) < 0.1:
        return STAIN
    return mul(HOOD, 0.88 + r * 0.24)


def mask(face, x, y, w, h):
    """The respirator's brass faceplate, riveted round the edge."""
    if face == "bottom":
        return B.BRASS_D
    if (x in (0, w - 1) or y in (0, h - 1)) and (x + y) % 2 == 0:
        return B.BRASS_L
    return B.BRASS if B.n(x, y, 27) > 0.3 else B.BRASS_D


def snout(face, x, y, w, h):
    """The respirator's snout: a dark grille in a brass ring."""
    if face == "front":
        if 0 < x < w - 1 and 0 < y < h - 1:
            return B.SOOT if y % 2 else B.IRON_L
        return B.BRASS_L
    return B.BRASS if y % 2 else B.BRASS_D


def canister(face, x, y, w, h):
    """A filter canister: copper with a perforated green cap."""
    if face == "front":
        return SPORE_D if (x + y) % 2 else B.COPPER_D
    return B.COPPER_L if y == 0 else (B.COPPER if (x + y) % 3 else B.COPPER_D)


def lens(face, x, y, w, h):
    if face != "front":
        return B.BRASS_D
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if y == 0 else B.BRASS_D
    return SPORE_L if (x, y) == (1, 1) else SPORE


def lens_glow(face, x, y, w, h):
    if face != "front" or x in (0, w - 1) or y in (0, h - 1):
        return None
    return SPORE_L if (x, y) == (1, 1) else SPORE


def cap(face, x, y, w, h):
    """The fly agaric's cap: glossy red, white warts scattered over it."""
    if face == "bottom":
        return GILL if x % 2 else GILL_D                                          # the gills underneath
    r = B.n(x, y, 31)
    if B.n(x // 2, y // 2, 33) > 0.82 and (x + y) % 2 == 0:
        return WART
    if face == "top":
        return CAP_L if r > 0.6 else CAP
    if y == h - 1:
        return CAP_D
    return CAP_L if r > 0.85 else (CAP if r > 0.2 else CAP_D)


def gills(face, x, y, w, h):
    if face in ("top", "bottom"):
        return GILL_D if x % 2 else GILL
    return GILL if x % 2 else GILL_D


def stalk(face, x, y, w, h):
    """The pale stalk, a ragged ring (the annulus) round it."""
    if face in ("top", "bottom"):
        return STALK_D
    if y == 1:
        return WART if x % 2 else STALK_D
    return STALK if B.n(x, y, 35) > 0.25 else STALK_D


def shelf(face, x, y, w, h):
    """A bracket fungus: orange, banded, a pale edge."""
    if face == "bottom":
        return SHELF_D
    if face == "top":
        return SHELF_L if (x + y) % 3 == 0 else SHELF
    return SHELF_L if x % 2 == 0 else SHELF


def thread(face, x, y, w, h):
    return MYC if (x + y) % 3 else MYC_D


def tank(face, x, y, w, h):
    """The spore tank: brass in copper bands, a gauge window of glowing spores."""
    if face == "top":
        return B.BRASS_L if (x + y) % 3 else B.BRASS_D
    if face == "bottom":
        return B.BRASS_D
    if y % 4 == 0:
        return B.COPPER_L if x % 3 == 1 else B.COPPER_D
    return B.brass(41, grad=0.3)(face, x, y, w, h)


def window(face, x, y, w, h):
    return SPORE if (x + y) % 2 else SPORE_L


def hose(face, x, y, w, h):
    """A ribbed rubber hose."""
    return HOSE if (x + y) % 2 else (78, 72, 66)


def sleeve(seed=0):
    def f(face, x, y, w, h):
        if face != "top" and y >= h - 2:
            return PLUM_D if (x + y) % 2 else MYC_D                                # the frayed cuff
        return mossy(wool(seed), seed + 1, 0.08)(face, x, y, w, h)
    return f


def hand(face, x, y, w, h):
    """Mottled grey-green skin, the fungus showing through."""
    r = B.n(x, y, 51)
    if r > 0.8:
        return MYC
    return SKIN if r > 0.3 else SKIN_D


def trousers(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return PLUM_DD
        return mul((54, 46, 44), 0.9 + B.n(x, y, seed) * 0.2)
    return f


def boot(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return (22, 18, 16)
        r = B.n(x, y, seed)
        if face != "top" and y <= 1 and r > 0.5:
            return MYC_D
        return BOOT if r > 0.3 else BOOT_L
    return f


def pole(face, x, y, w, h):
    """The stirring staff's dark wood, worn pale where he grips it."""
    if face in ("top", "bottom"):
        return WOOD_D
    return WOOD if (y // 3 + x) % 4 else WOOD_D


def flask(face, x, y, w, h):
    """The round flask at the staff's tip: glass, the green brew inside."""
    if face == "top":
        return GLASS
    if y <= 1:
        return GLASS if (x + y) % 2 else (200, 236, 214)
    return SPORE if (x + y) % 3 else SPORE_D


def flask_glow(face, x, y, w, h):
    if face == "top" or y <= 1:
        return None
    return SPORE if (x + y) % 3 else SPORE_L


def gun(face, x, y, w, h):
    """The nozzle-gun's brass body."""
    if face == "front":
        return B.SOOT if 0 < x < w - 1 and 0 < y < h - 1 else B.BRASS_D
    return B.BRASS_L if y == 0 else (B.BRASS if (x + y) % 3 else B.BRASS_D)


def nozzle(face, x, y, w, h):
    if face == "front":
        return B.SOOT if 0 < x < w - 1 and 0 < y < h - 1 else B.COPPER_L
    return B.COPPER if (x + y) % 2 else B.COPPER_D


# ---------------------------------------------------------------- build
def build():
    m = Model("spore_alchemist", seed=919, shadow=1.3, walk_speed=0.8, walk_scale=0.7, glow_pulse=0.07)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -21, 0))
    m.part("skirt_b", "hips", pivot=(0, 2, 5))
    m.part("apron", "hips", pivot=(0, -1, -5.5))
    m.part("chest", "hips", pivot=(0, -2, 0), rot=(26, 0, 0))
    m.part("head", "chest", pivot=(0, -18, -3), rot=(-30, 0, 0))
    m.part("hump", "chest", pivot=(0, -14, 5), rot=(-20, 0, 0))
    m.part("tank", "chest", pivot=(0, -5, 5))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(4 * sx, -21, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 10, 0))
    m.part("arm_r", "chest", pivot=(-10, -16, 0), rot=(-20, 0, 10))
    m.part("fore_r", "arm_r", pivot=(-0.5, 10, 0), rot=(-40, 0, -6))
    m.part("staff", "fore_r", pivot=(0, 10.5, -0.5), rot=(0, 0, 0))
    m.part("arm_l", "chest", pivot=(10, -16, 0), rot=(-30, 0, -8))
    m.part("fore_l", "arm_l", pivot=(0.5, 10, 0), rot=(-50, 0, 4))
    m.part("gun", "fore_l", pivot=(0, 10.5, -0.5), rot=(54, 0, 0))

    # ---- legs: bent, dark trousers, boots grown over with mycelium
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3, -1, -3, 6, 12, 6, trousers(1 + sx))
        m.box(shin, -3, 0, -3, 6, 5, 6, trousers(3 + sx))
        m.box(shin, -3.5, 5, -3.5, 7, 6, 7, boot(5 + sx))
        m.box(shin, -3.5, 8, -5.5, 7, 3, 2, boot(7 + sx))                          # the toe
        m.box(shin, -2 * sx - 0.5, 9, -6, 1, 2, 1, thread)                         # mycelium creeping up

    # ---- hips, the coat tails and the long apron
    m.box("hips", -8, -2, -5, 16, 5, 10, wool(20))
    m.box("hips", -8.5, 0, -4.5, 1, 14, 9, skirt(21))                               # the sides
    m.box("hips", 7.5, 0, -4.5, 1, 14, 9, skirt(22))
    m.box("skirt_b", -8, 0, 0, 16, 16, 1, skirt(23))
    m.box("apron", -6, 0, -1, 12, 15, 1, apron(24))
    for k, x in enumerate((-7, -4, 2, 5)):                                           # threads off the hem
        m.box("skirt_b", x, 16, 0, 1, 2 + k % 2, 1, thread)
    m.box("apron", -3, 15, -1, 1, 2, 1, thread)
    m.box("apron", 4, 15, -1, 1, 3, 1, thread)

    # ---- the hunched body: the coat, the apron's bib, a belt of vials, the shelf fungi on the shoulders
    m.box("chest", -8, -18, -5, 16, 18, 10, coat)
    m.box("chest", -5, -16, -5.6, 10, 15, 1, bib)
    m.box("chest", -8.5, -2, -5.5, 17, 2, 11, APRON_D)                              # the belt
    for k, x in enumerate((-7, -4.5, 3.5, 6)):                                       # vials on the belt
        m.box("chest", x, -3, -6.2, 1, 3, 1, SPORE if k % 2 else (190, 120, 220), glow=SPORE if k % 2 else None)
    m.box("chest", -11, -19, -4, 5, 1, 5, shelf)                                     # bracket fungi, right shoulder
    m.box("chest", -10.5, -17, -2, 3, 1, 4, shelf)
    m.box("chest", -9.5, -15, 0, 2, 1, 3, shelf)
    m.box("chest", 6, -19, -3, 5, 1, 5, shelf)                                       # left shoulder
    m.box("chest", 8, -17, 0, 3, 1, 4, shelf)
    m.box("chest", 8.4, -12, -3, 1, 1, 3, shelf)
    m.box("chest", -7, -19.5, -5, 14, 2, 10, wool(29))                              # the stooped shoulders

    # ---- the hood and the brass respirator mask with glowing green lenses
    m.box("head", -5, -10, -5, 10, 10, 10, hood)
    m.box("head", -5.5, -11, -4, 11, 3, 10, hood)                                   # the hood's sagging crown
    m.box("head", -4, -12, -1, 8, 2, 6, hood)
    m.box("head", -4.5, -8, -6, 9, 7, 1, mask)                                      # the faceplate
    m.box("head", -4, -7, -6.6, 3, 3, 1, lens, glow=lens_glow)                      # the goggle lenses
    m.box("head", 1, -7, -6.6, 3, 3, 1, lens, glow=lens_glow)
    m.box("head", -0.5, -6.5, -6.4, 1, 1, 1, B.BRASS_D)                             # the bridge
    m.box("head", -2, -4, -9, 4, 4, 3, snout)                                       # the snout
    m.box("head", -5, -3, -8, 2, 3, 3, canister)                                    # filter canisters
    m.box("head", 3, -3, -8, 2, 3, 3, canister)
    m.box("head", -5.4, -6, -2, 1, 2, 4, (52, 36, 28))                             # the mask's straps
    m.box("head", 4.4, -6, -2, 1, 2, 4, (52, 36, 28))
    m.box("head", 2, -12.5, 0, 2, 1, 2, thread)                                     # a tuft of mycelium

    # ---- the hump: a fly agaric sprouting from his back, two small caps budding beside it
    m.box("hump", -2.5, -4, -2, 5, 5, 5, stalk)
    m.box("hump", -9, -9, -7, 18, 5, 15, cap)
    m.box("hump", -7, -11, -5, 14, 2, 11, cap)
    m.box("hump", -4, -12, -3, 8, 1, 7, cap)
    m.box("hump", -8, -4, -6, 16, 1, 13, gills)
    m.box("hump", 5, 1, 2, 2, 3, 2, stalk)                                          # the budding caps
    m.box("hump", 4, -1, 1, 4, 2, 4, cap)
    m.box("hump", -7, 2, 1, 2, 2, 2, stalk)
    m.box("hump", -7.5, 0, 0.5, 3, 2, 3, cap)

    # ---- the spore tank on his lower back, its valve and the hose to the gun
    m.box("tank", -4, -6, 0, 8, 11, 6, tank)
    m.box("tank", -2, -3, 5.6, 4, 4, 1, window, glow=window)
    m.box("tank", -1.5, -8, 1.5, 3, 2, 3, B.brass(43))                               # the valve
    m.box("tank", -3, -9, 2.5, 6, 1, 1, (170, 30, 30))                              # its red wheel
    m.box("tank", 4, 1, 1, 4, 2, 2, hose)                                           # the hose out to the left
    m.box("tank", 7, 1, -3, 2, 2, 5, hose)

    # ---- right arm: the sleeve, the mottled hand, the stirring staff with its flask
    m.box("arm_r", -3, -2, -3, 6, 12, 6, sleeve(60))
    m.box("fore_r", -2.5, 0, -2.5, 5, 10, 5, sleeve(62))
    m.box("fore_r", -2, 10, -2, 4, 3, 4, hand)
    m.box("fore_r", -2, 8, 2.5, 1, 6, 1, thread)                                    # threads trailing the sleeve
    m.box("fore_r", 1, 9, 2.5, 1, 4, 1, thread)
    m.box("staff", -1, -34, -1, 2, 54, 2, pole)                                     # the pole
    m.box("staff", -1.5, 18, -1.5, 3, 2, 3, B.brass(70))                           # the brass ferrule
    m.box("staff", -1.5, -10, -1.5, 3, 1, 3, B.brass(71))                          # a collar
    m.box("staff", -1.5, -34, -1.5, 3, 1, 3, B.brass(72))
    m.box("staff", -1, -37, -1, 2, 3, 2, GLASS)                                     # the flask's neck
    m.box("staff", -3, -43, -3, 6, 6, 6, flask, glow=flask_glow)                    # the flask
    m.box("staff", -1, -44, -1, 2, 1, 2, (120, 90, 60))                             # its cork
    m.box("staff", 1, -22, -1, 2, 2, 2, stalk)                                      # a mushroom on the pole
    m.box("staff", 1, -24, -2, 4, 2, 4, cap)
    m.box("staff", -2, -16, 0, 1, 5, 1, thread)

    # ---- left arm: the sleeve, the hand, the nozzle-gun fed by the hose
    m.box("arm_l", -3, -2, -3, 6, 12, 6, sleeve(64))
    m.box("fore_l", -2.5, 0, -2.5, 5, 10, 5, sleeve(66))
    m.box("fore_l", -2, 10, -2, 4, 3, 4, hand)
    m.box("fore_l", 2.5, 1, 1, 2, 2, 8, hose)                                       # the hose along the forearm
    m.box("fore_l", 1, 8, 2.5, 1, 5, 1, thread)
    m.box("gun", -1, 1, -1, 2, 4, 2, B.MAHOGANY_D)                                  # the grip
    m.box("gun", -1.5, -2, -6, 3, 3, 8, gun)                                        # the body
    m.box("gun", -1, -1.5, -12, 2, 2, 6, nozzle)                                    # the nozzle
    m.box("gun", -1.5, -2, -13, 3, 3, 1, nozzle)                                    # its flared mouth
    m.box("gun", -1, -5, -4, 2, 3, 3, GLASS, glow=SPORE)                            # the spore reservoir
    m.box("gun", -1.5, -5.5, -4.5, 3, 1, 4, B.brass(80))

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.rot("chest", (0, (26, 0, 0)), (1.5, (29, 0, 0)), (3.0, (26, 0, 0)))
    idle.rot("head", (0, (-30, 0, 0)), (1.5, (-33, 6, 0)), (3.0, (-30, 0, 0)))
    idle.rot("hump", (0, (-20, 0, 0)), (1.5, (-17, 0, 2)), (3.0, (-20, 0, 0)))
    idle.scale("hump", (0, (1, 1, 1)), (1.5, (1.04, 1.06, 1.04)), (3.0, (1, 1, 1)))
    idle.rot("arm_l", (0, (-30, 0, -8)), (1.5, (-26, 0, -8)), (3.0, (-30, 0, -8)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (20, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("leg_l", (0, (-20, 0, 0)), (1.0, (20, 0, 0)), (2.0, (-20, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (16, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -0.8, 0)), (1.0, (0, 0, 0)), (1.5, (0, -0.8, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (26, 6, 3)), (1.0, (26, -6, -3)), (2.0, (26, 6, 3)))
    walk.rot("skirt_b", (0, (6, 0, 0)), (1.0, (12, 0, 0)), (2.0, (6, 0, 0)))
    walk.rot("apron", (0, (-8, 0, 0)), (1.0, (-2, 0, 0)), (2.0, (-8, 0, 0)))
    walk.rot("arm_r", (0, (-26, 0, 10)), (1.0, (-12, 0, 10)), (2.0, (-26, 0, 10)))

    # staff (16 / 20 / 14): the staff drawn back over his right shoulder (0.8 s) and swept across in front of him at
    # 0.8 s; he hauls it up overhead and brings the flask down on the cap ahead at 1.4 s; he leans on it to recover
    a = m.anim("staff", 2.5)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.7, (-80, 60, 40)), (0.8, (-84, 64, 40)), (0.86, (-80, -60, -10), "linear"),
          (1.0, (-90, -50, -6)), (1.3, (-170, 0, 10)), (1.4, (-172, 0, 10)), (1.46, (-70, 0, 6), "linear"),
          (2.0, (-60, 0, 8)), (2.5, (-20, 0, 10)))
    a.rot("fore_r", (0, (-40, 0, -6)), (0.8, (-10, 0, 0)), (1.3, (-10, 0, 0)), (1.46, (-30, 0, 0), "linear"),
          (2.5, (-40, 0, -6)))
    a.rot("staff", (0, (0, 0, 0)), (0.8, (56, 0, 0)), (1.3, (26, 0, 0)), (1.46, (46, 0, 0), "linear"),
          (2.5, (0, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (0.7, (24, 36, 0)), (0.8, (24, 40, 0)), (0.86, (30, -34, 0), "linear"),
          (1.3, (14, -6, 0)), (1.4, (12, -6, 0)), (1.46, (40, 0, 0), "linear"), (2.0, (36, 0, 0)), (2.5, (26, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (1.4, (12, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (12, 0, 0)), (1.4, (-16, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("hump", (0, (-20, 0, 0)), (0.86, (-16, 0, 10)), (1.46, (-26, 0, -6)), (2.5, (-20, 0, 0)))

    # spray (24 / 20 / 16): the nozzle-gun levelled from the hip, the tank hissing as it builds pressure (1.2 s); a
    # cone of spores sprayed from 1.2 s to 2.2 s, the gun swaying a little
    a = m.anim("spray", 3.0)
    a.rot("arm_l", (0, (-30, 0, -8)), (1.0, (-70, -10, -6)), (1.2, (-72, -10, -6)), (1.26, (-66, -8, -6), "linear"),
          (1.5, (-70, 4, -6)), (1.8, (-68, -14, -6)), (2.2, (-70, -4, -6)), (3.0, (-30, 0, -8)))
    a.rot("fore_l", (0, (-50, 0, 4)), (1.0, (-20, 0, 0)), (2.2, (-20, 0, 0)), (3.0, (-50, 0, 4)))
    a.rot("gun", (0, (54, 0, 0)), (1.0, (64, 0, 0)), (2.2, (64, 0, 0)), (3.0, (54, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (1.0, (22, -16, 0)), (1.2, (22, -18, 0)), (1.26, (24, -14, 0), "linear"),
          (2.2, (24, -14, 0)), (3.0, (26, 0, 0)))
    a.scale("tank", (0, (1, 1, 1)), (1.0, (1.08, 1.06, 1.1)), (1.26, (0.96, 1, 0.96), "linear"), (2.2, (1, 1, 1)),
            (3.0, (1, 1, 1)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (2.2, (-14, 0, 0)), (3.0, (0, 0, 0)))

    # flask (20 / 10 / 14): he plucks flasks from his belt and winds up (1.0 s), then lobs them at 1.0 s with an
    # overarm throw of his right arm (the staff tucked under it)
    a = m.anim("flask", 2.2)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.4, (-10, 0, 20)), (0.9, (-160, 20, 30)), (1.0, (-164, 20, 30)),
          (1.06, (-60, -10, 10), "linear"), (1.5, (-50, 0, 10)), (2.2, (-20, 0, 10)))
    a.rot("staff", (0, (0, 0, 0)), (0.4, (46, 0, 0)), (1.5, (46, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (0.9, (8, 20, 0)), (1.0, (6, 22, 0)), (1.06, (36, -16, 0), "linear"),
          (1.5, (32, -10, 0)), (2.2, (26, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.0, (16, 0, 0)), (1.5, (-8, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.5, (8, 0, 0)), (2.2, (0, 0, 0)))

    # sprout (18 / 8 / 16): the staff lifted in both hands (0.9 s) and driven into the cap at 0.9 s; mushrooms are
    # called up under his foes while he leans on it
    a = m.anim("sprout", 2.1)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.8, (-150, 0, 20)), (0.9, (-152, 0, 20)), (0.96, (-60, 0, 10), "linear"),
          (1.6, (-58, 0, 10)), (2.1, (-20, 0, 10)))
    a.rot("arm_l", (0, (-30, 0, -8)), (0.8, (-140, 0, -20)), (0.9, (-142, 0, -20)), (0.96, (-60, 0, -10), "linear"),
          (1.6, (-58, 0, -10)), (2.1, (-30, 0, -8)))
    a.rot("staff", (0, (0, 0, 0)), (0.9, (-44, 0, 0)), (0.96, (-24, 0, 0), "linear"), (1.6, (-24, 0, 0)),
          (2.1, (0, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (0.9, (6, 0, 0)), (0.96, (44, 0, 0), "linear"), (1.6, (40, 0, 0)),
          (2.1, (26, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -1, 0)), (0.96, (0, 2, 0), "linear"), (1.6, (0, 2, 0)), (2.1, (0, 0, 0)))
    a.scale("hump", (0, (1, 1, 1)), (0.96, (1.15, 1.2, 1.15), "linear"), (1.6, (1.05, 1.08, 1.05)), (2.1, (1, 1, 1)))

    # shroud (phase 2, 20 / 40 / 14): the tank's valve thrown open, he hunches into a billowing cloud (1.0 s) and is
    # gone (the cloud hides him: the model shrinks to nothing); he bursts out somewhere else at 2.5 s, arms flung wide
    a = m.anim("shroud", 3.7)
    a.rot("chest", (0, (26, 0, 0)), (0.9, (46, 0, 0)), (1.0, (48, 0, 0)), (2.5, (48, 0, 0)),
          (2.56, (0, 0, 0), "linear"), (3.0, (10, 0, 0)), (3.7, (26, 0, 0)))
    a.scale("bone", (0, (1, 1, 1)), (0.9, (0.9, 0.85, 0.9)), (1.0, (0.02, 0.02, 0.02), "linear"),
            (2.44, (0.02, 0.02, 0.02)), (2.5, (1.1, 1.1, 1.1), "linear"), (2.8, (1, 1, 1)), (3.7, (1, 1, 1)))
    a.rot("arm_r", (0, (-20, 0, 10)), (0.9, (-40, 0, 6)), (2.5, (-40, 0, 6)), (2.56, (-60, 0, 80), "linear"),
          (3.0, (-50, 0, 60)), (3.7, (-20, 0, 10)))
    a.rot("arm_l", (0, (-30, 0, -8)), (0.9, (-40, 0, -6)), (2.5, (-40, 0, -6)), (2.56, (-60, 0, -80), "linear"),
          (3.0, (-50, 0, -60)), (3.7, (-30, 0, -8)))
    a.scale("tank", (0, (1, 1, 1)), (0.9, (1.15, 1.1, 1.15)), (1.0, (1, 1, 1), "linear"), (3.7, (1, 1, 1)))

    # bogged (phase 2, 20 / 10 / 16): he stirs the staff in a circle over the cap (1.0 s) and strikes it down at
    # 1.0 s: the bogged claw up out of the mycelium
    a = m.anim("bogged", 2.3)
    a.rot("arm_r", (0, (-20, 0, 10)), (0.3, (-70, 30, 20)), (0.55, (-70, -30, 10)), (0.8, (-70, 30, 20)),
          (0.95, (-110, 0, 10)), (1.0, (-112, 0, 10)), (1.06, (-50, 0, 10), "linear"), (1.6, (-50, 0, 10)),
          (2.3, (-20, 0, 10)))
    a.rot("staff", (0, (0, 0, 0)), (0.8, (26, 0, 0)), (1.0, (-14, 0, 0)), (1.06, (-34, 0, 0), "linear"), (1.6, (-34, 0, 0)),
          (2.3, (0, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (0.3, (22, 10, 0)), (0.55, (22, -10, 0)), (0.8, (22, 10, 0)), (1.0, (18, 0, 0)),
          (1.06, (36, 0, 0), "linear"), (2.3, (26, 0, 0)))
    a.rot("head", (0, (-30, 0, 0)), (1.0, (-40, 0, 0)), (1.06, (-20, 0, 0), "linear"), (2.3, (-30, 0, 0)))

    # bloom (phase 3, 40 / 20 / 20): he throws his head back, the hump swelling and the tank shuddering (2.0 s),
    # then slams the staff down at 2.0 s: the cap breathes
    a = m.anim("bloom", 4.0)
    a.rot("chest", (0, (26, 0, 0)), (0.6, (4, 4, 2)), (0.9, (4, -4, -2)), (1.2, (4, 4, 2)), (1.5, (4, -4, -2)),
          (2.0, (-4, 0, 0)), (2.06, (40, 0, 0), "linear"), (3.2, (36, 0, 0)), (4.0, (26, 0, 0)))
    a.rot("head", (0, (-30, 0, 0)), (2.0, (-50, 0, 0)), (2.06, (-20, 0, 0), "linear"), (4.0, (-30, 0, 0)))
    a.scale("hump", (0, (1, 1, 1)), (2.0, (1.4, 1.5, 1.4)), (2.06, (1.25, 1.3, 1.25), "linear"), (3.2, (1.25, 1.3, 1.25)),
            (4.0, (1, 1, 1)))
    a.rot("arm_r", (0, (-20, 0, 10)), (1.0, (-150, 0, 40)), (2.0, (-170, 0, 30)), (2.06, (-50, 0, 10), "linear"),
          (3.2, (-50, 0, 10)), (4.0, (-20, 0, 10)))
    a.rot("arm_l", (0, (-30, 0, -8)), (1.0, (-120, 0, -50)), (2.0, (-130, 0, -50)), (2.06, (-50, 0, -30), "linear"),
          (3.2, (-50, 0, -30)), (4.0, (-30, 0, -8)))
    a.rot("staff", (0, (0, 0, 0)), (2.0, (-54, 0, 0)), (2.06, (-24, 0, 0), "linear"), (3.2, (-24, 0, 0)),
          (4.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (2.0, (0, -1, 0)), (2.06, (0, 2, 0), "linear"), (3.2, (0, 2, 0)), (4.0, (0, 0, 0)))

    # exhale (phase 3, 50 / 10 / 16): the cap breathes in: he spreads his arms and draws himself up as the hump
    # swells (2.5 s), then folds forward at 2.5 s as the cap breathes out its spores
    a = m.anim("exhale", 3.8)
    a.rot("chest", (0, (26, 0, 0)), (2.4, (0, 0, 0)), (2.5, (-2, 0, 0)), (2.56, (44, 0, 0), "linear"),
          (3.0, (40, 0, 0)), (3.8, (26, 0, 0)))
    a.scale("hump", (0, (1, 1, 1)), (2.4, (1.45, 1.4, 1.45)), (2.5, (1.5, 1.45, 1.5)), (2.56, (0.9, 0.9, 0.9), "linear"),
            (3.0, (0.95, 0.95, 0.95)), (3.8, (1, 1, 1)))
    a.rot("arm_r", (0, (-20, 0, 10)), (2.4, (-60, 0, 70)), (2.5, (-62, 0, 72)), (2.56, (-30, 0, 20), "linear"),
          (3.8, (-20, 0, 10)))
    a.rot("arm_l", (0, (-30, 0, -8)), (2.4, (-60, 0, -70)), (2.5, (-62, 0, -72)), (2.56, (-30, 0, -20), "linear"),
          (3.8, (-30, 0, -8)))
    a.rot("head", (0, (-30, 0, 0)), (2.4, (-50, 0, 0)), (2.56, (-10, 0, 0), "linear"), (3.8, (-30, 0, 0)))

    # roar (phase two): he rears up, arms wide, the hump shuddering, the lenses flaring
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (26, 0, 0)), (0.5, (-4, 0, 0)), (1.6, (-2, 0, 0)), (2.0, (26, 0, 0)))
    a.rot("head", (0, (-30, 0, 0)), (0.5, (-46, 0, 0)), (1.6, (-44, 0, 0)), (2.0, (-30, 0, 0)))
    a.rot("arm_r", (0, (-20, 0, 10)), (0.5, (-50, 0, 70)), (1.6, (-54, 0, 74)), (2.0, (-20, 0, 10)))
    a.rot("arm_l", (0, (-30, 0, -8)), (0.5, (-50, 0, -70)), (1.6, (-54, 0, -74)), (2.0, (-30, 0, -8)))
    a.scale("hump", (0, (1, 1, 1)), (0.5, (1.2, 1.25, 1.2)), (0.8, (1.1, 1.1, 1.1)), (1.1, (1.25, 1.3, 1.25)),
            (1.6, (1.2, 1.25, 1.2)), (2.0, (1, 1, 1)))

    # stagger: the tank sputters, he sinks to one knee, leaning on the staff
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, 5, 0)), (1.6, (0, 5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (26, 0, 0)), (0.3, (46, 0, 6)), (1.6, (48, 0, 6)), (2.0, (26, 0, 0)))
    a.rot("head", (0, (-30, 0, 0)), (0.3, (-10, 0, -10)), (1.6, (-10, 0, -10)), (2.0, (-30, 0, 0)))
    a.scale("hump", (0, (1, 1, 1)), (0.3, (0.9, 0.85, 0.9)), (1.6, (0.9, 0.85, 0.9)), (2.0, (1, 1, 1)))
