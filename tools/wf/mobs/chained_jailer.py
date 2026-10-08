"""The Chained Jailer (Le Geôlier enchaîné): warden of the Chained Bastion's prison, about 5.4 blocks tall.

Silhouette idea: a hunched, hulking jailer of blackstone and gilded iron, bound to his own prison. His head is a
locked iron birdcage with a fire burning inside it (two white-hot eyes in the flames), his barrel chest is a cuirass
whose heart is a great gilded padlock with a glowing keyhole, lava cracks running through the plates, a chain
bandolier across it. Strong asymmetry: a gibbet post rises from his back over the left shoulder and a small hanging
cage swings from it with a burning skull inside; the RIGHT fist drags a long chain ending in a spiked, burning
fetter-ball that rests on the floor; the LEFT arm ends in an oversized gauntlet with a broken shackle cuff, the
snapped chain dangling. A ring of great gold keys hangs at his left hip, and broken shackles grip both ankles.
"""
import functools
import random

from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B

BLACK = (46, 40, 48)            # blackstone
BLACK_L = (78, 70, 80)
BLACK_D = (26, 22, 28)
GILD = (226, 172, 58)
GILD_L = (255, 224, 126)
GILD_D = (150, 104, 30)
CHAIN = (118, 114, 124)
CHAIN_L = (176, 172, 182)
CHAIN_D = (62, 58, 68)
EMBER = (255, 124, 32)
EMBER_L = (255, 222, 132)
EMBER_D = (196, 54, 16)
CLOTH = (116, 28, 24)
CLOTH_D = (72, 16, 16)
LEATHER = (74, 46, 34)


# ---------------------------------------------------------------- paint
@functools.lru_cache(maxsize=None)
def _cracks(w, h, seed, count):
    """Pixels of a few jagged lava cracks running down a w x h face (random walks)."""
    rnd = random.Random(seed * 7919 + w * 131 + h)
    out = set()
    for _ in range(count):
        x = rnd.randint(1, max(1, w - 2))
        y = rnd.randint(0, max(0, h // 3))
        for _ in range(int(h * (0.45 + rnd.random() * 0.4))):
            out.add((x, y))
            y += 1
            x = max(1, min(w - 2, x + rnd.choice((-1, 0, 0, 1))))
            if rnd.random() < 0.15:                       # a short side branch
                out.add((max(0, min(w - 1, x + rnd.choice((-1, 1)))), y))
    return frozenset(out)


def stone(seed=0, cracks=0):
    """Blackstone: mottled near-black stone with lighter flecks, lit top, dark underside; optional lava cracks."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BLACK_D
        if cracks and face in ("front", "back", "left", "right") and (x, y) in _cracks(w, h, seed, cracks):
            return EMBER_D
        k = 1.06 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.18
        c = mul(BLACK, k)
        if B.n(x // 2, y // 2, seed + 5) < 0.12:
            c = mix(c, BLACK_L, 0.6)
        if face == "top":
            c = mul(c, 1.15)
        return c
    return f


def cracks_glow(seed=0, cracks=2):
    def f(face, x, y, w, h):
        if face in ("front", "back", "left", "right") and (x, y) in _cracks(w, h, seed, cracks):
            return EMBER if B.n(x, y, seed + 1) < 0.6 else EMBER_L
        return None
    return f


def gplate(seed=0, cracks=0):
    """A blackstone plate rimmed with gold: bright top row, darker gold rim, rivets in the corners."""
    inner = stone(seed, cracks)

    def f(face, x, y, w, h):
        if face == "bottom":
            return GILD_D
        if face == "top":
            return GILD if (x in (0, w - 1) or y in (0, h - 1)) else inner(face, x, y, w, h)
        if w > 2 and h > 2:
            if y == 0:
                return GILD_L
            if x in (0, w - 1) or y == h - 1:
                return GILD_D
            if w > 5 and h > 5 and y in (1, h - 2) and x in (1, w - 2):
                return GILD
        return inner(face, x, y, w, h)
    return f


def link(seed=0, hot=0.0):
    """A chain link: worn grey iron, bright top edge; ``hot`` > 0 tints it toward glowing ember."""
    base = mix(CHAIN, EMBER_D, hot)
    return B.plate(mix(CHAIN_L, EMBER, hot), CHAIN_D, mix((226, 224, 230), EMBER_L, hot), seed=seed, grad=0.12)


def mail(seed=0):
    """Chain mail: rows of tiny rings, dark gaps."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return CHAIN_D
        if (x + (y // 2) % 2) % 2 == 0 and y % 2 == 0:
            return CHAIN_D
        return mul(CHAIN if y % 2 else CHAIN_L, 1.0 - 0.25 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def iron(seed=0):
    return B.plate(CHAIN_D, BLACK_D, CHAIN, rivet=GILD, seed=seed)


def cloth(seed=0):
    """The tabard: dark red cloth, gold border down the sides, a ragged hem and a sigil of three prison bars."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return CLOTH_D
        if y == h - 1 and B.n(x, 0, seed) < 0.5:
            return None                                    # ragged hem
        if face == "front" and w >= 8:
            if x in (0, w - 1):
                return GILD_D
            cx = (w - 1) / 2
            if 3 <= y <= 9 and abs(x - cx) <= 2.6 and (round(x - cx + 2.5) % 2 == 0 or y in (3, 9)):
                return GILD                                # three bars in a frame
        k = 1.04 - 0.25 * y / max(1, h) + (0.06 if x % 3 == 1 else 0.0) + (B.n(x, y, seed) - 0.5) * 0.06
        return mul(CLOTH, k)
    return f


def chest_paint(f, x, y, w, h):
    """The cuirass: blackstone plates with gilded edges and lava cracks; in front, over the heart, a great gilded
    padlock (shackle arc on top, a glowing keyhole in its body)."""
    if f == "bottom":
        return BLACK_D
    if f != "front":
        return gplate(70, cracks=2)(f, x, y, w, h)
    cx = (w - 1) / 2
    dx = x - cx
    # padlock: shackle (an arch of gold) and a body
    if 4 <= y <= 8 and 2.5 <= abs(dx) <= 4.5 or y == 3 and abs(dx) <= 3.5:
        return GILD_L if y <= 4 else GILD
    if 9 <= y <= 17 and abs(dx) <= 5.5:
        if abs(dx) > 4.5 or y in (9, 17):
            return GILD_D
        if abs(dx) <= 0.6 and 13 <= y <= 15 or y in (11, 12) and abs(dx) <= 1.1:
            return EMBER                                    # keyhole
        return GILD_L if y == 10 else mul(GILD, 1.05 - 0.1 * (y - 9) / 8)
    if y == 0:
        return GILD_L
    if abs(abs(dx) - (w / 2 - 2.5)) < 0.6:
        return GILD_D                                      # plate seams
    if (x, y) in _cracks(w, h, 71, 3) and abs(dx) > 6:
        return EMBER_D
    return stone(72)(f, x, y, w, h)


def chest_glow(f, x, y, w, h):
    if f != "front":
        return cracks_glow(70, 2)(f, x, y, w, h) if f in ("back", "left", "right") else None
    cx = (w - 1) / 2
    dx = x - cx
    if 9 < y < 17 and (abs(dx) <= 0.6 and 13 <= y <= 15 or y in (11, 12) and abs(dx) <= 1.1):
        return EMBER_L
    if (x, y) in _cracks(w, h, 71, 3) and abs(dx) > 6 and abs(abs(dx) - (w / 2 - 2.5)) >= 0.6 and y > 0:
        return EMBER
    return None


def fire_face(f, x, y, w, h):
    """The fire inside the cage helm: embers dark at the top, white-hot at the bottom; two eyes and a mouth."""
    if f == "top":
        return EMBER_D
    if f == "bottom":
        return EMBER_L
    t = y / max(1, h - 1)
    c = mix(mix(BLACK_D, EMBER_D, 0.6), EMBER, t) if t < 0.75 else mix(EMBER, EMBER_L, (t - 0.75) * 4)
    if f == "front":
        if y == 3 and x in (1, 2, w - 3, w - 2):
            return (255, 250, 230)
        if y == 2 and x in (1, 2, w - 3, w - 2):
            return BLACK_D                                 # brow shadow
        if y == 6 and 2 <= x <= w - 3:
            return EMBER_L
    if B.n(x, y, 81) < 0.15:
        c = mul(c, 0.75)
    return c


def fire_glow(f, x, y, w, h):
    if f == "top":
        return None
    if f == "front" and y == 3 and x in (1, 2, w - 3, w - 2):
        return (255, 250, 230)
    if f == "front" and y == 6 and 2 <= x <= w - 3:
        return EMBER_L
    if y >= h * 0.45:
        return EMBER if B.n(x, y, 82) < 0.7 else EMBER_L
    return None


def skull_fire(f, x, y, w, h):
    """The burning skull in the gibbet cage: bone face, dark sockets, flames licking up."""
    if f == "front":
        if y in (2, 3) and x in (1, w - 2):
            return EMBER_L
        if y == 5 and x % 2 == 0:
            return BLACK_D
        return (214, 200, 170) if y < 5 else (176, 160, 130)
    if y >= h - 2:
        return EMBER
    return (196, 182, 152)


def skull_glow(f, x, y, w, h):
    if f == "front" and y in (2, 3) and x in (1, w - 2):
        return EMBER_L
    if y >= h - 2:
        return EMBER
    return None


def key_paint(f, x, y, w, h):
    if f == "bottom":
        return GILD_D
    return GILD_L if x == 0 and y < h // 2 else (GILD if y < h - 2 else GILD_D)


def ring_paint(f, x, y, w, h):
    """The key ring, seen from the side: a hollow gold ring."""
    if f in ("left", "right"):
        if 1 <= x <= w - 2 and 1 <= y <= h - 2:
            return None
        return GILD_L if y == 0 else GILD
    return GILD_D


# ---------------------------------------------------------------- helpers
def chain(m, part, n, y0=0.0, step=3, seed=0, hot=0.0):
    """``n`` alternating links hanging down from ``y0`` (flat 3x3x1 then edge-on 1x3x2)."""
    for k in range(n):
        h = hot * k / max(1, n - 1)
        if k % 2 == 0:
            m.box(part, -1.5, y0 + k * step, -0.5, 3, step + 1, 1, link(seed + k, h))
        else:
            m.box(part, -0.5, y0 + k * step, -1, 1, step + 1, 2, link(seed + k, h))


def bars(m, part, x0, x1, z0, z1, y0, h, xs, zs, seed=0):
    """Vertical 1x1 cage bars along the rectangle x0..x1 / z0..z1."""
    for x in xs:
        for z in (z0, z1):
            m.box(part, x, y0, z, 1, h, 1, B.rod(CHAIN_D, seed))
    for z in zs:
        for x in (x0, x1):
            m.box(part, x, y0, z, 1, h, 1, B.rod(CHAIN_D, seed + 1))


def build():
    m = Model("chained_jailer", seed=131, shadow=2.0, walk_speed=0.7, walk_scale=0.9)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -32, 0))
    m.part("tabard", "pelvis", pivot=(0, 2, -7.5), rot=(-4, 0, 0))
    m.part("tabard_b", "pelvis", pivot=(0, 2, 7.5), rot=(6, 0, 0))
    m.part("keys", "pelvis", pivot=(13, 1, 0), rot=(0, 0, -6))
    m.part("waist", "pelvis", pivot=(0, -4, 0))
    m.part("chest", "waist", pivot=(0, -6, 0), rot=(20, 0, 0))
    m.part("sash", "chest", pivot=(9, -12, -8), rot=(0, 0, 32))
    m.part("head", "chest", pivot=(0, -24, -5), rot=(-20, 0, 0))
    m.part("post", "chest", pivot=(9, -20, 7), rot=(-10, 0, 0))
    m.part("gibbet", "post", pivot=(0, -24, 10), rot=(10, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(7 * sx, 0, 0), rot=(0, 0, -5 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 15, 0), rot=(0, 0, 5 * sx))
    m.part("arm_r", "chest", pivot=(-18, -20, 0), rot=(-14, 0, 10))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-24, 0, -4))
    m.part("chain_r", "fore_r", pivot=(0, 18, 0), rot=(30, 0, 0))
    m.part("chain_r2", "chain_r", pivot=(0, 12, 0), rot=(-8, 0, 0))
    m.part("ball", "chain_r2", pivot=(0, 9, 0))
    m.part("arm_l", "chest", pivot=(18, -20, 0), rot=(-6, 0, -12))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-18, 0, 6))
    m.part("chain_l", "fore_l", pivot=(0, 6, 6.5), rot=(20, 0, 0))

    # ---- legs: blackstone greaves with gilded knee cops, broken shackles round the ankles
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -5, -2, -5, 10, 17, 10, mail(2 + (sx > 0)))
        m.box(th, -5.5, 1, -5.5, 11, 9, 2, gplate(4 + (sx > 0)))                       # tasset
        m.box(sh, -5.5, -2, -6.5, 11, 6, 4, gplate(6 + (sx > 0)))                      # knee cop
        m.box(sh, -5, 0, -5, 10, 13, 10, stone(8 + (sx > 0), cracks=1), glow=cracks_glow(8 + (sx > 0), 1))
        m.box(sh, -6, 8, -6, 12, 3, 12, iron(10))                                      # ankle shackle
        m.box(sh, -6.5, 13, -8.5, 13, 4, 14, gplate(11))                               # sabaton
        m.box(sh, -5.5, 14, -9.5, 11, 3, 1, GILD_D)                                    # toe cap
        # a snapped chain hanging off the shackle behind
        m.box(sh, -1.5 + 3 * sx, 11, 6, 3, 3, 1, link(12))
        m.box(sh, -0.5 + 3 * sx, 13, 5.5, 1, 3, 2, link(13))

    # ---- pelvis, belt with a padlock buckle, the tabard, the key ring
    m.box("pelvis", -11, -4, -7, 22, 7, 14, gplate(14))
    m.box("pelvis", -13, -1, -6, 3, 11, 12, gplate(15))
    m.box("pelvis", 10, -1, -6, 3, 11, 12, gplate(16))
    m.box("waist", -11.5, -5, -8, 23, 5, 16, B.bands(LEATHER, GILD_D, every=5, seed=17))
    m.box("waist", -2.5, -6, -8.8, 5, 6, 1, GILD, glow={"front": lambda f, x, y, w, h: EMBER if (x == 2 and y in (3, 4)) else None})
    m.box("tabard", -5, 0, -1, 10, 20, 1, cloth(18))
    m.box("tabard_b", -6, 0, 0, 12, 18, 1, cloth(19))
    m.box("keys", -0.5, 0, -3, 1, 7, 7, ring_paint)
    for i, (z, ln) in enumerate(((-3, 8), (-0.5, 10), (2, 7))):
        m.box("keys", -0.5, 5, z, 1, ln, 1, key_paint)
        m.box("keys", -0.5, 4 + ln, z - 1 if i != 1 else z + 1, 1, 2, 1 if i else 2, key_paint)    # bit

    # ---- the cuirass: padlock heart, lava cracks, gilded yoke, the chain bandolier
    m.box("chest", -14, -24, -8, 28, 24, 16, chest_paint, glow=chest_glow)
    m.box("chest", -15, -25, -6, 30, 3, 12, gplate(20))                               # shoulder yoke
    m.box("chest", -7, -26, -9, 14, 4, 4, gplate(21))                                 # gorget
    m.box("chest", -10, -20, 8, 20, 16, 2, stone(22, cracks=2), glow=cracks_glow(22, 2))   # back plate
    for k in range(9):
        y = -14 + k * 3
        if k % 2 == 0:
            m.box("sash", -2, y, -1, 4, 4, 1, link(23 + k))
        else:
            m.box("sash", -0.5, y, -1.5, 1, 4, 2, link(23 + k))

    # ---- head: the fire inside a locked birdcage helm, a crown of gold spikes, a hook on top
    m.box("head", -5, -10, -5, 10, 10, 10, fire_face, glow=fire_glow)
    m.box("head", -6, -1, -6, 12, 2, 12, gplate(30))                                  # collar
    m.box("head", -6, -12, -6, 12, 1, 12, iron(31))                                   # cage roof
    m.box("head", -4, -13, -4, 8, 1, 8, iron(32))
    m.box("head", -1, -16, -0.5, 2, 3, 1, GILD)                                       # hanging ring
    bars(m, "head", -6, 5, -6, 5, -11, 10, (-6, -3, 2, 5), (-3, 2), seed=33)
    m.box("head", -6, -7, -6.5, 12, 1, 1, iron(34))                                   # cross band
    m.box("head", -1.5, -7.5, -7, 3, 3, 1, GILD, glow={"front": lambda f, x, y, w, h: EMBER if x == 1 and y == 1 else None})
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box("head", 5.5 * sx - 0.5, -14, 5.5 * sz - 0.5, 1, 2, 1, GILD_L)        # spikes

    # ---- the gibbet: a post rising from his back, a beam reaching back, a cage with a burning skull
    m.box("post", -1.5, -24, -1.5, 3, 27, 3, B.rod(CHAIN_D, 40))
    m.box("post", -1.5, -27, -1.5, 3, 3, 13, iron(41))                                # beam
    m.box("post", -1, -24, 4, 2, 2, 5, B.rod(CHAIN_D, 42))                            # brace
    m.box("post", -2, -28, -2, 4, 1, 4, GILD)
    chain(m, "gibbet", 2, 0, step=3, seed=43)
    m.box("gibbet", -4, 6, -4, 8, 1, 8, iron(45))
    m.box("gibbet", -1, 5, -1, 2, 1, 2, GILD)
    bars(m, "gibbet", -4, 3, -4, 3, 7, 9, (-4, -1, 3), (-1, 1), seed=46)
    m.box("gibbet", -4, 16, -4, 8, 1, 8, iron(47))
    m.box("gibbet", -2.5, 9, -2.5, 5, 6, 5, skull_fire, glow=skull_glow)

    # ---- right arm: spiked pauldron, mail sleeve, gilded bracer and fist; the chain and its burning fetter-ball
    m.box("arm_r", -9, -7, -7, 13, 9, 14, gplate(50, cracks=1), glow=cracks_glow(50, 1))
    m.box("arm_r", -7, -10, -4, 2, 3, 2, GILD_L)                                        # pauldron spikes
    m.box("arm_r", -7, -10, 2, 2, 3, 2, GILD_L)
    m.box("arm_r", -4.5, 0, -4.5, 9, 13, 9, mail(51))
    m.box("fore_r", -5, 0, -5, 10, 12, 10, gplate(52))
    m.box("fore_r", -4.5, 12, -4.5, 9, 6, 9, iron(53))                                 # fist
    m.box("fore_r", -5, 14, -5.5, 10, 2, 1, GILD)                                      # knuckle bar
    chain(m, "chain_r", 4, 0, step=3, seed=54)
    chain(m, "chain_r2", 3, 0, step=3, seed=58, hot=0.6)
    m.box("ball", -4, 0, -4, 8, 8, 8, stone(61, cracks=3), glow=cracks_glow(61, 3))
    m.box("ball", -4.5, 3, -4.5, 9, 2, 9, GILD_D)
    m.box("ball", -1.5, -1, -1.5, 3, 1, 3, GILD)                                       # collar
    for (x, y, z) in ((-1, 3, -6), (-1, 3, 4), (-6, 3, -1), (4, 3, -1), (-1, 8, -1)):
        m.box("ball", x, y, z, 2, 2, 2, GILD_L)                                          # spikes
    for (x, y, z) in ((-5, 0, -5), (3, 0, -5), (-5, 6, 3), (3, 6, 3), (-5, 6, -5), (3, 0, 3)):
        m.box("ball", x, y, z, 2, 2, 2, CHAIN_L)

    # ---- left arm: pauldron, mail, the oversized gauntlet with a broken shackle cuff and its dangling chain
    m.box("arm_l", -4, -7, -7, 13, 9, 14, gplate(62, cracks=1), glow=cracks_glow(62, 1))
    m.box("arm_l", -4.5, 0, -4.5, 9, 13, 9, mail(63))
    m.box("fore_l", -6, 0, -6, 12, 12, 12, gplate(64, cracks=2), glow=cracks_glow(64, 2))
    m.box("fore_l", -6.5, 4, -6.5, 13, 3, 13, iron(65))                                # shackle cuff
    m.box("fore_l", -6, 12, -6.5, 12, 9, 12, iron(66))                                 # gauntlet fist
    m.box("fore_l", -6.5, 14, -7, 13, 3, 1, GILD)                                      # knuckles
    m.box("fore_l", -6.5, 18, -7, 13, 2, 1, GILD_D)
    chain(m, "chain_l", 4, 0, step=3, seed=67)

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 4.0)
    idle.pos("chest", (0, (0, 0, 0)), (2.0, (0, 0.9, 0)), (4.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (0, 8, 0)), (2.4, (0, 8, 0)), (3.2, (0, -6, 0)), (4.0, (0, 0, 0)))
    idle.rot("gibbet", (0, (0, 0, 0)), (1.0, (6, 0, 3)), (2.0, (0, 0, 0)), (3.0, (-6, 0, -3)), (4.0, (0, 0, 0)))
    idle.rot("chain_r", (0, (0, 0, 0)), (2.0, (3, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("chain_l", (0, (0, 0, 0)), (1.5, (8, 0, 0)), (3.0, (-4, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("keys", (0, (0, 0, 0)), (2.0, (4, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("tabard", (0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.8)
    walk.rot("thigh_r", (0, (22, 0, 0)), (0.9, (-22, 0, 0)), (1.8, (22, 0, 0)))
    walk.rot("thigh_l", (0, (-22, 0, 0)), (0.9, (22, 0, 0)), (1.8, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.45, (28, 0, 0)), (0.9, (0, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (1.35, (28, 0, 0)), (1.8, (0, 0, 0)))
    walk.rot("arm_l", (0, (-10, 0, 0)), (0.9, (10, 0, 0)), (1.8, (-10, 0, 0)))
    walk.rot("chain_r", (0, (12, 0, 0)), (0.9, (24, 0, 0)), (1.8, (12, 0, 0)))      # the ball drags behind
    walk.rot("chest", (0, (0, 5, 0)), (0.9, (0, -5, 0)), (1.8, (0, 5, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -1.2, 0)), (0.9, (0, 0, 0)), (1.35, (0, -1.2, 0)), (1.8, (0, 0, 0)))
    walk.rot("gibbet", (0, (8, 0, 0)), (0.45, (-6, 0, 0)), (0.9, (8, 0, 0)), (1.35, (-6, 0, 0)), (1.8, (8, 0, 0)))
    walk.rot("keys", (0, (0, 0, 8)), (0.9, (0, 0, -8)), (1.8, (0, 0, 8)))

    # lash: the chain is drawn back and out to his right (0.9 s = 18 ticks), then swung flat across his front
    a = m.anim("lash", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.75, (10, 40, 70)), (0.9, (12, 45, 75)), (1.05, (-85, -55, 15), "linear"),
          (1.3, (-80, -60, 15)), (1.8, (0, 0, 0)))
    a.rot("chain_r", (0, (0, 0, 0)), (0.9, (40, 0, 30)), (1.05, (-60, 0, 30), "linear"), (1.3, (-50, 0, 20)),
          (1.8, (0, 0, 0)))
    a.rot("chain_r2", (0, (0, 0, 0)), (0.9, (20, 0, 0)), (1.05, (-20, 0, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, 35, 0)), (1.05, (0, -35, 0), "linear"), (1.3, (0, -38, 0)), (1.8, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.9, (0, 10, 0)), (1.05, (0, -10, 0), "linear"), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-30, 0, -20)), (1.05, (10, 0, 10), "linear"), (1.8, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.9, (-14, 0, 6)), (1.8, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (12, 0, -4)), (1.8, (0, 0, 0)))

    # hook: the chain is wound back over his shoulder (0.8 s = 16 ticks), hurled straight ahead, then yanked back
    a = m.anim("hook", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.65, (-150, 0, 15)), (0.8, (-160, 0, 15)), (0.88, (-80, 0, 0), "linear"),
          (1.05, (-80, 0, 0)), (1.25, (-20, 0, 10)), (1.7, (0, 0, 0)))
    a.rot("chain_r", (0, (0, 0, 0)), (0.8, (60, 0, 0)), (0.88, (-30, 0, 0), "linear"), (1.05, (-30, 0, 0)),
          (1.25, (40, 0, 0)), (1.7, (0, 0, 0)))
    a.scale("chain_r", (0, (1, 1, 1)), (0.8, (1, 1, 1)), (0.88, (1, 2.2, 1), "linear"), (1.05, (1, 2.2, 1)),
            (1.25, (1, 1, 1)), (1.7, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-12, -20, 0)), (0.88, (14, 10, 0), "linear"), (1.05, (14, 10, 0)),
          (1.25, (-10, -10, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-40, 0, -20)), (1.25, (10, 0, -10)), (1.7, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (16, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.8, (-18, 0, 0)), (1.7, (0, 0, 0)))

    # slam: both fists heaved overhead (1.1 s = 22 ticks), brought down together in front; fire bursts from the floor
    a = m.anim("slam", 2.05)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.95, (-165, 0, -18 * sx)), (1.1, (-170, 0, -20 * sx)),
              (1.2, (-60, 0, -8 * sx), "linear"), (1.6, (-62, 0, -8 * sx)), (2.05, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-26, 0, -8 * sx), "linear"),
              (1.6, (-24, 0, -8 * sx)), (2.05, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (40, 0, 0), "linear"), (1.6, (38, 0, 0)),
              (2.05, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (-30, 0, 0), "linear"), (2.05, (0, 0, 0)))
    a.rot("chain_r", (0, (0, 0, 0)), (1.1, (40, 0, 0)), (1.2, (-50, 0, 0), "linear"), (1.6, (-40, 0, 0)), (2.05, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.2, (26, 0, 0), "linear"), (1.6, (22, 0, 0)), (2.05, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-10, 0, 0)), (1.2, (-14, 0, 0), "linear"), (2.05, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1.5, 0)), (1.2, (0, -4, 0), "linear"), (1.6, (0, -3.5, 0)), (2.05, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (1.1, (-14, 0, 0)), (1.25, (24, 0, 0)), (1.6, (-10, 0, 0)), (2.05, (0, 0, 0)))

    # shackles: the gauntlet raised high, its broken chain rattling (0.9 s = 18 ticks), then swept down palm-first
    # over the floor: chains burst up under his prisoners and hold them while he grinds his fist down
    a = m.anim("shackles", 2.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-160, 0, -10)), (0.7, (-150, 0, -14)), (0.8, (-162, 0, -8)),
          (0.9, (-155, 0, -10)), (0.98, (-45, 0, -45), "linear"), (1.9, (-48, 0, -42)), (2.5, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (0.98, (-50, 0, 0), "linear"), (1.9, (-50, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("chain_l", (0, (0, 0, 0)), (0.6, (-30, 0, 20)), (0.7, (30, 0, -20)), (0.8, (-30, 0, 20)), (0.9, (20, 0, -10)),
          (0.98, (60, 0, 0), "linear"), (1.9, (50, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-14, 10, 0)), (0.98, (22, -12, 0), "linear"), (1.9, (20, -10, 0)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (0.98, (10, 0, 0), "linear"), (1.9, (8, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("keys", (0, (0, 0, 0)), (0.6, (0, 0, 20)), (0.7, (0, 0, -20)), (0.8, (0, 0, 20)), (0.9, (0, 0, -10)),
          (1.2, (0, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-20, 0, 30)), (1.9, (10, 0, 20)), (2.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.98, (-30, 0, 0), "linear"), (1.9, (-28, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.98, (30, 0, 0), "linear"), (1.9, (28, 0, 0)), (2.5, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (0.98, (0, -2.5, 0), "linear"), (1.9, (0, -2.5, 0)), (2.5, (0, 0, 0)))

    # kick: the right foot drawn back (0.6 s = 12 ticks), then a heavy front kick that shoves huggers away
    a = m.anim("kick", 1.25)
    a.rot("thigh_r", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (0.6, (26, 0, 0)), (0.68, (-85, 0, 0), "linear"),
          (0.85, (-80, 0, 0)), (1.25, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.5, (60, 0, 0)), (0.6, (62, 0, 0)), (0.68, (0, 0, 0), "linear"),
          (0.85, (5, 0, 0)), (1.25, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (6, 0, 0)), (0.68, (-16, 0, 0), "linear"), (0.85, (-14, 0, 0)), (1.25, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.6, (-6, 0, 0)), (0.68, (10, 0, 0), "linear"), (1.25, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-20, 0, -20 * sx)), (0.68, (10, 0, -30 * sx), "linear"),
              (1.25, (0, 0, 0)))

    # whirl (phase 2): the chain paid out to his side (0.7 s = 14 ticks), then the burning ball spun round him for 2 s
    a = m.anim("whirl", 3.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-10, 0, 80)), (0.7, (-10, 0, 85)), (2.7, (-10, 0, 85)), (3.4, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (24, 0, 4)), (2.7, (24, 0, 4)), (3.4, (0, 0, 0)))
    a.rot("chain_r", (0, (0, 0, 0)), (0.7, (-30, 0, 10)), (2.7, (-30, 0, 10)), (3.4, (0, 0, 0)))
    a.scale("chain_r", (0, (1, 1, 1)), (0.7, (1, 1.6, 1)), (2.7, (1, 1.6, 1)), (3.4, (1, 1, 1)))
    a.rot("bone", (0, (0, 0, 0), "linear"), (0.7, (0, 0, 0), "linear"), (2.7, (0, 1440, 0), "linear"),
          (3.4, (0, 1440, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-20, 0, -40)), (2.7, (-20, 0, -40)), (3.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-8, 0, 0)), (2.7, (-8, 0, 0)), (3.4, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (0.7, (0, 0, 0)), (1.0, (0, 0, -40)), (2.7, (0, 0, -40)), (3.4, (0, 0, 0)))

    # pyre (phase 2): he rears up, arms spread wide while the fire gathers (1.1 s = 22 ticks), then drops to one knee
    # and drives both fists into the floor: lines of fire run out like the bars of a cell
    a = m.anim("pyre", 3.3)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.95, (-20, 0, -80 * sx)), (1.1, (-25, 0, -85 * sx)),
              (1.2, (-40, 0, -25 * sx), "linear"), (2.6, (-40, 0, -25 * sx)), (3.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-24, 0, 0)), (1.2, (30, 0, 0), "linear"), (2.6, (28, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (-26, 0, 0)), (1.2, (6, 0, 0), "linear"), (2.6, (6, 0, 0)), (3.3, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.1, (0, 1.5, 0)), (1.2, (0, -7, 0), "linear"), (2.6, (0, -7, 0)), (3.3, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (-70, 0, 0), "linear"), (2.6, (-70, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (70, 0, 0), "linear"), (2.6, (70, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (20, 0, 0), "linear"), (2.6, (20, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (75, 0, 0), "linear"), (2.6, (75, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (1.1, (-16, 0, 0)), (1.3, (28, 0, 0)), (1.8, (-12, 0, 0)), (2.6, (0, 0, 0)),
          (3.3, (0, 0, 0)))

    # verdict (phase 3, spectacle): the chain whirled overhead (1.2 s = 24 ticks), then flung up into the dark; he
    # holds the arm high while chains of judgement rain down
    a = m.anim("verdict", 4.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-170, 0, 10)), (1.2, (-172, 0, 10)), (1.28, (-178, 0, 0), "linear"),
          (3.2, (-172, 0, 5)), (4.0, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.5, (24, 0, 4)), (3.2, (24, 0, 4)), (4.0, (0, 0, 0)))
    a.rot("chain_r", (0, (0, 0, 0), "linear"), (0.5, (-80, 0, 0), "linear"), (1.2, (-80, 1080, 0), "linear"),
          (1.28, (0, 1080, 0), "linear"), (3.2, (0, 1080, 0)), (4.0, (0, 1080, 0)))
    a.scale("chain_r", (0, (1, 1, 1)), (1.2, (1, 1.3, 1)), (1.28, (1, 2.4, 1), "linear"), (1.6, (1, 1, 1)), (4.0, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-30, 0, 0)), (3.2, (-26, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-18, 0, 0)), (3.2, (-14, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.2, (-30, 0, -50)), (3.2, (-30, 0, -45)), (4.0, (0, 0, 0)))

    # unchain (phase 3 transition): he kneels and strains against the chains binding him (1.5 s = 30 ticks), then
    # tears them apart, arms flung wide, the fire in his cage roaring up
    a = m.anim("unchain", 3.5)
    a.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, -6, 0)), (1.5, (0, -6, 0)), (1.6, (0, 1, 0), "linear"), (2.8, (0, 0, 0)),
          (3.5, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.4, (-60, 0, 0)), (1.5, (-60, 0, 0)), (1.6, (-10, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (60, 0, 0)), (1.5, (60, 0, 0)), (1.6, (10, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (1.5, (20, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (70, 0, 0)), (1.5, (70, 0, 0)), (1.6, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    shake = [(0.4 + 0.1 * i, (30 + (4 if i % 2 else -4), 0, 0)) for i in range(11)]
    a.rot("chest", (0, (0, 0, 0)), *shake, (1.6, (-28, 0, 0), "linear"), (2.8, (-24, 0, 0)), (3.5, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.4, (-70, -40 * sx, 30 * sx)), (1.5, (-75, -45 * sx, 32 * sx)),
              (1.6, (-50, 0, -95 * sx), "linear"), (2.8, (-45, 0, -90 * sx)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (20, 0, 0)), (1.5, (24, 0, 0)), (1.6, (-38, 0, 0), "linear"), (2.8, (-34, 0, 0)),
          (3.5, (0, 0, 0)))
    a.scale("sash", (0, (1, 1, 1)), (1.5, (0.94, 0.94, 0.94)), (1.6, (1.25, 1.3, 1.25), "linear"), (2.0, (1, 1, 1)),
            (3.5, (1, 1, 1)))
    a.rot("sash", (0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (-30, 0, 20), "linear"), (2.2, (-10, 0, 5)), (3.5, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (1.5, (-10, 0, 0)), (1.7, (40, 0, 0)), (2.2, (-20, 0, 0)), (2.8, (8, 0, 0)),
          (3.5, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (1.5, (1, 1, 1)), (1.6, (1.12, 1.12, 1.12), "linear"), (2.8, (1.06, 1.06, 1.06)),
            (3.5, (1, 1, 1)))

    # roar (phase two): arms flung wide, the cage head thrown back, the chains rattle
    a = m.anim("roar", 2.0)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-40, 0, -55 * sx)), (1.6, (-45, 0, -60 * sx)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-18, 0, 0)), (1.6, (-16, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chain_l", (0, (0, 0, 0)), (0.6, (40, 0, 20)), (1.0, (-20, 0, -10)), (1.6, (30, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (0.6, (-24, 0, 0)), (1.1, (20, 0, 0)), (1.6, (-12, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: the padlock broken open for a moment: he sags onto one knee, the chain and ball dropped
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.2, (0, -6, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.3, (-60, 0, 0)), (1.2, (-60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.2, (60, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.3, (20, 0, 0)), (1.2, (20, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (70, 0, 0)), (1.2, (70, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (26, 0, 8)), (1.2, (28, 0, 8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, -10)), (1.2, (26, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (14, 0, 10)), (1.2, (16, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (10, 0, -10)), (1.2, (12, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("gibbet", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (0.7, (-14, 0, 0)), (1.2, (6, 0, 0)), (1.6, (0, 0, 0)))
