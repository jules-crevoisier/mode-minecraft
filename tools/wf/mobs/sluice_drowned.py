"""Sluice Drowned (Noyé de l'écluse): the drowned lock-keeper of the Great Aqueduct, about 2 blocks tall.

Silhouette idea: the keeper who went down with his sluice. A hunched, bloated corpse of grey-green waterlogged flesh
in a sodden canvas work coat and rubber waders, a faded oilskin sou'wester dripping over a sunken face with two
glowing cyan eyes and a slack jaw. Barnacles crust his shoulders, weed hangs off his elbows, a coil of rotten rope is
slung over his left shoulder and a brass keeper's badge still shines on his chest. In his right fist a long boat-hook
taller than himself: an ash pole bound with tarred twine, an iron hook and a spike on top. He hooks his prey from
afar and hauls it to him, jabs with the spike and sweeps the hook low at the legs.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

FLESH = (104, 142, 128)
FLESH_L = (148, 184, 166)
FLESH_D = (62, 94, 88)
ROT = (82, 104, 70)
EYE = (96, 236, 230)
EYE_L = (220, 255, 250)
COAT = (64, 80, 96)
COAT_D = (38, 48, 60)
COAT_L = (96, 112, 124)
OIL = (176, 146, 58)
OIL_D = (118, 94, 36)
OIL_L = (214, 186, 96)
RUBBER = (40, 42, 40)
RUBBER_L = (72, 76, 70)
WEED = (54, 110, 64)
WEED_D = (32, 74, 44)
ROPE = (150, 124, 82)
ROPE_D = (100, 80, 52)
BRASS = (196, 156, 70)
BRASS_D = (128, 94, 40)
IRON = (96, 92, 92)
IRON_L = (150, 146, 140)
IRON_D = (50, 46, 46)
RUST = (138, 78, 44)
WOOD = (122, 94, 62)
WOOD_D = (80, 60, 38)
SHELL = (206, 200, 182)
SHELL_D = (150, 144, 128)
WATER = (120, 190, 220)


def soaked(base, seed=0, wet=0.18):
    """Anything waterlogged: a dark wet line creeping down from the top, drips, green slime blotches."""
    def f(face, x, y, w, h):
        c = K.call(base, face, x, y, w, h)
        if c is None or face == "bottom":
            return c
        r = K.h(x, y, seed) % 100
        if face != "top" and K.h(x, seed) % 5 == 0 and y > h // 3:
            c = mul(c, 0.78)                                                   # a drip streak running down
        if r < wet * 30:
            c = mix(c, ROT, 0.55)
        elif r > 97:
            c = mix(c, WATER, 0.35)
        return c
    return f


def flesh(seed=0):
    """Bloated drowned skin: mottled grey-green, darker blotches, pale swollen highlights."""
    def f(face, x, y, w, h):
        r = K.h(x, y, seed) % 11
        c = FLESH
        if r == 0:
            c = FLESH_D
        elif r == 1:
            c = FLESH_L
        elif r == 2:
            c = mix(FLESH, ROT, 0.5)
        return mul(c, 1.04 - 0.12 * y / max(1, h))
    return f


def barnacles(base, seed=0, amount=0.2):
    """Barnacle clusters: off-white cones with a dark hole in the middle."""
    def f(face, x, y, w, h):
        c = K.call(base, face, x, y, w, h)
        if c is None or face == "bottom":
            return c
        r = K.h(x // 2, y // 2, seed) % 100
        if r < amount * 100:
            return SHELL_D if (x + y) % 2 else SHELL
        return c
    return f


def weed(seed=0):
    """Hanging weed: green strands with ragged, see-through ends."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return WEED_D
        if y >= h - 2 and (x + seed + y) % 2 == 0:
            return None
        return WEED if (x + seed) % 2 else WEED_D
    return f


def rope(seed=0):
    def f(face, x, y, w, h):
        return ROPE if (x + y + seed) % 3 else ROPE_D
    return f


def build():
    m = Model("sluice_drowned", seed=821, shadow=0.55, walk_speed=0.9, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton (hunched forward)
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("shin_r", "leg_r", pivot=(0, 6, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("shin_l", "leg_l", pivot=(0, 6, 0))
    m.part("body", "bone", pivot=(0, -12, 0), rot=(14, 0, 0))
    m.part("head", "body", pivot=(0, -12, -1), rot=(-12, 0, 0))
    m.part("jaw", "head", pivot=(0, -1.5, -1))
    m.part("brim", "head", pivot=(0, -6.5, 0))
    m.part("arm_r", "body", pivot=(-5.5, -10.5, 0), rot=(-10, 0, 14))
    m.part("forearm_r", "arm_r", pivot=(0, 5.5, 0), rot=(-40, 0, 0))
    m.part("pole", "forearm_r", pivot=(0, 5.5, -0.5), rot=(42, 0, -28))
    m.part("arm_l", "body", pivot=(5.5, -10.5, 0), rot=(-6, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 5.5, 0), rot=(-30, 0, 0))
    m.part("weed_r", "arm_r", pivot=(-1, 4, 2))
    m.part("weed_l", "arm_l", pivot=(1, 4, 2))
    m.part("key", "body", pivot=(-3.5, -1, -2.5), rot=(0, 0, 10))
    m.part("coattail", "body", pivot=(0, 0, 0))

    # ------------------------------------------------------------------ legs: rubber waders up to the thigh
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"

        def wader(f_, x, y, w, h, sx=sx):
            if f_ == "top":
                return RUBBER_L
            c = RUBBER_L if x == w // 2 and f_ == "front" else RUBBER
            if K.h(x, y, 5 + sx) % 9 == 0:
                c = mix(c, ROT, 0.6)
            return c
        m.box(leg, -2, 0, -2, 4, 6, 4, soaked(K.cloth(COAT_D, mul(COAT_D, 0.7), seed=3 + sx), 4 + sx))
        m.box(leg, -2.2, 3, -2.2, 4, 3, 4, wader, grow=0.2)                                    # wader tops
        m.box(shin, -2, 0, -2, 4, 5, 4, wader)
        m.box(shin, -2.5, 5, -3.2, 5, 1, 6, {"top": RUBBER_L, "*": RUBBER})  # boot sole
        m.box(shin, -2.3, 2, -2.3, 4, 1, 4, mix(RUBBER, BRASS_D, 0.3), grow=0.1)               # strap buckle line

    # ------------------------------------------------------------------ body: canvas coat, badge, belt, rope coil
    def coat(f_, x, y, w, h):
        if f_ == "front" and x == w // 2:
            return COAT_D if y % 3 else BRASS_D                                               # buttons down the front
        return K.cloth(COAT, COAT_D, seed=10)(f_, x, y, w, h)
    m.box("body", -4, -12, -2.5, 8, 12, 5, soaked(barnacles(coat, 11, 0.06), 12))
    m.box("body", -4.5, -12.5, -3, 9, 3, 6, barnacles(soaked(K.cloth(COAT_L, COAT, seed=13), 14), 15, 0.3))  # shoulder yoke

    def belt(f_, x, y, w, h):
        if f_ == "front" and abs(x - w // 2) <= 0:
            return BRASS
        return mix(RUBBER, ROPE_D, 0.3) if (x + y) % 2 else RUBBER
    m.box("body", -4.3, -2, -2.8, 8, 2, 5, belt, grow=0.2)

    def coattail(f_, x, y, w, h):
        if f_ in ("front", "back", "left", "right") and y == h - 1 and (x * 7 + 3) % 4 == 0:
            return None
        return soaked(K.cloth(COAT, COAT_D, seed=16), 17, 0.3)(f_, x, y, w, h)
    m.box("coattail", -4.5, 0, -3, 9, 5, 6, coattail, grow=0.1)

    # the keeper's badge: a little brass sluice-gate on the left breast
    badge = {(0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (2, 2)}
    m.box("body", 0.8, -10, -3.1, 3, 3, 1, {"front": lambda f_, x, y, w, h: BRASS if (x, y) in badge else BRASS_D,
                                             "*": BRASS_D})
    # the rope coil slung from the left shoulder to the right hip
    for i in range(6):
        m.box("body", 3.5 - i * 1.5, -12.5 + i * 2, -3.4, 2, 2, 1, rope(i))
    for i in range(6):
        m.box("body", 3.5 - i * 1.5, -12.5 + i * 2, 2.4, 2, 2, 1, rope(i + 3))
    m.box("body", 3.4, -13.4, -2, 2, 1, 4, rope(9))                                            # over the shoulder

    # the big T-handled sluice key hanging from the belt
    m.box("key", -0.5, 0, -0.5, 1, 7, 1, {"*": RUST, "front": IRON})
    m.box("key", -2, 6.5, -0.5, 4, 1, 1, {"*": IRON_D, "top": IRON_L})
    m.box("key", -1, -0.5, -1, 2, 1, 2, IRON_D)

    # ------------------------------------------------------------------ head: sunken face, slack jaw, sou'wester
    eyes = {(1, 3), (5, 3)}

    def face(f_, x, y, w, h):
        if (x, y) in eyes:
            return EYE
        if (x, y) in {(1, 2), (5, 2), (2, 3), (4, 3)}:
            return mul(FLESH_D, 0.5)                                                         # sunken sockets
        if y == 4 and x == 3:
            return FLESH_D                                                                   # the nose, mostly gone
        if y == 5 and x in (2, 3, 4):
            return mul(FLESH_D, 0.6)
        return flesh(20)(f_, x, y, w, h)
    m.box("head", -3.5, -6, -3.5, 7, 6, 7, {"front": face, "*": flesh(21)},
          glow={"front": lambda f_, x, y, w, h: EYE_L if (x, y) in eyes else None, "*": None})
    m.box("head", -3.6, -1.2, -3.6, 7, 1, 7, flesh(22), grow=0.0)                            # upper lip line
    # the slack jaw hanging open: a dark mouth inside, a few teeth
    def jaw(f_, x, y, w, h):
        if f_ == "top":
            return (30, 22, 24)
        if f_ == "front" and y == 0 and x % 2 == 1:
            return SHELL
        return flesh(23)(f_, x, y, w, h)
    m.box("jaw", -3, 0, -2.5, 6, 2, 5, jaw)
    m.box("jaw", -1, 1.5, -2.6, 2, 2, 1, weed(24))                                           # weed hanging from the chin
    # oilskin sou'wester: a soft crown and a long brim sloping down at the back
    def oil(seed):
        def f(f_, x, y, w, h):
            if f_ == "bottom":
                return OIL_D
            c = OIL_L if f_ == "top" and (x + y) % 5 == 0 else OIL
            if K.h(x, y, seed) % 7 == 0:
                c = mix(c, ROT, 0.4)
            if f_ != "top" and K.h(x, seed) % 3 == 0 and y >= h - 2:
                c = OIL_D
            return c
        return f
    m.box("head", -3.8, -8, -3.8, 8, 3, 8, oil(25))
    m.box("head", -3, -9, -3, 6, 1, 6, oil(26))
    m.box("brim", -5, 0, -5, 10, 1, 10, oil(27))
    m.box("brim", -4, 0.5, 4, 8, 1, 3, oil(28), grow=0.0)                                      # long rear flap
    # drips off the brim
    for i, (x, z) in enumerate(((-4.5, -4.5), (3.5, -4.7), (-4.6, 2), (4.0, 3))):
        m.box("brim", x, 1, z, 1, 1 + i % 2, 1, (*WATER, 190), glow={"*": None})

    # ------------------------------------------------------------------ arms: sodden sleeves, swollen hands, weed
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.8, -1, -1.8, 4, 6, 4, barnacles(soaked(K.cloth(COAT, COAT_D, seed=40 + sx), 41 + sx), 42 + sx, 0.18))
        m.box(fore, -1.8, 0, -1.8, 4, 4, 4, soaked(K.cloth(COAT_L, COAT, seed=43 + sx), 44 + sx))
        m.box(fore, -1.6, 4, -1.6, 3, 3, 3, flesh(45 + sx), grow=0.3)                         # swollen fist
        m.box(f"weed_{side}", -1, 0, 0, 2, 5, 1, weed(46 + sx))
    # the left hand's fingers: long and webbed with rot, hooked
    m.box("forearm_l", -1.5, 7, -1.5, 1, 2, 1, FLESH_D)
    m.box("forearm_l", 0.5, 7, -1.5, 1, 2, 1, FLESH_D)

    # ------------------------------------------------------------------ the boat-hook
    def pole(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return WOOD_D
        if y % 7 in (0, 1):
            return mix(RUBBER, ROPE, 0.25)                                                   # tarred twine bindings
        return WOOD if (x + y // 3) % 2 else WOOD_D
    m.box("pole", -0.5, -22, -0.5, 1, 28, 1, pole)
    m.box("pole", -0.8, 5, -0.8, 1, 1, 1, IRON_D, grow=0.3)                                    # iron butt cap
    # the head: an iron socket, the straight spike and the curled hook
    m.box("pole", -1, -25, -1, 2, 4, 2, {"*": IRON, "top": IRON_L, "front": RUST})
    m.box("pole", -0.5, -30, -0.5, 1, 5, 1, {"*": IRON_L, "top": (230, 230, 226)})            # the spike
    m.box("pole", -0.5, -27, -3, 1, 1, 2, {"*": IRON, "top": IRON_L})                         # the hook arm
    m.box("pole", -0.5, -27, -4, 1, 4, 1, {"*": IRON, "front": IRON_L})                        # down
    m.box("pole", -0.5, -24, -3, 1, 1, 1, IRON_L)                                              # the barb curling back
    m.box("pole", -0.6, -26, -4.2, 1, 1, 1, RUST, grow=0.1)

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.4)
    idle.pos("body", (0, (0, 0, 0)), (1.7, (0, -0.5, 0)), (3.4, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.7, (3, 0, 2)), (3.4, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.2, (6, 10, -6)), (2.4, (0, -6, 4)), (3.4, (0, 0, 0)))
    idle.rot("jaw", (0, (12, 0, 0)), (1.7, (20, 0, 0)), (3.4, (12, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.7, (6, 0, -3)), (3.4, (0, 0, 0)))
    idle.rot("weed_r", (0, (0, 0, 0)), (1.7, (12, 0, 4)), (3.4, (0, 0, 0)))
    idle.rot("weed_l", (0, (0, 0, 0)), (1.7, (12, 0, -4)), (3.4, (0, 0, 0)))
    idle.rot("key", (0, (0, 0, 0)), (1.7, (6, 0, -6)), (3.4, (0, 0, 0)))
    idle.rot("pole", (0, (0, 0, 0)), (1.7, (-3, 0, 2)), (3.4, (0, 0, 0)))

    walk = m.anim("walk", 1.3)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.65, (-22, 0, 0)), (1.3, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.65, (22, 0, 0)), (1.3, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.95, (30, 0, 0)), (1.3, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.3, (30, 0, 0)), (0.65, (0, 0, 0)), (1.3, (0, 0, 0)))
    walk.rot("body", (0, (2, 0, 5)), (0.65, (2, 0, -5)), (1.3, (2, 0, 5)))                    # a lurching sway
    walk.pos("body", (0, (0, 0, 0)), (0.32, (0, 0.6, 0)), (0.65, (0, 0, 0)), (0.97, (0, 0.6, 0)), (1.3, (0, 0, 0)))
    walk.rot("arm_l", (0, (16, 0, 0)), (0.65, (-16, 0, 0)), (1.3, (16, 0, 0)))
    walk.rot("arm_r", (0, (-6, 0, 0)), (0.65, (6, 0, 0)), (1.3, (-6, 0, 0)))
    walk.rot("head", (0, (0, 0, -6)), (0.65, (0, 0, 6)), (1.3, (0, 0, -6)))
    walk.rot("coattail", (0, (6, 0, 0)), (0.65, (10, 0, 0)), (1.3, (6, 0, 0)))
    walk.rot("weed_r", (0, (16, 0, 0)), (0.65, (4, 0, 0)), (1.3, (16, 0, 0)))
    walk.rot("weed_l", (0, (4, 0, 0)), (0.65, (16, 0, 0)), (1.3, (4, 0, 0)))
    walk.rot("key", (0, (10, 0, 0)), (0.65, (-10, 0, 0)), (1.3, (10, 0, 0)))

    # jab: the pole drawn back along the arm (0.4 s), the spike driven straight forward (lands at 0.45 s = 9 ticks)
    a = m.anim("jab", 0.9)
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (20, 0, -10)), (0.45, (-70, 0, -10), "linear"), (0.6, (-68, 0, -10)), (0.9, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.35, (-40, 0, 0)), (0.45, (10, 0, 0), "linear"), (0.6, (10, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("pole", (0, (0, 0, 0)), (0.2, (60, 0, 28)), (0.35, (84, 0, 28)), (0.45, (124, 0, 28), "linear"), (0.6, (124, 0, 28)), (0.9, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (-6, 20, 0)), (0.45, (12, -10, 0), "linear"), (0.6, (10, -8, 0)), (0.9, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.35, (0, 0, 1.5)), (0.45, (0, -0.5, -2.5), "linear"), (0.6, (0, -0.5, -2.5)),
          (0.9, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.45, (20, 0, 0)), (0.6, (20, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.45, (-24, 0, 0)), (0.6, (-24, 0, 0)), (0.9, (0, 0, 0)))
    a.rot("jaw", (0, (12, 0, 0)), (0.35, (30, 0, 0)), (0.9, (12, 0, 0)))

    # hook: the boat-hook raised high and circled over the hat (0.8 s telegraph), cast out at full stretch (lands at
    # 0.8 s = 16 ticks), then hauled back hand over hand (the pull)
    a = m.anim("hook", 1.7)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-150, 0, 20)), (0.5, (-160, 30, 10)), (0.7, (-170, -20, 20)),
          (0.8, (-70, 0, -10), "linear"), (0.95, (-68, 0, -10)), (1.3, (-20, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.3, (-30, 0, 0)), (0.7, (-30, 0, 0)), (0.8, (20, 0, 0), "linear"),
          (1.3, (-60, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("pole", (0, (0, 0, 0)), (0.3, (130, 0, 28)), (0.7, (130, 0, 28)), (0.8, (110, 0, 28), "linear"), (1.0, (112, 0, 28)),
          (1.3, (118, 0, 28)), (1.7, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (-14, 16, 0)), (0.7, (-18, 24, 0)), (0.8, (16, -14, 0), "linear"),
          (0.95, (14, -12, 0)), (1.3, (-12, 10, 0)), (1.7, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.7, (-30, 0, -30)), (0.8, (-50, 0, -10)), (1.0, (-70, 0, 6)), (1.3, (10, 0, 0)),
          (1.7, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.7, (-16, -10, 0)), (0.8, (6, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("jaw", (0, (12, 0, 0)), (0.7, (34, 0, 0)), (0.8, (40, 0, 0)), (1.7, (12, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.7, (0, 0.5, 1.5)), (0.8, (0, -1, -2), "linear"), (1.0, (0, -1, -2)),
          (1.3, (0, 0, 2)), (1.7, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.7, (14, 0, 0)), (0.8, (-20, 0, 0)), (1.3, (16, 0, 0)), (1.7, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.7, (-10, 0, 0)), (0.8, (20, 0, 0)), (1.3, (-12, 0, 0)), (1.7, (0, 0, 0)))

    # sweep: the hook swung out wide behind him low to the right (0.65 s telegraph), then swept across at knee height
    # (lands at 0.65 s = 13 ticks)
    a = m.anim("sweep", 1.3)
    a.rot("body", (0, (0, 0, 0)), (0.55, (20, 60, 0)), (0.65, (20, 55, 0)), (0.85, (22, -60, 0), "linear"),
          (1.0, (20, -55, 0)), (1.3, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-40, 0, 60)), (0.85, (-50, 0, -10), "linear"), (1.0, (-46, 0, -10)),
          (1.3, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.55, (0, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("pole", (0, (0, 0, 0)), (0.55, (95, 0, 28)), (0.85, (100, 0, 28)), (1.0, (100, 0, 28)), (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.55, (-20, 0, -40)), (0.85, (10, 0, -20)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (0, -50, 0)), (0.85, (0, 40, 0)), (1.3, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.55, (0, -2, 0)), (0.85, (0, -2, -1)), (1.3, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.55, (-20 * s, 0, 8 * s)), (0.85, (20 * s, 0, 8 * s)), (1.3, (0, 0, 0)))
