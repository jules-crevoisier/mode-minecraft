"""Cinder Hound (Molosse de cendre): the pack hunter of the Nether fortresses and foundries.

Silhouette idea: a wolf carved from a cooling lava flow. A lean, hunched hound of black basalt columns split by
glowing magma veins: a deep chest under a hackle of basalt shards, a narrow waist, dog legs with real hocks, a long
heavy-jawed skull full of ember teeth with swept-back ears, a broken iron chain still hanging from its collar and a
tail that thins into a plume of embers. It howls to rally the pack, then charges in a line of fire.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

BASALT = (54, 52, 58)
BASALT_D = (30, 28, 32)
BASALT_L = (96, 92, 98)
ASH = (120, 112, 108)
MAGMA = (255, 116, 28)
MAGMA_L = (255, 214, 120)
MAGMA_D = (170, 48, 16)
IRON = (104, 98, 96)
IRON_D = (56, 52, 52)


def vein(face, x, y, w, h, seed):
    """A magma vein meandering down a face (one per side face, its column chosen by the seed), plus a second, short
    branch on wide faces."""
    if face in ("top", "bottom") or w < 4 or h < 4:
        return False
    s = seed + {"front": 1, "back": 2, "left": 3, "right": 4}[face]
    x0 = 1 + K.h(s, w, h) % (w - 2)
    xi = x0 + (1 if (y + s) % 5 in (2, 3) else 0) - (1 if (y + s) % 7 == 0 else 0)
    if x == xi and 1 <= y <= h - 1 - (K.h(s, 3) % 2):
        return True
    if w >= 8 and h >= 5:
        x1 = (x0 + w // 2) % (w - 2) + 1
        return x == x1 + (y - 1) // 2 and 1 <= y <= min(h - 2, 3)
    return False


def basalt(seed=0, veins=True):
    """Basalt columns: vertical facets of three greys, lit along the top, ash on the top faces, darker underneath,
    split by magma veins (also the glow)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return BASALT_D
        if face == "top":
            return ASH if K.h(x, y, seed) % 5 == 0 else mul(BASALT_L, 0.95)
        if veins and vein(face, x, y, w, h, seed):
            return MAGMA
        if y == 0:
            return BASALT_L
        col = (x + K.h(x // 2, seed) % 2) % 3
        c = (BASALT, mul(BASALT, 0.86), mul(BASALT, 1.1))[col]
        return mul(c, 1.04 - 0.22 * y / max(1, h))
    return f


def basalt_glow(seed=0):
    def f(face, x, y, w, h):
        if vein(face, x, y, w, h, seed):
            return MAGMA_L if K.h(x, y, seed) % 4 == 0 else MAGMA
        return None
    return f


def ember(seed=0, tips=True):
    """Ember plume: hot yellow heart, orange, a dark cooling crust, flame tips cut into the far end."""
    def f(face, x, y, w, h):
        if tips and face == "back" and (x + y + seed) % 2 == 0:
            return None
        if face in ("left", "right", "top", "bottom") and tips and x >= w - 1 and (y + seed) % 2:
            return None
        r = K.h(x, y, seed) % 6
        return MAGMA_L if r == 0 else (MAGMA_D if r == 5 else MAGMA)
    return f


def build():
    m = Model("cinder_hound", seed=399, shadow=0.7, walk_speed=1.8, walk_scale=1.0)
    m.part("bone", pivot=(0, 24, 0))
    m.part("body", "bone", pivot=(0, -11, 0))
    m.part("hips", "body", pivot=(0, -2, 1))
    m.part("neck", "body", pivot=(0, -4, -6), rot=(-20, 0, 0))
    m.part("head", "neck", pivot=(0, -3, -3), rot=(18, 0, 0))
    m.part("jaw", "head", pivot=(0, 0.5, -3))
    m.part("ear_r", "head", pivot=(-2, -3, -1), rot=(-35, 0, -15))
    m.part("ear_l", "head", pivot=(2, -3, -1), rot=(-35, 0, 15))
    m.part("tail", "hips", pivot=(0, -2, 6), rot=(30, 0, 0))
    m.part("tail2", "tail", pivot=(0, 0, 4), rot=(-12, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 0, 4), rot=(-10, 0, 0))
    # front legs: upper and fore leg; hind legs: a thigh angled back, a hock angled forward
    for side, x in (("r", -2.5), ("l", 2.5)):
        m.part(f"leg_f{side}", "body", pivot=(x, 0, -4.5))
        m.part(f"leg_f{side}2", f"leg_f{side}", pivot=(0, 5, 0))
        m.part(f"leg_b{side}", "hips", pivot=(x, 1, 4), rot=(-18, 0, 0))
        m.part(f"leg_b{side}2", f"leg_b{side}", pivot=(0, 5.5, 1.5), rot=(34, 0, 0))
        m.part(f"paw_b{side}", f"leg_b{side}2", pivot=(0, 6, 0), rot=(-16, 0, 0))

    # ------------------------------------------------------------------ chest, hackles, the lean hindquarters
    m.box("body", -4, -5, -8, 8, 8, 9, basalt(1), glow=basalt_glow(1))                # deep chest and shoulders
    m.box("body", -3.5, 2, -7, 7, 2, 6, basalt(2, veins=False))                       # brisket, under the chest
    m.box("hips", -3, -3, -1, 6, 5, 8, basalt(3), glow=basalt_glow(3))                # waist and haunches
    m.box("hips", -3.5, -3.5, 3, 7, 6, 4, basalt(4), glow=basalt_glow(4))
    # the hackles: basalt shards bristling backwards along the spine, tallest over the shoulders
    for i, (z, hgt, tilt) in enumerate(((-7, 3, 40), (-5, 5, 46), (-3, 4, 50), (-1, 3, 54), (2, 2, 58), (5, 2, 60))):
        p = m.part(f"shard{i}", "body" if z < 1 else "hips", pivot=(0, -5 if z < 1 else -3, z if z < 1 else z - 1),
                   rot=(-tilt, 0, (6 if i % 2 else -6)))
        m.box(p, -0.5 - (i < 3) * 0.5, -hgt, -1, 1 + (i < 3), hgt, 2, basalt(10 + i, veins=False),
              glow={"top": MAGMA_L if i in (1, 2) else None, "*": None})
    for sx in (-1, 1):                                                                # shoulder blades
        m.box("body", -4.5 if sx < 0 else 3.5, -5.5, -7, 1, 4, 5, basalt(18 + sx), glow=basalt_glow(18 + sx))

    # ------------------------------------------------------------------ neck, collar and broken chain
    m.box("neck", -2.5, -4, -4, 5, 6, 5, basalt(20), glow=basalt_glow(20))

    def collar(f_, x, y, w, h):
        if f_ == "front" and x == w // 2:
            return (176, 140, 66)                                                     # the brass buckle
        return IRON if (x + y) % 3 else IRON_D
    m.box("neck", -3, -3, -1.5, 6, 5, 2, collar, grow=0.1)
    m.part("chain", "neck", pivot=(0, 2, -1), rot=(10, 0, 0))
    for k in range(3):
        m.box("chain", -0.5, k * 2, -0.5, 1, 2, 1, lambda f_, x, y, w, h: IRON if y == 0 else IRON_D)
    m.box("chain", -1, 6, -0.5, 2, 1, 1, IRON_D)                                     # the snapped link

    # ------------------------------------------------------------------ skull, brow, snout, jaw, ears
    eyes = {(0, 1), (1, 1), (4, 1), (5, 1)}

    def skull(f_, x, y, w, h):
        if f_ == "front" and (x, y) in eyes:
            return MAGMA_L if x in (1, 4) else MAGMA                                  # slit eyes
        if f_ == "front" and y == 0:
            return BASALT_L                                                           # the brow ridge
        return basalt(21)(f_, x, y, w, h)

    def skull_glow(f_, x, y, w, h):
        if f_ == "front" and (x, y) in eyes:
            return MAGMA_L if x in (1, 4) else MAGMA
        return basalt_glow(21)(f_, x, y, w, h)
    m.box("head", -3, -3, -3, 6, 5, 5, skull, glow=skull_glow)
    m.box("head", -3.5, -3.5, -3.2, 7, 1, 2, basalt(22, veins=False))                 # heavy brow
    m.box("head", -2, -2, -8, 4, 3, 5, basalt(23), glow=basalt_glow(23))              # long snout
    m.box("head", -1, -2.5, -8.3, 2, 1, 1, BASALT_D)                                  # nose
    m.box("head", -2, 1, -7.5, 4, 1, 4, {"bottom": MAGMA, "*": MAGMA_D}, glow={"bottom": MAGMA_L, "*": None})  # hot maw

    def upper_teeth(f_, x, y, w, h):
        return MAGMA_L if f_ != "top" and x % 2 == 0 else None
    m.box("head", -2, 1, -8, 4, 1, 4, {"front": upper_teeth, "left": upper_teeth, "right": upper_teeth, "*": None},
          glow={"front": upper_teeth, "left": upper_teeth, "right": upper_teeth, "*": None}, grow=0.02)

    def teeth(f_, x, y, w, h):
        if f_ in ("front", "left", "right") and y == 0 and x % 2 == 1:
            return MAGMA_L
        return basalt(24, veins=False)(f_, x, y, w, h)
    m.box("jaw", -2, 0, -5, 4, 2, 5, teeth, glow=lambda f_, x, y, w, h: MAGMA_L if f_ in ("front", "left", "right") and
          y == 0 and x % 2 == 1 else None)
    for ear in ("ear_r", "ear_l"):
        m.box(ear, -1, -4, -0.5, 2, 4, 1, basalt(25, veins=False), glow={"front": lambda f_, x, y, w, h: MAGMA_D if y > 1 else None,
                                                                         "*": None})

    # ------------------------------------------------------------------ legs
    for side in ("r", "l"):
        f_up, f_lo = f"leg_f{side}", f"leg_f{side}2"
        b_up, b_lo, b_paw = f"leg_b{side}", f"leg_b{side}2", f"paw_b{side}"
        m.box(f_up, -1.5, -1, -1.5, 3, 6, 3, basalt(30, veins=False))
        m.box(f_lo, -1, 0, -1, 2, 5, 2, basalt(31, veins=False))
        m.box(f_lo, -1.5, 5, -2.5, 3, 1, 3, {"*": BASALT_D, "top": BASALT})            # paw
        m.box(f_lo, -1.5, 5, -3.5, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})              # claws
        m.box(f_lo, 0.5, 5, -3.5, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})
        m.box(b_up, -1.5, -1, -2, 3, 7, 4, basalt(32), glow=basalt_glow(32))           # thigh
        m.box(b_lo, -1, 0, -1, 2, 6, 2, basalt(33, veins=False))                       # hock
        m.box(b_paw, -1.5, 0, -2.5, 3, 1, 3, {"*": BASALT_D, "top": BASALT})
        m.box(b_paw, -1.5, 0, -3.5, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})
        m.box(b_paw, 0.5, 0, -3.5, 1, 1, 1, MAGMA_L, glow={"*": MAGMA_L})

    # ------------------------------------------------------------------ the tail: basalt root, then a plume of embers
    m.box("tail", -1, -1, 0, 2, 2, 4, basalt(40), glow=basalt_glow(40))
    m.box("tail2", -1.5, -1.5, 0, 3, 3, 4, ember(41, tips=False), glow=ember(41, tips=False))
    m.box("tail3", -1, -1, 0, 2, 2, 4, ember(42), glow=ember(42))

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 2.0)
    # panting: the chest heaves twice per loop, the jaw hangs open with it
    idle.pos("body", (0, (0, 0, 0)), (0.5, (0, 0.5, 0)), (1.0, (0, 0, 0)), (1.5, (0, 0.5, 0)), (2.0, (0, 0, 0)))
    idle.scale("body", (0, (1, 1, 1)), (0.5, (1.04, 1.03, 1)), (1.0, (1, 1, 1)), (1.5, (1.04, 1.03, 1)), (2.0, (1, 1, 1)))
    idle.rot("jaw", (0, (8, 0, 0)), (0.25, (18, 0, 0)), (0.5, (8, 0, 0)), (1.0, (8, 0, 0)), (1.25, (18, 0, 0)),
             (1.5, (8, 0, 0)), (2.0, (8, 0, 0)))
    idle.rot("neck", (0, (0, 0, 0)), (0.8, (2, 10, 0)), (1.6, (0, -6, 0)), (2.0, (0, 0, 0)))
    idle.rot("ear_r", (0, (0, 0, 0)), (1.1, (0, 0, 0)), (1.2, (12, 0, -10)), (1.35, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("ear_l", (0, (0, 0, 0)), (0.3, (10, 0, 8)), (0.45, (0, 0, 0)), (2.0, (0, 0, 0)))
    idle.rot("tail", (0, (0, -12, 0)), (1.0, (6, 12, 0)), (2.0, (0, -12, 0)))
    idle.rot("tail2", (0, (0, 10, 0)), (1.0, (-4, -14, 0)), (2.0, (0, 10, 0)))
    idle.rot("tail3", (0, (0, 16, 0)), (1.0, (-6, -18, 0)), (2.0, (0, 16, 0)))
    idle.rot("chain", (0, (0, 0, 6)), (1.0, (0, 0, -6)), (2.0, (0, 0, 6)))

    # trot: diagonal pairs, the lower legs folding as each foot lifts, the spine flexing
    walk = m.anim("walk", 0.6)
    for side, ph in (("r", 0.0), ("l", 0.3)):
        def k(t):
            return round((t + ph) % 0.6, 3)

        def cyc(part, frames):
            pts = sorted(((k(t), v) for t, v in frames), key=lambda p: p[0])
            first = pts[0][1] if pts[0][0] == 0 else None
            if first is None:
                # interpolate a value at 0 from the wrap
                pts = [(0.0, pts[-1][1])] + pts
            pts.append((0.6, pts[0][1]))
            walk.rot(part, *[(t, v) for t, v in pts])
        cyc(f"leg_f{side}", [(0.0, (34, 0, 0)), (0.3, (-30, 0, 0))])
        cyc(f"leg_f{side}2", [(0.0, (0, 0, 0)), (0.15, (0, 0, 0)), (0.45, (-40, 0, 0))])
        cyc(f"leg_b{side}", [(0.3, (30, 0, 0)), (0.0, (-30, 0, 0))])
        cyc(f"leg_b{side}2", [(0.15, (24, 0, 0)), (0.3, (0, 0, 0)), (0.45, (0, 0, 0))])
    walk.pos("body", (0, (0, 0, 0)), (0.15, (0, 0.8, 0)), (0.3, (0, 0, 0)), (0.45, (0, 0.8, 0)), (0.6, (0, 0, 0)))
    walk.rot("hips", (0, (0, 4, 0)), (0.3, (0, -4, 0)), (0.6, (0, 4, 0)))
    walk.rot("neck", (0, (4, 0, 0)), (0.15, (8, 0, 0)), (0.3, (4, 0, 0)), (0.45, (8, 0, 0)), (0.6, (4, 0, 0)))
    walk.rot("tail", (0, (-24, 0, 0)), (0.3, (-18, 0, 0)), (0.6, (-24, 0, 0)))
    walk.rot("tail3", (0, (0, 14, 0)), (0.3, (0, -14, 0)), (0.6, (0, 14, 0)))
    walk.rot("chain", (0, (30, 0, 0)), (0.3, (40, 0, 0)), (0.6, (30, 0, 0)))
    walk.rot("ear_r", (0, (-20, 0, 0)), (0.6, (-20, 0, 0)))
    walk.rot("ear_l", (0, (-20, 0, 0)), (0.6, (-20, 0, 0)))

    # howl: sits back on its haunches, throws the head up and howls (1.4 s; the pack is called at 0.5 s)
    a = m.anim("howl", 1.4)
    a.rot("body", (0, (0, 0, 0)), (0.3, (-25, 0, 0)), (1.1, (-25, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("hips", (0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.1, (10, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.3, (-35, 0, 0)), (0.5, (-48, 0, 0)), (1.1, (-45, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-14, 0, 0)), (0.8, (-14, 5, 0)), (1.1, (-14, -5, 0)), (1.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.4, (34, 0, 0)), (1.1, (28, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("ear_r", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (1.1, (-30, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("ear_l", (0, (0, 0, 0)), (0.4, (-30, 0, 0)), (1.1, (-30, 0, 0)), (1.4, (0, 0, 0)))
    for side in ("r", "l"):
        a.rot(f"leg_b{side}", (0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.1, (-50, 0, 0)), (1.4, (0, 0, 0)))
        a.rot(f"leg_b{side}2", (0, (0, 0, 0)), (0.3, (40, 0, 0)), (1.1, (40, 0, 0)), (1.4, (0, 0, 0)))
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.3, (25, 0, 0)), (1.1, (25, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.3, (40, 0, 0)), (1.1, (40, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.3, (0, -2, 1)), (1.1, (0, -2, 1)), (1.4, (0, 0, 0)))

    # charge: crouches low with the head down and the hackles up, digging in (0.6 s = 12 ticks), then bursts
    # forward
    a = m.anim("charge", 1.2)
    a.pos("body", (0, (0, 0, 0)), (0.5, (0, -3, 1.5)), (0.6, (0, -3, 1.5)), (0.7, (0, 0, -2), "linear"), (1.0, (0, 0, -1)),
          (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.5, (8, 0, 0)), (0.7, (-6, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("neck", (0, (0, 0, 0)), (0.5, (24, 0, 0)), (0.7, (28, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (16, 0, 0)), (0.7, (24, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("ear_r", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("ear_l", (0, (0, 0, 0)), (0.5, (-40, 0, 0)), (1.2, (0, 0, 0)))
    for i in range(6):
        a.rot(f"shard{i}", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (1.0, (20, 0, 0)), (1.2, (0, 0, 0)))  # hackles raised
    for side in ("r", "l"):
        a.rot(f"leg_f{side}", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.7, (-60, 0, 0), "linear"), (1.2, (0, 0, 0)))
        a.rot(f"leg_f{side}2", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.2, (0, 0, 0)))
        a.rot(f"leg_b{side}", (0, (0, 0, 0)), (0.5, (30, 0, 0)), (0.7, (60, 0, 0), "linear"), (1.2, (0, 0, 0)))
        a.rot(f"leg_b{side}2", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.7, (-10, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("tail", (0, (0, 0, 0)), (0.5, (-30, 0, 0)), (0.7, (-50, 0, 0)), (1.2, (0, 0, 0)))

    # bite: the head drawn back with the jaw gaping, then a lunge and a snap (lands at 0.25 s = 5 ticks)
    a = m.anim("bite", 0.5)
    a.rot("neck", (0, (0, 0, 0)), (0.15, (-18, 0, 0)), (0.25, (22, 0, 0), "linear"), (0.35, (18, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.15, (48, 0, 0)), (0.25, (0, 0, 0), "linear"), (0.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.15, (-10, 0, 0)), (0.25, (8, 0, 0), "linear"), (0.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.15, (0, 0, 1)), (0.25, (0, 0, -2), "linear"), (0.5, (0, 0, 0)))
    a.rot("ear_r", (0, (0, 0, 0)), (0.15, (-30, 0, 0)), (0.5, (0, 0, 0)))
    a.rot("ear_l", (0, (0, 0, 0)), (0.15, (-30, 0, 0)), (0.5, (0, 0, 0)))
