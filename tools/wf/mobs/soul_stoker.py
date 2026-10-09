"""The Soul Stoker (Le Chauffeur des âmes): the champion of the Soul Engine, about 4 blocks tall.

Silhouette idea: a hulking furnace-man, a walking boiler. His torso is a squat drum of polished blackstone bound in
tarnished brass hoops, with a grated firebox mouth in the belly that glows with blue soul fire and a pressure gauge on
the chest; two ribbed chimneys rise from his back and vent blue flame over his shoulders. His head is a furnace door
made into a helmet: an iron door with hinges on one side, a skull face hammered into it whose eye-holes burn blue,
a latch for a jaw. Short, thick legs in iron greaves, heavy boots. From his belt hang chains of bone, each ending in
a soul lantern. Asymmetry: his RIGHT arm ends in a giant coal shovel (a long iron-shod haft, a wide scoop heaped with
glowing embers); his LEFT arm is a piston-driven fist (a copper cylinder for an upper arm, brass piston rods running
along it, a steel sleeve for a forearm and a huge iron fist on the piston rod).
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

STONE = (44, 38, 46)            # polished blackstone
STONE_L = (72, 64, 76)
STONE_D = (26, 22, 28)
STONE_DD = (16, 13, 18)
GILD = (214, 170, 72)           # gilded blackstone flecks
BONE = (226, 218, 190)
BONE_D = (176, 166, 134)
BONE_DD = (120, 110, 84)
SOUL = (60, 210, 240)           # soul fire
SOUL_L = (190, 250, 255)
SOUL_D = (30, 120, 170)
SOUL_DD = (16, 52, 84)
EMBER = (110, 230, 255)
LEATHER = (82, 44, 34)
LEATHER_D = (52, 28, 22)


# ---------------------------------------------------------------- paint
def blackstone(seed=0, hoops=0):
    """Polished blackstone: dark, faintly purple, a few gilded flecks; with ``hoops`` a brass band every ``hoops``
    texels (the boiler's courses)."""
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "bottom":
            return STONE_DD
        if face == "top":
            return STONE_L if r > 0.7 else STONE
        if hoops and y % hoops in (0, 1):
            band = B.BRASS if y % hoops == 0 else B.BRASS_D
            return B.BRASS_L if (y % hoops == 0 and x % 4 == 1) else band
        c = mul(STONE, 0.9 + r * 0.25 - 0.12 * y / max(1, h))
        if B.n(x // 2, y // 3, seed + 5) < 0.07:
            return mix(c, GILD, 0.6)
        if (x + y * 3) % 11 == 0:
            return STONE_D
        return c
    return f


def boiler(face, x, y, w, h):
    """The torso drum (24 x 26 x 18): blackstone courses between brass hoops, rivets along the hoops, soot streaks
    climbing from the firebox; the back face has a riveted inspection hatch."""
    base = blackstone(11, hoops=0)(face, x, y, w, h)
    if face in ("top", "bottom"):
        return base
    for hy in (1, 9, h - 2):
        if y in (hy, hy + 1):
            if y == hy and x % 3 == 1:
                return B.BRASS_L                                                        # rivet heads on the hoop
            return B.BRASS if y == hy else B.BRASS_D
    if face == "front" and 9 < y < 18 and B.n(x, y // 2, 13) < 0.25:
        return mix(base, B.SOOT, 0.6)                                                  # soot over the firebox
    if face == "back" and 5 <= x <= w - 6 and 4 <= y <= 15:
        if x in (5, w - 6) or y in (4, 15):
            return B.IRON_L if (x + y) % 3 else B.BRASS                                 # the inspection hatch
        return B.IRON
    return base


def firebox(face, x, y, w, h):
    """The firebox mouth: a brass frame, iron grate bars, blue soul fire behind them (the glow layer lights it)."""
    if face != "front":
        return B.iron(14)(face, x, y, w, h)
    if x == 0 or y == 0 or x == w - 1 or y == h - 1:
        return B.BRASS_L if y == 0 else B.BRASS_D
    if x % 2 == 0:
        return B.IRON_D
    return SOUL_L if y >= h - 3 else SOUL


def firebox_glow(face, x, y, w, h):
    if face != "front" or x == 0 or y == 0 or x == w - 1 or y == h - 1 or x % 2 == 0:
        return None
    return SOUL_L if y >= h - 3 else SOUL


def helmet(face, x, y, w, h):
    """The furnace-door helmet (12 x 12 x 12): black iron, riveted; the door itself is a separate plate."""
    if face == "top":
        if x in (0, w - 1) or y in (0, h - 1):
            return B.IRON_L
        return B.IRON if (x + y) % 4 else B.IRON_D
    if face == "bottom":
        return B.IRON_D
    if y in (0, h - 1) or x in (0, w - 1):
        return B.IRON_L if y == 0 else B.IRON_D
    if (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        return B.BRASS_L
    if face == "back" and 3 <= y <= 8 and x % 2 == 1 and 2 <= x <= w - 3:
        return B.SOOT                                                                  # draught slots
    return mul(B.IRON, 1.0 + (B.n(x, y, 21) - 0.5) * 0.12)


SKULL = ["..########..",
         ".##########.",
         "############",
         "##..####..##",
         "##..####..##",
         "############",
         ".#####.####.",
         ".##########.",
         "..#.#.#.#...",
         "..########..",
         "..........."]


def door(face, x, y, w, h):
    """The furnace door (10 x 11 x 1) on the helmet's front: a skull face hammered in bone-white enamel on black iron,
    the eye-holes and the nose cut through to the soul fire inside, a brass latch for a jaw-bar."""
    if face != "front":
        return B.IRON_D
    if y >= len(SKULL):
        return B.BRASS
    row = SKULL[y]
    ch = row[x] if x < len(row) else "."
    if y in (3, 4) and x in (2, 3, 8, 9):
        return SOUL                                                                    # the eye-holes
    if y == 6 and x == 6:
        return SOUL_D                                                                  # the nose
    if y == 8 and ch == "." and 2 <= x <= 9:
        return B.SOOT                                                                  # between the teeth
    if ch == "#":
        return BONE if B.n(x, y, 23) > 0.2 else BONE_D
    return B.IRON if (x + y) % 2 else B.IRON_D


def door_glow(face, x, y, w, h):
    if face != "front":
        return None
    if y in (3, 4) and x in (2, 3, 8, 9):
        return SOUL_L if y == 3 else SOUL
    if y == 6 and x == 6:
        return SOUL
    return None


def iron(seed=0):
    return B.iron(seed)


def copper(seed=0):
    return B.copper(seed, grad=0.3)


def steel(face, x, y, w, h):
    """A polished piston rod: bright streak down the middle, a cool sheen."""
    if face in ("top", "bottom"):
        return (150, 156, 166)
    k = 1.25 if x == w // 2 else (0.85 if x in (0, w - 1) else 1.0)
    return mul((176, 182, 194), k)


def bone(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return BONE_DD
        r = B.n(x, y, seed)
        if face == "top":
            return BONE
        return BONE if r > 0.3 else (BONE_D if r > 0.08 else BONE_DD)
    return f


def link(face, x, y, w, h):
    """A bone chain link: knuckled ends, a darker middle."""
    if face in ("top", "bottom"):
        return BONE_D
    return BONE if y in (0, h - 1) else BONE_D


def lantern(face, x, y, w, h):
    """A soul lantern: an iron cage with a blue flame (the glow layer lights the panes)."""
    if face in ("top", "bottom"):
        return B.IRON_D
    if y in (0, h - 1) or x in (0, w - 1):
        return B.IRON
    return SOUL


def lantern_glow(face, x, y, w, h):
    if face in ("top", "bottom") or y in (0, h - 1) or x in (0, w - 1):
        return None
    return SOUL_L if y == 1 else SOUL


def leather(seed=0):
    def f(face, x, y, w, h):
        r = B.n(x, y, seed)
        if face == "bottom":
            return LEATHER_D
        c = LEATHER if r > 0.25 else LEATHER_D
        if y % 4 == 3:
            return LEATHER_D
        return c
    return f


def belt(face, x, y, w, h):
    """The stoker's belt: thick leather, a row of brass studs, a big iron buckle in front."""
    if face in ("top", "bottom"):
        return LEATHER_D
    if face == "front" and abs(x - (w - 1) / 2) <= 2.5:
        if abs(x - (w - 1) / 2) > 1.5 or y in (0, h - 1):
            return B.BRASS_L if y < h / 2 else B.BRASS
        return B.IRON_D
    if y == h // 2 and x % 3 == 1:
        return B.BRASS_L
    return leather(31)(face, x, y, w, h)


def scoop(face, x, y, w, h):
    """The shovel's scoop: sooty black iron, a bright worn edge, rivets near the socket."""
    if face == "bottom":
        return (120, 120, 128)                                                         # the worn cutting edge
    if face == "top":
        return B.IRON_D
    if y == h - 1:
        return (150, 150, 160)
    if y == 0 and x % 3 == 1:
        return B.BRASS_L
    k = 0.8 + 0.4 * y / max(1, h) + (B.n(x, y, 41) - 0.5) * 0.1
    return mix(B.SOOT, B.IRON_L, min(1.0, 0.25 + 0.5 * k))


def embers(face, x, y, w, h):
    """A heap of soul embers in the scoop: dark cinders with blue-hot coals."""
    r = B.n(x, y, 43)
    if r > 0.66:
        return SOUL_L
    if r > 0.38:
        return SOUL
    return SOUL_DD if r > 0.15 else B.SOOT


def embers_glow(face, x, y, w, h):
    r = B.n(x, y, 43)
    if r > 0.66:
        return SOUL_L
    if r > 0.38:
        return SOUL
    return None


def haft(face, x, y, w, h):
    """The shovel's haft: dark wood bound in iron every few texels, a leather wrap where the hand grips."""
    if face in ("top", "bottom"):
        return B.IRON_D
    if y % 9 in (0, 1):
        return B.IRON_L if y % 9 == 0 else B.IRON
    k = 1.15 if x == w // 2 else 1.0
    return mul(B.MAHOGANY_D, k + (B.n(x, y, 45) - 0.5) * 0.12)


def chimney(seed=0):
    """A ribbed chimney stack: blackstone ribs, soot darkening toward the top."""
    def f(face, x, y, w, h):
        if face == "top":
            return B.SOOT
        if face == "bottom":
            return STONE_DD
        if y % 4 == 0:
            return B.BRASS_D if x % 2 else B.BRASS
        k = y / max(1, h - 1)
        return mix(B.SOOT, STONE_L, min(1.0, 0.25 + 0.75 * k))
    return f


def flame(face, x, y, w, h):
    if face == "bottom":
        return SOUL_D
    return SOUL_L if (x + y) % 3 == 0 else SOUL


def gauge(face, x, y, w, h):
    """The chest pressure gauge: a brass bezel, a cream dial, a blue arc for the safe zone, a red needle."""
    if face != "front":
        return B.brass(51)(face, x, y, w, h)
    if x in (0, w - 1) or y in (0, h - 1):
        return B.BRASS_L if y == 0 else B.BRASS_D
    if y == 1:
        return SOUL_D if x < w - 2 else (200, 40, 40)                                  # the scale: blue, then red
    if (x, y) in ((2, 2), (3, 2), (3, 3)):
        return (190, 30, 30)                                                           # the needle, near the red
    return B.CREAM


def valve(face, x, y, w, h):
    if face in ("front", "back") and (x == w // 2 or y == h // 2):
        return B.BRASS_L
    return B.BRASS_D


# ---------------------------------------------------------------- build
def build():
    m = Model("soul_stoker", seed=907, shadow=1.9, walk_speed=0.55, walk_scale=0.8, glow_pulse=0.08)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -22, 0))
    m.part("chains", "hips", pivot=(0, 2, 0))
    m.part("chest", "hips", pivot=(0, -3, 0))
    m.part("head", "chest", pivot=(0, -26, -1))
    m.part("jaw", "head", pivot=(0, -1, -6.5))
    m.part("stacks", "chest", pivot=(0, -24, 7))
    m.part("flames", "stacks", pivot=(0, -18, 2))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(6.5 * sx, -20, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 10, 0))
    m.part("arm_r", "chest", pivot=(-15, -22, 0), rot=(-8, 0, 10))
    m.part("fore_r", "arm_r", pivot=(-0.5, 11, 0), rot=(-34, 0, -6))
    m.part("hand_r", "fore_r", pivot=(0, 10, 0))
    m.part("shovel", "hand_r", pivot=(0, 2.5, 0), rot=(-15, 0, 0))
    m.part("arm_l", "chest", pivot=(15, -22, 0), rot=(-6, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0.5, 11, 0), rot=(-28, 0, 6))
    m.part("fist", "fore_l", pivot=(0, 10, 0))

    # ---- legs: thick iron greaves over blackstone, heavy boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -4, -2, -4, 8, 12, 8, blackstone(1 + sx))
        m.box(leg, -4.5, 3, -4.5, 9, 3, 9, B.brass(3 + sx))                            # a brass hoop at the thigh
        m.box(shin, -4.5, 0, -4.5, 9, 8, 9, iron(5 + sx))                               # the greave
        m.box(shin, -3, -1, -5.2, 6, 3, 1, B.brass(7 + sx))                            # the knee cop
        m.box(shin, -5, 7, -7, 10, 3, 12, iron(9 + sx))                                 # the boot
        m.box(shin, -4, 7.5, -8, 8, 2, 1, B.brass(11 + sx))                            # its toe cap

    # ---- hips: a broad leather belt with a buckle, a blackstone girdle under it
    m.box("hips", -10, -3, -7, 20, 6, 14, blackstone(20))
    m.box("hips", -11, -2, -7.5, 22, 4, 15, belt)

    # ---- bone chains from the belt, each ending in a soul lantern (front left, right hip, back)
    chains = [(-8.5, -7.6, 5), (8.5, -7.6, 4), (-11.6, 0, 6), (11.6, 2, 5), (4, 7.6, 4)]
    for k, (cx, cz, n) in enumerate(chains):
        for i in range(n):
            m.box("chains", cx - 0.5, i * 2, cz - 0.5, 1, 2, 1, link)
        m.box("chains", cx - 1.5, n * 2, cz - 1.5, 3, 4, 3, lantern, glow=lantern_glow)
        m.box("chains", cx - 1, n * 2 - 0.6, cz - 1, 2, 1, 2, B.IRON_D)                  # its cap
        m.box("chains", cx - 0.5, n * 2 + 4, cz - 0.5, 1, 1, 1, bone(60 + k))           # a knucklebone finial
    for x in (-9, -6, -3, 0, 3, 6, 9):
        m.box("chains", x - 0.5, -1, -7.8, 1, 2, 1, bone(70 + x))                      # small bones threaded on it

    # ---- the boiler: a blackstone drum in brass hoops, the firebox mouth, the gauge, the shoulder valves
    m.box("chest", -12, -26, -9, 24, 26, 18, boiler)
    m.box("chest", -11, -27.5, -8, 22, 2, 16, blackstone(30))                          # the domed crown
    m.box("chest", -6, -15, -10, 12, 9, 1, firebox, glow=firebox_glow)                 # the firebox mouth
    m.box("chest", -7, -16, -10.6, 14, 1, 2, B.brass(31))                              # its lintel
    m.box("chest", -7, -6, -10.6, 14, 1, 2, B.brass(32))                               # its sill
    m.box("chest", 4, -23, -10, 5, 5, 1, gauge)                                        # the pressure gauge
    m.box("chest", 6, -18, -10.2, 1, 3, 1, B.BRASS_D)                                   # its pipe
    m.box("chest", -9, -23, -10, 3, 3, 1, valve)                                        # a valve wheel
    m.box("chest", -13, -24, -6, 1, 18, 12, blackstone(33, hoops=6))                    # the drum's flanks
    m.box("chest", 12, -24, -6, 1, 18, 12, blackstone(34, hoops=6))
    # pauldrons: thick riveted iron caps over the shoulders
    m.box("chest", -18, -28, -6, 8, 5, 12, iron(35))
    m.box("chest", 10, -28, -6, 8, 5, 12, iron(36))
    m.box("chest", -18.5, -29, -2, 9, 1, 4, B.brass(37))
    m.box("chest", 9.5, -29, -2, 9, 1, 4, B.brass(38))

    # ---- head: the furnace-door helmet with a skull face, a latch-bar jaw, a little vent cap on top
    m.box("head", -6, -12, -6, 12, 12, 12, helmet)
    m.box("head", -5, -11.5, -7, 10, 11, 1, door, glow=door_glow)
    m.box("head", -7, -10, -5, 1, 3, 2, B.brass(40))                                   # the hinges (right side)
    m.box("head", -7, -4, -5, 1, 3, 2, B.brass(41))
    m.box("head", 5.5, -7, -7.6, 2, 2, 1, B.BRASS_L)                                    # the latch knob
    m.box("head", -2, -14, -2, 4, 2, 4, iron(42))                                       # the vent cap
    m.box("head", -2.5, -15, -2.5, 5, 1, 5, B.brass(43))
    m.box("jaw", -4, -1, -1, 8, 2, 1, B.brass(44))                                      # the latch-bar jaw
    m.box("jaw", -3, 1, -1, 1, 1, 1, BONE_D)
    m.box("jaw", 2, 1, -1, 1, 1, 1, BONE_D)

    # ---- the chimneys on his back, venting blue flame
    for sx, ht in ((-6, 20), (6, 17)):
        m.box("stacks", sx - 2.5, -ht + 2, 0, 5, ht, 5, chimney(50 + sx))
        m.box("stacks", sx - 3, -ht + 1, -0.5, 6, 2, 6, B.brass(52 + sx))               # the rim
        m.box("flames", sx - 1.5, -ht + 16, -1, 3, 4, 3, flame, glow=flame)            # blue flame over the rim
        m.box("flames", sx - 0.5, -ht + 13, 0, 1, 3, 1, SOUL_L, glow=SOUL_L)
    m.box("stacks", -9, -2, 1, 18, 3, 3, B.iron(55))                                     # the manifold joining them

    # ---- right arm: an iron shoulder, a leather-wrapped forearm, the coal shovel
    m.box("arm_r", -4, -2, -4, 7, 12, 8, blackstone(60))
    m.box("arm_r", -4.5, 4, -4.5, 8, 2, 9, B.brass(61))
    m.box("fore_r", -3.5, 0, -3.5, 7, 10, 7, leather(62))
    m.box("fore_r", -4, 7, -4, 8, 3, 8, iron(63))                                        # an iron cuff
    m.box("hand_r", -3, 0, -3, 6, 5, 6, iron(64))
    m.box("shovel", -1, -16, -1, 2, 42, 2, haft)
    m.box("shovel", -2, -18, -2, 4, 2, 4, iron(65))                                      # the D-grip's knob
    m.box("shovel", -1.5, 24, -1.5, 3, 4, 3, iron(66))                                   # the socket
    m.box("shovel", -6, 27, -2, 12, 13, 1, scoop)                                        # the scoop's back
    m.box("shovel", -7, 27, -2, 1, 12, 5, scoop)                                         # its turned-up sides
    m.box("shovel", 6, 27, -2, 1, 12, 5, scoop)
    m.box("shovel", -6, 30, -1, 12, 8, 3, embers, glow=embers_glow)                     # the heap of soul embers

    # ---- left arm: a copper cylinder for an upper arm with brass piston rods, a steel sleeve, the iron fist
    m.box("arm_l", -3, -2, -4, 7, 12, 8, copper(70))
    m.box("arm_l", -3.5, 0, -4.5, 8, 2, 9, B.brass(71))
    m.box("arm_l", -3.5, 8, -4.5, 8, 2, 9, B.brass(72))
    m.box("arm_l", 4, -1, -2, 1, 12, 1, steel)                                           # outer piston rods
    m.box("arm_l", 4, -1, 1, 1, 12, 1, steel)
    m.box("arm_l", 0, -4, -2, 4, 2, 4, valve)                                            # a steam valve on the shoulder
    m.box("fore_l", -4, 0, -4, 8, 9, 8, iron(73))                                        # the piston sleeve
    m.box("fore_l", -4.5, 1, -4.5, 9, 1, 9, B.brass(74))
    m.box("fore_l", -4.5, 7, -4.5, 9, 1, 9, B.brass(75))
    m.box("fore_l", 3.6, 2, -1, 1, 4, 2, gauge)                                          # a tiny gauge on the sleeve
    m.box("fist", -1.5, -6, -1.5, 3, 7, 3, steel)                                        # the piston rod (hidden when in)
    m.box("fist", -5, 1, -5, 10, 8, 10, iron(76))                                        # the great fist
    m.box("fist", -5.5, 6, -5.5, 11, 2, 11, B.brass(77))                                 # brass knuckle plate
    for k, x in enumerate((-4.5, -2, 0.5, 3)):
        m.box("fist", x, 8, -5.8, 2, 2, 2, iron(78 + k))                                 # the knuckles
    m.box("fist", -5.6, 2, -2, 1, 4, 4, iron(82))                                        # the thumb

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.8, 0)), (3.0, (0, 0, 0)))             # heavy breathing (the bellows)
    idle.scale("flames", (0, (1, 1, 1)), (0.75, (1.1, 1.35, 1.1)), (1.5, (0.9, 0.9, 0.9)), (2.25, (1.1, 1.3, 1.1)),
               (3.0, (1, 1, 1)))
    idle.rot("chains", (0, (0, 0, 0)), (1.5, (4, 0, 3)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (3, 6, 0)), (3.0, (0, 0, 0)))
    idle.rot("fore_l", (0, (0, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (0, 0, 0)))
    idle.pos("fist", (0, (0, 0, 0)), (1.4, (0, 0, 0)), (1.5, (0, 1.5, 0)), (1.7, (0, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("leg_r", (0, (22, 0, 0)), (1.0, (-22, 0, 0)), (2.0, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (1.0, (22, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (20, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -1.2, 0)), (1.0, (0, 0, 0)), (1.5, (0, -1.2, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, 6, 2)), (1.0, (0, -6, -2)), (2.0, (0, 6, 2)))
    walk.rot("arm_r", (0, (-10, 0, 0)), (1.0, (8, 0, 0)), (2.0, (-10, 0, 0)))
    walk.rot("arm_l", (0, (10, 0, 0)), (1.0, (-10, 0, 0)), (2.0, (10, 0, 0)))
    walk.rot("chains", (0, (8, 0, 4)), (1.0, (8, 0, -4)), (2.0, (8, 0, 4)))

    # shovel (16 / 20 / 16): the shovel drawn back across his body to the left (0.8 s), then swept round to the
    # right at 0.8 s, flinging its embers out ahead; he follows through and slowly recovers
    a = m.anim("shovel", 2.6)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.7, (-70, 60, -30)), (0.8, (-74, 64, -32)), (0.9, (-70, -60, 40), "linear"),
          (1.3, (-60, -70, 44)), (1.8, (-40, -40, 30)), (2.6, (-8, 0, 10)))
    a.rot("shovel", (0, (-15, 0, 0)), (0.8, (0, 0, 0)), (0.9, (-40, 0, 0), "linear"), (1.8, (-30, 0, 0)), (2.6, (-15, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (4, 40, 0)), (0.8, (4, 44, 0)), (0.9, (6, -36, 0), "linear"),
          (1.3, (4, -40, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (-6, 0, -10)), (0.8, (-30, 0, -40)), (1.3, (-10, 0, -30)), (2.6, (-6, 0, -10)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-14, 0, 0)), (1.3, (10, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (12, 0, 0)), (1.3, (-10, 0, 0)), (2.6, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (0.9, (1.4, 1.8, 1.4)), (1.4, (1, 1, 1)), (2.6, (1, 1, 1)))

    # piston (28 / 12 / 18): he plants his feet and cocks the piston fist far back, the arm hissing steam (1.4 s),
    # then drives it out at 1.4 s, the piston rod shooting out of the sleeve; he holds the punch, then hauls it in
    a = m.anim("piston", 2.9)
    a.rot("arm_l", (0, (-6, 0, -10)), (1.2, (40, -20, -20)), (1.4, (44, -22, -20)), (1.46, (-90, 0, -4), "linear"),
          (1.9, (-88, 0, -4)), (2.9, (-6, 0, -10)))
    a.rot("fore_l", (0, (-28, 0, 6)), (1.4, (-90, 0, 0)), (1.46, (0, 0, 0), "linear"), (1.9, (0, 0, 0)),
          (2.9, (-28, 0, 6)))
    a.pos("fist", (0, (0, 0, 0)), (1.4, (0, -2, 0)), (1.46, (0, 7, 0), "linear"), (1.9, (0, 7, 0)), (2.4, (0, 0, 0)),
          (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.4, (-6, -34, 0)), (1.46, (14, 26, 0), "linear"), (1.9, (12, 24, 0)),
          (2.9, (0, 0, 0)))
    a.rot("arm_r", (0, (-8, 0, 10)), (1.4, (-20, 0, 30)), (1.46, (10, 0, 20), "linear"), (2.9, (-8, 0, 10)))
    a.pos("hips", (0, (0, 0, 0)), (1.4, (0, 1.5, 2)), (1.46, (0, 1, -3), "linear"), (1.9, (0, 1, -3)),
          (2.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.4, (20, 0, 0)), (1.46, (24, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.4, (-24, 0, 0)), (1.46, (-26, 0, 0)), (2.9, (0, 0, 0)))

    # stoke (40 / 16 / 20): three shovelfuls of souls heaved into his firebox (0.3, 0.8, 1.3 s), then he braces,
    # head back, the boiler swelling (to 2.0 s), and the firebox door vents a cone of blue flame from 2.0 s
    a = m.anim("stoke", 3.8)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.2, (-30, 0, 40)), (0.3, (-80, -40, 10)), (0.5, (-30, 0, 40)),
          (0.7, (-30, 0, 40)), (0.8, (-80, -40, 10)), (1.0, (-30, 0, 40)), (1.2, (-30, 0, 40)), (1.3, (-80, -40, 10)),
          (1.6, (-20, 0, 50)), (2.0, (-20, 0, 60)), (3.0, (-20, 0, 60)), (3.8, (-8, 0, 10)))
    a.rot("arm_l", (0, (-6, 0, -10)), (1.6, (-20, 0, -50)), (2.0, (-20, 0, -60)), (3.0, (-20, 0, -60)),
          (3.8, (-6, 0, -10)))
    a.rot("chest", (0, (0, 0, 0)), (1.3, (6, 0, 0)), (1.9, (-14, 0, 0)), (2.0, (-16, 0, 0)), (2.06, (8, 0, 0), "linear"),
          (2.8, (6, 0, 0)), (3.8, (0, 0, 0)))
    a.scale("chest", (0, (1, 1, 1)), (1.3, (1, 1, 1)), (1.9, (1.08, 1.04, 1.08)), (2.0, (1.1, 1.05, 1.1)),
            (2.06, (0.98, 1, 0.98), "linear"), (2.8, (1, 1, 1)), (3.8, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.9, (-24, 0, 0)), (2.0, (-26, 0, 0)), (2.06, (6, 0, 0), "linear"), (3.8, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (1.9, (1.6, 2.2, 1.6)), (2.06, (2.0, 2.6, 2.0), "linear"), (2.8, (1.6, 2.0, 1.6)),
            (3.8, (1, 1, 1)))
    a.rot("jaw", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.06, (30, 0, 0), "linear"), (2.8, (30, 0, 0)), (3.8, (0, 0, 0)))

    # vents (20 / 34 / 14): he raises the shovel high (1.0 s) and rams its blade into the deck at 1.0 s; the vents
    # crack open one after another while he leans on it
    a = m.anim("vents", 3.4)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.9, (-160, 0, 10)), (1.0, (-164, 0, 10)), (1.06, (-60, 0, 10), "linear"),
          (2.7, (-56, 0, 10)), (3.4, (-8, 0, 10)))
    a.rot("shovel", (0, (-15, 0, 0)), (1.0, (20, 0, 0)), (1.06, (10, 0, 0), "linear"), (2.7, (10, 0, 0)),
          (3.4, (-15, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-12, 10, 0)), (1.06, (20, 0, 0), "linear"), (2.7, (18, 0, 0)),
          (3.4, (0, 0, 0)))
    a.rot("arm_l", (0, (-6, 0, -10)), (1.0, (-40, 0, -30)), (1.06, (-50, 0, -20), "linear"), (2.7, (-50, 0, -20)),
          (3.4, (-6, 0, -10)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, -1, 0)), (1.06, (0, 2, 0), "linear"), (2.7, (0, 2, 0)), (3.4, (0, 0, 0)))

    # thralls (20 / 10 / 16): he throws open his firebox with the shovel (1.0 s) and soul fire belches out: two
    # wither skeletons step out of it
    a = m.anim("thralls", 2.3)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.9, (-50, 40, -10)), (1.0, (-54, 44, -10)), (1.06, (-40, -30, 30), "linear"),
          (1.5, (-40, -30, 30)), (2.3, (-8, 0, 10)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.06, (-20, 0, 0), "linear"), (1.5, (-18, 0, 0)),
          (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.5, (-24, 0, 0)), (2.3, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (1.0, (1.5, 2.0, 1.5)), (1.5, (1.8, 2.4, 1.8)), (2.3, (1, 1, 1)))
    a.rot("arm_l", (0, (-6, 0, -10)), (1.0, (-60, 0, -50)), (1.5, (-60, 0, -50)), (2.3, (-6, 0, -10)))

    # charge (phase 2, 24 / 16 / 16): he hunches, chimneys roaring, the fist cocked at his side (1.2 s), then
    # rushes down the lane like a runaway engine, fist first
    a = m.anim("charge", 2.8)
    a.rot("chest", (0, (0, 0, 0)), (1.2, (24, 0, 0)), (1.26, (30, 0, 0), "linear"), (2.0, (30, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-20, 0, 0)), (2.0, (-20, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("arm_l", (0, (-6, 0, -10)), (1.2, (20, 0, -20)), (1.26, (-80, 0, -6), "linear"), (2.0, (-80, 0, -6)),
          (2.8, (-6, 0, -10)))
    a.rot("fore_l", (0, (-28, 0, 6)), (1.2, (-70, 0, 0)), (1.26, (0, 0, 0), "linear"), (2.0, (0, 0, 0)),
          (2.8, (-28, 0, 6)))
    a.rot("arm_r", (0, (-8, 0, 10)), (1.2, (30, 0, 30)), (2.0, (30, 0, 30)), (2.8, (-8, 0, 10)))
    a.rot("leg_r", (0, (0, 0, 0)), (1.26, (30, 0, 0)), (1.5, (-30, 0, 0)), (1.75, (30, 0, 0)), (2.0, (-20, 0, 0)),
          (2.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (1.26, (-30, 0, 0)), (1.5, (30, 0, 0)), (1.75, (-30, 0, 0)), (2.0, (20, 0, 0)),
          (2.8, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (1.2, (1.8, 2.6, 1.8)), (2.0, (1.8, 2.6, 1.8)), (2.8, (1, 1, 1)))

    # overpressure (phase 3, 40 / 20 / 20): every gauge pegged, he clutches his boiler and shudders, swelling
    # (2.0 s), then the safety valves blow and he throws his arms wide in a blast of blue flame
    a = m.anim("overpressure", 4.0)
    a.scale("chest", (0, (1, 1, 1)), (1.0, (1.06, 1.03, 1.06)), (1.5, (1.04, 1.02, 1.04)), (2.0, (1.14, 1.07, 1.14)),
            (2.06, (0.95, 1, 0.95), "linear"), (3.0, (1.03, 1.02, 1.03)), (4.0, (1, 1, 1)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.4, (-60, -40, -20)), (2.0, (-64, -44, -20)), (2.06, (-60, 0, 80), "linear"),
          (3.2, (-60, 0, 80)), (4.0, (-8, 0, 10)))
    a.rot("arm_l", (0, (-6, 0, -10)), (0.4, (-60, 40, 20)), (2.0, (-64, 44, 20)), (2.06, (-60, 0, -80), "linear"),
          (3.2, (-60, 0, -80)), (4.0, (-6, 0, -10)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (10, 4, 2)), (0.7, (10, -4, -2)), (0.9, (10, 4, 2)), (1.1, (10, -4, -2)),
          (1.3, (10, 4, 2)), (1.5, (10, -4, -2)), (1.7, (12, 4, 2)), (2.0, (12, 0, 0)), (2.06, (-16, 0, 0), "linear"),
          (3.2, (-12, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (2.0, (14, 0, 0)), (2.06, (-30, 0, 0), "linear"), (3.2, (-24, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.06, (40, 0, 0), "linear"), (3.2, (30, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (2.0, (1.4, 1.8, 1.4)), (2.06, (2.4, 3.2, 2.4), "linear"), (3.2, (2.0, 2.6, 2.0)),
            (4.0, (1, 1, 1)))

    # ringblast (phase 3, 20 / 40 / 16): he beats the shovel and the fist against his boiler (1.0 s); then
    # each safety valve lifts in turn (1.0, 1.6, 2.2 s), a ring of blue flame bursting out of him each time
    a = m.anim("ringblast", 3.8)
    a.rot("arm_r", (0, (-8, 0, 10)), (0.9, (-90, 0, 60)), (1.0, (-94, 0, 64)), (1.06, (-30, -40, 0), "linear"),
          (3.0, (-30, -40, 0)), (3.8, (-8, 0, 10)))
    a.rot("arm_l", (0, (-6, 0, -10)), (0.9, (-90, 0, -60)), (1.0, (-94, 0, -64)), (1.06, (-30, 40, 0), "linear"),
          (3.0, (-30, 40, 0)), (3.8, (-6, 0, -10)))
    puff = [(0, (1, 1, 1))]
    for t in (1.0, 1.6, 2.2):
        puff += [(t - 0.06, (1, 1, 1)), (t, (1.08, 1.04, 1.08)), (t + 0.1, (1, 1, 1))]
    a.scale("chest", *puff, (3.8, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-10, 0, 0)), (1.06, (4, 0, 0), "linear"), (3.0, (4, 0, 0)), (3.8, (0, 0, 0)))
    a.scale("flames", (0, (1, 1, 1)), (1.0, (2.0, 2.6, 2.0)), (3.0, (2.0, 2.8, 2.0)), (3.8, (1, 1, 1)))

    # roar (phase two): he rears up, arms wide, the jaw latch dropping, the chimneys flaring
    a = m.anim("roar", 2.0)
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-16, 0, 0)), (1.6, (-14, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-26, 0, 0)), (1.6, (-24, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (1.6, (40, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.5, (-60, 0, 70)), (1.6, (-64, 0, 74)), (2.0, (-8, 0, 10)))
    a.rot("arm_l", (0, (-6, 0, -10)), (0.5, (-60, 0, -70)), (1.6, (-64, 0, -74)), (2.0, (-6, 0, -10)))
    a.scale("flames", (0, (1, 1, 1)), (0.5, (2.2, 3.0, 2.2)), (1.6, (2.0, 2.8, 2.0)), (2.0, (1, 1, 1)))

    # stagger: the fire gutters, he sinks to one knee leaning on the shovel
    a = m.anim("stagger", 2.0)
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, 5, 0)), (1.6, (0, 5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.6, (-50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (28, 0, 6)), (1.6, (30, 0, 6)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (24, 0, -10)), (1.6, (24, 0, -10)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (-8, 0, 10)), (0.3, (-40, 0, 20)), (1.6, (-40, 0, 20)), (2.0, (-8, 0, 10)))
    a.scale("flames", (0, (1, 1, 1)), (0.3, (0.3, 0.3, 0.3)), (1.6, (0.4, 0.4, 0.4)), (2.0, (1, 1, 1)))
