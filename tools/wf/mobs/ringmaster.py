"""The Clockwork Ringmaster (Le Monsieur Loyal mécanique): the champion of the Clockwork Carnival, about 3.6 blocks.

Silhouette idea: a tall, thin brass showman of an abandoned steam carnival. A towering black silk top hat with a red
band, a brass buckle and a little steam whistle on its crown; a grinning lacquered brass face with a curled handlebar
moustache, rosy cheeks and an amber monocle; a high collar and a black bow tie over a white shirt front, a gold
brocade waistcoat with brass buttons, a scarlet tailcoat piped in gold with long swallow tails behind and brass cog
epaulettes fringed in gold; long legs in black-and-grey striped trousers, white spats over black boots. A wind-up key
turns slowly in his back. In his right white-gloved hand a black telescoping cane with a gold knob and a brass
ferrule (it whips out to twice its length); in his left a brass juggling bomb with a lit fuse.
"""
from ..texgen import mix, mul
from ..models import Model
from . import brasswork as B

SCARLET = (176, 30, 36)
SCARLET_L = (222, 64, 60)
SCARLET_D = (110, 16, 24)
GOLD = (226, 182, 72)
GOLD_L = (255, 226, 130)
GOLD_D = (156, 112, 36)
SILK = (30, 26, 32)
SILK_L = (70, 64, 78)
SILK_D = (14, 12, 16)
WHITE = (238, 234, 226)
WHITE_D = (196, 190, 182)
STRIPE_A = (36, 34, 40)
STRIPE_B = (120, 118, 126)
FACE = (214, 170, 92)           # the lacquered brass of his face
FACE_L = (246, 214, 140)
FACE_D = (150, 108, 52)
CHEEK = (222, 108, 92)
TEETH = (246, 240, 222)
MOUTH = (60, 20, 22)
LENS = (255, 176, 60)
LENS_L = (255, 236, 160)
FUSE = (255, 140, 40)

KEY_ROWS = [".##..##.",
            "#..##..#",
            "#..##..#",
            "#..##..#",
            "#..##..#",
            ".##..##."]


# ---------------------------------------------------------------- paint
def coat(seed=0, piping_rows=(), piping_cols=()):
    """The scarlet tailcoat: a fine twill, gold piping on the given rows and columns, darker at the edges."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return SCARLET_D
        if y in piping_rows or (face in ("front", "back") and x in piping_cols):
            return GOLD_L if (x + y) % 3 == 0 else GOLD
        r = B.n(x, y, seed)
        c = SCARLET_L if (x + y) % 4 == 0 and r > 0.6 else (SCARLET if r > 0.15 else SCARLET_D)
        if x in (0, w - 1) and face != "top":
            c = mix(c, SCARLET_D, 0.5)
        return c
    return f


def waistcoat(face, x, y, w, h):
    """Gold brocade: a diamond pattern, brass buttons down the middle of the front."""
    if face == "front" and x in (w // 2 - 1, w // 2) and y % 3 == 1:
        return B.BRASS_L if x == w // 2 - 1 else B.BRASS_D
    if face == "bottom":
        return GOLD_D
    d = (x + y) % 4 == 0 or (x - y) % 4 == 0
    return GOLD_L if d else (GOLD if B.n(x, y, 7) > 0.2 else GOLD_D)


def shirt(face, x, y, w, h):
    return WHITE if (y + x) % 5 else WHITE_D


def bowtie(face, x, y, w, h):
    if face == "front" and x == w // 2:
        return SILK_L
    return SILK if (x + y) % 3 else SILK_D


def silk(seed=0, sheen_col=None):
    """Black silk: a soft vertical sheen down one column, faint noise."""
    def f(face, x, y, w, h):
        if face == "top":
            return SILK_L if (x + y) % 5 == 0 else SILK
        sc = sheen_col if sheen_col is not None else w // 3
        if face in ("front", "left") and abs(x - sc) <= 0 and y > 0:
            return SILK_L
        r = B.n(x, y, seed)
        return SILK if r > 0.2 else SILK_D
    return f


def hat_band(face, x, y, w, h):
    if y == 0 or y == h - 1:
        return SCARLET_D
    return SCARLET if (x + y) % 3 else SCARLET_L


def stripes(seed=0):
    """Striped trousers: black and grey vertical stripes, two texels each."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return STRIPE_A
        c = STRIPE_B if (x // 1) % 3 == 1 else STRIPE_A
        return mul(c, 1.0 + (B.n(x, y, seed) - 0.5) * 0.1)
    return f


def boot(face, x, y, w, h):
    """Black boots with white spats buttoned on the outer side."""
    if face == "bottom":
        return SILK_D
    if y < h - 1:
        if face in ("left", "right") and x == w - 2 and y % 2 == 0:
            return B.BRASS_L
        return WHITE if (x + y) % 6 else WHITE_D
    return SILK


def boot_toe(face, x, y, w, h):
    if face == "top":
        return SILK_L if x % 3 == 0 else SILK
    return SILK if y < h - 1 else SILK_D


def glove(face, x, y, w, h):
    return WHITE if (x * 2 + y) % 7 else WHITE_D


def cuff(face, x, y, w, h):
    return GOLD_L if y == 0 else (GOLD if x % 2 else GOLD_D)


def face(face_, x, y, w, h):
    """The lacquered brass face (8 x 9): arched black brows, a bright left eye, the amber monocle on the right eye
    (its own cube), rosy cheeks, a wide grin of white teeth under the moustache; plates and rivets on the sides."""
    if face_ == "top":
        return FACE_D
    if face_ == "front":
        if y == 2 and x in (1, 2, 5, 6):
            return SILK                                                             # the brows
        if y == 3 and x == 5:
            return (250, 246, 230)
        if y == 3 and x == 6:
            return (40, 30, 30)                                                     # his left eye (the right eye is
        if y == 5 and x in (0, 7):                                                  # behind the monocle)
            return CHEEK
        if y == 7 and 1 <= x <= 6:
            return TEETH if x % 2 else mix(TEETH, FACE_D, 0.25)                     # the grin
        if y == 8 and 2 <= x <= 5:
            return MOUTH
        if y == 6 and x in (1, 6):
            return MOUTH                                                            # the corners of the grin
        if y in (4, 5) and x in (3, 4):
            return FACE_L if y == 4 else FACE                                       # the nose ridge
    if face_ in ("left", "right") and y in (2, 6) and x in (2, 5):
        return B.BRASS_L                                                            # rivets
    if face_ in ("left", "right") and x == 4:
        return FACE_D                                                               # a plate seam
    r = B.n(x, y, 31)
    return FACE_L if r > 0.85 else (FACE if r > 0.15 else FACE_D)


def face_glow(face_, x, y, w, h):
    if face_ == "front" and y == 3 and x == 6:
        return (255, 196, 90)
    return None


def moustache(face, x, y, w, h):
    """A curled handlebar moustache: thick in the middle, curling up at the tips."""
    if face == "front" and x in (0, w - 1):
        return SILK_L
    return SILK if (x + y) % 3 else SILK_D


def monocle(face, x, y, w, h):
    if face != "front":
        return GOLD
    if x in (0, w - 1) or y in (0, h - 1):
        return GOLD_L if (x + y) % 2 == 0 else GOLD
    return LENS_L if (x, y) == (1, 1) else LENS


def monocle_glow(face, x, y, w, h):
    if face == "front" and 0 < x < w - 1 and 0 < y < h - 1:
        return LENS_L
    return None


def epaulette(face, x, y, w, h):
    """A brass cog epaulette seen from above, the gold fringe its own cube under it."""
    if face == "top":
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d < 1.0:
            return B.BRASS_D
        return B.BRASS_L if (x + y) % 2 == 0 else B.BRASS
    return B.BRASS_L if x % 2 == 0 else B.BRASS_D


def fringe(face, x, y, w, h):
    if face in ("top", "bottom"):
        return GOLD_D
    if y == h - 1 and x % 2:
        return None
    return GOLD_L if x % 2 == 0 else GOLD


def key_bow(face, x, y, w, h):
    """The wind-up key's bow, a figure of eight on the broad (left/right) faces of a 1 x 6 x 8 cube."""
    if face in ("left", "right"):
        xx = x if face == "left" else w - 1 - x
        if KEY_ROWS[y][xx] != "#":
            return None
        return B.BRASS_L if y < 2 else (B.BRASS if y < 4 else B.BRASS_D)
    return B.BRASS


def cane(face, x, y, w, h):
    """The black lacquered cane with a silver sheen and a brass band every ten texels."""
    if y % 10 == 9:
        return B.BRASS_L if x % 2 == 0 else B.BRASS
    return SILK_L if (face == "front" and y % 3 == 0) else SILK


def knob(face, x, y, w, h):
    return GOLD_L if face == "top" or y == 0 else (GOLD if (x + y) % 2 else GOLD_D)


def bomb(face, x, y, w, h):
    """A brass juggling bomb: a riveted sphere-ish cube with a red band."""
    if y == h // 2 and face not in ("top", "bottom"):
        return SCARLET
    return B.brass(81)(face, x, y, w, h)


def fuse_glow(face, x, y, w, h):
    return FUSE if face == "top" else None


# ---------------------------------------------------------------- build
def build():
    m = Model("ringmaster", seed=1307, shadow=0.9, walk_speed=0.8, walk_scale=0.7, glow_pulse=0.05)

    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -22, 0))
    m.part("tails", "hips", pivot=(0, -1, 3.5), rot=(8, 0, 0))
    m.part("chest", "hips", pivot=(0, -3, 0))
    m.part("key", "chest", pivot=(0, -9, 3.5))
    m.part("head", "chest", pivot=(0, -18, 0))
    m.part("hat", "head", pivot=(0, -9, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"leg_{side}", "bone", pivot=(2.5 * sx, -22, 0))
        m.part(f"shin_{side}", f"leg_{side}", pivot=(0, 11, 0))
    m.part("arm_r", "chest", pivot=(-7.5, -15, 0), rot=(-6, 0, 4))
    m.part("fore_r", "arm_r", pivot=(0, 9, 0), rot=(-20, 0, 0))
    m.part("cane", "fore_r", pivot=(0, 9.5, 0), rot=(20, 0, 0))
    m.part("arm_l", "chest", pivot=(7.5, -15, 0), rot=(-6, 0, -4))
    m.part("fore_l", "arm_l", pivot=(0, 9, 0), rot=(-40, 0, 0))
    m.part("bomb", "fore_l", pivot=(0, 11, -0.5))

    # ---- legs: striped trousers, white spats over black boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2, -1, -2, 4, 12, 4, stripes(10 + sx))
        m.box(shin, -2, 0, -2, 4, 7, 4, stripes(12 + sx), grow=-0.2)
        m.box(shin, -2.25, 7, -2.25, 4, 3, 4, boot, grow=0.25)
        m.box(shin, -2, 9, -4, 4, 2, 6, boot_toe)

    # ---- hips: the waistcoat's lower edge, the coat's skirts and the long swallow tails
    m.box("hips", -5, -3, -3.5, 10, 4, 7, coat(20, piping_rows=(3,)))
    m.box("hips", -3, -3, -3.8, 6, 3, 1, waistcoat)
    m.box("tails", -5, 0, 0, 4, 15, 1, coat(21, piping_cols=(0,), piping_rows=(14,)))
    m.box("tails", 1, 0, 0, 4, 15, 1, coat(22, piping_cols=(3,), piping_rows=(14,)))

    # ---- the chest: tailcoat, brocade waistcoat, shirt front and bow tie, collar, cog epaulettes
    m.box("chest", -5.5, -16, -3.5, 11, 16, 7, coat(23, piping_cols=(0, 10)))
    m.box("chest", -3, -15, -3.8, 6, 14, 1, waistcoat)
    m.box("chest", -1.5, -16, -4.0, 3, 4, 1, shirt)
    m.box("chest", -2.5, -15, -4.4, 5, 2, 1, bowtie)
    m.box("chest", -5.5, -15, -4.0, 2, 10, 1, coat(24, piping_cols=(1,)))           # the lapels
    m.box("chest", 3.5, -15, -4.0, 2, 10, 1, coat(25, piping_cols=(0,)))
    m.box("chest", -4.5, -18, -3, 9, 2, 6, coat(26, piping_rows=(0,)))              # the high collar
    for sx in (-1, 1):
        x0 = -9.5 if sx < 0 else 5.5
        m.box("chest", x0, -17, -3, 4, 1, 6, epaulette)
        m.box("chest", x0, -16, -3, 4, 2, 6, fringe)
    m.box("chest", -5, -6, -3.9, 10, 1, 1, B.BRASS_D)                               # a watch chain across
    m.box("chest", 2, -7, -4.2, 2, 2, 1, B.BRASS_L)                                 # the fob watch

    # ---- the wind-up key in his back
    m.box("key", -0.5, -0.5, 0, 1, 1, 3, B.BRASS_D)
    m.box("key", -0.5, -3, 3, 1, 6, 8, key_bow)

    # ---- the head: the grinning brass face, moustache and monocle, the towering top hat
    m.box("head", -4, -9, -4, 8, 9, 8, face, glow=face_glow)
    m.box("head", -5, -3, -4.6, 10, 1, 1, moustache)
    m.box("head", -6, -4, -4.6, 1, 1, 1, moustache)                                 # the curled tips
    m.box("head", 5, -4, -4.6, 1, 1, 1, moustache)
    m.box("head", -3.5, -7, -4.7, 3, 3, 1, monocle, glow=monocle_glow)
    m.box("head", -3.5, -4, -4.5, 1, 4, 1, GOLD_D)                                  # the monocle's chain
    m.box("hat", -6.5, -1, -6.5, 13, 1, 13, silk(40))                               # the brim
    m.box("hat", -4.5, -12, -4.5, 9, 11, 9, silk(41))                               # the crown
    m.box("hat", -5, -4, -5, 10, 3, 10, hat_band)
    m.box("hat", -1.5, -4, -5.4, 3, 3, 1, B.brass(42))                              # the buckle
    m.box("hat", 4.6, -9, -1.5, 1, 4, 3, B.cog(teeth=6, faces=("left", "right")))  # a brass cog on the side
    m.box("hat", -1, -14, -1, 2, 2, 2, B.brass(43))                                 # the steam whistle
    m.box("hat", -0.5, -15, -0.5, 1, 1, 1, B.BRASS_L)

    # ---- arms: scarlet sleeves, gold cuffs, white gloves; the cane in the right hand, a bomb in the left
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -1.5, -1, -1.5, 3, 10, 3, coat(50 + sx))
        m.box(fore, -1.5, 0, -1.5, 3, 8, 3, coat(52 + sx))
        m.box(fore, -2, 6, -2, 4, 2, 4, cuff)
        m.box(fore, -1.5, 8, -1.5, 3, 3, 3, glove)
    m.box("cane", -0.5, -4, -0.5, 1, 26, 1, cane)
    m.box("cane", -1, -7, -1, 2, 3, 2, knob)
    m.box("cane", -0.5, 22, -0.5, 1, 2, 1, B.BRASS_L)                               # the ferrule
    m.box("bomb", -1.5, -1.5, -1.5, 3, 3, 3, bomb)
    m.box("bomb", -0.5, -3, -0.5, 1, 2, 1, SILK_L, glow=fuse_glow)

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
    REST = {"arm_r": (-6, 0, 4), "fore_r": (-20, 0, 0), "cane": (20, 0, 0), "arm_l": (-6, 0, -4),
            "fore_l": (-40, 0, 0)}

    idle = _abs(m, m.anim("idle", 3.0))
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, -0.4, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (-3, 8, 2)), (3.0, (0, 0, 0)))
    idle.rot("key", (0, (0, 0, 0)), (3.0, (0, 0, 360), "linear"))
    idle.rot("tails", (0, (8, 0, 0)), (1.5, (11, 0, 0)), (3.0, (8, 0, 0)))
    idle.rot("arm_l", (0, REST["arm_l"]), (0.75, (-20, 0, -4)), (1.5, REST["arm_l"]), (2.25, (-20, 0, -4)),
             (3.0, REST["arm_l"]))                                                  # tossing the bomb in his hand
    idle.pos("bomb", (0, (0, 0, 0)), (0.4, (0, 4, 0)), (0.75, (0, 0, 0)), (1.9, (0, 4, 0)), (2.25, (0, 0, 0)),
             (3.0, (0, 0, 0)))

    walk = _abs(m, m.anim("walk", 2.0))
    walk.rot("leg_r", (0, (24, 0, 0)), (1.0, (-24, 0, 0)), (2.0, (24, 0, 0)))
    walk.rot("leg_l", (0, (-24, 0, 0)), (1.0, (24, 0, 0)), (2.0, (-24, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.0, (0, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.5, (20, 0, 0)), (2.0, (0, 0, 0)))
    walk.rot("arm_r", (0, (-24, 0, 4)), (1.0, (10, 0, 4)), (2.0, (-24, 0, 4)))       # the cane swinging jauntily
    walk.rot("arm_l", (0, (6, 0, -4)), (1.0, (-20, 0, -4)), (2.0, (6, 0, -4)))
    walk.rot("tails", (0, (14, 0, 0)), (0.5, (20, 0, 0)), (1.0, (14, 0, 0)), (1.5, (20, 0, 0)), (2.0, (14, 0, 0)))
    walk.pos("hips", (0, (0, 0, 0)), (0.5, (0, -0.8, 0)), (1.0, (0, 0, 0)), (1.5, (0, -0.8, 0)), (2.0, (0, 0, 0)))

    # cane (14 / 16 / 14): he cocks the cane back over his right shoulder while it telescopes out to twice its length
    # (0.7 s), whips it round his front from right to left at 0.7 s, raises it and cracks it straight down ahead at
    # 1.1 s, then the cane slides shut again
    a = _abs(m, m.anim("cane", 2.2))
    a.rot("arm_r", (0, REST["arm_r"]), (0.6, (-100, 70, 40)), (0.7, (-102, 72, 40)),
          (0.78, (-88, -60, -30), "linear"), (0.95, (-165, -10, 10)), (1.1, (-70, 0, 0), "linear"),
          (1.5, (-66, 0, 2)), (2.2, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.7, (-10, 0, 0)), (1.1, (0, 0, 0)), (2.2, REST["fore_r"]))
    a.rot("cane", (0, REST["cane"]), (0.6, (80, 0, 0)), (0.7, (84, 0, 0)), (1.1, (70, 0, 0)), (1.5, (70, 0, 0)),
          (2.2, REST["cane"]))
    a.scale("cane", (0, (1, 1, 1)), (0.6, (1, 1.9, 1)), (1.5, (1, 1.9, 1)), (1.9, (1, 1, 1)), (2.2, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (0, 30, 0)), (0.78, (0, -24, 0), "linear"), (0.95, (-6, -4, 0)),
          (1.1, (10, 0, 0), "linear"), (2.2, (0, 0, 0)))
    a.rot("tails", (0, (8, 0, 0)), (0.78, (30, 0, 0)), (1.3, (16, 0, 0)), (2.2, (8, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (-14, 0, 0)), (1.1, (-18, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (12, 0, 0)), (1.1, (14, 0, 0)), (2.2, (0, 0, 0)))

    # juggle (20 / 20 / 14): he juggles, the bomb leaping from hand to hand faster and faster (1.0 s); at 1.0 s he
    # flings both hands up and the bombs fly off in their arcs, then he spreads his arms with a flourish
    a = _abs(m, m.anim("juggle", 2.7))
    a.rot("arm_l", (0, REST["arm_l"]), (0.25, (-60, 0, -10)), (0.45, (-30, 0, -4)), (0.65, (-70, 0, -10)),
          (0.8, (-34, 0, -4)), (0.92, (-60, 0, -8)), (1.0, (-150, 0, -20), "linear"), (1.6, (-140, 0, -40)),
          (2.0, (-60, 0, -70)), (2.7, REST["arm_l"]))
    a.rot("arm_r", (0, REST["arm_r"]), (0.35, (-60, 0, 10)), (0.55, (-30, 0, 4)), (0.72, (-66, 0, 10)),
          (0.86, (-34, 0, 4)), (1.0, (-150, 0, 20), "linear"), (1.6, (-140, 0, 40)), (2.0, (-60, 0, 70)),
          (2.7, REST["arm_r"]))
    a.pos("bomb", (0, (0, 0, 0)), (0.2, (0, 8, 0)), (0.4, (0, 0, 0)), (0.6, (0, 9, 0)), (0.78, (0, 0, 0)),
          (0.9, (0, 6, 0)), (1.0, (0, 0, 0)), (2.7, (0, 0, 0)))
    a.scale("bomb", (0, (1, 1, 1)), (1.0, (1, 1, 1)), (1.04, (0, 0, 0), "linear"), (2.3, (0, 0, 0)),
            (2.5, (1, 1, 1)), (2.7, (1, 1, 1)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-20, 0, 0)), (1.0, (-30, 0, 0)), (2.0, (-6, 0, 0)), (2.7, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-6, 0, 0)), (2.0, (0, 0, 0)), (2.7, (0, 0, 0)))

    # hat (18 / 30 / 14): he lifts the top hat from his head with his left hand (0.5 s), winds it back across his
    # body and spins it out like a discus at 0.9 s; it sails out and back and he catches it and claps it on at 2.3 s
    a = _abs(m, m.anim("hat", 3.1))
    a.rot("arm_l", (0, REST["arm_l"]), (0.45, (-175, 0, -10)), (0.55, (-170, 0, -10)), (0.85, (-80, 60, 50)),
          (0.9, (-82, 62, 50)), (0.96, (-80, -60, -40), "linear"), (1.4, (-60, -30, -20)), (2.1, (-120, 0, -30)),
          (2.3, (-170, 0, -10)), (2.6, (-140, 0, -10)), (3.1, REST["arm_l"]))
    a.pos("hat", (0, (0, 0, 0)), (0.45, (0, 2, 0)), (0.55, (2, 4, 0)), (0.85, (8, -8, -4)), (0.9, (8, -8, -4)),
          (0.94, (0, 0, 0), "linear"), (2.26, (0, 0, 0)), (2.3, (0, 3, 0), "linear"), (2.5, (0, 0, 0)),
          (3.1, (0, 0, 0)))
    a.scale("hat", (0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.94, (0, 0, 0), "linear"), (2.26, (0, 0, 0)),
            (2.3, (1, 1, 1), "linear"), (3.1, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, -34, 0)), (0.96, (0, 26, 0), "linear"), (1.6, (0, 10, 0)),
          (3.1, (0, 0, 0)))
    a.rot("arm_r", (0, REST["arm_r"]), (0.9, (-30, 0, 30)), (2.3, (-30, 0, 30)), (3.1, REST["arm_r"]))

    # flourish (16 / 8 / 16): he crouches and levels the cane at you like a rapier (0.8 s), then lunges across the
    # ring cane-first at 0.8 s; he rises and twirls the cane
    a = _abs(m, m.anim("flourish", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.7, (-84, 10, 0)), (0.8, (-86, 10, 0)), (0.85, (-92, 0, 0), "linear"),
          (1.2, (-90, 0, 0)), (1.6, (-150, 0, 20)), (2.0, REST["arm_r"]))
    a.rot("fore_r", (0, REST["fore_r"]), (0.8, (0, 0, 0)), (1.2, (0, 0, 0)), (2.0, REST["fore_r"]))
    a.rot("cane", (0, REST["cane"]), (0.7, (80, 0, 0)), (0.8, (90, 0, 0)), (1.2, (90, 0, 0)), (1.6, (90, 360, 0)),
          (2.0, REST["cane"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.8, (-40, 0, -60)), (1.2, (-40, 0, -70)), (2.0, REST["arm_l"]))
    a.rot("chest", (0, (0, 0, 0)), (0.8, (16, 20, 0)), (0.85, (26, 0, 0), "linear"), (1.2, (24, 0, 0)),
          (2.0, (0, 0, 0)))
    a.pos("hips", (0, (0, 0, 0)), (0.8, (0, -2, 0)), (0.85, (0, -3, 0), "linear"), (1.2, (0, -3, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.8, (-30, 0, 0)), (0.85, (-50, 0, 0), "linear"), (1.2, (-50, 0, 0)),
          (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.8, (30, 0, 0)), (0.85, (50, 0, 0), "linear"), (1.2, (50, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.8, (20, 0, 0)), (0.85, (34, 0, 0), "linear"), (1.2, (34, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("tails", (0, (8, 0, 0)), (0.85, (60, 0, 0), "linear"), (1.2, (50, 0, 0)), (2.0, (8, 0, 0)))

    # carousel (phase 2, 24 / 80 / 16): he plants the cane, throws his arms wide and starts to turn (1.2 s); at 1.2 s
    # the carousel of fire starts round the ring and he pirouettes with it, four slow turns, until 5.2 s
    a = _abs(m, m.anim("carousel", 6.0))
    a.rot("arm_r", (0, REST["arm_r"]), (1.1, (-20, 0, 80)), (1.2, (-20, 0, 86)), (5.2, (-20, 0, 86)),
          (6.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (1.1, (-20, 0, -80)), (1.2, (-20, 0, -86)), (5.2, (-20, 0, -86)),
          (6.0, REST["arm_l"]))
    a.rot("fore_r", (0, REST["fore_r"]), (1.2, (0, 0, 0)), (5.2, (0, 0, 0)), (6.0, REST["fore_r"]))
    a.rot("fore_l", (0, REST["fore_l"]), (1.2, (0, 0, 0)), (5.2, (0, 0, 0)), (6.0, REST["fore_l"]))
    a.rot("cane", (0, REST["cane"]), (1.2, (0, 0, 0)), (5.2, (0, 0, 0)), (6.0, REST["cane"]))
    a.scale("cane", (0, (1, 1, 1)), (1.2, (1, 1.6, 1)), (5.2, (1, 1.6, 1)), (6.0, (1, 1, 1)))
    a.rot("bone", (0, (0, 0, 0)), (1.2, (0, -20, 0)), (5.2, (0, -1460, 0), "linear"), (6.0, (0, -1440, 0)))
    a.rot("tails", (0, (8, 0, 0)), (1.2, (20, 0, 0)), (1.6, (50, 0, 0)), (5.2, (50, 0, 0)), (6.0, (8, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-14, 0, 0)), (5.2, (-14, 0, 0)), (6.0, (0, 0, 0)))

    # performers (phase 2, 20 / 10 / 16): he doffs the hat with a sweeping bow and presents the ring with his cane
    # (1.0 s); at 1.0 s his performers tumble in
    a = _abs(m, m.anim("performers", 2.3))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (-175, 0, -10)), (0.7, (-60, 0, -40)), (1.0, (-30, 0, -70)),
          (1.6, (-30, 0, -70)), (2.0, (-170, 0, -10)), (2.3, REST["arm_l"]))
    a.pos("hat", (0, (0, 0, 0)), (0.3, (0, 2, 0)), (0.35, (0, 0, 0), "linear"), (1.96, (0, 0, 0)),
          (2.0, (0, 2, 0), "linear"), (2.3, (0, 0, 0)))
    a.scale("hat", (0, (1, 1, 1)), (0.3, (1, 1, 1)), (0.35, (0, 0, 0), "linear"), (1.96, (0, 0, 0)),
            (2.0, (1, 1, 1), "linear"), (2.3, (1, 1, 1)))
    a.rot("chest", (0, (0, 0, 0)), (0.7, (40, 0, 0)), (1.0, (44, 0, 0)), (1.3, (0, 0, 0)), (2.3, (0, 0, 0)))
    a.rot("arm_r", (0, REST["arm_r"]), (0.7, (-20, 0, 30)), (1.0, (-120, 0, 40)), (1.06, (-130, 0, 50), "linear"),
          (1.8, (-120, 0, 40)), (2.3, REST["arm_r"]))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (16, 0, 0)), (1.3, (0, 0, 0)), (2.3, (0, 0, 0)))

    # finale (phase 3, 40 / 20 / 20): arms rising wide, head thrown back, the key whirring, the hat lifting off his
    # head on a jet of steam (2.0 s); at 2.0 s he flings both arms high: the Grand Finale
    a = _abs(m, m.anim("finale", 4.0))
    for s, sz in (("r", 1), ("l", -1)):
        a.rot(f"arm_{s}", (0, REST[f"arm_{s}"]), (1.9, (-60, 0, 120 * sz)), (2.0, (-62, 0, 122 * sz)),
              (2.06, (-170, 0, 20 * sz), "linear"), (3.2, (-166, 0, 22 * sz)), (4.0, REST[f"arm_{s}"]))
    a.rot("head", (0, (0, 0, 0)), (2.0, (-30, 0, 0)), (2.06, (-36, 0, 0), "linear"), (3.2, (-30, 0, 0)),
          (4.0, (0, 0, 0)))
    a.pos("hat", (0, (0, 0, 0)), (2.0, (0, 4, 0)), (2.06, (0, 10, 0), "linear"), (3.0, (0, 10, 0)),
          (3.6, (0, 0, 0)), (4.0, (0, 0, 0)))
    a.rot("hat", (0, (0, 0, 0)), (2.0, (0, 180, 0)), (3.0, (0, 720, 0)), (3.6, (0, 720, 0)), (4.0, (0, 720, 0)))
    a.rot("key", (0, (0, 0, 0)), (2.0, (0, 0, 1080)), (4.0, (0, 0, 1440)))
    a.rot("chest", (0, (0, 0, 0)), (2.0, (-12, 0, 0)), (2.06, (-16, 0, 0), "linear"), (4.0, (0, 0, 0)))

    # roar (phase two): he throws his arms wide, head back, a burst of steam lifting the hat
    a = _abs(m, m.anim("roar", 2.0))
    a.rot("arm_r", (0, REST["arm_r"]), (0.5, (-40, 0, 110)), (1.6, (-44, 0, 112)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.5, (-40, 0, -110)), (1.6, (-44, 0, -112)), (2.0, REST["arm_l"]))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (0, 0, 0)))
    a.pos("hat", (0, (0, 0, 0)), (0.5, (0, 5, 0)), (1.6, (0, 5, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (-12, 0, 0)), (1.6, (-10, 0, 0)), (2.0, (0, 0, 0)))

    # stagger: his spring runs down, he sags onto one knee leaning on the cane, the hat askew, the key stopped
    a = _abs(m, m.anim("stagger", 2.0))
    a.pos("hips", (0, (0, 0, 0)), (0.3, (0, -6, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.3, (-70, 0, 0)), (1.6, (-70, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.3, (80, 0, 0)), (1.6, (80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.3, (60, 0, 0)), (1.6, (60, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (30, 0, 8)), (1.6, (32, 0, 8)), (2.0, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (26, 0, -16)), (1.6, (26, 0, -16)), (2.0, (0, 0, 0)))
    a.rot("hat", (0, (0, 0, 0)), (0.3, (0, 0, -24)), (1.6, (0, 0, -24)), (2.0, (0, 0, 0)))
    a.pos("hat", (0, (0, 0, 0)), (0.3, (-1, -1, 0)), (1.6, (-1, -1, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, REST["arm_r"]), (0.3, (-40, 0, 10)), (1.6, (-40, 0, 10)), (2.0, REST["arm_r"]))
    a.rot("arm_l", (0, REST["arm_l"]), (0.3, (10, 0, -10)), (1.6, (10, 0, -10)), (2.0, REST["arm_l"]))
