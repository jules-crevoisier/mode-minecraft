"""Sylvan (Sylvain): the tall forest folk of the Sylvan Palace and the Hollow Giant Tree (tools/wf/denizens.py), one
texture variant per role: gardener, herbalist, woodwright, warden (same order as denizens.ROLE_ORDER["sylvan"]).

Silhouette idea: a willow. Taller and slimmer than a villager, long pointed ears swept back, hair to the waist, a
cape of overlapping leaves that sways behind them and softly glowing eyes. The gardener wears a flower crown and a
sickle, the herbalist a lilac hood, a herb satchel and a glowing vial, the woodwright a leather apron and a carving
mallet, the warden bark-plate armour, a green hood and a longbow.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

ROLES = ["gardener", "herbalist", "woodwright", "warden"]

PAL = {
    "gardener": dict(tunic=(96, 150, 70), tunic2=(74, 120, 54), trim=(232, 210, 120), skin=(236, 214, 186),
                     hair=(236, 206, 120), cape=(84, 152, 70), cape2=(56, 112, 50), boots=(110, 80, 50),
                     belt=(120, 86, 52)),
    "herbalist": dict(tunic=(150, 120, 186), tunic2=(118, 92, 154), trim=(226, 226, 240), skin=(232, 208, 196),
                      hair=(226, 230, 236), cape=(110, 140, 96), cape2=(80, 108, 70), boots=(90, 70, 80),
                      belt=(96, 72, 56)),
    "woodwright": dict(tunic=(140, 104, 66), tunic2=(112, 80, 50), trim=(196, 160, 96), skin=(218, 186, 150),
                       hair=(150, 72, 40), cape=(170, 120, 50), cape2=(132, 86, 36), boots=(84, 60, 38),
                       belt=(70, 50, 32)),
    "warden": dict(tunic=(60, 92, 60), tunic2=(44, 70, 46), trim=(170, 200, 120), skin=(224, 204, 180),
                   hair=(40, 56, 46), cape=(46, 96, 56), cape2=(30, 70, 40), boots=(64, 50, 36),
                   belt=(80, 58, 36)),
}
EYE = (110, 236, 200)
EYE_L = (220, 255, 240)
BARK = (110, 82, 56)
BARK_D = (74, 54, 38)
GLOWWOOD = (178, 206, 200)
GLOWWOOD_D = (120, 156, 156)
VIAL = (120, 240, 200)
STEEL = (196, 200, 206)


def leafy(base, dark, seed=0, ragged=True):
    """Overlapping leaves: rows of leaf shapes with a light vein, the lower edge cut into points."""
    def f(face, x, y, w, h):
        if ragged and face in ("front", "back", "left", "right") and y == h - 1 and (x + seed) % 2:
            return None
        row = y // 3
        lx = (x + row * 2 + seed) % 4
        c = base if lx in (1, 2) else dark
        if lx == 1 and y % 3 == 1:
            c = mix(base, (230, 250, 190), 0.35)       # vein highlight
        if K.h(x, y, seed) % 19 == 0:
            c = mix(c, (220, 160, 70), 0.4)             # a turning leaf
        return c
    return f


def bark_plate(seed=0):
    def f(face, x, y, w, h):
        if face == "bottom":
            return BARK_D
        c = BARK if (x + K.h(x // 2, 0, seed)) % 3 else BARK_D
        if y % 4 == 0 and face != "top":
            c = mix(c, (150, 120, 80), 0.5)
        return c
    return f


def build(variant=None):
    role = variant or ROLES[0]
    p = PAL[role]
    m = Model("sylvan", seed=313, shadow=0.45, variants=ROLES, walk_speed=1.0, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-1.7, -14, 0))
    m.part("leg_l", "bone", pivot=(1.7, -14, 0))
    m.part("body", "bone", pivot=(0, -14, 0))
    m.part("head", "body", pivot=(0, -12, 0))
    m.part("ear_r", "head", pivot=(-3.5, -4, 0.5), rot=(0, -35, -15))
    m.part("ear_l", "head", pivot=(3.5, -4, 0.5), rot=(0, 35, 15))
    m.part("cape", "body", pivot=(0, -12, 2.2), rot=(6, 0, 0))
    m.part("arm_r", "body", pivot=(-4.5, -11, 0), rot=(0, 0, 4))
    m.part("arm_l", "body", pivot=(4.5, -11, 0), rot=(0, 0, -4))
    m.part("tool", "arm_r", pivot=(0, 10, -0.5), rot=(-60, 0, 0))
    m.part("off", "arm_l", pivot=(0, 10, 0))

    tunic = K.cloth(p["tunic"], p["tunic2"], seed=1, trim=p["trim"], trim_rows=(0, -1))

    # ------------------------------------------------------------------ long legs, soft boots
    for leg in ("leg_r", "leg_l"):
        def legp(f_, x, y, w, h):
            if y >= h - 5:
                return K.leather(p["boots"], seed=2)(f_, x, y, w, h) if y != h - 5 else mul(p["boots"], 1.2)
            if role == "warden" and f_ == "front" and 2 <= y <= 5:
                return bark_plate(3)(f_, x, y, w, h)                      # greaves
            return K.cloth(mul(p["tunic2"], 0.85), mul(p["tunic2"], 0.7), seed=3)(f_, x, y, w, h)
        m.box(leg, -1.5, 0, -1.5, 3, 14, 3, legp)

    # ------------------------------------------------------------------ slim torso, long tunic skirt, belt
    def torso(f_, x, y, w, h):
        if role == "warden" and f_ in ("front", "back") and 1 <= y <= 7:
            return bark_plate(4)(f_, x, y, w, h)                          # bark cuirass
        if role == "woodwright" and f_ == "front" and 1 <= x <= w - 2 and y >= 4:
            return K.leather((120, 84, 50), seed=5)(f_, x, y, w, h)        # apron
        if role == "herbalist" and f_ == "front" and x == w // 2:
            return p["trim"]                                               # robe opening
        return tunic(f_, x, y, w, h)
    m.box("body", -3.5, -12, -2, 7, 12, 4, torso)

    def skirt(f_, x, y, w, h):
        if f_ == "bottom":
            return None
        if f_ in ("front", "back") and y == h - 1 and x % 3 == 1:
            return None                                                    # leaf-cut hem
        if role == "woodwright" and f_ == "front" and 1 <= x <= w - 2:
            return K.leather((120, 84, 50), seed=6)(f_, x, y, w, h)
        return K.cloth(p["tunic"], p["tunic2"], seed=7, trim=p["trim"], trim_rows=(-2,))(f_, x, y, w, h)
    m.box("body", -4, -1, -2.5, 8, 6, 5, skirt)

    def belt(f_, x, y, w, h):
        if f_ == "front" and x == w // 2:
            return (120, 220, 170) if role != "woodwright" else (200, 170, 100)     # a leaf-green clasp
        return p["belt"] if (x + y) % 3 else mul(p["belt"], 1.2)
    m.box("body", -4, -2, -2.5, 8, 1, 5, belt)

    # satchel on the right hip (herbalist: herbs; gardener: seeds) / quiver on the back (warden)
    def satchel(f_, x, y, w, h):
        if role not in ("herbalist", "gardener"):
            return None
        if f_ == "top":
            return (90, 170, 70) if (x + y) % 2 else (200, 90, 140)        # herbs and petals sticking out
        return K.leather((150, 112, 70), seed=8)(f_, x, y, w, h)
    m.box("body", -5.5, -3, -2, 2, 4, 4, satchel)

    def quiver(f_, x, y, w, h):
        if role != "warden":
            return None
        if f_ == "top":
            return (236, 236, 236) if (x + y) % 2 else (200, 60, 50)       # fletchings
        return K.leather((96, 66, 40), seed=9, stitch=(160, 130, 80))(f_, x, y, w, h)
    m.part("quiver", "body", pivot=(0, -6, 2), rot=(0, 0, -24))
    m.box("quiver", -1.5, -8, 0, 3, 10, 2, quiver)

    # pauldrons: bark (warden), else none
    for sx in (-1, 1):
        m.box("body", 2.5 if sx > 0 else -6.5, -12.5, -2.5, 4, 2, 5,
              lambda f_, x, y, w, h: bark_plate(10)(f_, x, y, w, h) if role == "warden" else None)

    # ------------------------------------------------------------------ cape of leaves
    m.box("cape", -4, 0, 0, 8, 15, 1, {"*": leafy(p["cape"], p["cape2"], seed=11), "top": p["cape"],
                                       "bottom": None})
    m.box("cape", -4.5, -0.5, -0.5, 9, 2, 2, leafy(mix(p["cape"], (255, 255, 255), 0.1), p["cape2"], 12, ragged=False))

    # ------------------------------------------------------------------ head: narrow face, glowing eyes, long hair
    hairp = K.hair(p["hair"], 13)

    def face(f_, x, y, w, h):
        sk = p["skin"]
        if f_ == "top":
            return hairp(f_, x, y, w, h)
        if f_ == "back":
            return hairp(f_, x, y, w, h)
        if f_ in ("left", "right"):
            if y < 2 or x >= w - 3 if f_ == "left" else (y < 2 or x <= 2):
                return hairp(f_, x, y, w, h)
            return K.skin(sk)(f_, x, y, w, h)
        if f_ == "bottom":
            return mul(sk, 0.85)
        if y < 2 or (y < 4 and x in (0, w - 1)):
            return hairp(f_, x, y, w, h)                                   # fringe swept to the sides
        if y == 3 and x in (1, 2, 4, 5):
            return mul(p["hair"], 0.8) if x in (1, 5) else sk              # thin brows
        if y == 4 and x in (1, 5):
            return EYE
        if y == 4 and x in (2, 4):
            return (40, 60, 56)
        if y == 6 and x == 3:
            return mul(sk, 0.86)                                           # small nose shadow
        if y == 7 and x in (2, 4):
            return mul(sk, 0.9)
        return K.skin(sk)(f_, x, y, w, h)

    def eyes(f_, x, y, w, h):
        return EYE_L if f_ == "front" and y == 4 and x in (1, 5) else None
    m.box("head", -3.5, -8, -3.5, 7, 8, 7, face, glow=eyes)
    m.box("head", -3.5, -7, 3.5, 7, 14, 1, {"*": hairp, "front": hairp, "bottom": None,
                                             "back": lambda f_, x, y, w, h: None if y == h - 1 and x % 2 else hairp(f_, x, y, w, h)})

    for side, sx in (("r", -1), ("l", 1)):
        m.box(f"ear_{side}", 0 if sx > 0 else -4, -1, -0.5, 4, 2, 1,
              lambda f_, x, y, w, h, sx=sx: None if (y == 0 and (x >= w - 1 if sx > 0 else x == 0)) else
              mul(p["skin"], 0.95 if f_ != "top" else 1.05))

    def crown(f_, x, y, w, h):
        if role == "gardener":
            if f_ in ("top", "bottom") and 1 <= x <= w - 2 and 1 <= y <= w - 2:
                return None
            r = K.h(x, y, 14) % 5
            return [(80, 160, 70), (240, 120, 160), (80, 160, 70), (250, 230, 110), (110, 190, 90)][r]
        if role == "herbalist":
            return None
        if role == "woodwright":
            if f_ in ("top", "bottom"):
                return None
            return (196, 150, 70) if f_ == "front" and x == w // 2 else (120, 84, 50)   # a leather headband
        if f_ in ("top", "bottom"):
            return None
        return (120, 220, 170) if f_ == "front" and x == w // 2 else GLOWWOOD_D          # a glowwood circlet
    m.box("head", -4, -7, -4, 8, 1, 8, crown, glow=K.role_only(role, "warden", {"front": lambda f_, x, y, w, h:
                                                                                  (160, 255, 210) if x == w // 2 else None,
                                                                                  "*": None}))

    def hood(f_, x, y, w, h):
        if role not in ("herbalist", "warden"):
            return None
        col, col2 = ((150, 120, 186), (118, 92, 154)) if role == "herbalist" else ((54, 96, 56), (40, 72, 42))
        if f_ == "front" and 1 <= x <= w - 2 and y >= 2:
            return None                                                    # the face shows
        if f_ == "bottom":
            return None
        return K.cloth(col, col2, seed=15)(f_, x, y, w, h)
    m.box("head", -4, -8.5, -4, 8, 9, 8, hood)

    # ------------------------------------------------------------------ slender arms
    def sleeve(f_, x, y, w, h):
        if f_ == "top":
            return p["tunic"]
        if y >= h - 2:
            return K.skin(p["skin"])(f_, x, y, w, h)
        if role == "warden" and y >= h - 6:
            return K.leather((96, 66, 40), seed=16)(f_, x, y, w, h)          # bracers
        if y == h - 3:
            return p["trim"]
        return K.cloth(p["tunic"], p["tunic2"], seed=17)(f_, x, y, w, h)
    for arm in ("arm_r", "arm_l"):
        m.box(arm, -1, -1, -1, 2, 12, 2, sleeve)

    # ---- right hand: sickle (gardener), mallet (woodwright), hunting knife (warden), nothing (herbalist)
    handle = K.wood((120, 84, 50), (84, 58, 36), seed=18, vertical=False)
    m.box("tool", -0.5, -0.5, -5, 1, 1, 6, K.role_only(role, ("gardener", "woodwright", "warden"), handle))

    def sickle(f_, x, y, w, h):
        if role != "gardener":
            return None
        if f_ in ("left", "right") and (x - 1) ** 2 + (y - 3) ** 2 < 4.5 and not ((x - 2) ** 2 + (y - 4) ** 2 < 2.5):
            return STEEL if y < 3 else mix(STEEL, (120, 124, 130), 0.4)
        return None
    m.box("tool", 0, -4, -8, 0, 5, 4, sickle)

    def mallet(f_, x, y, w, h):
        if role != "woodwright":
            return None
        return K.wood(GLOWWOOD, GLOWWOOD_D, seed=19)(f_, x, y, w, h) if f_ not in ("front", "back") else BARK
    m.box("tool", -1.5, -1.5, -8, 3, 3, 3, mallet)

    def knife(f_, x, y, w, h):
        if role != "warden":
            return None
        return STEEL if f_ in ("left", "right", "top") else mul(STEEL, 0.8)
    m.box("tool", -0.5, -0.5, -9, 1, 1, 4, knife)

    # ---- left hand: longbow (warden), glowing vial (herbalist)
    m.part("bow_top", "off", pivot=(0, -1, 0), rot=(-18, 0, 0))
    m.part("bow_bot", "off", pivot=(0, 1, 0), rot=(18, 0, 0))
    stave = K.role_only(role, "warden", K.wood(GLOWWOOD, GLOWWOOD_D, seed=20))
    grip = K.role_only(role, "warden", K.leather((96, 66, 40), seed=21))
    m.box("off", -0.5, -1.5, -1.5, 1, 3, 1, grip)
    m.box("bow_top", -0.5, -9, -1.5, 1, 8, 1, stave)
    m.box("bow_bot", -0.5, 1, -1.5, 1, 8, 1, stave)

    def vial(f_, x, y, w, h):
        if role != "herbalist":
            return None
        if y == 0:
            return (150, 110, 70)                                          # cork
        return VIAL if (x + y) % 2 else mix(VIAL, (255, 255, 255), 0.4)
    m.box("off", -1, -1, -1, 2, 3, 2, vial, glow=K.role_only(role, "herbalist",
                                                             lambda f_, x, y, w, h: None if y == 0 else VIAL))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.rot("body", (0, (0, 0, 0)), (2.0, (1, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.3, (5, 0, 2)), (2.6, (2, 0, -2)), (4.0, (0, 0, 0)))
    idle.rot("ear_r", (0, (0, 0, 0)), (2.9, (0, 0, 0)), (3.0, (0, 8, -6)), (3.15, (0, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("ear_l", (0, (0, 0, 0)), (2.9, (0, 0, 0)), (3.0, (0, -8, 6)), (3.15, (0, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, -2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (26, 0, 0)), (0.6, (-26, 0, 0)), (1.2, (26, 0, 0)))
    walk.rot("leg_l", (0, (-26, 0, 0)), (0.6, (26, 0, 0)), (1.2, (-26, 0, 0)))
    walk.rot("arm_r", (0, (-18, 0, 0)), (0.6, (18, 0, 0)), (1.2, (-18, 0, 0)))
    walk.rot("arm_l", (0, (18, 0, 0)), (0.6, (-18, 0, 0)), (1.2, (18, 0, 0)))
    walk.rot("cape", (0, (14, 0, 0)), (0.6, (20, 0, 0)), (1.2, (14, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.5, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.5, 0)), (1.2, (0, 0, 0)))

    # greet: a hand on the heart and a graceful bow
    a = m.anim("greet", 1.6)
    a.rot("body", (0, (0, 0, 0)), (0.4, (22, 0, 0)), (1.1, (22, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-70, 0, 40)), (1.1, (-70, 0, 40)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-10, 0, 30)), (1.1, (-10, 0, 30)), (1.6, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.4, (-14, 0, 0)), (1.1, (-14, 0, 0)), (1.6, (0, 0, 0)))

    # attack (the warden's shot): raise the bow, draw the string to the cheek, release at 0.75 s (15 ticks)
    a = m.anim("attack", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-90, -10, 0)), (0.75, (-90, -10, 0)), (0.85, (-86, -10, 0)), (1.2, (0, 0, 0)))
    a.rot("off", (0, (0, 0, 0)), (0.3, (90, 0, 0)), (0.85, (90, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-90, 20, 0)), (0.7, (-90, 60, 0)), (0.75, (-90, 60, 0)),
          (0.8, (-80, 80, 10), "linear"), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (0, -20, 0)), (0.75, (0, -24, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (0, 20, 0)), (0.75, (0, 24, 0)), (1.2, (0, 0, 0)))

    # tend: kneels, pats the soil twice, rises
    a = m.anim("tend", 2.0)
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, -5, 0)), (1.6, (0, -5, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (-80, 0, 0)), (1.6, (-80, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.4, (10, 0, 0)), (1.6, (10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (1.6, (30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-50, 0, 0)), (0.7, (-20, 0, 0), "linear"), (0.9, (-50, 0, 0)),
          (1.1, (-20, 0, 0), "linear"), (1.6, (-30, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.6, (-40, 0, 0)), (2.0, (0, 0, 0)))

    # brew: holds the vial up to the light and swirls it
    a = m.anim("brew", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-130, 0, 10)), (0.6, (-130, 0, 30)), (0.9, (-130, 0, -5)),
          (1.2, (-130, 0, 30)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-16, 10, 0)), (1.2, (-16, 10, 0)), (1.6, (0, 0, 0)))

    # carve: mallet taps on a peg held in the other hand
    a = m.anim("carve", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (-60, 0, 20)), (1.0, (-60, 0, 20)), (1.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (-80, -20, 0)), (0.35, (-50, -20, 0), "linear"), (0.55, (-80, -20, 0)),
          (0.7, (-50, -20, 0), "linear"), (0.9, (-80, -20, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.2, (20, 0, 0)), (1.0, (20, 0, 0)), (1.2, (0, 0, 0)))
    return m
