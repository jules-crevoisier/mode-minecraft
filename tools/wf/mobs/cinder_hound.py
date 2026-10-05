"""Cinder Hound (Molosse de cendre): the pack hunter of the Nether fortresses and foundries.

Silhouette idea: a wolf carved from a cooling lava flow. A lean, hunched hound of black basalt plates split by glowing
magma cracks, a heavy jaw full of ember teeth, a broken iron chain still hanging from its collar and a tail that is
nothing but a plume of embers. It howls to rally the pack, then charges in a line of fire.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

BASALT = (52, 50, 56)
BASALT_D = (32, 30, 34)
BASALT_L = (90, 86, 92)
MAGMA = (255, 120, 30)
MAGMA_L = (255, 210, 110)
IRON = (96, 92, 92)
IRON_D = (56, 52, 52)


def plates(seed=0):
    """Basalt plates split by magma cracks (the cracks are also the glow)."""
    def f(face, x, y, w, h):
        if crack(face, x, y, w, h, seed):
            return MAGMA
        c = BASALT if K.h(x // 2, y // 2, seed) % 3 else BASALT_D
        if face == "top":
            c = mul(c, 1.15)
        if y == 0 and face in ("front", "back", "left", "right"):
            c = BASALT_L
        return c
    return f


def crack(face, x, y, w, h, seed):
    if face == "bottom":
        return False
    # thin diagonal veins in some plates, never on the plate's lit top row
    if face != "top" and y == 0:
        return False
    return (x + 2 * y + seed) % 9 == 0 and K.h(x // 3, y // 3, seed) % 3 == 0


def plates_glow(seed=0):
    def f(face, x, y, w, h):
        if crack(face, x, y, w, h, seed):
            return MAGMA_L if K.h(x, y, seed + 2) % 3 == 0 else MAGMA
        return None
    return f


def build():
    m = Model("cinder_hound", seed=399, shadow=0.7, walk_speed=1.8, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -10, 0))
    m.part("neck", "body", pivot=(0, -2, -6), rot=(-15, 0, 0))
    m.part("head", "neck", pivot=(0, -2, -3))
    m.part("jaw", "head", pivot=(0, 0, -2))
    m.part("tail", "body", pivot=(0, -2, 6), rot=(35, 0, 0))
    m.part("tail2", "tail", pivot=(0, 0, 4))
    for name, x, z in (("leg_fr", -2.5, -4.5), ("leg_fl", 2.5, -4.5), ("leg_br", -2.5, 4.5), ("leg_bl", 2.5, 4.5)):
        m.part(name, "body", pivot=(x, 0, z))

    # ------------------------------------------------------------------ body: deep chest, ribbed flanks, spine ridge
    m.box("body", -4, -4, -7, 8, 7, 8, plates(1), glow=plates_glow(1))                # chest and shoulders
    m.box("body", -3, -3, 0, 6, 5, 7, plates(2), glow=plates_glow(2))                 # lean hindquarters
    for i, z in enumerate((-6, -3, 0, 3)):
        m.box("body", -0.5, -6 + (i == 0), z, 1, 2, 2, plates(3 + i), glow=plates_glow(3 + i))   # spine spikes

    # ------------------------------------------------------------------ neck, head, jaw, eyes
    m.box("neck", -2.5, -3, -4, 5, 5, 5, plates(8), glow=plates_glow(8))

    def collar(f_, x, y, w, h):
        return IRON if (x + y) % 2 else IRON_D
    m.box("neck", -3, -3.5, -2, 6, 6, 1, collar)
    m.part("chain", "neck", pivot=(0, 2.5, -1.5), rot=(10, 0, 0))
    for k in range(3):
        m.box("chain", -0.5, k * 2, -0.5, 1, 2, 1, lambda f_, x, y, w, h: IRON if y == 0 else IRON_D)

    def skull(f_, x, y, w, h):
        if f_ == "front" and y == 1 and x in (0, w - 1):
            return MAGMA_L                                                        # eyes
        return plates(9)(f_, x, y, w, h)
    m.box("head", -3, -3, -5, 6, 5, 5, skull, glow=lambda f_, x, y, w, h: MAGMA_L if f_ == "front" and y == 1 and x in (0, w - 1)
          else plates_glow(9)(f_, x, y, w, h))
    m.box("head", -2, -1, -9, 4, 2, 4, plates(10), glow=plates_glow(10))              # the snout
    m.box("head", -1, -1.5, -9.2, 2, 1, 1, BASALT_D)                                  # nose
    for sx in (-1, 1):
        m.box("head", (1 if sx > 0 else -3), -6, -1, 2, 3, 2, plates(11 + sx), glow=plates_glow(11 + sx))   # ears

    def teeth(f_, x, y, w, h):
        if f_ in ("front", "left", "right") and y == 0 and x % 2 == 0:
            return MAGMA_L
        return plates(13)(f_, x, y, w, h)
    m.box("jaw", -2, 1, -7, 4, 1, 5, teeth, glow=lambda f_, x, y, w, h: MAGMA_L if f_ in ("front", "left", "right") and
          y == 0 and x % 2 == 0 else None)
    m.box("head", -1.5, 0.5, -8.5, 3, 1, 3, {"*": (120, 30, 20), "bottom": MAGMA}, glow={"bottom": MAGMA, "*": None})  # the hot maw

    # ------------------------------------------------------------------ legs
    for name in ("leg_fr", "leg_fl", "leg_br", "leg_bl"):
        front = name[4] == "f"
        m.box(name, -1.5, 0, -1.5, 3, 10, 3, plates(14 + front), glow=plates_glow(14 + front))
        m.box(name, -2, 8, -2.5 if front else -2, 4, 2, 4, {"*": BASALT_D, "top": BASALT})   # paws
        m.box(name, -1.5, 9, -3.5 if front else -3, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})    # claw tips
        m.box(name, 0.5, 9, -3.5 if front else -3, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})

    # ------------------------------------------------------------------ the ember tail
    m.box("tail", -1, -1, 0, 2, 2, 4, plates(16), glow=plates_glow(16))
    m.box("tail2", -1.5, -1.5, 0, 3, 3, 5, {"*": lambda f_, x, y, w, h: MAGMA if (x + y + w) % 3 else MAGMA_L, "back": MAGMA_L},
          glow={"*": lambda f_, x, y, w, h: MAGMA if (x + y) % 3 else MAGMA_L})

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 2.0)
    idle.rot("tail", (0, (0, -10, 0)), (1.0, (6, 10, 0)), (2.0, (0, -10, 0)))
    idle.rot("tail2", (0, (0, 12, 0)), (1.0, (-6, -12, 0)), (2.0, (0, 12, 0)))
    idle.pos("body", (0, (0, 0, 0)), (0.5, (0, 0.5, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0.5, 0)), (2.0, (0, 0, 0)))   # panting
    idle.rot("jaw", (0, (0, 0, 0)), (0.25, (14, 0, 0)), (0.5, (0, 0, 0)), (1.0, (0, 0, 0)), (1.25, (14, 0, 0)),
             (1.5, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 6)), (1.0, (0, 0, -6)), (2.0, (0, 0, 6)))

    walk = m.anim("walk", 0.6)
    for name, ph in (("leg_fr", 0), ("leg_bl", 0), ("leg_fl", 1), ("leg_br", 1)):
        a, b = (36, -36) if ph == 0 else (-36, 36)
        walk.rot(name, (0, (a, 0, 0)), (0.3, (b, 0, 0)), (0.6, (a, 0, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.15, (0, 0.8, 0)), (0.3, (0, 0, 0)), (0.45, (0, 0.8, 0)), (0.6, (0, 0, 0)))
    walk.rot("tail", (0, (-20, 0, 0)), (0.6, (-20, 0, 0)))
    walk.rot("chain", (0, (30, 0, 0)), (0.3, (40, 0, 0)), (0.6, (30, 0, 0)))

    # howl: sits back, throws the head up and howls (1.4 s; the pack is called at 0.5 s)
    a = m.anim("howl", 1.4)
    a.rot("body", (0, (0, 0, 0)), (0.3, (-25, 0, 0)), (1.1, (-25, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.3, (-40, 0, 0)), (1.1, (-45, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (1.1, (26, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_br", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.1, (-50, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_bl", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.1, (-50, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_fr", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (1.1, (25, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("leg_fl", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (1.1, (25, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, -2, 1)), (1.1, (0, -2, 1)), (1.4, (0, 0, 0)))

    # charge: crouches low, digging in (0.6 s = 12 ticks), then bursts forward head down
    a = m.anim("charge", 1.2)
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, -3, 1.5)), (0.6, (0, -3, 1.5)), (0.7, (0, 0, -2), "linear"), (1.0, (0, 0, -1)),
          (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (8, 0, 0)), (0.7, (-6, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.7, (25, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("leg_fr", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.7, (-60, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("leg_fl", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.7, (-60, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("leg_br", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (0.7, (60, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("leg_bl", (0, (0, 0, 0)), (0.5, (40, 0, 0)), (0.7, (60, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.7, (-50, 0, 0)), (1.2, (0, 0, 0)))

    # bite: a lunge of the head and a snap (lands at 0.25 s = 5 ticks)
    a = m.anim("bite", 0.5)
    a.rot("neck", (0, (0, 0, 0)), (0.15, (-15, 0, 0)), (0.25, (20, 0, 0), "linear"), (0.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.15, (45, 0, 0)), (0.25, (0, 0, 0), "linear"), (0.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.15, (0, 0, 1)), (0.25, (0, 0, -2), "linear"), (0.5, (0, 0, 0)))
    return m
