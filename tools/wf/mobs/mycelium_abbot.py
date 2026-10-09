"""The Mycelium Abbot (L'Abbé du Mycélium): the champion of the Mycelium Monastery, about 3.4 blocks tall.

Silhouette idea: a steam monk who prayed so long in the spore-dark that the fungal network took him in. A long umber
habit with a brass-trimmed hem, a hempen rope belt and a dark scapular, its skirt eaten away into white mycelium that
trails over the floor in tendrils behind him; a capelet of mycelium felt over his shoulders where little glowing
mushrooms sprout. His hood has grown into a broad brown mushroom cap, wider than his shoulders, its underside lined
with pale gills that glow cyan at the rim. Under it a gaunt, grey-green face with glowing cyan eyes and a beard of
mycelium threads. On his back a small brass reliquary-boiler with a chimney (the steam of the order), and brass censer
chains crossed over his chest. Asymmetry: his RIGHT hand holds a tall crozier of dark wood banded in brass, its crook
curling forward and crowned with a glowing cyan mushroom; from his LEFT hand a brass censer swings on its chain,
spore-light glowing through its vents. Mycelium tendrils hang from his sleeves.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

ROBE = (94, 70, 56)             # the umber habit
ROBE_L = (124, 96, 76)
ROBE_D = (64, 46, 38)
ROBE_DD = (42, 30, 26)
MYC = (206, 196, 208)           # mycelium felt, a violet-white
MYC_L = (236, 230, 238)
MYC_D = (156, 140, 162)
MYC_P = (122, 98, 132)          # the purple of the mycelium block
CAP = (146, 96, 60)             # the brown mushroom cap
CAP_L = (184, 128, 84)
CAP_D = (102, 64, 40)
SPECK = (228, 212, 184)
GILL = (214, 196, 166)
GILL_D = (162, 140, 112)
GLOW = (100, 232, 216)          # bioluminescence
GLOW_L = (206, 255, 248)
GLOW_D = (40, 160, 160)
SKIN = (170, 172, 152)          # grey-green, pallid
SKIN_L = (196, 198, 178)
SKIN_D = (126, 128, 110)
ROPE = (176, 150, 100)
ROPE_D = (128, 104, 64)
WOOD = (70, 46, 32)
WOOD_L = (100, 70, 48)
WOOD_D = (44, 28, 20)


# ---------------------------------------------------------------- paint
def habit(seed=0, eaten=0):
    """The umber habit: coarse vertical weave, darker folds; with ``eaten`` the lowest rows are mycelium."""
    def f(face, x, y, w, h):
        if face == "top":
            return ROBE_D
        if face == "bottom":
            return MYC_D if eaten else ROBE_DD
        if eaten and y >= h - eaten:
            k = y - (h - eaten)
            if B.n(x, y, seed + 7) < 0.25 + k * 0.25:
                return MYC_L if B.n(x, y, seed) > 0.6 else MYC
        if eaten and y >= h - eaten - 2 and B.n(x, y, seed + 9) < 0.18:
            return MYC_D                                                            # threads creeping up
        r = B.n(x, y, seed)
        c = ROBE_L if (x % 4 == 0 and r > 0.55) else (ROBE if r > 0.2 else ROBE_D)
        if x % 5 == 2:
            c = mix(c, ROBE_D, 0.45)                                                # the folds
        return c
    return f


def hem(face, x, y, w, h):
    """The brass-trimmed hem: a band of brass, rivets every third pixel."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    return B.BRASS_L if (y == 0 and x % 3 == 0) else (B.BRASS if y == 0 else B.BRASS_D)


def scapular(face, x, y, w, h):
    if face != "front":
        return ROBE_DD
    if y in (2, 3) and x in (1, w - 2):
        return B.BRASS_L                                                            # a brass sigil
    if y == 3 and 1 <= x <= w - 2:
        return B.BRASS
    return ROBE_D if (x + y) % 4 else ROBE_DD


def rope(face, x, y, w, h):
    return ROPE if (x + y) % 3 else ROPE_D


def felt(seed=0):
    """Mycelium felt: mottled violet-white with purple flecks and threads."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if r < 0.12:
            return MYC_P
        return MYC_L if r > 0.82 else (MYC if r > 0.3 else MYC_D)
    return f


def tendril(face, x, y, w, h):
    return MYC_L if y % 3 == 0 else (MYC if y % 3 == 1 else MYC_D)


def skin(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        return SKIN_L if r > 0.85 else (SKIN if r > 0.2 else SKIN_D)
    return f


def head(face_, x, y, w, h):
    """The face (7 x 7): sunken cheeks, glowing cyan eyes under a heavy brow, a thin mouth in a mycelium beard."""
    if face_ == "front":
        if y == 1:
            return SKIN_D                                                           # the brow
        if y == 2 and x in (1, 5):
            return GLOW                                                             # the eyes
        if y == 2 and x in (2, 4):
            return SKIN_D
        if y in (2, 3) and x == 3:
            return SKIN_L                                                           # the nose
        if y == 4 and x in (1, 5):
            return SKIN_D                                                           # sunken cheeks
        if y >= 5:
            return MYC if (x + y) % 2 else MYC_D                                    # the beard begins
    if face_ in ("left", "right") and y >= 5 and x <= 2:
        return MYC_D
    return skin(11)(face_, x, y, w, h)


def head_glow(face_, x, y, w, h):
    if face_ == "front" and y == 2 and x in (1, 5):
        return GLOW_L
    return None


def beard(face, x, y, w, h):
    """Mycelium threads for a beard, a few glowing spores caught in it."""
    if face == "front" and (x + 2 * y) % 7 == 0:
        return GLOW
    return MYC_L if x % 2 == 0 else (MYC if y % 2 else MYC_D)


def beard_glow(face, x, y, w, h):
    return GLOW_L if face == "front" and (x + 2 * y) % 7 == 0 else None


def cowl(face, x, y, w, h):
    """The cowl of the hood, gone soft and felted where it meets the cap."""
    if y <= 1:
        return MYC_D if (x + y) % 2 else MYC
    return habit(21)(face, x, y, w, h)


def cap(seed=0, gills=False):
    """The brown mushroom cap: a warm umber skin with cream specks; with ``gills`` the underside is radial gills that
    glow at the rim."""
    def f(face, x, y, w, h):
        if face == "bottom" and gills:
            cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
            dx, dy = x - cx, y - cy
            rim = min(x, y, w - 1 - x, h - 1 - y)
            if rim == 0:
                return GLOW
            if rim == 1:
                return GLOW_D if (x + y) % 2 else GILL_D
            line = (abs(dx) < 0.6 or abs(dy) < 0.6 or abs(abs(dx) - abs(dy)) < 0.6
                    or abs(abs(dx) - 2 * abs(dy)) < 0.8 or abs(2 * abs(dx) - abs(dy)) < 0.8)
            return GILL_D if line else GILL
        if face == "bottom":
            return CAP_D
        r = B.n(x, y, seed)
        if face == "top":
            if r > 0.9:
                return SPECK
            return CAP_L if r > 0.6 else CAP
        if y == h - 1 and gills:
            return CAP_D
        if r > 0.93:
            return SPECK
        c = CAP_L if y == 0 else (CAP if r > 0.25 else CAP_D)
        return c
    return f


def cap_glow(face, x, y, w, h):
    if face != "bottom":
        return None
    rim = min(x, y, w - 1 - x, h - 1 - y)
    return GLOW_L if rim == 0 else (GLOW if rim == 1 and (x + y) % 2 else None)


def shroom_cap(face, x, y, w, h):
    """A little bioluminescent mushroom cap."""
    if face == "bottom":
        return GLOW_D
    return GLOW_L if (x + y) % 3 == 0 else GLOW


def shroom_glow(face, x, y, w, h):
    return GLOW_L if face != "bottom" else GLOW


def stalk(face, x, y, w, h):
    return MYC_L if y % 2 else MYC


def wood(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face in ("top", "bottom"):
            return WOOD_D
        c = WOOD_L if (y % 5 == 0 and r > 0.4) else (WOOD if r > 0.2 else WOOD_D)
        return c
    return f


def chain(face, x, y, w, h):
    """Brass censer chain: alternating light and dark links."""
    return B.BRASS_L if (y + x) % 2 == 0 else B.BRASS_D


def censer(face, x, y, w, h):
    """The censer globe: pierced brass, spore-light in the vents."""
    if face in ("top", "bottom"):
        return B.BRASS_D
    if y in (1, 3) and x % 2 == 1:
        return GLOW
    return B.BRASS_L if y == 0 else (B.BRASS if (x + y) % 3 else B.BRASS_D)


def censer_glow(face, x, y, w, h):
    if face not in ("top", "bottom") and y in (1, 3) and x % 2 == 1:
        return GLOW_L
    return None


def chimney(face, x, y, w, h):
    if face == "top":
        return B.SOOT
    return B.BRASS_L if y == 0 else (B.BRASS if x % 2 else B.BRASS_D)


def sandal(face, x, y, w, h):
    if face == "bottom":
        return ROPE_D
    if face == "top" or y == 0:
        return skin(31)(face, x, y, w, h)
    return ROPE_D if x % 2 else ROPE


# ---------------------------------------------------------------- build
def build():
    m = Model("mycelium_abbot", seed=1381, shadow=1.1, walk_speed=0.8, walk_scale=0.7, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -20, 0))
    m.part("skirt", "hips", pivot=(0, 0, 0))
    m.part("trail", "skirt", pivot=(0, 15, 4))
    m.part("chest", "hips", pivot=(0, -1, 0))
    m.part("sash", "chest", pivot=(0, -8, -4.2), rot=(0, 0, 32))
    m.part("pack", "chest", pivot=(0, -9, 3.5))
    m.part("head", "chest", pivot=(0, -15, 0))
    m.part("cap", "head", pivot=(0, -7, 0), rot=(-6, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(2.5 * sx, -20, 0))
    m.part("arm_r", "chest", pivot=(-7.5, -14, 0), rot=(-10, 0, 18))
    m.part("fore_r", "arm_r", pivot=(0, 8, 0), rot=(-34, 0, -4))
    m.part("hand_r", "fore_r", pivot=(0, 8, 0))
    m.part("crozier", "hand_r", pivot=(0, 1.5, -0.5), rot=(44, 0, -12))
    m.part("crook", "crozier", pivot=(0, -27, 0))
    m.part("arm_l", "chest", pivot=(7.5, -14, 0), rot=(-14, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 8, 0), rot=(-46, 0, 4))
    m.part("hand_l", "fore_l", pivot=(0, 8, 0))
    m.part("chain", "hand_l", pivot=(0, 2, -0.5), rot=(60, 0, 0))
    m.part("censer", "chain", pivot=(0, 9, 0))

    # ---- legs: barely seen under the habit, rope sandals on grey feet
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"
        m.box(leg, -2, 0, -2, 4, 17, 4, habit(300 + sx))
        m.box(leg, -2, 17, -3.5, 4, 3, 5, sandal)

    # ---- the habit's skirt, widening, eaten into mycelium at the hem; tendrils trailing behind
    m.box("skirt", -6, -1, -4, 12, 6, 8, habit(310))
    m.box("skirt", -7, 5, -5, 14, 6, 10, habit(311))
    m.box("skirt", -8, 11, -5.5, 16, 6, 11, habit(312, eaten=3))
    m.box("skirt", -8.5, 10, -6, 17, 1, 12, hem)                                        # the brass-trimmed band
    for k, (tx, tz, th) in enumerate(((-7, -5, 2), (-4, -5.5, 3), (2, -5.5, 2), (6, -5, 3), (-7.5, 2, 3),
                                      (7, 1, 2), (-3, 5, 2), (3, 5, 3))):
        m.box("skirt", tx, 17, tz, 1, th, 1, tendril)                                   # threads to the floor
    m.box("trail", -5, 0, 0, 3, 1, 9, felt(313))                                        # tendrils trailing behind
    m.box("trail", 1, 0, 0, 2, 1, 12, felt(314))
    m.box("trail", -1.5, 0, 1, 1, 1, 7, tendril)
    m.box("trail", 4, 0, 0, 2, 1, 6, felt(315))

    # ---- the torso: habit, scapular, rope belt, the mycelium capelet with glowing mushrooms, censer chains
    m.box("chest", -6, -15, -3.5, 12, 15, 7, habit(320))
    m.box("chest", -2.5, -13, -4.2, 5, 13, 1, scapular)
    m.box("chest", -6.5, -2, -4, 13, 2, 8, rope)
    m.box("chest", -4, 0, -4.4, 1, 6, 1, rope)                                          # the belt's tails
    m.box("chest", -2.5, 0, -4.4, 1, 4, 1, rope)
    m.box("chest", -7.5, -16, -4.5, 15, 4, 9, felt(321))                                 # the capelet
    m.box("chest", -6.5, -12, -4.6, 2, 2, 1, felt(322))                                 # felt creeping down
    m.box("chest", 4, -13, 3.6, 3, 4, 1, felt(323))
    for (sx_, sz_, s_) in ((-6, -2, 0), (5, 0, 1), (-4, 2, 1)):
        m.box("chest", sx_, -18, sz_, 1, 2, 1, stalk)                                   # little mushrooms
        m.box("chest", sx_ - 1, -19, sz_ - 1, 3, 1, 3, shroom_cap, glow=shroom_glow)
    m.box("sash", -0.5, -10, -0.5, 1, 20, 1, chain)                                     # chains crossing the chest
    m.box("sash", -1, -1, -0.8, 2, 2, 1, B.brass(324))                                  # their brass clasp

    # ---- on his back: the brass reliquary-boiler with its chimney
    m.box("pack", -3.5, -5, -0.5, 7, 9, 4, B.brass(330, rivet_step=3))
    m.box("pack", -2.5, -3, 3.4, 5, 5, 1, B.lens(core=GLOW, glass=GLOW_L), glow=B.lens_glow(core=GLOW, glass=GLOW_L))
    m.box("pack", 1.5, -11, 1, 2, 6, 2, chimney)
    m.box("pack", -3, -6, 0, 6, 1, 3, B.brass(331))

    # ---- the head: a gaunt face, glowing eyes, a mycelium beard; the cowl; the broad mushroom cap
    m.box("head", -3.5, -7, -3.5, 7, 7, 7, head, glow=head_glow)
    m.box("head", -3, -1, -4.2, 6, 3, 1, beard, glow=beard_glow)
    m.box("head", -2, 2, -4.0, 4, 3, 1, beard, glow=beard_glow)
    m.box("head", -1, 5, -3.8, 2, 2, 1, beard)
    m.box("head", -4.5, -7.5, -3.5, 1, 8, 8, cowl)                                      # the cowl's sides and back
    m.box("head", 3.5, -7.5, -3.5, 1, 8, 8, cowl)
    m.box("head", -4.5, -7.5, 3.5, 9, 9, 1, cowl)
    m.box("cap", -9, -1, -9, 18, 1, 18, cap(340, gills=True), glow=cap_glow)            # the brim, gills under
    m.box("cap", -8, -3, -8, 16, 2, 16, cap(341))                                       # the dome
    m.box("cap", -7, -5, -7, 14, 2, 14, cap(342))
    m.box("cap", -5.5, -7, -5.5, 11, 2, 11, cap(343))
    m.box("cap", -3.5, -8, -3.5, 7, 1, 7, cap(344))
    m.box("cap", -9.5, 0, -6, 1, 2, 2, tendril)                                          # threads off the rim
    m.box("cap", 8.5, 0, 3, 1, 3, 1, tendril)
    m.box("cap", 4, 0, -9.5, 1, 2, 1, tendril)

    # ---- arms: wide bell sleeves with brass cuffs, mycelium tendrils hanging from them; grey hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore, hand = f"arm_{side}", f"fore_{side}", f"hand_{side}"
        m.box(arm, -2.5, -1, -2.5, 5, 9, 5, habit(350 + sx))
        m.box(fore, -3, 0, -3, 6, 8, 6, habit(352 + sx, eaten=2))
        m.box(fore, -3.5, 7, -3.5, 7, 1, 7, hem)
        m.box(fore, 2 * sx, 8, 1, 1, 4, 1, tendril)
        m.box(fore, -1 * sx, 8, 2, 1, 3, 1, tendril)
        m.box(hand, -1.5, 0, -1.5, 3, 3, 3, skin(354 + sx))

    # ---- the crozier: dark wood banded in brass, a brass knop, the crook curling forward, the glowing mushroom
    m.box("crozier", -1, -27, -1, 2, 41, 2, wood(360))
    for y in (-20, -8, 8):
        m.box("crozier", -1.5, y, -1.5, 3, 1, 3, B.brass(361 + y))
    m.box("crozier", -1.5, 13, -1.5, 3, 2, 3, B.brass(364))                             # the ferrule
    m.box("crozier", -2, -29, -2, 4, 3, 4, B.brass(365))                                # the knop
    m.box("crook", -1, -7, -1, 2, 6, 2, wood(366))                                      # the crook rising,
    m.box("crook", -1, -9, -5, 2, 2, 6, wood(367))                                      # curling forward
    m.box("crook", -1, -8, -7, 2, 3, 2, wood(368))
    m.box("crook", -1, -5, -7.5, 2, 3, 2, wood(369))                                    # and down
    m.box("crook", -1.5, -3, -8, 3, 1, 3, B.brass(370))
    m.box("crook", -0.5, -11, -3.5, 1, 2, 1, stalk)                                     # the glowing mushroom
    m.box("crook", -3, -14, -6, 6, 3, 6, shroom_cap, glow=shroom_glow)
    m.box("crook", -2, -15, -5, 4, 1, 4, shroom_cap, glow=shroom_glow)
    m.box("crook", -0.5, -2, -7.5, 1, 2, 1, tendril)                                    # a thread off the tip

    # ---- the censer on its chain
    m.box("chain", -0.5, 0, -0.5, 1, 9, 1, chain)
    m.box("censer", -1.5, -1, -1.5, 3, 1, 3, B.brass(380))                              # the lid
    m.box("censer", -2.5, 0, -2.5, 5, 5, 5, censer, glow=censer_glow)
    m.box("censer", -1.5, 5, -1.5, 3, 1, 3, B.brass(381))
    m.box("censer", -0.5, -2, -0.5, 1, 1, 1, GLOW, glow=GLOW_L)                         # a spore-light finial

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
    REST = {p: m.parts[p].rot for p in ("arm_r", "fore_r", "crozier", "arm_l", "fore_l", "chain", "sash", "cap")}

    idle = _abs(m, m.anim("idle", 4.0))
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.5, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (6, 8, 0)), (2.5, (4, -8, 0)), (4.0, (0, 0, 0)))          # a murmured prayer
    idle.rot("chain", (0, REST["chain"]), (1.0, (68, 0, 8)), (2.0, (60, 0, 0)), (3.0, (68, 0, -8)),
             (4.0, REST["chain"]))
    idle.rot("censer", (0, (0, 0, 0)), (4.0, (0, 360, 0), "linear"))
    idle.rot("trail", (0, (0, 0, 0)), (2.0, (0, 6, 0)), (4.0, (0, 0, 0)))
    idle.scale("crook", (0, (1, 1, 1)), (2.0, (1.03, 1.03, 1.03)), (4.0, (1, 1, 1)))

    walk = _abs(m, m.anim("walk", 2.0))
    walk.rot("leg_r", (0, (20, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (20, 0, 0)))
    walk.rot("leg_l", (0, (-20, 0, 0)), (1.0, (20, 0, 0)), (2.0, (-20, 0, 0)))
    walk.rot("skirt", (0, (4, 0, 2)), (1.0, (4, 0, -2)), (2.0, (4, 0, 2)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -0.6, 0)), (1.0, (0, 0, 0)), (1.5, (0, -0.6, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (4, 4, 0)), (1.0, (4, -4, 0)), (2.0, (4, 4, 0)))
    walk.rot("trail", (0, (0, 8, 0)), (1.0, (0, -8, 0)), (2.0, (0, 8, 0)))
    walk.rot("chain", (0, (70, 0, 0)), (1.0, (50, 0, 0)), (2.0, (70, 0, 0)))

    # crozier (14 / 14 / 16): the crozier drawn back over his right shoulder (0.7 s), swept round his front at 0.7 s,
    # lifted high and brought down overhead at 1.2 s (the slam down the line), then lowered
    a = _abs(m, m.anim("crozier", 2.2))
    a.rot("arm_r", (0, REST["arm_r"]), (0.6, (-120, 50, 40)), (0.7, (-122, 52, 40)), (0.8, (-70, -60, -20), "linear"),
          (1.0, (-170, 0, 0)), (1.1, (-172, 0, 0)), (1.2, (-60, 0, 0), "linear"), (1.5, (-56, 0, 0)), (2.2, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.7, (-20, 0, 0)), (1.1, (-10, 0, 0)), (1.2, (0, 0, 0)), (2.2, REST["fore_r"]))
    a.rot("crozier", (0, REST["crozier"]), (0.7, (80, 0, 0)), (1.1, (90, 0, 0)), (1.2, (90, 0, 0)), (2.2, REST["crozier"]))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (0, 30, 0)), (0.8, (0, -26, 0), "linear"), (1.1, (-10, 0, 0)),
          (1.2, (20, 0, 0), "linear"), (1.5, (18, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (0, -16, 0)), (1.2, (10, 0, 0)), (2.2, (0, 0, 0)))

    # censer (18 / 16 / 14): the censer swung back on its chain, the chain wound round his fist (0.9 s); from 0.9 s he
    # swings it across his front from right to left, trailing the spore cloud (0.8 s), then lets it settle
    a = _abs(m, m.anim("censer", 2.4))
    a.rot("arm_l", (0, REST["arm_l"]), (0.8, (-70, -70, -20)), (0.9, (-72, -72, -20)), (1.3, (-90, 0, 0)),
          (1.7, (-70, 70, 20)), (2.4, REST["arm_l"]))
    a.rot("fore_l", (0, REST["fore_l"]), (0.9, (-20, 0, 0)), (1.7, (-20, 0, 0)), (2.4, REST["fore_l"]))
    a.rot("chain", (0, REST["chain"]), (0.8, (40, 0, -60)), (0.9, (40, 0, -64)), (1.3, (100, 0, 0), "linear"),
          (1.7, (40, 0, 70), "linear"), (2.0, (80, 0, 10)), (2.4, REST["chain"]))
    a.rot("censer", (0, (0, 0, 0)), (0.9, (0, 90, 0)), (1.7, (0, 540, 0)), (2.4, (0, 720, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, 34, 0)), (1.3, (0, 0, 0)), (1.7, (0, -34, 0)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (0, -20, 0)), (1.7, (0, 20, 0)), (2.4, (0, 0, 0)))

    # tendrils (26 / 10 / 14): he raises the crozier in both hands, chanting, the trail of mycelium stirring (1.3 s), and
    # drives its butt into the floor at 1.3 s: the tendrils erupt
    a = _abs(m, m.anim("tendrils", 2.5))
    a.rot("arm_r", (0, REST["arm_r"]), (1.1, (-150, 0, 10)), (1.3, (-156, 0, 10)), (1.36, (-40, 0, 10), "linear"),
          (1.8, (-40, 0, 10)), (2.5, REST["arm_r"]))
    a.rot("crozier", (0, REST["crozier"]), (1.1, (40, 0, 0)), (1.3, (40, 0, 0)), (1.36, (60, 0, 0)), (2.5, REST["crozier"]))
    a.rot("arm_l", (0, REST["arm_l"]), (1.1, (-140, 0, -40)), (1.3, (-144, 0, -40)), (1.36, (-50, 0, -10), "linear"),
          (1.8, (-50, 0, -10)), (2.5, REST["arm_l"]))
    a.rot("chest", (0, (0, 0, 0)), (1.3, (-12, 0, 0)), (1.36, (16, 0, 0), "linear"), (1.8, (14, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.3, (-24, 0, 0)), (1.36, (10, 0, 0), "linear"), (2.5, (0, 0, 0)))
    a.rot("trail", (0, (0, 0, 0)), (0.4, (-10, 20, 0)), (0.8, (-10, -20, 0)), (1.3, (-16, 0, 0)), (1.36, (6, 0, 0)),
          (2.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.3, (0, 1, 0)), (1.36, (0, -2, 0), "linear"), (1.8, (0, -2, 0)), (2.5, (0, 0, 0)))

    # crook (16 / 8 / 16): the crozier levelled at you, the crook hooked outward (0.8 s); it snaps forward at 0.8 s and
    # he hauls it back
    a = _abs(m, m.anim("crook", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.7, (-60, 20, 20)), (0.8, (-62, 22, 20)), (0.86, (-96, 0, 0), "linear"),
          (1.2, (-40, 10, 10)), (2.0, REST["arm_r"]))
    a.rot("crozier", (0, REST["crozier"]), (0.7, (110, 0, 0)), (0.86, (96, 0, 0), "linear"), (1.2, (80, 0, 0)),
          (2.0, REST["crozier"]))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (0, 20, 0)), (0.86, (10, -10, 0), "linear"), (1.2, (-6, 10, 0)), (2.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.8, (0, 0, 1)), (0.86, (0, 0, -2), "linear"), (1.2, (0, 0, 1)), (2.0, (0, 0, 0)))

    # pods (phase 2, 20 / 10 / 16): he kneels and sows spores from the censer over the floor (1.0 s), then lifts both
    # hands: the pods sprout
    a = _abs(m, m.anim("pods", 2.3))
    a.pos("hips", (0, (0, 0, 0)), (0.5, (0, -4, 0)), (1.0, (0, -4, 0)), (1.2, (0, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.0, (-40, 0, 0)), (1.2, (0, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (-60, 0, -40)), (0.6, (-60, 0, 40)), (1.0, (-60, 0, -40)),
          (1.1, (-150, 0, -30)), (1.8, (-150, 0, -30)), (2.3, REST["arm_l"]))
    a.rot("chain", (0, REST["chain"]), (0.3, (60, 0, -40)), (0.6, (60, 0, 40)), (1.0, (60, 0, -40)),
          (1.1, (160, 0, 0)), (1.8, (160, 0, 0)), (2.3, REST["chain"]))
    a.rot("arm_r", (0, REST["arm_r"]), (1.0, REST["arm_r"]), (1.1, (-150, 0, 30)), (1.8, (-150, 0, 30)),
          (2.3, REST["arm_r"]))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (1.0, (24, 0, 0)), (1.1, (-10, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (14, 0, 0)), (1.1, (-26, 0, 0)), (2.3, (0, 0, 0)))

    # monks (phase 2, 20 / 10 / 16): he rings the censer high over his head, calling the brothers (1.0 s), and spreads
    # his arms at 1.0 s
    a = _abs(m, m.anim("monks", 2.3))
    a.rot("arm_l", (0, REST["arm_l"]), (0.4, (-170, 0, -10)), (1.0, (-172, 0, -10)), (1.06, (-60, 0, -80), "linear"),
          (1.8, (-60, 0, -80)), (2.3, REST["arm_l"]))
    a.rot("chain", (0, REST["chain"]), (0.4, (170, 0, 0)), (0.6, (170, 0, 30)), (0.8, (170, 0, -30)), (1.0, (170, 0, 0)),
          (1.06, (60, 0, 0)), (2.3, REST["chain"]))
    a.rot("arm_r", (0, REST["arm_r"]), (1.0, REST["arm_r"]), (1.06, (-60, 0, 80), "linear"), (1.8, (-60, 0, 80)),
          (2.3, REST["arm_r"]))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.8, (-20, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.8, (-8, 0, 0)), (2.3, (0, 0, 0)))

    # communion (phase 3, 40 / 20 / 20): he sinks to his knees, arms wide, the cap's gills blazing, the trail spreading
    # over the floor (2.0 s); at 2.0 s the network answers: he flings his arms up and the mushroom ring blooms out
    a = _abs(m, m.anim("communion", 4.0))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -6, 0)), (2.0, (0, -6, 0)), (2.06, (0, 1, 0), "linear"), (2.6, (0, 0, 0)),
          (4.0, (0, 0, 0)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"leg_{s}", (0, (0, 0, 0)), (1.0, (-70, 0, 0)), (2.0, (-70, 0, 0)), (2.06, (0, 0, 0)), (4.0, (0, 0, 0)))
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.0, (-50, 0, 80 * sz)), (2.0, (-56, 0, 84 * sz)),
              (2.06, (-170, 0, 20 * sz), "linear"), (3.2, (-166, 0, 22 * sz)), (4.0, REST[f"arm_{s}"]))
    a.rot("head", (0, (0, 0, 0)), (2.0, (20, 0, 0)), (2.06, (-30, 0, 0), "linear"), (3.2, (-26, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("cap", (0, (1, 1, 1)), (2.0, (1.25, 1.1, 1.25)), (2.06, (1.35, 1.15, 1.35), "linear"), (3.2, (1.1, 1.05, 1.1)),
            (4.0, (1, 1, 1)))
    a.scale("trail", (0, (1, 1, 1)), (2.0, (1.6, 1, 1.6)), (3.2, (1.4, 1, 1.4)), (4.0, (1, 1, 1)))

    # burrow (phase 3, 20 / 40 / 16): he sinks straight down into the floor, the cap last (1.0 s); hidden underground
    # while the ring hunts you; at 2.5 s he bursts up out of the floor under it, arms flung up, and settles
    a = _abs(m, m.anim("burrow", 3.8))
    a.pos("bone", (0, (0, 0, 0)), (0.3, (0, -2, 0)), (1.0, (0, -60, 0)), (2.45, (0, -60, 0)), (2.5, (0, -40, 0)),
          (2.65, (0, 2, 0), "linear"), (3.0, (0, 0, 0)), (3.8, (0, 0, 0)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (0.3, (-40, 0, 40 * sz)), (1.0, (-170, 0, 10 * sz)),
              (2.5, (-170, 0, 10 * sz)), (2.65, (-150, 0, 40 * sz)), (3.2, (-120, 0, 30 * sz)), (3.8, REST[f"arm_{s}"]))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (2.65, (-24, 0, 0)), (3.8, (0, 0, 0)))
    a.scale("trail", (0, (1, 1, 1)), (1.0, (2.0, 1, 2.0)), (2.5, (0.5, 1, 0.5)), (3.0, (1.6, 1, 1.6)), (3.8, (1, 1, 1)))

    # roar (phase two): head thrown back, both arms raised, the crozier and the censer lifted, the cap swelling
    a = _abs(m, m.anim("roar", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.5, (-150, 0, 30)), (1.6, (-154, 0, 30)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.5, (-150, 0, -30)), (1.6, (-154, 0, -30)), (2.0, REST["arm_l"]))
    a.rot("chain", (0, REST["chain"]), (0.5, (150, 0, 0)), (1.0, (150, 0, 30)), (1.6, (150, 0, -20)), (2.0, REST["chain"]))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-12, 0, 0)), (1.6, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("cap", (0, (1, 1, 1)), (0.5, (1.2, 1.1, 1.2)), (1.6, (1.15, 1.1, 1.15)), (2.0, (1, 1, 1)))

    # stagger: he sags onto the crozier, one knee down, the cap drooping over his face
    a = _abs(m, m.anim("stagger", 2.0))
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -5, 0)), (1.6, (0, -5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.6, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (28, 0, 8)), (1.6, (30, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (30, 0, -12)), (1.6, (30, 0, -12)), (2.0, (0, 0, 0)))
    a.rot("cap", (0, REST["cap"]), (0.3, (14, 0, -10)), (1.6, (14, 0, -10)), (2.0, REST["cap"]))
    a.rot("arm_r", (0, REST["arm_r"]), (0.3, (-50, 0, 10)), (1.6, (-50, 0, 10)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (-10, 0, -20)), (1.6, (-10, 0, -20)), (2.0, REST["arm_l"]))
