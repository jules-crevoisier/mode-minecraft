"""Basalt Guard (Garde de basalte): a nether-fortress guard in basalt plate, about 2.6 blocks tall.

Silhouette: broad layered pauldrons (the left one spiked), a horned great-helm with a burning visor slit,
plates of ridged basalt split by glowing ember seams, a scorched tabard, and a long-hafted golden axe held
upright beside the head (the model carries the axe; held items are not rendered).
"""
from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
BAS = (62, 60, 68)
BAS_L = (94, 92, 102)
BAS_D = (36, 34, 40)
BAS_DD = (22, 21, 26)
EMBER = (255, 136, 36)
EMBER_L = (255, 214, 120)
EMBER_D = (196, 70, 18)
GOLD = (240, 194, 64)
GOLD_L = (255, 238, 150)
GOLD_D = (176, 118, 30)
GOLD_DD = (120, 72, 20)
CLOTH = (96, 30, 26)
CLOTH_D = (58, 18, 18)
HORN = (44, 38, 40)
HORN_L = (92, 80, 76)
WOOD = (52, 36, 30)
LEATHER = (84, 52, 34)

FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
def basalt_px(x, y, seed=0, fid=0):
    """Basalt: vertical columnar ridges (lit / mid / shadow), with sparse horizontal joints and pits."""
    k = (x + _h(seed, fid) % 3) % 3
    c = (BAS_L, BAS, BAS_D)[k]
    c = mix(c, BAS, 0.35)
    if (y + _h(seed, x // 3, fid)) % 7 == 0:
        c = mix(c, BAS_DD, 0.5)                       # joint between column drums
    r = _h(x, y, seed, fid)
    if r % 17 == 0:
        c = mix(c, BAS_DD, 0.6)
    elif r % 23 == 0:
        c = mix(c, BAS_L, 0.5)
    return c


def plate(seed=0, seams=(), vseams=(), rim=True, cracks=0):
    """A basalt armour plate: dark rim, lit top edge, ember seams at given rows (``seams``) and columns
    (``vseams``), and ``cracks`` small glowing cracks. Use with ``ember_glow`` for the emissive layer."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face == "bottom":
            return BAS_DD
        if face == "top":
            return mix(basalt_px(x, y, seed, fid), BAS_L, 0.3)
        if is_seam(face, x, y, w, h, seed, seams, vseams, cracks):
            return EMBER if (x + y) % 3 else EMBER_L
        c = basalt_px(x, y, seed, fid)
        if rim and (x == 0 or x == w - 1 or y == h - 1):
            c = mix(c, BAS_DD, 0.55)
        if rim and y == 0:
            c = mix(c, BAS_L, 0.5)
        return c
    return f


def is_seam(face, x, y, w, h, seed, seams, vseams, cracks):
    if face in ("top", "bottom"):
        return False
    if y in seams and 0 < x < w - 1:
        return True
    if face in ("front", "back") and x in vseams and 0 < y < h - 1:
        return True
    if cracks and face == "front":
        for i in range(cracks):
            cx = 1 + _h(seed, i, 1) % max(1, w - 2)
            cy = 1 + _h(seed, i, 2) % max(1, h - 3)
            for j in range(3):
                if x == cx + (j if i % 2 else -j) // 2 and y == cy + j:
                    return True
    return False


def ember_glow(seed=0, seams=(), vseams=(), cracks=0):
    def f(face, x, y, w, h):
        if is_seam(face, x, y, w, h, seed, seams, vseams, cracks):
            return EMBER if (x + y) % 3 else EMBER_L
        return None
    return f


def gold(seed=0, engrave=True, edge_side=None):
    """Polished gold: lit upper half, darker bevel at the rim, engraved zig-zag, a pale cutting edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return GOLD_D
        c = mix(GOLD, GOLD_L, 0.35) if y < h * 0.4 else GOLD
        if face == edge_side and x <= 0:
            return GOLD_L
        if (x == 0 or x == w - 1 or y == 0 or y == h - 1) and w > 2 and h > 2:
            c = mix(c, GOLD_D, 0.5)
        if engrave and w > 3 and h > 3 and face in ("left", "right") and (x + y) % 4 == 0 and 1 <= y < h - 1:
            c = mix(c, GOLD_DD, 0.45)
        if _h(x, y, seed) % 19 == 0:
            c = mix(c, GOLD_L, 0.6)
        return c
    return f


def horn(seed=0, tip=False):
    def f(face, x, y, w, h):
        if tip and y == 0:
            return EMBER
        c = HORN if (y + seed) % 3 else HORN_L
        if _h(x, y, seed) % 7 == 0:
            c = mix(c, HORN_L, 0.5)
        return c
    return f


def tabard(seed=0):
    """Scorched tabard: dark red cloth with a gold fortress tower emblem, singed ragged hem."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return CLOTH_D
        if y >= h - 1 - (_h(seed, x) % 3):
            return None
        c = CLOTH if (x + seed) % 3 else mix(CLOTH, CLOTH_D, 0.5)
        if y >= h - 4:
            c = mix(c, (30, 20, 18), 0.5)              # singed hem
        if face == "front" and w >= 4:
            cx = w // 2
            # tower emblem: battlements, body, gate
            if y == 1 and x in (cx - 2, cx, cx + 1) or (y in (2, 3, 4, 5) and cx - 2 <= x <= cx + 1):
                c = GOLD if not (y >= 4 and x in (cx - 1, cx)) else CLOTH_D
        return c
    return f


def shaft(seed=0):
    def f(face, x, y, w, h):
        if y % 9 == 0:
            return GOLD_D                              # gold rings
        if h - 14 <= y <= h - 6:
            return LEATHER if (y + x) % 2 else mul(LEATHER, 0.8)   # grip
        return WOOD if (x + y) % 4 else mul(WOOD, 1.25)
    return f


# ------------------------------------------------------------------ model
def mirror(x, w):
    return -(x + w)


def build():
    m = Model("basalt_guard", seed=56, shadow=0.8, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -15, 0))
    m.part("tabard", "hips", pivot=(0, 1, -4))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(4, 0, 0))
    m.part("head", "torso", pivot=(0, -15, -0.5))
    m.part("cape", "torso", pivot=(2.5, -14, 4.2), rot=(6, 0, 0))
    m.part("horn_r", "head", pivot=(-4, -6, 0), rot=(0, 0, 0))
    m.part("horn_l", "head", pivot=(4, -6, 0), rot=(0, 0, 0))
    m.part("arm_r", "torso", pivot=(-9, -12, 0), rot=(0, 0, 12))
    m.part("forearm_r", "arm_r", pivot=(0, 9, 0), rot=(-30, 0, -6))
    m.part("axe", "forearm_r", pivot=(0, 8.5, -0.5), rot=(12, 90, 0))
    m.part("arm_l", "torso", pivot=(9, -12, 0), rot=(0, 0, -6))
    m.part("forearm_l", "arm_l", pivot=(0, 9, 0), rot=(-10, 0, 0))
    m.part("leg_r", "bone", pivot=(-3.5, -15, 0))
    m.part("shin_r", "leg_r", pivot=(0, 7, 0))
    m.part("leg_l", "bone", pivot=(3.5, -15, 0))
    m.part("shin_l", "leg_l", pivot=(0, 7, 0))

    # ------------------------------------------------------------------ body
    m.box("hips", -6, -2, -3.5, 12, 4, 7, plate(1, seams=(2,)), glow=ember_glow(1, seams=(2,)))
    m.box("hips", -1.5, -1.5, -4, 3, 3, 1, gold(2, engrave=False))          # buckle
    for i, x in enumerate((-6, 2)):
        m.box("hips", x, 1, -4.5, 4, 6, 1, plate(3 + i))                    # front tassets
        m.box("hips", x, 1, 3.5, 4, 5, 1, plate(5 + i))                     # back tassets
    m.box("tabard", -2, 0, -0.5, 4, 10, 1, tabard(7))

    chest_seams = dict(seams=(5,), vseams=(6, 7), cracks=2)
    m.box("torso", -7, -14, -4, 14, 11, 8, {"front": plate(8, **chest_seams), "*": plate(8, seams=(5,))},
          glow={"front": ember_glow(8, **chest_seams), "*": ember_glow(8, seams=(5,))})
    m.box("torso", -2, -12, -4.5, 4, 3, 1, lambda f_, x, y, w, h: EMBER_L if 1 <= x <= 2 and y == 1 else EMBER,
          glow=lambda f_, x, y, w, h: EMBER_L if 1 <= x <= 2 and y == 1 else EMBER)   # ember core
    m.box("torso", -6, -3, -3.5, 12, 4, 7, plate(9, seams=(1,)), glow=ember_glow(9, seams=(1,)))  # abdomen
    m.box("torso", -4, -16, -3.5, 8, 3, 7, plate(10))                         # gorget
    m.box("torso", -7.5, -14.5, 3.5, 15, 9, 1, plate(11, vseams=(7,)), glow=ember_glow(11, vseams=(7,)))  # backplate

    # scorched half-cape hanging from the left shoulder
    m.box("cape", -4, 0, 0, 9, 17, 1, {"back": tabard(15), "front": tabard(16), "*": CLOTH_D})

    # head: a great-helm with a burning visor slit and curved horns
    visor = {(x, 4) for x in range(1, 7)}

    def helm_front(f_, x, y, w, h):
        if (x, y) in visor:
            return EMBER_L if x in (2, 5) else EMBER
        if y == 3 or y == 5:
            return BAS_DD if 1 <= x <= 6 else BAS_D
        if x in (3, 4) and y >= 6:
            return BAS_L if x == 3 else BAS_D          # nasal ridge / breath vents
        return plate(12, rim=True)(f_, x, y, w, h)
    m.box("head", -4, -9, -4, 8, 9, 8, {"front": helm_front, "*": plate(12)},
          glow={"front": lambda f_, x, y, w, h: (EMBER_L if x in (2, 5) else EMBER) if (x, y) in visor else None,
                "*": None})
    m.box("head", -1, -10, -4.5, 2, 6, 9, plate(13, rim=False))               # crest ridge
    m.box("head", -4.5, -7, -4.5, 9, 1, 2, gold(14, engrave=False))           # gold brow band over the visor
    for side, sx in (("r", -1), ("l", 1)):
        hp = f"horn_{side}"

        def hb(x, y, z, w, h, d, paint, glow=None):
            m.box(hp, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        hb(-3, -1, -1.5, 3, 3, 3, horn(1))
        hb(-6, -2, -1, 3, 2, 2, horn(2))
        hb(-8, -4, -1, 2, 3, 2, horn(3))
        hb(-8.5, -7, -1.5, 1, 3, 1, horn(4))
        hb(-8.5, -8, -2.5, 1, 1, 1, horn(5, tip=True), glow={"top": EMBER, "front": EMBER, "*": None})

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"

        def bx(part, x, y, z, w, h, d, paint, glow=None):
            m.box(part, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        big = side == "l"
        # layered pauldron (the shield side is bigger and spiked)
        bx(arm, -5 if big else -4, -3, -4.5, 8 if big else 7, 5, 9, plate(20 + sx, seams=(3,)),
           glow=ember_glow(20 + sx, seams=(3,)))
        bx(arm, -4, -5, -4, 6, 2, 8, plate(22 + sx))
        if big:
            bx(arm, -3, -9, -1, 2, 4, 2, horn(5, tip=True), glow={"top": EMBER, "*": None})
            bx(arm, -3, -7, 2, 2, 2, 2, horn(6))
        bx(arm, -2.5, 1, -2.5, 5, 8, 5, plate(24 + sx, rim=False))
        bx(fore, -3, 0, -3, 6, 7, 6, plate(26 + sx, seams=(1,)), glow=ember_glow(26 + sx, seams=(1,)))   # gauntlet
        bx(fore, -2.5, 7, -2.5, 5, 3, 5, plate(28 + sx, rim=False))           # fist

    # golden axe: a long haft rising from the right fist, crescent blade facing forward
    m.box("axe", -1, -28, -1, 2, 36, 2, shaft(1))
    m.box("axe", -1.5, -27, -1.5, 3, 2, 3, gold(2, engrave=False))                  # socket
    m.box("axe", -0.5, -26, -7, 1, 7, 6, gold(3))                                     # cheek of the blade
    m.box("axe", -0.5, -31, -10, 1, 18, 2, gold(4, engrave=False, edge_side="front"))  # crescent edge
    m.box("axe", -0.5, -29, -8, 1, 3, 1, gold(7, engrave=False))                      # upper arm of the crescent
    m.box("axe", -0.5, -18, -8, 1, 3, 1, gold(8, engrave=False))                      # lower arm
    m.box("axe", -0.5, -32, -9, 1, 1, 1, GOLD_L)
    m.box("axe", -0.5, -13, -9, 1, 1, 1, GOLD_L)
    m.box("axe", -0.5, -25, 1, 1, 3, 4, gold(5, engrave=False))                      # back spike
    m.box("axe", -0.5, -33, -0.5, 1, 5, 1, gold(6, engrave=False))                   # top spike
    m.box("axe", -1, -23.5, -5, 2, 2, 2, EMBER, glow=EMBER)                           # ember gem in the cheek

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg, shin = f"leg_{side}", f"shin_{side}"

        def bx(part, x, y, z, w, h, d, paint, glow=None):
            m.box(part, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        bx(leg, -3, 0, -3, 6, 7, 6, plate(40 + sx))
        bx(leg, -3.5, 5, -3.5, 7, 2, 7, plate(42 + sx, seams=(0,), rim=False), glow=ember_glow(42 + sx, seams=(0,)))  # knee
        bx(shin, -3, 0, -3, 6, 6, 6, plate(44 + sx, vseams=(3,)), glow=ember_glow(44 + sx, vseams=(3,)))
        bx(shin, -3.5, 6, -5, 7, 3, 8, plate(46 + sx))                           # sabaton

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.rot("torso", (0, (0, 0, 0)), (1.5, (-2, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.0, (0, 10, 0)), (2.0, (0, -6, 0)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-3, 0, -2)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-2, 0, 1)), (3.0, (0, 0, 0)))
    idle.rot("tabard", (0, (0, 0, 0)), (1.5, (-5, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("cape", (0, (0, 0, 0)), (1.5, (4, 0, -2)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 1.4)
    walk.rot("leg_r", (0, (24, 0, 0)), (0.7, (-24, 0, 0)), (1.4, (24, 0, 0)))
    walk.rot("leg_l", (0, (-24, 0, 0)), (0.7, (24, 0, 0)), (1.4, (-24, 0, 0)))
    walk.rot("shin_r", (0, (0, 0, 0)), (0.35, (28, 0, 0)), (0.7, (0, 0, 0)), (1.4, (0, 0, 0)))
    walk.rot("shin_l", (0, (0, 0, 0)), (0.7, (0, 0, 0)), (1.05, (28, 0, 0)), (1.4, (0, 0, 0)))
    walk.rot("arm_l", (0, (-18, 0, 0)), (0.7, (18, 0, 0)), (1.4, (-18, 0, 0)))
    walk.rot("arm_r", (0, (6, 0, 0)), (0.7, (-6, 0, 0)), (1.4, (6, 0, 0)))
    walk.rot("torso", (0, (0, -4, 0)), (0.7, (0, 4, 0)), (1.4, (0, -4, 0)))
    walk.rot("tabard", (0, (-14, 0, 0)), (0.35, (-4, 0, 0)), (0.7, (-14, 0, 0)), (1.05, (-4, 0, 0)), (1.4, (-14, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.35, (0, 1, 0)), (0.7, (0, 0, 0)), (1.05, (0, 1, 0)), (1.4, (0, 0, 0)))
    walk.rot("cape", (0, (12, 0, 0)), (0.35, (18, 0, 2)), (0.7, (12, 0, 0)), (1.05, (18, 0, -2)), (1.4, (12, 0, 0)))

    # chop: the axe is drawn back over the shoulder (telegraph), then brought down at 0.65 s (13 ticks)
    a = m.anim("chop", 1.3)
    a.rot("arm_r", (0, (0, 0, 0)), (0.5, (-60, 0, 14)), (0.65, (-62, 0, -6), "linear"), (0.9, (-55, 0, -6)),
          (1.3, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.5, (-60, 0, 0)), (0.65, (-6, 0, 0), "linear"), (0.9, (-8, 0, 0)),
          (1.3, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.5, (-34, -90, 0)), (0.65, (114, -90, 0), "linear"), (0.9, (110, -90, 0)),
          (1.3, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.5, (-40, 0, -20)), (0.65, (-60, 0, 10), "linear"), (0.9, (-55, 0, 10)),
          (1.3, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.5, (-12, 22, 0)), (0.65, (22, -12, 0), "linear"), (0.9, (20, -10, 0)),
          (1.3, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (-6, -16, 0)), (0.65, (-14, 10, 0)), (1.3, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.5, (0, 0, 1.5)), (0.65, (0, -1.5, -3), "linear"), (0.9, (0, -1.5, -3)),
          (1.3, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.5, (8, 0, 0)), (0.65, (-22, 0, 0)), (0.9, (-22, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.5, (-4, 0, 0)), (0.7, (22, 0, 0)), (1.3, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.5, (-6, 0, 0)), (0.65, (14, 0, 0)), (0.9, (14, 0, 0)), (1.3, (0, 0, 0)))

    # cleave: wound up to the right with the axe held level (long telegraph), a wide sweep at 0.8 s (16 ticks)
    a = m.anim("cleave", 1.6)
    a.rot("torso", (0, (0, 0, 0)), (0.6, (0, 62, 0)), (0.8, (6, -70, 0), "linear"), (1.15, (6, -66, 0)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.6, (0, -40, 0)), (0.8, (0, 30, 0), "linear"), (1.15, (0, 30, 0)), (1.6, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.6, (-80, 0, 20)), (0.8, (-84, 0, 6), "linear"), (1.15, (-80, 0, 6)),
          (1.6, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.6, (-10, 0, 0)), (0.8, (0, 0, 0)), (1.6, (0, 0, 0)))
    a.rot("axe", (0, (0, 0, 0)), (0.6, (160, -90, 0)), (0.8, (168, -90, 0), "linear"), (1.15, (168, -90, 0)),
          (1.6, (0, 0, 0)))
    a.rot("cape", (0, (0, 0, 0)), (0.6, (10, 0, 20)), (0.85, (30, 0, -25)), (1.6, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.6, (-20, 0, -40)), (0.8, (-10, 0, -60)), (1.15, (-10, 0, -55)), (1.6, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.6, (0, -1.5, 1)), (0.8, (0, -2, -2), "linear"), (1.15, (0, -2, -2)), (1.6, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.6, (-16, 0, 6)), (0.8, (10, 0, 6)), (1.15, (10, 0, 6)), (1.6, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.6, (12, 0, -6)), (0.8, (-14, 0, -6)), (1.15, (-14, 0, -6)), (1.6, (0, 0, 0)))
    a.rot("tabard", (0, (0, 0, 0)), (0.6, (-10, 0, -20)), (0.85, (-20, 0, 30)), (1.6, (0, 0, 0)))
    return m
