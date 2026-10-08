"""The Anvil Warden (Le Gardien de l'enclume): the smith the Basalt Titan's forge was built for, a hulking golem of
columnar basalt about 5.6 blocks tall, kept alive by the forge's heat that glows through every joint of its stone.

Silhouette idea: a smith's crucible for a head. A squat, hunched giant with enormous shoulders and short thick legs;
in place of a head it wears a graphite crucible banded in brass, its spout jutting forward, molten metal brimming at
its lip and a glowing slit for a visor. Strong asymmetry: its RIGHT arm, the heavier, carries a forge hammer whose
head nearly drags on the floor (a heavy iron block with a white-hot face); its LEFT arm holds long smith's tongs out
in front of it, a glowing billet in their jaws. A scorched leather apron hangs from a brass-buckled belt, a quench
bucket swings on its left hip, and three basalt columns jut from its left shoulder-blade, their tops still molten.
"""
import functools
import random

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

BASALT = (58, 54, 62)
BASALT_L = (104, 98, 108)
BASALT_D = (28, 25, 31)
CRUST = (52, 24, 20)
MAGMA = (255, 120, 28)
MAGMA_L = (255, 224, 128)
MAGMA_D = (186, 46, 14)
WHITE_HOT = (255, 246, 214)
GRAPHITE = (66, 60, 58)
GRAPHITE_L = (110, 102, 96)
GRAPHITE_D = (36, 32, 32)
STEEL = (88, 90, 100)
STEEL_L = (140, 142, 154)
STEEL_D = (46, 46, 54)
LEATHER = (98, 62, 40)
LEATHER_D = (58, 36, 24)
LEATHER_L = (138, 94, 62)
SCORCH = (34, 24, 20)
WOOD = (82, 54, 34)
WOOD_D = (52, 34, 22)
WATER = (60, 96, 170)


# ---------------------------------------------------------------- paint
@functools.lru_cache(maxsize=None)
def _seams(w, h, seed, count):
    """Glowing seams along the joints of the basalt columns: mostly vertical runs that jog sideways where two columns
    meet, a few short branches. {pixel: heat}, heat 2 at the core, 1 on the cooling edge."""
    rnd = random.Random(seed * 7919 + w * 31 + h * 131)
    core = set()
    for _ in range(count):
        x = rnd.randint(1, max(1, w - 2))
        y = rnd.randint(0, max(0, h // 5))
        for _ in range(int(h * (0.55 + rnd.random() * 0.4))):
            core.add((x, y))
            y += 1
            if rnd.random() < 0.22:                         # a column's corner: the seam jogs a pixel or two
                x = max(0, min(w - 1, x + rnd.choice((-1, 1))))
                core.add((x, y))
            if rnd.random() < 0.08:                         # a short horizontal joint between two drums
                bx = x
                for _ in range(rnd.randint(2, 4)):
                    bx = max(0, min(w - 1, bx + rnd.choice((-1, 1))))
                    core.add((bx, y))
    out = {}
    for (x, y) in core:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if 0 <= p[0] < w and 0 <= p[1] < h and p not in core:
                out[p] = 1
    for p in core:
        out[p] = 2
    return out


def basalt(seed=0, seams=0, top_hot=False):
    """Columnar basalt: dark purple-grey stone in vertical columns (a darker joint every 4-6 texels), lit top, dark
    underside; ``seams`` glowing joints (their cooling edges dull red); ``top_hot`` paints the top face molten."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BASALT_D
        if face == "top":
            if top_hot:
                return MAGMA_D if B.n(x, y, seed + 7) < 0.6 else CRUST
            return mul(BASALT_L, 0.85 + (B.n(x, y, seed) - 0.5) * 0.12)
        if seams:
            heat = _seams(w, h, seed, seams).get((x, y))
            if heat == 2:
                return MAGMA_D
            if heat == 1:
                return CRUST if B.n(x, y, seed + 3) < 0.75 else mix(MAGMA_D, CRUST, 0.75)
        k = 1.08 - 0.22 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.14
        c = mul(BASALT, k)
        col = (x + seed) % 5
        if col == 0:
            c = mul(c, 0.72)                                # the joint between two columns
        elif col == 1:
            c = mix(c, BASALT_L, 0.25)                      # the lit edge of the next one
        if B.n(x // 2, y // 3, seed + 5) < 0.1:
            c = mix(c, BASALT_L, 0.4)
        return c
    return f


def seams_glow(seed=0, seams=2, top_hot=False):
    """The emissive core of the seams painted by ``basalt`` with the same seed and count."""
    def f(face, x, y, w, h):
        if face == "top" and top_hot:
            return MAGMA_L if B.n(x, y, seed + 7) < 0.25 else (MAGMA if B.n(x, y, seed + 7) < 0.6 else None)
        if face in ("front", "back", "left", "right") and _seams(w, h, seed, seams).get((x, y)) == 2:
            return MAGMA_L if B.n(x, y, seed + 1) < 0.3 else MAGMA
        return None
    return f


def iron_plate(seed=0, rim=True):
    """Blackened iron armour plate with a brass rim and rivets, heat-blued near the edges."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return STEEL_D
        if rim and w > 3 and h > 3:
            if y == 0 or (face == "top" and (x in (0, w - 1) or y in (0, h - 1))):
                return B.BRASS_L
            if x in (0, w - 1) or y == h - 1:
                return B.BRASS_D if face != "top" else B.BRASS
            if (x in (1, w - 2)) and (y in (1, h - 2)) and w > 6 and h > 5:
                return B.BRASS_L
        c = mul(STEEL, 1.05 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.1)
        if face == "top":
            c = mul(c, 1.2)
        if B.n(x // 2, y, seed + 2) < 0.07:
            c = mix(c, (70, 80, 130), 0.35)                 # heat-blued streaks
        return c
    return f


def crucible(seed=0, visor=False):
    """The crucible helm: graphite clay, crazed and sooted, banded in brass; the front face of the body is cut by a
    narrow visor slit (``visor``) whose glow comes from ``visor_glow``."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GRAPHITE_D
        if face != "top" and y in (1, h - 3):
            return B.BRASS_L if face == "front" and x % 4 == 2 else B.BRASS
        if face != "top" and y in (2, h - 2):
            return B.BRASS_D
        if visor and face == "front":
            if y in (5, 6) and 2 <= x <= w - 3:
                return (20, 10, 8)
            if y == 7 and 3 <= x <= w - 4:
                return GRAPHITE_D
        c = mul(GRAPHITE, 1.06 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.14)
        if (x * 3 + y * 7 + seed) % 11 == 0:
            c = mul(c, 0.7)                                 # crazing in the glaze
        if face == "top":
            c = mix(c, GRAPHITE_L, 0.3)
        if y > h - 5 and B.n(x, y, seed + 4) < 0.25:
            c = mix(c, B.SOOT, 0.6)
        if face != "top" and y <= 3 and B.n(x, y, seed + 9) < 0.12:
            return MAGMA_D                                  # molten drips run down from the lip
        return c
    return f


def visor_glow(face, x, y, w, h):
    if face != "front":
        return None
    if y in (5, 6) and 2 <= x <= w - 3:
        eye = x in (3, 4, w - 5, w - 4)
        return WHITE_HOT if eye and y == 5 else (MAGMA_L if eye else MAGMA)
    return None


def molten(face, x, y, w, h):
    """The brimming metal: a white-hot centre, orange to the rim, a crust skin drifting on it."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = max(abs(x - cx) / max(1, cx), abs(y - cy) / max(1, cy))
    if B.n(x // 2, y // 2, 41) < 0.12:
        return MAGMA_D
    return WHITE_HOT if r < 0.3 else (MAGMA_L if r < 0.65 else MAGMA)


def leather(seed=0, rivets=False):
    """The apron: thick scorched leather, burn holes and soot, brass rivets down its edges."""
    def f(face, x, y, w, h):
        if face == "top":
            return LEATHER_D
        c = mul(LEATHER, 1.08 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.12)
        if (x + y * 2) % 7 == 0:
            c = mix(c, LEATHER_L, 0.25)                     # creases
        if B.n(x // 2, y // 2, seed + 3) < 0.13:
            c = mix(c, SCORCH, 0.7)                         # scorch marks
        if y >= h - 2:
            c = mix(c, SCORCH, 0.5)                         # the singed hem
        if rivets and face in ("front", "back") and x in (1, w - 2) and y % 3 == 1:
            return B.BRASS_L
        return c
    return f


def hem_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("front", "back") and y == h - 1 and B.n(x, y, seed + 6) < 0.3:
            return MAGMA
        return None
    return f


def hammer_head(seed=0):
    """The forge hammer's head: black steel with a polished bevel, brass wedges; its striking faces white-hot."""
    def f(face, x, y, w, h):
        if face in ("front", "back"):
            r = max(abs(x - (w - 1) / 2) / max(1, (w - 1) / 2), abs(y - (h - 1) / 2) / max(1, (h - 1) / 2))
            if r > 0.78:
                return STEEL_D
            return mix(MAGMA_D, MAGMA, 1.0 - r)
        if face == "top":
            return STEEL_L if x in (0, w - 1) else mul(STEEL, 1.15)
        if face == "bottom":
            return STEEL_D
        if y in (0, h - 1):
            return STEEL_L
        c = mul(STEEL, 0.95 + (B.n(x, y, seed) - 0.5) * 0.1)
        if x in (w // 2 - 1, w // 2):
            return B.BRASS if y not in (1, h - 2) else B.BRASS_D         # the wedges round the eye
        return c
    return f


def hammer_glow(face, x, y, w, h):
    if face not in ("front", "back"):
        return None
    r = max(abs(x - (w - 1) / 2) / max(1, (w - 1) / 2), abs(y - (h - 1) / 2) / max(1, (h - 1) / 2))
    if r > 0.78:
        return None
    return WHITE_HOT if r < 0.3 else (MAGMA_L if r < 0.55 else MAGMA)


def haft(seed=0):
    """Iron-bound ash haft, a leather wrap near the fist."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOD_D
        if y % 7 == 0:
            return STEEL
        c = mul(WOOD, 1.0 + (B.n(x, y, seed) - 0.5) * 0.15)
        if (y + seed) % 3 == 0:
            c = mul(c, 0.86)
        return c
    return f


def tong_iron(face, x, y, w, h):
    if face == "top":
        return STEEL_L
    if face == "bottom":
        return STEEL_D
    c = mul(STEEL, 1.0 - 0.3 * y / max(1, h))
    if y > h - 6:
        return mix(c, MAGMA_D, (y - (h - 6)) / 6 * 0.7)    # the jaws heat-tinted toward the billet
    return c


def billet_glow(face, x, y, w, h):
    return WHITE_HOT if (x + y) % 3 == 0 else MAGMA_L


def bucket(face, x, y, w, h):
    if face == "top":
        return WATER if 0 < x < w - 1 and 0 < y < h - 1 else STEEL_D
    if face == "bottom":
        return STEEL_D
    if y in (0, h - 1):
        return STEEL_L
    return mul(WOOD, 0.95 + (B.n(x, y, 77) - 0.5) * 0.15) if x % 3 else WOOD_D


# ---------------------------------------------------------------- build
def build():
    m = Model("anvil_warden", seed=263, shadow=2.0, walk_speed=0.55, walk_scale=0.75, glow_pulse=0.06)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -30, 0))
    m.part("apron", "pelvis", pivot=(0, -2, -8.6))
    m.part("bucket", "pelvis", pivot=(14, -1, 0))
    m.part("torso", "pelvis", pivot=(0, -5, 0), rot=(16, 0, 0))
    m.part("columns", "torso", pivot=(10, -30, 6), rot=(-26, 0, 22))
    m.part("head", "torso", pivot=(0, -31, -5), rot=(-16, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(8.5 * sx, -28, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 13, 0))
    m.part("arm_r", "torso", pivot=(-19, -25, -1), rot=(-6, 0, 12))
    m.part("fore_r", "arm_r", pivot=(-0.5, 14, 0), rot=(-28, 0, -4))
    m.part("hammer", "fore_r", pivot=(-0.5, 15, -0.5), rot=(18, 0, 0))
    m.part("arm_l", "torso", pivot=(18, -25, -1), rot=(-10, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0.5, 14, 0), rot=(-46, 0, 4))
    m.part("tongs", "fore_l", pivot=(0.5, 15, -0.5), rot=(-40, 0, 0))

    # ---- legs: short basalt pillars, iron knee plates, splayed basalt feet
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -6, -2, -6, 12, 15, 12, basalt(1 + sx, seams=1), glow=seams_glow(1 + sx, 1))
        m.box(leg, -5, 10, -7.5, 10, 6, 3, iron_plate(3 + sx))                 # knee plate
        m.box(shin, -5, 0, -5, 10, 11, 10, basalt(5 + sx, seams=1), glow=seams_glow(5 + sx, 1))
        m.box(shin, -6.5, 10, -9, 13, 5, 15, basalt(7 + sx))                   # the foot
        m.box(shin, -5.5, 9, -10, 11, 3, 3, iron_plate(9 + sx, rim=False))     # iron toe cap

    # ---- pelvis, belt, apron, quench bucket
    m.box("pelvis", -12, -6, -7.5, 24, 9, 15, basalt(10, seams=1), glow=seams_glow(10, 1))
    m.box("pelvis", -12.5, -5, -8, 25, 3, 16, leather(11))                     # the belt
    m.box("pelvis", -2.5, -5.5, -8.8, 5, 4, 1, B.brass(12, rivet_step=2))      # its buckle
    m.box("apron", -9, 0, -0.5, 18, 16, 1, leather(13, rivets=True), glow=hem_glow(13))
    m.box("bucket", -2, 0, -3, 5, 7, 6, bucket)
    m.box("bucket", -2.5, -3, -0.5, 6, 3, 1, STEEL_D)                          # its bail on the belt

    # ---- torso: a great hunched barrel of basalt, an iron gorget, molten seams
    m.box("torso", -12, -12, -8, 24, 13, 16, basalt(20, seams=1), glow=seams_glow(20, 1))
    m.box("torso", -17, -30, -10, 34, 19, 20, basalt(21, seams=2), glow=seams_glow(21, 2))
    m.box("torso", -13, -34, -4, 26, 5, 14, basalt(22, seams=2), glow=seams_glow(22, 2))       # the hump
    m.box("torso", -9, -33, -10.5, 18, 4, 9, iron_plate(23))                   # gorget
    m.box("torso", -10, -26, -10.8, 20, 12, 1, iron_plate(24))                 # breastplate over the furnace
    m.box("torso", -3, -23, -11.2, 6, 6, 1, B.grate(STEEL_D, B.SOOT), glow=B.grate_glow(MAGMA, MAGMA_L))   # its draught
    # basalt columns jutting from the left shoulder-blade, molten on top
    for i, (x, h, z) in enumerate(((-3, 18, 0), (2, 12, -3), (-1, 9, 4))):
        m.box("columns", x, -h, z - 2, 5, h, 5, basalt(30 + i, seams=1, top_hot=True),
              glow=seams_glow(30 + i, 1, top_hot=True))

    # ---- the crucible helm
    m.box("head", -5, -3, -6, 10, 4, 9, basalt(40))                            # the stone jaw under it
    m.box("head", -8, -16, -8, 16, 14, 16, crucible(41, visor=True), glow=visor_glow)
    m.box("head", -9, -18, -9, 18, 2, 1, crucible(42))                         # the lip: a thick ring
    m.box("head", -9, -18, 8, 18, 2, 1, crucible(43))
    m.box("head", -9, -18, -8, 1, 2, 16, crucible(44))
    m.box("head", 8, -18, -8, 1, 2, 16, crucible(45))
    m.box("head", -8, -17, -8, 16, 1, 16, molten, glow=molten)                 # the brimming metal
    m.box("head", -2.5, -18, -13, 5, 2, 4, crucible(46))                       # the spout
    m.box("head", -1.5, -18.4, -13.5, 3, 1, 5, molten, glow=molten)            # metal in its groove
    for sx in (-1, 1):                                                          # the bail lugs and its arc
        m.box("head", 8.5 if sx > 0 else -9.5, -13, -1.5, 1, 5, 3, B.BRASS_D)
    m.box("head", -9.5, -22, -0.5, 19, 1, 1, B.BRASS)                          # the bail over the crucible
    m.box("head", -9.5, -22, -0.5, 1, 10, 1, B.BRASS)
    m.box("head", 8.5, -22, -0.5, 1, 10, 1, B.BRASS)

    # ---- right arm: the heavier, a great iron pauldron, a brass bracer, the forge hammer
    m.box("arm_r", -9, -7, -8, 14, 10, 16, iron_plate(50))                     # pauldron
    m.box("arm_r", -9.5, -8, -6, 6, 2, 12, B.brass(51, rivet_step=3))          # its brass crest
    m.box("arm_r", -5, 2, -5, 10, 13, 10, basalt(52, seams=1), glow=seams_glow(52, 1))
    m.box("fore_r", -5.5, 0, -5.5, 11, 12, 11, basalt(53, seams=2), glow=seams_glow(53, 2))
    m.box("fore_r", -6, 2, -6, 12, 6, 12, B.bands(B.BRASS, B.BRASS_D, every=2, seed=54))      # bracer
    m.box("fore_r", -5, 11, -5, 10, 7, 10, basalt(55))                         # the fist
    m.box("hammer", -2, -8, -2, 4, 30, 4, haft(56))
    m.box("hammer", -2.5, -1, -2.5, 5, 6, 5, leather(57))                      # grip wrap
    m.box("hammer", -6, 20, -9, 12, 11, 18, hammer_head(58), glow=hammer_glow)
    m.box("hammer", -3, 18, -3, 6, 2, 6, B.BRASS_D)                        # the collar into the head

    # ---- left arm: brass pauldron, the tongs held out with a glowing billet
    m.box("arm_l", -4, -5, -6.5, 11, 8, 13, B.brass(60, rivet_step=3))
    m.box("arm_l", -4.5, 2, -4.5, 9, 13, 9, basalt(61, seams=1), glow=seams_glow(61, 1))
    m.box("fore_l", -4.5, 0, -4.5, 9, 12, 9, basalt(62, seams=1), glow=seams_glow(62, 1))
    m.box("fore_l", -5, 1, -5, 10, 4, 10, leather(63))                         # a leather cuff
    m.box("fore_l", -4, 11, -4, 8, 6, 8, basalt(64))                           # the hand
    m.box("tongs", -2.5, -6, -1, 2, 14, 2, tong_iron)                          # the reins
    m.box("tongs", 0.5, -6, -1, 2, 14, 2, tong_iron)
    m.box("tongs", -2, 7, -1.5, 4, 2, 3, B.BRASS_D)                            # the rivet
    m.box("tongs", -2.5, 9, -1, 2, 18, 2, tong_iron)                           # the jaws
    m.box("tongs", 0.5, 9, -1, 2, 18, 2, tong_iron)
    m.box("tongs", -2.5, 25, -3, 5, 4, 6, MAGMA, glow=billet_glow)             # the billet

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 4.0)
    idle.pos("torso", (0, (0, 0, 0)), (2.0, (0, -0.8, 0)), (4.0, (0, 0, 0)))
    idle.rot("torso", (0, (0, 0, 0)), (2.0, (2, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.4, (0, 8, 0)), (2.8, (-3, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (3, 0, -1)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("tongs", (0, (0, 0, 0)), (1.0, (3, 0, 0)), (3.0, (-3, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("bucket", (0, (0, 0, 0)), (2.0, (0, 0, 5)), (4.0, (0, 0, 0)))
    idle.rot("apron", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    for side, ph in (("r", 0.0), ("l", 1.0)):
        a0 = 22 if ph == 0 else -22
        walk.rot(f"leg_{side}", (0, (a0, 0, 0)), (1.0, (-a0, 0, 0)), (2.0, (a0, 0, 0)))
        lift = 0.5 if ph == 0 else 1.5
        keys = [(0, (0, 0, 0)), (lift, (24, 0, 0)), (lift + 0.5, (0, 0, 0)), (2.0, (0, 0, 0))]
        if lift > 0.5:
            keys.insert(1, (lift - 0.5, (0, 0, 0)))
        walk.rot(f"shin_{side}", *keys)
    walk.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -1.4, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.4, 0)), (2.0, (0, 0, 0)))
    walk.rot("pelvis", (0, (0, 0, 3)), (1.0, (0, 0, -3)), (2.0, (0, 0, 3)))
    walk.rot("torso", (0, (0, 4, 0)), (1.0, (0, -4, 0)), (2.0, (0, 4, 0)))
    walk.rot("arm_r", (0, (10, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("arm_l", (0, (-4, 0, 0)), (1.0, (4, 0, 0)), (2.0, (-4, 0, 0)))
    walk.rot("bucket", (0, (0, 0, 8)), (1.0, (0, 0, -8)), (2.0, (0, 0, 8)))

    # slam: the hammer heaved up over its right shoulder (0.9 s = 18 ticks), then brought down in front of it; the
    # anvil cracks in a line ahead
    a = m.anim("slam", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (-160, 0, -6)), (0.9, (-168, 0, -8)), (0.95, (-58, 0, 4), "linear"),
          (1.4, (-56, 0, 4)), (2.0, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (-34, 0, 0)), (0.95, (-6, 0, 0), "linear"), (1.4, (-6, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("hammer", (0, (0, 0, 0)), (0.9, (16, 0, 0)), (0.95, (-30, 0, 0), "linear"), (1.4, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.9, (-16, -14, 0)), (0.95, (20, 8, 0), "linear"), (1.4, (18, 8, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-20, 0, -30)), (0.95, (14, 0, -20), "linear"), (2.0, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.9, (0, 1, 0)), (0.95, (0, -3, 0), "linear"), (1.4, (0, -3, 0)), (2.0, (0, 0, 0)))
    for side, sx in (("r", -1), ("l", 1)):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.9, (-8, 0, -6 * sx)), (0.95, (-18, 0, -8 * sx), "linear"),
              (1.4, (-18, 0, -8 * sx)), (2.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.95, (22, 0, 0), "linear"), (1.4, (22, 0, 0)), (2.0, (0, 0, 0)))

    # combo: hammer forehand at 0.7 s (14 ticks), backhand at 1.2 s, phase 2 an overhead blow at 1.7 s
    a = m.anim("combo", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-70, -50, 70)), (0.7, (-74, -56, 74)), (0.78, (-70, 70, -10), "linear"),
          (1.05, (-72, 76, -14)), (1.2, (-74, -40, 66), "linear"), (1.45, (-130, -10, 20)), (1.6, (-168, 0, -6)),
          (1.7, (-170, 0, -8)), (1.76, (-60, 0, 4), "linear"), (2.1, (-56, 0, 4)), (2.6, (0, 0, 0)))
    a.rot("hammer", (0, (0, 0, 0)), (0.7, (-60, 0, 0)), (1.2, (-60, 0, 0)), (1.7, (16, 0, 0)),
          (1.76, (-30, 0, 0), "linear"), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.7, (0, 34, 0)), (0.78, (6, -36, 0), "linear"), (1.05, (6, -38, 0)),
          (1.2, (6, 30, 0), "linear"), (1.6, (-14, 4, 0)), (1.76, (20, 6, 0), "linear"), (2.1, (18, 6, 0)), (2.6, (0, 0, 0)))
    a.rot("pelvis", (0, (0, 0, 0)), (0.7, (0, 12, 0)), (0.78, (0, -14, 0), "linear"), (1.2, (0, 12, 0), "linear"),
          (1.76, (0, 0, 0), "linear"), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (10, 0, -30)), (1.2, (-10, 0, -30)), (1.76, (14, 0, -20), "linear"),
          (2.6, (0, 0, 0)))

    # grab: the tongs opened and thrust out (0.8 s = 16 ticks), they snap shut ahead of it; whoever is caught is lifted
    # and held up for 0.6 s, then flung away over its shoulder at 1.4 s
    a = m.anim("grab", 2.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.65, (-30, -30, -20)), (0.8, (-36, -34, -22)), (0.85, (-70, 0, -8), "linear"),
          (1.3, (-120, 0, -10)), (1.4, (-150, 40, -30), "linear"), (1.6, (-150, 46, -34)), (2.5, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.85, (20, 0, 0), "linear"), (1.3, (10, 0, 0)), (1.4, (-20, 0, 0)),
          (2.5, (0, 0, 0)))
    a.rot("tongs", (0, (0, 0, 0)), (0.8, (10, 0, 0)), (0.85, (20, 0, 0), "linear"), (1.3, (20, 0, 0)), (1.4, (-20, 0, 0),
          "linear"), (2.5, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.8, (8, 26, 0)), (0.85, (18, -10, 0), "linear"), (1.3, (-6, -6, 0)),
          (1.4, (-10, 40, 0), "linear"), (1.6, (-8, 44, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (20, 0, 20)), (1.4, (-20, 0, 30)), (2.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (-24, 0, 0)), (1.3, (-20, 0, 0)), (2.0, (0, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.3, (16, 0, 0)), (2.0, (0, 0, 0)), (2.5, (0, 0, 0)))

    # splash: it bows its head, the crucible tipped forward (1.0 s = 20 ticks), then jerks it up: molten metal flies
    # from the spout onto the marked tiles
    a = m.anim("splash", 2.2)
    a.rot("head", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (1.0, (34, 0, 0)), (1.08, (-36, 0, 0), "linear"), (1.5, (-30, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.0, (22, 0, 0)), (1.08, (-14, 0, 0), "linear"), (1.5, (-10, 0, 0)),
          (2.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (10, 0, 30)), (1.08, (-30, 0, 40), "linear"), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (10, 0, -30)), (1.08, (-30, 0, -40), "linear"), (2.2, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, -2, 0)), (1.08, (0, 1, 0), "linear"), (1.6, (0, 0, 0)), (2.2, (0, 0, 0)))

    # quench: the billet plunged into the bucket at its hip (0.6 s = 12 ticks), hissing; steam bursts out round it
    a = m.anim("quench", 1.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (30, 0, -4)), (0.6, (34, 0, -2)), (0.66, (-30, 0, -50), "linear"),
          (0.9, (-28, 0, -48)), (1.4, (0, 0, 0)))
    a.rot("tongs", (0, (0, 0, 0)), (0.6, (70, 0, 0)), (0.66, (20, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.6, (20, 0, -10)), (0.66, (-8, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (10, 0, 10)), (0.66, (-30, 0, 50), "linear"), (0.9, (-28, 0, 48)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (16, 0, 0)), (0.66, (-20, 0, 0), "linear"), (1.4, (0, 0, 0)))

    # charge: head down, hammer dragged behind it (0.8 s = 16 ticks), it barrels forward 0.6 s, then swings the hammer
    # up through you at 1.4 s
    a = m.anim("charge", 2.4)
    a.rot("torso", (0, (0, 0, 0)), (0.8, (24, 0, 0)), (0.85, (30, 0, 0), "linear"), (1.3, (30, 0, 0)),
          (1.4, (-16, -20, 0), "linear"), (1.7, (-14, -22, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (40, 0, 20)), (1.3, (44, 0, 20)), (1.4, (-150, 0, 10), "linear"),
          (1.7, (-146, 0, 10)), (2.4, (0, 0, 0)))
    a.rot("hammer", (0, (0, 0, 0)), (0.8, (40, 0, 0)), (1.3, (40, 0, 0)), (1.4, (-30, 0, 0), "linear"), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-40, 0, -10)), (1.3, (-40, 0, -10)), (2.4, (0, 0, 0)))
    for side, ph in (("r", 0), ("l", 1)):
        a.rot(f"leg_{side}", (0, (0, 0, 0)), (0.8, (-10 if ph else 20, 0, 0)), (0.95, (30 if ph else -30, 0, 0)),
              (1.1, (-30 if ph else 30, 0, 0)), (1.25, (30 if ph else -30, 0, 0)), (1.4, (0, 0, 0)), (2.4, (0, 0, 0)))

    # quake (phase 2): hammer and tongs raised together (1.0 s = 20 ticks), the hammer slams at 1.0 s, the tongs-fist at
    # 1.6 s: two shockwaves to jump
    a = m.anim("quake", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-160, 0, -4)), (1.0, (-166, 0, -6)), (1.05, (-56, 0, 4), "linear"),
          (1.6, (-50, 0, 10)), (2.0, (-50, 0, 10)), (2.6, (0, 0, 0)))
    a.rot("hammer", (0, (0, 0, 0)), (1.0, (16, 0, 0)), (1.05, (-30, 0, 0), "linear"), (2.0, (-30, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-120, 0, -10)), (1.45, (-164, 0, -4)), (1.6, (-170, 0, -6)),
          (1.65, (-60, 0, -4), "linear"), (2.0, (-58, 0, -4)), (2.6, (0, 0, 0)))
    a.rot("tongs", (0, (0, 0, 0)), (1.6, (40, 0, 0)), (1.65, (-20, 0, 0), "linear"), (2.6, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (1.0, (-16, -8, 0)), (1.05, (18, -8, 0), "linear"), (1.45, (-12, 8, 0)),
          (1.6, (-16, 10, 0)), (1.65, (22, 8, 0), "linear"), (2.0, (20, 8, 0)), (2.6, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.05, (0, -3, 0), "linear"), (1.6, (0, 0, 0)),
          (1.65, (0, -3, 0), "linear"), (2.0, (0, -3, 0)), (2.6, (0, 0, 0)))

    # billet (phase 2): the billet swung back over its left shoulder in the tongs (0.9 s = 18 ticks), then hurled
    a = m.anim("billet", 1.9)
    a.rot("arm_l", (0, (0, 0, 0)), (0.75, (-170, 20, -10)), (0.9, (-176, 24, -12)), (0.96, (-60, -10, -10), "linear"),
          (1.3, (-56, -10, -10)), (1.9, (0, 0, 0)))
    a.rot("tongs", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (0.96, (-10, 0, 0), "linear"), (1.9, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.9, (-14, -26, 0)), (0.96, (16, 20, 0), "linear"), (1.3, (14, 20, 0)), (1.9, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (20, 0, 30)), (0.96, (-20, 0, 20), "linear"), (1.9, (0, 0, 0)))

    # titan: it raises the hammer to the titan above and beats it on the tongs three times (2.0 s = 40 ticks: the
    # signal), then flings both arms wide as the titan's hammer comes down
    a = m.anim("titan", 3.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-178, 0, -10)), (0.6, (-150, 0, 20)), (0.8, (-178, 0, -10)), (1.0, (-150, 0, 20)),
          (1.2, (-178, 0, -10)), (1.4, (-150, 0, 20)), (1.9, (-176, 0, -10)), (2.0, (-178, 0, -12)),
          (2.08, (-60, 0, 80), "linear"), (2.5, (-58, 0, 76)), (3.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-150, 0, -24)), (1.4, (-150, 0, -24)), (2.0, (-160, 0, -16)),
          (2.08, (-60, 0, -80), "linear"), (2.5, (-58, 0, -76)), (3.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-40, 0, 0)), (2.0, (-44, 0, 0)), (2.08, (10, 0, 0), "linear"), (2.6, (6, 0, 0)),
          (3.3, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.4, (-24, 0, 0)), (2.0, (-26, 0, 0)), (2.08, (8, 0, 0), "linear"), (3.3, (0, 0, 0)))

    # overheat (phase 3, invulnerable): it drops to one knee and drinks the crucible, head thrown back (1.5 s = 30
    # ticks), then rises, arms wide, glowing
    a = m.anim("overheat", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -8, 0)), (1.5, (0, -8, 0)), (1.6, (0, -1, 0), "linear"), (2.8, (0, -1, 0)),
          (3.5, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (-70, 0, 0)), (1.5, (-70, 0, 0)), (1.6, (-8, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (70, 0, 0)), (1.5, (70, 0, 0)), (1.6, (8, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (1.5, (20, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (60, 0, 0)), (1.5, (60, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-50, 0, 0)), (1.5, (-54, 0, 0)), (1.6, (10, 0, 0), "linear"), (2.8, (6, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.5, (-22, 0, 0)), (1.6, (-28, 0, 0), "linear"), (2.8, (-24, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-20, 0, 40)), (1.5, (-24, 0, 40)), (1.6, (-50, 0, 80), "linear"),
          (2.8, (-48, 0, 76)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-20, 0, -40)), (1.5, (-24, 0, -40)), (1.6, (-50, 0, -80), "linear"),
          (2.8, (-48, 0, -76)), (3.5, (0, 0, 0)))
    a.scale("torso", (0, (1, 1, 1)), (1.5, (1.04, 1.03, 1.04)), (1.6, (1.08, 1.06, 1.08), "linear"), (2.8, (1.06, 1.04, 1.06)),
            (3.5, (1, 1, 1)))

    # vent (phase 3): it hunches, arms locked over its chest while the crucible boils over (2.0 s = 40 ticks), then
    # throws itself open: a radial blast of slag-steam
    a = m.anim("vent", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.5, (0, -4, 0)), (2.0, (0, -4, 0)), (2.06, (0, 1, 0), "linear"), (2.8, (0, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (22, 0, 0)), (2.0, (26, 0, 0)), (2.06, (-26, 0, 0), "linear"), (2.8, (-22, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.0, (16, 6, 0)), (1.5, (20, -6, 0)), (2.0, (22, 0, 0)),
          (2.06, (-36, 0, 0), "linear"), (2.8, (-30, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-60, -40, -30)), (2.0, (-64, -44, -30)), (2.06, (-40, 0, 90), "linear"),
          (2.8, (-38, 0, 86)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-60, 40, 30)), (2.0, (-64, 44, 30)), (2.06, (-40, 0, -90), "linear"),
          (2.8, (-38, 0, -86)), (3.5, (0, 0, 0)))
    a.scale("torso", (0, (1, 1, 1)), (1.9, (1.06, 1.04, 1.06)), (2.0, (1.08, 1.05, 1.08)), (2.06, (0.96, 0.97, 0.96), "linear"),
            (2.5, (1, 1, 1)), (3.5, (1, 1, 1)))

    # roar (phase two): hammer and tongs raised, head thrown back, the crucible spilling over
    a = m.anim("roar", 2.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-150, 0, 30)), (1.6, (-154, 0, 32)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-150, 0, -30)), (1.6, (-154, 0, -32)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.6, (-36, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-22, 0, 0)), (1.6, (-20, 0, 0)), (2.0, (0, 0, 0)))
    a.scale("torso", (0, (1, 1, 1)), (0.5, (1.05, 1.04, 1.05)), (1.6, (1.05, 1.04, 1.05)), (2.0, (1, 1, 1)))

    # stagger: a knee buckles, the hammer's head on the floor, the crucible lolling
    a = m.anim("stagger", 2.0)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.6, (-40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.3, (10, 0, 8)), (1.6, (12, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, -14)), (1.6, (22, 0, -14)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (20, 0, 10)), (1.6, (22, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (1.6, (12, 0, -10)), (2.0, (0, 0, 0)))
