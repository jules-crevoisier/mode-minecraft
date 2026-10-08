"""Frozen Huscarl (Huscarl gelé): the dead house-guard of the Glacier Hall, about 2.1 blocks tall.

Silhouette idea: a stocky shield-wall warrior who froze standing at his post and never fell. A broad mail-clad body
under a grey wolf-fur mantle, a faded crimson tunic hem, a round iron spangenhelm with spectacle eye-guards over two
cold blue eyes, a hoarfrost beard dripping icicles. The big round shield on his LEFT arm (crimson and white, an iron
boss, a frost-crusted rim and icicles along its lower edge) covers his front: hits from the front glance off it. In
his RIGHT fist a bearded hand-axe with a glowing frost edge; a cluster of ice crystals has grown out of his right
shoulder. He chops overhead, punches with the shield boss and cleaves wide with a freezing sweep.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

SKIN = (132, 158, 176)
SKIN_D = (88, 110, 132)
MAIL = (126, 132, 142)
MAIL_D = (66, 70, 82)
IRON = (104, 110, 122)
IRON_L = (170, 178, 190)
IRON_D = (52, 56, 66)
RIME = (214, 236, 248)
RIME_D = (156, 196, 222)
ICE = (150, 210, 240)
ICE_L = (228, 248, 255)
ICE_D = (84, 146, 200)
GLOW = (130, 230, 255)
GLOW_L = (222, 252, 255)
FUR = (136, 130, 122)
FUR_L = (196, 192, 184)
FUR_D = (84, 78, 72)
WOOL = (124, 36, 40)
WOOL_D = (78, 22, 28)
LEATHER = (92, 62, 42)
LEATHER_D = (58, 38, 26)
WOOD = (112, 82, 54)
WOOD_D = (72, 52, 34)
BRASS = (198, 158, 70)


def frosted(base, seed=0, amount=0.22):
    """Rime grown over anything: white-blue crystals crusting the top faces and the upper rows of the sides, thinning
    toward the bottom."""
    def f(face, x, y, w, h):
        c = base(face, x, y, w, h) if callable(base) else base
        if c is None:
            return None
        if face == "bottom":
            return c
        lim = amount * (1.6 if face == "top" else max(0.0, 1.0 - y / max(1, h) * 1.4))
        r = K.h(x, y, seed, K.h(face == "front", face == "left")) % 1000 / 1000
        if r < lim * 0.55:
            return RIME
        if r < lim:
            return mix(c, RIME_D, 0.6)
        return c
    return f


def mail(seed=0):
    """Riveted mail: rows of rings, dark gaps, lit ring tops, rust freckles."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return MAIL_D
        ring = (x + (y % 2)) % 2 == 0
        c = MAIL if ring else MAIL_D
        if ring and y % 2 == 0:
            c = mix(c, (220, 226, 236), 0.22)
        if K.h(x, y, seed) % 29 == 0:
            c = mix(c, (140, 86, 50), 0.5)
        return mul(c, 1.04 - 0.16 * y / max(1, h))
    return f


def fur(seed=0):
    """Wolf fur: tufts of three greys hanging in strands, a ragged lower edge."""
    def f(face, x, y, w, h):
        if face not in ("top", "bottom") and y == h - 1 and (x + seed) % 3 == 0:
            return None
        r = K.h(x, y // 2, seed) % 5
        c = (FUR, FUR_L, FUR_D, FUR, mix(FUR, FUR_L, 0.5))[r]
        if face == "top":
            c = mix(c, RIME, 0.3) if (x + y) % 3 == 0 else c
        return c
    return f


def iron(seed=0, rivets=True):
    """Dented iron: a lit top row, a dark rim, a vertical sheen and rivets."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return IRON_D
        if face == "top":
            return mix(IRON, IRON_L, 0.35)
        if w > 2 and h > 2:
            if y == 0:
                return IRON_L
            if x in (0, w - 1) or y == h - 1:
                return IRON_D
            if rivets and y == 1 and x % 3 == 1:
                return BRASS
        c = mul(IRON, 1.08 - 0.25 * y / max(1, h) + (0.12 if x == w // 3 else 0.0))
        return mul(c, 0.9) if K.h(x, y, seed) % 17 == 0 else c
    return f


def ice(seed=0):
    """Clear ice: light facets, a darker core, a white-hot tip."""
    def f(face, x, y, w, h):
        if face == "top":
            return ICE_L
        if face == "bottom":
            return ICE_D
        k = (x + y + seed) % 4
        c = (ICE, ICE_L, ICE, ICE_D)[k]
        return mix(c, ICE_L, 0.5) if y == 0 else c
    return f


def ice_glow(seed=0):
    return {"top": GLOW_L, "*": lambda f_, x, y, w, h: GLOW if (x + y + seed) % 4 == 1 else None}


def build():
    m = Model("frozen_huscarl", seed=611, shadow=0.6, walk_speed=1.1, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2.3, -13, 0))
    m.part("shin_r", "leg_r", pivot=(0, 7, 0))
    m.part("leg_l", "bone", pivot=(2.3, -13, 0))
    m.part("shin_l", "leg_l", pivot=(0, 7, 0))
    m.part("body", "bone", pivot=(0, -13, 0))
    m.part("head", "body", pivot=(0, -12, -0.5))
    m.part("beard", "head", pivot=(0, -1.5, -3.6), rot=(8, 0, 0))
    m.part("arm_r", "body", pivot=(-5.8, -10.5, 0), rot=(0, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(-0.3, 5, 0), rot=(-28, 0, 0))
    m.part("axe", "forearm_r", pivot=(-0.3, 6, -0.3), rot=(72, 0, 0))
    m.part("arm_l", "body", pivot=(5.8, -10.5, 0), rot=(-18, 0, -6))
    m.part("forearm_l", "arm_l", pivot=(0.3, 5, 0), rot=(-62, 0, 0))
    m.part("shield", "forearm_l", pivot=(0.6, 3.5, -2.6), rot=(62, -14, 0))
    m.part("crystals", "body", pivot=(-4, -12, 1.5), rot=(-14, 0, -24))

    # ------------------------------------------------------------------ legs: wool breeches, leg wraps, fur boots
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -2, 0, -2, 4, 7, 4, K.cloth(WOOL_D, mul(WOOL_D, 0.7), seed=3 + sx))
        m.box(shin, -2, 0, -2, 4, 4, 4, frosted(lambda f_, x, y, w, h: LEATHER_D if (x + y) % 3 == 0 else LEATHER, 5 + sx))
        m.box(shin, -2.5, 3, -2.5, 5, 2, 5, fur(7 + sx))                                 # fur cuff
        m.box(shin, -2.5, 5, -3.5, 5, 1, 6, {"top": LEATHER, "*": LEATHER_D})  # boot sole and toe
        m.box(shin, -2.2, 0.5, -2.3, 4, 1, 4, LEATHER_D, grow=0.05)                       # cross-garter

    # ------------------------------------------------------------------ body: hauberk, belt, tunic hem, mantle
    m.box("body", -4.5, -12, -2.5, 9, 12, 5, frosted(mail(10), 11, 0.18))
    m.box("body", -4.8, -1.5, -2.8, 9, 6, 5, frosted(mail(12), 13, 0.08), grow=0.3)       # mail skirt over the hips

    def hem(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return WOOL_D
        if y == h - 1 and (x + 1) % 3 == 0:
            return None
        return K.cloth(WOOL, WOOL_D, seed=14)(f_, x, y, w, h)
    m.box("body", -5, 3.5, -3, 10, 2, 6, hem, grow=0.2)                                   # crimson tunic hem

    def belt(f_, x, y, w, h):
        if f_ == "front" and abs(x - w // 2) <= 1:
            return BRASS if (x, y) != (w // 2, 1) else LEATHER_D                            # the buckle
        return LEATHER if y % 2 == 0 or f_ != "front" else LEATHER_D
    m.box("body", -5, -2, -3, 10, 2, 6, belt, grow=0.15)
    m.box("body", 2, -1, -3.6, 3, 4, 1, {"*": LEATHER_D, "front": lambda f_, x, y, w, h: BRASS if y == 0 else LEATHER})  # pouch
    # the wolf-fur mantle over the shoulders, a wolf tail hanging down the back
    m.box("body", -5.5, -13, -3.5, 11, 3, 7, fur(15))
    m.box("body", -4.5, -10, 2.2, 9, 5, 1, fur(16))
    m.box("body", -1, -6, 3, 2, 7, 1, fur(17))
    # chest straps of the shield baldric, a brass knot at the crossing
    m.box("body", -4.5, -11, -2.9, 9, 1, 1, LEATHER_D, grow=0.05)
    m.box("body", -1, -8, -3.2, 2, 2, 1, {"*": BRASS, "front": lambda f_, x, y, w, h: BRASS if (x + y) % 2 else (150, 110, 40)})

    # ice crystals grown out of the right shoulder blade
    for i, (x, z, hgt, tilt) in enumerate(((0, 0, 7, 0), (-1.5, 1, 5, -22), (1.5, -0.5, 4, 26), (0, 2, 3, -8))):
        p = m.part(f"crystal{i}", "crystals", pivot=(x, 0, z), rot=(tilt * 0.4, 0, tilt))
        m.box(p, -1, -hgt, -1, 2, hgt, 2, ice(i), glow=ice_glow(i))

    # ------------------------------------------------------------------ head: pale dead face, spangenhelm, beard
    eyes = {(1, 3), (2, 3), (4, 3), (5, 3)}

    def face(f_, x, y, w, h):
        if (x, y) in eyes:
            return GLOW_L if x in (2, 4) else GLOW
        if y == 2 or (y == 3 and x in (0, 3, 6)):
            return mul(SKIN_D, 0.55)                                                    # shadow under the brim
        if y >= 5:
            return RIME if (x + y) % 2 else RIME_D                                       # frost on the moustache
        return mix(SKIN, SKIN_D, 0.3 + 0.1 * (x % 2))
    m.box("head", -3.5, -7, -3.5, 7, 7, 7, {"front": face, "*": frosted(K.skin(SKIN, 3), 20, 0.3)},
          glow={"front": lambda f_, x, y, w, h: (GLOW_L if x in (2, 4) else GLOW) if (x, y) in eyes else None, "*": None})

    def helm(f_, x, y, w, h):
        if f_ in ("front", "back", "left", "right") and x % 4 == 0:
            return mix(IRON_D, BRASS, 0.45)                                              # the spangen bands
        return frosted(iron(21, rivets=False), 22, 0.25)(f_, x, y, w, h)
    m.box("head", -4, -8.5, -4, 8, 4, 8, helm)
    m.box("head", -2.5, -10, -2.5, 5, 2, 5, frosted(iron(23, rivets=False), 24, 0.45))     # the domed crown
    m.box("head", -0.5, -11, -0.5, 1, 1, 1, BRASS)                                        # finial
    # spectacle guard: two rings round the eyes and a nasal
    spect = {(1, 0), (2, 0), (4, 0), (5, 0)}
    m.box("head", -3.5, -5, -4.3, 7, 2, 1, {"front": lambda f_, x, y, w, h: None if (x, y) in {(1, 1), (2, 1), (4, 1), (5, 1)}
                                            else (IRON_L if (x, y) in spect else IRON), "*": IRON_D})
    m.box("head", -0.5, -4, -4.6, 1, 3, 1, {"front": IRON_L, "*": IRON_D})
    m.box("head", -4.3, -5.5, -3, 1, 5, 6, frosted(iron(25, rivets=False), 26, 0.2))     # cheek flaps
    m.box("head", 3.3, -5.5, -3, 1, 5, 6, frosted(iron(27, rivets=False), 28, 0.2))
    m.box("head", -4, -4.5, 3.3, 8, 4, 1, MAIL_D, grow=0.0)                               # mail aventail at the nape

    def beard(f_, x, y, w, h):
        if f_ in ("front", "left", "right") and y == h - 1 and x % 2 == 1:
            return None
        return (RIME, RIME_D, (240, 248, 255))[K.h(x, y // 2, 30) % 3]
    m.box("beard", -3, 0, -0.5, 6, 5, 2, beard)
    m.box("beard", -1.5, 4, -0.3, 1, 3, 1, ice(31), glow=ice_glow(31))                    # icicles
    m.box("beard", 0.5, 4, -0.3, 1, 2, 1, ice(32), glow=ice_glow(32))
    m.box("beard", 2, 4, 0, 1, 1, 1, ice(33))
    m.box("beard", -2, 1, -0.9, 4, 1, 1, LEATHER_D)                                        # a braid ring
    m.box("beard", -1, 2, -1.0, 2, 1, 1, BRASS)

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -2 + 0.3 * sx, -1, -2, 4, 6, 4, frosted(mail(40 + sx), 41 + sx, 0.15))
        m.box(arm, -2.5 + 0.5 * sx, -2, -2.5, 5, 3, 5, frosted(iron(42 + sx), 43 + sx, 0.35))   # pauldron
        m.box(fore, -2 + 0.3 * sx, 0, -2, 4, 5, 4, K.leather(LEATHER, seed=44 + sx, stitch=LEATHER_D))
        m.box(fore, -2.2 + 0.3 * sx, 0.5, -2.2, 4, 1, 4, BRASS, grow=0.1)                 # arm ring
        m.box(fore, -2 + 0.3 * sx, 5, -2, 4, 2, 4, frosted(K.skin(SKIN_D, 45 + sx), 46 + sx, 0.25))  # fist

    # the bearded axe: an ash haft, an iron head with a hooked beard, a glowing frost edge
    m.box("axe", -0.5, -15, -0.5, 1, 18, 1, K.wood(WOOD, WOOD_D, seed=50, vertical=False))
    m.box("axe", -0.7, -2, -0.7, 1, 3, 1, LEATHER_D, grow=0.2)                            # grip wrap
    m.box("axe", -0.6, -15.8, -0.6, 1, 1, 1, IRON_D, grow=0.15)                           # pommel cap at the top
    m.box("axe", -1, -15, -2, 2, 3, 2, iron(51, rivets=False))                             # socket
    m.box("axe", -0.5, -15, -5, 1, 2, 3, iron(52, rivets=False))                           # cheek
    m.box("axe", -0.5, -16, -7, 1, 6, 2, {"*": IRON_L, "front": ICE_L, "top": ICE_L},
          glow={"front": GLOW_L, "*": lambda f_, x, y, w, h: GLOW if f_ in ("left", "right") and x == 0 else None})  # beard
    m.box("axe", -0.5, -11, -6, 1, 2, 1, IRON)                                             # the hook of the beard
    m.box("axe", -0.5, -14.5, 1, 1, 2, 1, IRON_D)                                          # back spike

    # the round shield: crimson and white quarters, an iron rim, a big boss, frost and icicles on the lower rim
    def disc(f_, x, y, w, h):
        if f_ in ("top", "bottom", "left", "right"):
            return IRON_D
        if f_ == "back":
            return K.wood(WOOD, WOOD_D, seed=60)(f_, x, y, w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        dx, dy = x - cx, y - cy
        if max(abs(dx), abs(dy)) >= cx - 0.6:
            return IRON_L if dy < 0 else IRON
        quarter = (dx < 0) != (dy < 0)
        c = (230, 226, 216) if quarter else WOOL
        if abs(dx) < 0.6 or abs(dy) < 0.6:
            c = WOOL_D
        if dy > cy - 4 and K.h(x, y, 61) % 3 == 0:
            c = RIME
        return c
    m.box("shield", -6, -6, -1, 12, 12, 1, disc)
    m.box("shield", -7, -4, -0.9, 14, 8, 1, {"*": IRON_D, "front": lambda f_, x, y, w, h: IRON if 0 < y < h - 1 else IRON_L})
    m.box("shield", -4, -7, -0.9, 8, 14, 1, {"*": IRON_D, "front": lambda f_, x, y, w, h: IRON_L if y == 0 else IRON})
    m.box("shield", -2, -2, -2.4, 4, 4, 2, frosted(iron(62), 63, 0.3))                    # the boss
    m.box("shield", -1, -1, -2.9, 2, 2, 1, IRON_L)
    m.box("shield", -5, 6, -1.3, 10, 1, 1, RIME)                                            # frost crust on the rim
    for i, (x, hgt) in enumerate(((-4, 3), (-1.5, 4), (1, 2), (3.5, 3))):
        m.box("shield", x, 7, -1.1, 1, hgt, 1, ice(64 + i), glow=ice_glow(64 + i))
    m.box("shield", -1, -1, 0, 2, 2, 1, LEATHER_D)                                          # the grip strap behind

    _anims(m)
    return m


def _anims(m):
    idle = m.anim("idle", 3.0)
    idle.pos("body", (0, (0, 0, 0)), (1.5, (0, -0.4, 0)), (3.0, (0, 0, 0)))
    idle.rot("body", (0, (0, 0, 0)), (1.5, (2, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (0, 8, 0)), (2.0, (2, -6, 0)), (3.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.5, (-5, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-3, 0, -2)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (3, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("axe", (0, (0, 0, 0)), (1.5, (-4, 0, 0)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.0)
    walk.rot("leg_r", (0, (26, 0, 0)), (0.5, (-26, 0, 0)), (1.0, (26, 0, 0)))
    walk.rot("leg_l", (0, (-26, 0, 0)), (0.5, (26, 0, 0)), (1.0, (-26, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.25, (0, 0, 0)), (0.75, (34, 0, 0)), (1.0, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.25, (34, 0, 0)), (0.5, (0, 0, 0)), (1.0, (0, 0, 0)))
    walk.rot("arm_r", (0, (-20, 0, 0)), (0.5, (16, 0, 0)), (1.0, (-20, 0, 0)))
    walk.rot("arm_l", (0, (4, 0, 0)), (0.5, (-4, 0, 0)), (1.0, (4, 0, 0)))                   # the shield stays up
    walk.rot("body", (0, (4, 4, 0)), (0.5, (4, -4, 0)), (1.0, (4, 4, 0)))
    walk.pos("body", (0, (0, 0, 0)), (0.25, (0, 0.7, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.7, 0)), (1.0, (0, 0, 0)))
    walk.rot("beard", (0, (6, 0, 0)), (0.5, (10, 0, 0)), (1.0, (6, 0, 0)))

    # chop: the axe raised high behind the head (0.7 s telegraph), a heavy chop down (lands at 0.7 s = 14 ticks)
    a = m.anim("chop", 1.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-165, 0, 10)), (0.65, (-170, 0, 10)), (0.75, (-40, 0, 0), "linear"),
          (1.0, (-35, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.55, (-50, 0, 0)), (0.75, (10, 0, 0), "linear"), (1.3, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.6, (-12, -18, 0)), (0.75, (18, 8, 0), "linear"), (1.0, (14, 6, 0)), (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-10, 0, -12)), (0.75, (10, 0, -6)), (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (-10, 10, 0)), (0.75, (8, 0, 0)), (1.3, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.6, (0, 0.6, 1)), (0.75, (0, -1.2, -2), "linear"), (1.0, (0, -1, -2)), (1.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (10, 0, 0)), (0.75, (-24, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (-6, 0, 0)), (0.75, (16, 0, 0)), (1.3, (0, 0, 0)))

    # bash: the shield drawn back to the chest (0.3 s), then punched forward boss first (lands at 0.35 s = 7 ticks)
    a = m.anim("bash", 0.8)
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (10, -20, -10)), (0.35, (-50, 10, 0), "linear"), (0.55, (-46, 8, 0)), (0.8, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.25, (-20, 0, 0)), (0.35, (40, 0, 0), "linear"), (0.55, (36, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.25, (0, 24, 0)), (0.35, (10, -20, 0), "linear"), (0.55, (8, -18, 0)), (0.8, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.25, (0, 0, 1.5)), (0.35, (0, 0, -3), "linear"), (0.55, (0, 0, -3)), (0.8, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.35, (-26, 0, 0)), (0.55, (-26, 0, 0)), (0.8, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.35, (18, 0, 0)), (0.55, (18, 0, 0)), (0.8, (0, 0, 0)))

    # cleave: turns his whole body away with the axe out behind him (0.95 s telegraph, rime gathering on the edge),
    # then a wide freezing sweep (lands at 0.95 s = 19 ticks)
    a = m.anim("cleave", 1.6)
    a.rot("body", (0, (0, 0, 0)), (0.85, (6, 70, 0)), (0.95, (6, 60, 0)), (1.1, (8, -75, 0), "linear"), (1.3, (6, -70, 0)),
          (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.85, (-75, 0, 50)), (1.1, (-85, 0, -20), "linear"), (1.3, (-80, 0, -20)), (1.6, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.85, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.85, (-30, 0, 0)), (1.1, (-10, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.85, (-20, 0, -30)), (1.1, (10, 0, -10)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.85, (0, -50, 0)), (1.1, (0, 40, 0)), (1.6, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.85, (0, -1.5, 0)), (1.1, (0, -1.5, -1)), (1.6, (0, 0, 0)))
    for leg, s in (("leg_r", 1), ("leg_l", -1)):
        a.rot(leg, (0, (0, 0, 0)), (0.85, (-14 * s, 0, 8 * s)), (1.1, (14 * s, 0, 8 * s)), (1.6, (0, 0, 0)))

    # block: a frontal blow glances off the raised shield
    a = m.anim("block", 0.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.08, (-30, 6, 0)), (0.4, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.08, (-6, 8, 0)), (0.4, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.08, (0, 0, 1)), (0.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.08, (6, 0, 0)), (0.4, (0, 0, 0)))

    # stagger: an axe split his guard: the shield flung wide, he reels back for a long second
    a = m.anim("stagger", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.15, (-40, 0, -70)), (0.9, (-30, 0, -60)), (1.2, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.15, (50, 0, 0)), (0.9, (40, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.15, (-16, -10, 0)), (0.9, (-12, -8, 0)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.15, (-20, 0, 0)), (0.9, (-14, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.15, (20, 0, 30)), (0.9, (14, 0, 24)), (1.2, (0, 0, 0)))
    a.pos("body", (0, (0, 0, 0)), (0.15, (0, 0, 2)), (0.9, (0, 0, 1.5)), (1.2, (0, 0, 0)))
