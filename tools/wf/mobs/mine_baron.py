"""The Mine Baron (Le Baron de la mine): the greedy foreman of the Rust Mesa Mine-City, a huge man about 5.6 blocks tall
strapped into a riveted steam exo-rig, who never left the vein he was quarrying.

Silhouette idea: a fat foreman inside a walking machine. A barrel of a belly in a burgundy waistcoat with a gold watch
chain, rolled shirt-sleeves, a jowly ruddy face with a walrus moustache and a gold tooth, all caged in an iron rig: piston
legs with brass knee-hubs and huge hobnailed boots, a harness frame over the shoulders, and on his back a riveted boiler
with two smokestacks. On his head a brass miner's hard hat with a big glowing lantern on its front (in the last phase,
the only light left in the cavern). Strong asymmetry: his RIGHT arm is the rig's pneumatic drill (a piston upper arm,
a brass motor casing and a long spiral steel bit), his LEFT hand drags a colossal pickaxe-hammer (a hammer face in front,
a long pick behind) whose head hangs beside his left boot.

Three texture variants on the same cubes (``modelVariant()``):
  * ``bare``: the foreman in his rig (phases 1 and 3);
  * ``gilded``: the gold-greed of phase 2: a crust of raw gold and copper ore over his shoulders, arms, belly and helmet,
    and four glowing gold geodes on the boiler at his back (the weak spots players knock off);
  * ``cracked``: the crust half knocked away, two geodes left.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

VARIANTS = ["bare", "gilded", "cracked"]

SKIN = (206, 138, 112)
SKIN_D = (160, 96, 78)
SKIN_L = (232, 170, 142)
NOSE = (198, 92, 84)
STACHE = (74, 58, 50)
STACHE_L = (110, 90, 78)
VEST = (112, 34, 38)
VEST_D = (72, 20, 26)
VEST_L = (150, 56, 54)
SHIRT = (214, 200, 170)
SHIRT_D = (170, 152, 122)
GOLD = (255, 206, 72)
GOLD_L = (255, 238, 150)
GOLD_D = (190, 136, 30)
ORE_STONE = (122, 116, 112)
ORE_STONE_D = (78, 74, 72)
ORE_COPPER = (214, 120, 76)
STEEL = (150, 154, 164)
STEEL_L = (206, 210, 220)
STEEL_D = (86, 88, 98)
WOOD = (120, 82, 50)
WOOD_D = (78, 52, 32)
LEATHER = (96, 60, 38)
LEATHER_D = (60, 36, 24)
LAMP = (255, 214, 120)
LAMP_L = (255, 248, 210)
GEODE = (255, 196, 40)


def _gone(face, x, y, w, h):
    return None


# ---------------------------------------------------------------- paint
def iron(seed=0):
    return B.plate(B.IRON, B.IRON_D, B.IRON_L, rivet=B.BRASS, seed=seed, rivet_step=4, worn=0.12)


def brass(seed=0):
    return B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=seed, rivet_step=3, worn=0.08)


def copper(seed=0):
    return B.plate(B.COPPER, B.COPPER_D, B.COPPER_L, seed=seed, worn=0.1)


def piston(seed=0):
    """A polished piston rod: a bright streak, darker edges, a brass collar every 6 texels."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(STEEL, 1.05 if face == "top" else 0.7)
        if y % 6 == 5:
            return B.BRASS_D if x % 2 else B.BRASS
        k = 1.25 if x == w // 2 else (0.75 if x in (0, w - 1) else 1.0)
        return mul(STEEL, k + (B.n(x, y, seed) - 0.5) * 0.05)
    return f


def vest(seed=0, buttons=True, chain=False):
    """The burgundy waistcoat: a lit top, darker pinstripes, gold buttons down the middle, a watch chain swagged across."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return VEST_D
        if face == "top":
            return VEST_L
        c = mul(VEST, 1.08 - 0.25 * y / max(1, h))
        if x % 4 == 0:
            c = mul(c, 0.85)
        if face == "front":
            cx = w // 2
            if buttons and x in (cx - 1, cx) and y % 4 == 1:
                return GOLD if x == cx - 1 else GOLD_D
            if x == cx and not buttons:
                return VEST_D
            if chain:
                sag = int(h * 0.35 + 3.0 * math.sin(math.pi * x / max(1, w - 1)))
                if y == sag and 2 <= x <= w - 3:
                    return GOLD_L if x % 2 else GOLD
                if y == sag + 1 and x in (2, 3):
                    return GOLD_D                          # the watch in its pocket
            if y == h - 1 or y == h - 2:
                return VEST_D
        return c
    return f


def shirt(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SHIRT_D
        c = mul(SHIRT, 1.05 - 0.2 * y / max(1, h))
        if (x + y // 3) % 5 == 0:
            c = mul(c, 0.9)                                # folds
        return c
    return f


def skin(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return SKIN_D
        c = mul(SKIN, 1.06 - 0.18 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if B.n(x // 2, y, seed + 3) < 0.06:
            c = mix(c, NOSE, 0.4)                          # ruddy blotches
        return c
    return f


def face(face_, x, y, w, h):
    """The front of the head (14 x 12): the brim's shadow, greedy squinting eyes, a red nose, a walrus moustache, a
    gold tooth in a grin, heavy jowls."""
    if face_ != "front":
        c = skin(5)(face_, x, y, w, h)
        if face_ in ("left", "right") and 3 <= y <= 6 and 4 <= x <= 7:
            return mix(c, SKIN_D, 0.5)                     # ears
        if y <= 1:
            return mul(c, 0.7)
        return c
    cx = (w - 1) / 2
    if y <= 1:
        return mul(SKIN_D, 0.75)                           # under the brim
    if y == 2 and (abs(x - cx) > 1.5):
        return STACHE                                      # bushy brows
    if y in (3, 4) and 2 <= abs(x - cx) <= 4:
        if y == 3:
            return (34, 26, 24) if abs(x - cx) < 4 else SKIN_D
        return SKIN_D                                      # bags under the squint
    if 4 <= y <= 6 and abs(x - cx) <= 1:
        return NOSE if y < 6 else mul(NOSE, 0.85)
    if y in (7, 8) and abs(x - cx) <= 5.5:
        return STACHE_L if (x + y) % 3 == 0 else STACHE   # the walrus moustache
    if y == 9 and 1.5 <= abs(x - cx) <= 4.5:
        if round(x - cx) == 2:
            return GOLD                                    # the gold tooth
        return (238, 228, 210) if abs(x - cx) < 4 else (80, 30, 30)
    if y >= 10 and (x <= 1 or x >= w - 2):
        return SKIN_D                                      # jowls
    return skin(6)(face_, x, y, w, h)


def face_glow(face_, x, y, w, h):
    if face_ != "front":
        return None
    cx = (w - 1) / 2
    if y == 3 and 2 <= abs(x - cx) < 3:
        return GOLD                                        # a greedy gleam in each eye
    if y == 9 and round(x - cx) == 2:
        return GOLD_L
    return None


def hardhat(seed=0):
    """The brass miner's hard hat: a dented dome, a raised ridge down the middle, soot on the crown."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return B.BRASS_DD
        if face == "top":
            if x == w // 2 or x == w // 2 - 1:
                return B.BRASS_L
            c = mul(B.BRASS, 1.0 + (B.n(x, y, seed) - 0.5) * 0.1)
            return mix(c, B.SOOT, 0.35) if B.n(x // 3, y // 3, seed + 1) < 0.2 else c
        if y == h - 1:
            return B.BRASS_D
        if y == 0:
            return B.BRASS_L
        return mul(B.BRASS, 1.05 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def lamp(face_, x, y, w, h):
    """The helmet lantern: a brass bezel round a big round lens."""
    if face_ != "front":
        return brass(77)(face_, x, y, w, h)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r > min(w, h) / 2 - 0.6:
        return B.BRASS_D
    return LAMP_L if r < 1.2 else LAMP


def lamp_glow(face_, x, y, w, h):
    if face_ != "front":
        return None
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = math.hypot(x - cx, y - cy)
    if r > min(w, h) / 2 - 0.6:
        return None
    return LAMP_L if r < 1.6 else LAMP


def drill_bit(seed=0):
    """A spiral steel bit: a bright flute that winds round the bit, dark grooves between."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STEEL_D if face == "bottom" else STEEL
        off = {"front": 0, "right": 1, "back": 2, "left": 3}.get(face, 0) * w
        k = (x + off + y * 2) % 6
        if k == 0:
            return STEEL_L
        if k in (1, 2):
            return STEEL
        if k == 3:
            return mul(STEEL, 0.85)
        return STEEL_D
    return f


def ore(seed=0, copper_share=0.35):
    """A crust of raw ore: grey stone, gold nuggets and copper streaks, lit top edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return ORE_STONE_D
        n1 = B.n(x, y, seed)
        n2 = B.n(x // 2, y // 2, seed + 7)
        if n2 < 0.3:
            return GOLD if n1 < 0.6 else GOLD_D
        if n2 < 0.3 + copper_share * 0.4:
            return ORE_COPPER if n1 < 0.55 else mul(ORE_COPPER, 0.75)
        c = mul(ORE_STONE, 1.08 - 0.25 * y / max(1, h) + (n1 - 0.5) * 0.18)
        if face == "top" or y == 0:
            c = mix(c, (220, 214, 200), 0.25)
        return c
    return f


def ore_glow(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        if B.n(x // 2, y // 2, seed + 7) < 0.12 and B.n(x, y, seed) < 0.5:
            return GOLD
        return None
    return f


def geode(face_, x, y, w, h):
    """A gold geode growing out of the boiler: faceted crystal, bright core."""
    cx, cy = (w - 1) / 2, (h - 1) / 2
    if abs(x - cx) + abs(y - cy) < min(w, h) / 2.2:
        return GOLD_L
    return GOLD if (x + y) % 2 else GOLD_D


def geode_glow(face_, x, y, w, h):
    cx, cy = (w - 1) / 2, (h - 1) / 2
    return GOLD_L if abs(x - cx) + abs(y - cy) < min(w, h) / 2.0 else GEODE


def boot(seed=0):
    """Hobnailed iron-shod boots."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return B.IRON_D
        if face == "top":
            return LEATHER
        if y >= h - 2:
            return B.IRON_L if x % 2 == 0 and y == h - 1 else B.IRON
        return mul(LEATHER, 1.05 - 0.2 * y / max(1, h))
    return f


def haft(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WOOD_D
        if y % 9 in (0, 1) and y < 12:
            return LEATHER_D                               # leather grip wraps
        return mul(WOOD, 1.0 + (B.n(x, y // 3, seed) - 0.5) * 0.2)
    return f


def hammer_head(seed=0):
    """The pickaxe-hammer's head: a battered iron block, its striking face bright and pitted."""
    def f(face, x, y, w, h):
        if face == "front":
            return STEEL_L if B.n(x, y, seed) > 0.25 else STEEL
        return iron(seed)(face, x, y, w, h)
    return f


def pick_spike(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return STEEL_D
        return mix(STEEL, B.IRON, 0.4 + 0.4 * y / max(1, h)) if face != "top" else STEEL_L
    return f


def strap(face, x, y, w, h):
    if face in ("top", "bottom"):
        return LEATHER_D
    return B.BRASS if (y % 5 == 2 and x == w // 2) else LEATHER


def dynamite(face, x, y, w, h):
    """A bundle of red sticks round the bandolier."""
    if face in ("top", "bottom"):
        return (226, 210, 180) if (x + y) % 2 else (180, 40, 34)
    return (196, 46, 38) if x % 2 else (160, 32, 28)


# ---------------------------------------------------------------- build
def build(variant=None):
    variant = variant or "bare"
    gilded = variant == "gilded"
    cracked = variant == "cracked"
    m = Model("mine_baron", seed=919, shadow=2.0, walk_speed=0.6, walk_scale=0.8, variants=VARIANTS)

    def box(part, x, y, z, w, h, d, paint, glow=None, kind="core", k=0):
        """kind: core (always), ore (the crust: only gilded, and half of it cracked: k odd stays), geode (the back
        weak spots: four gilded, the first two cracked)."""
        if kind == "ore":
            if not (gilded or (cracked and k % 2 == 1)):
                paint, glow = _gone, None
        elif kind == "geode":
            if not (gilded or (cracked and k < 2)):
                paint, glow = _gone, None
        m.box(part, x, y, z, w, h, d, paint, glow=glow)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -34, 0))
    m.part("chest", "hips", pivot=(0, -6, 0), rot=(6, 0, 0))
    m.part("belly", "chest", pivot=(0, 0, 0))
    m.part("boiler", "chest", pivot=(0, -26, 8))
    m.part("head", "chest", pivot=(0, -40, -4), rot=(-6, 0, 0), scale=(1.3, 1.3, 1.3))
    m.part("arm_r", "chest", pivot=(-19, -36, 0), rot=(-6, 0, 10))
    m.part("fore_r", "arm_r", pivot=(-1, 14, 0), rot=(-52, 0, -4))
    m.part("drill", "fore_r", pivot=(0, 14, 0))
    m.part("arm_l", "chest", pivot=(19, -36, 0), rot=(4, 0, -12))
    m.part("fore_l", "arm_l", pivot=(1, 13, 0), rot=(-24, 0, 6))
    m.part("pick", "fore_l", pivot=(0, 14, -1), rot=(14, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "bone", pivot=(8 * sx, -34, 0), rot=(0, 0, -5 * sx))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 17, 0), rot=(0, 0, 5 * sx))

    # ---- legs: piston thighs in an iron frame, brass knee hubs, iron-shod boots
    for side, sx in (("r", -1), ("l", 1)):
        t, s = f"thigh_{side}", f"shin_{side}"
        box(t, -5, 0, -5, 10, 15, 10, iron(10 + sx))
        box(t, 5.5 * sx - 1.5, 2, -1.5, 3, 12, 3, piston(12 + sx))
        box(t, -6, 14, -6, 12, 5, 12, brass(14 + sx))                               # knee hub
        box(t, -2, 15, -7, 4, 3, 1, B.gauge())                                     # a knee gauge
        box(s, -4.5, 1, -4.5, 9, 13, 9, iron(20 + sx))
        box(s, -1, 2, -6, 2, 11, 2, piston(22 + sx))                               # the shin piston
        box(s, -6.5, 12, -10, 13, 5, 17, boot(24 + sx))                              # boots
        box(s, -7, 15, -11, 14, 2, 19, iron(26 + sx))                               # iron sole
        box(t, -6, 3, -6, 12, 6, 1, ore(30 + sx), glow=ore_glow(30 + sx), kind="ore", k=1)

    # ---- hips: the rig's pelvis frame, a leather belt with a bandolier of dynamite
    box("hips", -11, -4, -8, 22, 9, 16, iron(40))
    box("hips", -12, -6, -10, 24, 3, 19, strap)                                   # belt
    box("hips", -3, -6.5, -10.5, 6, 4, 1, brass(41))                               # buckle
    for i, x in enumerate((-10, -6, 6, 10)):
        box("hips", x - 1, -3, -10, 3, 6, 2, dynamite)
    box("hips", 11, -2, -4, 2, 7, 8, copper(42))                                   # a tool pouch / pipe junction

    # ---- the body: a barrel belly in a burgundy waistcoat, a broad chest in rolled shirt, the rig's shoulder frame
    box("belly", -13, -22, -12, 26, 20, 21, vest(50, chain=True))
    box("belly", -11, -6, -14, 22, 6, 3, vest(51, buttons=False))                # the overhang of the gut
    box("chest", -15, -38, -9, 30, 16, 18, shirt(52))
    box("chest", -9, -38, -10, 18, 14, 1, vest(53))                               # waistcoat top under the frame
    box("chest", -16, -40, -6, 32, 3, 13, iron(54))                               # shoulder yoke
    box("chest", -15, -37, -11, 3, 18, 2, strap)                                  # harness straps
    box("chest", 12, -37, -11, 3, 18, 2, strap)
    box("chest", -6, -42, -6, 12, 4, 10, skin(55))                                 # thick neck
    box("chest", -4, -30, -11, 8, 6, 2, B.gauge())                                # chest pressure gauge
    box("chest", -19, -42, -8, 6, 8, 16, ore(56), glow=ore_glow(56), kind="ore", k=1)   # ore on the shoulders
    box("chest", 13, -42, -8, 6, 8, 16, ore(57), glow=ore_glow(57), kind="ore", k=2)
    box("belly", -15, -21, -15, 9, 13, 5, ore(58), glow=ore_glow(58), kind="ore", k=3)  # ore across the belly
    box("belly", 6, -17, -15, 10, 11, 5, ore(59), glow=ore_glow(59), kind="ore", k=4)
    box("chest", -12, -36, -12, 9, 8, 3, ore(60), glow=ore_glow(60), kind="ore", k=5)

    # ---- the boiler on his back: banded copper drum, two smokestacks, a firebox grate, pipes over the shoulders
    box("boiler", -9, -12, 0, 18, 24, 11, B.bands(B.COPPER, B.COPPER_D, every=4, seed=60))
    box("boiler", -7, 6, 10, 14, 6, 2, B.grate(fire=B.AMBER), glow=B.grate_glow())  # firebox at the bottom
    box("boiler", -7, -24, 4, 4, 13, 4, B.soot(seed=61))                           # smokestacks
    box("boiler", 3, -28, 3, 5, 17, 5, B.soot(seed=62))
    box("boiler", 2, -29, 2, 7, 2, 7, B.IRON_D)
    box("boiler", -10, -14, 3, 20, 2, 6, iron(63))                                # top band
    box("boiler", -12, -15, -2, 3, 3, 3, copper(64))                               # pipes to the arms
    box("boiler", 9, -15, -2, 3, 3, 3, copper(65))
    box("boiler", -3, -6, 10, 6, 6, 1, B.gauge())
    # the weak spots of the gold-greed: four glowing geodes on the drum (the first two last)
    for k, (x, y) in enumerate(((-8, -10), (4, -10), (-8, 1), (4, 1))):
        box("boiler", x, y, 10, 5, 5, 3, geode, glow=geode_glow, kind="geode", k=k)
    box("boiler", -10, -12, 9, 20, 8, 3, ore(66), glow=ore_glow(66), kind="ore", k=7)

    # ---- the head: jowly face, moustache, a brass hard hat with a big lantern
    box("head", -7, -12, -7, 14, 12, 12, face, glow=face_glow)
    box("head", -8, -4, -6, 16, 4, 10, skin(70))                                   # jowls
    box("head", -8, -17, -8, 16, 6, 15, hardhat(71))                               # the dome
    box("head", -10, -12, -10, 20, 2, 19, hardhat(72))                             # the brim
    box("head", -3, -19, -12, 6, 6, 4, lamp, glow=lamp_glow)                       # the lantern
    box("head", -4, -20, -11, 8, 1, 3, brass(73))                                  # its hood
    box("head", -1, -21, 0, 2, 4, 2, copper(74))                                   # the lamp's carbide tank
    box("head", -9, -18, -6, 4, 4, 9, ore(75), glow=ore_glow(75), kind="ore", k=9)

    # ---- right arm: the pneumatic drill (piston upper arm, brass motor casing, a long spiral bit)
    box("arm_r", -8, -6, -7, 13, 10, 14, iron(80))                                 # rig pauldron
    box("arm_r", -4, 2, -4, 8, 13, 8, shirt(81))
    box("arm_r", -6, 3, -1.5, 2, 11, 3, piston(82))
    box("arm_r", -10, -9, -6, 8, 5, 12, ore(83), glow=ore_glow(83), kind="ore", k=11)
    box("fore_r", -6, 0, -6, 12, 15, 12, brass(84))                                # motor casing
    box("fore_r", -6.5, 4, -6.5, 13, 2, 13, B.IRON_D)
    box("fore_r", -6.5, 10, -6.5, 13, 2, 13, B.IRON_D)
    box("fore_r", -7, 2, -7, 3, 8, 14, ore(85), glow=ore_glow(85), kind="ore", k=13)
    box("drill", -5, 0, -5, 10, 3, 10, B.IRON)                                    # chuck
    box("drill", -4.5, 3, -4.5, 9, 6, 9, drill_bit(90))
    box("drill", -3.5, 9, -3.5, 7, 6, 7, drill_bit(91))
    box("drill", -2.5, 15, -2.5, 5, 6, 5, drill_bit(92))
    box("drill", -1.5, 21, -1.5, 3, 5, 3, drill_bit(93))
    box("drill", -0.5, 26, -0.5, 1, 3, 1, STEEL_L)

    # ---- left arm: a meaty arm in a rolled sleeve, the rig's brace, a fist round the pickaxe-hammer's haft
    box("arm_l", -4, -6, -7, 12, 10, 14, iron(100))                                # rig pauldron
    box("arm_l", -4, 2, -4, 8, 12, 8, shirt(101))
    box("arm_l", 4, 3, -1.5, 2, 10, 3, piston(102))
    box("arm_l", 2, -9, -6, 8, 5, 12, ore(103), glow=ore_glow(103), kind="ore", k=15)
    box("fore_l", -3.5, 0, -3.5, 7, 11, 7, skin(104))
    box("fore_l", -4, 3, -4, 8, 3, 8, iron(105))                                   # bracer
    box("fore_l", -4, 10, -4, 8, 6, 8, skin(106))                                  # the fist
    box("fore_l", 3, 4, -3, 2, 6, 6, ore(107), glow=ore_glow(107), kind="ore", k=17)
    box("pick", -1.5, -10, -1.5, 3, 42, 3, haft(110))                              # the haft
    box("pick", -5, 28, -13, 10, 10, 12, hammer_head(111))                          # hammer face (front)
    box("pick", -3.5, 29.5, -1, 7, 7, 3, iron(112))                                    # the eye collar
    box("pick", -3, 30.5, 2, 6, 5, 7, pick_spike(113))                           # the pick (back), tapering
    box("pick", -2, 31, 9, 4, 4, 6, pick_spike(114))
    box("pick", -1, 32, 15, 2, 2, 4, STEEL_L)

    _anims(m)
    return m


def _anims(m):
    # idle: heavy breathing (the belly heaves), the boiler chuffs, the drill bit idles round, the head looks about
    idle = m.anim("idle", 4.0)
    idle.scale("belly", (0, (1, 1, 1)), (2.0, (1.03, 1.02, 1.04)), (4.0, (1, 1, 1)))
    idle.rot("chest", (0, (0, 0, 0)), (2.0, (-2, 0, 0)), (4.0, (0, 0, 0)))
    idle.pos("boiler", (0, (0, 0, 0)), (0.5, (0, 0.6, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0.6, 0)), (2.0, (0, 0, 0)),
             (2.5, (0, 0.6, 0)), (3.0, (0, 0, 0)), (3.5, (0, 0.6, 0)), (4.0, (0, 0, 0)))
    idle.rot("drill", (0, (0, 0, 0)), (4.0, (0, 720, 0), "linear"))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (0, 12, 0)), (3.0, (2, -10, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (2, 0, -2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 2.0)
    walk.rot("thigh_r", (0, (-18, 0, 0)), (1.0, (18, 0, 0)), (2.0, (-18, 0, 0)))
    walk.rot("thigh_l", (0, (18, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (18, 0, 0)))
    walk.rot("shin_r", (0, (8, 0, 0)), (0.5, (26, 0, 0)), (1.0, (0, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (8, 0, 0)), (1.5, (26, 0, 0)), (2.0, (0, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, 1.6, 0)), (1.0, (0, 0, 0)), (1.5, (0, 1.6, 0)), (2.0, (0, 0, 0)))
    walk.rot("chest", (0, (0, -5, 3)), (1.0, (0, 5, -3)), (2.0, (0, -5, 3)))
    walk.rot("arm_r", (0, (8, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("arm_l", (0, (-6, 0, 0)), (1.0, (6, 0, 0)), (2.0, (-6, 0, 0)))
    walk.scale("belly", (0, (1, 1, 1)), (0.5, (1.02, 0.98, 1.02)), (1.0, (1, 1, 1)), (1.5, (1.02, 0.98, 1.02)),
               (2.0, (1, 1, 1)))

    # drill (16 / 14 / 16 ticks = 2.3 s): the drill arm drawn back at the hip (0.8 s), thrust straight ahead and held
    # spinning (hits at 0.8, 1.05, 1.3 s), pulled back
    a = m.anim("drill", 2.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (34, -10, 14)), (0.8, (36, -10, 14)), (0.86, (-62, 0, 0), "linear"),
          (1.5, (-64, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.8, (-28, 0, 0)), (0.86, (24, 0, 0), "linear"), (1.5, (26, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("drill", (0, (0, 0, 0)), (0.8, (0, 180, 0)), (1.5, (0, 1440, 0), "linear"), (2.3, (0, 1800, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-4, 26, 0)), (0.86, (10, -16, 0), "linear"), (1.5, (10, -16, 0)),
          (2.3, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.8, (12, 0, 0)), (0.86, (-24, 0, 0), "linear"), (1.5, (-24, 0, 0)),
          (2.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.8, (0, 0, 2)), (0.86, (0, -1.5, -3), "linear"), (1.5, (0, -1.5, -3)),
          (2.3, (0, 0, 0)))

    # slam (20 / 4 / 16 = 2.0 s): the pickaxe-hammer heaved over the left shoulder in both hands (1.0 s), brought down
    a = m.anim("slam", 2.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-168, -10, -6)), (1.0, (-174, -10, -6)), (1.08, (-46, 0, 0), "linear"),
          (1.5, (-44, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (10, 0, 0), "linear"), (2.0, (0, 0, 0)))
    a.rot("pick", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (-6, 0, 0), "linear"), (1.5, (-6, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.0, (-130, 20, 20)), (1.08, (-30, 0, 10), "linear"), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-18, -10, 0)), (1.08, (22, 0, 0), "linear"), (1.5, (20, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1.5, 0)), (1.08, (0, -4, -1), "linear"), (1.5, (0, -4, -1)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-14, 0, 0)), (1.08, (10, 0, 0), "linear"), (2.0, (0, 0, 0)))

    # charge (18 / 16 / 18 = 2.6 s): crouched behind the drill (0.9 s), then a rush with the drill out (to 1.7 s)
    a = m.anim("charge", 2.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-70, 0, 10)), (0.9, (-74, 0, 10)), (1.7, (-74, 0, 6)), (2.6, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (1.7, (40, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("drill", (0, (0, 0, 0)), (0.9, (0, 360, 0)), (1.7, (0, 2160, 0), "linear"), (2.6, (0, 2520, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (24, 0, 0)), (1.7, (26, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (1.7, (-20, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (30, 0, -20)), (1.7, (30, 0, -20)), (2.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.9, (-20, 0, 0)), (1.1, (24, 0, 0)), (1.3, (-24, 0, 0)), (1.5, (24, 0, 0)),
          (1.7, (-10, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (16, 0, 0)), (1.1, (-24, 0, 0)), (1.3, (24, 0, 0)), (1.5, (-24, 0, 0)),
          (1.7, (10, 0, 0)), (2.6, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.9, (0, -3, 0)), (1.7, (0, -3, 0)), (2.6, (0, 0, 0)))

    # dynamite (18 / 24 / 14 = 2.8 s): a bundle lit on the helmet lamp (0.9 s), then three throws at 0.9, 1.1, 1.3 s
    a = m.anim("dynamite", 2.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-150, 0, -20)), (0.8, (-150, 0, -24)), (0.9, (-160, 0, 0)),
          (0.95, (-60, 0, 0), "linear"), (1.05, (-150, 0, 0)), (1.15, (-60, 0, 0), "linear"), (1.25, (-150, 0, 0)),
          (1.35, (-60, 0, 0), "linear"), (2.1, (-50, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (0.9, (-40, 0, 0)), (1.35, (0, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-8, 20, 0)), (0.95, (8, -10, 0), "linear"), (1.35, (8, -10, 0)),
          (2.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (20, -20, 0)), (0.8, (20, -20, 0)), (0.9, (0, 0, 0)), (2.8, (0, 0, 0)))

    # exhaust (14 / 4 / 12 = 1.5 s): a whistle; he hunches and the boiler blasts steam out behind him (0.7 s)
    a = m.anim("exhaust", 1.5)
    a.rot("chest", (0, (0, 0, 0)), (0.6, (16, 0, 0)), (0.7, (18, 0, 0)), (0.76, (-8, 0, 0), "linear"), (1.5, (0, 0, 0)))
    a.pos("boiler", (0, (0, 0, 0)), (0.6, (0, -1, -1)), (0.7, (0, -1, -1.5)), (0.76, (0, 1, 3), "linear"),
          (1.5, (0, 0, 0)))
    a.scale("boiler", (0, (1, 1, 1)), (0.7, (1.08, 1.04, 1.1)), (0.76, (0.94, 1, 0.94), "linear"), (1.5, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (10, 0, 20)), (0.76, (-20, 0, 30), "linear"), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (10, 0, -20)), (0.76, (-20, 0, -30), "linear"), (1.5, (0, 0, 0)))

    # cavein (22 / 30 / 14 = 3.3 s): the pickaxe-hammer raised and struck on the floor (1.1 s), then he roars upward
    a = m.anim("cavein", 3.3)
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-150, 0, -30)), (1.1, (-156, 0, -30)), (1.16, (-40, 0, 0), "linear"),
          (2.4, (-40, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("pick", (0, (0, 0, 0)), (1.1, (-20, 0, 0)), (1.16, (-10, 0, 0), "linear"), (3.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.1, (-60, 0, 30)), (1.3, (-150, 0, 30)), (2.4, (-150, 0, 30)), (3.3, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-14, 0, 0)), (1.16, (20, 0, 0), "linear"), (1.5, (-16, 0, 0)),
          (2.4, (-16, 0, 0)), (3.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.16, (10, 0, 0)), (1.5, (-34, 0, 0)), (2.4, (-34, 0, 0)), (3.3, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.1, (0, 1, 0)), (1.16, (0, -3, 0), "linear"), (1.5, (0, 0, 0)), (3.3, (0, 0, 0)))

    # combo (14 / 30 / 14 = 2.9 s): drill jab (0.7 s), pickaxe backhand (1.2 s), overhead slam (1.8 s)
    a = m.anim("combo", 2.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (30, 0, 10)), (0.7, (32, 0, 10)), (0.76, (-70, 0, 0), "linear"),
          (1.0, (-60, 0, 0)), (1.2, (-20, 0, 20)), (1.6, (-140, 0, 20)), (1.8, (-140, 0, 20)), (1.86, (-40, 0, 10), "linear"),
          (2.9, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.7, (-30, 0, 0)), (0.76, (30, 0, 0), "linear"), (1.2, (0, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-40, 0, 0)), (1.1, (-80, 70, -40)), (1.2, (-82, 74, -42)),
          (1.26, (-70, -60, -20), "linear"), (1.6, (-170, 0, -10)), (1.8, (-174, 0, -10)), (1.86, (-46, 0, 0), "linear"),
          (2.4, (-44, 0, 0)), (2.9, (0, 0, 0)))
    a.rot("pick", (0, (0, 0, 0)), (1.2, (20, 0, 0)), (1.26, (0, 0, 0), "linear"), (1.8, (-30, 0, 0)),
          (1.86, (-6, 0, 0), "linear"), (2.9, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-4, 24, 0)), (0.76, (10, -18, 0), "linear"), (1.2, (0, 40, 0)),
          (1.26, (6, -40, 0), "linear"), (1.8, (-18, 0, 0)), (1.86, (22, 0, 0), "linear"), (2.4, (20, 0, 0)),
          (2.9, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.8, (0, 1.5, 0)), (1.86, (0, -4, -1), "linear"), (2.4, (0, -4, -1)), (2.9, (0, 0, 0)))

    # veinburst (20 / 20 / 16 = 2.8 s): the drill raised high and driven into the floor (1.0 s), held there grinding
    a = m.anim("veinburst", 2.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-150, 0, 20)), (1.0, (-156, 0, 20)), (1.06, (-20, 0, 6), "linear"),
          (2.0, (-20, 0, 6)), (2.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.06, (10, 0, 0), "linear"), (2.0, (10, 0, 0)), (2.8, (0, 0, 0)))
    a.rot("drill", (0, (0, 0, 0)), (1.0, (0, 360, 0)), (2.0, (0, 2160, 0), "linear"), (2.8, (0, 2520, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.06, (26, 0, 0), "linear"), (2.0, (24, 0, 0)), (2.8, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (1.0, (0, 1, 0)), (1.06, (0, -5, 0), "linear"), (2.0, (0, -5, 0)), (2.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.06, (20, 0, -30), "linear"), (2.0, (20, 0, -30)), (2.8, (0, 0, 0)))

    # fuseline (16 / 40 / 14 = 3.5 s): a keg swung underarm and lobbed (0.8 s), then he holds the drill to the fuse
    a = m.anim("fuseline", 3.5)
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (50, 0, -10)), (0.8, (54, 0, -10)), (0.86, (-110, 0, -10), "linear"),
          (1.3, (-60, 0, -10)), (2.8, (-50, 0, -10)), (3.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (0, 0, 10)), (1.2, (-40, 30, 0)), (2.8, (-40, 30, 0)), (3.5, (0, 0, 0)))
    a.rot("drill", (0, (0, 0, 0)), (1.2, (0, 0, 0)), (2.8, (0, 1440, 0), "linear"), (3.5, (0, 1800, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (8, 0, 0)), (0.86, (-12, 0, 0), "linear"), (1.3, (6, 10, 0)), (2.8, (6, 10, 0)),
          (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.3, (16, 20, 0)), (2.8, (16, 20, 0)), (3.5, (0, 0, 0)))

    # greed (the phase-2 roar, also the re-gilding: 30 / 10 / 10 = 2.5 s): arms out, the ore crawls over him, the crust
    # locks on at 1.5 s
    a = m.anim("greed", 2.5)
    a.rot("arm_r", (0, (0, 0, 0)), (1.3, (-100, 0, 60)), (1.5, (-104, 0, 64)), (1.56, (-30, 0, 20), "linear"),
          (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.3, (-100, 0, -60)), (1.5, (-104, 0, -64)), (1.56, (-30, 0, -20), "linear"),
          (2.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.3, (-20, 0, 0)), (1.5, (-22, 0, 0)), (1.56, (10, 0, 0), "linear"), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.3, (-30, 0, 0)), (1.56, (6, 0, 0), "linear"), (2.5, (0, 0, 0)))
    a.scale("belly", (0, (1, 1, 1)), (1.3, (1.1, 1.06, 1.12)), (1.5, (1.12, 1.08, 1.14)), (1.56, (0.98, 1, 0.98), "linear"),
            (2.5, (1, 1, 1)))
    a.pos("hips", (0, (0, 0, 0)), (1.5, (0, 2, 0)), (1.56, (0, -2, 0), "linear"), (2.5, (0, 0, 0)))

    # orebreak (10 / 60 / 10 = 4.0 s): the last geode knocked off: he drops to one knee, dazed, the drill sputtering
    a = m.anim("orebreak", 4.0)
    a.rot("chest", (0, (0, 0, 0)), (0.5, (30, 0, 10)), (3.5, (26, 0, 8)), (4.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.5, (0, -10, 0)), (3.5, (0, -9, 0)), (4.0, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.5, (-80, 0, 0)), (3.5, (-76, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.5, (80, 0, 0)), (3.5, (76, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.5, (10, 0, -10)), (3.5, (10, 0, -10)), (4.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.5, (80, 0, 0)), (3.5, (78, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (20, 0, 30)), (3.5, (16, 0, 26)), (4.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-30, 0, -20)), (3.5, (-30, 0, -20)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (1.2, (20, 14, 6)), (2.0, (24, -12, -6)), (2.8, (20, 10, 4)),
          (3.5, (24, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("drill", (0, (0, 0, 0)), (0.5, (0, 90, 0)), (1.0, (0, 60, 0)), (1.6, (0, 200, 0)), (2.4, (0, 160, 0)),
          (3.5, (0, 400, 0)), (4.0, (0, 360, 0)))

    # blackout (phase 3, once: 30 / 20 / 20 = 3.5 s): bundles flung at the props round the walls (1.5 s), then he
    # throws his arms up as the cavern goes dark
    a = m.anim("blackout", 3.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-150, 0, -10)), (0.5, (-60, 0, 0), "linear"), (0.8, (-150, 0, 10)),
          (0.9, (-60, 0, 0), "linear"), (1.2, (-150, 0, -10)), (1.3, (-60, 0, 0), "linear"), (1.5, (-120, 0, 60)),
          (2.6, (-120, 0, 60)), (3.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.3, (0, 0, -10)), (1.5, (-120, 0, -60)), (2.6, (-120, 0, -60)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.4, (-6, 20, 0)), (0.8, (-6, -20, 0)), (1.2, (-6, 10, 0)), (1.5, (-20, 0, 0)),
          (2.6, (-20, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.5, (-30, 0, 0)), (2.6, (-30, 0, 0)), (3.5, (0, 0, 0)))

    # glare (phase 3: 18 / 10 / 12 = 2.0 s): head lowered, the lamp turned on full (0.9 s): he stares the beam ahead
    a = m.anim("glare", 2.0)
    a.rot("head", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (0.9, (16, 0, 0)), (0.94, (-6, 0, 0), "linear"), (1.4, (-6, 0, 0)),
          (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (14, 0, 0)), (0.94, (-4, 0, 0), "linear"), (1.4, (-4, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-40, 0, 10)), (1.4, (-40, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-20, 0, -10)), (1.4, (-20, 0, -10)), (2.0, (0, 0, 0)))

    # stagger: the rig seizes, he sags, steam leaking
    a = m.anim("stagger", 2.5)
    a.rot("chest", (0, (0, 0, 0)), (0.2, (22, 0, -10)), (1.8, (18, 0, -8)), (2.5, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.2, (0, -5, 0)), (1.8, (0, -4, 0)), (2.5, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.2, (-26, 0, 0)), (1.8, (-22, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.2, (44, 0, 0)), (1.8, (40, 0, 0)), (2.5, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (24, 0, 30)), (1.8, (20, 0, 26)), (2.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (20, 0, -30)), (1.8, (16, 0, -26)), (2.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.2, (20, 10, 0)), (1.0, (16, -8, 0)), (1.8, (20, 10, 0)), (2.5, (0, 0, 0)))
