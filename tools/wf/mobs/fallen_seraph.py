"""The Fallen Seraph (Le Séraphin déchu): the guardian of the Shattered Halo, a haloed angel of the broken ring who
floats over the arena disc, about 5.4 blocks tall with the halo.

Silhouette idea: a tall robed figure with no feet, hovering, framed from behind by a great broken halo of gold
(a ring of segments with a gap torn out of its upper right and one shard drifting loose) and two huge wings. Six
smaller halo shards orbit her waist: they are her projectiles. Asymmetry: her right wing is whole, white and gold;
her left wing is burnt to the void, short and ragged, its feathers dark purple with glowing cracks. The same void
creeps up her robe from the hem. A gold blindfold hides her eyes; a long glaive whose blade is a crescent cut from
a halo rests in her right hand, the left hand is bare and cracked with light.
"""
import math

from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

WHITE = (238, 234, 226)
WHITE_L = (252, 250, 244)
WHITE_D = (190, 184, 182)
MARBLE = (226, 222, 234)
MARBLE_D = (168, 162, 182)
GOLD = (236, 190, 80)
GOLD_L = (255, 234, 150)
GOLD_D = (164, 116, 38)
VOID = (52, 26, 78)
VOID_D = (24, 11, 38)
VOID_L = (96, 58, 136)
CRACK = (214, 160, 255)
CRACK_L = (246, 226, 255)
LIGHT = (255, 248, 214)
HAIR = (238, 222, 172)
HAIR_D = (196, 172, 116)


# ---------------------------------------------------------------- paint
def robe(seed=0, void_from=0.55):
    """White linen in long vertical folds; from ``void_from`` (fraction of the height) down, the void creeps up the
    cloth: darker and darker, with glowing cracks."""
    def f(face, x, y, w, h):
        if face == "top":
            return WHITE_L
        if face == "bottom":
            return VOID_D
        t = y / max(1, h - 1)
        fold = 1.04 if x % 3 == 0 else (0.94 if x % 3 == 2 else 1.0)
        c = mul(WHITE, fold * (1.03 - 0.08 * t) + (B.n(x, y, seed) - 0.5) * 0.05)
        if t > void_from:
            k = min(1.0, (t - void_from) / max(0.05, 1 - void_from) * 1.3 + (B.n(x, y // 2, seed + 1) - 0.5) * 0.5)
            if k > 0:
                c = mix(c, VOID if k < 0.8 else VOID_D, min(1.0, k))
        return c
    return f


def robe_glow(seed=0, void_from=0.55):
    """The cracks of light in the voided cloth."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        t = y / max(1, h - 1)
        if t > void_from + 0.15 and (x * 7 + y * 3 + seed) % 11 == 0 and B.n(x, y, seed + 5) < 0.6:
            return CRACK
        return None
    return f


def gold(seed=0, band_every=0):
    """Polished gold with a lit top edge; optional engraved lines every ``band_every`` rows."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        if face == "top":
            return GOLD_L
        if band_every and y % band_every == band_every - 1:
            return GOLD_D
        if y == 0:
            return GOLD_L
        return mul(GOLD, 1.08 - 0.2 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def hem(seed=0):
    """Gold hem band on the robe, a row of void below it."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return GOLD_D
        if y == 0:
            return GOLD_L
        return GOLD if (x + seed) % 4 else GOLD_D
    return f


def marble(seed=0, cracks=0.0):
    """Pale marble skin, with fine dark veins (cracks > 0 adds glowing fractures, see marble_glow)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return MARBLE_D
        c = mul(MARBLE, 1.04 - 0.1 * y / max(1, h) + (B.n(x, y, seed) - 0.5) * 0.06)
        if (x + 2 * y + seed) % 9 == 0 and B.n(x, y, seed + 2) < 0.5:
            c = mul(c, 0.82)
        return c
    return f


def marble_glow(seed=0, amount=0.12):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if (x * 5 + y * 2 + seed) % 7 == 0 and B.n(x, y, seed + 9) < amount * 4:
            return CRACK_L
        return None
    return f


def face_paint(f, x, y, w, h):
    """Marble face under a gold blindfold, a calm mouth; long pale hair on the sides and back."""
    if f == "top":
        return HAIR
    if f == "bottom":
        return MARBLE_D
    if f in ("left", "right", "back"):
        return mul(HAIR, 1.0 if (x + y // 3) % 3 else 0.84)
    # front
    if y < 2:
        return mul(HAIR, 1.0 if x % 3 else 0.86)
    if y in (3, 4):
        if x in (2, w - 3) and y == 4:
            return CRACK_L
        return GOLD_L if y == 3 else GOLD
    if y == 7 and 3 <= x <= w - 4:
        return mul(MARBLE_D, 0.8)
    return marble(32)(f, x, y, w, h)


def face_glow(f, x, y, w, h):
    if f == "front" and y == 4 and x in (2, w - 3):
        return CRACK_L
    if f == "front" and y == 5 and x in (2, w - 3):
        return CRACK            # light weeping from under the blindfold
    return None


def feathers(light, mid, dark, seed=0, ragged=0.0):
    """Long feathers: vertical vanes with a dark shaft, tips darker; ``ragged`` cuts holes in them."""
    def f(face, x, y, w, h):
        if ragged and y > h * 0.45 and B.n(x, y // 3, seed + 3) < ragged:
            return None
        if face == "top":
            return light
        if face == "bottom":
            return dark
        t = y / max(1, h - 1)
        if x == w // 2 and w > 2:
            return mul(dark, 1.05)
        c = mix(light, mid, min(1.0, t * 1.2))
        if t > 0.8:
            c = mix(c, dark, (t - 0.8) * 4)
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.08)
    return f


def void_feather_glow(seed=0):
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return None
        if x == w // 2 and (y + seed) % 4 == 0:
            return CRACK
        return None
    return f


def halo_paint(f, x, y, w, h):
    """The halo's gold: bright face, an inner line of light."""
    if f == "bottom":
        return GOLD_D
    if f in ("front", "back") and y == h - 1:
        return LIGHT
    return mul(GOLD_L if y == 0 else GOLD, 1.0 + (B.n(x, y, 77) - 0.5) * 0.08)


def halo_glow(f, x, y, w, h):
    if f in ("front", "back", "top", "bottom"):
        return LIGHT if y == h - 1 or f in ("top", "bottom") else GOLD_L
    return None


def shard_paint(f, x, y, w, h):
    if f == "bottom":
        return GOLD_D
    return GOLD_L if (x + y) % 3 else LIGHT


def shard_glow(f, x, y, w, h):
    return LIGHT if (x + y) % 2 == 0 else GOLD_L


# ---------------------------------------------------------------- model
def build():
    m = Model("fallen_seraph", seed=161, shadow=1.4, walk_speed=0.7, walk_scale=0.6, glow_pulse=0.08)

    m.part("bone", pivot=(0, 24, 0))
    m.part("float", "bone", pivot=(0, -12, 0))                   # she hovers: the robe ends 7 px above the floor
    m.part("hem", "float", pivot=(0, 0, 0))
    m.part("waist", "float", pivot=(0, -26, 0))
    m.part("chest", "waist", pivot=(0, -2, 0), rot=(4, 0, 0))
    m.part("head", "chest", pivot=(0, -18, -0.5), rot=(-6, 0, 0))
    m.part("halo", "head", pivot=(0, -13, 8), rot=(-8, 0, 6))
    m.part("wing_r", "chest", pivot=(-3, -14, 4), rot=(10, 30, 40))
    m.part("wtip_r", "wing_r", pivot=(-20, -2, 0), rot=(0, 0, -14))
    m.part("wing_l", "chest", pivot=(3, -14, 4), rot=(16, -36, -44))
    m.part("wtip_l", "wing_l", pivot=(15, -1, 0), rot=(0, 0, 30))
    m.part("arm_r", "chest", pivot=(-10, -16, 0), rot=(-6, 0, 22))
    m.part("fore_r", "arm_r", pivot=(0, 12, 0), rot=(-60, 0, 0))
    m.part("glaive", "fore_r", pivot=(0, 12, -1), rot=(64, 0, -20))
    m.part("arm_l", "chest", pivot=(10, -16, 0), rot=(-10, 0, -16))
    m.part("fore_l", "arm_l", pivot=(0, 12, 0), rot=(-34, 0, 6))
    m.part("orbit", "float", pivot=(0, -24, 0))

    # ---- the robe: three flaring tiers, the void creeping up from the hem, a gold hem band, ragged tatters
    m.box("float", -7, -26, -5, 14, 12, 10, robe(1, void_from=0.9))
    m.box("float", -8, -14, -6, 16, 8, 12, robe(2, void_from=0.35), glow=robe_glow(2, 0.35))
    m.box("float", -9, -6, -7, 18, 6, 14, robe(3, void_from=0.0), glow=robe_glow(3, 0.0))
    m.box("float", -9.5, -7, -7.5, 19, 1, 15, hem(4))
    m.box("float", -2, -24, -5.6, 4, 18, 1, gold(5, band_every=4))                     # front panel
    for k, (x, z, w, d, ln) in enumerate(((-8, -7, 4, 1, 6), (-3, -7.2, 5, 1, 4), (3, -7, 5, 1, 7),
                                          (-9, -3, 1, 5, 5), (8, -2, 1, 6, 6), (-6, 6, 5, 1, 7),
                                          (1, 6.2, 6, 1, 5))):
        m.box("hem", x, 0, z, w, ln, d, robe(10 + k, void_from=0.0), glow=robe_glow(10 + k, 0.0))

    # ---- torso: a white tunic under a gold breastplate, a sash of gold, a cracked marble collarbone
    m.box("waist", -6, -4, -4, 12, 5, 8, gold(12, band_every=2))                        # belt
    m.box("chest", -8, -18, -4.5, 16, 16, 9, robe(13, void_from=1.1))
    m.box("chest", -7, -17, -5.5, 14, 10, 2, gold(14, band_every=5))                     # breastplate
    m.box("chest", -2, -14, -6.2, 4, 4, 1, {"front": lambda f, x, y, w, h: LIGHT if 0 < x < w - 1 and 0 < y < h - 1 else GOLD_D,
                                             "*": GOLD}, glow={"front": lambda f, x, y, w, h: LIGHT if 0 < x < w - 1 and 0 < y < h - 1 else None})
    m.box("chest", -4, -20, -3.5, 8, 3, 7, marble(15), glow=marble_glow(15))             # neck and collarbone
    m.box("chest", -7, -9, 4.5, 14, 6, 1, gold(16, band_every=3))                        # back plate (wing roots)

    # ---- head: marble face, gold blindfold, hair falling down her back
    m.box("head", -4, -9, -4, 8, 9, 8, face_paint, glow=face_glow)
    m.box("head", -4.5, -10, -1, 9, 3, 6, {"*": lambda f, x, y, w, h: mul(HAIR, 1.0 if (x + y) % 3 else 0.86)})
    m.box("head", -3.5, -1, 3, 7, 12, 2, {"*": lambda f, x, y, w, h: mul(HAIR if y < 8 else HAIR_D, 1.0 if x % 2 else 0.88)})
    m.box("head", -4.6, -5.5, -4.6, 1, 2, 9, GOLD)                                        # the blindfold's ties
    m.box("head", 3.6, -5.5, -4.6, 1, 2, 9, GOLD)
    m.box("head", 2, -4, 4, 2, 7, 0, {"*": GOLD, "front": GOLD, "back": GOLD_D})          # its tails

    # ---- the broken halo: 14 segments in a ring of radius 14 round the head, two torn out at the upper right and
    # one drifting loose
    n_seg = 14
    for k in range(n_seg):
        if k in (2, 3):
            continue
        ang = k * 360.0 / n_seg
        drift = 3 if k == 4 else 0
        m.part(f"halo_{k}", "halo", pivot=(0, 0, 0), rot=(0, 0, ang + (6 if k == 4 else 0)))
        m.box(f"halo_{k}", -3, -15 - drift, -1, 6, 3, 2, halo_paint, glow=halo_glow)
        if k % 2 == 0:
            m.box(f"halo_{k}", -0.5, -18 - drift, -0.5, 1, 3, 1, GOLD_L, glow=LIGHT)    # rays
    # the broken stubs at the gap
    m.part("halo_stub", "halo", pivot=(0, 0, 0), rot=(0, 0, 2 * 360.0 / n_seg - 8))
    m.box("halo_stub", -1, -15, -1, 2, 3, 2, halo_paint, glow=halo_glow)

    # ---- the whole right wing: a gold-capped arm, coverts, long white primaries
    WL, WM, WD = WHITE_L, (226, 218, 200), (180, 156, 112)
    m.box("wing_r", -21, -2, -1, 21, 4, 3, gold(20, band_every=3))
    m.box("wing_r", -20, 2, -0.5, 20, 6, 2, feathers(WL, WM, WD, 21))                      # coverts
    for i, (x, ln) in enumerate(((-5, 16), (-9, 20), (-13, 24), (-17, 26))):
        m.box("wing_r", x, 5, 0, 3, ln, 1, feathers(WL, WM, WD, 22 + i))
    m.box("wtip_r", -14, -2, -0.5, 14, 3, 2, gold(26))
    for i, (x, ln) in enumerate(((-4, 26), (-8, 28), (-12, 27), (-15, 22))):
        m.box("wtip_r", x, 0, 0, 4, ln, 1, feathers(WL, WM, WD, 27 + i))

    # ---- the burnt left wing: shorter, void-dark and ragged, cracked with light
    VL, VM, VD = VOID_L, VOID, VOID_D
    m.box("wing_l", 0, -2, -1, 16, 4, 3, {"*": lambda f, x, y, w, h: mul(VOID_D if x % 5 else VOID, 1.1)},
          glow=lambda f, x, y, w, h: CRACK if f in ("front", "back") and x % 5 == 2 and y == 1 else None)
    m.box("wing_l", 1, 2, -0.5, 14, 5, 2, feathers(VL, VM, VD, 41, ragged=0.25), glow=void_feather_glow(41))
    for i, (x, ln) in enumerate(((3, 12), (7, 16), (11, 13))):
        m.box("wing_l", x, 5, 0, 3, ln, 1, feathers(VL, VM, VD, 42 + i, ragged=0.3), glow=void_feather_glow(42 + i))
    m.box("wtip_l", 0, -1.5, -0.5, 9, 3, 2, {"*": VOID_D})
    for i, (x, ln) in enumerate(((1, 18), (5, 14))):
        m.box("wtip_l", x, 0, 0, 3, ln, 1, feathers(VL, VM, VD, 46 + i, ragged=0.35), glow=void_feather_glow(46 + i))
    m.box("wtip_l", 8, -1, 0, 2, 7, 1, {"*": VOID_D}, glow={"front": CRACK, "back": CRACK})    # a bare, broken bone

    # ---- right arm: a gold pauldron with a feather crest, marble arm, gold vambrace, the glaive
    m.box("arm_r", -6, -4, -4.5, 9, 5, 9, gold(50, band_every=2))
    m.box("arm_r", -7, -6, -2, 3, 3, 4, WHITE_L)
    m.box("arm_r", -2.5, 0, -2.5, 5, 12, 5, robe(51, void_from=1.1))                       # sleeve
    m.box("fore_r", -2.5, 0, -2.5, 5, 11, 5, marble(52), glow=marble_glow(52, 0.06))
    m.box("fore_r", -3, 2, -3, 6, 6, 6, gold(53, band_every=2))
    m.box("fore_r", -2.5, 11, -2.5, 5, 3, 5, marble(54))                                     # hand
    # the glaive: a long white-gold haft, a gold collar, a crescent of halo for a blade
    m.box("glaive", -1, -38, -1, 2, 54, 2, {"*": lambda f, x, y, w, h: GOLD if y % 9 == 0 else (WHITE if x % 2 else WHITE_D)})
    m.box("glaive", -1.5, 14, -1.5, 3, 3, 3, gold(55))                                       # butt cap
    m.box("glaive", -2, -41, -2, 4, 4, 4, gold(56), glow={"front": lambda f, x, y, w, h: LIGHT if x in (1, 2) and y in (1, 2) else None})
    for k, a in enumerate(range(-150, 31, 20)):
        m.part(f"blade_{k}", "glaive", pivot=(0, -48, 0), rot=(0, 0, a))
        m.box(f"blade_{k}", -1.5, -9, -0.5, 3, 3, 1, halo_paint, glow=halo_glow)
        if k not in (0, 9):
            m.box(f"blade_{k}", -1, -6, -0.4, 2, 1, 1, LIGHT, glow=LIGHT)                    # the inner edge of light
    m.box("glaive", -0.5, -58, -0.5, 1, 8, 1, GOLD_L, glow=LIGHT)                            # a spike through the crescent

    # ---- left arm: bare marble cracked with light, an open hand that casts
    m.box("arm_l", -3, -3, -3.5, 6, 4, 7, gold(60))
    m.box("arm_l", -2.5, 0, -2.5, 5, 12, 5, marble(61), glow=marble_glow(61, 0.2))
    m.box("fore_l", -2.5, 0, -2.5, 5, 11, 5, marble(62), glow=marble_glow(62, 0.25))
    m.box("fore_l", -3, 6, -3, 6, 2, 6, gold(63))
    m.box("fore_l", -2.5, 11, -2.5, 5, 3, 5, marble(64), glow=marble_glow(64, 0.3))

    # ---- six halo shards orbiting at her waist (her projectiles)
    for k in range(6):
        a = k * math.pi / 3
        m.part(f"shard_{k}", "orbit", pivot=(round(20 * math.cos(a)), 0, round(20 * math.sin(a))),
               rot=(0, -math.degrees(a), 22))
        m.box(f"shard_{k}", -1, -4, -1, 2, 7, 2, shard_paint, glow=shard_glow)
        m.box(f"shard_{k}", -0.5, -6, -0.5, 1, 2, 1, LIGHT, glow=LIGHT)
        m.box(f"shard_{k}", -0.5, 3, -0.5, 1, 2, 1, GOLD_L, glow=GOLD_L)

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))

    idle = m.anim("idle", 6.0)
    idle.pos("float", (0, (0, 0, 0)), (1.5, (0, 1.6, 0)), (3.0, (0, 0, 0)), (4.5, (0, 1.6, 0)), (6.0, (0, 0, 0)))
    idle.rot("orbit", (0, (0, 0, 0), "linear"), (6.0, (0, 360, 0), "linear"))
    for k in range(6):
        s = 1 if k % 2 else -1
        idle.pos(f"shard_{k}", (0, (0, 0, 0)), (1.5, (0, 1.4 * s, 0)), (3.0, (0, 0, 0)), (4.5, (0, -1.4 * s, 0)),
                 (6.0, (0, 0, 0)))
    idle.rot("wing_r", (0, (0, 0, 0)), (1.5, (0, -6, 4)), (3.0, (0, 0, 0)), (4.5, (0, -6, 4)), (6.0, (0, 0, 0)))
    idle.rot("wing_l", (0, (0, 0, 0)), (1.5, (0, 5, -3)), (3.0, (0, 0, 0)), (4.5, (0, 5, -3)), (6.0, (0, 0, 0)))
    idle.rot("halo", (0, (0, 0, 0)), (3.0, (0, 0, 8)), (6.0, (0, 0, 0)))
    idle.rot("hem", (0, (0, 0, 0)), (1.5, (5, 0, 2)), (3.0, (0, 0, 0)), (4.5, (-4, 0, -2)), (6.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (2.0, (0, 6, 0)), (3.0, (0, 6, 0)), (4.5, (0, -5, 0)), (6.0, (0, 0, 0)))

    # walk: she glides, leaning into the motion, the hem trailing and the wings drawn back
    walk = m.anim("walk", 2.0)
    walk.rot("float", (0, (8, 0, 0)), (1.0, (10, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("hem", (0, (-22, 0, 0)), (1.0, (-30, 0, 0)), (2.0, (-22, 0, 0)))
    walk.rot("wing_r", (0, (0, -8, 0)), (1.0, (0, -14, 6)), (2.0, (0, -8, 0)))
    walk.rot("wing_l", (0, (0, 8, 0)), (1.0, (0, 14, -6)), (2.0, (0, 8, 0)))
    walk.pos("float", (0, (0, 0, 0)), (1.0, (0, 1.0, 0)), (2.0, (0, 0, 0)))

    # glaive: the glaive drawn back over her right shoulder, body coiled (0.8 s = 16 ticks), then one wide sweep
    # from her right to her left
    a = m.anim("glaive", 1.7)
    # the haft is turned along the forearm (glaive +116 / +20 cancels its rest grip) so the blade leads the swing
    a.rot("arm_r", (0, (0, 0, 0)), (0.7, (-104, -96, -22)), (0.8, (-106, -100, -22)), (0.9, (-74, 70, -22), "linear"),
          (1.15, (-70, 74, -22)), (1.7, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.5, (60, 0, 0)), (1.15, (60, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("glaive", (0, (0, 0, 0)), (0.5, (116, 0, 20)), (1.15, (116, 0, 20)), (1.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-8, -38, 0)), (0.9, (10, 40, 0), "linear"), (1.15, (10, 42, 0)), (1.7, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.8, (0, -14, 0)), (0.9, (0, 16, 0), "linear"), (1.15, (0, 16, 0)), (1.7, (0, 0, 0)))
    a.rot("wing_r", (0, (0, 0, 0)), (0.8, (0, -20, 10)), (0.9, (0, 20, -10), "linear"), (1.7, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.8, (0, 0, -10)), (0.9, (0, 0, 14), "linear"), (1.7, (0, 0, 0)))

    # thrust: glaive levelled and drawn back, the body low (0.7 s = 14 ticks), then a lunge with the point forward
    a = m.anim("thrust", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-40, 24, -12)), (0.7, (-42, 26, -12)), (0.78, (-84, 0, -22), "linear"),
          (1.1, (-84, 0, -22)), (1.8, (0, 0, 0)))
    a.rot("fore_r", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (0.7, (10, 0, 0)), (0.78, (60, 0, 0), "linear"), (1.1, (60, 0, 0)),
          (1.8, (0, 0, 0)))
    a.rot("glaive", (0, (0, 0, 0)), (0.5, (116, 0, 20)), (1.1, (116, 0, 20)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (-6, -30, 0)), (0.78, (4, 12, 0), "linear"), (1.1, (4, 12, 0)), (1.8, (0, 0, 0)))
    a.rot("float", (0, (0, 0, 0)), (0.7, (-6, 0, 0)), (0.78, (8, 0, 0), "linear"), (1.1, (8, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (0.7, (0, -3, 3)), (0.78, (0, 0, -6), "linear"), (1.1, (0, 0, -6)), (1.8, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.7, (0, 18 * sx, -10 * sx)), (0.78, (0, -30 * sx, 14 * sx), "linear"),
              (1.1, (0, -30 * sx, 14 * sx)), (1.8, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.78, (-40, 0, 0), "linear"), (1.1, (-36, 0, 0)), (1.8, (0, 0, 0)))

    # shards: the left hand raised, the orbit spins up and lifts to her shoulders (0.9 s = 18 ticks), then the six
    # shards are flung one after the other (every 0.2 s), the hand pointing at the foe
    a = m.anim("shards", 2.7)
    a.rot("arm_l", (0, (0, 0, 0)), (0.8, (-150, 0, -30)), (0.9, (-154, 0, -32)), (0.98, (-90, -10, 4), "linear"),
          (2.1, (-88, -10, 4)), (2.7, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (0.98, (10, 0, 0), "linear"), (2.1, (10, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("orbit", (0, (0, 0, 0)), (0.9, (0, 300, 0)), (2.1, (0, 900, 0)), (2.7, (0, 1080, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.9, (0, 12, 0)), (2.1, (0, 12, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (-10, 16, 0)), (0.98, (6, -12, 0), "linear"), (2.1, (6, -12, 0)), (2.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-12, 0, 0)), (2.1, (-4, 0, 0)), (2.7, (0, 0, 0)))
    for k in range(6):
        t = 0.9 + k * 0.2
        a.scale(f"shard_{k}", (0, (1, 1, 1)), (max(0.05, t - 0.1), (1.4, 1.4, 1.4)), (t, (0.2, 0.2, 0.2), "linear"),
                (min(2.6, t + 0.6), (1, 1, 1)), (2.7, (1, 1, 1)))

    # pillars: both hands raised to the sky, wings spread wide (1.0 s = 20 ticks), then flung down: lances of light
    # fall where the rings were drawn
    a = m.anim("pillars", 2.7)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.9, (-170, 0, -24 * sx)), (1.0, (-172, 0, -26 * sx)),
              (1.08, (-40, 0, -40 * sx), "linear"), (2.1, (-40, 0, -40 * sx)), (2.7, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.0, (-10, 36 * sx, -30 * sx)), (1.08, (6, -10 * sx, 10 * sx), "linear"),
              (2.1, (6, -10 * sx, 10 * sx)), (2.7, (0, 0, 0)))
    a.rot("glaive", (0, (0, 0, 0)), (1.0, (-40, 0, 0)), (1.08, (20, 0, 0), "linear"), (2.1, (20, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-18, 0, 0)), (1.08, (16, 0, 0), "linear"), (2.1, (14, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-30, 0, 0)), (1.08, (8, 0, 0), "linear"), (2.7, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (1.0, (0, 5, 0)), (1.08, (0, -2, 0), "linear"), (2.1, (0, -2, 0)), (2.7, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (1.0, (1.3, 1.3, 1.3)), (1.08, (1.0, 1.0, 1.0), "linear"), (2.7, (1, 1, 1)))

    # blink: the wings fold round her like a cocoon (0.6 s = 12 ticks), she vanishes and bursts open at the arena's edge
    a = m.anim("blink", 1.0)
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.55, (0, 70 * sx, 10 * sx)), (0.6, (0, 74 * sx, 10 * sx)),
              (0.68, (-10, -30 * sx, -30 * sx), "linear"), (1.0, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-30, 0, 20 * sx)), (0.68, (-20, 0, -40 * sx), "linear"), (1.0, (0, 0, 0)))
    a.scale("float", (0, (1, 1, 1)), (0.55, (0.9, 1.05, 0.9)), (0.6, (0.6, 1.2, 0.6), "linear"),
            (0.66, (1.1, 0.95, 1.1), "linear"), (1.0, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (20, 0, 0)), (0.68, (-16, 0, 0), "linear"), (1.0, (0, 0, 0)))

    # beam (phase 2): she rises, head thrown back, the halo blazing (1.2 s = 24 ticks); a blinding beam pours from the
    # halo and sweeps from her left to her right for 2 s while her body turns with it
    a = m.anim("beam", 4.0)
    a.pos("float", (0, (0, 0, 0)), (1.2, (0, 10, 0)), (3.2, (0, 10, 0)), (4.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (-14, 58, 0)), (1.2, (-14, 60, 0)), (3.2, (-14, -60, 0), "linear"), (4.0, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (1.2, (0, 16, 0)), (3.2, (0, -16, 0), "linear"), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-26, 0, 0)), (3.2, (-26, 0, 0)), (4.0, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (1.2, (1.4, 1.4, 1.4)), (3.2, (1.4, 1.4, 1.4)), (4.0, (1, 1, 1)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.2, (-40, 0, -70 * sx)), (3.2, (-40, 0, -70 * sx)), (4.0, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.2, (-14, 40 * sx, -36 * sx)), (3.2, (-14, 40 * sx, -36 * sx)), (4.0, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (1.2, (10, 0, 0)), (3.2, (-10, 0, 0)), (4.0, (0, 0, 0)))

    # nova (phase 2): the halo raised over her head in both hands (1.0 s = 20 ticks), then thrust out: a ring of light
    # rolls out across the disc, and 0.8 s later a second ring rolls back in from the edge
    a = m.anim("nova", 3.5)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.9, (-168, 0, 18 * sx)), (1.0, (-170, 0, 20 * sx)),
              (1.08, (-90, 0, -80 * sx), "linear"), (2.0, (-90, 0, -80 * sx)), (2.2, (-170, 0, 20 * sx)),
              (2.8, (-168, 0, 18 * sx)), (3.5, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.0, (0, 20 * sx, -10 * sx)), (1.08, (-16, 50 * sx, -40 * sx), "linear"),
              (2.8, (-16, 50 * sx, -40 * sx)), (3.5, (0, 0, 0)))
    a.pos("halo", (0, (0, 0, 0)), (1.0, (0, 10, -6)), (1.08, (0, 6, -4), "linear"), (2.8, (0, 6, -4)), (3.5, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (1.0, (0.9, 0.9, 0.9)), (1.08, (1.8, 1.8, 1.8), "linear"), (1.8, (1.2, 1.2, 1.2)),
            (1.9, (1.8, 1.8, 1.8), "linear"), (2.8, (1.0, 1.0, 1.0)), (3.5, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-24, 0, 0)), (1.08, (0, 0, 0), "linear"), (3.5, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (1.0, (0, 4, 0)), (1.08, (0, -1, 0), "linear"), (2.8, (0, -1, 0)), (3.5, (0, 0, 0)))

    # rain (phase 3): she tears the shards from her orbit and hurls them at the sky (1.1 s = 22 ticks); for 2.2 s they
    # fall back on the disc, wave after wave
    a = m.anim("rain", 4.0)
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-40, 0, -20)), (1.1, (-60, 0, -30)), (1.2, (-178, 0, -10), "linear"),
          (3.3, (-176, 0, -12)), (4.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (1.1, (-30, 0, 30)), (1.2, (-100, 0, 40), "linear"), (3.3, (-100, 0, 40)), (4.0, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (1.1, (0, 4, 0)), (1.25, (0, 80, 0), "linear"), (3.3, (0, 80, 0)), (3.6, (0, 0, 0)),
          (4.0, (0, 0, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (1.1, (1, 1, 1)), (1.25, (2.0, 1, 2.0), "linear"), (3.3, (2.0, 1, 2.0)),
            (3.6, (1, 1, 1)), (4.0, (1, 1, 1)))
    a.rot("orbit", (0, (0, 0, 0)), (1.1, (0, 240, 0)), (3.3, (0, 1000, 0)), (4.0, (0, 1080, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.1, (8, -20, 0)), (1.2, (-20, 10, 0), "linear"), (3.3, (-18, 10, 0)), (4.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.1, (6, 0, 0)), (1.2, (-36, 0, 0), "linear"), (3.3, (-34, 0, 0)), (4.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.1, (0, -10 * sx, 6 * sx)), (1.2, (-10, 40 * sx, -30 * sx), "linear"),
              (3.3, (-10, 40 * sx, -30 * sx)), (4.0, (0, 0, 0)))

    # dive (phase 3): she crouches and beats her wings (0.4 s), soars high over the disc (by 0.8 s she is above the
    # gold ring that follows you), hangs there, and falls glaive-first at 1.5 s (30 ticks)
    a = m.anim("dive", 2.6)
    a.pos("float", (0, (0, 0, 0)), (0.35, (0, -4, 0)), (0.8, (0, 76, 0)), (1.4, (0, 80, 0)), (1.5, (0, -2, 0), "linear"),
          (2.1, (0, -2, 0)), (2.6, (0, 0, 0)))
    a.rot("float", (0, (0, 0, 0)), (0.35, (10, 0, 0)), (0.8, (-10, 0, 0)), (1.4, (-30, 0, 0)), (1.5, (30, 0, 0), "linear"),
          (2.1, (24, 0, 0)), (2.6, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.35, (-20, 50 * sx, -40 * sx)), (0.55, (20, -30 * sx, 40 * sx)),
              (0.8, (-20, 50 * sx, -40 * sx)), (1.4, (-20, 50 * sx, -40 * sx)), (1.5, (10, -50 * sx, 20 * sx), "linear"),
              (2.1, (10, -40 * sx, 20 * sx)), (2.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-150, 0, 10)), (1.4, (-160, 0, 10)), (1.5, (-40, 0, 0), "linear"),
          (2.1, (-40, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("glaive", (0, (0, 0, 0)), (1.4, (-10, 0, 0)), (1.5, (-60, 0, 0), "linear"), (2.1, (-60, 0, 0)), (2.6, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (1.4, (30, 0, 0)), (1.5, (-30, 0, 0), "linear"), (2.6, (0, 0, 0)))

    # shatter (phase 3 transition, invulnerable): she rises and curls up, the halo cracks wider (2.0 s = 40 ticks),
    # then she slams both fists down and the disc splits
    a = m.anim("shatter", 3.0)
    a.pos("float", (0, (0, 0, 0)), (1.9, (0, 14, 0)), (2.0, (0, 14, 0)), (2.08, (0, -3, 0), "linear"), (2.6, (0, -3, 0)),
          (3.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.9, (30, 0, 0)), (2.0, (32, 0, 0)), (2.08, (24, 0, 0), "linear"), (3.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.8, (26, 0, -10)), (1.9, (30, 0, 10)), (2.08, (-30, 0, 0), "linear"), (3.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.9, (-40, 0, 30 * sx)), (2.0, (-170, 0, -10 * sx)),
              (2.08, (-10, 0, -20 * sx), "linear"), (2.6, (-10, 0, -20 * sx)), (3.0, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.9, (0, 70 * sx, 10 * sx)), (2.08, (-20, 50 * sx, -50 * sx), "linear"),
              (2.6, (-20, 50 * sx, -50 * sx)), (3.0, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (1.0, (1.1, 1.1, 1.1)), (1.9, (0.8, 0.8, 0.8)), (2.08, (1.6, 1.6, 1.6), "linear"),
            (3.0, (1, 1, 1)))
    a.rot("halo", (0, (0, 0, 0)), (1.9, (0, 0, -40)), (2.08, (0, 0, 30), "linear"), (3.0, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (1.9, (0, 20, 0)), (2.08, (0, -8, 0), "linear"), (3.0, (0, 0, 0)))
    a.scale("orbit", (0, (1, 1, 1)), (1.9, (0.4, 1, 0.4)), (2.08, (1.8, 1, 1.8), "linear"), (3.0, (1, 1, 1)))

    # roar (phase 2): she throws her arms and wings wide, the halo flares and the void climbs her robe
    a = m.anim("roar", 2.4)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-120, 0, -60 * sx)), (2.0, (-124, 0, -64 * sx)), (2.4, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.6, (-20, 46 * sx, -46 * sx)), (2.0, (-22, 48 * sx, -48 * sx)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-34, 0, 0)), (2.0, (-30, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-14, 0, 0)), (2.0, (-12, 0, 0)), (2.4, (0, 0, 0)))
    a.pos("float", (0, (0, 0, 0)), (0.6, (0, 8, 0)), (2.0, (0, 9, 0)), (2.4, (0, 0, 0)))
    a.scale("halo", (0, (1, 1, 1)), (0.6, (1.5, 1.5, 1.5)), (2.0, (1.5, 1.5, 1.5)), (2.4, (1, 1, 1)))
    a.scale("orbit", (0, (1, 1, 1)), (0.6, (1.6, 1, 1.6)), (2.0, (1.6, 1, 1.6)), (2.4, (1, 1, 1)))

    # stagger: her light gutters, she sinks to the floor and slumps on the glaive, the shards dropping
    a = m.anim("stagger", 2.4)
    a.pos("float", (0, (0, 0, 0)), (0.3, (0, -9, 0)), (2.0, (0, -9, 0)), (2.4, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, -8)), (2.0, (32, 0, -8)), (2.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, 10)), (2.0, (28, 0, 10)), (2.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-20, 0, -20)), (2.0, (-20, 0, -20)), (2.4, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.3, (30, -20 * sx, 30 * sx)), (2.0, (32, -20 * sx, 32 * sx)), (2.4, (0, 0, 0)))
    a.pos("orbit", (0, (0, 0, 0)), (0.3, (0, -12, 0)), (2.0, (0, -12, 0)), (2.4, (0, 0, 0)))
    a.rot("halo", (0, (0, 0, 0)), (0.3, (20, 0, -24)), (2.0, (20, 0, -24)), (2.4, (0, 0, 0)))
    a.rot("hem", (0, (0, 0, 0)), (0.3, (-20, 0, 0)), (2.0, (-20, 0, 0)), (2.4, (0, 0, 0)))
