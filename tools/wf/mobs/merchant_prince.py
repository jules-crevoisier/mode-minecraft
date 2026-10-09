"""The Brass Merchant Prince (Le Prince marchand de laiton): the champion of the Brass Caravanserai, about 3.6 blocks.

Silhouette idea: a decadent merchant prince carried on his own clockwork palanquin. The palanquin is a brass-bound
mahogany coffer heaped with gold, a crimson cushion on top, gilded finials at its corners, scuttling on four splayed
brass spider legs. The prince sits cross-legged on the cushion: a plump figure in azure silks plated with brass scales,
a crimson sash, a jewelled collar; a dark oiled beard trimmed to a point; a towering cream turban wound with gold
bands, a great ruby set in front and a white plume rising from it. In his right hand a broad curved scimitar with a
gold back; on his left hand jewelled rings. Behind him a great brass mechanical arm rises from the coffer on a mast and
reaches over his left shoulder, its three-fingered claw clutching a gold bar: the arm that throws his money for him.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

SILK = (44, 88, 176)            # azure silk
SILK_L = (92, 140, 220)
SILK_D = (24, 50, 112)
SASH = (176, 30, 44)
SASH_L = (222, 72, 76)
SASH_D = (110, 16, 28)
CREAM = (238, 228, 204)
CREAM_D = (200, 186, 156)
GOLD = (232, 186, 70)
GOLD_L = (255, 230, 130)
GOLD_D = (160, 116, 34)
SKIN = (196, 140, 96)
SKIN_L = (222, 170, 122)
SKIN_D = (150, 100, 66)
BEARD = (34, 24, 22)
BEARD_L = (66, 50, 44)
RUBY = (210, 30, 52)
RUBY_L = (255, 120, 130)
SAPPH = (40, 90, 220)
SAPPH_L = (130, 180, 255)
EMER = (40, 180, 100)
WOOD = (110, 58, 38)
WOOD_D = (70, 36, 24)
STEEL = (206, 210, 220)
STEEL_L = (246, 248, 252)
STEEL_D = (140, 144, 156)
PLUME = (246, 244, 240)


# ---------------------------------------------------------------- paint
def silk(seed=0, scales=False):
    """Azure silk with a sheen; with ``scales``, rows of small brass scales plated over it."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SILK_D
        if scales and face != "top" and (y % 3 == 0) and ((x + (y // 3)) % 2 == 0):
            return B.BRASS_L if y % 6 == 0 else B.BRASS
        if scales and face != "top" and (y % 3 == 1) and ((x + (y // 3)) % 2 == 0):
            return B.BRASS_D
        r = B.n(x, y, seed)
        c = SILK_L if (x + y) % 5 == 0 and r > 0.5 else (SILK if r > 0.18 else SILK_D)
        if x in (0, w - 1) and face != "top":
            c = mix(c, SILK_D, 0.4)
        return c
    return f


def sash(face, x, y, w, h):
    if y == 0 or y == h - 1:
        return GOLD if x % 2 else GOLD_D
    return SASH_L if (x + 2 * y) % 5 == 0 else (SASH if B.n(x, y, 3) > 0.2 else SASH_D)


def collar(face, x, y, w, h):
    """The jewelled collar: gold links with a stone every third."""
    if face in ("top", "bottom"):
        return GOLD_D
    if x % 3 == 1 and y == h // 2:
        return (RUBY, SAPPH, EMER)[(x // 3) % 3]
    return GOLD_L if (x + y) % 2 == 0 else GOLD


def skin(face, x, y, w, h):
    r = B.n(x, y, 41)
    return SKIN_L if r > 0.85 else (SKIN if r > 0.15 else SKIN_D)


def head(face_, x, y, w, h):
    """The face (8 x 8): heavy black brows, kohl-dark eyes with a gold glint, a hooked nose, a curled moustache
    over a smug mouth; the beard is its own cube. Brass earrings on the sides."""
    if face_ == "top":
        return BEARD
    if face_ == "front":
        if y == 2 and x in (1, 2, 5, 6):
            return BEARD                                                            # the brows
        if y == 3 and x in (2, 5):
            return (30, 22, 20)                                                     # the eyes
        if y == 3 and x in (1, 6):
            return (250, 238, 220)
        if y in (3, 4) and x in (3, 4):
            return SKIN_L if y == 3 else SKIN_D                                     # the nose
        if y == 5 and x in (1, 2, 5, 6):
            return BEARD_L if x in (1, 6) else BEARD                                # the moustache
        if y == 5 and x in (3, 4):
            return SKIN_D
        if y == 6 and 2 <= x <= 5:
            return (120, 40, 40) if x in (3, 4) else BEARD                          # the mouth
        if y == 7:
            return BEARD
    if face_ in ("left", "right"):
        if y in (4, 5) and x == 4:
            return GOLD_L                                                           # an earring
        if y <= 1 or x >= 6:
            return BEARD                                                            # hair under the turban
        if y >= 6 and x <= 3:
            return BEARD
    if face_ == "back":
        return BEARD if y < 6 else SKIN_D
    return skin(face_, x, y, w, h)


def head_glow(face_, x, y, w, h):
    if face_ == "front" and y == 3 and x in (1, 6):
        return (255, 220, 120)
    return None


def beard(face, x, y, w, h):
    """An oiled beard trimmed to a point, gold beads threaded in."""
    if face == "front" and y == h - 2 and x == w // 2:
        return GOLD_L
    return BEARD_L if (x + y) % 3 == 0 else BEARD


def turban(seed=0):
    """Wound cream cloth: diagonal folds, a gold band every fourth row."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return CREAM_D
        if face != "top" and y % 4 == 3:
            return GOLD_L if x % 2 == 0 else GOLD
        if face == "top":
            return CREAM if (x + y) % 3 else CREAM_D
        fold = (x + y + seed) % 4 == 0
        return CREAM_D if fold else (CREAM if B.n(x, y, seed) > 0.12 else CREAM_D)
    return f


def jewel(face, x, y, w, h):
    if face == "front" and (x, y) == (0, 0):
        return RUBY_L
    return RUBY


def jewel_glow(face, x, y, w, h):
    return (255, 90, 110) if face == "front" else None


def setting(face, x, y, w, h):
    return GOLD_L if (x + y) % 2 == 0 else GOLD_D


def plume(face, x, y, w, h):
    return PLUME if (x + y) % 3 else (214, 210, 204)


def ring_hand(face, x, y, w, h):
    """A hand with jewelled rings across the knuckles."""
    if y == 1 and face in ("front", "left", "right"):
        return (RUBY, GOLD_L, SAPPH)[x % 3]
    return skin(face, x, y, w, h)


def cuff(face, x, y, w, h):
    return GOLD_L if y == 0 else (GOLD if x % 2 else GOLD_D)


def coffer(face, x, y, w, h):
    """The palanquin's coffer: mahogany panels framed in brass, brass corners and studs."""
    if face == "top":
        return GOLD if (x * 3 + y * 5) % 7 < 3 else (GOLD_L if (x + y) % 4 == 0 else GOLD_D)   # heaped coins
    if face == "bottom":
        return WOOD_D
    if y in (0, h - 1) or x in (0, w - 1) or (w > 12 and x == w // 2):
        return B.BRASS_L if y == 0 else B.BRASS
    if y in (1, h - 2) and x % 3 == 1:
        return B.BRASS_L                                                             # studs
    return WOOD if (x + B.n(x, y, 9) * 3) % 5 > 1 else WOOD_D


def cushion(face, x, y, w, h):
    if face == "top":
        return SASH_L if (x + y) % 4 == 0 else SASH
    if y == h - 1:
        return GOLD if x % 2 else GOLD_D                                             # tassel fringe
    return SASH_D if (x % 4 == 0) else SASH


def finial(face, x, y, w, h):
    return GOLD_L if face == "top" or y == 0 else (GOLD if (x + y) % 2 else GOLD_D)


def leg(seed=0):
    return B.brass(seed, grad=0.3)


def foot(face, x, y, w, h):
    if face == "bottom":
        return B.IRON_D
    return B.IRON_L if y == 0 else B.IRON


def blade(face, x, y, w, h):
    """The scimitar's steel: a bright edge, a soft fuller."""
    if face in ("left", "right"):
        return STEEL_L if x == 0 else STEEL
    if face in ("top", "bottom"):
        return STEEL_D
    return STEEL_L if x == 0 else (STEEL if x < w - 1 else STEEL_D)


def grip(face, x, y, w, h):
    return GOLD if y % 2 == 0 else SASH_D


def claw(face, x, y, w, h):
    return B.BRASS_L if y == 0 else (B.BRASS if (x + y) % 2 else B.BRASS_D)


def bar(face, x, y, w, h):
    """A gold bar: stamped top, bright edges."""
    if face == "top":
        return GOLD_D if 1 <= x <= w - 2 and y == h // 2 else GOLD_L
    return GOLD_L if y == 0 else (GOLD if x % 3 else GOLD_D)


# ---------------------------------------------------------------- build
def build():
    m = Model("merchant_prince", seed=1361, shadow=1.1, walk_speed=1.0, walk_scale=0.8, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("car", "bone", pivot=(0, -12, 0))
    for side, sx in (("r", -1), ("l", 1)):
        for end, sz in (("f", -1), ("b", 1)):
            m.part(f"thigh_{end}{side}", "car", pivot=(9 * sx, -6, 7 * sz), rot=(0, 0, -14 * sx))
            m.part(f"shin_{end}{side}", f"thigh_{end}{side}", pivot=(7 * sx, 0, 0), rot=(0, 0, 14 * sx))
    m.part("hips", "car", pivot=(0, -12, 0))
    m.part("chest", "hips", pivot=(0, -5, 0))
    m.part("head", "chest", pivot=(0, -13, 0))
    m.part("arm_r", "chest", pivot=(-7, -11, 0), rot=(-20, 0, 8))
    m.part("fore_r", "arm_r", pivot=(0, 8, 0), rot=(-40, 0, 0))
    m.part("sword", "fore_r", pivot=(0, 8.5, -0.5), rot=(60, 0, 0))
    m.part("arm_l", "chest", pivot=(7, -11, 0), rot=(-10, 0, -10))
    m.part("fore_l", "arm_l", pivot=(0, 8, 0), rot=(-50, 0, 0))
    m.part("mast", "car", pivot=(7, -10, 6))
    m.part("mech_up", "mast", pivot=(0, -14, 0), rot=(18, 0, 0))
    m.part("mech_fore", "mech_up", pivot=(0, -12, 0), rot=(80, 0, 0))
    m.part("claw", "mech_fore", pivot=(0, -10, 0))

    # ---- the palanquin: the coffer heaped with gold, finials, the cushion
    m.box("car", -10, -10, -9, 20, 10, 18, coffer)
    m.box("car", -10.5, -1, -9.5, 21, 1, 19, B.brass(5))                                # the brass skirt
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box("car", 9 * sx - 1.5, -14, 8 * sz - 1.5, 3, 4, 3, finial)              # gilded finials
            m.box("car", 9 * sx - 0.5, -15, 8 * sz - 0.5, 1, 1, 1, RUBY)
    m.box("car", -7, -12, -6, 14, 2, 12, cushion)
    m.box("car", -1.5, -6, -9.6, 3, 3, 1, B.lens())                                     # a lock plate

    # ---- four splayed brass legs
    for side, sx in (("r", -1), ("l", 1)):
        for end, sz in (("f", -1), ("b", 1)):
            th, sh = f"thigh_{end}{side}", f"shin_{end}{side}"
            x0 = 0 if sx > 0 else -8
            m.box(th, x0, -1.5, -1.5, 8, 3, 3, leg(20 + sx + sz))
            m.box(th, -1.5, -2, -2, 3, 4, 4, B.cog(teeth=6, faces=("front", "back")))   # the hip joint
            m.box(sh, -1.5, -1.5, -1.5, 3, 3, 3, B.brass(30 + sx))                      # the knee
            m.box(sh, -1, 1, -1, 2, 15, 2, B.rod(B.BRASS, 31 + sz))
            m.box(sh, -1.5, 16, -2, 3, 2, 4, foot)

    # ---- the prince seated cross-legged: hips and lap, the chest plated in brass scales, the sash and collar
    m.box("hips", -5, -5, -3.5, 10, 5, 7, silk(50))
    m.box("hips", -6.5, -3, -7.5, 13, 3, 5, silk(51))                                   # the crossed legs
    m.box("hips", -7, -2, -8, 3, 2, 2, GOLD_D)                                          # slipper toes
    m.box("hips", 4, -2, -8, 3, 2, 2, GOLD_D)
    m.box("chest", -5.5, -13, -3.5, 11, 13, 7, silk(52, scales=True))
    m.box("chest", -6, -3, -4, 12, 3, 8, sash)                                          # the sash round a full belly
    m.box("chest", -5, -6, -4.6, 10, 3, 1, silk(53, scales=True))                       # the belly
    m.box("chest", -4.5, -14, -4, 9, 2, 8, collar)
    m.box("chest", -8, -13, -3, 4, 3, 6, B.brass(54))                                   # brass pauldrons
    m.box("chest", 4, -13, -3, 4, 3, 6, B.brass(55))

    # ---- the head: the bearded face, the towering jewelled turban and its plume
    m.box("head", -4, -8, -4, 8, 8, 8, head, glow=head_glow)
    m.box("head", -2, -1, -4.6, 4, 3, 2, beard)
    m.box("head", -1, 2, -4.4, 2, 2, 1, beard)                                          # its point
    m.box("head", -5, -12, -5, 10, 5, 10, turban(1))
    m.box("head", -4, -15, -4, 8, 3, 8, turban(2))
    m.box("head", -2.5, -16, -2.5, 5, 1, 5, turban(3))
    m.box("head", -1.5, -12, -5.6, 3, 3, 1, setting)                                    # the jewel's setting
    m.box("head", -1, -11.5, -6.0, 2, 2, 1, jewel, glow=jewel_glow)
    m.box("head", -0.5, -21, -4.5, 1, 9, 1, plume)                                      # the plume
    m.box("head", -0.5, -22, -3.5, 1, 2, 1, plume)

    # ---- arms: silk sleeves, gold cuffs; the scimitar in the right hand, rings on the left
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 9, 3, silk(60 + sx))
        m.box(fore, -1.5, 0, -1.5, 3, 7, 3, silk(62 + sx))
        m.box(fore, -2, 5, -2, 4, 2, 4, cuff)
        m.box(fore, -1.5, 7, -1.5, 3, 3, 3, ring_hand if side == "l" else skin)
    m.box("sword", -0.5, -2, -0.5, 1, 4, 1, grip)
    m.box("sword", -0.5, -3, -0.5, 1, 1, 1, SAPPH)                                      # the pommel
    m.box("sword", -0.5, 2, -2.5, 1, 1, 5, setting)                                     # the crossguard
    for i, (z, y0, hh, ww) in enumerate(((-1.5, 3, 4, 2), (-1.0, 7, 4, 3), (-0.2, 11, 3, 3), (0.8, 14, 3, 3))):
        m.box("sword", -0.5, y0, z, 1, hh, ww, blade)                                   # the blade, curving back
        m.box("sword", -0.5, y0, z + ww, 1, hh, 1, GOLD)                                # the gold back
    m.box("sword", -0.5, 17, 2.4, 1, 2, 2, blade)                                       # the point
    m.box("sword", -0.5, 19, 3.4, 1, 1, 1, STEEL_L)

    # ---- the brass mechanical arm on its mast behind him, a gold bar in its claw
    m.box("mast", -2, -2, -2, 4, 2, 4, B.brass(70))
    m.box("mast", -1.5, -14, -1.5, 3, 12, 3, B.rod(B.BRASS, 71))
    m.box("mech_up", -2, -2, -2, 4, 4, 4, B.cog(teeth=6, faces=("left", "right")))     # the shoulder
    m.box("mech_up", -1.5, -12, -1.5, 3, 10, 3, B.brass(72))
    m.box("mech_up", -0.5, -11, 1.5, 1, 9, 1, B.rod(B.IRON, 73))                        # a piston
    m.box("mech_fore", -1.5, -1.5, -1.5, 3, 3, 3, B.brass(74))                          # the elbow
    m.box("mech_fore", -1.25, -10, -1.25, 2, 9, 2, B.brass(75))
    m.box("claw", -2, -2, -2, 4, 2, 4, B.brass(76))
    for x, z in ((-2, -2), (1, -2), (-0.5, 1)):
        m.box("claw", x, -5, z, 1, 3, 1, claw)                                          # three fingers
    m.box("claw", -1.5, -5, -3.5, 3, 2, 6, bar)                                         # the gold bar

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
    REST = {"arm_r": (-20, 0, 8), "fore_r": (-40, 0, 0), "sword": (60, 0, 0), "arm_l": (-10, 0, -10),
            "fore_l": (-50, 0, 0), "mech_up": (18, 0, 0), "mech_fore": (80, 0, 0)}
    LEGS = [(f"thigh_{e}{s}", f"shin_{e}{s}", sx) for e in ("f", "b") for s, sx in (("r", -1), ("l", 1))]

    idle = _abs(m, m.anim("idle", 3.0))
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, -0.4, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (-4, -10, 0)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, REST["arm_l"]), (1.5, (-30, -10, -16)), (3.0, REST["arm_l"]))       # admiring his rings
    idle.rot("mech_up", (0, REST["mech_up"]), (1.5, (24, 6, 0)), (3.0, REST["mech_up"]))
    idle.rot("mech_fore", (0, REST["mech_fore"]), (1.5, (72, 0, 0)), (3.0, REST["mech_fore"]))
    idle.rot("claw", (0, (0, 0, 0)), (3.0, (0, 360, 0), "linear"))                            # turning the bar

    walk = _abs(m, m.anim("walk", 1.2))
    for i, (th, sh, sx) in enumerate(LEGS):
        ph = 0.0 if i in (0, 3) else 0.6
        lift = (0, 0, (-14 - 16) * sx)
        down = (0, 0, -14 * sx)
        walk.rot(th, (0, down if ph else lift), (0.6, lift if ph else down), (1.2, down if ph else lift))
    walk.pos("car", (0, (0, 0, 0)), (0.3, (0, -0.6, 0)), (0.6, (0, 0, 0)), (0.9, (0, -0.6, 0)), (1.2, (0, 0, 0)))
    walk.rot("chest", (0, (0, -4, 0)), (0.6, (0, 4, 0)), (1.2, (0, -4, 0)))

    # slash (14 / 12 / 16): he draws the scimitar back across his body, high over his left shoulder (0.7 s), sweeps it
    # round his front at 0.7 s and flicks it out again at 1.0 s (the crescent), then lowers it
    a = _abs(m, m.anim("slash", 2.1))
    a.rot("arm_r", (0, REST["arm_r"]), (0.6, (-150, -60, -30)), (0.7, (-152, -62, -30)),
          (0.8, (-80, 70, 30), "linear"), (0.95, (-110, 40, 20)), (1.0, (-90, -10, 0), "linear"), (1.4, (-80, 0, 4)),
          (2.1, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.7, (-30, 0, 0)), (1.0, (-10, 0, 0)), (2.1, REST["fore_r"]))
    a.rot("sword", (0, REST["sword"]), (0.7, (80, 0, 0)), (1.0, (90, 0, 0)), (1.4, (85, 0, 0)), (2.1, REST["sword"]))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (0, -34, 0)), (0.8, (0, 28, 0), "linear"), (1.0, (0, -6, 0), "linear"),
          (2.1, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (0, 20, 0)), (1.0, (0, 0, 0)), (2.1, (0, 0, 0)))

    # coins (18 / 16 / 14): the brass arm dips into the coffer and swings back loaded (0.9 s); at 0.9 s it flings the
    # coins forward three times (every 0.25 s) in wide sweeps, while he waves the scimitar like a baton
    a = _abs(m, m.anim("coins", 2.4))
    a.rot("mech_up", (0, REST["mech_up"]), (0.4, (60, 0, 0)), (0.6, (64, 0, 0)), (0.85, (-30, 0, 0)),
          (0.9, (-32, 0, 0)), (0.98, (50, -30, 0), "linear"), (1.12, (10, 0, 0)), (1.23, (50, 0, 0), "linear"),
          (1.37, (10, 20, 0)), (1.48, (50, 30, 0), "linear"), (1.7, (40, 0, 0)), (2.4, REST["mech_up"]))
    a.rot("mech_fore", (0, REST["mech_fore"]), (0.4, (100, 0, 0)), (0.85, (20, 0, 0)), (0.98, (60, 0, 0), "linear"),
          (1.12, (30, 0, 0)), (1.23, (60, 0, 0), "linear"), (1.37, (30, 0, 0)), (1.48, (60, 0, 0), "linear"),
          (2.4, REST["mech_fore"]))
    a.rot("claw", (0, (0, 0, 0)), (0.9, (40, 0, 0)), (0.98, (-40, 0, 0), "linear"), (1.6, (-30, 0, 0)), (2.4, (0, 0, 0)))
    a.rot("arm_r", (0, REST["arm_r"]), (0.9, (-110, 0, 30)), (1.2, (-100, 0, 50)), (1.5, (-110, 0, 20)),
          (2.4, REST["arm_r"]))
    a.rot("head", (0, (0, 0, 0)), (0.9, (-10, 0, 0)), (1.5, (6, 0, 0)), (2.4, (0, 0, 0)))

    # bid (16 / 40 / 14): he raises a jewelled finger at you and the arm lifts the gold bar high (0.8 s); he holds the
    # pose while the price climbs, the arm rising higher and higher, and at 2.75 s brings the bar crashing down (the
    # slam falls on the marked spot at 2.75 s), then settles back
    a = _abs(m, m.anim("bid", 3.5))
    a.rot("arm_l", (0, REST["arm_l"]), (0.8, (-100, -10, -10)), (2.6, (-110, -10, -10)), (2.8, (-60, 0, -10)),
          (3.5, REST["arm_l"]))
    a.rot("fore_l", (0, REST["fore_l"]), (0.8, (-10, 0, 0)), (2.6, (-10, 0, 0)), (3.5, REST["fore_l"]))
    a.rot("mech_up", (0, REST["mech_up"]), (0.8, (-10, 0, 0)), (2.2, (-20, 0, 0)), (2.6, (-24, 0, 0)),
          (2.75, (60, 0, 0), "linear"), (3.1, (56, 0, 0)), (3.5, REST["mech_up"]))
    a.rot("mech_fore", (0, REST["mech_fore"]), (0.8, (10, 0, 0)), (2.6, (0, 0, 0)), (2.75, (70, 0, 0), "linear"),
          (3.5, REST["mech_fore"]))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-10, 0, 0)), (2.6, (-14, 0, 0)), (2.8, (4, 0, 0)), (3.5, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (-6, 10, 0)), (2.6, (-8, 10, 0)), (2.8, (6, 0, 0)), (3.5, (0, 0, 0)))

    # charge (16 / 8 / 16): the palanquin crouches low on its legs, the prince levels the scimitar (0.8 s); at 0.8 s the
    # legs spring and it scuttles forward, then rises again
    a = _abs(m, m.anim("charge", 2.0))
    a.pos("car", (0, (0, 0, 0)), (0.8, (0, 4, 0)), (0.85, (0, -1, 0), "linear"), (1.2, (0, 0, 0)), (2.0, (0, 0, 0)))
    for th, sh, sx in LEGS:
        a.rot(th, (0, (0, 0, -14 * sx)), (0.8, (0, 0, 14 * sx)), (0.85, (0, 0, -30 * sx), "linear"),
              (1.0, (0, 0, -6 * sx)), (1.2, (0, 0, -30 * sx)), (2.0, (0, 0, -14 * sx)))
    a.rot("arm_r", (0, REST["arm_r"]), (0.8, (-86, 10, 0)), (1.2, (-90, 0, 0)), (2.0, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.8, (0, 0, 0)), (1.2, (0, 0, 0)), (2.0, REST["fore_r"]))
    a.rot("sword", (0, REST["sword"]), (0.8, (90, 0, 0)), (1.2, (90, 0, 0)), (2.0, REST["sword"]))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (14, 0, 0)), (1.2, (18, 0, 0)), (2.0, (0, 0, 0)))

    # hire (20 / 10 / 16): the arm lifts a fat purse (the bar) and tosses it high (1.0 s); at 1.0 s he spreads his
    # hands to the bidders' steps, summoning his hired blades
    a = _abs(m, m.anim("hire", 2.3))
    a.rot("mech_up", (0, REST["mech_up"]), (0.7, (40, 0, 0)), (1.0, (-30, 0, 0), "linear"), (1.6, (-20, 0, 0)),
          (2.3, REST["mech_up"]))
    a.pos("claw", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.3, (0, -8, 0)), (1.6, (0, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("claw", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.6, (0, 720, 0)), (2.3, (0, 720, 0)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.0, (-50, 0, 70 * sz)), (1.06, (-56, 0, 76 * sz), "linear"),
              (1.8, (-50, 0, 70 * sz)), (2.3, REST[f"arm_{s}"]))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.8, (-10, 0, 0)), (2.3, (0, 0, 0)))

    # sandstorm (24 / 6 / 16): he whirls the scimitar round over his head, the palanquin turning with him (1.2 s); at
    # 1.2 s he points it at the spot and the vortex rises there
    a = _abs(m, m.anim("sandstorm", 2.3))
    a.rot("arm_r", (0, REST["arm_r"]), (0.3, (-170, 0, 20)), (1.1, (-170, 0, 20)), (1.2, (-90, 0, 0), "linear"),
          (1.6, (-86, 0, 0)), (2.3, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.3, (0, 0, 0)), (1.6, (0, 0, 0)), (2.3, REST["fore_r"]))
    a.rot("sword", (0, REST["sword"]), (0.3, (90, 0, 0)), (1.1, (90, 1080, 0), "linear"), (1.2, (90, 1080, 0)),
          (2.3, (60, 1080, 0)))
    a.rot("car", (0, (0, 0, 0)), (1.1, (0, 40, 0)), (1.2, (0, 0, 0), "linear"), (2.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-20, 0, 0)), (1.2, (6, 0, 0)), (2.3, (0, 0, 0)))

    # auction (phase 3, 40 / 20 / 20): he rises on the palanquin's legs, arms wide, the arm beating the bar on the
    # coffer like a gavel faster and faster (2.0 s); at 2.0 s the final blow: the Final Auction
    a = _abs(m, m.anim("auction", 4.0))
    a.pos("car", (0, (0, 0, 0)), (1.0, (0, -4, 0)), (2.0, (0, -4, 0)), (2.06, (0, 1, 0), "linear"), (2.6, (0, 0, 0)),
          (4.0, (0, 0, 0)))
    for th, sh, sx in LEGS:
        a.rot(th, (0, (0, 0, -14 * sx)), (1.0, (0, 0, -40 * sx)), (2.0, (0, 0, -40 * sx)),
              (2.06, (0, 0, 0), "linear"), (2.6, (0, 0, -14 * sx)), (4.0, (0, 0, -14 * sx)))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.9, (-60, 0, 110 * sz)), (2.0, (-62, 0, 112 * sz)),
              (2.06, (-160, 0, 20 * sz), "linear"), (3.2, (-156, 0, 22 * sz)), (4.0, REST[f"arm_{s}"]))
    a.rot("mech_up", (0, REST["mech_up"]), (0.4, (-20, 0, 0)), (0.7, (50, 0, 0), "linear"), (1.0, (-20, 0, 0)),
          (1.25, (50, 0, 0), "linear"), (1.45, (-20, 0, 0)), (1.65, (50, 0, 0), "linear"), (1.8, (-30, 0, 0)),
          (2.0, (70, 0, 0), "linear"), (3.0, (60, 0, 0)), (4.0, REST["mech_up"]))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-24, 0, 0)), (3.2, (-20, 0, 0)), (4.0, (0, 0, 0)))

    # dash (phase 3, 16 / 46 / 14): the palanquin crouches and springs (0.8 s); three dashes at 0.8, 1.8 and 2.8 s, the
    # legs flung back on each, the scimitar held out
    a = _abs(m, m.anim("dash", 3.8))
    keys = [(0, (0, 0, 0)), (0.8, (0, 4, 0))]
    for t0 in (0.8, 1.8, 2.8):
        keys += [(t0 + 0.05, (0, -1, 0), "linear"), (t0 + 0.3, (0, 0, 0)), (t0 + 0.9, (0, 3, 0))]
    keys[-1] = (3.7, (0, 0, 0))
    keys.append((3.8, (0, 0, 0)))
    a.pos("car", *keys)
    a.rot("arm_r", (0, REST["arm_r"]), (0.8, (-80, 30, 30)), (3.1, (-80, 30, 30)), (3.8, REST["arm_r"]))
    a.rot("sword", (0, REST["sword"]), (0.8, (90, 0, 0)), (3.1, (90, 0, 0)), (3.8, REST["sword"]))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (16, 0, 0)), (3.1, (16, 0, 0)), (3.8, (0, 0, 0)))
    a.rot("mech_up", (0, REST["mech_up"]), (0.8, (-10, 0, 0)), (3.1, (-10, 0, 0)), (3.8, REST["mech_up"]))

    # roar (phase two): he rises, flings his arms wide and the arm brandishes the gold bar overhead
    a = _abs(m, m.anim("roar", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.5, (-40, 0, 110)), (1.6, (-44, 0, 112)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.5, (-40, 0, -110)), (1.6, (-44, 0, -112)), (2.0, REST["arm_l"]))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("mech_up", (0, REST["mech_up"]), (0.5, (-20, 0, 0)), (1.6, (-20, 0, 0)), (2.0, REST["mech_up"]))
    a.rot("mech_fore", (0, REST["mech_fore"]), (0.5, (10, 0, 0)), (1.6, (10, 0, 0)), (2.0, REST["mech_fore"]))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-12, 0, 0)), (1.6, (-10, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: the palanquin's front legs buckle, he slumps against the cushion, the turban askew, the arm sagging
    a = _abs(m, m.anim("stagger", 2.0))
    a.rot("car", (0, (0, 0, 0)), (0.3, (6, 0, 0)), (1.6, (6, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("car", (0, (0, 0, 0)), (0.3, (0, 3, 0)), (1.6, (0, 3, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (14, 0, 10)), (1.6, (16, 0, 10)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, -16)), (1.6, (20, 0, -16)), (2.0, (0, 0, 0)))
    a.rot("mech_up", (0, REST["mech_up"]), (0.3, (70, 0, 20)), (1.6, (70, 0, 20)), (2.0, REST["mech_up"]))
    a.rot("mech_fore", (0, REST["mech_fore"]), (0.3, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, REST["mech_fore"]))
    a.rot("arm_r", (0, REST["arm_r"]), (0.3, (-10, 0, 20)), (1.6, (-10, 0, 20)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (10, 0, -20)), (1.6, (10, 0, -20)), (2.0, REST["arm_l"]))
