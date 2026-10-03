"""The Jade Jaguar (Le Jaguar de jade): a great jaguar carved of living jade, about 2.6 blocks at the shoulder
plates and three with its crest. Gold rosettes are inlaid in the stone, obsidian claws and fangs, glowing gold
eyes, a fan of quetzal plumes rising from the skull and a plumed tail. A gold collar carries a sun disc.
"""
import math

from ..models import FACE_ID, Model, bands, framed, speckle
from ..texgen import mix, mul

JADE = (40, 130, 94)
JADE_L = (98, 190, 138)
JADE_D = (22, 82, 62)
JADE_DD = (10, 46, 36)
BELLY = (136, 196, 160)
GOLD = (240, 194, 64)
GOLD_L = (255, 234, 140)
GOLD_D = (164, 110, 30)
OBS = (30, 22, 44)
OBS_L = (82, 64, 112)
IVORY = (232, 222, 196)
QUETZAL = (28, 168, 120)
QUETZAL_D = (16, 104, 104)
TEAL = (40, 150, 170)
RED = (196, 48, 40)
EYE = (255, 214, 80)
VEIN = (110, 236, 160)
Z = (0, 0, 0)


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (k & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return r


ROSETTE = (".GG..",
           "G..G.",
           "G...G",
           ".G.G.",
           "..G..")


def jade(seed=0, spots=True, base=JADE, belly_rows=0):
    """Polished jade: soft diagonal veins of lighter stone, a darker grain, and inlaid gold rosettes (the
    jaguar's spots) on a staggered lattice. ``belly_rows`` paints the last rows of the sides pale and unspotted."""
    def f(face, x, y, w, h):
        if belly_rows and face in ("left", "right", "front", "back") and y >= h - belly_rows:
            c = mix(BELLY, JADE_L, 0.3) if (x + y) % 5 else BELLY
            return c
        if face == "bottom":
            return mix(BELLY, JADE, 0.35)
        v = (x * 2 + y * 3 + seed * 5) % 23
        c = mix(base, JADE_L, 0.45) if v in (0, 1) else mix(base, JADE_D, 0.35) if v in (11, 12) else base
        if spots:
            row = (y + seed) // 7
            col = (x + (4 if row % 2 else 0) + seed * 2) // 7
            sx = (x + (4 if row % 2 else 0) + seed * 2) % 7
            sy = (y + seed) % 7
            if sx < 5 and sy < 5 and _h(row, col, seed, FACE_ID[face]) % 4 != 0:
                mk = ROSETTE[sy][sx]
                if mk == "G":
                    return GOLD if sy < 2 else GOLD_D        # lit on top, shadowed below
                if 0 < sx < 4 and 0 < sy < 4 and (sx, sy) != (3, 3):
                    return mix(base, JADE_DD, 0.5)           # the dark heart of the rosette
        return c
    return f


def obsidian(face, x, y, w, h):
    return OBS_L if (x + y) % 4 == 0 else OBS


def feather(main, dark, tip, seed=0):
    """A quetzal plume: a light shaft, barbs in two tones, a red-gold tip and a ragged end."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return tip
        if y < 2:
            return tip if y == 0 else GOLD
        if y >= h - 2:
            return GOLD_D if y == h - 1 else GOLD
        if w > 1 and x == w // 2:
            return mix(main, (230, 255, 230), 0.4)              # shaft
        return main if (y // 2 + seed) % 3 else dark
    return f


def plume(main, dark, seed=0):
    """A tail feather seen from above (texture y runs along the feather): gold quill, barbs, a red end."""
    def f(face, x, y, w, h):
        if y < 2:
            return GOLD if y == 0 else GOLD_D
        if y >= h - 2:
            return RED if y == h - 1 or x == 1 else mix(RED, GOLD, 0.4)
        if x == w // 2:
            return mix(main, (230, 255, 230), 0.4)
        return main if (y // 2 + seed) % 3 else dark
    return f


# angry slanted eyes (3 + 2 texels), a dark brow above them and black tear lines running down the cheeks
EYES = {(2, 4), (3, 4), (4, 4), (3, 5), (4, 5), (9, 4), (10, 4), (11, 4), (9, 5), (10, 5)}
BROW = {(1, 3), (2, 3), (3, 3), (4, 2), (5, 2), (8, 2), (9, 2), (10, 3), (11, 3), (12, 3)}
TEAR = {(5, 6), (5, 7), (4, 8), (8, 6), (8, 7), (9, 8), (1, 4), (12, 4), (1, 5), (12, 5)}


def face(f_, x, y, w, h):
    if (x, y) in EYES:
        return EYE
    if (x, y) in BROW or (x, y) in TEAR:
        return OBS
    if y in (0, 1):
        return GOLD if y == 1 else GOLD_D
    if (x, y) in ((6, 3), (7, 3), (6, 4), (7, 4)):
        return JADE_L                                              # bridge of the nose catching the light
    return jade(6, spots=False)(f_, x, y, w, h)


def cracks(seed=0, top_vein=False):
    """Glow layer: a few hairline cracks of living light in the stone (and the spine vein on top)."""
    def f(face, x, y, w, h):
        if face == "top":
            return VEIN if top_vein and x == w // 2 and y % 4 != 3 else None
        if face not in ("left", "right") or w < 8:
            return None
        for k in range(1):
            x0 = (seed * 7 + k * 9 + 4) % max(1, w - 4) + 2
            if y < h - 3 and 2 <= y <= 2 + (seed + k * 5) % (h - 4) and x == x0 + round(1.4 * math.sin(y * 0.8 + k)):
                return VEIN
        return None
    return f


def build():
    m = Model("jade_jaguar", seed=4, shadow=1.5, walk_speed=1.6, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton (y down, -z forward)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -31, -4))
    m.part("haunch", "body", pivot=(0, -1, 3))
    m.part("neck", "body", pivot=(0, -6, -13), rot=(-30, 0, 0))
    m.part("head", "neck", pivot=(0, -1, -8), rot=(30, 0, 0), scale=(1.2, 1.2, 1.2))
    m.part("jaw", "head", pivot=(0, 4, -2))
    m.part("crest", "head", pivot=(0, -7, -1), rot=(-20, 0, 0))
    m.part("leg_fr", "body", pivot=(-7, 5, -9))
    m.part("fore_fr", "leg_fr", pivot=(0, 11, 0))
    m.part("leg_fl", "body", pivot=(7, 5, -9))
    m.part("fore_fl", "leg_fl", pivot=(0, 11, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "haunch", pivot=(sx * 6, 1, 15), rot=(-28, 0, 0))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 11, 0), rot=(68, 0, 0))
        m.part(f"foot_{side}", f"shin_{side}", pivot=(0, 10, 0), rot=(-40, 0, 0))
    m.part("tail1", "haunch", pivot=(0, -5, 20), rot=(-35, 0, 0))
    m.part("tail2", "tail1", pivot=(0, 0, 12), rot=(25, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 0, 11), rot=(30, 0, 0))
    m.part("plume", "tail3", pivot=(0, 0, 10), rot=(20, 0, 0))

    # ------------------------------------------------------------------ body
    # deep chest with a heavy shoulder hump, the spine marked by a glowing vein
    m.box("body", -10, -10, -15, 20, 19, 18, {"*": jade(1, belly_rows=3), "top": jade(1)}, glow=cracks(1, True))
    m.box("body", -11, -12, -14, 22, 4, 10, {"*": jade(2), "top": jade(2)})                   # shoulder blades
    m.box("haunch", -9, -9, -1, 18, 14, 22, {"*": jade(3, belly_rows=3), "top": jade(3)}, glow=cracks(3, True))
    m.box("haunch", -10, -10, 10, 20, 11, 11, jade(4))                                            # rump
    # gold collar with jade beads and a glowing sun disc on the breast
    m.box("body", -11, -11, -17, 22, 6, 5, {"front": bands([(1, GOLD_D), (1, GOLD_L), (2, lambda f_, x, y, w, h: JADE_L if x % 3 == 1 else GOLD), (2, GOLD)]),
                                           "*": bands([(1, GOLD_D), (5, GOLD)])})
    m.box("body", -4, -6, -18, 8, 8, 1, {"front": lambda f_, x, y, w, h: (GOLD_D if x in (0, 7) or y in (0, 7) else
                                                                        RED if 2 < x < 5 and 2 < y < 5 else
                                                                        GOLD_L if (x + y) % 2 else GOLD), "*": GOLD},
          glow={"front": lambda f_, x, y, w, h: (255, 140, 60) if 2 < x < 5 and 2 < y < 5 else
                (255, 220, 120) if (x in (1, 6) or y in (1, 6)) and (x + y) % 2 else None})
    for i, (x, y) in enumerate(((-6, 3), (5, 3))):                                             # hanging jade beads
        m.box("body", x, y - 6, -17, 1, 4, 1, bands([(1, GOLD), (1, JADE_L), (1, GOLD), (1, JADE_L)]))

    # ------------------------------------------------------------------ neck and head
    m.box("neck", -6, -6, -10, 12, 12, 11, jade(5, belly_rows=2))
    m.box("head", -7, -7, -12, 14, 12, 12, {
        "front": face, "*": jade(6)},
        glow={"front": lambda f_, x, y, w, h: EYE if (x, y) in EYES else None})
    m.box("head", -8, -2, -9, 16, 7, 7, jade(7, spots=False))                                  # cheek ruff
    m.box("head", -4, -2, -18, 8, 6, 6, {"front": lambda f_, x, y, w, h: OBS if y < 2 and 1 < x < 6 else
                                         IVORY if y == 5 and x in (1, 6) else jade(8, spots=False)(f_, x, y, w, h),
                                         "top": jade(8, spots=False), "*": jade(8, spots=False)})  # muzzle
    m.box("head", -2, -3, -18, 4, 1, 3, OBS)                                                    # nose bridge
    m.box("head", -8, -9, -13, 16, 2, 4, {"front": lambda f_, x, y, w, h: JADE_L if x % 4 == 1 else GOLD,
                                          "*": GOLD_D, "top": GOLD})                            # gold diadem
    for sx in (-1, 1):
        x0 = 4 if sx > 0 else -7
        m.box("head", x0, -11, -4, 3, 4, 3, {"front": lambda f_, x, y, w, h: OBS if y > 0 and x == 1 else JADE_D,
                                              "*": jade(9)})                                    # ears
        m.box("head", x0 + 1, -12, -3, 1, 1, 1, GOLD)                                           # ear studs
        m.box("head", sx * 2 - (1 if sx > 0 else 0), 4, -17, 1, 3, 1, IVORY)                  # upper fangs
    m.box("jaw", -4, 0, -15, 8, 3, 15, {"*": jade(10, spots=False), "bottom": BELLY,
                                        "top": lambda f_, x, y, w, h: (120, 30, 40)})
    for sx in (-1, 1):
        m.box("jaw", sx * 3 - (1 if sx > 0 else 0), -2, -15, 1, 2, 1, IVORY)                   # lower fangs

    # the crest: a fan of quetzal plumes on a gold base, rising behind the skull
    m.box("crest", -6, -2, -2, 12, 3, 4, framed(GOLD, GOLD_D))
    fan = ((-60, 15, TEAL), (-40, 19, QUETZAL), (-20, 23, QUETZAL), (0, 26, TEAL), (20, 23, QUETZAL),
           (40, 19, QUETZAL), (60, 15, TEAL))
    for i, (ang, ln, col) in enumerate(fan):
        f = m.part(f"crest_{i}", "crest", pivot=(ang / 15.0, -1, 0), rot=(0, 0, ang))
        m.box(f, -1, -ln, 0, 3, ln, 1, feather(col, QUETZAL_D, RED, i),
              glow={"front": lambda f_, x, y, w, h: (255, 210, 120) if y == 0 else None})

    # ------------------------------------------------------------------ legs: thick jade, gold bands, obsidian claws
    for side, sx in (("r", -1), ("l", 1)):
        leg, fore = f"leg_f{side}", f"fore_f{side}"
        m.box(leg, -4, -5, -5, 8, 17, 9, jade(11 + sx))
        m.box(fore, -3, 0, -3, 6, 11, 6, {"*": jade(13 + sx), "side": bands([(6, jade(13 + sx)), (2, GOLD), (1, GOLD_D),
                                                                           (2, jade(13 + sx))])})
        m.box(fore, -4, 11, -6, 8, 4, 9, {"*": jade(15 + sx, spots=False), "bottom": JADE_DD})   # paw
        for cx in (-3, -1, 1, 3):
            m.box(fore, cx - (1 if cx > 0 else 0), 12, -8, 1, 3, 2, obsidian)                    # claws
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        m.box(th, -4, -4, -5, 8, 16, 11, jade(17 + sx))
        m.box(sh, -2, 0, -2, 5, 11, 5, jade(19 + sx))
        m.box(ft, -2, 0, -2, 5, 10, 5, {"*": jade(21 + sx, spots=False),
                                       "side": bands([(2, GOLD), (1, GOLD_D), (7, jade(21 + sx, spots=False))])})
        m.box(ft, -3, 10, -6, 7, 4, 8, {"*": jade(23 + sx, spots=False), "bottom": JADE_DD})
        for cx in (-2, 0, 2):
            m.box(ft, cx, 11, -7, 1, 3, 1, obsidian)

    # ------------------------------------------------------------------ tail and its plume
    m.box("tail1", -2, -2, 0, 5, 5, 13, jade(25))
    m.box("tail2", -2, -2, 0, 4, 4, 12, jade(26))
    m.box("tail3", -1, -1, 0, 3, 3, 11, jade(27))
    m.box("tail3", -2, -2, 8, 5, 5, 2, framed(GOLD, GOLD_D))
    for i, ang in enumerate((-36, -18, 0, 18, 36)):
        f = m.part(f"plume_{i}", "plume", rot=(ang * 0.4, ang, 0))
        ln = 18 if ang == 0 else 15 if abs(ang) == 18 else 12
        m.box(f, -1, -1, 0, 3, 1, ln, {"top": plume(QUETZAL if i % 2 else TEAL, QUETZAL_D, i),
                                        "bottom": plume(QUETZAL_D, JADE_DD, i), "*": QUETZAL_D})

    anims(m)
    return m


def anims(m):
    idle = m.anim("idle", 3.0)
    idle.rot("body", (0, Z), (1.5, (-1.5, 0, 0)), (3.0, Z))
    idle.scale("body", (0, (1, 1, 1)), (1.5, (1.03, 1.04, 1.0)), (3.0, (1, 1, 1)))
    idle.rot("head", (0, Z), (1.0, (3, 6, 0)), (2.0, (-2, -4, 0)), (3.0, Z))
    idle.rot("jaw", (0, Z), (1.5, (5, 0, 0)), (3.0, Z))
    idle.rot("tail1", (0, Z), (1.0, (0, 14, 0)), (2.0, (4, -14, 0)), (3.0, Z))
    idle.rot("tail2", (0, Z), (1.0, (6, 18, 0)), (2.0, (-4, -18, 0)), (3.0, Z))
    idle.rot("tail3", (0, Z), (1.0, (10, 22, 0)), (2.0, (6, -22, 0)), (3.0, Z))
    idle.rot("plume", (0, Z), (1.5, (12, 0, 0)), (3.0, Z))
    idle.rot("crest", (0, Z), (1.5, (-5, 0, 0)), (3.0, Z))

    # walk: a prowling diagonal gait (front right with hind left), the head low and steady
    walk = m.anim("walk", 1.2)
    walk.rot("leg_fr", (0, (28, 0, 0)), (0.6, (-28, 0, 0)), (1.2, (28, 0, 0)))
    walk.rot("leg_fl", (0, (-28, 0, 0)), (0.6, (28, 0, 0)), (1.2, (-28, 0, 0)))
    walk.rot("fore_fr", (0, Z), (0.3, (-35, 0, 0)), (0.6, Z), (1.2, Z))
    walk.rot("fore_fl", (0, Z), (0.6, Z), (0.9, (-35, 0, 0)), (1.2, Z))
    walk.rot("thigh_l", (0, (24, 0, 0)), (0.6, (-24, 0, 0)), (1.2, (24, 0, 0)))
    walk.rot("thigh_r", (0, (-24, 0, 0)), (0.6, (24, 0, 0)), (1.2, (-24, 0, 0)))
    walk.rot("shin_l", (0, Z), (0.3, (-25, 0, 0)), (0.6, Z), (1.2, Z))
    walk.rot("shin_r", (0, Z), (0.6, Z), (0.9, (-25, 0, 0)), (1.2, Z))
    walk.rot("body", (0, (0, 3, 2)), (0.6, (0, -3, -2)), (1.2, (0, 3, 2)))
    walk.rot("tail1", (0, (0, -10, 0)), (0.6, (0, 10, 0)), (1.2, (0, -10, 0)))
    walk.pos("bone", (0, Z), (0.3, (0, 1, 0)), (0.6, Z), (0.9, (0, 1, 0)), (1.2, Z))

    # pounce (impact 0.7): crouch with the haunches coiled, spring, forelegs reaching, land at 1.0
    a = m.anim("pounce", 1.6)
    a.pos("bone", (0, Z), (0.6, (0, -7, 4)), (0.7, (0, -7, 4)), (0.78, (0, 10, -10), "linear"), (0.95, (0, 6, -14)),
          (1.05, (0, -4, -14), "linear"), (1.3, (0, -2, -8)), (1.6, Z))
    a.rot("body", (0, Z), (0.6, (8, 0, 0)), (0.7, (8, 0, 0)), (0.78, (-22, 0, 0), "linear"), (0.95, (-8, 0, 0)),
          (1.05, (14, 0, 0), "linear"), (1.3, (6, 0, 0)), (1.6, Z))
    for leg in ("leg_fr", "leg_fl"):
        a.rot(leg, (0, Z), (0.6, (35, 0, 0)), (0.78, (-80, 0, 0), "linear"), (0.95, (-90, 0, 0)), (1.05, (-20, 0, 0), "linear"),
              (1.3, (-10, 0, 0)), (1.6, Z))
    for fore in ("fore_fr", "fore_fl"):
        a.rot(fore, (0, Z), (0.6, (-60, 0, 0)), (0.78, (20, 0, 0)), (1.05, (-10, 0, 0)), (1.6, Z))
    for th, sh in (("thigh_r", "shin_r"), ("thigh_l", "shin_l")):
        a.rot(th, (0, Z), (0.6, (-30, 0, 0)), (0.78, (60, 0, 0), "linear"), (0.95, (50, 0, 0)), (1.05, (10, 0, 0)), (1.6, Z))
        a.rot(sh, (0, Z), (0.6, (25, 0, 0)), (0.78, (-20, 0, 0), "linear"), (1.05, (10, 0, 0)), (1.6, Z))
    a.rot("head", (0, Z), (0.6, (-10, 0, 0)), (0.78, (20, 0, 0)), (1.05, (-5, 0, 0)), (1.6, Z))
    a.rot("jaw", (0, Z), (0.6, (20, 0, 0)), (0.95, (35, 0, 0)), (1.05, (5, 0, 0)), (1.6, Z))
    a.rot("tail1", (0, Z), (0.6, (-20, 0, 0)), (0.78, (30, 0, 0)), (1.05, (10, 0, 0)), (1.6, Z))

    # claw (impacts 0.6 and 0.95): rises on the hind legs, right paw rakes across, then the left
    a = m.anim("claw", 1.6)
    a.rot("body", (0, Z), (0.5, (-22, 20, 0)), (0.6, (-18, 20, 0)), (0.7, (-14, -20, 0), "linear"), (0.85, (-20, -20, 0)),
          (0.95, (-18, -20, 0)), (1.05, (-12, 20, 0), "linear"), (1.3, (-6, 8, 0)), (1.6, Z))
    a.pos("bone", (0, Z), (0.5, (0, 2, 2)), (0.7, (0, 0, -4)), (1.05, (0, 0, -8)), (1.6, Z))
    a.rot("leg_fr", (0, Z), (0.5, (-110, 0, 40)), (0.6, (-110, 0, 40)), (0.7, (-40, 0, -30), "linear"), (1.0, (-20, 0, 0)), (1.6, Z))
    a.rot("fore_fr", (0, Z), (0.5, (-30, 0, 0)), (0.7, (-10, 0, 0)), (1.6, Z))
    a.rot("leg_fl", (0, Z), (0.5, (-30, 0, 0)), (0.85, (-110, 0, -40)), (0.95, (-110, 0, -40)), (1.05, (-40, 0, 30), "linear"),
          (1.3, (-20, 0, 0)), (1.6, Z))
    a.rot("fore_fl", (0, Z), (0.85, (-30, 0, 0)), (1.05, (-10, 0, 0)), (1.6, Z))
    a.rot("head", (0, Z), (0.5, (10, -15, 0)), (0.7, (10, 15, 0)), (0.95, (10, 15, 0)), (1.05, (10, -15, 0)), (1.6, Z))
    a.rot("jaw", (0, Z), (0.5, (25, 0, 0)), (1.3, (25, 0, 0)), (1.6, Z))
    for th in ("thigh_r", "thigh_l"):
        a.rot(th, (0, Z), (0.5, (20, 0, 0)), (1.3, (15, 0, 0)), (1.6, Z))

    # tail_sweep (impact 0.75): coils to the right, then the whole body whirls a full turn, tail lashing out
    a = m.anim("tail_sweep", 1.6)
    a.rot("bone", (0, Z), (0.65, (0, 40, 0)), (0.75, (0, 40, 0)), (1.05, (0, -320, 0), "linear"), (1.3, (0, -360, 0)), (1.6, (0, -360, 0)), (1.6, Z))
    a.pos("bone", (0, Z), (0.65, (0, -3, 0)), (0.85, (0, 2, 0)), (1.05, Z), (1.6, Z))
    a.rot("tail1", (0, Z), (0.65, (0, -50, 0)), (0.75, (30, -50, 0)), (0.85, (35, 30, 0), "linear"), (1.05, (35, 40, 0)), (1.3, (10, 0, 0)), (1.6, Z))
    a.rot("tail2", (0, Z), (0.65, (0, -40, 0)), (0.85, (-15, 20, 0), "linear"), (1.05, (-20, 30, 0)), (1.6, Z))
    a.rot("tail3", (0, Z), (0.65, (0, -40, 0)), (0.85, (-20, 20, 0), "linear"), (1.05, (-25, 25, 0)), (1.6, Z))
    a.rot("head", (0, Z), (0.65, (0, -30, 0)), (1.05, (0, 25, 0)), (1.6, Z))
    a.rot("body", (0, Z), (0.65, (6, 0, -8)), (1.05, (0, 0, 10)), (1.6, Z))

    # bellow (impact 0.8): head drawn low, then thrust forward, jaws wide, the crest flaring
    a = m.anim("bellow", 1.8)
    a.rot("neck", (0, Z), (0.7, (25, 0, 0)), (0.8, (28, 0, 0)), (0.88, (-20, 0, 0), "linear"), (1.3, (-18, 0, 0)), (1.8, Z))
    a.rot("head", (0, Z), (0.7, (10, 0, 0)), (0.88, (-15, 0, 0), "linear"), (1.3, (-15, 0, 0)), (1.8, Z))
    a.rot("jaw", (0, Z), (0.7, (8, 0, 0)), (0.88, (55, 0, 0), "linear"), (1.3, (50, 0, 0)), (1.8, Z))
    a.rot("body", (0, Z), (0.7, (6, 0, 0)), (0.88, (-8, 0, 0), "linear"), (1.3, (-8, 0, 0)), (1.8, Z))
    a.pos("bone", (0, Z), (0.7, (0, -3, 3)), (0.88, (0, 0, -3), "linear"), (1.3, (0, 0, -3)), (1.8, Z))
    a.rot("crest", (0, Z), (0.7, (-15, 0, 0)), (0.88, (25, 0, 0), "linear"), (1.3, (25, 0, 0)), (1.8, Z))
    a.scale("crest", (0, (1, 1, 1)), (0.88, (1.3, 1.25, 1.0)), (1.3, (1.3, 1.25, 1.0)), (1.8, (1, 1, 1)))
    a.rot("tail1", (0, Z), (0.88, (40, 0, 0)), (1.3, (40, 0, 0)), (1.8, Z))

    # perch (land at 1.8): crouch, spring straight up (0.6), cling high above the floor curled and staring
    # down, then dive head first (1.6) and land in a crouch
    a = m.anim("perch", 3.0)
    a.pos("bone", (0, Z), (0.55, (0, -8, 0)), (0.6, (0, -8, 0)), (0.7, (0, 4, 0), "linear"), (1.75, (0, 2, 0)),
          (1.8, (0, -6, 0), "linear"), (2.1, (0, -5, 0)), (3.0, Z))
    a.rot("body", (0, Z), (0.55, (10, 0, 0)), (0.7, (-40, 0, 0), "linear"), (0.9, (25, 0, 0)), (1.55, (30, 0, 0)),
          (1.65, (45, 0, 0), "linear"), (1.8, (10, 0, 0), "linear"), (2.1, (6, 0, 0)), (3.0, Z))
    for leg in ("leg_fr", "leg_fl"):
        a.rot(leg, (0, Z), (0.55, (30, 0, 0)), (0.7, (-60, 0, 0)), (0.9, (40, 0, 0)), (1.55, (40, 0, 0)),
              (1.65, (-90, 0, 0), "linear"), (1.8, (-30, 0, 0), "linear"), (2.1, (-25, 0, 0)), (3.0, Z))
    for fore in ("fore_fr", "fore_fl"):
        a.rot(fore, (0, Z), (0.55, (-50, 0, 0)), (0.9, (-80, 0, 0)), (1.55, (-80, 0, 0)), (1.65, (0, 0, 0)),
              (2.1, (-10, 0, 0)), (3.0, Z))
    for th, sh in (("thigh_r", "shin_r"), ("thigh_l", "shin_l")):
        a.rot(th, (0, Z), (0.55, (-35, 0, 0)), (0.7, (50, 0, 0), "linear"), (0.9, (-50, 0, 0)), (1.55, (-50, 0, 0)),
              (1.65, (40, 0, 0)), (1.8, (-20, 0, 0)), (2.1, (-25, 0, 0)), (3.0, Z))
        a.rot(sh, (0, Z), (0.55, (30, 0, 0)), (0.9, (40, 0, 0)), (1.55, (40, 0, 0)), (1.8, (20, 0, 0)), (3.0, Z))
    a.rot("head", (0, Z), (0.9, (20, 0, 0)), (1.55, (25, 0, 0)), (1.8, (-10, 0, 0)), (3.0, Z))
    a.rot("jaw", (0, Z), (1.55, (10, 0, 0)), (1.75, (40, 0, 0)), (2.1, (10, 0, 0)), (3.0, Z))
    a.rot("tail1", (0, Z), (0.9, (-40, 0, 0)), (1.55, (-40, 20, 0)), (1.8, (30, 0, 0)), (3.0, Z))

    # spirits (phase 2, impact 0.8): sits back and howls at the sky; jade ghosts answer
    a = m.anim("spirits", 2.0)
    a.rot("body", (0, Z), (0.6, (-28, 0, 0)), (1.6, (-28, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.6, (0, -4, 6)), (1.6, (0, -4, 6)), (2.0, Z))
    for th in ("thigh_r", "thigh_l"):
        a.rot(th, (0, Z), (0.6, (-25, 0, 0)), (1.6, (-25, 0, 0)), (2.0, Z))
    for leg in ("leg_fr", "leg_fl"):
        a.rot(leg, (0, Z), (0.6, (20, 0, 0)), (1.6, (20, 0, 0)), (2.0, Z))
    a.rot("neck", (0, Z), (0.6, (-25, 0, 0)), (1.6, (-25, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.6, (-30, 0, 0)), (1.6, (-30, 0, 0)), (2.0, Z))
    a.rot("jaw", (0, Z), (0.6, (10, 0, 0)), (0.8, (50, 0, 0)), (1.5, (45, 0, 0)), (2.0, Z))
    a.scale("crest", (0, (1, 1, 1)), (0.8, (1.35, 1.3, 1)), (1.6, (1.35, 1.3, 1)), (2.0, (1, 1, 1)))
    a.rot("crest", (0, Z), (0.6, (50, 0, 0)), (1.6, (50, 0, 0)), (2.0, Z))
    a.rot("tail1", (0, Z), (0.6, (-30, 0, 0)), (1.6, (-30, 0, 0)), (2.0, Z))

    # maul (phase 2, impact 0.95): rears up tall on the hind legs, forepaws high, then hammers the floor
    a = m.anim("maul", 1.9)
    a.rot("body", (0, Z), (0.8, (-55, 0, 0)), (0.95, (-58, 0, 0)), (1.05, (12, 0, 0), "linear"), (1.4, (8, 0, 0)), (1.9, Z))
    a.pos("bone", (0, Z), (0.8, (0, 6, 8)), (0.95, (0, 7, 8)), (1.05, (0, -3, -6), "linear"), (1.4, (0, -3, -6)), (1.9, Z))
    for th, sh in (("thigh_r", "shin_r"), ("thigh_l", "shin_l")):
        a.rot(th, (0, Z), (0.8, (55, 0, 0)), (0.95, (55, 0, 0)), (1.05, (-10, 0, 0), "linear"), (1.9, Z))
        a.rot(sh, (0, Z), (0.8, (-20, 0, 0)), (1.05, (10, 0, 0)), (1.9, Z))
    for leg, fore, s in (("leg_fr", "fore_fr", 1), ("leg_fl", "fore_fl", -1)):
        a.rot(leg, (0, Z), (0.8, (-40, 0, s * 25)), (0.95, (-45, 0, s * 25)), (1.05, (-35, 0, 0), "linear"), (1.4, (-30, 0, 0)), (1.9, Z))
        a.rot(fore, (0, Z), (0.8, (-50, 0, 0)), (1.05, (0, 0, 0), "linear"), (1.9, Z))
    a.rot("neck", (0, Z), (0.8, (30, 0, 0)), (1.05, (-10, 0, 0)), (1.9, Z))
    a.rot("head", (0, Z), (0.8, (25, 0, 0)), (1.05, (10, 0, 0)), (1.9, Z))
    a.rot("jaw", (0, Z), (0.8, (35, 0, 0)), (1.4, (20, 0, 0)), (1.9, Z))
    a.rot("tail1", (0, Z), (0.8, (40, 0, 0)), (1.05, (-10, 0, 0)), (1.9, Z))

    # roar: phase change, head thrown up, crest blazing wide
    a = m.anim("roar", 2.4)
    a.rot("body", (0, Z), (0.5, (-18, 0, 0)), (1.9, (-18, 0, 0)), (2.4, Z))
    a.rot("neck", (0, Z), (0.5, (-20, 0, 0)), (1.9, (-20, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.5, (-25, 0, 0)), (1.9, (-25, 0, 0)), (2.4, Z))
    a.rot("jaw", (0, Z), (0.5, (55, 0, 0)), (1.9, (55, 0, 0)), (2.4, Z))
    a.scale("crest", (0, (1, 1, 1)), (0.5, (1.4, 1.35, 1)), (1.9, (1.4, 1.35, 1)), (2.4, (1, 1, 1)))
    a.rot("crest", (0, Z), (0.5, (45, 0, 0)), (1.9, (45, 0, 0)), (2.4, Z))
    a.rot("tail1", (0, Z), (0.5, (45, 0, 0)), (1.9, (45, 0, 0)), (2.4, Z))
    for leg in ("leg_fr", "leg_fl"):
        a.rot(leg, (0, Z), (0.5, (15, 0, 0)), (1.9, (15, 0, 0)), (2.4, Z))
    for th in ("thigh_r", "thigh_l"):
        a.rot(th, (0, Z), (0.5, (-10, 0, 0)), (1.9, (-10, 0, 0)), (2.4, Z))

    # stagger: posture broken, it slumps onto its side-chest, head down, tail limp
    a = m.anim("stagger", 2.5)
    a.pos("bone", (0, Z), (0.3, (0, -10, 0)), (2.1, (0, -10, 0)), (2.5, Z))
    a.rot("body", (0, Z), (0.3, (8, 0, 14)), (2.1, (8, 0, 14)), (2.5, Z))
    for leg in ("leg_fr", "leg_fl"):
        a.rot(leg, (0, Z), (0.3, (-60, 0, 0)), (2.1, (-60, 0, 0)), (2.5, Z))
    for fore in ("fore_fr", "fore_fl"):
        a.rot(fore, (0, Z), (0.3, (60, 0, 0)), (2.1, (60, 0, 0)), (2.5, Z))
    for th, sh in (("thigh_r", "shin_r"), ("thigh_l", "shin_l")):
        a.rot(th, (0, Z), (0.3, (-50, 0, 0)), (2.1, (-50, 0, 0)), (2.5, Z))
        a.rot(sh, (0, Z), (0.3, (50, 0, 0)), (2.1, (50, 0, 0)), (2.5, Z))
    a.rot("neck", (0, Z), (0.3, (30, 0, 0)), (2.1, (30, 0, 0)), (2.5, Z))
    a.rot("head", (0, Z), (0.3, (15, 0, 10)), (2.1, (15, 0, 10)), (2.5, Z))
    a.rot("tail1", (0, Z), (0.3, (-30, 0, 0)), (2.1, (-30, 0, 0)), (2.5, Z))
