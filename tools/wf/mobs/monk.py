"""Monk (Moine): the brothers and sisters of the Mountain Monastery (tools/wf/denizens.py), one texture variant per
role: scribe, healer, cook, warden (denizens.ROLE_ORDER["monk"]).

Silhouette idea: a bell. A shaved head over a heavy cowl, a long robe flaring to the ground with wide sleeves, a rope
belt with prayer beads, and the role's tool: the scribe's open book and quill, the healer's white robe and steaming
herb bowl, the cook's apron and ladle, the warden's wrapped fists and long iron-shod quarterstaff.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

ROLES = ["scribe", "healer", "cook", "warden"]

PAL = {
    "scribe": dict(robe=(118, 80, 52), robe2=(94, 62, 40), trim=(200, 170, 110), skin=(222, 180, 146), beads=(150, 40, 40)),
    "healer": dict(robe=(222, 220, 210), robe2=(190, 188, 180), trim=(80, 120, 190), skin=(206, 160, 128), beads=(70, 110, 180)),
    "cook": dict(robe=(130, 120, 104), robe2=(104, 96, 82), trim=(170, 150, 110), skin=(230, 186, 150), beads=(110, 80, 50)),
    "warden": dict(robe=(46, 62, 104), robe2=(34, 46, 80), trim=(200, 160, 70), skin=(196, 146, 112), beads=(200, 160, 70)),
}
ROPE = (196, 170, 120)
ROPE_D = (150, 126, 86)
PAGE = (240, 232, 210)
IRON = (140, 142, 150)


def build(variant=None):
    role = variant or ROLES[0]
    p = PAL[role]
    m = Model("monk", seed=339, shadow=0.5, variants=ROLES, walk_speed=1.0, walk_scale=1.0)
    robe = K.cloth(p["robe"], p["robe2"], seed=1, trim=p["trim"], trim_rows=(-1,))

    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("body", "bone", pivot=(0, -12, 0))
    m.part("head", "body", pivot=(0, -12, 0))
    m.part("arm_r", "body", pivot=(-5, -11, 0), rot=(0, 0, 6))
    m.part("arm_l", "body", pivot=(5, -11, 0), rot=(0, 0, -6))
    m.part("tool", "arm_r", pivot=(-0.5, 9.5, -0.5), rot=(-60, 0, 0))
    m.part("off", "arm_l", pivot=(0.5, 9.5, -0.5))
    m.part("robe", "body", pivot=(0, -1, 0))
    m.part("hood", "body", pivot=(0, -12, 2.5))

    # ------------------------------------------------------------------ legs: the robe's two halves, sandals
    for leg in ("leg_r", "leg_l"):
        def legp(f_, x, y, w, h):
            if y >= h - 1:
                return (110, 80, 50) if (x + y) % 2 else (150, 112, 70)          # sandal straps on bare feet
            if y == h - 2:
                return p["trim"]
            return K.cloth(p["robe"], p["robe2"], seed=2)(f_, x, y, w, h)
        m.box(leg, -2, 0, -2, 4, 12, 4, legp)

    # ------------------------------------------------------------------ robe body, flared skirt, rope belt
    def torso(f_, x, y, w, h):
        if role == "cook" and f_ == "front" and 1 <= x <= w - 2 and y >= 5:
            return (226, 220, 206) if (x + y) % 4 else (210, 204, 190)          # apron
        if f_ == "front" and x == w // 2 and y < 4:
            return mul(p["robe2"], 0.85)                                         # the robe's fold
        return robe(f_, x, y, w, h)
    m.box("body", -4, -12, -2.5, 8, 12, 5, torso)

    def skirt(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return None
        if role == "cook" and f_ == "front" and 1 <= x <= w - 2:
            return (226, 220, 206) if (x + y) % 4 else (210, 204, 190)
        return K.cloth(p["robe"], p["robe2"], seed=3, trim=p["trim"], trim_rows=(-1,))(f_, x, y, w, h)
    m.box("robe", -4.5, 0, -3, 9, 6, 6, skirt)
    m.box("robe", -5, 5, -3.5, 10, 6, 7, skirt)                                     # the bell of the robe

    def rope(f_, x, y, w, h):
        if f_ == "front" and x in (2, 3):
            return p["beads"]                                                    # the knot of beads
        return ROPE if (x + y) % 2 else ROPE_D
    m.box("body", -4.5, -3, -3, 9, 1, 6, rope)
    m.box("body", 1.5, -2, -3.2, 1, 5, 0, lambda f_, x, y, w, h: (p["beads"] if y % 2 else ROPE) if f_ in ("front", "back") else None)

    # the cowl lying on the shoulders
    def cowl(f_, x, y, w, h):
        if f_ == "bottom":
            return None
        if f_ == "top" and 2 <= x <= w - 3 and 2 <= y <= h - 3:
            return None                                                          # the neck hole
        return K.cloth(mul(p["robe"], 0.95), p["robe2"], seed=4)(f_, x, y, w, h)
    m.box("body", -4.5, -13, -3, 9, 3, 6, cowl)
    m.box("hood", -4, 0, 0, 8, 5, 1, K.cloth(mul(p["robe"], 0.9), p["robe2"], seed=5))   # the hood hanging behind
    m.box("hood", -2.5, 5, 0, 5, 2, 1, K.cloth(mul(p["robe"], 0.9), p["robe2"], seed=6))  # ... folded to a point

    # healer: a herb satchel; scribe: a scroll case; cook: a wooden spoon in the belt (one cube, painted per role)
    def hip(f_, x, y, w, h):
        if role == "healer":
            if f_ == "top":
                return (90, 170, 80)
            return K.leather((170, 140, 100), seed=6)(f_, x, y, w, h)
        if role == "scribe":
            return (140, 40, 36) if y % 3 else (200, 170, 90)
        return None
    m.box("body", 4, -4, -1.5, 2, 4, 3, hip)

    # ------------------------------------------------------------------ head: shaved scalp, kind face
    def face(f_, x, y, w, h):
        sk = p["skin"]
        if f_ == "top":
            return mix(sk, (120, 100, 90), 0.15) if (x + y) % 3 else sk          # shaved stubble
        if f_ == "bottom":
            return mul(sk, 0.82)
        hc = {"scribe": (92, 62, 40), "healer": (226, 226, 224), "cook": (176, 96, 50), "warden": (40, 34, 34)}[role]
        if f_ in ("left", "right", "back") and 1 <= y <= 3 or (f_ == "front" and y == 0 and x % 2 == 0):
            return hc if (x + y) % 3 else mul(hc, 0.85)                         # the tonsure ring
        if f_ in ("left", "right") and y == 4 and (x == 3 if f_ == "left" else x == w - 4):
            return mul(sk, 0.85)                                                # ear
        if f_ != "front":
            return K.skin(sk)(f_, x, y, w, h)
        if y == 3 and x in (1, 2, 5, 6):
            return mul(sk, 0.7) if role != "healer" else (230, 230, 230)        # brows (the healer is old)
        if y == 4 and x in (1, 6):
            return (240, 238, 232)
        if y == 4 and x in (2, 5):
            return (60, 50, 44)
        if y == 7 and 2 <= x <= 5 and role == "healer":
            return (230, 230, 230)                                              # a short white beard
        if y == 6 and x in (3, 4):
            return mul(sk, 0.8)
        if role == "warden" and y == 1 and x in (3, 4):
            return (60, 90, 170)                                                # a blue tattoo dot
        return K.skin(sk)(f_, x, y, w, h)
    m.box("head", -4, -8, -4, 8, 8, 8, face)
    m.box("head", -1, -4, -5, 2, 2, 1, mul(p["skin"], 0.94))

    # ------------------------------------------------------------------ wide sleeves, hands
    def sleeve(f_, x, y, w, h):
        if f_ == "top":
            return p["robe"]
        if y >= h - 2:
            if role == "warden":
                return (224, 214, 190) if (x + y) % 2 else (200, 190, 166)       # wrapped fists
            return K.skin(p["skin"])(f_, x, y, w, h)
        if y == h - 3:
            return p["trim"]
        return K.cloth(p["robe"], p["robe2"], seed=7)(f_, x, y, w, h)
    for arm in ("arm_r", "arm_l"):
        m.box(arm, -2, -1, -2, 4, 11, 4, sleeve)

        def cuff(f_, x, y, w, h):
            if f_ == "bottom":
                return None                                                     # open: the hand shows inside
            if f_ != "top" and y == h - 1:
                return p["trim"]
            return K.cloth(p["robe"], p["robe2"], seed=8)(f_, x, y, w, h)
        m.box(arm, -2.5, 5, -2.5, 5, 4, 5, cuff)                                  # the wide sleeve flaring open
    m.box("body", -3, -11, -2.8, 6, 6, 0, lambda f_, x, y, w, h: (p["beads"] if (x + y) % 2 else ROPE)
          if f_ in ("front", "back") and abs(abs(x - (w - 1) / 2) - (h - 1 - y) * ((w - 1) / 2) / (h - 1)) < 0.6 else None)

    # ---- right hand: quill (scribe), ladle (cook), quarterstaff (warden)
    def quill(f_, x, y, w, h):
        if role != "scribe":
            return None
        return (240, 240, 236) if y < h - 1 else (40, 40, 60)
    m.box("tool", -0.5, -4, -1, 0, 5, 2, quill)

    def ladle(f_, x, y, w, h):
        if role != "cook":
            return None
        return K.wood((170, 130, 80), (130, 96, 56), seed=8, vertical=False)(f_, x, y, w, h)
    m.box("tool", -0.5, -0.5, -7, 1, 1, 8, ladle)
    m.box("tool", -1.5, -1, -9, 3, 2, 2, K.role_only(role, "cook", K.wood((170, 130, 80), (130, 96, 56), seed=9)))

    def staff(f_, x, y, w, h):
        if role != "warden":
            return None
        along = y if f_ in ("left", "right", "top", "bottom") else x
        if f_ in ("front", "back"):
            return IRON
        if x < 2 or x > w - 3:
            return IRON                                                         # iron-shod ends
        if abs(x - w // 2) < 2:
            return (200, 60, 50) if x % 2 else (220, 190, 120)                  # the wrapped grip
        return K.wood((120, 80, 46), (86, 56, 30), seed=10, vertical=False)(f_, x, y, w, h)
    m.box("tool", -0.5, -0.5, -14, 1, 1, 26, staff)

    # ---- left hand: an open book (scribe), a steaming bowl (healer)
    def book(f_, x, y, w, h):
        if role != "scribe":
            return None
        if f_ == "top":
            return PAGE if x != w // 2 else (180, 160, 120)
        if f_ == "bottom":
            return (120, 40, 34)
        return (140, 46, 40)
    m.box("off", -2.5, 0, -3, 5, 1, 4, book)

    def bowl(f_, x, y, w, h):
        if role != "healer":
            return None
        if f_ == "top":
            return (110, 170, 90) if (x + y) % 2 else (150, 200, 120)          # the green brew
        return K.wood((160, 120, 76), (120, 86, 52), seed=11)(f_, x, y, w, h)
    m.box("off", -2, -1, -3, 4, 2, 4, bowl)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.rot("body", (0, (0, 0, 0)), (2.0, (1.5, 0, 0)), (4.0, (0, 0, 0)))
    idle.pos("body", (0, (0, 0, 0)), (2.0, (0, 0.35, 0)), (4.0, (0, 0, 0)))             # slow, calm breathing
    idle.rot("head", (0, (0, 0, 0)), (2.0, (4, 0, 0)), (2.8, (4, 8, 0)), (3.4, (2, 8, 0)), (4.0, (0, 0, 0)))
    idle.rot("robe", (0, (0, 0, 0)), (2.0, (-1.5, 0, 1)), (4.0, (0, 0, 0)))
    idle.rot("hood", (0, (0, 0, 0)), (2.0, (4, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, -2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.6, (-22, 0, 0)), (1.2, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.6, (22, 0, 0)), (1.2, (-22, 0, 0)))
    walk.rot("arm_r", (0, (-12, 0, 0)), (0.6, (12, 0, 0)), (1.2, (-12, 0, 0)))
    walk.rot("arm_l", (0, (12, 0, 0)), (0.6, (-12, 0, 0)), (1.2, (12, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.6, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.6, 0)), (1.2, (0, 0, 0)))
    walk.rot("body", (0, (2, -3, 0)), (0.6, (2, 3, 0)), (1.2, (2, -3, 0)))
    walk.rot("robe", (0, (8, 0, -3)), (0.3, (12, 0, 0)), (0.6, (8, 0, 3)), (0.9, (12, 0, 0)), (1.2, (8, 0, -3)))
    walk.rot("hood", (0, (10, 0, 0)), (0.3, (16, 0, 0)), (0.6, (10, 0, 0)), (0.9, (16, 0, 0)), (1.2, (10, 0, 0)))

    # greet: palms together and a slow bow
    a = m.anim("greet", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-70, -30, 0)), (1.2, (-70, -30, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-70, 30, 0)), (1.2, (-70, 30, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (1.0, (24, 0, 0)), (1.4, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (10, 0, 0)), (1.0, (10, 0, 0)), (1.6, (0, 0, 0)))

    # attack: the warden's staff sweep, wind-up 0.4 s, the blow lands at 0.5 s (10 ticks)
    a = m.anim("attack", 1.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-80, 70, 0)), (0.5, (-80, -50, 0), "linear"), (0.65, (-80, -60, 0)), (1.0, (0, 0, 0)))
    a.rot("tool", (0, (0, 0, 0)), (0.4, (60, 0, 0)), (0.5, (60, 0, 0)), (0.8, (40, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (0, 35, 0)), (0.5, (0, -30, 0), "linear"), (0.7, (0, -25, 0)), (1.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.4, (-20, 0, 0)), (0.7, (-20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-40, 0, -30)), (0.5, (-20, 0, -10), "linear"), (1.0, (0, 0, 0)))
    a.rot("robe", (0, (0, 0, 0)), (0.4, (0, -10, 6)), (0.5, (0, 14, -6), "linear"), (1.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, -1, 0)), (0.5, (0, 0, -1), "linear"), (1.0, (0, 0, 0)))

    # scribe: writes in the book held open in the other hand
    a = m.anim("scribe", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-55, 20, 0)), (1.3, (-55, 20, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-50, -25, 0)), (0.5, (-50, -10, 0)), (0.7, (-50, -25, 0)), (0.9, (-50, -10, 0)),
          (1.1, (-50, -25, 0)), (1.3, (-50, -10, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (22, 0, 0)), (1.3, (22, 0, 0)), (1.6, (0, 0, 0)))

    # brew: stirs the bowl, lifts it to sniff
    a = m.anim("brew", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.0, (-50, 0, 0)), (1.25, (-95, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-55, -20, 0)), (0.5, (-55, 10, 0)), (0.7, (-55, -20, 0)), (0.9, (-55, 10, 0)),
          (1.1, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (16, 0, 0)), (1.0, (16, 0, 0)), (1.25, (-6, 0, 0)), (1.6, (0, 0, 0)))

    # tend: the cook stirs a pot in front of it with the ladle, big slow circles
    a = m.anim("tend", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-40, 25, 0)), (0.6, (-40, -25, 0)), (0.9, (-40, 25, 0)), (1.2, (-40, -25, 0)),
          (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (14, 0, 0)), (1.2, (14, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (14, 0, 0)), (1.2, (14, 0, 0)), (1.6, (0, 0, 0)))
    return m
