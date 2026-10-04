"""The Grand Clockmaker (Le Grand Horloger): champion of the Clockwork Citadel, about 4.4 blocks tall.

Silhouette idea: a Victorian automaton gentleman with a clock for a heart. Long stilt legs on cog knees, a brass
tailcoat, a broad chest that IS a clock face (cream dial, aether hour marks, two iron hands that never stop
turning), a brass mask with a waxed moustache and one glowing monocle under a tall top hat, and two wings made of
great spinning cogs on iron spars. In his right hand a long cane ending in a heavy pendulum bob; on his left wrist
a pocket watch on a chain.
"""
from ..models import Model
from ..texgen import mix, mul
from . import brasswork as B


def coat(seed=0):
    """Tailcoat cloth: mahogany with a brass piping on the edges and faint vertical folds."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mul(B.MAHOGANY, 0.8)
        if x in (0, w - 1) or y == h - 1:
            return B.BRASS_D
        k = 1.0 + (0.08 if x % 3 == 0 else 0.0) - 0.2 * (y / max(1, h)) + (B.n(x, y, seed) - 0.5) * 0.05
        return mul(B.MAHOGANY, k)
    return f


def moustache(f, x, y, w, h):
    """A waxed moustache curling up at both ends (pixel art on a 10 x 3 x 1 cube)."""
    rows = ["#........#",
            "##.####.##",
            ".###..###."]
    if f in ("front", "back"):
        xx = x if f == "front" else w - 1 - x
        return (B.IRON_L if y == 0 else B.SOOT if y == 2 else B.IRON_D) if rows[y][xx] == "#" else None
    if f == "top":
        return B.IRON if rows[0][x] == "#" or rows[1][x] == "#" else None
    if f == "bottom":
        return B.SOOT if rows[2][x] == "#" else None
    return B.IRON_D if rows[y][0] == "#" else None


def build():
    m = Model("grand_clockmaker", seed=83, shadow=1.3, walk_speed=0.8, walk_scale=1.0)

    m.part("bone", pivot=(0, 24, 0))
    m.part("pelvis", "bone", pivot=(0, -30, 0))
    m.part("waist", "pelvis", pivot=(0, -3, 0))
    m.part("chest", "waist", pivot=(0, -5, 0))
    m.part("head", "chest", pivot=(0, -16, -1))
    m.part("hand_min", "chest", pivot=(0, -8, -6), rot=(0, 0, 60))
    m.part("hand_hour", "chest", pivot=(0, -8, -6), rot=(0, 0, -60))
    m.part("tails", "pelvis", pivot=(0, -1, 3), rot=(8, 0, 0))
    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"thigh_{side}", "pelvis", pivot=(3.5 * sx, 0, 0))
        m.part(f"shin_{side}", f"thigh_{side}", pivot=(0, 14, 0))
        m.part(f"arm_{side}", "chest", pivot=(9.5 * sx, -14, 0), rot=(0, 0, 8 * sx))
        m.part(f"fore_{side}", f"arm_{side}", pivot=(0, 11, 0), rot=(-14, 0, 0))
        m.part(f"wing_{side}", "chest", pivot=(4 * sx, -13, 5), rot=(0, -16 * sx, -38 * sx))
        for k, d in enumerate((8, 18, 26)):
            m.part(f"cog_{side}{k}", f"wing_{side}", pivot=(d * sx, 0, 1.5 + (k % 2) * 1.2))
    m.part("cane", "fore_r", pivot=(0, 12.5, 0))
    m.part("watch", "fore_l", pivot=(0, 11, -1))

    # ---- legs: iron stilts, cog knees, brass shins with copper piston sleeves, spatted boots
    for side, sx in (("r", -1), ("l", 1)):
        th, sh = f"thigh_{side}", f"shin_{side}"
        m.box(th, -2, -1, -2, 4, 4, 4, B.iron(1))                                        # hip joint
        m.box(th, -1.5, 3, -1.5, 3, 11, 3, B.rod(B.IRON, 2))
        m.box(th, (1.5 if sx > 0 else -2.5), 10, -3, 1, 6, 6,
              B.cog(B.BRASS, B.BRASS_D, teeth=8, hub=0.2, faces=("left", "right"), edges=True))  # knee cog
        m.box(sh, -1, 0, -1, 2, 13, 2, B.rod(B.BRASS, 3))
        m.box(sh, -1.5, 3, -1.5, 3, 5, 3, B.bands(B.COPPER, B.COPPER_D, every=2, seed=4))
        m.box(sh, -2, 13, -4, 4, 3, 7, B.iron(5))
        m.box(sh, -2.5, 12, -2.5, 5, 2, 5, B.plate(B.CREAM, B.CREAM_D, seed=6))           # spats
        m.box(sh, -1.5, 14, -5, 3, 2, 1, B.BRASS)                                          # toe cap

    # ---- pelvis, waist and tailcoat
    m.box("pelvis", -5, -3, -3, 10, 4, 6, B.iron(7, rivet_step=3))
    m.box("waist", -3, -5, -2.5, 6, 5, 5, B.bands(B.IRON, B.BRASS_D, every=2, seed=8))
    m.box("tails", -5, 0, 0, 4, 18, 1, coat(9))
    m.box("tails", 1, 0, 0, 4, 18, 1, coat(10))
    m.box("tails", -5.5, -1, -0.5, 11, 2, 2, B.brass(11))

    # ---- the clock chest: brass case, cream dial with glowing hour marks, iron hands
    m.box("chest", -8, -16, -5, 16, 16, 10, B.plate(B.BRASS_D, B.BRASS_DD, B.BRASS, seed=12, rivet_step=3))
    m.box("chest", -9, -17, -4, 18, 2, 8, B.plate(B.BRASS, B.BRASS_D, B.BRASS_L, seed=13))      # collar / shoulders
    m.box("chest", -7, -15, -5.6, 14, 14, 1, B.dial(B.BRASS, B.CREAM, B.IRON, B.BRASS_D),
          glow={"front": _dial_glow})
    m.box("chest", -1, -9, -6.6, 2, 2, 1, B.BRASS_L)                                            # hub
    m.box("hand_min", -0.5, -6, -1.1, 1, 6, 1, {"front": B.IRON_D, "*": B.IRON})
    m.box("hand_min", -1, -7, -1.1, 2, 1, 1, B.IRON_D)
    m.box("hand_hour", -0.5, -4, -0.9, 1, 4, 1, {"front": B.IRON_D, "*": B.IRON})
    m.box("hand_hour", -1, -5, -0.9, 2, 2, 1, B.IRON_D)
    m.box("chest", -7, -1, -5.4, 14, 1, 1, B.IRON_D)                                           # case foot
    m.box("chest", -6, -19, 1, 12, 2, 5, B.iron(14))                                            # back housing
    m.box("chest", -2, -21, 2, 4, 3, 2, B.soot(B.COPPER, 15))                                   # exhaust

    # ---- head: brass mask, monocle, waxed moustache, top hat
    def mask(f, x, y, w, h):
        if f != "front":
            return B.brass(16)(f, x, y, w, h)
        if y in (2, 3) and x == 5:
            return B.AMBER                                                                      # small right eye
        if y == 5 and 2 <= x <= 4:
            return B.BRASS_DD                                                                   # mouth slit
        return mul(B.BRASS, 1.06 - 0.12 * y / h)
    m.box("head", -3.5, -7, -3.5, 7, 7, 7, mask,
          glow={"front": lambda f, x, y, w, h: B.AMBER if (y in (2, 3) and x == 5) else None})
    m.box("head", -3, -6, -4.2, 3, 3, 1, B.lens(B.AMBER, B.BRASS_L, B.AMBER_L), glow=B.lens_glow(B.AMBER, B.AMBER_L))
    m.box("head", -5, -3, -4.4, 10, 3, 1, moustache)
    m.box("head", -1.5, 0, -2, 3, 2, 3, B.iron(17))                                             # neck
    m.box("head", -5.5, -8, -5.5, 11, 1, 11, B.plate(B.IRON, B.IRON_D, B.IRON_L, seed=18))      # hat brim
    m.box("head", -3.5, -15, -3.5, 7, 7, 7, B.plate(B.IRON, B.IRON_D, B.IRON_L, seed=19))       # hat crown
    m.box("head", -3.5, -10, -3.5, 7, 1, 7, B.BRASS, grow=0.1)                                  # hat band
    m.box("head", 2.5, -12, -4.1, 3, 3, 1, B.cog(B.BRASS_L, B.BRASS_D, teeth=6, hub=0.3))      # cog badge

    # ---- gear wings: an iron spar each, three cogs that turn
    for side, sx in (("r", -1), ("l", 1)):
        w = f"wing_{side}"
        m.box(w, (0 if sx > 0 else -28), -1, -0.5, 28, 2, 2, B.rod(B.IRON, 20))
        m.box(w, (-2 if sx > 0 else -2), -2, -1, 4, 4, 3, B.iron(26))                              # wing root
        for k, (size, teeth, col) in enumerate(((13, 10, B.BRASS), (9, 8, B.COPPER), (7, 6, B.BRASS_L))):
            c = f"cog_{side}{k}"
            half = size / 2
            m.box(c, -half, -half, -0.5, size, size, 1,
                  B.cog(col, mul(col, 0.55), teeth=teeth, hub=0.18, spokes=4 if size >= 9 else 0))

    # ---- arms: iron upper arms, brass forearms with cream cuffs, iron gloves
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"fore_{side}"
        m.box(arm, -2.5, -2.5, -2.5, 5, 5, 5, B.cog(B.BRASS, B.BRASS_D, teeth=8, hub=0.25, faces=("left", "right"), edges=True))
        m.box(arm, -2, -2, -2, 4, 4, 4, B.brass(21))
        m.box(arm, -1.5, 2, -1.5, 3, 9, 3, B.rod(B.IRON, 22))
        m.box(fore, -1.5, 0, -1.5, 3, 10, 3, B.rod(B.BRASS, 23))
        m.box(fore, -2, 7, -2, 4, 2, 4, B.CREAM)                                                # cuff
        m.box(fore, -2, 9, -2, 4, 4, 4, B.iron(24))                                             # glove

    # ---- the pendulum cane: a long iron shaft, a brass knob, a heavy bob with an aether core
    m.box("cane", -0.5, -4, -0.5, 1, 26, 1, B.rod(B.IRON_L, 25))
    m.box("cane", -1, -5, -1, 2, 2, 2, B.BRASS_L)
    m.box("cane", -3.5, 21, -1, 7, 7, 2, B.lens(B.AETHER, B.BRASS, B.AETHER_L), glow=B.lens_glow(B.AETHER, B.AETHER_L))
    m.box("cane", -4.5, 20, -0.5, 9, 9, 1, B.cog(B.BRASS, B.BRASS_D, teeth=10, hub=0.0))
    # ---- the pocket watch on its chain
    m.box("watch", -0.5, 0, -0.5, 1, 3, 1, B.IRON_L)
    m.box("watch", -1.5, 3, -1, 3, 3, 1, B.dial(B.BRASS_L, B.CREAM, B.IRON, B.BRASS_D, numerals=4))

    # ------------------------------------------------------------------ animations
    sides = (("r", -1), ("l", 1))
    cog_turn = {0: 360, 1: -720, 2: 1080}       # meshing cogs alternate direction, smaller ones turn faster

    idle = m.anim("idle", 6.0)
    idle.rot("hand_min", (0, (0, 0, 0), "linear"), (6.0, (0, 0, 1440), "linear"))
    idle.rot("hand_hour", (0, (0, 0, 0), "linear"), (6.0, (0, 0, 360), "linear"))
    for side, sx in sides:
        for k in range(3):
            idle.rot(f"cog_{side}{k}", (0, (0, 0, 0), "linear"), (6.0, (0, 0, cog_turn[k] * sx), "linear"))
        idle.rot(f"wing_{side}", (0, (0, 0, 0)), (3.0, (0, 4 * sx, 5 * sx)), (6.0, (0, 0, 0)))
    idle.pos("chest", (0, (0, 0, 0)), (1.5, (0, 0.6, 0)), (3.0, (0, 0, 0)), (4.5, (0, 0.6, 0)), (6.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (0, 0, 5)), (2.5, (0, 0, 5)), (3.5, (0, 0, -3)), (6.0, (0, 0, 0)))
    idle.rot("cane", (0, (0, 0, 0)), (1.5, (0, 0, 3)), (3.0, (0, 0, 0)), (4.5, (0, 0, -3)), (6.0, (0, 0, 0)))
    idle.rot("watch", (0, (0, 0, 0)), (1.5, (8, 0, 6)), (3.0, (0, 0, 0)), (4.5, (-8, 0, -6)), (6.0, (0, 0, 0)))
    idle.rot("tails", (0, (0, 0, 0)), (3.0, (4, 0, 0)), (6.0, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("thigh_r", (0, (24, 0, 0)), (0.8, (-24, 0, 0)), (1.6, (24, 0, 0)))
    walk.rot("thigh_l", (0, (-24, 0, 0)), (0.8, (24, 0, 0)), (1.6, (-24, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.8, (0, 0, 0)), (1.2, (30, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("arm_l", (0, (12, 0, 0)), (0.8, (-12, 0, 0)), (1.6, (12, 0, 0)))
    walk.rot("arm_r", (0, (-6, 0, 0)), (0.8, (6, 0, 0)), (1.6, (-6, 0, 0)))
    walk.pos("pelvis", (0, (0, 0, 0)), (0.4, (0, 1, 0)), (0.8, (0, 0, 0)), (1.2, (0, 1, 0)), (1.6, (0, 0, 0)))
    walk.rot("tails", (0, (6, 0, 0)), (0.4, (12, 0, 0)), (0.8, (6, 0, 0)), (1.2, (12, 0, 0)), (1.6, (6, 0, 0)))

    # sweep: the pendulum is lifted out to the right and behind (0.9 s = 18 ticks), then swings across the front
    a = m.anim("sweep", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.8, (-30, -50, 75)), (0.9, (-32, -55, 80)), (1.05, (-70, 60, -20), "linear"),
          (1.25, (-60, 70, -30)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.9, (0, -35, 0)), (1.05, (0, 30, 0), "linear"), (1.25, (0, 34, 0)), (1.6, (0, 0, 0)))
    a.rot("waist", (0, (0, 0, 0)), (0.9, (0, -10, 0)), (1.05, (0, 10, 0), "linear"), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-20, 0, 20)), (1.05, (10, 0, -10), "linear"), (1.6, (0, 0, 0)))
    a.rot("thigh_r", (0, (0, 0, 0)), (0.9, (10, 0, 6)), (1.6, (0, 0, 0)))
    a.rot("thigh_l", (0, (0, 0, 0)), (0.9, (-14, 0, -6)), (1.6, (0, 0, 0)))

    # slam: the cane rises overhead (1.0 s = 20 ticks), the bob crashes down in front
    a = m.anim("slam", 1.8)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-175, 0, 20)), (1.0, (-178, 0, 18)), (1.1, (-60, 0, -8), "linear"),
          (1.4, (-62, 0, -8)), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.9, (-160, 0, -20)), (1.0, (-165, 0, -18)), (1.1, (-60, 0, 8), "linear"),
          (1.4, (-62, 0, 8)), (1.8, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.0, (-16, 0, 0)), (1.1, (24, 0, 0), "linear"), (1.4, (20, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("pelvis", (0, (0, 0, 0)), (1.0, (0, 1.5, 0)), (1.1, (0, -3, 0), "linear"), (1.4, (0, -2.5, 0)), (1.8, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.0, (0, 10 * sx, 20 * sx)), (1.1, (0, -10 * sx, -10 * sx), "linear"),
              (1.8, (0, 0, 0)))
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (-25, 0, 8 * sx), "linear"), (1.4, (-22, 0, 8 * sx)),
              (1.8, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (40, 0, 0), "linear"), (1.4, (36, 0, 0)), (1.8, (0, 0, 0)))

    # summon: he winds the air with his left hand (0.8 s = 16 ticks), the clock races, spiders pour out
    a = m.anim("summon", 1.6)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-110, 0, -30)), (0.45, (-120, 30, -30)), (0.6, (-110, -30, -30)),
          (0.8, (-140, 0, -50)), (1.2, (-130, 0, -45)), (1.6, (0, 0, 0)))
    a.rot("fore_l", (0, (0, 0, 0)), (0.8, (-30, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("hand_min", (0, (0, 0, 0), "linear"), (1.6, (0, 0, 2160), "linear"))
    a.rot("hand_hour", (0, (0, 0, 0), "linear"), (1.6, (0, 0, 720), "linear"))
    a.rot("head", (0, (0, 0, 0)), (0.8, (-15, 0, 0)), (1.2, (-12, 0, 0)), (1.6, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.8, (0, 15 * sx, 25 * sx)), (1.2, (0, 15 * sx, 25 * sx)), (1.6, (0, 0, 0)))

    # timestop: arms flung wide, the hands rewind (1.2 s = 24 ticks), then everything holds still
    a = m.anim("timestop", 2.0)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (1.0, (-20, 0, 70 * sx)), (1.2, (-25, 0, 80 * sx)),
              (1.3, (-10, 0, 95 * sx), "linear"), (1.7, (-10, 0, 95 * sx)), (2.0, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.2, (0, 20 * sx, 30 * sx)), (1.7, (0, 20 * sx, 30 * sx)), (2.0, (0, 0, 0)))
        for k in range(3):
            a.rot(f"cog_{side}{k}", (0, (0, 0, 0), "linear"), (1.2, (0, 0, -720 * sx * (1 if k % 2 == 0 else -1)), "linear"),
                  (2.0, (0, 0, -720 * sx * (1 if k % 2 == 0 else -1)), "linear"))
    a.rot("hand_min", (0, (0, 0, 0), "linear"), (1.2, (0, 0, -1440), "linear"), (2.0, (0, 0, -1440), "linear"))
    a.rot("hand_hour", (0, (0, 0, 0), "linear"), (1.2, (0, 0, -720), "linear"), (2.0, (0, 0, -720), "linear"))
    a.rot("head", (0, (0, 0, 0)), (1.2, (-22, 0, 0)), (1.7, (-22, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (1.2, (-8, 0, 0)), (1.7, (-8, 0, 0)), (2.0, (0, 0, 0)))

    # gears: the left hand reaches back (0.6 s = 12 ticks) and flings a fan of cogs
    a = m.anim("gears", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.55, (30, 40, 50)), (0.6, (32, 42, 52)), (0.72, (-90, -30, -10), "linear"),
          (0.9, (-85, -25, -10)), (1.2, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (0, 25, 0)), (0.72, (0, -25, 0), "linear"), (1.2, (0, 0, 0)))
    for side, sx in sides:
        for k in range(3):
            a.rot(f"cog_{side}{k}", (0, (0, 0, 0), "linear"), (1.2, (0, 0, 720 * sx * (1 if k % 2 == 0 else -1)), "linear"))

    # blink: a deep crouch behind the cane (0.5 s = 10 ticks), then he springs up somewhere else
    a = m.anim("blink", 1.0)
    a.pos("pelvis", (0, (0, 0, 0)), (0.45, (0, -6, 0)), (0.5, (0, -6, 0)), (0.6, (0, 2, 0), "linear"), (1.0, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.45, (-45, 0, 10 * sx)), (0.5, (-45, 0, 10 * sx)), (0.6, (0, 0, 0), "linear"),
              (1.0, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.45, (70, 0, 0)), (0.5, (70, 0, 0)), (0.6, (0, 0, 0), "linear"), (1.0, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.5, (0, -20 * sx, -30 * sx)), (0.6, (0, 25 * sx, 35 * sx), "linear"),
              (1.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.5, (25, 0, 0)), (0.6, (-10, 0, 0), "linear"), (1.0, (0, 0, 0)))

    # chime (midnight): the cane is lifted high and planted (1.0 s = 20 ticks); the twelve hours toll around him
    a = m.anim("chime", 2.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.9, (-150, 0, -10)), (1.0, (-155, 0, -10)), (1.1, (-35, 0, 0), "linear"),
          (1.9, (-35, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (1.0, (-100, 0, -60)), (1.9, (-100, 0, -60)), (2.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (1.0, (-20, 0, 0)), (1.1, (8, 0, 0), "linear"), (1.9, (8, 0, 0)), (2.2, (0, 0, 0)))
    a.rot("hand_min", (0, (0, 0, 0), "linear"), (1.0, (0, 0, -360), "linear"), (2.2, (0, 0, -1080), "linear"))
    a.rot("hand_hour", (0, (0, 0, 0), "linear"), (1.0, (0, 0, 360), "linear"), (2.2, (0, 0, 720), "linear"))
    for side, sx in sides:
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (1.0, (0, 25 * sx, 35 * sx)), (1.9, (0, 25 * sx, 35 * sx)), (2.2, (0, 0, 0)))

    # roar (phase two): wings flare, the dial races, head thrown back
    a = m.anim("roar", 2.0)
    for side, sx in sides:
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.6, (-40, 0, 60 * sx)), (1.6, (-45, 0, 65 * sx)), (2.0, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.6, (0, 30 * sx, 40 * sx)), (1.6, (0, 30 * sx, 40 * sx)), (2.0, (0, 0, 0)))
        for k in range(3):
            a.rot(f"cog_{side}{k}", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 1440 * sx * (1 if k % 2 == 0 else -1)), "linear"))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-30, 0, 0)), (1.6, (-28, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.6, (-12, 0, 0)), (1.6, (-10, 0, 0)), (2.0, (0, 0, 0)))
    a.rot("hand_min", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 2880), "linear"))
    a.rot("hand_hour", (0, (0, 0, 0), "linear"), (2.0, (0, 0, 1440), "linear"))

    # stagger: the spring runs down, he sags on bent knees, the cogs grind to a halt
    a = m.anim("stagger", 1.6)
    a.pos("pelvis", (0, (0, 0, 0)), (0.3, (0, -4, 0)), (1.2, (0, -4, 0)), (1.6, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"thigh_{side}", (0, (0, 0, 0)), (0.3, (-30, 0, 6 * sx)), (1.2, (-30, 0, 6 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"shin_{side}", (0, (0, 0, 0)), (0.3, (50, 0, 0)), (1.2, (50, 0, 0)), (1.6, (0, 0, 0)))
        a.rot(f"arm_{side}", (0, (0, 0, 0)), (0.3, (10, 0, -6 * sx)), (1.2, (12, 0, -6 * sx)), (1.6, (0, 0, 0)))
        a.rot(f"wing_{side}", (0, (0, 0, 0)), (0.3, (0, -10 * sx, 55 * sx)), (1.2, (0, -10 * sx, 55 * sx)), (1.6, (0, 0, 0)))
    a.rot("chest", (0, (0, 0, 0)), (0.3, (22, 0, 8)), (1.2, (24, 0, 8)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (20, 0, -10)), (1.2, (22, 0, -10)), (1.6, (0, 0, 0)))
    return m


def _dial_glow(face, x, y, w, h):
    """Glow layer of the chest dial: only the hour marks shine (aether)."""
    if face != "front":
        return None
    col = B.dial(B.BRASS, B.CREAM, B.AETHER, B.BRASS_D)(face, x, y, w, h)
    return B.AETHER if col == B.AETHER else None
