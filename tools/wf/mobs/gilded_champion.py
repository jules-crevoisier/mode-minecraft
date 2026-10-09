"""The Gilded Champion (Le Champion doré): the champion of the Crimson Colosseum, about 4 blocks tall.

Silhouette idea: the undefeated piglin gladiator, a massive brute broader in the shoulders than a door. A crested
gladiator's helmet of gold (cheek guards, a brim, a tall crimson horsehair crest running front to back and a tail of
it down the nape) over a piglin's head: the flat snout, floppy ears hanging out under the cheek guards, small fierce
eyes and two tusks capped in gold. Ornate gilded plate: a muscle cuirass with a gorget, layered pauldrons, a segmented
manica down the sword arm, gilded greaves and knee cops, a skirt of crimson pteruges tipped in gold over a gold belt
hung with chains of trophies (small skulls, a dented helmet, gold coins). A crimson cape falls from the shoulders. In
the right hand a huge gladius of netherite edged in gold (a gold guard and pommel); on the left forearm a round gilded
shield with a hoglin skull for its boss.

Variants: "plain", and "gilded" for phase 3 (the emperor's favour): the gold glows, the shield is cast aside (its
cubes paint nothing) and a second gladius (painted nothing in the plain variant) is drawn in the left hand.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

VARIANTS = ["plain", "gilded"]

GOLD = (226, 178, 66)
GOLD_L = (255, 226, 128)
GOLD_D = (158, 110, 34)
GOLD_DD = (98, 64, 20)
NETH = (70, 62, 64)
NETH_L = (108, 98, 100)
NETH_D = (40, 34, 36)
CRIM = (156, 26, 36)
CRIM_L = (204, 52, 56)
CRIM_D = (94, 14, 24)
PIG = (224, 150, 138)
PIG_L = (242, 182, 168)
PIG_D = (178, 106, 100)
SNOUT = (236, 166, 152)
TUSK = (242, 234, 208)
BONE = (228, 216, 186)
BONE_D = (172, 158, 126)
LEATHER = (108, 62, 36)
LEATHER_D = (68, 38, 22)
EYE = (34, 20, 18)
EMBER = (255, 210, 90)
CHAIN = (72, 72, 82)
CHAIN_L = (120, 122, 134)


def hidden(face, x, y, w, h):
    return None


# ---------------------------------------------------------------- paint
def make_paint(variant):
    gilded = variant == "gilded"
    g = (1.12 if gilded else 1.0)

    def gold(seed=0, emboss="rim"):
        """Polished gold plate: a lit top row, a darker rim, a soft vertical gradient (brighter when gilded)."""
        base = mul(GOLD, g)
        hi = mul(GOLD_L, g)
        rim = GOLD_D

        def f(face, x, y, w, h):
            if face == "bottom":
                return GOLD_D
            if face == "top":
                return hi if (x + y) % 5 == 0 else base
            if emboss == "rim" and w > 2 and h > 2:
                if y == 0:
                    return hi
                if x in (0, w - 1) or y == h - 1:
                    return rim
            if emboss == "bands" and y % 3 == 2:
                return rim if x % 4 else hi
            k = 1.0 + 0.2 * (0.5 - y / max(1, h)) + (B.n(x, y, seed) - 0.5) * 0.08
            return mul(base, k)
        return f

    def gold_glow(face, x, y, w, h):
        """The gilded rage: the plate's edges and seams glow."""
        if not gilded or face == "bottom":
            return None
        if face != "top" and w > 2 and h > 2 and (y == 0 or x in (0, w - 1)):
            return GOLD_L
        if B.n(x, y, 77) > 0.86:
            return EMBER
        return None

    def cuirass(face, x, y, w, h):
        """The muscle cuirass: embossed pectorals and abdominal ridges on the front, a gold rim, plain plate behind."""
        base = mul(GOLD, g)
        if face == "front":
            cx = (w - 1) / 2
            if y == 0 or y == h - 1:
                return GOLD_D
            if abs(x - cx) < 0.6:
                return GOLD_D                                                          # the median line
            if y in (4, 5) and 2 <= abs(x - cx) <= 7:
                return GOLD_D if y == 5 else mul(GOLD_L, g)                            # under the pectorals
            if y in (8, 11) and 1 <= abs(x - cx) <= 4:
                return GOLD_D                                                          # abdominal ridges
            if y in (7, 10) and 1 <= abs(x - cx) <= 4:
                return mul(GOLD_L, g)
            if y < 4 and 2 <= abs(x - cx) <= 7 and (x + y) % 6 == 0:
                return mul(GOLD_L, g)
            return mul(base, 1.0 + 0.16 * (0.5 - y / h) + (B.n(x, y, 3) - 0.5) * 0.06)
        return gold(5)(face, x, y, w, h)

    def tunic(seed=0):
        def f(face, x, y, w, h):
            r = B.n(x, y // 2, seed)
            if face == "bottom":
                return CRIM_D
            return CRIM_L if r > 0.82 else (CRIM if r > 0.25 else CRIM_D)
        return f

    def cape(seed=0, ragged=False):
        """The crimson cape: folds running down, a gold border along the sides, ragged at the hem."""
        def f(face, x, y, w, h):
            if ragged and y >= h - 3 and B.n(x, 0, seed) * 3 < y - (h - 4):
                return None
            if face in ("front", "back") and (x in (0, w - 1)):
                return GOLD_D if face == "back" else CRIM_D
            fold = (x // 3) % 2
            c = CRIM if fold else CRIM_D
            if face == "back" and x % 3 == 1:
                c = CRIM_L if fold else CRIM
            return mul(c, 1.0 - 0.15 * (y / max(1, h)))
        return f

    def pteruges(face, x, y, w, h):
        """Leather strips of the skirt, crimson-dyed, gold-tipped."""
        if y >= h - 2:
            return mul(GOLD_L, g) if y == h - 2 else GOLD_D
        return CRIM_D if (x + y) % 5 == 0 else (CRIM if y % 4 else LEATHER)

    def belt(face, x, y, w, h):
        if face == "front" and abs(x - (w - 1) / 2) < 2.5:
            return mul(GOLD_L, g) if (x + y) % 2 else GOLD_D                           # the boar buckle
        if face in ("top", "bottom"):
            return LEATHER_D
        if y == 1 and x % 3 == 0:
            return mul(GOLD_L, g)                                                      # gold studs
        return mul(GOLD, g) if y != 1 else LEATHER

    def skin(seed=0):
        def f(face, x, y, w, h):
            r = B.n(x, y, seed)
            if face == "bottom":
                return PIG_D
            return PIG_L if r > 0.85 else (PIG if r > 0.2 else PIG_D)
        return f

    def head_face(face, x, y, w, h):
        """The piglin face (12 wide): heavy brows, small fierce eyes (embers when gilded)."""
        if face != "front":
            return skin(41)(face, x, y, w, h)
        if y == 4 and x in (1, 2, 3, 4, 7, 8, 9, 10):
            return PIG_D
        if y == 5 and x in (2, 3, 8, 9):
            return (250, 246, 236) if x in (2, 9) else (EMBER if gilded else EYE)
        return skin(42)(face, x, y, w, h)

    def eye_glow(face, x, y, w, h):
        if gilded and face == "front" and y == 5 and x in (3, 8):
            return EMBER
        return None

    def snout(face, x, y, w, h):
        if face == "front":
            if y in (1, 2) and x in (1, 2, w - 3, w - 2):
                return PIG_D if y == 1 else (120, 60, 58)                              # the nostrils
            return SNOUT if (x + y) % 4 else PIG_L
        return mix(SNOUT, PIG_D, 0.3) if face == "bottom" else SNOUT

    def tusk(face, x, y, w, h):
        return TUSK if B.n(x, y, 51) > 0.2 else BONE_D

    def ear(seed):
        def f(face, x, y, w, h):
            if face in ("left", "right") and 1 <= x <= w - 2 and 1 <= y <= h - 2:
                return PIG_D if B.n(x, y, seed) > 0.5 else mix(PIG, PIG_D, 0.5)        # the inside of the ear
            return skin(seed)(face, x, y, w, h)
        return f

    def helm(face, x, y, w, h):
        """The helmet's bowl: gold with a raised band and a row of rivets low on it."""
        if face == "top":
            return mul(GOLD_L, g) if x in (w // 2, w // 2 - 1) else mul(GOLD, g)
        if y == h - 2:
            return mul(GOLD_L, g) if x % 3 == 1 else GOLD_D
        if y == h - 1:
            return GOLD_DD
        return gold(31, emboss="none")(face, x, y, w, h)

    def crest(face, x, y, w, h):
        """Horsehair crest: crimson strands, the top edge ragged."""
        if face == "top":
            return CRIM_L if x % 2 else CRIM
        if face in ("left", "right") and y == 0 and B.n(x, 0, 61) > 0.5:
            return None
        r = B.n(x // 1, y // 2, 62)
        return CRIM_L if r > 0.75 else (CRIM if r > 0.3 else CRIM_D)

    def manica(face, x, y, w, h):
        """The segmented arm armour: overlapping gold lames with dark gaps."""
        if face in ("top", "bottom"):
            return GOLD_D
        if y % 3 == 2:
            return GOLD_DD
        return mul(GOLD_L, g) if y % 3 == 0 else mul(GOLD, g)

    def bracer(face, x, y, w, h):
        if face in ("top", "bottom"):
            return LEATHER_D
        if y in (0, h - 1):
            return mul(GOLD, g)
        return LEATHER if (x + y) % 4 else LEATHER_D

    def glove(face, x, y, w, h):
        return LEATHER if (x + y) % 4 else LEATHER_D

    def sabaton(face, x, y, w, h):
        """Netherite boots with a gold toe cap."""
        if face == "bottom":
            return NETH_D
        if face == "front" and y >= h - 3:
            return mul(GOLD, g) if y < h - 1 else GOLD_D
        if y == 0:
            return mul(GOLD, g)
        return NETH if B.n(x, y, 71) > 0.3 else NETH_D

    def wraps(face, x, y, w, h):
        return LEATHER_D if (y + x // 2) % 3 == 0 else LEATHER

    def neth_blade(face, x, y, w, h):
        """The gladius blade: dark netherite with a bright fuller down the middle."""
        if face in ("front", "back"):
            return NETH_L if x == w // 2 else (NETH if (x + y) % 7 else NETH_D)
        return NETH_D

    def edge(face, x, y, w, h):
        return mul(GOLD_L, g) if y % 4 else mul(GOLD, g)

    def grip(face, x, y, w, h):
        return LEATHER_D if y % 2 == 0 else CRIM_D

    def chain(face, x, y, w, h):
        return CHAIN_L if y % 2 == 0 else CHAIN

    def skull(face, x, y, w, h):
        """A little trophy skull (piglin): sockets on the front."""
        if face == "front" and y == 1 and x in (0, w - 1):
            return EYE
        return BONE if B.n(x, y, 81) > 0.25 else BONE_D

    def coin(face, x, y, w, h):
        return mul(GOLD_L, g) if (x + y) % 2 == 0 else GOLD

    def shield_row(yc, wid):
        """One row of the round shield: concentric gold rim, a dark band, a crimson field with gold rays."""
        def f(face, x, y, w, h):
            if face == "back":
                return LEATHER if (x + y) % 5 else LEATHER_D                           # the leather lining
            if face != "front":
                return GOLD_D
            gx = x - wid / 2 + 0.5
            gy = yc - 1 + y + 0.5
            r = math.hypot(gx, gy)
            if r > 9.4:
                return mul(GOLD_L, g) if (int(math.degrees(math.atan2(gy, gx))) // 20) % 2 else GOLD_D
            if r > 8.3:
                return mul(GOLD, g)
            if r > 7.4:
                return GOLD_DD
            if r > 3.6:
                ang = math.degrees(math.atan2(gy, gx)) % 45
                if ang < 7:
                    return mul(GOLD, g)                                                 # gold rays
                return CRIM if B.n(x, y + yc, 91) > 0.25 else CRIM_D
            return mul(GOLD_L, g) if r < 2.2 else GOLD
        return f

    def shield_glow(face, x, y, w, h):
        return None

    def hog_skull(face, x, y, w, h):
        """The hoglin skull boss: bone, dark eye sockets, a gold band across the brow."""
        if face == "front" and y == 1 and x in (1, w - 2):
            return EYE
        if face == "front" and y == 0:
            return mul(GOLD, g)
        return BONE if B.n(x, y, 93) > 0.3 else BONE_D

    def hog_snout(face, x, y, w, h):
        if face == "front" and y == 1 and x in (0, w - 1):
            return EYE
        return BONE_D if (x + y) % 3 == 0 else BONE

    return {
        "gold": gold, "gold_glow": gold_glow, "cuirass": cuirass, "tunic": tunic, "cape": cape, "pteruges": pteruges,
        "belt": belt, "skin": skin, "head_face": head_face, "eye_glow": eye_glow, "snout": snout, "tusk": tusk,
        "ear": ear, "helm": helm, "crest": crest, "manica": manica, "bracer": bracer, "glove": glove,
        "sabaton": sabaton, "wraps": wraps, "neth_blade": neth_blade, "edge": edge, "grip": grip, "chain": chain,
        "skull": skull, "coin": coin, "shield_row": shield_row, "shield_glow": shield_glow, "hog_skull": hog_skull,
        "hog_snout": hog_snout,
    }


def gladius(m, part, P, show=True):
    """A huge gladius from the fist (the part's pivot) upward: grip, gold guard and pommel, a netherite blade edged in
    gold, a leaf point."""
    def v(p):
        return p if show else hidden
    G = P["gold"]
    glow = P["gold_glow"] if show else None
    m.box(part, -1, -3, -1, 2, 6, 2, v(P["grip"]))                                     # the grip
    m.box(part, -1.5, 3, -1.5, 3, 3, 3, v(G(101)), glow=glow)                          # the pommel
    m.box(part, -4, -5, -2, 8, 2, 4, v(G(102)), glow=glow)                             # the guard
    m.box(part, -1.5, -30, -1, 3, 25, 2, v(P["neth_blade"]))                           # the blade
    m.box(part, -2.5, -29, -0.5, 1, 24, 1, v(P["edge"]), glow=glow)                    # its gold edges
    m.box(part, 1.5, -29, -0.5, 1, 24, 1, v(P["edge"]), glow=glow)
    m.box(part, -1.5, -33, -0.5, 3, 3, 1, v(P["edge"]), glow=glow)                     # the point
    m.box(part, -0.5, -35, -0.5, 1, 2, 1, v(P["edge"]), glow=glow)
    m.box(part, -1, -8, -1.5, 2, 2, 3, v(G(103)), glow=glow)                           # the ricasso collar


# ---------------------------------------------------------------- build
def build(variant=None):
    variant = variant or "plain"
    gilded = variant == "gilded"
    P = make_paint(variant)
    G = P["gold"]
    GG = P["gold_glow"]
    m = Model("gilded_champion", seed=1307, shadow=1.5, walk_speed=0.7, walk_scale=0.8, variants=VARIANTS,
              glow_pulse=0.08)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -22, 0))
    m.part("trophies", "hips", pivot=(0, -1, 0))
    m.part("chest", "hips", pivot=(0, -3, 0))
    m.part("head", "chest", pivot=(0, -23, -1))
    m.part("crest", "head", pivot=(0, -13, 0))
    m.part("cape", "chest", pivot=(0, -21, 7.5), rot=(8, 0, 0))
    m.part("cape_lo", "cape", pivot=(0, 22, 0), rot=(4, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(5.5 * sx, -22, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 11, 0))
        m.part(f"ear_{side}", "head", pivot=(6.2 * sx, -7, -1), rot=(0, 0, -40 * sx))
    m.part("arm_r", "chest", pivot=(-14.5, -18, 0), rot=(-10, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 11, 0), rot=(-40, 0, 0))
    m.part("gladius", "fore_r", pivot=(0, 11.5, 0), rot=(95, 0, 0))
    m.part("arm_l", "chest", pivot=(14.5, -18, 0), rot=(-14, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 11, 0), rot=(-50, 0, 0))
    m.part("shield", "fore_l", pivot=(2, 6, -5), rot=(64, 0, 12))
    m.part("gladius2", "fore_l", pivot=(0, 11.5, 0), rot=(110, 0, 0))

    # ---- legs: bare thighs, gold knee cops and greaves over leather wraps, netherite sabatons
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -4, -1, -4, 8, 12, 8, P["skin"](10 + sx))
        m.box(shin, -3.5, 0, -3.5, 7, 7, 7, P["wraps"])
        m.box(shin, -4, 0, -4.6, 8, 8, 2, G(12 + sx), glow=GG)                         # the greave
        m.box(shin, -3, -2, -5, 6, 3, 2, G(14 + sx, emboss="bands"), glow=GG)          # the knee cop
        m.box(shin, -4.5, 7, -5.5, 9, 4, 10, P["sabaton"])
        m.box(shin, -4, 8, -7, 8, 3, 2, P["sabaton"])                                  # the toe

    # ---- hips: the gold belt, the skirt of crimson pteruges tipped in gold
    m.box("hips", -10, -3, -6, 20, 6, 12, P["tunic"](20))
    m.box("hips", -10.5, -3, -6.5, 21, 3, 13, P["belt"])
    for i, x in enumerate(range(-9, 9, 3)):
        m.box("hips", x, 0, -6.8, 2, 8, 1, P["pteruges"])                              # front strips
        m.box("hips", x, 0, 5.8, 2, 8, 1, P["pteruges"])                               # back strips
    for sx in (-1, 1):
        for z in (-4, -1, 2):
            m.box("hips", 9.8 if sx > 0 else -10.8, 0, z, 1, 7, 2, P["pteruges"])     # side strips

    # ---- trophies hanging from the belt: chains with little skulls, a dented helmet and coins
    for x, kind in ((-8.5, "skull"), (-5.5, "coins"), (7.5, "helm"), (10.0, "skull")):
        z = -7.2 if x < 9 else -3.0
        m.box("trophies", x, -1, z, 1, 5, 1, P["chain"])
        if kind == "skull":
            m.box("trophies", x - 1, 4, z - 1, 3, 3, 3, P["skull"])
        elif kind == "coins":
            m.box("trophies", x - 1, 4, z - 0.5, 3, 1, 2, P["coin"])
            m.box("trophies", x - 0.5, 5, z - 0.5, 2, 1, 2, P["coin"])
        else:
            m.box("trophies", x - 1.5, 4, z - 1.5, 4, 3, 4, G(111))                   # a small looted helmet
            m.box("trophies", x - 0.5, 3, z - 0.5, 2, 1, 2, P["crest"])

    # ---- the torso: crimson tunic under the muscle cuirass, gorget, layered pauldrons
    m.box("chest", -11, -20, -7, 22, 20, 14, P["tunic"](21))
    m.box("chest", -11.5, -20, -7.5, 23, 15, 15, P["cuirass"], glow=GG)
    m.box("chest", -10, -6, -8.2, 20, 4, 1, G(22, emboss="bands"), glow=GG)           # the belly lames
    m.box("chest", -7, -23, -6, 14, 3, 12, G(23, emboss="bands"), glow=GG)            # the gorget
    for sx in (-1, 1):
        x0 = -18 if sx < 0 else 11
        m.box("chest", x0, -24, -5.5, 7, 5, 11, G(24 + sx), glow=GG)                  # the pauldrons
        m.box("chest", x0 - 0.5 if sx < 0 else x0 + 0.5, -20, -5, 7, 3, 10, G(26 + sx, emboss="bands"), glow=GG)
        m.box("chest", x0 + 1, -25, -2, 5, 1, 4, P["crest"])                           # a crimson plume tuft
    m.box("chest", -9, -22, 6.5, 3, 3, 2, G(28), glow=GG)                              # the cape's clasps
    m.box("chest", 6, -22, 6.5, 3, 3, 2, G(29), glow=GG)

    # ---- the cape
    m.box("cape", -10, 0, 0, 20, 22, 1, P["cape"](31))
    m.box("cape_lo", -10, 0, 0, 20, 10, 1, P["cape"](32, ragged=True))

    # ---- the head: piglin face and snout, gold-capped tusks, the crested gladiator helmet, floppy ears
    m.box("head", -6, -10, -6, 12, 10, 10, P["head_face"], glow=P["eye_glow"])
    m.box("head", -3.5, -5, -9, 7, 4, 3, P["snout"])
    m.box("head", -5, -1, -6.5, 10, 2, 6, P["skin"](43))                               # the heavy jaw
    for sx in (-1, 1):
        x = 3.5 if sx > 0 else -4.5
        m.box("head", x, -3, -8.5, 1, 3, 1, P["tusk"])                                 # the tusks
        m.box("head", x, -5, -8.5, 1, 2, 1, G(44 + sx), glow=GG)                      # their gold caps
    m.box("head", -6.5, -13, -6.5, 13, 5, 13, P["helm"], glow=GG)                     # the bowl
    m.box("head", -7.5, -8, -7.5, 15, 1, 15, G(45, emboss="none"), glow=GG)           # the brim
    for sx in (-1, 1):
        m.box("head", 6.5 if sx > 0 else -7.5, -8, -6.5, 1, 6, 7, G(46 + sx), glow=GG)  # the cheek guards
    m.box("head", -2.5, -10, -7.5, 5, 2, 1, G(48), glow=GG)                           # a brow plate
    m.box("crest", -1, -2, -5, 2, 2, 11, G(49), glow=GG)                               # the crest holder
    m.box("crest", -1.5, -7, -7, 3, 5, 15, P["crest"])                                 # the horsehair crest
    m.box("crest", -1, -2, 7, 2, 9, 2, P["crest"])                                     # its tail down the nape
    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"ear_{side}", -0.5 if sx > 0 else -0.5, 0, -2.5, 1, 7, 5, P["ear"](52 + sx))

    # ---- arms: the sword arm in a gold manica, the shield arm bare with a bracer
    m.box("arm_r", -4, -2, -4, 8, 13, 8, P["manica"], glow=GG)
    m.box("fore_r", -3.5, 0, -3.5, 7, 10, 7, P["manica"], glow=GG)
    m.box("fore_r", -3, 9, -3, 6, 4, 6, P["glove"])
    m.box("arm_l", -4, -2, -4, 8, 13, 8, P["skin"](61))
    m.box("arm_l", -4.5, -3, -4.5, 9, 4, 9, G(62, emboss="bands"), glow=GG)           # a gold arm ring
    m.box("fore_l", -3.5, 0, -3.5, 7, 10, 7, P["bracer"])
    m.box("fore_l", -3, 9, -3, 6, 4, 6, P["glove"])

    # ---- the gladius (right hand) and the second one (left hand, gilded only)
    gladius(m, "gladius", P, show=True)
    gladius(m, "gladius2", P, show=gilded)

    # ---- the round shield (cast aside when gilded): rows of a disc r 10, the hoglin skull boss
    def sv(p):
        return hidden if gilded else p
    for yc in range(-9, 11, 2):
        wid = max(4, 2 * int(round(math.sqrt(100 - yc * yc))))
        m.box("shield", -wid / 2, yc - 1, -1, wid, 2, 2, sv(P["shield_row"](yc, wid)))
    m.box("shield", -3, -3, -4, 6, 5, 3, sv(P["hog_skull"]))
    m.box("shield", -2, -1, -6, 4, 3, 2, sv(P["hog_snout"]))
    for sx in (-1, 1):
        m.box("shield", 2.5 if sx > 0 else -3.5, -1, -6.5, 1, 4, 1, sv(P["tusk"]))    # the skull's tusks
        m.box("shield", 3 if sx > 0 else -5, -4, -3, 2, 2, 2, sv(P["hog_skull"]))     # its little ears

    _anims(m)
    return m


R_ARM = (-10, 0, 10)
R_FORE = (-40, 0, 0)
R_GLAD = (95, 0, 0)
L_GLAD = (110, 0, 0)
L_ARM = (-14, 0, -12)
L_FORE = (-50, 0, 0)
Z = (0, 0, 0)


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, Z), (1.5, (0, 0.6, 0)), (3.0, Z))
    idle.rot("head", (0, Z), (1.5, (2, -8, 0)), (3.0, Z))
    idle.rot("ear_r", (0, Z), (0.8, (0, 0, -6)), (1.6, (0, 0, 4)), (3.0, Z))
    idle.rot("ear_l", (0, Z), (1.0, (0, 0, 6)), (1.9, (0, 0, -4)), (3.0, Z))
    idle.rot("cape", (0, Z), (1.5, (3, 0, 0)), (3.0, Z))
    idle.rot("cape_lo", (0, Z), (1.7, (5, 0, 0)), (3.0, Z))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("shin_r", (0, Z), (0.5, (18, 0, 0)), (1.0, Z), (2.0, Z))
    walk.rot("shin_l", (0, Z), (1.0, Z), (1.5, (18, 0, 0)), (2.0, Z))
    walk.pos("hips", (0, Z), (0.5, (0, -1.2, 0)), (1.0, Z), (1.5, (0, -1.2, 0)), (2.0, Z))
    walk.rot("chest", (0, (0, 5, 2)), (1.0, (0, -5, -2)), (2.0, (0, 5, 2)))
    walk.rot("cape", (0, (10, 0, 0)), (1.0, (14, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("trophies", (0, (6, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (6, 0, 0)))

    # combo (16 / 18 / 14): the gladius drawn back over his right shoulder (0.8 s); a forehand cut across his front at
    # 0.8 s, the backhand return at 1.2 s, and (phase 2) the thrust at 1.6 s; recovers by 2.4 s
    a = m.anim("combo", 2.4)
    a.rot("arm_r", (0, R_ARM), (0.7, (-120, 50, 60)), (0.8, (-122, 52, 60)), (0.86, (-80, -50, 10), "linear"),
          (1.1, (-84, -60, 0)), (1.2, (-90, 40, 40), "linear"), (1.45, (-60, 10, 10)), (1.6, (-95, 0, 6), "linear"),
          (1.85, (-92, 0, 6)), (2.4, R_ARM))
    a.rot("fore_r", (0, R_FORE), (0.8, (-30, 0, 0)), (0.86, (-10, 0, 0), "linear"), (1.45, (-40, 0, 0)),
          (1.6, (0, 0, 0), "linear"), (1.85, (0, 0, 0)), (2.4, R_FORE))
    a.rot("gladius", (0, R_GLAD), (0.8, (100, 0, 0)), (0.86, (115, 0, 0), "linear"), (1.45, (115, 0, 0)),
          (1.6, (170, 0, 0), "linear"), (1.85, (170, 0, 0)), (2.4, R_GLAD))
    a.rot("gladius2", (0, L_GLAD), (0.8, (90, 0, 0)), (0.86, (130, 0, 0), "linear"), (2.4, L_GLAD))
    a.rot("arm_l", (0, L_ARM), (0.8, (-60, -30, -50)), (0.86, (-80, 40, 0), "linear"), (1.45, (-70, 30, 0)),
          (2.4, L_ARM))
    a.rot("chest", (0, Z), (0.8, (-4, 34, 0)), (0.86, (6, -24, 0), "linear"), (1.1, (6, -30, 0)),
          (1.2, (4, 22, 0), "linear"), (1.45, (0, 6, 0)), (1.6, (10, -8, 0), "linear"), (1.85, (10, -8, 0)), (2.4, Z))
    a.pos("bone", (0, Z), (0.8, (0, 0, 1)), (0.86, (0, 0, -3)), (1.6, (0, 0, -6)), (1.85, (0, 0, -6)), (2.4, Z))
    a.rot("leg_r", (0, Z), (0.8, (10, 0, 0)), (1.6, (-18, 0, 0)), (2.4, Z))
    a.rot("leg_l", (0, Z), (0.8, (-8, 0, 0)), (1.6, (20, 0, 0)), (2.4, Z))

    # bash (14 / 8 / 16): the shield drawn back to the left (0.7 s), slammed forward at 0.7 s with his whole weight
    a = m.anim("bash", 1.9)
    a.rot("arm_l", (0, L_ARM), (0.6, (-40, -50, -40)), (0.7, (-42, -52, -40)), (0.76, (-80, 20, -6), "linear"),
          (1.1, (-80, 20, -6)), (1.9, L_ARM))
    a.rot("fore_l", (0, L_FORE), (0.7, (-70, 0, 0)), (0.76, (-20, 0, 0), "linear"), (1.1, (-20, 0, 0)), (1.9, L_FORE))
    a.rot("chest", (0, Z), (0.7, (-6, -30, 0)), (0.76, (14, 20, 0), "linear"), (1.1, (12, 16, 0)), (1.9, Z))
    a.pos("bone", (0, Z), (0.7, (0, 0, 2)), (0.76, (0, 0, -5), "linear"), (1.1, (0, 0, -5)), (1.9, Z))
    a.rot("leg_l", (0, Z), (0.7, (8, 0, 0)), (0.76, (-26, 0, 0), "linear"), (1.1, (-26, 0, 0)), (1.9, Z))
    a.rot("leg_r", (0, Z), (0.76, (18, 0, 0), "linear"), (1.1, (18, 0, 0)), (1.9, Z))

    # block (12 / 40 / 12): the shield raised before his face (0.6 s), held there 2 s, the gladius cocked behind it
    # ready to riposte; lowered by 3.2 s
    a = m.anim("block", 3.2)
    a.rot("arm_l", (0, L_ARM), (0.6, (-70, 30, -10)), (2.6, (-70, 30, -10)), (3.2, L_ARM))
    a.rot("fore_l", (0, L_FORE), (0.6, (-60, 0, 0)), (2.6, (-60, 0, 0)), (3.2, L_FORE))
    a.rot("arm_r", (0, R_ARM), (0.6, (-40, 30, 40)), (2.6, (-40, 30, 40)), (3.2, R_ARM))
    a.rot("gladius", (0, R_GLAD), (0.6, (60, 0, 0)), (2.6, (60, 0, 0)), (3.2, R_GLAD))
    a.rot("chest", (0, Z), (0.6, (8, -10, 0)), (1.6, (8, -8, 0)), (2.6, (8, -10, 0)), (3.2, Z))
    a.pos("hips", (0, Z), (0.6, (0, -2, 0)), (2.6, (0, -2, 0)), (3.2, Z))
    a.rot("leg_l", (0, Z), (0.6, (-24, 0, 0)), (2.6, (-24, 0, 0)), (3.2, Z))
    a.rot("leg_r", (0, Z), (0.6, (20, 0, 0)), (2.6, (20, 0, 0)), (3.2, Z))
    a.rot("head", (0, Z), (0.6, (10, 0, 0)), (2.6, (10, 0, 0)), (3.2, Z))

    # riposte (10 / 6 / 14): out from behind the shield, the gladius driven straight ahead at 0.5 s
    a = m.anim("riposte", 1.5)
    a.rot("arm_r", (0, (-40, 30, 40)), (0.45, (-30, 40, 30)), (0.5, (-95, 0, 6), "linear"), (0.8, (-92, 0, 6)),
          (1.5, R_ARM))
    a.rot("fore_r", (0, R_FORE), (0.45, (-60, 0, 0)), (0.5, (0, 0, 0), "linear"), (0.8, Z), (1.5, R_FORE))
    a.rot("gladius", (0, (60, 0, 0)), (0.45, (80, 0, 0)), (0.5, (170, 0, 0), "linear"), (0.8, (170, 0, 0)),
          (1.5, R_GLAD))
    a.rot("arm_l", (0, (-70, 30, -10)), (0.5, (-30, -20, -30)), (1.5, L_ARM))
    a.rot("chest", (0, (8, -10, 0)), (0.45, (0, 20, 0)), (0.5, (12, -16, 0), "linear"), (0.8, (12, -16, 0)), (1.5, Z))
    a.pos("bone", (0, Z), (0.5, (0, 0, -6), "linear"), (0.8, (0, 0, -6)), (1.5, Z))

    # charge (24 / 16 / 14): he lowers his helmet behind the shield and paws the sand (1.2 s), then tackles down the
    # lane from 1.2 s to 2.0 s, legs pumping; skids to a stop by 2.7 s
    a = m.anim("charge", 2.7)
    a.rot("chest", (0, Z), (1.0, (26, 0, 0)), (1.2, (30, 0, 0)), (2.0, (32, 0, 0)), (2.7, Z))
    a.rot("head", (0, Z), (1.2, (-14, 0, 0)), (2.0, (-14, 0, 0)), (2.7, Z))
    a.rot("arm_l", (0, L_ARM), (1.0, (-80, 10, -6)), (2.0, (-80, 10, -6)), (2.7, L_ARM))
    a.rot("arm_r", (0, R_ARM), (1.0, (-10, 0, 40)), (2.0, (-10, 0, 40)), (2.7, R_ARM))
    a.rot("leg_r", (0, Z), (0.3, (-20, 0, 0)), (0.5, (10, 0, 0)), (0.7, (-20, 0, 0)), (0.9, (10, 0, 0)),
          (1.2, (-30, 0, 0)), (1.4, (40, 0, 0)), (1.6, (-40, 0, 0)), (1.8, (40, 0, 0)), (2.0, (-30, 0, 0)), (2.7, Z))
    a.rot("leg_l", (0, Z), (1.2, (30, 0, 0)), (1.4, (-40, 0, 0)), (1.6, (40, 0, 0)), (1.8, (-40, 0, 0)),
          (2.0, (30, 0, 0)), (2.7, Z))
    a.rot("cape", (0, Z), (1.2, (20, 0, 0)), (1.4, (60, 0, 0)), (2.0, (60, 0, 0)), (2.7, Z))

    # net (20 / 10 / 16): a weighted gold net pulled from his belt and whirled overhead (1.0 s), flung at 1.0 s
    a = m.anim("net", 2.3)
    a.rot("arm_l", (0, L_ARM), (0.3, (-60, 0, -30)), (0.5, (-170, 0, -20)), (0.75, (-170, 40, -30)),
          (1.0, (-160, -40, -20)), (1.06, (-70, 0, -10), "linear"), (1.5, (-70, 0, -10)), (2.3, L_ARM))
    a.rot("chest", (0, Z), (1.0, (-10, -20, 0)), (1.06, (10, 14, 0), "linear"), (1.5, (8, 10, 0)), (2.3, Z))
    a.rot("arm_r", (0, R_ARM), (1.0, (-20, 0, 24)), (2.3, R_ARM))

    # crowd (22 / 30 / 16): the taunt: gladius and shield raised to the stands, head thrown back (1.1 s), holding the
    # pose while the crowd hurls its debris (1.5 s)
    a = m.anim("crowd", 3.4)
    a.rot("arm_r", (0, R_ARM), (0.6, (-170, 0, 24)), (1.1, (-176, 0, 30)), (1.4, (-160, 0, 20)), (1.8, (-176, 0, 30)),
          (2.6, (-176, 0, 30)), (3.4, R_ARM))
    a.rot("arm_l", (0, L_ARM), (0.6, (-150, 0, -40)), (1.1, (-160, 0, -40)), (2.6, (-160, 0, -40)), (3.4, L_ARM))
    a.rot("head", (0, Z), (0.6, (-28, 0, 0)), (1.1, (-32, 10, 0)), (1.8, (-32, -10, 0)), (2.6, (-30, 0, 0)), (3.4, Z))
    a.rot("chest", (0, Z), (1.1, (-14, 0, 0)), (2.6, (-12, 0, 0)), (3.4, Z))

    # gates (phase 2, 20 / 10 / 16): the gladius beaten on the shield three times (1.0 s), then pointed at a gate
    a = m.anim("gates", 2.3)
    a.rot("arm_r", (0, R_ARM), (0.2, (-80, -30, 10)), (0.35, (-50, -40, 0)), (0.5, (-80, -30, 10)), (0.65, (-50, -40, 0)),
          (0.8, (-80, -30, 10)), (1.0, (-50, -40, 0)), (1.06, (-90, 30, 20), "linear"), (1.6, (-90, 30, 20)),
          (2.3, R_ARM))
    a.rot("arm_l", (0, L_ARM), (0.2, (-60, 20, -10)), (1.0, (-60, 20, -10)), (2.3, L_ARM))
    a.rot("head", (0, Z), (1.06, (-10, -20, 0)), (1.6, (-10, -20, 0)), (2.3, Z))

    # favour (phase 3, 40 / 20 / 20): he kneels to the royal box and raises the gladius in salute while the gold takes
    # fire (2.0 s), then rises and slams it into the sand at 2.0 s
    a = m.anim("favour", 4.0)
    a.pos("hips", (0, Z), (0.6, (0, -6, 0)), (1.8, (0, -6, 0)), (2.0, (0, 1, 0)), (2.06, (0, -2, 0), "linear"),
          (3.2, (0, -2, 0)), (4.0, Z))
    a.rot("leg_r", (0, Z), (0.6, (-80, 0, 0)), (1.8, (-80, 0, 0)), (2.0, (-20, 0, 0)), (3.2, (-20, 0, 0)), (4.0, Z))
    a.rot("shin_r", (0, Z), (0.6, (80, 0, 0)), (1.8, (80, 0, 0)), (2.0, (20, 0, 0)), (4.0, Z))
    a.rot("leg_l", (0, Z), (0.6, (10, 0, 0)), (1.8, (10, 0, 0)), (2.0, (20, 0, 0)), (4.0, Z))
    a.rot("shin_l", (0, Z), (0.6, (80, 0, 0)), (1.8, (80, 0, 0)), (2.0, (10, 0, 0)), (4.0, Z))
    a.rot("arm_r", (0, R_ARM), (0.6, (-176, 0, 10)), (1.9, (-178, 0, 10)), (2.0, (-180, 0, 6)),
          (2.06, (-70, 0, 6), "linear"), (3.2, (-70, 0, 6)), (4.0, R_ARM))
    a.rot("gladius", (0, R_GLAD), (0.6, (180, 0, 0)), (2.0, (180, 0, 0)), (2.06, (150, 0, 0), "linear"), (3.2, (150, 0, 0)), (4.0, R_GLAD))
    a.rot("head", (0, Z), (0.6, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.06, (14, 0, 0), "linear"), (4.0, Z))
    a.rot("chest", (0, Z), (0.6, (-10, 0, 0)), (2.0, (-12, 0, 0)), (2.06, (24, 0, 0), "linear"), (3.2, (20, 0, 0)),
          (4.0, Z))

    # roar (phase two): the gladius thrust to the stands, the crowd answers
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, Z), (0.5, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.5, (-32, 0, 0)), (1.6, (-30, 0, 0)), (2.0, Z))
    a.rot("arm_r", (0, R_ARM), (0.5, (-172, 0, 16)), (1.6, (-174, 0, 18)), (2.0, R_ARM))
    a.rot("arm_l", (0, L_ARM), (0.5, (-60, 0, -60)), (1.6, (-64, 0, -64)), (2.0, L_ARM))
    a.rot("ear_r", (0, Z), (0.5, (0, 0, -30)), (1.6, (0, 0, -30)), (2.0, Z))
    a.rot("ear_l", (0, Z), (0.5, (0, 0, 30)), (1.6, (0, 0, 30)), (2.0, Z))

    # stagger: winded, he drops to one knee behind his shield, head hanging
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, Z), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.3, (-60, 0, 0)), (1.6, (-60, 0, 0)), (2.0, Z))
    a.rot("shin_r", (0, Z), (0.3, (70, 0, 0)), (1.6, (70, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, Z))
    a.rot("shin_l", (0, Z), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, Z))
    a.rot("chest", (0, Z), (0.3, (28, 0, 6)), (1.6, (30, 0, 6)), (2.0, Z))
    a.rot("head", (0, Z), (0.3, (30, 0, -8)), (1.6, (30, 0, -8)), (2.0, Z))
    a.rot("arm_r", (0, R_ARM), (0.3, (-20, 0, 30)), (1.6, (-20, 0, 30)), (2.0, R_ARM))
