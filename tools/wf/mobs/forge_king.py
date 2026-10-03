"""The Forge King (Le Roi-Forgeron): a colossal dwarf king, about 3.8 blocks tall and nearly 3 wide.

Silhouette idea: an anvil of a body. A crowned, horned helm (one horn broken) sunk between enormous
layered pauldrons, a huge silver beard braided with gold rings hanging to the knees, a crimson cloak
under a fur mantle, a red-hot war hammer (emissive head) planted at his right and a real anvil strapped
to his left forearm as a shield. Molten seams glow between the plates of his armour.
"""
import math

from ..models import Model
from ..texgen import mix, mul

# ---------------------------------------------------------------- palette
IRON = (70, 72, 82)
IRON_D = (40, 40, 48)
IRON_L = (122, 124, 136)
STEEL = (92, 96, 108)
GOLD = (226, 176, 62)
GOLD_D = (150, 98, 30)
GOLD_L = (255, 226, 132)
SKIN = (192, 124, 96)
SKIN_D = (140, 82, 66)
BEARD = (228, 224, 216)
BEARD_M = (190, 186, 178)
BEARD_D = (128, 122, 118)
EMBER = (255, 132, 36)
EMBER_D = (214, 64, 18)
HOT = (255, 214, 120)
WHITE_HOT = (255, 246, 210)
CRIMSON = (132, 26, 30)
CRIMSON_D = (78, 14, 20)
FUR = (84, 62, 46)
FUR_L = (126, 98, 72)
FUR_D = (52, 38, 30)
WOOD = (88, 58, 36)
WOOD_D = (58, 36, 22)
LEATHER = (96, 60, 38)
CHAIN = (88, 90, 100)
CHAIN_D = (44, 44, 52)


def _n(x, y, seed):
    """Deterministic hash noise in [0, 1)."""
    r = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF
    return (r % 1000) / 1000.0


# ---------------------------------------------------------------- paint helpers
def plate(base=IRON, rim=IRON_D, hi=IRON_L, rivet=None, seed=0, grad=0.22, rivet_step=0):
    """An armour plate: lit top edge, dark rim, vertical light gradient, faint hammer marks, rivets."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return mul(base, 0.75)
        if face == "top":
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                return mix(base, hi, 0.55)
            if rivet and w > 5 and h > 5 and x in (1, w - 2) and y in (1, h - 2):
                return rivet
            if w > 7 and x == w // 2:
                return mix(base, hi, 0.3)               # raised spine
            return mul(base, 1.1 - 0.12 * (y / max(1, h)) + (_n(x, y, seed) - 0.5) * 0.05)
        if w > 2 and h > 2:
            if y == 0:
                return hi
            if x == 0 or x == w - 1 or y == h - 1:
                return rim
        if rivet and w > 4 and h > 4:
            if y in (1 + 0, h - 2) and (x in (1, w - 2) or (rivet_step and x % rivet_step == 1)):
                return rivet
        k = 1 + grad * (0.5 - y / max(1, h)) + (_n(x, y, seed) - 0.5) * 0.06
        c = mul(base, k)
        if _n(x // 2, y // 2, seed + 3) < 0.05:
            c = mul(c, 0.86)  # hammer dent
        return c
    return f


def lames(rows, base=IRON, seam_c=IRON_D, seed=0):
    """Horizontal armour lames: every `rows` texels a dark seam (the glow layer lights them)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(base, 1.05 if face == "top" else 0.75)
        if y % rows == rows - 1:
            return seam_c
        k = 1.12 - 0.3 * ((y % rows) / rows) + (_n(x, y, seed) - 0.5) * 0.05
        return mul(base, k)
    return f


def lame_glow(rows, colour=EMBER, gap=0):
    """Molten light leaking through some lame seams, in irregular runs (never a neon stripe)."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom") or y % rows != rows - 1:
            return None
        k = _n(x // 3, y, rows + gap)
        if k < 0.35:
            return None
        return HOT if k > 0.9 else colour if k > 0.55 else EMBER_D
    return f


def chainmail(seed=0):
    def f(face, x, y, w, h):
        ring = (x + (y % 2)) % 2 == 0
        c = CHAIN if ring else CHAIN_D
        if ring and y % 2 == 0:
            c = mix(CHAIN, IRON_L, 0.35)
        return mul(c, 1 - 0.25 * (y / max(1, h)))
    return f


def fur(seed=0, ragged=True):
    """Thick fur: vertical tufts of three tones, light tips, dark roots, ragged hem."""
    def f(face, x, y, w, h):
        clump = x // 2
        drop = int(_n(clump, 1, seed) * 3)
        if ragged and face not in ("top", "bottom") and y >= h - drop:
            return None
        if face == "top":
            return FUR_L if _n(x, y, seed) < 0.5 else FUR
        off = int(_n(clump, 2, seed) * 4)
        layer = (y + off) % 5            # staggered overlapping tufts: lit tip, body, dark root
        c = (FUR_L, mix(FUR_L, FUR, 0.5), FUR, FUR, FUR_D)[layer]
        if x % 2 == 1:
            c = mul(c, 0.85)
        return mul(c, 1.1 - 0.35 * (y / max(1, h)))
    return f


def beard_strands(seed=0, ragged=True, shade_top=True):
    """Silver beard: long wavy locks four texels wide (lit edge, two mid tones, shadow), pointed tips."""
    def f(face, x, y, w, h):
        if face == "top":
            return BEARD_M
        if face == "bottom":
            return BEARD_D
        wave = int(round(1.0 * math.sin(y * 0.25 + seed)))
        lock = (x + wave) // 4
        pos = (x + wave) % 4
        if ragged:
            tip = h - 1 - int(_n(lock, 7, seed) * 3.5)
            if y > tip or (y == tip and pos in (0, 3)):
                return None
        c = (BEARD, BEARD, BEARD_M, mix(BEARD_M, BEARD_D, 0.7))[pos]
        if shade_top and y < 2:
            c = mul(c, 0.85)
        return mul(c, 1.02 - 0.12 * (y / max(1, h)))
    return f


def braid(seed=0):
    """A plait: alternating chevrons of light and shadow."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return BEARD_M
        k = (y + (x if (y // 2) % 2 else w - x)) % 4
        return (BEARD, BEARD_M, BEARD_D, BEARD_M)[k]
    return f


def gold_ring():
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return GOLD_L if face == "top" else GOLD_D
        if y == 0:
            return GOLD_L
        if y == h - 1:
            return GOLD_D
        return GOLD if x % 3 else mix(GOLD, GOLD_L, 0.5)
    return f


def gold_trim():
    return plate(GOLD, GOLD_D, GOLD_L, seed=5, grad=0.3)


def hot_metal():
    """Glow of the red-hot hammer head: white-hot striking faces, the long sides a dark crust split by
    glowing cracks that brighten toward the faces."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            cx, cy = (w - 1) / 2, (h - 1) / 2
            d = max(abs(x - cx) / max(1, cx), abs(y - cy) / max(1, cy)) + (_n(x, y, 11) - 0.5) * 0.25
            return WHITE_HOT if d < 0.4 else HOT if d < 0.65 else EMBER if d < 0.88 else EMBER_D
        # sides: heat creeps in from both ends (u = 0 and u = 1 are the striking faces)
        u = x / max(1, w - 1) if face in ("left", "right") else y / max(1, h - 1)
        v = y if face in ("left", "right") else x
        edge = min(u, 1 - u)
        crack = (v + int(3 * math.sin(u * 9 + v))) % 5 == 0 or _n(x, y, 13) < 0.08
        if edge < 0.16:
            return HOT if edge < 0.07 else EMBER
        if crack:
            return EMBER if edge < 0.3 else EMBER_D
        return None
    return f


def hot_paint():
    """Under the glow: scorched, blackened iron with a red sheen."""
    def f(face, x, y, w, h):
        return mul(mix(IRON_D, EMBER_D, 0.28), 0.9 + _n(x, y, 17) * 0.2)
    return f


def cloak(seed=0):
    """Crimson royal cloak: gold border, a hammer-and-anvil sigil on the back, tattered hem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom", "left", "right"):
            return CRIMSON_D
        if y >= h - 1 - int(_n(x // 2, 9, seed) * 4):
            return None
        if face == "front":
            return mul(CRIMSON_D, 0.85)
        # face == back: the visible outside of the cloak
        if x in (1, w - 2) or y == 1:
            return GOLD
        if x in (0, w - 1) or y == 0:
            return GOLD_D
        c = mul(CRIMSON, 1.0 - 0.35 * (y / h) + (0.06 if (x // 3) % 2 else -0.04))
        # sigil: hammer over an anvil, centred
        cx = w // 2
        u, v = x - cx, y - 8
        if -1 <= u <= 0 and 0 <= v <= 12:
            return GOLD                         # haft
        if -4 <= u <= 3 and 0 <= v <= 3:
            return GOLD_L if v == 0 else GOLD   # hammer head
        if -6 <= u <= 5 and 14 <= v <= 15:
            return GOLD                         # anvil face
        if -2 <= u <= 1 and 16 <= v <= 18:
            return GOLD_D
        if -5 <= u <= 4 and v == 19:
            return GOLD
        return c
    return f


# ---------------------------------------------------------------- the model
FORE_R = -22      # rest pitch of the right forearm (the fist forward)
HAM_R = 22        # rest pitch of the hammer, cancelling the forearm: the haft stands upright


def build():
    m = Model("forge_king", seed=35, shadow=1.7, walk_speed=0.9, walk_scale=1.0)

    # ------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -13, 0))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=(5, 0, 0))
    m.part("head", "torso", pivot=(0, -27, -5))
    m.part("horn_r", "head", pivot=(-8, -13, 0), rot=(0, 15, 20))
    m.part("horn_r2", "horn_r", pivot=(-6, 0, 0), rot=(0, 0, 40))
    m.part("horn_r3", "horn_r2", pivot=(-5, 0, 0), rot=(0, -25, 40))
    m.part("horn_l", "head", pivot=(8, -13, 0), rot=(0, -15, -20))
    m.part("horn_l2", "horn_l", pivot=(6, 0, 0), rot=(0, 0, -40))
    m.part("beard", "head", pivot=(0, -3, -8))
    m.part("braid_r", "beard", pivot=(-6, 13, 0))
    m.part("braid_c", "beard", pivot=(0, 17, 0))
    m.part("braid_l", "beard", pivot=(6, 13, 0))
    m.part("cape", "torso", pivot=(0, -27, 10), rot=(6, 0, 0))
    m.part("arm_r", "torso", pivot=(-18, -23, 0), rot=(0, 0, 14))
    m.part("forearm_r", "arm_r", pivot=(-0.5, 11, 0), rot=(FORE_R, 0, 0))
    m.part("hammer", "forearm_r", pivot=(-0.5, 13, -0.5), rot=(HAM_R, 0, -16))
    m.part("arm_l", "torso", pivot=(18, -23, 0), rot=(0, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0.5, 11, 0), rot=(-15, 0, 0))
    m.part("shield", "forearm_l", pivot=(6, 4, 0))
    m.part("leg_r", "bone", pivot=(-7, -13, 0))
    m.part("shin_r", "leg_r", pivot=(0, 6, 0))
    m.part("leg_l", "bone", pivot=(7, -13, 0))
    m.part("shin_l", "leg_l", pivot=(0, 6, 0))

    # ------------------------------------------------------------ hips: belt, mail skirt, tassets
    m.box("hips", -13, -5, -10, 26, 5, 19, {"front": lambda f_, x, y, w, h: GOLD_L if y == 0 else GOLD_D if y == h - 1
                                             else LEATHER if (x // 2) % 3 else mul(LEATHER, 0.8),
                                             "*": plate(LEATHER, mul(LEATHER, 0.6), mix(LEATHER, GOLD, 0.4), seed=1)})
    m.box("hips", -4, -6, -12, 8, 7, 2, {"front": lambda f_, x, y, w, h: GOLD_D if x in (0, w - 1) or y in (0, h - 1)
                                          else EMBER if (x in (3, 4) and 2 <= y <= 4) else GOLD,
                                          "*": GOLD_D},
          glow={"front": lambda f_, x, y, w, h: HOT if (x in (3, 4) and 2 <= y <= 4) else None})  # buckle, a forge-eye
    m.box("hips", -12, 0, -8, 24, 7, 16, chainmail())
    for x0 in (-12, 1):
        m.box("hips", x0, 0, -11, 11, 8, 2, plate(STEEL, IRON_D, GOLD, rivet=GOLD_L, seed=2))
    for s in (-1, 1):
        m.box("hips", -14 if s < 0 else 12, 0, -7, 2, 7, 14, plate(STEEL, IRON_D, GOLD, seed=3))

    # ------------------------------------------------------------ torso: barrel belly, breastplate, mantle
    m.box("torso", -14, -13, -10, 28, 13, 19, {"side": lames(5, IRON, IRON_D, seed=4), "top": IRON, "bottom": IRON_D},
          glow={"side": lame_glow(5, EMBER, gap=4)})
    breast = plate(IRON, IRON_D, IRON_L, rivet=GOLD_L, seed=5, rivet_step=5)

    def breast_front(f_, x, y, w, h):
        if y >= h - 2:
            return GOLD if y == h - 2 else GOLD_D         # gilded lower rim
        if x in (3, w - 4) and 1 <= y < h - 2:
            return GOLD_D                               # panel lines
        if x in (2, w - 3) and 2 <= y < h - 3:
            return EMBER_D                              # molten seam
        return breast(f_, x, y, w, h)
    m.box("torso", -16, -28, -11, 32, 16, 20, {"front": breast_front, "*": breast},
          glow={"front": lambda f_, x, y, w, h: EMBER if x in (2, w - 3) and 2 <= y < h - 3 else None})
    m.box("torso", -10, -31, -9, 20, 4, 16, plate(STEEL, IRON_D, GOLD_L, seed=6))    # gorget
    # fur mantle over the shoulders, rising behind the head like a collar
    m.box("torso", -19, -33, -4, 38, 7, 14, fur(1))
    m.box("torso", -13, -38, 2, 26, 6, 9, fur(2))

    # ------------------------------------------------------------ head: face, helm, crown, horns
    def face(f_, x, y, w, h):
        if y == 5 and x in (3, 4, 9, 10):
            return EMBER                                # glowing ember eyes
        if y == 5 and x in (2, 5, 8, 11):
            return (46, 24, 20)
        if y == 4 or (y == 5 and x in (6, 7)):
            return mul(SKIN_D, 0.75)                    # heavy brow shadow
        if y == 6 and x in (2, 3, 4, 5, 8, 9, 10, 11):
            return SKIN_D                               # under-eye folds
        return mul(SKIN, 1.04 - 0.03 * (y - 6))
    m.box("head", -7, -13, -7, 14, 13, 12, {"front": face, "*": SKIN_D},
          glow={"front": lambda f_, x, y, w, h: (HOT if x in (4, 9) else EMBER) if y == 5 and x in (3, 4, 9, 10) else None})
    m.box("head", -1.5, -8, -9, 3, 5, 2, {"*": SKIN, "bottom": SKIN_D,
                                           "front": lambda f_, x, y, w, h: mul(SKIN, 1.12 - 0.07 * y)})   # nose
    m.box("head", -8, -18, -8, 16, 8, 14, plate(IRON, IRON_D, IRON_L, rivet=GOLD_L, seed=7, rivet_step=3))  # helm
    m.box("head", -9, -11, -9, 18, 2, 16, gold_ring())                                                     # brow band
    m.box("head", -9, -9, -6, 2, 8, 10, plate(STEEL, IRON_D, IRON_L, rivet=GOLD_L, seed=8))               # cheek guards
    m.box("head", 7, -9, -6, 2, 8, 10, plate(STEEL, IRON_D, IRON_L, rivet=GOLD_L, seed=9))
    # crown: a gold band with tall points around a forge-gem
    m.box("head", -6, -21, -6, 12, 3, 11, plate(IRON, IRON_D, IRON_L, rivet=GOLD_L, seed=11))              # dome
    for bx, bz, bw, bd in ((-8.5, -8.5, 17, 1), (-8.5, 5.5, 17, 1), (-8.5, -7.5, 1, 13), (7.5, -7.5, 1, 13)):
        m.box("head", bx, -20, bz, bw, 2, bd, gold_ring())                                                  # crown band
    pts = ((-1, -9, 7, 2), (-5, -9, 5, 2), (3, -9, 5, 2), (-9, -4, 4, 1), (8, -4, 4, 1),
           (-9, 2, 5, 1), (8, 2, 5, 1), (-1, 5, 4, 2))
    for x, z, hgt, wd in pts:
        side = abs(x) >= 8
        m.box("head", x, -20 - hgt, z, wd if not side else 1, hgt, 1 if not side else 2,
              {"*": GOLD, "top": GOLD_L, "left": GOLD_D, "right": GOLD_D,
               "front": lambda f_, x_, y_, w_, h_: GOLD_L if y_ == 0 else GOLD})
        tz = z if not side else z + 0.5
        tx = x + 0.5 if not side else x
        m.box("head", tx, -22 - hgt, tz, 1, 2, 1, {"*": GOLD_L})
    m.box("head", -1.5, -25, -10, 3, 3, 1, EMBER, glow={"front": lambda f_, x, y, w, h: WHITE_HOT if x == 1 and y == 1 else HOT,
                                                          "*": EMBER})
    # horns: the right one curls up and forward, the left is broken off short
    def horn(seed):
        return lambda f_, x, y, w, h: (130, 112, 86) if (x + seed) % 3 == 0 else \
            mix((228, 214, 180), (160, 138, 104), (x / max(1, w)) * 0.7)
    m.box("horn_r", -6, -3, -3, 6, 6, 6, horn(0))
    m.box("horn_r2", -5, -2.5, -2.5, 5, 5, 5, horn(1))
    m.box("horn_r3", -6, -2, -2, 6, 4, 4, horn(2))
    m.box("horn_r3", -9, -1, -1, 3, 2, 2, (238, 228, 200))
    m.box("horn_l", 0, -3, -3, 6, 6, 6, horn(0))
    m.box("horn_l2", 0, -2.5, -2.5, 3, 5, 5, {"*": horn(1),
                                              "left": lambda f_, x, y, w, h: (96, 80, 60) if (x + y) % 2 else (176, 156, 124)})

    # ------------------------------------------------------------ beard: moustache, a vast mass, three braids ringed in gold
    m.box("beard", -10, -2, -4, 20, 3, 4, beard_strands(1, ragged=False, shade_top=False))
    m.box("beard", -9, 1, -3, 18, 11, 5, beard_strands(2))
    m.box("beard", -7, 0, -4, 14, 9, 1, beard_strands(3))
    m.box("beard", -7, 11, -3, 14, 7, 4, beard_strands(4))
    m.box("beard", -4, 17, -2, 8, 3, 3, beard_strands(5))
    m.part("whisk_r", "beard", pivot=(-9, 0, -1), rot=(0, 0, 18))
    m.part("whisk_l", "beard", pivot=(9, 0, -1), rot=(0, 0, -18))
    m.box("whisk_r", -4, -1, -2, 5, 10, 4, beard_strands(6))     # flaring side wings
    m.box("whisk_l", -1, -1, -2, 5, 10, 4, beard_strands(7))
    for part, n, wdt in (("braid_r", 10, 4), ("braid_c", 13, 5), ("braid_l", 10, 4)):
        o = -wdt / 2
        m.box(part, o, 0, o, wdt, n, wdt, braid(len(part)))
        for k in range(2, n - 1, 5):
            m.box(part, o - 0.5, k, o - 0.5, wdt + 1, 2, wdt + 1, gold_ring())
        m.box(part, o + 0.5, n, o + 0.5, wdt - 1, 3, wdt - 1, beard_strands(9))

    # ------------------------------------------------------------ cloak
    m.box("cape", -15, 0, 0, 30, 37, 1, cloak(3))

    # ------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        o = 1 if sx > 0 else -1      # pauldrons sit a little outward
        # pauldron: a gold-bossed dome over three lames that flare outward
        m.box(arm, -5 + o, -10, -6, 10, 3, 12, plate(GOLD, GOLD_D, GOLD_L, seed=20 + sx))
        m.box(arm, -7 + o, -7, -8, 14, 4, 16, plate(IRON, IRON_D, IRON_L, rivet=GOLD_L, seed=21 + sx, rivet_step=4))
        m.box(arm, -8 + o, -3, -8, 16, 4, 16, {"side": lames(4, STEEL, IRON_D, 22), "*": STEEL},
              glow={"side": lame_glow(4, EMBER, gap=3)})
        m.box(arm, -8 + o, 1, -7, 16, 3, 14, {"side": lambda f_, x, y, w, h: GOLD_L if y == 0 else GOLD if y == 1 else GOLD_D,
                                               "*": GOLD})
        m.box(arm, -4.5, 3, -4.5, 9, 9, 9, chainmail(24))
        # gauntlet: a flared gilded cuff, plated forearm, heavy fist
        m.box(fore, -5.5, 0, -5.5, 11, 4, 11, plate(GOLD, GOLD_D, GOLD_L, seed=25))
        m.box(fore, -5, 3, -5, 10, 7, 10, {"side": lames(4, IRON, IRON_D, 26), "*": IRON})
        m.box(fore, -4.5, 9, -5, 9, 7, 10, plate(STEEL, IRON_D, IRON_L, rivet=GOLD_L, seed=27))

    # ------------------------------------------------------------ the hammer: haft along -y from the fist, pommel on the ground
    m.box("hammer", -2.5, 15, -2.5, 5, 3, 5, gold_ring())                                   # pommel
    m.box("hammer", -1.5, -27, -1.5, 3, 42, 3, lambda f_, x, y, w, h:
          GOLD if y % 10 == 0 else (WOOD if (y // 2 + x) % 3 else WOOD_D) if y < 26 else
          (LEATHER if (x + y) % 3 else mul(LEATHER, 0.7)))
    m.box("hammer", -2.5, -31, -2.5, 5, 4, 5, plate(IRON, IRON_D, IRON_L, seed=30))         # socket collar
    m.box("hammer", -7, -45, -11, 14, 14, 22, hot_paint(), glow=hot_metal())                 # red-hot head
    for z in (-6, 3):
        m.box("hammer", -8, -46, z, 16, 16, 3, plate(IRON_D, (24, 22, 26), IRON, rivet=GOLD_L, seed=31 + z))
    m.box("hammer", -2, -50, -2, 4, 4, 4, plate(IRON_D, (24, 22, 26), IRON, seed=33))        # top spike

    # ------------------------------------------------------------ the anvil shield (profile in y-z, faces +x)
    anvil = plate((58, 60, 66), (30, 30, 36), (128, 130, 140), seed=40)
    m.box("shield", 0, -10, -13, 7, 6, 24, {"*": anvil, "top": lambda f_, x, y, w, h: (150, 152, 160) if 1 <= x < w - 1
                                             else (90, 92, 100)})
    m.box("shield", 0, -10, -19, 7, 4, 6, anvil)          # horn
    m.box("shield", 1, -10, -23, 5, 2, 4, anvil)          # horn tip
    m.box("shield", 0, -10, 11, 7, 4, 4, anvil)           # heel
    m.box("shield", 1, -4, -7, 5, 7, 13, {"*": anvil, "left": lambda f_, x, y, w, h: GOLD if (x - 6) ** 2 + (y - 3) ** 2 <= 4
                                          else (58, 60, 66)})   # waist with a gold seal
    m.box("shield", 0, 3, -11, 7, 4, 21, anvil)           # base
    m.box("shield", -1, -2, -3, 2, 4, 6, LEATHER)          # strap

    # ------------------------------------------------------------ legs: plated thighs, greaves, broad sabatons
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -5, 0, -5, 10, 7, 10, {"side": lames(4, STEEL, IRON_D, 41), "*": STEEL})
        m.box(shin, -5, 0, -5, 10, 4, 10, plate(IRON, IRON_D, IRON_L, seed=42))
        m.box(shin, -4, -2, -7, 8, 5, 3, plate(GOLD, GOLD_D, GOLD_L, seed=43))           # knee cop
        m.box(shin, -6, 3, -9, 12, 4, 15, plate(IRON_D, (26, 26, 30), IRON, rivet=GOLD_L, seed=44))
        m.box(shin, -5, 2, -10, 10, 2, 2, plate(STEEL, IRON_D, IRON_L, seed=45))         # toe cap

    anims(m)
    return m


def anims(m):
    Z = (0, 0, 0)
    # ------------------------------------------------------------ idle: heavy breathing, beard and cloak sway
    a = m.anim("idle", 3.2)
    a.rot("torso", (0, Z), (1.6, (2.5, 0, 0)), (3.2, Z))
    a.rot("head", (0, Z), (1.6, (-3, 4, 0)), (3.2, Z))
    a.rot("beard", (0, Z), (1.6, (-3, 0, 1.5)), (3.2, Z))
    a.rot("braid_c", (0, Z), (1.2, (4, 0, 2)), (2.4, (-2, 0, -2)), (3.2, Z))
    a.rot("braid_r", (0, Z), (1.4, (3, 0, -3)), (3.2, Z))
    a.rot("braid_l", (0, Z), (1.8, (3, 0, 3)), (3.2, Z))
    a.rot("cape", (0, Z), (1.6, (4, 0, 1)), (3.2, Z))
    a.rot("arm_r", (0, Z), (1.6, (0, 0, 2)), (3.2, Z))
    a.rot("arm_l", (0, Z), (1.6, (-2, 0, -2)), (3.2, Z))

    # ------------------------------------------------------------ walk: heavy stomping gait
    a = m.anim("walk", 1.8)
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (22 * s, 0, 0)), (0.9, (-22 * s, 0, 0)), (1.8, (22 * s, 0, 0)))
    a.rot("shin_r", (0, Z), (0.45, (28, 0, 0)), (0.9, Z), (1.8, Z))
    a.rot("shin_l", (0, Z), (0.9, Z), (1.35, (28, 0, 0)), (1.8, Z))
    a.rot("torso", (0, (0, 0, 3)), (0.9, (0, 0, -3)), (1.8, (0, 0, 3)))
    a.rot("arm_l", (0, (-12, 0, 0)), (0.9, (10, 0, 0)), (1.8, (-12, 0, 0)))
    a.rot("arm_r", (0, (6, 0, 0)), (0.9, (-6, 0, 0)), (1.8, (6, 0, 0)))
    a.rot("cape", (0, (6, 0, 0)), (0.45, (10, 0, 0)), (0.9, (6, 0, 0)), (1.35, (10, 0, 0)), (1.8, (6, 0, 0)))
    a.pos("bone", (0, Z), (0.45, (0, -1.5, 0)), (0.9, Z), (1.35, (0, -1.5, 0)), (1.8, Z))

    def ham(total, arm, fore=-FORE_R):
        """Hammer pitch offset so the head points at `total` degrees (0 = up, 90 = forward, -90 = back)
        relative to the torso, given the right arm's pitch offset and the forearm's."""
        return total - (arm + FORE_R + fore + HAM_R)

    UP_BACK, STRIKE = -50, 72           # hammer over the shoulder / hammer on the ground in front
    RAISED, SMASH = -170, -60           # right arm pitch for both
    H = ham(UP_BACK, RAISED, 12)       # the same offset also lands the head on STRIKE at SMASH

    # ------------------------------------------------------------ slam: hammer high overhead (long telegraph), smash at 1.0 s
    a = m.anim("slam", 2.0)
    a.rot("arm_r", (0, Z), (0.85, (RAISED, 0, -12)), (1.0, (SMASH, 0, -6), "linear"), (1.5, (SMASH + 5, 0, -6)), (2.0, Z))
    a.rot("forearm_r", (0, Z), (0.85, (12, 0, 0)), (1.0, (-FORE_R, 0, 0), "linear"), (1.5, (-FORE_R, 0, 0)), (2.0, Z))
    a.rot("hammer", (0, Z), (0.85, (H, 0, 16)), (1.0, (H, 0, 16)), (1.5, (H, 0, 16)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.85, (-50, 0, -35)), (1.0, (-20, 0, -10), "linear"), (2.0, Z))
    a.rot("torso", (0, Z), (0.85, (-16, 10, 0)), (1.0, (28, -5, 0), "linear"), (1.5, (24, -5, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.85, (-10, 0, 0)), (1.0, (-14, 0, 0)), (2.0, Z))
    a.rot("beard", (0, Z), (0.85, (-15, 0, 0)), (1.0, (25, 0, 0), "linear"), (1.3, (-8, 0, 0)), (2.0, Z))
    a.rot("cape", (0, Z), (0.85, (2, 0, 0)), (1.0, (-20, 0, 0), "linear"), (1.3, (12, 0, 0)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.85, (10, 0, 0)), (1.0, (-25, 0, 0)), (1.5, (-25, 0, 0)), (2.0, Z))
    a.rot("shin_r", (0, Z), (1.0, (25, 0, 0)), (1.5, (25, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.85, (0, 2, 2)), (1.0, (0, -4, -3), "linear"), (1.5, (0, -4, -3)), (2.0, Z))

    # ------------------------------------------------------------ sweep: hammer wound back to the right, scythes left at 0.8 s
    a = m.anim("sweep", 1.5)
    hs = ham(80, -55)
    a.rot("torso", (0, Z), (0.65, (4, 65, 0)), (0.8, (8, -70, 0), "linear"), (1.0, (8, -66, 0)), (1.5, Z))
    a.rot("arm_r", (0, Z), (0.65, (-55, 0, 30)), (0.8, (-55, 0, 10), "linear"), (1.0, (-55, 0, 10)), (1.5, Z))
    a.rot("forearm_r", (0, Z), (0.65, (-FORE_R, 0, 0)), (1.0, (-FORE_R, 0, 0)), (1.5, Z))
    a.rot("hammer", (0, Z), (0.65, (hs, 0, 16)), (0.8, (hs, 0, 16)), (1.0, (hs, 0, 16)), (1.5, Z))
    a.rot("arm_l", (0, Z), (0.65, (-35, 0, -25)), (0.8, (10, 0, -10)), (1.5, Z))
    a.rot("head", (0, Z), (0.65, (0, -40, 0)), (0.8, (0, 40, 0), "linear"), (1.0, (0, 35, 0)), (1.5, Z))
    a.rot("beard", (0, Z), (0.65, (0, 0, 10)), (0.8, (0, 0, -18), "linear"), (1.1, (0, 0, 6)), (1.5, Z))
    a.rot("leg_l", (0, Z), (0.65, (-20, 0, 0)), (0.8, (10, 0, 0)), (1.5, Z))
    a.pos("bone", (0, Z), (0.65, (0, -2, 2)), (0.8, (0, -3, -3), "linear"), (1.0, (0, -3, -3)), (1.5, Z))

    # ------------------------------------------------------------ bash: the anvil turned forward as a shield, crouch, charge from 0.7 s
    a = m.anim("bash", 1.8)
    a.rot("arm_l", (0, Z), (0.6, (-55, 0, 25)), (1.25, (-55, 0, 25)), (1.8, Z))
    a.rot("forearm_l", (0, Z), (0.6, (-25, 80, 0)), (1.25, (-25, 80, 0)), (1.8, Z))
    a.rot("torso", (0, Z), (0.6, (18, -25, 0)), (0.75, (26, -30, 0), "linear"), (1.25, (26, -30, 0)), (1.8, Z))
    a.rot("arm_r", (0, Z), (0.6, (20, 0, 10)), (1.25, (25, 0, 10)), (1.8, Z))
    a.rot("hammer", (0, Z), (0.6, (-30, 0, 0)), (1.25, (-30, 0, 0)), (1.8, Z))
    a.rot("leg_r", (0, Z), (0.6, (25, 0, 0)), (0.85, (-35, 0, 0)), (1.0, (30, 0, 0)), (1.15, (-35, 0, 0)), (1.3, Z), (1.8, Z))
    a.rot("leg_l", (0, Z), (0.6, (-35, 0, 0)), (0.85, (30, 0, 0)), (1.0, (-35, 0, 0)), (1.15, (30, 0, 0)), (1.3, Z), (1.8, Z))
    a.rot("shin_r", (0, Z), (0.6, (25, 0, 0)), (1.3, Z))
    a.rot("cape", (0, Z), (0.75, (20, 0, 0)), (1.25, (25, 0, 0)), (1.8, Z))
    a.pos("bone", (0, Z), (0.6, (0, -3, 0)), (0.75, (0, -1, -4), "linear"), (1.25, (0, -1, -4)), (1.8, Z))

    # ------------------------------------------------------------ sparks: the hammer dragged back along the floor, then flung up
    # at 0.75 s in an uppercut that sprays a fan of embers forward
    a = m.anim("sparks", 1.65)
    h_low, h_up = ham(-150, 35), ham(20, -150) - 360
    a.rot("arm_r", (0, Z), (0.6, (35, 0, 12)), (0.75, (-150, 0, -5), "linear"), (1.2, (-145, 0, -5)), (1.65, Z))
    a.rot("forearm_r", (0, Z), (0.6, (-FORE_R, 0, 0)), (1.2, (-FORE_R, 0, 0)), (1.65, Z))
    a.rot("hammer", (0, Z), (0.6, (h_low, 0, 16)), (0.75, (h_up, 0, 16), "linear"), (1.2, (h_up, 0, 16)), (1.65, Z))
    a.rot("torso", (0, Z), (0.6, (20, 35, 0)), (0.75, (-12, -20, 0), "linear"), (1.2, (-10, -18, 0)), (1.65, Z))
    a.rot("arm_l", (0, Z), (0.6, (-40, 0, -30)), (0.75, (10, 0, -15)), (1.65, Z))
    a.rot("head", (0, Z), (0.6, (10, -20, 0)), (0.75, (-15, 10, 0)), (1.65, Z))
    a.rot("beard", (0, Z), (0.6, (10, 0, 0)), (0.75, (-25, 0, 0), "linear"), (1.0, (8, 0, 0)), (1.65, Z))
    a.rot("leg_r", (0, Z), (0.6, (25, 0, 0)), (0.75, (-10, 0, 0)), (1.65, Z))
    a.pos("bone", (0, Z), (0.6, (0, -3, 2)), (0.75, (0, 0, -2), "linear"), (1.2, (0, 0, -2)), (1.65, Z))

    # ------------------------------------------------------------ anvil: the anvil lifted to the sky, driven into the floor (0.9 s)
    a = m.anim("anvil", 1.9)
    a.rot("arm_l", (0, Z), (0.75, (-175, 0, -15)), (0.9, (-45, 0, -5), "linear"), (1.4, (-45, 0, -5)), (1.9, Z))
    a.rot("forearm_l", (0, Z), (0.75, (-10, 0, 0)), (0.9, (15, 0, 0)), (1.9, Z))
    a.rot("torso", (0, Z), (0.75, (-15, -15, 0)), (0.9, (32, 10, 0), "linear"), (1.4, (30, 10, 0)), (1.9, Z))
    a.rot("head", (0, Z), (0.75, (-20, 0, 0)), (0.9, (-14, 0, 0)), (1.9, Z))
    a.rot("arm_r", (0, Z), (0.75, (-20, 0, 25)), (0.9, (10, 0, 15)), (1.9, Z))
    a.rot("hammer", (0, Z), (0.75, (20, 0, 0)), (0.9, (-20, 0, 0)), (1.9, Z))
    a.rot("leg_l", (0, Z), (0.75, (-35, 0, 0)), (0.9, (-25, 0, 0), "linear"), (1.4, (-25, 0, 0)), (1.9, Z))
    a.rot("shin_l", (0, Z), (0.75, (30, 0, 0)), (0.9, (25, 0, 0)), (1.4, (25, 0, 0)), (1.9, Z))
    a.rot("cape", (0, Z), (0.75, (5, 0, 0)), (0.9, (-15, 0, 0), "linear"), (1.2, (15, 0, 0)), (1.9, Z))
    a.pos("bone", (0, Z), (0.75, (0, 2, 0)), (0.9, (0, -5, -2), "linear"), (1.4, (0, -5, -2)), (1.9, Z))

    # ------------------------------------------------------------ spin (phase 2): hammer at arm's length, three full turns 0.6 -> 2.1 s
    a = m.anim("spin", 2.7)
    keys = [(0, Z), (0.6, (0, 40, 0))]
    turn = 0.5
    for i in range(3):
        t0 = 0.6 + i * turn
        keys.append((t0 + turn, (0, 40 - 360, 0), "linear"))
        if i < 2:
            keys.append((t0 + turn + 0.0005, (0, 40, 0), "linear"))
    keys += [(2.7, Z)]
    a.rot("bone", *keys)
    a.rot("arm_r", (0, Z), (0.6, (0, 0, 62)), (2.1, (0, 0, 62)), (2.7, Z))
    a.rot("forearm_r", (0, Z), (0.6, (-FORE_R, 0, 0)), (2.1, (-FORE_R, 0, 0)), (2.7, Z))
    a.rot("hammer", (0, Z), (0.6, (90 - HAM_R, 0, 16)), (2.1, (90 - HAM_R, 0, 16)), (2.7, Z))
    a.rot("arm_l", (0, Z), (0.6, (-20, 0, -60)), (2.1, (-20, 0, -60)), (2.7, Z))
    a.rot("torso", (0, Z), (0.6, (10, 0, 8)), (2.1, (10, 0, 8)), (2.7, Z))
    a.rot("beard", (0, Z), (0.6, (-25, 0, 20)), (2.1, (-25, 0, 20)), (2.7, Z))
    a.rot("cape", (0, Z), (0.6, (55, 0, 0)), (2.1, (55, 0, 0)), (2.7, Z))

    # ------------------------------------------------------------ triple (phase 2): slams at 0.9 s, 1.5 s and a delayed one at 2.3 s
    a = m.anim("triple", 3.25)
    a.rot("arm_r", (0, Z), (0.75, (RAISED, 0, -12)), (0.9, (SMASH, 0, -6), "linear"),
          (1.3, (RAISED + 5, 0, -12)), (1.5, (SMASH, 0, -6), "linear"),
          (1.9, (RAISED - 15, 0, -12)), (2.15, (RAISED - 20, 0, -12)), (2.3, (SMASH, 0, -6), "linear"),
          (2.8, (SMASH + 5, 0, -6)), (3.25, Z))
    a.rot("forearm_r", (0, Z), (0.75, (12, 0, 0)), (0.9, (-FORE_R, 0, 0)), (1.3, (12, 0, 0)), (1.5, (-FORE_R, 0, 0)),
          (2.15, (12, 0, 0)), (2.3, (-FORE_R, 0, 0)), (2.8, (-FORE_R, 0, 0)), (3.25, Z))
    a.rot("hammer", (0, Z), (0.75, (H, 0, 16)), (2.8, (H, 0, 16)), (3.25, Z))
    a.rot("torso", (0, Z), (0.75, (-14, 8, 0)), (0.9, (26, -5, 0), "linear"), (1.3, (-10, -8, 0)), (1.5, (26, 5, 0), "linear"),
          (2.15, (-22, 0, 0)), (2.3, (26, 0, 0), "linear"), (2.8, (24, 0, 0)), (3.25, Z))
    a.rot("arm_l", (0, Z), (0.75, (-50, 0, -35)), (1.5, (-30, 0, -30)), (2.15, (-90, 0, -40)), (2.3, (-20, 0, -10)), (3.25, Z))
    a.rot("beard", (0, Z), (0.9, (25, 0, 0)), (1.3, (-10, 0, 0)), (1.5, (25, 0, 0)), (2.15, (-15, 0, 0)), (2.3, (30, 0, 0)), (3.25, Z))
    a.rot("cape", (0, Z), (0.9, (-15, 0, 0)), (1.3, (10, 0, 0)), (1.5, (-15, 0, 0)), (2.15, (12, 0, 0)), (2.3, (-20, 0, 0)), (3.25, Z))
    a.pos("bone", (0, Z), (0.75, (0, 2, 2)), (0.9, (0, -4, -2), "linear"), (1.3, (0, 1, -2)), (1.5, (0, -4, -4), "linear"),
          (2.15, (0, 3, -4)), (2.3, (0, -4, -5), "linear"), (2.8, (0, -4, -5)), (3.25, Z))

    # ------------------------------------------------------------ leap (phase 2): crouch, launch at 0.8 s, crash down at 1.45 s
    a = m.anim("leap", 2.4)
    a.pos("bone", (0, Z), (0.75, (0, -6, 0)), (0.8, (0, -6, 0)), (1.1, (0, 8, 0)), (1.45, (0, -6, -2), "linear"),
          (1.9, (0, -6, -2)), (2.4, Z))
    for leg in ("leg_r", "leg_l"):
        a.rot(leg, (0, Z), (0.75, (-45, 0, 0)), (1.0, (15, 0, 0)), (1.45, (-40, 0, 0), "linear"), (1.9, (-40, 0, 0)), (2.4, Z))
    for shin in ("shin_r", "shin_l"):
        a.rot(shin, (0, Z), (0.75, (55, 0, 0)), (1.0, (10, 0, 0)), (1.45, (50, 0, 0), "linear"), (1.9, (50, 0, 0)), (2.4, Z))
    a.rot("torso", (0, Z), (0.75, (25, 0, 0)), (1.1, (-20, 0, 0)), (1.45, (22, 0, 0), "linear"), (1.9, (20, 0, 0)), (2.4, Z))
    a.rot("arm_r", (0, Z), (0.75, (20, 0, 10)), (1.1, (RAISED, 0, -12)), (1.45, (SMASH, 0, -6), "linear"), (1.9, (SMASH + 5, 0, -6)),
          (2.4, Z))
    a.rot("forearm_r", (0, Z), (1.1, (12, 0, 0)), (1.45, (-FORE_R, 0, 0)), (1.9, (-FORE_R, 0, 0)), (2.4, Z))
    a.rot("hammer", (0, Z), (0.75, (-20, 0, 0)), (1.1, (H, 0, 16)), (1.9, (H, 0, 16)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.75, (30, 0, -10)), (1.1, (-120, 0, -40)), (1.45, (-30, 0, -20)), (2.4, Z))
    a.rot("cape", (0, Z), (1.1, (40, 0, 0)), (1.45, (-5, 0, 0)), (2.4, Z))
    a.rot("beard", (0, Z), (1.1, (-30, 0, 0)), (1.45, (30, 0, 0), "linear"), (1.7, (-6, 0, 0)), (2.4, Z))

    # ------------------------------------------------------------ roar: hammer and anvil spread wide, head thrown back
    a = m.anim("roar", 2.4)
    a.rot("torso", (0, Z), (0.5, (-18, 0, 0)), (1.9, (-18, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, Z))
    a.rot("beard", (0, Z), (0.5, (-12, 0, 0)), (1.2, (-18, 0, 4)), (1.9, (-12, 0, 0)), (2.4, Z))
    a.rot("arm_r", (0, Z), (0.5, (-40, 0, 70)), (1.9, (-40, 0, 70)), (2.4, Z))
    a.rot("hammer", (0, Z), (0.5, (30, 0, -50)), (1.9, (30, 0, -50)), (2.4, Z))
    a.rot("arm_l", (0, Z), (0.5, (-40, 0, -70)), (1.9, (-40, 0, -70)), (2.4, Z))
    a.rot("cape", (0, Z), (0.5, (25, 0, 0)), (1.2, (35, 0, 0)), (1.9, (25, 0, 0)), (2.4, Z))
    a.pos("bone", (0, Z), (0.5, (0, -2, 0)), (1.9, (0, -2, 0)), (2.4, Z))

    # ------------------------------------------------------------ stagger: posture broken, falls to one knee leaning on the hammer
    a = m.anim("stagger", 2.0)
    a.pos("bone", (0, Z), (0.3, (0, -7, 2)), (1.6, (0, -7, 2)), (2.0, Z))
    a.rot("leg_r", (0, Z), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, Z))
    a.rot("shin_r", (0, Z), (0.3, (70, 0, 0)), (1.6, (70, 0, 0)), (2.0, Z))
    a.rot("leg_l", (0, Z), (0.3, (25, 0, 0)), (1.6, (25, 0, 0)), (2.0, Z))
    a.rot("shin_l", (0, Z), (0.3, (65, 0, 0)), (1.6, (65, 0, 0)), (2.0, Z))
    a.rot("torso", (0, Z), (0.3, (20, 0, 5)), (1.6, (20, 0, 5)), (2.0, Z))
    a.rot("head", (0, Z), (0.3, (18, 0, 0)), (1.6, (18, 0, 0)), (2.0, Z))
    a.rot("arm_l", (0, Z), (0.3, (25, 0, -10)), (1.6, (25, 0, -10)), (2.0, Z))
    a.rot("arm_r", (0, Z), (0.3, (-25, 0, 5)), (1.6, (-25, 0, 5)), (2.0, Z))
    a.rot("hammer", (0, Z), (0.3, (35, 0, 10)), (1.6, (35, 0, 10)), (2.0, Z))
