"""Lantern Wisp (Feu follet): the light thief of the catacombs and the tombs.

Silhouette idea: a lantern that walks on air. A rusty iron lantern with a peaked roof, a hook ring and corner posts
holds a pale soul-flame for a body with a mischievous face inside it; flame tongues lick up through the roof, two
long curling wisps of flame serve as arms, and a tapering, flickering tail trails below like a comet. It drinks the
flames of the candles around it: three texture variants (dim, lit, blazing) show how much light it has stolen.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

VARIANTS = ["dim", "lit", "blazing"]
IRON = (74, 66, 62)
IRON_L = (120, 108, 98)
IRON_D = (38, 34, 34)
RUST = (140, 76, 40)
RUST_D = (96, 50, 28)
BRASS = (190, 150, 70)
BRASS_L = (238, 204, 120)
SOOT = (26, 22, 24)
# flame colours per variant: (core, light, edge)
FLAME = {
    "dim": ((70, 120, 150), (150, 200, 220), (40, 70, 100)),
    "lit": ((90, 210, 230), (210, 250, 255), (50, 130, 170)),
    "blazing": ((150, 240, 255), (250, 255, 255), (90, 190, 230)),
}


def iron(seed=0, rivets=True):
    """Old lantern iron: a lit top edge, a dark rim, rust blooming from the bottom, rivets at the corners."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        if face == "top":
            return IRON_L if (x in (0, w - 1) or y in (0, h - 1)) else (RUST if K.h(x, y, seed) % 6 == 0 else IRON)
        if h > 2 and y == 0:
            return IRON_L
        if rivets and w > 3 and h > 2 and y == 1 and x in (1, w - 2):
            return BRASS_L
        if K.h(x, y, seed) % 100 < 10 + 40 * y / max(1, h):
            return RUST if K.h(x, y, seed + 1) % 3 else RUST_D
        return mul(IRON, 1.05 - 0.2 * y / max(1, h))
    return f


def cage(seed=0):
    """The lantern's walls: a riveted frame and two thin vertical bars per side, the panes open (the flame shows
    through); soot climbs the inside of the upper frame."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            if 1 <= x <= w - 2 and 1 <= y <= h - 2:
                return None
            return IRON
        if y == 0:
            return SOOT if K.h(x, seed) % 3 == 0 else IRON_L
        if y == h - 1:
            return RUST_D if K.h(x, seed + 1) % 4 == 0 else IRON
        if x in (0, w - 1):
            return IRON_D
        if face != "front" and x in (w // 3, w - 1 - w // 3):
            return IRON if y % 3 else BRASS                                     # the bars and their rivets
        if face != "front" and y == h // 2:
            return IRON_D                                                       # a cross bar
        return None
    return f


def flame_paint(core, light, edge, tongues=True, seed=0, ragged=False):
    """Soul flame: a bright heart, cooler edges, flickering tongues cut into the top rows (transparent)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return edge
        if face == "top":
            return light
        if tongues and w > 1 and y < 2 and (x + seed) % 3 == (1 if y == 0 else 0) and x not in (w // 2,):
            return None
        if ragged and w > 2 and face not in ("top", "bottom") and x in (0, w - 1) and K.h(x, y, seed) % 3 == 0:
            return None                                                         # flickering, broken edges
        if x in (0, w - 1) and w > 2:
            return edge
        k = y / max(1, h - 1)
        return mix(light, core, min(1.0, k * 1.4)) if (x + y + seed) % 4 else mix(core, edge, 0.5)
    return f


def build(variant=None):
    v = variant or VARIANTS[0]
    core, light, edge = FLAME[v]
    m = Model("lantern_wisp", seed=387, shadow=0.3, variants=VARIANTS, render="entityCutout", walk_speed=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -11, 0))
    m.part("head", "body", pivot=(0, -4, 0))
    m.part("flare", "head", pivot=(0, -6, 0))
    m.part("ring", "body", pivot=(0, -15.5, 0))
    m.part("arm_r", "body", pivot=(-4, -5, 0), rot=(0, 0, 40))
    m.part("hand_r", "arm_r", pivot=(0, 4, 0), rot=(0, 0, -30))
    m.part("arm_l", "body", pivot=(4, -5, 0), rot=(0, 0, -40))
    m.part("hand_l", "arm_l", pivot=(0, 4, 0), rot=(0, 0, 30))
    m.part("tail", "body", pivot=(0, 0, 0))
    m.part("tail2", "tail", pivot=(0, 3, 0.5))
    m.part("tail3", "tail2", pivot=(0, 3, 0.5))
    m.part("tail4", "tail3", pivot=(0, 2.5, 0.5))

    flame = flame_paint(core, light, edge, tongues=False)

    eyes = {(1, 1), (4, 1)}
    grin = {(1, 3), (4, 3), (2, 4), (3, 4)}

    def face(f_, x, y, w, h):
        if f_ == "front" and ((x, y) in eyes or (x, y) in grin):
            return (16, 26, 36)                                                  # hollow eyes and a wide grin
        return flame(f_, x, y, w, h)

    def face_glow(f_, x, y, w, h):
        if f_ == "front" and ((x, y) in eyes or (x, y) in grin):
            return None
        return flame(f_, x, y, w, h)

    # the flame body inside the lantern, with the face (it is the "head": it looks at its prey)
    m.box("head", -3, -6, -3, 6, 6, 6, face, glow=face_glow)
    # flame tongues licking up out of the head, through the roof
    tongue = flame_paint(core, light, edge, tongues=True, seed=1)
    m.box("flare", -2, -3, -2, 4, 3, 4, tongue, glow=tongue)
    m.box("flare", -1, -6, -1, 2, 3, 2, flame_paint(light, light, core, tongues=True, seed=2),
          glow=flame_paint(light, light, core, tongues=True, seed=2))

    # ---- the lantern: base plate, four corner posts, the open cage, a peaked roof, chimney and hook ring
    m.box("body", -4, -1.5, -4, 8, 2, 8, iron(1))
    m.box("body", -3, 0.5, -3, 6, 1, 6, iron(2, rivets=False))                   # the drip pan
    m.box("body", -3.5, -10.5, -3.5, 7, 9, 7, cage(3))
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.box("body", 3.5 * sx - 0.5 - 0.5 * sx, -11, 3.5 * sz - 0.5 - 0.5 * sz, 1, 10, 1, iron(4 + sx + sz, rivets=False), grow=0.15)
    m.box("body", -4.5, -12, -4.5, 9, 1, 9, iron(6))                            # eaves
    m.box("body", -3.5, -13, -3.5, 7, 1, 7, iron(7))
    m.box("body", -2.5, -14, -2.5, 5, 1, 5, iron(8, rivets=False))
    m.box("body", -1.5, -15, -1.5, 3, 1, 3, {"*": BRASS, "top": SOOT})          # the chimney, black with soot
    m.box("ring", -1.5, -3, -0.5, 3, 3, 1, {"front": lambda f_, x, y, w, h: None if (x, y) == (1, 1) else BRASS,
                                           "back": lambda f_, x, y, w, h: None if (x, y) == (1, 1) else BRASS,
                                           "*": mul(BRASS, 0.8)})

    # ---- flame arms: a thick wisp that thins into a curling tip
    for arm, hand in (("arm_r", "hand_r"), ("arm_l", "hand_l")):
        m.box(arm, -1, 0, -1, 2, 4, 2, flame_paint(core, light, edge, tongues=True, seed=3),
              glow=flame_paint(core, light, edge, tongues=True, seed=3))
        m.box(hand, -0.5, 0, -0.5, 1, 3, 1, flame_paint(core, light, edge, tongues=False),
              glow=lambda f_, x, y, w, h: core)
        m.box(hand, -0.5, 3, -1.5, 1, 1, 2, {"*": edge}, glow={"*": edge})      # the curling tip

    # ---- the trailing comet tail below the lantern
    rag = flame_paint(core, light, edge, tongues=False, seed=5, ragged=True)
    m.box("tail", -2, 0, -2, 4, 3, 4, rag, glow=rag)
    m.box("tail2", -1.5, 0, -1.5, 3, 3, 3, rag, glow=rag)
    m.box("tail3", -1, 0, -1, 2, 3, 2, flame, glow=lambda f_, x, y, w, h: core)
    m.box("tail4", -0.5, 0, -0.5, 1, 3, 1, {"*": edge, "bottom": None}, glow=lambda f_, x, y, w, h: edge)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.0)
    idle.pos("body", (0, (0, 0, 0)), (1.0, (0, 1.5, 0)), (2.0, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, -3)), (1.0, (0, 0, 3)), (2.0, (0, 0, -3)))
    idle.rot("ring", (0, (0, 0, 8)), (1.0, (0, 0, -8)), (2.0, (0, 0, 8)))       # the hook ring swings
    idle.rot("tail", (0, (8, 0, 0)), (0.5, (0, 0, 8)), (1.0, (-6, 0, 0)), (1.5, (0, 0, -8)), (2.0, (8, 0, 0)))
    idle.rot("tail2", (0, (10, 0, 6)), (0.5, (-6, 0, 10)), (1.0, (10, 0, -6)), (1.5, (-6, 0, -10)), (2.0, (10, 0, 6)))
    idle.rot("tail3", (0, (14, 0, -8)), (0.5, (-10, 0, 12)), (1.0, (14, 0, 8)), (1.5, (-10, 0, -12)), (2.0, (14, 0, -8)))
    idle.rot("tail4", (0, (-12, 0, 10)), (0.5, (14, 0, -10)), (1.0, (-12, 0, -10)), (1.5, (14, 0, 10)),
             (2.0, (-12, 0, 10)))
    idle.scale("head", (0, (1, 1, 1)), (0.25, (1.05, 1.1, 1.05)), (0.5, (1, 1, 1)), (0.8, (0.96, 1.06, 0.96)), (1.2, (1, 1, 1)),
               (1.6, (1.04, 0.95, 1.04)), (2.0, (1, 1, 1)))                     # the flame flickers
    idle.scale("flare", (0, (1, 1, 1)), (0.2, (0.9, 1.3, 0.9)), (0.45, (1.1, 0.8, 1.1)), (0.7, (0.95, 1.2, 0.95)),
               (1.1, (1, 0.9, 1)), (1.5, (0.9, 1.35, 0.9)), (2.0, (1, 1, 1)))
    idle.rot("flare", (0, (0, 0, 0)), (0.5, (0, 0, 8)), (1.0, (0, 0, -4)), (1.5, (0, 0, 6)), (2.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.0, (-20, 0, 10)), (2.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.0, (-20, 0, -10)), (2.0, (0, 0, 0)))
    idle.rot("hand_r", (0, (0, 0, 0)), (0.5, (-10, 0, -14)), (1.3, (10, 0, 6)), (2.0, (0, 0, 0)))
    idle.rot("hand_l", (0, (0, 0, 0)), (0.5, (-10, 0, 14)), (1.3, (10, 0, -6)), (2.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("body", (0, (14, 0, 0)), (1.0, (14, 0, 0)))
    walk.rot("tail", (0, (30, 0, 0)), (0.5, (36, 0, 0)), (1.0, (30, 0, 0)))
    walk.rot("tail2", (0, (10, 0, 0)), (0.5, (18, 0, 0)), (1.0, (10, 0, 0)))
    walk.rot("tail3", (0, (12, 0, 0)), (0.5, (4, 0, 0)), (1.0, (12, 0, 0)))
    walk.rot("arm_r", (0, (30, 0, 0)), (0.5, (40, 0, 0)), (1.0, (30, 0, 0)))  # the arms stream behind
    walk.rot("arm_l", (0, (40, 0, 0)), (0.5, (30, 0, 0)), (1.0, (40, 0, 0)))
    walk.rot("ring", (0, (-14, 0, 0)), (0.5, (-20, 0, 0)), (1.0, (-14, 0, 0)))
    walk.rot("flare", (0, (-16, 0, 0)), (0.5, (-22, 0, 0)), (1.0, (-16, 0, 0)))

    # snuff: leans toward a candle, reaches out and inhales its flame (the flame swells at 0.6 s)
    a = m.anim("snuff", 0.9)
    a.rot("body", (0, (0, 0, 0)), (0.4, (25, 0, 0)), (0.6, (25, 0, 0)), (0.9, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.4, (0.8, 0.8, 0.8)), (0.6, (1.3, 1.3, 1.3), "linear"), (0.9, (1, 1, 1)))
    a.scale("flare", (0, (1, 1, 1)), (0.4, (0.5, 0.5, 0.5)), (0.6, (1.4, 1.8, 1.4), "linear"), (0.9, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-90, 0, 20)), (0.6, (-40, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-90, 0, -20)), (0.6, (-40, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("hand_r", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (0.6, (10, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("hand_l", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (0.6, (10, 0, 0)), (0.9, (0, 0, 0)))

    # lunge: it rears back, gathering its arms behind it (wind-up), then dashes at its prey (contact at 0.35 s =
    # 7 ticks), the tail whipping after it
    a = m.anim("lunge", 0.7)
    a.rot("body", (0, (0, 0, 0)), (0.25, (-24, 0, 0)), (0.35, (40, 0, 0), "linear"), (0.5, (34, 0, 0)), (0.7, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.25, (0, 1.5, 2)), (0.35, (0, -1, -4), "linear"), (0.5, (0, -1, -3.5)),
          (0.7, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-150, 0, 0)), (0.35, (-40, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (-150, 0, 0)), (0.35, (-40, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.25, (-20, 0, 0)), (0.35, (50, 0, 0), "linear"), (0.7, (0, 0, 0)))
    a.rot("tail2", (0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.45, (30, 0, 0)), (0.7, (0, 0, 0)))
    a.scale("head", (0, (1, 1, 1)), (0.25, (0.9, 0.9, 0.9)), (0.35, (1.2, 1.2, 1.2), "linear"), (0.7, (1, 1, 1)))

    # pulse: draws the stolen light in (it shrinks, the arms fold in) then lets out a wave of darkness (at 0.5 s =
    # 10 ticks)
    a = m.anim("pulse", 1.0)
    a.scale("head", (0, (1, 1, 1)), (0.45, (0.6, 0.6, 0.6)), (0.5, (1.5, 1.5, 1.5), "linear"), (1.0, (1, 1, 1)))
    a.scale("flare", (0, (1, 1, 1)), (0.45, (0.3, 0.3, 0.3)), (0.5, (1.6, 2.2, 1.6), "linear"), (1.0, (1, 1, 1)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (0, 0, -60)), (0.5, (0, 0, 70), "linear"), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (0, 0, 60)), (0.5, (0, 0, -70), "linear"), (1.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.45, (0, 2, 0)), (0.5, (0, -1, 0)), (1.0, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.45, (0, 0, 0)), (0.55, (0, 0, 20)), (0.7, (0, 0, -16)), (1.0, (0, 0, 0)))
