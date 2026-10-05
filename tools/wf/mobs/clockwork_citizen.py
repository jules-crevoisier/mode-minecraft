"""Clockwork Citizen (Citoyen mécanique): the wound-up townsfolk of the Clockwork Citadel (tools/wf/denizens.py),
one texture variant per role: gearwright, mechanic, chronometrist, sentinel (denizens.ROLE_ORDER["clockwork_citizen"]).

Silhouette idea: a walking mantel clock. A clock-dial face with two lens eyes, a riveted boiler chest with a gauge, a
little smokestack and a big wind-up key on the back that never stops turning, piston legs and cog shoulders. The
gearwright wears a leather apron and swings a big wrench, the mechanic copper plates, goggles and an oil can, the
chronometrist a black top hat, a gold monocle and a pocket watch on a chain, the sentinel verdigris armour, a slit
visor and a piston fist.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B
from . import folkkit as K

ROLES = ["gearwright", "mechanic", "chronometrist", "sentinel"]

PAL = {
    "gearwright": dict(shell=B.BRASS, shell_d=B.BRASS_D, shell_l=B.BRASS_L, eye=B.AMBER, eye_l=B.AMBER_L),
    "mechanic": dict(shell=B.COPPER, shell_d=B.COPPER_D, shell_l=B.COPPER_L, eye=(120, 230, 255), eye_l=(220, 250, 255)),
    "chronometrist": dict(shell=(70, 64, 70), shell_d=(40, 36, 40), shell_l=(120, 112, 116), eye=(255, 220, 120),
                          eye_l=(255, 250, 220)),
    "sentinel": dict(shell=B.VERD, shell_d=B.VERD_D, shell_l=(130, 210, 196), eye=(255, 70, 46), eye_l=(255, 190, 150)),
}


def build(variant=None):
    role = variant or ROLES[0]
    p = PAL[role]
    shell = lambda seed, **kw: B.plate(p["shell"], p["shell_d"], p["shell_l"], seed=seed, **kw)  # noqa: E731
    m = Model("clockwork_citizen", seed=327, shadow=0.5, variants=ROLES, walk_speed=1.2, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("body", "bone", pivot=(0, -12, 0))
    m.part("head", "body", pivot=(0, -12, 0))
    m.part("key", "body", pivot=(0, -7, 4))
    m.part("arm_r", "body", pivot=(-5.5, -10.5, 0))
    m.part("arm_l", "body", pivot=(5.5, -10.5, 0))
    m.part("tool", "arm_r", pivot=(0, 9, -0.5), rot=(-70, 0, 0))
    m.part("off", "arm_l", pivot=(0, 9, 0))

    # ------------------------------------------------------------------ piston legs: iron thigh rod, shell shin, boot
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -1, 0, -1, 2, 6, 2, B.rod(B.IRON_L, 1))
        m.box(leg, -1.5, 5, -1.5, 3, 5, 3, shell(2))
        m.box(leg, -2, 10, -2.5, 4, 2, 4, B.iron(3))

    # ------------------------------------------------------------------ boiler chest
    def chest(f_, x, y, w, h):
        if f_ == "front" and role == "gearwright" and 1 <= x <= w - 2 and y >= 4:
            return K.leather((112, 72, 44), seed=4)(f_, x, y, w, h)              # leather apron
        if f_ == "front" and role == "chronometrist" and x in (w // 2 - 1, w // 2) and y >= 1:
            return (236, 230, 216) if x == w // 2 - 1 else (40, 36, 40)          # shirt front and tie
        return B.bands(p["shell"], p["shell_d"], every=3, seed=5)(f_, x, y, w, h)
    m.box("body", -4, -12, -3, 8, 10, 6, chest)
    m.box("body", -1.5, -10, -3.5, 3, 3, 1, B.gauge(), glow={"front": None, "*": None})
    m.box("body", -4.5, -2, -3.5, 9, 2, 7, B.iron(6, rivet_step=3))                # hip ring
    m.box("body", -3.5, 0, -2.5, 7, 1, 5, B.iron(7))

    def apron_skirt(f_, x, y, w, h):
        if role != "gearwright" or f_ != "front":
            return None
        return K.leather((112, 72, 44), seed=8)(f_, x, y, w, h)
    m.box("body", -3, -0.5, -3.6, 6, 5, 0, apron_skirt)

    # back: a small boiler with a grate, a smokestack
    m.box("body", -3, -11, 3, 6, 7, 2, B.iron(9))
    m.box("body", 1.5, -16, 3.2, 2, 6, 2, B.soot(B.IRON_L, 10))
    # the wind-up key
    m.box("key", -0.5, -0.5, 0, 1, 1, 3, B.rod(B.IRON_L, 11))
    m.box("key", -3.5, -3, 3, 7, 6, 0,
          B.key_bow(rows=["..###..", ".#####.", "##.#.##", "##.#.##", ".#####.", "..###.."]))

    # cog shoulders
    for sx in (-1, 1):
        m.box("body", 4 if sx > 0 else -5, -13, -2.5, 1, 5, 5,
              B.cog(p["shell"], p["shell_d"], teeth=8, hub=0.25, faces=("left", "right"), edges=True))

    # ------------------------------------------------------------------ the clock-dial head
    face_c = (232, 220, 190) if role != "sentinel" else (70, 80, 76)

    def dial(f_, x, y, w, h):
        """A big, simple clock face: a lit bezel, cream enamel, three hour ticks (12, 3, 9)."""
        if x in (0, w - 1) or y in (0, h - 1):
            return p["shell_l"] if y == 0 else p["shell"]
        if (x, y) in ((3, 1), (4, 1)):
            return B.IRON
        return mul(face_c, 1.04 - 0.1 * y / h)
    eyes = {(1, 2), (2, 2), (1, 3), (2, 3), (5, 2), (6, 2), (5, 3), (6, 3)}

    def head(f_, x, y, w, h):
        if f_ == "front":
            if (x, y) in eyes:
                return p["eye_l"] if y == 2 and x in (1, 5) else p["eye"]
            if role == "chronometrist" and (x, y) in ((4, 1), (7, 1), (4, 4), (7, 4), (4, 2), (4, 3), (7, 2), (7, 3),
                                                      (5, 1), (6, 1), (5, 4), (6, 4)):
                return (240, 200, 90)                                              # the gold monocle
            if (x, y) in ((3, 5), (4, 5)):
                return p["shell_d"]                                                # a mouth grille
            return dial(f_, x, y, w, h)
        return shell(12)(f_, x, y, w, h)

    def head_glow(f_, x, y, w, h):
        if f_ == "front" and (x, y) in eyes:
            return p["eye_l"] if y == 2 and x in (1, 5) else p["eye"]
        return None
    m.box("head", -4, -8, -3, 8, 8, 6, head, glow=head_glow)
    # antenna / ear bolts
    for sx in (-1, 1):
        m.box("head", 4 if sx > 0 else -5, -6, -1, 1, 3, 2, B.iron(13))

    # ---- headgear
    def hat_brim(f_, x, y, w, h):
        if role == "chronometrist":
            return (34, 30, 34) if f_ != "top" else (50, 46, 50)
        if role == "sentinel":
            return B.plate(B.VERD, B.VERD_D, (130, 210, 196), seed=14)(f_, x, y, w, h)
        if role == "mechanic":
            if f_ in ("top", "bottom"):
                return None
            if f_ == "front" and x in (2, 3, 6, 7):
                return (120, 230, 255) if x in (3, 6) else B.BRASS                  # goggles
            return (60, 44, 32)
        return None
    m.box("head", -4.5, -9, -3.5, 9, 1, 7, hat_brim)

    def hat_crown(f_, x, y, w, h):
        if role == "chronometrist":
            if f_ != "top" and y == h - 2:
                return (150, 30, 40)                                               # the hat band
            return (34, 30, 34) if (x + y) % 5 else (48, 44, 48)
        if role == "sentinel":
            if f_ == "front" and y == h - 1 and 1 <= x <= w - 2:
                return (255, 70, 46)                                               # the visor slit
            return B.plate(B.VERD, B.VERD_D, (130, 210, 196), seed=15)(f_, x, y, w, h)
        return None
    m.box("head", -3, -14, -2.5, 6, 5, 5, hat_crown,
          glow=K.role_only(role, "sentinel", {"front": lambda f_, x, y, w, h: (255, 120, 80) if y == h - 1 and
                                              1 <= x <= w - 2 else None, "*": None}))

    # ------------------------------------------------------------------ arms: iron rods, shell forearms, clamp hands
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        m.box(arm, -1, -1, -1, 2, 5, 2, B.rod(B.IRON_L, 17))
        m.box(arm, -1.5, 3.5, -1.5, 3, 5, 3, shell(18))
        m.box(arm, -1, 8, -1, 2, 2, 2, B.iron(19))

    def fist(f_, x, y, w, h):
        if role != "sentinel":
            return None
        if f_ == "front" and y % 2 == 1:
            return B.IRON_D                                                        # finger plates
        return B.plate(B.VERD, B.VERD_D, (130, 210, 196), seed=20)(f_, x, y, w, h)
    m.box("arm_r", -2.5, 6.5, -2.5, 5, 5, 5, fist)

    def piston(f_, x, y, w, h):
        if role != "sentinel":
            return None
        return B.rod(B.IRON_L, 21)(f_, x, y, w, h)
    m.box("arm_r", -0.5, 0, 1.5, 1, 7, 1, piston)

    # ---- right hand: wrench (gearwright), oil can (mechanic)
    def wrench(f_, x, y, w, h):
        if role != "gearwright":
            return None
        return B.rod(B.IRON_L, 22)(f_, x, y, w, h)
    m.box("tool", -0.5, -0.5, -7, 1, 1, 8, wrench)

    def jaw(f_, x, y, w, h):
        if role != "gearwright":
            return None
        if f_ in ("left", "right") and x == 0 and 1 <= y <= h - 2:
            return None                                                            # the open jaw
        return B.iron(23)(f_, x, y, w, h)
    m.box("tool", -0.5, -1.5, -9, 1, 3, 2, jaw)

    def can(f_, x, y, w, h):
        if role != "mechanic":
            return None
        if f_ == "top":
            return B.COPPER_D
        return B.bands(B.COPPER, B.COPPER_D, every=2, seed=24)(f_, x, y, w, h)
    m.box("tool", -1.5, -1.5, -3.5, 3, 3, 3, can)
    m.box("tool", -0.5, -2.5, -6.5, 1, 1, 3, K.role_only(role, "mechanic", B.rod(B.COPPER_L, 25)))

    # ---- left hand: the chronometrist's pocket watch
    def watch(f_, x, y, w, h):
        if role != "chronometrist":
            return None
        if f_ in ("left", "right"):
            return B.dial(rim=(230, 190, 80), numerals=4)("front", x, y, w, h)
        return (230, 190, 80)
    m.box("off", -0.5, 0, -1.5, 1, 3, 3, watch)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.0)
    idle.rot("key", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 360), "linear"))
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, 0.3, 0)), (2.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.9, (0, 0, 0)), (1.0, (0, 0, 6), "linear"), (1.1, (0, 0, 0), "linear"),
             (2.0, (0, 0, 0)))                                                       # a tick of the head
    idle.rot("arm_r", (0, (0, 0, 0)), (1.0, (-3, 0, 2)), (2.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.0, (-3, 0, -2)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("leg_r", (0, (28, 0, 0), "linear"), (0.5, (-28, 0, 0), "linear"), (1.0, (28, 0, 0), "linear"))
    walk.rot("leg_l", (0, (-28, 0, 0), "linear"), (0.5, (28, 0, 0), "linear"), (1.0, (-28, 0, 0), "linear"))
    walk.rot("arm_r", (0, (-22, 0, 0), "linear"), (0.5, (22, 0, 0), "linear"), (1.0, (-22, 0, 0), "linear"))
    walk.rot("arm_l", (0, (22, 0, 0), "linear"), (0.5, (-22, 0, 0), "linear"), (1.0, (22, 0, 0), "linear"))
    walk.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.6, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.6, 0)), (1.0, (0, 0, 0)))
    walk.rot("key", (0, (0, 0, 0), "linear"), (1.0, (0, 0, 360), "linear"))

    # greet: tips its hat (raises the right hand to the brim), the head ticks
    a = m.anim("greet", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-150, 0, -20)), (0.8, (-150, 0, -20)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (12, 0, 0), "linear"), (0.5, (12, 0, 8), "linear"), (0.7, (12, 0, -8), "linear"),
          (0.9, (0, 0, 0)), (1.2, (0, 0, 0)))

    # attack: the piston punch (wind-up 0.4 s, the fist lands at 0.5 s = 10 ticks)
    a = m.anim("attack", 1.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-60, 30, 0)), (0.5, (-95, -5, 0), "linear"), (0.7, (-90, 0, 0)), (1.0, (0, 0, 0)))
    a.pos("arm_r", (0, (0, 0, 0)), (0.4, (0, 0, 2)), (0.5, (0, 0, -3), "linear"), (0.7, (0, 0, -2)), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (0, 25, 0)), (0.5, (6, -20, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (1.0, (0, 0, 720), "linear"))

    # tinker: works a bolt in front of it with the tool, sparks at each turn
    a = m.anim("tinker", 1.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-70, 0, 0)), (0.45, (-70, 0, -40)), (0.65, (-70, 0, 0)), (0.85, (-70, 0, -40)),
          (1.05, (-70, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-55, 0, 10)), (1.05, (-55, 0, 10)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.25, (18, 0, 0)), (1.05, (18, 0, 0)), (1.4, (0, 0, 0)))

    # wind: reaches over its shoulder and winds its own key
    a = m.anim("wind", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-200, 0, -30)), (1.2, (-200, 0, -30)), (1.6, (0, 0, 0)))
    a.rot("key", (0, (0, 0, 0), "linear"), (0.3, (0, 0, 0), "linear"), (1.2, (0, 0, -1080), "linear"), (1.6, (0, 0, -1080), "linear"))
    a.rot("head", (0, (0, 0, 0)), (0.3, (0, 25, 0)), (1.2, (0, 25, 0)), (1.6, (0, 0, 0)))
    return m
