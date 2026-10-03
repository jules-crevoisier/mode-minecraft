"""The Sand Pharaoh (Le Pharaon ensablé): a towering mummified god-king, about five blocks tall.

Bandages wound over dark dried flesh, a striped gold-and-lapis nemes headdress, a golden death mask with
glowing turquoise eyes, a broad jewelled collar, and a great sun ring of gold standing behind his head.
At rest he holds the crook and the flail crossed over his chest, like the painted lids of the tombs.
"""
from ..models import FACE_ID, Model, bands, framed, speckle
from ..texgen import mix, mul

LINEN = (198, 180, 140)
LINEN_L = (226, 210, 172)
LINEN_D = (146, 124, 90)
FLESH = (84, 58, 42)
FLESH_D = (46, 32, 26)
GOLD = (240, 194, 64)
GOLD_L = (255, 234, 140)
GOLD_D = (164, 110, 30)
LAPIS = (36, 64, 158)
LAPIS_D = (20, 36, 98)
TURQ = (60, 186, 176)
CARN = (178, 54, 40)
EYE = (120, 255, 230)
SHROUD = (122, 104, 78)
SHROUD_D = (84, 70, 52)
SAND = (214, 188, 122)


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (k & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return r


def wraps(seed=0, flesh=0.10, base=LINEN):
    """Linen bandages wound around the limb: turns 3 texels tall that climb one texel every four, a dark
    seam under each turn, a lit upper edge, a few torn slits that show the dried flesh, sand at the bottom."""
    def f(face, x, y, w, h):
        k = y + (x // 4 if face not in ("top", "bottom") else x // 3) + seed
        turn, ph = k // 3, k % 3
        r = _h(turn, seed, FACE_ID.get(face, 0))
        c = mix(base, LINEN_L, 0.3) if r % 4 == 0 else mix(base, LINEN_D, 0.22) if r % 4 == 1 else base
        if face not in ("top", "bottom") and (r >> 8) % 1000 < flesh * 1000:
            a = (r >> 4) % max(1, w - 3)
            if a <= x < a + 3 + (r >> 12) % 3 and ph != 0:
                return FLESH_D if ph == 1 else FLESH                 # torn slit, flesh in shadow
        if ph == 0:
            c = mix(c, LINEN_D, 0.7)                                 # seam under the turn above
        elif ph == 1:
            c = mix(c, LINEN_L, 0.3)
        if face not in ("top", "bottom") and h > 6 and y >= h - 2:
            c = mix(c, SAND, 0.4)                                    # sand caked at the bottom
        return c
    return f


def nemes(seed=0, axis="y", period=5):
    """The striped royal headcloth: broad gold bands and narrow lapis bands, a dark line between them."""
    def f(face, x, y, w, h):
        p = (y if axis == "y" else x) + seed
        k = p % period
        if k == 0:
            return mul(GOLD_D, 0.8)
        if k <= period - 3:
            return GOLD_L if k == 1 else GOLD
        return LAPIS if k == period - 2 else LAPIS_D
    return f


def gold_plate(seed=0):
    return framed(speckle(GOLD, 0.04, seed), GOLD_D)


def jewel_bands(rows):
    """Horizontal bead rows of the broad collar (rows of colours from the top); tiny bead dots."""
    def f(face, x, y, w, h):
        c = rows[min(y, len(rows) - 1)]
        if c in (TURQ, CARN, LAPIS) and x % 2 == 1:
            c = mul(c, 0.78)
        return c
    return f


def mask_face(face, x, y, w, h):
    """The golden death mask: lapis brows, kohl-lined eyes (they glow), a calm mouth."""
    if y <= 1:
        return GOLD_D if y == 0 else GOLD_L                          # brow band under the nemes
    if y == 3 and x in (1, 2, 3, 6, 7, 8):
        return LAPIS                                                 # brows
    if y == 5:
        if x in (2, 3, 6, 7):
            return EYE
        if x in (1, 8):
            return LAPIS_D                                           # kohl
    if y == 6 and x in (0, 9):
        return LAPIS_D                                               # kohl tail
    if y == 6 and x in (2, 3, 6, 7):
        return GOLD_D                                                # lower lid shadow
    if y == 9 and 3 <= x <= 6:
        return CARN if x in (4, 5) else GOLD_D                       # lips
    if x in (0, 9):
        return GOLD_D
    if y == 11:
        return GOLD_D
    return GOLD_L if x in (4, 5) and y in (2, 4) else GOLD


# Rest pose: the crook and the flail crossed over the chest (solved so the forearms cross at the wrists and the
# crook's hook rises over the left shoulder). Animations below are written as absolute poses through ``ab``.
REST = {
    "torso": (6, 0, 0), "head": (-6, 0, 0),
    "arm_r": (-27, -8, 0), "forearm_r": (-105, -59, 0), "crook": (133, 32, 0),
    "arm_l": (-28, 7, 0), "forearm_l": (-93, 56, 0), "flail": (128, -21, 0), "lashes": (-32, 67, 0),
}
Z = (0, 0, 0)


def ab(part, rot):
    """Offset that brings ``part`` to the absolute rotation ``rot`` (degrees)."""
    r = REST.get(part, Z)
    return tuple(rot[i] - r[i] for i in range(3))


def build():
    m = Model("sand_pharaoh", seed=48, shadow=1.3, walk_speed=0.75, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -40, 0))
    m.part("torso", "hips", pivot=(0, -3, 0), rot=REST["torso"])
    m.part("head", "torso", pivot=(0, -27, -1), rot=REST["head"])
    m.part("halo", "torso", pivot=(0, -36, 12))
    m.part("ring", "halo")
    m.part("shroud", "torso", pivot=(0, -23, 6), rot=(6, 0, 0))
    m.part("arm_r", "torso", pivot=(-13, -23, 0), rot=REST["arm_r"])
    m.part("forearm_r", "arm_r", pivot=(0, 15, 0), rot=REST["forearm_r"])
    m.part("crook", "forearm_r", pivot=(0, 16, 0), rot=REST["crook"])
    m.part("arm_l", "torso", pivot=(13, -23, 0), rot=REST["arm_l"])
    m.part("forearm_l", "arm_l", pivot=(0, 15, 0), rot=REST["forearm_l"])
    m.part("flail", "forearm_l", pivot=(0, 16, 0), rot=REST["flail"])
    m.part("lashes", "flail", pivot=(0, -13, 0), rot=REST["lashes"])
    m.part("leg_r", "bone", pivot=(-5, -40, 0))
    m.part("shin_r", "leg_r", pivot=(0, 20, 0))
    m.part("leg_l", "bone", pivot=(5, -40, 0))
    m.part("shin_l", "leg_l", pivot=(0, 20, 0))
    m.part("tatter", "hips", pivot=(6, 2, 7))

    # ------------------------------------------------------------------ hips: gold belt, pleated kilt, apron
    m.box("hips", -9, -3, -6, 18, 5, 12, {"front": bands([(1, GOLD_D), (3, jewel_bands([GOLD, LAPIS, GOLD])), (1, GOLD_D)]),
                                          "*": bands([(1, GOLD_D), (3, GOLD), (1, GOLD_D)])})
    kilt = lambda f_, x, y, w, h: (None if y >= h - 1 and x % 3 == 0 else
                                   mix(LINEN_D, SAND, 0.2) if x % 3 == 0 else LINEN_L if x % 3 == 1 else LINEN)
    m.box("hips", -9, 2, -6, 18, 6, 12, {"side": kilt, "bottom": None, "top": None})
    m.box("hips", -10, 8, -7, 20, 9, 14, {"side": kilt, "bottom": None, "top": kilt})
    m.box("hips", -3, 2, -8, 6, 16, 1, bands([(2, GOLD), (2, LAPIS), (1, GOLD), (2, TURQ), (1, GOLD), (2, LAPIS),
                                               (1, GOLD), (2, CARN), (2, GOLD_D)]))
    # loose grave wrappings trailing from the belt
    for i, (x, ln) in enumerate(((0, 22), (3, 16), (-4, 12))):
        m.box("tatter", x, 0, 0, 2, ln, 1, wraps(40 + i, flesh=0))

    # ------------------------------------------------------------------ torso: gaunt bandaged trunk
    m.box("torso", -6, -13, -4, 12, 13, 8, wraps(1, flesh=0.25))
    # ribs in a torn breach on the belly
    m.box("torso", -4, -11, -5, 7, 7, 1, lambda f_, x, y, w, h: (LINEN_D if y % 2 == 0 else FLESH_D) if f_ == "front" else FLESH)
    m.box("torso", -10, -26, -6, 20, 14, 12, wraps(2, flesh=0.15))
    # broad collar (usekh): bead rows with a fringe of drop beads
    rows = [GOLD_D, GOLD, LAPIS, GOLD, TURQ, GOLD, CARN, GOLD_L]
    m.box("torso", -13, -28, -8, 26, 8, 16, {
        "front": jewel_bands(rows), "back": jewel_bands(rows), "left": jewel_bands(rows), "right": jewel_bands(rows),
        "top": lambda f_, x, y, w, h: [GOLD, LAPIS, GOLD, TURQ, GOLD, CARN, GOLD, LAPIS][min(x, y, w - 1 - x, h - 1 - y) % 8],
        "bottom": GOLD_D})
    m.box("torso", -11, -20, -8, 22, 2, 1, lambda f_, x, y, w, h: (GOLD if x % 2 else LAPIS) if y == 0 else
          (GOLD_D if x % 2 else None))
    # winged scarab amulet on the chest
    m.box("torso", -2, -18, -9, 4, 4, 1, {"front": lambda f_, x, y, w, h: TURQ if 0 < x < 3 and y < 3 else GOLD, "*": GOLD},
          glow={"front": lambda f_, x, y, w, h: (150, 255, 230) if 0 < x < 3 and 0 < y < 3 else None})
    m.box("torso", -6, -17, -9, 4, 2, 1, bands([(1, GOLD), (1, LAPIS)]))
    m.box("torso", 2, -17, -9, 4, 2, 1, bands([(1, GOLD), (1, LAPIS)]))

    # ------------------------------------------------------------------ the sun ring behind the head
    ring_front = lambda f_, x, y, w, h: (GOLD_D if y in (0, h - 1) else LAPIS if x % 5 == 2 else GOLD_L if y == 1 else GOLD)
    for k in range(8):
        seg = m.part(f"ring_{k}", "ring", rot=(0, 0, 45 * k))
        m.box(seg, -8, -21, 0, 16, 4, 2, {"front": ring_front, "back": ring_front, "*": GOLD_D},
              glow={"front": lambda f_, x, y, w, h: (255, 214, 96) if y == 2 and x % 5 == 2 else None})
        # a short ray between every segment
        m.box(seg, -1, -25, 0, 2, 4, 1, {"front": GOLD_L, "*": GOLD_D})
    # two rearing cobras (uraei) at the foot of the ring
    for sx in (-1, 1):
        cob = m.part(f"cobra_{'l' if sx > 0 else 'r'}", "halo", pivot=(sx * 17, 13, -1), rot=(0, 0, -sx * 10))
        m.box(cob, -1, -9, 0, 2, 9, 2, bands([(2, GOLD), (1, LAPIS), (2, GOLD), (1, LAPIS), (3, GOLD)]))
        m.box(cob, -2, -13, -1, 4, 5, 3, {"front": lambda f_, x, y, w, h: (EYE if y == 1 and x in (0, 3) else
                                                                         LAPIS if y >= 2 and 0 < x < 3 else GOLD), "*": GOLD},
              glow={"front": lambda f_, x, y, w, h: EYE if y == 1 and x in (0, 3) else None})
    m.box("halo", -3, -3, 0, 6, 6, 1, {"front": lambda f_, x, y, w, h: CARN if 0 < x < 5 and 0 < y < 5 else GOLD,
                                       "*": GOLD},
          glow={"front": lambda f_, x, y, w, h: (255, 120, 70) if 1 < x < 4 and 1 < y < 4 else None})

    # ------------------------------------------------------------------ head: death mask and nemes
    m.box("head", -5, -12, -6, 10, 12, 10, {"front": mask_face, "*": gold_plate(3), "bottom": GOLD_D},
          glow={"front": lambda f_, x, y, w, h: EYE if y == 5 and x in (2, 3, 6, 7) else None})
    m.box("head", -1, -7, -7, 2, 3, 1, {"front": bands([(2, GOLD_L), (1, GOLD_D)]), "*": GOLD})       # nose
    # nemes crown and the flaring side wings
    m.box("head", -7, -15, -6, 14, 6, 12, {"*": nemes(0), "top": nemes(0, "x", 4), "front": bands([(1, GOLD_D), (5, nemes(1))])})
    for sx in (-1, 1):
        x0 = 5 if sx > 0 else -9
        m.box("head", x0, -10, -5, 4, 9, 10, nemes(2))
        # lappets falling over the collar
        m.box("head", x0, -1, -6, 4, 13, 4, {"*": nemes(1, period=4), "bottom": GOLD_D})
        m.box("head", x0, 12, -6, 4, 1, 4, GOLD_D)
    m.box("head", -5, -10, 4, 10, 10, 3, nemes(3))
    m.box("head", -3, -1, 6, 6, 9, 2, {"*": nemes(0, period=4)})                           # braided queue
    # uraeus on the brow and the false beard
    m.box("head", -1, -18, -8, 2, 5, 2, {"front": bands([(1, GOLD), (1, LAPIS), (3, GOLD)]), "*": GOLD})
    m.box("head", -2, -19, -9, 4, 2, 2, {"front": lambda f_, x, y, w, h: EYE if y == 1 and x in (0, 3) else GOLD, "*": GOLD},
          glow={"front": lambda f_, x, y, w, h: EYE if y == 1 and x in (0, 3) else None})
    m.box("head", -1, 0, -6, 2, 6, 2, bands([(1, GOLD), (1, LAPIS)]))

    # back shroud: ragged grave linen hanging from the collar, a painted band of glyphs across it
    glyphs = ["010111010", "111101111", "110011110", "010010111", "101010101", "111010010"]

    def shroud(face, x, y, w, h):
        tear = (x * 5 + (x * x) % 7) % 6
        if y >= h - 1 - tear:
            return None
        c = SHROUD if (x // 3) % 2 else mix(SHROUD, SHROUD_D, 0.5)
        if y in (2, 8, 22, 28):
            return GOLD_D if y in (2, 28) else LAPIS_D               # hems of the glyph bands
        if 3 <= y <= 7 or 23 <= y <= 27:
            c = mix(LINEN, SAND, 0.3)
            gx, gy = (x - 1) % 5, y - (3 if y <= 7 else 23) - 1
            g = glyphs[((x - 1) // 5 + (y > 20) * 3) % len(glyphs)]
            if 0 <= gx < 3 and 0 <= gy < 3 and g[gy * 3 + gx] == "1":
                return LAPIS_D if (x // 5 + y // 20) % 2 else CARN
            return c
        if (x + y * 3) % 17 == 0:
            c = SHROUD_D
        return c
    m.box("shroud", -10, 0, 0, 20, 38, 1, {"back": shroud, "front": shroud, "*": SHROUD_D})

    # ------------------------------------------------------------------ arms: long, gaunt, bandaged
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"
        m.box(arm, -3, -2, -3, 6, 17, 6, wraps(10 + sx, flesh=0.25))
        m.box(arm, -4, -4, -4, 8, 5, 8, {"top": nemes(4, "x", 4), "*": jewel_bands([GOLD_D, GOLD, LAPIS, GOLD, GOLD_D])})
        m.box(arm, -4, 10, -4, 8, 2, 8, bands([(1, GOLD), (1, GOLD_D)]))                    # arm ring
        m.box(fore, -2, 0, -2, 5, 14, 5, wraps(12 + sx, flesh=0.3))
        m.box(fore, -3, 6, -3, 7, 6, 7, {"side": bands([(1, GOLD_D), (1, GOLD), (2, LAPIS), (1, GOLD), (1, GOLD_D)]),
                                         "*": GOLD})                                           # bracer
        m.box(fore, -2, 14, -3, 5, 4, 5, {"*": lambda f_, x, y, w, h: FLESH_D if (x + y) % 3 == 0 else FLESH})
        for i, fx in enumerate((-2, 0, 2)):
            m.box(fore, fx, 18, -3, 1, 3, 1, FLESH_D)                                           # dried claws
    m.box("forearm_l", 2, 2, 2, 1, 14, 1, wraps(30, flesh=0))                                  # a loose strip

    # the crook (heka): a long gold-and-lapis staff with a hooked head
    staff = bands([(2, GOLD), (1, GOLD_D), (2, LAPIS), (1, GOLD_D)] * 8)
    m.box("crook", -1, -28, -1, 2, 40, 2, staff)
    m.box("crook", -1, -30, -7, 2, 2, 8, {"*": bands([(1, GOLD_L), (1, GOLD_D)]), "top": GOLD_L})
    m.box("crook", -1, -28, -8, 2, 6, 2, bands([(2, GOLD), (1, LAPIS), (3, GOLD)]))
    m.box("crook", -2, 11, -2, 4, 3, 4, framed(GOLD, GOLD_D))
    # the flail (nekhakha): a short handle and three strands of beads
    m.box("flail", -1, -12, -1, 2, 16, 2, staff)
    m.box("flail", -2, -14, -2, 4, 3, 4, framed(GOLD, GOLD_D))
    for i, (fx, fz) in enumerate(((-2, 0), (0, -1), (1, 0))):
        m.box("lashes", fx, -1, fz, 1, 13, 1, bands([(1, GOLD), (1, LAPIS), (1, CARN), (1, GOLD), (1, TURQ)] * 3))

    # ------------------------------------------------------------------ legs
    for side, sx in (("l", 1), ("r", -1)):
        leg, shin = f"leg_{side}", f"shin_{side}"
        m.box(leg, -3, 0, -3, 6, 20, 6, wraps(20 + sx, flesh=0.2))
        m.box(shin, -3, 0, -3, 6, 17, 6, wraps(22 + sx, flesh=0.25))
        m.box(shin, -3, 1, -3, 6, 2, 6, bands([(1, GOLD), (1, LAPIS)]))
        m.box(shin, -4, 17, -7, 8, 3, 10, {"top": wraps(24 + sx), "side": bands([(2, LINEN), (1, GOLD_D)]),
                                           "*": GOLD_D})

    anims(m)
    return m


def anims(m):
    def arm(a, side, keys, length):
        ak = [(0, Z)] + [(k[0], ab(f"arm_{side}", k[1]), *k[3:]) for k in keys] + [(length, Z)]
        fk = [(0, Z)] + [(k[0], ab(f"forearm_{side}", k[2]), *k[3:]) for k in keys] + [(length, Z)]
        a.rot(f"arm_{side}", *ak)
        a.rot(f"forearm_{side}", *fk)

    def held(a, part, keys, length):
        a.rot(part, *([(0, Z)] + [(k[0], ab(part, k[1]), *k[2:]) for k in keys] + [(length, Z)]))

    # idle: slow breathing, the ring drifting, the flail strands swaying
    idle = m.anim("idle", 4.0)
    idle.rot("torso", (0, Z), (2.0, (2, 0, 0)), (4.0, Z))
    idle.rot("head", (0, Z), (2.0, (-3, 4, 0)), (4.0, Z))
    idle.rot("halo", (0, Z), (2.0, (0, 0, 6)), (4.0, Z))
    idle.pos("halo", (0, Z), (2.0, (0, 1.5, 0)), (4.0, Z))
    idle.rot("shroud", (0, Z), (2.0, (5, 0, 1)), (4.0, Z))
    idle.rot("lashes", (0, Z), (1.3, (6, 0, 4)), (2.6, (-3, 0, -2)), (4.0, Z))
    idle.rot("tatter", (0, Z), (2.0, (8, 0, -4)), (4.0, Z))

    walk = m.anim("walk", 2.0)
    for leg, sign in (("leg_r", 1), ("leg_l", -1)):
        walk.rot(leg, (0, (20 * sign, 0, 0)), (1.0, (-20 * sign, 0, 0)), (2.0, (20 * sign, 0, 0)))
    walk.rot("shin_r", (0, Z), (0.5, (25, 0, 0)), (1.0, Z), (2.0, Z))
    walk.rot("shin_l", (0, Z), (1.0, Z), (1.5, (25, 0, 0)), (2.0, Z))
    walk.rot("torso", (0, (0, 4, 2)), (1.0, (0, -4, -2)), (2.0, (0, 4, 2)))
    walk.rot("shroud", (0, (8, 0, 0)), (1.0, (12, 0, 0)), (2.0, (8, 0, 0)))
    walk.rot("tatter", (0, (10, 0, 0)), (1.0, (20, 0, 0)), (2.0, (10, 0, 0)))
    walk.pos("bone", (0, Z), (0.5, (0, -1, 0)), (1.0, Z), (1.5, (0, -1, 0)), (2.0, Z))

    # Impact time x 20 = wind-up ticks in SandPharaoh.java.
    # flail (impact 0.75): the left arm unfolds high behind the shoulder, then lashes down across the body
    a = m.anim("flail", 1.5)
    arm(a, "l", [(0.6, (-160, 0, -35), (-20, 0, 0)), (0.75, (-165, 0, -38), (-25, 0, 0)),
                 (0.85, (-35, 0, 30), (-10, 0, 0), "linear"), (1.15, (-30, 0, 25), (-15, 0, 0))], 1.5)
    held(a, "flail", [(0.6, (180, 0, 0)), (0.85, (180, 0, 0)), (1.15, (180, 0, 0))], 1.5)
    a.rot("lashes", (0, Z), (0.6, ab("lashes", (70, 0, 0))), (0.75, ab("lashes", (90, 0, 0))),
          (0.85, ab("lashes", (-60, 0, 0)), "linear"), (1.0, ab("lashes", (20, 0, 0))), (1.5, Z))
    a.rot("torso", (0, Z), (0.6, (-8, -25, 0)), (0.75, (-8, -28, 0)), (0.85, (14, 25, 0), "linear"), (1.15, (12, 22, 0)), (1.5, Z))

    # hook (impact 0.8): the crook drawn back, thrust out, then yanked back toward the body
    a = m.anim("hook", 1.6)
    arm(a, "r", [(0.7, (-40, 50, 40), (-70, 0, 0)), (0.8, (-45, 55, 45), (-75, 0, 0)),
                 (0.9, (-90, 0, 0), (-5, 0, 0), "linear"), (1.05, (-90, 0, 0), (-5, 0, 0)),
                 (1.2, (-55, 30, 15), (-80, 0, 0), "linear")], 1.6)
    held(a, "crook", [(0.7, (180, 0, 0)), (0.9, (180, 0, 0)), (1.2, (180, 0, 0))], 1.6)
    a.rot("torso", (0, Z), (0.7, (-4, 30, 0)), (0.9, (12, -25, 0), "linear"), (1.05, (12, -25, 0)), (1.2, (-6, 15, 0), "linear"), (1.6, Z))
    a.pos("bone", (0, Z), (0.7, (0, 0, 3)), (0.9, (0, 0, -6), "linear"), (1.05, (0, 0, -6)), (1.2, (0, 0, -2)), (1.6, Z))

    # pillars (impact 0.95): both hands lift the crook over the head and drive its butt into the sand
    a = m.anim("pillars", 2.0)
    arm(a, "r", [(0.8, (-165, 0, -15), (-10, 0, 0)), (0.95, (-170, 0, -15), (-10, 0, 0)),
                 (1.05, (-55, 0, -10), (-20, 0, 0), "linear"), (1.5, (-55, 0, -10), (-20, 0, 0))], 2.0)
    arm(a, "l", [(0.8, (-165, 0, 15), (-10, 0, 0)), (0.95, (-170, 0, 15), (-10, 0, 0)),
                 (1.05, (-55, 0, 10), (-20, 0, 0), "linear"), (1.5, (-55, 0, 10), (-20, 0, 0))], 2.0)
    held(a, "crook", [(0.8, (180, 0, 0)), (1.05, (105, 0, 0), "linear"), (1.5, (105, 0, 0))], 2.0)
    a.rot("torso", (0, Z), (0.8, (-15, 0, 0)), (0.95, (-18, 0, 0)), (1.05, (24, 0, 0), "linear"), (1.5, (22, 0, 0)), (2.0, Z))
    a.rot("head", (0, Z), (0.8, (-20, 0, 0)), (1.05, (10, 0, 0)), (2.0, Z))
    a.pos("bone", (0, Z), (0.8, (0, 3, 0)), (1.05, (0, -4, 0), "linear"), (1.5, (0, -4, 0)), (2.0, Z))

    # scarabs (impact 0.8): arms flung wide, the head thrown back, the sun ring flares and spins
    a = m.anim("scarabs", 2.0)
    arm(a, "r", [(0.6, (-30, 0, 80), (-30, 0, 0)), (0.8, (-35, 0, 95), (-25, 0, 0)), (1.6, (-35, 0, 95), (-25, 0, 0))], 2.0)
    arm(a, "l", [(0.6, (-30, 0, -80), (-30, 0, 0)), (0.8, (-35, 0, -95), (-25, 0, 0)), (1.6, (-35, 0, -95), (-25, 0, 0))], 2.0)
    held(a, "crook", [(0.6, (180, 0, 0)), (1.6, (180, 0, 0))], 2.0)
    held(a, "flail", [(0.6, (180, 0, 0)), (1.6, (180, 0, 0))], 2.0)
    a.rot("head", (0, Z), (0.6, (-25, 0, 0)), (1.6, (-25, 0, 0)), (2.0, Z))
    a.rot("torso", (0, Z), (0.6, (-12, 0, 0)), (1.6, (-12, 0, 0)), (2.0, Z))
    a.rot("ring", (0, Z), (0.8, (0, 0, 90), "linear"), (1.6, (0, 0, 270), "linear"), (2.0, (0, 0, 360)), (2.0, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.8, (1.25, 1.25, 1)), (1.6, (1.25, 1.25, 1)), (2.0, (1, 1, 1)))

    # curse (impact 0.9): the flail points at the victim, the mask leans in, eyes blazing
    a = m.anim("curse", 1.6)
    arm(a, "l", [(0.7, (-95, 0, -10), (-5, 0, 0)), (0.9, (-100, 0, -10), (-5, 0, 0)), (1.2, (-100, 0, -10), (-5, 0, 0))], 1.6)
    held(a, "flail", [(0.7, (180, 0, 0)), (1.2, (180, 0, 0))], 1.6)
    a.rot("head", (0, Z), (0.7, (14, 0, 0)), (0.9, (18, 0, 0)), (1.2, (18, 0, 0)), (1.6, Z))
    a.rot("torso", (0, Z), (0.7, (8, -15, 0)), (1.2, (8, -15, 0)), (1.6, Z))
    a.scale("head", (0, (1, 1, 1)), (0.9, (1.1, 1.1, 1.1)), (1.0, (1, 1, 1)), (1.6, (1, 1, 1)))

    # burrow (impact 0.8, emerges at 1.4): sinks into the sand, travels under it, bursts out arms raised
    a = m.anim("burrow", 2.4)
    a.pos("bone", (0, Z), (0.3, (0, 4, 0)), (0.8, (0, -90, 0)), (1.3, (0, -90, 0)), (1.4, (0, 6, 0), "linear"), (1.8, Z), (2.4, Z))
    a.rot("bone", (0, Z), (0.8, (0, 180, 0)), (1.3, (0, 180, 0)), (1.4, (0, 360, 0), "linear"), (2.4, (0, 360, 0)), (2.4, Z))
    arm(a, "r", [(0.3, (-40, 0, 30), (-60, 0, 0)), (0.8, (-175, 0, -10), (0, 0, 0)), (1.4, (-170, 0, -25), (0, 0, 0)),
                 (1.8, (-150, 0, -35), (-10, 0, 0))], 2.4)
    arm(a, "l", [(0.3, (-40, 0, -30), (-60, 0, 0)), (0.8, (-175, 0, 10), (0, 0, 0)), (1.4, (-170, 0, 25), (0, 0, 0)),
                 (1.8, (-150, 0, 35), (-10, 0, 0))], 2.4)
    held(a, "crook", [(0.3, (180, 0, 0)), (1.8, (180, 0, 0))], 2.4)
    held(a, "flail", [(0.3, (180, 0, 0)), (1.8, (180, 0, 0))], 2.4)
    a.rot("head", (0, Z), (1.4, (-25, 0, 0)), (1.8, (-20, 0, 0)), (2.4, Z))

    # sandstorm (phase 2, impact 0.6): arms raised, the body slowly turning inside the storm
    a = m.anim("sandstorm", 3.3)
    arm(a, "r", [(0.5, (-150, 0, 35), (-15, 0, 0)), (2.6, (-150, 0, 35), (-15, 0, 0))], 3.3)
    arm(a, "l", [(0.5, (-150, 0, -35), (-15, 0, 0)), (2.6, (-150, 0, -35), (-15, 0, 0))], 3.3)
    held(a, "crook", [(0.5, (180, 0, 0)), (2.6, (180, 0, 0))], 3.3)
    held(a, "flail", [(0.5, (180, 0, 0)), (2.6, (180, 0, 0))], 3.3)
    a.rot("bone", (0, Z), (0.6, (0, 20, 0)), (2.6, (0, 380, 0), "linear"), (3.3, (0, 360, 0)), (3.3, Z))
    a.rot("head", (0, Z), (0.5, (-25, 0, 0)), (2.6, (-25, 0, 0)), (3.3, Z))
    a.rot("ring", (0, Z), (2.6, (0, 0, -720), "linear"), (3.3, (0, 0, -720)), (3.3, Z))
    a.rot("shroud", (0, Z), (0.6, (40, 0, 0)), (2.6, (45, 0, 0)), (3.3, Z))

    # sarcophagus (phase 2, impact 1.0): both arms call it from the sky and pull it down on the victim
    a = m.anim("sarcophagus", 2.4)
    arm(a, "r", [(0.8, (-175, 0, 20), (0, 0, 0)), (1.0, (-178, 0, 20), (0, 0, 0)), (1.12, (-60, 0, 10), (-10, 0, 0), "linear"),
                 (1.8, (-55, 0, 10), (-10, 0, 0))], 2.4)
    arm(a, "l", [(0.8, (-175, 0, -20), (0, 0, 0)), (1.0, (-178, 0, -20), (0, 0, 0)), (1.12, (-60, 0, -10), (-10, 0, 0), "linear"),
                 (1.8, (-55, 0, -10), (-10, 0, 0))], 2.4)
    held(a, "crook", [(0.8, (180, 0, 0)), (1.8, (180, 0, 0))], 2.4)
    held(a, "flail", [(0.8, (180, 0, 0)), (1.8, (180, 0, 0))], 2.4)
    a.rot("torso", (0, Z), (0.8, (-18, 0, 0)), (1.0, (-20, 0, 0)), (1.12, (20, 0, 0), "linear"), (1.8, (16, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.8, (-30, 0, 0)), (1.12, (5, 0, 0)), (2.4, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.8, (1.35, 1.35, 1)), (1.12, (1, 1, 1)), (2.4, (1, 1, 1)))

    # flurry (phase 2, impact 0.6 then every 0.35 s): crook, flail, crook, flail, stepping forward
    a = m.anim("flurry", 2.6)
    arm(a, "r", [(0.5, (-150, 30, 20), (-20, 0, 0)), (0.6, (-150, 30, 20), (-20, 0, 0)), (0.7, (-40, -20, -10), (-10, 0, 0), "linear"),
                 (1.15, (-150, 30, 20), (-20, 0, 0)), (1.3, (-150, 30, 20), (-20, 0, 0)), (1.4, (-30, -30, -10), (-10, 0, 0), "linear"),
                 (2.0, (-30, -20, -5), (-20, 0, 0))], 2.6)
    arm(a, "l", [(0.6, (-50, 0, 0), (-60, 0, 0)), (0.85, (-150, -30, -20), (-20, 0, 0)), (0.95, (-150, -30, -20), (-20, 0, 0)),
                 (1.05, (-30, 20, 10), (-10, 0, 0), "linear"), (1.5, (-150, -30, -20), (-20, 0, 0)), (1.65, (-155, -30, -20), (-20, 0, 0)),
                 (1.75, (-20, 20, 10), (-10, 0, 0), "linear"), (2.0, (-30, 10, 5), (-20, 0, 0))], 2.6)
    held(a, "crook", [(0.5, (180, 0, 0)), (2.0, (180, 0, 0))], 2.6)
    held(a, "flail", [(0.6, (180, 0, 0)), (2.0, (180, 0, 0))], 2.6)
    a.rot("lashes", (0, Z), (0.95, ab("lashes", (70, 0, 0))), (1.05, ab("lashes", (-60, 0, 0)), "linear"),
          (1.65, ab("lashes", (70, 0, 0))), (1.75, ab("lashes", (-60, 0, 0)), "linear"), (2.2, ab("lashes", (10, 0, 0))), (2.6, Z))
    a.rot("torso", (0, Z), (0.6, (-6, 25, 0)), (0.7, (12, -25, 0), "linear"), (0.95, (-6, -25, 0)), (1.05, (12, 25, 0), "linear"),
          (1.3, (-6, 25, 0)), (1.4, (12, -25, 0), "linear"), (1.65, (-6, -25, 0)), (1.75, (14, 25, 0), "linear"), (2.0, (12, 20, 0)), (2.6, Z))
    a.pos("bone", (0, Z), (0.7, (0, 0, -4)), (1.05, (0, 0, -8)), (1.4, (0, 0, -12)), (1.75, (0, 0, -16)), (2.0, (0, 0, -16)), (2.6, Z))

    # roar: phase change, arms flung open, the ring spinning and swelling
    a = m.anim("roar", 2.4)
    a.rot("torso", (0, Z), (0.5, (-22, 0, 0)), (1.9, (-22, 0, 0)), (2.4, Z))
    a.rot("head", (0, Z), (0.5, (-35, 0, 0)), (1.9, (-35, 0, 0)), (2.4, Z))
    arm(a, "r", [(0.5, (-30, 0, 85), (-20, 0, 0)), (1.9, (-30, 0, 85), (-20, 0, 0))], 2.4)
    arm(a, "l", [(0.5, (-30, 0, -85), (-20, 0, 0)), (1.9, (-30, 0, -85), (-20, 0, 0))], 2.4)
    held(a, "crook", [(0.5, (180, 0, 0)), (1.9, (180, 0, 0))], 2.4)
    held(a, "flail", [(0.5, (180, 0, 0)), (1.9, (180, 0, 0))], 2.4)
    a.rot("ring", (0, Z), (1.9, (0, 0, 540), "linear"), (2.4, (0, 0, 720)), (2.4, Z))
    a.scale("halo", (0, (1, 1, 1)), (0.5, (1.4, 1.4, 1)), (1.9, (1.4, 1.4, 1)), (2.4, (1, 1, 1)))

    # stagger: posture broken, he sags onto one knee, the mask bowed, the crook arm hanging
    a = m.anim("stagger", 2.5)
    a.pos("bone", (0, Z), (0.3, (0, -8, 2)), (2.1, (0, -8, 2)), (2.5, Z))
    a.rot("leg_r", (0, Z), (0.3, (-65, 0, 0)), (2.1, (-65, 0, 0)), (2.5, Z))
    a.rot("shin_r", (0, Z), (0.3, (65, 0, 0)), (2.1, (65, 0, 0)), (2.5, Z))
    a.rot("leg_l", (0, Z), (0.3, (20, 0, 0)), (2.1, (20, 0, 0)), (2.5, Z))
    a.rot("shin_l", (0, Z), (0.3, (65, 0, 0)), (2.1, (65, 0, 0)), (2.5, Z))
    a.rot("torso", (0, Z), (0.3, (20, 0, 6)), (2.1, (20, 0, 6)), (2.5, Z))
    a.rot("head", (0, Z), (0.3, (22, 0, 0)), (2.1, (22, 0, 0)), (2.5, Z))
    arm(a, "r", [(0.3, (-10, 0, 5), (-15, 0, 0)), (2.1, (-10, 0, 5), (-15, 0, 0))], 2.5)
    held(a, "crook", [(0.3, (170, 0, 0)), (2.1, (170, 0, 0))], 2.5)
    a.rot("halo", (0, Z), (0.3, (0, 0, -20)), (2.1, (0, 0, -20)), (2.5, Z))
