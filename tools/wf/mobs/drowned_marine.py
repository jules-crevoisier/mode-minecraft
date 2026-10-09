"""Drowned Marine (Fusilier noyé): a marine of the Dreadnought Wreck who never left his post, about 2 blocks tall.

Silhouette idea: the ship's marine guard, still on watch at the bottom of the sea. A bloated, grey-green drowned
corpse in the rags of a navy-blue marine tunic with two rows of tarnished brass buttons, white canvas cross-belts
with cartridge pouches, puttees wound round his shins and hobnailed boots. A dented steel brodie helmet crusted with
barnacles sits low over two glowing cyan eyes and a slack, weed-hung jaw. He carries a long service rifle with a
fixed bayonet at port arms, its stock swollen and the barrel streaked with rust. He takes one careful shot at you,
then lowers the bayonet and charges; up close he thrusts with it. He swims and breathes under water.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K
from . import sluice_drowned as D

NAVY = (36, 50, 88)
NAVY_L = (66, 82, 122)
NAVY_D = (20, 28, 54)
WEBBING = (196, 190, 160)
WEBBING_D = (140, 134, 104)
BRASS = (188, 150, 66)
BRASS_D = (120, 90, 40)
STEEL = (110, 116, 112)
STEEL_L = (160, 166, 158)
STEEL_D = (64, 68, 66)
PUTTEE = (98, 90, 66)
PUTTEE_D = (66, 60, 44)
BOOT = (40, 32, 28)
STOCK = (112, 74, 44)
STOCK_D = (74, 46, 26)
BLADE = (200, 206, 204)
RUST = D.RUST


def tunic(seed=0):
    """Navy wool gone dark with water: soft folds, the waterlogged drips and rot of the drowned."""
    return D.soaked(D.barnacles(K.cloth(NAVY, NAVY_D, seed=seed), seed + 1, 0.05), seed + 2, 0.2)


def puttee(face, x, y, w, h):
    if face in ("top", "bottom"):
        return PUTTEE_D
    return PUTTEE if (x + y) % 3 else PUTTEE_D                                               # spiral wraps


def build():
    m = Model("drowned_marine", seed=1277, shadow=0.55, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("shin_r", "leg_r", pivot=(0, 6, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("shin_l", "leg_l", pivot=(0, 6, 0))
    m.part("body", "bone", pivot=(0, -12, 0), rot=(8, 0, 0))
    m.part("head", "body", pivot=(0, -12, -0.5), rot=(-8, 0, 0))
    m.part("jaw", "head", pivot=(0, -1.5, -1))
    m.part("helmet", "head", pivot=(0, -6, 0), rot=(-6, 0, 4))
    m.part("arm_r", "body", pivot=(-5.5, -10.5, 0), rot=(-30, 0, 10))
    m.part("forearm_r", "arm_r", pivot=(0, 5.5, 0), rot=(-50, 0, 0))
    m.part("rifle", "forearm_r", pivot=(0, 5, -0.5), rot=(-40, 0, -50))
    m.part("arm_l", "body", pivot=(5.5, -10.5, 0), rot=(-50, -20, -10))
    m.part("forearm_l", "arm_l", pivot=(0, 5.5, 0), rot=(-50, 0, 0))

    # ------------------------------------------------------------------ legs: trousers, puttees, boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2, 0, -2, 4, 6, 4, D.soaked(K.cloth(NAVY_D, mul(NAVY_D, 0.7), seed=3 + sx), 4 + sx))
        m.box(shin, -2, 0, -2, 4, 4, 4, puttee)
        m.box(shin, -2.2, 4, -2.8, 4, 2, 5, {"*": BOOT, "top": mul(BOOT, 1.4)}, grow=0.2)
        m.box(shin, -2.3, 5.6, -3, 5, 1, 5, mix(BOOT, STEEL_D, 0.3), grow=0.0)                  # hobnailed sole

    # ------------------------------------------------------------------ body: tunic, buttons, cross-belts, pouches
    def front(f_, x, y, w, h):
        if f_ == "front" and x in (2, w - 3) and y % 3 == 1 and y < h - 2:
            return BRASS if K.h(x, y) % 3 else BRASS_D                                          # two rows of buttons
        return tunic(10)(f_, x, y, w, h)
    m.box("body", -4, -12, -2.5, 8, 12, 5, front)
    m.box("body", -4.5, -12.5, -3, 9, 2, 6, tunic(13))                                          # high collar and yoke
    m.box("body", -4.6, -12.6, -2.2, 2, 1, 4, BRASS_D)                                         # epaulette buttons
    m.box("body", 2.6, -12.6, -2.2, 2, 1, 4, BRASS_D)
    # white canvas cross-belts, crossing at the chest
    for i in range(6):
        m.box("body", -3.6 + i * 1.3, -11.5 + i * 1.8, -2.9, 1, 2, 1, WEBBING if i % 2 else WEBBING_D)
        m.box("body", 2.6 - i * 1.3, -11.5 + i * 1.8, -2.9, 1, 2, 1, WEBBING_D if i % 2 else WEBBING)
    m.box("body", -4.3, -2.5, -2.8, 8, 2, 5, {"*": WEBBING_D, "front": lambda f_, x, y, w, h: BRASS if x == w // 2 else WEBBING},
          grow=0.2)                                                                             # the waist belt
    for sx in (-1, 1):
        m.box("body", (-3.8 if sx < 0 else 1.3), -2.4, -3.6, 3, 2, 1, {"*": WEBBING_D, "top": WEBBING})  # cartridge pouches
    m.box("body", -3.6, -12, 2.2, 7, 6, 2, D.soaked(K.leather((84, 66, 44), seed=14), 15))       # the pack on his back
    m.box("body", -4.5, 0, -3, 9, 3, 6, D.soaked(K.cloth(NAVY, NAVY_D, seed=16), 17, 0.3), grow=0.05)  # tunic skirt

    # ------------------------------------------------------------------ head: drowned face, steel helmet
    eyes = {(1, 3), (5, 3)}

    def face(f_, x, y, w, h):
        if (x, y) in eyes:
            return D.EYE
        if (x, y) in {(1, 2), (5, 2), (2, 3), (4, 3)}:
            return mul(D.FLESH_D, 0.5)
        if y == 5 and x in (2, 3, 4):
            return mul(D.FLESH_D, 0.6)
        return D.flesh(20)(f_, x, y, w, h)
    m.box("head", -3.5, -6, -3.5, 7, 6, 7, {"front": face, "*": D.flesh(21)},
          glow={"front": lambda f_, x, y, w, h: D.EYE_L if (x, y) in eyes else None, "*": None})

    def jaw(f_, x, y, w, h):
        if f_ == "top":
            return (30, 22, 24)
        if f_ == "front" and y == 0 and x % 2 == 1:
            return D.SHELL
        return D.flesh(23)(f_, x, y, w, h)
    m.box("jaw", -3, 0, -2.5, 6, 2, 5, jaw)
    m.box("jaw", 0.5, 1.5, -2.6, 1, 2, 1, D.weed(24))
    m.box("jaw", -2, 0.5, -2.7, 4, 1, 1, WEBBING_D)                                             # the chin strap

    def steel(seed):
        def f(f_, x, y, w, h):
            if f_ == "bottom":
                return STEEL_D
            c = STEEL_L if f_ == "top" and (x + y) % 4 == 0 else STEEL
            if K.h(x, y, seed) % 6 == 0:
                c = mix(c, RUST, 0.6)
            if f_ != "top" and y == h - 1:
                c = STEEL_D
            return c
        return D.barnacles(f, seed + 1, 0.16)
    m.box("helmet", -3.5, -2, -3.5, 7, 2, 7, steel(30))                                         # the bowl
    m.box("helmet", -2.5, -3, -2.5, 5, 1, 5, steel(31))
    m.box("helmet", -5, 0, -5, 10, 1, 10, steel(32))                                            # the wide brim
    m.box("helmet", 3, -2.5, -1, 1, 1, 2, D.WEED)                                               # weed caught on it

    # ------------------------------------------------------------------ arms: sodden sleeves, swollen hands
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -1.8, -1, -1.8, 4, 6, 4, D.barnacles(tunic(40 + sx), 42 + sx, 0.12))
        m.box(fore, -1.8, 0, -1.8, 4, 4, 4, tunic(43 + sx))
        m.box(fore, -2, 2.6, -2, 4, 1, 4, BRASS_D, grow=0.1)                                     # cuff buttons
        m.box(fore, -1.6, 4, -1.6, 3, 3, 3, D.flesh(45 + sx), grow=0.2)

    # ------------------------------------------------------------------ the rifle: the hand grips it at y = 0, the stock
    # runs back along the forearm (-y), the barrel and bayonet forward (+y)
    def stock(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return STOCK_D
        c = STOCK if (x + K.h(y // 3, 7)) % 3 else STOCK_D
        return mix(c, D.ROT, 0.3) if K.h(x, y, 8) % 7 == 0 else c
    m.box("rifle", -1, -7, -1.5, 2, 6, 3, stock)                                                # butt stock
    m.box("rifle", -1, -8, -2, 2, 1, 4, STEEL_D)                                                # butt plate
    m.box("rifle", -1, -1, -1, 2, 3, 2, stock)                                                  # wrist and grip
    m.box("rifle", -0.5, 1, -1.2, 1, 2, 1, STEEL_D)                                             # trigger guard
    m.box("rifle", -1, 2, -1, 2, 8, 2, stock)                                                   # fore-end
    m.box("rifle", -0.5, 1, 0.6, 1, 4, 1, {"*": STEEL, "back": STEEL_L})                       # the bolt and receiver
    m.box("rifle", -0.5, 10, -0.5, 1, 5, 1, {"*": STEEL, "front": mix(STEEL, RUST, 0.5)})      # barrel
    m.box("rifle", -0.8, 9, -0.8, 1, 1, 1, BRASS_D, grow=0.3)                                   # the barrel band
    m.box("rifle", -0.5, 15, -0.5, 1, 1, 1, STEEL_D, grow=0.15)                                 # bayonet ring
    m.box("rifle", -0.5, 16, -0.5, 1, 8, 1, {"*": BLADE, "left": STEEL_L, "right": STEEL_L,
                                             "bottom": (240, 244, 240)})                        # the long bayonet
    m.box("rifle", -0.5, 6, -1.6, 1, 1, 1, WEBBING_D)                                           # sling swivel

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.2)
    idle.pos("body", (0, (0, 0, 0)), (1.6, (0, -0.4, 0)), (3.2, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.6, (2, 0, -2)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (4, 14, 0)), (2.2, (0, -12, 4)), (3.2, (0, 0, 0)))
    idle.rot("jaw", (0, (10, 0, 0)), (1.6, (18, 0, 0)), (3.2, (10, 0, 0)))
    idle.rot("rifle", (0, (0, 0, 0)), (1.6, (-3, 0, 2)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.6, (-22, 0, 0)), (1.2, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.6, (22, 0, 0)), (1.2, (-22, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.9, (28, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.3, (28, 0, 0)), (0.6, (0, 0, 0)), (1.2, (0, 0, 0)))
    walk.rot("body", (0, (0, 0, 3)), (0.6, (0, 0, -3)), (1.2, (0, 0, 3)))
    walk.pos("body", (0, (0, 0, 0)), (0.3, (0, 0.6, 0)), (0.6, (0, 0, 0)), (0.9, (0, 0.6, 0)), (1.2, (0, 0, 0)))
    walk.rot("head", (0, (0, 0, -4)), (0.6, (0, 0, 4)), (1.2, (0, 0, -4)))

    # shot: the rifle swung up into the shoulder, the left hand under the fore-end, head down over the sights (aims
    # from 0.35 s; the aim locks at 0.75 s), fires at 1.0 s = 20 ticks: the muzzle kicks up and he rocks back
    a = m.anim("shot", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.35, (-82, -12, 0)), (1.0, (-82, -12, 0)), (1.05, (-96, -12, 0), "linear"), (1.25, (-84, -12, 0)),
          (1.6, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.35, (50, 0, 0)), (1.0, (50, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("rifle", (0, (0, 0, 0)), (0.35, (40, 0, 50)), (1.0, (40, 0, 50)), (1.05, (30, 0, 50), "linear"), (1.25, (38, 0, 50)),
          (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.35, (-50, 30, 0)), (1.0, (-50, 30, 0)), (1.05, (-60, 30, 0)), (1.6, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.35, (40, 0, 0)), (1.0, (40, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (-4, 20, 0)), (1.0, (-4, 20, 0)), (1.05, (-10, 18, 0), "linear"), (1.3, (-4, 16, 0)),
          (1.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.05, (0, 0, 1.5), "linear"), (1.3, (0, 0, 0.5)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.35, (10, -18, 0)), (1.0, (10, -18, 0)), (1.1, (0, -14, 0)), (1.6, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.35, (14, 0, 0)), (1.3, (14, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.35, (-14, 0, 0)), (1.3, (-14, 0, 0)), (1.6, (0, 0, 0)))

    # charge: the bayonet levelled at the hip and he drops into a crouch (0.5 s telegraph), then runs at the prey
    # (from 0.5 s = 10 ticks), legs pumping, until he stumbles to a stop
    a = m.anim("charge", 1.5)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (-40, 0, 0)), (1.3, (-40, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.4, (-10, 0, 0)), (1.3, (-10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("rifle", (0, (0, 0, 0)), (0.4, (40, 0, 50)), (1.3, (40, 0, 50)), (1.5, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (-30, 40, 0)), (1.3, (-30, 40, 0)), (1.5, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.4, (10, 0, 0)), (1.3, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (24, 10, 0)), (0.5, (26, 10, 0)), (1.3, (26, 10, 0)), (1.5, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, -2, 0)), (0.5, (0, -2, 0)), (0.6, (0, -1, 0)), (0.7, (0, -1.6, 0)), (0.8, (0, -1, 0)),
          (0.9, (0, -1.6, 0)), (1.0, (0, -1, 0)), (1.1, (0, -1.6, 0)), (1.2, (0, -1, 0)), (1.5, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.4, (-20, -10, 0)), (1.3, (-20, -10, 0)), (1.5, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.4, (-20 * s, 0, 0)), (0.5, (-20 * s, 0, 0)), (0.7, (40 * s, 0, 0)), (0.9, (-40 * s, 0, 0)),
              (1.1, (40 * s, 0, 0)), (1.3, (-30 * s, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("shin_r", (0, (0, 0, 0)), (0.4, (30, 0, 0)), (0.7, (10, 0, 0)), (0.9, (50, 0, 0)), (1.1, (10, 0, 0)), (1.5, (0, 0, 0)))
    a.rot("shin_l", (0, (0, 0, 0)), (0.4, (10, 0, 0)), (0.7, (50, 0, 0)), (0.9, (10, 0, 0)), (1.1, (50, 0, 0)), (1.5, (0, 0, 0)))

    # thrust: the rifle drawn back along his side (0.45 s telegraph), then the bayonet driven forward (lands at 0.45 s
    # = 9 ticks)
    a = m.anim("thrust", 1.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.4, (30, 30, 0)), (0.45, (32, 30, 0)), (0.55, (-40, 20, 0), "linear"), (0.7, (-38, 20, 0)),
          (1.0, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.4, (-40, 0, 0)), (0.55, (30, 0, 0), "linear"), (0.7, (30, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("rifle", (0, (0, 0, 0)), (0.4, (40, 0, 50)), (0.55, (40, 0, 50)), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.4, (20, 40, 0)), (0.55, (-30, 40, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.4, (0, 0, 0)), (0.55, (40, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.4, (-6, 30, 0)), (0.55, (16, 0, 0), "linear"), (0.7, (14, 0, 0)), (1.0, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.4, (0, 0, 2)), (0.55, (0, -0.5, -3), "linear"), (0.7, (0, -0.5, -3)), (1.0, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.55, (20, 0, 0)), (0.7, (20, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.55, (-26, 0, 0)), (0.7, (-26, 0, 0)), (1.0, (0, 0, 0)))
